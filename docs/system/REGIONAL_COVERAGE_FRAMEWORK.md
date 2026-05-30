# Regional Coverage Framework v0

**Status:** Required coverage layer.  
**Purpose:** Prevent the archive index from becoming an Euro-American framework with decorative global additions.

## Principle

The project must pursue broad geographic coverage across Europe, the Americas, Japan, Korea, East Asia, China, and other global regions. It cannot claim total coverage, but it must design for systematic expansion rather than treating non-European and non-American histories as supplements.

## Current Position

The previous seed framework was useful but still structurally biased toward Euro-American reference points. The regional coverage layer corrects this by making region-node coverage a database object.

New seed files:

- `data/regions.csv`
- `data/coverage_matrix.csv`
- `data/regional_source_priorities.csv`

New database skeleton:

- `db/004_coverage_skeleton.sql`

New read models:

- `api_regions`
- `api_coverage_matrix`

## Required Launch Coverage Regions

Launch coverage includes all of the following from the first public version:

- Western and Central Europe;
- Eastern Europe, Balkans, and Central/Eastern socialist contexts;
- North America;
- Latin America and the Caribbean;
- Japan;
- Korea;
- East Asia as a transnational parent frame;
- Mainland China;
- Hong Kong;
- Taiwan;
- Southeast Asia;
- South Asia;
- Middle East and North Africa;
- Africa;
- Oceania and Pacific.

The `priority` field should therefore mean launch inclusion, not deferred phasing. Research readiness is tracked separately through `coverage_status`.

## China and East Asia Coverage Rule

China, Japan, Korea, Hong Kong, and Taiwan must not be treated as a single undifferentiated East Asian block.

Each needs:

- language/script-aware search terms;
- regional source registry;
- periodization;
- local design schools, studios, publishers, magazines, and institutions;
- political and commercial print histories;
- typography and script-specific design histories;
- born-digital and platform histories;
- rights and access review based on source jurisdiction.

## Coverage Matrix

`coverage_matrix.csv` creates one row for every pair of:

- historical node;
- region.

Current count:

- 15 historical nodes;
- 15 regions;
- 225 coverage rows.

Coverage status values:

- `seeded`: initial material exists but needs validation;
- `launch_research_required`: structurally important launch-scope gap requiring focused research;
- `planned`: recognized but not yet researched;
- future values may include `validated`, `sampled`, `source_mapped`, `blocked`, `out_of_scope`.

## Why This Matters

Without this layer, the system might appear global while its actual data model remains Euro-American. The coverage matrix forces the project to ask, for every historical node:

- What is the China-related history here?
- What is the Japan-related history here?
- What is the Korea-related history here?
- What is the Latin American history here?
- What is the Eastern European or socialist-state history here?
- What is missing because the source ecosystem is weak?
- Which records are unavailable because of rights, language, or digitization barriers?

## What We Still Do Not Have

The project still does not have a complete event history.

Missing next layers:

- country-level historical node maps;
- regional movement taxonomies;
- regional source registries;
- local-language search vocabularies;
- city-level design centers;
- institution and school lists;
- periodical and magazine lists;
- event-level timelines;
- regional authority resolution;
- jurisdiction-specific rights review.

## Next Work

1. Run regional Deep Research for China, Japan, Korea, Hong Kong, Taiwan, Europe, and the Americas.
2. Convert results into:
   - `regional_movements.csv`;
   - `regional_events.csv`;
   - `regional_sources.csv`;
   - `regional_search_vocabulary.csv`;
   - `authority_resolution_queue.csv`.
3. Update `coverage_matrix.csv` from `launch_research_required` to `source_mapped` only when sources are identified.
4. Update to `validated` only when cited source records exist.

## Public Claim Boundary

The project may claim:

> This archive index is designed for broad, gap-aware, and expandable coverage across multiple regions and historical contexts.

The project must not claim:

> This archive index fully covers world graphic design history.
