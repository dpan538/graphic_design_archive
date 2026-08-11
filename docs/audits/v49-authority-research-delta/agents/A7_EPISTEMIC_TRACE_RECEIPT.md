# A7 — Epistemic Relation Registry and TRACE Projection Receipt

- Task: v49 Phase 1C A7
- Date: 2026-08-11 (Australia/Brisbane)
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Branch: `refactor/v49-data-platform`
- Baseline commit: `6b111a78818a9e9ef37e4909c1f288d3b844b77e`
- Result: **PASS_WITH_EXPLICIT_HOLDS**
- Exit status: **PASS**

`PASS` means the assigned epistemic registry and TRACE-delta scope is complete and internally reconciles to A2/A3 evidence. It does not authorize canonical graph migration: accepted claims, semantic relations, TRACE-eligible objects and v49 TRACE projection edges remain zero.

## 1. Independent task boundary

A7 was responsible only for:

- defining the four closed epistemic classes and their evidence profiles;
- mapping every relation label observed in the 255,695-edge frozen graph to an explicit authority, epistemic route, evidence requirement, promotion decision and TRACE-projectability decision;
- adding the reserved zero-count `influenced_by` policy;
- documenting the delta from frozen v48 graph/display facts to the v49 evidence → claim → semantic relation → projection model.

A7 wrote only:

- [08_EPISTEMIC_RELATION_REGISTRY.json](../08_EPISTEMIC_RELATION_REGISTRY.json);
- [12_TRACE_PROJECTION_DELTA.md](../12_TRACE_PROJECTION_DELTA.md);
- this receipt.

Visual rights, provider policy, delivery mode, endpoint health, raw-source disposition, corpus membership, database DDL, migration and frontend implementation were outside A7 scope.

## 2. Assets read

| Path | Use |
|---|---|
| `docs/audits/v49-authority-research-delta/03_GRAPH_FACT_CLASSIFICATION_RULES.json` | A3 closed classification and fail-closed contract |
| `docs/audits/v49-authority-research-delta/04_GRAPH_FACT_RECONCILIATION.json` | Exact per-label and graph-unit counts |
| `docs/audits/v49-authority-research-delta/05_METADATA_SUPPORTED_RECONCILIATION.md` | A2 authority/tier boundary |
| `docs/audits/v49-authority-research-delta/09_RESEARCH_CORPUS_POLICY.md` | TRACE eligibility and corpus boundary |
| `docs/audits/v49-authority-research-delta/agents/A2_COUNT_PARSER_RECEIPT.md` | Candidate arrays, 79,683/126,822/9,393 evidence |
| `docs/audits/v49-authority-research-delta/agents/A3_GRAPH_CLASSIFICATION_RECEIPT.md` | Full graph classification, evidence and residual receipt |
| `docs/adr/0004-research-claims-corpora-and-visual-registry.md` | Normative evidence/claim/relation/projection and epistemic model |
| `DATA_MODEL_V49.md` | Current research tables, fail-closed constraints and orthogonal states |
| `docs/architecture/DDL_DECISION_PACK_V49.md` | Relation/membership identities, projection count semantics and state vocabulary |
| `docs/audits/v49-pre-migration/05_TRACE_RESEARCH_SEMANTICS.md` | Prior measured research-semantic risks and required boundaries |
| `frontend/src/components/archive/trace/trace-taxonomy.ts` | Read-only legacy 20-label display registry and fail-open fallback evidence |
| `scripts/verify_v49_authority_research_delta.py` | Read-only inspection of the final verifier's registry contract |

A7 did not read the 190 MB candidate JSON or query SQLite. It reused the coordinated A2/A3 evidence and did not repeat the disk-intensive scans.

## 3. Commands executed

The read-only inspection and validation commands were:

```sh
git status --short
rg --files docs/audits/v49-authority-research-delta docs | rg '(A2_|A3_|03_GRAPH|04_GRAPH|05_METADATA|TRACE|RESEARCH|DDL_DECISION|DATA_MODEL|ARCHITECTURE|0004)' | sort
wc -l <selected A2/A3/normative evidence files>
cat docs/audits/v49-authority-research-delta/03_GRAPH_FACT_CLASSIFICATION_RULES.json
cat docs/audits/v49-authority-research-delta/agents/A3_GRAPH_CLASSIFICATION_RECEIPT.md
jq 'keys' docs/audits/v49-authority-research-delta/04_GRAPH_FACT_RECONCILIATION.json
jq '<graph units, candidate authority, SQLite reconciliation, label rows, gates and holds>' docs/audits/v49-authority-research-delta/04_GRAPH_FACT_RECONCILIATION.json
cat docs/adr/0004-research-claims-corpora-and-visual-registry.md
cat docs/audits/v49-authority-research-delta/09_RESEARCH_CORPUS_POLICY.md
cat docs/audits/v49-authority-research-delta/05_METADATA_SUPPORTED_RECONCILIATION.md
rg -n -C 8 'epistemic|claim|semantic relation|TRACE projection|influence|predicate registry|computed association|causal' <normative evidence files>
sed -n '250,360p' docs/audits/v49-pre-migration/05_TRACE_RESEARCH_SEMANTICS.md
sed -n '129,170p' DATA_MODEL_V49.md
sed -n '245,330p' docs/architecture/DDL_DECISION_PACK_V49.md
sed -n '1,245p' frontend/src/components/archive/trace/trace-taxonomy.ts
jq -r '.relationLabelReconciliation[].label' docs/audits/v49-authority-research-delta/04_GRAPH_FACT_RECONCILIATION.json | LC_ALL=C sort | shasum -a 256
jq '<candidate, membership and full-edge sums>' docs/audits/v49-authority-research-delta/04_GRAPH_FACT_RECONCILIATION.json
test -f scripts/verify_v49_authority_research_delta.py
rg -n -C 3 '08_EPISTEMIC|epistemic|relations|TRACE_ELIGIBLE|UNCLASSIFIED_GRAPH|projectable' scripts/verify_v49_authority_research_delta.py
sed -n '570,690p' scripts/verify_v49_authority_research_delta.py
python3 -m json.tool docs/audits/v49-authority-research-delta/08_EPISTEMIC_RELATION_REGISTRY.json
jq '<registry relation/scope/route/count/projectability checks>' docs/audits/v49-authority-research-delta/08_EPISTEMIC_RELATION_REGISTRY.json
comm -3 <(jq -r '<A3 labels>' ...) <(jq -r '<registry observed labels>' ...)
python3 - <<'PY'
# bounded read-only cross-check of every registry label/count/state against A3;
# also verifies totals, fail-closed fields and Markdown link targets
PY
git diff --check -- docs/audits/v49-authority-research-delta/08_EPISTEMIC_RELATION_REGISTRY.json docs/audits/v49-authority-research-delta/12_TRACE_PROJECTION_DELTA.md
shasum -a 256 docs/audits/v49-authority-research-delta/08_EPISTEMIC_RELATION_REGISTRY.json docs/audits/v49-authority-research-delta/12_TRACE_PROJECTION_DELTA.md
ps -axo pid=,ppid=,state=,etime=,command= | awk '<target-worktree path filter>'
```

Three repository writes used `apply_patch`: registry creation, verifier-compatible `failClosedPolicy` addition, and TRACE-delta creation. This receipt was also created with `apply_patch`.

One bounded `jq` sum expression had incorrect pipeline precedence and exited with `Cannot iterate over number (255695)`. The corrected object-form expression immediately returned exact sums. The failed expression was read-only and changed nothing.

The first sandboxed `ps` attempt was denied by the environment (`operation not permitted`). It was rerun once with read-only process-list approval and returned no target-worktree process. No process was killed.

The formal package verifier is:

```sh
python3 scripts/verify_v49_authority_research_delta.py --json
```

A7 did not run it because the cross-package manifest, checksums and independent-verifier phase were not yet final. Root/A5 owns that final whole-package execution.

## 4. Measured evidence

| Evidence | Result |
|---|---:|
| Registry entries | 40 (39 observed + 1 reserved) |
| Full-graph observed labels matched exactly | 39 / 39 |
| Active labels | 20 |
| Full-graph-only unregistered labels | 19 |
| Documented-source route labels | 18 |
| Computed-association route labels | 2 |
| Reserved causal route labels | 1 (`influenced_by`) |
| Candidate label occurrences | 79,683 |
| Candidate opaque edge IDs | 126,822 |
| Surfaces where edge IDs/labels cannot be zipped | 9,393 |
| Active memberships | 126,822 |
| Full graph edges | 255,695 |
| Known non-analytical legacy full edges | 217,554 |
| Computed full edges without governed run | 6,004 |
| Unknown full edges held | 32,137 |
| Influence edges | 0 |
| Current projectable relation entries | 0 |
| TRACE-eligible objects | 0 |
| Unclassified graph facts | 0 |

