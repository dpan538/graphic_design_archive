# Context public API contract

## Resource

`/api/v1/releases/{release}/trace/objects/{id}/context`

The additive Context resource is compatible with Read API v1 because it preserves the existing release selector, response envelope, error model, immutable version headers, `GET`/`HEAD`/`OPTIONS` method policy, and read-only repository boundary. Its payload has its own explicit `trace-context/v1` schema and governed projection pins.

## Behavior

- `GET` returns exactly one selected public Context dataset.
- `HEAD` performs the same release and record lookup but returns no body.
- `OPTIONS` returns 204 without opening or querying a record.
- Other methods return 405.
- Public stable IDs must match `^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$` and be at most 80 characters; malformed IDs return 400.
- Held and well-formed unknown IDs return identical 404 problem bodies.
- An unavailable exact research release returns 404; a compatible repository/projection mismatch returns 409.
- Artifact or reference integrity failure returns 503.

Responses use `Cache-Control: no-store`, preserve the release manifest `Vary` contract, and contain the research release pair plus Context projection pair. The DTO includes safe selected-record metadata, governed representations, only the explanations used by that record, counts, and equivalent accessible rows. It contains no membership or semantic-edge fields.

The normative additive Read API documentation is `docs/api/trace-context-v1-read-api.md`; freeze-hashed historical API snapshots remain untouched.
