# TRACE Context v1 read resource

This additive contract documents the governed Context projection derived from
the frozen v49 research release. It does not rewrite the frozen v49 database,
release manifest, or the historical v49 Read API closure documents.

## Resource

```text
GET /api/v1/releases/{release}/trace/objects/{id}/context
```

`{release}` is either `current` or an exact research release ID. Exact release
requests use `Archive-Research-Manifest-Sha256` and must open the same immutable
research pair recorded by the Context projection. `{id}` is one public surface
ID matching `SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*` and is bounded to 80 characters.

The resource adds one template to the existing v1 read-only dispatcher. It is
semantically additive: no existing v1 DTO or endpoint changes meaning.

## Methods and caching

| Method | Contract |
| --- | --- |
| `GET` | Return one release- and projection-pinned `trace-context/v1` dataset. |
| `HEAD` | Perform the same release, integrity, eligibility, and object lookup; return the same status and version headers with no body. |
| `OPTIONS` | Return `204` with `Allow: GET, HEAD, OPTIONS`; do not load a record. |
| `POST`, `PUT`, `PATCH`, `DELETE` | Return `405`; no read-model or source mutation occurs. |

The resource intentionally preserves the current Read API caching boundary:

```text
Cache-Control: no-store
Vary: Archive-Research-Manifest-Sha256
Allow: GET, HEAD, OPTIONS
```

The projection is deterministic, but this closure round does not promote the
Canvas or its data to final public navigation. Immutable public caching can be
introduced only through a later API-wide cache policy change.

## Success envelope and DTO

The normal v1 response envelope remains authoritative and contains the exact
research release pair. Its `data` field is a `PublicContextDataset`:

```json
{
  "schemaVersion": "trace-context/v1",
  "release": {
    "researchReleaseId": "v49-api-contract-fresh-c",
    "researchManifestSha256": "64 lowercase hexadecimal characters",
    "contextProjectionId": "trace-context-v1",
    "contextProjectionSha256": "64 lowercase hexadecimal characters"
  },
  "selectedRecord": {
    "surfaceId": "SURF-PUBLIC-ID",
    "title": "Public title",
    "rootMetadata": {
      "creatorAttribution": "Source-reported attribution",
      "objectType": "Source-reported object type",
      "dateDisplay": "Source-reported date",
      "sourceName": "Source name"
    }
  },
  "availability": "ready",
  "representations": [],
  "counts": {
    "representations": 0,
    "byKind": { "medium": 0, "theme": 0, "movementContext": 0 }
  },
  "explanationRegistryVersion": "trace-context-explanations-v1",
  "explanations": [],
  "accessibleRows": []
}
```

Each representation contains a governed public representation ID, governed
term ID, one of `medium`, `theme`, or `movement_context`, label, explanation
code, `project_curated_context` epistemic role, distinct publication state,
and a safe provenance summary. The provenance states that the frozen source
row remains `proposed`; Context publication does not relabel it as an accepted
semantic or historical relation.

`explanations` contains only entries used by the selected dataset. The
accessible rows expose the same type, publication state, source basis, and
permitted-interpretation information available to the graphic inspector.

The DTO never contains raw membership nodes, raw folder identifiers, internal
UUIDs, validation-only `ctxv49:` identifiers, region Context nodes, semantic
edges, held fields, URLs, or the full term/record corpus.

## Status contract

| Status | Code | Meaning |
| ---: | --- | --- |
| `200` | — | The selected public object has a valid governed Context dataset. |
| `400` | `INVALID_ARGUMENT` | The object ID does not satisfy the public stable-ID grammar or bound. |
| `404` | `NOT_FOUND` | The well-formed object is held or unknown. Both cases use the same code and detail. |
| `404` | `RELEASE_NOT_FOUND` | The requested exact research pair is unavailable under the existing v1 selector contract. |
| `409` | `RELEASE_VERSION_MISMATCH` | An opened research pair is incompatible with the pinned Context projection. No fallback occurs. |
| `503` | `INTEGRITY_FAILURE` | A generated artifact has the wrong schema, hash, count, identity, reference, or release binding. |
| `503` | `UNAVAILABLE` | The exact read service is unavailable. |

Held and unknown lookup failures use the same public message:

```text
Context dataset is not available for this object.
```

The endpoint exposes no list, term-registry, membership-detail, candidate, or
held-object enumeration resource.

## Server boundary

The runtime reads the committed `frontend/generated/trace-context-v1`
projection through a `server-only` module. It validates the projection manifest
and payload hashes once, caches a compact public-record lookup, and constructs
only the requested DTO. The exhaustive Round 2 SQLite/ledger source index is a
generation and reconciliation tool and is not imported by this resource.
