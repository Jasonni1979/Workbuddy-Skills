#!/usr/bin/env python3
"""channel_score.py — 全渠道健康度六维加权评分（仅 Python 标准库，非交互）。

用法:
    python channel_score.py --data channels.csv --config config.json --out ./out

输入:
    --data   渠道汇总 CSV（UTF-8，一行一渠道），列名由 config.columns 映射
    --config JSON:
        columns: channel(必填) / gmv / margin / margin_rate / return_rate /
                 cac_cost / new_customers / inventory_days / gmv_yoy（其余可选）
        weights: 六维权重（gmv_share/margin_quality/return_rate/cac/inventory/growth），
                 缺省用默认权重；数据缺失的维度不计权并归一化
        benchmarks: {"margin_rate": 0.55, "return_rate": 0.25, "cac": 80,
                     "inventory_days": 60}（行业/品牌基准，缺省用此默认）
        strategic_channels: [渠道名]（战略投入期渠道，单列不参与排名）
    --out    输出目录（自动创建）

输出:
    channel_scores.csv    渠道,六维得分(0-100),加权总分,分级,是否战略单列,排名
    dimension_detail.csv  渠道,维度,原始值,基准,得分,是否计权
    summary.json          排名、GMV集中度(HHI)、预警清单、数据缺口

评分逻辑（详见 references/channel-framework.md）:
    gmv_share     体量分(份额对数缩放)×0.6 + 组合健康(依赖惩罚)×0.4
    margin_quality 毛利率/基准 封顶 1.2 后缩放
    return_rate   基准/实际（越低越好），封顶
    cac           基准/CAC（越低越好），封顶
    inventory     基准/周转天数（越低越好），封顶
    growth        同比增速映射（≥30% 满分，≤-20% 0 分，线性）
设计约束: 无网络、无交互。
已知局限: 相对健康的量化表达，战略投入期低分是常态；渠道口径不一致时评分失真，
须先对齐口径。分级阈值可在报告中按品牌调整。
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys

DEFAULT_WEIGHTS = {"gmv_share": 0.20, "margin_quality": 0.25, "return_rate": 0.15,
                   "cac": 0.15, "inventory": 0.10, "growth": 0.15}
DEFAULT_BENCH = {"margin_rate": 0.55, "return_rate": 0.25, "cac": 80, "inventory_days": 60}
DIMS = list(DEFAULT_WEIGHTS.keys())


def clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))


def to_num(v):
    try:
        s = str(v).replace(",", "").replace("%", "").replace("￥", "").replace("¥", "").strip()
        return float(s)
    except (TypeError, ValueError):
        return None


def to_ratio(v):
    """解析增速/比率：'3%'→0.03；0.03→0.03；裸数字按 |x|>1 视为百分数（3→0.03）。"""
    if v is None:
        return None
    s = str(v).strip()
    n = to_num(s)
    if n is None:
        return None
    if "%" in s:
        return n / 100
    if abs(n) > 1:
        return n / 100
    return n


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    if "channel" not in cfg.get("columns", {}):
        raise SystemExit("[FAIL] config.columns.channel 必填")
    cfg.setdefault("weights", DEFAULT_WEIGHTS)
    cfg.setdefault("benchmarks", DEFAULT_BENCH)
    cfg.setdefault("strategic_channels", [])
    w = cfg["weights"]
    s = sum(w.get(d, 0) for d in DIMS)
    if s <= 0:
        raise SystemExit("[FAIL] weights 总和须 > 0")
    return cfg


def main() -> int:
    ap = argparse.ArgumentParser(description="全渠道健康度评分")
    ap.add_argument("--data", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cfg = load_config(args.config)
    cols = cfg["columns"]
    weights = {d: cfg["weights"].get(d, DEFAULT_WEIGHTS[d]) for d in DIMS}
    bench = {**DEFAULT_BENCH, **cfg["benchmarks"]}
    strategic = set(cfg["strategic_channels"])

    with open(args.data, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise SystemExit("[FAIL] CSV 无表头")
        missing = [c for c in cols.values() if c and c not in reader.fieldnames]
        if missing:
            raise SystemExit(f"[FAIL] CSV 缺少列: {missing}；实际列: {reader.fieldnames}")
        rows = list(reader)
    if not rows:
        raise SystemExit("[FAIL] 数据为空")

    chans = []
    for r in rows:
        name = str(r.get(cols["channel"]) or "").strip()
        if not name:
            continue
        gmv = to_num(r.get(cols["gmv"])) if cols.get("gmv") else None
        margin_rate = to_ratio(r.get(cols.get("margin_rate", ""))) if cols.get("margin_rate") else None
        margin = to_num(r.get(cols.get("margin", ""))) if cols.get("margin") else None
        if margin_rate is None and margin is not None and gmv:
            margin_rate = margin / gmv
        ret = to_ratio(r.get(cols["return_rate"])) if cols.get("return_rate") else None
        cac_cost = to_num(r.get(cols["cac_cost"])) if cols.get("cac_cost") else None
        newc = to_num(r.get(cols["new_customers"])) if cols.get("new_customers") else None
        cac_direct = to_num(r.get(cols["cac"])) if cols.get("cac") else None
        if cac_cost is not None and newc:
            cac = cac_cost / newc
        else:
            cac = cac_direct
        inv = to_num(r.get(cols["inventory_days"])) if cols.get("inventory_days") else None
        yoy = to_ratio(r.get(cols["gmv_yoy"])) if cols.get("gmv_yoy") else None
        chans.append({"name": name, "gmv": gmv, "margin_rate": margin_rate, "return_rate": ret,
                      "cac": cac, "inventory_days": inv, "yoy": yoy, "strategic": name in strategic})

    total_gmv = sum(c["gmv"] or 0 for c in chans) or 1
    hhi = sum(((c["gmv"] or 0) / total_gmv * 100) ** 2 for c in chans)

    for c in chans:
        scores = {}
        # gmv_share：体量对数缩放 0.6 + 依赖惩罚 0.4
        if c["gmv"] is not None:
            share = c["gmv"] / total_gmv
            vol = clamp(math.log10(share * 100 + 1) / 2 * 100)  # share=100%→100, 1%→~30
            dep = clamp(100 - max(0, share - 0.6) / 0.4 * 100)  # 份额>60% 开始扣分
            scores["gmv_share"] = round(vol * 0.6 + dep * 0.4, 1)
        # margin_quality（比率口径：毛利率/基准，封顶 120%）
        if c["margin_rate"] is not None:
            b = bench["margin_rate"] if bench["margin_rate"] <= 1 else bench["margin_rate"] / 100
            scores["margin_quality"] = round(clamp(c["margin_rate"] / b * 100 / 1.2 if b > 0 else 0), 1)
        # return_rate（越低越好，比率口径）
        if c["return_rate"] is not None:
            rr = c["return_rate"] if c["return_rate"] <= 1 else c["return_rate"] / 100
            b = bench["return_rate"] if bench["return_rate"] <= 1 else bench["return_rate"] / 100
            scores["return_rate"] = round(clamp(b / rr * 100 / 1.5 if rr > 0 else 100), 1)
        # cac（越低越好）
        if c["cac"] is not None and c["cac"] > 0:
            scores["cac"] = round(clamp(bench["cac"] / c["cac"] * 100 / 1.5), 1)
        # inventory（越低越好）
        if c["inventory_days"] is not None and c["inventory_days"] > 0:
            scores["inventory"] = round(clamp(bench["inventory_days"] / c["inventory_days"] * 100 / 1.5), 1)
        # growth（比率口径：-20%→0 分，+30%→100 分线性）
        if c["yoy"] is not None:
            scores["growth"] = round(clamp((c["yoy"] + 0.2) / 0.5 * 100), 1)

        active_w = {d: weights[d] for d in scores}
        wsum = sum(active_w.values())
        total = round(sum(scores[d] * w for d, w in active_w.items()) / wsum, 1) if wsum else 0
        c["scores"] = scores
        c["total"] = total
        c["missing_dims"] = [d for d in DIMS if d not in scores]
        grade = ("S ≥85" if total >= 85 else "A 70-84" if total >= 70 else
                 "B 55-69" if total >= 55 else "C 40-54" if total >= 40 else "D <40")
        c["grade"] = grade

    os.makedirs(args.out, exist_ok=True)

    ranked = sorted([c for c in chans if not c["strategic"]], key=lambda x: -x["total"])
    for i, c in enumerate(ranked, start=1):
        c["rank"] = i
    for c in chans:
        c.setdefault("rank", "战略单列")

    p1 = os.path.join(args.out, "channel_scores.csv")
    with open(p1, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["渠道", "总分", "分级", "排名"] + [f"{d}得分" for d in DIMS] + ["缺失维度", "战略单列"])
        for c in chans:
            w.writerow([c["name"], c["total"], c["grade"], c["rank"]]
                       + [c["scores"].get(d, "") for d in DIMS]
                       + ["|".join(c["missing_dims"]), "是" if c["strategic"] else ""])

    p2 = os.path.join(args.out, "dimension_detail.csv")
    with open(p2, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["渠道", "维度", "原始值", "基准", "得分", "是否计权"])
        for c in chans:
            raw = {"gmv_share": c["gmv"], "margin_quality": c["margin_rate"],
                   "return_rate": c["return_rate"], "cac": c["cac"],
                   "inventory": c["inventory_days"], "growth": c["yoy"]}
            for d in DIMS:
                w.writerow([c["name"], d, raw[d] if raw[d] is not None else "",
                            bench.get({"margin_quality": "margin_rate", "return_rate": "return_rate",
                                       "cac": "cac", "inventory": "inventory_days"}.get(d, ""), ""),
                            c["scores"].get(d, ""), "是" if d in c["scores"] else "否"])

    alerts = []
    for c in chans:
        if c["strategic"]:
            continue
        if c["total"] < 40:
            alerts.append(f"{c['name']}: 总分 {c['total']}（D 级），进入问题渠道评估")
        if c["gmv"] is not None and c["gmv"] / total_gmv > 0.6:
            alerts.append(f"{c['name']}: GMV 占比 {c['gmv'] / total_gmv:.0%} > 60%，单渠道依赖风险")
        if "return_rate" in c["scores"] and c["scores"]["return_rate"] < 40:
            alerts.append(f"{c['name']}: 退货维度得分 {c['scores']['return_rate']}，联动 return-rate-clinic 诊断")
        if "cac" in c["scores"] and c["scores"]["cac"] < 40:
            alerts.append(f"{c['name']}: CAC 维度得分 {c['scores']['cac']}，买量效率预警")

    summary = {
        "channels": len(chans),
        "strategic_channels": sorted(strategic),
        "ranking": [{"channel": c["name"], "total": c["total"], "grade": c["grade"]} for c in ranked],
        "gmv_hhi": round(hhi, 1),
        "hhi_note": "HHI>2500 高集中（依赖风险）；1500-2500 中度；<1500 分散",
        "alerts": alerts,
        "data_gaps": {c["name"]: c["missing_dims"] for c in chans if c["missing_dims"]},
        "weights_used": weights,
        "benchmarks_used": bench,
        "outputs": [p1, p2],
    }
    p3 = os.path.join(args.out, "summary.json")
    with open(p3, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"[OK] 渠道 {len(chans)} 个（战略单列 {len(strategic & {c['name'] for c in chans})} 个）")
    print(f"[OK] 排名: " + " > ".join(f"{c['name']}({c['total']})" for c in ranked))
    print(f"[OK] GMV HHI {hhi:.0f}；预警 {len(alerts)} 条")
    print(f"[OK] 输出: {p3}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
