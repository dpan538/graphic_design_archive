# Main/Sub/Text Packet Relation Sandbox Preview v1

Scope: narrow, non-mutating sandbox preview for explicit packet parent/member relations.

This pass keeps selected anchors as main sheets and previews only blocker-free member/sub candidates as support-packet rows. It does not write generated payload JSON, mutate the official payload, download images, or change rights/image states.

## Summary

- base_override_rows: 2445 (Packet-relation sandbox preview statistic.)
- eligible_explicit_clusters: 83 (Packet-relation sandbox preview statistic.)
- member_rows_considered: 73 (Packet-relation sandbox preview statistic.)
- merged_override_rows: 2518 (Packet-relation sandbox preview statistic.)
- new_preview_overrides: 73 (Packet-relation sandbox preview statistic.)
- preview_applied: 73 (Packet-relation sandbox preview statistic.)
- rejected_examples: 0 (Packet-relation sandbox preview statistic.)
- rejected_rows: 0 (Packet-relation sandbox preview statistic.)
- selected_clusters: 18 (Packet-relation sandbox preview statistic.)
- selected_member_rows: 73 (Packet-relation sandbox preview statistic.)
- selected_region:Aotearoa New Zealand: 1 (Packet-relation sandbox preview statistic.)
- selected_region:Australia / Indigenous: 1 (Packet-relation sandbox preview statistic.)
- selected_region:Azerbaijan: 1 (Packet-relation sandbox preview statistic.)
- selected_region:China / Hong Kong: 1 (Packet-relation sandbox preview statistic.)
- selected_region:Ethiopia: 1 (Packet-relation sandbox preview statistic.)
- selected_region:India: 1 (Packet-relation sandbox preview statistic.)
- selected_region:Indonesia: 1 (Packet-relation sandbox preview statistic.)
- selected_region:Iran: 2 (Packet-relation sandbox preview statistic.)
- selected_region:Korean Peninsula: 1 (Packet-relation sandbox preview statistic.)
- selected_region:Latin America: 1 (Packet-relation sandbox preview statistic.)
- selected_region:Serbia: 1 (Packet-relation sandbox preview statistic.)
- selected_region:Syria: 1 (Packet-relation sandbox preview statistic.)
- selected_region:Uganda: 1 (Packet-relation sandbox preview statistic.)
- selected_region:United Kingdom: 1 (Packet-relation sandbox preview statistic.)
- selected_region:United States: 2 (Packet-relation sandbox preview statistic.)
- selected_region:Uruguay: 1 (Packet-relation sandbox preview statistic.)
- selected_role:packet_member_review: 48 (Packet-relation sandbox preview statistic.)
- selected_role:sub_under_packet_candidate: 25 (Packet-relation sandbox preview statistic.)

## Delta Status

- `preview_disposition_applied`: 73

## Key Metric Deltas

- surfaces: 16175 -> 16175 (delta 0)
- active public sources: 14997 -> 14997 (delta 0)
- main sheets: 13537 -> 13464 (delta -73)
- support packets: 692 -> 765 (delta 73)
- cards: 1944 -> 1944 (delta 0)
- text templates: 94 -> 94 (delta 0)
- object source-visible rate: 98.92 -> 98.92 (delta 0.00)
- object verified-open rate: 95.29 -> 95.29 (delta 0.00)
- object weighted publication-grade rate: 97.26 -> 97.26 (delta 0.00)
- object IMG04 rate: 0.82 -> 0.82 (delta 0.00)

## Interpretation

- This preview tests whether explicit parent/member clusters can move member rows out of main-sheet status without changing source inclusion or rights state.
- Parent anchors are listed in the cluster plan but are not role-overridden by this pass.
- A successful preview means the relation method is technically stable; it does not mean the selected parent choices are final.
- The selected explicit clusters are currently all Wikimedia Commons; this validates a Commons-heavy structure path and must be repeated on museum/API/design-institution sources before generalization.
- Text-page estimates remain planning signals and are not generated here.

## Safety

- No image files were downloaded.
- No rights, source authority, authorship, or IMG01/IMG03 upgrades were made.
- The official payload, frontend mirrors, shards, and release build outputs were not modified.
