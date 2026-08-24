# NLP aspect document specification

## Contract state

`DOCUMENT_STATE=SEALED_PRECOMMIT_PASS`

```text
SCHEMA_VERSION=trace-nlp-aspect-document/v1
POLICY_VERSION=trace-nlp-corpus-v1
FIELD_REGISTRY_VERSION=trace-nlp-text-field-registry-v1
NORMALIZATION_VERSION=trace-nlp-normalization-v1
```

This contract defines local/offline research documents. Full documents are not
committed. Committed summaries and review rows expose only bounded public-safe
fields.

## Top-level document

Each document contains:

```text
schemaVersion
publicObjectId
objectId
policyVersion
policySha256
fieldRegistryVersion
fieldRegistrySha256
normalizationVersion
aspectDocumentVersion
aspects
historicalRelation=false
semanticRelation=false
probability=false
```

`publicObjectId` and `objectId` must be the same governed public surface ID.
Internal UUIDs, held identifiers, folder/control identifiers, and file URLs are
invalid. Documents are sorted by public ID and unique across the 7,995-object
cohort.

## Aspect payload

Every available aspect records:

```text
aspectId
sourceFieldIds[]
sourceFieldRoles[]
sourceArtifactSha256
originalSourceHashes[]
originalTextHash
semanticNormalizedHash
lexicalCasefoldedHash
characterCount
codePointCount
languageScriptState
scriptClasses[]
modelInputTokenCap
modelInputTruncationPolicy=HEAD_AT_MODEL_INPUT_ONLY
truncated=false
boilerplateRemoved
sourceIdentityMasked
structuredLabelsMasked
urlRemovedCount
markupRemoved
htmlEntityDecoded
publicSafe
rightsSafe
historicalRelation=false
semanticRelation=false
probability=false
```

Local text-bearing documents may additionally contain `displayOriginal`,
`semanticNormalized`, and `lexicalCasefolded`. `displayOriginal` is set to
`null` when a URL was present so the generated document does not replicate a
source URL. Committed receipts retain hashes and aggregates, not full values.

`truncated=false` in the base corpus proves that source normalization was not
overwritten. A separate tokenizer/model receipt records any model-input-only
head truncation.

## Registered aspects

| Aspect ID | Authoritative field | Role | Count | Status |
| --- | --- | --- | ---: | --- |
| `NLP_TITLE` | `NLP-FIELD-001` | `OBJECT_TITLE` | 7,995 | object-semantic aspect |
| `NLP_SUBJECT` | `NLP-FIELD-003` | `OBJECT_SUBJECT_TERMS` | 7,838 | separate, leakage-gated aspect |
| `NLP_OBJECT_DESCRIPTION` | none | unavailable | 0 | no document is emitted |
| `NLP_SOURCE_NARRATIVE` | `NLP-FIELD-004` | `SOURCE_NARRATIVE` | 7,431 | isolated diagnostic aspect |
| `NLP_OBJECT_SEMANTIC_COMPOSITE` | `NLP-FIELD-001` | `OBJECT_TITLE` | 7,995 | title-only composite |

The composite adds:

```text
compositePolicy=TITLE_ONLY
includedAspectIds=[NLP_TITLE]
```

It cannot include subjects, source narrative, source name, rights,
provenance, boilerplate, folder labels, creator attribution, object type, or
other structured controls in v1.

## Unavailable aspects

Aspect absence is represented by absence from the `aspects` mapping and by
cohort-level availability receipts. It must not be encoded as a zero-text
document and included in query denominators. Dense storage may use a zero row
only with a separate exact availability mask; unavailable IDs cannot become
queries or neighbors for that aspect.

The declared query cohort for each aspect is exactly the available aspect
cohort. Receipts distinguish `fullPublicCohort`, `fullAspectCohort`, available
count, unavailable count, and query-ID hash.

## Tokenizer-specific model-input receipt

Before every dense run, the exact tokenizer and revision census the final
prepared model input, including official template and special tokens. Each
record binds:

```text
policyVersion
policySha256
aspectId
governedAspectTokenCap
officialModelMaxTokens
effectiveTokenCap
semanticNormalizedHash
tokenCountBefore
tokenCountAfter
tokensRemoved
truncated
truncationDirection=HEAD
applicationStage=MODEL_INPUT_ONLY
fullNormalizedHashPreserved=true
corpusTextOverwritten=false
```

Aggregate receipts report P50/P90/P95/P99/MAX, documents truncated, tokens
removed, and affected rates by model and aspect.

## Variant flags

Boilerplate, source-mask, structured-label-mask, punctuation, Unicode, and
compatibility experiments create explicitly named derived inputs and set the
applicable flags. They never overwrite the base document or its full hashes.
Every transform is deterministic, versioned, and separately evaluated.

## Output semantics

An affinity result must preserve aspect identity, jointly available and
unavailable aspects, source/language diagnostics, method ID, model revision,
and all three false relation/probability flags. Aspect scores cannot be reduced
to one scalar without a separately evaluated fusion policy, which this round
does not select.

## Final contract reconciliation

```text
CORPUS_DOCUMENT_RECEIPT_SHA256=69aa8f290f7390bdb8ce7c0a3cf4ecdfb7426c908804bf48f9126c0eec4fdac8
CORPUS_URL_REMOVED_COUNT=209
ASPECT_SPEC_VERIFICATION=PASS
ASPECT_SPEC_RECEIPT_SHA256=69aa8f290f7390bdb8ce7c0a3cf4ecdfb7426c908804bf48f9126c0eec4fdac8
```
