# Region / Geography Normalization Decisions v1

Scope: read-only reconciliation of the Region and Geography Normalization research packet against live project taxonomy audit outputs. This report does not rewrite records, source files, public surfaces, regions, or geographies.

## Summary

- decision rows: 29
- auto country mapping rows: 9
- structural or sensitive split rows: 10
- likely true source-gap rows after cleanup: 4
- internal QA rows: 1

## Decision Classes

- auto_country_mapping: 7
- auto_country_mapping_with_historical_review: 1
- auto_country_mapping_with_specificity_review: 1
- controlled_geo_missing: 1
- controlled_region_rename_candidate: 1
- controlled_region_semantics_review: 1
- historical_period_review: 1
- internal_qa_state: 1
- likely_true_source_gap: 1
- likely_true_source_gap_after_Australia_split: 1
- likely_true_source_gap_after_Palestine_split: 1
- likely_true_source_gap_after_Southern_Africa_split: 1
- mapping_gap_or_display_alias: 1
- parent_browse_node_not_item_gap: 1
- possible_hidden_mapping_gap: 3
- possible_hidden_mapping_gap_or_source_gap: 1
- sensitive_historical_split: 1
- sensitive_structural_split: 1
- structural_split: 2
- structural_split_with_missing_geo: 1

## Proposed Actions

- add_country_geography_then_map: 1
- audit_unresolved_then_target_source_routes: 1
- auto_map: 7
- keep_parent_region_only: 1
- keep_pending_then_batch_resolve: 1
- map_then_review_1949_1990_records: 1
- map_then_review_constituent_country_when_named: 1
- map_to_REG004_and_review_exact_child_need: 1
- prioritize_Africa_beyond_Southern_Africa: 1
- prioritize_MENA_beyond_Palestine: 1
- prioritize_Pacific_and_Aotearoa_after_protocol_review: 1
- prioritize_source_discovery_after_mapping_cleanup: 1
- resolve_unresolved_region_before_source_gap_claim: 1
- retain_id_but_stop_assigning_full_phrase_as_item_label: 1
- review_rename_to_Northern_America: 1
- route_by_date_and_territorial_scope: 1
- split_China_Hong_Kong_and_unresolved_records_first: 2
- split_and_add_country_if_needed: 1
- split_by_record_evidence: 1
- split_place_and_context: 1
- split_with_historical_review: 1
- split_with_protocol_review: 1

## Highest-Impact Rows

- Australia / Indigenous: sensitive_structural_split -> split_with_protocol_review (surfaces=95, sources=43)
- China / Hong Kong: structural_split -> split_by_record_evidence (surfaces=53, sources=46)
- Latin America: mapping_gap_or_display_alias -> map_to_REG004_and_review_exact_child_need (surfaces=925, sources=923)
- Palestine / transnational: sensitive_historical_split -> split_with_historical_review (surfaces=25, sources=23)
- South Africa / Botswana: structural_split_with_missing_geo -> split_and_add_country_if_needed (surfaces=57, sources=36)
- Unresolved region: internal_qa_state -> keep_pending_then_batch_resolve (surfaces=4693, sources=4079)

## Likely True Source Gaps After Mapping Cleanup

- Southeast Asia: prioritize_source_discovery_after_mapping_cleanup · guardrail: Do not use one country as proxy for the region.
- Middle East and North Africa: prioritize_MENA_beyond_Palestine · guardrail: Do not treat political-poster-only material as full regional coverage.
- Africa: prioritize_Africa_beyond_Southern_Africa · guardrail: Avoid continent-as-single-category treatment.
- Oceania and Pacific: prioritize_Pacific_and_Aotearoa_after_protocol_review · guardrail: Do not let Australian institutional data stand in for Pacific coverage.

## Implementation Notes

- First pass should only auto-map high-confidence country labels already present in `geographies.csv`.
- Slash labels should be split from record evidence, not normalized as preferred labels.
- `Unresolved region` should be removed from public browse semantics and treated as an internal QA state.
- Sensitive and historical labels need period/source review before any automated rewrite.
- True source-gap capture should start only after the major mapping and split decisions are applied or sampled.

## Generated Files

- `data/region_geography_normalization_decisions_v1.csv`
- `docs/capture/REGION_GEOGRAPHY_NORMALIZATION_DECISIONS_v1.md`
