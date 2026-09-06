import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import createJiti from 'jiti';
const root=resolve(import.meta.dirname,'..');
const jiti=createJiti(import.meta.url,{alias:{'@':resolve(root,'src'),'server-only':resolve(root,'scripts/server-only-stub.mjs')}});
const {safeJsonLd,implementation}=await jiti.import(resolve(root,'src/features/machine-reading/project.ts'));
const {aboutMarkdown,sourceMarkdown}=await jiti.import(resolve(root,'src/features/machine-reading/markdown.ts'));
const sitemap=await jiti.import(resolve(root,'src/app/sitemap.ts'));
const eligibility=JSON.parse(readFileSync(resolve(root,'generated/reader-eligibility-v49/eligibility.json')));
const eligible=eligibility.entries.filter(x=>x[1]==='INDEX_ELIGIBLE').map(x=>x[0]);
const records=eligibility.entries.filter(x=>x[1]==='RECORD_ONLY').map(x=>x[0]);
const results=[];
async function test(name,fn,kind='UNIT_CONTRACT'){try{const evidence=await fn();results.push({name,kind,status:'PASS',evidence});}catch(e){results.push({name,kind,status:'FAIL',detail:e.message});process.exitCode=1;}}
await test('JSON-LD resists script injection and round-trips data',()=>{const value={name:'</script><script>alert(1)</script>&\u2028'};const encoded=safeJsonLd(value);assert.ok(!encoded.includes('<'));assert.deepEqual(JSON.parse(encoded),value);});
await test('Sitemap exactly matches independent eligibility artifact',()=>{const items=sitemap.default();const urls=items.map(x=>x.url);assert.equal(new Set(urls).size,urls.length);const ids=urls.filter(x=>x.includes('/surfaces/')).map(x=>decodeURIComponent(x.split('/').at(-1)));assert.deepEqual(ids.sort(),eligible.sort());assert.ok(items.every(x=>!x.lastModified));assert.ok(urls.every(x=>x.startsWith('https://mgdarchive.com/')&&!x.includes('?')));return {eligible:ids.length,recordOnlyExcluded:records.length};});
await test('Markdown shares the visible implementation source',()=>{for(const x of implementation)assert.ok(aboutMarkdown.includes(x.text));assert.ok(sourceMarkdown.includes('provenance'));assert.ok(!/llms-full|api\/system-suggestions/.test(aboutMarkdown+sourceMarkdown));});
const base=process.env.MGDA_BASE_URL;
if(base){
 const htmlText=s=>s.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,'').replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi,'').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ');
 async function get(path,ua='Mozilla/5.0 desktop'){const r=await fetch(base+path,{headers:{'user-agent':ua}});const body=await r.text();return {r,body};}
 for(const path of ['/','/about','/source','/directory','/read-api',`/surfaces/${eligible[0]}`]) await test('No-JS HTML '+path,async()=>{
  const {r,body}=await get(path);assert.equal(r.status,200);const text=htmlText(body);assert.ok(text.length>150);assert.ok(/source|Source|provenance/.test(text));
  const scripts=[...body.matchAll(/<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g)].map(x=>JSON.parse(x[1]));assert.ok(scripts.length);assert.ok(body.includes('rel="canonical"'));return {textCharacters:text.length,jsonLdCount:scripts.length};
 },'HTTP_REAL_APP');
 await test('Object JSON-LD and visible metadata match independent public fixture',async()=>{const tuples=JSON.parse(readFileSync(resolve(root,'generated/search-v2/documents.json'))).documents;const fixture=tuples.find(x=>x[0]===eligible[0]);const {body}=await get('/surfaces/'+fixture[0]);const data=[...body.matchAll(/<script[^>]*type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g)].map(x=>JSON.parse(x[1])).find(x=>x['@type']==='WebPage');assert.equal(data.identifier,fixture[0]);assert.equal(data.name,fixture[1]);assert.ok(htmlText(body).includes(fixture[0]));assert.ok(!('image' in data)&&!('creator' in data)&&!('license' in data));},'HTTP_REAL_APP');
 await test('TRACE explanation exists in raw HTML',async()=>{const {r,body}=await get('/trace');assert.equal(r.status,200);const text=htmlText(body);for(const phrase of ['Context','Exploration','Spacetime'])assert.ok(text.includes(phrase));},'HTTP_REAL_APP');
 await test('Desktop/mobile core About facts and private device response',async()=>{for(const ua of ['Mozilla/5.0 desktop','Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Mobile']) { const {r,body}=await get('/about',ua);const text=htmlText(body);for(const x of ['5,423','2,572','AI-assisted','Spacetime','PostgreSQL'])assert.ok(text.includes(x),x);assert.ok(!/public|s-maxage/.test(r.headers.get('cache-control')??''));} },'HTTP_REAL_APP');
 await test('Text routes and sitemap HTML contract',async()=>{for(const [path,expected] of [['/about.md',aboutMarkdown],['/source.md',sourceMarkdown]]){const {r,body}=await get(path);assert.equal(r.status,200);assert.equal(body,expected);}const {body}=await get('/sitemap.xml');assert.equal([...body.matchAll(/<loc>/g)].length,eligible.length+5);const llms=await get('/llms.txt');assert.equal(llms.r.status,200);for(const match of llms.body.matchAll(/\]\(https:\/\/mgdarchive.com([^)]*)\)/g))assert.equal((await get(match[1])).r.status,200);},'HTTP_REAL_APP');
 await test('Record-only and retired resources do not regain discovery',async()=>{const record=await get('/surfaces/'+records[0]);assert.equal(record.r.status,200);assert.match(record.body,/noindex/);for(const path of ['/data/public_surface_mock_v0.json','/data/trace-v48/catalog.json','/surfaces/INVENTED-NOT-PUBLIC','/llms-full.txt'])assert.equal((await get(path)).r.status,404);const spec=JSON.parse((await get('/openapi.json')).body);assert.deepEqual(Object.keys(spec.paths).sort(),['/api/index/v1','/api/search/v1','/api/search/v1/facets']);},'HTTP_REAL_APP');
} else if(process.argv.includes('--require-http')) {results.push({name:'HTTP required',status:'BLOCKED',detail:'MGDA_BASE_URL missing'});process.exitCode=1;}
if(process.env.MGDA_MACHINE_RESULTS)writeFileSync(process.env.MGDA_MACHINE_RESULTS,results.map(x=>JSON.stringify(x)).join('\n')+'\n');
console.log(JSON.stringify(results,null,2));
