import { env } from "cloudflare:workers";
import { readState } from "../../../lib/collector";
export const dynamic="force-dynamic";
export async function POST(request: Request) {
 const origin=request.headers.get("origin");if(origin&&origin!==new URL(request.url).origin)return Response.json({error:"Forbidden"},{status:403});
 try {const body=await request.json() as {id?:unknown;enabled?:unknown};if(!body||typeof body.id!=="string"||body.id.length>200||typeof body.enabled!=="boolean")return Response.json({error:"Invalid schedule"},{status:400});
 if(!env.DB)throw new Error("DB unavailable");
 const value={id:body.id,enabled:body.enabled,time:"08:00",timezone:"Asia/Shanghai",recordedAt:new Date().toISOString()};
 await env.DB.prepare("INSERT INTO collector_state(key,value) VALUES ('schedule',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value").bind(JSON.stringify(value)).run();
 return Response.json(await readState(env.DB,"schedule"));
 }catch{return Response.json({error:"无法记录计划状态"},{status:503});}
}
