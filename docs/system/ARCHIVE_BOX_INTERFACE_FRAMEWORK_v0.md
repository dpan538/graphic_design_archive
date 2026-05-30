# Archive Box Interface Framework v0

Date: 2026-05-30

Source report:

- `Rights-Aware Archive Box Interface Framework for Modern Graphic Design History.docx`

## Purpose

This document defines the public interface framework: what users see, which layout modules exist, and how the archive-box metaphor behaves.

The user sees a box of folders and papers, not a gallery, course, or timeline website.

## Core Model

```text
Archive Box
-> Folder type entry: Region / Theme / Medium / Movement
-> Folder cover
-> Chronological folder index
-> Main sheets / cards / stubs / proposed items / unassigned items
-> Sheet appendices / source / citation
```

Time is the default sorting axis inside every folder. Time is not a container.

Folders are aggregation views. They do not own records and do not change a record’s layout.

## Folder Types

Only these four folder types should own public folder color:

| Folder type | Purpose | Color role |
|---|---|---|
| Region | Country, city, region, transnational geography. | Folder/tab identity only |
| Theme | Propaganda, gender, corporate identity, global modernisms, protest, etc. | Folder/tab identity only |
| Medium | Poster, periodical, typography, identity system, web, standards, etc. | Folder/tab identity only |
| Movement | Movement, school, formation, design tendency. | Folder/tab identity only |

Color must not change sheet layout. It appears in folder tabs, folder cover labels, edge markers, or index bands only.

## Interface-Wide Layout Elements

| Element | Purpose | Surfaces | Fixed? |
|---|---|---|---|
| Archive box shell | Persistent outer frame, folder type entry, search placeholder, global counts. | Box home, folder root | Fixed |
| Folder tab | Shows folder type through color, code, and shape. | Folder lists, covers, dividers | Fixed geometry |
| Folder cover | Overview for folder aggregation. | Folder root | Fixed |
| Chronological divider | Separates year/decade/date ranges inside folder. | Folder index | Fixed strip |
| Binder margin | Punch-hole/spine margin and appendix navigation. | Sheets, appendices | Fixed |
| Sheet ID corner | Display ID and surface type code. | Sheets, cards, stubs | Fixed |
| Rights stamp | Media rights, record rights, review status. | Covers, sheets, cards, stubs | Fixed |
| Source return action | Primary outbound link to provider/source. | Sheets, cards, stubs, appendices | Fixed |
| IMG zone | Media bay with IMG00-IMG04 behavior. | Sheets, cards | Fixed slot when applicable |
| Metadata table | Tombstone facts. | Sheets, appendices | Fixed labels |
| Classification table | Folder memberships, controlled terms, authority links. | Sheets, appendices | Fixed labels |
| Relation table | Parent/child, related works, source relations. | Sheets, appendices | Fixed labels |
| Citation block | Preferred citation and source citation. | Sheets, cards, appendices | Fixed footer |
| Appendix marker | Shows p02/p03 and appendix types. | Sheets, appendices | Fixed |
| Uncertainty strip | Approximate dates, uncertain attribution, contextual matches. | Sheets, cards, stubs | Fixed |
| Registration log | Created/revised/verified facts. | Sheets, appendices | Fixed footer or appendix |
| Card stack | Compact below-threshold items. | Folder stream, compound sheets | Fixed template |
| Bookmark / guide | Explains states and archive reading rules. | Covers, sheets, appendices | Fixed margin module |

Identifiers, rights, source-return, and revision status are structural interface elements, not advanced metadata.

## Archive Box Shell

The archive box home should include:

- project title;
- four folder-type entry points;
- global search placeholder;
- total records count;
- main sheet/card/stub/proposed/unassigned counts;
- IMG00-IMG04 distribution;
- source count;
- last updated;
- short method note;
- reading guide link.

Search remains placeholder until WebLLM is implemented.

Suggested placeholder:

```text
Search records, sources, people, movements, places...
```

## Folder Cover

A folder cover is an index surface, not an essay page.

Required fields:

| Field | Level | Display rule |
|---|---|---|
| Folder title | Essential | Large title |
| Folder type | Essential | Region / Theme / Medium / Movement |
| Folder color and tab code | Essential | Color plus code; color never stands alone |
| Date span | Essential | Based on current members |
| Total record count | Essential | Distinct records in aggregation |
| Main sheet count | Core | In surface mix block |
| Card count | Core | Beside sheets |
| Fallback count | Core | Separate count |
| Unassigned/proposed count | Core | Visibly provisional |
| IMG00-IMG04 distribution | Core | Five-state bar with counts |
| Source count | Core | Distinct providers/source records |
| Chronological index | Essential | Year/decade buckets |
| Scope note | Essential | Inclusion logic, not textbook history |
| Related folders | Core | Cross-folder links with counts |
| Last updated / verified | Core | Admin line |

Folder cover should behave like a finding aid, register, and filing plan.

## Folder Index

Every folder index is a chronological stream.

Members can be:

- main sheets;
- continuation indicators;
- cards;
- fallback stubs;
- proposed cell items;
- unassigned research items;
- chronological dividers.

Default sort:

