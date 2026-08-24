# TRACE v49 Exploration NLP Round 1 executive receipt

## Receipt state

`DOCUMENT_STATE=SEALED`

This audit receipt is sealed against the final bounded package. Frozen source,
cohort, registry, policy, benchmark, manifest, checksum, regression, Git, and
changed-file facts are recorded below.

```text
SOURCE_SHA=580587a74f400d8a04d995937f4efb31e6621dd8
WORKTREE=/private/tmp/graphic_design_archive_v49_exploration_nlp_semantic_round1
BRANCH=research/v49-exploration-nlp-semantic-round1-20260824

CANONICAL_OBJECT_COUNT=15923
PUBLIC_OBJECT_COUNT=7995
HELD_OBJECT_COUNT=7928
NLP_HELD_OBJECTS_INCLUDED=0

TEXT_SOURCE_FIELD_COUNT=37
TEXT_SOURCE_FIELD_CLASSIFIED_COUNT=37
UNCLASSIFIED_TEXT_FIELD_COUNT=0

NLP_CORPUS_POLICY_VERSION=trace-nlp-corpus-v1
NLP_CORPUS_POLICY_SHA256=e20d6de00345fce6f925b4ee1ba5c89be7ee4b859e8bda0432bcd6c964a03f16
NLP_TEXT_FIELD_REGISTRY_SHA256=b70c98f8a52de2ae5bbaf5d2d69db85381bfa59a0d07722df0823018d2aec3b6
```

## Round boundary

Round 7 audits text roles and compares isolated lexical/dense retrieval
families. Its possible interpretation is semantic text affinity or a
text-derived retrieval candidate. Every result retains
`historicalRelation=false`, `semanticRelation=false`, and `probability=false`.

This package does not select or expose a public model, train weights, choose
fusion weights, modify `CG-CUR-4` or `M2/M5/M7`, change Search/Context/
Spacetime, add an API or route, add a vector database, add a renderer, or call a
hosted/generative inference service.

## Required package shape

The final verifier must observe exactly 28 research files, including exactly
17 required TSVs, and the required 10 audit Markdown files plus
`MANIFEST.tsv`, `SHA256SUMS.txt`, and bounded `raw/` receipts. It must reject
weights, embeddings, token arrays, raw full-corpus text, held text, and full
pair or neighbor matrices.

```text
RESEARCH_FILE_COUNT=28
RESEARCH_TSV_COUNT=17
AUDIT_MARKDOWN_COUNT=10
AUDIT_RAW_RECEIPT_COUNT=13
MANIFEST_VALIDATION=PASS
SHA256_LEDGER_VALIDATION=PASS
```

## Evidence summary

| Gate | Frozen/current evidence | Final state |
| --- | --- | --- |
| cohort | 7,995 public; 7,928 held; zero overlap/unclassified | `PASS` |
| field governance | 37/37 fields classified; zero unclassified | `PASS` |
| aspects | title 7,995; subject 7,838; description 0; narrative 7,431; title composite 7,995 | `PASS_WITH_LANGUAGE_DIAGNOSTIC_NOT_RUN_AND_NO_ASPECT_FUSION` |
| lexical baselines | BM25F, char 3--5, word 1--2, equal RRF | `PASS_FULL_GOVERNED_ASPECTS_NO_FAMILY_SHORTLISTED` |
| dense baselines | exact-revision D1 and D3 eligible for local full runs | `PASS_2_FULL_CORPUS_MODELS_4_ASPECT_RUNS_NO_MODEL_SHORTLISTED` |
| pairs | 3 external identity positives; 0 cross-language positives; 309 controls | `PASS_IDENTITY_AND_CONTROL_REGISTRIES; CROSS_LANGUAGE_NOT_RUN_NO_VERIFIED_POSITIVES` |
| leakage/hubness | mandatory and decision-blocking | `STOPPED_RECOVERABLE_CHECKPOINT_2_SOURCE_LEAKAGE_BLOCKERS` |
| review | bounded 24--36 target; no fabricated judgments | `NOT_RUN_DOMAIN_EXPERT_REVIEW; 24_ANCHOR_PACKET_WITH_PENDING_JUDGMENTS` |
| regressions | Search, Context, Spacetime, Round 6, TRACE, Read/API, typecheck, build | `PASS` |

## Final decision

```text
PHASE_STATUS=STOPPED_RECOVERABLE_CHECKPOINT
NLP_MODEL_DECISION=NLP_CORPUS_AUDIT_ONLY
DENSE_MODEL_SHORTLIST_COUNT=0
DENSE_MODEL_SHORTLIST_IDS=NONE
NLP_CHANNEL_POSITION_SHORTLIST=NONE

PUBLIC_NLP_MODEL_SELECTED=false
PUBLIC_NLP_WEIGHTS_SELECTED=false
PUBLIC_EXPLORATION_MODEL_SELECTED=false
STRUCTURED_NLP_FUSION_SELECTED=false
STRUCTURED_NLP_FUSION_WEIGHTS_SELECTED=false
```

The authoritative detailed receipt is `27_ROUND_DECISION.md`. Any unresolved
or adverse value must narrow that decision or preserve a recoverable
checkpoint; it cannot be omitted here.
