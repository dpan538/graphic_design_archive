# Rollback and recovery

## Immutable anchor

The annotated tag `main-pre-v49-research-integration-20260825` was created, pushed, and remotely peeled to `592c765d0af5bf15b1666784dce784ac8e22624d` before the main update. Its tag message records the incoming tip `47978c519c3c7141690e3894315a1ef1b7a403db`, expected count 72, date, reason, and the prohibition on history rewriting.

## Recovery principle

The main update is a non-force fast-forward. If a later review finds a defect, do not rewrite or force-move `main`, and do not move either integration tag. Create a new recovery branch from the appropriate immutable anchor and use a new, reviewed forward commit or revert according to the incident decision.

## Read-only diagnosis

1. Fetch `origin/main` and all tags.
2. Verify the pre-tag object and peeled commit independently.
3. Compare `592c765d0af5bf15b1666784dce784ac8e22624d..origin/main` and preserve the 72 incoming identities.
4. Inspect the post-integration tag `v49-research-main-integration-20260825` for the containing integration SHA and validation statement.
5. Do not delete research/recovery branches during diagnosis.

No rollback action is executed by this package.
