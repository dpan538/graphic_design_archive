# Forward-only migrations

Discovered next unused ordinals were migration 013, function 019, and—after the v5 API verification gap was reproduced—roles 007.

- `database/migrations/013_release_projection_snapshot_db_closure.sql`: drops one proven duplicate v49-only candidate index.
- `database/functions/019_release_projection_snapshot_db_closure.sql`: fixes full-tuple parity, current-leaf validation gaps, deterministic equal-time review supersession, one-builder serialization, and the v5-specific verification entry point.
- `database/roles/007_release_projection_snapshot_db_closure_grants.sql`: grants only the v5 verification function to reviewer and revokes it from PUBLIC, publisher, and API reader.

No historical SQL file was edited, squashed, reordered, or deleted.
