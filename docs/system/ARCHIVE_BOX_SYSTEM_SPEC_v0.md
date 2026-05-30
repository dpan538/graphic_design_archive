# Archive Box System Spec v0

Date: 2026-05-30

## Purpose

This document is the implementation-facing system specification for the public archive box interface.

It consolidates the production, storage, surface, and interface rulebooks into one working model that can be implemented by scripts and rendered by the frontend.

## System Definition

The project is a rights-aware archive index and research framework for modern graphic design history.

The user-facing metaphor is:

```text
archive box -> folder type -> folder -> chronological record stream -> sheet/card/stub/appendix -> source
```

The system is not:

- a course;
- a textbook;
- an image gallery;
- a timeline site;
- a local archive replacing source institutions;
- a bespoke visual page per movement.

## Core System Rules

1. Time is the default sorting axis, not a container.
2. Public folder types are limited to Region, Theme, Medium, and Movement.
3. Folders are aggregation/filter views and do not own records.
4. A record can appear in many folders without changing layout.
5. Folder type can own color; records cannot.
6. Capture batches are production candidate pools.
7. Raw source payloads are preserved before normalization.
8. Source metadata, normalized metadata, rights review, and classification remain separate.
9. Every public surface must show source return, rights state, citation, status, and uncertainty when present.
10. A main sheet requires completeness >= 60 plus essential gates.

## Primary Entities

| Entity | Meaning |
|---|---|
| Source | External provider, archive, museum, database, library, website, or collection system. |
| Capture batch | One production run that fetches/source-checks a set of candidate rows. |
| Capture row | Parsed candidate derived from raw source payload. |
| Source record | Reviewed evidence record about a source object/resource/page. |
| Entity | Local normalized object/person/institution/place/text/movement/medium/theme assertion. |
| Folder | Region/Theme/Medium/Movement aggregation view. |
| Cell | Controlled folder-like research coordinate. Can be ratified or proposed. |
| Surface | Generated public archive UI/document view. |
| Publication sequence | Stable public sequence assigned to generated main surfaces. |

## Folder Types

| Folder type | Code | Owns color? | Controls layout? | Sort rule |
|---|---|---:|---:|---|
| Region | `REG` | Yes | No | Chronological |
| Theme | `THM` | Yes | No | Chronological |
| Medium | `MED` | Yes | No | Chronological |
| Movement | `MOV` | Yes | No | Chronological |

Folders aggregate all eligible surface states:

- main sheets;
- continuation sheets;
- cards;
- fallback stubs;
- proposed cell items;
- unassigned research items;
- appendix indicators.

## Time Model

Time does not create first-level navigation containers.

Every folder stream is sorted by:

1. normalized earliest date;
2. date precision;
3. normalized latest date;
4. publication sequence if present;
5. capture batch order if no sequence exists;
6. undated group.

Chronological dividers are generated inside folder streams as navigation aids:

```text
1890s
1910s
1940s
1970s
undated / date under review
```

## Record States

| State | Public surface |
|---|---|
| Raw capture | No public surface |
| Capture row | No public surface by default |
| Source record draft | Optional candidate card |
| Source record | Sheet/card/stub depending on completeness |
| Normalized entity | Sheet/card/authority text sheet |
| Main sheet eligible | Main loose-leaf sheet |
| Below threshold | Card |
| Minimal but citable | Fallback stub |
| No responsible placement | Unassigned research item |
| Repeated framework gap | Proposed cell item |
| Deprecated | Tombstone/stub |

## Surface Types

