# Database object cleanup ledger

| object | type | introduced | dependencies/use | decision | forward-only file | rollback/grant impact |
|---|---|---|---|---|---|---|
| `provenance.canonical_assignment_publishable_v5_idx` | partial index | migration 012 | no constraint, view, function, API, sealed-release, or external dependent; zero diagnostic scans | drop; fully covered by earlier selection/reverse-leaf indexes | migration 013 | replay-only rollback; no grant impact |
| `provenance.canonical_assignment_current_leaf_v5_idx` | partial reverse index | migration 012 | used by current-leaf anti-join | keep | n/a | correctness/performance boundary |
| `provenance.assignment_review_decision_current_leaf_v5_idx` | partial reverse index | migration 012 | used by effective-decision anti-join | keep | n/a | correctness/performance boundary |
| `release.research_launch_protocol_v5` | append-only table | migration 012 | build receipt/integrity/API lifecycle | keep | n/a | explicit revokes retained |
| `release.build_research_launch_snapshot_v5_internal` | function | function 018 | controlled wrapper and tests | replace | function 019 | signature/grants preserved |
| `release.record_research_launch_verification_v5` | function | function 019 | v5 seal verification before API/CAS | add/keep | function 019 + roles 007 | reviewer only |

Catalog dependency, definition, usage, owner, and post-drop evidence is under `raw/final/cleanup/`. Cleanup passes only with fresh replay, digest/schema parity, permission, and fault matrices.

The catalog inventory contains 168 v3/v4/v5/current-leaf/projection/launch objects plus its header. The post-drop proof reports the target absent, API/function references zero, and both reverse-leaf indexes present. Fresh A/B replay, schema/digest parity, 36/36 permissions, and 6/6 faults all passed, so `DATABASE_CLEANUP_LEDGER=PASS`.
