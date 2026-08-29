# Graphic Design Archive

Graphic Design Archive is a rights-aware PostgreSQL-backed research archive for modern graphic design history. v49 closes and freezes the database/release projection and exposes the sealed release through the versioned read-only API.

## v49 status

- PostgreSQL schema and release projection: closed and frozen.
- Canonical objects / assignments: 15,923 / 47,982.
- Publicly eligible / held: 7,995 / 7,928.
- Accepted typed historical TRACE relations / positive visual rights: 0 / 0, fail-closed.
- Validated evidence-qualified pairwise generic associations: 21.
- Public Read API: 18 documented endpoint templates; search and pagination closed.
- Frontend: consumes the API/repository boundary and never connects directly to PostgreSQL.
- Immutable source anchor: `v49-data-api-closure-20260821`.

## TRACE Exploration — current public status

“TRACE Exploration is an evidence-bounded system rather than a claim of
complete historical closure. Its validated mode currently uses 21
evidence-qualified pairwise generic associations. Round 16B additionally
records 11 scoped higher-order association hypotheses as unresolved open
inquiries. These hypotheses are not counted as validated relations, do not
generate implicit pairwise edges, and may appear only in explicitly labelled
inquiry contexts. Nine further excluded higher-order structures are currently
known, while the complete exclusion universe remains indeterminate.”

```text
TRACE Exploration
├── Validated Exploration
└── Open Inquiry
```

`PAIR_ASSOCIATION_CLOSURE=false`

`HIGHER_ORDER_ASSOCIATION_CLOSURE=false`

`GLOBAL_COMPOSITION_COHERENCE_CLOSURE=false`

`PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE=false`

`COMPUTATIONAL_SPACE_CLOSURE=false`

`FUNCTION3_CLOSURE=false`

Open Inquiry is an explicitly labelled, unresolved layer. It is not part of
validated results and cannot add pair edges, validated compositions, topology,
exports, or metrics. External human review remains pending; frontend visual
design and deployment have not been performed.

## v49 research-history main integration

This section records the historical 2026-08-25 integration state. The complete linear v49 research and engineering chain was prepared for fast-forward-only integration from the old `main` anchor `592c765d0af5bf15b1666784dce784ac8e22624d`. The 72 existing commits through Round 9 tip `47978c519c3c7141690e3894315a1ef1b7a403db` are preserved without rewriting; the resulting `main` anchor is identified by annotated tag `v49-research-main-integration-20260825`.

The integration ledger and receipts are under `docs/releases/v49/main-integration-20260825/` and `docs/audits/v49-main-integration-20260825/`. Integration does not reactivate the superseded Round 6 object-similarity or Round 7 object-NLP approaches. Round 9 supplied grammar-research candidates only; it did not define active product vocabulary. Its then-next Round 10 gate is historical and has been completed.

## Repository layout

- `database/` — the only active database root: migrations, functions, roles, views, fixtures, tests, and v48→v49 replay tooling.
- `frontend/` — current Next.js frontend and server-side Read API implementation.
- `data/` and `generated/` — only the four byte-pinned v49 input/reconciliation artifacts listed in `docs/releases/v49/DATA_INPUT_MANIFEST.json`.
- `scripts/repository/` — repository hygiene, release-document, and database-freeze verification tooling.
- `docs/api/` — Read API catalog, OpenAPI 3.1 contract, interface map, and examples.
- `docs/architecture/`, `docs/operations/`, `docs/design/` — current architecture, operations, and design handoff indexes.
- `docs/releases/v49/` — immutable source, data-input, audit, and freeze indexes.
- `docs/maintenance/` — repository layout, retention policy, inventories, and branch/worktree ledgers.
- `docs/audits/` — indexed v49 audit evidence, including final DB, API, and repository closure packages.

The former `db/` skeleton, raw capture trees, backups, pre-v49 generated artifacts, prompts, reports, and the full historical project log are not active inputs. They remain recoverable from the immutable source tag without being copied into another active archive directory.

## Canonical and generated data boundary

`generated/public_surfaces_prefreeze_candidate_v48.json` is the sole canonical population input. The v48 SQLite database and two transfer manifests are reconciliation/integrity inputs only; they must never backfill, infer, normalize, or widen canonical state. Missing, null, empty-string, empty-array, absent-relationship, and quarantined semantics remain distinct.

Current frontend/runtime data under `frontend/` is separate from the canonical migration input. Generated files may remain active only when a current runtime, API, test, or release verification consumer and checksum are documented.

## Database and API commands

Database replay and verification:

```bash
database/data-migrations/v48-to-v49/run-rehearsal.sh
python3 scripts/repository/verify_v49_database_freeze.py
python3 scripts/repository/audit_repository_hygiene.py
```

Frontend/API checks:

```bash
cd frontend
npm install
npm run typecheck:runtime
npm run test:read-platform
node scripts/verify-page-by-key-module-contract.mjs
node scripts/run-runtime-acceptance-vectors.mjs
npm run build
```

The exhaustive PostgreSQL-backed API harness is documented in `docs/audits/v49-api-read-contract-closure/` and must use the dedicated read-only API database role.

## Freeze and change policy

The v49 files enumerated by `database/FREEZE_V49.json` are immutable. Subsequent database work must target database version 50 or later, use a new forward-only migration, preserve every v49 historical file, and include a new ADR. Frontend design work must not modify `database/**` or canonical release inputs; server adapters must conform to the frozen API contract.

## Rights boundary

This repository is a metadata, citation, and source-return layer, not a source-image mirror. Zero positive visual rights is an intentional release fact. Do not infer rights, acceptance, relations, or publication eligibility. Software is governed by `LICENSE`; original interface design and visual identity are governed separately by `FRONTEND_DESIGN_LICENSE.md`; third-party material remains subject to its source terms.

## Documentation entry points

- `docs/releases/v49/RELEASE_INDEX.md`
- `docs/releases/v49/AUDIT_INDEX.md`
- `docs/research/EXPLORATION_CURRENT.md`
- `docs/research/trace-v49-exploration-round16b-main-integration/00_PUBLIC_LANGUAGE_AND_STATUS.md`
- `docs/audits/v49-exploration-round16b-main-integration/`
- `docs/releases/v49/main-integration-20260825/00_EXECUTIVE_DECISION.md`
- `docs/maintenance/DOCUMENTATION_MAP.md`
- `docs/maintenance/REPOSITORY_LAYOUT.md`
- `database/FROZEN_V49.md`
- `READ_API_V1.md`
- `PROJECT_LOG.md`
