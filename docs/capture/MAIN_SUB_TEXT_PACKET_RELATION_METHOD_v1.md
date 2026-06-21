# Main/Sub/Text Packet Relation Method v1

Scope: non-mutating second-pass audit for packet relation, text need, and main/sub/card boundary planning.

This pass reads the full-role assessment only. It does not apply overrides, rebuild payloads, download images, or change rights/image states.

## Inputs and Outputs

- Assessment rows read: 13537.
- Relation clusters audited: 2579.
- Relation role queue rows: 12257.
- Validation sample rows: 800.

## Cluster Lanes

- `mixed_manual_relation_review`: 1523.
- `small_anchor_or_manual`: 426.
- `card_context_cluster`: 258.
- `strong_packet_candidate`: 161.
- `packet_parentage_review`: 92.
- `text_scaffold_needed`: 78.
- `macro_cluster_needs_split`: 41.

## Proposed Relation Roles

- `card_context_candidate`: 5666.
- `packet_member_review`: 3094.
- `provisional_main_anchor_needs_text`: 1018.
- `sub_under_packet_candidate`: 964.
- `manual_relation_review`: 748.
- `candidate_packet_anchor`: 681.
- `anchor_or_sibling_review`: 85.
- `text_or_appendix_candidate`: 1.

## Readiness

- `eligible_for_next_sandbox_review`: 1986.
- `method_review_only`: 4604.
- `support_only_review`: 5667.

## Method Reading

- `strong_packet_candidate` clusters may be used to test parent/child relation rules, but they are not automatic release mutations.
- `packet_parentage_review` is the central backlog: these clusters likely contain usable sub/main relations, but parent selection must be explicit.
- `text_scaffold_needed` means main status depends on real editorial text; generated filler should not count.
- `macro_cluster_needs_split` is a warning lane for over-broad buckets such as global Commons typography groups; these need narrower source series, creator, project, object-type, or theme splitting before sandbox use.
- `card_context_cluster` preserves weak context, stamp, event/photo, or source-file evidence without treating it as a main research anchor.

## Advantages

- Separates packet relation design from rights/image/source-count work.
- Keeps main-sheet demotion reversible during methodology testing.
- Provides a concrete text-page estimate without forcing text generation now.
- Makes parent selection auditable at the cluster level before any rebuild.

## Disadvantages

- Cluster keys are still provisional and depend on current region/theme/source/five-year grouping.
- Commons-heavy source distribution can overrepresent card-context decisions.
- The method cannot prove final reading quality until a later small rebuild displays the packet structure.
- Text-page estimates are planning signals, not release requirements yet.

## Next Permitted Action

Review `data/prefreeze_main_sub_text_packet_relation_validation_sample_v1.csv` and use the `eligible_for_next_sandbox_review` rows for a later, limited sandbox preview only after parent-selection rules are accepted.

## Safety

- No image files were downloaded.
- No rights, source authority, authorship, or IMG01/IMG03 upgrades were made.
- Region scarcity, source family, and period signals remain internal triage signals only.
