# Performance validation

## Evidence state

`VALIDATION_STATE=SEALED_PRECOMMIT_PASS`

The benchmark must measure the correct bounded architecture before making any
interactive-runtime claim. Timings and process memory are observational and
excluded from deterministic result hashes. Runs A and B may differ in those
fields while their canonical deterministic payloads must agree.

## Workload

```text
PUBLIC_OBJECT_COUNT=7995
EXHAUSTIVE_PAIR_COUNT=31956015
TOP_K_RETAINED_PER_OBJECT=50
PAIR_ROWS_MATERIALIZED=0
FULL_PAIR_MATRIX_COMMITTED=false
FULL_PAIR_MATRIX_IN_CLIENT=false
```

Scalar model evaluation streams unordered pairs and retains only bounded
per-object heaps plus aggregates/hashes. M8 remains a non-scalar object-local
Pareto baseline. Candidate generation is separately evaluated against the
exhaustive scalar references.

## Measurement distinctions

- Candidate-index serialized bytes measure the deterministic encoded index.
- Candidate-index/model-context heap follows the declared Python tracing
  replay and must name native allocations it excludes.
- Peak RSS is the process-lifetime operating-system high-water value.
- Exhaustive benchmark time covers the declared scalar model suite.
- Object-local P50/P95 covers deterministic, explanation-bearing queries.
- Temporary evidence size covers bounded summaries/specifications, never pair
  rows.

## Final measurements

| Metric | Final value |
| --- | ---: |
| Candidate-index build ms | 532.542624976486 |
| Candidate-index bytes | 2,866,456 |
| Candidate-index/model-context heap bytes | 159,714,072 |
| Interaction registry/posting build ms | 61,253.70875000954 |
| Normalized public load ms | 11,228.36379200453 |
| Exhaustive model benchmark ms | 242,356.32762307068 |
| Object-local query P50 ms | 124.96837499202229 |
| Object-local query P95 ms | 365.8331037295284 |
| Peak heap bytes | 159,714,072 |
| Peak RSS bytes | 899,448,832 |
| Run A total elapsed ms | 715,879.1515830089 |
| Authored TSV bytes | 918,719 |

The final narrative must also report candidate pool reduction, zero/near-full
counts, candidate-index/runtime observations, the deterministic payload SHA,
and Run A/B equality. Performance cannot waive recall, lineage, explanation,
security, or epistemic failures.

Run A and Run B timing-bearing file digests differ, while their deterministic
payloads are byte-equal at
`c4ba0106e4a361c52f56106f86aa6b4cc360ff48ecb26019fc3d248aac9fde8a`.
The complete bounded audit raw directory contains 13 JSON receipts and no pair
rows. The independent verifier passes all performance, bounded-artifact, and
no-matrix gates; the protected-product regressions and production build also
pass.
