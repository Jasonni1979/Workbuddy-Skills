#!/usr/bin/env python3
"""review_stats.py — 电商评论主题打标与统计（仅依赖 Python 标准库，非交互）。

用法:
    python review_stats.py --data reviews.csv --config config.json --out ./out

输入:
    --data   CSV 文件（UTF-8，含表头）。列名由 config 的 columns 映射指定。
    --config JSON 配置文件，字段:
        columns:      {"text": 评论列, "rating": 评分列(可选), "sku": SKU列(可选), "date": 日期列(可选)}
        themes:       {"主题名": ["关键词", ...], ...}   关键词命中即打标（子串匹配）
        rating_scale: 评分满分（默认 5，用于计算平均分口径说明）
        min_count:    计入问题清单的最小条数（默认 3）
    --out    输出目录（自动创建）

输出:
    theme_stats.csv     主题,命中条数,占比,平均分(如有评分),样例评论
    labeled_reviews.csv 原始行 + 命中的主题标签（多标签用 | 分隔）
    summary.json        总条数、有效率、主题分布、观察清单(未达阈值)

设计约束: 无网络、无交互输入、不连接数据库、不写输入目录。
已知局限: 关键词为子串匹配，不识别否定语境（"不黏腻"会命中"黏腻"）；
结果仅作初筛，需人工/Agent 复核样例评论后使用。
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter, defaultdict


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    if "columns" not in cfg or "text" not in cfg["columns"]:
        raise SystemExit("[FAIL] config.columns.text 必填（评论文本列名）")
    if "themes" not in cfg or not cfg["themes"]:
        raise SystemExit("[FAIL] config.themes 必填且不能为空")
    cfg.setdefault("rating_scale", 5)
    cfg.setdefault("min_count", 3)
    return cfg


def load_rows(path: str, columns: dict) -> list[dict]:
    if not path.lower().endswith(".csv"):
        raise SystemExit("[FAIL] --data 仅支持 CSV；Excel 请先另存为 CSV")
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise SystemExit("[FAIL] CSV 无表头")
        missing = [c for c in columns.values() if c and c not in reader.fieldnames]
        if missing:
            raise SystemExit(f"[FAIL] CSV 缺少列: {missing}；实际列: {reader.fieldnames}")
        return [row for row in reader]


def to_rating(value, scale: int):
    try:
        r = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if r < 0 or r > scale:
        return None
    return r


def anonymize(text: str, limit: int = 60) -> str:
    """截取关键句并去除疑似个人信息（11 位手机号、长数字订单号）。"""
    import re

    t = re.sub(r"1[3-9]\d{9}", "[手机]", text)
    t = re.sub(r"\d{8,}", "[编号]", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[: limit + 1] + ("…" if len(t) > limit else "")


def main() -> int:
    ap = argparse.ArgumentParser(description="电商评论主题打标与统计")
    ap.add_argument("--data", required=True, help="评论 CSV 文件路径")
    ap.add_argument("--config", required=True, help="配置 JSON 路径")
    ap.add_argument("--out", required=True, help="输出目录")
    args = ap.parse_args()

    cfg = load_config(args.config)
    cols = cfg["columns"]
    scale = cfg["rating_scale"]
    min_count = cfg["min_count"]

    rows = load_rows(args.data, cols)
    total = len(rows)
    if total == 0:
        raise SystemExit("[FAIL] 数据为空")

    themes: dict[str, list[str]] = cfg["themes"]
    theme_hits: Counter = Counter()
    theme_rating: defaultdict[str, list[float]] = defaultdict(list)
    theme_samples: defaultdict[str, list[str]] = defaultdict(list)
    labeled: list[dict] = []
    empty_text = 0

    for row in rows:
        text = (row.get(cols["text"]) or "").strip()
        if not text:
            empty_text += 1
            continue
        rating_col = cols.get("rating")
        rating = to_rating(row.get(rating_col), scale) if rating_col else None
        matched = [name for name, kws in themes.items() if any(kw in text for kw in kws)]
        for name in matched:
            theme_hits[name] += 1
            if rating is not None:
                theme_rating[name].append(rating)
            if len(theme_samples[name]) < 3:
                theme_samples[name].append(anonymize(text))
        out_row = dict(row)
        out_row["_themes"] = "|".join(matched)
        if rating is not None:
            out_row["_rating"] = rating
        labeled.append(out_row)

    valid = total - empty_text
    os.makedirs(args.out, exist_ok=True)

    # theme_stats.csv
    stats_path = os.path.join(args.out, "theme_stats.csv")
    with open(stats_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["主题", "命中条数", "占比(有效样本)", "平均分", "样例评论"])
        for name, cnt in theme_hits.most_common():
            ratings = theme_rating.get(name) or []
            avg = round(sum(ratings) / len(ratings), 2) if ratings else ""
            share = f"{cnt / valid * 100:.1f}%" if valid else "0%"
            w.writerow([name, cnt, share, avg, " / ".join(theme_samples[name])])

    # labeled_reviews.csv
    labeled_path = os.path.join(args.out, "labeled_reviews.csv")
    fieldnames = list(rows[0].keys()) + ["_themes"] + (["_rating"] if cols.get("rating") else [])
    with open(labeled_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(labeled)

    problems = {n: c for n, c in theme_hits.items() if c >= min_count}
    watchlist = {n: c for n, c in theme_hits.items() if c < min_count}
    summary = {
        "total_rows": total,
        "empty_text_rows": empty_text,
        "valid_rows": valid,
        "rating_scale": scale,
        "min_count_threshold": min_count,
        "theme_distribution": dict(theme_hits.most_common()),
        "problems": problems,
        "watchlist": watchlist,
        "outputs": [stats_path, labeled_path],
    }
    summary_path = os.path.join(args.out, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"[OK] 总条数 {total}，有效 {valid}，空文本 {empty_text}")
    print(f"[OK] 主题命中: {dict(theme_hits.most_common())}")
    print(f"[OK] 达到问题阈值(>= {min_count}): {list(problems.keys()) or '无'}")
    print(f"[OK] 观察清单(未达阈值): {list(watchlist.keys()) or '无'}")
    print(f"[OK] 输出: {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
