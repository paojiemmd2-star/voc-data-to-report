#!/usr/bin/env python3
"""Validate human-calibrated VOC coding and export auditable statistics (stdlib only)."""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

SENTIMENTS = ('正向', '负向', '中性', '混合')
L1 = {'人群场景', '功能价值', '保障价值', '体验价值'}
EXCLUDED_ROLES = {'seller_founder', 'seller', 'brand', 'bot'}

def fail(message):
    raise ValueError(message)

def load(path):
    records = []
    seen = set()
    with path.open(encoding='utf-8-sig') as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            r = json.loads(line)
            prefix = f'{path.name}:{line_no}'
            if r.get('coding_status') != '已校准':
                fail(f'{prefix}: coding_status 必须为已校准，未打标模板不可用于正式统计')
            for name in ('source_id', 'text_raw', 'platform', 'source_url', 'content_type', 'author_role'):
                if not isinstance(r.get(name), str) or not r[name].strip():
                    fail(f'{prefix}: {name} 必须是非空字符串')
            if r['source_id'] in seen:
                fail(f'{prefix}: source_id 重复，请先合并同一评论的 labels')
            seen.add(r['source_id'])
            rating = r.get('rating')
            if rating is not None and (isinstance(rating, bool) or not isinstance(rating, (int, float)) or not 1 <= rating <= 5):
                fail(f'{prefix}: rating 必须为空或1–5的数字')
            if r['platform'] == 'Reddit' and rating is not None:
                fail(f'{prefix}: Reddit 互动不可转换为星级')
            if not isinstance(r.get('in_scope'), bool):
                fail(f'{prefix}: in_scope 必须为布尔值')
            if not isinstance(r.get('labels'), list):
                fail(f'{prefix}: labels 必须为数组，未命中可以为空数组')
            brand = r.get('brand')
            if brand is not None:
                evidence = r.get('brand_evidence')
                if not isinstance(brand, str) or not brand.strip() or not isinstance(evidence, str) or not evidence:
                    fail(f'{prefix}: 品牌非空时须提供 brand_evidence')
                if evidence not in r['text_raw'] and not r.get('brand_source_url'):
                    fail(f'{prefix}: 品牌证据不在原文时须提供品牌来源URL')
                if not r.get('brand_object'):
                    fail(f'{prefix}: 品牌须说明 brand_object，避免混淆主体产品和配件品牌')
            for j, label in enumerate(r['labels'], 1):
                lp = f'{prefix} label{j}'
                if label.get('level1') not in L1:
                    fail(f'{lp}: 一级标签不在固定四类中')
                for field in ('level2', 'level3'):
                    if not isinstance(label.get(field), str) or not 1 <= len(label[field]) <= 5:
                        fail(f'{lp}: {field} 长度必须为1–5字')
                if label.get('sentiment') not in SENTIMENTS:
                    fail(f'{lp}: sentiment 必须是 {SENTIMENTS}')
                if not isinstance(label.get('evidence_quote'), str) or not label['evidence_quote'] or label['evidence_quote'] not in r['text_raw']:
                    fail(f'{lp}: evidence_quote 必须逐字来自本条 text_raw')
                if not isinstance(label.get('is_defect'), bool):
                    fail(f'{lp}: is_defect 必须为布尔值')
                if label.get('assertion_type') not in {'实际经历', '购买诉求', '推测', '建议', '一般陈述'}:
                    fail(f'{lp}: assertion_type 不合法')
                if not isinstance(label.get('evidence_object'), str) or not label['evidence_object']:
                    fail(f'{lp}: 必须填写 evidence_object')
            records.append(r)
    if not records:
        fail('输入文件没有已打标记录；不能生成真实统计')
    return records

def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def merge_sentiments(values):
    values = set(values)
    if '混合' in values or {'正向', '负向'} <= values:
        return '混合'
    if '负向' in values:
        return '负向'
    if '正向' in values:
        return '正向'
    return '中性'

