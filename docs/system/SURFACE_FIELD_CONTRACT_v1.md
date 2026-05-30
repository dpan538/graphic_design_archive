# Surface Field Contract v1

**Status:** Frozen field contract for static publication surfaces.  
**Date:** 2026-05-30  
**Applies to:** DB export, generated static payloads, frontend rendering, future ingest scripts.

This file freezes what can be filled into the public archive surfaces.

The frontend may change visual styling, spacing, typography, and responsive behavior, but it should not invent new evidence fields outside this contract. Future ingest scripts should fill these fields, generate static payloads, and let the frontend read them as finished archive surfaces.

## 1. Frozen Public System

### Public Folder Types

The only public folder types are:

```text
region | theme | medium | movement
```

Time is a sorting axis inside every folder, not a public folder type.

Historical nodes (`HN*`) remain research/classification/search metadata. They are not folder tabs, folder routes, or display-number segments.

### Public Surface Types

The public surface types are:

```text
sheet
card
fallback_stub
appendix
folder_cover
folder_index
registration_card
bookmark
```

The first frontend must support at minimum:

```text
sheet
card
fallback_stub
```

### Template IDs

The minimum frozen template IDs are:

```text
sheet.main.v1
sheet.img00.v1
sheet.text.v1
card.sparse.v1
stub.fallback.v1
appendix.table.v1
folder.cover.v1
folder.index.v1
```

Older `*.v0` template IDs in mock data can be treated as aliases during prototype work.

### Display Number

Public display number:

```text
GD / {ERA} / {SEQ} / {TIER}-p{PAGE}
```

Examples:

```text
GD / 1894 / STAGED-0002 / M-p01
GD / 1917-1918 / SEQ000001 / M-p01
GD / undated / SEQ000211 / S-p01
```

Rules:

- Do not encode `HN`, movement ID, region ID, folder ID, or source ID in display numbers.
- `SEQ` is global and never restarts inside folders.
- During visual validation, `STAGED-*` is allowed.
- Final `SEQ*` is minted only after source review and rights review pass.
- If a published surface is corrected, preserve old display aliases in a correction/deprecation note rather than reusing the number.

## 2. Static Publication Flow

The pipeline is:

```text
capture/manual input
-> source record
-> normalized assertions
-> rights review
-> classification/folder membership
-> completeness route
-> publication surface payload
-> generated static files
-> frontend reads static files
```

The frontend should not dynamically reconstruct archive pages from raw DB rows.

The next generated payload target is:

```text
generated/public_surfaces_v1.json
```

It must keep the top-level shape:

```json
{
  "meta": {},
  "folderTypes": [],
  "folders": [],
  "surfaces": []
}
```

## 3. Empty Value Rules

Use these exact display conventions:

| Condition | Stored value | Public display |
|---|---|---|
| Unknown but expected | `null` | `Unknown` |
| Not applicable | `"not_applicable"` | `Not applicable` |
| Undated | `dateText: "undated"` | `undated` |
| Uncertain | value plus `confidence: "low"` | show uncertainty marker |
| Rights not reviewed | `rights.state: "rights_review_required"` | show rights stamp |
| Image not displayable | `image.state: "IMG00"` | empty image frame |
| No image frame | `image.state: "IMG04"` | no image area |
| Link-only record | `surfaceType: "fallback_stub"` | source/path action only |

Do not hide missing or uncertain data in order to make the page look cleaner.

## 4. Surface Base Payload

Every public surface must include these fields.

```ts
type Surface = {
  surfaceId: string
  sourceRecordId: string | null
  surfaceType: "sheet" | "card" | "fallback_stub" | "appendix" | "folder_cover" | "folder_index" | "registration_card" | "bookmark"
  templateId: string
  displayNumber: string
  displaySlug: string
  seqLabel: string
  pageLabel: string
  tier: "S" | "M" | "L" | "XL" | "XXL"
  workflowStatus: "draft" | "staged" | "published" | "deprecated"
  title: string
  subtitle: string | null
  creator: string | null
  dateText: string
  dateStart: number | null
  dateEnd: number | null
  sortYear: number | null
  placeText: string | null
  objectType: string | null
  medium: string | null
  languageScript: string | null
  sourceName: string | null
  sourceUrl: string | null
  accessDate: string | null
  completenessScore: number
  reviewGates: ReviewGates
  image: ImageState
  rights: RightsState
  folders: FolderMembership[]
  authorityRefs: AuthorityRefs
  tables: SurfaceTable[]
  warnings: SurfaceWarning[]
  provenance: SurfaceProvenance
  correction: CorrectionState | null
}
```

