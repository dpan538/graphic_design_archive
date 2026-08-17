# A2 — v4 SQL complexity, plan, and index audit

## Scope and method

This was a read-only static audit of source tree
`56d41d7bd55d90a7034bbcd017b0305b680e20b4` on branch
`fix/v49-release-projection-snapshot-performance-20260817`.  No PostgreSQL,
fixture, build, profiling command, or implementation edit was run.

Inspected paths:

- `database/functions/017_release_projection_snapshot_closure.sql`
- `database/migrations/010_release_projection_snapshot.sql`
- `database/migrations/011_release_projection_snapshot_closure.sql`
- `database/migrations/002_raw_core_provenance.sql`
- `database/migrations/003_research_rights.sql`
- `database/fixtures/phase2s_scale_snapshot.sql`
- `database/tests/007_release_projection_scale.sql`
- `docs/audits/v49-release-projection-snapshot-closure/00_EXECUTIVE_PERFORMANCE_CHECKPOINT.md`
- `docs/audits/v49-release-projection-snapshot-closure/04_PERFORMANCE_STOP_RECEIPT.txt`

Commands used: `git status --short --branch`, `git rev-parse HEAD`, `rg -n`,
and `sed -n` against the paths above.  The performance worktree was clean
before this report was written.

## Findings

### P0 — assignment supersession selects the chain root, not the current leaf

`release.research_launch_publishable_folder_assignments_v4` filters
`a.supersedes_assignment_id IS NULL` at
`database/functions/017_release_projection_snapshot_closure.sql:41-44`.
Under the stated semantics where a newer assignment points to the assignment it
supersedes, that expression selects the oldest/root assignment.  It does not
exclude an older accepted assignment that has a newer successor.  The same
predicate is duplicated in the pre-copy multiple-decision check at lines
`200-217`.

Required corrective shape is a current-leaf anti-join, for example:

```sql
NOT EXISTS (
  SELECT 1
  FROM provenance.canonical_assignment newer
  WHERE newer.supersedes_assignment_id = a.canonical_assignment_id
)
```

The v5 negative fixture must create a two-level assignment chain and prove
that only the current leaf reaches folder type, folder, and member projections.
No scale timing is meaningful until this correctness gate passes.

### P1 — the publishable-assignment relation is re-evaluated six times

The expensive relation joins membership, canonical assignment, ledger, corpus,
current effective decision, and supporting evidence (`017:12-44`).  The v4
builder invokes it independently for metadata validation (`222-226`), folder
types (`295-301`), folders (`308-313`), membership insertion (`323-328`), and
both sides of membership `EXCEPT` parity (`395-401`): six evaluations total.
The separate multiple-effective-decision guard (`200-217`) repeats a closely
related join.  This makes the release build repeatedly scan or hash the same
24,107 expected memberships at the 8,000 scale.

The v5 builder should materialize one transaction-local expected membership
set after all eligibility/current-leaf checks, then reuse that relation for
metadata, type/folder selection, insertion, dispositions, and parity.  The
materialization must retain source assignment, decision, role, and ordinal so
the public-safety predicate is not weakened.

### P1 — per-membership scalar digest functions introduce N correlated lookups

At `017:317-328`, each projected membership calls both
`research_launch_assignment_snapshot_sha_v4` and
`research_launch_decision_snapshot_sha_v4`.  Their definitions at `73-99`
each contain scalar lookups; the decision helper also aggregates evidence.
For 24,107 memberships this is 48,214 function calls and repeated hashing of
the same lookup shape.  Existing primary keys help individual lookups, but do
not remove SQL-function invocation, JSON construction, aggregate, and hash
cost per member.

Build assignment, decision, and evidence row representations from the single
expected set with joins and grouped evidence, calculate row digests set-wise,
and insert those results directly.  `EXPLAIN (ANALYZE ...)` must demonstrate
that subplan loops are not proportional to membership count.

### P1 — current component hash remains an unbounded full-release text aggregate

`research_launch_component_hash_v4` uses `string_agg(... ORDER BY ...)` into
one `text` variable for each component (`017:51-70`).  It avoids v3's giant
JSON aggregate but still constructs one complete ordered string for release
objects, presentation, membership, and search components.  This has
O(total-projection-bytes) peak aggregate state and is expressly incompatible
with a bounded digest design at the authorized large scale.

