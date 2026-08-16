# Scope and process receipt

Only one task-owned PostgreSQL 16 cluster was active at any time. It used a
private Unix socket, port 55681, and `listen_addresses=''`; every attempted
runner stopped it and removed task-owned temporary data. Final process checks
found no task-owned PostgreSQL, Next, browser, npm, TypeScript compiler, or
importer process.

This phase did not run npm, Next, Chrome/Chromium, TypeScript, a full Next
build, a full v48 population replay, an extractor, or any staging scan. It
did not connect to production PostgreSQL. It did not change frontend/API/
adapter files, migrations 001–009, historical function/role/test/audit files,
the feature branch, stable branch, main, or the protected legacy main worktree.

No proposed membership was auto-accepted. The fixture contains a proposed
held-member sentinel and an accounted-but-corpus-held sentinel; neither is
eligible for public v3 membership, presentation, or search projection.
