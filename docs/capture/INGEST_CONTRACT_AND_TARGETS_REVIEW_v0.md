# Ingest Contract and First Target Reports Review v0

Date reviewed: 2026-05-30

Reviewed reports:

- `Rights and Access Review for a Rights-Aware Graphic Design History Archive Index.docx`
- `Field Mapping and Ingest Contract Review for a Rights-Aware Graphic Design History Archive.docx`
- `First 48 Record Target Selection for a Rights-Aware Modern Graphic Design History Archive Index.docx`

## Executive Decision

The three reports support the next step, but they do not support broad scraping.

Status:

- `SOURCE_TERMS_READY_FOR_FIRST_INGEST: yes_with_conditions`
- `INGEST_CONTRACT_READY: yes_with_conditions`
- `FIRST_48_TARGETS_READY: yes_with_conditions`

Operational meaning:

- The project can proceed to schema completion and controlled manual or semi-automated ingest preparation.
- The project should not begin bulk crawling or image harvesting.
- `IMG00` remains the default for image-bearing records unless item-level rights evidence upgrades the display state.
- Source metadata, normalized metadata, rights review, classification, relations, and citations must remain separate.

## Source and Access Findings

The source report confirms a metadata-first ingest lane:

- Official APIs and datasets can be used cautiously for metadata where documented, including sources such as Europeana, Library of Congress, Smithsonian Open Access, V&A, NYPL, NDL, Trove, POLONA, and selected national library platforms.
- Aggregators do not override provider rights. Europeana, Japan Search, Trove, and similar sources must preserve provider rights text and item-level rights statements.
- Many design-history sources are valuable but not automation-safe for images, including Bauhaus-Archiv, MoMA, Letterform Archive, AIGA, Fonts In Use, JAGDA, PGDA, and activist/community archives.
- Wayback and Internet Archive capture availability must not be treated as image reuse permission.
- Indigenous and community-controlled materials require protocol review in addition to copyright review.

Required database consequence:

- Source-level terms review must include access mode, API/key status, rate limits, forbidden behavior, default image state, and evidence URLs.
- Record-level rights review must still happen even when a source is generally usable.

## Field Mapping Findings

The field mapping report confirms that the system must be source-first and assertion-aware.

Required principles:

- A source record is evidence, not truth.
- A normalized entity is a local assertion layer, not a copy of a source record.
- A described object/work/page and its delivered digital representation are separate.
- Rights state gates public image display.
- Parent-child structures must be explicit: issue to page, collection to item, book to page, event to related records, web capture to original URL.
- Multilingual and non-Latin metadata must retain original script, transliteration, and translation as separate fields.
- `same_as`, `possibly_same_as`, `close_match`, and visual resemblance cannot be collapsed into one relation.

Required database consequence:

- Add field-level provenance.
- Add a digital representation layer separate from `image_assets`.
- Add source record relations for host/part and capture/original relations.
- Add validation profiles for publishable sheet, card/stub, authority-only record, IMG00 link-only record, IMG04 text appendix, periodical chain, web capture, and non-Latin metadata.

## First 48 Target Findings

The first target report identifies:

- `EXACT_RECORDS_IDENTIFIED: 38`
- `SEARCH_PATH_ONLY_TARGETS: 10`
- `TARGETS_REQUIRING_TERMS_REVIEW: 7`
- `TARGETS_REQUIRING_MANUAL_RIGHTS_REVIEW: 31`

The 48-target set is useful because it tests:

- canonical museum objects without assuming image rights;
- link-only activist/community archive records;
- authority-only records;
- text and institutional history pages;
- Japanese, Chinese, Korean, Persian, multilingual, and Indigenous metadata;
- periodical issue to page chains;
- web preservation records;
- `IMG00`, `IMG02`, `IMG03`, and `IMG04` behavior.

It is ready for manual target verification and schema testing. It is not ready for blind automated ingest.

Implementation note:

- The 48 targets have been converted into `data/first_ingest_record_targets.csv`.
- The CSV is an operational verification list. It is not evidence that the records have been ingested, normalized, rights-reviewed, or published.
- Each row must still produce source metadata capture, citations, rights review, field provenance, and publication-surface assignment before it becomes an archive record.

## Recommended Ingest Order

1. Text, authority, event, institutional, and standards records with low image risk.
2. Explicit-license or viewer-permitted records, especially NAIDOC and NAS examples after rights text is captured.
3. Metadata-rich link-only museum/archive records that stay `IMG00`.
4. Structural chain records, especially periodical issue/page and web capture chains.
5. Search-path cases with uncertain rights, unstable target URLs, or creator ambiguity.

## Immediate Schema Actions

Add or confirm:

- source terms access decision fields;
- field-level provenance;
- source record parent-child and capture relations;
- digital representations;
- first-ingest target registry;
- record-family validation profiles;
- page-level image state and image-frame signal;
- API read models for all of the above.

## What This Does Not Yet Prove

The reports do not prove complete global coverage of modern graphic design history. They prove that the current framework can move into a controlled first ingest without structurally reducing the project to a Euro-American museum-image demo.

The remaining open question is not whether the project has every possible historical node. The next practical question is whether the first 48 targets can be manually verified against source terms, rights evidence, and the ingest contract without breaking the schema.
