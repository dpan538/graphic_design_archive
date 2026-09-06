#!/usr/bin/env python3
"""Create a separate disposable TLS test service in a NEW private directory; never touches retained local data."""
from pathlib import Path
import os,secrets,hashlib,json,subprocess
import sys
root=Path(__file__).resolve().parents[2];d=Path(sys.argv[1]).resolve();d.mkdir(mode=0o700);os.umask(0o077);(d/'data').mkdir();app=secrets.token_hex(32);admin=secrets.token_hex(32)
(d/'users.acl').write_text(f'user default off ~test:mgda:redis-readiness:* -@all +incr +pexpireat +del +set +select +multi +exec\nuser mgda on #{hashlib.sha256(app.encode()).hexdigest()} ~test:mgda:redis-readiness:* -@all +ping +info +select +quit +client|setinfo +client|setname +eval +incr +pexpire +pttl\nuser operator on #{hashlib.sha256(admin.encode()).hexdigest()} ~* &* +@all\n')
(d/'redis.conf').write_text((root/'.local/redis-integration/redis.conf').read_text())
(d/'runtime.json').write_text(json.dumps({'url':f'rediss://mgda:{app}@localhost:16421/0','operator':f'rediss://operator:{admin}@localhost:16421/0'}))
for p in d.glob('*'):
 if p.is_file():p.chmod(0o600)
subprocess.run(['docker','run','-d','--name','mgda-redis-readiness-test','--label','mgda.purpose=isolated-redis-readiness','--user',f'{os.getuid()}:{os.getgid()}','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','-p','127.0.0.1:16421:6379','-v',f'{d}/redis.conf:/config/redis.conf:ro','-v',f'{d}/users.acl:/config/users.acl:ro','-v',f'{root}/.local/redis-integration/tls/ca.crt:/tls/ca.crt:ro','-v',f'{root}/.local/redis-integration/tls/server.crt:/tls/server.crt:ro','-v',f'{root}/.local/redis-integration/tls/server.key:/tls/server.key:ro','-v',f'{d}/data:/data','--entrypoint','/usr/local/bin/redis-server','redis@sha256:ff02b58f971e7d7d156a1267e283fcbbeee91773b6aa36c49dac28ecfe28eadf','/config/redis.conf'],check=True,stdout=subprocess.DEVNULL)
print('ISOLATED_TEST_REDIS_STARTED=true')
