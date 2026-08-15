# Queue A2 — CI, coupling, route and test-structure audit

## Scope and boundary

- Inspected revision: `60329e8ec713221bbf42318a4f4c7477e6eb5a72` in `/private/tmp/graphic_design_archive_v49_read_platform`.
- This was a read-only baseline audit for Phase 2C/2D. It did not run npm, Next.js, TypeScript, PostgreSQL, browser automation, generators, Git mutation, or network access.
- This report makes no implementation claim. It identifies the starting surface that the feature branch must replace or isolate.

## Inspected paths

- CI and project configuration: `.github/workflows/audit-package-self-contained.yml`, `frontend/package.json`, `frontend/tsconfig.json`, `frontend/next.config.ts`, `database/scripts/run_tests.sh`.
- Route map: all `frontend/src/app/**/page.tsx` files; there are no `frontend/src/app/**/route.ts` handlers at this revision.
- Migrated-slice candidates and their immediate dependencies: `frontend/src/app/search/page.tsx`, `frontend/src/app/folders/[type]/page.tsx`, `frontend/src/app/folders/[type]/[slug]/page.tsx`, `frontend/src/app/surfaces/[id]/page.tsx`, `frontend/src/components/archive/search/SearchWorkspace.tsx`, `frontend/src/components/archive/trace/TraceExplorer.tsx`, `frontend/src/lib/archive-data.ts`, `frontend/src/lib/archive-search-client.ts`.
- Related legacy sources: `frontend/public/data/archive-search-v1.json`, `frontend/public/data/public_surface_mock_v0.json`, `frontend/public/data/trace-v48/**`, `frontend/scripts/generate-archive-search-index.mjs`, `frontend/scripts/verify-trace-visualization.mjs`, `frontend/scripts/verify-about-mobile.mjs`.
- Governing baseline references: `ARCHITECTURE.md`, `READ_API_V1.md`, `ACCEPTANCE_GATES.md`.

## Actual read-only commands

```text
pwd; git status --short; git rev-parse HEAD
rg --files … (architecture, route, workflow, test and package inventory)
find .github frontend …; sed -n … frontend/package.json; sed -n … .github/workflows/*
find frontend/src/app -type f \( -name page.tsx -o -name route.ts \)
rg -n -i … frontend/src frontend/scripts
sed -n … on the listed route, component and data-access modules
find frontend/public/data -type f …
sed -n … frontend/tsconfig.json; frontend/next.config.ts; database/scripts/run_tests.sh
rg -n 'CI|test|fixture|read API|release|front' ARCHITECTURE.md READ_API_V1.md ACCEPTANCE_GATES.md
```

The working tree was clean when inspected. One exploratory `rg` expression had a zsh parse error and was retried with individual expressions; it made no state change.

## Actual frontend route manifest

```text
/
/about
/appendix
/badges
/bookmarks
/bookmarks/horizontal
/bookmarks/vertical
/cards
/cards/color
/cards/dense
/cards/rectangle
/cards/special
/cards/square
/contents
/folders
/folders/[type]
/folders/[type]/[slug]
/main-sheets
/reading-notes
/search
/slips
/sub-sheets
/surfaces/[id]
/text-pages
/trace
/trace/types/[type]
```

The requested Archive target `/folders/region` is served by the dynamic `/folders/[type]` page. The actual surface-detail route is `/surfaces/[id]`.

## Findings

### P0 — none found by this read-only audit

No current code change was assessed here, and this audit did not identify a newly introduced P0 issue. The starting code is nevertheless not eligible for the Phase 2C/2D acceptance claims until the P1 items below are resolved and tested.

### P1 — no v49 Read API route layer exists

`find frontend/src/app -name route.ts` returned no handlers. The only workflow is the Phase 2B audit-package self-contained check. Therefore there is no current `/api/v1` implementation, HTTP envelope/problem-details mapping, exact release-pair transport, method gate, cursor contract, or public DTO serializer to exercise.

This agrees with `READ_API_V1.md`, which describes the API as a contract at this revision. Phase 2C must add only the documented core subset and must not infer an alternative route naming scheme.

### P1 — the three intended frontend slices have direct legacy data coupling

