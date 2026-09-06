#!/usr/bin/env python3
"""price_check.py — 全渠道到手价核算与破价识别（仅 Python 标准库，非交互）。

用法:
    python price_check.py --data channel_prices.csv --config config.json --out ./out

输入:
    --data   价格采集/成交明细 CSV（UTF-8，含表头），列名由 config.columns 映射
    --config JSON:
        columns: sku(必填) / channel(必填) / page_price(必填) / shop_coupon /
                 platform_coupon / promo_discount / gift_value / date / seller
        price_plate: {SKU: {"msrp": 吊牌价, "floor": {渠道: 授权底价, "默认": 兜底},
                    "promo_windows": [{"start","end","floor_all"}]}}
        gift_included: 赠品价值是否计入到手价折算（默认 true）
        tolerance: 底价容差比例（默认 0.02，2% 内不判违规，防汇率/凑整噪声）
    --out    输出目录（自动创建）

输出:
    effective_price.csv  SKU,渠道,日期,页面价,各项优惠,到手价,授权底价,判定
    violations.csv       低于底价记录（含破价幅度、是否在大促窗口、店铺）
    spread_analysis.csv  SKU×渠道 到手价价差矩阵（>5% 标渠道冲突风险）
    health_score.json    价盘健康度评分（底价合规40+价差秩序25+窜货控制20+机制稳定15）

到手价 = 页面价 − 店铺券 − 平台券 − 促销立减 − 赠品价值(gift_included 时)。
设计约束: 无网络、无交互。
已知局限: 只判"到手价<底价"，隐性破价（站外返现/客服改价/内购链接）与
平台补贴定性须由 Agent 复核；platform_coupon 默认视为平台补贴，单独列示供定性。
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    cols = cfg.get("columns", {})
    for k in ("sku", "channel", "page_price"):
        if k not in cols:
            raise SystemExit(f"[FAIL] config.columns.{k} 必填")
    if not cfg.get("price_plate"):
        raise SystemExit("[FAIL] config.price_plate 必填（无价盘表时先整理基线再运行）")
    cfg.setdefault("gift_included", True)
    cfg.setdefault("tolerance", 0.02)
    return cfg


def read_csv(path: str, cols: dict) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise SystemExit("[FAIL] CSV 无表头")
        missing = [c for c in cols.values() if c and c not in reader.fieldnames]
        if missing:
            raise SystemExit(f"[FAIL] CSV 缺少列: {missing}；实际列: {reader.fieldnames}")
        return list(reader)


def to_num(value) -> float:
    try:
        return float(str(value).replace(",", "").replace("￥", "").replace("¥", "").strip())
    except (TypeError, ValueError):
        return 0.0


def parse_date(value):
    s = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s[:10] if len(fmt) <= 10 else s[:19], fmt)
        except ValueError:
            continue
    return None


def floor_for(plate: dict, sku: str, channel: str, date) -> tuple[float | None, str]:
    """返回 (适用底价, 底价类型)。大促窗口优先。"""
    p = plate.get(sku)
    if not p:
        return None, "无价盘"
    if date:
        for w in p.get("promo_windows", []):
            ws, we = parse_date(w.get("start")), parse_date(w.get("end"))
            if ws and we and ws <= date <= we and w.get("floor_all") is not None:
                return float(w["floor_all"]), "大促授权窗口"
    floors = p.get("floor", {})
    if channel in floors:
        return float(floors[channel]), "渠道授权底价"
    if "默认" in floors:
        return float(floors["默认"]), "默认底价"
    return None, "无底价"


def main() -> int:
    ap = argparse.ArgumentParser(description="全渠道到手价核算")
    ap.add_argument("--data", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cfg = load_config(args.config)
    cols = cfg["columns"]
    plate = cfg["price_plate"]
    tol = cfg["tolerance"]
    gift_in = cfg["gift_included"]

    rows = read_csv(args.data, cols)
    if not rows:
        raise SystemExit("[FAIL] 数据为空")

    os.makedirs(args.out, exist_ok=True)
    eff_rows, violations = [], []
    sku_channel_price: defaultdict[tuple, list[float]] = defaultdict(list)
    n_checked = n_violation = n_promo_window = n_no_plate = 0

    for r in rows:
        sku = str(r.get(cols["sku"]) or "").strip()
        ch = str(r.get(cols["channel"]) or "").strip()
        if not sku or not ch:
            continue
        page = to_num(r.get(cols["page_price"]))
        shop_c = to_num(r.get(cols.get("shop_coupon"))) if cols.get("shop_coupon") else 0.0
        plat_c = to_num(r.get(cols.get("platform_coupon"))) if cols.get("platform_coupon") else 0.0
        promo = to_num(r.get(cols.get("promo_discount"))) if cols.get("promo_discount") else 0.0
        gift = to_num(r.get(cols.get("gift_value"))) if cols.get("gift_value") and gift_in else 0.0
        date = parse_date(r.get(cols.get("date"))) if cols.get("date") else None
        seller = str(r.get(cols.get("seller"), "") or "").strip() if cols.get("seller") else ""

        eff = round(page - shop_c - plat_c - promo - gift, 2)
        merchant_eff = round(eff + plat_c, 2)  # 商家实收口径（平台券为平台补贴时）
        floor, ftype = floor_for(plate, sku, ch, date)
        n_checked += 1
        if floor is None:
            n_no_plate += 1
            verdict = "无价盘基线"
        elif ftype == "大促授权窗口":
            n_promo_window += 1
            verdict = "大促窗口内合规" if merchant_eff >= floor * (1 - tol) else "窗口内仍破价"
        else:
            verdict = "合规" if merchant_eff >= floor * (1 - tol) else "低于底价"

        eff_rows.append({
            "sku": sku, "channel": ch, "date": str(date.date()) if date else "",
            "seller": seller, "page_price": page, "shop_coupon": shop_c,
            "platform_coupon": plat_c, "promo_discount": promo, "gift_value": gift,
            "effective_price": eff, "merchant_effective": merchant_eff,
            "floor": floor if floor is not None else "", "floor_type": ftype, "verdict": verdict,
        })
        sku_channel_price[(sku, ch)].append(eff)

        if verdict in ("低于底价", "窗口内仍破价"):
            n_violation += 1
            violations.append({
                "sku": sku, "channel": ch, "seller": seller,
                "date": str(date.date()) if date else "",
                "effective_price": eff, "merchant_effective": merchant_eff,
                "floor": floor, "floor_type": ftype,
                "breach_amount": round(floor - merchant_eff, 2),
                "breach_pct": f"{(floor - merchant_eff) / floor * 100:.1f}%" if floor else "",
                "platform_coupon_part": plat_c,
                "agent_review": "待定性(真破价/平台补贴/窜货/机制漏洞)",
            })

    # effective_price.csv
    p1 = os.path.join(args.out, "effective_price.csv")
    with open(p1, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(eff_rows[0].keys()))
        w.writeheader()
        w.writerows(eff_rows)

    # violations.csv
    p2 = os.path.join(args.out, "violations.csv")
    vfields = list(violations[0].keys()) if violations else ["sku", "channel", "seller", "date",
        "effective_price", "merchant_effective", "floor", "floor_type", "breach_amount",
        "breach_pct", "platform_coupon_part", "agent_review"]
    with open(p2, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=vfields)
        w.writeheader()
        w.writerows(violations)

    # spread_analysis.csv：SKU×渠道价差
    p3 = os.path.join(args.out, "spread_analysis.csv")
    skus = sorted({s for s, _ in sku_channel_price})
    channels = sorted({c for _, c in sku_channel_price})
    conflicts = []
    with open(p3, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["SKU"] + [f"{c}均价" for c in channels] + ["最大价差%", "冲突风险"])
        for sku in skus:
            avgs = []
            for c in channels:
                vals = sku_channel_price.get((sku, c))
                avgs.append(round(sum(vals) / len(vals), 2) if vals else "")
            nums = [a for a in avgs if a != ""]
            spread_pct = ""
            risk = ""
            if len(nums) >= 2 and min(nums) > 0:
                sp = (max(nums) - min(nums)) / min(nums) * 100
                spread_pct = f"{sp:.1f}%"
                if sp > 5:
                    risk = "价差>5% 渠道冲突风险"
                    conflicts.append((sku, round(sp, 1)))
            w.writerow([sku] + avgs + [spread_pct, risk])

    # health_score.json
    compliance = round((1 - n_violation / n_checked) * 40, 1) if n_checked else 0
    spread_score = round((1 - min(len(conflicts) / max(len(skus), 1), 1)) * 25, 1)
    diversion_proxy = round((1 - min(n_violation / max(n_checked, 1), 1)) * 20, 1)
    stability = round((1 - min(len(conflicts) * 0.1, 1)) * 15, 1)
    health = {
        "records_checked": n_checked,
        "no_price_plate_records": n_no_plate,
        "promo_window_records": n_promo_window,
        "violations": n_violation,
        "conflict_skus": [f"{s}(价差{p}%)" for s, p in conflicts[:20]],
        "score": {
            "底价合规(40)": compliance,
            "价差秩序(25)": spread_score,
            "窜货控制代理(20)": diversion_proxy,
            "机制稳定(15)": stability,
            "总分": round(compliance + spread_score + diversion_proxy + stability, 1),
        },
        "score_notice": "窜货控制用破价率代理（真窜货判定需批号溯源证据）；权重口径见 references/price-framework.md",
        "outputs": [p1, p2, p3],
    }
    p4 = os.path.join(args.out, "health_score.json")
    with open(p4, "w", encoding="utf-8") as f:
        json.dump(health, f, ensure_ascii=False, indent=2)

    print(f"[OK] 核算 {n_checked} 条，违规候选 {n_violation} 条（待 Agent 定性），无价盘 {n_no_plate} 条")
    print(f"[OK] 价差冲突 SKU {len(conflicts)} 个")
    print(f"[OK] 健康度总分 {health['score']['总分']}")
    print(f"[OK] 输出: {p4}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
