# Changed-files receipt

## Evidence state

`DOCUMENT_STATE=SEALED`

This receipt was regenerated from the final scoped Git diff immediately before
sealing. The inventory below is the authoritative changed-file list.

## Allowed changed paths

Only these scoped paths are expected:

```text
scripts/exploration-v49-nlp/
docs/research/trace-v49-exploration-nlp-round1/
docs/audits/v49-exploration-nlp-round1/
PROJECT_LOG.md
```

`PROJECT_LOG.md` may receive only the compact Round 7 status update. Any other
path requires explicit review and is presumed out of scope.

## Expected research package

The research directory must contain exactly 28 required files: 11 Markdown
documents and 17 TSVs. No extra file may hide a raw corpus, model artifact, or
pair matrix.

```text
RESEARCH_FILE_COUNT=28
RESEARCH_MARKDOWN_COUNT=11
RESEARCH_TSV_COUNT=17
RESEARCH_UNEXPECTED_FILE_COUNT=0
```

## Expected audit package

The audit directory must contain the 10 required Markdown files,
`MANIFEST.tsv`, `SHA256SUMS.txt`, and bounded JSON receipts under `raw/`.
Weights and full embeddings are prohibited.

```text
AUDIT_MARKDOWN_COUNT=10
AUDIT_RAW_RECEIPT_COUNT=13
AUDIT_UNEXPECTED_FILE_COUNT=0
MANIFEST_ROW_COUNT=23
SHA256_LEDGER_ROW_COUNT=24
```

## Forbidden-scope scan

| Scope | Required final value |
| --- | --- |
| database files changed | `0` |
| canonical release changed | `false` |
| Search files changed | `0` |
| Context semantics/governance/projection changed | `false` |
| Spacetime governance/projection changed | `false` |
| `CG-CUR-4` changed | `false` |
| `M2`, `M5`, or `M7` specification changed | `false` |
| public Exploration route/API added | `false` |
| vector database added | `false` |
| renderer implemented | `false` |
| public model/weights selected | `false` |
| model/tokenizer/embedding/token-array file committed | `0` |
| raw full corpus or full pair/neighbor matrix committed | `0` |

## Final Git inventory

```text
CHANGED_FILE_COUNT=86
ADDED_FILE_COUNT=85
MODIFIED_FILE_COUNT=1
DELETED_FILE_COUNT=0
UNEXPECTED_CHANGED_FILE_COUNT=0
GIT_DIFF_CHECK=PASS
```

Authoritative path list:

