# Performance and architecture

## Evidence state

`DOCUMENT_STATE=SEALED_PRECOMMIT_PASS`

This document records authoritative Run A performance and deterministic A/B
equality. It does not extrapolate these observations into a service-level
promise. Run B used a separate cache/output location and produced different
timings but exactly the same deterministic payload as Run A.

## Architecture under evaluation

The research implementation uses a bounded two-stage design:

```text
7,995 governed/approved public records
  -> deterministic inverted candidate index
  -> object-local candidate pool
  -> separately chosen analysis scorer or Pareto profiler
  -> affinity profile + comparability profile
  -> deterministic explanation
```

Candidate postings may increase recall but never become score credit merely
because they retrieved a record. Raw curated memberships occupy a recall-only
namespace. Governed direct postings, candidate-only geography-class fallback,
and the exact approved high-information interaction postings are hashed into
the candidate-index receipt. Scoring recomputes independent evidence from the
normalized public cohort.

## Exhaustive reference design

For research evaluation, the benchmark visits exactly 31,956,015 unordered
public-object pairs for each scalar reference family. It retains bounded top-50
heaps per object, aggregate distributions, and hashes; transient pair values
are discarded. The M8 non-scalar baseline is evaluated as deterministic Pareto
profiles and is not collapsed to an undocumented scalar.

The sealed implementation proves:

```text
PAIR_ROWS_MATERIALIZED=0
FULL_PAIR_MATRIX_COMMITTED=false
FULL_PAIR_MATRIX_IN_CLIENT=false
RANDOMNESS_AFFECTS_CANDIDATE_SET=false
RANDOMNESS_AFFECTS_AFFINITY=false
```

The exhaustive rankings are offline reference evidence. They are not a
request-time architecture and are not committed as object-pair rows.

## Measurement policy

Wall-clock timings are observational and excluded from deterministic hashes.
Deterministic receipts bind inputs, parameters, bounded results, and ranking
hashes. A second run must reproduce the deterministic payload SHA even though
timings and process high-water memory may differ.

The performance receipt distinguishes:

- candidate-index construction time;
- serialized candidate-index bytes;
- Python-traced peak allocation for the declared index/model-context replay;
- process-lifetime peak resident set size;
- complete exhaustive model-suite elapsed time;
- object-local query latency over deterministic explanation-bearing queries;
- top-k heap maintenance within the exhaustive stage; and
- temporary bounded evidence size.

Python `tracemalloc` heap and operating-system RSS are not interchangeable.
Native allocations excluded from a `tracemalloc` policy must be named rather
than silently treated as measured Python heap.

## Final measurement receipt

| Metric | Final value | Interpretation |
| --- | ---: | --- |
| Candidate-index build | 532.542624976486 ms | elapsed milliseconds |
| Candidate-index serialized bytes | 2,866,456 | deterministic encoded index size |
| Candidate-index/model-context traced heap | 159,714,072 bytes | Python-traced peak under the declared replay policy |
| Exhaustive model benchmark | 242,356.32762307068 ms | elapsed milliseconds for the complete scalar suite |
| Object-local query P50 | 124.96837499202229 ms | milliseconds, explanation-bearing queries |
| Object-local query P95 | 365.8331037295284 ms | milliseconds, explanation-bearing queries |
| Peak RSS | 899,448,832 bytes | process-lifetime high-water value |
| Run A total elapsed | 715,879.1515830089 ms | complete authoritative benchmark process |
| Authored TSV bytes | 918,719 | 11 bounded research tables; no pair rows |

Run A file SHA-256 begins `d42fdcc`; Run B file SHA-256 begins `810b4888`.
Their distinct file digests reflect excluded timing observations. After the
declared timestamp/performance removal, their canonical payloads are byte-equal
and both hash to
`c4ba0106e4a361c52f56106f86aa6b4cc360ff48ecb26019fc3d248aac9fde8a`.

## Candidate-pool performance

For each CG-CUR variant, `11_CANDIDATE_RECALL_RESULTS.tsv` reports pool
P50/P90/P95/P99/MAX, reduction against 7,994 possible other objects,
zero-candidate count, near-full-corpus count, generation runtime, index bytes,
index heap, and exhaustive recall at 10, 20, and 50 for every shortlisted
reference model.

The selected candidate architecture meets the declared rule in its analysis
receipt: minimum recall@20 of at least 0.98 with a materially reduced pool. A
miss would remain a documented trade-off, never grounds to change the reference
denominator or hide near-full pools.

The authoritative selection is CG-CUR-4. Pool P50/P90/P95/P99/MAX is
3,008/3,608/3,662/5,644/5,991 against 7,994 possible other objects. There are
zero empty pools and zero near-full pools. Minimum recall at 10/20/50 is
0.9998499061913696/0.9995809881175735/0.9974158849280801; mean recall is
0.9998999374609131/0.9997081509276632/0.9982472378569941. The recall@20 target
is met without weakening its exhaustive denominator.

All 11 TSVs imported, inspected, formula/error-scanned, rendered, and passed
visual review. Their row counts are 64/9/25/72/15/72/648/40/15/864/47 in the
required file order. These are bounded evidence projections, not pair rows.

## Future runtime implications

The research design supports a future interactive object-local tool only if
candidate retrieval stays public-only, deterministic, bounded, and separate
from scoring. This round does not install the candidate index in the database,
ship it to the browser, add an API, or promise a latency service level.

No performance observation can override lineage, missingness, explanation,
security, or epistemic gates. A faster method that double-scores a source fact,
admits held data, or requires a pair matrix is ineligible.
