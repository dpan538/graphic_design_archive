# B4 — Harness and scaling audit

## Scope and method

Read-only audit of worktree
`/private/tmp/graphic_design_archive_v49_release_snapshot_performance`, at
`00241aa3807a488934a4facb4dda295fb63bf5be` (`perf(database): stage v5
component row digests once`). I did not start PostgreSQL, `psql`, a test
runner, or any application process, and I made no implementation change.

Inspected paths:

- `database/scripts/run_phase2sp_profile.py`
- `database/tests/009_release_projection_snapshot_performance_scale.sql`
- `database/fixtures/phase2s_scale_snapshot.sql`
- `database/functions/018_release_projection_snapshot_performance.sql`
- `database/migrations/012_release_projection_snapshot_performance.sql`
- `database/roles/006_release_projection_snapshot_performance_grants.sql`
- the then-available JSON profiles beneath
  `/private/tmp/gda_phase2sp_profile.0PVy61/`
- `docs/audits/v49-release-projection-snapshot-performance/agents/A1_current_leaf_correctness.md`
- `docs/audits/v49-release-projection-snapshot-performance/agents/A2_sql_complexity.md`

Commands used:

```text
find /private/tmp -maxdepth 3 -type f \( -iname '*phase2sp*' -o -iname '*profile*.json' -o -iname '*scale*.json' -o -iname '*timing*.json' \)
sed -n / nl -ba on the inspected repository files
jq on profile JSON and JSON plans while they existed
git log --format=... -- database/functions/018... database/scripts/run_phase2sp_profile.py database/tests/009...
git status --short --branch
```

The profile directory was deleted as disposable task state before this report
was written. Its values below are first-hand observations made while it was
present, but the JSON files are **not yet candidate-tree evidence**. They must
be copied into the new audit package (with hashes) if the primary task wants
to preserve them. This report is not a replacement for those profile files.

## Observed final-tree ladder result

The `final-profile-*` files were timestamped after commit `00241aa` and
therefore are the applicable attempt for the current tree. All three observed
calls exited zero and emitted the expected object/membership counts.

| Scale | Memberships | Builder transaction wall time | Selection plan execution time | Exit |
| ---: | ---: | ---: | ---: | ---: |
| 32 | 128 | 3,505.257 ms | 38.117 ms | 0 |
| 1,000 | 3,107 | 26,111.103 ms | 3,402.023 ms | 0 |
| 2,000 | 6,107 | 86,370.397 ms | 19,123.695 ms | 0 |

For the required 1,000 → 2,000 doubling:

```text
t_2N / t_N = 3.307803466
p = ln(t_2N / t_N) / ln(2) = 1.725873519
predicted 4,000 builder time = 285,696.299 ms
predicted 8,000 builder time = 945,027.206 ms
```

This exceeds the mandatory `p <= 1.35` gate at 2,000. It also predicts a
4,000 build above both the `<90 s` target and `120 s` cap, and an 8,000 build
well above the `180 s` cap. The fixed task protocol requires a checkpoint at
this point; **4,000 and 8,000 must not be started from this remediation SHA**.

The final 2,000 plan is only a top-level `Function Scan` returning 6,107 rows
in one loop (19,123.695 ms, zero temporary blocks). SQL-language function
opacity means it contains no inner plans for its anti-joins, hashing, temp
tables, or builder phases. It cannot establish the required absence of
membership-proportional correlated subplans.

## Harness evidence assessment

### Valid properties

- `run_phase2sp_profile.py:44-57` loads the deterministic scale fixture and
  runs `ANALYZE` on the relevant source relations before its one `EXPLAIN`.
- The fixture enforces the authorized shape at
  `phase2s_scale_snapshot.sql:37-48`; observed counts follow
  `3N + min(N,107)`.
- `009...scale.sql:27-43` runs a serializable transaction and obtains counts,
  the component manifest, candidate fingerprint, and content digest from the
  actual v5 builder; it is not a fabricated pass value.
- The harness has no retry loop and does not lengthen timeouts
  (`run_phase2sp_profile.py:1-8, 71-96`).

### Limits that prevent performance closure

1. The harness measures only fixture load, `ANALYZE`, one opaque function plan,
   and total candidate-builder wall time (`run_phase2sp_profile.py:44-95`). It
   does **not** produce the required eight phase timings: guard/policy,
   publishable selection, object/presentation, folder/member, corpus/search/
   TRACE, assignment/decision/evidence hashes, component/manifest, and
   parity/integrity/candidate transition.
