"""Transparent order analytics. No model API or network access is used here."""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from dataclasses import dataclass
from datetime import timedelta
import hashlib
import math
import re
import numpy as np
import pandas as pd

ALIASES = {
    'order': ['InvoiceNo', '订单号', '订单编号', 'order_id', 'OrderID'],
    'date': ['InvoiceDate', '日期', '下单时间', '订单日期', 'date'],
    'product': ['Description', '商品', '商品名称', 'product', 'ProductName'],
    'sku': ['StockCode', '商品编码', 'SKU', 'sku'],
    'quantity': ['Quantity', '数量', '购买数量', 'quantity'],
    'unitprice': ['UnitPrice', '单价', 'unit_price'],
    'amount': ['实付金额', '行金额', '金额', 'amount', 'line_total'],
}
NON_PRODUCT_CODES = {'POST', 'DOT', 'M', 'D', 'C2', 'CRUK', 'BANK CHARGES', 'AMAZONFEE', 'S', 'B'}


def guess_mapping(columns):
    return {key: next((candidate for candidate in candidates if candidate in columns), '')
            for key, candidates in ALIASES.items()}


def number(value, digits=2):
    return round(float(value), digits) if pd.notna(value) and math.isfinite(float(value)) else None


def parse_dates(series, date_order):
    text = series.fillna('').astype(str).str.strip()
    if date_order == 'iso':
        valid_format = text.str.match(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:[ T].*)?$')
        return pd.to_datetime(text.where(valid_format), errors='coerce', format='mixed')
    if date_order not in {'dmy', 'mdy'}:
        raise ValueError('请选择年-月-日、日/月/年或月/日/年的日期口径。')
    return pd.to_datetime(text, errors='coerce', format='mixed', dayfirst=date_order == 'dmy')


