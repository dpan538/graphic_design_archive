# Deep Research Prompt: Field Mapping and Ingest Contract for First Experimental Ingest

Use this prompt to design the field mapping and ingest output contract for a rights-aware modern graphic design history archive index.

This research is independent. Do not assume the reader has access to previous reports.

## Project Definition

The project is a rights-aware archive index and research framework for modern graphic design history.

It does not replace archives, copy collections, build a course, produce a textbook, or impose a single historical narrative. It indexes and links distributed works, texts, people, institutions, movements, media technologies, places, sources, citations, rights states, and historical nodes back to original sources.

The project prioritizes indexing over possession:

- source metadata must remain separate from normalized metadata;
- rights and citation must be visible;
- editorial classification must be evidence-bound;
- visual resemblance is not causal relation;
- AI cannot create historical evidence;
- source links remain primary actions.

## Public Surface Model

The frontend will render archive-cabinet publication surfaces:

- `SEQ` is global;
- display number grammar: `GD / {ERA} / {HN} / {MV|NONE} / {SEQ} / {TIER}-p{PAGE}`;
- page/sheet tiers: `S`, `M`, `L`, `XL`, `XXL`;
- layout ID controls geometry and size;
- image zone controls image-presence state, not size;
- fixed table kinds: `SOURCE`, `NORMALIZED`, `RIGHTS`, `CLASSIFICATION`, `RELATIONS`, `CITATIONS`;
- folder views are filters, not duplicate records;
- first page often has image/name/category; later pages may be pure text.

## Image Presence Codes

| Code | Meaning |
|------|---------|
| `IMG00` | Image frame exists, no source image is shown; empty archive frame with rights/source text and source link. |
| `IMG01` | Image frame exists, permitted thumbnail only. |
| `IMG02` | Image frame exists, permitted embed / IIIF / source-served image. |
| `IMG03` | Image frame exists, open image with item-level license evidence. |
| `IMG04` | No image frame; pure text page or continuation/appendix page. Script/template signal: `has_image_frame = false`. |

`IMG00` through `IMG03` assume an image frame exists and are resolved by copyright/display permission. `IMG04` means no image frame and is not a copyright tier.

## First-Ingest Record Families

The first controlled ingest will include heterogeneous record families:

- museum object record;
- poster record;
- periodical issue;
- periodical page;
- advertisement/editorial page item;
- archive collection/folder record;
- source page / institutional history page;
- event page;
- authority/person/institution/place record;
- web standard page;
- web archive capture;
- community/protocol-sensitive record;
- pure text appendix/continuation page.

## First-Ingest Cells

The first ingest scope has 15 cells:

- C01 Bauhaus / 1919 founding;
- C02 Polish Poster School;
- C03 IBM corporate design;
- C04 Taller de Grafica Popular;
- C05 Brigadas Ramona Parra;
- C06 World Design Conference 1960 / NDC;
- C07 Shanghai Sketch / yuefenpai;
- C08 Minjung / Kwangju posters;
- C09 Singapore multilingual poster/logotype systems;
- C10 NID development communication;
- C11 Iranian modern poster design;
- C12 Medu / Culture and Resistance;
- C13 NAIDOC / land-rights posters;
- C14 Gran Fury / ACT UP;
- C15 Early web / CSS / GeoCities.

## Research Goal

Design a practical ingest contract that tells a script or human editor how to transform source records into database-ready JSON and six-table publication surfaces.

This report should answer:

1. What common fields are required for every ingested source record?
2. What additional fields are required by record family?
3. How should raw source metadata map to `SOURCE` rows?
4. How should normalized metadata map to `NORMALIZED` rows?
5. How should rights evidence map to `RIGHTS` rows?
6. How should HN/MV/event/source classifications map to `CLASSIFICATION` rows?
7. How should relations map to `RELATIONS` rows?
8. How should citations map to `CITATIONS` rows?
9. How should parent-child records work, especially issue -> page and collection -> item?
10. How should `IMG00` through `IMG04` be assigned by rules?

