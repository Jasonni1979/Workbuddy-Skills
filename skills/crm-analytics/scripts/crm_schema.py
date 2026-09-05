#!/usr/bin/env python3
"""crm_schema.py — CRM 分析模型的「逻辑字段契约」。

驱动的能力：
1) crm_analyze.py --dry-run 的执行前预检（字段是否存在、类型能否解析）
2) crm_receipt.py 的需求理解确认书（模型所需字段 ↔ 真实列映射）
3) crm_connect.py --action diff 的「双源字典差异核对」（自动读 ∩ 手动提供）
4) crm_analyze.py --list-models 模型清单打印
"""
import re


# 每个模型：(逻辑字段, 类型, 是否必填)
MODEL_SCHEMA = {
    "rfm": [
        ("customer_id", "id", True),
        ("order_date", "date", True),
        ("amount", "numeric", True),
    ],
    "aarrr": [
        ("user_id", "id", True),
        ("event", "category", True),
        ("event_date", "date", True),
    ],
    "aipl": [
        ("customer_id", "id", True),
        ("stage", "category", True),
    ],
    "clv": [
        ("customer_id", "id", True),
        ("order_date", "date", True),
        ("amount", "numeric", True),
    ],
    "cohort": [
        ("user_id", "id", True),
        ("signup_date", "date", True),
        ("activity_date", "date", True),
    ],
    "churn": [
        ("customer_id", "id", True),
        ("last_active_date", "date", False),  # 缺则回退 order_date
    ],
    "segmentation": [],  # 特征来自 params.features
    "funnel": [
        ("stage", "category", True),
        ("count", "numeric", False),   # 宽表模式需要
        ("user_id", "id", False),      # 事件型模式需要
    ],
    "market_basket": [
        ("order_id", "id", True),
        ("product", "category", True),
    ],
    "abc": [
        ("id", "id", True),
        ("value", "numeric", True),
    ],
    "nps": [
        ("score", "numeric", True),
    ],
}

# 模型中文标题与一句话说明（用于确认书/清单）
MODEL_TITLES = {
    "rfm": "RFM 客户价值分层",
    "aarrr": "AARRR 增长漏斗",
    "aipl": "AIPL 营销漏斗",
    "clv": "CLV 客户生命周期价值",
    "cohort": "同期群留存分析",
    "churn": "流失预警",
    "segmentation": "客户分群(K-Means)",
    "funnel": "销售漏斗",
    "market_basket": "购物篮/关联分析",
    "abc": "ABC 帕累托分析",
    "nps": "NPS 净推荐值",
}

MODEL_DESC = {
    "rfm": "按最近购买/频次/金额把客户分 8 类，定位高价值与挽留对象。",
    "aarrr": "度量获客→激活→留存→收入→自传播五环，找增长瓶颈。",
    "aipl": "认知→兴趣→购买→忠诚人群流转，看营销漏斗漏损。",
    "clv": "测算客户终身价值，指导获客预算与重点客户。",
    "cohort": "按注册 cohorts 看各期留存率，评估黏性。",
    "churn": "识别高危流失客户并打分，输出挽回名单。",
    "segmentation": "基于多指标无监督聚类，做差异化运营。",
    "funnel": "各阶段转化与流失，定位最大漏损环节。",
    "market_basket": "商品共现与关联规则，指导推荐与陈列。",
    "abc": "区分核心/普通/长尾客户或商品，资源分级。",
    "nps": "计算推荐者/中立/贬损占比，衡量口碑。",
}

# 可选推断的回退字段（仅用于校验提示，不强制）
FALLBACK = {
    "churn": {"last_active_date": "order_date"},
}


# ---------- 模型清单（用于 --list-models / 第 1 步展示）----------
def list_models_str():
    """返回编号化的模型清单字符串（含必填/可选字段）。"""
    lines = []
    keys = list(MODEL_TITLES.keys())
    for i, m in enumerate(keys, 1):
        schema = MODEL_SCHEMA.get(m, [])
        if m == "segmentation":
            fields = "必需: params.features（一组数值特征列）"
        elif m == "funnel":
            fields = "必需: stage；可选: count（宽表模式）或 user_id + stage_order（事件型）"
        else:
            req = [f for f, _, r in schema if r]
            opt = [f for f, _, r in schema if not r]
            fields = "必需: " + ", ".join(req)
            if opt:
                fields += "；可选: " + ", ".join(opt)
        lines.append(f"{i:2}. {MODEL_TITLES[m]}  ({m})\n"
                     f"     {MODEL_DESC[m]}\n"
                     f"     字段: {fields}")
    return "\n".join(lines)


# ---------- 双源字典差异核对（自动读 ∩ 手动提供）----------
def _norm_type(t):
    """把数据库类型归一化为大类，便于跨方言比对类型一致性。"""
    t = (t or "").lower()
    t = re.sub(r"\(.*?\)", "", t).strip()      # 去掉 (n) / (precision,scale)
    t = t.split()[0]                            # 去掉修饰
    mapping = {
        "int": "integer", "bigint": "integer", "smallint": "integer",
        "tinyint": "integer", "mediumint": "integer", "integer": "integer",
        "serial": "integer", "identity": "integer",
        "numeric": "number", "decimal": "number", "float": "number",
        "double": "number", "real": "number", "money": "number",
        "varchar": "string", "char": "string", "text": "string",
        "nvarchar": "string", "longtext": "string", "clob": "string",
        "string": "string",
        "datetime": "datetime", "timestamp": "datetime", "date": "date",
        "time": "time",
        "boolean": "boolean", "bool": "boolean", "bit": "boolean",
    }
    return mapping.get(t, t) or "unknown"