@dataclass
class Dataset:
    frame: pd.DataFrame
    metadata: dict
    mapping: dict
    date_order: str
    cancelled_prefix: bool

    @classmethod
    def create(cls, raw, metadata, mapping=None, date_order='iso', cancelled_prefix=False):
        mapping = mapping or guess_mapping(raw.columns)
        for key in ['order', 'date', 'product', 'quantity']:
            if not mapping.get(key) or mapping[key] not in raw.columns:
                raise ValueError(f'缺少必需字段：{key}，请在导入窗口完成列映射。')
        if not (mapping.get('amount') in raw.columns or mapping.get('unitprice') in raw.columns):
            raise ValueError('至少需要“行实付金额”或“单价”中的一列。')
        frame = pd.DataFrame(index=raw.index)
        for field in ['order', 'product', 'sku']:
            selected = mapping.get(field) or mapping['product']
            frame[field] = raw[selected].fillna('').astype(str).str.strip()
        frame['raw_date'] = raw[mapping['date']].fillna('').astype(str)
        dates = parse_dates(raw[mapping['date']], date_order)
        try:
            if dates.dt.tz is not None:
                raise ValueError('日期带有时区，请先统一为不带时区的本地订单日期。')
            frame['date'] = dates.dt.normalize()
        except AttributeError as exc:
            raise ValueError('日期含混合时区，请先统一为本地订单日期。') from exc
        frame['quantity'] = pd.to_numeric(raw[mapping['quantity']], errors='coerce')
        if mapping.get('amount') in raw.columns:
            frame['amount'] = pd.to_numeric(raw[mapping['amount']], errors='coerce')
        else:
            frame['amount'] = frame['quantity'] * pd.to_numeric(raw[mapping['unitprice']], errors='coerce')
        frame['source_row'] = pd.to_numeric(raw['SourceRow'], errors='coerce') if 'SourceRow' in raw and metadata.get('kind') == 'public' else raw.index + 2
        frame['duplicate'] = frame.duplicated(subset=['order', 'sku', 'product', 'raw_date', 'quantity', 'amount'], keep='first')
        frame['missing_key'] = frame['order'].eq('') | frame['product'].eq('') | frame['sku'].eq('')
        frame['invalid_date'] = frame['date'].isna()
        frame['invalid_quantity'] = ~np.isfinite(frame['quantity']) | frame['quantity'].eq(0)
        frame['invalid_amount'] = ~np.isfinite(frame['amount']) | frame['amount'].eq(0)
        prefix = frame['order'].str.upper().str.startswith('C') if cancelled_prefix else pd.Series(False, index=frame.index)
        frame['reversal'] = frame['quantity'].lt(0) | frame['amount'].lt(0) | prefix
        frame['invalid'] = frame[['missing_key', 'invalid_date', 'invalid_quantity', 'invalid_amount']].any(axis=1)
        if not (~frame['invalid']).any():
            raise ValueError('没有可分析记录。请检查列映射、日期顺序、数量及金额；取消导入可保留原数据。')
        metadata = dict(metadata)
        metadata['rows'] = int(len(frame))
        metadata['start'] = frame['date'].min().strftime('%Y-%m-%d')
        metadata['end'] = frame['date'].max().strftime('%Y-%m-%d')
        return cls(frame, metadata, mapping, date_order, cancelled_prefix)

    def quality(self, deduplicate=True):
        frame = self.frame
        excluded = frame['invalid'] | (frame['duplicate'] if deduplicate else False)
        issues = [
            ('duplicate', '精确重复行', '保留首行，其余按当前去重选项处理', int(frame['duplicate'].sum())),
            ('missing_key', '关键标识缺失', '订单号或商品缺失，无法可靠归属', int(frame['missing_key'].sum())),
            ('invalid_date', '日期无法识别', '按所选日期格式解析失败，先核对原表', int(frame['invalid_date'].sum())),
            ('invalid_quantity', '数量不可用', '数量为零、空值或非有限数值', int(frame['invalid_quantity'].sum())),
            ('invalid_amount', '金额不可用', '金额为零、空值或非有限数值', int(frame['invalid_amount'].sum())),
            ('reversal', '负向 / 取消记录', '单独列示，不计入正向销售；不等于已确认退款', int((frame['reversal'] & ~frame['invalid']).sum())),
        ]
        flagged = frame['invalid'] | frame['duplicate'] | frame['reversal']
        examples = []
        labels = {key: title for key, title, _, _ in issues}
        for _, row in frame[flagged].head(30).iterrows():
            examples.append({'sourceRow': int(row['source_row']) if pd.notna(row['source_row']) else None,
                             'order': row['order'], 'product': row['product'], 'date': row['raw_date'],
                             'quantity': number(row['quantity'], 4), 'amount': number(row['amount']),
                             'issues': [labels[key] for key in labels if row[key]]})
        return {'totalRows': int(len(frame)), 'excludedRows': int(excluded.sum()),
                'positiveRows': int((~excluded & ~frame['reversal']).sum()),
                'reversalRows': int((~excluded & frame['reversal']).sum()),
                'flaggedRows': int(flagged.sum()), 'duplicateRows': int(frame['duplicate'].sum()),
                'invalidRows': int(frame['invalid'].sum()),
                'issues': [{'id': key, 'title': title, 'description': desc, 'count': count} for key, title, desc, count in issues],
                'examples': examples,
                'note': '体检覆盖全文件；问题类型可能重叠，不能把各项计数直接相加。原始文件不被修改。'}

    def analyze(self, days=30, deduplicate=True):
        if days not in {7, 14, 30, 60, 0}:
            raise ValueError('不支持的分析天数。')
        frame = self.frame
        end = pd.Timestamp(self.metadata['end'])
        start = end - timedelta(days=days - 1) if days else pd.Timestamp(self.metadata['start'])
        start = max(start, pd.Timestamp(self.metadata['start']))
        period_length = (end - start).days + 1
        previous_end = start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=period_length - 1)
        comparison_complete = previous_start >= pd.Timestamp(self.metadata['start'])
        excluded = frame['invalid'] | (frame['duplicate'] if deduplicate else False)
        eligible = frame[~excluded]
        current = eligible[eligible['date'].between(start, end)]
        prior = eligible[eligible['date'].between(previous_start, previous_end)]

        def summarize(part):
            positives = part[~part['reversal']]
            reversals = part[part['reversal']]
            merchandise = positives[~positives['sku'].isin(NON_PRODUCT_CODES)] if self.metadata['kind'] == 'public' else positives
            sales = float(positives['amount'].sum())
            orders = positives['order'].nunique()
            all_orders = part['order'].nunique()
            return {'sales': number(sales), 'orders': int(orders),
                    'averageOrder': number(sales / orders) if orders else None,
                    'products': int(merchandise['sku'].nunique()),
                    'nonProductAmount': number(positives.loc[~positives.index.isin(merchandise.index), 'amount'].sum()),
                    'reversalAmount': number(reversals['amount'].abs().sum()),
                    'reversalOrders': int(reversals['order'].nunique()),
                    'reversalRate': number(reversals['order'].nunique() / all_orders, 6) if all_orders else 0,
                    'rows': int(len(part))}

        summary = summarize(current)
        previous = summarize(prior)
        deltas = {}
        for key in ['sales', 'orders', 'averageOrder', 'products']:
            before, after = previous[key], summary[key]
            deltas[key] = number((after - before) / before, 6) if comparison_complete and before and after is not None else None
        positives = current[~current['reversal']]
        old_positives = prior[~prior['reversal']]
        totals = positives.groupby('date')['amount'].sum()
        old_totals = old_positives.groupby('date')['amount'].sum()
        trend = [{'date': date.strftime('%Y-%m-%d'), 'sales': number(totals.get(date, 0)),
                  'previous': number(old_totals.get(date - timedelta(days=period_length), 0)) if comparison_complete else None}
                 for date in pd.date_range(start, end)]
        products = []
        merchandise = positives[~positives['sku'].isin(NON_PRODUCT_CODES)] if self.metadata['kind'] == 'public' else positives
        if len(merchandise):
            grouped = merchandise.groupby('sku').agg(name=('product', 'first'), sales=('amount', 'sum'),
                                                   quantity=('quantity', 'sum'), orders=('order', 'nunique'))
            grouped = grouped.sort_values('sales', ascending=False)
            for sku, row in grouped.head(100).iterrows():
                products.append({'sku': str(sku), 'name': row['name'], 'sales': number(row['sales']),
                                 'quantity': number(row['quantity'], 4), 'orders': int(row['orders']),
                                 'share': number(row['sales'] / summary['sales'], 6) if summary['sales'] else 0})
        pairs, pair_method = self.associations(positives)
        quality = self.quality(deduplicate)
        actions = []

        def action(rule, title, detail, evidence, target, priority='建议核查'):
            key = hashlib.sha256(f'{rule}:{start}:{end}:{deduplicate}'.encode()).hexdigest()[:12]
            actions.append({'id': key, 'rule': rule, 'title': title, 'detail': detail, 'evidence': evidence,
                            'target': target, 'priority': priority})

        if quality['excludedRows']:
            action('quality', '先核对被排除的数据行', '查看原行号及问题类型，核实后修正原文件并重新导入。去重可切换，原始文件不会被改写。',
                   f"全文件{quality['totalRows']:,}行；当前排除{quality['excludedRows']:,}行，其中精确重复{quality['duplicateRows']:,}行，其他不可用记录{quality['invalidRows']:,}行（可能重叠）。", 'quality', '优先核查')
        if summary['reversalOrders']:
            action('reversal', '单独核对负向与取消记录', '核实它们是取消、退货还是记账修正。本工具没有支付流水，不能据此认定已退款或计算净利润。',
                   f"本期{summary['reversalOrders']:,}个订单编号存在负向/取消记录；绝对金额{self.metadata['currencySymbol']}{summary['reversalAmount']:,.2f}。", 'quality')
        if deltas['sales'] is not None and deltas['sales'] <= -0.15:
            action('decline', '核对本期销售下降的原因', '先比较订单数量和客单金额，再核对活动、缺货或营业时间。时间对比只描述变化，不判断变化原因。',
                   f"与前一个同长区间相比，正向销售额变化{deltas['sales']:+.1%}，正向订单数变化{deltas['orders']:+.1%}。", 'overview')
        top_three_share = sum(item['share'] for item in products[:3])
        if len(products) > 3 and top_three_share >= 0.2:
            action('concentration', '检查核心商品的可售状态', '核对核心商品是否仍可正常交付。本工具没有库存字段，不自动生成补货数量。',
                   f'前三项商品占本期正向销售额{top_three_share:.1%}；共有{summary["products"]:,}种商品产生正向记录。', 'products')
        if pairs:
            top = pairs[0]
            action('pair', '把同购关联作为组合试验线索', '可以先做小范围组合陈列试验，并记录结果。关联不等于组合促销一定有效。',
                   f'{top["aName"]} 与 {top["bName"]} 同现{top["count"]}单，提升度{top["lift"]:.2f}；完整口径见商品洞察。', 'products')
        return {'meta': self.metadata, 'mapping': self.mapping, 'quality': quality, 'summary': summary,
                'previous': previous, 'deltas': deltas, 'trend': trend, 'products': products,
                'pairs': pairs, 'pairMethod': pair_method, 'actions': actions,
                'period': {'start': start.strftime('%Y-%m-%d'), 'end': end.strftime('%Y-%m-%d'), 'days': period_length,
                           'previousStart': previous_start.strftime('%Y-%m-%d'), 'previousEnd': previous_end.strftime('%Y-%m-%d'),
                           'comparisonComplete': bool(comparison_complete)},
                'options': {'days': days, 'deduplicate': bool(deduplicate), 'dateOrder': self.date_order,
                            'cancelledPrefix': bool(self.cancelled_prefix)},
                'methods': {'sales': '有效正向行金额之和，包含有效的邮费等费用记录；排除当前规则下的重复、不可用和负向/取消记录。不是净利润或已确认收款。公开样例中的已知非商品编码不参与商品数量、榜单及同购计算；商品占比的分母仍为全部正向行金额。',
                            'averageOrder': '有效正向行金额合计 ÷ 正向记录的去重订单编号数。',
                            'comparison': '与本期紧邻的前一个同长日历区间比较；若原始数据日期范围不覆盖完整上期或分母为零，不展示增幅。未出现订单的日期按0处理，无法判断是否缺报。',
                            'duplicates': '订单号、商品编码、名称、原日期文本、数量与行金额完全相同视为重复候选；也可能是合法重复行，请核实后选择是否剔除。'}}

    def associations(self, positives):
        ignored_codes = NON_PRODUCT_CODES if self.metadata['kind'] == 'public' else set()
        product_rows = positives[~positives['sku'].isin(ignored_codes)]
        top_skus = set(product_rows.groupby('sku')['amount'].sum().nlargest(80).index)
        baskets = product_rows.groupby('order')['sku'].agg(lambda s: set(s))
        skipped = int(baskets.map(len).gt(60).sum())
        baskets = baskets[baskets.map(len).le(60)]
        base = int(len(baskets))
        item_counts, pair_counts = Counter(), Counter()
        for basket in baskets:
            selected = sorted(basket & top_skus)
            item_counts.update(selected)
            pair_counts.update(combinations(selected, 2))
        names = product_rows.drop_duplicates('sku').set_index('sku')['product'].to_dict()
        output = []
        for (a, b), count in pair_counts.items():
            if count < 3:
                continue
            lift = count * base / (item_counts[a] * item_counts[b])
            if lift <= 1:
                continue
            output.append({'a': str(a), 'b': str(b), 'aName': names[a], 'bName': names[b], 'count': int(count),
                           'support': number(count / base, 6), 'confidence': number(count / item_counts[a], 6),
                           'lift': number(lift, 4)})
        output.sort(key=lambda row: (row['count'], row['lift']), reverse=True)
        selected_pairs = output[:8]
        for pair in selected_pairs:
            orders = [order for order, basket in baskets.items() if pair['a'] in basket and pair['b'] in basket][:10]
            evidence = []
            for order in orders:
                lines = positives[positives['order'].eq(order) & positives['sku'].isin([pair['a'], pair['b']])]
                evidence.append({'order': str(order), 'date': lines['date'].min().strftime('%Y-%m-%d'),
                                 'aQuantity': number(lines.loc[lines['sku'].eq(pair['a']), 'quantity'].sum(), 4),
                                 'bQuantity': number(lines.loc[lines['sku'].eq(pair['b']), 'quantity'].sum(), 4),
                                 'sourceRows': [int(value) for value in lines['source_row'] if pd.notna(value)]})
            pair['evidence'] = evidence
        return selected_pairs, {'basketOrders': base, 'largeOrdersSkipped': skipped, 'candidateLimit': 80, 'minCoorders': 3,
                           'description': '取本期销售额最高的至多80种商品计算二项同购；排除超过60种商品的大单。每单同一商品只计一次。至少同现3单且提升度>1才展示；这是探索线索，未作显著性或因果检验。',
                           'support': '同购订单数 / 纳入计算的有效商品订单数',
                           'confidence': '同时包含A、B的订单数 / 包含A的订单数（A→B）',
                           'lift': '同购订单数 × 有效商品订单数 /（包含A的订单数 × 包含B的订单数）'}
