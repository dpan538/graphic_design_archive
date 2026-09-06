# Current frozen database CI

Run `sh scripts/ci/run-current-db-integration.sh` with PostgreSQL 16; set `GDA_PG_BIN` to its bin directory on Linux. The runner owns an ephemeral cluster with Unix sockets and no TCP listener, runs the frozen replay without altering grants, and cleans up on success or failure.

The previous workflow invoked `database/tests/002_release_seal_cas.sql`, a historical phase2c contract that assembles releases piecemeal. Frozen roles 004–007 intentionally revoke that publishing path and promote v5. Re-running that historical test against the complete current replay fails with the *correct* permission denial; granting the old API back would weaken the frozen contract.

CI now executes the existing current tests 010–013 (v5 build/validate/seal, topology, missingness, 36 DML/permission cases and six atomic fault points), the bounded multi-session v5 concurrency harness, and an additional six real SQL calls that must deny obsolete/internal publisher entrypoints. No frozen SQL, historical test, fixture, expected digest or role grant is edited. The old suite remains historical evidence; it is not claimed as a current passing test.
