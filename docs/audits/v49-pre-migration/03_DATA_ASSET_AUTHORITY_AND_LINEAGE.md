# 03 — Data Asset Authority and Lineage

- Audit package: A3
- Audit date: 2026-08-11 (Australia/Brisbane)
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Baseline branch: `refactor/v49-data-platform`
- Scope result: **PARTIAL**
- Coverage result: **COMPLETE** for the requested repository data-asset boundary
- Database mutation: **none**
- Frozen asset mutation: **none**

`PARTIAL` describes readiness, not scan coverage. The repository inventory, authority roles, population sets, v48 SQLite relationships, and current lineage chain were measured. Five P0 data-governance gaps remain: current-checkout regeneration depends on absent v47 parent assets; the TRACE generator depends on reconciliation/legacy products rather than JSON alone; one frozen JSON summary counter disagrees with row-level data; tracked raw-provider payloads have no repository-level redaction-review receipt despite an explicit non-commit policy; and the historical 20,000/4,077 aspiration still appears in migration-facing material.

## 1. Scope

This package covers:

- all tracked `JSON`, `CSV`, `SQLite`, `SQL`, shard, manifest, and receipt assets;
- the authority role of canonical, reconciliation, integrity-evidence, derived, historical, experimental, and unknown assets;
- v48 lineage and whether a clean checkout can reproduce or independently reconcile it;
- ID sets, duplicate IDs, null/blank values, orphans, delimiter-packed fields, and graph count units;
- the 8,636 Search population versus the 15,923 canonical/TRACE population;
- the 255,695 TRACE graph edges versus 126,822 object-relation memberships;
- the 4,425 review and 11 auxiliary layers;
- legacy, intermediate, and cache-like databases;
- migration/freeze blockers that follow from the measured data.

Affected paths include `data/`, `generated/`, `frontend/public/data/`, `frontend/src/data/`, `db/`, `scripts/`, and the v49 architecture documents used to interpret authority. This audit did not interpret visual quality, runtime UX, rights eligibility, or TRACE epistemic claims beyond their data-lineage consequences; those belong to A5, A6, A7, A9, and A10.

## 2. Explicit non-actions

The following actions were explicitly not performed:

- no PostgreSQL or Docker process was started;
- no SQLite write connection, migration, `VACUUM`, journal, WAL, or sidecar was created;
- no data was exported, regenerated, normalized, or rewritten;
- no `npm`, Next.js, TypeScript, browser, screenshot, or frontend build command ran;
- no third-party content was downloaded;
- no five-asset full SHA-256 pass was repeated by A3; the main auditor owns that single pass;
- no second `PRAGMA integrity_check` was run; the main auditor owns the single current-run integrity check;
- no frozen manifest, shard, receipt, JSON, CSV, or SQLite file was edited;
- no candidate was deleted or moved;
- no secret value was read or printed;
- no commit, push, merge, PR, or deploy was performed by A3.

All SQLite queries in this package used the URI form:

```text
file:/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform/data/<database>.sqlite?mode=ro&immutable=1
```

## 3. Evidence commands

Commands below are representative exact forms. Long result tables are summarized in the measured-results sections.

| Purpose | Read-only command |
| --- | --- |
| Tracked format inventory | `git ls-files` grouped by extension and top-level path with `awk` |
| Database/manifest discovery | `find . -type f \( -iname '*.sqlite' -o -iname '*.db' -o -iname '*.sql' -o -iname '*manifest*' -o -iname '*receipt*' \) -print` |
| Critical file size/signature | `stat -f '%N|%z|%Sm' ...` and `file ...` |
| SQLite schemas | `sqlite3 'file:.../prefreeze_candidate_v48.sqlite?mode=ro&immutable=1'` with `pragma_table_info(...)` |
| SQLite counts/cardinality | Immutable SQLite `SELECT count(*)`, `count(DISTINCT ...)`, grouped collision, packed-field, and relation-family queries |
| Search/canonical/TRACE set comparison | One read-only Python process loaded Search and TRACE compact JSON and selected canonical IDs from immutable SQLite; it printed only aggregate set sizes |
| TRACE manifest coverage | Python parsed `manifest.json`, checked every declared path and byte length, and counted shards; it did not recompute asset hashes |
| Transfer manifest agreement | Python compared the 65 JSON entries and 65 CSV rows after string-normalizing `bytes` |
| Legacy duplicate payloads | `git rev-parse HEAD:<path>` on the three 8,636-surface payload copies |
| Missing parent recovery refs | `git cat-file -e`, `git rev-parse`, and `git cat-file -p` on historical v47 paths and LFS pointers |
| Capture manifest drift | Python compared `capture_run_manifest_v1.csv` paths with current directories and tracked files |
| Frozen gate receipts | `rg -n 'orphan|broken|unlinked|integrity|trace_adjunct' data/prefreeze_candidate_v48_*gate.csv` |
| Residual session state | Every A3 unified execution cell returned completion; the final global OS process scan is assigned to the main auditor because `ps` is sandbox-restricted here |

