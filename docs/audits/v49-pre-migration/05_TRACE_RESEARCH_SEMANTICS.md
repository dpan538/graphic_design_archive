# 05 — TRACE Research Semantics

- Audit package: **A5**
- Audit date: **2026-08-11** (Australia/Brisbane)
- Baseline branch: `refactor/v49-data-platform`
- Baseline commit: `f076ca3444aaa0f413bb61fe2cb568d6a9aa2720`
- Frozen source ancestor: `0404c7f96f9189f576c4c5b1368061e4082e436b`
- Independent scope: TRACE epistemics, relation/claim/projection identity, research-corpus selection, missingness, source concentration, coverage, and research-quality gates
- Unique output: `docs/audits/v49-pre-migration/05_TRACE_RESEARCH_SEMANTICS.md`
- Audit coverage: **COMPLETE**
- Readiness result: **PARTIAL**

`PARTIAL` means the repository boundary requested for A5 was fully inspected, but research semantics are not ready to become physical DDL. The frozen v48 product has strong no-inference language, exact count units, object-level source return, active/review/auxiliary separation, and three useful research views. It does not yet provide the independent identities and governed cardinalities needed for semantic relations, source/scholarly claims, computed analyses, TRACE release projections, strict research corpora, or evidence-bounded missingness statements.

The safe conclusion is:

```text
15,923 Browse Index objects are operational catalogued design objects.
They are not 15,923 independently proven unique intellectual works.

255,695 stored TRACE graph edges are frozen graph evidence.
They are not 255,695 interchangeable scholarly or causal claims.

126,822 active-object relation memberships are a projection unit.
They are not a measure of historical importance, influence, or corpus quality.
```

## 1. Scope

This package audited:

- the nine v49 architecture documents for research semantics and pre-DDL gates;
- the A3 data-authority/lineage report and A4 DDL-readiness report as shared evidence;
- frozen TRACE manifest, atlas, catalog, auxiliary product, and a representative neighborhood shard;
- TRACE types, taxonomy, generator, visual decisions, and active component reachability;
- v48 research-positioning, methodology, coverage, packet-structure, packet-readiness, and research-review documents;
- measured population, graph-unit, evidence, layer, source-concentration, tree-concentration, medium-concentration, and mapped/unmapped boundaries;
- whether Atlas, Constellation, and Object TRACE answer independent research questions;
- the minimum research-quality gate that must close before physical research/TRACE DDL.

Primary affected paths:

- `ARCHITECTURE.md`, `DATA_MODEL_V49.md`, `MIGRATION_V48_TO_V49.md`, `ACCEPTANCE_GATES.md`;
- `docs/architecture/DDL_DECISION_PACK_V49.md` and the three v49 ADRs;
- `docs/research/MODERN_GRAPHIC_DESIGN_RESEARCH_AND_ARCHIVE_COMPARISON_V48.md`;
- `docs/methodology/Methodology_v0.md` and `docs/methodology/RESEARCH_PACKET_STRUCTURE_METHOD_v1.md`;
- `docs/system/TRACE_VISUALIZATION_V48_*.md`, `docs/system/COVERAGE_ASSESSMENT.md`, and `docs/system/REGIONAL_COVERAGE_FRAMEWORK.md`;
- `docs/TRACE_VISUALIZATION_DECISION_v48.md`, `docs/TRACE_VISUAL_ANALYTICS_MOBILE_DECISION_V48.md`, `docs/TRACE_EVOLUTION_FIELD_DECISION.md`, and `docs/TRACE_VISUALIZATION_ROUND2_ASSESSMENT.md`;
- `frontend/src/components/archive/trace/trace-types.ts`, `trace-taxonomy.ts`, `TraceExplorer.tsx`, `TraceConstellation.tsx`, `TraceConstellationSystem.tsx`, and `TraceDiagrams.tsx`;
- `scripts/build_prefreeze_candidate_v48_trace_visualization.py`;
- `frontend/public/data/trace-v48/`;
- source-concentration, coverage, region-gap, and research-packet CSVs under `data/`.

Rights policy and visual-registry implementation are owned by A6. Frontend performance is owned by A7. AI/RAG corpus retirement is owned by A8. This report only records their research-semantic intersections.

## 2. Evidence commands

All commands were read-only. No secret value was requested or printed. Representative exact forms are shown below; large outputs were inspected in bounded ranges.

