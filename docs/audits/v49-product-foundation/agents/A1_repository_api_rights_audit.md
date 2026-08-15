# Queue A1 — Repository/API, exact-version, serializer and rights-boundary audit

- Audit date: 2026-08-15
- Audited tree: `/private/tmp/graphic_design_archive_v49_read_platform`
- Audited commit: `60329e8ec713221bbf42318a4f4c7477e6eb5a72`
- Scope: read-only baseline inspection before the Phase 2C implementation. No implementation, Git, network, Node, Next, TypeScript, PostgreSQL, browser, or generator command was run by this auditor.

## Inspected paths

- `ARCHITECTURE.md`
- `DATA_MODEL_V49.md`
- `READ_API_V1.md`
- `ACCEPTANCE_GATES.md`
- `docs/adr/0001-canonical-postgres-and-read-only-release.md`
- `docs/adr/0002-immutable-data-versioning.md`
- `docs/adr/0003-runtime-repository-and-fixture-mode.md`
- `database/views/001_api_v1.sql`
- `database/functions/003_release_and_cas.sql`
- `database/functions/007_release_protocol_closure.sql`
- `database/tests/002_release_seal_cas.sql`
- `database/fixtures/phase2a_base.sql`
- `frontend/src/lib/archive-data.ts`
- `frontend/src/lib/archive-search-client.ts`
- `frontend/src/types/archive.ts`
- `frontend/src/app/search/page.tsx`
- `frontend/src/app/folders/[type]/page.tsx`
- `frontend/src/app/folders/[type]/[slug]/page.tsx`
- `frontend/src/app/surfaces/[id]/page.tsx`
- `frontend/src/app/trace/page.tsx`
- `frontend/src/components/archive/search/SearchWorkspace.tsx`
- `frontend/src/components/archive/trace/TraceExplorer.tsx`
- target-slice references under `frontend/src/app/{search,folders,trace}` and `frontend/src/components/archive/{search,trace}`.

## Actual read-only commands

```text
pwd; rg --files -g 'AGENTS.md' -g 'ARCHITECTURE.md' ... /private/tmp/graphic_design_archive_v49_read_platform
wc -l ARCHITECTURE.md DATA_MODEL_V49.md READ_API_V1.md ACCEPTANCE_GATES.md docs/adr/000{1,2,3}-*.md
sed -n on the normative documents listed above
rg --files frontend database .github
rg -n on repository/API/release/rights/TRACE/search terms under frontend, database and .github
sed -n on the frontend target slices and their data helpers
sed -n on database/views/001_api_v1.sql, release functions and release tests
rg --files frontend/src/app | rg '/api/'
rg --files frontend/src | rg -i 'repository|fixture|api-v1|api_v1'
rg -n on direct frozen-data imports/fetches in the three target slices
git status --short; git rev-parse HEAD
```

## Normative contract recovered from the specifications

1. Every read is bound to an exact `researchReleaseId + researchManifestSha256`; the optional visual pair is atomic and independent. `current` may be resolved only once by a provider and cannot be used as a mutable downstream read target.
2. `ArchiveRepositoryProvider.open()` and every repository method accept cancellation via `AbortSignal`, use typed `RepoResult` errors, and cover overview, folders/members, surface, search, TRACE atlas/objects/neighborhood, relation types, relations, claims and corpora.
3. The contract is DTO-first, not PostgreSQL-row-first. Public `surfaceId` is a sealed route identity, not a canonical object key. Pagination is keyset-only, release/filter/sort-bound and defaults to 50 with a maximum of 100.
4. The public serializer must be a positive allowlist. `BLOCKED`, `CITATION_ONLY`, `LINK_ONLY` and `SOURCE_VIEWER` structurally omit pixel, thumbnail and image-service fields. Only `REMOTE_IMAGE` may expose an allowlisted direct pixel locator.
5. Unregistered relations and descriptor/hash/compatibility failures fail closed as typed errors; they never render an `OTHER` relation, empty success, stale `current`, v48 asset, or fixture fallback.
6. Seal/CAS protocols are independent for research and visual releases. Candidate/sealed release projections must not read mutable canonical tables; research and visual current pointers remain independently CAS-controlled.

## Baseline findings

### P0 — no discovered immediate safety violation in the existing sealed SQL layer

- No P0 was found in the inspected database release primitives. `database/functions/003_release_and_cas.sql`, `database/functions/007_release_protocol_closure.sql`, and `database/tests/002_release_seal_cas.sql` establish release fingerprints, validation/seal workflow and CAS-oriented test coverage. They provide a viable basis for a disposable-fixture proof.
- `database/views/001_api_v1.sql` uses `security_barrier` views and has an `release.effective_visual_entry` view that reduces delivery mode before exposing canonical-record, viewer or remote-image locator fields. Its output conditionally exposes `remote_image_url` only when the effective mode is `remote_image`.

This is a limited static statement, not runtime proof of grants, serializer behavior, or a public API.

