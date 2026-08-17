# A2 — Negative Matrix and Concurrency Protocol Audit

Date: 2026-08-17  
Mode: read-only source audit; no PostgreSQL, npm, TypeScript, frontend, or browser process was started.

## Scope and inspected paths

The audit was made from the fixed partial-checkpoint source `dc76920e3d843c9128e73dcec7ce7f26da7cfa51`:

- `database/migrations/001_foundation.sql`
- `database/migrations/002_raw_core_provenance.sql`
- `database/migrations/003_research_rights.sql`
- `database/migrations/004_release_audit.sql`
- `database/migrations/010_release_projection_snapshot.sql`
- `database/functions/002_mutation_guards.sql`
- `database/functions/003_release_and_cas.sql`
- `database/functions/016_release_projection_snapshot_v3.sql`
- `database/roles/001_cluster_roles.sql`
- `database/roles/002_database_grants.sql`
- `database/roles/004_release_projection_snapshot_grants.sql`
- `database/fixtures/phase2s_32_snapshot.sql`
- `database/tests/005_release_projection_snapshot.sql`
- `database/scripts/replay.sh`

Actual read-only commands were `git worktree list --porcelain`, `git status --porcelain=v1`, `rg -n …`, and `nl -ba … | sed -n …`. No command connected to PostgreSQL.

## P0/P1/P2 conclusion

| Severity | Count | Finding |
|---|---:|---|
| P0 | 0 | The required forward-only closure can be expressed with 011/017/005 and fresh test assets. |
| P1 | 4 | Existing folder predicate divergence, working-table TRACE counting, publisher-accessible fault hook, and absent complete negative/concurrency runner require closure. |
| P2 | 1 | Fixture SQL uses several positional `INSERT`s; the new scale fixture must not repeat that pattern. |

## Exact current contracts and closure corrections

### Folder publication predicate

The source tables are:

| Contract | Source table / constraint |
|---|---|
| Assignment identity | `provenance.canonical_assignment(canonical_assignment_id)` |
| Assignment kind/status | `assignment_kind provenance.assignment_kind`, `status provenance.assertion_status`; enum contains `folder_membership` and `proposed/accepted/rejected/superseded` |
| Assignment supersession | `canonical_assignment.supersedes_assignment_id` self-FK |
| Folder member source | `provenance.assignment_folder_membership(canonical_assignment_id)` with unique `(folder_id, archive_object_id, membership_role)` and `(folder_id, membership_role, member_ordinal)` |
| Review | `provenance.assignment_review_decision`, effective test is absence of a row whose `supersedes_decision_id` points to the decision |
| Supporting evidence | `provenance.assignment_decision_evidence`, with enum role `supports` |
| Pinned corpus | `research.launch_snapshot_policy_v3.public_corpus_version_id`; `research.corpus_membership` PK `(corpus_version_id, archive_object_id)` and disposition enum `eligible/held/rejected/excluded` |
| Publication metadata | `research.folder_type_registry` and `research.folder_publication_metadata`; the latter has type/slug and type/ordinal uniqueness |

`016_release_projection_snapshot_v3.sql` currently uses only `a.status='accepted'` in the folder-type and folder `EXISTS` predicates (lines 250–261). The membership insertion (264–275) adds kind, a non-superseded `accept` decision and `supports` evidence, but does **not** require `a.supersedes_assignment_id IS NULL`, and its lateral join permits more than one effective accept decision. That means folder types/folders/members do not have one shared predicate.

011/017 should introduce one set-based publishable-assignment relation or helper used identically by all three inserts and both `EXCEPT` parity checks. It must require all of:

```sql
a.assignment_kind = 'folder_membership'
AND a.status = 'accepted'
AND a.supersedes_assignment_id IS NULL
AND cm.corpus_version_id = policy.public_corpus_version_id
AND cm.disposition = 'eligible'
AND exactly_one_current_unsuperseded_accept_decision
AND that decision has EXISTS supports evidence
```

Before copying, group the effective decisions by `canonical_assignment_id`. A count other than one must raise SQLSTATE `23514`, message `MULTIPLE_EFFECTIVE_FOLDER_DECISIONS` for greater-than-one; no later unique-constraint (`23505`) may be the control path. A zero decision is simply non-publishable; accepted-but-unreviewed must therefore not publish type, folder, or member. The same candidate relation must also enforce a current assignment (`supersedes_assignment_id IS NULL`) and reject a current accepted assignment whose source folder or object is otherwise missing through normal FK/metadata gates.

### TRACE availability

`016` lines 303–309 currently derive public availability from mutable working `research.object_trace_node` and `research.object_relation_membership`. This violates the closure requirement even when the result happens to be zero.

The v3 launch snapshot currently has no release-owned non-empty relation component. 017 must instead:

1. detect `research.semantic_relation.status = 'accepted'` in the canonical input relevant to the candidate and fail before any copy with SQLSTATE `23514`, message `TRACE_NONEMPTY_PROJECTION_NOT_IMPLEMENTED`;
2. insert exactly one release-owned `research_trace_availability_projection_v3` row with `0`, `0`, and `NO_ACCEPTED_SEMANTIC_RELATIONS` only when there is no accepted semantic relation;
3. never examine `object_trace_node`, `object_relation_membership`, legacy graph tables, proposed relation state, or unreviewed relation decisions for a public count.

The required negative tests should add proposed/unreviewed relation and working node/membership sentinels, then prove both public counts remain zero; an accepted semantic relation must hit the named fail-closed exception and leave no parent/child residue.

### Fault hook and grants

The current public builder identity is:

```sql
release.build_research_launch_snapshot_v3(
  uuid, uuid, uuid, uuid, core.sha256_hex, text DEFAULT NULL)
```

It is `SECURITY DEFINER` and role 004 grants that six-argument function to `gda_v49_phase2a_publisher`. Its accepted values are currently only checked by equality branches, so an unknown string silently succeeds. The existing five test fault points omit `before_candidate_transition`.

005 must revoke `EXECUTE` from both `PUBLIC` and `gda_v49_phase2a_publisher` on the six-argument signature. Production should expose an exact five-business-argument wrapper, while a separately named six-argument test-only entrypoint is executable only by the schema owner in a disposable cluster. The test function must validate the exact closed set before the builder has written any row:

```text
after_release_objects
after_folders
after_memberships
after_component_hashes
after_build_receipt
before_candidate_transition
```

Any other non-null value must return `22023` / `RESEARCH_LAUNCH_V3_UNKNOWN_FAULT_POINT`. The negative matrix must prove a publisher receives `42501` for every test-only fault entrypoint and cannot obtain a fault by invoking the five-argument production wrapper.

### Projection and audit residue inventory

For every fault case, use the release UUID as a parameter and verify zero rows in the following 18 projection/audit/receipt tables, plus the parent and pointer/seal state:

1. `release.research_release_object`
2. `release.research_folder_type_projection_v3`
3. `release.research_folder_projection_v3`
4. `release.research_surface_presentation_projection_v3`
5. `release.research_surface_credit_projection_v3`
6. `release.research_surface_citation_projection_v3`
7. `release.research_folder_membership_projection_v3`
8. `release.research_search_document_projection_v3`
9. `release.research_corpus_summary_projection_v3`
10. `release.research_trace_availability_projection_v3`
11. `release.research_launch_component_manifest_v3`
12. `release.research_launch_source_disposition_count_v3`
13. `release.research_launch_build_receipt_v3`
14. `release.research_launch_validation_v3`
15. `release.research_launch_manifest_v3`
16. `release.research_release_manifest`
17. `audit.research_release_event`
18. `audit.research_seal_event`

Also assert: no `release.research_release` parent; no row in `release.research_current_pointer` naming the failed release; and no seal event / manifest of that release. All currently have release FK paths except the current pointer, so the explicit pointer check is still necessary evidence.

## Required negative-matrix harness

`database/tests/006_release_projection_negative_matrix.sql` should use a ledger relation with exactly:

```text
case_id
expected_sqlstate
actual_sqlstate
expected_message_or_constraint
actual_message
actual_constraint
pre_state_digest
post_state_digest
residue_count
pass
```

The harness should derive `pre_state_digest` and `post_state_digest` from a stable ordered JSON array over the 18 tables, parent, pointer, and seal state. Each case must execute in a nested PL/pgSQL exception block (savepoint), record `RETURNED_SQLSTATE`, `MESSAGE_TEXT`, and `CONSTRAINT_NAME` through `GET STACKED DIAGNOSTICS`, and compare all three expected values explicitly. A catch-all may record diagnostics but never constitutes a pass by itself. The base fixture and every intentional test mutation must be deterministic.

Recommended case groups, minimum coverage:

| Group | Minimum cases / expected behavior |
|---|---|
| Entry gate | nonpublisher `42501`; non-serializable `25001`; unknown fault `22023`; absent batch/policy/allowlist/metadata `23514` named messages |
| Metadata / FK | invalid type, slug, ordinal; duplicate slug and ordinal; missing folder/object; cross-release folder/object/presentation composite FKs |
| Membership shape | duplicate member key; duplicate role/ordinal; bad role; negative ordinal; nonaccepted status |
| Surface missingness | all seven `(value IS NULL) = (missingness='missing')` constraints in both directions: 14 independent cases |
| Projection data | invalid citation route; blank search document; invalid component/disposition; manifest hash mismatch |
| Corpus / assignment exclusion | held/rejected/excluded corpus; proposed/rejected/superseded/wrong-kind/unreviewed/no-support/superseded-decision assignment all publish no folder type/folder/member |
| Decision ambiguity | two current unsuperseded supported accepts yields `23514 MULTIPLE_EFFECTIVE_FOLDER_DECISIONS` before any row copy |
| TRACE | proposed/unreviewed relation leaves `0/0`; accepted relation raises named `23514` with zero residue |
| Lifecycle / tamper | second builder; builder from candidate/validated/sealed; missing or tampered component/receipt/fingerprint/manifest |
| Guards | 12 guarded projection tables × INSERT/UPDATE/DELETE = exactly 36 `55000 RESEARCH_LAUNCH_V3_POST_BUILD_MUTATION_DENIED` cases |
| Privileges | publisher legacy close/validate/seal denial, publisher test-fault denial, api reader base read/write denial, `PUBLIC` privilege count zero |
| Atomicity | every one of the six listed fault points returns the expected injected error and leaves the complete residue inventory at zero |

