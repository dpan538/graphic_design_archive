# Internet Archive Rights Repair Preflight v1

This local preflight checks Internet Archive IMG02 candidates against already captured CSV metadata. It does not call archive.org, download files/images, mutate records, or upgrade IMG01/IMG03.

## Result

- Internet Archive candidate rows: 75
- local records found: 75
- automatic upgrades allowed: 0
- candidate weighted gap points: 33.75

## Local Image States

- IMG02: 75

## License Signals

- no_explicit_license_url: 74
- blocking_noncommercial_or_noderivatives_url: 1

## Rights Signals

- no_explicit_item_license_url: 74
- blocked_by_noncommercial_or_noderivatives_license: 1

## Upgrade Recommendations

- no_upgrade: 75 (33.75 weighted points)

## Interpretation

- Internet Archive remains useful for reading/source support, but most candidates lack explicit item-level open-license URLs in local metadata.
- One candidate has a non-commercial/no-derivatives Creative Commons URL and is explicitly not an open publication-grade repair.
- Any IA upgrade must preserve explicit item license evidence; IA thumbnails or scans alone are source-visible context, not reusable image evidence.

## Output Files

- `data/internet_archive_rights_repair_preflight_v1.csv`
- `data/internet_archive_rights_repair_summary_v1.csv`