| Slice / route | Current direct coupling | Consequence for Phase 2D |
| --- | --- | --- |
| Search (`/search`) | `archive-search-client.ts` fetches `/data/archive-search-v1.json`; `SearchWorkspace.tsx` fetches `/data/trace-v48/atlas.json` then its declared catalog and searches decoded payloads client-side. It also imports the local TRACE taxonomy. | Replace data reads with the uniform Repository/API client and receive relation registry/search results from the exact release. Retain only presentation logic after contract coverage exists. |
| Archive (`/folders/[type]`, `/folders/[type]/[slug]`, `/surfaces/[id]`) | The pages call `archive-data.ts`, which imports `@/data/public_surface_mock_v0.json` directly and exposes folders, membership, surfaces and research dossiers from that frozen payload. | Move the requested folder/detail/member paths to Repository/API reads with bounded members and keyset paging; do not carry the mock import into the migrated path. |
| TRACE (`/trace`) | `TraceExplorer.tsx` fetches the frozen v48 atlas, catalog/review/auxiliary payloads and neighborhood shards. It has a hard-coded mobile featured object ID. | Replace verified-data reads with exact-release TRACE endpoints. The v49 real fixture must remain an honest `totalExact=0` state; no v48 catalog, shard or featured-object fallback may remain active. |

Additional direct legacy consumers outside the three initial slices include `/` and `/about` importing `trace-v48/atlas.json`, `MainSheetLab`/`SubSheetLab` fetching `public_surface_mock_v0.json`, and scripts that generate or verify those assets. They are not evidence that the three requested slices are already migrated; global repository migration must remain explicitly incomplete.

### P1 — existing client data format conflicts with the proposed public-rights boundary

The pre-existing public mock and v48 TRACE assets are browser-accessible static JSON. The inspected source types and generated source include fields such as historical text, raw-payload references, source URLs and, in legacy objects, image URL/display-policy data. Phase 2C must use positive-allowlist DTOs and an isolated held-locator sentinel test. The migration must not expose those legacy payload shapes through `/api/v1`, even if the old static assets remain checked in for non-migrated legacy pages.

### P1 — CI/test structure is insufficient for the requested layered gates

- `frontend/package.json` has `dev`, `build`, visual/capture scripts and `lint`, but no unit-test, contract-test, focused typecheck or CI script.
- No JavaScript/TypeScript test framework configuration or frontend test files were found in the non-data inventory.
- The sole workflow, `audit-package-self-contained.yml`, correctly preserves the Phase 2B evidence-package gate but does not supply `pr-fast`, `small-db-integration`, or `manual-full-rehearsal` wiring.
- `database/scripts/run_tests.sh` runs four existing SQL scripts (`001_constraints.sql` through `004_serializable_seal.sql`) against a dedicated Phase 2A database and confirms no residue. It is not a Phase 2C fixture/API/adapter test lane as-is.

The requested implementation should add narrow, named layers without using `next build` or turning frontend CI into a canonical-data importer.

### P2 — current route and build ergonomics require care, not redesign

- `frontend/next.config.ts` intentionally constrains static generation; archive dynamic pages state that the frozen dataset is large. This supports the task rule to avoid full Next builds and favor focused checks.
- The existing `trace/types/[type]` route is driven by a static local taxonomy. Once relation registry API support is introduced, its authority must be reviewed separately; this audit does not decide whether presentation labels can remain a local constant.
- Existing verify/capture scripts read legacy public assets. They should not be repurposed as v49 correctness proof without changing their inputs and assertions deliberately.

## Unresolved assumptions requiring an explicit implementation decision

1. The report does not decide the precise identity, runtime placement or release-selection transport for the Repository provider; `ARCHITECTURE.md`, ADR 0003 and `READ_API_V1.md` remain authoritative.
2. The report does not infer whether legacy static data is to be removed repository-wide. The task permits only the three migrated slices to lose direct coupling and requires `REPOSITORY_MIGRATION_GLOBAL_COMPLETE=false`.
3. The report does not decide whether `/trace/types/[type]` joins this Phase 2D migration; it is a related route but not one of the three named initial slices.
4. No browser, runtime, schema, performance or accessibility result is claimed. Those require later focused execution in the main task after backend gates pass.

## Conclusion

At `60329e8`, the repository has the intended visual prototypes and a Phase 2B audit-package guard, but it has no Read API route layer or frontend repository-test lane. Search, Archive and TRACE each directly bind to frozen v48/static data through imports or browser fetches. Phase 2C should first create and prove the release-pinned Repository/API/fixture boundary; only then can each of these three slices be marked migrated. This baseline supports `REPOSITORY_MIGRATION_GLOBAL_COMPLETE=false` and sets the measurable post-migration target `DIRECT_DATA_COUPLING_IN_MIGRATED_SLICES=0`.
