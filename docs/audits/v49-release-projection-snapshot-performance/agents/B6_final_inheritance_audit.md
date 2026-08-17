# B6 — Final-tree inheritance and boundary audit

## Scope and independence

This is a read-only Git and evidence review performed against the live
performance worktree.  I did not start PostgreSQL, a fixture, a test runner,
or an application process, and I did not edit an implementation file.  The
only file written by this reviewer is this report.

At inspection time the worktree head was
`00241aa3807a488934a4facb4dda295fb63bf5be`, on
`fix/v49-release-projection-snapshot-performance-20260817`.  The prescribed
inherited checkpoint was present at
`56d41d7bd55d90a7034bbcd017b0305b680e20b4`.

## Git ancestry and forward-only boundary

`git log 56d41d7..HEAD` showed exactly these forward commits:

| Commit | Subject |
| --- | --- |
| `8940b1d` | `feat(database): add v5 release snapshot protocol` |
| `0282ca9` | `test(database): add bounded v5 snapshot profiler` |
| `00241aa` | `perf(database): stage v5 component row digests once` |

The committed path diff from `56d41d7` to `00241aa` is limited to:

```text
database/fixtures/phase2s_scale_snapshot.sql
database/functions/018_release_projection_snapshot_performance.sql
database/migrations/012_release_projection_snapshot_performance.sql
database/roles/006_release_projection_snapshot_performance_grants.sql
database/scripts/replay.sh
database/scripts/run_phase2sp_profile.py
database/tests/008_release_projection_snapshot_performance.sql
database/tests/009_release_projection_snapshot_performance_scale.sql
```

This is a forward-only v5 shape.  In particular, the committed diff contains
no change to migrations `010`/`011`, functions `016`/`017`, roles `004`/`005`,
the inherited closure audit, frontend, or Read API.  The new migration/function
and grants use `012`, `018`, and `006`, respectively, so they do not reuse a
historical version slot.

The v5 code statically includes the reverse `NOT EXISTS` current-leaf form,
reverse supersession indexes, a five-argument publisher wrapper, and a
separately permissioned faultable internal function.  Those are implementation
claims only: this audit did not execute them.

## Inherited checkpoint verification

The source audit directory
`docs/audits/v49-release-projection-snapshot-closure/` is present in the
candidate tree and was not modified by the committed diff.  Running
`shasum -a 256 -c CHECKSUMS.sha256` in that directory returned `OK` for all
12 listed entries.  Its executive receipt continues to state
`PHASE_STATUS=PARTIAL_PERFORMANCE_CHECKPOINT`, explicitly marks the prior
32-object and six-fault results as pre-final-tree only, and records that its
8,000-object run exceeded the budget with zero checked residue.  It must be
classified as **HISTORICAL_ONLY**, not as final-tree performance or correctness
evidence.

## New-audit availability

At this review point the new additive directory existed and contained Queue-A
reports `A1_current_leaf_correctness.md` and `A2_sql_complexity.md`.  A final
executive receipt, inherited-evidence ledger, profiling measurements/plans,
scale receipts, final matrix/concurrency receipts, manifest, and checksums
were not yet available for review.  Therefore neither a self-contained new
audit package nor a final evidence gate can be endorsed at this point.

## Findings and status recommendation

| Severity | Finding | Disposition |
| --- | --- | --- |
| P0 | No prohibited-boundary modification is visible in the committed v5 diff. | Clear for bounded database verification only. |
| P1 | Final-tree execution evidence for the 32/fault/current-leaf tests, profiling ladder, 8,000 budget, full A/B, matrix, and concurrency was not available. | Do not claim any final-tree PASS from inherited evidence. |
| P1 | The additive performance audit was incomplete at review time and had no final manifest/checksum gate. | Complete only after all actual evidence exists in the candidate Git tree. |
| P2 | My `git fetch origin` attempt was denied by local worktree `FETCH_HEAD` permissions, so this reviewer could not independently refresh remote refs. | The main task must record a successful fetch/ref comparison before push/promotion decisions. |

**Recommendation:** status is `IN_PROGRESS` while bounded verification is
running.  If any required performance/correctness gate remains unrun or fails,
the only supportable result is a precise `PARTIAL_*_CHECKPOINT`; it is not
permissible to report
`RELEASE_SNAPSHOT_CORRECTNESS_AND_PERFORMANCE_CLOSED`.  A full closure requires
same-final-SHA evidence and a complete self-contained new audit package with
P0=0 and P1=0.

## Commands actually used

```text
pwd
sed -n '1,620p' <user-provided pasted task attachment>
git -C /Users/jarlgiovanni/Desktop/modern_GD_history worktree list --porcelain
git status --porcelain=v1
git log --oneline --decorate 56d41d7..HEAD
git diff --name-status 56d41d7..HEAD
git diff --name-only 56d41d7..HEAD
git diff --stat 56d41d7..HEAD
git show --stat --oneline 8940b1d 0282ca9 00241aa
git show 56d41d7:docs/audits/v49-release-projection-snapshot-closure/00_EXECUTIVE_PERFORMANCE_CHECKPOINT.md
shasum -a 256 -c docs/audits/v49-release-projection-snapshot-closure/CHECKSUMS.sha256
rg -n <v5/current-leaf/fault/grant identifiers> <new forward files>
find docs/audits/v49-release-projection-snapshot-performance -maxdepth 3 -type f
git fetch origin  # denied before network use: FETCH_HEAD permission
```
