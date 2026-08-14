# B2 independent scale-curve, digest, and parity review

## Provisional receipt

```text
AGENT=B2
QUEUE=B_INDEPENDENT_ACCEPTANCE
REVIEW_MODE=READ_ONLY_EXISTING_EVIDENCE_REVIEW
POSTGRES_STARTED=false
POSTGRES_CONNECTED=false
IMPORTER_STARTED=false
EXTRACTOR_STARTED=false
BUILD_STARTED=false
FROZEN_STAGING_SCANNED=false
CORE_IMPLEMENTATION_CHANGED=false
REPORT_ONLY_WRITE=true

B2_REVIEW_STATUS=PROVISIONAL_AWAITING_SCALE_08000
B2_P0_FINDING_COUNT=0
B2_SCALE_RESULTS_AVAILABLE=4/5
B2_AVAILABLE_SCALES=50,250,1000,4000
B2_SCALE_08000_RECEIPT_PRESENT=false
B2_LARGEST_THREE_FIT_AVAILABLE=false
B2_FULL_REPLAY_PROJECTION_ACCEPTED=false
B2_COUNTS_PARITY_AVAILABLE_SCALES=PASS
B2_DIGESTS_AVAILABLE_SCALES=PASS
B2_SCHEMA_HASH_AVAILABLE_SCALES=PASS
B2_NAMED_GROUP_BUDGET_AVAILABLE_SCALES=PASS
B2_UPDATED_CODE_FAILURE_PROBES=11/11
B2_CPU_EVIDENCE_COMPLETE=false
B2_PEAK_DISK_EVIDENCE_COMPLETE=false
FULL_REPLAY_AUTHORIZED_BY_B2=false
```

No P0 correctness or semantic-parity defect is visible in the four completed
scale receipts.  Each completed rung committed, verified, preserved the
remediated schema hash, matched its content-addressed fixture, and reported
zero integrity mismatch.  The scale-4,000 result is encouraging: its total
wall time was 1,596.583135 seconds, its slowest named group was 61.486119
seconds, and its final all-constraint omission check took 0.021803 seconds.

This is not yet a P3 acceptance.  The required scale-8,000 receipt does not
exist, so the specified largest-three-rung fit (`1,000 / 4,000 / 8,000`), the
8,000-object 45-minute boundary, and a defensible 15,923-object projection
cannot be evaluated.  Two observability limitations also need explicit
closure before the controller treats the ladder as complete: the recorded CPU
fields are client-child CPU rather than PostgreSQL backend CPU, and the
receipts record final database size rather than peak task-owned disk usage.

## Review boundary and inputs

I reviewed only repository code and already-generated audit artifacts.  I did
not read the frozen 4.5 GB staging payload, hash large TSVs, or inspect any
fixture data rows.  The reviewed evidence was:

- `evidence/P2_FIXTURE_BUILD.json`;
- `evidence/P2_FIXTURE_COVERAGE.json`;
- `evidence/P2_SCALE_00050.json`;
- `evidence/P2_SCALE_00250.json`;
- `evidence/P2_SCALE_01000.json`;
- `evidence/P2_SCALE_04000.json`;
- `evidence/P2_UPDATED_CODE_FAILURE_PROBES.json`;
- `evidence/P1_RIGHTS_LEAF_POST_FIX_PLAN_1000.log`;
- `evidence/P1_DELIVERY_POST_FIX_PLAN_1000.log`;
- `03_ROOT_CAUSE_ANALYSIS.md` and B1's closing remediation review; and
- `run_performance_fixture.py`, solely to determine what the receipt fields
  measure.

At review time `evidence/P2_SCALE_08000.json` was absent.  No conclusion below
silently substitutes a projection for that missing observation.

## Fixture determinism and coverage

The fixture-build receipt is `PASS`, reports `stagingReused=true` and
`extractorRerun=false`, and binds all five rungs to the inherited staging
manifest `01ac60c705f7450c6668a91ee6a3d2842c3b0258a4ecd85139611bf916681322`,
attestation `11742e9afc577d976ea097540326c2697937290635735ad9d4466efce1758bcc`,
and canonical Candidate SHA
`b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48`.
The result receipts' fixture-manifest and selection identities agree with the
build receipt:

