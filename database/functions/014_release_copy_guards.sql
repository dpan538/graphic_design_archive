\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE FUNCTION release.enforce_claim_evidence_copy_source()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE e provenance.evidence_item%ROWTYPE;
BEGIN
  SELECT * INTO STRICT e
  FROM provenance.evidence_item x
  WHERE x.evidence_item_id = NEW.evidence_item_id;
  IF NEW.source_asset_id IS DISTINCT FROM e.source_asset_id
    OR NEW.source_version_id IS DISTINCT FROM e.source_version_id
    OR NEW.source_record_id IS DISTINCT FROM e.source_record_id
    OR NEW.locator_scheme IS DISTINCT FROM COALESCE(e.locator_scheme, 'none')
    OR NEW.locator_value IS DISTINCT FROM e.internal_locator
    OR NEW.span_start IS DISTINCT FROM e.span_start
    OR NEW.span_end IS DISTINCT FROM e.span_end
    OR NEW.content_sha256 IS DISTINCT FROM e.content_sha256
    OR NEW.stable_citation IS DISTINCT FROM e.stable_citation
    OR NEW.evidence_snapshot_sha256 IS DISTINCT FROM
      release.evidence_snapshot_sha(e.evidence_item_id) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'RESEARCH_CLAIM_EVIDENCE_COPY_SOURCE_MISMATCH';
  END IF;
  RETURN NEW;
END
$function$;

CREATE TRIGGER research_claim_evidence_copy_source
BEFORE INSERT OR UPDATE ON release.research_release_claim_evidence
FOR EACH ROW EXECUTE FUNCTION release.enforce_claim_evidence_copy_source();

CREATE FUNCTION release.enforce_relation_evidence_copy_source()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE e provenance.evidence_item%ROWTYPE;
BEGIN
  SELECT * INTO STRICT e
  FROM provenance.evidence_item x
  WHERE x.evidence_item_id = NEW.evidence_item_id;
  IF NEW.source_asset_id IS DISTINCT FROM e.source_asset_id
    OR NEW.source_version_id IS DISTINCT FROM e.source_version_id
    OR NEW.source_record_id IS DISTINCT FROM e.source_record_id
    OR NEW.locator_value IS DISTINCT FROM e.internal_locator
    OR NEW.content_sha256 IS DISTINCT FROM e.content_sha256
    OR NEW.stable_citation IS DISTINCT FROM e.stable_citation
    OR NEW.evidence_snapshot_sha256 IS DISTINCT FROM
      release.evidence_snapshot_sha(e.evidence_item_id) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'RESEARCH_RELATION_EVIDENCE_COPY_SOURCE_MISMATCH';
  END IF;
  RETURN NEW;
END
$function$;

CREATE TRIGGER research_relation_evidence_copy_source
BEFORE INSERT OR UPDATE ON release.research_release_relation_evidence
FOR EACH ROW EXECUTE FUNCTION release.enforce_relation_evidence_copy_source();

CREATE FUNCTION release.enforce_analysis_run_copy_source()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE a research.analysis_run%ROWTYPE;
BEGIN
  SELECT * INTO STRICT a
  FROM research.analysis_run x
  WHERE x.analysis_run_id = NEW.analysis_run_id;
  IF NEW.method_version IS DISTINCT FROM a.method_version
    OR NEW.software_sha256 IS DISTINCT FROM a.software_sha256
    OR NEW.parameters_sha256 IS DISTINCT FROM a.parameters_sha256
    OR NEW.input_research_release_id IS DISTINCT FROM a.input_release_id
    OR NEW.input_research_manifest_sha256 IS DISTINCT FROM a.input_manifest_sha256
    OR NEW.input_corpus_version_id IS DISTINCT FROM a.input_corpus_version_id
    OR NEW.input_corpus_policy_sha256 IS DISTINCT FROM a.input_corpus_policy_sha256
    OR NEW.score_value IS DISTINCT FROM a.score_value
    OR NEW.score_unit IS DISTINCT FROM a.score_unit
    OR NEW.uncertainty_lower IS DISTINCT FROM a.uncertainty_lower
    OR NEW.uncertainty_upper IS DISTINCT FROM a.uncertainty_upper
    OR NEW.threshold_value IS DISTINCT FROM a.threshold_value
    OR NEW.threshold_unit IS DISTINCT FROM a.threshold_unit
    OR NEW.output_sha256 IS DISTINCT FROM a.output_sha256
    OR NEW.run_snapshot_sha256 IS DISTINCT FROM
      release.analysis_run_snapshot_sha(a.analysis_run_id) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'RESEARCH_ANALYSIS_RUN_COPY_SOURCE_MISMATCH';
  END IF;
  RETURN NEW;
