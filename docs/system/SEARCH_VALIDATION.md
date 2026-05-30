# Search Validation v0

**Date:** 2026-05-29  
**Status:** Seed-level deterministic search validation.

## Purpose

This document records the first search validation pass over the seed data. The goal is not to evaluate final UX, ranking, or visual design. The goal is to confirm that the current historical nodes, movements, media/technology terms, sources, search vocabulary, rights strategies, regions, geographies, regional movements, and regional event nodes can be indexed together and queried deterministically before the project moves into formal data ingestion.

## Build Artifacts

- SQLite snapshot: `data/archive_seed.sqlite`
- Builder: `scripts/build_sqlite_snapshot.py`
- CLI search test: `scripts/search_seed.py`
- Seed source CSVs: `data/*.csv`

The SQLite snapshot is a reproducibility artifact. It does not replace PostgreSQL as the intended canonical database.

## Validation Queries

The following queries were run against the FTS5 index:

```bash
python3 scripts/search_seed.py bauhaus 5
python3 scripts/search_seed.py poster 5
python3 scripts/search_seed.py interface 5
python3 scripts/search_seed.py protest 5
python3 scripts/search_seed.py rights 5
python3 scripts/search_seed.py "corporate identity" 5
python3 scripts/search_seed.py China 10
python3 scripts/search_seed.py Korea 8
python3 scripts/search_seed.py Japan 8
python3 scripts/search_seed.py Africa 8
python3 scripts/search_seed.py Arabic 8
```

## Observed Results

### `bauhaus`

Returned:

- `movements:MV011 | Bauhaus`
- `search_vocabulary:SV0005 | bauhaus`
- `historical_nodes:HN008 | Bauhaus, New Typography, modernist books and magazines`

This confirms that a canonical movement can connect to a movement row, vocabulary row, and historical node.

### `poster`

Returned:

- `media_technologies:MT019 | Poster`
- `search_vocabulary:SV0043 | poster`
- `search_vocabulary:SV0137 | poster`
- `media_technologies:MT005 | Lithography`
- `movements:MV021 | Poster workshop movements`

This confirms that an object type can connect to medium/format terms, vocabulary, technical process, and movement formation.

### `interface`

Returned:

- `media_technologies:MT030 | Interface`
- `search_vocabulary:SV0065 | interface`
- `movements:MV035 | Interface design`
- `historical_nodes:HN015 | Web, interface, platform, algorithmic and generative communication`
- `sources:SRC029 | Fonts In Use`

This confirms that contemporary and born-digital terms can be indexed across media, movement, node, vocabulary, and source layers.

### `protest`

Returned:

- `search_vocabulary:SV0091 | protest`
- `historical_nodes:HN012 | Protest graphics and counterpublics`
- `sources:SRC017 | Interference Archive`
- `media_technologies:MT007 | Screen printing`
- `movements:MV021 | Poster workshop movements`

This confirms that counterpublic and activist terms can surface non-canonical sources and media terms.

### `rights`

Returned:

- `rights_strategies:RS006 | IIIF endpoints`
- `media_technologies:MT021 | Exhibition catalogue`
- `search_vocabulary:SV0097 | civil rights`
- `rights_strategies:RS007 | Community archives and crowdsourced archives`
- `rights_strategies:RS005 | Aggregators returning partner links`

This confirms that rights strategy records are searchable, but also reveals a future ranking issue: the query `rights` also matches thematic terms such as `civil rights`. This is acceptable at seed stage but should be handled later through facets and field-weighting.

### `corporate identity`

Returned:

- `movements:MV016 | Corporate identity modernism`
- `historical_nodes:HN011 | Corporate identity, editorial systems, packaging systems`
- `media_technologies:MT022 | Corporate identity manual`
- `sources:SRC014 | Vignelli Center for Design Studies`
- `historical_nodes:HN010 | Swiss Style, grids, systems, information design, wayfinding`

This confirms that phrase-like search can connect formation, historical node, format, and source.

### Global Coverage Checks

`China`, `Korea`, `Japan`, `Africa`, and `Arabic` now return geography rows, regional movement rows, regional event nodes, and/or source rows. This confirms that global coverage is searchable at seed level and not confined to the older Euro-American movement list.

## Findings

The current seed layer is sufficient for the next implementation step:

- core concepts can be found deterministically;
- search crosses taxonomy layers;
- rights records can be indexed alongside historical/material records;
- non-canonical areas such as protest, queer, feminist, labor, community archives, African graphic histories, East Asian script/typography, South Asian multiscript design, Arabic/Persian/Hebrew/Turkish typography, and Pacific community contexts are represented in the seed structure;
- search results expose the need for field weighting and facets before public UI.

## Known Limits

- FTS5 ranking is only a development proxy and does not represent final search behavior.
- Search terms are still too English-heavy and need regional-language expansion.
- Authority IDs are unresolved.
- Multi-value fields are still semicolon-separated strings.
- Rights policies remain source-level until object-level source records are ingested.
- The SQLite snapshot does not enforce the full PostgreSQL relation model.

## Next Step

Proceed to database implementation planning:

1. Import CSVs into PostgreSQL seed tables.
2. Convert selected seed rows into first `entities`.
3. Create 20-30 manual `source_records` from Launch sources.
4. Build `searchable_documents` from both seed data and source records.
5. Add facets and field-weighting before frontend design.
