# Phase 2A C2 — security, visual release, seal/CAS and public-boundary review

- Reviewer: Phase 2A C2, independent read-only reviewer
- Review result: **PASS**
- Implementation result: **NOT ASSERTED BY C2**
- Reviewed branch/entry commit: `refactor/v49-data-platform` at `ee393a8956ef6a6e3bfcc5613b9356323ae37c0d`
- Frozen source ancestor: `0404c7f96f9189f576c4c5b1368061e4082e436b`
- Files written by C2: only this receipt

`PASS` means the locked Phase 1C/1D authority, rights, release, role and machine-boundary decisions contain no unresolved identity, cardinality, state, version, serialization or privilege contradiction that blocks physical DDL. It does not mean that a PostgreSQL cluster, migration, role, function, trigger, view or executable negative test has passed. Those results belong to the designated Phase 2A implementation and independent replay suites.

## Scope

C2 reviewed the physical-security implications of:

- the five independent visual axes: rights evidence/assessment, provider-policy version/evaluation, delivery decision, endpoint-health observation and takedown state;
- attribution as an additional explicit positive-delivery prerequisite, not a sixth collapsed rights status;
- independent research and visual release lifecycles, manifests, sidecars and current pointers;
- candidate closure, validated/sealed immutability, current-pointer CAS and transient research/visual mismatch;
- append-only post-seal health/takedown sidecars and effective-delivery reduction;
- owner/migrator/ingestor/reviewer/releaser/reader/auditor duties and their Phase 2A equivalent names;
- explicit grants, default privileges, hardened `SECURITY DEFINER` functions, public views and raw/held-locator non-disclosure;
- the adversarial negative-test oracle required to establish the boundary.

C2 did not design the core/research physical table inventory, edit SQL, run or connect to PostgreSQL, inspect an existing user database, import data, or execute a fixture.

## Complete-read and integrity evidence

C2 completely read the five root v49 documents, the DDL decision pack, all four ADRs, the Phase 1C authority/research package, the Phase 1D rights/machine package and the Phase 1D final package. Large TSV/JSON packages were read to EOF as bytes, UTF-8 decoded, structurally parsed, and checked for fixed row widths; this was in addition to semantic line-by-line review of the governing decision documents.

### Normative corpus

- `ARCHITECTURE.md`
- `DATA_MODEL_V49.md`
- `READ_API_V1.md`
- `MIGRATION_V48_TO_V49.md`
- `ACCEPTANCE_GATES.md`
- `docs/architecture/DDL_DECISION_PACK_V49.md`
- `docs/adr/0001-canonical-postgres-and-read-only-release.md`
- `docs/adr/0002-immutable-data-versioning.md`
- `docs/adr/0003-runtime-repository-and-fixture-mode.md`
- `docs/adr/0004-research-claims-corpora-and-visual-registry.md`

### Evidence packages

| Package | Files read to EOF | Structural result | Manifest SHA-256 | Checksums SHA-256 |
|---|---:|---|---|---|
| `docs/audits/v49-authority-research-delta/` | 25 | all text UTF-8; JSON parse PASS; TSV widths `12`, `20`, `16`, `19` as declared | `925efaf84b7a38c18beb0726968354dbe087819fa322031812134c39e7a911de` | `51f0657ef52d25369cc1c3785673a3a8588c702a0ec6f140ee2816407aebd23b` |
| `docs/audits/v49-rights-machine/` | 22 | all text UTF-8; JSON parse PASS; truth table `21×16`; visual baseline `72×29` | `69e8a78bf30d5af40527b90ab00353ce0aee04595ae9e6c337182455a84f0536` | `562b955a79f31dfea9fb23cdf67407d17a4563100997ee82c46fcfca8a998c24` |
| `docs/audits/v49-phase1d-final/` | 4 | all text UTF-8; JSON parse PASS; all three declared artifact checksums PASS | `c7d7f44d8fda37ee79ee122dd70c8924f9e348882141bc5eac3ee54c72746130` | `5230e8b50dde724ca3d069d5e13639b43b42bf2925f3d3151b88cc6a74c4d788` |

