# Project Log

This log records project decisions, implementation steps, and collaboration boundaries. It should be updated after every meaningful change so that future work, including database implementation and frontend handoff, remains traceable.

## 2026-06-10

### Region Cleanup Application Layer and Non-mainstream Capture Guardrails

Scope:

- Completed the first confirmed cleanup layer before wider capture work.
- The layer targets region/geography misfiling caused by generated surface
  folder assignment, not by rewriting source evidence.
- `research-repo/` remains read-only and was not edited, staged, or committed.

Implementation:

- Updated `scripts/run_midcentury_capture_1930_1970.py` so `region_for()` gives
  explicit `source_place_text` country evidence priority before broader title,
  subject, source-name, or source-note keyword fallback.
- Verified the 64 `ready_for_batch_apply_after_sample_audit` geography cleanup
  rows against the underlying capture records: 64 matched rows, 0 failures.
- Rebuilt public surfaces after the rule change.
- Added zero-result preservation guards to:
  - `scripts/run_nonmainstream_item_image_capture_2026_v1.py`
  - `scripts/run_nonmainstream_region_content_capture_1990_2026.py`

Guardrail result:

- The item/image capture rerun checked 2,284 pre-surface leads and returned 0
  new image-bearing records in the current network/source state. Because an
  existing non-empty canonical records CSV was present, the script preserved the
  587 existing data rows and wrote only diagnostic zero-result files under
  `data/capture_runs/`.
- The region-content capture rerun checked 10 target sources and returned 0 new
  records. Because an existing non-empty canonical records CSV was present, the
  script preserved the 21 existing data rows and wrote only diagnostic
  zero-result files under `data/capture_runs/`.
- This prevents transient endpoint failures, source-side blocking, or selector
  drift from replacing validated capture output with empty CSVs.

Large-range capture state:

- The non-mainstream v3 source profile capture remains the current productive
  large-range lane: 127 converted OK sources from 228 candidates.
- Source-profile macro-region distribution:
  - Latin America / Caribbean: 34
  - Africa: 29
  - Eastern Europe / Caucasus: 18
  - MENA: 14
  - South Asia: 12
  - Southeast Asia: 9
  - Central Asia: 5
  - Oceania / Indigenous: 5
  - East Asia: 1
- Source-profile protocol family distribution:
  - HTML: 82
  - HTML/catalog: 27
  - catalog/HTML: 14
  - HTML/database: 2
  - HTML/data: 1
  - OAI/HTML: 1
- Source-profile impact-rating distribution:
  - A: 51
  - B: 73
  - C: 3

Rebuild output:

- Public surfaces: 7,836.
- Source rows scanned by rebuild: 7,956.
- Public folders: 55.
- Image states: IMG00 43, IMG01 37, IMG02 1,327, IMG03 6,171, IMG04 258.
- Source-visible image-ready surfaces: 7,535 / 7,836 (96.16%).
- Weighted publication image score: 6,294.85 / 7,836 (80.33%).

Detection output:

- Release snapshot:
  - Active public sources: 6,499.
  - Object source-visible rate: 96.34%.
  - Object verified-open rate: 78.96%.
  - Object IMG04 rate: 3.11%.
- Source coverage v2:
  - Source pool period fill rate: 100.00%.
  - Strict distribution-adjusted source coverage rate: 28.96%.
  - Period surface balance rate: 81.92%.
  - Period quality main balance rate: 38.88%.
  - Region surface balance rate: 9.39%.
  - Region quality main balance rate: 7.20%.
  - Research quality-adjusted source coverage rate v2: 2.69%.
- Non-mainstream low-coverage probe health:
  - New candidates: 228.
  - Baseline plus new: 309.
  - OK sources: 127.
  - Probe health: 55.70%.
  - Success target met: true.
- Non-mainstream region capture health:
  - Target source coverage: 50.00%.
  - Record health: 100.00%.
  - IMG rate: 71.43%.
  - Impact ratings: A 15, B 6.
- Public sheet counts:
  - Main sheets: 7,582.
  - Sub sheets: 240.
  - Text sheets: 242.
  - Main sheets with more than 2 sub sheets: 359.
  - Main sheets with more than 5 text sheets: 5.
- Surface assignment gates:
  - Main-sheet candidates: 7,152.
  - Subsheet visual: 472.
  - Text-sheet candidates: 198.
  - Group/review records: 105.

Release-gate interpretation:

- Source-visible is above the 95% object-level gate.
- Object verified-open remains below the 85% gate.
- Weighted publication image coverage remains below the future 95% object-level
  gate.
- IMG04 is low at 3.11% object-level, but blocking sources still need cleanup
  because IMG04 is now part of release evaluation.
- `audit_public_surface_integrity.py` still reports 6 exact repeated image URL
  groups across 12 surfaces, so duplicate visual route review remains open.
- The archive is still main-sheet heavy; future classification work should
  improve main/sub/text packet structure instead of only adding records.

Boundary:

- No image binaries, screenshots, thumbnails, or third-party raw payloads were
  downloaded in this pass.
- No `IMG01` or `IMG03` rights upgrades were made.
- Impact/source priority remains internal triage only.

Next capture direction:

- Continue large-range capture through lanes that can produce actual
  source-visible records rather than only source profiles.
- Prioritize low-coverage regions that can plausibly improve strict
  distribution coverage: Africa beyond South Africa/Nigeria, MENA beyond
  Palestine/UAE, Southeast Asia beyond Singapore/Malaysia/Indonesia, South Asia
  beyond India/Pakistan/Bangladesh, Central Asia/Caucasus, and Pacific/Oceania
  beyond Australia/Aotearoa.
- Before another long run, add preflight health probes to item/image capture
  targets and require a nonzero sample before replacing canonical outputs.

### Region and Geography Normalization Decision Table Added

Reviewed:

- `Region and Geography Normalization for modern_GD_history.docx`

Conclusion:

- The report is useful as a geography-normalization method and release-gate
  cleanup guide, but it should not be applied directly because it did not
  inspect the project CSVs when written.
- Its strongest contribution is the separation between mapping gaps,
  structural slash-label splits, sensitive historical/place contexts, and true
  source gaps.
- The live audit confirms that several suggestions already exist in controlled
  geography rows, including Palestine historical/modern contexts, Indigenous
  Australian contexts, Central Asia, Caucasus, and southern African solidarity
  routes.

Created:

- `scripts/generate_region_geography_normalization_decisions_v1.py`
- `data/region_geography_normalization_decisions_v1.csv`
- `docs/capture/REGION_GEOGRAPHY_NORMALIZATION_DECISIONS_v1.md`

Decision output:

- 29 region/geography decision rows were generated.
- 9 rows are high-confidence country mappings or country mappings with
  historical/specificity review.
- 10 rows require structural or sensitive split handling.
- 1 row marks `Unresolved region` as an internal QA state rather than a public
  geography.
- 4 rows remain likely true source gaps after mapping cleanup: Southeast Asia,
  Middle East and North Africa beyond Palestine, Africa beyond Southern Africa,
  and Oceania/Pacific beyond Australia.

Implementation boundary:

- This pass is read-only. It does not rewrite records, surfaces, source files,
  `regions.csv`, or `geographies.csv`.
- The next safe step is a proposal-only normalization-candidate script that can
  auto-map obvious country labels, queue slash-label splits, and keep sensitive
  historical labels in review before any archive rebuild.

### Region and Geography Candidate Queue Added

Created:

- `scripts/generate_region_geography_normalization_candidates_v1.py`
- `data/region_geography_normalization_candidates_v1.csv`
- `data/region_geography_normalization_candidate_summary_v1.csv`
- `docs/capture/REGION_GEOGRAPHY_NORMALIZATION_CANDIDATES_v1.md`

Candidate output:

- 7,836 public surfaces were scanned.
- 7,810 proposal-only candidate rows were generated.
- 1,685 rows are existing high-confidence country mapping candidates.
- 945 rows are taxonomy mapping candidates, led by the `Latin America`
  display/rollup issue and the missing controlled `Uruguay` geography.
- 586 `Unresolved region` rows have a single high-signal auto-map candidate
  from `placeText` or `sourceSubjects`.
- 40 `Unresolved region` rows need sensitive, multiple, or historical/context
  review from high-signal evidence.
- 163 `Unresolved region` rows have only low-signal geography hints from
  title, source description, source notes, or source name and must not be
  auto-applied.
- 3,900 `Unresolved region` rows remain pending because the inspected fields do
  not yet provide enough geography evidence.
- 344 existing public region labels conflict with high-signal geography
  evidence and need review before automated application. The largest conflict
  group is currently `United States`, often where source evidence points to
  Mexico or other specific places.

Quality guardrail:

- The candidate script was tightened so `sourceDescription`, `sourceNotes`,
  `title`, and `sourceName` can support review, but do not trigger automatic
  geography assignment by themselves. This prevents false auto-mapping from
  incidental references such as collection locations, depicted artworks, or file
  names.
- The candidate script also detects existing region-label conflicts so current
  public folder labels do not automatically override stronger record-level
  geography evidence.
- The candidate script also routes explicit composite place text such as
  `Europe and USA` into multi-geography review instead of collapsing the record
  to one country.

Implementation boundary:

- This pass is still read-only. It does not rewrite public surface JSON,
  source records, `regions.csv`, or `geographies.csv`.
- The safest application path is to sample the 586 high-signal unresolved
  auto-map candidates first, then create a separate apply script with a dry-run
  default.

### Region and Geography Auto Candidate QA Sample Added

Created:

- `scripts/sample_region_geography_auto_candidates_v1.py`
- `data/region_geography_normalization_auto_review_sample_v1.csv`
- `docs/capture/REGION_GEOGRAPHY_NORMALIZATION_AUTO_REVIEW_SAMPLE_v1.md`

Sample output:

- 7,810 candidate rows were read.
- 205 QA rows were generated.
- 125 rows are stratified samples from the 586 high-signal unresolved auto-map
  candidates.
- 40 rows sample low-signal geography hints.
- 40 rows sample sensitive, historical, or multi-geography review queues.

Review rule:

- Only `auto_map_from_unresolved` rows can become a dry-run application batch.
- Low-signal, sensitive, historical, multi-geography, and existing-region
  conflict rows must remain review-only until the evidence is checked.

### Region and Geography Local Enrichment Audit Added

Context:

- The 3,900 remaining `Unresolved region` rows are not an acceptable final
  state, but they also should not be force-bound to geographies from weak text
  evidence.
- The user supplied a reference workflow for direct conflict parsing, historical
  split suggestions, NER-style text resurfacing, and audit aggregation.
- The workflow was adapted to the project schema without adding external
  dependencies. The project uses `data/geographies.csv` as the controlled
  geography table and `evidence_snippet`/surface metadata fields as the audit
  source.

Created:

- `scripts/parse_region_conflict_evidence_v1.py`
- `scripts/suggest_region_conflict_historical_splits_v1.py`
- `scripts/resurface_region_geo_text_suggestions_v1.py`
- `scripts/audit_region_geo_enrichment_suggestions_v1.py`
- `data/region_conflict_direct_parse_v1.csv`
- `data/region_conflict_historical_split_suggestions_v1.csv`
- `data/region_pending_geo_text_suggestions_v1.csv`
- `data/region_geo_enrichment_audit_summary_v1.csv`
- `docs/capture/REGION_GEO_ENRICHMENT_AUDIT_v1.md`

Enrichment output:

- 342 existing region-label conflicts received direct high-signal controlled
  geography suggestions.
- 228 historical split suggestions were generated for conflict rows, mostly
  Mexico / United States military occupation context around Matamoros and 1846.
- 803 pending or low-signal rows received rule-based geography resurfacing
  suggestions.
- 1,147 unique surfaces now have at least one local enrichment suggestion.

Interpretation:

- Direct conflict parse suggestions are the strongest local enrichment output
  and can feed a review-first correction batch.
- Historical split suggestions remain review-only until controlled historical
  geography rows and public display rules are confirmed.
- Pending text suggestions are useful for prioritizing review and source-family
  repair, not for automatic application. Some low-signal cases may represent
  colonial, depicted, publisher, or collection geography rather than object
  geography.
- A Wikidata or external lookup pass can be added later with caching,
  rate-limits, and a dry-run-only output contract, but it was not run in this
  local pass.

### Civic Ephemera Index Color and Design System Landed

Decision:

- Reframe the frontend visual system as a civic ephemera index: a bright
  research-library interface shaped by public-information print rather than a
  dark archive room or decorative retro skin.
- Treat the palette as an operational system with three separate roles:
  reading base, four classification axes, and supporting printed-ephemera stock
  colors.
- Replace the former pure/near-black ink behavior with a single Brown Black so
  text, rules, icon work, shadows, and ticket-like marks share one material
  source.

Design research basis:

- Japanese railway and commemorative passenger tickets informed route bands,
  numbered gates, serial fields, pale ticket stock, red overprints, and blue
  transit panels.
- JR station stamp references informed small public-system compositions with
  local pictorial icons, place labels, spot-color constraints, and rough printed
  texture.
- Long Island Rail Road World's Fair coupons informed detachable coupon logic,
  validation stamps, dense rules, and the idea that administrative proof can be
  as visible as destination.
- Yankee Stadium, aviation, postal, safety-stamp, KTG instructional booklet,
  Crossreference, Trawelt, ITYA, and cyberspace-style references informed the
  mix of oversized numbers, fare/date fields, punched tabs, command labels,
  card stacks, ticket edges, and high-contrast ephemera colors.

Implementation:

- Added the final palette to global CSS and Tailwind tokens:
  - base: Canvas, Paper, Surface, Line, Brown Black;
  - index axes: Region, Theme, Movement, Medium;
  - ephemera stock: ticket cream, newsprint grey, cardboard tan, ochre stock,
    signal yellow, process orange, grass stock, olive card, harbor teal, grid
    mint, station sky, railway blue, transit indigo, register pink, ledger mauve,
    and copper ink.
- Updated folder ink assignments so Theme uses Stamp Green, Movement uses
  Diagram Violet, Medium uses Permit Red, and Region keeps railway blue.
- Added readable index variants for small text and kept raw index colors for
  navigation, labels, bars, and block accents.
- Rewrote the About design-research section so it names the design position,
  cites the visual source families, explains why color roles are separated, and
  renders the palette directly on the page.
- Updated handoff and asset documentation so future frontend work inherits the
  civic ephemera index system instead of the older placeholder palette.

Verification:

- `npm run build` completed successfully after clearing the corrupted `.next`
  output left by an earlier disk-space failure.
- Old color tokens and old exact hex values were scanned and removed from the
  targeted frontend/design-system files.
- Contrast checks confirmed Brown Black on the reading base and readable index
  variants meet normal-text AA thresholds.

## 2026-06-01

### Text Page Preview Failure Logged and Capture Constraint Added

During text page asset design, the review process failed because screenshot
generation was not stabilized before layout iteration continued. Temporary file
paths, static HTML extraction, Quick Look rendering, and ad hoc browser capture
were mixed together, producing stale or incomplete screenshots and preventing a
trustworthy design review.

Corrective action:

- added `frontend/scripts/capture-text-pages.js`;
- added `npm run preview:text-pages` for an isolated `127.0.0.1:3037` preview;
- added `npm run capture:text-pages` for manifest-based group screenshots;
- added `docs/frontend/ASSET_PREVIEW_CAPTURE_CONSTRAINTS.md`;
- added `docs/frontend/TEXT_PAGE_PREVIEW_FAILURE_REPORT_2026_06_01.md`.

New project constraint:

- future asset work may not be presented as visually complete unless a fresh
  canonical capture has been generated after the latest change and the manifest
  passes overflow, ratio, image, group, and selector checks.

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
  - folder type colors resolve to the then-current legacy blue, black, red, and yellow folder inks;
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

---

## Cooper Hewitt GraphQL Image-Ready Capture

User asked to continue the next source expansion round, with special attention
to image coverage, duplicate images, and source honesty.

Changes made:

- Added `scripts/run_cooperhewitt_graphql_image_ready_1830_2026.py`.
- Added `data/capture_batch_cooperhewitt_graphql_image_ready_1830_2026_records.csv`.
- Added `data/capture_batch_cooperhewitt_graphql_image_ready_1830_2026_source_summary.csv`.
- Added the Cooper Hewitt batch to `scripts/rebuild_public_surfaces_from_records.py`.
- The first probe showed that a naive `graphic design` query captured too many
  non-graphic "Design for..." decorative/object sketches. The script was
  tightened before publication:
  - kept poster, packaging, label, brochure, advertising, and typography routes;
  - removed over-broad book-cover/illustration routes;
  - stopped using department name alone as relevance evidence;
  - removed overly broad relevance triggers such as generic `lithograph`,
    `print`, and `cover`;
  - split Cooper Hewitt GraphQL requests by time ranges because the API returned
    empty results for one very broad `1830-2026` poster query.

Verified results:

- Cooper Hewitt official records: 148
- Cooper Hewitt public surfaces after normalization: 137
- All Cooper Hewitt records are `IMG02` source-hosted image candidates.
- Cooper Hewitt duplicate image URLs: 0
- Cumulative public payload after rebuild:
  - public surfaces: 916
  - sheets: 866
  - cards: 50
  - image-ready: 797 / 916
  - image-ready coverage: 87%
  - `IMG00`: 68
  - `IMG01`: 37
  - `IMG02`: 384
  - `IMG03`: 376
  - `IMG04`: 51
- Integrity audit:
  - exact repeated image URLs: 0
  - placeholder image URLs: 0
  - short text sheets under 60 words: 0
  - bookmarks: 30
  - appendices: 35
  - registration cards: 30
- Frontend build passed:
  - static pages generated: 966

Interpretation:

- This is a real improvement but still not launch-ready for the user's 95%+
  visual-design threshold.
- The project is now around 87% image-ready by the current static payload
  metric. The remaining gap is mostly structural: `IMG00`, `IMG04`, and
  thumbnail-only `IMG01` rows still need conversion or better source selection.
- Cooper Hewitt is useful as a design-specific image source, but it must be
  queried narrowly; broad design terms can produce decorative/object design
  false positives.
- The next capture round should prioritize additional design-specific or
  protocol-stable sources with visible images and item-level rights evidence,
  rather than broad keyword search alone.

---

## Noncanonical Movement Visibility Pass

User emphasized that the project's core value is not simply filling a Western
museum/archive index, but making non-mainstream, non-Western, counterpublic,
and regional graphic formations visible.

Changes made:

- Added `scripts/run_noncanonical_movement_commons_capture_1930_2000.py`.
- Added `data/capture_batch_noncanonical_movement_commons_1930_2000_records.csv`.
- Added `data/capture_batch_noncanonical_movement_commons_1930_2000_source_summary.csv`.
- Added the new batch to `scripts/rebuild_public_surfaces_from_records.py`.
- Updated `scripts/run_midcentury_capture_1930_1970.py` so public surfaces can
  receive conservative movement/formation folders.
- Added regional movement authority rows:
  - `RM090` OSPAAAL and Tricontinental solidarity graphics.
  - `RM091` Palestinian liberation and solidarity poster culture.

Capture policy:

- This pass is intentionally small and conservative.
- Wikimedia Commons is treated only as a rights-aware image/display layer, not
  as the final historical authority.
- A record must have explicit movement/formation term evidence, a date in
  `1930-2000`, an open-license image, and a real source URL.
- False-positive filters reject later photographs, PDFs/DJVUs/SVGs, and broad
  query drift.

Verified results:

- New records captured: 7
- New image states: 7 `IMG03`
- New/activated movement folders after rebuild:
  - Bauhaus / New Typography first-ingest network
  - Brigadas Ramona Parra first-ingest scope
  - Gran Fury and ACT UP activist graphics
  - Japanese postwar design institution network
  - Medu Art Ensemble and anti-apartheid poster movement
  - OSPAAAL and Tricontinental solidarity graphics
  - Palestinian liberation and solidarity poster culture
  - Taller de Grafica Popular first-ingest scope
- Surfaces with movement IDs after rebuild: 30
- Cumulative public payload after rebuild:
  - public surfaces: 923
  - sheets: 873
  - cards: 50
  - image-ready: 804 / 923
  - image-ready coverage: 87%
  - `IMG00`: 68
  - `IMG01`: 37
  - `IMG02`: 384
  - `IMG03`: 383
  - `IMG04`: 51
- Integrity audit:
  - exact repeated image URLs: 0
  - placeholder image URLs: 0
  - short text sheets under 60 words: 0

Interpretation:

- This pass does not solve the global-balance gap by quantity, but it changes
  the structure: movement folders now exist in the generated public interface.
- The project still needs primary or community archive sources for these
  formations. Commons images are a temporary visibility layer, not the final
  archival base.
- The next careful expansion should target primary/noncanonical sources such
  as Palestinian Museum Digital Archive, African Activist Archive, SAHA/SAHO,
  Memoria Chilena/M68, NDL/Japan, and South Asia Open Archives with source-link
  and rights review first.

---

## Noncanonical Exact-Source Capture Pass

User clarified that the largest gap is the project's core value: histories and
visual systems outside mainstream Western museum canons need to be visible, but
capturing them must remain careful and source-bound.

Changes made:

- Added `scripts/run_noncanonical_exact_source_capture_1970_2000.py`.
- Added `data/capture_batch_noncanonical_exact_sources_1970_2000_records.csv`.
- Added `data/capture_batch_noncanonical_exact_sources_1970_2000_source_summary.csv`.
- Added raw exact-source page captures under
  `data/capture_batch_noncanonical_exact_sources_1970_2000_raw/`.
- Added the new batch to `scripts/rebuild_public_surfaces_from_records.py`.
- Updated `scripts/generate_source_dependency_reference.py` with source
  dependency metadata for:
  - South African History Archive
  - Biblioteca Nacional Digital de Chile / Memoria Chilena
  - NAIDOC / AIATSIS
  - Roots.sg / National Heritage Board Singapore

Capture policy:

- This pass uses preselected exact source pages rather than broad keyword
  search.
- Source-hosted images are admitted only as `IMG02`, with no local copy and no
  open-reuse claim.
- Error pages are rejected rather than stored as fallback records.
- Theme/navigation images are filtered out so menu icons are not mistaken for
  archive images.
- Text/context records are retained as `IMG04` only when the source page is an
  important collection or authority route.

Verified results:

- New exact-source records captured: 10
- New image states:
  - `IMG02`: 8
  - `IMG04`: 2
- Failed/rejected targets:
  - Wits Historical Papers Medu portal: DNS resolution failed during capture.
  - Korea Democracy Foundation exact URLs: returned 404/error pages.
- New source families represented:
  - South African History Archive: 3 Medu/anti-apartheid records
  - Biblioteca Nacional Digital de Chile / Memoria Chilena: 3 Brigadas Ramona
    Parra records
  - Roots.sg / National Heritage Board Singapore: 2 Singapore signage records
  - NAIDOC / AIATSIS: 2 Indigenous poster-history collection/context records
- Cumulative public payload after rebuild:
  - public surfaces: 933
  - sheets: 883
  - cards: 50
  - image-ready: 812 / 933
  - image-ready coverage: 87%
  - `IMG00`: 68
  - `IMG01`: 37
  - `IMG02`: 392
  - `IMG03`: 383
  - `IMG04`: 53
- Period image coverage after rebuild:
  - `<1930`: 282 / 302 image-ready, 93.4%
  - `1930-1970`: 388 / 487 image-ready, 79.7%
  - `1971-2000`: 136 / 136 image-ready, 100.0%
  - `2001-2026`: 6 / 8 image-ready, 75.0%
- Integrity audit:
  - exact repeated image URLs: 0
  - placeholder image URLs: 0
  - short text sheets under 60 words: 0
- Frontend build passed:
  - static pages generated: 999

Interpretation:

- This pass increases noncanonical visibility in the generated archive without
  treating secondary web images as project-owned assets.
- The exact-source approach is slower than API capture but much safer for
  counterpublic/community archives because it preserves source return, rights
  caution, and local context.
- NAIDOC/AIATSIS currently need item-level poster extraction before they can
  contribute healthy visual coverage; collection-level pages remain useful as
  authority/context records.
- KDF and Wits should stay in the source queue, but they need either revised
  endpoints, browser-assisted verification, or a different access path before
  ingest.

## 2026-05-31 — Gap Noncanonical Image/Text Capture

Purpose:

- Start filling the project’s real gap: non-mainstream, regional, Indigenous,
  and counterpublic graphic design records with usable source-hosted images and
  enough text to support future reading pages.
- Avoid another broad keyword bulk pass. This round admits only records that
  pass stricter image and text checks.

Changes made:

- Added `scripts/run_gap_noncanonical_image_text_capture_1930_2000.py`.
- Added `data/capture_batch_gap_noncanonical_image_text_1930_2000_records.csv`.
- Added `data/capture_batch_gap_noncanonical_image_text_1930_2000_source_summary.csv`.
- Added raw source excerpts under
  `data/capture_batch_gap_noncanonical_image_text_1930_2000_raw/`.
- Added the batch to `scripts/rebuild_public_surfaces_from_records.py`.
- Updated `scripts/generate_source_dependency_reference.py` and regenerated:
  - `data/source_dependency_ledger.csv`
  - `docs/system/SOURCE_DEPENDENCY_AND_TEXT_REFERENCES_v0.md`

Capture policy:

- Te Papa object records are accepted only when the page exposes a real
  `media.tepapa.govt.nz/collection/.../preview` image and a source description
  of at least 80 characters.
- NAIDOC item pages use official poster-gallery pages and extract poster title,
  artist, source-hosted image URL, and image alt text/body metadata.
- All new images are `IMG02`: source-hosted display only, no local image copy,
  no open-reuse claim.
- Duplicate titles and repeated image URLs are rejected within this batch.

Verified results:

- New records captured: 58
  - Te Papa Collections Online: 32
  - NAIDOC Poster Gallery: 26
- New image states:
  - `IMG02`: 58
- Batch quality checks:
  - repeated image URLs: 0
  - repeated titles: 0
  - Te Papa decoration/placeholder images: 0
  - descriptions under 80 characters: 0
- Cumulative public payload after rebuild:
  - public surfaces: 991
  - sheets: 941
  - cards: 50
  - image-ready: 870 / 991
  - image-ready coverage: 88%
  - `IMG00`: 68
  - `IMG01`: 37
  - `IMG02`: 450
  - `IMG03`: 383
  - `IMG04`: 53
- Period image coverage after rebuild:
  - `<1930`: 282 / 302 image-ready, 93.4%
  - `1930-1970`: 404 / 503 image-ready, 80.3%
  - `1971-2000`: 178 / 178 image-ready, 100.0%
  - `2001-2026`: 6 / 8 image-ready, 75.0%
- Integrity audit:
  - exact repeated image URLs: 0
  - placeholder image URLs: 0
  - short text sheets under 60 words: 0
- Frontend build passed:
  - static pages generated: 1057

Interpretation:

- The overall image-ready percentage improved modestly because the archive is
  now large, but the new batch is high quality and specifically targets the
  noncanonical gap.
- The next data-side priority is not simply more records. It is reducing the
  remaining `1930-1970` `IMG00/IMG04` pool through source-specific remediation
  and adding more non-Western movement archives with real item pages.

## 2026-06-01 — Appendix Dispatch and Region Grouping Adjustment

Purpose:

- Prevent appendix pages from becoming repeated placeholder inserts, especially
  consecutive `AX01` pages for same-source `IMG00` records.
- Make the six appendix layouts participate in the production reader without
  turning every sheet into a table-overflow appendix.
- Add a macro-region reading layer to the region folder entrance so users are
  not forced to parse a flat list of small geopolitical folders.

Changes made:

- Updated `frontend/src/lib/paginate.ts`:
  - each surface may still receive one appendix packet according to AX01-AX06
    evidence rules;
  - folder readers suppress consecutive duplicate `AX01.rights` appendices
    when source, image state, and display policy are the same;
  - removed generic table-overflow appendix packing from the reading path.
- Updated `frontend/src/components/archive/appendix/AppendixLab.tsx` so AX01
  includes more record-specific evidence: display number, title, source URL,
  source identifier, access date, policy fields, and raw payload reference.
- Updated `frontend/src/lib/archive-data.ts`,
  `frontend/src/app/folders/[type]/page.tsx`, and
  `frontend/src/components/archive/drawer/FolderTypeSpeedIndex.tsx` so region
  folders display under macro groups such as North America, Europe, East Asia,
  West / South Asia, Africa, Oceania / Indigenous, Latin America / Caribbean,
  and Unresolved / Transregional.
- Rebuilt public payloads after the appendix rule update:
  - appendices exposed in payload: 195
  - `AX01.rights`: 35
  - `AX02.citation`: 15
  - `AX03.relations`: 63
  - `AX04.context`: 22
  - `AX05.statement`: 40
  - `AX06.typed-index`: 20

Verification:

- `npm run build` passed.
- Local dev server restarted and `http://localhost:3000/folders/region/russia`
  returned `200 OK`.

Interpretation:

- The payload still records all AX01 candidates for auditability, but folder
  reading now avoids a visible run of repeated same-source rights placeholders.
- The remaining content problem is not primarily layout. Some `IMG00` records
  need source remediation or replacement with image-ready alternate sources so
  rights appendices remain exceptional rather than a common reading experience.

## 2026-06-01 — AX01 State-Aware Rights Evidence and IA IMG00 Remediation

Purpose:

- Correct the mistaken assumption that `AX01.rights` only represents `IMG00`.
- Convert eligible metadata-only records into source-hosted image states where
  the source provides a stable image endpoint without requiring local copying.
- Keep genuinely rights-sensitive records as `IMG00` rather than inflating image
  coverage with uncleared images.

Changes made:

- Updated `frontend/src/components/archive/appendix/AppendixLab.tsx`:
  - AX01 now renders the actual `surface.image.state` (`IMG00`, `IMG01`,
    `IMG02`, or `IMG03`) instead of hardcoded `IMG00`;
  - non-IMG00 AX01 pages now say “image display evidence recorded” and explain
    that no image is reproduced on the appendix page;
  - AX01 evidence rows now include image state and rights basis.
- Updated `frontend/src/lib/paginate.ts` and
  `scripts/rebuild_public_surfaces_from_records.py`:
  - AX01 remains mandatory for `IMG00`;
  - selected `IMG01/IMG02/IMG03` records with unresolved display/review evidence
    can now receive AX01 after source/citation and relation appendices have
    priority.
- Added `scripts/remediate_img00_source_hosted_images.py`:
  - upgraded 29 Internet Archive records from `IMG00` to `IMG02`;
  - uses `https://archive.org/services/img/{identifier}` as a source-hosted
    display endpoint;
  - keeps `local_copy_permitted=false` and `rights_review_required=true`.
- Rebuilt all static public payloads.

Current image state after rebuild:

- total surfaces: 991
- `IMG00`: 39
- `IMG01`: 37
- `IMG02`: 479
- `IMG03`: 383
- `IMG04`: 53
- image-ready: 899 / 991
- image-ready coverage: 91%

Period image coverage after rebuild:

- `1830-1930`: 316 / 336 image-ready, 94.0%
- `1931-1970`: 399 / 469 image-ready, 85.1%
- `1971-2000`: 178 / 178 image-ready, 100.0%
- `2001-2026`: 6 / 8 image-ready, 75.0%

Remaining IMG00 by source:

- Art Institute of Chicago API: 35
- Wellcome Collection Catalogue API: 3
- Chinese Posters: 1

Rights interpretation:

- AIC samples expose `image_id` but return `is_public_domain=false`; these
  remain `IMG00` unless the project later adopts a source-viewer-only policy
  for AIC non-public-domain images.
- Wellcome samples with placeholder image URLs remain `IMG00`; the IIIF
  manifests return placeholder canvases rather than real visual evidence.
- Chinese Posters remains high-value but rights-sensitive; it should be treated
  as source-return evidence until explicit image reuse policy is verified.

Verification:

- `npm run build` passed after clearing stale `.next` cache.
- Local dev server restarted and
  `http://localhost:3000/folders/region/russia` returned `200 OK`.

## 2026-06-01 — Source Candidate Registry v1

Purpose:

- Separate the current public payload source count from the broader research
  source universe.
- Make community, university, government, municipal, and regional sources
  explicit before the next crawler wave.
- Move the project away from a narrow “large museum API” source model.

Changes made:

- Added `scripts/generate_source_candidate_registry_v1.py`.
- Generated `data/source_candidate_registry_v1.csv`.
- Generated `docs/capture/SOURCE_CANDIDATE_REGISTRY_v1.md`.

Current source registry state:

- 253 candidate sources total.
- 21 sources already active in the current public payload.
- 118 inherited from the earlier source expansion matrix.
- 114 newly added edge/community/local candidates.
- 154 rows are explicitly marked as community, university, government, or
  municipal sources.

Regional source candidate distribution:

- Western/Central Europe: 30
- North America: 28
- Latin America: 28
- East Asia: 27
- Eastern Europe: 23
- Southeast Asia: 23
- Africa: 20
- South Asia: 16
- Middle East and North Africa: 16
- Oceania and Pacific: 14

Next capture rule:

- Treat `source_candidate_registry_v1.csv` as the source planning universe.
- The public interface should count only sources with published surfaces.
- The About/methodology page can cite the 253-source registry as a verified /
  under-verification source universe.
- New crawls should be selected by protocol family and underrepresented region:
  Kramerius, OAI-PMH, IIIF, CONTENTdm, Omeka, DSpace, and local HTML archives.

## 2026-06-01 — Edge Source Probe and Item Capture Queue

Purpose:

- Begin execution of the expanded source strategy without inflating public
  surface counts.
- Verify source reachability and protocol clues before writing item-level
  crawlers.
- Avoid another broad museum-keyword pass by turning source evidence into a
  concrete adapter queue.

Changes made:

- Added `scripts/probe_source_candidate_registry_v1.py`.
- Generated `data/source_candidate_probe_v1.csv`.
- Stored source-level raw probe evidence in
  `data/source_candidate_probe_v1_raw/`.
- Added `docs/capture/SOURCE_CANDIDATE_PROBE_v1.md`.
- Added `scripts/generate_item_capture_queue_v1.py`.
- Generated `data/item_capture_queue_v1.csv`.
- Added `docs/capture/ITEM_CAPTURE_QUEUE_v1.md`.

Probe results:

- 60 edge/community/university/government/library candidates were probed.
- 51 returned a reachable source page.
- 6 returned HTTP errors.
- 3 failed at probe level.
- 27 are promoted as `P1_adapter_candidate`.
- 16 are promoted as `P2_html_source_candidate`.

Next item-level queue:

- 39 source rows queued.
- 27 Q1 adapter/protocol rows.
- 12 Q2 HTML/text rows.

Adapter mix in the queue:

- `html_text_source_adapter`: 12
- `html_jsonld_adapter`: 8
- `iiif_manifest_adapter`: 6
- `pdf_text_or_link_adapter`: 6
- `dspace_oai_or_rest_adapter`: 3
- `kramerius_adapter`: 2
- `omeka_api_adapter`: 1
- `html_source_probe_then_manual_rules`: 1

Regional mix in the queue:

- Latin America: 9
- East Asia: 8
- Eastern Europe: 8
- Africa: 5
- South Asia: 3
- Middle East and North Africa: 2
- Southeast Asia: 2
- Oceania and Pacific: 2

Important correction:

- Initial protocol detection over-counted `ArchiveSpace/EAD` because a broad
  string match could detect ordinary HTML `head` text. The detector was
  tightened and the probe was rerun before writing the final queue.

Execution rule:

- Run one adapter family at a time.
- Each item-level capture must write raw source payloads, rights/source
  evidence, text excerpts or context, and failure rows.
- Sources that fail automation remain in the registry as link-only/manual-review
  sources rather than disappearing from the archive map.

## 2026-06-01 — Public Surface Gate Recalculation

Purpose:

- Tighten the distinction between a full main sheet, a support packet, a card,
  and a bookmark-level fragment.
- Prevent thin metadata rows from reading as full archive sheets.
- Prepare the data layer for duplicate/enrichment clustering, where weaker rows
  can support stronger canonical records instead of appearing as repeated pages.

Changes made:

- Updated `scripts/run_midcentury_capture_1930_1970.py` with a true 0-100
  completeness score.
- Raised the full main-sheet threshold from the earlier permissive `60` to
  `75`.
- Added `surfaceDisposition`, `publicationRole`, `sourceReadingTextLength`,
  `contextTextLength`, and `publicationGate` fields to generated surfaces.
- Updated methodology rules in:
  - `docs/methodology/ARCHIVE_PRODUCTION_RULEBOOK_v0.md`
  - `docs/methodology/SURFACE_TAXONOMY_RULEBOOK_v0.md`
  - `docs/methodology/SURFACE_GENERATION_PIPELINE_v0.md`
- Added recalculation report:
  `docs/capture/PUBLIC_SURFACE_GATE_RECALC_2026_06_01.md`.

Recalculation result:

- 1092 input rows after dedupe.
- 991 public surfaces.
- 44 folder views.
- 899 image-ready surfaces (`IMG01`/`IMG02`/`IMG03`), or 91%.
- 237 top-level appendix candidates.

Disposition counts:

- `main_sheet`: 849
- `support_packet_appendix_text`: 125
- `merge_candidate_support_packet`: 14
- `thin_visual_support_packet`: 1
- compound / missing explicit disposition: 2

Rule note:

- Support packets may still use existing sheet templates until the frontend has
  a dedicated support-packet renderer. The data layer now marks them separately
  so they do not have to be treated as full main sheets.

## 2026-06-01 — Surface Group Candidate Audit

Purpose:

- Establish grouping logic before the next broad coverage pass.
- Give loose leaves, support packets, cards, appendices, and bookmark-level
  fragments a responsible parent-candidate system.
- Avoid treating repeated thin source rows as independent main sheets when
  they should support a stronger canonical record or source register.

Files added:

- `scripts/generate_surface_group_candidates_v1.py`
- `data/surface_group_candidates_v1.csv`
- `data/surface_group_memberships_v1.csv`
- `docs/capture/SURFACE_GROUPING_AUDIT_v1.md`

Audit result:

- 231 candidate groups.
- 1588 candidate memberships.
- Group types include `same_title_within_source`, `same_series_stem`,
  `same_source_collection`, and `folder_cell_decade`.
- Recommended actions include canonical main records with source registers,
  canonical main records with support children, support-packet clusters,
  compound-main candidates, and review-only groups.

Important constraint:

- These groups are not final merged records. They are a capture and review
  scaffold. The next coverage passes should attach new records to these
  candidates when evidence is strong, and create new groups only when a record
  cannot responsibly attach.

Next use:

- The 1970-2026 capture pass should use group-level gaps (`needs_image`,
  `needs_text`, `needs_rights`, `multi_region_review`) to decide what to search
  next.
- Coverage remains the priority until the region/theme/medium/movement map is
  structurally complete; fine enrichment can follow once the category skeleton
  is stable.

## 2026-06-01 — Late Period Coverage Capture 1970-2026

Purpose:

- Start the 1970-2026 coverage pass after establishing group candidates.
- Add late-period visual/design records without changing the frozen record
  schema.
- Prefer source-hosted image evidence and text/discourse support records over
  local image copying.

Files added:

- `scripts/run_late_period_coverage_capture_1970_2026.py`
- `data/capture_batch_late_period_coverage_1970_2026_records.csv`
- `data/capture_batch_late_period_coverage_1970_2026_source_summary.csv`
- `data/capture_batch_late_period_coverage_1970_2026_raw/`
- `docs/capture/LATE_PERIOD_COVERAGE_CAPTURE_2026_06_01.md`

Capture result:

- 104 new late-period records.
- Sources:
  - Internet Archive / text and periodical collections: 46
  - Te Papa Collections Online: 24
  - NAIDOC Poster Gallery: 23
  - Wikimedia Commons: 11
- Image states:
  - `IMG02`: 92
  - `IMG03`: 11
  - `IMG00`: 1
- Period split:
  - 1970-2000: 24
  - 2001-2026: 80

Payload result:

- Rebuilt public surfaces with the late-period batch included.
- 1196 input rows after dedupe.
- 1095 public surfaces.
- 45 folder views.
- 1002 image-ready surfaces, or 92%.
- Regenerated group candidates: 257 groups and 1773 memberships.

Important note:

- Late-period coverage is now high by renderable image state, but most new
  image records are `IMG02` source-hosted display records. This is not the same
  as open reuse. Source return and rights evidence remain mandatory.
- The global 95% launch gate is still blocked mostly by earlier/midcentury
  `IMG00`/`IMG04` records, especially AIC, V&A, Met, LoC, Getty, and Wellcome.

## 2026-06-01 — Image Coverage Metric Recalibration

Purpose:

- Correct the over-optimistic interpretation of image coverage.
- Stop treating `IMG02` source-hosted display records as equivalent to
  publication-grade image coverage.

Changes made:

- Updated `scripts/audit_image_release_gate.py` to report:
  - source-visible coverage
  - verified open coverage
  - weighted publication coverage
- Added report:
  `docs/capture/IMAGE_COVERAGE_METRICS_RECALIBRATION_2026_06_01.md`.

Current recalibrated result:

- Source-visible coverage: 91.51%.
- Verified open coverage: 35.98%.
- Weighted publication coverage: 71.4%.
- Weighted/publication-grade launch gate remains 95%.

Rule note:

- `IMG02` remains a valid rights-aware display state, but it is no longer
  treated as a full image-coverage success.
- Future capture should continue broad source/category coverage while also
  prioritizing explicit rights evidence that can move records toward `IMG03`.

## 2026-06-01 — Full-Coverage Source Probe and 1970-2026 Queue

Purpose:

- Continue full coverage work without turning every source page into a weak
  public sheet.
- Probe underrepresented non-European/non-US community, university, government,
  municipal, and library sources before item-level capture.

Probe result:

- 111 source candidates probed.
- 82 reachable `ok` sources.
- 45 `P1_adapter_candidate` rows.
- 27 `P2_html_source_candidate` rows.
- Region mix includes Latin America, East Asia, Eastern Europe, Africa,
  Southeast Asia, Oceania/Pacific, South Asia, and Middle East/North Africa.

Queue result:

- Regenerated `data/item_capture_queue_v1.csv`.
- 65 item-level queue rows for the 1970-2026 coverage pass.
- Q1 rows: 45.
- Q2 rows: 20.
- Adapter mix includes IIIF, DSpace/OAI, Kramerius, Omeka, CONTENTdm, JSON-LD,
  PDF/text, and HTML text sources.

Important rule:

- The queue is not public archive content. It is the next capture map.
- Failed or HTTP-error sources stay in the source registry as source
  territories; they are not deleted just because automation is difficult.

## 2026-06-01 — Protocol Item Capture 1970-2026

Purpose:

- Start converting the 1970-2026 queue into item-level records from
  underrepresented protocol sources.
- Avoid promoting source-level hopes or weak keyword matches into public
  sheets.

Changes made:

- Added `scripts/run_protocol_item_capture_1970_2026.py`.
- Captured Q1 DSpace/OAI and Omeka sources first.
- Wrote `data/capture_batch_protocol_item_1970_2026_records.csv`.
- Wrote `data/capture_batch_protocol_item_1970_2026_source_summary.csv`.
- Wrote raw API payloads under
  `data/capture_batch_protocol_item_1970_2026_raw/`.
- Wrote `docs/capture/PROTOCOL_ITEM_CAPTURE_1970_2026.md`.

Result:

- 8 promoted item-level records.
- 6 sources attempted.
- Promoted source families include University of Ghana Digital Collections,
  National Repository of Nigeria, and University of Cape Town Digital
  Collections.
- Repeated newspaper/magazine issue records are grouped before publication so
  they do not render as many thin sheets.

Validation:

- Rebuilt static public surfaces with the protocol batch included.
- 1204 input rows after dedupe.
- 1103 public surfaces.
- Image states: `IMG00=40`, `IMG01=37`, `IMG02=573`, `IMG03=394`,
  `IMG04=59`.
- `scripts/audit_public_surface_integrity.py` passed with no exact repeated
  image URLs and no placeholder image URLs.
- Weighted publication coverage is 71.0%; this pass improves source diversity
  and reading context, not release-grade image coverage.

## 2026-06-01 — Source Breadth Capture 1970-2026

Purpose:

- Increase distinct source coverage beyond the dominant museum/API sources.
- Prioritize underrepresented municipal, national-library, community, and
  university sources without promoting generic landing pages as archive sheets.
- Improve the source mix for Aotearoa New Zealand, Japan, and Argentina.

Changes made:

- Added `scripts/run_source_breadth_capture_1970_2026.py`.
- Captured Auckland Libraries Heritage Collections via CONTENTdm item records.
- Captured Los Angeles Public Library Tessa via CONTENTdm item records.
- Captured University of Washington Digital Collections via CONTENTdm item
  records.
- Captured SMU Libraries, University of Miami Libraries, and Temple University
  Libraries via the same CONTENTdm family adapter.
- Probed additional CONTENTdm-family local/university sources, keeping
  no-record or timeout outcomes in the source summary instead of promoting them
  as thin public sheets.
- Captured limited AHIRA and CeDInCI WordPress source-context records only when
  title/body evidence mentions magazines, posters, design, advertising, or
  political print culture.
- Captured NDL Search / National Diet Library SRU bibliographic records for
  Japanese advertising/poster/design publication evidence.
- Wrote `data/capture_batch_source_breadth_1970_2026_records.csv`.
- Wrote `data/capture_batch_source_breadth_1970_2026_source_summary.csv`.
- Wrote raw payloads under
  `data/capture_batch_source_breadth_1970_2026_raw/`.
- Wrote `docs/capture/SOURCE_BREADTH_CAPTURE_1970_2026.md`.
- Added the new records CSV to the cumulative static payload rebuild script.

Result:

- 39 promoted records.
- 9 additional public sources.
- Image states in this batch: `IMG02=23`, `IMG03=6`, `IMG04=10`.
- Auckland CONTENTdm now prefers image-bearing records first and limits
  text-only folder records to avoid a source becoming only a register.
- New promoted sources in this update: Auckland Libraries, LAPL Tessa,
  University of Washington, University of Miami Libraries, SMU Libraries,
  Temple University Libraries, AHIRA, CeDInCI, and NDL Search.

Validation:

- Rebuilt static public surfaces with this batch included.
- 1243 input rows after dedupe.
- 1142 public surfaces.
- Distinct public sources: 33.
- Image states: `IMG00=40`, `IMG01=37`, `IMG02=596`, `IMG03=400`,
  `IMG04=69`.
- Period source-visible image coverage: pre-1930 `94.9%`, 1931-1970 `86.0%`,
  1971-2000 `95.6%`, 2001-2026 `88.8%`.
- `scripts/audit_public_surface_integrity.py` passed with no exact repeated
  image URLs and no placeholder image URLs.
- Source-visible image coverage is 90.46%; weighted publication coverage is
  70.41%, still far below the 95% launch target because many source-hosted
  images remain `IMG02` rather than verified-open `IMG03`.

## 2026-06-01 — Independent + Asia Source Probe and Capture

Purpose:

- Expand the source map beyond large museum APIs and Western institutional
  sources.
- Treat post-1990 independent design sites as a contemporary context/link
  layer, not as open-image evidence.
- Begin a more careful East Asia and Southeast Asia source strategy covering
  local, community, university, government, and independent archives from
  pre-WWII contexts to the present.

Changes made:

- Added `scripts/probe_independent_asia_sources_v1.py`.
- Probed 30 independent, East Asian, and Southeast Asian source candidates.
- Wrote `data/source_probe_independent_asia_v1.csv`.
- Wrote raw probe payloads under
  `data/source_probe_independent_asia_v1_raw/`.
- Wrote `docs/capture/INDEPENDENT_ASIA_SOURCE_PROBE_v1.md`.
- Added `scripts/run_independent_asia_capture_1990_2026.py`.
- Captured a small low-risk batch from Malaysia Design Archive and Another
  Graphic via public WordPress REST endpoints.
- Corrected Malaysia Design Archive image detection by following
  `wp:attachment` media links; this reduced false `IMG04` records in the batch.
- Wrote `data/capture_batch_independent_asia_1990_2026_records.csv`.
- Wrote `data/capture_batch_independent_asia_1990_2026_source_summary.csv`.
- Wrote raw payloads under
  `data/capture_batch_independent_asia_1990_2026_raw/`.
- Wrote `docs/capture/INDEPENDENT_ASIA_CAPTURE_1990_2026.md`.
- Added the new records CSV to the cumulative static payload rebuild script.

Source policy:

- Pinterest, Instagram, Behance, Are.na, and similar platforms may be used only
  as discovery channels for original source sites.
- Independent/community design sites default to `IMG02` source-hosted display
  or `IMG00/IMG04` when image rights or media endpoints are not clear.
- No independent-site image is promoted to `IMG03` without explicit item-level
  open licensing.

Result:

- Source probe: 30 candidates, 22 reachable, 19 P1 next-capture candidates.
- Capture batch: 22 promoted records from 2 sources.
- Batch image states after attachment fix: `IMG02=20`, `IMG04=2`.
- New public sources added in this update: Malaysia Design Archive and Another
  Graphic.

Validation:

- Rebuilt static public surfaces with this batch included.
- 1265 input rows after dedupe.
- 1164 public surfaces.
- Distinct public sources: 35.
- Image states: `IMG00=40`, `IMG01=37`, `IMG02=616`, `IMG03=400`,
  `IMG04=71`.
- Period source-visible image coverage: pre-1930 `94.0%`, 1931-1970 `85.2%`,
  1971-2000 `98.2%`, 2001-2026 `87.1%`.
- `scripts/audit_public_surface_integrity.py` passed with no exact repeated
  image URLs and no placeholder image URLs.
- Source-visible coverage remains `90.46%`; weighted publication coverage is
  `70.19%`. The launch target is not met because the source-hosted `IMG02`
  population is large and must be treated as rights-sensitive rather than
  open-image proof.

## 2026-06-01 — Edge Source Probe v2

Purpose:

- Expand the source map toward the 200-source target with underrepresented,
  local, community, university, professional, and government sources.
- Move beyond the current large-institution API bias, especially across East
  Asia, Southeast Asia, Latin America, Africa, and the Middle East.
- Build a source-registry layer before promoting thin records into public
  surfaces.

Changes made:

- Added `scripts/probe_edge_source_candidates_v2.py`.
- Probed 64 source candidates and wrote
  `data/source_probe_edge_v2.csv`.
- Wrote redacted raw probe payloads under
  `data/source_probe_edge_v2_raw/`.
- Wrote `docs/capture/EDGE_SOURCE_PROBE_v2.md`.
- Tightened protocol detection after catching an `EAD` false positive caused
  by generic HTML text.

Result:

- 48 of 64 candidates were reachable during this run.
- 37 candidates were marked P1 for adapter/source-registry follow-up.
- P1 regional distribution: Southeast Asia 17, East Asia 8, Latin America 4,
  Global 3, Africa 2, North America 1, Europe 1, Middle East 1.
- Protocol hints among reachable pages: WordPress REST/RSS 16, JSON-LD 14,
  PDF 7, RSS/Atom 6, IIIF 3, Next/static JS 1, ArchiveSpace/EAD 1.

Policy notes:

- This probe does not publish archive records or inflate surface counts.
- Social platforms remain discovery-only and default to `IMG00`.
- Independent/community/private sources default to `IMG02` source-hosted or
  `IMG00` link-only until item-level rights and image endpoints are reviewed.
- The next capture pass should prioritise P1 sources with repeatable protocols
  first: WordPress, IIIF, JSON-LD, PDF/OCR, and stable institutional HTML.

Validation:

- `scripts/audit_secret_patterns.py` passed after the probe.

## 2026-06-01 — Edge WordPress Source Capture 1970-2026

Purpose:

- Convert the edge-source probe into a small number of actual capture records
  without lowering the archive threshold.
- Prefer public WordPress REST endpoints because they expose repeatable
  metadata, source URLs, source text, and source-hosted image references.
- Expand post-1970 source breadth through Southeast Asian, Indonesian,
  Cambodian, regional film, independent, and design-history sources.

Changes made:

- Added `scripts/run_edge_wordpress_source_capture_1970_2026.py`.
- Wrote `data/capture_batch_edge_wordpress_1970_2026_records.csv`.
- Wrote `data/capture_batch_edge_wordpress_1970_2026_source_summary.csv`.
- Wrote raw payloads under
  `data/capture_batch_edge_wordpress_1970_2026_raw/`.
- Wrote `docs/capture/EDGE_WORDPRESS_CAPTURE_1970_2026.md`.
- Added this records CSV to the cumulative public-surface rebuild input list.

Result:

- Captured 40 source-context records from 5 sources.
- Source counts: Desain Grafis Indonesia 10, Asian Film Archive 8, Bophana
  Audiovisual Resource Center 8, Design Reviewed 8, Another Graphic 6.
- Image states: `IMG02=39`, `IMG04=1`.
- 38 records include at least 160 characters of source text.
- No duplicate source URLs or duplicate detected image URLs were found inside
  this batch.

Quality notes:

- This is not a final publication batch. These records should pass through the
  surface taxonomy gate: many should become source-context sheets, text pages,
  cards, or grouped appendices rather than automatic main sheets.
- Administrative pages, terms/privacy pages, tender/application notices,
  reopening notices, and other non-archive announcements are filtered out by
  the capture script.
- Images remain source-hosted and rights-sensitive; no record is promoted to
  `IMG03` in this pass.

Validation:

- `scripts/audit_secret_patterns.py` passed after the capture.

## 2026-06-01 — Deep Research Integration Review: Source, Linkage, Image, Surface, Contemporary Noise

Purpose:

- Read the five newly added Deep Research reports in `reports/deep-research`.
- Integrate their implications into a single project-facing review before further
  capture expansion.

Reviewed reports:

- `Rights-Aware Source Discovery for a Distributed Graphic Design History Archive Index.docx`
- `Provenance-First Record Linkage for a Graphic Design History Archive.docx`
- `Rights-Aware Visual Evidence Standard for a Graphic Design Archive Index.docx`
- `Publication-Surface Logic for a Graphic Design History Archive.docx`
- `Inclusion and Noise Filtering for Contemporary Graphic Design Archive Capture.docx`

Changes made:

- Added `docs/research-reviews/DEEP_RESEARCH_2026_06_01_INTEGRATION_REVIEW_v0.md`.

Result:

- Confirmed that the next capture phase should expand source breadth and protocol
  coverage before blindly adding more public sheets.
- Confirmed that duplicate/overlapping source records should be preserved and
  grouped as composite records, dossiers, or explicit relations rather than
  silently deduplicated.
- Confirmed that image health must be measured in separate layers: source-visible,
  publication-grade, open-image, rights-labeled, and unclear image state.
- Confirmed that weak records should route to text pages, appendices, slips,
  cards, bookmarks, or grouped dossiers rather than thin main sheets.
- Confirmed that contemporary capture needs source-type gates and noise filters
  so social/discovery platforms remain leads unless provenance is established.

Next action:

- Build a broader source prospect registry with source family, protocol, region,
  language/script, rights posture, image path, and text path.
- Add period-split and source-breadth metrics before the next major capture pass.
- Update grouping and appendix generation so repeated AX01 pages are not created
  without record-specific evidence differences.

## 2026-06-01 — Deep Research Remediation Plan

Purpose:

- Convert the five Deep Research findings into a durable, step-by-step
  remediation plan so the project does not lose the thread after context
  compaction or parallel work.

Changes made:

- Added `docs/methodology/DEEP_RESEARCH_REMEDIATION_PLAN_2026_06_01.md`.

Plan locked:

1. Build `source_prospect_registry_v2` before the next broad capture pass.
2. Add layered image/source metrics by period and source family.
3. Generate linkage/group candidates before public-surface promotion.
4. Recalculate surface assignment so weak rows become text pages, appendices,
   cards, slips, bookmarks, or grouped dossiers rather than thin main sheets.
5. Add appendix inheritance and repetition suppression, especially for AX01.
6. Add contemporary source-type gates and noise filters.

Next implementation task:

- Create `scripts/generate_source_prospect_registry_v2.py`,
  `data/source_prospect_registry_v2.csv`, and
  `docs/capture/SOURCE_PROSPECT_REGISTRY_v2.md`.

## 2026-06-01 — Source Prospect Registry v2

Purpose:

- Execute the first remediation task from
  `docs/methodology/DEEP_RESEARCH_REMEDIATION_PLAN_2026_06_01.md`.
- Consolidate the source universe before more broad capture so future crawls
  can be selected by region, protocol, source family, language/script, and
  rights posture.

Changes made:

- Added `scripts/generate_source_prospect_registry_v2.py`.
- Generated `data/source_prospect_registry_v2.csv`.
- Added `docs/capture/SOURCE_PROSPECT_REGISTRY_v2.md`.

Inputs merged:

- `data/source_candidate_registry_v1.csv`
- `data/source_candidate_probe_v1.csv`
- `data/source_probe_edge_v2.csv`
- `data/source_probe_independent_asia_v1.csv`
- `data/source_dependency_ledger.csv`
- all `data/capture_batch_*_source_summary.csv` files

Result:

- 298 source prospects.
- 129 `P1_next_adapter_or_probe` candidates.
- 103 P1 candidates outside Western Europe / North America.
- 161 local/community/university/government/municipal candidates.
- 0 duplicate source names after same-name/source-summary merging.

Validation:

- Required registry fields are populated except for 16 source URLs inherited
  from capture summary rows that need source-registry backfill.
- `scripts/audit_secret_patterns.py` passed.

Next action:

- Implement layered image/source metrics by period and source family before
  running another capture batch.

## 2026-06-01 — Remediation Execution: Metrics, Linkage, Gates, Appendix

Purpose:

- Execute the Deep Research remediation plan in data/methodology layers before
  another broad capture pass.
- Correct misleading image coverage, repeated records, thin main sheets, and
  repetitive appendix behavior.

Changes made:

- Added `scripts/audit_layered_image_source_metrics_v1.py`.
- Generated `data/layered_image_source_metrics_v1.csv`.
- Generated `data/duplicate_image_url_warnings_v1.csv`.
- Added `docs/capture/LAYERED_IMAGE_SOURCE_METRICS_v1.md`.
- Added `scripts/generate_source_record_linkage_candidates_v1.py`.
- Generated `data/source_record_linkage_candidates_v1.csv`.
- Generated `data/source_record_linkage_memberships_v1.csv`.
- Added `docs/capture/SOURCE_RECORD_LINKAGE_CANDIDATES_v1.md`.
- Added `scripts/audit_surface_assignment_gates_v1.py`.
- Generated `data/surface_assignment_gate_audit_v1.csv`.
- Added `docs/capture/SURFACE_ASSIGNMENT_GATE_AUDIT_v1.md`.
- Added `scripts/audit_appendix_generation_rules_v1.py`.
- Generated `data/appendix_generation_rule_audit_v1.csv`.
- Added `docs/capture/APPENDIX_GENERATION_RULE_AUDIT_v1.md`.
- Updated `docs/methodology/SURFACE_TAXONOMY_RULEBOOK_v0.md`,
  `docs/methodology/SURFACE_GENERATION_PIPELINE_v0.md`, and
  `docs/methodology/DEEP_RESEARCH_REMEDIATION_PLAN_2026_06_01.md`
  to use the hierarchy:
  `main sheet -> subsheet -> appendix/text sheet -> card/slip -> bookmark`.

Key results:

- Capture records audited: 1,378.
- Source-visible image coverage: 92.02%.
- Publication-grade candidate coverage: 84.40%.
- Open-image candidate coverage: 9.36%.
- Duplicate image URL groups: 33.
- Source-record linkage groups: 321.
- Linkage memberships: 1,076.
- Confirmed same-entity groups: 87.
- Series/campaign groups: 85.
- Repeated-image review groups: 33.
- Revised surface gate audit now identifies:
  - 974 `main_sheet_candidate` rows;
  - 188 `subsheet_visual` rows;
  - 55 `appendix_or_text_sheet` rows;
  - 45 `dedupe_child_record` rows;
  - 31 `subsheet_text_or_appendix_review` rows;
  - 26 `text_sheet_candidate` rows;
  - 24 `subsheet_group_child` rows;
  - 16 `subsheet_or_group_anchor_review` rows;
  - 16 `img00_rights_sheet_candidate` rows;
  - 3 `duplicate_image_review_packet` rows.
- Appendix audit now emits 633 evidence packets with no placeholder-like AX
  packets:
  - AX06: 246;
  - AX05: 122;
  - AX02: 105;
  - AX01: 88;
  - AX04: 51;
  - AX03: 21.

Interpretation:

- Previous "image coverage" was too blunt. The archive has strong
  source-visible coverage, but open-image coverage remains low and must not be
  reported as a launch-quality visual archive metric.
- Many former main sheets should become subsheets. Subsheet is now the explicit
  home for strong-but-thin visual records.
- Duplicate and same-source records should be grouped or inherited, not shown as
  unrelated standalone sheets.
- AX01 is no longer an automatic per-record page; it is emitted only when
  rights/display evidence is materially needed, and it can support IMG00/01/02/03.

Validation:

- `scripts/audit_secret_patterns.py` passed after these generated reports.

Next action:

- Add contemporary source/noise filtering before the next 1990-2026 independent
  and local-source capture pass.

## 2026-06-01 — Text Page Group 04 Design Correction

Purpose:

- Correct the fourth text-page group after review showed three layouts were
  borrowing asset languages that belong to tickets, bookmarks, cards, or
  specimen sheets rather than A4 text pages.

Failure recorded:

- The previous experimental text-page pass treated overflow as the primary
  problem, but the deeper issue was design-system mismatch.
- A tabbed/register page, a full-page background-image overprint, and an
  unconditional four-image wall repeated earlier asset directions and weakened
  the text-page reading hierarchy.

Changes made:

- Kept the accepted perforated-register and waiting-plate directions.
- Replaced the tabbed/register study with a marginal-essay text page.
- Replaced the background-image overprint with a bounded cutline-plate page.
- Replaced the unconditional four-image wall with a source-dossier page that
  only renders a multi-image wall when the same surface has at least three
  distinct renderable images.
- Removed Group 02 page 02 from the text-page preview set; Group 02 now keeps
  only the accepted first, third, and fourth layouts.
- Added text-page-specific constraints to
  `docs/frontend/ASSET_PREVIEW_CAPTURE_CONSTRAINTS.md`.

Validation:

- `npm run build` passed.
- `npm run capture:text-pages` passed and produced a manifest with no overflow,
  broken-image, missing-group, empty-group, or ratio issues:
  `/private/tmp/mgd-text-page-captures/20260601T142922Z/manifest.json`.

Constraint added:

- Text pages must not borrow functional border/edge language from bookmarks,
  cards, slips, tickets, or appendices.
- Text pages must not use source images as full-page background textures.
- Multi-image walls are allowed only when the same surface has at least three
  distinct renderable image URLs; otherwise the layout must fall back to a
  single evidence plate plus text/citation structure.

## 2026-06-01 — Remediation Execution: Contemporary Filter And Date-Range Guard

Purpose:

- Prevent contemporary/local-source expansion from ingesting generic design
  pages as public archive records.
- Prevent capture-phase ranges such as `1970-2026` from appearing as object,
  movement, or sheet chronology.

Changes made:

- Added `scripts/contemporary_noise_filter.py`.
- Added `scripts/audit_contemporary_noise_filter_v1.py`.
- Generated `data/contemporary_noise_filter_audit_v1.csv`.
- Added `docs/capture/CONTEMPORARY_NOISE_FILTER_AUDIT_v1.md`.
- Integrated the shared filter into:
  - `scripts/run_late_period_coverage_capture_1970_2026.py`;
  - `scripts/run_source_breadth_capture_1970_2026.py`;
  - `scripts/run_independent_asia_capture_1990_2026.py`;
  - `scripts/run_edge_wordpress_source_capture_1970_2026.py`.
- Added `scripts/audit_public_date_range_leaks_v1.py`.
- Generated `data/public_date_range_leak_audit_v1.csv`.
- Added `docs/capture/PUBLIC_DATE_RANGE_LEAK_AUDIT_v1.md`.
- Updated `scripts/rebuild_public_surfaces_from_records.py` so broad
  source/capture ranges are treated as source scope, not object dates.
- Updated protocol and noncanonical capture scripts so future records do not
  write capture-phase date ranges into public notes or ongoing collection-level
  source records.

Key results:

- Existing contemporary-adjacent rows audited: 281.
- Noise decisions:
  - 243 `include_candidate`;
  - 16 `downgrade_candidate`;
  - 22 `review_lead`;
  - 0 `discovery_only`;
  - 0 `exclude_noise`.
- Public payload rebuilt from records:
  - 1,305 source rows after dedupe;
  - 1,204 surfaces;
  - 45 folders;
  - image states: 40 IMG00, 37 IMG01, 655 IMG02, 400 IMG03, 72 IMG04;
  - image-ready layer: 1,092 / 1,204 (91%).
- Public date-range leak audit now reports 0 issues for visible public fields.
- Manual verification found 0 visible `1970-2026` / `1930-1970` phase labels
  in sheet title/date/context fields after rebuild.

Constraint added:

- Capture-phase bands may exist in file names, raw payload paths, and internal
  reports, but not in public object chronology. Collection-level records with
  ongoing ranges must resolve to source scope, bookmark/source dossier, or
  grouped support material unless item-level dates are captured.

Follow-up fix:

- Expanded the public date-range leak audit to include folder `scopeNote`,
  visible table rows, and broad movement-folder date ranges.
- Updated the public payload rebuild step so folder notes describe folder
  function rather than capture stage.
- Movement folders with member spans above 35 years now expose the broad span
  only as `memberDateStart/memberDateEnd` with
  `chronologyStatus=member_date_span_not_movement_duration`; public
  `dateStart/dateEnd` are cleared so the UI does not read the member span as a
  movement duration.
- Rebuilt the public payload and reran the expanded audit: 0 public date-range
  leak issues.

## 2026-06-02 — Failure Record: Text Page Group Baseline Drift

Failure:

- The requested operation was to delete `TP13` and `TP15`, then show only
  `TP12`, `TP14`, and `TP16` as Group 04.
- The implementation path treated a membership/filtering request as if it were
  an opportunity to revise the group presentation, causing the accepted
  baseline to appear changed.
- This made screenshot review unreliable because the user could no longer
  compare the remaining accepted layouts against the prior accepted state.

Constraint:

- Layout deletion/filtering requests are membership-only unless the user
  explicitly asks for redesign.
- Do not change kept layout component code, CSS, assigned surfaces, card/page
  scale, or screenshot framing while carrying out deletion/filtering.
- Preserve and compare against the last accepted screenshot baseline by layout
  ID, rendered page class, dimensions, and capture manifest.
- If the instruction names layout IDs, repeat those IDs internally and execute
  that exact set; do not remap to a new composition.

Corrected state:

- Group 04 contains only `TP12.perforated-field`, `TP14.waiting-plate`, and
  `TP16.source-dossier`.
- The accepted corrected capture preserved the original five-up scale and
  passed manifest checks with no overflow, broken image, missing group, empty
  group, or ratio issues:
  `/private/tmp/mgd-text-page-captures/20260601T160157Z/manifest.json`.

## 2026-06-02 — Main Sheet Group 01 Frozen

Decision:

- The first main-sheet group is accepted and frozen as four distinct layout
  directions:
  - `MS01.protocol-ledger`
  - `MS02.evidence-dossier`
  - `MS03.split-bulletin`
  - `MS04.grid-register`
- `MS02` and `MS03` are the preferred main-sheet voice. They should appear
  materially more often than `MS01` and `MS04`.

Distribution:

- Default ratio: `MS01 : MS02 : MS03 : MS04 = 2 : 3.5 : 3.5 : 1`.
- Normalized target: `20% / 35% / 35% / 10%`.

Implementation notes:

- Added `frontend/src/lib/main-sheet-layout.ts` as the reusable layout registry
  and weight source.
- Added `frontend/src/components/archive/main-sheets/MAIN_SHEET_RULES.md` to
  document the frozen set, use cases, and hard constraints.
- The accepted capture for this group passed the headless preview audit with no
  overflow or broken images:
  `/private/tmp/mgd-main-sheet-captures/20260602T010700Z/main-sheets-group-01.png`.

Constraint:

- Do not collapse the four frozen directions into one generic main-sheet
  template. Future main-sheet work may extend the set, but it must preserve the
  accepted layout IDs and their distribution unless explicitly revised.

## 2026-06-02 — Postwar DigitalNZ Capture Repair

Action:

- Added `scripts/run_digitalnz_postwar_image_ready_1945_2026.py` as a
  postwar-first regional image-ready capture batch for Aotearoa New Zealand and
  Pacific-connected visual communication records.
- Repaired `scripts/run_digitalnz_image_ready_1830_1970.py` so DigitalNZ uses
  the active `text` query parameter instead of ignored `search_text`.
- Repaired object-date parsing so `syndication_date`, `updated_at`, and
  record/upload dates do not become public object dates. When `display_date`
  exists, it is treated as the preferred object-date source.

Result:

- First broken run produced 0 records because the inactive query parameter
  returned default noise.
- After query repair, the batch produced 130 records, but inspection revealed
  pre-1945 records misfiled by record synchronization dates.
- After date repair, the final batch produced 117 records:
  - `IMG03`: 53
  - `IMG02`: 64
  - `IMG00/IMG01/IMG04`: 0
- The final batch has no pre-1945 rows, no object-date spans above 40 years,
  and no duplicate image URLs. Duplicate titles remain where they represent
  series/event views and should be handled by grouping rather than deletion.

Constraint:

- Source API record/update/syndication dates must never be used as object
  history dates unless the source explicitly identifies them as creation,
  publication, or object dates.
- For DigitalNZ-style aggregators, public object dating must prefer
  `display_date`; fallback date fields require inspection because they may be
  repository timestamps.
- Partial/non-commercial visual records may enter as `IMG02` only with
  source-return display policy, no local copy, and rights review required.

## 2026-06-02 — Edge RSS/HTML Source Probe

Action:

- Added `scripts/run_edge_rss_html_source_capture_1970_2026.py` for
  post-1970 independent/professional/community design sources that expose feeds
  but not clean object APIs.
- The adapter fetches RSS/Atom items, then visits item pages for
  `og:image`/description metadata. It writes source-context rows only:
  source-hosted images, no local copy, rights review required.
- Raw HTML/XML writes are passed through the same secret-pattern redaction
  guard used for edge WordPress captures.

Result:

- Captured 8 `IMG02` source-context records from Another Graphic.
- JAGDA and Tokyo TDC feed endpoints were reachable but did not yield included
  rows under the current design-term/date/noise filters.
- Fonts In Use, People's Graphic Design Archive, M+ Magazine, BiblioAsia, and
  Design Reviewed feed endpoints failed or were unavailable through the tested
  feed URLs.

Constraint:

- Generic RSS probing is useful for source feasibility but should not be
  treated as sufficient coverage for independent design archives.
- JAGDA, Tokyo TDC, Fonts In Use, M+, PGDA, and BiblioAsia need source-specific
  adapters or manually seeded item routes before they can be counted as serious
  coverage.

## 2026-06-02 — Source Coverage Rate v1

Action:

- Added `scripts/audit_source_coverage_rate_v1.py` to measure source breadth
  separately from image readiness.
- The metric distinguishes candidate/prospect sources from active captured
  sources. Candidate sources do not count as coverage until at least one record
  enters a capture batch.
- The v1 formula uses region-weighted source points, then applies a
  time-coverage multiplier:
  `source_coverage_rate_v1 = source_pool_rate × time_weighted_balance_rate`.
- A stricter diagnostic also multiplies by regional distribution balance, but
  this is not the main rate because `source_pool_rate` already includes region
  weights.

Current result:

- Candidate/prospect sources: 298
- Active captured sources: 39
- Weighted active source points: 30.75 / 200.00
- Source pool rate: 15.38%
- Time-weighted balance rate: 33.00%
- Source coverage rate v1: 5.07%
- Strict distribution-adjusted diagnostic: 0.72%

Constraint:

- Do not use raw candidate source count as a public coverage claim.
- Source coverage reporting must include at least:
  active source count, candidate source count, region-weighted source rate,
  time-weighted balance, and strict regional distribution diagnostic.
- Region/source mapping gaps are themselves coverage failures. A record filed
  under an East Asian region folder does not prove East Asian source coverage
  unless the source itself is regionally mapped and active.

## 2026-06-02 — Period Source + Image Capture Priority v1

Action:

- Added `scripts/audit_period_source_image_priority_v1.py` to combine
  per-period source breadth and weighted image coverage into a ranked next
  capture plan.
- The period source metric counts active sources inside each period and sums
  their region weights. It does not count candidate sources.
- The priority formula is:
  `period_weight × (0.55 × source_gap + 0.45 × image_gap)`.

Current ranked result:

- `1930_1970`: priority `0.2185`; source coverage `20.64%`; weighted image
  coverage `55.36%`.
- `1970_2000`: priority `0.1482`; source coverage `21.10%`; weighted image
  coverage `61.43%`.
- `2000_2026`: priority `0.1344`; source coverage `36.80%`; weighted image
  coverage `54.91%`.
- `pre_1930`: priority `0.0804`; source coverage `21.33%`; weighted image
  coverage `73.17%`.

Decision:

- Next broad capture should prioritize `1930_1970`.
- `1970_2000` needs source breadth before more records from existing sources.
- `2000_2026` needs image quality and source-specific adapters for independent
  or local post-digital sources.
- `pre_1930` should pause broad capture and only receive targeted non-West or
  local-source work plus duplicate-image review.

## 2026-06-02 — Source Coverage Gap Capture 1931-2026

Action:

- Pushed the current `main` snapshot to GitHub before new capture work.
- Added `scripts/run_source_coverage_gap_capture_1931_2026.py`.
- Added the new batch to `scripts/rebuild_public_surfaces_from_records.py`.
- Added source-region overrides for NDL, UCT, Pretoria, Stellenbosch, Wits,
  AUB, and the National Repository of Nigeria so coverage metrics do not file
  these sources as unmapped.

Capture result:

- Captured records: 25
- Distinct captured sources in this batch: 6
- Image states: `IMG02: 6`, `IMG04: 19`
- Period distribution: `1931_1970: 1`, `1971_2000: 2`, `2001_2026: 22`
- Sources: University of Cape Town Digital Collections, University of Pretoria
  Research Repository, Stellenbosch University Scholar, Wits University
  WiredSpace, American University of Beirut ScholarWorks, National Repository
  of Nigeria.

Post-rebuild metrics:

- Public surfaces: 1356
- Source-visible image readiness: 90.56%
- Weighted publication image score: 61.54%
- Active captured sources: 43
- Source coverage rate v1: 6.70%
- Strict distribution-adjusted diagnostic: 1.17%
- Updated period priority:
  `1930_1970` remains highest priority at `0.2148`; `1970_2000` is `0.1448`;
  `2000_2026` is `0.1213`; `pre_1930` is `0.0804`.

Constraint:

- Do not promote broad search-bounded records as dated records unless an
  item-level date exists. NDL SRU returned many 1931-1970 search-bounded hits,
  but several records lacked publishable item dates, so they stayed in summary
  rather than becoming public leaves.
- DSpace records from regional universities and repositories are usually
  text/context evidence. They should render as text sheets, appendix evidence,
  or grouped supporting leaves, not as thin main sheets.
- Adding non-mainstream sources may lower image coverage in the short term.
  That decrease is acceptable when it reflects honest text/source coverage
  rather than inflated IMG states.

## 2026-06-02 — Edge Source Registry Context + South Asia Probe

Action:

- Added `scripts/run_edge_source_registry_context_capture_1931_2026.py`.
- Added `scripts/probe_south_asia_sources_v1.py`.
- Promoted reachable edge-source probes into source-registry context records
  rather than object-level sheets.
- Added the source-registry context batch to
  `scripts/rebuild_public_surfaces_from_records.py`.
- Added a hard disposition guard in `scripts/run_midcentury_capture_1930_1970.py`
  so `source registry/context record` rows cannot become `main_sheet`.

Capture result:

- Edge source-registry context records: 61
- Distinct sources in the batch: 61
- Image states: `IMG02: 24`, `IMG04: 37`
- Regional spread: Africa 2, East Asia 20, Eastern Europe 2, Latin America 4,
  Middle East 2, South Asia 6, Southeast Asia 25.
- South Asia probe: 9 P1/P2 sources probed, 6 reachable.
- South Asia active source entries added: India Design Council, Madan Puraskar
  Pustakalaya, NID, National Digital Library of India, National Library of
  India, Roja Muthiah Research Library.
- South Asia sources still needing fallback/manual strategy: South Asia Open
  Archives returned 403; Tasveer Ghar reset the connection; Panjab Digital
  Library SSL handshake timed out.

Post-rebuild metrics:

- Public surfaces: 1417
- New source-registry surfaces: 61
- New source-registry publication role: all `support_packet_appendix_text`
- Source-visible image readiness: 88.29%
- Weighted publication image score: 59.78%
- Active captured sources: 104
- Source coverage rate v1: 22.59%
- South Asia region balance: 59.55% after previously being 0%.

Constraint:

- Source-context records are evidence for source breadth and future adapter
  planning. They should render as source dossiers, support packets, reading
  notes, cards, or bookmarks, not as canonical main sheets.
- Broad source-scope dates such as `modern-present` or `pre-WWII-present` must
  not become public object dates.
- IMG02 on a source-context record means source-hosted or metadata-discovered
  image evidence only. It is not an open-image claim and local copying remains
  false by default.
- Raw probe/capture files must be redacted for token-like strings before git
  staging. This pass scanned new raw/source files for common API key and token
  patterns and found no matches.

## 2026-06-03 — Asset Grammar + Readability Gate

Action:

- Added `docs/frontend/ASSET_GRAMMAR_AND_A11Y_CONTRACT_v0.md`.
- Added the frontend `asset:a11y-check` script and generated-report ignore
  rule.
- Added global asset readability constraints to `frontend/src/app/globals.css`:
  body text `>= 0.72rem`, metadata `>= 0.62rem`, micro labels `>= 0.56rem`,
  with shorter line-length rules for cards, slips, bookmarks, and prose pages.
- Updated asset preview constraints so screenshot review now includes the
  readability/accessibility gate.

Verification:

- `npm run build` passed.
- `BASE_URL=http://127.0.0.1:3001 npm run asset:a11y-check` checked 21
  page/viewport states and returned `0 failed`, `0 warnings`, `0 errors`.

Constraint:

- Required archive evidence must remain legible even when a page uses dense
  ledger/specimen references. Text below `0.56rem` is decorative only and must
  be hidden from the accessibility tree or marked `data-decorative`.
- Asset DOM/keyboard reading order must preserve:
  title -> date/creator -> source -> image state -> summary -> metadata ->
  citation/action.
- Generated raw files and captured HTML must continue to be scanned/redacted
  before staging so token-like strings are not pushed into GitHub.

## 2026-06-03 — Text Enrichment Pass v1

Action:

- Updated `scripts/rebuild_public_surfaces_from_records.py` so public reading
  text is no longer generated from capture-log wording.
- Replaced repeated boilerplate such as `is indexed from`, `enters the
  archive`, `captured item metadata`, and duplicate `Folder placement` language
  with source-linked reading prose.
- Added sentence-boundary trimming, evidence-list cleanup, source-family
  context notes, and deterministic wording variants so sheets do not all read
  like the same registration form.
- Rebuilt all public static payloads:
  `generated/public_surfaces_v1.json`,
  `frontend/src/data/public_surface_mock_v0.json`,
  `frontend/public/data/public_surface_mock_v0.json`, and
  `data/public_surface_mock_v0.json`.

Post-rebuild metrics:

- Public surfaces: 1417
- Folders: 48
- Appendices exposed in payload: 578
- Bookmarks exposed in payload: 48
- `is indexed from`: 0
- `enters the archive`: 0
- duplicate `Folder placement`: 0
- old sparse-prose phrase: 0
- Reading text length: median 2355 chars; average 2412.2 chars; 8 surfaces
  under 1500 chars, mostly compound/grouped support records.
- Image states unchanged: `IMG00: 41`, `IMG01: 37`, `IMG02: 733`,
  `IMG03: 481`, `IMG04: 125`.

Verification:

- `npm run build` passed after regenerating the static payload.

Constraint:

- Text enrichment must remain source-derived or field-derived. It can clarify
  what a record contributes and how to read it, but it must not invent
  design-historical claims not supported by source metadata, cited prose,
  OCR/excerpt text, or an explicit project methodology note.
- Sparse source records should state that the source does not provide extended
  descriptive prose rather than pretending to offer a complete interpretation.
- Grouped sheets are allowed to stay shorter when their function is to keep
  duplicate or weak item records together; they should be upgraded only after
  source-specific long-form evidence is captured.

## 2026-06-03 — Research Dossier Export Contract v0

Action:

- Added `researchDossiers` to the generated public payload.
- Added TypeScript interfaces and data helpers for research dossiers.
- Added `docs/system/RESEARCH_DOSSIER_EXPORT_MODEL_v0.md`.
- Rebuilt the static payload and verified the frontend build.

Decision:

- The archive is not a flat sheet browser. A research unit is a dossier:
  `main_sheet` -> `subsheet` -> `text_page` -> `appendix` -> `card` / `slip`
  -> `bookmark`.
- Folder views remain filters over records/dossiers. They do not own or clone
  dossier pages.
- PDF export should read dossier `pageSequence`, not the flat folder page
  sequence. Exported pages must carry archive marks, source links, image state,
  and rights/citation notes.

Generated data:

- `researchDossiers`: 1417
- `compound_or_series_cluster`: 21
- largest dossier: 33 pages
- anchor types: `main_sheet: 1179`, `subsheet: 224`, `card: 14`

Constraint:

- Do not infer dossier grouping from same folder, same country, same movement,
  date proximity, or visual resemblance alone.
- Multi-page research dossiers need linkage evidence: same source identifier,
  accession/call number, issue, campaign, publication series, object set,
  production pattern, manifestation relation, or explicit source relation.
- The current contract is conservative. Most records remain single-anchor
  dossiers until a linkage/grouping pass promotes them into larger research
  packets.

## 2026-06-03 — Reading Note / Bookmark Count Correction

Issue:

- The public payload exposed 48 `bookmarks` for 48 folders. This was a data
  contract error: folder-level reading notes had been serialized as bookmarks.
- This made the archive appear to have one fallback bookmark per folder, even
  though bookmarks should be rare fallback leaves, not normal folder notes.

Action:

- Changed `attach_structural_collections()` so each folder emits a
  `readingNotes` record instead of a bookmark record.
- Kept `bookmarks` as a separate collection for true low-information fallback
  leaves only. The current payload has no true bookmark candidates.
- Added surface-level reading-note candidates for long main-sheet records, so
  reading notes are not limited to folder-level notes.
- Added TypeScript support for `readingNotes` and archive-data helpers for
  reading-note lookup.
- Updated `scripts/audit_public_surface_integrity.py` to flag suspicious
  bookmark counts when bookmarks look folder-like, and to warn when reading
  notes are folder-only.
- Rebuilt all public static payloads and verified the frontend build.

Post-rebuild metrics:

- Folders: 48
- Reading notes: 119
  - Folder reading notes: 48
  - Surface reading notes: 71
- Bookmarks: 0
- Appendices: 578
- Research dossiers: 1417
- `npm run build` passed.

Constraint:

- Reading notes are interpretive/register leaves. They may appear once per
  folder and may also attach to long main-sheet/dossier records.
- `readingNotes == folders` should be treated as a coverage smell, because it
  means no long sheet or dossier has received a reading note.
- Bookmarks are sparse fallback leaves for very weak fragments, method markers,
  or tiny research hints. They must never be generated one-per-folder.
- A future payload with `bookmarks >= folders` should be treated as a likely
  taxonomy error unless there is a specific documented exception.

## 2026-06-03 — Local WebLLM / RAG Feasibility v0

Action:

- Added `docs/system/LOCAL_WEBLLM_RAG_FEASIBILITY_v0.md`.
- Reviewed three browser-local/lightweight options for archive assistant use:
  MLC WebLLM, Transformers.js, and Wllama.
- Added sub-1B Qwen candidates to the horizontal generation-model comparison,
  including Qwen2.5-0.5B-Instruct and Qwen3.5-0.8B.

Decision:

- The archive assistant should be a local retrieval assistant, not a general
  chatbot.
- Recommended v0 stack: Transformers.js for local embeddings/retrieval,
  static build-time RAG chunks, and Qwen3.5-0.8B as the first multimodal
  local-generation target.
- Because the archive is visual, the first assistant prototype should be
  multimodal rather than text-only.

Follow-up decision:

- Qwen3.5-0.8B is no longer a candidate among several small models; it is the
  fixed first-version model.
- Text-only Qwen 0.5B/0.6B models and Wllama are not fallback generation paths
  for v0.
- Keyword/facet search remains a normal non-AI search interface, not an LLM
  fallback answer mode.
- The remaining implementation risk is runtime packaging and local browser
  execution, not model selection.

Constraint:

- The assistant may answer only from supplied archive chunks, methodology
  documents, source metadata, rights notes, and dossier structure.
- No remote LLM API calls.
- No live remote page fetching during a user query.
- No AI-generated content may become historical evidence.
- Model assets must be handled as documented local/static assets with cache and
  checksum policy, not accidentally committed as opaque project clutter.

Runtime probe:

- Added `frontend/scripts/probe-qwen35-rag-policy.js` and
  `frontend/scripts/probe-qwen35-runtime.mjs`.
- Installed `@huggingface/transformers` in the frontend workspace for the local
  runtime probe.
- The raw `Qwen/Qwen3.5-0.8B` Hugging Face repository failed as a direct
  Transformers.js runtime target because the expected quantized ONNX files were
  not present there.
- The project should keep `Qwen/Qwen3.5-0.8B` as the model identity but use
  `onnx-community/Qwen3.5-0.8B-ONNX` as the browser/ONNX runtime artifact.
- The first ONNX artifact load exposed a Node external-data path issue. The
  probe now passes external data explicitly and loads
  `Qwen3_5ForConditionalGeneration` successfully.
- Successful local probe: import 198 ms, model load 7911 ms after runtime files
  were cached locally.
- Image-policy probe currently permits only 481 `IMG03/open_image_frame`
  records to pass image pixels into the local multimodal model. IMG00, IMG01,
  IMG02, and IMG04 are withheld from model-image context under the conservative
  v0 rule.
- Added `.model-cache/` to `.gitignore` so downloaded model files stay local.

Generation probe:

- Added `frontend/scripts/probe-qwen35-generation.mjs`.
- The model generated a constrained answer from a supplied archive surface
  context, but generation remains slow in the local Node/CPU probe:
  cached load 3852 ms, evidence answer 48475 ms.
- The first no-evidence test showed a serious guardrail issue: prompt
  instructions alone did not prevent hallucination.
- The probe was corrected to enforce a retrieval gate before model invocation.
  If no cited chunk is available, the assistant returns an archive-limited
  refusal and does not call the model.
- This confirms the implementation rule: Qwen3.5-0.8B is a lazy synthesis layer
  after retrieval, not an instant search replacement and not a source of
  independent historical claims.

Search-assistant timing probe:

- User target: reduce perceived assistant latency from roughly 48 seconds to
  about 10-15 seconds.
- Compression attempt 1 shortened the record context from long archive prose to
  a compact record slip. Timing improved but answers were truncated or useless:
  one search answer returned only `Source:`.
- Compression attempt 2 switched to the tokenizer chat template and decoded
  only newly generated tokens. This removed prompt echoing and reduced hidden
  reasoning leakage, but timing was still around 17-20 seconds for short
  answers.
- Compression attempt 3 used a micro-answer contract. It reached the target
  range for one search pass, but the text was still prone to truncation when
  `max_new_tokens` was too low.
- Final hybrid probe reached the target envelope:
  - cached load: 4107 ms;
  - record micro-note: 11846 ms;
  - search micro-note: 13968 ms;
  - no-evidence refusal: 0 ms because the retrieval gate blocks model
    invocation.

Failure log:

- A model-only answer is not reliable enough for archive facts.
- Prompt-only refusal is unsafe; it hallucinated when no context was supplied.
- Over-compressing generation creates incomplete prose.
- The model should not be responsible for full search result text, source
  links, dates, or verification instructions.

Implementation constraint:

- Ordinary search must remain deterministic and DB-backed.
- Search results may include a local Qwen micro-note only as an optional reading
  angle after the DB has already returned exact records and citations.
- The UI must hide or retry incomplete micro-notes; it must never replace the
  deterministic title/date/source rows with generated text.
- Qwen output must not write back to the database, alter records, fetch remote
  pages, or read source images unless the image state explicitly permits local
  model context.
- A generated micro-note is interface assistance, not archive evidence.

## 2026-06-05 — Rights-first crawler decision engine

Added a conservative rights-first crawler policy after reviewing proposed
advanced crawler ideas for IIIF, JSON-LD, headless browser parsing, visual
rights detection, ToS NLP parsing, decentralized provenance checks, and
similar-open-image discovery.

New project constraints:

- crawler image state must be decided before any image pixel is stored;
- only explicit item-level open rights evidence may upgrade a record to
  `IMG03`;
- IIIF manifests, source viewers, OpenGraph images, JSON-LD image objects, and
  JavaScript-rendered image URLs are discovery/display-route evidence, not
  automatic reuse permission;
- visual copyright/CC-logo detection, LLM ToS summaries, IPFS/Wayback traces,
  and pHash/CLIP similarity can create review signals or downgrade risk, but
  cannot automatically upgrade an image to `IMG03`;
- `IMG04` remains a no-image-frame state for text, authority, appendix,
  bibliography, source, or context-led pages. Parser failure for a visual
  object must stay diagnosable and should not masquerade as `IMG04`;
- all raw capture payloads still need secret-pattern auditing before GitHub
  push because third-party public HTML can contain token-like strings.

Implemented:

- `scripts/rights_decision_engine.py` as a pure Python decision helper for new
  crawlers;
- `docs/capture/RIGHTS_FIRST_CRAWLER_DECISION_ENGINE_v0.md` as the production
  policy for using advanced crawler signals without violating rights logic;
- `scripts/audit_img_state_contract.py` to separate data-layer IMG contract
  problems from frontend template/CSS rendering problems.

Follow-up tightening:

- `scripts/source_policy_registry.py` now separates reviewed source-policy
  evidence from broad domain allowlists. A crawler must not treat platform
  names such as Wikimedia Commons, Flickr, Unsplash, Pinterest, or a museum
  domain as automatic thumbnail permission.
- `scripts/iiif_discovery.py` provides deterministic IIIF manifest discovery
  for source-hosted display routes. A discovered manifest may support `IMG02`,
  but it is not local reuse permission.
- `scripts/discovery_signal_policy.py` defines non-upgrading discovery-signal
  categories for visual, ToS, Wayback/IPFS, and similar-open-image hints.
- `source_terms_allow_thumbnail=true` is ignored unless paired with a reviewed
  source policy. `manual_review` remains a review-needed state, not approval.

## 2026-06-05 — Global edge discovery registry v1

Converted a broad set of proposed global archive-discovery strategies into a
conservative candidate-source registry rather than a crawler that immediately
downloads images or mints publication records.

Generated:

- `scripts/generate_global_edge_discovery_registry_v1.py`
- `data/global_edge_discovery_candidates_v1.csv`
- `data/global_edge_discovery_metrics_v1.csv`
- `docs/capture/GLOBAL_EDGE_DISCOVERY_STRATEGY_v1.md`

Test calculation:

- 81 candidate sources were normalized.
- 79/81 candidates, or 97.5%, sit outside the dominant United States and
  Western European source pattern.
- Macro-region distribution: Asia 26, Global 19, Latin America 10, Africa 8,
  Middle East and North Africa 8, Europe 5, Oceania 4, North America 1.
- Priority distribution: P1 46, P2 25, P3 9, P4 1.
- Period support: 1830-1930 has 56 candidate source routes; 1931-1970 has 66;
  1971-2000 has 69; 2001-2026 has 70.

Implementation constraints:

- OAI-PMH, IIIF, museum/library APIs, HTML metadata, WordPress, CollectiveAccess,
  newspaper/OCR, and manual source-registry paths are adapter families, not
  rights clearance.
- Social platforms, portfolio platforms, Pinterest boards, Reddit threads, and
  repost networks are discovery leads only. They must not write images, infer
  open licenses, or mint final object sheets without source review.
- Proxy/geobypass and authenticated database scraping remain outside production
  automation. They may be documented as manual or institutionally authorized
  research routes, but not embedded as automatic capture behavior.
- Impact-score ideas may rank review priority. They cannot decide scholarly
  inclusion, source authority, or image state.
- LLM ToS parsing, visual copyright detection, similar-image search, and
  Archive.org/IPFS hints remain review signals only. They cannot upgrade
  `IMG00` to `IMG01` or `IMG03`.

Next route:

- Promote reviewed P1 candidates into `source_prospect_registry_v2` and adapter
  queues only after source terms, access route, field provenance, and citation
  expectations are clear.
- Prioritize non-US/non-Western-European source families with deterministic
  metadata routes before exploratory platform crawling.

## 2026-06-05 — Source candidate probe v1 and contemporary scan

Ran the first rights-safe source-level probe over the global edge discovery
registry, then generated and probed a separate 1990-2026 contemporary /
independent-source candidate set. This round is source discovery and adapter
planning only; it does not mint publication records, store source images, or
upgrade any image state from heuristic evidence.

Generated:

- `scripts/probe_global_edge_discovery_candidates_v1.py`
- `scripts/generate_contemporary_source_scan_1990_2026_v1.py`
- `data/global_edge_discovery_probe_v1.csv`
- `data/global_edge_discovery_probe_metrics_v1.csv`
- `docs/capture/GLOBAL_EDGE_DISCOVERY_PROBE_v1.md`
- `data/contemporary_source_scan_candidates_1990_2026_v1.csv`
- `data/contemporary_source_scan_probe_1990_2026_v1.csv`
- `data/contemporary_source_scan_metrics_1990_2026_v1.csv`
- `docs/capture/CONTEMPORARY_SOURCE_SCAN_1990_2026_v1.md`

Global edge probe test calculation:

- 81 candidate sources were probed at source/page level.
- Probe status: 60 `ok`, 11 `failed`, 10 `http_error`.
- Review priority: 24 `P1 adapter build`, 20 `P1 text/source enrichment`, 21
  `P2 retry/manual verification`, 11 `P2 discovery lead queue`, and 5 `P2
  manual source review`.
- Detected protocol families: IIIF 18, RSS/Atom 15, Static JS App 14, JSON-LD
  13, WordPress REST 11, PDF 5, GraphQL 4, ArchiveSpace/EAD 3, OAI-PMH 1, and
  Kramerius 1.

Contemporary 1990-2026 scan test calculation:

- 65 contemporary, platform, independent, regional, and edge-source candidates
  were generated and probed.
- Probe status: 50 `ok`, 11 `failed`, 4 `http_error`.
- Macro-region distribution: Global 13, East Asia 12, Southeast Asia 10, Latin
  America 8, South Asia 5, MENA 5, Africa 5, Oceania 3, Eastern Europe 2,
  Europe 1, North America 1.
- Review priority: 22 `P1 adapter build`, 18 `P1 text/source enrichment`, 15
  `P2 retry/manual verification`, 8 `P2 discovery lead queue`, and 2 `P2
  manual source review`.
- Detected protocol families: Static JS App 17, JSON-LD 15, RSS/Atom 14,
  WordPress REST 14, IIIF 13, PDF 5, GraphQL 3, ArchiveSpace/EAD 2, and
  OAI-PMH 1.

Important failure correction:

- The first contemporary probe run was invalid because `raw_dir` was treated as
  a relative path while the script tried to compute a workspace-relative report
  path. That made the run look like an all-source failure even though the issue
  was script-local path handling.
- The probe script now resolves input, output, metrics, report, and raw
  evidence directories against the workspace root before writing files.
- The corrected contemporary probe was rerun with external network access and
  produced the valid metrics above.

Constraints preserved:

- Probe output stores page/source text evidence and headers only. It does not
  download image binaries.
- Detected IIIF, JSON-LD, WordPress, RSS, GraphQL, static app markers, PDFs, or
  platform traces are adapter hints, not rights clearance.
- `IMG03` remains available only when authoritative item-level source metadata
  provides open/reusable evidence. Discovery, visual similarity, ToS parsing,
  social platform metadata, and LLM notes cannot upgrade an item to `IMG01` or
  `IMG03`.
- Behance, Pinterest, Cargo, Tumblr, Are.na, social media references, and
  repost networks remain discovery queues unless they resolve to a reviewed
  original source record.
- Impact or source-priority scoring remains an internal triage signal only. It
  cannot decide scholarly authority, public inclusion, authorship, or rights.

Next route:

- Build protocol-family adapters before single-site crawlers: WordPress/REST,
  JSON-LD, RSS/Atom, IIIF, OAI-PMH, PDF text/link extraction, and cautious
  static/headless metadata probing.
- Promote P1 contemporary candidates first where source text, source terms, and
  stable records are available: Another Graphic, Design Reviewed, Letterform
  Archive Blog, Fonts In Use, JAGDA, Tokyo TDC, Tokyo ADC, Ginza Graphic
  Gallery, ddd Gallery, Korea Design DB, NLB/BiblioAsia, Roots.sg, Malaysian
  Design Archive, Grafis Nusantara, Arabic Design Archive, Arab Image
  Foundation, African Activist Archive, SAHA, Fundación IDA, Diseño Nacional,
  Gráfica Latina, and La Patria.
- Retry or replace sources with DNS, SSL, 403, 429, or timeout failures through
  alternate endpoints or manual source-registry records rather than treating
  them as absent.

## 2026-06-05 — Contemporary source scan v2

Continued the rights-aware 1990-2026 source discovery pass by repairing and
running the v2 candidate generator, then probing the expanded candidate set at
source/page level only. This round generated source leads, protocol signals,
adapter hints, and review priorities. It did not download image binaries, create
public archive records, or upgrade rights/image state from heuristic evidence.

Generated:

- `scripts/generate_contemporary_source_scan_1990_2026_v2.py`
- `data/contemporary_source_scan_candidates_1990_2026_v2.csv`
- `data/contemporary_source_scan_probe_1990_2026_v2.csv`
- `data/contemporary_source_scan_metrics_1990_2026_v2.csv`
- `docs/capture/CONTEMPORARY_SOURCE_SCAN_1990_2026_v2.md`

Generator and probe rules checked:

- The v2 generator is source discovery only. It writes candidate source rows and
  does not fetch pages, download images, or mint item records.
- Priority and impact-like language remains internal triage only. It is not a
  scholarly authority, source partnership, inclusion, authorship, or rights
  decision.
- `IMG01` and `IMG03` cannot be assigned by heuristics, LLM notes, ToS parsing,
  social/platform signals, OpenGraph images, JSON-LD images, or IIIF/viewer
  availability.
- `IMG04` remains a true text/source-registry or no-image-frame state; it is not
  a parser-failure fallback or an automatic upgrade from weak signals.

V2 candidate registry:

- 148 candidate sources after URL dedupe.
- Candidate triage distribution: 68 `P0`, 63 `P1`, 15 `P2`, and 2 `P3`.
- Macro-region distribution: Global 33, East Asia 27, Southeast Asia 17, MENA
  12, Africa 12, South Asia 11, Latin America / Caribbean 9, Latin America 8,
  Eastern Europe / Central Asia 6, Oceania / Indigenous 6, Oceania 3, Eastern
  Europe 2, Europe 1, and North America 1.

V2 source-only probe:

- 148 candidate sources were probed with the existing source-level probe script.
- Probe status: 111 `ok`, 23 `failed`, and 14 `http_error`.
- Next capture priority: 52 `P1 text/source enrichment`, 45 `P1 adapter build`,
  37 `P2 retry/manual verification`, 8 `P2 discovery lead queue`, and 6 `P2
  manual source review`.
- Detected protocol families: RSS/Atom 37, WordPress REST 35, JSON-LD 31,
  Static JS App 28, IIIF 25, PDF 11, GraphQL 3, ArchiveSpace/EAD 2, OAI-PMH 2,
  DSpace 2, Omeka 1, Kramerius 1, and CONTENTdm 1.

Best next capture directions:

- Build protocol-family adapters before single-source crawlers: WordPress/REST,
  RSS/Atom, JSON-LD, IIIF/viewer metadata, static/headless metadata, and PDF
  text/link extraction.
- Prioritize reachable non-Western and underrepresented P1 rows where source
  text and stable records are already visible: East Asia, Southeast Asia, MENA,
  Africa, South Asia, Latin America, and Oceania/Indigenous sources.
- Retry or replace failed DNS, SSL, 403, 404, 429, and timeout rows via
  alternate endpoints or manual source-registry records rather than treating the
  sources as absent.
- Keep social/platform rows as discovery leads only until they resolve to
  original, stable, rights-reviewed source records.

Safety scan:

- Scanned the generated v2 script, candidate CSV, probe CSV, metrics CSV, report,
  and `PROJECT_LOG.md` for `API_KEY`, token, password, secret, cookie, session,
  bearer, `/Users/`, and `.env` patterns.
- No commit-bound file contains a real secret or local `/Users/` path from this
  run. The hits in commit-bound files were policy/documentation words such as
  `token` in historical log text or `image possession` notes.
- The raw probe directory contained third-party page text with token-like,
  password, cookie, and session UI/config strings, so it was removed and is not
  part of the commit.

## 2026-06-05 — Contemporary source follow-up v2 step 1: P1 protocol queue

Started the v2 follow-up sequence by deriving a P1 protocol queue from the
existing candidate/probe CSVs. This step reads only committed CSV metadata and
does not fetch pages, read raw probe bodies, download images, or change
rights/image states.

Generated:

- `scripts/generate_contemporary_source_followup_1990_2026_v2.py`
- `data/contemporary_source_p1_protocol_queue_1990_2026_v2.csv`

Step 1 metrics:

- 97 P1 rows were queued for adapter or source-text follow-up.
- Protocol lanes: WordPress REST / HTML 30, IIIF/source-viewer metadata 19,
  Static JS/headless metadata 15, RSS/Atom source feed 13, Search
  interface/manual source registry 8, JSON-LD page metadata 5, PDF text/link
  extraction 2, HTML/manual source registry 2, CONTENTdm source metadata 1,
  Kramerius / IIIF source metadata 1, and Omeka source metadata 1.
- Regional spread: Global 24, East Asia 19, Africa 8, Southeast Asia 8, MENA 6,
  South Asia 6, Latin America 6, Eastern Europe / Central Asia 6, Oceania /
  Indigenous 5, Latin America / Caribbean 4, Oceania 2, Europe 1, North America
  1, and Eastern Europe 1.

Boundary:

- This queue is an implementation queue for metadata/source-link adapters.
- It explicitly carries `do_not_capture_images` style boundaries and keeps
  `IMG01`/`IMG03` behind authoritative item-level rights evidence only.

## 2026-06-05 — Contemporary source follow-up v2 step 2: regional priorities

Completed the regional coverage priority table from the same v2 candidate/probe
CSV inputs. This is a planning score for where to spend adapter and manual
review effort; it is not a public coverage claim.

Generated:

- `data/contemporary_source_region_priorities_1990_2026_v2.csv`

Step 2 metrics:

- 14 macro-region rows were ranked.
- Top priority rows by score: East Asia 104, Global 85, Southeast Asia 84,
  Africa 81, South Asia 79, MENA 78, Latin America / Caribbean 66, and Latin
  America 60.
- East Asia has 27 candidates, 19 reachable rows, 6 `P1 adapter build`, 13 `P1
  text/source enrichment`, and 8 retry/manual rows.
- Southeast Asia, Africa, South Asia, and MENA remain high-value because they
  combine underrepresented coverage, P0/P1 candidates, reachable text/protocol
  rows, and failed-source endpoint work.
- Global ranks high for reusable protocol adapter value, not because it should
  dominate historical coverage or public narrative.

Boundary:

- Regional scores rank internal work. They do not decide inclusion, authorship,
  authority, rights, or image state.

## 2026-06-05 — Contemporary source follow-up v2 step 3: retry registry

Completed the failed-source retry and alternate-endpoint registry. This table
turns failed, HTTP-error, and `P2 retry/manual verification` probe rows into
specific follow-up routes without treating temporary network/access failures as
source absence.

Generated:

- `data/contemporary_source_retry_registry_1990_2026_v2.csv`

Step 3 metrics:

- 37 retry/manual verification rows were queued.
- Failure families: DNS/domain 11, forbidden 403 9, SSL certificate 6,
  connection reset 3, timeout 3, not found 404 3, auth required 401 1, and rate
  limited 429 1.
- Regional concentration: East Asia 8, Southeast Asia 6, South Asia 5, Latin
  America / Caribbean 5, MENA 4, Global 4, Africa 3, and Latin America 2.

Retry rules:

- 403, 401, and 429 rows are manual source-registry or documented endpoint
  review tasks. They must not be bypassed.
- DNS/domain and 404 rows need canonical-domain, successor-page, source-root, or
  institutional endpoint checks.
- SSL and timeout rows need manual browser/canonical-domain confirmation before
  another automated probe.
- All retry rows keep the same image boundary: metadata, source links,
  descriptions, and rights evidence only; no image binary capture.

## 2026-06-05 — Contemporary source follow-up v2 step 4: adapter queue

Completed the consolidated adapter queue and follow-up report. This combines the
P1 protocol queue, region-priority logic, and retry/manual review routes into a
single execution table for the next implementation phase.

Generated:

- `data/contemporary_source_adapter_queue_1990_2026_v2.csv`
- `docs/capture/CONTEMPORARY_SOURCE_SCAN_FOLLOWUP_1990_2026_v2.md`

Step 4 metrics:

- 148 adapter queue rows were written.
- Queue priority distribution: 52 `P1B_text_source_enrichment`, 45
  `P1A_protocol_adapter`, 37 `P2_retry_or_alternate_endpoint`, 8
  `P2_discovery_source_resolution`, and 6 `P2_manual_source_review`.
- Queue status distribution: 97 `ready` rows and 51 `review_first` rows.
- The follow-up report records the implementation order:
  WordPress/RSS/JSON-LD source adapters first; IIIF/CONTENTdm/Kramerius/DSpace
  metadata adapters second; headless/static metadata probes third; retry rows
  through canonical endpoint checks or manual source-registry notes fourth.

Boundary:

- Every adapter queue row carries `do_not_capture_images=true`.
- The queue is for source metadata, canonical links, descriptions, tags,
  citations, and rights text. It is not an image mirror plan.
- `IMG01` and `IMG03` remain gated by authoritative item-level rights evidence.

Verification:

- `python3 -m py_compile` passed for the follow-up generator, v2 scan generator,
  and source probe script.
- `git diff --check` passed.
- Safety scan checked the follow-up generator, four new follow-up CSVs, the
  follow-up report, and `PROJECT_LOG.md` for `API_KEY`, token, password, secret,
  cookie, session, bearer, `/Users/`, and `.env` patterns.
- No real secret, credential, cookie/session payload, local `/Users/` path, or
  `.env` reference was found in commit-bound files. The remaining hits are
  policy text or the substring `session` inside `possession`.
- No v2 raw probe directory is present for this follow-up pass.

## 2026-06-05 — README licensing and non-mainstream regional capture v1

Completed the README licensing update and a source-only capture pass focused on
underrepresented/non-mainstream 1990-2026 regional coverage.

Step 1 - repository licensing:

- Added `LICENSE` with the MIT License for source code.
- Added `FRONTEND_DESIGN_LICENSE.md` to reserve the original frontend visual
  design, archive-box interface concept, layout language, visual identity,
  design-specific assets, prototype trade dress, and screenshots.
- Updated `README.md` to explain the layered reuse boundary: MIT applies to
  source code only; frontend visual design is under the personal frontend
  design license; project data/docs remain research-prototype materials unless
  stated otherwise; third-party source materials remain under their source
  owners' rights and terms.

Step 2 - source list and content capture:

- Added `scripts/run_nonmainstream_region_content_capture_1990_2026.py`.
- Targeted 10 sources: DesignSingapore Council, Malaysian Design Archive,
  Grafis Nusantara, 29LT, Barjeel Art Foundation, African Digital Heritage,
  GALA Queer Archive, Indian Memory Project, MAP Academy, and Diseño Nacional.
- Generated `data/nonmainstream_region_capture_targets_1990_2026_v1.csv`.
- Generated `data/capture_batch_nonmainstream_region_1990_2026_records.csv`
  with 21 candidate records from 5 captured sources.
- Generated `data/capture_batch_nonmainstream_region_1990_2026_source_summary.csv`.
- Generated `data/nonmainstream_region_impact_ratings_1990_2026_v1.csv`.
- Generated `docs/capture/NONMAINSTREAM_REGION_CAPTURE_1990_2026_v1.md`.

Capture metrics:

- Target source coverage: 5 of 10 sources.
- Captured records: 21.
- Source summary: Malaysian Design Archive 5, Barjeel Art Foundation 4,
  African Digital Heritage 4, GALA Queer Archive 4, and Indian Memory Project 4.
- Targeted sources with no promoted records this pass: DesignSingapore Council,
  Grafis Nusantara, 29LT, MAP Academy, and Diseño Nacional.
- MAP Academy produced 4 endpoint failures; the other zero-record sources were
  reachable or non-promoted for this batch rather than treated as absent.
- Macro-region captured-source distribution: Africa 2, Southeast Asia 1, MENA
  1, and South Asia 1.
- Image-state distribution: `IMG02` 15 and `IMG04` 6.
- Impact-factor distribution: A 15 and B 6.

Boundary:

- This pass did not download image binaries.
- This pass did not write raw third-party payloads.
- `IMG02` rows point to source-hosted image routes only and still require
  item-level rights review.
- `IMG04` rows are real no-image/text records, not parser failures.
- Impact ratings are internal triage only and do not decide public authority,
  inclusion, authorship, or rights.

Step 3 - database/public surface integration:

- Updated `scripts/rebuild_public_surfaces_from_records.py` so the new
  non-mainstream regional record CSV feeds the generated public-surface payloads.
- Rebuilt generated public payloads after capture.
- Rebuild output: 1,558 source rows, 1,438 public surfaces, 48 folders.
- Rebuilt public-surface image states: `IMG00` 41, `IMG01` 37, `IMG02` 748,
  `IMG03` 481, and `IMG04` 131.
- Rebuilt source-visible image readiness: 1,266 of 1,438 surfaces, 88.04%.
- Rebuilt weighted publication image score: 855.4 of 1,438, 59.49%.

Step 4 - health and coverage checks:

- Added `scripts/audit_nonmainstream_region_capture_health_v1.py`.
- Generated `data/nonmainstream_region_capture_health_v1.csv`.
- Generated `docs/capture/NONMAINSTREAM_REGION_CAPTURE_HEALTH_v1.md`.
- Non-mainstream regional health metrics: target source coverage 50.00%,
  record health 100.00%, IMG/source-visible rate 71.43%, rights-review required
  rate 100.00%, impact ratings A 15 and B 6.
- Ran `scripts/audit_source_coverage_rate_v1.py`: active source count 109,
  candidate source count 298, source pool rate 52.42%, region weighted balance
  rate 35.85%, time weighted balance rate 46.00%, source coverage rate v1
  24.12%, and strict distribution-adjusted source coverage rate 8.64%.
- Ran `scripts/audit_layered_image_source_metrics_v1.py`: 1,631 records,
  source-visible rate 89.64%, publication-grade rate 83.20%, weighted
  publication rate 58.77%, open image rate 9.99%, rights-labeled rate 100.00%,
  and unclear image-state rate 0.25%.
- Ran `scripts/audit_period_source_image_priority_v1.py`: highest priority
  periods remain 1930-1970, 2000-2026, 1970-2000, and pre-1930 in that order.
- Ran `scripts/audit_img_state_contract.py`: passed after rebuild.
- Ran `scripts/audit_image_release_gate.py`: executed successfully but the
  release gate remains unmet, as expected for the current prototype. Current
  public-surface source-visible coverage is 88.04% and weighted publication
  coverage is 59.49% against the 95% minimum launch gate.
- Ran `scripts/audit_public_surface_integrity.py`: executed successfully with a
  warning that 12 surfaces share 6 exact image URLs. This is a warning to review
  duplicate source-hosted image references, not evidence of local image copying.

Next capture directions:

- Highest-value next automated pass: WordPress/RSS/JSON-LD source adapters for
  reachable Southeast Asia, Africa, South Asia, MENA, and Latin America sources.
- Highest-value manual/retry pass: MAP Academy endpoint review, then 403/401/429
  rows from the v2 retry registry without bypassing source restrictions.
- Highest-value rights/IMG pass: review `IMG02` source-hosted routes for item
  rights evidence while keeping `IMG01`/`IMG03` upgrades behind authoritative
  page-level terms only.
- Data cleanup to consider later: normalize the Malaysia/Malaysian Design
  Archive source label across older and newer batches.

Verification:

- `python3 -m py_compile` passed for the new capture/audit scripts, the public
  surface rebuild script, and the relevant health/coverage/image audit scripts.
- `git diff --check` passed.
- `npm run build` passed in `frontend/`, generating 1,514 static pages.
- Safety scans were run against the intended commit-bound files for credential
  and local-path patterns. The broad keyword scan found expected policy words,
  historical log text, and public content titles such as "Secret" or "Session".
  The stricter credential-shape scan found no real credentials, bearer values,
  cookie/session assignments, API key assignments, local user paths, or env-file
  references in the intended commit-bound files.
- Pre-existing raw capture leftovers from other worktrees/windows remain
  uncommitted and are not part of this batch.

## 2026-06-05 — Non-mainstream low-coverage source expansion v3

Completed a long source-discovery/probe pass to expand underrepresented and
non-mainstream regional source coverage. This round follows the corrected goal:
add 200+ new sources on top of the existing 81-source global edge baseline, so
the combined candidate pool reaches roughly 281-300+ sources.

Step 1 - new source target generation:

- Added `scripts/generate_nonmainstream_low_coverage_source_targets_1990_2026_v3.py`.
- Generated `data/nonmainstream_low_coverage_source_candidates_1990_2026_v3.csv`.
- Generated `data/nonmainstream_low_coverage_source_candidate_metrics_1990_2026_v3.csv`.
- Generated `docs/capture/NONMAINSTREAM_LOW_COVERAGE_SOURCE_TARGETS_1990_2026_v3.md`.
- The generator deduplicates candidate URL/name keys against the existing source
  registry, global edge candidates, contemporary v1/v2 scan candidates,
  non-mainstream v1 capture targets, source candidate registry, and source
  prospect registry.
- 69 existing source keys and 1 duplicate seed key were skipped.

Candidate metrics:

- New candidate sources: 228.
- Existing global edge baseline: 81.
- Baseline + new source-discovery pool: 309.
- Macro-region distribution: Africa 65, Latin America / Caribbean 58, MENA 22,
  South Asia 22, Eastern Europe / Caucasus 21, Southeast Asia 17, Oceania /
  Indigenous 13, Central Asia 8, and East Asia 2.
- Candidate source priority distribution: P1 135, P2 77, P0 16.
- Internal impact-rating distribution: B 138, A 81, C 9.

Boundary:

- This generator is source discovery only.
- It does not crawl sources, download images, write raw payloads, infer rights,
  or promote image states.
- Impact/source priority is internal triage only.

Step 2 - source-only probe:

- Ran `scripts/probe_global_edge_discovery_candidates_v1.py` against the 228
  v3 candidates.
- Generated `data/nonmainstream_low_coverage_source_probe_1990_2026_v3.csv`.
- Generated `data/nonmainstream_low_coverage_source_probe_metrics_1990_2026_v3.csv`.
- Generated `docs/capture/NONMAINSTREAM_LOW_COVERAGE_SOURCE_PROBE_1990_2026_v3.md`.
- Raw probe text was written only as temporary runtime evidence and then deleted
  because it is third-party page text with copyright, privacy, token-like
  string, and repository-size risk. It is not committed.

Probe metrics:

- Probe rows: 228.
- ok: 127.
- failed: 90.
- http_error: 11.
- Success target: 127 of required 120, met.
- Probe health / ok rate: 55.70%.
- P1 actionable rows: 119.
- Next capture priority distribution: P2 retry/manual verification 101, P1
  adapter build 68, P1 text/source enrichment 51, and P2 manual source review 8.
- Detected protocols: RSS/Atom 59, WordPress REST 55, JSON-LD 43, PDF 33,
  Static JS App 30, IIIF 10, DSpace 3, and CONTENTdm 1.
- Adapter hints: manual review or alternate endpoint 101, WordPress REST/HTML
  50, HTML metadata 19, JSON-LD 13, headless metadata 11, bibliographic 10,
  IIIF 9, RSS/Atom 5, PDF text/link 4, DSpace 3, and one each for manual source,
  CONTENTdm, and aggregator metadata.

Step 3 - health audit:

- Added `scripts/audit_nonmainstream_low_coverage_source_probe_v3.py`.
- Generated `data/nonmainstream_low_coverage_source_probe_health_1990_2026_v3.csv`.
- Generated `data/nonmainstream_low_coverage_source_probe_region_breakdown_1990_2026_v3.csv`.
- Generated `docs/capture/NONMAINSTREAM_LOW_COVERAGE_SOURCE_PROBE_HEALTH_1990_2026_v3.md`.

Health audit metrics:

- New-source target met: 228 / 220 = 103.64%.
- Success target met: 127 / 120 = 105.83%.
- P1 actionable rate: 119 / 228 = 52.19%.
- Source-visible protocol candidates: 13 / 228 = 5.70%. This counts protocol
  evidence such as IIIF, CONTENTdm, DSpace, or Kramerius only. It is not an image
  permission claim.
- IMG01/IMG03 automatic upgrades: 0.
- Candidate priority among ok rows: P1 79, P2 37, P0 11.
- Impact ratings among ok rows: B 73, A 51, C 3.

Macro-region success:

- Eastern Europe / Caucasus: 18 ok of 21, 85.71%.
- MENA: 14 ok of 22, 63.64%.
- Central Asia: 5 ok of 8, 62.50%.
- Latin America / Caribbean: 34 ok of 58, 58.62%.
- South Asia: 12 ok of 22, 54.55%.
- Southeast Asia: 9 ok of 17, 52.94%.
- East Asia: 1 ok of 2, 50.00%.
- Africa: 29 ok of 65, 44.62%.
- Oceania / Indigenous: 5 ok of 13, 38.46%.

Failure families:

- DNS/domain: 56.
- SSL/certificate: 18.
- Timeout: 13.
- HTTP 403: 8.
- HTTP 404: 2.
- Other failure: 2.
- HTTP 500: 1.
- Network unreachable: 1.

Best next capture directions:

- First adapter pass: the 119 P1 actionable ok rows, especially WordPress
  REST/RSS/JSON-LD/PDF rows with source text and stable institutional pages.
- Highest-yield macro-region pass: Eastern Europe / Caucasus, MENA, Central
  Asia, and Latin America / Caribbean because their ok rates were above 58%.
- Highest-coverage repair pass: Africa and Oceania / Indigenous need manual
  endpoint repair, canonical-domain checks, and SSL/browser confirmation before
  another automated pass.
- Highest source-visible protocol pass: IIIF/CONTENTdm/DSpace rows from
  Biblioteca Digital de Bogota, Biblioteca Nacional Jose Marti, Digital Library
  Iverieli, Polish Digital Libraries Federation, Moravian Gallery Brno, Estonian
  Museum of Applied Art and Design, and related Eastern Europe/Latin America
  rows.

Step 4 - project-level checks:

- Ran `scripts/audit_source_coverage_rate_v1.py`: source coverage rate v1 remains
  24.12%, strict distribution-adjusted source coverage rate remains 8.64%.
  This is expected because v3 expands the source candidate/probe pool, not the
  ingested item-record database.
- Ran `scripts/audit_layered_image_source_metrics_v1.py`: source-visible rate
  remains 89.64%, weighted publication rate 58.77%, open image rate 9.99%, and
  rights-labeled rate 100.00%.
- Ran `scripts/audit_period_source_image_priority_v1.py`: highest priority
  periods remain 1930-1970, 2000-2026, 1970-2000, and pre-1930.
- Ran `scripts/audit_img_state_contract.py`: passed.
- Ran `scripts/audit_image_release_gate.py`: executed and still fails the launch
  gate as expected. Public-surface source-visible coverage remains 88.04% and
  weighted publication coverage remains 59.49% against the 95% minimum launch
  gate.
- Ran `scripts/audit_public_surface_integrity.py`: executed and still warns that
  12 surfaces share 6 exact image URLs.

Verification:

- `python3 -m py_compile` passed for the new v3 generator/audit scripts plus
  the reused probe and project-level audit scripts.
- `git diff --check` passed.
- Safety scan covered the intended commit-bound files for credential and
  local-path patterns. The only hits were older project-log policy lines that
  spell out the scan terms (`API_KEY`, token, password, secret, cookie, session,
  bearer, `/Users/`, and `.env`). No real credential, bearer value,
  cookie/session assignment, API key assignment, local user path, or env-file
  reference was found in the v3 commit-bound files.
- The v3 raw probe directory was deleted before staging and is not part of this
  batch.
- Pre-existing raw capture leftovers from other worktrees/windows remain
  unrelated and must not be staged.

## 2026-06-05 — Release gate reset and non-mainstream source-profile pages

Updated the release-gate definition and continued the low-coverage regional
expansion by turning successful v3 source probes into source-profile pages. This
round is deliberately source-visible metadata work, not image capture.

Step 1 - release gate definition update:

- Updated `scripts/audit_image_release_gate.py`.
- Release gate now reports and hard-checks:
  - object-level source-visible coverage minimum: 95%;
  - object-level verified-open coverage minimum: 85%;
  - object-level weighted publication-grade image coverage minimum: 95%;
  - release source target: 2000 active sources;
  - release source coverage minimum: 80%.
- Weighted publication-grade image coverage is now object-level. Repeated
  photos/views of the same object are grouped by normalized source URL when
  possible, then by source record fallback. Each object contributes only the
  best single image-state weight, so multi-photo modern projects cannot inflate
  the score.
- `IMG01` and `IMG03` remain review states only. The gate script does not
  upgrade them from heuristics, LLM inference, terms-of-service text, platform
  signals, protocol evidence, impact score, or source priority.

Current release-gate result after the source-profile rebuild:

- Public surfaces: 1565.
- Object groups: 1553.
- Object-level source-visible coverage: 81.20% against the 95% gate.
- Object-level verified-open coverage: 30.97% against the 85% gate.
- Object-level weighted publication-grade image coverage: 54.90% against the
  95% gate.
- Release active source count: 236 against the 2000 source target.
- Simple release source coverage: 11.80%.
- Sources still needed for the 80% minimum release source gate: 1364.
- Sources still needed for the full 2000-source target: 1764.
- All four release gates currently fail, as expected for the prototype.

Step 2 - source coverage target reset:

- Updated `scripts/audit_source_coverage_rate_v1.py` from the early 200-source
  weighted target to the final 2000-source weighted target.
- Active source count after this round: 236.
- Weighted active source points: 130.25.
- Weighted source pool rate: 6.51%.
- Region weighted balance rate: 4.96%.
- Time weighted balance rate: 10.95%.
- Source coverage rate v1: 0.71%.
- Strict distribution-adjusted source coverage rate: 0.04%.
- Release source coverage gate passed: false.

Step 3 - source-profile capture:

- Added `scripts/run_nonmainstream_source_profile_capture_1990_2026_v1.py`.
- Generated `data/capture_batch_nonmainstream_source_profiles_1990_2026_records.csv`.
- Generated
  `data/capture_batch_nonmainstream_source_profiles_1990_2026_source_summary.csv`.
- Generated `data/nonmainstream_source_profile_impact_ratings_1990_2026_v1.csv`.
- Generated `docs/capture/NONMAINSTREAM_SOURCE_PROFILE_CAPTURE_1990_2026_v1.md`.
- Converted 127 successful v3 probe rows into 127 source-profile records.
- Record health for this batch: 127/127 = 100.00%.
- IMG/open or source-visible item image rate for this batch: 0/127 = 0.00%.
- IMG04 source-profile text pages: 127.

Macro-region distribution for the new source-profile pages:

- Latin America / Caribbean: 34.
- Africa: 29.
- Eastern Europe / Caucasus: 18.
- MENA: 14.
- South Asia: 12.
- Southeast Asia: 9.
- Central Asia: 5.
- Oceania / Indigenous: 5.
- East Asia: 1.

Protocol family distribution for the new source-profile pages:

- HTML: 82.
- HTML/catalog: 27.
- catalog/HTML: 14.
- HTML/database: 2.
- HTML/data: 1.
- OAI/HTML: 1.

Internal impact-rating distribution for the new source-profile pages:

- B: 73.
- A: 51.
- C: 3.

Next capture priority distribution from the v3 probe rows used here:

- P1 adapter build: 68.
- P1 text/source enrichment: 51.
- P2 manual source review: 8.

Step 4 - public surface rebuild and sheet statistics:

- Updated `scripts/rebuild_public_surfaces_from_records.py` so the new
  source-profile record CSV feeds public-surface generation.
- Rebuilt public payloads after source-profile capture.
- Rebuild output: 1685 source rows, 1565 public surfaces, 49 folders.
- Rebuilt public-surface image states: `IMG00` 41, `IMG01` 37, `IMG02` 748,
  `IMG03` 481, and `IMG04` 258.
- Added `scripts/audit_public_surface_sheet_counts_v1.py`.
- Generated `data/public_surface_sheet_counts_v1.csv`.
- Generated `data/public_surface_sheet_parent_breakdown_v1.csv`.
- Generated `docs/capture/PUBLIC_SURFACE_SHEET_COUNTS_v1.md`.
- Current main sheets: 1325.
- Current sub sheets: 226.
- Current text sheets: 242.
- Inferred parent main sheets: 185.
- Main sheets with more than 2 sub sheets: 121.
- Main sheets with more than 5 text sheets: 1.

Step 5 - README/license clarification:

- Updated `README.md` to clarify that GitHub may display MIT because the
  software code layer is MIT-licensed, but the frontend visual design remains
  governed by `FRONTEND_DESIGN_LICENSE.md`.
- `LICENSE` and `FRONTEND_DESIGN_LICENSE.md` remain the two explicit license
  files for the code layer and personal frontend design layer.

Boundary:

- This round did not download image binaries.
- This round did not capture screenshots, thumbnails, or source raw payloads.
- All newly generated source-profile records are `IMG04` because they are real
  source-level text/profile pages, not parser failures.
- No source priority, impact score, protocol signal, platform signal, TOS text,
  heuristic, or LLM output upgraded `IMG01` or `IMG03`.
- Impact/source priority remains internal triage only.
- The new pages help non-mainstream regions form a visible source system, but
  they do not yet provide publication-grade images or item-level rights review.

Best next capture directions:

- First: use the 68 P1 adapter-build rows to create real item/source adapters
  for WordPress REST, RSS/Atom, JSON-LD, PDF text/link, DSpace, CONTENTdm, IIIF,
  and Kramerius-like endpoints where stable source metadata is available.
- Second: use the 51 P1 text/source enrichment rows to add richer source
  descriptions, collection scope, and source-link pages without changing image
  states.
- Third: prioritize Latin America / Caribbean, Africa, Eastern Europe /
  Caucasus, MENA, and South Asia because this batch now has enough successful
  source-profile pages to form visible regional clusters.
- Fourth: repair Africa and Oceania / Indigenous failures from the v3 probe
  with manual canonical-domain checks and browser confirmation before another
  automated retry pass.
- Fifth: work the image gate separately by reviewing existing high-volume
  `IMG02` sources for authoritative item-level rights evidence, especially
  Cooper Hewitt, GSU CONTENTdm, Wellcome, Internet Archive, Te Papa, DigitalNZ,
  NAIDOC, Princeton Figgy, and V&A.

Verification:

- `python3 -m py_compile` passed for the updated/new release, source coverage,
  sheet-count, source-profile capture, rebuild, and probe scripts.
- `python3 scripts/audit_img_state_contract.py` passed.
- `python3 scripts/audit_public_surface_integrity.py` still reports the known
  warning that 12 surfaces share 6 exact image URLs. This is duplicate
  source-hosted URL review work, not evidence of local image copying.
- `python3 scripts/audit_image_release_gate.py` now fails by design because the
  final release gates are stricter than the current prototype state.
- `git diff --check` passed.
- Broad safety scan found expected policy words and false positives in public
  source text or URL slugs. A stricter credential-shape scan found no real
  credential assignment, bearer/cookie/session payload, API key assignment,
  local `/Users/` path, private key block, OpenAI-style key, AWS-style key, or
  `.env` reference in the intended commit-bound files.
- Pre-existing raw capture leftovers from other worktrees/windows remain
  unrelated and must not be staged.

## 2026-06-05 — Image-based release direction clarified

Decision update after reviewing the source-profile expansion:

- The project remains an image-based archive, not only a source directory.
- Source count must continue rising toward the final 2000-source release target,
  but future expansion needs to balance source coverage with usable image
  evidence.
- `IMG01` and `IMG03` rights upgrades should be actively pursued when there is
  authoritative item-level rights evidence. The ban is only on automatic
  upgrades from heuristics, LLM inference, source priority, platform signals,
  protocol hints, TOS text alone, or impact score.
- Open-image/verified-open rate should improve where evidence supports it, but
  without inflating the archive through unreviewed or locally copied images.
- `IMG04` remains valid for genuine no-image/text/context/source-profile pages,
  but its share now counts as an online-release risk because too many `IMG04`
  records weaken the image-based archive experience.
- Updated `scripts/audit_image_release_gate.py` to report both surface-level and
  object-level `IMG04` counts and coverage. The hard `IMG04` maximum threshold
  is not set yet and is currently reported as pending.

Current interpretation of the last source-profile pass:

- The 127 new source-profile pages helped source count and non-mainstream
  regional system visibility.
- They did not improve image coverage, open-image rate, verified-open rate, or
  publication-grade image coverage.
- Similar pure `IMG04` expansion should not be repeated as the main strategy
  unless it is paired with item-level capture, source-hosted image evidence, or
  rights-reviewable `IMG01`/`IMG03` opportunities.

Sheet-structure note:

- Current sheet statistics are not yet satisfactory.
- Main sheets should normally have meaningful sub sheets. The current low
  parent/sub depth may mean classification and grouping are still too weak, or
  it may become clearer only after source and surface volume increase.
- Text sheet count is also lower than the desired future structure. The working
  expectation is that a mature main sheet may carry roughly two text pages and a
  mature sub sheet may carry roughly one text page.
- This text/sub-sheet expectation is recorded now but should become a later
  consolidation and release-readiness audit after the source and surface pool is
  larger.

Next practical direction:

- Keep increasing source count and source coverage, but prioritize sources that
  can produce item-level records with source-hosted image routes, IIIF/viewer
  evidence, or explicit open rights.
- Review high-volume `IMG02` sources for authoritative rights evidence before
  upgrading to `IMG03`.
- Review conservative `IMG00`/`IMG04` rows where source-hosted visual evidence
  exists but was not yet promoted, especially when the source gives stable
  item pages and rights text.
- Continue non-mainstream regional expansion, but prefer capture routes that
  produce image-bearing object records over source-profile-only pages.

## 2026-06-05 — 500 non-mainstream pre-surface source registry batch

Correction: this batch should not be counted as 500 successful archive sources.
It records 500 newly reachable official source sites, distributed across
undercovered and non-mainstream regions, but they have not yet gone through
item-level capture, public-surface rebuild, or `IMG01`/`IMG02`/`IMG03`
image-bearing validation. These rows are therefore pre-surface source leads for
the next item/image capture pass.

Project source-success definition reaffirmed:

- A source counts as successful for release/source coverage only after it has
  produced item/source records, been rebuilt into archive surfaces, and yielded
  usable image-bearing evidence (`IMG01`, `IMG02`, or `IMG03`) with the relevant
  rights/review fields.
- Reachable official source homepages are useful leads, but they are not enough
  to count as successful archive sources.
- The 500-row registry below is retained as capture queue material, not as
  release-ready source coverage.

Step 1 - pre-surface source crawler:

- Added `scripts/run_nonmainstream_source_success_registry_2026_v1.py`.
- The script queries Wikidata for official websites of museums, libraries,
  archives, art museums/galleries, and cultural centers in undercovered
  countries/regions.
- The script probes official source URLs and records successful source
  responses as pre-surface capture leads.
- The final run used chunked Wikidata queries, single-country retries for
  timeout-prone countries, macro/country-balanced candidate selection, and macro
  caps to avoid overfitting one region.
- Generated `data/nonmainstream_source_success_registry_2026_v1.csv`.
- Generated `data/nonmainstream_source_success_summary_2026_v1.csv`.
- Generated `data/nonmainstream_source_success_region_breakdown_2026_v1.csv`.
- Generated `docs/capture/NONMAINSTREAM_SOURCE_SUCCESS_REGISTRY_2026_v1.md`.

Pre-surface source-lead metrics:

- Candidate official source sites after existing-source dedupe and balanced
  sampling: 2600.
- Reachable new source sites available from the crawl: 1071.
- Pre-surface source sites selected and archived: 500.
- Runtime: 913.8 seconds.
- These are reachable source leads, not release-counted successful sources.

Macro-region distribution for the 500 pre-surface source leads:

- Africa: 71.
- Latin America / Caribbean: 71.
- MENA: 71.
- Southeast Asia: 71.
- Eastern Europe / Caucasus: 70.
- South Asia: 66.
- Central Asia: 55.
- East Asia: 17.
- Oceania / Indigenous: 8.

Source class distribution:

- Museum: 281.
- Library: 136.
- Cultural center: 36.
- Archives: 29.
- Art gallery: 18.

Protocol/source-route hints:

- 31 rows are `P0 item/image adapter` priorities.
- 270 rows are `P1 item/source adapter` priorities.
- 124 rows are `P1 manual item capture` priorities.
- 75 rows are `P2 source enrichment` priorities.
- Protocol hints include IIIF, DSpace, RSS/Atom, JSON-LD, WordPress REST, PDF,
  and static app signals. These are adapter hints only and do not clear rights.

Coverage impact:

- Corrected `scripts/audit_source_coverage_rate_v1.py` so pre-surface registry
  rows do not count toward active source coverage until item-level
  image-bearing surfaces are built.
- Corrected `scripts/audit_image_release_gate.py` so release active source count
  does not include pre-surface registry rows.
- Active source count remains 236.
- Pre-surface source registry count: 500.
- Weighted active source points: 130.25.
- Weighted source pool rate: 6.51%.
- Region weighted balance rate: 4.96%.
- Time weighted balance rate: 10.95%.
- Source coverage rate v1: 0.71%.
- Strict distribution-adjusted source coverage rate: 0.04%.
- Release active source coverage remains 11.80% against the 2000-source target.
- Sources still needed for the 80% release source gate: 1364.
- Sources still needed for the full 2000-source target: 1764.

Image and sheet impact:

- Public surface count remains 1565.
- No generated public surfaces were added in this batch.
- Public `IMG04` count remains 258 surfaces / 251 objects.
- Public object-level `IMG04` coverage remains 16.16%.
- Object source-visible coverage remains 81.20%.
- Object verified-open coverage remains 30.97%.
- Object weighted publication-grade image coverage remains 54.90%.
- Main sheets remain 1325.
- Sub sheets remain 226.
- Text sheets remain 242.
- Main sheets with more than 2 sub sheets remain 121.
- Main sheets with more than 5 text sheets remain 1.

Boundary:

- No image binaries were downloaded.
- No screenshots, thumbnails, cookies, credentials, or raw HTML/source payloads
  were saved.
- Reachable source status did not upgrade `IMG01` or `IMG03`.
- No source priority, protocol signal, platform signal, Wikidata signal, or
  metadata heuristic is treated as rights clearance.
- The batch improves the next-capture queue only. It does not improve active
  source coverage, image coverage, open-image rate, or sheet counts until P0/P1
  rows are converted into item-level, image-bearing surfaces with explicit
  rights review.

Verification:

- `python3 -m py_compile` passed for the new source crawler and updated
  source/release audit scripts.
- `python3 scripts/audit_source_coverage_rate_v1.py` passed and wrote updated
  source coverage metrics under the corrected pre-surface/non-counted registry
  policy.
- `python3 scripts/audit_image_release_gate.py` still fails by design because
  image and source release gates remain below final thresholds.
- `python3 scripts/audit_img_state_contract.py` passed.
- `python3 scripts/audit_layered_image_source_metrics_v1.py` passed; image
  metrics did not change because the 500 pre-surface leads are not public image
  records.
- `python3 scripts/audit_public_surface_sheet_counts_v1.py` passed; sheet counts
  did not change.
- `git diff --check` passed.
- Strict credential-shape scan found no real credential assignment,
  bearer/cookie/session payload, API key assignment, local user path, private
  key block, OpenAI-style key, AWS-style key, or `.env` reference in the
  intended commit-bound files. Remaining broad hits are historical log lines
  that spell out safety scan terms.

## 2026-06-05 - Non-mainstream item/image capture expansion to 500+ successful records

Goal:

- Continue beyond pre-surface source discovery and produce at least 500 newly
  captured, image-bearing source records before rebuilding public surfaces.
- Use the previous non-mainstream registry work plus new source expansion, then
  run item/image capture, rebuild surfaces, and recalculate source coverage,
  image state coverage, and sheet counts.
- Keep the archive rights-aware: no image binaries, no thumbnails, no
  screenshots, no cookies/session data, and no raw source payloads were saved.

Source-lead expansion:

- Updated `scripts/run_nonmainstream_source_success_registry_2026_v1.py` so
  later batches can write separate versioned outputs and, for larger fill
  batches, accept `--target-count`.
- Generated four additional pre-surface source registries:
  - `v2`: 500 selected source leads from 1024 reachable successes.
  - `v3`: 500 selected source leads from 1103 reachable successes.
  - `v4`: 1000 selected source leads from 1065 reachable successes.
  - `v5`: 1000 selected source leads from 1022 reachable successes.
- Total pre-surface source registry rows now counted by audits: 3500.
- The combined v1-v5 registry pool deduped to 2284 unique source leads for
  item/image probing.

Registry distribution:

- v2 macro distribution: Africa 92, Latin America / Caribbean 91, MENA 90,
  Southeast Asia 80, Eastern Europe / Caucasus 70, South Asia 44, Central Asia
  22, East Asia 10, Oceania / Indigenous 1.
- v3 macro distribution: Africa 99, Latin America / Caribbean 98, MENA 81,
  Southeast Asia 80, Eastern Europe / Caucasus 70, South Asia 41, Central Asia
  20, East Asia 10, Oceania / Indigenous 1.
- v4 macro distribution: Eastern Europe / Caucasus 342, Latin America /
  Caribbean 231, Africa 198, Southeast Asia 80, MENA 77, South Asia 41,
  Central Asia 20, East Asia 10, Oceania / Indigenous 1.
- v5 macro distribution: Latin America / Caribbean 796, Southeast Asia 83,
  Africa 62, Central Asia 20, Eastern Europe / Caucasus 17, MENA 12, South
  Asia 9, Oceania / Indigenous 1.
- v5 is visibly Latin America-heavy because many MENA/Eastern Europe/South Asia
  Wikidata retries timed out during that run. It was used as a fill batch to
  reach clean image-bearing count, not as a balanced regional model.

Item/image capture:

- Added `scripts/run_nonmainstream_item_image_capture_2026_v1.py`.
- The script reads all `nonmainstream_source_success_registry_2026_v*.csv`
  files, probes official source pages, and writes archive records only when a
  source-hosted image route is visible in page metadata or JSON-LD.
- The first unfiltered pass found enough image routes but included too many
  favicons/logos/repeated page images. The script was tightened to reject
  favicon, icon, logo, tracker, sprite, and repeated image URL routes and to
  avoid image URLs already present in existing capture records.
- Final output: 587 clean image-bearing records across 581 source names.
- Final item/image macro distribution: Latin America 297, Eastern Europe 99,
  Africa 81, MENA 41, Southeast Asia 39, East Asia 14, Central Asia 8, South
  Asia 7, Oceania 1.
- Image states: 587 `IMG02`, 0 `IMG01`, 0 `IMG03`, 0 `IMG04`.
- Image route basis: `og:image` 549, `jsonld:image` 32, `twitter:image` 3,
  `link:image_src` 2, `twitter:image:src` 1.
- No `IMG01` or `IMG03` rights upgrade was made. All new records remain
  source-hosted `IMG02` pending item-level rights review.

Surface rebuild:

- Added `data/capture_batch_nonmainstream_item_image_2026_records.csv` to
  `scripts/rebuild_public_surfaces_from_records.py`.
- Rebuilt public surfaces and frontend mock payloads.
- Final rebuilt rows: 2266.
- Final public surfaces: 2146.
- Folders: 49.
- Surface image states: `IMG00` 43, `IMG01` 37, `IMG02` 1327, `IMG03` 481,
  `IMG04` 258.
- Source-visible image-ready surfaces: 1845/2146 (85.97%).
- Weighted publication image score: 1173.85/2146 (54.70%).

Final release-gate metrics:

- Active source count: 813.
- Release source target: 2000.
- Release source coverage: 40.65%.
- Sources still needed for 80% release source coverage: 787.
- Sources still needed for full 2000-source target: 1187.
- Object source-visible coverage: 86.54% against the 95% gate.
- Object verified-open coverage: 22.64% against the 85% gate.
- Object weighted publication-grade image coverage: 55.08% against the 95%
  gate. Object grouping counts repeated photos/views by source object, not by
  every surface row.
- Object `IMG04` coverage: 11.44%. The project still needs an explicit maximum
  `IMG04` release threshold.
- Release gates still fail by design: source-visible, verified-open, weighted
  publication-grade, and source-coverage gates remain below final targets.

Sheet statistics:

- Main sheets: 1903.
- Sub sheets: 229.
- Text sheets: 242.
- Main sheets with more than 2 sub sheets: 121.
- Main sheets with more than 5 text sheets: 1.
- The new batch mostly added main-sheet candidates. Sub/text sheet growth is
  still weak, which supports the earlier diagnosis that surface grouping and
  sheet consolidation need a later normalization pass.

Additional audit notes:

- `audit_layered_image_source_metrics_v1.py`: records total 2345,
  source-visible rate 87.38%, publication-grade candidate rate 82.90%,
  weighted publication rate 54.64%, open-image rate 6.95%, duplicate image URL
  rate 3.03%.
- `audit_public_surface_integrity.py` still exits with warnings because 12
  existing surfaces share 6 exact image URLs. After the final clean pass, the
  remaining repeated examples are existing Another Graphic / Barjeel records,
  not new non-mainstream item/image records.
- `audit_period_source_image_priority_v1.py`: highest combined priority remains
  `1930_1970` (0.2526), followed by `1970_2000` (0.1726), `2000_2026`
  (0.1481), and `pre_1930` (0.0963).
- `audit_nonmainstream_region_capture_health_v1.py`: target source coverage
  50.00%, record health 100.00%, IMG rate 71.43%, impact ratings A:15, B:6.
  This legacy health audit covers the earlier nonmainstream region batch, not
  all v1-v5 source leads.
- README/license check: `README.md` already documents the layered MIT software
  license plus `FRONTEND_DESIGN_LICENSE.md`; `LICENSE` is MIT and the personal
  frontend design license file is present.

Boundary:

- No image binaries were downloaded.
- No raw HTML/source payloads, cookies, sessions, browser state, screenshots,
  or local image files were saved.
- No source priority, protocol signal, platform signal, Wikidata signal,
  homepage metadata signal, or LLM/heuristic signal was used to upgrade
  `IMG01` or `IMG03`.
- `IMG02` records mean source-hosted visual routes only. They increase active
  source count and source-visible coverage, but they do not solve verified-open
  or publication-grade release gates.

Verification:

- `npm run build` passed in `frontend/`; Next generated 2223 static pages.
- `python3 -m py_compile` passed for the modified/new capture, rebuild, and
  audit scripts.
- `git diff --check` passed after normalizing the surface-assignment audit CSV
  line endings.
- `python3 scripts/audit_source_coverage_rate_v1.py` passed with corrected
  v1-v5 pre-surface registry diagnostics.
- `python3 scripts/audit_image_release_gate.py` still exits non-zero by design
  because release thresholds are not yet met.
- `python3 scripts/audit_img_state_contract.py` passed.
- `python3 scripts/audit_layered_image_source_metrics_v1.py` passed.
- `python3 scripts/audit_public_surface_sheet_counts_v1.py` passed.
- `python3 scripts/audit_period_source_image_priority_v1.py` passed.
- `python3 scripts/audit_nonmainstream_region_capture_health_v1.py` passed.
- `python3 scripts/audit_surface_assignment_gates_v1.py` passed.
- `python3 scripts/audit_public_surface_integrity.py` still exits non-zero with
  duplicate-image warnings: 12 existing surfaces share 6 exact image URLs.
- Strict credential-shape scan over commit-bound files found no real credential
  assignment, bearer/cookie/session payload, private key block, OpenAI-style key,
  AWS-style key, or local user path. Remaining `/Users/` and `.env` hits are
  historical safety-scan terms inside `PROJECT_LOG.md`.

## 2026-06-06 - Commons open source expansion, date repair, and source-coverage pass

Goal:

- Continue the non-mainstream/low-coverage source expansion and count success
  only after item/image capture, surface rebuild, frontend build, and gate
  audits.
- Add at least 1000 successful active sources.
- Raise object verified-open above 40%, source-visible above 90%, source
  coverage above 65%, and keep object `IMG04` below 10%.
- Audit text/sheet counts and document remaining grouping weaknesses.

Capture batches:

- Added `scripts/run_commons_open_global_south_image_capture_2026_v1.py`.
- Added `scripts/run_commons_open_period_balance_image_capture_2026_v1.py`.
- Added `data/capture_batch_commons_open_global_south_image_2026_records.csv`.
- Added `data/capture_batch_commons_open_period_balance_image_2026_records.csv`.
- Added matching source summaries and capture reports under `docs/capture/`.
- Both batches store source metadata, source links, rights evidence, and
  source-hosted Commons image URLs only. No image binaries, thumbnails,
  screenshots, raw API payloads, cookies, sessions, or browser state were
  saved.
- All new records are `IMG03` only when Commons extmetadata exposes open-license
  evidence. No heuristic, source-priority, platform, protocol, or LLM signal was
  used for rights upgrade.

Global South open-image batch:

- API capture wrote 1400 initial Commons open-image records.
- Date audit found a real bug: many records were incorrectly falling into 2026
  because object-year extraction did not prioritize Commons `DateTimeOriginal`
  and the earlier parser could use current/modified Commons timestamps or a
  current-year fallback as object dates.
- Fixed the parser so object dates come from explicit object-year evidence only:
  `DateTimeOriginal`, object name, image description, title, and category text.
  Commons modified/upload `DateTime` is not used as object date.
- Records without explicit object-year evidence are excluded.
- After repair: 1380 records retained, 20 dropped, 286 date fields corrected.
- Remaining explicit 2026 records: 7.
- Distinct file-source labels: 1376.
- Macro-region distribution: Latin America 1333, East Asia 26, Middle East and
  North Africa 14, Southeast Asia 4, Eastern Europe 2, Africa 1.
- Period distribution: pre-1930 561, 1930-1970 324, 1970-2000 77, 2000-2026
  418.

Period-balance open-image batch:

- Added after the date repair showed source coverage was still limited by
  period balance rather than active source count.
- Exact-year search targets 1970-2000 first and accepts global period-balanced
  Commons records when a non-mainstream region cannot be inferred from page
  metadata.
- Captured 90 records across 90 distinct source labels.
- Period distribution: 1930-1970 67, 1970-2000 23.
- Macro-region distribution: Global 61, Southeast Asia 22, Middle East and
  North Africa 2, Africa 2, Latin America 2, Eastern Europe 1.

Surface rebuild:

- Added both Commons capture record files to
  `scripts/rebuild_public_surfaces_from_records.py`.
- Rebuilt generated and frontend public-surface payloads.
- Final rebuilt rows: 3736.
- Public surfaces: 3616.
- Folders: 49.
- Surface image states: `IMG00` 43, `IMG01` 37, `IMG02` 1327, `IMG03` 1951,
  `IMG04` 258.
- Source-visible image-ready surfaces: 3315/3616 (91.68%).
- Weighted publication image score: 2496.85/3616 (69.05%).

Final release-gate metrics:

- Active source count: 2279.
- Release source target: 2000.
- Release source coverage by active source count: 113.95%.
- Source coverage rate v1: 67.05%, passing the requested 65% round target.
- Source pool rate: 100.00%.
- Region-weighted balance rate: 27.08%; this remains the main structural
  weakness because the new open batch is heavily Latin America weighted.
- Time-weighted balance rate: 67.05%.
- Object source-visible coverage: 92.04%, passing the requested 90% round
  target but still below the final 95% release gate.
- Object verified-open coverage: 54.27%, passing the requested 40% round target
  but still below the final 85% release gate.
- Object weighted publication-grade image coverage: 69.36%, still below the
  final 95% release gate. Object grouping counts repeated photos/views by source
  object rather than every surface row.
- Object `IMG04` coverage: 6.76%, passing the requested under-10% round target.

Source-coverage period breakdown:

- pre-1930: 569 active sources, 1028 records, 100.00% balance.
- 1930-1970: 415 active sources, 919 records, 59.29% balance.
- 1970-2000: 126 active sources, 391 records, 25.20% balance.
- 2000-2026: 1152 active sources, 1403 records, 100.00% balance.
- Next best source direction: targeted 1970-2000 open-image source pages,
  especially Africa, South Asia, Southeast Asia, MENA, Oceania/Pacific, and
  Eastern Europe. Latin America now needs consolidation more than volume.

Sheet and text statistics:

- Main sheets: 3371.
- Sub sheets: 231.
- Text sheets: 242.
- Main sheets with more than 2 sub sheets: 121.
- Main sheets with more than 5 text sheets: 1.
- Text sheet count remains flat despite richer source text in new records. This
  confirms that the current surface assignment layer is still producing mostly
  main-sheet candidates; text/subsheet expansion will need a later grouping and
  dossier-normalization pass rather than more raw capture alone.

Additional audit notes:

- `audit_layered_image_source_metrics_v1.py`: records total 3815,
  source-visible rate 92.24%, publication-grade candidate rate 89.49%,
  weighted publication rate 68.27%, open-image rate 42.80%, duplicate image URL
  rate 1.86%.
- `audit_img_state_contract.py` passed.
- `audit_period_source_image_priority_v1.py`: highest combined priority remains
  `1930_1970` (0.2067), followed by `1970_2000` (0.1580), `2000_2026`
  (0.1098), and `pre_1930` (0.0590).
- `audit_surface_assignment_gates_v1.py` passed and wrote 3815 audit rows.
- `audit_public_surface_integrity.py` still exits non-zero only for existing
  duplicate image URL warnings: 12 surfaces share 6 exact URLs from prior
  Another Graphic / Barjeel records, not the new Commons batches.
- README/license check: `README.md` already documents MIT for the software code
  layer plus the personal frontend design license in
  `FRONTEND_DESIGN_LICENSE.md`; no README change was needed this round.

Verification:

- `npm run build` passed in `frontend/`; Next generated 3693 static pages.
- `python3 -m py_compile` passed for the new/modified capture, rebuild, audit,
  and probe scripts.
- `python3 scripts/audit_source_coverage_rate_v1.py` passed with
  `source_coverage_rate_v1=67.05`.
- `python3 scripts/audit_image_release_gate.py` still exits non-zero by design
  because final release gates remain 95% source-visible, 85% verified-open, and
  95% weighted publication-grade.
- `python3 scripts/audit_img_state_contract.py` passed.
- `python3 scripts/audit_layered_image_source_metrics_v1.py` passed.
- `python3 scripts/audit_public_surface_sheet_counts_v1.py` passed.
- `python3 scripts/audit_period_source_image_priority_v1.py` passed.
- `python3 scripts/audit_surface_assignment_gates_v1.py` passed.
- `python3 scripts/audit_public_surface_integrity.py` reports only the existing
  duplicate URL warnings listed above.
- `git diff --check` passed.
- `python3 scripts/audit_secret_patterns.py` still reports token-shaped URL
  parameters in older raw probe HTML files that are not part of this commit.
- Commit-bound safety scan for `API_KEY`, token, password, secret, cookie,
  session, bearer, `/Users/`, and `.env` found no real credential assignment,
  bearer/cookie/session payload, private key, API key, or local user path. Hits
  were false positives in public titles such as `Secreto de confesion`,
  `poster-session`, normal project boundary text, or historical log entries.

## 2026-06-06 - Release-gate source expansion and sheet topology audit

Goal:

- Continue source expansion with at least 2000 new active sources.
- Push source coverage above 90%.
- Push object source-visible above 96%.
- Keep object `IMG04` as low as possible while preserving real text/context
  material.
- Audit text-page and sub-sheet structure without performing a merge or
  reclassification pass.
- Confirm object years, rebuild public surfaces, run frontend build, and push to
  `main` with a detailed description.

Why this batch captured more than 2000 records:

- Baseline object source-visible coverage was 3309/3595 (92.04%).
- Adding exactly 2000 fully visible objects would only reach roughly 94.9%.
- To exceed 96% without hiding or deleting existing `IMG00`/`IMG04` blockers,
  the batch needed roughly 3555+ additional source-visible object records.
- The release-gate capture target was therefore set to 4100 explicit-year
  `IMG03` records to leave rebuild/dedupe margin while still satisfying the
  user's 2000+ active-source requirement.

Capture batch:

- Added `scripts/run_commons_open_release_gate_expansion_2026_v1.py`.
- Added `data/capture_batch_commons_open_release_gate_expansion_2026_records.csv`.
- Added `data/capture_batch_commons_open_release_gate_expansion_2026_source_summary.csv`.
- Added `docs/capture/COMMONS_OPEN_RELEASE_GATE_EXPANSION_2026_v1.md`.
- The script uses Wikimedia Commons source pages as source-visible open records.
  It stores source metadata, source links, rights evidence, and source-hosted
  Commons image URLs only.
- No image binaries, thumbnails, screenshots, raw API payloads, cookies,
  sessions, browser state, or local image files were saved.
- All records are `IMG03` only when Commons extmetadata exposes open-license
  evidence. No heuristic, protocol, platform, priority, or LLM signal was used
  for rights upgrade.
- Records without explicit object-year evidence are excluded. Commons
  modified/upload timestamps are not used as object dates.

Release-gate expansion results:

- Records captured: 4100.
- Distinct active source labels: 4100.
- Period distribution: 1970-2000 1862, 1930-1970 1387, pre-1930 573,
  2000-2026 278.
- Macro-region distribution: Global 3430, Southeast Asia 392, Middle East and
  North Africa 85, Eastern Europe 57, Latin America 52, South Asia 38, Africa
  33, East Asia 13.
- Source-derived text length: minimum 108 characters, median 313 characters.
- Top date values: 1979 (459), 1974 (288), 1971 (193), 1972 (165), 1975 (140),
  1976 (137), 1973 (131), 1944 (109), 1970 (97), 1952 (87), 1935 (65), 1977
  (62).
- Explicit 2026 records in the new batch: 2. Manual spot check confirmed they
  carry explicit 2026 object-date evidence rather than fallback/current-year
  pollution.

Surface rebuild:

- Added the release-gate expansion records file to
  `scripts/rebuild_public_surfaces_from_records.py`.
- Rebuilt generated and frontend public-surface payloads.
- Final rebuilt rows: 7836.
- Public surfaces: 7716.
- Folders: 50.
- Surface image states: `IMG00` 43, `IMG01` 37, `IMG02` 1327, `IMG03` 6051,
  `IMG04` 258.
- Source-visible image-ready surfaces: 7415/7716 (96.10%).
- Weighted publication image score: 6186.85/7716 (80.18%).

Final release-gate metrics after rebuild:

- Active source count: 6379.
- New active source labels in this batch: 4100.
- Release source target: 2000.
- Release active-source coverage: 318.95%.
- Source coverage rate v1: 100.00%, above the requested 90% target.
- Source pool rate: 100.00%.
- Time-weighted balance rate: 100.00%.
- Region-weighted balance rate: 28.96%; still a structural diagnostic weakness
  because the release-gate filler is mostly global Commons rather than
  region-balanced local archive sources.
- Object source-visible coverage: 96.28%, above the requested 96% target.
- Object verified-open coverage: 78.64%, still below the final 85% release gate
  but substantially higher than the previous round.
- Object weighted publication-grade image coverage: 80.36%, still below the
  final 95% release gate.
- Object `IMG04` coverage: 3.16%, lower than the previous 6.76% and well under
  the current round's pressure to keep `IMG04` low.

Source-coverage period breakdown:

- pre-1930: 1142 active sources, 1601 records, 100.00% balance.
- 1930-1970: 1802 active sources, 2306 records, 100.00% balance.
- 1970-2000: 1988 active sources, 2253 records, 100.00% balance.
- 2000-2026: 1430 active sources, 1681 records, 100.00% balance.

Sheet topology and text audit:

- Added `scripts/audit_sheet_topology_text_ratio_v1.py`.
- Added `data/sheet_topology_text_ratio_v1.csv`.
- Added `data/sheet_topology_group_opportunities_v1.csv`.
- Added `docs/capture/SHEET_TOPOLOGY_TEXT_RATIO_v1.md`.
- Main sheets: 7462.
- Sub sheets: 240.
- Independent text-sheet surfaces: 242.
- Independent text-sheet surface rate: 3.14%.
- Sub/support surface rate: 3.29%.
- Research dossiers: 7716.
- Single-anchor dossiers: 7452.
- Compound/group dossiers: 264.
- Dossiers with any generated `text_page`: 7702.
- Dossiers with two or more text pages: 0.
- Dossiers with more than two total pages: 2008.
- Average dossier pages: 2.28.
- Average dossier text pages: 1.00.
- Group candidates: 257.
- Strong group candidates: 143 medium/high-confidence groups with at least
  three members.
- Interpretation: capture is now far ahead of sheet architecture. Most new
  records become main-sheet surfaces. The export/dossier layer does add one text
  page for nearly every dossier, but independent text sheets and multi-page
  research packets are still scarce. The next structural task should be a
  grouping/dossier normalization pass, not another raw capture-only pass.

Additional audit notes:

- `audit_layered_image_source_metrics_v1.py`: records total 7915,
  source-visible rate 96.26%, publication-grade candidate rate 94.93%,
  weighted publication rate 79.52%, open-image rate 72.43%, duplicate image URL
  rate 0.90%.
- `audit_period_source_image_priority_v1.py`: highest combined priority is now
  `1930_1970` (0.1105), followed by `2000_2026` (0.0885), `1970_2000`
  (0.0336), and `pre_1930` (0.0255).
- `audit_surface_assignment_gates_v1.py` passed and wrote 7915 audit rows.
- `audit_public_surface_integrity.py` still exits non-zero only for the existing
  duplicate image URL warnings: 12 surfaces share 6 exact URLs from prior
  Another Graphic / Barjeel records, not the new Commons release-gate batch.

Verification:

- `python3 -m py_compile` passed for the new/modified release-gate capture,
  rebuild, source coverage, sheet-topology, and existing Commons capture
  scripts.
- `python3 scripts/audit_source_coverage_rate_v1.py` passed with
  `source_coverage_rate_v1=100.00`.
- `python3 scripts/audit_image_release_gate.py` now passes the object
  source-visible and release-source gates, but still exits non-zero by design
  because final verified-open and weighted-publication gates are below 85% and
  95%.
- `python3 scripts/audit_img_state_contract.py` passed.
- `python3 scripts/audit_layered_image_source_metrics_v1.py` passed.
- `python3 scripts/audit_public_surface_sheet_counts_v1.py` passed.
- `python3 scripts/audit_period_source_image_priority_v1.py` passed.
- `python3 scripts/audit_surface_assignment_gates_v1.py` passed.
- `python3 scripts/audit_sheet_topology_text_ratio_v1.py` passed.
- `python3 scripts/audit_public_surface_integrity.py` reports only the existing
  duplicate URL warnings listed above.
- `npm run build` passed in `frontend/`; Next generated 7794 static pages. The
  first attempt failed with `ENOSPC` after a partial `.next` build consumed the
  remaining disk space. The partial `frontend/.next` build output was removed,
  freeing space, and the clean rerun completed. The successful build emitted
  several Next static-generation retry messages for slow pages, but finished
  successfully.
- Final safety follow-up sanitized a Commons metadata string that contained a
  source-side Windows user-profile file URL before it could remain in public
  payloads. The cleanup is enforced in
  `rebuild_public_surfaces_from_records.py` and the shared Commons capture
  cleaning helper for future runs.
- After the sanitization rebuild, targeted scans found no remaining Windows
  user-profile file URL strings in the new release-gate CSV, generated payload,
  frontend payload, or mirrored public JSON. A commit-bound strict
  credential-shape scan reported `strict_hits 0`.
- `python3 scripts/audit_secret_patterns.py` still exits non-zero only for
  older uncommitted raw HTML probe files under
  `data/contemporary_source_scan_probe_1990_2026_v1_raw/` and
  `data/global_edge_discovery_probe_v1_raw/`; those files are outside this
  round's staged set.
- A final post-sanitization `npm run build` in `frontend/` passed again with
  7794/7794 static pages generated. The same slow-page retry warnings appeared
  during static generation, but the build exited successfully.
- Push follow-up: GitHub rejected the first push attempt because the pretty
  printed public-surface JSON exceeded the 100 MB per-file limit. The rebuild
  writer now emits compact JSON with equivalent payload content, reducing each
  mirrored public payload from about 107 MB to about 78 MB. A post-compact
  rebuild kept the same surface and image-state metrics, and another
  `npm run build` passed with 7794/7794 static pages generated.

## 2026-06-06 - Source coverage v2 and main-sheet research value audit

Purpose:

- Reframe the suspicious `source_coverage_rate_v1=100.00` result as a capped
  pool/time-fill signal rather than a true release-health signal.
- Add a stricter source coverage v2 metric that includes distribution,
  period balance, source-visible rate, and main-sheet research quality.
- Audit whether current main sheets have enough source text, impact/context,
  image evidence, and grouping basis to remain standalone research anchors.
- Run a bounded contemporary/non-mainstream Commons calibration capture after
  the previous large Commons expansion showed diminishing returns.

Capture:

- Added `scripts/run_commons_open_contemporary_region_research_capture_2026_v1.py`.
- Output records:
  `data/capture_batch_commons_open_contemporary_region_research_2026_records.csv`.
- Output summary:
  `data/capture_batch_commons_open_contemporary_region_research_2026_source_summary.csv`.
- Output report:
  `docs/capture/COMMONS_OPEN_CONTEMPORARY_REGION_RESEARCH_CAPTURE_2026_v1.md`.
- Records captured: 120.
- Distinct active source names: 120.
- Period distribution: `2000_2026` 83, `1970_2000` 28, `1930_1970` 9.
- Macro-region distribution: Latin America 74, Middle East and North Africa 34,
  Africa 10, South Asia 2.
- Explicit 2026 rows: 0, so this round did not introduce current-year fallback
  pollution.
- Query failures: 20.
- Boundary: metadata, source links, rights evidence, source-derived text, and
  source-hosted image URLs only. No image binaries, thumbnails, screenshots,
  raw API payloads, cookies, or browser sessions were saved.
- Interpretation: Commons still works for small open-image calibration, but the
  high-frequency region/object paths are now heavily exhausted by previous
  batches. A serious 2000-2026 expansion needs non-Commons project/studio,
  festival, independent archive, type-design, community, and design-platform
  sources.

Surface rebuild:

- Added the contemporary region research CSV to
  `scripts/rebuild_public_surfaces_from_records.py`.
- Rebuilt generated and frontend public payloads.
- Rebuilt rows: 7956.
- Public surfaces: 7836.
- Folders: 50.
- Surface image states: `IMG00` 43, `IMG01` 37, `IMG02` 1327, `IMG03` 6171,
  `IMG04` 258.
- Source-visible image-ready surfaces: 7535/7836 (96.16%).
- Weighted publication image score: 6294.85/7836 (80.33%).
- Mirrored compact public payloads are about 79 MB each, still under the
  repository host's 100 MB per-file hard limit.

Source coverage v2:

- Added `scripts/audit_source_coverage_rate_v2.py`.
- Added `data/source_coverage_rate_v2.csv`.
- Added `data/source_coverage_period_breakdown_v2.csv`.
- Added `data/source_coverage_region_breakdown_v2.csv`.
- Added `docs/capture/SOURCE_COVERAGE_RATE_v2.md`.
- `source_pool_period_fill_rate`: 100.00. This is the old v1 capacity/time-fill
  signal and should no longer be presented alone as true coverage health.
- `strict_distribution_adjusted_source_coverage_rate`: 28.96.
- `period_surface_balance_rate`: 81.92.
- `period_quality_main_balance_rate`: 38.88.
- `region_surface_balance_rate`: 12.50.
- `region_quality_main_balance_rate`: 8.55.
- `source_visible_surface_rate`: 96.16.
- `research_quality_adjusted_source_coverage_rate_v2`: 3.20.
- Interpretation: the archive has enough source volume to fill the old release
  target, but it does not yet have healthy region distribution or enough
  quality main-sheet research anchors.

Main-sheet research value audit:

- Added `scripts/audit_main_sheet_research_value_v1.py`.
- Added `data/main_sheet_research_value_audit_v1.csv`.
- Added `data/main_sheet_research_value_period_breakdown_v1.csv`.
- Added `docs/capture/MAIN_SHEET_RESEARCH_VALUE_AUDIT_v1.md`.
- Public surfaces audited: 7836.
- Main sheets audited: 7582.
- Recommended actions among main sheets:
  - `keep_main`: 3142.
  - `keep_main_add_editorial_text`: 66.
  - `promote_text_or_appendix`: 189.
  - `demote_to_sub`: 4176.
  - `demote_to_card`: 9.
- The audit separates source-derived text from generated/editorial context.
  It uses impact as internal triage only; impact does not upgrade rights,
  authorship, source authority, or `IMG01`/`IMG03`.
- Interpretation: the main-sheet count is over-granted. Many image-bearing
  records have enough metadata to be useful but not enough research structure
  to stand alone. They should become subsheets/cards/support packets unless
  grouped under a stronger parent or given reviewed editorial text pages.

Sheet/topology after rebuild:

- Main sheets: 7582.
- Sub sheets: 240.
- Independent text-sheet surfaces: 242.
- Research dossiers: 7836.
- Dossiers with any generated `text_page`: 7822.
- Dossiers with two or more text pages: 0.
- Average dossier pages: 2.28.
- Group candidates: 553.
- Strong group candidates: 351.
- Main sheets with more than two sub sheets: 359.
- Main sheets with more than five text sheets: 5.
- Interpretation: the generated dossier layer gives most sheets one text page,
  but independent text sheets and multi-text-page research packets remain far
  too scarce.

Other audit results:

- `audit_image_release_gate.py`: object source-visible 96.34%; object
  verified-open 78.96%; object weighted publication-grade 80.51%; object
  `IMG04` 3.11%; active source count 6499. It still exits non-zero by design
  because final verified-open and weighted-publication gates are below 85% and
  95%.
- `audit_layered_image_source_metrics_v1.py`: records total 8035,
  source-visible rate 96.32%, publication-grade candidate rate 95.01%,
  weighted publication rate 79.68%, open-image rate 72.84%, duplicate image URL
  rate 0.88%.
- `audit_period_source_image_priority_v1.py`: highest combined priority remains
  `1930_1970` (0.1100), followed by `2000_2026` (0.0839), `1970_2000`
  (0.0321), and `pre_1930` (0.0255).
- `audit_surface_assignment_gates_v1.py`: wrote 8035 rows; dispositions include
  `main_sheet_candidate` 7152, `subsheet_visual` 472, `text_sheet_candidate`
  198, and `dedupe_child_record` 60.
- `audit_public_surface_integrity.py` still exits non-zero only for the existing
  duplicate URL warnings: 12 surfaces share 6 exact image URLs from prior
  Another Graphic / Barjeel records.

Verification:

- `npm run build` passed in `frontend/`; Next generated 7914/7914 static pages.
  The same slow-page retry warnings appeared during static generation, but the
  build exited successfully.
- `python3 -m py_compile` passed for the new/modified capture, audit, grouping,
  linkage, coverage, and rebuild scripts.
- `git diff --check` passed after normalizing generated group/linkage CSV
  output to strip trailing field whitespace.
- `python3 scripts/audit_secret_patterns.py` still exits non-zero only for
  older uncommitted raw HTML probe files under prior probe directories; those
  files are outside this round's staged set.
- Commit-bound strict credential-shape scan reported `strict_hits 0`.

## 2026-06-06 - Research Packet Anchor Frontend Strategy

Scope:

- Locked the next frontend direction before the larger classification/deep
  research cycle: a `research packet anchor` is treated as a flexible folder,
  not a fixed spread/book metaphor.
- The packet structure is allowed to choose `main`, `sub`, `card`, `text`, and
  `appendix` roles from impact, source depth, relation density, period span,
  rights state, region scarcity, and editorial need.
- No source capture, source probing, image download, image mirroring, rights
  upgrade, `IMG01`/`IMG03` promotion, main/sub demotion, or generated
  classification rewrite was performed in this round.

Frontend implementation:

- Disabled the reader spread-mode entry path. The reader now advances one page
  at a time and no longer exposes a single/spread toggle.
- Replaced the old bottom spread button with an `AI` button that opens the
  right-side research assistant panel.
- Moved reader content navigation out of the right-side nav stack and into a
  left-side `Content` button.
- Added a left slide-in packet/tree panel that shows the active packet anchor,
  current structure basis, page count, pending dossier grouping state, and the
  archive page sequence.
- Dedicated the right slide-in panel to AI/research support: current object
  summary, image/rights/source state, packet factors, and the next review
  queue for editorial and classification work.
- Kept the packet/dossier data hook optional in `Reader`. Direct dossier lookup
  was not wired into static surface routes because it made large static builds
  more fragile; a lightweight precomputed packet index should be the next
  bridge before deep research classification is connected to the UI.
- Added cached research-dossier lookup maps in `archive-data` so future packet
  integrations can avoid repeated linear scans.

Verification:

- `npm run build` passed in `frontend/`; Next generated 7914/7914 static pages.
  The build still emitted slow static-page retry warnings in this environment,
  but exited successfully.
- Local dev server verification used `http://127.0.0.1:3040`.
- HTTP checks returned 200 for `/surfaces/SURF-GAX1970R001` and
  `/folders/region/brazil`.
- Headless Chrome check confirmed:
  - the right `AI` panel opens and shows `Research assistant`;
  - the left `Content` panel opens and shows the packet anchor block plus
    archive sequence;
  - no visible `spread` control text remains in the reader;
  - the sample page reported `VIS OK`.

## 2026-06-06 - Reader Inspection Fixes After Packet Prototype

Scope:

- Follow-up frontend corrections from live reader inspection.
- No source capture, image download, rights upgrade, or classification/deep
  research change was performed.

Reader shell changes:

- Narrowed the left packet/content panel by about 30% on desktop.
- Changed the bottom AI entry into a square icon + `Assistant` button.
- Removed the separate right-side AI research panel from the reader flow.
- Search and Assistant now reuse the same floating-window container, but the
  entry point decides the render path: Search opens search-only UI; Assistant
  opens assistant-only UI with current object context and a reference lookup.
- Added an explicit WebLLM adapter path for Assistant. It attempts to load the
  WebLLM runtime in-browser via WebGPU, then sends the current archive object
  context into a local assistant prompt. The UI reports loading, ready, and
  error states rather than presenting a fake chat surface.
- Marked the bottom-left `VIS` reader badge as a pre-release QA marker that
  must be removed before launch.

Surface/layout containment:

- Added an internal vertical-scroll fallback for main sheets, sub sheets, and
  archive cards inside the single-page reader so overlong image/text cards do
  not force the outer page frame to break.
- Updated the reader visual check so deliberately scrollable internal cards do
  not count as page overflow failures.

Appendix routing:

- Temporarily disabled automatic reader appendix packets. AX01 rights strips,
  AX05 source statements, and AX06 typed-index pages remain in the appendix lab
  for redesign, but they are no longer inserted into the primary reading flow.
- Reason: the current long/narrow appendix designs interrupt body reading,
  compete with the main sheet, and create visible overflow/legibility issues.

## 2026-06-06 - Assistant WebLLM Interaction Correction

Scope:

- Corrected the Assistant interaction after live review. This was a frontend
  interaction pass only: no source capture, image download, rights upgrade,
  surface rebuild, or classification/deep-research change was performed.

Assistant changes:

- Removed the visible `Load WebLLM` control. Assistant is treated as WebLLM;
  the browser-side WebLLM session now prepares automatically when Assistant
  opens.
- Kept Search and Assistant in the same floating container, but removed the
  reference-lookup/search input from Assistant mode. Search renders search;
  Assistant renders a chat surface.
- Replaced the single-answer prototype with a simple chat thread, message
  input, `Send` action, and `Research` action.
- `Research` uses the same local WebLLM session with a more developed,
  sectioned response instruction for source evidence, interpretation, and next
  checks. It still must not claim image-rights upgrades.
- Cached the WebLLM session in the browser module so closing and reopening
  Assistant does not intentionally restart the model setup. Failed
  initializations clear the cache so a later retry can run.

Verification:

- `npm run build` passed in `frontend/`; Next generated 7914/7914 static pages.
  The familiar slow static-page retry warnings appeared, but the build exited
  successfully.

## 2026-06-06 - Assistant RAG Prompt Composition Correction

Scope:

- Corrected the Assistant RAG behavior after review. This was a frontend
  assistant/runtime and documentation pass only: no source capture, image
  download, rights upgrade, surface rebuild, or classification/archive merge
  was performed.

Reason:

- The Assistant should not be a deterministic search wrapper. Search returns
  records; Assistant should use Qwen over retrieved archive evidence to give a
  short, useful, human research response.
- The word "script" in the Assistant plan means request classification and
  prompt composition, not scripted final answers.
- After the previous push, the dev server showed a
  `/models/onnx-community/Qwen3.5-0.8B-ONNX/tokenizer_config.json` 404. The
  project does not currently package model assets under `frontend/public/models`,
  so local model probing was misleading and could slow or confuse cold-start
  diagnosis.

Correction:

- Added scripted request planning inside `frontend/src/lib/assistant-retrieval.ts`.
  It classifies user intent as archive intro, first/earliest, recommendation,
  current object, rights/image, comparison, source lookup, or open exploration.
- The retrieval script now emits a compact `REQUEST_PLAN` plus compressed
  candidate evidence. The plan contains answer job, answer shape, focus terms,
  and evidence policy, and explicitly says it must not be quoted as the answer.
- Ordinary Assistant still calls Qwen fast mode for the final response. The
  script only shortens and clarifies the RAG prompt so Qwen can answer more
  usefully with less context.
- Fast mode now passes a shorter conversation window to Qwen while preserving
  same-page memory behavior.
- Disabled Transformers.js local `/models/` probing by setting
  `allowLocalModels=false`; the only allowed runtime artifact remains
  `onnx-community/Qwen3.5-0.8B-ONNX` with browser cache.
- Updated `docs/system/ASSISTANT_RESPONSE_STRATEGY_v0.md` to record the prompt
  composition boundary: retrieval may classify and brief, but Qwen generates
  the Assistant/Research answer.

Guardrails:

- `Qwen/Qwen3.5-0.8B` remains the only Assistant model identity.
- No Llama, hosted LLM API, WebLLM catalog fallback, or alternate model path is
  permitted.
- Search remains deterministic and separate from Assistant.
- Assistant/RAG prompt composition does not download images, create local image
  mirrors, or upgrade IMG01/IMG03 rights state.

Verification:

- `npm run build` passed in `frontend/`; Next generated 7914/7914 static pages.
  The familiar 60-second static-page retry warnings appeared, but the build
  exited successfully.
- `git diff --check` passed.
- Runtime scan over `frontend/src/lib`, `frontend/src/components`, and
  `frontend/scripts` found no `Llama`, `WEBLLM`, `WebLLM`, or `Load WebLLM`
  references.
- Scripted-answer scan found no `assistant-instant`,
  `buildInstantAssistantAnswer`, `DRAFT_ANSWER`, or `FAST_REFINE` in
  `frontend/src` or `docs/system`.
- Commit-bound credential scan found no real API key, password, secret, bearer
  value, cookie assignment, local user path, or env-file reference. Remaining
  hits are historical project-log scan terms plus `transformers.env`,
  tokenizer, and max-token identifiers.
- Local dev server started at `http://localhost:3040`; route checks returned
  HTTP 200 for `/folders/region/russia` and `/surfaces/SURF-GAX1970R001`.
- Chrome smoke test on `http://127.0.0.1:3040/folders/region/russia` confirmed
  the Assistant panel opens, the bottom navigation is not obscured, and the dev
  server no longer logs a `/models/onnx-community/...` Qwen local-probe 404.

## 2026-06-06 - Assistant Instant Layer And Qwen Fast-Refine Correction

Scope:

- Corrected ordinary Assistant latency after product review. This was a
  frontend assistant/runtime and documentation pass only: no source capture,
  image download, rights upgrade, surface rebuild, or archive classification
  change was performed.

Diagnosis:

- A normal Assistant question must not wait for model load or generation.
  Calling Qwen should not mean blocking the user interface.
- The prior correction reduced Qwen output length and forced WebGPU, but normal
  Assistant still had a model-first path. That could keep answers above the
  desired sub-5-second interaction target whenever the Qwen session was cold or
  slow.
- Project rule remains unchanged: `Qwen/Qwen3.5-0.8B` is the only model
  identity and `onnx-community/Qwen3.5-0.8B-ONNX` is the only browser runtime
  artifact. No Llama, hosted API, WebLLM catalog fallback, or alternate local
  generation model is allowed.

Correction:

- Added `frontend/src/lib/assistant-instant.ts` as the ordinary Assistant
  deterministic answer layer. It uses active page context, archive retrieval
  candidates, image-state policy, source/rights metadata, and short scripted
  response patterns.
- Extended `frontend/src/lib/assistant-retrieval.ts` to return structured
  candidate evidence so ordinary answers can cite real archive candidates
  without asking the model to invent rows.
- Changed `frontend/src/components/archive/shell/search.tsx` so normal
  Assistant immediately renders the scripted answer, then starts/reuses Qwen in
  the background for a bounded fast-refine pass. If Qwen returns quickly, it
  replaces the same answer with a lightly polished version; if it misses the
  budget, the scripted answer remains visible.
- Kept Research as the explicit waiting path. Research still uses the same
  Qwen3.5-0.8B session with broader retrieval and longer answer budget.
- Added fast-refine controls to `frontend/src/lib/qwen35-adapter.ts`:
  `fast`, `draft`, and a 36-token generation cap. Fast-refine is instructed to
  improve phrasing only, use supplied archive context, and add no new facts.
- Added `docs/system/ASSISTANT_RESPONSE_STRATEGY_v0.md` to document the product
  rule: ordinary Assistant is script-first plus non-blocking Qwen fast-refine;
  Research is the only path that waits for Qwen.

Build reliability note:

- The first production build after this change compiled and type-checked, but
  failed during static export with `ENOSPC` at
  `/folders/region/unresolved-region`. The cause was local disk exhaustion,
  amplified by Next production webpack cache growth, not a TypeScript or
  application error.
- Updated `frontend/next.config.ts` to disable production webpack disk cache.
  This reduced the completed `.next` directory to about 714 MB and allowed the
  full static build to finish on the current machine.

Verification:

- `npm run build` passed in `frontend/`; Next generated 7914/7914 static pages.
  The known slow static-page retry warnings appeared, but the build exited
  successfully.
- `git diff --check` passed.
- Runtime scan over `frontend/src/lib`, `frontend/src/components`, and
  `frontend/scripts` found no `Llama`, `WEBLLM`, `WebLLM`, or `Load WebLLM`
  references.
- Local dev smoke test used `http://127.0.0.1:3040/surfaces/SURF-GAX1970R001`.
  A normal Assistant question rendered the scripted archive answer in 555 ms,
  before any blocking model path, and the page text contained no Llama/WebLLM
  labels.
- A recommendation prompt on
  `http://127.0.0.1:3040/folders/region/france` returned in 33 ms with
  archive candidates and surface IDs, framed as current-archive navigation
  rather than an invented external canon claim.
- Commit-bound credential scan for `api_key`, `password`, `secret`, `cookie`,
  `bearer`, `.env`, `/Users/`, and `token` found no real credentials. Hits were
  false positives in `transformers.env`, tokenizer/max-token identifiers, and
  historical PROJECT_LOG scan descriptions.
- Existing raw capture modifications and untracked raw probe directories remain
  unstaged and were not part of this frontend assistant pass.

## 2026-06-06 - Assistant RAG Prompt Correction

Scope:

- Corrected the previous instant-assistant interpretation after product review.
  This was a frontend assistant prompt/runtime and documentation pass only: no
  source capture, image download, rights upgrade, surface rebuild, or archive
  classification change was performed.

Reason:

- The project intent is not to turn Assistant into Search. Search should return
  deterministic matching records; Assistant should improve reading and research
  flow through local Qwen over a compact RAG evidence brief.
- The prior script-first path made ordinary Assistant very fast, but it also
  produced catalog-like replies such as folder restatements. That failed the
  product goal: Assistant needs to be conversational, advisory, and useful for
  archive orientation, recommendations, caveats, and research extension.

Correction:

- Removed the scripted ordinary-answer module from the runtime path. Retrieval
  now prepares evidence only; Qwen fast mode is responsible for normal
  Assistant answers.
- Updated `frontend/src/components/archive/shell/search.tsx` so ordinary
  Assistant calls the same local Qwen session used by Research. If Qwen is
  cold, the UI shows a temporary preparation notice after about 3 seconds and
  replaces it when the local model answer is ready.
- Updated `frontend/src/lib/qwen35-adapter.ts` with a more human RAG prompt:
  ordinary answers should be short, advisory, grounded in supplied evidence,
  and avoid engineering/catalog phrases such as `is indexed here`,
  `reading angle`, or `current context`.
- Reduced the ordinary fast-answer cap to 56 new tokens so normal Assistant
  remains a short-answer path rather than a long reasoning mode.
- Replaced `docs/system/ASSISTANT_RESPONSE_STRATEGY_v0.md` so it now states:
  Assistant is Qwen-backed fast RAG, Search is deterministic lookup, Research
  is longer RAG, and no scripted ordinary-answer module should be used as the
  final Assistant layer.

Model/runtime rule:

- `Qwen/Qwen3.5-0.8B` remains the only model identity.
- `onnx-community/Qwen3.5-0.8B-ONNX` remains the only frontend runtime artifact.
- No Llama, hosted API, WebLLM catalog fallback, or alternate local generation
  model was introduced.

Verification:

- `npm run build` passed in `frontend/`; Next generated 7914/7914 static pages.
  The known slow static-page retry warnings appeared, but the build exited
  successfully.
- `git diff --check` passed.
- Runtime source scan over `frontend/src/lib`, `frontend/src/components`, and
  `frontend/scripts` found no `Llama`, `WEBLLM`, `WebLLM`, or `Load WebLLM`
  references.
- Runtime source scan found no remaining `assistant-instant`,
  `buildInstantAssistantAnswer`, `DRAFT_ANSWER`, or fast-refine draft path.
- Commit-bound credential scan for `api_key`, `password`, `secret`, `cookie`,
  `bearer`, `.env`, `/Users/`, and `token` found no real credentials. Hits were
  false positives in `transformers.env`, tokenizer/max-token identifiers, and
  historical PROJECT_LOG scan descriptions.
- Local dev smoke test used `http://127.0.0.1:3040/folders/region/russia`.
  A normal Assistant question no longer produced the old scripted
  `is indexed here` / `Reading angle` / `Current context` response. On cold
  model load, the UI showed a temporary local-Qwen preparation notice instead.
- Local verification used `http://127.0.0.1:3040/folders/region/france`.
- Browser check confirmed Assistant renders `close ×`, `Send`, and `Research`
  controls; it no longer renders `Load WebLLM`, a reference lookup, or an
  internal search input.
- Browser check confirmed Search mode still renders the archive search input
  and does not render WebLLM or `Research`.

## 2026-06-06 - Assistant Panel Simplification After Live Review

Scope:

- Follow-up frontend correction after live reader screenshots. No source
  capture, image download, rights upgrade, surface rebuild, or classification
  change was performed.

Assistant panel changes:

- Removed the Assistant context/status block entirely. The panel no longer
  displays implementation identity, current object summary, date/image/source
  rows, or readiness metadata.
- Removed the separate `Research` button from the compose area.
- Converted the top-left `ASSISTANT` title into the research-mode toggle:
  hovering it reveals `RESEARCH`; clicking enables research mode; clicking
  again returns to Assistant mode.
- Assistant replies are labeled `Assistant`, not by the underlying local model
  implementation.
- The compose area now has one submit control only: `Send`.

Layout containment:

- Updated the floating Search/Assistant container to measure the bottom
  page-turn control and use that as its lower boundary.
- The panel now receives a fixed computed height and keeps conversation
  overflow inside the assistant thread, preventing overlap with the bottom
  navigation/page controls.

Verification:

- `npm run build` passed in `frontend/`; Next generated 7914/7914 static pages.
  The known slow static-page retry warnings appeared, but the build exited
  successfully.
- Local verification used `http://127.0.0.1:3040/folders/region/france`.
- Browser check confirmed the Assistant panel no longer renders the deleted
  context/status block, WebLLM wording, date/image/source rows, or a separate
  `Research` compose button.
- Browser layout check confirmed the floating Assistant stack bottom stays
  above the page-turn control.
- Browser interaction check confirmed the top-left Assistant title toggles
  research mode, and the bottom Assistant control closes the open panel when
  clicked again.

## 2026-06-06 - Assistant Model Correction: Qwen3.5-0.8B Only

Scope:

- Corrected the local assistant model/runtime path after review. This was a
  frontend assistant integration pass only: no source capture, image download,
  rights upgrade, surface rebuild, or classification/deep-research change was
  performed.

Reason:

- The project log and feasibility note from 2026-06-03 fixed the first-version
  assistant model as `Qwen/Qwen3.5-0.8B`, with
  `onnx-community/Qwen3.5-0.8B-ONNX` as the local runtime artifact.
- The previous frontend adapter incorrectly introduced a Llama/WebLLM runtime
  example path. That contradicted the documented project rule and has been
  removed from runtime code.

Model/runtime rule:

- `Qwen/Qwen3.5-0.8B` is the only assistant generation model.
- `onnx-community/Qwen3.5-0.8B-ONNX` is the only frontend runtime artifact.
- No Llama model, WebLLM fallback model, hosted LLM API, or alternate local
  generation model is allowed in the assistant path.
- Normal Assistant mode and Research mode use the same Qwen3.5-0.8B session.
  Research mode only changes retrieval breadth and response structure; it is
  not a separate model and must not silently fall back to another runtime.

Implementation:

- Replaced the WebLLM/Llama adapter with a Qwen3.5 adapter aligned to the
  existing probes:
  `frontend/scripts/probe-qwen35-runtime.mjs` and
  `frontend/scripts/probe-qwen35-generation.mjs`.
- Added a binding clarification to
  `docs/system/LOCAL_WEBLLM_RAG_FEASIBILITY_v0.md` so the older model-family
  comparison cannot be read as permission to use Llama or any fallback runtime.
- Reused the already tested Transformers.js loading shape:
  `Qwen3_5ForConditionalGeneration`, `AutoTokenizer`, q4 token/decoder
  weights, fp16 vision encoder, and explicit ONNX external-data entries.
- Kept the model lazy-loaded on first actual assistant question so opening the
  panel does not immediately trigger a heavy local model load.

Retrieval and memory guardrails:

- Added a deterministic local archive-retrieval gate before model invocation.
  If no candidate archive evidence is retrieved, the UI returns an
  archive-limited answer without calling Qwen.
- Added same-page assistant memory with a 3-minute TTL, stored in
  `sessionStorage` and capped to the last 12 messages per page.
- The memory store clears after more than 3 page switches. It is conversation
  context only, not archive evidence, and it is not written back into the
  project database.
- The active `surfaceId` is now passed into the assistant open event so page
  memory and retrieval can use a stable object key.

Verification target:

- Runtime source scan should show no Llama/WebLLM adapter references in
  `frontend/src/lib`, `frontend/src/components`, or `frontend/scripts`.
- Historical documentation may still mention Llama or WebLLM as comparison
  background, but those names are not allowed in the current assistant runtime
  path.

Verification:

- `npm run build` passed in `frontend/`; Next generated 7914/7914 static pages.
  The familiar slow static-page retry warnings appeared, but the build exited
  successfully.
- `git diff --check` passed.
- Runtime source scan over `frontend/src/lib`, `frontend/src/components`, and
  `frontend/scripts` found no Llama/WebLLM adapter references.
- Local browser smoke test used `http://127.0.0.1:3040/folders/region/france`.
  Assistant rendered its chat textarea, did not overlap the bottom navigation,
  did not show `WEBLLM`, `Llama`, or `Load WebLLM`, and did not trigger
  Qwen/Hugging Face/ONNX model network requests before the user sends a
  question.
- Search still rendered as the separate search input in the same floating
  container.

## 2026-06-06 - Assistant Latency Diagnosis And Micro-Mode Correction

Scope:

- Investigated regular Assistant responses taking longer than 30 seconds.
- Frontend assistant runtime/configuration change only: no source capture,
  image download, rights upgrade, surface rebuild, or classification change was
  performed.

Diagnosis:

- The slow response is not caused by archive retrieval/search. The retrieval
  helper is local metadata ranking over the static payload.
- The project's earlier Qwen probe established the intended regular envelope:
  compact record/search micro-notes around 11.8-14.0 seconds after cached load,
  using compact slips and `max_new_tokens=12`.
- The integrated frontend had drifted away from that envelope:
  regular Assistant mode used `max_new_tokens=150`, selected 6 candidate
  records, and sent longer candidate notes.
- Transformers.js documentation and local package source also show that browser
  execution defaults to CPU/WASM unless WebGPU is explicitly selected or made
  available through the selected execution providers. Silent CPU/WASM behavior
  is unacceptable for this interactive assistant because it looks like the app
  is thinking while it is only running a slow local backend.
- Local browser capability check on `http://127.0.0.1:3040` confirmed
  `navigator.gpu=true`, secure context, 8 hardware threads, and 16 GB reported
  device memory, so WebGPU is available in the test browser.

Correction:

- Regular Assistant mode now uses a micro-answer budget:
  `max_new_tokens=48`, at most 3 retrieved candidates, and 120-character
  candidate notes.
- Research mode remains broader but was reduced to `max_new_tokens=180` and
  at most 10 candidates.
- The Qwen chat-template call now passes `enable_thinking=false` explicitly.
- The assistant model load now requires WebGPU and passes `device="webgpu"` to
  Transformers.js. If WebGPU is unavailable, the assistant fails fast instead
  of silently falling back to a very slow CPU-only experience.

Verification:

- `npm run build` passed in `frontend/`; Next generated 7914/7914 static pages.
  The familiar slow static-page retry warnings appeared, but the build exited
  successfully.

## 2026-06-06 - Research Assistant WebGPU Stabilization And Panel Split

Scope:

- Follow-up frontend correction after live review of the Russia reader,
  Assistant latency, and CONTENT/CONTEXT panel behavior.
- This pass did not run source capture, did not download images, did not
  rebuild archive data, did not change rights states, and did not perform any
  IMG01/IMG03 upgrade.

Qwen runtime correction:

- The assistant runtime now requires the text-only
  `Qwen3_5ForCausalLM` class from `@huggingface/transformers`.
- Removed the frontend fallback path to
  `Qwen3_5ForConditionalGeneration`, including the vision encoder dtype and
  `vision_encoder_fp16.onnx_data` external-data entry.
- `Qwen/Qwen3.5-0.8B` remains the only Assistant model identity, and
  `onnx-community/Qwen3.5-0.8B-ONNX` remains the only browser runtime
  artifact.
- The WebGPU memory error seen during Research was treated as a runtime
  session failure: the app now clears the cached Qwen session and asks the
  user to reload or retry after closing heavy tabs.

Assistant/RAG behavior:

- Regular Assistant mode still calls local Qwen, but now sends a much smaller
  fast evidence packet: one top archive lead, compact scope, and concise
  routing instructions instead of multiple long candidate records.
- Regular Assistant output is capped to 34 new tokens and instructed to return
  one complete short advisory sentence.
- Research mode keeps the broader evidence packet, but remains on the same
  Qwen3.5-0.8B text-only session; it is not a separate model or fallback.
- Same-page memory still lasts three minutes and clears after more than three
  page switches. Transient `Thinking...`, `Researching...`, and old preparation
  notices are filtered when loading or saving memory.

Reader UI changes:

- Split the left controls into `CONTENT` and `CONTEXT`, both using the same
  left-panel container.
- `CONTEXT` now owns the background context and full archive sequence that
  previously overloaded the content panel.
- `CONTENT` is now a compact relationship/navigation view only:
  - when the active main sheet has a main-sheet dossier, it shows that main
    sheet's internal packet nodes;
  - otherwise it shows the current main sheet plus up to two previous and two
    next main sheet names.
- CONTENT nodes are clickable navigation buttons and expose extra relationship
  details on hover/focus.
- Opening CONTENT/CONTEXT now closes the right-side Search/Assistant panel;
  opening Search/Assistant closes the left panel.
- The bottom Assistant launcher was renamed to `RESEARCH` and the whole
  bottom page-turn control was enlarged by about 10%.
- Removed the left-bottom visual-monitor badge and disabled the Next dev
  indicator overlay.
- Added vertical scroll containment for single-page cards/slips/sheets so tall
  image or text content can be inspected inside the card instead of being
  clipped by the viewport.
- Darkened global secondary ink and line colors to improve reading contrast.

Verification:

- `npm run build` passed in `frontend/`; Next generated 7914/7914 static pages.
  The familiar slow static-page retry warnings appeared, but the build exited
  successfully.
- `git diff --check` passed.
- Runtime scan over frontend source found no `Llama`, `WEBLLM`, `WebLLM`,
  `LOAD WEBLLM`, `vision_encoder`, `Qwen3_5ForConditionalGeneration`,
  `visual-check`, or `VIS OK` references.
- Commit-bound safety scan found no real API key, password, secret, bearer
  value, cookie assignment, local user path, or env-file reference. Remaining
  broad-scan hits were expected false positives in `transformers.env` and
  historical PROJECT_LOG scan descriptions.
- Local dev server was started at
  `http://127.0.0.1:3040/folders/region/russia?fresh=1`.
- Browser smoke confirmed the Russia page renders after a fresh reload, the
  old left-bottom monitor badge is gone, no Next issues overlay is visible,
  CONTENT and CONTEXT appear as separate left controls, the right-bottom
  launcher reads `RESEARCH`, and the Research panel stays above the page-turn
  control.
- Browser smoke confirmed CONTENT on the Russia register shows only nearby
  main sheets, and CONTENT on the first Russia main sheet shows the same
  nearby-main fallback because that surface does not yet have a main-sheet
  dossier sequence.

## 2026-06-07 - Independent Qwen RAG Research Repo Boundary

Scope:

- Recorded the browser-local Qwen RAG work as an independent research repo/lab
  direction, not an archive product branch.
- Added a Deep Research prompt for the separate research workflow around
  WebGPU/WebLLM/RAG optimization, evidence-packet compression, benchmark design,
  and possible paper framing.
- This archive repository keeps only boundary documentation and product-facing
  decision context. It does not contain the independent research repo code,
  benchmark outputs, model files, browser cache, or experiment fixture package.
- This pass did not change source capture, did not download images, did not
  rebuild surfaces, did not alter rights states, and did not perform any
  IMG01/IMG03 upgrade.

Boundary:

- Research runtime comparisons such as WebLLM/MLC, ONNX Runtime WebGPU,
  speculative RAG, MiniRAG-style retrieval, or KV-cache compression remain
  research-only until a later archive product decision accepts them.
- Archive product constraints remain fixed for now:
  `Qwen/Qwen3.5-0.8B` is the only Assistant model identity,
  `onnx-community/Qwen3.5-0.8B-ONNX` is the only browser runtime artifact,
  Search remains deterministic, and Assistant output is not archive evidence.

Files:

- `docs/system/WEBGPU_WEBLLM_RAG_RESEARCH_BRANCH_BRIEF_v0.md`

## 2026-06-13 - Commons Open Source Cleaning and Controlled Expansion Attempt

Scope:

- Cleaned the recent Commons open-source expansion lane before attempting the
  next source-count push.
- Added three new source-capture lanes:
  - `scripts/run_commons_open_authority_weighted_expansion_2026_v1.py`
  - `scripts/run_commons_open_controlled_expansion_2026_v1.py`
  - `scripts/run_commons_open_publication_category_tree_2026_v1.py`
- Added/updated cleaning scripts so recent Commons batches are audited and
  quarantined before any public rebuild:
  - `scripts/audit_commons_open_source_cleaning_2026_v1.py`
  - `scripts/apply_commons_open_source_cleaning_2026_v1.py`

Cleaning result:

- Prior recent Commons batches after cleaning: 5034 release-ready records.
- New raw records captured this round: 1427.
- New records removed by cleaning quarantine: 175 duplicate-review records.
- New release-ready records retained this round: 1252.
- Combined audited recent Commons row set after cleaning: 6286 release-ready
  rows, 0 remaining cleaning blockers.
- No image binaries, thumbnails, screenshots, raw API payloads, cookies,
  browser sessions, or local image files were downloaded.
- A token-like Medium URL fragment exposed through Commons metadata was removed
  from the source record/audit output, and the shared Commons capture `clean()`
  helper now strips token/session/password-style URL parameters before writing
  CSV fields.

New retained batch distribution:

- Authority-weighted expansion: 300 retained.
- Controlled expansion: 925 retained after 175 duplicate rows were removed.
- Publication category-tree trial: 27 retained.
- Object families across retained new rows: advertising 476; postage stamp
  353; label/packaging 118; poster 91; typography/identity 63; magazine cover
  47; book cover 41; brochure/pamphlet 31; film poster 22; political poster 6;
  travel poster 4.
- Period distribution across retained new rows: pre-1940 500; 1940-1970 406;
  1970-2000 143; 2000-2026 203.
- Macro-region distribution across retained new rows: Latin America 376;
  Global fallback 357; Middle East and North Africa 127; Oceania 120;
  Southeast Asia 73; Eastern Europe 68; East Asia 48; South Asia 47; Africa
  33; Central Asia 3.

Capture note:

- The requested 5000-new-source target was not reached. After de-duplicating
  against existing capture batches, Commons open/source-visible records with
  usable object-year evidence entered a long-tail zone: broad search,
  year-category, country/alias, authority-weighted, and publication-category
  lanes all showed sharply declining yield.
- Continuing the same Commons strategy would likely add hours of low-yield
  crawl time while increasing Global fallback and duplicate pressure. The next
  large expansion should switch toward non-Commons institutional APIs and
  source-specific adapters, especially Cooper Hewitt, Wellcome, DPLA/CONTENTdm,
  national libraries, art schools, community archives, and rights-clear
  publication collections.

Gate snapshot:

- Record-level layered image/source metrics now see 15121 capture records.
- Record-level source-visible rate: 98.04%.
- Record-level open image rate: 85.57%.
- Record-level weighted publication rate: 93.34%.
- Existing public-surface release snapshot remains at 13680 surfaces because
  this round did not safely commit a full surface rebuild.
- Existing public-surface object source-visible rate: 97.91%.
- Existing public-surface object verified-open rate: 87.96%.
- Existing public-surface object IMG04 rate: 1.78%.
- Existing public-surface weighted publication rate: 93.36%, below the 95%
  target by 223.4 weighted points.
- Sheet topology remains weak: 13419 main sheets, 247 sub sheets, 242 text
  sheets; 359 main sheets have more than two sub sheets, and only 5 main sheets
  have more than five text sheets.

Build/rebuild boundary:

- The four generated public-surface JSON files are tracked and currently about
  136MB each, above GitHub's normal 100MB push safety threshold for new blobs.
  A full surface rebuild was therefore not staged in this round. The next
  infrastructure task should shard or compress public-surface exports before
  requiring every source-capture iteration to rebuild and commit the frontend
  payload.

Next capture strategy:

- Prioritize source-specific adapters over broader Commons searching.
- Highest weighted-publication gap sources: Cooper Hewitt, Wellcome, Library of
  Congress, Georgia State University CONTENTdm, Art Institute of Chicago,
  Internet Archive, V&A, Te Papa, DigitalNZ, NAIDOC, Princeton Figgy, and The
  Met.
- For the 20000-source launch target and the stricter 99% source-visible / 95%
  verified-open goals, the next round should first convert high-volume IMG02
  and IMG04 blockers into verified open or source-visible states where source
  terms support it, then add new institutional sources only where authority and
  rights evidence are explicit.
- Verification for this round: cleaning audit passed with 6286/6286
  release-ready rows; `python3 -m py_compile` passed for the new/updated
  cleaning, capture, release-gate, layered-metrics, base Commons, and rebuild
  scripts; `git diff --check` passed; a targeted credential scan found no real
  credential values in commit-bound files. Remaining scan hits are regex policy
  text in the sanitizers and historical log wording.

## 2026-06-13 - Project State Assessment and 12h Optimization Plan

Scope:

- Recorded the current project-state assessment and the expected order for the
  next long optimization pass.
- This is a planning/decision record only; no rights state, taxonomy, capture
  payload, surface payload, or frontend runtime was changed by the assessment.

Assessment:

- Current active public sources: 12,342; launch target is 20,000 active public
  sources, not merely raw capture rows.
- Public surfaces: 13,680; capture records: 15,121.
- Object source-visible is close to the new 99% target at 97.91%.
- Object verified-open is the largest gate gap at 87.96% against the new 95%
  target.
- Object weighted publication-grade is 93.36% against the 95% target.
- Object IMG04 remains controlled at 1.78%.
- Strict distribution-adjusted source coverage remains weak at 28.96%, with
  region quality-main balance at 6.47%.
- Sheet topology remains structurally immature: 13,419 main sheets, 261
  sub/support surfaces, 242 independent text sheets, and 351 strong grouping
  candidates.

Optimization expectations:

- First fix public-surface payload size and sharding/build safety.
- Then clarify release source-count semantics around active public sources.
- Then repair verified-open and weighted-publication gaps in high-authority
  source families before another broad capture push.
- Then reduce unresolved/global-fallback geography and begin research-packet
  restructuring from strong grouping candidates.

File:

- `docs/capture/PROJECT_STATE_ASSESSMENT_AND_12H_OPTIMIZATION_PLAN_2026_06_13.md`

## 2026-06-12 - Commons Open Source Expansion And Gate Recheck

Scope:

- Continued the long-running source expansion track with a Commons-only,
  rights-aware metadata capture round aimed at adding roughly 5000 open source
  records before reassignment, cleaning, rebuild, and gate checks.
- The capture remained source-discovery and source-evidence oriented. It saved
  CSV metadata, source links, Commons page identifiers, source-hosted image URLs,
  dates, region/macro-region labels, and rights evidence. It did not download
  image binaries, screenshots, raw API payload dumps, cookies, or browser state.
- IMG03 was assigned only from Wikimedia Commons open-license extmetadata. No
  IMG01/IMG03 upgrade was made from heuristics, LLM judgment, terms-of-service
  inference, or platform-level assumptions.

New capture:

- `run_commons_open_category_tree_image_capture_2026_v1.py` captured 4544
  distinct active source records from Commons country/category trees. It did not
  reach its standalone 5000-row target because the useful queue was exhausted
  after macro, period, duplicate, object-type, and weak graphic-evidence filters.
- Category-tree quality summary:
  - 4544 records, 4544 distinct active source names.
  - IMG03: 4544.
  - 2026 count: 6, or 0.13 percent. No 2026 concentration bug was observed.
  - Period distribution: 2000-2026 1700; 1930-1970 1200; 1970-2000 844;
    pre-1930 800.
  - Macro-region distribution: Africa 819; Latin America 800; MENA 650;
    Southeast Asia 605; Eastern Europe 450; South Asia 338; Central Asia 320;
    Oceania 307; East Asia 255.
  - Largest country fills include Bolivia 300, Indonesia 300, Algeria 276,
    Kazakhstan 274, India 261, Iran 227, Iraq 222, Brazil 152, Aotearoa New
    Zealand 152, Philippines 142, Australia/Indigenous 105, Romania 102, China
    100, Morocco 98, Turkey 96, South Africa 83, Korea 80, Azerbaijan 80, Kenya
    73, Ukraine 72, Vietnam 71, Mexico 68, Pakistan 60, Poland 57, Cuba 57,
    Malaysia 53, Uruguay 52, Serbia 51, Zimbabwe 50, Croatia 45, Peru 45,
    Colombia 43, Tunisia 42, Palestine 41, Egypt 40, Hong Kong 40, Angola 38,
    Taiwan 35, Venezuela 33, Tanzania 30, Jordan 30, Papua New Guinea 30,
    Uzbekistan 28, Nigeria 27, and Lebanon 25.
- `run_commons_open_region_balance_image_capture_2026_v3.py` was kept as a
  smaller search-based supplement and captured 500 additional distinct active
  source records after category-tree capture.
- Region-balance v3 quality summary:
  - 500 records, 500 distinct active source names.
  - IMG03: 500.
  - 2026 count: 3, or 0.60 percent. No 2026 concentration bug was observed.
  - Period distribution: 2000-2026 354; 1930-1970 67; 1970-2000 44;
    pre-1930 35.
  - Macro-region distribution: Southeast Asia 315; Eastern Europe 79; MENA 30;
    South Asia 30; East Asia 21; Africa 16; Latin America 6; Central Asia 3.
- Combined new open-source metadata records for this round: 5044.

Rebuild and release checks:

- `rebuild_public_surfaces_from_records.py` completed:
  - rows: 13800.
  - public surfaces: 13680.
  - folders: 97.
  - image states: IMG00 43; IMG01 37; IMG02 1327; IMG03 12015; IMG04 258.
  - source-visible image-ready surfaces: 13379/13680, or 97.8 percent.
  - weighted publication image score: 11554.45/13680, or 84.46 percent.
- `run_release_snapshot_v1.py`:
  - public surfaces: 13680.
  - active public sources: 12342.
  - object source-visible rate: 97.91 percent, passing the 96 percent gate.
  - object verified-open rate: 87.96 percent, passing the 85 percent gate.
  - object IMG04 rate: 1.78 percent, passing the current under-10 percent gate.
  - release source target: passing, with 12342 active sources against the 2000
    minimum target.
  - weighted publication-grade image coverage: 84.57 percent, still failing the
    95 percent target and requiring about 1424.9 additional weighted points.
  - 2026 surface rate: 0.39 percent, passing the year sanity check.
- `audit_image_release_gate.py` confirmed the same gate shape: source-visible,
  verified-open, IMG04, and source-count gates pass; weighted publication-grade
  image coverage remains the release blocker.
- `audit_source_coverage_rate_v2.py` remains a critical caution:
  - source pool period fill rate: 100.00 percent.
  - strict distribution-adjusted source coverage rate: 28.96 percent.
  - region surface balance rate: 6.71 percent.
  - region quality main balance rate: 6.26 percent.
  - research quality adjusted source coverage rate v2: 2.39 percent.
  This confirms that raw source quantity is now far ahead of region-quality
  balance and research packet quality.

Sheet and assignment state:

- `audit_public_surface_sheet_counts_v1.py`:
  - main sheets: 13419.
  - sub sheets: 247.
  - independent text sheets: 242.
  - inferred parent main sheets: 455.
  - main sheets with more than two sub sheets: 359.
  - main sheets with more than five text sheets: 5.
- `audit_surface_assignment_gates_v1.py` still classifies most records as
  main-sheet candidates: main_sheet_candidate 12946; subsheet_visual 522;
  text_sheet_candidate 198; dedupe_child_record 60; appendix_or_text_sheet 55;
  subsheet_text_or_appendix_review 37; subsheet_group_child 22;
  subsheet_or_group_anchor_review 18; img00_rights_sheet_candidate 16;
  duplicate_image_review_packet 5; group_review 105.
- `audit_main_sheet_research_value_v1.py` shows the current main/sub/text
  topology is still structurally immature: demote_to_sub 9523; keep_main 3617;
  promote_text_or_appendix 189; demote_to_card 58; keep_main_add_editorial_text
  32. This is an audit signal only, not an automatic demotion action.

Build and verification:

- Python compile passed for:
  - `scripts/run_commons_open_category_tree_image_capture_2026_v1.py`
  - `scripts/run_commons_open_region_balance_image_capture_2026_v3.py`
  - `scripts/rebuild_public_surfaces_from_records.py`
- `git diff --check` passed.
- `npm run build` at repository root is not defined.
- `npm run build` inside `frontend/` compiled successfully, then failed during
  static page generation with `ENOSPC: no space left on device, write` while
  prerendering `/folders/region/unresolved-region` after generating
  10353/13805 static pages. This is a static-export scale and disk-capacity
  blocker, not a TypeScript compile failure. The frontend now needs a sandboxed
  or partial-build validation mode before further large capture rounds.
- The rebuilt surface JSON exports were generated locally, but each full export
  is now about 136 MB. They are intentionally not included in the GitHub-bound
  commit because they exceed GitHub's 100 MB blob limit and should be handled by
  regeneration, sharding, compression, or an artifact strategy before the next
  large public build.
- Repository-wide secret scan still reports old raw-file URL parameter hits in
  previously existing raw probe files. These are not from this round. The
  commit-bound scan for this round must remain limited to staged files.
- Commit-bound scan over the new scripts, generated CSV/JSON/Markdown reports,
  audit outputs, and this log found no real API key, bearer value,
  password/secret assignment, cookie/session assignment, private key block,
  local user path, or environment-file payload. Broad hits were false positives
  in policy/log wording or public source titles such as "Secret", "Secretary",
  and "poster session".

Next priorities:

- Push weighted publication-grade coverage upward before another pure source
  count push. Highest weighted-gap sources are Cooper Hewitt, Wellcome, LOC,
  GSU CONTENTdm, Art Institute, Internet Archive, V&A, DigitalNZ, Gallica,
  Te Papa, NAIDOC, Princeton, Met, and Wikimedia Commons residual duplicate or
  weak cases.
- Focus capture and source verification on 1930-1970 and 2000-2026, where
  weighted image coverage remains the most visible release gap.
- Continue region-quality balancing rather than only adding records. Africa,
  Latin America, MENA, Central Asia, South Asia, Southeast Asia, Oceania, and
  underrepresented East Asia need higher-quality anchors, not only more
  individual source rows.
- Treat main/sub/text restructuring as a separate information-architecture
  cycle. The current evidence supports auditing and grouping work, but not a
  blind automatic demotion of thousands of main sheets.

## 2026-06-12 - Region-Balanced Commons Capture v2 and Surface Gate Rebuild

Scope:

- Ran the next archive data round as a longer autonomous capture/repair/rebuild
  cycle focused on non-mainstream and low-coverage region balance.
- Added a region-balanced Wikimedia Commons open-image capture path for
  source-visible IMG03 records and connected it to the public-surface rebuild
  through the capture-run manifest.
- Strengthened the public region fallback mapping used by the midcentury capture
  utilities so explicit source-place strings such as Nigeria, Ghana, Iran,
  Bangladesh, Indonesia, Kazakhstan, Uruguay, and Aotearoa New Zealand do not
  collapse into unresolved regions during later rebuilds.

Capture repair notes:

- The first Python urllib Commons request failed inside the sandbox with DNS
  resolution errors, while `curl -I` against Commons succeeded. The capture was
  rerun with approved network escalation.
- An early v2 pass was rejected as too noisy because the relevance filter could
  self-confirm against project-assigned fields. The script was patched so
  graphic-design relevance is checked only against source-derived evidence
  fields such as source title, Commons description, source notes, and source
  categories.
- The final strict run saved 800 records and 799 distinct active source names.
  All records are IMG03 open-image metadata records.
- No image binaries, screenshots, raw API payload dumps, cookies, sessions, or
  credential-bearing files were downloaded or saved.
- No IMG01 or IMG03 rights upgrade was performed by heuristic, LLM inference,
  terms-of-service language, or platform signal. IMG03 rows are backed by
  Commons open-license metadata and preserved as source-discovery/item records.

Final v2 capture distribution:

- Periods: 2000-2026 = 451; 1930-1970 = 134; 1970-2000 = 125; pre-1930 = 90.
- Macro-regions: Eastern Europe = 168; Middle East and North Africa = 150;
  Southeast Asia = 144; Africa = 94; Central Asia = 80; East Asia = 80;
  South Asia = 71; Latin America = 12; Oceania = 1.
- Rejections: base filter = 8686; weak graphic evidence = 1339; duplicate =
  908; distribution cap = 218; non-graphic object = 83.
- Query failures: 76, mostly HTTP 429 rate limits from Commons. These were
  logged as capture limits rather than converted into local raw payloads.
- Source-derived text quality floor: minimum 113 characters; median 308
  characters.

Surface rebuild:

- Rebuilt public surfaces from the manifest-extended source record set.
- Public surfaces: 8636.
- Folders: 96.
- Surface image states: IMG00 = 43; IMG01 = 37; IMG02 = 1327; IMG03 = 6971;
  IMG04 = 258.
- Source-visible image-ready surfaces: 8335/8636 = 96.51%.
- Weighted publication image score: 7014.85/8636 = 81.23%.

Release and audit metrics:

- Active public source names: 7298, above the 2000 release source target.
- Release source coverage rate: 364.90%, above the minimum 80% target.
- Object source-visible rate: 96.68%, passing the 96% gate.
- Object verified-open rate: 80.92%, below the 85% gate.
- Object weighted publication-grade image rate: 81.39%, below the 95% gate.
  This object-level calculation counts repeated photos/views only once.
- Object IMG04 rate: 2.82%, currently under the working 10% maximum.
- 2026 surface rate: 0.51%; post-2026 or future-date error count: 0.
- Strict distribution-adjusted source coverage rate remains 28.96%.
- Region surface balance rate is 6.48%; region quality main balance is 6.26%.
- Research-quality adjusted source coverage v2 is 2.35%, confirming that broad
  source count is now ahead of region-quality and dossier-quality structure.

Sheet and research-packet topology:

- Main sheets: 8379.
- Sub sheets: 243.
- Independent text sheets: 242.
- Inferred parent main sheets: 455.
- Main sheets with more than two sub sheets: 359.
- Main sheets with more than five text sheets: 5.
- Assignment audit dispositions: main_sheet_candidate = 7933; subsheet_visual =
  491; text_sheet_candidate = 198; dedupe_child_record = 60;
  appendix_or_text_sheet = 55; group review = 105.
- Main-sheet research value audit actions: demote_to_sub = 4960; keep_main =
  3211; promote_text_or_appendix = 189; demote_to_card = 15;
  keep_main_add_editorial_text = 4.
- This confirms that the archive has enough object/source mass to continue
  building, but many current main sheets are still object records rather than
  fully formed research packets.

Integrity and gate findings:

- IMG state contract passed.
- Public surface integrity found 6 exact repeated image URL groups affecting 12
  surfaces. These are reviewable grouping/dedupe candidates, mostly from
  Another Graphic and Barjeel, not a rebuild failure.
- Image release gate fails only on verified-open and weighted publication-grade
  targets. The biggest weighted blockers are Cooper Hewitt, Wellcome, Library of
  Congress, Georgia State University Digital Collections, Art Institute of
  Chicago, Internet Archive, V&A, DigitalNZ, Gallica, Te Papa, and NAIDOC.
- Period priority now ranks 1930-1970 highest for next capture repair because it
  has the largest source gap and still needs stronger image/open evidence.
  2000-2026 also remains important because its weighted image coverage is only
  70.65% despite good source count.

Next recommended round:

- Do not run a broad random Commons pass first. Target the verified-open and
  weighted publication gaps by upgrading or replacing blocker source families
  with explicit open-image evidence, especially Cooper Hewitt, Wellcome, LOC,
  GSV/CONTENTdm, DigitalNZ, Te Papa, NAIDOC, Gallica, V&A, and Art Institute of
  Chicago.
- Continue low-coverage region work, but bias toward Latin America, Oceania, and
  underfilled Africa/South Asia subsets because this v2 pass still skewed toward
  Eastern Europe, MENA, and Southeast Asia after strict filtering.
- Add a dedupe/grouping pass for repeated-image records and a research-packet
  classification pass before any large main/sub demotion is applied.

Files:

- `scripts/run_commons_open_region_balance_image_capture_2026_v2.py`
- `scripts/run_midcentury_capture_1930_1970.py`
- `scripts/rebuild_public_surfaces_from_records.py`
- `data/capture_batch_commons_open_region_balance_image_2026_v2_records.csv`
- `data/capture_batch_commons_open_region_balance_image_2026_v2_source_summary.csv`
- `data/commons_open_region_balance_image_2026_v2_quality.csv`
- `data/capture_runs/capture_run_manifest_v1.csv`
- `docs/capture/COMMONS_OPEN_REGION_BALANCE_IMAGE_CAPTURE_2026_v2.md`
- `generated/public_surfaces_v1.json`
- `data/public_surface_mock_v0.json`
- `frontend/public/data/public_surface_mock_v0.json`
- `frontend/src/data/public_surface_mock_v0.json`
- Updated release, coverage, image, sheet topology, assignment, and integrity
  audit outputs under `data/` and `docs/capture/`.

## 2026-06-10 - Region/Geography Enrichment Confidence Gate v1

Scope:

- Region/geography normalization audit only.
- No source capture, image download, image-rights upgrade, public surface
  rebuild, taxonomy rewrite, or automatic mapping application was performed.
- The work converts local enrichment suggestions into reviewable confidence
  tiers so the 3,900 pending geography records are no longer treated as one
  opaque backlog.

Inputs:

- `data/region_geography_normalization_candidates_v1.csv`
- `data/region_conflict_direct_parse_v1.csv`
- `data/region_conflict_historical_split_suggestions_v1.csv`
- `data/region_pending_geo_text_suggestions_v1.csv`

Outputs:

- `scripts/score_region_geo_enrichment_confidence_v1.py`
- `scripts/wikidata_region_geo_factcheck_v1.py`
- `scripts/build_region_geo_safe_apply_review_lists_v1.py`
- `data/region_geo_enrichment_with_confidence_v1.csv`
- `data/region_geo_auto_apply_ready_v1.csv`
- `data/region_geo_wikidata_validation_v1.csv`
- `data/region_geo_ready_for_auto_apply_v1.csv`
- `data/region_geo_priority_manual_review_v1.csv`
- `data/region_geo_requires_historical_split_review_v1.csv`
- `docs/capture/REGION_GEO_SAFE_APPLY_REVIEW_LIST_v1.md`

Results:

- Scored enrichment suggestions: 1,373.
- Suggestion sources:
  - pending text resurfacing: 803
  - direct conflict parse: 342
  - historical split: 228
- Confidence distribution:
  - high: 88
  - medium: 1,137
  - low: 148
- Safe queue distribution:
  - ready for auto apply: 88
  - priority manual review: 1,057
  - historical split review: 228
- Auto-apply label distribution:
  - Brazil: 30
  - Mexico: 28
  - Argentina: 17
  - Egypt: 7
  - Chile: 3
  - Germany: 1
  - South Africa: 1
  - Turkey: 1
- Historical split review distribution:
  - Mexico; United States military occupation context: 220
  - France; wartime occupation/state-context review: 4
  - Russia / USSR contexts; republic-specific review: 3
  - Germany; East/West Germany review: 1

Interpretation:

- The 248 Mexico direct conflict parse suggestions remain valuable, but most
  Matamoros / American Flag records fall in 1846 and are now blocked from
  automatic application by the historical dispute gate.
- Pending text resurfacing is useful for prioritizing review, especially the
  large Indonesia, Caucasus, Azerbaijan, Georgia, and Singapore clusters, but it
  remains review-only because topic geography, publisher geography, and source
  geography can be mixed in those fields.
- The Wikidata fact-check script is installed as an optional external evidence
  layer with cache and query limits. It was run in default dry-run mode only:
  909 medium-confidence candidates were enumerated, 0 network queries were
  performed, and all external validation states remain `unchecked`.
- The strict gate intentionally produces only 88 automatic candidates in this
  pass. That is conservative, but safer than applying date-sensitive or
  low-signal records into public region statistics.

Verification:

- `python3 -m py_compile` passed for the new confidence, Wikidata fact-check,
  safe-list, and upstream region/geography enrichment scripts.
- `git diff --check` passed for the updated log, new scripts, and generated
  safe-list report.
- The project-wide `scripts/audit_secret_patterns.py` still exits non-zero on
  older raw HTML probe files with third-party URL key parameters. Those files
  are unrelated to this region/geography pass and remain outside the safe
  commit set.
- A targeted credential/path scan over the new region/geography scripts, CSVs,
  and report found no real API key, bearer value, password/secret assignment,
  cookie assignment, local user path, or env-file reference.

## 2026-06-10 - Region/Geography Cleaning Plan And Next Capture Plan v1

Scope:

- Data cleaning optimization and next capture planning only.
- No source probe, remote capture, image download, image rights upgrade,
  taxonomy rewrite, public surface rewrite, or frontend build was performed.
- `research-repo/` remains an independent research repository and is read-only
  from the archive product workflow.

Changes:

- Added `scripts/build_region_geo_cleaning_plan_v1.py` to convert the scored
  enrichment queues into a dry-run cleaning action plan and compressed manual
  review clusters.
- Added `scripts/generate_next_capture_plan_v1.py` to turn the cleaning
  findings into a next-cycle capture plan with source strategy, rights
  preference, text requirements, cleaning dependencies, and validation gates.

Outputs:

- `data/region_geo_cleaning_action_plan_v1.csv`
- `data/region_geo_manual_review_clusters_v1.csv`
- `data/next_capture_plan_v1.csv`
- `docs/capture/REGION_GEO_CLEANING_PLAN_v1.md`
- `docs/capture/NEXT_CAPTURE_AND_CLEANING_PLAN_v1.md`

Results:

- Region/geography cleaning action rows: 88.
- Batch-ready after sample audit: 64.
- Spot-check before apply: 24.
- Manual review rows compressed into clusters: 64.
- Largest manual clusters:
  - Indonesia: 381
  - Mexico historical/date-sensitive review: 220
  - Caucasus: 64
  - Azerbaijan: 39
  - Georgia: 38
  - Singapore: 31
- Next capture plan rows: 8.
- Planned next-cycle tracks:
  - P0 region/geography safe apply review
  - P0 Mexico / United States military occupation historical split policy
  - P1 Southeast Asia modern/contemporary expansion
  - P1 Caucasus/Central Asia repair
  - P1 South Asia country-level expansion
  - P1 MENA/Sub-Saharan Africa noncanonical expansion
  - P2 Latin America cleanup and growth
  - P2 classification deep-research inputs

Interpretation:

- The stricter cleaning layer found that 24 of the 88 high-confidence candidates
  still need spot-checking because the title contains the current country or
  another country label, or because the year is missing. These are not rejected;
  they are moved out of direct batch-application until a human sample audit
  confirms the correct geography basis.
- The remaining 64 action rows are still dry-run patch candidates, not applied
  mappings. They should be sampled by label/source family before any batch
  relabel script is written.
- The next capture cycle should begin after this first cleaning pass so new
  source work inherits stricter region/geography and text-value rules.
- Data cleaning and capture are now coupled: source discovery alone is not
  enough; new success counts must still pass item/image capture, surface build,
  archive incorporation, source-visible/source-coverage/IMG-rate metrics, and
  text-value review.

Verification:

- `python3 -m py_compile` passed for the new cleaning-plan and next-capture
  planning scripts.
- `git diff --check` passed for the updated log, new scripts, CSVs, and
  reports.
- Targeted credential/path scan over the new cleaning/capture plan scripts,
  CSVs, and reports found no real API key, bearer value, password/secret
  assignment, cookie assignment, local user path, or env-file reference.
- `prompts/DEEP_RESEARCH_WEBGPU_WEBLLM_RAG_OPTIMIZATION_PROMPT.md`

## 2026-06-07 - Assistant RAG Timing And Humanized Fast Answers

Scope:

- Product Assistant optimization pass only.
- No source capture, image download, surface rebuild, model switch, hosted
  inference, LoRA integration, rights-state change, or IMG01/IMG03 upgrade was
  performed.

Changes:

- Added per-question development timing for Assistant and Research in
  `frontend/src/components/archive/shell/search.tsx`.
- Timing logs now capture retrieval time, model preparation time, Qwen ask time,
  total time, candidate count, evidence size, intent, status, prompt chars,
  input tokens, generated tokens, tokenization time, generation time, and decode
  time when Qwen returns successfully.
- Development timing is stored on `window.__archiveAssistantTimings` and logged
  with `[archive-assistant timing]`; it is not visible archive UI chrome.
- Fast Assistant now blocks no-evidence questions before Qwen invocation, using
  a scoped fallback route instead of asking the model to guess.
- Explicit region/date scopes are now strict: if a query such as a specific
  region plus exact year has no candidates, retrieval does not fall back to a
  weak fuzzy match outside that scope.
- Fast Qwen prompt gained compact style examples for first/earliest,
  recommendation, and archive-orientation answers.
- Fast generation cap increased from 34 to 44 new tokens to reduce incomplete
  one-sentence answers while keeping the short-answer contract.
- `docs/system/ASSISTANT_RESPONSE_STRATEGY_v0.md` now records that LoRA/fine
  tuning is deferred until a reviewed answer fixture set and latency baseline
  exist; current failures are treated as RAG orchestration and prompt-contract
  issues first.

Verification:

- `npm run build` passed in `frontend/`; Next generated 7914/7914 static pages.
  The existing static-page timeout retry warnings appeared, then the build
  completed successfully.
- `git diff --check` passed.
- Local HTTP smoke:
  - `http://127.0.0.1:3040/folders/region/russia?fresh=assistant-pass`
    returned 200.
  - `http://127.0.0.1:3040/surfaces/SURF-GAX1970R001?fresh=assistant-pass`
    returned 200.
- Commit-bound safety scan found no real API key, password, secret, bearer
  value, cookie assignment, local user path, or env-file reference. Remaining
  hits are expected false positives such as tokenizer/max-token identifiers,
  token metrics, session wording, `transformers.env`, and historical log scan
  terms.

## 2026-06-08 - Independent Research Repo Shared Results Log

Scope:

- Work on browser-local Qwen/WebGPU/WebLLM/RAG benchmarking continued in the
  separate research repository, not in the archive product runtime.
- The research repo advanced the Round 03 experiment line around 300-query
  controlled-condition testing, contract validation, latency triage, and a
  50-query performance pilot set for later optimization variants.
- The research direction identified a useful hybrid-lane hypothesis:
  deterministic or UI/rule-managed lanes such as refusal and source/rights
  reporting should be measured separately from Qwen free generation, because
  they may improve latency and reliability without claiming improved model
  generation ability.

Archive repository boundary:

- No archive source capture, raw evidence ingestion, frontend Assistant UI
  change, product runtime change, model swap, rights-state change, image
  download, or surface rebuild was performed in this repository as part of that
  research work.
- Research outputs from 2026-06-08 are treated as shared results only. They may
  inform later archive product decisions, but they do not modify archive product
  constraints or implementation by themselves.
- The archive repo should continue to record only boundary decisions and
  product-facing implications from the research repo, not the research repo's
  experimental code, benchmark artifacts, browser cache, or model files.

Follow-up:

- Continue Round 03 as a performance-and-usability optimization experiment
  rather than opening Round 04 prematurely.
- Produce a separate hybrid-lane report if the deterministic source/rights and
  refusal-lane evidence remains strong after pilot testing.

## 2026-06-09 - Research Repo Read-Only Separation Constraint

Decision:

- The browser-local Qwen/WebGPU/WebLLM/RAG research work now lives in a fully
  separate research repository, with its own research branch and commit history.
- The archive product repository and the research repository remain independent
  working trees. They may share results, but they must not share write access
  during normal task execution.

Constraint:

- Archive-product work may read research outputs, reports, benchmark summaries,
  and explicitly exported fixtures from the research repo, but must not edit,
  stage, commit, or push files inside that repo.
- Research-repo work may read archive metadata/text/source/rights/image-state
  exports that are explicitly shared for experiments, but must not alter archive
  product runtime code, capture flows, Assistant UI, product constraints, or
  source evidence.
- Shared material should move as documented reports, small explicit exports, or
  cited summaries. Do not cross-stage untracked files between repositories or
  treat one repo's working tree as part of the other.
- Any research finding proposed for the archive product requires a later product
  decision record before implementation in this repository.

Files:

- `docs/system/WEBGPU_WEBLLM_RAG_RESEARCH_BRANCH_BRIEF_v0.md`

## 2026-06-13 - Public Surface Payload Sharding v1

Scope:

- Began the long release-gate optimization round from the 2026-06-13 project
  state assessment.
- This pass addressed build and audit safety only. It did not change public
  source records, rights states, IMG01/IMG03 upgrade policy, source coverage,
  frontend rendering behavior, or research-repo files.

Findings:

- Current canonical public payload remains
  `generated/public_surfaces_v1.json`, size 135.98 MiB.
- Payload size is concentrated in `surfaces` and `researchDossiers`:
  `surfaces` has 13,680 rows and about 104.62 MiB; `researchDossiers` has
  13,680 rows and about 23.24 MiB.
- The size concentration confirms that later full rebuilds should avoid
  treating the monolithic JSON import as the only frontend data primitive.

Changes:

- Added `scripts/shard_public_surface_payload_v1.py`.
- The script creates deterministic sidecar shards for the canonical public
  payload, plus manifest/index files for future lazy loading.
- `scripts/rebuild_public_surfaces_from_records.py` now emits the sidecar shard
  roots after writing the existing monolithic payload, while preserving all
  legacy payload paths.
- Added `.gitignore` entries for the generated shard directories so the archive
  repository does not commit a second 140 MiB copy of data already represented
  by the canonical payload.
- Added `data/public_surface_payload_sharding_v1.csv` and
  `docs/capture/PUBLIC_SURFACE_PAYLOAD_SHARDING_v1.md`.

Shard result:

- Output roots generated locally:
  `generated/public_surfaces_v1_shards` and
  `frontend/public/data/public_surface_shards_v1`.
- Each output root contains 73 files.
- Largest generated shard/section is 4.52 MiB.
- `surfaces`: 13,680 rows across 28 shards.
- `researchDossiers`: 13,680 rows across 28 shards.
- `registrationCards`: 97 rows across 4 shards.
- Manifest paths are relative to the shard root (`sections/...` and
  `indexes/...`) so later frontend fetch logic can consume them without
  repository-path coupling.

Verification:

- `python3 -m py_compile scripts/shard_public_surface_payload_v1.py
  scripts/rebuild_public_surfaces_from_records.py` passed.
- `python3 scripts/shard_public_surface_payload_v1.py` passed.
- No image files, thumbnails, screenshots, raw third-party payloads, cookies, or
  sessions were created.

Next:

- Keep the monolithic payload canonical for release audits until the frontend
  data layer is migrated.
- Next optimization step should formalize release-gate/source-count semantics
  and then prioritize rights/open-image repair before another large capture run.

## 2026-06-13 - Release Gate Contract v2

Scope:

- Formalized the updated launch gate after the project target moved from the
  earlier 2,000-source milestone to a 20,000 public-active-source launch target.
- This pass changed gate thresholds and reports only. It did not capture new
  sources, rebuild surfaces, download images, alter rights states, or edit
  research-repo files.

Gate contract:

- Public active source target: 20,000.
- Minimum public source coverage: 80%.
- Object source-visible target: at least 99%.
- Object verified-open target: at least 95%.
- Object weighted publication-grade image target: at least 95%.
- Object IMG04 cap: at most 10%.
- Future date errors: 0.

Source-count semantics:

- `archive_active_public_sources` is now documented as the launch-facing source
  count: distinct public `sourceName` values present in the generated public
  payload after rebuild.
- `capture_distinct_source_count`, source-prospect rows, and pre-surface source
  registries remain diagnostics. They do not count as successful release
  sources until item/source evidence becomes part of the public payload.
- This resolves the earlier misleading 100%/617% style source coverage signal:
  the old 2,000-source capacity target was obsolete.

Changed files:

- `scripts/audit_source_coverage_rate_v1.py`
- `scripts/run_release_snapshot_v1.py`
- `scripts/audit_image_release_gate.py`
- `docs/capture/RELEASE_GATE_CONTRACT_v2.md`
- Refreshed `data/source_coverage_rate_v1.csv`,
  `data/source_coverage_period_breakdown_v1.csv`,
  `data/source_coverage_region_breakdown_v1.csv`,
  `data/source_coverage_rate_v2.csv`,
  `docs/capture/SOURCE_COVERAGE_RATE_v1.md`,
  `docs/capture/SOURCE_COVERAGE_RATE_v2.md`,
  `data/release_snapshot_v1.csv`, and
  `docs/capture/RELEASE_SNAPSHOT_v1.md`.

Current baseline under v2 gate:

- Public surfaces: 13,680.
- Archive active public sources: 12,342 / 20,000 = 61.71%.
- Capture distinct source count: 13,560.
- Source pool period fill rate: 51.45%.
- Strict distribution-adjusted source coverage: 15.62%.
- Research-quality adjusted source coverage v2: 1.44%.
- Object source-visible: 97.91%.
- Object verified-open: 87.96%.
- Object weighted publication-grade image rate: 93.36%.
- Object IMG04: 1.78%.
- Future-date errors: 0.

Gate result:

- Failing: public active source coverage, source pool period fill, strict
  distribution-adjusted source coverage, research-quality adjusted source
  coverage, object source-visible, object verified-open, and object weighted
  publication-grade image rate.
- Passing: object IMG04 cap and future-date sanity.

Immediate priorities from the updated gate:

- Add at least 3,658 public-payload-ready sources to reach the 80% source
  minimum and about 7,658 to reach the full 20,000-source target.
- Prioritize rights/open-image repair for top weighted-gap families:
  Cooper Hewitt, Wellcome, Library of Congress, Georgia State CONTENTdm, Art
  Institute of Chicago, Internet Archive, V&A, Te Papa, DigitalNZ, NAIDOC,
  Princeton/Figgy, and The Met.
- Continue regional normalization and research-packet grouping before relying
  on source volume alone, because strict distribution and research-quality
  adjusted coverage remain very low.

Verification:

- `python3 -m py_compile scripts/audit_source_coverage_rate_v1.py
  scripts/audit_source_coverage_rate_v2.py scripts/run_release_snapshot_v1.py
  scripts/audit_image_release_gate.py` passed.
- `python3 scripts/audit_source_coverage_rate_v1.py`,
  `python3 scripts/audit_source_coverage_rate_v2.py`, and
  `python3 scripts/run_release_snapshot_v1.py` passed.
- `python3 scripts/audit_image_release_gate.py` exited non-zero as expected
  because the updated release gates are not yet met.

## 2026-06-13 - Image Rights Repair Queue v1

Scope:

- Built an object-level advisory queue for image-rights and weighted
  publication repair under the updated release gate.
- This pass did not change any surface image state, did not upgrade IMG01 or
  IMG03, did not infer rights from heuristics/LLM/TOS/platform signals, did not
  download image files, and did not edit research-repo files.

Files:

- `scripts/audit_image_rights_repair_queue_v1.py`
- `data/image_rights_repair_summary_v1.csv`
- `data/image_rights_repair_source_priorities_v1.csv`
- `data/image_rights_repair_candidates_v1.csv`
- `docs/capture/IMAGE_RIGHTS_REPAIR_QUEUE_v1.md`

Results:

- Object-level repair candidate objects: 1,644.
- Source families represented in the queue: 802.
- Weighted publication points needed for the 95% gate: 223.40.
- Candidate IMG02 objects: 1,321.
- Candidate IMG01 objects: 37.
- Candidate IMG00 objects: 43.
- Candidate IMG04 objects: 243.

Top weighted-gap source priorities:

- Cooper Hewitt Collection GraphQL API: 61.65 gap points, 137 IMG02 objects.
- Wellcome Collection Catalogue API: 39.45 gap points, 81 IMG02 and 3 IMG00
  objects.
- Library of Congress loc.gov API: 38.90 gap points, 37 IMG01 and 13 IMG04
  objects.
- Georgia State University Library Digital Collections / CONTENTdm: 38.25 gap
  points, 85 IMG02 objects.
- Art Institute of Chicago API: 36.00 gap points, 35 IMG00 and 1 IMG04
  objects.
- Internet Archive / text and periodical collections: 33.75 gap points, 75
  IMG02 objects.
- V&A Collections API: 30.25 gap points, 25 IMG02 and 19 IMG04 objects.
- Te Papa Collections Online, DigitalNZ, NAIDOC Poster Gallery, and Princeton
  / Figgy are the next high-value IMG02 review families.

Interpretation:

- The fastest weighted-publication repair is not more random capture. It is a
  targeted rights-evidence pass over high-volume IMG02 sources, plus source
  visible repair for the AIC/LOC/Met/V&A blockers.
- The queue remains conservative: every row has `automatic_upgrade_allowed=false`
  and specifies the item-level evidence needed before a later upgrade.

Verification:

- `python3 -m py_compile scripts/audit_image_rights_repair_queue_v1.py` passed.
- `python3 scripts/audit_image_rights_repair_queue_v1.py` passed.

## 2026-06-13 - Region/Geography Auto-Apply Hardening v1

Scope:

- Added a stricter audit layer in front of the existing region/geography
  auto-apply queue.
- This pass did not mutate archive regions/geographies, did not rebuild or
  rewrite public surfaces, did not download images, and did not touch
  `research-repo`.
- The old ready queue is now treated as a weak pre-queue; later cleaning plans
  prefer the hardened queue.

Files:

- `scripts/audit_region_geo_auto_apply_hardening_v1.py`
- `scripts/build_region_geo_cleaning_plan_v1.py`
- `data/region_geo_auto_apply_hardened_v1.csv`
- `data/region_geo_auto_apply_quarantine_v1.csv`
- `data/region_geo_auto_apply_hardening_summary_v1.csv`
- `data/region_geo_cleaning_action_plan_v1.csv`
- `data/region_geo_manual_review_clusters_v1.csv`
- `docs/capture/REGION_GEO_AUTO_APPLY_HARDENING_v1.md`
- `docs/capture/REGION_GEO_CLEANING_PLAN_v1.md`

Results:

- Existing ready rows reviewed: 88.
- Hardened rows retained for sample-before-mutation review: 8.
- Rows quarantined for manual review: 80.
- Cleaning action plan rows after hardening: 8.
- Manual review clusters retained: 64.

Major hardening blockers:

- Suggested country absent from title/source/source URL evidence: 70.
- Current label present in title/source/source URL evidence: 38.
- Stamp issuer conflicts with the suggested country label: 6.
- Other country present in title/source/source URL evidence: 3.
- `New Mexico` subnational ambiguity blocked from Mexico relabeling: 3.

Largest manual-review geography clusters:

- Indonesia: 381.
- Mexico date-sensitive / military occupation context: 220.
- Caucasus: 64.
- Azerbaijan: 39.
- Georgia: 38.
- Singapore: 31.

Interpretation:

- The previous direct-parse ready queue was too permissive for automatic
  application. Several rows showed topic/issuer/place ambiguity, especially
  Commons-derived stamp and title patterns.
- The safe next step is to spot-check the 8 hardened rows, keep the 80
  quarantined rows out of batch mutation, and use the large manual clusters as
  capture/normalization prompts rather than direct mapping evidence.

Verification:

- `python3 -m py_compile scripts/audit_region_geo_auto_apply_hardening_v1.py
  scripts/build_region_geo_cleaning_plan_v1.py` passed.
- `python3 scripts/audit_region_geo_auto_apply_hardening_v1.py` passed.
- `python3 scripts/build_region_geo_cleaning_plan_v1.py` passed.

## 2026-06-13 - Next Capture And Cleaning Plan v1 Refresh

Scope:

- Refreshed the next capture plan so it reflects the current 20,000-source
  release target, 99% object source-visible target, 95% object verified-open
  target, 95% weighted publication-grade target, and the hardened
  region/geography cleaning queue.
- This pass did not run network capture, did not mutate surfaces, did not
  download images, and did not touch `research-repo`.

Files:

- `scripts/generate_next_capture_plan_v1.py`
- `data/next_capture_plan_v1.csv`
- `docs/capture/NEXT_CAPTURE_AND_CLEANING_PLAN_v1.md`

Current gate read used by the plan:

- Active public sources: 12,342.
- Gap to 20,000 public active sources: 7,658.
- Gap to the 80% source floor: 3,658.
- Object source-visible: 97.91%.
- Object verified-open: 87.96%.
- Object weighted publication-grade: 93.36%.
- Object IMG04: 1.78%.

Planned sequence:

- P0: spot-check the 8 hardened region/geography candidates before any mapping.
- P0: decide the 220 Matamoros 1846 Mexico / United States historical-context
  rows as policy, not simple country relabels.
- P0: run rights repair before volume growth, especially Cooper Hewitt,
  Wellcome, Library of Congress, GSU CONTENTdm, AIC, Internet Archive, V&A,
  and Te Papa.
- P0/P1: first 5,000 successful active sources after item/image capture,
  surface build, and release metrics, weighted toward authority institutions,
  art/design schools, contemporary studios/platforms, Southeast Asia, South
  Asia, Caucasus/Central Asia, MENA/Africa, and pre-1940 continuity.
- P2: run a second 5,000-source tranche only after tranche A is audited,
  deduplicated, rebuilt, and measured.

Interpretation:

- The next capture round should not be a raw count chase. It should combine
  source authority review, region/geography cleanup, rights repair, and
  text-bearing sources so the added volume moves release gates rather than
  inflating weak surfaces.

Verification:

- `python3 -m py_compile scripts/generate_next_capture_plan_v1.py` passed.
- `python3 scripts/generate_next_capture_plan_v1.py` passed.

## 2026-06-13 - Image Rights Repair Preflight Batches v1

Scope:

- Started the P0 rights-repair execution layer by splitting the object-level
  image repair queue into source-family batches.
- This pass did not fetch remote records, did not download images, did not
  mutate surfaces, and did not upgrade IMG01 or IMG03.

Files:

- `scripts/build_image_rights_repair_preflight_batches_v1.py`
- `data/image_rights_repair_preflight_batches_v1.csv`
- `docs/capture/IMAGE_RIGHTS_REPAIR_PREFLIGHT_BATCHES_v1.md`

Results:

- Total source-family repair batches: 802.
- P0 batches: 7.
- P1 batches: 5.
- P2 batches: 790.
- All 802 batches have `automatic_upgrade_allowed=false`.
- Estimated P0 weighted-gap points: 278.25.
- Estimated P0+P1 weighted-gap points: 382.45.
- Current weighted-publication gap to the 95% gate is 223.40 points, so the P0
  source families are sufficient in theory if item-level rights evidence
  validates.

P0 execution order:

- Cooper Hewitt Collection GraphQL API: 137 candidates, 61.65 weighted points.
- Wellcome Collection Catalogue API: 84 candidates, 39.45 weighted points.
- Library of Congress loc.gov API: 50 candidates, 38.90 weighted points.
- Georgia State University Library Digital Collections / CONTENTdm: 85
  candidates, 38.25 weighted points.
- Art Institute of Chicago API: 36 candidates, 36.00 weighted points.
- Internet Archive / text and periodical collections: 75 candidates, 33.75
  weighted points.
- V&A Collections API: 44 candidates, 30.25 weighted points.

Interpretation:

- The fastest path toward the 95% weighted publication-grade gate is a focused
  item-level rights/source-evidence pass over seven source families, not random
  new capture.
- Any later execution run must store metadata, source text, rights evidence,
  and source links only; raw payloads must be redacted and audited before
  commit.

Verification:

- `python3 -m py_compile scripts/build_image_rights_repair_preflight_batches_v1.py`
  passed.
- `python3 scripts/build_image_rights_repair_preflight_batches_v1.py` passed.

## 2026-06-13 - Cooper Hewitt Rights Repair Preflight v1

Scope:

- Started P0 batch execution review with Cooper Hewitt because it had the
  largest weighted-publication repair gap.
- This pass used already captured local metadata only. It did not call GraphQL,
  fetch item pages, download images, mutate surfaces, or upgrade IMG01/IMG03.

Files:

- `scripts/audit_cooperhewitt_rights_repair_preflight_v1.py`
- `data/cooperhewitt_rights_repair_preflight_v1.csv`
- `data/cooperhewitt_rights_repair_summary_v1.csv`
- `docs/capture/COOPERHEWITT_RIGHTS_REPAIR_PREFLIGHT_v1.md`

Results:

- Cooper Hewitt repair candidate rows: 137.
- Local Cooper Hewitt records found: 137.
- Automatic upgrades allowed: 0.
- Upgrade recommendation `no_upgrade`: 133.
- Upgrade recommendation `review_only_no_automatic_upgrade`: 4.

Rights signals:

- Local legal credit only / no open evidence: 74.
- Blocked by local copyright or restriction signal: 51.
- No item-level open-rights evidence: 8.
- Possible open text requiring item verification: 4.

Interpretation:

- Cooper Hewitt remains a strong source-visible IMG02 family, but the local
  metadata does not support automatic verified-open promotion.
- Rows with `cc0`-like hints but copyright/restriction context still remain
  blocked unless a later item-page/source check provides explicit open evidence.
- For weighted-publication repair, Cooper Hewitt should not be counted as
  quick verified-open gain. The next P0 source families should be Wellcome,
  Library of Congress, GSU CONTENTdm, AIC, Internet Archive, and V&A.

Verification:

- `python3 -m py_compile scripts/audit_cooperhewitt_rights_repair_preflight_v1.py`
  passed.
- `python3 scripts/audit_cooperhewitt_rights_repair_preflight_v1.py` passed.

## 2026-06-13 - Wellcome Rights Repair Preflight v1

Scope:

- Continued P0 rights-repair execution review with Wellcome Collection
  Catalogue API, the second-largest weighted-publication repair batch.
- This pass used already captured local capture records only. It did not call
  Wellcome APIs, fetch item pages, download images, mutate surfaces, or upgrade
  IMG01/IMG03.

Files:

- `scripts/audit_wellcome_rights_repair_preflight_v1.py`
- `data/wellcome_rights_repair_preflight_v1.csv`
- `data/wellcome_rights_repair_summary_v1.csv`
- `docs/capture/WELLCOME_RIGHTS_REPAIR_PREFLIGHT_v1.md`

Results:

- Wellcome repair candidate rows: 84.
- Local Wellcome records found: 84.
- Candidate weighted-publication gap points represented: 39.45.
- Automatic upgrades allowed: 0.
- Upgrade recommendation `no_upgrade`: 81 rows / 36.45 weighted points.
- Upgrade recommendation `source_visible_repair_needed`: 3 rows / 3.00
  weighted points.

Rights and image signals:

- Local image states: 82 IMG02, 2 legacy local IMG03.
- License signals: 82 no open-license text, 2 blocking/non-commercial terms.
- Rights signals: 81 source-hosted viewer records without open-license signal,
  3 placeholder/no-displayable-image blockers.

Important finding:

- The two legacy local IMG03 rows carry `cc-by-nc` / `cc-by-nc-nd` license text
  and placeholder image URLs. These are not verified-open publication evidence
  under the current gate contract and should be treated as repair/downgrade
  risks, not as IMG03 upgrade candidates.
- The Wellcome preflight therefore tightens local license detection so a
  generated phrase such as `open licence signal:` is not sufficient by itself;
  the actual license id must be PDM, CC0, public domain, or a non-NC/ND CC BY
  signal.

Interpretation:

- Wellcome is valuable for source-visible public-health graphics, but it is not
  a quick verified-open repair path unless item-level license evidence is
  rechecked and captured.
- The next P0 rights families should continue with Library of Congress, GSU
  CONTENTdm, AIC, Internet Archive, and V&A before the large 5,000-source
  capture tranche.

Verification:

- `python3 -m py_compile scripts/audit_wellcome_rights_repair_preflight_v1.py`
  passed.
- `python3 scripts/audit_wellcome_rights_repair_preflight_v1.py` passed.

## 2026-06-13 - Library of Congress Rights Repair Preflight v1

Scope:

- Continued P0 rights-repair execution review with Library of Congress
  `loc.gov` API candidates.
- This pass used already captured local records only. It did not call
  `loc.gov`, fetch item pages, download images, mutate surfaces, or upgrade
  IMG01/IMG03.

Files:

- `scripts/audit_loc_rights_repair_preflight_v1.py`
- `data/loc_rights_repair_preflight_v1.csv`
- `data/loc_rights_repair_summary_v1.csv`
- `docs/capture/LOC_RIGHTS_REPAIR_PREFLIGHT_v1.md`

Results:

- LOC repair candidate rows: 50.
- Local LOC records found: 50.
- Candidate weighted-publication gap points represented: 38.90.
- Automatic upgrades allowed: 0.
- Original repair families: 37 `img01_item_image_and_rights_review`,
  13 `img04_text_state_review`.
- Local image states: 37 IMG01, 13 IMG04.
- Local rights signals: 49 without item rights-advisory text, 1 with
  blocking/unresolved rights text.
- Upgrade recommendation `item_rights_capture_required`: 37 rows / 25.90
  weighted points.
- Upgrade recommendation `source_visible_repair_needed`: 13 rows / 13.00
  weighted points.

Interpretation:

- LOC is a stronger repair route than Cooper Hewitt and Wellcome because the
  current blockers are missing item-page rights/image evidence, not an
  institutional pattern that already fails the verified-open gate.
- The 37 IMG01 rows should be deep-probed for item JSON/page rights advisory
  and image derivative evidence before any rights-state decision.
- The 13 IMG04 rows should also be deep-probed before they are accepted as
  true text-only pages, because the earlier search-row capture may have missed
  item-level images.
- No LOC row can be upgraded by source-family reputation alone.

Verification:

- `python3 -m py_compile scripts/audit_loc_rights_repair_preflight_v1.py`
  passed.
- `python3 scripts/audit_loc_rights_repair_preflight_v1.py` passed.

## 2026-06-13 - GSU CONTENTdm Rights Repair Preflight v1

Scope:

- Continued P0 rights-repair execution review with Georgia State University
  Library Digital Collections / CONTENTdm candidates.
- This pass used already captured local CSV records plus local raw CONTENTdm
  JSON only. It did not call CONTENTdm, fetch item pages, download images,
  mutate surfaces, or upgrade IMG01/IMG03.

Files:

- `scripts/audit_gsu_rights_repair_preflight_v1.py`
- `data/gsu_rights_repair_preflight_v1.csv`
- `data/gsu_rights_repair_summary_v1.csv`
- `docs/capture/GSU_RIGHTS_REPAIR_PREFLIGHT_v1.md`

Results:

- GSU repair candidate rows: 85.
- Local records found: 85.
- Local raw CONTENTdm JSON records found: 85.
- Candidate weighted-publication gap points represented: 38.25.
- Automatic upgrades allowed: 0.
- Local image states: 85 IMG02.
- Raw rights signals: 76 blocking/permission/copyright signals, 8 present but
  unclassified rights statements, 1 raw open-rights signal.
- Upgrade recommendation `no_upgrade`: 84 rows / 37.80 weighted points.
- Upgrade recommendation `review_rebuild_alignment_no_automatic_upgrade`:
  1 row / 0.45 weighted points.

Important finding:

- One candidate, `SURF-GSU2026R020` (`Revolution RCP Monthly`), has a local raw
  CONTENTdm standardized rights URI of `https://creativecommons.org/publicdomain/zero/1.0/`.
  It is not automatically upgraded; it requires manual item check and rebuild
  alignment so the public record preserves the source rights evidence.
- The existing GSU capture path appears to overwrite the source rights statement
  with image-display basis text in the record CSV. A follow-up patch should
  preserve the local rights text and image-display basis as separate evidence
  fields.

Interpretation:

- GSU remains useful for regional/local print-culture coverage, but it is not a
  bulk verified-open repair family under current evidence.
- Later GSU capture should prioritize rights-field preservation and selective
  CC0/open-rights rebuilding rather than assuming CONTENTdm source-hosted images
  are publication-grade.

Verification:

- `python3 -m py_compile scripts/audit_gsu_rights_repair_preflight_v1.py`
  passed.
- `python3 scripts/audit_gsu_rights_repair_preflight_v1.py` passed.

## 2026-06-13 - AIC Rights Repair Preflight v1

Scope:

- Continued P0 rights-repair execution review with Art Institute of Chicago API
  candidates.
- This pass used already captured local CSV/JSON only. It did not call AIC
  APIs, fetch item pages, download images, mutate surfaces, or upgrade
  IMG01/IMG03.

Files:

- `scripts/audit_aic_rights_repair_preflight_v1.py`
- `data/aic_rights_repair_preflight_v1.csv`
- `data/aic_rights_repair_summary_v1.csv`
- `docs/capture/AIC_RIGHTS_REPAIR_PREFLIGHT_v1.md`

Results:

- AIC repair candidate rows: 36.
- Local records found: 36.
- Local raw AIC JSON records found: 27.
- Candidate weighted-publication gap points represented: 36.00.
- Automatic upgrades allowed: 0.
- Original repair families: 35 `img00_source_visible_repair`,
  1 `img04_text_state_review`.
- Local image states: 35 IMG00, 1 legacy local IMG03.
- Raw rights signals: 26 raw image identifiers with `is_public_domain=false`,
  9 raw records missing, 1 raw record without image identifier.
- Upgrade recommendation `no_upgrade`: 36 rows / 36.00 weighted points.

Interpretation:

- AIC is not an immediate verified-open repair family in this candidate set.
  Most image-bearing candidates have local raw search metadata indicating
  `is_public_domain=false`.
- AIC image identifiers and IIIF URLs are not sufficient evidence for
  publication-grade open display without item-level public-domain confirmation.
- Future AIC work should use item API probes to confirm whether any records have
  changed rights status, then rebuild only rows with explicit public-domain
  evidence.

Verification:

- `python3 -m py_compile scripts/audit_aic_rights_repair_preflight_v1.py`
  passed.
- `python3 scripts/audit_aic_rights_repair_preflight_v1.py` passed.

## 2026-06-13 - Internet Archive Rights Repair Preflight v1

Scope:

- Continued P0 rights-repair execution review with Internet Archive text and
  periodical collection candidates.
- This pass used already captured local CSV metadata only. It did not call
  archive.org, download files/images, mutate surfaces, or upgrade IMG01/IMG03.

Files:

- `scripts/audit_internet_archive_rights_repair_preflight_v1.py`
- `data/internet_archive_rights_repair_preflight_v1.csv`
- `data/internet_archive_rights_repair_summary_v1.csv`
- `docs/capture/INTERNET_ARCHIVE_RIGHTS_REPAIR_PREFLIGHT_v1.md`

Results:

- Internet Archive repair candidate rows: 75.
- Local records found: 75.
- Candidate weighted-publication gap points represented: 33.75.
- Automatic upgrades allowed: 0.
- Local image states: 75 IMG02.
- License signals: 74 with no explicit item license URL, 1 with a blocking
  non-commercial/no-derivatives Creative Commons URL.
- Upgrade recommendation `no_upgrade`: 75 rows / 33.75 weighted points.

Interpretation:

- Internet Archive is useful for reading/source support, especially for
  periodicals, books, zines, and web/interface design texts, but the current
  repair queue does not contain verified-open image evidence.
- IA thumbnails or scans are not enough for publication-grade image display;
  any later upgrade must preserve explicit item license evidence.
- The one candidate with an explicit license URL uses BY-NC-ND and is therefore
  blocked for the verified-open/publication-grade target.

Verification:

- `python3 -m py_compile scripts/audit_internet_archive_rights_repair_preflight_v1.py`
  passed.
- `python3 scripts/audit_internet_archive_rights_repair_preflight_v1.py` passed.

## 2026-06-13 - V&A Rights Repair Preflight v1

Scope:

- Continued P0 rights-repair execution review with V&A Collections API
  candidates.
- This pass used already captured local CSV records and local
  `vam_object_*.json` object-detail payloads only. It did not call V&A APIs,
  download images, mutate surfaces, or upgrade IMG01/IMG03.

Files:

- `scripts/audit_vam_rights_repair_preflight_v1.py`
- `data/vam_rights_repair_preflight_v1.csv`
- `data/vam_rights_repair_summary_v1.csv`
- `docs/capture/VAM_RIGHTS_REPAIR_PREFLIGHT_v1.md`

Results:

- V&A repair candidate rows: 44.
- Local object-detail raw records found: 44.
- Candidate weighted-publication gap points represented: 30.25.
- Automatic upgrades allowed: 0.
- Original repair families: 25 `img02_open_rights_review`,
  17 `img04_text_state_review`, 2 `img04_visual_record_search`.
- Local image states: 25 IMG02, 19 IMG04.
- Object image resolution metadata: 37 low-resolution, 7 high-resolution.
- Object image signals: 25 with image copyright metadata, 19 with image
  metadata but no open-rights statement.
- Upgrade recommendation `no_upgrade`: 25 rows / 11.25 weighted points.
- Upgrade recommendation `source_visible_repair_needed`: 19 rows / 19.00
  weighted points.

Interpretation:

- V&A object-detail metadata improves source-visible triage but does not
  provide bulk verified-open image evidence in this candidate set.
- Rows with copyright metadata stay IMG02/IMG04 unless later item evidence
  exposes explicit open/public-domain rights.
- Rows with image metadata but no open-rights statement may support
  source-visible repair, but not IMG03.
- Compound IMG04 rows need member-level visual search rather than source-family
  rights promotion.

Verification:

- `python3 -m py_compile scripts/audit_vam_rights_repair_preflight_v1.py`
  passed.
- `python3 scripts/audit_vam_rights_repair_preflight_v1.py` passed.

## 2026-06-13 - P0 Rights Repair Preflight Rollup v1

Scope:

- Combined the seven P0 image-rights repair preflights into one advisory
  rollup.
- This pass used only local preflight CSV outputs and the existing rights
  repair candidate queue. It did not call external APIs, download images,
  mutate surfaces, or upgrade IMG01/IMG03.

Files:

- `scripts/summarize_p0_rights_repair_preflight_v1.py`
- `data/p0_rights_repair_preflight_rollup_v1.csv`
- `data/p0_rights_repair_preflight_recommendations_v1.csv`
- `docs/capture/P0_RIGHTS_REPAIR_PREFLIGHT_ROLLUP_v1.md`

Results:

- P0 source families summarized: 7.
- Candidate rows represented: 511.
- Weighted-publication gap points represented: 278.25.
- Automatic upgrades allowed: 0.
- Recommendation totals:
  - `no_upgrade`: 434 rows / 215.10 weighted points.
  - `item_rights_capture_required`: 37 rows / 25.90 weighted points.
  - `source_visible_repair_needed`: 35 rows / 35.00 weighted points.
  - `review_only_no_automatic_upgrade`: 4 rows / 1.80 weighted points.
  - `review_rebuild_alignment_no_automatic_upgrade`: 1 row / 0.45 weighted
    points.

Interpretation:

- The P0 family preflight is a negative bulk-rights-upgrade result. Source
  family reputation, source-hosted images, thumbnails, or platform metadata do
  not justify IMG01/IMG03 upgrades.
- LOC is the strongest next deep-probe path because its blockers are missing
  item image/rights capture rather than explicit local copyright restrictions.
- Cooper Hewitt, Wellcome, AIC, Internet Archive, V&A, and most GSU rows should
  stay source-visible/context sources unless explicit item-level open evidence
  is captured.
- GSU needs a capture-logic patch before any rebuild so local rights statements
  and image-display basis are preserved separately.
- The next 5,000-source capture tranche should prioritize sources with explicit
  public-domain/open-license item fields and low region coverage, rather than
  trying to mine verified-open gains from these P0 source families.

Verification:

- `python3 -m py_compile scripts/summarize_p0_rights_repair_preflight_v1.py`
  passed.
- `python3 scripts/summarize_p0_rights_repair_preflight_v1.py` passed.

## 2026-06-13 - Capture Rights Rule Hardening v1

Scope:

- Hardened future capture behavior before the next large source tranche.
- This pass did not fetch records, download images, mutate surfaces, rebuild
  public payloads, or upgrade IMG01/IMG03.

Files:

- `scripts/run_midcentury_expansion_capture_1931_1970.py`
- `scripts/run_gsu_contentdm_image_ready_1830_1970.py`
- `scripts/harvest_gsu_contentdm_raw_records.py`
- `scripts/audit_capture_rights_rule_hardening_v1.py`
- `data/capture_rights_rule_hardening_v1.csv`
- `docs/capture/CAPTURE_RIGHTS_RULE_HARDENING_v1.md`

Changes:

- Replaced permissive Wellcome/Internet Archive license substring checks with
  `publication_grade_open_license()`.
- `cc-by-nc`, `cc-by-nd`, and `cc-by-nc-nd` are now blocked from
  publication-grade open classification.
- Explicit `CC BY`, `CC BY-SA`, `CC0`, public-domain, and `PDM` signals remain
  accepted as item-level open/public-domain candidates.
- Moved GSU CONTENTdm `**rights` expansion before the explicit
  `source_rights_text` assignment so local rights statements are not overwritten
  by image-display basis text.

Audit:

- `scripts/audit_capture_rights_rule_hardening_v1.py` ran 10 local checks with
  0 failures.
- The audit confirms restricted Creative Commons variants are blocked and GSU
  local rights statements are preserved separately from display-basis fields.

Interpretation:

- This is a gate-preparation fix for future capture batches. It does not
  retroactively repair existing Wellcome, IA, or GSU rows.
- Existing affected rows remain in the rights repair/rebuild queue and should
  be handled only after item-level evidence is captured.

Verification:

- `python3 -m py_compile scripts/audit_capture_rights_rule_hardening_v1.py scripts/run_midcentury_expansion_capture_1931_1970.py scripts/run_gsu_contentdm_image_ready_1830_1970.py scripts/harvest_gsu_contentdm_raw_records.py scripts/harvest_gsu_contentdm_raw_records_1971_2026.py`
  passed.
- `python3 scripts/audit_capture_rights_rule_hardening_v1.py` passed.

## 2026-06-13 - LOC Rights Item Probe v1

Scope:

- Ran a source-only loc.gov item JSON probe against the 50 P0 Library of
  Congress rights-repair candidates.
- The probe extracted item-level rights/advisory text and source-hosted image
  URL signals. It did not download images, save raw JSON, mutate surfaces,
  rebuild public payloads, or upgrade IMG01/IMG03.

Files:

- `scripts/probe_loc_rights_item_metadata_v1.py`
- `data/loc_rights_item_probe_v1.csv`
- `data/loc_rights_item_probe_summary_v1.csv`
- `docs/capture/LOC_RIGHTS_ITEM_PROBE_v1.md`

Results:

- Candidate rows probed: 50.
- Rows with source-hosted LOC image URLs: 20.
- Rows with item-level open-rights text: 21.
- Manual IMG03 candidate rows: 20.
- Manual IMG03 candidate weighted gap points represented: 14.00.
- Rate-limited rows queued for later retry: 29.
- Rows kept as IMG04/text until visual source is found: 1.
- Automatic upgrades allowed: 0.

Interpretation:

- LOC is confirmed as a useful targeted repair path, but not a bulk automatic
  rights-upgrade path.
- The 20 `manual_img03_candidate_item_rights_visible` rows expose both
  source-hosted image URLs and LOC item-level "No known restrictions on
  publication" text. They can enter a human/rebuild review pass, but they were
  not promoted in this round.
- LOC returned HTTP 429 for 29 rows after the initial successful subset. The
  script now treats 429 as `retry_later_rate_limited` instead of blocking the
  run with long in-process backoff.
- The candidate set is valuable for pre-1940 advertising/trade-card continuity
  and 1930-1970 WPA/Federal Art poster coverage.

Verification:

- `python3 -m py_compile scripts/probe_loc_rights_item_metadata_v1.py` passed.
- `python3 scripts/probe_loc_rights_item_metadata_v1.py` completed with network
  permission and source-only output.

## 2026-06-13 - LOC Manual IMG03 Rebuild Queue v1

Scope:

- Built a manual rebuild queue from the LOC source-only item probe.
- This queue isolates rows where LOC item JSON exposed both a source-hosted
  image URL and item-level open/publication rights text.
- This pass did not download images, save raw JSON, mutate capture records,
  rebuild surfaces, or upgrade IMG01/IMG03.

Files:

- `scripts/build_loc_manual_img03_rebuild_queue_v1.py`
- `data/loc_manual_img03_rebuild_queue_v1.csv`
- `data/loc_manual_img03_rebuild_summary_v1.csv`
- `docs/capture/LOC_MANUAL_IMG03_REBUILD_QUEUE_v1.md`

Results:

- Manual rebuild candidate rows: 20.
- Weighted gap points represented: 14.00.
- Automatic upgrades allowed: 0.
- Current local image states: 20 IMG01.
- Future patch targets:
  - `data/capture_batch_midcentury_1930_1970_records.csv`: 13 rows.
  - `data/capture_batch_early_region_1830_1930_records.csv`: 5 rows.
  - `data/capture_batch_early_region_1830_1880_records.csv`: 2 rows.

Interpretation:

- These rows are plausible verified-open repair candidates because LOC item
  metadata provides source-hosted image URLs plus "No known restrictions on
  publication" text.
- They still require a controlled capture-record patch and rebuild before they
  can affect public surface metrics.
- The 29 LOC rate-limited rows remain queued in the item probe as
  `retry_later_rate_limited` and are not part of this rebuild queue.

Verification:

- `python3 -m py_compile scripts/build_loc_manual_img03_rebuild_queue_v1.py`
  passed.
- `python3 scripts/build_loc_manual_img03_rebuild_queue_v1.py` passed.

## 2026-06-13 - LOC Manual IMG03 Apply Dry Run v1

Scope:

- Planned a controlled capture-record patch for the 20 LOC manual IMG03 rebuild
  candidates.
- This was a dry-run only. It did not write target capture CSVs, rebuild
  surfaces, download images, or change archive metrics.

Files:

- `scripts/dry_run_loc_manual_img03_apply_v1.py`
- `data/loc_manual_img03_apply_dry_run_v1.csv`
- `data/loc_manual_img03_apply_dry_run_summary_v1.csv`
- `docs/capture/LOC_MANUAL_IMG03_APPLY_DRY_RUN_v1.md`

Results:

- Planned rows: 20.
- Ready for manual apply: 20.
- Blocked/review-required rows: 0.
- Automatic upgrades allowed: 0.
- Target files:
  - `data/capture_batch_midcentury_1930_1970_records.csv`: 13 rows.
  - `data/capture_batch_early_region_1830_1930_records.csv`: 5 rows.
  - `data/capture_batch_early_region_1830_1880_records.csv`: 2 rows.
- Current image state for all planned rows: IMG01.

Planned field changes for a future apply pass:

- `image_presence_code`: IMG01 -> IMG03.
- `image_frame_behavior`: `open_image_frame`.
- `image_state_confidence`: `high`.
- `source_rights_text` / `rights_basis`: LOC item rights/advisory text.
- `image_url_detected`: LOC source-hosted image URL.
- `iiif_or_viewer_available`: source record URL remains visible.

Interpretation:

- The dry-run confirms the LOC repair is technically ready for a controlled
  apply/rebuild pass, but no archive state changed in this step.
- Because generated public payloads and frontend data are already dirty in the
  current worktree from other work, the real apply/rebuild should be isolated
  in a clean rebuild step rather than mixed with unrelated payload changes.

Verification:

- `python3 -m py_compile scripts/dry_run_loc_manual_img03_apply_v1.py` passed.
- `python3 scripts/dry_run_loc_manual_img03_apply_v1.py` passed.

## 2026-06-13 - LOC Manual IMG03 Apply Script v1

Scope:

- Added a controlled apply script for the reviewed LOC manual IMG03 repair
  queue.
- Default execution remains dry-run and only writes a plan, summary, and
  capture note.
- Target capture CSV writes require both `--apply` and
  `--confirm-item-rights-reviewed`.
- This pass did not run `--apply`, rebuild surfaces, download images, save LOC
  raw payloads, or change archive metrics.

Files:

- `scripts/apply_loc_manual_img03_records_v1.py`
- `data/loc_manual_img03_capture_apply_plan_v1.csv`
- `data/loc_manual_img03_capture_apply_summary_v1.csv`
- `docs/capture/LOC_MANUAL_IMG03_CAPTURE_APPLY_PLAN_v1.md`

Results:

- Planned rows: 20.
- Ready for apply: 20.
- Blocked rows: 0.
- Capture rows written: 0.
- Public surfaces rebuilt: false.

Planned field changes:

- `image_presence_code`: `IMG03`.
- `source_rights_text` / `rights_basis`: LOC item-level
  no-known-restrictions advisory.
- `image_url_detected`: LOC source-hosted image URL.
- `image_frame_behavior`: `open_image_frame`.
- `local_copy_permitted`: `false`.
- `iiif_or_viewer_available`: LOC item/source record URL.

Interpretation:

- This adds the missing controlled execution layer between the reviewed LOC
  evidence queue and the eventual capture-record mutation.
- Because the current worktree still contains unrelated generated/frontend and
  raw-capture changes, this step intentionally stopped at dry-run mode.
- Future application should be isolated, followed by a public surface rebuild
  and release gate snapshot.

Verification:

- `python3 -m py_compile scripts/apply_loc_manual_img03_records_v1.py` passed.
- `python3 scripts/apply_loc_manual_img03_records_v1.py` passed.

## 2026-06-13 - LOC Manual IMG03 Controlled Apply v1

Scope:

- Backed up the three capture-record CSVs touched by the LOC manual IMG03
  repair queue.
- Ran the guarded apply command:
  `python3 scripts/apply_loc_manual_img03_records_v1.py --apply --confirm-item-rights-reviewed`.
- Added and ran a post-apply contract audit.
- This pass did not rebuild generated public surfaces, frontend payload
  mirrors, or any visual frontend assets.

Backup:

- `data/backups/loc_manual_img03_apply_2026_06_13/MANIFEST.md`
- `data/backups/loc_manual_img03_apply_2026_06_13/capture_batch_midcentury_1930_1970_records.before_loc_img03_apply.csv`
- `data/backups/loc_manual_img03_apply_2026_06_13/capture_batch_early_region_1830_1930_records.before_loc_img03_apply.csv`
- `data/backups/loc_manual_img03_apply_2026_06_13/capture_batch_early_region_1830_1880_records.before_loc_img03_apply.csv`

Apply results:

- Planned rows: 20.
- Capture rows written: 20.
- Blocked rows: 0.
- Images downloaded: 0.
- Public surfaces rebuilt: false.
- Target files changed:
  - `data/capture_batch_midcentury_1930_1970_records.csv`: 13 rows.
  - `data/capture_batch_early_region_1830_1930_records.csv`: 5 rows.
  - `data/capture_batch_early_region_1830_1880_records.csv`: 2 rows.

Postcheck results:

- Checked rows: 20.
- Pass rows: 20.
- Fail rows: 0.
- Post-apply image state: 20 IMG03.

Files:

- `scripts/apply_loc_manual_img03_records_v1.py`
- `scripts/audit_loc_manual_img03_apply_postcheck_v1.py`
- `data/loc_manual_img03_capture_apply_plan_v1.csv`
- `data/loc_manual_img03_capture_apply_summary_v1.csv`
- `data/loc_manual_img03_apply_postcheck_v1.csv`
- `data/loc_manual_img03_apply_postcheck_summary_v1.csv`
- `docs/capture/LOC_MANUAL_IMG03_CAPTURE_APPLY_PLAN_v1.md`
- `docs/capture/LOC_MANUAL_IMG03_APPLY_POSTCHECK_v1.md`

Implementation note:

- The apply script was updated to preserve the target CSV line terminator.
  The first apply attempt revealed that rewriting CRLF capture files as LF
  produced noisy whole-file diffs; the backup was used to restore the files
  before reapplying with preserved line endings. Final target-file diff is the
  expected 20 changed rows only.

Interpretation:

- The capture-record layer now contains the 20 LOC IMG03 repairs, based on
  item-level LOC no-known-restrictions text plus source-hosted image URLs.
- Public release metrics are not yet updated because surfaces were not rebuilt.
- The next safe step is a small, isolated rebuild/audit pass rather than a full
  frontend rebuild.

Verification:

- `python3 -m py_compile scripts/apply_loc_manual_img03_records_v1.py scripts/audit_loc_manual_img03_apply_postcheck_v1.py` passed.
- `python3 scripts/audit_loc_manual_img03_apply_postcheck_v1.py` passed.

## 2026-06-13 - Non-mainstream Item/Image Capture Quality Audit v1

Scope:

- Added an offline quality audit for the existing non-mainstream item/image
  capture batch before any surface rebuild.
- Recorded line-count and SHA-256 recovery anchors for the two audit input
  CSVs under `data/backups/nonmainstream_item_image_quality_audit_2026_06_13/`.
- Generated triage CSVs for ready, manual-review, and quarantine queues.
- This pass did not fetch network data, download images, mutate capture
  records, upgrade IMG01/IMG03, rebuild public surfaces, or touch frontend
  payload mirrors.

Backup:

- `data/backups/nonmainstream_item_image_quality_audit_2026_06_13/MANIFEST.md`
- The source CSVs were not mutated, so duplicate raw-like copies were not
  committed. Recovery is anchored by Git history plus manifest hashes.

Audit results:

- Records audited: 587.
- Ready for item review: 5.
- Manual review before surface: 345.
- Quarantine / not counted: 237.
- Image state distribution in the input remains IMG02-only.

Macro-region distribution:

- Latin America: 297.
- Eastern Europe: 99.
- Africa: 81.
- MENA: 41.
- Southeast Asia: 39.
- East Asia: 14.
- Central Asia: 8.
- South Asia: 7.
- Oceania: 1.

Risk findings:

- Missing explicit design signal: 546.
- Source-summary geography repair needed: 424.
- Low surface signal: 225.
- Generic non-design source: 20.
- Spam/SEO pollution: 12.
- QID used as source name: 4.

Interpretation:

- The batch contains useful under-covered-region leads, but it is not safe to
  count all 587 rows as successful active sources.
- The biggest blockers are not IMG availability; they are weak graphic-design
  relevance, source-summary geography that collapses country-level
  `source_place_text` into broad buckets such as Caribbean/Caucasus, and a
  small number of polluted source pages.
- The audit now infers country-level geography from `source_place_text` for all
  587 rows; 424 rows need the summary geography repaired upstream before they
  can honestly improve strict source coverage.
- The next large capture round should push geographic normalization and
  source-authority/design-signal filtering upstream into discovery, otherwise
  a 5,000-source expansion will inflate source count without improving release
  gate quality.

Files:

- `scripts/audit_nonmainstream_item_image_capture_quality_v1.py`
- `data/nonmainstream_item_image_capture_quality_v1.csv`
- `data/nonmainstream_item_image_capture_quality_summary_v1.csv`
- `data/nonmainstream_item_image_capture_ready_queue_v1.csv`
- `data/nonmainstream_item_image_capture_manual_review_v1.csv`
- `data/nonmainstream_item_image_capture_quarantine_v1.csv`
- `docs/capture/NONMAINSTREAM_ITEM_IMAGE_CAPTURE_QUALITY_v1.md`

Next action:

- Use the manual-review queue to repair overbroad geography and identify
  genuinely design-relevant institutions before any rebuild.
- Quarantine rows should be excluded from success totals until replaced or
  manually repaired.
- Full frontend/public-surface rebuild remains deferred to a smaller isolated
  pass because full rebuilds are currently too expensive for the workstation.

Verification:

- `python3 -m py_compile scripts/audit_nonmainstream_item_image_capture_quality_v1.py` passed.
- `python3 scripts/audit_nonmainstream_item_image_capture_quality_v1.py` passed.

## 2026-06-13 - Non-mainstream Source-summary Geography Repair v1

Scope:

- Fixed the non-mainstream item/image capture generator so source summaries
  derive geography from the first and last `source_place_text` segments.
  Example: `Latin America / Caribbean / Argentina` now becomes
  `Latin America / Argentina`, not `Latin America / Caribbean`.
- Added a guarded source-summary repair/postcheck script for the existing
  non-mainstream item/image capture batch.
- Applied the repair to
  `data/capture_batch_nonmainstream_item_image_2026_source_summary.csv`.
- Re-ran the non-mainstream item/image capture quality audit after repair.
- This pass did not fetch network data, download images, mutate capture
  records, upgrade IMG01/IMG03, rebuild public surfaces, or touch frontend
  payload mirrors.

Root cause:

- The earlier summary generator used the middle path segment as
  `country_or_region`. That collapsed three-part paths into broad buckets such
  as `Caribbean`, `Caucasus`, and `Indigenous`, which would have inflated
  source coverage without adding country-level release evidence.
- The capture-record layer already carried the country-level evidence in
  `source_place_text`; the repair is therefore a deterministic local
  normalization, not a new source claim.

Repair result:

- Source summary rows checked: 581.
- Net source-summary rows changed versus the pre-repair tracked baseline: 393.
- Repaired old buckets: Caribbean 295, Caucasus 97, Indigenous 1.
- Main repaired target countries: Colombia 141, Argentina 79, Peru 22,
  Uruguay 19, Bosnia and Herzegovina 15, Bulgaria 15, Serbia 15, Romania 12,
  Armenia 10, Belarus 9, Chile 8, Bolivia 7, North Macedonia 6, Ukraine 5.
- Duplicate source IDs in capture records: 91. The repair and audit now key
  source summaries by `source_id` plus `source_name`, not source ID alone.
- Source summary SHA-256 changed from
  `802cd9d8f963ef820fda49598297fbf97d4e1fc2c2ee3d5381a3d15db5d6d64a`
  to `6cee404a5dabd582d96fe77c35704215d32e26b3cc0e9b7d4a0e188351b0706a`.
- Final repair postcheck: 581 unchanged rows, `postcheck_clean=true`.

Post-repair quality audit:

- Records audited: 587.
- Ready for item review: 5.
- Manual review before surface: 345.
- Quarantine / not counted: 237.
- Geography precision: 587 `country_from_source_place`.
- Source-summary geography repair needed: 0.
- Main remaining risk flags: missing design signal 546, low surface signal
  225, generic non-design source 20, spam/SEO pollution 12, QID source name 4.

Interpretation:

- The geography-summary bug is fixed for this batch and for future runs of the
  current generator.
- These rows still remain IMG02 and do not become successful active sources
  until item/surface review confirms object-level design relevance and a valid
  source route.
- The next large capture round should use stronger design-signal and authority
  filters up front. Quarantine rows should stay out of success totals and
  rebuild inputs unless a later manual/source replacement pass repairs them.
- A full frontend/public-surface rebuild remains deferred; this was a data
  cleaning layer intended to make the next long capture safer.

Files:

- `scripts/run_nonmainstream_item_image_capture_2026_v1.py`
- `scripts/repair_nonmainstream_item_image_source_summary_geo_v1.py`
- `scripts/audit_nonmainstream_item_image_capture_quality_v1.py`
- `data/capture_batch_nonmainstream_item_image_2026_source_summary.csv`
- `data/nonmainstream_item_image_source_summary_geo_repair_plan_v1.csv`
- `data/nonmainstream_item_image_source_summary_geo_repair_summary_v1.csv`
- `data/nonmainstream_item_image_capture_quality_v1.csv`
- `data/nonmainstream_item_image_capture_quality_summary_v1.csv`
- `data/nonmainstream_item_image_capture_ready_queue_v1.csv`
- `data/nonmainstream_item_image_capture_manual_review_v1.csv`
- `data/nonmainstream_item_image_capture_quarantine_v1.csv`
- `docs/capture/NONMAINSTREAM_ITEM_IMAGE_SOURCE_SUMMARY_GEO_REPAIR_v1.md`
- `docs/capture/NONMAINSTREAM_ITEM_IMAGE_CAPTURE_QUALITY_v1.md`
- `data/backups/nonmainstream_item_image_source_summary_geo_repair_2026_06_13/MANIFEST.md`

Verification:

- `python3 -m py_compile scripts/run_nonmainstream_item_image_capture_2026_v1.py scripts/repair_nonmainstream_item_image_source_summary_geo_v1.py scripts/audit_nonmainstream_item_image_capture_quality_v1.py`
  passed.
- `python3 scripts/repair_nonmainstream_item_image_source_summary_geo_v1.py`
  passed and reported `postcheck_clean=true`.
- `python3 scripts/audit_nonmainstream_item_image_capture_quality_v1.py`
  passed and reported `geo_repair_needed=false` for all 587 records.
- `git diff --check` passed for all intended commit-bound files.
- Broad safety scan for `API_KEY`, token, password, secret, cookie, session,
  bearer, `/Users/`, and `.env` found no real credential or local-path payload
  in this change. Hits were expected false positives: script variable names,
  ordinary public URL text, and historical scan-language entries in this log.

## 2026-06-13 - Commons Open Authority-weighted 5k Source Batch Completion

Scope:

- Resumed the authority-weighted Commons open metadata capture from the
  300-record checkpoint and completed the planned 5,000-source batch.
- Added a narrow topoff runner after the general queue became sparse near the
  target. The topoff uses whitelisted country/object Commons metadata queries
  and the same duplicate, rights, year, object-family, and distribution gates as
  the authority batch.
- Attempted a controlled-expansion topoff lane, but stopped it after it added
  only 10 records and showed low yield. The controlled script now supports a
  temporary environment target for future small topoff attempts.
- Deferred full frontend/public-surface rebuild. This round remains
  item-image/source metadata capture plus cleaning audit; source records are
  not counted as final public surfaces until a later isolated rebuild.

Capture result:

- Authority-weighted Commons records: 5,055.
- Authority-weighted distinct source names: 5,021.
- Authority-weighted distinct source identifiers: 5,055.
- Image state distribution: IMG03 5,055; IMG00/IMG01/IMG02/IMG04 0.
- 2026 records: 53, about 1.05% of the authority-weighted batch. The earlier
  risk of recent-year overconcentration did not appear in this run.
- Controlled topoff attempt: 935 total controlled records after the attempt,
  with 10 added in this pass; not used as the main 5k threshold.

Authority batch distribution:

- Periods: pre_1940 1,927; 2000_2026 1,617; 1940_1970 898; 1970_2000 613.
- Macro-regions: Eastern Europe 1,069; Africa 1,034; Latin America 842;
  Middle East and North Africa 686; Southeast Asia 441; South Asia 416;
  Oceania 204; East Asia 187; Central Asia 176.
- Object families: postage_stamp 1,445; poster 1,403; label_packaging 889;
  advertising_trade 807; book_cover 173; brochure_pamphlet 108; film_poster
  97; typography_identity 64; political_poster 37; magazine_cover 27;
  travel_poster 5.

Cleaning and metrics:

- Commons open-source cleaning audit: 11,051 recent Commons open records
  audited; 11,039 release-ready; 6 weak-graphic review; 6 duplicate review.
- Commons authority distribution in the cleaning audit: 6,564 Commons files with
  extra source evidence; 2,276 institutional/education context; 2,156
  structured catalog source links; 55 Commons-platform-only.
- Layered image/source metrics across all capture records: 19,886 records;
  source-visible 98.51%; publication-grade 98.08%; weighted publication 95.01%;
  open image 89.03%; rights-labeled 100.00%; IMG04 count 295; duplicate image
  URL record rate 0.37%.
- Source coverage v1: active source count 18,312; candidate source count 298;
  pre-surface success registry count 3,500; source pool 100.00%; time-weighted
  source coverage 82.62%; strict distribution adjusted source coverage 26.23%.
- Source coverage v2, still pre-rebuild: source-visible surface rate 97.80%;
  period surface balance 100.00%; period quality-main balance 44.23%; region
  quality-main balance 6.47%; research-quality adjusted source coverage 2.31%.

Script hardening:

- `run_commons_open_authority_weighted_expansion_2026_v1.py`
  now ignores stale query-state rows whose `rows_after` exceeds the saved CSV
  record count, writes after every query that adds rows, extends graphic terms
  for postage stamps/matchbox labels/trade cards/type specimens/letterheads,
  and moves higher-yield topoff lanes ahead of sparse pre-1940 fallback queues.
- `run_commons_open_controlled_expansion_2026_v1.py` now accepts
  `COMMONS_OPEN_CONTROLLED_TARGET_ROWS`, writes after productive queries, and
  marks its manifest stage as pending rebuild.
- Added `run_commons_open_authority_topoff_2026_v1.py` for slow, whitelisted,
  checkpointed topoff runs near a target.

Boundaries:

- No image binaries, thumbnails, screenshots, raw API payload dumps, browser
  sessions, cookies, or local image files were saved.
- IMG03 remains Commons open-license extmetadata only; no IMG01/IMG03 rights
  upgrade was made by heuristic, LLM, platform signal, or terms-of-service
  inference.
- Impact/source priority and topoff query order are internal triage only.
- Full frontend/public-surface rebuild remains deferred to avoid workstation
  instability; surface-level coverage numbers should be interpreted as
  pre-rebuild diagnostics.

Files:

- `scripts/run_commons_open_authority_weighted_expansion_2026_v1.py`
- `scripts/run_commons_open_controlled_expansion_2026_v1.py`
- `scripts/run_commons_open_authority_topoff_2026_v1.py`
- `data/capture_batch_commons_open_authority_weighted_expansion_2026_v1_records.csv`
- `data/capture_batch_commons_open_authority_weighted_expansion_2026_v1_source_summary.csv`
- `data/commons_open_authority_weighted_expansion_2026_v1_quality.csv`
- `data/commons_open_authority_weighted_expansion_2026_v1_query_state.csv`
- `data/capture_batch_commons_open_controlled_expansion_2026_v1_records.csv`
- `data/capture_batch_commons_open_controlled_expansion_2026_v1_source_summary.csv`
- `data/commons_open_controlled_expansion_2026_v1_quality.csv`
- `data/commons_open_controlled_expansion_2026_v1_query_state.csv`
- `data/commons_open_source_cleaning_audit_2026_v1.csv`
- `data/commons_open_source_cleaning_summary_2026_v1.csv`
- `data/layered_image_source_metrics_v1.csv`
- `data/duplicate_image_url_warnings_v1.csv`
- `data/source_coverage_rate_v1.csv`
- `data/source_coverage_region_breakdown_v1.csv`
- `data/source_coverage_period_breakdown_v1.csv`
- `data/source_coverage_rate_v2.csv`
- `data/source_coverage_period_breakdown_v2.csv`
- `data/source_coverage_region_breakdown_v2.csv`
- `data/capture_runs/capture_run_manifest_v1.csv`
- `docs/capture/COMMONS_OPEN_AUTHORITY_WEIGHTED_EXPANSION_2026_v1.md`
- `docs/capture/COMMONS_OPEN_CONTROLLED_EXPANSION_2026_v1.md`
- `docs/capture/COMMONS_OPEN_AUTHORITY_TOPOFF_2026_v1.md`
- `docs/capture/COMMONS_OPEN_SOURCE_CLEANING_AUDIT_2026_v1.md`
- `docs/capture/LAYERED_IMAGE_SOURCE_METRICS_v1.md`
- `docs/capture/SOURCE_COVERAGE_RATE_v1.md`
- `docs/capture/SOURCE_COVERAGE_RATE_v2.md`
- `data/backups/commons_open_authority_weighted_resume_2026_06_13/MANIFEST.md`
- `data/backups/commons_open_controlled_topoff_2026_06_13/`

Next action:

- Run the next public-surface rebuild in an isolated/sandboxed pass rather than
  during long source capture.
- Use the cleaning audit's weak/duplicate review rows to quarantine or repair
  the 12 flagged Commons records before release counting.
- Improve strict distribution coverage: despite source volume, region-quality
  balance remains weak. The next capture/assignment cycle should prioritize
  underrepresented region-to-surface conversion, not only raw source count.
- Revisit weighted publication-grade image coverage at the object level during
  rebuild so multiple photos of one object collapse to one weighted object
  contribution.

Verification:

- `python3 -m py_compile scripts/run_commons_open_authority_topoff_2026_v1.py scripts/run_commons_open_authority_weighted_expansion_2026_v1.py scripts/run_commons_open_controlled_expansion_2026_v1.py`
  passed.
- `python3 scripts/audit_commons_open_source_cleaning_2026_v1.py` passed.
- `python3 scripts/audit_layered_image_source_metrics_v1.py` passed.
- `python3 scripts/audit_source_coverage_rate_v1.py` passed.
- `python3 scripts/audit_source_coverage_rate_v2.py` passed.
- `git diff --check` passed.
- `python3 scripts/audit_secret_patterns.py` still exits non-zero only for old
  raw HTML URL-parameter hits outside this commit scope:
  `data/contemporary_source_scan_probe_1990_2026_v1_raw/CSS0023.html.txt` and
  `data/global_edge_discovery_probe_v1_raw/GED0005.html.txt`.
- Commit-bound safety scan for `API_KEY`, token, password, secret, cookie,
  session, bearer, `/Users/`, and `.env` found no real credential, bearer
  value, cookie/session assignment, API key assignment, private key, local user
  path, or env-file reference. Remaining broad hits are policy/log wording,
  public source titles such as `Secret`/`Secretary`/`poster session`, and
  source-description text from Commons metadata.

## 2026-06-18

### Temporal distribution anomaly audit and recent object-quality review

Added a non-mutating audit layer to inspect the suspicious 2025-2026 counts,
recent stamp/event overrepresentation, and the actual state of 2005-2025
independent studio/project coverage.

Scope and boundaries:

- This round does not rewrite capture records, apply geography relinks, download
  images, or rebuild frontend/public surfaces.
- Uncertain object/source links are kept as review rows instead of blocking the
  run. The audit produces queues for later cleaning rather than pretending every
  row can be resolved automatically.
- `research-repo/` remains out of scope.
- Access-date/source-profile/span records are separated from object-year
  evidence before temporal coverage is interpreted.

Temporal audit:

- Added `scripts/audit_temporal_distribution_anomalies_v1.py`.
- Scanned 19,886 capture records.
- Corrected the audit logic after an initial over-strict pass: `Accessed 2026`
  inside citation text is no longer enough to remove an otherwise object-dated
  row. A row is treated as access-year pollution only when the object date is
  absent or the date fields themselves are driven by accessed/coverage-span
  metadata.
- 2025: 230 all records / 230 object-dated / 0 span-profile records.
- 2026: 820 all records / 106 object-dated / 714 span-profile or access-year
  records.
- Main 2026 pollution causes: 587 source-page image-bearing records, 127 source
  profile records, long spans ending in 2026, and coverage-target/access-year
  metadata being counted as object dates.
- 5-year temporal gap priorities after object-year correction:
  - 2025-2026: 336 object records, share 0.454, severe gap.
  - 1980-1984: 345, share 0.466, severe gap.
  - 2000-2004: 372, share 0.503, severe gap.
  - 1985-1989: 374, share 0.506, severe gap.
  - 1955-1959: 385, share 0.520, severe gap.
  - 1960-1964: 446, share 0.603, moderate gap.
  - 1990-1994: 468, share 0.633, moderate gap.
  - 1995-1999: 500, share 0.676, moderate gap.
  - 2020-2024: 1,140, share 1.541, recent overfull review.

Recent object-quality audit:

- Added `scripts/audit_recent_design_object_quality_v1.py`.
- Scanned 4,838 records dated 2005-2025.
- Added safeguards after finding a feedback-contamination bug: generated audit
  phrases such as `weak event-photo filtering` are excluded from object-quality
  signals so prior machine notes do not trigger new event/photo flags.
- Independent studio/project candidates:
  - High-confidence studio work rows: 6.
  - Unique high-confidence studio keys: 3.
  - Manual-review studio rows: 38.
  - Unique manual-review studio keys: 26.
- Recent downranking queues:
  - Post-2010 stamp/philatelic or commemorative review rows: 1,578.
  - Event/photo/memory material card-only rows: 65.
- Concentration risks:
  - `commons.wikimedia.org`: 4,627 recent-scope rows; 1,642 stamp/event rows.
  - `DigitalNZ`: 54 rows.
  - `archive.org`: 46 rows.
  - `Internet Archive / text and periodical collections`: 46 rows.

Quality-adjusted recent-year findings:

- 2010-2014 are heavily polluted by stamp/philatelic material:
  - 2010 primary 100/186; stamp/event share 0.462.
  - 2011 primary 126/377; stamp/event share 0.666.
  - 2012 primary 114/273; stamp/event share 0.582.
  - 2013 primary 169/516; stamp/event share 0.672.
  - 2014 primary 154/414; stamp/event share 0.628.
- 2015-2019 has a healthier primary share but weak independent studio depth:
  - 2015 primary 138/192; 2016 primary 186/220; 2017 primary 158/253;
    2018 primary 141/226; 2019 primary 132/190.
- 2020-2025 should be reviewed for research value, not expanded by volume
  alone:
  - 2020 primary 153/249.
  - 2021 primary 209/232.
  - 2022 primary 217/233.
  - 2023 primary 236/260.
  - 2024 primary 152/166.
  - 2025 primary 193/230.

Interpretation:

- The earlier high 2026 count was mostly a metrics bug: span/source-profile and
  source-page records were counted as object years.
- The project has enough raw source mass for late-stage work, but contemporary
  research quality is not solved by raw count. Post-2010 stamps and
  event/memory photos must be sampled, demoted to card/appendix, or excluded
  from primary object-success metrics.
- Independent studio/project coverage for 2005-2025 is currently thin and
  should be expanded through authority/design-institution/art-school/community
  sources, not by more broad Commons harvesting.
- Next capture/cleaning priorities should focus on:
  - 1980s posters, record sleeves, magazine covers, identity systems, and
    political/cultural graphics.
  - 2000-2004 studio/platform projects and early web visual communication.
  - Late-1950s/early-1960s institutional posters, book covers, labels,
    advertising, and design-school records.
  - 1990s early web/platform graphics, studios, magazines, posters, and
    cultural identity systems.
  - 2015-2019 independent studios, design platforms, art schools, and community
    archives with explicit object years and source-visible image evidence.

Files:

- `scripts/audit_temporal_distribution_anomalies_v1.py`
- `scripts/audit_recent_design_object_quality_v1.py`
- `data/temporal_distribution_year_counts_v1.csv`
- `data/temporal_distribution_5yr_bins_v1.csv`
- `data/temporal_distribution_10yr_bins_v1.csv`
- `data/temporal_gap_priority_v1.csv`
- `data/temporal_recent_anomaly_review_v1.csv`
- `data/recent_design_object_quality_audit_2005_2025_v1.csv`
- `data/recent_design_object_quality_summary_2005_2025_v1.csv`
- `data/recent_design_object_quality_year_summary_2005_2025_v1.csv`
- `data/independent_studio_work_audit_2005_2025_v1.csv`
- `data/recent_stamp_event_reclassification_queue_v1.csv`
- `data/recent_source_concentration_review_v1.csv`
- `docs/capture/TEMPORAL_DISTRIBUTION_ANOMALY_AUDIT_v1.md`
- `docs/capture/RECENT_DESIGN_OBJECT_QUALITY_AUDIT_2005_2025_v1.md`

Verification:

- `python3 -m py_compile scripts/audit_temporal_distribution_anomalies_v1.py`
  passed.
- `python3 -m py_compile scripts/audit_recent_design_object_quality_v1.py`
  passed.
- `python3 scripts/audit_temporal_distribution_anomalies_v1.py` passed.
- `python3 scripts/audit_recent_design_object_quality_v1.py` passed.

### Release-quality action plan from audit queues

Added a non-mutating release-quality action plan that turns the temporal and
recent-object audits into operational queues. This lets future cleaning and
capture passes keep moving even when individual records cannot be perfectly
linked immediately.

Outputs:

- `scripts/generate_release_quality_action_plan_v1.py`
- `data/release_quality_action_plan_v1.csv`
- `data/release_quality_primary_exclusion_candidates_v1.csv`
- `data/release_quality_capture_targets_v1.csv`
- `docs/capture/RELEASE_QUALITY_ACTION_PLAN_v1.md`

Action rows:

- Total action rows: 2,678.
- Primary/object-year exclusion candidates: 2,357.
- Capture target rows: 11.
- P0 rows: 2,357.
- P1 rows: 321.

Action families:

- `post_2010_stamp_or_philatelic_demote`: 1,578.
- `temporal_span_profile_exclude`: 714.
- `recent_research_value_review`: 321.
- `event_photo_memory_card_only`: 65.

Release-count rule:

- P0 rows are release-count guards, not deletion instructions.
- Post-2010 stamps and philatelic material should be excluded from primary
  object success and retained only as card/appendix material when editorially
  useful.
- Event/photo/memory and poster-session records should be card-only support.
- Source-profile, source-page, long-span, access-year, and coverage-target rows
  should be excluded from object-year metrics until item-level dates are
  resolved.

Capture/cleaning plan:

- `2025-2026` is now a current-year guard, not a volume target. The plan says
  not to expand this bin by volume; only verified studio/project pages with
  clear object years and research value should enter.
- Priority capture targets:
  - `1980-1984`: 1980s posters, record sleeves, magazine covers, identity
    systems, political/cultural graphics.
  - `2000-2004`: studio/platform projects, early web visual communication,
    art-school/community posters.
  - `1985-1989`: same 1980s object families, with low duplication.
  - `1955-1959` and `1960-1964`: institutional posters, book covers, labels,
    advertising, and design-school records.
  - `1990-1994` and `1995-1999`: early web/platform graphics, studio projects,
    posters, magazines, and cultural identity systems.
  - `2015-2019`: independent studio/platform/art-school/community depth, but
    only with explicit object years and source-visible image evidence.
- Avoid patterns for the next capture round: access-year-only pages, source
  profile spans, source-page hero images, event photos, poster-session
  documentation, current-year padding, and more broad Commons stamp harvesting.

Verification:

- `python3 -m py_compile scripts/generate_release_quality_action_plan_v1.py`
  passed.
- `python3 scripts/generate_release_quality_action_plan_v1.py` passed.

### Final-gap capture tooling and failed high-volume Commons attempt

Added a stricter final-gap Commons capture script for the last information
gathering phase:

- `scripts/run_final_gap_open_source_capture_1955_2024_v1.py`

Purpose:

- Target the release-priority gaps identified in the action plan:
  `1945-1949`, `1955-1964`, `1980-1989`, `1990-1999`, `2000-2004`, and
  `2015-2019`.
- Prefer non-mainstream / low-coverage regions and movements, including
  Latin America, Africa, South Asia, Southeast Asia, Eastern Europe/Caucasus,
  Palestine, Indigenous Australia, and related movement/community records.
- Keep the capture rights-aware: metadata, source links, rights evidence, and
  source-hosted image URLs only; no image binaries or raw image downloads.

Safety and quality changes made during this round:

- Added hard exclusions for post-2010 stamp/philatelic drift, event photos,
  poster sessions, conference documentation, designer portraits, page images,
  and other context-only images.
- Added current-year guards so `2025-2026` records are not used as volume
  padding.
- Added object-level variant de-duplication so cropped/v1/v2/A01/A03 variants
  of the same visual work do not count as separate objects.
- Added region-evidence validation: a country/region can no longer be assigned
  only because it appeared in the search query; it must also be visible in
  title, source description, source metadata, categories, collection, or creator
  evidence.
- Added country, creator, collection, year, object-family, and period caps to
  reduce repeated-source concentration.
- Added query state and consecutive-failure protection so interrupted runs can
  resume without reprocessing failed/empty queries.

Run outcome:

- Multiple smoke runs confirmed that the script can capture valid IMG03 Commons
  metadata records when the query path is productive.
- A 400-record intermediate run was intentionally discarded after review because
  it exposed query-induced geography errors and event/photo leakage, including
  non-Vietnam records returned by `Vietnamese poster` searches and conference
  poster-session photographs.
- After adding the stricter region-evidence gate, Commons returned sustained
  `429`/connection failures from repeated testing. No final-gap Commons records
  were merged in this round.
- The failure is therefore a capture-source/rate-limit issue plus a useful
  quality-gate discovery, not a permission upgrade or image-rights expansion.

Related fallback runs:

- `scripts/run_noncanonical_exact_source_capture_1970_2000.py` was run as a
  high-confidence institution/source fallback. The network result was worse
  than the previously committed batch because several exact pages returned
  transient SSL/403 errors, so the regenerated records were not committed.
- `scripts/run_source_coverage_gap_capture_1931_2026.py` was run and then
  tightened after it exposed DSpace false positives such as medical conference
  records, generic handbook records, and non-design repository hits. The script
  relevance filter now excludes these false-positive patterns, but the
  regenerated records were not committed because the run produced mostly IMG04
  text/context records and lost the previous UCT IMG02 poster channel.

Coverage snapshot after reverting unstable outputs:

- `active_source_count`: 18,312.
- `source_coverage_rate_v1`: 82.63% during the transient run, effectively
  unchanged from the prior snapshot after unstable outputs were not staged.
- `strict_distribution_adjusted_source_coverage_rate`: 26.24% during the
  transient run, still low and still the main distribution problem.

Next capture plan:

- Let Commons cool down before a new high-volume run.
- Use the stricter final-gap script, but start with manually verified productive
  phrases/categories instead of broad Commons category assumptions.
- Keep the source-gap DSpace script as a text/context tool only unless its
  results pass image/object relevance review.
- Do not count IMG04-heavy fallback runs as successful image-based archive
  growth.

Verification:

- `python3 -m py_compile scripts/run_final_gap_open_source_capture_1955_2024_v1.py`
  passed.
- `python3 -m py_compile scripts/run_source_coverage_gap_capture_1931_2026.py`
  passed after false-positive filter changes.

### Final-gap productive-seed Commons capture after cooldown

After roughly one hour of Commons cooldown, the final-gap capture was resumed
with a much narrower seed strategy rather than another broad high-volume run.

Script changes:

- `scripts/run_final_gap_open_source_capture_1955_2024_v1.py` now supports
  `FINAL_GAP_QUERY_MODE=high_yield` and `FINAL_GAP_QUERY_MODE=productive_seed`.
- Added `FINAL_GAP_RESET_STATE=1` and `FINAL_GAP_RESET_RECORDS=1` so interrupted
  probe state can be cleared without editing unrelated capture files.
- Added stricter object-level cleanup for context/photo/memory leakage:
  `Fortepan`, poster cutouts, `Schriftzug`, street/environment poster rows,
  department-store poster surroundings, `Last Address` memorial material, and
  black/white vs color variants of the same object.
- Kept the prior hard rules: no image binary downloads, IMG03 only from explicit
  Commons open-license extmetadata, no post-2010 stamp padding, no event-photo
  or poster-session records, and no query-only region assignment.

Run sequence:

- A first broad recovery probe confirmed Commons had cooled down but was too
  inefficient: 133 query-state rows produced only 9 in-memory pass candidates
  before interruption, with 45 query failures and 1,945 rejects. It did not reach
  checkpoint output and was not kept as a records batch.
- A first `high_yield` run was also too wide: it reached only 8 in-memory
  candidates by query 83/2,086 and was stopped.
- A `productive_seed` run using only previously productive phrases was then run
  with `FINAL_GAP_CHECKPOINT_EVERY=1` so every accepted record was written
  immediately.
- Two cleanup reruns were made after manual title/description review. The final
  kept batch is intentionally smaller but cleaner.

Final kept outputs:

- `data/capture_batch_final_gap_open_source_1955_2024_v1_records.csv`
- `data/capture_batch_final_gap_open_source_1955_2024_v1_source_summary.csv`
- `data/final_gap_open_source_capture_1955_2024_v1_quality.csv`
- `data/final_gap_open_source_capture_1955_2024_v1_query_state.csv`
- `data/final_gap_open_source_capture_1955_2024_v1_failures.csv`
- `docs/capture/FINAL_GAP_OPEN_SOURCE_CAPTURE_1955_2024_v1.md`

Final metrics:

- Records captured: 12.
- Image state: 12 IMG03 / 0 IMG04.
- Query failures: 53.
- Distinct source collections: 11.
- Distinct creators: 11.
- Period distribution:
  - `1945_1949_moderate_gap`: 2.
  - `1955_1964_gap`: 5.
  - `1980_1989_gap`: 5.
- Region distribution:
  - Eastern Europe / Caucasus / Russia: 4.
  - Eastern Europe / Caucasus / Poland: 2.
  - Southeast Asia / Indonesia: 4.
  - Southeast Asia / Vietnam: 2.
- Object family distribution: 11 poster, 1 film poster.
- Top reject reasons:
  - `base_parser_rejected`: 2,063.
  - `outside_target_periods`: 898.
  - `region_not_source_evidenced`: 438.
  - `event_photo_or_memory_material`: 91.
  - `weak_source_or_platform_noise`: 77.
  - `non_object_text_or_context_image`: 10.

Review notes:

- The batch is not a meaningful volume increase against the 20,000-source
  release target; it is a quality-controlled final-gap patch.
- Commons search has very low marginal yield under the current strict object
  and rights gates. Further volume should come from institution APIs and known
  collection endpoints rather than broad Commons search phrases.
- No image files, screenshots, cookies, sessions, or raw API payloads were saved.
- No IMG01/IMG03 rights upgrades were made by heuristic, LLM, TOS, or platform
  signal. IMG03 entries derive from explicit Commons extmetadata only.

Light release snapshot after the capture, without a frontend or surface rebuild:

- `public_surfaces`: 13,680.
- `archive_active_public_sources`: 12,342.
- `release_source_coverage_rate`: 61.71% against the 20,000-source release
  target.
- `object_source_visible_rate`: 97.91%.
- `object_verified_open_rate`: 87.96%.
- `object_weighted_publication_grade_rate`: 93.36%; repeated photos/views of
  one object are counted once by object grouping.
- `object_img04_rate`: 1.78%.
- `source_pool_period_fill_rate`: 82.62%.
- `strict_distribution_adjusted_source_coverage_rate`: 26.23%.
- `research_quality_adjusted_source_coverage_rate_v2`: 2.31%.
- Main/sub/text snapshot remains structurally weak: 13,419 main sheets, 261
  sub/support surfaces, 242 independent text sheets, 13,666 dossier text pages,
  and 3,247 dossier sub/card/appendix entries.

Verification:

- `python3 -m py_compile scripts/run_final_gap_open_source_capture_1955_2024_v1.py`
  passed.
- `python3 -m py_compile scripts/run_release_snapshot_v1.py` passed.
- `python3 scripts/run_release_snapshot_v1.py` passed.
- `git diff --check` passed.
- Commit-bound safety scan found no real API key, bearer value, password/secret
  assignment, cookie/session assignment, local user path, or env-file reference.
  Remaining hits are expected policy text, environment-variable names, and
  historical project-log scan terms.

### Pre-freeze data cleaning and release-quality audit

After the final-gap capture showed low marginal yield from broad Commons search,
the next phase shifted from raw source growth to non-mutating data cleaning and
release-quality evaluation. Source count is now treated as capacity context, not
the defining archive-quality metric.

Scripts run:

- `scripts/audit_temporal_distribution_anomalies_v1.py`
- `scripts/audit_recent_design_object_quality_v1.py`
- `scripts/audit_source_coverage_rate_v2.py`
- `scripts/run_release_snapshot_v1.py`
- New consolidated script:
  `scripts/audit_prefreeze_data_cleaning_v1.py`

New pre-freeze audit outputs:

- `data/prefreeze_data_cleaning_summary_v1.csv`
- `data/prefreeze_data_cleaning_priority_queue_v1.csv`
- `data/prefreeze_source_authority_concentration_v1.csv`
- `data/prefreeze_region_period_gap_matrix_v1.csv`
- `docs/capture/PREFREEZE_DATA_CLEANING_AUDIT_v1.md`

Release-quality snapshot used by the audit:

- Capture records scanned: 19,898.
- Public surfaces: 13,680.
- Active public sources: 12,342.
- Object source-visible: 97.91%.
- Object verified-open: 87.96%.
- Object IMG04: 1.78%.
- Strict distribution adjusted coverage: 26.23%.
- Research-quality adjusted source coverage v2: 2.31%.

Pre-freeze cleaning queue:

- P0: 5,287 rows. These can materially distort release metrics if retained as
  primary objects: access-year/span/profile rows, recent stamp drift,
  event/memory material, context images, and source-page/profile records.
- P1: 2,566 rows. These need duplicate, rights, or date review before final
  surface rebuild.
- P2: 2,670 rows. These are metadata cleanup and lower-priority normalization
  tasks.

Action distribution:

- `card_or_appendix_reclass_review`: 2,930.
- `metadata_cleanup_review`: 2,670.
- `recent_stamp_event_reclassification`: 1,643.
- `deduplicate_or_merge_review`: 1,141.
- `manual_rights_or_date_review`: 1,089.
- `date_or_span_reclass_review`: 1,050.

Temporal and recent-object findings:

- The temporal anomaly audit scanned 19,898 capture records and produced 1,050
  recent-year review rows.
- 2026 remains suspicious: 820 capture rows were present, and many are
  access-year/span/profile records rather than true object-year records.
- The weakest five-year bands remain late 1950s/early 1960s, 1980s, 1990s, and
  2000-2004, while 2020-2024 and 2025-2026 need quality review rather than more
  volume.
- The recent-object audit found 1,578 post-2010 stamp-review rows, 65
  event/memory card-only rows, and only 6 high-confidence independent-studio
  rows for 2005-2025. This confirms that recent volume is not yet equivalent to
  research-quality contemporary coverage.

Source and region findings:

- Commons dominates the capture pool: 17,697 scanned capture records come from
  `commons.wikimedia.org`, with 2,582 post-2010 stamp/event-risk rows. Further
  broad Commons capture should remain paused except for manually verified
  collection gaps.
- Institution APIs and known collection endpoints are better next capture
  targets than broad search phrases.
- The region-period matrix shows the largest structural blockers in unresolved
  region groups and thin quality-main coverage for several region/period pairs.
  Region normalization should run before any final surface rebuild.

Script QA note:

- The first pre-freeze classifier over-flagged some authority-weighted Commons
  rows because internal `classification_rationale` text contained the phrase
  "weak event-photo filtering". The script was corrected so risk matching uses
  source-facing metadata fields only.
- Event/memory matching was narrowed from broad words such as `opening`,
  `launch`, and `memory` to event-specific phrases such as `opening ceremony`,
  `exhibition opening`, `launch event`, `memorial`, `remembrance`, and
  `tribute`. This reduced false positives and kept P0 focused on actual
  release-risk rows.

Next execution order:

- First, process the P0 queue and downgrade or exclude stamp/event/context/span
  records before they can be promoted into main sheets.
- Second, process P1 duplicate/date/rights review, with special attention to
  verified-open uplift toward the 95% release target.
- Third, apply region normalization and unresolved-region cleanup before the
  next surface rebuild.
- Fourth, run a targeted rights/source-visible repair pass.
- Fifth, only after the database is cleaner, run a limited surface rebuild and
  reassess main/sub/text structure. Full frontend rebuild remains deferred.

No source records or surfaces were mutated by this audit. No image binaries were
downloaded, no rights states were upgraded, and no research-repo files were
included.

### Active-source stagnation diagnosis and first pre-freeze cleaning gate

The repeated `archive_active_public_sources = 12,342` figure was investigated
because recent capture batches had been added after the last public payload
generation. The result is not that capture failed; it is that the release
snapshot counts only sources represented in `generated/public_surfaces_v1.json`.

Confirmed cause:

- `scripts/run_release_snapshot_v1.py` computes `archive_active_public_sources`
  by deduplicating `sourceName` inside generated public surfaces.
- `generated/public_surfaces_v1.json` was last modified on 2026-06-13, while
  later capture records such as the final-gap and source-coverage batches were
  created on 2026-06-18 and 2026-06-19.
- Therefore recent capture rows are not reflected in release source count until
  a controlled public-surface rebuild runs.

Active-source stage audit:

- `scripts/audit_active_source_success_v1.py` was run to separate source stages.
- `archive_active_public_sources`: 12,342.
- `captured_not_public_sources`: 5,983 after the small Commons quarantine below.
- `pre_surface_only_sources`: 1,615.
- This confirms that several thousand captured source keys are waiting outside
  the public surface layer.

Capture-run manifest audit:

- `scripts/generate_capture_run_manifest_v1.py` regenerated the capture run
  manifest with explicit rebuild inclusion fields.
- Capture record files: 44.
- Included in current public rebuild inputs: 35.
- Not yet included in current public rebuild inputs: 9.
- Important not-yet-included batches include:
  - `commons_open_authority_weighted_expansion_2026_v1`: 5,049 records / 5,015
    source keys after quarantine.
  - `commons_open_category_tree_image_2026_v1`: 4,537 records / 4,537 source
    keys.
  - `commons_open_controlled_expansion_2026_v1`: 929 records / 929 source keys
    after quarantine.
  - `commons_open_region_balance_image_2026_v2`: 800 records / 799 source keys.
  - `commons_open_region_balance_image_2026_v3`: 497 records / 497 source keys.
  - `final_gap_open_source_1955_2024_v1`: 12 records / 12 source keys.
- These batches explain why raw capture volume and release source count diverge.

Executed first cleaning layer:

- `scripts/audit_commons_open_source_cleaning_2026_v1.py` audited 11,051 recent
  Commons rows.
- 11,039 rows were release-ready under that conservative pass.
- 12 rows were quarantined:
  - 6 weak-graphic-evidence rows.
  - 6 duplicate-review rows.
- `scripts/apply_commons_open_source_cleaning_2026_v1.py` removed those 12 rows
  from the two affected Commons capture CSVs and wrote
  `data/commons_open_source_cleaning_quarantine_2026_v1.csv`.
- No images were downloaded and no rights states were upgraded.

New rebuild exclusion gate:

- `scripts/build_prefreeze_public_rebuild_exclusion_v1.py` converts the P0
  pre-freeze cleaning queue into a non-destructive rebuild exclusion table.
- `data/prefreeze_public_rebuild_exclusion_v1.csv` contains 3,549 distinct
  `source_file + capture_id` rows.
- Affected capture files: 29.
- Action distribution:
  - `card_or_appendix_reclass_review`: 2,930.
  - `date_or_span_reclass_review`: 579.
  - `recent_stamp_event_reclassification`: 40.
- `scripts/rebuild_public_surfaces_from_records.py` now reads this exclusion
  table when present and skips matching rows before dedupe and surface
  generation.
- Current rebuild inputs match 1,311 of the exclusion rows. The remaining P0
  exclusions belong mostly to capture batches that are not yet included in
  rebuild inputs; this is intentional until their noise level is reviewed.

Interpretation:

- The source-count plateau is a pipeline-layer issue: capture succeeded, but
  many later sources are either not included in rebuild inputs or are waiting
  behind the new cleaning gate.
- The next controlled rebuild should not blindly include all 9 missing batches.
  It should first decide which not-yet-included batches are safe, then rebuild
  with the pre-freeze exclusion table active.
- Source count should rise only after this controlled rebuild, not immediately
  after probe/capture.

### Chunked pre-freeze rebuild validation

To avoid another large monolithic rebuild, a sandbox chunked rebuild validator
was added and run.

Run setup:

- New script: `scripts/rebuild_public_surfaces_chunked_prefreeze_v1.py`.
- Scope: `all-capture`.
- Chunk size: 2,000 rows.
- Output is metrics/report only. It does not overwrite
  `generated/public_surfaces_v1.json`, frontend payloads, or sharded public
  payloads.
- P0 pre-freeze exclusion table was active.

Run results:

- Capture CSV inputs scanned: 44.
- Raw input rows: 19,886.
- P0 rows skipped by exclusion table: 3,549.
- Deduped candidate rows after exclusion: 16,294.
- Chunks executed: 9.
- Chunks succeeded: 9.
- Chunk errors: 0.
- Chunk surface sum: 16,185.
- Per-chunk source-name sum: 15,079.
- Per-chunk source-visible surface sum: 16,004.
- Per-chunk verified-open surface sum: 15,406.

Chunk distribution:

- chunk 0001: 2,000 rows -> 1,968 surfaces.
- chunk 0002: 2,000 rows -> 1,950 surfaces.
- chunk 0003: 2,000 rows -> 2,000 surfaces.
- chunk 0004: 2,000 rows -> 1,992 surfaces.
- chunk 0005: 2,000 rows -> 2,000 surfaces.
- chunk 0006: 2,000 rows -> 1,997 surfaces.
- chunk 0007: 2,000 rows -> 1,995 surfaces.
- chunk 0008: 2,000 rows -> 1,989 surfaces.
- chunk 0009: 294 rows -> 294 surfaces.

Interpretation:

- The full capture pool can be processed safely in chunks of 2,000 or fewer
  with the pre-freeze exclusion table active.
- The current official release snapshot should not change from this pass,
  because no official payload or frontend file was overwritten.
- The chunk surface/source sums are diagnostic only. A final official public
  payload still needs global grouping, folder aggregation, object-level dedupe,
  and release audits after chunk validation.
- The next safe step is a controlled global merge/finalization pass that uses
  the validated chunks as evidence, not a blind full rebuild.

### Prefreeze candidate payload and full evaluation pass

Built a candidate public-surface payload from the full local capture pool
without overwriting the official payload or frontend mirrors.

Run setup:

- New script: `scripts/build_prefreeze_candidate_payload_v1.py`.
- New script: `scripts/audit_prefreeze_candidate_payload_v1.py`.
- Candidate payload: `generated/public_surfaces_prefreeze_candidate_v1.json`.
- Inputs: all local `data/capture_batch_*_records.csv` files.
- P0 pre-freeze rebuild exclusion table was active.
- No images were downloaded.
- IMG01/IMG03 were not upgraded by heuristic, LLM, TOS, platform signal, or
  source-priority signal.

Candidate build results:

- Capture CSV inputs scanned: 44.
- Raw input rows: 19,886.
- Rows skipped by P0 exclusion: 3,549.
- Rows after exclusion: 16,337.
- Deduped candidate rows: 16,294.
- Candidate public surfaces: 16,180.
- Candidate active public sources: 14,997.
- Candidate research dossiers: 16,180.

Candidate release/gate results:

- Candidate release source coverage rate: 74.98% against the 20,000-source
  release target.
- Candidate object source-visible rate: 98.92%; still below the new 99% target.
- Candidate object verified-open rate: 95.29%; passes the 95% target.
- Candidate weighted publication-grade rate: 97.26%; object-level grouping
  counts repeated photos/views once.
- Candidate object IMG04 rate: 0.82%; passes the 10% maximum target.
- Candidate 2025-2026 surface rate: 1.59%; no longer showing the earlier
  suspicious 2026-heavy failure pattern.
- Candidate strict distribution adjusted source coverage rate: 74.98%.
- Candidate period surface balance rate: 100.00%.
- Candidate macro-region surface balance rate: 85.84% after mapping country
  folder labels back to launch macro-regions.

Candidate sheet/research-packet structure:

- Main sheets: 15,901.
- Sub/support surfaces: 279.
- Independent text sheets: 112.
- Research dossiers: 16,180.
- Dossier text pages: 16,153.
- Dossier sub/card/appendix/child-source pages: 3,639.
- Dossiers with more than two support pages: 20.
- Dossiers with more than five text pages: 0.

Candidate warnings:

- Integrity audit found 5 exact repeated image URLs across 10 surfaces, all in
  Another Graphic rows. This reinforces the next cleaning rule: contemporary
  studio/platform batches must be deduped by image URL and project family before
  promotion.
- Recent post-2010 stamp-like rows: 5.
- Event/photo-like rows: 63; these should usually be card/support material, not
  standalone design-object main sheets.
- Unresolved region remains very high at 4,942 candidate surfaces. This is now
  the largest cleaning problem before formal promotion.
- `data/geographies.csv` still lacks enough country-level rows for several
  discovered labels, so the candidate evaluator includes a conservative
  reporting-only fallback map. The taxonomy table itself still needs a proper
  controlled-geography update.

Official-vs-candidate interpretation:

- The official active public source count remains 12,342 because the official
  `generated/public_surfaces_v1.json` was not overwritten.
- The candidate layer reaches 14,997 active public sources, proving the
  source-count plateau is caused by promotion/rebuild state rather than missing
  capture.
- The remaining release gap is roughly 5,003 active public sources if the final
  target stays at 20,000.
- The next round should prioritize data cleaning and controlled promotion over
  broad raw capture: unresolved geography, duplicate contemporary platform rows,
  event/photo reclassification, and the remaining 1.08 percentage-point gap in
  object source visibility.

### Candidate promotion blocker audit and duplicate-delta gate

Executed the first small promotion-cleaning layer after the candidate payload
evaluation.

New audit layer:

- New script: `scripts/audit_prefreeze_candidate_promotion_blockers_v1.py`.
- Inputs: `generated/public_surfaces_prefreeze_candidate_v1.json`, all local
  capture record CSVs, and the current pre-freeze rebuild exclusion table.
- Outputs:
  - `data/prefreeze_candidate_promotion_blockers_v1.csv`
  - `data/prefreeze_candidate_geo_repair_queue_v1.csv`
  - `data/prefreeze_candidate_exclusion_delta_v1.csv`
  - `data/prefreeze_candidate_promotion_blockers_summary_v1.csv`
  - `docs/capture/PREFREEZE_CANDIDATE_PROMOTION_BLOCKERS_v1.md`

Important implementation fix:

- The first blocker pass incorrectly normalized image URLs by dropping query
  strings. Smithsonian image IDs live in `?id=...`, so that caused false
  duplicate matches.
- The script now preserves query strings for image-URL duplicate detection.
- After the fix, the duplicate delta matched the integrity audit: only 5 exact
  duplicate image URL variants remained, all from Another Graphic duplicate
  visual/project rows.

Gate update:

- `scripts/build_prefreeze_public_rebuild_exclusion_v1.py` now merges
  `data/prefreeze_candidate_exclusion_delta_v1.csv` when present.
- The merged gate remains non-destructive: it skips matching
  `source_file + capture_id` rows before future public-surface rebuilds, but
  does not delete capture records or mutate rights states.
- Exclusion rows increased from 3,549 to 3,554.
- New action count: `duplicate_visual_variant_review`: 5.

Post-cleaning candidate rebuild:

- Candidate public surfaces: 16,175, down from 16,180.
- Candidate active public sources: 14,997, unchanged.
- Candidate object source-visible rate: 98.92%, still just below the 99% target.
- Candidate object verified-open rate: 95.29%, still passing.
- Candidate weighted publication-grade rate: 97.26%, still passing.
- Candidate object IMG04 rate: 0.82%, still passing.
- Candidate 2025-2026 surface rate: 1.58%, still not showing a 2026-heavy bug.
- Candidate exact repeated image URLs: 0, down from 5.

Remaining promotion blockers:

- Promotion blocker rows: 7,285.
- P0 blocker rows: 2, now review-only event/context flags; they are not merged
  automatically because false positives can include actual designed
  affiches/posters.
- Unresolved-region repair rows: 4,938.
- Source-visible gap rows: 181.
- Event/photo/context-image review rows: 2,166.
- Exclusion delta rows after the gate merge: 0.

Interpretation:

- The small duplicate-cleaning layer worked and did not reduce source coverage.
- The next substantial step is not another broad source scrape; it is geography
  repair and controlled reclassification:
  - resolve the 4,938 unresolved-region rows;
  - review the 181 IMG00/IMG04 source-visible gaps without rights upgrades;
  - manually reclassify event/photo/context-image rows into card/support where
    they are not item-level designed surfaces;
  - only then consider promoting the candidate payload toward the official
    release layer.

### Prefreeze geography repair and cleaning review

Executed the first deterministic geography repair layer and the follow-up
source-visible/context-image review layer against the pre-freeze candidate
payload. This was a candidate-only cleaning run: it did not overwrite the
official `generated/public_surfaces_v1.json`, did not mirror data into the
frontend, did not download images, and did not upgrade IMG01/IMG03 rights states
by heuristic, LLM, TOS, platform, or source-priority signals.

Implementation:

- New script: `scripts/build_prefreeze_geo_repair_decisions_v1.py`.
- New cumulative geography override file:
  `data/prefreeze_geo_repair_overrides_v1.csv`.
- `scripts/rebuild_public_surfaces_from_records.py` now supports an auditable
  in-memory pre-freeze geography override layer keyed by
  `source_file + capture_id`.
- `scripts/build_prefreeze_candidate_payload_v1.py` now applies the same
  override layer while building the ignored candidate payload.
- `scripts/run_midcentury_capture_1930_1970.py` now honors explicit
  `region_folder`, `region_ids`, and `geo_ids` before falling back to old
  keyword inference.
- New review script: `scripts/audit_prefreeze_cleaning_review_v1.py`.

Geography repair results:

- Initial unresolved-region queue before repair: 4,938 rows.
- First deterministic pass produced 4,720 override rows.
- Second incremental pass preserved those overrides and added 88 more.
- Cumulative geography override rows: 4,808.
- Remaining unresolved-region rows after candidate rebuild and blocker audit:
  133.
- Remaining unresolved rows are mostly low-evidence IA/Met/Wellcome/LOC items
  or records that need item-level source recapture, not safe deterministic
  geography binding.

Candidate metrics after geography repair:

- Candidate public surfaces: 16,175.
- Candidate active public sources: 14,997.
- Candidate object source-visible rate: 98.92%.
- Candidate object verified-open rate: 95.29%.
- Candidate weighted publication-grade rate: 97.26%.
- Candidate object IMG04 rate: 0.82%.
- Candidate strict distribution adjusted source coverage rate: 74.98%.
- Exact repeated image URLs: 0.

Remaining promotion blockers after rule correction:

- Promotion blocker rows: 2,463.
- P0 blocker rows: 0.
- P1 blocker rows: 2,463.
- Unresolved-region rows: 133.
- Source-visible gap rows: 181.
- Event/photo/context-image review rows: 2,149.
- Exclusion delta rows: 0.

Source-visible review:

- New output: `data/prefreeze_source_visible_gap_review_v1.csv`.
- IMG04/IMG00 source-visible review rows: 181.
- Review classes:
  - text-only item or collection: 96.
  - image missing or parser gap: 41.
  - source registry context page: 37.
  - registry/archive landing page: 7.
- Interpretation: the 181-row gap should be handled by recapture, card/support
  demotion, or context-source treatment, not by deleting rows just to improve a
  metric.

Context-image review:

- New output: `data/prefreeze_context_image_review_v1.csv`.
- Context/event/photo review rows: 2,149.
- Review classes:
  - weak context/profile/own-work image: 1,899.
  - philatelic or stamp-like: 208.
  - event/photo language with design claim: 42.
- The blocker audit was corrected so English `talk/lecture` no longer causes
  broad false positives, and `advertisement` / `typography` stems count as
  design evidence.

Next recommended step:

- Build a demotion gate for the 1,899 weak context/profile image rows and 208
  philatelic/stamp-like rows, but keep it reviewable rather than destructive.
- Keep the 42 event/photo rows with design evidence in manual review.
- Recapture or demote the 181 IMG00/IMG04 source-visible gaps.
- Defer official payload promotion until the context/stamp demotion pass and
  source-visible recapture pass are both evaluated.

### Prefreeze Surface Role Override Layer and Main/Sub/Text Audit

Scope:

- Added the first reviewable surface-role cleanup layer for the pre-freeze
  candidate payload.
- The layer addresses weak context/profile images, stamp-like records, registry
  context pages, and text-only source gaps by changing candidate presentation
  role only.
- No official payload was overwritten, no image files were downloaded, and no
  IMG01/IMG03 rights or image-state upgrades were made.
- `research-repo/` remained read-only and was not edited or staged.

Implementation:

- New script: `scripts/build_prefreeze_surface_role_overrides_v1.py`.
- New role override outputs:
  - `data/prefreeze_surface_role_override_decisions_v1.csv`.
  - `data/prefreeze_surface_role_overrides_v1.csv`.
  - `data/prefreeze_surface_role_override_summary_v1.csv`.
  - `docs/capture/PREFREEZE_SURFACE_ROLE_OVERRIDES_v1.md`.
- `scripts/rebuild_public_surfaces_from_records.py` now supports an auditable
  pre-freeze surface role override layer keyed by `source_file + capture_id`.
- `scripts/build_prefreeze_candidate_payload_v1.py` applies the same role
  override layer and records `role_overrides_applied`.
- `scripts/run_midcentury_capture_1930_1970.py` now preserves explicit
  `surface_disposition_override` values when present.
- New audit script: `scripts/audit_prefreeze_main_sub_text_structure_v1.py`.

Role override results:

- Role decision rows: 2,330.
- Candidate role override rows: 2,247.
- Applied card demotions: 1,943.
- Applied support-appendix/subsheet demotions: 304.
- Manual review only: 42 event/photo language rows with some design evidence.
- Manual recapture/review: 41 image-missing or parser-gap rows.
- Review classes:
  - weak context/profile/own-work image: 1,899.
  - philatelic or stamp-like: 208.
  - text-only item or collection: 96.
  - event/photo language: 42.
  - image missing or parser gap: 41.
  - source registry context page: 37.
  - registry/archive landing page: 7.

Candidate metrics after role override:

- Candidate public surfaces: 16,175.
- Candidate active public sources: 14,997.
- Candidate release source coverage rate: 74.98% against the 20,000-source
  final target.
- Candidate object source-visible rate: 98.92%.
- Candidate object verified-open rate: 95.29%.
- Candidate weighted publication-grade rate: 97.26%.
- Candidate object IMG04 rate: 0.82%.
- Candidate strict distribution adjusted source coverage rate: 74.98%.
- Candidate 2025/2026 surface rate: 1.58%.
- Exact repeated image URLs: 0.

Promotion and cleaning state after role override:

- Promotion blocker rows: 2,463.
- P0 blocker rows: 0.
- P1 blocker rows: 2,463.
- Unresolved-region rows: 133.
- Source-visible gap rows: 181.
- Event/photo/context-image review rows: 2,149.
- Exclusion delta rows: 0.

Main/sub/text structure audit:

- New outputs:
  - `data/prefreeze_main_sub_text_structure_summary_v1.csv`.
  - `data/prefreeze_main_sub_text_structure_by_period_v1.csv`.
  - `data/prefreeze_main_sheet_structure_review_v1.csv`.
  - `docs/capture/PREFREEZE_MAIN_SUB_TEXT_STRUCTURE_v1.md`.
- Candidate surfaces scanned: 16,175.
- Candidate research dossiers: 16,175.
- Publication-role distribution:
  - main sheet: 13,737.
  - card: 1,943.
  - support packet appendix text: 489.
  - thin visual support packet: 3.
  - merge candidate support packet: 1.
- Dossier anchor distribution:
  - main sheet: 13,739.
  - card: 1,944.
  - subsheet: 492.
- Dossier page distribution:
  - text page: 14,231.
  - main sheet: 13,739.
  - appendix: 3,089.
  - card: 1,944.
  - subsheet: 492.
  - child source record: 131.
- Main sheets with explicit `compoundChildren`: 9.
- Main sheets with more than two child records: 9.
- Main sheets with more than five child records: 4.
- Dossiers with more than two subsheet pages: 0.
- Dossiers with more than five text pages: 0.
- Main-sheet structure review rows: 13,728.

Interpretation:

- The role cleanup reduces obvious weak/context pages from main-sheet status, but
  the archive still behaves mostly as one-source-per-main-sheet.
- Current `compoundChildren` is the only explicit relation signal in the
  candidate payload, so main/sub/card/text grouping is still underdeveloped.
- This supports the user's concern: the next structural milestone should be a
  relation-density and packet-building pass, not another blind source-volume
  push.
- Time-period distribution after role cleanup remains uneven: 1914-1945 and
  1970-1989 are strong; 1990-1999 and 2000-2009 remain comparatively thin; the
  2020-2026 region is now mostly cards after context demotion.

Next recommended step:

- Keep the candidate payload local/ignored and continue using it for pre-freeze
  audits.
- Build a deterministic packetization audit that groups nearby objects by
  source family, creator/studio, country, movement/theme, and period span.
- Treat grouped records as research packets first, then decide which anchors
  become main sheets, which become subsheets, which become cards, and which need
  editorial text pages.
- Recapture or manually review the remaining 181 source-visible gaps and 133
  unresolved-region rows before official payload promotion.

Methodological note added after review:

- New brief: `docs/capture/PREFREEZE_MAIN_SUB_PACKETIZATION_BRIEF_v1.md`.
- The next round should make main-sheet status stricter. A main sheet should be
  a research packet anchor: a representative work, project, institution,
  movement, communication method, or design idea with enough source depth and
  relation density to support expansion.
- A single captured object should not become a main sheet by default. Thin
  single-object records should usually become subsheets, cards, or appendices
  unless impact, scarcity, or source depth justifies main-sheet promotion.
- Research resources should be integrated as packet evidence: source family,
  rights trail, text pages, appendices, cards, and related object clusters.
- The next audit should produce main-promotion review, subsheet cluster
  suggestions, card/support evidence suggestions, editorial text needs, and
  packet confidence levels.

### Prefreeze Packetization Audit v1

Scope:

- Added a stricter advisory audit for main/sub/card/text packetization.
- The audit treats main sheets as research packet anchors rather than default
  object pages.
- It only generates CSV recommendations and a report. It does not mutate the
  official public payload, does not download images, and does not upgrade rights
  or image states.

Implementation:

- New script: `scripts/audit_prefreeze_packetization_candidates_v1.py`.
- New outputs:
  - `data/prefreeze_packetization_candidates_v1.csv`.
  - `data/prefreeze_packetization_surface_recommendations_v1.csv`.
  - `data/prefreeze_packetization_summary_v1.csv`.
  - `data/prefreeze_packetization_source_family_summary_v1.csv`.
  - `docs/capture/PREFREEZE_PACKETIZATION_AUDIT_v1.md`.
- The audit derives candidate packets from stricter relation keys:
  - same source identifier.
  - same normalized title inside source family.
  - shared title/series stem.
  - creator + region + medium + decade.
  - collection + region + decade.
  - folder cell + decade as weak planning evidence only.
- The scoring model considers relation density, source depth, visible image
  state, rights-reviewed state, region scarcity, design-language signal, and
  weak-object signals such as stamps, event/photo/session records, natural
  history images, and other context-only material.

Packetization results:

- Candidate surfaces scanned: 16,175.
- Candidate packet rows: 2,259.
- Surfaces with at least one packet relation: 10,785.
- Surfaces without strict packet relation: 5,390.
- Surface-level recommendations:
  - subsheet or card review: 4,906.
  - card or appendix candidate: 3,876.
  - subsheet candidate: 3,735.
  - existing card: 1,944.
  - main sheet manual review: 668.
  - main sheet anchor candidate: 502.
  - existing appendix/subsheet support: 492.
  - singleton main sheet review: 52.
- Packet-level recommendations:
  - manual packet or card review: 1,253.
  - demote parallel mains to subsheet cluster: 511.
  - promote one main anchor and demote members to subsheets: 428.
  - packet review only: 46.
  - hold as support or editorial review: 21.
- Packet confidence distribution:
  - high: 782.
  - medium: 1,011.
  - low: 466.

Quality-control adjustment:

- The first packetization pass correctly exposed relation clusters but still
  treated too many weak Commons series as possible main-anchor packets.
- The rule set was tightened so stamp/Colnect/philatelic, event/session,
  natural-history, and similar context-only clusters route to
  `manual_packet_or_card_review` rather than automatic main-anchor treatment.
- All stamp-keyed packet actions in the second pass route to manual/card review.

Source-family finding:

- Wikimedia Commons remains structurally dominant: 15,063 candidate surfaces,
  12,947 current main sheets, 9,950 packet-member surfaces, and 461 candidate
  anchors after stricter filtering.
- Gallica has 239 candidate surfaces, all currently main sheets, with 11
  candidate anchors after packetization.
- This confirms that source count alone is no longer the primary constraint.
  The next bottleneck is source-family concentration, packet integration, and
  main-sheet overclaiming.

Interpretation:

- A large part of the current archive should become packet members rather than
  standalone main sheets.
- High-confidence packet anchors should be sampled before becoming an applied
  override layer.
- Medium/low confidence packets should stay as planning evidence until reviewed.
- Singleton records should not be automatically deleted or demoted; they need a
  stricter main/sub/card decision based on source depth, impact, scarcity, and
  editorial need.

Next recommended step:

- Sample the 502 `main_sheet_anchor_candidate` rows and the 511
  `demote_parallel_mains_to_subsheet_cluster` packet rows.
- Build a reviewed packet-role override layer only from sampled high-confidence
  clusters.
- Keep the 1,253 manual packet/card review rows out of automatic promotion.
- Start a source-family authority audit focused on Commons over-concentration,
  Gallica all-main behavior, and institution-specific repeated-series patterns.

### Prefreeze Packet Role Review Draft v1

Scope:

- Added the first packet-role review queue and conservative draft override file
  derived from the packetization audit.
- This pass is still advisory. It does not wire packet decisions into rebuild
  scripts, does not mutate the official payload, does not download images, and
  does not change rights or image states.
- Draft override rows intentionally keep `source_file` blank. Applying the
  draft requires a later audited join against the capture registry or candidate
  payload source metadata.

Implementation:

- New script: `scripts/build_prefreeze_packet_role_review_v1.py`.
- New outputs:
  - `data/prefreeze_packet_role_review_queue_v1.csv`.
  - `data/prefreeze_packet_role_override_draft_v1.csv`.
  - `data/prefreeze_packet_role_review_summary_v1.csv`.
  - `docs/capture/PREFREEZE_PACKET_ROLE_REVIEW_v1.md`.

Review results:

- Packet candidates scanned: 2,259.
- Surface recommendations scanned: 16,175.
- Packet role review queue rows: 9,725.
- Conservative draft override rows: 2,452.
- Packet-level lanes:
  - manual packet or card review: 1,253 packets.
  - sample before override: 632 packets.
  - conservative draft override: 307 packets.
  - packet reference only: 67 packets.
- Surface-level lanes:
  - manual packet or card review: 5,669 rows.
  - conservative draft override: 2,458 rows.
  - sample before override: 1,598 rows.
- Review decisions:
  - review only: 7,267.
  - draft subsheet demote: 2,142.
  - keep main anchor candidate: 161.
  - keep card support: 103.
  - draft card demote: 46.
  - anchor manual review: 6.
- Draft override role distribution:
  - support packet appendix text: 2,142.
  - main sheet: 161.
  - card: 149.

Interpretation:

- The conservative draft confirms that only a small fraction of current
  candidate surfaces should remain main anchors without further manual review.
- The largest safe movement is not deletion; it is moving parallel main sheets
  into packet member roles around selected anchors.
- Manual packet/card review remains larger than the draft layer, which is
  expected because weak Commons clusters, stamp/philatelic clusters,
  event/session/context records, and broad folder-cell groupings should not be
  auto-applied.
- This gives the archive a clearer next-stage workflow: review packet anchors,
  join source files, then apply a small audited override layer before another
  candidate rebuild.

Next recommended step:

- Sample the 2,452 conservative draft override rows by source family, period,
  and region before applying them.
- Join draft rows to `source_file + capture_id` only after sample review.
- Keep the 5,669 manual packet/card rows as editorial planning evidence.
- Begin a source-family authority audit to reduce repeated-source overclaiming,
  especially Commons and all-main institutional clusters.

### Prefreeze Packet Role Apply Readiness v1

Scope:

- Added a source-file join and confidence gate for the packet-role draft layer.
- This pass is still pre-application. It does not mutate capture records, does
  not rebuild the official payload, does not download images, and does not
  change rights or image states.
- The goal is to separate a small rebuild-testable queue from the much larger
  packet/research-combination review queue.

Implementation:

- New script: `scripts/build_prefreeze_packet_role_apply_readiness_v1.py`.
- New outputs:
  - `data/prefreeze_packet_role_apply_ready_v1.csv`.
  - `data/prefreeze_packet_role_hold_review_v1.csv`.
  - `data/prefreeze_packet_role_sample_review_v1.csv`.
  - `data/prefreeze_packet_role_source_join_summary_v1.csv`.
  - `docs/capture/PREFREEZE_PACKET_ROLE_APPLY_READINESS_v1.md`.

Readiness results:

- Draft rows scanned: 2,452.
- Source-file join status:
  - unique capture id: 2,446.
  - resolved duplicate capture id: 3.
  - ambiguous capture id: 2.
  - missing capture id: 1.
- Apply-ready rows after the stricter confidence gate: 200.
- Hold-review rows: 2,091.
- Reference-only main-anchor rows: 161.
- Deterministic sample-review queue rows: 2,270.
- Apply-ready role distribution:
  - support packet appendix text: 200.
- Top hold reasons:
  - Commons/Colnect or source-family sample review required: 1,253.
  - unstable or unresolved region/transnational binding: 675.
  - card-related visual/editorial sample review required: 149.
  - historical/geography review periods: 10.
  - non-unique source joins: 3.
  - stamp/event/photo/context term review: 1.
- Apply-ready source families:
  - Gallica / BnF APIs: 106.
  - DigitalNZ: 36.
  - Princeton University Library Digital Collections / Figgy: 29.
  - Wellcome Collection Catalogue API: 11.
  - Georgia State University Library Digital Collections / CONTENTdm: 9.
  - V&A Collections API: 5.
  - Cleveland Museum Open Access API: 3.
  - Art Institute of Chicago API: 1.

Interpretation:

- The first run showed that a naive "joinable and high confidence" rule would
  have admitted 2,139 rows, including historical and Commons/geography-risk
  clusters. The script was tightened before logging final outputs.
- The current 200-row apply-ready file is deliberately small. It is suitable
  for the next sandbox rebuild test, not for direct official publication.
- Most packet combinations remain research material until source-family,
  geography, and visual/editorial samples are reviewed. This is especially
  important for Commons file-page clusters, transnational labels, historical
  conflict periods, and card/support candidates.
- The readiness layer gives the next rebuild a controlled entry point: apply a
  200-row source-file-backed override slice, build in small chunks, then compare
  main/sub/text counts and release-gate metrics before expanding.

Next recommended step:

- Sample the 200 apply-ready rows across source family, year, and packet type.
- If the sample passes, create a separate applied override file from
  `data/prefreeze_packet_role_apply_ready_v1.csv` only.
- Run a small candidate rebuild chunk before attempting any broad packet-role
  rewrite.
- Keep the 2,091 hold-review rows for confidence cleanup, source-family
  authority review, and later research packet design.

### Prefreeze Packet Role Applied Override Sandbox and Main Anchor Markers v1

Scope:

- Created a sandbox merged role override layer from the existing pre-freeze
  role overrides plus the 200 packet apply-ready rows.
- Rebuilt only the local candidate payload with this sandbox role layer. The
  official `generated/public_surfaces_v1.json` and frontend mirrors were not
  intentionally rebuilt or overwritten in this pass.
- Added a non-mutating main-anchor strictness audit for main/sub/text archival
  planning. Main-sheet status is treated as a soft research-packet anchor
  marker, not as a final release gate or automatic demotion rule.

Implementation:

- New script: `scripts/build_prefreeze_packet_role_applied_overrides_v1.py`.
- New script: `scripts/audit_prefreeze_main_anchor_strictness_v1.py`.
- `scripts/rebuild_public_surfaces_from_records.py` now accepts
  `PREFREEZE_ROLE_OVERRIDES_PATH` so candidate builds can explicitly point at a
  sandbox role override file while the canonical pre-freeze role override file
  remains unchanged.
- New outputs:
  - `data/prefreeze_surface_role_overrides_packet_applied_v1.csv`.
  - `data/prefreeze_packet_role_applied_override_summary_v1.csv`.
  - `docs/capture/PREFREEZE_PACKET_ROLE_APPLIED_OVERRIDES_v1.md`.
  - `data/prefreeze_main_anchor_strictness_review_v1.csv`.
  - `data/prefreeze_main_anchor_cluster_review_v1.csv`.
  - `data/prefreeze_main_anchor_strictness_summary_v1.csv`.
  - `docs/capture/PREFREEZE_MAIN_ANCHOR_STRICTNESS_v1.md`.

Sandbox override results:

- Base pre-freeze role override input rows: 2,247.
- Packet apply-ready rows considered: 200.
- Merged sandbox override rows: 2,445.
- Collision or rejected rows: 0.
- Merged role distribution:
  - card: 1,943.
  - support packet appendix text: 502.
- Override source distribution:
  - existing surface role override layer: 2,245.
  - packet role apply-ready layer: 200.

Candidate rebuild and release snapshot:

- Candidate surfaces: 16,175.
- Candidate active public sources: 14,997.
- Candidate object source-visible rate: 98.92%.
- Candidate object verified-open rate: 95.29%.
- Candidate object weighted publication-grade rate: 97.26%.
- Candidate object IMG04 rate: 0.82%.
- Candidate strict distribution adjusted source coverage rate: 74.98%.
- These metrics remained stable because this pass changed structure roles only,
  not source count, image state, or rights state.

Main/sub/text structure after the sandbox role layer:

- Candidate main sheets: 13,537.
- Candidate cards: 1,943.
- Candidate support packet appendix text rows: 689.
- Thin visual support packets: 3.
- Main-sheet review rows: 13,528.
- Main sheets with explicit `compoundChildren`: 9.
- Main dossiers with more than two subsheet pages: 0.
- Main dossiers with more than five text pages: 0.
- Text pages generated in dossiers: 14,231.
- Subsheet pages generated in dossiers: 692.
- Appendix pages generated in dossiers: 3,089.

Soft main-anchor marker audit:

- Main sheets scanned: 13,537.
- Region/theme/source/decade clusters with at least three main records: 68.
- Main anchor review lanes:
  - support or card review: 9,251.
  - main anchor manual review: 3,809.
  - keep main anchor candidate: 397.
  - needs packet/subsheet assignment: 42.
  - needs editorial text: 38.
- The audit adds `research_packet_anchor_marker` values so main sheets can
  function as provisional research packet anchors without pretending that the
  packet structure is already final.
- The rule set was corrected during this pass: a naive substring match treated
  `stamp` inside French `estampe` as a philatelic risk. The final script uses
  word-boundary matching so Gallica print/poster records are not misflagged by
  that false positive.

Interpretation:

- The 200-row packet apply-ready layer moves a small, controlled set of records
  toward sub/support packet roles and lowers the main-sheet review queue by the
  expected amount without harming release-gate metrics.
- The structural problem remains large: most current main sheets do not yet
  have explicit sub-sheet relations, and dossiers are still mostly one-anchor
  packets with one text page.
- Main sheet should be treated as a provisional research-packet anchor class.
  It can carry anchor intent before the full packet is assembled, but it should
  not be read as proof that a surface already has enough text, relation density,
  or editorial framing.
- The next meaningful work is not more raw source count; it is source-family
  authority cleanup, main-anchor sample review, and then a carefully applied
  packet/sub/text assignment layer.

Next recommended step:

- Sample the 397 `keep_main_anchor_candidate` rows and 3,809
  `main_anchor_manual_review` rows by source family, period, and region.
- Review the 9,251 `support_or_card_review` rows in priority buckets,
  especially Commons file-source clusters, unresolved/transnational geography,
  event/photo/context records, stamps, and natural-history/geology false
  positives.
- Convert only reviewed packet groups into an applied override layer, then run
  another candidate rebuild before touching official payload/front-end data.
