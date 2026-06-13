# Wellcome Rights Repair Preflight v1

This local preflight checks Wellcome IMG repair candidates against already captured item metadata. It does not call Wellcome APIs, fetch item pages, download images, mutate surfaces, or upgrade IMG01/IMG03.

## Result

- Wellcome candidate rows: 84
- local records found: 84
- automatic upgrades allowed: 0
- candidate weighted gap points: 39.45

## Local Image States

- IMG02: 82
- IMG03: 2

## License Signals

- no_open_license_text: 82
- blocking_or_noncommercial_terms: 2

## Rights Signals

- source_hosted_viewer_no_open_license_signal: 81
- placeholder_or_no_displayable_image_blocker: 3

## Upgrade Recommendations

- no_upgrade: 81 (36.45 weighted points)
- source_visible_repair_needed: 3 (3.00 weighted points)

## Interpretation

- Wellcome does not provide quick verified-open gain under this local-only preflight. Most rows are source-hosted IIIF/viewer records without open-license text.
- Two legacy local IMG03 rows carry non-commercial license text and placeholder image URLs; they should be treated as repair/downgrade risks, not as verified-open evidence.
- IMG02 rows with IIIF/viewer availability remain source-visible but not verified-open until item-level license evidence is captured.
- IMG00/placeholder rows should be repaired as source-visible records before any rights upgrade is considered.

## Output Files

- `data/wellcome_rights_repair_preflight_v1.csv`
- `data/wellcome_rights_repair_summary_v1.csv`
