# Full 7,995-record governed validation

## Cohort

The authoritative eligible population contains 7,995 public records. The negative population contains 7,928 held records. Validation uses the frozen eligibility ledger and never infers eligibility from the generated projection itself.

Every public record was exercised through:

- selected-record and root-metadata construction;
- governed term, representation, and provenance IDs;
- explanation and publication-state resolution;
- governed template initialization and controlled-only palette;
- deterministic auto layout and connection construction;
- inspector and accessible explanation equivalence;
- export preparation and traceability metadata;
- public DTO construction and API serialization;
- repeated lookup/determinism checks.

## Result

```text
PUBLIC_OBJECTS_TESTED=7995
PUBLIC_OBJECTS_GOVERNED=7995
HELD_OBJECTS_TESTED=7928
HELD_OBJECTS_EXPOSED=0
FAILED_CONTEXT_OBJECTS=0
UNEXPLAINED_NODES=0
UNKNOWN_TERM_IDS=0
PROVENANCE_FAILURES=0
API_SERIALIZATION_FAILURES=0
ACCESSIBLE_EXPLANATION_MISMATCH_COUNT=0
EXPORT_PREPARATION_FAILURE_COUNT=0
NONFINITE_POSITION_COUNT=0
INVALID_CONNECTOR_COUNT=0
```

The held and well-formed unknown lookup paths are fail-closed and indistinguishable at the API boundary. The evidence records only their aggregate counts.

## Workload envelope

| Default controlled workload | P50 | P95 | Maximum |
| --- | ---: | ---: | ---: |
| Visible Context representations | 2 | 2 | 4 |
| Visible Context connections | 2 | 2 | 4 |
| Total nodes including selected-record root | 3 | 3 | 5 |

The histogram is 7,884 records with two representations, 106 with three, and five with four. This is materially simpler than Round 2 because 16,106 source membership structures are retained as provenance instead of duplicated as nodes and connections.

## Coverage and missingness

Every public record has one medium and at least one theme, so all 7,995 records have usable Context. Movement context is optional and appears on 110 records. The absence of movement creates no placeholder node. If a later governance version holds a representation, object eligibility and a valid dataset remain independent; governance must expose explicit missingness rather than repair it from held data.

## Conclusion

`CONTEXT_FULL_COHORT_TESTS=PASS`
