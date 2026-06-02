# Surface Generation Pipeline v0

Date: 2026-05-30

## Purpose

This document defines how project data becomes renderable archive surfaces.

The pipeline must not render raw capture rows directly as final public pages. It should transform reviewed or staged production records into explicit surface payloads that can be rendered consistently.

## Pipeline Overview

```text
source registry
capture batches
raw payloads
capture rows
cell assignments
source reviews
rights reviews
source records
normalized entities
relations
completeness scoring
surface assignment
surface payload generation
folder aggregation generation
search index generation
static/public rendering
```

## Pipeline Stages

| Stage | Input | Output | Script owner |
|---|---|---|---|
| Capture | source registry, source query plan | raw payloads, capture rows | ingest |
| Image-state evaluation | capture rows, source policy | IMG00-IMG04 fields | ingest/rights |
| Cell assignment | capture rows, folder/cell authority | existing/proposed/unassigned assignments | classification |
| Source review | capture rows, raw payloads | source record drafts | review |
| Rights review | source records, source policy | rights disposition | review |
| Completeness scoring | source/entity/review data | completeness score and gates | publish |
| Surface assignment | score, state, IMG, volume | surface type/template ID | publish |
| Payload generation | surface inputs | JSON payloads | publish |
| Folder aggregation | surface payloads, memberships | folder covers/indexes | publish |
| Search indexing | public payloads | searchable documents | publish/search |

## Required Intermediate Data

Before rendering, every candidate needs a surface input row or object with:

- stable internal ID;
- record state;
- source name;
- source URL or source locator;
- source identifier if available;
- title/label;
- date/date_text;
- normalized date sort fields when available;
- record family/type;
- IMG state;
- rights summary;
- citation seed;
- folder memberships or proposed/unassigned state;
- completeness score;
- surface eligibility decision;
- uncertainty notes;
- raw/canonical provenance pointers.

## Surface Assignment Logic

Pseudocode:

```text
if record_state == proposed_cell:
  surface_type = item.proposed-cell
elif record_state == unassigned:
  surface_type = item.unassigned
elif record_state == fallback_stub:
  surface_type = stub.fallback
elif essential_gates_fail:
  surface_type = stub.fallback or item.unassigned
elif qualifies_as_research_unit and completeness_score >= 80 and source_reading_text_length >= 160:
  if is_compound:
    surface_type = sheet.compound
  elif img_state == IMG04:
    surface_type = sheet.text
  elif img_state == IMG00:
    surface_type = sheet.img00
  else:
    surface_type = sheet.main
elif completeness_score >= 75:
  surface_type = sheet.subsheet
elif completeness_score >= 55:
  surface_type = appendix.or_text_sheet
elif completeness_score >= 40:
  surface_type = card.with_slip_or_parent_attachment
elif completeness_score >= 20:
  surface_type = card.record
else:
  surface_type = bookmark.candidate or item.unassigned
```

Hierarchy rule:

```text
main sheet
  -> subsheet
    -> appendix
    -> text sheet
    -> card
      -> slip
    -> bookmark
```

`main sheet` is the highest public research unit, not the default renderer.
Many records that previously became main sheets should become `subsheet`
records. A subsheet may still have its own appendix, text sheet, card, slip, or
bookmark children. Appendix is mainly tabular/evidence material; text sheet is
reading-led image/text material; card is compact visual/title material; slip is
card-bound text supplement; bookmark is the fallback pointer.

## Surface Payload Shape

All public surface payloads should share a base shape:

```json
{
  "surfaceId": "SURF000001",
  "surfaceType": "sheet.main",
  "templateId": "sheet.main.v0",
  "status": "candidate",
  "displayNumber": "GD/...",
  "displaySlug": "gd-...",
  "seqId": "SEQ000001",
  "internalId": "SRC001",
  "sourceRecordIds": ["SRC001"],
  "entityIds": ["ENT000001"],
  "title": "Record title",
  "date": {
    "display": "1917/18",
    "start": 1917,
    "end": 1918,
    "precision": "year-range",
    "sortKey": "1917"
  },
  "folders": [
    {"type": "movement", "id": "C02", "label": "Polish Poster School"}
  ],
  "img": {
    "state": "IMG00",
    "frameBehavior": "empty_rights_frame",
    "policy": "do_not_display",
    "basis": "No item-level display permission captured."
  },
  "rights": {
    "state": "link_only",
    "localCopyPermitted": false,
    "reviewRequired": true,
    "basis": "..."
  },
  "source": {
    "name": "Provider",
    "url": "https://example.org/record",
    "identifier": "provider-id",
    "accessDate": "2026-05-30",
    "actionLabel": "View at source"
  },
  "contentModules": [],
  "appendices": [],
  "uncertainty": [],
  "provenance": {
    "captureBatchId": "CB001",
    "captureRowId": "CB001-R0001",
    "rawPayloadPath": "data/capture_batches/CB001/raw/CB001-R0001/response_body.json",
    "generatedAt": "2026-05-30T00:00:00Z"
  }
}
```

