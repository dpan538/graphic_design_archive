# Prefreeze Main Anchor Strictness v1

Scope: non-mutating review queue for stricter main/sub/text archival planning.

This pass does not demote surfaces, rebuild the official payload, download images, or change rights/image states.

## Summary

- main_sheets_scanned: 13537 (Candidate main_sheet surfaces scanned.)
- cluster_review_rows: 68 (Region/theme/source/decade main clusters with at least three records.)
- lane:support_or_card_review: 9251 (Main anchor review lane distribution.)
- lane:main_anchor_manual_review: 3809 (Main anchor review lane distribution.)
- lane:keep_main_anchor_candidate: 397 (Main anchor review lane distribution.)
- lane:needs_packet_subsheet_assignment: 42 (Main anchor review lane distribution.)
- lane:needs_editorial_text: 38 (Main anchor review lane distribution.)
- period_lane:1850_1899:keep_main_anchor_candidate: 51 (Main anchor lane by period.)
- period_lane:1850_1899:main_anchor_manual_review: 390 (Main anchor lane by period.)
- period_lane:1850_1899:needs_editorial_text: 1 (Main anchor lane by period.)
- period_lane:1850_1899:needs_packet_subsheet_assignment: 3 (Main anchor lane by period.)
- period_lane:1850_1899:support_or_card_review: 799 (Main anchor lane by period.)
- period_lane:1900_1913:keep_main_anchor_candidate: 4 (Main anchor lane by period.)
- period_lane:1900_1913:main_anchor_manual_review: 304 (Main anchor lane by period.)
- period_lane:1900_1913:needs_editorial_text: 2 (Main anchor lane by period.)
- period_lane:1900_1913:support_or_card_review: 449 (Main anchor lane by period.)
- period_lane:1914_1945:keep_main_anchor_candidate: 108 (Main anchor lane by period.)
- period_lane:1914_1945:main_anchor_manual_review: 1044 (Main anchor lane by period.)
- period_lane:1914_1945:needs_editorial_text: 11 (Main anchor lane by period.)
- period_lane:1914_1945:needs_packet_subsheet_assignment: 6 (Main anchor lane by period.)
- period_lane:1914_1945:support_or_card_review: 2356 (Main anchor lane by period.)
- period_lane:1946_1969:keep_main_anchor_candidate: 50 (Main anchor lane by period.)
- period_lane:1946_1969:main_anchor_manual_review: 469 (Main anchor lane by period.)
- period_lane:1946_1969:needs_editorial_text: 5 (Main anchor lane by period.)

## Interpretation

- `keep_main_anchor_candidate` is not a final approval; it marks records with enough text or explicit relations to sample first.
- These lanes are soft archival markers, not release gates or automatic demotion instructions.
- `needs_packet_subsheet_assignment` is the main归档 backlog: these records may be packet anchors or members, but need relation design before application.
- `needs_editorial_text` means the surface can remain a main anchor if later editorial text justifies it.
- `support_or_card_review` is a high-priority manual review lane for weak visual/context records; some may still become packet anchors after source review.
