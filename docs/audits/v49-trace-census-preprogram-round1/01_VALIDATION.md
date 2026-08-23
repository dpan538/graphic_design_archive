# Validation Evidence

The final command receipts are recorded here after running from the isolated worktree. The package is valid only when every required gate below is `PASS` and protected-surface diffs are empty.

| Gate | Command/evidence | Result |
|---|---|---|
| clean dependency install | `npm ci` | PASS; 145 packages |
| typecheck | `npx tsc --noEmit --pretty false` | PASS |
| TRACE invariants | `node scripts/verify-trace-v49-preprogram.mjs` | PASS; 19 checks, all 16 required invariants |
| TRACE capacity benchmark | `node --expose-gc scripts/trace-v49-analysis/benchmark_trace_v49_preprogram.mjs ...` | PASS; 15 cases; max projection P95 0.035545 ms |
| deterministic statistics rebuild | generator normal run then two `--check` runs | PASS; both checks reported 15,923/7,995/7,928, 47,982 assignments, 0 relations |
| protected search index | `npm run verify:search-v49-index` | PASS; 7,995 documents; index SHA `35a6b7e...b1522` |
| search regression | `npm run test:search-v49` | PASS; 14 checks; 7,995 documents |
| API tests | `npm run test:read-platform` | PASS; direct data coupling 0 |
| retained v48 verifier | `npm run verify:trace-visualization` | PASS; all 23 checks; inspected only, no legacy files changed |
| production build | `npm run build` | PASS; 46 static/dynamic routes generated; `/trace` unchanged at 176 B route module |
| diff hygiene | `git diff --cached --check` | PASS |
| current `/trace` before/after | local browser smoke | PASS; same title/message/zero count, HTTP 200, no warning/error logs |
| database/canonical/search/v48 route scope | explicit path diff checks and staged-path inventory | PASS; zero protected-path diffs; only authorized new TRACE paths staged |

Known pre-existing/out-of-scope test gaps are documented rather than hidden:

- the runtime acceptance vector runner currently fails before TRACE because Search scope defaults differ between controller and direct fixture calls;
- current derived-v49 empty TRACE list handling bypasses declared layer/page/cursor validation;
- retained v48 verification is not validation of current `/trace`.
