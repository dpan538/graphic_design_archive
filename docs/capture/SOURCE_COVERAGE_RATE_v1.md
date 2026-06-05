# Source Coverage Rate v1

Date: 2026-06-06

Scope: active captured sources, not candidate/prospect sources. This metric measures source breadth and distribution; it is separate from image coverage.

## Formula

- `source_pool_rate = weighted_active_source_points / weighted_source_target`
- `region_weighted_balance_rate = weighted average of per-region active-source coverage`
- `time_weighted_balance_rate = weighted average of active-source coverage by period band`
- `source_coverage_rate_v1 = source_pool_rate × time_weighted_balance_rate`
- `strict_distribution_adjusted_source_coverage_rate = source_pool_rate × region_weighted_balance_rate × time_weighted_balance_rate`

The main rate uses region-weighted source points first, then applies time coverage. The stricter diagnostic additionally penalizes uneven regional distribution. The current release source target is at least 2000 sources, with an 80% minimum source-coverage gate before final release.

## Current Result

- active_source_count: 813 (Distinct source_name values with at least one captured record.)
- candidate_source_count: 298 (Candidate/prospect sources in source_prospect_registry_v2; not counted as active coverage.)
- pre_surface_source_registry_count: 3500 (Official source sites verified as reachable, but not counted as active source coverage until item-level image-bearing surfaces are built.)
- weighted_active_source_points: 247.95 (Sum of active source region weights. Non-West/local regions carry higher weights.)
- weighted_source_target: 2000.00 (Final release source target requested as at least 2000 sources, expressed as weighted source points.)
- minimum_release_source_coverage_rate: 80.00 (Release gate threshold for source coverage before publication readiness.)
- release_source_coverage_gate_passed: false (True only when source_pool_rate reaches the configured final release coverage threshold.)
- source_pool_rate: 12.40 (weighted_active_source_points / weighted_source_target.)
- region_weighted_balance_rate: 5.10 (Weighted average of per-region active-source coverage against regional source targets.)
- time_weighted_balance_rate: 28.10 (Weighted average of active-source coverage across period bands.)
- source_coverage_rate_v1: 3.48 (source_pool_rate * time_weighted_balance_rate. The source pool itself is already region-weighted.)
- strict_distribution_adjusted_source_coverage_rate: 0.18 (source_pool_rate * region_weighted_balance_rate * time_weighted_balance_rate; diagnostic only.)

## Weakest Regions

- Eastern Europe / Caucasus: active=0, candidate=2, target≈101, balance=0.00%
- Latin America / Transregional: active=0, candidate=1, target≈101, balance=0.00%
- Latin America and the Caribbean: active=0, candidate=3, target≈101, balance=0.00%
- North America / Global digital: active=0, candidate=1, target≈101, balance=0.00%
- Europe: active=1, candidate=2, target≈101, balance=0.99%
- Global: active=1, candidate=3, target≈101, balance=0.99%
- Mainland China: active=1, candidate=1, target≈101, balance=0.99%
- Eastern Europe: active=2, candidate=21, target≈101, balance=1.99%

## Period Balance

- pre_1930: active_sources=10, target≈300, records=467, balance=3.33%
- 1930_1970: active_sources=26, target≈700, records=528, balance=3.71%
- 1970_2000: active_sources=26, target≈500, records=291, balance=5.20%
- 2000_2026: active_sources=734, target≈500, records=985, balance=100.00%

## Weakest Periods

- pre_1930: 3.33%
- 1930_1970: 3.71%
- 1970_2000: 5.20%
- 2000_2026: 100.00%

## Interpretation

- Candidate sources are useful for planning but do not count as coverage until they produce captured records.
- Region weights intentionally favor underrepresented/local regions so the score is not satisfied by Western museum API concentration.
- Period weights currently prioritize postwar coverage: 1930-1970, 1970-2000, and 2000-2026 together carry 85% of the time-balance weight.
- `unmapped_region` is included in diagnostics but carries a low weight; sources should be mapped rather than left as a hidden coverage bucket.