| Scale | Selection SHA-256 | Fixture manifest SHA-256 | Input bytes | Raw literals | Folder assignments |
|---:|---|---|---:|---:|---:|
| 50 | `d5f2d5fa...b9217fee` | `2da48a77...b926292e` | 256,830,322 | 11,750 | 165 |
| 250 | `0744ad83...7ac94cb` | `56a65219...d2bcad` | 269,414,195 | 56,851 | 772 |
| 1,000 | `24f7d1f7...8bfa94dc` | `38b7f7b3...78cb14` | 317,108,731 | 225,929 | 3,049 |
| 4,000 | `369075e8...7a33141` | `6b2196f5...02d6d60` | 507,571,899 | 901,977 | 12,132 |
| 8,000 (built, not run) | `e2e88fff...3a2eb3` | `f23301df...92bb08` | 760,195,954 | 1,799,337 | 24,166 |

The dedicated coverage receipt says every rung includes eligible and held
objects, tier present and missing, visual-reference present and absent, all
five literal-value quantiles, all five folder-population rank quantiles, all
observed rights states, and high-cardinality objects.  It also explains a
potentially confusing field in the build receipt: `folderQuantiles=[4]`
reflects value-quantile collapse because nearly all objects have three folder
memberships.  The population-rank method still assigns and covers quantiles
0--4, and every rung includes membership counts 3, 4, and the six count-5
objects.  I accept that explanation; it does not represent a missing fixture
stratum.

## Completed-rung timing and load volume

All four result receipts have `status=PASS`, importer
`status=COMMITTED/returnCode=0`, `committedMarker=true`, and verifier
`status=PASS`.  All were labelled warm-cache runs.

| Scale | Total wall s | Import wall s | Client child user+sys CPU s | Input bytes | Final DB bytes | COPY s / rows | Durable inserts s / rows | Analyze s | Parity s |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 231.127721 | 161.739072 | 2.220699 | 256,830,322 | 88,505,367 | 87.481063 / 12,961 | 61.503729 / 12,541 | 1.687390 | 0.048938 |
| 250 | 542.888934 | 386.023878 | 2.829828 | 269,414,195 | 104,938,519 | 206.793863 / 62,823 | 143.744543 / 60,818 | 1.053915 | 0.636199 |
| 1,000 | 586.432368 | 382.874296 | 3.221108 | 317,108,731 | 163,847,191 | 141.344922 / 250,206 | 175.425267 / 242,274 | 3.004043 | 0.836281 |
| 4,000 | 1,596.583135 | 1,219.804102 | 5.511757 | 507,571,899 | 399,203,351 | 547.488146 / 1,001,072 | 433.968392 / 969,169 | 1.125898 | 2.502620 |

The non-monotonic scale-250/1,000 timings make a fit over the smaller rungs
misleading.  They are consistent with the large fixed `source-assets.tsv`
component and warm-cache/system variability.  This reinforces the specified
rule to fit only the largest three rungs, not to cherry-pick the visually best
pair.

The receipts include PostgreSQL 16.13 and the same key settings on each rung:
`fsync=on`, `synchronous_commit=on`, `full_page_writes=on`,
`track_io_timing=on`, `track_wal_io_timing=on`, `shared_buffers=65536` pages,
and `work_mem=65536` kB.  After each observed run, active peer backends and
ungranted locks were both zero.

## Named constraint groups

Every loader receipt contains all eleven business groups plus the required
`final_all_omission_check`.  The four root-cause paths are separately visible,
and no completed group approaches the 15-minute P3 limit:

| Scale | Slowest group (s) | Current leaf s | Delivery parent s | Delivery rights s | Delivery policy s | Final ALL s |
|---:|---|---:|---:|---:|---:|---:|
| 50 | `folder_assignment_shape` (3.348217) | 0.090037 | 1.443922 | 0.169637 | 0.582419 | 0.046832 |
| 250 | `folder_assignment_shape` (7.398826) | 0.386690 | 4.222509 | 3.276272 | 2.375397 | 0.000265 |
| 1,000 | `folder_assignment_shape` (22.568334) | 0.657998 | 7.556021 | 6.155783 | 4.507659 | 0.005127 |
| 4,000 | `folder_assignment_shape` (61.486119) | 2.370158 | 24.671268 | 36.013907 | 30.003194 | 0.021803 |

The scale-1,000 post-fix plan receipts independently explain the actual typed
queries, not the legacy opaque predicates.  The current-leaf query uses
`rights_assessment_visual_reference_target_idx`, then the assessment primary
key and supersession index, and executes in 0.379 ms with zero temp writes and
zero WAL.  The delivery-completeness query uses the same target-leading index
plus the bridge, assessment/current-leaf, and delivery-rights indexes; its
explained execution time is 0.129 ms, also with zero temp writes and WAL.  This
supports the mechanism-level finding that the prior global scan was removed.

