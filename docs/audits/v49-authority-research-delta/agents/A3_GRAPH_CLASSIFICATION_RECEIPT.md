# A3 — Research semantics and graph classification receipt

- Package: v49 Phase 1C A3
- Date: 2026-08-11 (Australia/Brisbane)
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Branch: `refactor/v49-data-platform`
- Result: **PASS — classification closed with explicit holds; canonical graph promotion remains blocked**
- Files owned by A3: `03_GRAPH_FACT_CLASSIFICATION_RULES.json`, `04_GRAPH_FACT_RECONCILIATION.json`, and this receipt

`PASS` means every measured A3 graph-fact unit has one of the five approved dispositions and the three required negative gates pass. It does not mean that a v49 semantic relation, accepted claim, TRACE projection, research corpus, database, or release is ready. The candidate input cannot authoritatively reconstruct the directed graph.

## 1. Scope and boundary

A3 classified and reconciled:

- candidate-JSON TRACE tree, branch, object-node, edge-ID, label, state, review, influence, tier, and declared-count occurrences;
- immutable SQLite nodes, directed edge rows, edge evidence observations, object-edge memberships, tree/branch placements, review rows, states, and count units;
- the 20-label active membership vocabulary versus the 39 labels in the full SQLite graph;
- the v47 auxiliary input and its derived v48 auxiliary read product;
- the frozen TRACE manifest's 580 listed assets and 576 neighborhood shards;
- legacy relation-family, taxonomy, and tier-normalization code paths that fail open or create derived state.

The authority boundary was fixed throughout:

```text
candidate JSON = sole canonical migration input
SQLite = immutable reconciliation evidence only
TRACE manifest = integrity evidence
atlas/catalog/shards/auxiliary JSON = derived products
```

Candidate occurrences classified `CANONICAL_ASSERTION_CANDIDATE` are only proposed source-bound literals or legacy crosswalks. They do not constitute accepted claims or semantic relations and do not make any object TRACE-eligible.

## 2. Assets read

| Path | Authority used by A3 | Read mode / note |
|---|---|---|
| `generated/public_surfaces_prefreeze_candidate_v48.json` | sole canonical migration input | Parsed exactly once by A2; A3 consumed the shared ledger and summary, not the 190 MB asset again |
| `/private/tmp/v49_phase1c_candidate_rows.tsv` | cross-agent measurement evidence | 15,923 rows plus header; 2,238,838 bytes; SHA-256 `4d5f15cda8e1267426fd91ea76da92573ab2851ee033468ebb0ef206ff0c4c46` |
| `/private/tmp/v49_phase1c_a2_summary.json` | cross-agent measurement evidence | A2 single-parse aggregate |
| `/private/tmp/v49_phase1c_a2_post.json` | cross-agent measurement evidence | candidate/SQLite tier delta and JSONL hashes |
| `data/prefreeze_candidate_v48.sqlite` | immutable reconciliation only | URI `file:data/prefreeze_candidate_v48.sqlite?mode=ro&immutable=1`; no integrity check |
| `generated/prefreeze_candidate_v47_aic_trace_adjuncts.json` | unsupported v47 parent/auxiliary input | read-only; never promoted |
| `frontend/public/data/trace-v48/atlas.json` | derived reconciliation product | read-only |
| `frontend/public/data/trace-v48/manifest.json` | TRACE integrity evidence | read-only; full frozen hash was not repeated by A3 |
| `frontend/public/data/trace-v48/auxiliary.json` | derived reconciliation product | read-only |
| `scripts/build_prefreeze_candidate_v48_trace_visualization.py` | legacy generator code | read-only |
| `scripts/build_prefreeze_candidate_v9_search_sqlite.py` | legacy SQLite builder code | read-only |
| `frontend/src/components/archive/trace/trace-taxonomy.ts` | legacy display registry code | read-only |

## 3. Evidence commands

Representative exact commands were:

```sh
sqlite3 'file:data/prefreeze_candidate_v48.sqlite?mode=ro&immutable=1' '.schema trace_nodes'
sqlite3 'file:data/prefreeze_candidate_v48.sqlite?mode=ro&immutable=1' '.schema trace_edges'
sqlite3 'file:data/prefreeze_candidate_v48.sqlite?mode=ro&immutable=1' '.schema object_trace_edges'

# One completed A3 aggregation pass ordered node rows by node_id, edge rows by
# edge_id, memberships by (surface_id,edge_id), active object refs by surface_id,
# and review rows by review_id. Each hash row is a compact UTF-8 JSON array + LF.
python3 - <<'PY'
# stdlib sqlite3 opened mode=ro&immutable=1; counters and SHA-256 only
PY

sqlite3 -noheader 'file:data/prefreeze_candidate_v48.sqlite?mode=ro&immutable=1' \
  'select distinct edge_id from object_trace_edges order by edge_id;' | shasum -a 256
sqlite3 -noheader 'file:data/prefreeze_candidate_v48.sqlite?mode=ro&immutable=1' \
  'select distinct trace_object_node_id from objects where count_eligible=1 order by trace_object_node_id;' | shasum -a 256
sqlite3 -noheader 'file:data/prefreeze_candidate_v48.sqlite?mode=ro&immutable=1' \
  'select distinct e.edge_label from object_trace_edges x join trace_edges e on e.edge_id=x.edge_id order by e.edge_label;' | shasum -a 256

nl -ba scripts/build_prefreeze_candidate_v48_trace_visualization.py | sed -n '20,115p'
nl -ba frontend/src/components/archive/trace/trace-taxonomy.ts | sed -n '185,230p'
nl -ba scripts/build_prefreeze_candidate_v9_search_sqlite.py | sed -n '270,340p'

python3 -m json.tool docs/audits/v49-authority-research-delta/03_GRAPH_FACT_CLASSIFICATION_RULES.json
python3 -m json.tool docs/audits/v49-authority-research-delta/04_GRAPH_FACT_RECONCILIATION.json
```

The stable full-package reproduction command is:

```sh
python3 scripts/verify_v49_authority_research_delta.py --json
```

Final acceptance must not use `--skip-large-assets`.

## 4. Measured results

### 4.1 Exact graph units

| Unit | Count | Evidence boundary |
|---|---:|---|
| TRACE nodes | 97,889 | 97,889 unique node IDs; row SHA-256 `2e43e7382bdaed6a37c6c5c3c994ea8606b3424c51655c1ec649a881adb52824` |
| Full directed graph edges | 255,695 | 255,695 unique IDs and directed triples; row SHA-256 `85c9ec63e42bd510cb6bc02ae5a3d81c5a7adff9db3dd655deccc61746ae9c62` |
| Object-edge memberships | 126,822 | 126,822 unique pairs, surfaces 15,923, edges 126,822, shared edges 0; row SHA-256 `a5b94fce847e2f7bc9473045033704cba504c2d455b0d5e785fcf321679a5018` |
| Edge evidence observations | 255,695 | 255,247 distinct `(url,text,field)` composites; 389 reused groups across 837 occurrences; blank text 3 |
| Full graph trees | 37 | Projection-wide unit; seven are outside the active 30-tree cohort |
| Active research trees | 30 | Candidate and SQLite active tree sets agree |
| Full graph branch IDs | 106 | Projection-wide unit |
| Candidate branch IDs | 85 | 80,093 occurrences; SQLite active membership edges use 77 |
| Active relation labels | 20 | Membership-family counts sum exactly to 126,822 |
| Full graph relation labels | 39 | 19 labels never enter active memberships |
| Review rows | 4,425 | All unlinked; row SHA-256 `a2b8e739edcf4a0007e9b85c4777144022702415c9440db357e8a34f83f661c2` |
| v47 auxiliary input | 11 items / 36 nodes / 33 edges | Held; not canonical input |
| v48 derived auxiliary product | 11 items / 44 nodes / 33 edges | Legacy projection only |
| TRACE assets / shards | 580 / 576 | Manifest-listed assets exclude the manifest itself |
| Historical influence edges | 0 | Both main graph and auxiliary evidence measure zero |

