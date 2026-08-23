# Cross-dimensional validation

## Committed tables

| File | Rows | Columns | Validation |
| --- | ---: | ---: | --- |
| `06_MISSINGNESS_CENSUS.tsv` | 38 | 23 | PASS |
| `08_ONE_DIMENSION_FREQUENCIES.tsv` | 3,364 | 14 | PASS |
| `09_TWO_DIMENSION_INTERSECTIONS.tsv` | 6,146 | 24 | PASS |
| `10_THREE_DIMENSION_INTERSECTIONS.tsv` | 2,399 | 24 | PASS |
| `11_RARE_INTERSECTION_REGISTER.tsv` | 4,251 | 23 | PASS |
| `13_EXPLORATION_SIGNAL_REGISTRY.tsv` | 64 | 27 | PASS |
| `15_PATHOLOGICAL_SAMPLE_REGISTER.tsv` | 15 | 17 | PASS |

Every table is rectangular and stable-sorted. Every count/rate has a denominator. Pair and triple tables contain observed cells only; zero Cartesian cells and object-pair rows are absent.

The artifact workflow independently imported and round-tripped all seven files. Formula/error scan count is zero for every file, rendered previews were inspected, and all shapes above were confirmed visually.

## Cross-dimensional receipts

| Metric | Value |
| --- | ---: |
| Normalized records | 7,995 |
| Dimension membership events | 128,302 |
| Pair membership events | 192,973 |
| Triple membership events | 48,150 |
| Pair specifications / observed cells | 18 / 6,146 |
| Triple specifications / observed cells | 6 / 2,399 |
| Source concentration rows | 59 |
| Four-family concentration rows | 4 |

Cross deterministic SHA is `dc64fca6425e163f0bc7d3d20018086166482a8996ca6b99113860e883212f81`; the concentration-row SHA is `57f2eedd0a9c91d132b21de6c1cabc1496bc220e1c2f8d6273759d73a1100000`.

## Concentration reconciliation

Assignment denominators are source 7,995, decade 8,033, geography 7,996, and curated container 24,102. Distinct counts are 15/23/93/118. HHI values are 0.2881509041962984, 0.12388228508851257, 0.19532871738520585, and 0.15115428130139877 respectively.

Minimum source-subset support is 30. Conditional rates and lift remain `ANALYSIS_DIAGNOSTIC_NOT_A_RELATION`. Rare maximum count is 20 and rarity never implies importance.

## Verification result

The full verifier rederives the current cohort, compares committed bytes, checks all scoped raw/TSV files, and passes 18 of 18 invariants. Verification receipt SHA is sealed in `SHA256SUMS.txt`.
