# TRACE NLP corpus governance policy

## Policy identity

`DOCUMENT_STATE=SEALED_PRECOMMIT_PASS`

```text
NLP_CORPUS_POLICY_VERSION=trace-nlp-corpus-v1
NLP_CORPUS_POLICY_SHA256=e20d6de00345fce6f925b4ee1ba5c89be7ee4b859e8bda0432bcd6c964a03f16
TEXT_FIELD_REGISTRY_VERSION=trace-nlp-text-field-registry-v1
TEXT_FIELD_REGISTRY_SHA256=b70c98f8a52de2ae5bbaf5d2d69db85381bfa59a0d07722df0823018d2aec3b6
NORMALIZATION_VERSION=trace-nlp-normalization-v1
ASPECT_DOCUMENT_VERSION=trace-nlp-aspect-document-v1
BOILERPLATE_REGISTRY_VERSION=trace-nlp-boilerplate-v1
```

The policy object and hashes are frozen in the deterministic research code.
This Markdown file is not the hash material; the final package reconciliation
confirms that it mirrors the frozen policy object.

## 1. Eligible cohort

The sole eligibility authority is the frozen migration ledger. Exactly 7,995
records with `research_disposition=eligible` may enter the corpus. Exactly
7,928 held records are rejected before text normalization. Held and unknown
lookup failures expose the same public error and no private distinction.

The corpus contains one sorted, unique public document identity per eligible
surface. An internal UUID, held ID, folder/control ID, or file URL is invalid.

## 2. Included and excluded roles

Included source roles are `OBJECT_TITLE`, `OBJECT_SUBJECT_TERMS`, and
`SOURCE_NARRATIVE`, but their aspects and permissions remain distinct.

- `NLP_TITLE` uses only `NLP-FIELD-001`.
- `NLP_SUBJECT` uses only `NLP-FIELD-003` and is leakage-gated.
- `NLP_SOURCE_NARRATIVE` uses only `NLP-FIELD-004` and is diagnostic.
- `NLP_OBJECT_SEMANTIC_COMPOSITE` is title-only in v1.
- `NLP_OBJECT_DESCRIPTION` is unavailable.

Curatorial, reading, dossier, registration, provenance, rights, boilerplate,
source-identity, structured-label, and internal-control roles add zero
object-semantic affinity. Creator and object type remain metadata only.

## 3. Original-text preservation

Source artifacts are immutable and never overwritten. Every admitted aspect
records its original source hash, original text hash, semantic-normalized hash,
lexical-casefolded hash, source artifact hash, and normalization version.

Full generated documents may exist only locally. The committed package may
contain code, schemas, field/boilerplate registries, aggregate statistics,
bounded public-safe review rows, hashes, and receipts. It may not contain a
full text corpus.

## 4. Deterministic normalization

The primary semantic view is NFC. The normalizer deterministically:

- normalizes CRLF/CR to LF;
- replaces non-breaking spaces;
- decodes verified HTML entities;
- removes markup through a parser and discards script/style/noscript content;
- rejects disallowed C0/C1 controls;
- removes URLs from semantic input;
- collapses repeated whitespace; and
- preserves punctuation, hyphens, apostrophes, diacritics, and non-Latin
  scripts.

`DISPLAY_ORIGINAL`, `SEMANTIC_NORMALIZED`, `LEXICAL_CASEFOLDED`, and
`LEXICAL_COMPATIBILITY_FALLBACK` are separate views. NFKC and diacritic folding
occur only in the fallback lexical view, never as the sole stored or semantic
representation.

No dictionary or fuzzy process corrects historical spelling, archaic language,
personal names, place names, movement terminology, or transliteration.

## 5. Language and script analysis

Unicode-property script classification is deterministic and analysis-only. It
does not use source institution or geography as a proxy for language. A model
language label, if later admitted, must be pinned to an exact artifact,
checksum, license, coverage statement, and minimum-length policy. `MIXED` and
`UNDETERMINED` are valid outputs.

