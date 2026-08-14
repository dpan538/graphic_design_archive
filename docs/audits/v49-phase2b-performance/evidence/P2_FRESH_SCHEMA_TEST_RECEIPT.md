# Forward-migration fresh-schema test receipt

This human-readable receipt preserves the controller result for the two
fresh, empty-schema tests executed before the scale ladder. The disposable
databases and their temporary stdout logs were deleted after successful
verification; no raw terminal log is claimed to survive.

Both runs used the same socket-only PostgreSQL 16.13 cluster, replayed the
immutable Phase 2A chain, applied
`database/data-migrations/v48-to-v49/001_performance_remediation.sql` as
`gda_v49_phase2a_schema_owner`, and then executed
`database/scripts/run_tests.sh` with `ON_ERROR_STOP=1`.

| Run | Base schema SHA-256 | Final schema SHA-256 | `run_tests.sh` exit | Final test marker | Fixture residue | Database disposal |
|---|---|---|---:|---|---:|---|
| fresh schema 1 | `4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105` | `aa8cb0af7b61931e51f1f71ed2e4cf0d10b178669de16807871819b330742e8b` | 0 | `CONSTRAINT_TESTS=PASS ROLE_TESTS=PASS RELEASE_TESTS=PASS TEST_FIXTURE_RESIDUE=0` | 0 | normal drop |
| fresh schema 2 | `4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105` | `aa8cb0af7b61931e51f1f71ed2e4cf0d10b178669de16807871819b330742e8b` | 0 | `CONSTRAINT_TESTS=PASS ROLE_TESTS=PASS RELEASE_TESTS=PASS TEST_FIXTURE_RESIDUE=0` | 0 | normal drop |

The invoked suite consists of:

- `database/tests/001_constraints.sql`, including the unknown/inactive
  relation negative paths and rights/delivery negatives;
- `database/tests/002_release_seal_cas.sql`;
- `database/tests/003_roles.sql`;
- `database/tests/004_serializable_seal.sql`;
- the runner's final all-project-table zero-residue loop.

The independent scale review subsequently observed four additional fresh
base-replay + forward-migration paths with the same final schema SHA, and both
full Fresh A/B verifiers later observed that SHA before and after population.
Those later facts corroborate schema determinism; they do not substitute for
the two test-suite executions recorded above.

```text
FRESH_EMPTY_SCHEMA_REPLAY_COUNT=2
FRESH_EMPTY_SCHEMA_TESTS_PASSED=2/2
ROLE_TESTS_PASSED=2/2
SEAL_CAS_TESTS_PASSED=2/2
UNKNOWN_RELATION_NEGATIVE_TESTS_PASSED=2/2
TEST_FIXTURE_RESIDUE=0
RAW_TEST_STDOUT_RETAINED=false
```
