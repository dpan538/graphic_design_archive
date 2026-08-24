# Independent signal basis

## Deterministic lineage result

The sealed Round 5 registry contains 64 signals. The explicit Round 6 lineage
table classifies all 64 and leaves none unclassified:

| Disposition | Count |
| --- | ---: |
| `INDEPENDENT_BASE_SIGNAL` | 8 |
| `DEPENDENT_INTERACTION_SIGNAL` | 2 |
| `CANDIDATE_GENERATION_ONLY` | 9 |
| `COMPARABILITY_ONLY` | 8 |
| `EXPLANATION_ONLY` | 9 |
| `DIAGNOSTIC_ONLY` | 19 |
| `REJECT` | 9 |
| **Total** | **64** |

The 64 records resolve into 28 `same_source_fact_group` values. Ten signals
are scoring-allowed: the eight independent base signals and two separately
residualized interaction carriers. No source-fact group has more than one base
scoring contribution, so `SAME_SOURCE_FACT_DOUBLE_SCORE_COUNT=0`.

The authoritative row-level reasons and parent links are in
`03_SIGNAL_LINEAGE_REGISTRY.tsv`. This document records the resulting basis;
it does not replace that registry.

## Smallest defensible basis

Eight independent signals form eight basis units across five active affinity
families. Each unit contains exactly one independent source fact. Governed
geography class is a deterministic derivation of governed geography assignment,
so it remains a candidate-generation or explanation fallback with zero
additive scoring credit.

| Basis unit | Family | Primary signal(s) | Positive evidence | Non-duplication rule |
| --- | --- | --- | --- | --- |
| `BASIS-CONTEXT-MEDIUM` | `GOVERNED_CONTEXT` | `SIG-CONTEXT-MEDIUM` | observed shared governed values | one medium contribution |
| `BASIS-CONTEXT-THEME` | `GOVERNED_CONTEXT` | `SIG-CONTEXT-THEME` | observed shared governed values | one theme contribution |
| `BASIS-CONTEXT-MOVEMENT` | `GOVERNED_CONTEXT` | `SIG-CONTEXT-MOVEMENT` | both observed and sharing a published governed value | absent movement context is unavailable, not a match |
| `BASIS-TEMPORAL-OBSERVATION` | `GOVERNED_TEMPORAL` | `SIG-TEMPORAL-EXTENT` | one declared transparent extent function | decade, range span, precision, and same-decade are derivations or qualifiers, not additional base credits |
| `BASIS-GEOGRAPHY-OBSERVATION` | `GOVERNED_GEOGRAPHY` | `SIG-GEOGRAPHY-ASSIGNMENT` | exact governed overlap only | `SIG-GEOGRAPHY-CLASS` is a derived candidate/explanation fallback and adds zero score |
| `BASIS-SOURCE-IDENTITY` | `SOURCE_COMPOSITION` | `SIG-SOURCE-NAME` | only under an explicit SOURCE experiment | default disabled; same source is not automatically positive |
| `BASIS-DESCRIPTIVE-CREATOR` | `DESCRIPTIVE_METADATA` | `SIG-DESCRIPTIVE-CREATOR` | observed non-unknown public attribution equality | unknown and qualified-unknown values add zero |
| `BASIS-DESCRIPTIVE-OBJECT-TYPE` | `DESCRIPTIVE_METADATA` | `SIG-DESCRIPTIVE-OBJECT-TYPE` | observed shared approved public value | remains separate from governed medium |

The five active family names are `GOVERNED_CONTEXT`, `GOVERNED_TEMPORAL`,
`GOVERNED_GEOGRAPHY`, `SOURCE_COMPOSITION`, and `DESCRIPTIVE_METADATA`.
`SOURCE_COMPOSITION` is represented in the research basis but is not enabled
by default. Active means available for a declared experiment, not selected or
automatically positive.

## Why the basis is minimal

- Medium, theme, and movement context are distinct governed Context facts;
  removing one cannot be repaired by adding its same-value or folder-derived
  aliases.
- The inclusive governed temporal extent is the least-derived temporal fact.
  Decades are useful postings and TEMP-1 inputs, but are not an extra base fact
  when extent evidence is already counted.
- Governed geography assignment is the sole independent location fact. All 93
  governed geography IDs deterministically resolve to one governed geography
  class, so `SIG-GEOGRAPHY-CLASS` is retained only for candidate generation or
  explanation and adds zero affinity. Mapping state, qualification, and
  multi-region status belong to comparability or explanation.
- Source identity is independent corpus-composition information, but its
  collection bias requires an explicit SOURCE policy and a family cap.
