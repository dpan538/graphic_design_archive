# Context Domain Readiness

Context is the broadest internal candidate domain, but no candidate category is an accepted semantic graph.

| Category | Classification | Records/public coverage | Unique values | Median / P95 / max per public object | Evidence/review | Stable public ID | Aggregate safe | Object-local safe | Semantic edge safe |
|---|---|---:|---:|---:|---|---|---|---|---|
| raw medium/folder candidate | `CONTROLLED_ASSIGNMENT` | 7,995 / 7,995 | 1,167 raw labels | 1 / 1 / 1 | proposed/raw; no evidence item | object only | analysis only | preprogram only | no |
| raw theme candidate | `CONTROLLED_ASSIGNMENT` | 7,996 assignments on 7,995 objects | not governed | 1 / 1 / 2 | proposed | object only | analysis only | preprogram only | no |
| movement candidate | `CONTROLLED_ASSIGNMENT` | 115 assignments on 110 objects | not governed | 0 / 0 / 2 | proposed | object only | analysis only | preprogram only | no |
| folder membership, all types | `CURATED_MEMBERSHIP` | 24,102 assignments; 7,995 objects | 185 folders globally | 3 / 3 / 5 | all proposed; 0 accepted | internal folder token only | analysis only | preprogram only | no |
| raw object type | `ATTRIBUTE` | 7,995 / 7,995 | 89 labels | 1 / 1 / 1 diagnostic | raw only | object only | analysis only | preprogram only | no |
| raw collection context | `SOURCE_CONTEXT` | 7,980 / 7,995 | not public-governed | 1 / 1 / 1; 15 zero | raw source metadata | object only | analysis only | preprogram only | no |
| raw creator label | `ATTRIBUTE` | 5,968 / 7,995 | not published by v49 projection | 1 / 1 / 1; 2,027 zero | raw only | object only | analysis only | preprogram only | no |
| normalized object-agent/medium/type/subject/collection | `CONTROLLED_ASSIGNMENT` | 0 | 0 | 0 / 0 / 0 | empty | schema only | no rows | no rows | no rows |
| tree/branch membership | `CURATED_MEMBERSHIP` | 0 | 0 | 0 / 0 / 0 | empty | schema only | no rows | no rows | no |
| context semantic relation | `SEMANTIC_RELATION` | 0 | 0 predicates | 0 / 0 / 0 | no registry/evidence | schema only | no rows | no rows | no rows |

The combined measured candidate association workload is context assignments plus folder memberships: minimum/median/P95/P99/max = `5/5/5/7/9`. This is a workload envelope only. Value-node uniqueness was not promoted, so node counts are reported as conservative upper bounds in the capacity document.

## Semantic guardrails

- A medium or type assignment is descriptive metadata, not a historical relationship.
- Tree or folder membership is curation, not influence.
- Shared classification between two objects does not establish an object-to-object relation.
- Collection membership does not establish creation, ownership, chronology, or causation unless separately reviewed and modeled.
- A renderer may draw guides for grouping, but those guides must remain `semantic:false`.

Public aggregate and object-local payloads require a release-owned serializer with safe stable identifiers and accepted/review states. The current raw labels and internal folder IDs are not public read models.

```text
CONTEXT_V1=READY_FOR_PREPROGRAM_ONLY
```
