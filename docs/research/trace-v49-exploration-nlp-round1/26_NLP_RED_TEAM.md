# NLP epistemic and systems red team

## Purpose and evidence state

`DOCUMENT_STATE=FINAL_EVIDENCE_BOUND_AUDIT_ONLY`

This red team attempts to falsify the corpus and baseline conclusions. A good
retrieval metric cannot waive a held-data, field-semantics, leakage, license,
hubness, determinism, or interpretation failure.

## 1. Cohort and field-governance attacks

Adversarial cases include a held record placed in a source mirror, an unknown
ID queried through local tooling, a title repeated in a registration/dossier
projection, a source narrative mislabeled as object description, and an
unregistered future field entering by schema flattening.

Required behavior: fail closed; normalize no held text; expose no held/unknown
distinction; count one public identity once; reject an unregistered field; and
keep source narrative isolated.

Final outcome: `PASS`; the 7,995/7,928 public/held boundary has zero overlap,
zero held inputs, and all 37 text fields are classified.

## 2. Normalization and transformation attacks

The normalizer is attacked with CRLF, non-breaking spaces, entity encoding,
markup, script/style elements, URLs, disallowed controls, composed/decomposed
Unicode, diacritics, apostrophes, hyphens, and non-Latin scripts.

Required behavior: preserve immutable original hashes; use NFC in the semantic
view; keep compatibility folding separate; reject disallowed controls; and
never invoke translation, spelling repair, summarization, classification, or
generated text.

Final outcome: `PASS`; original hashes are preserved, generated transformation
counts are zero, and normalization remains a separately versioned view.

## 3. Identity and pair-label attacks

Same title, same common word, same source, same language, same date, rights
text, source-name text, and provider boilerplate are injected as tempting
positives. Only external immutable identity evidence may create a Task A
positive. Task B must remain empty when no archive-native verified variant
exists.

Required behavior: keep 4,344 distinct-identity same-title stress pairs out of
the positive registry; report zero Task B positives and `N/A` metrics; describe
the three Task A pairs as representation consistency only.

Final outcome: `PASS_WITH_LIMITATION`; the registry has three mechanically
verified representation pairs, zero Task B positives, and 309 controls. Task B
therefore remains `N/A`.

## 4. Source, language, and label-leakage attacks

Models are challenged with literal source names, URLs, provider templates,
source-conditioned prose, medium/theme/object-type labels, geographic displays,
same-language neighborhoods, and short named entities forced into a language
class.

Required behavior: report same-source/language rates and probes; compare
original, source-masked, boilerplate-decision, target-label-masked, and
all-governed-label-masked variants; allow `MIXED`/`UNDETERMINED`; and call a
collapse after literal masking “label leakage,” not semantic understanding.

Final outcome: `BLOCKED`; both dense title models exceed the frozen
source-provider-dominance gate. `SOURCE_LEAKAGE_BLOCKER_COUNT=2`, while language
leakage remains `NOT_RUN` because no reliable language-label cohort was selected.

## 5. Model-artifact and execution attacks

Attacks include a mutable `main` revision, changed artifact bytes, hosted
inference, concurrent model loads, unreviewed remote code, pickle weights,
non-commercial weights winning a production shortlist, and a model-specific
prompt replaced with a universal prompt.

Required behavior: immutable revision and hash checks before import; official
repository only; local/offline inference; one active model; no unreviewed code;
separate license/eligibility/execution states; and exact query/document mode in
every receipt.

Final outcome: `PASS`; the two executed candidates use verified immutable local
safetensor snapshots, local-only loading, `trust_remote_code=false`, and zero
hosted inference calls.

## 6. Truncation, missingness, and aspect attacks

Long source narratives are placed beside short titles, unavailable aspects are
encoded as zero text, padded batches are ordered adversarially, and subject or
source narrative is inserted into the title composite.

Required behavior: deterministic length buckets, field-specific caps,
model-input-only head truncation receipts, exact availability masks, no
unavailable queries, canonical-order restoration, title-only v1 composite, and
separate aspect results.

Final outcome: `PASS_WITH_LIMITATION`; all available-aspect cohorts and missingness
masks are explicit, but the governed object-description aspect has zero rows and
no aspect fusion is selected.

## 7. Hubness, anisotropy, and correction attacks

