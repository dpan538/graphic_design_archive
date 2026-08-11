# C4 — Security, rights, seal/CAS and public-boundary adversarial review

- Phase: v49 Phase 2A
- Review mode: independent static, read-only SQL oracle
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Branch: `refactor/v49-data-platform`
- Reviewed base HEAD: `ee393a8956ef6a6e3bfcc5613b9356323ae37c0d`
- Final reviewed snapshot: `FINAL_SQL_STABLE_5`
- Result: **PASS**
- Residual blocking findings: **0**
- SQL/database implementation performed by C4: **none**
- PostgreSQL started or connected by C4: **no**
- File written by C4: only this receipt

`PASS` means the hash-pinned SQL snapshot has no remaining C4 P0/P1 defect in
the role/grant boundary, `SECURITY DEFINER` boundary, sealed-copy guards,
research/visual CAS, rights reduction, takedown precedence, public redaction,
or legal zero-TRACE/zero-positive-rights states. It does not independently
assert the controller's cluster lifecycle, fresh replay count, schema hashes,
or final repository manifest; those belong to the primary Phase 2A receipts.

## Scope

C4 read the final SQL that defines and tests:

- cluster roles, database/schema/type/table/function/default privileges;
- caller checks and all `SECURITY DEFINER` controlled write paths;
- release parent state transitions and every release child mutation guard;
- candidate validation, validation receipts, JCS manifests, seals and detached
  verification;
- research and visual current-pointer initialization and CAS promotion;
- rights observation/assessment, provider-policy evaluation, attribution,
  delivery assessment, endpoint health and takedown as separate axes;
- sealed visual snapshots and append-only post-seal health/takedown sidecars;
- `release.effective_visual_entry` and the three `api_v1` public views;
- constraint, release/CAS, role/grant and serializable-seal negative tests;
- replay/test orchestration relevant to privilege ordering and fixture residue.

C4 did not review frontend code, import v48 data, modify frozen evidence, run a
browser, run TypeScript, start Docker, or connect to any PostgreSQL instance.

## Hash-pinned snapshot

The controller froze an exact 37-file checksum list at:

```text
CHECKSUM_LIST=/private/tmp/gda_v49_phase2a_stable5.sha256
CHECKSUM_LIST_SHA256=23d2e588c78de7a6756d5fe57117bb972dde453ba44c7b9eb3b4a9373d6f4473
CHECKSUM_ENTRY_COUNT=37
CHECKSUM_REPLAY=PASS (37/37)
```

C4 independently ran `shasum -a 256 -c` against the list. All fixtures,
migrations, functions, views, role files, tests and support scripts matched.
Critical boundary hashes were:

| File | SHA-256 |
|---|---|
| `database/functions/001_deferred_constraints.sql` | `52aedc965690785eebd0a9ec9aa921bcad23f201a65ab085b17efce3878d07f6` |
| `database/functions/002_mutation_guards.sql` | `affd3878a81c24dc3f57c4c7edd923c053a5c264e8987f801c8e17167719071b` |
| `database/functions/003_release_and_cas.sql` | `671188620b0000540ada593607d053777b1e821ffeb4673e5b07922d5748a382` |
| `database/functions/004_controlled_writes.sql` | `d12cf8a95b0cdd6e07d6a37f231385756250d4b7c00c3dd57a09f839178bd2ca` |
| `database/functions/006_normative_closure.sql` | `95a6fc5302b619459f9d4484473676563e41d79b299d830c8324da7ed49523a8` |
| `database/functions/007_release_protocol_closure.sql` | `6f7fc352411923c58f5b6f7185c0e3be4a4f4d3c5e514aa6c957938baf27cd67` |
| `database/functions/010_visual_inventory_builders.sql` | `deffe1c63574e59577eac81de8cb8d883c650dd03be6a87a678e30bc4b20adbd` |
| `database/functions/012_controlled_write_closure.sql` | `ddb4553af764fd708a0f4dcf507690474c982d3911f500e7de490b75e082567d` |
| `database/functions/014_release_copy_guards.sql` | `6c0be3796c711edcf2c75c9baf029fdc2ac4e77d28a4f612fa7846bdb0579044` |
| `database/functions/015_final_integrity_closure.sql` | `53641a6610410f66f82bf6fd8ee63389897c7ee374d668b3297d15e52b5b1923` |
| `database/migrations/008_final_integrity_closure.sql` | `db3c2748cbf4065299e271ba7dce1580fd9ac3b2b4320fdec504f04f0024caca` |
| `database/roles/002_database_grants.sql` | `4d0f78d995c131afb189ed1607008ea858d827d1b336cfef89031693ee15b823` |
| `database/views/001_api_v1.sql` | `7ad59b69177135ab3150178005cb79532925cc324062d9873f81ce6a45f566e2` |
| `database/tests/001_constraints.sql` | `e82f78aaea9c4480c0f3e015ad52075876b5072d4f86315fc09c1ce93d09b51c` |
| `database/tests/002_release_seal_cas.sql` | `e75d01d0a2c4d884e4e6064a42eedbb706bd7fea73c27595ac837c099d9f295e` |
| `database/tests/003_roles.sql` | `09f3335028d34b0474d3802e0b8c033020cbb13f6b0c4dbd4fb89a22508a3bee` |

