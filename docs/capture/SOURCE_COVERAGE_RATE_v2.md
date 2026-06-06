# Source Coverage Rate v2

Scope: public surfaces plus main-sheet research-value diagnostics. v2 separates capacity fill from distribution and research quality.

## Summary

- source_pool_period_fill_rate: 100.00 (Former v1 source_coverage_rate; capacity/time fill only, capped at 100%.)
- strict_distribution_adjusted_source_coverage_rate: 28.96 (v1 strict diagnostic retained as a first-class warning signal.)
- period_surface_balance_rate: 81.92 (Surface count balance against v2 period targets; 2000-2026 target is intentionally higher.)
- period_quality_main_balance_rate: 38.88 (Quality main-sheet balance against v2 period targets.)
- region_surface_balance_rate: 12.50 (Surface count balance against v2 regional targets.)
- region_quality_main_balance_rate: 8.55 (Quality main-sheet balance against v2 regional targets.)
- source_visible_surface_rate: 96.16 (Surfaces with IMG01/IMG02/IMG03.)
- research_quality_adjusted_source_coverage_rate_v2: 3.20 (source_pool_period_fill * period_quality_main_balance * region_quality_main_balance * source_visible_rate.)

## Period Targets

- pre_1930: surfaces=1481, main=1433, quality_main=756, target=1700, surface_balance=87.12%, quality_balance=44.47%
- 1930_1970: surfaces=2283, main=2181, quality_main=1017, target=2000, surface_balance=100.00%, quality_balance=50.85%
- 1970_2000: surfaces=2270, main=2237, quality_main=857, target=2200, surface_balance=100.00%, quality_balance=38.95%
- 2000_2026: surfaces=1054, main=1032, quality_main=552, target=2600, surface_balance=40.54%, quality_balance=21.23%
- undated_or_unparsed: surfaces=748, main=699, quality_main=22, target=250, surface_balance=100.00%, quality_balance=8.80%

## Weakest Periods By Quality Main Balance

- undated_or_unparsed: quality_balance=8.80%, target=250
- 2000_2026: quality_balance=21.23%, target=2600
- 1970_2000: quality_balance=38.95%, target=2200
- pre_1930: quality_balance=44.47%, target=1700

## Weakest Regions By Quality Main Balance

- Africa: surfaces=0, quality_main=0, target=750, quality_balance=0.00%
- Cuba: surfaces=8, quality_main=0, target=250, quality_balance=0.00%
- East Asia: surfaces=0, quality_main=0, target=750, quality_balance=0.00%
- Eastern Europe: surfaces=0, quality_main=0, target=650, quality_balance=0.00%
- Eastern Europe / Caucasus: surfaces=0, quality_main=0, target=650, quality_balance=0.00%
- Europe: surfaces=0, quality_main=0, target=550, quality_balance=0.00%
- Global: surfaces=0, quality_main=0, target=400, quality_balance=0.00%
- Global / web / transnational: surfaces=0, quality_main=0, target=400, quality_balance=0.00%
- Latin America and the Caribbean: surfaces=0, quality_main=0, target=850, quality_balance=0.00%
- Middle East and North Africa: surfaces=0, quality_main=0, target=750, quality_balance=0.00%

## Interpretation

- `source_pool_period_fill_rate` can reach 100% while the archive is still structurally weak.
- `research_quality_adjusted_source_coverage_rate_v2` should be treated as the stricter release-facing source coverage diagnostic.
- v2 gives the 2000-2026 period a larger target because contemporary graphic design, graphic art, and visual communication are broader and more diverse in the internet period.