```text
date_start -> date_precision -> date_end -> seq/capture order -> undated
```

## Main Loose-Leaf Sheet

Main sheet first page should contain:

- unique display ID;
- internal stable ID;
- title;
- supplied-title/source-title indicator if needed;
- date/date range;
- normalized earliest/latest date;
- source name;
- source URL / View at source;
- record type;
- people/institutions;
- region/place;
- folder memberships;
- IMG zone;
- rights stamp;
- 40-120 word abstract/scope note;
- citation block;
- status;
- last verified;
- uncertainty strip if needed;
- appendix markers.

Main sheet can be object-like, text-only, rights-placeholder, or compound. The record’s folder path does not change the sheet.

## Appendix / Second Page

Use appendix or second page for:

- long description;
- source metadata table;
- normalized metadata table;
- classification table;
- relations table;
- citation list;
- provenance log;
- rights review note;
- transcript/text-only content;
- raw field mapping;
- child cards in compound sheets.

Appendix pages usually use IMG04 unless a specific image state is justified.

## Card

Cards are for records below main sheet threshold but strong enough to remain visible.

Required card fields:

- title/label;
- source;
- source return link;
- date or date_text if known;
- folder memberships or proposed/unassigned state;
- status;
- reason it is a card;
- rights/IMG state;
- parent/compound link if any;
- citation seed.

Cards are not failures. They are compact archive fragments.

## Fallback Stub

Fallback stubs remain visible in folders.

Required fields:

- label;
- source name;
- source/search URL;
- fallback reason;
- required next action;
- expected IMG state;
- date if known;
- folder/proposed/unassigned placement;
- public status label.

Fallback stubs should look intentionally incomplete, not broken.

## Unassigned Research Item

Unassigned items are public research-needed entries.

Required fields:

- label/title;
- source;
- source link;
- date if known;
- image state;
- why unassigned;
- possible next actions;
- related proposed cells if any.

They can appear in folder indexes when there is a plausible relation, and in a global unassigned tray.

## Proposed Cell Item

Proposed cell items show framework gaps.

Required fields:

- proposed cell ID;
- label;
- folder type candidate;
- scope note;
- date span;
- supporting capture/source rows;
- reason existing cells are insufficient;
- review status;
- accepted/rejected/superseded pointer later.

## Main Sheet Threshold

A main sheet requires 60+ points and all essential gates.

| Area | Points |
|---|---:|
| Public identity | 20 |
| Source and citation | 20 |
| Date and place | 15 |
| People / institution | 10 |
| Classification and folder memberships | 15 |
| Rights and image state | 10 |
| Description / scope note | 10 |

Essential gates:

- public label;
- internal stable ID;
- source URL or locator;
- source/provider name;
- rights/IMG state;
- at least one date/date_text or a declared undated state;
- citation seed.

## IMG Layout Behavior

| IMG | Layout behavior |
|---|---|
| IMG00 | Image bay exists; empty frame with line/shadow and rights/source text. |
| IMG01 | Same image bay; controlled thumbnail and attribution. |
| IMG02 | Same image bay; source-hosted viewer/IIIF/embed candidate with source context. |
| IMG03 | Same image bay; open image candidate with rights basis. |
| IMG04 | No image bay; text/table layout expands into that space. |

## Visual Direction

The interface should borrow from:

- archive boxes;
- folders;
- loose-leaf sheets;
- binder margins;
- index tables;
- library cards;
- graphic standards manuals;
- typed transcripts;
- stamps and registration marks.

Do:

- fixed templates;
- high contrast base;
- sparse folder colors;
- visible metadata;
- visible source and rights;
- chronological streams.

Do not:

- make a gallery wall;
- make movement-specific visual identities;
- bury source/rights;
- turn every relation into a visualization;
- let image availability dominate the page.

## Text Wireframes

Folder cover:

```text
[folder tab: REGION/THEME/MEDIUM/MOVEMENT]
[folder title]                     [date span]
[scope note]

[surface mix] sheets / cards / stubs / proposed / unassigned
[IMG distribution] 00 01 02 03 04
[source count] [last verified]

[chronological index]
1890s   12 records
1900s    8 records
...

[related folders]
```

Main sheet:

```text
[binder margin] [SEQ / GD display ID]              [rights stamp]

[title]
[date] [record type] [source]
[people/institutions] [place]
[folder memberships]

[IMG zone or expanded text zone]

[short description / scope note]

[SOURCE] [NORMALIZED] [CLASSIFICATION]
[RELATIONS] [CITATIONS]

[View at source] [last verified] [appendix markers]
```

Card:

```text
[card ID] [status] [IMG badge]
[title / label]
[date] [source]
[folder memberships]
[reason this is a card]
[View at source]
```

Fallback stub:

```text
[stub ID] [fallback reason]
[label]
[source/search link]
[required next action]
[expected IMG state]
```

## Anti-Patterns

- Treating timeline as a container.
- Making record layout depend on folder.
- Hiding incomplete records.
- Treating cards as failures.
- Creating bespoke movement pages.
- Using folder color as decoration.
- Displaying image before rights basis is captured.
- Hiding `View at source`.