```sh
repo=/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform

sed -n '1,280p' DATA_MODEL_V49.md
sed -n '1,420p' docs/architecture/DDL_DECISION_PACK_V49.md
sed -n '1,220p' ACCEPTANCE_GATES.md
sed -n '1,190p' MIGRATION_V48_TO_V49.md

rg -n -i --context 3 \
  'archive object|intellectual work|semantic relation|epistem|claim|assertion|trace node|relation_edge|computed|causal|influence|corpus|inclusion|exclusion|missingness|concentration|coverage' \
  ARCHITECTURE.md DATA_MODEL_V49.md READ_API_V1.md \
  MIGRATION_V48_TO_V49.md ACCEPTANCE_GATES.md \
  docs/adr/*.md docs/architecture/DDL_DECISION_PACK_V49.md

for term in corpus missingness claimant 'analysis run' parameters score \
  documented_fact scholarly_claim computed_association causal_interpretation; do
  rg -n -i "$term" ARCHITECTURE.md DATA_MODEL_V49.md READ_API_V1.md \
    MIGRATION_V48_TO_V49.md ACCEPTANCE_GATES.md \
    docs/adr/*.md docs/architecture/DDL_DECISION_PACK_V49.md
done

sed -n '1,700p' \
  docs/research/MODERN_GRAPHIC_DESIGN_RESEARCH_AND_ARCHIVE_COMPARISON_V48.md
sed -n '1,760p' docs/methodology/Methodology_v0.md
sed -n '1,220p' docs/methodology/RESEARCH_PACKET_STRUCTURE_METHOD_v1.md
sed -n '1,180p' docs/capture/RESEARCH_PACKET_READINESS_LAYER_v1.md
sed -n '1,520p' docs/audits/v49-pre-migration/03_DATA_ASSET_AUTHORITY_AND_LINEAGE.md
sed -n '1,540p' docs/audits/v49-pre-migration/04_DATABASE_AND_DDL_READINESS.md

sed -n '1,300p' frontend/src/components/archive/trace/trace-types.ts
sed -n '1,360p' frontend/src/components/archive/trace/trace-taxonomy.ts
sed -n '1,460p' scripts/build_prefreeze_candidate_v48_trace_visualization.py

jq '{version,status,policy,counts,relationTypes,treeCounts,topSources,mediumGroups}' \
  frontend/public/data/trace-v48/atlas.json
jq '{relation_type_count:(.relationTypes|length),relation_membership_sum:(.relationTypes|map(.count)|add),graph_edges:.counts.traceEdges,tree_membership_sum:(.treeCounts|map(.count)|add)}' \
  frontend/public/data/trace-v48/atlas.json
jq '{version,layer,countEligible,item_count:(.items|length),first:(.items[0] // null)}' \
  frontend/public/data/trace-v48/auxiliary.json
jq '{version,shard,object_count:(.objects|length),first:(.objects|to_entries|.[0])}' \
  frontend/public/data/trace-v48/neighborhoods/000.json

rg -o 'status: "[^"]+"' \
  frontend/src/components/archive/trace/trace-taxonomy.ts | sort | uniq -c
rg -n 'return "medium_context"|MC-OTHER|retained without a registered display definition' \
  scripts/build_prefreeze_candidate_v48_trace_visualization.py \
  frontend/src/components/archive/trace/trace-taxonomy.ts

rg -n 'TraceConstellation(System)?' frontend/src --glob '*.tsx' --glob '*.ts'
rg -n 'EvolutionSystemPlate|ChronogeographicRoutes|TimeGeographyMap|TraceDiagrams' \
  frontend/src --glob '*.tsx' --glob '*.ts'

sed -n '1,120p' data/research_packet_readiness_layer_summary_v1.csv
sed -n '1,8p' data/prefreeze_source_authority_concentration_v1.csv
sed -n '1,8p' data/recent_source_concentration_review_v1.csv
sed -n '1,8p' data/prefreeze_region_period_gap_matrix_v1.csv
sed -n '1,180p' docs/capture/SOURCE_COVERAGE_RATE_v2.md
rg -n --context 5 'research_quality_adjusted|target|balance_rate' \
  scripts/audit_source_coverage_rate_v2.py
```

A5 did not open SQLite. Exact SQLite identities, counts, orphan checks, evidence duplicates, and the one coordinated integrity run are reused from [03 — Data Asset Authority and Lineage](03_DATA_ASSET_AUTHORITY_AND_LINEAGE.md). This avoids a redundant full-database scan.

## 3. Measured v48 research boundary

### 3.1 Population and layers

