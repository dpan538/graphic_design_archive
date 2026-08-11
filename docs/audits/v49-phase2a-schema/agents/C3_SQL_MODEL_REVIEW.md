# C3 — Final physical SQL model and release-copy review

- Phase: v49 Phase 2A
- Review mode: independent static, read-only physical-model review
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Branch: `refactor/v49-data-platform`
- Reviewed base HEAD: `ee393a8956ef6a6e3bfcc5613b9356323ae37c0d`
- Final reviewed snapshot: `FINAL_SQL_STABLE_5`
- Result: **PASS**
- Residual P0: **0**
- Residual P1: **0**
- SQL or database implementation performed by C3: **none**
- PostgreSQL started or connected by C3: **no**
- File written by C3: only this receipt

`PASS` means the exact hash-pinned SQL snapshot has no remaining C3 P0/P1
defect in physical FK shape, deferred identity/subtype/cardinality invariants,
assertion/evidence/relation/TRACE separation, visual-rights cardinality, or
research/visual release-copy and seal boundaries. It does not independently
assert the controller's cluster lifecycle, replay count, normalized schema
hash, or final audit manifest.

## Scope

C3 completely read the final migrations, functions, views, role/grant SQL,
fixtures, test SQL and replay support files under `database/`, plus the locked
architecture/data/migration/acceptance documents, DDL decision pack, all ADRs,
the Phase 1C authority/research gate, Phase 1D rights/machine and joint gate
receipts, and the Phase 2A C1/C2 review receipts. The review concentrated on:

- ingest lineage, immutable raw authority and held/rejected preservation;
- `core.entity` exact subtype identity and typed legacy-resolution history;
- the thirteen canonical-assignment shapes and typed FK targets;
- assertion, claim, relation, decision and evidence cardinalities;
- accepted-relation fail-closed validation and TRACE projection isolation;
- research corpus/release membership and immutable copied projections;
- visual bridge review identity, five independent rights/delivery axes and
  evidence-bound snapshot cardinality;
- independently sealed research and visual releases, copied manifests,
  mutation guards, CAS/current-pointer separation and public-view redaction;
- least-privilege grants and the executable negative-test oracle.

C3 did not review frontend implementation, import any v48 data, run a browser,
run TypeScript, start Docker, connect to PostgreSQL, or execute the SQL harness.

## Hash-pinned snapshot

The controller froze the reviewed 37-file snapshot at:

```text
CHECKSUM_LIST=/private/tmp/gda_v49_phase2a_stable5.sha256
CHECKSUM_LIST_SHA256=23d2e588c78de7a6756d5fe57117bb972dde453ba44c7b9eb3b4a9373d6f4473
CHECKSUM_ENTRY_COUNT=37
C3_CHECKSUM_REPLAY=PASS (37/37)
```

C3 independently reran `shasum -a 256 -c` after the final freeze. Every
migration, function, view, role file, fixture, test and support script matched.
Boundary-critical hashes include:

| File | SHA-256 |
|---|---|
| `database/migrations/001_foundation.sql` | `5a855f12b56325078cfe45d9525f4eef1feed707ac742c553ef20677546b127b` |
| `database/migrations/002_raw_core_provenance.sql` | `c1acc5cc08efe4b5f34daee962e5c74111e2e77813ff80f5a886359c444db052` |
| `database/migrations/003_research_rights.sql` | `50351e03db8f916b60565264608c5e0028fc636f2fb7a00bf6e85793d41b1452` |
| `database/migrations/004_release_audit.sql` | `5895d75594f337e85885e0f445e7918438e3891aa13baf4d481dda3134c7312c` |
| `database/migrations/005_normative_closure.sql` | `16f7450bb384caa865d20c3b2ecd3dea388df8cc9a159ebcf4b0cd48f97c7496` |
| `database/migrations/006_epistemic_trace_closure.sql` | `6722b1911dd289ed562bb4db163d442344c3bab64689653449cf4dbdd87c41ed` |
| `database/migrations/007_release_copy_integrity.sql` | `6f8395d69f28337d314428e111e943139e605a64ae33ebe6812437f39a2c0457` |
| `database/migrations/008_final_integrity_closure.sql` | `db3c2748cbf4065299e271ba7dce1580fd9ac3b2b4320fdec504f04f0024caca` |
| `database/functions/001_deferred_constraints.sql` | `52aedc965690785eebd0a9ec9aa921bcad23f201a65ab085b17efce3878d07f6` |
| `database/functions/003_release_and_cas.sql` | `671188620b0000540ada593607d053777b1e821ffeb4673e5b07922d5748a382` |
| `database/functions/006_normative_closure.sql` | `95a6fc5302b619459f9d4484473676563e41d79b299d830c8324da7ed49523a8` |
| `database/functions/007_release_protocol_closure.sql` | `6f7fc352411923c58f5b6f7185c0e3be4a4f4d3c5e514aa6c957938baf27cd67` |
| `database/functions/010_visual_inventory_builders.sql` | `deffe1c63574e59577eac81de8cb8d883c650dd03be6a87a678e30bc4b20adbd` |
| `database/functions/012_controlled_write_closure.sql` | `ddb4553af764fd708a0f4dcf507690474c982d3911f500e7de490b75e082567d` |
| `database/functions/014_release_copy_guards.sql` | `6c0be3796c711edcf2c75c9baf029fdc2ac4e77d28a4f612fa7846bdb0579044` |
| `database/functions/015_final_integrity_closure.sql` | `53641a6610410f66f82bf6fd8ee63389897c7ee374d668b3297d15e52b5b1923` |
| `database/roles/002_database_grants.sql` | `4d0f78d995c131afb189ed1607008ea858d827d1b336cfef89031693ee15b823` |
| `database/views/001_api_v1.sql` | `7ad59b69177135ab3150178005cb79532925cc324062d9873f81ce6a45f566e2` |
| `database/tests/001_constraints.sql` | `e82f78aaea9c4480c0f3e015ad52075876b5072d4f86315fc09c1ce93d09b51c` |
| `database/tests/002_release_seal_cas.sql` | `e75d01d0a2c4d884e4e6064a42eedbb706bd7fea73c27595ac837c099d9f295e` |
| `database/tests/003_roles.sql` | `09f3335028d34b0474d3802e0b8c033020cbb13f6b0c4dbd4fb89a22508a3bee` |
| `database/tests/004_serializable_seal.sql` | `4402bc9f2a874fcc59501a14b42d82cf5be1401e295514902972c7d28885b58b` |

## Evidence commands

Representative read-only commands were:

```text
shasum -a 256 /private/tmp/gda_v49_phase2a_stable5.sha256
shasum -a 256 -c /private/tmp/gda_v49_phase2a_stable5.sha256
git status --short --branch
wc -l database/functions/007_release_protocol_closure.sql
sed -n <complete bounded ranges> <all database SQL/test/support files>
rg -n <CREATE TABLE, FK, constraint trigger, copy guard, release validator,
       evidence, relation, TRACE, rights, seal, CAS and grant terms> database
rg -n 'ON DELETE CASCADE|target_type|target_id' database
rg -n 'GRANT (ALL|INSERT|UPDATE|DELETE|TRUNCATE|REFERENCES|TRIGGER) ON'
  database/roles/002_database_grants.sql
perl -0777 -ne <static SECURITY DEFINER search_path scan> database/**/*.sql
git diff --check
```

Measured static results relevant to this review:

```text
FROZEN_FILE_HASH_MATCH=37/37
RUNTIME_ROLE_DIRECT_BASE_TABLE_DML_GRANTS=0
ON_DELETE_CASCADE_IN_DOMAIN_SQL=0
ARBITRARY_CANONICAL_TARGET_TYPE_PLUS_TARGET_ID_COLUMNS=0
SECURITY_DEFINER_WITHOUT_FIXED_PG_CATALOG_HEADER=0
RESIDUAL_P0=0
RESIDUAL_P1=0
```

The `p_kind + p_target_id` parameters in `audit.record_decision_event` are not
an unconstrained canonical polymorphic row: the closed enum dispatches into one
of the FK-bearing typed audit subtype tables, and deferred exact-subtype
constraints require exactly one matching child.

## Findings

### 1. Identity, subtype and source cardinality — PASS