The A3 set-comparison program opened the v48 database with Python `sqlite3.connect(..., uri=True)` and the exact `mode=ro&immutable=1` URI. It created no temporary database or output file.

## 4. Repository data inventory

### 4.1 Tracked format counts

At the baseline commit, existing data-like files are tracked; the only untracked tree seen by A3 was the concurrently created `docs/audits/` output tree.

| Format | Tracked files | Location split |
| --- | ---: | --- |
| JSON | 1,915 | `data/` 1,311; `frontend/` 587; `generated/` 16; `db/` 1 |
| CSV | 447 | all under `data/` |
| SQLite | 3 | all under `data/` |
| SQL | 14 | all under `db/` |

Important subgroups:

- 1,271 provider/probe JSON files occur in paths named `_raw/` or `/raw/`;
- 30 manual source-record JSON files and 8 remediation source-record JSON files are separate from those raw captures;
- 576 JSON files are TRACE neighborhood shards;
- 581 files form the complete checked-in TRACE v48 product, including its manifest;
- 85 tracked paths contain `manifest` or `receipt` in their names;
- 13 tracked files occur under `data/backups/`;
- 46 top-level `capture_batch*_records.csv` files use three distinct header schemas: 42 files have 48 fields, two have 35 fields, and two have 38 fields.

The main data storage measured by `du -sk` is approximately:

| Path | KiB |
| --- | ---: |
| `data/` | 1,255,028 |
| `generated/` | 471,260 |
| `frontend/public/data/` | 223,760 |
| `frontend/src/data/` | 98,368 |
| `db/` | 4,116 |

These are allocation figures, not byte-authority values and not freeze gates.

### 4.2 Critical files and signatures

| Path | Bytes | Signature | Role |
| --- | ---: | --- | --- |
| `generated/public_surfaces_prefreeze_candidate_v48.json` | 190,067,852 | JSON/ASCII, single very long line | sole v48 migration input |
| `data/prefreeze_candidate_v48.sqlite` | 421,801,984 | SQLite 3.x | frozen reconciliation snapshot |
| `generated/prefreeze_candidate_v48_transfer_manifest.json` | 21,752 | JSON | integrity/transfer evidence |
| `data/prefreeze_candidate_v48_transfer_manifest.csv` | 12,861 | CSV | human-audit mirror of transfer evidence |
| `frontend/public/data/trace-v48/manifest.json` | 83,900 | JSON | integrity evidence for derived TRACE assets |
| `frontend/public/data/archive-search-v1.json` | 22,695,973 | JSON | derived legacy Search projection |
| `frontend/src/data/public_surface_mock_v0.json` | 90,895,254 | JSON/ASCII, single very long line | legacy 8,636-surface payload |
| `data/prefreeze_candidate_v46.sqlite` | 419,688,448 | SQLite 3.x | historical/intermediate reconciliation snapshot |
| `generated/public_surfaces_prefreeze_candidate_v46.json` | 190,039,480 | JSON | historical/intermediate candidate |
| `data/archive_seed.sqlite` | 2,912,256 | SQLite 3.x | legacy planning/seed database, not v48 archive data |

### 4.3 Database inventory

| Database | Measured contents | Authority/classification | Risk and action |
| --- | --- | --- | --- |
| `data/prefreeze_candidate_v48.sqlite` | 15,923 objects; 97,889 nodes; 255,695 edges; 126,822 memberships; 47,982 folder refs; 4,425 review rows | `ARCHIVE_READ_ONLY`; reconciliation only | Never use it to fill a missing JSON row/field. Keep immutable as v48 evidence. |
| `data/prefreeze_candidate_v46.sqlite` | 15,921 objects; 97,845 nodes; 255,638 edges; 126,798 memberships; 4,425 review rows | `ARCHIVE_READ_ONLY`; old intermediate | Do not treat the numeric delta to v48 as a complete lineage because the missing v47 parent lies between them. Move to versioned cold archive only after recovery validation. |
| `data/archive_seed.sqlite` | Legacy planning tables, including 1,542 `search_docs`, 66 sources, 200 vocabulary rows, coverage and source-priority skeleton data | `HOLD_UNKNOWN`; legacy planning seed | Namespace and deprecate before any v49 execution. It is neither the 8,636 Search product nor the 15,923 canonical cohort. |

