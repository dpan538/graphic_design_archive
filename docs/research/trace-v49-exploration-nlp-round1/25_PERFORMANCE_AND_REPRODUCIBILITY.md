# Performance and reproducibility

## Evidence state

`DOCUMENT_STATE=FINAL_EVIDENCE_BOUND_AUDIT_ONLY`

Timing and memory values are observational. They do not relax corpus,
licensing, leakage, or epistemic gates and are not service-level promises.

## Hardware preflight

The research host is an Apple M1 MacBook Pro with eight CPU cores, eight GPU
cores, and 16 GiB unified memory. PyTorch is executed on CPU. Its MPS backend is
built but unavailable to this process; CUDA is unavailable and dedicated VRAM
is not applicable. Dense models are loaded and released sequentially so their
resident weights do not overlap.

Storage was preflighted before each official snapshot download. The two
selected execution snapshots occupy approximately 1.20 GB and 1.14 GB of
required files respectively. Larger, pickle-bearing, or conditional candidates
were not downloaded merely to expand the benchmark.

## Isolated runtime

The executed environment is `/private/tmp/trace-nlp-v1-venv` with:

| Dependency | Exact version |
| --- | --- |
| Python | 3.13.5 |
| PyTorch | 2.12.0 |
| Transformers | 5.12.0 |
| tokenizers | 0.22.2 |
| NumPy | 2.4.4 |
| SciPy | 1.17.1 |
| huggingface-hub | 1.19.0 |
| safetensors | 0.8.0 |
| accelerate | 1.14.0 |
| psutil | 7.0.0 |

Sentence Transformers, scikit-learn, and a third-party BM25 package are not
assumed unless the final runtime receipt explicitly lists them. The lexical
implementations are versioned repository code.

## Execution architecture

```text
7,995 governed public documents
  -> aspect-available query cohort
  -> deterministic length buckets
  -> exact pinned tokenizer/template
  -> bounded model-input head truncation
  -> one locally loaded encoder
  -> L2-normalized 1,024-dimensional rows
  -> blockwise exact top-k search
  -> bounded aggregate/top-k receipts
```

Canonical IDs are restored after length-bucket encoding. Missing aspects use an
explicit availability mask and cannot become queries or neighbors. No ANN,
FAISS, HNSW, vector database, full pair matrix, or full ranking matrix is
introduced at 7,995 records.

Lexical baselines likewise retain bounded top-k results and aggregate receipts;
they do not alter Search v49.

## Measurement policy

Each model/aspect receipt records:

- model load time;
- corpus/tokenizer-census and encoding time;
- available/unavailable documents and exact query-ID hash;
- documents and tokens per second;
- embedding and exact-index bytes;
- peak process RSS and applicable VRAM;
- exact-search query P50/P95;
- batch size and batch-sensitivity observations;
- tokenizer truncation counts/rates; and
- bounded ranking hash.

Final aggregate values:

```text
LEXICAL_INDEX_BUILD_MS=7761.928794032428
DENSE_CORPUS_ENCODING_MS=931534.216
DENSE_DOCUMENTS_PER_SECOND=50.72170102659975
DENSE_TOKENS_PER_SECOND=N/A_NOT_RECORDED_BY_HARDENED_ENCODING_RECEIPT
DENSE_EMBEDDING_BYTES=32747520_PER_FULL_PUBLIC_ID_MATRIX
DENSE_INDEX_BYTES=32747520
DENSE_EXACT_QUERY_P50_MS=1.1305452485430578
DENSE_EXACT_QUERY_P95_MS=2.408029649004674
NLP_PEAK_RAM_BYTES=3112517632
NLP_PEAK_VRAM_BYTES=N/A
```

## Determinism levels

The receipt separates:

1. **semantic determinism** — same frozen corpus roles, normalized hashes,
   templates, masks, and parameters;
2. **ranking determinism** — same object IDs, availability, dimensions, token
   counts, and bounded top-k ordering/hash; and
3. **floating-point observation** — small backend-dependent differences that
   may exist without changing the declared ordering.

Seeds are recorded only when a probe or sampling diagnostic needs them. Seeded
randomness affects no corpus, embedding, neighbor, or score. Timestamps,
filesystem paths, process IDs, cache state, and timing fields are excluded from
deterministic result material.

## Replay policy

Each full model/aspect run is repeated where computationally practical.
Separate local output locations must agree on public IDs, preprocessed text
hashes, token counts, embedding dimensions, availability masks, and bounded
ranking hashes. A skipped replay must identify the hardware/resource reason and
cannot claim byte-identical floating-point output.

```text
FULL_RUN_REPLAY_COUNT=2
SEMANTIC_RECEIPT_EQUALITY=PASS_FOR_D1_TITLE_A_B_AND_D3_TITLE_A_B
BOUNDED_RANKING_HASH_EQUALITY=PASS_FOR_D1_TITLE_A_B_AND_D3_TITLE_A_B
FLOATING_POINT_EXCEPTION_COUNT=0
```

## Reproducibility pins

Every run binds the source commit, frozen input artifact hashes, public cohort
hash, corpus policy and field registry hashes, normalization and aspect
versions, boilerplate registry, exact code revision, model and tokenizer
revision, artifact hashes, input mode, template, pooling, normalization, dtype,
quantization, aspect, token cap/census, batch size, query cohort hash, and
bounded output hash.

The final verifier must prove that no weight, embedding array, token array,
full corpus, or full pair/neighbor matrix appears in the committed package.
