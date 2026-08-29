# TRACE export contract

This contract describes functional export behavior already supported by repository sources and the constraints a future frontend must preserve. It does not prescribe visual styling.

## Export surface matrix

| Function/layer | Export surface | Current contract | Boundary |
|---|---|---|---|
| Context Canvas | browser-generated PNG | current governed canvas composition and optional projection footer | project-curated context only; identifiers are public-safe |
| Spacetime | deterministic functional JSON/SVG-ready value | `trace-spacetime-functional-export/v1` prepared in code | aggregate positions only; no object coordinates and no semantic edges |
| Validated Exploration v2 | manifest, PNG, and SVG API responses; plain-text tree in every map/manifest | `trace-exploration-export-manifest-v2` and `trace-exploration-portrait-png-v2` | validated vocabulary and pair associations only |
| Exploration v3 | read-only records in the `exports` collection | semantic/projection-preservation audit records | not a render endpoint and not a replacement for v2 export |
| Open Inquiry | none | no export route | must never contaminate a validated export |

## Validated Exploration v2 export

### Preconditions

An export is valid only for the exact governed state currently returned by the v2 map API. Submit:

```json
{
  "map_id": "<current map ID>",
  "state_hash": "<current state hash>",
  "composition_id": "<current composition ID>",
  "export_preset": "portrait_card",
  "theme_token_set": "neutral-v1"
}
```

`theme_token_set` may be `neutral-v1` or `neutral-contrast-v1`. The only preset is `portrait_card`. The service rejects a stale state, a state belonging to another map, a composition mismatch, or a state that does not advertise `EXPORT_CURRENT_STATE`.

### Endpoints

- `POST /api/trace/v2/exploration/exports/manifest` returns the authoritative JSON manifest.
- `POST /api/trace/v2/exploration/exports/png` returns `image/png`.
- `POST /api/trace/v2/exploration/export/svg` returns `image/svg+xml`.

Use the identical request body for all three. The frontend should obtain and retain the manifest before downloading a binary so it can display or log the governed identity without parsing image bytes.

### Manifest invariants

The manifest binds:

- API, manifest, and render versions;
- `export_id`, database snapshot, map, state ID/hash, category entry, composition, and seed;
- the exact visible nodes and validated pair associations;
- the Unicode and ASCII plain-text tree;
- node and association counts;
- a provenance summary whose `generic_association_only` is true and whose source locators are withheld from the public export;
- independent semantic and presentation hashes;
- governed alt text and suggested filename.

The portrait output is exactly 1080 × 1620 pixels. It supports one through eight nodes. The renderer fails when node/tree membership diverges, an association endpoint is absent, or the tree exceeds its bounded layout. Those are integrity failures, not a reason to silently omit content.

The PNG response exposes `X-TRACE-Semantic-Hash`, `X-TRACE-Presentation-Hash`, `X-TRACE-State-Hash`, `X-TRACE-Export-ID`, and `X-TRACE-Export-Version`. The SVG exposes the same identities plus a restrictive content-security policy. The frontend must compare these values with the manifest/state it requested before reporting success.

PNG rendering is capacity-bounded: two concurrent renders, a queue of 32, and a ten-second queue wait in the current implementation. `RENDER_CAPACITY_EXCEEDED` is a retryable `503`; preserve the user’s state and offer an explicit retry. Do not resubmit continuously.

### Plain-text tree semantics

The `plain_text_tree` object is part of every v2 map and export manifest. It contains:

- the tree contract version;
- composition and root identity;
- the exact tree-node and tree-association ID sets;
- the visible association ID set;
- a Unicode tree and an ASCII equivalent.

It is a first-class equivalent representation, not decorative fallback text. Copy/download behavior must use the returned string verbatim. Do not reconstruct a tree from screen coordinates, and do not add Open Inquiry participants or inferred pair edges.

## Context Canvas PNG

Context Canvas prepares an export-only SVG from the current governed composition and converts it to PNG with browser-native image APIs. The output includes visible nodes and connections, full labels in SVG titles, and—by default—a metadata footer binding the selected public record, research release, and Context projection identity.

The filename follows `context-canvas-{public-record}-{UTC-instant}.png`. UUID-like material is replaced with `public-reference-withheld`; the frontend must not bypass that public-safe transformation.

The current safety limits are:

- scale capped at 4;
- either dimension capped at 16,384 pixels;
- total area capped at 64,000,000 pixels.

An over-limit composition or unavailable browser canvas fails explicitly. Keep the editable canvas intact, announce the failure, and do not offer a partial image as successful.

Context connections remain contextual classifications or governed memberships. Their appearance in a PNG does not turn them into historical or Exploration associations.

## Spacetime functional export

`prepareSpacetimeFunctionalExport` creates a canonical, newline-terminated `trace-spacetime-functional-export/v1` value. It binds the release, period, geometry asset hash, projection, renderer mode, map marks, legend, counts, mapping summary, accessible geography rows, and selected geography.

The exporter requires the renderer period, atlas denominator, and geometry hash to match. It sorts map geometry, marks, and rows deterministically. It excludes DOM state, CSS state, archive record payloads, held geography rows, internal UUIDs, and object coordinates.

Every position is labelled `aggregate_only`; the coordinate interpretation is “derived aggregate layout positions; not object coordinates”; `realSemanticEdgeCount` is zero. A future download control must carry those qualifications with the exported value. No current API route publishes a Spacetime export binary, so the handoff must not invent one.

## Open Inquiry exclusion

Open Inquiry has no export endpoint. Its 11 unresolved records cannot appear in:

- v2 export manifests;
- v2 PNG or SVG bytes;
- v2 plain-text trees;
- validated association counts or provenance summaries;
- v3 active product export records.

If a future product need calls for an inquiry-only export, it requires a separate contract, explicit `OPEN_INQUIRY` labelling, and new verification. It must not reuse a validated-export filename, manifest version, semantic hash, or endpoint.

## Frontend completion states

For every export control, expose these functional states independently of styling:

1. ready — current state is exportable;
2. preparing — the request or browser encoding is active;
3. complete — the returned identities match the request and the download has been initiated;
4. retryable error — capacity or temporary service failure;
5. non-retryable error — stale identity, invalid composition, integrity failure, or client capability failure.

Disable duplicate submissions while preparing. Cancellation may stop client work, but it must not mutate the governed map/canvas state. Never label an export complete solely because an HTTP response arrived; validate content type and the available identity headers first.
