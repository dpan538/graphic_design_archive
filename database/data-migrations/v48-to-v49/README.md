# v48 Candidate JSON → v49 population rehearsal

This directory is a **population migration**, separate from the immutable
Phase 2A physical-schema chain. It does not modify `database/migrations/`,
roles, functions, views, or any Phase 1/2A receipt.

`generated/public_surfaces_prefreeze_candidate_v48.json` is the one and only
source that can create population rows. SQLite, transfer manifests, TRACE
assets, Search and audit packages are verified only as reconciliation or
integrity evidence.

## Deterministic flow

1. `extract.py` strictly parses the frozen JSON once and creates a temporary
   staging bundle. It rejects duplicate keys, non-UTF-8, non-finite constants,
   non-array `/surfaces`, ID collisions, unknown tiers, unaccounted pointers,
   unsafe TRACE pairing, and visual-count drift before PostgreSQL is contacted.
2. `load.sql` is executed only inside the importer transaction. It derives
   fixed UUIDv5 identities from the frozen hash and exact occurrence keys; no
   runtime timestamp, sequence, random UUID, delimiter split, array zip or
   deduplication contributes to content.
3. `import.py` imports one bundle into a fresh replayed Phase 2A database or
   returns a verified deterministic no-op for an identical completed batch.
   The persisted batch binding contains the Candidate, mapping, schema,
   extractor and implementation-base hashes; a reused batch ID with any one
   of those bindings changed fails before a write.
4. `verify.py` compares table vectors, stable-key hashes and a distinct
   normalized semantic-content hash. It also executes the `api_reader` role
   for its allowed view and denied raw-locator/source/write probes, and checks
   the tier partition and ledger-to-row cardinalities.

The full field-occurrence ledger is intentionally temporary because it is a
large, mechanically regenerated expansion. It has a schema, row count,
byte count and SHA-256 in the staging manifest and is deleted only after the
final Phase 2B receipts record that evidence. Every present scalar/null
occurrence also has a durable `raw.field_literal` row with an exact relative
JSON Pointer, source-record UUID, source-order ordinal and canonical raw
literal bytes; container bytes remain exactly recoverable from the parent
`raw.source_record.raw_value`.

## Intentional conservative boundaries

- The 47,982 Candidate folder pairs are independently recomputed from both
  Candidate representations before loading. They become deterministic,
  **proposed** typed `folder_membership` assignments with their structured
  folder ID, object crosswalk and source-order ordinal. No acceptance decision,
  provenance evidence, free-text inference or public/research release is
  invented by this rehearsal.
- The three exact legacy identity namespaces are retained, and each archive
  object receives one real `research.object_trace_node` `root` bridge.  A
  `core.legacy_identity_resolution` is deliberately not created because its
  physical model is release-pinned and evidence-governed; Phase 2B does not
  create a research release just to satisfy that later workflow.
- Tier absence is distinct from JSON null and empty string.  The occurrence
  ledger retains every presence class; a present non-string/empty tier fails
  preflight rather than being silently treated as missing.

## Rehearsal boundary

Use only a disposable PostgreSQL cluster with a private Unix socket and a
non-default port. The load never creates a release, visual registry, current
pointer, public pixel locator, accepted semantic relation, TRACE projection
edge, or production database. Every failure injection runs against a fresh
database and must roll back its migration batch and canonical rows.

## Reproduction

After a controller has created a disposable database owned by
`gda_v49_phase2a_schema_owner` inside an isolated socket-only cluster, a
single replay is reproducible with:

```sh
PGHOST=/private/tmp/gda_v49_phase2b/socket \
PGPORT=58652 \
PGDATABASE=gda_v49_phase2a_phase2b_replay1 \
GDA_ADMIN_USER=gda_v49_phase2b_admin \
GDA_PHASE2B_STAGE=/private/tmp/gda_v49_phase2b_stage/staging \
GDA_PHASE2B_REPORT=/private/tmp/gda_v49_phase2b_report1.json \
sh database/data-migrations/v48-to-v49/run-rehearsal.sh
```

The runner only replays the existing Phase 2A schema and invokes the Phase 2B
population code. It does not create or remove clusters/databases, access the
network, or perform release sealing. The controller runs it once per fresh
database, then runs fault injection and idempotency probes against explicitly
named disposable databases.
