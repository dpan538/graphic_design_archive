# Public Interface Layout Spec v0

Date: 2026-05-30

## Purpose

This document defines the visible archive-box interface and its layout modules.

The public interface should feel like opening an archive box, selecting folders, and reading loose-leaf sheets, cards, stubs, and appendices. It should not feel like a course, gallery, dashboard, or timeline exhibition.

## Visual Principles

1. Fixed templates before visual invention.
2. High-contrast 1-bit paper base.
3. Folder colors only for folder type recognition.
4. Visible metadata, rights, source, and uncertainty.
5. Chronology as ordering, not narrative.
6. No bespoke page design by movement/theme/region/medium.
7. No image wall.
8. No source ownership confusion.

## Global Layout Elements

| Element | Role | Required |
|---|---|---:|
| Archive box frame | Outer shell, project title, folder entry, global counts. | Yes |
| Search placeholder | Future WebLLM/global search entry. | Yes |
| Folder type rail | Region/Theme/Medium/Movement entry points. | Yes |
| Folder tab | Color + code + type label. | Yes |
| Chronology strip | Year/decade separators inside folder stream. | Yes |
| Binder margin | Left-side page spine, holes, page markers. | Yes on sheets |
| Sheet ID corner | Display number, page number, surface type. | Yes |
| Rights stamp | Rights/IMG/local-copy/review status. | Yes |
| Source return action | `View at source`. | Yes |
| Uncertainty strip | Approximate, contextual, unassigned, proposed warnings. | Conditional |
| Appendix marker | p02/p03 and appendix type markers. | Conditional |

## Folder Color Tokens

Folder type owns color. Records do not.

| Folder type | Token | Use |
|---|---|---|
| Region | `folder.region` | Folder tab, cover edge, index marker |
| Theme | `folder.theme` | Folder tab, cover edge, index marker |
| Medium | `folder.medium` | Folder tab, cover edge, index marker |
| Movement | `folder.movement` | Folder tab, cover edge, index marker |

Color must be paired with text/code. Color alone is not meaning.

## Archive Box Overview

Template: `box.overview.v0`

Required modules:

```text
[global header]
  project title
  method note
  search placeholder

[folder type rail]
  Region
  Theme
  Medium
  Movement

[archive counts]
  total records
  main sheets
  cards
  stubs
  proposed cells
  unassigned items
  sources

[IMG distribution]
  IMG00 IMG01 IMG02 IMG03 IMG04

[reading guides]
  how to read image states
  how to read folder views
  why some records are incomplete
```

The overview is orientation, not an essay.

## Folder Type Entry

Template: `folder.type-index.v0`

Each folder type page lists all folders in that type:

- folder title;
- folder type;
- color/tab;
- date span;
- record count;
- surface mix;
- proposed/unassigned count;
- last updated.

Sort options:

- alphabetical;
- most records;
- earliest date;
- recently updated.

Default can be alphabetical at type-index level. Inside a specific folder, default is chronological.

## Folder Cover

Template: `folder.cover.v0`

Wireframe:

```text
[folder tab: TYPE CODE]                         [last verified]

[folder title]
[folder type] [date span]

[scope note: inclusion logic, not textbook explanation]

[surface mix]
main sheets | cards | fallback | proposed | unassigned

[IMG distribution]
00 | 01 | 02 | 03 | 04

[source count] [related folders count]

[chronological index]
1890s  06
1900s  14
1910s  08
undated/date under review  03

[related folders]
Region ... Theme ... Medium ... Movement ...

[open chronological index]
```

Folder cover should answer:

- What kind of folder is this?
- What does it aggregate?
- What date span does it cover?
- What kinds of surfaces are inside?
- How much of it is incomplete/proposed/unassigned?
- Where does the user start reading?

## Folder Index

Template: `folder.index.v0`

Folder index is a chronological stream:

```text
[folder mini header]
[sort: chronological default]

[chronological divider: 1890s]
  sheet row
  card row
  fallback row

[chronological divider: 1900s]
  ...

[undated / date under review]
  ...
```

Each row/entry should show:

- surface type;
- title;
- date/date_text;
- source;
- IMG badge;
- status;
- folder memberships preview;
- `View sheet/card/stub`;
- optional `View at source`.

Folder index can include:

- main sheet entry;
- card entry;
- fallback stub entry;
- proposed cell item;
- unassigned item.

## Main Loose-Leaf Sheet

Templates:

- `sheet.main.v0`
- `sheet.img00.v0`
- `sheet.text.v0`
- `sheet.compound.v0`

Wireframe:

```text
[binder margin] [display ID / SEQ / p01]              [rights stamp]

[title]
[date] [record type] [status]

[source name] [View at source]
[people / institutions]
[place / region]
[folder memberships: region theme medium movement]

[IMG zone]
  IMG00 empty frame
  IMG01 thumbnail
  IMG02 source-hosted viewer
  IMG03 open image
  IMG04 no image bay; text expands

[short abstract / scope note]

[metadata table]
[classification table]
[citation block]

[uncertainty strip if needed]
[appendix markers: p02 source / p03 relations / p04 rights]
[last verified]
```

