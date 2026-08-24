# Model benchmark validation

## Evidence state

`VALIDATION_STATE=SEALED_PRECOMMIT_PASS`

The analysis suite evaluates M0 through M8 without historical-relation labels,
invented classification targets, embeddings, learned weights, clustering, or
visual-plausibility selection. Scalar exhaustive reference rankings stream the
exact 31,956,015 unordered public pairs and retain bounded top-50 heaps only.

## Model boundary

| Model | Research role | Shortlist eligibility |
| --- | --- | --- |
| M0 raw curated Jaccard | negative control and structural diagnostic | never |
| M1 unweighted family overlap | symmetric transparent baseline | gate-dependent |
| M2 IDF-weighted sparse cosine | symmetric family-normalized baseline | gate-dependent |
| M3 weighted Jaccard/Tanimoto | symmetric approved-feature baseline | gate-dependent |
| M4 Goodall-style rarity | symmetric bounded rarity experiment | gate-dependent |
| M5 Gower-style mixed profile | symmetric family-balanced experiment | gate-dependent |
| M6 Tversky contrast | symmetric or explicitly asymmetric by parameters | task/variant-dependent |
| M7 BM25F-like retrieval | explicitly asymmetric Task B experiment | Task B only |
| M8 Pareto/multi-channel | symmetric non-scalar profile | gate-dependent |

Every result must expose family contributions, true normalized contribution
shares, comparability, distinctive and unavailable features, ignored lineage
duplicates, optional separately residualized interaction evidence, method and
run pins, and false relation/probability flags.

## Evaluation evidence

The sealed benchmark reconciles:

- all declared model/parameter variants and their deterministic ranking hashes;
- the 15 mechanical axioms and shortlist applicability;
- symmetric reversal and explicit query asymmetry;
- MISSING-A through MISSING-D;
- global, within-family, and smoothed IDF;
- equal, availability-normalized, user-selected, and capped family weighting;
- TEMP-1 through TEMP-4 and sensitivity parameters;
- SOURCE-0 through SOURCE-4;
- CUR-W1 through CUR-W6;
- ablations and stability;
- hubness, source composition, and family dominance;
- exhaustive candidate recall; and
- explanation/run-receipt validation.

## Recoverable interaction-scorer rehearsal

The first pre-authoritative full-corpus attempt reached the real interaction
scorer and stopped when a tiny final proportional residual rounded negative.
Clipping the value to zero left the sum of emitted interaction rows above the
aggregate cap. The implementation was corrected to allocate non-balancer rows
first and reserve the largest raw row as the deterministic final balancer.

The model, explanation, benchmark, and verifier share one declared tolerance.
The former failing vector, 18,000 deterministic fuzz cases, and all four module
self-tests pass after the change. This is useful adversarial evidence but not
an authoritative full-corpus pass. No output from that attempt is accepted as
Run A, Run B, or final benchmark evidence.

## Final result fields

```text
MODEL_VARIANT_COUNT=25
MODEL_SHORTLIST_COUNT=3
MODEL_SHORTLIST_IDS=M2,M5,M7
MODEL_DECISION=MODEL_FAMILY_SHORTLISTED
MECHANICAL_AXIOM_COUNT=15
MECHANICAL_AXIOM_FAILURE_COUNT=0
UNEXPLAINED_SHORTLIST_RESULT_COUNT=0
ANALYSIS_RUN_COUNT=47
ANALYSIS_RUN_RECEIPT_FAILURE_COUNT=0
DETERMINISTIC_RUN_A_B_EQUAL=true
DETERMINISTIC_PAYLOAD_SHA256=c4ba0106e4a361c52f56106f86aa6b4cc360ff48ecb26019fc3d248aac9fde8a
```

All related TSVs pass the artifact workflow: model results 25x26, ablation
648x13, interaction methods 40x9, mechanical cases 15x14, blinded review packet
864x28, and analysis runs 47x1. The benchmark retains nine ablation-collapse
diagnostics and measured severe hubness; therefore it shortlists families
rather than selecting a provisional profile. The packet has 72 anchors and no
fabricated judgments or score labels.

The final decision is the permitted internal research state
`MODEL_FAMILY_SHORTLISTED`. It selects only the M2/M5/M7 model families—not a
model, parameter profile, weights, or public decision. Human-review packet
readiness is not misstated as completed researcher review. The independent
full verifier passes all 11 checks and all 24 EXP-SIM invariants.