Static source inventory at that snapshot was 9 schemas, 223 table
declarations, 222 function declarations, 335 trigger declarations, 15 view
declarations and 7 cluster-role declarations. Counts are source declarations,
not a claim about deduplicated `pg_catalog` object counts after replacements.

## Evidence commands

Representative read-only command families:

```text
git rev-parse HEAD
git branch --show-current
git status --porcelain=v1
shasum -a 256 /private/tmp/gda_v49_phase2a_stable5.sha256
shasum -a 256 -c /private/tmp/gda_v49_phase2a_stable5.sha256
wc -l database/{fixtures,migrations,functions,views,roles,tests,scripts}/*
sed -n <complete bounded ranges> <every security/release/rights SQL file>
rg -n <role, grant, SECURITY DEFINER, search_path, seal, CAS, sidecar,
       locator, takedown, review, evidence, public-view and test terms> database
python3 -c <static function-segment parser; no file writes>
git diff --check -- database docs/audits/v49-phase2a-schema
```

The static function parser measured:

```text
SECURITY_DEFINER_DECLARATIONS=83
SECURITY_DEFINER_MISSING_PINNED_SEARCH_PATH=0
SECURITY_DEFINER_DYNAMIC_EXECUTE=0
```

The executable role test independently queries `pg_proc.prosecdef` and
`proconfig`, rather than relying only on source text.

## Findings

### 1. Roles, grants and escalation boundary — PASS

- `gda_v49_phase2a_schema_owner` is `NOLOGIN`; only the migrator is its
  member. Runtime roles have no superuser, database-creation, role-creation,
  replication or RLS-bypass attributes.
- `PUBLIC` loses database, schema, table, sequence, function and project-type
  privileges. Default table, sequence, function and type privileges are also
  revoked for the schema owner before runtime use.
- Ingest writer, reviewer and publisher receive schema/type usage plus narrow
  functions and role-specific views. They receive no base-table DML.
- The publisher cannot directly write release tables; the reviewer cannot
  seal/promote; the ingestor cannot declare frozen source authority; the
  auditor cannot promote; and the API reader receives only three `api_v1`
  views with no write privilege.
- All 83 `SECURITY DEFINER` declarations pin `search_path` to `pg_catalog`.
  Controlled functions schema-qualify project objects, contain no dynamic SQL,
  and check `session_user` through the exact ingest/reviewer/publisher guards.
- The only dynamic SQL in the privilege file is owner-time `%I` quoting over a
  fixed project-schema catalog query to revoke existing type privileges. It is
  not a runtime `SECURITY DEFINER` path.

### 2. Release state, post-seal mutation and manifests — PASS

- Parent transitions are closed to `draft -> candidate -> validated -> sealed`.
  A sealed parent is immutable and only a draft parent may be deleted.
- Every research/TRACE and visual release projection family has a parent-state
  guard. An update cannot reparent a child to a different release. Manifests
  are insert-only at `validated`; validation receipts, verification receipts,
  publication histories and post-seal sidecars are append-only.
- Candidate fingerprints cover the expanded research and visual snapshots.
  JCS manifest generation is deterministic in the deliberately restricted
  value domain; fractional analysis measurements are normalized as exact
  decimal strings and traverse candidate, validation and seal tests.
- Sealing requires `serializable`, reruns deferred projection validation,
  requires the complete validation profile/receipts, computes manifest bytes
  and SHA internally, and writes typed release/seal history.
- Detached verification recomputes the immutable copied candidate fingerprint
  and exact manifest bytes. Later canonical working-state changes and permitted
  sidecars do not mutate or invalidate the sealed projection.

### 3. CAS and dual-release independence — PASS

- Research CAS row-locks the research pointer. Visual CAS locks research first
  and visual second, preventing the visual promotion from observing an
  unguarded research-current transition.
