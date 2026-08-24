# Model artifact validation

## Evidence state

`DOCUMENT_STATE=SEALED`

The model registry performs no network call and loads no model. Its immutable
metadata currently passes self-test with six candidates and SHA-256
`2b77f50cf883714544d16224f84ef15e511d45251bd52e81fc8764d2f64fcd82`.

## Candidate register

| Candidate | Channel | Revision | License decision | Execution gate |
| --- | --- | --- | --- | --- |
| `NLP-D1` | dense | `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` | production-eligible | ready from verified official safetensors snapshot |
| `NLP-D2` | dense | `5617a9f61b028005a4858fdac845db406aefb181` | production-eligible | conditional: pickle weights |
| `NLP-D3` | dense | `274baa43b0e13e37fafa6428dbc7938e62e5c439` | production-eligible | ready from verified official safetensors snapshot |
| `NLP-D4` | dense | `ab036b023d30b4d1138c4c3bfa9f0c445ab455d6` | research-only | blocked: non-commercial and unreviewed remote code |
| `NLP-S1` | sparse | `5617a9f61b028005a4858fdac845db406aefb181` | production-eligible | conditional: FlagEmbedding and pickle artifacts |
| `NLP-LID1` | language ID | `9f1c466f5d3c80b0e1cc3985dbccf89859cf67b2` | research-only | conditional, analysis-only |

The registry records official owner/repository, model/tokenizer revisions,
artifact sizes and hashes, license, eligibility, remote-code state, parameter
count, dimension, input limit, pooling, normalization, input templates, dtype,
quantization, language coverage, and loader family.

## Local snapshot verification

The execution candidates have these required weights:

```text
NLP-D1_MODEL_SAFETENSORS_BYTES=1191586416
NLP-D1_MODEL_SAFETENSORS_SHA256=0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd
NLP-D3_MODEL_SAFETENSORS_BYTES=1119825680
NLP-D3_MODEL_SAFETENSORS_SHA256=dd6b6e4f52db0a7aff83a13d10e6c5342ef9f6ab799bad3221f4b35ef390fa85
```

Their configuration, tokenizer, pooling/module, special-token, and model-card
files are individually hashed in the final TSV. Snapshot verification occurs
before importing/loading model code. Execution uses `local_files_only` and
`trust_remote_code=false`.

```text
NLP_D1_SNAPSHOT_VERIFICATION=PASS
NLP_D3_SNAPSHOT_VERIFICATION=PASS
UNVERIFIED_ARTIFACT_EXECUTION_COUNT=0
REMOTE_CODE_EXECUTION_COUNT=0
```

## Model-mode checks

The final validator must bind official query/document templates, pooling,
normalization, dtype, quantization state, maximum input length, tokenizer
revision, aspect cap, and symmetric/asymmetric mode to each result row.
Plain-document symmetric diagnostics cannot be reported as official asymmetric
retrieval results or vice versa.

## Commit boundary

```text
MODEL_ARTIFACT_REGISTER_ROW_COUNT=6
MODEL_ARTIFACT_REGISTER_SHA256=14738232b2dc9762a2f1749c0efdbb894049b85bde98978e1b2f8f4e8aa99122
MODEL_WEIGHT_FILES_COMMITTED=0
TOKENIZER_ARTIFACT_FILES_COMMITTED=0
LANGUAGE_ID_MODEL_COMMITTED=false
FULL_EMBEDDING_MATRIX_COMMITTED=false
```

Any unverified artifact execution, remote-code execution, or committed model
file is a hard failure.
