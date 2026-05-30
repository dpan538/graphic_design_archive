-- Modern Graphic Design History Archive Index
-- Database validation queries.
-- Run after schema migrations and seed import.

do $$
declare
  expected int;
  actual int;
begin
  select count(*) into actual from historical_nodes;
  expected := 15;
  if actual <> expected then
    raise exception 'historical_nodes count mismatch: expected %, got %', expected, actual;
  end if;

  select count(*) into actual from movements;
  expected := 38;
  if actual <> expected then
    raise exception 'movements count mismatch: expected %, got %', expected, actual;
  end if;

  select count(*) into actual from media_technologies;
  expected := 35;
  if actual <> expected then
    raise exception 'media_technologies count mismatch: expected %, got %', expected, actual;
  end if;

  select count(*) into actual from sources;
  expected := 54;
  if actual <> expected then
    raise exception 'sources count mismatch: expected %, got %', expected, actual;
  end if;

  select count(*) into actual from search_vocabulary;
  expected := 200;
  if actual <> expected then
    raise exception 'search_vocabulary count mismatch: expected %, got %', expected, actual;
  end if;

  select count(*) into actual from rights_strategies;
  expected := 10;
  if actual <> expected then
    raise exception 'rights_strategies count mismatch: expected %, got %', expected, actual;
  end if;

  select count(*) into actual from searchable_documents;
  expected := 992;
  if actual <> expected then
    raise exception 'searchable_documents count mismatch: expected %, got %', expected, actual;
  end if;

  select count(*) into actual from regions;
  expected := 15;
  if actual <> expected then
    raise exception 'regions count mismatch: expected %, got %', expected, actual;
  end if;

  select count(*) into actual from coverage_matrix;
  expected := 225;
  if actual <> expected then
    raise exception 'coverage_matrix count mismatch: expected %, got %', expected, actual;
  end if;

  select count(*) into actual from regional_source_priorities;
  expected := 90;
  if actual <> expected then
    raise exception 'regional_source_priorities count mismatch: expected %, got %', expected, actual;
  end if;

  select count(*) into actual from classification_axes;
  expected := 10;
  if actual <> expected then
    raise exception 'classification_axes count mismatch: expected %, got %', expected, actual;
  end if;

  select count(*) into actual from geographies;
  expected := 109;
  if actual <> expected then
    raise exception 'geographies count mismatch: expected %, got %', expected, actual;
  end if;

  select count(*) into actual from regional_movements;
  expected := 89;
  if actual <> expected then
    raise exception 'regional_movements count mismatch: expected %, got %', expected, actual;
  end if;

  select count(*) into actual from regional_event_nodes;
  expected := 63;
  if actual <> expected then
    raise exception 'regional_event_nodes count mismatch: expected %, got %', expected, actual;
  end if;

  select count(*) into actual from experimental_ingest_candidates;
  expected := 39;
  if actual <> expected then
    raise exception 'experimental_ingest_candidates count mismatch: expected %, got %', expected, actual;
  end if;
end
$$;

do $$
begin
  if exists (select 1 from historical_nodes where node_id is null or node_name is null or node_name = '') then
    raise exception 'historical_nodes has missing required identifiers or labels';
  end if;

  if exists (select 1 from movements where movement_id is null or name is null or name = '') then
    raise exception 'movements has missing required identifiers or labels';
  end if;

  if exists (select 1 from media_technologies where media_id is null or term is null or term = '') then
    raise exception 'media_technologies has missing required identifiers or labels';
  end if;

  if exists (select 1 from sources where source_id is null or name is null or name = '' or url is null or url = '') then
    raise exception 'sources has missing identifiers, names, or URLs';
  end if;

  if exists (select 1 from rights_strategies where strategy_id is null or source_category is null or source_category = '') then
    raise exception 'rights_strategies has missing identifiers or categories';
  end if;

  if exists (select 1 from search_vocabulary where term_id is null or term is null or term = '' or normalized_term is null or normalized_term = '') then
    raise exception 'search_vocabulary has missing identifiers or terms';
  end if;

  if exists (select 1 from regions where region_id is null or region_name is null or region_name = '') then
    raise exception 'regions has missing identifiers or names';
  end if;

  if exists (select 1 from coverage_matrix where coverage_id is null or node_id is null or region_id is null) then
    raise exception 'coverage_matrix has missing identifiers or foreign keys';
  end if;

  if exists (select 1 from classification_axes where axis_id is null or axis_name is null or axis_name = '') then
    raise exception 'classification_axes has missing identifiers or names';
  end if;

  if exists (select 1 from geographies where geo_id is null or name is null or name = '' or geo_type is null or geo_type = '') then
    raise exception 'geographies has missing identifiers, names, or types';
  end if;

  if exists (select 1 from regional_movements where regional_movement_id is null or name is null or name = '' or region_id is null) then
    raise exception 'regional_movements has missing identifiers, names, or region links';
  end if;

  if exists (select 1 from regional_event_nodes where event_node_id is null or event_name is null or event_name = '' or region_id is null) then
    raise exception 'regional_event_nodes has missing identifiers, names, or region links';
  end if;

  if exists (select 1 from experimental_ingest_candidates where experimental_candidate_id is null or candidate_name is null or candidate_name = '' or expected_image_zone is null) then
    raise exception 'experimental_ingest_candidates has missing identifiers, names, or image-zone decisions';
  end if;
