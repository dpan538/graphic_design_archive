# TRACE NLP data statement

## Evidence state and scope

`DOCUMENT_STATE=SEALED_PRECOMMIT_PASS`

This statement describes the text available to the Round 7 research program.
It is not a claim that the archive represents world graphic-design history,
all languages, all institutions, or the underlying designed objects equally.

The source commit is
`580587a74f400d8a04d995937f4efb31e6621dd8`. The authoritative migration ledger
partitions 15,923 canonical surfaces into 7,995 eligible public surfaces and
7,928 held surfaces with no overlap and no unclassified record. Only the 7,995
public IDs may enter a corpus, index, evaluation pair, embedding run, neighbor
output, or review packet.

## Sources and provider concentration

Text comes from frozen canonical public surfaces, governed Context titles,
governed Context metadata used only as controls, governed Spacetime displays
used only as controls, selected frozen SQLite seams used only to audit mirrors
and provenance, and the bounded Round 6 review artifact used only to prove it
must not become new corpus input.

The corpus reflects provider cataloguing practices. Source distribution and
provider concentration are not sampling weights and must not be generalized to
the broader history of graphic design.

```text
DISTINCT_SOURCE_COUNT=15
LARGEST_SOURCE_OBJECT_COUNT=3505
LARGEST_SOURCE_SHARE=0.43839899937460913
SOURCE_HHI=0.2881509041962984
```

## Text roles and coverage

All 37 discovered text seams receive one primary role and one governance
decision. The registered semantic/diagnostic aspects are:

| Aspect | Coverage | Data character |
| --- | ---: | --- |
| title | 7,995 | short, governed public title |
| subject | 7,838 | provider/source terms; structured-label leakage risk |
| object description | 0 | no seam passed the object-description governance gate |
| source narrative | 7,431 | provider prose; isolated from object-semantic input |
| approved composite | 7,995 | title only in v1 |

Missing aspects remain unavailable. They are not replaced by empty vectors,
source notes, folder labels, rights text, generated summaries, or inferred
descriptions.

## Languages and scripts

Script classes are assigned deterministically from Unicode properties. The
audit distinguishes Latin, Cyrillic, Greek, Han, Hiragana, Katakana, Hangul,
Arabic, Hebrew, Devanagari, mixed, other, and undetermined text. A source
institution or geography is never used as a language label.

No local language-identification model is selected unless its immutable
artifact, license, hash, coverage, and minimum-length policy pass separately.
Short titles and named entities may remain `UNDETERMINED` or `MIXED`.

```text
DISTINCT_SCRIPT_CLASS_COUNT=3
DISTINCT_LANGUAGE_LABEL_COUNT=0
UNDETERMINED_LANGUAGE_OBJECT_COUNT=5
MIXED_SCRIPT_OBJECT_COUNT=4
LANGUAGE_ID_MODEL=NOT_SELECTED
```

## Length, truncation, and missingness

The committed package reports character, code-point, lexical-token, and each
dense-tokenizer length distributions by field role. Full normalized text and
its hash are preserved even when a model input is head-truncated. Governed caps
are 256 final tokenizer tokens for title, subject, and title-only composite,
and 512 for source narrative, further bounded by the official model maximum.

The final census must report, by model and aspect, every truncated document and
removed-token aggregate. No silent overwrite or undisclosed truncation is
allowed.

## Duplication, noise, and boilerplate

The archive contains repeated titles, duplicated imports, provider templates,
URLs, markup, rights/provenance language, historical spelling, punctuation
variants, and source-conditioned cataloguing phrases. Equal text does not imply
equal object identity. Different public IDs remain distinct.

The deterministic boilerplate registry contains 105 rules in the current
frozen census: 15 explicit source-identity masks and 90 held repetition
candidates. It authorizes no frequency-derived automatic removal. The current
audit associates one or more repetition candidates with 6,563 public objects;
this is exposure to a review rule, not proof that the entire record is
boilerplate.

Known OCR/transcription coverage and verified OCR-noise counts are:

```text
OCR_TEXT_FIELD_COUNT=0
OCR_PUBLIC_OBJECT_COUNT=0
KNOWN_NOISY_TEXT_OBJECT_COUNT=N/A_NOT_RUN_NO_GOVERNED_OCR_OR_TRANSCRIPTION_SEAM
```

Absence of a governed OCR seam must be reported as absence, not silently
equated with clean text.

## Normalization and preservation

Original source text is immutable. Generated documents retain original and
normalized SHA-256 values, not a committed raw corpus. The primary semantic
view uses NFC, verified HTML entity decoding, parser-based markup removal,
line-ending and whitespace normalization, non-breaking-space replacement,
control-character rejection, and URL removal. Separate lexical views provide
case folding and an explicitly fallback-only compatibility/diacritic-folded
variant.

The policy does not automatically remove punctuation, hyphens, apostrophes,
diacritics, or non-Latin scripts. It does not correct historical spelling,
names, places, transliteration, or terminology.

## Rights and public-safety boundary

Public availability of a catalogue record is not a blanket license to publish
all its prose or derived weights. Fields marked `REVIEW_REQUIRED` remain
subject to review packet bounds and artifact policy. Rights, provenance,
internal control text, source notes, compound-child notes, and full generated
documents are not committed as semantic inputs.

Committed object-level samples must be bounded, public-safe, and free of
internal UUIDs, held IDs, private notes, URLs, weights, vectors, and token
arrays.

## Intended use

This corpus may support offline comparison of field-separated lexical and
dense retrieval behavior, source/language leakage diagnostics, robustness
tests, representation-consistency checks, aspect disagreement analysis, and a
bounded later domain-review packet.

## Prohibited use

It must not support claims of historical relation, influence, contact,
causation, lineage, creator intent, importance, quality, canonicality,
probability, or world-history representativeness. It must not train or expose a
public model, generate translations or summaries, repair text with a language
model, or silently fuse NLP with `CG-CUR-4`, `M2`, `M5`, or `M7`.

## Generalization boundary

All findings are conditional on this exact public cohort, these frozen source
artifacts, the registered field semantics, the observed missingness, and the
exact model revisions. Results do not establish performance for held records,
unseen providers, other collections, other eras, other languages, richer
object descriptions, or expert design-history research questions.
