"""Synthetic fixtures only; these are not customer comments or VOC findings."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from voc_statistics import analyze, load

def label(sentiment='负向', assertion='实际经历', defect=True, leaf='罩体固定'):
    return dict(level1='功能价值', level2='配件适配', level3=leaf, sentiment=sentiment,
                is_defect=defect, assertion_type=assertion, evidence_object='保护套', evidence_quote='synthetic')

def record(sid='test1', platform='Amazon', rating=2):
    return dict(source_id=sid, text_raw='synthetic fixture text', platform=platform, rating=rating,
                source_url='https://example.invalid/test', content_type='review' if platform=='Amazon' else 'comment',
                author_role='consumer', in_scope=True, coding_status='已校准',brand=None, labels=[label()])

class StatisticsTests(unittest.TestCase):
    def run_analysis(self, rows):
        with tempfile.TemporaryDirectory() as d:
            m=analyze(rows, Path(d))
            result=json.loads((Path(d)/'statistics.json').read_text())
            cell_map=json.loads((Path(d)/'cell_source_map.json').read_text())
            known={r['source_id'] for r in rows}
            for cell in cell_map:
                self.assertEqual(cell['frequency'],len(set(cell['source_ids'])))
                self.assertTrue(set(cell['source_ids']) <= known)
                self.assertLessEqual(cell['frequency'],cell['n'])
            evidence=(Path(d)/'label_evidence.csv').read_text(encoding='utf-8-sig')
            return m,result,evidence

    def test_duplicate_tag_and_opposing_sentiment(self):
        r=record(); r['labels']=[label(),label(),label('正向',defect=False)]
        m,result,evidence=self.run_analysis([r])
        self.assertEqual(result['top20'][0]['frequency'],1)
        self.assertEqual(result['top20'][0]['mixed'],1)
        self.assertEqual(result['low_star_defects'][0]['frequency'],1)
        self.assertIn('synthetic fixture text',evidence)
        self.assertIn('test1',evidence)

    def test_second_level_dedupe_and_unlabeled_denominator(self):
        r=record();r['labels'] += [label(leaf='装配方式')]
        empty=record('test2');empty['labels']=[]
        m,result,_=self.run_analysis([r,empty])
        self.assertEqual(result['brand_cross_table'][0]['frequency'],1)
        self.assertEqual(result['brand_cross_table'][0]['n_brand'],2)
        self.assertEqual(result['top20'][0]['mention_rate'],.5)

    def test_reddit_and_seller_excluded_from_low_star(self):
        r=record(platform='Reddit',rating=None)
        seller=record('seller');seller['author_role']='seller_founder'
        m,result,_=self.run_analysis([r,seller])
        self.assertEqual(m['n_eligible'],1)
        self.assertEqual(m['n_low_star'],0)
        self.assertEqual(result['low_star_defects'],[])

    def test_speculation_not_defect(self):
        r=record();r['labels']=[label(assertion='推测')]
        m,result,_=self.run_analysis([r])
        self.assertEqual(m['n_low_star'],1)
        self.assertEqual(result['low_star_defects'],[])

    def test_reject_pending_or_nonverbatim_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input.jsonl';r=record();r['coding_status']='待校准'
            p.write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError,'已校准'):load(p)
            r['coding_status']='已校准';r['labels'][0]['evidence_quote']='not present'
            p.write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError,'逐字'):load(p)

    def test_brand_objects_remain_separate(self):
        a=record('a');b=record('b')
        for r,obj in [(a,'戒指本体'),(b,'保护套')]:
            r.update(brand='TestBrand',brand_object=obj,brand_evidence='synthetic')
        m,result,_=self.run_analysis([a,b])
        self.assertEqual(len(result['brand_cross_table']),2)
        self.assertTrue(all(r['n_brand']==1 for r in result['brand_cross_table']))

if __name__=='__main__':unittest.main()
