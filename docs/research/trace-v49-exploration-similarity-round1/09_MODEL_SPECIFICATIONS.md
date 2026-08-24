# Model specifications

## Research boundary

M0 through M8 are transparent analysis families, not public products. They use
the eight independent base signals organized into eight basis units across five
families, plus an optional separately residualized interaction layer. The
current independent curatorial residual count is zero.

This specification defines the benchmark search space. It does not assert an
empirical winner, shortlist, final weights, final diagnostic score, or
provisional model. Model selection remains an output of the evaluation and
round-decision artifacts.

## Common output contract

Every pair model emits an affinity profile containing public query/candidate
IDs, model and variant IDs, symmetry declaration, per-family scores, jointly
observable and unavailable families, a separate comparability profile,
interaction and base contributions, distinctive features, ignored lineage
duplicates, and an optional diagnostic scalar or Pareto vector.

Every result fixes:

```text
historicalRelation=false
semanticRelation=false
probability=false
randomnessAffectsAffinity=false
```

Contributions expose numerator and denominator, or explicit source identity
where applicable. Scalar ties resolve by descending diagnostic value and then
ascending public candidate ID. No scalar is described as likelihood or
probability.

## Model family suite

| ID | Analysis family | Task and symmetry | Core calculation | Eligibility and principal failure test |
| --- | --- | --- | --- | --- |
| `M0` | raw curated Jaccard negative control | structural diagnostic only; symmetric | intersection over union of raw curated memberships | never shortlist/public/runtime eligible; reproduces broad-curation saturation |
| `M1` | unweighted family overlap | Task A; symmetric | per-field set overlap followed by equal family aggregation | transparent baseline; must not count tokens or duplicate fields as extra families |
| `M2` | IDF-weighted sparse cosine | Task A; symmetric | cosine on family-qualified approved tokens, normalized within each family before family aggregation | test global, within-family, and smoothed IDF; high-cardinality dominance and hubness are failure risks |
| `M3` | IDF-weighted Jaccard/Tanimoto | Task A; symmetric | weighted approved-feature intersection over weighted union | distinct from M0; weighting may still suffer broad/common-feature or set-size effects |
| `M4` | Goodall-style rarity-aware categorical similarity | Task A; symmetric | bounded rarity value for observed categorical matches, aggregated by family | support floors and contribution caps are mandatory; support 1–2 cannot dominate |
| `M5` | Gower-style family-balanced mixed similarity | Task A; symmetric | one bounded contribution per eligible family with explicit availability masks and transparent temporal treatment | test family availability, temporal sensitivity, and geography boundary; no coordinate distance |
| `M6` | Tversky feature contrast | Task A when alpha=beta; Task B when declared asymmetric | common approved features relative to query-only and candidate-only features | symmetry declaration must agree with parameters; no tuning against invented labels |
| `M7` | BM25F-like fielded retrieval | Task B; explicitly asymmetric | selected object/filter as query over family-qualified fields with IDF, field normalization, and declared field weights | query/document roles exposed; not a universal symmetric similarity or probabilistic relation model |
| `M8` | non-scalar multi-channel/Pareto profile | Task A research baseline; family scores symmetric | nondominated fronts or distinct strong family profiles without a total score | candidate-set size and explanation clarity evaluated; must not hide a scalar collapse |

M0 lives in the isolated analysis-only `negative_control.py`. M1–M8 live in the
scoring-eligible analysis module, which does not import M0. Future production,
frontend, candidate-generator, explanation-runtime, and public scorer roots may
not import raw curated Jaccard.

## Approved base families

The default symmetric scoring set is Context, Temporal, Geography, and
Descriptive. Source is governed by SOURCE-0 through SOURCE-4 and is excluded
from the default baseline. A Curatorial Residual family could enter only after
a new lineage review; its Round 6 signal count is zero.

- Context combines governed medium, theme, and published movement context
  under one family cap.
- Temporal contributes once from governed extent using one declared TEMP
  function.
- Geography scores exact governed assignment overlap only. Deterministic
  geography class is a candidate/explanation fallback and adds zero score.
- Source contributes only through an explicit SOURCE experiment and cap.
- Descriptive combines observed creator and object type without treating
  unknown creator values as matches.

Temporal decade is a retrieval alias or a TEMP-1 representation, not an extra
contribution beside temporal extent. Mapping/precision/missingness states belong
to comparability or explanation.

## IDF configurations

M2 and weighted methods benchmark three declared configurations:

- `GLOBAL_IDF`: document frequency against the full public cohort;
- `WITHIN_FAMILY_IDF`: document frequency against records with that family;
  and
- `SMOOTHED_IDF`: additive smoothing with all constants in the parameter
  receipt.

Feature IDs are family/field-qualified. Family normalization occurs after
within-family scoring so a multivalued or high-cardinality family does not gain
weight merely through token count.

## Family normalization configurations

Every scalar model declares one of:

- `EQUAL_FAMILY`;
- `AVAILABILITY_NORMALIZED`;
- `USER_SELECTED`; or
- `CAPPED_FAMILY`.

User-selected weights must be explicit query parameters. They are not learned,
not historical importance, and not selected because a visualization looks
balanced. Missingness behavior is still declared separately.

## Missingness configurations

- `MISSING-A`: available-family renormalization;
- `MISSING-B`: conservative full-eligible-family lower bound;
- `MISSING-C`: observed affinity and comparability as two channels; and
- `MISSING-D`: separate uncertainty-state exploration with zero positive base
  credit.

