# Research Dossier + Export Model v0

Date: 2026-06-03

## Purpose

The archive should not behave as a flat sequence of independent sheets. A
published research unit is a dossier: one anchor page plus a controlled sequence
of supporting pages. Folder views remain filters over dossiers and pages, not
containers that own records.

This model supports:

- a main sheet as the dossier anchor;
- multiple sub sheets under the same research unit;
- one or more text pages for each sheet-level member;
- evidence appendices inherited at dossier level when possible;
- cards, slips, and bookmarks as lower-strength or provisional supports;
- page selection and PDF export with archival marks on every exported page.

## Page Hierarchy

The intended hierarchy is:

1. `main_sheet`
   - Anchor and cover of a research unit.
   - Must have strong identity evidence, source return, rights state, and enough
     visual/textual evidence to support a research dossier.
2. `subsheet`
   - A member item, variant, manifestation, issue, campaign component, source
     witness, or related support record under a main sheet.
   - It should not be promoted to a main sheet unless it can stand as an
     independent research unit.
3. `text_page`
   - Required for every sheet-level member.
   - Carries readable source-derived prose, OCR/excerpt material, catalogue
     context, project methodology notes, and uncertainty.
   - A text page may be pure text or image + text, but it should not be a table
     ledger.
4. `appendix`
   - Evidence ledger: rights, source/citation, relations/classification,
     protocol/context, statement, typed index.
   - Should be emitted once per evidence class per dossier unless a child record
     has materially different evidence.
5. `card`
   - Compact citable record for thin but stable evidence.
6. `slip`
   - Optional companion to a card when the record has more prose than a card can
     hold but not enough evidence to become a sheet.
7. `bookmark`
   - Lowest-strength fallback: source pointer, unresolved lead, reading marker,
     method note, or external-location note.

## Dossier Contract

The generated payload now exposes `researchDossiers`.

Each dossier includes:

- `dossierId`
- `anchorSurfaceId`
- `anchorType`
- `sourceScope`
- `title`
- `dateStart`
- `dateEnd`
- `folderIds`
- `pageCount`
- `pageSequence`
- `exportPolicy`
- `groupingBasis`

Each `pageSequence` entry includes:

- stable `pageId`
- `pageType`
- `surfaceId`
- display number
- title
- image state
- layout id when known
- source name and source URL
- rights state
- exportability flag

This is the data object that future left-side thumbnails, page checkboxes, and
PDF export should read.

## Export Rules

PDF export should use the dossier sequence, not the flat folder sequence.

Export behavior:

- users can select all pages or chosen pages from one dossier;
- every exported page receives a stable archive mark;
- every exported page keeps its source/citation/rights state;
- the PDF includes a dossier cover or export manifest;
- local image copying remains false by default unless the image state and
  rights policy explicitly allow it;
- IMG00 pages export as blank/withheld image evidence, not as generated image
  substitutes;
- source-return links must remain visible in the export.

Archive mark fields should include:

- project prefix;
- dossier id;
- page id;
- surface id;
- display number;
- source name;
- image state;
- export date;
- rights/citation note.

## Grouping Rules

Do not group pages merely because they share a folder, country, date, movement,
or visual resemblance.

Allowed grouping evidence:

- same source identifier, accession number, call number, issue number, or
  persistent id;
- same campaign, publication title, issue, object set, series, exhibition, or
  documented production pattern;
- same work but different manifestation, carrier, edition, language, or digital
  surrogate;
- repeated title/source-generic records that are better read as a cluster;
- explicit source relation or citation relation.

If grouping evidence is weak, keep the record as a single-anchor dossier or a
candidate support packet. Do not collapse it into a main sheet.

## Current Status

Current generated payload:

- `researchDossiers`: 1417
- `compound_or_series_cluster`: 21
- largest dossier: 33 pages
- most dossiers still have 2-3 pages because the linkage pass has not yet been
  expanded.

This is correct for a conservative first contract, but not the final research
archive shape. The next data task is a linkage/grouping pass that promotes
source series, campaigns, publication issues, visual programs, and repeated
source clusters into multi-page dossiers.
