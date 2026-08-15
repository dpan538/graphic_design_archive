# Database and contract receipt

`database/scripts/run-phase2c-small-db-integration.sh` passed with local
PostgreSQL 16.13 in a private temporary data directory, Unix socket and
non-5432 port. The runner created no TCP listener and removes the cluster on
exit. The schema replay completed with nine project schemas.

The test uses `database/fixtures/phase2c_32_base.sql`, a small synthetic
fixture only. It does not read a staging directory, SQLite, search index,
atlas, shards or production records. Its one held object is a database
authorization control; public fixture responses remain citation-only.

The core Read API is intentionally a subset: exact/current descriptor,
overview, folders, surfaces, archive search, TRACE atlas/objects/neighborhood
and relation registry routes. It implements GET/HEAD/OPTIONS and rejects
writes with 405. `FULL_READ_API_V1_IMPLEMENTED=false`.

The Postgres adapter uses parameterized queries against the new exact sealed
views only. It has no `current` query path and is marked `server-only`.
