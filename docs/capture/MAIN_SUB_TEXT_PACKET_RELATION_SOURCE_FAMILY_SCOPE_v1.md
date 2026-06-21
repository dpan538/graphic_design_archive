# Main/Sub/Text Packet Relation Source-Family Scope v1

Scope: non-mutating source-family validation for extending packet relation rules beyond Commons-heavy clusters.

This pass does not rebuild payloads, apply overrides, download images, or change rights/image states.

## Summary

- scope: non_mutating_non_commons_source_family_scope (No rebuild, no role override, no image download, no rights/image-state change.)
- non_commons_role_rows: 442 (Non-Commons rows in packet relation role queue.)
- non_commons_cluster_rows: 303 (Non-Commons packet relation clusters reviewed.)
- source_family_rows: 27 (Non-Commons source families represented.)
- validation_sample_rows: 260 (Stratified sample for source-family scope review.)
- strict_sandbox_ready_clusters: 0 (Clusters satisfying cautious non-Commons sandbox shape.)
- eligible_non_commons_rows: 25 (Non-Commons rows currently marked eligible for next sandbox review.)
- family_scope_status:needs_more_relation_or_source_depth: 23 (Source-family scope status distribution.)
- family_scope_status:eligible_but_scope_blocked: 4 (Source-family scope status distribution.)
- cluster_scope_status:method_review_only: 297 (Non-Commons cluster scope status distribution.)
- cluster_scope_status:scope_candidate_but_blocked: 6 (Non-Commons cluster scope status distribution.)
- role_source_family:Gallica / BnF APIs: 95 (Non-Commons role queue source-family distribution.)
- role_source_family:Georgia State CONTENTdm: 63 (Non-Commons role queue source-family distribution.)
- role_source_family:Internet Archive: 50 (Non-Commons role queue source-family distribution.)
- role_source_family:Te Papa: 35 (Non-Commons role queue source-family distribution.)
- role_source_family:Wellcome Collection: 32 (Non-Commons role queue source-family distribution.)
- role_source_family:DigitalNZ: 30 (Non-Commons role queue source-family distribution.)
- role_source_family:NAIDOC Poster Gallery: 27 (Non-Commons role queue source-family distribution.)
- role_source_family:Library of Congress: 22 (Non-Commons role queue source-family distribution.)
- role_source_family:Another Graphic: 11 (Non-Commons role queue source-family distribution.)
- role_source_family:Malaysia Design Archive: 9 (Non-Commons role queue source-family distribution.)
- role_source_family:Smithsonian: 8 (Non-Commons role queue source-family distribution.)
- role_source_family:Letterform Archive: 7 (Non-Commons role queue source-family distribution.)
- role_source_family:Asian Film Archive: 7 (Non-Commons role queue source-family distribution.)
- role_source_family:Princeton Figgy: 6 (Non-Commons role queue source-family distribution.)
- role_source_family:Design Reviewed: 6 (Non-Commons role queue source-family distribution.)
- role_source_family:Los Angeles Public Library Tessa / CONTENTdm: 5 (Non-Commons role queue source-family distribution.)
- role_source_family:Art Institute of Chicago API: 5 (Non-Commons role queue source-family distribution.)
- role_source_family:Cleveland Museum Open Access API: 5 (Non-Commons role queue source-family distribution.)
- role_source_family:Indian Memory Project: 4 (Non-Commons role queue source-family distribution.)
- role_source_family:Barjeel Art Foundation: 3 (Non-Commons role queue source-family distribution.)
- role_source_family:African Digital Heritage: 3 (Non-Commons role queue source-family distribution.)
- role_source_family:Desain Grafis Indonesia: 3 (Non-Commons role queue source-family distribution.)
- role_source_family:V&A Collections API: 2 (Non-Commons role queue source-family distribution.)
- role_source_family:Chinese Posters: 1 (Non-Commons role queue source-family distribution.)
- role_source_family:SMU Libraries Digital Collections / CONTENTdm: 1 (Non-Commons role queue source-family distribution.)
- role_source_family:GALA Queer Archive: 1 (Non-Commons role queue source-family distribution.)
- role_source_family:Auckland Libraries Heritage Collections / CONTENTdm: 1 (Non-Commons role queue source-family distribution.)
- family_class:library_archive_or_aggregator: 272 (Non-Commons role queue source-family class distribution.)
- family_class:museum_or_collection_api: 85 (Non-Commons role queue source-family class distribution.)
- family_class:design_or_cultural_institution: 83 (Non-Commons role queue source-family class distribution.)
- family_class:other_non_commons: 2 (Non-Commons role queue source-family class distribution.)