- Expected generation, release UUID and manifest use null-safe
  `IS DISTINCT FROM` comparisons. A null expected generation is explicitly
  stale. Uninitialized channels and unsealed/unverified targets fail closed.
- Successful public promotions append history in the same transaction as the
  pointer update. Failed attempts append typed failure reasons without a
  pointer mutation.
- Visual promotion requires exact compatibility with the locked research
  release UUID and manifest SHA. It updates only visual current; research
  promotion updates only research current. The tests assert stale, null and
  unsealed failures plus independent generations/history.

### 4. Rights/delivery/health/takedown separation — PASS

- Rights evidence/assessment, provider policy/version/evaluation, delivery
  assessment, endpoint-health observation and takedown remain separate tables,
  histories and snapshot axes. Attribution is an additional explicit positive
  remote-delivery prerequisite.
- A delivery assessment must link the complete set of current applicable
  rights assessments and provider-policy evaluations for its bridge. The
  effective mode cannot exceed the minimum rights, policy, attribution and
  takedown cap.
- Provider policy versions are provider- and scope-bound, evidence-bound and
  time-bounded. Evaluation cannot exceed a linked version, omit a current
  applicable version, or claim a version for an unknown/missing provider.
- Locator qualifications must belong to the same visual reference, match their
  typed role, use a matching observation, be `healthy_fresh`, not postdate the
  delivery decision and remain inside the bounded validity interval.
- Endpoint health can make an already-authorized locator unavailable or
  available; it never raises the independent rights/policy/attribution cap.
- Active takedown always wins. Visual seal and all controlled rights,
  health/takedown writers share the visual advisory lock. New takedowns and
  stricter override corrections fan out to every matching sealed entry in the
  same transaction and append exact sidecar/audit events. A correction cannot
  relax its predecessor or the event action.
- The exact negative oracle now appends fresh immutable successors: unknown
  rights plus healthy endpoint and permitted rights plus viewer-only policy
  both fail with `23514 / DELIVERY_ASSESSMENT_EXCEEDS_FAIL_CLOSED_CAP`;
  permitted rights plus an unreachable endpoint fails with
  `23514 / DELIVERY_REQUIRES_MATCHING_HEALTHY_FRESH_TYPED_LOCATOR`. These tests
  reach the delivery validator rather than merely hitting an append-only
  update guard.

### 5. Visual bridge evidence/review boundary — PASS

- Stable object-to-visual bridge identity is separate from append-only review
  history. Accepted, rejected and superseded states require exactly one current
  evidence-bound decision of the matching outcome; competing current leaves
  fail deferred validation.
- The controlled reviewer path locks the bridge, must supersede the exact
  current decision, updates state/evidence atomically and appends the exact
  `visual_bridge_review` audit subtype.
- Caller-supplied bridge review time is fail closed: null or future
  `p_decided_at` receives `23514 / FUTURE_VISUAL_BRIDGE_REVIEW_DENIED` before
  any state change. A reviewer-role negative test exercises the future case.
- Only an accepted bridge with its current accept decision and matching
  evidence may be copied. The sealed bridge row includes decision/evidence IDs
  and their hashes; validation rechecks the live source before seal, while
  detached post-seal verification relies on the immutable copied row.

### 6. Public serializer boundary — PASS

- `api_reader` cannot read raw assets, internal `rights` tables, working
  locators, release tables or `release.effective_visual_entry` directly.
- The effective visual view reads sealed-copy tables plus append-only
  health/takedown sidecars. It does not recompute public delivery from mutable
  canonical rights decisions after seal.
- Stale/expired provider policy caps to citation-only. Unhealthy or expired
  endpoints only downgrade. The most restrictive latched takedown wins.
- URL columns are structurally projected only for the effective mode:
  citation/blocked expose none; link exposes canonical record only; viewer
  exposes the viewer locator; remote image alone exposes direct-image pixels.
- `api_v1.current_object` requires a sealed, verified research release and only
  accepted/active copied objects. It requires exact research/visual UUID+SHA
  compatibility before joining a visual entry. On mismatch, research metadata
  remains available, visual fields are absent, and the mismatch is explicit.
- Zero visual permission still returns the research record. No raw, held,
  thumbnail, direct-image or service locator can leak through an API grant when
  effective delivery does not allow it.

### 7. Zero states and derived isolation — PASS

- No DDL count or state default requires a positive canonical TRACE relation,
  a visual entry, a remotely deliverable image, 15,923 rows or 20,000 rows.
- The release suite validates, seals, verifies and promotes an empty accepted
  TRACE state and a zero-positive-rights visual registry.