The pairwise 1,000-to-4,000 slopes are diagnostic only:

| Metric/group | Pairwise exponent |
|---|---:|
| Total wall | 0.722476 |
| Import wall | 0.835853 |
| COPY wall | 0.976804 |
| Durable-insert wall | 0.653367 |
| `folder_assignment_shape` | 0.722980 |
| `rights_assessment_current_leaf` | 0.924414 |
| `rights_assessment_shape_support` | 1.170810 |
| `delivery_parent_validation` | 0.853567 |
| `delivery_rights_validation` | 1.274270 |
| `delivery_policy_validation` | 1.367330 |

The two delivery-link slopes slightly exceed 1.25 on this single pair.  That
is not a gate failure by itself, because the required test is a three-point
fit and these groups are far below their absolute budget.  It is, however, a
specific reason B2 must examine the 8,000 result rather than declaring the
curve linear from aggregate wall time alone.

## I/O, WAL, and statistics

Before/after counter deltas from the sequential single-cluster runs are:

| Scale | WAL delta bytes | DB active-time delta ms | DB read/write ms | Client read/write bytes | Temp files/bytes | Tuples inserted delta |
|---:|---:|---:|---:|---:|---:|---:|
| 50 | 73,424,998 | 174,198.141 | 1,763.826 / 3,835.728 | 131,727,360 / 130,195,456 | 0 / 0 | 45,824 |
| 250 | 99,457,174 | 446,226.031 | 4,899.034 / 17,846.552 | 167,960,576 / 143,032,320 | 0 / 0 | 98,393 |
| 1,000 | 194,791,714 | 437,455.311 | 4,864.395 / 20,005.052 | 289,185,792 / 191,668,224 | 1 / 76,636,160 | 295,786 |
| 4,000 | 694,682,693 | 1,435,023.381 | 15,926.703 / 61,554.545 | 756,080,640 / 385,785,856 | 3 / 370,221,056 | 1,087,610 |

These receipts preserve table/index-stat snapshots as well as I/O/WAL
counters.  Because `pg_stat_io` and WAL counters are cluster-level and can be
reported asynchronously, their before/after deltas are suitable for coarse
sequential-run accounting, not per-query attribution.  The direct P1
`EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)` receipts are the stronger evidence
for the repaired indexes.  Scale-1,000 and scale-4,000 snapshots show 6,329 and
27,091 scans of the exercised visual-reference target index respectively;
smaller-rung index snapshots appear affected by statistics flush timing and
should not be used for a curve.

## Counts, semantic digests, and schema replay

For every completed rung, the expected fixture counts equal the verifier's
actual metrics:

| Scale | Objects | Eligible / held | Raw literals | Folders / assignments | Bundles / with reference | Locator occurrences | Trace / positive rights / pointers / seals |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 50 | 50 | 36 / 14 | 11,750 | 40 / 165 | 50 / 39 | 39 | 0 / 0 / 0 / 0 |
| 250 | 250 | 105 / 145 | 56,851 | 91 / 772 | 250 / 206 | 206 | 0 / 0 / 0 / 0 |
| 1,000 | 1,000 | 390 / 610 | 225,929 | 132 / 3,049 | 1,000 / 899 | 899 | 0 / 0 / 0 / 0 |
| 4,000 | 4,000 | 1,565 / 2,435 | 901,977 | 171 / 12,132 | 4,000 / 3,865 | 3,867 | 0 / 0 / 0 / 0 |

All twenty reported integrity-invariant counters are zero on every completed
rung.  Public-fixture checks also report raw locator/source select denied,
archive write denied, and zero API current/pixel rows.  This is useful
scale-fixture evidence, but it is not the final post-Fresh-B public-boundary
gate.

Each rung records three independent digest dimensions:

| Scale | Count-vector SHA-256 | Normalized semantic SHA-256 | Stable-key-set SHA-256 |
|---:|---|---|---|
| 50 | `2c676000...186634` | `048b0074...177155` | `22e948fb...4d08c3` |
| 250 | `c7ab28f1...c4e8b0` | `36549b59...202dd1` | `fe98f468...c4b5de` |
| 1,000 | `2d9efc15...ea8d9b` | `3bb62a46...2e2e23` | `29b99d7b...2c94d` |
| 4,000 | `c17d0615...0d7ed8` | `cebeefcb...2da6f7` | `77c67f5f...f12b88` |

Digests are expected to differ across rungs because the selected populations
differ.  Their acceptance meaning here is that each completed fixture emitted
all three non-empty deterministic receipts while its own count and invariant
checks passed.  A/B equality cannot be inferred from this ladder and remains
a later full-replay obligation.

