# v49 Phase 2A — Executive receipt

Status: `PHYSICAL_SCHEMA_IMPLEMENTED`

Phase 2A implements the fresh PostgreSQL 16 physical model, least-privilege
roles, deferred research and rights constraints, independent research/visual
release seals, serializable validation, compare-and-swap promotion, public
redaction views, and adversarial tests. It imports no v48 production row and
does not modify the frontend.

## Verified outcome

- Two isolated fresh replays completed from an empty database.
- Both replay/test suites returned `CONSTRAINT_TESTS=PASS`,
  `ROLE_TESTS=PASS`, `RELEASE_TESTS=PASS`, and
  `TEST_FIXTURE_RESIDUE=0`.
- Both normalized schema dumps are byte-identical at SHA-256
  `4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105`.
- Project-table production row count is `0`; all fixture transactions rolled
  back.
- Empty accepted TRACE and zero-positive-rights releases both validate, seal,
  verify and promote in the executable fixture.
- Stable5 received independent C3 and C4 review with residual P0/P1 `0/0`.

## Boundaries

`DATABASE_POPULATED=false`. `MIGRATION_EXECUTED=false` refers to the future
15,923-row v48 JSON population migration; only empty-schema migrations and
rollback-only fixtures ran here. No API, OpenAPI, JSON-LD, DCAT, frontend,
CI/deployment or production database was implemented or contacted.

See [12_PHASE2A_GATE_RECEIPT.md](12_PHASE2A_GATE_RECEIPT.md) for the exact gate
fields and [MANIFEST.json](MANIFEST.json) for machine-verifiable scope.
