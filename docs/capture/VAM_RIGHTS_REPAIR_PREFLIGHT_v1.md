# V&A Rights Repair Preflight v1

This local preflight checks V&A repair candidates against already captured CSV records and local V&A object-detail JSON. It does not call V&A APIs, download images, mutate records, or upgrade IMG01/IMG03.

## Result

- V&A candidate rows: 44
- object raw records found: 44
- automatic upgrades allowed: 0
- candidate weighted gap points: 30.25

## Repair Families

- img02_open_rights_review: 25
- img04_text_state_review: 17
- img04_visual_record_search: 2

## Local Image States

- IMG02: 25
- IMG04: 19

## Object Image Resolution

- low: 37
- high: 7

## Object Image Signals

- object_image_copyright_metadata_present: 25
- object_image_metadata_without_open_rights: 19

## Rights Signals

- blocked_by_object_image_copyright_metadata: 25
- no_source_visible_image_in_public_record: 19

## Upgrade Recommendations

- no_upgrade: 25 (11.25 weighted points)
- source_visible_repair_needed: 19 (19.00 weighted points)

## Interpretation

- V&A object detail metadata improves source-visible triage, but it does not provide bulk verified-open image evidence in this candidate set.
- Rows with copyright metadata stay IMG02/IMG04 unless a later item page exposes explicit open/public-domain evidence.
- Rows with image metadata but no open-rights statement may be useful source-hosted records, but they are not IMG03 repair candidates.
- The compound IMG04 rows need member-level visual search rather than a source-family rights upgrade.

## Output Files

- `data/vam_rights_repair_preflight_v1.csv`
- `data/vam_rights_repair_summary_v1.csv`
