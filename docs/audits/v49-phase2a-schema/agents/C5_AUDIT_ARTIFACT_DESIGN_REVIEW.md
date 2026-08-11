# C5 — Phase 2A audit-artifact design review

- Phase: v49 Phase 2A
- Reviewer: C5, bounded read-only audit-artifact design reviewer
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Branch: `refactor/v49-data-platform`
- Reviewed baseline HEAD: `ee393a8956ef6a6e3bfcc5613b9356323ae37c0d`
- Reviewed SQL snapshot: `FINAL_SQL_STABLE_5`
- Snapshot checksum-list SHA-256: `23d2e588c78de7a6756d5fe57117bb972dde453ba44c7b9eb3b4a9373d6f4473`
- Result: **PASS — the design below covers every required Phase 2A artifact gate**
- PostgreSQL started or connected by C5: **no**
- Database SQL modified by C5: **no**
- Files modified by C5: **only this receipt**

`PASS` applies to the artifact design, not to row counts that the controller must
derive from the two final fresh databases. C5 does not assert the final schema
hash, replay count, role result, production-row count, fixture residue, commit,
push, or process cleanup. Those values remain controller-owned evidence.

## Task boundary

C5 reviewed only the design of these deliverables and their package wrapper:

1. `01_SCHEMA_OBJECT_INVENTORY.tsv`;
2. `02_TABLE_CONSTRAINT_MATRIX.tsv`;
3. `03_ROLE_GRANT_MATRIX.tsv`;
4. `05_NEGATIVE_TEST_REGISTER.tsv`;
5. `MANIFEST.json`, `CHECKSUMS.sha256`, changed-file allowlisting, and
   JSON/TSV structural verification insofar as they make the four TSVs
   reproducible.

C5 did not make an identity, cardinality, rights, relation, role, release,
serialization, or migration-policy decision. The existing SQL and normative
packages are inputs to the recommended extraction rules. C5 did not write the
four root TSVs, the package manifest/checksum ledger, or any final gate receipt.

## Assets read and evidence basis

### Phase 2A implementation

C5 byte-read the current `database/` tree and reviewed the definitions relevant
to inventory, constraint, privilege, and test extraction:

- 8 versioned migrations;
- 15 function files;
- 2 role/grant files;
- 2 view files;
- the transaction-scoped fixture;
- all 4 SQL test files;
- all 5 replay/hash/historical-verifier scripts;
- `database/README.md`, `database/PHYSICAL_SCHEMA.md`, and
  `database/JSON_MIGRATION_CONTRACT.md`.

The current tree contains 40 database files, 17,596 lines, and 819,841 bytes.
The hash-pinned SQL/replay/test subset contains 37 files. C5 independently
verified all 37 entries against
`/private/tmp/gda_v49_phase2a_stable5.sha256`; the list itself contains 37
entries and hashes to the value recorded above.

The source contains 9 project schemas, 223 `CREATE TABLE` declarations, 222
function declarations, 335 trigger declarations, 15 view declarations, and 7
cluster-role declarations. These are source-declaration counts only. They are
not safe final catalog counts because `CREATE OR REPLACE`, overloaded routines,
constraint-backed indexes, implicit table row types, and later `ALTER` files
change the installed-object cardinality.

### Prior audit package conventions

C5 read the complete manifests and checksum ledgers for:

- `docs/audits/v49-authority-research-delta/`;
- `docs/audits/v49-rights-machine/`;
- `docs/audits/v49-runtime-cleanup/`;
- `docs/audits/v49-phase1d-final/`.

The stable convention is:

- the manifest contains package identity, baseline/ancestor identity, scope,
  gates, input-package pins, and an artifact array of path/byte/hash records;
- the artifact array does not contain `MANIFEST.json` or
  `CHECKSUMS.sha256`, avoiding a hash cycle;
- `CHECKSUMS.sha256` contains every artifact plus `MANIFEST.json`;
- `CHECKSUMS.sha256` does not hash itself;
- historical packages are pinned by their manifest/checksum hashes, not
  rewritten or re-signed for a later HEAD.

### Review commands

Read-only command families used by C5:

```text
git status --short --branch
find database docs/audits/v49-phase2a-schema -type f
wc -lc database/**
sed -n <complete bounded ranges> <database and prior audit files>
rg -n <CREATE/ALTER/GRANT/REVOKE/test-label patterns> database
shasum -a 256 <database files and stable checksum list>
shasum -a 256 -c /private/tmp/gda_v49_phase2a_stable5.sha256
git diff --check -- database docs/audits/v49-phase2a-schema
```

No command connected to PostgreSQL or SQLite, touched port 5432, imported data,
ran a generator, accessed the network, or modified a frozen asset.

## Common TSV serialization contract

The four TSVs should use one closed lexical contract so a byte-level checksum
and a semantic parser agree:

1. UTF-8 without BOM, LF line endings, one terminal LF, no blank rows.
2. The first row is the exact ordered header specified below. Header names are
   unique lowercase ASCII `snake_case`.
3. Every record has exactly the header column count. Raw tab, CR, or LF is
   forbidden inside a field.
4. Null is encoded as `\N`; empty string is encoded as an empty field. They are
   never conflated.