| Unit | Measured value | Research-safe interpretation |
|---|---:|---|
| Canonical/active TRACE object IDs | 15,923 unique | Operational catalogued design-object rows in the frozen Browse Index |
| Archive Search IDs | 8,636 unique | Legacy derived Search projection, not a research corpus or canonical database |
| Canonical/TRACE ∩ Search | 2,585 | IDs represented in both products |
| Search-only | 6,051 | Derived-product exclusions; never missing migration objects |
| Canonical/TRACE-only | 13,338 | Canonical objects without the legacy internal Search/surface route |
| Canonical/TRACE ∪ Search | 21,974 | Set reconciliation only; not a corpus target |
| Review/authority hold | 4,425 | Isolated release/read layer; not active-count eligible |
| Auxiliary TRACE objects | 11 | Count-ineligible contextual branch; not promoted to the main design-object cohort |

The 15,923 active rows are a complete v48 operational Browse Index boundary. No file or normative rule proves that all 15,923 are distinct intellectual works, that all are equally research-ready, or that all must enter every strict research corpus.

### 3.2 Graph and evidence units

| Unit | Measured value | Boundary |
|---|---:|---|
| TRACE nodes | 97,889 | Independent graph nodes, not archive objects or claims |
| Total graph edges | 255,695 | Unique frozen directed triples across the stored graph |
| Active-object relation memberships | 126,822 | Object-to-edge projection rows; the 20 observed relation counts sum to this value |
| Medium/context memberships | 79,206 | Projection family count, not a historical-causation measure |
| Source/provenance memberships | 31,288 | Projection family count |
| Time/place memberships | 16,328 | Projection family count |
| Historical influence | 0 | No active v48 `influenced_by` edge satisfies the current evidence rule |
| Active research trees | 30 | v48 tree counts sum to 15,923; they are curated organization, not 30 historical genealogies |

A3 measured 255,247 distinct `(evidence_url,evidence_text,evidence_field)` composites for 255,695 edges, 389 reused evidence composites across 837 edges, and three blank evidence texts. Evidence is therefore shareable and cannot be edge identity. A locator-only evidence class may make a blank text valid, but the rule does not yet exist; these three cases must remain explicit in the graph delta ledger.

### 3.3 Relation vocabulary actually exposed

The frozen atlas contains 20 observed relation labels. The frontend taxonomy defines those 20 plus a reserved zero-count `influenced_by` definition:

- 18 observed definitions are labelled `documented`;
- 2 observed definitions are labelled `analytical` (`associated_with_research_cluster`, `associated_with_theme`);
- 1 reserved definition is `absent_in_v48` (`influenced_by`).

This three-value display vocabulary is useful but not an epistemic model. It cannot represent a source statement disputed by another source, a named scholar's interpretation, a computed association with a method and score, or a causal claim that is challenged but retained.

### 3.4 Concentration and coverage observations

Measured from the frozen active atlas:

| Observation | Value | Interpretation limit |
|---|---:|---|
| Top five source labels | 11,210 / 15,923 = 70.40% | Source-label concentration in this release, not institutional authority or world-history share |
| Top 20 source labels | 14,704 / 15,923 = 92.34% | Requires provider/source-family normalization before HHI or cross-release comparison |
| Top three research trees | 11,444 / 15,923 = 71.87% | Curatorial/tree concentration, not evidence strength or historical importance |
| `graphic object / other` + `poster` | 14,755 / 15,923 = 92.67% | Current display grouping and source mix, not the real medium distribution of design history |
| Mapped normalized region rows | 15,569 | Region aggregation, not production coordinates |
| Intentionally unmapped | 354 | Broad, transnational, historic, or unsupported map geometry remains visible as missing/unsupported mapping |

The repository contains useful working diagnostics (`prefreeze_source_authority_concentration_v1.csv`, `prefreeze_region_period_gap_matrix_v1.csv`, `SOURCE_COVERAGE_RATE_v2.md`), but they do not form one release-bound research measurement model. In particular, Source Coverage v2 reads the legacy `generated/public_surfaces_v1.json`, applies manually chosen period/region targets, multiplies four rates into a 2.31 composite, and calls it release-facing. It is historical derived analysis, not a v49 freeze metric.

### 3.5 Research packet readiness is not corpus admission

The packet-readiness ledger contains 2,088 cluster rows and only 113 marked safe for a sandbox packet-shape trial. Its largest blockers are:

- 1,274 missing or unsettled normal-main anchors;
- 394 parentage/relation-confidence cases not ready;
- 199 unresolved global or macro scope cases;
- 107 editorial/cover work requirements;
- 81 method-review holds;
- only 6 rows with no blocking issue.

These are valuable editorial workflow observations. They demonstrate why “present in Browse Index” and “admitted to a strict research corpus/packet” must be separate decisions. They must not be imported as canonical truth without lineage to the exact input release and selection rule version.