The Phase 1D rights checksum replay passes against the current tree. The Phase 1D final checksum replay also passes. A naive current-tree replay of the Phase 1C checksum file differs only for `ACCEPTANCE_GATES.md`, `DATA_MODEL_V49.md`, and `MIGRATION_V48_TO_V49.md`, which were intentionally changed by the authorized Phase 1D normative commit. The joint receipt verifies their exact Phase 1C blobs at `967cbe3` and all 25 package-local Phase 1C entries. This is the known manifest-pinned orchestration limitation that Phase 2A must fix without changing historical receipts; it is not evidence corruption or a schema-policy conflict.

### Representative evidence commands

```text
git status --short --branch
git rev-parse HEAD origin/refactor/v49-data-platform
wc -l -c <normative and package files>
sed -n '<bounded complete ranges>' <normative documents>
shasum -a 256 -c docs/audits/v49-rights-machine/CHECKSUMS.sha256
shasum -a 256 -c docs/audits/v49-phase1d-final/CHECKSUMS.sha256
python3 -c '<read every package file; UTF-8 decode; JSON parse; TSV row-width validation; SHA-256>'
rg -n '<seal/CAS/rights/role/search_path/public-view terms>' <normative corpus and legacy SQL>
wc -l -c db/*.sql db/README.md
sed -n '<bounded ranges>' db/*.sql
```

No command printed a secret value.

## Normative conflict review

### Conflict result

```text
AUTHORITY_CONFLICT=0
VISUAL_IDENTITY_CARDINALITY_CONFLICT=0
FIVE_AXIS_STATE_CONFLICT=0
DUAL_RELEASE_VERSION_CONFLICT=0
SEAL_CAS_CONFLICT=0
ROLE_PRIVILEGE_CONFLICT=0
PUBLIC_SERIALIZATION_CONFLICT=0
DDL_BLOCKING_CONFLICT=0
```

The following apparent differences are explicitly compatible, not conflicts:

1. Phase 1C and the Phase 1D decision-stage receipts retain pre-DDL readiness `false`; the later independent joint receipt is the authorized evidence that changes the five decision-level readiness fields to `true`.
2. The architecture role names `owner`, `ingestor`, `releaser`, and `reader` are responsibility names. Phase 2A may use the equivalent physical names `schema_owner`, `ingest_writer`/`curator`, `publisher`, and `api_reader`, provided the grants preserve the locked duties.
3. Research-current and visual-current are independent because neither operation writes the other pointer. Visual CAS still must read-lock and verify the expected research-current generation/pair. That compatibility guard is not lockstep coupling.
4. Research-current may advance while visual-current still names an older pair. This is an intentional fail-closed mismatch window: research remains available, visual composition is unavailable, and no old registry is inherited.
5. Explicitly selecting an incompatible visual pair is a typed mismatch error. Merely lacking a compatible visual current is a successful research-only state. The selection context distinguishes them.
6. Endpoint health may recover technically over time, but it can never increase the permission ceiling established by the sealed rights/policy/delivery decision. Effective delivery is always bounded above by that sealed decision and reduced by any active restrictive sidecar.

### Locked zero states

The schema and validation functions must accept these states without synthetic promotion:

```text
OPERATIONAL_ARCHIVE_OBJECTS=15923
RESEARCH_ELIGIBLE_OBJECTS=7995
HELD_OBJECTS=7928
ACCEPTED_TRACE_RELATIONS=0
POSITIVE_VISUAL_RIGHTS_COVERAGE=0.0000%
```

An empty accepted-TRACE projection and a visual registry containing only fail-closed delivery modes are valid. Neither validation nor seal may require a nonzero relation, pixel locator, `REMOTE_IMAGE` entry, or positive-rights assessment.

## Legacy SQL convention assessment

The checked-in `db/*.sql` chain is historical evidence only. It uses a mutable public schema, `IF NOT EXISTS`, mixed seed DML, free-text and array-packed relationships, `target_type + target_id`, collapsed rights/display enums, broad cascades, and no v49 role/default-privilege/seal/CAS boundary. It must not be sourced, replayed, copied as a migration prefix, or counted as the Phase 2A schema.

Useful style conventions that may be retained are limited to plain versioned SQL, explicit transaction ordering, readable snake-case identifiers, and `psql`-visible validation failures. New v49 migrations should be strict on a fresh database: unexpected pre-existing objects should fail rather than be hidden by indiscriminate `IF NOT EXISTS`.