- TRACE/Search projections are release children built through publisher-only
  copy functions. They have no API or runtime grant that writes canonical
  research tables; a legacy projection cannot be promoted into an accepted
  semantic relation.

## P0 closure log

C4 raised the following issues while SQL was explicitly unfrozen. Each was
closed before `FINAL_SQL_STABLE_5`, then included in a fresh replay/harness:

| Issue | Closure evidence |
|---|---|
| A stricter takedown correction did not initially fan out to sealed-entry sidecars. | `rights.record_takedown_override_correction` now holds the common advisory lock, appends one matching sidecar plus typed audit event per sealed entry, and cannot relax; public citation-to-blocked redaction and exact counts pass. |
| Fractional computed-claim numerics initially fell outside the restricted JCS manifest domain. | Analysis numeric fields are canonical decimal strings; timezone-invariant fractional candidate/validation/seal coverage passes. |
| Visual bridge review accepted a caller-supplied future decision timestamp. | Null/future time is denied before insert/update; reviewer negative test passes. |
| Three required rights truth-table tests initially failed only at a generic append-only UPDATE guard. | Tests now append fresh successor histories and assert exact delivery-validator SQLSTATE/messages for unknown rights, viewer-only policy and dead endpoint. |

```text
RESIDUAL_P0=0
RESIDUAL_P1=0
```

## Controller execution evidence read, not rerun by C4

The primary controller reported for the hash-pinned snapshot:

```text
DISPOSABLE_DATABASE=gda_v49_phase2a_dev5
FRESH_REPLAY=PASS
CONSTRAINT_TESTS=PASS
ROLE_TESTS=PASS
RELEASE_TESTS=PASS
TEST_FIXTURE_RESIDUE=0
```

C4 did not connect to that cluster. C4 instead read the exact replay/test
scripts and test SQL, independently replayed the 37 file hashes, and verified
that the corrected adversarial statements target the intended deferred
validators and exact messages.

## Non-blocking executable hardening recommendations

These are P2 follow-ups, not Phase 2A blockers and not evidence of a current
authorization bypass:

1. Add a two-session `psql` harness. Session A should hold a visual seal or
   current-pointer transaction; Session B should attempt a takedown, health
   observation and competing CAS. Assert advisory/row-lock ordering, no
   deadlock, no missed sealed-entry fan-out and exactly one winning generation.
2. Add the null companion to the future visual-bridge-review test:
   call `rights.record_object_visual_reference_review_decision(..., NULL)` as
   reviewer and assert exact `23514 / FUTURE_VISUAL_BRIDGE_REVIEW_DENIED`.
3. Expand the restricted JCS vector suite with boundary safe integers,
   non-ASCII string escaping and the fixed ASCII manifest key set. Do not widen
   the accepted numeric domain unless a conforming number encoder replaces the
   current deliberate fail-closed restriction.
4. Where audit hashes are still caller-supplied metadata rather than release
   integrity inputs, add negative tests that tamper them and document the
   distinction. A later hardening pass may compute all controlled-write audit
   event digests internally for uniformity.

## Actions explicitly not performed

- No SQL, migration, role, view, fixture, test or script was edited by C4.
- No PostgreSQL process was started, connected, stopped or removed by C4.
- No v48 JSON, SQLite, TRACE shard, manifest or production row was read or
  changed by C4.
- No frontend, Next, TypeScript, browser, Docker, HTTP, import, export, PR,
  merge, deployment or force operation was performed.
- Process-table inspection was attempted only after review, but the child
  sandbox denied `ps`/`pgrep`. C4 started no process, so its task-owned process
  residue is zero; the primary controller must retain the authoritative final
  host-wide residual-process scan.

## Final C4 receipt

```text
C4_STATUS=PASS
C4_HASH_PINNED_SNAPSHOT_VERIFIED=true
C4_SECURITY_DEFINER_BOUNDARY=PASS
C4_ROLE_GRANT_BOUNDARY=PASS
C4_POST_SEAL_MUTATION_BOUNDARY=PASS
C4_CAS_AND_DUAL_RELEASE_BOUNDARY=PASS
C4_RIGHTS_FAIL_CLOSED_BOUNDARY=PASS
C4_PUBLIC_REDACTION_BOUNDARY=PASS
C4_ZERO_TRACE_ZERO_RIGHTS_BOUNDARY=PASS
C4_P0=0
C4_P1=0
C4_P2_RECOMMENDATIONS=4
C4_SQL_MODIFIED=false
C4_POSTGRES_STARTED_OR_CONNECTED=false
C4_TASK_OWNED_RESIDUAL_PROCESSES=0
RESIDUAL_BLOCKING_FINDINGS=0
```
