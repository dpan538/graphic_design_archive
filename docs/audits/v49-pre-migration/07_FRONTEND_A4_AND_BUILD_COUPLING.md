# 07 — Frontend, A4 and Build Coupling Audit

- Audit package: **A7**
- Audit date: **2026-08-11 (Australia/Brisbane)**
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Baseline branch: `refactor/v49-data-platform`
- Baseline commit: `f076ca3444aaa0f413bb61fe2cb568d6a9aa2720`
- Independent output: `docs/audits/v49-pre-migration/07_FRONTEND_A4_AND_BUILD_COUPLING.md`
- Scan coverage: **COMPLETE** for the assigned A7 boundary
- Readiness result: **PARTIAL**

`PARTIAL` means that the static repository scan is complete, but frontend/data
decoupling and bounded delivery are not ready for migration promotion. The
current branch has already stopped statically generating every surface and
folder reader route. That useful mitigation did not remove the 8,636-row
legacy JSON from the application dependency graph, did not bound `/contents`
or large-folder runtime work, and did not create a sealed-release repository
boundary.

## 1. Scope

This package statically inspected:

- all 26 App Router `page.tsx` route files and the one API route;
- `frontend/src/lib`, `frontend/src/components`, the type contract, global CSS,
  and the production Reader/pagination path;
- `frontend/package.json`, `next.config.ts`, TypeScript metadata, and the
  checked-in frontend handoff;
- `generateStaticParams`, dynamic-route declarations, build-time imports,
  fixed `/data/` fetches, and data-dependent rendering loops;
- A4/physical-leaf components, print/PDF/export references, Puppeteer capture
  scripts, screenshot entry points, and static-data producers;
- root scripts that write directly into `frontend/src/data` or
  `frontend/public/data`;
- recorded build-timeout evidence and Git history for the earlier bulk route
  generator;
- existing A2/A3 audit evidence for storage, authority, and set boundaries.

This package does not judge TRACE epistemology, image rights, AI retirement,
individual QA screenshots, CI/deployment policy, or data authority except where
those facts create a frontend build/runtime dependency. Those are owned by A3,
A5, A6, A8, A9, and A10.

## 2. Explicit non-actions

The following were explicitly **not** performed:

- no `npm install`, `next dev`, `next build`, `next start`, lint, TypeScript,
  or bundler command;
- no browser, Puppeteer, Playwright, screenshot, page render, PDF, print, or
  export process;
- no PostgreSQL, Docker, SQLite, data generation, payload normalization,
  sharding, Search generation, or TRACE generation;
- no frontend, package, lockfile, configuration, CI, deployment, frozen v48,
  shard, manifest, or QA-image modification;
- no deletion, dependency change, cleanup execution, commit, push, merge, PR,
  or deploy;
- no secret value read or emitted.

One read-only `jq` pass over the 90,895,254-byte legacy frontend JSON emitted
only aggregate counts. It did not write or transform the payload. All shell
commands completed; A7 started no persistent process and has no residual PID or
execution session.

## 3. Evidence commands

Representative commands are shown exactly enough to reproduce the scan. All
were read-only except creation of this report.

