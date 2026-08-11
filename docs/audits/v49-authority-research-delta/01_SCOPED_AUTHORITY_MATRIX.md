# 01 — Scoped authority, lineage, and parent-asset boundary

- Audit package: Phase 1C A1
- Audit date: 2026-08-11 (Australia/Brisbane)
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Branch and audited HEAD: `refactor/v49-data-platform` at `6b111a78818a9e9ef37e4909c1f288d3b844b77e`
- Result: **PASS** for the scoped authority decision and dependency inventory
- Legacy v48 exact byte replay from current HEAD: **UNVERIFIED and explicitly outside the v49 migration contract**
- Frozen artifact mutation: **none**

## Scope

This package closes the authority question that was left open by Phase 1B: whether missing v47 intermediates are migration authority, whether a clean v49 migration may depend on them, and which graph/read-product facts remain legacy projections. It inventories the concrete parent chain, checks legacy builder inputs statically, and fixes the preservation contract.

It does not classify every graph row, decide research-corpus membership, adjudicate visual rights, implement a migration, or replay a legacy builder. Graph-row classification belongs to the Phase 1C graph reconciliation package; rights/provider/delivery decisions belong to Prompt B.

## Locked outcome

```text
PARENT_ASSET_AUTHORITY_BOUNDARY_LOCKED=true
V49_BASELINE_MIGRATION_REQUIRES_V47_PARENTS=false
V49_BASELINE_MIGRATION_INPUT=generated/public_surfaces_prefreeze_candidate_v48.json
LEGACY_V48_EXACT_BYTE_REPLAY_FROM_CURRENT_HEAD=UNVERIFIED
V49_MIGRATION_IMPLEMENTED=false
```

The two absent v47 artifacts are provenance and historical replay references, not migration inputs. Their absence prevents direct execution of several legacy v48 builders, but it does not authorize recovery, refetch, derived backfill, or a migration hold. v49.0 migrates the final frozen v48 candidate JSON as the sole canonical input and independently reconciles it against the immutable SQLite and integrity manifests. A future migration or verifier that requires either v47 path violates this boundary and must fail.

This adopts **frozen-output verification, not legacy source-to-output regeneration**, as the v49 preservation contract. It preserves the truth that exact v46→v47→v48 byte replay has not been demonstrated.

## Scoped authority matrix