The four unique scale databases each report base schema SHA
`4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105`
and final schema SHA
`aa8cb0af7b61931e51f1f71ed2e4cf0d10b178669de16807871819b330742e8b`.
The final SHA is identical before and after each population transaction.  The
four successful base replay + forward migration paths are consistent with a
deterministic remediated schema and exceed the requested minimum of two fresh
schema results.  B2 does not independently certify how the controller created
or later dropped each database; B3 owns final process/residue cleanup.

The changed importer path's bounded scale-50 failure receipt is also `PASS`:
all eleven named failures returned code 2, observed the expected marker, and
left zero project-table, migration-batch, pointer, or seal residue.  The
receipt correctly records `fullScaleFailureProbesRerun=false`.

## Final-fit method once scale 8,000 exists

B2 will use only the three completed points `N = {1000, 4000, 8000}` and their
top-level `wallSeconds`.  Let `x = ln(N)` and `y = ln(seconds)`.  The ordinary
least-squares exponent is:

```text
beta = sum((x - mean(x)) * (y - mean(y)))
       / sum((x - mean(x))^2)
alpha = mean(y) - beta * mean(x)
```

The complexity gate requires `beta <= approximately 1.25`.  The primary full
projection will be `exp(alpha + beta * ln(15923))`; B2 will cross-check it
against the observed-8,000 anchor
`t8000 * (15923 / 8000)^beta`.  In addition, B2 will calculate the same
diagnostic slope for COPY, durable inserts, and every named constraint group
to ensure aggregate time is not masking one superlinear deferred family.

Acceptance then additionally requires:

1. scale 8,000 result and verifier both `PASS`;
2. scale 8,000 total wall `<= 2,700` seconds;
3. every scale-8,000 named group `<= 900` seconds;
4. final `ALL` omission check completes successfully;
5. fitted total-wall exponent `<= approximately 1.25`;
6. projected 15,923 total `<= 5,400` seconds;
7. expected/actual counts, integrity counters, schema hash, and digest receipts
   remain valid; and
8. Queue B has no P0 finding.

For context only, the two-point 1,000/4,000 total-wall exponent is 0.722476;
anchoring it at 4,000 projects 4,331.63 seconds for 15,923.  A simple linear
4,000-object extrapolation instead gives 6,355.60 seconds.  This wide split
shows why neither projection is accepted without the actual 8,000 rung.

## Evidence gaps that must not be overstated

### B2-E1 — scale 8,000 is mandatory

This is the current gate blocker.  Until the result exists, B2 cannot report
`PERFORMANCE_BUDGET_MET=true`, `FULL_REPLAY_AUTHORIZED=true`, or a final
growth exponent.  Failure or timeout at 8,000 is a P3 No-Go; it must not be
replaced by the favourable 1,000/4,000 pair.

### B2-E2 — the recorded CPU is not PostgreSQL backend CPU

`run_performance_fixture.py` obtains `childUserCpuSeconds` and
`childSystemCpuSeconds` from Python's `resource.RUSAGE_CHILDREN`.  Those values
cover child client processes such as `psql`, schema tools, and verifier Python;
the PostgreSQL server/backend belongs to the separately started cluster and
is not that runner's child.  The scale-4,000 receipt's 5.511757 CPU seconds
against 1,596.583135 wall seconds makes this boundary visible.  The fields are
valid client CPU, but they are not per-stage database CPU and must not be
labelled as such.

Before final P3 acceptance, the controller should capture backend CPU against
the already-emitted backend PID and named stage boundaries, or explicitly
record an approved equivalent.  `databaseStats.active_time` is useful server
active duration, not CPU time, and does not close this requirement by itself.

### B2-E3 — final database size is not peak disk usage

Each receipt records `databaseBytes` after verification.  It also records
temporary bytes through PostgreSQL statistics, but no sampled maximum of the
task-owned PGDATA/runtime footprint.  Because scale 4,000 used 370,221,056
temporary bytes, the final 399,203,351-byte database cannot safely be asserted
to be the peak.  A peak-disk observation is required for scale 8,000/full
replays if the final audit package claims that metric.

The activity and lock evidence is likewise boundary-based: pre/post receipts
contain activity, table/index/I/O, and ungranted-lock snapshots, while the
import receipt contains backend PID and named-stage markers.  They do not form
an in-flight activity/lock time series.  This is adequate to show clean
boundaries on completed rungs, not to reconstruct a stalled stage after the
fact.

## Provisional B2 conclusion

