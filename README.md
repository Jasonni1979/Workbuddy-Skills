# wise-workbuddy-assets

凯淳股份 WISE 技术交付中心 · WorkBuddy 开放平台（open.workbuddy.cn）提审资产仓库。

管理四类上架资产：技能 Skill / 专家 Expert / 连接器 Connector / Buddy 应用，覆盖从开发、合规自检、打包、提审到版本迭代的全生命周期。

## 目录结构

```
wise-workbuddy-assets/
├── skills/           # 技能包（zip 根目录即 skills/）
│   ├── crm-analytics/            # CRM 数据分析与客户分群（已验证）
│   ├── promo-review/             # 电商大促复盘助手（纯指令型）
│   ├── ad-compliance-check/      # 广告文案合规检查（纯指令型）
│   ├── competitor-review/        # 竞品分析报告生成器（纯指令型）
│   ├── review-insight/           # 电商评价洞察分析（含标准库脚本）
│   ├── member-lifecycle-calendar/ # 会员生命周期营销日历（纯指令型）
│   ├── multi-platform-merge/     # 多平台销售数据合并对齐（标准库脚本）
│   ├── inventory-alert/          # 库存周转与补货预警（标准库脚本）
│   ├── ecom-daily-report/        # 电商数据日报周报自动化（标准库脚本）
│   ├── video-script-planner/     # 短视频脚本策划助手（纯指令型）
│   ├── beauty-ops/               # 行业层：美妆个护运营手册（纯指令型）
│   ├── fashion-ops/              # 行业层：快时尚服饰运营手册（纯指令型）
│   ├── luxury-ops/               # 行业层：轻奢奢品运营手册（纯指令型）
│   ├── electronics-ops/          # 行业层：消费电子运营手册（纯指令型）
│   ├── sports-ops/               # 行业层：运动户外运营手册（纯指令型）
│   ├── liquor-ops/               # 行业层：酒类运营手册（纯指令型）
│   ├── content-matrix-planner/   # 全渠道层：种草内容矩阵策划（纯指令型）
│   ├── cs-ticket-insight/        # 全渠道层：客服工单洞察分析（标准库脚本）
│   ├── return-rate-clinic/       # 全渠道层：退货率诊断治理（标准库脚本）
│   ├── private-domain-sop/       # 全渠道层：私域触达话术 SOP（纯指令型）
│   ├── member-oneid-merge/       # 全渠道层：全渠道会员 One-ID 合并（标准库脚本）
│   ├── price-governance/         # 全渠道层：跨渠道价格治理（标准库脚本）
│   └── channel-health-score/     # 全渠道层：渠道健康度评分（标准库脚本）
├── experts/          # 专家 / 专家团插件包（.codebuddy-plugin/plugin.json）
├── connectors/       # 连接器（connector-meta.json + mcp.json + icon.svg）
├── buddy-apps/       # Buddy 应用配置备份
├── docs/             # 平台规格、上架 SOP、审核记录
├── assets/           # 市场物料：技能头像（512×512）与生成脚本 make_avatars.py
└── dist/             # 提审 zip 产物（git 忽略，本地生成）
```

## 资产清单

> **三层技能架构**：通用能力层（10 技能，跨行业方法论与工具脚本）× 行业参数层（6 技能，每行业 1 个运营手册，注入品类基准/合规红线/专属打法，并以"参数注入表"改写通用技能的默认参数，命名约定 `*-ops`，头像带左上菱形角标）× 全渠道运营层（7 技能，覆盖种草→转化→售后→私域→数据底座的全链路闭环，头像无角标）。

