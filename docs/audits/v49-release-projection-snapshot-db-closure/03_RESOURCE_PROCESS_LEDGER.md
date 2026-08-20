# Resource and process ledger

The closure used one socket-only PostgreSQL 16.13 cluster on non-default port 55483 with `shared_buffers=128MB`, `work_mem=4MB`, `effective_cache_size=4GB`, JIT enabled, and unchanged single-builder budgets. Every profile preflight required zero other task database sessions; each postflight required zero residual sessions.

The dedicated concurrency harness used one Python controller and at most two database sessions. It observed backend PIDs and an explicit `PgSleep` writer barrier; it did not start another cluster, importer, or builder controller. Final counts and the PID/session ledger are under `raw/final/process/`.
