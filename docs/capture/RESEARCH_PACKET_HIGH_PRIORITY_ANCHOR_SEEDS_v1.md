# Research Packet High-Priority Anchor Seeds v1

Scope: non-mutating seed plan for high-priority anchor review.

This pass separates high-priority anchor candidates into manual review
lanes. It does not apply packet roles or rebuild any payload.

## Summary

- scope: non_mutating_high_priority_anchor_seed_plan (No rebuild, role override, image download, rights/image-state change, or frontend mirror write.)
- high_priority_seed_rows: 42 (High-priority anchor-selection clusters.)
- candidate_rows: 210 (Candidate rows copied into the seed review packet.)
- sandbox_allowed_after_review: 16 (Clusters that may enter sandbox only after manual anchor confirmation.)
- seed_lane:anchor_confirmation_seed: 11 (High-priority seed lane distribution.)
- seed_lane:anchor_then_cover_seed: 12 (High-priority seed lane distribution.)
- seed_lane:card_pressure_anchor_review: 7 (High-priority seed lane distribution.)
- seed_lane:cover_editorial_seed_ready: 4 (High-priority seed lane distribution.)
- seed_lane:graphic_object_scope_review: 4 (High-priority seed lane distribution.)
- seed_lane:manual_hold: 4 (High-priority seed lane distribution.)
- source_family:Another Graphic: 1 (High-priority seed source-family distribution.)
- source_family:Georgia State CONTENTdm: 1 (High-priority seed source-family distribution.)
- source_family:Library of Congress: 1 (High-priority seed source-family distribution.)
- source_family:Malaysia Design Archive: 1 (High-priority seed source-family distribution.)
- source_family:NAIDOC Poster Gallery: 2 (High-priority seed source-family distribution.)
- source_family:Te Papa: 2 (High-priority seed source-family distribution.)
- source_family:Wikimedia Commons: 34 (High-priority seed source-family distribution.)

## First Seed Rows

- United States|New Deal and civic poster programs|Library of Congress|1935-1939: lane=cover_editorial_seed_ready; top=SURF-MC1930R017; subs=8; cards=0; sandbox_after_review=true
- Poland|Modern typography and layout|Wikimedia Commons|1935-1939: lane=cover_editorial_seed_ready; top=SURF-CCE2026R00403; subs=8; cards=2; sandbox_after_review=true
- Aotearoa New Zealand|World War and public-information graphics|Te Papa|1980-1984: lane=cover_editorial_seed_ready; top=SURF-GAPIT2026R025; subs=5; cards=0; sandbox_after_review=true
- Aotearoa New Zealand|Postwar exhibition and cultural posters|Te Papa|1985-1989: lane=cover_editorial_seed_ready; top=SURF-LPC2026R018; subs=8; cards=0; sandbox_after_review=true
- Argentina|Modern typography and layout|Wikimedia Commons|1960-1964: lane=anchor_then_cover_seed; top=SURF-CCE2026R00645; subs=8; cards=10; sandbox_after_review=true
- Aotearoa New Zealand|Modern typography and layout|Wikimedia Commons|1920-1924: lane=anchor_then_cover_seed; top=SURF-CAW2026R01526; subs=12; cards=9; sandbox_after_review=true
- Aotearoa New Zealand|Travel and transport poster culture|Wikimedia Commons|1925-1929: lane=anchor_then_cover_seed; top=SURF-CCT2026R03356; subs=8; cards=0; sandbox_after_review=true
- India|Modern typography and layout|Wikimedia Commons|1960-1964: lane=anchor_then_cover_seed; top=SURF-CAW2026R02612; subs=9; cards=1; sandbox_after_review=true
- Argentina|Modern typography and layout|Wikimedia Commons|1945-1949: lane=anchor_then_cover_seed; top=SURF-CGS2026R0185; subs=11; cards=0; sandbox_after_review=true
- Aotearoa New Zealand|Travel and transport poster culture|Wikimedia Commons|1935-1939: lane=anchor_then_cover_seed; top=SURF-CCT2026R03379; subs=7; cards=0; sandbox_after_review=true
- Nigeria|Modern typography and layout|Wikimedia Commons|1945-1949: lane=anchor_then_cover_seed; top=SURF-CAW2026R02234; subs=21; cards=3; sandbox_after_review=true
- North Macedonia|Modern typography and layout|Wikimedia Commons|1920-1924: lane=anchor_then_cover_seed; top=SURF-CAW2026R01502; subs=7; cards=0; sandbox_after_review=true
- Singapore|Modern typography and layout|Wikimedia Commons|2020-2024: lane=anchor_then_cover_seed; top=SURF-CAW2026R04817; subs=8; cards=0; sandbox_after_review=true
- India|Modern typography and layout|Wikimedia Commons|1955-1959: lane=anchor_then_cover_seed; top=SURF-CCT2026R03753; subs=8; cards=9; sandbox_after_review=true
- Global / transnational|Modern typography and layout|Another Graphic|2025-2029: lane=anchor_then_cover_seed; top=SURF-ERS1970R003; subs=7; cards=0; sandbox_after_review=true
- Azerbaijan|Modern typography and layout|Wikimedia Commons|1935-1939: lane=anchor_then_cover_seed; top=SURF-CCT2026R01419; subs=17; cards=0; sandbox_after_review=true
- Brazil|Modern typography and layout|Wikimedia Commons|1935-1939: lane=anchor_confirmation_seed; top=SURF-CGS2026R0440; subs=4; cards=5; sandbox_after_review=false
- Peru|Modern typography and layout|Wikimedia Commons|1925-1929: lane=anchor_confirmation_seed; top=SURF-CRB2026V2R0428; subs=3; cards=8; sandbox_after_review=false
- Nigeria|Modern typography and layout|Wikimedia Commons|1950-1954: lane=anchor_confirmation_seed; top=SURF-CAW2026R02431; subs=4; cards=6; sandbox_after_review=false
- Argentina|Modern typography and layout|Wikimedia Commons|1970-1974: lane=anchor_confirmation_seed; top=SURF-CGS2026R0242; subs=3; cards=5; sandbox_after_review=false

## Method Commitments

- `sandbox_allowed_after_review` still requires manual anchor confirmation.
- Card pressure blocks immediate cover/editorial seeding.
- Strong-packet and sub-rich candidates are separated because they need different review artifacts.
- Candidate ordering is triage only, not role assignment.

## Safety

- No image files were downloaded.
- No rights/source authority/image-state upgrades were made.
- No packet role was applied by this audit.