- Observed creator attribution and object type are approved descriptive facts
  not deterministically recoverable from Context, time, geography, or one
  another.

No extra family is retained simply because a diagnostic was measured in Round
5.

## Candidate postings are not additional score facts

The basis permits direct candidate postings for governed medium, theme,
movement context, temporal decade, governed geography, derived geography
class, approved source, creator, and object type. Temporal decade is a retrieval
alias for the temporal observation rather than an additional temporal
contribution. Geography class likewise retrieves or explains a broader
deterministic fallback and contributes zero affinity beside its assignment
parent.

Four high-information posting candidates remain candidate-generation-only:

- `SIG-CONTEXT-THEME-MOVEMENT`;
- `SIG-DESCRIPTIVE-CREATOR-MEDIUM`;
- `SIG-DESCRIPTIVE-OBJECT-TYPE-MEDIUM`; and
- `SIG-INTERSECTION-MEDIUM-THEME`.

Their parent features already supply base evidence. Retrieval through a
compound posting must not repeat that evidence in the base score.

Two generic observed-cell carriers are dependent interactions:
`SIG-INTERSECTION-PAIR-SUPPORT` and
`SIG-INTERSECTION-BOUNDED-TRIPLE`. They may contribute only through a separate,
support-thresholded, bounded residual layer. Raw support, PMI, lift, or a
parent-value match is not itself an extra base contribution.

## Curatorial result

Lineage deduplication finds no independent residual curatorial signal:

```text
CURATORIAL_AS_RECALL_INDEX=true
CURATORIAL_AS_INDEPENDENT_SCORE=false
CURATORIAL_RESIDUAL_SIGNAL_COUNT=0
```

The three curatorial recall signals are
`SIG-CURATORIAL-MEMBERSHIP`, `SIG-CURATORIAL-SHARED-COUNT`, and
`SIG-CURATORIAL-SUPPORT`. The underlying medium, theme, movement, and region
container memberships are the source facts from which governed
Context/Spacetime projections are built. Re-crediting their raw container
memberships would count the same fact twice.

Curatorial postings remain useful as a recall substrate, provenance, and
structural diagnostic. In the current corpus CG-CUR-5 has no residual
curatorial postings; a future non-empty residual would require a new lineage
decision before scoring could be reconsidered.

Raw curated Jaccard remains the M0 negative control. Its static boundary is:

- production eligible: false;
- shortlist eligible: false;
- runtime scorer import allowed: false;
- candidate-generator import allowed: false; and
- allowed roles: `NEGATIVE_CONTROL` and `STRUCTURAL_DIAGNOSTIC` only.

## Comparability basis

Eight signals are comparability-only:

- `SIG-TEMPORAL-PRECISION`;
- `SIG-GEOGRAPHY-MAPPING-STATE`;
- `SIG-GEOGRAPHY-MULTI-REGION`;
- `SIG-MISSINGNESS-TEMPORAL`;
- `SIG-MISSINGNESS-GEOGRAPHY-MAPPING`;
- `SIG-MISSINGNESS-GEOGRAPHY-QUALIFIED`;
- `SIG-MISSINGNESS-MOVEMENT-AVAILABILITY`; and
- `SIG-MISSINGNESS-CREATOR`.

They describe whether and how families can be compared. They are excluded from
the affinity numerator and emitted in a separate profile containing eligible,
jointly observable, and unavailable families plus observed and eligible family
counts and their ratio. Shared unknown, not-governed, or unavailable states add
zero default affinity. A non-applicable state is preserved as such and is not
silently converted to missingness.

## Family aggregation contract

- Context combines medium, theme, and movement only through an explicitly
  declared mean or capped aggregate, with one Context family cap.
- Temporal emits one extent-derived contribution; precision remains separate.
- Geography scores exact governed assignment overlap only. Deterministic class
  lookup is a candidate/explanation fallback with zero scoring credit.
- Source requires SOURCE-0 through SOURCE-4 treatment; SOURCE-0 exclusion is
  the default baseline.
- Descriptive metadata combines observed creator and object type through an
  explicitly declared mean or cap.

High-cardinality and multi-valued families do not gain weight from token count.
No learned family weights are permitted without a labeled review set.

## Explicit exclusions

The basis gives zero contribution to shared unknown states, map/screen/centroid
distance, ungoverned adjacency, seeded randomness, raw curated overlap, inferred
historical relation, probability, clustering, or embeddings. It preserves
`historicalRelation=false`, `semanticRelation=false`, and `probability=false`
on every result.

These findings define eligible inputs and separation rules. They do not select
a model family, parameter set, weight set, shortlist, or public score.
