# API Contract v0

**Status:** Draft contract for future backend/frontend implementation.  
**Scope:** Read-only archive index access. No crawling, ingestion, or WebLLM endpoints are included.

## Principles

- API responses must preserve citation, source, rights, and uncertainty context.
- Search is deterministic first.
- Images are optional and must be governed by rights policy.
- Frontend must treat missing images as normal.
- No endpoint should create historical claims.
- No endpoint should trigger ingestion jobs.

## Read Models

Database views:

- `api_search_documents`
- `api_source_registry`
- `api_historical_nodes`
- `api_entity_detail_base`
- `api_source_record_detail_base`
- `api_rights_review_summary`
- `api_relation_assertions`
- `api_regions`
- `api_coverage_matrix`
- `api_classification_axes`
- `api_geographies`
- `api_regional_movements`
- `api_regional_event_nodes`
- `api_publication_surfaces`
- `api_publication_surface_pages`
- `api_surface_table_rows`
- `api_folder_views`
- `api_folder_memberships`
- `api_filing_registry_cards`
- `api_filing_registry_members`
- `api_sparse_cards`
- `api_archive_bookmarks`
- `api_evidence_bundles`
- `api_evidence_bundle_items`
- `api_external_identifier_status`
- `api_authority_resolution_events`
- `api_entity_appellations`
- `api_geography_appellations`
- `api_relation_predicate_rules`
- `api_protocol_rights_reviews`
- `api_source_policy_summary`
- `api_source_terms_review_policy`
- `api_experimental_ingest_candidates`
- `api_source_record_relations`
- `api_digital_representations`
- `api_field_provenance`
- `api_record_family_profiles`
- `api_ingest_validation_rules`
- `api_first_ingest_record_targets`
- `api_first_ingest_target_verifications`

First-ingest scope additions:

- `api_source_registry` includes source-level automation status, rights basis, record-level-rights requirement, image-zone default, thumbnail/preview/IIIF capability, API-key flag, and protocol-sensitive flag.
- `api_regional_movements` includes first-ingest movement mode, script flags, collective authorship, periodical relevance, protocol-sensitive flag, and source priority class.
- `api_regional_event_nodes` includes event date precision, anchor strength, source-record requirement, browse priority, and web-archive relevance.
- `api_experimental_ingest_candidates` includes scope cell ID, target record count, HN/MV/event links, query profile, expected surface type, protocol flag, and manual-review requirement.
- `api_first_ingest_record_targets` exposes the first 48 target registry as operational planning data, not as already-ingested archive content.
- `api_first_ingest_target_verifications` exposes the mechanical verification result for each first-target row, including ready/manual/link-only/search-path/replacement/browser-recheck decisions.
- `api_field_provenance` exposes how normalized fields were produced from source fields, citations, evidence bundles, or editorial assertions.
- `api_digital_representations` keeps images, embeds, IIIF, captures, PDFs, and thumbnails separate from the described source record/entity.
- `api_source_record_relations` exposes issue/page, collection/item, book/page, web-capture/original, and other source-record host/part links.

Image-zone note:

- `IMG00` through `IMG03` imply an image frame exists and the display state is governed by rights/review evidence.
- `IMG04` means no image frame and should be used for text, appendix, authority, event, or institutional pages where an image area is not part of the page.

## Endpoints

### `GET /api/search`

Searches `api_search_documents`.

Query parameters:

- `q`: required search query.
- `type`: optional document type.
- `source`: optional source ID.
- `rights`: optional rights state or policy.
- `region`: optional region ID.
- `geo`: optional geography ID.
- `historicalNode`: optional historical node ID.
- `movement`: optional movement/regional movement ID.
- `dateStart`: optional start year.
- `dateEnd`: optional end year.
- `limit`: default `20`.
- `offset`: default `0`.

Response:

```json
{
  "query": "bauhaus",
  "limit": 20,
  "offset": 0,
  "results": [
    {
      "id": "historical_nodes:HN008",
      "documentType": "historical_nodes",
      "title": "Bauhaus, New Typography, modernist books and magazines",
      "snippet": "Matched field excerpt",
      "seedTable": "historical_nodes",
      "seedId": "HN008",
      "entityId": null,
      "sourceRecordId": null,
      "facets": {
        "seedTable": "historical_nodes",
        "dateStart": "1919",
        "dateEnd": "1938"
      }
    }
  ]
}
```

Required frontend behavior:

- show the source/context of the match where available;
- do not imply ranking equals historical importance;
- expose filters/facets separately from result title/snippet.

### `GET /api/historical-nodes`

Returns historical spine/tree nodes.

Response:

