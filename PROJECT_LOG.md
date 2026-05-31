# Project Log

This log records project decisions, implementation steps, and collaboration boundaries. It should be updated after every meaningful change so that future work, including database implementation and frontend handoff, remains traceable.

## 2026-05-29

### Project Definition Settled

The project is defined as a rights-aware archive index and research framework for modern graphic design history.

Key boundaries:

- It is not a course, textbook, museum education platform, inspiration gallery, or replacement archive.
- It does not impose a single historical or visual narrative.
- It prioritizes indexing, citation, classification, rights status, and source links over copying or locally hosting materials.
- It is a window into distributed archives, not a project that absorbs their contents.

### Methodology v0 Created

Created:

- `Methodology_v0.md`
- `Methodology_v0.docx`

Core principles:

- integrity
- reproducibility
- source transparency
- rights-aware indexing
- separation of source metadata, normalized metadata, editorial classification, and research inference

### WebLLM Position Clarified

Decision:

- WebLLM is not part of the initial database/search/frontend contract.
- WebLLM must be local/browser-side and packaged with or controlled by the project.
- WebLLM must not call a hosted LLM API for normal public use.
- WebLLM belongs only at the final enhancement stage after method, database, search, and frontend contracts are stable.

### Deep Research Node Map Prompt Created

Created:

- `DEEP_RESEARCH_NODE_MAP_PROMPT.md`

Purpose:

- validate historical nodes;
- expand movement and formation taxonomy;
- expand media/technology taxonomy;
- expand source universe;
- produce search vocabulary;
- produce rights-safe indexing strategy.

### Deep Research Report Reviewed

Reviewed:

- `Rights-Aware Archive Index Framework for Modern Graphic Design History.docx`

Conclusion:

- The report is sufficient to move from methodology into structured seed data.
- It supports historical nodes, movement taxonomy, media taxonomy, source registry, rights strategy, and CSV schema.

### Seed Data v0 Generated

Created:

- `data/historical_nodes.csv`
- `data/movements.csv`
- `data/media_technologies.csv`
- `data/source_registry.csv`
- `data/search_vocabulary.csv`
- `data/rights_strategy.csv`
- `data/README.md`
- `scripts/generate_seed_data.py`

Validation:

- `historical_nodes.csv`: 15 rows
- `movements.csv`: 38 rows
- `media_technologies.csv`: 35 rows
- `source_registry.csv`: 35 rows
- `search_vocabulary.csv`: 163 rows
- `rights_strategy.csv`: 10 rows

### Data Dictionary and Schema Draft Created

Created:

- `DATA_DICTIONARY.md`
- `SCHEMA_DRAFT.md`

Purpose:

- document fields before database implementation;
- preserve seed meaning and constraints;
- prepare PostgreSQL schema design.

### Search Validation Layer Created

Created:

- `db/001_initial_schema.sql`
- `scripts/build_sqlite_snapshot.py`
- `scripts/search_seed.py`
- `data/archive_seed.sqlite`
- `SEARCH_VALIDATION.md`

Validation:

- SQLite snapshot generated successfully.
- `search_docs`: 296 searchable seed records.
- Tested deterministic search queries:
  - `bauhaus`
  - `poster`
  - `interface`
  - `protest`
  - `rights`
  - `corporate identity`

Finding:

- Seed search works across historical nodes, movements, media/technologies, sources, search vocabulary, and rights strategies.
- Field weighting and facets will be required before frontend work.

### Workflow Boundary Reconfirmed

Decision:

- Do not begin data scraping yet.
- Do not begin frontend implementation yet.
- Complete the database skeleton first.
- Frontend work will later be handed to Cursor, so database contracts, API expectations, and data boundaries must be explicit before UI work begins.

Next step:

- Build the complete database skeleton before any source crawling or ingestion.

### Database Skeleton Boundary Established

Decision:

- No automated data acquisition should begin until the database skeleton gates are complete.
- Database skeleton comes before scraping, API ingestion, frontend design, and WebLLM.
- The project must be able to receive records without losing source evidence, rights context, classification basis, review state, or audit history.

Created:

- `DB_SKELETON_PLAN.md`
- `db/002_operational_skeleton.sql`

`db/002_operational_skeleton.sql` adds tables for:

- schema versions;
- project releases and release files;
- authority sources;
- external identifiers;
- entity aliases;
- relation predicate registry;
- classification schemes;
- source terms reviews;
- rights reviews;
- ingestion runs;
- ingestion events;
- source record snapshots;
- editorial reviews;
- workflow events;
- assertion reviews;
- search index queue;
- export jobs;
- audit log.

### Frontend Handoff Boundary Established

Decision:

- Frontend implementation should not begin until database skeleton gates are complete.
- Cursor/frontend work should consume stable contracts, not unstable crawling output.
- Frontend must not assume local images, open image rights, WebLLM, or graph visualization as the primary experience.

Created:

- `FRONTEND_HANDOFF_CONTRACT.md`

This file defines early API shapes for:

- search results;
- source registry items;
- entity details;
- source record details;
- citation panel;
- rights panel;
- provenance and uncertainty panel.

Next step:

- Create migration runner, seed import script, and database validation script.

### Database Migration and Validation Tooling Added

Created:

- `db/003_read_models.sql`
- `db/010_seed_data.sql`
- `db/900_validation_queries.sql`
- `db/README.md`
- `scripts/generate_postgres_seed_sql.py`
- `scripts/run_db_migrations.py`
- `scripts/check_db_skeleton.py`

Purpose:

- generate PostgreSQL seed inserts from `data/*.csv`;
- define read-only API/frontend views;
- run migrations in order when `DATABASE_URL` is configured;
- validate expected row counts and required tables/views;
- check the database skeleton offline before any live PostgreSQL instance is used.

Validation completed:

- `python scripts/run_db_migrations.py --dry-run --validate`
- `python scripts/check_db_skeleton.py`

Result:

- migration plan resolves successfully;
- required files exist;
- CSV counts pass;
- SQLite snapshot counts pass;
- SQL skeleton tokens pass;
- generated seed SQL contains expected inserts;
- no database changes were made because this was a dry-run/offline skeleton validation.

Current boundary:

- Database skeleton tooling is ready for live PostgreSQL validation.
- Automated source crawling remains blocked.
- Next step is either configure a local PostgreSQL `DATABASE_URL` for live schema validation or continue refining manual source-record templates and API contracts.

### Manual Source Record and API Contracts Added

Created:

- `MANUAL_SOURCE_RECORD_TEMPLATE.md`
- `db/manual_source_record.schema.json`
- `data/manual_source_record.example.json`
- `scripts/validate_manual_source_record.py`
- `API_CONTRACT.md`

Purpose:

- define how the first real source records may enter the system manually;
- require source link, access date, citation, rights state, image policy, and classification before publication;
- keep source metadata separate from normalized metadata;
- prevent unclear image rights from becoming local display;
- define read-only API shapes for future backend/frontend work.

Validation completed:

- `python scripts/validate_manual_source_record.py data/manual_source_record.example.json`
- `python -m json.tool db/manual_source_record.schema.json`
- `python scripts/check_db_skeleton.py`

Result:

- example manual source record passes validation;
- JSON schema is syntactically valid;
- database skeleton offline check still passes.

Coverage note:

- Current historical nodes and taxonomies are a structured seed framework, not a complete event history of graphic design.
- The project must not claim complete coverage of all graphic design events.
- Coverage should be treated as iterative, auditable, and gap-aware.

### Regional Coverage Layer Added

Decision:

- Broad geographic coverage is now a database requirement, not a later editorial add-on.
- The project must avoid becoming an Euro-American framework with decorative global examples.
- Europe, the Americas, Japan, Korea, East Asia, Mainland China, Hong Kong, Taiwan, Southeast Asia, South Asia, Middle East and North Africa, Africa, and Oceania/Pacific are all launch-scope coverage contexts.

Created:

- `REGIONAL_COVERAGE_FRAMEWORK.md`
- `DEEP_RESEARCH_REGIONAL_COVERAGE_PROMPT.md`
- `scripts/generate_regional_coverage_data.py`
- `data/regions.csv`
- `data/coverage_matrix.csv`
- `data/regional_source_priorities.csv`
- `db/004_coverage_skeleton.sql`

Database/read-model updates:

- `regions`
- `coverage_matrix`
- `regional_source_priorities`
- `historical_events`
- `coverage_gap_notes`
- `api_regions`
- `api_coverage_matrix`

Validation impact:

- `searchable_documents` seed count increased from 296 to 626 because region and coverage seed rows are now searchable.

Current coverage statement:

- The project still does not fully cover all events in graphic design history.
- It now has a structural mechanism to track broad regional coverage and expose gaps instead of hiding them.

### Launch Scope Reframed

Decision:

- Remove launch phasing thinking from regional coverage.
- The first public version should be designed as a launch-complete global framework.
- Readiness can differ by region, but inclusion cannot be deferred conceptually.
- The design system should be built against the full coverage structure from the beginning.

Implementation update:

- `data/regions.csv` now marks all regions as `Launch`.
- `data/regional_source_priorities.csv` now marks all source-need rows as `Launch`.
- `data/coverage_matrix.csv` now uses `launch_research_required` for major launch-scope gaps.
- `data/source_registry.csv` now marks all current sources as `Launch` candidates.
- PostgreSQL seed SQL and SQLite snapshot were regenerated.

Created:

- `LAUNCH_SCOPE.md`

Validation:

- Active contract files were checked for old phased terminology.
- `python scripts/check_db_skeleton.py` passed.
- `python scripts/run_db_migrations.py --dry-run --validate` passed.

---

## Visual Archive System v0 — Design Decisions (Cursor concept session)

This section records frontend/visual-system decisions from a Cursor concept discussion. These decisions are **candidate visual-system directions**, not binding system architecture.

**Status:** Partly superseded by `FRONTEND_FIELD_DECISIONS_v1.md`, `ARCHIVE_BOX_SYSTEM_SPEC_v0.md`, and `PUBLIC_INTERFACE_LAYOUT_SPEC_v0.md`.

Current binding correction:

- Public folder types are now exactly `region`, `theme`, `medium`, and `movement`.
- Historical nodes (`HN*`) remain research/classification/search metadata, not public folder types.
- Time is a sorting axis inside every folder type, not a historical drawer/container.
- Public display numbers no longer include `HN` or movement segments.
- The current public display-number grammar is `GD / {ERA} / {SEQ} / {TIER}-p{PAGE}`.

### Aesthetic and technical approach

- **History archive** metaphor: users face a **filing cabinet**, pull **folders** or **binders**, and read **loose-leaf** documents.
- **Skeuomorphic + 1-bit + functional:** physical cues (tabs, punch holes, stamps, rules) without per-record illustration.
- **Specification-table design:** information is carried by **fixed grids and field tables** so templates can be filled programmatically (human or AI). Avoid bespoke page design per record.
- **AI collaboration constraint:** do not rely on complex painted SVG; use repeatable CSS/grid/SVG components.
- **Language:** **English only** for all UI chrome, labels, stickers, bookmarks, and table headers during development. Source record text may remain in original language.

### Information architecture

| Layer | Meaning |
|-------|---------|
| **Cabinet** | Whole public index |
| **Folder type rail** | Four public entries only: `region`, `theme`, `medium`, `movement` |
| **Folder** | **Filter view**, not a separate corpus. A surface can appear in many folders without changing layout |
| **Time** | Default sorting axis inside folders; not a public folder type |
| **Loose-leaf sheet** | Primary publishable record surface |
| **Index appendix** | Overflow fixed tables (relations, classifications, etc.) |
| **Card** | Sparse branch information **not** sufficient for a full sheet |
| **Registration card** | **Classification ledger** (not museum accession) |
| **Bookmark** | **Pre-authored** editorial supplement (no user login) |
| **Nameplate** | Drawer/bay label (≠ tab) |
| **Tab** | Folder edge label (distinct from nameplate) |

**Excluded formats:** receipt slip; perforated checklist.

### Unified sequence (candidate)

- **`SEQ` is library-wide and unified.** One global publish sequence for primary sheets.
- **Folders do not own separate sequences.** Historical and movement folders are **filters** over the same records, sorted by `SEQ` (with documented tie-breaks).
- After the visual system exists, **records are classified by algorithm**, assigned `SEQ` + template, then **rendered** into the correct folder views automatically.

### Display numbering grammar

```
GD / {ERA} / {SEQ} / {TIER}-p{PAGE}
```