## Content Modules

Surface payloads should compose modules rather than bespoke layouts:

| Module | Use |
|---|---|
| `module.header` | ID, title, date, status |
| `module.img-zone` | IMG00-IMG04 behavior |
| `module.rights-stamp` | Rights and image policy |
| `module.source-action` | View at source |
| `module.metadata-table` | Source/normalized facts |
| `module.classification-table` | Folder memberships and terms |
| `module.relations-table` | Related records/entities |
| `module.citation-block` | Citation and access date |
| `module.uncertainty-strip` | Warnings/context |
| `module.appendix-list` | Links to p02/p03 |
| `module.registration-log` | Created/verified/updated |

## Folder Generation

Folder generation uses surface payloads, not raw records.

For every folder:

1. collect member surfaces;
2. deduplicate by stable record/surface ID;
3. sort chronologically;
4. bucket by year/decade/date span;
5. count surface mix;
6. count IMG00-IMG04;
7. count source providers;
8. generate folder cover payload;
9. generate folder index payload.

Folder cover payload:

```json
{
  "folderId": "REG001",
  "folderType": "region",
  "templateId": "folder.cover.v0",
  "title": "Japan",
  "dateSpan": "1920-2008",
  "counts": {
    "total": 42,
    "mainSheets": 18,
    "cards": 12,
    "fallback": 5,
    "proposed": 3,
    "unassigned": 4
  },
  "imgDistribution": {
    "IMG00": 20,
    "IMG01": 4,
    "IMG02": 2,
    "IMG03": 6,
    "IMG04": 10
  },
  "chronologyBuckets": [],
  "relatedFolders": []
}
```

## Search Generation

Search index should be generated from public surface payloads plus selected registry/source records.

Index fields:

- title;
- normalized title;
- date/date_text;
- source;
- people/institutions;
- folders;
- record type;
- IMG state;
- rights state;
- surface type;
- status;
- citation;
- uncertainty terms.

Search rank should prefer:

1. main sheets;
2. text sheets / compound sheets;
3. cards;
4. folder covers;
5. proposed cell items;
6. fallback stubs;
7. unassigned items;
8. appendices.

## Publication Sequence

Assign `SEQ` only when a surface is ready to become a stable public sheet/card/stub.

Rules:

- `SEQ` is global.
- Never reuse a `SEQ`.
- Keep gaps if records are withdrawn.
- Multi-page surfaces share the same `SEQ` with `p001`, `p002`, etc.
- Folders do not get `SEQ`; they get folder IDs.

## Display Number Generation

Display number is generated from publication metadata:

```text
GD/{ERA}/{SEQ}/{TIER}-p{PAGE}
```

Rules:

- `GD/...` is user-facing, not a primary key.
- Do not encode `HN` or movement membership in the public display number.
- Store historical-node and movement references as classification/folder metadata.
- Use safe `display_slug` for URLs/files.
- If display-number grammar changes after publication, preserve old display aliases.

## Completeness Scoring Script

Future script:

```text
scripts/publish/score_surface_completeness.py
```

Inputs:

- source records;
- capture rows;
- cell assignments;
- rights reviews;
- citations;
- relations.

Outputs:

- `surface_completeness_scores.csv`;
- eligibility status;
- missing essential gates;
- recommended surface type.

## Surface Payload Generator

Future script:

```text
scripts/publish/generate_surface_payloads.py
```

Outputs:

```text
data/publication_surfaces/payloads/
  surfaces.jsonl
  folder_covers.jsonl
  folder_indexes.jsonl
  search_documents.jsonl
```

## Current Flat-File Bridge

Until the project is reorganized into the target directory tree, generation may read:

- `data/capture_batch_001_records.csv`
- `data/capture_batch_001_cell_assignments.csv`
- `data/capture_batch_001_cell_summary.csv`
- `data/source_registry.csv`
- `data/manual_source_records_index.csv`
- `data/remediation_source_records_index.csv`
- `data/fallback_source_stubs.csv`

But generated public surfaces should go into a dedicated output folder, not back into raw/capture CSVs.

## Validation Rules

Every generated surface payload must validate:

- has `surfaceId`;
- has `surfaceType`;
- has `templateId`;
- has `status`;
- has source or explicit no-source reason;
- has rights/IMG state;
- has citation seed if public;
- has folder/proposed/unassigned placement;
- has provenance pointer;
- does not expose local image path unless `localCopyPermitted=true`;
- does not display image for `IMG00`;
- does not include image bay for `IMG04`.

## First Implementation Target

The first surface generation implementation should generate from capture batch 001:

- proposed cell item payloads;
- unassigned item payloads;
- folder cover payloads for folders with capture assignments;
- folder index payloads;
- card/stub previews for below-threshold capture rows.

It should not yet mint final `SEQ` or final `GD/...` display numbers until source review and rights review gates are implemented.
