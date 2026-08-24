# Evaluation protocol

## Purpose

This protocol precedes model selection. The archive has no accepted labels for
historical relation, influence, contact, or causation, so those concepts cannot
serve as ground truth. Evaluation asks whether a transparent Exploration method
obeys explicit mechanical rules, retrieves its own exhaustive structured
reference results efficiently, remains stable on real archive data, avoids
pathological hubs and corpus-composition dominance, and produces explanations
that researchers can review.

Agreement with an invented relation label, classification accuracy against
fabricated examples, and visual plausibility are prohibited selection criteria.
No single metric declares a public model correct.

## Frozen evaluation population

| Item | Contract |
| --- | --- |
| Source commit | `0e311f0b88b4adc3cbfe2080ac98d622013cc6d3` |
| Public cohort | 7,995 public surface IDs |
| Held objects in evaluation | 0 |
| Complete unordered public pair count | 31,956,015 |
| Full pair matrix committed | false |
| Internal UUIDs in outputs | 0 |
| Randomness affecting candidates or scores | false |

All runs are pinned to source, research release, Context projection, Spacetime
projection, the Exploration signal registry, and candidate-index hashes. A
timestamp is metadata outside deterministic hash material. Input order must not
change rankings or receipts.

## 1. Mechanical expectation suite

The 15 deterministic cases are project-rule expectations, not historical
ground truth. Every shortlisted model must pass every applicable case.

| ID | Required expectation |
| --- | --- |
| `AX-001` | Several independent governed matches outrank one extremely broad curatorial-only match. |
| `AX-002` | Adding an alias or duplicate derivation of one source fact changes neither family contribution nor score. |
| `AX-003` | Shared unknown, missing, or not-governed states add zero default affinity. |
| `AX-004` | Adding an independent high-information match does not reduce affinity under the same availability state. |
| `AX-005` | Adding an unrelated broad feature causes no material score increase. |
| `AX-006` | Same source alone cannot overwhelm Context/Spacetime evidence. |
| `AX-007` | Support-1 or support-2 observations cannot produce an unbounded rarity or interaction contribution. |
| `AX-008` | Every Task A scalar/profile declared symmetric is symmetric under pair reversal. |
| `AX-009` | Task B asymmetry is declared in the model specification and exactly reproducible. |
| `AX-010` | Removing an unavailable family changes comparability and cannot silently strengthen the evidence profile. |
| `AX-011` | The query object never appears in its candidate list or ranking. |
| `AX-012` | Equal titles do not collapse distinct public object identities. |
| `AX-013` | Map, centroid, projected-layout, or screen-coordinate distance contributes exactly zero. |
| `AX-014` | Broad source/container universal hubs are measured and surfaced as failures rather than hidden. |
| `AX-015` | Seed values change neither candidate membership, affinity contribution, comparability, nor rank. |

The regression artifact records fixtures, expected ordering or equality,
observed behavior, applicability, and pass/fail status. A failure blocks the
affected model from the shortlist; it is not waived by better aggregate
metrics.

## 2. Exhaustive offline reference rankings

For analysis only, each scalar benchmark may stream all 31,956,015 unordered
pairs. The implementation must:

1. use the same pure scoring path used by object-local evaluation;
2. visit unordered pairs without storing pair rows;
3. retain only bounded top-k heaps per object;
4. use descending diagnostic value and ascending public candidate ID as the
   stable tie-break;
5. retain bounded aggregate distributions and hashes; and
6. discard transient pair values.

M8 is non-scalar. Its Pareto fronts are evaluated object-locally and must not
be collapsed to an undocumented scalar merely to fit the exhaustive heap
protocol.

## 3. Candidate-generator recall and reduction

Evaluate CG-CUR-1 through CG-CUR-6 independently of scoring. For every
shortlisted scalar model, compare each object's candidate set with that model's
exhaustive top-k ranking and report macro and micro recall at 10, 20, and 50.

Also report candidate-pool P50, P90, P95, P99, maximum, reduction relative to
7,994 possible other objects, zero-candidate object count, and near-full-corpus
candidate count. Performance evidence includes index build time, serialized
bytes, heap, object-local P50/P95 query time, and candidate-generation runtime.

The provisional shortlist target is recall@20 at least 0.98 with a materially
reduced pool. Missing the target is reported as a trade-off; the reference
ranking or denominator must not be weakened to manufacture a pass.

## 4. Real-data stability and sensitivity

Each scalar model and declared parameter variant is run over the same frozen
public cohort. Required stability views include top-k overlap and rank
correlation under:

- repeated deterministic execution;
- global, within-family, and smoothed IDF variants where applicable;
- equal, availability-normalized, user-selected, and capped family
  normalization;