def analyze(records, out, low_star_max=3, input_path=None):
    out.mkdir(parents=True, exist_ok=True)
    eligible = [r for r in records if r['in_scope'] and r['content_type'] in {'review', 'comment'} and r['author_role'] not in EXCLUDED_ROLES]
    if not eligible:
        fail('筛选后没有可统计的消费者评论')
    evidence = []
    for r in eligible:
        for i, label in enumerate(r['labels'], 1):
            evidence.append({
                'assignment_id': hashlib.sha256(f"{r['source_id']}|{i}".encode()).hexdigest()[:24],
                'source_id': r['source_id'], 'platform': r['platform'], 'brand': r.get('brand') or '品牌未知',
                'brand_object': r.get('brand_object') or '对象未知',
                'rating': r.get('rating'), 'level1': label['level1'], 'level2': label['level2'], 'level3': label['level3'],
                'sentiment': label['sentiment'], 'is_defect': label['is_defect'], 'assertion_type': label['assertion_type'],
                'evidence_object': label['evidence_object'], 'evidence_quote': label['evidence_quote'],
                'text_raw': r['text_raw'], 'source_url': r['source_url']})
    # A source counts once per tag path; multiple opposing statements resolve to mixed.
    groups = defaultdict(list)
    for e in evidence:
        groups[(e['source_id'], e['level1'], e['level2'], e['level3'])].append(e)
    counts = defaultdict(Counter)
    for (_, a, b, c), assignments in groups.items():
        counts[(a, b, c)][merge_sentiments(e['sentiment'] for e in assignments)] += 1
    n = len(eligible)
    top = []
    for (a, b, c), counter in sorted(counts.items(), key=lambda kv: (-sum(kv[1].values()), kv[0]))[:20]:
        hits = sum(counter.values())
        top.append(dict(level1=a, level2=b, level3=c, frequency=hits, positive=counter['正向'], negative=counter['负向'], neutral=counter['中性'], mixed=counter['混合'], n=n, mention_rate=round(hits/n, 6), definition='同一source_id同一三级路径计1次；按总频次降序；情感针对标签'))
    # Aggregate at level2 again to prevent multiple level3 tags inflating the cross-tab.
    brand_denominators = defaultdict(set)
    for r in eligible:
        brand_denominators[(r.get('brand') or '品牌未知', r.get('brand_object') or '对象未知')].add(r['source_id'])
    brand_groups = defaultdict(list)
    for e in evidence:
        brand_groups[(e['brand'], e['brand_object'], e['source_id'], e['level1'], e['level2'])].append(e['sentiment'])
    brand_counts = defaultdict(Counter)
    for (brand, obj, sid, a, b), sentiments in brand_groups.items():
        brand_counts[(brand, obj, a, b)][merge_sentiments(sentiments)] += 1
    cross = []
    for (brand, obj, a, b), counter in sorted(brand_counts.items()):
        bn = len(brand_denominators[(brand, obj)])
        cross.append(dict(brand=brand, brand_object=obj, level1=a, level2=b, positive=counter['正向'], negative=counter['负向'], neutral=counter['中性'], mixed=counter['混合'], frequency=sum(counter.values()), n_brand=bn, n_total=n, definition='同一品牌对象内，同一source_id同一二级路径计1次；未知品牌单列'))
    low = [r for r in eligible if r['platform']=='Amazon' and r.get('rating') is not None and r['rating'] <= low_star_max]
    low_ids = {r['source_id'] for r in low}
    defects = defaultdict(set)
    for e in evidence:
        if e['source_id'] in low_ids and e['is_defect'] and e['assertion_type']=='实际经历' and e['sentiment'] in {'负向', '混合'}:
            defects[(e['evidence_object'], e['level1'], e['level2'], e['level3'])].add(e['source_id'])
    defect_rows = []
    for (obj, a, b, c), ids in sorted(defects.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        defect_rows.append(dict(evidence_object=obj, level1=a, level2=b, level3=c, frequency=len(ids), n_low_star=len(low), mention_rate=round(len(ids)/len(low), 6), source_ids='|'.join(sorted(ids)), definition=f'Amazon星级≤{low_star_max}；仅实际经历且缺陷标记为true、情感负向或混合；同条同标签计1次'))
    write_csv(out/'top20_level3_sentiment.csv', ['level1','level2','level3','frequency','positive','negative','neutral','mixed','n','mention_rate','definition'], top)
    write_csv(out/'brand_level2_sentiment.csv', ['brand','brand_object','level1','level2','positive','negative','neutral','mixed','frequency','n_brand','n_total','definition'], cross)
    write_csv(out/'low_star_defects.csv', ['evidence_object','level1','level2','level3','frequency','n_low_star','mention_rate','source_ids','definition'], defect_rows)
    write_csv(out/'label_evidence.csv', ['assignment_id','source_id','platform','brand','brand_object','rating','level1','level2','level3','sentiment','is_defect','assertion_type','evidence_object','evidence_quote','text_raw','source_url'], evidence)
    metadata = {
        'input': str(input_path) if input_path else None,
        'input_sha256': hashlib.sha256(input_path.read_bytes()).hexdigest() if input_path else None,
        'n_input': len(records), 'n_eligible': n, 'n_excluded': len(records)-n,
        'n_labeled_sources': sum(bool(r['labels']) for r in eligible), 'n_label_assignments': len(evidence),
        'n_low_star': len(low), 'low_star_max': low_star_max,
        'n_low_star_with_defects': len(set().union(*defects.values())) if defects else 0,
        'n_unknown_brand': sum(not r.get('brand') for r in eligible),
        'brand_denominators': [{'brand': b, 'brand_object': o, 'n':len(ids)} for (b,o),ids in sorted(brand_denominators.items())],
        'rules': [
            '统计单位为唯一source_id；排除母帖、商家、品牌、机器人和范围外内容。',
            '空labels仍纳入合格样本分母，避免只对有标签评论计算提及率。',
            '同路径同时出现正负向归混合；正或负与中性并存时采用正或负。',
            '不同标签允许同一评论重复出现，因此标签提及率之和可超过100%。',
            '品牌由人工证据字段提供，不从产品ID、平台或兼容设备名称自动猜测配件品牌。',
            '低星缺陷不等于全部负向表达；价格、诉求、推测和建议不自动视为实际缺陷。',
            'Reddit没有星级，不能进入低星子集；样本频次不能解释为市场普及率。',
            'n_low_star为0时缺陷CSV仅保留表头，元数据保留n=0，不伪造零缺陷结论。']}
    (out/'statistics_metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    cell_map = []
    third_cells = defaultdict(set)
    for (sid, a, b, c), assignments in groups.items():
        third_cells[(a,b,c,merge_sentiments(e['sentiment'] for e in assignments))].add(sid)
    for (a,b,c,sentiment), ids in sorted(third_cells.items()):
        cell_map.append(dict(table='level3_sentiment',level1=a,level2=b,level3=c,sentiment=sentiment,frequency=len(ids),n=n,source_ids=sorted(ids)))
    brand_cells = defaultdict(set)
    for (brand,obj,sid,a,b), sentiments in brand_groups.items():
        brand_cells[(brand,obj,a,b,merge_sentiments(sentiments))].add(sid)
    for (brand,obj,a,b,sentiment), ids in sorted(brand_cells.items()):
        cell_map.append(dict(table='brand_level2_sentiment',brand=brand,brand_object=obj,level1=a,level2=b,sentiment=sentiment,frequency=len(ids),n=len(brand_denominators[(brand,obj)]),source_ids=sorted(ids)))
    for (obj,a,b,c), ids in sorted(defects.items()):
        cell_map.append(dict(table='low_star_defects',evidence_object=obj,level1=a,level2=b,level3=c,frequency=len(ids),n=len(low),source_ids=sorted(ids)))
    (out/'cell_source_map.json').write_text(json.dumps(cell_map,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'statistics.json').write_text(json.dumps({'metadata':metadata, 'top20':top, 'brand_cross_table':cross, 'low_star_defects':defect_rows}, ensure_ascii=False, indent=2), encoding='utf-8')
    return metadata

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', required=True, type=Path, help='已校准打标JSONL，一条评论一行')
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--low-star-max', type=int, default=3, choices=[1,2,3,4,5])
    args = p.parse_args()
    try:
        result = analyze(load(args.input), args.out, args.low_star_max, args.input)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        p.exit(2, f'错误：{exc}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