5. Free text uses deterministic backslash escaping in this order: backslash
   becomes `\\`, tab becomes `\t`, CR becomes `\r`, and LF becomes `\n`.
6. Boolean values are exactly `true` or `false`; integers use canonical base-10
   notation; SHA-256 values are 64 lowercase hexadecimal characters.
7. Closed enum columns reject unknown values. Multi-valued cells are avoided.
   Where an ordered column list is unavoidable, encode it as a compact JSON
   array with no whitespace and validate it as JSON.
8. Rows are byte-sorted by the primary key stated for each TSV. Primary keys
   are unique and non-null.
9. Catalog OIDs must not appear in the committed TSVs. They are replay-local
   join aids and commonly differ between fresh clusters.
10. Catalog definitions are hashed from UTF-8 bytes after normalizing CRLF/CR
    to LF and stripping only trailing horizontal whitespace. Do not collapse
    SQL whitespace or case. PostgreSQL version is recorded in the package.

The authoritative structural parser should use a strict TSV reader, not a
spreadsheet application's display heuristics. A spreadsheet/artifact-tool
import is a useful secondary check that all rows and columns remain visible,
but it must not coerce identifiers, UUIDs, hashes, SQLSTATEs, or version tokens
to numbers or dates.

## 01_SCHEMA_OBJECT_INVENTORY.tsv

### Row unit

One row represents one installed project-schema catalog object or one table
column from a final fresh replay. The closed `object_kind` set is:

```text
SCHEMA
TABLE
PARTITIONED_TABLE
VIEW
MATERIALIZED_VIEW
SEQUENCE
TABLE_COLUMN
INDEX
ENUM
DOMAIN
COMPOSITE_TYPE
RANGE_TYPE
FUNCTION
PROCEDURE
TRIGGER
CONSTRAINT
```

Roles and grants belong in `03_ROLE_GRANT_MATRIX.tsv`; test-session `pg_temp`
objects and implicit array/table-row types do not belong here.

The stable object key is constructed without OIDs:

```text
SCHEMA:                 object_kind|schema_name
routine:                object_kind|schema_name|object_name|identity_arguments
column/index/trigger/
constraint:             object_kind|parent_schema|parent_name|object_name
all other objects:      object_kind|schema_name|object_name
```

### Exact recommended header

```text
object_key	object_kind	schema_name	object_name	identity_arguments	parent_schema	parent_name	owner_role	relation_persistence	relation_security_barrier	routine_language	routine_volatility	routine_security_definer	routine_search_path	type_category	definition_sha256_replay_1	definition_sha256_replay_2	replay_match
```

Column rules:

- `identity_arguments` is `pg_get_function_identity_arguments()` for routines
  and `\N` otherwise. It is required even when the routine has zero arguments.
- `parent_schema` and `parent_name` are mandatory for column, index, trigger,
  and constraint rows; they are `\N` otherwise.
- `relation_persistence` is one of `permanent`, `unlogged`, `temporary`, or
  `\N`. A committed project object must not be temporary.
- `relation_security_barrier` is a boolean for views and `\N` otherwise.
- the four `routine_*` fields apply only to functions/procedures.
  `routine_search_path` records the exact `proconfig` entry or `\N`.
- `type_category` is one of `enum`, `domain`, `composite`, `range`, or `\N`.
- the two definition hashes come from kind-specific deterministic catalog
  signatures. `replay_match` is true only when the same `object_key` exists in
  both final replays and both definition hashes match.

The signature for a table column must include ordinal, formatted type,
typmod, collation, nullability, generated/identity state, and default
expression. Relation signatures include owner, relkind, persistence, RLS
flags, and reloptions. Enum signatures include labels in `enumsortorder`.
Routine signatures include identity arguments, result type, language,
volatility, parallel safety, leakproof/security-definer flags, complete
`proconfig`, and `pg_get_functiondef()`. Trigger, index, constraint, domain,
and view signatures use the corresponding `pg_get_*def` function plus the
attributes that are not present in that textual definition.

### Catalog extraction pseudocode

