# AIC Rights Repair Preflight v1

This local preflight checks Art Institute of Chicago repair candidates against already captured CSV/JSON metadata. It does not call AIC APIs, download images, mutate records, or upgrade IMG01/IMG03.

## Result

- AIC candidate rows: 36
- local records found: 36
- raw records found: 27
- automatic upgrades allowed: 0
- candidate weighted gap points: 36.00

## Repair Families

- img00_source_visible_repair: 35
- img04_text_state_review: 1

## Local Image States

- IMG00: 35
- IMG03: 1

## Raw Rights Signals

- raw_image_id_non_public_domain: 26
- raw_record_missing: 9
- raw_no_image_identifier: 1

## Rights Signals

- image_identifier_not_public_domain: 26
- no_public_domain_image_evidence: 10

## Upgrade Recommendations

- no_upgrade: 36 (36.00 weighted points)

## Interpretation

- AIC is not an immediate verified-open repair family in this candidate set. The local raw search metadata marks most image-bearing candidates as `is_public_domain=false`.
- These rows may still be valuable source records, but publication-grade open image display requires item-level public-domain evidence, not merely an AIC image identifier or IIIF URL.
- Future AIC work should use item API probes to confirm whether any source records changed rights status, then rebuild only rows with explicit public-domain evidence.

## Output Files

- `data/aic_rights_repair_preflight_v1.csv`
- `data/aic_rights_repair_summary_v1.csv`
