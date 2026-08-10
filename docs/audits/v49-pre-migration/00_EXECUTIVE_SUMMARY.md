# v49 Phase 1B comprehensive pre-migration audit — executive summary

## Scope

This report consolidates ten independent audit packages covering Git/history, files/storage, data/lineage, DDL readiness, TRACE research semantics, rights/visual federation, frontend/A4/build coupling, AI/RAG/SLM retirement, QA/accessibility evidence, and machine API/security/CI/deployment. The audited baseline is `f076ca3444aaa0f413bb61fe2cb568d6a9aa2720` on `refactor/v49-data-platform`; the frozen source ancestor is `0404c7f96f9189f576c4c5b1368061e4082e436b`.

This is an evidence and normative-calibration checkpoint. It implements no PostgreSQL schema, migration, verifier, API, adapter, fixture, frontend change, release, visual registry, CI workflow, cleanup execution, or deployment.

## Outcome

```text
AUDIT_COMPLETE=true
PRE_CLEAN_CLASSIFICATION_COMPLETE=true
REVERSIBLE_PRE_CLEAN_COMPLETE=true
DIRTY_MAIN_CLEANUP_EXECUTED=false
FROZEN_DATA_MUTATED=false
TRACKED_LEGACY_DELETED=false

ENGINEERING_PRE_DDL_READY=false
RESEARCH_SEMANTICS_PRE_DDL_READY=false
RIGHTS_VISUAL_PRE_DDL_READY=false
OVERALL_PRE_DDL_READY=false

DATABASE_IMPLEMENTED=false
DATABASE_FREEZE_READY=false
FRONTEND_PROMOTION_READY=false
DEPLOYMENT_READY=false
```

`AUDIT_COMPLETE=true` means all ten required partitions have a report, evidence commands, measured findings, priorities, non-actions, and process receipt. It does not convert a `PARTIAL` or `FAIL` readiness result into approval. The audit found unresolved P0s in engineering lineage, research semantics, rights federation, frontend/runtime, QA, and machine delivery; physical DDL must not begin yet.

## Audit coverage

| Package | Coverage | Readiness result | P0 / P1 / P2 | Primary output |
|---|---|---|---:|---|
| A1 Git/worktree/history/LFS | PARTIAL | PARTIAL | 2 / 6 / 1 | `01_GIT_WORKTREE_AND_HISTORY.md` |
| A2 files/storage/duplicates | COMPLETE | PASS | 3 / 4 / 2 | `02_FILE_AND_STORAGE_INVENTORY.md`, `02_FILE_INVENTORY.tsv` |
| A3 data authority/lineage | COMPLETE | PARTIAL | 5 / 5 / 3 | `03_DATA_ASSET_AUTHORITY_AND_LINEAGE.md` |
| A4 database/DDL readiness | COMPLETE | PARTIAL | 10 / 6 / 3 | `04_DATABASE_AND_DDL_READINESS.md` |
| A5 TRACE/research semantics | COMPLETE | PARTIAL | 8 / 6 / 4 | `05_TRACE_RESEARCH_SEMANTICS.md` |
| A6 rights/visual federation | COMPLETE | FAIL | 7 / 6 / 3 | `06_RIGHTS_AND_VISUAL_FEDERATION.md` |
| A7 frontend/A4/build coupling | COMPLETE | PARTIAL | 5 / 7 / 4 | `07_FRONTEND_A4_AND_BUILD_COUPLING.md` |
| A8 AI/RAG/SLM retirement | COMPLETE | PARTIAL | 2 / 6 / 1 | `08_AI_RAG_SLM_RETIREMENT.md` |
| A9 QA/accessibility evidence | COMPLETE | PARTIAL | 3 / 5 / 1 | `09_QA_ACCESSIBILITY_AND_VISUAL_EVIDENCE.md` |
| A10 API/security/CI/deployment | COMPLETE | FAIL | 7 / 7 / 3 | `10_MACHINE_API_SECURITY_CI_DEPLOYMENT.md` |

A1 is coverage-PARTIAL because a full historical `git fsck` was stopped under the no-output health rule and arbitrary-content historical secret assurance is not proved. All required Git/worktree/ref/LFS/large-blob/duplicate/governance surfaces were nevertheless measured. Across packages there are **52 P0, 58 P1, and 25 P2 contributed observations**. These 135 observations are not deduplicated; several packages independently identify the same root blocker.

## Frozen-source integrity and authority

The primary task performed one full SHA-256 pass over all five frozen assets and one immutable read-only SQLite integrity check.

