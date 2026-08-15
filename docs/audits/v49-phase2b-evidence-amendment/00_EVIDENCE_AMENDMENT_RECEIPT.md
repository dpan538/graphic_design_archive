# Phase 2B audit evidence amendment receipt

```text
SOURCE_SHA=11e7b82d27b2774273d2f0d68904632246dabd37
IMPLEMENTATION_SHA=302ddb9683e8b3ee06c34557d10fd72a65c2afaf
PRE_FIX_SCHEMA_STATE=86ba95cae9ecf12e58fcabb8170c9020e151b386
POST_FIX_AUDIT_STATE=11e7b82d27b2774273d2f0d68904632246dabd37
POSTGRESQL_VERSION=16.13

ORIGINAL_PACKAGE_VERIFIED=false
ORIGINAL_CHECKSUM_VERIFICATION=61/72
ORIGINAL_MISSING_COUNT=11
HISTORICAL_ARTIFACTS_RECOVERED=false
CHECKSUM_GATE_LOWERED=false
HISTORICAL_AUDIT_FILES_REWRITTEN=false
SUPERSESSION_DECLARED=true

EVIDENCE_REMEDIATION_MODE=AUDITED_P1_REPRODUCTION_SUPERSESSION
CORRECTIVE_PROBE_RERUN_COUNT=11
CORRECTIVE_PROBE_PASS_COUNT=11
CORRECTIVE_PACKAGE_CHECKSUM=233/233
SEMANTIC_EQUIVALENCE_VERIFIED=true
INDEPENDENT_VERIFIER_P0=0
INDEPENDENT_VERIFIER_P1=0
PROMOTION_EVIDENCE_BASIS=AUDITED_P1_REPRODUCTION_SUPERSESSION
EVIDENTIARY_GAP_CLOSED=true

EMPTY_SCHEMA_A_EXIT=0
EMPTY_SCHEMA_A_HASH=aa8cb0af7b61931e51f1f71ed2e4cf0d10b178669de16807871819b330742e8b
EMPTY_SCHEMA_B_EXIT=0
EMPTY_SCHEMA_B_HASH=aa8cb0af7b61931e51f1f71ed2e4cf0d10b178669de16807871819b330742e8b
```

This additive package supersedes the missing P1 primary artifacts for
promotion-gate purposes only. It never claims the original 72/72 checksum
passed, and it never places new logs at the missing historical paths.

Each role used the existing formal probe script on a separate disposable
database and ended in the script's `ROLLBACK;`. The post-run zero-row checks,
normal `dropdb`, normal fast cluster shutdown, deleted socket/PGDATA, and
process receipt establish no partial database residue. No stage directory was
read; no Candidate extractor, Fresh A/B, or full population replay was run.

The two diagnosed quadratic paths are preserved in scope: the leaf path serves
`rights.rights_assessment_one_current_leaf`; the delivery completeness path
serves `rights.delivery_assessment_validation`,
`rights.delivery_rights_validation`, and
`rights.delivery_policy_validation`. Pre-fix roles reproduced the sequential
scan behavior, while post-fix runs verified the target-led forward indexes and
the scale-1,000 plan roles named
`rights_assessment_visual_reference_target_idx`.

The retained historical Fresh A/B receipts already verified their migration
batch before database disposal. The later `MIGRATION_BATCH_RESIDUE=0` result
is a cleanup condition, not a claim that a batch was absent during validation.
