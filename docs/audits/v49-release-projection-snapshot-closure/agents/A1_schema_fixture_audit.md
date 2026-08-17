# A1 — Schema and Fixture Closure Audit

**Mode:** read-only source audit. No PostgreSQL, npm, TypeScript, browser,
generator, or implementation command was run by this reviewer.

**Source inspected:** `dc76920e3d843c9128e73dcec7ce7f26da7cfa51`
(`fix/v49-release-projection-snapshot-20260816`). This report is additive to,
and does not alter, the prior partial-checkpoint audit package.

## Inspected paths and commands

| Path | Purpose |
| --- | --- |
| `database/migrations/010_release_projection_snapshot.sql` | v3 projection tables and constraints |
| `database/functions/016_release_projection_snapshot_v3.sql` | atomic builder, validation/seal and guards |
| `database/roles/004_release_projection_snapshot_grants.sql` | publisher/api-reader grants |
| `database/fixtures/phase2s_32_snapshot.sql` | current deterministic 32-object fixture |
| `database/tests/005_release_projection_snapshot.sql` | focused v3 test and fault probes |
| `database/scripts/run-phase2s-snapshot.sh` | fresh replay runner |
| `database/schema-manifest-v3.json` and `database/scripts/verify_schema_inventory_v3.py` | inventory coverage |
| `database/migrations/001_foundation.sql`, `002_raw_core_provenance.sql`, `003_research_rights.sql` | assignment, decision, relation and TRACE contracts |

Commands actually used were read-only: `git status --short --branch`, `git
rev-parse HEAD`, `git worktree list --porcelain`, `rg -n`, `rg --files`,
`sed -n`, `wc -l`, and `git log -1`.

## Required additive closure work

### P1 — one shared folder publication predicate

`016` currently applies three different filters:

- folder types only require an `accepted` assignment and a released object;
- folders use the same broad accepted-status existence test;
- membership additionally joins an effective `accept` decision with
  `supports` evidence.

The type/folder paths can therefore publish a shell for an
accepted-but-unreviewed assignment even though its member is not public. The
membership LATERAL query also has no explicit pre-check for multiple current,
unsuperseded accept decisions; it can fall through to a downstream duplicate
constraint rather than fail with the required named condition.

`011`/`017` should add one set-returning or otherwise shared canonical
predicate used unchanged by *all* three copy paths and their parity checks.
It must require, at minimum:

1. `assignment_kind = 'folder_membership'` and assignment status `accepted`;
2. an eligible object in the pinned corpus and in the selected/released source
   universe;
3. exactly one current, unsuperseded `accept` decision;
4. at least one `supports` decision-evidence row; and
5. valid folder metadata/type registry membership.

Before copying, a grouped check must raise SQLSTATE `23514` with
`MULTIPLE_EFFECTIVE_FOLDER_DECISIONS` when a source assignment has more than
one current unsuperseded accept decision. Proposed, rejected, superseded,
wrong-kind, accepted-but-unreviewed, decision-superseded, and no-support rows
must be excluded before type, folder, *and* member selection—not merely from
the final membership insert.

### P1 — TRACE must not consult working graph tables for public availability

The current trace availability insert in `016` counts
`research.object_trace_node` and `research.object_relation_membership`. Both
are working/canonical graph structures, so proposed or otherwise unreviewed
state can make a sealed v3 release appear TRACE-available.

The closure builder must instead write the literal release-owned honest-empty
row:

```text
trace_eligible_object_count = 0
trace_relation_count = 0
availability_reason = NO_ACCEPTED_SEMANTIC_RELATIONS
```

It must separately detect a truly accepted, current canonical semantic
relation in the selected corpus and fail closed with SQLSTATE `23514`, message
`TRACE_NONEMPTY_PROJECTION_NOT_IMPLEMENTED`. Working
`object_trace_node`, `object_relation_membership`, legacy graph facts, and
proposed/unreviewed relation data must not contribute to either count.

### P1 — separate production builder from test-only fault hook

`release.build_research_launch_snapshot_v3` is a six-argument SECURITY
DEFINER function and `004` grants all six arguments to the publisher. The
final parameter exposes fault injection to a production publishing role.