```sh
repo=/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform

rg --files frontend \
  -g '!frontend/node_modules/**' -g '!frontend/.next/**'

find frontend/src/app -name page.tsx -print | sort

sed -n '1,240p' frontend/package.json
sed -n '1,240p' frontend/next.config.ts
sed -n '1,720p' frontend/src/lib/archive-data.ts
sed -n '1,700p' frontend/src/lib/paginate.ts
sed -n '1,860p' frontend/src/components/archive/reader/Reader.tsx

rg -l 'from "@/lib/archive-data"' frontend/src --glob '*.{ts,tsx}'
rg -n 'generateStaticParams|export const dynamic|export const revalidate' \
  frontend/src/app --glob '*.{ts,tsx}'
rg -n 'public_surface_mock_v0\.json|archive-search-v1\.json|trace-v48/|fetch\(' \
  frontend/src --glob '*.{ts,tsx}'

rg -l 'puppeteer|playwright|\.screenshot\(|page\.goto\(|launch\(' \
  frontend scripts --glob '*.{js,mjs,ts,tsx,py}'
rg -n -i '\bA4\b|210[[:space:]]*/[[:space:]]*297|@media[[:space:]]+print|window\.print|page\.pdf|html2canvas' \
  frontend/src frontend/scripts --glob '*.{ts,tsx,js,mjs,css}'

rg -n 'frontend.*(src|public).*data|FRONTEND_DATA|FRONTEND_PUBLIC_DATA|public_surface_mock_v0|trace-v48|public_surface_shards' \
  scripts frontend/scripts --glob '*.{py,js,mjs}'

stat -f '%N|%z' \
  frontend/src/data/public_surface_mock_v0.json \
  frontend/public/data/public_surface_mock_v0.json \
  frontend/public/data/archive-search-v1.json \
  frontend/public/data/trace-v48/catalog.json

jq '{surfaces:(.surfaces|length),folders:(.folders|length),
  folderMembershipRefs:([.folders[].surfaceIds|length]|add),
  surfaceEmbeddedFolderRefs:([.surfaces[].folders|length]|add),
  maxFolderMemberships:([.folders[]|(.surfaceIds|length)]|max)}' \
  frontend/src/data/public_surface_mock_v0.json

git log --all -S'allSurfaceParams()' -- \
  'frontend/src/app/surfaces/[id]/page.tsx'
git log --all -S'force-dynamic' -- \
  'frontend/src/app/surfaces/[id]/page.tsx' \
  'frontend/src/app/folders/[type]/[slug]/page.tsx'
git show 1ecbadf^:'frontend/src/app/surfaces/[id]/page.tsx'
```

The previously generated A3 report was read as shared evidence rather than
repeating canonical/TRACE scans:
[03_DATA_ASSET_AUTHORITY_AND_LINEAGE.md](03_DATA_ASSET_AUTHORITY_AND_LINEAGE.md).

## 4. Measured inventory

### 4.1 Route and static-generation surface

| Measurement | Result |
| --- | ---: |
| App Router page files | 26 |
| Explicit `force-dynamic` page routes | 2 |
| Current `generateStaticParams` functions | 2 |
| Folder-type static params | 4 |
| TRACE-type static params | 21 |
| Explicit static-param route instances | 25 |
| Non-parameter page files without an explicit dynamic declaration | 22 |
| Source-level static-prerender candidates | 47 (22 + 25), **not build-verified** |
| Dormant bulk param helpers | 2 (`allFolderParams`, `allSurfaceParams`) |

The two deliberately dynamic readers are:

- `frontend/src/app/surfaces/[id]/page.tsx`;
- `frontend/src/app/folders/[type]/[slug]/page.tsx`.

The only active static-param generators are the four folder-type pages and 21
small TRACE taxonomy pages. There is no active all-object
`generateStaticParams` call in the current tree. Because this audit was
forbidden to run a build, 47 is a source-level candidate count, not a claim
about a specific Next build receipt.

Git history proves the bulk path is recent, not hypothetical. Immediately
before commit `1ecbadf0ea369f9b3ff804a44b079ef1434d6f05`, surface and folder
reader pages called `allSurfaceParams()` and `allFolderParams()`. That commit
replaced both with `force-dynamic`. The dormant helpers remain exported from
`archive-data.ts`, so re-importing either would silently restore bulk fan-out.

`docs/TRACE_EVOLUTION_FIELD_DECISION.md` records the historical consequence:
an optimized production compilation took 17.5 minutes, then static generation
attempted 8,783 pages and entered repeated 60-second route retries. This is
historical evidence, not the measured current page count.

### 4.2 Frontend payload sizes and populations

