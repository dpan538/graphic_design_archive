# External model purge

`EXPLORATION_EXTERNAL_MODEL_POLICY=DENY_BY_DEFAULT`

`APPROVED_EXTERNAL_RESEARCH_MODEL_COUNT=0`

The active Round 7 model registry, downloader/loader paths, dense encoder, embedding index, ranking helpers, and benchmark/generation entry points were removed with `scripts/exploration-v49-nlp/`. The object-affinity and discovery execution paths were also removed with `scripts/exploration-v49-similarity/` and `scripts/exploration-v49-analysis/`.

The frontend manifest contained no Transformers, Sentence Transformers, Hugging Face, FlagEmbedding, fastText, FAISS, HNSW, external embedding, or vector-database dependency. No dependency was removed because none had been added to a manifest; every existing dependency supports unrelated frontend, Context, or Spacetime functionality.

The three package commands that exposed the superseded discovery analysis were removed. New commands execute only local structural tests and deterministic static guards.

Task-owned cleanup removed 11,077,291 bytes from the documented Round 7 `/private/tmp` virtual environment, preflight, schema, empty runtime directory, and 23 self-test receipts. No global cache or ambiguous path was touched. Remaining task-owned runtime bytes: zero.

No model was downloaded or executed in this reset round.
