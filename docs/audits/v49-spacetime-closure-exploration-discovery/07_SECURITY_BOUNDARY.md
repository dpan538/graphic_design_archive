# Security and epistemic boundary

## Public/private data

The authoritative Exploration cohort contains 7,995 public objects. All 7,928 held objects are excluded from committed statistics. Candidate/internal data may be read to compute aggregate validation receipts, but committed outputs do not contain held IDs, held titles, internal UUIDs, private URLs, restricted raw text, raw private folder tokens, normalized object rows, or raw source rows.

The 15-case pathological TSV is the sole approved exception for public stable object IDs. It contains one public ID per case, or one sorted public pair for the cross-source/context case, solely to reproduce regressions. Held count is zero and no title or raw private value appears.

## Automated scan

The verifier safety-scans every TSV and every JSON in the scoped research/raw directories, rejects unexpected files, and reports:

```text
HELD_IDENTIFIER_COUNT=0
INTERNAL_UUID_COUNT=0
RAW_PRIVATE_IDENTIFIER_COUNT=0
TITLE_KEY_COUNT=0
URL_COUNT=0
```

The private-ID adversary accepts safe prose such as “folder membership” and rejects actual prefixed private tokens. No broad case-insensitive fragment match is used.

## Materialization boundary

```text
FULL_PAIR_MATRIX_COMMITTED=false
PAIR_ROWS_COMMITTED=false
NORMALIZED_OBJECT_ROWS_COMMITTED=false
OBJECT_VECTOR_ROWS_COMMITTED=false
FULL_SOURCE_CORPUS_IN_CLIENT_BUNDLE=false
```

Exact pair analysis is streamed/aggregated. The object-level missingness and curatorial-support vectors are hashed and discarded. Large matrices do not enter Git.

## Epistemic boundary

Every signal has `historical_relation=false` and `semantic_relation=false`. Curation describes project structure; frequency and concentration describe the current release; rarity is not importance; missingness states are not historical absence; geography is not an object coordinate; conditional rates/lift are not probabilities; and no creator-intent or influence claim is made.

Context and Spacetime remain the governed truth sources. Exploration consumes them without rewriting their terms, time semantics, geography registry, or projection artifacts.
