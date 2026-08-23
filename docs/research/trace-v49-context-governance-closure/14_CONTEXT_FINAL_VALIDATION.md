# Context V1 final validation

## Acceptance basis

Context V1 was validated as a governed projection derived from the frozen v49 research release. The validation binds the source commit `b60ac6faf5f249e4c0d40697e9255770277cac03`, research release `v49-api-contract-fresh-c`, research manifest SHA-256 `4addfdb3cb9314587908096572242b9d63e9cef9e6e1be68c0c646491a43a90a`, governance policy `context-governance-v1`, and projection `trace-context-v1`.

The generated manifest reports policy SHA-256 `aa13eaff6d42533a37777e546b8976bdad7d2be3a4ab4d405a77ce1aa61c7a0c` and projection SHA-256 `825f6ecaa9ae1496c8a00ea0fefa5c90319046cf9c1f08a2ef76b9b02df4baeb`. A deterministic check rebuilds the projection twice in memory, compares those bytes, and then compares them with the committed artifacts.

## Governed census

| Measure | Result |
| --- | ---: |
| Eligible public records | 7,995 |
| Held records excluded | 7,928 |
| Public records with Context | 7,995 |
| Context kinds | 3 |
| Public terms | 25 |
| Medium terms / representations | 10 / 7,995 |
| Theme terms / representations | 8 / 7,996 |
| Movement-context terms / representations | 7 / 115 |
| Published representations | 16,106 |
| Qualified / held / excluded representations | 0 / 0 / 0 |
| Real semantic edges | 0 |
| Region Context nodes | 0 |
| Region rows deferred to Spacetime | 7,996 |

The six same-kind multi-value records remain intact: one record carries two themes and five records carry two movement contexts. No term or value was merged to simplify the result. All 115 public movement representations were audited and published only as project-curated research context, never as definitive historical membership.

## Full-cohort gate

The authoritative verifier exercised every one of the 7,995 public datasets through governed identity, term and explanation resolution, provenance, publication state, default governed template, layout, palette availability, inspector data, accessible rows, export preparation, public DTO construction, and API serialization. Negative lookup testing covered all 7,928 held identities without recording or exposing those identities in the evidence package.

```text
PUBLIC_OBJECTS_GOVERNED=7995
GOVERNED_DATASET_FAILURE_COUNT=0
HELD_OBJECTS_EXPOSED=0
UNEXPLAINED_VISIBLE_NODE_COUNT=0
UNRESOLVED_EXPLANATION_CODE_COUNT=0
PROVENANCE_RESOLUTION_FAILURE_COUNT=0
PUBLIC_ID_COLLISION_COUNT=0
VALIDATION_ID_IN_GOVERNED_DTO_COUNT=0
INTERNAL_ID_EXPOSURE_COUNT=0
API_SERIALIZATION_FAILURE_COUNT=0
```

The visible controlled-representation distribution is P50 2, P95 2, and maximum 4. Because the selected-record root is separate, the corresponding default total-node distribution is P50 3, P95 3, and maximum 5. Default controlled connections match the representation distribution. Membership nodes and membership connections are zero; membership remains provenance only.

## Invariant result

All 22 required `CTX-GOV-INV-*` invariants passed. Together they establish registered explanations and stable IDs for every visible representation; absence of validation IDs, internal IDs, held records, membership nodes, region nodes, and semantic edges; resolved provenance and publication state; release/projection pinning; deterministic rebuild; accessible/visual semantic equivalence; client-source-graph exclusion; and preservation of frozen source state `proposed`. Production static-bundle exclusion is recorded separately by the post-build gate.

## Projection and runtime envelope

```text
GOVERNED_PROJECTION_RAW_BYTES=13129562
GOVERNED_PROJECTION_GZIP_BYTES=1661608
GOVERNED_RUNTIME_HEAP_BYTES=18203424
GOVERNED_RECORD_LOOKUP_P95_MS=0.012
HEAVY_VALIDATION_SOURCE_INDEX_USED_BY_PUBLIC_RUNTIME=false
FULL_CONTEXT_CORPUS_IN_CLIENT_BUNDLE=false
```

The public reader is server-only, validates projection integrity before lookup, and returns one release- and projection-pinned dataset. The exhaustive Round 2 source index remains a generation/regression tool and is not in the public reader dependency graph.

## API and regression gates

The additive resource is `/api/v1/releases/{release}/trace/objects/{id}/context`. The contract covers `GET`, `HEAD`, and `OPTIONS`; rejects writes; distinguishes malformed input from unavailable release and integrity failure; and makes held and well-formed unknown objects indistinguishable at the `404` boundary.

```text
NPM_CI=PASS
TYPECHECK=PASS
RUNTIME_TYPECHECK=PASS
CONTEXT_SYNTHETIC_REGRESSION=PASS
CONTEXT_REALDATA_REGRESSION=PASS
CONTEXT_GOVERNANCE_TESTS=PASS
CONTEXT_PUBLIC_PROJECTION_TESTS=PASS
CONTEXT_FULL_COHORT_TESTS=PASS
TRACE_PREPROGRAM_REGRESSION=PASS
SEARCH_INDEX_VERIFICATION=PASS
SEARCH_REGRESSION=PASS
API_TESTS=PASS
CONTEXT_API_HELD_NEGATIVE_TEST=PASS
READ_PLATFORM_REGRESSION=PASS
PRODUCTION_BUILD=PASS
GIT_DIFF_CHECK=PASS
```

No localhost preview or browser visual acceptance was required. This is a semantic, data, read-model, and functional Canvas acceptance; global navigation and final visual design remain deferred.

## Closure

`CONTEXT_V1_DECISION=CONTEXT_V1_CLOSED`

The closure claim applies to Context V1 semantics, governance, explainability, reproducible projection, public selected-record read model, and governed Canvas data mode. It does not authorize database mutation, a canonical-release change, final visual publication, Spacetime implementation, or Exploration Field implementation.