```json
{
  "items": [
    {
      "id": "HN008",
      "title": "Bauhaus, New Typography, modernist books and magazines",
      "dateStart": 1919,
      "dateEnd": 1938,
      "dateText": "c.1919-1938",
      "geoCenters": "Weimar; Dessau; Berlin; Zurich; Prague; Amsterdam; London",
      "associatedFormations": "Bauhaus; New Typography; functional modernism",
      "rightsRiskLevel": "Medium",
      "underdocumentedNotes": "Transmission into Britain, the U.S., Latin America, and elsewhere should be indexed as relations, not assumed."
    }
  ]
}
```

### `GET /api/sources`

Returns source registry records.

Query parameters:

- `priority`: launch inclusion/readiness label, currently `Launch` for first-version scope.
- `accessMethod`: optional.
- `linkOnlySafer`: optional.

Response:

```json
{
  "items": [
    {
      "sourceId": "SRC005",
      "name": "V&A Collections API",
      "url": "https://developers.vam.ac.uk/guide/v2/",
      "sourceType": "museum collection",
      "accessMethod": "API",
      "priority": "Launch",
      "automatedIngestion": "Yes",
      "linkOnlySafer": "Yes for images",
      "rightsSummary": "Collection data and images available; object-level rights vary.",
      "defaultImageZone": "IMG00",
      "defaultRecordPolicy": "manual_review_required",
      "recordLevelRightsRequired": true,
      "automationStatus": "manual_review",
      "lastVerifiedDate": "2026-05-29"
    }
  ]
}
```

### `GET /api/geographies`

Returns launch-scope geography and context records.

Query parameters:

- `region`: optional region ID.
- `type`: optional geography type.
- `q`: optional name/search query.

Response:

```json
{
  "items": [
    {
      "geoId": "GEO040",
      "name": "Mainland China",
      "parentGeoId": "GEO035",
      "parentName": "East Asia",
      "regionId": "REG008",
      "regionName": "Mainland China",
      "geoType": "country_context",
      "isoCode": "CN",
      "languageScope": "Chinese; minority languages; English",
      "scriptScope": "Simplified Chinese; Traditional Chinese historical; Latin; others"
    }
  ]
}
```

### `GET /api/regional-movements`

Returns regional movements, formations, schools, publishing cultures, state formations, counterpublic formations, and technical/digital regimes.

Query parameters:

- `region`: optional region ID.
- `geo`: optional geography ID.
- `historicalNode`: optional node ID.
- `dateStart`: optional start year.
- `dateEnd`: optional end year.

### `GET /api/regional-event-nodes`

Returns dateable regional historical nodes that connect geography, historical nodes, source needs, and rights risks.

### `GET /api/experimental-ingest-candidates`

Returns source/right behavior tests and first-ingest scope cells.

Important filters:

- `scopeRole=first_ingest_scope`
- `imageZone=IMG00`
- `queryProfile=shanghai_manhua`
- `protocolSensitive=true`

Minimum first-ingest response item:

```json
{
  "experimentalCandidateId": "EIC031",
  "scopeCellId": "C07",
  "scopeRole": "first_ingest_scope",
  "candidateName": "Shanghai Sketch / yuefenpai first-ingest cell",
  "historicalNodeIds": "HN005; HN007; HN013",
  "movementIds": "RM081",
  "eventIds": "REN055",
  "queryProfileId": "shanghai_manhua",
  "targetRecordCount": 4,
  "expectedImageZone": "IMG00",
  "manualReviewRequired": true,
  "expectedSurfaceType": "periodical issue sheet + page sheet"
}
```

### `GET /api/publication-surfaces/:id`

Returns the normalized public paper surface for rendering a loose-leaf sheet, card, folder cover, registration card, bookmark, index appendix, or excerpt strip.

Minimum response:

```json
{
  "publicationSurfaceId": "PUB000001",
  "seq": 42,
  "seqLabel": "00042",
  "surfaceType": "sheet",
  "targetType": "source_record",
  "targetId": "SR0001",
  "historicalNodeId": "HN008",
  "movementId": "MV011",
  "era": "1919-1933",
  "movementDisplay": "MV011",
  "tier": "M",
  "layoutId": "M-001",
  "imageZone": "IMG00",
  "displayNumber": "GD / 1919-1933 / 00042 / M-p01",
  "workflowStatus": "published"
}
```

Required frontend behavior:

- treat `SEQ` as library-wide, not folder-local;
- treat `historicalNodeId` and `movementId` as metadata/facets, not public folder routes;
- use `imageZone` and rights policy to decide image behavior;
- fetch pages and six-table rows rather than constructing historical claims in UI.

