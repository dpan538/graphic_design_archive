# A1 — Current-leaf / supersession correctness audit

## Scope and conclusion

This was a read-only source audit of commit
`56d41d7bd55d90a7034bbcd017b0305b680e20b4`.  No PostgreSQL cluster, test
runner, or application process was started, and no implementation file was
changed by this reviewer.

**Conclusion: P0 — the v4 folder-publication predicate selects assignment
roots, not current leaves.**  The v5 correction must be completed and tested
before any performance ladder is treated as meaningful.

`provenance.canonical_assignment.supersedes_assignment_id` points from a new
assignment to the assignment it supersedes.  Therefore,
`a.supersedes_assignment_id IS NULL` identifies a root.  The deferred
constraint further requires a superseded parent to have `status='superseded'`.
For a normal two-node chain, the root is rejected by `a.status='accepted'` and
the accepted leaf is rejected by `a.supersedes_assignment_id IS NULL`; the
chain produces no public folder/type/member projection.

The v4 predicate is shared by the folder-type, folder, membership and parity
paths, so this is not an isolated display defect.

## Inspected paths

| Path | Finding |
| --- | --- |
| `database/functions/017_release_projection_snapshot_closure.sql:7-41` | Shared `research_launch_publishable_folder_assignments_v4` uses `a.supersedes_assignment_id IS NULL` at line 40.  Decision current-leaf detection already correctly uses reverse `NOT EXISTS`. |
| `database/functions/017_release_projection_snapshot_closure.sql:197-228,291-328,394-402` | The same predicate controls duplicate-effective-decision preflight, folder types, folders, members and bidirectional membership parity. |
| `database/functions/001_deferred_constraints.sql:2211-2219` | A child assignment with a non-null supersession pointer must point to a same-kind parent whose status is `superseded`; this confirms pointer direction and the P0 consequence. |
| `database/migrations/002_raw_core_provenance.sql:458-468,599-624` | Assignment and assignment-decision supersession pointers exist, but neither has a reverse supersession index.  The existing assignment index is kind/status-led, not a direct reverse-leaf access path. |
| `database/migrations/011_release_projection_snapshot_closure.sql:18-21` | The v4 index embeds `supersedes_assignment_id` behind `assignment_kind,status`; it does not replace the required reverse-pointer index for the correlated leaf predicate. |
| `database/functions/004_controlled_writes.sql:320-385` | Assignment-review decisions correctly reject superseding a noncurrent decision using reverse `NOT EXISTS`; assignment status changes are decision-driven. |
| `database/fixtures/phase2s_32_snapshot.sql:80-92` | The 32-object fixture contains only root assignments with null assignment-supersession pointers. |
| `database/fixtures/phase2s_scale_snapshot.sql:180-215` | The scale fixture likewise contains only root assignments and only unsuperseded decisions. |
| `database/tests/006_release_projection_negative_matrix.sql:55-189` | It exercises the v4 common predicate and several lifecycle/fault cases, but contains no two-level assignment chain or branch-leaf test. |

## Exact read-only commands

```text
git -C /private/tmp/graphic_design_archive_v49_release_snapshot_closure rev-parse HEAD
git -C /private/tmp/graphic_design_archive_v49_release_snapshot_closure status --porcelain=v1
git -C /private/tmp/graphic_design_archive_v49_release_snapshot_closure worktree list --porcelain
rg -n -C 5 "publishable_folder_assignments|supersedes_assignment_id|effective.*decision|supports|build_research_launch_snapshot_v4|canonical_assignment" database/functions/017_release_projection_snapshot_closure.sql database/migrations/011_release_projection_snapshot_closure.sql database/tests/006_release_projection_negative_matrix.sql database/fixtures/phase2s_scale_snapshot.sql
rg -n "CREATE INDEX .*supersed|supersedes_(assignment|decision)_id" database/migrations database/functions
nl -ba database/functions/001_deferred_constraints.sql | sed -n '2194,2248p'
nl -ba database/functions/004_controlled_writes.sql | sed -n '320,386p'
nl -ba database/migrations/002_raw_core_provenance.sql | sed -n '458,468p;599,624p'
nl -ba database/functions/017_release_projection_snapshot_closure.sql | sed -n '1,46p;190,230p;285,355p;340,420p'
rg -n -C 4 "folder_membership|canonical_assignment|assignment_review_decision|supersed" database/fixtures/phase2s_32_snapshot.sql
```

