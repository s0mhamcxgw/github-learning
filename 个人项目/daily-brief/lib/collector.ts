import { SOURCES, SEEDS, TOPICS, type Document, type Source } from "./catalog";

export function plain(html: string) {
 return html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi," ").replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi," ")
 .replace(/<[^>]*>/g," ").replace(/&nbsp;|&#160;/g," ").replace(/&amp;/g,"&").replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&lt;/g,"<").replace(/&gt;/g,">").replace(/\s+/g," ").trim();
}
export function canonical(raw: string) {
 const url=new URL(raw); url.hash=""; for(const k of [...url.searchParams.keys()]) if(/^utm_|^from$/.test(k)) url.searchParams.delete(k);
 url.pathname=url.pathname.replace(/_mobile\.html$/,"_pc.html");return url.href;
}
export function topicsFor(text: string) {
 const rules=[/数据要素|数据流通|数据产权|公共数据|数据基础制度/,/数据交易|交易所|交易场所|数据商|数据流通服务机构/,/数据工厂|数据赋能工场|数据标注|数据生产/,/数据质量|质量评估|质量评测|质量评价|数据治理/,/高质量数据集|数据集建设|数据集质量/,/可信数据空间|数据空间/];
 return TOPICS.filter((_,i)=>rules[i].test(text));
}
export function kindFor(title: string) {
 if(/解读|答记者问|图读懂/.test(title)) return "政策解读";
 if(/征求|需求|征集|试点|发布.*报告|报告.*发布|关于发布.*通知/.test(title)) return "行业动态";
 if(/条例|中华人民共和国.*法|管理条例/.test(title)) return "法律法规";
 if(/技术架构|技术文件/.test(title)) return "技术文件";
 if(/白皮书|研究报告|发展报告|建设指南/.test(title)) return "研究报告";
 if(/标准|GB\/T|YD\/T/.test(title)) return "标准";
 if(/通知|意见|办法|方案|行动计划|指引/.test(title)) return "政策文件";
 return "行业动态";
}
export function regionFor(title:string,url:string,source:Source){
 if(/贵州|贵阳|贵安|遵义|毕节|六盘水|安顺|铜仁|黔东南|黔南|黔西南/.test(title)||/\/snyw\//.test(url))return "贵州";
 if(/\/gnyw\//.test(url)||/全国|国家|中共中央|国务院/.test(title))return "全国";
 return source.region;
}
export function publishedDate(html: string): string|null {
 const meta=html.match(/<meta[^>]*(?:name|property)=["'](?:PubDate|pubdate|publishdate|publishDate|date|article:published_time|DC.date.issued)["'][^>]*content=["']([^"']+)/i)?.[1];
 const reverse=html.match(/<meta[^>]*content=["']([^"']+)["'][^>]*(?:name|property)=["'](?:PubDate|publishdate|article:published_time|DC.date.issued)["']/i)?.[1];
 const visible=plain(html).match(/(?:发布时间|发布日期|发布时间：|发布日期：)\s*[:：]?\s*(20\d{2}[年./-]\d{1,2}[月./-]\d{1,2})/)?.[1];
 const v=(meta||reverse||visible||"").match(/(20\d{2})[年./-](\d{1,2})[月./-](\d{1,2})/);
 if(!v)return null;const date=`${v[1]}-${v[2].padStart(2,"0")}-${v[3].padStart(2,"0")}`;
 return Number(v[2])<=12&&Number(v[2])>0&&Number(v[3])<=31&&Number(v[3])>0&&date<=new Date().toISOString().slice(0,10)?date:null;
}
export function linksFor(html: string, source: Source) {
 const result=new Map<string,string>();
 for(const m of html.matchAll(/<a\b([^>]*\bhref\s*=\s*["']([^"']+)["'][^>]*)>([\s\S]*?)<\/a>/gi)) {
  const title=plain(m[1].match(/\btitle\s*=\s*["']([^"']+)["']/i)?.[1]||m[3]);
  if(title.length<10||!topicsFor(title).length)continue;
  try {const url=new URL(m[2].replace(/&amp;/g,"&"),source.url);const host=new URL(source.url).hostname;
   if(url.protocol!=="https:"||url.hostname!==host||!/\.html?$|\.pdf$/i.test(url.pathname)||url.pathname.includes("/list/"))continue;
   result.set(canonical(url.href),title.slice(0,250));
  }catch{}
 }
 return [...result].map(([url,title])=>({url,title}));
}
async function load(url: string) {
 let response=await fetch(url,{signal:AbortSignal.timeout(10000),redirect:"manual",headers:{"User-Agent":"QianData-Research/1.0 (public policy index)","Accept":"text/html"}});
 if(response.status>=300&&response.status<400){
  const next=new URL(response.headers.get("location")||url,url);
  if(next.origin!==new URL(url).origin)throw new Error("源站跳转到其他域名，请人工核对入口");
  response=await fetch(next.href,{signal:AbortSignal.timeout(10000),redirect:"manual",headers:{"Accept":"text/html"}});
 }
 if(!response.ok)throw new Error(`HTTP ${response.status}`);
 const size=Number(response.headers.get("content-length")||0);if(size>2500000)throw new Error("页面过大");
 const buf=await response.arrayBuffer();if(buf.byteLength>2500000)throw new Error("页面过大");
 const charset=response.headers.get("content-type")?.match(/charset=([^;\s]+)/i)?.[1];
 return new TextDecoder(charset&&/gb/i.test(charset)?"gb18030":"utf-8").decode(buf);
}
type DB = D1Database;
export async function readState(db: DB,key: string) {const row=await db.prepare("SELECT value FROM collector_state WHERE key=?").bind(key).first<{value:string}>();return row?JSON.parse(row.value):null;}
async function state(db: DB,key: string,value: unknown) {await db.prepare("INSERT INTO collector_state(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value").bind(key,JSON.stringify(value)).run();}
export async function getDocuments(db: DB) {
 const {results}=await db.prepare("SELECT data FROM documents ORDER BY collected_at DESC LIMIT 2000").all<{data:string}>();
 const merged=new Map(SEEDS.map(d=>[canonical(d.url),d]));
 for(const row of results)try{const d=JSON.parse(row.data);merged.set(canonical(d.url),d);}catch{}
 return [...merged.values()].sort((a,b)=>(b.date||"").localeCompare(a.date||""));
}
export async function refresh(db: DB) {
 const now=new Date().toISOString();
 const lease=await db.prepare("INSERT INTO collector_state(key,value) VALUES ('lock',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value WHERE collector_state.value < ?").bind(String(Date.now()+120000),String(Date.now())).run();
 if(!lease.meta.changes)return {busy:true};
 try {
 const last=await readState(db,"lastRun");
 if(last&&Date.now()-Date.parse(last.finishedAt)<180000)return {cached:true,...last};
 const existing=new Set((await getDocuments(db)).map(d=>canonical(d.url)));
 let added=0;
 const results=[];
 // Source requests are concurrent; article fetches are bounded to stay below Worker request limits.
 const listings=await Promise.allSettled(SOURCES.map(s=>load(s.url)));
 for(let i=0;i<SOURCES.length;i++) {
  const source=SOURCES[i],listing=listings[i];
  if(listing.status==="rejected"){results.push({id:source.id,status:"error",message:String(listing.reason?.message||"访问失败").slice(0,100),found:0,added:0});continue;}
  if(!/<html|<!doctype|<a\b/i.test(listing.value)||/访问验证|人机验证|captcha|安全验证/i.test(plain(listing.value).slice(0,300))){results.push({id:source.id,status:"error",message:"源站返回验证页面，未收录",found:0,added:0});continue;}
  const candidates=linksFor(listing.value,source);
  const pending=candidates.filter(d=>!existing.has(d.url)).slice(0,4);
  let count=0,failed=0;
  const pages=await Promise.allSettled(pending.map(d=>/\.pdf$/i.test(new URL(d.url).pathname)?Promise.reject(new Error("PDF需人工核对")):load(d.url)));
  for(let j=0;j<pending.length;j++) {
   const page=pages[j];if(page.status!=="fulfilled"){failed++;continue;}
   const item=pending[j],html=page.value;
   const h1=html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i)?.[1];
   const title=plain(h1||item.title).slice(0,250);
   const tags=topicsFor(title);if(!tags.length)continue;
   const article=html.match(/<!--\s*TRS_Editor\s*-->([\s\S]*?)<!--\s*\/TRS_Editor\s*-->/i)?.[1]||html.match(/<article[^>]*>([\s\S]*?)<\/article>/i)?.[1]||html.match(/<div[^>]*class=["'][^"']*(?:TRS_Editor|article|content_con)[^"']*["'][^>]*>([\s\S]*?)<\/div>/i)?.[1]||"";
   const desc=html.match(/<meta[^>]*name=["']description["'][^>]*content=["']([^"']*)/i)?.[1];
   const summary=plain(desc||article).slice(0,140);
   const kind=kindFor(title);
   const d:Document={id:item.url,url:item.url,title,source:source.name,region:regionFor(title,item.url,source),kind,status:/征求意见/.test(title)?"征求意见稿 · 待核对":/解读/.test(title)?"解读材料 · 非政策原文":"自动分类 · 待核对",date:publishedDate(html),topics:tags,summary:summary||"已发现相关原文链接，摘要尚未提取，请打开原文核对。",question:"核对发布机构、文号、正文及附件，确认与课题的关联后再引用。",verified:false,collectedAt:now};
   await db.prepare("INSERT OR IGNORE INTO documents(url,data,collected_at) VALUES (?,?,?)").bind(d.url,JSON.stringify(d),now).run();
   existing.add(d.url);count++;added++;
  }
  results.push({id:source.id,status:failed?"partial":"ok",message:failed?`${failed}条详情未获取（含PDF待核对）`:candidates.length?"检查完成":"页面可访问；未解析到相关条目，可能需调整适配",found:candidates.length,added:count});
 }
 const run={startedAt:now,finishedAt:new Date().toISOString(),added,sources:results};
 await state(db,"lastRun",run);return run;
 }finally{await db.prepare("DELETE FROM collector_state WHERE key='lock'").run();}
}
