# Source Coverage Rate v2

Scope: public surfaces plus main-sheet research-value diagnostics. v2 separates capacity fill from distribution and research quality.

## Summary

- source_pool_period_fill_rate: 100.00 (Former v1 source_coverage_rate; capacity/time fill only, capped at 100%.)
- strict_distribution_adjusted_source_coverage_rate: 28.96 (v1 strict diagnostic retained as a first-class warning signal.)
- period_surface_balance_rate: 100.00 (Surface count balance against v2 period targets; 2000-2026 target is intentionally higher.)
- period_quality_main_balance_rate: 44.23 (Quality main-sheet balance against v2 period targets.)
- region_surface_balance_rate: 6.71 (Surface count balance against v2 regional targets.)
- region_quality_main_balance_rate: 6.47 (Quality main-sheet balance against v2 regional targets.)
- source_visible_surface_rate: 97.80 (Surfaces with IMG01/IMG02/IMG03.)
- research_quality_adjusted_source_coverage_rate_v2: 2.80 (source_pool_period_fill * period_quality_main_balance * region_quality_main_balance * source_visible_rate.)

## Period Targets

- pre_1930: surfaces=2406, main=2358, quality_main=871, target=1700, surface_balance=100.00%, quality_balance=51.24%
- 1930_1970: surfaces=3684, main=3582, quality_main=1118, target=2000, surface_balance=100.00%, quality_balance=55.90%
- 1970_2000: surfaces=3283, main=3250, quality_main=966, target=2200, surface_balance=100.00%, quality_balance=43.91%
- 2000_2026: surfaces=3559, main=3530, quality_main=673, target=2600, surface_balance=100.00%, quality_balance=25.88%
- undated_or_unparsed: surfaces=748, main=699, quality_main=20, target=250, surface_balance=100.00%, quality_balance=8.00%

## Weakest Periods By Quality Main Balance

- undated_or_unparsed: quality_balance=8.00%, target=250
- 2000_2026: quality_balance=25.88%, target=2600
- 1970_2000: quality_balance=43.91%, target=2200
- pre_1930: quality_balance=51.24%, target=1700

## Weakest Regions By Quality Main Balance

- Africa: surfaces=0, quality_main=0, target=750, quality_balance=0.00%
- East Asia: surfaces=0, quality_main=0, target=750, quality_balance=0.00%
- Eastern Europe: surfaces=0, quality_main=0, target=650, quality_balance=0.00%
- Eastern Europe / Caucasus: surfaces=0, quality_main=0, target=650, quality_balance=0.00%
- Ethiopia: surfaces=10, quality_main=0, target=250, quality_balance=0.00%
- Europe: surfaces=0, quality_main=0, target=550, quality_balance=0.00%
- Global: surfaces=0, quality_main=0, target=400, quality_balance=0.00%
- Global / web / transnational: surfaces=0, quality_main=0, target=400, quality_balance=0.00%
- Latin America and the Caribbean: surfaces=0, quality_main=0, target=850, quality_balance=0.00%
- Middle East and North Africa: surfaces=0, quality_main=0, target=750, quality_balance=0.00%

## Interpretation

- `source_pool_period_fill_rate` can reach 100% while the archive is still structurally weak.
- `research_quality_adjusted_source_coverage_rate_v2` should be treated as the stricter release-facing source coverage diagnostic.
- v2 gives the 2000-2026 period a larger target because contemporary graphic design, graphic art, and visual communication are broader and more diverse in the internet period.