| Artifact family | Measured observation | Authority in Phase 1C | Allowed use | Prohibited use | Disposition | Result |
|---|---|---|---|---|---|---|
| `generated/public_surfaces_prefreeze_candidate_v48.json` | 190,067,852 bytes; frozen expected SHA-256 `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48`; 15,923 is the Phase 1C verification target and was not independently recomputed by A1 | Sole canonical migration input; raw bytes are lexical authority | Deterministic one-surface-to-one-baseline-object import; raw-byte/hash and row-accounting verification | Editing, deduplication, silent delimiter splitting, or supplementing rows from any other product | `MIGRATE_READ_ONLY` | PASS for authority; primary verifier owns count proof |
| `data/prefreeze_candidate_v48.sqlite` | 421,801,984 bytes; expected SHA-256 `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` | Immutable reconciliation evidence only | `mode=ro&immutable=1` integrity, schema, counts, sets, and known-delta comparison | Canonical row/field backfill, migration input, writes, sidecars, or graph promotion | `ARCHIVE_READ_ONLY` | PASS |
| v48 transfer manifest JSON/CSV | 65 declared files and 613,077,245 bytes; one canonical candidate, one frozen query snapshot, 50 evidence/validation files, 13 contract files | Integrity and transfer evidence | Byte/path/hash inventory verification and historical recovery evidence | Treating manifest membership as canonical data authority or treating the manifests as the complete TRACE release | `ARCHIVE_READ_ONLY` | PASS |
| `frontend/public/data/trace-v48/manifest.json` | Declares 580 assets: four top-level products and 576 shards | Integrity evidence for the derived TRACE product only | Validate declared legacy product bytes/counts and behavior | Promote graph facts, claims, relations, or objects merely because they are manifested | `ARCHIVE_READ_ONLY` | PASS |
| TRACE atlas/catalog/review/auxiliary/neighborhood products | 580 derived assets; active 15,923, review 4,425, auxiliary 11 | Derived read products and legacy projection evidence | Reconciliation, QA, and row-by-row classification input | Canonical migration input, research-claim authority, semantic-relation authority, or missing-row supplier | `ARCHIVE_READ_ONLY` | PASS |
| `frontend/public/data/archive-search-v1.json` | 8,636 items; `generatedFrom=public_surface_mock_v0` | Derived Search projection | Reconcile v48 behavior and population boundary | Second canonical database; supply the 6,051 Search-only IDs to v49 | `ARCHIVE_READ_ONLY` | PASS |
| three 8,636-surface legacy payload copies | Phase 1B proved the same Git blob; one copy is the Search source and one controls TRACE internal routes | Legacy presentation inputs, never source authority | Behavioral recovery until repository cutover | Canonical ingestion, graph authority, or public-object identity creation | `ARCHIVE_READ_ONLY`, later cleanup candidate | PASS |
| `generated/public_surfaces_prefreeze_candidate_v47.json` | Absent from HEAD; historical 134-byte LFS pointer names object `bc9d83892c91beabc7a1ec593f4d4315d7f377f3d9d98df6e2f20b082142ff7f`, size 190,062,921 | Historical derived intermediate and recovery reference only | Document lineage; optionally recover only in a separately authorized archival replay task | Required v49 migration input, implicit network fetch, or substitute canonical input | `ARCHIVE_REFERENCE_HOLD` | PASS for boundary; replay unverified |
| `data/prefreeze_candidate_v47.sqlite` | Absent from HEAD; historical 134-byte LFS pointer names object `e3b597f365960007562aa8715fcbc713220239c6a011b3040fd926ae4e47cd7c`, size 421,670,912 | Historical reconciliation intermediate and recovery reference only | Document lineage; separately authorized archival replay only | v49 migration input, canonical backfill, or implicit LFS fetch | `ARCHIVE_REFERENCE_HOLD` | PASS for boundary; replay unverified |
| v46 JSON/SQLite | Both LFS-managed bodies are present; 190,039,480 and 419,688,448 bytes | Historical intermediates | Static dependency audit and historical replay planning | Substitute v48 authority or seed v49 | `ARCHIVE_READ_ONLY` | PASS |
| v47 AIC records/nodes/edges and adjunct JSON | Current tracked evidence is present; adjunct has 11 non-count-eligible items | Source/provenance candidates and legacy graph projections, depending on field | Retain; classify evidence under explicit governed ingest | Automatic active-object creation, automatic influence, or graph promotion | `ARCHIVE_READ_ONLY` | PASS |
| v48 LOC repair CSVs and 18 saved provider responses | Current tracked evidence is present and selected by transfer manifest | Source/provenance candidates; repair graph files remain legacy projections | Retain as evidence and map only through reviewed transformations | Refetch during migration, direct row creation, or SQLite/shard backfill | `ARCHIVE_READ_ONLY` | PASS |
| other raw/provider payloads and authored source records | Phase 1B inventory remains mixed and not globally dispositioned | Potential provenance evidence only after artifact-level review | Quarantine, hash, and explicit ingest decision | Assume Git tracking, API availability, or filename grants authority | `HOLD_UNKNOWN` | PARTIAL outside A1; raw-disposition package owns closure |
| v46/v47/v48 saved samples, gates, reports, and summaries | Historical QA/freeze evidence includes a known `2,970` versus `2,971` summary conflict | Integrity/reconciliation evidence | Verify documented historical behavior and explicit known exceptions | Override row-level values or silently resolve conflicts | `ARCHIVE_READ_ONLY` | PASS for authority boundary |
| `db/*.sql`, `data/archive_seed.sqlite`, legacy caches/experiments | Not compatible with the accepted v49 model | Historical/unknown, non-executable for v49 | Inventory and later archive/retirement | Run as v49 schema, seed canonical rows, or supply missing objects | `HOLD_UNKNOWN` | PASS for isolation |
| Future v49 PostgreSQL and sealed releases | No implementation exists in this checkpoint | Future canonical and immutable projection layers only after gates | Consume the one allowed v48 input; retain exact raw/provenance links; derive releases forward | Reverse-write from API/release/Search/TRACE or depend on v47 parents | `NOT_IMPLEMENTED` | Not claimed |

## Concrete lineage and the missing-parent distinction

