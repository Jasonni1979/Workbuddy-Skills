#!/usr/bin/env python3
"""daily_report.py — 电商日报/周报指标计算（仅标准库，非交互）。

用法:
    python daily_report.py --data daily.csv --config cfg.json --out ./out

data.csv 列（经 config.columns 映射）: date(必填), gmv(必填), orders, uv, qty, refund, channel(可选)
config:
{
  "columns": {...},
  "report": "daily" | "weekly",
  "as_of": "2026-09-04",          # 报告基准日（T-1）；weekly 时为周末日
  "month_target": 20000000,       # 可选
  "alert_threshold": 0.15
}

输出:
    metrics.csv      逐日: date,gmv,orders,uv,qty,refund,aov,cvr,refund_rate
    brief_data.json  当日值/环比/同比(有则算)/月累计/目标进度/时间进度/异动清单/渠道结构

设计约束: 无网络、无交互；as_of 当日无数据时报错退出（不用旧数据冒充）。
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import date as D
from datetime import datetime, timedelta


def pdate(raw):
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
        return 0.0
    try:
        return float(raw)
    except ValueError:
        return 0.0


def pct_change(cur, prev):
    if prev in (None, 0):
        return None
    return round((cur - prev) / prev, 4)


def main() -> int:
    ap = argparse.ArgumentParser(description="电商日报/周报指标计算")
    ap.add_argument("--data", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8"))
    cols = cfg["columns"]
    report = cfg.get("report", "daily")
    as_of = pdate(cfg.get("as_of", ""))
    if as_of is None:
        raise SystemExit("[FAIL] config.as_of 必填且为合法日期")
    thr = cfg.get("alert_threshold", 0.15)
    target = cfg.get("month_target")

    daily = defaultdict(lambda: defaultdict(float))
    chan = defaultdict(lambda: defaultdict(float))
    with open(a.data, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise SystemExit("[FAIL] 数据无表头")
        miss = [c for c in (cols["date"], cols["gmv"]) if c not in reader.fieldnames]
        if miss:
            raise SystemExit(f"[FAIL] 缺列 {miss}")
        for row in reader:
            d = pdate(row.get(cols["date"]))
            if d is None:
                continue
            for k in ("gmv", "orders", "uv", "qty", "refund"):
                if cols.get(k):
                    daily[d][k] += fnum(row.get(cols[k]))
            if cols.get("channel"):
                ch = (row.get(cols["channel"]) or "unknown").strip()
                chan[d][ch] += fnum(row.get(cols["gmv"]))
    if as_of not in daily:
        raise SystemExit(f"[FAIL] as_of={as_of} 当日无数据（数据最新到 {max(daily)}），"
                         f"请确认 T-1 数据是否到位，勿用旧数据冒充")

    os.makedirs(a.out, exist_ok=True)
    rows = []
    for d in sorted(daily):
        r = daily[d]
        rows.append({
            "date": d.isoformat(), "gmv": round(r["gmv"], 2), "orders": r["orders"],
            "uv": r["uv"], "qty": r["qty"], "refund": round(r["refund"], 2),
            "aov": round(r["gmv"] / r["orders"], 2) if r["orders"] else "",
            "cvr": round(r["orders"] / r["uv"], 4) if r["uv"] else "",
            "refund_rate": round(r["refund"] / r["gmv"], 4) if r["gmv"] else "",
        })
    out_m = os.path.join(a.out, "metrics.csv")
    with open(out_m, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def agg(days):
        t = defaultdict(float)
        for d in days:
            for k, v in daily[d].items():
                t[k] += v
        return t

    if report == "weekly":
        cur_days = [as_of - timedelta(days=i) for i in range(7)]
        prev_days = [as_of - timedelta(days=7 + i) for i in range(7)]
        yoy_days = [as_of.replace(year=as_of.year - 1) - timedelta(days=i) for i in range(7)]
        label = f"{cur_days[-1]} ~ {as_of}"
    else:
        cur_days, prev_days = [as_of], [as_of - timedelta(days=1)]
        yoy_days = [as_of.replace(year=as_of.year - 1)]
        label = as_of.isoformat()
    cur, prev = agg(cur_days), agg(prev_days)
    yoy = agg([d for d in yoy_days if d in daily]) or None

    mtd_days = [d for d in daily if d.year == as_of.year and d.month == as_of.month and d <= as_of]
    mtd = agg(mtd_days)
    month_days = 31 if as_of.month in (1, 3, 5, 7, 8, 10, 12) else 30 if as_of.month != 2 else \
        (29 if as_of.year % 4 == 0 and (as_of.year % 100 != 0 or as_of.year % 400 == 0) else 28)
    time_progress = round(len(mtd_days) / month_days, 4)

    alerts = []
    for k in ("gmv", "orders", "uv"):
        c, p = cur[k], prev[k]
        chg = pct_change(c, p)
        if chg is not None and abs(chg) >= thr:
            alerts.append({"metric": k, "cur": round(c, 2), "prev": round(p, 2), "change": chg})
    aov_cur = cur["gmv"] / cur["orders"] if cur["orders"] else None
    aov_prev = prev["gmv"] / prev["orders"] if prev["orders"] else None
    if aov_cur and aov_prev:
        chg = pct_change(aov_cur, aov_prev)
        if abs(chg) >= thr:
            alerts.append({"metric": "aov", "cur": round(aov_cur, 2),
                           "prev": round(aov_prev, 2), "change": chg})

    cur_chan = chan[cur_days[0]] if report == "daily" else \
        {c: sum(chan[d][c] for d in cur_days) for c in {c for d in cur_days for c in chan[d]}}
    prev_chan = chan[prev_days[0]] if report == "daily" else \
        {c: sum(chan[d][c] for d in prev_days) for c in {c for d in prev_days for c in chan[d]}}
    delta_total = cur["gmv"] - prev["gmv"]
    chan_struct = []
    if delta_total and (cur_chan or prev_chan):
        for c in sorted(set(cur_chan) | set(prev_chan)):
            dlt = cur_chan.get(c, 0) - prev_chan.get(c, 0)
            chan_struct.append({"channel": c, "delta": round(dlt, 2),
                                "contribution": round(dlt / delta_total, 4) if delta_total else None})
        chan_struct.sort(key=lambda x: -abs(x["delta"]))

    brief = {
        "report": report, "period": label, "as_of": as_of.isoformat(),
        "cur": {k: round(v, 2) for k, v in cur.items()},
        "prev": {k: round(v, 2) for k, v in prev.items()},
        "changes": {k: pct_change(cur[k], prev[k]) for k in ("gmv", "orders", "uv", "qty", "refund")},
        "yoy_changes": {k: pct_change(cur[k], yoy[k]) for k in ("gmv", "orders", "uv")} if yoy else None,
        "aov": {"cur": round(aov_cur, 2) if aov_cur else None,
                "prev": round(aov_prev, 2) if aov_prev else None},
        "cvr": {"cur": round(cur["orders"] / cur["uv"], 4) if cur["uv"] else None,
                "prev": round(prev["orders"] / prev["uv"], 4) if prev["uv"] else None},
        "mtd_gmv": round(mtd["gmv"], 2),
        "month_target": target,
        "target_progress": round(mtd["gmv"] / target, 4) if target else None,
        "time_progress": time_progress,
        "progress_gap": round(mtd["gmv"] / target - time_progress, 4) if target else None,
        "alerts": alerts,
        "channel_structure": chan_struct,
        "week_trend": [r for r in rows if r["date"] >= (as_of - timedelta(days=6)).isoformat()]
        if report == "weekly" else None,
        "outputs": [out_m],
    }
    out_b = os.path.join(a.out, "brief_data.json")
    with open(out_b, "w", encoding="utf-8") as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    print(f"[OK] {report} 基准日 {as_of}；GMV {cur['gmv']:.0f} 环比 {brief['changes']['gmv']}")
    if target:
        print(f"[OK] 月目标进度 {brief['target_progress']} vs 时间进度 {time_progress} "
              f"(差 {brief['progress_gap']})")
    print(f"[OK] 触发异动 {len(alerts)} 项: {[x['metric'] for x in alerts] or '无'}")
    print(f"[OK] 输出 {out_m} / {out_b}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
