# LOC Manual IMG03 Apply Dry Run v1

This dry-run plans a controlled capture-record patch for LOC manual IMG03 candidates. It does not write target CSVs, rebuild surfaces, download images, or change archive metrics.

## Summary

- planned rows: 20
- ready for manual apply: 20
- blocked/review required: 0
- automatic upgrades allowed: 0

## Planned Field Changes

- `image_presence_code`: IMG01 -> IMG03
- `image_frame_behavior`: open_image_frame
- `image_state_confidence`: high
- `source_rights_text` / `rights_basis`: LOC item rights/advisory text
- `image_url_detected`: LOC source-hosted image URL
- `iiif_or_viewer_available`: source record URL should remain visible in a future apply pass

## Boundary

- No capture records were changed in this pass.
- No public payload or frontend data was rebuilt.
- This is not a substitute for the future apply/rebuild audit.

## Output Files

- `data/loc_manual_img03_apply_dry_run_v1.csv`
- `data/loc_manual_img03_apply_dry_run_summary_v1.csv`
