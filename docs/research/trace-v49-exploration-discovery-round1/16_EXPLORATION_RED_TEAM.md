# Exploration red-team

## Governing rule

Every Exploration signal reports a deterministic property of the selected archive release. No signal is a historical relation, semantic relation, causal claim, importance/quality judgment, probability, recommendation, or evidence of creator intent. The table enumerates all 20 `HIGH_POTENTIAL` signals; none is covered only by a generic disclaimer.

| Signal | Permitted diagnostic interpretation | Explicitly prohibited interpretation |
| --- | --- | --- |
| `SIG-CONTEXT-MEDIUM` — Medium | Count and filter governed project medium assignments in this release. | Do not infer historical relation, causation, influence, importance, quality, creator intent, or probability from a medium assignment. |
| `SIG-CONTEXT-MEDIUM-THEME` — Medium-theme intersection | Describe observed support where governed medium and theme assignments co-occur. | Do not treat a cell as a historical category, causal pairing, important canon, or probability of relation. |
| `SIG-CONTEXT-SAME-MEDIUM` — Same-medium overlap | Identify candidate pairs sharing at least one governed medium for structural exploration. | Shared medium is not historical contact, influence, equivalence, importance, or likelihood of relation. |
| `SIG-CONTEXT-SAME-THEME` — Same-theme overlap | Identify candidate pairs sharing at least one governed project theme. | Shared theme is not a historical relation, common intent, causal lineage, importance, or calibrated probability. |
| `SIG-CONTEXT-THEME` — Theme | Count and filter governed project theme assignments. | A curatorial theme is not a historical cause, creator intention, quality judgment, canonicality, or probability. |
| `SIG-CURATORIAL-FANOUT` — Co-membership fanout thresholds | Measure how many public neighbors share at least one, two, or three curated containers. | High fanout does not show historical connectedness, influence, importance, representativeness, or high relation probability. |
| `SIG-CURATORIAL-MEMBERSHIP-COUNT` — Membership count per object | Audit project cataloguing density and candidate-query cost per object. | More memberships do not mean more important, higher quality, historically central, influential, or more likely related. |
| `SIG-CURATORIAL-SHARED-COUNT` — Shared-container count | Describe exact project-curated structural overlap for a candidate pair. | Shared containers are not historical relations, causal links, influence, creator intent, importance, or probability. |
| `SIG-CURATORIAL-SUPPORT` — Curated-container support concentration | Measure how broadly or narrowly current public memberships are distributed among containers. | Concentration does not establish historical importance, representative coverage, canonicality, quality, influence, or probability. |
| `SIG-FREQUENCY-ONE-DIMENSION` — One-dimensional frequency | Report observed counts and support rates with explicit denominators. | Frequency is not historical prevalence, importance, quality, representativeness, causation, or relation probability. |
| `SIG-GEOGRAPHY-ASSIGNMENT` — Governed geography | Filter/count the recorded geography context published by Spacetime. | Geography does not assert an object coordinate, historical presence, contact, influence, importance, or probability. |
| `SIG-GEOGRAPHY-SAME` — Same-geography overlap | Identify records sharing a governed geography identifier for exploration. | Shared geography is not historical contact, causal proximity, influence, importance, or likelihood of relation. |
| `SIG-INTERSECTION-MEDIUM-THEME` — Medium-theme observed support | Describe an observed medium-theme cell and its denominator. | Cell support is not a historical relation, recommendation score, importance measure, causal pattern, or probability. |
| `SIG-INTERSECTION-PAIR-SUPPORT` — Observed pair support | Compare bounded observed pair cells within their stated observable cohorts. | Pair support is not probability of relation, historical influence, importance, quality, or evidence of causation. |
| `SIG-INTERSECTION-RARE-MULTI` — Rare multi-dimensional intersection | Flag an observed pair/triple cell with count at most 20 for further research. | Rare does not mean historically absent, important, significant, high quality, causally exceptional, or probably related. |
| `SIG-SOURCE-CONCENTRATION` — Source concentration | Audit top shares, HHI, and entropy for this release and supported subsets. | Concentration is not source authority, truth, historical representativeness, quality, importance, causation, or probability. |
| `SIG-SOURCE-FREQUENCY` — Source frequency | Count public records by normalized source value. | Source frequency is not authority, independence, quality, historical prevalence, importance, or relation probability. |
| `SIG-SOURCE-SHARE` — Source share | Express source count over the authoritative public denominator. | Share does not prove source independence, representative sampling, truth, importance, causal weight, or probability. |
| `SIG-TEMPORAL-DECADE` — Decade | Filter/count governed interval-overlap period assignments. | A decade bucket is not a historical relation, causal era assignment, importance ranking, or probability; ranges may span buckets. |
| `SIG-TEMPORAL-SAME-DECADE` — Same-decade overlap | Identify records whose governed time memberships overlap at least one decade. | Temporal co-occurrence is not contact, influence, causation, importance, equivalence, or probability of relation. |

## Additional adversaries

- `UNKNOWN_SOURCE_VALUE` and `QUALIFIED_UNKNOWN_SOURCE_VALUE` are explicit source semantics, not null missingness.
- `NO_PUBLISHED_MOVEMENT_CONTEXT` does not mean the historical movement context was absent.
- `AGGREGATE_ONLY` and `UNMAPPED` do not mean geographic absence.
- Conditional rates and lift are diagnostics, not calibrated probabilities.
- Map layout coordinates and centroid distance are not historical distance.
- The folder-related graph connects project-curated containers, not objects or historical actors.
- SQLite trace node/edge row counts are structural row counts, not object memberships.
- A known empty public projection is fail-closed evidence, not an unknown schema state.

All 18 Exploration invariants pass. Similarity research may begin only if it preserves these per-signal boundaries and retains explainable denominators.
