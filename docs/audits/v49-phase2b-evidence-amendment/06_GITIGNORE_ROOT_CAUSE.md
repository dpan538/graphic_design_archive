# Git-ignore root cause and forward prevention

The original repository ignore file contains the broad rule:

```text
*.log
```

The old Phase 2B manifest and checksum ledger referenced eleven P1 `.log`
files, but those paths were absent from the source commit. This is consistent
with a local packaging run seeing ignored outputs and an ordinary Git staging
step omitting them. It is not repaired by changing that historical package.

This amendment adds a narrow unignore exception only for its own committed
audit package. `database/scripts/verify_audit_package_self_contained.py` then
fails closed when any manifest/checksum artifact is absent, is ignored, has a
hash/size mismatch, or is not in the Git index. The CI workflow executes that
gate on every relevant push and pull request.

The forward control is additive. It does not regenerate, edit, delete, or
re-sign the defective historical manifest, checksum ledger, or receipts.
