# Main/Sub/Text Initial Role Review v1

Scope: first-pass method review of the 320-row validation packet.

This pass does not rebuild surfaces, does not apply role overrides, does not download images, and does not change rights or image states.

## Result

- Rows reviewed: 320.
- Sandbox candidate-pool rows: 11.
- Manual calibration queue rows: 80.
- Sandbox gate: not ready for override because manual calibration and reviewer agreement have not happened yet.

## Recommended Role Distribution

- `card_context`: 120.
- `manual_hold`: 71.
- `main_needs_text`: 57.
- `sub_under_packet`: 43.
- `keep_main`: 28.
- `exclude_or_deprioritize`: 1.

## Review Result Distribution

- `revise`: 177.
- `pass`: 143.

## Confidence Distribution

- `medium`: 243.
- `low`: 60.
- `high`: 17.

## Main Blockers

- `transnational_geography_manual`: 101.
- `unresolved_region_or_theme_manual`: 45.
- `large_cluster_parentage_review`: 20.
- `stamp_or_commemorative_manual`: 16.
- `weak_commons_only_manual`: 16.
- `natural_history_geology_false_positive`: 1.

## Interpretation

- The initial review can identify likely support/card and manual-hold lanes, but it is not a substitute for human method calibration.
- High-confidence automation remains intentionally narrow and is limited to candidate-pool rows, not applied overrides.
- Main retention remains conservative: keep-main and main-needs-text decisions should stay human-confirmed until the validation packet has calibrated review.
- Records with geography, event/photo, stamp, weak Commons-only, large-cluster, or false-positive signals remain manual-first.

## Next Step

Manually calibrate the 80-row queue, including all blocker classes and all main-sensitive lanes. If agreement is near 80% and fail patterns stay below 10%, convert a small subset of the candidate pool into a sandbox override test.
