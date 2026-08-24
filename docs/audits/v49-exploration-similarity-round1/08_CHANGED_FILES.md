# Changed-file boundary

## Inventory state

`INVENTORY_STATE=FINAL_CONTENT_COMPLETE_AWAITING_GIT_RECEIPT`

The read-only tree comparison against source commit
`0e311f0b88b4adc3cbfe2080ac98d622013cc6d3` resolves exactly 67 authorized
paths: one modified path and 66 new paths. It includes all 24 research files,
all 13 bounded raw receipts, nine audit narratives, both integrity ledgers, 18
analysis scripts, and the Project Log closure. No unauthorized or protected
path appears. Git commit/push identity remains intentionally unclaimed.

## Authorized scope

Changes are limited to:

- additive deterministic analysis scripts under
  `scripts/exploration-v49-similarity/`;
- exactly 24 Round 6 research artifacts under
  `docs/research/trace-v49-exploration-similarity-round1/`;
- nine audit narratives, 13 bounded raw JSON receipts, `MANIFEST.tsv`, and
  `SHA256SUMS.txt` under
  `docs/audits/v49-exploration-similarity-round1/`; and
- one additive Round 6 closure entry in `PROJECT_LOG.md`.

No TSV belongs to the audit directory. No full pair matrix, cache, row-spec
intermediate, rendered preview, normalized cohort, or run-output scratch file
belongs in Git.

## Protected boundaries

| Boundary | Required final result |
| --- | --- |
| Database files changed | 0 |
| Canonical release changed | false |
| Search files changed | 0 |
| Context semantics/governance/projection changed | false / false / false |
| Spacetime governance/projection changed | false / false |
| Prior research or audit packages changed | 0 |
| Runtime/frontend dependency added | 0 |
| Exploration public route/API/renderer added | 0 / 0 / 0 |
| Pair matrix committed | false |

## Exact final content paths

```text
SOURCE_SHA=0e311f0b88b4adc3cbfe2080ac98d622013cc6d3
FINAL_PATH_COUNT=67
MODIFIED_PATH_COUNT=1
NEW_PATH_COUNT=66
AUTHORIZED_PATH_COUNT=67
UNAUTHORIZED_PATH_COUNT=0
PROJECT_LOG_UPDATED=true
FINAL_GIT_STATUS=AWAITING_PRECOMMIT_RECEIPT
```

### Modified path (1)

```text
PROJECT_LOG.md
```

### New research paths (24)

```text
docs/research/trace-v49-exploration-similarity-round1/00_EXECUTIVE_DECISION.md
docs/research/trace-v49-exploration-similarity-round1/01_EXPLORATION_TASK_DEFINITIONS.md
docs/research/trace-v49-exploration-similarity-round1/02_SIMILARITY_LITERATURE_AND_APPLICABILITY.md
docs/research/trace-v49-exploration-similarity-round1/03_SIGNAL_LINEAGE_REGISTRY.tsv
docs/research/trace-v49-exploration-similarity-round1/04_INDEPENDENT_SIGNAL_BASIS.md
docs/research/trace-v49-exploration-similarity-round1/05_EVALUATION_PROTOCOL.md
docs/research/trace-v49-exploration-similarity-round1/06_CANDIDATE_GENERATION_ARCHITECTURE.md
docs/research/trace-v49-exploration-similarity-round1/07_CURATORIAL_ATTENUATION_EXPERIMENTS.tsv
docs/research/trace-v49-exploration-similarity-round1/08_MISSINGNESS_AND_COMPARABILITY.md
docs/research/trace-v49-exploration-similarity-round1/09_MODEL_SPECIFICATIONS.md
docs/research/trace-v49-exploration-similarity-round1/10_MODEL_BENCHMARK_RESULTS.tsv
docs/research/trace-v49-exploration-similarity-round1/11_CANDIDATE_RECALL_RESULTS.tsv
docs/research/trace-v49-exploration-similarity-round1/12_SOURCE_BIAS_AND_FAMILY_DOMINANCE.tsv
docs/research/trace-v49-exploration-similarity-round1/13_HUBNESS_ANALYSIS.tsv
docs/research/trace-v49-exploration-similarity-round1/14_ABLATION_AND_STABILITY.tsv
docs/research/trace-v49-exploration-similarity-round1/15_INTERACTION_STATISTICS_REVIEW.tsv
docs/research/trace-v49-exploration-similarity-round1/16_MECHANICAL_EXPECTATION_CASES.tsv
docs/research/trace-v49-exploration-similarity-round1/17_HUMAN_REVIEW_PACKET.tsv
docs/research/trace-v49-exploration-similarity-round1/18_EXPLANATION_CONTRACT.md
docs/research/trace-v49-exploration-similarity-round1/19_ANALYSIS_RUN_REGISTER.tsv
docs/research/trace-v49-exploration-similarity-round1/20_PERFORMANCE_AND_ARCHITECTURE.md
docs/research/trace-v49-exploration-similarity-round1/21_RED_TEAM.md
docs/research/trace-v49-exploration-similarity-round1/22_MODEL_SHORTLIST_DECISION.md
docs/research/trace-v49-exploration-similarity-round1/23_ROUND_DECISION.md
```

