# Concentration and density analysis

## Observed-cell policy

The analysis commits only observed value/cell aggregates. It does not create zero-valued Cartesian rows. Unique object membership is enforced per value or cell before counting. Every rate retains its eligible or jointly observable denominator.

| Registry | Rows | Scope |
| --- | ---: | --- |
| One-dimensional frequencies | 3,364 | all usable observed values |
| Two-dimensional intersections | 6,146 | 18 bounded pair specifications |
| Three-dimensional intersections | 2,399 | 6 bounded triple specifications |
| Rare intersection register | 4,251 | observed pair/triple cells with count at most 20 |
| Density/rarity summary rows | 24 | bounded family/specification summaries |

The pair rows retain count, eligible denominator, joint-observable denominator, support rates, conditional observed rates, and lift diagnostics. The triple rows retain the same denominator discipline without inventing a final three-factor score.

## Four-family concentration receipt

Concentration is calculated from unique public-object value assignments. Assignment denominators may exceed 7,995 when an object has multiple governed values.

| Family | Eligible objects | Assignments | Distinct values | Top 1 count/share | Top 5 count/share | HHI | Shannon entropy | Normalized entropy |
| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| Source | 7,995 | 7,995 | 15 | 3,505 / 0.43839899937460913 | 7,326 / 0.9163227016885553 | 0.2881509041962984 | 1.622746730779968 | 0.5992306679246528 |
| Temporal decade | 7,995 | 8,033 | 23 | 1,898 / 0.23627536412299266 | 5,478 / 0.681937009834433 | 0.12388228508851257 | 2.436622733167872 | 0.7771096246292455 |
| Geography | 7,995 | 7,996 | 93 | 3,214 / 0.4019509754877439 | 5,609 / 0.7014757378689345 | 0.19532871738520585 | 2.5277965728429077 | 0.5576924624955911 |
| Curated container | 7,995 | 24,102 | 118 | 7,105 / 0.29478881420628994 | 18,379 / 0.7625508256576218 | 0.15115428130139877 | 2.524719942927906 | 0.5292154358685331 |

The four-row receipt SHA is `57f2eedd0a9c91d132b21de6c1cabc1496bc220e1c2f8d6273759d73a1100000`. Six signal-registry rows bind the native receipts directly; the generator does not invent proxy concentration values during TSV formatting.

## Rarity boundary

`RARE_INTERSECTION_CANDIDATE` means an observed cell has low support within its stated denominator. It does not mean important, historically absent, overlooked, high quality, unusual in the wider historical field, or likely to be related to another record.

Geographic layout distance remains `DEFER`: map projection coordinates are not research distance. Rights/image state remains `DEFER_NOT_GOVERNED`. No expansion is permitted without a governed semantic basis.
