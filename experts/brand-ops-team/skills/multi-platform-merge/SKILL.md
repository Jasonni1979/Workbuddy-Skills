---
name: multi-platform-merge
display_name: 多平台销售数据合并对齐
display_name_en: Multi-platform Sales Data Merge and Alignment
description: 将天猫、京东、抖音、拼多多等多平台导出的销售/订单/流量数据做字段映射与口径统一，合并为一张标准化明细表，输出合并 CSV、口径对照表与数据质量报告，结果可直接供 CRM 分析技能使用。当用户要做多平台数据合并、跨平台数据对齐、全渠道销售汇总、平台报表口径统一、生意参谋与商智罗盘数据整合时使用本技能。
description_zh: 多平台销售数据字段映射与口径统一，合并为标准化明细表并输出数据质量报告。
description_en: Map and unify fields across Tmall, JD, Douyin and PDD exports into one standardized sales table with a caliber dictionary and data quality report.
category: 数据分析
version: 1.0.0
author: 凯淳股份 WISE 技术交付中心
---

# 多平台销售数据合并对齐

把各电商平台导出的异构报表（字段名、口径、时间粒度、金额单位各不相同）
合并为一张标准化销售明细表，交付三类产物：合并 CSV、口径对照表、数据质量报告。

平台字段映射与口径规则见 @references/platform-caliber.md，报告骨架见 templates/merge-report.md。
合并执行用 scripts/merge_platforms.py（仅依赖 Python 标准库，非交互）。

## 第 1 步 盘点输入文件

向用户确认并检查每个平台文件：
1. 平台与报表类型（销售明细 / 订单明细 / 流量日报 / 商品分析）；
2. 文件格式：CSV 或 Excel（Excel 需先另存 CSV，或告知 Agent 用 openpyxl 转换）；
3. 时间范围与粒度（日/周/月/订单级）；
4. 关键字段抽查：日期、商品、销售额、销量、退款、流量——缺哪个记哪个。

用 `--inspect` 模式先预览每个文件的表头与前 5 行，确认编码（UTF-8/GBK）与分隔符：

```bash
python scripts/merge_platforms.py --inspect <文件1> <文件2> ...
```

## 第 2 步 生成映射配置

按 references/platform-caliber.md 的字段映射表，为每个文件写映射 JSON（可由 Agent 起草后与用户确认）：

```json
{
  "platform": "tmall",
  "file": "tmall_sales_202608.csv",
  "encoding": "utf-8-sig",
  "granularity": "daily",
  "columns": {
    "date": "统计日期", "sku": "商品ID", "sku_name": "商品名称",
    "gmv": "支付金额", "qty": "支付件数", "refund": "成功退款金额",
    "uv": "访客数", "orders": "支付订单数"
  },
  "date_format": "%Y-%m-%d",
  "amount_unit": "yuan",
  "dedup_keys": ["date", "sku"]
}
```

口径决策必须显式确认（默认值见 references）：
- GMV 口径：支付金额（含未发货）vs 成交金额（剔除取消）——默认支付金额，报告注明；
- 退款口径：是否从 GMV 扣除——默认单列 refund 不扣减，净销售额 = gmv − refund 另算；
- 金额单位：元/分——默认元，发现整数大额异常时提示确认是否"分"；
- 跨平台同款：SKU 编码不一致时用商品名称模糊匹配或用户提供的对照表（spu_map）。

## 第 3 步 执行合并与质量检查

```bash
python scripts/merge_platforms.py --config <映射JSON数组文件> --out <输出目录>
```

脚本产出：
- `merged_sales.csv`：标准化明细（date/platform/sku/sku_name/gmv/qty/refund/uv/orders/net_gmv）；
- `caliber_dict.csv`：口径对照（平台×原始字段×标准字段×换算规则）；
- `quality_report.json`：每文件行数、空值率、日期解析失败数、重复键数、金额异常值（负数/极端值）清单。

Agent 必须阅读 quality_report.json 并向用户汇报：
1. 各平台行数与合并后行数（差异原因：去重/过滤）；
2. 日期解析失败与空值字段——是否需要补映射重跑；
3. 金额异常值样例——确认单位或口径后再定稿。

## 第 4 步 产出报告与下游衔接

按 templates/merge-report.md 输出合并报告：
- 各平台贡献占比（GMV/销量/流量）一张表；
- 口径决策记录（本次采用的 GMV/退款/单位口径，供后续复跑保持一致）；
- 数据质量结论与遗留问题清单。

下游衔接提示（每条最多一次）：
- 合并表可直接作为 crm-analytics 技能的输入做全渠道客户/商品分析；
- 需要按天监控合并结果异动 → ecom-daily-report 技能；
- 需要评估各平台竞争位置 → competitor-review 技能。

## 约束

- 不静默丢数据：任何被过滤/去重的行必须计入 quality_report 并说明原因；
- 不猜口径：映射与口径决策未经用户确认不得定稿，默认值须在报告中显式标注；
- 金额换算（分→元、含税→不含税）必须在 caliber_dict 中留痕，可复算；
- 脚本仅标准库、非交互、不联网；Excel 输入由 Agent 先转 CSV 再进脚本；
- 用户数据仅用于本次合并，输出文件不携带其他客户的残留数据。