```sql
WITH project_schema(name) AS (
  VALUES ('raw'),('core'),('provenance'),('research'),('rights'),
         ('workflow'),('release'),('audit'),('api_v1')
),
schema_rows AS (
  SELECT ... FROM pg_catalog.pg_namespace n JOIN project_schema s ...
),
relation_rows AS (
  SELECT ... FROM pg_catalog.pg_class c
  JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname IN (...) AND c.relkind IN ('r','p','v','m','S')
),
column_rows AS (
  SELECT ... FROM pg_catalog.pg_attribute a
  JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
  JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
  LEFT JOIN pg_catalog.pg_attrdef d
    ON d.adrelid = a.attrelid AND d.adnum = a.attnum
  WHERE n.nspname IN (...) AND a.attnum > 0 AND NOT a.attisdropped
),
index_rows AS (
  SELECT ..., pg_catalog.pg_get_indexdef(i.indexrelid)
  FROM pg_catalog.pg_index i
  JOIN pg_catalog.pg_class idx ON idx.oid = i.indexrelid
  JOIN pg_catalog.pg_class base ON base.oid = i.indrelid
  JOIN pg_catalog.pg_namespace n ON n.oid = base.relnamespace
  WHERE n.nspname IN (...)
),
routine_rows AS (
  SELECT ..., pg_catalog.pg_get_function_identity_arguments(p.oid),
         pg_catalog.pg_get_function_result(p.oid),
         pg_catalog.pg_get_functiondef(p.oid)
  FROM pg_catalog.pg_proc p
  JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
  WHERE n.nspname IN (...) AND p.prokind IN ('f','p')
),
type_rows AS (
  SELECT ... FROM pg_catalog.pg_type t
  JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
  WHERE n.nspname IN (...)
    AND t.typtype IN ('d','e','c','r')
    AND t.typelem = 0
    AND (t.typtype <> 'c' OR t.typrelid = 0)
),
trigger_rows AS (
  SELECT ..., pg_catalog.pg_get_triggerdef(t.oid, true)
  FROM pg_catalog.pg_trigger t
  JOIN pg_catalog.pg_class c ON c.oid = t.tgrelid
  JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname IN (...) AND NOT t.tgisinternal
),
constraint_rows AS (
  SELECT ..., pg_catalog.pg_get_constraintdef(k.oid, true)
  FROM pg_catalog.pg_constraint k
  JOIN pg_catalog.pg_namespace n ON n.oid = k.connamespace
  WHERE n.nspname IN (...)
)
SELECT * FROM schema_rows
UNION ALL SELECT * FROM relation_rows
UNION ALL SELECT * FROM column_rows
UNION ALL SELECT * FROM index_rows
UNION ALL SELECT * FROM routine_rows
UNION ALL SELECT * FROM type_rows
UNION ALL SELECT * FROM trigger_rows
UNION ALL SELECT * FROM constraint_rows;
```

### Completeness oracles

- `object_key` is unique and the TSV row count equals the independently
  recomputed union count for each replay.
- The set symmetric difference of object keys between replay 1 and replay 2
  is empty; every `replay_match` is true.
- Every non-dropped column of every project relation appears exactly once.
- Every project index, non-internal trigger, user constraint, routine, enum,
  domain, and approved view appears exactly once.
- Every trigger/function/constraint parent key resolves to another inventory
  row.
- All 9 schemas exist and are owned by
  `gda_v49_phase2a_schema_owner`; no project object is temporary or extension
  owned.
- Every `SECURITY DEFINER` routine records
  `search_path=pg_catalog`; the count missing that setting is zero.
- The three `api_v1` public views and the role-workspace/audit views are
  distinct objects, not misclassified tables.
- Source declaration counts are diagnostic only; they must never replace the
  catalog-union oracle.

## 02_TABLE_CONSTRAINT_MATRIX.tsv

### Row unit

One row represents one installed table control. The union deliberately covers
both declarative constraints and non-`pg_constraint` enforcement:

```text
PRIMARY_KEY
UNIQUE_CONSTRAINT
FOREIGN_KEY
CHECK
EXCLUSION
NOT_NULL
COLUMN_DEFAULT
GENERATED_COLUMN
IDENTITY_COLUMN
INDEX
UNIQUE_INDEX
CONSTRAINT_TRIGGER
ROW_TRIGGER
```

An index backing a primary/unique/exclusion constraint remains an `INDEX` row
but links to its constraint through `backing_constraint_key`. It is not counted
as a second declarative constraint. User constraint triggers are represented by
their non-internal `pg_trigger` row; a corresponding `pg_constraint` trigger
metadata row, if present, is linked rather than emitted twice.

### Exact recommended header

```text
control_key	table_schema	table_name	control_kind	control_name	column_names_json	referenced_schema	referenced_table	referenced_columns_json	match_type	on_update	on_delete	deferrable	initially_deferred	validated	enabled_state	trigger_timing	trigger_events_json	trigger_level	guard_function_identity	predicate_escaped	definition_sha256_replay_1	definition_sha256_replay_2	replay_match	backing_constraint_key	normative_invariant	test_ids_json	status
```

The primary key is `control_key`, formed as
`table_schema|table_name|control_kind|control_name`. Synthetic column controls
use stable names such as `column_name:NOT_NULL`. Ordered column/event/test lists
are compact JSON arrays. `status` is exactly `PASS` or `FAIL` and is `PASS`
only when the catalog object, replay match, normative mapping, and referenced
test evidence all agree.

`normative_invariant` is a closed implementation tag, not free-form policy.
Recommended values include:

```text
IDENTITY_FK
NATURAL_KEY
CANONICAL_PARENT_RESTRICT
CLOSED_SUBTYPE
DEFERRED_EVIDENCE_VALIDATION
UNKNOWN_RELATION_FAIL_CLOSED
APPEND_ONLY
SEALED_MUTATION_GUARD
CURRENT_POINTER_CAS
RIGHTS_AXIS_SEPARATION
PUBLIC_LOCATOR_REDACTION
ACCESS_PATH_ONLY
```

### Catalog extraction pseudocode

