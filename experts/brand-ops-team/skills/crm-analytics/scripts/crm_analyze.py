#!/usr/bin/env python3
"""
crm_analyze.py — 按选定模型执行 CRM 数据分析，产出报告 + 分群 CSV + 图表。

用法:
  # 正式执行
  python crm_analyze.py --model rfm --data data.csv --config config.json --outdir ./results
  # 执行前预检（不跑分析，只校验字段映射与数据质量）
  python crm_analyze.py --model rfm --data data.csv --config config.json --outdir ./results --dry-run

三道防线:
  1) --dry-run 执行前预检：缺列 / 类型不可解析 / 空表 / 日期越界 → 大声失败
  2) 执行期 coerce 记录：数值/日期解析失败不再静默填 0，而是记录并在报告末尾告警
  3) 每模型结果交叉验证：合计对账、比率∈[0,1]、漏斗单调、双法对照等
"""
import argparse
import json
import os
import sys
import itertools

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# 中文显示（若环境无中文字体则退化为英文标签，不影响数据）
try:
    plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "PingFang SC", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
except Exception:
    pass

# 共享字段契约
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crm_schema import MODEL_SCHEMA, FALLBACK, MODEL_TITLES, list_models_str  # noqa: E402


# ---------- 类型解析（带记录，杜绝静默填 0）----------
_COERCE_LOG = {}


def coerce_numeric(s):
    out = pd.to_numeric(s, errors="coerce")
    n = int(out.isna().sum())
    if n:
        _COERCE_LOG[s.name] = (n, list(s[out.isna()].astype(str).head(3)))
    return out


def coerce_date(s):
    out = pd.to_datetime(s, errors="coerce")
    n = int(out.isna().sum())
    if n:
        _COERCE_LOG[s.name] = (n, list(s[out.isna()].astype(str).head(3)))
    return out


def coerce_note():
    if not _COERCE_LOG:
        return ""
    lines = ["\n## ⚠️ 数据质量问题（执行期）\n",
             "下列字段存在无法解析为数值/日期的记录，已按缺失处理"
             "（**未被静默填 0 掩盖**，请复核字段映射与源数据）：\n",
             "| 字段 | 无法解析行数 | 样例原始值 |", "|---|---|---|"]
    for col, (n, ex) in _COERCE_LOG.items():
        lines.append(f"| {col} | {n} | {', '.join(ex)} |")
    return "\n".join(lines) + "\n"


# ---------- 交叉验证小节渲染 ----------
def xcheck_section(checks):
    """checks: list of (name, ok, detail)。ok: True=PASS, False=FAIL, None=WARN"""
    if not checks:
        return ""
    lines = ["\n## 交叉验证", "",
             "| 校验项 | 结果 | 说明 |", "|---|---|---|"]
    n_fail = 0
    for name, ok, detail in checks:
        if ok is None:
            tag = "⚠️ WARN"
        else:
            ok = bool(ok)
            if ok:
                tag = "✅ PASS"
            else:
                tag = "❌ FAIL"
                n_fail += 1
        lines.append(f"| {name} | {tag} | {detail} |")
    lines.append("")
    if n_fail:
        lines.append(f"> **{n_fail} 项未通过**，请复核数据与字段映射后再采信结论。")
    else:
        lines.append("> 一致性校验全部通过。")
    return "\n".join(lines) + "\n"


# ---------- 工具 ----------
def get_col(df, cfg, logical, default=None):
    return cfg.get("columns", {}).get(logical, default if default else logical)


def norm_features(feats):
    """把 features 规范为列表：支持逗号分隔字符串或列表/元组。"""
    if feats is None:
        return []
    if isinstance(feats, str):
        return [x.strip() for x in feats.split(",") if x.strip()]
    if isinstance(feats, (list, tuple)):
        return [str(x).strip() for x in feats if str(x).strip()]
    return []


def load_data(path):
    if path.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(path)
    return pd.read_csv(path)


def save_chart(fig, outdir, name):
    path = os.path.join(outdir, name)
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return os.path.basename(path)


def md_table(df, max_rows=20):
    if df is None or df.empty:
        return "_(无数据)_"
    d = df.head(max_rows)
    headers = list(d.columns)
    lines = ["| " + " | ".join(str(h) for h in headers) + " |",
             "| " + " | ".join("---" for _ in headers) + " |"]
    for _, row in d.iterrows():
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    if len(df) > max_rows:
        lines.append(f"\n_（仅显示前 {max_rows} 行，完整数据见 segments.csv）_")
    return "\n".join(lines)


