# CRM 首批上架 · 落地执行方案（假设开放平台申请已完成）

> v1.0 ｜ 2026-09-05 ｜ 依据《WorkBuddy 开放平台接口研究报告》
> 目标：4 周内完成 CRM 方向第一批资产上架（2 个 Skill 公开市场 + 1 个连接器 PoC 内部验证）

---

## 〇、执行总览

| 批次 | 资产 | 市场 | 周期 | 依赖 |
|---|---|---|---|---|
| P1-A | Skill：CRM 数据分析与客户分群（crm-analytics 合规版） | 公开 | D1-D5 | 无 |
| P1-B | Skill：电商大促复盘 / 会员运营分析 | 公开 | D3-D8 | 行业方法论提炼 |
| P1-C | 连接器 PoC：CRM 数据查询 MCP（token 模式） | 内部验证 | D5-D15 | 需 HTTPS 托管 |
| P2（并行预研） | 专家团"品牌客户运营专家团"（自带 MCP 依赖） | 公开+企业 | D15-D30 | P1-C 经验 |

---

## 一、P1-A：crm-analytics 合规上架（D1-D5，2 人日）

### 1.1 改造清单（已按研究报告 Gap 表确认）
1. **重写 SKILL.md frontmatter**（新文件，不改本地原版）：
```yaml
---
name: crm-analytics
display_name: CRM 数据分析与客户分群
display_name_en: CRM Analytics & Customer Segmentation
description: 分析 CRM 数据（CSV/Excel/SQLite），执行 RFM、客户分群、复购留存、增长漏斗、流失预警、CLV 等 10+ 模型，产出报告+分群表+图表。当用户要做客户分层、复购分析、留存、漏斗、流失预警、CLV、NPS 或 CRM 数据分析时使用。
description_zh: 连接或读取 CRM 数据，内置常用分析模型，产出报告、分群结果与图表。
description_en: Analyze CRM data with built-in models (RFM, cohort, funnel, churn, CLV) and deliver report, segments and charts.
category: 数据分析
version: 1.0.0
author: 凯淳股份 WISE 技术交付中心
---
```
2. **正文重写为"非交互优先"指令**：
   - 第 0 步环境准备：改为"探测 python3 → 在当前工作区建隔离 venv"（删除所有 /Users/wise01 绝对路径）；
   - 执行路径只写 `python scripts/crm_analyze.py --model X --data Y --config Z --outdir ./results`，先 `--dry-run` 预检再执行；
   - 禁止使用 --interactive 与 crm_connect.py（公开版不含这两个入口的凭据交互）；
   - 保留四步门控（模型清单→字段映射确认→预检→执行），但门控由 AI 对话完成，脚本全参数化。
3. **文件裁剪**：上架包只含 `SKILL.md + references/(models_catalog.md, db_dialects.md) + scripts/(crm_analyze.py, crm_schema.py, make_sample_db.py)`；**剔除 crm_connect.py、crm_receipt.py**（DB 直连与回款场景留给企业版/连接器）。
4. **新增 templates/report-template.md**（报告骨架，作为交付物规范）。
5. **示例数据**：make_sample_db.py 生成样例 SQLite/CSV，供用户零数据试玩（市场转化关键）。

### 1.2 市场展示物料
- 头像 512×512（K-AIDE 品牌色 #185FA5 系）；
- 服务类目：商业服务 / 电商（兜底），按审核反馈调整；
- 3 条示例问句（examples 用）："帮我做一份 RFM 客户分层"、"分析这批会员的复购和留存"、"做个增长漏斗看看哪步流失最多"。

### 1.3 自验与提审（D4-D5）
- 本地干净 venv 全流程跑通：--list-models / --dry-run / 完整执行（rfm + funnel 两个模型）；
- YAML 校验脚本检查（冒号空格、无引号、必填字段齐）；
- 打包 zip（≤20MB，根目录为 skills/crm-analytics/）→ 后台上传 → 补信息 → 提审。

### 1.4 验收标准
- [ ] 干净 macOS 环境零报错跑通 3 个模型
- [ ] frontmatter 解析一次通过
- [ ] 提审成功进入审核队列（7 工作日）

---

## 二、P1-B：电商大促复盘 / 会员运营分析（D3-D8，2 人日）

