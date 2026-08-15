# R1 runtime gate audit

## Scope and method

This is a read-only inspection of commit `6e66186f2626bd10272b3cd408778f2ac091a598` before runtime-acceptance implementation. No npm, Next, TypeScript compiler, PostgreSQL, browser, generator, commit, or push was run by this reviewer. The protected legacy main was not entered or modified.

### Inspected paths

- `.github/workflows/pr-fast.yml`, `.github/workflows/small-db-integration.yml`, `.github/workflows/manual-full-rehearsal.yml`, and `.github/workflows/audit-package-self-contained.yml`
- `frontend/package.json`, `frontend/tsconfig.json`, `frontend/scripts/verify-read-platform-contract.mjs`
- `frontend/src/lib/read-platform/{types,repository,pagination,http-repository}.ts`
- `frontend/src/lib/read-platform/server/{fixture,provider,open-read-repository,postgres-repository}.ts`
- `frontend/src/lib/read-platform/test-fixtures.ts` and `frontend/src/app/api/v1/[...path]/route.ts`
- `frontend/src/app/{search,folders/[type],folders/[type]/[slug],surfaces/[id],trace}/page.tsx`
- `frontend/src/components/archive/{read-platform/ReadPlatformViews.tsx,shell/ArchiveShell.tsx,shell/ArchiveShell.module.css}` and `frontend/src/app/globals.css`
- `database/scripts/run-phase2c-small-db-integration.sh`, `database/fixtures/phase2c_32_base.sql`, `database/tests/002_release_seal_cas.sql`, `database/migrations/009_read_api_core.sql`, `database/roles/003_read_api_core_grants.sql`, and `database/scripts/replay.sh`
- `docs/audits/v49-product-foundation/00_PHASE2C2D_CHECKPOINT_RECEIPT.md`

### Commands actually run

```text
git -C /private/tmp/graphic_design_archive_v49_read_platform rev-parse HEAD
git -C /private/tmp/graphic_design_archive_v49_read_platform ls-tree -r --name-only HEAD -- .github frontend database docs/audits/v49-product-foundation
sed -n on the inspected source, workflow, fixture, migration, and receipt files
rg -n on the inspected frontend/database paths for runtime coupling and wording
git -C /private/tmp/graphic_design_archive_v49_read_platform worktree list --porcelain
git status --short
```

## Findings

### P0 — 0

No P0 security or integrity breach was found by static inspection. The fixture provider is server-only, explicitly requires `ARCHIVE_REPOSITORY_MODE=fixture`, and refuses fixture selection when `NODE_ENV=production`. The public fixture DTO has no locator or pixel field; the held sentinel remains isolated in `test-fixtures.ts`.

### P1 — 5 runtime-gate gaps

1. **The PR-fast TypeScript step is not affected-only.** `frontend/package.json` maps `typecheck:affected` to `tsc --noEmit --pretty false`; its `tsconfig.json` includes all `**/*.ts` and `**/*.tsx`. `.github/workflows/pr-fast.yml` invokes that misleading name after the static contract script. Create an explicitly named narrow runtime tsconfig/script containing the read-platform contract/adapters, API route, the five migrated routes and their imported closure; update the workflow to call that explicit script. Do not label the full-project command as affected.

2. **There is no runtime query-vector suite.** `verify-read-platform-contract.mjs` checks source text only. It does not execute Fixture, Postgres, or HTTP adapters; it does not exercise cursors, cancellation, method handling, error mapping, or canonical JSON parity. Add one runtime vector runner and preserve the static guard as a separate preliminary check.

3. **Postgres and fixture implementations are not yet parity-equivalent.** `PostgresArchiveRepositoryProvider.open()` rejects a `current` selector, returns no folder types/folders/members, and projects only exact descriptor/surface data. `FixtureArchiveRepository` resolves `current`, has one `region` folder type/four folders/32 objects, and supports two-page keysets. The current adapters therefore cannot produce equal vectors without a compact sealed projection plus an explicit one-time current resolver in the Postgres path.

4. **HTTP cannot currently be tested through a real in-process route dispatcher.** `HttpArchiveRepository` binds directly to global `fetch`; `dispatch` in the API route is private. Introduce only a small injected fetch seam and a shared/exported route dispatcher that accepts real `Request` and returns real `Response`. The test must call that shared implementation, not copy API behavior.

5. **Do not re-run the existing small-DB wrapper as this round's parity proof.** `database/tests/002_release_seal_cas.sql` does correctly `\\ir ../fixtures/phase2c_32_base.sql`, copies all 32 objects, and proves the compact release count. However, it deliberately exercises the complete R1/V1/R2 Seal/CAS and ends with `ROLLBACK`; `database/scripts/run-phase2c-small-db-integration.sh` invokes that full test. The current task marks that Seal/CAS work already passed and forbids rerunning it. A runtime runner must use a fresh disposable cluster and a minimal, bounded setup that does not repeat the complete Seal/CAS protocol, or record a blocker rather than misrepresenting the old runner as a new runtime proof.

### P2 — 3 follow-ups

1. `frontend/src/app/trace/page.tsx` metadata still calls the selected data a “frozen v48 archive candidate”; change only this copy to v49/read-release-neutral wording.
2. `frontend/src/app/not-found.tsx` says “current staged pool”; change only this copy to “selected sealed release” wording.
3. The mobile-menu target-size requirement needs runtime measurement. Global styles define `2.7rem` / later `3.25rem` mobile rules, while the CSS module declares `3rem`; static source does not prove the required final 48px ±1 geometry, panel width, or item count.

## Runtime/public-boundary observations

- The API route has explicit GET/HEAD/OPTIONS support and a 405 path for writes. Its emitted envelope carries the exact research pair and visual `null` state.
- The fixture is 32 objects, zero TRACE eligible, zero positive visual rights. Its TRACE atlas is explicitly zero and neighborhood returns `NOT_FOUND`, so an accepted runtime vector can prove an honest empty state rather than inferred graph data.
- The static fixture sentinel is `HELD_SENTINEL_URL` in a test-only file. Browser/API/HTML/chunk/network scans remain mandatory runtime evidence; static isolation alone cannot produce zero match counts.
- The existing checkpoint correctly states that dev-listener/browser evidence is absent. Do not upgrade any browser, accessibility, reduced-motion, network, bundle, or screenshot status until a long-lived PTY listener and local browser session actually execute.

## Conclusion

`6e66186` is a suitable fixed source for the requested runtime-resume work, but it does **not** yet satisfy runtime parity, narrow TypeScript, or browser acceptance. The minimum justified implementation is: explicit narrow type gate; a real shared API dispatcher plus injected HTTP fetch; a bounded three-adapter vector suite over one disposable compact release; then the prescribed one-listener local browser evidence. No product-surface expansion is indicated by this audit.

```text
R1_CONCLUSION=RUNTIME_GATES_REQUIRE_IMPLEMENTATION_AND_EXECUTION
P0_COUNT=0
P1_COUNT=5
P2_COUNT=3
```
