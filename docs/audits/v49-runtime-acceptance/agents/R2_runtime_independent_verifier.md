# R2 independent runtime-acceptance verifier

## Scope and independence

This is a read-only review of the uncommitted runtime-acceptance worktree state
on `verify/v49-read-platform-runtime-acceptance-20260815`, based at
`6e66186f2626bd10272b3cd408778f2ac091a598`.  I did not run npm, Next,
TypeScript, PostgreSQL, a browser, a generator, a commit, or a push.  I did not
enter or modify the protected legacy main.  Consequently, this report does not
promote a static observation into runtime evidence.

## Inspected paths

- `.github/workflows/pr-fast.yml`
- `frontend/package.json`, `frontend/tsconfig.runtime-acceptance.json`, and
  `frontend/scripts/verify-read-platform-contract.mjs`
- `frontend/scripts/run-runtime-acceptance-vectors.mjs` and its test-only
  `frontend/scripts/runtime-stubs/server-only/index.js` resolver shim
- `frontend/src/app/api/v1/[...path]/route.ts`
- `frontend/src/lib/read-platform/http-repository.ts`
- `frontend/src/lib/read-platform/server/{fixture,postgres-repository}.ts`
- `frontend/src/lib/read-platform/test-fixtures.ts`
- `frontend/src/app/{not-found,trace}/page.tsx`
- `docs/audits/v49-runtime-acceptance/` and
  `docs/audits/v49-runtime-acceptance/agents/R1_runtime_gate_audit.md`

## Commands actually run

```text
git status --short
git branch --show-current
git log --oneline --decorate -5
rg --files docs/audits/v49-runtime-acceptance frontend .github | sed -n '1,240p'
git diff -- <runtime implementation paths>
sed -n on the R1 report and inspected implementation files
find docs/audits/v49-runtime-acceptance -maxdepth 3 -type f -print | sort
git diff --check
git ls-files --error-unmatch frontend/package-lock.json
```

All commands were read-only inspection commands.  `git diff --check` reported
no whitespace error in the observed working changes.

## Findings

### P0 — 0

No P0 finding was established by this static review.  In particular, the held
sentinel remains in `test-fixtures.ts`, and the new route seam takes a provider
explicitly.  These are implementation observations only; five-layer public
boundary verification remains unexecuted.

### P1 — 5

1. **Postgres runtime parity is still absent.**
   `run-runtime-acceptance-vectors.mjs` constructs and compares only
   `FixtureArchiveRepositoryProvider` and `HttpArchiveRepositoryProvider`.
   It creates no disposable PostgreSQL cluster and never imports or opens
   `PostgresArchiveRepositoryProvider`.  The existing Postgres implementation
   continues to reject `current`, return empty folder/folder-member projections,
   and differ from the 32-object fixture.  It cannot support the required
   three-adapter canonical digest assertion as inspected.

2. **The new Fixture/HTTP vector has a deterministic release-pair mismatch
   disagreement.**  A mismatched exact pair reaches the fixture API dispatcher
   as `RELEASE_NOT_FOUND` (HTTP 404).  `HttpArchiveRepositoryProvider.open()`
   maps every non-OK descriptor response, including that 404, to
   `UNAVAILABLE`.  The vector's `paired("release-pair-mismatch", ...)` compares
   those error codes, so it should fail rather than prove parity until the
   transport preserves the typed error semantics.

3. **The vector script emits several security/integrity result fields without
   performing their corresponding checks.**  Its final payload hard-codes
   `heldLocatorApiLeakCount: 0`, `rawPayloadApiLeakCount: 0`, and
   `unknownRelationFailClosed: true`.  The script does not scan serialized API
   responses for the held sentinel or raw payload fields, and it does not make a
   direct unknown-relation request.  These fields must not be used as evidence
   until real assertions and transcripts exist.

4. **No executable PR-fast or narrow-TypeScript transcript exists yet.**
   The workflow now calls the accurately named `typecheck:runtime` and the
   tsconfig explicitly lists the read-platform/API/migrated-slice entry files,
   which is a constructive change.  `test:read-platform` remains a static text
   guard, however, and the audit directory currently contains only R1's report
   and this review.  There is no exit code, duration, stdout, or stderr proving
   the required local PR-fast sequence or the narrow TypeScript gate.

5. **All live-listener, browser, accessibility, reduced-motion, network, DOM,
   bundle, and screenshot gates remain unverified.**  The audit directory has
   no dev-server transcript, listener/probe receipt, browser matrix, keyboard
   transcript, boundary scan, network log, or screenshot manifest.  It would be
   incorrect to report any browser/public-boundary zero count, eight-screen
   uniqueness result, menu geometry, or touch-swipe result at this point.

### P2 — 2

1. The targeted v48 TRACE metadata and “staged pool” wording changes are
   present and confined to their two stated page files.
2. The test-only `server-only` resolver shim is untracked and visible in the
   current implementation state.  Before any commit, its role and scope should
   be documented as test-only, and its path should be explicitly staged if it
   is retained; it must not be mistaken for application runtime evidence.

## Gate conclusion

The narrow typecheck wiring and in-process HTTP seam are useful prerequisites,
but the required runtime record is not yet present.  The static release-pair
error mismatch is sufficient to block a successful Fixture/HTTP parity claim;
the Postgres adapter has not been included at all.  Browser and public-boundary
acceptance are also strictly `UNVERIFIED` until a persistent local listener and
the prescribed local-browser evidence actually run.

```text
R2_CONCLUSION=RUNTIME_ACCEPTANCE_NOT_YET_VERIFIED
P0_COUNT=0
P1_COUNT=5
P2_COUNT=2
POSTGRES_ADAPTER_RUNTIME_PASS=UNVERIFIED
FIXTURE_HTTP_RUNTIME_PARITY=BLOCKED_TYPED_ERROR_MISMATCH
LIVE_NEXT_HTTP_VERIFIED=UNVERIFIED
BROWSER_VERIFIED=UNVERIFIED
PUBLIC_BOUNDARY_FIVE_LAYER_STATUS=UNVERIFIED
```