| Asset | Bytes | Runtime role |
| --- | ---: | --- |
| `frontend/src/data/public_surface_mock_v0.json` | 90,895,254 | statically imported legacy archive repository |
| `frontend/public/data/public_surface_mock_v0.json` | 90,895,254 | client-fetched mirror used by layout labs |
| `frontend/public/data/archive-search-v1.json` | 22,695,973 | lazy Search projection |
| `frontend/public/data/trace-v48/catalog.json` | 2,629,051 | lazy active TRACE catalog |
| `frontend/public/data/trace-v48/` | 102,672 KiB allocated | atlas/catalog/review/auxiliary plus 576 neighborhood shards |

The three 8,636-surface legacy payload copies are the same Git blob according
to A3. They are a presentation/Search projection, not the v49 migration input.

The one aggregate A7 pass over that legacy payload measured:

| Legacy frontend unit | Count |
| --- | ---: |
| surfaces | 8,636 |
| folders | 96 |
| folder-side membership references | 26,041 |
| surface-embedded folder references | 26,038 |
| largest folder membership count | 5,740 |
| research dossiers | 8,636 |
| reading notes | 377 |

The three-reference folder/surface discrepancy is evidence that even the
legacy projection should not be treated as a self-validating database. A7 did
not guess which side is correct and did not perform a second large-file pass to
extract the rows; reconciliation belongs in the data-quality gate.

The frontend simultaneously exposes:

- the 8,636-item Archive/Search projection;
- the 15,923-item canonical/active TRACE cohort;
- an intersection of 2,585 IDs;
- 6,051 Search-only IDs;
- 13,338 canonical/TRACE-only IDs.

Home and About take headline counts from the 15,923 TRACE atlas while folder,
surface, Reader, assistant-retrieval, and A4 layout paths take records from the
8,636 legacy payload. Search joins both products in one UI without one release
identity. This is a presentation-level population split, not a second
canonical database, but it can be mistaken for one by users and maintainers.

## 5. Direct frontend/data coupling ledger

### 5.1 Consumer count

The reproducible file-level count is:

| Coupling class | Files |
| --- | ---: |
| Direct imports of `@/lib/archive-data` | 19 |
| Direct fixed/raw JSON, Search, or TRACE asset readers | 10 |
| Files in both groups | 3 |
| **Distinct runtime/compile consumer files** | **26** |

The ten raw-path readers are:

1. `frontend/src/app/about/page.tsx`;
2. `frontend/src/app/page.tsx`;
3. `frontend/src/components/archive/main-sheets/MainSheetLab.tsx`;
4. `frontend/src/components/archive/search/SearchWorkspace.tsx`;
5. `frontend/src/components/archive/sub-sheets/SubSheetLab.tsx`;
6. `frontend/src/components/archive/trace/ChronogeographicRoutes.tsx`;
7. `frontend/src/components/archive/trace/TimeGeographyMap.tsx`;
8. `frontend/src/components/archive/trace/TraceExplorer.tsx`;
9. `frontend/src/lib/archive-data.ts`;
10. `frontend/src/lib/archive-search-client.ts`.

Four client modules directly import `archive-data.ts`:

- `MainSheetLab.tsx` and `SubSheetLab.tsx` import its re-exported palette;
- `TocNav.tsx` imports folder metadata;
- `TextPageLab.tsx` imports surfaces and scans the full collection for samples.

`Reader.tsx` imports `LeafFrame.tsx`, which imports `layouts.tsx`; that module
imports the MainSheet, SubSheet, TextPage, Card, Bookmark, ReadingNote, Slip,
and Appendix lab implementations. Therefore the production Reader and design
lab graph are not isolated. Static source analysis proves the dependency edge;
without a prohibited build it does not claim an exact emitted JavaScript byte
count.

### 5.2 Producer count

Nine executable scripts write directly into the frontend data tree:

| Producer class | Count | Paths |
| --- | ---: | --- |
| Legacy monolithic mirror writers | 6 | `normalize_public_surfaces.py`, `rebuild_public_surfaces_from_records.py`, `run_early_region_capture_1830_1930.py`, `run_midcentury_capture_1930_1970.py`, `run_midcentury_expansion_capture_1931_1970.py`, `generate_global_stress_public_surfaces.py` |
| Search projection writer | 1 | `frontend/scripts/generate-archive-search-index.mjs` |
| TRACE v48 product writer | 1 | `scripts/build_prefreeze_candidate_v48_trace_visualization.py` |
| Legacy public-shard writer | 1 | `scripts/shard_public_surface_payload_v1.py` |
| **Direct frontend-data producer files** | **9** |  |