| Segment | Meaning |
|---------|---------|
| `GD` | Project prefix |
| `ERA` | Record time belonging (`date_start`–`date_end`, else best available date text, else `undated`) |
| `SEQ` | **Global** sequence (fixed width, e.g. `00042`) |
| `TIER` | Fixed sheet size class: `S`, `M`, `L`, `XL`, `XXL` |
| `PAGE` | Page within multi-page sheet |

- **Database ids** (`ENT*`, `SR*`, etc.) remain on every sheet separate from display numbers.
- **Public browse:** same `SEQ` can appear in Region, Theme, Medium, and Movement folders. Folder membership is shown in the surface metadata, not encoded into the display number.
- `HN*`, `MV*`, `RM*`, `REG*`, and `GEO*` remain authority/classification references.

### Sheet sizes vs layouts (candidate)

- **Five fixed physical size tiers** (`S`–`XXL`): outer dimensions are discrete and limited.
- **Layouts vary within a tier:** multiple layout template IDs per tier (different grid arrangements, same outer size).
- **Assignment:** content volume + field completeness + relations + image policy → `TIER` + `layout_id` (algorithm to be specified in visual system spec).

### Format inventory (required components)

1. **Nameplate** — drawer/bay id  
2. **Tab** — folder edge (distinct from nameplate)  
3. **Folder cover** — node or movement summary + index of member `SEQ`  
4. **Standard loose-leaf** — five tiers, multiple layouts each  
5. **Index appendix** — fixed overflow tables  
6. **Excerpt strip** — search/citation narrow row  
7. **Sticker** — rights, status, confidence (1-bit hatch, fixed corners)  
8. **Bookmark** — editorial, functional-first (`BM-*` ids)  
9. **Registration card** — classification ledger  
10. **Card** — sparse branch / cross-ref only  

### Registration card vs card (candidate)

**Registration card** records:

- `registration_id`
- **category** (classification type + value)
- **classified_at**
- **modified_at**
- **member_pages** (table: sheet display numbers / `SEQ` / `HN` / `MV|NONE`)
- registrar / notes optional

Visual precedents: **library circulation card** (ledger columns, corner serials, AUTHOR/TITLE header); **library card project** (TITLE \| PUBLICATION table, corner numerals).

**Card** is for **branch information** that cannot yet (or never should) fill a loose-leaf: stubs, cross-refs, provisional aliases. **Promotion rules** to loose-leaf require minimum source/citation/rights/classification checklist (to be detailed in spec).

### Fixed table systems (candidate)

Six mandatory table schemas on sheets (column order fixed):

1. `TABLE-SOURCE` — metadata as found at source  
2. `TABLE-NORMALIZED` — local normalized fields (visually separated)  
3. `TABLE-RIGHTS` — rights and image policies  
4. `TABLE-CLASSIFICATION`  
5. `TABLE-RELATIONS`  
6. `TABLE-CITATIONS`  

Overflow → **index appendix** pages.

### Image zones (candidate)

Four codes, fixed placement per layout template:

| Code | Use |
|------|-----|
| `IMG00` | Empty image frame only; no source image/thumbnail/screenshot rendered; linework/shadow + rights/source text + source link |
| `IMG01` | Thumbnail frame + attribution |
| `IMG02` | Embed / IIIF + credit |
| `IMG03` | Open image + license + source link |
| `IMG04` | Pure text page; no image frame |

Image zones describe image presence state. Image size is controlled separately by `TIER`, layout ID, and template rules.
`IMG00` through `IMG03` assume an image frame exists and are resolved by copyright/display permission. `IMG04` is a script/template signal for no image frame.

### Movement folders and historical nodes

- Representative movements can be public folders, but public folder IDs are folder-view IDs, not raw `MV*` IDs.
- Historical nodes (`HN*`) are not public folders. They remain research/classification metadata and search facets.
- Example: a Bauhaus-related surface may reference `HN008` and `MV011`, but the public movement folder should use a folder-view ID/slug such as `FOL-MOVEMENT-BAUHAUS`.
- Display numbers do not encode `HN`, `MV`, or `NONE`; folder memberships are shown separately.

### Collaboration boundaries (reconfirmed)

| Owner | Responsibility |
|-------|----------------|
| **Codex** | PostgreSQL schema, ingestion, classification fields, API/read models, `SEQ` allocation logic, export |
| **Cursor** | Visual system spec consumption, template components, cabinet UI (after DB gates) |
| **Deep Research** | Produce detailed `VISUAL_ARCHIVE_SYSTEM` specification from prompt below |

### Files for this track

- `DEEP_RESEARCH_VISUAL_ARCHIVE_SYSTEM_PROMPT.md` — referenced as the future long-form research prompt for the full visual archive design system. The file is not currently present in the folder and should be recreated/re-written after global coverage review before use.

### Predecessor prompt (superseded in emphasis)

- `DEEP_RESEARCH_FRONTEND_CONCEPT_PROMPT.md` — earlier generic UI/precedent brief; it should remain secondary until the global coverage baseline is accepted and the visual archive prompt is rewritten.

### Visual reference assets (discussion)

Collected reference patterns (not project assets): library circulation card; library card project cards; Bauhaus Dessau letterhead (reference row, address bracket, punch holes); employee record folder tabs; NASA manual index; functional numbered grid layout. Stored in Cursor session assets for design research.

### Open items for Deep Research to close

- Exact `SEQ` allocation on publish/deprecate  
- Corner stamp field matrix per layout  
- Minimum layouts per tier (≥3 each)  
- Registration card ID format (`REG-*`)  
- Bookmark initial catalog  
- Grid unit (gu) base measure  
- Classification → `TIER` + `layout_id` decision table  

### Next steps

1. Complete global coverage baseline and database/API classification axes.  
2. Rewrite `DEEP_RESEARCH_VISUAL_ARCHIVE_SYSTEM_PROMPT.md` using the completed coverage baseline.  
3. Run Deep Research only after that rewrite.  
4. Review output; commit as `VISUAL_ARCHIVE_SYSTEM_SPEC.md` (+ supporting docs listed in prompt Part N).  
5. Codex: align API payloads only after the final visual system spec is accepted.  
6. Cursor: implement template renderer only after spec + `FRONTEND_HANDOFF_CONTRACT.md` gates are met.

---

## Global Coverage Classification Skeleton

User direction:

- The design system should not be finalized until global coverage is structurally represented.
- The system must support broad launch coverage across Europe, the Americas, Japan, Korea, East Asia, Mainland China, Hong Kong, Taiwan, Southeast Asia, South Asia, Middle East and North Africa, Africa, and Oceania/Pacific.
- Country/region/date/year classification is a database requirement before frontend design.
- Cursor's visual archive concept should remain a candidate until this coverage work is complete.

Created:

- `scripts/generate_global_coverage_data.py`
- `db/005_global_classification_skeleton.sql`
- `data/classification_axes.csv`
- `data/geographies.csv`
- `data/regional_movements.csv`
- `data/regional_event_nodes.csv`

Database/API updates:

- Added `classification_axes`, `geographies`, `geography_aliases`, `regional_movements`, `regional_event_nodes`, `normalized_dates`, `entity_geographies`, and `source_record_geographies`.
- Added read models: `api_classification_axes`, `api_geographies`, `api_regional_movements`, and `api_regional_event_nodes`.
- Reordered migration plan so read models run after coverage and global classification tables.

Seed coverage counts:

- 10 classification axes.
- 109 geographies / country-context / territory / regional-context rows.
- 74 regional movements and formations.
- 48 regional event nodes.
- 867 searchable seed documents after regeneration.

Validation:

- `python3 scripts/check_db_skeleton.py` passed.
- `python3 scripts/run_db_migrations.py --dry-run --validate` passed.
- `python3 scripts/search_seed.py China 10` returned Mainland China plus related East Asia/Hong Kong/Taiwan records.
- `python3 scripts/search_seed.py Korea 8` returned South Korea, North Korea, Korea, and East Asia records.
- `python3 scripts/search_seed.py Japan 8` returned Japan source/geography/event records.
- `python3 scripts/search_seed.py Africa 8` returned Africa, South Africa, African event nodes, and related counter-canonical records.
- `python3 scripts/search_seed.py Arabic 8` returned MENA, Arabic typography, Egypt, Levant, Maghreb, and related script contexts.

---

## Archive-Cabinet Publication Surface Normalization

User direction:

- Treat the archive-cabinet / 1-bit / specification-table design system as the current working design-system definition.
- Check it against the actual database.
- Begin the first normalization step before Deep Research visual design work.
- Run a Deep Research coverage audit before rewriting the visual archive prompt.

Finding:

- The existing database supported source records, entities, rights, citations, relations, classifications, search, geography, and global coverage.
- It did not yet normalize the public paper layer: global `SEQ`, display number, sheet/card distinction, `TIER`, `layout_id`, image zone, multi-page sheets, six table rows, folder/filter memberships, registration cards, sparse cards, or bookmarks.

Created:

- `DESIGN_SYSTEM_DATABASE_AUDIT_v0.md`
- `db/006_publication_surface_skeleton.sql`
- `DEEP_RESEARCH_GLOBAL_COVERAGE_AUDIT_PROMPT.md`

Database/API updates:

- Added publication/display enums: `publication_surface_type`, `sheet_tier`, `image_zone_code`, `surface_table_kind`, `folder_view_type`.
- Added tables: `display_templates`, `publication_surfaces`, `publication_surface_pages`, `surface_table_rows`, `folder_views`, `folder_memberships`, `filing_registry_cards`, `filing_registry_members`, `sparse_cards`, `archive_bookmarks`.
- Added read models: `api_publication_surfaces`, `api_publication_surface_pages`, `api_surface_table_rows`, `api_folder_views`, `api_folder_memberships`, `api_filing_registry_cards`, `api_filing_registry_members`, `api_sparse_cards`, `api_archive_bookmarks`.
- Updated API and frontend handoff contracts with publication surface, folder, registry card, and fixed-table expectations.

Boundary:

- This starts database normalization for the design system.
- It does not decide final dimensions, grid unit, layout library, or visual styling.
- Those decisions should wait until first experimental source records are normalized and rendered through the six-table paper model.

---

## Deep Research Reports Review

Reviewed:

- `Audit of the Global Coverage Framework for a Rights-Aware Graphic Design History Index.docx`
- `Authority and Vocabulary Normalization Audit for a Rights-Aware Graphic Design Archive Gateway.docx`

Created:

- `DEEP_RESEARCH_REPORTS_REVIEW_v0.md`

Key finding:

- Both reports say the framework is promising but not ready for design-system freeze.
- The blockers are structural: geography granularity, multilingual/script modeling, source-family diversity, authority-resolution workflow, and protocol-aware rights handling.

Important discrepancy:

- The expected `Source & Rights Feasibility Audit` report is not currently present in the project folder.
- The two available new reports are global coverage and authority/vocabulary normalization.

Immediate implications:

- Add an authority-normalization schema layer.
- Expand coverage seed rows for missing geographies, regional movements, and event nodes.
- Expand source registry from the coverage audit source recommendations.
- Keep visual archive prompt rewrite blocked until coverage, authority, source/rights, and experimental ingest results are available.

Implementation update:

- Added `db/007_authority_normalization_skeleton.sql`.
- Added authority/evidence enums: `authority_match_status`, `appellation_type`, `mapping_relation`, `evidence_mode`.
- Added `evidence_bundles`, `evidence_bundle_items`, `authority_resolution_events`, `entity_appellations`, and `geography_appellations`.
- Expanded existing authority, identifier, relation, assertion, classification, date, source record, geography, and rights review tables with multilingual, evidence, review, and protocol fields.
- Added read models for evidence bundles, external identifier status, authority resolution events, appellations, relation predicate rules, and protocol-aware rights.
- Updated API/frontend/schema/database docs so public UI can expose source-language labels, unresolved authority matches, transliteration, evidence bundles, and predicate warnings.
- Expanded global coverage seed rows from the coverage audit:
  - geographies: 71 → 109;
  - regional movements/formations: 55 → 74;
  - regional event nodes: 35 → 48;
  - searchable seed documents: 797 → 867.
- Added coverage for Central Asia, Caucasus, Iran, Palestine/Israel, Caribbean subcontexts, Nepal, Cambodia, Myanmar, Singapore/Malaya/Jawi-Rumi, West Africa, Horn of Africa, Indigenous North America, Aboriginal Australia, Torres Strait Islander contexts, Māori print, Melanesia, Polynesia, and Micronesia.

---

## Source and Rights Feasibility Report Review

Reviewed:

- `Source and Rights Feasibility Audit for a Modern Graphic Design History Research Gateway.docx`

