# Semantic equivalence review

The corrective P1 evidence uses the repository's existing, unmodified probe
files:

```text
RIGHTS_PROBE=database/data-migrations/v48-to-v49/p1_rights_leaf_probe.sql
DELIVERY_PROBE=database/data-migrations/v48-to-v49/p1_delivery_validation_probe.sql
PRE_FIX_SCHEMA_STATE=86ba95cae9ecf12e58fcabb8170c9020e151b386
POST_FIX_IMPLEMENTATION_STATE=302ddb9683e8b3ee06c34557d10fd72a65c2afaf
POST_FIX_AUDIT_STATE=11e7b82d27b2774273d2f0d68904632246dabd37
POSTGRESQL_VERSION=16.13
```

The Phase 2A `migrations/`, `functions/`, `views/`, and `roles/` trees are
byte-identical between `86ba95c` and `11e7b82`. Replaying that unchanged tree
therefore establishes the stated pre-fix schema without importing data. The
post-fix state applies only the existing forward migration with SHA-256
`558ac2c8e8bf36166290bf588035c8822f8ff17ae481e30ebff98a8dc6715e48`.

The two SQL probes construct their own small deterministic fixtures, execute
the same four named deferred constraints, emit an `EXPLAIN (ANALYZE, BUFFERS,
WAL, SETTINGS, TIMING, SUMMARY, FORMAT JSON)`, and end with `ROLLBACK`.
Nothing reads the staging cache, imports a surface, runs the extractor, or
changes a production database.

For pre-fix roles, acceptance requires the emitted plan to retain a sequential
scan. For post-fix roles, acceptance requires the emitted plan to name
`rights_assessment_visual_reference_target_idx`. This captures the old
whole-table, opaque-predicate path and the repaired target-led indexed path
without asserting that new wall-clock timestamps or byte streams equal lost
historical logs.

The equivalence claim is deliberately narrow: P1 establishes the diagnosed
constraint/function/access-path behavior at the original fixture scales. It
does not replace Fresh A/B, the scale ladder, logical digests, or the public
boundary receipts; those retained historical receipts are not altered.