The checked-in scripts declare this legacy chain:

```text
v46 candidate JSON
  + v47 AIC active-record and TRACE CSVs
  + v47 adjunct record/node/edge CSVs
  + legacy payload helper code
  -> v47 candidate JSON (absent direct parent)
  -> v48 candidate JSON via 18 LOC repair rows and two AIC route repairs

v46 SQLite
  + v47 candidate JSON
  + v47 TRACE node/edge CSVs
  + v47 adjunct JSON
  -> v47 SQLite (absent direct parent)
  -> v48 SQLite via v48 candidate JSON and LOC repair node/edge CSVs

v48 SQLite + v48 candidate JSON + v47 adjunct JSON + 8,636 legacy frontend payload
  -> derived TRACE atlas/catalog/review/auxiliary/shards/manifest

8,636 legacy frontend payload
  -> derived archive-search-v1.json
```

`HEAD` does not contain the two direct v47 parents. Commit `31f8481ba960087a3ba740d62a40639bbf48258a` and source-lineage commit `1d919fb0e6c5ed5bba9bf728cf7aa27fb7ce821b` retain identical LFS pointer blobs for them. Pointer presence proves recovery metadata, not local or remote body availability; no fetch was attempted.

All explicitly declared v46 bodies, v47 AIC CSV inputs, sample input, and helper modules inspected for the v46→v47 stage are present and tracked. Therefore the indirect chain is **statically dependency-complete at the enumerated path level**. It is not byte-replay proof: the builders were not run, output bytes were not compared with the historical LFS OIDs, interpreter/library environment was not reconstructed, and hidden semantic or runtime dependencies were not inferred. This corrects an overbroad reading of “missing direct parent” without claiming reproducibility that was not measured.

The full dependency ledger is `02_PARENT_ASSET_DEPENDENCY_LEDGER.tsv`.

## Legacy builder clean-checkpoint assessment

| Entrypoint | Declared inputs in current HEAD | Direct clean execution | Authority/use result | Reason |
|---|---|---|---|---|
| `scripts/build_prefreeze_candidate_v47_aic_balance.py` | All enumerated v46 JSON, record/node/edge/adjunct CSVs, sample, and helper modules are present | **STATICALLY CLOSED; NOT RUN** | Historical replay only | Writes v47 JSON, adjunct JSON, summary, and sample. Exact historical byte equality is unverified. |
| `scripts/build_prefreeze_candidate_v47_search_sqlite.py` | v46 SQLite and v47 graph inputs are present, but its required v47 JSON output is absent | **NO as invoked from HEAD** | Historical replay only | Requires running the preceding writer; it deletes/recreates v47 SQLite and writes gates/reports. |
| `scripts/repair_prefreeze_candidate_v48_loc_geography.py` | Direct v47 JSON is absent; script also calls live LOC endpoints | **NO** | Capture script, forbidden as migration dependency | Not offline/self-contained; saved responses and repair CSV already exist. |
| `scripts/build_prefreeze_candidate_v48_loc_geo_repair.py` | Repair CSVs and sample exist; direct v47 JSON is absent | **NO** | Legacy JSON writer only | Cannot start without the excluded parent and writes the frozen candidate plus CSVs. |
| `scripts/build_prefreeze_candidate_v48_search_sqlite.py` | v48 JSON and repair CSVs exist; direct v47 SQLite is absent | **NO** | Legacy reconciliation writer only | Deletes/recreates the v48 SQLite and writes gates/reports; prohibited. |
| `scripts/audit_prefreeze_candidate_v48_freeze.py` | Final v48 artifacts and saved evidence exist; direct v47 JSON is absent | **NO** | Saved 55 PASS/0 HOLD remains historical evidence | It is not a pure clean-room verifier and writes a frozen gate path. |
| `scripts/build_prefreeze_candidate_v48_transfer_manifest.py` | Its declared selected inputs are present according to the existing manifest and static path checks | **STATICALLY CLOSED; NOT RUN** | Integrity-evidence generator only | Writes both frozen manifests and embeds historical 20,000 metadata; not a v49 verifier. |
| `scripts/build_prefreeze_candidate_v48_trace_visualization.py` | v48 SQLite, v48 JSON, v47 adjunct, and legacy frontend payload are present | **STATICALLY CLOSED; NOT RUN** | Derived-product generator only | Deletes the output directory, hashes inputs, opens SQLite without `immutable=1`, and writes 581 files. It cannot establish graph authority. |
| `frontend/scripts/generate-archive-search-index.mjs` | Its 8,636-item legacy input is present | **STATICALLY CLOSED; NOT RUN** | Derived Search generator only | Produces a presentation projection, not source or canonical data. |
| Phase 1C read-only authority/research verifier | Final implementation owned by the primary task | **Must pass independently** | v49 checkpoint evidence | Its allowed input boundary excludes both v47 parents and forbids reverse authority. |