## 4. Archive-object semantics

### Result: **FAIL — P0 before DDL**

The Phase 1A seed rule is appropriately conservative: one UUIDv5 object is created for each canonical JSON `surfaceId`, with no automatic deduplication. The decision pack also says v48 does not independently express intellectual-object identity. However, `DATA_MODEL_V49.md` still calls `core.archive_object` a “stable intellectual-object subtype identity.”

The measured source supports only this normative meaning:

> An archive object is the operational catalogued design object around which this index binds source descriptions, surfaces, representations, classifications, research claims, and release projections. A v48 seed object corresponds to one frozen canonical row. Its existence does not assert that it is the unique intellectual work, that another row is a different work, or that item, manifestation, edition, design concept, and digital surrogate are identical.

Required consequences:

1. v48 seeding remains exactly one operational object per row; no deduplication is introduced.
2. Work/concept, manifestation/edition, physical/digital item, event, and surrogate identity are later evidence-bearing typed entities or relations, not assumptions hidden in the archive-object PK.
3. Merge/split decisions require claims, evidence, and a curator decision; source-key/title/image similarity is insufficient.
4. A research claim may target the operational object, a later identified work/manifestation, a source record, a representation, or another typed subject. The target must remain explicit.

This decision closes an ontological overclaim without deleting or weakening any of the 15,923 records.

## 5. Semantic relation, claim, and TRACE projection

### Result: **FAIL — P0 before DDL**

The current v49 model calls `research.relation_edge` both a canonical semantic assignment and a TRACE node triple. The current v48 product stores evidence, confidence, review state, and inference check directly on `TraceEdge`. These are different identity layers.

The required model is:

```text
immutable evidence item(s)
        │ supports / challenges
        ▼
source- or scholar-bounded claim(s)
        │ accepted support / contradiction / qualification
        ▼
normalized semantic relation proposition
        │ selected under one corpus + release policy
        ▼
sealed TRACE projection (nodes, edge, tree/branch placement, display layer)
```

| Layer | Identity and cardinality | Must not mean |
|---|---|---|
| Evidence | Source artifact/record, locator/span, content hash; N:M with claims | A relation or truth merely because a URL exists |
| Claim | One claimant, exact wording or structured proposition, source/citation, locator, epistemic class, stance; many claims may discuss one relation | The normalized relation itself |
| Semantic relation | Stable typed subject–predicate–object proposition; may be supported, challenged, qualified, or unresolved by many claims | A TRACE node placement or one scholar's wording |
| TRACE projection | Release/corpus-specific rendering of eligible relation/claim material into nodes/edges/trees; one underlying relation may have multiple placements | Canonical source evidence or a timeless graph fact |

The v48 directed triple `(subject_trace_node_id, relation_type_id, object_trace_node_id)` remains a valid frozen projection key and reconciliation unit. It must not become the universal natural key for claims. Competing claims can share a proposition while differing in claimant, wording, evidence, date, stance, and epistemic status.

Before graph migration, every legacy node, edge, evidence tuple, object membership, tree/branch placement, review row, and auxiliary fact must be classified as:

- `REGENERABLE` from canonical JSON plus governed configuration;
- `GOVERNED_EXTERNAL_EVIDENCE` with independently preserved authoritative evidence and an explicit ingest decision; or
- `HOLD`.

The current TRACE generator reads reconciliation SQLite, a v47 adjunct, and a legacy frontend payload. Its frozen output is valid v48 evidence, but graph parity alone does not authorize those rows to enter v49 canonical research tables.

## 6. Epistemic relation classes

### Result: **FAIL — P0 before DDL**

The v49 normative corpus contains no structured definitions for `documented_fact`, `scholarly_claim`, `computed_association`, or `causal_interpretation`. The minimum pre-DDL contract is:

| Class | Required content | Acceptance boundary |
|---|---|---|
| `documented_fact` | Prefer the public label “documented source statement”; source/claimant, exact source record, original wording or preserved structured value, locator, date/access context, predicate mapping | Records what a source states; does not silently convert provider metadata into universal truth |
| `scholarly_claim` | Claimant agent, cited publication/source, exact locator, preserved wording or licensed excerpt/hash, claim date/version, stance, review state | May support/challenge/qualify a relation; competing claims remain separate |
| `computed_association` | Analysis-run identity, method and software version/hash, deterministic parameters, input `researchReleaseId + researchManifestSha256`, corpus version/hash, output subject/object, score, uncertainty/threshold, generated time | Never published as documented fact or causation; reruns are separately addressable |
| `causal_interpretation` | Named claimant, exact wording, source/citation and locator, causal predicate, scope/qualifiers, evidence chain, heightened review decision | Cannot be created by similarity, co-occurrence, time, place, source, medium, cluster, or score alone |

