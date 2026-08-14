# Failure probes and rollback

All eleven persisted negative probes passed before Fresh A. The recovery rollback is an additional bounded cancellation test, independently proving zero rows, zero batch, zero pointers, and zero seals.

```text
FAILURE_PROBES_PASSED=11/11
RUNTIME_FAILURE_MARKERS=5
DURABLE_PROJECT_ROWS_AFTER_CANCEL=0
MIGRATION_BATCH_RESIDUE=0
CURRENT_POINTER_COUNT=0
SEALED_RELEASE_COUNT=0
```

The machine-readable reports are in `evidence/`.
