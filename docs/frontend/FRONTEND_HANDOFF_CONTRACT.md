# Frontend Handoff Contract v0

**Status:** Draft contract for future Cursor/frontend work.  
**Important:** Frontend implementation should not begin until the database skeleton gates are complete.
**Design-system freeze is blocked** until the global coverage baseline is represented in database and API contracts.

## Project Role of the Frontend

The frontend is a reading, search, and source-navigation interface. It is not the primary research object by itself, and it should not impose a single visual narrative.

The frontend must support:

- global search;
- historical spine/tree reading;
- source registry browsing;
- entity/detail pages;
- source record pages;
- citation panels;
- rights panels;
- related records;
- uncertainty/provenance notes;
- filters/facets.
- geography/date filters across regions, countries/context areas, cities/places, historical nodes, movements/formations, language/script, and source/rights status.
- archive-cabinet publication surfaces: `SEQ`, display number, sheet tier, layout ID, page labels, image zone, six fixed table kinds, folder memberships, filing registry cards, sparse cards, and bookmarks.
- authority and vocabulary transparency: source-language labels, script codes, transliteration systems, external identifier status, unresolved matches, evidence bundles, and relation predicate warnings.
- source and rights policy capsules: source-level default policy, item-level rights override, terms review status, default image zone, and warnings that prevent accidental image escalation.
- first-ingest scope cells: planned target record count, expected surface type, query profile, manual-review requirement, and reason for inclusion before real source records exist.
- first-ingest record targets: the first 48 proposed records/search paths, including target readiness, expected image zone, rights risk, and review dependencies.
- first-ingest target verifications: mechanical readiness checks that distinguish source records ready for manual ingest from search paths, blocked records, source replacements, and browser-recheck cases.
- fallback source stubs: historically relevant targets that cannot yet become source records, but should still appear as link-only/search-path areas with clear not-ingested status.
- field provenance and digital representation records as separate panels or expandable evidence rows, not blended into descriptive prose.

The frontend must not assume:

- images are locally stored;
- all records have images;
- all records have open image rights;
- AI is available;
- graph visualization is the primary experience;
- search results are ranked by historical importance.
- Europe or the United States are the default historical center.
- Latin-script labels fit all records.

## WebLLM Boundary

WebLLM is not part of the first frontend handoff.

If added later:

- it must run locally/browser-side;
- it must not call a hosted LLM API for ordinary public use;
- it must be optional;
- it may assist query expansion or result summarization;
- it must not create unsourced historical claims;
- it must not decide classification, rights, entity merges, or relation assertions.

## Minimum API Concepts

The frontend should eventually consume stable read-only endpoints shaped around these concepts:

### Search Result

```json
{
  "id": "search_docs:example",
  "documentType": "historical_node",
  "title": "Bauhaus, New Typography, modernist books and magazines",
  "snippet": "Matched text with field context",
  "facets": {
    "historicalNode": "HN008",
    "entityType": "movement_period",
    "source": null,
    "rightsState": null,
    "dateStart": 1919,
    "dateEnd": 1938
  },
  "sourceContext": {
    "sourceName": null,
    "sourceUrl": null,
    "accessDate": null
  },
  "rights": {
    "displayPolicy": "metadata_only",
    "rightsLabel": null,
    "rightsUri": null
  }
}
```

### Source Registry Item

```json
{
  "sourceId": "SRC005",
  "name": "V&A Collections API",
  "url": "https://developers.vam.ac.uk/guide/v2/",
  "sourceType": "museum collection",
  "accessMethod": "API",
  "priority": "Launch",
  "automatedIngestion": "Yes",
  "linkOnlySafer": "Yes for images",
  "rightsSummary": "Object-level rights vary.",
  "defaultImageZone": "IMG00",
  "recordLevelRightsRequired": true,
  "automationStatus": "manual_review",
  "lastVerifiedDate": "2026-05-29"
}
```

### Geography Item

```json
{
  "geoId": "GEO040",
  "name": "Mainland China",
  "parentGeoId": "GEO035",
  "regionId": "REG008",
  "geoType": "country_context",
  "isoCode": "CN",
  "languageScope": "Chinese; minority languages; English",
  "scriptScope": "Simplified Chinese; Traditional Chinese historical; Latin; others"
}
```

### Regional Movement Item

```json
{
  "regionalMovementId": "RM028",
  "name": "Chinese Republican Shanghai commercial print",
  "regionId": "REG008",
  "geoId": "GEO040",
  "dateStart": 1912,
  "dateEnd": 1949,
  "relatedNodeIds": "HN005; HN007",
  "sourceNeeds": "Shanghai library collections; periodicals; poster archives",
  "rightsRisk": "high"
}
```

### Experimental Ingest Candidate

```json
{
  "experimentalCandidateId": "EIC037",
  "scopeCellId": "C13",
  "scopeRole": "first_ingest_scope",
  "candidateName": "NAIDOC / land-rights posters first-ingest cell",
  "primaryRegion": "REG015",
  "historicalNodeIds": "HN012; HN013; HN015",
  "movementIds": "RM087",
  "eventIds": "REN061",
  "expectedImageZone": "IMG00",
  "protocolSensitive": true,
  "manualReviewRequired": true,
  "targetRecordCount": 3,
  "expectedSurfaceType": "registration card + protocol appendix"
}
```