The complete direct coupling surface is therefore **35 files**: 26
runtime/compile consumers plus 9 producer scripts. Consumer count (26),
producer count (9), and combined boundary (35) must remain separate in future
receipts; they are not interchangeable units.

Six historical capture/rebuild utilities overwrite both monolithic frontend
copies as a side effect. They bypass a release repository, immutable version
path, current-pointer CAS, and frontend-independent publication channel. The
Search generator reads the legacy source copy and has no `prebuild` hook, so it
can also drift unless run manually. The TRACE builder additionally reads
SQLite and legacy frontend data; A3 classifies its output as a frozen derived
v48 product, not migration authority.

## 6. Build and runtime hotspots

### 6.1 `/contents`: current static bulk-render hotspot

`frontend/src/app/contents/page.tsx` is an unparameterized route with no dynamic
declaration. It loops every folder and every folder member and renders a link
for each membership. Against the checked-in legacy frontend payload this is at
least **26,041 surface-link list items**, plus 96 folder sections. The same
8,636 records are intentionally repeated across folder memberships.

The route also renders client `TocNav`, which imports the monolithic
`archive-data.ts` merely to show four folder types. Thus `/contents` combines a
large static HTML/RSC traversal with a client dependency edge to the same
90.9 MB source payload. This is the clearest surviving equivalent of a bulk
generator and must not remain a one-page release gate.

### 6.2 Dynamic folder Reader: bulk work moved to request time

`force-dynamic` prevents all folders from being generated at build time, but
the selected folder is still expanded in one request:

1. `paginateFolder()` resolves and sorts every member;
2. it constructs at least one leaf per member plus register and reading-note
   leaves;
3. `folderJumpTargets()` constructs an entry for each surface;
4. the full `leaves` and `jumpTargets` arrays cross into client `Reader`;
5. Reader displays one active leaf, but maps the complete jump-target list.

For the largest legacy folder, 5,740 members imply a strict lower bound of
**5,742 leaves** before optional text, slip, appendix, bookmark, or extra
register leaves, and at least **5,741 jump entries**. Rendering only one leaf
does not make the serialized input bounded. A cursor/window contract is needed
for both normal reading and future print selection.

### 6.3 Search and assistant scans

- `archive-search-client.ts` lazily downloads and decodes all 8,636 Search
  records, then scans them in the browser for each query. Both shell Search and
  the full Search workspace use it.
- Search workspace also downloads and decodes the full 15,923 TRACE catalog and
  filters it in the browser.
- `assistant-retrieval.ts` imports the monolithic archive repository and uses
  `fuzzySearchSurfaces()`, which scans the 8,636 full records server-side per
  evidence request.
- `archive-data.ts` still retains an older substring search and fuzzy search
  alongside the compact Search client, so two Search implementations and two
  data representations coexist.

These are bounded enough for a prototype only under explicit fixtures. They
are not release-repository or API boundaries.

### 6.4 Configuration is a mitigation, not decoupling

`next.config.ts` sets:

- `staticPageGenerationTimeout: 300`;
- `staticGenerationMaxConcurrency: 1`;
- `staticGenerationMinPagesPerWorker: 100`;
- two experimental CPUs;
- production webpack cache disabled.

The comments explicitly cite memory thrashing and retry storms. Low
concurrency helped contain the historical failure but makes a data-driven full
build serial and disables reuse of production compiler cache. No config value
can replace repository paging, immutable data publication, or independent
data/frontend CI.

### 6.5 Data changes still couple to frontend delivery

There are two coupling modes:

1. Changes to `frontend/src/data/public_surface_mock_v0.json` invalidate the
   shared `archive-data.ts` module graph and every statically generated or
   client path depending on it.
