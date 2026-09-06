import {readFileSync,readdirSync,existsSync} from "node:fs";
import {resolve,join} from "node:path";
const root=resolve(process.argv[2]??process.cwd());
const known=new Set(JSON.parse(readFileSync(join(root,"generated/reader-eligibility-v49/eligibility.json"))).entries.map(x=>x[0]));
let files=0,bytes=0;
function walk(dir){if(!existsSync(dir))throw Error("Missing public artifact directory");for(const entry of readdirSync(dir,{withFileTypes:true})){const p=join(dir,entry.name);if(entry.isSymbolicLink())throw Error("Public symlink rejected");if(entry.isDirectory()){walk(p);continue;}const data=readFileSync(p),text=data.toString();for(const id of text.match(/SURF-[A-Z0-9_-]{6,}/g)??[])if(!known.has(id))throw Error("Non-public stable ID in artifact: "+p);if(/(?:sk-[A-Za-z0-9]{24,}|rediss?:\/\/[^\s"']*:[^\s"']*@)/.test(text))throw Error("Credential pattern in artifact: "+p);files++;bytes+=data.length;}}
walk(join(root,"public"));walk(join(root,".next/static"));console.log(JSON.stringify({status:"PASS",files,bytes,publicIdentityCount:known.size}));
