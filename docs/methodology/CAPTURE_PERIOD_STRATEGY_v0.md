# Capture Period Strategy v0

Date: 2026-05-30

## Purpose

This document defines the staged crawl periods for the archive preview and the
promotion rules that keep the archive from becoming a table-only checklist.

The current `1830-1930` payload is a visual-verification batch, not complete
coverage of all pre-1930 graphic design history.

## Period Segmentation

Time is still a sorting axis, not a historical container. Period batches are
used only to manage capture scope and frontend validation.

| Batch | Date rule | Working role |
|---|---|---|
| `1830-1930` | records whose end year is `<= 1930` | early commercial print, posters, trade cards, lithography, early advertising |
| `1930-1970` | records whose end year is `1931-1970` | modernism, propaganda, corporate identity, postwar design institutions, international style, regional modernisms |
| `1970-2000` | records whose end year is `1971-2000` | postmodernism, political graphics, desktop publishing, late print culture, early interface culture |
| `2000-2026` | records whose end year is `2001-2026` | networked visual communication, web/platform graphics, social campaigns, contemporary archive records |

If a record has a start/end range, the **end year** controls period assignment.
If the end year is unknown, use the latest defensible year in the source date
text. If no defensible year exists, keep it in `undated/date under review`.

## Current Status

The `1830-1930` preview contains:

- 60 surfaces
- 12 folders
- date range 1830-1930

This is not comprehensive. It is only the first usable period payload for
testing folder navigation, image states, source links, rights display, and sheet
layout.

The active frontend preview has now advanced to the first `1930-1970`
midcentury capture batch:

- 95 surfaces
- 16 folders
- date range 1931-1970
- image states: `IMG00` 25, `IMG01` 24, `IMG02` 8, `IMG03` 0, `IMG04` 38

This is also not comprehensive. It is the first production candidate pool for
the period and reveals a follow-up need for more open-image and text-rich
sources.

## 1930-1970 Capture Requirements

The next production capture period is `1930-1970`.

This period must prioritize sources that provide at least one of the following:

- object/collection descriptions long enough to support a reading paragraph;
- exhibition, catalogue, or collection essays;
- source-side rights statements;
- IIIF, thumbnails, source-hosted viewers, or explicit open images;
- authority records for people, studios, schools, institutions, and movements;
- bibliographic/contextual texts that can become `IMG04` reading pages.

## Reading Gate

A main sheet should not be promoted if it only fills tables.

Recommended publication behavior:

| Reading evidence | Surface outcome |
|---|---|
| 180+ characters of captured description/notes/subjects/context | eligible for main sheet |
| 80-179 characters plus strong image/source evidence | eligible for main sheet, but flagged as thin text |
| less than 80 characters and no contextual source | card, compound child, fallback stub, or internal capture row |
| source is primarily textual/bibliographic | `IMG04` text sheet if citation and source link are strong |

The six specification tables remain the evidence layer. They should not be the
primary reading experience.

## Image Gate

For `1930-1970`, every candidate should preserve one of these visible states:

- `IMG00`: empty image frame plus source/right reason;
- `IMG01`: controlled thumbnail only when source policy allows it;
- `IMG02`: source-hosted viewer/IIIF/link behavior;
- `IMG03`: open image only with item-level evidence;
- `IMG04`: no image frame, but only for real text/authority/bibliographic pages.

Do not use `IMG04` merely because a parser failed to find an image. If the
source describes a visual object, default to `IMG00` until rights evidence is
reviewed.

## Source Direction for 1930-1970

The next crawl should mix object-rich and text-rich sources:

- museum APIs and collection records for works/images;
- national library and archive records for posters, manuals, periodicals, and
  public information graphics;
- design archive pages for institutions and exhibitions;
- bibliographic/reference sources for movements, schools, designers, and
  corporate design systems;
- regionally distributed sources so the period does not collapse into a
  Western modernism sample.

The current next-step plan is documented in
`NEXT_1931_1970_EXPANSION_PLAN_v0.md`. The recommended mixed source set is:

- NDL Digital Collections / NDL Search;
- Hemeroteca Digital Brasileira or Hemeroteca Nacional Digital de Mexico;
- Chinese Posters;
- Getty Research Portal plus Getty Vocabularies;
- Europeana for targeted gap repair.

Secondary alternates include Palestinian Museum Digital Archive, M68
Ciudadanias en Movimiento, South Asia Open Archives, African Activist Archive,
Te Papa, and State Library of NSW.

## Frontend Preview Rule

Only the active period payload should sync into:

- `frontend/src/data/public_surface_mock_v0.json`
- `frontend/public/data/public_surface_mock_v0.json`

Research batches and global stress batches must not sync to frontend unless the
command explicitly asks for a stress preview.
