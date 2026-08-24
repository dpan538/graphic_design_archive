# TRACE v49 Round 7 executive decision

## Evidence state

`DOCUMENT_STATE=SEALED_PRECOMMIT_PASS`

This document is the decision surface for the first Exploration NLP semantic
research round. Corpus mapping, governance, benchmark, leakage, hubness, and
package values below are reconciled to the authoritative sealed analysis
summary. The resulting checkpoint is audit-only and does not select a model.

The immutable input boundary is:

```text
SOURCE_SHA=580587a74f400d8a04d995937f4efb31e6621dd8
CANONICAL_OBJECT_COUNT=15923
PUBLIC_OBJECT_COUNT=7995
HELD_OBJECT_COUNT=7928
OVERLAP_COUNT=0
UNCLASSIFIED_COUNT=0
```

## What this round can decide

The only permissible output is evidence about **semantic text affinity** or a
**text-derived retrieval candidate**. It is not evidence of historical
relation, design-historical influence, creator intent, causation, lineage,
contact, importance, quality, canonicality, or probability of relation.

The final model decision must be exactly one of:

```text
NLP_CORPUS_AUDIT_ONLY
NLP_BASELINE_FAMILIES_SHORTLISTED
PROVISIONAL_INTERNAL_NLP_CHANNEL_SELECTED
```

`PUBLIC_NLP_MODEL_SELECTED=false` is invariant under every option. The sealed
decision is `NLP_CORPUS_AUDIT_ONLY`: source/provider dominance blocks a model
shortlist, and no result is promoted beyond diagnostic evidence.

## Frozen corpus result

The governed implementation classifies all 37 discovered text fields and
leaves zero fields unclassified. It builds one public document per eligible
surface and no document for a held surface.

```text
NLP_TEXT_FIELD_REGISTRY_VERSION=trace-nlp-text-field-registry-v1
NLP_TEXT_FIELD_REGISTRY_SHA256=b70c98f8a52de2ae5bbaf5d2d69db85381bfa59a0d07722df0823018d2aec3b6
NLP_CORPUS_POLICY_VERSION=trace-nlp-corpus-v1
NLP_CORPUS_POLICY_SHA256=e20d6de00345fce6f925b4ee1ba5c89be7ee4b859e8bda0432bcd6c964a03f16
NLP_NORMALIZATION_VERSION=trace-nlp-normalization-v1
NLP_ASPECT_DOCUMENT_VERSION=trace-nlp-aspect-document-v1
NLP_BOILERPLATE_REGISTRY_VERSION=trace-nlp-boilerplate-v1
```

The v1 aspects are intentionally narrow:

| Aspect | Public objects | Current semantic role |
| --- | ---: | --- |
| `NLP_TITLE` | 7,995 | governed object title |
| `NLP_SUBJECT` | 7,838 | separate source-subject channel with label-leakage controls |
| `NLP_OBJECT_DESCRIPTION` | 0 | not admitted because no governed object-description seam was established |
| `NLP_SOURCE_NARRATIVE` | 7,431 | isolated provider/source diagnostic |
| `NLP_OBJECT_SEMANTIC_COMPOSITE` | 7,995 | title only; no subject or source narrative |

Source narrative is never silently interpreted as object description. Rights,
provenance, source identity, structured labels, folder labels, control text,
and boilerplate contribute zero object-semantic affinity.

## Evaluation boundary

The mechanically verified registry currently contains three Task A positive
pairs. Each is a same-source-item duplicate-import identity established from
immutable source evidence; none is a same-title semantic judgment. Task B has
zero verified translation, transliteration, alternate-title, or multilingual
variant pairs and must report `N/A`, not a fabricated score. The registry also
contains 309 negative/diagnostic controls. Those controls test leakage and are
not historical non-relations.

Known-item retrieval therefore tests representation consistency only. It does
not validate object-semantic affinity, historical usefulness, or multilingual
generalization.

## Baseline program

The full lexical cohort is evaluated with fielded BM25F, character 3--5-gram
TF-IDF cosine, word 1--2-gram TF-IDF cosine, and equal reciprocal-rank fusion.
Two exact-revision, production-eligible dense candidates are eligible for
local/offline full-cohort execution:

- `NLP-D1`: `Qwen/Qwen3-Embedding-0.6B` at
  `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`;
- `NLP-D3`: `intfloat/multilingual-e5-large-instruct` at
  `274baa43b0e13e37fafa6428dbc7938e62e5c439`.

No hosted inference or generative preprocessing is permitted. Final run state:

```text
LEXICAL_FULL_CORPUS_STATUS=PASS
DENSE_FULL_CORPUS_MODEL_COUNT=2
BEST_LEXICAL_MODEL_ID=NONE
DENSE_MODEL_SHORTLIST_IDS=NONE
SOURCE_LEAKAGE_BLOCKER_COUNT=2
LANGUAGE_LEAKAGE_BLOCKER_COUNT=0
```

## Structured-channel separation

Round 6 remains unchanged: candidate retrieval is `CG-CUR-4`, while `M2`, `M5`,
and `M7` are research-only structured architectures. NLP rankings may be
compared with those profiles, but no score, representation, or weight crosses
between them in this round.

```text
CG_CUR_4_CHANGED=false
M2_SPECIFICATION_CHANGED=false
M5_SPECIFICATION_CHANGED=false
M7_SPECIFICATION_CHANGED=false
STRUCTURED_NLP_FUSION_SELECTED=false
STRUCTURED_NLP_FUSION_WEIGHTS_SELECTED=false
```

## Permanent non-selection boundary

```text
PUBLIC_NLP_MODEL_SELECTED=false
PUBLIC_NLP_WEIGHTS_SELECTED=false
PUBLIC_EXPLORATION_MODEL_SELECTED=false
PUBLIC_EXPLORATION_API_ADDED=false
PUBLIC_EXPLORATION_ROUTE_ADDED=false
VECTOR_DATABASE_ADDED=false
EXPLORATION_RENDERER_IMPLEMENTED=false
EXTERNAL_INFERENCE_API_CALL_COUNT=0
GENERATIVE_TEXT_TRANSFORMATION_COUNT=0
MODEL_WEIGHT_FILES_COMMITTED=0
FULL_EMBEDDING_MATRIX_COMMITTED=false
```

The final package carries the adverse and not-run results into
`27_ROUND_DECISION.md`; none is waived to produce a stronger decision.