Created:

- `SOURCE_RIGHTS_REPORT_REVIEW_v0.md`
- `db/008_source_rights_policy_skeleton.sql`
- `data/experimental_ingest_shortlist.csv`

Key decision:

- `SOURCE_RIGHTS_READY_FOR_EXPERIMENTAL_INGEST: yes`
- But image-rich ingest is blocked until source-level defaults, item-level rights overrides, versioned terms reviews, and renderer-level `IMG00` default behavior are enforced.

Database/API updates:

- Added source/right policy enums: `source_record_policy`, `public_display_policy`, `asset_origin`, `terms_review_decision`.
- Expanded `sources`, `source_terms_reviews`, `rights_reviews`, `image_assets`, and `ingestion_runs` with policy, evidence, rights, protocol, and ingest metrics fields.
- Added `experimental_ingest_candidates`.
- Added read models: `api_source_policy_summary`, `api_source_terms_review_policy`, and `api_experimental_ingest_candidates`.

Seed/update counts:

- Added 24 experimental ingest candidates.
- Searchable seed documents: 867 → 891.

Operational rule:

- Unknown or ambiguous image rights default to `IMG00`.
- The frontend must consume rights decisions; it must not decide image display from raw image URLs.

---

## First Experimental Ingest Scope Prompt

Created:

- `DEEP_RESEARCH_FIRST_INGEST_SCOPE_PROMPT.md`
- `FIRST_EXPERIMENTAL_INGEST_SCOPE_BRIEF_v0.md`

Reason:

- The source/rights audit proves that experimental ingest is possible with conservative guardrails, but it does not decide which movements, formations, or event nodes should be represented in the first controlled ingest.
- The current 24 experimental candidates test source behavior and image zones, but they do not yet guarantee global movement/event coverage.

Decision:

- Run one additional Deep Research pass before actual crawling.
- The new research should define a rights-safe, globally balanced first ingest scope across movements, dateable events, regions, source families, media regimes, and image zones.
- This is a controlled seed set for the database and interface grammar, not a reduction of the project's global ambition.

---

## First Experimental Ingest Scope Report Review

Reviewed:

- `First Experimental Ingest Scope for a Rights-Aware Graphic Design History Archive.docx`

Created:

- `FIRST_INGEST_SCOPE_REPORT_REVIEW_v0.md`
- `db/009_first_ingest_scope_skeleton.sql`
- `scripts/apply_first_ingest_scope_seed.py`

Key decision:

- `FIRST_INGEST_SCOPE_READY: yes_with_conditions`
- `FIRST_INGEST_CAN_START_AFTER_TERMS_REVIEW: yes`
- Recommended first controlled ingest: 48 target records, 15 movement/formations, 15 event-node anchors, and 15 source families.

Implementation update:

- Added 15 first-ingest scope cells C01-C15 to `experimental_ingest_shortlist.csv`.
- Added first-ingest movement rows RM075-RM089.
- Added first-ingest event anchor rows REN049-REN063.
- Added 19 concrete source registry rows for first-ingest source families and support sources.
- Added 37 multilingual/query-profile search vocabulary rows.
- Added schema fields for source-record parent-child relations, issue/page chains, capture datetime, ICIP/protocol flags, query profiles, target record counts, and expected paper-surface types.
- Regenerated PostgreSQL seed SQL and SQLite search snapshot.

Seed/update counts:

- sources: 35 -> 54
- search vocabulary: 163 -> 200
- regional movements/formations: 74 -> 89
- regional event nodes: 48 -> 63
- experimental ingest candidates: 24 -> 39
- searchable seed documents: 891 -> 992

Operational rule:

- First ingest is now scoped but still blocked on source terms review.
- All first-ingest cells default to `IMG00` unless item-level evidence permits escalation.
- `IMG00` means an intentionally empty archive image frame, not a removed image area.
- `IMG04` means no image frame and should be reserved for pure text/appendix/continuation pages. It is a script/template signal, not a copyright level.

---

## Deep Research Prompts Before First Ingest

Created:

- `DEEP_RESEARCH_SOURCE_TERMS_ACCESS_PROMPT.md`
- `DEEP_RESEARCH_FIELD_MAPPING_INGEST_CONTRACT_PROMPT.md`
- `DEEP_RESEARCH_FIRST_48_TARGET_SELECTION_PROMPT.md`

Reason:

- The next step is still framework work, but only the final pre-ingest layer.
- Three independent research questions must be separated:
  - whether each source can be accessed and under what terms;
  - how heterogeneous source records map into the ingest JSON and six-table paper model;
  - which 48 concrete target records or deterministic search paths should be used.

Boundary:

- These prompts do not authorize crawling.
- They should return source terms rows, ingest-contract requirements, and target-record candidates for review before the first controlled ingest begins.

---

## Source Access, Ingest Contract, and First 48 Reports Reviewed

Reviewed:

- `Rights and Access Review for a Rights-Aware Graphic Design History Archive Index.docx`
- `Field Mapping and Ingest Contract Review for a Rights-Aware Graphic Design History Archive.docx`
- `First 48 Record Target Selection for a Rights-Aware Modern Graphic Design History Archive Index.docx`

Created:

- `INGEST_CONTRACT_AND_TARGETS_REVIEW_v0.md`
- `db/011_ingest_contract_targets_skeleton.sql`

Key decision:

- `SOURCE_TERMS_READY_FOR_FIRST_INGEST: yes_with_conditions`
- `INGEST_CONTRACT_READY: yes_with_conditions`
- `FIRST_48_TARGETS_READY: yes_with_conditions`

Meaning:

- The project can proceed with schema completion and controlled manual or semi-automated ingest preparation.
- The project should not begin bulk crawling or image harvesting.
- The first 48 targets are a verification set, not already-ingested content.

Database/API updates:

- Added `source_record_relations` for issue/page, collection/item, web-capture/original, and other source-record host/part links.
- Added `digital_representations` so source records/entities remain separate from images, thumbnails, IIIF, embeds, PDFs, and web captures.
- Added `field_provenance` so normalized fields can point back to source fields, citations, evidence bundles, and review status.
- Added `record_family_profiles` and `ingest_validation_rules` for publishable sheets, cards, authority-only records, IMG00 link-only records, IMG04 text appendices, periodical chains, web captures, and multilingual records.
- Added `first_ingest_record_targets` as an operational registry for the first 48 target records/search paths.
- Expanded source terms reviews with access mode, API availability, API key, automation level, forbidden behavior, default image zone, evidence URLs, and terms-checked date.
- Expanded publication surface pages with page-level image zone, `has_image_frame`, and image layout profile.
- Added read models: `api_source_record_relations`, `api_digital_representations`, `api_field_provenance`, `api_record_family_profiles`, `api_ingest_validation_rules`, and `api_first_ingest_record_targets`.
- Added `data/first_ingest_record_targets.csv` with 48 first-ingest target records/search paths from the Deep Research report.
- Updated seed generation and SQLite snapshot tooling to include `first_ingest_record_targets`.

Operational rule:

- `IMG00` through `IMG03` imply an image frame exists and the visible state is governed by rights evidence.
- `IMG04` means no image frame and should be used for text, appendix, authority, event, institutional, or standards pages.
- Any upgrade above `IMG00` requires item-level rights evidence; source-level openness alone is not enough.

Prompt organization:

- Moved existing `DEEP_RESEARCH_*_PROMPT.md` files into `prompts/` so used research prompts are kept separately from framework, schema, and report-review documents.

Validation:

- `python3 scripts/check_db_skeleton.py` passed.
- `python3 scripts/run_db_migrations.py --dry-run --validate` passed.
- Search validation found first-ingest target rows for `Shape of Land`, `Program of the State Bauhaus`, and `CSS1`.

Current searchable seed count:

- `searchable_documents` / SQLite `search_docs`: 992 -> 1040.

---

## Automated Archive Workflow Defined

Created:

- `AUTOMATED_ARCHIVE_WORKFLOW_v0.md`

Core clarification:

- The project is a modern automated archive workflow, not only a public website.
- The human researcher provides the conceptual and methodological framework.
- Codex performs large-scale mechanical verification and structured preparation.
- Scripts transform approved source records into normalized database rows.
- The database becomes the archive core.
- Publication surfaces are generated from database state as rights-aware sheets, cards, folders, appendices, and registration cards.

Workflow:

1. Human research framework.
2. Target scope and historical spine.
3. Codex-assisted source verification.
4. Structured source record capture.
5. Scripted normalization and classification.
6. Rights and protocol review gates.
7. Database as archive core.
8. Publication surface assignment.
9. Loose-leaf/card/folder generation.
10. Search, browse, citation, and summary interface.

Boundary:

- Codex and scripts organize and verify evidence; they do not invent historical evidence.
- Public pages should be generated from structured records, citations, rights decisions, and templates rather than manually designed one by one.

---

## First Target Verification Made Machine-Readable

Created:

- `FIRST_48_TARGET_VERIFICATION_PASS_v0.md`
- `data/first_ingest_target_verifications.csv`
- `prompts/DEEP_RESEARCH_UNRESOLVED_FIRST_TARGETS_PROMPT.md`

Database/API updates:

- Added `first_ingest_target_verifications` to `db/011_ingest_contract_targets_skeleton.sql`.
- Added `api_first_ingest_target_verifications`.
- Updated seed generation and SQLite snapshot scripts to include target verification rows.

Current verification result:

- Ready for manual metadata ingest now: 30.
- Ready only after exact URL / browser / page-level recheck: 12.
- Search-path only and not yet source records: 5.
- Recommended source replacement: 1.

Important finding:

- FIT026 should likely be replaced by Seoul Museum of Art Archive record `MA-06-00004326`, because the original OpenArchive target was not confirmed and SEMA provides clearer metadata and rights warning.

Validation:

- `python3 scripts/check_db_skeleton.py` passed.
- `python3 scripts/run_db_migrations.py --dry-run --validate` passed.
- Search validation confirms verification records are searchable, including `replace_target` and `ready_manual_open_with_protocol`.
- `python3 scripts/export_ready_manual_targets.py` generated `data/ready_manual_ingest_targets.csv` with 30 ready targets.

---

## Manual Source Record Draft Pass

Created:

- `scripts/generate_manual_source_record_drafts.py`
- `data/manual_source_records/*.json`
- `data/manual_source_records_index.csv`
- `MANUAL_SOURCE_RECORD_DRAFTS_v0.md`

Updated:

- `db/manual_source_record.schema.json`
- `scripts/validate_manual_source_record.py`
- `data/source_registry.csv`
- `data/README.md`
- `scripts/check_db_skeleton.py`
- `data/archive_seed.sqlite`
- `db/010_seed_data.sql`

Source registry additions:

- `SRC055` Getty ULAN
- `SRC056` Getty CONA
- `SRC057` museum.or.jp
- `SRC058` JAGDA
- `SRC059` University of Hong Kong Libraries
- `SRC060` National Archives of Singapore
- `SRC061` ICOD
- `SRC062` NYPL Digital Collections

Methodological clarification:

- `IMG00`-`IMG03` are image-frame presence/display states resolved by rights evidence.
- `IMG04` is a no-image-frame page state for text, authority, event, standard, appendix, or collection pages.
- Image code does not determine image size; size remains a publication template/layout decision.

Result:

- 30 ready targets were converted into candidate manual source record JSON drafts.
- 30/30 drafts passed local validation.
- Draft records preserve uncertainty and are not final ingested records.

Validation:

- `python3 scripts/generate_manual_source_record_drafts.py` passed.
- `python3 scripts/validate_manual_source_record.py data/manual_source_records` passed for all 30 drafts.
- `python3 scripts/check_db_skeleton.py` passed.
- `python3 scripts/run_db_migrations.py --dry-run --validate` passed.
- Search validation confirms the new source registry rows are discoverable.

Current searchable seed count:

- `searchable_documents` / SQLite `search_docs`: 1088 -> 1096.

---

## Fallback and Ingest Status Policy Added

Created:

- `FALLBACK_AND_INGEST_STATUS_POLICY_v0.md`
- `scripts/generate_fallback_source_stubs.py`
- `data/fallback_source_stubs.csv`

Updated:

- `db/011_ingest_contract_targets_skeleton.sql`
- `db/003_read_models.sql`
- `scripts/build_sqlite_snapshot.py`
- `scripts/generate_postgres_seed_sql.py`
- `scripts/check_db_skeleton.py`
- `AUTOMATED_ARCHIVE_WORKFLOW_v0.md`
- `FRONTEND_HANDOFF_CONTRACT.md`
- `DATA_DICTIONARY.md`
- `data/README.md`
- `data/archive_seed.sqlite`
- `db/010_seed_data.sql`

