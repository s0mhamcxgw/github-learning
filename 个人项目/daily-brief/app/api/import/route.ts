import { env } from "cloudflare:workers";
import { KINDS, SEEDS, TOPICS, type Document } from "../../../lib/catalog";
import { canonical, kindFor, topicsFor } from "../../../lib/collector";
export const dynamic="force-dynamic";
const domains:Record<string,string>={"www.nda.gov.cn":"国家数据局","dsj.guizhou.gov.cn":"贵州省大数据发展管理局","www.gzrd.gov.cn":"贵州人大","www.guizhou.gov.cn":"贵州省人民政府","www.caict.ac.cn":"中国信息通信研究院","std.samr.gov.cn":"全国标准信息公共服务平台","openstd.samr.gov.cn":"国家标准全文公开系统","www.tc609.org.cn":"全国数据标准化技术委员会","www.gov.cn":"中国政府网","app.www.gov.cn":"中国政府网","www.ndrc.gov.cn":"国家发展改革委"};
export async function POST(request:Request){
 const origin=request.headers.get("origin");if(origin&&origin!==new URL(request.url).origin)return Response.json({error:"Forbidden"},{status:403});
 try{
  const raw=await request.text();if(raw.length>100000)return Response.json({error:"批次过大"},{status:413});
  const body=JSON.parse(raw);if(!Array.isArray(body.documents)||body.documents.length>40)return Response.json({error:"每批至多40条"},{status:400});
  if(!env.DB)throw new Error("DB unavailable");
  const now=new Date().toISOString();let added=0,skipped=0;const errors:string[]=[];
  for(const item of body.documents){
   try{
    if(typeof item.url!=="string"||typeof item.title!=="string"||item.title.trim().length<5)throw new Error("缺少标题或链接");
    const parsed=new URL(item.url);if(parsed.protocol!=="https:"||!domains[parsed.hostname]||parsed.username||parsed.password||parsed.port)throw new Error("只接收白名单官方来源HTTPS链接");
    const url=canonical(item.url);if(SEEDS.some(d=>canonical(d.url)===url)){skipped++;continue;}
    const title=item.title.trim().slice(0,250);const summary=typeof item.summary==="string"?item.summary.slice(0,200):"补充收录的官方资料，请打开原文核对。";
    const topics=Array.isArray(item.topics)?item.topics.filter((t:unknown)=>typeof t==="string"&&TOPICS.includes(t)):topicsFor(title+summary);
    if(!topics.length)throw new Error("未关联导师指定研究主题");
    const date=typeof item.date==="string"&&/^20\d{2}-\d{2}-\d{2}$/.test(item.date)&&!Number.isNaN(Date.parse(item.date))&&item.date<=now.slice(0,10)?item.date:null;
    const d:Document={id:url,url,title,source:domains[parsed.hostname],region:item.region==="贵州"?"贵州":"全国",kind:KINDS.includes(item.kind)?item.kind:kindFor(title),status:"补充收录 · 待核对版本",date,number:typeof item.number==="string"?item.number.slice(0,80):undefined,topics:[...new Set<string>(topics)],summary,question:"核对正式文本、文号、时间与引用页码，记录和课题的关系。",verified:false,collectedAt:now};
    const result=await env.DB.prepare("INSERT OR IGNORE INTO documents(url,data,collected_at) VALUES (?,?,?)").bind(url,JSON.stringify(d),now).run();
    if(result.meta.changes)added++;else skipped++;
   }catch(e){errors.push(e instanceof Error?e.message:"条目无效");}
  }
  return Response.json({added,skipped,errors,checkedAt:now});
 }catch{return Response.json({error:"资料写入未完成"},{status:503});}
}
