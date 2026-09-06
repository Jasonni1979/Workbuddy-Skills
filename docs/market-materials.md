# 市场物料与提审清单（23 技能 + 1 专家团：通用层 10 + 行业层 6 + 全渠道层 7 + brand-ops-team）

> 2026-09-06 备齐（全渠道层 7 技能物料同日补齐；品牌客户运营专家团同日完成）。头像见 `outputs/avatars/` 与仓库 `assets/avatars/`
> （512×512 PNG，品牌色 #185FA5，均 <20KB，远低于 500KB 上限）；预览拼图 `_preview-grid.png`（通用 1-6）/`_preview-grid2.png`（通用 7-10）/`_preview-grid3.png`（行业层 6，左上菱形角标=行业手册系列）/`_preview-grid4.png`（全渠道层 7）。
> 生成脚本 `outputs/make_avatars.py`（技能）与 `outputs/make_team_avatars.py`（专家团 5 张，PIL，可复跑改色改形）。提审 zip 见 `dist/` 与 `outputs/`。
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
| sports-ops | sports-ops.png | 山峰+峰顶旗+行业角标（运动户外手册） |
| liquor-ops | liquor-ops.png | 威士忌杯+冰块+行业角标（酒类手册） |
| content-matrix-planner | content-matrix-planner.png | 3×3 内容九宫格（种草矩阵） |
| cs-ticket-insight | cs-ticket-insight.png | 耳麦+对话气泡（客服洞察） |
| return-rate-clinic | return-rate-clinic.png | 回环箭头+诊断十字（退货治理） |
| private-domain-sop | private-domain-sop.png | 双人+对话气泡（私域触达） |
| member-oneid-merge | member-oneid-merge.png | 三源汇聚到 ID 徽章（One-ID） |
| price-governance | price-governance.png | 价签+盾牌对勾（价格治理） |
| channel-health-score | channel-health-score.png | 六维雷达图（渠道体检） |
| brand-ops-team（主理人头像） | brand-ops-team.png | 人物+指挥光环+四枢纽节点+金色领结（凯队长） |
| brand-ops-data-analyst | brand-ops-data-analyst.png | 人物+折线面板（数析） |
| brand-ops-member-expert | brand-ops-member-expert.png | 人物+双心纽带（会运营） |
| brand-ops-content-expert | brand-ops-content-expert.png | 人物+嫩芽波纹（种草） |
| brand-ops-channel-expert | brand-ops-channel-expert.png | 人物+网络盾（渠道官） |

> 专家团 5 张头像由 `make_team_avatars.py` 生成（人物角色隐喻，与技能图标系列区分）；提审时主头像用 `brand-ops-team.png`，成员头像暂存备用（后台如支持成员展示再用）。

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

### sports-ops 运动户外运营手册
1. 跑鞋卖了 8 个月，复购提醒按什么里程周期触发
2. 门店、电商、社群、赛事四拨会员怎么合成一个体系
3. 高活跃低消费的运动社群用户怎么运营成 KOC

### liquor-ops 酒类运营手册
1. 威士忌短视频能拍倒酒和举杯吗？平台审核边界在哪
2. 中秋礼赠档期什么时候启动？节点日历给我一份
3. 稀缺配额款怎么管理？二级市场价格要不要盯

### content-matrix-planner 种草内容矩阵
1. 小红书月度预算 8 万，帮我排一份种草内容矩阵和达人组合
2. 新品上市前两周，测评/教程/场景内容怎么配比
3. 腰部达人怎么筛选？爆文率和 CPE 基准给我一份

### cs-ticket-insight 客服工单洞察
1. 这是近 30 天工单导出，帮我做归因和 SLA 达标率分析
2. 哪些工单是升级风险？给我红橙黄分级清单
3. 客服话术哪里要改？按高频场景给改进对照表

### return-rate-clinic 退货率诊断
1. 女装退货率 48%，帮我归因并定位高退货 SKU
2. 大促退货比日常高 2 倍，是凑单问题还是尺码问题
3. 退货率降 1pp 能省多少钱？治理动作按 ROI 排个序

### private-domain-sop 私域触达话术
1. 企微 1v1 沉睡 90 天客户怎么唤醒？给我三波话术
2. 复购提醒话术怎么写不招人烦？频控规则给我一份
3. 大促前 7 天的社群预告节奏和话术帮我排一下

### member-oneid-merge 会员 One-ID 合并
1. 天猫和门店的会员名单帮我合并成一张表，手机号为主键
2. 没有手机号的门店会员怎么和线上对上？模糊匹配规则给我
3. 合并质量怎么样？跨渠道重合率和冲突清单给我一份

### price-governance 跨渠道价格治理
1. 帮我核对各渠道到手价，有没有低于授权底价的破价
2. 拼多多这家店低价出货，是窜货还是平台补贴？怎么定性
3. 渠道间价差超过 5% 的 SKU 有哪些？价盘健康度打个分

### channel-health-score 渠道健康度评分
1. 六个渠道帮我做健康度评分，哪个该加码哪个该收缩
2. 抖音增长快但毛利低，算什么角色？资源怎么配
3. GMV 集中度风险大吗？第二渠道培育给个方案