Epistemic class, acceptance state, evidence tier, confidence/score, workflow state, publication layer, and metric eligibility are independent axes. A high numeric score does not change a computed association into a documented fact. An accepted claim does not require its TRACE projection to be active in every corpus.

### 6.1 Historical influence

The current zero `influenced_by` count is a methodological success, not missing data and not a claim that influence did not occur.

Any future influence claim must retain:

- claimant identity and role;
- the claimant's wording, not a generated paraphrase alone;
- source/citation identity and exact locator;
- subject and object at the correct entity layer;
- direction, scope, qualification, and temporal context;
- evidence stance and competing claims;
- reviewer decision and stricter relation-policy version;
- the research release/corpus in which it is projected.

No influence edge may be synthesized from visual similarity, shared metadata, shared geography, chronology, medium, collection, research cluster, or computed score.

### 6.2 Computed analyses

Atlas aggregation, same-period co-presence, source concentration, provider ablation, balanced resampling, clustering, similarity, and ranking are analyses. Their results require an analysis-run record with method/version, parameters, exact input release and corpus hashes, score/unit, and output artifact hash. A visual line, adjacency, or layout coordinate is not itself a semantic relation.

The current `associated_with_research_cluster` and `associated_with_theme` labels are marked analytical but carry no analysis-run identity in the read product. They remain frozen v48 display evidence and must be held from v49 semantic promotion until their governed assignment provenance is classified.

## 7. Corpus selection, missingness, and coverage

### Result: **FAIL — P0 before DDL**

The nine v49 documents do not define a research corpus, corpus membership, selection policy, missingness observation, or source-concentration analysis. The word `corpus` occurs only in the phrase “normative architecture corpus”; `missingness` is absent.

### 7.1 Browse Index versus research corpus

The required boundary is:

| Product | Population rule | Intended use |
|---|---|---|
| Browse Index | All 15,923 operational v48 seed objects that satisfy the frozen active publication layer | Discovery, source return, portfolio/corpus-scale evidence, and reconciliation |
| Strict TRACE research corpus | An explicitly versioned subset selected by a named research question, eligibility rule, evidence threshold, rights-safe metadata rule, and curator/analysis decision | Research claims, metrics, comparisons, and TRACE projections |
| Review corpus | Explicitly scoped unresolved/held records, never silently mixed into the strict corpus | Bias, authority, and missingness study |
| Auxiliary/context corpus | Explicit contextual records such as the 11 v48 adjuncts, with separate eligibility and claim limits | Contextual comparison without main-object promotion |

There may be multiple overlapping strict corpora. No universal `in_research_corpus` boolean is sufficient. Each corpus version needs:

- corpus ID/version and immutable policy hash;
- research question/scope and population frame;
- inclusion and exclusion criteria;
- subject membership with decision, reason code, evidence, actor/run, and validity;
- exact input research release/manifest hash;
- count/unit query hash;
- explicit treatment of review, auxiliary, withdrawn, rights-limited, and unavailable records;
- immutable membership snapshot at seal.

### 7.2 Missingness

Missingness must be an evidence-bounded observation, not a guessed explanation for an unknown world population. At minimum, reason classes must distinguish:

- `not_collected_or_not_known`;
- `not_digitized`;
- `not_discovered_by_project`;
- `source_unavailable_or_endpoint_failed`;
- `metadata_insufficient`;
- `authority_or_language_unresolved`;
- `rights_restricted_or_display_withheld`;
- `excluded_by_declared_scope`;
- `excluded_by_quality_rule`;
- `duplicate_or_identity_unresolved`;
- `not_geometrically_mappable`;
- `unknown_cause`.

Each observation needs the scoped denominator or population frame, metric/unit, observed date, source/evidence, method/run, release/corpus hash, and confidence. “No record found,” “record exists but no image may be shown,” and “record excluded from this research question” are different states.

### 7.3 Source concentration and coverage

Research metrics must be release- and corpus-scoped analyses, not mutable public constants. The freeze gate should require, at minimum:

- normalized provider/source-family definitions and registry hash;
- Top-k share and HHI by object membership, claim evidence, and image-visible representation as separate units;
- region, period, medium, language/script, source type, rights mode, and publication-layer distributions;
- known missingness and unresolved rates by the same axes;
- provider-ablation or other sensitivity analysis for any public comparative claim;
- exact query/method/parameter/input hashes;
- no single opaque “coverage score” used as a truth or promotion gate.

