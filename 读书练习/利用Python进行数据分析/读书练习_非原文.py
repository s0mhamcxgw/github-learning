"""自编读书练习，非原书代码；只使用本机合成数据。"""
import io
import json
import os
import sys
from pathlib import Path

WORK = Path('E:/Documents/ChatGPT/obsidian/work/book-study-pydata2-20261111')
OUT = Path('E:/Documents/ChatGPT/obsidian/outputs/利用Python进行数据分析-第2版练习-20261111')
OUT.mkdir(parents=True, exist_ok=True)
os.environ['MPLCONFIGDIR'] = str(WORK / 'matplotlib-cache')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 练习01：引用与副本
original = [1, 2]
reference = original
independent = original.copy()
reference.append(3)
assert original == [1, 2, 3] and independent == [1, 2]

# 练习02：数组形状、广播与矩阵乘积
array = np.arange(6).reshape(2, 3)
centered = array - array.mean(axis=1, keepdims=True)
assert np.array_equal(centered, [[-1, 0, 1], [-1, 0, 1]])
assert np.array_equal(array @ array.T, [[5, 14], [14, 50]])

# 练习03：CSV读入、缺失与重复
csv_text = 'id,city,amount,date\n1,贵阳,100,2026-01-01\n2,贵阳,,2026-01-02\n3,成都,50,2026-01-01\n3,成都,50,2026-01-01\n4,成都,70,2026-01-02\n'
raw = pd.read_csv(io.StringIO(csv_text))
assert len(raw) == 5 and raw['amount'].isna().sum() == 1
clean = raw.drop_duplicates(subset='id').copy()
clean['amount'] = clean['amount'].fillna(clean.groupby('city')['amount'].transform('mean'))
assert len(clean) == 4 and clean['amount'].isna().sum() == 0

# 练习04：连接与分组
lookup = pd.DataFrame({'city': ['贵阳', '成都'], 'region': ['贵州', '四川']})
joined = clean.merge(lookup, on='city', how='left', validate='many_to_one')
assert len(joined) == 4 and joined['region'].notna().all()
totals = joined.groupby('city')['amount'].sum()
assert totals.to_dict() == {'成都': 120.0, '贵阳': 200.0}

# 练习05：重塑与按天汇总
joined['date'] = pd.to_datetime(joined['date'])
wide = joined.pivot(index='date', columns='city', values='amount')
daily = joined.set_index('date')['amount'].resample('D').sum()
assert wide.shape == (2, 2) and daily.tolist() == [150.0, 170.0]

# 练习06：组内比例、分类类型与文本往返
joined['share'] = joined['amount'] / joined.groupby('city')['amount'].transform('sum')
assert np.allclose(joined.groupby('city')['share'].sum(), 1.0)
joined['city'] = joined['city'].astype('category')
reloaded = pd.read_csv(io.StringIO(joined.to_csv(index=False)))
assert len(reloaded) == 4 and reloaded['amount'].sum() == 320.0

# 练习07：最小线性拟合示意，不作为模型评估
x = np.array([0., 1., 2.])
y = np.array([1., 3., 5.])
design = np.column_stack([np.ones_like(x), x])
coefficients = np.linalg.lstsq(design, y, rcond=None)[0]
assert np.allclose(coefficients, [1., 2.])

# 练习08：柱状图方向与保存
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
fig, axes = plt.subplots(1, 2, figsize=(8, 3.4))
bars = axes[0].bar(totals.index.tolist(), totals.values)
bars_horizontal = axes[1].barh(totals.index.tolist(), totals.values)
assert bars.patches[0].get_height() == 120.0
assert bars_horizontal.patches[0].get_width() == 120.0
axes[0].set_title('bar：竖向柱状图')
axes[1].set_title('barh：横向柱状图')
axes[0].set_ylabel('金额（自编练习）')
axes[1].set_xlabel('金额（自编练习）')
fig.tight_layout()
figure = OUT / 'Python数据分析2版_自编练习_柱状图方向.png'
fig.savefig(figure, dpi=150)
plt.close(fig)

report = {'status': 'passed', 'examples': 8, 'python': sys.version.split()[0], 'numpy': np.__version__, 'pandas': pd.__version__,
          'matplotlib': matplotlib.__version__, 'raw_rows': len(raw), 'clean_rows': len(clean),
          'city_totals': totals.to_dict(), 'daily_totals': daily.tolist(), 'linear_coefficients': coefficients.tolist(),
          'bar_direction': 'vertical', 'barh_direction': 'horizontal', 'figure': str(figure),
          'scope': 'Only these eight synthetic examples; not all original book code'}
(WORK / 'practice-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
(OUT / '运行结果.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
(OUT / '读书练习_非原文.py').write_text(Path(__file__).read_text(encoding='utf-8'), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
