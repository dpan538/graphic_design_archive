# Missingness and uncertainty taxonomy

## Decision

Missingness is not reduced to SQL null. The analysis freezes ten supported classes and one orthogonal multi-region flag. No single uncertainty score is created.

| Class | Meaning | Generic missing? |
| --- | --- | --- |
| `OBSERVED` | A governed or explicitly classified value is present. | no |
| `UNKNOWN_SOURCE_VALUE` | The public source explicitly says unknown. | no |
| `QUALIFIED_UNKNOWN_SOURCE_VALUE` | Unknown is retained with a bounded role qualifier. | no |
| `NO_PUBLISHED_MOVEMENT_CONTEXT` | No governed movement-context representation is published. | no |
| `APPROXIMATE` | Governed temporal precision is approximate. | no |
| `RANGE` | Governed temporal observation is an inclusive range. | no |
| `AGGREGATE_ONLY` | Geography remains countable without a map point. | no |
| `UNMAPPED` | Governed geography has no selected geometry mapping. | no |
| `QUALIFIED` | A governed value carries an explicit qualification. | no |
| `NOT_GOVERNED` | A source diagnostic exists but is not a governed public feature. | no |

`MULTI_REGION` is an orthogonal flag, not a missingness class.

## Field matrix

| Field | Authoritative state counts | Boundary |
| --- | --- | --- |
| Medium | observed 7,995 | governed direct feature |
| Theme | observed 7,995 | governed direct feature |
| Movement context | observed 110; no published context 7,885 | absence is not generic missingness |
| Temporal precision | year 7,552; approximate 305; day 78; month 27; range 33 | governed direct feature |
| Geography | mapped 7,800; aggregate-only 194; unmapped 1; qualified 467; multi-region 1 | mapping/qualification states are retained |
| Creator | observed 5,806; explicit unknown 2,027; qualified unknown 162 | public metadata analysis only; null-missing count 0 |
| Source | observed 7,995 | public metadata analysis only |
| Object type | observed 7,995 | public metadata analysis only |
| Source collection | present 7,980; absent 15 | internal diagnostic, `NOT_GOVERNED`; missing count 0 |

Rights/delivery and image state are deferred because no governed public aggregate class exists. The analysis does not guess a class from raw values.

## Object-level vector

The analysis constructs 7,995 public-only vectors, totaling 11,075 active state events with at most four active states per object. The vector digest is `da439396aa1782ee616929ca70d451d822fe748dac5e8f622e342286ed644603`. Vectors are temporary analysis material: zero vector rows and zero public or held IDs are committed.

## Co-occurrence

Nineteen observed uncertainty/state intersections are committed in `06_MISSINGNESS_CENSUS.tsv`, each with an eligible denominator of 7,995. Examples include approximate time with no published movement context, aggregate-only geography with explicit unknown creator, and qualified geography with no published movement context. These are observed intersections only; they do not explain why states co-occur and are not causal signals.

## Invariants

```text
GENERIC_MOVEMENT_MISSING_COUNT=0
CREATOR_NULL_MISSING_COUNT=0
HELD_OBJECTS_INCLUDED=0
SINGLE_UNCERTAINTY_SCORE=false
HISTORICAL_RELATION=false
SEMANTIC_RELATION=false
```
