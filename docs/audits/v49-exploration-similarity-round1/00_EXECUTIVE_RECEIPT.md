# TRACE v49 Round 6 executive audit receipt

## Package state

`AUDIT_PACKAGE_STATE=SEALED_PRECOMMIT_PASS`

This package audits Exploration Affinity Research Round 1 at source commit
`0e311f0b88b4adc3cbfe2080ac98d622013cc6d3`. It covers a 7,995-object public
cohort and exactly 31,956,015 possible unordered public-object pairs. Held
objects in the evaluation cohort are fixed at zero.

Authoritative exhaustive Runs A and B, final TSV validation, the independent
full verifier, protected-product regressions, the production build, the
changed-file inventory, and the Project Log update are complete and pass. The
only remaining identity fields are the post-commit/post-push Git receipts.

## Evidence inventory contract

The final research directory contains exactly 24 artifacts: 13 Markdown
narratives and 11 TSVs. The final audit directory contains nine Markdown
narratives, `MANIFEST.tsv`, `SHA256SUMS.txt`, and exactly 13 bounded raw JSON
receipts:

| Raw receipt | Narrative role |
| --- | --- |
| `exploration-similarity-evaluation-summary.json` | central full-corpus decision and cross-artifact binding |
| `signal-lineage-summary.json` | 64-signal classification, source-fact groups, and M0 boundary |
| `independent-basis-summary.json` | independent basis units, families, and curatorial residual result |
| `candidate-index-summary.json` | public-only index, CG-CUR results, recall, reduction, and index hashes |
| `model-benchmark-summary.json` | M0–M8 variants, exhaustive ranking hashes, profiles, and shortlist evidence |
| `missingness-summary.json` | MISSING-A–D behavior and comparability distribution |
| `interaction-summary.json` | registry cells, method/threshold grid, residual scoring, and parent-cap checks |
| `hubness-summary.json` | k-occurrence, source/family dominance, categorical associations, and corrections |
| `ablation-summary.json` | leave-family-out and sensitivity stability rows |
| `human-review-summary.json` | deterministic blinded packet readiness and explanation validation |
| `performance-summary.json` | timing, memory, bounded-artifact, and pair-matrix boundaries |
| `analysis-run-summary.json` | release/projection/registry/index/cohort-pinned run receipts |
| `security-summary.json` | import, held-data, UUID, pair-row, relation-language, and protected-boundary scans |

The raw receipts are bounded summaries. They contain no full pair matrix,
normalized object rows, private source corpus, or held cohort.

## Immutable decisions

```text
RAW_CURATED_JACCARD_PRODUCTION_ELIGIBLE=false
PUBLIC_SIMILARITY_MODEL_SELECTED=false
PUBLIC_SIMILARITY_WEIGHTS_SELECTED=false
PROBABILITY_MODEL_SELECTED=false
CLUSTERING_MODEL_SELECTED=false
FULL_PAIR_MATRIX_COMMITTED=false
FULL_PAIR_MATRIX_IN_CLIENT=false
HUMAN_REVIEW_COMPLETED=false
PR_CREATED=false
MERGED=false
DEPLOYED=false
```

## Decision and gate fields

| Field | Status |
| --- | --- |
| Phase | `COMPLETE`; sealed pre-commit research checkpoint |
| Model decision | `MODEL_FAMILY_SHORTLISTED`; M2/M5/M7 |
| Candidate architecture | CG-CUR-4 selected |
| Deterministic Run A/B equality | PASS; `c4ba0106e4a361c52f56106f86aa6b4cc360ff48ecb26019fc3d248aac9fde8a` |
| Independent full verifier | PASS; 11 checks and EXP-SIM-INV-001 through EXP-SIM-INV-024 |
| 15 mechanical axioms | PASS, zero failures |
| 11 TSV artifact validations | PASS, import/inspect/error-scan/render/visual |
| Context/Spacetime/Search/TRACE/Read Platform/API regressions | PASS |
| Production build | PASS; Next.js 15.5.18, 46/46 static pages |
| Research/audit integrity ledgers | PASS; exact pre-commit package bytes sealed |

Runs A and B each visited all 31,956,015 pairs from independent cache/output
locations. CG-CUR-4 yields pool P50/P95/P99/MAX 3,008/3,662/5,644/5,991,
zero empty/near-full pools, and minimum recall@10/20/50 of
0.9998499061913696/0.9995809881175735/0.9974158849280801. The benchmark covers
25 model variants, 216 ablation variants, 47 run receipts, 72 review anchors,
and 864 validated explanations.

The one-time spreadsheet marker ran exactly once. The 11 TSV data shapes are
64x16, 9x33, 25x26, 72x19, 15x15, 72x13, 648x13, 40x9, 15x14, 864x28, and
47x1. Formula/error and visual-render failures are zero; total TSV bytes are
918,719.

The authoritative verifier passed all 11 top-level checks and all 24 numbered
EXP-SIM invariants over exactly 24 research files and 11 research TSVs. Full
and runtime TypeScript checks pass. Search projects 7,995 public records and
7,928 indexed records with projection SHA prefix `35a6b7e1` and passes 14
tests; TRACE passes 19 checks and 16 invariants; Read Platform and `pageByKey`
pass. Context passes its 7,995-object / 25-family / 16,106-row projection
(SHA prefix `825f6e`), API, 22-rule full-cohort require-build governance,
runtime, 36/18 synthetic Canvas case, and 7,995-object / 31,980-row / 18-family
post-build Canvas case. Spacetime passes projection (SHA prefix `f751b0`),
20-rule / 7,995-object / 373-record governance, GIS, 373/351 runtime, and
require-build API checks. The production build passes with all 46 pages,
including Context at 18 kB / 120 kB and Spacetime at 21.8 kB / 127 kB. The
only emitted diagnostics are expected Node SQLite and module-type warnings;
there are no blockers.

## Recoverable rehearsal ledger

One pre-authoritative full-corpus attempt reached the real interaction scorer
and correctly stopped when proportional residual rounding produced a tiny
negative final row. Clipping it made the emitted row sum exceed the aggregate
interaction cap. The implementation now reserves the largest raw interaction
row as a deterministic final balancer and applies a shared declared
reconciliation tolerance across model, explanation, benchmark, and verifier.
The former failing vector, 18,000 deterministic fuzz cases, and all four module
self-tests pass after that repair.

This is a recoverable implementation rehearsal, not an authoritative Run A or
Run B, and no central benchmark receipt from it is accepted into this package.

## Seal rule

The research file set is exact, all raw and TSV bytes are independently
verified, Runs A and B agree on deterministic material, all required
regressions pass, the changed-file scope is reconciled, and `MANIFEST.tsv`
plus `SHA256SUMS.txt` seal the final pre-commit bytes. Git final/remote identity
is reported only after the corresponding commit and push operations succeed.
