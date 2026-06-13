# Capture Rights Rule Hardening v1

This audit records the local rule hardening applied before the next large source tranche. It does not fetch records, download images, mutate surfaces, or upgrade IMG01/IMG03.

## Summary

- checks: 10
- failures: 0
- restricted CC BY-NC/BY-ND variants: blocked
- explicit CC BY, CC BY-SA, CC0, and PDM signals: still accepted as publication-grade open candidates
- GSU local rights statements: preserved separately from image-display basis fields

## Files Hardened

- `scripts/run_midcentury_expansion_capture_1931_1970.py`
- `scripts/run_gsu_contentdm_image_ready_1830_1970.py`
- `scripts/harvest_gsu_contentdm_raw_records.py`

## Boundary

- This pass changes future capture behavior only.
- It does not reclassify existing records, rebuild surfaces, or claim any new rights upgrades.
- Existing Wellcome/IA/GSU rows that may be affected remain part of the repair/rebuild queue.

## Output

- `data/capture_rights_rule_hardening_v1.csv`
