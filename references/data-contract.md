# 数据契约

推荐项目结构：PROJECT.md、config、work/<platform>/<run>、data/raw、data/clean、data/coded、output/report。原始证据、清洗、初标、校准和报告不能互相覆盖。项目目录名和参数来自当前产品，不复制案例数据。

## 原始记录

| 字段 | 规则 |
|---|---|
| source_id | 稳定唯一本地ID，优先平台ID结合内容哈希；无平台ID用内容哈希并声明，不冒充平台ID |
| native_id | 可见平台原生ID，不可见为null |
| date / date_raw | 标准日期与页面原始显示；相对时间不假造精确日期 |
| text_raw | 原文，不混机翻、UI、Vine徽章或广告；分段连接方式固定 |
| source_url | 优先评论级，只能母帖级时写url_granularity |
| rating / engagement | 原星级与原互动分开；Reddit/X无星级则null |
| context | 产品ID/ASIN、品牌证据、对象、作者角色、Vine、购买验证、母帖、国家及source_files |
| completeness | 完整/可见文本/疑似截断/不可确认；不能靠末尾句号判断全文完整 |

证据清单每行含来源、目标/查询、保存时间、文件、sha256、采集方法、attempt、可确认状态、stop_reason；未观察HTTP状态则null。失败和临时加载页面单独保存，不把旧页当新查询成功。公开交付去除账号、购物车和私人侧栏，受限原件和脱敏副本留映射。

## 打标记录

每行一条评论：source_id、text_raw、source_url、platform、rating、content_type、author_role、in_scope、coding_status、brand、brand_object、brand_evidence、brand_source_url、labels。

labels每次赋值包含level1、level2、level3、sentiment、evidence_quote、evidence_object、assertion_type、is_defect。

- sentiment：正向/负向/中性/混合，不从星级直接生成。
- assertion_type：实际经历/购买诉求/推测/建议/一般陈述。
- evidence_quote：非空、逐字来自本条text_raw，不能以译文代替。
- is_defect：人工判定的具体缺陷，不因负向情绪自动为true。
- 已读且确认无标签可labels=[]；未读/待判不能冒充无标签。
- coding_status只在真实校准后设“已校准”；另存taxonomy_version和校准记录。
- brand未知为null。品牌证据不在评论时提供外部证据和brand_source_url。
- 附带统计脚本每条评论只接受一个品牌对象。多品牌对比需扩展标签级品牌证据再统计，或排除品牌比较，不把整条所有标签归同品牌。

## 结论记录

claim_id、title、statement、claim_type、n、source_ids、evidence_object、limits。性质分样本观察/关联线索/待验证解释/建议。统计结论须全量成员集合；代表性引文只作展示。source_id或正文修订时版本化并保存old→new映射，旧报告不失联。
