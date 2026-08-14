# D4 — Import atomicity, idempotency, and deterministic-verification review

## Assignment, scope, and exit condition

**Task.** Independently review the Phase 2B population implementation for
transaction atomicity, idempotency, raw/source identity lineage, forbidden
non-Candidate backfill, failure injection, and deterministic verification.

**Boundary observed.** This was a static review only. I did **not** parse the
Candidate JSON, open SQLite, start or connect to PostgreSQL, invoke the
importer, modify a migration, modify a frozen asset, or write outside this
record. The only commands used were repository reads plus Python `ast.parse`
and JSON parsing of implementation files. Both returned `PASS` without
executing the importer.

**Result at review handoff.** `PHASE2A_SCHEMA_CONFLICT=false`.
The Phase 2A model can express the required no-release rehearsal without a
forward schema migration. Several implementation P0s were reported to the
primary executor during review; they must be remediated and independently
retested before a `MIGRATION_REHEARSAL_VERIFIED` gate can be claimed. This
record intentionally distinguishes those implementation findings from a
schema conflict.

## Evidence read

Read in full or searched to the relevant definitions:

- `database/data-migrations/v48-to-v49/{README.md,mapping-v1.json,expected-baseline.json,extract.py,import.py,prepare-staging.sql,prepare-runtime.sql,load.sql,verify.py}`;
- Phase 2A roles, replay runner, grants, raw/core/research/rights migrations,
  deferred constraint functions, controlled-write functions, and public
  views;
- Phase 2B D1, D2, and D3 independent records; and
- the locked Phase 2B requirements supplied to the primary task.

Static syntax/integrity check:

```text
PYTHON_AST_PARSE=PASS
JSON_PARSE=PASS
```

## Confirmed sound design elements

1. The implementation treats the Candidate SHA, mapping SHA, normalized
   schema SHA, extractor SHA, and original base commit as staging-manifest
   inputs. It refuses a non-private socket, port 5432, or a database without
   the `gda_v49_phase2a_` prefix.
2. The extractor creates a one-time staging bundle before PostgreSQL access,
   uses UUIDv5 recipes, retains the lexical Candidate as the one canonical
   source asset, and contains no SQLite/Search/TRACE population writer.
3. `load.sql` has no `ON CONFLICT`, performs all durable writes after staging,
   defers constraints only in one enclosing transaction, executes explicit
   parity checks, and reaches `SET CONSTRAINTS ALL IMMEDIATE` before commit.
4. Source-asset, source-record, surface-ledger, archive-object, and seed-link
   ordering follows the Phase 2A deferred reciprocal-FK model. The raw record
   fingerprint is propagated to the ledger, preserving the `raw` lineage
   requirement.
5. No legacy graph edge, accepted semantic relation, TRACE projection edge,
   current pointer, or release seal is staged by the reviewed loader.
6. The corrected surface-row ledger has exactly the required 15 columns:
   `source_ordinal` through `quarantine_id`; the emitted row shape matches it.

## P0 findings sent to the primary executor

### 1. Migration-role / temporary-staging boundary — remediated in the reviewed patch

The first version opened the import session as the disposable-cluster admin,
created temporary tables, then changed to `schema_owner`. That both bypassed
the `migrator -> schema_owner` boundary and would leave the owner role without
ACL access to admin-owned temporary tables.

The later reviewed patch takes the correct shape: each replay database must be
owned by `gda_v49_phase2a_schema_owner`; the session logs in as
`gda_v49_phase2a_migrator`, enters one transaction, then `SET ROLE`s to
schema owner before creating and reading temporary staging tables and writing
durable rows. The administrative role is now used only for read-only cluster
and schema-hash checks. Final execution must prove that every replay database
has that database owner and that no admin creates population rows.

### 2. Five-axis visual baseline was incomplete

The reviewed `load.sql` inserts visual reference/bridge/locator rows and
legacy classifications, but it did not yet insert the required separate
rights observation/unknown assessment, provider-policy evaluation, and
fail-closed delivery assessment. Classifications alone cannot substitute for
the separately governed rights, policy, delivery, health, and takedown axes.

The corrective implementation must create only source-supported unknown
rights/policy records and a valid `citation_only` or `link_only` assessment
with the governed Phase 2A FKs/decision history. It must create no permissive
provider, health observation, public pixel locator, or `remote_image`
decision. A zero `REMOTE_IMAGE` count by itself is not sufficient proof of a
delivery decision.

### 3. Normalized content hash was not semantic

The reviewed `verify.py` generated `stableKeySetSha256` and
`normalizedContentSha256` from the identical `stable_rows()` list. Those rows
omit, among other values, preferred labels, parsed projections, membership
reasons, visual classifications, and the required rights/policy/delivery
records. A content mutation preserving IDs and table counts would therefore
leave both hashes unchanged.