Active membership families remain separate units:

```text
medium_context      79,206
source_provenance   31,288
time_place          16,328
historical_influence     0
total              126,822
```

### 4.2 Candidate authority versus graph projection

Candidate JSON proves these crosswalk/set facts:

- 15,923 unique object-node references; the raw-line set hash exactly equals SQLite active objects: `7ab83cfcbc11ebc5a5902609f6e6b35f2831ceff9c41fcf33047434d51f98c4d`.
- 126,822 unique edge-ID references with no shared ID; the raw-line set hash exactly equals SQLite active membership edges: `7b4be2de0dd739d648037b51d77128128cecaaf413385f0a918ae5cf8f4045ba`.
- The 20-label candidate vocabulary exactly equals the active membership vocabulary: `6d741cb7822268659dec27b58a77b942157ea05f3afd5530614c2e7dafb3e9f4`.
- Candidate branch references contain eight IDs not used by SQLite active membership edges: `TRB100`, `TRB114`, `TRB115`, `TRB116`, `TRB120`, `TRB121`, `TRB122`, and `TRB123`.

Candidate JSON does **not** prove an edge-to-label mapping:

```text
edgeId occurrences       126,822
edgeLabel occurrences     79,683
surfaces with unequal arrays 9,393
authorized positional mappings 0
```

The label occurrences are therefore independent source-row assertions: 73,843 non-analytical occurrences are `CANONICAL_ASSERTION_CANDIDATE`; 5,840 cluster/theme occurrences are `COMPUTED_ASSOCIATION` and remain held without an analysis run. The 126,822 edge IDs are opaque legacy crosswalks. No endpoint, predicate assignment, evidence bridge, claim, or semantic relation can be reconstructed by zipping arrays or consulting SQLite.

### 4.3 Tier normalization delta

The candidate row-level tier distribution is:

```text
blank                 4,957
source_verified       7,995
metadata_supported    2,971
total                15,923
```

SQLite reports `source_verified=12,952` and `metadata_supported=2,971`. All 4,957 differences are candidate blank → SQLite `source_verified`; no other tier delta exists. The exact blank-ID set hash is `fbabc473e5ca7c7435a13d3c6c28a05198a97d15331f1f0b0b01b7464d81cceb`.

The cause is measured at `scripts/build_prefreeze_candidate_v9_search_sqlite.py:299`: a blank `trace.tier` becomes `source_verified` when the legacy builder's accepted predicate passes. This is `LEGACY_PROJECTION_ONLY` normalization. SQLite must not backfill the candidate literal, and the derived tier grants no research-corpus or TRACE eligibility.

## 5. Closed classification

The complete machine counts are in `04_GRAPH_FACT_RECONCILIATION.json`. Principal dispositions are:

| Unit | CANONICAL ASSERTION CANDIDATE | LEGACY PROJECTION ONLY | COMPUTED ASSOCIATION | HELD UNSUPPORTED | REJECTED | Unclassified |
|---|---:|---:|---:|---:|---:|---:|
| Candidate edge-ID references | 126,822 | 0 | 0 | 0 | 0 | 0 |
| Candidate label occurrences | 73,843 | 0 | 5,840 | 0 | 0 | 0 |
| Candidate tier literals | 10,966 | 0 | 0 | 4,957 | 0 | 0 |
| SQLite node rows | 0 | 97,889 | 0 | 0 | 0 | 0 |
| SQLite full edge rows | 0 | 217,554 | 6,004 | 32,137 | 0 | 0 |
| SQLite edge evidence | 0 | 255,692 | 0 | 3 | 0 | 0 |
| SQLite object-edge memberships | 0 | 120,982 | 5,840 | 0 | 0 | 0 |
| SQLite review rows | 0 | 0 | 0 | 4,425 | 0 | 0 |
| v47 auxiliary input items/nodes/edges | 0 | 0 | 0 | 80 | 0 | 0 |
| v48 derived auxiliary items/nodes/edges | 0 | 88 | 0 | 0 | 0 | 0 |

