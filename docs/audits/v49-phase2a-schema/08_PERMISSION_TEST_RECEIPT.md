# v49 Phase 2A — Permission and security receipt

## Role boundary

The schema creates seven project roles: NOLOGIN `schema_owner`, and login
`migrator`, `ingest_writer`, `reviewer`, `publisher`, `api_reader`, and
`auditor`. Only migrator may `SET ROLE` to schema owner. Runtime roles have no
superuser, createdb, createrole, replication or bypass-RLS attribute.

`PUBLIC` loses database connect, project-schema access, existing object/type
privileges and all schema-owner default privileges. Runtime writes are exposed
only through exact controlled functions. Publisher has no direct release-table
DML; curator/reviewer cannot seal; auditor cannot promote; api_reader has only
approved `api_v1` view reads and no base-table or write grant.

## Machine evidence

[03_ROLE_GRANT_MATRIX.tsv](03_ROLE_GRANT_MATRIX.tsv) contains 15,485 sorted,
unique cross-product rows covering role attributes, ordered membership pairs,
database/schema/relation/sequence/routine/type privileges and default ACLs.
Every row matches across both fresh replays and has `status=PASS`.

`database/tests/003_roles.sql` also runs positive controlled paths for
assertion, assignment, claim, relation and visual-bridge review, plus negative
PUBLIC/API/publisher/auditor oracles. Stable5 contains 83
`SECURITY DEFINER` declarations; all pin `search_path=pg_catalog`, and none
contains dynamic SQL.

`ROLE_GRANT_MATRIX_VERIFIED=true`

`RAW_HELD_LOCATOR_HIDDEN=true`

`PUBLIC_WRITE_DENIED=true`