No builder was executed. “Statically closed” means only that every explicitly inspected path exists; it does not mean deterministic output equality or semantic validity.

## TRACE facts that remain legacy projections

The current TRACE builder reads graph structure from reconciliation SQLite, derives relation families in code, mixes a v47 adjunct product, and uses the 8,636-item frontend payload to choose internal versus source links. These products remain valuable v48 behavior evidence but cannot become canonical research truth by persistence alone.

| Fact/unit | Observed legacy scale | Authority boundary |
|---|---:|---|
| Active object ↔ TRACE root crosswalk | 15,923 | The candidate JSON may seed the legacy crosswalk field. Full node attributes still require classification; root identity is not a semantic relation. |
| TRACE nodes | 97,889 | Every node/attribute not deterministically supported by the candidate JSON plus governed configuration is `LEGACY_PROJECTION_ONLY` or held. SQLite and shards cannot fill the gap. |
| Directed TRACE edges | 255,695 | The legacy directed triple and `TRE-*` ID are reconciliation keys, not claim or semantic-relation identity. |
| Active object-relation memberships | 126,822 | Legacy projection memberships are not evidence, claims, or canonical relations. They migrate only through an approved classified transformation. |
| Tree/branch placement and visualization grouping | 30 active trees plus legacy branches | Release/corpus presentation only; it cannot create an accepted claim. |
| Relation family assignment | Legacy builder maps any non-provenance, non-time/place, non-influence label to `medium_context` | Fail-open classification is prohibited. Unknown labels must produce no semantic relation or TRACE projection. |
| Review layer | 4,425 | Workflow/reconciliation visibility only; never added to the 15,923 baseline or silently promoted. |
| Auxiliary layer | 11 | Count-ineligible legacy adjunct projection; no automatic object, claim, relation, or influence creation. |
| Internal `href` and `hrefKind` | Based on intersection with the 8,636 legacy frontend payload | Routing/presentation data only; never identity or research authority. |
| TRACE manifest and shard hashes | 580 assets, 576 shards | Integrity evidence proves bytes of the derived product, not epistemic validity. |

A1 intentionally does not assign final per-row research classes. Until the graph reconciliation classifies a fact into an approved closed class, the fail-closed authority is legacy projection/hold and its canonical migration eligibility is false.

## Why v49 can and must sever the v47 parents

1. The authoritative baseline is already a complete frozen final byte stream with a fixed hash; its 15,923 surfaces are the required source-accounting population.
2. v47 JSON and SQLite are explicitly excluded derived intermediates in the v48 transfer manifest.
3. SQLite, Search, TRACE products, and all historical intermediates have narrower reconciliation/integrity/behavior roles and therefore cannot improve canonical completeness by backfill.
4. v49 identity seeding is one deterministic archive object per final JSON surface, without deduplication or merge. It does not need the edit history that produced the row.
5. Historical lineage is retained as artifact metadata and recovery references. Provenance loss is not concealed; it is separated from migration authority.
6. The migration/verifier acceptance test is negative as well as positive: the declared input graph must contain the final candidate JSON and may contain reconciliation/evidence readers, but must contain no read of either v47 parent and no derived-to-canonical path.

Therefore missing v47 parents no longer block the v49 baseline migration design. They remain a P1 archival-replay question. An actual migration is still unimplemented and cannot be claimed by this document.

## Evidence commands

Representative read-only commands used by A1:

```text
git status --short --branch
git cat-file -e HEAD:<v47-parent-path>
git cat-file -p <historical-commit>:<v47-parent-path>
git ls-tree -l <historical-commit> <v47-parent-paths>
git log --all --format=... -- <v47-parent-paths>
git check-attr filter diff merge text -- <v46-v48 large assets>
git ls-files <enumerated legacy dependencies>
stat -f '%N\t%z' <enumerated legacy dependencies>
rg -n <input/write/network patterns> <legacy builder entrypoints>
jq <bounded metadata and role projections> <transfer manifest, TRACE manifest, Search index>
git ls-files 'frontend/public/data/trace-v48/*.json' 'frontend/public/data/trace-v48/neighborhoods/*.json'
```

The Phase 1B checksum receipt was read, but A1 did not repeat the five-asset full hash pass or SQLite integrity check. No command printed secret values.

## Findings and priorities

### P0 closed in this scope

| ID | Finding | Resolution | Acceptance boundary |
|---|---|---|---|
| A1-P0-01 | Two direct v47 parents are absent, and several legacy v48 entrypoints cannot run directly from HEAD. | Lock them as historical replay references only. v49 consumes the final v48 candidate JSON and verifies frozen outputs rather than rebuilding v48. | `PARENT_ASSET_AUTHORITY_BOUNDARY_LOCKED=true`; future verifier/migration has zero v47-parent reads. |
| A1-P0-02 | SQLite/TRACE/Search and adjunct products contain facts not proven by the canonical input. | Classify all such facts as legacy projection/hold by default; allow promotion only through the closed graph classification with explicit authoritative evidence. | Zero derived-to-canonical paths and zero unclassified graph facts in the combined Phase 1C gate. |

### P1 retained

| ID | Finding | Risk | Required next action |
|---|---|---|---|
| A1-P1-01 | The v46→v47→v48 chain is statically path-complete at the enumerated level but exact byte replay was not run. | A historical preservation claim could overstate reproducibility. | If archival replay is later authorized, run in a quarantined read-only-input workspace, pin runtime, compare outputs to historical LFS OIDs, and preserve a receipt. This is not a v49 migration gate. |
| A1-P1-02 | Legacy builders write or delete frozen/product paths; the LOC repair collector also uses live network access. | Accidental mutation or non-deterministic refetch. | Keep these entrypoints outside Phase 1C and future migration execution allowlists. |

### P2 retained

| ID | Finding | Risk | Recommended action |
|---|---|---|---|
| A1-P2-01 | Historical LFS pointer bodies were not fetched or checked for remote availability. | Recovery metadata could be mistaken for a present retrievable body. | Perform a separately authorized LFS recovery drill only if archival replay becomes a requirement. |

## Unresolved items

- Per-row graph classification and the exact authority/research reconciliation totals are owned by the graph package and independent verifier.
- Raw/provenance disposition outside the named v47/v48 repair inputs is owned by the raw-evidence package.
- Visual rights, provider policy, delivery mode, and machine pixel exposure are explicitly excluded for Prompt B.
- The database, migration, release, and promotion remain unimplemented; this report only locks their input boundary.

## Actions explicitly not performed

- no v47 asset was fetched, copied, restored, generated, or materialized;
- no legacy builder, data exporter, migration, or database writer ran;
- no PostgreSQL, Docker, npm, Next.js, TypeScript, browser, screenshot, image download, or HTTP probe ran;
- no SQLite connection or integrity scan was opened by A1;
- no frozen JSON, SQLite, manifest, TRACE asset, Search asset, frontend file, QA file, or protected-main path was modified;
- no commit, push, PR, merge, deploy, force operation, cleanup, stash, or reset was performed.

## Final scoped status

```text
A1_STATUS=PASS
A1_COVERAGE=COMPLETE
PARENT_ASSET_AUTHORITY_BOUNDARY_LOCKED=true
LEGACY_DIRECT_V48_BUILDERS_SELF_CONTAINED=false
LEGACY_INDIRECT_REPLAY_STATIC_PATH_CLOSURE=true
LEGACY_INDIRECT_REPLAY_BYTE_EQUALITY_PROVEN=false
V49_BASELINE_MIGRATION_REQUIRES_V47_PARENTS=false
DERIVED_PRODUCT_CAN_CREATE_CANONICAL_ROWS=false
FROZEN_DATA_MUTATED=false
RESIDUAL_A1_EXECUTION_SESSION=0
GLOBAL_RESIDUAL_PROCESS_SCAN=PRIMARY_TASK_OWNED
```