1. 从凯淳自有行业方法论提炼（**不碰阿里共创内容**）：大促复盘五段式（目标-流量-转化-客单-复购）、会员运营 AIPL/生命周期框架；
2. 形态：纯指令型 Skill（references 放方法论 md + templates 放报告模板），**无脚本依赖**，审核风险最低；
3. frontmatter 同上规范；category 选电商/营销类；
4. 与 P1-A 形成组合：P1-B 出分析框架与解读，P1-A 出数据计算——在两个 SKILL.md 的 description 中互相埋触发词，形成联动。

---

## 三、P1-C：CRM 数据查询连接器 PoC（D5-D15，3-4 人日）

### 3.1 目标
验证"用户自填 Token 模式 MCP 连接器"全链路，为阶段二 Weaver OA 连接器与企业版 CRM 连接器铺路。**不上公开市场，仅内部/企业市场验证。**

### 3.2 技术方案（严格对齐接口规格）
```
kaytune-crm/
├── connector-meta.json     # type: mcp, auth_mode: "token", source: kaytune-crm
├── mcp.json                # type: streamableHttp, url: https://<host>/mcp,
│                           #   headers: {Authorization: "Bearer ${CRM_TOKEN}"}, timeout: 30000
├── token-schema.json       # fields: CRM_TOKEN(password,required) + CRM_BASE_URL(text,默认值)
├── icon.svg                # 64×64
└── skills/crm-query/SKILL.md
```
- MCP Server 用 Python/TS SDK 实现，暴露 4 个工具：`crm_query_customers`、`crm_query_orders`、`crm_rfm_snapshot`、`crm_schema`；
- 全部只读、30s 内响应、错误返回可读信息；
- 托管：WISE 现有 HTTPS 出口（或腾讯云轻量），可用性 ≥99.9%；
- minWorkbuddyVersion: "4.23.0"（token 模式要求）。

### 3.3 验证清单
- [ ] WorkBuddy 客户端连接 → 弹表单 → 填 Token → 连接成功
- [ ] 自然语言"查一下最近 30 天新增客户"→ 工具调用正确返回
- [ ] Token 错误时返回可识别错误并引导重连
- [ ] 提交审核（连接器 10-15 分钟生效）

---

## 四、P2 预研：品牌客户运营专家团（D15-D30）

1. 结构：lead（运营策略主理人，前缀命名）+ 3 成员（数据分析/会员运营/内容协作）；
2. categoryId: 07-SalesCommerce；tags 3 个；quickPrompts 3 条（首条=defaultInitPrompt）；displayDescription 中文 40-50 字；
3. dependencies：`.mcp.json` 声明 P1-C 的 MCP（x-workbuddy auth.type=token + tokenSchema）→ 召唤前引导连接，实现"专家自带连接器"；
4. 人设文件只写方法论与流程（不可自定义 tools，能力靠 scripts/依赖 MCP）。

---

## 五、工程与合规基线（全批次通用）

| 项 | 规则 |
|---|---|
| 代码 | 禁硬编码绝对路径/凭据；禁 input()/getpass；脚本退出码+JSON 输出 |
| 权属 | 仅凯淳自有资产；阿里共创内容零使用 |
| 版本 | 只用基础字段；version 语义化递增 |
| 品牌 | 命名"凯淳/WISE"系，色 #185FA5；避开腾讯系仿冒禁词 |
| 审核沟通 | 解析失败邮件 openworkbuddy@tencent.com；入群获取类目建议 |
| 运营 | 上线后每周看调用量/活跃用户；按反馈迭代版本 |

---

## 六、人力与日历

| 日 | P1-A | P1-B | P1-C |
|---|---|---|---|
| D1-D2 | SKILL.md 重写+裁剪 | 方法论提炼 | — |
| D3-D4 | 自验+物料 | 编写+自验 | 方案设计 |
| D5 | **提审 A** | — | MCP Server 开发 |
| D6-D8 | 审核期（改 P2 人设） | **提审 B** | 开发+托管 |
| D9-D12 | 审核反馈修正 | 反馈修正 | 客户端联调 |
| D13-D15 | 上架运营 | 上架运营 | **提交连接器审核** |

人力：Jason 主导 + 李俊杰协作，首批总投入 ≤2 人周。

---

## 七、交付物清单（本方案配套已产出）

1. `outputs/wb-submit/skills/crm-analytics/` —— P1-A 可提审包 v1（SKILL.md 重写版+裁剪脚本+模板）
2. 本报告 + 《接口研究报告》
3. 后续：P1-B 技能包、P1-C 连接器工程（另立仓库）