def canonize_dict(raw):
    """接受多种字典形态，统一为 {'tables':[{'table','columns':[{'name','type','nullable','comment'}]}]}。

    支持：
      A) 标准结构 {'tables':[{'table','columns':[{'name','type',...}]}]}
      B) 松散结构 {'table': ['col1','col2']}
      C) 松散结构 {'table': {'col': 'type', ...}}
    """
    if isinstance(raw, dict) and "tables" in raw and isinstance(raw["tables"], list):
        out = []
        for t in raw["tables"]:
            cols = []
            for c in t.get("columns", []):
                if isinstance(c, dict):
                    cols.append({"name": c.get("name") or c.get("col"),
                                 "type": c.get("type", ""),
                                 "nullable": c.get("nullable", ""),
                                 "comment": c.get("comment", "")})
                elif isinstance(c, str):
                    cols.append({"name": c, "type": "", "nullable": "", "comment": ""})
            out.append({"table": t.get("table") or t.get("name"), "columns": cols})
        return {"tables": out}
    if isinstance(raw, dict):
        out = []
        for tbl, cols in raw.items():
            c_list = []
            if isinstance(cols, list):
                for c in cols:
                    if isinstance(c, str):
                        c_list.append({"name": c, "type": "", "nullable": "", "comment": ""})
                    elif isinstance(c, dict):
                        c_list.append({"name": c.get("name"), "type": c.get("type", ""),
                                       "nullable": "", "comment": c.get("comment", "")})
            elif isinstance(cols, dict):
                for cn, ct in cols.items():
                    c_list.append({"name": cn, "type": ct if isinstance(ct, str) else "",
                                   "nullable": "", "comment": ""})
            out.append({"table": tbl, "columns": c_list})
        return {"tables": out}
    raise SystemExit("无法识别的字典格式，请使用标准结构或 {'表':[列,...]} / {'表':{列:类型}}")


def diff_dictionaries(auto, manual):
    """比对自动读取字典与手动提供字典，返回结构化差异。"""
    a = canonize_dict(auto)
    b = canonize_dict(manual)
    a_tables = {t["table"]: {c["name"]: c for c in t["columns"]} for t in a["tables"]}
    b_tables = {t["table"]: {c["name"]: c for c in t["columns"]} for t in b["tables"]}

    only_a = [t for t in a_tables if t not in b_tables]
    only_b = [t for t in b_tables if t not in a_tables]
    shared = [t for t in a_tables if t in b_tables]

    col_only_a, col_only_b, type_mismatch = [], [], []
    for t in shared:
        ac, bc = a_tables[t], b_tables[t]
        for cn in ac:
            if cn not in bc:
                col_only_a.append((t, cn))
        for cn in bc:
            if cn not in ac:
                col_only_b.append((t, cn))
        for cn in ac:
            if cn in bc:
                ta, tb = _norm_type(ac[cn]["type"]), _norm_type(bc[cn]["type"])
                if ta and tb and ta != tb:
                    type_mismatch.append((t, cn, ac[cn]["type"], bc[cn]["type"]))

    n_a = sum(len(v) for v in a_tables.values())
    n_b = sum(len(v) for v in b_tables.values())
    return {
        "summary": {
            "tables_auto": len(a_tables), "tables_manual": len(b_tables),
            "cols_auto": n_a, "cols_manual": n_b,
            "tables_only_auto": only_a, "tables_only_manual": only_b,
            "cols_only_auto": col_only_a, "cols_only_b": col_only_b,
            "type_mismatch": type_mismatch,
        },
        "only_a": only_a, "only_b": only_b,
        "col_only_a": col_only_a, "col_only_b": col_only_b,
        "type_mismatch": type_mismatch,
    }


def diff_markdown(d):
    """把 diff 结果渲染为 Markdown 报告。"""
    s = d["summary"]
    lines = ["# 双源数据字典差异核对（自动读取 ∩ 手动提供）", "",
             f"- 自动读取：{s['tables_auto']} 张表 / {s['cols_auto']} 个字段",
             f"- 手动提供：{s['tables_manual']} 张表 / {s['cols_manual']} 个字段", ""]
    if not (s["tables_only_auto"] or s["tables_only_manual"]
            or s["cols_only_auto"] or s["cols_only_b"] or s["type_mismatch"]):
        lines.append("✅ **两源完全一致**，字段映射可放心采用。")
        return "\n".join(lines) + "\n"
    if s["tables_only_auto"]:
        lines.append(f"⚠️ 仅自动有（手动缺失）的表：{', '.join(s['tables_only_auto'])}")
    if s["tables_only_manual"]:
        lines.append(f"⚠️ 仅手动有（自动缺失）的表：{', '.join(s['tables_only_manual'])}")
    if s["cols_only_auto"]:
        lines.append("⚠️ 仅自动有（手动缺失）的字段：" + "; ".join(f"{t}.{c}" for t, c in s["cols_only_auto"]))
    if s["cols_only_b"]:
        lines.append("⚠️ 仅手动有（自动缺失）的字段：" + "; ".join(f"{t}.{c}" for t, c in s["cols_only_b"]))
    if s["type_mismatch"]:
        lines.append("⚠️ 类型不一致：" + "; ".join(f"{t}.{c}(自动 {at} ≠ 手动 {bt})"
                                                  for t, c, at, bt in s["type_mismatch"]))
    lines += ["",
              "> 差异项请与用户复核：是手动字典笔误，还是自动读取权限不足导致漏表/漏列？"
              "一致性确认后再执行分析。"]
    return "\n".join(lines) + "\n"