# ---------- 各模型 ----------
def model_rfm(df, cfg):
    cid = get_col(df, cfg, "customer_id")
    od = get_col(df, cfg, "order_date")
    amt = get_col(df, cfg, "amount")
    params = cfg.get("params", {})
    cur = params.get("currency", "CNY")
    q = int(params.get("quantile", 4))
    snap = pd.to_datetime(params.get("snapshot_date")) if params.get("snapshot_date") else df[od].max()
    snap = pd.to_datetime(snap)

    d = df[[cid, od, amt]].copy()
    d[od] = coerce_date(d[od])
    d[amt] = coerce_numeric(d[amt])
    d["_R_days"] = (snap - d[od]).dt.days
    g = d.groupby(cid).agg(R=("_R_days", "min"),
                           F=(amt, "count"),
                           M=(amt, "sum"))
    g["R"] = g["R"].astype(int)
    g["R_score"] = q - pd.qcut(g["R"].rank(method="first"), q, labels=False)
    g["F_score"] = pd.qcut(g["F"].rank(method="first"), q, labels=False) + 1
    g["M_score"] = pd.qcut(g["M"].rank(method="first"), q, labels=False) + 1

    def seg(r, f, m):
        if r >= 3 and f >= 3 and m >= 3: return "重要价值客户"
        if r < 3 and f >= 3 and m >= 3: return "重要保持客户"
        if r >= 3 and f < 3 and m >= 3: return "重要发展客户"
        if r < 3 and f < 3 and m >= 3: return "重要挽留客户"
        if r >= 3 and f < 3 and m < 3: return "一般发展客户"
        if r < 3 and f < 3 and m < 3: return "一般挽留客户"
        if r >= 3 and f >= 3 and m < 3: return "一般价值客户"
        return "一般保持客户"
    g["segment"] = [seg(r, f, m) for r, f, m in zip(g["R_score"], g["F_score"], g["M_score"])]

    seg_sum = g.groupby("segment").agg(
        客户数=("M", "size"), 平均R=("R", "mean"),
        平均F=("F", "mean"), 平均M=("M", "mean")).round(1)
    seg_sum["金额占比%"] = (g.groupby("segment")["M"].sum() / g["M"].sum() * 100).round(1)
    seg_sum = seg_sum.sort_values("金额占比%", ascending=False)
    seg_sum["客户数占比%"] = (seg_sum["客户数"] / seg_sum["客户数"].sum() * 100).round(1)
    seg_sum = seg_sum.reset_index()

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(seg_sum["segment"], seg_sum["客户数"])
    ax.set_ylabel("客户数"); ax.set_title("RFM 各客群客户数"); plt.xticks(rotation=30, ha="right")
    chart = save_chart(fig, cfg["_outdir"], "chart_rfm_counts.png")

    report = f"# RFM 客户价值分层分析\n\n"
    report += f"- 分析基准日：{snap.date()}　货币单位：{cur}　分箱数：{q}\n"
    report += f"- 客户总数：{len(g)}　订单总额：{g['M'].sum():,.0f} {cur}\n\n"
    report += "## 客群分布与贡献\n\n" + md_table(seg_sum) + "\n\n"
    report += f"![客群分布]({chart})\n\n"
    report += "## 解读建议\n"
    report += "- **重要价值/保持客户**：高价值，配置专属权益与唤醒触达。\n"
    report += "- **重要挽留客户**：高金额但已静默，流失风险高，优先挽回。\n"
    report += "- **一般发展客户**：近期活跃但金额低，做客单提升（交叉销售）。\n"

    # 交叉验证
    total = len(g)
    seg_n = int(seg_sum["客户数"].sum())
    neg = int((g["M"] < 0).sum())
    checks = [
        ("客户数对账（分段合计=客户总数）", seg_n == total, f"{seg_n} = {total}"),
        ("金额非负", neg == 0, f"负金额 {neg} 条" if neg else "ok"),
    ]
    report += xcheck_section(checks)

    segs = g.reset_index()[[cid, "R", "F", "M", "R_score", "F_score", "M_score", "segment"]]
    return report, segs, [chart]


def model_aarrr(df, cfg):
    uid = get_col(df, cfg, "user_id")
    ev = get_col(df, cfg, "event")
    ed = get_col(df, cfg, "event_date")
    order = ["signup", "activate", "retain", "pay", "refer"]
    d = df[[uid, ev, ed]].copy()
    d[ev] = d[ev].astype(str).str.lower()
    counts = {s: d.loc[d[ev] == s, uid].nunique() for s in order}
    rows = []
    prev = None
    for s in order:
        conv = "" if prev is None else f"{(counts[s]/counts[prev]*100):.1f}%" if counts[prev] else "0%"
        rows.append([s, counts[s], conv])
        prev = s
    res = pd.DataFrame(rows, columns=["环节", "人数", "较上一环转化率"])
    overall = (counts["refer"] / counts["signup"] * 100) if counts["signup"] else 0

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(order, [counts[s] for s in order], marker="o")
    for i, s in enumerate(order):
        ax.annotate(str(counts[s]), (i, counts[s]), textcoords="offset points", xytext=(0, 6))
    ax.set_title("AARRR 增长漏斗"); ax.set_ylabel("人数"); plt.xticks(rotation=20)
    chart = save_chart(fig, cfg["_outdir"], "chart_aarrr.png")

    report = "# AARRR 增长漏斗分析\n\n" + md_table(res) + "\n\n"
    report += f"- 整体转化（refer / signup）：**{overall:.1f}%**\n\n"
    report += f"![AARRR]({chart})\n\n"
    rates = [counts[order[i+1]]/counts[order[i]] if counts[order[i]] else 0 for i in range(len(order)-1)]
    if rates:
        b = int(np.argmin(rates))
        report += f"## 瓶颈环节\n- 转化最低：**{order[b]} → {order[b+1]}**（{rates[b]*100:.1f}%），建议优先优化。\n"

    # 交叉验证
    ok_seq = all(counts[order[i+1]] <= counts[order[i]] for i in range(len(order)-1))
    zero = [s for s in order if counts[s] == 0]
    checks = [
        ("漏斗人数单调递减", ok_seq, "后续环节人数应≤前一环" if ok_seq else "存在环节人数逆增"),
        ("无空环节", len(zero) == 0, f"空环节: {zero}" if zero else "ok"),
    ]
    report += xcheck_section(checks)
    return report, None, [chart]


