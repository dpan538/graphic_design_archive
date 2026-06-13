# LOC Manual IMG03 Apply Postcheck v1

This audit verifies the capture-record state after the controlled LOC manual IMG03 apply pass. It does not rebuild public surfaces or frontend payloads.

## Summary

- checked rows: 20
- pass rows: 20
- fail rows: 0
- images downloaded: 0
- public surfaces rebuilt: false

## Contract Checked

- target capture row exists
- `image_presence_code == IMG03`
- `image_url_detected` matches the LOC source-hosted image URL
- `source_rights_text` carries the LOC item rights/advisory text
- `rights_basis` identifies item-level LOC metadata
- `iiif_or_viewer_available` points back to the LOC item/source record
- `local_copy_permitted == false`
- `image_frame_behavior == open_image_frame`

## Boundary

- No image binaries were downloaded.
- No raw LOC payloads were saved.
- No public surfaces or frontend data were rebuilt.
- Public release metrics remain unchanged until a later rebuild/audit pass.

## Output Files

- `data/loc_manual_img03_apply_postcheck_v1.csv`
- `data/loc_manual_img03_apply_postcheck_summary_v1.csv`