- `core.entity` has one closed kind and deferred triggers require exactly one
  matching subtype row. Subtype PKs are real FKs to the supertype.
- The generic legacy registry is namespace-typed; every resolution has a
  closed target shape, append-only supersession, one effective leaf and typed
  split successors. It can represent primary/alias/redirect/merge/split/
  withdrawal without an arbitrary target string.
- Raw surface accounting retains the exact canonical source asset, record,
  ordinal, lexical fingerprint and import disposition. Held/rejected rows must
  remain reciprocally accounted; no delimiter-derived object creation exists.
- Object/source, folder/member, object/TRACE-node and object/visual-reference
  relations use typed bridge tables and declared natural keys. Canonical parent
  deletion uses `RESTRICT`; domain SQL contains no `ON DELETE CASCADE`.

### 2. Assertions, assignments, claims and evidence — PASS

- Assertion subject/value shapes are closed by typed child tables and deferred
  exact-shape constraints. Accepted assertions require supporting evidence and
  one current accepting decision with decision evidence.
- All thirteen canonical-assignment subtypes are FK-bearing and exact-shape
  checked. Accepted assignments must be supported by an accepted assertion and
  a current evidence-bound decision; orthogonal publication/workflow states do
  not silently promote them.
- Claim revisions, review decisions, evidence and analysis runs are separate,
  append-only identities. Computed claims pin method, parameters, input release
  UUID+manifest SHA, corpus policy, score/threshold and output hashes.
- Release claim/evidence and analysis-run rows copy the source values and
  deterministic snapshot hashes. Source-copy triggers reject mismatches before
  candidate closure.

### 3. Relations and TRACE — PASS

- Semantic endpoints are closed typed rows with real `core.entity` FKs.
  Relation type, endpoint kind, active registry state, evidence and current
  review/claim support are deferred acceptance invariants.
- Unknown or inactive relation types cannot be accepted. Legacy projection
  origin cannot be accepted, implicit transitivity is fixed false, and
  automatic influence inference is fixed false.
- `research.relation_claim` identity is revision-pinned. A release relation
  must reference an already copied accepted claim revision or the current
  evidence-bearing curator accept decision; copied evidence is source-hash
  guarded.
- TRACE nodes, edges, trees, branches, placements and memberships are release
  projections. Edges require copied typed endpoint nodes and a copied accepted
  semantic relation; deterministic generation keys are revalidated. No derived
  projection path writes canonical relations.
- The validators and release tests support an accepted-relation/TRACE-edge
  count of zero without weakening any acceptance rule.

### 4. Research and visual release copies — PASS

- Every release projection family is draft-only mutable, cannot be reparented,
  participates in the candidate fingerprint, and is immutable after candidate
  closure. Manifest insertion is restricted to a validated parent; sealed
  parent, children and manifest are protected from insert/update/delete.
- Research lineage requires the five authority roles, exact source hashes,
  projection/registry/corpus/count snapshots, deterministic asset inventory,
  claim/evidence/relation checks, TRACE topology and exact legacy split sets.
- Visual releases are composite-FK pinned to a sealed research UUID+manifest
  pair. Provider/reference/bridge, rights observation/assessment, policy
  version/evaluation, delivery, attribution, typed locator/health and takedown
  rows are copied into distinct snapshot families.
- Accepted visual bridges require a current evidence-bound accept decision.
  Copy and validation pin bridge/evidence/decision hashes; null or future review
  time fails closed.
- Visual copy validation proves exact governing rights/policy link sets,
  current leaf histories, typed healthy locators, delivery caps and active
  takedown coverage. Rights, provider policy, delivery, endpoint health and
  takedown remain independent axes; health cannot elevate permission.
- Research and visual seals use independent manifests and current pointers.
  Sealing reruns validation in a serializable transaction; visual sealing and
  takedown writes share the advisory lock. CAS uses row locks, exact UUID+SHA
  pairs, null-safe expected values and independent publication history.

### 5. Public and privilege boundary — PASS

- Runtime roles receive no direct base-table DML. Publisher construction,
  validation, seal and promotion occur only through fixed-search-path
  controlled functions; reviewer and ingestor capabilities remain disjoint.
