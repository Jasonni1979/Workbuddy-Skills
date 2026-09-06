#!/usr/bin/env python3
"""oneid_merge.py — 多源会员名单 One-ID 合并（仅 Python 标准库，非交互，不联网）。

用法:
    # 预览检查
    python oneid_merge.py --inspect src1.csv src2.csv
    # 执行合并
    python oneid_merge.py --sources src1.csv,src2.csv --config config.json --out ./out

config.json:
    sources: {文件名: {"channel": 渠道名, "columns": {逻辑字段: 实际列名}}}
             逻辑字段: phone/name/nickname/address/level/register_date/total_spend
    phone_hash: "none"（明文）| "md5"（已 MD5 密文，直接当键用）
    fuzzy: {"enable": true, "name_exact_required": true, "address_min_score": 0.6}
    field_priority: {字段: [渠道优先级列表] | "sum" | "max" | "min"}

输出（--out 目录）:
    oneid_master.csv    一人一行，one_id + 各渠道字段 + 来源渠道 + 置信度
    conflicts.csv       模糊匹配候选对（待人工/Agent 裁决，不自动合并）
    quality_report.json 合并率/重合率/字段缺失矩阵/质量风险
    masked_master.csv   手机号打码版（前3后4）

设计约束: 无网络、无交互、数据不出本机。
已知局限: 地址相似度为字符二元组 Jaccard（无分词库），对"同小区不同门牌"区分有限，
中置信度候选必须过冲突裁决；脱敏手机号（平台密文）跨源不可比，只能同源去重。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict


def try_read(path: str) -> tuple[list[dict], str]:
    for enc in ("utf-8-sig", "gbk", "utf-8"):
        try:
            with open(path, encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    raise ValueError("no header")
                return list(reader), enc
        except (UnicodeDecodeError, ValueError):
            continue
    raise SystemExit(f"[FAIL] {path}: 无法识别编码（试过 utf-8-sig/gbk/utf-8）")


def norm_phone(v: str, phone_hash: str) -> str:
    s = re.sub(r"[\s\-()]", "", str(v or ""))
    if not s:
        return ""
    if s.startswith("+86"):
        s = s[3:]
    if s.startswith("86") and len(s) == 13:
        s = s[2:]
    if phone_hash == "md5":
        return s.lower()  # 已是密文，统一大小写即可
    if re.fullmatch(r"1[3-9]\d{9}", s):
        return hashlib.md5(s.encode()).hexdigest()  # 明文统一转 MD5 作内部键，输出打码
    return ""  # 非合规手机号不作精确键


def bigrams(s: str) -> set:
    s = re.sub(r"\s+", "", str(s or ""))
    return {s[i:i + 2] for i in range(len(s) - 1)} if len(s) >= 2 else ({s} if s else set())


def addr_score(a: str, b: str) -> float:
    ba, bb = bigrams(a), bigrams(b)
    if not ba or not bb:
        return 0.0
    return len(ba & bb) / len(ba | bb)


def mask_phone(v: str) -> str:
    s = re.sub(r"\D", "", str(v or ""))
    if len(s) == 11:
        return s[:3] + "****" + s[7:]
    return (str(v or "")[:3] + "****") if v else ""


def main() -> int:
    ap = argparse.ArgumentParser(description="多源会员 One-ID 合并")
    ap.add_argument("--inspect", nargs="+", help="仅预览检查文件（编码/列/手机号合规率）")
    ap.add_argument("--sources", help="逗号分隔的源 CSV 列表")
    ap.add_argument("--config", help="配置 JSON")
    ap.add_argument("--out", help="输出目录")
    args = ap.parse_args()

    if args.inspect:
        for p in args.inspect:
            rows, enc = try_read(p)
            cols = rows[0].keys() if rows else []
            phone_col = next((c for c in cols if "手机" in c or "phone" in c.lower() or "mobile" in c.lower()), None)
            ok = 0
            if phone_col:
                ok = sum(1 for r in rows if re.fullmatch(r"1[3-9]\d{9}", re.sub(r"[\s\-]", "", str(r.get(phone_col) or ""))))
            print(f"[OK] {os.path.basename(p)}: 编码={enc} 行数={len(rows)} 疑似手机列={phone_col or '未识别'} "
                  f"明文合规={ok}/{len(rows)}")
            print(f"     列: {list(cols)}")
            if rows and re.search(r"合计|总计|汇总", str(list(rows[-1].values())[0] or "")):
                print("     [WARN] 末行疑似汇总行，合并时自动过滤")
        return 0

    if not (args.sources and args.config and args.out):
        raise SystemExit("[FAIL] 合并模式需要 --sources --config --out（预览用 --inspect）")

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)
    src_cfg = cfg.get("sources", {})
    phone_hash = cfg.get("phone_hash", "none")
    fuzzy = cfg.get("fuzzy", {"enable": True, "name_exact_required": True, "address_min_score": 0.6})
    fpriority = cfg.get("field_priority", {})
    files = [s.strip() for s in args.sources.split(",") if s.strip()]

    records = []  # 规范化记录列表
    for path in files:
        base = os.path.basename(path)
        if base not in src_cfg:
            raise SystemExit(f"[FAIL] config.sources 缺少 {base} 的配置")
        sc = src_cfg[base]
        channel, colmap = sc.get("channel", base), sc.get("columns", {})
        if "phone" not in colmap:
            raise SystemExit(f"[FAIL] {base}: columns.phone 必填")
        rows, enc = try_read(path)
        n_sum = 0
        for r in rows:
            first_val = str(list(r.values())[0] or "")
            if re.search(r"^(合计|总计|汇总)", first_val):
                n_sum += 1
                continue
            rec = {
                "_channel": channel, "_enc": enc,
                "phone_key": norm_phone(r.get(colmap["phone"]), phone_hash),
                "phone_raw": str(r.get(colmap["phone"]) or ""),
                "name": str(r.get(colmap.get("name", ""), "") or "").strip(),
                "nickname": str(r.get(colmap.get("nickname", ""), "") or "").strip(),
                "address": str(r.get(colmap.get("address", ""), "") or "").strip(),
                "level": str(r.get(colmap.get("level", ""), "") or "").strip(),
                "register_date": str(r.get(colmap.get("register_date", ""), "") or "").strip(),
                "total_spend": str(r.get(colmap.get("total_spend", ""), "") or "").strip(),
            }
            records.append(rec)
        print(f"[OK] {base}: {channel} 加载 {len(rows) - n_sum} 行（过滤汇总行 {n_sum}，编码 {enc}）")

    total = len(records)
    if total == 0:
        raise SystemExit("[FAIL] 无有效记录")

    # 1) 精确层：手机号键分组
    by_phone: defaultdict[str, list[dict]] = defaultdict(list)
    no_phone: list[dict] = []
    for rec in records:
        if rec["phone_key"]:
            by_phone[rec["phone_key"]].append(rec)
        else:
            no_phone.append(rec)

    clusters: list[list[dict]] = []
    conf = {}
    for k, group in by_phone.items():
        clusters.append(group)
        conf[k] = "高(手机号精确)"
    unmatched = list(no_phone)

    # 2) 模糊层：无手机号记录 与（无手机号记录 + 各精确簇代表）比对
    #    姓名一致 + 地址相似度达标 → 候选对进冲突裁决，不自动合并
    conflicts = []
    if fuzzy.get("enable", True):
        min_score = fuzzy.get("address_min_score", 0.6)
        # 精确簇代表记录（每簇取首条，用于跨"有手机号/无手机号"的候选比对）
        cluster_reps = [g[0] for g in clusters]
        candidates = [(a, b) for i, a in enumerate(unmatched) for b in unmatched[i + 1:]]
        candidates += [(a, rep) for a in unmatched for rep in cluster_reps]
        for a, b in candidates:
            if fuzzy.get("name_exact_required", True) and a["name"] != b["name"]:
                continue
            if not a["name"] and not b["name"]:
                continue
            sc = addr_score(a["address"], b["address"]) if a["address"] and b["address"] else (0.5 if a["nickname"] and a["nickname"] == b["nickname"] else 0.0)
            if sc >= min_score:
                conflicts.append({"a": a, "b": b, "score": round(sc, 3)})

    def pick(field: str, group: list[dict]) -> str:
        rule = fpriority.get(field)
        vals = [(g["_channel"], g[field]) for g in group if g[field]]
        if not vals:
            return ""
        if rule in ("sum", "max", "min") and field == "total_spend":
            nums = []
            for _, v in vals:
                try:
                    nums.append(float(str(v).replace(",", "")))
                except ValueError:
                    pass
            if nums:
                return str(round({"sum": sum, "max": max, "min": min}[rule](nums), 2))
        if rule == "min" and field == "register_date":
            ds = sorted(v for _, v in vals)
            return ds[0]
        if isinstance(rule, list):
            for ch in rule:
                for cch, v in vals:
                    if cch == ch:
                        return v
        return vals[0][1]

    os.makedirs(args.out, exist_ok=True)
    master_fields = ["one_id", "phone_masked", "phone_key_md5", "name", "nickname", "address",
                     "level", "register_date", "total_spend", "channels", "n_records", "confidence"]

    master_rows, masked_rows = [], []
    for idx, group in enumerate(sorted(clusters, key=lambda g: -len(g)), start=1):
        oid = f"OID{idx:06d}"
        key = group[0]["phone_key"]
        row = {
            "one_id": oid,
            "phone_masked": mask_phone(group[0]["phone_raw"]),
            "phone_key_md5": key,
            "name": pick("name", group), "nickname": pick("nickname", group),
            "address": pick("address", group), "level": pick("level", group),
            "register_date": pick("register_date", group), "total_spend": pick("total_spend", group),
            "channels": "|".join(sorted({g["_channel"] for g in group})),
            "n_records": len(group),
            "confidence": conf.get(key, "高(手机号精确)"),
        }
        master_rows.append(row)
        m = dict(row)
        m["phone_key_md5"] = ""  # 打码版不带匹配键
        masked_rows.append(m)

    # 未匹配记录单独成行（低置信）
    for rec in unmatched:
        if any(rec is c["a"] or rec is c["b"] for c in conflicts):
            continue  # 已进入冲突清单，等裁决，不单独成行
        oid = f"OID{len(master_rows) + 1:06d}"
        row = {
            "one_id": oid, "phone_masked": mask_phone(rec["phone_raw"]), "phone_key_md5": "",
            "name": rec["name"], "nickname": rec["nickname"], "address": rec["address"],
            "level": rec["level"], "register_date": rec["register_date"],
            "total_spend": rec["total_spend"], "channels": rec["_channel"],
            "n_records": 1, "confidence": "低(无手机号未匹配)",
        }
        master_rows.append(row)
        m = dict(row)
        masked_rows.append(m)

    p1 = os.path.join(args.out, "oneid_master.csv")
    with open(p1, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=master_fields)
        w.writeheader()
        w.writerows(master_rows)
    p4 = os.path.join(args.out, "masked_master.csv")
    with open(p4, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=master_fields)
        w.writeheader()
        w.writerows(masked_rows)

    p2 = os.path.join(args.out, "conflicts.csv")
    with open(p2, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["候选对ID", "A渠道", "A姓名", "A昵称", "A地址(截断)", "B渠道", "B姓名", "B昵称",
                    "B地址(截断)", "地址相似度", "建议", "裁决(人工填写:合并/拒绝)"])
        for i, c in enumerate(conflicts, start=1):
            sug = "建议合并" if c["score"] >= 0.85 and c["a"]["name"] == c["b"]["name"] else "需人工确认"
            w.writerow([f"C{i:04d}", c["a"]["_channel"], c["a"]["name"], c["a"]["nickname"],
                        c["a"]["address"][:30], c["b"]["_channel"], c["b"]["name"], c["b"]["nickname"],
                        c["b"]["address"][:30], c["score"], sug, ""])

    # 质量报告
    multi = sum(1 for r in master_rows if "|" in r["channels"])
    missing = defaultdict(lambda: defaultdict(int))
    chan_n = Counter()
    for rec in records:
        chan_n[rec["_channel"]] += 1
        for field in ("name", "address", "level", "register_date", "total_spend"):
            if not rec[field]:
                missing[rec["_channel"]][field] += 1
    phone_abuse = [r["phone_masked"] for r in master_rows if r["n_records"] > 5]
    quality = {
        "total_source_records": total,
        "oneid_count": len(master_rows),
        "merge_rate": round(1 - len(master_rows) / total, 4) if total else 0,
        "multi_channel_oneid": multi,
        "cross_channel_overlap_rate": round(multi / len(master_rows), 4) if master_rows else 0,
        "exact_match_clusters": len(clusters),
        "fuzzy_conflict_pairs": len(conflicts),
        "unmatched_low_confidence": sum(1 for r in master_rows if r["confidence"].startswith("低")),
        "records_per_channel": dict(chan_n),
        "field_missing_matrix": {ch: dict(m) for ch, m in missing.items()},
        "risk_signals": {
            "phone_with_gt5_records": phone_abuse[:20],
            "notice": "同手机号>5身份为羊毛党/公用号信号，需业务复核",
        },
        "outputs": [p1, p2, p4],
    }
    p3 = os.path.join(args.out, "quality_report.json")
    with open(p3, "w", encoding="utf-8") as f:
        json.dump(quality, f, ensure_ascii=False, indent=2)

    print(f"[OK] 源记录 {total} → One-ID {len(master_rows)}（合并率 {quality['merge_rate']:.1%}）")
    print(f"[OK] 跨渠道重合 One-ID {multi}（{quality['cross_channel_overlap_rate']:.1%}）")
    print(f"[OK] 精确簇 {len(clusters)}，模糊候选对 {len(conflicts)}（待裁决，未自动合并）")
    print(f"[OK] 输出: {p3}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
