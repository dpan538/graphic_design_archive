# TRACE frontend data contracts and examples

This document is an implementation handoff, not a visual-design brief. It describes the data boundaries the frontend must preserve across the three top-level TRACE functions:

1. Context Canvas;
2. Spacetime;
3. Exploration, divided into Validated Exploration and Open Inquiry.

The complete route inventory is in `docs/api/trace/trace-api-catalog.v1.json`. The examples below are deliberately shortened; an omitted field is marked in prose rather than represented as a schema-valid payload.

## Contract boundary at a glance

| Function and layer | Read contract | Mutable client state | Required epistemic treatment |
|---|---|---|---|
| Function 1 — Context Canvas | governed Context V1 projection through `/api/v1/releases/{release}/trace/objects/{id}/context` | local canvas composition, viewport, selection, undo/redo, export state | project-curated context; never a historical relation |
| Function 2 — Spacetime | governed periods, atlas, and geography-record pages under `/api/v1/releases/{release}/trace/spacetime/…` | selected period, geography, renderer mode, viewport, page accumulator | recorded geographic and temporal context; aggregate marks are not object coordinates or semantic edges |
| Function 3 — Validated Exploration | stateful validated API under `/api/trace/v2/exploration` | map, governed state identity/hash, focus, expansion, composition choice, export request | exactly 21 evidence-qualified pairwise generic associations; no typed historical relation is inferred |
| Function 3 — Open Inquiry | independent read-only list/detail API under `/api/trace/v1/open-inquiry` | list/detail navigation only | unresolved inquiry records; never validated, active, projected, or topology-changing |
| Function 3 — v3 runtime/control inspection | read-only `/api/trace/v3/exploration` collections | catalog selection only | `ACTIVE_PRODUCT_FACT` and `SYNTHETIC_CONTROL` are explicit data classes; v3 controls are not Open Inquiry records |

Do not treat the shared word “TRACE” or coincident labels as permission to join records. A frontend join requires an explicit stable identifier supplied by the relevant contract.

## Function 1 — Context Canvas

### Request

```http
GET /api/v1/releases/current/trace/objects/SURF-EXAMPLE/context
Accept: application/json
```

For an exact release rather than `current`, send the release identity in the path and its matching research-manifest SHA-256 in `Archive-Research-Manifest-Sha256`. The runtime rejects an unavailable release/manifest pair.

### Response shape

The shared read API wraps the governed dataset as `{ "apiVersion": "v1", "data": … }`. The `data` object supplies:

- `schemaVersion: "trace-context/v1"`;
- release, manifest, Context projection, and projection-hash identities;
- one `selectedRecord` with a public surface ID and root metadata;
- `availability`, which is `ready` or `empty`;
- governed `representations` of kind `medium`, `theme`, or `movement_context`;
- explanations and provenance for each representation;
- `accessibleRows`, the non-graph equivalent of the same information.

Representative excerpt:

```json
{
  "apiVersion": "v1",
  "data": {
    "schemaVersion": "trace-context/v1",
    "release": {
      "researchReleaseId": "v49",
      "researchManifestSha256": "<64 lowercase hex characters>",
      "contextProjectionId": "trace-context-v1",
      "contextProjectionSha256": "<64 lowercase hex characters>"
    },
    "selectedRecord": {
      "surfaceId": "SURF-EXAMPLE",
      "title": "Example public record",
      "rootMetadata": {
        "creatorAttribution": "…",
        "objectType": "…",
        "dateDisplay": "…",
        "sourceName": "…"
      }
    },
    "availability": "ready",
    "representations": [],
    "accessibleRows": []
  }
}
```

The frontend must render `availability: "empty"` as a valid empty Context result, not as a network failure. It must preserve `publicationState`, the explanation wording, and the provenance decision when representations exist.

## Function 2 — Spacetime

### Read sequence

