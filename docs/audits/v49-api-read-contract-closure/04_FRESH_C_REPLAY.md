# FRESH_C replay

FRESH_C began as an empty database and ran only `database/data-migrations/v48-to-v49/run-rehearsal.sh` with the attested Candidate staging bundle. The formal replay copied 3,957,270 rows / 1,245,479,023 bytes, committed 3,829,784 durable inserts, and reconciled 15,923 Candidate stable IDs.

```text
FRESH_C_REPLAY=PASS
FRESH_C_SCHEMA_HASH_MATCH=PASS
FRESH_C_RELEASE_DIGEST_MATCH=PASS
FRESH_C_STABLE_ID_RECONCILIATION=PASS
FRESH_C_CURRENT_LEAF=PASS
FRESH_C_14_14_MISSINGNESS=PASS
FRESH_C_36_36_DML_PERMISSION=PASS
CANONICAL_OBJECTS=15923
ELIGIBLE=7995
HELD=7928
ACCEPTED_TRACE=0
POSITIVE_RIGHTS=0
```

The disposable release fixture then produced sealed/current release `v49-api-contract-fresh-c`, manifest `4addfdb3cb9314587908096572242b9d63e9cef9e6e1be68c0c646491a43a90a`, projection digest `e7ab41633b481d455bc3ceab3e2d0d2a1d5410b186b65bfb2697059182d1b49d`, and 7,995 public surfaces. An initial fixture preflight referred to a non-existent `description` column; its transaction rolled back atomically before the corrected `public_contract_version` insert ran.