Core rule:

- If a source cannot be fetched, confirmed, rights-cleared, or safely captured, the historical area remains present as a fallback source stub.
- A fallback source stub is not a source record and not a published sheet.
- It preserves source/search links, target label, scope cell, verification decision, blocking reason, required next action, and expected `IMG` state.

Current result:

- 18 fallback source stubs generated from the non-ready first-target verification rows.
- Together with the 30 manual source record drafts, all 48 first targets now have a structured state.

Validation:

- `python3 scripts/generate_fallback_source_stubs.py` passed.
- `python3 scripts/check_db_skeleton.py` passed.
- `python3 scripts/run_db_migrations.py --dry-run --validate` passed.
- Search validation confirms fallback stubs are searchable, including `replacement_recommended` and `Search at source`.

Current searchable seed count:

- `searchable_documents` / SQLite `search_docs`: 1096 -> 1114.

---

## Source Redundancy Reports Integrated

Reviewed:

- `Rights-Aware Source Redundancy Audit for Modern Graphic Design History.docx`
- `Rights-Aware Remediation of Unresolved Graphic Design Archive Targets.docx`
- `Rights-aware source expansion for a global graphic design history archive index.docx`

Created:

- `scripts/extract_deep_research_report_tables.py`
- `scripts/generate_fallback_remediation_projection.py`
- `DEEP_RESEARCH_SOURCE_REDUNDANCY_REVIEW_v0.md`
- `db/012_deep_research_outputs_skeleton.sql`
- `data/source_redundancy_candidates.csv`
- `data/source_redundancy_triage.csv`
- `data/recommended_six_target_ingest_sets.csv`
- `data/fallback_remediation_recommendations.csv`
- `data/fallback_remediation_projection.csv`
- `data/global_source_expansion_candidates.csv`
- `data/first_production_low_friction_sources.csv`
- `data/high_value_fragile_sources.csv`

Updated:

- `db/003_read_models.sql`
- `scripts/build_sqlite_snapshot.py`
- `scripts/generate_postgres_seed_sql.py`
- `scripts/run_db_migrations.py`
- `scripts/check_db_skeleton.py`
- `data/README.md`
- `data/archive_seed.sqlite`
- `db/010_seed_data.sql`

Key result:

- The reports converted the fallback problem from 18 unresolved targets into a remediation projection.
- Projected after source-level verification:
  - 10 replacement candidates.
  - 3 candidate promotions.
  - 2 browser/page recheck rows.
  - 3 rows remaining fallback stubs.
- Projected unresolved fallback/recheck rate: 5 / 48 = 10.4%.

Source expansion result:

- 84 global source-expansion candidates extracted.
- 20 low-friction production-source candidates extracted.
- 20 high-value fragile sources extracted.

Caveat:

- The expansion table is still weak for South Asia, MENA, Africa, and Oceania/Indigenous sources as structured production-source candidates.
- These areas need a focused follow-up audit before global source coverage can be treated as stable.

Validation:

- `python3 scripts/extract_deep_research_report_tables.py` passed.
- `python3 scripts/generate_fallback_remediation_projection.py` passed.
- `python3 scripts/check_db_skeleton.py` passed.
- `python3 scripts/run_db_migrations.py --dry-run --validate` passed.
- Search validation confirms projected remediation rows and global source expansion rows are searchable.

Current searchable seed count:

- `searchable_documents` / SQLite `search_docs`: 1114 -> 1388.

---

## Remediation Source Verification Pass

Created:

- `REMEDIATION_SOURCE_VERIFICATION_PASS_v0.md`
- `scripts/generate_remediation_source_record_drafts.py`
- `data/remediation_source_verifications.csv`
- `data/remediation_source_records_index.csv`
- `data/remediation_source_records/*.json`

Updated:

- `data/source_registry.csv`
- `data/README.md`
- `db/012_deep_research_outputs_skeleton.sql`
- `db/003_read_models.sql`
- `scripts/build_sqlite_snapshot.py`
- `scripts/generate_postgres_seed_sql.py`
- `scripts/check_db_skeleton.py`
- `data/archive_seed.sqlite`
- `db/010_seed_data.sql`

Key result:

- 10 remediation verification rows were created from the fallback remediation projection.
- 8 rows generated valid candidate source-record drafts.
- 2 rows remain fallback stubs because exact source evidence or a reviewed bibliographic anchor is still missing.
- `IMG00` and `IMG04` are now both represented in remediation records:
  - `IMG00`: fixed image frame exists, but no image is displayed.
  - `IMG04`: text/source page with no image frame.

Source registry expansion:

- `SRC063`: Biblioteca Nacional Digital de Chile
- `SRC064`: NDL Search
- `SRC065`: Seoul Museum of Art
- `SRC066`: National Library Board Singapore

Validation:

- `python3 scripts/generate_remediation_source_record_drafts.py` passed.
- `python3 scripts/validate_manual_source_record.py data/remediation_source_records` passed.
- `python3 scripts/check_db_skeleton.py` passed.
- `python3 scripts/run_db_migrations.py --dry-run --validate` passed.
- Search validation confirms the new source rows and remediation evidence are discoverable.

Current searchable seed count:

- `searchable_documents` / SQLite `search_docs`: 1388 -> 1402.

---

## Capture Batch 001

Created:

- `CAPTURE_BATCH_001_REPORT_v0.md`
- `scripts/run_capture_batch_001.py`
- `scripts/assign_capture_batch_cells.py`
- `db/013_capture_batch_skeleton.sql`
- `data/capture_batch_001_records.csv`
- `data/capture_batch_001_source_summary.csv`
- `data/capture_batch_001_cell_assignments.csv`
- `data/capture_batch_001_cell_summary.csv`
- `data/capture_batch_001_next_generation_queue.csv`
- `data/capture_batch_001_raw/*.json`

Updated:

- `db/003_read_models.sql`
- `scripts/build_sqlite_snapshot.py`
- `scripts/generate_postgres_seed_sql.py`
- `scripts/run_db_migrations.py`
- `scripts/check_db_skeleton.py`
- `data/README.md`
- `data/archive_seed.sqlite`
- `db/010_seed_data.sql`

Capture directions:

- `D01`: open and restricted museum poster objects.
- `D02`: design museum poster catalogue metadata.
- `D03`: public poster archive search records.

Key result:

- 50 rows captured.
- 0 source-level failures.
- Image-state distribution after row-level assignment:
  - `IMG00`: 12
  - `IMG01`: 4
  - `IMG02`: 8
  - `IMG03`: 13
  - `IMG04`: 13
- Cell assignment distribution:
  - 7 rows connect to existing C-cells.
  - 23 rows suggest proposed new cells.
  - 20 rows remain in the unassigned capture pool.
- Proposed new cells surfaced by the batch:
  - `PC01`: Art Nouveau and Belle Epoque poster culture.
  - `PC02`: World War public-information and propaganda posters.
  - `PC03`: 1970s London political solidarity posters.
  - `PC04`: South and Central Asian political poster collections.
  - `PC05`: Contemporary campaign graphics and network circulation.
  - `PC06`: Exhibition poster as design-history metadata.
- All rows keep `local_copy_permitted=false` until record-level review.

Validation:

- `python3 scripts/run_capture_batch_001.py` passed.
- `python3 scripts/assign_capture_batch_cells.py` passed.
- `python3 scripts/check_db_skeleton.py` passed.
- `python3 scripts/run_db_migrations.py --dry-run --validate` passed.
- Search validation confirms capture rows, cell assignments, summaries, and next-generation queue rows are discoverable.

Current searchable seed count:

- `searchable_documents` / SQLite `search_docs`: 1402 -> 1542.

---

## Surface System Reports Integrated

Reviewed:

- `Archive Production Rulebook for a Rights-Aware Research Gateway to Modern Graphic Design History.docx`
- `File Naming and Archival Storage Rulebook for a Rights-Aware Graphic Design History Archive Index.docx`
- `Surface Taxonomy Rulebook for a Rights-Aware Graphic Design History Archive.docx`
- `Rights-Aware Archive Box Interface Framework for Modern Graphic Design History.docx`

Created:

- `ARCHIVE_PRODUCTION_RULEBOOK_v0.md`
- `FILE_NAMING_AND_ARCHIVAL_STORAGE_v0.md`
- `SURFACE_TAXONOMY_RULEBOOK_v0.md`
- `ARCHIVE_BOX_INTERFACE_FRAMEWORK_v0.md`
- `DEEP_RESEARCH_SURFACE_SYSTEM_REVIEW_v0.md`

Key decisions:

- Time is a sorting axis, not a container.
- Primary folder types are Region, Theme, Medium, and Movement.
- Folders are aggregation/filter views and do not change record layout.
- Capture batches are production candidate pools.
- Main sheets require a completeness threshold and essential gates.
- Below-threshold records remain visible as cards, fallback stubs, proposed cell items, or unassigned research items.
- Source return, rights state, uncertainty, and citation are structural interface elements.

Recommended next step:

- Write a frontend handoff spec for the archive box system before more capture work.

---

## Archive Box Implementation Specs Added

Created:

- `ARCHIVE_BOX_SYSTEM_SPEC_v0.md`
- `PUBLIC_INTERFACE_LAYOUT_SPEC_v0.md`
- `SURFACE_GENERATION_PIPELINE_v0.md`

Key decisions:

- The public system is now defined as an archive box, not a timeline site: box -> folder type -> folder -> chronological record stream -> sheet/card/stub/appendix -> source.
- Time remains the default ordering logic across Region, Theme, Medium, and Movement folders.
- Folder views aggregate fixed record surfaces; folders do not own records and do not alter sheet layout.
- Main sheets require essential gates plus a completeness score of at least 60. Lower-completeness items route to cards, fallback stubs, compound sheets, proposed folder items, or unassigned research items.
- `IMG00-IMG04` is defined as image existence/display state, not page size: `IMG00` keeps an empty image bay, `IMG04` removes the image bay for pure text/source/authority pages.
- Frontend rendering should consume generated surface payloads, not raw capture rows.
- Final `SEQ` and `GD/...` display numbers should not be minted until source review and rights review gates are implemented.

Next implementation target:

- Build the first surface payload schema and generator around capture batch 001.
- Generate provisional folder cover/index payloads and provisional sheet/card/stub payloads.
- Keep all outputs in a generated/staged publication layer until source and rights review rules are enforced.

---

## Simple Frontend Handoff Prepared

Created:

- `CURSOR_SIMPLE_FRONTEND_BRIEF_v0.md`
- `data/public_surface_mock_v0.json`

Purpose:

- Provide Cursor with a narrow first frontend scope.
- Keep the prototype static and rights-aware.
- Make the archive box, folder, sheet, card, stub, and IMG00-IMG04 rules renderable before real API integration.

Frontend boundary:

- Build a minimal `/frontend` app from static mock data.
- Required routes: `/`, `/folders`, `/folders/[type]`, `/folders/[type]/[slug]`, `/surfaces/[id]`, `/search`.
- Search is a placeholder only.
- No WebLLM, crawling, ingestion, authentication, graph visualization, or admin workflow in this version.

Key protection:

- The frontend must not render raw capture data directly.
- The frontend must not display images for `IMG00`.
- The frontend must render no image frame for `IMG04`.
- Every surface must keep source return and rights stamp visible.

---

## Frontend Field Decisions Resolved

Created:

- `FRONTEND_FIELD_DECISIONS_v1.md`

Updated:

- `CURSOR_SIMPLE_FRONTEND_BRIEF_v0.md`
- `data/public_surface_mock_v0.json`
- `FILE_NAMING_AND_ARCHIVAL_STORAGE_v0.md`
- `SURFACE_GENERATION_PIPELINE_v0.md`
- `API_CONTRACT.md`
- `FRONTEND_HANDOFF_CONTRACT.md`
- `db/006_publication_surface_skeleton.sql`
- `db/003_read_models.sql`

Resolved decisions:

- Historical nodes (`HN*`) remain research/classification/search metadata, but are not public folder types.
- Public folder types are exactly `region`, `theme`, `medium`, and `movement`.
- Public display numbers now use `GD / {ERA} / {SEQ} / {TIER}-p{PAGE}`.
- Public folder IDs now use folder-view IDs such as `FOL-MEDIUM-POSTER`; authority IDs such as `REG*`, `GEO*`, `MV*`, and `RM*` live in `authorityRefs`.
- Frontend v1 should use static local search over the mock payload only.
- Mock data now includes a sparse card (`card.sparse.v0`) as well as sheet and fallback-stub examples.

