# Non-mainstream item/image source-summary geography repair v1

Generated: 2026-06-13
Run mode: dry-run postcheck
Applied mutation: false

## Scope

- Repairs only `data/capture_batch_nonmainstream_item_image_2026_source_summary.csv`.
- Uses country-level `source_place_text` already present in capture records.
- Does not fetch network data, download images, mutate capture records, upgrade image rights, or rebuild public surfaces.

## Hashes

- Before SHA-256: `6cee404a5dabd582d96fe77c35704215d32e26b3cc0e9b7d4a0e188351b0706a`
- After SHA-256: `6cee404a5dabd582d96fe77c35704215d32e26b3cc0e9b7d4a0e188351b0706a`

## Actions

- duplicate_source_ids_in_records: 91
- unchanged: 581

## Main repaired old country buckets


## Main repaired target countries


## Examples

- No repair-ready rows.

## Interpretation

- Current source-summary geography matches the country-level `source_place_text` carried by the capture records.
- The earlier overbroad buckets such as Caribbean and Caucasus are no longer present as repair-needed summary countries.
- Duplicate source IDs are present in the capture-record layer, so this repair keys on source_id plus source_name.
- Rows checked here still remain IMG02 and must pass item/surface review before they count as successful active sources.

## Output files

- `data/nonmainstream_item_image_source_summary_geo_repair_plan_v1.csv`
- `data/nonmainstream_item_image_source_summary_geo_repair_summary_v1.csv`
- `data/backups/nonmainstream_item_image_source_summary_geo_repair_2026_06_13/MANIFEST.md`
