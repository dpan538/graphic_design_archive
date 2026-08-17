# Correctness root cause and v5 closure

The v4 predicate required `a.supersedes_assignment_id IS NULL`.  Provenance
semantics point a newer assignment back to the superseded assignment, so this
selects a root, not the current leaf.  An accepted leaf therefore failed to
publish while its superseded root could not qualify either.

`018_release_projection_snapshot_performance.sql` uses the reverse anti-join
`NOT EXISTS (newer.supersedes_assignment_id = a.canonical_assignment_id)` for
both assignments and review decisions.  Migration 012 adds partial reverse
indexes without adding an invalid no-branching uniqueness rule.

Final-tree test `008_release_projection_snapshot_performance.sql` creates a
two-level chain: the superseded root is absent from the release, the accepted
leaf is present, the public object/member count remains 32, the held sentinel
is absent, and unknown internal fault text raises SQLSTATE `22023`.

`CURRENT_LEAF_NEGATIVE_FIXTURE_PASS=true`
`UNREVIEWED_FOLDER_PUBLIC_LEAK_COUNT=UNVERIFIED_AFTER_PERFORMANCE_STOP`
