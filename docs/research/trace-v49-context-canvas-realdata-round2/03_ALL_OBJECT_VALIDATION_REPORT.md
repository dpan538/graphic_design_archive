# All-Object Validation Report

## Report status

`REPORT_STATUS=PASS`

The isolated verifier processed all 7,995 eligible public objects twice and exercised all four templates for 31,980 object/template cases. All 18 `CTX-REAL-INV` invariants passed and the failure register contains only its header.

```text
PUBLIC_OBJECTS_VALIDATED=7995
PUBLIC_OBJECT_VALIDATION_FAILURE_COUNT=0
HELD_OBJECTS_EXPOSED=0
AUTO_LAYOUT_OBJECT_TEMPLATE_CASES=31980
REAL_CONTEXT_REBUILD_DETERMINISTIC=true
REAL_CONTEXT_CHECKSUM_MATCH=true
REAL_CONTEXT_AGGREGATE_SHA256=499624075b99745c1eb95a8d6c2c1438eb7e74ca63222227b8bfb87fdaf38d76
EXPORT_PREPARATION_SHA256=3c88449337f52ece7be2b8bf282812fb2402b020f72ced7984a9a7c03ab410b9
ISOLATED_EVIDENCE_FILE_COUNT=12
ISOLATED_EVIDENCE_SHA256=9d4a3d1f5a739269a7dc6abfb0711717d75d30dc81ced4b03aa6d2cb63f03ca0
```

## Authoritative reconciliation

| Measure | Result | Status |
| --- | ---: | --- |
| Canonical objects | 15,923 | `PASS` |
| Eligible public objects | 7,995 | `PASS` |
| Held objects | 7,928 | `PASS` |
| Public/held overlap | 0 | `PASS` |
| Unclassified objects | 0 | `PASS` |
| Runtime-verified frozen inputs | 3 | `PASS` |
| Public proposed folder memberships | 24,102 | `PASS` |
| Public controlled-assignment candidates | 16,106 | `PASS` |
| Real semantic relations | 0 | `PASS` |

The source manifest is `c07de2b6531f5f17cd31f705b6e42443277bf837ce9e13225ae684001da17363`, derived from the mapping-version line and the sorted path/hash entries for the freeze receipt, eligibility ledger, and immutable SQLite.

## Reconciled Context workload

| Measure | Result |
| --- | ---: |
| Controlled-assignment object coverage | 7,995 / 7,995 |
| Curated-membership object coverage | 7,995 / 7,995 |
| Controlled assignments | 16,106 |
| Curated memberships | 24,102 |
| Combined association instances | 40,208 |
| Associations minimum | 5 |
| Associations P50 | 5 |
| Associations P95 | 5 |
| Associations P99 | 7 |
| Associations maximum | 9 |

The workload histogram is 7,884 objects with 5 associations, 105 with 7, one with 8, and five with 9.

## Functional failure counters

```text
ENTITY_ID_COLLISION_COUNT=0
CONNECTION_ID_COLLISION_COUNT=0
DANGLING_CONNECTION_COUNT=0
SAME_IDENTITY_CONFLICTING_LABEL_COUNT=0
UNDOCUMENTED_CONNECTION_CATEGORY_COUNT=0
VISIBLE_ENTITY_OUTSIDE_DATASET_COUNT=0
NON_PROPOSED_CANDIDATE_COUNT=0

AUTO_LAYOUT_COLLISION_COUNT=0
NODE_OUTSIDE_COMPUTED_BOUNDS_COUNT=0
NONFINITE_POSITION_COUNT=0
INVALID_CONNECTOR_COUNT=0

ACCESSIBLE_ROW_MISMATCH_COUNT=0
DUPLICATE_ACCESSIBLE_ROW_COUNT=0
SERIALIZATION_FAILURE_COUNT=0
PERSISTENCE_KEY_COLLISION_COUNT=0
PERSISTENCE_KEY_COUNT=7995
RECORD_SWITCH_STATE_LEAK_COUNT=0

EXPORT_SVG_PREPARATION_OBJECT_COUNT=7995
EXPORT_SVG_PREPARATION_TEMPLATE_CASES=31980
EXPORT_PREPARATION_FAILURE_COUNT=0
EXPORT_MISSING_FULL_LABEL_COUNT=0
UNSAFE_FILENAME_COUNT=0
INTERNAL_UUID_CLIENT_EXPOSURE_COUNT=0
SOURCE_LABEL_MUTATION_COUNT=0
DETERMINISM_FAILURE_COUNT=0
```

The machine-readable bug-class ledger contains all 28 required keys. Twenty-five are zero. Its three nonzero observation counters are expected and non-failing: two valid control-bearing public titles handled by the normalization policy, 155 repeated public title strings attached to different stable identities, and 23,024 display truncations whose full source values remain accessible.

## Payload distribution

| Metric | P50 | P90 | P95 | P99 | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Entities per dataset | 6 | 6 | 6 | 8 | 10 |
| Connections per dataset | 5 | 5 | 5 | 7 | 9 |
| Serialized dataset bytes | 6,167 | 7,047 | 7,434 | 8,882 | 16,510 |
| Accessible rows | 6 | 6 | 6 | 8 | 10 |
| Export SVG bytes | 6,496 | 6,906 | 7,091 | 8,903 | 12,050 |

## Performance

I/O and pure Canvas computation are reported separately.

```text
COLD_SOURCE_INDEX_REBUILD_A_MS=302.671
COLD_SOURCE_INDEX_REBUILD_B_MS=305.578
SOURCE_INDEX_HEAP_DELTA_BYTES=425887128
WARM_CACHE_REFERENCE_MS=0.001
WARM_SELECTED_RECORD_LOOKUP_P50_MS=0.029
WARM_SELECTED_RECORD_LOOKUP_P95_MS=0.035

DATASET_DERIVATION_P50_MS=0.036
DATASET_DERIVATION_P95_MS=0.058
DATASET_DERIVATION_P99_MS=0.084
CANVAS_PURE_FUNCTION_P50_MS=0.360
CANVAS_PURE_FUNCTION_P95_MS=0.458
CANVAS_PURE_FUNCTION_P99_MS=1.154
```

## Browser boundary

```text
LOCALHOST_PREVIEW=NOT_RUN_BY_REQUEST
BROWSER_INTERACTION_ACCEPTANCE=USER_REVIEW_PENDING
PNG_BROWSER_CONVERSION=USER_REVIEW_PENDING
```

SVG preparation is fully validated. Actual native bitmap download remains a manual user-review item because browser execution was excluded.
