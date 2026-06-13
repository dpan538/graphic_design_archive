# GSU CONTENTdm Rights Repair Preflight v1

This local preflight checks GSU CONTENTdm IMG02 candidates against already captured CSV records and local raw CONTENTdm JSON. It does not call CONTENTdm, download images, mutate records, or upgrade IMG01/IMG03.

## Result

- GSU candidate rows: 85
- local records found: 85
- raw records found: 85
- automatic upgrades allowed: 0
- candidate weighted gap points: 38.25

## Local Image States

- IMG02: 85

## Raw Rights Signals

- raw_blocking_or_permission_rights_signal: 76
- raw_rights_present_unclassified: 8
- raw_open_rights_signal: 1

## Rights Signals

- blocked_by_raw_copyright_or_permission_signal: 76
- raw_rights_present_but_unclassified: 8
- raw_open_rights_signal_needs_record_rebuild_review: 1

## Upgrade Recommendations

- no_upgrade: 84 (37.80 weighted points)
- review_rebuild_alignment_no_automatic_upgrade: 1 (0.45 weighted points)

## Interpretation

- GSU is not a broad verified-open repair route under the current evidence. Most raw records carry copyright, permission, InC, or educational-use signals.
- One local raw record carries a CC0 URI. It is still not automatically upgraded; it should be manually checked and then rebuilt so the public record preserves the item-level rights evidence.
- The existing GSU capture path appears to overwrite the source rights statement with image-state basis text in the record CSV. A future capture-script patch should preserve both local rights text and image-display basis separately.
- GSU remains useful for regional/local print-culture coverage, but rights repair should be selective rather than counted as a bulk IMG03 gain.

## Output Files

- `data/gsu_rights_repair_preflight_v1.csv`
- `data/gsu_rights_repair_summary_v1.csv`