### brand-ops-team 品牌客户运营专家团（quickPrompts，与 plugin.json 一致）
1. 我是品牌电商运营负责人，帮我梳理经营数据并给出行动建议。（= defaultInitPrompt）
2. 帮我做一次大促复盘：GMV、渠道贡献、退货情况与下一轮行动。
3. 给我一份会员分群、生命周期营销与私域触达的季度运营计划。

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
| sports-ops | 电商/营销运营类 | 行业层；运动是凯淳×阿里共创重点行业，主打 CRM 全渠道 |
| liquor-ops | 电商/营销运营类 | 行业层；注意酒类广告合规表述不写入类目资质触发项 |
| content-matrix-planner | 内容创作/短视频类 | 与 video-script-planner 同类目 |
| cs-ticket-insight | 数据分析/商业智能类 | 客服质检场景，避免法律类资质 |
| return-rate-clinic | 数据分析/商业智能类 | 与 inventory-alert 同类目 |
| private-domain-sop | 电商/营销运营类 | 与 member-lifecycle-calendar 同类目 |
| member-oneid-merge | 数据分析/商业智能类 | 数据清洗类，与 crm-analytics 同类目 |
| price-governance | 电商/营销运营类 | 渠道管理类 |
| channel-health-score | 数据分析/商业智能类 | 经营诊断类 |
| brand-ops-team | 电商/营销运营类 | Expert Team；categoryId=07-SalesCommerce，市场页走专家团 Tab |

> 规则：每账号选 1-5 个服务类目，二三级各附资质要求；23 个技能收敛到 3 个大类（电商运营/数据智能/内容创作），避免触发额外资质。

## 提审日 Checklist（每技能）

- [ ] zip 包（dist/ 下已备，重打包先 rm 旧文件）
- [ ] 头像上传（outputs/avatars/）
- [ ] 示例问句 3 条（上文）
- [ ] 服务类目选择（上表，后台确认）
- [ ] 展示信息：display_name 中英、简介（description_zh 直接用）
- [ ] 提交后登记 docs/review-log.md（日期/版本/审核状态）

## 组合叙事（市场页/专家介绍用）

**三层架构**：通用能力层（10 技能，跨行业方法论与工具）× 行业参数层（6 技能，注入品类基准/合规红线/专属打法）× 全渠道运营层（7 技能，覆盖种草→转化→售后→私域→底座的全链路）。
行业层技能的核心价值是"参数注入表"——用户先问行业手册，再用通用技能时自动带上正确参数（如美妆 T=60 天、服饰售罄率模式、奢品 VIC 分层线、电子贬值型库存）。
全渠道层的核心价值是"链路补全"——通用层管"数据与复盘"，全渠道层管"触点与治理"（内容种草、客服、退货、私域话术、One-ID、价盘、渠道体检）。

三条产品线（通用层）：
1. **数据主线**：multi-platform-merge（合数）→ ecom-daily-report（监控）→ crm-analytics（分层）→ member-lifecycle-calendar（运营）；
2. **复盘主线**：promo-review（复盘）→ competitor-review（竞品）→ review-insight（口碑）；
3. **护航与内容**：ad-compliance-check（合规）+ inventory-alert（供应链）+ video-script-planner（内容）。
主线闭环：**复盘（promo-review）→ 分层（crm-analytics）→ 运营（member-lifecycle-calendar）**。

全渠道层闭环：**种草（content-matrix-planner）→ 承接（private-domain-sop）→ 转化诊断（return-rate-clinic / cs-ticket-insight）→ 底座（member-oneid-merge / price-governance / channel-health-score）**。
底座三件套是全渠道 CRM 的地基：One-ID 打通人、价盘治理管秩序、渠道评分定资源。

行业层覆盖凯淳全部六大擅长行业：美妆香氛（beauty-ops）、快时尚（fashion-ops）、奢品珠宝（luxury-ops）、消费电子（electronics-ops）、运动户外（sports-ops，主打 CRM 全渠道）、酒类（liquor-ops，威士忌业务沉淀）。
免费层全部公开可装；数据库直连、定时跑批、写回业务系统等企业级能力走服务端连接器（规划中）。

**专家团封装（brand-ops-team）**：23 技能不是散装给用户，而是被一支五人专家团"包起来"。主理人凯队长负责分诊派单与口径把关，四位成员各管一域——数析（数据洞察 6 技能）、会运营（会员 CRM 4 技能）、种草（内容合规 3 技能）、渠道官（渠道治理 4 技能 + 六大行业手册）。plugin.json 的 `skills` 字段内嵌全部 23 技能，agent frontmatter 的 `skills` 字段按角色预加载子集，用户召唤一个专家团即得完整运营工具箱。这是"技能矩阵"到"组织能力"的封装：技能解决单点，专家团解决"该找谁、按什么顺序、口径怎么统一"。行业差异由渠道官在派单前先锁行业、注入参数，确保美妆不用酒类的基准。
