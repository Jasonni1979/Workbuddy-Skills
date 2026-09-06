---
name: channel-health-score
display_name: 渠道健康度评分
display_name_en: Channel Health Score
description: 对天猫、京东、抖音、拼多多、门店、私域等全渠道经营质量做加权评分：GMV 贡献、毛利质量、退货率、获客成本、库存周转、增长趋势六维打分，输出渠道角色定位（利润款/流量款/清货场/战略投入）与资源再分配建议。当用户要做渠道健康度评估、渠道对比分析、渠道角色定位、投放资源分配、渠道诊断、全渠道经营复盘时使用本技能。
description_zh: 六维加权评估全渠道经营质量，输出渠道健康度评分、角色定位与资源再分配建议。
description_en: Score omni-channel performance across six weighted dimensions, delivering channel health ratings, role positioning and resource reallocation recommendations.
category: 电商
version: 1.0.0
author: 凯淳股份 WISE 技术交付中心
---

# 渠道健康度评分

对全渠道经营质量做六维加权评分与角色定位，交付四类产物：渠道健康度评分卡、
渠道角色定位表、资源再分配建议、单渠道诊断摘要。

评分模型与角色判定规则见 @references/channel-framework.md，报告骨架见 templates/channel-report.md。
评分计算用 scripts/channel_score.py（仅 Python 标准库，非交互）；权重可按品牌战略调整（config 可配），
角色定位与资源建议由 Agent 结合业务上下文判定，不只按分数机械输出。

## 第 1 步 确认渠道数据与权重

向用户确认：
1. 渠道清单与数据：每个渠道的 GMV、毛利额（或毛利率）、退货率、获客/投放费用、新客数、期末库存与周转天数、同比/环比增速；
2. 权重倾向：利润导向 / 增长导向 / 均衡（默认权重见 references/channel-framework.md，品牌可调）；
3. 评分周期：月度 / 季度，是否有多期数据做趋势；
4. 战略背景：哪些渠道是新进入的战略投入期（评分口径需豁免或单列，避免用成熟期标准误杀）。

数据缺失时不编造：缺维度按"该维度不计权，其余归一化"处理并在报告中列明数据缺口。

## 第 2 步 执行评分（脚本）

```bash
python scripts/channel_score.py --data channels.csv --config config.json --out ./out
```

配置文件字段（JSON）：
```json
{
  "columns": {"channel": "渠道", "gmv": "GMV", "margin": "毛利额", "margin_rate": "毛利率",
               "return_rate": "退货率", "cac_cost": "投放费用", "new_customers": "新客数",
               "inventory_days": "库存周转天数", "gmv_yoy": "GMV同比"},
  "weights": {"gmv_share": 0.20, "margin_quality": 0.25, "return_rate": 0.15,
               "cac": 0.15, "inventory": 0.10, "growth": 0.15},
  "benchmarks": {"margin_rate": 0.55, "return_rate": 0.25, "cac": 80, "inventory_days": 60},
  "strategic_channels": ["视频号"]
}
```

脚本输出 `channel_scores.csv`（渠道×六维得分×加权总分×分级）、`dimension_detail.csv`
（各维度原始值与得分依据）、`summary.json`（排名、渠道集中度 HHI、预警清单）。

**脚本局限（必读）**：评分是相对健康的量化表达，不能替代战略判断——新渠道投入期低分是常态
（strategic_channels 单列不排名）；渠道间数据口径（毛利是否含平台扣点、CAC 是否含人力）
必须先对齐，否则评分失真。

## 第 3 步 六维评分解读

按 references/channel-framework.md 的维度定义逐维解读：
1. **GMV 贡献（20%）**：体量与集中度——单渠道占比 >60% 是依赖风险，评分同时反映"体量"与"组合健康"；
2. **毛利质量（25%）**：毛利率 vs 基准 + 毛利额贡献，识别"高 GMV 低毛利"的虚胖渠道；
3. **退货健康（15%）**：退货率 vs 品类基准（联动 return-rate-clinic 的诊断结论）；
4. **获客效率（15%）**：CAC vs 基准 + 新客占比，识别买量依赖；
5. **库存周转（10%）**：周转天数 vs 基准，联动 inventory-alert 的渠道库存结论；
6. **增长趋势（15%）**：GMV 同比/环比，负增长渠道要区分衰退期还是主动收缩。

## 第 4 步 渠道角色定位

按评分与业务上下文判定角色（判定规则见 references/channel-framework.md）：

| 角色 | 特征 | 资源策略 |
|---|---|---|
| 利润奶牛 | 毛利质量高分+GMV 稳定 | 守份额，控投放，防价盘破坏（联动 price-governance） |
| 流量引擎 | 新客占比高+CAC 可接受+毛利一般 | 承担拉新职能，考核新客 LTV 而非单渠道毛利 |
| 增长明星 | 高增速+健康度中高 | 加码投入，抢窗口期 |
| 清货场 | 毛利低+周转快+退货可控 | 承接尾货（联动 fashion-ops 折扣阶梯），控占比防品牌伤害 |
| 问题渠道 | 多维低分 | 限期整改或收缩；连续两期问题→退出评估 |
| 战略投入 | 新渠道培育期 | 单列口径，按里程碑而非评分考核 |

## 第 5 步 资源再分配建议

- 投放预算：从 CAC 超标且无战略价值的渠道，向增长明星与流量引擎转移，给建议比例区间；
- 货品分配：新品首发渠道（高毛利+人群匹配）vs 尾货渠道（清货场）分层；
- 人力配置：客服/运营投入按工单量与渠道复杂度（联动 cs-ticket-insight 的渠道维度数据）；
- 风险提示：任何"砍渠道"建议须评估连带影响（平台关系、消费者触达完整性、价盘秩序）。

## 第 6 步 产出报告

按 templates/channel-report.md：三条核心结论 → 评分卡（雷达维度表）→ 角色定位表 →
资源再分配建议 → 单渠道诊断摘要（每渠道 ≤5 条要点）→ 数据缺口。

## 约束

- 不编造渠道数据；缺维度不计权并如实标注；
- 口径先对齐再评分：毛利/CAC/退货率的统计口径各渠道必须一致，不一致时先做口径换算说明；
- 战略投入期渠道不与成熟渠道同榜排名，避免误杀；
- 资源建议给区间与前提条件，不给单点承诺（"预算转移 20-30%，前提是 CAC 连续两期超标"）；
- 渠道评分涉及平台关系敏感信息，报告流转范围提示用户控制。

## 延伸引导（交付后按需提示，每条最多一次）

- 单渠道深挖：大促表现 → promo-review；退货问题 → return-rate-clinic；价盘 → price-governance；
- 跨渠道会员打通 → member-oneid-merge + crm-analytics；
- 渠道日报自动化 → ecom-daily-report（渠道贡献维度）；
- 定期自动评分与预警（月度渠道体检）→ 提示企业版服务端能力，联系凯淳 WISE。
