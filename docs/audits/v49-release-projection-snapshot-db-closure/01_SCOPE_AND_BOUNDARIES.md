# Scope and boundaries

- Canonical population input: byte-pinned v48 Candidate JSON only.
- SQLite, Search, TRACE, manifests, and staging ledgers: reconciliation/integrity evidence only.
- v48, sealed releases, historical migrations, and predecessor audit package: read-only.
- Successor worktree only; no rebase, force-push, stable/main mutation, PR, merge, deployment, staging, or production access.
- One task-owned PostgreSQL cluster, one controller/importer/builder process outside the dedicated session-level concurrency harness.
- API phase is limited to the existing server-side GET/HEAD/OPTIONS contract. UI and browser work are excluded.

Historical migration hashes and final path checks are in `raw/final/historical-boundary.sha256` and `raw/final/git-boundary.txt`.