```sql
-- Declarative constraints (exclude trigger metadata duplicated below).
SELECT ...,
  pg_catalog.pg_get_constraintdef(c.oid, true),
  c.contype, c.condeferrable, c.condeferred, c.convalidated,
  c.confmatchtype, c.confupdtype, c.confdeltype
FROM pg_catalog.pg_constraint c
JOIN pg_catalog.pg_class t ON t.oid = c.conrelid
JOIN pg_catalog.pg_namespace n ON n.oid = t.relnamespace
WHERE n.nspname IN (...) AND c.contype IN ('p','u','f','c','x');

-- Column controls absent from pg_constraint.
SELECT ... FROM pg_catalog.pg_attribute a
LEFT JOIN pg_catalog.pg_attrdef d ...
WHERE a.attnum > 0 AND NOT a.attisdropped
  AND (a.attnotnull OR d.oid IS NOT NULL
       OR a.attgenerated <> '' OR a.attidentity <> '');

-- Every index, including predicate/expression/include columns.
SELECT ..., i.indisunique, i.indisprimary, i.indisvalid, i.indisready,
  pg_catalog.pg_get_indexdef(i.indexrelid),
  pg_catalog.pg_get_expr(i.indpred, i.indrelid, true)
FROM pg_catalog.pg_index i ...;

-- Every user trigger; map tgfoid through regprocedure identity.
SELECT ..., t.tgenabled, t.tgdeferrable, t.tginitdeferred,
  p.oid::regprocedure::text,
  pg_catalog.pg_get_triggerdef(t.oid, true)
FROM pg_catalog.pg_trigger t
JOIN pg_catalog.pg_proc p ON p.oid = t.tgfoid ...
WHERE NOT t.tgisinternal;
```

Column arrays must be resolved by ordinal from `conkey`/`confkey` and
`indkey`; never serialize raw `int2vector` values as if they were names.

### Completeness oracles

- Every ordinary/partitioned table in inventory appears in the matrix and has
  exactly one primary-key control unless an explicit, reviewed exception is
  recorded. No exception is expected for this Phase 2A schema.
- The matrix row count equals the independent union of constraints, selected
  column controls, all indexes, and all non-internal triggers.
- All foreign-key parent/column identities resolve; all referenced parent
  tables exist; no FK is unvalidated.
- Any `ON DELETE CASCADE` or `ON UPDATE CASCADE` is explicitly mapped. A
  cascade reaching canonical `raw`, `core`, `provenance`, or `research`
  parents is a blocker. Do not impose a false global zero-cascade rule on
  release-owned child structures without checking the normative mapping.
- Every deferred cross-table evidence/subtype/relation/release completeness
  control is a constraint trigger with the intended deferrability and enabled
  state. Every append-only/sealed guard is enabled.
- Every `guard_function_identity` resolves to the exact overloaded routine in
  inventory and every test ID resolves in the negative register.
- Every index in inventory has one matrix row, including partial/expression
  indexes; invalid or not-ready indexes are blockers.
- Replay object sets and definition hashes are identical and every status is
  `PASS`.

## 03_ROLE_GRANT_MATRIX.tsv

### Row unit

One row represents one expected-versus-actual privilege, role attribute,
membership, or default-ACL cell. The closed `record_kind` set is:

```text
ROLE_ATTRIBUTE
ROLE_MEMBERSHIP
DATABASE_PRIVILEGE
SCHEMA_PRIVILEGE
TYPE_PRIVILEGE
RELATION_PRIVILEGE
SEQUENCE_PRIVILEGE
ROUTINE_PRIVILEGE
DEFAULT_ACL
```

The principal set is the seven `gda_v49_phase2a_*` roles plus the `PUBLIC`
sentinel. The matrix is not merely an export of positive ACL rows: it includes
the closed negative cross-product needed to prove least privilege.

### Exact recommended header

```text
grant_key	principal	principal_kind	record_kind	object_kind	object_schema	object_identity	privilege_or_attribute	expected_effective	actual_effective	actual_direct	grantor	is_grantable	effective_via	default_acl_owner	default_acl_schema	test_id	replay_match	status
```

`grant_key` is
`principal|record_kind|object_schema|object_identity|privilege_or_attribute`.
`expected_effective`, `actual_effective`, `actual_direct`, `is_grantable`, and
`replay_match` are booleans or `\N` where the concept does not apply.
`effective_via` is one of `DIRECT`, `PUBLIC`, `MEMBERSHIP`, `OWNER`,
`SET_ROLE`, `BUILTIN_DEFAULT`, or `NONE`.

Routine identity must be exact `regprocedure` text including identity
arguments. A function name without arguments is not a valid matrix key.

### Closed privilege cross-product

For each principal, generate these cells even when the answer is false:

| Scope | Privileges/attributes |
|---|---|
| Role attribute | `LOGIN`, `SUPERUSER`, `CREATEDB`, `CREATEROLE`, `INHERIT`, `REPLICATION`, `BYPASSRLS` |
| Role membership | every ordered pair of the seven roles, `MEMBER` |
| Database | `CONNECT`, `CREATE`, `TEMP` |
| Every project schema | `USAGE`, `CREATE` |
| Every table/view | `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `REFERENCES`, `TRIGGER` |
| Every sequence | `USAGE`, `SELECT`, `UPDATE` |
| Every function/procedure | `EXECUTE` |
| Every enum/domain/composite/range type | `USAGE` |
| Schema-owner default ACL | `PUBLIC` on tables, sequences, routines, and types for the relevant default privilege |

The schema owner is intentionally `NOLOGIN`. Migrator membership in the owner
is intentional and must be represented as `SET_ROLE`, not mistaken for a
runtime privilege leak. No other runtime role may be a member of the owner.

### Catalog extraction pseudocode

```sql
-- Attributes and memberships.
SELECT rolname, rolcanlogin, rolsuper, rolcreatedb, rolcreaterole,
       rolinherit, rolreplication, rolbypassrls
