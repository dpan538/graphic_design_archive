# Leakage and hubness validation

## Evidence state

`DOCUMENT_STATE=SEALED`

Leakage and hubness are decision gates, not optional descriptive appendices.
High source or language predictability is a diagnostic, not a quality score.

## Source and language leakage

Every applicable lexical/dense model and aspect reports same-source neighbor
rate, cross-source rate, top-k source distribution, source HHI, and a simple
source probe where statistically meaningful. Reliable language labels, if any,
receive analogous same-language/cross-language and probe diagnostics.

The comparison variants are original approved input, source-identity masked,
registered boilerplate decisions applied, target structured label masked, and
all governed Context labels masked. Source names and URLs are masked only by
registered deterministic rules.

```text
BEST_MODEL_SAME_SOURCE_NEIGHBOR_RATE=N/A_NO_MODEL_SELECTED
BEST_MODEL_CROSS_SOURCE_RATE=N/A_NO_MODEL_SELECTED
BEST_MODEL_SOURCE_HHI=N/A_NO_MODEL_SELECTED
BEST_MODEL_SOURCE_PROBE_MACRO_F1=N/A_NO_MODEL_SELECTED
SOURCE_PROBE_MAJORITY_MACRO_F1=N/A_NO_MODEL_SELECTED

BEST_MODEL_SAME_LANGUAGE_NEIGHBOR_RATE=N/A_NO_MODEL_SELECTED_AND_NO_RELIABLE_LANGUAGE_LABEL_COHORT
BEST_MODEL_CROSS_LANGUAGE_RATE=N/A_NO_MODEL_SELECTED_AND_NO_RELIABLE_LANGUAGE_LABEL_COHORT
BEST_MODEL_LANGUAGE_PROBE_MACRO_F1=N/A_NO_MODEL_SELECTED_AND_NO_RELIABLE_LANGUAGE_LABEL_COHORT
LANGUAGE_PROBE_MAJORITY_MACRO_F1=N/A_NO_RELIABLE_LANGUAGE_LABEL_COHORT

SOURCE_LEAKAGE_BLOCKER_COUNT=2
LANGUAGE_LEAKAGE_BLOCKER_COUNT=0
```

The decision-blocking title diagnostics are retained without calling either
model “best”: `NLP-D1` has same-source@20
`0.6982864290181363`, cross-source@20 `0.3017135709818637`, mean query-source
HHI@20 `0.6869949968730457`, and source-probe macro-F1
`0.3941585872995411` against a `0.0406376811594203` majority macro-F1
baseline. The frozen decision census compares dense title same-source@20 to
the corpus source HHI `0.2881509041962984`; `NLP-D1` is `0.6982864290181363`
and `NLP-D3` is `0.7862539086929331`. The blocker model IDs are
`NLP-D1,NLP-D3`. Lexical leakage metrics remain reported, but the frozen
blocker census is specifically the two dense title models.

If reliable language labels are unavailable, probe metrics are `N/A`; source or
script cannot be substituted as language ground truth.

## Boilerplate and label robustness

```text
BOILERPLATE_REMOVAL_TOP20_OVERLAP=N/A_NO_AUTHORIZED_REMOVE_RULE
SOURCE_MASKING_TOP20_OVERLAP=1.0
MARKUP_CLEANING_TOP20_OVERLAP=N/A_NOT_RUN_NO_AUTHORIZED_PRECOMPUTED_VARIANT
TARGET_LABEL_MASKING_TOP20_OVERLAP=N/A_METADATA_HOLDOUT_REPORTED_SEPARATELY
ALL_GOVERNED_LABEL_MASKING_TOP20_OVERLAP=N/A_METADATA_HOLDOUT_REPORTED_SEPARATELY
```

The current boilerplate registry has no authorized automatic removal. A
boilerplate-removed run must therefore state unchanged/`N/A` unless a later
explicit rule authorizes mutation; held candidates cannot be silently removed.

## Hubness

For k=10, 20, and 50, every dense model/aspect reports occurrence Gini,
skewness, top-one-percent share, maximum occurrence, and zero-occurrence count.
Associations with source, script/language, text length, boilerplate, generic
title, and metadata completeness are included where data support them.

```text
BEST_MODEL_HUBNESS_GINI_K20=N/A_NO_MODEL_SELECTED
BEST_MODEL_TOP1_PERCENT_OCCURRENCE_SHARE_K20=N/A_NO_MODEL_SELECTED
BEST_MODEL_MAX_OCCURRENCE_K20=N/A_NO_MODEL_SELECTED
BEST_MODEL_ZERO_OCCURRENCE_COUNT_K20=N/A_NO_MODEL_SELECTED
```

## Anisotropy

Every dense space reports mean sampled cosine, cosine variance, nearest-neighbor
distance distribution, norm distribution before/after L2 normalization, and
first-PC variance share where practical.

```text
BEST_MODEL_MEAN_SAMPLED_COSINE=N/A_NO_MODEL_SELECTED
BEST_MODEL_COSINE_VARIANCE=N/A_NO_MODEL_SELECTED
BEST_MODEL_FIRST_PC_VARIANCE_SHARE=N/A_NO_MODEL_SELECTED
```

No centering, whitening, component removal, local scaling, or mutual proximity
is silently applied. If a correction is tested, it remains analysis-only and
must report known-pair retrieval, leakage, hubness, stability, and explanation
cost.

```text
HUBNESS_CORRECTION_TESTED=false
HUBNESS_CORRECTION_SELECTED=false
```

## Final validation

```text
NLP_SOURCE_LEAKAGE_TESTS=PASS
NLP_LANGUAGE_LEAKAGE_TESTS=PASS
NLP_HUBNESS_TESTS=PASS
NLP_ROBUSTNESS_TESTS=PASS
LEAKAGE_HUBNESS_RECEIPT_SHA256=02569700d597ae002e159eb65a2aa905587782b2983ec1d1eac03265fe259b1e
```

The source-masking overlap is the lexical-title L0--L3 value at k=20; no
SHA-pinned dense masked re-encoding was available. These four `PASS` values
mean the assertions validated the reported evidence and fail-closed statuses.
They do not convert the reliable-language diagnostic, missing pre-normalization
norms, or unexecuted robustness variants into completed scientific results.
The aggregate receipt hash is the sealed analysis summary's
`analysisSummarySha256`.
