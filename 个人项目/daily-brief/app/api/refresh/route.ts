import { env } from "cloudflare:workers";
import { refresh } from "../../../lib/collector";
export const dynamic="force-dynamic";
export async function POST(request: Request) {
 const origin=request.headers.get("origin");
 if(origin&&origin!==new URL(request.url).origin)return Response.json({error:"请求来源不匹配"},{status:403});
 // This shared collector is protected by the owner-private Site access boundary.
 // Keep the Site owner-private; do not expose the writer on a public Site.
 try {if(!env.DB)throw new Error("DB unavailable");return Response.json(await refresh(env.DB),{headers:{"Cache-Control":"no-store"}});}
 catch{return Response.json({error:"收集未完成，已有资料仍然保留，请稍后重试。"},{status:503});}
}