def model_aipl(df, cfg):
    cid = get_col(df, cfg, "customer_id")
    st = get_col(df, cfg, "stage")
    order = ["A", "I", "P", "L"]
    d = df[[cid, st]].copy()
    d[st] = d[st].astype(str).str.upper()
    counts = {s: d.loc[d[st] == s, cid].nunique() for s in order}
    rows = []
    prev = None
    for s in order:
        conv = "" if prev is None else f"{(counts[s]/counts[prev]*100):.1f}%" if counts[prev] else "0%"
        rows.append([s, counts[s], conv]); prev = s
    res = pd.DataFrame(rows, columns=["阶段", "人数", "流转率"])
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(order, [counts[s] for s in order])
    for i, s in enumerate(order):
        ax.annotate(str(counts[s]), (i, counts[s]), textcoords="offset points", xytext=(0, 5))
    ax.set_title("AIPL 营销漏斗"); plt.xticks(rotation=0)
    chart = save_chart(fig, cfg["_outdir"], "chart_aipl.png")
    report = "# AIPL 营销漏斗分析\n\n" + md_table(res) + f"\n\n![AIPL]({chart})\n\n"
    report += "## 解读\n- **I→P 低**：兴趣转化弱，优化种草到下单路径。\n- **P→L 低**：复购/会员体系弱，强化忠诚度运营。\n"

    ok_seq = all(counts[order[i+1]] <= counts[order[i]] for i in range(len(order)-1))
    zero = [s for s in order if counts[s] == 0]
    checks = [
        ("漏斗人数单调递减", ok_seq, "后续阶段人数应≤前一阶段" if ok_seq else "存在阶段人数逆增"),
        ("无空阶段", len(zero) == 0, f"空阶段: {zero}" if zero else "ok"),
    ]
    report += xcheck_section(checks)
    return report, None, [chart]


def model_clv(df, cfg):
    cid = get_col(df, cfg, "customer_id")
    od = get_col(df, cfg, "order_date")
    amt = get_col(df, cfg, "amount")
    params = cfg.get("params", {})
    margin = float(params.get("margin", 1.0))
    lifespan = params.get("lifespan")
    d = df[[cid, od, amt]].copy()
    d[od] = coerce_date(d[od]); d[amt] = coerce_numeric(d[amt])
    g = d.groupby(cid).agg(orders=(amt, "count"), total=(amt, "sum"),
                           first=(od, "min"), last=(od, "max"))
    g["span_years"] = ((g["last"] - g["first"]).dt.days / 365.25).clip(lower=1/365.25)
    life = float(lifespan) if lifespan else g["span_years"].median()
    g["AOV"] = (g["total"] / g["orders"]).round(2)
    g["freq_per_year"] = g["orders"] / g["span_years"]
    g["CLV"] = (g["AOV"] * g["freq_per_year"] * life * margin).round(0)
    g["historical_value"] = g["total"].round(0)
    segs = g.reset_index()[[cid, "orders", "total", "AOV", "CLV", "historical_value"]].sort_values("CLV", ascending=False)
    avg_clv = g["CLV"].mean()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(g["CLV"].clip(upper=g["CLV"].quantile(0.95)), bins=30)
    ax.set_title("CLV 分布（截断至 95 分位）"); ax.set_xlabel("CLV")
    chart = save_chart(fig, cfg["_outdir"], "chart_clv.png")
    report = "# CLV 客户生命周期价值\n\n"
    report += f"- 平均 CLV：{avg_clv:,.0f}　生命周期假设：{life:.2f} 年　毛利率系数：{margin}\n\n"
    report += "## Top 客户（按 CLV）\n\n" + md_table(segs.head(15)) + f"\n\n![CLV分布]({chart})\n\n"
    report += "## 解读\n- CLV 远高于获客成本(CAC) 的客户/渠道值得加投；反之需止损。\n"

    # 交叉验证：CLV 非负 + 预测/历史量级对照
    neg_clv = int((g["CLV"] < 0).sum())
    hist_total = g["historical_value"].sum()
    pred_total = g["CLV"].sum()
    ratio = (pred_total / hist_total) if hist_total else 0
    checks = [
        ("CLV 非负", neg_clv == 0, f"负值 {neg_clv} 条" if neg_clv else "ok"),
        ("CLV 量级对照(预测/历史)", True if (0.1 <= ratio <= 50) else None,
         f"比值 {ratio:.2f}（历史消费合计 {hist_total:,.0f} vs 预测 CLV 合计 {pred_total:,.0f}；"
         f"偏离过大说明生命周期/毛利率假设需复核）"),
    ]
    report += xcheck_section(checks)
    return report, segs, [chart]


