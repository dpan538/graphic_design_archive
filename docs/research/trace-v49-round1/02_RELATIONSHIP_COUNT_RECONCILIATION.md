# Reconciliation of the Reported 47,982 “Relationships”

## Exact interpretation

`47,982` is the count of distinct candidate `(folder_id, archive_object)` pairs loaded as proposed curated folder-membership assignments. It is **not** a count of accepted semantic relations, claims, TRACE edges, object–relation memberships, or public projections.

The lineage is deterministic:

1. The canonical candidate JSON has 47,982 folder/object pairs on both folder-side and surface-side representations.
2. The v48-to-v49 extractor set-compares those representations and emits one assignment with `assignment_kind=folder_membership`, `membership_role=curated_member`, `status=proposed` per pair.
3. The loader writes one parent row to `provenance.canonical_assignment` and one subtype row to `provenance.assignment_folder_membership` per assignment.
4. The verifier calls the metric `folderMembershipAssignments`.
5. Repository closure code renamed it `relationshipCount` in `FREEZE_V49.json`.

The parent and subtype counts describe the same rows and are not additive. A global sort by `(folder_id, stable_id)` produces pair-set SHA-256:

```text
b2ddbe94f4d569f6b9970246855b535374b7c1a9b8ac047de58899c860bd4573
```

| Source/table | Rows | Semantic meaning | State/public split | TRACE mark? | TRACE edge? | Evidence/review | Notes |
|---|---:|---|---|---|---|---|---|
| candidate JSON folder-side pairs | 47,982 | candidate curated membership | internal candidate | only after review | no | required | source representation |
| candidate JSON surface-side pairs | 47,982 | same pair set | internal candidate | only after review | no | required | cross-check, not additive |
| SQLite `object_folder_refs` | 47,982 | legacy reconciliation memberships | 24,102 public endpoint; 23,880 held endpoint | diagnostic only | no | v49 review required | same pair-set hash |
| `provenance.canonical_assignment` | 47,982 | assignment lifecycle parent | proposed 47,982; accepted/rejected/superseded 0 | after acceptance only | no | accepted evidence-bound decision | same assignments |
| `provenance.assignment_folder_membership` | 47,982 | typed curated membership | public endpoint 24,102; held endpoint 23,880; projected 0 | after acceptance only | no | required | exact source of headline count |
| `research.semantic_relation` | 0 | typed semantic proposition | all states 0 | no rows | no rows | predicate/evidence policy | actual semantic-edge source |
| `research.object_relation_membership` | 0 | object participation in relation | empty | no rows | no | inherits relation | separate count unit |
| release TRACE edge projection | 0 | release-owned public edge | public 0 | no rows | no rows | accepted, safe endpoints | fail-closed release |

## Other relationship-like legacy counts

Legacy v48 has 97,889 nodes, 255,695 graph edges, and 126,822 object-edge memberships. These are independent reconciliation/capacity units. They were not imported to `research.semantic_relation` and cannot be mapped to predicates: 9,393 objects have unequal `edgeIds` and `edgeLabels` array lengths, and zero row-by-row ID→predicate mappings are authorized.

The corrected headline is:

```text
FOLDER_MEMBERSHIP_ASSIGNMENT_COUNT=47982
ACCEPTED_SEMANTIC_RELATION_COUNT=0
API_VISIBLE_RELATIONSHIP_COUNT=0
```
