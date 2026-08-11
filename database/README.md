# v49 PostgreSQL physical schema

This directory is the Phase 2A empty-database implementation for PostgreSQL
16. It contains no production rows and imports none of the v48 JSON, SQLite,
TRACE shards, Search assets, legacy graph edges, or third-party media.

## Migration order

The cluster roles are created once from `roles/001_cluster_roles.sql`. Each
fresh database is owned by `gda_v49_phase2a_schema_owner` and is replayed in
this exact order:

1. `migrations/001_foundation.sql`
2. `migrations/002_raw_core_provenance.sql`
3. `migrations/003_research_rights.sql`
4. `migrations/004_release_audit.sql`
5. `migrations/005_normative_closure.sql`
6. `migrations/006_epistemic_trace_closure.sql`
7. `migrations/007_release_copy_integrity.sql`
8. `migrations/008_final_integrity_closure.sql`
9. `functions/001_deferred_constraints.sql`
10. `functions/002_mutation_guards.sql`
11. `functions/003_release_and_cas.sql`
12. `functions/004_controlled_writes.sql`
13. `functions/005_projection_builders.sql`
14. `functions/006_normative_closure.sql`
15. `functions/007_release_protocol_closure.sql`
16. `functions/008_projection_builders_v2.sql`
17. `functions/009_projection_inventory_builders.sql`
18. `functions/010_visual_inventory_builders.sql`
19. `functions/011_rights_hash_closure.sql`
20. `functions/012_controlled_write_closure.sql`
21. `functions/013_review_case_closure.sql`
22. `functions/014_release_copy_guards.sql`
23. `functions/015_final_integrity_closure.sql`
24. `views/001_api_v1.sql`
25. `views/002_role_workspaces.sql`
26. `roles/002_database_grants.sql`

`scripts/replay.sh` enforces that order and refuses TCP-style hosts, port
5432, databases outside the `gda_v49_phase2a_` namespace, and databases that
already contain a v49 project schema. The historical `db/` SQL chain is not a
prefix of this schema.

## Local isolated replay

The caller must create a disposable cluster and database first, then provide
an explicit Unix socket, non-default port, and database name:

```sh
PGHOST=/absolute/disposable/socket \
PGPORT=58649 \
PGDATABASE=gda_v49_phase2a_replay1 \
GDA_PSQL=/absolute/path/to/psql \
database/scripts/replay.sh
```

Run the transaction-scoped fixture and adversarial suite with the same
connection boundary:

```sh
PGHOST=/absolute/disposable/socket \
PGPORT=58649 \
PGDATABASE=gda_v49_phase2a_replay1 \
GDA_PSQL=/absolute/path/to/psql \
database/scripts/run_tests.sh
```

The runner verifies that all test rows roll back. `schema_hash.sh` creates a
temporary schema-only dump, removes dump-session noise, and emits the
normalized SHA-256 used for deterministic replay comparison.

The SQL files intentionally use `CREATE`, not idempotent `IF NOT EXISTS`
shortcuts: replay is defined only against a fresh database. A duplicate or
partially populated target therefore fails instead of silently accepting an
unknown schema state.

## Historical audit verification

`scripts/verify_historical_audit.py` separates the immutable audit baseline
from the current implementation identity. It reads the manifest and checksum
ledger from the explicitly named historical commit, proves that commit is an
ancestor of the separately named current implementation commit, and refuses a
current identity that is not exactly `HEAD`:

```sh
python3 database/scripts/verify_historical_audit.py \
  --expected-base-commit 967cbe3 \
  --audit-manifest docs/audits/v49-authority-research-delta/MANIFEST.json \
  --checksums docs/audits/v49-authority-research-delta/CHECKSUMS.sha256 \
  --expected-normative-version 1.0.0 \
  --current-implementation-commit "$(git rev-parse HEAD)"
```

This does not rewrite or re-sign the Phase 1C/1D package. A changed historical
blob still fails, while a later implementation commit no longer creates a
false failure merely because `HEAD` advanced.

## Role boundary

| Role | Runtime responsibility | Direct base-table writes |
|---|---|---|
| `schema_owner` | Owns schema objects; `NOLOGIN` | Owner only |
| `migrator` | Applies this reviewed file sequence | Via owner membership |
| `ingest_writer` | Governed-source and health observation functions | None |
| `reviewer` | Review, rights, policy, delivery, takedown and verification functions | None |
| `publisher` | Draft copy, validate, seal and CAS functions | None |
| `api_reader` | Three positive-allowlist `api_v1` views | None |
| `auditor` | Audit inventory and public release descriptors | None |

`PUBLIC` has no database, schema, table, sequence, function, or project-type
privilege. Every `SECURITY DEFINER` function fixes `search_path` to
`pg_catalog`, schema-qualifies project objects, and contains no dynamic SQL.

## Authority and release boundaries

- The later JSON migration owns the deterministic UUID recipe. DDL never
  assumes 15,923 is a capacity ceiling.
- `raw.source_asset` stores bytes and SHA-256; runtime ingest can register only
  `governed_source`. Frozen authority kinds are reserved for the migrator.
- Unknown relation text is retained in raw/workflow rows. There is no sentinel
  relation type and no automatic influence or transitivity.
- Canonical research relations and TRACE release projections are separate.
- Research and visual releases each follow
  `draft → candidate → validated → sealed`, have independent manifests,
  detached verification, current pointers, and row-locked CAS.
- Sealed child rows and manifests are immutable. Health and takedown changes
  use append-only visual sidecars and may only reduce effective exposure.
- `api_v1` reads only verified, publicly promoted research snapshots. Raw,
  held, internal locator, and non-public channel state remain inaccessible.

See `PHYSICAL_SCHEMA.md` for the domain diagram and constraint strategy, and
`JSON_MIGRATION_CONTRACT.md` for the next phase's input contract.

## Recovery boundary

Before population, recovery means discarding only the explicitly named fresh
database and replaying these files. No down migration mutates a sealed release.
After publication, corrections create new canonical revisions and new sealed
release versions; current pointers move only through successful CAS.
