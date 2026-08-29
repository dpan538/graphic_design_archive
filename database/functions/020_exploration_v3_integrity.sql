\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

CREATE FUNCTION exploration_v3.assert_vocabulary_object(
  p_object_kind text,
  p_object_id text
) RETURNS void
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_concept exploration_v3.concept%ROWTYPE;
  v_sense exploration_v3.concept_sense%ROWTYPE;
  v_concept_realm exploration_v3.realm;
  v_authority exploration_v3.governed_authority%ROWTYPE;
BEGIN
  IF p_object_kind = 'CONCEPT' THEN
    SELECT * INTO v_concept
    FROM exploration_v3.concept WHERE concept_id = p_object_id;
    IF NOT FOUND THEN RETURN; END IF;
    SELECT * INTO STRICT v_authority
    FROM exploration_v3.governed_authority
    WHERE authority_id = v_concept.authority_id;
    IF v_concept.lifecycle_state = 'ACTIVE'
      AND (NOT v_concept.association_eligible
        OR v_authority.authority_state <> 'FINAL') THEN
      RAISE EXCEPTION USING ERRCODE = '23514',
        MESSAGE = 'ACTIVE_CONCEPT_AUTHORITY_OR_ELIGIBILITY_INVALID';
    END IF;
    IF v_concept.realm = 'PRODUCTION'
      AND v_authority.authority_kind = 'SYNTHETIC_TEST_AUTHORITY' THEN
      RAISE EXCEPTION USING ERRCODE = '23514',
        MESSAGE = 'PRODUCTION_CONCEPT_SYNTHETIC_AUTHORITY_FORBIDDEN';
    END IF;
    RETURN;
  ELSIF p_object_kind <> 'CONCEPT_SENSE' THEN
    RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'VOCABULARY_OBJECT_KIND_INVALID';
  END IF;

  SELECT * INTO v_sense
  FROM exploration_v3.concept_sense WHERE sense_id = p_object_id;
  IF NOT FOUND THEN RETURN; END IF;
  SELECT realm INTO STRICT v_concept_realm
  FROM exploration_v3.concept WHERE concept_id = v_sense.concept_id;
  SELECT * INTO STRICT v_authority
  FROM exploration_v3.governed_authority
  WHERE authority_id = v_sense.authority_id;
  IF v_sense.realm <> v_concept_realm THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'CONCEPT_SENSE_REALM_MISMATCH';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM exploration_v3.concept_sense_scope ss
    JOIN exploration_v3.governed_scope gs ON gs.scope_id = ss.scope_id
    WHERE ss.sense_id = p_object_id AND gs.realm <> v_sense.realm
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'CONCEPT_SENSE_SCOPE_REALM_MISMATCH';
  END IF;
  IF v_sense.lifecycle_state = 'ACTIVE' AND (
    NOT v_sense.association_eligible
    OR v_authority.authority_state <> 'FINAL'
    OR NOT EXISTS (
      SELECT 1 FROM exploration_v3.concept_sense_scope
      WHERE sense_id = p_object_id)
    OR NOT EXISTS (
      SELECT 1 FROM exploration_v3.aggregate_seal
      WHERE aggregate_kind = 'CONCEPT_SENSE' AND aggregate_id = p_object_id)
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ACTIVE_CONCEPT_SENSE_AUTHORITY_ELIGIBILITY_OR_SCOPE_INVALID';
  END IF;
  IF v_sense.realm = 'PRODUCTION'
    AND v_authority.authority_kind = 'SYNTHETIC_TEST_AUTHORITY' THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'PRODUCTION_CONCEPT_SENSE_SYNTHETIC_AUTHORITY_FORBIDDEN';
  END IF;
END
$function$;

CREATE FUNCTION exploration_v3.enforce_vocabulary_object()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
BEGIN
  IF TG_TABLE_NAME = 'concept' THEN
    PERFORM exploration_v3.assert_vocabulary_object(
      'CONCEPT', COALESCE(NEW.concept_id, OLD.concept_id));
  ELSIF TG_TABLE_NAME = 'concept_sense' THEN
    PERFORM exploration_v3.assert_vocabulary_object(
      'CONCEPT_SENSE', COALESCE(NEW.sense_id, OLD.sense_id));
  ELSE
    PERFORM exploration_v3.assert_vocabulary_object(
      'CONCEPT_SENSE', COALESCE(NEW.sense_id, OLD.sense_id));
  END IF;
  RETURN NULL;
END
$function$;

-- The governed association identifier is the prefix of the exact v3 semantic
-- identity digest.  Scope set arrays and unordered participants are sorted
-- here, so callers cannot smuggle storage order into identity.
CREATE FUNCTION exploration_v3.association_identity_sha(
  p_association_kind exploration_v3.association_kind,
  p_order_semantics exploration_v3.order_semantics,
  p_roles_meaningful boolean,
  p_scope_id text,
  p_concept_ids text[],
  p_sense_ids text[],
  p_ordinals integer[],
  p_role_ids text[]
) RETURNS core.sha256_hex
LANGUAGE plpgsql STABLE STRICT
SET search_path = pg_catalog
AS $function$
DECLARE
  v_scope exploration_v3.governed_scope%ROWTYPE;
  v_count integer := cardinality(p_concept_ids);
  v_participants jsonb;
  v_scope_identity jsonb;
BEGIN
  IF v_count IS NULL OR v_count < 2
    OR cardinality(p_sense_ids) <> v_count
    OR cardinality(p_ordinals) <> v_count
    OR cardinality(p_role_ids) <> v_count
    OR (p_association_kind = 'PAIR' AND v_count <> 2)
    OR (p_association_kind = 'HIGHER_ORDER' AND v_count < 3) THEN
    RAISE EXCEPTION USING ERRCODE = '22023',
      MESSAGE = 'ASSOCIATION_IDENTITY_PARTICIPANT_SHAPE_INVALID';
  END IF;
  IF p_order_semantics = 'ORDERED' AND (
      EXISTS (SELECT 1 FROM generate_subscripts(p_ordinals, 1) g
        WHERE p_ordinals[g] IS NULL)
      OR (SELECT min(p_ordinals[g]) FROM generate_subscripts(p_ordinals, 1) g) <> 0
      OR (SELECT max(p_ordinals[g]) FROM generate_subscripts(p_ordinals, 1) g) <> v_count - 1
      OR (SELECT count(DISTINCT p_ordinals[g]) FROM generate_subscripts(p_ordinals, 1) g) <> v_count
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '22023',
      MESSAGE = 'ASSOCIATION_IDENTITY_ORDER_INVALID';
  ELSIF p_order_semantics = 'UNORDERED' AND EXISTS (
    SELECT 1 FROM generate_subscripts(p_ordinals, 1) g
    WHERE p_ordinals[g] IS NOT NULL
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '22023',
      MESSAGE = 'ASSOCIATION_IDENTITY_ORDER_INVALID';
  END IF;
  IF p_roles_meaningful AND EXISTS (
    SELECT 1 FROM generate_subscripts(p_role_ids, 1) g
    WHERE p_role_ids[g] IS NULL OR btrim(p_role_ids[g]) = ''
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '22023',
      MESSAGE = 'ASSOCIATION_IDENTITY_ROLE_INVALID';
  ELSIF NOT p_roles_meaningful AND EXISTS (
    SELECT 1 FROM generate_subscripts(p_role_ids, 1) g
    WHERE p_role_ids[g] IS NOT NULL
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '22023',
      MESSAGE = 'ASSOCIATION_IDENTITY_ROLE_INVALID';
  END IF;

  SELECT * INTO STRICT v_scope
  FROM exploration_v3.governed_scope WHERE scope_id = p_scope_id;
  SELECT jsonb_agg(
    jsonb_build_object(
      'concept_id', p_concept_ids[g],
      'sense_id', p_sense_ids[g],
      'ordinal', p_ordinals[g],
      'role_id', p_role_ids[g]
    ) ORDER BY
      CASE WHEN p_order_semantics = 'ORDERED' THEN p_ordinals[g] END,
      CASE WHEN p_order_semantics = 'UNORDERED' AND p_roles_meaningful
        THEN p_role_ids[g] END COLLATE "C",
      CASE WHEN p_order_semantics = 'UNORDERED' THEN p_sense_ids[g] END COLLATE "C",
      CASE WHEN p_order_semantics = 'UNORDERED' THEN p_concept_ids[g] END COLLATE "C"
  ) INTO v_participants
  FROM generate_subscripts(p_concept_ids, 1) g;

  v_scope_identity := jsonb_build_object(
    'scope_id', v_scope.scope_id,
    'historical_case_ids', COALESCE((
      SELECT jsonb_agg(x ORDER BY x COLLATE "C") FROM unnest(v_scope.historical_case_ids) x
    ), '[]'::jsonb),
    'time_bounds', jsonb_build_object('start', v_scope.time_start, 'end', v_scope.time_end),
    'geographies', COALESCE((
      SELECT jsonb_agg(x ORDER BY x COLLATE "C") FROM unnest(v_scope.geographies) x
    ), '[]'::jsonb),
    'institutions', COALESCE((
      SELECT jsonb_agg(x ORDER BY x COLLATE "C") FROM unnest(v_scope.institutions) x
    ), '[]'::jsonb),
    'actors', COALESCE((
      SELECT jsonb_agg(x ORDER BY x COLLATE "C") FROM unnest(v_scope.actors) x
    ), '[]'::jsonb),
    'mechanisms', COALESCE((
      SELECT jsonb_agg(x ORDER BY x COLLATE "C") FROM unnest(v_scope.mechanisms) x
    ), '[]'::jsonb)
  );
  RETURN release.canonical_jsonb_sha256(jsonb_build_object(
    'association_kind', p_association_kind::text,
    'participants', v_participants,
    'scope_identity', v_scope_identity,
    'order_semantics', p_order_semantics::text,
    'roles_meaningful', p_roles_meaningful
  ));
END
$function$;

CREATE FUNCTION exploration_v3.association_revision_identity_sha(
  p_association_revision_id text
) RETURNS core.sha256_hex
LANGUAGE plpgsql STABLE STRICT
SET search_path = pg_catalog
AS $function$
DECLARE
  v_association exploration_v3.association%ROWTYPE;
  v_scope_id text;
  v_concepts text[];
  v_senses text[];
  v_ordinals integer[];
  v_roles text[];
BEGIN
  SELECT a.*
  INTO STRICT v_association
  FROM exploration_v3.association_revision r
  JOIN exploration_v3.association a ON a.association_id = r.association_id
  WHERE r.association_revision_id = p_association_revision_id;
  SELECT r.scope_id
  INTO STRICT v_scope_id
  FROM exploration_v3.association_revision r
  WHERE r.association_revision_id = p_association_revision_id;
  SELECT array_agg(concept_id ORDER BY incidence_id COLLATE "C"),
    array_agg(sense_id ORDER BY incidence_id COLLATE "C"),
    array_agg(ordinal ORDER BY incidence_id COLLATE "C"),
    array_agg(role_id ORDER BY incidence_id COLLATE "C")
  INTO v_concepts, v_senses, v_ordinals, v_roles
  FROM exploration_v3.association_incidence
  WHERE association_revision_id = p_association_revision_id;
  RETURN exploration_v3.association_identity_sha(
    v_association.association_kind, v_association.order_semantics,
    v_association.roles_meaningful, v_scope_id,
    v_concepts, v_senses, v_ordinals, v_roles);
END
$function$;

CREATE FUNCTION exploration_v3.lock_aggregate_parent(
  p_aggregate_kind text,
  p_aggregate_id text
) RETURNS void
LANGUAGE plpgsql VOLATILE
SET search_path = pg_catalog
AS $function$
BEGIN
  CASE p_aggregate_kind
    WHEN 'EVIDENCE_REFERENCE' THEN
      PERFORM 1 FROM exploration_v3.evidence_reference
      WHERE evidence_reference_id = p_aggregate_id FOR UPDATE;
    WHEN 'CONCEPT_SENSE' THEN
      PERFORM 1 FROM exploration_v3.concept_sense
      WHERE sense_id = p_aggregate_id FOR UPDATE;
    WHEN 'ASSOCIATION_REVISION' THEN
      PERFORM 1 FROM exploration_v3.association_revision
      WHERE association_revision_id = p_aggregate_id FOR UPDATE;
    WHEN 'COMPOSITION_REVISION' THEN
      PERFORM 1 FROM exploration_v3.composition_revision
      WHERE composition_revision_id = p_aggregate_id FOR UPDATE;
    WHEN 'NAVIGATION_STATE' THEN
      PERFORM 1 FROM exploration_v3.navigation_state
      WHERE state_id = p_aggregate_id FOR UPDATE;
    WHEN 'WORKFLOW' THEN
      PERFORM 1 FROM exploration_v3.exploration_workflow
      WHERE workflow_id = p_aggregate_id FOR UPDATE;
    WHEN 'EXPORT' THEN
      PERFORM 1 FROM exploration_v3.export_manifest
      WHERE export_id = p_aggregate_id FOR UPDATE;
    ELSE
      RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'AGGREGATE_SEAL_KIND_INVALID';
  END CASE;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'AGGREGATE_SEAL_PARENT_NOT_FOUND';
  END IF;
END
$function$;

CREATE FUNCTION exploration_v3.acquire_aggregate_membership_lock(
  p_aggregate_kind text,
  p_aggregate_id text
) RETURNS void
LANGUAGE plpgsql VOLATILE
SET search_path = pg_catalog
AS $function$
BEGIN
  IF current_setting('transaction_isolation') <> 'read committed' THEN
    RAISE EXCEPTION USING ERRCODE = '25000',
      MESSAGE = 'AGGREGATE_MEMBERSHIP_WRITES_REQUIRE_READ_COMMITTED';
  END IF;
  -- Never wait inside the child/seal statement: a statement snapshot taken
  -- before a competing commit would otherwise be stale after the wait.  A
  -- hash collision can only cause a safe false retry, never an unsafe write.
  IF NOT pg_try_advisory_xact_lock(hashtextextended(
    'exploration_v3:' || p_aggregate_kind || ':' || p_aggregate_id, 0)) THEN
    RAISE EXCEPTION USING ERRCODE = '40001',
      MESSAGE = 'AGGREGATE_MEMBERSHIP_CONCURRENT_WRITE_RETRY';
  END IF;
END
$function$;

-- Canonical aggregate material binds the complete governed parent and every
-- semantically relevant child row.  JSONB JCS removes key-order variance;
-- every child array has an explicit stable sort.
CREATE FUNCTION exploration_v3.aggregate_content_sha(
  p_aggregate_kind text,
  p_aggregate_id text
) RETURNS core.sha256_hex
LANGUAGE plpgsql STABLE STRICT
SET search_path = pg_catalog
SET TimeZone = 'UTC'
AS $function$
DECLARE v_material jsonb;
BEGIN
  CASE p_aggregate_kind
    WHEN 'EVIDENCE_REFERENCE' THEN
      SELECT jsonb_build_object(
        'aggregate_kind', p_aggregate_kind, 'aggregate_id', p_aggregate_id,
        'parent', to_jsonb(r),
        'locators', COALESCE((SELECT jsonb_agg(to_jsonb(l) ORDER BY l.locator_id COLLATE "C")
          FROM exploration_v3.evidence_locator l
          WHERE l.evidence_reference_id = r.evidence_reference_id), '[]'::jsonb)
      ) INTO v_material
      FROM exploration_v3.evidence_reference r
      WHERE r.evidence_reference_id = p_aggregate_id;
    WHEN 'CONCEPT_SENSE' THEN
      SELECT jsonb_build_object(
        'aggregate_kind', p_aggregate_kind, 'aggregate_id', p_aggregate_id,
        'parent', to_jsonb(s),
        'scopes', COALESCE((SELECT jsonb_agg(to_jsonb(ss) ORDER BY ss.scope_id COLLATE "C")
          FROM exploration_v3.concept_sense_scope ss
          WHERE ss.sense_id = s.sense_id), '[]'::jsonb)
      ) INTO v_material
      FROM exploration_v3.concept_sense s WHERE s.sense_id = p_aggregate_id;
    WHEN 'ASSOCIATION_REVISION' THEN
      SELECT jsonb_build_object(
        'aggregate_kind', p_aggregate_kind, 'aggregate_id', p_aggregate_id,
        'association', to_jsonb(a), 'revision', to_jsonb(r),
        'incidences', COALESCE((SELECT jsonb_agg(to_jsonb(i) ORDER BY i.incidence_id COLLATE "C")
          FROM exploration_v3.association_incidence i
          WHERE i.association_revision_id = r.association_revision_id), '[]'::jsonb),
        'evidence_links', COALESCE((SELECT jsonb_agg(to_jsonb(e)
          ORDER BY e.evidence_reference_id COLLATE "C", e.evidence_role::text COLLATE "C")
          FROM exploration_v3.association_revision_evidence e
          WHERE e.association_revision_id = r.association_revision_id), '[]'::jsonb),
        'synthesis_steps', COALESCE((SELECT jsonb_agg(to_jsonb(s) ORDER BY s.step_ordinal)
          FROM exploration_v3.association_synthesis_step s
          WHERE s.association_revision_id = r.association_revision_id), '[]'::jsonb),
        'synthesis_evidence', COALESCE((SELECT jsonb_agg(to_jsonb(se)
          ORDER BY se.step_ordinal, se.evidence_reference_id COLLATE "C")
          FROM exploration_v3.association_synthesis_step_evidence se
          WHERE se.association_revision_id = r.association_revision_id), '[]'::jsonb),
        'conflict_resolutions', COALESCE((SELECT jsonb_agg(to_jsonb(cr)
          ORDER BY cr.conflict_resolution_id COLLATE "C")
          FROM exploration_v3.association_conflict_resolution cr
          WHERE cr.association_revision_id = r.association_revision_id), '[]'::jsonb),
        'review', (SELECT to_jsonb(rv) FROM exploration_v3.association_review rv
          WHERE rv.association_revision_id = r.association_revision_id),
        'internal_pair_links', COALESCE((SELECT jsonb_agg(to_jsonb(ip)
          ORDER BY ip.pair_revision_id COLLATE "C", ip.higher_incidence_a COLLATE "C",
            ip.higher_incidence_b COLLATE "C")
          FROM exploration_v3.internal_pair_link ip
          WHERE ip.higher_order_revision_id = r.association_revision_id), '[]'::jsonb)
      ) INTO v_material
      FROM exploration_v3.association_revision r
      JOIN exploration_v3.association a ON a.association_id = r.association_id
      WHERE r.association_revision_id = p_aggregate_id;
    WHEN 'COMPOSITION_REVISION' THEN
      SELECT jsonb_build_object(
        'aggregate_kind', p_aggregate_kind, 'aggregate_id', p_aggregate_id,
        'composition', to_jsonb(c), 'revision', to_jsonb(r),
        'nodes', COALESCE((SELECT jsonb_agg(to_jsonb(n) ORDER BY n.concept_id COLLATE "C")
          FROM exploration_v3.composition_node n
          WHERE n.composition_revision_id = r.composition_revision_id), '[]'::jsonb),
        'realizations', COALESCE((SELECT jsonb_agg(to_jsonb(ar)
          ORDER BY ar.association_realization_id COLLATE "C")
          FROM exploration_v3.association_realization ar
          WHERE ar.composition_revision_id = r.composition_revision_id), '[]'::jsonb),
        'realization_incidences', COALESCE((SELECT jsonb_agg(to_jsonb(ri)
          ORDER BY ri.association_realization_id COLLATE "C", ri.incidence_id COLLATE "C")
          FROM exploration_v3.association_realization ar
          JOIN exploration_v3.realization_incidence ri USING (association_realization_id)
          WHERE ar.composition_revision_id = r.composition_revision_id), '[]'::jsonb),
        'review', (SELECT to_jsonb(rv) FROM exploration_v3.composition_coherence_review rv
          WHERE rv.composition_revision_id = r.composition_revision_id),
        'review_realizations', COALESCE((SELECT jsonb_agg(to_jsonb(rr)
          ORDER BY rr.association_realization_id COLLATE "C")
          FROM exploration_v3.composition_coherence_review rv
          JOIN exploration_v3.composition_review_realization rr
            USING (composition_coherence_review_id)
          WHERE rv.composition_revision_id = r.composition_revision_id), '[]'::jsonb)
      ) INTO v_material
      FROM exploration_v3.composition_revision r
      JOIN exploration_v3.composition c ON c.composition_id = r.composition_id
      WHERE r.composition_revision_id = p_aggregate_id;
    WHEN 'NAVIGATION_STATE' THEN
      SELECT jsonb_build_object(
        'aggregate_kind', p_aggregate_kind, 'aggregate_id', p_aggregate_id,
        'parent', to_jsonb(s),
        'nodes', COALESCE((SELECT jsonb_agg(to_jsonb(n) ORDER BY n.navigation_node_id COLLATE "C")
          FROM exploration_v3.navigation_node n WHERE n.state_id = s.state_id), '[]'::jsonb),
        'path', COALESCE((SELECT jsonb_agg(to_jsonb(p) ORDER BY p.step_ordinal)
          FROM exploration_v3.navigation_path_step p WHERE p.state_id = s.state_id), '[]'::jsonb)
      ) INTO v_material
      FROM exploration_v3.navigation_state s WHERE s.state_id = p_aggregate_id;
    WHEN 'WORKFLOW' THEN
      SELECT jsonb_build_object(
        'aggregate_kind', p_aggregate_kind, 'aggregate_id', p_aggregate_id,
        'parent', to_jsonb(w),
        'states', COALESCE((SELECT jsonb_agg(to_jsonb(ws) ORDER BY ws.state_id COLLATE "C")
          FROM exploration_v3.workflow_state ws WHERE ws.workflow_id = w.workflow_id), '[]'::jsonb),
        'association_revisions', COALESCE((SELECT jsonb_agg(to_jsonb(wa)
          ORDER BY wa.association_revision_id COLLATE "C")
          FROM exploration_v3.workflow_association_revision wa
          WHERE wa.workflow_id = w.workflow_id), '[]'::jsonb),
        'association_realizations', COALESCE((SELECT jsonb_agg(to_jsonb(wr)
          ORDER BY wr.association_realization_id COLLATE "C")
          FROM exploration_v3.workflow_association_realization wr
          WHERE wr.workflow_id = w.workflow_id), '[]'::jsonb),
        'transitions', COALESCE((SELECT jsonb_agg(to_jsonb(wt) ORDER BY wt.transition_id COLLATE "C")
          FROM exploration_v3.workflow_transition wt WHERE wt.workflow_id = w.workflow_id), '[]'::jsonb)
      ) INTO v_material
      FROM exploration_v3.exploration_workflow w WHERE w.workflow_id = p_aggregate_id;
    WHEN 'EXPORT' THEN
      SELECT jsonb_build_object(
        'aggregate_kind', p_aggregate_kind, 'aggregate_id', p_aggregate_id,
        'parent', to_jsonb(e),
        'preservation', COALESCE((SELECT jsonb_agg(to_jsonb(p)
          ORDER BY p.association_revision_id COLLATE "C",
            p.association_realization_id COLLATE "C")
          FROM exploration_v3.export_projection_preservation p
          WHERE p.export_id = e.export_id), '[]'::jsonb)
      ) INTO v_material
      FROM exploration_v3.export_manifest e WHERE e.export_id = p_aggregate_id;
    ELSE
      RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'AGGREGATE_SEAL_KIND_INVALID';
  END CASE;
  IF v_material IS NULL THEN
    RAISE EXCEPTION USING ERRCODE = '23503', MESSAGE = 'AGGREGATE_SEAL_PARENT_NOT_FOUND';
  END IF;
  RETURN release.canonical_jsonb_sha256(v_material);
END
$function$;

CREATE FUNCTION exploration_v3.assert_aggregate_seal(
  p_aggregate_kind text,
  p_aggregate_id text
) RETURNS void
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE v_seal_hash core.sha256_hex;
DECLARE v_expected_hash core.sha256_hex;
BEGIN
  SELECT aggregate_content_sha256 INTO v_seal_hash
  FROM exploration_v3.aggregate_seal
  WHERE aggregate_kind = p_aggregate_kind AND aggregate_id = p_aggregate_id;
  IF NOT FOUND THEN RETURN; END IF;
  v_expected_hash := exploration_v3.aggregate_content_sha(
    p_aggregate_kind, p_aggregate_id);
  IF v_expected_hash <> v_seal_hash THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'AGGREGATE_SEAL_CONTENT_HASH_MISMATCH';
  END IF;
END
$function$;

CREATE FUNCTION exploration_v3.enforce_aggregate_seal_insert()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
DECLARE v_expected_hash core.sha256_hex;
BEGIN
  PERFORM exploration_v3.acquire_aggregate_membership_lock(
    NEW.aggregate_kind, NEW.aggregate_id);
  PERFORM exploration_v3.lock_aggregate_parent(NEW.aggregate_kind, NEW.aggregate_id);
  v_expected_hash := exploration_v3.aggregate_content_sha(
    NEW.aggregate_kind, NEW.aggregate_id);
  IF NEW.aggregate_content_sha256 <> v_expected_hash THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'AGGREGATE_SEAL_CONTENT_HASH_MISMATCH';
  END IF;
  RETURN NEW;
END
$function$;

CREATE FUNCTION exploration_v3.enforce_aggregate_seal()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM exploration_v3.assert_aggregate_seal(
    COALESCE(NEW.aggregate_kind, OLD.aggregate_kind),
    COALESCE(NEW.aggregate_id, OLD.aggregate_id));
  RETURN NULL;
END
$function$;

CREATE FUNCTION exploration_v3.reject_sealed_child_insert()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
DECLARE v_kind text;
DECLARE v_id text;
BEGIN
  CASE TG_TABLE_NAME
    WHEN 'evidence_locator' THEN
      v_kind := 'EVIDENCE_REFERENCE'; v_id := NEW.evidence_reference_id;
    WHEN 'concept_sense_scope' THEN
      v_kind := 'CONCEPT_SENSE'; v_id := NEW.sense_id;
    WHEN 'association_incidence' THEN
      v_kind := 'ASSOCIATION_REVISION'; v_id := NEW.association_revision_id;
    WHEN 'association_revision_evidence' THEN
      v_kind := 'ASSOCIATION_REVISION'; v_id := NEW.association_revision_id;
    WHEN 'association_synthesis_step' THEN
      v_kind := 'ASSOCIATION_REVISION'; v_id := NEW.association_revision_id;
    WHEN 'association_synthesis_step_evidence' THEN
      v_kind := 'ASSOCIATION_REVISION'; v_id := NEW.association_revision_id;
    WHEN 'association_conflict_resolution' THEN
      v_kind := 'ASSOCIATION_REVISION'; v_id := NEW.association_revision_id;
    WHEN 'association_review' THEN
      v_kind := 'ASSOCIATION_REVISION'; v_id := NEW.association_revision_id;
    WHEN 'internal_pair_link' THEN
      v_kind := 'ASSOCIATION_REVISION'; v_id := NEW.higher_order_revision_id;
    WHEN 'composition_node' THEN
      v_kind := 'COMPOSITION_REVISION'; v_id := NEW.composition_revision_id;
    WHEN 'association_realization' THEN
      v_kind := 'COMPOSITION_REVISION'; v_id := NEW.composition_revision_id;
    WHEN 'composition_coherence_review' THEN
      v_kind := 'COMPOSITION_REVISION'; v_id := NEW.composition_revision_id;
    WHEN 'realization_incidence' THEN
      v_kind := 'COMPOSITION_REVISION';
      SELECT composition_revision_id INTO STRICT v_id
      FROM exploration_v3.association_realization
      WHERE association_realization_id = NEW.association_realization_id;
    WHEN 'composition_review_realization' THEN
      v_kind := 'COMPOSITION_REVISION';
      SELECT composition_revision_id INTO STRICT v_id
      FROM exploration_v3.composition_coherence_review
      WHERE composition_coherence_review_id = NEW.composition_coherence_review_id;
    WHEN 'navigation_node' THEN
      v_kind := 'NAVIGATION_STATE'; v_id := NEW.state_id;
    WHEN 'navigation_path_step' THEN
      v_kind := 'NAVIGATION_STATE'; v_id := NEW.state_id;
    WHEN 'workflow_state' THEN
      v_kind := 'WORKFLOW'; v_id := NEW.workflow_id;
    WHEN 'workflow_association_revision' THEN
      v_kind := 'WORKFLOW'; v_id := NEW.workflow_id;
    WHEN 'workflow_association_realization' THEN
      v_kind := 'WORKFLOW'; v_id := NEW.workflow_id;
    WHEN 'workflow_transition' THEN
      v_kind := 'WORKFLOW'; v_id := NEW.workflow_id;
    WHEN 'export_projection_preservation' THEN
      v_kind := 'EXPORT'; v_id := NEW.export_id;
    ELSE
      RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'SEALED_CHILD_TABLE_UNMAPPED';
  END CASE;
  PERFORM exploration_v3.acquire_aggregate_membership_lock(v_kind, v_id);
  -- Parent row locks bind the resolved identifier to its exact parent.  The
  -- non-waiting advisory guard above eliminates stale post-wait snapshots.
  PERFORM exploration_v3.lock_aggregate_parent(v_kind, v_id);
  IF EXISTS (
    SELECT 1 FROM exploration_v3.aggregate_seal
    WHERE aggregate_kind = v_kind AND aggregate_id = v_id
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '55000',
      MESSAGE = 'SEALED_AGGREGATE_CHILD_INSERT_FORBIDDEN';
  END IF;
  RETURN NEW;
END
$function$;

CREATE FUNCTION exploration_v3.assert_association_revision(
  p_association_revision_id text
) RETURNS void
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_revision exploration_v3.association_revision%ROWTYPE;
  v_association exploration_v3.association%ROWTYPE;
  v_incidence_count integer;
  v_review exploration_v3.association_review%ROWTYPE;
  v_authority exploration_v3.governed_authority%ROWTYPE;
  v_superseded_revision_number integer;
  v_scope_realm exploration_v3.realm;
  v_scope_context_qualifications text[];
  v_identity_hash core.sha256_hex;
  v_positive_disposition boolean;
BEGIN
  SELECT * INTO v_revision
  FROM exploration_v3.association_revision
  WHERE association_revision_id = p_association_revision_id;
  IF NOT FOUND THEN RETURN; END IF;

  SELECT * INTO STRICT v_association
  FROM exploration_v3.association
  WHERE association_id = v_revision.association_id;

  SELECT realm, context_qualifications
  INTO STRICT v_scope_realm, v_scope_context_qualifications
  FROM exploration_v3.governed_scope WHERE scope_id = v_revision.scope_id;
  IF v_scope_realm <> v_association.realm THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ASSOCIATION_SCOPE_REALM_MISMATCH';
  END IF;
  IF (v_association.realm = 'PRODUCTION' AND (
      (v_revision.product_eligible
        AND v_revision.product_eligibility_disposition <> 'ELIGIBLE')
      OR (NOT v_revision.product_eligible
        AND v_revision.product_eligibility_disposition NOT IN ('INELIGIBLE','DEFERRED'))
    )) OR (v_association.realm = 'SYNTHETIC_CONTROL' AND (
      v_revision.product_eligible
      OR v_revision.product_eligibility_disposition <> 'NOT_APPLICABLE_SYNTHETIC'
    )) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ASSOCIATION_PRODUCT_DISPOSITION_MATRIX_INVALID';
  END IF;

  -- The immutable scope row carries the identity-bearing scope fields.  Each
  -- association revision carries the complete context-qualification snapshot
  -- used by that revision's semantic material.  Revision one must reproduce
  -- the source scope; successors may change qualifications without changing
  -- the stable association identity.
  IF v_revision.revision_number = 1
    AND v_revision.scope_context_qualifications IS DISTINCT FROM
      v_scope_context_qualifications THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ASSOCIATION_REVISION_SCOPE_CONTEXT_SNAPSHOT_INVALID';
  END IF;

  IF v_revision.revision_number = 1
    AND v_revision.supersedes_association_revision_id IS NOT NULL THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ASSOCIATION_REVISION_LINEAGE_INVALID';
  ELSIF v_revision.revision_number > 1 THEN
    IF v_revision.supersedes_association_revision_id IS NULL THEN
      RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ASSOCIATION_REVISION_LINEAGE_INVALID';
    END IF;
    SELECT revision_number INTO v_superseded_revision_number
    FROM exploration_v3.association_revision
    WHERE association_id = v_revision.association_id
      AND association_revision_id = v_revision.supersedes_association_revision_id;
    IF NOT FOUND OR v_superseded_revision_number <> v_revision.revision_number - 1 THEN
      RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ASSOCIATION_REVISION_LINEAGE_INVALID';
    END IF;
  END IF;

  SELECT count(*) INTO v_incidence_count
  FROM exploration_v3.association_incidence
  WHERE association_revision_id = p_association_revision_id;
  IF v_incidence_count <> v_association.arity THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ASSOCIATION_ARITY_INCIDENCE_MISMATCH';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM exploration_v3.association_incidence i
    JOIN exploration_v3.concept c ON c.concept_id = i.concept_id
    JOIN exploration_v3.concept_sense s ON s.sense_id = i.sense_id
    JOIN exploration_v3.governed_scope ps ON ps.scope_id = i.participant_scope_id
    JOIN exploration_v3.governed_scope rs ON rs.scope_id = v_revision.scope_id
    WHERE i.association_revision_id = p_association_revision_id
      AND (c.realm <> v_association.realm OR s.realm <> v_association.realm
        OR ps.realm <> v_association.realm OR rs.realm <> v_association.realm
        OR i.participant_scope_id <> v_revision.scope_id)
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ASSOCIATION_REALM_MISMATCH';
  END IF;

  IF v_association.order_semantics = 'ORDERED' AND (
    EXISTS (SELECT 1 FROM exploration_v3.association_incidence
      WHERE association_revision_id = p_association_revision_id AND ordinal IS NULL)
    OR (SELECT min(ordinal) FROM exploration_v3.association_incidence
        WHERE association_revision_id = p_association_revision_id) <> 0
    OR (SELECT max(ordinal) FROM exploration_v3.association_incidence
        WHERE association_revision_id = p_association_revision_id) <> v_association.arity - 1
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ORDERED_INCIDENCE_ORDINALS_NOT_CONTIGUOUS';
  ELSIF v_association.order_semantics = 'UNORDERED' AND EXISTS (
    SELECT 1 FROM exploration_v3.association_incidence
    WHERE association_revision_id = p_association_revision_id AND ordinal IS NOT NULL
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'UNORDERED_INCIDENCE_HAS_ORDINAL';
  END IF;

  IF v_association.roles_meaningful AND EXISTS (
    SELECT 1 FROM exploration_v3.association_incidence
    WHERE association_revision_id = p_association_revision_id AND role_id IS NULL
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'MEANINGFUL_ROLE_MISSING';
  ELSIF NOT v_association.roles_meaningful AND EXISTS (
    SELECT 1 FROM exploration_v3.association_incidence
    WHERE association_revision_id = p_association_revision_id AND role_id IS NOT NULL
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'UNMEANINGFUL_ROLE_INVENTED';
  END IF;

  v_identity_hash := exploration_v3.association_revision_identity_sha(
    p_association_revision_id);
  IF v_association.identity_material_sha256 <> v_identity_hash
    OR v_association.association_id <>
      'association:v3:' || left(v_identity_hash::text, 24) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ASSOCIATION_STABLE_IDENTITY_MISMATCH';
  END IF;

  IF v_association.association_kind = 'PAIR'
    AND v_revision.support_mode NOT IN ('DIRECT_PAIR', 'PAIR_ONLY', 'NONE') THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'PAIR_SUPPORT_MODE_INVALID';
  ELSIF v_association.association_kind = 'HIGHER_ORDER'
    AND v_revision.support_mode = 'DIRECT_PAIR' THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'HIGHER_ORDER_DIRECT_PAIR_MODE_INVALID';
  END IF;

  -- A final conflict resolution is itself a governed decision.  Production
  -- resolutions may never be finalized by synthetic authority, regardless of
  -- lifecycle state or eventual review disposition.
  IF EXISTS (
    SELECT 1
    FROM exploration_v3.association_conflict_resolution cr
    JOIN exploration_v3.governed_authority ca ON ca.authority_id = cr.authority_id
    WHERE cr.association_revision_id = p_association_revision_id
      AND cr.resolution_state = 'FINAL'
      AND (ca.authority_state <> 'FINAL'
        OR (v_association.realm = 'PRODUCTION'
          AND ca.authority_kind = 'SYNTHETIC_TEST_AUTHORITY'))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'FINAL_CONFLICT_RESOLUTION_AUTHORITY_INVALID';
  END IF;

  SELECT * INTO v_review
  FROM exploration_v3.association_review
  WHERE association_revision_id = p_association_revision_id;
  IF FOUND AND v_review.review_state = 'FINAL' THEN
    IF NOT EXISTS (
      SELECT 1 FROM exploration_v3.aggregate_seal
      WHERE aggregate_kind = 'ASSOCIATION_REVISION'
        AND aggregate_id = p_association_revision_id
    ) THEN
      RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'FINAL_ASSOCIATION_REVIEW_UNSEALED';
    END IF;
    SELECT * INTO STRICT v_authority
    FROM exploration_v3.governed_authority WHERE authority_id = v_review.authority_id;
    IF v_authority.authority_state <> 'FINAL'
      OR (v_association.realm = 'PRODUCTION'
        AND v_authority.authority_kind = 'SYNTHETIC_TEST_AUTHORITY')
      OR v_review.disposition = 'PENDING_GOVERNED_REVIEW' THEN
      RAISE EXCEPTION USING ERRCODE = '23514',
        MESSAGE = 'FINAL_ASSOCIATION_DISPOSITION_PARITY_INVALID';
    END IF;
    -- Final decisions, including negative and unresolved dispositions, must be
    -- traceable to at least one sealed, locator-bearing, rights-cleared
    -- evidence reference in the same governed realm.
    IF NOT EXISTS (
      SELECT 1 FROM exploration_v3.association_revision_evidence e
      WHERE e.association_revision_id = p_association_revision_id
    ) OR EXISTS (
      SELECT 1
      FROM exploration_v3.association_revision_evidence e
      JOIN exploration_v3.evidence_reference er
        ON er.evidence_reference_id = e.evidence_reference_id
      WHERE e.association_revision_id = p_association_revision_id
        AND (er.realm <> v_association.realm
          OR NOT er.rights_cleared_for_governed_use
          OR NOT EXISTS (
            SELECT 1 FROM exploration_v3.evidence_locator locator
            WHERE locator.evidence_reference_id = er.evidence_reference_id)
          OR NOT EXISTS (
            SELECT 1 FROM exploration_v3.aggregate_seal evidence_seal
            WHERE evidence_seal.aggregate_kind = 'EVIDENCE_REFERENCE'
              AND evidence_seal.aggregate_id = er.evidence_reference_id))
    ) THEN
      RAISE EXCEPTION USING ERRCODE = '23514',
        MESSAGE = 'FINAL_ASSOCIATION_EVIDENCE_TRACE_INVALID';
    END IF;
    v_positive_disposition := v_review.disposition IN (
      'DIRECT_PAIRWISE_SUPPORT', 'DIRECT_HIGHER_ORDER_SUPPORT',
      'COHERENT_COMPOSITE_SUPPORT', 'MIXED_DIRECT_AND_COMPOSITE_SUPPORT');
    IF v_positive_disposition THEN
      IF v_review.global_coherence <> 'PASS'
        OR NOT v_review.bounded_senses_compatible
        OR NOT v_review.case_scope_compatible
        OR NOT v_review.roles_and_topology_supported
        OR v_review.unsupported_bridge_count <> 0
        OR NOT v_revision.evidence_complete
        OR NOT v_revision.same_configuration
        OR NOT v_revision.conflicts_resolved
        OR NOT v_revision.rights_cleared_for_governed_use
        OR NOT v_revision.synthesis_complete
        OR NOT (
          (v_association.association_kind = 'PAIR'
            AND v_revision.support_mode = 'DIRECT_PAIR'
            AND v_review.disposition = 'DIRECT_PAIRWISE_SUPPORT')
          OR (v_association.association_kind = 'HIGHER_ORDER'
            AND v_revision.support_mode = 'DIRECT_GROUP'
            AND v_review.disposition = 'DIRECT_HIGHER_ORDER_SUPPORT')
          OR (v_association.association_kind = 'HIGHER_ORDER'
            AND v_revision.support_mode = 'COHERENT_COMPOSITE'
            AND v_review.disposition = 'COHERENT_COMPOSITE_SUPPORT')
          OR (v_association.association_kind = 'HIGHER_ORDER'
            AND v_revision.support_mode = 'MIXED'
            AND v_review.disposition = 'MIXED_DIRECT_AND_COMPOSITE_SUPPORT')
        )
        OR NOT EXISTS (
          SELECT 1 FROM exploration_v3.association_revision_evidence e
          JOIN exploration_v3.evidence_reference er
            ON er.evidence_reference_id = e.evidence_reference_id
          WHERE e.association_revision_id = p_association_revision_id
            AND e.evidence_role = 'supports'
            AND er.realm = v_association.realm
            AND er.rights_cleared_for_governed_use
            AND EXISTS (SELECT 1 FROM exploration_v3.evidence_locator l
              WHERE l.evidence_reference_id = er.evidence_reference_id)
            AND EXISTS (SELECT 1 FROM exploration_v3.aggregate_seal es
              WHERE es.aggregate_kind = 'EVIDENCE_REFERENCE'
                AND es.aggregate_id = er.evidence_reference_id)
        )
        OR EXISTS (
          SELECT 1
          FROM exploration_v3.association_revision_evidence e
          JOIN exploration_v3.evidence_reference er
            ON er.evidence_reference_id = e.evidence_reference_id
          WHERE e.association_revision_id = p_association_revision_id
            AND (e.evidence_role = 'contradicts' OR er.negative_or_conflicting)
            AND NOT EXISTS (
              SELECT 1 FROM exploration_v3.association_conflict_resolution cr
              JOIN exploration_v3.governed_authority ca ON ca.authority_id = cr.authority_id
              WHERE cr.association_revision_id = e.association_revision_id
                AND cr.evidence_reference_id = e.evidence_reference_id
                AND cr.resolution_state = 'FINAL' AND ca.authority_state = 'FINAL'
                AND (v_association.realm = 'SYNTHETIC_CONTROL'
                  OR ca.authority_kind <> 'SYNTHETIC_TEST_AUTHORITY'))
        ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
          MESSAGE = 'FINAL_ASSOCIATION_DISPOSITION_PARITY_INVALID';
      END IF;
      IF v_revision.support_mode IN ('COHERENT_COMPOSITE','MIXED') AND (
        NOT EXISTS (SELECT 1 FROM exploration_v3.association_synthesis_step s
          WHERE s.association_revision_id = p_association_revision_id)
        OR EXISTS (SELECT 1 FROM exploration_v3.association_synthesis_step s
          WHERE s.association_revision_id = p_association_revision_id
            AND NOT s.bridge_supported)
        OR EXISTS (
          SELECT 1 FROM exploration_v3.association_synthesis_step s
          WHERE s.association_revision_id = p_association_revision_id
            AND NOT EXISTS (
              SELECT 1 FROM exploration_v3.association_synthesis_step_evidence se
              JOIN exploration_v3.association_revision_evidence ae
                ON ae.association_revision_id = se.association_revision_id
               AND ae.evidence_reference_id = se.evidence_reference_id
               AND ae.evidence_role IN ('supports','contextualises')
              WHERE se.association_revision_id = s.association_revision_id
                AND se.step_ordinal = s.step_ordinal))
      ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
          MESSAGE = 'FINAL_ASSOCIATION_DISPOSITION_PARITY_INVALID';
      END IF;
      IF v_revision.support_mode IN ('DIRECT_PAIR','DIRECT_GROUP') AND EXISTS (
        SELECT 1 FROM exploration_v3.association_synthesis_step s
        WHERE s.association_revision_id = p_association_revision_id
      ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
          MESSAGE = 'FINAL_ASSOCIATION_DISPOSITION_PARITY_INVALID';
      END IF;
    ELSIF v_review.global_coherence = 'PASS'
      OR v_revision.activation_decision = 'ALLOW'
      OR v_revision.all_activation_gates_pass
      OR v_revision.lifecycle_state = 'ACTIVE'
      OR v_revision.product_eligible THEN
      RAISE EXCEPTION USING ERRCODE = '23514',
        MESSAGE = 'FINAL_ASSOCIATION_DISPOSITION_PARITY_INVALID';
    END IF;
  END IF;

  IF v_revision.lifecycle_state <> 'ACTIVE' THEN RETURN; END IF;

  IF v_revision.activation_decision <> 'ALLOW'
    OR NOT v_revision.all_activation_gates_pass
    OR NOT v_revision.evidence_complete
    OR NOT v_revision.same_configuration
    OR NOT v_revision.conflicts_resolved
    OR NOT v_revision.rights_cleared_for_governed_use
    OR NOT v_revision.synthesis_complete
    OR v_revision.uncertainty_status <> 'RESOLVED_BOUNDED'
    OR v_revision.uncertainty_level = 'UNKNOWN'
    OR v_revision.uncertainty_activation_policy <> 'ALLOWED_BOUNDED' THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ACTIVE_ASSOCIATION_GATE_FAILURE';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM exploration_v3.association_revision_evidence e
    WHERE e.association_revision_id = p_association_revision_id
      AND e.evidence_role = 'supports'
  ) OR EXISTS (
    SELECT 1
    FROM exploration_v3.association_revision_evidence e
    JOIN exploration_v3.evidence_reference r
      ON r.evidence_reference_id = e.evidence_reference_id
    WHERE e.association_revision_id = p_association_revision_id
      AND (NOT r.rights_cleared_for_governed_use
        OR r.realm <> v_association.realm
        OR NOT EXISTS (
          SELECT 1 FROM exploration_v3.evidence_locator l
          WHERE l.evidence_reference_id = r.evidence_reference_id)
        OR NOT EXISTS (
          SELECT 1 FROM exploration_v3.aggregate_seal es
          WHERE es.aggregate_kind = 'EVIDENCE_REFERENCE'
            AND es.aggregate_id = r.evidence_reference_id))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ACTIVE_ASSOCIATION_EVIDENCE_INVALID';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM exploration_v3.association_revision_evidence e
    JOIN exploration_v3.evidence_reference r
      ON r.evidence_reference_id = e.evidence_reference_id
    WHERE e.association_revision_id = p_association_revision_id
      AND (e.evidence_role = 'contradicts' OR r.negative_or_conflicting)
      AND NOT EXISTS (
        SELECT 1
        FROM exploration_v3.association_conflict_resolution cr
        JOIN exploration_v3.governed_authority ca ON ca.authority_id = cr.authority_id
        WHERE cr.association_revision_id = e.association_revision_id
          AND cr.evidence_reference_id = e.evidence_reference_id
          AND cr.resolution_state = 'FINAL' AND ca.authority_state = 'FINAL'
          AND (v_association.realm = 'SYNTHETIC_CONTROL'
            OR ca.authority_kind <> 'SYNTHETIC_TEST_AUTHORITY'))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ACTIVE_ASSOCIATION_CONFLICT_UNRESOLVED';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM exploration_v3.association_conflict_resolution cr
    JOIN exploration_v3.governed_authority ca ON ca.authority_id = cr.authority_id
    WHERE cr.association_revision_id = p_association_revision_id
      AND (cr.resolution_state <> 'FINAL' OR ca.authority_state <> 'FINAL'
        OR (v_association.realm = 'PRODUCTION'
          AND ca.authority_kind = 'SYNTHETIC_TEST_AUTHORITY')
        OR NOT EXISTS (
          SELECT 1 FROM exploration_v3.association_revision_evidence e
          JOIN exploration_v3.evidence_reference r
            ON r.evidence_reference_id = e.evidence_reference_id
          WHERE e.association_revision_id = cr.association_revision_id
            AND e.evidence_reference_id = cr.evidence_reference_id
            AND (e.evidence_role = 'contradicts' OR r.negative_or_conflicting)))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ACTIVE_ASSOCIATION_CONFLICT_RESOLUTION_INVALID';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM exploration_v3.association_incidence i
    JOIN exploration_v3.concept c ON c.concept_id = i.concept_id
    JOIN exploration_v3.concept_sense s ON s.sense_id = i.sense_id
    JOIN exploration_v3.governed_authority ca ON ca.authority_id = c.authority_id
    JOIN exploration_v3.governed_authority sa ON sa.authority_id = s.authority_id
    WHERE i.association_revision_id = p_association_revision_id
      AND (c.lifecycle_state <> 'ACTIVE' OR NOT c.association_eligible
        OR s.lifecycle_state <> 'ACTIVE' OR NOT s.association_eligible
        OR ca.authority_state <> 'FINAL' OR sa.authority_state <> 'FINAL'
        OR (v_association.realm = 'PRODUCTION'
          AND (ca.authority_kind = 'SYNTHETIC_TEST_AUTHORITY'
            OR sa.authority_kind = 'SYNTHETIC_TEST_AUTHORITY'))
        OR NOT EXISTS (
          SELECT 1 FROM exploration_v3.concept_sense_scope css
          WHERE css.sense_id = s.sense_id AND css.scope_id = i.participant_scope_id)
        OR NOT EXISTS (
          SELECT 1 FROM exploration_v3.aggregate_seal ss
          WHERE ss.aggregate_kind = 'CONCEPT_SENSE'
            AND ss.aggregate_id = s.sense_id))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ACTIVE_ASSOCIATION_PARTICIPANT_INVALID';
  END IF;
  IF v_revision.product_eligible AND EXISTS (
    SELECT 1
    FROM exploration_v3.association_incidence i
    JOIN exploration_v3.concept c ON c.concept_id = i.concept_id
    JOIN exploration_v3.concept_sense s ON s.sense_id = i.sense_id
    WHERE i.association_revision_id = p_association_revision_id
      AND (NOT c.product_eligible OR NOT s.product_eligible)
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'ACTIVE_PRODUCT_ASSOCIATION_PARTICIPANT_INELIGIBLE';
  END IF;

  SELECT * INTO v_review
  FROM exploration_v3.association_review
  WHERE association_revision_id = p_association_revision_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ACTIVE_ASSOCIATION_REVIEW_MISSING';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM exploration_v3.aggregate_seal
    WHERE aggregate_kind = 'ASSOCIATION_REVISION'
      AND aggregate_id = p_association_revision_id
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ACTIVE_ASSOCIATION_UNSEALED';
  END IF;
  SELECT * INTO STRICT v_authority
  FROM exploration_v3.governed_authority WHERE authority_id = v_review.authority_id;
  IF v_review.review_state <> 'FINAL' OR v_authority.authority_state <> 'FINAL'
    OR v_review.global_coherence <> 'PASS'
    OR NOT v_review.bounded_senses_compatible
    OR NOT v_review.case_scope_compatible
    OR NOT v_review.roles_and_topology_supported
    OR v_review.unsupported_bridge_count <> 0 THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ACTIVE_ASSOCIATION_REVIEW_INVALID';
  END IF;
  IF v_association.realm = 'PRODUCTION'
    AND v_authority.authority_kind = 'SYNTHETIC_TEST_AUTHORITY' THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'SYNTHETIC_AUTHORITY_CANNOT_ACTIVATE_PRODUCTION';
  ELSIF v_association.realm = 'SYNTHETIC_CONTROL'
    AND (v_revision.product_eligible
      OR v_revision.product_eligibility_disposition <> 'NOT_APPLICABLE_SYNTHETIC') THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'SYNTHETIC_ASSOCIATION_PRODUCT_FORBIDDEN';
  END IF;

  IF v_association.association_kind = 'PAIR' AND (
    v_revision.support_mode <> 'DIRECT_PAIR'
    OR v_review.disposition <> 'DIRECT_PAIRWISE_SUPPORT'
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ACTIVE_PAIR_DISPOSITION_INVALID';
  ELSIF v_association.association_kind = 'HIGHER_ORDER' AND NOT (
    (v_revision.support_mode = 'DIRECT_GROUP'
      AND v_review.disposition = 'DIRECT_HIGHER_ORDER_SUPPORT')
    OR (v_revision.support_mode = 'COHERENT_COMPOSITE'
      AND v_review.disposition = 'COHERENT_COMPOSITE_SUPPORT')
    OR (v_revision.support_mode = 'MIXED'
      AND v_review.disposition = 'MIXED_DIRECT_AND_COMPOSITE_SUPPORT')
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ACTIVE_HIGHER_ORDER_DISPOSITION_INVALID';
  END IF;

  IF v_revision.support_mode IN ('COHERENT_COMPOSITE', 'MIXED') AND (
    NOT EXISTS (SELECT 1 FROM exploration_v3.association_synthesis_step
      WHERE association_revision_id = p_association_revision_id)
    OR EXISTS (SELECT 1 FROM exploration_v3.association_synthesis_step
      WHERE association_revision_id = p_association_revision_id AND NOT bridge_supported)
    OR EXISTS (
      SELECT 1 FROM exploration_v3.association_synthesis_step s
      WHERE s.association_revision_id = p_association_revision_id
        AND NOT EXISTS (
          SELECT 1 FROM exploration_v3.association_synthesis_step_evidence se
          JOIN exploration_v3.association_revision_evidence ae
            ON ae.association_revision_id = se.association_revision_id
           AND ae.evidence_reference_id = se.evidence_reference_id
           AND ae.evidence_role IN ('supports','contextualises')
          WHERE se.association_revision_id = s.association_revision_id
            AND se.step_ordinal = s.step_ordinal))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ACTIVE_SYNTHESIS_STEPS_INVALID';
  ELSIF v_revision.support_mode IN ('DIRECT_PAIR', 'DIRECT_GROUP') AND EXISTS (
    SELECT 1 FROM exploration_v3.association_synthesis_step
    WHERE association_revision_id = p_association_revision_id
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'DIRECT_SUPPORT_HAS_SYNTHESIS_STEPS';
  END IF;

  IF v_revision.product_eligible AND v_association.realm <> 'PRODUCTION' THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'PRODUCT_ASSOCIATION_NOT_PRODUCTION';
  ELSIF v_revision.product_eligible AND EXISTS (
    SELECT 1 FROM exploration_v3.association_revision successor
    WHERE successor.association_id = v_revision.association_id
      AND successor.supersedes_association_revision_id = p_association_revision_id
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'PRODUCT_ASSOCIATION_REVISION_NOT_CURRENT_HEAD';
  ELSIF NOT v_revision.product_eligible
    AND v_association.realm = 'PRODUCTION'
    AND v_revision.product_eligibility_disposition NOT IN ('INELIGIBLE', 'DEFERRED') THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ACTIVE_PRODUCTION_PRODUCT_DISPOSITION_INVALID';
  END IF;
END
$function$;

CREATE FUNCTION exploration_v3.enforce_association_revision()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM exploration_v3.assert_association_revision(
    COALESCE(NEW.association_revision_id, OLD.association_revision_id));
  RETURN NULL;
END
$function$;

CREATE FUNCTION exploration_v3.assert_internal_pair_link(
  p_higher_order_revision_id text,
  p_pair_revision_id text,
  p_higher_incidence_a text,
  p_higher_incidence_b text,
  p_pair_incidence_a text,
  p_pair_incidence_b text
) RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
DECLARE v_higher_kind exploration_v3.association_kind;
DECLARE v_pair_kind exploration_v3.association_kind;
DECLARE v_higher_realm exploration_v3.realm;
DECLARE v_pair_realm exploration_v3.realm;
DECLARE v_higher_state exploration_v3.lifecycle_state;
DECLARE v_pair_state exploration_v3.lifecycle_state;
BEGIN
  SELECT a.association_kind, a.realm, r.lifecycle_state
  INTO STRICT v_higher_kind, v_higher_realm, v_higher_state
  FROM exploration_v3.association_revision r
  JOIN exploration_v3.association a ON a.association_id = r.association_id
  WHERE r.association_revision_id = p_higher_order_revision_id;
  SELECT a.association_kind, a.realm, r.lifecycle_state
  INTO STRICT v_pair_kind, v_pair_realm, v_pair_state
  FROM exploration_v3.association_revision r
  JOIN exploration_v3.association a ON a.association_id = r.association_id
  WHERE r.association_revision_id = p_pair_revision_id;
  IF v_higher_kind <> 'HIGHER_ORDER' OR v_pair_kind <> 'PAIR'
    OR v_higher_realm <> v_pair_realm
    OR (v_higher_state = 'ACTIVE' AND v_pair_state <> 'ACTIVE') THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'INTERNAL_PAIR_LINK_KIND_MISMATCH';
  END IF;
  IF (SELECT array_agg(sense_id ORDER BY sense_id)
      FROM exploration_v3.association_incidence
      WHERE incidence_id IN (p_higher_incidence_a, p_higher_incidence_b))
    IS DISTINCT FROM
    (SELECT array_agg(sense_id ORDER BY sense_id)
      FROM exploration_v3.association_incidence
      WHERE incidence_id IN (p_pair_incidence_a, p_pair_incidence_b)) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'INTERNAL_PAIR_LINK_SENSE_MISMATCH';
  END IF;
END
$function$;

CREATE FUNCTION exploration_v3.enforce_internal_pair_link()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM exploration_v3.assert_internal_pair_link(
    NEW.higher_order_revision_id, NEW.pair_revision_id,
    NEW.higher_incidence_a, NEW.higher_incidence_b,
    NEW.pair_incidence_a, NEW.pair_incidence_b);
  RETURN NEW;
END
$function$;

CREATE FUNCTION exploration_v3.assert_association_realization(
  p_association_realization_id text
) RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
DECLARE v_kind exploration_v3.association_kind;
DECLARE v_arity integer;
DECLARE v_realm exploration_v3.realm;
DECLARE v_composition_realm exploration_v3.realm;
DECLARE v_realization_kind exploration_v3.realization_kind;
DECLARE v_revision_id text;
BEGIN
  SELECT a.association_kind, a.arity, a.realm, c.realm,
    r.realization_kind, r.association_revision_id
  INTO STRICT v_kind, v_arity, v_realm, v_composition_realm,
    v_realization_kind, v_revision_id
  FROM exploration_v3.association_realization r
  JOIN exploration_v3.association_revision ar
    ON ar.association_revision_id = r.association_revision_id
  JOIN exploration_v3.association a ON a.association_id = ar.association_id
  JOIN exploration_v3.composition_revision cr
    ON cr.composition_revision_id = r.composition_revision_id
  JOIN exploration_v3.composition c ON c.composition_id = cr.composition_id
  WHERE r.association_realization_id = p_association_realization_id;
  IF v_realm <> v_composition_realm THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'REALIZATION_REALM_MISMATCH';
  END IF;
  IF (v_kind = 'PAIR' AND v_realization_kind <> 'PAIR_EDGE')
    OR (v_kind = 'HIGHER_ORDER' AND v_realization_kind = 'PAIR_EDGE') THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'REALIZATION_KIND_ASSOCIATION_MISMATCH';
  END IF;
  IF (SELECT count(*) FROM exploration_v3.realization_incidence
      WHERE association_realization_id = p_association_realization_id) <> v_arity
    OR EXISTS (
      SELECT 1 FROM exploration_v3.realization_incidence ri
      JOIN exploration_v3.association_incidence i ON i.incidence_id = ri.incidence_id
      WHERE ri.association_realization_id = p_association_realization_id
        AND i.association_revision_id <> v_revision_id
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'REALIZATION_INCIDENCE_COVERAGE_MISMATCH';
  END IF;
END
$function$;

CREATE FUNCTION exploration_v3.enforce_association_realization()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
DECLARE v_composition_revision_id text;
BEGIN
  SELECT composition_revision_id INTO STRICT v_composition_revision_id
  FROM exploration_v3.association_realization
  WHERE association_realization_id =
    COALESCE(NEW.association_realization_id, OLD.association_realization_id);
  PERFORM exploration_v3.assert_association_realization(
    COALESCE(NEW.association_realization_id, OLD.association_realization_id));
  PERFORM exploration_v3.assert_composition_revision(v_composition_revision_id);
  RETURN NULL;
END
$function$;

CREATE FUNCTION exploration_v3.assert_composition_revision(
  p_composition_revision_id text
) RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
DECLARE v_revision exploration_v3.composition_revision%ROWTYPE;
DECLARE v_realm exploration_v3.realm;
DECLARE v_review exploration_v3.composition_coherence_review%ROWTYPE;
DECLARE v_authority_state exploration_v3.authority_state;
DECLARE v_authority_kind exploration_v3.authority_kind;
DECLARE v_review_found boolean := false;
DECLARE v_superseded_revision_number integer;
BEGIN
  SELECT * INTO v_revision
  FROM exploration_v3.composition_revision
  WHERE composition_revision_id = p_composition_revision_id;
  IF NOT FOUND THEN RETURN; END IF;
  SELECT realm INTO STRICT v_realm FROM exploration_v3.composition
  WHERE composition_id = v_revision.composition_id;

  IF (v_realm = 'PRODUCTION' AND (
      (v_revision.product_eligible
        AND v_revision.product_eligibility_disposition <> 'ELIGIBLE')
      OR (NOT v_revision.product_eligible
        AND v_revision.product_eligibility_disposition NOT IN ('INELIGIBLE','DEFERRED'))
    )) OR (v_realm = 'SYNTHETIC_CONTROL' AND (
      v_revision.product_eligible
      OR v_revision.product_eligibility_disposition <> 'NOT_APPLICABLE_SYNTHETIC'
    )) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'COMPOSITION_PRODUCT_DISPOSITION_MATRIX_INVALID';
  END IF;
  IF EXISTS (
    SELECT 1 FROM exploration_v3.composition_node node
    JOIN exploration_v3.concept concept ON concept.concept_id = node.concept_id
    WHERE node.composition_revision_id = p_composition_revision_id
      AND concept.realm <> v_realm
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'COMPOSITION_NODE_REALM_MISMATCH';
  END IF;

  IF v_revision.revision_number = 1
    AND v_revision.supersedes_composition_revision_id IS NOT NULL THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'COMPOSITION_REVISION_LINEAGE_INVALID';
  ELSIF v_revision.revision_number > 1 THEN
    IF v_revision.supersedes_composition_revision_id IS NULL THEN
      RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'COMPOSITION_REVISION_LINEAGE_INVALID';
    END IF;
    SELECT revision_number INTO v_superseded_revision_number
    FROM exploration_v3.composition_revision
    WHERE composition_id = v_revision.composition_id
      AND composition_revision_id = v_revision.supersedes_composition_revision_id;
    IF NOT FOUND OR v_superseded_revision_number <> v_revision.revision_number - 1 THEN
      RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'COMPOSITION_REVISION_LINEAGE_INVALID';
    END IF;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM exploration_v3.association_realization
      WHERE composition_revision_id = p_composition_revision_id)
    OR EXISTS (
      SELECT 1
      FROM exploration_v3.association_realization ar
      JOIN exploration_v3.association_revision r
        ON r.association_revision_id = ar.association_revision_id
      JOIN exploration_v3.association a ON a.association_id = r.association_id
      WHERE ar.composition_revision_id = p_composition_revision_id
        AND a.realm <> v_realm
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'COMPOSITION_ASSOCIATION_TRACE_INVALID';
  END IF;
  IF v_revision.association_trace_complete AND (
    EXISTS (
      SELECT i.concept_id
      FROM exploration_v3.association_realization ar
      JOIN exploration_v3.realization_incidence ri USING (association_realization_id)
      JOIN exploration_v3.association_incidence i USING (incidence_id)
      WHERE ar.composition_revision_id = p_composition_revision_id
      EXCEPT
      SELECT concept_id FROM exploration_v3.composition_node
      WHERE composition_revision_id = p_composition_revision_id
    ) OR EXISTS (
      SELECT concept_id FROM exploration_v3.composition_node
      WHERE composition_revision_id = p_composition_revision_id
      EXCEPT
      SELECT i.concept_id
      FROM exploration_v3.association_realization ar
      JOIN exploration_v3.realization_incidence ri USING (association_realization_id)
      JOIN exploration_v3.association_incidence i USING (incidence_id)
      WHERE ar.composition_revision_id = p_composition_revision_id
    )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'COMPOSITION_NODE_TRACE_MISMATCH';
  END IF;

  SELECT * INTO v_review
  FROM exploration_v3.composition_coherence_review
  WHERE composition_revision_id = p_composition_revision_id;
  IF FOUND THEN
    v_review_found := true;
    SELECT authority_state, authority_kind
    INTO STRICT v_authority_state, v_authority_kind
    FROM exploration_v3.governed_authority WHERE authority_id = v_review.authority_id;
    IF v_review.realm <> v_realm THEN
      RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'COMPOSITION_REVIEW_REALM_MISMATCH';
    END IF;
    IF EXISTS (
      SELECT association_realization_id
      FROM exploration_v3.association_realization
      WHERE composition_revision_id = p_composition_revision_id
      EXCEPT
      SELECT rr.association_realization_id
      FROM exploration_v3.composition_review_realization rr
      WHERE rr.composition_coherence_review_id = v_review.composition_coherence_review_id
    ) OR EXISTS (
      SELECT rr.association_realization_id
      FROM exploration_v3.composition_review_realization rr
      WHERE rr.composition_coherence_review_id = v_review.composition_coherence_review_id
      EXCEPT
      SELECT association_realization_id
      FROM exploration_v3.association_realization
      WHERE composition_revision_id = p_composition_revision_id
    ) THEN
      RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'COMPOSITION_REVIEW_TRACE_MISMATCH';
    END IF;
    IF v_review.review_state = 'FINAL' AND NOT EXISTS (
      SELECT 1 FROM exploration_v3.aggregate_seal
      WHERE aggregate_kind = 'COMPOSITION_REVISION'
        AND aggregate_id = p_composition_revision_id
    ) THEN
      RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'FINAL_COMPOSITION_REVIEW_UNSEALED';
    END IF;
    IF v_review.review_state = 'FINAL' AND (
      v_authority_state <> 'FINAL'
      OR (v_realm = 'PRODUCTION'
        AND v_authority_kind = 'SYNTHETIC_TEST_AUTHORITY')
      OR (v_review.decision = 'COHERENT' AND (
        v_review.global_coherence <> 'PASS'
        OR NOT v_review.bounded_senses_compatible
        OR NOT v_review.case_scope_compatible
        OR NOT v_review.roles_and_topology_supported
        OR NOT v_review.same_configuration
        OR v_review.unsupported_bridge_count <> 0))
      OR (v_review.decision = 'INCOHERENT' AND (
        v_review.global_coherence <> 'FAIL'
        OR (v_review.bounded_senses_compatible
          AND v_review.case_scope_compatible
          AND v_review.roles_and_topology_supported
          AND v_review.same_configuration
          AND v_review.unsupported_bridge_count = 0)))
      OR (v_review.decision = 'UNRESOLVED'
        AND v_review.global_coherence <> 'UNRESOLVED')
    ) THEN
      RAISE EXCEPTION USING ERRCODE = '23514',
        MESSAGE = 'FINAL_COMPOSITION_REVIEW_PARITY_INVALID';
    ELSIF v_review.review_state <> 'FINAL'
      AND v_review.decision = 'COHERENT' THEN
      RAISE EXCEPTION USING ERRCODE = '23514',
        MESSAGE = 'COHERENT_COMPOSITION_REVIEW_PARITY_INVALID';
    END IF;
  END IF;

  IF NOT v_revision.product_eligible THEN RETURN; END IF;
  IF NOT EXISTS (
    SELECT 1 FROM exploration_v3.aggregate_seal
    WHERE aggregate_kind = 'COMPOSITION_REVISION'
      AND aggregate_id = p_composition_revision_id
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'PRODUCT_COMPOSITION_UNSEALED';
  END IF;
  IF v_realm <> 'PRODUCTION' OR NOT v_revision.association_trace_complete
    OR v_revision.renderability <> 'PASS' OR NOT v_review_found THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'PRODUCT_COMPOSITION_BASE_GATE_FAILURE';
  END IF;
  IF EXISTS (
    SELECT 1 FROM exploration_v3.composition_revision successor
    WHERE successor.composition_id = v_revision.composition_id
      AND successor.supersedes_composition_revision_id = p_composition_revision_id
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'PRODUCT_COMPOSITION_REVISION_NOT_CURRENT_HEAD';
  END IF;
  IF v_review.review_state <> 'FINAL' OR v_review.decision <> 'COHERENT'
    OR v_review.global_coherence <> 'PASS' OR NOT v_review.bounded_senses_compatible
    OR NOT v_review.case_scope_compatible OR NOT v_review.roles_and_topology_supported
    OR NOT v_review.same_configuration OR v_review.unsupported_bridge_count <> 0
    OR v_authority_state <> 'FINAL' OR v_authority_kind = 'SYNTHETIC_TEST_AUTHORITY' THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'PRODUCT_COMPOSITION_REVIEW_GATE_FAILURE';
  END IF;
  IF EXISTS (
    SELECT 1 FROM exploration_v3.association_realization ar
    WHERE ar.composition_revision_id = p_composition_revision_id
      AND NOT EXISTS (
        SELECT 1
        FROM exploration_v3.association_revision r
        JOIN exploration_v3.association a ON a.association_id = r.association_id
        JOIN exploration_v3.association_review rv
          ON rv.association_revision_id = r.association_revision_id
        JOIN exploration_v3.governed_authority au ON au.authority_id = rv.authority_id
        WHERE r.association_revision_id = ar.association_revision_id
          AND r.lifecycle_state = 'ACTIVE' AND r.product_eligible
          AND NOT EXISTS (
            SELECT 1 FROM exploration_v3.association_revision successor
            WHERE successor.association_id = r.association_id
              AND successor.supersedes_association_revision_id = r.association_revision_id)
          AND a.realm = 'PRODUCTION' AND rv.review_state = 'FINAL'
          AND rv.global_coherence = 'PASS' AND rv.bounded_senses_compatible
          AND rv.case_scope_compatible AND rv.roles_and_topology_supported
          AND rv.unsupported_bridge_count = 0 AND au.authority_state = 'FINAL'
          AND au.authority_kind <> 'SYNTHETIC_TEST_AUTHORITY')
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'PRODUCT_COMPOSITION_ASSOCIATION_INELIGIBLE';
  END IF;
END
$function$;

CREATE FUNCTION exploration_v3.enforce_composition_revision()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM exploration_v3.assert_composition_revision(
    COALESCE(NEW.composition_revision_id, OLD.composition_revision_id));
  RETURN NULL;
END
$function$;

CREATE FUNCTION exploration_v3.enforce_composition_review_realization()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
DECLARE v_composition_revision_id text;
BEGIN
  SELECT r.composition_revision_id INTO STRICT v_composition_revision_id
  FROM exploration_v3.composition_review_realization rr
  JOIN exploration_v3.composition_coherence_review r
    ON r.composition_coherence_review_id = rr.composition_coherence_review_id
  WHERE rr.composition_coherence_review_id =
      COALESCE(NEW.composition_coherence_review_id, OLD.composition_coherence_review_id)
    AND rr.association_realization_id =
      COALESCE(NEW.association_realization_id, OLD.association_realization_id);
  PERFORM exploration_v3.assert_composition_revision(v_composition_revision_id);
  RETURN NULL;
END
$function$;

CREATE FUNCTION exploration_v3.assert_navigation_state(p_state_id text)
RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
DECLARE v_composition_revision_id text;
DECLARE v_realm exploration_v3.realm;
DECLARE v_composition_realm exploration_v3.realm;
BEGIN
  SELECT composition_revision_id, realm INTO v_composition_revision_id, v_realm
  FROM exploration_v3.navigation_state WHERE state_id = p_state_id;
  IF NOT FOUND THEN RETURN; END IF;
  SELECT c.realm INTO STRICT v_composition_realm
  FROM exploration_v3.composition_revision cr
  JOIN exploration_v3.composition c ON c.composition_id = cr.composition_id
  WHERE cr.composition_revision_id = v_composition_revision_id;
  IF v_realm <> v_composition_realm THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'NAVIGATION_STATE_REALM_MISMATCH';
  END IF;
  IF (SELECT count(*) FROM exploration_v3.navigation_node WHERE state_id = p_state_id) < 3
    OR NOT EXISTS (SELECT 1 FROM exploration_v3.navigation_node n
      JOIN exploration_v3.navigation_state s ON s.state_id = n.state_id
      WHERE n.state_id = p_state_id
        AND n.navigation_node_id = s.focus_navigation_node_id)
    OR NOT EXISTS (SELECT 1 FROM exploration_v3.navigation_path_step WHERE state_id = p_state_id)
    OR (SELECT min(step_ordinal) FROM exploration_v3.navigation_path_step
        WHERE state_id = p_state_id) <> 0
    OR (SELECT max(step_ordinal) FROM exploration_v3.navigation_path_step
        WHERE state_id = p_state_id) + 1 <>
       (SELECT count(*) FROM exploration_v3.navigation_path_step WHERE state_id = p_state_id) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'NAVIGATION_STATE_SHAPE_INVALID';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM exploration_v3.navigation_path_step current_step
    JOIN exploration_v3.navigation_path_step next_step
      ON next_step.state_id = current_step.state_id
     AND next_step.step_ordinal = current_step.step_ordinal + 1
    WHERE current_step.state_id = p_state_id
      AND current_step.to_navigation_node_id <> next_step.from_navigation_node_id
  ) OR (
    SELECT to_navigation_node_id
    FROM exploration_v3.navigation_path_step
    WHERE state_id = p_state_id
    ORDER BY step_ordinal DESC
    LIMIT 1
  ) <> (
    SELECT focus_navigation_node_id
    FROM exploration_v3.navigation_state WHERE state_id = p_state_id
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'NAVIGATION_PATH_CONTINUITY_OR_TERMINAL_FOCUS_INVALID';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM exploration_v3.navigation_path_step p
    JOIN exploration_v3.navigation_node f
      ON f.state_id = p.state_id AND f.navigation_node_id = p.from_navigation_node_id
    JOIN exploration_v3.navigation_node t
      ON t.state_id = p.state_id AND t.navigation_node_id = p.to_navigation_node_id
    JOIN exploration_v3.association_incidence i ON i.incidence_id = p.incidence_id
    WHERE p.state_id = p_state_id
      AND (f.node_kind = t.node_kind OR NOT (
        (f.node_kind = 'ASSOCIATION' AND f.association_revision_id = i.association_revision_id
          AND t.node_kind = 'CONCEPT' AND t.concept_id = i.concept_id)
        OR
        (t.node_kind = 'ASSOCIATION' AND t.association_revision_id = i.association_revision_id
          AND f.node_kind = 'CONCEPT' AND f.concept_id = i.concept_id)
      ))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'NAVIGATION_INCIDENCE_PATH_INVALID';
  END IF;
  IF EXISTS (
    SELECT 1 FROM exploration_v3.navigation_node n
    WHERE n.state_id = p_state_id AND (
      (n.node_kind = 'CONCEPT' AND NOT EXISTS (
        SELECT 1 FROM exploration_v3.composition_node cn
        WHERE cn.composition_revision_id = v_composition_revision_id
          AND cn.concept_id = n.concept_id))
      OR
      (n.node_kind = 'ASSOCIATION' AND NOT EXISTS (
        SELECT 1 FROM exploration_v3.association_realization ar
        WHERE ar.composition_revision_id = v_composition_revision_id
          AND ar.association_revision_id = n.association_revision_id))
    )
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'NAVIGATION_NODE_OUTSIDE_COMPOSITION';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM exploration_v3.aggregate_seal
    WHERE aggregate_kind = 'NAVIGATION_STATE' AND aggregate_id = p_state_id
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'NAVIGATION_STATE_UNSEALED';
  END IF;
END
$function$;

CREATE FUNCTION exploration_v3.enforce_navigation_state()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM exploration_v3.assert_navigation_state(COALESCE(NEW.state_id, OLD.state_id));
  RETURN NULL;
END
$function$;

CREATE FUNCTION exploration_v3.assert_interaction_transition(p_transition_id text)
RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
DECLARE v_transition exploration_v3.interaction_transition%ROWTYPE;
DECLARE v_from_composition text;
DECLARE v_to_composition text;
DECLARE v_expected_composition_count integer;
BEGIN
  SELECT * INTO v_transition FROM exploration_v3.interaction_transition
  WHERE transition_id = p_transition_id;
  IF NOT FOUND THEN RETURN; END IF;
  SELECT composition_revision_id INTO STRICT v_from_composition
  FROM exploration_v3.navigation_state
  WHERE state_id = v_transition.from_state_id AND realm = v_transition.realm;
  SELECT composition_revision_id INTO STRICT v_to_composition
  FROM exploration_v3.navigation_state
  WHERE state_id = v_transition.to_state_id AND realm = v_transition.realm;
  IF (v_transition.incidence_id IS NULL) <> (v_transition.association_revision_id IS NULL)
    OR (v_transition.association_revision_id IS NULL) <>
       (v_transition.association_realization_id IS NULL) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'TRANSITION_TRACE_PARTIAL';
  END IF;
  IF v_transition.association_revision_id IS NOT NULL AND (
    v_from_composition <> v_to_composition
    OR NOT EXISTS (
      SELECT 1
      FROM exploration_v3.association_incidence i
      JOIN exploration_v3.association_realization ar
        ON ar.association_realization_id = v_transition.association_realization_id
      WHERE i.incidence_id = v_transition.incidence_id
        AND i.association_revision_id = v_transition.association_revision_id
        AND ar.association_revision_id = v_transition.association_revision_id
        AND ar.composition_revision_id = v_from_composition
        AND EXISTS (SELECT 1 FROM exploration_v3.realization_incidence ri
          WHERE ri.association_realization_id = ar.association_realization_id
            AND ri.incidence_id = i.incidence_id))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'TRANSITION_INCIDENCE_TRACE_INVALID';
  END IF;
  IF NOT v_transition.product_eligible THEN RETURN; END IF;
  v_expected_composition_count := CASE
    WHEN v_from_composition = v_to_composition THEN 1 ELSE 2 END;
  IF EXISTS (
    SELECT 1 FROM exploration_v3.composition_revision cr
    WHERE cr.composition_revision_id IN (v_from_composition, v_to_composition)
      AND (NOT cr.product_eligible OR EXISTS (
        SELECT 1 FROM exploration_v3.composition_revision successor
        WHERE successor.composition_id = cr.composition_id
          AND successor.supersedes_composition_revision_id =
            cr.composition_revision_id))
  ) OR (SELECT count(*) FROM exploration_v3.composition_revision
        WHERE composition_revision_id IN (v_from_composition, v_to_composition)) <
       v_expected_composition_count THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'PRODUCT_TRANSITION_COMPOSITION_INELIGIBLE';
  END IF;
  IF v_transition.association_revision_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM exploration_v3.association_revision r
    JOIN exploration_v3.association a ON a.association_id = r.association_id
    JOIN exploration_v3.association_review rv
      ON rv.association_revision_id = r.association_revision_id
    JOIN exploration_v3.governed_authority au ON au.authority_id = rv.authority_id
    WHERE r.association_revision_id = v_transition.association_revision_id
      AND r.lifecycle_state = 'ACTIVE' AND r.product_eligible
      AND NOT EXISTS (
        SELECT 1 FROM exploration_v3.association_revision successor
        WHERE successor.association_id = r.association_id
          AND successor.supersedes_association_revision_id = r.association_revision_id)
      AND a.realm = 'PRODUCTION' AND rv.review_state = 'FINAL'
      AND rv.global_coherence = 'PASS' AND au.authority_state = 'FINAL'
      AND au.authority_kind <> 'SYNTHETIC_TEST_AUTHORITY'
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'PRODUCT_TRANSITION_ASSOCIATION_INELIGIBLE';
  END IF;
END
$function$;

CREATE FUNCTION exploration_v3.enforce_interaction_transition()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM exploration_v3.assert_interaction_transition(
    COALESCE(NEW.transition_id, OLD.transition_id));
  RETURN NULL;
END
$function$;

CREATE FUNCTION exploration_v3.assert_workflow(p_workflow_id text)
RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
DECLARE v_workflow exploration_v3.exploration_workflow%ROWTYPE;
DECLARE v_derived_reachable boolean;
BEGIN
  SELECT * INTO v_workflow FROM exploration_v3.exploration_workflow
  WHERE workflow_id = p_workflow_id;
  IF NOT FOUND THEN RETURN; END IF;
  IF NOT EXISTS (SELECT 1 FROM exploration_v3.workflow_state
      WHERE workflow_id = p_workflow_id AND state_id = v_workflow.initial_state_id)
    OR NOT EXISTS (SELECT 1 FROM exploration_v3.workflow_association_revision
      WHERE workflow_id = p_workflow_id)
    OR NOT EXISTS (SELECT 1 FROM exploration_v3.workflow_association_realization
      WHERE workflow_id = p_workflow_id)
    OR NOT EXISTS (SELECT 1 FROM exploration_v3.workflow_transition
      WHERE workflow_id = p_workflow_id)
    OR EXISTS (
      SELECT 1 FROM exploration_v3.workflow_state ws
      JOIN exploration_v3.navigation_state s ON s.state_id = ws.state_id
      WHERE ws.workflow_id = p_workflow_id AND s.realm <> v_workflow.realm)
    OR EXISTS (
      SELECT 1 FROM exploration_v3.workflow_association_realization wr
      JOIN exploration_v3.association_realization ar
        ON ar.association_realization_id = wr.association_realization_id
      WHERE wr.workflow_id = p_workflow_id AND NOT EXISTS (
        SELECT 1 FROM exploration_v3.workflow_association_revision wa
        WHERE wa.workflow_id = p_workflow_id
          AND wa.association_revision_id = ar.association_revision_id))
    OR EXISTS (
      SELECT wa.association_revision_id
      FROM exploration_v3.workflow_association_revision wa
      WHERE wa.workflow_id = p_workflow_id
      EXCEPT
      SELECT ar.association_revision_id
      FROM exploration_v3.workflow_association_realization wr
      JOIN exploration_v3.association_realization ar
        ON ar.association_realization_id = wr.association_realization_id
      WHERE wr.workflow_id = p_workflow_id)
    OR EXISTS (
      SELECT 1 FROM exploration_v3.workflow_association_realization wr
      JOIN exploration_v3.association_realization ar
        ON ar.association_realization_id = wr.association_realization_id
      WHERE wr.workflow_id = p_workflow_id
        AND NOT EXISTS (
          SELECT 1 FROM exploration_v3.workflow_state ws
          JOIN exploration_v3.navigation_state s ON s.state_id = ws.state_id
          WHERE ws.workflow_id = p_workflow_id
            AND s.composition_revision_id = ar.composition_revision_id))
    OR EXISTS (
      SELECT ar.association_realization_id
      FROM exploration_v3.workflow_state ws
      JOIN exploration_v3.navigation_state s ON s.state_id = ws.state_id
      JOIN exploration_v3.association_realization ar
        ON ar.composition_revision_id = s.composition_revision_id
      WHERE ws.workflow_id = p_workflow_id
      EXCEPT
      SELECT wr.association_realization_id
      FROM exploration_v3.workflow_association_realization wr
      WHERE wr.workflow_id = p_workflow_id)
    OR EXISTS (
      SELECT 1 FROM exploration_v3.workflow_transition wt
      JOIN exploration_v3.interaction_transition t ON t.transition_id = wt.transition_id
      WHERE wt.workflow_id = p_workflow_id
        AND (t.realm <> v_workflow.realm OR t.transition_kind <> v_workflow.transition_kind
          OR NOT EXISTS (SELECT 1 FROM exploration_v3.workflow_state ws
            WHERE ws.workflow_id = p_workflow_id AND ws.state_id = t.from_state_id)
          OR NOT EXISTS (SELECT 1 FROM exploration_v3.workflow_state ws
            WHERE ws.workflow_id = p_workflow_id AND ws.state_id = t.to_state_id)))
  THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'WORKFLOW_TRACE_INVALID';
  END IF;
  WITH RECURSIVE reached(state_id) AS (
    SELECT v_workflow.initial_state_id
    UNION
    SELECT transition_row.to_state_id
    FROM reached
    JOIN exploration_v3.workflow_transition workflow_edge
      ON workflow_edge.workflow_id = p_workflow_id
    JOIN exploration_v3.interaction_transition transition_row
      ON transition_row.transition_id = workflow_edge.transition_id
     AND transition_row.from_state_id = reached.state_id
  )
  SELECT NOT EXISTS (
    SELECT state_id FROM exploration_v3.workflow_state
    WHERE workflow_id = p_workflow_id
    EXCEPT
    SELECT state_id FROM reached
  ) INTO v_derived_reachable;
  IF v_workflow.reachable <> v_derived_reachable THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'WORKFLOW_REACHABILITY_ASSERTION_MISMATCH';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM exploration_v3.aggregate_seal
    WHERE aggregate_kind = 'WORKFLOW' AND aggregate_id = p_workflow_id
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'WORKFLOW_UNSEALED';
  END IF;
  IF v_workflow.product_eligible AND (
    EXISTS (
      SELECT 1 FROM exploration_v3.workflow_state ws
      JOIN exploration_v3.navigation_state s ON s.state_id = ws.state_id
      WHERE ws.workflow_id = p_workflow_id
        AND NOT EXISTS (
          SELECT 1
          FROM exploration_v3.composition_revision c
          JOIN exploration_v3.composition_coherence_review rv
            ON rv.composition_revision_id = c.composition_revision_id
          JOIN exploration_v3.governed_authority au ON au.authority_id = rv.authority_id
          WHERE c.composition_revision_id = s.composition_revision_id
            AND c.product_eligible AND rv.review_state = 'FINAL'
            AND NOT EXISTS (
              SELECT 1 FROM exploration_v3.composition_revision successor
              WHERE successor.composition_id = c.composition_id
                AND successor.supersedes_composition_revision_id = c.composition_revision_id)
            AND rv.decision = 'COHERENT' AND rv.global_coherence = 'PASS'
            AND rv.bounded_senses_compatible AND rv.case_scope_compatible
            AND rv.roles_and_topology_supported AND rv.same_configuration
            AND rv.unsupported_bridge_count = 0 AND au.authority_state = 'FINAL'
            AND au.authority_kind <> 'SYNTHETIC_TEST_AUTHORITY'))
    OR EXISTS (
      SELECT 1 FROM exploration_v3.workflow_transition wt
      JOIN exploration_v3.interaction_transition t ON t.transition_id = wt.transition_id
      WHERE wt.workflow_id = p_workflow_id AND NOT t.product_eligible)
    OR EXISTS (
      SELECT 1 FROM exploration_v3.workflow_association_revision wa
      WHERE wa.workflow_id = p_workflow_id
        AND NOT EXISTS (
          SELECT 1
          FROM exploration_v3.association_revision r
          JOIN exploration_v3.association a ON a.association_id = r.association_id
          JOIN exploration_v3.association_review rv
            ON rv.association_revision_id = r.association_revision_id
          JOIN exploration_v3.governed_authority au ON au.authority_id = rv.authority_id
          WHERE r.association_revision_id = wa.association_revision_id
            AND r.lifecycle_state = 'ACTIVE' AND r.product_eligible
            AND NOT EXISTS (
              SELECT 1 FROM exploration_v3.association_revision successor
              WHERE successor.association_id = r.association_id
                AND successor.supersedes_association_revision_id = r.association_revision_id)
            AND a.realm = 'PRODUCTION' AND rv.review_state = 'FINAL'
            AND rv.global_coherence = 'PASS' AND rv.bounded_senses_compatible
            AND rv.case_scope_compatible AND rv.roles_and_topology_supported
            AND rv.unsupported_bridge_count = 0 AND au.authority_state = 'FINAL'
            AND au.authority_kind <> 'SYNTHETIC_TEST_AUTHORITY'))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'PRODUCT_WORKFLOW_DEPENDENCY_INELIGIBLE';
  END IF;
END
$function$;

CREATE FUNCTION exploration_v3.enforce_workflow()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM exploration_v3.assert_workflow(COALESCE(NEW.workflow_id, OLD.workflow_id));
  RETURN NULL;
END
$function$;

CREATE FUNCTION exploration_v3.assert_export(p_export_id text)
RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
DECLARE v_export exploration_v3.export_manifest%ROWTYPE;
DECLARE v_workflow_realm exploration_v3.realm;
DECLARE v_state_realm exploration_v3.realm;
DECLARE v_composition_realm exploration_v3.realm;
BEGIN
  SELECT * INTO v_export FROM exploration_v3.export_manifest WHERE export_id = p_export_id;
  IF NOT FOUND THEN RETURN; END IF;
  SELECT realm INTO STRICT v_workflow_realm
  FROM exploration_v3.exploration_workflow WHERE workflow_id = v_export.workflow_id;
  SELECT realm INTO STRICT v_state_realm
  FROM exploration_v3.navigation_state WHERE state_id = v_export.state_id;
  SELECT c.realm INTO STRICT v_composition_realm
  FROM exploration_v3.composition_revision cr
  JOIN exploration_v3.composition c ON c.composition_id = cr.composition_id
  WHERE cr.composition_revision_id = v_export.composition_revision_id;
  IF v_export.realm <> v_workflow_realm OR v_export.realm <> v_state_realm
    OR v_export.realm <> v_composition_realm THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'EXPORT_REALM_MISMATCH';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM exploration_v3.workflow_state
    WHERE workflow_id = v_export.workflow_id AND state_id = v_export.state_id)
    OR (SELECT composition_revision_id FROM exploration_v3.navigation_state
        WHERE state_id = v_export.state_id) <> v_export.composition_revision_id
    OR NOT EXISTS (SELECT 1 FROM exploration_v3.export_projection_preservation
      WHERE export_id = p_export_id)
    OR EXISTS (
      SELECT 1 FROM exploration_v3.export_projection_preservation p
      JOIN exploration_v3.association_realization ar
        ON ar.association_realization_id = p.association_realization_id
      JOIN exploration_v3.association_revision r
        ON r.association_revision_id = p.association_revision_id
      JOIN exploration_v3.association a ON a.association_id = r.association_id
      WHERE p.export_id = p_export_id
        AND (ar.association_revision_id <> p.association_revision_id
          OR ar.composition_revision_id <> v_export.composition_revision_id
          OR a.pair_projection_policy <> p.pair_projection_policy
          OR ar.realization_kind <> p.realization_kind
          OR (a.association_kind = 'HIGHER_ORDER' AND p.realization_kind = 'PAIR_EDGE')))
    OR EXISTS (
      SELECT association_realization_id
      FROM exploration_v3.workflow_association_realization
      WHERE workflow_id = v_export.workflow_id
      EXCEPT
      SELECT association_realization_id
      FROM exploration_v3.export_projection_preservation
      WHERE export_id = p_export_id)
    OR EXISTS (
      SELECT association_realization_id
      FROM exploration_v3.export_projection_preservation
      WHERE export_id = p_export_id
      EXCEPT
      SELECT association_realization_id
      FROM exploration_v3.workflow_association_realization
      WHERE workflow_id = v_export.workflow_id)
    OR EXISTS (
      SELECT association_realization_id
      FROM exploration_v3.association_realization
      WHERE composition_revision_id = v_export.composition_revision_id
      EXCEPT
      SELECT association_realization_id
      FROM exploration_v3.export_projection_preservation
      WHERE export_id = p_export_id)
    OR EXISTS (
      SELECT association_realization_id
      FROM exploration_v3.export_projection_preservation
      WHERE export_id = p_export_id
      EXCEPT
      SELECT association_realization_id
      FROM exploration_v3.association_realization
      WHERE composition_revision_id = v_export.composition_revision_id)
  THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'EXPORT_PROJECTION_PRESERVATION_INVALID';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM exploration_v3.aggregate_seal
    WHERE aggregate_kind = 'EXPORT' AND aggregate_id = p_export_id
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'EXPORT_UNSEALED';
  END IF;
  IF v_export.product_eligible AND (
    NOT (SELECT product_eligible FROM exploration_v3.exploration_workflow
      WHERE workflow_id = v_export.workflow_id)
    OR NOT EXISTS (
      SELECT 1
      FROM exploration_v3.composition_revision c
      JOIN exploration_v3.composition_coherence_review rv
        ON rv.composition_revision_id = c.composition_revision_id
      JOIN exploration_v3.governed_authority au ON au.authority_id = rv.authority_id
      WHERE c.composition_revision_id = v_export.composition_revision_id
        AND c.product_eligible AND rv.review_state = 'FINAL'
        AND NOT EXISTS (
          SELECT 1 FROM exploration_v3.composition_revision successor
          WHERE successor.composition_id = c.composition_id
            AND successor.supersedes_composition_revision_id = c.composition_revision_id)
        AND rv.decision = 'COHERENT' AND rv.global_coherence = 'PASS'
        AND rv.bounded_senses_compatible AND rv.case_scope_compatible
        AND rv.roles_and_topology_supported AND rv.same_configuration
        AND rv.unsupported_bridge_count = 0 AND au.authority_state = 'FINAL'
        AND au.authority_kind <> 'SYNTHETIC_TEST_AUTHORITY')
    OR EXISTS (
      SELECT 1 FROM exploration_v3.export_projection_preservation p
      WHERE p.export_id = p_export_id
        AND NOT EXISTS (
          SELECT 1
          FROM exploration_v3.association_revision r
          JOIN exploration_v3.association a ON a.association_id = r.association_id
          JOIN exploration_v3.association_review rv
            ON rv.association_revision_id = r.association_revision_id
          JOIN exploration_v3.governed_authority au ON au.authority_id = rv.authority_id
          WHERE r.association_revision_id = p.association_revision_id
            AND r.lifecycle_state = 'ACTIVE' AND r.product_eligible
            AND NOT EXISTS (
              SELECT 1 FROM exploration_v3.association_revision successor
              WHERE successor.association_id = r.association_id
                AND successor.supersedes_association_revision_id = r.association_revision_id)
            AND a.realm = 'PRODUCTION' AND rv.review_state = 'FINAL'
            AND rv.global_coherence = 'PASS' AND rv.bounded_senses_compatible
            AND rv.case_scope_compatible AND rv.roles_and_topology_supported
            AND rv.unsupported_bridge_count = 0 AND au.authority_state = 'FINAL'
            AND au.authority_kind <> 'SYNTHETIC_TEST_AUTHORITY'))
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'PRODUCT_EXPORT_DEPENDENCY_INELIGIBLE';
  END IF;
END
$function$;

CREATE FUNCTION exploration_v3.enforce_export()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog
AS $function$
BEGIN
  PERFORM exploration_v3.assert_export(COALESCE(NEW.export_id, OLD.export_id));
  RETURN NULL;
END
$function$;

CREATE CONSTRAINT TRIGGER concept_integrity
AFTER INSERT OR UPDATE ON exploration_v3.concept
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_vocabulary_object();
CREATE CONSTRAINT TRIGGER concept_sense_integrity
AFTER INSERT OR UPDATE ON exploration_v3.concept_sense
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_vocabulary_object();
CREATE CONSTRAINT TRIGGER concept_sense_scope_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.concept_sense_scope
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_vocabulary_object();
CREATE TRIGGER aggregate_seal_content_guard
BEFORE INSERT ON exploration_v3.aggregate_seal
FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_aggregate_seal_insert();
CREATE CONSTRAINT TRIGGER aggregate_seal_integrity
AFTER INSERT OR UPDATE ON exploration_v3.aggregate_seal
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_aggregate_seal();

-- Aggregate children are insertable only until their parent aggregate is
-- explicitly sealed.  Every subsequent correction therefore needs a new
-- governed revision/identity, rather than a silent child-row append.
DO $sealed_child_insert_triggers$
DECLARE v_table text;
BEGIN
  FOREACH v_table IN ARRAY ARRAY[
    'evidence_locator','concept_sense_scope','association_incidence',
    'association_revision_evidence','association_synthesis_step',
    'association_synthesis_step_evidence','association_conflict_resolution',
    'association_review','internal_pair_link','composition_node',
    'association_realization','realization_incidence','composition_coherence_review',
    'composition_review_realization','navigation_node','navigation_path_step',
    'workflow_state','workflow_association_revision','workflow_association_realization',
    'workflow_transition','export_projection_preservation'
  ]
  LOOP
    EXECUTE pg_catalog.format(
      'CREATE TRIGGER %I_sealed_parent BEFORE INSERT ON exploration_v3.%I '
      'FOR EACH ROW EXECUTE FUNCTION exploration_v3.reject_sealed_child_insert()',
      v_table, v_table);
  END LOOP;
END
$sealed_child_insert_triggers$;

CREATE CONSTRAINT TRIGGER association_revision_integrity
AFTER INSERT OR UPDATE ON exploration_v3.association_revision
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_association_revision();
CREATE CONSTRAINT TRIGGER association_incidence_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.association_incidence
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_association_revision();
CREATE CONSTRAINT TRIGGER association_evidence_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.association_revision_evidence
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_association_revision();
CREATE CONSTRAINT TRIGGER association_synthesis_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.association_synthesis_step
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_association_revision();
CREATE CONSTRAINT TRIGGER association_synthesis_evidence_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.association_synthesis_step_evidence
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_association_revision();
CREATE CONSTRAINT TRIGGER association_review_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.association_review
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_association_revision();
CREATE CONSTRAINT TRIGGER association_conflict_resolution_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.association_conflict_resolution
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_association_revision();
CREATE CONSTRAINT TRIGGER internal_pair_link_integrity
AFTER INSERT OR UPDATE ON exploration_v3.internal_pair_link
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_internal_pair_link();

CREATE CONSTRAINT TRIGGER association_realization_integrity
AFTER INSERT OR UPDATE ON exploration_v3.association_realization
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_association_realization();
CREATE CONSTRAINT TRIGGER realization_incidence_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.realization_incidence
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_association_realization();
CREATE CONSTRAINT TRIGGER composition_revision_integrity
AFTER INSERT OR UPDATE ON exploration_v3.composition_revision
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_composition_revision();
CREATE CONSTRAINT TRIGGER composition_node_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.composition_node
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_composition_revision();
CREATE CONSTRAINT TRIGGER composition_review_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.composition_coherence_review
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_composition_revision();
CREATE CONSTRAINT TRIGGER composition_review_realization_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.composition_review_realization
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_composition_review_realization();

CREATE CONSTRAINT TRIGGER navigation_state_integrity
AFTER INSERT OR UPDATE ON exploration_v3.navigation_state
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_navigation_state();
CREATE CONSTRAINT TRIGGER navigation_node_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.navigation_node
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_navigation_state();
CREATE CONSTRAINT TRIGGER navigation_path_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.navigation_path_step
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_navigation_state();

CREATE CONSTRAINT TRIGGER interaction_transition_integrity
AFTER INSERT OR UPDATE ON exploration_v3.interaction_transition
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_interaction_transition();

CREATE CONSTRAINT TRIGGER workflow_integrity
AFTER INSERT OR UPDATE ON exploration_v3.exploration_workflow
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_workflow();
CREATE CONSTRAINT TRIGGER workflow_state_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.workflow_state
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_workflow();
CREATE CONSTRAINT TRIGGER workflow_revision_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.workflow_association_revision
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_workflow();
CREATE CONSTRAINT TRIGGER workflow_realization_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.workflow_association_realization
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_workflow();
CREATE CONSTRAINT TRIGGER workflow_transition_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.workflow_transition
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_workflow();

CREATE CONSTRAINT TRIGGER export_integrity
AFTER INSERT OR UPDATE ON exploration_v3.export_manifest
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_export();
CREATE CONSTRAINT TRIGGER export_projection_integrity
AFTER INSERT OR UPDATE OR DELETE ON exploration_v3.export_projection_preservation
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION exploration_v3.enforce_export();

-- Every governed record is append-only.  A correction creates a new revision;
-- already reviewed research identity is never edited in place.
DO $append_only_triggers$
DECLARE v_table text;
BEGIN
  FOREACH v_table IN ARRAY ARRAY[
    'governed_authority','governed_scope','concept','concept_sense','concept_sense_scope',
    'evidence_reference','evidence_locator','association','association_revision',
    'association_incidence','association_revision_evidence','association_synthesis_step',
    'association_synthesis_step_evidence',
    'association_conflict_resolution','association_review','internal_pair_link',
    'composition','composition_revision','composition_node','association_realization',
    'realization_incidence','composition_coherence_review','composition_review_realization',
    'navigation_state','navigation_node','navigation_path_step','exploration_workflow',
    'interaction_transition','workflow_state','workflow_association_revision',
    'workflow_association_realization','workflow_transition',
    'export_manifest','export_projection_preservation','aggregate_seal'
  ]
  LOOP
    EXECUTE pg_catalog.format(
      'CREATE TRIGGER %I_append_only BEFORE UPDATE OR DELETE ON exploration_v3.%I '
      'FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete()', v_table, v_table);
  END LOOP;
END
$append_only_triggers$;

RESET ROLE;