## Core Finding

- Strict non-Commons sandbox-ready clusters: 0.
- Non-Commons clusters with eligible rows but blocked scope: 6.
- Under the current cautious rules, non-Commons coverage is not yet strong enough to run a representative museum/API/design-institution sandbox.

## Why This Matters

- The prior packet sandbox validated a Commons-heavy path only.
- Non-Commons source families have much fewer eligible rows, and many remain `mixed_manual_relation_review`, global/transnational, or anchor-only without member/sub rows.
- A release-bound method should not assume that Commons file-source clusters behave like museum APIs, national libraries, design archives, or cultural institutions.

## Source Families Needing Attention

- Internet Archive: status=eligible_but_scope_blocked; role_rows=50; eligible=13; strict_ready_clusters=0; reason=Has eligible rows but lacks explicit non-macro parent/member cluster shape.
- Te Papa: status=eligible_but_scope_blocked; role_rows=35; eligible=1; strict_ready_clusters=0; reason=Has eligible rows but lacks explicit non-macro parent/member cluster shape.
- Library of Congress: status=eligible_but_scope_blocked; role_rows=22; eligible=4; strict_ready_clusters=0; reason=Has eligible rows but lacks explicit non-macro parent/member cluster shape.
- Another Graphic: status=eligible_but_scope_blocked; role_rows=11; eligible=7; strict_ready_clusters=0; reason=Has eligible rows but lacks explicit non-macro parent/member cluster shape.
- Gallica / BnF APIs: status=needs_more_relation_or_source_depth; role_rows=95; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- Georgia State CONTENTdm: status=needs_more_relation_or_source_depth; role_rows=63; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- Wellcome Collection: status=needs_more_relation_or_source_depth; role_rows=32; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- DigitalNZ: status=needs_more_relation_or_source_depth; role_rows=30; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- NAIDOC Poster Gallery: status=needs_more_relation_or_source_depth; role_rows=27; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- Malaysia Design Archive: status=needs_more_relation_or_source_depth; role_rows=9; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- Smithsonian: status=needs_more_relation_or_source_depth; role_rows=8; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- Asian Film Archive: status=needs_more_relation_or_source_depth; role_rows=7; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- Letterform Archive: status=needs_more_relation_or_source_depth; role_rows=7; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- Design Reviewed: status=needs_more_relation_or_source_depth; role_rows=6; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- Princeton Figgy: status=needs_more_relation_or_source_depth; role_rows=6; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- Art Institute of Chicago API: status=needs_more_relation_or_source_depth; role_rows=5; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- Cleveland Museum Open Access API: status=needs_more_relation_or_source_depth; role_rows=5; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- Los Angeles Public Library Tessa / CONTENTdm: status=needs_more_relation_or_source_depth; role_rows=5; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- Indian Memory Project: status=needs_more_relation_or_source_depth; role_rows=4; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- African Digital Heritage: status=needs_more_relation_or_source_depth; role_rows=3; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- Barjeel Art Foundation: status=needs_more_relation_or_source_depth; role_rows=3; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- Desain Grafis Indonesia: status=needs_more_relation_or_source_depth; role_rows=3; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- V&A Collections API: status=needs_more_relation_or_source_depth; role_rows=2; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.
- Auckland Libraries Heritage Collections / CONTENTdm: status=needs_more_relation_or_source_depth; role_rows=1; eligible=0; strict_ready_clusters=0; reason=Rows remain method-review only or support-only under current packet rules.

## Next Safe Action

- Do not run a non-Commons sandbox from this pass unless strict-ready clusters appear after source-family-specific rule tuning.
- First tune relation rules for recurring source families such as Gallica / BnF APIs, DigitalNZ, Te Papa, Wellcome Collection, Library of Congress, NAIDOC Poster Gallery, V&A Collections API, and design archives.
- Add source-family-specific parentage heuristics only as audit signals, not automatic role upgrades.

## Safety

- No image files were downloaded.
- No rights, source authority, authorship, or IMG01/IMG03 upgrades were made.
- Source-family scope is an internal method-validation signal only.