## Required role and grant matrix

Physical role names may carry the mandated `gda_v49_phase2a_` prefix. The table below records responsibilities, not an instruction to reuse unprefixed global roles.

| Responsibility | Minimum allowed operations | Explicit denials | Ownership/elevation boundary |
|---|---|---|---|
| `schema_owner` | own all v49 schemas, types, tables, views and definer functions | routine login/runtime use | `NOLOGIN`; only object owner; audited break-glass outside application tests |
| `migrator` | connect during the migration window and `SET ROLE schema_owner` for reviewed, versioned migrations | runtime ingest/review/publish/read credentials | ephemeral/`NOINHERIT`; sole membership that can assume owner; the runner/manifest supplies the “approved migration” control |
| `ingest_writer` / curator-equivalent | append raw artifacts, records, literals, observations, proposed assertions and workflow cases through allowlisted functions | raw update/delete, acceptance/rejection, DDL, seal, pointer CAS, rights widening | owns nothing; no owner/publisher membership |
| `reviewer` | read assigned evidence/candidates; append evidence-bound review, rights/policy/delivery and takedown decisions through separate functions | raw rewrite, direct canonical DML, release projection DML, seal/CAS, DDL | owns nothing; effective actor is captured from `session_user` |
| `publisher` | read accepted state/receipts; build draft copied projections and invoke boundary-specific candidate/validate/seal/CAS functions | direct rights/research decision mutation, direct release DML, cross-boundary mutation, DDL | owns nothing; execute grants only on exact release functions |
| `api_reader` | `SELECT` only the approved `api_v1` positive-allowlist views/materializations and safe descriptors | base schemas, unsealed rows, raw/internal/held locators, every DML/DDL operation | owns nothing; no role membership or definer mutation function |
| `auditor` | select explicit audit views for hashes, receipts, grants, state/pointer history and approved protected evidence | DML/DDL, queue claim, review decision, seal/CAS, `SET ROLE`, `BYPASSRLS` | owns nothing; no definer bypass for ordinary audit reads |

The privilege bootstrap must revoke, before granting the allowlist:

- database `CONNECT` and `TEMP` from `PUBLIC`, then grant only required connect roles;
- `CREATE`/`USAGE` on every v49 and legacy-public schema from `PUBLIC`;
- all table, sequence, type and function privileges from `PUBLIC` where applicable;
- default table, sequence, type, schema and function privileges for objects later created by `schema_owner`;
- default function `EXECUTE`, because PostgreSQL otherwise grants it to `PUBLIC` at creation.

Application roles own no schema object and receive no broad `ALL TABLES` grant. `api_reader` and `auditor` read through explicit projection/audit surfaces. The owner must not be a production connection identity.

## `SECURITY DEFINER` boundary

Only the following narrowly separated operation families may be definer functions:

```text
append_raw_or_visual_observation          -> ingest_writer
append_review_or_rights_policy_decision   -> reviewer
append_takedown_event_or_override         -> reviewer
build_or_close_research_candidate         -> publisher
validate_and_seal_research_release        -> publisher
build_or_close_visual_candidate           -> publisher
validate_and_seal_visual_registry         -> publisher
promote_research_current_cas              -> publisher
promote_visual_current_cas                -> publisher
```

Required hardening for every definer function:

1. owner is the `NOLOGIN` schema owner;
2. `PUBLIC EXECUTE` is explicitly revoked and exactly one operational role receives `EXECUTE`;
3. function configuration fixes `search_path` to `pg_catalog` only; every project object, function, operator with nontrivial resolution risk, sequence and type is schema-qualified;
4. no dynamic SQL, caller-supplied schema/table/column identifier, `regclass` target, or interpolated SQL fragment is accepted;
5. the caller is checked against the expected responsibility and `session_user` is recorded; a test should use a true/set session authorization identity rather than mistake the function owner's `current_user` for the caller;
6. typed FKs, lifecycle state, candidate fingerprint, receipt identity and expected pointer generation/pair are rechecked under lock;
7. constraints, triggers, RLS and sealed-row guards cannot be disabled by the function;
8. errors and audit rows never include held locator text, raw payload, token, filesystem path or private legal note.

