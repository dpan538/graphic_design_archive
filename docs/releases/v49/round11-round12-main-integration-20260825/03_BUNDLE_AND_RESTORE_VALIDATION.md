# Bundle and restore validation

The retained bundle is `/private/tmp/graphic_design_archive_v49_round12_backup_20260825/graphic_design_archive_round12_preintegration.bundle` (91051946 bytes; SHA-256 `dbd5c6160ad0305eb7bfaa7932e53c8637fa7eeec9bc7484d5043e84e943695c`). `git bundle verify` reports a complete history and six heads: main, Round 12, both remote backup branches, and both annotated tags.

A bare mirror was cloned from the bundle into the exact temporary restore-test path. Commits `cc311ab0c9a74731cc1bb0158579708a8a9158fc`, `5ca999b53d9a5d18b47317817402f9e51ad26cec`, `fc11f033d2fcdbb98130879cdbd3e4a52890e5d2`, and `4bd82deba482ec2fbf8c4856080151416fb8ee83` each resolved as commit and tree objects; their parent lines matched the original graph. Restored `git fsck --full` exited zero. `RESTORE_DRILL=PASS`, `RESTORED_REQUIRED_COMMIT_COUNT=4`, and `RESTORED_MISSING_OBJECT_COUNT=0`.

The restore-test copy may be deleted after this receipt is sealed. The bundle must be retained until a later explicit backup-cleanup task.