Validation:

- `data/public_surface_mock_v0.json` parses as valid JSON.
- Mock folder/surface references are internally consistent: 7 folders, 5 surfaces, 0 missing refs.
- `python3 scripts/check_db_skeleton.py` passed.
- `python3 scripts/run_db_migrations.py --dry-run --validate` passed.

---

## Surface Field Contract Frozen

Created:

- `SURFACE_FIELD_CONTRACT_v1.md`

Purpose:

- Freeze the fields that future capture/manual-ingest/export scripts must fill.
- Translate the archive-box visual system into a stable surface payload contract.
- Prevent future frontend or ingest work from adding ad hoc page structures.

Frozen elements:

- Public folder types: `region`, `theme`, `medium`, `movement`.
- Display number grammar: `GD / {ERA} / {SEQ} / {TIER}-p{PAGE}`.
- Surface types: `sheet`, `card`, `fallback_stub`, `appendix`, `folder_cover`, `folder_index`, `registration_card`, `bookmark`.
- Image states: `IMG00` through `IMG04`.
- Six table kinds and order: `SOURCE`, `NORMALIZED`, `RIGHTS`, `CLASSIFICATION`, `RELATIONS`, `CITATIONS`.
- Required base surface fields, image/rights/folder/authority/provenance fields, and null-display rules.

Implementation note:

- Frontend and generated payload scripts should now treat `SURFACE_FIELD_CONTRACT_v1.md` as the primary field contract.
- Future generated payload target remains `generated/public_surfaces_v1.json`.

---

## Early Region Capture Batch 1830-1930

Created:

- `scripts/run_early_region_capture_1830_1930.py`
- `data/capture_batch_early_region_1830_1930_records.csv`
- `data/capture_batch_early_region_1830_1930_source_summary.csv`
- `data/capture_batch_early_region_1830_1930_raw/`
- `generated/public_surfaces_v1.json`

Also synced the generated payload into the current frontend mock locations:

- `frontend/src/data/public_surface_mock_v0.json`
- `frontend/public/data/public_surface_mock_v0.json`

Scope:

- Region-oriented early graphic design / commercial print capture.
- Date range: 1830-1930.
- Sources: Art Institute of Chicago API, V&A Collections API, Library of Congress loc.gov API, Cleveland Museum Open Access API.
- Excludes obviously non-graphic objects where possible by requiring print/advertising/poster/trade-card/lithographic relevance terms.

Results:

- 77 captured rows.
- 77 generated staged surfaces.
- 12 generated folders.
- Date range in records: 1830-1930.
- Source counts:
  - AIC: 20
  - V&A: 25
  - LOC: 20
  - Cleveland: 12
- Image-state distribution:
  - `IMG00`: 10
  - `IMG01`: 13
  - `IMG02`: 9
  - `IMG03`: 21
  - `IMG04`: 24
- Folder distribution:
  - Region folders: Belgium, France, Germany, United Kingdom, United States, Unresolved region.
  - Theme folder: Nineteenth-century commercial print ecology.
  - Medium folders: Advertisement, Commercial print, Lithographic print, Poster, Trade card.

Validation:

- Generated payload has 77 surfaces, 12 folders, and 0 missing folder/surface references.
- `npm run build` in `/frontend` passed and generated 99 static pages.

Notes:

- These surfaces are staged visual-verification data, not final published source records.
- Unresolved-region rows remain visible as archive states and should be reviewed later for better region assignment.

---

## Reading Text Layer Added to Early Region Payload

Issue identified:

- The first generated early-region payload had enough object metadata for indexing, but too little prose for reading.
- The problem was not that archives lack text. The first pass used search/object-list metadata and did not fetch item-detail text fields.

Verified source text availability:

- AIC detail API can expose `description`, `short_description`, and related history fields for some records.
- V&A detail API can expose `physicalDescription`, category text, and production/materials notes.
- LOC item JSON can expose catalogue `notes`, subjects, and item-level metadata.
- Cleveland API can expose `description`, inscriptions, provenance, exhibitions, and creator descriptions.

Updated:

- `scripts/run_early_region_capture_1830_1930.py`
- `frontend/src/types/archive.ts`
- `frontend/src/components/archive/blocks.tsx`
- regenerated `data/capture_batch_early_region_1830_1930_records.csv`
- regenerated `generated/public_surfaces_v1.json`
- synced frontend static data copies.

New payload fields:

- `source_description`
- `source_notes`
- `source_subjects`
- `descriptionSummary`
- `sourceDescription`
- `sourceNotes`
- `sourceSubjects`

Results after regeneration:

- 77 rows total.
- 47 rows with `source_description`.
- 45 rows with `source_notes`.
- 58 rows with `source_subjects`.
- 56 generated surfaces with `descriptionSummary`.

Frontend behavior:

- The lead/reading block now uses `descriptionSummary`, `sourceDescription`, or `sourceNotes`.
- It no longer uses the rights label as pseudo-body text.

Validation:

- `npm run build` in `/frontend` passed after adding the reading text layer.

---

## Compound Surface Optimization Added

Issue addressed:

- The early-region payload contained several repeated or series-like source records that were technically valid as atomic captures, but visually repetitive as standalone public sheets.
- Keeping every repeated member as an independent main sheet made folder browsing feel like a duplicated table set rather than an archive file.

Decision:

- Source/capture rows remain atomic in `data/capture_batch_early_region_1830_1930_records.csv`.
- Public surfaces may collapse obvious series-like atomic rows into one compound sheet.
- This is a public-interface optimization only; it does not erase source records, source links, dates, image states, or rights evidence.

Updated:

- `scripts/run_early_region_capture_1830_1930.py`

Added:

- `--from-csv` regeneration mode for rebuilding public static payloads from existing capture rows without making network requests.
- Compound grouping pass for repeated/series-like early records.
- Compound sheets use `templateId: sheet.compound.v0`, `layoutHint: compound`, and `compoundChildren`.

Current compound groups:

- `Arundel Society chromolithograph copy series`: 9 member source records, 1864-1891.
- `Huntley & Palmers trade-card series`: 10 member source records, 1890.

Results after regeneration from existing CSV:

- Atomic captured rows remain: 77.
- Public surfaces generated: 60.
- Generated folders: 12.
- Missing folder/surface references: 0.
- Template distribution:
  - `sheet.main.v0`: 40
  - `sheet.img00.v0`: 10
  - `sheet.text.v0`: 8
  - `sheet.compound.v0`: 2

Validation:

- `python3 scripts/run_early_region_capture_1830_1930.py --from-csv` passed.
- `npm run build` in `/frontend` passed and generated 83 static pages.

---

## Global Stress Batch Public Surfaces Added

Purpose:

- Add a production-candidate global batch after the early-region 1830-1930 payload.
- Validate that the archive-box interface can carry non-Western, postwar, activist, institutional, authority, born-digital, protocol-sensitive, and link-only records.
- Keep the frontend on one combined static payload instead of splitting browse data across separate files.

Updated:

- Added `scripts/generate_global_stress_public_surfaces.py`.
- Generated `generated/global_stress_surfaces_v1.json`.
- Regenerated combined `generated/public_surfaces_v1.json`.
- Synced combined payload into frontend static data copies.
- Added `data/capture_batch_global_stress_surface_summary.csv`.

Inputs:

- Validated manual source records in `data/manual_source_records/`.
- Validated remediation source records in `data/remediation_source_records/`.
- Existing early-region CSV from `data/capture_batch_early_region_1830_1930_records.csv`.

Global stress coverage:

- Bauhaus / New Typography
- Polish Poster School
- IBM corporate design systems
- Taller de Grafica Popular
- Brigadas Ramona Parra
- Japanese postwar design institutions / World Design Conference context
- Shanghai Manhua / yuefenpai commercial print
- Singapore multilingual public graphics
- NID / development communication
- Iranian modern poster design
- Medu / Culture and Resistance
- NAIDOC / land-rights poster cultures
- Gran Fury / ACT UP
- Early web / CSS standards
- Korean Minjung / democratization graphics

Results:

- Global stress surfaces: 35.
- Combined public surfaces: 95.
- Combined folders: 63.
- Folder-type distribution:
  - region: 19
  - theme: 17
  - medium: 14
  - movement: 13
- Combined image-state distribution:
  - `IMG00`: 29
  - `IMG01`: 13
  - `IMG02`: 7
  - `IMG03`: 21
  - `IMG04`: 25
- Compound sheets now present:
  - Arundel Society chromolithograph copy series
  - Huntley & Palmers trade-card series
  - NAIDOC poster cultures, 2020-2022

Important implementation note:

- The generator deduplicates by `URL + title`, not by URL alone.
- This preserves one-source-page / many-object cases such as annual NAIDOC poster records.

Validation:

- `python3 scripts/generate_global_stress_public_surfaces.py` passed.
- `python3 -m py_compile scripts/generate_global_stress_public_surfaces.py scripts/run_early_region_capture_1830_1930.py` passed.
- Payload validation found 0 missing folder/surface references.
- `npm run build` in `/frontend` passed and generated 169 static pages.

Follow-up preview refresh:

- Rebuilt `/frontend` again after confirming the browser preview still showed the old `12 folders / 77 surfaces` state.
- Stopped the stale `localhost:3000` node process.
- Restarted `npm run dev -- -p 3000`.
- Confirmed `http://localhost:3000/folders` returns `200 OK`.
- The running preview should now read the combined `63 folders / 95 surfaces` payload.

---

## Frontend Interaction Refinement: Folder Scroll, Index Card, Search Rail

Issues addressed:

- Folder type pages could not browse all folders comfortably after the global payload expanded folder count.
- Hover-reveal folder cards needed edge-hover auto-scroll rather than a static stack.
- The `/contents` left index card was too long and collided visually with the wordmark.
- Search matching was too permissive because short subsequence fuzzy matches returned broad, noisy results.
- Opening search moved the archive counts card upward because both lived in the same right-side flex stack.

Updated:

- `frontend/src/components/archive/drawer/FolderDrawer.tsx`
- `frontend/src/components/archive/shell/ArchiveShell.tsx`
- `frontend/src/components/archive/shell/TocNav.tsx`
- `frontend/src/lib/archive-data.ts`
- `frontend/src/app/globals.css`

Changes:

- Added a scroll viewport around the folder stack.
- Added pointer-edge auto-scroll for long folder stacks.
- Kept folder hover reveal behavior intact.
- Reduced `/contents` left index card to the four public axes only: Region, Theme, Medium, Movement.
- Gave the main index table more horizontal room.
- Tightened local fuzzy search:
  - short one-character queries return no results;
  - short terms require substring/prefix matches;
  - subsequence matching is now only allowed for longer terms;
  - low-weight table matches are reduced;
  - visible result set is capped.
- Split the right rail into independent fixed regions:
  - counts card remains fixed at bottom-right;
  - search panel is independently positioned between the search icon and the counts card.
- Search panel position is computed from the actual search icon, panel height, and counts card position so the top/bottom gaps stay visually balanced.

Validation:

- `npm run build` in `/frontend` passed and generated 169 static pages.
- Restarted `localhost:3000` after the production build to avoid stale `.next` dev cache.
- Confirmed:
  - `http://localhost:3000/folders` returns `200 OK`
  - `http://localhost:3000/folders/region` returns `200 OK`

---

## Appendix Table Overlap Fix

Issue addressed:

- On the China / Hong Kong folder reader, appendix pages with long citation strings, URLs, and source-record file paths could overlap inside the two-column appendix layout.

Updated:

- `frontend/src/components/archive/layouts.tsx`
- `frontend/src/app/globals.css`

Changes:

- Appendix continuation pages now render specification tables in one column instead of two.
- Specification tables now use fixed table layout.
- Table cells now use `overflow-wrap: anywhere` so long citations, URLs, and file paths wrap inside the cell.
- Label/value column ratio was adjusted to give values more room.

Image-state clarification for China / Hong Kong records:

- `SURF-FIT022` / `上海漫畫 1928.05.19 第五期` is `IMG00`, not `IMG04`.
- `SURF-FIT025` / `Calendar poster Shanghai 上海日曆海報` is `IMG00`, not `IMG04`.
- Both are link-only / do-not-display image records in the current payload. The source pages may contain visual material, but the project has not captured display-safe image evidence, so the frontend renders an empty rights frame on the main sheet and routes users back to source.

Validation:

- `npm run build` in `/frontend` passed and generated 169 static pages.
- Restarted `localhost:3000`.
- Confirmed:
  - `http://localhost:3000/folders/region/china-hong-kong` returns `200 OK`
  - `http://localhost:3000/surfaces/SURF-FIT022?folder=FOL-REGION-CHINA-HONG-KONG` returns `200 OK`

---

## Frontend Rail and Folder Color Correction

Issues addressed:

- Folder category tabs lost their distinct type colors after the interface refinements.
- The search panel could expand downward into the archive counts card when many results were returned.
- The top folder in a long folder stack could feel clipped when hover expansion translated it upward.

Updated:

- `frontend/src/lib/archive-data.ts`
- `frontend/src/components/archive/shell/ArchiveShell.tsx`
- `frontend/src/components/archive/shell/search.tsx`
- `frontend/src/app/globals.css`

Changes:

- Restored four explicit folder inks:
  - Region: blue
  - Theme: black
  - Medium: red
  - Movement: yellow
- Search geometry now follows fixed archive-rail spacing:
  - search panel starts `2.5rem` below the search icon;
  - search panel is capped `2.5rem` above the counts card;
  - search results scroll inside the panel instead of pushing into the counts card.
- Increased folder-scroll viewport height and top padding so hover-open folder tabs retain visible clearance.

Validation:

- `npm run build` in `/frontend` passed and generated 169 static pages.
- Restarted `localhost:3000`.
- Browser inspection confirmed:
  - folder type colors resolve to `#2F5BEA`, `#33302b`, `#D94A38`, and `#E2C044`;
  - search-icon to search-panel gap is approximately `2.5rem`;
  - search-panel to counts-card gap is approximately `2.5rem`;
  - the top folder tab retains visible clearance after the hover translation.

Follow-up correction:

- The folder drawer no longer relies on inline `--folder-color` styles for tab/chip color.
- Each folder card now writes `data-folder-type="region|theme|medium|movement"`.
- CSS assigns the folder color from that type, so the drawer cannot silently fall back to all-black tabs if JS/hydration state is stale.
- Rebuilt and restarted `localhost:3000`; browser inspection confirmed:
  - Region chip/tab: `rgb(47, 91, 234)`
  - Theme chip/tab: `rgb(44, 41, 36)`
  - Medium chip/tab: `rgb(217, 74, 56)`
  - Movement chip/tab: `rgb(226, 192, 68)`

---

## Public Preview Scope Reset and Index Anchor Fix

Issue addressed:

- The frontend public preview incorrectly included the global stress batch alongside the 1830-1930 visual-verification crawl.
- This surfaced post-2000 records such as `Australia / Indigenous` / `NAIDOC poster cultures, 2020-2022`, which was not part of the current 1830-1930 preview scope.
- The `/contents` left index card linked out to folder pages instead of jumping to the relevant section of the index page.
- Main sheets leaned too heavily on specification tables, reducing reading value.

Updated:

- `frontend/src/data/public_surface_mock_v0.json`
- `frontend/public/data/public_surface_mock_v0.json`
- `generated/public_surfaces_v1.json`
- `frontend/src/components/archive/shell/TocNav.tsx`
- `frontend/src/app/contents/page.tsx`
- `frontend/src/components/archive/layouts.tsx`
- `frontend/src/app/globals.css`

Changes:

- Regenerated the current public preview from `data/capture_batch_early_region_1830_1930_records.csv` only.
- Current preview now contains:
  - 60 surfaces
  - 12 folders
  - date range 1830-1930
  - image states: `IMG03` 21, `IMG01` 13, `IMG04` 10, `IMG00` 10, `IMG02` 6
- Removed the global stress batch from the active frontend payload; it remains internal research/stress-test material, not the current public preview.
- Changed `/contents` left navigation:
  - Region -> `/contents#toc-region`
  - Theme -> `/contents#toc-theme`
  - Medium -> `/contents#toc-medium`
  - Movement -> `/contents#toc-movement`
- Added matching section IDs on the index page.
- Added captured source text/notes/subjects into the L01 main-sheet reading column before the six specification tables.

Validation:

- `npm run build` in `/frontend` passed and generated 83 static pages.
- Restarted `localhost:3000`.
- Confirmed:
  - `http://localhost:3000/folders/region/australia-indigenous` returns `404 Not Found`
  - `http://localhost:3000/contents` returns `200 OK`
  - Browser inspection confirms all four `/contents#toc-*` anchors exist and the left index card points to them.

---

## Period Strategy and Reading Gate

Issue addressed:

- The active preview scope must not be confused with complete historical coverage.
- The `1830-1930` payload is a visual-verification batch, not a finished pre-1930 archive.
- Later captures need stronger reading content and image evidence, otherwise the archive risks becoming a table-only checklist.
- Global stress batches should not sync into the frontend preview by default.

Updated:

- `CAPTURE_PERIOD_STRATEGY_v0.md`
- `ARCHIVE_PRODUCTION_RULEBOOK_v0.md`
- `scripts/generate_global_stress_public_surfaces.py`

Changes:

- Defined period segmentation:
  - `1830-1930`
  - `1931-1970`
  - `1971-2000`
  - `2001-2026`
- Period assignment uses the record end year when a date range exists.
- Added a reading gate:
  - 180+ characters of captured description/notes/context: main sheet eligible;
  - 80-179 characters plus strong image/source evidence: main sheet eligible but thin;
  - under 80 characters without context: card, compound child, fallback, or internal capture row;
  - textual/bibliographic sources can become `IMG04` text sheets.
- Clarified that `IMG04` is not a failed-image fallback. Visual-object records without display rights should remain `IMG00` with an empty image frame.
- Changed global stress generation:
  - writes internal global and combined stress payloads;
  - does not update frontend preview unless `--sync-frontend` is explicitly passed.

Validation:

- `python3 -m py_compile scripts/generate_global_stress_public_surfaces.py` passed.
- `python3 scripts/generate_global_stress_public_surfaces.py` now reports:
  - `generated/global_stress_surfaces_v1.json`: 35 global stress surfaces
  - `generated/combined_stress_public_surfaces_v1.json`: 95 combined surfaces
  - frontend preview not updated unless `--sync-frontend` is passed
- Confirmed active preview remains:
  - 60 surfaces
  - 12 folders
  - 1830-1930 date range

---

## Midcentury 1930-1970 Capture Batch

Issue addressed:

- Began the next period capture after the 1830-1930 visual-verification payload.
- This batch follows the period rule that records with date ranges are assigned by their end year.
- Records ending `<= 1930` are excluded to avoid overlap with the previous preview payload.
- Reading text is now part of publication quality control: thin records should not become table-only main sheets.

Added:

- `scripts/run_midcentury_capture_1930_1970.py`
- `data/capture_batch_midcentury_1930_1970_records.csv`
- `data/capture_batch_midcentury_1930_1970_source_summary.csv`
- `data/capture_batch_midcentury_1930_1970_raw/`

Capture directions:

- `MC01`: Art Institute of Chicago API
- `MC02`: V&A Collections API
- `MC03`: Library of Congress loc.gov API
- `MC04`: Cleveland Museum Open Access API
- `MC05`: The Met Open Access

Results:

- 95 captured rows
- 95 public surfaces
- 16 folders
- Date range: 1931-1970
- Source counts:
  - Library of Congress loc.gov API: 30
  - Art Institute of Chicago API: 25
  - V&A Collections API: 25
  - The Met Open Access: 15
- Image states:
  - `IMG00`: 25
  - `IMG01`: 24
  - `IMG02`: 8
  - `IMG03`: 0
  - `IMG04`: 38
- Surface types:
  - sheets: 71
  - cards: 24

Reading gate result:

- 24 captured rows have under 80 characters of description/notes/subjects.
- 0 thin records were promoted to main sheets.
- Thin records were downgraded to cards when image state and text evidence were insufficient.

Important limitation:

- This is not complete 1930-1970 coverage.
- The batch is still weighted toward AIC, V&A, LOC, and Met API-accessible records.
- Cleveland returned no publishable rows under the current query and relevance filters.
- `IMG03` did not appear in this batch; a follow-up source pass should include more explicit open-image sources and text-rich institutional/context sources.

Frontend:

- Regenerated active frontend payload to the 1930-1970 batch.
- `npm run build` in `/frontend` passed and generated 122 static pages.
- Restarted `localhost:3000`.
- Confirmed:
  - `http://localhost:3000/contents` returns `200 OK`
  - `http://localhost:3000/folders/theme/world-war-and-public-information-graphics` returns `200 OK`
  - `http://localhost:3000/surfaces/SURF-MC1930R021` returns `200 OK`
  - frontend payload reports 95 surfaces, 16 folders, 1931-1970 date range.

---

## Source Expansion Matrix v0

Issue addressed:

- The active preview proves the archive box/sheet system can render, but it is
  still source-poor and cannot be treated as historical coverage.
- Current records are heavily weighted toward API-friendly museum/library
  sources, especially AIC, V&A, Library of Congress, and The Met.
- The next expansion must increase the source universe before simply crawling
  more records from the same providers.

Added:

- `scripts/generate_source_expansion_matrix.py`
- `data/source_expansion_matrix.csv`
- `data/source_expansion_priority_1930_1970.csv`
- `SOURCE_EXPANSION_MATRIX_v0.md`

Results:

- 105 normalized source rows.
- 67 rows marked as useful for the 1931-1970 expansion period.
- 28 P1 rows for low-friction object/image or text-rich crawls.
- 29 P2 rows for regional balance, source probes, or semi-manual ingest.
- 29 rows still require targeted Deep Research before reliable production use.

Interpretation:

- A broad new Deep Research pass is not required before the next mechanical
  step.
- Targeted Deep Research is still needed for weak or rights-unclear areas:
  South Asia beyond NID, MENA/Iranian/Arabic/Persian/Hebrew sources, Africa
  beyond South Africa/Medu, Korea and Mainland China machine access, Latin
  America machine access, and Indigenous/Oceania protocol handling.

Next production direction:

- Use a mixed 1931-1970 expansion set rather than one museum-heavy API batch:
  one open/viewer image source, one periodical/newspaper/text source, one
  non-Western regional source, one authority/context source, and one existing
  API source only for targeted gap repair.

---

## Source / Image / Text Deep Research Integration

Reports reviewed:

- `Rights-Aware Source Expansion Plan for Modern Graphic Design History.docx`
- `Rights-Aware Image Strategy for a Modern Graphic Design Archive Index.docx`
- `Text Enrichment Methodology for a Rights-Aware Archive Index of Modern Graphic Design History.docx`

Outcome:

- The reports support moving forward with a source-expansion crawl rather than
  running another broad Deep Research pass.
- They confirm that the current preview is structurally valid but too
  museum/API-heavy and too table-like.
- The next crawl must prioritize OCR-rich periodicals/newspapers, poster-specific
  archives, institutional/company histories, community/protest archives, and
  authority/context sources.

Updated:

- `scripts/generate_source_expansion_matrix.py`
- `data/source_expansion_matrix.csv`
- `data/source_expansion_priority_1930_1970.csv`
- `SOURCE_EXPANSION_MATRIX_v0.md`
- `ARCHIVE_PRODUCTION_RULEBOOK_v0.md`
- `CAPTURE_PERIOD_STRATEGY_v0.md`

Added:

- `DEEP_RESEARCH_SOURCE_IMAGE_TEXT_REVIEW_v0.md`
- `IMAGE_AND_TEXT_ENRICHMENT_RULES_v0.md`
- `NEXT_1931_1970_EXPANSION_PLAN_v0.md`

Source matrix after integration:

- 127 source rows.
- 85 rows useful for 1931-1970.
- 35 P1 rows.
- 39 P2 rows.
- 36 rows still require targeted Deep Research before reliable production use.

Important rule change:

- Image state, parser status, and text eligibility are now treated as separate
  decisions.
- `IMG04` is only for genuinely text, authority, bibliography, appendix, or
  context-led pages.
- Parser failure must be logged separately and must not masquerade as `IMG04`.
- Editor-authored text can be added as grounded summary/context/classification,
  but self-made or generated substitute images should not replace missing
  archival images.

---

## Midcentury Expansion Capture 1931-1970

Script:

- `scripts/run_midcentury_expansion_capture_1931_1970.py`

Outputs:

- `data/capture_batch_midcentury_expansion_1931_1970_records.csv`
- `data/capture_batch_midcentury_expansion_1931_1970_source_summary.csv`
- `generated/public_surfaces_v1.json`
- `frontend/src/data/public_surface_mock_v0.json`
- `frontend/public/data/public_surface_mock_v0.json`

