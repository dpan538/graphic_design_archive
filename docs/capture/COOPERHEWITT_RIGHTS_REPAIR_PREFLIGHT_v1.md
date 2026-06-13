# Cooper Hewitt Rights Repair Preflight v1

This local preflight checks Cooper Hewitt IMG02 repair candidates against already captured item metadata. It does not call GraphQL, fetch item pages, download images, mutate surfaces, or upgrade IMG01/IMG03.

## Result

- Cooper Hewitt candidate rows: 137
- local records found: 137
- automatic upgrades allowed: 0

## Rights Signals

- local_legal_credit_only_no_open_evidence: 74
- blocked_by_local_copyright_or_restriction_signal: 51
- no_item_level_open_rights_evidence: 8
- possible_open_text_requires_item_verification: 4

## Interpretation

- Cooper Hewitt remains a high-value source-visible IMG02 family, but local metadata does not support automatic verified-open promotion.
- Rows with copyright/restriction signals should stay IMG02 unless an item page later exposes explicit open evidence.
- Rows with credit-only or no open-rights evidence also stay IMG02; source-hosted display is not the same as project-local open publication.

## Output Files

- `data/cooperhewitt_rights_repair_preflight_v1.csv`
- `data/cooperhewitt_rights_repair_summary_v1.csv`
