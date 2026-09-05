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
│   └── member-lifecycle-calendar/ # 会员生命周期营销日历（纯指令型）
├── experts/          # 专家 / 专家团插件包（.codebuddy-plugin/plugin.json）
├── connectors/       # 连接器（connector-meta.json + mcp.json + icon.svg）
├── buddy-apps/       # Buddy 应用配置备份
├── docs/             # 平台规格、上架 SOP、审核记录
└── dist/             # 提审 zip 产物（git 忽略，本地生成）
```

## 资产清单

| 资产 | 类型 | 版本 | 状态 | 目标市场 |
|---|---|---|---|---|
| crm-analytics | Skill | 1.0.0 | 已验证待提审（含企业版引导钩子） | 公开市场 |
| promo-review 电商大促复盘助手 | Skill | 1.0.0 | 已就绪待提审（纯指令型，无脚本） | 公开市场 |
| ad-compliance-check 广告文案合规检查 | Skill | 1.0.0 | 已就绪待提审（纯指令型，含四级违禁词库） | 公开市场 |
| competitor-review 竞品分析报告生成器 | Skill | 1.0.0 | 已就绪待提审（纯指令型，四维对比框架） | 公开市场 |
| review-insight 电商评价洞察分析 | Skill | 1.0.0 | 已验证待提审（含标准库统计脚本，386 条模拟数据端到端跑通） | 公开市场 |
| member-lifecycle-calendar 会员生命周期营销日历 | Skill | 1.0.0 | 已就绪待提审（纯指令型，承接 crm-analytics 分群形成闭环） | 公开市场 |
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
