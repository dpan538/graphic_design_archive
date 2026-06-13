# Library of Congress Rights Repair Preflight v1

This local preflight checks Library of Congress IMG repair candidates against already captured item metadata. It does not call loc.gov, download images, mutate surfaces, or upgrade IMG01/IMG03.

## Result

- LOC candidate rows: 50
- local records found: 50
- automatic upgrades allowed: 0
- candidate weighted gap points: 38.90

## Repair Families

- img01_item_image_and_rights_review: 37
- img04_text_state_review: 13

## Local Image States

- IMG01: 37
- IMG04: 13

## Local Rights Signals

- no_item_rights_advisory_text: 49
- blocking_or_unresolved_rights_terms: 1

## Rights Signals

- thumbnail_only_item_rights_missing: 37
- no_usable_image_in_local_capture: 13

## Upgrade Recommendations

- item_rights_capture_required: 37 (25.90 weighted points)
- source_visible_repair_needed: 13 (13.00 weighted points)

## Interpretation

- LOC is a stronger repair route than Cooper Hewitt/Wellcome because most candidates are thumbnail or no-image records where item-level image and rights data may not yet have been captured.
- The 37 IMG01 rows should not be upgraded automatically; they need loc.gov item JSON/page rights-advisory capture and image derivative evidence.
- The 13 IMG04 rows should be deep-probed before being accepted as true text-only pages, because an earlier search row may have missed item-level images.
- Any later LOC upgrade must store the item page, rights advisory, source URL, and image evidence; source-family reputation alone is not sufficient.

## Output Files

- `data/loc_rights_repair_preflight_v1.csv`
- `data/loc_rights_repair_summary_v1.csv`
