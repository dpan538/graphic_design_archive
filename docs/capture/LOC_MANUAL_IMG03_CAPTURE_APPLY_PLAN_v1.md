# LOC Manual IMG03 Capture Apply Plan v1

This script layer converts the reviewed LOC manual IMG03 queue into a controlled capture-record patch plan. Default execution is dry-run; target capture CSVs are written only with `--apply`.

## Summary

- mode: apply
- planned rows: 20
- ready for apply: 20
- blocked rows: 0
- capture rows written: 20
- public surfaces rebuilt: false

## Planned Capture Fields

- `image_presence_code`: `IMG03`
- `source_rights_text` and `rights_basis`: LOC item-level no-known-restrictions advisory
- `image_url_detected`: LOC source-hosted image URL
- `image_frame_behavior`: `open_image_frame`
- `local_copy_permitted`: `false`
- `iiif_or_viewer_available`: LOC item/source record URL

## Boundary

- No image files are downloaded.
- No raw LOC payloads are saved.
- No heuristic, LLM, TOS, or platform-family signal upgrades are allowed.
- Public metrics change only after a later isolated rebuild/audit pass.

## Execution Note

This run wrote target capture CSVs.

## Output Files

- `data/loc_manual_img03_capture_apply_plan_v1.csv`
- `data/loc_manual_img03_capture_apply_summary_v1.csv`
