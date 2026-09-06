# Graphic Design Archive (MGDA)

A rights-aware, PostgreSQL-backed research archive for modern graphic design history, built end to end by one person: source capture across fifteen institutional APIs and collections, reconciliation into a canonical population, a frozen versioned database and read-only API, and a research-grade public frontend (Index, Search, Object records, TRACE research views) that never touches the database directly. Release v49 is closed, frozen and byte-anchored; every public figure on this page is read from a file in this repository.

```yaml
# machine-readable summary (all values verifiable at the paths given)
project: Graphic Design Archive (MGDA)
author: Dai Pan (潘岱) — sole author (git log: 256 commits, 2026-05-31 → 2026-09-06)
domain: digital humanities · design history · research infrastructure
release:
  id: v49
  status: closed, frozen, byte-anchored
  immutable_source_anchor: v49-data-api-closure-20260821
  freeze_manifest: database/FREEZE_V49.json
canonical_population:
  objects: 15923            # docs/releases/v49/RELEASE_MANIFEST.json
  assignments: 47982
  publicly_eligible: 7995
  held: 7928
reader_projection:          # frontend/generated/reader-eligibility-v49/manifest.json
  reader_facing_objects: 5423
  record_only_entries: 2572
  rules: gda-reader-eligibility-rules-v1
sources:
  public_set_institutions: 15
  distinct_source_labels: 272   # frontend/src/data/status-v49.json (meta.sources)
  places: 424
research_layer:             # docs/research/EXPLORATION_CURRENT.md
  validated_pairwise_generic_associations: 21
  open_inquiry_higher_order_hypotheses: 11
  known_excluded_higher_order_structures: 9
  accepted_typed_historical_relations: 0
  positive_visual_rights: 0
api:
  read_endpoints: 18        # docs/api/v49-read-api-openapi.yaml
  product_route_map_entries: 91   # docs/api/product-api-map.v1.json
  database_access: read-only role; frontend never connects to PostgreSQL
database:
  migrations: 14
  functions: 20
  tests: 14
  next_version: 50          # database/VERSION
stack: [PostgreSQL, Python, Next.js (App Router), React 19, TypeScript strict, CSS Modules, three.js]
ci_workflows: 6             # .github/workflows
verification_scripts: { frontend_package_scripts: 48, frontend_script_files: 89 }
audits: 41                  # docs/audits
adrs: 6                     # docs/adr
licences: { software: MIT (LICENSE), interface_design: FRONTEND_DESIGN_LICENSE.md }
entry_points:
  - docs/releases/v49/RELEASE_INDEX.md
  - docs/api/v49-read-api-catalog.md
  - docs/frontend/FRONTEND_DESIGN_DECISION.md
  - docs/research/EXPLORATION_CURRENT.md
  - database/FROZEN_V49.md
```

## What this project is

- **A research archive, not an image mirror.** The repository is a metadata, citation and source-return layer. Zero positive visual rights is a deliberate release fact; nothing infers rights, acceptance, relations or publication eligibility.
- **A governed pipeline from source to reader.** Records move from candidate to canonical to published through reconciliation and screening; what is published, held or excluded is decided by rule, and the rule is written down. Missing, null, empty and quarantined are kept distinct.
- **An evidence-bounded research surface.** TRACE exposes only validated, evidence-qualified generic associations, and keeps unresolved hypotheses in an explicitly labelled Open Inquiry layer that can never add edges, compositions or metrics.

## What I built