2. Search, TRACE, shard, and public mock files live under `frontend/public`.
   They are lazy at runtime, but the repository has no independent static-data
   publish/pointer step; changing them currently requires another frontend
   deployment, whose package build command is `next build`.

Home and About statically import `trace-v48/atlas.json`, so even a headline
count change is a source build input. Fixed paths such as
`/data/archive-search-v1.json` and `/data/trace-v48/atlas.json` do not carry a
research-release plus visual-registry pair, and clients do not verify manifest
SHA values before decoding related files.

## 7. A4, print, PDF, screenshot and exporter ledger

### 7.1 Counted A4/page/static-render entry points

The requested executable entry-point count is **9**:

| Entry class | Count | Disposition |
| --- | ---: | --- |
| Full Next production build (`npm run build` → `next build`) | 1 | Required only in later frontend CI; prohibited as a prototype/checkpoint gate |
| Active `generateStaticParams` route functions | 2 | Keep the two low-cardinality concepts after repository decoupling; never restore object/folder bulk params |
| Puppeteer screenshot/a11y executables | 6 | Isolate as QA tooling; never run as build hooks or release data generators |
| **Total** | **9** |  |

The six browser executables are:

1. `frontend/scripts/capture-main-sheets.js`;
2. `frontend/scripts/capture-sub-sheets.js`;
3. `frontend/scripts/capture-text-pages.js`;
4. `frontend/scripts/capture-cards.js`;
5. `frontend/scripts/capture-file-page.js`;
6. `frontend/scripts/asset-a11y-check.js`.

Four paired `preview:*` package aliases start Next development servers. They
are operational prerequisites for four capture scripts, but are **not** counted
as generation entries. `capture-file-page.js` is directly executable but has no
package alias. The a11y script defaults to eight routes across three viewports,
creating 24 screenshots plus JSON reports per run.

The nine static-data producers in section 5.2 are also not mixed into this A4
page-render count. Keeping those units separate prevents an apparently simple
“9 generators” statement from hiding 18 distinct delivery-side executables.

### 7.2 What actually exists

- A4 is a **visual leaf geometry** (`aspect-ratio: 210 / 297`) used by Reader
  and layout studies.
- No `@media print`, `window.print`, `page.pdf`, HTML-to-canvas, server PDF
  route, or PDF library call exists in the scanned frontend implementation.
- The five capture scripts create PNGs, not PDFs or citable publication
  exports.
- `docs/system/RESEARCH_DOSSIER_EXPORT_MODEL_v0.md` specifies future PDF
  behavior but is not implementation evidence.

Therefore the number of implemented print/PDF exporters is **zero**. The
dynamic Reader/pagination system is only a candidate rendering substrate. It
may be retained for an eventual **on-demand, rights-filtered, explicitly
selected and bounded** print renderer; it must not be treated as one today.

### 7.3 Retirement boundaries

| Class | Current examples | Decision |
| --- | --- | --- |
| Must-retire bulk generation | dormant `allSurfaceParams`/`allFolderParams`; one-page `/contents`; any future all-object A4 loop | Remove or make unreachable before production build gates; replace with cursor/windowed reads |
| Keepable on-demand renderer substrate | dynamic surface Reader; bounded portion of dynamic folder Reader; physical leaf/layout components | Keep only behind `ArchiveRepository`, release identity, rights filtering, explicit page selection, and hard request limits |
| Design/QA capture tooling | four layout capture scripts and `asset-a11y-check.js` | Keep outside runtime/build and run only against a bounded fixture or explicit QA deployment |
| Orphan/general screenshot helper | `capture-file-page.js` | `HOLD_UNKNOWN`; archive or delete candidate only after confirming no undocumented QA dependency |
| Independent data exporter concept | Search, TRACE, and shard producers | Separate from frontend CI; replace legacy sources with sealed-release/visual-registry inputs and immutable manifests |
| Implemented independent print/PDF exporter | none | Future task; do not infer readiness from CSS A4 ratios |

