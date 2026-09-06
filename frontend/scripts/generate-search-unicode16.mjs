import fs from 'node:fs';import crypto from 'node:crypto';
if(process.versions.unicode!=='16.0')throw Error('Unicode 16 host required');
const ranges={assigned:[],mark:[],latin:[],separator:[],number:[]};const patterns={assigned:/\p{Assigned}/u,mark:/\p{M}/u,latin:/\p{Script=Latin}/u,separator:/[\p{P}\p{S}]/u,number:/\p{N}/u};const lower={};
for(let cp=0;cp<=0x10ffff;cp++){const c=String.fromCodePoint(cp);for(const [name,re] of Object.entries(patterns)){if(re.test(c)){const a=ranges[name],last=a.at(-1);if(last&&last[1]===cp-1)last[1]=cp;else a.push([cp,cp]);}}const folded=c.toLowerCase().replaceAll('ß','ss').replaceAll('ς','σ');if(folded!==c)lower[cp]=folded;}
const data={unicode:'16.0',ranges,lower};const text=JSON.stringify(data)+'\n';const output=new URL('../generated/search-unicode16/properties.json',import.meta.url);
if(process.argv.includes('--check')) { if(fs.readFileSync(output,'utf8')!==text)throw Error('Unicode 16 property artifact mismatch'); } else {fs.mkdirSync(new URL('../generated/search-unicode16/',import.meta.url),{recursive:true});fs.writeFileSync(output,text);}
console.log(JSON.stringify({bytes:text.length,hash:crypto.createHash('sha256').update(text).digest('hex'),ranges:Object.fromEntries(Object.entries(ranges).map(([k,v])=>[k,v.length])),lower:Object.keys(lower).length}));
