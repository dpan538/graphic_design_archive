# Context public API validation

## Additive resource

```text
/api/v1/releases/{release}/trace/objects/{id}/context
```

One read-only template was added to the existing v1 dispatcher. The resource retains the existing release selector, response envelope, version headers, error model, and repository boundary while using the explicit `trace-context/v1` data schema. Existing frozen API documents remain unchanged; the additive contract is documented separately in `docs/api/trace-context-v1-read-api.md`.

## Method and status matrix

| Case | Expected behavior | Result |
| --- | --- | --- |
| Public `GET` | `200`; one exact release/projection-pinned dataset | PASS |
| Public `HEAD` | Same lookup and headers; no body | PASS |
| `OPTIONS` | `204`; no record lookup; `Allow: GET, HEAD, OPTIONS` | PASS |
| Write methods | `405`; no mutation | PASS |
| Malformed or overlong ID | `400 INVALID_ARGUMENT` | PASS |
| Held ID | `404 NOT_FOUND` with generic Context detail | PASS |
| Well-formed unknown ID | Identical `404 NOT_FOUND` body | PASS |
| Missing exact release | `404 RELEASE_NOT_FOUND` | PASS |
| Research/projection mismatch | `409 RELEASE_VERSION_MISMATCH` | PASS |
| Artifact/reference integrity failure | `503 INTEGRITY_FAILURE` | PASS |

The accepted public ID grammar is `^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$`, bounded to 80 characters. Responses intentionally use `Cache-Control: no-store`, preserve `Vary: Archive-Research-Manifest-Sha256`, and advertise `Allow: GET, HEAD, OPTIONS`.

## DTO boundary

The success DTO contains the research release pair, Context projection pair, safe selected-record metadata, governed representations, the exact used explanation subset, equivalent accessible rows, and counts. It does not contain membership or semantic-edge collections, region nodes, internal UUIDs, private folder IDs, source URLs, held fields, validation-only IDs, or the full Context corpus.

Every serialized representation resolves a stable term ID, stable representation ID, registered explanation, publication state, and safe provenance record. The source state remains `proposed` and is not overloaded as publication.

## Test result

```text
CONTEXT_PUBLIC_API_TEMPLATES_ADDED=1
CONTEXT_API_TESTS=PASS
CONTEXT_API_HELD_NEGATIVE_TEST=PASS
API_SERIALIZATION_FAILURE_COUNT=0
READ_PLATFORM_REGRESSION=PASS
```

Held and unknown negative testing records only aggregate outcomes. No held identity is included in this package.