Ordinary reads and audit queries must not be wrapped in generic definer functions. If `api_v1` uses owner-backed views over release copies, those views must be `security_barrier`, positive-allowlist projections and the reader must still have no base-table privilege. Materialized/copy tables directly readable by `api_reader` are also valid if only publisher functions can populate them before closure.

## Release state, mutation and lock boundary

Both boundaries have the same closed forward state graph and separate tables/functions:

```text
draft -> candidate -> validated -> sealed
```

| Boundary | Mandatory enforcement |
|---|---|
| Draft | copied rows may be built only through publisher functions; no public/current resolution |
| Candidate closure | one transaction locks the parent, verifies expected state/version, stores a closed candidate fingerprint, and prevents later cohort/compatibility/projection/asset mutation |
| Validation | immutable PASS receipts must name and hash-bind the same candidate fingerprint; zero TRACE and zero positive rights remain legal |
| Seal | serializable transaction locks the parent; rechecks fingerprint/receipts/inventory; stores exact manifest bytes and a SHA-256 computed from those bytes; transitions `validated -> sealed` atomically |
| Post-seal | projection, membership, entry, locator allowlist, manifest and parent metadata reject `INSERT`, `UPDATE`, and `DELETE`; append-only sidecar/audit tables are the only post-seal writes |
| Pointer eligibility | target must be sealed and have an independently verified detached sidecar for the exact ID/hash; seal without sidecar is not current-eligible |

Defense in depth requires both absence of direct application DML grants and triggers/constraints that reject writes when a parent is `candidate`, `validated`, or `sealed`. The trigger family must cover child `INSERT` as well as parent/child `UPDATE` and `DELETE`. Sidecar tables are intentionally separate and append-only; they must not be caught by a rule that makes emergency takedown impossible.

### CAS and failure-audit semantics

Research CAS locks only the research channel pointer and compares the channel, expected generation, expected old release ID and expected old manifest SHA before installing one sealed, sidecar-verified replacement pair.

Visual CAS uses a fixed lock order:

1. lock/read-guard the named research-current pointer;
2. verify its expected generation and exact pair;
3. lock the visual-current pointer;
4. verify its expected generation and old exact visual pair;
5. verify the new visual version is sealed, sidecar-verified and declares the guarded research pair;
6. update only the visual pointer and append visual history.

Stale, unsealed, sidecar-invalid and incompatible attempts change neither pointer. CAS-attempt history is append-only and should include failures. An implementation that inserts a failed-attempt row and then raises an exception in the same transaction will roll the evidence back. The maintainable pattern is to return a closed structured rejection result after recording the failure, while reserving exceptions for privilege/programming faults; the negative harness then asserts `succeeded=false`, the exact reason code, unchanged pointer generations/pairs and one appended attempt event.

There is no generic function taking a boundary name. Research functions cannot write visual tables or pointers, and visual functions cannot write research projections or the research pointer.

## Post-seal health and takedown sidecars

Health and takedown sidecars are append-only events referencing typed targets with real FKs. They do not update a sealed registry entry, locator, manifest or delivery decision.

- a takedown override may express only `BLOCKED` or `CITATION_ONLY` and has highest precedence;
- endpoint health never changes rights assessment or provider-policy evaluation;
- the effective delivery mode is no more permissive than the sealed entry's mode and no more permissive than any currently effective restrictive overlay;
- a later healthy observation may remove a technical downgrade only up to the sealed permission ceiling; it cannot manufacture a provider policy, rights assessment, attribution bundle or `REMOTE_IMAGE` decision;
- rescission of a takedown does not reactivate positive delivery in an old registry; a new review and visual-registry version is required;
- every effective locator-bearing public row includes the exact visual pair and, when applied, the deterministic overlay digest.

The effective-delivery view/function must use an explicit mode ordering, not lexical enum order or `greatest`/`least` over strings. It must select the governed current health observation and all active takedown scopes deterministically.

## Public projection and serializer boundary

`api_reader` must be able to query research metadata and citation-safe fields when no compatible visual registry exists or when positive-rights coverage is zero. A public projection must expose:

- the exact research ID/hash pair;
- an atomic optional visual version/hash pair;
- an explicit compatible/unavailable state and reason;
- stable public IDs/URNs and release-safe metadata;
- an effective delivery mode and safe reason codes where a compatible entry exists;
- at most the locator fields explicitly permitted by the v1 truth table.

