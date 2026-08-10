# 04 — Database and DDL Readiness

- Audit package: **A4**
- Audit date: 2026-08-11 (Australia/Brisbane)
- Baseline commit: `f076ca3444aaa0f413bb61fe2cb568d6a9aa2720`
- Frozen source ancestor: `0404c7f96f9189f576c4c5b1368061e4082e436b`
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Independent scope: DDL readiness, identity/cardinality, assertions/assignments/evidence/decisions, roles/privileges, release seal/CAS, migration and freeze gates
- Unique output: `docs/audits/v49-pre-migration/04_DATABASE_AND_DDL_READINESS.md`
- Audit coverage: **COMPLETE**
- Readiness result: **PARTIAL**

`PARTIAL` means the requested repository and normative surface was completely inspected, but physical v49 DDL must not begin yet. The Phase 1A documents establish a strong typed-identity and immutable-release baseline; ten P0 decisions or gate corrections below remain open. No PostgreSQL implementation exists for v49, and the executable-looking `db/*.sql` tree is a May 2026 legacy skeleton that is incompatible with the accepted v49 model.

## 1. Scope and boundaries

This package audited:

- all nine v49 normative architecture documents;
- all 14 tracked SQL files, their migration runner, database README, and legacy schema planning documents;
- identity and cardinality facts carried by the Phase 1A decision pack;
- assertion, canonical-assignment, evidence, review-case, and curator-decision cardinalities;
- the seven-role privilege model and `SECURITY DEFINER` boundary;
- release states, candidate closure, pre-seal receipts, manifest hashing, post-seal sidecar, and `current` CAS;
- canonical parity, graph parity, derived reconciliation, and historical aspiration units;
- repository-hygiene, research/data-quality, machine-readable, migration, freeze, and promotion gates;
- cross-evidence from [A1 Git/worktree/history](01_GIT_WORKTREE_AND_HISTORY.md) and [A3 data authority/lineage](03_DATA_ASSET_AUTHORITY_AND_LINEAGE.md).

The audit did not create or test physical DDL, connect to PostgreSQL, run the legacy migration runner, migrate/import/export data, generate a release, modify v48 artifacts, or edit a normative document.

## 2. Evidence commands

All commands were read-only. SQL files were read as text; no SQL was executed. Secret values were neither requested nor printed.