| 资产 | 类型 | 版本 | 状态 | 目标市场 |
|---|---|---|---|---|
| crm-analytics | Skill | 1.0.0 | 已验证待提审（含企业版引导钩子） | 公开市场 |
| promo-review 电商大促复盘助手 | Skill | 1.0.0 | 已就绪待提审（纯指令型，无脚本） | 公开市场 |
| ad-compliance-check 广告文案合规检查 | Skill | 1.0.0 | 已就绪待提审（纯指令型，含四级违禁词库） | 公开市场 |
| competitor-review 竞品分析报告生成器 | Skill | 1.0.0 | 已就绪待提审（纯指令型，四维对比框架） | 公开市场 |
| review-insight 电商评价洞察分析 | Skill | 1.0.0 | 已验证待提审（含标准库统计脚本，386 条模拟数据端到端跑通） | 公开市场 |
| member-lifecycle-calendar 会员生命周期营销日历 | Skill | 1.0.0 | 已就绪待提审（纯指令型，承接 crm-analytics 分群形成闭环） | 公开市场 |
| multi-platform-merge 多平台销售数据合并对齐 | Skill | 1.0.0 | 已验证待提审（标准库脚本：GBK/分→元/汇总行过滤实测通过） | 公开市场 |
| inventory-alert 库存周转与补货预警 | Skill | 1.0.0 | 已验证待提审（标准库脚本：五级分级/安全库存/大促备货实测通过） | 公开市场 |
| ecom-daily-report 电商数据日报周报自动化 | Skill | 1.0.0 | 已验证待提审（标准库脚本：异动阈值/目标进度/渠道贡献实测通过） | 公开市场 |
| video-script-planner 短视频脚本策划助手 | Skill | 1.0.0 | 已就绪待提审（纯指令型，三段式 SOP+逐秒分镜+品类红线自查） | 公开市场 |
| beauty-ops 美妆个护行业运营手册 | Skill | 1.0.0 | 已就绪待提审（行业层：功效合规三档+T=60d+参数注入表） | 公开市场 |
| fashion-ops 快时尚服饰行业运营手册 | Skill | 1.0.0 | 已就绪待提审（行业层：售罄率模式+波段模型+折扣阶梯） | 公开市场 |
| luxury-ops 轻奢奢品行业运营手册 | Skill | 1.0.0 | 已就绪待提审（行业层：价格纪律+VIC clienteling+礼赠运营） | 公开市场 |
| electronics-ops 消费电子行业运营手册 | Skill | 1.0.0 | 已就绪待提审（行业层：贬值型库存+参数合规矩阵+配件复购引擎） | 公开市场 |
| sports-ops 运动户外行业运营手册 | Skill | 1.0.0 | 已就绪待提审（行业层：装备寿命复购+全渠道四源会员+KOC 运营） | 公开市场 |
| liquor-ops 酒类行业运营手册 | Skill | 1.0.0 | 已就绪待提审（行业层：广告法酒类红线+礼赠节点+稀缺配额管理） | 公开市场 |
| content-matrix-planner 种草内容矩阵策划 | Skill | 1.0.0 | 已就绪待提审（全渠道层：四象限配比+达人金字塔+排期选题卡） | 公开市场 |
| cs-ticket-insight 客服工单洞察分析 | Skill | 1.0.0 | 已验证待提审（全渠道层：SLA 三维+升级红橙黄+话术骨架，240 条实测） | 公开市场 |
| return-rate-clinic 退货率诊断治理 | Skill | 1.0.0 | 已验证待提审（全渠道层：五类归因+ROI 治理清单，300+900 条实测） | 公开市场 |
| private-domain-sop 私域触达话术 SOP | Skill | 1.0.0 | 已就绪待提审（全渠道层：五场景话术+频控硬约束+A/B 判定） | 公开市场 |
| member-oneid-merge 全渠道会员 One-ID 合并 | Skill | 1.0.0 | 已验证待提审（全渠道层：三层匹配+冲突裁决+合规前置，160 记录实测） | 公开市场 |
| price-governance 跨渠道价格治理 | Skill | 1.0.0 | 已验证待提审（全渠道层：双口径到手价+五类定性+健康度评分，48 条实测） | 公开市场 |
| channel-health-score 渠道健康度评分 | Skill | 1.0.0 | 已验证待提审（全渠道层：六维加权+角色定位+HHI，6 渠道实测） | 公开市场 |
| （规划）CRM 数据查询 MCP | Connector | — | 规划中 P1-C | 企业市场 |
| （规划）品牌客户运营专家团 | Expert Team | — | 规划中 P2 | 公开+企业 |

## 上架工作流

1. `skills/<name>/` 开发，本地干净 venv 端到端自验
2. 合规扫描：无绝对路径 / 无凭据 / 无交互式输入（`input()`/`getpass`）
3. 打包：`cd <repo> && zip -qr dist/<name>-v<version>-submit.zip skills/<name>`
4. 上传开放平台后台 → 补分类/服务类目/头像 → 提审（Skill 约 7 个工作日）
5. 审核记录归档到 `docs/review-log.md`，版本变更写入本 README 资产清单

## 红线（全资产通用）

- 禁硬编码：绝对路径、API Key、口令、内部域名
- 禁交互式输入：Agent 运行环境无 TTY
- 权属：仅凯淳自有方法论与代码；阿里共创内容零使用
- 高价值算法不落客户端：核心逻辑放服务端连接器（auth_mode: token）
- YAML：冒号后必须空格、避免引号；zip ≤ 20MB

## 相关链接

- 开放平台：https://open.workbuddy.cn
- 开放文档：https://open.workbuddy.cn/docs
- 技能规格：https://open.workbuddy.cn/docs/skill
- 连接器规格：https://open.workbuddy.cn/docs/connector
- 专家规格：https://open.workbuddy.cn/docs/expert
- 运营支持：openworkbuddy@tencent.com
