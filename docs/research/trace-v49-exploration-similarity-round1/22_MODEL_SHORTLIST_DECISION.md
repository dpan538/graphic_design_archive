# Model shortlist decision

## Decision state

`DOCUMENT_STATE=SEALED_PRECOMMIT_PASS`

```text
MODEL_DECISION=MODEL_FAMILY_SHORTLISTED
MODEL_SHORTLIST_COUNT=3
MODEL_SHORTLIST_IDS=M2,M5,M7
CANDIDATE_ARCHITECTURE_SELECTED=true
SELECTED_CANDIDATE_VARIANT=CG-CUR-4
PUBLIC_SIMILARITY_MODEL_SELECTED=false
PUBLIC_SIMILARITY_WEIGHTS_SELECTED=false
```

Authoritative Runs A and B support `MODEL_FAMILY_SHORTLISTED`. Exactly three
architectures remain: M2 and M5 for symmetric Task A, and M7 for asymmetric
Task B. This shortlist is an internal research result, not a final score,
weight set, public product decision, historical model, or claim that one method
is correct.

## Shortlisted architecture families

The benchmark evaluated and retained three predeclared architecture hypotheses:

| Architecture hypothesis | Intended task | Why it is tested | Mandatory cautions |
| --- | --- | --- | --- |
| M2 `M2-SMOOTHED_IDF` | symmetric Task A | transparent approved-feature weighting with within-family normalization | geography ablation and hubness remain material diagnostics |
| M5 `M5-GOWER-TEMP-4` | symmetric Task A | direct mixed-family interpretation with explicit availability masks and interval overlap | geography ablation and hubness remain material diagnostics |
| M7 `M7-BM25F-QUERY` | asymmetric Task B | explicit selected-object/filter query with inspectable field weighting | time ablation and strongest observed shortlist hubness; never a universal similarity metric |

M0 remains a negative control and cannot be shortlisted. M1, M3, M4,
symmetric/asymmetric M6 variants, and M8 remain comparison baselines that
contextualize the three shortlisted families.

## Hard gate matrix

| Gate | Required condition | Final evidence | Status |
| --- | --- | --- | --- |
| Mechanical expectations | all 15 cases pass; zero failures | `16_MECHANICAL_EXPECTATION_CASES.tsv` | `PASS` |
| Lineage | 64 classified, zero unclassified, zero same-source double score | `03_SIGNAL_LINEAGE_REGISTRY.tsv` and raw receipt | `PASS` |
| Candidate retrieval | CG-CUR-4; minimum recall@20 0.9995809881175735; pool P50 3,008 | `11_CANDIDATE_RECALL_RESULTS.tsv` | `PASS` |
| Missingness | shared-unknown credit zero; separate comparability emitted | missingness raw/TSV receipts | `PASS` |
| Interactions | eight methods/five thresholds; low-support and parent failures zero | `15_INTERACTION_STATISTICS_REVIEW.tsv` | `PASS` |
| Source/curation dominance | source/curation dominated query rates zero; zero independent curation | `07_`, `12_`, and `13_` TSVs | `PASS` |
| Stability | 216 variants measured; nine collapse diagnostics retained | `14_ABLATION_AND_STABILITY.tsv` | `DIAGNOSTIC_CAUTION` |
| Hubness | k=10/20/50 measured; severe diagnostics triggered correction experiments | `13_HUBNESS_ANALYSIS.tsv` | `DIAGNOSTIC_CAUTION` |
| Explanations | 864 sampled explanations; invalid/unexplained/score-only counts zero | explanation/raw receipts | `PASS` |
| Provenance | 47 complete analysis-run receipts; zero receipt failures | `19_ANALYSIS_RUN_REGISTER.tsv` | `PASS` |
| Security/scope | held and UUID exposure zero; no pair matrix, runtime scorer, route, API, or governance change | verifier and changed-file receipt | `PASS` |

## Candidate-architecture decision