- `PUBLIC` privileges and schema-owner default privileges are revoked. The API
  reader has only the approved `api_v1` views and no raw/internal rights or
  locator access.
- Public visual output is built from sealed copies plus append-only restrictive
  sidecars. Pixel URL is structurally present only for effective
  `remote_image`; mismatch, missing registry, zero positive rights and held/
  citation states preserve research metadata while omitting disallowed URLs.

## Prior P0 closure ledger

C3 reviewed each earlier issue against the final frozen source and found it
closed before `FINAL_SQL_STABLE_5`:

| Earlier defect | Final closure |
|---|---|
| Partial legacy split copies could pass. | Copy helper and validator require the exact ordered successor set, all or nothing. |
| Relation/claim support was not revision-pinned. | `research.relation_claim` primary identity includes `claim_revision_id`; release builder and tests use the exact revision. |
| Accepted visual bridges lacked evidence-bound append-only review identity. | Typed review history, one-current-leaf invariant, snapshot hashes and audit subtype are enforced. |
| Future/null visual bridge review time could pass. | Controlled reviewer function rejects both before mutation; negative coverage pins the error. |
| Provider policy scope/source evidence and copied link sets were incomplete. | Typed scope/evidence FKs, exact evaluation-version sets and release validation are present. |
| Visual release snapshot fan-out could omit governing rows. | Builder and bidirectional set-difference validators cover assessments, observations, policy versions/evaluations and delivery links. |
| Takedown correction did not cover every matching sealed entry. | One advisory-lock transaction writes every matching sidecar plus typed audit and forbids relaxation. |
| Fractional computed values were outside the restricted JCS domain. | Analysis numerics enter manifests as canonical decimal strings; JCS still rejects unsafe raw numbers. |
| Required rights truth-table tests previously stopped at append-only guards. | Stable5 appends successor histories and reaches the exact fail-closed cap/health validators. |

```text
RESIDUAL_P0=0
RESIDUAL_P1=0
```

## Controller execution evidence read, not rerun by C3

The primary controller reported for the same hash-pinned snapshot:

```text
DISPOSABLE_DATABASE=gda_v49_phase2a_dev5
FRESH_REPLAY=PASS
CONSTRAINT_TESTS=PASS
ROLE_TESTS=PASS
RELEASE_TESTS=PASS
TEST_FIXTURE_RESIDUE=0
```

C3 did not connect to the cluster. C3 read the fixture and all four test files,
verified that the adversarial cases reach the intended constraint/permission/
seal validators, and independently verified all 37 file hashes.

## Actions explicitly not performed

- No migration, function, view, role, fixture, test or support script was
  edited by C3.
- No PostgreSQL instance was started, connected, stopped or removed by C3.
- No v48 JSON, SQLite, TRACE shard, manifest or production row was imported or
  modified by C3.
- No frontend, Next, TypeScript, browser, Docker, HTTP, ORM, API, PR, merge,
  deployment, force operation or dirty-main action was performed.
- Host process-table inspection was attempted after review, but the child
  sandbox denied `ps` and `pgrep`. C3 launched no background or long-running
  process, so C3-owned residue is zero; the primary controller retains the
  authoritative final host-wide residual-process scan.

## Final C3 receipt

```text
C3_STATUS=PASS
C3_HASH_PINNED_SNAPSHOT_VERIFIED=true
C3_IDENTITY_SUBTYPE_CARDINALITY=PASS
C3_ASSERTION_ASSIGNMENT_EVIDENCE=PASS
C3_RELATION_TRACE_FAIL_CLOSED=PASS
C3_RIGHTS_VISUAL_CARDINALITY=PASS
C3_RELEASE_COPY_INTEGRITY=PASS
C3_SEAL_CAS_BOUNDARY=PASS
C3_ROLE_GRANT_BOUNDARY=PASS
C3_PUBLIC_REDACTION_BOUNDARY=PASS
C3_ZERO_TRACE_ZERO_RIGHTS_STATE=PASS
C3_P0=0
C3_P1=0
C3_SQL_MODIFIED=false
C3_POSTGRES_STARTED_OR_CONNECTED=false
C3_TASK_OWNED_RESIDUAL_PROCESSES=0
RESIDUAL_BLOCKING_FINDINGS=0
```