```sh
repo=/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform

git -C "$repo" status --short
git -C "$repo" rev-parse HEAD

wc -l \
  ARCHITECTURE.md DATA_MODEL_V49.md READ_API_V1.md \
  MIGRATION_V48_TO_V49.md ACCEPTANCE_GATES.md \
  docs/adr/0001-canonical-postgres-and-read-only-release.md \
  docs/adr/0002-immutable-data-versioning.md \
  docs/adr/0003-runtime-repository-and-fixture-mode.md \
  docs/architecture/DDL_DECISION_PACK_V49.md

sed -n '1,420p' ARCHITECTURE.md
sed -n '1,110p' DATA_MODEL_V49.md
sed -n '111,220p' DATA_MODEL_V49.md
sed -n '221,330p' DATA_MODEL_V49.md
sed -n '1,260p' READ_API_V1.md
sed -n '1,260p' MIGRATION_V48_TO_V49.md
sed -n '1,260p' ACCEPTANCE_GATES.md
sed -n '1,240p' docs/adr/0001-canonical-postgres-and-read-only-release.md
sed -n '1,240p' docs/adr/0002-immutable-data-versioning.md
sed -n '1,240p' docs/adr/0003-runtime-repository-and-fixture-mode.md
sed -n '1,130p' docs/architecture/DDL_DECISION_PACK_V49.md
sed -n '131,260p' docs/architecture/DDL_DECISION_PACK_V49.md
sed -n '261,430p' docs/architecture/DDL_DECISION_PACK_V49.md

rg -n \
  '20,000|4,077|20k|aspiration|canonical parity|graph parity|derived reconciliation|historical aspiration|repository hygiene|data-quality|machine-readable|epistemic|corpus|missingness|visual registry|research release|operational' \
  ARCHITECTURE.md DATA_MODEL_V49.md READ_API_V1.md \
  MIGRATION_V48_TO_V49.md ACCEPTANCE_GATES.md \
  docs/adr/*.md docs/architecture/DDL_DECISION_PACK_V49.md

wc -l db/*.sql scripts/run_db_migrations.py
git -C "$repo" ls-files --stage db scripts/run_db_migrations.py
file db/*.sql scripts/run_db_migrations.py

rg -n -i \
  'target_type|target_id|create schema|create role|grant |revoke |security definer|row level security|create policy|current_pointer|manifest_sha|sealed|candidate|validated|draft' \
  db --glob '*.sql' --glob '!010_seed_data.sql'

awk 'BEGIN{IGNORECASE=1}
  /^[[:space:]]*create table/{
    t=$0; sub(/.*exists[[:space:]]+/,"",t); sub(/[[:space:]]*\(.*/,"",t)
  }
  /target_type[[:space:]]+text|review_target_type[[:space:]]+text|target_table[[:space:]]+text/{
    print FILENAME ":" FNR "\t" t "\t" $0
  }' db/*.sql

rg -c -i '^\s*create table' db --glob '*.sql' --glob '!010_seed_data.sql'
rg -c -i '^\s*create (or replace )?view' db --glob '*.sql' --glob '!010_seed_data.sql'
rg -n -i \
  '^\s*(create schema|create role|grant\b|revoke\b|alter default privileges|create policy|alter table .*enable row level security|create .*function|security definer)' \
  db --glob '*.sql' --glob '!010_seed_data.sql'

sed -n '130,240p' db/001_initial_schema.sql
sed -n '1,125p' db/002_operational_skeleton.sql
sed -n '250,345p' db/002_operational_skeleton.sql
sed -n '55,180p' db/006_publication_surface_skeleton.sql
sed -n '95,135p' db/007_authority_normalization_skeleton.sql
sed -n '125,175p' db/011_ingest_contract_targets_skeleton.sql
sed -n '1,220p' db/README.md
sed -n '1,220p' scripts/run_db_migrations.py
sed -n '1,260p' docs/system/DB_SKELETON_PLAN.md
sed -n '1,260p' docs/system/SCHEMA_DRAFT.md
sed -n '261,430p' docs/system/SCHEMA_DRAFT.md

git -C "$repo" log -1 --format='%H%x09%ad%x09%s' --date=iso-strict -- \
  db/001_initial_schema.sql db/013_capture_batch_skeleton.sql \
  scripts/run_db_migrations.py

rg -n \
  'run_db_migrations|db/001_initial_schema|DB_SKELETON_PLAN|schema-only|DATABASE_URL' \
  --glob '!docs/audits/**' --glob '!db/010_seed_data.sql' .

sed -n '1,520p' docs/audits/v49-pre-migration/01_GIT_WORKTREE_AND_HISTORY.md
sed -n '1,560p' docs/audits/v49-pre-migration/03_DATA_ASSET_AUTHORITY_AND_LINEAGE.md
```

## 3. Measured repository results

### 3.1 Normative corpus

The nine-document v49 corpus contains 1,755 lines at the audit baseline:

| Document | Lines |
|---|---:|
| `ARCHITECTURE.md` | 197 |
| `DATA_MODEL_V49.md` | 290 |
| `READ_API_V1.md` | 200 |
| `MIGRATION_V48_TO_V49.md` | 159 |
| `ACCEPTANCE_GATES.md` | 171 |
| ADR 0001 | 88 |
| ADR 0002 | 131 |
| ADR 0003 | 151 |
| `DDL_DECISION_PACK_V49.md` | 368 |

The corpus consistently establishes the eight schemas, JSON-only migration authority, raw-byte lexical authority, typed FKs, fail-closed unknown relations, five orthogonal state axes, release state machine, repository/API separation, and prototype command restrictions. It is not yet cross-consistent on the research relation model, dual research/visual version identity, archive-object semantics, or migration count taxonomy.

### 3.2 Existing database files are legacy, not v49 DDL

Measured legacy implementation surface:

| Measurement | Result |
|---|---:|
| Tracked SQL files under `db/` | 14 |
| SQL lines | 23,224 |
| Legacy tables declared outside generated seed SQL | 82 |
| Legacy read views | 55 |
| Generated seed SQL lines | 19,547 |
| Migration runners | 1 (`scripts/run_db_migrations.py`) |
| v49 schema declarations (`raw/core/provenance/rights/research/workflow/release/api_v1`) | 0 |
| Role/default-privilege/RLS/definer implementation statements | 0 |
| Legacy tables using free `target_type + target_id` or `target_table + target_id` | 10 |

The SQL and runner were introduced by commit `4f1a10f35916df91d0c979819a25d2670161d2eb` on 2026-05-31 under the message `initial archive framework`. They predate the v49 decisions.

