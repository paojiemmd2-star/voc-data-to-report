#!/usr/bin/env python3
"""Create a product-specific VOC workspace without network access or fake data."""
import argparse,json,csv
from datetime import datetime,timezone
from pathlib import Path

def create(root,product,market,method='rendered_only',asins=(),keywords=(),parent_cap=None,sample_cap=None):
    if root.exists():raise ValueError('目录已存在；请检查并复用，或选择新目录，不能覆盖原证据')
    if parent_cap is not None and parent_cap<1:raise ValueError('每母帖上限必须为正整数')
    if sample_cap is not None and sample_cap<1:raise ValueError('总样本上限必须为正整数')
    for asin in asins:
        if len(asin)!=10 or not asin.isalnum():raise ValueError('ASIN格式应为10位字母数字')
    for folder in ['config','work/amazon','work/reddit','work/x','data/raw','data/clean','data/coded','output/report']:
        (root/folder).mkdir(parents=True,exist_ok=False)
    brief=dict(product=product,market=market,collection_method=method,method_default_disclosed=method=='rendered_only',asins=list(asins),keywords=list(keywords),parent_comment_cap=parent_cap,sample_cap=sample_cap,created_at_utc=datetime.now(timezone.utc).isoformat(),stage='研究简报待完善',taxonomy_status='未构建',coding_status='未打标',collection_status='未开始')
    (root/'config/brief.json').write_text(json.dumps(brief,ensure_ascii=False,indent=2),encoding='utf-8')
    for filename,fields,rows in [
        ('amazon_targets.tsv',['asin','mode','lang','title'],[dict(asin=a,mode='',lang='',title='') for a in asins]),
        ('reddit_queries.tsv',['query','lang','round'],[dict(query=k,lang='',round=1) for k in keywords]),
        ('x_queries.tsv',['query','lang','round'],[])]:
        with (root/'config'/filename).open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader();w.writerows(rows)
    (root/'PROJECT.md').write_text(f'''# {product} VOC研究

市场：{market}
方法：{method}。rendered_only为只读渲染；若使用默认值，执行前向用户说明并尊重其最新明确方式。
每母帖上限：{parent_cap if parent_cap else '待定，不能无界滚动'}
总样本上限：{sample_cap if sample_cap else '待定，执行前按研究范围设置停止条件'}

## 本轮需完善

研究问题、用户任务、竞品重点款及basic/full/max、时间窗、平台范围、采集停止条件、报告形式与Listing是否需要。配置为空不代表采集失败，已填写也不代表执行成功。

## 阶段状态

采集未开始；标签未构建；未打标。默认先给标签JSON等校准；如用户明确要求探索性报告，标记分析师初标待复核，不假称校准完成。

## 决策与版本记录

记录后续确认、样本冻结哈希、标签版本、校准证据和方法变化。原始证据不得覆盖。
''',encoding='utf-8')
    return brief

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--product',required=True)
    p.add_argument('--market',required=True)
    p.add_argument('--method',choices=['rendered_only','platform_skill_default'],default='rendered_only')
    p.add_argument('--asins',nargs='*',default=[])
    p.add_argument('--keywords',nargs='*',default=[])
    p.add_argument('--parent-cap',type=int)
    p.add_argument('--sample-cap',type=int)
    a=p.parse_args()
    try:r=create(a.root,a.product,a.market,a.method,a.asins,a.keywords,a.parent_cap,a.sample_cap)
    except (ValueError,OSError) as e:p.exit(2,f'错误：{e}\n')
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
