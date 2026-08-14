# Public boundary receipt

The population-specific Fresh B probe passed after both full replays.

```text
PUBLIC_BOUNDARY_VERIFIED=true
API_READER_RAW_LOCATOR_SELECT_DENIED=true
API_READER_RAW_SOURCE_SELECT_DENIED=true
API_READER_ARCHIVE_WRITE_DENIED=true
API_CURRENT_ROWS=0
API_REMOTE_IMAGE_ROWS=0
HELD_LOCATOR_PUBLIC_LEAK_COUNT=0
POSITIVE_RIGHTS_COVERAGE=0
REMOTE_IMAGE_DECISION_COUNT=0
PUBLIC_PIXEL_LOCATOR_COUNT=0
CURRENT_POINTER_COUNT=0
SEALED_RELEASE_COUNT=0
PRODUCTION_DATABASE_TOUCHED=false
```

The connection was the task-owned Unix socket with `listen_addresses=''`;
`inet_server_addr()` and `inet_server_port()` were null. The generic Phase 2A
empty-schema Seal/CAS fixture was also attempted in a rollback-only
transaction. It reached its assertion that total held rows equal exactly one,
which is intentionally false for this populated rehearsal's 7,928 held rows.
That transaction rolled back and created zero persistent rows. This
cardinality precondition failure is recorded as `NOT_APPLICABLE`, not hidden
or called a pass. The purpose-built population probe and both full verifiers
directly establish the boundary required by this phase.

Evidence: `evidence/P5_PUBLIC_BOUNDARY_POPULATION.json` and
`evidence/P5_FRESH_B_VERIFY.json`.