Result:

- 68 new rows captured.
- Cumulative frontend payload now contains 163 surfaces and 21 folders.
- New batch image states: 40 `IMG00`, 21 `IMG02`, 4 `IMG03`, 3 `IMG04`.
- Cumulative payload image states: 65 `IMG00`, 24 `IMG01`, 29 `IMG02`, 4 `IMG03`, 41 `IMG04`.
- New batch sources: Wellcome Collection Catalogue API 24, Internet Archive 30,
  Chinese Posters 11, Getty Research Portal 3.
- Europeana remains unavailable without an API key.
- NDL Search produced no publishable in-scope rows in this pass; keep it as a
  targeted parser/source-research task rather than silently treating it as empty
  coverage.

Implementation notes:

- Wellcome adapter now filters for IIIF presentation records and extracts
  thumbnails from IIIF manifests.
- Chinese Posters adapter now falls back to curated seed URLs if public search
  endpoints do not return usable results.
- The expansion script now writes an expansion CSV while generating a cumulative
  frontend payload by merging the prior 1931-1970 baseline capture.
- `npm run build` passed after payload sync, and localhost was restarted on
  port 3000.

---

## Repository Organization Pass

Repository layout was normalized before first GitHub push.

Kept operational paths stable:

- `frontend/`
- `data/`
- `generated/`
- `db/`
- `scripts/`
- `prompts/`

Moved root-level documentation into:

- `docs/methodology/`
- `docs/system/`
- `docs/frontend/`
- `docs/capture/`
- `docs/research-reviews/`
- `reports/deep-research/`

Added:

- `README.md`
- `.gitignore`
- `docs/README.md`
- `reports/README.md`

Intent:

- Keep runnable code/data paths intact.
- Stop root-level documentation sprawl.
- Exclude local build/cache/vendor files such as `frontend/node_modules/`,
  `frontend/.next/`, Python cache, and `.DS_Store`.

Initial repository push:

- Initialized local git repository on `main`.
- Added remote `git@github.com:dpan538/graphic_design_archive.git`.
- Pushed initial commit `4f1a10f` to GitHub.

---

## Surface Normalization and Physical Format Pass

Implemented after repository initialization.

Changes:

- Added `scripts/normalize_public_surfaces.py`.
- Grouped repeated source-generic records into compound sheets when the same
  source/title appears three or more times.
- Current normalization grouped 11 repeated Chinese Posters records into one
  `sheet.compound.v0` surface:
  `SURF-MX1970R055-GROUP`.
- China / Hong Kong register now shows the compound group instead of eleven
  repeated `Chineseposters.net` rows.
- Added explicit frontend physical surface classes:
  - normal sheet/register: A4 proportion
  - card: A5 proportion
  - fallback stub: A6 proportion
  - appendix: A4 height, two-thirds A4 width
- Added image coverage health metric to archive counts.

Rule:

- Image-ready coverage is counted as `IMG01 + IMG02 + IMG03`.
- `IMG00` is a valid rights-aware visual placeholder, but it does not count as
  healthy image coverage.
- Healthy design-archive target is 90% image-ready coverage.

Verification:

- `npm run build` passed after the normalization/format pass.
- Localhost was restarted on port 3000.

---

## Image-Ready Expansion Pass 1931-1970

Implemented after the repository entered the GitHub-backed project state.

Purpose:

- Increase healthy design-archive image coverage by converting the public
  surface set toward `IMG01` / `IMG02` / `IMG03`.
- Treat `IMG02` correctly as source-hosted / IIIF display evidence rather than
  as an empty rights frame.
- Preserve concurrent data work by rebuilding the public payload from all
  known CSV capture batches instead of overwriting from a single run.

Changes:

- Added `scripts/run_image_ready_expansion_1931_1970.py`.
- Added `scripts/rebuild_public_surfaces_from_records.py`.
- Updated the surface generator so `IMG02` records keep `image_url_detected`.
- Updated the frontend layout rule so `IMG02` with a URL can render as a
  source-hosted image, while still not implying local ownership or mirroring.
- Rebuilt the cumulative static payload into:
  - `generated/public_surfaces_v1.json`
  - `frontend/src/data/public_surface_mock_v0.json`
  - `frontend/public/data/public_surface_mock_v0.json`
  - `data/public_surface_mock_v0.json`

Capture result:

- New image-ready batch:
  - 78 rows
  - `IMG02`: 74
  - `IMG03`: 4
- Source contribution:
  - V&A Collections API: 13 `IMG02`
  - Wellcome Collection Catalogue API: 61 `IMG02`, 4 `IMG03`
- Library of Congress was rate-limited with HTTP 429 in this pass; this is
  retained as a capture-state fact and should be retried slowly later.

Cumulative public payload after rebuild:

- 291 surfaces
- 29 folders
- Image states:
  - `IMG00`: 65
  - `IMG01`: 37
  - `IMG02`: 109
  - `IMG03`: 29
  - `IMG04`: 51
- Image-ready coverage: 175 / 291 = 60%.

Pre-1931 audit after rebuild:

- 60 early public surfaces remain in the cumulative payload.
- Early image states:
  - `IMG00`: 10
  - `IMG01`: 13
  - `IMG02`: 6
  - `IMG03`: 21
  - `IMG04`: 10
- Early image-ready coverage: 40 / 60 = 67%.
- The remaining early `IMG00` cluster is mostly AIC records with detected image
  URLs but without captured open/public-domain evidence.
- The remaining early `IMG04` cluster is mostly LOC/V&A rows where the first
  automated capture did not expose usable image metadata.

Verification:

- `npm run build` passed after clearing a stale Next.js build cache and adding
  `about` to the `ArchiveShell` active-nav type.
- Static generation currently produces 332 pages, including `/about`, four
  folder-type routes, 29 folder detail routes, and 291 surface routes.

---

## Gallica / IIIF Protocol Capture Pass 1830-1970

Implemented as the first protocol-family expansion after the source review.

Reason:

- The project had many candidate sources in `source_expansion_matrix.csv`, but
  live adapters were still concentrated around a small group of large museum
  APIs and broad English keywords.
- Gallica / BnF was selected because it is a low-friction national-library
  source with SRU search, stable ARK identifiers, IIIF images, public-domain
  rights signals, and strong coverage of posters, printed ephemera, advertising,
  and visual-document records.

Changes:

- Added `scripts/run_gallica_image_ready_1830_1970.py`.
- Added the Gallica batch to
  `scripts/rebuild_public_surfaces_from_records.py`.
- The adapter uses Gallica SRU XML records as metadata evidence and constructs
  IIIF image/manifest URLs from ARK identifiers.
- Records with `public domain` / `domaine public` rights are assigned `IMG03`;
  records with IIIF image evidence but less explicit rights text are assigned
  `IMG02`.

Capture result:

- New Gallica batch:
  - 120 rows
  - `IMG03`: 113
  - `IMG02`: 7
- Query groups:
  - 1830-1930 affiche records: 40
  - 1931-1970 affiche records: 50
  - publicité records: 15
  - arts graphiques records: 15

Cumulative public payload after Gallica rebuild:

- 411 surfaces
- 29 folders
- Image states:
  - `IMG00`: 65
  - `IMG01`: 37
  - `IMG02`: 116
  - `IMG03`: 142
  - `IMG04`: 51
- Image-ready coverage: 295 / 411 = 72%.

Period audit after Gallica rebuild:

- Pre-1931:
  - 121 surfaces
  - Image-ready coverage: 101 / 121 = 83%.
- 1931-1970:
  - 290 surfaces
  - Image-ready coverage: 194 / 290 = 67%.

Verification:

- `npm run build` passed after the Gallica batch.
- Static generation currently produces 452 pages, including 411 surface routes.
- `http://localhost:3000/surfaces/SURF-GA1970R001` renders a Gallica `IMG03`
  sheet with one visible image.

---

## Public Launch Image Coverage Gate

Updated after project direction clarification.

Decision:

- For the first public launch, visual coverage is not an aspirational metric;
  it is a release gate.
- Minimum acceptable public-launch image-ready coverage: 95%.
- Project target: 100%.
- Image-ready means `IMG01 + IMG02 + IMG03`.
- `IMG00` and `IMG04` remain valid archival states, but they are blockers for
  public visual-surface launch unless they are demoted to non-primary support
  material, replaced by image-ready sources, or explicitly kept outside the
  public visual-surface denominator.

Added:

- `scripts/audit_image_release_gate.py`

Current gate result:

- Current cumulative public payload: 655 surfaces.
- Current image-ready coverage: 539 / 655 = 82.29%.
- Current blockers:
  - `IMG00`: 65
  - `IMG04`: 51
- If no blockers are removed or demoted, reaching 95% would require roughly
  1665 additional image-ready surfaces, which is structurally inefficient.

Implication:

- The launch path should prioritize converting, replacing, or demoting blockers
  rather than only adding more image-ready records.
- `IMG00` should be rare in the first public visual archive and reserved for
  historically essential records whose absence must be visible.
- `IMG04` should primarily be appendix/bookmark/context material, not a primary
  visual sheet.

---

## DigitalNZ and Wikimedia Commons Image-Ready Expansion

Added no-key image-ready source expansion batches after the 95% launch image
coverage gate was defined.

DigitalNZ:

- Script: `scripts/run_digitalnz_image_ready_1830_1970.py`
- Records: `data/capture_batch_digitalnz_image_ready_1830_1970_records.csv`
- Result:
  - 80 captured rows
  - `IMG03`: 80
- Source value:
  - expands beyond museum-object APIs into newspaper, advertising, periodical,
    and public visual culture records from Aotearoa New Zealand.

Wikimedia Commons:

- Script: `scripts/run_wikimedia_commons_image_ready_1830_1970.py`
- Records: `data/capture_batch_wikimedia_commons_image_ready_1830_1970_records.csv`
- Result after tightening search relevance:
  - 104 captured rows
  - `IMG03`: 104
- Search strategy:
  - Commons category-backed searches for 1930s, 1940s, 1950s, and 1960s posters,
    advertising posters, travel posters, and Bauhaus/modernist poster routes.
- Source policy:
  - Commons is treated as an open-license image supplement and discovery layer,
    not as a replacement for the original holding archive.
  - Source links, license labels, and original credit metadata remain required.

Secondary Gallica expansion:

- Script: `scripts/run_gallica_secondary_image_ready_1830_1970.py`
- Records: `data/capture_batch_gallica_secondary_image_ready_1830_1970_records.csv`
- Result:
  - 121 captured rows
  - `IMG03`: 113
  - `IMG02`: 8
- Search strategy:
  - SRU/IIIF routes for affiche publicitaire, réclame, typographie, imprimerie,
    and catalogue + affiche records.
- Source value:
  - provides image-ready records with stronger national-library provenance than
    broad web image aggregation and improves text/context availability for
    typography and printing history.

Normalizer update:

- `scripts/normalize_public_surfaces.py` now lets compound grouped sheets inherit
  a representative `IMG01`/`IMG02`/`IMG03` image from grouped source records
  instead of forcing grouped records back to `IMG00`.
- This prevents repeated source-generic titles from becoming visually empty
  after deduplication.

Cumulative payload after DigitalNZ + Commons + secondary Gallica:

- Raw rows included in rebuild: 743
- Public surfaces: 655
- Public folders: 30
- Image states:
  - `IMG00`: 65
  - `IMG01`: 37
  - `IMG02`: 124
  - `IMG03`: 378
  - `IMG04`: 51
- Image-ready coverage: 539 / 655 = 82.29%.

Build verification:

- `npm run build` passed.
- Static generation now produces 697 pages, including 655 surface routes.

Remaining implication:

- Adding image-ready records improves the archive, but it will not efficiently
  reach the 95% launch gate while all legacy `IMG00` and `IMG04` records remain
  counted as primary visual surfaces.
- Next remediation should combine source expansion with surface demotion:
  convert or replace high-value blockers where possible, and move unresolved
  `IMG00`/`IMG04` records into card, appendix, bibliography, or source-only
  support surfaces outside the primary visual coverage denominator.

---

## Appendix and Text-Leaf Pagination Correction

Issue confirmed:

- The payload itself did not contain excessive appendix surfaces:
  - 655 public surfaces
  - 605 sheets
  - 50 cards
- The problem was the frontend pagination rule:
  - every surface carried the six canonical tables;
  - the pagination engine treated every table overflow as a physical appendix;
  - estimated physical leaves before correction:
    - main leaves: 655
    - appendix leaves: 1992
  - this made the interface read like table overflow rather than archival
    reading material.