Required first-page fields:

- display ID;
- internal stable ID;
- title;
- date/date_text;
- record type;
- source name;
- source URL;
- `View at source`;
- rights stamp;
- IMG state;
- status;
- citation seed;
- folder memberships;
- last verified.

## Second Page / Appendix Sheet

Template: `sheet.continuation.v0`

Appendix page types:

- `source appendix`;
- `normalized metadata appendix`;
- `relations appendix`;
- `classification appendix`;
- `citation appendix`;
- `rights appendix`;
- `provenance appendix`;
- `transcript/text appendix`;
- `child card appendix`.

Wireframe:

```text
[binder margin] [same display ID / p02]              [appendix type]

[appendix heading]
[parent record title]

[table or long-form text]

[source/citation footer]
[return to p01]
```

Appendices are not separate records. They belong to a parent surface unless explicitly declared otherwise.

## Card

Template: `card.record.v0`

Cards appear inside folder indexes and sometimes inside compound sheets.

Card layout families must not be distributed evenly. Regular cards carry the
main archive workload: neutral, square, rectangular, and color systems should
account for roughly 92-94% of card placements. Special physical-proportion
cards are rare accents with lower priority and a target placement share around
6%, capped at 8% in any generated card set. Use a special card only when its
physical reference adds function or archival meaning, not because a layout slot
needs decoration.

Required fields:

- card ID;
- title/label;
- date/date_text;
- source name;
- source link;
- surface reason: why not main sheet;
- IMG badge;
- rights/status label;
- folder memberships;
- parent/compound link if any.

Wireframe:

```text
[card id] [IMG badge] [status]
[title]
[date] [source]
[reason: below main sheet threshold / fragment / contextual]
[folder codes]
[View at source]
```

## Fallback Stub

Template: `stub.fallback.v0`

Fallback stubs should look deliberate, not broken.

Required fields:

- stub ID;
- label/title;
- source or search path;
- fallback reason;
- required next action;
- expected IMG state;
- date/date_text if known;
- assigned folder/proposed/unassigned state;
- public note.

Wireframe:

```text
[stub id] [fallback]
[label]
[source/search link]
[reason this is a stub]
[required next action]
[expected IMG state]
```

## Unassigned Research Item

Template: `item.unassigned.v0`

Unassigned items preserve valid or promising material without forcing false classification.

Required fields:

- item ID;
- title/label;
- source;
- source link;
- date/date_text if known;
- IMG state;
- reason unassigned;
- possible folders/cells;
- next review action.

Visible label:

```text
Research placement needed
```

## Proposed Cell Item

Template: `item.proposed-cell.v0`

Proposed cell items represent framework gaps.

Required fields:

- proposed cell ID;
- proposed label;
- possible folder type;
- scope note;
- date span;
- supporting capture/source rows;
- why existing folders/cells are insufficient;
- review status;
- reviewer note;
- accepted/rejected/superseded pointer later.

Visible label:

```text
Proposed folder / under review
```

## Rights Stamp

Template module: `module.rights-stamp.v0`

Required fields:

- IMG state;
- image policy;
- record rights state;
- local copy permitted;
- rights review status;
- source rights basis;
- last rights review date;
- credit/source note.

Compact visual:

```text
IMG02
source-hosted viewer
local copy: no
rights review: required
```

## Source Return Action

Every public record-like surface must expose:

```text
View at source
```

This action should be more visually important than internal navigation actions.

## Uncertainty Strip

Template module: `module.uncertainty-strip.v0`

Use when:

- attribution uncertain;
- date approximate;
- contextual match;
- proposed cell;
- unassigned;
- rights not evaluated;
- source page is search-path-only;
- record is fallback.

Example:

```text
Contextual match: related to Medu / Culture and Resistance, not an exact Medu record.
```

## Layout Response to IMG State

| IMG | First page effect |
|---|---|
| IMG00 | Fixed empty image bay with linework, shadow, rights/source note. |
| IMG01 | Fixed image bay with thumbnail and credit. |
| IMG02 | Fixed image bay with source-hosted viewer or viewer link. |
| IMG03 | Fixed image bay with open image and rights basis. |
| IMG04 | No image bay; text/table area expands. |

## Mobile Behavior

Mobile keeps the same information order:

1. ID/status/rights;
2. title/date/source;
3. image/text zone;
4. metadata;
5. classification;
6. citation/source action;
7. appendices.

Do not collapse rights/source behind hidden menus.

## Anti-Patterns

- Hero pages for records.
- Decorative cards inside cards.
- Movement-specific page styles.
- Timeline-first navigation.
- Hiding stubs/unassigned items.
- Using color without labels.
- Making image the primary proof of record value.
- Letting WebLLM search replace folder/index structure.