The view starts from copied sealed release rows, not mutable `core`, `rights`, `research`, `raw`, or `workflow` joins. Third-party pixel locators never appear in a research-release table. A public visual view may express `remote_image_url` only when the effective mode is `REMOTE_IMAGE`; otherwise that value is SQL `NULL`/unrepresentable at this boundary and the later serializer must omit the property. In v1, thumbnail and image-service URL columns are never public even for `REMOTE_IMAGE`.

Raw locator literals, held/private/tokenized endpoints, source payloads, reviewer notes, request fingerprints and unsealed rows are absent from every `api_v1` and public audit projection. `api_reader` has neither schema usage nor table privilege that could bypass the views.

## Minimum adversarial test register

| Test family | Required attempts | Required oracle |
|---|---|---|
| PUBLIC/default privileges | connect/schema/table/function access as `PUBLIC`; inspect new owner-created objects | no inherited access; default function execute absent |
| Runtime DDL/DML | create/alter/drop and base insert/update/delete as each application role | denied; objects and fingerprints unchanged |
| Caller separation | ingestor calls review/seal/CAS; reviewer rewrites raw or seals; publisher writes decisions/base release rows; auditor promotes | denied at grant/caller check |
| Definer search path | invoke each definer with hostile caller `search_path` and shadow object names | function still resolves only schema-qualified trusted objects; no attacker object called |
| Sealed research | insert/update/delete release parent, manifest, membership, asset and TRACE projection | all rejected; exact release fingerprint unchanged |
| Sealed visual | insert/update/delete registry parent, entry, locator allowlist and manifest | all rejected; exact registry fingerprint unchanged |
| Stale/unsealed CAS | stale generation, stale expected pair, unsealed target, absent/bad sidecar | structured failure; pointer unchanged; failure attempt appended |
| Cross-boundary CAS | research CAS before/after visual pointer; incompatible visual target | no cross-write; mismatch explicit; research metadata remains readable with no locator |
| Rights truth table | unknown rights + healthy pixel; viewer-only policy + healthy pixel; dead endpoint; active takedown | no unauthorized remote locator; downgrade only; takedown wins |
| Health non-escalation | improve health while rights/policy/attribution is absent or restrictive | permission ceiling unchanged; no `REMOTE_IMAGE` |
| Public locator redaction | select public views as `api_reader`; try base `rights`/`release` tables | raw/held locator unreadable; non-remote pixel value unrepresentable |
| Empty TRACE | validate/seal a transaction fixture with zero accepted semantic relations/TRACE edges | succeeds; zero is preserved, not backfilled |
| Zero positive rights | validate/seal registry fixture whose entries are all link/citation/blocked and no remote pixels | succeeds; positive-rights count remains zero |
| Fixture cleanup | count every non-registry domain table before/after test transaction | rollback leaves `PRODUCTION_ROW_COUNT=0` and `TEST_FIXTURE_RESIDUE=0` |

The harness should use `SET SESSION AUTHORIZATION` or independent role connections where available so permission results are not accidentally tested as the cluster superuser. An expected SQL error alone is insufficient: every negative test also checks unchanged data/pointer fingerprint, and stale CAS additionally checks the append-only failure attempt.

## Findings by priority

### P0

| ID | Finding | Status | Acceptance boundary |
|---|---|---|---|
| `C2-P0-01` | A public/role/seal implementation that omits explicit revoke/default-privilege closure would permit ambient PostgreSQL privileges. | OPEN UNTIL EXECUTABLE TEST | all explicit and default `PUBLIC` privileges denied; new-object probe passes |
| `C2-P0-02` | Direct publisher DML or a generic definer transition would bypass evidence-bound state and cross-boundary rules. | OPEN UNTIL EXECUTABLE TEST | publisher has execute-only mutation surface; functions are boundary-specific and search-path hardened |
| `C2-P0-03` | Sealed immutability is incomplete if child insert or candidate/validated mutation remains possible. | OPEN UNTIL EXECUTABLE TEST | parent and every copied child/manifest/asset class reject all prohibited verbs |
| `C2-P0-04` | CAS is incomplete without expected old pair+generation, row locks, sidecar verification, visual compatibility guard and unchanged-on-failure proof. | OPEN UNTIL EXECUTABLE TEST | stale/unsealed/incompatible cases fail atomically; pointers remain independent |
| `C2-P0-05` | Public redaction fails if `api_reader` can reach base locators or a non-`REMOTE_IMAGE` row can express a pixel value. | OPEN UNTIL EXECUTABLE TEST | base access denied and public-view leak count zero |
| `C2-P0-06` | Zero TRACE or zero positive rights must not be treated as validation failure. | OPEN UNTIL EXECUTABLE TEST | both zero-state seal fixtures pass and roll back |