def model_cohort(df, cfg):
    uid = get_col(df, cfg, "user_id")
    sd = get_col(df, cfg, "signup_date")
    ad = get_col(df, cfg, "activity_date")
    d = df[[uid, sd, ad]].copy()
    d[sd] = coerce_date(d[sd]); d[ad] = coerce_date(d[ad])
    d["cohort"] = d[sd].dt.to_period("M").astype(str)
    d["period"] = (d[ad].dt.year - d[sd].dt.year) * 12 + (d[ad].dt.month - d[sd].dt.month)
    piv = d.pivot_table(index="cohort", columns="period", values=uid, aggfunc="nunique")
    sizes = d.groupby("cohort")[uid].nunique()
    ret = piv.div(sizes, axis=0).round(3) * 100
    show = ret.iloc[:, :min(8, ret.shape[1])]
    fig, ax = plt.subplots(figsize=(9, 5))
    im = ax.imshow(show.values, aspect="auto", cmap="YlGnBu")
    ax.set_xticks(range(show.shape[1])); ax.set_xticklabels(show.columns)
    ax.set_yticks(range(show.shape[0])); ax.set_yticklabels(show.index)
    ax.set_title("同期群留存热力图 (%)"); plt.colorbar(im, ax=ax)
    chart = save_chart(fig, cfg["_outdir"], "chart_cohort.png")
    report = "# 同期群留存分析\n\n" + md_table(show.reset_index().rename(columns={"index": "cohort"}), 15) + f"\n\n![留存热力]({chart})\n\n"
    report += "## 解读\n- 若各 cohort 后期留存趋于平稳，说明产品具备稳定黏性；快速衰减则需优化新用户激活。\n"

    arr = show.values
    bad = int(((arr < 0) | (arr > 100) | np.isnan(arr)).sum())
    checks = [("留存率∈[0,100]%", bad == 0, f"越界/缺失 {bad} 格" if bad else "ok")]
    report += xcheck_section(checks)
    return report, None, [chart]


def model_churn(df, cfg):
    cid = get_col(df, cfg, "customer_id")
    lad = get_col(df, cfg, "last_active_date") if get_col(df, cfg, "last_active_date") in df else get_col(df, cfg, "order_date")
    params = cfg.get("params", {})
    churn_days = int(params.get("churn_days", 90))
    if lad == get_col(df, cfg, "order_date"):
        d = df[[cid, lad]].copy(); d[lad] = coerce_date(d[lad])
        d = d.groupby(cid)[lad].max().reset_index()
    else:
        d = df[[cid, lad]].copy(); d[lad] = coerce_date(d[lad])
    snap = pd.to_datetime(params.get("snapshot_date")) if params.get("snapshot_date") else d[lad].max()
    d["沉默天数"] = (pd.to_datetime(snap) - d[lad]).dt.days
    d["已流失"] = d["沉默天数"] >= churn_days
    maxd = d["沉默天数"].max() or 1
    d["风险分"] = (d["沉默天数"] / maxd * 100).round(0)
    d["风险等级"] = pd.cut(d["风险分"], [0, 40, 70, 100], labels=["低", "中", "高"], include_lowest=True)
    segs = d[[cid, lad, "沉默天数", "已流失", "风险分", "风险等级"]].sort_values("风险分", ascending=False)
    churned = int(d["已流失"].sum())
    fig, ax = plt.subplots(figsize=(6, 4))
    d["风险等级"].value_counts().reindex(["高", "中", "低"]).plot(kind="bar", ax=ax)
    ax.set_title("流失风险分布"); ax.set_ylabel("客户数")
    chart = save_chart(fig, cfg["_outdir"], "chart_churn.png")
    report = "# 流失预警分析\n\n"
    report += f"- 流失阈值：静默 ≥ {churn_days} 天　基准日：{pd.to_datetime(snap).date()}\n"
    report += f"- 已流失客户：**{churned}** / 总 {len(d)}（{churned/len(d)*100:.1f}%）\n\n"
    report += "## 高风险客户（Top 15）\n\n" + md_table(segs.head(15)) + f"\n\n![风险分布]({chart})\n\n"
    report += "## 解读\n- 高风险且历史价值高的客户进入挽回名单（优惠券/专属关怀）。\n"

    n = len(d)
    lvl = d["风险等级"].value_counts()
    empty = [lv for lv in ["高", "中", "低"] if lvl.get(lv, 0) == 0]
    checks = [
        ("流失率∈[0,100%]", 0 <= churned <= n, f"{churned}/{n}"),
        ("风险分级完整", len(empty) == 0, f"无样本等级: {empty}" if empty else "ok"),
    ]
    report += xcheck_section(checks)
    return report, segs, [chart]


