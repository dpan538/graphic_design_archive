# First Experimental Ingest Scope Report Review v0

**Date:** 2026-05-30  
**Reviewed file:** `First Experimental Ingest Scope for a Rights-Aware Graphic Design History Archive.docx`

## Executive Read

Decision from report:

- `FIRST_INGEST_SCOPE_READY: yes_with_conditions`
- `FIRST_INGEST_CAN_START_AFTER_TERMS_REVIEW: yes`

Recommended first controlled ingest:

- 48 target source records.
- 15 movement / formation cells.
- 15 event-node anchors.
- 15 source families.
- At least 12 launch regions or transregional frames represented.
- At least 60% of records from non-Euro-American regions or explicitly transregional decolonial/digital formations.
- At least 6 records preserving non-Latin source-language metadata.
- At least 8 records intentionally remaining `IMG00`.
- At least 1 periodical issue/page chain.
- At least 1 web-archive capture chain.

## Methodological Meaning

The report confirms that the first ingest should test the framework, not data volume.

The selected scope is designed to stress:

- source record vs normalized work/entity separation;
- issue/page and collection/item parent-child records;
- link-only records as first-class records;
- multilingual/script metadata;
- collective and anonymous authorship;
- event anchoring;
- protocol-sensitive material;
- born-digital capture metadata;
- rights escalation barriers.

## Implementation Completed

Created:

- `db/009_first_ingest_scope_skeleton.sql`
- `scripts/apply_first_ingest_scope_seed.py`

Updated seed data:

- `data/experimental_ingest_shortlist.csv`: 24 -> 39 rows.
- `data/regional_movements.csv`: 74 -> 89 rows.
- `data/regional_event_nodes.csv`: 48 -> 63 rows.
- `data/source_registry.csv`: 35 -> 54 rows.
- `data/search_vocabulary.csv`: 163 -> 200 rows.
- `data/archive_seed.sqlite`: regenerated.
- `db/010_seed_data.sql`: regenerated.

Added first-ingest cells:

- C01 Bauhaus / 1919 founding.
- C02 Polish Poster School.
- C03 IBM corporate design.
- C04 Taller de Grafica Popular.
- C05 Brigadas Ramona Parra.
- C06 World Design Conference 1960 / NDC.
- C07 Shanghai Sketch / yuefenpai.
- C08 Minjung / Kwangju posters.
- C09 Singapore multilingual poster/logotype systems.
- C10 NID development communication.
- C11 Iranian modern poster design.
- C12 Medu / Culture and Resistance.
- C13 NAIDOC / land-rights posters.
- C14 Gran Fury / ACT UP.
- C15 Early web / CSS / GeoCities.

## Schema Impact

Added structural fields for:

- first-ingest scope cells;
- query profiles;
- source-family IDs;
- target record counts;
- expected sheet/card type;
- movement assignment mode;
- script flags;
- protocol-sensitive flags;
- event anchor strength;
- source-record required flags;
- web-archive relevance;
- source automation and rights basis;
- source record parent-child relationships;
- periodical issue/page fields;
- web capture datetime;
- ICIP flags;
- rights evidence URL/note;
- classification confidence fields.

## Operational Rule

The first ingest can begin only after source terms review rows exist for the selected sources.

Default display remains:

- `IMG00` for all first-ingest cells unless item-level evidence explicitly permits escalation. `IMG00` renders an intentionally empty image frame with linework/shadow, rights/source text, and source link only.
- `IMG01` only after thumbnail-specific review.
- `IMG02` only after IIIF/embed review.
- `IMG03` only after explicit OA/CC0/PD evidence.

## Validation

Validated:

- CSV counts.
- SQLite snapshot counts.
- SQL skeleton tokens.
- PostgreSQL migration dry-run plan.
- Searchability for `Shanghai Manhua`, `NAIDOC`, and first-ingest query profile fields.

Known minor issue:

- SQLite FTS still needs escaping for hyphenated query literals such as `IMG03`.
