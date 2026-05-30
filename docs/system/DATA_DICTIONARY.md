# Data Dictionary v0

**Status:** Draft derived from `data/*.csv` seed files.  
**Source basis:** `Rights-Aware Archive Index Framework for Modern Graphic Design History.docx` and `Methodology_v0.md`.

## Purpose

This dictionary defines the first implementation fields for the archive index seed layer. These fields are not yet the final production schema. They are designed to support methodology validation, search testing, rights review, and database design.

## Common Conventions

- IDs are stable local identifiers and should not be reused after deletion.
- Empty fields mean unknown, not applicable, or pending review. Production tables should distinguish these states more explicitly.
- Semicolon-separated fields indicate a controlled-list candidate that may later become a join table.
- Authority IDs are placeholders until an authority-resolution pass is completed.
- Rights and display fields are advisory until source-specific terms are reviewed.

## `historical_nodes.csv`

Historical spine and broad node map.

- `node_id`: stable local node ID, e.g. `HN001`.
- `node_name`: public node label.
- `date_start`: normalized start year where possible.
- `date_end`: normalized end year where possible.
- `date_text`: human-readable date range.
- `geo_centers`: major places or regions.
- `transnational_routes`: circulation routes, migrations, or network paths.
- `associated_formations`: linked movements, schools, or formations.
- `key_media_technologies`: important media, processes, or technical conditions.
- `key_object_types`: likely object or record types.
- `key_people`: notable people or collectives, not exhaustive.
- `key_institutions`: schools, studios, archives, publishers, or agencies.
- `likely_source_types`: expected archive/source categories.
- `search_keywords`: deterministic search seed terms.
- `required_metadata_fields`: fields needed to describe records in this node responsibly.
- `rights_risk_level`: rough rights risk, not legal advice.
- `underdocumented_notes`: historiographic gaps and inclusion cautions.
- `editorial_note`: local scope or indexing guidance.
- `source_basis_note`: source or rationale for the seed row.

## `movements.csv`

Movements, formations, schools, regimes, publishing cultures, and counter-historical groupings.

- `movement_id`: stable local movement ID, e.g. `MV001`.
- `name`: preferred label.
- `alternate_names`: alternate names or aliases.
- `date_start`: normalized start year where possible.
- `date_end`: normalized end year where possible.
- `date_text`: human-readable date range.
- `region`: geographic scope.
- `group_type`: movement, school, field, technical regime, counterpublic formation, etc.
- `associated_people`: notable people.
- `associated_institutions`: notable institutions, collectives, or publishers.
- `representative_media`: formats or media where the formation appears.
- `relation_to_graphic_design`: why the formation matters to the project.
- `source_confidence`: rough confidence level from the report.
- `search_terms`: deterministic search terms.
- `authority_scheme`: likely authority source.
- `authority_id`: unresolved external ID placeholder.
- `authority_status`: current authority resolution state.
- `editorial_scope_note`: caution or inclusion note.

## `media_technologies.csv`

Processes, technologies, production methods, formats, and object types.

- `media_id`: stable local media/technology ID, e.g. `MT001`.
- `term`: preferred label.
- `term_type`: process, technology, format, system, software, etc.
- `definition`: concise definition.
- `date_start`: normalized start year where possible.
- `date_end`: normalized end year where possible.
- `date_text`: human-readable date range.
- `relation_to_graphic_design`: relevance to graphic design history.
- `associated_source_types`: likely source types.
- `required_metadata_fields`: fields needed to describe records using this term.
- `search_keywords`: deterministic search terms.
- `rights_display_issues`: rights or display concerns.
- `authority_scheme`: future authority source.
- `authority_id`: unresolved external ID placeholder.

## `source_registry.csv`

Candidate source universe.

- `source_id`: stable local source ID, e.g. `SRC001`.
- `name`: source name.
- `url`: main source URL.
- `source_type`: museum, archive, aggregator, library, community archive, etc.
- `access_method`: API, dataset, search interface, manual, OAI-PMH, IIIF, etc.
- `api_base_or_endpoint`: API or access endpoint when known.
- `iiif_support`: yes/no/unknown/mixed.
- `oai_pmh_support`: yes/no/unknown/mixed.
- `dataset_support`: yes/no/unknown/mixed.
- `geo_coverage`: geographic coverage.
- `historical_coverage`: historical coverage.
- `graphic_design_relevance`: relevance estimate.
- `likely_record_types`: expected record types.
- `rights_summary`: source-level rights summary.
- `rights_uri_support`: whether structured rights appear likely.
- `metadata_quality_estimate`: rough quality estimate.
- `stable_identifiers`: whether stable identifiers are available.
- `automated_ingestion`: yes/no/partial/caution.
- `link_only_safer`: whether link-only indexing is safer.
- `priority`: Launch, Launch, Later, or Reference Only.
- `notes`: implementation notes.
- `last_verified_date`: date reviewed.

## `search_vocabulary.csv`

Seed terms for deterministic search and query expansion.

- `term_id`: stable local term ID, e.g. `SV0001`.
- `term`: search term.
- `normalized_term`: lowercase/search-normalized form.
- `term_class`: movement, object type, theme, region, etc.
- `language`: language code; currently many are `und` until language tagging is reviewed.
- `alternate_forms`: variant spellings or multilingual forms.
- `broader_term`: future hierarchy field.
- `narrower_term`: future hierarchy field.
- `related_terms`: future relation field.
- `preferred_for_query`: whether the term should be used in search.
- `query_context`: intended search use.
- `authority_scheme`: future authority source.
- `authority_id`: unresolved external ID placeholder.
- `notes`: review notes.