The chosen CG-CUR variant is selected by a declared deterministic rule over
exhaustive recall and pool reduction. Candidate retrieval is separate
from model scoring. A curatorial posting can be part of a bounded recall layer
without becoming ranking evidence. A high recall result obtained from a
near-full pool is not described as efficient retrieval.

CG-CUR-4 is selected by
`MINIMUM_P50_POOL_WITH_MINIMUM_SHORTLIST_RECALL_AT_20_GTE_0.98;LINEAGE_SAFE_RESIDUAL_ONLY_TIE_BREAK`.
It yields pool P50/P95/P99/MAX 3,008/3,662/5,644/5,991, with zero empty or
near-full pools. Minimum recall@10/20/50 is
0.9998499061913696/0.9995809881175735/0.9974158849280801. Candidate retrieval
remains independent of scoring, and CG-CUR-4 curatorial reasons remain
`scoringAllowed=false`.

## Model-by-model disposition

The sealed document gives every M0–M8 family one explicit disposition and
evidence-backed reason.

| Model | Final disposition | Evidence-backed reason |
| --- | --- | --- |
| M0 | `NEGATIVE_CONTROL_ONLY` | fixed: raw curated Jaccard is import-isolated and shortlist-ineligible |
| M1 | `COMPARISON_BASELINE` | transparent equal-family control; not retained as a shortlist architecture |
| M2 | `SHORTLISTED_TASK_A` | smoothed IDF, family normalization, exhaustive recall, mechanical, and explanation gates pass; geography ablation remains sensitive |
| M3 | `COMPARISON_BASELINE` | approved-feature weighted-Jaccard sensitivity control; not assumed repaired merely by IDF |
| M4 | `COMPARISON_BASELINE` | bounded rarity experiment; three temporal-decay ablations fall below 0.50 mean top-20 overlap |
| M5 | `SHORTLISTED_TASK_A` | family-balanced mixed profile and TEMP-4 interval treatment pass gates; geography ablation remains sensitive |
| M6 | `COMPARISON_BASELINE` | retains explicit symmetric/asymmetric contrast evidence; not added beyond the three-architecture cap |
| M7 | `SHORTLISTED_TASK_B` | explicit fielded query retrieval with validated formula provenance; time ablation and hubness require human review |
| M8 | `COMPARISON_BASELINE` | retains non-scalar Pareto evidence without an undocumented universal scalar |

## Why no provisional internal profile is selected

The benchmark deliberately retains instability and hubness evidence. At k=20,
M2 geography removal has mean top-k overlap 0.4659722222222222, M5 geography
removal has 0.4708333333333333, and M7 time removal has
0.43819444444444444. Across all candidate models, nine of 216 ablation variants
fall below the declared 0.50 collapse threshold.

At k=20, the worst shortlist Gini is 0.7446896993547796, top-1% occurrence
share is 0.26864915572232645, and maximum occurrence is 1,653. All three
shortlist families triggered analysis-only correction experiments. Corrections
were not selected because they add explanation complexity and materially alter
rankings; no one transformation closes every trade-off. Source- and
curation-dominated query rates are zero, and P95 maximum-family contribution
share is 0.4, but those positives do not erase the retained stability and
hubness cautions.

## Human-review boundary

The deterministic blinded packet may be ready while review remains incomplete.
Packet generation cannot fabricate researcher judgments and does not validate
historical relation.

```text
HUMAN_REVIEW_PACKET_ANCHOR_COUNT=72
HUMAN_REVIEW_PACKET_READY=true
HUMAN_REVIEW_COMPLETED=false
EXPLORATION_HUMAN_REVIEW_NEXT=true
```

## Non-selection statements

Regardless of the internal research outcome:

```text
PUBLIC_SIMILARITY_MODEL_SELECTED=false
PUBLIC_SIMILARITY_WEIGHTS_SELECTED=false
PROBABILITY_MODEL_SELECTED=false
CLUSTERING_MODEL_SELECTED=false
EXPLORATION_PUBLIC_MODEL_READY=false
```
