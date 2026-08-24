# Dense model validation

## Evidence state

`DOCUMENT_STATE=SEALED`

All inference occurs locally/offline after exact official snapshot
verification. No archive text is sent to a hosted service.

## Execution candidates

| ID | Model | Revision | Mode requirements | Dimension |
| --- | --- | --- | --- | ---: |
| `NLP-D1` | Qwen3-Embedding-0.6B | `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` | last non-padding pooling; L2; exact official asymmetric instruction or explicitly named plain symmetric diagnostic | 1,024 |
| `NLP-D3` | multilingual-e5-large-instruct | `274baa43b0e13e37fafa6428dbc7938e62e5c439` | attention-mask mean pooling; L2; exact official asymmetric instruction or explicitly named plain symmetric diagnostic | 1,024 |

Both use verified safetensors, `trust_remote_code=false`, CPU float32
execution, and one active model at a time. `NLP-D2`, `NLP-S1`, `NLP-D4`, and
`NLP-LID1` do not execute without their separate gates.

## Corpus and tokenizer checks

Before encoding, each model/aspect must prove:

- exactly 7,995 canonical input document identities;
- an aspect-available encoding/query cohort and explicit unavailable mask;
- policy, registry, normalization, model, and tokenizer hashes;
- full prepared-input token census;
- the smaller official/governed cap;
- deterministic `(full token count, public ID)` length buckets;
- canonical ID order restored after encoding;
- normalized 1,024-dimensional output for available rows; and
- no held, empty/unavailable, or self candidate in exact top-k.

The base corpus is never truncated. Model-input-only head truncation and
removed-token aggregates are reported by model/aspect.

## Exact-search boundary

At 7,995 objects, blockwise exact cosine top-k is the reference. No ANN,
FAISS, HNSW, vector database, full cosine matrix, or committed full neighbor
matrix is authorized.

## Result receipt

```text
DENSE_MODEL_CANDIDATE_COUNT=4
DENSE_MODEL_FULL_CORPUS_COUNT=2
DENSE_MODEL_PILOT_ONLY_COUNT=0

NLP_D1_FULL_CORPUS=PASS
NLP_D3_FULL_CORPUS=PASS
NLP_D1_ASPECT_COUNT=1
NLP_D3_ASPECT_COUNT=3

DENSE_MODEL_SHORTLIST_COUNT=0
DENSE_MODEL_SHORTLIST_IDS=NONE
BEST_DENSE_KNOWN_ITEM_RECALL_AT_10=N/A_NO_MODEL_SELECTED
BEST_DENSE_BOUNDED_RANKING_SHA256=N/A_NO_MODEL_SELECTED
```

Known-item recall demonstrates representation consistency only. A full-cohort
run does not by itself establish semantic validity or shortlist eligibility.

## Replay and commit validation

```text
DENSE_SEMANTIC_RECEIPT_EQUALITY=PASS_EXACT_D1_AND_D3_TITLE_A_B
DENSE_BOUNDED_RANKING_HASH_EQUALITY=PASS
NLP_DENSE_MODEL_TESTS=PASS
MODEL_WEIGHT_FILES_COMMITTED=0
FULL_EMBEDDING_MATRIX_COMMITTED=false
FULL_NEIGHBOR_MATRIX_COMMITTED=false
```

An incomplete run is reported as pilot-only or not run; it is never
extrapolated to the full cohort.