The v5 protocol should hash canonical per-row representations, form fixed
1,024-row ordered chunks, and hash a manifest that binds protocol version, row
count, chunk size, chunk ordinal, and ordered chunk digests.  Tests must prove
that reordering, deletion, duplication, and mutation change the v5 digest and
that independent fresh runs agree.

### P1 — parity uses repeated full-set `EXCEPT` work

The old checkpoint records the last observed slow context as the bidirectional
release-object `EXCEPT` parity query.  That query is at `017:378-392`; folder
membership parity repeats the expected relation twice with two more `EXCEPT`
operations at `394-402`.  `EXCEPT` is semantically sound, but each branch can
require hashing/sorting its entire input.  With the expected set not reused,
the membership parity has both full set work and predicate recomputation.

Only after before/after plans establish equivalent set semantics may v5 use a
count comparison plus indexed anti-joins.  The proof must include duplicate
handling: an anti-join/count replacement is valid only if expected membership
identity remains unique under `(folder_id, archive_object_id, membership_role)`
and `(folder_id, membership_role, member_ordinal)`.

### P1 — two reverse supersession access paths are absent from the source tree

The v4 predicate tests whether a decision has a newer decision (`017:29-31`),
but the historical index is only
`assignment_review_effective_idx(canonical_assignment_id, decided_at DESC)` in
`002_raw_core_provenance.sql:611-613`; it does not support lookup by
`supersedes_decision_id`.  The current-leaf correction likewise needs lookup
by `canonical_assignment.supersedes_assignment_id`.  Migration 011's
`canonical_assignment_launch_v4_selection_idx` begins with kind/status and is
not a replacement for a reverse pointer lookup.

Required plan-led candidates are partial indexes such as:

```sql
CREATE INDEX ... ON provenance.canonical_assignment (supersedes_assignment_id)
  WHERE supersedes_assignment_id IS NOT NULL;
CREATE INDEX ... ON provenance.assignment_review_decision (supersedes_decision_id)
  WHERE supersedes_decision_id IS NOT NULL;
```

Do not add them merely on this static finding: preserve before/after JSON plans
and require the specified 4,000-scale improvement threshold.

### P2 — source-disposition accounting rescans broad sources eight times

At `017:345-357`, four correlated counts scan `corpus_membership` and four
more join folder membership/canonical assignment/corpus membership.  This is
bounded to eight scans rather than N scans, so it is secondary, but a grouped
aggregate over the materialized expected/source relations is simpler and more
predictable.

## Required profiling measurements before remediation

The existing `database/tests/007_release_projection_scale.sql` runs only a
whole build for 8,000 or 15,923; it contains no `EXPLAIN`, phase timer, or
1,000/2,000/4,000 ladder.  Add a committed diagnostic harness that loads and
`ANALYZE`s one deterministic 8,000 fixture, derives 32/1k/2k/4k/8k selection
sets from it, and records separate plans for:

1. guard/source/policy resolution;
2. publishable assignment selection;
3. object/presentation projection;
4. folder/member projection;
5. corpus/search/TRACE projection;
6. assignment/decision/evidence hashing;
7. component hash/manifest; and
8. parity/integrity/candidate transition.

For every measured query use:

```sql
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS, SUMMARY, FORMAT JSON)
```

and retain `scale`, `phase`, query SHA-256, wall/execution milliseconds,
calls, rows, loops, planned rows, shared/temp reads/writes, WAL bytes, and
plan SHA-256.  Stop escalation if a correlated subplan loop tracks membership
count, a phase takes at least 10% of total time, `p > 1.35`, the 4,000 builder
reaches 90 seconds, or predicted 8,000 exceeds 180 seconds.

## Conclusion

Static audit result: **P0=1, P1=4, P2=1**.  The first required change is the
current-leaf predicate plus a negative two-level-chain test.  The most likely
dominant 8,000 causes are repeated expected-set construction, correlated
per-membership snapshot hashing, and unbounded aggregate component hashing;
the old checkpoint additionally records bidirectional `EXCEPT` as its last
observed active context.  These are hypotheses until the required phase-level
plans are captured.  Do not represent this report as database performance
evidence or rerun 8,000 before the profiling harness and correctness gate are
in place.