The corrected verifier must compute a distinct normalized semantic content
hash from deterministically ordered, domain-tagged rows covering every table
populated by Phase 2B. It may use raw/fingerprint columns in place of large
payloads, but must include every semantic target value and normalize
timestamps/session-dependent values explicitly.

### 4. Public-boundary check was not executed as `api_reader`

The initial `public_boundary()` query ran as the administrative role. Its
`has_table_privilege(api_reader, ...)` predicates are useful metadata checks,
but its public-view rows were not read using the actual API role, and it did
not attempt denied raw-locator SELECT or DML as that role.

The corrective test must connect as `gda_v49_phase2a_api_reader` for positive
approved-view access and negative raw/internal/held-locator and write tests.
A rollback-only release/current fixture is required for the positive object
case because Phase 2B correctly leaves no durable seal or current pointer.

### 5. Parity checks were count-only rather than a partition proof

The initial verifier counted `raw.fail_closed_delta` and membership rows but
did not prove distinct object/source identity, disjointness, or full ledger
coverage. A duplicate held delta combined with an omitted held object could
pass the raw count of 7,928.

The corrected verifier must establish the exact partition:

```text
15923 distinct ledger/object/raw/seed-link identities
7995 distinct eligible identities
7928 distinct held identities
eligible ∩ held = ∅
eligible ∪ held = all 15923 ledger identities
```

It must also verify exactly one visual disposition per ledger and a complete,
closed classification set per visual bundle, with source-record/asset and
fingerprint joins intact.

### 6. Mid-object fault must occur after a non-zero proper subset

The original `after_objects` injection checkpoint occurred after the complete
object/ledger/source/identity/TRACE block. It demonstrates a late rollback in
that block but not the required failure **during** object import.

The failure suite needs a deterministic split or equivalent failure point
after a non-zero proper subset of archive-object/ledger rows, followed by
assertions that the transaction committed zero batch and canonical rows.

### 7. Root-level field mapping / stale metadata reconciliation was absent

The field-occurrence walker traversed only `/surfaces/*`. It did not map or
inventory root-level `meta`, `folderTypes`, and `folders` fields beyond the
pair-set comparison. In particular it did not record the required stale raw
`/meta/traceMetadataSupportedCount=2970` reconciliation observation.

The implementation must add explicit root-level raw-only/reconciliation
occurrences (exact pointer, presence, type, literal hash, and disposition),
so `UNMAPPED_SOURCE_FIELDS=0` covers the entire Candidate rather than only
surface objects. This must not turn the stale scalar into a corpus membership
or canonical fact.

### 8. Same-batch collision binding needs all required components

The initial existing-batch lookup compared only batch UUID, Candidate/input
SHA, and mapping SHA. It did not persist or compare the extractor SHA or
implementation-base binding when returning a no-op. The user requirement is
that a same batch identity with *any* different binding fails.

The explicit mapping-collision hook added during review is a useful negative
test, but final code still needs a durable/verifiable bundle-binding comparison
for Candidate SHA, mapping SHA/version, schema SHA, extractor SHA, and base
commit before it may return `IDEMPOTENT_NOOP`.

## Required post-remediation test evidence

Before D6/final verification, retain command output or structured receipts
showing all of the following:

1. two fresh database replays with the same schema hash and distinct replay
   databases;
2. `COMMITTED` exactly once per fresh replay and an identical-bundle no-op;
3. a conflicting-bundle/batch collision failure with zero new durable rows;
4. the full required failure matrix, including source/schema preflight,
   after-staging, true mid-object, after-corpus, after-visual-locator,
   parity, duplicate/missing/extra surface, unmapped field/type, and mapping
   collision; every case must prove zero durable batch/canonical residue;
5. independent count vector, stable-key set hash, and normalized semantic
   content hash equality across replays;
6. real-credential `api_reader` tests plus the rollback-only public fixture;
   and
7. no committed release/current pointer/seal and no live task-owned database
   process after cleanup.

## Schema-forward decision

`BLOCKED_SCHEMA_FORWARD_MIGRATION_REQUIRED=false`.

The findings concern the Phase 2B importer/verifier and test harness, not an
unexpressible approved mapping. The existing Phase 2A tables and deferred
constraints can represent source-supported unknown rights/policy/delivery
state, the raw/root reconciliation record, full identity lineage, and
transaction rollback without modifying historical DDL.

## Exit status

D4 wrote this detailed independent receipt and exited. No database, long
process, browser, Node, TypeScript, Docker, or Candidate parser process was
started by this task.
