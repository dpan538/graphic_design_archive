\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE FUNCTION raw.enforce_migration_batch_authority()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM raw.source_asset a
    WHERE a.source_asset_id = NEW.canonical_input_asset_id
      AND a.authority = 'canonical_migration_input'
      AND a.sha256 = NEW.input_sha256
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'MIGRATION_BATCH_REQUIRES_EXACT_CANONICAL_INPUT_ASSET';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER migration_batch_authority_exact
AFTER INSERT OR UPDATE ON raw.migration_batch
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION raw.enforce_migration_batch_authority();

CREATE FUNCTION raw.enforce_legacy_surface_lineage()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE v_id uuid := COALESCE(NEW.legacy_surface_ledger_id, OLD.legacy_surface_ledger_id);
BEGIN
  IF EXISTS (
    SELECT 1
    FROM raw.legacy_surface_ledger l
    JOIN raw.migration_batch b ON b.migration_batch_id = l.migration_batch_id
    JOIN raw.source_record r ON r.source_record_id = l.source_record_id
    WHERE l.legacy_surface_ledger_id = v_id
      AND (
        l.canonical_input_asset_id IS DISTINCT FROM b.canonical_input_asset_id
        OR r.source_asset_id IS DISTINCT FROM b.canonical_input_asset_id
        OR l.source_fingerprint IS DISTINCT FROM r.raw_fingerprint
        OR (l.import_disposition <> 'candidate' AND NOT EXISTS (
          SELECT 1 FROM core.archive_object o
          WHERE o.archive_object_id = l.archive_object_id
            AND o.created_from_surface_ledger_id = l.legacy_surface_ledger_id
        ))
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'LEGACY_SURFACE_LINEAGE_OR_RECIPROCAL_OBJECT_MISMATCH';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER legacy_surface_lineage_exact
AFTER INSERT OR UPDATE OR DELETE ON raw.legacy_surface_ledger
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION raw.enforce_legacy_surface_lineage();

CREATE FUNCTION raw.enforce_archive_object_surface_reciprocal()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE v_id uuid := COALESCE(NEW.archive_object_id, OLD.archive_object_id);
BEGIN
  IF EXISTS (
    SELECT 1 FROM core.archive_object o
    LEFT JOIN raw.legacy_surface_ledger l
      ON l.legacy_surface_ledger_id = o.created_from_surface_ledger_id
    WHERE o.archive_object_id = v_id
      AND o.created_from_surface_ledger_id IS NOT NULL
      AND (l.archive_object_id IS DISTINCT FROM o.archive_object_id
        OR l.import_disposition = 'candidate')
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ARCHIVE_OBJECT_SURFACE_LEDGER_RECIPROCAL_MISMATCH';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER archive_object_surface_reciprocal
AFTER INSERT OR UPDATE OR DELETE ON core.archive_object
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION raw.enforce_archive_object_surface_reciprocal();

CREATE FUNCTION core.enforce_legacy_identity_resolution()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := COALESCE(to_jsonb(NEW), to_jsonb(OLD));
  v_resolution_id uuid := COALESCE(
    (v_row ->> 'legacy_identity_resolution_id')::uuid,
    (SELECT s.legacy_identity_resolution_id
     FROM core.legacy_identity_split_successor s
     WHERE s.successor_archive_object_id = (v_row ->> 'successor_archive_object_id')::uuid
     LIMIT 1)
  );
  v_identity_id uuid;
  v_kind core.legacy_identity_kind;
  v_state core.identity_resolution_state;
  v_target_count integer;
  v_split_count integer;
  v_current_count integer;
BEGIN
  SELECT r.legacy_identity_id, i.identity_kind, r.resolution_state,
    num_nonnulls(r.target_archive_object_id, r.target_source_record_id,
      r.target_trace_node_id, r.target_folder_id)
      + CASE WHEN r.target_trace_edge_release_id IS NULL THEN 0 ELSE 1 END
  INTO v_identity_id, v_kind, v_state, v_target_count
  FROM core.legacy_identity_resolution r
  JOIN core.legacy_identity i ON i.legacy_identity_id = r.legacy_identity_id
  WHERE r.legacy_identity_resolution_id = v_resolution_id;
  IF NOT FOUND THEN RETURN NULL; END IF;

  IF (v_kind = 'archive_object'
      AND v_state NOT IN ('split','unresolved','withdrawn')
      AND NOT EXISTS (
      SELECT 1 FROM core.legacy_identity_resolution r
      WHERE r.legacy_identity_resolution_id = v_resolution_id
        AND r.target_archive_object_id IS NOT NULL))
    OR (v_kind = 'source_record'
      AND v_state NOT IN ('split','unresolved','withdrawn') AND NOT EXISTS (
      SELECT 1 FROM core.legacy_identity_resolution r
      WHERE r.legacy_identity_resolution_id = v_resolution_id
        AND r.target_source_record_id IS NOT NULL))
    OR (v_kind = 'trace_node'
      AND v_state NOT IN ('split','unresolved','withdrawn') AND NOT EXISTS (
      SELECT 1 FROM core.legacy_identity_resolution r
      WHERE r.legacy_identity_resolution_id = v_resolution_id
        AND r.target_trace_node_id IS NOT NULL))
    OR (v_kind = 'folder'
      AND v_state NOT IN ('split','unresolved','withdrawn') AND NOT EXISTS (
      SELECT 1 FROM core.legacy_identity_resolution r
      WHERE r.legacy_identity_resolution_id = v_resolution_id
        AND r.target_folder_id IS NOT NULL))
    OR (v_kind = 'trace_edge'
      AND v_state NOT IN ('split','unresolved','withdrawn')
      AND NOT EXISTS (
        SELECT 1 FROM core.legacy_identity_resolution r
        WHERE r.legacy_identity_resolution_id = v_resolution_id
          AND r.target_trace_edge_release_id IS NOT NULL
          AND r.effective_release_id = r.target_trace_edge_release_id
      )) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'LEGACY_IDENTITY_TYPED_TARGET_MISMATCH';
  END IF;

  IF EXISTS (
    SELECT 1 FROM core.legacy_identity_resolution r
    JOIN core.legacy_identity_resolution p
      ON p.legacy_identity_resolution_id = r.supersedes_resolution_id
    WHERE r.legacy_identity_resolution_id = v_resolution_id
      AND (r.legacy_identity_id IS DISTINCT FROM p.legacy_identity_id
        OR r.effective_from <= p.effective_from)
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'LEGACY_IDENTITY_RESOLUTION_SUPERSESSION_MISMATCH';
  END IF;

  SELECT count(*) INTO v_current_count
  FROM core.legacy_identity_resolution r
  WHERE r.legacy_identity_id = v_identity_id
    AND NOT EXISTS (
      SELECT 1 FROM core.legacy_identity_resolution n
      WHERE n.supersedes_resolution_id = r.legacy_identity_resolution_id
    );
  IF v_current_count <> 1 THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'LEGACY_IDENTITY_REQUIRES_ONE_CURRENT_RESOLUTION';
  END IF;

  SELECT count(*) INTO v_split_count
  FROM core.legacy_identity_split_successor s
  WHERE s.legacy_identity_resolution_id = v_resolution_id;
  IF (v_state = 'split' AND v_split_count < 2)
    OR (v_state <> 'split' AND v_split_count <> 0) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'LEGACY_IDENTITY_SPLIT_ARITY_MISMATCH';
  END IF;
  IF v_state NOT IN ('unresolved','withdrawn')
    AND EXISTS (
      SELECT 1 FROM core.legacy_identity_resolution r
      WHERE r.legacy_identity_resolution_id = v_resolution_id
        AND (r.decision_evidence_item_id IS NULL OR r.effective_release_id IS NULL)
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'LEGACY_IDENTITY_RESOLUTION_REQUIRES_EVIDENCE_AND_RELEASE';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER legacy_identity_resolution_exact
AFTER INSERT OR UPDATE OR DELETE ON core.legacy_identity_resolution
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION core.enforce_legacy_identity_resolution();
CREATE CONSTRAINT TRIGGER legacy_identity_split_exact
AFTER INSERT OR UPDATE OR DELETE ON core.legacy_identity_split_successor
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION core.enforce_legacy_identity_resolution();

CREATE FUNCTION core.enforce_entity_subtype()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := COALESCE(to_jsonb(NEW), to_jsonb(OLD));
  v_entity_id uuid := COALESCE(
    (v_row ->> 'entity_id')::uuid,
    (v_row ->> 'archive_object_id')::uuid,
    (v_row ->> 'agent_id')::uuid,
    (v_row ->> 'place_id')::uuid,
    (v_row ->> 'concept_id')::uuid,
    (v_row ->> 'collection_id')::uuid,
    (v_row ->> 'temporal_extent_id')::uuid
  );
  v_kind core.entity_kind;
  v_count integer;
  v_matches boolean;
BEGIN
  SELECT e.entity_kind INTO v_kind
  FROM core.entity AS e WHERE e.entity_id = v_entity_id;
  IF NOT FOUND THEN
    RETURN NULL;
  END IF;

  SELECT
    (SELECT count(*) FROM core.archive_object a WHERE a.archive_object_id = v_entity_id)
    + (SELECT count(*) FROM core.agent a WHERE a.agent_id = v_entity_id)
    + (SELECT count(*) FROM core.place p WHERE p.place_id = v_entity_id)
    + (SELECT count(*) FROM core.concept c WHERE c.concept_id = v_entity_id)
    + (SELECT count(*) FROM core.collection c WHERE c.collection_id = v_entity_id)
    + (SELECT count(*) FROM core.temporal_extent t WHERE t.temporal_extent_id = v_entity_id)
  INTO v_count;

  v_matches := CASE v_kind
    WHEN 'archive_object' THEN EXISTS (SELECT 1 FROM core.archive_object a WHERE a.archive_object_id = v_entity_id)
    WHEN 'agent' THEN EXISTS (SELECT 1 FROM core.agent a WHERE a.agent_id = v_entity_id)
    WHEN 'place' THEN EXISTS (SELECT 1 FROM core.place p WHERE p.place_id = v_entity_id)
    WHEN 'concept' THEN EXISTS (SELECT 1 FROM core.concept c WHERE c.concept_id = v_entity_id)
    WHEN 'collection' THEN EXISTS (SELECT 1 FROM core.collection c WHERE c.collection_id = v_entity_id)
    WHEN 'temporal_extent' THEN EXISTS (SELECT 1 FROM core.temporal_extent t WHERE t.temporal_extent_id = v_entity_id)
    ELSE false
  END;

  IF v_count <> 1 OR NOT v_matches THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ENTITY_SUBTYPE_EXACTLY_ONE_VIOLATION';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER entity_subtype_from_entity
AFTER INSERT OR UPDATE OR DELETE ON core.entity
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION core.enforce_entity_subtype();

CREATE CONSTRAINT TRIGGER entity_subtype_from_archive_object
AFTER INSERT OR UPDATE OR DELETE ON core.archive_object
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION core.enforce_entity_subtype();
CREATE CONSTRAINT TRIGGER entity_subtype_from_agent
AFTER INSERT OR UPDATE OR DELETE ON core.agent
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION core.enforce_entity_subtype();
CREATE CONSTRAINT TRIGGER entity_subtype_from_place
AFTER INSERT OR UPDATE OR DELETE ON core.place
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION core.enforce_entity_subtype();
CREATE CONSTRAINT TRIGGER entity_subtype_from_concept
AFTER INSERT OR UPDATE OR DELETE ON core.concept
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION core.enforce_entity_subtype();
CREATE CONSTRAINT TRIGGER entity_subtype_from_collection
AFTER INSERT OR UPDATE OR DELETE ON core.collection
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION core.enforce_entity_subtype();
CREATE CONSTRAINT TRIGGER entity_subtype_from_temporal_extent
AFTER INSERT OR UPDATE OR DELETE ON core.temporal_extent
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION core.enforce_entity_subtype();

CREATE FUNCTION provenance.enforce_assertion_shape()
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

  SELECT (SELECT count(*) FROM provenance.assertion_subject_entity s WHERE s.assertion_id = v_id)
      + (SELECT count(*) FROM provenance.assertion_subject_source_record s WHERE s.assertion_id = v_id)
      + (SELECT count(*) FROM provenance.assertion_subject_trace_node s WHERE s.assertion_id = v_id)
      + (SELECT count(*) FROM provenance.assertion_subject_representation s WHERE s.assertion_id = v_id),
    (SELECT count(*) FROM provenance.assertion_value_literal v WHERE v.assertion_id = v_id)
      + (SELECT count(*) FROM provenance.assertion_value_entity v WHERE v.assertion_id = v_id)
      + (SELECT count(*) FROM provenance.assertion_value_source_record v WHERE v.assertion_id = v_id)
      + (SELECT count(*) FROM provenance.assertion_value_trace_node v WHERE v.assertion_id = v_id)
  INTO v_subject_count, v_value_count;

  IF v_subject_count <> 1
    OR (v_subject_kind = 'entity' AND NOT EXISTS (SELECT 1 FROM provenance.assertion_subject_entity s WHERE s.assertion_id = v_id))
    OR (v_subject_kind = 'source_record' AND NOT EXISTS (SELECT 1 FROM provenance.assertion_subject_source_record s WHERE s.assertion_id = v_id))
    OR (v_subject_kind = 'trace_node' AND NOT EXISTS (SELECT 1 FROM provenance.assertion_subject_trace_node s WHERE s.assertion_id = v_id))
    OR (v_subject_kind = 'digital_representation' AND NOT EXISTS (SELECT 1 FROM provenance.assertion_subject_representation s WHERE s.assertion_id = v_id)) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ASSERTION_SUBJECT_EXACTLY_ONE_VIOLATION';
  END IF;
  IF v_value_count <> 1
    OR (v_value_kind = 'literal' AND NOT EXISTS (SELECT 1 FROM provenance.assertion_value_literal v WHERE v.assertion_id = v_id))
    OR (v_value_kind = 'entity' AND NOT EXISTS (SELECT 1 FROM provenance.assertion_value_entity v WHERE v.assertion_id = v_id))
    OR (v_value_kind = 'source_record' AND NOT EXISTS (SELECT 1 FROM provenance.assertion_value_source_record v WHERE v.assertion_id = v_id))
    OR (v_value_kind = 'trace_node' AND NOT EXISTS (SELECT 1 FROM provenance.assertion_value_trace_node v WHERE v.assertion_id = v_id)) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ASSERTION_VALUE_EXACTLY_ONE_VIOLATION';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER assertion_shape_from_assertion
AFTER INSERT OR UPDATE OR DELETE ON provenance.assertion
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assertion_shape();
CREATE CONSTRAINT TRIGGER assertion_shape_from_subject
AFTER INSERT OR UPDATE OR DELETE ON provenance.assertion_subject_entity
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assertion_shape();
CREATE CONSTRAINT TRIGGER assertion_shape_from_source_record_subject
AFTER INSERT OR UPDATE OR DELETE ON provenance.assertion_subject_source_record
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assertion_shape();
CREATE CONSTRAINT TRIGGER assertion_shape_from_trace_node_subject
AFTER INSERT OR UPDATE OR DELETE ON provenance.assertion_subject_trace_node
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assertion_shape();
CREATE CONSTRAINT TRIGGER assertion_shape_from_representation_subject
AFTER INSERT OR UPDATE OR DELETE ON provenance.assertion_subject_representation
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assertion_shape();
CREATE CONSTRAINT TRIGGER assertion_shape_from_literal
AFTER INSERT OR UPDATE OR DELETE ON provenance.assertion_value_literal
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assertion_shape();
CREATE CONSTRAINT TRIGGER assertion_shape_from_entity_value
AFTER INSERT OR UPDATE OR DELETE ON provenance.assertion_value_entity
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assertion_shape();
CREATE CONSTRAINT TRIGGER assertion_shape_from_source_record_value
AFTER INSERT OR UPDATE OR DELETE ON provenance.assertion_value_source_record
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assertion_shape();
CREATE CONSTRAINT TRIGGER assertion_shape_from_trace_node_value
AFTER INSERT OR UPDATE OR DELETE ON provenance.assertion_value_trace_node
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assertion_shape();

CREATE FUNCTION provenance.enforce_accepted_assertion()
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
    JOIN provenance.assertion_predicate p ON p.assertion_predicate_id = a.assertion_predicate_id
    WHERE a.assertion_id = v_id AND a.status = 'accepted'
      AND (NOT p.active OR NOT EXISTS (
        SELECT 1 FROM provenance.assertion_evidence ae
        WHERE ae.assertion_id = a.assertion_id AND ae.evidence_role = 'supports'
      ) OR NOT EXISTS (
        SELECT 1
        FROM provenance.assertion_review_decision d
        WHERE d.assertion_id = a.assertion_id
          AND d.outcome = 'accept'
          AND NOT EXISTS (
            SELECT 1 FROM provenance.assertion_review_decision newer
            WHERE newer.supersedes_decision_id = d.assertion_review_decision_id
          )
          AND EXISTS (
            SELECT 1 FROM provenance.assertion_decision_evidence de
            WHERE de.assertion_review_decision_id = d.assertion_review_decision_id
              AND de.evidence_role = 'supports'
          )
      ))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ACCEPTED_ASSERTION_REQUIRES_ACTIVE_PREDICATE_AND_EVIDENCE';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER accepted_assertion_from_assertion
AFTER INSERT OR UPDATE ON provenance.assertion
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_accepted_assertion();
CREATE CONSTRAINT TRIGGER accepted_assertion_from_evidence
AFTER INSERT OR UPDATE OR DELETE ON provenance.assertion_evidence
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_accepted_assertion();
CREATE CONSTRAINT TRIGGER accepted_assertion_from_decision
AFTER INSERT OR UPDATE OR DELETE ON provenance.assertion_review_decision
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_accepted_assertion();
CREATE CONSTRAINT TRIGGER accepted_assertion_from_decision_evidence
AFTER INSERT OR UPDATE OR DELETE ON provenance.assertion_decision_evidence
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_accepted_assertion();

CREATE FUNCTION provenance.validate_one_assignment(p_assignment_id uuid)
RETURNS void
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_kind provenance.assignment_kind;
  v_status provenance.assertion_status;
  v_count integer;
BEGIN
  SELECT a.assignment_kind, a.status INTO v_kind, v_status
  FROM provenance.canonical_assignment a
  WHERE a.canonical_assignment_id = p_assignment_id;
  IF NOT FOUND THEN RETURN; END IF;

  SELECT
      (SELECT count(*) FROM provenance.assignment_entity_name x WHERE x.canonical_assignment_id = p_assignment_id)
    + (SELECT count(*) FROM provenance.assignment_object_source_record x WHERE x.canonical_assignment_id = p_assignment_id)
    + (SELECT count(*) FROM provenance.assignment_object_agent_credit x WHERE x.canonical_assignment_id = p_assignment_id)
    + (SELECT count(*) FROM provenance.assignment_object_medium x WHERE x.canonical_assignment_id = p_assignment_id)
    + (SELECT count(*) FROM provenance.assignment_object_type x WHERE x.canonical_assignment_id = p_assignment_id)
    + (SELECT count(*) FROM provenance.assignment_object_subject x WHERE x.canonical_assignment_id = p_assignment_id)
    + (SELECT count(*) FROM provenance.assignment_object_collection x WHERE x.canonical_assignment_id = p_assignment_id)
    + (SELECT count(*) FROM provenance.assignment_object_temporal x WHERE x.canonical_assignment_id = p_assignment_id)
    + (SELECT count(*) FROM provenance.assignment_object_place x WHERE x.canonical_assignment_id = p_assignment_id)
    + (SELECT count(*) FROM provenance.assignment_folder_membership x WHERE x.canonical_assignment_id = p_assignment_id)
    + (SELECT count(*) FROM provenance.assignment_object_tree_membership x WHERE x.canonical_assignment_id = p_assignment_id)
    + (SELECT count(*) FROM provenance.assignment_object_representation x WHERE x.canonical_assignment_id = p_assignment_id)
    + (SELECT count(*) FROM provenance.assignment_identity_resolution x WHERE x.canonical_assignment_id = p_assignment_id)
  INTO v_count;

  IF v_count <> 1 OR NOT (CASE v_kind
    WHEN 'entity_name' THEN EXISTS (SELECT 1 FROM provenance.assignment_entity_name x WHERE x.canonical_assignment_id = p_assignment_id)
    WHEN 'object_source_record' THEN EXISTS (SELECT 1 FROM provenance.assignment_object_source_record x WHERE x.canonical_assignment_id = p_assignment_id)
    WHEN 'object_agent_credit' THEN EXISTS (SELECT 1 FROM provenance.assignment_object_agent_credit x WHERE x.canonical_assignment_id = p_assignment_id)
    WHEN 'object_medium' THEN EXISTS (SELECT 1 FROM provenance.assignment_object_medium x WHERE x.canonical_assignment_id = p_assignment_id)
    WHEN 'object_type' THEN EXISTS (SELECT 1 FROM provenance.assignment_object_type x WHERE x.canonical_assignment_id = p_assignment_id)
    WHEN 'object_subject' THEN EXISTS (SELECT 1 FROM provenance.assignment_object_subject x WHERE x.canonical_assignment_id = p_assignment_id)
    WHEN 'object_collection' THEN EXISTS (SELECT 1 FROM provenance.assignment_object_collection x WHERE x.canonical_assignment_id = p_assignment_id)
    WHEN 'object_temporal' THEN EXISTS (SELECT 1 FROM provenance.assignment_object_temporal x WHERE x.canonical_assignment_id = p_assignment_id)
    WHEN 'object_place' THEN EXISTS (SELECT 1 FROM provenance.assignment_object_place x WHERE x.canonical_assignment_id = p_assignment_id)
    WHEN 'folder_membership' THEN EXISTS (SELECT 1 FROM provenance.assignment_folder_membership x WHERE x.canonical_assignment_id = p_assignment_id)
    WHEN 'object_tree_membership' THEN EXISTS (SELECT 1 FROM provenance.assignment_object_tree_membership x WHERE x.canonical_assignment_id = p_assignment_id)
    WHEN 'object_representation' THEN EXISTS (SELECT 1 FROM provenance.assignment_object_representation x WHERE x.canonical_assignment_id = p_assignment_id)
    WHEN 'identity_resolution' THEN EXISTS (SELECT 1 FROM provenance.assignment_identity_resolution x WHERE x.canonical_assignment_id = p_assignment_id)
    ELSE false
  END) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'CANONICAL_ASSIGNMENT_EXACTLY_ONE_TYPED_SUBTYPE_VIOLATION';
  END IF;

  IF v_status = 'accepted' AND NOT (
    EXISTS (
      SELECT 1
      FROM provenance.assignment_assertion aa
      JOIN provenance.assertion a ON a.assertion_id = aa.assertion_id
      WHERE aa.canonical_assignment_id = p_assignment_id
        AND aa.support_role = 'supports' AND a.status = 'accepted'
    ) OR EXISTS (
      SELECT 1
      FROM provenance.assignment_review_decision d
      WHERE d.canonical_assignment_id = p_assignment_id
        AND d.outcome = 'accept'
        AND NOT EXISTS (
          SELECT 1 FROM provenance.assignment_review_decision newer
          WHERE newer.supersedes_decision_id = d.assignment_review_decision_id
        )
        AND EXISTS (
          SELECT 1 FROM provenance.assignment_decision_evidence de
          WHERE de.assignment_review_decision_id = d.assignment_review_decision_id
            AND de.evidence_role = 'supports'
        )
    )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ACCEPTED_ASSIGNMENT_REQUIRES_ACCEPTED_ASSERTION_OR_EVIDENCE_BOUND_DECISION';
  END IF;
END
$function$;

CREATE FUNCTION provenance.enforce_assignment_shape_and_support()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := COALESCE(to_jsonb(NEW), to_jsonb(OLD));
  v_id uuid := (v_row ->> 'canonical_assignment_id')::uuid;
BEGIN
  IF v_id IS NULL AND v_row ? 'assignment_review_decision_id' THEN
    SELECT d.canonical_assignment_id INTO v_id
    FROM provenance.assignment_review_decision d
    WHERE d.assignment_review_decision_id =
      (v_row ->> 'assignment_review_decision_id')::uuid;
  END IF;
  PERFORM provenance.validate_one_assignment(v_id);
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER assignment_shape_from_assignment
AFTER INSERT OR UPDATE OR DELETE ON provenance.canonical_assignment
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assignment_shape_and_support();
CREATE CONSTRAINT TRIGGER assignment_shape_from_entity_name
AFTER INSERT OR UPDATE OR DELETE ON provenance.assignment_entity_name
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assignment_shape_and_support();
CREATE CONSTRAINT TRIGGER assignment_shape_from_source_record
AFTER INSERT OR UPDATE OR DELETE ON provenance.assignment_object_source_record
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assignment_shape_and_support();
CREATE CONSTRAINT TRIGGER assignment_shape_from_agent_credit
AFTER INSERT OR UPDATE OR DELETE ON provenance.assignment_object_agent_credit
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assignment_shape_and_support();
CREATE CONSTRAINT TRIGGER assignment_shape_from_medium
AFTER INSERT OR UPDATE OR DELETE ON provenance.assignment_object_medium
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assignment_shape_and_support();
CREATE CONSTRAINT TRIGGER assignment_shape_from_type
AFTER INSERT OR UPDATE OR DELETE ON provenance.assignment_object_type
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assignment_shape_and_support();
CREATE CONSTRAINT TRIGGER assignment_shape_from_subject
AFTER INSERT OR UPDATE OR DELETE ON provenance.assignment_object_subject
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assignment_shape_and_support();
CREATE CONSTRAINT TRIGGER assignment_shape_from_collection
AFTER INSERT OR UPDATE OR DELETE ON provenance.assignment_object_collection
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assignment_shape_and_support();
CREATE CONSTRAINT TRIGGER assignment_shape_from_temporal
AFTER INSERT OR UPDATE OR DELETE ON provenance.assignment_object_temporal
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assignment_shape_and_support();
CREATE CONSTRAINT TRIGGER assignment_shape_from_place
AFTER INSERT OR UPDATE OR DELETE ON provenance.assignment_object_place
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assignment_shape_and_support();
CREATE CONSTRAINT TRIGGER assignment_shape_from_folder
AFTER INSERT OR UPDATE OR DELETE ON provenance.assignment_folder_membership
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assignment_shape_and_support();
CREATE CONSTRAINT TRIGGER assignment_shape_from_tree
AFTER INSERT OR UPDATE OR DELETE ON provenance.assignment_object_tree_membership
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assignment_shape_and_support();
CREATE CONSTRAINT TRIGGER assignment_shape_from_representation
AFTER INSERT OR UPDATE OR DELETE ON provenance.assignment_object_representation
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assignment_shape_and_support();
CREATE CONSTRAINT TRIGGER assignment_shape_from_identity
AFTER INSERT OR UPDATE OR DELETE ON provenance.assignment_identity_resolution
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assignment_shape_and_support();
CREATE CONSTRAINT TRIGGER assignment_support_from_assertion
AFTER INSERT OR UPDATE OR DELETE ON provenance.assignment_assertion
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assignment_shape_and_support();
CREATE CONSTRAINT TRIGGER assignment_support_from_decision
AFTER INSERT OR UPDATE OR DELETE ON provenance.assignment_review_decision
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assignment_shape_and_support();
CREATE CONSTRAINT TRIGGER assignment_support_from_decision_evidence
AFTER INSERT OR UPDATE OR DELETE ON provenance.assignment_decision_evidence
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION provenance.enforce_assignment_shape_and_support();

CREATE FUNCTION provenance.enforce_assignments_for_assertion()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE r record;
BEGIN
  FOR r IN
    SELECT DISTINCT aa.canonical_assignment_id
    FROM provenance.assignment_assertion aa
    WHERE aa.assertion_id IN (NEW.assertion_id, OLD.assertion_id)
  LOOP
    PERFORM provenance.validate_one_assignment(r.canonical_assignment_id);
  END LOOP;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER assignment_support_from_assertion_status
AFTER UPDATE ON provenance.assertion
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION provenance.enforce_assignments_for_assertion();

CREATE FUNCTION research.enforce_claim_acceptance()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := COALESCE(to_jsonb(NEW), to_jsonb(OLD));
  v_id uuid := (v_row ->> 'claim_revision_id')::uuid;
BEGIN
  IF v_id IS NULL AND v_row ? 'claim_review_decision_id' THEN
    SELECT d.claim_revision_id INTO v_id
    FROM research.claim_review_decision d
    WHERE d.claim_review_decision_id =
      (v_row ->> 'claim_review_decision_id')::uuid;
  END IF;
  IF EXISTS (
    SELECT 1 FROM research.claim_revision cr
    JOIN research.epistemic_class ec ON ec.epistemic_class_id = cr.epistemic_class_id
    WHERE cr.claim_revision_id = v_id AND cr.status = 'accepted'
      AND (
        NOT ec.active
        OR cr.workflow_state <> 'resolved'
        OR (ec.requires_analysis_run AND cr.analysis_run_id IS NULL)
        OR (ec.requires_claimant_source AND cr.claimant_agent_id IS NULL)
        OR NOT EXISTS (
          SELECT 1 FROM research.claim_evidence ce
          WHERE ce.claim_revision_id = cr.claim_revision_id AND ce.evidence_role = 'supports'
        )
        OR NOT EXISTS (
          SELECT 1 FROM research.claim_review_decision d
          WHERE d.claim_revision_id = cr.claim_revision_id
            AND d.outcome = 'accept'
            AND NOT EXISTS (
              SELECT 1 FROM research.claim_review_decision newer
              WHERE newer.supersedes_decision_id = d.claim_review_decision_id
            )
            AND EXISTS (
              SELECT 1 FROM research.claim_decision_evidence de
              WHERE de.claim_review_decision_id = d.claim_review_decision_id
                AND de.evidence_role = 'supports'
            )
            AND (ec.class_code <> 'causal_interpretation' OR d.heightened_review)
        )
        OR (ec.class_code = 'causal_interpretation' AND NOT EXISTS (
          SELECT 1 FROM research.claim_evidence ce
          JOIN provenance.evidence_item ei ON ei.evidence_item_id = ce.evidence_item_id
          WHERE ce.claim_revision_id = cr.claim_revision_id
            AND ce.evidence_role = 'supports'
            AND (ei.internal_locator IS NOT NULL
              OR ei.span_start IS NOT NULL OR ei.stable_citation IS NOT NULL)
        ))
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ACCEPTED_CLAIM_REQUIRES_ACTIVE_CLASS_PROFILE_AND_EVIDENCE';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER claim_acceptance_from_revision
AFTER INSERT OR UPDATE ON research.claim_revision
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION research.enforce_claim_acceptance();
CREATE CONSTRAINT TRIGGER claim_acceptance_from_evidence
AFTER INSERT OR UPDATE OR DELETE ON research.claim_evidence
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION research.enforce_claim_acceptance();
CREATE CONSTRAINT TRIGGER claim_acceptance_from_decision
AFTER INSERT OR UPDATE OR DELETE ON research.claim_review_decision
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION research.enforce_claim_acceptance();
CREATE CONSTRAINT TRIGGER claim_acceptance_from_decision_evidence
AFTER INSERT OR UPDATE OR DELETE ON research.claim_decision_evidence
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION research.enforce_claim_acceptance();

CREATE FUNCTION research.enforce_one_current_claim_decision()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := COALESCE(to_jsonb(NEW), to_jsonb(OLD));
  v_decision_id uuid := (v_row ->> 'claim_review_decision_id')::uuid;
  v_revision_id uuid;
  v_count integer;
BEGIN
  SELECT d.claim_revision_id INTO v_revision_id
  FROM research.claim_review_decision d
  WHERE d.claim_review_decision_id = v_decision_id;
  IF v_revision_id IS NULL THEN RETURN NULL; END IF;
  IF EXISTS (
    SELECT 1 FROM research.claim_review_decision d
    JOIN research.claim_review_decision p
      ON p.claim_review_decision_id = d.supersedes_decision_id
    WHERE d.claim_review_decision_id = v_decision_id
      AND (d.claim_revision_id IS DISTINCT FROM p.claim_revision_id
        OR d.decided_at <= p.decided_at)
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'CLAIM_DECISION_SUPERSESSION_MISMATCH';
  END IF;
  SELECT count(*) INTO v_count
  FROM research.claim_review_decision d
  WHERE d.claim_revision_id = v_revision_id
    AND NOT EXISTS (
      SELECT 1 FROM research.claim_review_decision n
      WHERE n.supersedes_decision_id = d.claim_review_decision_id
    );
  IF v_count <> 1 THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'CLAIM_REQUIRES_ONE_EFFECTIVE_REVIEW_DECISION';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER claim_one_current_decision
AFTER INSERT OR UPDATE OR DELETE ON research.claim_review_decision
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION research.enforce_one_current_claim_decision();

CREATE FUNCTION research.enforce_relation_endpoint_shape()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_id uuid := COALESCE(NEW.relation_endpoint_id, OLD.relation_endpoint_id);
  v_kind research.relation_endpoint_kind;
  v_count integer;
BEGIN
  SELECT e.endpoint_kind INTO v_kind FROM research.relation_endpoint e
  WHERE e.relation_endpoint_id = v_id;
  IF NOT FOUND THEN RETURN NULL; END IF;
  SELECT count(*) INTO v_count FROM research.relation_endpoint_entity x
  WHERE x.relation_endpoint_id = v_id;
  IF v_count <> 1 OR v_kind <> 'entity' THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'RELATION_ENDPOINT_EXACTLY_ONE_TYPED_TARGET_REQUIRED';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER relation_endpoint_shape_from_parent
AFTER INSERT OR UPDATE OR DELETE ON research.relation_endpoint
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION research.enforce_relation_endpoint_shape();
CREATE CONSTRAINT TRIGGER relation_endpoint_shape_from_entity
AFTER INSERT OR UPDATE OR DELETE ON research.relation_endpoint_entity
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION research.enforce_relation_endpoint_shape();

CREATE FUNCTION research.validate_one_semantic_relation(p_relation_id uuid)
RETURNS void
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_bad boolean;
BEGIN
  SELECT (
    NOT rt.active
    OR sr.origin = 'legacy_projection_only'
    OR se.entity_kind <> rt.subject_entity_kind
    OR oe.entity_kind <> rt.object_entity_kind
    OR NOT (
      EXISTS (
      SELECT 1 FROM research.relation_claim rc
      JOIN research.claim_revision cr ON cr.claim_revision_id = rc.claim_revision_id
      JOIN research.claim_evidence ce ON ce.claim_revision_id = cr.claim_revision_id
      WHERE rc.semantic_relation_id = sr.semantic_relation_id
        AND rc.claim_role = 'supports' AND cr.status = 'accepted'
        AND ce.evidence_role = 'supports'
      )
      OR EXISTS (
      SELECT 1 FROM research.relation_review_decision rd
      WHERE rd.semantic_relation_id = sr.semantic_relation_id AND rd.outcome = 'accept'
        AND NOT EXISTS (
          SELECT 1 FROM research.relation_review_decision newer
          WHERE newer.supersedes_decision_id = rd.relation_review_decision_id
        )
        AND EXISTS (
          SELECT 1 FROM research.relation_decision_evidence de
          WHERE de.relation_review_decision_id = rd.relation_review_decision_id
            AND de.evidence_role = 'supports'
        )
      )
    )
  ) INTO v_bad
  FROM research.semantic_relation sr
  JOIN research.relation_type rt ON rt.relation_type_id = sr.relation_type_id
  JOIN research.relation_endpoint_entity sre ON sre.relation_endpoint_id = sr.subject_endpoint_id
  JOIN core.entity se ON se.entity_id = sre.entity_id
  JOIN research.relation_endpoint_entity ore ON ore.relation_endpoint_id = sr.object_endpoint_id
  JOIN core.entity oe ON oe.entity_id = ore.entity_id
  WHERE sr.semantic_relation_id = p_relation_id AND sr.status = 'accepted';

  IF COALESCE(v_bad, false) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ACCEPTED_RELATION_VALIDATION_FAILED';
  END IF;
END
$function$;

CREATE FUNCTION research.enforce_semantic_relation_acceptance()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := COALESCE(to_jsonb(NEW), to_jsonb(OLD));
  v_id uuid := (v_row ->> 'semantic_relation_id')::uuid;
BEGIN
  IF v_id IS NULL AND v_row ? 'relation_review_decision_id' THEN
    SELECT d.semantic_relation_id INTO v_id
    FROM research.relation_review_decision d
    WHERE d.relation_review_decision_id = (v_row ->> 'relation_review_decision_id')::uuid;
  END IF;
  PERFORM research.validate_one_semantic_relation(v_id);
  RETURN NULL;
END
$function$;

CREATE FUNCTION research.enforce_relations_for_type()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE r record;
BEGIN
  FOR r IN SELECT sr.semantic_relation_id FROM research.semantic_relation sr
    WHERE sr.relation_type_id = COALESCE(NEW.relation_type_id, OLD.relation_type_id)
  LOOP
    PERFORM research.validate_one_semantic_relation(r.semantic_relation_id);
  END LOOP;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER semantic_relation_acceptance_from_relation
AFTER INSERT OR UPDATE ON research.semantic_relation
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION research.enforce_semantic_relation_acceptance();
CREATE CONSTRAINT TRIGGER semantic_relation_acceptance_from_claim
AFTER INSERT OR UPDATE OR DELETE ON research.relation_claim
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION research.enforce_semantic_relation_acceptance();
CREATE CONSTRAINT TRIGGER semantic_relation_acceptance_from_decision
AFTER INSERT OR UPDATE OR DELETE ON research.relation_review_decision
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION research.enforce_semantic_relation_acceptance();
CREATE CONSTRAINT TRIGGER semantic_relation_acceptance_from_decision_evidence
AFTER INSERT OR UPDATE OR DELETE ON research.relation_decision_evidence
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION research.enforce_semantic_relation_acceptance();
CREATE CONSTRAINT TRIGGER semantic_relation_acceptance_from_type
AFTER UPDATE ON research.relation_type
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION research.enforce_relations_for_type();

CREATE FUNCTION research.enforce_one_current_relation_decision()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := COALESCE(to_jsonb(NEW), to_jsonb(OLD));
  v_decision_id uuid := (v_row ->> 'relation_review_decision_id')::uuid;
  v_relation_id uuid;
  v_count integer;
BEGIN
  SELECT d.semantic_relation_id INTO v_relation_id
  FROM research.relation_review_decision d
  WHERE d.relation_review_decision_id = v_decision_id;
  IF v_relation_id IS NULL THEN RETURN NULL; END IF;
  IF EXISTS (
    SELECT 1 FROM research.relation_review_decision d
    JOIN research.relation_review_decision p
      ON p.relation_review_decision_id = d.supersedes_decision_id
    WHERE d.relation_review_decision_id = v_decision_id
      AND (d.semantic_relation_id IS DISTINCT FROM p.semantic_relation_id
        OR d.decided_at <= p.decided_at)
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'RELATION_DECISION_SUPERSESSION_MISMATCH';
  END IF;
  SELECT count(*) INTO v_count
  FROM research.relation_review_decision d
  WHERE d.semantic_relation_id = v_relation_id
    AND NOT EXISTS (
      SELECT 1 FROM research.relation_review_decision n
      WHERE n.supersedes_decision_id = d.relation_review_decision_id
    );
  IF v_count > 1 THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'RELATION_HAS_COMPETING_EFFECTIVE_DECISIONS';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER relation_one_current_decision
AFTER INSERT OR UPDATE OR DELETE ON research.relation_review_decision
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION research.enforce_one_current_relation_decision();

CREATE FUNCTION research.enforce_relations_for_claim_revision()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := COALESCE(to_jsonb(NEW), to_jsonb(OLD));
  v_claim_revision_id uuid := (v_row ->> 'claim_revision_id')::uuid;
  r record;
BEGIN
  FOR r IN
    SELECT DISTINCT rc.semantic_relation_id
    FROM research.relation_claim rc
    WHERE rc.claim_revision_id = v_claim_revision_id
  LOOP
    PERFORM research.validate_one_semantic_relation(r.semantic_relation_id);
  END LOOP;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER semantic_relation_acceptance_from_claim_revision
AFTER UPDATE ON research.claim_revision
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION research.enforce_relations_for_claim_revision();
CREATE CONSTRAINT TRIGGER semantic_relation_acceptance_from_claim_evidence
AFTER INSERT OR UPDATE OR DELETE ON research.claim_evidence
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION research.enforce_relations_for_claim_revision();

CREATE FUNCTION research.enforce_relations_for_endpoint()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := COALESCE(to_jsonb(NEW), to_jsonb(OLD));
  v_endpoint_id uuid := (v_row ->> 'relation_endpoint_id')::uuid;
  r record;
BEGIN
  FOR r IN
    SELECT sr.semantic_relation_id
    FROM research.semantic_relation sr
    WHERE sr.subject_endpoint_id = v_endpoint_id
       OR sr.object_endpoint_id = v_endpoint_id
  LOOP
    PERFORM research.validate_one_semantic_relation(r.semantic_relation_id);
  END LOOP;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER semantic_relation_acceptance_from_endpoint_target
AFTER INSERT OR UPDATE OR DELETE ON research.relation_endpoint_entity
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION research.enforce_relations_for_endpoint();

CREATE FUNCTION rights.enforce_rights_observation_shape()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := COALESCE(to_jsonb(NEW), to_jsonb(OLD));
  v_id uuid := (v_row ->> 'rights_observation_id')::uuid;
  v_kind rights.rights_subject_kind;
  v_count integer;
  v_observed_at timestamptz;
BEGIN
  SELECT o.subject_kind, o.observed_at INTO v_kind, v_observed_at
  FROM rights.rights_observation o WHERE o.rights_observation_id = v_id;
  IF NOT FOUND THEN RETURN NULL; END IF;
  IF v_observed_at > clock_timestamp() THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'FUTURE_RIGHTS_OBSERVATION_DENIED';
  END IF;
  SELECT
      (SELECT count(*) FROM rights.rights_observation_provider_object x WHERE x.rights_observation_id = v_id)
    + (SELECT count(*) FROM rights.rights_observation_visual_reference x WHERE x.rights_observation_id = v_id)
    + (SELECT count(*) FROM rights.rights_observation_representation x WHERE x.rights_observation_id = v_id)
    + (SELECT count(*) FROM rights.rights_observation_locator x WHERE x.rights_observation_id = v_id)
  INTO v_count;
  IF v_count <> 1 OR NOT (CASE v_kind
    WHEN 'provider_object' THEN EXISTS (SELECT 1 FROM rights.rights_observation_provider_object x WHERE x.rights_observation_id = v_id)
    WHEN 'external_visual_reference' THEN EXISTS (SELECT 1 FROM rights.rights_observation_visual_reference x WHERE x.rights_observation_id = v_id)
    WHEN 'digital_representation' THEN EXISTS (SELECT 1 FROM rights.rights_observation_representation x WHERE x.rights_observation_id = v_id)
    WHEN 'visual_locator' THEN EXISTS (SELECT 1 FROM rights.rights_observation_locator x WHERE x.rights_observation_id = v_id)
    ELSE false
  END) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'RIGHTS_OBSERVATION_EXACTLY_ONE_TYPED_SUBJECT_REQUIRED';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER rights_observation_shape_from_parent
AFTER INSERT OR UPDATE OR DELETE ON rights.rights_observation
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_rights_observation_shape();
CREATE CONSTRAINT TRIGGER rights_observation_shape_from_provider_object
AFTER INSERT OR UPDATE OR DELETE ON rights.rights_observation_provider_object
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_rights_observation_shape();
CREATE CONSTRAINT TRIGGER rights_observation_shape_from_reference
AFTER INSERT OR UPDATE OR DELETE ON rights.rights_observation_visual_reference
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_rights_observation_shape();
CREATE CONSTRAINT TRIGGER rights_observation_shape_from_representation
AFTER INSERT OR UPDATE OR DELETE ON rights.rights_observation_representation
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_rights_observation_shape();
CREATE CONSTRAINT TRIGGER rights_observation_shape_from_locator
AFTER INSERT OR UPDATE OR DELETE ON rights.rights_observation_locator
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_rights_observation_shape();

CREATE FUNCTION rights.observation_subject_key(p_observation_id uuid)
RETURNS text
LANGUAGE plpgsql STABLE
SET search_path = pg_catalog
AS $function$
DECLARE v_kind rights.rights_subject_kind; v_target uuid;
BEGIN
  SELECT o.subject_kind INTO v_kind FROM rights.rights_observation o
  WHERE o.rights_observation_id = p_observation_id;
  IF v_kind = 'provider_object' THEN
    SELECT x.provider_object_id INTO v_target FROM rights.rights_observation_provider_object x WHERE x.rights_observation_id = p_observation_id;
  ELSIF v_kind = 'external_visual_reference' THEN
    SELECT x.external_visual_reference_id INTO v_target FROM rights.rights_observation_visual_reference x WHERE x.rights_observation_id = p_observation_id;
  ELSIF v_kind = 'digital_representation' THEN
    SELECT x.digital_representation_id INTO v_target FROM rights.rights_observation_representation x WHERE x.rights_observation_id = p_observation_id;
  ELSIF v_kind = 'visual_locator' THEN
    SELECT x.visual_locator_id INTO v_target FROM rights.rights_observation_locator x WHERE x.rights_observation_id = p_observation_id;
  END IF;
  RETURN v_kind::text || ':' || v_target::text;
END
$function$;

CREATE FUNCTION rights.assessment_subject_key(p_assessment_id uuid)
RETURNS text
LANGUAGE plpgsql STABLE
SET search_path = pg_catalog
AS $function$
DECLARE v_kind rights.rights_subject_kind; v_target uuid;
BEGIN
  SELECT a.subject_kind INTO v_kind FROM rights.rights_assessment a
  WHERE a.rights_assessment_id = p_assessment_id;
  IF v_kind = 'provider_object' THEN
    SELECT x.provider_object_id INTO v_target FROM rights.rights_assessment_provider_object x WHERE x.rights_assessment_id = p_assessment_id;
  ELSIF v_kind = 'external_visual_reference' THEN
    SELECT x.external_visual_reference_id INTO v_target FROM rights.rights_assessment_visual_reference x WHERE x.rights_assessment_id = p_assessment_id;
  ELSIF v_kind = 'digital_representation' THEN
    SELECT x.digital_representation_id INTO v_target FROM rights.rights_assessment_representation x WHERE x.rights_assessment_id = p_assessment_id;
  ELSIF v_kind = 'visual_locator' THEN
    SELECT x.visual_locator_id INTO v_target FROM rights.rights_assessment_locator x WHERE x.rights_assessment_id = p_assessment_id;
  END IF;
  RETURN v_kind::text || ':' || v_target::text;
END
$function$;

CREATE FUNCTION rights.enforce_rights_assessment()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := COALESCE(to_jsonb(NEW), to_jsonb(OLD));
  v_id uuid := (v_row ->> 'rights_assessment_id')::uuid;
  v_kind rights.rights_subject_kind;
  v_state rights.rights_evidence_state;
  v_count integer;
  v_assessed_at timestamptz;
BEGIN
  SELECT a.subject_kind, a.assessed_state, a.assessed_at
  INTO v_kind, v_state, v_assessed_at
  FROM rights.rights_assessment a WHERE a.rights_assessment_id = v_id;
  IF NOT FOUND THEN RETURN NULL; END IF;
  IF v_assessed_at > clock_timestamp() THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'FUTURE_RIGHTS_ASSESSMENT_DENIED';
  END IF;
  SELECT
      (SELECT count(*) FROM rights.rights_assessment_provider_object x WHERE x.rights_assessment_id = v_id)
    + (SELECT count(*) FROM rights.rights_assessment_visual_reference x WHERE x.rights_assessment_id = v_id)
    + (SELECT count(*) FROM rights.rights_assessment_representation x WHERE x.rights_assessment_id = v_id)
    + (SELECT count(*) FROM rights.rights_assessment_locator x WHERE x.rights_assessment_id = v_id)
  INTO v_count;
  IF v_count <> 1 OR NOT (CASE v_kind
    WHEN 'provider_object' THEN EXISTS (SELECT 1 FROM rights.rights_assessment_provider_object x WHERE x.rights_assessment_id = v_id)
    WHEN 'external_visual_reference' THEN EXISTS (SELECT 1 FROM rights.rights_assessment_visual_reference x WHERE x.rights_assessment_id = v_id)
    WHEN 'digital_representation' THEN EXISTS (SELECT 1 FROM rights.rights_assessment_representation x WHERE x.rights_assessment_id = v_id)
    WHEN 'visual_locator' THEN EXISTS (SELECT 1 FROM rights.rights_assessment_locator x WHERE x.rights_assessment_id = v_id)
    ELSE false
  END) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'RIGHTS_ASSESSMENT_EXACTLY_ONE_TYPED_SUBJECT_REQUIRED';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM rights.rights_assessment_observation x
    WHERE x.rights_assessment_id = v_id
  ) OR EXISTS (
    SELECT 1 FROM rights.rights_assessment_observation x
    JOIN rights.rights_observation o
      ON o.rights_observation_id = x.rights_observation_id
    WHERE x.rights_assessment_id = v_id
      AND (
        rights.observation_subject_key(x.rights_observation_id)
          IS DISTINCT FROM rights.assessment_subject_key(v_id)
        OR o.observed_at > (
          SELECT a.assessed_at FROM rights.rights_assessment a
          WHERE a.rights_assessment_id = v_id
        )
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'RIGHTS_ASSESSMENT_REQUIRES_MATCHING_OBSERVATION';
  END IF;
  IF v_state = 'permitted' AND NOT EXISTS (
    SELECT 1 FROM rights.rights_assessment_observation x
    JOIN rights.rights_observation o
      ON o.rights_observation_id = x.rights_observation_id
    WHERE x.rights_assessment_id = v_id
      AND x.evidence_role = 'supports'
      AND o.evidence_state = 'permitted'
      AND o.evidence_item_id IS NOT NULL
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'PERMITTED_RIGHTS_REQUIRES_EVIDENCE_OBSERVATION';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER rights_assessment_from_assessment
AFTER INSERT OR UPDATE OR DELETE ON rights.rights_assessment
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_rights_assessment();
CREATE CONSTRAINT TRIGGER rights_assessment_from_provider_object
AFTER INSERT OR UPDATE OR DELETE ON rights.rights_assessment_provider_object
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_rights_assessment();
CREATE CONSTRAINT TRIGGER rights_assessment_from_reference
AFTER INSERT OR UPDATE OR DELETE ON rights.rights_assessment_visual_reference
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_rights_assessment();
CREATE CONSTRAINT TRIGGER rights_assessment_from_representation
AFTER INSERT OR UPDATE OR DELETE ON rights.rights_assessment_representation
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_rights_assessment();
CREATE CONSTRAINT TRIGGER rights_assessment_from_locator
AFTER INSERT OR UPDATE OR DELETE ON rights.rights_assessment_locator
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_rights_assessment();
CREATE CONSTRAINT TRIGGER rights_assessment_from_observation_bridge
AFTER INSERT OR UPDATE OR DELETE ON rights.rights_assessment_observation
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_rights_assessment();

CREATE FUNCTION rights.policy_rank(p_state rights.policy_state)
RETURNS integer
LANGUAGE sql IMMUTABLE
SET search_path = pg_catalog
RETURN CASE p_state
  WHEN 'remote_display_allowed' THEN 4
  WHEN 'source_viewer_only' THEN 3
  WHEN 'link_only' THEN 2
  WHEN 'citation_only' THEN 1
  WHEN 'disallowed' THEN 1
  ELSE 1
END;

CREATE FUNCTION rights.delivery_rank(p_mode rights.delivery_mode)
RETURNS integer
LANGUAGE sql IMMUTABLE
SET search_path = pg_catalog
RETURN CASE p_mode
  WHEN 'remote_image' THEN 4
  WHEN 'source_viewer' THEN 3
  WHEN 'link_only' THEN 2
  WHEN 'citation_only' THEN 1
  WHEN 'blocked' THEN 0
END;

CREATE FUNCTION rights.validate_one_provider_policy_evaluation(p_evaluation_id uuid)
RETURNS void
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_id uuid := p_evaluation_id;
  v_state rights.policy_state;
  v_bridge uuid;
  v_provider uuid;
  v_count integer;
  v_evaluated_at timestamptz;
BEGIN
  SELECT e.evaluated_state, e.object_visual_reference_id, e.evaluated_at
  INTO v_state, v_bridge, v_evaluated_at
  FROM rights.provider_policy_evaluation e
  WHERE e.provider_policy_evaluation_id = v_id;
  IF NOT FOUND THEN RETURN; END IF;
  IF v_evaluated_at > clock_timestamp() THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'FUTURE_PROVIDER_POLICY_EVALUATION_DENIED';
  END IF;

  SELECT po.provider_id INTO v_provider
  FROM rights.object_visual_reference b
  JOIN rights.external_visual_reference vr
    ON vr.external_visual_reference_id = b.external_visual_reference_id
  LEFT JOIN rights.provider_object po ON po.provider_object_id = vr.provider_object_id
  WHERE b.object_visual_reference_id = v_bridge;

  SELECT count(*) INTO v_count
  FROM rights.provider_policy_evaluation_version x
  WHERE x.provider_policy_evaluation_id = v_id;

  IF v_provider IS NULL THEN
    IF v_count <> 0 OR v_state NOT IN ('unknown', 'missing') THEN
      RAISE EXCEPTION USING ERRCODE = '23514',
        MESSAGE = 'UNMAPPED_PROVIDER_POLICY_MUST_FAIL_CLOSED';
    END IF;
  ELSIF v_state IN ('unknown', 'missing') THEN
    IF v_count <> 0 THEN
      RAISE EXCEPTION USING ERRCODE = '23514',
        MESSAGE = 'UNKNOWN_OR_MISSING_POLICY_MUST_NOT_CLAIM_VERSION';
    END IF;
  ELSIF v_count = 0 OR EXISTS (
    SELECT 1
    FROM rights.provider_policy_evaluation_version x
    JOIN rights.provider_policy_version pv
      ON pv.provider_policy_version_id = x.provider_policy_version_id
    WHERE x.provider_policy_evaluation_id = v_id
      AND (
        pv.provider_id IS DISTINCT FROM v_provider
        OR rights.policy_rank(v_state) > rights.policy_rank(pv.policy_state)
        OR (v_state = 'remote_display_allowed'
          AND pv.source_evidence_item_id IS NULL)
        OR (v_state NOT IN ('stale', 'conflict') AND (
          pv.effective_from > v_evaluated_at
          OR (pv.effective_until IS NOT NULL
            AND pv.effective_until <= v_evaluated_at)
          OR pv.review_due <= v_evaluated_at
        ))
      )
  ) OR EXISTS (
    SELECT 1
    FROM rights.provider_policy_version pv
    WHERE pv.provider_id = v_provider
      AND pv.effective_from <= v_evaluated_at
      AND (pv.effective_until IS NULL OR pv.effective_until > v_evaluated_at)
      AND NOT EXISTS (
        SELECT 1 FROM rights.provider_policy_evaluation_version x
        WHERE x.provider_policy_evaluation_id = v_id
          AND x.provider_policy_version_id = pv.provider_policy_version_id
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'PROVIDER_POLICY_EVALUATION_PROVIDER_CAP_OR_COMPLETENESS_VIOLATION';
  END IF;
  RETURN;
END
$function$;

CREATE FUNCTION rights.enforce_provider_policy_evaluation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := COALESCE(to_jsonb(NEW), to_jsonb(OLD));
  v_id uuid := (v_row ->> 'provider_policy_evaluation_id')::uuid;
BEGIN
  PERFORM rights.validate_one_provider_policy_evaluation(v_id);
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER provider_policy_evaluation_from_parent
AFTER INSERT OR UPDATE OR DELETE ON rights.provider_policy_evaluation
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_provider_policy_evaluation();
CREATE CONSTRAINT TRIGGER provider_policy_evaluation_from_version
AFTER INSERT OR UPDATE OR DELETE ON rights.provider_policy_evaluation_version
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_provider_policy_evaluation();

CREATE FUNCTION rights.enforce_takedown_scope_shape()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := COALESCE(to_jsonb(NEW), to_jsonb(OLD));
  v_id uuid := (v_row ->> 'takedown_scope_id')::uuid;
  v_kind rights.takedown_scope_kind;
  v_count integer;
BEGIN
  SELECT s.scope_kind INTO v_kind FROM rights.takedown_scope s
  WHERE s.takedown_scope_id = v_id;
  IF NOT FOUND THEN RETURN NULL; END IF;
  SELECT
      (SELECT count(*) FROM rights.takedown_scope_provider x WHERE x.takedown_scope_id = v_id)
    + (SELECT count(*) FROM rights.takedown_scope_provider_object x WHERE x.takedown_scope_id = v_id)
    + (SELECT count(*) FROM rights.takedown_scope_visual_reference x WHERE x.takedown_scope_id = v_id)
    + (SELECT count(*) FROM rights.takedown_scope_representation x WHERE x.takedown_scope_id = v_id)
    + (SELECT count(*) FROM rights.takedown_scope_locator x WHERE x.takedown_scope_id = v_id)
    + (SELECT count(*) FROM rights.takedown_scope_object_visual_reference x WHERE x.takedown_scope_id = v_id)
  INTO v_count;
  IF v_count <> 1 OR NOT (CASE v_kind
    WHEN 'provider' THEN EXISTS (SELECT 1 FROM rights.takedown_scope_provider x WHERE x.takedown_scope_id = v_id)
    WHEN 'provider_object' THEN EXISTS (SELECT 1 FROM rights.takedown_scope_provider_object x WHERE x.takedown_scope_id = v_id)
    WHEN 'external_visual_reference' THEN EXISTS (SELECT 1 FROM rights.takedown_scope_visual_reference x WHERE x.takedown_scope_id = v_id)
    WHEN 'digital_representation' THEN EXISTS (SELECT 1 FROM rights.takedown_scope_representation x WHERE x.takedown_scope_id = v_id)
    WHEN 'visual_locator' THEN EXISTS (SELECT 1 FROM rights.takedown_scope_locator x WHERE x.takedown_scope_id = v_id)
    WHEN 'object_visual_reference' THEN EXISTS (SELECT 1 FROM rights.takedown_scope_object_visual_reference x WHERE x.takedown_scope_id = v_id)
    ELSE false
  END) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'TAKEDOWN_SCOPE_EXACTLY_ONE_TYPED_TARGET_REQUIRED';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM rights.takedown_override o
    WHERE o.takedown_scope_id = v_id
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'TAKEDOWN_SCOPE_REQUIRES_RESTRICTIVE_OVERRIDE';
  END IF;
  RETURN NULL;
END
$function$;

CREATE FUNCTION rights.enforce_takedown_event_scope()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := COALESCE(to_jsonb(NEW), to_jsonb(OLD));
  v_event_id uuid := (v_row ->> 'takedown_event_id')::uuid;
BEGIN
  IF EXISTS (
    SELECT 1 FROM rights.takedown_event e
    WHERE e.takedown_event_id = v_event_id
      AND NOT EXISTS (
        SELECT 1 FROM rights.takedown_scope s
        WHERE s.takedown_event_id = e.takedown_event_id
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'TAKEDOWN_EVENT_REQUIRES_ONE_OR_MORE_SCOPES';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER takedown_scope_shape_from_parent
AFTER INSERT OR UPDATE OR DELETE ON rights.takedown_scope
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_takedown_scope_shape();
CREATE CONSTRAINT TRIGGER takedown_scope_shape_from_visual
AFTER INSERT OR UPDATE OR DELETE ON rights.takedown_scope_visual_reference
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_takedown_scope_shape();
CREATE CONSTRAINT TRIGGER takedown_scope_shape_from_provider
AFTER INSERT OR UPDATE OR DELETE ON rights.takedown_scope_provider
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_takedown_scope_shape();
CREATE CONSTRAINT TRIGGER takedown_scope_shape_from_provider_object
AFTER INSERT OR UPDATE OR DELETE ON rights.takedown_scope_provider_object
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_takedown_scope_shape();
CREATE CONSTRAINT TRIGGER takedown_scope_shape_from_representation
AFTER INSERT OR UPDATE OR DELETE ON rights.takedown_scope_representation
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_takedown_scope_shape();
CREATE CONSTRAINT TRIGGER takedown_scope_shape_from_locator
AFTER INSERT OR UPDATE OR DELETE ON rights.takedown_scope_locator
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_takedown_scope_shape();
CREATE CONSTRAINT TRIGGER takedown_scope_shape_from_bridge
AFTER INSERT OR UPDATE OR DELETE ON rights.takedown_scope_object_visual_reference
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_takedown_scope_shape();
CREATE CONSTRAINT TRIGGER takedown_event_has_scope_from_event
AFTER INSERT OR UPDATE OR DELETE ON rights.takedown_event
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_takedown_event_scope();
CREATE CONSTRAINT TRIGGER takedown_event_has_scope_from_scope
AFTER INSERT OR UPDATE OR DELETE ON rights.takedown_scope
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_takedown_event_scope();

CREATE FUNCTION rights.scope_matches_bridge(
  p_scope_id uuid,
  p_bridge_id uuid
)
RETURNS boolean
LANGUAGE plpgsql STABLE
SET search_path = pg_catalog
AS $function$
DECLARE
  v_kind rights.takedown_scope_kind;
  v_reference_id uuid;
  v_provider_object_id uuid;
  v_provider_id uuid;
BEGIN
  SELECT s.scope_kind, b.external_visual_reference_id,
    vr.provider_object_id, po.provider_id
  INTO v_kind, v_reference_id, v_provider_object_id, v_provider_id
  FROM rights.takedown_scope s
  CROSS JOIN rights.object_visual_reference b
  JOIN rights.external_visual_reference vr
    ON vr.external_visual_reference_id = b.external_visual_reference_id
  LEFT JOIN rights.provider_object po ON po.provider_object_id = vr.provider_object_id
  WHERE s.takedown_scope_id = p_scope_id
    AND b.object_visual_reference_id = p_bridge_id;
  IF NOT FOUND THEN RETURN false; END IF;
  RETURN CASE v_kind
    WHEN 'provider' THEN EXISTS (
      SELECT 1 FROM rights.takedown_scope_provider x
      WHERE x.takedown_scope_id = p_scope_id AND x.provider_id = v_provider_id)
    WHEN 'provider_object' THEN EXISTS (
      SELECT 1 FROM rights.takedown_scope_provider_object x
      WHERE x.takedown_scope_id = p_scope_id AND x.provider_object_id = v_provider_object_id)
    WHEN 'external_visual_reference' THEN EXISTS (
      SELECT 1 FROM rights.takedown_scope_visual_reference x
      WHERE x.takedown_scope_id = p_scope_id AND x.external_visual_reference_id = v_reference_id)
    WHEN 'digital_representation' THEN EXISTS (
      SELECT 1 FROM rights.takedown_scope_representation x
      JOIN rights.visual_reference_representation r
        ON r.digital_representation_id = x.digital_representation_id
      WHERE x.takedown_scope_id = p_scope_id
        AND r.external_visual_reference_id = v_reference_id)
    WHEN 'visual_locator' THEN EXISTS (
      SELECT 1 FROM rights.takedown_scope_locator x
      JOIN rights.visual_locator l ON l.visual_locator_id = x.visual_locator_id
      WHERE x.takedown_scope_id = p_scope_id
        AND l.external_visual_reference_id = v_reference_id)
    WHEN 'object_visual_reference' THEN EXISTS (
      SELECT 1 FROM rights.takedown_scope_object_visual_reference x
      WHERE x.takedown_scope_id = p_scope_id
        AND x.object_visual_reference_id = p_bridge_id)
    ELSE false
  END;
END
$function$;

CREATE FUNCTION rights.subject_applies_to_delivery(
  p_subject_kind rights.rights_subject_kind,
  p_subject_id uuid,
  p_bridge_id uuid,
  p_delivery_id uuid
)
RETURNS boolean
LANGUAGE plpgsql STABLE
SET search_path = pg_catalog
AS $function$
DECLARE v_reference_id uuid; v_provider_object_id uuid;
BEGIN
  SELECT b.external_visual_reference_id, vr.provider_object_id
  INTO v_reference_id, v_provider_object_id
  FROM rights.object_visual_reference b
  JOIN rights.external_visual_reference vr
    ON vr.external_visual_reference_id = b.external_visual_reference_id
  WHERE b.object_visual_reference_id = p_bridge_id;
  RETURN CASE p_subject_kind
    WHEN 'provider_object' THEN p_subject_id = v_provider_object_id
    WHEN 'external_visual_reference' THEN p_subject_id = v_reference_id
    WHEN 'digital_representation' THEN EXISTS (
      SELECT 1
      FROM rights.delivery_locator_qualification q
      JOIN rights.visual_locator_representation r
        ON r.visual_locator_id = q.visual_locator_id
      WHERE q.delivery_assessment_id = p_delivery_id
        AND r.external_visual_reference_id = v_reference_id
        AND r.digital_representation_id = p_subject_id)
    WHEN 'visual_locator' THEN EXISTS (
      SELECT 1 FROM rights.delivery_locator_qualification q
      JOIN rights.visual_locator l ON l.visual_locator_id = q.visual_locator_id
      WHERE q.delivery_assessment_id = p_delivery_id
        AND q.visual_locator_id = p_subject_id
        AND l.external_visual_reference_id = v_reference_id)
    ELSE false
  END;
END
$function$;

CREATE FUNCTION rights.takedown_scope_target_key(p_scope_id uuid)
RETURNS uuid
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN (
  SELECT COALESCE(p.provider_id, po.provider_object_id,
    vr.external_visual_reference_id, dr.digital_representation_id,
    vl.visual_locator_id, ov.object_visual_reference_id)
  FROM rights.takedown_scope s
  LEFT JOIN rights.takedown_scope_provider p
    ON p.takedown_scope_id = s.takedown_scope_id
  LEFT JOIN rights.takedown_scope_provider_object po
    ON po.takedown_scope_id = s.takedown_scope_id
  LEFT JOIN rights.takedown_scope_visual_reference vr
    ON vr.takedown_scope_id = s.takedown_scope_id
  LEFT JOIN rights.takedown_scope_representation dr
    ON dr.takedown_scope_id = s.takedown_scope_id
  LEFT JOIN rights.takedown_scope_locator vl
    ON vl.takedown_scope_id = s.takedown_scope_id
  LEFT JOIN rights.takedown_scope_object_visual_reference ov
    ON ov.takedown_scope_id = s.takedown_scope_id
  WHERE s.takedown_scope_id = p_scope_id
);

CREATE FUNCTION rights.enforce_takedown_override()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := COALESCE(to_jsonb(NEW), to_jsonb(OLD));
  v_id uuid := (v_row ->> 'takedown_override_id')::uuid;
BEGIN
  IF EXISTS (
    SELECT 1
    FROM rights.takedown_override o
    JOIN rights.takedown_scope s ON s.takedown_scope_id = o.takedown_scope_id
    JOIN rights.takedown_event e ON e.takedown_event_id = s.takedown_event_id
    WHERE o.takedown_override_id = v_id
      AND e.action = 'blocked' AND o.restrictive_mode <> 'blocked'
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'TAKEDOWN_OVERRIDE_CANNOT_WEAKEN_EVENT';
  END IF;
  IF EXISTS (
    SELECT 1 FROM rights.takedown_override o
    JOIN rights.takedown_override p
      ON p.takedown_override_id = o.supersedes_takedown_override_id
    WHERE o.takedown_override_id = v_id
      AND (o.takedown_scope_id IS DISTINCT FROM p.takedown_scope_id
        OR rights.delivery_rank(o.restrictive_mode)
          > rights.delivery_rank(p.restrictive_mode))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'TAKEDOWN_OVERRIDE_SUPERSESSION_CANNOT_REPARENT_OR_WEAKEN';
  END IF;
  IF EXISTS (
    SELECT 1 FROM rights.takedown_override o
    WHERE o.takedown_override_id = v_id
      AND o.overlay_sha256 IS DISTINCT FROM
        rights.compute_takedown_override_sha(o.takedown_override_id)
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'TAKEDOWN_OVERRIDE_DIGEST_MISMATCH';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER takedown_override_cannot_weaken_event
AFTER INSERT OR UPDATE ON rights.takedown_override
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_takedown_override();

CREATE FUNCTION rights.compute_attribution_bundle_sha(p_bundle_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN encode(sha256(convert_to(COALESCE((
  SELECT jsonb_agg(jsonb_build_array(
    v.value_kind, v.value_ordinal, v.language_tag, v.value_text
  ) ORDER BY v.value_kind, v.value_ordinal)::text
  FROM rights.attribution_bundle_value v
  WHERE v.attribution_bundle_id = p_bundle_id
), '[]'), 'UTF8')), 'hex')::core.sha256_hex;

CREATE FUNCTION rights.compute_delivery_rights_sha(p_delivery_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN encode(sha256(convert_to(COALESCE((
  SELECT jsonb_agg(jsonb_build_object(
    'assessmentId', a.rights_assessment_id,
    'subjectKind', a.subject_kind,
    'subjectId', rights.assessment_subject_key(a.rights_assessment_id),
    'state', a.assessed_state,
    'reviewer', a.reviewer_actor,
    'rationale', a.rationale,
    'assessedAtUs', (extract(epoch FROM a.assessed_at) * 1000000)::bigint,
    'observations', COALESCE((
      SELECT jsonb_agg(jsonb_build_object(
        'observationId', o.rights_observation_id,
        'subjectKind', o.subject_kind,
        'subjectId', rights.observation_subject_key(o.rights_observation_id),
        'state', o.evidence_state,
        'evidenceId', o.evidence_item_id,
        'evidence', CASE WHEN ei.evidence_item_id IS NULL THEN NULL ELSE
          jsonb_build_object(
            'sourceVersionId', ei.source_version_id,
            'sourceRecordId', ei.source_record_id,
            'locatorScheme', ei.locator_scheme,
            'internalLocator', ei.internal_locator,
            'spanStart', ei.span_start,
            'spanEnd', ei.span_end,
            'contentSha256', ei.content_sha256,
            'stableCitation', ei.stable_citation
          ) END,
        'wording', o.observed_wording,
        'observedAtUs', (extract(epoch FROM o.observed_at) * 1000000)::bigint,
        'role', ao.evidence_role
      ) ORDER BY o.rights_observation_id, ao.evidence_role)
      FROM rights.rights_assessment_observation ao
      JOIN rights.rights_observation o
        ON o.rights_observation_id = ao.rights_observation_id
      LEFT JOIN provenance.evidence_item ei
        ON ei.evidence_item_id = o.evidence_item_id
      WHERE ao.rights_assessment_id = a.rights_assessment_id
    ), '[]'::jsonb)
  ) ORDER BY a.rights_assessment_id)::text
  FROM rights.delivery_rights_assessment x
  JOIN rights.rights_assessment a ON a.rights_assessment_id = x.rights_assessment_id
  WHERE x.delivery_assessment_id = p_delivery_id
), '[]'), 'UTF8')), 'hex')::core.sha256_hex;

CREATE FUNCTION rights.compute_delivery_policy_sha(p_delivery_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN encode(sha256(convert_to(COALESCE((
  SELECT jsonb_agg(jsonb_build_object(
    'evaluationId', e.provider_policy_evaluation_id,
    'bridgeId', e.object_visual_reference_id,
    'state', e.evaluated_state,
    'evaluator', e.evaluator_actor,
    'evaluatedAtUs', (extract(epoch FROM e.evaluated_at) * 1000000)::bigint,
    'versions', COALESCE((
      SELECT jsonb_agg(jsonb_build_object(
        'versionId', pv.provider_policy_version_id,
        'providerId', pv.provider_id,
        'versionToken', pv.version_token,
        'policySha256', pv.policy_sha256,
        'policyState', pv.policy_state,
        'effectiveFromUs', (extract(epoch FROM pv.effective_from) * 1000000)::bigint,
        'effectiveUntilUs', CASE WHEN pv.effective_until IS NULL THEN NULL
          ELSE (extract(epoch FROM pv.effective_until) * 1000000)::bigint END,
        'reviewDueUs', (extract(epoch FROM pv.review_due) * 1000000)::bigint,
        'sourceEvidenceId', pv.source_evidence_item_id
        ,'sourceEvidence', CASE WHEN ei.evidence_item_id IS NULL THEN NULL ELSE
          jsonb_build_object(
            'sourceVersionId', ei.source_version_id,
            'sourceRecordId', ei.source_record_id,
            'locatorScheme', ei.locator_scheme,
            'internalLocator', ei.internal_locator,
            'spanStart', ei.span_start,
            'spanEnd', ei.span_end,
            'contentSha256', ei.content_sha256,
            'stableCitation', ei.stable_citation
          ) END
      ) ORDER BY pv.provider_policy_version_id)
      FROM rights.provider_policy_evaluation_version v
      JOIN rights.provider_policy_version pv
        ON pv.provider_policy_version_id = v.provider_policy_version_id
      LEFT JOIN provenance.evidence_item ei
        ON ei.evidence_item_id = pv.source_evidence_item_id
      WHERE v.provider_policy_evaluation_id = e.provider_policy_evaluation_id
    ), '[]'::jsonb)
  ) ORDER BY e.provider_policy_evaluation_id)::text
  FROM rights.delivery_policy_evaluation x
  JOIN rights.provider_policy_evaluation e
    ON e.provider_policy_evaluation_id = x.provider_policy_evaluation_id
  WHERE x.delivery_assessment_id = p_delivery_id
), '[]'), 'UTF8')), 'hex')::core.sha256_hex;

CREATE FUNCTION rights.compute_health_observation_sha(p_health_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN (
  SELECT encode(sha256(convert_to(jsonb_build_array(
    h.endpoint_health_observation_id, h.visual_locator_id,
    h.health_state, h.method_version,
    (extract(epoch FROM h.checked_at) * 1000000)::bigint,
    CASE WHEN h.valid_until IS NULL THEN NULL
      ELSE (extract(epoch FROM h.valid_until) * 1000000)::bigint END,
    h.request_fingerprint
  )::text, 'UTF8')), 'hex')::core.sha256_hex
  FROM rights.endpoint_health_observation h
  WHERE h.endpoint_health_observation_id = p_health_id
);

CREATE FUNCTION rights.compute_takedown_override_sha(p_override_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN (
  SELECT encode(sha256(convert_to(jsonb_build_object(
    'overrideId', o.takedown_override_id,
    'scopeId', s.takedown_scope_id,
    'scopeKind', s.scope_kind,
    'scopeTarget', rights.takedown_scope_target_key(s.takedown_scope_id),
    'eventId', e.takedown_event_id,
    'action', e.action,
    'effectiveFromUs', (extract(epoch FROM e.effective_from) * 1000000)::bigint,
    'effectiveUntilUs', CASE WHEN e.effective_until IS NULL THEN NULL
      ELSE (extract(epoch FROM e.effective_until) * 1000000)::bigint END,
    'reasonCode', e.reason_code,
    'evidenceId', e.evidence_item_id,
    'restrictiveMode', o.restrictive_mode,
    'supersedesOverrideId', o.supersedes_takedown_override_id,
    'createdAtUs', (extract(epoch FROM o.created_at) * 1000000)::bigint
  )::text, 'UTF8')), 'hex')::core.sha256_hex
  FROM rights.takedown_override o
  JOIN rights.takedown_scope s ON s.takedown_scope_id = o.takedown_scope_id
  JOIN rights.takedown_event e ON e.takedown_event_id = s.takedown_event_id
  WHERE o.takedown_override_id = p_override_id
);

CREATE FUNCTION rights.compute_rights_observation_sha(p_observation_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN (
  SELECT encode(sha256(convert_to(jsonb_build_object(
    'observationId', o.rights_observation_id,
    'subjectKind', o.subject_kind,
    'subjectKey', rights.observation_subject_key(o.rights_observation_id),
    'state', o.evidence_state,
    'evidenceId', o.evidence_item_id,
    'wording', o.observed_wording,
    'observedAtUs', (extract(epoch FROM o.observed_at) * 1000000)::bigint,
    'evidence', CASE WHEN ei.evidence_item_id IS NULL THEN NULL ELSE
      jsonb_build_object(
        'sourceVersionId', ei.source_version_id,
        'sourceRecordId', ei.source_record_id,
        'locatorScheme', ei.locator_scheme,
        'internalLocator', ei.internal_locator,
        'spanStart', ei.span_start,
        'spanEnd', ei.span_end,
        'contentSha256', ei.content_sha256,
        'stableCitation', ei.stable_citation
      ) END
  )::text, 'UTF8')), 'hex')::core.sha256_hex
  FROM rights.rights_observation o
  LEFT JOIN provenance.evidence_item ei
    ON ei.evidence_item_id = o.evidence_item_id
  WHERE o.rights_observation_id = p_observation_id
);

CREATE FUNCTION rights.compute_rights_assessment_sha(p_assessment_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN (
  SELECT encode(sha256(convert_to(jsonb_build_object(
    'assessmentId', a.rights_assessment_id,
    'subjectKind', a.subject_kind,
    'subjectKey', rights.assessment_subject_key(a.rights_assessment_id),
    'state', a.assessed_state,
    'reviewer', a.reviewer_actor,
    'rationale', a.rationale,
    'assessedAtUs', (extract(epoch FROM a.assessed_at) * 1000000)::bigint,
    'observations', COALESCE((
      SELECT jsonb_agg(jsonb_build_object(
        'observationId', o.rights_observation_id,
        'subjectKind', o.subject_kind,
        'subjectKey', rights.observation_subject_key(o.rights_observation_id),
        'state', o.evidence_state,
        'evidenceId', o.evidence_item_id,
        'wording', o.observed_wording,
        'observedAtUs', (extract(epoch FROM o.observed_at) * 1000000)::bigint,
        'role', x.evidence_role,
        'evidence', CASE WHEN ei.evidence_item_id IS NULL THEN NULL ELSE
          jsonb_build_object(
            'sourceVersionId', ei.source_version_id,
            'sourceRecordId', ei.source_record_id,
            'locatorScheme', ei.locator_scheme,
            'internalLocator', ei.internal_locator,
            'spanStart', ei.span_start,
            'spanEnd', ei.span_end,
            'contentSha256', ei.content_sha256,
            'stableCitation', ei.stable_citation
          ) END
      ) ORDER BY o.rights_observation_id, x.evidence_role)
      FROM rights.rights_assessment_observation x
      JOIN rights.rights_observation o
        ON o.rights_observation_id = x.rights_observation_id
      LEFT JOIN provenance.evidence_item ei
        ON ei.evidence_item_id = o.evidence_item_id
      WHERE x.rights_assessment_id = a.rights_assessment_id
    ), '[]'::jsonb)
  )::text, 'UTF8')), 'hex')::core.sha256_hex
  FROM rights.rights_assessment a
  WHERE a.rights_assessment_id = p_assessment_id
);

CREATE OR REPLACE FUNCTION rights.compute_attribution_bundle_sha(p_bundle_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN (
  SELECT encode(sha256(convert_to(jsonb_build_object(
    'bundleId', a.attribution_bundle_id,
    'bridgeId', a.object_visual_reference_id,
    'state', a.attribution_state,
    'evidenceId', a.evidence_item_id,
    'validatedBy', a.validated_by,
    'validatedAtUs', (extract(epoch FROM a.validated_at) * 1000000)::bigint,
    'supersedesBundleId', a.supersedes_attribution_bundle_id,
    'values', COALESCE((
      SELECT jsonb_agg(jsonb_build_array(
        v.value_kind, v.value_ordinal, v.language_tag, v.value_text
      ) ORDER BY v.value_kind, v.value_ordinal)
      FROM rights.attribution_bundle_value v
      WHERE v.attribution_bundle_id = a.attribution_bundle_id
    ), '[]'::jsonb)
  )::text, 'UTF8')), 'hex')::core.sha256_hex
  FROM rights.attribution_bundle a
  WHERE a.attribution_bundle_id = p_bundle_id
);

CREATE FUNCTION rights.compute_provider_policy_evaluation_sha(p_evaluation_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN (
  SELECT encode(sha256(convert_to(jsonb_build_object(
    'evaluationId', e.provider_policy_evaluation_id,
    'bridgeId', e.object_visual_reference_id,
    'state', e.evaluated_state,
    'evaluator', e.evaluator_actor,
    'evaluatedAtUs', (extract(epoch FROM e.evaluated_at) * 1000000)::bigint,
    'versions', COALESCE((
      SELECT jsonb_agg(jsonb_build_object(
        'versionId', pv.provider_policy_version_id,
        'providerId', pv.provider_id,
        'versionToken', pv.version_token,
        'policySha256', pv.policy_sha256,
        'policyState', pv.policy_state,
        'effectiveFromUs', (extract(epoch FROM pv.effective_from) * 1000000)::bigint,
        'effectiveUntilUs', CASE WHEN pv.effective_until IS NULL THEN NULL
          ELSE (extract(epoch FROM pv.effective_until) * 1000000)::bigint END,
        'reviewDueUs', (extract(epoch FROM pv.review_due) * 1000000)::bigint,
        'sourceEvidenceId', pv.source_evidence_item_id,
        'sourceEvidence', CASE WHEN ei.evidence_item_id IS NULL THEN NULL ELSE
          jsonb_build_object(
            'sourceVersionId', ei.source_version_id,
            'sourceRecordId', ei.source_record_id,
            'locatorScheme', ei.locator_scheme,
            'internalLocator', ei.internal_locator,
            'spanStart', ei.span_start,
            'spanEnd', ei.span_end,
            'contentSha256', ei.content_sha256,
            'stableCitation', ei.stable_citation
          ) END
      ) ORDER BY pv.provider_policy_version_id)
      FROM rights.provider_policy_evaluation_version x
      JOIN rights.provider_policy_version pv
        ON pv.provider_policy_version_id = x.provider_policy_version_id
      LEFT JOIN provenance.evidence_item ei
        ON ei.evidence_item_id = pv.source_evidence_item_id
      WHERE x.provider_policy_evaluation_id = e.provider_policy_evaluation_id
    ), '[]'::jsonb)
  )::text, 'UTF8')), 'hex')::core.sha256_hex
  FROM rights.provider_policy_evaluation e
  WHERE e.provider_policy_evaluation_id = p_evaluation_id
);

CREATE OR REPLACE FUNCTION rights.compute_delivery_rights_sha(p_delivery_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN encode(sha256(convert_to(COALESCE((
  SELECT jsonb_agg(jsonb_build_array(
    x.rights_assessment_id, x.evidence_role,
    rights.compute_rights_assessment_sha(x.rights_assessment_id)
  ) ORDER BY x.rights_assessment_id, x.evidence_role)::text
  FROM rights.delivery_rights_assessment x
  WHERE x.delivery_assessment_id = p_delivery_id
), '[]'), 'UTF8')), 'hex')::core.sha256_hex;

CREATE OR REPLACE FUNCTION rights.compute_delivery_policy_sha(p_delivery_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN encode(sha256(convert_to(COALESCE((
  SELECT jsonb_agg(jsonb_build_array(
    x.provider_policy_evaluation_id,
    rights.compute_provider_policy_evaluation_sha(
      x.provider_policy_evaluation_id)
  ) ORDER BY x.provider_policy_evaluation_id)::text
  FROM rights.delivery_policy_evaluation x
  WHERE x.delivery_assessment_id = p_delivery_id
), '[]'), 'UTF8')), 'hex')::core.sha256_hex;

CREATE FUNCTION rights.compute_delivery_snapshot_sha(p_delivery_id uuid)
RETURNS core.sha256_hex
LANGUAGE sql STABLE
SET search_path = pg_catalog
RETURN (
  SELECT encode(sha256(convert_to(jsonb_build_object(
    'deliveryId', d.delivery_assessment_id,
    'bridgeId', d.object_visual_reference_id,
    'attributionBundleId', d.attribution_bundle_id,
    'mode', d.delivery_mode,
    'reasonCode', d.reason_code,
    'assessor', d.assessor_actor,
    'assessedAtUs', (extract(epoch FROM d.assessed_at) * 1000000)::bigint,
    'rightsSha256', rights.compute_delivery_rights_sha(d.delivery_assessment_id),
    'policySha256', rights.compute_delivery_policy_sha(d.delivery_assessment_id),
    'attributionSha256', CASE WHEN d.attribution_bundle_id IS NULL THEN NULL
      ELSE rights.compute_attribution_bundle_sha(d.attribution_bundle_id) END,
    'qualifications', COALESCE((
      SELECT jsonb_agg(jsonb_build_array(
        q.visual_locator_id, q.endpoint_health_observation_id,
        q.allowlisted_role,
        rights.compute_health_observation_sha(q.endpoint_health_observation_id)
      ) ORDER BY q.allowlisted_role, q.visual_locator_id)
      FROM rights.delivery_locator_qualification q
      WHERE q.delivery_assessment_id = d.delivery_assessment_id
    ), '[]'::jsonb)
  )::text, 'UTF8')), 'hex')::core.sha256_hex
  FROM rights.delivery_assessment d
  WHERE d.delivery_assessment_id = p_delivery_id
);

CREATE FUNCTION rights.validate_one_delivery_assessment(p_delivery_id uuid)
RETURNS void
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_id uuid := p_delivery_id;
  v_bridge uuid;
  v_mode rights.delivery_mode;
  v_assessed_at timestamptz;
  v_attribution uuid;
  v_rights_cap integer;
  v_policy_cap integer;
  v_attribution_cap integer;
  v_takedown_cap integer := 4;
  v_required_role rights.locator_role;
BEGIN
  SELECT d.object_visual_reference_id, d.delivery_mode, d.assessed_at,
    d.attribution_bundle_id
  INTO v_bridge, v_mode, v_assessed_at, v_attribution
  FROM rights.delivery_assessment d WHERE d.delivery_assessment_id = v_id;
  IF NOT FOUND THEN RETURN; END IF;
  IF v_assessed_at > clock_timestamp() THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'FUTURE_DELIVERY_ASSESSMENT_DENIED';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM rights.delivery_rights_assessment x
    WHERE x.delivery_assessment_id = v_id
  ) OR EXISTS (
    SELECT 1
    FROM rights.delivery_rights_assessment x
    JOIN rights.rights_assessment a ON a.rights_assessment_id = x.rights_assessment_id
    LEFT JOIN rights.rights_assessment_provider_object po
      ON po.rights_assessment_id = a.rights_assessment_id
    LEFT JOIN rights.rights_assessment_visual_reference vr
      ON vr.rights_assessment_id = a.rights_assessment_id
    LEFT JOIN rights.rights_assessment_representation rp
      ON rp.rights_assessment_id = a.rights_assessment_id
    LEFT JOIN rights.rights_assessment_locator lo
      ON lo.rights_assessment_id = a.rights_assessment_id
    WHERE x.delivery_assessment_id = v_id
      AND (
        NOT rights.subject_applies_to_delivery(
          a.subject_kind,
          COALESCE(po.provider_object_id, vr.external_visual_reference_id,
            rp.digital_representation_id, lo.visual_locator_id),
          v_bridge, v_id
        )
        OR a.assessed_at > v_assessed_at
        OR EXISTS (
          SELECT 1 FROM rights.rights_assessment newer
          WHERE newer.supersedes_rights_assessment_id = a.rights_assessment_id
        )
      )
  ) OR EXISTS (
    SELECT 1
    FROM rights.rights_assessment a
    LEFT JOIN rights.rights_assessment_provider_object po
      ON po.rights_assessment_id = a.rights_assessment_id
    LEFT JOIN rights.rights_assessment_visual_reference vr
      ON vr.rights_assessment_id = a.rights_assessment_id
    LEFT JOIN rights.rights_assessment_representation rp
      ON rp.rights_assessment_id = a.rights_assessment_id
    LEFT JOIN rights.rights_assessment_locator lo
      ON lo.rights_assessment_id = a.rights_assessment_id
    WHERE NOT EXISTS (
      SELECT 1 FROM rights.rights_assessment newer
      WHERE newer.supersedes_rights_assessment_id = a.rights_assessment_id
    )
      AND rights.subject_applies_to_delivery(
        a.subject_kind,
        COALESCE(po.provider_object_id, vr.external_visual_reference_id,
          rp.digital_representation_id, lo.visual_locator_id),
        v_bridge, v_id
      )
      AND NOT EXISTS (
        SELECT 1 FROM rights.delivery_rights_assessment linked
        WHERE linked.delivery_assessment_id = v_id
          AND linked.rights_assessment_id = a.rights_assessment_id
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'DELIVERY_REQUIRES_APPLICABLE_RIGHTS_ASSESSMENT';
  END IF;

  SELECT min(CASE
    WHEN x.evidence_role = 'contradicts' THEN 1
    WHEN x.evidence_role = 'contextualises' THEN 2
    WHEN a.assessed_state = 'permitted' THEN CASE
      WHEN a.subject_kind = 'digital_representation' THEN 2 ELSE 4 END
    WHEN a.assessed_state = 'restricted' THEN 1
    ELSE 2 END)
  INTO v_rights_cap
  FROM rights.delivery_rights_assessment x
  JOIN rights.rights_assessment a ON a.rights_assessment_id = x.rights_assessment_id
  WHERE x.delivery_assessment_id = v_id;

  IF NOT EXISTS (
    SELECT 1 FROM rights.delivery_policy_evaluation x
    WHERE x.delivery_assessment_id = v_id
  ) OR EXISTS (
    SELECT 1 FROM rights.delivery_policy_evaluation x
    JOIN rights.provider_policy_evaluation e
      ON e.provider_policy_evaluation_id = x.provider_policy_evaluation_id
    WHERE x.delivery_assessment_id = v_id
      AND (e.object_visual_reference_id IS DISTINCT FROM v_bridge
        OR e.evaluated_at > v_assessed_at
        OR EXISTS (
          SELECT 1 FROM rights.provider_policy_evaluation newer
          WHERE newer.supersedes_provider_policy_evaluation_id =
            e.provider_policy_evaluation_id
        ))
  ) OR EXISTS (
    SELECT 1 FROM rights.provider_policy_evaluation e
    WHERE e.object_visual_reference_id = v_bridge
      AND NOT EXISTS (
        SELECT 1 FROM rights.provider_policy_evaluation newer
        WHERE newer.supersedes_provider_policy_evaluation_id =
          e.provider_policy_evaluation_id
      )
      AND NOT EXISTS (
        SELECT 1 FROM rights.delivery_policy_evaluation linked
        WHERE linked.delivery_assessment_id = v_id
          AND linked.provider_policy_evaluation_id =
            e.provider_policy_evaluation_id
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'DELIVERY_REQUIRES_APPLICABLE_PROVIDER_POLICY_EVALUATION';
  END IF;

  SELECT min(rights.policy_rank(e.evaluated_state))
  INTO v_policy_cap
  FROM rights.delivery_policy_evaluation x
  JOIN rights.provider_policy_evaluation e
    ON e.provider_policy_evaluation_id = x.provider_policy_evaluation_id
  WHERE x.delivery_assessment_id = v_id;

  IF v_attribution IS NULL THEN
    v_attribution_cap := 2;
  ELSIF NOT EXISTS (
    SELECT 1 FROM rights.attribution_bundle a
    WHERE a.attribution_bundle_id = v_attribution
      AND a.object_visual_reference_id = v_bridge
      AND a.evidence_item_id IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM rights.attribution_bundle newer
        WHERE newer.supersedes_attribution_bundle_id = a.attribution_bundle_id
      )
      AND 1 = (
        SELECT count(*) FROM rights.attribution_bundle current_bundle
        WHERE current_bundle.object_visual_reference_id = v_bridge
          AND NOT EXISTS (
            SELECT 1 FROM rights.attribution_bundle newer
            WHERE newer.supersedes_attribution_bundle_id =
              current_bundle.attribution_bundle_id
          )
      )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'DELIVERY_ATTRIBUTION_BUNDLE_BRIDGE_MISMATCH';
  ELSIF EXISTS (
    SELECT 1 FROM rights.attribution_bundle a
    WHERE a.attribution_bundle_id = v_attribution
      AND a.validated_at > v_assessed_at
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'DELIVERY_ATTRIBUTION_POSTDATES_DECISION';
  ELSIF EXISTS (
    SELECT 1 FROM rights.attribution_bundle a
    WHERE a.attribution_bundle_id = v_attribution
      AND a.bundle_sha256 IS DISTINCT FROM
        rights.compute_attribution_bundle_sha(a.attribution_bundle_id)
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ATTRIBUTION_BUNDLE_HASH_MISMATCH';
  ELSIF EXISTS (
    SELECT 1 FROM rights.attribution_bundle a
    WHERE a.attribution_bundle_id = v_attribution
      AND a.attribution_state = 'complete'
      AND EXISTS (
        SELECT 1 FROM rights.attribution_bundle_value x
        WHERE x.attribution_bundle_id = a.attribution_bundle_id
          AND x.value_kind = 'attribution'
      )
      AND EXISTS (
        SELECT 1 FROM rights.attribution_bundle_value x
        WHERE x.attribution_bundle_id = a.attribution_bundle_id
          AND x.value_kind = 'required_statement'
      )
  ) THEN
    v_attribution_cap := 4;
  ELSE
    v_attribution_cap := 2;
  END IF;

  SELECT COALESCE(min(CASE e.action WHEN 'blocked' THEN 0 ELSE 1 END), 4)
  INTO v_takedown_cap
  FROM rights.takedown_event e
  JOIN rights.takedown_scope s ON s.takedown_event_id = e.takedown_event_id
  WHERE e.effective_from <= v_assessed_at
    AND (e.effective_until IS NULL OR e.effective_until > v_assessed_at)
    AND rights.scope_matches_bridge(s.takedown_scope_id, v_bridge);

  IF rights.delivery_rank(v_mode) > LEAST(
    v_rights_cap, v_policy_cap, v_attribution_cap, v_takedown_cap
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'DELIVERY_ASSESSMENT_EXCEEDS_FAIL_CLOSED_CAP';
  END IF;

  v_required_role := CASE v_mode
    WHEN 'link_only' THEN 'canonical_record'::rights.locator_role
    WHEN 'source_viewer' THEN 'source_viewer'::rights.locator_role
    WHEN 'remote_image' THEN 'direct_image'::rights.locator_role
    ELSE NULL
  END;

  IF EXISTS (
    SELECT 1
    FROM rights.delivery_locator_qualification q
    JOIN rights.visual_locator l ON l.visual_locator_id = q.visual_locator_id
    JOIN rights.endpoint_health_observation h
      ON h.endpoint_health_observation_id = q.endpoint_health_observation_id
    JOIN rights.object_visual_reference b ON b.object_visual_reference_id = v_bridge
    WHERE q.delivery_assessment_id = v_id
      AND (
        l.external_visual_reference_id IS DISTINCT FROM b.external_visual_reference_id
        OR l.locator_role IS DISTINCT FROM q.allowlisted_role
        OR h.visual_locator_id IS DISTINCT FROM l.visual_locator_id
        OR h.health_state <> 'healthy_fresh'
        OR h.checked_at > v_assessed_at
        OR h.valid_until IS NULL
        OR h.valid_until <= v_assessed_at
        OR EXISTS (
          SELECT 1 FROM rights.visual_locator newer
          WHERE newer.supersedes_visual_locator_id = l.visual_locator_id
        )
      )
  ) OR (v_required_role IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM rights.delivery_locator_qualification q
    WHERE q.delivery_assessment_id = v_id
      AND q.allowlisted_role = v_required_role
  )) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'DELIVERY_REQUIRES_MATCHING_HEALTHY_FRESH_TYPED_LOCATOR';
  END IF;
  RETURN;
END
$function$;

CREATE FUNCTION rights.enforce_delivery_assessment()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := COALESCE(to_jsonb(NEW), to_jsonb(OLD));
  v_id uuid := (v_row ->> 'delivery_assessment_id')::uuid;
BEGIN
  PERFORM rights.validate_one_delivery_assessment(v_id);
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER delivery_assessment_validation
AFTER INSERT OR UPDATE OR DELETE ON rights.delivery_assessment
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_delivery_assessment();
CREATE CONSTRAINT TRIGGER delivery_rights_validation
AFTER INSERT OR UPDATE OR DELETE ON rights.delivery_rights_assessment
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_delivery_assessment();
CREATE CONSTRAINT TRIGGER delivery_policy_validation
AFTER INSERT OR UPDATE OR DELETE ON rights.delivery_policy_evaluation
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_delivery_assessment();
CREATE CONSTRAINT TRIGGER delivery_locator_validation
AFTER INSERT OR UPDATE OR DELETE ON rights.delivery_locator_qualification
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION rights.enforce_delivery_assessment();

CREATE FUNCTION provenance.enforce_provenance_supersession_parent()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := pg_catalog.to_jsonb(NEW);
BEGIN
  IF TG_TABLE_NAME = 'source_version'
    AND v_row->>'supersedes_source_version_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM provenance.source_version prior
      WHERE prior.source_version_id = (v_row->>'supersedes_source_version_id')::uuid
        AND prior.source_document_id = (v_row->>'source_document_id')::uuid
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'SOURCE_VERSION_SUPERSESSION_PARENT_MISMATCH';
  ELSIF TG_TABLE_NAME = 'evidence_item'
    AND v_row->>'supersedes_evidence_item_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1
      FROM provenance.evidence_item prior
      JOIN provenance.source_version oldv ON oldv.source_version_id = prior.source_version_id
      JOIN provenance.source_version newv ON newv.source_version_id = (v_row->>'source_version_id')::uuid
      WHERE prior.evidence_item_id = (v_row->>'supersedes_evidence_item_id')::uuid
        AND oldv.source_document_id = newv.source_document_id
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'EVIDENCE_SUPERSESSION_SOURCE_MISMATCH';
  ELSIF TG_TABLE_NAME = 'assertion'
    AND v_row->>'supersedes_assertion_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM provenance.assertion prior
      WHERE prior.assertion_id = (v_row->>'supersedes_assertion_id')::uuid
        AND prior.assertion_predicate_id = (v_row->>'assertion_predicate_id')::uuid
        AND prior.subject_kind::text = v_row->>'subject_kind'
        AND prior.value_kind::text = v_row->>'value_kind'
        AND prior.status = 'superseded'
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ASSERTION_SUPERSESSION_IDENTITY_MISMATCH';
  ELSIF TG_TABLE_NAME = 'canonical_assignment'
    AND v_row->>'supersedes_assignment_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM provenance.canonical_assignment prior
      WHERE prior.canonical_assignment_id = (v_row->>'supersedes_assignment_id')::uuid
        AND prior.assignment_kind::text = v_row->>'assignment_kind'
        AND prior.status = 'superseded'
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ASSIGNMENT_SUPERSESSION_KIND_MISMATCH';
  ELSIF TG_TABLE_NAME = 'assignment_review_decision'
    AND v_row->>'supersedes_decision_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM provenance.assignment_review_decision prior
      WHERE prior.assignment_review_decision_id = (v_row->>'supersedes_decision_id')::uuid
        AND prior.canonical_assignment_id = (v_row->>'canonical_assignment_id')::uuid
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ASSIGNMENT_DECISION_SUPERSESSION_PARENT_MISMATCH';
  ELSIF TG_TABLE_NAME = 'assertion_review_decision'
    AND v_row->>'supersedes_decision_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM provenance.assertion_review_decision prior
      WHERE prior.assertion_review_decision_id = (v_row->>'supersedes_decision_id')::uuid
        AND prior.assertion_id = (v_row->>'assertion_id')::uuid
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ASSERTION_DECISION_SUPERSESSION_PARENT_MISMATCH';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER source_version_supersession_parent
AFTER INSERT ON provenance.source_version DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION provenance.enforce_provenance_supersession_parent();
CREATE CONSTRAINT TRIGGER evidence_supersession_parent
AFTER INSERT ON provenance.evidence_item DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION provenance.enforce_provenance_supersession_parent();
CREATE CONSTRAINT TRIGGER assertion_supersession_parent
AFTER INSERT ON provenance.assertion DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION provenance.enforce_provenance_supersession_parent();
CREATE CONSTRAINT TRIGGER assignment_supersession_parent
AFTER INSERT ON provenance.canonical_assignment DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION provenance.enforce_provenance_supersession_parent();
CREATE CONSTRAINT TRIGGER assignment_decision_supersession_parent
AFTER INSERT ON provenance.assignment_review_decision DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION provenance.enforce_provenance_supersession_parent();
CREATE CONSTRAINT TRIGGER assertion_decision_supersession_parent
AFTER INSERT ON provenance.assertion_review_decision DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION provenance.enforce_provenance_supersession_parent();

CREATE FUNCTION provenance.enforce_one_current_review_decision()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := to_jsonb(NEW);
  v_parent_id uuid;
  v_current_count integer;
BEGIN
  IF TG_TABLE_NAME = 'assertion_review_decision' THEN
    v_parent_id := (v_row ->> 'assertion_id')::uuid;
    SELECT count(*) INTO v_current_count
    FROM provenance.assertion_review_decision d
    WHERE d.assertion_id = v_parent_id
      AND NOT EXISTS (
        SELECT 1 FROM provenance.assertion_review_decision newer
        WHERE newer.supersedes_decision_id = d.assertion_review_decision_id);
    IF v_row ->> 'supersedes_decision_id' IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM provenance.assertion_review_decision prior
      WHERE prior.assertion_review_decision_id =
          (v_row ->> 'supersedes_decision_id')::uuid
        AND prior.assertion_id = v_parent_id
        AND prior.decided_at < (v_row ->> 'decided_at')::timestamptz
    ) THEN
      RAISE EXCEPTION USING ERRCODE = '23514',
        MESSAGE = 'ASSERTION_DECISION_SUPERSESSION_ORDER_MISMATCH';
    END IF;
  ELSE
    v_parent_id := (v_row ->> 'canonical_assignment_id')::uuid;
    SELECT count(*) INTO v_current_count
    FROM provenance.assignment_review_decision d
    WHERE d.canonical_assignment_id = v_parent_id
      AND NOT EXISTS (
        SELECT 1 FROM provenance.assignment_review_decision newer
        WHERE newer.supersedes_decision_id = d.assignment_review_decision_id);
    IF v_row ->> 'supersedes_decision_id' IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM provenance.assignment_review_decision prior
      WHERE prior.assignment_review_decision_id =
          (v_row ->> 'supersedes_decision_id')::uuid
        AND prior.canonical_assignment_id = v_parent_id
        AND prior.decided_at < (v_row ->> 'decided_at')::timestamptz
    ) THEN
      RAISE EXCEPTION USING ERRCODE = '23514',
        MESSAGE = 'ASSIGNMENT_DECISION_SUPERSESSION_ORDER_MISMATCH';
    END IF;
  END IF;
  IF v_current_count <> 1 THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'PROVENANCE_REVIEW_REQUIRES_ONE_CURRENT_DECISION';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER assertion_one_current_decision
AFTER INSERT ON provenance.assertion_review_decision
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION provenance.enforce_one_current_review_decision();
CREATE CONSTRAINT TRIGGER assignment_one_current_decision
AFTER INSERT ON provenance.assignment_review_decision
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION provenance.enforce_one_current_review_decision();

CREATE FUNCTION research.enforce_research_supersession_parent()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := pg_catalog.to_jsonb(NEW);
BEGIN
  IF TG_TABLE_NAME = 'claim_revision'
    AND v_row->>'supersedes_claim_revision_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM research.claim_revision prior
      WHERE prior.claim_revision_id = (v_row->>'supersedes_claim_revision_id')::uuid
        AND prior.claim_id = (v_row->>'claim_id')::uuid
        AND prior.status = 'superseded'
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'CLAIM_REVISION_SUPERSESSION_PARENT_MISMATCH';
  ELSIF TG_TABLE_NAME = 'semantic_relation'
    AND v_row->>'supersedes_semantic_relation_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM research.semantic_relation prior
      WHERE prior.semantic_relation_id = (v_row->>'supersedes_semantic_relation_id')::uuid
        AND prior.subject_endpoint_id = (v_row->>'subject_endpoint_id')::uuid
        AND prior.relation_type_id = (v_row->>'relation_type_id')::uuid
        AND prior.object_endpoint_id = (v_row->>'object_endpoint_id')::uuid
        AND prior.status = 'superseded'
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'RELATION_SUPERSESSION_IDENTITY_MISMATCH';
  ELSIF TG_TABLE_NAME = 'relation_review_decision'
    AND v_row->>'supersedes_decision_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM research.relation_review_decision prior
      WHERE prior.relation_review_decision_id = (v_row->>'supersedes_decision_id')::uuid
        AND prior.semantic_relation_id = (v_row->>'semantic_relation_id')::uuid
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'RELATION_DECISION_SUPERSESSION_PARENT_MISMATCH';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER claim_revision_supersession_parent
AFTER INSERT ON research.claim_revision DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION research.enforce_research_supersession_parent();
CREATE CONSTRAINT TRIGGER semantic_relation_supersession_parent
AFTER INSERT ON research.semantic_relation DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION research.enforce_research_supersession_parent();
CREATE CONSTRAINT TRIGGER relation_decision_supersession_parent
AFTER INSERT ON research.relation_review_decision DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION research.enforce_research_supersession_parent();

CREATE FUNCTION rights.enforce_rights_supersession_parent()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := pg_catalog.to_jsonb(NEW);
BEGIN
  IF TG_TABLE_NAME = 'rights_observation'
    AND v_row->>'supersedes_rights_observation_id' IS NOT NULL
    AND rights.observation_subject_key((v_row->>'supersedes_rights_observation_id')::uuid)
      IS DISTINCT FROM rights.observation_subject_key((v_row->>'rights_observation_id')::uuid) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'RIGHTS_OBSERVATION_SUPERSESSION_SUBJECT_MISMATCH';
  ELSIF TG_TABLE_NAME = 'rights_assessment'
    AND v_row->>'supersedes_rights_assessment_id' IS NOT NULL
    AND rights.assessment_subject_key((v_row->>'supersedes_rights_assessment_id')::uuid)
      IS DISTINCT FROM rights.assessment_subject_key((v_row->>'rights_assessment_id')::uuid) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'RIGHTS_ASSESSMENT_SUPERSESSION_SUBJECT_MISMATCH';
  ELSIF TG_TABLE_NAME = 'provider_policy_evaluation'
    AND v_row->>'supersedes_provider_policy_evaluation_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM rights.provider_policy_evaluation prior
      WHERE prior.provider_policy_evaluation_id = (v_row->>'supersedes_provider_policy_evaluation_id')::uuid
        AND prior.object_visual_reference_id = (v_row->>'object_visual_reference_id')::uuid
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'POLICY_EVALUATION_SUPERSESSION_BRIDGE_MISMATCH';
  ELSIF TG_TABLE_NAME = 'delivery_assessment'
    AND v_row->>'supersedes_delivery_assessment_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM rights.delivery_assessment prior
      WHERE prior.delivery_assessment_id = (v_row->>'supersedes_delivery_assessment_id')::uuid
        AND prior.object_visual_reference_id = (v_row->>'object_visual_reference_id')::uuid
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'DELIVERY_SUPERSESSION_BRIDGE_MISMATCH';
  ELSIF TG_TABLE_NAME = 'visual_locator'
    AND v_row->>'supersedes_visual_locator_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM rights.visual_locator prior
      WHERE prior.visual_locator_id = (v_row->>'supersedes_visual_locator_id')::uuid
        AND prior.external_visual_reference_id = (v_row->>'external_visual_reference_id')::uuid
        AND prior.locator_role::text = v_row->>'locator_role'
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'LOCATOR_SUPERSESSION_REFERENCE_ROLE_MISMATCH';
  ELSIF TG_TABLE_NAME = 'takedown_override'
    AND v_row->>'supersedes_takedown_override_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM rights.takedown_override prior
      WHERE prior.takedown_override_id = (v_row->>'supersedes_takedown_override_id')::uuid
        AND prior.takedown_scope_id = (v_row->>'takedown_scope_id')::uuid
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'TAKEDOWN_OVERRIDE_SUPERSESSION_SCOPE_MISMATCH';
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER rights_observation_supersession_parent
AFTER INSERT ON rights.rights_observation DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION rights.enforce_rights_supersession_parent();
CREATE CONSTRAINT TRIGGER rights_assessment_supersession_parent
AFTER INSERT ON rights.rights_assessment DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION rights.enforce_rights_supersession_parent();
CREATE CONSTRAINT TRIGGER policy_evaluation_supersession_parent
AFTER INSERT ON rights.provider_policy_evaluation DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION rights.enforce_rights_supersession_parent();
CREATE CONSTRAINT TRIGGER delivery_supersession_parent
AFTER INSERT ON rights.delivery_assessment DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION rights.enforce_rights_supersession_parent();
CREATE CONSTRAINT TRIGGER locator_supersession_parent
AFTER INSERT ON rights.visual_locator DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION rights.enforce_rights_supersession_parent();
CREATE CONSTRAINT TRIGGER takedown_override_supersession_parent
AFTER INSERT ON rights.takedown_override DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION rights.enforce_rights_supersession_parent();

CREATE FUNCTION workflow.validate_one_review_case(p_case_id uuid)
RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
DECLARE
  v_kind workflow.case_kind;
  v_total integer;
  v_expected integer;
BEGIN
  SELECT case_kind INTO v_kind FROM workflow.review_case
  WHERE review_case_id = p_case_id;
  IF NOT FOUND THEN RETURN; END IF;
  SELECT
    (SELECT count(*) FROM workflow.review_case_assertion x WHERE x.review_case_id = p_case_id) +
    (SELECT count(*) FROM workflow.review_case_assignment x WHERE x.review_case_id = p_case_id) +
    (SELECT count(*) FROM workflow.review_case_claim x WHERE x.review_case_id = p_case_id) +
    (SELECT count(*) FROM workflow.review_case_relation x WHERE x.review_case_id = p_case_id) +
    (SELECT count(*) FROM workflow.review_case_relation_type_literal x WHERE x.review_case_id = p_case_id) +
    (SELECT count(*) FROM workflow.review_case_rights_assessment x WHERE x.review_case_id = p_case_id)
  INTO v_total;
  v_expected := CASE v_kind
    WHEN 'assertion' THEN (SELECT count(*) FROM workflow.review_case_assertion x WHERE x.review_case_id = p_case_id)
    WHEN 'canonical_assignment' THEN (SELECT count(*) FROM workflow.review_case_assignment x WHERE x.review_case_id = p_case_id)
    WHEN 'claim_revision' THEN (SELECT count(*) FROM workflow.review_case_claim x WHERE x.review_case_id = p_case_id)
    WHEN 'semantic_relation' THEN (SELECT count(*) FROM workflow.review_case_relation x WHERE x.review_case_id = p_case_id)
    WHEN 'relation_type_literal' THEN (SELECT count(*) FROM workflow.review_case_relation_type_literal x WHERE x.review_case_id = p_case_id)
    WHEN 'rights_assessment' THEN (SELECT count(*) FROM workflow.review_case_rights_assessment x WHERE x.review_case_id = p_case_id)
  END;
  IF v_total <> 1 OR v_expected <> 1 THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'WORKFLOW_REVIEW_CASE_EXACT_SUBTYPE_VIOLATION';
  END IF;
END
$function$;

CREATE FUNCTION workflow.enforce_review_case_subtype()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
DECLARE v_new_id uuid; v_old_id uuid;
BEGIN
  IF TG_OP <> 'DELETE' THEN
    v_new_id := (to_jsonb(NEW) ->> 'review_case_id')::uuid;
    PERFORM workflow.validate_one_review_case(v_new_id);
  END IF;
  IF TG_OP <> 'INSERT' THEN
    v_old_id := (to_jsonb(OLD) ->> 'review_case_id')::uuid;
    IF v_old_id IS DISTINCT FROM v_new_id THEN
      PERFORM workflow.validate_one_review_case(v_old_id);
    END IF;
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER review_case_exact_subtype_parent
AFTER INSERT OR UPDATE ON workflow.review_case
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION workflow.enforce_review_case_subtype();
CREATE CONSTRAINT TRIGGER review_case_exact_subtype_assertion
AFTER INSERT OR UPDATE OR DELETE ON workflow.review_case_assertion
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION workflow.enforce_review_case_subtype();
CREATE CONSTRAINT TRIGGER review_case_exact_subtype_assignment
AFTER INSERT OR UPDATE OR DELETE ON workflow.review_case_assignment
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION workflow.enforce_review_case_subtype();
CREATE CONSTRAINT TRIGGER review_case_exact_subtype_claim
AFTER INSERT OR UPDATE OR DELETE ON workflow.review_case_claim
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION workflow.enforce_review_case_subtype();
CREATE CONSTRAINT TRIGGER review_case_exact_subtype_relation
AFTER INSERT OR UPDATE OR DELETE ON workflow.review_case_relation
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION workflow.enforce_review_case_subtype();
CREATE CONSTRAINT TRIGGER review_case_exact_subtype_relation_type
AFTER INSERT OR UPDATE OR DELETE ON workflow.review_case_relation_type_literal
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION workflow.enforce_review_case_subtype();
CREATE CONSTRAINT TRIGGER review_case_exact_subtype_rights
AFTER INSERT OR UPDATE OR DELETE ON workflow.review_case_rights_assessment
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION workflow.enforce_review_case_subtype();

CREATE FUNCTION audit.validate_one_decision_event(p_event_id uuid)
RETURNS void
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_kind audit.decision_kind;
  v_total integer;
  v_expected integer;
BEGIN
  SELECT decision_kind INTO v_kind
  FROM audit.decision_event
  WHERE decision_event_id = p_event_id;
  IF NOT FOUND THEN
    RETURN;
  END IF;

  SELECT
    (SELECT count(*) FROM audit.decision_event_assertion_review x
      WHERE x.decision_event_id = p_event_id) +
    (SELECT count(*) FROM audit.decision_event_assignment_review x
      WHERE x.decision_event_id = p_event_id) +
    (SELECT count(*) FROM audit.decision_event_claim_review x
      WHERE x.decision_event_id = p_event_id) +
    (SELECT count(*) FROM audit.decision_event_relation_review x
      WHERE x.decision_event_id = p_event_id) +
    (SELECT count(*) FROM audit.decision_event_rights_observation x
      WHERE x.decision_event_id = p_event_id) +
    (SELECT count(*) FROM audit.decision_event_rights_assessment x
      WHERE x.decision_event_id = p_event_id) +
    (SELECT count(*) FROM audit.decision_event_policy_evaluation x
      WHERE x.decision_event_id = p_event_id) +
    (SELECT count(*) FROM audit.decision_event_delivery_assessment x
      WHERE x.decision_event_id = p_event_id) +
    (SELECT count(*) FROM audit.decision_event_attribution_validation x
      WHERE x.decision_event_id = p_event_id) +
    (SELECT count(*) FROM audit.decision_event_takedown x
      WHERE x.decision_event_id = p_event_id) +
    (SELECT count(*) FROM audit.decision_event_visual_bridge_review x
      WHERE x.decision_event_id = p_event_id)
  INTO v_total;

  v_expected := CASE v_kind
    WHEN 'assertion_review' THEN
      (SELECT count(*) FROM audit.decision_event_assertion_review x
       WHERE x.decision_event_id = p_event_id)
    WHEN 'assignment_review' THEN
      (SELECT count(*) FROM audit.decision_event_assignment_review x
       WHERE x.decision_event_id = p_event_id)
    WHEN 'claim_review' THEN
      (SELECT count(*) FROM audit.decision_event_claim_review x
       WHERE x.decision_event_id = p_event_id)
    WHEN 'relation_review' THEN
      (SELECT count(*) FROM audit.decision_event_relation_review x
       WHERE x.decision_event_id = p_event_id)
    WHEN 'rights_observation' THEN
      (SELECT count(*) FROM audit.decision_event_rights_observation x
       WHERE x.decision_event_id = p_event_id)
    WHEN 'rights_assessment' THEN
      (SELECT count(*) FROM audit.decision_event_rights_assessment x
       WHERE x.decision_event_id = p_event_id)
    WHEN 'provider_policy_evaluation' THEN
      (SELECT count(*) FROM audit.decision_event_policy_evaluation x
       WHERE x.decision_event_id = p_event_id)
    WHEN 'delivery_assessment' THEN
      (SELECT count(*) FROM audit.decision_event_delivery_assessment x
       WHERE x.decision_event_id = p_event_id)
    WHEN 'attribution_validation' THEN
      (SELECT count(*) FROM audit.decision_event_attribution_validation x
       WHERE x.decision_event_id = p_event_id)
    WHEN 'takedown' THEN
      (SELECT count(*) FROM audit.decision_event_takedown x
       WHERE x.decision_event_id = p_event_id)
    WHEN 'visual_bridge_review' THEN
      (SELECT count(*) FROM audit.decision_event_visual_bridge_review x
       WHERE x.decision_event_id = p_event_id)
  END;
  IF v_total <> 1 OR v_expected <> 1 THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'AUDIT_DECISION_EVENT_EXACT_SUBTYPE_VIOLATION';
  END IF;
END
$function$;

CREATE FUNCTION audit.enforce_decision_event_subtype()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_new_id uuid;
  v_old_id uuid;
BEGIN
  IF TG_OP <> 'DELETE' THEN
    v_new_id := (to_jsonb(NEW) ->> 'decision_event_id')::uuid;
    PERFORM audit.validate_one_decision_event(v_new_id);
  END IF;
  IF TG_OP <> 'INSERT' THEN
    v_old_id := (to_jsonb(OLD) ->> 'decision_event_id')::uuid;
    IF v_old_id IS DISTINCT FROM v_new_id THEN
      PERFORM audit.validate_one_decision_event(v_old_id);
    END IF;
  END IF;
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER decision_event_exact_subtype_parent
AFTER INSERT OR UPDATE ON audit.decision_event
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION audit.enforce_decision_event_subtype();
CREATE CONSTRAINT TRIGGER decision_event_exact_subtype_assertion
AFTER INSERT OR UPDATE OR DELETE ON audit.decision_event_assertion_review
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION audit.enforce_decision_event_subtype();
CREATE CONSTRAINT TRIGGER decision_event_exact_subtype_assignment
AFTER INSERT OR UPDATE OR DELETE ON audit.decision_event_assignment_review
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION audit.enforce_decision_event_subtype();
CREATE CONSTRAINT TRIGGER decision_event_exact_subtype_claim
AFTER INSERT OR UPDATE OR DELETE ON audit.decision_event_claim_review
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION audit.enforce_decision_event_subtype();
CREATE CONSTRAINT TRIGGER decision_event_exact_subtype_relation
AFTER INSERT OR UPDATE OR DELETE ON audit.decision_event_relation_review
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION audit.enforce_decision_event_subtype();
CREATE CONSTRAINT TRIGGER decision_event_exact_subtype_observation
AFTER INSERT OR UPDATE OR DELETE ON audit.decision_event_rights_observation
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION audit.enforce_decision_event_subtype();
CREATE CONSTRAINT TRIGGER decision_event_exact_subtype_assessment
AFTER INSERT OR UPDATE OR DELETE ON audit.decision_event_rights_assessment
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION audit.enforce_decision_event_subtype();
CREATE CONSTRAINT TRIGGER decision_event_exact_subtype_policy
AFTER INSERT OR UPDATE OR DELETE ON audit.decision_event_policy_evaluation
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION audit.enforce_decision_event_subtype();
CREATE CONSTRAINT TRIGGER decision_event_exact_subtype_delivery
AFTER INSERT OR UPDATE OR DELETE ON audit.decision_event_delivery_assessment
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION audit.enforce_decision_event_subtype();
CREATE CONSTRAINT TRIGGER decision_event_exact_subtype_attribution
AFTER INSERT OR UPDATE OR DELETE ON audit.decision_event_attribution_validation
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION audit.enforce_decision_event_subtype();
CREATE CONSTRAINT TRIGGER decision_event_exact_subtype_takedown
AFTER INSERT OR UPDATE OR DELETE ON audit.decision_event_takedown
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION audit.enforce_decision_event_subtype();
CREATE CONSTRAINT TRIGGER decision_event_exact_subtype_visual_bridge
AFTER INSERT OR UPDATE OR DELETE ON audit.decision_event_visual_bridge_review
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION audit.enforce_decision_event_subtype();

RESET ROLE;
