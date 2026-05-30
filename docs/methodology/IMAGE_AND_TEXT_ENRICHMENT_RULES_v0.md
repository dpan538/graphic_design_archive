# Image and Text Enrichment Rules v0

Date: 2026-05-30

This document converts the image-strategy and text-enrichment Deep Research
reports into production rules for generated archive surfaces.

## Image State Rules

Image state describes whether the page has an image area and what can appear
inside it. It does not describe paper size, layout tier, or folder type.

| Code | Public behavior | Use when |
|---|---|---|
| `IMG00` | Empty image frame with rights/source explanation and source link. | A visual object likely has an image, but the project cannot display it safely. |
| `IMG01` | Controlled thumbnail with credit and full source link. | A thumbnail is permitted or tolerated under source policy. |
| `IMG02` | Source-hosted viewer, IIIF, or source-interface link behavior. | The image should stay at the source; no local copy. |
| `IMG03` | Open/reusable image with rights basis, credit, and source link. | Item-level rights explicitly allow display or reuse. |
| `IMG04` | No image frame. Text layout expands into that area. | The page is text, authority, bibliography, appendix, or context-led. |

## Image Decision Ladder

1. Decide whether an image should exist.
2. If not, use `IMG04`.
3. If yes, parse item-level rights before looking for pixels.
4. If rights clearly allow display or reuse, use `IMG03`.
5. If there is a source-hosted viewer or IIIF manifest but no local display
   basis, use `IMG02`.
6. If only a safe thumbnail exists, use `IMG01`.
7. If the object likely has an image but no safe display basis exists, use
   `IMG00`.

Acceptable open-image signals include:

- `CC0`;
- Public Domain Mark;
- explicit `public domain`;
- explicit `out of copyright`;
- `CC BY` or equivalent open license;
- source-specific equivalent such as NDL `Rights (production): pdm`.

Do not promote an image because an image URL exists.

## Parser Failure Is Not IMG04

Public image state and internal capture status must stay separate.

Recommended internal fields:

- `image_expectation`: `expected | not_expected | unknown`;
- `parser_status`: `ok | parser_failed | fetch_failed | no_candidate | embargoed | blocked_by_rights`;
- `display_mode`: `empty_frame | thumbnail | source_viewer | open_image | no_frame`;
- `rights_basis`;
- `rights_text`;
- `rights_url`;
- `source_url`;
- `manifest_url`;
- `thumb_url`;
- `credit_line`;
- `citation_text`;
- `rights_snapshot_date`.

If an image should exist but the parser fails, the public state should usually
remain visually close to `IMG00`, while the internal diagnostic status records
the failure.

## IMG00 Frame Text

Use specific archival language, not generic broken-image language.

Rights-restricted:

```text
Image exists at the source archive, but this project does not display a local copy.
Rights / display basis: [short rights text].
View at source.
```

Viewer-only:

```text
Image available through the source viewer.
This record links to the source-hosted image rather than storing a local copy.
View at source.
```

Rights-unclear:

```text
Source record indicates an image, but reuse terms are not clear enough for local display.
View at source.
```

Parser incomplete:

```text
A source image may be present, but capture was not completed at the time of indexing.
View at source.
```

## Text Layers

Every full sheet should include a readable text block before the six evidence
tables whenever enough grounded text exists.

Keep four text layers separate:

| Layer | Field direction | Meaning |
|---|---|---|
| Source text | `source_description_raw`, `source_notes_raw`, `source_subjects_raw`, `extracted_text_snippet` | Verbatim or minimally processed source evidence. |
| Normalized summary | `editorial_summary` | Neutral paraphrase of source evidence. |
| Context note | `historical_context_note` | Why this record matters, grounded in cited sources. |
| Interpretation | `classification_rationale`, relation notes | Movement/theme/significance claims requiring stronger citation or explicit inference label. |

## Reading Gate

| Condition | Surface decision |
|---|---|
| 180+ grounded characters and at least one strong citation basis | Main sheet eligible |
| 80-179 grounded characters plus strong image/source evidence | Thin main sheet eligible, visibly flagged |
| Under 80 grounded characters with no contextual source | Card, compound child, fallback stub, or internal capture row |
| Strong text/authority source with stable citation | `IMG04` text sheet |
| Visual object with failed image parsing | `IMG00` or diagnostic state, not `IMG04` |

## Text Length Targets

- Object/work sheet: 100-250 words.
- Poster sheet: 100-250 words.
- Periodical issue sheet: 120-250 words.
- Book/catalogue/manual sheet: 120-250 words.
- Authority/person/institution sheet: 100-250 words.
- Folder intro: 150-350 words.
- Thin-but-eligible sheet: 60-120 words, with visible thinness status.

## Source Hierarchy For Writing

Use sources in this order unless a record-specific reason says otherwise:

1. object-level museum/archive/library record;
2. collection or finding aid;
3. exhibition text;
4. institutional history;
5. scholarly book, article, catalogue essay, or manual;
6. OCR-discovered periodical/newspaper evidence;
7. authority/vocabulary record for normalization only.

OCR is a discovery and snippet layer. It must be verified against page images
before it supports a strong claim.

## Evidence Boundary

Before publishing any sentence, classify it:

- Evidence: directly recoverable from a source record, stable identifier,
  verified image, or transcribed snippet.
- Description: faithful paraphrase of evidence.
- Interpretation: significance, causality, influence, reception, movement
  membership, or comparative claim.

Interpretation needs direct citation or explicit editor-inference status.

## What We Can Add Ourselves

The project may add editor-authored:

- neutral summaries;
- historical context notes;
- classification rationales;
- uncertainty notes;
- folder introductions;
- empty-frame image notes;
- citation/rights explanations.

These additions are not evidence by themselves. They must point back to source
records, authority records, bibliography, or clearly marked inference.

The project should not add self-made or generated substitute images to stand in
for missing archival images.