| Artifact role | Bytes | SHA-256 | Result |
|---|---:|---|---|
| Canonical v48 JSON; only migration input | 190,067,852 | `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48` | PASS |
| SQLite; reconciliation only | 421,801,984 | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` | PASS; `integrity_check=ok` |
| Transfer manifest JSON; integrity evidence | 21,752 | `865358db84c15d960b3535969a32521c0ffec177f7455d21db86cd131f787d5b` | PASS |
| Transfer manifest CSV; integrity evidence | 12,861 | `694a60657077bcab8888c4a4ef1daf6059706e544606d4862e46c57dcf6ddc18` | PASS |
| TRACE manifest; derived-product integrity evidence | 83,900 | `1678e211023aa324078e0478f88670d2378b6dc5c398cc5c04722605038fee23` | PASS |

Search, atlas/catalogs, TRACE shards, and SQLite are derived or reconciliation products and may not supply missing canonical rows. Raw bytes, byte length, and hash are lexical authority; JSONB is only a parsed projection.

The frozen assets are byte-verifiable but the current clean tree is not self-sufficient for full v48 regeneration: builders refer to omitted v47 JSON/SQLite parents, and the 97,889-node/255,695-edge graph cannot be regenerated solely from the canonical JSON and governed configuration currently present. That is a P0 lineage/authority gap, not permission to ingest derived data.

## Population and count boundaries

| Unit | Exact result | Classification |
|---|---:|---|
| Canonical JSON / operational archive objects / active TRACE catalog | 15,923 | canonical parity |
| Legacy Search artifact | 8,636 | derived reconciliation |
| Search ∩ canonical/TRACE | 2,585 | derived reconciliation |
| Search-only | 6,051 | derived reconciliation; not migration input |
| Canonical/TRACE-only | 13,338 | derived reconciliation |
| Union | 21,974 | derived reconciliation |
| TRACE projection nodes | 97,889 | graph parity |
| TRACE projection edges | 255,695 | graph parity |
| Object-relation membership projections | 126,822 | graph parity |
| Review / auxiliary | 4,425 / 11 | derived layer reconciliation |

The row-level `metadata_supported` count is 2,971 while frozen manifest/meta evidence states 2,970. The one-row conflict remains explicit and promotion-blocking until an evidence-bearing delta decision exists. The former 20,000 target and derived 4,077 remainder are historical aspiration only and were removed from migration, freeze, release, and promotion gates.

## Repository and runtime ledger

The path-level authority/cleanup ledger contains 14,359 rows: all 3,419 v49 tracked paths, the initial audit output/ignored snapshot, and all 10,937 protected-main untracked paths.

| Classification | Paths | Bytes |
|---|---:|---:|
| `KEEP_ACTIVE` | 201 | 6,689,919 |
| `MIGRATE` | 973 | 499,759,140 |
| `ARCHIVE_READ_ONLY` | 12,998 | 14,206,109,066 |
| `GENERATED_REPRODUCIBLE` | 0 | 0 |
| `DELETE_CANDIDATE` | 11 | 447,239 |
| `HOLD_UNKNOWN` | 176 | 7,967,299,304 |

`DELETE_CANDIDATE` is not deletion approval. No candidate was deleted. Protected main contains about 20.6 GB of untracked material and remains completely out of migration inputs.

After A9 semantic/provenance review, the consolidated action ledger conservatively overrides the ten QA duplicate non-keepers to `HOLD_UNKNOWN`. Effective action counts are therefore `KEEP_ACTIVE=201`, `MIGRATE=973`, `ARCHIVE_READ_ONLY=12,998`, `GENERATED_REPRODUCIBLE=0`, `DELETE_CANDIDATE=1`, and `HOLD_UNKNOWN=186`; report 11 preserves both the mechanical snapshot and this governing override.

Additional measured surfaces:

- historical Git: 14,693 blobs, 22.05 GB logical content, 78 blobs at least 100 MiB, four current LFS pointers, 113 duplicate-OID groups;
- direct frontend/data coupling: 26 runtime/compile consumers plus 9 producer scripts = **35 files**;
- A4/page/static-render execution entrances: **9** (one `next build`, two `generateStaticParams` routes, six Puppeteer screenshot/accessibility executables); nine static-data producer/exporter scripts are tracked separately;
- AI/RAG/SLM retirement ledger: **75 logical units** = 10 remove from runtime, 22 archive for history, 42 keep as documentation, 1 unknown; nested repositories' 892 tracked files are context, not double-counted;
- QA: 60/60 files hashed; all are JPEG bytes, 26 have `.png` extensions, 50 unique hashes, seven duplicate groups/ten redundant copies, and no evidence manifest or rights provenance;
- machine delivery: one current POST assistant API route, zero `/api/v1` routes, zero API/release schemas, zero JSON-LD/DCAT/change-feed/sitemap implementations, zero CI workflows, and zero deployment config.

## Consolidated P0 blockers

1. **Authority and reproducibility** — missing current-tree v47 parent assets, graph regeneration gap, 2,970/2,971 conflict, and incomplete artifact-level disposition for 1,266 tracked raw files (manifest says 29 directories; observed 26).
2. **Physical schema boundary** — legacy `db/*.sql` is an 82-table/55-view public-schema prototype with unconstrained polymorphic targets and no v49 roles, subtype exclusivity, dual seals, or CAS. Its runner must be execution-denied for v49.
3. **Research semantics** — operational archive object is not unique-work identity; assertions, claims, semantic relations, evidence, decisions, and TRACE projections require separate identities/cardinalities. Four epistemic classes, influence/computed provenance, corpus selection, missingness, coverage, and concentration are not implemented.
4. **Rights/visual federation** — 15,621 external image URLs across 49 hosts exist; provider/endpoint identity, observations/policies, independent assessment/delivery/health axes, attribution, review-due, takedown, sealed visual registry, and CAS are absent. Unknown/missing/conflict/stale must fail closed to `LINK_ONLY` or `CITATION_ONLY`.
5. **Runtime and frontend** — the approximately 90.9 MB legacy payload and fixed Search/TRACE assets remain directly coupled; unknown relation fallback and remote-pixel delivery remain fail-open; `/contents` expands 26,041 memberships and the largest folder has 5,740 members.
6. **AI retirement** — active Qwen preparation/runtime paths remain in the frontend, and the protected-main retirement copy is untracked/non-authoritative.
7. **QA and accessibility** — current screenshots have no rights/capture/release/registry manifest and do not evidence keyboard, screen-reader, reduced-motion, source-drawer, error, font, color, focus, or ARIA acceptance.
8. **Machine publication/security delivery** — stable relation/claim URIs, GET-only read API, schemas, crawlable HTML, JSON-LD/Linked Art/PROV-O/DCAT, diff feed, sitemap, separated CI, SBOM/NOTICE, and rights-leakage tests do not exist.

## Normative calibration

The nine existing v49 architecture documents and new ADR 0004 now define:

- operational archive-object semantics and persistent crosswalk/merge/split/redirect policy;
- a closed `core.entity` model and no unconstrained `target_type + target_id`;
- separate assertions, canonical assignments, evidence, curator decisions, epistemic claims, semantic relations, and TRACE projections;
- four epistemic claim classes plus corpus selection, missingness, coverage, and concentration;
- Search as a sealed projection rather than a second canonical database;
- independent exact `(researchReleaseId,researchManifestSha256)` and `(visualRegistryVersion,registrySha256)` boundaries, manifests, sidecars, and CAS pointers;
- rights assessment, delivery mode, endpoint health, workflow, acceptance, publication layer, epistemic class, and metric eligibility as orthogonal axes;
- repository hygiene, research/data-quality, machine-readable contract, and rights/visual federation gates;
- canonical/graph/derived/historical count classes and a prototype-only full-build prohibition.

These corrections close vocabulary ambiguity but not the measured evidence gaps. `OVERALL_PRE_DDL_READY` remains false.

## Evidence commands

Package reports record exact commands. Consolidation used only read-only Git/file queries, bounded metadata/signature/hash scans, immutable SQLite URI queries, Markdown/path/terminology checks, `git diff --check`, changed-file allowlist checks, and sanitized process listings. The primary full-hash and integrity commands are recorded in `13_PROCESS_AND_COMMAND_RECEIPT.md`.

## Risk and recommended action

Starting physical DDL now risks encoding derived TRACE structure as canonical fact, losing raw/provider evidence, conflating catalog records with works, and making visual authorization inseparable from research releases. Starting frontend integration now risks preserving the current full-payload, model-runtime, static-generation, and remote-pixel coupling behind a new interface without closing authority gates.

At most three independent next tasks are authorized by this audit design, each with its own acceptance boundary:

1. **Authority and research-delta closure** — classify every legacy graph fact as regenerable, governed external evidence, or hold; restore/replace only authoritative builder inputs; resolve 2,970/2,971; complete raw artifact disposition. Exit: zero unclassified graph facts and signed reconciliation decisions, without DDL or derived-row ingestion.
2. **Rights visual-registry decision pack** — complete provider/object/endpoint crosswalk, rights observations/policy/attribution/review/takedown rules, held-pixel projection rules, and exact visual seal/CAS contract. Exit: every external visual/reference has a fail-closed disposition and the logical-to-physical mapping is review-approved, without downloading images.
3. **Fresh physical-schema specification and privilege test plan** — design migrations from an empty namespace, isolate the legacy runner, map every typed FK/state/natural key/role/dual-seal rule, and specify negative SQL tests. Exit: all pre-DDL evidence gates PASS and migration review authorizes DDL; no import or frontend work is included.

## Actions explicitly not performed

No npm/Next/TypeScript build or server, browser automation, Docker, PostgreSQL creation/query/migration, data export/regeneration, image download, destructive cleanup, package/CI/deployment/frontend/QA/frozen-data edit, PR, merge, rebase, force push, or deployment was performed. No secret value was printed. Protected dirty main was not modified.
