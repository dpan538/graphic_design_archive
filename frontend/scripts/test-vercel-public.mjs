import assert from "node:assert/strict";
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,existsSync,symlinkSync,rmSync} from "node:fs";
import {tmpdir} from "node:os";
import {join,resolve} from "node:path";
import {spawnSync} from "node:child_process";
const script=resolve(import.meta.dirname,"prepare-vercel-public.mjs"),geo="trace-spacetime-v1/natural-earth-50m-admin0-v5.1.1.geojson";
let checks=0;
for(const mode of ["normal","unknown","symlink","unguarded"]){const dir=mkdtempSync(join(tmpdir(),"mgda-public-contract-"));try {mkdirSync(join(dir,"public/data"),{recursive:true});mkdirSync(join(dir,"public",geo,".."),{recursive:true});writeFileSync(join(dir,"public/data/frozen.json"),"HELD_FIXTURE");writeFileSync(join(dir,"public",geo),"{}");if(mode==="unknown")writeFileSync(join(dir,"public/secret.env"),"REJECT_FIXTURE");if(mode==="symlink")symlinkSync(join(dir,"public/data/frozen.json"),join(dir,"public/leak"));
const result=spawnSync(process.execPath,[script],{cwd:dir,env:{...process.env,VERCEL:"0",MGDA_EPHEMERAL_BUILD:mode==="unguarded"?"0":"1"},encoding:"utf8"});assert.equal(result.status===0,mode==="normal");if(mode==="normal"){assert.equal(readFileSync(join(dir,".mgda-private-public/data/frozen.json"),"utf8"),"HELD_FIXTURE");assert.ok(!existsSync(join(dir,"public/data")));assert.equal(spawnSync(process.execPath,[script],{cwd:dir,env:{...process.env,MGDA_EPHEMERAL_BUILD:"1"}}).status,0);}checks++;} finally{rmSync(dir,{recursive:true,force:true});}}
console.log(`VERCEL_PUBLIC_CONTRACT=PASS checks=${checks}`);