The 14 SQL files under `db/` are an older PostgreSQL skeleton. They include a generated `010_seed_data.sql` and validation constants that do not describe the accepted v49 supertype, release, provenance, and privilege decisions. Their status for v49 is `HOLD_UNKNOWN`, with a recommended action of archival/deprecation before new DDL is introduced. They must not be executed as v49 migrations.

## 5. Authority and lifecycle classification

Authority is not inferred from file size, filename, Git tracking, or API provenance. The following classifications are normative for migration planning.

| Path/pattern | Count | Authority | Classification | Source/owner | Recovery reference | Proposed action | Deletion risk |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| `generated/public_surfaces_prefreeze_candidate_v48.json` | 1 | lexical and migration authority | `MIGRATE` | frozen v48 candidate | checkpoint `0404c7f`; transfer/freeze receipts | ingest raw bytes once, then parsed projection and typed rows | critical/irrecoverable without LFS and Git |
| `data/prefreeze_candidate_v48.sqlite` | 1 | reconciliation only | `ARCHIVE_READ_ONLY` | v48 search/TRACE builder | checkpoint plus manifest SHA | immutable reconciliation; never canonical fallback | critical validation evidence |
| v48 transfer JSON/CSV | 2 | integrity/transfer evidence | `ARCHIVE_READ_ONLY` | v48 freeze process | checkpoint and freeze receipt | preserve as paired evidence | high; loss weakens transfer audit |
| TRACE v48 manifest | 1 | derived-product integrity evidence | `ARCHIVE_READ_ONLY` | TRACE visualization build | checkpoint `0404c7f` | preserve with its exact product | high for QA/recovery, not canonical data |
| TRACE atlas/catalog/review/auxiliary/neighborhoods | 580 | derived read product | `GENERATED_REPRODUCIBLE` only relative to all four legacy inputs named by its generator | TRACE visualization build | TRACE manifest lists all assets | keep frozen product; do not migrate as authority | medium; reproducibility currently has a source-authority gap |
| `archive-search-v1.json` | 1 | derived legacy search index | `GENERATED_REPRODUCIBLE` | frontend Search generator | source payload and generator in Git | preserve for v48 behavior only; regenerate v49 Search from sealed release | low after behavior evidence is sealed |
| three `public_surface_mock_v0`/`public_surfaces_v1` copies | 3 | legacy 8,636-surface presentation payload, not v49 source authority | `DELETE_CANDIDATE` after runtime refactor and archival receipt | old frontend archive | all three resolve to Git blob `7efcc95620697d1938b491381d019cea8e8e318f` | retain one cold reference; remove redundant runtime copies in later cleanup | high before Search/runtime decoupling |
| v46 JSON/SQLite, holds, and draft manifests | 7 principal assets across `generated/`, `data/`, and SQLite | historical/intermediate | `ARCHIVE_READ_ONLY` | pre-v48 candidate work | historical commits/LFS | cold archive; exclude from migration | high while v47 lineage remains unresolved |
| `generated/` archive-primer, stress, and Qwen probes | 6 | generated experiments | `HOLD_UNKNOWN` | multiple experiments | Git history | owner-by-owner retirement/archival review | medium; some carry unique experiment evidence |
| v47 adjunct and v48 remote-verification JSON | 2 | selected evidence / transfer verification | `ARCHIVE_READ_ONLY` | v47/v48 freeze work | transfer manifest and Git history | preserve with explicit evidence role; never canonical input | high if removed before lineage closure |
| 1,271 raw/probe JSON files | 1,271 | provider-response evidence only where capture context is complete | `HOLD_UNKNOWN` pending redaction/rights/provenance receipts | capture scripts/providers | Git history; selected 30 are in v48 transfer manifest | inventory artifact hash, provider, request context, policy, and review before any raw-layer use | high: source terms, PII-like fields, unstable payloads, incomplete lineage |
| 30 manual + 8 remediation source records | 38 | authored source evidence, not canonical object rows | `ARCHIVE_READ_ONLY` pending governed re-ingest | project curation | Git history | retain and map to provenance only through a new ingest decision | high if unique manual research is lost |
| 447 CSV files | 447 | mixed raw-normalization, capture, queue, quality, gate, summary, repair, and manifest evidence | mostly `ARCHIVE_READ_ONLY` or `HOLD_UNKNOWN` | many capture/build stages | Git history and capture docs | classify per run; only explicitly selected v48 evidence may support reconciliation | high if treated as one coherent schema |
| `db/*.sql` | 14 | obsolete/legacy schema and generated seeds | `HOLD_UNKNOWN` | pre-v49 database skeleton | Git history | mark non-executable for v49; archive after DDL replacement | severe if accidentally executed |
| `data/backups/**` | 13 | point-in-time working backups | `ARCHIVE_READ_ONLY` pending duplicate/recovery review | historical capture repairs | directory manifests and Git | retain until A2 duplicate ledger proves recovery source | medium |

