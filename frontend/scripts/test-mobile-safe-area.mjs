import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { chromium, webkit } from '@playwright/test';
const base = process.env.MGDA_BASE_URL || 'http://127.0.0.1:3140';
const out = resolve(process.env.MGDA_MOBILE_EVIDENCE || '/tmp/mgda-mobile-safe-area');
mkdirSync(out,{recursive:true});
const results=[];
const ua='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1';
let failures=0;
for(const [engine,launcher] of Object.entries({chromium,webkit})) {
 const browser=await launcher.launch({headless:true});
 const context=await browser.newContext({viewport:{width:390,height:844},userAgent:ua,isMobile:true,hasTouch:true,deviceScaleFactor:1});
 const page=await context.newPage();
 const errors=[]; page.on('pageerror',e=>errors.push(e.message));
 const run=async(name,fn)=>{try{await fn();results.push({engine,name,type:'BROWSER_ENGINE_SIMULATION',status:'PASS'});}catch(e){failures++;results.push({engine,name,type:'BROWSER_ENGINE_SIMULATION',status:'FAIL',error:e.message});} writeFileSync(out+'/results.json',JSON.stringify(results,null,2));};
 const shot=async(name)=>page.screenshot({path:`${out}/${engine}-${name}.png`});
 const settle=async()=>{await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(150);};
 const bounds=async()=>page.evaluate(()=>{
  const nav=document.querySelector('[data-nav="mobile"]');const n=nav.getBoundingClientRect();
  const links=[...nav.querySelectorAll('a')].map(a=>{const b=a.getBoundingClientRect();return{x:b.x,y:b.y,right:b.right,bottom:b.bottom};});
  return {nav:{top:n.top,bottom:n.bottom,height:n.height},links,width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth,root:getComputedStyle(document.documentElement).backgroundColor,body:getComputedStyle(document.body).backgroundColor};
 });
 const insets=async()=>page.addStyleTag({content:'[class*="MobileShell_shell"] { --safe-top: 27px !important; --safe-right: 32px !important; --safe-bottom: 34px !important; --safe-left: 32px !important; }'});
 await run('SSR viewport and first background',async()=>{
  const res=await context.request.get(base+'/');const html=await res.text();
  const tags=html.match(/<meta[^>]*name="viewport"[^>]*>/g)||[];assert.equal(tags.length,1);assert.match(tags[0],/viewport-fit=cover/);assert.doesNotMatch(tags[0],/maximum-scale|user-scalable/);
  await page.goto(base+'/');await settle();const b=await bounds();assert.equal(b.root,'rgb(255, 253, 249)');assert.equal(b.body,b.root);assert.equal(b.overflow,false);await shot('home-first');
 });
 await run('Search inset, dynamic visible height, close and scroll restore',async()=>{
  await page.evaluate(()=>scrollTo(0,380));const y=await page.evaluate(()=>scrollY);
  await page.locator('nav a[aria-label="Search"]').click();await page.getByRole('dialog').waitFor();await insets();await settle();
  const geometry=await page.evaluate(()=>({nav:document.querySelector('[data-nav="mobile"]').getBoundingClientRect().bottom,overlay:document.querySelector('[data-search-overlay]').getBoundingClientRect().top}));
  assert.ok(Math.abs(geometry.nav-geometry.overlay)<2,JSON.stringify(geometry));const safe=await bounds();for(const a of safe.links) assert.ok(a.x>=32&&a.right<=358,JSON.stringify(a));await shot('search-insets');
  await page.getByRole('searchbox',{name:'Search query'}).fill('poster');
  const layoutHeight=await page.evaluate(()=>innerHeight);
  await page.evaluate(()=>{Object.defineProperty(visualViewport,'height',{configurable:true,get:()=>420});visualViewport.dispatchEvent(new Event('resize'));});await settle();
  const visualOnly=await page.locator('[data-search-overlay]').boundingBox();assert.ok(visualOnly.y+visualOnly.height<=421);assert.equal(await page.evaluate(()=>innerHeight),layoutHeight);await shot('simulated-visual-only-keyboard');
  await page.evaluate(()=>{delete visualViewport.height;visualViewport.dispatchEvent(new Event('resize'));});await settle();
  // Viewport reduction is a layout defense test, not a real OS keyboard.
  await page.setViewportSize({width:390,height:480});await settle();
  const o=await page.locator('[data-search-overlay]').boundingBox();assert.ok(o.y+o.height<=481);
  await page.getByRole('button',{name:'Close search',exact:true}).scrollIntoViewIfNeeded();await shot('search-reduced-viewport');
  await page.setViewportSize({width:390,height:844});await settle();
  await page.getByRole('button',{name:'Close search',exact:true}).click();await page.waitForURL(base+'/');await settle();
  assert.equal(await page.getByRole('dialog').count(),0);assert.ok(Math.abs((await page.evaluate(()=>scrollY))-y)<3);
  assert.notEqual(await page.evaluate(()=>document.body.style.overflow),'hidden');await shot('search-closed');
 });
 await run('Landscape safe content and navigation',async()=>{
  await page.goto(base+'/about');await page.setViewportSize({width:844,height:390});await insets();await settle();
  const b=await bounds();assert.equal(b.overflow,false);for(const a of b.links){assert.ok(a.x>=32&&a.right<=812);assert.ok(a.y>=27&&a.bottom<=390);}
  await shot('about-landscape');await page.evaluate(()=>scrollTo(0,document.body.scrollHeight));await settle();await shot('about-bottom');
 });
 await run('Index object back and direct Search scroll',async()=>{
  await page.setViewportSize({width:390,height:844});await page.goto(base+'/directory');await settle();
  const link=page.locator('a[href^="/surfaces/"]').first();await link.waitFor();const href=await link.getAttribute('href');await link.click();await page.waitForURL('**/surfaces/**');await settle();await shot('object');
  assert.equal((await bounds()).overflow,false);await page.goBack();await page.waitForURL('**/directory**');await page.locator(`a[href="${href}"]`).first().waitFor();
  await Promise.all([page.waitForResponse(r=>r.url().includes('/api/system-suggestions/v1')),page.goto(base+'/search?q=poster')]);await settle();
  const scroll=await page.evaluate(()=>{const n=document.querySelector('[class*="SearchMobile_page"]');n.scrollTop=200;return {y:n.scrollTop,overflow:getComputedStyle(n).overflowY};});
  assert.equal(scroll.overflow,'auto');assert.ok(scroll.y>0);await shot('direct-search-scroll');
 });
 await run('Source, UA isolation and no page exceptions',async()=>{
  await page.goto(base+'/source');await settle();await shot('source');
  const desktop=await context.request.get(base+'/',{headers:{'user-agent':'Mozilla/5.0 (X11; Linux x86_64) Chrome/145'}});assert.doesNotMatch(await desktop.text(),/data-nav="mobile"/);
  assert.deepEqual(errors,[]);
 });
 await context.close();await browser.close();
}
console.log(JSON.stringify({passed:results.length-failures,failed:failures,evidence:out,realDevice:'NOT_RUN'}));
if(failures)process.exitCode=1;