Correction:

- `frontend/src/lib/paginate.ts`
  - added a distinct `text` leaf type;
  - long image-bearing sheets now receive a `Text continuation` page when
    captured/normalized source text is substantial;
  - appendix leaves are no longer automatic table overflow;
  - appendix pages are reserved for exceptional evidence:
    - `IMG00` rights details;
    - unusually long relation/citation evidence;
    - large compound groups.
- `frontend/src/components/archive/blocks.tsx`
  - text pages now include:
    - captured source text;
    - subjects;
    - historical context note;
    - classification rationale;
    - uncertainty note;
    - citation basis.

Estimated physical-leaf result after correction:

- main leaves: 655
- text continuation leaves: 186
- appendix leaves: 36
- appendix/surface ratio: 0.055
- text/surface ratio: 0.284

Verification:

- `npm run build` passed after the pagination and text-page update.

Methodological implication:

- The complete six-table payload remains available for reproducibility.
- The public reading surface is now curated:
  - image sheets foreground visual evidence;
  - text leaves carry readable research/context material;
  - appendix leaves become rare source-evidence continuations rather than the
    default destination for all unused table rows.

---

## Source Dependency and Text Reference Ledger

Added a generated source-dependency layer so About-page claims and public text
rules are tied to current payload evidence.

Added:

- `scripts/generate_source_dependency_reference.py`
- `data/source_dependency_ledger.csv`
- `docs/system/SOURCE_DEPENDENCY_AND_TEXT_REFERENCES_v0.md`

Generated ledger basis:

- Input: `generated/public_surfaces_v1.json`
- Current public surfaces: 655
- Current source families: 12

The ledger records, per source:

- surface count;
- `IMG00`-`IMG04` distribution;
- dependency role;
- reference fields;
- rights dependency;
- text dependency;
- capture scripts.

About-page update:

- `frontend/src/app/about/page.tsx` now reflects current source counts:
  - Gallica / BnF APIs: 239
  - Wikimedia Commons: 104
  - Wellcome Collection Catalogue API: 89
  - Library of Congress loc.gov API: 50
  - V&A Collections API: 46
  - Art Institute of Chicago API: 45
  - Internet Archive / text and periodical collections: 30
  - DigitalNZ: 21
  - The Met Open Access: 15
  - Cleveland Museum Open Access API: 12
  - Getty Research Portal: 3
  - Chinese Posters: 1
- The About page now lists the generated ledger, source-dependency rulebook,
  text-enrichment rules, surface pipeline, and rights strategy as explicit
  references.
- It also states the text dependency rules:
  - source fields;
  - raw capture;
  - context/classification fields;
  - OCR/excerpt limits;
  - no substitute evidence from editor/AI wording.

Verification:

- `npm run build` passed after the About/source-dependency update.
- `scripts/audit_image_release_gate.py` still fails as intended because current
  image-ready coverage remains 82.29%, below the 95% launch gate.

---

## Local / University Image-Ready Source Expansion

Added two protocol-family source adapters to improve image coverage beyond the
large museum/API cluster:

- `scripts/run_princeton_figgy_image_ready_1830_1970.py`
- `scripts/run_gsu_contentdm_image_ready_1830_1970.py`

Captured batches:

- `data/capture_batch_princeton_figgy_image_ready_1830_1970_records.csv`
  - 41 records
  - 41 `IMG02`
  - source: Princeton University Library Digital Collections / Figgy
  - method: Blacklight JSON search + per-record IIIF manifest
- `data/capture_batch_gsu_contentdm_image_ready_1830_1970_records.csv`
  - 2 records
  - 2 `IMG02`
  - source: Georgia State University Library Digital Collections / CONTENTdm
  - method: CONTENTdm search API + singleitem API + item-level local rights

Why this matters:

- Princeton confirms a reusable university-library `catalog.json` + IIIF
  manifest pattern for posters, broadsides, advertising print, banners, and
  scanned visual resources.
- GSU confirms a reusable CONTENTdm pattern for local/university collections,
  including labor, civil-rights, newspaper, theatre, and urban print culture.
- Both sources are kept as `IMG02` unless item/manifest rights explicitly
  support an open-image claim. This improves image presence without weakening
  the rights model.

Pipeline updates:

- Added the two new records CSVs to
  `scripts/rebuild_public_surfaces_from_records.py`.
- Added source dependency metadata to
  `scripts/generate_source_dependency_reference.py`.
- Added source registry entries `SRC130` and `SRC131`.
- Regenerated:
  - `generated/public_surfaces_v1.json`
  - `frontend/src/data/public_surface_mock_v0.json`
  - `frontend/public/data/public_surface_mock_v0.json`
  - `data/public_surface_mock_v0.json`
  - `data/source_dependency_ledger.csv`
  - `docs/system/SOURCE_DEPENDENCY_AND_TEXT_REFERENCES_v0.md`

Current image gate after this expansion:

- public surfaces: 698
- image-ready: 582
- image-ready coverage: 83.38%
- image states:
  - `IMG00`: 65
  - `IMG01`: 37
  - `IMG02`: 167
  - `IMG03`: 378
  - `IMG04`: 51

Remaining blockers are still concentrated in legacy `IMG00`/`IMG04` records
from Art Institute of Chicago, Internet Archive, V&A, Met, LoC, Getty, and
Chinese Posters. The next productive image work should either upgrade these
blockers item-by-item or add larger local/government/university protocol
families with high image yield, especially CONTENTdm, IIIF manifests, Omeka S,
Kramerius, and national/regional newspaper repositories.

---

## Public Surface Integrity Correction

User review found that the visual archive was still too close to a flat table:

- several pages appeared to reuse the same image while browsing;
- `IMG` coverage was reported without checking placeholder images;
- most sheet records had no visible text-continuation leaf in the reader;
- the static payload did not explicitly expose bookmark, appendix, or
  registration-card structures.

Corrections made:

- Added `scripts/audit_public_surface_integrity.py` as a release-facing local
  audit. It checks exact repeated image URLs, placeholder image URLs, short
  text sheets, image state counts, source distribution, and structural
  collections.
- Updated `scripts/normalize_public_surfaces.py` to reject placeholder image
  URLs. Three Wellcome records using `https://wellcomecollection.org/placeholder.jpg`
  were demoted from renderable `IMG02`/`IMG03` to `IMG00`.
- Updated `scripts/rebuild_public_surfaces_from_records.py` to add explicit
  structural collections to the payload:
  - 30 folder bookmarks;
  - 35 appendix candidates, limited to real rights/image-evidence continuation
    cases rather than generic six-table overflow;
  - 30 registration cards / folder membership ledgers.
- Strengthened fallback enrichment text so no sheet currently falls below the
  60-word audit floor.
- Rebuilt all static public payload copies.

Verified results:

- public surfaces: 696
- sheets: 646
- cards: 50
- image-ready: 577 / 696
- image-ready coverage: 82.90%
- image states:
  - `IMG00`: 68
  - `IMG01`: 37
  - `IMG02`: 164
  - `IMG03`: 376
  - `IMG04`: 51
- exact repeated image URLs: 0
- placeholder image URLs: 0
- short text sheets under 60 words: 0
- structural payload collections:
  - bookmarks: 30
  - appendices: 35
  - registration cards: 30

Important interpretation:

- The earlier 83.38% image-ready number was too generous because it counted
  three placeholder images as displayable. The corrected image-ready rate is
  82.90%.
- A local Gallica sample check showed distinct IIIF URLs and distinct downloaded
  image hashes for the user-reported adjacent records, so the repeated-image
  symptom is likely a frontend image-state/cache reuse issue rather than an
  exact payload URL duplicate. Frontend mitigation resets image load/error state
  on URL change and keys the image element by URL.
- The launch target remains 95%+ image-ready coverage, so the archive still
  needs substantial source expansion and item-level upgrades before release.

---

## GSU CONTENTdm Raw Harvest and API Limit Check

User clarified that later-stage records should be retained when discovered,
because the archive will ultimately cover all time bands. This round therefore
keeps the capture logic moving toward stage-aware retention rather than
discarding non-current-period evidence by default.

Changes made:

- Added `scripts/harvest_gsu_contentdm_raw_records.py`.
- Converted already captured Georgia State University Library CONTENTdm raw
  records into a controlled official batch instead of leaving them as unused
  raw files.
- Applied per-collection caps so serial issue sources such as `The Machinist`,
  `Great Speckled Bird`, `Georgia Education Journal`, and `Signal` do not flood
  the archive as visually repetitive independent sheets.
- Fixed GSU date parsing so long ranges such as `1938-1951` or `1963-1965` are
  handled as complete ranges rather than incorrectly reading only the first
  in-period year.
- Added `scripts/run_loc_deep_image_ready_1931_1970.py` and
  `scripts/run_wikimedia_commons_deep_image_ready_1830_1970.py` as reproducible
  next-source capture attempts.
- Registered both deep-capture CSVs in
  `scripts/rebuild_public_surfaces_from_records.py` so future successful runs
  will flow into the static payload automatically.

Verified results:

- GSU official records increased from 2 to 33.
- All 33 GSU records are `IMG02` source-hosted image records.
- Public payload after rebuild:
  - public surfaces: 727
  - sheets: 677
  - cards: 50
  - image-ready: 608 / 727
  - image-ready coverage: 83.63% (rounded script output: 84%)
  - `IMG00`: 68
  - `IMG01`: 37
  - `IMG02`: 195
  - `IMG03`: 376
  - `IMG04`: 51
- Integrity audit:
  - exact repeated image URLs: 0
  - placeholder image URLs: 0
  - short text sheets under 60 words: 0
  - bookmarks: 30
  - appendices: 35
  - registration cards: 30

Source-limit findings:

- Library of Congress deep image pass was blocked by HTTP 429 rate limiting.
- Smithsonian Open Access image pass was blocked by HTTP 429 rate limiting.
- The first Commons deep pass produced no usable rows; the initial query shape
  was too broad/ambiguous and returned noise such as non-design images. A
  corrected category-based Commons script is retained, but this run still
  produced zero official rows.

Interpretation:

- This round improves the payload but does not solve the 95%+ image target.
- The most productive next capture family is likely not another broad LoC or
  Commons pass. It should prioritize protocol families with predictable image
  fields and less rate-limit friction: CONTENTdm collections, IIIF manifest
  endpoints, Omeka S archives, Kramerius/OAI-PMH repositories, and local
  university/government collections.
- The official archive must keep source dependency and rate-limit failures in
  About/Methodology so users understand why some regions or sources remain
  link-only or delayed.

---

## GSU Later-Stage Raw Harvest

User clarified that if a capture pass finds records from the next time bands,
they should be retained rather than discarded, because the archive is intended
to cover all stages through 2026.

Changes made:

- Added `scripts/harvest_gsu_contentdm_raw_records_1971_2026.py`.
- Reused the GSU CONTENTdm raw harvest logic but wrote a separate official
  output batch:
  - `data/capture_batch_gsu_contentdm_image_ready_1971_2026_records.csv`
  - `data/capture_batch_gsu_contentdm_image_ready_1971_2026_source_summary.csv`
- Added the new batch to `scripts/rebuild_public_surfaces_from_records.py`.
- Updated surface display numbering to prefer `date_end` over `date_start`
  when generating the provisional display era, so long-range records such as
  `1965-1990` are filed by their terminal year rather than visually treated as
  1960s-only records.
- Updated cumulative rebuild sorting to use terminal year first.

Verified results:

- New GSU late-stage records: 52
  - 46 records ending in 1971-2000
  - 6 records ending in 2001-2026
  - all 52 are `IMG02`
- Cumulative public payload:
  - public surfaces: 779
  - sheets: 729
  - cards: 50
  - image-ready: 660 / 779
  - image-ready coverage: 84.72% (rounded script output: 85%)
  - `IMG00`: 68
  - `IMG01`: 37
  - `IMG02`: 247
  - `IMG03`: 376
  - `IMG04`: 51
- GSU total public surfaces: 85
- Integrity audit:
  - exact repeated image URLs: 0
  - placeholder image URLs: 0
  - short text sheets under 60 words: 0
- Frontend build passed:
  - static pages generated: 828

Interpretation:

- This pass improves image coverage and proves that the stage-aware retention
  rule works.
- It is still not enough for launch: the project remains roughly ten percentage
  points below the 95% image-ready target.
- The next substantial jump still requires additional high-yield image sources,
  ideally CONTENTdm/IIIF/Omeka/Kramerius/local-government collections rather
  than broad APIs currently subject to rate limits.