Do not select final target records. Do not review source terms in detail. This report is about field mapping and ingest contract.

## Required Output

Produce a structured report with these sections.

### 1. Executive Decision

State:

- `INGEST_CONTRACT_READY: yes/no/yes_with_conditions`
- whether one JSON schema can cover all first-ingest record families;
- what must remain manually reviewed;
- what fields are non-negotiable.

### 2. Universal Ingest JSON Contract

Design a single JSON object shape for each source record.

Include these conceptual groups:

- source identity;
- source metadata as found;
- normalized metadata;
- rights evidence;
- image presence state;
- citations;
- classifications;
- relations;
- authority candidates;
- language/script/transliteration;
- parent-child links;
- event links;
- publication surface hints;
- review status.

Provide a JSON example with placeholder values.

### 3. Record Family Extensions

Use this table:

| Record family | Required additional fields | Parent-child behavior | Recommended surface type | Likely image zone | Notes |

Include:

- object;
- poster;
- periodical issue;
- periodical page;
- advertisement/editorial page item;
- archive folder/collection;
- authority record;
- event/institutional page;
- web capture;
- pure text appendix/continuation page.

### 4. Six-Table Mapping Rules

For each table kind, define:

#### SOURCE

What fields go here? What must remain source-language/source-as-found?

#### NORMALIZED

What fields go here? What fields must include confidence or transliteration?

#### RIGHTS

What evidence is required? How should `IMG00`-`IMG04` be represented?

#### CLASSIFICATION

How should HN, MV, regional movement, event node, medium, technology, region, and theme be stored?

#### RELATIONS

How should creator, publisher, institution, event, collection, issue/page, source, movement, and visual resemblance relations be represented?

#### CITATIONS

What citation fields are required for every record?

### 5. Image-Zone Assignment Algorithm

Write clear deterministic pseudocode for assigning `IMG00`-`IMG04`.

Rules must include:

- if page is pure text / appendix / continuation without image area -> `IMG04`;
- if image rights are unknown or high risk -> `IMG00`;
- if thumbnail is explicitly allowed -> `IMG01`;
- if IIIF/embed is explicitly allowed -> `IMG02`;
- if open image evidence exists -> `IMG03`;
- protocol-sensitive flags can force `IMG00`;
- frontend must not upgrade image state.

Make clear that image size is separate from image zone.

### 6. Parent-Child Record Rules

Define how to represent:

- periodical issue -> page;
- collection/folder -> item;
- source page -> normalized event/person/institution record;
- web source -> capture;
- first page -> text continuation page;
- object record -> rights appendix.

Use relation predicates where useful.

### 7. Publication Surface Hints

Recommend how ingest output should suggest:

- surface type;
- sheet tier;
- layout ID placeholder;
- page count;
- first page image zone;
- continuation page `IMG04`;
- whether registry card or appendix is needed.

Do not design visuals. This is only data contract guidance.

### 8. Validation Checklist

Create a checklist that a script can use to reject or quarantine records.

Include missing:

- source URL;
- access date;
- rights evidence;
- source title;
- record family;
- language/script for non-Latin records;
- parent issue for page records;
- capture datetime for web captures;
- citation;
- manual review for protocol-sensitive material.

### 9. Database/API Patch Recommendations

Return machine-usable recommendations:

```text
db/schema
- add/confirm ...

manual_source_record.schema.json
- add/confirm ...

API read models
- expose ...

frontend handoff
- requires ...
```

### 10. Final Flags

End with:

- `FIRST_INGEST_CONTRACT_READY: yes/no/yes_with_conditions`
- `REQUIRED_SCHEMA_PATCHES: ...`
- `REQUIRED_JSON_FIELDS: ...`
- `RECORD_FAMILIES_SUPPORTED: ...`
- `MANUAL_REVIEW_GATES: ...`

## Output Style

Be operational. Use tables, JSON examples, and pseudocode. Do not write a general essay. Do not select final records. Do not review source terms in detail.