The ten free-polymorphic target tables are:

1. `editorial_reviews`;
2. `workflow_events`;
3. `search_index_queue`;
4. `audit_log`;
5. `normalized_dates`;
6. `publication_surfaces`;
7. `sparse_cards`;
8. `archive_bookmarks`;
9. `authority_resolution_events`;
10. `field_provenance`.

Additional incompatibilities are structural:

- all legacy objects live in the default/public schema rather than the eight v49 layers;
- `entities.entity_id` is text and `entity_type` includes `source_record` and `image_asset`, contrary to the closed v49 `core.entity` boundary;
- subtype exclusivity is not represented;
- `assertions` requires entity-to-entity subject/object columns and cannot express the accepted typed subject/value families;
- evidence, assignment support, and curator decisions are not represented by the required N:M bridges;
- `workflow_status`, `review_status`, `assertion_status`, and `rights_state` conflate axes that v49 keeps orthogonal;
- `project_releases`/`release_files` have no candidate fingerprint, validated state, immutable manifest bytes, post-seal sidecar, copied projections, or pointer CAS;
- `release_files.checksum_sha256` is optional;
- generated seed SQL uses mutable `ON CONFLICT ... DO UPDATE` and time-dependent updates, which cannot be a v49 immutable migration input;
- the runner executes the legacy schema and generated seed by default, one `psql` invocation per file, and has no v49 migration-set hash, transaction/replay receipt, role bootstrap, or schema-namespace guard.

`db/README.md`, `docs/system/DB_SKELETON_PLAN.md`, `PROJECT_LOG.md`, and other historical reports still advertise the runner. Therefore filename proximity and “PostgreSQL” wording create a real operator hazard. These paths must remain preserved as legacy evidence but be explicitly denied as v49 executable input.

## 4. Artifact authority and migration-source readiness

### 4.1 Authority decision: PASS

The v49 documents and A3 agree on this hierarchy:

| Asset class | v49 authority |
|---|---|
| Frozen candidate JSON | Sole migration input; raw bytes/hash are lexical authority |
| Frozen SQLite | Reconciliation only; `mode=ro&immutable=1`; never fills a canonical row or field |
| Transfer JSON/CSV and TRACE manifest | Integrity evidence |
| Search, atlas, catalogs, neighborhoods/shards | Derived products; never a second canonical database |
| JSONB | Parsed projection; never proves byte equality |

Search-only 6,051 IDs remain derived exclusions. Search must be generated from a sealed v49 cohort.

### 4.2 Clean-input graph regeneration: FAIL

A3 measured that the canonical JSON cannot by itself regenerate the 97,889 TRACE nodes, 255,695 edges, 126,822 memberships, review catalog, or all graph evidence. The checked-in TRACE generator reads four inputs:

1. v48 SQLite;
2. canonical JSON;
3. a v47 adjunct;
4. the legacy 8,636-item frontend payload.

The SQLite and frontend payload are non-authoritative for migration. In addition, the current checkout omits the v47 JSON and SQLite parents required by v48 builders; only historical LFS pointers provide recovery references. Frozen outputs can be verified, but the current tree is not a self-contained authoritative replay source.

The existing Phase 1A rule already fails closed: graph material beyond JSON may enter v49 only if a deterministic transformation regenerates it from JSON plus governed configuration. The missing implementation decision is a complete graph delta ledger. Until every node, claim, evidence locator, review row, and adjunct fact is classified `REGENERABLE`, `GOVERNED_EXTERNAL_EVIDENCE`, or `HOLD`, graph parity is evidence—not authorization to import TRACE/SQLite rows.

## 5. Count and unit taxonomy

The migration/freeze contract must use four independent classes.

### 5.1 Canonical parity

Canonical parity is measured from the sole migration input and its deterministic typed projection:

- 15,923 JSON surface rows and 15,923 unique `surfaceId` values;
- 15,923 nonblank unique `sourceRecordId` values;
- one deterministic seed object and primary surface crosswalk per JSON row, with no automatic identity merge;
- 47,982 unique folder/member pairs when regenerated from the JSON folder and surface arrays;
- exact raw artifact byte length and SHA-256;
- any normalized value only when linked to a raw pointer, transformation, and accepted assertion/decision.

The row-level `source_verified=12,952` and `metadata_supported=2,971` split may be used as canonical-derived parity only when recomputed from row-level records. The frozen JSON top-level metadata says 2,970, a known one-row conflict. Frozen bytes must not be edited; the verifier must preserve and report that exact known delta while treating row-level classification as authoritative.