### Required Public Fields

A surface cannot be public unless it has:

- `surfaceId`
- `surfaceType`
- `templateId`
- `displayNumber` or `provisionalDisplayNumber` during staging
- `seqLabel`
- `pageLabel`
- `tier`
- `title`
- `dateText`
- `sourceName` or explicit fallback source/path label
- `sourceUrl` or explicit fallback/search path
- `accessDate`
- `image.state`
- `rights.state`
- at least one folder membership, proposed folder, or unassigned/fallback state
- all six table kinds, even if some tables only contain uncertainty/fallback rows

## 5. Review Gates

```ts
type ReviewGates = {
  sourceUrl: boolean
  sourceCaptured: boolean
  rightsReviewed: boolean
  dateKnown: boolean
  classificationKnown: boolean
  citationPresent: boolean
}
```

Routing meaning:

| Route | Condition |
|---|---|
| `sheet` | essential gates pass and completeness >= 60 |
| `card` | enough identity exists but completeness is 45-59, or editorially marked sparse |
| `fallback_stub` | source/path is relevant but record remains incomplete, usually 25-44 |
| `unassigned_internal` | below public threshold; do not render as public surface unless grouped |

Frontend reads the route; frontend does not calculate it.

## 6. Image State

```ts
type ImageState = {
  state: "IMG00" | "IMG01" | "IMG02" | "IMG03" | "IMG04"
  hasImageFrame: boolean
  url: string | null
  thumbnailUrl: string | null
  iiifManifestUrl: string | null
  credit: string | null
  licenseLabel: string | null
  licenseUrl: string | null
  imageUsePolicy: string
  evidence: string | null
}
```

Rules:

- `IMG00`: image frame exists, source image is not shown.
- `IMG01`: constrained thumbnail only.
- `IMG02`: source-served embed/IIIF only.
- `IMG03`: open/reusable image only with evidence.
- `IMG04`: no image frame.

Unknown image rights default to `IMG00`.

## 7. Rights State

```ts
type RightsState = {
  state: string
  displayPolicy: string
  label: string
  rightsText: string | null
  rightsUri: string | null
  rightsBasis: string | null
  localCopyPermitted: boolean
  rightsReviewRequired: boolean
  reviewedBy: string | null
  reviewedAt: string | null
  sourceReturnRequired: boolean
}
```

Minimum public behavior:

- Always show rights state.
- Always show source return.
- Do not display image content when `localCopyPermitted` is false unless the image state explicitly permits source-hosted display.
- Rights text from the source is not the same as permission; keep `rightsText` and `displayPolicy` separate.

## 8. Folder Membership

```ts
type FolderMembership = {
  folderId: string
  type: "region" | "theme" | "medium" | "movement"
  slug: string
  title: string
  confidence: "high" | "medium" | "low" | "unknown"
  basis: string | null
}
```

Rules:

- Folder IDs are public folder-view IDs, such as `FOL-MEDIUM-POSTER`.
- Authority IDs live in `authorityRefs`.
- A folder does not own or duplicate the surface.
- Folder membership may change; display number should not.

## 9. Authority References

```ts
type AuthorityRefs = {
  historicalNodeIds: string[]
  movementIds: string[]
  regionalMovementIds: string[]
  regionIds: string[]
  geoIds: string[]
  mediaIds: string[]
  themeKeys: string[]
  personEntityIds: string[]
  institutionEntityIds: string[]
  sourceIds: string[]
}
```

Authority references support research integrity. They are not all public headings.

## 10. Six Fixed Tables

Every surface carries six table kinds in this order:

```text
SOURCE
NORMALIZED
RIGHTS
CLASSIFICATION
RELATIONS
CITATIONS
```

Each table uses the same row shape:

```ts
type SurfaceTable = {
  kind: "SOURCE" | "NORMALIZED" | "RIGHTS" | "CLASSIFICATION" | "RELATIONS" | "CITATIONS"
  title: string
  rows: SurfaceTableRow[]
}

type SurfaceTableRow = {
  key: string
  label: string
  value: string | number | boolean | null
  valueDisplay: string
  sourceField: string | null
  normalizedField: string | null
  confidence: "high" | "medium" | "low" | "unknown"
  basis: string | null
  warningCode: string | null
  citationIds: string[]
}
```

The prototype mock may still use compact two-column rows, but generated v1 payloads should use the row object shape above.

## 11. SOURCE Table

Purpose: preserve source-provided or source-adjacent fields without rewriting them as local interpretation.

Required rows:

| key | label | value source |
|---|---|---|
| `source_id` | Source ID | source registry |
| `source_name` | Source name | source registry |
| `source_identifier` | Source identifier | source/object id |
| `source_title` | Source title | raw/source title |
| `source_creator` | Source creator | raw/source creator/maker |
| `source_date` | Source date | raw/source date |
| `source_place` | Source place | raw/source place |
| `source_object_type` | Source object type | raw/source type/classification |
| `source_medium` | Source medium | raw/source medium/material |
| `source_collection` | Collection | source collection/department |
| `source_rights_text` | Source rights text | raw rights statement |
| `source_url` | Source URL | canonical record URL |
| `access_date` | Access date | capture/access date |

Allowed extra rows:

- source language;
- source dimensions;
- source publisher;
- source repository;
- source API endpoint;
- raw payload path.

## 12. NORMALIZED Table

Purpose: show the local normalized fields used by the archive system.

Required rows:

| key | label |
|---|---|
| `normalized_title` | Normalized title |
| `normalized_creator` | Normalized creator |
| `date_text` | Date text |
| `date_start` | Date start |
| `date_end` | Date end |
| `sort_year` | Sort year |
| `place_text` | Place |
| `object_type` | Object type |
| `medium` | Medium |
| `language_script` | Language / script |
| `description_summary` | Description summary |

Rules:

- Descriptions must be short, factual, and sourced.
- Do not use AI-generated interpretation as evidence.
- If normalization is uncertain, mark confidence and basis.

## 13. RIGHTS Table

Purpose: make rights and image display decisions visible.

Required rows:

| key | label |
|---|---|
| `rights_state` | Rights state |
| `display_policy` | Display policy |
| `image_state` | Image state |
| `image_use_policy` | Image use policy |
| `local_copy_permitted` | Local copy permitted |
| `source_return_required` | Source return required |
| `rights_text` | Rights text |
| `rights_uri` | Rights URI |
| `rights_basis` | Rights basis |
| `rights_review_required` | Rights review required |
| `reviewed_by` | Reviewed by |
| `reviewed_at` | Reviewed at |

Rules:

- `IMG00` is a valid public state, not a failure.
- `IMG04` means no image frame, not a rights level.
- A raw image URL never upgrades rights by itself.

## 14. CLASSIFICATION Table

Purpose: show how this surface is filed and what authority terms it touches.

Required rows:

| key | label |
|---|---|
| `folder_region` | Region folder |
| `folder_theme` | Theme folder |
| `folder_medium` | Medium folder |
| `folder_movement` | Movement folder |
| `historical_nodes` | Historical node refs |
| `movement_refs` | Movement refs |
| `regional_movement_refs` | Regional movement refs |
| `geo_refs` | Geography refs |
| `media_refs` | Medium / technology refs |
| `classification_basis` | Classification basis |
| `classification_confidence` | Classification confidence |

Rules:

- Public folder membership and authority refs must remain separate.
- `HN*` can appear here as refs, but not as folder tabs.
- Low confidence must remain visible.

## 15. RELATIONS Table

Purpose: show relationships without turning them into narrative prose.

Each relation row must use:

