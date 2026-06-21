# Main/Sub/Text Packet Relation Source-Family Tuning v1

Scope: non-mutating tuning audit for non-Commons packet relation evidence.

This pass does not rebuild payloads, apply overrides, download images, or change rights/image states.

## Summary

- scope: non_mutating_source_family_tuning_audit (No rebuild, role override, payload write, image download, or rights/image-state change.)
- source_family_rows: 27 (Source-family tuning matrix rows.)
- cluster_blocker_rows: 303 (Non-Commons clusters with blocking dimensions.)
- rule_candidate_rows: 27 (Audit-only source-family rule signal candidates.)
- tiny_sandbox_seed_rows: 6 (Manual seed rows for a future tiny sandbox after tuning.)
- strict_ready_clusters: 0 (Carried forward from scope v1; this pass does not create ready clusters.)
- tuning_status:improve_design_object_and_cluster_confidence: 15 (Source-family tuning status distribution.)
- tuning_status:define_parentage_signal: 5 (Source-family tuning status distribution.)
- tuning_status:tiny_seed_after_manual_resolution: 4 (Source-family tuning status distribution.)
- tuning_status:manual_source_family_review: 3 (Source-family tuning status distribution.)
- primary_blocker:lane_not_strong: 23 (Dominant source-family blocking dimension.)
- primary_blocker:missing_member_or_sub: 2 (Dominant source-family blocking dimension.)
- primary_blocker:missing_anchor: 1 (Dominant source-family blocking dimension.)
- primary_blocker:no_eligible_rows: 1 (Dominant source-family blocking dimension.)
- resolution_path:improve_relation_evidence_before_sandbox: 255 (Cluster-level manual resolution path distribution.)
- resolution_path:resolve_region_scope_before_packeting: 46 (Cluster-level manual resolution path distribution.)
- resolution_path:identify_blocker_free_anchor_candidate: 1 (Cluster-level manual resolution path distribution.)
- resolution_path:identify_blocker_free_member_or_sub_candidate: 1 (Cluster-level manual resolution path distribution.)
- family_class:design_or_cultural_institution: 13 (Source-family class distribution.)
- family_class:library_archive_or_aggregator: 8 (Source-family class distribution.)
- family_class:museum_or_collection_api: 5 (Source-family class distribution.)
- family_class:other_non_commons: 1 (Source-family class distribution.)

## Core Finding

- This pass intentionally creates no strict-ready clusters.
- Non-Commons packeting needs family-specific relation evidence before any broader sandbox.
- The most useful next step is a small manual tuning cycle on blocked eligible clusters, not a full rebuild.

## Priority Families

- Internet Archive: status=tiny_seed_after_manual_resolution; rows=50; eligible=13; primary_blocker=missing_member_or_sub; signal=scan_or_publication_host_signal; next=review blocked eligible clusters, then rerun strict-ready audit on this family only
- Te Papa: status=tiny_seed_after_manual_resolution; rows=35; eligible=1; primary_blocker=missing_member_or_sub; signal=collection_api_object_signal; next=review blocked eligible clusters, then rerun strict-ready audit on this family only
- Library of Congress: status=tiny_seed_after_manual_resolution; rows=22; eligible=4; primary_blocker=missing_anchor; signal=library_archive_series_signal; next=review blocked eligible clusters, then rerun strict-ready audit on this family only
- Another Graphic: status=tiny_seed_after_manual_resolution; rows=11; eligible=7; primary_blocker=lane_not_strong; signal=editorial_project_or_event_signal; next=review blocked eligible clusters, then rerun strict-ready audit on this family only
- Gallica / BnF APIs: status=define_parentage_signal; rows=95; eligible=0; primary_blocker=no_eligible_rows; signal=bibliographic_sequence_signal; next=write a source-family parentage signal and test as audit-only scoring
- Georgia State CONTENTdm: status=define_parentage_signal; rows=63; eligible=0; primary_blocker=lane_not_strong; signal=collection_record_series_signal; next=write a source-family parentage signal and test as audit-only scoring
- DigitalNZ: status=define_parentage_signal; rows=30; eligible=0; primary_blocker=lane_not_strong; signal=collection_api_object_signal; next=write a source-family parentage signal and test as audit-only scoring
- NAIDOC Poster Gallery: status=define_parentage_signal; rows=27; eligible=0; primary_blocker=lane_not_strong; signal=editorial_project_or_event_signal; next=write a source-family parentage signal and test as audit-only scoring
- Malaysia Design Archive: status=define_parentage_signal; rows=9; eligible=0; primary_blocker=lane_not_strong; signal=editorial_project_or_event_signal; next=write a source-family parentage signal and test as audit-only scoring
- Wellcome Collection: status=improve_design_object_and_cluster_confidence; rows=32; eligible=0; primary_blocker=lane_not_strong; signal=collection_api_object_signal; next=separate design-object evidence from host/source-register evidence before packeting
- Smithsonian: status=improve_design_object_and_cluster_confidence; rows=8; eligible=0; primary_blocker=lane_not_strong; signal=collection_api_object_signal; next=separate design-object evidence from host/source-register evidence before packeting
- Asian Film Archive: status=improve_design_object_and_cluster_confidence; rows=7; eligible=0; primary_blocker=lane_not_strong; signal=editorial_project_or_event_signal; next=separate design-object evidence from host/source-register evidence before packeting
- Design Reviewed: status=improve_design_object_and_cluster_confidence; rows=6; eligible=0; primary_blocker=lane_not_strong; signal=editorial_project_or_event_signal; next=separate design-object evidence from host/source-register evidence before packeting
- Princeton Figgy: status=improve_design_object_and_cluster_confidence; rows=6; eligible=0; primary_blocker=lane_not_strong; signal=library_archive_series_signal; next=separate design-object evidence from host/source-register evidence before packeting

## Tiny Sandbox Seeds

- Global / transnational|Midcentury modern graphic communication|Internet Archive|2015-2019: priority=54; path=resolve_region_scope_before_packeting; blockers=macro_or_unresolved_region; missing_member_or_sub
- United States|New Deal and civic poster programs|Library of Congress|1935-1939: priority=48; path=identify_blocker_free_anchor_candidate; blockers=missing_anchor
- Global / transnational|Modern typography and layout|Another Graphic|2025-2029: priority=41; path=resolve_region_scope_before_packeting; blockers=macro_or_unresolved_region; lane_not_strong; confidence_not_high; missing_anchor
- Global / transnational|Midcentury modern graphic communication|Internet Archive|2010-2014: priority=37; path=resolve_region_scope_before_packeting; blockers=macro_or_unresolved_region
- Global / transnational|Midcentury modern graphic communication|Internet Archive|2020-2024: priority=30; path=resolve_region_scope_before_packeting; blockers=macro_or_unresolved_region; missing_member_or_sub
- Aotearoa New Zealand|World War and public-information graphics|Te Papa|1940-1944: priority=27; path=identify_blocker_free_member_or_sub_candidate; blockers=missing_member_or_sub

## Safety

- Rule candidates are audit signals only.
- No candidate may upgrade source authority, authorship, rights state, or IMG01/IMG03 state.
- No source-family signal may override macro/unresolved region review.
- Event/photo/interview/profile/stamp/support records remain card/support candidates unless design-object evidence is explicit.
