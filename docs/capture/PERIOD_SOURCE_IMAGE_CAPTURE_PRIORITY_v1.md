# Period Source + Image Capture Priority v1

Date: 2026-06-12

Scope: active capture records grouped by project period bands. This report combines period-level source breadth and visual evidence health for next-capture planning.

## Formula

- `period_source_coverage_rate = weighted_source_points_in_period / target_weighted_source_points_for_period`
- `image_gap_to_launch_target = (95 - weighted_image_coverage_rate) / 95`
- `capture_priority_index = period_weight × (0.55 × source_gap + 0.45 × image_gap)`

Source gap is weighted slightly higher because adding another record from the same source does not solve archive breadth.

## Ranked Periods

- 1930_1970: priority=0.1019, source=57.83%, image=82.51%, active_sources=1945, records=2449
  Action: Maintain; fill known region/theme gaps and improve grouping/text enrichment.
- 2000_2026: priority=0.0519, source=83.26%, image=70.65%, active_sources=1964, records=2215
  Action: Maintain; fill known region/theme gaps and improve grouping/text enrichment.
- 1970_2000: priority=0.0249, source=89.33%, image=86.35%, active_sources=2141, records=2406
  Action: Maintain; fill known region/theme gaps and improve grouping/text enrichment.
- pre_1930: priority=0.0204, source=83.53%, image=85.35%, active_sources=1231, records=1691
  Action: Target missing regional source families only; do not let prewar work displace postwar coverage.

## Current Table

- 1930_1970: source_points=404.80/700.00, source_gap=42.17%, image_gap=13.15%, IMG03=2074, IMG02=267, IMG00=42, IMG04=42
- 2000_2026: source_points=416.30/500.00, source_gap=16.74%, image_gap=25.63%, IMG03=1253, IMG02=795, IMG00=1, IMG04=166
- 1970_2000: source_points=446.65/500.00, source_gap=10.67%, image_gap=9.11%, IMG03=2171, IMG02=225, IMG00=1, IMG04=9
- pre_1930: source_points=250.60/300.00, source_gap=16.47%, image_gap=10.16%, IMG03=1557, IMG02=66, IMG00=15, IMG04=34

## Interpretation

- 1930-1970 remains the highest-priority period because it has the largest period weight, weak source breadth, and weak weighted image coverage.
- 1970-2000 ranks second because its source breadth is still low, even though its visible-image rate is comparatively healthy after the latest DigitalNZ batch.
- 2000-2026 ranks third in the combined index, but it has the weakest weighted image coverage and needs independent/local post-digital sources with stronger image evidence.
- pre_1930 has comparatively strong image coverage and lower period weight; it should receive targeted non-West/local source work, not broad capture.
