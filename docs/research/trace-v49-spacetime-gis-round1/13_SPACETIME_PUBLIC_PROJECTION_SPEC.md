# Spacetime public projection specification

## Identity

| Field | Value |
| --- | --- |
| Projection ID | `trace-spacetime-v1` |
| Schema | `trace-spacetime/v1` |
| Geography policy | `spacetime-geography-governance-v1` |
| Temporal policy | `spacetime-temporal-governance-v1` |
| Generator | `trace-spacetime-projection-generator-v1` |
| Bucket policy | `DECADE` |
| Range policy | `INTERVAL_OVERLAP` |
| Server-only full record index | Yes |
| Deterministic | Yes |

Final projection SHA-256: `f751b0f432ff684fd1000201b910aa397a4d9965468c2f7dd5022d6a4ae01c06`.

## Generated artifacts

- `manifest.json`: release bindings, policy IDs, exact counts, payload hashes, geometry reference, aggregate projection hash;
- `geography-registry.json`: 93 explicit governed entries;
- `time-buckets.json`: 23 decade periods and default period;
- `period-region-aggregates.json`: one compact geography cube per period;
- `record-index.json`: server-only 7,995-record public index for selected-geography pages;
- `governance-policy.json`: semantic roles, decision rules, invariants, held boundary, release diagnostics;
- `geometry/geometry-manifest.json`: immutable geometry provenance;
- `CHECKSUMS.sha256`: deterministic payload checksum register.

The static geometry itself is outside the server JSON directory under `public/trace-spacetime-v1/` so the client can fetch it once as an immutable asset.

## Canonical serialization

Serialization recursively sorts object keys, preserves meaningful array order, minifies JSON, appends one final LF, and writes UTF-8. The generator rebuilds in memory and compares output deterministically. The projection hash is derived from the governed payload hashes and policy/release identity, not from filesystem timestamps.

## Public versus server-only data

The client may receive:

- periods and geometry reference;
- one selected-period atlas;
- one cursor-paged selected-geography record page.

It must not receive the full 7,995-record index, held identities, private folder IDs, source SQLite rows, the full candidate metadata corpus, Context artifacts, exact object coordinates, or semantic relation claims.

## Counts and safety

The projection covers all 7,995 public records and zero held records. It retains 194 aggregate-only objects and one unmapped object rather than hiding them. There are zero internal UUID exposures, exact object-coordinate inferences, silent historical normalizations, and map-created TRACE semantic edges.

## Runtime integrity

The server reader validates manifest/payload hashes, policy/release bindings, counts, geography references, period membership, record totals, and browser-safe DTO boundaries once per process, then reuses immutable indexes. It does not open the generator inputs at public runtime.