| key | label |
|---|---|
| `predicate` | Predicate |
| `target_label` | Target |
| `target_type` | Target type |
| `target_id` | Target ID |
| `confidence` | Confidence |
| `basis` | Basis |
| `citation` | Citation |
| `warning` | Warning |

Allowed predicates include:

- `created_by`
- `published_by`
- `held_by`
- `part_of`
- `associated_with`
- `classified_as`
- `mentions`
- `discussed_in`
- `possibly_same_as`
- `visually_resembles`

Rules:

- `visually_resembles` must show a warning.
- `influenced_by` requires documentary or scholarly evidence.
- Do not infer influence from visual similarity alone.

## 16. CITATIONS Table

Purpose: make every public claim traceable.

Each citation row must use:

| key | label |
|---|---|
| `citation_id` | Citation ID |
| `citation_type` | Citation type |
| `label` | Label |
| `url` | URL |
| `access_date` | Access date |
| `bibliographic_text` | Bibliographic text |
| `supports` | Supports |

Minimum citation rows:

- source record URL;
- source access date;
- rights/source terms URL when relevant;
- scholarly/book citation when a historical claim goes beyond source metadata.

## 17. Surface-Type Specific Rules

### Sheet

Use for records with enough information to fill the main public page.

Minimum:

- `completenessScore >= 60`;
- source return;
- rights state;
- classification/folder placement;
- all six tables.

### Card

Use for sparse but meaningful records.

Cards still require:

- title or target label;
- source/path;
- rights state;
- folder placement or fallback area;
- reason not promoted to sheet.

Cards must not pretend to be complete records.

### Fallback Stub

Use when the area/source/path must remain visible but the record is not ingestable enough.

Fallback stubs require:

- target label;
- source/search path or replacement path;
- not-ingested reason;
- expected image state, usually `IMG00`;
- user action label, usually `View at source`.

### Appendix

Use for overflow tables, continuation text, citations, relation lists, or pure-text pages.

Appendix pages usually use `IMG04`.

## 18. Folder Payload

```ts
type Folder = {
  folderId: string
  type: "region" | "theme" | "medium" | "movement"
  slug: string
  title: string
  dateStart: number | null
  dateEnd: number | null
  scopeNote: string
  surfaceIds: string[]
  relatedFolderIds: string[]
  authorityRefs: Partial<AuthorityRefs>
  counts: {
    sheet: number
    card: number
    fallback_stub: number
    appendix: number
    IMG00: number
    IMG01: number
    IMG02: number
    IMG03: number
    IMG04: number
  }
}
```

Folder order:

1. sort by `sortYear`;
2. then `seqLabel`;
3. then `surfaceId`.

## 19. Provenance

```ts
type SurfaceProvenance = {
  captureBatchId: string | null
  captureRowId: string | null
  rawPayloadPath: string | null
  sourceRecordCreatedAt: string | null
  generatedAt: string
  generatorVersion: string
  lastVerifiedAt: string | null
}
```

Every generated surface must state where it came from.

## 20. Correction and Deprecation

```ts
type CorrectionState = {
  status: "active" | "corrected" | "deprecated"
  replacesSurfaceId: string | null
  replacedBySurfaceId: string | null
  reason: string | null
  changedAt: string | null
}
```

Do not silently overwrite public records after publication.

If a source changes, a rights decision changes, or a classification is corrected, record the correction state.

## 21. Freeze Boundary

Frozen:

- folder types;
- public display-number grammar;
- surface types;
- IMG00-IMG04 meanings;
- six table kinds and order;
- required base surface fields;
- source return and rights stamp;
- static generated-payload approach.

Allowed to append:

- new folders;
- new source records;
- new authority refs;
- new table rows using existing table kinds;
- new citations;
- new relation rows using governed predicates;
- new warnings;
- new templates that still consume the same field contract.

Not allowed without a new contract version:

- adding a fifth public folder type;
- adding a seventh required table kind;
- removing source return;
- hiding rights state;
- putting HN back into public folder routes or display numbers;
- changing IMG00 or IMG04 behavior;
- making the frontend reconstruct pages from raw capture data.

