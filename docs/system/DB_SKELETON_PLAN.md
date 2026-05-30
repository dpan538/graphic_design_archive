# Database Skeleton Plan v0

**Status:** Active planning document.  
**Rule:** No source crawling, scraping, or bulk ingestion should begin until the database skeleton gates below are complete.

## Purpose

The database skeleton is the contract between research methodology, ingestion, search, and future frontend work. It must be complete before data acquisition begins because this project depends on integrity, reproducibility, rights handling, and source traceability.

The skeleton does not mean the database is full. It means the database can safely receive records without losing evidence, rights context, classification basis, or review history.

## Current Files

- `db/001_initial_schema.sql`: seed tables, core entity model, source records, citations, assertions, classifications, image assets, and search documents.
- `db/002_operational_skeleton.sql`: operational tables for reviews, rights, ingestion runs, snapshots, external identifiers, workflow events, releases, and audit logs.
- `DATA_DICTIONARY.md`: field definitions for seed data.
- `SCHEMA_DRAFT.md`: conceptual schema draft.
- `SEARCH_VALIDATION.md`: deterministic seed search validation.
- `data/*.csv`: seed data.
- `data/archive_seed.sqlite`: reproducible seed snapshot.

## Skeleton Gates

### Gate 1: Seed Layer

Status: complete.

Requirements:

- historical nodes exist;
- movement taxonomy exists;
- media/technology taxonomy exists;
- source registry exists;
- search vocabulary exists;
- rights strategy exists;
- CSV files are parseable;
- SQLite snapshot can be generated.

Evidence:

- `data/*.csv`
- `scripts/generate_seed_data.py`
- `scripts/build_sqlite_snapshot.py`
- `data/archive_seed.sqlite`

### Gate 2: Canonical Schema

Status: draft complete, implementation pending.

Requirements:

- PostgreSQL schema exists for seed tables;
- PostgreSQL schema exists for entities;
- PostgreSQL schema exists for source records;
- PostgreSQL schema exists for citations;
- PostgreSQL schema exists for assertions;
- PostgreSQL schema exists for classifications;
- PostgreSQL schema exists for image assets;
- PostgreSQL schema exists for searchable documents.

Evidence:

- `db/001_initial_schema.sql`

### Gate 3: Operational Governance

Status: draft complete, implementation pending.

Requirements:

- source terms review table;
- rights review table;
- ingestion run table;
- ingestion event table;
- source record snapshot table;
- editorial review table;
- workflow event table;
- assertion review table;
- external identifier table;
- authority source table;
- audit log table;
- export/release tables.

Evidence:

- `db/002_operational_skeleton.sql`

### Gate 4: Import and Validation Scripts

Status: offline tooling complete; live PostgreSQL execution pending.

Requirements:

- script to create local PostgreSQL database or connect to configured database;
- script to run migrations in order;
- script to import seed CSVs;
- script to validate row counts;
- script to validate required fields;
- script to build `searchable_documents`;
- script to export reproducible CSV/JSONL snapshots from PostgreSQL.

Current implementation:

- `scripts/generate_postgres_seed_sql.py`
- `db/010_seed_data.sql`
- `db/004_coverage_skeleton.sql`
- `db/005_global_classification_skeleton.sql`
- `scripts/run_db_migrations.py`
- `db/900_validation_queries.sql`
- `scripts/check_db_skeleton.py`
- `db/README.md`

Global coverage seed files now included in the validation gate:

- `data/classification_axes.csv`
- `data/geographies.csv`
- `data/regional_movements.csv`
- `data/regional_event_nodes.csv`

Offline checks pass. Live PostgreSQL validation requires a configured `DATABASE_URL`.

No source crawling should happen before this gate is complete.

### Gate 5: Manual Source Record Trial

Status: pending.

Requirements:

- manually create 20-30 source records from launch-scope sources;
- each source record must include source link, access date, rights state, citation, and capture method;
- no automated crawling;
- no local image copying unless rights are explicitly open;
- test that records can move through workflow states;
- test search over source records and seed records together.

This is the first moment real external records may enter the database.

### Gate 6: Ingestion Protocol

Status: pending.

Requirements:

- source terms review completed for each target source;
- rights review policy mapped to each target source;
- ingestion run config format defined;
- error logging defined;
- snapshot/hash policy defined;
- rollback strategy defined;
- rate limit and robots/terms policy documented;
- explicit source allowlist created.

Only after this gate may controlled ingestion begin.

## Data Acquisition Rule

No automated data acquisition should begin until:

1. PostgreSQL migrations run successfully;
2. seed imports validate successfully;
3. operational review tables exist;
4. manual source record trial succeeds;
5. source-specific terms and rights reviews are completed;
6. `PROJECT_LOG.md` records the decision to begin a specific ingestion run.

## Frontend Handoff Boundary

Frontend work should not depend on live scraping or unstable source records.

Cursor/front-end implementation should receive:

- stable API contract;
- documented entity types;
- documented search result shape;
- rights display rules;
- citation panel requirements;
- source registry fields;
- no WebLLM requirement;
- no assumption that images are locally available.

The first frontend should consume seed and manually reviewed records only.

## Next Tasks

1. Create migration runner.
2. Create PostgreSQL seed import script.
3. Create database validation script.
4. Create source-record manual entry template.
5. Create API contract draft for future frontend work.
6. Update `PROJECT_LOG.md` after each completed task.
