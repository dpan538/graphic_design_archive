# Database root consolidation

`database/` is the sole active database root and `db/` is absent. Official implementation diff count is `0`. Replay, API, tests, CI, and current operations use `database/`; historical `db/` is recoverable from `v49-data-api-closure-20260821`.
