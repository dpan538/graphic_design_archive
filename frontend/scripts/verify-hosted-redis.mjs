// Opt-in, non-destructive Valkey/Redis compatibility check. No provider calls.
// Uses isolated, automatically expiring keys; never pauses/restarts/flushes a service.
import { createRequire } from 'node:module';
import { fork } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { resolve } from 'node:path';
const require=createRequire(import.meta.url), root=resolve(import.meta.dirname,'..');
require('@next/env').loadEnvConfig(root,true,{info(){},error(){}});
let url;try{url=new URL(process.env.REDIS_URL);}catch{}
if(!url || url.protocol!=='rediss:' || !url.password || ['localhost','127.0.0.1','::1'].includes(url.hostname) || process.env.NODE_TLS_REJECT_UNAUTHORIZED==='0') {
 console.log(JSON.stringify({status:'BLOCKED_CONFIGURATION',hostedCompatibility:'NOT_RUN'}));process.exit(2);
}
const jiti=require('jiti')(import.meta.url,{tryNative:false,alias:{'@':root+'/src','server-only':import.meta.dirname+'/server-only-marker.mjs'}});
const limiter=await jiti.import(root+'/src/features/system-suggestions/rate-limiter.server.ts');
if(process.argv.includes('--worker')) {
 const rows=await Promise.all(Array.from({length:50},async(_,i)=>{
  const start=performance.now();
  const response=await limiter.checkRequestRateLimit(new Request(`https://integration.invalid/api/${['search','context','exploration','inquiry'][i%4]}`));
  return {status:response.status,remaining:response.remaining,retryAfter:response.retryAfter,ms:performance.now()-start};
 }));
 process.send(rows,()=>process.exit(0));
} else {
 if(!process.argv.includes('--run')){console.log('Explicit --run required for isolated hosted counter writes.');process.exit(2);}
 const namespace=`test:mgda:hosted:${randomUUID()}`;
 const prerequisite=limiter.makeLimiterClient(process.env.REDIS_URL);
 let errorCategory='LIMITER_UNAVAILABLE';
 prerequisite.on('error',error=>{
  errorCategory=['WRONGPASS','NOAUTH','NOPERM','ENOTFOUND','ECONNREFUSED','ETIMEDOUT','ECONNRESET','ERR_TLS_CERT_ALTNAME_INVALID'].find(code=>error.code===code||String(error.message).includes(code))||'CONNECTION_ERROR';
 });
 const admission=await limiter.consumeFixedWindow(prerequisite,namespace+':prerequisite');prerequisite.disconnect();
 if(admission.status!=='ALLOWED'){
  console.log(JSON.stringify({status:'FAIL',stage:'AUTH_TLS_SCRIPT_PREREQUISITE',errorCategory,sharedQuota:'NOT_RUN',providerRequests:0}));process.exit(2);
 }
 const worker=()=>new Promise((done,reject)=>{
  const child=fork(new URL(import.meta.url),['--worker'],{env:{...process.env,NODE_ENV:'test',SYSTEM_SUGGESTIONS_RATE_LIMIT_NAMESPACE:namespace,SYSTEM_SUGGESTIONS_IDENTITY_SECRET:randomIdentity,SYSTEM_SUGGESTIONS_TRUSTED_IP_HEADER:''},stdio:['ignore','ignore','ignore','ipc']});
  let received=false;const timer=setTimeout(()=>{child.kill();reject(Error('WORKER_TIMEOUT'));},10000);
  child.on('message',data=>{received=true;clearTimeout(timer);done(data);});child.on('exit',()=>{if(!received){clearTimeout(timer);reject(Error('WORKER_FAILED'));}});
 });
 const randomIdentity=randomUUID()+randomUUID();
 try {
  const rows=(await Promise.all([worker(),worker()])).flat();
  const allowed=rows.filter(x=>x.status==='ALLOWED').length;
  const unavailable=rows.filter(x=>x.status==='LIMITER_UNAVAILABLE').length;
  const client=limiter.makeLimiterClient(process.env.REDIS_URL), key=namespace+':reuse';
  const cold=performance.now();const first=await limiter.consumeFixedWindow(client,key,1200,2);const coldMs=performance.now()-cold;
  await new Promise(r=>setTimeout(r,150));const hot=performance.now();const second=await limiter.consumeFixedWindow(client,key,1200,2);const hotMs=performance.now()-hot;
  const reuse=client.status==='ready';const third=await limiter.consumeFixedWindow(client,key,1200,2);
  await new Promise(r=>setTimeout(r,1250));const recovered=await limiter.consumeFixedWindow(client,key,1200,2);client.disconnect();
  const pass=allowed===30 && unavailable===0 && first.status==='ALLOWED' && second.remaining===0 && third.status==='LIMIT_REACHED' && second.resetAt<=first.resetAt+30 && recovered.remaining===1 && reuse;
  const lat=rows.map(r=>r.ms).sort((a,b)=>a-b);
  console.log(JSON.stringify({status:pass?'PASS':'FAIL',type:'INTEGRATION_REAL_HOSTED_REDIS',requests:100,independentProcesses:2,allowed,unavailable,coldMs,hotMs,p50Ms:lat[49],p95Ms:lat[94],connectionReuse:reuse,tlsCertificateVerification:true,script:'EVAL/INCR/PEXPIRE/PTTL',providerRequests:0,cleanup:'TTL only',freePlan:'OWNER_ACCOUNT_VERIFICATION_REQUIRED',proxyOverwrite:'NOT_RUN'}));
  if(!pass)process.exitCode=1;
 } catch { console.log(JSON.stringify({status:'FAIL',errorCategory:'HOSTED_INTEGRATION_FAILED',providerRequests:0}));process.exitCode=1; }
}
