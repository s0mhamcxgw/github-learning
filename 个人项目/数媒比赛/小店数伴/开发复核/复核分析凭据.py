"""Replay a public-sample analysis JSON. This is a consistency check, not a signature."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine import Dataset

parser=argparse.ArgumentParser(description='用内置公开样例重算导出的分析凭据。')
parser.add_argument('report',type=Path)
args=parser.parse_args()
record=json.loads(args.report.read_text(encoding='utf-8'))
if record.get('schema')!='shop-companion-analysis-v1':
    raise ValueError('这不是“导出分析凭据 JSON”生成的文件。')
expected=record['analysis']
if expected['meta'].get('kind')!='public':
    raise ValueError('此复核脚本仅支持内置公开样例；用户文件需保留原表另行复核。')
metadata=json.loads((ROOT/'data'/'source.json').read_text(encoding='utf-8'))
data_file=ROOT/'data'/'uci-retail-2011-10-11.csv.gz'
digest=hashlib.sha256(data_file.read_bytes()).hexdigest()
if digest!=metadata['derivedSha256'] or digest!=expected['meta']['derivedSha256']:
    raise ValueError('凭据或本地样例的来源摘要不一致。')
options=expected['options']
frame=pd.read_csv(data_file,dtype=str,keep_default_na=False)
dataset=Dataset.create(frame,metadata,date_order=options['dateOrder'],cancelled_prefix=options['cancelledPrefix'])
actual=dataset.analyze(days=options['days'],deduplicate=options['deduplicate'])
checks={name:actual[name]==expected[name] for name in ['summary','previous','deltas','period','products','pairs']}
print(json.dumps({'sourceHashMatched':True,'checks':checks,'result':'matched' if all(checks.values()) else 'mismatch',
                  'note':'检查当前源文件、参数与程序输出的一致性，不是第三方真实性签名或商户效果证明。'},ensure_ascii=False,indent=2))
if not all(checks.values()):raise SystemExit(1)
