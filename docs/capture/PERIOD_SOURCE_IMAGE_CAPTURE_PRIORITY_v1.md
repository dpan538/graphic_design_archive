# Period Source + Image Capture Priority v1

Date: 2026-06-06

Scope: active capture records grouped by project period bands. This report combines period-level source breadth and visual evidence health for next-capture planning.

## Formula

- `period_source_coverage_rate = weighted_source_points_in_period / target_weighted_source_points_for_period`
- `image_gap_to_launch_target = (95 - weighted_image_coverage_rate) / 95`
- `capture_priority_index = period_weight × (0.55 × source_gap + 0.45 × image_gap)`

Source gap is weighted slightly higher because adding another record from the same source does not solve archive breadth.

## Ranked Periods

- 1930_1970: priority=0.2067, source=14.11%, image=70.04%, active_sources=415, records=919
  Action: Add source breadth first: local/community/university/government adapters before more records from existing sources.
- 1970_2000: priority=0.1580, source=8.73%, image=67.56%, active_sources=126, records=391
  Action: Add source breadth first: local/community/university/government adapters before more records from existing sources.
- 2000_2026: priority=0.1098, source=50.78%, image=59.45%, active_sources=1152, records=1403
  Action: Improve image quality: upgrade IMG02/IMG00/IMG04 through source-specific image adapters and rights review.
- pre_1930: priority=0.0590, source=39.40%, image=82.35%, active_sources=569, records=1028
  Action: Target missing regional source families only; do not let prewar work displace postwar coverage.

## Current Table

- 1930_1970: source_points=98.80/700.00, source_gap=85.89%, image_gap=26.27%, IMG03=544, IMG02=267, IMG00=42, IMG04=42
- 1970_2000: source_points=43.65/500.00, source_gap=91.27%, image_gap=28.88%, IMG03=156, IMG02=225, IMG00=1, IMG04=9
- 2000_2026: source_points=253.90/500.00, source_gap=49.22%, image_gap=37.42%, IMG03=441, IMG02=795, IMG00=1, IMG04=166
- pre_1930: source_points=118.20/300.00, source_gap=60.60%, image_gap=13.32%, IMG03=894, IMG02=66, IMG00=15, IMG04=34

## Interpretation

- 1930-1970 remains the highest-priority period because it has the largest period weight, weak source breadth, and weak weighted image coverage.
- 1970-2000 ranks second because its source breadth is still low, even though its visible-image rate is comparatively healthy after the latest DigitalNZ batch.
- 2000-2026 ranks third in the combined index, but it has the weakest weighted image coverage and needs independent/local post-digital sources with stronger image evidence.
- pre_1930 has comparatively strong image coverage and lower period weight; it should receive targeted non-West/local source work, not broad capture.