FROM pg_catalog.pg_roles WHERE rolname LIKE 'gda_v49_phase2a_%';

SELECT member.rolname, parent.rolname, m.admin_option,
       pg_catalog.pg_has_role(member.oid, parent.oid, 'MEMBER')
FROM pg_catalog.pg_auth_members m
JOIN pg_catalog.pg_roles parent ON parent.oid = m.roleid
JOIN pg_catalog.pg_roles member ON member.oid = m.member;

-- Direct ACL evidence. Use aclexplode on database/schema/class/proc/type ACLs.
SELECT ... FROM pg_catalog.aclexplode(COALESCE(object_acl,
                                                acldefault(...))) ...;

-- Default ACLs are separate evidence.
SELECT d.defaclrole, d.defaclnamespace, d.defaclobjtype, x.*
FROM pg_catalog.pg_default_acl d
CROSS JOIN LATERAL pg_catalog.aclexplode(d.defaclacl) x;

-- Effective values use the object OID, not an ambiguous text name.
SELECT pg_catalog.has_database_privilege(role_oid, database_oid, privilege),
       pg_catalog.has_schema_privilege(role_oid, schema_oid, privilege),
       pg_catalog.has_table_privilege(role_oid, relation_oid, privilege),
       pg_catalog.has_sequence_privilege(role_oid, sequence_oid, privilege),
       pg_catalog.has_function_privilege(role_oid, routine_oid, 'EXECUTE'),
       pg_catalog.has_type_privilege(role_oid, type_oid, 'USAGE');
