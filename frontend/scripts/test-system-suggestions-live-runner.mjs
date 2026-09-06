import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { execFileSync, spawnSync } from 'node:child_process';
import { SURFACES, buildPlan, summarize, runPlan, reserveAttempt, createRunDirectory, fatalCategory } from './system-suggestions-live-support.mjs';

const cases = SURFACES.flatMap(surface => Array.from({length:5},(_,index)=>({id:`${surface}-${index}`,surface,reference:{fixture:index}})));
const configurations = [{id:'temperature-0',temperature:0},{id:'temperature-0.2',temperature:.2}];
const plan = buildPlan(cases,configurations.slice(0,1));
const ready = {keyPresent:true,redisConfigured:true,redisReady:true,modeAllowed:true};
const good = {provider_requests_sent:1,schema_passed:true,gate_passed:true,source_class:'MODEL',provider_status:'MODEL_OK',cache_hit:false,latency_ms:100,usage:{input_tokens:10,output_tokens:5,total_tokens:15}};
const executed = (entries=plan) => entries.map(entry=>({...entry,...good,execution:'EXECUTED'}));
const results=[];
async function test(name,fn){try{await fn();results.push({test_nature:'UNIT_MOCK',case:name,result:'PASS'});}catch(error){results.push({test_nature:'UNIT_MOCK',case:name,result:'FAIL',detail:error.message});}}
const temporary=mkdtempSync(join(tmpdir(),'mgda-runner-unit-'));
try {
await test('Base plan is 60, first four requests cover all active surfaces',()=>{assert.equal(plan.length,60);assert.deepEqual(plan.slice(0,4).map(item=>item.surface),SURFACES);assert.ok(plan.slice(0,4).every(item=>item.repetition===1));assert.equal(new Set(plan.map(item=>item.entry_id)).size,60);});
for(const [name,prerequisites,reason] of [
 ['missing key',{...ready,keyPresent:false},'NO_KEY'],['missing isolated Redis',{...ready,redisConfigured:false},'REDIS_MISSING'],
 ['Redis unavailable',{...ready,redisReady:false},'REDIS_UNAVAILABLE'],['provider disabled',{...ready,modeAllowed:false},'PROVIDER_DISABLED'],
 ['invalid configuration',{...ready,invalidConfiguration:true},'INVALID_CONFIGURATION'],
])await test(name+' blocks all cases and exits nonzero',async()=>{let attempts=0;const {rows,summary}=await runPlan({plan,prerequisites,attempt:async()=>{attempts++;return good;}});assert.equal(attempts,0);assert.equal(summary.status,'BLOCKED_ENVIRONMENT');assert.equal(summary.exit_code,2);assert.equal(summary.actual_requests,0);assert.equal(summary.stop_reason,reason);assert.equal(rows.filter(row=>row.execution==='NOT_EXECUTED').length,60);});
await test('Complete base group requires at least 57 genuine valid outputs',()=>{const rows=executed();for(let i=57;i<60;i++)Object.assign(rows[i],{schema_passed:false,gate_passed:false,source_class:'STATIC_FALLBACK',provider_status:'INVALID_RESPONSE'});const summary=summarize(plan,rows);assert.equal(summary.status,'PASS');assert.equal(summary.effective_outputs,57);assert.equal(summary.effective_rate,.95);assert.equal(summary.configurations[0].surfaces.TRACE_OPEN_INQUIRY.effective_outputs,12);assert.deepEqual(summary.fallback_reasons,{INVALID_RESPONSE:3});assert.equal(summary.usage.total_tokens,900);});
await test('56 of 60 fails',()=>{const rows=executed();for(let i=56;i<60;i++)rows[i].gate_passed=false;assert.equal(summarize(plan,rows).status,'FAIL');assert.equal(summarize(plan,rows).exit_code,1);});
await test('Two complete configuration groups evaluated independently at 120 attempts',()=>{const entries=buildPlan(cases,configurations),rows=executed(entries);for(const offset of [0,60])for(let i=57;i<60;i++)rows[offset+i].gate_passed=false;const summary=summarize(entries,rows);assert.equal(summary.status,'PASS');assert.equal(summary.actual_requests,120);assert.deepEqual(summary.configurations.map(group=>[group.planned,group.actual_requests,group.effective_outputs]),[[60,60,57],[60,60,57]]);});
await test('Aggregate 116 of 120 does not conceal failing configuration',()=>{const entries=buildPlan(cases,configurations),rows=executed(entries);for(let i=116;i<120;i++)rows[i].gate_passed=false;const summary=summarize(entries,rows);assert.ok(summary.effective_rate>.95);assert.equal(summary.status,'FAIL');assert.equal(summary.configurations[1].target_met,false);});
await test('Cache hit cannot count as a provider attempt or complete plan',()=>{const rows=executed();Object.assign(rows[59],{provider_requests_sent:0,cache_hit:true});const summary=summarize(plan,rows);assert.equal(summary.actual_requests,59);assert.equal(summary.effective_outputs,59);assert.equal(summary.cache_hits,1);assert.equal(summary.status,'INCOMPLETE');assert.equal(summary.exit_code,1);});
await test('Partial, duplicate and empty result sets cannot pass',()=>{assert.equal(summarize(plan,executed().slice(0,59)).status,'INCOMPLETE');const rows=executed();rows[59]=rows[0];assert.equal(summarize(plan,rows).status,'INCOMPLETE');assert.equal(summarize([],[]).status,'INCOMPLETE');});
await test('Retry consumes an additional attempt without appearing as a complete base run',()=>{const rows=executed();rows[59].provider_requests_sent=2;const summary=summarize(plan,rows);assert.equal(summary.actual_requests,61);assert.equal(summary.status,'INCOMPLETE');});
await test('Failed initial surface check stops before remaining 56 cases',async()=>{let attempts=0;const {summary}=await runPlan({plan,prerequisites:ready,attempt:async()=>++attempts===2?{...good,gate_passed:false,source_class:'STATIC_FALLBACK'}:good});assert.equal(attempts,4);assert.equal(summary.not_executed,56);assert.equal(summary.stop_reason,'INITIAL_SURFACE_CHECK_FAILED');assert.equal(summary.exit_code,1);});
for(const [status,category] of [[401,'AUTHENTICATION'],[403,'AUTHENTICATION'],[402,'BILLING'],[400,'PROVIDER_CONFIGURATION'],[404,'PROVIDER_CONFIGURATION']])await test(`HTTP ${status} stops further paid requests immediately`,async()=>{let attempts=0;const {summary}=await runPlan({plan,prerequisites:ready,attempt:async()=>{attempts++;return {...good,gate_passed:false,source_class:'STATIC_FALLBACK',fatal_category:fatalCategory(status)};}});assert.equal(attempts,1);assert.equal(summary.actual_requests,1);assert.equal(summary.not_executed,59);assert.equal(summary.stop_reason,category);assert.equal(summary.exit_code,2);});
await test('Budget failure captured by service still halts the runner',async()=>{let attempts=0;const {summary}=await runPlan({plan,prerequisites:ready,attempt:async()=>{attempts++;return {...good,provider_requests_sent:0,source_class:'STATIC_FALLBACK',fatal_category:'BUDGET_EXHAUSTED'};}});assert.equal(attempts,1);assert.equal(summary.actual_requests,0);assert.equal(summary.exit_code,1);assert.equal(summary.stop_reason,'BUDGET_EXHAUSTED');});
await test('Source change stops before issuing next request',async()=>{const {summary}=await runPlan({plan,prerequisites:ready,attempt:async()=>{throw Object.assign(new Error('changed'),{code:'SOURCE_CHANGED'});}});assert.equal(summary.actual_requests,0);assert.equal(summary.exit_code,1);});
await test('Shared persistent budget covers runs, retries and production, never exceeds 130',()=>{const path=join(temporary,'budget.json');for(let i=1;i<=130;i++)assert.equal(reserveAttempt(path,{run_id:`run-${i%3}`,phase:i>120?'PRODUCTION_MODE_SMOKE':'LIVE_PROVIDER'}),i);assert.throws(()=>reserveAttempt(path,{run_id:'new-run'}),{code:'BUDGET_EXHAUSTED'});assert.equal(JSON.parse(readFileSync(path)).attempts.length,130);});
for(const value of ['bad JSON','{}',JSON.stringify({limit:131,attempts:[]}),JSON.stringify({limit:130,attempts:null})])await test('Corrupt or oversized budget fails closed: '+value,()=>{const path=join(temporary,'invalid-budget.json');writeFileSync(path,value);assert.throws(()=>reserveAttempt(path,{}),{code:'BUDGET_EXHAUSTED'});assert.equal(readFileSync(path,'utf8'),value);});
await test('Unique run directories preserve earlier BLOCKED evidence',()=>{const first=createRunDirectory(join(temporary,'runs'));writeFileSync(join(first.directory,'summary.json'),'BLOCKED 0/60');const second=createRunDirectory(join(temporary,'runs'));assert.notEqual(first.id,second.id);assert.equal(readFileSync(join(first.directory,'summary.json'),'utf8'),'BLOCKED 0/60');});
await test('CLI exit codes propagate PASS, INCOMPLETE and BLOCKED to parent process',()=>{const moduleUrl=new URL('./system-suggestions-live-support.mjs',import.meta.url).href;for(const [reason,code] of [['NO_KEY',2],[null,1]]){const child=spawnSync(process.execPath,['--input-type=module','-e',`import {summarize} from ${JSON.stringify(moduleUrl)};process.exitCode=summarize([],[],${JSON.stringify(reason)}).exit_code;`]);assert.equal(child.status,code);}const child=spawnSync(process.execPath,['--input-type=module','-e',`import {summarize} from ${JSON.stringify(moduleUrl)};process.exitCode=summarize(${JSON.stringify(plan)},${JSON.stringify(executed())}).exit_code;`]);assert.equal(child.status,0);});
await test('Actual live CLI returns exit 2 and immutable 0/60 evidence with isolated fake environment loader',()=>{
  // Run the real entry point, replacing only dependencies inside a temporary fixture project.
  // Neither the owner's environment files nor any real network client are reachable here.
  const frontend=join(temporary,'fixture-project','frontend'),scripts=join(frontend,'scripts');
  mkdirSync(scripts,{recursive:true});
  for(const name of ['verify-system-suggestions-live-v1.mjs','system-suggestions-live-support.mjs'])writeFileSync(join(scripts,name),readFileSync(new URL(name,import.meta.url)));
  writeFileSync(join(scripts,'system-suggestions-live-fixtures.mjs'),`export async function liveCases(){return ${JSON.stringify(cases)}}`);
  for(const name of ['jiti','@next/env'])mkdirSync(join(frontend,'node_modules',name),{recursive:true});
  writeFileSync(join(frontend,'node_modules','jiti','index.js'),"module.exports=()=>({import:async()=>({})});");
  writeFileSync(join(frontend,'node_modules','@next/env','index.js'),"module.exports={loadEnvConfig:()=>({loadedEnvFiles:[]})};");
  const gitDir=execFileSync('git',['rev-parse','--absolute-git-dir'],{encoding:'utf8'}).trim();
  const runs=join(temporary,'fixture-project','docs/qa/system-suggestions-live-completion-v3/runs');
  mkdirSync(runs,{recursive:true});
  for(const [extra,reason] of [[{},'NO_KEY'],[{DEEPSEEK_API_KEY:'offline-fixture'},'REDIS_MISSING'],[{DEEPSEEK_API_KEY:'offline-fixture',SYSTEM_SUGGESTS_TEST_REDIS_URL:'unused',SYSTEM_SUGGESTIONS_PROVIDER:'off'},'PROVIDER_DISABLED'],[{DEEPSEEK_API_KEY:'offline-fixture',SYSTEM_SUGGESTS_TEST_REDIS_URL:'unused',DEEPSEEK_MODEL:'unapproved'},'INVALID_CONFIGURATION']]){
    const before=new Set(readdirSync(runs));
    const child=spawnSync(process.execPath,[join(scripts,'verify-system-suggestions-live-v1.mjs')],{cwd:frontend,env:{PATH:process.env.PATH,GIT_DIR:gitDir,...extra},encoding:'utf8'});
    assert.equal(child.status,2,child.stderr+child.stdout);
    const added=readdirSync(runs).filter(name=>!before.has(name));assert.equal(added.length,1);
    const summary=JSON.parse(readFileSync(join(runs,added[0],'summary.json')));
    assert.equal(summary.status,'BLOCKED_ENVIRONMENT');assert.equal(summary.stop_reason,reason);assert.equal(summary.actual_requests,0);assert.equal(summary.not_executed,60);
  }
  assert.equal(readdirSync(runs).length,4);
});
await test('Continuation retains executed results and sends only missing entries',async()=>{let calls=0;const completedRows=executed().slice(0,45);completedRows[20].source_class='STATIC_FALLBACK';completedRows[20].gate_passed=false;const {rows,summary}=await runPlan({plan,prerequisites:ready,completedRows,attempt:async()=>{calls++;return good;}});assert.equal(calls,15);assert.equal(summary.actual_requests,60);assert.equal(summary.effective_outputs,59);assert.equal(summary.status,'PASS');assert.equal(rows.filter(row=>row.inherited).length,45);});
await test('Runner CLI uses computed status and durable reservation before fetch',()=>{const main=readFileSync(new URL('./verify-system-suggestions-live-v1.mjs',import.meta.url),'utf8');assert.match(main,/process\.exitCode=summary\.exit_code/);assert.doesNotMatch(main,/process\.exit\(0\)|calls\s*===\s*60/);assert.ok(main.indexOf('reserveAttempt(budgetFile')<main.indexOf('await fetch(url,init)'));assert.match(main,/fatal='BUDGET_EXHAUSTED'/);});
}finally{rmSync(temporary,{recursive:true,force:true});}
for(const result of results)console.log(JSON.stringify(result));
const failed=results.filter(item=>item.result==='FAIL').length;
console.log(JSON.stringify({summary:true,test_nature:'UNIT_MOCK',passed:results.length-failed,failed,external_requests:0}));
process.exitCode=failed?1:0;
