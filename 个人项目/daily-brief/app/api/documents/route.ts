import { env } from "cloudflare:workers";
import { getDocuments, readState } from "../../../lib/collector";
export const dynamic="force-dynamic";
export async function GET() {
 try {
  if(!env.DB)throw new Error("数据库未连接");
  return Response.json({documents:await getDocuments(env.DB),lastRun:await readState(env.DB,"lastRun"),schedule:await readState(env.DB,"schedule")},{headers:{"Cache-Control":"no-store"}});
 }catch{return Response.json({error:"资料库暂时无法连接，请稍后重试。"},{status:503});}
}