1. Load periods: `GET /api/v1/releases/{release}/trace/spacetime/periods`.
2. Load one atlas: `GET /api/v1/releases/{release}/trace/spacetime/atlas?period={periodId}`.
3. After geography selection, load records: `GET /api/v1/releases/{release}/trace/spacetime/geographies/{geographyId}/records?period={periodId}&first={1..100}`.
4. Continue only with the returned opaque cursor: append `&after={endCursor}`.

The periods resource accepts no query parameters. The atlas accepts exactly one `period`. The record resource accepts only `period`, `first`, and `after`; `first` is at most 100 and `after` is an opaque governed cursor.

The same shared read envelope and exact-release manifest binding used by Context apply here.

### Dataset semantics

- `PublicSpacetimePeriodsDataset` supplies the decade buckets, default period, membership policy, and governed geometry identity.
- `PublicSpacetimeAtlasDataset` separates `mappedGeographies`, `aggregateOnlyGeographies`, and `unmappedGeographies`; it also supplies `accessibleRows` and `realSemanticEdgeCount: 0`.
- `PublicSpacetimeRecordPage` supplies public record summaries and `pageInfo.hasNextPage` / `pageInfo.endCursor`.
- `recorded_date_context` and `recorded_region_context` are contextual roles. They do not assert where an object was physically made, used, or viewed.
- A range belongs to a period by interval overlap. The selected period is therefore not necessarily an exact object date.

Record-page excerpt:

```json
{
  "apiVersion": "v1",
  "data": {
    "schemaVersion": "trace-spacetime/v1",
    "period": {
      "periodId": "<governed period ID>",
      "membershipPolicy": "INTERVAL_OVERLAP"
    },
    "geography": {
      "geographyId": "<governed geography ID>",
      "label": "<public label>",
      "mappingState": "mapped"
    },
    "nodes": [],
    "pageInfo": {
      "hasNextPage": false,
      "endCursor": null
    },
    "totalCount": 0
  }
}
```

The frontend must discard a late atlas or record-page response if its projection hash, period, geography, or cursor identity does not match the request still current in the UI.

## Function 3 — Validated Exploration v2

Validated Exploration is the interactive product contract. It contains the validated vocabulary and the 21 evidence-qualified pairwise generic associations. Open Inquiry is not an option, query flag, or response variant of this API.

### Bootstrap and map creation

```http
GET /api/trace/v2/exploration/capabilities
GET /api/trace/v2/exploration/categories
POST /api/trace/v2/exploration/maps
Content-Type: application/json

{
  "category_id": "theme",
  "category_entry_id": "<optional governed category-entry ID>",
  "locale": "en"
}
```

`category_id` is one of `region`, `theme`, `medium`, or `movement`. Omitting `category_entry_id` deterministically selects the first governed entry in that category. English is the only supported locale.

The map response includes:

- `database_snapshot` and `map_id`;
- the selected category and composition;
- a state carrying both `state_id` and `state_hash`;
- at most eight visible nodes;
- only validated generic pair associations;
- a Unicode and ASCII plain-text tree representing the same composition;
- a textual map summary.

### State transition

```http
POST /api/trace/v2/exploration/maps/{mapId}/actions
Content-Type: application/json

{
  "action": "FOCUS_NODE",
  "target_id": "<governed vocabulary ID>",
  "expected_state_hash": "<current state hash>",
  "database_snapshot": "<current database snapshot>"
}
```

The available action vocabulary is `SELECT_CATEGORY`, `FOCUS_NODE`, `EXPAND_NODE`, `COLLAPSE_NODE`, `MOVE_FOCUS`, `SELECT_COMPOSITION`, `RESET_CATEGORY`, and `EXPORT_CURRENT_STATE`. The UI must send only an action listed in the current state’s `available_actions`. A `409` stale-state or database-version response invalidates optimistic state and requires a governed reload; it must not be patched locally.

### Read-only detail

- `GET /api/trace/v2/exploration/maps/{mapId}?state_id={stateId}` retrieves a governed state of that map.
- `GET /api/trace/v2/exploration/vocabulary/{vocabularyId}` retrieves one validated vocabulary record.
- `GET /api/trace/v2/exploration/associations/{associationId}` retrieves one validated generic pair association, including its accessible description and explicit nonclaims.

