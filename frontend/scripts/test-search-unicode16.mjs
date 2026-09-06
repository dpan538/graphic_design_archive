import {createRequire} from 'node:module';import {createHash} from 'node:crypto';import fs from 'node:fs';
const root=new URL('..',import.meta.url).pathname.replace(/\/$/,'');const require=createRequire(root+'/package.json');const jiti=require('jiti')(import.meta.url,{alias:{'@':root+'/src','server-only':root+'/scripts/server-only-stub.mjs'}});
const path=root+'/src/features/search-v49/core.ts';
const core=await jiti.import(path);const hash=createHash('sha256');let cases=0;
function add(s){hash.update(JSON.stringify([core.caseFoldV1(s),core.normalizeSearchText(s),core.normalizeSearchText(s,'NFKC'),core.foldLatinDiacritics(s)])+'\n');cases++;}
for(let cp=0;cp<=0x10ffff;cp++){const c=String.fromCodePoint(cp);add(c);add('A'+c+'\u0301Σ');}
for(const tuple of JSON.parse(fs.readFileSync(root+'/generated/search-v2/documents.json')).documents)for(const i of [0,1,2,6])if(typeof tuple[i]==='string')add(tuple[i]);
for(const s of ['ΟΣ ΟΣΑ ΣΣ','IİıißẞςΣ','production production site','education design education','1,898 1980','École E\u0301cole','\u1100\u1161\u11a8','\uD800A\uDC00','A\u{1E6D0}\u0301','A\u{1CCD6}\u0301'])add(s);
const reference=JSON.parse(fs.readFileSync(new URL('./fixtures/search-unicode16-reference.json',import.meta.url)));
const result={node:process.version,unicode:process.versions.unicode,cases,digest:hash.digest('hex')};if(result.cases!==reference.cases || result.digest!==reference.digest)throw Error('Released Unicode 16 semantics changed');console.log(JSON.stringify({status:'PASS',...result}));if(process.env.MGDA_UNICODE_OUTPUT)fs.writeFileSync(process.env.MGDA_UNICODE_OUTPUT,JSON.stringify(result,null,2)+'\n');
