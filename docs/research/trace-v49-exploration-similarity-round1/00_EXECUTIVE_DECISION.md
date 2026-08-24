# TRACE v49 Round 6 executive decision

## Evidence state

`DOCUMENT_STATE=SEALED_PRECOMMIT_PASS`

This document is the decision surface for Exploration Affinity Research Round
1. Authoritative exhaustive Runs A and B are complete and their deterministic
payloads are exactly equal. The exact 24-file research package and bounded raw
receipts pass the independent verifier, all regressions pass, and the final
pre-commit package is sealed.

The immutable evaluation boundary is:

```text
SOURCE_SHA=0e311f0b88b4adc3cbfe2080ac98d622013cc6d3
PUBLIC_OBJECT_COUNT=7995
HELD_EXPLORATION_OBJECT_COUNT=0
EXHAUSTIVE_PAIR_COUNT=31956015
```

Run-specific timings are excluded from the deterministic material. The shared
deterministic payload SHA-256 is
`c4ba0106e4a361c52f56106f86aa6b4cc360ff48ecb26019fc3d248aac9fde8a`.
Only post-commit/post-push Git identity remains outside this research receipt.

## Research decision boundary

Round 6 evaluates transparent archive-derived affinity architectures. It does
not authorize a public Exploration route, public API, renderer, score, weight
set, clustering model, probability model, embedding, neural model, or final
template registry. All candidate output remains an
`exploratory_derived_signal`, never a `TraceSemanticEdge`, semantic relation,
historical claim, or probability of relation.

The round must issue exactly one verified decision:

```text
MODEL_DECISION=MODEL_FAMILY_SHORTLISTED
MODEL_SHORTLIST_COUNT=3
MODEL_SHORTLIST_IDS=M2,M5,M7
```

The decision shortlists three architectures rather than selecting a provisional
internal profile. Ablation sensitivity, measured hubness, correction trade-offs,
and pending researcher review make a single profile premature.
`PUBLIC_SIMILARITY_MODEL_SELECTED=false` remains fixed regardless of this
internal research decision.

## Verified independence result

The deterministic lineage implementation maps the inherited 64-signal
registry into 28 source-fact groups. Its verified classified basis contains
eight independent base signals and two separately residualized interaction
carriers; curation supplies recall and diagnostics but no independent score
family. These values reconcile byte-for-byte across
`04_INDEPENDENT_SIGNAL_BASIS.md`, `03_SIGNAL_LINEAGE_REGISTRY.tsv`, the raw
lineage receipt, and the final verifier.

The governing consequences are already non-negotiable:

- one source fact receives at most one base-affinity contribution;
- missing, unknown, and not-governed states add zero default affinity;
- comparability remains separate from affinity;
- governed geography class is a candidate/explanation fallback, not a second
  geography score;
- pair/triple evidence is candidate-only or separately residualized;
- raw curatorial Jaccard remains the isolated M0 negative control; and
- seeded randomness changes neither candidates nor affinity.

## Evaluation program

The full-corpus program evaluates:

| Area | Required evidence |
| --- | --- |
| Tasks | symmetric object-local affinity, user-conditioned retrieval, contrastive discovery requirements, and subset-pattern analysis |
| Candidate generation | CG-CUR-1 through CG-CUR-6; pool reduction and exhaustive recall at 10, 20, and 50 |
| Models | M0 through M8; M0 isolated and never shortlist eligible |
| Missingness | MISSING-A through MISSING-D with an explicit comparability channel |
| Curation | CUR-W1 through CUR-W6, including 25/50/75/90% broad-container stops |
| Interaction | eight statistics, five support thresholds, four residual policies, and zero parent duplication |
| Evaluation | 15 mechanical axioms, real-data sensitivity, ablation, hubness, bias, explanations, and a blinded review packet |
| Performance | exact streamed pair count, bounded top-k retention, index/query/runtime/memory measurements, and no pair matrix |
| Provenance | release/projection/registry/index/cohort pins and deterministic run receipts |

## Authoritative benchmark result