The current 005 helper accepts a list of SQLSTATE values and discards message/constraint diagnostics. It cannot be reused unchanged as proof for this matrix.

## Two-session standard-library concurrency protocol

Implement `database/scripts/run_phase2s_concurrency.py` using only `subprocess`, `selectors`, `json`, `time`, and `pathlib` from the standard library. Use two persistent `psql -X -Atq -v ON_ERROR_STOP=1` processes over the task-owned Unix socket, with stdin pipes held open. Emit machine-readable marker rows, capture each backend PID through `SELECT pg_backend_pid()`, and have the runner enforce:

```text
statement_timeout <= 120s
lock_timeout <= 30s
barrier_timeout <= 15s
whole concurrency run <= 5m
```

Do not use a fixed `sleep` as a barrier. A monitor connection can inspect `pg_stat_activity` / `pg_locks` by the captured B PID until the requested advisory lock wait is observed, with an absolute 15 second deadline.

### Same-release two-builder case

1. Seed and commit a deterministic fixture plus exactly one fresh draft release.
2. Session A: `BEGIN ISOLATION LEVEL SERIALIZABLE`; set the publisher authorization and timeouts; acquire `pg_advisory_xact_lock(hashtextextended(release_id::text, 49023))`; print `A_LOCKED`.
3. Session B: begin `SERIALIZABLE` before A commits, invoke the five-argument production builder for the same release with its own event UUID, and print either `B_DONE` or a structured SQLSTATE marker.
4. The Python monitor must observe B waiting on the same advisory lock (`pg_locks.granted=false` for B) before allowing A to invoke the builder and `COMMIT`.
5. B must complete as `40001`, then issue `ROLLBACK`; it must not silently retry.
6. Verify A `00000`; one v3 build receipt; one draft→candidate audit event; ten component rows; one parent; zero B event/receipt/manifests; and no projection residue attributable to B.

The lock key above is the exact key used by 016 line 190. B has to start its serializable transaction before A commits; otherwise it would only observe the non-draft parent and may return `55000`, which would not prove the requested serialization behavior.

### Canonical-writer overlap case

1. Seed and commit a second fresh draft release.
2. Session A begins `SERIALIZABLE`, authenticates as publisher, and first reads a stable, sorted canonical vector of all publishable `(folder_id, archive_object_id, membership_role, member_ordinal, assignment_id, effective_decision_id)` tuples. Print `A_SNAPSHOT_FIXED` with its digest.
3. Session B, as schema-owner fixture writer, changes exactly one accepted membership ordinal to an otherwise unused ordinal and commits. Do not use a guessed sleep: release B only after A’s marker is received; wait for B’s commit marker before asking A to build.
4. A invokes the production builder and commits, or returns `40001` and rolls back.
5. If A succeeds, query the release-owned member vector and require it exactly match A’s pre-B vector, with no mixture. If A receives `40001`, require zero parent/18-table/pointer/seal residue. Any other SQLSTATE, a mixed vector, or more than one receipt fails.

The mutation needs to retain the underlying table uniqueness — for the fixture, move ordinal `0` to an unused `8`, not to an ordinal already in the same folder/role. The runner must write a JSON transcript with markers, PID/PGID, backend PIDs, observed advisory wait, SQLSTATEs, source/vector digests, elapsed times, and final residue counts. Do not include credentials or DSN secrets.

## Required fresh/scale harness properties

The closure runner should create a single disposable PostgreSQL 16 cluster, replay the final tree twice, and use a named Unix socket plus a non-5432 port. The new scale fixture must use explicit column lists and validate every seeded catalog column before writing. It must seed deterministic UUIDs/timestamps/ordinals/evidence and an ID range disjoint from the 32 fixture; do not use `gen_random_uuid()`, `clock_timestamp()`, or positional inserts. `core.entity` specifically needs:

```text
entity_id, entity_kind, lifecycle_state, created_at, withdrawn_at
```

The A/B scale result JSON should include elapsed total/build time, counts, component-manifest SHA, candidate fingerprint, content SHA, result SQLSTATE, schema hash, and zero-residue result. A/B parity must compare the logical output fields only, excluding diagnostics such as PID, txid, and timestamps.

## Unresolved items / acceptance implication

No implementation was changed by this audit. The four P1 findings are expected to be closed only when new 011/017/005 and the requested deterministic fixture/test/runners pass on the final tree. Until the six-point fault capability, full negative ledger, two-session results, and 8,000/15,923 scale evidence exist, this audit alone does **not** authorize `RELEASE_PROJECTION_SNAPSHOT_CLOSED`.