The measured 70.40% top-five source-label share is a current-release risk signal. It does not by itself prove bias in real design history; it proves that source supply strongly shapes this indexed corpus.

## 8. TRACE research views: preserve, constrain, and consolidate

Visual complexity and scale are not deletion reasons. The three principal views answer independent questions and should remain available after repository decoupling.

| View | Classification | Independent research question | Required semantic boundary |
|---|---|---|---|
| Global Atlas / evolution field | `KEEP_ACTIVE` | How does the indexed corpus distribute across time, normalized geography, source, medium, layer, and missing-map status? | Always names release/corpus and unit; distribution is not diffusion, importance, or causation |
| Evidence Constellation | `KEEP_ACTIVE` | How are curated research-tree memberships and observed relation-family memberships distributed? | Tree size is organizational attention; family volume is membership count; neither is evidence strength or historical prevalence |
| Object TRACE | `KEEP_ACTIVE` | Which source-bounded claims/evidence support the selected object's normalized relations, and what is prohibited from inference? | Must project claim/evidence identity, not only flatten evidence fields onto an edge |

Additional findings:

- `ChronogeographicRoutes` and `EvolutionSystemPlate` are valid derived readings when each publishes a distinct research question and unit. If both merely redraw the same region×decade counts, they are `HOLD_UNKNOWN` for semantic consolidation, not deletion by visual complexity.
- `frontend/src/components/archive/trace/TraceConstellationSystem.tsx` is the imported active constellation implementation.
- `frontend/src/components/archive/trace/TraceConstellation.tsx` has no importer in the scanned frontend source. It is a **P2 `DELETE_CANDIDATE`** as an apparently superseded duplicate implementation, but only after A7 confirms route reachability and Git remains the recovery reference. No deletion occurred.
- The local metro, map, and source tree remain useful object-level grammars because they deliberately separate medium/context, time/place, and source/provenance questions.

## 9. Legacy fail-open behavior

### Result: **FAIL for reuse; frozen v48 remains archival evidence**

Two legacy code paths coerce unknown labels:

1. `relation_family()` in `scripts/build_prefreeze_candidate_v48_trace_visualization.py` returns `medium_context` for every label not explicitly recognized as influence, provenance, or time/place.
2. `traceTypeFor()` in `trace-taxonomy.ts` synthesizes an `MC-OTHER` definition with status `documented` for an unregistered label.

This contradicts the accepted v49 fail-closed rule. The frozen v48 assets remain read-only historical/QA evidence, but these fallbacks must not be reused for migration, v49 release generation, or API projection. Acceptance requires that unknown labels remain raw proposed assertions in a workflow queue and create no semantic relation, family, TRACE projection, publication row, or metric row.

## 10. Research/data-quality freeze gate

Before physical research/TRACE DDL, the normative gate must exist. Before a database freeze, it must be implemented and evidenced. A research/data-quality gate may pass only when:

1. operational archive-object semantics are fixed and no seed row is presented as a proven unique intellectual work;
2. evidence, claim, semantic relation, and TRACE projection identities/cardinalities are separate;
3. the four epistemic classes and their required provenance are registered and versioned;
4. every influence claim retains claimant, wording, source, locator, stance, and heightened review;
5. every computed association retains analysis run, method/version, parameters, input research-release/manifest and corpus hashes, score, and uncertainty;
6. every legacy graph fact is `REGENERABLE`, `GOVERNED_EXTERNAL_EVIDENCE`, or `HOLD`, with zero unclassified facts;
7. every published research metric names release, corpus, unit, query/method hash, and denominator;
8. Browse Index, strict research corpus, review corpus, and auxiliary/context corpus are explicitly separated;
9. corpus membership has inclusion/exclusion policy, reason, evidence, and immutable version identity;
10. missingness reasons and unknown cause remain distinguishable and evidence-bounded;
11. source concentration and coverage are multi-axis diagnostics, not one composite score;
12. total graph edges, active-object memberships, claims, semantic relations, and projected TRACE edges remain different count units;
13. the known 2,970/2,971 summary conflict is preserved as a declared historical delta and row-level parity is authoritative;
14. 20,000/4,077 remains historical aspiration only and cannot block migration, freeze, or promotion;
15. unknown relation behavior passes a negative fail-closed test in the later implementation phase.

## 11. Findings and priorities

### P0 — must close before physical v49 research/TRACE DDL

