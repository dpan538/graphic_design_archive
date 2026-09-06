// Process-only config check; never print URLs, IPs, passwords or raw errors.
import { createRequire } from "node:module";
import { resolve } from "node:path";
const require = createRequire(import.meta.url);
require("@next/env").loadEnvConfig(resolve(import.meta.dirname,".."), true, {info(){},error(){}});
const env=process.env, fields=["REDIS_URL","SYSTEM_SUGGESTIONS_RATE_LIMIT_NAMESPACE","SYSTEM_SUGGESTIONS_IDENTITY_SECRET","SYSTEM_SUGGESTIONS_TRUSTED_IP_HEADER","DEEPSEEK_API_KEY"];
const presence=Object.fromEntries(fields.map(x=>[`${x}_PRESENT`,!!env[x]?.trim()]));
let valid=false;
try { const url=new URL(env.REDIS_URL); valid=url.protocol==="rediss:" && !!url.password && !!env.SYSTEM_SUGGESTIONS_IDENTITY_SECRET && env.SYSTEM_SUGGESTIONS_IDENTITY_SECRET.length>=32 && /^mgda:(preview|production):system-suggestions:v1$/.test(env.SYSTEM_SUGGESTIONS_RATE_LIMIT_NAMESPACE??"") && env.SYSTEM_SUGGESTIONS_TRUSTED_IP_HEADER==="x-vercel-forwarded-for" && env.NODE_TLS_REJECT_UNAUTHORIZED!=="0"; }catch{}
console.log(JSON.stringify({ ...presence, HOSTED_CONFIGURATION:valid?"VALID_FORMAT":"BLOCKED_CONFIGURATION", connectivity:"NOT_RUN", proxyOverwrite:"NOT_RUN", freePlan:"NOT_VERIFIED" }));
if(!valid)process.exitCode=2;