### `GET /api/folder-views/:id`

Returns a folder/filter view. Folder views do not own copied records; they expose memberships over shared publication surfaces.

Public `folderType` values are limited to:

```text
region | theme | medium | movement
```

Historical nodes, geographies, regional movements, and sources can appear as authority references or search facets, but they are not public folder types in v1.

### `GET /api/filing-registry-cards/:id`

Returns the classification ledger for a category or folder. This is the public explanation of why particular `SEQ` records appear in a class.

### `GET /api/entities/:id/appellations`

Returns source labels, preferred labels, alternate labels, transliterations, translations, community-preferred names, deprecated terms, language/script codes, and provenance.

### `GET /api/authority-resolution/:targetType/:targetId`

Returns authority identifiers, match status, resolution events, evidence bundles, rejected matches, unresolved candidates, and replacement/deprecation history.

### `GET /api/relation-predicates`

Returns predicate governance rules, including inverse labels, citation requirements, whether visual-only evidence is allowed, and public warning text.

Required rule:

- `visually_resembles` is the only predicate that may be based on visual comparison alone.
- `influenced_by`, `associated_with`, `part_of`, movement membership, and identity claims require documentary, source-metadata, or scholarly evidence.

### `GET /api/entities/:id`

Returns base entity detail plus relations, classifications, citations, and uncertainty notes when implemented.

Minimum response:

```json
{
  "entityId": "ENT0001",
  "entityType": "movement_period",
  "preferredLabel": "Bauhaus",
  "alternateLabels": "Staatliches Bauhaus",
  "description": "Reviewed description",
  "dateStart": 1919,
  "dateEnd": 1933,
  "dateText": "1919-1933",
  "authority": {
    "scheme": "VIAF",
    "id": null,
    "status": "needs_resolution"
  },
  "classifications": [],
  "relations": [],
  "citations": [],
  "uncertaintyNotes": []
}
```

### `GET /api/source-records/:id`

Returns one manually reviewed or ingested source record.

Minimum response:

```json
{
  "sourceRecordId": "SR0001",
  "source": {
    "sourceId": "SRC001",
    "name": "The Met Open Access",
    "url": "https://www.metmuseum.org/hubs/open-access"
  },
  "sourceIdentifier": "external-id",
  "sourceRecordUrl": "https://example.org/record",
  "title": "Source title",
  "creator": "Source creator display",
  "dateText": "Source date text",
  "captureMethod": "manual",
  "accessDate": "2026-05-29",
  "rights": {
    "rightsState": "link_only",
    "rightsUri": null,
    "displayPolicy": "metadata_only"
  },
  "citation": {
    "citationText": "Human-readable citation",
    "url": "https://example.org/record"
  },
  "images": []
}
```

Required frontend behavior:

- show source link prominently;
- show citation panel;
- show rights panel;
- if image array is empty, render metadata and source link without visual placeholder drama;
- never display an image when `displayPolicy` forbids it.

### `GET /api/source-policy/:sourceId`

Returns source-level ingest and display defaults, terms review state, metadata/image license notes, default image zone, protocol/privacy flags, and whether item-level rights override is supported.

### `GET /api/experimental-ingest-candidates`

Returns the controlled first-ingest shortlist. These are planning candidates only; listing them does not authorize crawling or image display.

Required frontend behavior:

- public rendering must refuse to display an image unless the read model contains a positive rights decision for `IMG01`, `IMG02`, or `IMG03`;
- unknown or ambiguous rights must render as `IMG00`;
- `IMG00` records must be treated as complete research records with an intentionally empty archive image frame: linework/shadow, brief rights/source text, and source link only.
- `IMG00` through `IMG03` assume an image frame exists and the visible state is determined by copyright/display permission.
- `IMG04` means no image frame; render as a pure text page. Treat it as `hasImageFrame=false`, not as a copyright tier.
- image zone must not be used as the size/frame dimension. Size belongs to tier/layout/template.

## Error Shape

```json
{
  "error": {
    "code": "not_found",
    "message": "Record not found",
    "details": {}
  }
}
```

## Non-Goals for v0

- No write endpoints.
- No crawling endpoints.
- No ingestion trigger endpoints.
- No WebLLM endpoints.
- No image proxy endpoints.
- No recommendation engine.

## Frontend Minimum Viable Readiness

Frontend work may begin only after:

- database skeleton migrations pass;
- seed data is loaded;
- search endpoint contract is implemented against seed data;
- source registry endpoint works;
- rights and citation fields are present in detail responses;
- `PROJECT_LOG.md` records the frontend handoff decision.
