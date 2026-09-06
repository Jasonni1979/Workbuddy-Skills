#!/usr/bin/env python3
"""ticket_stats.py — 客服工单主题打标、SLA 统计与升级预警（仅 Python 标准库，非交互）。

用法:
    python ticket_stats.py --data tickets.csv --config config.json --out ./out

输入:
    --data   CSV（UTF-8，含表头）。列名由 config.columns 映射。
    --config JSON:
        columns: text(会话文本,必填) / created / first_reply / resolved /
                 channel / csat / escalated / agent（其余可选）
        themes:  {"主题": ["关键词", ...], ...}（子串匹配打标）
        sla:     {"first_reply_minutes": 5, "resolve_hours": 24}（可选）
        escalation_keywords: ["投诉", "曝光", ...]（可选，命中即入升级清单待复核）
    --out    输出目录（自动创建）

输出:
    ticket_stats.csv      主题,条数,占比,平均首响(分),平均满意度,样例(脱敏)
    sla_report.csv        维度(总体/渠道/客服),样本数,首响达标率,解决达标率,P50/P90解决时长
    escalation_list.csv   工单行 + 命中的升级关键词（须人工复核）
    labeled_tickets.csv   原始行 + _themes + _first_reply_min + _resolve_h
    summary.json          汇总

时间字段兼容: ISO(2026-01-01T10:00:00)、空格分隔(2026-01-01 10:00:00)、
Excel 序列号(45658.5)。设计约束: 无网络、无交互、不写输入目录。
已知局限: 关键词子串匹配不识别否定语境；升级关键词命中≠真实升级意图，需人工复核。
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    if "text" not in cfg.get("columns", {}):
        raise SystemExit("[FAIL] config.columns.text 必填（会话文本列名）")
    cfg.setdefault("themes", {})
    cfg.setdefault("sla", {})
    cfg.setdefault("escalation_keywords", [])
    return cfg


def parse_dt(value):
    """兼容 ISO / 'YYYY-MM-DD HH:MM:SS' / Excel 序列号。失败返回 None。"""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S",
                "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return datetime(1899, 12, 30) + timedelta(days=float(s))
    except (ValueError, OverflowError):
        return None


def to_float(value):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def anonymize(text: str, limit: int = 60) -> str:
    t = re.sub(r"1[3-9]\d{9}", "[手机]", text)
    t = re.sub(r"\d{8,}", "[编号]", t)
    t = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[邮箱]", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[: limit + 1] + ("…" if len(t) > limit else "")


def percentile(sorted_vals, p):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    return round(sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo), 2)


def main() -> int:
    ap = argparse.ArgumentParser(description="客服工单主题打标与 SLA 统计")
    ap.add_argument("--data", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cfg = load_config(args.config)
    cols = cfg["columns"]
    themes: dict[str, list[str]] = cfg["themes"]
    sla = cfg["sla"]
    esc_kws: list[str] = cfg["escalation_keywords"]

    with open(args.data, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise SystemExit("[FAIL] CSV 无表头")
        missing = [c for c in cols.values() if c and c not in reader.fieldnames]
        if missing:
            raise SystemExit(f"[FAIL] CSV 缺少列: {missing}；实际列: {reader.fieldnames}")
        rows = list(reader)
    total = len(rows)
    if total == 0:
        raise SystemExit("[FAIL] 数据为空")

    theme_hits: Counter = Counter()
    theme_first: defaultdict[str, list[float]] = defaultdict(list)
    theme_csat: defaultdict[str, list[float]] = defaultdict(list)
    theme_samples: defaultdict[str, list[str]] = defaultdict(list)

    dim_stats: dict[str, dict] = {"总体": {"firsts": [], "resolves": []}}
    dim_first_ok: Counter = Counter()
    dim_resolve_ok: Counter = Counter()
    dim_n: Counter = Counter()

    escalations: list[dict] = []
    labeled: list[dict] = []
    no_time = 0

    for row in rows:
        text = (row.get(cols["text"]) or "").strip()
        matched = [n for n, kws in themes.items() if any(k in text for k in kws)]
        for n in matched:
            theme_hits[n] += 1
            if len(theme_samples[n]) < 3:
                theme_samples[n].append(anonymize(text))

        created = parse_dt(row.get(cols.get("created"))) if cols.get("created") else None
        first = parse_dt(row.get(cols.get("first_reply"))) if cols.get("first_reply") else None
        resolved = parse_dt(row.get(cols.get("resolved"))) if cols.get("resolved") else None
        fr_min = round((first - created).total_seconds() / 60, 2) if created and first else None
        rs_h = round((resolved - created).total_seconds() / 3600, 2) if created and resolved else None
        if fr_min is None and rs_h is None:
            no_time += 1

        csat = to_float(row.get(cols.get("csat"))) if cols.get("csat") else None
        for n in matched:
            if fr_min is not None:
                theme_first[n].append(fr_min)
            if csat is not None:
                theme_csat[n].append(csat)

        # 维度聚合：总体 + 渠道 + 客服
        dims = {"总体": "总体"}
        if cols.get("channel") and (row.get(cols["channel"]) or "").strip():
            dims[f"渠道:{row[cols['channel']].strip()}"] = "channel"
        if cols.get("agent") and (row.get(cols["agent"]) or "").strip():
            dims[f"客服:{row[cols['agent']].strip()}"] = "agent"
        for dname in dims:
            dim_stats.setdefault(dname, {"firsts": [], "resolves": []})
            dim_n[dname] += 1
            if fr_min is not None:
                dim_stats[dname]["firsts"].append(fr_min)
                if sla.get("first_reply_minutes") is not None:
                    dim_first_ok[dname] += 1 if fr_min <= sla["first_reply_minutes"] else 0
            if rs_h is not None:
                dim_stats[dname]["resolves"].append(rs_h)
                if sla.get("resolve_hours") is not None:
                    dim_resolve_ok[dname] += 1 if rs_h <= sla["resolve_hours"] else 0

        # 升级预警：关键词命中 或 escalated 标记为真
        esc_flag = str(row.get(cols.get("escalated"), "")).strip().lower() in ("1", "true", "yes", "是", "y")
        hit_kws = [k for k in esc_kws if k in text]
        if hit_kws or esc_flag:
            e = dict(row)
            e["_escalation_keywords"] = "|".join(hit_kws)
            e["_flagged"] = bool(esc_flag)
            e["_text_sample"] = anonymize(text, 40)
            escalations.append(e)

        out_row = dict(row)
        out_row["_themes"] = "|".join(matched)
        if fr_min is not None:
            out_row["_first_reply_min"] = fr_min
        if rs_h is not None:
            out_row["_resolve_h"] = rs_h
        labeled.append(out_row)

    os.makedirs(args.out, exist_ok=True)

    # ticket_stats.csv
    p1 = os.path.join(args.out, "ticket_stats.csv")
    with open(p1, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["主题", "条数", "占比", "平均首响(分)", "平均满意度", "样例(脱敏)"])
        for n, c in theme_hits.most_common():
            fr = round(sum(theme_first[n]) / len(theme_first[n]), 2) if theme_first[n] else ""
            cs = round(sum(theme_csat[n]) / len(theme_csat[n]), 2) if theme_csat[n] else ""
            w.writerow([n, c, f"{c / total * 100:.1f}%", fr, cs, " / ".join(theme_samples[n])])

    # sla_report.csv
    p2 = os.path.join(args.out, "sla_report.csv")
    with open(p2, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["维度", "样本数", "首响样本", "首响达标率", "解决样本", "解决达标率",
                    "首响P50(分)", "首响P90(分)", "解决P50(h)", "解决P90(h)"])
        for dname, st in dim_stats.items():
            firsts = sorted(st["firsts"])
            resolves = sorted(st["resolves"])
            fr_rate = (f"{dim_first_ok[dname] / len(firsts) * 100:.1f}%"
                       if firsts and sla.get("first_reply_minutes") is not None else "")
            rs_rate = (f"{dim_resolve_ok[dname] / len(resolves) * 100:.1f}%"
                       if resolves and sla.get("resolve_hours") is not None else "")
            w.writerow([dname, dim_n[dname], len(firsts), fr_rate, len(resolves), rs_rate,
                        percentile(firsts, 0.5) if firsts else "",
                        percentile(firsts, 0.9) if firsts else "",
                        percentile(resolves, 0.5) if resolves else "",
                        percentile(resolves, 0.9) if resolves else ""])

    # escalation_list.csv
    p3 = os.path.join(args.out, "escalation_list.csv")
    if escalations:
        fieldnames = list(escalations[0].keys())
    else:
        fieldnames = list(rows[0].keys()) + ["_escalation_keywords", "_flagged", "_text_sample"]
    with open(p3, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(escalations)

    # labeled_tickets.csv
    p4 = os.path.join(args.out, "labeled_tickets.csv")
    lf = list(rows[0].keys()) + ["_themes", "_first_reply_min", "_resolve_h"]
    with open(p4, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=lf, extrasaction="ignore")
        w.writeheader()
        w.writerows(labeled)

    summary = {
        "total_rows": total,
        "rows_without_time": no_time,
        "theme_distribution": dict(theme_hits.most_common()),
        "sla_config": sla,
        "escalation_candidates": len(escalations),
        "escalation_keyword_only": sum(1 for e in escalations if not e["_flagged"]),
        "outputs": [p1, p2, p3, p4],
        "notice": "升级清单为关键词初筛，必须人工/Agent 逐条复核后再定级",
    }
    p5 = os.path.join(args.out, "summary.json")
    with open(p5, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"[OK] 总工单 {total}，无时间字段 {no_time}")
    print(f"[OK] 主题命中: {dict(theme_hits.most_common()) or '无'}")
    print(f"[OK] 升级候选(待复核): {len(escalations)}")
    print(f"[OK] 输出: {p5}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