### 5.2 Graph parity

Graph units remain independently named:

- 97,889 TRACE nodes;
- 255,695 total directed graph edges;
- 126,822 active-object relation memberships;
- membership-family rows: 79,206 medium/context, 31,288 source/provenance, 16,328 time/place, and zero historical influence;
- 30 active research trees.

These counts are corpus and portfolio evidence. They become a migration acceptance target only for the subset whose authoritative regeneration/curation path is closed. An unexplained gap is `HOLD`; it is not repaired from SQLite or a shard.

### 5.3 Derived reconciliation

Derived reconciliation includes:

- Search 8,636;
- canonical/TRACE and Search intersection 2,585;
- Search-only 6,051;
- canonical/TRACE-only 13,338;
- union 21,974;
- review layer 4,425 and auxiliary layer 11;
- TRACE manifest/file/shard counts and hashes;
- saved 200/200 audit samples and 55 PASS/0 HOLD receipts.

Derived counts prove v48 behavior and set boundaries. They do not add canonical rows and do not prescribe the future v49 Search count.

### 5.4 Historical aspiration

`20,000` and `remaining 4,077` are historical portfolio-planning metadata only. They are not canonical parity, graph parity, migration completion, freeze, promotion, or release-quality gates.

At the baseline they still appear normatively in:

- `DATA_MODEL_V49.md` under “v48 reconciliation baseline”;
- `MIGRATION_V48_TO_V49.md` M6 exact baseline;
- `ACCEPTANCE_GATES.md` G2 PASS requirements.

They must be removed from normative parity while remaining preserved as historical metadata in frozen v48 artifacts/receipts.

## 6. Identity and cardinality readiness

### 6.1 Closed decisions: PASS

The Phase 1A ledger is sufficiently precise for these physical keys:

| Area | Locked decision |
|---|---|
| `archive_object_id` | UUID PK/FK subtype of `core.entity`; deterministic UUIDv5 for v48 seed, persisted UUIDv7 for future objects |
| `surface_id` | Public/legacy route identifier and typed crosswalk, not object PK |
| raw source record | One immutable occurrence keyed by artifact and ordinal; provider keys are non-unique attributes |
| object↔source | N:M, natural key `(archive_object_id, source_record_id, source_role)`; v48 seed measured 1:1 |
| TRACE node | Independent identity; `canonical_key` is not a key |
| object↔TRACE node | N:M typed join with role; v48 root baseline 1:1 |
| folder↔object | N:M, natural key `(folder_id, archive_object_id, membership_role)`; v48 47,982 rows |
| semantic edge projection | Directed triple currently specified as `(subject_trace_node_id, relation_type_id, object_trace_node_id)` |
| object↔edge | N:M assignment keyed by `(archive_object_id, relation_edge_id, membership_role)` |
| legacy IDs | Typed namespace crosswalk with append-only alias/redirect/merge/split/withdraw/unresolved history |

The source-object-key collisions and TRACE canonical-key collisions are explicitly preserved; no provider key or label is promoted to a PK.

### 6.2 Operational archive-object semantics: PARTIAL

The documents correctly say that one UUIDv5 is created per v48 row and that this does not assert global real-world uniqueness. However, `DATA_MODEL_V49.md` still describes `core.archive_object` as a “stable intellectual-object subtype identity,” while the measured source only proves an operational catalogued design-object record.

Before DDL, the normative definition must say that the Phase 1 seed object is an **operational catalogued design object**: the stable subject around which the archive binds descriptions, surfaces, sources, representations, and research claims. It is not, without an evidence-bearing curator decision, a claim that the row is the unique intellectual work or that two rows denote different works. Work-level clustering/identity must be a separate typed relation or later subtype, never implicit deduplication.

This is a P0 semantic choice because it controls uniqueness, merge/split, source cardinality, and scholarly claim targets.

## 7. Assertions, assignments, evidence, decisions, and TRACE

### 7.1 What is already sound

- assertions have exactly one registered predicate, one closed typed subject subtype, and one closed typed value subtype;
- evidence is shareable and source/locator/span/hash-bound rather than edge identity;
- assertion↔evidence, assignment↔assertion, and decision↔evidence are N:M;
- an accepted assignment requires accepted support or an effective evidence-bearing curator decision;
- review cases use typed subject bridges and have append-only decisions, with at most one effective non-superseded decision;
- unknown predicates remain proposed/queued and create no canonical edge, publication row, or metric row;
- publication, workflow, acceptance, rights, and count eligibility are independent axes.

