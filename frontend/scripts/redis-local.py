#!/usr/bin/env python3
"""Persistent LOCAL TLS Redis. init/up/status/stop/restart; never deletes data."""
from pathlib import Path
import os,sys,subprocess,secrets,hashlib,json
ROOT=Path(__file__).resolve().parents[2];STATE=ROOT/'.local/redis-integration'

def run(args):
 subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def save(path,text):
 path.write_text(text);path.chmod(0o600)
def initialize():
 if STATE.exists():
  if not (STATE/'runtime.json').exists():raise RuntimeError('Incomplete initialization: inspect private state; never replace existing credentials automatically')
  print('LOCAL_CONFIG_PRESENT=true; existing credentials preserved');return
 run(['git','check-ignore',str(STATE/'runtime.json')])
 os.umask(0o077);STATE.mkdir(parents=True,mode=0o700);(STATE/'tls').mkdir();(STATE/'data').mkdir()
 tls=STATE/'tls'
 run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-sha256','-days','365','-subj','/CN=MGDA local integration CA','-keyout',str(tls/'ca.key'),'-out',str(tls/'ca.crt')])
 run(['openssl','req','-newkey','rsa:2048','-nodes','-subj','/CN=localhost','-keyout',str(tls/'server.key'),'-out',str(tls/'server.csr')])
 save(tls/'extensions.cnf','subjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth\n')
 run(['openssl','x509','-req','-in',str(tls/'server.csr'),'-CA',str(tls/'ca.crt'),'-CAkey',str(tls/'ca.key'),'-CAcreateserial','-days','365','-sha256','-extfile',str(tls/'extensions.cnf'),'-out',str(tls/'server.crt')])
 app=secrets.token_hex(32);admin=secrets.token_hex(32)
 namespace='mgda:local:system-suggestions:v1'
 save(STATE/'users.acl',f'user default off ~mgda:local:system-suggestions:v1:* -@all +incr +pexpireat +del +set +select +multi +exec\nuser mgda on #{hashlib.sha256(app.encode()).hexdigest()} ~{namespace}:* -@all +ping +info +select +quit +client|setinfo +client|setname +eval +incr +pexpire +pttl\nuser operator on #{hashlib.sha256(admin.encode()).hexdigest()} ~* &* +@all\n')
 save(STATE/'redis.conf','''bind 0.0.0.0
protected-mode yes
port 0
tls-port 6379
tls-cert-file /tls/server.crt
tls-key-file /tls/server.key
tls-ca-cert-file /tls/ca.crt
tls-auth-clients no
aclfile /config/users.acl
dir /data
maxmemory 64mb
maxmemory-policy noeviction
appendonly yes
appendfsync everysec
save ""
''')
 save(STATE/'runtime.json',json.dumps({'REDIS_URL':f'rediss://mgda:{app}@localhost:16420/0','SYSTEM_SUGGESTIONS_RATE_LIMIT_NAMESPACE':namespace,'SYSTEM_SUGGESTIONS_IDENTITY_SECRET':secrets.token_hex(32),'SYSTEM_SUGGESTIONS_TRUSTED_IP_HEADER':'','NODE_EXTRA_CA_CERTS':str(tls/'ca.crt')},indent=2))
 save(STATE/'operator.json',json.dumps({'url':f'rediss://operator:{admin}@localhost:16420/0'}))
 save(STATE/'compose.env',f'MGDA_REDIS_STATE={STATE}\nMGDA_REDIS_UID={os.getuid()}\nMGDA_REDIS_GID={os.getgid()}\n')
 print('LOCAL_CONFIG_CREATED=true; secrets stored privately; namespace stable')

def compose(*args):
 subprocess.run(['docker','compose','--env-file',str(STATE/'compose.env'),'-f',str(ROOT/'ops/redis/compose.yaml'),*args],check=True)
try:
 action=sys.argv[1] if len(sys.argv)>1 else 'status'
 if action=='init':initialize()
 elif action=='up':initialize();compose('up','-d')
 elif action=='stop':compose('stop')
 elif action=='restart':compose('restart')
 elif action=='status':compose('ps')
 else:raise ValueError('Use init/up/status/stop/restart; data destruction deliberately unsupported')
except Exception as error:
 print('LOCAL_REDIS_OPERATION_FAILED='+type(error).__name__,file=sys.stderr);sys.exit(1)