```text
PROJECT_LOG.md
docs/audits/v49-exploration-nlp-round1/00_EXECUTIVE_RECEIPT.md
docs/audits/v49-exploration-nlp-round1/01_CORPUS_BOUNDARY_VALIDATION.md
docs/audits/v49-exploration-nlp-round1/02_TEXT_FIELD_GOVERNANCE.md
docs/audits/v49-exploration-nlp-round1/03_MODEL_ARTIFACT_VALIDATION.md
docs/audits/v49-exploration-nlp-round1/04_LEXICAL_BASELINE_VALIDATION.md
docs/audits/v49-exploration-nlp-round1/05_DENSE_MODEL_VALIDATION.md
docs/audits/v49-exploration-nlp-round1/06_LEAKAGE_AND_HUBNESS_VALIDATION.md
docs/audits/v49-exploration-nlp-round1/07_REPRODUCIBILITY.md
docs/audits/v49-exploration-nlp-round1/08_SECURITY_AND_LICENSE.md
docs/audits/v49-exploration-nlp-round1/09_CHANGED_FILES.md
docs/audits/v49-exploration-nlp-round1/MANIFEST.tsv
docs/audits/v49-exploration-nlp-round1/SHA256SUMS.txt
docs/audits/v49-exploration-nlp-round1/raw/aspect-structured-hybrid-summary.json
docs/audits/v49-exploration-nlp-round1/raw/corpus-governance-summary.json
docs/audits/v49-exploration-nlp-round1/raw/dense-cross-language-summary.json
docs/audits/v49-exploration-nlp-round1/raw/duplication-boilerplate-summary.json
docs/audits/v49-exploration-nlp-round1/raw/evaluation-registry-summary.json
docs/audits/v49-exploration-nlp-round1/raw/hubness-robustness-summary.json
docs/audits/v49-exploration-nlp-round1/raw/language-tokenization-summary.json
docs/audits/v49-exploration-nlp-round1/raw/lexical-baseline-summary.json
docs/audits/v49-exploration-nlp-round1/raw/metadata-leakage-summary.json
docs/audits/v49-exploration-nlp-round1/raw/model-artifact-summary.json
docs/audits/v49-exploration-nlp-round1/raw/nlp-round1-analysis-summary.json
docs/audits/v49-exploration-nlp-round1/raw/review-architecture-summary.json
docs/audits/v49-exploration-nlp-round1/raw/run-performance-security-summary.json
docs/research/trace-v49-exploration-nlp-round1/00_EXECUTIVE_DECISION.md
docs/research/trace-v49-exploration-nlp-round1/01_NLP_DATA_STATEMENT.md
docs/research/trace-v49-exploration-nlp-round1/02_TEXT_SOURCE_INVENTORY.md
docs/research/trace-v49-exploration-nlp-round1/03_NLP_TEXT_FIELD_REGISTRY.tsv
docs/research/trace-v49-exploration-nlp-round1/04_NLP_CORPUS_GOVERNANCE_POLICY.md
docs/research/trace-v49-exploration-nlp-round1/05_LANGUAGE_AND_SCRIPT_CENSUS.tsv
docs/research/trace-v49-exploration-nlp-round1/06_TEXT_LENGTH_AND_TOKENIZATION.tsv
docs/research/trace-v49-exploration-nlp-round1/07_DUPLICATION_AND_BOILERPLATE_AUDIT.md
docs/research/trace-v49-exploration-nlp-round1/08_NLP_BOILERPLATE_REGISTRY.tsv
docs/research/trace-v49-exploration-nlp-round1/09_ASPECT_DOCUMENT_SPEC.md
docs/research/trace-v49-exploration-nlp-round1/10_MODEL_ARTIFACT_REGISTER.tsv
docs/research/trace-v49-exploration-nlp-round1/11_EVALUATION_PAIR_REGISTRY.tsv
docs/research/trace-v49-exploration-nlp-round1/12_LEXICAL_BASELINE_RESULTS.tsv
docs/research/trace-v49-exploration-nlp-round1/13_DENSE_MODEL_RESULTS.tsv
docs/research/trace-v49-exploration-nlp-round1/14_CROSS_LANGUAGE_RESULTS.tsv
docs/research/trace-v49-exploration-nlp-round1/15_METADATA_HOLDOUT_RESULTS.tsv
docs/research/trace-v49-exploration-nlp-round1/16_SOURCE_LANGUAGE_LEAKAGE.tsv
docs/research/trace-v49-exploration-nlp-round1/17_HUBNESS_AND_ANISOTROPY.tsv
docs/research/trace-v49-exploration-nlp-round1/18_ROBUSTNESS_AND_ABLATION.tsv
docs/research/trace-v49-exploration-nlp-round1/19_ASPECT_DISAGREEMENT.tsv
docs/research/trace-v49-exploration-nlp-round1/20_STRUCTURED_NLP_DISAGREEMENT.tsv
docs/research/trace-v49-exploration-nlp-round1/21_HYBRID_EXPERIMENTS.tsv
docs/research/trace-v49-exploration-nlp-round1/22_NLP_REVIEW_PACKET.tsv
docs/research/trace-v49-exploration-nlp-round1/23_NLP_CHANNEL_ARCHITECTURE.md
docs/research/trace-v49-exploration-nlp-round1/24_LICENSE_AND_PRODUCTION_ELIGIBILITY.md
docs/research/trace-v49-exploration-nlp-round1/25_PERFORMANCE_AND_REPRODUCIBILITY.md
docs/research/trace-v49-exploration-nlp-round1/26_NLP_RED_TEAM.md
docs/research/trace-v49-exploration-nlp-round1/27_ROUND_DECISION.md
scripts/exploration-v49-nlp/aspect_disagreement.py
scripts/exploration-v49-nlp/benchmark_round1.py
scripts/exploration-v49-nlp/boilerplate_audit.py
scripts/exploration-v49-nlp/channel_architecture.py
scripts/exploration-v49-nlp/common.py
scripts/exploration-v49-nlp/corpus_builder.py
scripts/exploration-v49-nlp/cross_language_eval.py
scripts/exploration-v49-nlp/dense_encoder.py
scripts/exploration-v49-nlp/embedding_index.py
scripts/exploration-v49-nlp/evaluation_registry.py
scripts/exploration-v49-nlp/field_governance.py
scripts/exploration-v49-nlp/generate_round1.py
scripts/exploration-v49-nlp/hubness_anisotropy.py
scripts/exploration-v49-nlp/hybrid_experiments.py
scripts/exploration-v49-nlp/known_item_eval.py
scripts/exploration-v49-nlp/language_leakage_eval.py
scripts/exploration-v49-nlp/language_script_audit.py
scripts/exploration-v49-nlp/lexical_bm25f.py
scripts/exploration-v49-nlp/lexical_char_ngram.py
scripts/exploration-v49-nlp/lexical_common.py
scripts/exploration-v49-nlp/lexical_eval.py
scripts/exploration-v49-nlp/lexical_word_ngram.py
scripts/exploration-v49-nlp/metadata_holdout_eval.py
scripts/exploration-v49-nlp/model_registry.py
scripts/exploration-v49-nlp/model_run_receipts.py
scripts/exploration-v49-nlp/normalization.py
scripts/exploration-v49-nlp/review_packet.py
scripts/exploration-v49-nlp/robustness_ablation.py
scripts/exploration-v49-nlp/source_inventory.py
scripts/exploration-v49-nlp/source_leakage_eval.py
scripts/exploration-v49-nlp/structured_nlp_disagreement.py
scripts/exploration-v49-nlp/verify_round1.py
```

## Final workflow

Only explicit paths may be staged. `git add .`, `git add -A`, and
`git add --all` are prohibited. The feature branch may be pushed after tests,
artifact validation, final package verification, and a clean post-commit
worktree. No pull request, merge, or deploy is part of this round.

```text
PR_CREATED=false
MERGED=false
DEPLOYED=false
```
