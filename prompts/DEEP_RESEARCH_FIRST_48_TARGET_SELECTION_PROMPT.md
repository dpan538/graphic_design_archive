# Deep Research Prompt: First 48 Target Record Selection for Controlled Ingest

Use this prompt to select concrete target records or deterministic search paths for the first controlled ingest of a rights-aware modern graphic design history archive index.

This research is independent. Do not assume the reader has access to previous reports.

## Project Definition

The project is a rights-aware archive index and research framework for modern graphic design history.

It does not replace archives, copy collections, build a course, produce a textbook, or impose a single historical narrative. It indexes and links distributed works, texts, people, institutions, movements, media technologies, places, sources, citations, rights states, and historical nodes back to original sources.

The project prioritizes indexing over possession:

- source links are primary;
- metadata, citations, and rights evidence are more important than image display;
- high-risk images remain empty-frame `IMG00`;
- pure text pages use `IMG04`;
- source-language metadata must be preserved;
- final records must remain traceable and reproducible.

## Image Presence Codes

| Code | Meaning |
|------|---------|
| `IMG00` | Image frame exists, no source image is shown; empty archive frame only. |
| `IMG01` | Image frame exists, permitted thumbnail only. |
| `IMG02` | Image frame exists, permitted embed / IIIF / source-served image. |
| `IMG03` | Image frame exists, open image with item-level license evidence. |
| `IMG04` | No image frame; pure text page or continuation/appendix page. |

`IMG00` through `IMG03` assume an image frame exists and are resolved by copyright/display permission. `IMG04` is a script/template signal that the page has no image frame.

## First-Ingest Scope

Select a total of 48 target records across these 15 cells:

| Cell | Movement / event | Target count | Required role |
|------|------------------|--------------|---------------|
| C01 | Bauhaus / 1919 founding | 4 | canonical modernism normalization and rights false-positive test |
| C02 | Polish Poster School | 2 | socialist-context poster indexing |
| C03 | IBM corporate design | 4 | institution-designer-manual-object relations |
| C04 | Taller de Grafica Popular | 4 | collective printshop and publication/object separation |
| C05 | Brigadas Ramona Parra | 3 | counterpublic collective-authorship and mural/source boundary |
| C06 | World Design Conference 1960 / NDC | 4 | Japanese-language event/person/institution/work relations |
| C07 | Shanghai Sketch / yuefenpai | 4 | Chinese issue/page hierarchy and commercial/vernacular overlap |
| C08 | Minjung / Kwangju posters | 3 | Korean-script event-linked protest poster records |
| C09 | Singapore multilingual poster/logotype systems | 3 | four-language public campaign and catalogue/object distinction |
| C10 | NID development communication | 3 | state-building, pedagogy, design education, multilingual India |
| C11 | Iranian modern poster design | 2 | Persian-script and transliteration test |
| C12 | Medu / Culture and Resistance | 4 | collective authorship, exile, anti-apartheid, call-number metadata |
| C13 | NAIDOC / land-rights posters | 3 | ICIP/protocol-sensitive metadata test |
| C14 | Gran Fury / ACT UP | 3 | collective authorship, campaign relation, queer counterpublic graphics |
| C15 | Early web / CSS / GeoCities | 2 | born-digital source/capture timestamp and archived-rights test |

## Important Constraint

Do not choose targets because they are visually attractive.

Choose targets because they are:

- citable;
- stable enough to link;
- useful for field mapping;
- rights-safe or rights-clear enough for the intended image state;
- able to test source metadata vs normalized metadata;
- able to test relation/classification/citation behavior;
- globally balanced;
- realistic for a controlled ingest.

If a concrete record cannot be selected safely, provide a deterministic search path and selection criteria instead.

## Target Record Types Needed

The final 48 should include:

- at least 6 periodical issue/page records;
- at least 8 authority/person/institution/event records or cards;
- at least 8 event-linked records;
- at least 8 link-only `IMG00` records from non-open sources;
- at least 4 protocol-sensitive or culturally sensitive records;
- at least 4 born-digital or web-archive records/pages;
- at least 6 records preserving non-Latin source-language metadata;
- at least 1 page or continuation candidate that should use `IMG04`.

