# LOC Manual IMG03 Rebuild Queue v1

This queue isolates LOC repair candidates where the source-only item probe found both a source-hosted image URL and item-level open/publication rights text. It is advisory only and does not mutate records or upgrade IMG01/IMG03.

## Summary

- candidate rows: 20
- weighted gap points represented: 14.00
- automatic upgrades allowed: 0

## Rebuild Boundary

- Future application must patch the original capture record with the LOC item rights text, image URL, source URL, and review note.
- Surfaces must be rebuilt after the capture-record patch before the source can count as successful archive integration.
- The queue does not contain image binaries or raw JSON payloads.
- Rate-limited LOC rows are not included; they remain in `retry_later_rate_limited` from the item probe.

## Output Files

- `data/loc_manual_img03_rebuild_queue_v1.csv`
- `data/loc_manual_img03_rebuild_summary_v1.csv`
