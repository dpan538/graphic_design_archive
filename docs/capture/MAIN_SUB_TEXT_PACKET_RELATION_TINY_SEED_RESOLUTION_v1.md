# Main/Sub/Text Packet Relation Tiny Seed Resolution v1

Scope: non-mutating manual-resolution audit for the six non-Commons tiny sandbox seeds.

This pass does not rebuild payloads, apply overrides, download images, or change rights/image states.

## Summary

- scope: non_mutating_tiny_seed_resolution (No rebuild, role override, payload write, image download, or rights/image-state change.)
- tiny_seed_rows: 6 (Seed clusters reviewed.)
- seed_role_detail_rows: 44 (Role rows inside seed clusters.)
- sandbox_ready_rows: 0 (Rows that could enter tiny sandbox after manual sign-off.)
- resolution_status:hold_macro_anchor_only_series: 1 (Seed resolution status distribution.)
- resolution_status:needs_anchor_selection_review: 1 (Seed resolution status distribution.)
- resolution_status:hold_profile_directory_not_packet: 1 (Seed resolution status distribution.)
- resolution_status:needs_region_split_before_tiny_sandbox: 1 (Seed resolution status distribution.)
- resolution_status:hold_reference_publication_drift: 1 (Seed resolution status distribution.)
- resolution_status:needs_member_evidence_review: 1 (Seed resolution status distribution.)
- record_kind:poster_or_campaign_item: 12 (Record-kind hints inside seed clusters.)
- record_kind:issue_or_serial: 12 (Record-kind hints inside seed clusters.)
- record_kind:profile_or_interview: 8 (Record-kind hints inside seed clusters.)
- record_kind:event_or_exhibition: 7 (Record-kind hints inside seed clusters.)
- record_kind:book_or_software: 5 (Record-kind hints inside seed clusters.)

## Seed Decisions

- Global / transnational|Midcentury modern graphic communication|Internet Archive|2015-2019: status=hold_macro_anchor_only_series; reason=Cluster has macro/global region and eligible anchors but no eligible member/sub rows.; next=Do not sandbox; resolve region and relation shape first.
- United States|New Deal and civic poster programs|Library of Congress|1935-1939: status=needs_anchor_selection_review; reason=Cluster has eligible member/sub rows but no blocker-free anchor.; next=Create an anchor-selection review; do not auto-promote an anchor.
- Global / transnational|Modern typography and layout|Another Graphic|2025-2029: status=hold_profile_directory_not_packet; reason=Rows look like designer/studio profile pages, not a proven work/project packet.; next=Keep out of sandbox; use as card/profile support or wait for project-level records.
- Global / transnational|Midcentury modern graphic communication|Internet Archive|2010-2014: status=needs_region_split_before_tiny_sandbox; reason=Cluster has potentially useful anchor/member shape but region scope is macro/global.; next=Run a region-scope review before any role override.
- Global / transnational|Midcentury modern graphic communication|Internet Archive|2020-2024: status=hold_reference_publication_drift; reason=Seed mixes reference/software/web-design books with archive issues, creating design-object drift risk.; next=Remove from tiny sandbox candidate list until cluster is split by object type.
- Aotearoa New Zealand|World War and public-information graphics|Te Papa|1940-1944: status=needs_member_evidence_review; reason=Cluster has an anchor but members are blocked by weak design-object evidence.; next=Review member evidence before any tiny sandbox.

## Method Note

- A seed is not sandbox-ready just because it has eligible rows.
- Macro/global clusters need region-scope resolution before packet role changes.
- Profile, interview, software/book, and support/reference records should not become packet members without explicit design-object evidence.
- Anchor/member repair remains a manual review action, not an automatic upgrade.

## Safety

- No rights, source authority, authorship, or IMG01/IMG03 state changes were made.
- No source-family or seed signal may override macro/unresolved region review.
- No image files were downloaded.
