# B5 — Matrix, concurrency, missingness, DML and permission audit

## Scope and method

This is a read-only source audit of
`00241aa3807a488934a4facb4dda295fb63bf5be` on
`fix/v49-release-projection-snapshot-performance-20260817`.  I did not start
PostgreSQL, run `psql`, start any application process, or change implementation
files.  This report therefore distinguishes a static implementation assertion
from an executed final-tree gate.

Inspected paths:

- `database/migrations/012_release_projection_snapshot_performance.sql`
- `database/functions/018_release_projection_snapshot_performance.sql`
- `database/roles/006_release_projection_snapshot_performance_grants.sql`
- `database/tests/008_release_projection_snapshot_performance.sql`
- `database/tests/009_release_projection_snapshot_performance_scale.sql`
- `database/tests/006_release_projection_negative_matrix.sql`
- `database/tests/005_release_projection_snapshot.sql`
- `database/scripts/run_phase2sp_profile.py`
- `database/fixtures/phase2s_32_snapshot.sql`

Commands used were `git log`, `git diff --stat`, `git status --short --branch`,
`rg -n`, and `nl -ba ... | sed -n ...`; no command opened a database
connection.

## Static positive findings — not runtime acceptance

- v5 uses reverse `NOT EXISTS` leaf selection for assignments and decisions
  (`018:15-71`, `284-330`), and migration 012 adds reverse supersession
  indexes.  It does not reuse the v4 root predicate.
- `008_release_projection_snapshot_performance.sql` contains a two-level
  assignment-chain fixture and source assertions that the leaf is projected
  and the superseded root is absent (`008:6-68`).
- The v5 internal six-argument builder has an explicit six-value fault set;
  an unknown value is statically mapped to `22023`
  `RESEARCH_LAUNCH_V5_UNKNOWN_FAULT_POINT` (`018:241-268`).  The public
  wrapper has only five arguments and grant file 006 revokes the internal
  entry point from `PUBLIC` and the publisher.

These observations are only static.  No final-tree execution receipt existed
in the new audit directory at this audit point, so none may be cited as a
runtime PASS.

## Required-gate ledger

| Gate | Static coverage | Final-tree execution evidence | Disposition |
| --- | --- | --- | --- |
| Current assignment leaf | `008` supplies one two-node assignment chain; v5 selection is reverse anti-join. | Unverified. | Must run focused v5 test and record actual projection, folder/type and component-digest assertions. |
| Decision current leaf / multiple effective accepts | v5 builder has `MULTIPLE_EFFECTIVE_FOLDER_DECISIONS`, but `008` creates no decision-supersession chain and no duplicate-current-decision case. | Unrun. | Insufficient. Add/execute named-error cases. |
| Assignment branch leaves | Unique temporary indexes can fail downstream generically, but there is no pre-copy named `23514` branch test or documented nonconflicting-branch semantics. | Unrun. | Insufficient. |
| Held/proposed/rejected/unreviewed/wrong-kind/no-support exclusion | Fixture includes one held object and one proposed held assignment; `008` directly checks only the held object. | Unrun; proposed source ID is not directly checked. | Insufficient for the requested negative predicate matrix. |
| TRACE availability | v5 statically fails closed when a canonical accepted relation exists, but `008` exercises neither proposed/unreviewed zero counts nor accepted-relation v5 failure.  Existing such coverage is v4-only (`006`). | Unrun on v5. | Insufficient. |
| Fault injection | `008` tests only an **unknown** fault point.  `006` exercises six v4 fault points/protocol v4. | v5 `6/6` unrun. | Historical v4 `6/6` cannot be inherited as final-v5 proof. |
| Missingness matrix | No v5 parameterized seven value/missingness pairs (14 cases) were found. | `0/14` represented by source coverage; unrun. | Missing. |
| Guarded-table DML | `006` has only two v4 tests (one `UPDATE`, one `DELETE`); no v5 matrix covers `INSERT`/`UPDATE`/`DELETE` for all 12 guarded tables. | v5 `0/36` source coverage; unrun. | Missing. |
| Publisher/API-reader/PUBLIC permissions | Grant 006 is a static revoke/grant change.  No v5 test invokes the public wrapper as publisher, denies the internal fault function as publisher, denies `api_reader` base-table read/write, or enumerates PUBLIC privileges. | Unrun. | Insufficient. |
| Same-release dual builder | v5 has an advisory transaction lock, but no two-session runner/barrier or assertion of A=`00000`, B=`40001`, one receipt/event and loser residue zero. | Unrun. | Missing. |
| Different-release isolation | No two-session test found. | Unrun. | Missing. |
| Canonical-writer overlap | No two-session serializable writer/build test or pre-state versus `40001` assertion found. | Unrun. | Missing. |
| Post-build/seal and stale-CAS denial | Not covered by the new v5 focused or scale tests. | Unrun. | Insufficient. |

`run_phase2sp_profile.py` starts one `psql` process at a time and contains no
barrier, `pg_locks` observation, second backend, or SQLSTATE `40001` assertion;
it cannot serve as any of the three required concurrency tests.  Likewise,
`009_release_projection_snapshot_performance_scale.sql` creates one release
and prints counts/digests but cannot substantiate the above negative or
permission matrices.

## Evidence inheritance rule

`006_release_projection_negative_matrix.sql` and
`005_release_projection_snapshot.sql` name v3/v4 functions and v4 protocol
tables.  Their fault, DML and permission results are **HISTORICAL_ONLY** after
the v5 migration/function/grant changes.  They may explain prior behavior but
cannot satisfy a final-tree v5 claim, even where a guard table is shared.

## Verdict

```text
P0_COUNT=0
P1_COUNT=7
P2_COUNT=0
FINAL_TREE_MATRIX_ACCEPTANCE=NOT_ESTABLISHED
CONCURRENCY_ACCEPTANCE=NOT_ESTABLISHED
MISSINGNESS_NEGATIVE_CASES=0/14_SOURCE_COVERAGE
POST_BUILD_DML_DENIAL_CASES=0/36_SOURCE_COVERAGE
FAILURE_INJECTION_PASS_COUNT=0/6_ON_V5_FINAL_TREE
```

The v5 correctness shape removes the previously identified root/leaf P0
statically, but the mandatory correctness/performance stop does **not** permit
the unrun or v4-only gates above to be represented as PASS.  If the bounded
scale ladder subsequently stops or exceeds its hard limit, Phase 2S-P must be
reported as a `PARTIAL_*_CHECKPOINT`; full correctness/performance closure and
runtime-closure authorization remain blocked until the same final SHA has the
executed v5 matrix and two-session evidence.
