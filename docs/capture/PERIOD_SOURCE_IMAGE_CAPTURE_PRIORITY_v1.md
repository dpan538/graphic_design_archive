# Period Source + Image Capture Priority v1

Date: 2026-06-13

Scope: active capture records grouped by project period bands. This report combines period-level source breadth and visual evidence health for next-capture planning.

## Formula

- `period_source_coverage_rate = weighted_source_points_in_period / target_weighted_source_points_for_period`
- `image_gap_to_launch_target = (95 - weighted_image_coverage_rate) / 95`
- `capture_priority_index = period_weight × (0.55 × source_gap + 0.45 × image_gap)`

Source gap is weighted slightly higher because adding another record from the same source does not solve archive breadth.

## Ranked Periods

- 1930_1970: priority=0.0280, source=94.03%, image=85.06%, active_sources=3212, records=3716
  Action: Maintain; fill known region/theme gaps and improve grouping/text enrichment.
- 2000_2026: priority=0.0178, source=100.00%, image=79.96%, active_sources=4018, records=4269
  Action: Maintain; fill known region/theme gaps and improve grouping/text enrichment.
- 1970_2000: priority=0.0091, source=100.00%, image=87.34%, active_sources=3029, records=3294
  Action: Maintain; fill known region/theme gaps and improve grouping/text enrichment.
- pre_1930: priority=0.0058, source=100.00%, image=86.89%, active_sources=2066, records=2526
  Action: Target missing regional source families only; do not let prewar work displace postwar coverage.

## Current Table

- 1930_1970: source_points=658.20/700.00, source_gap=5.97%, image_gap=10.46%, IMG03=3341, IMG02=267, IMG00=42, IMG04=42
- 2000_2026: source_points=827.10/500.00, source_gap=0.00%, image_gap=15.83%, IMG03=3307, IMG02=795, IMG00=1, IMG04=166
- 1970_2000: source_points=624.25/500.00, source_gap=0.00%, image_gap=8.06%, IMG03=3059, IMG02=225, IMG00=1, IMG04=9
- pre_1930: source_points=417.60/300.00, source_gap=0.00%, image_gap=8.54%, IMG03=2392, IMG02=66, IMG00=15, IMG04=34

## Interpretation

- 1930-1970 remains the highest-priority period because it has the largest period weight, weak source breadth, and weak weighted image coverage.
- 1970-2000 ranks second because its source breadth is still low, even though its visible-image rate is comparatively healthy after the latest DigitalNZ batch.
- 2000-2026 ranks third in the combined index, but it has the weakest weighted image coverage and needs independent/local post-digital sources with stronger image evidence.
- pre_1930 has comparatively strong image coverage and lower period weight; it should receive targeted non-West/local source work, not broad capture.
