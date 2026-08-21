# v49 data retention

Only four byte-pinned v48 artifacts remain in the active tree. `generated/public_surfaces_prefreeze_candidate_v48.json` is the sole canonical population input; SQLite and transfer manifests are reconciliation/integrity evidence and never backfill canonical state. Their bytes and missing/null/empty semantics are frozen.

Historical raw captures, backups, queues, audits, v46/v47 outputs, and superseded summaries are removed from the active tip only after `v49-data-api-closure-20260821` was remotely verified. They remain recoverable from that immutable source tree and are not copied into an active archive directory.