### P1 — core Phase 2C implementation gaps (expected at this fixed starting point)

1. No application `/api/v1` route files exist under `frontend/src/app`; the focused file enumeration returned no route. No `ArchiveRepository`, provider, DTO-contract module, HTTP adapter, Postgres server adapter, or application fixture adapter file exists under `frontend/src`.
2. `database/views/001_api_v1.sql` currently creates only `api_v1.current_version_status`, `api_v1.current_object`, and `api_v1.research_release_descriptor` (plus `release.effective_visual_entry`). It does not yet provide the documented exact-pair archive, folders, members, surface, Search, TRACE atlas/object/neighborhood, or relation-registry read surface. The implementation needs a new forward-only read migration/view/function set, not alteration of historical migrations.
3. The existing Phase 2A database fixture is a transaction-scoped schema test fixture with two archive objects (`Fixture object A` and `Fixture held object B`), not the required complete, miniature 32-object sealed read release. It must not be silently treated as the product fixture.
4. Existing frontend types in `frontend/src/types/archive.ts` model the v48 mock shape, including `sourceRecordId`, `sourceUrl`, `sourceDescription`, `sourceNotes`, review fields and raw-style table strings. They cannot be carried wholesale into a v1 public DTO without a dedicated positive serializer.
5. No implementation currently proves the required public-boundary behaviors: held sentinel elimination through API/SSR/DOM/client bundle/network, production fixture rejection, exact pair/cursor mismatch rejection, unknown relation integrity failure, or browser exclusion of `pg`/database configuration.

### P2 — direct data coupling that must be removed only from migrated slices

1. `frontend/src/lib/archive-data.ts` imports `@/data/public_surface_mock_v0.json` and resolves folders, surfaces and memberships directly in memory. Folder and surface routes import it directly.
2. `frontend/src/lib/archive-search-client.ts` fetches and decodes `/data/archive-search-v1.json` directly. `SearchWorkspace.tsx` imports this client.
3. `SearchWorkspace.tsx` fetches `/data/trace-v48/atlas.json` and its catalog asset, and imports the legacy `trace-taxonomy` registry.
4. `TraceExplorer.tsx` fetches `/data/trace-v48/atlas.json`, then dynamically loads legacy catalog/review/auxiliary assets and neighborhood shard JSON. Its mobile path selects a hard-coded real v48 object ID, which conflicts with the required honest zero-eligible TRACE state for the real v49 fixture.
5. `frontend/src/app/folders/[type]/page.tsx`, `frontend/src/app/folders/[type]/[slug]/page.tsx`, and `frontend/src/app/surfaces/[id]/page.tsx` compute folder membership/reader content from the imported frozen mock. These imports must disappear from the Archive slice after its migration, but they are useful route/visual-shape references for a narrow adaptation.

## Rights and held-data boundary assessment

- The SQL-level `effective_visual_entry` is directionally aligned with the rights decision: effective delivery mode is reduced by takedown, policy, and health; remote pixels are selected only for a remote-image effective mode.
- This SQL view alone is insufficient for a public boundary. A new serializer must never accept arbitrary `raw_locator`, held locator, raw provider payload, internal ID, workflow note, database address, or an object-shaped row and then filter it. Its construction should begin from the DTO allowlist specified in `READ_API_V1.md`.
- The prospective real fixture has zero positive visual rights. Its normal public visual fields should therefore be structurally absent; any held sentinel should be stored only in a non-public test-only layer and asserted absent from all API/HTML/DOM/bundle/network evidence.
- A nonempty TRACE, `REMOTE_IMAGE`, unknown-relation and takedown test case can be synthetic only in `NODE_ENV=test`, marked `synthetic: true`, and cannot become a production fixture/API/page fallback.

## Unresolved assumptions / decisions that need explicit contract-delta handling if not already decided

- The normative documents prescribe the envelope, identity pairs, error codes and resource inventory, but this audit found no concrete TypeScript DTO schema/field-by-field serializer mapping for the existing page presentation bundle. The implementation should create a contract-delta ledger before inventing identity/cardinality/release/public DTO semantics.
- The exact transport shape for optional visual selection is documented as an implementation detail, except that the two selector values are atomic. Select one documented header/query mechanism once in the API contract ledger and test the all-or-none rule.
- `READ_API_V1.md` names relation, claim and corpus resources while the task permits a core subset. The route ledger must mark excluded routes as intentionally out of scope rather than silently claiming full v1.

## Conclusion

The fixed baseline has sufficiently strong Phase 2A release/seal/CAS primitives and a partially rights-safe SQL projection to support a **forward-only** Phase 2C read layer. It has no product Repository or read API yet, and all three proposed frontend slices remain coupled to frozen v48/mock artifacts. Proceed only by adding a separate Repository/DTO/API boundary, a genuine 32-object sealed fixture, and focused conformance/public-leak tests before migrating Search, then Archive, then TRACE. No historical migration, v48 asset, Phase 2B audit package, or old main change is indicated by this audit.