- TEMP-1 through TEMP-4 and the declared temporal-decay grid;
- SOURCE-0 through SOURCE-4;
- CUR-W1 through CUR-W6 and broad-container thresholds at 25%, 50%, 75%, and
  90%; and
- interaction support thresholds 2, 3, 5, 10, and 20.

Sensitivity does not select the threshold that merely looks balanced. Results
must expose the parameter set and retain alternative outcomes.

## 5. Ablation suite

For every candidate model, measure top-k overlap and rank correlation after
leaving out each of:

- Context;
- Time;
- Geography;
- Source;
- Curation;
- missingness diagnostics; and
- interactions.

Also evaluate removal of the largest curated container, removal of the dominant
source, changes to broad-container and rare-support thresholds, changes to
temporal decay, and changes to family normalization. A ranking that collapses
when one broad source or container is removed is unstable, even if its overall
score distribution appears smooth.

## 6. Hubness protocol

For each scalar model and shortlist variant, construct k-occurrence counts at
`k=10`, `k=20`, and `k=50`. Report mean, variance, skewness, Gini coefficient,
top-1% occurrence share, maximum occurrence, and zero-occurrence object count.

Test associations with dominant source, broad curated membership, common
medium/theme, metadata observability, geography, and decade. High hubness is a
failure signal requiring explanation; it is not automatically disqualifying.

Only a model showing severe hubness proceeds to analysis-only correction tests:
local scaling, mutual-proximity/global-scaling style transformation, and
reciprocal-neighbor filtering. Report hub reduction, top-k stability,
explanation complexity, symmetry, candidate recall, and source bias. A
correction is not selected merely because one hub statistic improves.

## 7. Source, curation, and family-dominance diagnostics

For every model/result family, report:

- top-1 source share, result-set source HHI, and cross-source rate relative to
  corpus composition;
- median and P95 maximum-family contribution share;
- share of queries with one family above 80%;
- source-dominated query rate; and
- curation-dominated query rate.

CUR-W1 through CUR-W6 must additionally report fanout, top-k stability,
hubness, source concentration, family dominance, and explanation clarity. Raw
curation is a recall or diagnostic substrate, not a scoring family in the
current zero-residual basis.

## 8. Missingness and interaction checks

Benchmark MISSING-A through MISSING-D. Every result exposes affinity among
observed families and a separate comparability profile. Shared unknown states
must produce zero positive credit. Removing an unavailable family must remain
visible in the eligible denominator or comparability ratio.

Interaction experiments cover raw support, conditional support, lift, PMI,
normalized PMI, log-likelihood ratio, and smoothed/shrunk variants at support
thresholds 2, 3, 5, 10, and 20. Raw PMI and lift are diagnostics. Optional
interaction scoring is separately residualized and capped; parent feature
contributions are never repeated. Report low-support inflation and parent
double-count failure counts.

## 9. Explanation validation

No score-only result is eligible. Each sampled and shortlisted result must show
retrieval reasons, independent family contributions with numerator/denominator
or source identity, distinctive signals, ignored duplicate derivations,
unavailable families, comparability, attenuation and source-bias notes,
interaction evidence, method/version, and pinned hashes.

Validation rejects unexplained results, non-public identifiers, missing
provenance, probability language, relation flags not fixed to false, or any
contribution not resolvable to the lineage registry.

## 10. Blinded human-review packet

Generate approximately 60–80 deterministic public anchors. Include the 15
existing pathological cases and stratify the remainder across common/rare
Context, common/rare geography, multiple decades, dominant/rare sources,
broad/narrow curation, missingness states, multi-region records, and movement
context.

For every shortlisted model, provide three to five bounded candidates per
anchor. Blind model identity where practical. Include public ID/title, shared
and distinctive signals, comparability, source composition, and explanations,
but omit diagnostic score labels that could bias review.

The packet contains blank fields for usefulness, intelligibility, broad-category
dependence, new defensible research direction, accidental relation suggestion,
and reviewer notes. The generator must leave:

```text
HUMAN_REVIEW_PACKET_READY=true
HUMAN_REVIEW_COMPLETED=false
```

No human judgment may be fabricated. Packet readiness is not human approval.

## Decision gate

After all evidence is generated, the round may issue exactly one of:

- `NO_MODEL_SELECTED`;
- `MODEL_FAMILY_SHORTLISTED`; or
- `PROVISIONAL_INTERNAL_AFFINITY_PROFILE_SELECTED`.

At most three architectures may be shortlisted. A provisional internal profile
requires all applicable mechanical axioms to pass, acceptable candidate recall,
zero lineage double counting, explicit missingness/comparability behavior,
measured hubness, bounded source and curation dominance, stable explanations,
documented ablations, and no historical-relation implication.

This protocol does not itself choose a decision. A public model, public weights,
probability model, clustering model, route, API, renderer, and final template
registry remain unselected and unauthorized.
