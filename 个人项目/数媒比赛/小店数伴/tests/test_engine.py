import unittest
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import Dataset


def metadata():
    return {'id':'test', 'kind':'user', 'currency':'CNY', 'currencySymbol':'¥'}


def row(order, product, quantity=1, price=10, date='2026-10-01'):
    return {'订单号':order,'日期':date,'商品':product,'数量':quantity,'单价':price}


class AnalyticsTests(unittest.TestCase):
    def test_money_counts_exclusions_and_deduplication(self):
        raw = pd.DataFrame([
            row('A1','苹果',2,10), row('A1','香蕉',1,5),
            row('A2','苹果',1,10,'2026-10-02'), row('A2','苹果',1,10,'2026-10-02'),
            row('C3','苹果',-1,10), row('A4','',1,10),
            row('A5','苹果',1,10,'not-a-date'),row('A6','苹果',0,10),
        ])
        dataset=Dataset.create(raw,metadata())
        report=dataset.analyze(days=30)
        self.assertEqual(report['summary']['sales'],35)
        self.assertEqual(report['summary']['orders'],2)
        self.assertEqual(report['summary']['averageOrder'],17.5)
        self.assertEqual(report['summary']['reversalAmount'],10)
        self.assertEqual(report['quality']['totalRows'],8)
        self.assertEqual(report['quality']['excludedRows'],4)
        self.assertEqual(report['quality']['positiveRows'],3)
        self.assertEqual(report['quality']['reversalRows'],1)
        self.assertEqual(dataset.analyze(days=30,deduplicate=False)['summary']['sales'],45)
        self.assertFalse(report['period']['comparisonComplete'])
        self.assertIsNone(report['deltas']['sales'])

    def test_cancelled_prefix_is_explicit_not_assumed_for_user_files(self):
        raw=pd.DataFrame([row('C100','茶杯')])
        self.assertEqual(Dataset.create(raw,metadata()).analyze()['summary']['sales'],10)
        result=Dataset.create(raw,metadata(),cancelled_prefix=True).analyze()
        self.assertEqual(result['summary']['sales'],0)
        self.assertEqual(result['summary']['reversalOrders'],1)
        self.assertIsNone(result['summary']['averageOrder'])

    def test_line_amount_has_priority_and_currency_is_not_converted(self):
        raw=pd.DataFrame([row('1','茶杯',2,10)])
        raw['实付金额']=[7.5]
        report=Dataset.create(raw,metadata()).analyze()
        self.assertEqual(report['summary']['sales'],7.5)
        self.assertEqual(report['meta']['currency'],'CNY')

    def test_ambiguous_dates_need_selected_order(self):
        raw=pd.DataFrame([row('1','茶杯',date='03/04/2026')])
        with self.assertRaises(ValueError):
            Dataset.create(raw,metadata())
        self.assertEqual(Dataset.create(raw,metadata(),date_order='dmy').metadata['start'],'2026-04-03')
        self.assertEqual(Dataset.create(raw,metadata(),date_order='mdy').metadata['start'],'2026-03-04')

    def test_nonfinite_quantity_and_amount_do_not_pollute_sum(self):
        raw=pd.DataFrame([row('1','茶杯'),row('2','茶杯',float('inf')),row('3','茶杯',1,'NaN')])
        result=Dataset.create(raw,metadata()).analyze()
        self.assertEqual(result['summary']['sales'],10)
        self.assertEqual(result['quality']['excludedRows'],2)

    def test_basket_metrics_use_distinct_orders_not_line_frequency(self):
        rows=[]
        for order in ['1','2','3']:
            rows.extend([row(order,'A'),row(order,'B')])
        rows.extend([row('4','A'),row('5','B'),row('6','C'),row('7','C'),row('8','C')])
        result=Dataset.create(pd.DataFrame(rows),metadata()).analyze()
        pair=next(p for p in result['pairs'] if p['a']=='A' and p['b']=='B')
        self.assertEqual(pair['count'],3)
        self.assertEqual(pair['support'],.375)
        self.assertEqual(pair['confidence'],.75)
        self.assertEqual(pair['lift'],1.5)
        self.assertEqual(result['pairMethod']['basketOrders'],8)
        self.assertEqual([r['order'] for r in pair['evidence']],['1','2','3'])
        self.assertEqual(pair['evidence'][0]['sourceRows'],[2,3])
        self.assertEqual(pair['evidence'][0]['aQuantity'],1)

    def test_complete_previous_window_and_zero_denominator(self):
        raw=pd.DataFrame([row('1','A',1,10,'2026-10-01'),row('2','A',1,20,'2026-10-14')])
        result=Dataset.create(raw,metadata()).analyze(days=7)
        self.assertTrue(result['period']['comparisonComplete'])
        self.assertEqual(result['summary']['sales'],20)
        self.assertEqual(result['previous']['sales'],10)
        self.assertEqual(result['deltas']['sales'],1)
        raw=pd.DataFrame([row('C1','A',-1,10,'2026-10-01'),row('2','A',1,20,'2026-10-14')])
        result=Dataset.create(raw,metadata()).analyze(days=7)
        self.assertTrue(result['period']['comparisonComplete'])
        self.assertIsNone(result['deltas']['sales'])

    def test_oversized_baskets_are_reported_and_not_counted(self):
        raw=pd.DataFrame([row('big',f'P{i}') for i in range(61)]+[row('small','A')])
        result=Dataset.create(raw,metadata()).analyze()
        self.assertEqual(result['pairMethod']['largeOrdersSkipped'],1)
        self.assertEqual(result['pairMethod']['basketOrders'],1)
        self.assertEqual(result['pairs'],[])

    def test_known_public_fees_are_separated_from_merchandise(self):
        raw=pd.DataFrame([{'InvoiceNo':'1','InvoiceDate':'2026-10-01','Description':'Postage','StockCode':'POST','Quantity':1,'UnitPrice':20},
                          {'InvoiceNo':'1','InvoiceDate':'2026-10-01','Description':'Cup','StockCode':'100','Quantity':2,'UnitPrice':10}])
        meta=metadata();meta['kind']='public'
        result=Dataset.create(raw,meta).analyze()
        self.assertEqual(result['summary']['sales'],40)
        self.assertEqual(result['summary']['nonProductAmount'],20)
        self.assertEqual(result['summary']['products'],1)
        self.assertEqual(result['products'][0]['sku'],'100')
        self.assertEqual(result['products'][0]['share'],.5)

    def test_user_supplied_source_row_does_not_replace_actual_file_row(self):
        raw=pd.DataFrame([row('1','A'),row('1','B')]);raw['SourceRow']=[99999,88888]
        dataset=Dataset.create(raw,metadata())
        self.assertEqual(list(dataset.frame['source_row']),[2,3])


if __name__=='__main__':
    unittest.main(verbosity=2)
