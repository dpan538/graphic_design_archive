# Period Source + Image Capture Priority v1

Date: 2026-06-06

Scope: active capture records grouped by project period bands. This report combines period-level source breadth and visual evidence health for next-capture planning.

## Formula

- `period_source_coverage_rate = weighted_source_points_in_period / target_weighted_source_points_for_period`
- `image_gap_to_launch_target = (95 - weighted_image_coverage_rate) / 95`
- `capture_priority_index = period_weight × (0.55 × source_gap + 0.45 × image_gap)`

Source gap is weighted slightly higher because adding another record from the same source does not solve archive breadth.

## Ranked Periods

- 1930_1970: priority=0.1100, source=54.00%, image=82.04%, active_sources=1811, records=2315
  Action: Maintain; fill known region/theme gaps and improve grouping/text enrichment.
- 2000_2026: priority=0.0839, source=65.22%, image=64.51%, active_sources=1513, records=1764
  Action: Maintain; fill known region/theme gaps and improve grouping/text enrichment.
- 1970_2000: priority=0.0321, source=84.33%, image=86.11%, active_sources=2016, records=2281
  Action: Maintain; fill known region/theme gaps and improve grouping/text enrichment.
- pre_1930: priority=0.0255, source=77.60%, image=85.09%, active_sources=1142, records=1601
  Action: Target missing regional source families only; do not let prewar work displace postwar coverage.

## Current Table

- 1930_1970: source_points=378.00/700.00, source_gap=46.00%, image_gap=13.64%, IMG03=1931, IMG02=267, IMG00=42, IMG04=42
- 2000_2026: source_points=326.10/500.00, source_gap=34.78%, image_gap=32.09%, IMG03=719, IMG02=795, IMG00=1, IMG04=166
- 1970_2000: source_points=421.65/500.00, source_gap=15.67%, image_gap=9.36%, IMG03=2018, IMG02=225, IMG00=1, IMG04=9
- pre_1930: source_points=232.80/300.00, source_gap=22.40%, image_gap=10.43%, IMG03=1467, IMG02=66, IMG00=15, IMG04=34

## Interpretation

- 1930-1970 remains the highest-priority period because it has the largest period weight, weak source breadth, and weak weighted image coverage.
- 1970-2000 ranks second because its source breadth is still low, even though its visible-image rate is comparatively healthy after the latest DigitalNZ batch.
- 2000-2026 ranks third in the combined index, but it has the weakest weighted image coverage and needs independent/local post-digital sources with stronger image evidence.
- pre_1930 has comparatively strong image coverage and lower period weight; it should receive targeted non-West/local source work, not broad capture.