The audit tests whether generic titles, long provider narratives, source,
language, text length, boilerplate, or metadata completeness become hubs.
Mean cosine, variance, norm distributions, first-PC share, and k-occurrence at
10/20/50 must be visible.

No mean centering, component removal, whitening, local scaling, or mutual
proximity can be selected solely because one Gini statistic improves. A
correction must also preserve known-pair behavior, ranking stability, and
leakage accounting.

Final outcome: `PARTIAL`; core diagnostics were computed, but the frozen suite
remains `NOT_RUN` overall because reliable language associations and
pre-normalization norms are unavailable. No correction was tested or selected.

## 8. Structured-channel and interpretation attacks

High NLP/structured agreement is presented as truth; low agreement is called
an error; a hybrid is tuned to reproduce `M2`, `M5`, or `M7`; and an affinity
score is renamed a relation probability.

Required behavior: independent channels, no fusion selection or weights,
bounded disagreement categories, no historical/semantic relation claim, and
all relation/probability flags false.

Final outcome: `PASS_WITH_LIMITATION`; the bounded disagreement study remains
diagnostic and `PARTIAL`, with all relation/probability and fusion flags false.

## 9. Materialization and changed-scope attacks

The commit is scanned for raw full corpus text, held text, private notes,
internal UUIDs, model/tokenizer files, embeddings, token arrays, full
nearest-neighbor or pair matrices, database mutation, Search/Context/Spacetime
changes, `CG-CUR-4` or `M2/M5/M7` edits, dependencies, routes, APIs, renderers,
and vector databases.

Required behavior: zero forbidden files and changes; bounded public-safe review
rows only; all regressions pass.

Final outcome: `PASS_FOR_BOUNDED_EVIDENCE_PACKAGE`; the sealed summary reports
zero database/Search/specification changes, zero forbidden committed matrices or
weights, and zero internal UUID or held-identifier exposure. Final Git and build
state are recorded separately in the final recovery receipt.

## Required invariant matrix

| Invariant | Assertion | Final status |
| --- | --- | --- |
| `NLP-INV-001` | only 7,995 public objects enter the NLP corpus | `PASS` |
| `NLP-INV-002` | no held object or text enters model input | `PASS` |
| `NLP-INV-003` | every included text field has a governed role and decision | `PASS` |
| `NLP-INV-004` | source narrative is not merged with object-semantic text | `PASS` |
| `NLP-INV-005` | rights, provenance, and boilerplate add zero object-semantic affinity | `PASS` |
| `NLP-INV-006` | original source text is never overwritten | `PASS` |
| `NLP-INV-007` | no translation or generated summary enters the corpus | `PASS` |
| `NLP-INV-008` | same title does not imply same object identity | `PASS` |
| `NLP-INV-009` | every positive pair has an external verification source | `PASS` |
| `NLP-INV-010` | proxy targets are masked in the masked variant | `PASS` |
| `NLP-INV-011` | source identity is measured as leakage | `PASS` |
| `NLP-INV-012` | language identity is measured and not semantic truth | `PASS` |
| `NLP-INV-013` | every dense model uses an exact pinned revision | `PASS` |
| `NLP-INV-014` | every model has license and eligibility decisions | `PASS` |
| `NLP-INV-015` | unreviewed remote code cannot execute | `PASS` |
| `NLP-INV-016` | no model weight is committed | `PASS` |
| `NLP-INV-017` | no full embedding matrix is committed | `PASS` |
| `NLP-INV-018` | every aspect remains separately evaluable | `PASS` |
| `NLP-INV-019` | no NLP score becomes a historical relation | `PASS` |
| `NLP-INV-020` | no NLP score is described as probability | `PASS` |
| `NLP-INV-021` | NLP does not modify `CG-CUR-4` | `PASS` |
| `NLP-INV-022` | NLP does not modify `M2/M5/M7` | `PASS` |
| `NLP-INV-023` | structured and NLP channels remain separate | `PASS` |
| `NLP-INV-024` | seeded randomness changes no corpus, embedding, neighbor, or score | `PASS` |
| `NLP-INV-025` | every committed review row is public-safe | `PASS` |
| `NLP-INV-026` | leakage and hubness reports govern shortlist decisions | `PASS` |

Any non-pass invariant narrows the decision or forces a recoverable checkpoint.
It cannot be waived to manufacture completion.