```text
B2_AVAILABLE_SCALE_RECEIPTS_PASS=true
B2_FIXTURE_BINDING_PASS=true
B2_FIXTURE_COVERAGE_PASS=true
B2_AVAILABLE_COUNT_PARITY_PASS=true
B2_AVAILABLE_DIGEST_RECEIPTS_PASS=true
B2_SCHEMA_HASH_CONSISTENT=true
B2_UPDATED_PATH_ROLLBACK_PASS=true
B2_NAMED_GROUPS_OBSERVED=true
B2_FINAL_ALL_OMISSION_CHECK_OBSERVED=true
B2_ROOT_CAUSE_PLAN_MECHANISM_CONFIRMED=true
B2_SCALE_8000_PENDING=true
B2_FINAL_FIT_PENDING=true
B2_FULL_PROJECTION_PENDING=true
B2_CPU_EVIDENCE_GAP=true
B2_PEAK_DISK_EVIDENCE_GAP=true
B2_P3_GO=false
FULL_REPLAY_AUTHORIZED_BY_B2=false
```

The four available rungs support continued bounded execution to scale 8,000;
they do not authorize Fresh A.  B2 will issue a closing refresh only after the
scale-8,000 receipt is present and the controller has addressed the stated
observability gaps.

## Closing review refresh — monitored decisive ladder

This closing section supersedes the provisional Go/No-Go conclusion above.
It does not erase the historical evidence boundary: the preceding section
accurately describes what was available before the monitored reruns.  The
controller subsequently ran a single consistent, monitored version of the
three decisive rungs (`1,000 / 4,000 / 8,000`) and persisted separate scale,
backend statement-CPU, and five-second resource-monitor receipts for each.
B2 reviewed those receipts read-only and did not start or connect to a
database, importer, extractor, or build.

### Closing receipt

```text
B2_CLOSING_REVIEW_STATUS=GO
B2_REVIEW_MODE=READ_ONLY_EXISTING_MONITORED_EVIDENCE_REVIEW
B2_MONITORED_DECISIVE_SCALES=1000,4000,8000
B2_MONITORED_SCALE_RECEIPTS=3/3_PASS
B2_BACKEND_CPU_RECEIPTS=3/3_PASS
B2_RESOURCE_MONITOR_RECEIPTS=3/3_PASS
B2_INITIAL_MONITORED_LOGICAL_MATCH=3/3
B2_P0_FINDING_COUNT=0
B2_P1_FINDING_COUNT=0

B2_TOTAL_WALL_OLS_EXPONENT=0.750318118554367
B2_TOTAL_WALL_OLS_PROJECTION_15923_SECONDS=3530.5179820149265
B2_TOTAL_WALL_8000_ANCHORED_OLS_PROJECTION_15923_SECONDS=3982.552489738611
B2_SCALE_8000_TOTAL_SECONDS=2376.102825
B2_SCALE_8000_IMPORT_SECONDS=1687.537084
B2_SCALE_8000_MAX_NAMED_GROUP=folder_assignment_shape
B2_SCALE_8000_MAX_NAMED_GROUP_SECONDS=158.029628
B2_SCALE_8000_FINAL_ALL_SECONDS=0.057805

B2_CPU_EVIDENCE_COMPLETE_FOR_DECISIVE_MAX_THREE=true
B2_PEAK_DISK_EVIDENCE_COMPLETE_FOR_DECISIVE_MAX_THREE=true
B2_COUNTS_PARITY_PASS=true
B2_DIGEST_DETERMINISM_PASS=true
B2_SCHEMA_HASH_PASS=true
B2_PERFORMANCE_BUDGET_MET=true
B2_P3_GO=true
FULL_REPLAY_AUTHORIZED_BY_B2=true
```

`FULL_REPLAY_AUTHORIZED_BY_B2=true` is B2's independent performance-gate
verdict.  The controller must still enforce the Fresh A/B order, their hard
timeouts, the global task clock, B3's later atomicity/public-boundary review,
and cleanup requirements.

### Monitored result set

The three runs used the same content-addressed fixture identities already
reviewed above, the same remediated schema SHA
`aa8cb0af7b61931e51f1f71ed2e4cf0d10b178669de16807871819b330742e8b`,
PostgreSQL 16.13, warm-cache labels, `fsync=on`,
`synchronous_commit=on`, and `full_page_writes=on`.  All three result and
verifier statuses are `PASS`; all three importers returned zero, emitted the
commit marker, and reused the bound staging attestation.