### 7.2 P0 contract gaps

1. **No assertion-predicate registry table is named.** The model says “registered predicate,” but only `research.relation_type` is explicit. Descriptive assertions need an FK-backed predicate registry with domain/range, epistemic/evidence requirements, status, and version.
2. **The closed canonical-assignment subtype set is not enumerated.** `provenance.canonical_assignment` requires exactly one subtype, but core joins and research joins do not consistently state their PK/FK membership in that closed set. A deferred exclusivity mechanism cannot be designed until every initial subtype is listed.
3. **Direct edge evidence is contradictory.** Section 7 of the decision pack says assignments reach evidence only through assertions or effective decisions; Section 8 says multiple evidence rows attach through an edge/evidence bridge. DDL must choose one explicit model and preserve stance/ordinal without two competing support paths.
4. **Relation, claim, and TRACE projection are conflated.** The current `research.relation_edge` is called both a canonical assignment/semantic edge and a TRACE triple. A relation proposition, an individual source- or scholar-bounded claim, and a release-specific TRACE projection have different identities and cardinalities.
5. **Epistemic classes are absent.** `documented_fact`, `scholarly_claim`, `computed_association`, and `causal_interpretation` need structured classes. Historical influence must retain claimant, wording, source, locator, and evidence; computed associations must retain analysis run, method/version, parameters, input research-release hash, and score. Competing claims must not collapse merely because their directed triple matches.

The safe target is: immutable evidence supports source-bounded claims; accepted claims may support a normalized semantic relation; a sealed research release projects eligible relations/claims into TRACE nodes/edges. The TRACE triple can remain a projection natural key inside one release, but it must not be the natural identity of every underlying claim.

## 8. Roles and privilege readiness

### 8.1 High-level matrix: PASS

The seven required roles and hard boundaries are present:

- `v49_owner` is `NOLOGIN` and owns all objects;
- ephemeral `migrator` alone may `SET ROLE v49_owner` in a reviewed migration window;
- `ingestor` appends raw/proposed data through allowlisted operations;
- `reviewer` claims cases and appends decisions/evidence;
- `releaser` alone transitions release state, seals, and changes `current` by CAS;
- `reader` selects only sealed `api_v1`/public release projections;
- `auditor` uses read-only audit views and cannot mutate, claim, decide, seal, CAS, `SET ROLE`, or bypass RLS;
- `PUBLIC` receives no create/table/sequence/function privilege;
- definer functions are allowlisted, schema-qualified, fixed-search-path, non-dynamic, audited, lock/CAS checked, and unable to disable constraints or sealed protection.

### 8.2 Executable privilege specification: PARTIAL

Before role DDL, the matrix still needs an exact bootstrap/grant appendix that fixes:

- whether each application role is a group `NOLOGIN` role or direct ephemeral `LOGIN`, and which login may `SET ROLE` it;
- explicit `NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS NOINHERIT` attributes;
- database `CONNECT`/`TEMP`, per-schema `USAGE`/`CREATE`, table, sequence, type, and function privileges;
- `ALTER DEFAULT PRIVILEGES` for every owner/schema so later tables/functions do not widen access;
- extension ownership and the schema in which extensions may install;
- which unsealed release rows `releaser` can see and how copied projections are inserted without direct unrestricted DML;
- exact audit views for restricted raw content, including redaction policy and access logging;
- revocation tests for every denied action, not only positive grant tests;
- migration-session expiry, credential handling, and break-glass receipt requirements.

The legacy SQL implements none of these grants. The high-level decision is sound, but role DDL without this negative matrix would be unsafe.

## 9. Release seal and CAS readiness

### 9.1 Single-release protocol: PASS

The current protocol is internally strong:

```text
draft → candidate → validated → sealed
```

- candidate closure fixes snapshot, cohort, migrations/query packs, registries, copied projections, and asset inventory;
- immutable pre-seal receipts are bound to one candidate fingerprint and cover all five frozen assets, counts/sets, FKs/orphans, relation/rights registries, unknown relations, grants, projections, and assets;
- RFC 8785 canonical manifest bytes and SHA-256 are stored atomically with `validated → sealed` in a serializable transaction;
- sealed rows/assets are immutable by ownership, revocation, and defense-in-depth trigger;
- post-seal sidecar failure leaves a sealed release non-pointer-eligible;
- `current` is mutable routing metadata with append-only history and changes only through CAS to an exact sealed `(releaseId, manifestSha256)` pair;
- candidate/sealed projections are copied rows and never drift by joining mutable canonical tables.