## Research Goal

For each cell, recommend exact target records where possible.

For each target, provide:

- source;
- record URL or deterministic search path;
- title/source title;
- creator/person/institution if available;
- date/date text;
- record family;
- why it was selected;
- expected HN/MV/event mapping;
- expected image state (`IMG00`-`IMG04`);
- required rights evidence;
- citation/access-date needs;
- fallback if the target fails terms review.

## Required Output

Produce a structured report with these sections.

### 1. Executive Decision

State:

- `FIRST_48_TARGETS_READY: yes/no/yes_with_conditions`
- number of exact record URLs found;
- number requiring manual search paths;
- number requiring terms review before final selection;
- number expected as `IMG00`, `IMG01`, `IMG02`, `IMG03`, and `IMG04`.

### 2. Target Record Table

Use this table:

| Target ID | Cell | Source | Record URL or search path | Source title | Creator / institution | Date | Record family | HN | Movement / regional movement | Event node | Expected IMG | Why selected | Rights evidence needed | Fallback |

Target IDs should be:

- `T001` through `T048`.

### 3. Cell-by-Cell Rationale

For each C01-C15, explain:

- why the selected targets satisfy the cell;
- what record families are represented;
- whether the target count is met;
- what remains uncertain.

### 4. Non-Latin and Multilingual Coverage

Use this table:

| Target ID | Language/script | Source-language fields expected | Transliteration need | Search terms used |

Include Chinese, Japanese, Korean, Persian, and at least one South/Southeast Asian or Indigenous/community-language case where feasible.

### 5. Rights and Image State Summary

Use this table:

| Expected IMG | Target IDs | Reason | Required evidence |

Make clear:

- `IMG00` means image frame exists but no image content;
- `IMG04` means no image frame and should be used for pure text pages or appendices.

### 6. Parent-Child and Relation Tests

Identify targets that test:

- issue -> page;
- collection/folder -> item;
- institution -> designer -> work/manual;
- event -> object/source;
- collective -> campaign/poster;
- source page -> normalized event;
- web source -> web capture.

Use this table:

| Relation test | Target IDs | Expected relation predicates | Notes |

### 7. Fallback Target Pool

Provide 10-15 fallback records or search paths, especially for sources whose terms may block automation or display.

Use:

| Fallback ID | Cell | Source | Search path / URL | Why useful | Expected IMG |

### 8. Exclusions

List tempting targets that should not be used in first ingest.

Use:

| Excluded target/source | Reason to exclude or defer | Safe alternative |

Include image-rights traps, modern social media, unstable web pages, community-sensitive items, or records without citation stability.

### 9. Machine-Usable Patch Recommendation

Return a CSV-like recommendation for a future target file:

```text
data/first_ingest_targets.csv
columns:
target_id,cell_id,source_id,source_name,record_url_or_search_path,source_title,creator_or_institution,date_text,record_family,hn_ids,movement_ids,event_ids,expected_image_zone,rights_evidence_required,citation_required,manual_review_required,fallback_target,notes
```

Then provide the 48 rows in a copyable table or code block.

### 10. Final Flags

End with:

- `FIRST_48_SELECTION_READY_FOR_TERMS_REVIEW: yes/no/yes_with_conditions`
- `EXACT_URL_COUNT: ...`
- `SEARCH_PATH_COUNT: ...`
- `IMG00_COUNT: ...`
- `IMG01_COUNT: ...`
- `IMG02_COUNT: ...`
- `IMG03_COUNT: ...`
- `IMG04_COUNT: ...`
- `NON_LATIN_RECORD_COUNT: ...`
- `PROTOCOL_SENSITIVE_COUNT: ...`
- `WEB_CAPTURE_COUNT: ...`
- `PERIODICAL_CHAIN_COUNT: ...`

## Output Style

Be precise and operational. Cite record pages or explain search paths. Do not write a general essay. Do not design the frontend. Do not make legal conclusions beyond conservative rights/display recommendations.