```

`information_schema.role_table_grants` alone is insufficient: it omits role
attributes, role membership, owner semantics, `PUBLIC`, default ACLs, most
object kinds, and denied cross-product cells.

### Completeness oracles

- Matrix cardinality equals the closed principal/object/privilege
  cross-product plus role-attribute, membership, and default-ACL rows.
- Every `expected_effective` equals `actual_effective` in both fresh replays;
  every status is `PASS`.
- `PUBLIC` has no database `CONNECT`, project-schema usage, project object
  privilege, project type usage, or routine execute privilege.
- All runtime roles lack superuser, createdb, createrole, replication, and
  bypass-RLS attributes. Only the migrator has owner membership.
- `api_reader` has exactly `USAGE` on `api_v1` and `SELECT` on the three
  approved public views; it has no base-table read or any write privilege.
- Reviewer, ingestor, publisher, and auditor positive grants are exact
  allowlists. Publisher has controlled-function execute but no direct release
  DML; auditor cannot promote; reviewer cannot seal; ingestor cannot register
  frozen authority.
- All schema-owner default ACL rows deny `PUBLIC` table/sequence/type access
  and function execute. Absence must not be interpreted as denial because
  PostgreSQL built-in function defaults can grant `PUBLIC EXECUTE`.
- Every routine privilege resolves to one exact routine inventory key and all
  replay values match.

## 05_NEGATIVE_TEST_REGISTER.tsv

### Row unit

One row represents one independently executable oracle: a helper-based error
expectation, explicit failure sentinel, catalog assertion, state/postcondition
assertion, positive control required to prove a negative rule is reachable, or
fixture-residue assertion. It is not one row per SQL file and not one row per
statement inside a compound fixture.

The closed `oracle_kind` set is:

```text
EXACT_ERROR
SQLSTATE_SET
PRIVILEGE_EXCEPTION
BOOLEAN_POSTCONDITION
CATALOG_ASSERTION
POSITIVE_CONTROL
ROLLBACK_RESIDUE
DETERMINISM
```

### Exact recommended header

```text
test_id	gate_domain	requirement_id	oracle_kind	test_file	test_line_start	sql_label_or_marker	actor_role	transaction_isolation	fixture_scope	enforcement_object_identity	expected_sqlstates_json	expected_message	expected_postcondition_escaped	expected_audit_effect_escaped	rollback_required	test_file_sha256	replay_1_result	replay_2_result	replay_match	status	notes
```

`test_id` is a stable identifier such as `P2A-REL-UNKNOWN-ACCEPT-001`; it is
the primary key. `requirement_id` is one atomic Phase 2A requirement. If one
executable assertion covers multiple requirements, assign the primary
requirement and create separate executable assertions or explain the compound
coverage in `notes`; do not duplicate a test row with the same test ID.

`expected_sqlstates_json` is an ordered JSON array such as `["23514"]` or
`["23503","55000"]`. Exact semantic tests must fill `expected_message`.
Stateful negative tests must fill both the unchanged-state postcondition and
any required append-only failure/audit effect. A caught exception without a
postcondition is insufficient for CAS, publication, seal, sidecar, and rights
tests.

### Minimum requirement crosswalk

The register is complete only when every item below maps to at least one
passing row in each final replay:

#### Identity and FK

- orphan object/source, evidence, claim, relation, and endpoint paths fail;
- closed entity subtype mismatch fails;
- arbitrary string polymorphic targets are absent;
- duplicate governed occurrence/natural fingerprints fail at their specified
  key, without implying global raw-fingerprint deduplication;
- canonical parent deletion is restricted.

#### Relation, evidence, and TRACE

- unknown relation accepted fails;
- inactive relation type accepted fails;
- accepted relation without qualifying evidence fails;
- legacy projection cannot be promoted to an accepted semantic relation;
- automatic influence/transitivity remains absent;
- held/rejected operational rows survive release construction;
- zero accepted TRACE relation/edge release validates and seals;
- derived TRACE/Search surfaces have no canonical back-write grant/path;
- claim-revision succession proves immutable relation support can advance
  without rewriting prior evidence.

#### Rights and visual registry

- unknown rights plus healthy endpoint cannot produce `REMOTE_IMAGE`, reaching
  the delivery validator with exact
  `23514 / DELIVERY_ASSESSMENT_EXCEEDS_FAIL_CLOSED_CAP`;
- permitted rights plus viewer-only provider policy cannot embed, with the
  same exact fail-closed-cap error;
- permitted rights plus unreachable endpoint fails with exact
  `23514 / DELIVERY_REQUIRES_MATCHING_HEALTHY_FRESH_TYPED_LOCATOR`;
- a health observation never raises the independent rights/policy ceiling;
- active takedown removes locators, stricter correction wins, and attempted
  relaxation fails;
- zero positive-rights registry is valid and returns research metadata;
- raw/internal/held locators remain unreadable/unrepresentable to public role;
- accepted object/visual bridge cannot lose evidence-bound review support and
  cannot have competing/future current decisions.

#### Release, CAS, and security

- post-seal child insert, update, delete, and manifest update all fail;
- stale and null-expected CAS fail with pointer unchanged and failure attempt
  appended;
- unsealed research and visual current promotion fail;
- research and visual current generations remain independent;
- `PUBLIC` access is absent;
- `api_reader` write and raw read fail;
- curator/ingestor seal fails;
- publisher direct base-table bypass fails;
- auditor promotion fails;
- every `SECURITY DEFINER` routine pins `search_path=pg_catalog`, has no dynamic
  SQL, and is not exploitable through caller search path;
- seal functions fail outside a serializable transaction;
- successful promotions append publication history atomically.

#### Determinism and cleanup

- restricted JCS, timezone-invariant fractional analysis, and visual/research
  fingerprint controls pass;
- every fixture transaction rolls back;
- every project base table has zero residue after each test run;
- production row count remains zero.

### Extraction and completeness pseudocode

```text
for each database/tests/*.sql in replay order:
  parse pg_temp.expect_error / expect_error_message invocations;
  parse ASSERTION_FAILED labels from pg_temp.assert_true invocations;
  parse explicit EXPECTED_*_NOT_RAISED sentinels in DO blocks;
  parse CAS failure reason-code count assertions;
  bind each to file SHA, source line, actor role, isolation, enforcement object,
  expected SQLSTATE/message, postcondition, and rollback boundary;
  reject an unregistered executable oracle or a register row with no source;

add harness-level rows for:
  replay exit status, schema hash equality, fixture residue, production rows,
  historical audit verification, and process cleanup where applicable;
```

The current SQL uses both helper calls and manual `DO`-block sentinels; a
regex that reads only helper labels will undercount role/security tests. CAS
negative outcomes are often asserted by append-only reason-code counts rather
than thrown exceptions. The extractor must support all three forms.

### Completeness oracles

- Every executable oracle label/marker in the four test files appears exactly
  once in the register; every register source location resolves to the same
  file SHA.
- Every minimum requirement above has a passing register row and no required
  domain has an untested item.
- Both final replay results are `PASS`; `replay_match` and `status` are true/
  `PASS` for every row.
- Critical rights tests name the exact delivery validator error, not a generic
  append-only update error. The current `FINAL_SQL_STABLE_5` tests satisfy this
  design by appending successor histories.
- CAS/seal/takedown/public-redaction tests include state and audit
  postconditions. Error receipt alone is not enough.
- `rollback_required=true` for fixture tests and the controller independently
  proves `TEST_FIXTURE_RESIDUE=0` after the harness.

## Required MANIFEST.json design

The recommended top-level schema identifier is
`v49.phase2a-schema-manifest/v1`, with `packageVersion` `1.0.0`. Required
top-level fields are:

```text
schema
packageVersion
phase
phaseStatus
branch
initialCommit
implementationCommit
finalReceiptCommit
frozenSourceAncestor
requiredAncestors
normativeVersion
scope
inputAuditPackages
postgresqlEnvironment
sourceSnapshot
schemaReplay
testExecution
gates
deferred
processReceipt
artifacts
```

Required semantics:

- `initialCommit` is the fixed Phase 2A start
  `ee393a8956ef6a6e3bfcc5613b9356323ae37c0d`.
- `requiredAncestors` records full identities for `0404c7f`, `6b111a7`, and
  `967cbe3` and their verified-ancestor result.
- `implementationCommit` identifies the SQL/test implementation commit;
  `finalReceiptCommit` identifies the commit containing final receipts. If the
  manifest is generated before that final commit exists, use an explicit null
  plus a separately recorded current implementation tree hash; never invent a
  future commit.
- `scope` explicitly states: empty physical schema only; no v48 JSON, SQLite,
  TRACE shards, legacy edges, image assets, frontend, HTTP API, ORM, CI,
  deployment, or production data.
- `inputAuditPackages` pins Phase 1C, rights/machine, and Phase 1D final
  manifest/checksum paths and SHA-256 values, the expected historical base
  commit/version, and the new verifier-run result. Historical receipts are not
  modified.
- `postgresqlEnvironment` records exact PostgreSQL version, dedicated Unix
  socket, non-5432 port, task-created cluster path/PID, no external listen,
  and the later clean-stop/removal result. Ephemeral paths are evidence, not
  committed dependencies.
- `sourceSnapshot` records the 37-entry stable SQL checksum-list hash and the
  final `database/schema-manifest.json` hash.
- `schemaReplay` records both fresh database names, replay count, normalized
  schema hashes, equality, schema-hash algorithm/script hash, schema-only dump
  hashes/bytes, production row count, and fixture residue.
- `testExecution` records constraint, role, seal/CAS, serializable, zero-state,
  redaction, and historical-verifier results plus log hashes.
- `gates` uses the exact typed final fields requested for Phase 2A. Counts are
  integers and gate values are JSON booleans, not strings.
- `deferred` separates later JSON population, API/frontend/CI/deployment, and
  workload-driven physical tuning from Phase 2A blockers.
- `processReceipt` records final task-owned PostgreSQL, Node, Next, tsc,
  browser, Docker, and generator process counts.
- every `artifacts` element has exactly `path`, `bytes`, `sha256`, and `role`.
  Paths are unique, repository-relative POSIX paths with no `..`, leading `/`,
  symlink traversal, tab, CR, or LF.

### Checksum scope

The manifest artifact array and checksum ledger must cover:

- every committed file under the exact final `database/` implementation,
  including migration, function, role, view, fixture, test, script, physical
  docs, JSON migration contract, and `database/schema-manifest.json`;
- all required `docs/audits/v49-phase2a-schema/00` through `12` receipts/
  ledgers, the four TSVs, `AGENT_TASK_REGISTER.md`, agent receipts, and any
  package-local deterministic verifier used to generate or validate them.

The artifact array excludes `MANIFEST.json` and `CHECKSUMS.sha256`.
`CHECKSUMS.sha256` contains the exact artifact path set plus `MANIFEST.json`,
sorted bytewise by path. It excludes itself. Each line is exactly:

```text
<64 lowercase hex><two ASCII spaces><repository-relative path><LF>
```

Temporary clusters, schema dumps, normalized dumps, and logs are not committed
artifacts. Their exact bytes/hash/path/size/regeneration command belong in the
execution receipts and manifest evidence blocks before the task-owned temp
directory is safely removed.

## Changed-file allowlist

The permitted roots are deliberately narrow:

```text
database/
docs/audits/v49-phase2a-schema/
```

That prefix check is necessary but not sufficient. The final allowlist is the
exact, sorted path list in the Phase 2A manifest plus `MANIFEST.json` and
`CHECKSUMS.sha256`. `git diff --name-only` and untracked-file enumeration must
be equal to that declared set, subject only to files already committed in an
earlier Phase 2A commit. A broad glob must not silently admit an unexpected
file.

Explicitly forbidden changes include:

```text
frontend/**
generated/**
data/**
db/**
docs/audits/v49-authority-research-delta/**
docs/audits/v49-rights-machine/**
docs/audits/v49-phase1d-final/**
ARCHITECTURE.md
DATA_MODEL_V49.md
READ_API_V1.md
MIGRATION_V48_TO_V49.md
ACCEPTANCE_GATES.md
docs/architecture/DDL_DECISION_PACK_V49.md
docs/adr/**
```

The last normative paths may change only after an independently proven
normative conflict. C5 found no artifact-design reason to change them.

## JSON, TSV, and checksum validation rules

Before commit and again before push, the controller should require all of the
following:

1. JSON parses with duplicate-key rejection, UTF-8 decoding, no NaN/Infinity,
   no floating counts, and the exact expected top-level schema/version.
2. Artifact paths are unique, sorted, regular files, inside the repository and
   inside the exact allowlist; bytes and SHA-256 recompute exactly.
3. Checksum lines match `^[0-9a-f]{64}  [^\t\r\n]+$`; path order is bytewise;
   the ledger path set is exactly artifact paths plus `MANIFEST.json`.
4. Every TSV satisfies the common lexical contract, exact header, exact column
   count, closed enums, field types, sorted unique primary key, and non-empty
   row set.
5. Cross-file references resolve: constraints to inventory, role objects to
   inventory, negative-test enforcement objects to inventory/constraint rows,
   and constraint test IDs to the negative register.
6. Catalog union/cross-product counts independently reconcile to every TSV;
   replay 1/replay 2 symmetric differences are empty.
7. Every row-level status is `PASS`; top-level aggregate counts equal parsed
   row counts and do not rely on Markdown prose.
8. `database/schema-manifest.json` file order exactly matches replay order and
   pins the same SQL/test/script bytes as the Phase 2A manifest.
9. `git diff --check` passes, then the changed-file set and manifest/checksum
   sets are recomputed after staging to catch late drift.

## Collision and ambiguity risks

| Risk | Required prevention |
|---|---|
| Overloaded or replaced routines | Key by `schema.name(identity_arguments)`; use final catalog, not `CREATE FUNCTION` count. |
| Constraint/index/trigger names are not globally unique | Include parent schema/table and object kind in keys. |
| Constraint-backed index double count | Inventory both objects; matrix links `backing_constraint_key` and does not call the index a second constraint. |
| Implicit array and table row types inflate type counts | Exclude arrays and relation row types from standalone type rows. |
| Views share `pg_class` with tables | Classify by `relkind`; do not derive kind from schema or name. |
| Dropped columns remain in `pg_attribute` | Require `attnum > 0 AND NOT attisdropped`. |
| OIDs differ between fresh replays | Never commit OIDs; compare semantic keys and definition hashes. |
| `information_schema` hides grants | Use `pg_catalog`, ACL explosion, `has_*_privilege`, membership, and default ACLs. |
| Owner/NOINHERIT/SET ROLE semantics look like runtime leakage | Record `effective_via` and treat the migrator owner membership as an explicit migration boundary. |
| `PUBLIC` is not a normal role row | Generate it as a sentinel principal and test it directly. |
| Missing default ACL can mean built-in allow | Inspect `pg_default_acl`; do not equate absence with denial, especially function execute. |
| Free-form SQL definitions break TSV shape | Hash normalized bytes and apply the common escaping contract. |
| Generic error masks intended semantic validation | Pin critical SQLSTATE/message and enforcement object, plus state postcondition. |
| Manual `DO`-block security tests escape helper parsing | Parse `EXPECTED_*_NOT_RAISED` sentinels and CAS reason-code assertions. |
| Source declaration counts diverge from installed catalog | Treat source counts as diagnostics only; catalog union is authoritative. |
| Transient logs disappear during cleanup | Record size/hash/regeneration command before exact temp removal. |

## Blocking versus deferred findings

### Blocking for `PHYSICAL_SCHEMA_IMPLEMENTED`

- any missing, duplicate, malformed, unsorted, or catalog-incomplete TSV row;
- any object/definition difference between the two final fresh replays;
- any unresolved constraint/trigger/function/test cross-reference;
- any invalid/not-ready index, unvalidated constraint, disabled required guard,
  or canonical-parent cascade outside an explicit normative mapping;
- any role cross-product mismatch, `PUBLIC` access, API write/base read,
  unpinned `SECURITY DEFINER`, runtime DDL, or direct publisher release DML;
- any missing minimum negative oracle, false-positive oracle, wrong semantic
  SQLSTATE/message, pointer mutation on failed CAS, or missing audit event;
- historical input manifest/checksum drift, current artifact hash mismatch, or
  changed-file allowlist drift;
- schema-hash inequality, production rows, fixture residue, unsafe cluster
  isolation, or task-owned residual process.

### Deferred and non-blocking for Phase 2A

- importing or reconciling the 15,923 JSON surfaces;
- materializing the 7,995 research-eligible / 7,928 held population;
- populating a TRACE release beyond the legal empty state;
- obtaining positive visual rights beyond the legal zero baseline;
- HTTP API, OpenAPI, JSON Schema, JSON-LD, DCAT, frontend repository adapter,
  browser evidence, CI, deployment, and production health services;
- synthetic capacity loading, query-plan performance claims, partitioning,
  PostGIS, graph storage, full-text search, broad GIN, or materialized
  visualization structures;
- extra two-session contention tests beyond the required serializable seal/CAS
  contract, provided the required Phase 2A negative and isolation tests pass.

The future engineering capacities of 20,000, 50,000, or 100,000 objects are
not acceptance counts and must not appear as a TSV or manifest PASS threshold.

## Findings and unresolved controller work

### Findings

1. The four TSVs can be derived deterministically without modifying schema or
   production state.
2. Catalog OID removal plus semantic object keys prevents false replay drift.
3. A full negative privilege cross-product is necessary; a positive ACL export
   alone cannot prove least privilege.
4. Critical rights tests in `FINAL_SQL_STABLE_5` now reach the intended
   delivery validators rather than stopping at the append-only mutation guard.
5. Prior manifest/checksum conventions cleanly avoid self-hash cycles and can
   pin both the historical baseline and current implementation identity.

### Unresolved, non-design items owned by the controller

- run the two final fresh replays and populate actual catalog counts/hashes;
- generate the four TSVs from those final databases;
- run strict JSON/TSV/checksum/cross-reference validation;
- record final commits, push identity, cluster shutdown/removal, and residual
  process counts;
- appoint the independent final verifier and resolve any discrepancy it finds.

These are execution steps, not gaps in the artifact design.

## Exit receipt

```text
TASK_BOUNDARY_COMPLETE=true
FOUR_TSV_DESIGNS_COMPLETE=true
CATALOG_COMPLETENESS_ORACLES_COMPLETE=true
MANIFEST_CHECKSUM_SCOPE_COMPLETE=true
ALLOWLIST_DEFINED=true
JSON_TSV_VALIDATION_DEFINED=true
COLLISION_RISKS_COVERED=true
BLOCKING_DEFERRED_BOUNDARY_COVERED=true
DATABASE_SQL_MODIFIED=false
POSTGRESQL_STARTED_OR_CONNECTED=false
LONG_PROCESS_STARTED=false
C5_OWNED_RESIDUAL_PROCESS_COUNT=0
EXIT_STATUS=PASS
```
