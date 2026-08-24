# Exploration task definitions

## Status and interpretation boundary

This document defines four different Exploration research tasks before any
metric or model is selected. A model that is useful for one task is not thereby
valid for another. All candidate outputs are `exploratory_derived_signal`
artifacts. They are not a `TraceSemanticEdge`, a semantic relation, a historical
claim, or a probability of relation.

This round does not authorize a public Exploration route, API, renderer, final
score, final weights, clustering model, probability model, or template
registry. Model benchmark results, a shortlist, and the round decision are
evaluation outputs; none is asserted here.

## Task A — symmetric object-local affinity

**Question.** Which public archive records share a balanced, explainable set of
governed or approved archive characteristics with one selected public record?

**Query form.** One public object identity already present in the deterministic
candidate index.

**Result form.** A bounded candidate list in which each result carries:

- per-family affinity contributions;
- jointly observable and unavailable families;
- a separate comparability profile;
- distinctive features;
- retrieval provenance;
- ignored duplicate derivations;
- source-bias, curatorial-attenuation, and interaction diagnostics; and
- explicit `historicalRelation=false`, `semanticRelation=false`, and
  `probability=false` declarations.

**Required behavior.** Pair profiles and any diagnostic scalar used to order
them must be symmetric. Reversing query and candidate must preserve family
scores and the diagnostic value. Stable ranking ties resolve by public
candidate ID. The selected object is always excluded.

**Relevant model families.** M1–M5, symmetric M6 configurations, and the
non-scalar M8 profile are Task A research candidates. Their inclusion in the
benchmark is not a selection.

**Non-goals.** A high Task A affinity must not be described as influence,
contact, lineage, shared intent, quality, importance, or likely historical
relation.

## Task B — user-conditioned factor retrieval

**Question.** Given explicit user-selected dimensions such as Theme, Medium,
Time, or Geography, which public records best satisfy the declared query?

**Query form.** A selected public object, an explicit filter set, or an explicit
set of approved family-qualified features. Query dimensions and any user
weights must be recorded in the run parameters.

**Result form.** A bounded retrieval ranking with the same explanation and
comparability channels required for Task A. It must additionally expose the
query-side conditions, query/document role, and the declared source-treatment
policy.

**Required behavior.** Asymmetry is permitted only when it is explicit and
reproducible. Swapping query and candidate may change an asymmetric result, but
the method version and parameters must make the reason inspectable. Query
weights are declared inputs, not learned weights and not inferred historical
importance.

**Relevant model families.** Asymmetric M6 Tversky variants and M7 BM25F-like
fielded retrieval are Task B research candidates. Symmetric Task A affinity is
not silently reused as user-conditioned retrieval.

## Task C — contrastive or serendipitous discovery

**Question.** Which records deliberately match on declared dimensions while
differing on another declared dimension?

Examples include:

- same theme and decade, different source;
- same medium, different governed geography; and
- same governed geography, different theme.

**Query form.** A positive-match constraint set plus at least one explicit
contrast dimension. The contrast dimension is part of the request, not a
post-hoc interpretation of a nearest neighbor.

**Result form.** A constraint-qualified candidate set showing both the matched
and deliberately distinctive dimensions. SOURCE-3 may express a cross-source
preference only in this dedicated task. SOURCE-4 may diversify a result set
after scoring without changing pair scores.

**Required behavior.** Task C is not ordinary nearest-neighbor ranking. A
difference is not negative evidence unless the contrast request names it, and
it never implies opposition, influence, or historical separation. This round
researches its data and model requirements only; it does not define a public
template.

## Task D — subset pattern exploration

**Question.** What concentration, rarity, missingness, or source-composition
pattern is visible in a selected public subset?

**Query form.** An explicitly selected public subset and a declared aggregate
question.

**Result form.** Bounded aggregate distributions, counts, supports,
concentration measures, missingness profiles, or source-composition summaries
with their denominators and input receipt.

**Required behavior.** Task D is aggregate analysis, not object-pair affinity.
It does not emit neighbors or a pair score. `rare` means low observed support;
it does not mean important. Missingness matching may be inspected in a
missingness-oriented mode but contributes zero to general affinity.

## Task dispatch contract

| Property | Task A | Task B | Task C | Task D |
| --- | --- | --- | --- | --- |
| Unit of analysis | object pair | ordered query/result | constrained pair/result | subset aggregate |
| Symmetry | required for scored variants | optional, declared | constraint-dependent | not applicable |
| Scalar required | no | no | no | no |
| Candidate index | required | required | required before constraint evaluation | optional subset index |
| Comparability | separate channel | separate channel | separate channel | aggregate observability report |
| Distinctive features | explanation | query mismatch explanation | first-class requested output | distributional contrast |
| Historical relation output | prohibited | prohibited | prohibited | prohibited |
| Ordinary nearest-neighbor semantics | candidate only | query retrieval only | prohibited | not applicable |

## Shared gates

Every task operates only on the 7,995-record public cohort. Held records,
internal UUIDs, and frozen database writes are prohibited. Candidate generation
and scoring remain separate. Deterministic retrieval and ranking use no seeded
randomness. Every scored signal must resolve to the 64-row lineage registry,
and the same source fact may contribute at most once to base affinity.

Raw curated Jaccard is M0, an isolated negative control and structural
diagnostic. Curatorial membership may support recall and provenance, but it is
not ranking evidence in the current independent basis. No task may import M0
as a production/public scorer or translate curated overlap into a relation.

Mechanical, recall, stability, hubness, bias, explanation, and human-review
evidence must be evaluated per task. Success for one task cannot select a model
for another.