All v2 responses are `private, no-store` and bind the response to the database snapshot. Do not cache a map response across snapshot identities.

## Function 3 — Open Inquiry v1

Open Inquiry is a separate, read-only layer:

```http
GET /api/trace/v1/open-inquiry
GET /api/trace/v1/open-inquiry/{inquiryId}
```

Both routes also implement `HEAD` and `OPTIONS`. They accept no query parameters, pagination, filtering, or sorting controls. An unsupported query parameter fails with `400`; mutation methods fail with `405`.

Representative response envelope:

```json
{
  "schema_version": "trace-open-inquiry-response/v1",
  "api_version": "trace-open-inquiry/v1",
  "layer": "OPEN_INQUIRY",
  "registry_sha256": "<64 lowercase hex characters>",
  "boundary": {
    "evidence_bounded": true,
    "validated_layer_contamination_allowed": false,
    "implicit_pair_projection_allowed": false,
    "validated_topology_mutation_allowed": false,
    "stochastic_display": false
  },
  "data": {
    "count": 11,
    "items": []
  }
}
```

Every returned record states all of the following: `epistemic_status: "UNRESOLVED_OPEN_INQUIRY"`, `validated_relation: false`, `counts_as_validated: false`, `eligible_for_validated_graph: false`, `eligible_for_validated_composition: false`, `may_generate_pair_edges: false`, `may_modify_validated_topology: false`, `display_eligible: true`, `display_layer: "OPEN_INQUIRY"`, and `default_in_validated_results: false`.

The record may expose source-bounded evidence, counterevidence, qualifications, nonclaims, and provenance. It never exposes a truth probability, probability of truth, likelihood score, or confidence percentage. The frontend must not derive one.

Open Inquiry errors use `trace-open-inquiry-error/v1`. A registry integrity failure is retryable and fails closed with `503`; the UI must not substitute cached or validated records.

## Function 3 — v3 runtime and controls

Exploration v3 is a read-only integrity and runtime surface, not the interactive v2 map API and not the Open Inquiry registry. It exposes capabilities, baseline reconciliation, and list/detail resources for twelve collections:

`association-realizations`, `associations`, `composition-coherence-reviews`, `compositions`, `concept-senses`, `concepts`, `exports`, `incidences`, `navigation-states`, `scopes`, `transitions`, and `workflows`.

Direct collection routes return `data_class: "ACTIVE_PRODUCT_FACT"`. The corresponding `/controls/{collection}` routes return `data_class: "SYNTHETIC_CONTROL"`. Synthetic controls are test and reconciliation fixtures. They must not be relabelled “Open Inquiry,” counted among its 11 hypotheses, or presented as active product facts.

The v3 headers explicitly report fail-closed product activation and no active product state graph. A missing direct item that exists only in controls returns `NOT_ACTIVE_PRODUCT_FACT`; the frontend must preserve that distinction.

## Loading, empty, partial, and error treatment

- Loading state is owned by the request that initiated it. A late response must not overwrite newer state.
- Empty is a successful contract state only when the response schema permits it. Do not convert `404`, integrity failure, or registry failure into “empty.”
- Spacetime record pages are partial until `hasNextPage` is false. Display loaded and total counts separately.
- Validated v2 state is atomic. Do not combine nodes from one state hash with associations, tree, or export identities from another.
- Open Inquiry list and detail responses are atomic registry views. Do not retain items when their `registry_sha256` changes.
- Use the server-provided retryability flag. Do not retry non-retryable evidence or identity failures automatically.

## Forbidden data flows

The frontend must never:

- append Open Inquiry records to a v2 or v3 validated association array;
- turn a higher-order participant subset into pair edges;
- use an Open Inquiry record to alter a validated composition, state, metric, topology, tree, or export;
- treat v3 synthetic controls as unresolved Open Inquiry records;
- infer semantic relations from Context membership or Spacetime co-occurrence;
- make stochastic decisions about which Open Inquiry record to display.
