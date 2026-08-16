# Phase 2C-S release projection snapshot — partial checkpoint

This is an additive, forward-only database checkpoint from
`3e666b5265ebe7b41ea0c98531b35761ff0d9485`. It introduces migration 010,
v3 release-owned folder, membership, surface-presentation, search, corpus
summary, TRACE-availability, component-manifest, receipt, validation, and
manifest structures. It does not modify migrations 001–009, historical
functions, historical roles/tests/audits, frontend, API route, adapter,
feature/stable/main, staging, or production.

The builder requires a caller-owned `SERIALIZABLE` transaction, takes a
per-release transaction advisory lock, requires a fresh empty draft, selects
only `eligible` objects from the policy-bound corpus, and uses set-based
inserts. It records the otherwise unpromoted held/excluded/proposed/rejected
source dispositions in a release-owned count table. Candidate validation and
seal use the v3 receipt/component rows rather than live canonical sources.

The two fresh replays and the 32-object v3 build/validate/seal/fault-injection
test passed with normalized schema SHA-256
`6b6a7a01cfb08bf934b695722782e829da5941378ce7b242ea8c127addb8211b`.
The performance ladder stopped before completion: after one targeted repair
for a source-record ordinal collision, the permitted recheck reached a
distinct `core.entity` fixture-column mismatch at the 8,000-object stage.
The stop rule therefore forbids a third run. No concurrency test was started,
and this package must not be read as a phase closure.

```text
PHASE_STATUS=PARTIAL_CHECKPOINTED
DESIGN_CHANGE_AUTHORIZED=true
HISTORICAL_MIGRATIONS_001_009_EDITED=false
FRESH_SCHEMA_REPLAY_COUNT=2
SCHEMA_HASH_DETERMINISTIC=true
FIXTURE_OBJECT_COUNT=32
FIXTURE_FOLDER_COUNT=4
FIXTURE_PUBLIC_MEMBERSHIP_COUNT=32
FAILURE_INJECTION_PASS_COUNT=5/5
PERFORMANCE_BUDGET_MET=UNVERIFIED
CONCURRENT_SNAPSHOT_TEST_PASS=UNVERIFIED
RUNTIME_CLOSURE_AUTHORIZED=false
FEATURE_BRANCH_ADVANCED=false
STABLE_BRANCH_TOUCHED=false
PROTECTED_MAIN_TOUCHED=false
```