END
$function$;

CREATE TRIGGER research_analysis_run_copy_source
BEFORE INSERT OR UPDATE ON release.research_release_analysis_run
FOR EACH ROW EXECUTE FUNCTION release.enforce_analysis_run_copy_source();

CREATE FUNCTION release.enforce_folder_copy_source()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM research.folder f
    WHERE f.folder_id = NEW.folder_id
      AND f.folder_token = NEW.folder_token
      AND f.label = NEW.label
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'RESEARCH_FOLDER_COPY_SOURCE_MISMATCH';
  END IF;
  RETURN NEW;
END
$function$;

CREATE TRIGGER research_folder_copy_source
BEFORE INSERT OR UPDATE ON release.research_folder_projection
FOR EACH ROW EXECUTE FUNCTION release.enforce_folder_copy_source();
CREATE TRIGGER guard_research_folder_projection
BEFORE INSERT OR UPDATE OR DELETE ON release.research_folder_projection
FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();

CREATE FUNCTION release.enforce_legacy_resolution_copy_source()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM core.legacy_identity_resolution r
    JOIN core.legacy_identity i ON i.legacy_identity_id = r.legacy_identity_id
    WHERE r.legacy_identity_resolution_id = NEW.legacy_identity_resolution_id
      AND r.legacy_identity_id = NEW.legacy_identity_id
      AND i.identity_kind = NEW.identity_kind
      AND i.namespace = NEW.namespace
      AND i.legacy_id = NEW.legacy_id
      AND r.resolution_state = NEW.resolution_state
      AND r.target_archive_object_id IS NOT DISTINCT FROM
        NEW.target_archive_object_id
      AND r.target_source_record_id IS NOT DISTINCT FROM
        NEW.target_source_record_id
      AND r.target_trace_node_id IS NOT DISTINCT FROM NEW.target_trace_node_id
      AND r.target_folder_id IS NOT DISTINCT FROM NEW.target_folder_id
      AND r.target_trace_edge_corpus_version_id IS NOT DISTINCT FROM
        NEW.target_trace_edge_corpus_version_id
      AND r.target_trace_edge_subject_node_id IS NOT DISTINCT FROM
        NEW.target_trace_edge_subject_node_id
      AND r.target_trace_edge_relation_id IS NOT DISTINCT FROM
        NEW.target_trace_edge_relation_id
      AND r.target_trace_edge_object_node_id IS NOT DISTINCT FROM
        NEW.target_trace_edge_object_node_id
      AND r.target_trace_edge_projection_role IS NOT DISTINCT FROM
        NEW.target_trace_edge_projection_role
      AND r.reason_code = NEW.reason_code
      AND r.effective_from = NEW.effective_from
      AND r.effective_release_id = NEW.research_release_id
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'RESEARCH_LEGACY_RESOLUTION_COPY_SOURCE_MISMATCH';
  END IF;
  RETURN NEW;
END
$function$;

CREATE TRIGGER research_legacy_resolution_copy_source
BEFORE INSERT OR UPDATE ON release.research_legacy_identity_resolution
FOR EACH ROW EXECUTE FUNCTION release.enforce_legacy_resolution_copy_source();

