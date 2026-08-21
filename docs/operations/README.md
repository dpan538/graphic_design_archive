# Operations

The formal v49 replay entry point is `database/data-migrations/v48-to-v49/run-rehearsal.sh`; legacy runners and `db/` are prohibited. Run only against an isolated local PostgreSQL cluster on a non-default port, then use the official verifier, database tests, API read-only harness, repository hygiene gate, and database freeze verifier.

Production and staging access are outside repository verification. See `MIGRATION_V48_TO_V49.md`, `ACCEPTANCE_GATES.md`, and the final audit indexes under `docs/releases/v49/`.