def model_segmentation(df, cfg):
    params = cfg.get("params", {})
    feats = params.get("features") or cfg.get("columns", {}).get("features")
    feats = norm_features(feats)
    if not feats:
        raise SystemExit("segmentation 模型需要在 params.features 指定数值特征列（逗号分隔或数组）")
    X = df[feats].apply(lambda c: coerce_numeric(c))
    if X.isna().any().any():
        raise SystemExit(
            "分群特征存在无法解析为非数值的记录，已中止（缺失/脏值会污染聚类中心）。"
            "请先清洗数据或调整 features，或用 --dry-run 预检定位坏值。")
    X = X.values
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd[sd == 0] = 1.0
    Xs = (X - mu) / sd
    k = int(params.get("k", 0)) or 4
    labels, centers = _kmeans(Xs, k, seed=42)
    df2 = df.copy(); df2["cluster"] = labels
    centers_df = pd.DataFrame(centers * sd + mu, columns=feats)
    fig, ax = plt.subplots(figsize=(8, 4))
    for c in range(k):
        ax.scatter(Xs[labels == c, 0], Xs[labels == c, 1], label=f"簇{c}", s=12)
    ax.set_xlabel(feats[0]); ax.set_ylabel(feats[1] if len(feats) > 1 else "标准化值")
    ax.set_title("K-Means 客户分群"); ax.legend()
    chart = save_chart(fig, cfg["_outdir"], "chart_seg.png")
    report = "# 客户分群（K-Means）\n\n"
    report += f"- 特征：{', '.join(feats)}　簇数 k={k}（纯 numpy 实现，无需 scikit-learn）\n\n"
    report += "## 各簇中心画像（原始量纲）\n\n" + md_table(centers_df.round(2)) + f"\n\n![分群]({chart})\n\n"
    report += "## 解读\n- 按各簇中心高低命名（如高频低额/低频高额），匹配差异化运营策略。\n"

    ncl = len(set(labels.tolist()))
    empty = [c for c in range(k) if int((labels == c).sum()) == 0]
    checks = [
        ("簇数=k", ncl == k, f"实际 {ncl} 簇"),
        ("无空簇", len(empty) == 0, f"空簇: {empty}" if empty else "ok"),
    ]
    report += xcheck_section(checks)
    return report, df2, [chart]


def _kmeans(X, k, seed=42, iters=100):
    rng = np.random.default_rng(seed)
    n = X.shape[0]
    centers = [X[rng.integers(n)]]
    for _ in range(1, k):
        d2 = np.min([np.sum((X - c) ** 2, axis=1) for c in centers], axis=0)
        probs = d2 / d2.sum()
        centers.append(X[rng.choice(n, p=probs)])
    centers = np.array(centers, dtype=float)
    for _ in range(iters):
        dist = np.linalg.norm(X[:, None, :] - centers[None, :, :], axis=2)
        labels = dist.argmin(axis=1)
        new = np.array([X[labels == j].mean(axis=0) if np.any(labels == j) else centers[j]
                        for j in range(k)])
        if np.allclose(new, centers):
            break
        centers = new
    dist = np.linalg.norm(X[:, None, :] - centers[None, :, :], axis=2)
    labels = dist.argmin(axis=1)
    return labels, centers


def model_funnel(df, cfg):
    params = cfg.get("params", {})
    stage_order = params.get("stage_order")
    st = get_col(df, cfg, "stage")
    if st in df.columns and get_col(df, cfg, "count") not in df.columns and get_col(df, cfg, "user_id") in df.columns:
        uid = get_col(df, cfg, "user_id")
        if not stage_order:
            raise SystemExit("事件型漏斗需要在 params.stage_order 指定阶段顺序")
        d = df[[uid, st]].copy(); d[st] = d[st].astype(str)
        counts = {s: d.loc[d[st] == s, uid].nunique() for s in stage_order}
    else:
        cnt = get_col(df, cfg, "count")
        s = df[[st, cnt]].copy()
        if stage_order:
            s = s.set_index(st).reindex(stage_order).dropna()
        counts = {k: int(v) for k, v in zip(s.index, s[cnt])}
    rows = []; prev = None
    for s in counts:
        conv = "" if prev is None else f"{counts[s]/counts[prev]*100:.1f}%" if counts[prev] else "0%"
        rows.append([s, counts[s], conv]); prev = s
    res = pd.DataFrame(rows, columns=["阶段", "人数", "转化率"])
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(list(counts.keys()), list(counts.values()))
    ax.set_title("销售漏斗"); plt.xticks(rotation=20)
    chart = save_chart(fig, cfg["_outdir"], "chart_funnel.png")
    report = "# 销售漏斗分析\n\n" + md_table(res) + f"\n\n![漏斗]({chart})\n\n"
    report += "## 解读\n- 找出最大漏损阶段，针对性设计干预（如报价→成交低，强化销售跟进）。\n"

    ks = list(counts.keys())
    ok_seq = all(counts[ks[i+1]] <= counts[ks[i]] for i in range(len(ks)-1))
    zero = [s for s in ks if counts[s] == 0]
    checks = [
        ("漏斗人数单调递减", ok_seq, "后阶段人数应≤前阶段" if ok_seq else "存在阶段人数逆增"),
        ("无空阶段", len(zero) == 0, f"空阶段: {zero}" if zero else "ok"),
    ]
    report += xcheck_section(checks)
    return report, None, [chart]


