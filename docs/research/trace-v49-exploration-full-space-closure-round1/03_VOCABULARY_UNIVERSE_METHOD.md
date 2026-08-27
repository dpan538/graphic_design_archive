# Vocabulary-universe method

## Freeze rule

The candidate universe is the case-insensitive, Unicode-normalised, exact-label union of every governed candidate/end-point source below. Rows are included regardless of their historical pass, defer, reject, control, active, or inactive disposition. Exact forms and source-row identities are retained. No database text, metadata token, Search result, Context label, or Spacetime label may add a candidate.

Sources:

- Round 9 raw candidate registry and pass/defer/reject records;
- Round 10 input, derivation, and node-role decisions;
- Round 12 frozen research-candidate package;
- Round 13 vocabulary-gap evidence, decisions, and activation candidates;
- both endpoints of all 35 Round 14 assessments, including controls and failures;
- Round 16 scholarly additions' supported terms;
- all 26 current Round 16 active labels.

After the generated universe hash is frozen, an incidental discovery is appended to `future-vocabulary-candidates.tsv` and cannot enter this round.

## One-disposition rule

Every deduplicated candidate receives exactly one of:

- `ACTIVE_PRODUCT_VOCABULARY`
- `VALID_RESEARCH_ONLY`
- `DEFER_POLYSEMY`
- `DEFER_INSUFFICIENT_EVIDENCE`
- `REJECT_GENERIC`
- `REJECT_NOT_RELATIONAL`
- `REJECT_ONE_OFF_FORMULATION`
- `REJECT_STRUCTURAL_OR_INTERFACE_LABEL`

Earlier decisions are evidence, not automatically the final Round 16A disposition. A later governed split or scholarly addition may supersede an earlier defer for the narrower exact phrase; the earlier broad label remains separately classified.

## Active gate

An active row must contain a stable sense-bearing ID, exact and normalised forms, language, accepted attestation and academic-source records, a source-bounded sense, scope and ambiguity notes, at least one category binding, and a complete provenance chain. Product eligibility is decided before and independently of pair status. Multi-category membership is allowed. A legitimate but incompletely bounded term remains research-only or deferred; it is not activated to increase graph density.

The final generator rejects any active row lacking one of these requirements and reports the exact failure counts. Structural/interface labels can remain in the all-source universe but cannot be active product vocabulary.