`017` should introduce a five-business-argument production wrapper and an
owner-only six-argument internal/test hook. `005` must revoke `PUBLIC` and
publisher execute on the existing six-argument v3 builder and on the new
internal function, then grant only the five-argument wrapper to the publisher.
The schema owner retains the internal hook solely for disposable test
databases. Validate the finite fault vocabulary before any mutation:

```text
after_release_objects
after_folders
after_memberships
after_component_hashes
after_build_receipt
before_candidate_transition
```

Any other fault value must return SQLSTATE `22023` and
`RESEARCH_LAUNCH_V3_UNKNOWN_FAULT_POINT` (or the equivalent v4/v3 closure
name). The current focused test probes only the first five; closure testing
must cover all six and demonstrate zero parent/projection/event/receipt/pointer
residue for every one.

### P1 — deterministic scale fixture and replayable runners are absent

The source tree has no `phase2s_scale_snapshot.sql`, no two-session
concurrency runner, and no closure runner. The current shell runner performs
two replays plus test 005 only; it does not create the 8,000 or
15,923/47,982 datasets, compare A/B digests, or run the requested lock
protocol.

The new scale fixture should:

- declare explicit column lists on every insert, including exact
  `core.entity(entity_id, entity_kind, lifecycle_state, created_at,
  withdrawn_at)`;
- query `pg_catalog` up front and fail closed if every seeded table/column is
  not present;
- derive UUIDs, timestamps, source ordinals, assignments, decisions, and
  evidence deterministically from `object_count`, `membership_count`, and
  `scale_tag`—no `gen_random_uuid()` or clock source;
- reserve a high, non-overlapping ordinal range from the 32-object fixture;
- produce exactly 24,107 memberships for 8,000 objects and 47,982 for the
  15,923-object fixture, including the specified fixed first-three-folder and
  213-object fourth-folder distribution; and
- expose normalized component-manifest, content, and candidate-fingerprint
  digests for Fresh A/B comparison without committing generated SQL or
  database files.

The Python standard-library runners need process-backed barriers based on
observed backend state, not fixed sleeps, plus the required
`statement_timeout`, `lock_timeout`, and barrier timeout bounds. They should
record actual SQLSTATE, parent/receipt/event/component residue, and digest
values in structured output.

### P2 — test harness observability

`005` uses `pg_temp.expect_error` with broad `WHEN OTHERS`; that is suitable
for a small smoke test but cannot produce the mandated negative-case ledger.
The closure negative matrix should catch only the expected category, obtain
`RETURNED_SQLSTATE`, `MESSAGE_TEXT`, and `CONSTRAINT_NAME` via `GET STACKED
DIAGNOSTICS`, and record the required before/after digest and residue columns.
The v4 inventory must include `011`, `017`, `005`, all new fixture/test/runner
files, and the replay ordering; it must not rewrite the historical v3
inventory.

## Contract decision table

| Area | Existing status | Closure requirement |
| --- | --- | --- |
| Folder type publication | Not safe: accepted-only | Shared publishable predicate |
| Folder publication | Not safe: accepted-only | Shared publishable predicate |
| Folder member publication | Partly safe; multi-decision ambiguity | Shared predicate + explicit `23514` |
| TRACE availability | Reads mutable working graph | Honest zero or named accepted-relation failure |
| Fault injection | Publisher can invoke six-arg builder | Owner-only internal hook + five-arg wrapper |
| Fault coverage | 5/6 | 6/6 and all-zero residue |
| 32-object fixture | Deterministic basic fixture | Retain; add closure matrix cases |
| Scale/concurrency | Absent | Deterministic replayable assets |
| Manifest | v3 includes 009/010 | New v4 inventory includes closure files |

## Findings

```text
P0_COUNT=0
P1_COUNT=4
P2_COUNT=1
UNRESOLVED_ITEMS=shared-folder-predicate;trace-fail-closed;fault-hook-privilege;scale-and-concurrency-assets
CONCLUSION=FORWARD_ONLY_CLOSURE_REQUIRED_BEFORE_RELEASE_PROJECTION_SNAPSHOT_CLOSED
```

No conclusion in this report treats static review as a runtime/database pass.
