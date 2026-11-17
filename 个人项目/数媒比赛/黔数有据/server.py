"""黔数有据: local data workspace. Python standard library only."""
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from contextlib import contextmanager
import sqlite3, json, csv, io, hashlib, secrets, mimetypes, argparse, re, threading

ROOT=Path(__file__).resolve().parent
SEED=json.loads((ROOT/'data'/'seed.json').read_text(encoding='utf-8'))
METRICS={m['id']:m for m in SEED['metrics']}
TOKEN=secrets.token_urlsafe(32)
LOCK=threading.RLock()
DB=ROOT/'data'/'workspace.sqlite3'
def now():return datetime.now(timezone.utc).isoformat()
def dump(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def digest(x):return hashlib.sha256(dump(x).encode()).hexdigest()
def dec(x):
 try:r=Decimal(str(x))
 except (InvalidOperation,ValueError):raise ValueError('数值格式无效')
 if not r.is_finite() or abs(r)>Decimal('1e16'):raise ValueError('数值必须有限且绝对值不超过10^16')
 return r
def ds(x):return format(x,'f')
def text(x,name,maxlen=300,required=True):
 if not isinstance(x,str) or len(x)>maxlen or (required and not x.strip()):raise ValueError(f'{name}须为1—{maxlen}字文本')
 return x.strip()
@contextmanager
def connect():
 con=sqlite3.connect(DB,timeout=15);con.row_factory=sqlite3.Row;con.execute('PRAGMA foreign_keys=ON')
 try:yield con
 finally:con.close()
def init():
 DB.parent.mkdir(parents=True,exist_ok=True)
 with connect() as c:
  c.executescript('''PRAGMA journal_mode=WAL;
   CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY,payload TEXT NOT NULL);
   CREATE TABLE IF NOT EXISTS observations(id TEXT PRIMARY KEY,source_id TEXT NOT NULL REFERENCES sources(id),payload TEXT NOT NULL,fingerprint TEXT NOT NULL UNIQUE,batch_id TEXT);
   CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY,created TEXT NOT NULL,state TEXT NOT NULL,payload TEXT NOT NULL);
   CREATE TABLE IF NOT EXISTS reports(id TEXT PRIMARY KEY,created TEXT NOT NULL,payload TEXT NOT NULL);
   CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,created TEXT NOT NULL,action TEXT NOT NULL,detail TEXT NOT NULL);
  ''')
  for s in SEED['sources']:c.execute('INSERT OR IGNORE INTO sources VALUES(?,?)',(s['id'],dump(s)))
  for r in SEED['observations']:c.execute('INSERT OR IGNORE INTO observations VALUES(?,?,?,?,?)',(r['id'],r['source_id'],dump(r),row_fingerprint(r),None))
  c.commit()
def rows_from(c,table):return [json.loads(r[0]) for r in c.execute(f'SELECT payload FROM {table}')] # table names are internal constants.
def row_fingerprint(r):return digest({k:r[k] for k in ['source_id','region','year','period','metric','value','unit','basis','scope']})
def note(c,action,detail):c.execute('INSERT INTO audit(created,action,detail) VALUES(?,?,?)',(now(),action,dump(detail)))
def canonical(row):
 r=dict(row);metric=METRICS[r['metric']];v=dec(r['value']);u=r['unit'];target=metric['unit']
 if u not in metric['allowed_units']:raise ValueError(f'指标{metric["label"]}不支持单位{u}')
 if u=='亿美元':return {**r,'canonical_value':ds(v),'canonical_unit':'亿美元','conversion':'保留原币种；未取得汇率，不转换为人民币'}
 factors={('万元','亿元'):Decimal('.0001'),('万亿元','亿元'):Decimal('10000'),('万元','元'):Decimal('10000'),('人','万人'):Decimal('.0001')}
 factor=Decimal(1) if u==target else factors.get((u,target))
 if factor is None:raise ValueError('单位转换不明确')
 return {**r,'canonical_value':ds(v*factor),'canonical_unit':target,'conversion':'无需换算' if u==target else f'{u} × {factor} → {target}'}
def key(r):return tuple(r[k] for k in ['region','year','period','metric','basis','scope'])
def effective(records,sources):
 by={s['id']:s for s in sources};groups={}
 for r in records:groups.setdefault(key(r),[]).append(r)
 result=[]
 for group in groups.values():
  # Latest refers only to observed publication date, never an authoritative claim.
  group.sort(key=lambda r:(by[r['source_id']]['published'],r['source_id'],r['id']),reverse=True)
  result.append(group[0])
 return result
def revisions(records,sources):
 by={s['id']:s for s in sources};groups={}
 for r in records:groups.setdefault(key(r),[]).append(r)
 result=[]
 for group in groups.values():
  if len(group)<2:continue
  group.sort(key=lambda r:(by[r['source_id']]['published'],r['source_id'],r['id']))
  normalized=[canonical(r) for r in group]
  units={r['canonical_unit'] for r in normalized};values={r['canonical_value'] for r in normalized}
  if len(values)>1 or len(units)>1:result.append({'key':list(key(group[0])),'versions':normalized,'sameUnit':len(units)==1,'difference':ds(dec(normalized[-1]['canonical_value'])-dec(normalized[0]['canonical_value'])) if len(units)==1 else None,'note':'不同发布版本保留并列；存在修订不等于某个来源错误。'})
 return result
def quality(records,sources):
 issues=[];by={s['id']:s for s in sources}
 def add(code,severity,message,ids):issues.append({'id':digest([code,ids])[:16],'code':code,'severity':severity,'message':message,'observation_ids':ids})
 for r in records:
  if not by[r['source_id']].get('verified'):add('UNVERIFIED_SOURCE','review','用户登记来源，尚未核实原站与数字语义',[r['id']])
  if r['unit']=='亿美元':add('CURRENCY_GUARD','info','保留美元计价；跨币种比较需取得合适汇率及时间口径',[r['id']])
  if r['period']!='全年':add('PERIOD_GUARD','info','季度观察值单独保存，不与全年总量直接作增长比较',[r['id']])
 for revision in revisions(records,sources):add('VERSION_DIFFERENCE','review',f'{revision["key"][0]} {revision["key"][1]}年 {METRICS[revision["key"][3]]["label"]}有不同发布值，比较前明确版本',[r['id'] for r in revision['versions']])
 groups={}
 for r in records:groups.setdefault((r['source_id'],r['region'],r['year'],r['period'],r['basis'],r['scope']),{})[r['metric']]=r
 for group in groups.values():
  for total,parts in [('gdp',['primary','secondary','tertiary']),('trade',['exports','imports'])]:
   if total not in group or not all(x in group for x in parts):continue
   rs=[canonical(group[x]) for x in [total]+parts]
   if len({r['canonical_unit'] for r in rs})!=1:continue
   diff=dec(rs[0]['canonical_value'])-sum((dec(r['canonical_value']) for r in rs[1:]),Decimal(0))
   # Source rounding tolerance: one half-unit in the last displayed decimal per term.
   tolerance=sum((Decimal(10)**dec(r['value']).as_tuple().exponent/2 for r in rs),Decimal(0))
   if abs(diff)>tolerance:add('SUM_INCONSISTENCY','review',f'{group[total]["region"]} {total}与分项合计差{ds(diff)}，超出原表显示精度修约容差{ds(tolerance)}',[r['id'] for r in rs])
 return issues
def validate_row(raw,source_id,line):
 r={};r['id']='u'+secrets.token_hex(6);r['source_id']=source_id
 r['region']=text(raw.get('region'),'地区',30)
 try:r['year']=int(str(raw.get('year','')))
 except ValueError:raise ValueError('年份须为整数')
 if r['year']<1950 or r['year']>2100:raise ValueError('年份应在1950—2100之间')
 r['period']=text(raw.get('period'),'期间',10)
 if r['period'] not in ['全年','一季度','上半年','前三季度','四季度']:raise ValueError('期间须选择全年、一季度、上半年、前三季度或四季度')
 r['metric']=text(raw.get('metric'),'指标代码',40)
 if r['metric'] not in METRICS:raise ValueError('指标代码未在指标字典中定义')
 r['value']=ds(dec(raw.get('value','')))
 if r['metric']!='gdp_growth' and dec(r['value'])<0:raise ValueError('该指标不能为负值')
 r['unit']=text(raw.get('unit'),'单位',10);r['basis']=text(raw.get('basis'),'价格/计算口径',20);r['scope']=text(raw.get('scope'),'人群范围',20)
 if r['basis']!=METRICS[r['metric']]['basis']:raise ValueError('价格/计算口径与指标字典不一致')
 if r['scope'] not in ['全体','城镇','农村']:raise ValueError('范围须为全体、城镇或农村')
 if r['metric'] not in ['income','spending'] and r['scope']!='全体':raise ValueError('该指标当前只支持全体范围')
 if r['metric']=='urbanization' and not 0<=dec(r['value'])<=100:raise ValueError('城镇化率须在0—100%之间')
 r.update(anchor='用户导入表第'+str(line)+'行',source_line=line,extraction='用户CSV映射导入，来源与语义待审核',seed=False)
 canonical(r);return r
FIELDS=['region','year','period','metric','value','unit','basis','scope']
def preview(payload):
 raw=text(payload.get('csv'),'CSV内容',500000);mapping=payload.get('mapping');sid=text(payload.get('source_id'),'来源编号',80)
 if not isinstance(mapping,dict) or set(mapping)!=set(FIELDS) or any(not isinstance(v,str) for v in mapping.values()):raise ValueError('需要完整的八列字段映射')
 with connect() as c:
  if not c.execute('SELECT 1 FROM sources WHERE id=?',(sid,)).fetchone():raise ValueError('来源不存在，请先登记')
  reader=csv.DictReader(io.StringIO(raw.lstrip('\ufeff')))
  if not reader.fieldnames or len(set(reader.fieldnames))!=len(reader.fieldnames):raise ValueError('CSV表头缺失或重复')
  if any(v not in reader.fieldnames for v in mapping.values()):raise ValueError('映射指向了不存在的表头')
  existing={r[0] for r in c.execute('SELECT fingerprint FROM observations')};seen=set();records=[];errors=[];duplicates=[];conversions=[]
  for i,row in enumerate(reader,2):
   if i>2001:raise ValueError('一次最多导入2000行')
   if None in row:errors.append({'line':i,'message':'数据列数超过表头'});continue
   try:
    r=validate_row({f:row[mapping[f]] for f in FIELDS},sid,i);fingerprint=row_fingerprint(r)
    if fingerprint in seen or fingerprint in existing:duplicates.append({'line':i,'message':'同源同口径同值重复，本批跳过'});continue
    seen.add(fingerprint);records.append(r);can=canonical(r)
    if can['conversion']!='无需换算':conversions.append({'line':i,'rule':can['conversion'],'result':can['canonical_value']+' '+can['canonical_unit']})
   except (ValueError,TypeError,KeyError) as e:errors.append({'line':i,'message':str(e)})
  if not records and not errors:errors.append({'line':1,'message':'没有可新增记录，可能全部重复或文件为空'})
  batch={'id':'batch-'+secrets.token_hex(6),'created':now(),'state':'preview','source_id':sid,'records':records,'errors':errors,'duplicates':duplicates,'conversions':conversions,'mapping':mapping,'csv_sha256':hashlib.sha256(raw.encode()).hexdigest()}
  c.execute('INSERT INTO batches VALUES(?,?,?,?)',(batch['id'],batch['created'],'preview',dump(batch)));note(c,'预览导入',{'batch':batch['id'],'valid':len(records),'errors':len(errors)});c.commit()
  return batch
def commit(batch_id):
 with LOCK,connect() as c:
  c.execute('BEGIN IMMEDIATE');row=c.execute('SELECT state,payload FROM batches WHERE id=?',(batch_id,)).fetchone()
  if not row:raise ValueError('导入预览不存在')
  if row['state']!='preview':raise ValueError('该批次已提交或撤销，不能重复提交')
  b=json.loads(row['payload'])
  if b['errors'] or not b['records']:raise ValueError('存在错误或无有效记录，不能入库；请修改CSV后重新预览')
  inserted=0
  for r in b['records']:
   inserted+=c.execute('INSERT OR IGNORE INTO observations VALUES(?,?,?,?,?)',(r['id'],r['source_id'],dump(r),row_fingerprint(r),b['id'])).rowcount
  b['state']='committed';b['inserted']=inserted;c.execute('UPDATE batches SET state=?,payload=? WHERE id=?',('committed',dump(b),b['id']));note(c,'提交数据批次',{'batch':b['id'],'inserted':inserted});c.commit();return b
def undo(batch_id):
 with LOCK,connect() as c:
  c.execute('BEGIN IMMEDIATE');row=c.execute('SELECT state,payload FROM batches WHERE id=?',(batch_id,)).fetchone()
  if not row or row['state']!='committed':raise ValueError('只能撤销已提交的用户导入批次')
  b=json.loads(row['payload']);deleted=c.execute('DELETE FROM observations WHERE batch_id=?',(batch_id,)).rowcount;b['state']='undone';c.execute('UPDATE batches SET state=?,payload=? WHERE id=?',('undone',dump(b),batch_id));note(c,'撤销用户批次',{'batch':batch_id,'deleted':deleted});c.commit();return {'deleted':deleted,'batch':batch_id}
def compare(payload,records,sources):
 ids={r['id']:r for r in records};mode=payload.get('mode','difference');a=ids.get(payload.get('left'));b=ids.get(payload.get('right'))
 if not a or not b:raise ValueError('请选择两个存在的观察值')
 a=canonical(a);b=canonical(b);fail=[];warnings=[]
 def same(field,message):
  if a[field]!=b[field]:fail.append(message)
 if mode in ['difference','growth']:
  for f,m in [('region','地区不同'),('metric','指标不同'),('period','统计期间不同'),('scope','人群范围不同'),('basis','价格/计算口径不同'),('canonical_unit','单位或币种无法直接比较')]:same(f,m)
  if mode=='growth' and a['year']+1!=b['year']:fail.append('增长比较要求左侧为上年、右侧为相邻本年；跨缺失年份不能当同比')
  if mode=='growth' and a['metric'] in ['gdp_growth','urbanization']:fail.append('该字段为比率，使用差值（百分点），不再计算“增速的增长率”')
  if a['year']==b['year'] and a['source_id']!=b['source_id']:warnings.append('同一年度的不同发布版本：结果是版本差额，不是年度增长')
 elif mode=='percapita':
  for f,m in [('region','地区不同'),('year','年份不同'),('period','统计期间不同'),('scope','人群范围不同')]:same(f,m)
  if a['metric']!='gdp':fail.append('左侧须为地区生产总值')
  if b['metric']!='population_avg':fail.append('右侧须为年平均常住人口；年末人口不能替代官方人均GDP的平均人口分母')
  if a['canonical_unit']!='亿元' or b['canonical_unit']!='万人':fail.append('该人均计算目前仅支持人民币亿元和万人')
 elif mode=='share':
  for f,m in [('year','年份不同'),('period','统计期间不同'),('metric','指标不同'),('basis','价格/计算口径不同'),('scope','人群范围不同'),('canonical_unit','币种或单位不同')]:same(f,m)
  parent={'贵阳市':['贵州省','全国'],'贵州省':['全国']}
  if b['region'] not in parent.get(a['region'],[]):fail.append('右侧不是字典中已知的上级区域，不能自动解释为区域占比')
  warnings.append('区域占比受两地核算版本与统计覆盖影响；不将地区之和强制等同全国值')
 else:raise ValueError('计算模式无效')
 av=dec(a['canonical_value']);bv=dec(b['canonical_value'])
 if (mode in ['growth'] and av==0) or (mode in ['percapita','share'] and bv==0):fail.append('分母不能为0')
 value=None;unit='';formula=''
 if not fail:
  if mode=='difference':value=bv-av;unit='个百分点' if a['canonical_unit']=='%' else a['canonical_unit'];formula=f'{ds(bv)} − {ds(av)}'
  elif mode=='growth':value=(bv/av-1)*100;unit='%';formula=f'({ds(bv)} ÷ {ds(av)} − 1) × 100';warnings.append('由现价总量算出的变化率不是官方不变价GDP增速' if a['metric'] in ['gdp','primary','secondary','tertiary'] else '变化率按所选发布版本和口径计算，不自动继承官方增速定义')
  elif mode=='percapita':value=av/bv*10000;unit='元/人';formula=f'{ds(av)} ÷ {ds(bv)} × 10000';warnings.append('基于已公布且经过修约的总量和平均人口计算，末位可能与官方人均值不同')
  else:value=av/bv*100;unit='%';formula=f'{ds(av)} ÷ {ds(bv)} × 100'
 source_ids={a['source_id'],b['source_id']};refs=[s for s in sources if s['id'] in source_ids]
 latest_ids={r['id'] for r in effective(records,sources)}
 if a['id'] not in latest_ids or b['id'] not in latest_ids:warnings.append('选取了库内有后续发布版本的历史值，请明确保留该版本的理由')
 return {'mode':mode,'allowed':not fail,'blockers':fail,'warnings':warnings,'left':a,'right':b,'value':ds(value) if value is not None else None,'unit':unit,'formula':formula,'sources':refs,'calculated_at':now(),'input_sha256':digest([a,b,mode])}
def bootstrap():
 with connect() as c:
  sources=rows_from(c,'sources');records=rows_from(c,'observations');reports=rows_from(c,'reports');batches=rows_from(c,'batches')
  latest=effective(records,sources);checks=quality(records,sources)
  return {'version':'1.0.0','token':TOKEN,'metrics':SEED['metrics'],'sources':sources,'observations':[canonical(r) for r in records],'revisions':revisions(records,sources),'quality':checks,'reports':[{'id':r['id'],'title':r['title'],'created':r['created'],'comparisons':len(r['comparisons'])} for r in reports],'batches':[{'id':b['id'],'state':b['state'],'created':b['created'],'rows':len(b['records']),'errors':len(b['errors']),'inserted':b.get('inserted',0)} for b in batches],'audit':[dict(r) for r in c.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 40')],'summary':{'observations':len(records),'effective':len(latest),'sources':len(sources),'metrics':len(METRICS),'revisions':len(revisions(records,sources)),'reports':len(reports),'database':'SQLite／本机持久化'},'notes':SEED['notes']}
def create_report(payload):
 title=text(payload.get('title'),'报告标题',100);memo=text(payload.get('note',''),'报告备注',2000,False);items=payload.get('comparisons')
 if not isinstance(items,list) or not 1<=len(items)<=12:raise ValueError('报告需要1—12项比较')
 with connect() as c:
  records=rows_from(c,'observations');sources=rows_from(c,'sources');results=[compare(x,records,sources) for x in items]
  report={'id':'report-'+secrets.token_hex(6),'title':title,'note':memo,'created':now(),'comparisons':results,'version':'1.0.0','limitation':'来源登记与自动规则不能替代人工审核；结果为所选发布版本下的描述性计算。'}
  report['sha256']=digest(report);c.execute('INSERT INTO reports VALUES(?,?,?)',(report['id'],report['created'],dump(report)));note(c,'冻结分析报告',{'report':report['id'],'comparisons':len(results)});c.commit();return report
def report_md(r):
 out=[f'# {r["title"]}',f'\n生成时间：{r["created"]}\n输入与结果快照SHA-256：{r["sha256"]}',r['note']]
 for i,x in enumerate(r['comparisons'],1):
  out+=[f'\n## {i}. {x["mode"]}',f'左：{x["left"]["region"]} {x["left"]["year"]} {x["left"]["period"]} {METRICS[x["left"]["metric"]]["label"]} {x["left"]["value"]}{x["left"]["unit"]}',f'右：{x["right"]["region"]} {x["right"]["year"]} {x["right"]["period"]} {METRICS[x["right"]["metric"]]["label"]} {x["right"]["value"]}{x["right"]["unit"]}',f'计算：{x["formula"]} = {x["value"] or "未计算"} {x["unit"]}']
  out+=['阻止原因：'+s for s in x['blockers']];out+=['解释限制：'+s for s in x['warnings']]
  out +=[f'来源：{s["title"]}（{s["published"]}，{s["status"]}）\n{s["url"]}' for s in x['sources']]
 out+=['\n'+r['limitation'],'\n快照保留导出时的原始输入，后续撤销导入批次不改写已冻结报告。']
 return '\n\n'.join(out)

class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def send(self,data,status=200,mime='application/json; charset=utf-8'):
  body=dump(data).encode() if mime.startswith('application/json') else data.encode('utf-8') if isinstance(data,str) else data
  self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(body)));self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
 def valid_host(self):return self.headers.get('Host','').split(':')[0] in ['127.0.0.1','localhost']
 def do_GET(self):
  if not self.valid_host():return self.send({'error':'仅允许本机访问'},403)
  parsed=urlparse(self.path);p=parsed.path;q=parse_qs(parsed.query)
  try:
   if p=='/api/bootstrap':return self.send(bootstrap())
   if p=='/api/export':
    data=bootstrap();data.pop('token');return self.send(data)
   if p.startswith('/api/reports/'):
    rid=p.rsplit('/',1)[1]
    with connect() as c:row=c.execute('SELECT payload FROM reports WHERE id=?',(rid,)).fetchone()
    if not row:return self.send({'error':'报告不存在'},404)
    r=json.loads(row[0]);return self.send(report_md(r),mime='text/markdown; charset=utf-8') if q.get('format')==['md'] else self.send(r)
   file=(ROOT/'app'/('index.html' if p=='/' else p.lstrip('/'))).resolve();app=(ROOT/'app').resolve()
   if not file.is_relative_to(app) or not file.is_file():return self.send({'error':'文件不存在'},404)
   return self.send(file.read_bytes(),mime=mimetypes.guess_type(file.name)[0] or 'application/octet-stream')
  except (ValueError,KeyError,TypeError) as e:return self.send({'error':str(e)},400)
 def do_POST(self):
  if not self.valid_host():return self.send({'error':'仅允许本机访问'},403)
  origin=self.headers.get('Origin')
  if origin and origin not in [f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}']:return self.send({'error':'不允许跨站写入'},403)
  if self.headers.get('X-Workspace-Token')!=TOKEN:return self.send({'error':'本机写入凭据不匹配，请刷新页面'},403)
  try:
   length=int(self.headers.get('Content-Length',0))
   if length<=0 or length>1500000:raise ValueError('请求体须为1—1500000字节')
   data=json.loads(self.rfile.read(length));p=urlparse(self.path).path
   if not isinstance(data,dict):raise ValueError('请求需要JSON对象')
   if p=='/api/preview':return self.send(preview(data))
   if p=='/api/commit':return self.send(commit(text(data.get('batch_id'),'批次编号',80)))
   if p=='/api/undo':return self.send(undo(text(data.get('batch_id'),'批次编号',80)))
   if p=='/api/compare':
    with connect() as c:return self.send(compare(data,rows_from(c,'observations'),rows_from(c,'sources')))
   if p=='/api/reports':return self.send(create_report(data))
   if p=='/api/sources':
    s={'id':'source-'+secrets.token_hex(6),'title':text(data.get('title'),'来源标题',120),'publisher':text(data.get('publisher'),'发布者',80),'url':text(data.get('url'),'来源URL',600),'published':text(data.get('published'),'发布日期',10),'status':text(data.get('status','用户登记'),'发布状态',30),'verified':False,'hosting':'用户登记，未联网核验','checked_at':now()[:10],'sha256':'未获取原页快照','note':'由使用者登记；程序未证明链接内容或数据真实性。'}
    if urlparse(s['url']).scheme not in ['http','https'] or not urlparse(s['url']).hostname:raise ValueError('来源链接须为完整HTTP/HTTPS地址')
    datetime.strptime(s['published'],'%Y-%m-%d')
    with connect() as c:c.execute('INSERT INTO sources VALUES(?,?)',(s['id'],dump(s)));note(c,'登记待审来源',{'source':s['id']});c.commit()
    return self.send(s)
   return self.send({'error':'接口不存在'},404)
  except (ValueError,KeyError,TypeError,json.JSONDecodeError,sqlite3.IntegrityError) as e:return self.send({'error':str(e)},400)

def main():
 global DB
 parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8796);parser.add_argument('--db',type=Path);args=parser.parse_args()
 if args.db:DB=args.db.resolve()
 init();server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
 print(f'黔数有据：http://127.0.0.1:{server.server_port} （仅本机）',flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
if __name__=='__main__':main()