| Scale | Total wall s | Import wall s | Input bytes | Final DB bytes | COPY s / rows | Durable inserts s / rows | Analyze s | Parity s |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,000 | 470.001139 | 268.347949 | 317,108,731 | 164,002,839 | 106.270762 / 250,206 | 107.717277 / 242,274 | 1.074860 | 1.262412 |
| 4,000 | 1,045.175616 | 738.936675 | 507,571,899 | 399,350,807 | 150.196810 / 1,001,072 | 337.197362 / 969,169 | 2.096969 | 4.121074 |
| 8,000 | 2,376.102825 | 1,687.537084 | 760,195,954 | 710,769,687 | 222.517797 / 1,998,473 | 1,054.606571 / 1,934,563 | 4.821018 | 9.465361 |

At 8,000 objects, total time is 39.601714 minutes, leaving 323.897175
seconds against the 45-minute gate.  The largest named group is
`folder_assignment_shape` at 158.029628 seconds (2.633827 minutes), leaving
741.970372 seconds against the 15-minute group gate.  The final all-constraint
omission check completed in 0.057805 seconds.

The monitored runs' relevant I/O/statistics deltas were:

| Scale | WAL bytes | DB active-time ms | DB read/write ms | Client read/write bytes | Temp files/bytes | Target-index scans |
|---:|---:|---:|---:|---:|---:|---:|
| 1,000 | 194,908,524 | 394,178.873 | 2,849.084 / 5,482.575 | 289,193,984 / 191,668,224 | 1 / 76,636,160 | 6,329 |
| 4,000 | 725,389,435 | 968,034.882 | 7,685.768 / 18,851.361 | 756,080,640 / 385,785,856 | 3 / 370,221,056 | 27,091 |
| 8,000 | 1,460,731,433 | 2,341,044.025 | 76,897.304 / 62,586.030 | 1,412,620,288 / 644,243,456 | 2 / 675,135,488 | 55,091 |

The target-index scan sequence is consistent with bounded target-led
validation and the P1 plans.  All after-run activity snapshots report zero
peer active backends and zero ungranted locks.

### Initial-versus-monitored logical equality

Instrumentation did not alter fixture choice, schema, counts, or logical
content.  For all three sizes, the monitored run exactly matches the earlier
run in selection SHA, fixture-manifest SHA, schema SHA, complete count vector,
complete semantic metrics, and all three digest dimensions:

| Scale | Count-vector SHA-256 | Normalized semantic SHA-256 | Stable-key-set SHA-256 | Initial = monitored |
|---:|---|---|---|---|
| 1,000 | `2d9efc1515c83b63fb495455c7a2b8985458cd9952dc5485f842f62087ea8d9b` | `3bb62a463df1eaf041f5985ee37241b2120240a28fb49f0ef84aeaf429be2e23` | `29b99d7b30aa7c3a4ec543dbd1e58e93ecb60e435d6a299c305128099f22c94d` | true |
| 4,000 | `c17d06159a44dbbd531607f32349e990fd7ff5bc9ed34a51df29071fd10d7ed8` | `cebeefcb50fd0d7b5ec8e3e0a9e811303705efaf8b9caaac0a8a625aae2da6f7` | `77c67f5fb875178c0a15e287b9a2b55c7dd4c86f6537b89fa6b2871025f12b88` | true |
| 8,000 | `b05d02b2ce4869bf2fd0cf8150ac82525fa378328f04d7dd89b5b1a39cd1f91c` | `6992476f531566f3f55295c6f55f7c3b75916474b636734eee405790c95c88ff` | `f7b0997a3cc296694dfb0063cb7a0b65c8169520cb766d902fc876f323abd0e3` | true |

The scale-8,000 actual metrics equal the fixture expectation: 8,000 input and
operational objects; 3,378 eligible; 4,622 held; 1,799,337 raw literals; 178
folders; 24,166 folder memberships; 8,000 visual bundles; 7,865 bundles with a
reference; and 7,867 locator occurrences.  Rejected, TRACE-eligible, positive
rights, remote-image decisions, current pointers, and sealed releases are all
zero.  Every integrity mismatch remains zero, and schema SHA before/after is
identical.

### Backend statement CPU and sampled peak resources

The prior CPU/peak-disk evidence gaps are closed for the decisive maximum
three rungs.  Each backend-CPU receipt is `PASS`, maps exactly 181 statements,
finds all 12 constraint groups, and reports both
`missingConstraintGroups=[]` and `unmappedConstraintStatements=[]`.
Statement elapsed time covers essentially the entire importer wall interval,
and the five-second OS monitor independently observes the same writer PID and
its normal exit.

