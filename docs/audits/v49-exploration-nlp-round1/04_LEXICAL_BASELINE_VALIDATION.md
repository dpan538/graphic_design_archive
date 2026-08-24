# Lexical baseline validation

## Evidence state

`DOCUMENT_STATE=SEALED`

The lexical baselines are isolated research implementations and do not import,
modify, or replace Search v49.

## Declared methods

| ID | Method | Frozen parameters |
| --- | --- | --- |
| `NLP-L0` | fielded BM25F-style retrieval | registered fields, positive Robertson IDF, explicit field weights/length normalization |
| `NLP-L1` | character TF-IDF cosine | Unicode character n-grams 3--5 |
| `NLP-L2` | word TF-IDF cosine | deterministic Unicode lexer, word n-grams 1--2 |
| `NLP-L3` | lexical hybrid | equal reciprocal-rank fusion of L0/L1, `k=60`, fused before top-k truncation |

No hidden field flattening or selected production weight exists. Equal-field
results are required. Each aspect uses only its available query cohort; missing
subject or source-narrative rows cannot enter as empty queries.

## Required validations

- all 7,995 title documents are indexed;
- subject and source-narrative denominators equal their available aspects;
- public IDs are sorted/unique and no held ID enters;
- duplicate titles remain distinct documents;
- BM25F field length, saturation, IDF, and field weighting reconcile;
- char/word vocabularies and IDF use deterministic ordering;
- self-neighbors are excluded;
- full top-50 is retained locally, while committed outputs are bounded;
- two runs agree on query IDs and bounded ranking hashes; and
- same-source, known-item, metadata-holdout, and robustness evaluations use the
  mechanically frozen registries and masks.

## Full-corpus result receipt

```text
LEXICAL_MODEL_COUNT=4
BM25F_FULL_CORPUS=PASS
CHAR_NGRAM_FULL_CORPUS=PASS
WORD_NGRAM_FULL_CORPUS=PASS
LEXICAL_HYBRID_FULL_CORPUS=PASS

BEST_LEXICAL_MODEL_ID=NONE
BEST_LEXICAL_KNOWN_ITEM_RECALL_AT_10=N/A_NO_LEXICAL_MODEL_SELECTED
LEXICAL_SOURCE_LEAKAGE_BLOCKER_COUNT=N/A_NOT_SEPARATELY_FROZEN
LEXICAL_INDEX_BUILD_MS=7761.928794032428
LEXICAL_BOUNDED_RANKING_SHA256=N/A_NO_LEXICAL_MODEL_SELECTED
```

The “best” label, if used, is task-specific. No aggregate overall accuracy may
combine identity retrieval, nonexistent cross-language pairs, metadata proxy
alignment, leakage, and object-semantic review.

## Pair and holdout boundary

Task A has three externally verified duplicate-import identity pairs; Task B
has zero verified language/title variants. The 309 registered controls test
leakage and are not historical non-relations. Same-title stress pairs cannot
become positives.

Metadata holdout must report original, target-label-masked, and all-governed-
label-masked variants with target distributions and broad-class baselines.

## Final validation

```text
NLP_LEXICAL_BASELINE_TESTS=PASS
LEXICAL_RESULT_TSV_ROW_COUNT=12
LEXICAL_RESULT_TSV_SHA256=494af726e80b64c64da10beb813bb01b26730be96d85a396a9ebcaf534d59adc
LEXICAL_RUN_RECEIPT_SHA256=10fee55f74b0f712af2ab1950d1ae9d6fa717d76ef79de0b73a4ec7de0dfbb5e
```
