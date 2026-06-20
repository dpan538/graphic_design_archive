# Main/Sub/Text Manual Calibration Queue v1

Scope: deterministic 80-row queue for calibrating the initial method review before any sandbox override.

This queue does not apply overrides, rebuild surfaces, download images, or change rights/image states.

## Queue Size

- Calibration rows: 80.
- This is 25% of the 320-row validation packet.

## Role Spread

- `card_context`: 26.
- `sub_under_packet`: 17.
- `manual_hold`: 15.
- `main_needs_text`: 14.
- `keep_main`: 7.
- `exclude_or_deprioritize`: 1.

## Calibration Groups

- `large_cluster_parentage_review`: 8.
- `stamp_or_commemorative_manual`: 8.
- `transnational_geography_manual`: 8.
- `main_sensitive:anchor_if_editorial_text_added:main_needs_text`: 7.
- `main_sensitive:packet_anchor_or_member_review:sub_under_packet`: 7.
- `main_sensitive:soft_anchor_review:main_needs_text`: 7.
- `main_sensitive:soft_anchor_review:manual_hold`: 7.
- `main_sensitive:strong_soft_anchor:keep_main`: 7.
- `support:card_context`: 7.
- `unresolved_region_or_theme_manual`: 7.
- `weak_commons_only_manual`: 4.
- `main_sensitive:soft_anchor_review:sub_under_packet`: 2.
- `natural_history_geology_false_positive`: 1.

## How To Use

- Review each row's recommended role, blocker class, relation type, and text need.
- Mark whether the role is accepted, revised, or rejected.
- Track recurring failure patterns rather than treating each row as isolated.
- Do not create a sandbox override until the queue shows stable agreement.
