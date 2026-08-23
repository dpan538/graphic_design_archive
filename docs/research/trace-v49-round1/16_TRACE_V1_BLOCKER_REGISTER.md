# TRACE V1 Blocker Register

| ID | Severity | Class | Blocker | Evidence/impact | Required owner/action |
|---|---|---|---|---|---|
| TRACE-BLOCK-001 | P1 | SEMANTIC | `relationshipCount=47982` is ambiguous | Count is proposed folder membership, not semantic relations; can mislead product/publication decisions | future manifest/docs release: rename count unit |
| TRACE-BLOCK-002 | P1 | DATA | governed relation/evidence population is empty | relation types, relations, claims, evidence, assertions all 0 | future explicit data/research release |
| TRACE-BLOCK-003 | P1 | PUBLICATION | no non-empty public domain projection/serializer | raw/internal rows and UUIDs cannot enter client payloads | design release-owned safe projections |
| TRACE-BLOCK-004 | P1 | SEMANTIC | place roles and coordinate provenance are absent | registered exact object-place roles 0; coordinate rows 0; all 7,995 unmapped | authority mapping, review, evidence policy |
| TRACE-BLOCK-005 | P1 | REVIEW | all 47,982 folder assignments remain proposed | accepted/evidence-complete memberships 0 | row-level review; do not bulk-promote |
| TRACE-BLOCK-006 | P1 | PUBLICATION | retained pages expose v48 counts/taxonomy beside empty v49 TRACE | release identity is confusing; unknown-label fallback is unsafe if revived | separate future scoped publication task |
| TRACE-BLOCK-007 | P1 | API | current release builder/API only supports empty TRACE | nonzero accepted population is explicitly rejected; DTOs are zero-only | future versioned API/read-model implementation |
| TRACE-BLOCK-008 | P2 | API | empty TRACE object list bypasses declared input validation | bogus layer, first bounds, and malformed cursor return 200 empty | future API conformance fix |
| TRACE-BLOCK-009 | P2 | PERFORMANCE | unrestricted legacy-like depth 2 is pathological | P95 5,682 nodes/27,614 edges; max 6,363/28,566 | typed depth-1 default, budgets, pagination, truncation |
| TRACE-BLOCK-010 | P2 | VISUALIZATION | visual grammar remains undecided | census was required before layout selection | later evidence-based visualization round |

```text
P0_COUNT=0
P1_COUNT=7
P2_COUNT=3
```

There is no P0 in the delivered disconnected foundation: held archive endpoints are rejected and no accepted public edge exists that can violate evidence policy. Public TRACE remains blocked by P1 data, semantic, review, publication, and API gaps.