### New audit paths (24)

```text
docs/audits/v49-exploration-similarity-round1/00_EXECUTIVE_RECEIPT.md
docs/audits/v49-exploration-similarity-round1/01_SIGNAL_LINEAGE_VALIDATION.md
docs/audits/v49-exploration-similarity-round1/02_CANDIDATE_INDEX_VALIDATION.md
docs/audits/v49-exploration-similarity-round1/03_MODEL_BENCHMARK_VALIDATION.md
docs/audits/v49-exploration-similarity-round1/04_MISSINGNESS_VALIDATION.md
docs/audits/v49-exploration-similarity-round1/05_HUBNESS_AND_BIAS_VALIDATION.md
docs/audits/v49-exploration-similarity-round1/06_PERFORMANCE.md
docs/audits/v49-exploration-similarity-round1/07_SECURITY_BOUNDARY.md
docs/audits/v49-exploration-similarity-round1/08_CHANGED_FILES.md
docs/audits/v49-exploration-similarity-round1/MANIFEST.tsv
docs/audits/v49-exploration-similarity-round1/SHA256SUMS.txt
docs/audits/v49-exploration-similarity-round1/raw/ablation-summary.json
docs/audits/v49-exploration-similarity-round1/raw/analysis-run-summary.json
docs/audits/v49-exploration-similarity-round1/raw/candidate-index-summary.json
docs/audits/v49-exploration-similarity-round1/raw/exploration-similarity-evaluation-summary.json
docs/audits/v49-exploration-similarity-round1/raw/hubness-summary.json
docs/audits/v49-exploration-similarity-round1/raw/human-review-summary.json
docs/audits/v49-exploration-similarity-round1/raw/independent-basis-summary.json
docs/audits/v49-exploration-similarity-round1/raw/interaction-summary.json
docs/audits/v49-exploration-similarity-round1/raw/missingness-summary.json
docs/audits/v49-exploration-similarity-round1/raw/model-benchmark-summary.json
docs/audits/v49-exploration-similarity-round1/raw/performance-summary.json
docs/audits/v49-exploration-similarity-round1/raw/security-summary.json
docs/audits/v49-exploration-similarity-round1/raw/signal-lineage-summary.json
```

### New analysis-script paths (18)

```text
scripts/exploration-v49-similarity/ablation.py
scripts/exploration-v49-similarity/analysis_run_receipts.py
scripts/exploration-v49-similarity/benchmark_round1.py
scripts/exploration-v49-similarity/candidate_index.py
scripts/exploration-v49-similarity/common.py
scripts/exploration-v49-similarity/curatorial_attenuation.py
scripts/exploration-v49-similarity/evidence_preparation.py
scripts/exploration-v49-similarity/explanation.py
scripts/exploration-v49-similarity/hubness.py
scripts/exploration-v49-similarity/human_review_packet.py
scripts/exploration-v49-similarity/independent_feature_basis.py
scripts/exploration-v49-similarity/interaction_statistics.py
scripts/exploration-v49-similarity/mechanical_expectations.py
scripts/exploration-v49-similarity/missingness_comparability.py
scripts/exploration-v49-similarity/model_baselines.py
scripts/exploration-v49-similarity/negative_control.py
scripts/exploration-v49-similarity/signal_lineage.py
scripts/exploration-v49-similarity/verify_round1.py
```

This inventory reconciles the exact path classes and counts. It excludes Git
metadata, temporary benchmark caches, artifact-tool scratch files, rendered
previews, and unrelated user changes.

## Git boundary

Commit, push, local/remote SHA equality, ahead/behind state, and clean-worktree
claims are not made here. The integrating agent updates those receipts only
after each operation succeeds. No PR, merge, or deployment is authorized.
