# Remediation Source Verification Pass v0

Date: 2026-05-30

## Purpose

This pass tests whether unresolved first-ingest fallback rows can move through a reproducible remediation workflow without collapsing the distinction between source links, source records, and published sheets.

The goal is not to ingest final records yet. The goal is to prove that a blocked target can remain present in the framework, receive new source evidence, and either become a candidate source record or remain a clearly marked fallback stub.

## Inputs

- `data/fallback_remediation_projection.csv`
- `data/remediation_source_verifications.csv`
- `data/source_registry.csv`
- Source links and source-search paths identified by the remediation reports

## Outputs

- `data/remediation_source_verifications.csv`: 10 verification rows.
- `data/remediation_source_records_index.csv`: 8 valid candidate source-record drafts.
- `data/remediation_source_records/*.json`: 8 candidate JSON records.
- `data/source_registry.csv`: expanded from 62 to 66 source rows.
- `data/archive_seed.sqlite`: rebuilt search snapshot.
- `db/010_seed_data.sql`: rebuilt seed SQL.

## Verification Result

The pass produced 10 remediation verification rows:

- 4 rows: `promote_to_candidate_after_source_capture`
- 2 rows: `promote_as_contextual_candidate_not_direct_replacement`
- 1 row: `promote_as_replacement_candidate_after_source_capture`
- 1 row: `promote_as_contextual_candidate_not_direct_item_replacement`
- 1 row: `keep_fallback_until_exact_record`
- 1 row: `keep_fallback_or_replace_with_proceedings_anchor`

This means 8 of the 10 verification rows can become candidate source-record drafts after source-field capture. The remaining 2 should stay as fallback stubs for now.

## Image Presence Result

The 10 verification rows split evenly:

- 5 rows: `IMG00`, fixed image area exists but no image may be displayed.
- 5 rows: `IMG04`, pure text/source page with no image frame.

The 8 generated candidate records split as:

- 4 rows: `IMG00`
- 4 rows: `IMG04`

This confirms the corrected image model:

- `IMG00` through `IMG03` describe image-display permission states where an image frame exists.
- `IMG04` is a layout signal for pages with no image frame.
- Image size remains a separate template/display decision.

## Source Registry Additions

Four sources were added to support this remediation layer:

- `SRC063`: Biblioteca Nacional Digital de Chile
- `SRC064`: NDL Search
- `SRC065`: Seoul Museum of Art
- `SRC066`: National Library Board Singapore

These sources are launch candidates for remediation and low-friction indexing, but they still require item-level source terms and rights review before publication use.

## Candidate Records Created

Generated draft records:

- `RSV001_source_record.json`
- `RSV003_source_record.json`
- `RSV004_source_record.json`
- `RSV006_source_record.json`
- `RSV007_source_record.json`
- `RSV008_source_record.json`
- `RSV009_source_record.json`
- `RSV010_source_record.json`

Not generated as source records:

- `RSV002`: keep fallback until an exact source record is found.
- `RSV005`: keep fallback, or replace only with a proceedings or bibliographic anchor after review.

## Methodological Meaning

This pass supports the archive framework in three ways:

1. Fallback is a first-class archival state, not a failed row.
2. Contextual replacements are allowed, but must be marked as contextual rather than direct replacements.
3. Rights state and image presence state travel with the candidate record from the beginning.

This is especially important for a global graphic design history index, because fragile, politically sensitive, regional, or non-museum sources will often be harder to fetch than large Western museum APIs. The framework must preserve those areas without pretending that missing capture equals missing historical importance.

## Validation

Commands run:

- `python3 scripts/generate_remediation_source_record_drafts.py`
- `python3 scripts/validate_manual_source_record.py data/remediation_source_records`
- `python3 scripts/build_sqlite_snapshot.py`
- `python3 scripts/generate_postgres_seed_sql.py`
- `python3 scripts/check_db_skeleton.py`
- `python3 scripts/run_db_migrations.py --dry-run --validate`
- `python3 scripts/search_seed.py "Biblioteca Nacional Digital de Chile" 5`
- `python3 scripts/search_seed.py "Hong Sung Dam" 5`

All checks passed.

Current searchable seed count:

- `searchable_documents` / SQLite `search_docs`: 1388 -> 1402.

## Remaining Cautions

- Candidate source-record drafts are not final ingested records.
- Field-level source capture and provenance are still required.
- Rights review is still required before image display, thumbnail use, or publication.
- Contextual remediation candidates must not be presented as exact replacements.
- The search/fallback ratio improved, but source coverage is still uneven across South Asia, MENA, Africa, Oceania, and Indigenous design histories.