## 8. Findings and priorities

### P0 — must close before frontend migration/promotion

| ID | Finding | Affected paths | Risk | Required action |
| --- | --- | --- | --- | --- |
| A7-P0-01 | 26 runtime/compile consumer files remain tied to legacy files or `archive-data.ts`; production Reader and design labs share a client dependency graph | `frontend/src/lib/archive-data.ts`, `frontend/src/components/archive/layouts.tsx`, Reader and 24 other consumers | 90.9 MB projection can enter compile/client/runtime paths; no replaceable repository contract | Make `ArchiveRepository` the sole runtime boundary; pass small typed DTOs/fixtures into client components; ban raw JSON imports outside one adapter during transition |
| A7-P0-02 | One interface mixes Search 8,636 and TRACE 15,923 without one release identity | Home, About, Search, shell Search, Reader, TRACE | misleading counts/routes; Search may appear canonical | Resolve both through sealed research release plus independent visual registry; label projection and cohort explicitly |
| A7-P0-03 | `/contents` expands 26,041 membership links in one static route | `frontend/src/app/contents/page.tsx`, `TocNav.tsx` | build memory/time, huge HTML/RSC/client payload, repeated records | Replace with server-rendered bounded index pages and cursor/search navigation; preserve crawlable summaries without all memberships in one document |
| A7-P0-04 | Dynamic folder Reader serializes an unbounded full folder; current largest is 5,740 members | folder route, `paginate.ts`, `Reader.tsx` | build hotspot moved to request latency/memory and hydration; future print amplifies it | Define max window/page selection and cursor contract; fetch only active/adjacent leaves and bounded index segments |
| A7-P0-05 | Nine producer scripts write directly into frontend assets; six overwrite monolithic mirrors | scripts in section 5.2 | release drift, bypassed seal/CAS, data mutation implies frontend deployment/build | Retire mirror side effects; publish immutable release assets in data CI; frontend consumes versioned pointers/contracts only |

### P1 — required before frontend CI/promotion gate

| ID | Finding | Risk | Recommended action |
| --- | --- | --- | --- |
| A7-P1-01 | `allSurfaceParams` and `allFolderParams` remain exported after the historical 8,783-page failure | accidental one-line regression restores bulk generation | Delete in a later frontend task or enforce a static check forbidding imports from routes |
| A7-P1-02 | Main/Sub labs fetch 90.9 MB to show 4/8 studies; TextPage lab imports the full payload; lab routes ship with the product | unnecessary bandwidth/memory and production route surface | Replace with a small immutable layout fixture and exclude lab/capture routes from production navigation/deploy |
| A7-P1-03 | Search decodes 22.7 MB/8,636 rows and TRACE decodes 15,923 rows in the main browser thread | mobile latency and repeated whole-array scans | Move to bounded read/search API or worker/index chunks tied to a sealed release |
| A7-P1-04 | Fixed asset URLs have no client manifest-hash verification or dual research/visual version | mismatched Search/TRACE/visual files can be combined | Resolve all asset URLs from one verified release descriptor plus visual-registry descriptor |
| A7-P1-05 | Serial static generation, 300-second timeout, and disabled production webpack cache encode past failure as permanent config | slow builds and masked regressions | After decoupling, remove workaround values only through focused CI measurements; keep prototype full-build ban |
| A7-P1-06 | Browser capture tooling is callable beside production package scripts and assumes hard-coded local Chrome | accidental server/browser launch, nonportable QA | Move to explicit QA package/workflow with fixture limits, manifests, and no default production dependency |
| A7-P1-07 | No implemented print/PDF exporter enforces dossier selection, rights, or release identity | A4 appearance may be mistaken for export readiness | Design a separate on-demand exporter only after rights/release gates; do not bulk-render the archive |

### P2 — hygiene and maintainability