### 9.2 Research release versus visual registry: FAIL

ADR 0002 currently puts Archive, Search, TRACE, rights-safe representations, and registries under one release identity. The task requires two independently versioned, integrity-bound axes:

- `researchReleaseId + researchManifestSha256` for research/corpus/claim/TRACE data;
- `visualRegistryVersion + registrySha256` for external visual references, provider endpoints, rights observations/policy decisions, delivery mode, health, attribution, review due, and takedown overrides.

The visual registry needs its own immutable state transition and `current` CAS. A visual-registry update must not rewrite a sealed research manifest; a research release must pin the exact registry version/hash used for a delivered composite response. Rights assessment, delivery mode, and endpoint health remain independent. Unknown/missing/conflict/stale rights fail closed to `LINK_ONLY` or `CITATION_ONLY`.

This dual-version relation must be resolved before `release` and `rights` DDL because it changes keys, manifest lineage, current pointers, cache identities, API envelopes, takedown behavior, and seal receipts.

### 9.3 Deterministic manifest detail: P1

The manifest example includes `createdAt`, while the prose prohibits timestamps that make otherwise equal exports differ. The contract should require a candidate-closed timestamp or other fixed source value; wall-clock export time belongs in an external receipt/sidecar. This does not change the state machine but is required before exporter implementation.

## 10. Migration, freeze, and delivery gates

### 10.1 Existing gate strengths

- all five frozen assets are byte/hash gates;
- SQLite is immutable read-only reconciliation;
- G4/G5 allow fully accounted proposed/queued rows without treating queue non-emptiness as failure;
- unknown relations fail closed;
- G7 includes the complete seal protocol;
- G9 applies only to explicitly scoped architecture/recovery/prototype checkpoints;
- data CI and frontend CI are separated by immutable contracts;
- no architecture-only result authorizes promotion.

### 10.2 Required corrections

| Required gate correction | Current evidence | Required acceptance boundary |
|---|---|---|
| Remove 20,000/4,077 from parity | Present in model, M6, and G2 | Preserve only as historical aspiration; never blocks migration/freeze/promotion |
| Add repository-hygiene gate | A1 found 78 reachable ≥100 MiB blobs, incomplete full fsck/secret history review, prunable worktrees, and license boundary gaps | Remote race, LFS availability, full object integrity, redacted history-secret scan, changed-file allowlist, no unclassified release blob |
| Add research/data-quality freeze gate | A3 found non-self-contained lineage, graph-authority gap, 2,970/2,971 conflict, and unreviewed raw captures | Complete source/claim/corpus/missingness/delta ledger; exact known-delta receipt; zero unclassified graph/raw facts |
| Add machine-readable contract gate | Current G6 covers API shape but not full publication contract | Stable URIs, JSON Schema, JSON-LD/PROV/Linked Art mapping, DCAT manifest, release diff/change feed, sitemap/crawlability, rights-safe response tests |
| Add dual-version integrity gate | One release currently owns visuals | Bind exact research release and visual registry pair; independent CAS/seal/takedown rules; no rights-held pixel URL leakage |
| Add legacy-DDL deny gate | Runner remains advertised and executable | New v49 migration namespace; runner refuses legacy/default set; old SQL never participates in v49 migration-set hash |
| Correct G0 commit budget | G0 says at most one architecture commit; Phase 1B permits two scoped commits | Gate uses the task-authorized commit budget and exact changed-file allowlist |
| Split pre-DDL readiness axes | Current promotion rule is broad | Report engineering, research-semantic, rights/visual, overall pre-DDL readiness separately |

## 11. Findings and priorities

### P0 — must close before physical v49 DDL starts