| Layer | What it is | Where to look |
| --- | --- | --- |
| Source capture and reconciliation | Capture across fifteen institutional APIs and collections (V&A, Library of Congress, Art Institute of Chicago, Yale, Cooper Hewitt, National Library of Norway, Nasjonalmuseet, Gallica/BnF, Biblioteca Nacional de Chile, Malaysia Design Archive, Desain Grafis Indonesia, Pacific Community Digital Library and others), period and region strategies, fallback and ingest policies, then reconciliation into one canonical population of 15,923 objects | `docs/capture/`, `docs/methodology/`, `docs/releases/v49/DATA_INPUT_MANIFEST.json` |
| PostgreSQL database | 14 forward-only migrations, 20 SQL functions, 14 database tests, roles and views; a v48 → v49 replay with an expected baseline and a rehearsal script; the release frozen by manifest and checksum | `database/`, `database/data-migrations/v48-to-v49/`, `database/FREEZE_V49.json` |
| Read API | 18 documented read-only endpoints under an OpenAPI 3.1 contract, with examples, an error catalog and a product route map; served by the frontend's server side through a dedicated read-only database role | `docs/api/v49-read-api-openapi.yaml`, `docs/api/v49-read-api-catalog.md`, `docs/api/product-api-map.v1.json` |
| Reader-eligibility projection | A governed split of the 7,995 public records into 5,423 reader-facing objects and 2,572 record-only entries (titles that are source identifiers or numbers), with per-record reasons, a rules version and checksums; Index, Search and object pages all join against it | `frontend/generated/reader-eligibility-v49/`, `frontend/src/features/reader-eligibility/` |
| Public frontend | Next.js App Router, TypeScript strict, CSS Modules. Home, Index, Search (live API with cursor paging and facets), Object records, About and Source. Desktop and mobile are two separate trees that share only `lib/` and content, enforced by a 539-check coupling audit | `frontend/src/app/`, `frontend/scripts/audit-mobile-desktop-coupling.mjs` |
| TRACE research views | Context Canvas (one object among governed representations) and Exploration (a bounded generative visual explorer with sixteen pure-graphic templates and five reference export forms over the frozen Exploration V2 state machine); Open Inquiry as a reading layer | `frontend/src/app/trace/`, `frontend/src/features/trace-v49/`, `docs/research/EXPLORATION_CURRENT.md` |
| "System suggests" | A bounded language-model annotation: a server-side fact layer, a relation gate that rejects any note naming a number, term or pairing not on screen, a cache, and a provider disclosed only on the About page | `frontend/src/features/system-suggestions/`, `docs/qa/system-suggestions-release-v1/` |
| Design system | A stamp-sheet visual language (flat colour, black keylines, one idea per section) with a written design decision record; a 17 px mobile type floor; every round measured in the browser before it ships | `docs/frontend/FRONTEND_DESIGN_DECISION.md`, `docs/design/` |
| Engineering governance | Six CI workflows, repository hygiene and freeze verifiers, 41 audit packages, 6 ADRs, immutable tags and a documented change policy | `.github/workflows/`, `scripts/repository/`, `docs/audits/`, `docs/adr/` |

## Numbers you can check

| Figure | Value | File |
| --- | --- | --- |
| Canonical objects / assignments | 15,923 / 47,982 | `docs/releases/v49/RELEASE_MANIFEST.json` |
| Publicly eligible / held | 7,995 / 7,928 | `docs/releases/v49/RELEASE_MANIFEST.json` |
| Reader-facing objects / record-only entries | 5,423 / 2,572 | `frontend/generated/reader-eligibility-v49/manifest.json` |
| Distinct source labels / object-type labels / places | 272 / 271 / 424 | `frontend/src/data/status-v49.json` |
| Validated pairwise generic associations | 21 | `docs/research/EXPLORATION_CURRENT.md` |
| Open Inquiry higher-order hypotheses / known excluded structures | 11 / 9 | `docs/research/EXPLORATION_CURRENT.md` |
| Accepted typed historical relations / positive visual rights | 0 / 0 (fail-closed) | `database/FROZEN_V49.md` |
| Read API endpoint templates | 18 | `docs/api/v49-read-api-openapi.yaml` |
| Database migrations / functions / tests | 14 / 20 / 14 | `database/` |

## Architecture

```
institutional APIs and collections (15 in the public set)
        │  capture · period and region strategies · fallback and ingest policy
        ▼
reconciliation → canonical population (one byte-pinned payload, DATA_INPUT_MANIFEST.json)
        │  v48 → v49 replay, expected baseline, rehearsal
        ▼
PostgreSQL v49 (frozen: migrations, functions, roles, views, FREEZE_V49.json)
        │  read-only API role only
        ▼
Read API · 18 endpoints · OpenAPI 3.1 · read-only
        │  the frontend never opens a database connection
        ▼
Next.js frontend
   ├── desktop tree ─┐  share only lib/ and content; a 539-check audit
   └── mobile tree  ─┘  keeps them apart
        │
        ▼
reader · Index (5,423) · Search · Object records (7,995) · About · TRACE
```

## Research method and governance

