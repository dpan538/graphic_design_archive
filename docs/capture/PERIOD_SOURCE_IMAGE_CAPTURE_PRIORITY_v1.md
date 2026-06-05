# Period Source + Image Capture Priority v1

Date: 2026-06-06

Scope: active capture records grouped by project period bands. This report combines period-level source breadth and visual evidence health for next-capture planning.

## Formula

- `period_source_coverage_rate = weighted_source_points_in_period / target_weighted_source_points_for_period`
- `image_gap_to_launch_target = (95 - weighted_image_coverage_rate) / 95`
- `capture_priority_index = period_weight × (0.55 × source_gap + 0.45 × image_gap)`

Source gap is weighted slightly higher because adding another record from the same source does not solve archive breadth.

## Ranked Periods

- 1930_1970: priority=0.2526, source=3.00%, image=55.26%, active_sources=26, records=528
  Action: Highest priority: add new active sources and prefer IMG03/strong IMG02 records before adding more thin sheets.
- 1970_2000: priority=0.1726, source=4.73%, image=59.85%, active_sources=26, records=291
  Action: Highest priority: add new active sources and prefer IMG03/strong IMG02 records before adding more thin sheets.
- 2000_2026: priority=0.1481, source=34.06%, image=46.49%, active_sources=734, records=985
  Action: Highest priority: add new active sources and prefer IMG03/strong IMG02 records before adding more thin sheets.
- pre_1930: priority=0.0963, source=2.13%, image=73.17%, active_sources=10, records=467
  Action: Hold broad capture; add targeted non-West/local source diversity and dedupe repeated early image evidence.

## Current Table

- 1930_1970: source_points=21.00/700.00, source_gap=97.00%, image_gap=41.83%, IMG03=153, IMG02=267, IMG00=42, IMG04=42
- 1970_2000: source_points=23.65/500.00, source_gap=95.27%, image_gap=37.00%, IMG03=56, IMG02=225, IMG00=1, IMG04=9
- 2000_2026: source_points=170.30/500.00, source_gap=65.94%, image_gap=51.06%, IMG03=23, IMG02=795, IMG00=1, IMG04=166
- pre_1930: source_points=6.40/300.00, source_gap=97.87%, image_gap=22.98%, IMG03=333, IMG02=66, IMG00=15, IMG04=34

## Interpretation

- 1930-1970 remains the highest-priority period because it has the largest period weight, weak source breadth, and weak weighted image coverage.
- 1970-2000 ranks second because its source breadth is still low, even though its visible-image rate is comparatively healthy after the latest DigitalNZ batch.
- 2000-2026 ranks third in the combined index, but it has the weakest weighted image coverage and needs independent/local post-digital sources with stronger image evidence.
- pre_1930 has comparatively strong image coverage and lower period weight; it should receive targeted non-West/local source work, not broad capture.
