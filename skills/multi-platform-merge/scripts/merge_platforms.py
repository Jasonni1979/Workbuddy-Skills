#!/usr/bin/env python3
"""merge_platforms.py — 多平台销售数据字段映射与合并（仅标准库，非交互）。

用法:
    预览:  python merge_platforms.py --inspect a.csv b.csv ...
    合并:  python merge_platforms.py --config mappings.json --out ./out

mappings.json 为数组，每项:
{
  "platform": "tmall",
  "file": "tmall_sales.csv",
  "encoding": "utf-8-sig",          # 可选，默认 utf-8-sig
  "delimiter": ",",                 # 可选
  "granularity": "daily",           # daily/weekly/monthly/order，仅记录
  "columns": {"date":..., "sku":..., "sku_name":..., "gmv":..., "qty":...,
              "refund":..., "uv":..., "orders":...},   # date 必填，其余可选
  "date_format": "%Y-%m-%d",        # 可选，失败时回退常见格式
  "amount_unit": "yuan",            # yuan | cent（cent 自动 /100）
  "dedup_keys": ["date", "sku"]     # 可选；同键重复行保留首行并计数
}

输出:
    merged_sales.csv   date,platform,sku,sku_name,gmv,qty,refund,uv,orders,net_gmv
    caliber_dict.csv   platform,standard_field,source_column,transform
    quality_report.json 每文件行数/空值/日期失败/重复键/金额异常清单

设计约束: 无网络、无交互、不写输入目录；被过滤行全部计入质量报告。
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime

DATE_FALLBACKS = ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%Y-%m-%d %H:%M:%S", "%Y年%m月%d日"]
NUM_FIELDS = ["gmv", "qty", "refund", "uv", "orders"]


def parse_date(raw: str, fmt: str | None):
    raw = (raw or "").strip()
    if not raw:
        return None
    for f in ([fmt] if fmt else []) + DATE_FALLBACKS:
        try:
            return datetime.strptime(raw, f).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_num(raw, unit: str):
    raw = (raw or "").strip().replace(",", "").replace("¥", "").replace("￥", "")
    if raw in ("", "-", "--"):
        return None
    try:
        v = float(raw)
    except ValueError:
        return None
    if unit == "cent":
        v = v / 100.0
    return round(v, 2)


def inspect(paths: list[str]) -> int:
    for p in paths:
        print(f"\n===== {p} =====")
        for enc in ("utf-8-sig", "gbk", "utf-8"):
            try:
                with open(p, encoding=enc, newline="") as f:
                    reader = csv.reader(f)
                    rows = [next(reader) for _ in range(6)]
                print(f"[编码] {enc}")
                break
            except (UnicodeDecodeError, StopIteration):
                continue
        else:
            print("[FAIL] 无法识别编码"); continue
        header, sample = rows[0], rows[1:]
        print(f"[表头] {header}")
        for r in sample[:5]:
            print("  ", r)
    return 0


def run(config_path: str, out_dir: str) -> int:
    with open(config_path, encoding="utf-8") as f:
        mappings = json.load(f)
    if not isinstance(mappings, list) or not mappings:
        raise SystemExit("[FAIL] config 必须是非空数组")

    os.makedirs(out_dir, exist_ok=True)
    merged: list[dict] = []
    caliber: list[dict] = []
    quality: dict = {"files": [], "total_merged_rows": 0}

    for m in mappings:
        plat = m.get("platform") or os.path.basename(m.get("file", "unknown"))
        path = m["file"]
        cols = m.get("columns", {})
        if "date" not in cols:
            raise SystemExit(f"[FAIL] {plat}: columns.date 必填")
        enc = m.get("encoding", "utf-8-sig")
        unit = m.get("amount_unit", "yuan")
        dedup = m.get("dedup_keys") or []
        fmt = m.get("date_format")

        rep = {"platform": plat, "file": path, "rows": 0, "kept": 0,
               "date_parse_fail": 0, "null_counts": {}, "dup_keys_dropped": 0,
               "amount_anomalies": []}
        seen = set()
        with open(path, encoding=enc, newline="") as f:
            reader = csv.DictReader(f, delimiter=m.get("delimiter", ","))
            if reader.fieldnames is None:
                raise SystemExit(f"[FAIL] {plat}: 文件无表头")
            missing = [c for c in cols.values() if c not in reader.fieldnames]
            if missing:
                raise SystemExit(f"[FAIL] {plat}: 缺少列 {missing}；实际 {reader.fieldnames}")
            for row in reader:
                rep["rows"] += 1
                d = parse_date(row.get(cols["date"]), fmt)
                if d is None:
                    rep["date_parse_fail"] += 1
                    continue
                rec = {"date": d, "platform": plat,
                       "sku": (row.get(cols.get("sku")) or "").strip() if cols.get("sku") else "",
                       "sku_name": (row.get(cols.get("sku_name")) or "").strip() if cols.get("sku_name") else ""}
                for nf in NUM_FIELDS:
                    src = cols.get(nf)
                    # 单位换算仅适用于金额字段（gmv/refund），件数/人数不换算
                    unit_nf = unit if nf in ("gmv", "refund") else "yuan"
                    rec[nf] = parse_num(row.get(src), unit_nf) if src else None
                    if src and rec[nf] is None and (row.get(src) or "").strip() not in ("", "-", "--"):
                        rep["null_counts"][nf] = rep["null_counts"].get(nf, 0) + 1
                if dedup:
                    key = tuple(rec.get(k, "") for k in dedup)
                    if key in seen:
                        rep["dup_keys_dropped"] += 1
                        continue
                    seen.add(key)
                for nf in ("gmv", "refund"):
                    v = rec.get(nf)
                    if v is not None and (v < 0 or v > 10_000_000):
                        rep["amount_anomalies"].append(
                            {"date": d, "field": nf, "value": v,
                             "sku": rec["sku"] or rec["sku_name"]})
                rec["net_gmv"] = round((rec["gmv"] or 0) - (rec["refund"] or 0), 2) \
                    if rec["gmv"] is not None else None
                merged.append(rec)
                rep["kept"] += 1
        quality["files"].append(rep)
        for std, src in cols.items():
            transform = "cent->yuan(/100)" if (unit == "cent" and std in ("gmv", "refund")) \
                else ("date->%Y-%m-%d" if std == "date" else "direct")
            caliber.append({"platform": plat, "standard_field": std,
                            "source_column": src, "transform": transform})

    merged.sort(key=lambda r: (r["date"], r["platform"], r["sku"]))
    out_merged = os.path.join(out_dir, "merged_sales.csv")
    with open(out_merged, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "platform", "sku", "sku_name",
                                          "gmv", "qty", "refund", "uv", "orders", "net_gmv"])
        w.writeheader()
        w.writerows(merged)
    out_cal = os.path.join(out_dir, "caliber_dict.csv")
    with open(out_cal, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["platform", "standard_field", "source_column", "transform"])
        w.writeheader()
        w.writerows(caliber)
    quality["total_merged_rows"] = len(merged)
    quality["outputs"] = [out_merged, out_cal]
    out_q = os.path.join(out_dir, "quality_report.json")
    with open(out_q, "w", encoding="utf-8") as f:
        json.dump(quality, f, ensure_ascii=False, indent=2)

    print(f"[OK] 合并行数 {len(merged)} -> {out_merged}")
    for rep in quality["files"]:
        print(f"[OK] {rep['platform']}: 读入 {rep['rows']} 保留 {rep['kept']} "
              f"日期失败 {rep['date_parse_fail']} 去重丢弃 {rep['dup_keys_dropped']} "
              f"金额异常 {len(rep['amount_anomalies'])}")
    print(f"[OK] 口径对照 {out_cal}；质量报告 {out_q}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="多平台销售数据合并对齐")
    ap.add_argument("--inspect", nargs="+", help="预览文件表头与样例行")
    ap.add_argument("--config", help="映射配置 JSON（数组）")
    ap.add_argument("--out", help="输出目录")
    args = ap.parse_args()
    if args.inspect:
        return inspect(args.inspect)
    if not (args.config and args.out):
        raise SystemExit("[FAIL] 合并模式需同时提供 --config 与 --out")
    return run(args.config, args.out)


if __name__ == "__main__":
    sys.exit(main())
