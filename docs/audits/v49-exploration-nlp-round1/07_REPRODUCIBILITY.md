# Reproducibility validation

## Evidence state

`DOCUMENT_STATE=SEALED`

## Deterministic inputs

Every run binds:

- source commit `580587a74f400d8a04d995937f4efb31e6621dd8`;
- all frozen source-artifact and projection hashes;
- the exact 7,995-object public-ID hash;
- corpus policy `trace-nlp-corpus-v1` and SHA-256
  `e20d6de00345fce6f925b4ee1ba5c89be7ee4b859e8bda0432bcd6c964a03f16`;
- field registry `trace-nlp-text-field-registry-v1` and SHA-256
  `b70c98f8a52de2ae5bbaf5d2d69db85381bfa59a0d07722df0823018d2aec3b6`;
- normalization, aspect-document, and boilerplate versions;
- code/implementation version;
- model/tokenizer revision and verified artifact hashes;
- exact aspect, availability mask, input mode, template, pooling,
  normalization, dtype, quantization, cap, and token census; and
- bounded result/ranking hashes.

## Environment

The isolated `/private/tmp/trace-nlp-v1-venv` runtime is Python 3.13.5 with
PyTorch 2.12.0, Transformers 5.12.0, tokenizers 0.22.2, NumPy 2.4.4, SciPy
1.17.1, huggingface-hub 1.19.0, safetensors 0.8.0, accelerate 1.14.0, and
psutil 7.0.0. Execution is CPU-only on Apple M1; MPS and CUDA are unavailable.

## Replay criteria

Two runs, where computationally practical, must agree on:

- corpus IDs and available-aspect query IDs;
- preprocessed text hashes;
- token counts and truncation receipts;
- embedding dimensions and availability masks;
- lexical/index parameters; and
- bounded top-k ordering/hash.

Timings, process high-water memory, paths, timestamps, and cache state are
excluded from deterministic equality. Small floating-point differences may be
reported only if the declared top-k ordering remains identical.

```text
FULL_RUN_REPLAY_COUNT=2
CORPUS_ID_HASH_EQUALITY=PASS
PREPROCESSED_HASH_EQUALITY=PASS
TOKEN_COUNT_EQUALITY=PASS
EMBEDDING_DIMENSION_EQUALITY=PASS
BOUNDED_RANKING_HASH_EQUALITY=PASS
FLOATING_POINT_EXCEPTION_COUNT=0
```

## Randomness and ordering

Canonical documents are sorted by public ID. Dense batches are sorted by full
token length and public ID, then restored to canonical order. Exact top-k ties
use deterministic public-ID ordering. A seed may govern probe folds or bounded
sampling, but affects no corpus, embedding, neighbor, or score.

```text
RANDOMNESS_AFFECTS_CORPUS=false
RANDOMNESS_AFFECTS_EMBEDDING=false
RANDOMNESS_AFFECTS_NEIGHBOR=false
RANDOMNESS_AFFECTS_SCORE=false
```

## Local-artifact policy

Full documents and embeddings may exist only under `.local/trace-nlp-v1/` or
an explicit temporary root. They are not manifest inputs except through
bounded hashes/receipts and must not be staged.

## Final verification

```text
NLP_REPRODUCIBILITY_TESTS=PASS
RUN_RECEIPT_COUNT=20
RUN_RECEIPT_FAILURE_COUNT=0
REPRODUCIBILITY_RECEIPT_SHA256=d4deddad6a790d3a60103e5d09cdf7713c754bba465c52aac9787ea108037fc3
```

A non-replayed expensive run must carry an explicit limitation. It cannot claim
full byte reproducibility across hardware.
