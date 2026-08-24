# Missingness and comparability

## Governing rule

Affinity among observed features and the amount of jointly observable evidence
are different quantities. They must be emitted as separate channels. A pair
with two jointly observable families and a pair with five jointly observable
families must not appear equally evidential merely because their observed-only
affinity values are equal.

The term `comparability` is used deliberately. It is not `confidence`, a
probability, validation of a historical relation, or a hidden score penalty.

## Family availability

Each model declares a non-empty, unique set of eligible families. The available
research families are Context, Temporal, Geography, Source, Descriptive, and an
optional lineage-approved Curatorial Residual family. SOURCE treatment can
exclude Source from an individual model's eligible set. The current independent
basis has no curatorial residual signal.

A family is available for one record only when it has approved observed data:

- Context: at least one observed governed medium, theme, or published movement
  context value;
- Temporal: valid governed start/end extent plus a non-unknown precision;
- Geography: at least one governed geography value;
- Source: an observed approved source identity;
- Descriptive: an observed approved object type or non-unknown creator
  attribution; and
- Curatorial Residual: at least one lineage-approved residual membership.

Pairwise joint observability requires availability on both records. One-sided
availability is not a mismatch score and two-sided absence is not a match.

## Comparability profile

For declared eligible family set `E`, let `J` be the subset jointly observable
for both records. Emit:

```text
observedFamilyCount = |J|
eligibleFamilyCount = |E|
ratio = |J| / |E|
jointlyObservableFamilies = sorted(J)
unavailableFamilies = E - J
```

The eligible set and its ordering belong to the model specification. A result
must expose both lists as well as the counts and ratio. Affinity aggregation may
refer to those denominators under a declared missingness variant, but it cannot
erase or rename the comparability profile.

## Missingness variants

All four variants are benchmark inputs; this document does not select one.

| ID | Affinity treatment | Required separate output |
| --- | --- | --- |
| `MISSING-A` | Pairwise deletion with available-family renormalization. Only observed family scores contribute to the numerator and observed-family denominator. | Full comparability profile remains visible. |
| `MISSING-B` | Conservative lower-bound aggregation. Unavailable families contribute no positive evidence while the full eligible-family denominator remains visible. | Full comparability profile and both observed and eligible denominators. |
| `MISSING-C` | Two-channel model: affinity among observed families plus comparability. | Affinity and comparability are peers; neither is silently collapsed into the other. |
| `MISSING-D` | Explicit uncertainty-state exploration channel. Matching states may be reported for a dedicated missingness mode. | `positiveAffinityCredit=0` and the ordinary comparability profile. |

MISSING-A and MISSING-C may share an observed-family aggregation formula, but
their contract differs: MISSING-C explicitly treats comparability as a
co-equal result channel. Neither permits the displayed affinity to stand alone.

## Unknown and uncertainty states

The following states never create default positive affinity:

- `UNKNOWN_SOURCE_VALUE`;
- `QUALIFIED_UNKNOWN_SOURCE_VALUE`;
- `NO_PUBLISHED_MOVEMENT_CONTEXT`;
- `NOT_GOVERNED`;
- blank or not-available values; and
- mapped/aggregate-only/unmapped geography states when used as availability
  diagnostics rather than governed geography values.

Matching states may be useful only in a dedicated missingness-oriented
Exploration mode. The uncertainty comparison reports matching fields and
shared unknown fields while hard-coding `positiveAffinityCredit=0`.

The current state-vector contract records:

- movement-context availability;
- temporal uncertainty or precision state;
- geography mapping state;
- geography qualification state;
- creator attribution state;
- source availability; and
- object-type availability.

These states are diagnostics and explanation data. They are not
family-qualified score tokens.

## Temporal uncertainty

Day, month, year, range, and approximate precision are preserved. Temporal
models operate on the governed extent and declare TEMP-1 through TEMP-4. A
range is not converted to an exact midpoint. Approximate observations may be
expanded only through a declared transparent rule and sensitivity analysis.
Precision qualifies temporal interpretation and comparability; equal precision
labels are not an additional temporal match.

## Geography uncertainty

Exact governed geography assignment may create a geography-family
contribution. `SIG-GEOGRAPHY-CLASS` is a deterministic derivation of that
assignment and remains candidate-generation or explanation fallback only; its
additive affinity credit is zero. Mapping state, qualification, and multi-region
state describe the observation and may affect availability or explanation;
equality of those states is not positive geography affinity.

Map centroid, projected screen position, object coordinate distance, border
adjacency, and invented hierarchy contribute zero. A future distance policy
would require separate governance and is outside this round.

## Interaction with family aggregation

Every family score is bounded to `[0,1]` before aggregation and every family
contribution carries its own numerator/denominator or source identity. Family
weights are declared parameters. Missing families contribute no numerator.
Under MISSING-B they remain represented in the eligible denominator; under the
other variants their absence remains visible in the separate comparability
profile.

High-cardinality fields cannot manufacture greater comparability through token
count: the unit is the eligible family. Curatorial recall postings and
candidate-generation interactions do not make a family jointly observable for
scoring.

## Required result shape

Every scalar or non-scalar candidate profile must contain:

```text
familyScores
jointlyObservableFamilies
unavailableFamilies
comparability.observedFamilyCount
comparability.eligibleFamilyCount
comparability.ratio
interactions
diagnosticScore (optional)
historicalRelation=false
semanticRelation=false
probability=false
```

An explanation additionally identifies unavailable signals, ignored duplicate
derivations, method/version, and run provenance. `diagnosticScore` is not a
probability and must not be presented without the family and comparability
profiles.

## Validation gates

The mechanical suite must prove:

- shared unknown positive credit count is zero;
- not-applicable states are not silently recoded as missing;
- removal of an unavailable family changes comparability rather than
  strengthening evidence invisibly;
- changing record order does not change the profile;
- symmetric model comparability is symmetric;
- no missingness signal appears in the base affinity numerator; and
- held records and internal identifiers never enter the comparison cohort.

Distributional evaluation reports comparability P50, P95, minimum, and maximum
over the declared cohort. These observations are benchmark outputs and are not
invented in this static contract.
