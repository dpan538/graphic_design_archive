# Forward-only corrections

- `database/migrations/011_release_projection_snapshot_closure.sql` adds only
  the v4 protocol marker and bounded source-selection indexes.
- `database/functions/017_release_projection_snapshot_closure.sql` keeps 016
  byte-for-byte intact and adds the v4 shared publication predicate, v4
  builder/lifecycle, owner-only fault hook, and bounded hash implementation.
- `database/roles/005_release_projection_snapshot_closure_grants.sql` revokes
  publisher/PUBLIC access to both six-argument faultable builders and grants
  only the five-argument v4 production wrapper plus v4 validation/seal.

The shared predicate requires `folder_membership`, accepted and unsuperseded
assignment, one current unsuperseded accepting decision with `supports`
evidence, an accounted pinned-corpus `eligible` object, and valid publication
metadata.  Multiple effective accepting decisions raise SQLSTATE `23514` with
`MULTIPLE_EFFECTIVE_FOLDER_DECISIONS` before any copy.

TRACE v4 writes exactly `(0,0,'NO_ACCEPTED_SEMANTIC_RELATIONS')`.  Any current
canonical accepted semantic relation raises SQLSTATE `23514`
`TRACE_NONEMPTY_PROJECTION_NOT_IMPLEMENTED`; working TRACE nodes, memberships,
and legacy graph rows are not read for public availability.