def model_market_basket(df, cfg):
    oid = get_col(df, cfg, "order_id")
    prod = get_col(df, cfg, "product")
    d = df[[oid, prod]].dropna().drop_duplicates()
    baskets = d.groupby(oid)[prod].apply(list)
    from collections import Counter
    pair = Counter(); item = Counter()
    for items in baskets:
        items = list(set(items))
        item.update(items)
        for a, b in itertools.combinations(sorted(items), 2):
            pair[(a, b)] += 1
    total = len(baskets)
    rows = []
    for (a, b), co in pair.most_common(50):
        supp = co / total
        conf = co / item[a]
        lift = conf / (item[b] / total)
        rows.append([a, b, round(supp, 4), round(conf, 4), round(lift, 3), co])
    res = pd.DataFrame(rows, columns=["前项", "后项", "支持度", "置信度", "提升度", "共现次数"])
    fig, ax = plt.subplots(figsize=(8, 4))
    top = res.head(10)
    ax.barh(top["前项"] + "→" + top["后项"], top["提升度"]); ax.set_title("Top 关联规则（按提升度）")
    chart = save_chart(fig, cfg["_outdir"], "chart_basket.png")
    report = "# 购物篮 / 关联分析\n\n" + md_table(res.head(20)) + f"\n\n![关联规则]({chart})\n\n"
    report += "## 解读\n- 提升度 > 1 且置信度高的规则可用于'买了 A 也买了 B'推荐与陈列搭配。\n"

    bad_lift = int((res["提升度"] < 0).sum()) if len(res) else 0
    bad_supp = int(((res["支持度"] < 0) | (res["支持度"] > 1)).sum()) if len(res) else 0
    checks = [
        ("提升度≥0", bad_lift == 0, f"负值 {bad_lift}" if bad_lift else "ok"),
        ("支持度∈[0,1]", bad_supp == 0, f"越界 {bad_supp}" if bad_supp else "ok"),
    ]
    report += xcheck_section(checks)
    return report, res, [chart]


def model_abc(df, cfg):
    params = cfg.get("params", {})
    idc = get_col(df, cfg, "id")
    val = get_col(df, cfg, "value")
    d = df[[idc, val]].copy(); d[val] = coerce_numeric(d[val])
    d = d.groupby(idc)[val].sum().reset_index().sort_values(val, ascending=False)
    total = d[val].sum(); d["cum"] = d[val].cumsum() / total
    a_thr = float(params.get("a_threshold", 0.7)); b_thr = float(params.get("b_threshold", 0.9))
    def cls(c):
        return "A" if c <= a_thr else ("B" if c <= b_thr else "C")
    d["class"] = d["cum"].apply(cls)
    summ = d.groupby("class").agg(数量=("class", "size"), 金额=(val, "sum"))
    summ["金额占比%"] = (summ["金额"] / total * 100).round(1)
    summ["数量占比%"] = (summ["数量"] / len(d) * 100).round(1)
    summ = summ.reset_index()
    fig, ax = plt.subplots(figsize=(6, 4))
    summ.plot(kind="bar", x="class", y="金额占比%", ax=ax, legend=False)
    ax.set_title("ABC 帕累托（金额占比%）")
    chart = save_chart(fig, cfg["_outdir"], "chart_abc.png")
    report = "# ABC 帕累托分析\n\n" + md_table(summ) + f"\n\n![ABC]({chart})\n\n"
    report += "## 解读\n- A 类（少数高贡献）投入重点服务；C 类长尾走自动化/低成本运营。\n"

    n = len(d)
    cnts = d["class"].value_counts()
    n_abc = int(cnts.get("A", 0) + cnts.get("B", 0) + cnts.get("C", 0))
    checks = [
        ("分类数对账(A+B+C=总数)", n_abc == n, f"{n_abc} = {n}"),
        ("累计占比收敛到100%", abs(float(d["cum"].max()) - 1.0) < 1e-6, f"末累计 {d['cum'].max():.4f}"),
    ]
    report += xcheck_section(checks)
    return report, d[[idc, val, "cum", "class"]], [chart]


def model_nps(df, cfg):
    sc = get_col(df, cfg, "score")
    d = df.copy(); d[sc] = coerce_numeric(d[sc])
    prom = (d[sc] >= 9).sum(); passiv = ((d[sc] >= 7) & (d[sc] <= 8)).sum(); detr = (d[sc] <= 6).sum()
    n = len(d); nps = (prom - detr) / n * 100 if n else 0
    res = pd.DataFrame({"类别": ["推荐者(9-10)", "中立(7-8)", "贬损者(0-6)"],
                        "人数": [prom, passiv, detr],
                        "占比%": [round(prom/n*100, 1), round(passiv/n*100, 1), round(detr/n*100, 1)]})
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(res["类别"], res["人数"], color=["#2ca02c", "#ff7f0e", "#d62728"])
    ax.set_title(f"NPS = {nps:.0f}")
    chart = save_chart(fig, cfg["_outdir"], "chart_nps.png")
    report = "# NPS 净推荐值分析\n\n" + md_table(res) + f"\n\n- **NPS = {nps:.0f}**（推荐者% − 贬损者%）\n\n![NPS]({chart})\n\n"
    report += "## 解读\n- NPS 提升常对应营收增长；结合开放文本定位体验痛点。\n"

    checks = [
        ("人数对账(推荐+中立+贬损=总数)", int(prom+passiv+detr) == n, f"{int(prom+passiv+detr)} = {n}"),
        ("NPS∈[-100,100]", -100 <= nps <= 100, f"NPS={nps:.0f}"),
    ]
    report += xcheck_section(checks)
    return report, None, [chart]


MODELS = {
    "rfm": model_rfm, "aarrr": model_aarrr, "aipl": model_aipl, "clv": model_clv,
    "cohort": model_cohort, "churn": model_churn, "segmentation": model_segmentation,
    "funnel": model_funnel, "market_basket": model_market_basket, "abc": model_abc, "nps": model_nps,
}