These are not newly discovered normative conflicts. They are the executable P0 conditions Phase 2A is authorized to close.

### P1

| ID | Finding | Risk | Required treatment |
|---|---|---|---|
| `C2-P1-01` | Failed CAS audit rows disappear if the function raises after inserting them in the same transaction. | false append-only audit completeness | return a closed failure result after recording; assert both unchanged pointer and retained attempt |
| `C2-P1-02` | Initial channel provisioning can evade the “row lock” CAS rule if CAS implicitly creates a pointer row. | ambiguous first-promotion concurrency | provision a null generation-0 channel through a controlled setup function/fixture, then require every CAS to lock that row |
| `C2-P1-03` | Default PostgreSQL view semantics can be misunderstood as a grant on base tables, while `security_invoker` views would require privileges that violate reader isolation. | accidental base grant or unusable view | use owner-backed security-barrier positive views or safe copied/materialized tables; grant no base access |
| `C2-P1-04` | Using lexical enum order for delivery reduction can change meaning when labels evolve. | health/takedown may widen by implementation accident | define and test an explicit immutable mode-rank function/table |

### P2

| ID | Finding | Interpretation |
|---|---|---|
| `C2-P2-01` | Root architecture/DDL/ADR status headers still say joint verification pending or readiness false. | historical pre-joint status is superseded by the checksummed Phase 1D final receipt; do not rewrite historical receipts for Phase 2A |
| `C2-P2-02` | Role vocabulary differs between logical and physical task wording. | publish a one-row-per-role alias map in Phase 2A receipts; privileges, not names, are normative |
| `C2-P2-03` | The legacy `db` chain demonstrates readable plain SQL but not safe idempotence. | retain plain SQL readability; prefer strict fresh replay and schema hashes over silent `IF NOT EXISTS` drift |

## Recommended acceptance outcome

The physical implementation may proceed. C2 recommends `PASS` for the normative/security-release review, subject to every P0 above becoming executable PASS before the Phase 2A gate receipt claims `PHYSICAL_SCHEMA_IMPLEMENTED=true`.

```text
C2_STATUS=PASS
C2_NORMATIVE_CONFLICTS=0
C2_DDL_BLOCKING_CONFLICTS=0
C2_EXECUTABLE_P0_PENDING=6
C2_SQL_MODIFIED=false
C2_POSTGRES_STARTED_OR_CONNECTED=false
C2_PRODUCTION_DATA_IMPORTED=false
C2_DIRTY_MAIN_TOUCHED=false
```

## Actions explicitly not performed

- no SQL, migration, role, grant, function, trigger, view, fixture, manifest or historical receipt was edited by C2;
- no PostgreSQL binary, cluster, socket, port, server, client connection, database, extension or schema was started, opened, created, altered or dropped;
- no v48 JSON, SQLite, manifest, TRACE/Search shard, visual asset, frontend or protected dirty-main path was written;
- no npm, Next.js, TypeScript, browser, Docker, network, HTTP/IIIF, image, export, import, PR, merge, push or deployment command was run;
- no secret value was read or printed;
- C2 launched no background process or long-running session.

## Exit and residual-process receipt

All C2 shell commands were bounded read-only invocations and returned terminal exit states. C2 started no PostgreSQL, Node, Next, TypeScript, browser automation, Docker, generator or background process.

```text
C2_EXIT=PASS
C2_TASK_OWNED_RESIDUAL_PROCESSES=0
C2_FILES_WRITTEN=docs/audits/v49-phase2a-schema/agents/C2_SECURITY_RELEASE_REVIEW.md
```
