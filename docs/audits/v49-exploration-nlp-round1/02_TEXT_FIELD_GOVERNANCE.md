# Text-field governance validation

## Evidence state

`DOCUMENT_STATE=SEALED`

## Registry identity

```text
REGISTRY_VERSION=trace-nlp-text-field-registry-v1
REGISTRY_SHA256=b70c98f8a52de2ae5bbaf5d2d69db85381bfa59a0d07722df0823018d2aec3b6
FIELD_COUNT=37
CLASSIFIED_FIELD_COUNT=37
UNCLASSIFIED_FIELD_COUNT=0
```

Every discovered field has exactly one allowed primary role and one allowed
governance decision. The complete population, length, script, duplication,
boilerplate, source-identity, structured-label, URL, markup, rights, and safety
columns are carried in `03_NLP_TEXT_FIELD_REGISTRY.tsv`.

## Admitted fields

| Field | Role | Decision | Aspect | Restriction |
| --- | --- | --- | --- | --- |
| `NLP-FIELD-001` | object title | include title | `NLP_TITLE` | same title proves neither identity nor relation |
| `NLP-FIELD-003` | object subject terms | include subject | `NLP_SUBJECT` | separate; mask proxy labels; not in v1 composite |
| `NLP-FIELD-004` | source narrative | diagnostic inclusion | `NLP_SOURCE_NARRATIVE` | never object description or composite text |

Creator attribution and object type remain metadata only. Source name, medium,
folder/representation labels, source notes, and collection/source provenance
remain diagnostic or explanatory only. All rights, provenance, control,
duplicate-display, dossier, registration, child, Search-body, and display-table
seams are held or excluded from semantic input.

## Policy reconciliation

```text
CORPUS_POLICY_VERSION=trace-nlp-corpus-v1
CORPUS_POLICY_SHA256=e20d6de00345fce6f925b4ee1ba5c89be7ee4b859e8bda0432bcd6c964a03f16
SOURCE_NARRATIVE_ISOLATED=true
TITLE_ONLY_COMPOSITE=true
SUBJECT_COMPOSITE_ADMISSION=BLOCKED_PENDING_LEAKAGE_AND_BOILERPLATE_REVIEW
```

The base corpus preserves full normalized hashes and uses model-input-only
head truncation. Governed caps are 256 tokens for title, subject, and
title-only composite and 512 for source narrative.

## Required negative checks

The final validator must reject:

- a field absent from the 37-row registry;
- an invalid or multiple primary role;
- an invalid or multiple governance decision;
- an included field that is not authoritative for its aspect;
- source narrative or subject in the v1 composite;
- rights/provenance/source-identity credit;
- a public-safe value assumed rights-safe without its registered decision;
- a mirrored seam counted as an independent document;
- an unavailable object description synthesized from source narrative; and
- any change to the policy or registry material under the recorded hash.

```text
NLP_FIELD_GOVERNANCE_TESTS=PASS
REGISTRY_TSV_ROW_COUNT=37
REGISTRY_TSV_SHA256=381ff4d1e16bc0f77fa3dd47bce504cfb8feb36f84b8c426af12ae239ed864a1
POLICY_MARKDOWN_RECONCILIATION=PASS
```
