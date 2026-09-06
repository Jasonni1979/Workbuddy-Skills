#!/usr/bin/env python3
"""return_analysis.py — 退货数据结构化交叉统计（仅 Python 标准库，非交互）。

用法:
    python return_analysis.py --data returns.csv --config config.json --out ./out
    # 可选：提供成交明细计算真实退货率
    python return_analysis.py --data returns.csv --orders orders.csv --config config.json --out ./out

输入:
    --data    退货明细 CSV（UTF-8，含表头），列名由 config.columns 映射
    --orders  成交明细 CSV（可选，同列映射口径）。提供时计算 SKU×渠道退货率；
              不提供时仅做退货记录分布分析（报告中须注明分母缺失）
    --config  JSON:
        columns: sku / category / channel / order_date / return_date / reason /
                 qty / amount / freight_insurance（仅 sku、reason 必填，其余可选）
        reason_map: {"归因大类": ["关键词", ...], ...}  对原因文本/原因码子串匹配归类
        benchmarks: {"品类": 退货率基准(float 0-1), ...}（可选，超标即标记）
        alert_return_rate: 高退货预警线（默认 0.5）
        promo_keywords: 大促订单识别关键词（order_date 所在月份判断的替代：
                        可选 promo_months: ["06","11"] 按月份识别大促）
    --out     输出目录（自动创建）

输出:
    sku_return_stats.csv  SKU,渠道,退货件数,退货金额,原因分布,退货率(如有orders),超基准标记
    reason_matrix.csv     归因大类×品类 交叉表（件数与金额）
    time_pattern.csv      月份/大促期 退货件数与金额、退货间隔分布(<24h/1-7d/>7d)
    summary.json          总体统计、Top10 高退货 SKU、成本估算（假设系数见脚本内注释）

设计约束: 无网络、无交互、不写输入目录。
已知局限: 原因归类为关键词子串匹配，平台原因码口径不一（"七天无理由"可能掩盖尺码问题），
Top SKU 的真实原因结构须由 Agent 结合退款留言文本复核。
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

# 退货成本系数（行业参考假设，测算时用；有实际数据应替换）：
# 双向运费占退款额比例、包装损耗比例、质检翻新人工比例
COST_FACTORS = {"freight_ratio": 0.08, "package_ratio": 0.02, "labor_ratio": 0.03}


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    cols = cfg.get("columns", {})
    for k in ("sku", "reason"):
        if k not in cols:
            raise SystemExit(f"[FAIL] config.columns.{k} 必填")
    cfg.setdefault("reason_map", {})
    cfg.setdefault("benchmarks", {})
    cfg.setdefault("alert_return_rate", 0.5)
    cfg.setdefault("promo_months", [])
    return cfg


def read_csv(path: str, cols: dict, only: list[str] | None = None) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise SystemExit(f"[FAIL] {path} 无表头")
        keys = only if only else list(cols)
        missing = [cols[k] for k in keys if cols.get(k) and cols[k] not in reader.fieldnames]
        if missing:
            raise SystemExit(f"[FAIL] {path} 缺少列: {missing}；实际列: {reader.fieldnames}")
        return list(reader)


def to_num(value, default=0.0) -> float:
    try:
        return float(str(value).replace(",", "").replace("￥", "").replace("¥", "").strip())
    except (TypeError, ValueError):
        return default


def parse_date(value):
    if not value:
        return None
    s = str(value).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S",
                "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s[:19] if "T" in fmt or "%H" in fmt else s[:10], fmt)
        except ValueError:
            continue
    return None


def classify(reason_text: str, reason_map: dict) -> str:
    for cat, kws in reason_map.items():
        if any(k.lower() in reason_text.lower() for k in kws):
            return cat
    return "未归类" if reason_map else "未配置归类"


def anon(text: str, limit: int = 40) -> str:
    t = re.sub(r"1[3-9]\d{9}", "[手机]", text or "")
    t = re.sub(r"\d{8,}", "[编号]", t)
    return t[:limit]


def main() -> int:
    ap = argparse.ArgumentParser(description="退货数据交叉统计")
    ap.add_argument("--data", required=True, help="退货明细 CSV")
    ap.add_argument("--orders", help="成交明细 CSV（可选，用于退货率分母）")
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cfg = load_config(args.config)
    cols = cfg["columns"]
    reason_map = cfg["reason_map"]
    benchmarks = cfg["benchmarks"]
    alert = cfg["alert_return_rate"]
    promo_months = set(cfg["promo_months"])

    returns = read_csv(args.data, cols)
    if not returns:
        raise SystemExit("[FAIL] 退货明细为空")
    # 成交明细只需 SKU/渠道/件数列（分母口径），其余退货专属列不作要求
    orders = read_csv(args.orders, cols, only=["sku", "channel", "qty"]) if args.orders else None

    def key(row):
        sku = (row.get(cols["sku"]) or "").strip()
        ch = (row.get(cols.get("channel", ""), "") or "").strip() if cols.get("channel") else ""
        return (sku, ch)

    # SKU×渠道 聚合
    ret_qty: Counter = Counter()
    ret_amt: Counter = Counter()
    ret_reason: defaultdict[tuple, Counter] = defaultdict(Counter)
    for r in returns:
        k = key(r)
        q = to_num(r.get(cols.get("qty")), 1) or 1
        ret_qty[k] += q
        ret_amt[k] += to_num(r.get(cols.get("amount")))
        ret_reason[k][classify((r.get(cols["reason"]) or ""), reason_map)] += q

    ord_qty: Counter = Counter()
    if orders:
        for o in orders:
            k = key(o)
            ord_qty[k] += to_num(o.get(cols.get("qty")), 1) or 1

    # 归因×品类矩阵
    matrix_qty: defaultdict[str, Counter] = defaultdict(Counter)
    matrix_amt: defaultdict[str, float] = defaultdict(float)
    for r in returns:
        cat = classify((r.get(cols["reason"]) or ""), reason_map)
        pcat = (r.get(cols.get("category", ""), "") or "未分类").strip() if cols.get("category") else "未分类"
        matrix_qty[pcat][cat] += to_num(r.get(cols.get("qty")), 1) or 1
        matrix_amt[f"{pcat}|{cat}"] += to_num(r.get(cols.get("amount")))

    # 时间模式
    month_qty: Counter = Counter()
    month_amt: Counter = Counter()
    interval_buckets: Counter = Counter()
    for r in returns:
        od = parse_date(r.get(cols.get("order_date"))) if cols.get("order_date") else None
        rd = parse_date(r.get(cols.get("return_date"))) if cols.get("return_date") else None
        q = to_num(r.get(cols.get("qty")), 1) or 1
        amt = to_num(r.get(cols.get("amount")))
        if rd:
            m = rd.strftime("%Y-%m")
            month_qty[m] += q
            month_amt[m] += amt
        if od and rd:
            days = (rd - od).days
            b = "<24h(冲动/比价)" if days == 0 else ("1-7d(收货即退)" if days <= 7 else ">7d(使用后问题)")
            interval_buckets[b] += q

    os.makedirs(args.out, exist_ok=True)

    # sku_return_stats.csv
    p1 = os.path.join(args.out, "sku_return_stats.csv")
    top: list[tuple] = []
    with open(p1, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["SKU", "渠道", "退货件数", "退货金额", "成交件数", "退货率",
                    "原因分布", "超基准/预警"])
        for k in sorted(ret_qty, key=lambda x: -ret_qty[x]):
            sku, ch = k
            oq = ord_qty.get(k)
            rate = ret_qty[k] / oq if oq else None
            cat = ""
            # 品类基准需要 category 字段，取该 SKU 退货记录中的首个品类
            flags = []
            if rate is not None and rate >= alert:
                flags.append(f"≥预警线{alert:.0%}")
            if benchmarks and cols.get("category"):
                for r in returns:
                    if (r.get(cols["sku"]) or "").strip() == sku:
                        cat = (r.get(cols["category"]) or "").strip()
                        break
                bm = benchmarks.get(cat)
                if bm is not None and rate is not None and rate > bm:
                    flags.append(f"超{cat}基准{bm:.0%}")
            reasons = " / ".join(f"{c}:{q}" for c, q in ret_reason[k].most_common(3))
            w.writerow([sku, ch, ret_qty[k], round(ret_amt[k], 2),
                        oq if oq else "", f"{rate:.1%}" if rate is not None else "",
                        reasons, "；".join(flags)])
            if rate is not None:
                top.append((rate, sku, ch, ret_qty[k], ret_amt[k]))

    # reason_matrix.csv
    p2 = os.path.join(args.out, "reason_matrix.csv")
    all_cats = sorted({c for m in matrix_qty.values() for c in m})
    with open(p2, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["品类"] + [f"{c}(件)" for c in all_cats] + [f"{c}(金额)" for c in all_cats])
        for pcat, m in matrix_qty.items():
            w.writerow([pcat] + [m.get(c, 0) for c in all_cats]
                       + [round(matrix_amt.get(f"{pcat}|{c}", 0), 2) for c in all_cats])

    # time_pattern.csv
    p3 = os.path.join(args.out, "time_pattern.csv")
    with open(p3, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["月份", "退货件数", "退货金额", "大促月"])
        for m in sorted(month_qty):
            w.writerow([m, month_qty[m], round(month_amt[m], 2), "是" if m[-2:] in promo_months else ""])
        w.writerow([])
        w.writerow(["退货间隔", "件数", "", ""])
        for b, q in interval_buckets.most_common():
            w.writerow([b, q, "", ""])

    total_amt = sum(ret_amt.values())
    cost_est = round(total_amt * (COST_FACTORS["freight_ratio"] + COST_FACTORS["package_ratio"]
                                  + COST_FACTORS["labor_ratio"]), 2)
    summary = {
        "return_rows": len(returns),
        "order_rows": len(orders) if orders else None,
        "rate_denominator_available": orders is not None,
        "total_return_qty": sum(ret_qty.values()),
        "total_return_amount": round(total_amt, 2),
        "extra_cost_estimate": cost_est,
        "cost_factors_assumption": COST_FACTORS,
        "top10_return_rate": [
            {"sku": s, "channel": c, "rate": round(r, 4), "qty": q, "amount": round(a, 2)}
            for r, s, c, q, a in sorted(top, reverse=True)[:10]
        ] if orders else "无成交分母，退货率未计算",
        "interval_distribution": dict(interval_buckets),
        "reason_distribution": dict(Counter(
            classify((r.get(cols["reason"]) or ""), reason_map) for r in returns)),
        "outputs": [p1, p2, p3],
        "notice": "原因归类为关键词初筛，Top SKU 须结合退款留言复核",
    }
    p4 = os.path.join(args.out, "summary.json")
    with open(p4, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"[OK] 退货记录 {len(returns)}，成交记录 {len(orders) if orders else '未提供(退货率缺分母)'}")
    print(f"[OK] 退货总金额 {round(total_amt, 2)}，附加成本估算 {cost_est}（系数为行业假设）")
    print(f"[OK] 归因分布: {summary['reason_distribution']}")
    print(f"[OK] 间隔分布: {dict(interval_buckets)}")
    print(f"[OK] 输出: {p4}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
