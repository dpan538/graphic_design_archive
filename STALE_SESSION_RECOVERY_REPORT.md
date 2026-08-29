# TRACE v49 Round 16B stale-session recovery report

Audit timestamp: 2026-08-29T12:16:04+10:00
Recovery scope: TRACE v49 Round 16B Clean Main Integration
Disposition: preserve the pre-existing dirty checkout, retire stale processes, and perform all integration work in a separate worktree.

## Authoritative identities

- Original local checkout branch: `main`
- Original local checkout HEAD: `7ef26d66b6ad671fdcc5e11bfa831699a39426bc`
- Original upstream: `origin/main`
- Refreshed `origin/main`: `8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e`
- Refreshed Round 16B research branch: `codex/trace-v49-exploration-higher-order-association-closure-round16b`
- Refreshed Round 16B research SHA: `8c3588e422a3650b634693b409a9c0b13714d58f`
- New isolated integration branch: `codex/trace-v49-round16b-evidence-bounded-main-integration`
- New isolated integration base: `8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e`

The original local `main` was zero commits ahead of and 88 commits behind `origin/main`. It was not used as the integration worktree.

## Ancestry and non-continuation proof

Both replayed historical checkpoints were tested with `git merge-base --is-ancestor` and returned success:

- `dbf0fed447c5398468714e49d5322587f29983e3` is an ancestor of `8c3588e422a3650b634693b409a9c0b13714d58f`.
- `11412d23e309a647a3a2fb0b3db4369dcdd15993` is an ancestor of `8c3588e422a3650b634693b409a9c0b13714d58f`.
- The original local HEAD, `7ef26d66b6ad671fdcc5e11bfa831699a39426bc`, is also an ancestor of the published Round 16B tip.
- The merge base of the new clean integration worktree and the research tip is exactly the requested old-main base, `8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e`.
- Before import, the new integration branch contained zero commits after the requested base.

No Checkpoint 010 or Checkpoint 011 development was continued, copied as a commit, cherry-picked, merged, amended, rebased, squashed, or recommitted.

## Original worktree inventory

- Staged paths: 0
- Unstaged tracked paths: 60 (49 modified and 11 deleted)
- Tracked diff: 20,912 insertions and 21,270 deletions
- Untracked Git-visible entries: 10,891
- Untracked apparent size: 20,045,312 KiB (19.117 GiB)
- Complete classified entries: 10,951

The dirty checkout contains a large body of archive capture, dataset, frontend, Search, and local research-lab work that predates this integration task. It was not reset, cleaned, stashed, moved, or imported.

## Preservation artifacts

The recovery artifacts are deliberately external to Git under `/private/tmp/trace_v49_round16b_stale_session_recovery_20260829/`:

| Artifact | Bytes | SHA-256 | Purpose |
| --- | ---: | --- | --- |
| `stale_session_tracked_changes.patch` | 369,105,144 | `4210dd8c4724140f033e70933c3729d132a64d0c5fbcd63256ac80137b6865ca` | Binary-safe tracked-file patch from the original local HEAD |
| `stale_session_worktree.tar.zst` | 5,268,733,387 | `a53601da40aa0dc0711d28705a9ddb0883f73df47cfaf924f6674d4cefc1c2b6` | Compressed tar of every present changed or untracked path |
| `archive_paths.zlist` | 893,049 | `2505a56f2e44a71797b25b9b0e9b55a62cb427877f033fb2c08aafe202e1d210` | NUL-safe tar input manifest |
| `worktree_status_before_preservation.zlist` | 922,193 | `5af493ad8468ca6331bb943bf022d4e8cf89e5508971f81f568b3eaa35c3f59a` | NUL-safe porcelain-v2 status snapshot |
| `stale_session_classification.json` | 6,820,393 | `193c04dc68562aea478e87f6d519fe27794f8d017ef7eb2b981b0b31a1ba9f62` | Per-path disposition source embedded in the receipt |

`zstd -t` validated the compressed tar stream, whose uncompressed size is 20,537,456,640 bytes. A full streaming tar listing succeeded with 20,360 archive members.

## Per-path classification

The machine-readable receipt classifies all 10,951 Git-visible changed paths:

- already present in the Round 16B final tree: 10;
- obsolete intermediate output for this clean integration lineage: 10,941;
- genuinely new integration work: 0.

“Obsolete intermediate output” is a release-lineage disposition only: it means that the pre-existing local path is not admissible to this clean integration import. It does not authorize deletion and does not claim that the user’s preserved work lacks value in another lineage.

Every entry has disposition `preserved_external_not_imported`. Nothing from the original dirty checkout was discarded.

## Process inventory and retirement

No Round 16B, Git, Python, npm, Next.js, test, or verification process was running. Unrelated ChatGPT and WeChat Node helpers were left untouched. The normal Homebrew PostgreSQL service at `/opt/homebrew/var/postgresql@16` was left running.

Six stale temporary PostgreSQL clusters from earlier Rounds 3b/3i/3j/3k were recorded, their approximately 1.8 GiB of data directories were retained, and each server was stopped cleanly with `pg_ctl ... stop -m fast`:

- `/private/tmp/round3i-audit-pg.nUS445`
- `/private/tmp/round3i-audit-pg.JgzD2V`
- `/private/tmp/round3j-pg16.WbxSgj/data`
- `/private/tmp/round3k-core-pg.TdHcE6/data`
- `/private/tmp/coffee-round3k-pg16.aoVtxr/data`
- `/tmp/coffee-round3b-pg16`

A post-stop process check found only the normal Homebrew PostgreSQL service in the scoped process set.

## Required result

`STALE_ROUND16B_PROCESS_CONTINUED=false`

No Search work, frontend visual design, or deployment was begun during recovery.
