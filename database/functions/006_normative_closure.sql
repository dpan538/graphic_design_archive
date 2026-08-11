\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

-- RFC 8785 encoder for the deliberately restricted manifest value domain.
-- Manifests contain objects, arrays, strings, booleans, null, and safe-range
-- integers only.  Any other numeric value fails closed rather than silently
-- claiming JCS conformance.
CREATE FUNCTION release.jcs_text(p_value jsonb)
RETURNS text
LANGUAGE plpgsql IMMUTABLE STRICT
SET search_path = pg_catalog
AS $function$
DECLARE
  v_type text := jsonb_typeof(p_value);
  v_result text;
  v_key text;
  v_item jsonb;
  v_first boolean := true;
  v_number numeric;
BEGIN
  CASE v_type
    WHEN 'null' THEN RETURN 'null';
    WHEN 'boolean' THEN RETURN p_value::text;
    WHEN 'string' THEN RETURN to_jsonb(p_value #>> '{}')::text;
    WHEN 'number' THEN
      v_number := (p_value::text)::numeric;
      IF v_number <> trunc(v_number)
        OR abs(v_number) > 9007199254740991::numeric THEN
        RAISE EXCEPTION USING ERRCODE = '22023',
          MESSAGE = 'JCS_MANIFEST_NUMBER_OUTSIDE_SAFE_INTEGER_DOMAIN';
      END IF;
      RETURN trunc(v_number)::text;
    WHEN 'array' THEN
      v_result := '[';
      FOR v_item IN SELECT value FROM jsonb_array_elements(p_value)
      LOOP
        IF NOT v_first THEN v_result := v_result || ','; END IF;
        v_result := v_result || release.jcs_text(v_item);
        v_first := false;
      END LOOP;
      RETURN v_result || ']';
    WHEN 'object' THEN
      v_result := '{';
      FOR v_key, v_item IN
        SELECT key, value FROM jsonb_each(p_value) ORDER BY key COLLATE "C"
      LOOP
        IF NOT v_first THEN v_result := v_result || ','; END IF;
        v_result := v_result || to_jsonb(v_key)::text || ':'
          || release.jcs_text(v_item);
        v_first := false;
      END LOOP;
      RETURN v_result || '}';
    ELSE
      RAISE EXCEPTION USING ERRCODE = '22023',
        MESSAGE = 'JCS_MANIFEST_UNSUPPORTED_JSON_TYPE';
  END CASE;
END
$function$;

CREATE FUNCTION release.jcs_bytes(p_value jsonb)
RETURNS bytea
LANGUAGE sql IMMUTABLE STRICT
SET search_path = pg_catalog
RETURN convert_to(release.jcs_text(p_value), 'UTF8');

-- RFC 8785 permits finite JSON numbers, but PostgreSQL's jsonb text rendering
-- is not itself an RFC 8785 number encoder.  Analysis measurements therefore
-- enter the restricted manifest domain as canonical decimal strings.  This
-- preserves arbitrary-precision numeric values without session, locale, or
-- floating-point drift while keeping release.jcs_text deliberately small.
CREATE FUNCTION release.canonical_decimal_text(p_value numeric)
RETURNS text
LANGUAGE plpgsql IMMUTABLE STRICT
SET search_path = pg_catalog
AS $function$
DECLARE
  v_text text := trim_scale(p_value)::text;
BEGIN
  IF v_text IN ('NaN', 'Infinity', '-Infinity')
    OR v_text ~ '[eE]' THEN
    RAISE EXCEPTION USING ERRCODE = '22023',
      MESSAGE = 'MANIFEST_DECIMAL_MUST_BE_FINITE_PLAIN_NOTATION';
  END IF;
  IF v_text = '-0' THEN
    RETURN '0';
  END IF;
  RETURN v_text;
END
$function$;

CREATE FUNCTION release.analysis_run_manifest_json(p_row jsonb)
RETURNS jsonb
LANGUAGE sql IMMUTABLE STRICT
SET search_path = pg_catalog
RETURN (p_row - ARRAY[
    'score_value', 'uncertainty_lower', 'uncertainty_upper',
    'threshold_value'
  ]) || jsonb_build_object(
    'score_value', release.canonical_decimal_text(
      (p_row ->> 'score_value')::numeric),
    'uncertainty_lower', release.canonical_decimal_text(
      (p_row ->> 'uncertainty_lower')::numeric),
    'uncertainty_upper', release.canonical_decimal_text(
      (p_row ->> 'uncertainty_upper')::numeric),
    'threshold_value', release.canonical_decimal_text(
      (p_row ->> 'threshold_value')::numeric)
  );

CREATE OR REPLACE FUNCTION release.canonical_jsonb_sha256(p_value jsonb)
RETURNS core.sha256_hex
LANGUAGE sql IMMUTABLE STRICT
SET search_path = pg_catalog
RETURN encode(sha256(release.jcs_bytes(p_value)), 'hex')::core.sha256_hex;

CREATE FUNCTION rights.object_visual_reference_decision_sha(
  p_decision_id uuid
)
RETURNS core.sha256_hex
LANGUAGE sql STABLE STRICT
SET search_path = pg_catalog
SET TimeZone = 'UTC'
RETURN release.canonical_jsonb_sha256((
  SELECT to_jsonb(d)
  FROM rights.object_visual_reference_review_decision d
  WHERE d.object_visual_reference_review_decision_id = p_decision_id
));

CREATE FUNCTION rights.object_visual_reference_evidence_sha(
  p_evidence_item_id uuid
)
RETURNS core.sha256_hex
LANGUAGE sql STABLE STRICT
SET search_path = pg_catalog
SET TimeZone = 'UTC'
RETURN release.canonical_jsonb_sha256((
  SELECT to_jsonb(e)
  FROM provenance.evidence_item e
  WHERE e.evidence_item_id = p_evidence_item_id
));

CREATE FUNCTION rights.object_visual_reference_snapshot_sha(
  p_bridge_id uuid,
  p_compatible_research_release_id uuid,
  p_compatible_research_manifest_sha256 core.sha256_hex
)
RETURNS core.sha256_hex
LANGUAGE sql STABLE STRICT
SET search_path = pg_catalog
SET TimeZone = 'UTC'
RETURN (
  SELECT release.canonical_jsonb_sha256(jsonb_build_object(
    'objectVisualReferenceId', b.object_visual_reference_id,
    'compatibleResearchReleaseId', p_compatible_research_release_id,
    'compatibleResearchManifestSha256',
      p_compatible_research_manifest_sha256,
    'archiveObjectId', b.archive_object_id,
    'externalVisualReferenceId', b.external_visual_reference_id,
    'referenceRole', b.reference_role,
    'ordinal', b.ordinal,
    'acceptanceState', b.acceptance_state,
    'evidenceItemId', b.evidence_item_id,
    'evidenceSnapshotSha256',
      rights.object_visual_reference_evidence_sha(b.evidence_item_id),
    'reviewDecisionId', d.object_visual_reference_review_decision_id,
    'decisionSnapshotSha256',
      rights.object_visual_reference_decision_sha(
        d.object_visual_reference_review_decision_id)
  ))
  FROM rights.object_visual_reference b
  JOIN rights.object_visual_reference_review_decision d
    ON d.object_visual_reference_id = b.object_visual_reference_id
   AND d.outcome = 'accept'
   AND d.evidence_item_id = b.evidence_item_id
  WHERE b.object_visual_reference_id = p_bridge_id
    AND b.acceptance_state = 'accepted'
    AND NOT EXISTS (
      SELECT 1
      FROM rights.object_visual_reference_review_decision newer
      WHERE newer.supersedes_decision_id =
        d.object_visual_reference_review_decision_id
    )
);

CREATE FUNCTION release.assert_validation_profile_complete(
  p_profile_id uuid, p_boundary release.boundary_kind
)
RETURNS void
LANGUAGE plpgsql STABLE
SET search_path = pg_catalog
AS $function$
DECLARE
  v_missing integer;
  v_extra integer;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM release.validation_profile p
    WHERE p.validation_profile_id = p_profile_id
      AND p.boundary_kind = p_boundary
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'VALIDATION_PROFILE_BOUNDARY_MISMATCH';
  END IF;

  IF p_boundary = 'research' THEN
    SELECT count(*) INTO v_missing
    FROM unnest(ARRAY[
      'research_frozen_asset_authority',
      'research_migration_query_identity',
      'research_population_and_count_parity',
      'research_corpus_missingness_concentration',
      'research_fk_orphan_integrity',
      'research_predicate_relation_epistemic_registry',
      'research_claim_projection_eligibility',
      'research_unknown_relation_isolation',
      'research_projection_fingerprint',
      'research_deterministic_asset_inventory',
      'research_role_grant_security'
    ]::release.validation_receipt_kind[]) expected(kind)
    WHERE NOT EXISTS (
      SELECT 1 FROM release.validation_profile_requirement r
      WHERE r.validation_profile_id = p_profile_id
        AND r.receipt_kind = expected.kind);
    SELECT count(*) INTO v_extra
    FROM release.validation_profile_requirement r
    WHERE r.validation_profile_id = p_profile_id
      AND r.receipt_kind::text !~ '^research_';
  ELSE
    SELECT count(*) INTO v_missing
    FROM unnest(ARRAY[
      'visual_legacy_disposition',
      'visual_reference_bridge_provider_locator_identity',
      'visual_rights_policy_delivery_health_takedown',
      'visual_attribution_review_due',
      'visual_held_pixel_non_disclosure',
      'visual_research_compatibility',
      'visual_projection_fingerprint',
      'visual_deterministic_asset_inventory',
      'visual_role_grant_security'
    ]::release.validation_receipt_kind[]) expected(kind)
    WHERE NOT EXISTS (
      SELECT 1 FROM release.validation_profile_requirement r
      WHERE r.validation_profile_id = p_profile_id
        AND r.receipt_kind = expected.kind);
    SELECT count(*) INTO v_extra
    FROM release.validation_profile_requirement r
    WHERE r.validation_profile_id = p_profile_id
      AND r.receipt_kind::text !~ '^visual_';
  END IF;
  IF v_missing <> 0 OR v_extra <> 0 THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'VALIDATION_PROFILE_REQUIRED_SET_INCOMPLETE';
  END IF;
END
$function$;

CREATE FUNCTION release.assert_required_receipts_complete(
  p_boundary release.boundary_kind, p_release_id uuid
)
RETURNS void
LANGUAGE plpgsql STABLE
SET search_path = pg_catalog
AS $function$
DECLARE v_profile_id uuid; v_missing integer;
BEGIN
  IF p_boundary = 'research' THEN
    SELECT validation_profile_id INTO v_profile_id
    FROM release.research_release WHERE research_release_id = p_release_id;
    SELECT count(*) INTO v_missing
    FROM release.validation_profile_requirement req
    WHERE req.validation_profile_id = v_profile_id
      AND NOT EXISTS (
        SELECT 1 FROM release.research_validation_receipt r
        WHERE r.research_release_id = p_release_id
          AND r.receipt_kind = req.receipt_kind
          AND r.validation_result = 'pass'
          AND r.candidate_fingerprint = (
            SELECT candidate_fingerprint FROM release.research_release
            WHERE research_release_id = p_release_id));
  ELSE
    SELECT validation_profile_id INTO v_profile_id
    FROM release.visual_registry_release
    WHERE visual_registry_release_id = p_release_id;
    SELECT count(*) INTO v_missing
    FROM release.validation_profile_requirement req
    WHERE req.validation_profile_id = v_profile_id
      AND NOT EXISTS (
        SELECT 1 FROM release.visual_validation_receipt r
        WHERE r.visual_registry_release_id = p_release_id
          AND r.receipt_kind = req.receipt_kind
          AND r.validation_result = 'pass'
          AND r.candidate_fingerprint = (
            SELECT candidate_fingerprint FROM release.visual_registry_release
            WHERE visual_registry_release_id = p_release_id));
  END IF;
  IF v_missing <> 0 THEN
    RAISE EXCEPTION USING ERRCODE = '55000',
      MESSAGE = 'REQUIRED_VALIDATION_RECEIPT_SET_INCOMPLETE';
  END IF;
END
$function$;

-- New typed value subtypes participate in the exact-one assertion shape.
CREATE TRIGGER assertion_value_folder_append_only
BEFORE UPDATE OR DELETE ON provenance.assertion_value_folder
FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assertion_value_representation_append_only
BEFORE UPDATE OR DELETE ON provenance.assertion_value_representation
FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assertion_value_identity_append_only
BEFORE UPDATE OR DELETE ON provenance.assertion_value_identity_resolution
FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();

CREATE OR REPLACE FUNCTION provenance.enforce_assertion_shape()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_id uuid := COALESCE(NEW.assertion_id, OLD.assertion_id);
  v_subject_kind provenance.assertion_subject_kind;
  v_value_kind provenance.assertion_value_kind;
  v_subject_count integer;
  v_value_count integer;
BEGIN
  SELECT a.subject_kind, a.value_kind INTO v_subject_kind, v_value_kind
  FROM provenance.assertion a WHERE a.assertion_id = v_id;
  IF NOT FOUND THEN RETURN NULL; END IF;
  SELECT
    (SELECT count(*) FROM provenance.assertion_subject_entity x WHERE x.assertion_id=v_id)
    + (SELECT count(*) FROM provenance.assertion_subject_source_record x WHERE x.assertion_id=v_id)
    + (SELECT count(*) FROM provenance.assertion_subject_trace_node x WHERE x.assertion_id=v_id)
    + (SELECT count(*) FROM provenance.assertion_subject_representation x WHERE x.assertion_id=v_id),
    (SELECT count(*) FROM provenance.assertion_value_literal x WHERE x.assertion_id=v_id)
    + (SELECT count(*) FROM provenance.assertion_value_entity x WHERE x.assertion_id=v_id)
    + (SELECT count(*) FROM provenance.assertion_value_source_record x WHERE x.assertion_id=v_id)
    + (SELECT count(*) FROM provenance.assertion_value_trace_node x WHERE x.assertion_id=v_id)
    + (SELECT count(*) FROM provenance.assertion_value_folder x WHERE x.assertion_id=v_id)
    + (SELECT count(*) FROM provenance.assertion_value_representation x WHERE x.assertion_id=v_id)
    + (SELECT count(*) FROM provenance.assertion_value_identity_resolution x WHERE x.assertion_id=v_id)
  INTO v_subject_count, v_value_count;
  IF v_subject_count <> 1 OR NOT (CASE v_subject_kind
    WHEN 'entity' THEN EXISTS (SELECT 1 FROM provenance.assertion_subject_entity x WHERE x.assertion_id=v_id)
    WHEN 'source_record' THEN EXISTS (SELECT 1 FROM provenance.assertion_subject_source_record x WHERE x.assertion_id=v_id)
    WHEN 'trace_node' THEN EXISTS (SELECT 1 FROM provenance.assertion_subject_trace_node x WHERE x.assertion_id=v_id)
    WHEN 'digital_representation' THEN EXISTS (SELECT 1 FROM provenance.assertion_subject_representation x WHERE x.assertion_id=v_id)
    ELSE false END) THEN
    RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='ASSERTION_SUBJECT_EXACTLY_ONE_VIOLATION';
  END IF;
  IF v_value_count <> 1 OR NOT (CASE v_value_kind
    WHEN 'literal' THEN EXISTS (SELECT 1 FROM provenance.assertion_value_literal x WHERE x.assertion_id=v_id)
    WHEN 'entity' THEN EXISTS (SELECT 1 FROM provenance.assertion_value_entity x WHERE x.assertion_id=v_id)
    WHEN 'source_record' THEN EXISTS (SELECT 1 FROM provenance.assertion_value_source_record x WHERE x.assertion_id=v_id)
    WHEN 'trace_node' THEN EXISTS (SELECT 1 FROM provenance.assertion_value_trace_node x WHERE x.assertion_id=v_id)
    WHEN 'folder' THEN EXISTS (SELECT 1 FROM provenance.assertion_value_folder x WHERE x.assertion_id=v_id)
    WHEN 'digital_representation' THEN EXISTS (SELECT 1 FROM provenance.assertion_value_representation x WHERE x.assertion_id=v_id)
    WHEN 'legacy_identity_resolution' THEN EXISTS (SELECT 1 FROM provenance.assertion_value_identity_resolution x WHERE x.assertion_id=v_id)
    ELSE false END) THEN
    RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='ASSERTION_VALUE_EXACTLY_ONE_VIOLATION';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER assertion_shape_from_folder_value
AFTER INSERT OR UPDATE OR DELETE ON provenance.assertion_value_folder
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION provenance.enforce_assertion_shape();
CREATE CONSTRAINT TRIGGER assertion_shape_from_representation_value
AFTER INSERT OR UPDATE OR DELETE ON provenance.assertion_value_representation
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION provenance.enforce_assertion_shape();
CREATE CONSTRAINT TRIGGER assertion_shape_from_identity_value
AFTER INSERT OR UPDATE OR DELETE ON provenance.assertion_value_identity_resolution
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION provenance.enforce_assertion_shape();

CREATE OR REPLACE FUNCTION provenance.enforce_accepted_assertion()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := COALESCE(to_jsonb(NEW), to_jsonb(OLD));
  v_id uuid := (v_row ->> 'assertion_id')::uuid;
BEGIN
  IF v_id IS NULL AND v_row ? 'assertion_review_decision_id' THEN
    SELECT d.assertion_id INTO v_id
    FROM provenance.assertion_review_decision d
    WHERE d.assertion_review_decision_id =
      (v_row ->> 'assertion_review_decision_id')::uuid;
  END IF;
  IF EXISTS (
    SELECT 1 FROM provenance.assertion a
    JOIN provenance.assertion_predicate p
      ON p.assertion_predicate_id=a.assertion_predicate_id
    JOIN provenance.predicate_evidence_profile ep
      ON ep.predicate_evidence_profile_id=p.predicate_evidence_profile_id
    WHERE a.assertion_id=v_id AND a.status='accepted'
      AND (NOT p.active OR p.subject_domain<>a.subject_kind
        OR p.value_range<>a.value_kind
        OR (ep.requires_supporting_evidence AND (
          SELECT count(*) FROM provenance.assertion_evidence ae
          WHERE ae.assertion_id=a.assertion_id
            AND ae.evidence_role='supports') < ep.minimum_support_count
        OR (ep.requires_review_decision AND NOT EXISTS (
          SELECT 1 FROM provenance.assertion_review_decision d
          WHERE d.assertion_id=a.assertion_id AND d.outcome='accept'
            AND NOT EXISTS (SELECT 1 FROM provenance.assertion_review_decision n
              WHERE n.supersedes_decision_id=d.assertion_review_decision_id)
            AND EXISTS (SELECT 1 FROM provenance.assertion_decision_evidence de
              WHERE de.assertion_review_decision_id=d.assertion_review_decision_id
                AND de.evidence_role='supports')))))
  ) THEN
    RAISE EXCEPTION USING ERRCODE='23514',
      MESSAGE='ACCEPTED_ASSERTION_PREDICATE_DOMAIN_RANGE_OR_EVIDENCE_VIOLATION';
  END IF;
  RETURN NULL;
END
$function$;

CREATE FUNCTION provenance.enforce_predicate_registry_fanout()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog
AS $function$
DECLARE r record;
BEGIN
  FOR r IN SELECT assertion_id FROM provenance.assertion
    WHERE assertion_predicate_id=NEW.assertion_predicate_id
  LOOP
    IF EXISTS (SELECT 1 FROM provenance.assertion a
      WHERE a.assertion_id=r.assertion_id AND a.status='accepted'
      AND (NOT NEW.active OR NEW.subject_domain<>a.subject_kind
          OR NEW.value_range<>a.value_kind
          OR OLD.registry_version IS DISTINCT FROM NEW.registry_version
          OR OLD.predicate_evidence_profile_id IS DISTINCT FROM
            NEW.predicate_evidence_profile_id)) THEN
      RAISE EXCEPTION USING ERRCODE='23514',
        MESSAGE='PREDICATE_REGISTRY_CHANGE_INVALIDATES_ACCEPTED_ASSERTION';
    END IF;
  END LOOP;
  RETURN NULL;
END
$function$;
CREATE CONSTRAINT TRIGGER predicate_registry_fanout
AFTER UPDATE ON provenance.assertion_predicate
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION provenance.enforce_predicate_registry_fanout();

CREATE FUNCTION provenance.assignment_assertion_matches(
  p_assignment_id uuid, p_assertion_id uuid
)
RETURNS boolean
LANGUAGE plpgsql STABLE
SET search_path=pg_catalog
AS $function$
DECLARE v_kind provenance.assignment_kind; v_match boolean := false;
BEGIN
  SELECT assignment_kind INTO v_kind FROM provenance.canonical_assignment
  WHERE canonical_assignment_id=p_assignment_id;
  IF NOT EXISTS (
    SELECT 1 FROM provenance.assertion a
    JOIN provenance.assignment_predicate_compatibility c
      ON c.assertion_predicate_id=a.assertion_predicate_id
      AND c.assignment_kind=v_kind
    WHERE a.assertion_id=p_assertion_id AND a.status='accepted'
  ) THEN RETURN false; END IF;
  CASE v_kind
    WHEN 'entity_name' THEN SELECT EXISTS (
      SELECT 1 FROM provenance.assignment_entity_name x
      JOIN provenance.assertion_subject_entity s ON s.assertion_id=p_assertion_id AND s.entity_id=x.entity_id
      JOIN provenance.assertion_value_literal v ON v.assertion_id=p_assertion_id AND v.field_literal_id=x.field_literal_id
      WHERE x.canonical_assignment_id=p_assignment_id) INTO v_match;
    WHEN 'object_source_record' THEN SELECT EXISTS (
      SELECT 1 FROM provenance.assignment_object_source_record x
      JOIN provenance.assertion_subject_entity s ON s.assertion_id=p_assertion_id AND s.entity_id=x.archive_object_id
      JOIN provenance.assertion_value_source_record v ON v.assertion_id=p_assertion_id AND v.source_record_id=x.source_record_id
      WHERE x.canonical_assignment_id=p_assignment_id) INTO v_match;
    WHEN 'object_agent_credit' THEN SELECT EXISTS (
      SELECT 1 FROM provenance.assignment_object_agent_credit x
      JOIN provenance.assertion_subject_entity s ON s.assertion_id=p_assertion_id AND s.entity_id=x.archive_object_id
      JOIN provenance.assertion_value_entity v ON v.assertion_id=p_assertion_id AND v.entity_id=x.agent_id
      WHERE x.canonical_assignment_id=p_assignment_id) INTO v_match;
    WHEN 'object_medium' THEN SELECT EXISTS (
      SELECT 1 FROM provenance.assignment_object_medium x JOIN provenance.assertion_subject_entity s ON s.assertion_id=p_assertion_id AND s.entity_id=x.archive_object_id JOIN provenance.assertion_value_entity v ON v.assertion_id=p_assertion_id AND v.entity_id=x.medium_concept_id WHERE x.canonical_assignment_id=p_assignment_id) INTO v_match;
    WHEN 'object_type' THEN SELECT EXISTS (
      SELECT 1 FROM provenance.assignment_object_type x JOIN provenance.assertion_subject_entity s ON s.assertion_id=p_assertion_id AND s.entity_id=x.archive_object_id JOIN provenance.assertion_value_entity v ON v.assertion_id=p_assertion_id AND v.entity_id=x.type_concept_id WHERE x.canonical_assignment_id=p_assignment_id) INTO v_match;
    WHEN 'object_subject' THEN SELECT EXISTS (
      SELECT 1 FROM provenance.assignment_object_subject x JOIN provenance.assertion_subject_entity s ON s.assertion_id=p_assertion_id AND s.entity_id=x.archive_object_id JOIN provenance.assertion_value_entity v ON v.assertion_id=p_assertion_id AND v.entity_id=x.subject_concept_id WHERE x.canonical_assignment_id=p_assignment_id) INTO v_match;
    WHEN 'object_collection' THEN SELECT EXISTS (
      SELECT 1 FROM provenance.assignment_object_collection x JOIN provenance.assertion_subject_entity s ON s.assertion_id=p_assertion_id AND s.entity_id=x.archive_object_id JOIN provenance.assertion_value_entity v ON v.assertion_id=p_assertion_id AND v.entity_id=x.collection_id WHERE x.canonical_assignment_id=p_assignment_id) INTO v_match;
    WHEN 'object_temporal' THEN SELECT EXISTS (
      SELECT 1 FROM provenance.assignment_object_temporal x JOIN provenance.assertion_subject_entity s ON s.assertion_id=p_assertion_id AND s.entity_id=x.archive_object_id JOIN provenance.assertion_value_entity v ON v.assertion_id=p_assertion_id AND v.entity_id=x.temporal_extent_id WHERE x.canonical_assignment_id=p_assignment_id) INTO v_match;
    WHEN 'object_place' THEN SELECT EXISTS (
      SELECT 1 FROM provenance.assignment_object_place x JOIN provenance.assertion_subject_entity s ON s.assertion_id=p_assertion_id AND s.entity_id=x.archive_object_id JOIN provenance.assertion_value_entity v ON v.assertion_id=p_assertion_id AND v.entity_id=x.place_id WHERE x.canonical_assignment_id=p_assignment_id) INTO v_match;
    WHEN 'folder_membership' THEN SELECT EXISTS (
      SELECT 1 FROM provenance.assignment_folder_membership x JOIN provenance.assertion_subject_entity s ON s.assertion_id=p_assertion_id AND s.entity_id=x.archive_object_id JOIN provenance.assertion_value_folder v ON v.assertion_id=p_assertion_id AND v.folder_id=x.folder_id WHERE x.canonical_assignment_id=p_assignment_id) INTO v_match;
    WHEN 'object_tree_membership' THEN SELECT EXISTS (
      SELECT 1 FROM provenance.assignment_object_tree_membership x JOIN provenance.assertion_subject_entity s ON s.assertion_id=p_assertion_id AND s.entity_id=x.archive_object_id JOIN provenance.assertion_value_trace_node v ON v.assertion_id=p_assertion_id AND v.trace_node_id=x.trace_node_id WHERE x.canonical_assignment_id=p_assignment_id) INTO v_match;
    WHEN 'object_representation' THEN SELECT EXISTS (
      SELECT 1 FROM provenance.assignment_object_representation x JOIN provenance.assertion_subject_entity s ON s.assertion_id=p_assertion_id AND s.entity_id=x.archive_object_id JOIN provenance.assertion_value_representation v ON v.assertion_id=p_assertion_id AND v.digital_representation_id=x.digital_representation_id WHERE x.canonical_assignment_id=p_assignment_id) INTO v_match;
    WHEN 'identity_resolution' THEN SELECT EXISTS (
      SELECT 1 FROM provenance.assignment_identity_resolution x JOIN provenance.assertion_value_identity_resolution v ON v.assertion_id=p_assertion_id AND v.legacy_identity_resolution_id=x.legacy_identity_resolution_id WHERE x.canonical_assignment_id=p_assignment_id) INTO v_match;
  END CASE;
  RETURN COALESCE(v_match,false);
END
$function$;

-- Preserve the existing exact-one subtype check, but strengthen the accepted
-- assertion path so an unrelated accepted assertion cannot authorize a join.
ALTER FUNCTION provenance.validate_one_assignment(uuid)
  RENAME TO validate_one_assignment_shape_v1;
CREATE FUNCTION provenance.validate_one_assignment(p_assignment_id uuid)
RETURNS void LANGUAGE plpgsql SET search_path=pg_catalog
AS $function$
DECLARE v_status provenance.assertion_status;
BEGIN
  PERFORM provenance.validate_one_assignment_shape_v1(p_assignment_id);
  SELECT status INTO v_status FROM provenance.canonical_assignment
  WHERE canonical_assignment_id=p_assignment_id;
  IF v_status='accepted'
    AND NOT EXISTS (
      SELECT 1 FROM provenance.assignment_assertion aa
      WHERE aa.canonical_assignment_id=p_assignment_id
        AND aa.support_role='supports'
        AND provenance.assignment_assertion_matches(
          p_assignment_id, aa.assertion_id))
    AND NOT EXISTS (
      SELECT 1 FROM provenance.assignment_review_decision d
      WHERE d.canonical_assignment_id=p_assignment_id AND d.outcome='accept'
        AND NOT EXISTS (SELECT 1 FROM provenance.assignment_review_decision n
          WHERE n.supersedes_decision_id=d.assignment_review_decision_id)
        AND EXISTS (SELECT 1 FROM provenance.assignment_decision_evidence e
          WHERE e.assignment_review_decision_id=d.assignment_review_decision_id
            AND e.evidence_role='supports')) THEN
    RAISE EXCEPTION USING ERRCODE='23514',
      MESSAGE='ACCEPTED_ASSIGNMENT_SUPPORT_NOT_TARGET_COMPATIBLE';
  END IF;
END
$function$;

CREATE FUNCTION research.enforce_epistemic_registry_fanout()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog
AS $function$
BEGIN
  IF EXISTS (SELECT 1 FROM research.claim_revision c
    WHERE c.epistemic_class_id=NEW.epistemic_class_id
      AND c.status='accepted')
    AND to_jsonb(OLD) IS DISTINCT FROM to_jsonb(NEW) THEN
    RAISE EXCEPTION USING ERRCODE='23514',
      MESSAGE='EPISTEMIC_REGISTRY_CHANGE_INVALIDATES_ACCEPTED_CLAIM';
  END IF;
  RETURN NULL;
END
$function$;
CREATE CONSTRAINT TRIGGER epistemic_registry_fanout
AFTER UPDATE ON research.epistemic_class
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION research.enforce_epistemic_registry_fanout();

CREATE FUNCTION rights.enforce_one_current_history_leaf()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog
AS $function$
DECLARE v_count integer;
BEGIN
  IF TG_TABLE_NAME='rights_assessment' THEN
    IF NEW.supersedes_rights_assessment_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM rights.rights_assessment p
      WHERE p.rights_assessment_id=NEW.supersedes_rights_assessment_id
        AND p.assessed_at < NEW.assessed_at) THEN
      RAISE EXCEPTION USING ERRCODE='23514',
        MESSAGE='RIGHTS_ASSESSMENT_SUPERSESSION_TIME_OR_PARENT_MISMATCH';
    END IF;
    SELECT count(*) INTO v_count FROM rights.rights_assessment x
    WHERE rights.assessment_subject_key(x.rights_assessment_id)
      = rights.assessment_subject_key(NEW.rights_assessment_id)
      AND NOT EXISTS (SELECT 1 FROM rights.rights_assessment n
        WHERE n.supersedes_rights_assessment_id=x.rights_assessment_id);
  ELSIF TG_TABLE_NAME='provider_policy_evaluation' THEN
    IF NEW.supersedes_provider_policy_evaluation_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM rights.provider_policy_evaluation p
      WHERE p.provider_policy_evaluation_id=
          NEW.supersedes_provider_policy_evaluation_id
        AND p.object_visual_reference_id=NEW.object_visual_reference_id
        AND p.evaluated_at < NEW.evaluated_at) THEN
      RAISE EXCEPTION USING ERRCODE='23514',
        MESSAGE='POLICY_EVALUATION_SUPERSESSION_TIME_OR_PARENT_MISMATCH';
    END IF;
    SELECT count(*) INTO v_count FROM rights.provider_policy_evaluation x
    WHERE x.object_visual_reference_id=NEW.object_visual_reference_id
      AND NOT EXISTS (SELECT 1 FROM rights.provider_policy_evaluation n
        WHERE n.supersedes_provider_policy_evaluation_id=x.provider_policy_evaluation_id);
  ELSIF TG_TABLE_NAME='delivery_assessment' THEN
    IF NEW.supersedes_delivery_assessment_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM rights.delivery_assessment p
      WHERE p.delivery_assessment_id=NEW.supersedes_delivery_assessment_id
        AND p.object_visual_reference_id=NEW.object_visual_reference_id
        AND p.assessed_at < NEW.assessed_at) THEN
      RAISE EXCEPTION USING ERRCODE='23514',
        MESSAGE='DELIVERY_SUPERSESSION_TIME_OR_PARENT_MISMATCH';
    END IF;
    SELECT count(*) INTO v_count FROM rights.delivery_assessment x
    WHERE x.object_visual_reference_id=NEW.object_visual_reference_id
      AND NOT EXISTS (SELECT 1 FROM rights.delivery_assessment n
        WHERE n.supersedes_delivery_assessment_id=x.delivery_assessment_id);
  ELSE
    IF NEW.supersedes_attribution_bundle_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM rights.attribution_bundle p
      WHERE p.attribution_bundle_id=NEW.supersedes_attribution_bundle_id
        AND p.object_visual_reference_id=NEW.object_visual_reference_id
        AND p.validated_at < NEW.validated_at) THEN
      RAISE EXCEPTION USING ERRCODE='23514',
        MESSAGE='ATTRIBUTION_SUPERSESSION_TIME_OR_PARENT_MISMATCH';
    END IF;
    SELECT count(*) INTO v_count FROM rights.attribution_bundle x
    WHERE x.object_visual_reference_id=NEW.object_visual_reference_id
      AND NOT EXISTS (SELECT 1 FROM rights.attribution_bundle n
        WHERE n.supersedes_attribution_bundle_id=x.attribution_bundle_id);
  END IF;
  IF v_count<>1 THEN
    RAISE EXCEPTION USING ERRCODE='23514',
      MESSAGE='RIGHTS_HISTORY_REQUIRES_ONE_CURRENT_LEAF';
  END IF;
  RETURN NULL;
