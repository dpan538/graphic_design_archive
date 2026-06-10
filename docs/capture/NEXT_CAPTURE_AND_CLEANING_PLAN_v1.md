# Next Capture And Cleaning Plan v1

This plan schedules the next work cycle after the region/geography confidence gate. It does not run capture or mutate archive data.

## Current Read

- The project now has a usable normalization frame, but region/geography certainty is uneven.
- The immediate bottleneck is not raw source discovery alone; it is controlled attribution, historical-context policy, and text-supported surface value.
- The next capture cycle should start after the first cleaning pass so new sources inherit stricter labels.

## Region Surface Snapshot

- Unresolved region: 4693
- Latin America: 925
- United States: 576
- France: 317
- Brazil: 297
- Mexico: 241
- Italy: 145
- United Kingdom: 133
- Australia: 95
- Germany: 90
- India: 74
- South Africa: 57
- China: 53
- Japan: 35
- Russia: 26

## Plan Phases

- capture_after_cleaning: 5
- cleaning_first: 2
- method_lock: 1

## Priorities

- P1: 4
- P0: 2
- P2: 2

## Recommended Sequence

- P0 `region_geo_safe_apply`: 88 high-confidence direct-conflict candidates (88 reviewed patch candidates)
- P0 `historical_split_policy`: Mexico; United States military occupation context (220 reviewed decisions)
- P1 `southeast_asia_modern_contemporary`: Indonesia (381 review hints); Vietnam; Philippines; Thailand; Malaysia; Singapore (220 active sources / 140 surface-ready objects)
- P1 `caucasus_central_asia_repair`: Caucasus (64); Azerbaijan (39); Georgia (38); Armenia; Kazakhstan; Uzbekistan; Kyrgyzstan (180 active sources / 110 surface-ready objects)
- P1 `south_asia_bangladesh_nepal_pakistan`: Bangladesh (22); Pakistan; Nepal; Sri Lanka; India non-canonical regional sources (180 active sources / 110 surface-ready objects)
- P1 `mena_africa_noncanonical`: Egypt; Morocco; Tunisia; Algeria; Lebanon; Palestine; Nigeria; Ghana; Kenya; Ethiopia; Senegal; South Africa (260 active sources / 160 surface-ready objects)
- P2 `latin_america_cleanup_and_growth`: Mexico; Brazil; Argentina; Chile; Colombia; Peru; Cuba; Caribbean design/print cultures (180 active sources / 110 surface-ready objects)
- P2 `classification_deep_research_inputs`: movement/theme/method terms that remain unstable (one evidence packet per disputed method family)

## Operating Rules

- Do not download images during source discovery.
- Do not upgrade IMG01/IMG03 from heuristic, platform, TOS, or LLM signals.
- Count new successful sources only after item/image capture, surface build, archive incorporation, and release-gate metrics.
- Keep IMG04 low, but do not remove text capture pressure; text is required for research-packet value.
- Use sandbox/sample runs before full rebuilds whenever the task does not require rebuilding all surfaces.

## Output File

- `data/next_capture_plan_v1.csv`
