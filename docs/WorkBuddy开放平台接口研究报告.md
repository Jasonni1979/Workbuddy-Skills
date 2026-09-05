# WorkBuddy 开放平台接口研究报告（接口级深研）

> 版本 v1.0 ｜ 2026-09-05 ｜ 研究范围：open.workbuddy.cn 全部开放文档（概述/入驻/技能/专家/专家团/连接器/Buddy应用/第三方应用/Open API）
> 目的：为"CRM 能力第一批上架"提供接口级依据。假设开放平台申请（企业认证）已完成。

---

## 一、平台技术架构总览

```
┌──────────────────────── WorkBuddy Agent OS 底座 ────────────────────────┐
│  理解 · 规划 · 执行 · 记忆 · 多Agent协作 · 权限治理（腾讯封装为可调用接口）   │
└───────────────────────────────────────────────────────────────────────┘
        ▲                ▲                ▲                ▲
   技能 Skill       专家/专家团        连接器 Connector    Buddy 应用 / 第三方应用(Open API)
  （能力包,最轻）   （人设+知识+技能）  （MCP/CLI 接外部系统） （行业工作台 / OAuth 2.1 调用户数据）
```

三类开发者资产的工程本质：
- **Skill** = 1 个 SKILL.md（YAML+Markdown）+ 可选 references/scripts/templates，**零服务依赖**，AI 用内置工具（Read/Write/Bash/WebSearch 等）执行。
- **专家/专家团** = plugin.json + agents/*.md（人设）+ avatars，可声明依赖（自带 MCP 或已上架连接器），召唤前引导用户连接。
- **连接器** = 一个 MCP Server（远程 HTTPS 或 stdio）或一个 CLI，把外部系统变成 Agent 可调用的工具。
- **Open API** = 第三方应用经 OAuth 2.1 调用用户侧能力（本地助理、云端任务、会话产物、兑换码）。

---

## 二、技能（Skill）接口规格

### 2.1 目录与打包
```
skills/{skill-name}/
├── SKILL.md            # 必须
├── references/         # 可选：AI 执行时读入作上下文（@references/xxx.md 引用）
├── scripts/            # 可选：AI 通过 Bash 执行
└── templates/          # 可选：模板文件
```
zip 上传 ≤20MB；平台自动解析 frontmatter，失败会逐条报错（缺字段/YAML 语法）。

### 2.2 Frontmatter 字段（实测文档）
| 字段 | 必填 | 说明 |
|---|---|---|
| name | 否 | 技能标识 |
| description | **是** | 写清用途和**触发词**——决定 AI 何时自动调起 |
| description_zh / description_en | **是** | 中英简介 |
| version | **是** | 语义化版本 |
| author | **是** | 合作方名称 |
| display_name / display_name_en | 建议 | 市场展示名（解析报错清单含这两项，视为事实必填） |
| category | 建议 | 分类之一（示例值：writing / 办公协同；枚举未公开，解析/审核反馈可校正） |
| allowed-tools | 否 | 工具白名单（逗号分隔） |
| disable-model-invocation | 否 | true = 仅手动调用 |
| user-invocable | 否 | false = 隐藏菜单，仅供 AI 内部使用 |

**YAML 红线**：冒号后必须空格；避免引号（尤其中文引号）；必填字段一个不能少。

### 2.3 执行模型
- AI 触发依据 description 的触发词；scripts 由 AI 用 Bash 调起，**运行环境是用户本机**——脚本必须跨平台、无硬编码绝对路径、无交互式 input()（Agent 环境无 TTY）。
- 审核三道：安全扫描 + AI 审核 + 人工抽检，约 7 个工作日；问题反馈邮箱 openworkbuddy@tencent.com。

---

## 三、专家 / 专家团接口规格

### 3.1 结构
```
my-expert/
├── .codebuddy-plugin/plugin.json
├── agents/{agent-name}.md      # YAML frontmatter + 系统提示词正文
├── avatars/expert.png          # 512×512 PNG ≤500KB
└── README.md
```

### 3.2 plugin.json 必填字段
name（kebab-case）、expertType（agent/team）、version、description（英文）、author{name,email}、agents[]、agentName、displayName{en,zh}、profession{en,zh}、displayDescription{en,zh}（**中文 40-50 字**）、avatar、categoryId、defaultInitPrompt{en,zh}（**必须与 quickPrompts 第一条一致**）、plugin（=name）、tags（**固定 3 个**）、quickPrompts（**固定 3 个**）。
team 时增加 `teamInfo: {leadAgent, memberAgents[]}`；主理人文件名须带专家团前缀。

### 3.3 行业分类（15 个 categoryId，CRM 对口）
- **07-SalesCommerce 销售商务**：客户开发、销售策略、**电商运营**、BD ← 首选
- 04-DataAI 数据智能：数据分析、AI 应用 ← 备选
- 05-MarketingGrowth 营销增长 ← 会员运营类备选

### 3.4 依赖声明（关键能力）
plugin.json `dependencies: {mcpServers: "./.mcp.json", connectors: ["tencent-docs"]}`。自带 MCP 可在 `.mcp.json` 中附 `x-workbuddy`（展示名/描述/图标/auth: oauth|token|none + tokenSchema）。**这意味着专家可以"自带"我们的 CRM MCP 连接器，召唤前引导用户授权连接**——是"专家+连接器"组合上架的官方机制。

### 3.5 工具权限
开发者**不可自定义 tools**，系统统一分配（Read/Write/Grep/Glob/Bash/WebSearch/WebFetch，主理人另有 AgentTool/SendMessage）。→ 人设文件只能约束"怎么想、怎么干"，能力扩展必须走 scripts/依赖 MCP。

---

## 四、连接器（Connector）接口规格

### 4.1 方案选择
| 方案 | 适用 | 我们的场景 |
|---|---|---|
| MCP+Skill（推荐） | 有/可开发 API 服务 | **Weaver OA / CRM 数据连接器** |
| CLI+Skill | 已有稳定跨平台 CLI | 暂不需要 |

### 4.2 mcp.json 关键字段
type（sse/streamableHttp/stdio）、url（**生产必须 HTTPS**）、headers（`${VAR}` 占位，禁写真凭证）、timeout（默认 30000，**单请求建议 ≤30s**）、runtime{type:node}、npmRegistry、staticEnv/staticHeaders、preAuth、disabledTools。**一个连接器只配一个 Server**。

### 4.3 connector-meta.json 关键字段
name/name_en/name_zh、description 三语（20-100 字）、source（**全局唯一 kebab-case**）、type（mcp/cli）、version、examples_zh/examples_en（各 2-5 条自然语言）、auth_mode（省略/server-side/gateway/token）、minWorkbuddyVersion。

### 4.4 认证四模式
| auth_mode | 场景 | 说明 |
|---|---|---|
| 省略 | MCP 自带 OAuth 或无需认证 | OAuth 2.1+PKCE，公共客户端；服务端需实现 5 个端点（well-known×2、register、authorize(S256)、token），redirect_uri 支持 `workbuddy://...` 或 127.0.0.1 回环；access_token 1h / refresh ≥30d |
| server-side / gateway | 腾讯云端托管 OAuth | 需与 WorkBuddy 团队确认 |
| token | 用户自填 Token/API Key | 附 token-schema.json 表单（password 类型），凭证仅存用户本机，`${VAR}` 注入 headers/url；minWorkbuddyVersion ≥4.23.0 |

### 4.5 CLI 方案硬约束（备查）
auth 命令 10 秒内 stdout 输出 https URL（空白分隔）；status 幂等 10s；登录态须跨重启有效；轮询 3s/最长 5min；init 5min；推荐 Device Code Flow。

### 4.6 版本兼容表（关键）
使用新字段必须声明 minWorkbuddyVersion：token 模式≥4.23.0；name_zh/examples≥4.24.0；preAuth/runtime/python≥5.0.0；name_map≥5.2.0。**保守策略：首批只用"基础"字段，minWorkbuddyVersion 不声明或声明 4.24.0。**

### 4.7 审核
连接器提交 WorkBuddy 团队审核，**通过后更新重提 10-15 分钟同步生效**（比 Skill 的 7 天快得多）。

---

## 五、Open API（第三方应用）端点清单

OAuth 2.1 授权码流程；`GET /openapi/v2/authorize` → `POST /openapi/v2/token`；Bearer 鉴权；client_secret 严禁前端暴露。

| 分类 | 方法 | 端点 | 用途 |
|---|---|---|---|
| 认证 | GET/POST | /openapi/v2/authorize、/openapi/v2/token | 授权与换票 |
| 个人资料 | GET | /openapi/v2/user/profile、/user/phoneverification | 昵称头像、手机号校验 |
| 本地助理 | GET/POST | /openapi/v2/localassistant(、/message) | 查询在线、向用户 PC 端助理发消息、读历史 |
| 云端任务 | POST/GET | /openapi/v2/tasks(、/{task_id}) | 创建/查询云端任务，返回 ACP link+token |
| ACP 通道 | GET/POST | {link} | SSE 接收 + JSON-RPC 发送，实时双向 |
| 会话产物 | GET | {sandbox_url}/api/session/artifacts | 拉取 plan/tasks/media/overview |
| 兑换码 | POST | /openapi/v2/redemptions | 发积分 |

Scope：user.task.readable/invokable、user.localassistant.readable/invokable、user.profile.readable、user.contact.readable、user.credit.exchange。
限制：code 10 分钟一次性；access_token 1h；429 指数退避；任务列表 size≤100；产物 limit≤500。

**对 K-AIDE 的意义**：`localassistant/message` + `tasks` + ACP 通道 = 可以让 K-AIDE/企微 bot 把任务派发到用户电脑的 WorkBuddy 执行并回收产物——这是阶段三"K-AIDE × WorkBuddy 互通"的官方接口依据。

---

## 六、Buddy 应用（备查）
垂直行业 AI Harness：自定义 System Prompt、场景胶囊、模型配置、应用内市场、工作模式；**授权列表首次创建后不可改**；仅企业主体。→ 阶段三再启动，本阶段不投入。

---

## 七、我们现有 crm-analytics 与平台规格的差距分析（Gap）

| 检查项 | 现状 | 平台要求 | 差距/动作 |
|---|---|---|---|
| frontmatter 必填字段 | 仅有 name/description/version(在metadata内)/author 缺失 | description(_zh/_en)、version、author、display_name(_en) 必填 | **重写 frontmatter** |
| description | 单条长中文 | 需触发词+中英三语 | 重写 |
| category | 无 | 需要 | 补（数据类，审核反馈校正） |
| 硬编码路径 | SKILL.md 4 处 /Users/wise01/... | 用户本机运行，禁绝对路径 | **改为相对路径/自动探测** |
| 交互式 input() | 仅 --interactive 分支 | Agent 无 TTY | 上架版指令只走非交互 CLI（--model/--data/--config/--dry-run 已具备） |
| 凭据交互 | crm_connect.py getpass 收 DB 口令 | 公开市场禁凭据交互 | **公开版不含 crm_connect/crm_receipt**，DB 场景留给企业版连接器 |
| 依赖安装 | 指定受管 python venv 绝对路径 | 用户环境各异 | 改为"探测 python3 → 当前工作区建隔离 venv"指引 |
| 交付物 | 报告 md + segments.csv + 图表 png | 契合 | 保留，作为市场卖点 |
| 脚本规模 | 1551 行，非交互模式完整 | — | 无需重写脚本，只改 SKILL.md 与裁剪文件 |

**结论：改造集中在 SKILL.md 重写 + 文件裁剪，脚本零改动即可上架。** 预估 2 人日。

---

## 八、研究结论

1. **Skill 是最轻、最快、零服务依赖的上架形态**，且我们脚本已具备非交互 CLI——第一批以 Skill 切入完全正确。
2. **连接器审核 10-15 分钟生效、Skill 7 个工作日**——连接器迭代快但需要 HTTPS 服务托管；首批 Skill 先行，连接器 PoC 并行。
3. **专家可自带 MCP 依赖（x-workbuddy + tokenSchema）**——"CRM 专家 + CRM 数据连接器"组合是第二阶段的最佳形态，用户自填 Token 模式可绕开 OAuth 服务端建设。
4. **Open API 的 localassistant/tasks/ACP 是 K-AIDE 互通的官方通道**，列入阶段三技术预研。
5. 版本字段保守化（只用基础字段）可最大化低版本客户端覆盖。
