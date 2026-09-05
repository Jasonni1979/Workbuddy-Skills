# 市场物料与提审清单（6 技能）

> 2026-09-05 备齐。头像见 `outputs/avatars/`（512×512 PNG，品牌色 #185FA5，均 <20KB，远低于 500KB 上限）；
> 预览拼图 `_preview-grid.png`。生成脚本 `outputs/make_avatars.py`（PIL，可复跑改色改形）。
> 提审 zip 见 `dist/` 与 `outputs/`。企业认证通过后按本清单同日提交。

## 头像对照

| 技能 | 头像文件 | 图形语言 |
|---|---|---|
| crm-analytics | crm-analytics.png | 分层漏斗（客户分层） |
| promo-review | promo-review.png | 上升折线+峰值旗（大促增长） |
| ad-compliance-check | ad-compliance-check.png | 盾牌+对勾（合规防护） |
| competitor-review | competitor-review.png | 对比柱+放大镜（竞品洞察） |
| review-insight | review-insight.png | 对话气泡+星标（评价口碑） |
| member-lifecycle-calendar | member-lifecycle-calendar.png | 日历+循环徽章（生命周期运营） |

## 示例问句（每技能 3 条，用于市场页与 quickPrompts 参考）

### crm-analytics 数据分析
1. 帮我分析这份客户订单数据，做 RFM 分层并找出高价值客户
2. 这批会员的复购率和留存怎么样？给我一份分析报告
3. 用这份销售数据跑一下流失预警，哪些客户快流失了

### promo-review 大促复盘
1. 帮我复盘今年 618，目标 GMV 800 万实际 640 万，问题出在哪
2. 双11 流量涨了但转化跌了，按五段式框架帮我找原因
3. 这份大促数据帮我做复盘报告，并给双12 的行动建议

### ad-compliance-check 合规检查
1. 帮我检查这段详情页文案有没有广告法违禁词
2. 这条直播话术说"全网销量第一、7 天必白"，合规吗？怎么改
3. 我们是美妆品牌，这段种草笔记帮我做合规扫描并给改写建议

### competitor-review 竞品分析
1. 帮我对比我们和竞品 A、B 的价格带与核心卖点
2. 竞品大促满减力度很大，帮我拆解它的活动机制和等效折扣
3. 给我一份竞品矩阵报告，判断哪个竞品威胁最大、怎么应对

### review-insight 评价洞察
1. 这是近 90 天的差评数据，帮我归因并排改进优先级
2. 评论里说"和描述不符"的很多，是产品问题还是详情页问题
3. 帮我从好评里找出用户真正买账的卖点，用于详情页优化

### member-lifecycle-calendar 营销日历
1. 基于这份 RFM 分群结果，帮我排一份全年会员触达日历
2. 美妆品类，沉睡和流失会员的唤醒与挽回计划怎么做
3. 帮我设计生日月和等级保级的触达 SOP，含权益和频控

## 服务类目建议（提审时后台下拉确认具体二三级）

| 技能 | 建议类目方向 | 备注 |
|---|---|---|
| crm-analytics | 数据分析/商业智能类 | 无资质要求优先 |
| promo-review | 电商/营销运营类 | |
| ad-compliance-check | 电商/营销运营类 或 法律合规类 | 若法律类需资质则选电商类 |
| competitor-review | 电商/营销运营类 | |
| review-insight | 电商/营销运营类 | |
| member-lifecycle-calendar | 电商/营销运营类 | |

> 规则：每账号选 1-5 个服务类目，二三级各附资质要求；6 个技能尽量收敛到 1-2 个大类，避免触发额外资质。

## 提审日 Checklist（每技能）

- [ ] zip 包（dist/ 下已备，重打包先 rm 旧文件）
- [ ] 头像上传（outputs/avatars/）
- [ ] 示例问句 3 条（上文）
- [ ] 服务类目选择（上表，后台确认）
- [ ] 展示信息：display_name 中英、简介（description_zh 直接用）
- [ ] 提交后登记 docs/review-log.md（日期/版本/审核状态）

## 组合叙事（市场页/专家介绍用）

六技能覆盖品牌电商运营全链路：**复盘（promo-review）→ 分层（crm-analytics）→ 运营（member-lifecycle-calendar）**
为主线闭环，**合规（ad-compliance-check）、竞品（competitor-review）、口碑（review-insight）**为三大护航能力。
免费层全部公开可装；数据库直连、定时跑批、写回业务系统等企业级能力走服务端连接器（规划中）。
