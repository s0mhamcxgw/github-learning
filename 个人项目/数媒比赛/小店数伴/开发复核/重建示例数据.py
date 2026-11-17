"""Rebuild the exact published subset from the attributed UCI source archive.

Usage: python 开发复核/重建示例数据.py <downloaded-online-retail.zip>
The script makes no network requests and replaces only its derived CSV after verification.
"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import argparse
import hashlib
import json
import tempfile
import pandas as pd

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description='从官方Online Retail压缩包复现内置示例。')
parser.add_argument('source_zip', type=Path)
args = parser.parse_args()
metadata_path = root / 'data' / 'source.json'
metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
digest = hashlib.sha256(args.source_zip.read_bytes()).hexdigest()
if digest != metadata['sourceZipSha256']:
    raise ValueError('输入压缩包与已记录的官方源文件摘要不一致，请核对版本和来源。')
with ZipFile(args.source_zip) as archive:
    raw = pd.read_excel(BytesIO(archive.read('Online Retail.xlsx')), engine='openpyxl')
raw['SourceRow'] = raw.index + 2
raw['InvoiceDate'] = pd.to_datetime(raw['InvoiceDate'])
subset = raw.loc[(raw['InvoiceDate'] >= '2011-10-01') & (raw['InvoiceDate'] < '2011-12-01'),
                 ['InvoiceNo','StockCode','Description','Quantity','InvoiceDate','UnitPrice','SourceRow']].copy()
subset['InvoiceDate'] = subset['InvoiceDate'].dt.strftime('%Y-%m-%d %H:%M:%S')
out = root / 'data' / 'uci-retail-2011-10-11.csv.gz'
with tempfile.TemporaryDirectory(prefix='rebuild-',dir=root/'data') as temp:
    candidate = Path(temp) / out.name
    subset.to_csv(candidate,index=False,encoding='utf-8',compression={'method':'gzip','mtime':0})
    rebuilt_hash = hashlib.sha256(candidate.read_bytes()).hexdigest()
    assert rebuilt_hash == metadata['derivedSha256'], '复现文件摘要不匹配；原示例未替换，请检查运行环境。'
    out.write_bytes(candidate.read_bytes())
print(json.dumps({'rows':len(subset),'sha256':rebuilt_hash,'result':'matched'},ensure_ascii=False))