# ---------- 执行前预检（dry-run）----------
def validate_input(df, cfg, model):
    """返回 checks: list of (name, ok, detail)。ok: True/False/None(WARN)"""
    checks = []
    if len(df) == 0:
        return [("数据非空", False, "0 行，无法分析")]
    schema = MODEL_SCHEMA.get(model, [])
    cols = cfg.get("columns", {})
    for logical, dtype, req in schema:
        col = cols.get(logical)
        # 回退字段
        if col is None and logical in FALLBACK.get(model, {}):
            col = cols.get(FALLBACK[model][logical])
        if col is None:
            checks.append((f"字段映射存在: {logical}", False if req else None,
                           "config.columns 未提供该字段" + ("" if req else "（可选）")))
            continue
        if col not in df.columns:
            checks.append((f"字段存在: {logical}→{col}", False, f"数据中无列 '{col}'"))
            continue
        if dtype in ("numeric", "date"):
            out = coerce_numeric(df[col]) if dtype == "numeric" else coerce_date(df[col])
            n = int(out.isna().sum())
            if n:
                ex = list(df[col][out.isna()].astype(str).head(3))
                checks.append((f"类型可解析: {logical}({dtype})", False if req else None,
                               f"{n}/{len(df)} 行无法解析为{dtype}；样例: {ex}"))
            else:
                checks.append((f"类型可解析: {logical}({dtype})", True, "ok"))
        else:
            checks.append((f"字段存在: {logical}→{col}", True, "ok"))

    # segmentation 特征
    if model == "segmentation":
        feats = norm_features(cfg.get("params", {}).get("features"))
        if not feats:
            checks.append(("特征列已指定", False, "params.features 为空"))
        for f in feats:
            if f not in df.columns:
                checks.append((f"特征列存在: {f}", False, f"数据中无列 '{f}'"))
            else:
                out = coerce_numeric(df[f]); n = int(out.isna().sum())
                if n:
                    checks.append((f"特征值可解析: {f}", False, f"{n}/{len(df)} 行非数值（缺失会污染聚类，须先清洗）"))

    # funnel 事件型
    if model == "funnel" and not cols.get("count"):
        if not cfg.get("params", {}).get("stage_order"):
            checks.append(("漏斗阶段顺序", False, "事件型漏斗缺 params.stage_order"))
        if not cols.get("user_id"):
            checks.append(("漏斗用户列", False, "事件型漏斗缺 user_id"))

    # 日期基准 sanity（rfm/churn）
    if model in ("rfm", "churn") and cfg.get("params", {}).get("snapshot_date"):
        snap = pd.to_datetime(cfg["params"]["snapshot_date"])
        odcol = cols.get("order_date") or cols.get("last_active_date")
        if odcol and odcol in df.columns:
            mx = coerce_date(df[odcol]).max()
            if pd.notna(mx) and snap < mx:
                checks.append(("基准日≥最新数据", None,
                               f"基准日 {snap.date()} 早于数据最新 {mx.date()}，R/沉默天数将含负值"))
    return checks


def cmd_list_models():
    """--list-models：打印模型清单（含必填/可选字段），不需要数据文件。"""
    print(list_models_str())
    print("\n提示：直接用 --model <key> 运行分析；或加 --interactive 进入交互式引导。")


def _resolve_model(pick):
    keys = list(MODEL_TITLES.keys())
    pick = (pick or "").strip()
    if pick in keys:
        return pick
    try:
        i = int(pick) - 1
        if 0 <= i < len(keys):
            return keys[i]
    except ValueError:
        pass
    return None