The first ingest scope is not public content by itself. It is an operational layer that tells Cursor/frontends which templates and empty states must exist before records are actually fetched.

### Fallback Source Stub

```json
{
  "fallbackStubId": "FSS026",
  "firstTargetId": "FIT026",
  "scopeCellId": "C08",
  "targetLabel": "한국민중판화모음전 포스터",
  "sourceName": "OpenArchive",
  "sourceUrlOrSearchPath": "https://archives.kdemo.or.kr/isad/view/01015877",
  "replacementUrl": "https://sema.seoul.go.kr/semaaa/front/archive/view.do?iId=21227",
  "fallbackStatus": "replacement_recommended",
  "publicStubPolicy": "show_replacement_link_only_stub",
  "expectedImageZone": "IMG00",
  "displayAreaPolicy": "preserve_area_with_empty_frame",
  "notIngestedReason": "Original exact source not confirmed",
  "userActionLabel": "View at source",
  "userActionUrl": "https://sema.seoul.go.kr/semaaa/front/archive/view.do?iId=21227"
}
```

Fallback stubs are not failed cards. They are intentional archive states. They must remain visibly distinct from reviewed source records and from published loose-leaf sheets.

### Publication Surface

```json
{
  "publicationSurfaceId": "PUB000001",
  "seq": 42,
  "seqLabel": "00042",
  "surfaceType": "sheet",
  "displayNumber": "GD / 1919-1933 / 00042 / M-p01",
  "historicalNodeId": "HN008",
  "movementDisplay": "MV011",
  "tier": "M",
  "layoutId": "M-001",
  "imageZone": "IMG00",
  "hasImageFrame": true,
  "workflowStatus": "published"
}
```

`IMG04` pages should render without an image frame. Do not reserve image space for `IMG04`.

Historical-node IDs may appear as metadata or search facets, but the frontend must not create a historical-node folder rail or historical-node browse route in v1.

### Surface Table Row

```json
{
  "publicationPageId": "PAGE000001",
  "tableKind": "SOURCE",
  "rowOrder": 1,
  "sourceLabel": "Title",
  "sourceValue": "Source title as found",
  "normalizedLabel": null,
  "normalizedValue": null,
  "confidence": "high",
  "warningCode": null
}
```

### Entity Detail

```json
{
  "entityId": "ENT0001",
  "entityType": "movement_period",
  "preferredLabel": "Bauhaus",
  "alternateLabels": ["Staatliches Bauhaus"],
  "dateText": "1919-1933",
  "description": "Short reviewed description",
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

### Source Record Detail

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

## Required UI Panels

### Citation Panel

Must show:

- source name;
- source record URL;
- access date;
- citation text;
- source identifier if available.

### Rights Panel

Must show:

- rights state;
- display policy;
- rights URI or rights note;
- whether local copy is permitted;
- whether full image, thumbnail, or link-only mode is allowed.

### Provenance / Uncertainty Panel

Must show:

- source metadata vs editorial metadata distinction;
- review status where available;
- uncertainty notes;
- confidence level for relations or classifications.
- authority match status where available;
- source-language label and transliteration where available;
- evidence/citation bundle for interpretive assertions.

## Required Archive-Cabinet Rendering Rules

- `SEQ` is global and must not restart inside folders.
- Historical nodes and movements are folder/filter views over the same publication surfaces.
- `MV|NONE` must be explicit in display numbers and UI metadata.
- `IMG00` must render a fixed empty archive image frame: linework/shadow plus short rights/source text and a source link. It must not render the source image, thumbnail, screenshot, preview, or local copy.
- `IMG01`, `IMG02`, and `IMG03` also assume an image frame exists; copyright/display permission determines whether that frame contains thumbnail, embed/IIIF, or open image.
- `IMG04` must render no image frame at all. Use it for pure text pages, appendices, continuation pages, citation pages, and registry pages. Treat it as a script/template signal, not a copyright level.
- Image zone codes describe image presence state only. Image size is controlled separately by tier/layout/template rules.
- Six table kinds are fixed: `SOURCE`, `NORMALIZED`, `RIGHTS`, `CLASSIFICATION`, `RELATIONS`, `CITATIONS`.
- Sparse cards are not loose-leaf sheets; they must show promotion/review status.
- `visually_resembles` must be visually marked as non-causal visual comparison.
- The UI must not display `influenced_by`, `associated_with`, `part_of`, movement membership, or identity claims without citation/evidence context.
- Public rendering must consume `imageZone` and rights decisions from the API; the frontend must not upgrade `IMG00` to image display on its own.
- `IMG00` records must be designed as first-class archive records, not as failed image cards or missing assets.
- Fallback stubs with `IMG00` must preserve the target area with an empty frame and source/search action. Fallback stubs with `IMG04` must render as text-only status rows or cards.
- The frontend must not convert fallback stubs into source records. Promotion requires source-level capture, citation, rights review, and field provenance.

## First Frontend Data Scope

The first frontend prototype should only use:

- seed data;
- global coverage seed data;
- manually reviewed source records;
- reviewed citations;
- rights-reviewed image or link policies.

It should not call ingestion jobs directly. It should not scrape. It should not depend on WebLLM.

## Design Priority

Priority order:

1. readable search results;
2. clear source and rights context;
3. historical tree navigation;
4. detail page structure;
5. filters and facets;
6. lightweight graph/timeline only after the above works.

The frontend should feel like a research gateway, not a visual showcase.