END
$function$;
CREATE CONSTRAINT TRIGGER rights_assessment_one_current_leaf
AFTER INSERT ON rights.rights_assessment DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION rights.enforce_one_current_history_leaf();
CREATE CONSTRAINT TRIGGER policy_evaluation_one_current_leaf
AFTER INSERT ON rights.provider_policy_evaluation DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION rights.enforce_one_current_history_leaf();
CREATE CONSTRAINT TRIGGER delivery_assessment_one_current_leaf
AFTER INSERT ON rights.delivery_assessment DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION rights.enforce_one_current_history_leaf();
CREATE CONSTRAINT TRIGGER attribution_bundle_one_current_leaf
AFTER INSERT ON rights.attribution_bundle DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION rights.enforce_one_current_history_leaf();

CREATE TRIGGER predicate_evidence_profile_append_only
BEFORE UPDATE OR DELETE ON provenance.predicate_evidence_profile
FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER assignment_predicate_compatibility_append_only
BEFORE UPDATE OR DELETE ON provenance.assignment_predicate_compatibility
FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER analysis_run_append_only
BEFORE UPDATE OR DELETE ON research.analysis_run
FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER trace_node_append_only
BEFORE UPDATE OR DELETE ON research.trace_node
FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER trace_tree_append_only
BEFORE UPDATE OR DELETE ON research.trace_tree
FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER trace_branch_append_only
BEFORE UPDATE OR DELETE ON research.trace_branch
FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER trace_node_tree_membership_append_only
BEFORE UPDATE OR DELETE ON research.trace_node_tree_membership
FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();