The 32,137 held full-graph edges use 19 labels absent from the active 20-label registry. They are explicitly held rather than silently receiving `medium_context/documented`. The remaining 217,554 full edge rows are still only legacy projection evidence; the 6,004 analytical rows retain a computed-association disposition but cannot be promoted without analysis-run provenance.

Required A3 gates:

```text
UNCLASSIFIED_GRAPH_FACT=0
SILENT_UNKNOWN_RELATION_FALLBACK=0
AUTOMATIC_INFLUENCE_INFERENCE=0
CANONICAL_GRAPH_PROMOTION_ALLOWED=false
```

Legacy source still contains two fail-open relation code paths:

1. `relation_family()` at `scripts/build_prefreeze_candidate_v48_trace_visualization.py:100-107` defaults every unmatched label to `medium_context`.
2. `traceTypeFor()` at `frontend/src/components/archive/trace/trace-taxonomy.ts:203-215` creates `MC-OTHER`, family `medium_context`, status `documented` for an unknown label.

Both are forbidden for v49 migration and release generation. The A3 `SILENT_UNKNOWN_RELATION_FALLBACK=0` result means the new classification ledger holds every unknown occurrence; it does not claim that the legacy functions are safe.

## 6. Findings, risk, and action

### P0

| ID | Finding | Risk | Required action / acceptance |
|---|---|---|---|
| A3-P0-01 | 9,393 surfaces prove `edgeIds` and `edgeLabels` are not parallel arrays | Zipping manufactures predicate assignments and canonical relations | Preserve IDs and labels as separate candidate literals; typed relation migration remains blocked unless authoritative endpoint/predicate/evidence records are supplied independently |
| A3-P0-02 | 32,137 full-graph edges use 19 labels outside the active registry | Legacy fallback can publish unknowns as documented medium/context | Keep all 32,137 held; v49 verifier must reject any default family/epistemic class and emit zero projections/metrics |
| A3-P0-03 | 6,004 analytical full edges, including 5,840 active membership occurrences, have no governed analysis run | Cluster/theme display data can be laundered into research claims | Retain as computed associations with promotion held until method/parameters/input/output hashes and score semantics exist |
| A3-P0-04 | 4,957 blank candidate tiers were automatically upgraded to SQLite `source_verified` | Derived state can falsely grant eligibility or overwrite lexical authority | Preserve blank canonical literals and version the missingness; forbid SQLite backfill and builder auto-promotion |
| A3-P0-05 | The full graph's endpoints, evidence and placements are absent from the sole input and seven graph trees lie outside the active cohort | Graph parity can be mistaken for canonical research authority | Keep complete SQLite graph as legacy projection only; canonical semantic relation and TRACE projection counts remain zero |
| A3-P0-06 | Eleven auxiliary objects depend on a v47 adjunct parent | Context rows can bypass the canonical-input boundary | Hold parent facts; preserve the derived auxiliary product only as v48 projection evidence |

### P1

| ID | Finding | Risk | Required action / acceptance |
|---|---|---|---|
| A3-P1-01 | Three graph-only edges have blank evidence text and no registered locator-only evidence kind | Incomplete evidence and valid locator-only evidence are indistinguishable | Keep the three held until evidence-kind requirements explicitly authorize their URL+field form |
| A3-P1-02 | Candidate branch set has eight IDs absent from active membership edge placements | Tree/branch UI organization can be confused with edge identity | Preserve as candidate crosswalk assertions only; do not infer placement or relation semantics |
| A3-P1-03 | Evidence composites are reused (389 groups / 837 occurrences) | Evidence equality can alter edge/claim counts | Deduplicate only by the v49 source-bound evidence natural key; never by text/URL alone |

