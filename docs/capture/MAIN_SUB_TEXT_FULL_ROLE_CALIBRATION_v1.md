# Main/Sub/Text Full Role Calibration v1

Scope: non-mutating calibration of the 500-row full-role sample.

This pass does not apply overrides, rebuild payloads, download images, or change rights/image states.

## Summary

- Calibration rows: 500.
- Preview-only sandbox candidates: 135.
- `accepted_for_method`: 212.
- `accepted_for_preview`: 135.
- `revise_rule`: 108.
- `hold_for_manual`: 45.

## Calibrated Actions

- `manual_review`: 188.
- `downgrade_to_card_candidate`: 126.
- `keep_main_anchor`: 88.
- `downgrade_to_sub_candidate`: 53.
- `packet_anchor_review`: 29.
- `keep_main_add_text`: 15.
- `convert_to_text_or_appendix`: 1.

## Preview Candidate Roles

- `card_context`: 126.
- `sub_under_packet`: 8.
- `text_or_appendix`: 1.

## Source-Family Bias

- Wikimedia Commons: 430.
- DigitalNZ: 10.
- Wellcome Collection: 8.
- Te Papa: 7.
- Internet Archive: 7.
- Another Graphic: 4.
- Georgia State CONTENTdm: 4.
- Gallica / BnF APIs: 3.
- V&A Collections API: 3.
- Library of Congress: 2.
- Barjeel Art Foundation: 2.
- Indian Memory Project: 2.
- Malaysia Design Archive: 2.
- University of Miami Libraries Digital Collections / CONTENTdm: 2.
- Auckland Libraries Heritage Collections / CONTENTdm: 2.

## Interpretation

- The calibration confirms the direction of card treatment for stamp/philatelic and context/photo evidence.
- Keep-main and keep-main-add-text actions are accepted as method signals only, not as release approval.
- Packet-anchor review remains a relation-design task and should not be converted into overrides before parent/child rules are defined.
- The sample remains Commons-heavy because the underlying candidate archive is Commons-heavy; this must remain visible in later validation.

## Next Permitted Action

Use `data/prefreeze_main_sub_text_full_role_sandbox_candidates_v1.csv` only for a later sandbox preview. Do not apply it to the official payload.
