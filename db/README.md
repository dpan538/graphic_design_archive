# Database Skeleton

This directory contains the PostgreSQL database skeleton for the Modern Graphic Design History Archive Index.

No crawling or bulk ingestion should begin until the skeleton gates in `DB_SKELETON_PLAN.md` are satisfied.

## Migration Order

1. `001_initial_schema.sql`  
   Seed tables, core entities, source records, citations, assertions, classifications, image assets, and searchable documents.

2. `002_operational_skeleton.sql`  
   Governance and operational tables: source terms reviews, rights reviews, ingestion runs, ingestion events, source snapshots, workflow events, audit log, releases, and authority identifiers.

3. `004_coverage_skeleton.sql`  
   Regions, region-node coverage matrix, regional source priorities, historical events, and coverage gap tracking.

4. `005_global_classification_skeleton.sql`  
   Geography, date normalization, regional movement, event-node, and classification-axis tables.

5. `006_publication_surface_skeleton.sql`  
   Publication/display layer for the archive-cabinet design system: SEQ, display numbers, sheet pages, six fixed table rows, folder filter views, registration cards, sparse cards, and bookmarks.

6. `007_authority_normalization_skeleton.sql`  
   Authority, vocabulary, appellation, evidence-bundle, relation-rule, multilingual, and protocol-aware rights skeleton.

7. `008_source_rights_policy_skeleton.sql`  
   Source-level policy defaults, item-level rights override fields, versioned terms review extensions, image asset origin policy, ingest rights metrics, and experimental ingest candidate table.

8. `009_first_ingest_scope_skeleton.sql`
   First-ingest scope fields for regional movements, event nodes, sources, vocabulary, source records, rights reviews, and classifications.

9. `011_ingest_contract_targets_skeleton.sql`
   Field-level provenance, source record relations, digital representations, record-family profiles, validation rules, and the first-ingest target registry.

10. `003_read_models.sql`  
   Read-only views for frontend/API handoff. This runs after schema tables so geography and coverage views can resolve.

11. `010_seed_data.sql`  
   Generated seed inserts from `data/*.csv`.

12. `900_validation_queries.sql`  
   Validation checks for row counts, required fields, operational tables, and read models.

## Generate Seed SQL

```bash
python scripts/generate_postgres_seed_sql.py
```

This regenerates:

```text
db/010_seed_data.sql
```

## Dry Run Migrations

```bash
python scripts/run_db_migrations.py --dry-run --validate
```

This prints the migration plan without touching a database.

## Run Migrations

Requires `psql` and a configured PostgreSQL database URL.

```bash
DATABASE_URL="postgresql://user:password@localhost:5432/modern_gd_history" \
python scripts/run_db_migrations.py --validate
```

For schema-only setup:

```bash
DATABASE_URL="postgresql://user:password@localhost:5432/modern_gd_history" \
python scripts/run_db_migrations.py --schema-only
```

## Offline Skeleton Check

```bash
python scripts/check_db_skeleton.py
```

This checks:

- required migration files exist;
- seed CSV row counts match expectations;
- SQLite snapshot row counts match expectations;
- required SQL table/view tokens exist;
- generated seed SQL contains all expected seed inserts.

## Important Boundary

The database skeleton supports future ingestion, but it does not authorize ingestion. Before any automated source acquisition, each target source still needs:

- source terms review;
- rights review;
- field-level provenance policy;
- digital representation policy;
- source record parent/child relation policy;
- ingestion run configuration;
- snapshot/hash policy;
- error logging policy;
- explicit project log entry approving that ingestion run.
