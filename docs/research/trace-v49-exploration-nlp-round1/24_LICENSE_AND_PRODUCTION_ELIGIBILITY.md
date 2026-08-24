# License and production eligibility

## Evidence state

`DOCUMENT_STATE=FINAL_EVIDENCE_BOUND_AUDIT_ONLY`

The model register is metadata-only and pinned to
`trace-nlp-model-registry/v1`. Its current deterministic SHA-256 is
`2b77f50cf883714544d16224f84ef15e511d45251bd52e81fc8764d2f64fcd82`.
This review records research governance decisions; it is not a substitute for
legal advice or a later deployment review.

## Candidate decisions

| Candidate | Exact repository revision | License | Eligibility | Execution state | Governing reason |
| --- | --- | --- | --- | --- | --- |
| `NLP-D1` Qwen3-Embedding-0.6B | `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` | Apache-2.0 | `PRODUCTION_ELIGIBLE` | verified local snapshot; execution-ready | official safetensors snapshot, no remote code |
| `NLP-D2` BGE-M3 dense | `5617a9f61b028005a4858fdac845db406aefb181` | MIT | `PRODUCTION_ELIGIBLE` | conditional | pickle-formatted weights require explicit review/authorization |
| `NLP-S1` BGE-M3 sparse | `5617a9f61b028005a4858fdac845db406aefb181` | MIT | `PRODUCTION_ELIGIBLE` | conditional | FlagEmbedding source and pickle artifacts require review/authorization |
| `NLP-D3` multilingual-e5-large-instruct | `274baa43b0e13e37fafa6428dbc7938e62e5c439` | MIT | `PRODUCTION_ELIGIBLE` | verified local snapshot; execution-ready | official safetensors snapshot, no remote code |
| `NLP-D4` jina-embeddings-v3 | `ab036b023d30b4d1138c4c3bfa9f0c445ab455d6` | CC-BY-NC-4.0 | `RESEARCH_ONLY` | blocked | non-commercial artifact and unreviewed required remote code |
| `NLP-LID1` fastText language ID | `9f1c466f5d3c80b0e1cc3985dbccf89859cf67b2` | CC-BY-NC-4.0 | `RESEARCH_ONLY` | conditional, analysis-only | non-commercial artifact; no automatic production use |

`PRODUCTION_ELIGIBLE` means only that the registered license is not an
immediate product-use blocker under this research policy. It does not mean the
model is selected, public-validated, secure for deployment, or approved by
domain review.

## Verified local snapshots

The two full-corpus execution candidates were downloaded from their official
repositories at exact immutable revisions and verified before local loading.

| Candidate | Weight artifact | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `NLP-D1` | `model.safetensors` | 1,191,586,416 | `0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd` |
| `NLP-D3` | `model.safetensors` | 1,119,825,680 | `dd6b6e4f52db0a7aff83a13d10e6c5342ef9f6ab799bad3221f4b35ef390fa85` |

Configuration, tokenizer, pooling, special-token, module, and model-card hashes
are recorded row-by-row in `10_MODEL_ARTIFACT_REGISTER.tsv`. Both candidates
load with `trust_remote_code=false`, `local_files_only`, and no hosted
inference.

```text
NLP_D1_SNAPSHOT_VERIFICATION=PASS_VERIFIED_LOCAL_OFFICIAL_SNAPSHOT
NLP_D3_SNAPSHOT_VERIFICATION=PASS_VERIFIED_LOCAL_OFFICIAL_SNAPSHOT
MODEL_ARTIFACT_REGISTER_SHA256=2b77f50cf883714544d16224f84ef15e511d45251bd52e81fc8764d2f64fcd82
```

## Remote-code boundary

No candidate requiring `trust_remote_code=True` may run unless its custom code
repository and revision are pinned, the complete executed code is reviewed,
and its SHA-256 is registered. `NLP-D4` fails that execution gate. Setting
`trust_remote_code=false` in an unrelated loader does not waive the model's
documented adapter requirement.

Unreviewed FlagEmbedding code and pickle artifacts likewise remain
non-executed. A permissive model license does not authorize unsafe
serialization or unreviewed code.

## Selection states

Every architecture must report three independent states:

```text
RESEARCH_SHORTLISTED=<true|false>
PRODUCTION_ELIGIBLE=<true|false>
PUBLIC_VALIDATED=false
```

A research-only model cannot win a future production shortlist. A
production-eligible model cannot become public merely because it completed a
benchmark.

Final counts:

```text
DENSE_MODEL_CANDIDATE_COUNT=4
PRODUCTION_ELIGIBLE_DENSE_MODEL_COUNT=3
RESEARCH_ONLY_DENSE_MODEL_COUNT=1
REJECTED_DENSE_MODEL_COUNT=0
DENSE_MODEL_SHORTLIST_COUNT=0
DENSE_MODEL_SHORTLIST_IDS=NONE
```

## Artifact and redistribution boundary

Model weights, tokenizer/model snapshots, embeddings, token arrays, full
nearest-neighbor output, and full cosine matrices stay outside Git. Committed
files contain only hashes, bounded aggregate receipts, and public-safe samples.

```text
MODEL_WEIGHT_FILES_COMMITTED=0
LANGUAGE_ID_MODEL_COMMITTED=false
FULL_EMBEDDING_MATRIX_COMMITTED=false
PUBLIC_NLP_WEIGHTS_SELECTED=false
```

The final changed-file and manifest scan must validate those values before this
document can be sealed.