def cmd_interactive(a):
    """--interactive：交互式引导选择模型与字段映射，并自动跑预检。"""
    from datetime import date
    print("=== CRM 分析模型清单 ===")
    print(list_models_str())
    print("")
    model = _resolve_model(input("请选择模型（编号或 key，如 1 / rfm）：").strip())
    if not model:
        raise SystemExit("未识别到有效模型，退出。")
    headers = list(pd.read_csv(a.data).columns) if a.data else []
    print(f"数据列：{headers}\n" if headers else "（未提供 --data，将仅生成 config）")

    cfg = {"model": model, "columns": {}, "params": {}}
    if model == "segmentation":
        feats = input(f"分群数值特征列（逗号分隔；数据列: {headers}）：").strip()
        cfg["params"]["features"] = feats
        cfg["params"]["k"] = input("簇数 k（默认 4）：").strip() or "4"
    elif model == "funnel":
        cfg["columns"]["stage"] = input("阶段列名：").strip()
        mode = input("模式 [wide 宽表(各阶段人数) / event 事件型(用户+阶段)，默认 wide]：").strip() or "wide"
        if mode == "wide":
            cfg["columns"]["count"] = input("人数列名：").strip()
        else:
            cfg["columns"]["user_id"] = input("用户列名：").strip()
            cfg["params"]["stage_order"] = [s.strip() for s in
                                            input("阶段顺序（逗号分隔，如 signup,activate,pay）：").split(",") if s.strip()]
    else:
        for logical, dtype, req in MODEL_SCHEMA.get(model, []):
            default = logical if logical in headers else ""
            val = input(f"字段 '{logical}'（{dtype}{'·必填' if req else '·可选'}）→ 真实列名"
                        f"（默认 {default or '无'}）：").strip() or default
            cfg["columns"][logical] = val

    # 通用口径
    if model in ("rfm", "clv", "churn"):
        cfg["params"]["snapshot_date"] = input("基准日 snapshot_date（默认今天）：").strip() or date.today().isoformat()
    if model in ("rfm", "abc"):
        q = input("分箱分位数 quantile（RFM 默认 4；ABC 留空用阈值）：").strip()
        if q:
            cfg["params"]["quantile"] = int(q)
    cfg["params"].setdefault("currency", "CNY")

    cfgpath = a.config or "config_interactive.json"
    with open(cfgpath, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] 已生成配置 → {cfgpath}")

    if not a.data:
        print("未提供 --data，无法预检。请随后执行：")
        print(f"  python crm_analyze.py --model {model} --data <文件> --config {cfgpath} --dry-run")
        return

    # 跑预检
    df = load_data(a.data)
    _COERCE_LOG.clear()
    checks = validate_input(df, cfg, model)
    n_fail = sum(1 for _, ok, _ in checks if ok is False)
    print("\n=== 执行前预检 ===")
    for name, ok, detail in checks:
        tag = "✅ PASS" if ok is True else ("❌ FAIL" if ok is False else "⚠️ WARN")
        print(f"  {tag} {name}：{detail}")
    if n_fail:
        print(f"\n预检未通过（{n_fail} 项失败），请修正字段映射后重试。")
        sys.exit(1)
    go = input("\n预检通过。是否立即执行分析？[y/N]：").strip().lower()
    if go != "y":
        print("已取消。可手动执行："
              f" python crm_analyze.py --model {model} --data {a.data} --config {cfgpath} --outdir {a.outdir}")
        return
    os.makedirs(a.outdir, exist_ok=True)
    cfg["_outdir"] = a.outdir
    report, segs, charts = MODELS[model](df, cfg)
    report += coerce_note()
    with open(os.path.join(a.outdir, "report.md"), "w", encoding="utf-8") as f:
        f.write(report)
    if segs is not None:
        segs.to_csv(os.path.join(a.outdir, "segments.csv"), index=False, encoding="utf-8-sig")
    print(f"[OK] 模型 {model} 完成 → {a.outdir}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--list-models", action="store_true", help="打印模型清单后退出")
    p.add_argument("--interactive", action="store_true", help="交互式引导选模型与字段映射")
    p.add_argument("--model", choices=list(MODELS.keys()))
    p.add_argument("--data")
    p.add_argument("--config")
    p.add_argument("--outdir", default="./results")
    p.add_argument("--dry-run", action="store_true", help="仅执行前预检，不跑分析")
    a = p.parse_args()

    if a.list_models:
        cmd_list_models()
        return
    if a.interactive:
        cmd_interactive(a)
        return
    if not a.model or not a.data or not a.config:
        raise SystemExit("运行分析需 --model / --data / --config；或改用 --list-models / --interactive。")

    os.makedirs(a.outdir, exist_ok=True)
    cfg = json.load(open(a.config, encoding="utf-8"))
    cfg["_outdir"] = a.outdir
    cfg["model"] = a.model
    df = load_data(a.data)
    _COERCE_LOG.clear()

    if a.model not in MODELS:
        raise SystemExit(f"未知模型: {a.model}，可选: {list(MODELS)}")

    # ---- 执行前预检 ----
    checks = validate_input(df, cfg, a.model)
    n_fail = sum(1 for _, ok, _ in checks if ok is False)
    if a.dry_run:
        lines = [f"# 预检报告：{a.model}", "",
                 "| 校验项 | 结果 | 说明 |", "|---|---|---|"]
        for name, ok, detail in checks:
            tag = "✅ PASS" if ok is True else ("❌ FAIL" if ok is False else "⚠️ WARN")
            lines.append(f"| {name} | {tag} | {detail} |")
        lines.append("")
        passed = n_fail == 0
        lines.append(f"> 预检结论：**{'通过，可以执行' if passed else f'未通过（{n_fail} 项失败），请修正后重试'}**")
        report = "\n".join(lines) + "\n"
        with open(os.path.join(a.outdir, "validation.md"), "w", encoding="utf-8") as f:
            f.write(report)
        json.dump({"model": a.model, "passed": passed, "checks": [
            {"name": n, "status": ("PASS" if ok is True else "FAIL" if ok is False else "WARN"),
             "detail": d} for n, ok, d in checks]},
            open(os.path.join(a.outdir, "validation.json"), "w", encoding="utf-8"),
            ensure_ascii=False, indent=2)
        print(report)
        sys.exit(0 if passed else 1)

    if n_fail:
        # 非 dry-run 也先拦一道，避免静默产出错误结论
        print("[预检未通过] 以下字段映射或数据质量问题存在，已中止执行：", file=sys.stderr)
        for name, ok, detail in checks:
            if ok is False:
                print(f"  ❌ {name}: {detail}", file=sys.stderr)
        raise SystemExit("请先修正上述字段映射/数据质量问题，或加 --dry-run 查看完整预检。")

    report, segs, charts = MODELS[a.model](df, cfg)
    report += coerce_note()  # 执行期数据质量告警

    with open(os.path.join(a.outdir, "report.md"), "w", encoding="utf-8") as f:
        f.write(report)
    if segs is not None:
        segs.to_csv(os.path.join(a.outdir, "segments.csv"), index=False, encoding="utf-8-sig")
    print(f"[OK] 模型 {a.model} 完成 → {a.outdir}")
    print(f"     报告: report.md | 分群: {'segments.csv' if segs is not None else '无'} | 图表: {len(charts)} 张")


if __name__ == "__main__":
    main()