| Scale | Statement elapsed s | Backend CPU user/sys/total s | COPY CPU s | Durable CPU s | Constraint CPU s | Analyze CPU s |
|---:|---:|---:|---:|---:|---:|---:|
| 1,000 | 265.433561 | 18.994704 / 1.777530 / 20.772234 | 7.285589 | 9.823038 | 3.411498 | 0.028338 |
| 4,000 | 736.386665 | 50.265446 / 3.999568 / 54.265014 | 9.781771 | 26.827745 | 16.978775 | 0.090478 |
| 8,000 | 1,683.400688 | 91.594346 / 7.610863 / 99.205209 | 12.811904 | 57.662897 | 27.514715 | 0.154847 |

The backend CPU OLS exponents are 0.743457424 for all importer statements,
0.263037113 for COPY, 0.833078082 for durable inserts, and 1.025868538 for
constraints.  These server-side CPU figures replace the provisional report's
client-child CPU limitation for the three points actually used by P3.

The named-group backend CPU seconds at 1,000 / 4,000 / 8,000 are:

| Group | Backend CPU seconds |
|---|---:|
| `raw_core_cycle` | 0.194188 / 1.000854 / 1.603240 |
| `folder_assignment_shape` | 1.153225 / 6.327624 / 10.351041 |
| `visual_bridge_and_locator` | 0.054219 / 0.329419 / 0.497347 |
| `rights_observation` | 0.106831 / 0.815649 / 1.260594 |
| `rights_assessment_shape_support` | 0.376848 / 2.102070 / 3.600962 |
| `rights_assessment_current_leaf` | 0.032661 / 0.156662 / 0.237232 |
| `provider_policy` | 0.086511 / 0.501470 / 0.773986 |
| `delivery_parent_validation` | 0.472081 / 1.846684 / 3.052222 |
| `delivery_rights_validation` | 0.453850 / 1.777491 / 2.718074 |
| `delivery_policy_validation` | 0.402197 / 1.695980 / 2.798211 |
| `delivery_history_and_rule` | 0.078879 / 0.424855 / 0.621771 |
| `final_all_omission_check` | 0.000008 / 0.000017 / 0.000035 |

The persistent monitor summaries record 5.0-second sampling, observe both the
writer and its exit, and retain the following maxima:

| Scale | Samples | Peak backend RSS bytes | Peak DB bytes | Peak PGDATA allocated bytes | Peak PGDATA logical bytes |
|---:|---:|---:|---:|---:|---:|
| 1,000 | 60 | 1,009,762,304 | 358,611,991 | 1,515,515,904 | 1,494,564,183 |
| 4,000 | 134 | 1,068,859,392 | 789,609,495 | 1,992,167,424 | 1,925,578,071 |
| 8,000 | 263 | 1,086,816,256 | 1,360,010,263 | 2,676,232,192 | 2,579,873,111 |

These are explicitly sampled peaks rather than a claim of continuous
nanosecond maxima.  They are nevertheless a defined, consistent measurement
at the requested five-second cadence and close the prior absence of any peak
resource receipt.

The scale-50/250 historical receipts still expose only client-child CPU.  B2
does not relabel those fields.  That limitation is non-blocking because the
controller reran the complete decision set used for the specified maximum-
three fit with backend statement CPU and peak monitoring; no 50/250 datum is
used in the final fit or full-population projection.

### Exact monitored OLS results for the 04/05 receipts

B2 applied the previously declared natural-log OLS method without changing
the point set or mixing initial and monitored runtimes.  The following values
are suitable for direct use in the machine/human scale receipts.  `OLS full`
is `exp(alpha + beta * ln(15923))`; `8k-anchor` is
`t8000 * (15923/8000)^beta`.

