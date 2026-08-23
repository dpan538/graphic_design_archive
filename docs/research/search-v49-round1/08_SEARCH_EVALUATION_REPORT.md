# Search Evaluation Report

## Method

The reproducible suite contains 271 real-record-derived queries: 74 tuning and 197 held-out. The held-out split is selected by SHA-256, with approximately three quarters held out. It covers exact title/ID, case, punctuation, whitespace, Latin diacritics, unique prefix, unique middle substring, substitution, transposition, ordered/out-of-order/incomplete multi-token, real Han/bilingual partials, verified no-results, and ambiguous short-query stress.

The OLD comparator reproduces current behavior: lowercase raw-title substring, then title/ID order. NEW is `v49-lexical-fuzzy-1`. Positive mechanical cases choose actual public records and, where necessary, unique predicates/tokens. Ambiguous short cases are excluded from target metrics.

This benchmark measures known-item recovery under deterministic query transformations. Its 100% NEW score must not be presented as a human judgment of general topical relevance. The separately reviewed noise candidates are in `09_FAILURE_ANALYSIS.md`.

## Held-out quality

| Metric | OLD | NEW |
|---|---:|---:|
| Positive queries | 173 | 173 |
| Top-1 | 31.79% | 100.00% |
| Top-5 | 32.37% | 100.00% |
| Recall@10 | 32.37% | 100.00% |
| MRR@10 | 0.3191 | 1.0000 |
| No-result precision (12 held-out negatives) | 100.00% | 100.00% |
| Prefix recovery | 48.00% | 100.00% |
| Typo recovery | 0.00% | 100.00% |
| Multilingual/diacritic recovery | 18.75% | 100.00% |

The improvement is meaningful and concentrated exactly where literal substring fails: whitespace/punctuation normalization, diacritic fallback, token order, incomplete tokens, and edit/transposition errors.

## Performance

Environment: Node v22.21.0, Unicode 16.0, Darwin arm64. These are local single-process measurements, not deployed Vercel telemetry.

| Measure | Result |
|---|---:|
| Artifact read | 3.02 ms |
| JSON parse | 2.89 ms |
| Hydration | 21.13 ms |
| Cold typo query after hydration | 88.83 ms |
| NEW compute P50 | 41.90 ms |
| NEW compute P95 | 56.73 ms |
| NEW maximum | 189.31 ms |
| OLD compute P50 | 0.60 ms |
| OLD compute P95 | 1.01 ms |
| Serialization P95 | 0.029 ms |
| End-to-end deterministic index build | 1,304.74 ms |
| Process RSS after suite + GC | 183,074,816 bytes |
| Process heap used after suite + GC | 37,988,760 bytes |

The selected design has no separate candidate-generation stage: the fixed candidate set is all 7,995 public documents. The measured NEW time is ranking over that set. P50 and P95 pass the provisional 75/200 ms computation targets. The 189.31 ms maximum is below 200 ms but showed scheduler/JIT variability across runs; deployed API P95 should be monitored against the 500 ms provisional target.

## Artifact

| Property | Result |
|---|---:|
| Documents | 7,995 |
| Held excluded | 7,928 |
| Raw bytes | 1,435,371 |
| Gzip bytes | 256,941 |
| Index SHA-256 | `35a6b7e1f8b749fca0ebfda9cf84f265de58d69fe6ef2bac0a4a2a9d263b1522` |
| Consecutive rebuild checksum equality | PASS |

## Interpretation

The full scan costs more CPU than literal substring but remains within launch targets and is much simpler than a postings index. No-result precision stayed at 100% because every query token must match. The principal remaining quality issue is result-set breadth for very short/common prefixes, not displacement of the mechanically expected record.

Raw cases are `03_SEARCH_QUALITY_COMPARISON.tsv`; machine-readable aggregates are `../../audits/v49-search-fuzzy-round1/benchmark-results.json`.
