# Frontend Field Decisions v1

**Status:** Binding for the first simple frontend prototype and the next generated payload contract.  
**Date:** 2026-05-30

This note resolves the field conflicts that appeared after narrowing the public archive box to four folder types.

## 1. Historical Nodes in Public UI

Historical nodes (`HN*`) remain in the project, but they are not public folder types.

Public folder types are only:

- `region`
- `theme`
- `medium`
- `movement`

Historical nodes may appear as:

- search facets;
- source/research metadata;
- internal ingest/classification fields;
- optional small provenance rows inside the `CLASSIFICATION` table;
- generator inputs for chronology and scope checks.

Historical nodes must not appear as:

- top-level public browse routes;
- folder tabs;
- folder type rails;
- drawer names;
- required public page headings;
- primary display-number segments.

## 2. Display Number Grammar

Public display numbers should no longer encode `HN` or movement membership.

Use:

```text
GD / {ERA} / {SEQ} / {TIER}-p{PAGE}
```

Examples:

```text
GD / 1894 / STAGED-0002 / M-p01
GD / 1917-1918 / STAGED-0001 / M-p01
GD / 1976 / STAGED-9001 / L-p02
```

Reason:

- folders are filters, not containers;
- a surface can belong to many folders;
- folder memberships can change without forcing public display-number aliases;
- `HN` is a research axis, not a public folder axis.

`SEQ` remains global. During visual validation, `STAGED-*` labels are allowed. Final `SEQ` labels are minted only after source review and rights review gates pass.

## 3. Historical Nodes and API

Keep:

- `historical_nodes`
- `api_historical_nodes`
- historical-node search documents
- `historicalNodeId` / `historicalNodeIds` in research or classification payloads

Do not create:

- `/folders/historical-node`
- `/historical-nodes` as a primary public browse page for v1

If a historical-node route is ever added later, it should be a research/reference appendix, not part of the archive box folder rail.

## 4. Folder Type Enum

Public folder views should align exactly with:

```text
region | theme | medium | movement
```

Legacy or internal categories such as `historical_node`, `regional_movement`, `geography`, and `source` are not public folder types. Their identifiers can still be stored as authority references on a public folder.

## 5. Folder ID and Slug Rules

Public folder IDs are folder-view IDs, not authority IDs.

Use:

```text
FOL-{TYPE}-{SLUG_UPPER}
```

Examples:

```text
FOL-REGION-UNITED-STATES
FOL-REGION-FRANCE
FOL-MEDIUM-POSTER
FOL-MOVEMENT-ART-NOUVEAU-BELLE-EPOQUE
```

Rules:

- `folderId` is stable for folder view membership.
- `slug` is lowercase kebab-case and used in routes.
- authority IDs stay in `authorityRefs`.
- region folders may reference `REG*` and/or `GEO*`.
- movement folders may reference `MV*` and/or `RM*`.
- medium folders may reference `media_technologies.media_id` where available.
- theme folders may use curated theme keys until a theme authority table exists.

## 6. Movement Folder Key

Public movement folders use folder-view IDs and slugs, not raw `MV*` IDs.

The relationship to authority data is stored separately:

```json
{
  "folderId": "FOL-MOVEMENT-ART-NOUVEAU-BELLE-EPOQUE",
  "type": "movement",
  "slug": "art-nouveau-belle-epoque",
  "authorityRefs": {
    "movementIds": ["MV002"],
    "regionalMovementIds": ["RM002"]
  }
}
```

This lets one public folder collect a broad movement label plus regional formations without collapsing their authority records.

## 7. Mock to Generated Payload

The next generated payload should be:

```text
generated/public_surfaces_v1.json
```

It should be shape-compatible with:

```text
data/public_surface_mock_v0.json
```

Cursor can build TypeScript types from the mock shape now. The generator should preserve the same top-level keys:

- `meta`
- `folderTypes`
- `folders`
- `surfaces`

Later payloads may add fields, but should not remove or rename these v1 fields without a migration note.

## 8. Search Behavior

Frontend v1 should implement local deterministic search over the mock payload only.

Search fields:

- surface title;
- creator;
- date text;
- place text;
- object type;
- medium;
- source name;
- folder titles;
- table row values.

When connected to API later, use `api_search_documents`/`api_search` shape with:

- `title`
- `snippet`
- `facets`
- `sourceContext`
- `rights`

Local search must not call WebLLM or any hosted LLM API.

## 9. Sparse Cards and Fallback Stubs

The frontend mock must include at least:

- one `sheet` with `IMG00`;
- one `sheet` with `IMG03` or open-image candidate behavior;
- one `sheet` with `IMG04`;
- one `card` using `card.sparse.v0`;
- one `fallback_stub` using `stub.fallback.v0`.

Cards and stubs are public archive states, not failed pages.

## 10. Final Decision Summary

- HN remains as research metadata and search facet.
- HN is removed from public display numbers.
- HN is not a public folder type.
- Public folders are exactly `region`, `theme`, `medium`, and `movement`.
- Folder IDs are public view IDs; authority IDs live in `authorityRefs`.
- Mock and generated payloads should stay shape-compatible.
- v1 search is local static search only.