Language identity never becomes positive semantic affinity.

## 6. Markup, boilerplate, duplicates, and source identity

Markup cleaning follows the normalization rule above. Boilerplate can mutate
model input only through an explicit row in the versioned boilerplate registry.
Frequency alone authorizes neither deletion nor a hidden blacklist. Current
frequency-derived candidates are `HOLD`; source identity is masked only in the
declared leakage variant.

Exact duplicates, same-title records, case/punctuation/whitespace variants,
and source templates retain distinct public object identities. Deduplication
may prevent duplicate computation but may not merge IDs or create a positive
evaluation pair.

## 7. Structured-label leakage

Medium, theme, movement-context, geography, source, object-type, and aliases
are registered controls. Metadata-holdout experiments must distinguish:

1. original approved input;
2. target label and aliases masked; and
3. all governed Context labels masked.

Any visible literal target is disclosed. A score that collapses only after
masking is reported as label leakage, not semantic understanding.

## 8. Field-specific caps and truncation

| Aspect | Governed cap |
| --- | ---: |
| `NLP_TITLE` | 256 final tokenizer tokens |
| `NLP_SUBJECT` | 256 final tokenizer tokens |
| `NLP_OBJECT_SEMANTIC_COMPOSITE` | 256 final tokenizer tokens |
| `NLP_SOURCE_NARRATIVE` | 512 final tokenizer tokens |

The effective cap is the smaller of the governed aspect cap and official model
maximum. Counting occurs on final prepared input, including the exact
model-specific template and special tokens. Truncation is deterministic head
truncation at model input only. The full normalized corpus text and hashes are
preserved.

Every model/aspect run records document count, token counts before and after,
documents truncated, tokens removed, document truncation rate, and token
removal rate. Silent corpus overwrite is forbidden.

## 9. Model input and artifact controls

Each model uses its exact official query/document instructions, pooling,
normalization, tokenizer, and immutable revision. Symmetric plain-document
diagnostics remain distinct from official asymmetric retrieval modes.

Model weights and tokenizer artifacts are downloaded only from verified
official repositories after resource preflight. Inference then runs locally
with network disabled and `local_files_only`. Unreviewed remote code cannot
execute. Model weights, tokenizer arrays, embeddings, and full neighbor or pair
matrices are never committed.

## 10. Aspect separation

No generic concatenated document exists. Title, subject, object description,
source narrative, and approved composite remain separately addressable.
Unavailable aspects are recorded as unavailable, never as synthetic text.

The v1 composite contains only the title. Subject admission is blocked pending
label-leakage and boilerplate review. Source narrative cannot enter it because
it describes provider/source prose rather than a governed object-description
role.

## 11. Reproducibility and local artifacts

Local corpus artifacts use `.local/trace-nlp-v1/` or an explicit temporary
directory and must remain untracked. A run binds source commit, input hashes,
policy and registry hashes, model and tokenizer revisions, aspect, template,
token census, deterministic ordering, and bounded ranking hashes.

Seeds, timestamps, process IDs, paths, and cache state cannot change corpus,
embeddings, neighbors, or scores. Hardware-dependent floating-point
observations are separated from semantic and ranking determinism.

## 12. Review and exceptions

An exception requires a new registered field or boilerplate decision, a reason,
public/rights review, prohibited-use statement, version increment where
semantics change, regenerated hashes, and full boundary/regression validation.
No operator or benchmark result may silently override a hold or exclusion.

## 13. Prohibited inference

Every result must retain:

```text
historicalRelation=false
semanticRelation=false
probability=false
```

No output may assert historical relation, influence, causation, lineage,
contact, creator intent, importance, quality, canonicality, or relation
probability. No generative system may translate, rewrite, summarize, classify,
repair OCR, generate keywords, infer language, normalize terminology, create
positive pairs, or judge similarity for this corpus.
