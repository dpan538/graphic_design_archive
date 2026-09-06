import {readFileSync,writeFileSync} from 'node:fs';
import {dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const dir=join(dirname(fileURLToPath(import.meta.url)),'../../docs/qa/system-suggestions-final-v2');
const base=process.env.SYSTEM_SUGGESTS_PRODUCTION_URL??'http://127.0.0.1:3107';
const rows=readFileSync(join(dir,'system-suggests-test-cases.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const results=[];
for(const id of ['SS-079','SS-080','SS-081','SS-082']){
 const row=rows.find(r=>r.id===id);const body={schemaVersion:'gda-system-suggestions-request/v2',surface:row.surface,reference:row.reference};const start=performance.now();
 const response=await fetch(base+'/api/system-suggestions/v1',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(30000)});const data=await response.json();
 assert.equal(response.status,200);assert.equal(data.sourceClass,'STATIC_FALLBACK');assert.equal(data.providerStatus,'LIMITER_UNAVAILABLE');assert.ok(data.note.split(/\s+/).length<=45);
 if(id==='SS-081')assert.equal(data.note,'In this view, trade is paired with propaganda.');
 results.push({test_nature:'PRODUCTION_MODE_SMOKE',case:row.surface,result:'PASS',status:response.status,latency_ms:Math.round(performance.now()-start),body:data});
}
for(const [name,path] of [['Search','/search?q=poster'],['Canvas','/trace/context-canvas'],['Exploration','/trace/exploration']]){
 const r=await fetch(base+path,{signal:AbortSignal.timeout(30000)});const html=await r.text();assert.equal(r.status,200);assert.ok(html.length>1000);
 results.push({test_nature:'PRODUCTION_MODE_SMOKE',case:name+' page',result:'PASS',status:r.status,bytes:html.length});
}
for(const [name,body,status] of [['Spacetime',{surface:'TRACE_SPACETIME'},404],['forged',{schemaVersion:'gda-system-suggestions-request/v2',surface:'SEARCH_RESULTS',reference:{query:'poster',filters:{}},shown:{exactResultCount:99999}},400]]){
 const r=await fetch(base+'/api/system-suggestions/v1',{method:'POST',body:JSON.stringify(body),signal:AbortSignal.timeout(10000)});assert.equal(r.status,status);
 results.push({test_nature:'PRODUCTION_MODE_SMOKE',case:name,result:'PASS',status:r.status,body:await r.json()});
}
writeFileSync(join(dir,'production-smoke.jsonl'),results.map(JSON.stringify).join('\n')+'\n');console.log('PRODUCTION_SMOKE=PASS cases='+results.length);