No `DELETE_CANDIDATE` was deleted. Classification does not authorize execution.

## 6. Frozen v48 authority and receipts

The five frozen artifacts and expected SHA-256 values are:

| Artifact | Expected SHA-256 | Authority |
| --- | --- | --- |
| Candidate JSON | `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48` | sole migration input; raw bytes are lexical authority |
| SQLite | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` | reconciliation only |
| Transfer manifest JSON | `865358db84c15d960b3535969a32521c0ffec177f7455d21db86cd131f787d5b` | integrity evidence |
| Transfer manifest CSV | `694a60657077bcab8888c4a4ef1daf6059706e544606d4862e46c57dcf6ddc18` | human-audit integrity evidence |
| TRACE manifest | `1678e211023aa324078e0478f88670d2378b6dc5c398cc5c04722605038fee23` | derived TRACE integrity evidence |

A3 intentionally did not recalculate these full hashes. The main audit performs the single coordinated pass. A3 instead established:

- the transfer JSON declares 65 files and 613,077,245 bytes;
- all 65 declared paths exist and match declared byte lengths;
- transfer batches contain 13 contract files, one canonical JSON, one SQLite snapshot, and 50 evidence/validation files;
- the JSON and CSV manifests both contain 65 ordered rows and are field-for-field equal after normalizing the numeric `bytes` value to text;
- the TRACE manifest declares 580 generated assets: 576 neighborhood shards and four top-level products;
- every declared TRACE asset exists and matches its declared byte length;
- the TRACE generator gate says `PASS` with zero declared failures;
- including its manifest, the frozen TRACE directory contains 581 data-product files.

Manifest claims are evidence, not self-validating truth. Current byte/hash and SQLite integrity acceptance depends on the main auditor's independent checks.

## 7. Lineage reconstruction

### 7.1 Canonical v48 chain

The checked-in builders declare this chain:

```text
generated/public_surfaces_prefreeze_candidate_v47.json
  + data/prefreeze_candidate_v48_loc_geo_repairs.csv
  + v48 trace node/edge CSVs
  + selected AIC route changes
  -> generated/public_surfaces_prefreeze_candidate_v48.json

data/prefreeze_candidate_v47.sqlite
  + canonical v48 JSON
  + v48 repair node/edge CSVs
  -> data/prefreeze_candidate_v48.sqlite
