# Region/Geography Auto-Apply Hardening v1

This audit tightens the existing region/geography auto-apply queue before any archive mutation.
It is advisory and dry-run only: `automatic_archive_mutation=false` for every row.

## Result

- input ready rows: 88
- hardened rows requiring sample before mutation: 8
- quarantine/manual rows: 80

## Blocking Flags

- suggested_absent_from_title_source_url: 70
- current_label_present_in_title_source_url: 38
- stamp_issuer_conflicts_with_suggested_label: 6
- other_country_present_in_title_source_url: 3
- new_mexico_subnational_ambiguity: 3

## Advisory Flags

- commons_metadata_sample_required: 84
- pre_1992_sample_required: 73
- missing_year: 2
- multi_country_context: 1

## Suggested Labels

- Brazil: 30 total; 2 hardened; 28 quarantined
- Mexico: 28 total; 2 hardened; 26 quarantined
- Argentina: 17 total; 2 hardened; 15 quarantined
- Egypt: 7 total; 0 hardened; 7 quarantined
- Chile: 3 total; 2 hardened; 1 quarantined
- Germany: 1 total; 0 hardened; 1 quarantined
- South Africa: 1 total; 0 hardened; 1 quarantined
- Turkey: 1 total; 0 hardened; 1 quarantined

## Method Notes

- The previous ready queue is not treated as enough evidence by itself.
- A row remains batch-candidate only when the suggested country appears in title/source/source URL evidence and in place/subject/evidence fields.
- Rows are quarantined when another country or the current label is visible in title/source evidence.
- Historical dispute periods and external contradictions block automated use.
- All surviving rows still require sampling before any future mutation.

## Output Files

- `data/region_geo_auto_apply_hardened_v1.csv`
- `data/region_geo_auto_apply_quarantine_v1.csv`
- `data/region_geo_auto_apply_hardening_summary_v1.csv`
