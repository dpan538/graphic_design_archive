# Prefreeze Packet Role Review v1

Scope: review queues and conservative draft overrides derived from the packetization audit.

This pass is advisory. It does not mutate the official payload, does not download images, and does not change rights or image states.

## Summary

- packets_scanned: 2259 (Packet candidates scanned.)
- surface_recommendations_scanned: 16175 (Surface recommendations scanned.)
- review_queue_rows: 9725 (Rows in packet role review queue.)
- draft_override_rows: 2452 (Conservative draft override rows; not applied.)
- packet_lane:manual_packet_or_card_review: 1253 (Packet-level lane distribution.)
- packet_lane:sample_before_override: 632 (Packet-level lane distribution.)
- packet_lane:conservative_draft_override: 307 (Packet-level lane distribution.)
- packet_lane:packet_reference_only: 67 (Packet-level lane distribution.)
- review_lane:manual_packet_or_card_review: 5669 (Surface-level review lane distribution.)
- review_lane:conservative_draft_override: 2458 (Surface-level review lane distribution.)
- review_lane:sample_before_override: 1598 (Surface-level review lane distribution.)
- decision:review_only: 7267 (Surface-level review decision distribution.)
- decision:draft_subsheet_demote: 2142 (Surface-level review decision distribution.)
- decision:keep_main_anchor_candidate: 161 (Surface-level review decision distribution.)
- decision:keep_card_support: 103 (Surface-level review decision distribution.)
- decision:draft_card_demote: 46 (Surface-level review decision distribution.)
- decision:anchor_manual_review: 6 (Surface-level review decision distribution.)
- draft_override_role:support_packet_appendix_text: 2142 (Draft override role distribution.)
- draft_override_role:main_sheet: 161 (Draft override role distribution.)
- draft_override_role:card: 149 (Draft override role distribution.)

## Review Lanes

- manual_packet_or_card_review: 5669
- conservative_draft_override: 2458
- sample_before_override: 1598

## Decisions

- review_only: 7267
- draft_subsheet_demote: 2142
- keep_main_anchor_candidate: 161
- keep_card_support: 103
- draft_card_demote: 46
- anchor_manual_review: 6

## Guardrails

- Draft overrides are not wired into rebuild scripts.
- `source_file` is intentionally blank in the draft override file; application requires a later audited join.
- Manual packet/card review rows are excluded from conservative override application.
- Weak or broad packets remain review evidence only.

## Next Use

- Sample the conservative draft override rows by source family and period before any applied override layer.
- Add source-file joins only after sample review confirms the packet logic.
- Use manual lanes for editorial packet planning, not automatic rebuild changes.
