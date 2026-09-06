# 品牌客户运营专家团（brand-ops-team）

> 凯淳股份 WISE 技术交付中心出品 ｜ v1.0.0 ｜ expertType=team ｜ categoryId=07-SalesCommerce

面向品牌电商全链路运营的**五人专家团**：主理人统筹分诊，四位专家分别负责数据洞察、会员 CRM、内容种草、渠道治理与行业打法。**内嵌 23 个实战技能**（通用能力层 10 + 行业参数层 6 + 全渠道运营层 7），召唤即得完整运营工具箱。

## 团队结构

```
brand-ops-team/
├── .codebuddy-plugin/plugin.json     # team 配置：teamInfo + 23 技能路径
├── agents/
│   ├── brand-ops-team-lead.md        # 主理人「凯队长」：分诊→派单→汇总把关
│   ├── brand-ops-data-analyst.md     # 数析：日报/大促复盘/多平台合并/库存/竞品/评价
│   ├── brand-ops-member-expert.md    # 会运营：CRM分群/生命周期日历/One-ID/私域SOP
│   ├── brand-ops-content-expert.md   # 种草：内容矩阵/短视频脚本/广告合规
│   └── brand-ops-channel-expert.md   # 渠道官：渠道健康度/价盘/工单/退货/六大行业手册
├── skills/                           # 内嵌 23 技能（与资产仓库 skills/ 同步）
├── avatars/                          # 5 张 512×512 头像（品牌色 #185FA5）
└── README.md
```

## 成员 × 技能分工

| 成员 | 预加载技能（frontmatter.skills） |
|---|---|
| 凯队长（主理人） | 不预加载，靠派单调度全团 23 技能 |
| 数析 | ecom-daily-report、promo-review、multi-platform-merge、inventory-alert、competitor-review、review-insight |
| 会运营 | crm-analytics、member-lifecycle-calendar、member-oneid-merge、private-domain-sop |
| 种草 | content-matrix-planner、video-script-planner、ad-compliance-check |
| 渠道官 | channel-health-score、price-governance、cs-ticket-insight、return-rate-clinic + 六大行业手册（beauty/fashion/luxury/electronics/sports/liquor-ops） |

## 工作机制

1. **分诊**：主理人识别问题域（数据/会员/内容/渠道×行业），跨域问题拆子任务并行派发。
2. **行业参数注入**：渠道官先锁行业，用行业手册基准替换通用技能默认参数，输出显式标注"已应用 X 行业参数"。
3. **合规一票否决**：对外内容过广告合规检查、会员数据匿名化、强监管行业（酒类/美妆）红线前置。
4. **收口**：主理人检查口径一致性后，按"结论先行→关键数据表→分域详情→P0/P1/P2 行动清单"输出。

## 红线

- 无绝对路径、无凭据硬编码、无交互式输入（继承技能层全部红线）
- 高价值算法保留在技能脚本内（标准库、参数化、非联网）
- 权属：仅凯淳自有方法论与代码

## 提审物料

- zip：`dist/brand-ops-team-v1.0.0-submit.zip`（根目录为包名目录）
- 头像 5 张：512×512 PNG ≤500KB，品牌色 #185FA5
- 示例问句 3 条：见 plugin.json quickPrompts（与 defaultInitPrompt 第一条一致）
