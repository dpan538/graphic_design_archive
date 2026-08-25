# Rollback and recovery

Recovery should create a new branch or worktree from an immutable anchor; force pushing is not the default.

1. Remote branch: fetch `backup/main-before-round11-round12-integration-20260825`, then create a recovery branch at `cc311ab0c9a74731cc1bb0158579708a8a9158fc`. The sealed Round 12 chain is independently available at `backup/round12-sealed-before-integration-20260825`.
2. Annotated tag: verify `main-before-round11-round12-integration-20260825^{}` equals `cc311ab0c9a74731cc1bb0158579708a8a9158fc` or `round12-sealed-20260825^{}` equals `fc11f033d2fcdbb98130879cdbd3e4a52890e5d2`, then branch from the selected tag.
3. Offline bundle: run `git bundle verify /private/tmp/graphic_design_archive_v49_round12_backup_20260825/graphic_design_archive_round12_preintegration.bundle`, clone it as a mirror, and create a worktree from one of the six listed heads. Verify SHA-256 `dbd5c6160ad0305eb7bfaa7932e53c8637fa7eeec9bc7484d5043e84e943695c` before recovery.

If operational policy later requires changing `main`, use a separately reviewed forward recovery commit or merge. No tag, backup branch, source branch, integration branch, or bundle is deleted in this task.
