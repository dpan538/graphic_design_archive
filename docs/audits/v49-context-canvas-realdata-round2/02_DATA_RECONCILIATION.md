# Data reconciliation

## Frozen-source identities

| Artifact | Role | SHA-256 |
| --- | --- | --- |
| `docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv` | sole public/held eligibility authority | `48f98f68ca2ec0cef96c82ecc9c01e4129eb9a3f91e08b07ad9a59644a9d4e01` |
| `database/FREEZE_V49.json` | frozen count receipt | `f0dda59dd515ba243eaf213bce9f42513727f1ab0a44685635921c3759a7d22e` |
| `data/prefreeze_candidate_v48.sqlite` | immutable selected-record title and typed-folder source | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` |
| `docs/statistics/v49-release-data-profile.json` | release publication/semantic profile | `091dba486c2096f99c332b03cf9586139f1bc26594bce4e1575d2b1ddc8fea0f` |
| `frontend/generated/search-v49/documents.json` | protected public ID/title parity cross-check only | `35a6b7e1f8b749fca0ebfda9cf84f265de58d69fe6ef2bac0a4a2a9d263b1522` |

The Context validation manifest is SHA-256 over newline-separated content: `mapping:trace-context-realdata-v1`, followed by the three frozen-input `path:sha256` entries sorted by path:

```text
VALIDATION_RELEASE_ID=trace-v49-context-validation-round2-v1
VALIDATION_MANIFEST_SHA256=c07de2b6531f5f17cd31f705b6e42443277bf837ce9e13225ae684001da17363
```

The loader calculates and verifies all three registered source-file hashes before parsing. The independent verifier recomputed the same manifest and confirmed the runtime binding.

## Eligibility reconciliation

The read-only source audit established:

```text
CANONICAL_OBJECT_COUNT=15923
PUBLIC_OBJECT_COUNT=7995
HELD_OBJECT_COUNT=7928
PUBLIC_HELD_OVERLAP_COUNT=0
UNCLASSIFIED_OBJECT_COUNT=0
PUBLIC_ID_DUPLICATE_COUNT=0
PUBLIC_SQLITE_TITLE_MISSING_COUNT=0
PUBLIC_SEARCH_ID_MISSING_COUNT=0
HELD_SEARCH_ID_COUNT=0
PUBLIC_SQLITE_SEARCH_TITLE_MISMATCH_COUNT=0
```

Eligibility is derived only from ledger fields `surface_id_exact` and `research_disposition`. The SQLite fields `objects.count_eligible` and `objects.trace_tier` are unsafe public filters:

- all 15,923 SQLite objects have `count_eligible=1`, which would expose all 7,928 held objects;
- 12,952 objects have `trace_tier=source_verified`, including 4,957 held objects.

Held and well-formed unknown identifiers therefore share the same externally visible `RECORD_NOT_AVAILABLE` result.

## Candidate-source reconciliation

| Typed folder category | Public rows | Public objects | Public folder identities | Held rows audited only as an aggregate |
| --- | ---: | ---: | ---: | ---: |
| Medium | 7,995 | 7,995 | 10 | 7,928 |
| Theme | 7,996 | 7,995 | 8 | 7,928 |
| Movement | 115 | 110 | 7 | 96 |
| Region | 7,996 | 7,995 | 93 | 7,928 |
| Total | 24,102 | 7,995 | 118 typed identities across the four public category sets | 23,880 |

Across the full SQLite source there are 47,982 distinct `(surface_id, folder_id)` rows, 185 folder identities, four typed categories, no duplicate source pair, no folder identity with conflicting type/label, and no same-type label mapped to multiple folder identities.

Seven public records have multiple values within one category: five movement cases, one theme case, and one region case.

## Projection reconciliation

| Projection class | Instances | Object coverage | State |
| --- | ---: | ---: | --- |
| Controlled-assignment candidates: medium/theme/movement | 16,106 | 7,995 / 7,995 | proposed |
| Curated memberships: medium/theme/movement/region | 24,102 | 7,995 / 7,995 | proposed |
| Combined Context associations | 40,208 | 7,995 / 7,995 | proposed |
| Real semantic edges | 0 | 0 | absent |

The controlled and curated categories deliberately project medium/theme/movement source rows into two distinct semantic classes. Region is curated-only. This reproduces the prior census workload:

```text
CONTEXT_ASSOCIATIONS_MIN=5
CONTEXT_ASSOCIATIONS_P50=5
CONTEXT_ASSOCIATIONS_P95=5
CONTEXT_ASSOCIATIONS_P99=7
CONTEXT_ASSOCIATIONS_MAX=9
```

Raw `objects.medium`, creator, collection/source context, object type, arbitrary metadata, URLs, and internal UUIDs are not projected as connected entities.

## Label and pathological-sample reconciliation

The audited projected label occurrence count is 48,203: 7,995 public object titles, 16,106 controlled-assignment label occurrences, and 24,102 curated-membership label occurrences.

```text
LABEL_P50_LENGTH=14
LABEL_P95_LENGTH=46
LABEL_P99_LENGTH=103
LABEL_MAX_LENGTH=806
DISPLAY_TRUNCATION_REQUIRED_COUNT=23024
EMPTY_LABEL_COUNT=0
PATHOLOGICAL_SAMPLE_COUNT=26
```

The committed pathological register contains 26 unique eligible public stable IDs and public titles with measurable reasons and numeric shape fields. The final two rows are the lexicographically deterministic public `"CATALOG"` same-label/different-identity pair. The register contains no held ID, internal UUID, URL, or raw candidate label.

## Runtime closure

Two exhaustive passes closed the Canvas execution gates:

```text
PUBLIC_OBJECTS_VALIDATED=7995
HELD_LOOKUPS_TESTED=7928
HELD_OBJECTS_EXPOSED=0
DATASET_FAILURE_COUNT=0
ENTITY_ID_COLLISION_COUNT=0
CONNECTION_ID_COLLISION_COUNT=0
DANGLING_CONNECTION_COUNT=0
AUTO_LAYOUT_COLLISION_COUNT=0
ACCESSIBLE_ROW_MISMATCH_COUNT=0
EXPORT_PREPARATION_FAILURE_COUNT=0
PERSISTENCE_KEY_COLLISION_COUNT=0
DETERMINISM_FAILURE_COUNT=0
REAL_CONTEXT_REBUILD_DETERMINISTIC=true
REAL_CONTEXT_CHECKSUM_MATCH=true
```
