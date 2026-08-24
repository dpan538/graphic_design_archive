# Hubness and bias validation

## Evidence state

`VALIDATION_STATE=SEALED_PRECOMMIT_PASS_WITH_DIAGNOSTIC_CAUTION`

Hubness, source composition, curation breadth, and family dominance are failure
diagnostics. They are not silently normalized away and are not historical
properties of the objects.

## Hubness protocol

For every scalar model and shortlist variant, k-occurrence distributions at
k=10, 20, and 50 report mean, variance, skewness, Gini, top-1% occurrence
share, maximum occurrence, and zero-occurrence object count. Association rows
inspect dominant source, broad curated membership, common medium/theme,
metadata observability, geography, and decade.

If the declared severe-hubness rule fires, analysis-only corrections cover:

- local scaling;
- mutual-proximity/global-scaling-style transformation; and
- reciprocal-neighbor filtering.

Correction evaluation reports hub reduction, top-k stability, explanation
complexity, symmetry, recall, and source bias. No correction is selected merely
because one hub statistic improves.

## Source and family-dominance protocol

Every result set reports top-1 source share, source HHI, and cross-source rate
against corpus composition. SOURCE-0 through SOURCE-4 remain distinct policies;
same source is not automatically positive affinity. SOURCE-3 applies only to a
declared contrastive task, while SOURCE-4 diversifies ranking order without
changing pair scores.

Family diagnostics distinguish contribution units in final-score space from
true normalized contribution shares. Positive-result shares must sum to one.
The benchmark reports median and P95 maximum-family share, the fraction of
queries above 80%, and source- and curation-dominated query rates. The
explanation validator must recompute these values rather than trust their outer
hash.

## Curatorial boundary

The current lineage basis has no independent curatorial scoring signal. CUR-W
variants measure fanout, support attenuation, stability, hubness, source
concentration, and explanation clarity; raw curated membership supplies no
base-affinity contribution. Broad-container dominance and curatorial parent
duplication failures must be reported explicitly.

## Final receipt

```text
HUBNESS_K_VALUES=10,20,50
SHORTLIST_TOP1_PERCENT_OCCURRENCE_SHARE=0.26864915572232645
SHORTLIST_MAX_K_OCCURRENCE=1653
SHORTLIST_HUBNESS_GINI=0.7446896993547796
SOURCE_DOMINATED_QUERY_RATE=0
CURATION_DOMINATED_QUERY_RATE=0
MAX_FAMILY_CONTRIBUTION_P95=0.4
BROAD_CONTAINER_DOMINANCE_FAILURE_COUNT=0
CURATORIAL_PARENT_DUPLICATION_FAILURE_COUNT=0
HUBNESS_CORRECTION_TESTED=true
HUBNESS_CORRECTION_SELECTED=false
```

The artifact workflow validates 15x15 source/family rows and 72x13 hubness
rows. The raw evidence adds 24 bias rows, 3,576 categorical-association rows,
and nine correction rows. All three shortlist families trigger severe-hubness
diagnostics; corrections remain analysis-only and unselected because they add
explanation complexity and change rankings materially. This caution is a
reason for family shortlisting rather than provisional-profile selection.

Evidence sources are `12_SOURCE_BIAS_AND_FAMILY_DOMINANCE.tsv`,
`13_HUBNESS_ANALYSIS.tsv`, `hubness-summary.json`, the curatorial and ablation
receipts, standalone explanation validation, and the passing independent full
verifier. The caution is a documented research result, not a failed gate.
