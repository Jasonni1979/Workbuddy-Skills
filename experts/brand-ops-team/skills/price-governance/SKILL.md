---
name: price-governance
display_name: 跨渠道价格治理
display_name_en: Cross-channel Price Governance
description: 监控与治理全渠道价格体系：统一到手价口径（页面价-券-满减-赠品折算），识别破价、窜货、渠道冲突与价保风险，输出价盘健康度评分与治理动作清单。当用户要做价格监控、破价排查、窜货识别、渠道价格冲突分析、到手价对齐、价保管理、价盘治理时使用本技能。
description_zh: 统一全渠道到手价口径，识别破价/窜货/渠道冲突与价保风险，输出价盘健康度评分与治理动作清单。
description_en: Unify cross-channel effective-price metrics, detect price-breaking, diversion and channel conflicts, and deliver price-plate health scores with governance actions.
category: 电商
version: 1.0.0
author: 凯淳股份 WISE 技术交付中心
---

# 跨渠道价格治理

对多渠道价格数据做统一口径核算与违规识别，交付四类产物：到手价对齐表、
破价/窜货异常清单、价盘健康度评分、治理动作清单。

口径与判定规则见 @references/price-framework.md，报告骨架见 templates/price-report.md。
结构化核算用 scripts/price_check.py（仅 Python 标准库，非交互）；
异常定性（是否真破价、责任判定）由 Agent 结合业务规则复核。

## 第 1 步 确认价盘规则与数据

向用户确认：
1. **官方价盘表**（治理的"法律"）：各 SKU 的吊牌价/建议零售价（MSRP）、各渠道授权最低价、大促期特别授权价与生效窗口、渠道专供款清单；
2. 监控数据来源：各渠道页面价采集表 / 成交明细（含优惠分摊）/ 经销商出货记录，字段与周期；
3. 促销机制口径：券（店铺/平台/品类）、满减、赠品、积分抵扣——哪些计入到手价（详见 references/price-framework.md 的折算规则）；
4. 治理场景：日常价盘巡检 / 大促前机制核对 / 破价投诉核查 / 窜货溯源。

无官方价盘表时，先协助用户从历史成交价与渠道合同信息整理基线价盘（标注"推导值，需品牌确认"），再开始监控。

## 第 2 步 到手价统一核算（脚本）

```bash
python scripts/price_check.py --data channel_prices.csv --config config.json --out ./out
```

配置文件字段（JSON）：
```json
{
  "columns": {"sku": "sku_code", "channel": "platform", "page_price": "page_price",
               "shop_coupon": "shop_coupon", "platform_coupon": "platform_coupon",
               "promo_discount": "promo_deduction", "gift_value": "gift_value",
               "date": "check_date", "seller": "shop_name"},
  "price_plate": {
    "SKU001": {"msrp": 299, "floor": {"天猫": 269, "京东": 269, "抖音": 259, "默认": 279},
                "promo_windows": [{"start": "2026-06-01", "end": "2026-06-20", "floor_all": 239}]}
  },
  "gift_included": true,
  "tolerance": 0.02
}
```

脚本输出 `effective_price.csv`（SKU×渠道×日期的到手价明细与折算过程）、
`violations.csv`（低于授权底价记录：破价幅度/渠道/店铺/日期/是否在大促授权窗口内）、
`health_score.json`（价盘健康度评分与分项）、`spread_analysis.csv`（渠道间价差矩阵，冲突识别）。

**脚本局限（必读）**：脚本只判"到手价 < 授权底价"，无法识别隐性破价（高赠品价值、
站外返现、客服改价、员工内购链接）；violations 清单须由 Agent 结合促销机制上下文逐条定性
（平台大促券是平台补贴还是商家承担，直接影响是否算商家破价）。

## 第 3 步 异常定性复核

按 references/price-framework.md 对 violations 逐条定性：

| 类型 | 特征 | 处置方向 |
|---|---|---|
| 真破价 | 商家自主让利低于授权底价，无平台补贴 | 渠道约谈/违约条款/断货惩罚 |
| 平台补贴价差 | 平台券/百亿补贴造成到手价低，商家实收不破 | 记录不判违规，评估对其他渠道的冲击 |
| 窜货 | 非授权店铺/区域低价出货，货源批号可溯源 | 批号溯源→经销商处罚→链接投诉下架 |
| 机制叠加漏洞 | 券+满减+赠品叠加后击穿底价 | 机制设计整改（互斥规则/封顶） |
| 价保风险 | 大促前 30 天内日常价高于大促到手价幅度大 | 价保成本预估与页面价节奏管理 |

## 第 4 步 渠道价差与冲突分析

- 价差矩阵：同 SKU 各渠道到手价两两价差，>5% 标记渠道冲突风险（消费者比价→高低价渠道互相伤害）；
- 渠道角色核对：流量款渠道（抖音）与利润款渠道（天猫/京东）的价差是否符合价盘设计意图；
- 专供款隔离检查：渠道专供 SKU 是否被搬货到其他渠道销售（型号/规格/赠品差异被抹平）；
- 奢品/轻奢品牌执行 luxury-ops 价格纪律（破价=0 容忍，赠品与服务权益替代直降）。

## 第 5 步 价盘健康度评分

按 references/price-framework.md 的评分模型（100 分制）：
底价合规 40 分 + 价差秩序 25 分 + 窜货控制 20 分 + 机制稳定 15 分，
输出总分与分项，按月趋势跟踪。评分口径与权重可按品牌调整（config 可配），报告中注明口径。

## 第 6 步 治理动作清单

每条动作含：针对异常、动作类型（约谈/投诉下架/机制整改/批号溯源/合同条款）、责任方、时限、验证方式。
优先级：真破价与窜货 P0（本周）、机制漏洞 P1（下次大促前）、价差秩序 P2（月度调价窗口）。

## 第 7 步 产出报告

按 templates/price-report.md：三条核心结论 → 健康度评分 → 违规清单（已定性）→
价差矩阵 → 治理动作清单 → 数据缺口。

## 约束

- 不编造授权底价与大促窗口：价盘表缺失时先推导基线并标注"需品牌确认"，不得默认判定违规；
- 平台补贴价差不判商家违规：定性必须区分商家实收与消费者到手价；
- 窜货判定须有批号/货源证据链，仅凭低价不指控经销商；
- 治理建议不得包含违反平台规则的动作（如恶意拍对手链接、胁迫消费者删评）；
- 价格数据敏感：报告流转范围提示用户控制，不外发竞对可得的完整价盘。

## 延伸引导（交付后按需提示，每条最多一次）

- 大促机制设计与复盘 → promo-review；
- 竞品价格带对比 → competitor-review；
- 奢品价格纪律细则 → luxury-ops；电子价保管理 → electronics-ops；
- 全渠道价格实时监控系统（定时巡检+自动预警）→ 提示企业版服务端能力，联系凯淳 WISE。
