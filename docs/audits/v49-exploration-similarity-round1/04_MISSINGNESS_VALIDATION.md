# Missingness and comparability validation

## Evidence state

`VALIDATION_STATE=SEALED_PRECOMMIT_PASS`

Affinity among observed evidence and joint observability are separate outputs.
Comparability is not confidence, probability, or a historical-relation score.
Every scalar and non-scalar profile must expose observed and eligible family
counts, their ratio, jointly observable families, and unavailable families.

## Variants

| Variant | Affinity treatment | Mandatory visibility |
| --- | --- | --- |
| MISSING-A | available-family renormalization | full comparability profile |
| MISSING-B | conservative full eligible-family denominator | observed and eligible denominators |
| MISSING-C | observed affinity plus a peer comparability channel | neither channel may hide the other |
| MISSING-D | uncertainty-state exploration only | positive affinity credit fixed to zero |

Unknown creator/source states, qualified unknown values, no published movement
context, not-governed states, blank/unavailable values, and diagnostic geography
mapping states never create default positive affinity. Matching absence may be
reported only in MISSING-D.

## Required reconciliation

The verifier is fail-closed against any profile where:

- comparability is missing;
- observed or eligible counts are invalid;
- ratio differs from observed divided by eligible;
- jointly observable and unavailable sets do not partition eligible families;
- missingness appears in the base-affinity numerator;
- a non-applicable state is silently converted to missing;
- one-sided availability becomes a positive match; or
- pair reversal changes comparability for a symmetric model.

Temporal precision, geography mapping/qualification/multi-region state,
movement availability, and creator uncertainty remain qualifiers or
comparability/explanation data. Equal qualifiers are not independent affinity.

## Final receipt

```text
COMPARABILITY_CHANNEL_IMPLEMENTED=true
MISSINGNESS_VARIANT_COUNT=4
SHARED_UNKNOWN_POSITIVE_CREDIT_COUNT=0
NOT_APPLICABLE_AS_MISSING_COUNT=0
COMPARABILITY_P50=1
COMPARABILITY_P95=1
```

The benchmark evaluates 159,900 bounded ranked pairs; 156,539 share at least
one unknown-state diagnostic and still receive zero positive unknown credit.
Comparability minimum/median/P95/maximum are all 1 for this evaluated ranking
sample. This distribution does not reclassify comparability as confidence.

Evidence sources are `missingness-summary.json`, the central receipt, the
model/explanation samples, mechanical AX-003 and AX-010, and the independent
verifier. All applicable checks and EXP-SIM invariants pass.
