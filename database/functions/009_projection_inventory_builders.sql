\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE FUNCTION release.add_research_source_lineage_to_draft(
  p_release_id uuid, p_source_role release.research_source_role,
  p_source_asset_id uuid, p_source_git_commit text
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
DECLARE
  v_asset raw.source_asset%ROWTYPE;
  v_expected raw.asset_authority;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);
  SELECT * INTO STRICT v_asset
  FROM raw.source_asset a
  WHERE a.source_asset_id = p_source_asset_id;
  v_expected := CASE p_source_role
    WHEN 'v48_candidate_json' THEN 'canonical_migration_input'
    WHEN 'v48_sqlite_reconciliation' THEN 'immutable_reconciliation_evidence'
    ELSE 'integrity_evidence'
  END;
  IF v_asset.authority IS DISTINCT FROM v_expected THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'SOURCE_ROLE_AUTHORITY_MISMATCH';
  END IF;
  INSERT INTO release.research_source_lineage (
    research_release_id, source_role, source_asset_id,
    asset_authority, asset_sha256, source_git_commit
  ) VALUES (
    p_release_id, p_source_role, v_asset.source_asset_id,
    v_asset.authority, v_asset.sha256, p_source_git_commit
  );
END
$function$;

CREATE FUNCTION release.set_research_projection_set_to_draft(
  p_release_id uuid, p_database_snapshot_identity text,
  p_migration_set_sha256 core.sha256_hex,
  p_projection_query_pack_sha256 core.sha256_hex
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);
  INSERT INTO release.research_projection_set VALUES (
    p_release_id, p_database_snapshot_identity,
    p_migration_set_sha256, p_projection_query_pack_sha256);
END
$function$;

CREATE FUNCTION release.set_research_registry_snapshot_to_draft(
  p_release_id uuid, p_predicate_registry_sha256 core.sha256_hex,
  p_relation_registry_sha256 core.sha256_hex,
  p_epistemic_registry_sha256 core.sha256_hex
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);
  INSERT INTO release.research_registry_snapshot VALUES (
    p_release_id, p_predicate_registry_sha256,
    p_relation_registry_sha256, p_epistemic_registry_sha256);
END
$function$;

CREATE FUNCTION release.copy_research_corpus_snapshot_to_draft(
  p_release_id uuid, p_corpus_version_id uuid,
  p_missingness_snapshot_id uuid, p_coverage_snapshot_id uuid,
  p_concentration_receipt_sha256 core.sha256_hex
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);
  INSERT INTO release.research_corpus_snapshot (
    research_release_id, corpus_version_id, corpus_token,
    corpus_version_token, selection_policy_sha256, population_frame,
    missingness_snapshot_sha256, coverage_snapshot_sha256,
    concentration_receipt_sha256
  )
  SELECT p_release_id, cv.corpus_version_id, c.corpus_token,
    cv.version_token, cv.policy_sha256, cv.population_frame,
    m.input_sha256, v.input_sha256, p_concentration_receipt_sha256
  FROM research.corpus_version cv
  JOIN research.corpus c ON c.corpus_id = cv.corpus_id
  JOIN research.missingness_snapshot m
    ON m.missingness_snapshot_id = p_missingness_snapshot_id
   AND m.corpus_version_id = cv.corpus_version_id
  JOIN research.coverage_snapshot v
    ON v.coverage_snapshot_id = p_coverage_snapshot_id
   AND v.corpus_version_id = cv.corpus_version_id
  WHERE cv.corpus_version_id = p_corpus_version_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'CORPUS_MISSINGNESS_COVERAGE_COPY_MISMATCH';
  END IF;
END
$function$;

CREATE FUNCTION release.add_research_count_snapshot_to_draft(
  p_release_id uuid, p_metric_code core.release_token,
  p_scope_definition text, p_unit_definition text,
  p_query_sha256 core.sha256_hex, p_exact_count bigint
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);
  INSERT INTO release.research_count_snapshot VALUES (
    p_release_id, p_metric_code, p_scope_definition,
    p_unit_definition, p_query_sha256, p_exact_count);
END
$function$;

CREATE FUNCTION release.add_research_asset_to_draft(
  p_release_id uuid, p_relative_path text,
  p_resource_kind core.release_token, p_media_type text,
  p_content_encoding text, p_schema_id text,
  p_byte_length bigint, p_record_count bigint,
  p_sha256 core.sha256_hex, p_deterministic_sort_key text,
  p_partition_description text, p_uncompressed_sha256 core.sha256_hex
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);
  INSERT INTO release.research_asset VALUES (
    p_release_id, p_relative_path, p_resource_kind, p_media_type,
    p_content_encoding, p_schema_id, p_byte_length, p_record_count,
    p_sha256, p_deterministic_sort_key, p_partition_description,
    p_uncompressed_sha256);
END
$function$;

CREATE FUNCTION release.add_research_asset_dependency_to_draft(
  p_release_id uuid, p_asset_path text, p_dependency_path text
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
DECLARE v_dependency_sha core.sha256_hex;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);
  SELECT a.sha256 INTO STRICT v_dependency_sha
  FROM release.research_asset a
  WHERE a.research_release_id = p_release_id
    AND a.relative_path = p_dependency_path;
  INSERT INTO release.research_asset_dependency VALUES (
    p_release_id, p_asset_path, p_dependency_path, v_dependency_sha);