```text
CANDIDATE_ARCHITECTURE_SELECTED=true
SELECTED_CANDIDATE_VARIANT=CG-CUR-4
MODEL_SHORTLIST_IDS=M2,M5,M7
MECHANICAL_AXIOM_FAILURE_COUNT=0
CANDIDATE_RECALL_AT_20_MINIMUM=0.9995809881175735
SAME_SOURCE_FACT_DOUBLE_SCORE_COUNT=0
INTERACTION_PARENT_DOUBLE_COUNT_FAILURES=0
UNEXPLAINED_SHORTLIST_RESULT_COUNT=0
HUMAN_REVIEW_PACKET_READY=true
HUMAN_REVIEW_COMPLETED=false
```

CG-CUR-4 was selected by the predeclared rule: minimize median candidate pool
among variants whose minimum shortlist recall@20 is at least 0.98, with the
lineage-safe priority used only for exact ties. Its pool P50/P95/P99/MAX is
3,008/3,662/5,644/5,991; zero-candidate and near-full-corpus query counts are
both zero. Minimum recall at 10/20/50 is 0.9998499061913696,
0.9995809881175735, and 0.9974158849280801. Mean recall is
0.9998999374609131, 0.9997081509276632, and 0.9982472378569941.

The benchmark covers 25 model variants. M2 smoothed IDF cosine and M5
Gower-style TEMP-4 remain symmetric Task A candidates; M7 BM25F-like fielded
retrieval remains an explicitly asymmetric Task B candidate. None is a public
model. The deterministic human-review packet contains 72 anchors, including
all 15 inherited pathological cases, and intentionally contains no completed
judgment.

All 15 mechanical expectations pass in the benchmark; shared-unknown positive
credit, lineage double scoring, low-support inflation failure, interaction
parent duplication, curatorial-parent duplication, broad-container dominance,
and unexplained shortlist counts are zero. The full verifier independently
reconciles those claims against the authored TSV/raw package and passes 11
checks and all 24 EXP-SIM invariants across exactly 24 research files and 11
TSVs.

## Tabular evidence receipt

The one-time spreadsheet create-operation marker succeeded exactly once. The
bundled artifact workflow authored, imported, inspected, formula/error-scanned,
rendered, and visually checked all 11 required TSVs. All pass. Their data-row
and column shapes are:

```text
03_SIGNAL_LINEAGE_REGISTRY.tsv=64x16
07_CURATORIAL_ATTENUATION_EXPERIMENTS.tsv=9x33
10_MODEL_BENCHMARK_RESULTS.tsv=25x26
11_CANDIDATE_RECALL_RESULTS.tsv=72x19
12_SOURCE_BIAS_AND_FAMILY_DOMINANCE.tsv=15x15
13_HUBNESS_ANALYSIS.tsv=72x13
14_ABLATION_AND_STABILITY.tsv=648x13
15_INTERACTION_STATISTICS_REVIEW.tsv=40x9
16_MECHANICAL_EXPECTATION_CASES.tsv=15x14
17_HUMAN_REVIEW_PACKET.tsv=864x28
19_ANALYSIS_RUN_REGISTER.tsv=47x1
```

Their common source benchmark file SHA-256 is
`d42fdcc5eb63f0bbdb74cb57437eb40345314748c38393ad7876db13ea75c428`;
the TSV bytes total 918,719. No table is a pair matrix.

## Regression receipt

Full/runtime TypeScript, Search projection and 14 tests, TRACE preprogram (19
checks/16 invariants), Read Platform/page-by-key, Context projection/API/
governance/runtime/Canvas, Spacetime projection/governance/GIS/runtime/API, and
the production build all pass. Next 15.5.18 emits all 46 expected pages.
Expected Node SQLite and module-type warnings are non-blocking. Context and
Spacetime semantics remain frozen.

The final decision must explain any failed target or stop condition honestly.
A clean formula is not required, and no model may be selected merely to close
the round.

## Permanent non-selection boundary

```text
PUBLIC_SIMILARITY_MODEL_SELECTED=false
PUBLIC_SIMILARITY_WEIGHTS_SELECTED=false
PROBABILITY_MODEL_SELECTED=false
CLUSTERING_MODEL_SELECTED=false
PUBLIC_EXPLORATION_API_ADDED=false
PUBLIC_EXPLORATION_ROUTE_ADDED=false
EXPLORATION_RENDERER_IMPLEMENTED=false
EXPLORATION_TEMPLATE_REGISTRY_FROZEN=false
FULL_PAIR_MATRIX_COMMITTED=false
FULL_PAIR_MATRIX_IN_CLIENT=false
```
