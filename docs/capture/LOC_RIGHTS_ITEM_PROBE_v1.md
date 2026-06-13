# LOC Rights Item Probe v1

This source-only probe checks P0 Library of Congress repair candidates against loc.gov item JSON metadata. It does not download images, save raw JSON, mutate records, rebuild surfaces, or upgrade IMG01/IMG03.

## Summary

- candidate rows probed: 50
- rows with source-hosted image URL: 20
- manual IMG03 candidate weighted gap points: 14.00
- automatic upgrades allowed: 0

## Recommendation Counts

- retry_later_rate_limited: 29
- manual_img03_candidate_item_rights_visible: 20
- keep_img04_or_text_until_visual_source_found: 1

## Boundary

- `manual_img03_candidate_item_rights_visible` means LOC item metadata exposes both an image URL and open-rights text, but a human/rebuild pass must still decide whether to promote.
- `source_visible_img02_rebuild_candidate` can improve source-visible coverage but is not verified-open.
- `automatic_upgrade_allowed` is false for every row.
- LOC HTTP 429 responses are kept as `retry_later_rate_limited` rather than blocking the run with long in-process backoff.

## Output Files

- `data/loc_rights_item_probe_v1.csv`
- `data/loc_rights_item_probe_summary_v1.csv`
