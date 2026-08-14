# Recovery corrections and evidence reconciliation

This checkpoint records real controller-side audit and cleanup corrections. None
changed frozen inputs, Phase 2A schema files, the protected main worktree, or
the rolled-back database contents.

## Corrections

1. The first live-checkpoint capture referenced a non-existent `server.log`
   path. It was immediately corrected to the task-owned `postgresql.log` path;
   the corrected path and hash are retained in `evidence/performance-live.json`.
   No PostgreSQL state was changed by this correction.
2. The first disposable-cluster cleanup report falsely treated an empty Unix
   socket *directory* and the cleanup command itself as proof that PostgreSQL
   was still running. The exact task-owned database had already been dropped
   and the cluster had already stopped normally. The cleanup verifier was
   corrected to require the actual `.s.PGSQL.58652` socket file and to exclude
   its own process; final cleanup evidence confirms the cluster root is absent.
3. A 277 MB duplicate root-reconciliation ledger was initially placed in the
   audit package. It was moved out of Git to the verified external staging
   cache, replaced with its provenance record and deterministic sample, and
   bound by SHA-256 in `evidence/root-ledger-externalization.json`.
4. The audit-only surface-row TSV used empty trailing cells for absent
   `quarantine_id`, which is valid TSV but fails Git whitespace checks. The
   submitted audit copy deterministically renders that final empty value as
   `NONE`; the original raw staging descriptor is retained in
   `STAGING_PROVENANCE.json` and the conversion is documented in
   `18_SURFACE_ROW_LEDGER_NORMALIZATION.md`.
5. Independent verifier D9 observed a later change to the user-owned protected
   main fingerprint while its HEAD, branch, and item counts remained the same.
   This package now reports that external change explicitly. No protected-main
   restore, stash, reset, checkout, or write occurred.
6. The partial-audit renderer initially failed when asked to re-render from its
   already-archived evidence because `shutil.copyfile` rejects a source and
   destination that are the same file. The renderer now detects that exact
   resolved-path case and preserves immutable evidence bytes in place. Its
   exception path also now imports `sys` before writing a structured failure.

## Outcome

The only migration execution outcome remains `PARTIAL_PERFORMANCE_BLOCKED`:
Fresh A was cancelled at `SET CONSTRAINTS ALL IMMEDIATE`, rolled back with zero
durable project rows, and Fresh B was never started.