end
$$;

do $$
begin
  if to_regclass('public.source_terms_reviews') is null then
    raise exception 'missing source_terms_reviews table';
  end if;
  if to_regclass('public.rights_reviews') is null then
    raise exception 'missing rights_reviews table';
  end if;
  if to_regclass('public.ingestion_runs') is null then
    raise exception 'missing ingestion_runs table';
  end if;
  if to_regclass('public.ingestion_events') is null then
    raise exception 'missing ingestion_events table';
  end if;
  if to_regclass('public.source_record_snapshots') is null then
    raise exception 'missing source_record_snapshots table';
  end if;
  if to_regclass('public.audit_log') is null then
    raise exception 'missing audit_log table';
  end if;
  if to_regclass('public.api_search_documents') is null then
    raise exception 'missing api_search_documents view';
  end if;
  if to_regclass('public.api_source_registry') is null then
    raise exception 'missing api_source_registry view';
  end if;
  if to_regclass('public.api_regions') is null then
    raise exception 'missing api_regions view';
  end if;
  if to_regclass('public.api_coverage_matrix') is null then
    raise exception 'missing api_coverage_matrix view';
  end if;
  if to_regclass('public.classification_axes') is null then
    raise exception 'missing classification_axes table';
  end if;
  if to_regclass('public.geographies') is null then
    raise exception 'missing geographies table';
  end if;
  if to_regclass('public.regional_movements') is null then
    raise exception 'missing regional_movements table';
  end if;
  if to_regclass('public.regional_event_nodes') is null then
    raise exception 'missing regional_event_nodes table';
  end if;
  if to_regclass('public.api_classification_axes') is null then
    raise exception 'missing api_classification_axes view';
  end if;
  if to_regclass('public.api_geographies') is null then
    raise exception 'missing api_geographies view';
  end if;
  if to_regclass('public.api_regional_movements') is null then
    raise exception 'missing api_regional_movements view';
  end if;
  if to_regclass('public.api_regional_event_nodes') is null then
    raise exception 'missing api_regional_event_nodes view';
  end if;
  if to_regclass('public.display_templates') is null then
    raise exception 'missing display_templates table';
  end if;
  if to_regclass('public.publication_surfaces') is null then
    raise exception 'missing publication_surfaces table';
  end if;
  if to_regclass('public.publication_surface_pages') is null then
    raise exception 'missing publication_surface_pages table';
  end if;
  if to_regclass('public.surface_table_rows') is null then
    raise exception 'missing surface_table_rows table';
  end if;
  if to_regclass('public.folder_views') is null then
    raise exception 'missing folder_views table';
  end if;
  if to_regclass('public.folder_memberships') is null then
    raise exception 'missing folder_memberships table';
  end if;
  if to_regclass('public.filing_registry_cards') is null then
    raise exception 'missing filing_registry_cards table';
  end if;
  if to_regclass('public.filing_registry_members') is null then
    raise exception 'missing filing_registry_members table';
  end if;
  if to_regclass('public.sparse_cards') is null then
    raise exception 'missing sparse_cards table';
  end if;
  if to_regclass('public.archive_bookmarks') is null then
    raise exception 'missing archive_bookmarks table';
  end if;
  if to_regclass('public.api_publication_surfaces') is null then
    raise exception 'missing api_publication_surfaces view';
  end if;
  if to_regclass('public.api_publication_surface_pages') is null then
    raise exception 'missing api_publication_surface_pages view';
  end if;
  if to_regclass('public.api_surface_table_rows') is null then
    raise exception 'missing api_surface_table_rows view';
  end if;
  if to_regclass('public.api_folder_views') is null then
    raise exception 'missing api_folder_views view';
  end if;
  if to_regclass('public.api_folder_memberships') is null then
    raise exception 'missing api_folder_memberships view';
  end if;
  if to_regclass('public.api_filing_registry_cards') is null then
    raise exception 'missing api_filing_registry_cards view';
  end if;
  if to_regclass('public.api_filing_registry_members') is null then
    raise exception 'missing api_filing_registry_members view';
  end if;
  if to_regclass('public.api_sparse_cards') is null then
    raise exception 'missing api_sparse_cards view';
  end if;
  if to_regclass('public.api_archive_bookmarks') is null then
    raise exception 'missing api_archive_bookmarks view';
  end if;
  if to_regclass('public.evidence_bundles') is null then
    raise exception 'missing evidence_bundles table';
  end if;
  if to_regclass('public.evidence_bundle_items') is null then
    raise exception 'missing evidence_bundle_items table';
  end if;
  if to_regclass('public.authority_resolution_events') is null then
    raise exception 'missing authority_resolution_events table';
  end if;
  if to_regclass('public.entity_appellations') is null then
    raise exception 'missing entity_appellations table';
  end if;
  if to_regclass('public.geography_appellations') is null then
    raise exception 'missing geography_appellations table';
  end if;
  if to_regclass('public.api_evidence_bundles') is null then
    raise exception 'missing api_evidence_bundles view';
  end if;
  if to_regclass('public.api_evidence_bundle_items') is null then
    raise exception 'missing api_evidence_bundle_items view';
  end if;
  if to_regclass('public.api_external_identifier_status') is null then
    raise exception 'missing api_external_identifier_status view';
  end if;
  if to_regclass('public.api_authority_resolution_events') is null then
    raise exception 'missing api_authority_resolution_events view';
  end if;
  if to_regclass('public.api_entity_appellations') is null then
    raise exception 'missing api_entity_appellations view';
  end if;
  if to_regclass('public.api_geography_appellations') is null then
    raise exception 'missing api_geography_appellations view';
  end if;
  if to_regclass('public.api_relation_predicate_rules') is null then
    raise exception 'missing api_relation_predicate_rules view';
  end if;
  if to_regclass('public.api_protocol_rights_reviews') is null then
    raise exception 'missing api_protocol_rights_reviews view';
  end if;
  if to_regclass('public.experimental_ingest_candidates') is null then
    raise exception 'missing experimental_ingest_candidates table';
  end if;
  if to_regclass('public.api_source_policy_summary') is null then
    raise exception 'missing api_source_policy_summary view';
  end if;
  if to_regclass('public.api_source_terms_review_policy') is null then
    raise exception 'missing api_source_terms_review_policy view';
  end if;
  if to_regclass('public.api_experimental_ingest_candidates') is null then
    raise exception 'missing api_experimental_ingest_candidates view';
  end if;
  if to_regclass('public.source_record_relations') is null then
    raise exception 'missing source_record_relations table';
  end if;
  if to_regclass('public.digital_representations') is null then
    raise exception 'missing digital_representations table';
  end if;
  if to_regclass('public.field_provenance') is null then
    raise exception 'missing field_provenance table';
  end if;
  if to_regclass('public.record_family_profiles') is null then
    raise exception 'missing record_family_profiles table';
  end if;
  if to_regclass('public.ingest_validation_rules') is null then
    raise exception 'missing ingest_validation_rules table';
  end if;
  if to_regclass('public.first_ingest_record_targets') is null then
    raise exception 'missing first_ingest_record_targets table';
  end if;
  if to_regclass('public.first_ingest_target_verifications') is null then
    raise exception 'missing first_ingest_target_verifications table';
  end if;
  if to_regclass('public.api_source_record_relations') is null then
    raise exception 'missing api_source_record_relations view';
  end if;
  if to_regclass('public.api_digital_representations') is null then
    raise exception 'missing api_digital_representations view';
  end if;
  if to_regclass('public.api_field_provenance') is null then
    raise exception 'missing api_field_provenance view';
  end if;
  if to_regclass('public.api_record_family_profiles') is null then
    raise exception 'missing api_record_family_profiles view';
  end if;
  if to_regclass('public.api_ingest_validation_rules') is null then
    raise exception 'missing api_ingest_validation_rules view';
  end if;
  if to_regclass('public.api_first_ingest_record_targets') is null then
    raise exception 'missing api_first_ingest_record_targets view';
  end if;
  if to_regclass('public.api_first_ingest_target_verifications') is null then
    raise exception 'missing api_first_ingest_target_verifications view';
  end if;
end
$$;

select 'database validation passed' as validation_status;
