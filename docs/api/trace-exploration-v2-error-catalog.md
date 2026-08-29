# TRACE Exploration API v2 error catalog

The v2 API returns a closed, sanitized error document defined by
`schemas/trace/exploration/v2/error.schema.json`. It never returns stack traces,
filesystem paths, caught exception text, submitted identifiers, or internal
read-model records.

Every v2 error contains:

- `schema_version`: `trace-exploration-api-error-v2`
- `api_version`: `trace-exploration/v2`
- `code`: one governed code from the table below
- `message`: stable public wording
- `status`: HTTP status
- `retryable`: whether an unchanged request may reasonably succeed later
- `instance`: the fixed API root `/api/trace/v2/exploration`
- `database_snapshot`: the active snapshot identity, or `unavailable` when the
  read model itself cannot pass its integrity boundary

The bare v2 root is governed: `GET` and `HEAD` return `308` with `Location:
/api/trace/v2/exploration/capabilities`, `OPTIONS` returns `204`, and mutation
methods return the same sanitized `405 METHOD_NOT_ALLOWED` document and
consistent `Allow: GET, POST, HEAD, OPTIONS` header as the catch-all route.

| Code | HTTP | Retryable | Meaning |
|---|---:|:---:|---|
| `INVALID_REQUEST` | 400 | No | JSON is malformed, has unknown fields, or violates the request shape. |
| `INVALID_ACTION` | 400 | No | The action name or target identifier is invalid. |
| `INVALID_EXPORT_PRESET` | 400 | No | The preset or neutral theme is unsupported. |
| `INVALID_CATEGORY` | 404 | No | The category is not one of the four canonical categories. |
| `INVALID_CATEGORY_ENTRY` | 404 | No | The requested governed category entry is unavailable. |
| `INVALID_VOCABULARY` | 404 | No | The vocabulary identifier is not active in the production model. |
| `INVALID_ASSOCIATION` | 404 | No | The association identifier is not active in the production model. |
| `STATE_NOT_FOUND` | 404 | No | The endpoint, map, or state does not exist in the requested category entry. |
| `METHOD_NOT_ALLOWED` | 405 | No | The HTTP method is not available for the endpoint. |
| `ACTION_NOT_AVAILABLE` | 409 | No | No transition exists for the exact state, action, and target. |
| `STALE_EXPLORATION_STATE` | 409 | No | A well-formed expected state hash is stale or belongs to another map. |
| `STATE_DATABASE_VERSION_MISMATCH` | 409 | No | The request is bound to another frozen database snapshot. |
| `NO_EXPORTABLE_COMPOSITION` | 409 | No | The state/composition pair is inconsistent or not exportable. |
| `REQUEST_LIMIT_EXCEEDED` | 413 | No | The streamed UTF-8 request body exceeds 65,536 bytes. |
| `RENDER_CAPACITY_EXCEEDED` | 503 | Yes | All bounded export-render slots and the bounded wait queue are occupied, or the wait timed out. |
| `INTERNAL_DATA_INTEGRITY_FAILURE` | 503 | Yes | The compact production model, deterministic derivation, or renderer failed its integrity contract. |

## Compact transition derivation

The production read model retains the top-level `transitions` boundary as a
closed descriptor:

```json
{
  "derivation_version": "trace-exploration-derived-transitions-v2",
  "key_format": "state_hash|action|target",
  "transition_count": 749944
}
```

It does not store the exhaustive transition map. At load time the server
validates the complete immutable focus × expansion state product for every
composition, builds a compact state-key index, and proves that the derived
legal-target cardinality equals both descriptor and capability counts. Action
requests use the same governed `state_hash|action|target` identity and return
the same next state as the exhaustive transition census.

## SVG export boundary

`POST /api/trace/v2/exploration/export/svg` accepts the same closed
`ExplorationV2ExportRequest` as the manifest and PNG operations. It resolves
the same manifest `export_id`, state hash, semantic hash, presentation hash,
and render version as PNG, while changing only the response representation and
the attachment filename extension.

The successful response is a fixed 1080 by 1620, self-contained UTF-8
`image/svg+xml` document. Labels are XML-escaped, output size and content are
bounded by the governed manifest (at most eight nodes), and the document does
not contain scripts, event handlers, active embedded XML, external-resource
references, source locators, or held data. Identical accepted requests produce
byte-identical SVG bodies.

Failures never return a partial SVG or renderer exception text. They use the
same sanitized JSON error schema and fixed code/status/retryability bindings as
the rest of v2: malformed input or an unsupported preset is `400`, missing
governed identifiers are `404`, wrong methods are `405`, stale or inconsistent
export state is `409`, bodies over 65,536 UTF-8 bytes are `413`, and bounded
render-capacity or integrity failures are `503`.

## Retired v1 route

The historical v1 implementation and read-model artifacts are preserved for
audit history, but its HTTP root and catch-all routes are retired. Every v1
route and HTTP method returns `410 Gone` with:

```json
{
  "schema_version": "trace-exploration-api-retirement-v1",
  "api_version": "trace-exploration/v1",
  "code": "API_VERSION_RETIRED",
  "message": "This Exploration API version is retired. Use the versioned successor.",
  "status": 410,
  "retryable": false,
  "successor": "/api/trace/v2/exploration"
}
```

The response also carries a `Link` header with `rel="successor-version"` and a
`Sunset` header. This is an explicit version retirement, not a silent v1 schema
change.
