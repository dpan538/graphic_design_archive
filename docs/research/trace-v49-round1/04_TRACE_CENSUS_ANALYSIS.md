# TRACE Census Analysis

The machine-readable census is [03_TRACE_CENSUS.tsv](./03_TRACE_CENSUS.tsv). Counts are release-pinned to the verified source SHA and derive from frozen receipts, the eligibility ledger, canonical source hash, and immutable SQLite reconciliation input.

## Populated layers

- Raw preservation is populated: 15,923 source records and 3,559,820 path-addressed field literals. Raw content is restricted.
- Publication eligibility is populated: 7,995 eligible corpus memberships and 7,928 held fail-closed deltas.
- Provenance bridges are populated: one `object_source_record` per canonical object.
- Curated candidate membership is populated: 47,982 folder assignments, all `proposed`.
- Root identity is populated: one `trace_node` and `object_trace_node` bridge per canonical object.

Root nodes and source-record bridges are identity/provenance structures, not evidence that an object is TRACE-eligible.

## Empty governed semantic layers

Relation types, epistemic classes, claims and revisions, claim evidence, semantic relations, relation claims, analysis runs, working TRACE trees/branches, object–relation memberships, normalized object assignments, normalized source documents/versions, evidence items, assertions, and all relevant public release projections are zero.

The state census therefore does not need invented normalization vocabulary: semantic relation state counts are all exactly zero. Folder assignments use the actual formal state `proposed`; none are accepted, rejected, or superseded.

## Integrity results

For the v49 governed semantic population:

- duplicate propositions/IDs: 0;
- self-loops: 0;
- dangling endpoints: 0;
- unregistered or inactive predicates used: 0;
- accepted relations missing evidence/claim: 0;
- duplicate relation/root memberships: 0;
- orphan branches/trees: 0 because none exist;
- root identity cardinality defects: 0; all 15,923 objects have one root bridge.

These zeros result from an empty semantic population, not proof that candidate legacy relations are valid.

## Public boundary

The authoritative ledger partitions 15,923 as 7,995 `eligible` and 7,928 `held`, with zero overlap and complete coverage. SQLite fallback eligibility must not be used: it historically upgrades missing-tier records and produces an incompatible `source_verified` count.

All 7,995 public objects have raw context, date, region, and source-adjacent candidates. None has a non-empty public TRACE domain projection. Therefore analysis reports both layers explicitly:

```text
INTERNAL_EXISTS(candidate domain data)=7995
REVIEWED/ACCEPTED(domain semantics)=0
PUBLIC_ELIGIBLE(archive object)=7995
PUBLIC_PROJECTED(non-empty TRACE domain)=0
```

No data repair was performed. Future population of governed facts requires an explicit future data/review release.