CREATE FUNCTION release.enforce_legacy_split_copy_source()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM core.legacy_identity_split_successor s
    JOIN core.archive_object o
      ON o.archive_object_id = s.successor_archive_object_id
    WHERE s.legacy_identity_resolution_id = NEW.legacy_identity_resolution_id
      AND s.successor_ordinal + 1 = NEW.successor_ordinal
      AND s.successor_archive_object_id = NEW.successor_archive_object_id
      AND o.object_urn = NEW.successor_object_urn
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'RESEARCH_LEGACY_SPLIT_COPY_SOURCE_MISMATCH';
  END IF;
  RETURN NEW;
END
$function$;

CREATE TRIGGER research_legacy_split_copy_source
BEFORE INSERT OR UPDATE ON release.research_legacy_identity_split_successor
FOR EACH ROW EXECUTE FUNCTION release.enforce_legacy_split_copy_source();

CREATE FUNCTION release.copy_legacy_identity_resolution_to_draft(
  p_release_id uuid, p_legacy_identity_resolution_id uuid,
  p_target_trace_node_corpus_version_id uuid
)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  PERFORM release.require_research_draft(p_release_id);

  IF EXISTS (
    SELECT 1
    FROM core.legacy_identity_split_successor s
    WHERE s.legacy_identity_resolution_id =
        p_legacy_identity_resolution_id
      AND NOT EXISTS (
        SELECT 1
        FROM release.research_release_object o
        WHERE o.research_release_id = p_release_id
          AND o.archive_object_id = s.successor_archive_object_id
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'LEGACY_SPLIT_SUCCESSOR_NOT_IN_RELEASE_OBJECT_SET';
  END IF;

  INSERT INTO release.research_legacy_identity_resolution (
    research_release_id, legacy_identity_id,
    legacy_identity_resolution_id, identity_kind, namespace, legacy_id,
    resolution_state, target_archive_object_id, target_source_record_id,
    target_trace_node_id, target_folder_id,
    target_trace_edge_corpus_version_id,
    target_trace_edge_subject_node_id, target_trace_edge_relation_id,
    target_trace_edge_object_node_id, target_trace_edge_projection_role,
    reason_code, effective_from, target_trace_node_corpus_version_id
  )
  SELECT p_release_id, i.legacy_identity_id,
    r.legacy_identity_resolution_id, i.identity_kind, i.namespace,
    i.legacy_id, r.resolution_state, r.target_archive_object_id,
    r.target_source_record_id, r.target_trace_node_id,
    r.target_folder_id, r.target_trace_edge_corpus_version_id,
    r.target_trace_edge_subject_node_id, r.target_trace_edge_relation_id,
    r.target_trace_edge_object_node_id,
    r.target_trace_edge_projection_role, r.reason_code,
    r.effective_from, p_target_trace_node_corpus_version_id
  FROM core.legacy_identity_resolution r
  JOIN core.legacy_identity i ON i.legacy_identity_id = r.legacy_identity_id
  WHERE r.legacy_identity_resolution_id = p_legacy_identity_resolution_id
    AND r.effective_release_id = p_release_id
    AND ((r.target_trace_node_id IS NULL
          AND p_target_trace_node_corpus_version_id IS NULL)
      OR (r.target_trace_node_id IS NOT NULL
          AND p_target_trace_node_corpus_version_id IS NOT NULL));
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'LEGACY_RESOLUTION_NOT_EFFECTIVE_FOR_RELEASE';
  END IF;

  INSERT INTO release.research_legacy_identity_split_successor (
    research_release_id, legacy_identity_resolution_id,
    successor_ordinal, successor_archive_object_id, successor_object_urn
  )
  SELECT p_release_id, s.legacy_identity_resolution_id,
    s.successor_ordinal + 1, s.successor_archive_object_id, o.object_urn
  FROM core.legacy_identity_split_successor s
  JOIN release.research_release_object o
    ON o.research_release_id = p_release_id
   AND o.archive_object_id = s.successor_archive_object_id
  WHERE s.legacy_identity_resolution_id = p_legacy_identity_resolution_id;
END
$function$;

RESET ROLE;
