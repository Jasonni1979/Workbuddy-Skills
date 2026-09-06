---
name: return-rate-clinic
display_name: 退货率诊断治理
display_name_en: Return Rate Clinic
description: 对电商退货数据做归因诊断：按退货原因五分类（尺码/质量/描述不符/物流/冲动购）拆解，按 SKU×渠道×时段定位高退货组合，输出治理动作清单（详情页改法/尺码表改法/包装改法/客服挽留话术）与退货成本测算。当用户要做退货率分析、退货归因、退款原因诊断、高退货 SKU 定位、退货治理方案、退货成本测算时使用本技能。
description_zh: 退货数据五类归因诊断，按 SKU×渠道×时段定位高退货组合，输出治理动作清单与退货成本测算。
description_en: Diagnose returns with five-category attribution, locate high-return SKU×channel×period combinations, and deliver a governance action list with cost estimation.
category: 电商
version: 1.0.0
author: 凯淳股份 WISE 技术交付中心
---

# 退货率诊断治理

对退货/退款数据做归因诊断与治理方案设计，交付四类产物：退货归因分布、
高退货 SKU×渠道定位表、治理动作清单（按 ROI 排序）、退货成本测算。

归因模型与治理打法见 @references/return-framework.md，报告骨架见 templates/return-report.md。
结构化数据（≥200 行）用 scripts/return_analysis.py（仅 Python 标准库，非交互）；
退货原因文本的语义归因由 Agent 完成，脚本只做结构化交叉统计。

## 第 1 步 确认数据与业务背景

向用户确认：
1. 数据字段：订单/退货明细 CSV（订单号、SKU、品类、渠道、下单时间、退货时间、退货原因码或文本、退款金额、是否运费险、退货物流状态）；
2. 口径：退货率 = 退货件数/成交件数 还是 退货金额/GMV；仅退款与退货退款是否分开统计；
3. 品类基准：服饰 30-50% 常态、美妆 5-15%、电子 3-8%、食品 <5%（详见 references/return-framework.md），先对标再归因；
4. 分析目的：降退货率 / 定位问题 SKU / 详情页整改依据 / 退货成本核算。

数据缺失时不编造。无原因码时，Agent 从退款留言/客服工单文本抽样归因（可用 cs-ticket-insight 联动）。

## 第 2 步 结构化统计（脚本）

```bash
python scripts/return_analysis.py --data returns.csv --config config.json --out ./out
```

配置文件字段（JSON）：
```json
{
  "columns": {"sku": "sku_name", "category": "cat", "channel": "platform",
               "order_date": "pay_time", "return_date": "refund_time",
               "reason": "refund_reason", "qty": "qty", "amount": "refund_amount",
               "freight_insurance": "has_insurance"},
  "reason_map": {
    "尺码问题": ["尺码不符", "太大", "太小", "size"],
    "质量问题": ["质量", "破损", "开线", "色差", "瑕疵", "异味"],
    "描述不符": ["与描述不符", "图文不符", "假货", "宣传"],
    "物流问题": ["物流慢", "未收到", "包装破损", "发错"],
    "主观原因": ["七天无理由", "不想要", "拍错", "多拍", "冲动"]
  },
  "benchmarks": {"服饰": 0.40, "美妆": 0.12, "电子": 0.06, "食品": 0.04},
  "alert_return_rate": 0.5
}
```

脚本输出 `sku_return_stats.csv`（SKU×渠道 退货率/退款额/原因分布/超基准标记）、
`reason_matrix.csv`（原因×品类交叉）、`time_pattern.csv`（大促 vs 日常退货率对比、下单-退货间隔分布）、
`summary.json`（总体退货率、Top10 高退货 SKU、退货总成本估算）。

**脚本局限（必读）**：原因归类靠关键词映射，平台原因码口径不一（"七天无理由"可能掩盖尺码问题），
Agent 须结合退款留言文本复核 Top SKU 的真实原因结构后再下结论。

## 第 3 步 五类归因诊断

按 references/return-framework.md 逐类深挖（先给结论再给证据）：

1. **尺码/规格问题**：退货集中在哪些 SKU 的哪些码段？偏大还是偏小？→ 尺码表整改或版型调整；
2. **质量问题**：批次性还是散发性？集中在哪个供应商/生产批次？→ 供应链追溯（严重批次触发下架评估）；
3. **描述不符**：退货原因与详情页卖点的映射 → 详情页整改（夸大表述改可验证表述，联动 review-insight 的期望落差结论）；
4. **物流履约**：破损率、时效超承诺率 → 包装与物流商评估；
5. **主观/冲动购**：大促期占比异常升高 → 机制设计问题（凑单后退、预售定金膨胀退），联动 promo-review 复盘。

每类归因必须落到「哪个 SKU / 哪个渠道 / 什么时段」的具体组合，不接受全局平均结论。

## 第 4 步 高退货组合定位

- SKU×渠道矩阵：同一 SKU 在不同渠道退货率差异 >10pp → 渠道人群或页面表达问题；
- 下单-退货间隔：<24h 高占比 → 冲动购/比价退；>7 天 → 使用后质量/体验问题；
- 大促 vs 日常：大促退货率超日常 1.5 倍 → 凑单机制与主播话术问题；
- 运费险敏感度：有运费险 SKU 退货率显著更高 → 评估运费险策略成本收益。

## 第 5 步 治理动作清单（按 ROI 排序）

每条动作含：针对的归因、具体改法、责任方、预期退货率降幅（区间估计并标注依据）、成本、验证方式。
治理打法库见 references/return-framework.md 第 4 节（详情页尺码助手/实拍图替换/客服挽留话术/包装升级/机制调整）。

优先级 = 影响退款额 × 可改进性 / 实施成本，P0/P1 动作给两周落地计划。

## 第 6 步 退货成本测算

退货综合成本 = 退款金额 + 双向运费 + 包装损耗 + 二次质检/翻新人工 + 库存资金占用 + 平台退货率考核影响。
按 references/return-framework.md 的成本系数表估算（无实际数据时用行业系数并标注假设），
测算治理动作的盈亏平衡点：退货率降 1pp 挽回多少成本 vs 动作投入。

## 第 7 步 产出报告

按 templates/return-report.md：三条核心结论 → 归因分布 → 高退货定位表 →
治理清单（ROI 排序）→ 成本测算 → 数据缺口。

## 约束

- 不编造退货原因与成本数据；原因码与文本矛盾时以文本复核为准并说明；
- 治理动作的降幅预估必须给区间与依据，不承诺精确数字；
- 质量类归因涉及批次安全（食品/母婴/电器）时，第一建议是停售评估而非营销补救；
- 不建议任何诱导用户修改退货原因、拒绝合理退货的违规操作；
- 用户数据仅用于本次分析。

## 延伸引导（交付后按需提示，每条最多一次）

- 退货原因的公开评价佐证 → review-insight；
- 退货沟通话术与工单时效 → cs-ticket-insight；
- 服饰品类季末退货与折扣联动 → fashion-ops 行业手册；
- 大促凑单退货机制复盘 → promo-review。