2. The only `EXPLAIN` is `SELECT * FROM
   research_launch_publishable_folder_assignments_v5(...)` at lines 58-68.
   PostgreSQL reports a `Function Scan`, not plans for the SQL inside the
   function nor for the PL/pgSQL builder. It is insufficient as before/after
   index or root-cause evidence.
3. Each invocation loads a scale-specific fixture into its supplied database;
   the harness does not load one 8,000 base fixture and select 32/1k/2k/4k/8k
   subsets from common base data as required. It also does not record cache
   state, server settings, PostgreSQL version, or an environment receipt.
4. The harness itself has no hard deadline enforcement, `pg_cancel_backend`,
   rollback/residue confirmation, `try/finally` cluster cleanup, or a
   structured calculation of `p`. Those may be performed by an outer runner,
   but no outer-runner receipt was available in the candidate tree at audit
   time.
5. `009...scale.sql` builds a candidate only. It does not separately time or
   run v5 validation and sealing, so it cannot meet the requested separate
   builder/validate/seal timing record.
6. Profiles were stored only under a deleted `/private/tmp` directory. No
   `04_PHASE_TIMINGS.tsv`, plan copy, profile environment JSON, or checksum
   binding yet exists in the audit directory.

## Root-cause signal from source, not proof

The v5 builder does correctly materialize expected decisions/memberships
(`018...sql:284-330`) and stages component row digests once
(`392-419`). That is a plausible bounded improvement over v4, but the 1k→2k
result shows the actual builder is still superlinear. The final profile cannot
attribute the cost because it omits phase-level instrumentation. In particular,
the builder still creates and indexes multiple temp relations, serializes and
hashes every projection row, groups per component, and performs parity
anti-joins (`334-425`). This is a hypothesis list only; no plan evidence here
permits selecting another remediation.

## Exact unrun / non-passing gates

```text
FINAL_TREE_4000_PROFILE=NOT_RUN (forbidden after p=1.725873519)
FINAL_TREE_8000_PROFILE=NOT_RUN (forbidden after p=1.725873519)
FINAL_TREE_8000_BUILDER_LE_180S=NOT_MET
FINAL_TREE_FULL_15923_47982_FRESH_A=NOT_RUN
FINAL_TREE_FULL_15923_47982_FRESH_B=NOT_RUN
FINAL_TREE_FULL_A_B_DIGEST_PARITY=NOT_RUN
FINAL_TREE_PHASE_LEVEL_EIGHT_STAGE_TIMINGS=NOT_AVAILABLE
FINAL_TREE_EXPLAIN_BEFORE_AFTER_INDEX_EVIDENCE=NOT_AVAILABLE
FINAL_TREE_VALIDATE_SEAL_TIMINGS=NOT_RUN
FINAL_TREE_PROFILE_ARTIFACTS_IN_GIT_AUDIT=NOT_AVAILABLE_AT_AUDIT_TIME
```

The following closure gates are outside this B4 profiler’s executed scope and
also have no final-tree evidence in the audit directory at audit time:
schema replay/hash, final focused 32, six fault injections, missingness
14/14, DML/permission 36/36, concurrency, Fresh A/B release digest parity,
and final process/residue receipts.

## Findings and recommendation

| Severity | Finding | Disposition |
| --- | --- | --- |
| P1 | Final-tree 2,000 scaling exponent is `1.725873519`, above the `1.35` stop threshold. | Stop the ladder and checkpoint; do not run 4k/8k/full or concurrency. |
| P1 | Harness lacks the required phase-level timings and executable inner-builder/index plans. | Do not call its single Function Scan a root-cause proof. |
| P1 | Scale inputs are loaded separately and the profiler has no deadline/residue/cleanup receipt. | Treat observed timings as diagnostic, not closure evidence. |
| P1 | Profile JSON/plan artifacts were transient and are absent from the candidate-tree audit at this review point. | Preserve only additive copies with checksums; otherwise record them as unavailable. |
| P2 | JSON embeds raw `stdout` rather than a structured digest/count result plus explicit `p` calculation. | Improve only in a future authorized remediation, not during this checkpoint. |

```text
P0_COUNT=0
P1_COUNT=4
P2_COUNT=1
PERFORMANCE_GATE=FAILED_AT_2000
RECOMMENDED_STATUS=PARTIAL_PERFORMANCE_CHECKPOINT
```

The evidence cannot support `RELEASE_SNAPSHOT_CORRECTNESS_AND_PERFORMANCE_CLOSED` or `RUNTIME_CLOSURE_AUTHORIZED=true`.