| ID | Finding / affected paths | Risk | Required action and acceptance |
|---|---|---|---|
| A5-P0-01 | `core.archive_object` is still called an intellectual-object identity | One source row can be mistaken for a globally unique work; merge/split and claim targets become ontological guesses | Define operational catalogued design object; model work/manifestation/item/surrogate identity separately with evidence |
| A5-P0-02 | Semantic relation, claim, and TRACE projection share one edge concept | Competing or qualified claims collapse; release placement becomes canonical truth | Define independent identities/cardinalities and projection support path |
| A5-P0-03 | Requested epistemic classes are absent | Documented source statements, scholarship, computation, and causation can be rendered equivalently | Register the four classes and exact required provenance; no implicit promotion between them |
| A5-P0-04 | Influence and computed-analysis provenance are underspecified | Causation can be manufactured from similarity/counts; analytical results cannot be reproduced | Require claimant/source/locator/wording for influence and run/method/params/input hashes/score for computation |
| A5-P0-05 | No versioned corpus-selection or missingness model exists | 15,923 Browse rows can be mislabeled a representative research corpus; absences can be guessed | Define versioned N:M corpus membership, selection policy, evidence-bounded missingness and strict corpus separation |
| A5-P0-06 | TRACE graph cannot be regenerated from the sole migration input | SQLite/shard-only graph facts could be laundered into canonical research data | Complete the graph-authority delta ledger; zero unclassified graph facts; `HOLD` non-authoritative facts |
| A5-P0-07 | Legacy generator and taxonomy fail open to `medium_context/documented` | Unknown predicates can silently become publishable research relations | Deny legacy fallback reuse; v49 negative fixture must prove zero edge/family/projection leakage |
| A5-P0-08 | No normative research/data-quality freeze gate exists | DDL/freeze can appear complete while claim, corpus, bias, and missingness semantics are unresolved | Add the 15-part gate above with separate research-semantics readiness status |

### P1 — close before research release/freeze

| ID | Finding | Risk | Recommended action |
|---|---|---|---|
| A5-P1-01 | Historic/visual docs sometimes call 255,695 “documented relations” while 126,822 is the observed active relation-membership sum | Public and research writing can compare different units under one label | Reserve `total graph edges` and `active-object relation memberships`; count claims and projected edges separately |
| A5-P1-02 | Top-source, medium, tree, and geographic concentration are visible but not release-bound analysis runs | Results can drift or be mistaken for historical prevalence | Seal normalized registry, query, corpus, method, parameter and result hashes |
| A5-P1-03 | Source Coverage v2 uses a legacy population, manual targets and an opaque multiplicative composite | A 2.31 score can be mistaken for objective research quality | Archive as historical analysis; replace with named multi-axis metrics and explicit denominators |
| A5-P1-04 | Packet-readiness decisions are rich but not tied to a sealed research release/corpus | Editorial readiness could silently become canonical membership | Preserve as workflow evidence and re-evaluate against pinned corpus/release identity |
| A5-P1-05 | Object TRACE flattens evidence fields onto edges and lacks stable claim citations | Users cannot cite or compare competing claims independently | Project stable claim/evidence IDs, stances, citations, and prohibited-inference text |
| A5-P1-06 | Analytical cluster/theme assignments lack run/method identity in the read product | Curatorial grouping and computation cannot be distinguished or reproduced | Classify each assignment as curator decision or computed run before migration |

### P2 — refinement after semantic closure

| ID | Finding | Risk | Recommended action |
|---|---|---|---|
| A5-P2-01 | `TraceConstellation.tsx` appears unreachable while `TraceConstellationSystem.tsx` is active | Duplicate code obscures the authoritative visualization implementation | A7 verifies reachability; then list old component for recoverable deletion in a later authorized cleanup |
| A5-P2-02 | Evolution and chronogeographic views may overlap the same region×decade aggregate | Multiple visual forms may look like independent evidence | Give each a named analytical question/output contract or consolidate presentation while preserving underlying research capability |
| A5-P2-03 | Three blank v48 edge evidence texts lack an explicit locator-only class | A valid locator-only item and incomplete evidence are indistinguishable | Classify each in graph delta ledger and define required evidence fields by evidence kind |
| A5-P2-04 | Research-quality targets such as double coding, provider ablation and user no-inference studies remain future work | Methodological potential can be advertised as proven contribution | Keep claims provisional until study protocols, samples, results and release hashes exist |

Priority totals for A5: **P0 8 / P1 6 / P2 4**.

## 12. Gate assessment

