# Research Packet Anchor Selection v1

Scope: non-mutating audit for normal-main anchor selection blockers.

This pass writes review queues only. It does not apply normal-main, sub,
appendix, card, or text roles.

## Summary

- scope: non_mutating_research_packet_anchor_selection (No rebuild, role override, image download, rights/image-state change, or frontend mirror write.)
- cluster_review_rows: 1274 (Phase 1 anchor-selection clusters.)
- candidate_review_rows: 2600 (Top surface candidates written for manual anchor review.)
- can_seed_anchor_review: 414 (Clusters with a plausible candidate for manual anchor review, not automatic role application.)
- anchor_review_lane:card_heavy_support_pool: 94 (Anchor review lane distribution.)
- anchor_review_lane:defer_anchor_method_review: 33 (Anchor review lane distribution.)
- anchor_review_lane:manual_anchor_candidate_review: 11 (Anchor review lane distribution.)
- anchor_review_lane:parentage_before_anchor: 8 (Anchor review lane distribution.)
- anchor_review_lane:small_packet_standalone_or_sub_review: 1015 (Anchor review lane distribution.)
- anchor_review_lane:strong_packet_anchor_candidate_review: 5 (Anchor review lane distribution.)
- anchor_review_lane:sub_rich_anchor_candidate_review: 37 (Anchor review lane distribution.)
- anchor_review_lane:weak_graphic_anchor_risk: 71 (Anchor review lane distribution.)
- manual_review_priority:high: 42 (Manual review priority distribution.)
- manual_review_priority:low: 1048 (Manual review priority distribution.)
- manual_review_priority:medium: 184 (Manual review priority distribution.)
- packet_scale:large: 69 (Phase 1 packet scale distribution.)
- packet_scale:medium: 131 (Phase 1 packet scale distribution.)
- packet_scale:single_or_micro: 619 (Phase 1 packet scale distribution.)
- packet_scale:small: 455 (Phase 1 packet scale distribution.)

## High-Priority Seed Candidates

- Poland|Modern typography and layout|Wikimedia Commons|1935-1939: lane=strong_packet_anchor_candidate_review; top=SURF-CCE2026R00403; score=84.45; subs=8; cards=2
- Brazil|Modern typography and layout|Wikimedia Commons|1830-1834: lane=strong_packet_anchor_candidate_review; top=SURF-CAW2026R00032; score=81.15; subs=9; cards=0
- Aotearoa New Zealand|Postwar exhibition and cultural posters|Te Papa|1985-1989: lane=strong_packet_anchor_candidate_review; top=SURF-LPC2026R018; score=78.35; subs=8; cards=0
- United States|New Deal and civic poster programs|Library of Congress|1935-1939: lane=strong_packet_anchor_candidate_review; top=SURF-MC1930R017; score=86.05; subs=8; cards=0
- Aotearoa New Zealand|World War and public-information graphics|Te Papa|1980-1984: lane=strong_packet_anchor_candidate_review; top=SURF-GAPIT2026R025; score=83.8; subs=5; cards=0
- Brazil|Modern typography and layout|Wikimedia Commons|1925-1929: lane=sub_rich_anchor_candidate_review; top=SURF-CGS2026R0415; score=84.45; subs=6; cards=39
- Indonesia|Modern typography and layout|Wikimedia Commons|1980-1984: lane=sub_rich_anchor_candidate_review; top=SURF-CRB2026V3R00226; score=73.85; subs=3; cards=42
- Latin America|Modern typography and layout|Wikimedia Commons|1890-1894: lane=sub_rich_anchor_candidate_review; top=SURF-CAW2026R00594; score=95.75; subs=5; cards=25
- Indonesia|Modern typography and layout|Wikimedia Commons|1985-1989: lane=sub_rich_anchor_candidate_review; top=SURF-CAW2026R03073; score=67.55; subs=5; cards=20
- Nigeria|Modern typography and layout|Wikimedia Commons|1945-1949: lane=sub_rich_anchor_candidate_review; top=SURF-CAW2026R02234; score=69.95; subs=21; cards=3
- Aotearoa New Zealand|Modern typography and layout|Wikimedia Commons|1920-1924: lane=sub_rich_anchor_candidate_review; top=SURF-CAW2026R01526; score=74.65; subs=12; cards=9
- Argentina|Modern typography and layout|Wikimedia Commons|1900-1904: lane=sub_rich_anchor_candidate_review; top=SURF-CGS2026R0075; score=99.05; subs=3; cards=14
- Brazil|Modern typography and layout|Wikimedia Commons|1940-1944: lane=sub_rich_anchor_candidate_review; top=SURF-CCE2026R00431; score=99.05; subs=3; cards=16
- Algeria|Modern typography and layout|Wikimedia Commons|1965-1969: lane=sub_rich_anchor_candidate_review; top=SURF-CCT2026R00242; score=74.25; subs=4; cards=15
- Argentina|Modern typography and layout|Wikimedia Commons|1960-1964: lane=sub_rich_anchor_candidate_review; top=SURF-CCE2026R00645; score=77.55; subs=8; cards=10
- Azerbaijan|Modern typography and layout|Wikimedia Commons|1935-1939: lane=sub_rich_anchor_candidate_review; top=SURF-CCT2026R01419; score=66.65; subs=17; cards=0
- India|Modern typography and layout|Wikimedia Commons|1955-1959: lane=sub_rich_anchor_candidate_review; top=SURF-CCT2026R03753; score=69.55; subs=8; cards=9
- Ukraine|Modern typography and layout|Wikimedia Commons|2005-2009: lane=sub_rich_anchor_candidate_review; top=SURF-CCT2026R01813; score=99.65; subs=6; cards=10
- Latin America|Modern typography and layout|Wikimedia Commons|1950-1954: lane=sub_rich_anchor_candidate_review; top=SURF-CAW2026R02357; score=73.15; subs=15; cards=0
- Peru|Modern typography and layout|Wikimedia Commons|1925-1929: lane=sub_rich_anchor_candidate_review; top=SURF-CRB2026V2R0428; score=95.75; subs=3; cards=8

## Method Commitments

- Candidate ranking is triage only; it does not apply packet roles.
- Card-heavy clusters without sub structure remain support pools.
- A cover main can organize normal mains, but cannot invent a normal-main anchor.
- Same source family, region, or period is not sufficient parentage.
- Weak graphic-object risk flags block automatic anchor promotion.

## Safety

- No image files were downloaded.
- No rights/source authority/image-state upgrades were made.
- No packet role was applied by this audit.