## Required forward-only v5 criteria

1. Add only forward files (`012_release_projection_snapshot_performance.sql`
   and `018_release_projection_snapshot_performance.sql`, plus grants only if
   required).  Do not edit 010/011, 016/017, 004/005, or historical evidence.
2. Define the assignment half of the publishable predicate as an accepted
   **leaf**, equivalent to:

   ```sql
   a.assignment_kind = 'folder_membership'
   AND a.status = 'accepted'
   AND NOT EXISTS (
     SELECT 1
     FROM provenance.canonical_assignment AS newer
     WHERE newer.supersedes_assignment_id = a.canonical_assignment_id
   )
   ```

   Retain the existing current-leaf decision test, `outcome='accept'`, and the
   positive `supports` evidence requirement.  Compute this relation once per
   build and reuse it for types, folders, memberships and parity.
3. Add reverse lookup indexes proven by `EXPLAIN (ANALYZE, BUFFERS, FORMAT
   JSON)`, at minimum partial indexes equivalent to:

   ```sql
   CREATE INDEX ... ON provenance.canonical_assignment (supersedes_assignment_id)
     WHERE supersedes_assignment_id IS NOT NULL;
   CREATE INDEX ... ON provenance.assignment_review_decision (supersedes_decision_id)
     WHERE supersedes_decision_id IS NOT NULL;
   ```

   Do not introduce a unique supersession constraint merely as a performance
   shortcut: the current schema does not establish that assignments or
   decisions cannot branch.
4. Add a final-tree negative/correctness fixture with a two-level assignment
   chain.  The root must be `superseded`; the accepted child points to that
   root and has its own accepted, supported current decision.  Assert that
   only the leaf's folder/object/role/ordinal is projected, that the folder
   and folder type remain available through the same shared predicate, and
   that the root is absent from the release snapshot and component digest.
5. Add a branch-leaf case.  If two current accepted leaves would publish the
   same public membership/ordinal domain, fail before copying with a named
   23514 protocol error (rather than relying on a downstream unique
   violation).  If the model intentionally permits a nonconflicting branch,
   specify and test its deterministic public semantics explicitly.
6. Test decision supersession independently: a superseded decision must not
   publish; exactly one supported current accept decision must be required.
   Keep the existing explicit `MULTIPLE_EFFECTIVE_FOLDER_DECISIONS` fail-closed
   behavior and cover it with a fixture.
7. Assert the v5 row/component/manifest/fingerprint digests change when the
   published leaf's assignment ID, role or ordinal changes, and use only
   release-owned data after build.

## Findings ledger

| Severity | Finding | Required disposition |
| --- | --- | --- |
| P0 | v4 assignment predicate selects roots (`supersedes_assignment_id IS NULL`) rather than current leaves. | Correct before profiling or performance acceptance. |
| P1 | No reverse indexes support the current-leaf anti-joins. | Add in forward-only migration, retain before/after plan evidence. |
| P1 | 32 and scale fixtures have no assignment supersession chain; the negative matrix does not prove leaf publication or branch handling. | Add final-tree fixtures and assertions before scale promotion. |
| P1 | A branch can yield multiple leaves because no uniqueness rule establishes linearity; generic snapshot uniqueness errors would be too late and ambiguous. | Define explicit fail-closed or documented deterministic branch semantics. |
| P2 | Existing test comments call the v4 relation a “common predicate” without distinguishing root vs leaf semantics. | Update v5 test/receipt terminology while preserving historical files. |

## Unresolved items

No database state or runtime plan was inspected in this audit.  The required
two-level/branch fixtures, negative proof, and index plans remain unverified
until the main task implements and runs them on the final v5 tree.