```

The current checkout does **not** contain either direct parent:

- `generated/public_surfaces_prefreeze_candidate_v47.json` — missing from the current tree;
- `data/prefreeze_candidate_v47.sqlite` — missing from the current tree.

Historical Git commit `31f8481`/source lineage commit `1d919fb0e6c5ed5bba9bf728cf7aa27fb7ce821b` retains LFS pointers:

- v47 JSON LFS object: `bc9d83892c91beabc7a1ec593f4d4315d7f377f3d9d98df6e2f20b082142ff7f`, size 190,062,921;
- v47 SQLite LFS object: `e3b597f365960007562aa8715fcbc713220239c6a011b3040fd926ae4e47cd7c`, size 421,670,912.

This is a recovery reference, not proof that a clean clone can fetch the LFS bodies. No fetch was attempted.

The current tree does contain the 18 v48 LOC response files, repair CSV, repair node/edge CSVs, builder scripts, final JSON, final SQLite, and selected v47 AIC evidence. Thus the frozen outputs are byte-addressable and reconcilable, but the declared transformation cannot run from current-tree inputs alone.

**Verdict:** v48 is independently **verifiable as a frozen artifact set**, subject to the main hash/integrity pass; it is **not self-reproducible from the present clean checkout** without recovering two historical LFS parent assets. These are distinct properties and must not share one gate.

### 7.2 TRACE derived-product chain

`scripts/build_prefreeze_candidate_v48_trace_visualization.py` reads four inputs:

1. frozen v48 SQLite;
2. canonical v48 JSON;
3. v47 AIC TRACE adjunct JSON;
4. legacy 8,636-surface frontend payload.

It then emits the atlas, active catalog, review catalog, auxiliary catalog, 576 shards, and manifest. The active graph structure and review rows are read from SQLite; the frontend payload controls whether an active TRACE object gets an internal `/surfaces/<id>` route; adjunct content comes from a separate v47 artifact.

This is reproducible as a legacy visualization build while all four inputs exist, but it does not satisfy the v49 decision that TRACE nodes/edges may enter canonical v49 research data only when a deterministic transformation regenerates them from the canonical JSON plus governed configuration. SQLite is reconciliation-only and the 8,636 frontend payload is a derived legacy artifact. Therefore:

- TRACE files remain valid v48 read/QA evidence;
- they are not migration inputs;
- graph facts absent from canonical JSON cannot be promoted merely because SQLite or shards contain them;
- before graph migration, a delta ledger must identify which nodes, relations, evidence locators, and review data can be regenerated from authoritative inputs and which remain held.

The generator also opens SQLite with `mode=ro` rather than `mode=ro&immutable=1`; A3 did not run it. A future archival verifier must use the stricter immutable URI.

### 7.3 Search chain

`frontend/scripts/generate-archive-search-index.mjs` reads `frontend/src/data/public_surface_mock_v0.json` and writes `frontend/public/data/archive-search-v1.json`. It performs a projection into a compact schema and has no independent authority.

The following paths share the exact Git blob `7efcc95620697d1938b491381d019cea8e8e318f`:

- `generated/public_surfaces_v1.json`;
- `frontend/public/data/public_surface_mock_v0.json`;
- `frontend/src/data/public_surface_mock_v0.json`.

Search is therefore reproducible from a checked-in legacy derived payload, but it must not seed `raw`, `core`, or a second canonical database. v49 Search must be derived from a sealed release cohort.

### 7.4 Capture lineage

`data/capture_runs/capture_run_manifest_v1.csv` declares:

- 44 capture runs and 19,886 record rows;
- 35 runs included by the old public rebuild script and 9 not included;
- stages: 18 `public_surface_rebuild_input`, 13 `item_image_capture`, 9 `capture_records_unclassified`, 2 `source_profile_or_context`, and 2 `empty_or_pending`.

Current-path comparison found:

- 26 declared raw directories actually present, not the manifest/document claim of 29;
- 1,266 files under those 26 directories, all tracked;
- all 26 present raw directories carry `do_not_commit_without_redaction_review` in the manifest;
- three directories are declared present but absent now: `capture_batch_edge_source_registry_context_1931_2026_raw`, `capture_batch_loc_deep_image_ready_1931_1970_raw`, and `capture_batch_source_coverage_gap_1931_2026_raw`;
- two record CSVs are outside this capture-run manifest, but both are explicitly selected v47 TRACE/AIC evidence in the v48 transfer manifest.

No repository-level receipt proving redaction/terms review for all 1,266 tracked raw files was found in A3's data boundary. Git tracking alone cannot stand in for that review.

## 8. Population and count-unit ledger

### 8.1 Search, canonical, and TRACE sets

Let:

- `C` be v48 canonical/reconciliation object IDs;
- `T` be v48 active TRACE catalog IDs;
- `S` be archive Search IDs.

One read-only set comparison measured:

| Set | Rows | Unique IDs | Blank IDs |
| --- | ---: | ---: | ---: |
| `C` from immutable SQLite reconciliation | 15,923 | 15,923 | 0 |
| `T` from TRACE active catalog | 15,923 | 15,923 | 0 |
| `S` from archive Search | 8,636 | 8,636 | 0 |

`C == T` is true. Cross-set boundaries are:

| Population expression | Count |
| --- | ---: |
| `C ∩ S` | 2,585 |
| `S − C` | 6,051 |
| `C − S` | 13,338 |
| `C ∪ S` | 21,974 |

Consequences:

- Search is not a subset of canonical/TRACE;
- the 6,051 Search-only IDs are derived-product exclusions, not missing migration rows;
- the future v49 Search result count is not required to equal 8,636;
- no `remaining to 20,000` value is derivable from this union or usable as parity.

### 8.2 Canonical and graph units

| Unit | Exact count | Meaning |
| --- | ---: | --- |
| active canonical objects | 15,923 | one v48 JSON/reconciliation surface row per seed object |
| source records | 15,923 unique IDs | one seed description per canonical row |
| source documents | 12,635 | documents can describe more than one object |
| folders | 185 | folder entities in v48 presentation model |
| folder memberships | 47,982 | unique `(surface_id, folder_id)` rows |
| TRACE nodes | 97,889 | graph nodes, not archive objects |
| TRACE graph edges | 255,695 | unique edge IDs; full graph unit |
| active-object relation memberships | 126,822 | unique `(surface_id, edge_id)` rows; active object projection unit |
| active TRACE trees | 30 | tree labels represented in active objects |
| source-verified active objects | 12,952 | row-level `trace_tier` |
| metadata-supported active objects | 2,971 | row-level `trace_tier`; see frozen metadata conflict below |
| review/authority hold | 4,425 | separate, count-ineligible review layer |
| auxiliary | 11 | separate, count-ineligible TRACE adjunct layer |
| historical influence edges | 0 | no inferred `influenced_by` edges |

The 126,822 active-object memberships group into:

| Relation family | Membership rows |
| --- | ---: |
| `medium_context` | 79,206 |
| `source_provenance` | 31,288 |
| `time_place` | 16,328 |
| **total** | **126,822** |

These are memberships, not the 255,695 total graph edges. A parity query must name the table/unit, release layer, and eligibility predicate.

### 8.3 Review and auxiliary separation

- `review-catalog.json` declares layer `review` and contains 4,425 rows;
- `auxiliary.json` declares `countEligible=false` and contains 11 items;
- saved v48 freeze/search gates report zero review/authority leakage into active and zero auxiliary leakage into active;
- neither 4,425 nor 11 may be added to 15,923 to create a canonical parity target;
- workflow state, publication layer, acceptance state, and count eligibility remain independent axes.

## 9. Identity, null, orphan, and packed-field results

### 9.1 Object/source identities

Measured in immutable v48 SQLite:

- 15,923 object rows and 15,923 unique `surface_id` values;
- 15,923 nonblank and unique `source_record_id` values;
- 15,923 unique `trace_object_node_id` values;
- 15,921 unique `(identity_scope, source_object_key)` pairs;
- 12,635 distinct source-document IDs, whose declared `object_count` values sum to 15,923;
- 86 source documents are explicitly marked shared.

The two scoped source-key collisions are:

| Scoped key | Surfaces |
| --- | --- |
| `explicit_source_object_key / 2016648591` | `SURF-CGS2026R0740`; `SURF-LOCTRACE2026R02046` |
| `explicit_source_object_key / 96523423` | `SURF-CGS2026R0383`; `SURF-LOCTRACE2026ICC0337ACE0D517` |

Therefore provider/source object keys are attributes, not primary or unique keys. No automatic merge is justified.

### 9.2 TRACE identities and evidence

- 97,889 `trace_nodes` rows have 97,889 unique node IDs;
- only 82,918 canonical keys are unique;
- even `(tree_id, node_type, canonical_key)` produces only 97,647 groups;
- 255,695 edge IDs are present;
- the accepted Phase 1A measurement records 255,695 unique directed `(subject_node_id, edge_label, object_node_id)` triples;
- 126,822 membership rows cover all 15,923 canonical objects, with 126,822 distinct edge IDs in the active-object projection;
- saved freeze gates report zero orphan subject endpoints, zero orphan object endpoints, and zero broken object-edge references;
- edge evidence has zero blank URLs, three blank evidence texts, and zero blank evidence fields;
- Phase 1A records 255,247 distinct `(evidence_url, evidence_text, evidence_field)` composites, with 389 composites reused across 837 edges and a maximum reuse of 7.

Evidence is consequently shareable and not edge identity. The three blank texts require a held evidence-quality rule or an explicitly valid locator-only evidence class before graph migration.

### 9.3 Null and placeholder observations

For canonical object rows:

- blank `surface_id`, `source_record_id`, `source_locator`, `title`, `source_url`, `trace_object_node_id`, and `trace_tree_id`: 0 each;
- blank/null `image_url`: 302;
- blank `source_subjects`: 458;
- `creator`, `medium`, and `object_type` columns are physically nonblank, but this does not mean the values are known; for example, `creator='Unknown'` occurs 2,477 times and `creator='Unknown author'` occurs 198 times.

Missing, unknown, empty, null, held, and not-applicable values must not be collapsed in v49.

### 9.4 Delimiter-packed fields

Rows containing delimiters were measured as follows:

| Field/delimiter | Rows |
| --- | ---: |
| `objects.creator` contains `;` | 3,849 |
| `objects.creator` contains `|` | 4 |
| `objects.medium` contains `;` | 10,791 |
| `objects.medium` contains `|` | 567 |
| `objects.object_type` contains `;` | 7,117 |
| `objects.source_subjects` contains `;` | 15,233 |
| `objects.source_subjects` contains `|` | 22 |
| `capture_records.branch_ids` contains `;` | 9,934 |

No newline-packed rows were found in those fields. Delimiter presence is a migration-candidate signal, not a safe universal parser rule: literal punctuation, provider conventions, and field-specific escaping must be preserved in raw values while typed assignments are created with explicit transformation evidence.

## 10. Conflicts and readiness findings

### P0

| ID | Finding | Affected paths | Risk | Required action / acceptance boundary |
| --- | --- | --- | --- | --- |
| A3-P0-01 | Current checkout lacks the v47 JSON and SQLite directly required by the v48 builders. | `scripts/build_prefreeze_candidate_v48_loc_geo_repair.py`; `scripts/build_prefreeze_candidate_v48_search_sqlite.py`; missing v47 paths | A clean clone can verify final bytes but cannot reproduce v48 from present inputs. | Recover both historical LFS objects into a quarantined read-only provenance bundle; verify their OIDs/bytes; document a no-network replay or formally declare frozen-output verification, not regeneration, as the preservation contract. |
| A3-P0-02 | TRACE generation reads SQLite and the legacy frontend payload for data/route decisions; the graph is not shown to regenerate from canonical JSON plus governed configuration. | TRACE generator, SQLite, adjunct JSON, frontend mock, TRACE assets | Reconciliation/derived data could silently become canonical research data. | Produce a relation/node/evidence delta ledger. Only reproducible authoritative facts may migrate; all others remain held. Acceptance requires zero unclassified graph fields. |
| A3-P0-03 | Frozen JSON top-level metadata says `traceMetadataSupportedCount=2970`, while row-level SQLite and TRACE atlas say 2,971; `sourceVerified=12952`, so the stale top-level pair sums to 15,922. | canonical JSON `meta`; SQLite rows; TRACE atlas | An importer that trusts summary metadata fails parity or drops/misclassifies one object. The frozen file cannot be edited in place. | Normatively declare row-level records authoritative for parity and top-level counters as historical annotations; migration verifier must report the known delta exactly and reject any new unexplained delta. |
| A3-P0-04 | 1,266 tracked raw files sit under 26 manifest-listed directories whose policy is `do_not_commit_without_redaction_review`; no comprehensive review receipt was found. | capture raw directories and capture manifest | Possible source-policy, confidential-field, or provenance breach; raw bytes cannot automatically enter `raw`. | Before raw-layer ingestion or public freeze, attach artifact-level source/terms/redaction/rights decisions or quarantine the files. A passing gate requires every raw artifact to have an explicit disposition. |
| A3-P0-05 | `remainingToMinimumTarget=4077` and the 20,000 aspiration remain embedded in frozen metadata/receipts and in at least one current migration specification section. | canonical `meta`; freeze receipts; `MIGRATION_V48_TO_V49.md` | Historical aspiration may be mistaken for migration or promotion parity. | Preserve the value only as historical metadata. Remove it from normative migration/promotion gates; canonical parity is 15,923, graph parity is unit-specific, and derived reconciliation is separate. |

### P1

| ID | Finding | Affected paths | Risk | Recommended action |
| --- | --- | --- | --- | --- |
| A3-P1-01 | Capture manifest says 29 raw directories are present; only 26 exist. | capture manifest, its report, three missing directories | Stale lineage inventory and false clean-input assumption. | Regenerate the manifest only in a separately authorized data-governance task, preserving the old manifest as historical evidence. |
| A3-P1-02 | Capture record files use three schemas; 9 runs are explicitly unclassified and two files are special-case transfer evidence outside the run manifest. | 46 record CSVs | A single bulk CSV importer would misparse fields or conflate stages. | Version schemas and import by declared contract; unknown/unclassified runs remain held. |
| A3-P1-03 | `archive_seed.sqlite` and 14 old SQL files have ambiguous names and remain executable-looking beside v49 docs. | `data/archive_seed.sqlite`; `db/*.sql`; `db/README.md` | Operators could run obsolete schema/seed logic or treat 1,542 legacy search docs as archive data. | Add an explicit legacy/non-v49 marker and execution deny gate; archive after the v49 DDL replaces it. |
| A3-P1-04 | v46 intermediate JSON/SQLite and exact duplicate 8,636-surface payloads occupy active storage. | v46 assets and three duplicate payload paths | Storage and accidental-authority risk. | Retain read-only until recovery and runtime-decoupling gates pass, then cold-archive one recovery copy and list the rest as deletion candidates. |
| A3-P1-05 | Transfer manifest uses short `sourceDataCommit` and omits the later TRACE product from its 65-file package. | transfer manifest and TRACE manifest | A consumer may assume one manifest seals the entire v48 product. | Use full commit IDs and explicitly model separate canonical-transfer and derived-product manifests under one release evidence index. Do not rewrite v48 receipts. |

### P2

| ID | Finding | Risk | Recommended action |
| --- | --- | --- | --- |
| A3-P2-01 | Non-authoritative small JSON/CSV products were classified by path family, not semantically re-derived one by one. | Hidden duplicates or undocumented one-off value transformations may remain. | Carry all files into the cleanup ledger; require owner and recovery reference before deletion. |
| A3-P2-02 | Provider-level source concentration, content licenses, and rights semantics were not adjudicated by A3. | Data may be technically reproducible but not publishable. | Use A5/A6/A10 results; no API availability may imply display permission. |
| A3-P2-03 | A3 did not fetch historical LFS bodies to prove remote recoverability. | Git pointer presence could be mistaken for available bytes. | Perform a separately authorized, read-only LFS recovery drill before archival cleanup. |

## 11. Gate assessment

| Gate | Result | Evidence |
| --- | --- | --- |
| Repository data-format inventory | PASS | counts and path groups measured across all tracked JSON/CSV/SQLite/SQL assets |
| Five-role artifact authority separation | PASS | canonical JSON, reconciliation SQLite, integrity manifests, Search projection, and TRACE products are distinct |
| Frozen byte/hash verification | DELEGATED | expected values fixed here; main auditor performs the single full-hash pass |
| SQLite immutable query discipline | PASS | every A3 connection used `mode=ro&immutable=1` |
| SQLite current-run integrity | DELEGATED | saved receipt inspected; main auditor performs the single current-run check |
| Search/canonical/TRACE population boundary | PASS | exact six set measurements reproduced |
| Count/unit separation | PASS | object, node, graph edge, membership, review, and auxiliary units explicit |
| ID/null/delimiter/orphan accounting | PASS | direct statistics plus frozen orphan gate receipts |
| Current-checkout v48 self-reproduction | FAIL | missing v47 JSON/SQLite parent assets |
| TRACE authoritative regeneration | FAIL | graph generator relies on reconciliation and legacy presentation inputs |
| Raw artifact disposition coverage | FAIL | 1,266 tracked raw files lack comprehensive review receipt |
| Data-quality metadata consistency | FAIL | frozen `2970` summary versus 2,971 row-level count |
| Search as projection, not second canonical DB | PASS | Search-only 6,051 explicitly excluded from migration |
| Data/database audit coverage | COMPLETE | no requested A3 partition lacks evidence commands or a result |

## 12. Recommended next actions

At most three independent implementation tasks follow from A3:

1. **Lineage recovery and replay contract.** Recover the two v47 LFS parent bodies read-only, pin full commit/OID/size/hash, and decide whether preservation promises exact regeneration or only frozen-output verification. Acceptance: a complete DAG has no missing input and no network-only step without saved bytes.
2. **Authoritative graph delta ledger.** Compare canonical JSON fields with every v48 node, edge, evidence tuple, review row, and adjunct input; label each `REGENERABLE`, `GOVERNED_EXTERNAL_EVIDENCE`, or `HOLD`. Acceptance: zero unclassified graph facts, and no SQLite/shard-only fact enters migration.
3. **Raw/capture governance closure.** Version the three CSV schemas, repair the stale run manifest, and assign artifact-level provider, terms/redaction, rights, lineage, and disposition records to all tracked raw files. Acceptance: every raw artifact has an owner, authority role, recovery reference, and allow/hold decision; no secret value is exposed in the ledger.

## 13. Final A3 status

- Audit package status: **PARTIAL**
- Audit coverage: **COMPLETE**
- Canonical parity known: **true**
- Graph parity units known: **true**
- Derived reconciliation separated: **true**
- Historical 20,000 aspiration separated: **partially; normative documents still require correction**
- v48 current-checkout self-reproduction: **false**
- Data lineage ready for unrestricted migration: **false**
- Frozen data mutated: **false**
- Database implemented: **false**
- Residual A3 execution sessions: **0**
- Global residual process scan: **main auditor pending**

The safe conclusion is not that v48 is corrupt. Its frozen bytes, receipts, reconciliation database, and derived TRACE product form a strong recoverable checkpoint. The blocking distinction is that frozen-output integrity is currently stronger than source-to-output reproducibility and raw-provider governance. PostgreSQL migration must preserve that distinction rather than laundering derived or unreviewed material into canonical authority.