- **Evidence over inference.** A described record is not a cleared image; metadata, rights and evidence are assessed separately, and clearing one never implies clearing another.
- **Absence is a finding.** What the archive leaves out stays recorded, countable and labelled unresolved; the year chart on the homepage draws the held share rather than omitting it.
- **Reproducible releases.** Releases are identified, hashed and re-derivable; a result can be returned to and checked against the state that produced it. The v49 files enumerated by `database/FREEZE_V49.json` are immutable; later work targets database version 50 with a new forward-only migration and a new ADR.
- **TRACE, in its governed public language:**

  > TRACE Exploration is an evidence-bounded system rather than a claim of complete historical closure. Its validated mode currently uses 21 evidence-qualified pairwise generic associations. Round 16B additionally records 11 scoped higher-order association hypotheses as unresolved open inquiries. These hypotheses are not counted as validated relations, do not generate implicit pairwise edges, and may appear only in explicitly labelled inquiry contexts. Nine further excluded higher-order structures are currently known, while the complete exclusion universe remains indeterminate.

  ```
  TRACE Exploration
  ├── Validated Exploration
  └── Open Inquiry
  ```

  `PAIR_ASSOCIATION_CLOSURE=false` · `HIGHER_ORDER_ASSOCIATION_CLOSURE=false` · `GLOBAL_COMPOSITION_COHERENCE_CLOSURE=false` · `PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE=false` · `COMPUTATIONAL_SPACE_CLOSURE=false` · `FUNCTION3_CLOSURE=false`

  Open Inquiry is an explicitly labelled, unresolved layer. It is not part of validated results and cannot add pair edges, validated compositions, topology, exports or metrics. External human review remains pending.

- **Rights boundary.** Software is governed by `LICENSE` (MIT); the original interface design and visual identity by `FRONTEND_DESIGN_LICENSE.md`; third-party material remains subject to its source terms.

## Frontend

| Surface | Route | What it does |
| --- | --- | --- |
| Home | `/` | The archive's identity, contribution and research status, drawn from the frozen release |
| Index | `/directory` | The 5,423 reader-facing objects by year, place, object type and theme, served by `/api/index/v1` |
| Search | `/search` | The live public Search API with exact counts, cursor paging, facets and starter queries; normal searches answer from the reader-facing projection, an exact identifier lookup may return a record-only entry and says so |
| Object record | `/surfaces/[id]` | Every public record by stable ID, as a full object page or an archive record |
| About and Source | `/about`, `/source` | Purpose, methodology, visual design rationale, the archive in numbers, contact and citation, sources and rights, claim boundaries |
| TRACE | `/trace/context-canvas`, `/trace/exploration` | The research views, desktop only by policy |

- Desktop and mobile are two component trees under every route (`desktop/`, `mobile/`), chosen on the server; a mobile change cannot reach the desktop except through a shared `lib/` module or content file, which the audit names.
- Verification is scripted: 48 test and verify entries in `frontend/package.json`, design-contract tests (`frontend/scripts/test-mobile-design.mjs`), API contract tests (`frontend/scripts/test-search-v2-api.mjs`), a presentation verifier with SSIM gates for Exploration, and release reviews under `docs/qa/`.

## Engineering practice

| Workflow | Trigger | Purpose |
| --- | --- | --- |
| `pr-fast` | pull request | Fast checks on every change |
| `repository hygiene` | push to `main`, pull request | Layout, retention and active-script allowlist audit |
| `small-db-integration` | pull request | Database integration on a small cluster |
| `v49 database freeze` | changes under `database/` | The frozen v49 files stay byte-identical |
| `Audit package self-contained` | changes to an audit package | Audit evidence stays self-contained |
| `manual-full-rehearsal` | manual | The full v48 → v49 replay |

- Immutable anchors: `v49-data-api-closure-20260821` (source closure) and `v49-research-main-integration-20260825` (research-history integration, fast-forward only from the old `main` anchor `592c765d0af5bf15b1666784dce784ac8e22624d`, preserving the 72 commits through the Round 9 tip `47978c519c3c7141690e3894315a1ef1b7a403db`). Ledgers: `docs/releases/v49/main-integration-20260825/`, `docs/audits/v49-main-integration-20260825/`.
- The former `db/` skeleton, raw capture trees, backups, pre-v49 generated artefacts and the full historical log are not active inputs; they remain recoverable from the immutable tag.

## Skills this repository demonstrates