## `rights_strategy.csv`

Rights-safe indexing and display rules.

- `strategy_id`: stable local rights strategy ID.
- `source_category`: source or rights category.
- `rights_signal`: what rights signal triggers the strategy.
- `ingest_policy`: what may be stored.
- `display_policy`: what may be shown.
- `review_required`: whether human review is required.
- `citation_required`: whether citation is required.
- `attrib_required`: whether attribution is required.
- `thumbnail_allowed`: thumbnail display policy.
- `full_image_allowed`: full image display policy.
- `iiif_embed_allowed`: IIIF/embed policy.
- `notes`: operational notes.

## `classification_axes.csv`

Required classification axes for the launch framework.

- `axis_id`: stable local axis ID, e.g. `AX001`.
- `axis_name`: machine-readable axis name.
- `axis_type`: geography, date, history, media, language, or source.
- `required_for_launch`: whether the axis must exist before launch design work.
- `required_for_record`: whether records must carry this axis.
- `supports_multiple`: whether multiple values are allowed.
- `api_filter`: whether the axis should be exposed as a filter.
- `controlled_source`: table or field family controlling values.
- `notes`: implementation and methodological notes.

## `geographies.csv`

Launch-scope geography, country/context, territory, macro-region, transnational, and historical-context rows.

- `geo_id`: stable local geography ID, e.g. `GEO040`.
- `name`: display name.
- `parent_geo_id`: parent geography when applicable.
- `region_id`: related launch region.
- `geo_type`: macro_region, country_context, city/territory_context, regional_context, historical_context, or transnational_context.
- `iso_code`: ISO code where applicable.
- `language_scope`: languages expected in source records.
- `script_scope`: scripts expected in source records.
- `date_scope`: broad period note.
- `notes`: bias, source, or classification notes.

## `regional_movements.csv`

Regional movements, formations, schools, publishing cultures, state formations, counterpublics, and technical/digital regimes.

- `regional_movement_id`: stable local ID, e.g. `RM028`.
- `name`: formation name.
- `alternate_names`: variants or translated names.
- `region_id`: related launch region.
- `geo_id`: related geography/context.
- `date_start`: normalized start year where possible.
- `date_end`: normalized end year where possible.
- `date_text`: human-readable date range.
- `formation_type`: movement, publishing formation, state formation, counterpublic formation, technical regime, etc.
- `related_node_ids`: semicolon-separated historical node IDs.
- `related_movement_ids`: semicolon-separated canonical/global movement IDs when applicable.
- `key_media`: likely object/media types.
- `source_needs`: source families required for validation.
- `rights_risk`: low, medium, high, very high, or unknown.
- `status`: current inclusion/readiness status.
- `notes`: methodological notes.

## `regional_event_nodes.csv`

Dateable regional historical nodes that connect geography, source needs, and the historical spine.

- `event_node_id`: stable local event-node ID, e.g. `REN022`.
- `event_name`: event/node display name.
- `event_type`: technology, movement, state, political, commercial, digital, script, or other node type.
- `region_id`: related launch region.
- `geo_id`: related geography/context.
- `date_start`: normalized start year where possible.
- `date_end`: normalized end year where possible.
- `date_text`: human-readable date range.
- `related_node_ids`: semicolon-separated historical node IDs.
- `related_regional_movement_ids`: semicolon-separated regional movement IDs.
- `source_need`: source families required for validation.
- `rights_risk`: low, medium, high, very high, or unknown.
- `status`: current inclusion/readiness status.
- `notes`: methodological notes.

## `fallback_source_stubs.csv`

Fallback source stubs for first-ingest targets that cannot yet become source records.

These rows preserve historical coverage and user navigation without treating unresolved, blocked, or search-path-only material as ingested evidence.

- `fallback_stub_id`: stable local fallback ID, e.g. `FSS026`.
- `first_target_id`: related first-ingest target ID.
- `scope_cell_id`: related first-ingest scope cell.
- `target_label`: target label to preserve in the historical area.
- `source_name`: source where the material is expected or where the target was attempted.
- `source_url_or_search_path`: original URL or deterministic search path from target selection.
- `canonical_url`: confirmed or plausible URL if available.
- `replacement_url`: better replacement source when recommended.
- `fallback_status`: reason-class status such as `search_path_only`, `browser_recheck_required`, `page_level_recheck_required`, or `replacement_recommended`.
- `public_stub_policy`: how the frontend may show the stub.
- `expected_image_zone`: expected image state; usually `IMG00` for image-bearing but not ingested material, or `IMG04` for text-only fallback.
- `display_area_policy`: whether to preserve an empty frame or render a text-only fallback.
- `not_ingested_reason`: concise reason the target is not a source record.
- `user_action_label`: public action label, e.g. `View at source` or `Search at source`.
- `user_action_url`: source URL users can open; for search paths, this should be the source root or stable search page, not a fake record URL.
- `verification_decision`: mechanical verification decision from the first pass.
- `verified_at`: verification date.
- `verified_by`: verifier.
- `evidence_summary`: summary of what was observed.
- `required_action`: next action needed before promotion.
- `blocking_reason`: specific block if applicable.

## Next Review Passes

1. Authority resolution for movements, people, institutions, places, and media terms.
2. Source-specific rights and terms review.
3. Conversion of semicolon-separated multi-value fields into join tables.
4. Jurisdiction-aware copyright review for priority sources.
5. Search vocabulary language tagging and synonym expansion.
