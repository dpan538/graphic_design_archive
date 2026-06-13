# LOC Manual IMG03 Apply Backup - 2026-06-13

Purpose: backup the three capture-record CSVs before applying the reviewed LOC
manual IMG03 repair queue. This backup supports rollback of the capture-record
mutation layer only; it is not a public payload or frontend rebuild backup.

## Source Files

| Source file | Backup file | Lines | SHA-256 |
| --- | --- | ---: | --- |
| `data/capture_batch_midcentury_1930_1970_records.csv` | `data/backups/loc_manual_img03_apply_2026_06_13/capture_batch_midcentury_1930_1970_records.before_loc_img03_apply.csv` | 140 | `5b2bf1fa5e668a2f4a3022627bf383db0abba1d517c9d6aeb5af8d11e1a7172f` |
| `data/capture_batch_early_region_1830_1930_records.csv` | `data/backups/loc_manual_img03_apply_2026_06_13/capture_batch_early_region_1830_1930_records.before_loc_img03_apply.csv` | 101 | `c0cb822b1abfc96448433aeff33b3819d0ad2bf43bbac00647106153f7b9e0d3` |
| `data/capture_batch_early_region_1830_1880_records.csv` | `data/backups/loc_manual_img03_apply_2026_06_13/capture_batch_early_region_1830_1880_records.before_loc_img03_apply.csv` | 24 | `cb541a4664b3cbb7f9d91e5d910fd8b372aacb353cdafe3e6ca59eda7d251a77` |

## Boundary

- Backup only, before running the controlled LOC apply script.
- No image binaries, thumbnails, screenshots, raw LOC payloads, cookies, or
  browser state are included.
- No generated public surface payloads or frontend mirrors are backed up here.
