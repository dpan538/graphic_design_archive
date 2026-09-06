// Safe process-only injection. No secret is printed, copied into a build, or passed as argv.
import {readFileSync,statSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve,dirname} from 'node:path';
import {createRequire} from 'node:module';
import {spawn} from 'node:child_process';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..'),frontend=resolve(root,'frontend');
export function localEnvironment(){
 const path=resolve(root,'.local/redis-integration/runtime.json');
 if((statSync(path).mode&0o077)!==0)throw Error('PRIVATE_CONFIG_PERMISSIONS_REQUIRED');
 const config=JSON.parse(readFileSync(path,'utf8'));
 if(new URL(config.REDIS_URL).protocol!=='rediss:'||!config.SYSTEM_SUGGESTIONS_IDENTITY_SECRET||config.SYSTEM_SUGGESTIONS_IDENTITY_SECRET.length<32)throw Error('LOCAL_TLS_AND_STABLE_IDENTITY_REQUIRED');
 if(process.env.NODE_TLS_REJECT_UNAUTHORIZED==='0')throw Error('TLS_CERTIFICATE_VERIFICATION_REQUIRED');
 const require=createRequire(import.meta.url);
 require('@next/env').loadEnvConfig(frontend,true,{info(){},error(){}});
 return {...process.env,...config};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 const env=localEnvironment();
 console.log(JSON.stringify({KEY_PRESENT:!!env.DEEPSEEK_API_KEY?.trim(),LOCAL_REDIS_CONFIG_PRESENT:true,namespace:env.SYSTEM_SUGGESTIONS_RATE_LIMIT_NAMESPACE,identity_mode:env.SYSTEM_SUGGESTIONS_TRUSTED_IP_HEADER?'configured-header':'anonymous-shared',protocol:new URL(env.REDIS_URL).protocol}));
 const args=process.argv.slice(2);if(!args.length)throw Error('Supply a command, e.g. node scripts/redis-health.mjs');
 const child=spawn(args[0],args.slice(1),{env,stdio:'inherit'});
 for(const sig of ['SIGINT','SIGTERM'])process.on(sig,()=>child.kill(sig));
 child.on('error',()=>{console.error('CHILD_PROCESS_START_FAILED');process.exitCode=1});
 child.on('exit',code=>process.exitCode=code??1);
}
