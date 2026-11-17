"""Local application server. Uploaded tables stay in process memory."""
from __future__ import annotations

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from io import BytesIO
from threading import Lock
import argparse
import hashlib
import json
import mimetypes
import secrets
import sys
import time
import webbrowser
from datetime import datetime
import pandas as pd

from engine import Dataset, guess_mapping

ROOT = Path(__file__).resolve().parent
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else ROOT
EXPORT_DIR = APP_DIR / 'exports'
DATASETS = {}
UPLOADS = {}
CACHE = {}
LOCK = Lock()
MAX_BYTES = 35 * 1024 * 1024


def load_sample():
    metadata = json.loads((ROOT / 'data' / 'source.json').read_text(encoding='utf-8'))
    raw = pd.read_csv(ROOT / 'data' / 'uci-retail-2011-10-11.csv.gz', dtype=str, keep_default_na=False)
    dataset = Dataset.create(raw, metadata, cancelled_prefix=True)
    DATASETS[metadata['id']] = dataset
    return metadata['id']


class Handler(BaseHTTPRequestHandler):
    server_version = 'ShopCompanion/1.0'

    def log_message(self, fmt, *args):
        if args and str(args[0]).startswith('POST'):
            return
        super().log_message(fmt, *args)

    def send(self, status, content, content_type='application/json; charset=utf-8'):
        if isinstance(content, (dict, list)):
            content = json.dumps(content, ensure_ascii=False, allow_nan=False).encode('utf-8')
        elif isinstance(content, str):
            content = content.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        try:
            if parsed.path == '/api/health':
                return self.send(200, {'ready': True, 'defaultDataset': self.server.sample_id, 'version': '1.0.0'})
            if parsed.path == '/api/analyze':
                dataset_id = query.get('dataset', [self.server.sample_id])[0]
                days = int(query.get('days', ['30'])[0])
                dedup = query.get('deduplicate', ['true'])[0] == 'true'
                key = (dataset_id, days, dedup)
                with LOCK:
                    if dataset_id not in DATASETS:
                        return self.send(404, {'error': '该导入数据已随服务重启清除，请重新导入或使用公开示例。'})
                    if key not in CACHE:
                        CACHE[key] = DATASETS[dataset_id].analyze(days, dedup)
                    result = CACHE[key]
                return self.send(200, result)
            if parsed.path == '/api/template':
                template = '订单号,日期,商品,数量,单价\nDEMO001,2026-10-01,示例商品A,2,10\nDEMO001,2026-10-01,示例商品B,1,20\nDEMO002,2026-10-02,示例商品A,1,10\n'
                return self.send(200, '\ufeff' + template, 'text/csv; charset=utf-8')
            if parsed.path.startswith('/api/'):
                return self.send(404, {'error': '接口不存在。'})
            if parsed.path.startswith('/exports/'):
                report = (EXPORT_DIR / parsed.path.removeprefix('/exports/')).resolve()
                if report.is_relative_to(EXPORT_DIR.resolve()) and report.is_file() and report.suffix in {'.html', '.json'}:
                    return self.send(200, report.read_bytes(), 'text/html; charset=utf-8' if report.suffix == '.html' else 'application/json; charset=utf-8')
                return self.send(404, '报告不存在。', 'text/plain; charset=utf-8')
            request_path = parsed.path.lstrip('/') or 'index.html'
            path = (ROOT / 'web' / request_path).resolve()
            if not path.is_relative_to((ROOT / 'web').resolve()) or not path.is_file():
                return self.send(404, '页面不存在。', 'text/plain; charset=utf-8')
            mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
            if path.suffix in {'.js', '.css', '.html', '.svg'}:
                mime += '; charset=utf-8'
            return self.send(200, path.read_bytes(), mime)
        except (ValueError, KeyError) as exc:
            return self.send(400, {'error': str(exc)})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as exc:
            print('Analysis error:', type(exc).__name__, str(exc), file=sys.stderr)
            return self.send(500, {'error': '分析未完成，请检查文件与字段，或重新载入公开示例。'})

    def do_POST(self):
        parsed = urlparse(self.path)
        origin = self.headers.get('Origin')
        allowed = {f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'}
        if origin and origin not in allowed:
            return self.send(403, {'error': '仅接受本机页面的导入请求。'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length <= 0 or length > MAX_BYTES:
                return self.send(413, {'error': '请选择非空文件，大小不超过35MB。'})
            body = self.rfile.read(length)
            if parsed.path == '/api/export':
                payload = json.loads(body)
                extension = payload.get('extension')
                content = payload.get('content')
                if extension not in {'html', 'json'} or not isinstance(content, str) or len(content) > 2_000_000:
                    raise ValueError('仅支持不超过2MB的HTML分析报告或JSON核查记录。')
                if extension == 'json':
                    json.loads(content)
                target_dir = EXPORT_DIR
                target_dir.mkdir(exist_ok=True)
                filename = f'report_{datetime.now():%Y%m%d_%H%M%S}_{secrets.token_hex(3)}.{extension}'
                target = target_dir / filename
                target.write_text(content, encoding='utf-8')
                return self.send(200, {'path': str(target), 'url': '/exports/' + filename})
            if parsed.path == '/api/preview':
                name = parse_qs(parsed.query).get('name', ['orders.csv'])[0]
                suffix = Path(name).suffix.lower()
                if suffix == '.xlsx':
                    raw = pd.read_excel(BytesIO(body), dtype=str, keep_default_na=False, engine='openpyxl')
                elif suffix == '.csv':
                    raw = None
                    for encoding in ['utf-8-sig', 'gb18030']:
                        try:
                            raw = pd.read_csv(BytesIO(body), dtype=str, keep_default_na=False, encoding=encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    if raw is None:
                        raise ValueError('文件编码无法识别，请另存为UTF-8 CSV。')
                else:
                    raise ValueError('支持.csv或.xlsx，请先将旧版.xls另存为.xlsx。')
                if raw.empty or len(raw) > 600000 or len(raw.columns) > 100:
                    raise ValueError('文件需包含1—600000行数据，且不超过100列。')
                token = secrets.token_urlsafe(18)
                with LOCK:
                    while len(UPLOADS) >= 3:
                        UPLOADS.pop(next(iter(UPLOADS)))
                    UPLOADS[token] = {'raw': raw, 'name': Path(name).name, 'hash': hashlib.sha256(body).hexdigest()}
                return self.send(200, {'token': token, 'columns': list(raw.columns), 'rows': len(raw),
                                       'preview': raw.head(3).fillna('').to_dict(orient='records'),
                                       'mapping': guess_mapping(raw.columns)})
            if parsed.path == '/api/import':
                payload = json.loads(body)
                token = payload.get('token')
                with LOCK:
                    upload = UPLOADS.get(token)
                    if not upload:
                        raise ValueError('文件预览已失效，请重新选择文件。')
                    currency = payload.get('currency', 'CNY')
                    symbols = {'CNY': '¥', 'GBP': '£', 'USD': '$', 'EUR': '€'}
                    if currency not in symbols:
                        raise ValueError('请选择支持的币种；本工具不进行汇率换算。')
                    dataset_id = 'local-' + upload['hash'][:12] + '-' + secrets.token_hex(3)
                    metadata = {'id': dataset_id, 'name': upload['name'], 'kind': 'user', 'source': '本机导入文件',
                                'sourceUrl': None, 'currency': currency, 'currencySymbol': symbols[currency],
                                'license': '由导入者核实使用权限', 'creator': '', 'citation': '', 'selection': '由用户选择字段和日期口径；原文件不被修改。',
                                'limitations': '这是本机导入数据，来源及采集完整性未由本工具外部核验；分析不代表已发生的经营改善。',
                                'derivedSha256': upload['hash'], 'dateOrder': payload.get('dateOrder', 'iso')}
                    dataset = Dataset.create(upload['raw'], metadata, payload.get('mapping'),
                                             date_order=payload.get('dateOrder', 'iso'),
                                             cancelled_prefix=bool(payload.get('cancelledPrefix', False)))
                    if len(DATASETS) > 5:
                        for old_id in list(DATASETS):
                            if old_id != self.server.sample_id:
                                DATASETS.pop(old_id)
                                for cache_key in list(CACHE):
                                    if cache_key[0] == old_id:
                                        CACHE.pop(cache_key)
                                break
                    DATASETS[dataset_id] = dataset
                    UPLOADS.pop(token, None)
                return self.send(200, {'dataset': dataset_id})
            return self.send(404, {'error': '接口不存在。'})
        except (ValueError, KeyError, pd.errors.ParserError) as exc:
            return self.send(400, {'error': str(exc)})
        except Exception as exc:
            print('Import error:', type(exc).__name__, str(exc), file=sys.stderr)
            return self.send(400, {'error': '无法读取文件，请确认文件未加密、格式完整、列名及数据类型正确。'})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--open', action='store_true')
    parser.add_argument('--no-open', action='store_true')
    args = parser.parse_args()
    sample_id = load_sample()
    server = None
    for port in range(args.port, min(args.port + 5, 65536)):
        try:
            server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
            break
        except OSError:
            continue
    if server is None:
        raise OSError('未能启动本机端口，请关闭已有作品窗口或用--port指定其他端口。')
    server.sample_id = sample_id
    print(f'小店数伴已启动：http://127.0.0.1:{server.server_port}', flush=True)
    print('关闭此窗口即可停止服务；导入文件仅保存在本机进程内存中。', flush=True)
    if (args.open or getattr(sys, 'frozen', False)) and not args.no_open:
        webbrowser.open(f'http://127.0.0.1:{server.server_port}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
