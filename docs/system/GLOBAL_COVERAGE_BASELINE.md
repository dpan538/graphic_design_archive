# Global Coverage Baseline v0

**Status:** Required before design system freeze.

**Current implementation status:** Database baseline represented as of 2026-05-29.

- 15 launch regions.
- 225 region × historical-node coverage rows.
- 90 regional source-priority rows.
- 10 classification axes.
- 109 geography/context rows.
- 89 regional movement/formation rows.
- 63 regional event-node rows.
- 39 experimental ingest candidates.
- 992 searchable seed documents.

## Principle

The design system should not be finalized until the project has a global coverage baseline for graphic design history. Otherwise the frontend will repeatedly need structural patches for regions, scripts, dates, rights states, and source types that were not represented in the first design model.

The goal is not to claim exhaustive completion of every historical event. The goal is to include the known global structure at launch:

- regions;
- countries/territories/context areas;
- historical nodes;
- regional movements/formations;
- media/technology regimes;
- event categories;
- source categories;
- rights patterns;
- search vocabulary;
- date/year handling;
- language/script handling.

## Required Axes Before Design System Freeze

### 1. Geography

The system must support:

- macro-region;
- country/context;
- city/place;
- transnational route;
- diaspora/circulation context;
- historical jurisdiction where relevant.

Records must be able to carry more than one geographic relation:

- made in;
- published in;
- circulated in;
- held by;
- associated with;
- about/depicts;
- source institution location.

### 2. Date and Year

The system must support:

- exact year;
- approximate year;
- date range;
- decade;
- century;
- unknown date;
- source date text;
- normalized start/end years;
- event date vs object date vs publication date vs digitization date.

### 3. Historical Node

Every launch-scope record should be attachable to at least one historical node, or marked as `node_pending`.

### 4. Movement / Formation

Movements should not be limited to canonical European art/design movements. The taxonomy must include:

- schools;
- studios;
- publishing cultures;
- state design formations;
- protest/counterpublic formations;
- typography/script formations;
- commercial/vernacular formations;
- digital/platform formations;
- regional modernisms.

### 5. Medium / Technology / Format

The system must support both process and object type:

- how something was made;
- what kind of object it is;
- how it circulated;
- how it is preserved or digitized.

### 6. Source and Rights

Each region must have source needs mapped before visual system freeze:

- national libraries;
- museums;
- design archives;
- university collections;
- periodical/newspaper archives;
- poster archives;
- community archives;
- web archives;
- authority/vocabulary sources.

Rights display rules must not assume that image display is available.

### 7. Language and Script

The design system must assume:

- English UI chrome during development;
- source-language titles and metadata;
- CJK text;
- Hangul;
- right-to-left scripts in future;
- transliteration/romanization fields;
- multilingual search vocabulary.

## Launch Coverage Baseline Gates

Before visual design system freeze:

1. `regions.csv` exists and includes all launch regions.
2. `coverage_matrix.csv` exists for every region × historical node pair.
3. `regional_source_priorities.csv` exists.
4. `classification_axes.csv` exists.
5. `geographies.csv` exists.
6. `regional_movements.csv` exists.
7. `regional_event_nodes.csv` exists.
8. `regional_search_vocabulary.csv` exists or is explicitly queued.
9. `authority_resolution_queue.csv` exists or is explicitly queued.
10. API contract includes geography/date filters.
11. Frontend handoff contract states visual system is blocked until these axes are represented.

## Cursor Visual System Dependency

Cursor's visual archive concept can continue as a candidate interaction metaphor, but it must not become the design system source of truth until the global coverage baseline is represented.

The filing-cabinet metaphor must be tested against:

- non-Latin scripts;
- long multilingual names;
- country/region/date filtering;
- records without images;
- records with link-only rights;
- regional gaps;
- multi-region records;
- date uncertainty;
- movement `NONE`;
- multiple movements;
- event-level records.

## Public Claim Boundary

Allowed:

> The project launches with a global coverage framework designed to index modern graphic design history across regions, dates, movements, media, and source types.

Not allowed:

> The project has completed all known events in world graphic design history.

The correct standard is launch-complete structure, not omniscient data completeness.