END
$function$;

CREATE FUNCTION release.add_research_membership_projection_to_draft(
  p_release_id uuid, p_corpus_version_id uuid,
  p_archive_object_id uuid, p_semantic_relation_id uuid,
  p_membership_role text, p_publication_layer release.publication_layer,
  p_metric_code text, p_count_eligibility release.count_eligibility,
  p_eligibility_reason_code text
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);
  INSERT INTO release.object_relation_membership_projection VALUES (
    p_release_id, p_corpus_version_id, p_archive_object_id,
    p_semantic_relation_id, p_membership_role, p_publication_layer,
    p_metric_code, p_count_eligibility, p_eligibility_reason_code);
END
$function$;

CREATE FUNCTION release.add_research_metric_eligibility_to_draft(
  p_release_id uuid, p_archive_object_id uuid, p_metric_code text,
  p_count_eligibility release.count_eligibility, p_reason_code text
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);
  INSERT INTO release.research_object_metric_eligibility VALUES (
    p_release_id, p_archive_object_id, p_metric_code,
    p_count_eligibility, p_reason_code);
END
$function$;

CREATE FUNCTION release.copy_research_folder_to_draft(
  p_release_id uuid, p_folder_id uuid
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);
  INSERT INTO release.research_folder_projection
  SELECT p_release_id, f.folder_id, f.folder_token, f.label
  FROM research.folder f WHERE f.folder_id = p_folder_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'FOLDER_NOT_FOUND';
  END IF;
END
$function$;

CREATE FUNCTION release.copy_trace_tree_to_draft(
  p_release_id uuid, p_corpus_version_id uuid, p_trace_tree_id uuid
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);
  INSERT INTO release.trace_tree_projection
  SELECT p_release_id, p_corpus_version_id, t.trace_tree_id,
    t.tree_token, t.label, t.evidence_item_id
  FROM research.trace_tree t
  WHERE t.trace_tree_id = p_trace_tree_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'TRACE_TREE_NOT_FOUND';
  END IF;
END
$function$;

CREATE FUNCTION release.copy_trace_branch_to_draft(
  p_release_id uuid, p_corpus_version_id uuid,
  p_trace_tree_id uuid, p_trace_branch_id uuid
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);
  INSERT INTO release.trace_branch_projection
  SELECT p_release_id, p_corpus_version_id, b.trace_tree_id,
    b.trace_branch_id, b.branch_token, b.label
  FROM research.trace_branch b
  WHERE b.trace_tree_id = p_trace_tree_id
    AND b.trace_branch_id = p_trace_branch_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'TRACE_BRANCH_NOT_FOUND';
  END IF;
END
$function$;

CREATE FUNCTION release.copy_trace_node_placement_to_draft(
  p_release_id uuid, p_corpus_version_id uuid, p_trace_node_id uuid,
  p_trace_tree_id uuid, p_trace_branch_id uuid,
  p_placement_role core.release_token
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);
  INSERT INTO release.trace_node_tree_placement
  SELECT p_release_id, p_corpus_version_id, m.trace_node_id,
    m.trace_tree_id, m.trace_branch_id, m.placement_role,
    m.evidence_item_id
  FROM research.trace_node_tree_membership m
  WHERE m.trace_node_id = p_trace_node_id
    AND m.trace_tree_id = p_trace_tree_id
    AND m.trace_branch_id = p_trace_branch_id
    AND m.placement_role = p_placement_role;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'TRACE_NODE_PLACEMENT_SOURCE_MISMATCH';
  END IF;
END
$function$;

CREATE FUNCTION release.add_trace_edge_placement_to_draft(
  p_release_id uuid, p_corpus_version_id uuid,
  p_subject_trace_node_id uuid, p_semantic_relation_id uuid,
  p_object_trace_node_id uuid, p_projection_role text,
  p_trace_tree_id uuid, p_trace_branch_id uuid,
  p_placement_role core.release_token
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);
  INSERT INTO release.trace_edge_tree_placement VALUES (
    p_release_id, p_corpus_version_id, p_subject_trace_node_id,
    p_semantic_relation_id, p_object_trace_node_id, p_projection_role,
    p_trace_tree_id, p_trace_branch_id, p_placement_role);
END
$function$;

CREATE OR REPLACE FUNCTION release.add_trace_edge_to_draft(
  p_release_id uuid, p_corpus_version_id uuid,
  p_subject_trace_node_id uuid, p_semantic_relation_id uuid,
  p_object_trace_node_id uuid, p_projection_role text
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);
  INSERT INTO release.trace_projection_edge VALUES (
    p_release_id, p_corpus_version_id, p_subject_trace_node_id,
    p_semantic_relation_id, p_object_trace_node_id, p_projection_role,
    release.trace_edge_generation_key(
      p_release_id, p_corpus_version_id, p_subject_trace_node_id,
      p_semantic_relation_id, p_object_trace_node_id, p_projection_role));
END
$function$;

RESET ROLE;
