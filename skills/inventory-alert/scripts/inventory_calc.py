#!/usr/bin/env python3
"""inventory_calc.py — 库存周转与补货指标计算（仅标准库，非交互）。

用法:
    python inventory_calc.py --stock stock.csv --sales sales.csv --config cfg.json --out ./out

stock.csv 列（经 config.columns.stock 映射）: sku, on_hand, in_transit, age_days(可选), cost(可选)
sales.csv 列（经 config.columns.sales 映射）: sku, date, qty（日粒度，可多平台多行，脚本按 sku+date 聚合）

config:
{
  "columns": {...},
  "lead_time_days": 21,            # 补货提前期
  "service_level_z": 1.65,         # 95% 服务水平
  "sales_window_days": 30,         # 日均销计算窗口
  "review_period_days": 7,         # 订货审查周期（补货量=目标水位-现有）
  "turnover_target_days": 90,      # 周转目标天数
  "slow_moving": {"no_sale_days": 90, "turnover_days_max": 180},
  "promo": {"enabled": false, "days": 15, "uplift": 3.0}
}

输出:
    inventory_metrics.csv  逐 SKU 指标与风险分级、建议补货量
    summary.json           分级计数、资金占用、断货敞口

公式（references/inventory-model.md）:
    日均销 = 窗口内销量 / 窗口天数（无销日按 0 计入标准差）
    安全库存 = z * 日销标准差 * sqrt(提前期)
    补货点   = 日均销 * 提前期 + 安全库存
    目标水位 = 日均销 * (提前期 + 审查周期) + 安全库存 (+ 大促增量)
    可售天数 = (在库 + 在途) / 日均销
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta


def parse_date(raw):
    raw = (raw or "").strip()
    for f in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(raw, f).date()
        except ValueError:
            continue
    return None


def fnum(raw):
    raw = (raw or "").strip().replace(",", "")
    if raw in ("", "-", "--"):
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="库存周转与补货指标计算")
    ap.add_argument("--stock", required=True)
    ap.add_argument("--sales", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    cfg = json.load(open(a.config, encoding="utf-8"))
    cs, cl = cfg["columns"]["stock"], cfg["columns"]["sales"]
    lead = cfg.get("lead_time_days", 21)
    z = cfg.get("service_level_z", 1.65)
    window = cfg.get("sales_window_days", 30)
    review = cfg.get("review_period_days", 7)
    target_turn = cfg.get("turnover_target_days", 90)
    slow = cfg.get("slow_moving", {"no_sale_days": 90, "turnover_days_max": 180})
    promo = cfg.get("promo", {"enabled": False})

    # 销量聚合: sku -> {date: qty}
    daily = defaultdict(lambda: defaultdict(float))
    bad_dates = 0
    with open(a.sales, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            sku = (row.get(cl["sku"]) or "").strip()
            d = parse_date(row.get(cl["date"]))
            q = fnum(row.get(cl["qty"])) or 0.0
            if not sku or d is None:
                bad_dates += 1
                continue
            daily[sku][d] += q

    os.makedirs(a.out, exist_ok=True)
    metrics, summary_counts = [], defaultdict(int)
    capital_total = capital_risk = capital_slow = 0.0

    with open(a.stock, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            sku = (row.get(cs["sku"]) or "").strip()
            if not sku:
                continue
            on_hand = fnum(row.get(cs["on_hand"])) or 0.0
            in_transit = fnum(row.get(cs.get("in_transit"))) or 0.0 if cs.get("in_transit") else 0.0
            age = fnum(row.get(cs.get("age_days"))) if cs.get("age_days") else None
            cost = fnum(row.get(cs.get("cost"))) if cs.get("cost") else None

            hist = daily.get(sku, {})
            if not hist:
                max_d = None
            else:
                max_d = max(hist)
            end = max_d or datetime.now().date()
            start = end - timedelta(days=window - 1)
            qty_window = sum(q for d, q in hist.items() if start <= d <= end)
            qty_90 = sum(q for d, q in hist.items() if end - timedelta(days=89) <= d <= end)
            days = [hist.get(start + timedelta(days=i), 0.0) for i in range(window)]
            avg = qty_window / window
            var = sum((x - avg) ** 2 for x in days) / window
            std = math.sqrt(var)

            ss = z * std * math.sqrt(lead)
            rop = avg * lead + ss
            promo_qty = (promo.get("uplift", 1.0) * avg * promo.get("days", 0)) if promo.get("enabled") else 0.0
            target = avg * (lead + review) + ss + promo_qty
            available = on_hand + in_transit
            cover = available / avg if avg > 0 else float("inf")
            turnover = on_hand / avg if avg > 0 else float("inf")
            order_qty = max(0.0, math.ceil(target - available)) if available <= rop + promo_qty else 0.0

            # 风险分级
            if qty_90 == 0:
                grade = "black"
            elif cover < lead:
                grade = "red"
            elif cover < lead * 1.5:
                grade = "orange"
            elif (turnover > slow.get("turnover_days_max", 180)) or \
                 (age is not None and age > slow.get("no_sale_days", 90) and avg == 0):
                grade = "yellow"
            elif cover > target_turn * 2:
                grade = "yellow"
            else:
                grade = "green"
            summary_counts[grade] += 1
            if cost is not None:
                capital_total += on_hand * cost
                if grade in ("red", "orange"):
                    capital_risk += order_qty * cost
                if grade in ("yellow", "black"):
                    capital_slow += on_hand * cost

            metrics.append({
                "sku": sku, "on_hand": on_hand, "in_transit": in_transit,
                "age_days": age if age is not None else "", "cost": cost if cost is not None else "",
                "daily_avg": round(avg, 2), "daily_std": round(std, 2),
                "sales_30d": round(qty_window, 1), "sales_90d": round(qty_90, 1),
                "turnover_days": round(turnover, 1) if turnover != float("inf") else "inf",
                "cover_days": round(cover, 1) if cover != float("inf") else "inf",
                "safety_stock": round(ss, 1), "reorder_point": round(rop, 1),
                "target_level": round(target, 1), "suggested_order_qty": order_qty,
                "promo_demand": round(promo_qty, 1), "risk_grade": grade,
            })

    metrics.sort(key=lambda r: ({"red": 0, "orange": 1, "yellow": 2, "black": 3, "green": 4}[r["risk_grade"]],
                                -((r["cost"] or 0) * r["daily_avg"])))
    out_m = os.path.join(a.out, "inventory_metrics.csv")
    with open(out_m, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(metrics[0].keys()) if metrics else ["sku"])
        w.writeheader()
        w.writerows(metrics)
    summary = {
        "params": {"lead_time_days": lead, "service_level_z": z, "sales_window_days": window,
                   "review_period_days": review, "turnover_target_days": target_turn,
                   "slow_moving": slow, "promo": promo},
        "grade_counts": dict(summary_counts),
        "sku_total": len(metrics),
        "bad_sales_rows": bad_dates,
        "capital_total": round(capital_total, 2),
        "stockout_risk_capital": round(capital_risk, 2),
        "slow_dead_capital": round(capital_slow, 2),
        "outputs": [out_m],
    }
    out_s = os.path.join(a.out, "summary.json")
    with open(out_s, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"[OK] SKU {len(metrics)} 个；分级 {dict(summary_counts)}")
    print(f"[OK] 库存资金占用 {capital_total:.0f}；断货风险敞口 {capital_risk:.0f}；滞销死库存占用 {capital_slow:.0f}")
    print(f"[OK] 销量表无法解析行 {bad_dates}")
    print(f"[OK] 输出 {out_m} / {out_s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