The sorted 39-label set hash is `ef9a5814d002d3d590ff20d7db94d669cc76cc79e5df9801ce92f566e2431961` using exact UTF-8 labels in `LC_ALL=C` order with one LF each.

Pre-receipt file hashes were:

```text
d53618df6f3aad291a2a2308c97e71b23e4b8d014ae361fb5a50f7313c5bb7cf  08_EPISTEMIC_RELATION_REGISTRY.json
8da8e8d7c1a1707c638bc626f59cd04cb140a490df11df72a00f57fe289ae30d  12_TRACE_PROJECTION_DELTA.md
```

Final package `CHECKSUMS.sha256` supersedes these working hashes after all audit files are assembled.

## 5. Findings and status

### P0 — closed for classification/policy

| ID | Finding | Resolution |
|---|---|---|
| A7-P0-01 | Candidate edge IDs and labels cannot be positionally paired | All 126,822 edge IDs are opaque crosswalks; authorized mappings 0 |
| A7-P0-02 | Nineteen full-only labels can trigger fail-open family/epistemic defaults | All 32,137 occurrences are `HELD_UNSUPPORTED`, family null, epistemic class null, proposed/held/review |
| A7-P0-03 | Display status can conflate source statements, scholarship, computations and causation | Four closed epistemic classes and independent evidence profiles are versioned |
| A7-P0-04 | Influence can be manufactured from weak correlates | Named claimant, wording, source, locator, direction/scope, qualification and heightened review are mandatory; inference count 0 |
| A7-P0-05 | Frozen TRACE can be mistaken for canonical graph authority | TRACE is explicitly a release/corpus projection; v48 facts remain reconciliation/history only |

### P1 — explicit holds

| ID | Hold | Promotion impact |
|---|---|---|
| A7-P1-01 | No authoritative edge-ID/predicate/endpoints/evidence mapping in the sole input | Accepted claims, semantic relations and TRACE projection remain zero |
| A7-P1-02 | No analysis-run identity for cluster/theme rows | 6,004 full edges and 5,840 active memberships remain computed and held |
| A7-P1-03 | No approved typed mapping for 19 full-only labels | 32,137 edges remain held without guessed family |
| A7-P1-04 | Three graph-only evidence rows have blank text and no approved locator-only profile | Those occurrences remain held |

No A7 P2 finding is required before independent package verification.

## 6. Unresolved items

The classification delta has no unclassified facts, but canonical promotion remains deliberately unresolved until new governed evidence exists:

- no accepted source/scholarly claim was created from the graph;
- no normalized semantic relation was created from the graph;
- no analysis-run provenance was recovered or invented;
- no TRACE projection or TRACE eligibility was granted;
- no unknown relation received a default family or epistemic class.

These are evidence holds, not missing ledger coverage.

## 7. Modifications and residual processes

A7 modified only the three assigned files. It did not modify architecture documents, scripts, data, SQLite, manifests, shards, frontend, package files, QA evidence or the protected dirty main.

The final approved target-path process scan returned no rows:

```text
A7_TARGET_WORKTREE_RESIDUAL_PROCESSES=0
A7_STARTED_SERVERS_OR_GENERATORS=0
```

## 8. Actions explicitly not performed

- No candidate JSON or SQLite rescan, full hash, integrity check or data export.
- No delimiter split, edge-label zip, merge, deduplication, inference or canonical promotion.
- No PostgreSQL, DDL, migration, import or database write.
- No npm, Next.js, TypeScript, browser, frontend screenshot, Docker, HTTP or image operation.
- No rights, provider, delivery or endpoint-health decision.
- No commit, push, PR, merge, deployment or protected-main cleanup.

## 9. Exit

```text
A7_SCOPE=PASS
OBSERVED_FULL_GRAPH_LABELS_CLASSIFIED=39
UNCLASSIFIED_GRAPH_FACT=0
UNKNOWN_RELATION_FAIL_CLOSED=true
SILENT_UNKNOWN_RELATION_FALLBACK=0
AUTOMATIC_INFLUENCE_INFERENCE=0
TRACE_ELIGIBLE_OBJECTS=0
A7_TARGET_WORKTREE_RESIDUAL_PROCESSES=0
```
