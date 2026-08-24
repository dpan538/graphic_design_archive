# Security and license validation

## Evidence state

`DOCUMENT_STATE=SEALED`

## External-data boundary

Archive text is processed only from frozen local artifacts. External access is
limited to explicitly authorized downloads from exact official model
repositories. After verification, all inference is local/offline.

```text
EXTERNAL_INFERENCE_API_CALL_COUNT=0
HOSTED_EMBEDDING_CALL_COUNT=0
GENERATIVE_TEXT_TRANSFORMATION_COUNT=0
MACHINE_TRANSLATION_COUNT=0
GENERATED_SUMMARY_COUNT=0
GENERATED_POSITIVE_PAIR_COUNT=0
```

No archive text is sent to OpenAI, DashScope, Cohere, Jina, Voyage, Google,
AWS Bedrock, Azure, Hugging Face inference endpoints, or another hosted
inference service.

## Code and serialization boundary

Unreviewed remote code cannot execute. The two executed candidates require no
remote code and use safetensors. `NLP-D4` is blocked because it requires
unreviewed custom code and carries a non-commercial license. BGE-M3 dense and
sparse paths remain conditional because their registered snapshots contain
pickle artifacts; the sparse path additionally requires FlagEmbedding review.

```text
TRUST_REMOTE_CODE_EXECUTION_COUNT=0
UNREVIEWED_CUSTOM_CODE_EXECUTION_COUNT=0
PICKLE_MODEL_EXECUTION_COUNT=0
UNVERIFIED_ARTIFACT_EXECUTION_COUNT=0
```

All four must be zero for this execution plan.

## License decisions

| State | Candidates |
| --- | --- |
| production-eligible | `NLP-D1`, `NLP-D2`, `NLP-D3`, `NLP-S1` |
| research-only | `NLP-D4`, `NLP-LID1` |
| rejected | none in the metadata audit |

Production eligibility does not imply selection or public validation. A
non-commercial comparator cannot become the future public default.

## Commit/privacy boundary

The final changed-file scan must find zero:

- model or language-ID weights;
- tokenizer/model snapshot files;
- full embedding or token arrays;
- full raw/normalized corpus dumps;
- full nearest-neighbor, lexical-similarity, cosine, or pair matrices;
- held IDs, held text, private notes, or internal UUIDs;
- private/file URLs in bounded review output; and
- new frontend NLP dependencies, route, API, renderer, vector database, or
  hosted-inference integration.

```text
MODEL_WEIGHT_FILES_COMMITTED=0
TOKENIZER_ARTIFACT_FILES_COMMITTED=0
FULL_EMBEDDING_MATRIX_COMMITTED=false
FULL_TEXT_CORPUS_COMMITTED=false
FULL_PAIR_MATRIX_COMMITTED=false
FULL_NEIGHBOR_MATRIX_COMMITTED=false
INTERNAL_UUID_EXPOSURE_COUNT=0
HELD_ID_EXPOSURE_COUNT=0
```

## Frozen-system boundary

```text
DATABASE_FILES_CHANGED=0
CANONICAL_RELEASE_CHANGED=false
SEARCH_FILES_CHANGED=0
CONTEXT_SEMANTICS_CHANGED=false
CONTEXT_GOVERNANCE_CHANGED=false
SPACETIME_GOVERNANCE_CHANGED=false
CG_CUR_4_CHANGED=false
M2_SPECIFICATION_CHANGED=false
M5_SPECIFICATION_CHANGED=false
M7_SPECIFICATION_CHANGED=false
PUBLIC_EXPLORATION_API_ADDED=false
PUBLIC_EXPLORATION_ROUTE_ADDED=false
VECTOR_DATABASE_ADDED=false
EXPLORATION_RENDERER_IMPLEMENTED=false
```

## Final validation

```text
SECURITY_SCAN=PASS
LICENSE_REGISTER_RECONCILIATION=PASS
FORBIDDEN_ARTIFACT_SCAN=PASS
SECURITY_LICENSE_RECEIPT_SHA256=02569700d597ae002e159eb65a2aa905587782b2983ec1d1eac03265fe259b1e
```
