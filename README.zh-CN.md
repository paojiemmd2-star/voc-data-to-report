# 从收集数据到生成可视化报告

[English](README.md) · [技能入口](SKILL.md) · [数据契约](references/data-contract.md) · [MIT许可证](LICENSE)

一套可跨产品复用的电商VOC研究工作流：研究简报 → 数据采集 → 原文审计 → 标签JSON → 人工校准 → 证据打标 → Python统计 → 可视化报告 → 可选Listing策略。

每个标签绑定原文摘录和 `source_id`，每条报告结论绑定全量证据集合；统计表有明确口径、样本分母 `n` 和源记录映射。

## 能力与边界

- 组织Amazon、Reddit、X采集，但不内置抓取器。采集需要宿主工具或另行安装的bggg平台skill，本仓库不打包这些外部工具。
- 先构建四个一级下的三级标签：人群场景、功能价值、保障价值、体验价值；二三级中文标签均不超过5字，主题名不含情感。
- 用户要求人工校准时必须等待，不能将“请写统计脚本”误当成同意打标。
- 区分品牌对象、主体与配件、商家与消费者、Vine与非Vine、实际经历与推测。
- 提供标准库Python脚本统计TOP20、品牌交叉、低星缺陷和完整证据映射。
- 指导生成七部分可视化报告；本仓库不内置自动PDF/HTML生成器，报告需宿主相应创作与渲染能力。
- Listing主张同时需要用户需求证据和我方具体SKU事实，不把竞品评论改写为本品承诺。

## 安装与调用

让兼容的技能安装器安装本仓库，技能就在仓库根目录：

> 从 https://github.com/paojiemmd2-star/voc-data-to-report 安装 voc-data-to-report 技能。

或克隆仓库，将文件放入宿主支持的个人技能目录下的 `voc-data-to-report` 文件夹，确保 `SKILL.md` 在该文件夹第一层。同一技能不要在多个活跃发现路径重复安装；已有安装先检查备份再更新。

下一轮通过宿主技能选择器或 `$voc-data-to-report` 调用：

> 为【产品】研究【市场】，竞品【ASIN/URL】，关键词【词】，采集方式【只读渲染/已授权的平台方法】，样本和时间上限【范围】。先给标签JSON等校准，再做逐条证据打标、统计和完整报告。

## 初始化研究目录

Python 3.9及以上，脚本只用标准库，不联网、不生成假评论：

```bash
python3 scripts/init_voc_project.py \
  --root ../research-example \
  --product "示例产品" \
  --market "US" \
  --method rendered_only \
  --keywords "示例产品" "示例配件" \
  --parent-cap 30 \
  --sample-cap 200
```

示例数量是参数演示，不是适合所有研究的固定样本量。已有目录会拒绝覆盖；配置文件生成不等于已经采集。

## 对已校准数据统计

```bash
python3 scripts/voc_statistics.py \
  --input ../research-example/data/coded/coded_reviews.jsonl \
  --out ../research-example/output/statistics \
  --low-star-max 3
```

输入字段、枚举与校准状态见[数据契约](references/data-contract.md)。脚本默认拒绝待校准输入，不自动判断情感、品牌或缺陷。仅修改状态文字不代表完成人工校准。

输出七个文件：

| 文件 | 用途 |
|---|---|
| top20_level3_sentiment.csv | 三级完整路径频次×情感TOP20及n |
| brand_level2_sentiment.csv | 品牌对象×二级路径×情感交叉表及分组/总体n |
| low_star_defects.csv | 默认Amazon1–3星实际缺陷及source_ids |
| label_evidence.csv | 每次赋值的原文、摘录、来源及标签 |
| cell_source_map.json | 每个统计单元的全部source_id |
| statistics_metadata.json | 输入哈希、排除量、分母和规则 |
| statistics.json | 表格和元数据的统一JSON |

详见[分析与报告口径](references/analysis-and-report.md)。脚本每条评论仅支持一个品牌对象，多品牌对比需扩展标签级品牌绑定或不进入品牌比较；不能把设备品牌当配件品牌。

## 报告七部分

一页纸总览、数据说明、正面热点与痛点排序、异常信号卡、用户画像、证据链、可视化图表。评论频次不是市场普及率，低星不是所有负向情感，报告完整不代表采集全量。初标报告必须标为待复核，不冒充已校准。

## 测试与隐私

```bash
python3 -m unittest discover -s scripts -p 'test_*.py' -v
```

测试只用合成数据，不是真实研究结果。格式校验不替代语义校准。公开仓库不附私人对话、记忆记录、原始研究评论、账号、Cookie或本机绝对路径。工作区和导出目录默认忽略，但发布前仍需检查文件。

MIT许可证见[LICENSE](LICENSE)；外部采集工具保留各自许可与使用条款，未在本仓库重新分发。
