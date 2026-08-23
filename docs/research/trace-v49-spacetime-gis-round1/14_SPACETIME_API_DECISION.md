# Spacetime API decision

## Decision

Expose three read-only governed resources under the existing v1 release API:

```text
GET /api/v1/releases/{release}/trace/spacetime/periods
GET /api/v1/releases/{release}/trace/spacetime/atlas?period=<period-id>
GET /api/v1/releases/{release}/trace/spacetime/geographies/<geography-id>/records
    ?period=<period-id>&first=<1..100>&after=<cursor>
```

The exact Spacetime path is detected before the generic repository/Search provider is imported or opened. This keeps the governed projection independent of Search and database-backed generic reads.

## Periods resource

Returns release/projection identity, temporal role/policy, decade/range policy, default period, 23 period summaries, and the immutable geometry reference. It accepts no query parameters.

## Atlas resource

Requires exactly one valid `period` parameter. Returns the selected period, unique-record denominator, mapped/unmapped record counts, geography-assignment count, held-excluded count, mapped marks, aggregate-only and unmapped side collections, accessible numerical rows, dot-policy metadata, and geometry reference.

Geometry polygons are not duplicated in atlas responses.

## Selected-geography records resource

Requires a valid opaque geography ID and period. It returns a deterministic page of public stable IDs, titles, governed region displays, and temporal summaries. Default page size is bounded; `first` cannot exceed 100. The opaque cursor is bound to the selected projection/geography/period state and is length-limited.

The resource does not expose a dot-to-record relation or exact coordinate.

## Release and error behavior

`current` resolves to the frozen current research pair. An exact release request must match both research release ID and `Archive-Research-Manifest-Sha256`. Unknown or mismatched releases fail closed. Duplicate/unknown query parameters, invalid period/geography IDs, malformed page sizes, and cursors return deterministic public errors.

Projection-integrity failures return a generic integrity error; implementation details and private identities are not exposed.

## Route use

The unlinked, noindex `/trace/spacetime` Server Component reads initial periods/atlas directly from the server reader rather than self-fetching over HTTP. The client fetches the stable geometry once, one small atlas per period change, and record pages only after selection.