| ID | Finding / affected paths | Risk | Required action and acceptance |
|---|---|---|---|
| A4-P0-01 | `20,000 / 4,077` remains normative in `DATA_MODEL_V49.md`, `MIGRATION_V48_TO_V49.md`, `ACCEPTANCE_GATES.md` | An aspiration becomes a false parity/promotion requirement | Move to historical aspiration only; four-way count taxonomy is explicit everywhere |
| A4-P0-02 | `core.archive_object` is still described as an intellectual-object identity | Seed rows may be overclaimed as unique works; merges/dedup become ontological guesses | Define operational catalogued design object; model evidence-bearing work identity separately |
| A4-P0-03 | Semantic relation, source/scholarly claim, and TRACE projection are conflated | Competing claims and projection choices collapse into one triple | Separate identities/cardinalities and add epistemic relation classes before table design |
| A4-P0-04 | Graph facts cannot be regenerated from canonical JSON alone | SQLite/TRACE-derived facts could be laundered into canonical research tables | Complete authoritative graph delta ledger; zero unclassified facts; HOLD anything non-authoritative |
| A4-P0-05 | Assertion predicate registry, closed assignment subtype list, and direct edge-evidence path are incomplete/contradictory | FKs and deferred subtype/support constraints cannot be implemented unambiguously | Name predicate registry; enumerate every subtype; choose one auditable evidence path |
| A4-P0-06 | Research release and visual registry have no independent identities/seals/CAS | Rights/health changes would rewrite or silently drift research identity | Specify dual manifests, cross-pin, independent pointers, rights-safe composite behavior |
| A4-P0-07 | Legacy `db/*.sql` and runner look executable as v49 but violate core invariants | Accidental execution creates 82 incompatible tables and mutable seed data | Establish a new v49 migration namespace and hard legacy execution deny; archive only after dependency review |
| A4-P0-08 | Role matrix lacks exact role attributes, default privileges, schema grants, negative tests, and login mapping | A nominal least-privilege design can leak by defaults or ownership | Approve executable role/grant/deny matrix before role DDL |
| A4-P0-09 | Repository, research/data-quality, machine-readable, dual-version, and split pre-DDL gates are absent | DDL/freeze may appear ready without research, rights, security, or publication evidence | Add named gates with exact PASS/PARTIAL/FAIL evidence and independent readiness booleans |
| A4-P0-10 | Frozen summary says 2,970 metadata-supported while row-level truth is 2,971 | Importer may drop or misclassify one object or reject a known historical inconsistency | Declare row-level parity authoritative; preserve frozen counter; record exact known delta; reject new deltas |

### P1 — close before migration/release implementation

| ID | Finding | Risk | Recommended action |
|---|---|---|---|
| A4-P1-01 | Evidence natural key assumes record-scoped evidence | Artifact-level evidence could be forced into a fake record or collide on nullable fields | Add explicit evidence scope kind with checked typed FK/null rules |
| A4-P1-02 | Multi-value/JSONB inventory is representative rather than a complete field-by-field mapping contract | Order, duplicate, null, literal, or orphan behavior can remain implicit | Produce a path-level mapping ledger and round-trip query for every canonical JSON field |
| A4-P1-03 | Manifest `createdAt` determinism is not exact | Repeat exports can differ only by clock time | Freeze timestamp at candidate closure; keep operational time in receipts/sidecar |
| A4-P1-04 | Migration execution protocol is not yet specified | Partial multi-file application, drift, or wrong migration set | Define transaction boundaries, advisory lock, migration hashes, replay/idempotency, recovery, and receipt format |
| A4-P1-05 | G0 still encodes a one-commit architecture limit | A compliant two-commit Phase 1B could fail its own gate | Make commit budget phase-defined and bind changed-file allowlist |
| A4-P1-06 | Legacy SQL contains research seed content as well as obsolete schema | Blanket deletion could lose unique historical research evidence | Inventory consumers/source ownership; preserve data lineage before archival/deletion classification |

### P2 — physical design after P0 closure

| ID | Finding | Risk | Recommended action |
|---|---|---|---|
| A4-P2-01 | Index, partition, materialization, and query-plan choices are intentionally open | Premature choices may not fit production queries | Decide with representative data and `EXPLAIN` in the authorized implementation phase |
| A4-P2-02 | UUIDv7 mechanism/extension is not selected | Portability and extension ownership differ | Select a persisted generator compatible with the privilege/extension policy |
| A4-P2-03 | Auditor redacted-view details are deferred | Oversharing or insufficient audit visibility | Design view-by-view column policy and access receipts before operational cutover |

Priority totals for A4: **P0 10 / P1 6 / P2 3**.

## 12. Gate assessment