| ID | Finding | Recommended action |
| --- | --- | --- |
| A7-P2-01 | `frontend/HANDOFF.md` still says no WebLLM/graph and cites an old successful 22-page build | Archive it as historical or rewrite only after authorized frontend work; never use it as current acceptance evidence |
| A7-P2-02 | Production layout exports live in `*Lab.tsx` files with capture-only wrappers | Split pure layout components from lab/fixture wrappers so production imports cannot pull lab data effects |
| A7-P2-03 | Old full-payload search functions and compact Search client coexist | Retire the old UI search after assistant/repository replacement; keep one typed Search contract |
| A7-P2-04 | `capture-file-page.js` has no package owner/alias | Confirm owner and recovery reference; then archive or list as deletion candidate |

Priority totals: **P0 = 5, P1 = 7, P2 = 4**.

## 9. Required gates and dependency order

### 9.1 Physical schema and data migration dependencies

Physical schema work does not need to implement frontend routes, but it must
provide the identities and release projections required to remove raw-file
coupling:

1. object/surface/source crosswalk and stable route identity;
2. release-scoped folder membership and bounded ordering keys;
3. Search and TRACE projection provenance;
4. rights-safe representation/delivery fields;
5. immutable research release and independent visual-registry identities.

The three-count discrepancy in the legacy folder projection is reconciliation
evidence only and must not override canonical migration input.

### 9.2 Frontend integration gate

Frontend integration may begin when:

- `ArchiveRepository` returns versioned bounded DTOs for folder indexes,
  surfaces, Search, TRACE summaries, and neighborhoods;
- no production component imports `public_surface_mock_v0.json`;
- no frontend request needs to decode the full canonical release;
- Search remains a projection and reports its release identity;
- large folders and `/contents` have cursor/window limits;
- fixture mode covers normal, review, auxiliary, held-rights, multilingual,
  long-title, and error states without a full build.

### 9.3 Frontend CI gate

Data CI must seal/publish manifests and projections independently. Frontend CI
must validate repository contracts and bounded fixtures without regenerating
data. During prototype/checkpoint work, full `next build`, all-route generation,
browser automation, and data export remain prohibited. A later production-build
job is allowed only after the above decoupling gates and must record route
counts, memory, duration, largest output, and forbidden bulk-param checks.

### 9.4 Final push/promotion gate

No frontend promotion should pass until:

- direct raw payload consumers are zero outside an explicitly temporary
  adapter;
- direct frontend-data producer side effects are zero;
- `/contents` and folder Reader bounds are tested at the largest release
  cardinality;
- research release and visual registry versions are displayed and
  machine-readable;
- rights-held pixel URLs cannot leak through repository, Search, print, or
  static payloads;
- production build evidence is generated in frontend CI, not during a
  prototype architecture checkpoint.

## 10. Status summary

| Audit question | Result |
| --- | --- |
| Complete static A7 scan | **PASS** |
| Current all-object `generateStaticParams` absent | **PASS** |
| Dormant/historical bulk route path retired | **PARTIAL** — calls removed; helpers remain |
| Direct frontend/data decoupling | **FAIL** — 35-file consumer/producer boundary |
| `/contents` bounded | **FAIL** |
| Folder Reader bounded | **FAIL** |
| Search/TRACE population identity unified | **FAIL** |
| A4 layout preserved without bulk generation | **PARTIAL** |
| Implemented rights-aware on-demand print/PDF | **FAIL** — no implementation exists |
| Data CI independent of frontend build | **FAIL** |
| Prototype full-build prohibition respected in A7 | **PASS** |
| Frontend or frozen data changed by A7 | **PASS** — none |
| A7 residual process/session | **PASS** — none |

**A7 conclusion:** audit coverage is `COMPLETE`; implementation readiness is
`PARTIAL`. The current tree contains valuable on-demand Reader and progressive
TRACE patterns, but `ENGINEERING_PRE_DDL_READY` cannot rely on the frontend as
a clean repository client yet, and `FRONTEND_PROMOTION_READY` is false. The
first implementation task after physical data/repository contracts should be a
bounded repository adapter and fixture-mode cutover—not another all-route build
or A4 bulk exporter.