| Surface type | Template ID | Generated when |
|---|---|---|
| Archive box overview | `box.overview.v0` | Always |
| Folder cover | `folder.cover.v0` | For every public folder |
| Folder index | `folder.index.v0` | For every folder with members |
| Main loose-leaf sheet | `sheet.main.v0` | Completeness >= 60 and gates pass |
| Text sheet | `sheet.text.v0` | Main sheet eligible with IMG04/text nature |
| Image placeholder sheet | `sheet.img00.v0` | Main sheet eligible with IMG00 |
| Continuation sheet | `sheet.continuation.v0` | Main sheet overflow |
| Compound sheet | `sheet.compound.v0` | Weak records form one intellectual unit |
| Card | `card.record.v0` | Completeness 45-59 |
| Fallback stub | `stub.fallback.v0` | Completeness 25-44 or source-minimal |
| Unassigned item | `item.unassigned.v0` | Valid/valuable but no responsible placement |
| Proposed cell item | `item.proposed-cell.v0` | Repeated evidence suggests missing cell |
| Rights appendix | `appendix.rights.v0` | Rights explanation exceeds stamp |
| Relation appendix | `appendix.relations.v0` | Relation density exceeds sheet |
| Citation appendix | `appendix.citations.v0` | Citation list exceeds sheet |
| Registration card | `registry.card.v0` | Folder/classification event summary |

## Main Sheet Gates

A record cannot become a main sheet unless all essential gates pass:

- stable internal ID;
- public label/title;
- source name;
- source URL or source locator;
- access date;
- rights state;
- IMG state;
- record type/family;
- date/date_text or declared undated state;
- citation seed;
- at least one folder/proposed/unassigned placement.

Then calculate completeness:

| Category | Points |
|---|---:|
| Identity | 20 |
| Source/citation | 20 |
| Date/place | 15 |
| People/institution | 10 |
| Classification/folder membership | 15 |
| Rights/IMG state | 10 |
| Description/scope note | 10 |

Outcome:

- `60-100`: main sheet, if gates pass.
- `45-59`: card, unless compounded.
- `25-44`: fallback stub.
- `<25`: unassigned/internal candidate.

## IMG State Rules

| IMG | Layout effect | Rights meaning |
|---|---|---|
| IMG00 | Image bay exists, but empty. | Image not displayed because rights/evidence insufficient. |
| IMG01 | Image bay shows controlled thumbnail. | Thumbnail candidate only. |
| IMG02 | Image bay shows/links source-hosted viewer or IIIF. | No local copy. |
| IMG03 | Image bay shows open/reusable candidate. | Explicit open evidence required. |
| IMG04 | No image bay. Text/table layout expands. | No-image-frame page state. |

## Public Route Model

Suggested routes:

```text
/
/folders
/folders/region
/folders/theme
/folders/medium
/folders/movement
/folders/{folderType}/{folderSlug}
/folders/{folderType}/{folderSlug}/index
/records/{seqOrRecordSlug}
/records/{seqOrRecordSlug}/p/{page}
/cards/{cardSlug}
/stubs/{stubSlug}
/proposed/{proposedCellSlug}
/unassigned
/sources/{sourceSlug}
/search
```

WebLLM/global search remains a placeholder in v0. Static/search-index routes should still exist.

## Surface Payload Contract

Each generated surface payload should include:

```text
surface_id
surface_type
template_id
status
display_number
internal_id
seq_id
title
date_display
date_sort
folder_memberships
source_summary
rights_summary
img_state
content_modules
actions
appendices
provenance
updated_at
```

The frontend should render surface payloads, not raw capture rows.

## Data Flow

```text
source_registry
capture_batches
capture_rows
cell_assignments
source_reviews
rights_reviews
source_records
entities
relations
publication_surface_inputs
surface_payloads
folder_indexes
search_documents
```

## Implementation Priority

1. Surface payload schema.
2. Folder registry and folder membership generation.
3. Completeness scoring script.
4. Surface assignment script.
5. Folder cover/index payload generation.
6. Main sheet/card/stub payload generation.
7. Static frontend rendering.
8. WebLLM search placeholder becomes real search later.

## Open Questions

- Whether proposed cells are public immediately or only after acceptance.
- Whether `IMG01` is allowed in first public release.
- Whether registration cards are public in v0.
- Whether legacy `ECAP001` is migrated immediately to `CB001-R0001` or kept as alias until next batch.