| Skill | Evidence |
| --- | --- |
| Data engineering across heterogeneous sources | Fifteen institutional APIs reconciled into one canonical population with explicit missing/held semantics (`docs/capture/`, `docs/methodology/`) |
| Relational database design and release management | Forward-only migrations, SQL functions and tests, roles and views, a replayed and checksummed freeze (`database/`) |
| API design | An 18-endpoint OpenAPI 3.1 read contract with examples, an error catalog and a read-only role boundary (`docs/api/`) |
| Full-stack TypeScript | Next.js App Router with server-side adapters, strict typing, client hooks for live search, cursor paging and guidance (`frontend/src/`) |
| Research governance and honest computation | Fail-closed rights, evidence-qualified associations, an explicitly labelled open-inquiry layer, a gate that blocks any language-model note not grounded in on-screen facts (`docs/research/`, `frontend/src/features/system-suggestions/`) |
| Interface design | A written design system and decision record, a separate mobile tree with a measured type floor, a generative visual engine with verification gates (`docs/frontend/`, `frontend/src/features/trace-v49/exploration-view/`) |
| Engineering discipline | Six CI workflows, 41 audit packages, 6 ADRs, immutable tags, a documented change policy (`.github/workflows/`, `docs/audits/`, `docs/adr/`) |

## Run it

Database replay and verification:

```bash
database/data-migrations/v48-to-v49/run-rehearsal.sh
python3 scripts/repository/verify_v49_database_freeze.py
python3 scripts/repository/audit_repository_hygiene.py
```

Frontend and API checks:

```bash
cd frontend
npm install
npm run typecheck:runtime
npm run test:read-platform
node scripts/verify-page-by-key-module-contract.mjs
node scripts/run-runtime-acceptance-vectors.mjs
node scripts/test-mobile-design.mjs
node scripts/audit-mobile-desktop-coupling.mjs
npm run build
```

The exhaustive PostgreSQL-backed API harness is documented in `docs/audits/v49-api-read-contract-closure/` and must use the dedicated read-only API database role.

## Repository layout

- `database/` — the only active database root: migrations, functions, roles, views, fixtures, tests, and the v48 → v49 replay tooling.
- `frontend/` — the Next.js frontend and the server-side Read API implementation.
- `data/` and `generated/` — only the four byte-pinned v49 input and reconciliation artefacts listed in `docs/releases/v49/DATA_INPUT_MANIFEST.json`.
- `scripts/repository/` — repository hygiene, release-document and database-freeze verification tooling.
- `docs/api/` — Read API catalog, OpenAPI 3.1 contract, product route map and examples.
- `docs/architecture/`, `docs/operations/`, `docs/design/`, `docs/frontend/` — architecture, operations, design handoff and the design decision record.
- `docs/research/`, `docs/methodology/`, `docs/capture/` — research status, method rulebooks, capture strategies.
- `docs/releases/v49/` — immutable source, data-input, audit and freeze indexes.
- `docs/maintenance/` — repository layout, retention policy, inventories, branch and worktree ledgers.
- `docs/audits/` — indexed v49 audit evidence, including the final database, API and repository closure packages.

`generated/public_surfaces_prefreeze_candidate_v48.json` is the sole canonical population input. The v48 SQLite database and the two transfer manifests are reconciliation and integrity inputs only; they never backfill, infer, normalise or widen canonical state. Runtime data under `frontend/` is separate from the canonical migration input and stays active only while a documented consumer and checksum exist.

## Documentation entry points

- `docs/releases/v49/RELEASE_INDEX.md`
- `docs/releases/v49/AUDIT_INDEX.md`
- `docs/api/v49-read-api-catalog.md`
- `docs/frontend/FRONTEND_DESIGN_DECISION.md`
- `docs/research/EXPLORATION_CURRENT.md`
- `docs/research/trace-v49-exploration-round16b-main-integration/00_PUBLIC_LANGUAGE_AND_STATUS.md`
- `docs/releases/v49/main-integration-20260825/00_EXECUTIVE_DECISION.md`
- `docs/maintenance/DOCUMENTATION_MAP.md`
- `docs/maintenance/REPOSITORY_LAYOUT.md`
- `database/FROZEN_V49.md`
- `READ_API_V1.md`
- `PROJECT_LOG.md`

## Author

Dai Pan (潘岱) — project lead, sole author. Contact and citation guidance: the About page of the running site, or `frontend/src/app/about/content.ts`.