| Area | Result | Evidence |
|---|---|---|
| A5 repository/document/code/data coverage | COMPLETE | Every requested A5 category has evidence commands and a result |
| Operational Browse Index population | PASS | 15,923 exact operational objects; layer and Search set boundaries known |
| Operational object vs unique intellectual work | FAIL | Seed policy is conservative, but normative subtype wording still overclaims |
| TRACE graph count/unit separation | PASS | 97,889 nodes, 255,695 edges and 126,822 memberships remain distinct |
| Semantic relation / claim / TRACE projection separation | FAIL | No independent claim/projection identity model |
| Epistemic relation classes | FAIL | Four required classes and cardinalities absent |
| Historical influence safeguards | PARTIAL | Strong zero-edge/no-inference policy exists; claimant/wording/locator model absent |
| Computed-association reproducibility | FAIL | No analysis-run/method/input-release/score contract |
| Strict research corpus model | FAIL | Browse population exists; versioned corpus selection does not |
| Missingness model | FAIL | Narrative awareness exists; structured evidence-bounded model does not |
| Source concentration/coverage evidence | PARTIAL | Risks measured; registry/run/corpus-bound metrics absent |
| Graph migration authority | FAIL | Frozen graph is verifiable but not authoritative from JSON alone |
| Atlas preservation | PASS | Independent aggregate research question and explicit no-causation boundary |
| Constellation preservation | PASS | Independent tree/relation-membership question; active implementation identified |
| Object TRACE preservation | PASS | Independent object-to-source/evidence question; claim-level upgrade required |
| Unknown-relation fail-closed architecture | PASS | Phase 1A rule is explicit |
| Unknown-relation legacy implementation | FAIL FOR REUSE | Two observed fallbacks coerce unknown labels |
| Research/data-quality freeze gate | FAIL | No normative gate currently covers all required semantics |

## 13. Readiness state

```text
AUDIT_COVERAGE_TRACE_RESEARCH=COMPLETE
RESEARCH_SEMANTICS_PRE_DDL_READY=false
OVERALL_PRE_DDL_READY=false
DATABASE_IMPLEMENTED=false
DATABASE_FREEZE_READY=false
FRONTEND_PROMOTION_READY=false
DEPLOYMENT_READY=false
```

The false readiness values do not invalidate v48. They distinguish a strong frozen visualization/reconciliation product from a governed research claim and corpus model suitable for new physical keys.

## 14. Recommended closure sequence

At most three independent tasks follow from A5:

1. **Research identity and epistemic contract.** Define operational archive objects, work/manifestation/item/surrogate relations, evidence, four claim classes, semantic relation propositions, and sealed TRACE projections. Acceptance: every identity/cardinality is explicit; influence and computation retain all required provenance; competing claims do not collapse.
2. **Corpus, selection, missingness, and metric contract.** Define versioned N:M corpus membership, inclusion/exclusion evidence, missingness reason model, normalized provider/source registry, and release-bound multi-axis analyses. Acceptance: Browse Index and strict corpora are distinct; every metric has exact release/corpus/unit/query/method hashes; no opaque coverage score is a promotion gate.
3. **Legacy graph authority ledger and freeze gate.** Classify every v48 graph fact `REGENERABLE`, `GOVERNED_EXTERNAL_EVIDENCE`, or `HOLD`; quarantine fail-open generators; add the research/data-quality gate. Acceptance: zero unclassified facts and zero unknown-label coercion; non-authoritative material cannot enter v49 canonical research data.

## 15. Actions explicitly not performed

- No normative architecture document was modified by A5.
- No frontend, script, package, CI, deployment, data, SQLite, shard, manifest, receipt, or QA screenshot was modified.
- No PostgreSQL, Docker, SQLite query/write, migration, `VACUUM`, data import/export/regeneration, npm, Next.js, TypeScript, browser, screenshot, server, or model process was started.
- No third-party image or web resource was downloaded.
- No legacy graph fact was promoted, reclassified, deleted, or rewritten.
- No visual was deleted because of complexity, scale, style, or lack of runtime replay.
- No commit, push, merge, rebase, PR, force push, or deployment was performed by A5.
- No secret file was opened and no secret value was printed.

## 16. Residual processes and handoff

Every A5 shell execution completed and released its session. A5 started no Node, Next, TypeScript, PostgreSQL, Docker, browser automation, data generation/export, server, or model process. A5-owned residual sessions: **0**. The global OS residual-process scan remains assigned to the main auditor.

The main auditor should use this report to calibrate the allowed v49 normative documents, then re-evaluate A5-P0-01 through A5-P0-08. Until all eight close, `RESEARCH_SEMANTICS_PRE_DDL_READY` and `OVERALL_PRE_DDL_READY` must remain `false`.