### P2

No A3 P2 is required before the independent verifier. Display consolidation remains a frontend/research-view concern outside this package.

## 7. Unresolved items and readiness impact

All unresolved material has a closed hold disposition; nothing remains unclassified. Remaining blockers are authority/provenance blockers, not missing ledger rows:

- no authoritative candidate mapping from edge ID to predicate, endpoints, evidence, tree placement, or claim;
- no analysis-run provenance for cluster/theme associations;
- no approved v49 mapping for 19 full-graph-only labels;
- no candidate tier for 4,957 surfaces;
- no approved parent/evidence ingest decision for 11 adjunct objects;
- no locator-only evidence kind for three blank-text graph-only observations.

Consequently:

```text
TRACE_ELIGIBLE_OBJECTS=0
CANONICAL_SEMANTIC_RELATIONS_FROM_V48_GRAPH=0
CANONICAL_RESEARCH_CLAIMS_FROM_V48_GRAPH=0
PRE_DDL_READY=false
```

The first three values are authority conclusions for this Phase 1C baseline; they do not delete v48 TRACE or deny its value as a frozen research visualization and reconciliation product.

## 8. Process and command receipt

One initial read-only Python aggregation was started, but the tool returned an empty output handle while the process continued. Before the missing handle was diagnosed, a second aggregation began. A read-only process inspection found:

- first duplicate: PID `96493`, running, A3-owned;
- retained scan: shell PID `96856`, Python PID `96863`, active and producing the recoverable `/tmp` result.

A3 terminated PID `96493` with `kill 96493`, retained only one scan, waited for it to complete, and verified all three PIDs were absent afterward. The completed temporary aggregate was 6,731 bytes with SHA-256 `52d380b7c6f41a513ade43ec10ec189307393f329c0050dddedffd32682d4088`. It contains counts/hashes only and no frozen bytes.

A3-owned residual processes: **0**.

## 9. Modifications

A3 modified only:

- `docs/audits/v49-authority-research-delta/03_GRAPH_FACT_CLASSIFICATION_RULES.json`;
- `docs/audits/v49-authority-research-delta/04_GRAPH_FACT_RECONCILIATION.json`;
- `docs/audits/v49-authority-research-delta/agents/A3_GRAPH_CLASSIFICATION_RECEIPT.md`.

No data, SQLite, manifest, TRACE asset, script, architecture document, frontend, package, CI, deployment file, QA screenshot, or protected-main file was modified.

## 10. Actions explicitly not performed

- No candidate JSON reparse was performed by A3 after A2 supplied its single-pass evidence.
- No frozen full-file hash or SQLite integrity check was repeated.
- No SQLite write, transaction, migration, sidecar, `VACUUM`, export, or regenerated asset was created.
- No automatic deduplication, merge, delimiter split, tier repair, predicate mapping, or edge-label zip was performed.
- No graph fact was promoted to an accepted claim, semantic relation, TRACE projection, publication layer, or metric row.
- No PostgreSQL, Docker, npm, Next.js, TypeScript, browser, frontend screenshot, HTTP probe, image download, server, build, PR, merge, deploy, or protected-main cleanup was run.
- No commit or push was performed by A3.

## 11. Exit

```text
A3_SCOPE=PASS
UNCLASSIFIED_GRAPH_FACT=0
SILENT_UNKNOWN_RELATION_FALLBACK=0
AUTOMATIC_INFLUENCE_INFERENCE=0
CANONICAL_GRAPH_PROMOTION_ALLOWED=false
A3_RESIDUAL_PROCESSES=0
```

The independent verifier must reproduce these exact unit counts and hashes. Any attempt to use SQLite, atlas, catalog, shards, review rows, auxiliary product, or legacy fallback code to create canonical graph facts is a gate failure.
