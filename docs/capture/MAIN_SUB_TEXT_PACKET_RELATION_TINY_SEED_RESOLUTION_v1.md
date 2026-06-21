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
- resolution_status:needs_global_showcase_relation_review: 1 (Seed resolution status distribution.)
- resolution_status:needs_global_scope_review_before_tiny_sandbox: 1 (Seed resolution status distribution.)
- resolution_status:hold_reference_publication_drift: 1 (Seed resolution status distribution.)
- resolution_status:needs_member_evidence_review: 1 (Seed resolution status distribution.)
- record_kind:poster_or_campaign_item: 12 (Record-kind hints inside seed clusters.)
- record_kind:issue_or_serial: 12 (Record-kind hints inside seed clusters.)
- record_kind:showcase_or_project_page: 7 (Record-kind hints inside seed clusters.)
- record_kind:event_or_exhibition: 7 (Record-kind hints inside seed clusters.)
- record_kind:book_or_software: 5 (Record-kind hints inside seed clusters.)
- record_kind:profile_or_interview: 1 (Record-kind hints inside seed clusters.)
- global_scope_policy:global_host_requires_scope_review: 3 (Seed-level global scope policy distribution.)
- global_scope_policy:region_specific_or_not_global: 2 (Seed-level global scope policy distribution.)
- global_scope_policy:global_site_acceptable_with_relation_review: 1 (Seed-level global scope policy distribution.)

## Seed Decisions

- Global / transnational|Midcentury modern graphic communication|Internet Archive|2015-2019: status=hold_macro_anchor_only_series; reason=Cluster has macro/global region and eligible anchors but no eligible member/sub rows.; actual_year_span=2016-2016; global_policy=global_host_requires_scope_review; next=Do not sandbox; resolve scope and relation shape first.
- United States|New Deal and civic poster programs|Library of Congress|1935-1939: status=needs_anchor_selection_review; reason=Cluster has eligible member/sub rows but no blocker-free anchor.; actual_year_span=1936-1938; global_policy=region_specific_or_not_global; next=Create an anchor-selection review; do not auto-promote an anchor.
- Global / transnational|Modern typography and layout|Another Graphic|2025-2029: status=needs_global_showcase_relation_review; reason=Rows look like contemporary showcase/project pages; global scope can be acceptable for this source family, but packet parentage is not yet proven.; actual_year_span=2026-2026; global_policy=global_site_acceptable_with_relation_review; next=Keep as a global-site review seed; do not require country split, but do require relation evidence and anchor selection.
- Global / transnational|Midcentury modern graphic communication|Internet Archive|2010-2014: status=needs_global_scope_review_before_tiny_sandbox; reason=Cluster has potentially useful anchor/member shape but region scope is macro/global.; actual_year_span=2012-2014; global_policy=global_host_requires_scope_review; next=Run a global-scope review before any role override; do not force country assignment if the organization/platform is genuinely transnational.
- Global / transnational|Midcentury modern graphic communication|Internet Archive|2020-2024: status=hold_reference_publication_drift; reason=Seed mixes reference/software/web-design books with archive issues, creating design-object drift risk.; actual_year_span=2020-2024; global_policy=global_host_requires_scope_review; next=Remove from tiny sandbox candidate list until cluster is split by object type.
- Aotearoa New Zealand|World War and public-information graphics|Te Papa|1940-1944: status=needs_member_evidence_review; reason=Cluster has an anchor but members are blocked by weak design-object evidence.; actual_year_span=1940-1944; global_policy=region_specific_or_not_global; next=Review member evidence before any tiny sandbox.

## Method Note

- A seed is not sandbox-ready just because it has eligible rows.
- Global/transnational scope is a valid archive category, not a parser failure or a mandatory country-split queue.
- Macro/global clusters need scope review before packet role changes unless the source family has an explicit global-site policy.
- Contemporary showcase platforms and cross-border organizations can remain global/transnational when the source itself is a cross-border design display context, but they still need anchor/member relation evidence.
- Aggregator or host platforms need scope review because global may mean either real transnational organization or unresolved metadata; do not force country assignment without evidence.
- Profile, interview, software/book, and support/reference records should not become packet members without explicit design-object evidence.
- Five-year buckets such as 2025-2029 are grouping keys only; use actual_year_span for current data coverage.
- Anchor/member repair remains a manual review action, not an automatic upgrade.

## Safety

- No rights, source authority, authorship, or IMG01/IMG03 state changes were made.
- No source-family or seed signal may override macro/unresolved region review.
- No image files were downloaded.
