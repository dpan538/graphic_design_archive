# v49 Phase 2B recovery checkpoint

The bounded Fresh A completion window expired inside deferred PostgreSQL validation. The transaction was cancelled only after a live checkpoint, rolled back with zero durable project rows, and no Fresh B was started. The verified staging bundle is preserved outside Git for a separately authorized performance remediation.

```text
PHASE_STATUS=PARTIAL_PERFORMANCE_BLOCKED
PHASE2B_REHEARSAL_COMPLETE=false
RECOVERY_CHECKPOINT_CREATED=true
STAGING_BUNDLE_VERIFIED=true
STAGING_DESCRIPTOR_FILES_VERIFIED=35
FAILURE_PROBES_PASSED=11/11
FRESH_REPLAY_A_STARTED=true
FRESH_REPLAY_A_COMMITTED=false
FRESH_REPLAY_A_ROLLED_BACK=true
FRESH_POPULATION_REPLAY_COUNT=0
PERFORMANCE_GATE=FAIL
PERFORMANCE_BLOCKING_STAGE=SET_CONSTRAINTS_ALL_IMMEDIATE
DEFERRED_VALIDATION_COMPLETED=false
PARTIAL_IMPORT_RESIDUE=0
MIGRATION_BATCH_RESIDUE=0
CURRENT_POINTER_COUNT=0
SEALED_RELEASE_COUNT=0
SCHEMA_HASH_DETERMINISTIC=true
DATABASE_POPULATION_PARITY_VERIFIED=false
POPULATION_CONTENT_HASH_DETERMINISTIC=false
PUBLIC_BOUNDARY_VERIFIED=false
PRODUCTION_ROW_COUNT=0
DATABASE_POPULATED=false
PRODUCTION_MIGRATION_EXECUTED=false
FREEZE_READY=false
PROMOTION_READY=false
DEPLOYMENT_READY=false
```

| Evidence | Value |
|---|---|
| performance checkpoint | `2026-08-14T11:06:20Z` |
| rollback checkpoint | `2026-08-14T11:21:17Z` |
| cache destination | `/Users/jarlgiovanni/Library/Caches/gda_v49_phase2b/staging-20260814` |
| cleanup | `2026-08-14T11:47:19Z` |
| package generated | `2026-08-14T12:26:59Z` |
