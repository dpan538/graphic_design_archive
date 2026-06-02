# Period Source + Image Capture Priority v1

Date: 2026-06-02

Scope: active capture records grouped by project period bands. This report combines period-level source breadth and visual evidence health for next-capture planning.

## Formula

- `period_source_coverage_rate = weighted_source_points_in_period / target_weighted_source_points_for_period`
- `image_gap_to_launch_target = (95 - weighted_image_coverage_rate) / 95`
- `capture_priority_index = period_weight × (0.55 × source_gap + 0.45 × image_gap)`

Source gap is weighted slightly higher because adding another record from the same source does not solve archive breadth.

## Ranked Periods

- 1930_1970: priority=0.2185, source=20.64%, image=55.36%, active_sources=21, records=523
  Action: Highest priority: add new active sources and prefer IMG03/strong IMG02 records before adding more thin sheets.
- 1970_2000: priority=0.1482, source=21.10%, image=61.43%, active_sources=15, records=279
  Action: Add source breadth first: local/community/university/government adapters before more records from existing sources.
- 2000_2026: priority=0.1344, source=36.80%, image=54.91%, active_sources=20, records=227
  Action: Improve image quality: upgrade IMG02/IMG00/IMG04 through source-specific image adapters and rights review.
- pre_1930: priority=0.0804, source=21.33%, image=73.17%, active_sources=10, records=467
  Action: Hold broad capture; add targeted non-West/local source diversity and dedupe repeated early image evidence.

## Current Table

- 1930_1970: source_points=14.45/70.00, source_gap=79.36%, image_gap=41.73%, IMG03=153, IMG02=263, IMG00=42, IMG04=41
- 1970_2000: source_points=10.55/50.00, source_gap=78.90%, image_gap=35.34%, IMG03=56, IMG02=220, IMG00=1, IMG04=2
- 2000_2026: source_points=18.40/50.00, source_gap=63.20%, image_gap=42.20%, IMG03=23, IMG02=189, IMG00=1, IMG04=14
- pre_1930: source_points=6.40/30.00, source_gap=78.67%, image_gap=22.98%, IMG03=333, IMG02=66, IMG00=15, IMG04=34

## Interpretation

- 1930-1970 remains the highest-priority period because it has the largest period weight, weak source breadth, and weak weighted image coverage.
- 1970-2000 ranks second because its source breadth is still low, even though its visible-image rate is comparatively healthy after the latest DigitalNZ batch.
- 2000-2026 ranks third in the combined index, but it has the weakest weighted image coverage and needs independent/local post-digital sources with stronger image evidence.
- pre_1930 has comparatively strong image coverage and lower period weight; it should receive targeted non-West/local source work, not broad capture.
