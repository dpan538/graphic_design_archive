/* Live acceptance: four first-plan surface requests, then the remaining 56.
   Credentials are loaded locally; only safe metadata and public fixture output are recorded.
   A run is immutable, and the shared campaign ledger caps ALL external attempts at 130. */
import { appendFileSync, readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildPlan, createRunDirectory, fatalCategory, reserveAttempt, runPlan, sourceSnapshot, SURFACES } from './system-suggestions-live-support.mjs';
import { liveCases } from './system-suggestions-live-fixtures.mjs';
const here=dirname(fileURLToPath(import.meta.url)), frontendRoot=join(here,'..');
const qa=join(frontendRoot,'../docs/qa/system-suggestions-live-completion-v3');
const run=createRunDirectory(join(qa,'runs'));
const ledger=join(run.directory,'system-suggests-live-results.jsonl');
const budgetFile=join(qa,'campaign-budget.json');
const require=createRequire(import.meta.url);
const jiti=require('jiti')(import.meta.url,{interopDefault:true,tryNative:false,alias:{'@':join(frontendRoot,'src'),'server-only':join(here,'server-only-marker.mjs')}});
const before=sourceSnapshot(frontendRoot);
writeFileSync(join(run.directory,'source-before.json'),JSON.stringify(before,null,2)+'\n');
let redis;
try {
  const shellKeyPresent=Boolean(process.env.DEEPSEEK_API_KEY?.trim());
  const previous=process.env.NODE_ENV;
  if(previous==='test')process.env.NODE_ENV='development';
  const loaded=require('@next/env').loadEnvConfig(frontendRoot,true,{info(){},error(){}});
  if(previous===undefined)delete process.env.NODE_ENV;else process.env.NODE_ENV=previous;
  const environment={...process.env};
  const key=environment.DEEPSEEK_API_KEY?.trim()??'';
  const configSources=shellKeyPresent?['process environment']:loaded.loadedEnvFiles.filter(file=>/^\s*DEEPSEEK_API_KEY\s*=/m.test(file.contents)).map(file=>join(frontendRoot,file.path));
  const temperatures=(environment.LIVE_TEMPERATURES??'0').split(',').map(value=>Number(value.trim()));
  const mode=environment.SYSTEM_SUGGESTIONS_PROVIDER?.trim().toLowerCase()||'auto';
  const invalidConfiguration=temperatures.some(value=>![0,.2].includes(value))||new Set(temperatures).size!==temperatures.length
    ||(temperatures.includes(.2)&&!environment.LIVE_COMPARISON_REASON?.trim())
    ||(environment.LIVE_RUNS!==undefined&&environment.LIVE_RUNS!=='3')
    ||(environment.DEEPSEEK_MODEL!==undefined&&environment.DEEPSEEK_MODEL!=='deepseek-v4-flash')
    ||(environment.DEEPSEEK_BASE_URL!==undefined&&environment.DEEPSEEK_BASE_URL!=='https://api.deepseek.com');
  const configurations=(invalidConfiguration?[0]:temperatures).map(temperature=>({id:`deepseek-v4-flash:responses:none:t${temperature}:512`,model:'deepseek-v4-flash',protocol:'Responses',reasoning:'none',temperature,max_output_tokens:512}));
  const cases=await liveCases(jiti,frontendRoot,join);
  if(cases.length!==20||SURFACES.some(surface=>cases.filter(item=>item.surface===surface).length!==5))throw new Error('Fixture coverage invalid');
  const plan=buildPlan(cases,configurations);
  const resumeId=environment.LIVE_RESUME_RUN_ID;
  let completedRows=[];
  if(resumeId){
    if(!/^[a-zA-Z0-9:-]+$/.test(resumeId))throw Error('Invalid resume identity');
    const parent=join(qa,'runs',resumeId);
    const prior=JSON.parse(readFileSync(join(parent,'source-before.json'),'utf8'));
    const runtime=files=>Object.fromEntries(Object.entries(files).filter(([name])=>!name.startsWith('scripts/')));
    if(prior.head!==before.head||JSON.stringify(runtime(prior.files))!==JSON.stringify(runtime(before.files)))throw Error('Continuation candidate differs');
    const priorPlan=JSON.parse(readFileSync(join(parent,'plan.json'),'utf8'));
    if(JSON.stringify(priorPlan)!==JSON.stringify(plan))throw Error('Continuation plan differs');
    completedRows=readFileSync(join(parent,'system-suggests-live-results.jsonl'),'utf8').trim().split('\n').map(JSON.parse).filter(row=>row.execution==='EXECUTED');
  }
  writeFileSync(join(run.directory,'plan.json'),JSON.stringify(plan,null,2)+'\n');
  const limiter=await jiti.import(join(frontendRoot,'src/features/system-suggestions/rate-limiter.server.ts'));
  const svc=await jiti.import(join(frontendRoot,'src/features/system-suggestions/service.server.ts'));
  const cache=await jiti.import(join(frontendRoot,'src/features/system-suggestions/cache.server.ts'));
  const providers=await jiti.import(join(frontendRoot,'src/features/system-suggestions/providers.server.ts'));
  let redisReady=false;
  if(key&&environment.SYSTEM_SUGGESTS_TEST_REDIS_URL&&['auto','deepseek'].includes(mode)&&!invalidConfiguration){
    redis=limiter.makeLimiterClient(environment.SYSTEM_SUGGESTS_TEST_REDIS_URL);
    try{await redis.connect();redisReady=(await redis.ping())==='PONG';}catch{}
  }
  const prerequisites={keyPresent:Boolean(key),redisConfigured:Boolean(environment.SYSTEM_SUGGESTS_TEST_REDIS_URL),redisReady,modeAllowed:['auto','deepseek'].includes(mode),invalidConfiguration};
  const metadata={run_id:run.id,test_nature:'LIVE_PROVIDER',KEY_PRESENT:Boolean(key),config_sources:configSources,redis_ready:redisReady,provider_mode_allowed:prerequisites.modeAllowed,configurations,planned:plan.length,source_fingerprint:before.fingerprint};
  writeFileSync(join(run.directory,'run.json'),JSON.stringify(metadata,null,2)+'\n');console.log(JSON.stringify(metadata));
  const liveKey=`test:mgda:live-completion:${run.id}:single-requester`;
  let previousAttempt=0;
  const result=await runPlan({plan,prerequisites,completedRows,record:row=>appendFileSync(ledger,JSON.stringify({test_nature:'LIVE_PROVIDER',run_id:run.id,...row})+'\n'),attempt:async entry=>{
    if(sourceSnapshot(frontendRoot).fingerprint!==before.fingerprint)throw Object.assign(new Error('Source changed'),{code:'SOURCE_CHANGED'});
    const pause=Math.max(0,2050-(Date.now()-previousAttempt));if(previousAttempt&&pause)await new Promise(resolve=>setTimeout(resolve,pause));
    const admission=await limiter.consumeFixedWindow(redis,liveKey);
    if(admission.status!=='ALLOWED')throw Object.assign(new Error('Admission unavailable'),{code:admission.status==='LIMIT_REACHED'?'RATE_LIMIT_REACHED':'REDIS_UNAVAILABLE'});
    cache.resetGuidanceCacheForTest();
    let sent=0,httpStatus=null,usage=null,schemaPassed=false,providerNote=null,outputSummary=null,fatal=null,providerDraft=null;
    const started=performance.now();
    const fetchImpl=async(url,init)=>{
      try { reserveAttempt(budgetFile,{run_id:run.id,phase:'LIVE_PROVIDER',entry_id:entry.entry_id}); }
      catch (error) { fatal='BUDGET_EXHAUSTED'; throw error; }
      sent++;previousAttempt=Date.now();
      const response=await fetch(url,init);httpStatus=response.status;fatal=fatalCategory(httpStatus);
      const text=await response.text();
      try{
        const payload=JSON.parse(text);usage=payload.usage??null;
        outputSummary={response_status:typeof payload.status==='string'?payload.status.slice(0,40):null,output_types:Array.isArray(payload.output)?payload.output.map(item=>String(item.type).slice(0,40)):[],bytes:text.length};
        const draft=providers.parseProviderDraft(providers.providerOutputText(payload));schemaPassed=true;providerNote=draft.note.replaceAll(key,'[REDACTED]');providerDraft={...draft,note:providerNote};
      }catch{}
      return new Response(text,{status:response.status,headers:response.headers});
    };
    const request={schemaVersion:'gda-system-suggestions-request/v2',surface:entry.surface,reference:entry.reference};
    const facts=svc.resolveSystemSuggestionsFactsForTest(request).facts;
    const response=await svc.createSystemSuggestions(request,{environment:{...environment,SYSTEM_SUGGESTIONS_TEMPERATURE:String(entry.configuration.temperature)},fetchImpl,admission});
    const row={provider_requests_sent:sent,schema_passed:schemaPassed,gate_passed:response.sourceClass==='MODEL',cache_hit:/CACHED|LAST_GOOD/.test(response.providerStatus),source_class:response.sourceClass,provider_status:response.providerStatus,http_status:httpStatus,fatal_category:fatal,latency_ms:Math.round(performance.now()-started),usage,provider_draft:providerDraft,provider_note:providerNote,output_summary:outputSummary,note:response.note,used_fact_ids:response.usedFactIds??[],suggestions:response.suggestions.map(item=>item.label),context_fingerprint:response.contextFingerprint,review_facts:{pairs:facts.pairs,counts:facts.counts,labels:facts.labels,statements:facts.statements},content_review:'PENDING_INDEPENDENT_REVIEW'};
    console.log(`${entry.surface} ${entry.id} #${entry.repetition} t=${entry.configuration.temperature} → ${row.source_class} ${row.provider_status} (${sent} external attempt)`);
    return row;
  }});
  if(redisReady){try{await redis.del(liveKey);}catch{}}
  const after=sourceSnapshot(frontendRoot);
  writeFileSync(join(run.directory,'source-after.json'),JSON.stringify(after,null,2)+'\n');
  const stable=before.fingerprint===after.fingerprint;
  if(!stable){result.summary.status='INCOMPLETE';result.summary.exit_code=1;result.summary.stop_reason='SOURCE_CHANGED';}
  const summary={run_id:run.id,continuation_of:resumeId??null,new_provider_requests:result.rows.filter(row=>!row.inherited).reduce((sum,row)=>sum+(row.provider_requests_sent??0),0),inherited_provider_requests:completedRows.reduce((sum,row)=>sum+row.provider_requests_sent,0),test_nature:'LIVE_PROVIDER',SOURCE_SNAPSHOT_STABLE:stable,...result.summary};
  writeFileSync(join(run.directory,'summary.json'),JSON.stringify(summary,null,2)+'\n');
  appendFileSync(ledger,JSON.stringify({summary:true,...summary})+'\n');
  console.log(`SYSTEM_SUGGESTS_LIVE=${summary.status} actual=${summary.actual_requests}/${summary.planned} exit=${summary.exit_code} run=${run.id}`);
  process.exitCode=summary.exit_code;
}catch{
  writeFileSync(join(run.directory,'summary.json'),JSON.stringify({run_id:run.id,test_nature:'LIVE_PROVIDER',status:'INCOMPLETE',stop_reason:'RUNNER_ERROR',exit_code:1})+'\n');
  console.error(`SYSTEM_SUGGESTS_LIVE=INCOMPLETE reason=RUNNER_ERROR run=${run.id}`);process.exitCode=1;
}finally{redis?.disconnect();}