Every model emits comparability regardless of variant. Shared unknown,
qualified-unknown, no-published-movement, and not-governed states add zero
default affinity.

## Temporal configurations

| ID | Function | Constraint |
| --- | --- | --- |
| `TEMP-1` | overlap of governed decade memberships | decade is not also counted as an independent extent fact |
| `TEMP-2` | bounded same/adjacent-decade similarity | adjacency window is declared and sensitivity-tested |
| `TEMP-3` | bounded distance decay over governed extents | bandwidth is declared and sensitivity-tested; no learned value |
| `TEMP-4` | inclusive interval overlap | precision and range/approximate state are preserved |

Approximate and range observations are not exact points. No temporal bandwidth
is selected by this document.

## Geography boundary

Permitted scoring uses exact governed geography assignment overlap. A reviewed
explicit multi-geography concept may supply exact governed assignments.
`SIG-GEOGRAPHY-CLASS` is deterministically derived from assignment and may be
used only for candidate generation or explanation, with zero additive scoring
credit. Mapping state is diagnostic. Projected layout distance, map/screen
coordinates, centroid distance as historical distance, ungoverned border
adjacency, and an invented hierarchy contribute zero.

## Source configurations

| ID | Treatment |
| --- | --- |
| `SOURCE-0` | exclude source from affinity and retain it for explanation/bias analysis |
| `SOURCE-1` | include same source as one capped family contribution |
| `SOURCE-2` | same source adds zero but may be reported |
| `SOURCE-3` | prefer cross-source results only for the explicitly contrastive Task C |
| `SOURCE-4` | diversify by source after ranking without changing pair scores |

Each experiment reports top-1 source share, result HHI, cross-source rate, and
comparison with corpus composition. Same source is never automatically
positive.

## Curatorial attenuation configurations

Curatorial membership is recall and diagnostic substrate in this corpus, not an
independent scoring family. CUR-W variants remain necessary to test candidate
fanout and any future residual policy:

- `CUR-W1`: smoothed IDF-like weight `log((N+alpha)/(df+alpha))`;
- `CUR-W2`: within-container-type IDF;
- `CUR-W3`: broad-container stops at support above 25%, 50%, 75%, or 90%;
- `CUR-W4`: capped maximum curatorial-family contribution;
- `CUR-W5`: bounded rare-and-broad weighting so both extremes have limited
  influence; and
- `CUR-W6`: residual-only curation after lineage deduplication.

Because `CURATORIAL_RESIDUAL_SIGNAL_COUNT=0`, CUR-W4 and any scoring aspect of
CUR-W5 have no independent input in the current basis. Raw-curation M0 remains
diagnostic only. Attenuation effects are reported for fanout, top-k stability,
hubness, source concentration, family dominance, and explanation clarity.

## Goodall support policy

M4 benchmarks support floors 2, 3, 5, 10, and 20 and a declared maximum match
contribution. Values below the floor are shrunk rather than allowed to approach
an unbounded rarity bonus. `rare` means low support, not quality, importance,
or historical significance.

## Tversky parameter grid

The declared non-learned grid includes `(alpha,beta)` values `(0.5,0.5)`,
`(1.0,1.0)`, `(0.8,0.2)`, and `(0.6,0.4)`. Equal parameters are symmetric Task
A variants. Unequal parameters are explicitly asymmetric Task B variants. The
grid is a sensitivity experiment, not a learned optimum.

## BM25F-like retrieval contract

M7 treats the selected object or filter set as a query and candidates as
documents. Each field exposes IDF, query-side matched terms, document-length
normalization, and declared field weight. The analysis parameters include
`k1`, `b`, eligible fields, and user weights. The method name describes a
fielded retrieval adaptation; it does not claim a calibrated relevance
probability or historical relation.

## Interaction statistics and residualization

The interaction diagnostics benchmark eight reported statistics:

- `RAW_SUPPORT`;
- `CONDITIONAL_SUPPORT`;
- `LIFT`;
- `PMI`;
- `NORMALIZED_PMI`;
- `LOG_LIKELIHOOD_RATIO`;
- `SMOOTHED_LIFT`; and
- `SHRUNK_NORMALIZED_PMI`.

Support thresholds are 2, 3, 5, 10, and 20. Raw lift and PMI are diagnostics
because of low-support inflation. Optional scoring uses exactly one declared
residual policy:

- `NO_INTERACTION_CONTRIBUTION`;
- `CAPPED_INTERACTION_BONUS`;
- `INFORMATION_RESIDUAL_CONTRIBUTION`; or
- `LOG_LIKELIHOOD_INTERACTION_CONTRIBUTION`.

Every residual row identifies parent signals, support, threshold, method, cap,
and `parentContributionRepeated=false`. The total interaction layer is capped
separately from base families. An interaction cannot repeat medium, theme,
decade, or other parent evidence.

## Determinism, performance, and selection

M1–M7 scalar exhaustive evaluation streams unordered pairs and retains bounded
top-k heaps only. M8 is evaluated as deterministic Pareto layers. Candidate
generation and scoring are separate, the selected object is excluded, duplicate
titles remain different identities, and no seed affects membership or rank.

Benchmarks must report candidate recall, stability, ablation, hubness, source
and family dominance, missingness behavior, explanation completeness, runtime,
and memory. This specification deliberately leaves every shortlist and final
decision field unset. It cannot authorize a public score, weights, relation,
probability, clustering model, route, API, renderer, or template registry.
