# MGDA retained LOCAL Redis

This is a retained local integration service, not production infrastructure. No external platform, private network or per-requester ingress contract is approved yet.

From repository root:

```sh
python3 frontend/scripts/redis-local.py up
node frontend/scripts/redis-runtime.mjs node frontend/scripts/redis-health.mjs
python3 frontend/scripts/redis-local.py status
python3 frontend/scripts/redis-local.py stop
python3 frontend/scripts/redis-local.py up
```

`up` initializes once and preserves existing credentials, namespace and data on subsequent calls. `stop` preserves data. `restart` performs a graceful process restart; it is not a data reset. There is intentionally no destructive reset/down-volume command. Run Docker Desktop before `up`. The fixed Redis 7.4.11 image is already available locally; on another host install the reviewed digest explicitly before running (pull_policy is never).

**Retained service:** Compose project `mgda-redis-integration`; container `mgda-redis-integration-redis-1`; TLS at localhost:16420, published only on 127.0.0.1. Runs with host UID/GID, read-only root filesystem, dropped capabilities. The private bind data directory is `.local/redis-integration/data` (persistent volume semantics). Do not delete it during QA cleanup. Docker restart policy is unless-stopped; Docker itself must be running.

**Private configuration:** `.local/redis-integration/runtime.json` contains stable app credentials and identity secret, `operator.json` separate management credentials, and `users.acl` password hashes. Files are mode 600; state directories mode 700 and Git ignored. Never print, stage, copy into frontend/public, or upload these. The app uses `redis-runtime.mjs` for process-only injection; the existing `frontend/.env.local` is loaded read-only for DeepSeek. The identity secret and `mgda:local:system-suggestions:v1` namespace are not regenerated at app restart or tied to build ID/PID/time. Test URLs are never written into retained application configuration.

**TLS:** A private local CA issues the localhost/127.0.0.1 server certificate. The wrapper supplies `NODE_EXTRA_CA_CERTS` to a fresh child Node process, retaining certificate verification. The CA private key is not mounted into Redis. Certificates currently have a one-year lifetime; monitor expiry and renew before it ends. Keep the CA private key protected; re-sign a replacement localhost certificate with the same CA and restart gracefully, or explicitly rotate trust and certificates together. Never use NODE_TLS_REJECT_UNAUTHORIZED=0.

**ACL:** Application `mgda` has only INFO/PING/SELECT/QUIT, connection initialization, and EVAL/INCR/PEXPIRE/PTTL on the local namespace. It cannot CONFIG, FLUSHDB, read other namespaces or manage users. The operator credential is separate. Default user is OFF with no password: cannot authenticate. It has only the namespaced commands required by AOF replay (INCR/PEXPIREAT/DEL/SET/SELECT/MULTI/EXEC). On this Redis version a default OFF user without these replay permissions caused acknowledged Lua writes/TTL to fail restoration; the isolated regression caught and verified the correction. Do not remove replay permissions without a restart regression, and never enable the default user to fix replay.

**Memory/durability:** 64 MiB, noeviction. OOM rejects writes and the app returns LIMITER_UNAVAILABLE without starting provider requests. AOF is enabled with everysec fsync, RDB periodic snapshots disabled. Graceful restart and same-host SIGKILL were tested to retain the current counter and TTL. These do not prove durability under host power loss or managed failover: recent writes can be lost (typically up to the fsync interval), and the restored quota could then be larger. This limiter is not a global daily spend cap. On recovery do not delete counters; they expire naturally after 60 seconds. Treat persistence errors as operational faults. Store any backups of private state securely outside Git/public artifacts, and restore config + data as a matched set with the service stopped; backups of old counters are not a guarantee of a live current quota.

**Monitoring:** Docker health verifies TLS listener/auth challenge every 15 seconds. `redis-health.mjs` performs authenticated app checks and reports bounded connect latency, connections, memory/maxmemory/noeviction, evictions, AOF and error counters without credentials. Alert operationally if unhealthy, AOF write status not ok, evicted_keys nonzero, memory approaching limit, or rejected/error counts rising. The Docker liveness challenge intentionally produces NOAUTH; exclude that expected background count when assessing error deltas. Authenticated health failures and unexpected command errors need attention. Authentication/ACL rejections in deliberate tests are not a production baseline. Platform alert delivery and capacity sizing remain to be configured after target selection.

## Run the clean production-mode application locally

Build and package via the existing Webpack path and `package-release.py`; never publish this ops directory or the private config. For the package already verified in this run:

```sh
cd /private/tmp/mgda-redis-release-v1/private-runtime
node /Users/jarlgiovanni/Desktop/modern_GD_history_frontend_redesign/frontend/scripts/redis-runtime.mjs npm run start -- --hostname 127.0.0.1 --port 3000
```

The temporary verified package can be reclaimed by the OS; the Redis service/config/data are retained in the project. Rebuild from the recorded source identity when needed. This ordinary start command has no QA cache bypass, fault injection or paid-call instrumentation. Stop the application with Ctrl-C; Redis continues running and counters are preserved. Do not expose this development machine to the internet.

The trusted-header setting is intentionally empty. Untrusted forwarding headers are ignored and all anonymous requests share one safe bucket. It is **not** production-ready per-person identity. The eventual ingress must strip/overwrite one exact trusted IP header and prevent origin bypass; confirm this before configuring that header.

## Isolated destructive acceptance (not the retained service)

Create a NEW temporary directory and the separate fixed test container. Never reuse a production URL:

```sh
python3 frontend/scripts/redis-isolated-test.py /private/tmp/mgda-redis-test-new-run
MGDA_ISOLATED_REDIS_CONFIG=/private/tmp/mgda-redis-test-new-run/runtime.json \
MGDA_OWNED_REDIS_CONTAINER=mgda-redis-readiness-test \
MGDA_REDIS_QA_DIR=/private/tmp/mgda-redis-test-new-run/results \
node frontend/scripts/redis-runtime.mjs node frontend/scripts/verify-redis-readiness.mjs
```

`runtime.json` inside this isolated directory supplies the test-only application/operator URLs; the retained runtime.json does not. `SYSTEM_SUGGESTS_TEST_REDIS_URL` remains exclusively a test-runner variable when using the older regression runner; never substitute it for retained REDIS_URL. The extended runner tests app ACL, cold two-process HTTP, four surfaces, spoofing, real 60-second expiry, restart, OOM, auth/TTL/slow failures with a fake provider. It deletes only its test namespace. It intentionally pauses/restarts **only** `mgda-redis-readiness-test`. Remove that container after tests only after confirming its identity/label; retain `mgda-redis-integration-redis-1` and its data.

## Rollback and production handoff

Cold-connect application fix is limited to rate-limiter.server.ts. Reverting it restores the previously observed 99/100 cold-request degradation; it is not recommended as an operational recovery step. An app rollback must keep the same Redis URL, namespace and identity secret, and must not clear Redis. Do not roll back to the first ACL file that failed AOF replay.

Owner has chosen “finish local handoff”. Before production: approve the specific application host and region, Redis target and cost ceiling/access, shared secret injection, private/TLS network path, noeviction/equivalent and recovery policy, ingress overwrite + origin isolation, health alerting and protected remote smoke. No paid resource or public deployment is authorized by these local scripts.

## Vercel hosted connection

The current vendor-neutral Import contract is [../vercel/README.md](../vercel/README.md). This local TLS service is retained for local integration only; no Upstash account binding is required. Never put its loopback endpoint into Vercel.