-- Guard every new immutable release projection and new append-only receipt.
CREATE TRIGGER guard_research_source_lineage BEFORE INSERT OR UPDATE OR DELETE ON release.research_source_lineage FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_research_projection_set BEFORE INSERT OR UPDATE OR DELETE ON release.research_projection_set FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_research_registry_snapshot BEFORE INSERT OR UPDATE OR DELETE ON release.research_registry_snapshot FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_research_corpus_snapshot BEFORE INSERT OR UPDATE OR DELETE ON release.research_corpus_snapshot FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_research_count_snapshot BEFORE INSERT OR UPDATE OR DELETE ON release.research_count_snapshot FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_research_asset BEFORE INSERT OR UPDATE OR DELETE ON release.research_asset FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_research_asset_dependency BEFORE INSERT OR UPDATE OR DELETE ON release.research_asset_dependency FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_research_claim_evidence BEFORE INSERT OR UPDATE OR DELETE ON release.research_release_claim_evidence FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_research_analysis_run BEFORE INSERT OR UPDATE OR DELETE ON release.research_release_analysis_run FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_research_relation_evidence BEFORE INSERT OR UPDATE OR DELETE ON release.research_release_relation_evidence FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_research_identity_resolution BEFORE INSERT OR UPDATE OR DELETE ON release.research_legacy_identity_resolution FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_research_split_successor BEFORE INSERT OR UPDATE OR DELETE ON release.research_legacy_identity_split_successor FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_trace_tree_projection BEFORE INSERT OR UPDATE OR DELETE ON release.trace_tree_projection FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_trace_branch_projection BEFORE INSERT OR UPDATE OR DELETE ON release.trace_branch_projection FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_trace_node_tree_placement BEFORE INSERT OR UPDATE OR DELETE ON release.trace_node_tree_placement FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_trace_edge_tree_placement BEFORE INSERT OR UPDATE OR DELETE ON release.trace_edge_tree_placement FOR EACH ROW EXECUTE FUNCTION release.guard_research_projection_mutation();
CREATE TRIGGER guard_visual_policy_input BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_policy_input FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_asset BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_asset FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_asset_dependency BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_asset_dependency FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER guard_visual_legacy_snapshot BEFORE INSERT OR UPDATE OR DELETE ON release.visual_registry_legacy_disposition_snapshot FOR EACH ROW EXECUTE FUNCTION release.guard_visual_projection_mutation();
CREATE TRIGGER audit_research_validation_receipt_append_only BEFORE UPDATE OR DELETE ON audit.research_validation_receipt_event FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER audit_visual_validation_receipt_append_only BEFORE UPDATE OR DELETE ON audit.visual_validation_receipt_event FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();

RESET ROLE;
