# Capture Batch 001 Report v0

Date: 2026-05-30

## Purpose

This batch adds 50 captured source rows to the project workflow as a production candidate pool.

The output is not a temporary sample. It is a staged capture batch: every row remains part of the project record and must be filtered into cells, reviewed for rights/source terms, and either promoted, held, or used to define a missing cell. It does not yet complete source-record publication, field provenance, scholarly classification, or final rights review.

## Capture Directions

The 50 rows were split across three directions:

1. `D01 open_and_restricted_museum_poster_objects`
   - Art Institute of Chicago API: 15 rows
   - Cleveland Museum Open Access API: 10 rows
2. `D02 design_museum_poster_catalogue_metadata`
   - V&A Collections API: 15 rows
3. `D03 public_poster_archive_search_records`
   - Library of Congress loc.gov API: 10 rows

This gives the project three different production behaviors:

- open-image museum records;
- restricted or unclear image-bearing object records;
- public archive search records where item-level rights still need review.

## Outputs

- `scripts/run_capture_batch_001.py`
- `scripts/assign_capture_batch_cells.py`
- `data/capture_batch_001_records.csv`
- `data/capture_batch_001_source_summary.csv`
- `data/capture_batch_001_cell_assignments.csv`
- `data/capture_batch_001_cell_summary.csv`
- `data/capture_batch_001_next_generation_queue.csv`
- `data/capture_batch_001_raw/SRC005_vam_search.json`
- `data/capture_batch_001_raw/SRC006_loc_search.json`
- `data/capture_batch_001_raw/SRC020_aic_search.json`
- `data/capture_batch_001_raw/SRC022_cleveland_search.json`
- `db/013_capture_batch_skeleton.sql`

## Results

Total captured rows: 50

By source:

- Art Institute of Chicago API: 15
- Cleveland Museum Open Access API: 10
- V&A Collections API: 15
- Library of Congress loc.gov API: 10

By direction:

- `D01`: 25
- `D02`: 15
- `D03`: 10

By image state:

- `IMG00`: 12
- `IMG01`: 4
- `IMG02`: 8
- `IMG03`: 13
- `IMG04`: 13

Fallback required:

- `false`: 50
- `true`: 0

## Rights Interpretation

This pass deliberately uses row-level image-state behavior.

- `IMG00` is assigned when an image-bearing record exists but no displayable image state is supported by the captured rights evidence.
- `IMG01` is assigned when only a controlled source thumbnail is detected and item-level rights advisory still needs review.
- `IMG02` is assigned when source-hosted viewer or IIIF-service evidence is detected, with no local image copy permitted.
- `IMG03` is assigned only when the API row exposes open-image evidence such as public-domain or CC0 status.
- `IMG04` is assigned when the captured row has no usable source image, no image identifier, or only a not-digitized placeholder. It is a no-image-frame signal, not a copyright tier.
- `local_copy_permitted` remains `false` for every row, including `IMG03`, until record-level review decides otherwise.

## Database Integration

The capture batch rows are stored separately from final source records:

- table: `capture_batch_records`
- table: `capture_batch_cell_assignments`
- table: `capture_batch_cell_summary`
- table: `capture_batch_next_generation_queue`
- API view: `api_capture_batch_records`
- summary view: `api_capture_batch_summary`
- cell assignment view: `api_capture_batch_cell_assignments`
- cell summary view: `api_capture_batch_cell_summary`
- next-generation queue view: `api_capture_batch_next_generation_queue`

This separation matters because capture is a real production state, not final publication. A captured row can become a source record only after cell assignment, source terms review, rights review, provenance capture, and classification review.

Search integration was rebuilt:

- previous `search_docs`: 1402
- current `search_docs`: 1542

## Cell Assignment

The batch now follows the intended workflow:

1. one capture batch produces a raw candidate pool;
2. each row receives an `IMG00`-`IMG04` image-state evaluation;
3. each row is filtered into an existing cell, a proposed new cell, or an unassigned pool;
4. cell-level summaries are collected;
5. the next-generation queue records what should be generated or searched next.

Assignment result:

- 50 capture rows assigned.
- 7 rows connect to existing C-cells.
- 23 rows suggest proposed new cells.
- 20 rows remain in the unassigned capture pool.

Cells with assigned rows:

- `C02 Polish Poster School`: 1 row.
- `C04 Taller de Grafica Popular`: 1 contextual row.
- `C12 Medu / Culture and Resistance`: 4 contextual rows.
- `C14 Gran Fury / ACT UP`: 1 contextual row.
- `PC01 Art Nouveau and Belle Epoque poster culture`: 6 rows.
- `PC02 World War public-information and propaganda posters`: 8 rows.
- `PC03 1970s London political solidarity posters`: 3 rows.
- `PC04 South and Central Asian political poster collections`: 1 row.
- `PC05 Contemporary campaign graphics and network circulation`: 1 row.
- `PC06 Exhibition poster as design-history metadata`: 4 rows.
- `UNASSIGNED`: 20 rows.

This means the batch is not only filling the current framework. It is also identifying framework gaps. Proposed cells should not be silently added to the historical spine; they should be reviewed as candidate framework expansions before source-record generation.

## Validation

Commands run:

- `python3 scripts/run_capture_batch_001.py`
- `python3 scripts/assign_capture_batch_cells.py`
- `python3 scripts/build_sqlite_snapshot.py`
- `python3 scripts/generate_postgres_seed_sql.py`
- `python3 scripts/check_db_skeleton.py`
- `python3 scripts/run_db_migrations.py --dry-run --validate`
- `python3 scripts/search_seed.py "Buy a Little Present for the Kaiser" 5`
- `python3 scripts/search_seed.py "Piper at the Gates of Dawn" 5`
- `python3 scripts/search_seed.py "Unassigned capture pool" 5`
- `python3 scripts/search_seed.py "World War public-information" 5`

All checks passed.

## Methodological Finding

The automated archive workflow can now support a staged capture model:

1. source API/search result capture;
2. raw JSON preservation;
3. normalized capture batch row;
4. conservative image-state assignment;
5. search/database visibility;
6. later promotion into source records only after source-level field provenance, classification, citation review, and rights review.

This is the right boundary for the next round. The project can expand capture volume while keeping every captured row in a visible production state.

## Next Questions

- Add a text/authority capture direction for standards, institutional histories, and bibliographic records so `IMG04` is represented outside not-digitized object records.
- Add a stricter source-terms parser for `IMG01` and `IMG02`, because this pass detects candidate display states but does not complete final rights review.
- Add non-Western API-capable sources into the same harness, especially Japan Search/NDL, DigitalNZ, Trove, Gallica, and national-library sources.
- Use the cell summary and next-generation queue to decide which cells generate candidate source-record drafts next.
