# 市场物料与提审清单（14 技能：通用层 10 + 行业层 4）

> 2026-09-05 备齐（行业层 4 技能物料同日补齐）。头像见 `outputs/avatars/` 与仓库 `assets/avatars/`
> （512×512 PNG，品牌色 #185FA5，均 <20KB，远低于 500KB 上限）；预览拼图 `_preview-grid.png`（通用 1-6）/`_preview-grid2.png`（通用 7-10）/`_preview-grid3.png`（行业层 4，左上菱形角标=行业手册系列）。
> 生成脚本 `outputs/make_avatars.py`（PIL，可复跑改色改形）。提审 zip 见 `dist/` 与 `outputs/`。
> 企业认证通过后按本清单同日提交。

## 头像对照

| 技能 | 头像文件 | 图形语言 |
|---|---|---|
| crm-analytics | crm-analytics.png | 分层漏斗（客户分层） |
| promo-review | promo-review.png | 上升折线+峰值旗（大促增长） |
| ad-compliance-check | ad-compliance-check.png | 盾牌+对勾（合规防护） |
| competitor-review | competitor-review.png | 对比柱+放大镜（竞品洞察） |
| review-insight | review-insight.png | 对话气泡+星标（评价口碑） |
| member-lifecycle-calendar | member-lifecycle-calendar.png | 日历+循环徽章（生命周期运营） |
| multi-platform-merge | multi-platform-merge.png | 三源汇聚到一张表（多平台合并） |
| inventory-alert | inventory-alert.png | 立体箱+警示徽章（库存预警） |
| ecom-daily-report | ecom-daily-report.png | 报表+迷你柱状与上升箭头（日报） |
| video-script-planner | video-script-planner.png | 场记板+播放键（短视频策划） |
| beauty-ops | beauty-ops.png | 口红+星芒+行业角标（美妆手册） |
| fashion-ops | fashion-ops.png | 衣架+裙摆+行业角标（快时尚手册） |
| luxury-ops | luxury-ops.png | 钻石切面+行业角标（轻奢手册） |
| electronics-ops | electronics-ops.png | 芯片引脚+行业角标（消费电子手册） |

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

### multi-platform-merge 多平台合并
1. 把天猫和京东导出的销售表合并成一张表，口径统一
2. 京东报表金额单位是分、编码还是 GBK，帮我处理后再合并
3. 合并后各平台 GMV 占比多少？给我一份数据质量报告

### inventory-alert 库存预警
1. 这份库存和近 30 天销量，帮我算哪些 SKU 快断货了
2. 双11 要备多少货？按 3 倍销量放大帮我测算
3. 哪些是滞销和死库存？按资金占用排个清理清单

### ecom-daily-report 日报周报
1. 用这份日数据生成昨天的电商日报，月目标 180 万
2. 昨天 GMV 环比涨了 24%，帮我归因是流量还是转化
3. 帮我出上周的销售周报，含 7 日趋势和渠道结构变化

### video-script-planner 短视频脚本
1. 给 Macallan 15 年策划一条 30 秒种草视频脚本
2. 这条带货视频前 3 秒钩子不够抓人，给我 3 个备选
3. 按分镜表输出：画面、口播、字幕、音效、转场都要

### beauty-ops 美妆运营手册
1. 我们是中端护肤品牌，会员复购提醒应该隔多久触发
2. 详情页写"修复屏障""7 天焕白"合规吗？美妆功效宣称红线有哪些
3. 给我美妆行业的转化率、复购率基准，对标一下我们的数据

### fashion-ops 快时尚运营手册
1. 新款上市两周售罄率 20%，该追单还是进折扣池
2. 女装线上退货率 45% 正常吗？尺码问题怎么治理
3. 季末库存还有 40% 没卖完，折扣阶梯怎么排不伤品牌

### luxury-ops 轻奢运营手册
1. 轻奢品牌大促能不能打折？不破价的机制怎么设计
2. VIC 客户怎么定义和运营？一对一触达 SOP 给我一份
3. 礼赠场景占我们 GMV 多少算健康？节点日历怎么排

### electronics-ops 消费电子运营手册
1. 下代产品发布前，老款库存怎么清不贬值
2. 详情页写"续航 48 小时""IPX8 防水"要怎么标才合规
3. 配件耗材复购提醒按什么周期触发？延保续费节点怎么设

## 服务类目建议（提审时后台下拉确认具体二三级）

| 技能 | 建议类目方向 | 备注 |
|---|---|---|
| crm-analytics | 数据分析/商业智能类 | 无资质要求优先 |
| promo-review | 电商/营销运营类 | |
| ad-compliance-check | 电商/营销运营类 或 法律合规类 | 若法律类需资质则选电商类 |
| competitor-review | 电商/营销运营类 | |
| review-insight | 电商/营销运营类 | |
| member-lifecycle-calendar | 电商/营销运营类 | |
| multi-platform-merge | 数据分析/商业智能类 | 与 crm-analytics 同类目 |
| inventory-alert | 数据分析/商业智能类 或 电商类 | 二选一，与整体类目数权衡 |
| ecom-daily-report | 数据分析/商业智能类 | |
| video-script-planner | 内容创作/短视频类 | 新增大类，注意是否触发资质 |
| beauty-ops | 电商/营销运营类 | 行业层，与美妆客户案例强相关 |
| fashion-ops | 电商/营销运营类 | 行业层 |
| luxury-ops | 电商/营销运营类 | 行业层；奢品珠宝是凯淳核心行业 |
| electronics-ops | 电商/营销运营类 | 行业层 |

> 规则：每账号选 1-5 个服务类目，二三级各附资质要求；6 个技能尽量收敛到 1-2 个大类，避免触发额外资质。

## 提审日 Checklist（每技能）

- [ ] zip 包（dist/ 下已备，重打包先 rm 旧文件）
- [ ] 头像上传（outputs/avatars/）
- [ ] 示例问句 3 条（上文）
- [ ] 服务类目选择（上表，后台确认）
- [ ] 展示信息：display_name 中英、简介（description_zh 直接用）
- [ ] 提交后登记 docs/review-log.md（日期/版本/审核状态）

## 组合叙事（市场页/专家介绍用）

**两层架构**：通用能力层（10 技能，跨行业方法论与工具）× 行业参数层（4 技能，注入品类基准/合规红线/专属打法）。
行业层技能的核心价值是"参数注入表"——用户先问行业手册，再用通用技能时自动带上正确参数（如美妆 T=60 天、服饰售罄率模式、奢品 VIC 分层线、电子贬值型库存）。

三条产品线（通用层）：
1. **数据主线**：multi-platform-merge（合数）→ ecom-daily-report（监控）→ crm-analytics（分层）→ member-lifecycle-calendar（运营）；
2. **复盘主线**：promo-review（复盘）→ competitor-review（竞品）→ review-insight（口碑）；
3. **护航与内容**：ad-compliance-check（合规）+ inventory-alert（供应链）+ video-script-planner（内容）。
主线闭环：**复盘（promo-review）→ 分层（crm-analytics）→ 运营（member-lifecycle-calendar）**。

行业层覆盖凯淳核心行业：美妆香氛（beauty-ops）、快时尚（fashion-ops）、奢品珠宝（luxury-ops）、消费电子（electronics-ops）；
下一波候选：运动户外（sports-ops，主打 CRM 全渠道）、酒类（liquor-ops，威士忌业务沉淀）。
免费层全部公开可装；数据库直连、定时跑批、写回业务系统等企业级能力走服务端连接器（规划中）。