| Metric | 1k / 4k / 8k wall s | OLS beta | OLS full s | 8k-anchor full s |
|---|---|---:|---:|---:|
| Total replay | 470.001139 / 1,045.175616 / 2,376.102825 | 0.750318118554367 | 3,530.517982014927 | 3,982.552489738611 |
| Import | 268.347949 / 738.936675 / 1,687.537084 | 0.862308259314135 | 2,788.696071663830 | 3,055.113614728211 |
| COPY | 106.270762 / 150.196810 / 222.517797 | 0.340272389286002 | 264.104200324707 | 281.244505756055 |
| Durable inserts | 107.717277 / 337.197362 / 1,054.606571 | 1.057991204740965 | 1,856.407395218733 | 2,184.544905838631 |
| Combined named constraints | 48.073639 / 239.870203 / 384.410882 | 1.022590076085128 | 854.452470771417 | not used |
| `raw_core_cycle` | 2.401542 / 17.267301 / 24.899010 | 1.167302242629070 | 66.390144800808 | 55.607000353207 |
| `folder_assignment_shape` | 14.339426 / 80.159357 / 158.029628 | 1.166530514595369 | 371.540159407119 | 352.740405619024 |
| `visual_bridge_and_locator` | 0.798809 / 4.784737 / 6.796247 | 1.066984307807328 | 16.547839108155 | 14.165372854704 |
| `rights_observation` | 2.308174 / 12.399924 / 12.611877 | 0.873238846415225 | 29.108877204760 | 23.004950380021 |
| `rights_assessment_shape_support` | 5.444886 / 30.708232 / 52.165013 | 1.109720484323163 | 123.221749108725 | 111.973050766773 |
| `rights_assessment_current_leaf` | 0.248402 / 2.704366 / 3.598544 | 1.347942866852875 | 11.796629739206 | 9.100683151798 |
| `provider_policy` | 1.340211 / 8.771429 / 11.560464 | 1.081787194851314 | 29.420998903432 | 24.342166087961 |
| `delivery_parent_validation` | 8.345858 / 27.698326 / 48.309048 | 0.847379362933877 | 87.648484419617 | 86.564485308419 |
| `delivery_rights_validation` | 6.506917 / 27.386344 / 31.204781 | 0.794306767689161 | 63.772933225030 | 53.909730355988 |
| `delivery_policy_validation` | 5.655180 / 24.461918 / 28.241692 | 0.813829955526497 | 58.506983046722 | 49.450751432236 |
| `delivery_history_and_rule` | 0.683892 / 3.527473 / 6.936773 | 1.124035117593021 | 15.668976103265 | 15.037333005995 |
| `final_all_omission_check` | 0.000342 / 0.000796 / 0.057805 | 2.201642051147251 | 0.087256191548 | 0.263095287864 |

The P3 complexity threshold applies to the total replay fit; the separate
named-group gate is an absolute 900-second ceiling.  B2 nevertheless reviewed
every group slope as a diagnostic.  Two require explanation:

- `rights_assessment_current_leaf` has beta 1.347942867, driven by the very
  small 0.248402-second 1,000 baseline and the 1,000-to-4,000 jump.  Its most
  recent 4,000-to-8,000 exponent is only 0.412122884, the 8,000 observation is
  3.598544 seconds, its OLS full projection is 11.796630 seconds, and the P1
  index plan proves the target-led mechanism.  This is not the former
  quadratic blocker and does not approach the group budget.
- `final_all_omission_check` is deliberately a no-op after all named groups.
  Its first two values are 0.342 and 0.796 milliseconds, so a 57.805-
  millisecond scheduling/statement-logging observation at 8,000 yields a
  numerically large but complexity-meaningless exponent.  Even its anchored
  full projection is 0.263096 seconds.

The durable-insert latest adjacent exponent is 1.645039736, although its
three-point OLS exponent is 1.057991205.  B2 does not hide that variability.
The same latest-pair sensitivity applied to total replay gives exponent
1.184851898 and a 15,923 projection of 5,371.045405 seconds, still below the
5,400-second hard gate, though with only 28.954595 seconds of projection
headroom.  Fresh A therefore needs the controller's strict 90-minute hard
stop; this sensitivity is a risk signal, not a P3 No-Go under the specified
three-point fit and observed 8,000 budgets.

### Closing B2 Go/No-Go

| P3 condition in B2 scope | Evidence | Verdict |
|---|---|---|
| 8,000 completes | 2,376.102825 s | PASS |
| Largest-three total beta | 0.750318119 <= approximately 1.25 | PASS |
| Any named group <= 900 s | max 158.029628 s | PASS |
| Full projection <= 5,400 s | OLS 3,530.517982 s; anchored 3,982.552490 s | PASS |
| Counts/digests/schema | exact expected and initial/monitored equality | PASS |
| Backend stage/group CPU | 3/3 receipts, no missing/unmapped statement | PASS |
| Peak resource monitoring | 3/3 five-second monitor receipts | PASS |
| Queue B P0/P1 in B2 scope | none | PASS |

Accordingly, B2's final independent verdict is:

```text
B2_CLOSING_REVIEW=PASS
B2_RESIDUAL_P0=NONE
B2_RESIDUAL_P1=NONE
B2_PERFORMANCE_GO=true
PERFORMANCE_BUDGET_MET=true
FULL_REPLAY_AUTHORIZED_BY_B2=true
```