| Area | Result | Reason |
|---|---|---|
| Artifact authority | PASS | JSON/SQLite/manifests/Search/TRACE roles are explicit and consistent |
| Raw bytes versus JSONB | PASS | lexical and semantic equality are separate |
| Measured identity/cardinality ledger | PASS | IDs, collisions, N:M joins, natural keys, and population sets are explicit |
| Operational archive-object semantics | PARTIAL | non-dedup rule exists; operational versus intellectual-work meaning is not normative enough |
| Typed FK/no free polymorphism design | PASS | v49 rule is sound; legacy SQL is explicitly incompatible |
| Assertion/evidence/decision DDL contract | PARTIAL | registry/subtype/support-path decisions remain |
| Relation/claim/TRACE semantic separation | FAIL | currently one edge concept carries incompatible identities |
| Graph migration authority | FAIL | canonical JSON does not self-regenerate the graph |
| High-level role model | PASS | seven roles and definer boundary are present |
| Executable role/grant matrix | PARTIAL | exact role attributes/default privileges/negative tests absent |
| Single research-release seal/CAS | PASS | state machine, receipts, manifest, sidecar, and pointer CAS are strong |
| Research/visual dual-version seal | FAIL | separate visual registry identity/pointer is absent |
| Canonical/graph/derived/aspiration taxonomy | PARTIAL | design is clear here; baseline normative docs still require correction |
| Repository hygiene gate | PARTIAL | A1 evidence exists, normative gate absent |
| Research/data-quality freeze gate | PARTIAL | A3 evidence exists, normative gate absent |
| Machine-readable contract gate | PARTIAL | API baseline exists; publication gate is incomplete |
| Legacy v49 DDL isolation | FAIL | advertised runner can execute incompatible public-schema skeleton |
| Physical v49 schema | NOT IMPLEMENTED | expected and required to remain false in Phase 1B |

## 13. Readiness state

```text
AUDIT_COVERAGE_DATABASE_AND_DDL=COMPLETE
ENGINEERING_PRE_DDL_READY=false
RESEARCH_SEMANTICS_PRE_DDL_READY=false
RIGHTS_VISUAL_PRE_DDL_READY=false
OVERALL_PRE_DDL_READY=false
DATABASE_IMPLEMENTED=false
DATABASE_FREEZE_READY=false
FRONTEND_PROMOTION_READY=false
DEPLOYMENT_READY=false
```

The false readiness values do not mean v48 is corrupt. They mean frozen-output integrity is stronger than authoritative replay and that the Phase 1A logical design still lacks the research/claim and visual-registry identities needed to freeze physical keys safely.

## 14. Recommended closure sequence

At most three independent work packages should follow this audit:

1. **Research identity and graph authority decision.** Define operational archive objects, semantic relations, claim/epistemic classes, computed-analysis provenance, TRACE projection, corpus/missingness, and classify every legacy graph fact. Acceptance: zero ambiguous keys/cardinalities and zero unclassified graph facts.
2. **Rights-aware dual release and machine contract decision.** Define independent research/visual manifests, registries, current CAS, rights-safe URL behavior, stable URIs/JSON-LD/schema/DCAT/diff contract, and required gates. Acceptance: one exact research+visual pair is reproducible and rights-held pixel URLs cannot leak.
3. **Physical DDL execution boundary.** Approve the closed assignment/evidence registry, exact role/default-privilege matrix, a new v49-only migration namespace/runner, and legacy deny guard. Acceptance: clean empty replay produces only the eight v49 schemas, all negative privilege/unknown-relation/seal tests pass, and no legacy SQL is in the migration-set hash.

## 15. Actions explicitly not performed

- No PostgreSQL connection, database, schema, role, extension, migration, import, query, backup, or sidecar was created.
- No `scripts/run_db_migrations.py`, `psql`, Docker, SQLite write mode, `VACUUM`, data export, or data generator was run.
- No npm, Next.js, TypeScript, browser, screenshot, frontend, CI, deployment, PR, merge, rebase, commit, or push action was performed by A4.
- No legacy SQL, normative document, v48 JSON/SQLite/manifest/shard, QA screenshot, package file, CI file, deployment file, dirty-main file, or another audit report was modified.
- No `DELETE_CANDIDATE` was deleted and no old schema was renamed or archived.
- No environment/credential file was opened and no secret value was printed.

## 16. Residual processes and handoff

Every A4 shell execution completed and released its session. A4 started no Node, Next, TypeScript, PostgreSQL, Docker, browser automation, data generation, export, or server process. A4 did not perform a global OS process scan because the main auditor owns the final authorized residual-process gate; therefore the global residual state remains **main-auditor pending**, while A4-owned residual sessions are **0**.

The main auditor should use this report as baseline evidence, apply allowed normative corrections, then re-evaluate all ten P0 items against the final documents. This report itself does not authorize DDL.
