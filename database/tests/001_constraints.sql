\set ON_ERROR_STOP on
BEGIN;
SET CONSTRAINTS ALL DEFERRED;

CREATE FUNCTION pg_temp.assert_true(p_condition boolean, p_label text)
RETURNS void LANGUAGE plpgsql AS $function$
BEGIN
  IF NOT COALESCE(p_condition, false) THEN
    RAISE EXCEPTION 'ASSERTION_FAILED: %', p_label;
  END IF;
END
$function$;

CREATE FUNCTION pg_temp.expect_error(
  p_sql text, p_expected_states text[], p_label text
)
RETURNS void LANGUAGE plpgsql AS $function$
DECLARE
  v_failed boolean := false;
  v_state text;
BEGIN
  BEGIN
    EXECUTE p_sql;
    SET CONSTRAINTS ALL IMMEDIATE;
  EXCEPTION WHEN OTHERS THEN
    v_failed := true;
    v_state := SQLSTATE;
  END;
  SET CONSTRAINTS ALL DEFERRED;
  IF NOT v_failed THEN
    RAISE EXCEPTION 'EXPECTED_ERROR_NOT_RAISED: %', p_label;
  END IF;
  IF NOT (v_state = ANY (p_expected_states)) THEN
    RAISE EXCEPTION 'WRONG_SQLSTATE: % got %, expected %',
      p_label, v_state, p_expected_states;
  END IF;
END
$function$;

CREATE FUNCTION pg_temp.expect_error_message(
  p_sql text, p_expected_state text, p_expected_message text, p_label text
)
RETURNS void LANGUAGE plpgsql AS $function$
DECLARE
  v_failed boolean := false;
  v_state text;
  v_message text;
BEGIN
  BEGIN
    EXECUTE p_sql;
    SET CONSTRAINTS ALL IMMEDIATE;
  EXCEPTION WHEN OTHERS THEN
    v_failed := true;
    v_state := SQLSTATE;
    v_message := SQLERRM;
  END;
  SET CONSTRAINTS ALL DEFERRED;
  IF NOT v_failed THEN
    RAISE EXCEPTION 'EXPECTED_ERROR_NOT_RAISED: %', p_label;
  END IF;
  IF v_state IS DISTINCT FROM p_expected_state
    OR v_message IS DISTINCT FROM p_expected_message THEN
    RAISE EXCEPTION
      'WRONG_SEMANTIC_ERROR: % got [%] %, expected [%] %',
      p_label, v_state, v_message, p_expected_state, p_expected_message;
  END IF;
END
$function$;

\ir ../fixtures/phase2a_base.sql

SELECT pg_temp.expect_error(
  $$INSERT INTO provenance.object_source_record
      VALUES ('20000000-0000-4000-8000-000000000001',
              'ffffffff-ffff-4fff-8fff-fffffffffff1', 'primary')$$,
  ARRAY['23503'], 'orphan object-source bridge denied');

SELECT pg_temp.expect_error(
  $$INSERT INTO provenance.assertion_evidence
      VALUES ('30000000-0000-4000-8000-000000000005',
              'ffffffff-ffff-4fff-8fff-fffffffffff2', 'supports')$$,
  ARRAY['23503'], 'orphan evidence bridge denied');

SELECT pg_temp.expect_error(
  $$INSERT INTO research.relation_claim
      VALUES ('40000000-0000-4000-8000-000000000009',
              'ffffffff-ffff-4fff-8fff-fffffffffff3',
              'ffffffff-ffff-4fff-8fff-fffffffffff4', 'supports')$$,
  ARRAY['23503'], 'orphan claim bridge denied');

SELECT pg_temp.expect_error(
  $$INSERT INTO research.semantic_relation (
      semantic_relation_id, subject_endpoint_id, relation_type_id,
      object_endpoint_id, origin, status, created_at
    ) VALUES (
      'ffffffff-ffff-4fff-8fff-fffffffffff4',
      'ffffffff-ffff-4fff-8fff-fffffffffff5',
      '40000000-0000-4000-8000-000000000006',
      '40000000-0000-4000-8000-000000000008',
      'curator_created', 'proposed', clock_timestamp())$$,
  ARRAY['23503'], 'orphan relation endpoint denied');

SELECT pg_temp.expect_error(
  $$INSERT INTO core.agent VALUES (
      '20000000-0000-4000-8000-000000000001', 'wrong subtype')$$,
  ARRAY['23514'], 'closed entity subtype exactness');

SELECT pg_temp.expect_error(
  $$INSERT INTO raw.source_record (
      source_record_id, source_asset_id, record_ordinal,
      legacy_source_record_id, raw_value, raw_fingerprint,
      parsed_projection, parse_error_code
    ) VALUES (
      'ffffffff-ffff-4fff-8fff-fffffffffff6',
      '10000000-0000-4000-8000-000000000001', 0,
      'duplicate-occurrence', convert_to('duplicate', 'UTF8'),
      encode(sha256(convert_to('duplicate', 'UTF8')), 'hex'), NULL, NULL)$$,
  ARRAY['23505'], 'duplicate source occurrence denied');

SELECT pg_temp.expect_error(
  $$DELETE FROM raw.source_asset
      WHERE source_asset_id = '10000000-0000-4000-8000-000000000001'$$,
  ARRAY['23503','55000'], 'canonical parent delete restricted');

SELECT pg_temp.expect_error(
  $$INSERT INTO research.semantic_relation (
      semantic_relation_id, subject_endpoint_id, relation_type_id,
      object_endpoint_id, origin, status, created_at
    ) VALUES (
      'ffffffff-ffff-4fff-8fff-fffffffffff7',
      '40000000-0000-4000-8000-000000000007',
      'ffffffff-ffff-4fff-8fff-fffffffffff8',
      '40000000-0000-4000-8000-000000000008',
      'curator_created', 'accepted', clock_timestamp())$$,
  ARRAY['23503'], 'unknown relation type accepted denied');

INSERT INTO research.relation_type VALUES (
  '60000000-0000-4000-8000-000000000001',
  'fixture_inactive_relation', false, 'archive_object', 'archive_object',
  true, 'fixture-evidence-v1', false, false, 'Inactive negative fixture',
  'phase2a-fixture-v1');

SELECT pg_temp.expect_error(
  $$INSERT INTO research.semantic_relation (
      semantic_relation_id, subject_endpoint_id, relation_type_id,
      object_endpoint_id, origin, status, created_at
    ) VALUES (
      '60000000-0000-4000-8000-000000000002',
      '40000000-0000-4000-8000-000000000007',
      '60000000-0000-4000-8000-000000000001',
      '40000000-0000-4000-8000-000000000008',
      'curator_created', 'accepted', clock_timestamp())$$,
  ARRAY['23514'], 'inactive relation type accepted denied');

INSERT INTO research.relation_type VALUES (
  '60000000-0000-4000-8000-000000000003',
  'fixture_evidence_required_relation', true,
  'archive_object', 'archive_object', true, 'fixture-evidence-v1',
  false, false, 'No-evidence negative fixture', 'phase2a-fixture-v1');

SELECT pg_temp.expect_error(
  $$INSERT INTO research.semantic_relation (
      semantic_relation_id, subject_endpoint_id, relation_type_id,
      object_endpoint_id, origin, status, created_at
    ) VALUES (
      '60000000-0000-4000-8000-000000000004',
      '40000000-0000-4000-8000-000000000007',
      '60000000-0000-4000-8000-000000000003',
      '40000000-0000-4000-8000-000000000008',
      'curator_created', 'accepted', clock_timestamp())$$,
  ARRAY['23514'], 'accepted relation without evidence denied');

SELECT pg_temp.expect_error(
  $$UPDATE research.semantic_relation
      SET origin = 'legacy_projection_only'
      WHERE semantic_relation_id = '40000000-0000-4000-8000-000000000009'$$,
  ARRAY['23514'], 'legacy projection cannot become accepted relation');

SELECT pg_temp.expect_error(
  $$UPDATE provenance.assertion_evidence
      SET assertion_id = 'ffffffff-ffff-4fff-8fff-ffffffffffa1'
      WHERE assertion_id = '30000000-0000-4000-8000-000000000005'$$,
  ARRAY['55000'], 'accepted assertion evidence reparent denied');

SELECT pg_temp.expect_error(
  $$UPDATE provenance.assignment_assertion
      SET canonical_assignment_id = 'ffffffff-ffff-4fff-8fff-ffffffffffa2'
      WHERE canonical_assignment_id = '30000000-0000-4000-8000-000000000006'$$,
  ARRAY['55000'], 'accepted assignment support reparent denied');

SELECT pg_temp.expect_error(
  $$UPDATE research.claim_evidence
      SET claim_revision_id = 'ffffffff-ffff-4fff-8fff-ffffffffffa3'
      WHERE claim_revision_id = '40000000-0000-4000-8000-000000000005'$$,
  ARRAY['55000'], 'accepted claim evidence reparent denied');

SELECT pg_temp.expect_error(
  $$UPDATE research.relation_claim
      SET semantic_relation_id = 'ffffffff-ffff-4fff-8fff-ffffffffffa4'
      WHERE semantic_relation_id = '40000000-0000-4000-8000-000000000009'$$,
  ARRAY['55000'], 'accepted relation claim reparent denied');

SELECT pg_temp.expect_error(
  $$INSERT INTO provenance.assertion_review_decision VALUES (
      'ffffffff-ffff-4fff-8fff-ffffffffffa5',
      '30000000-0000-4000-8000-000000000005', 'hold',
      'second-root-reviewer', 'Competing current root', NULL,
      clock_timestamp())$$,
  ARRAY['23514'], 'competing current assertion decision denied');

SELECT pg_temp.expect_error(
  $$INSERT INTO provenance.assignment_review_decision VALUES (
      'ffffffff-ffff-4fff-8fff-ffffffffffa6',
      '30000000-0000-4000-8000-000000000006', 'hold',
      'second-root-reviewer', 'Competing current root', NULL,
      clock_timestamp())$$,
  ARRAY['23514'], 'competing current assignment decision denied');

-- These truth-table tests append fresh immutable observations/decisions and
-- attempt a new REMOTE_IMAGE assessment. They deliberately do not UPDATE an
-- append-only source row: the asserted error must come from the fail-closed
-- delivery validator, not from the generic mutation guard.
SELECT pg_temp.expect_error_message(
  $$INSERT INTO rights.rights_observation (
      rights_observation_id, subject_kind, evidence_state, evidence_item_id,
      observed_wording, observed_at, supersedes_rights_observation_id
    ) VALUES (
      '61000000-0000-4000-8000-000000000001',
      'external_visual_reference', 'unknown', NULL,
      'Fresh unknown-rights observation', clock_timestamp() - interval '3 minutes',
      '50000000-0000-4000-8000-000000000007');
    INSERT INTO rights.rights_observation_visual_reference VALUES (
      '61000000-0000-4000-8000-000000000001',
      '50000000-0000-4000-8000-000000000004');
    INSERT INTO rights.rights_assessment (
      rights_assessment_id, subject_kind, assessed_state, reviewer_actor,
      rationale, assessed_at, supersedes_rights_assessment_id
    ) VALUES (
      '61000000-0000-4000-8000-000000000002',
      'external_visual_reference', 'unknown', 'adversarial-reviewer',
      'Unknown rights must cap delivery', clock_timestamp() - interval '2 minutes',
      '50000000-0000-4000-8000-000000000008');
    INSERT INTO rights.rights_assessment_visual_reference VALUES (
      '61000000-0000-4000-8000-000000000002',
      '50000000-0000-4000-8000-000000000004');
    INSERT INTO rights.rights_assessment_observation VALUES (
      '61000000-0000-4000-8000-000000000002',
      '61000000-0000-4000-8000-000000000001', 'supports');
    INSERT INTO rights.delivery_assessment (
      delivery_assessment_id, object_visual_reference_id,
      attribution_bundle_id, delivery_mode, reason_code, assessor_actor,
      assessed_at, supersedes_delivery_assessment_id, machine_reason_code
    ) VALUES (
      '61000000-0000-4000-8000-000000000003',
      '50000000-0000-4000-8000-000000000014',
      '50000000-0000-4000-8000-000000000015',
      'remote_image', 'RD-080', 'adversarial-reviewer',
      clock_timestamp() - interval '1 minute',
      '50000000-0000-4000-8000-000000000010',
      'REMOTE_IMAGE_ALL_GATES_PASS');
    INSERT INTO rights.delivery_rights_assessment VALUES (
      '61000000-0000-4000-8000-000000000003',
      '61000000-0000-4000-8000-000000000002', 'supports');
    INSERT INTO rights.delivery_policy_evaluation VALUES (
      '61000000-0000-4000-8000-000000000003',
      '50000000-0000-4000-8000-000000000009');
    INSERT INTO rights.delivery_locator_qualification VALUES
      ('61000000-0000-4000-8000-000000000003',
       '50000000-0000-4000-8000-000000000005',
       '50000000-0000-4000-8000-000000000011', 'canonical_record'),
      ('61000000-0000-4000-8000-000000000003',
       '50000000-0000-4000-8000-000000000006',
       '50000000-0000-4000-8000-000000000012', 'direct_image')$$,
  '23514', 'DELIVERY_ASSESSMENT_EXCEEDS_FAIL_CLOSED_CAP',
  'unknown rights plus healthy endpoint cannot remote');

SELECT pg_temp.expect_error_message(
  $$INSERT INTO rights.provider_policy_version (
      provider_policy_version_id, provider_id, version_token, policy_sha256,
      policy_state, effective_from, effective_until, review_due,
      source_evidence_item_id, policy_scope_id
    ) VALUES (
      '61000000-0000-4000-8000-000000000011',
      '50000000-0000-4000-8000-000000000001',
      'fixture-policy-viewer-v2', repeat('b', 64), 'source_viewer_only',
      clock_timestamp() - interval '1 hour',
      clock_timestamp() + interval '7 days',
      clock_timestamp() + interval '5 days',
      '30000000-0000-4000-8000-000000000003',
      '50000000-0000-4000-8000-000000000016');
    INSERT INTO rights.provider_policy_evaluation (
      provider_policy_evaluation_id, object_visual_reference_id,
      evaluated_state, evaluator_actor, evaluated_at,
      supersedes_provider_policy_evaluation_id
    ) VALUES (
      '61000000-0000-4000-8000-000000000012',
      '50000000-0000-4000-8000-000000000014',
      'source_viewer_only', 'adversarial-reviewer',
      clock_timestamp() - interval '2 minutes',
      '50000000-0000-4000-8000-000000000009');
    INSERT INTO rights.provider_policy_evaluation_version VALUES
      ('61000000-0000-4000-8000-000000000012',
       '50000000-0000-4000-8000-000000000003'),
      ('61000000-0000-4000-8000-000000000012',
       '61000000-0000-4000-8000-000000000011');
    INSERT INTO rights.delivery_assessment (
      delivery_assessment_id, object_visual_reference_id,
      attribution_bundle_id, delivery_mode, reason_code, assessor_actor,
      assessed_at, supersedes_delivery_assessment_id, machine_reason_code
    ) VALUES (
      '61000000-0000-4000-8000-000000000013',
      '50000000-0000-4000-8000-000000000014',
      '50000000-0000-4000-8000-000000000015',
      'remote_image', 'RD-080', 'adversarial-reviewer',
      clock_timestamp() - interval '1 minute',
      '50000000-0000-4000-8000-000000000010',
      'REMOTE_IMAGE_ALL_GATES_PASS');
    INSERT INTO rights.delivery_rights_assessment VALUES (
      '61000000-0000-4000-8000-000000000013',
      '50000000-0000-4000-8000-000000000008', 'supports');
    INSERT INTO rights.delivery_policy_evaluation VALUES (
      '61000000-0000-4000-8000-000000000013',
      '61000000-0000-4000-8000-000000000012');
    INSERT INTO rights.delivery_locator_qualification VALUES
      ('61000000-0000-4000-8000-000000000013',
       '50000000-0000-4000-8000-000000000005',
       '50000000-0000-4000-8000-000000000011', 'canonical_record'),
      ('61000000-0000-4000-8000-000000000013',
       '50000000-0000-4000-8000-000000000006',
       '50000000-0000-4000-8000-000000000012', 'direct_image')$$,
  '23514', 'DELIVERY_ASSESSMENT_EXCEEDS_FAIL_CLOSED_CAP',
  'permitted rights plus provider viewer-only policy cannot remote');

SELECT pg_temp.expect_error_message(
  $$INSERT INTO rights.endpoint_health_observation (
      endpoint_health_observation_id, visual_locator_id, health_state,
      method_version, checked_at, valid_until, request_fingerprint
    ) VALUES (
      '61000000-0000-4000-8000-000000000021',
      '50000000-0000-4000-8000-000000000006', 'unreachable',
      'phase2a-health-v1', clock_timestamp() - interval '2 minutes',
      clock_timestamp() + interval '1 day', repeat('c', 64));
    INSERT INTO rights.delivery_assessment (
      delivery_assessment_id, object_visual_reference_id,
      attribution_bundle_id, delivery_mode, reason_code, assessor_actor,
      assessed_at, supersedes_delivery_assessment_id, machine_reason_code
    ) VALUES (
      '61000000-0000-4000-8000-000000000022',
      '50000000-0000-4000-8000-000000000014',
      '50000000-0000-4000-8000-000000000015',
      'remote_image', 'RD-080', 'adversarial-reviewer',
      clock_timestamp() - interval '1 minute',
      '50000000-0000-4000-8000-000000000010',
      'REMOTE_IMAGE_ALL_GATES_PASS');
    INSERT INTO rights.delivery_rights_assessment VALUES (
      '61000000-0000-4000-8000-000000000022',
      '50000000-0000-4000-8000-000000000008', 'supports');
    INSERT INTO rights.delivery_policy_evaluation VALUES (
      '61000000-0000-4000-8000-000000000022',
      '50000000-0000-4000-8000-000000000009');
    INSERT INTO rights.delivery_locator_qualification VALUES
      ('61000000-0000-4000-8000-000000000022',
       '50000000-0000-4000-8000-000000000005',
       '50000000-0000-4000-8000-000000000011', 'canonical_record'),
      ('61000000-0000-4000-8000-000000000022',
       '50000000-0000-4000-8000-000000000006',
       '61000000-0000-4000-8000-000000000021', 'direct_image')$$,
  '23514', 'DELIVERY_REQUIRES_MATCHING_HEALTHY_FRESH_TYPED_LOCATOR',
  'permitted rights plus dead endpoint cannot remote');

SELECT pg_temp.expect_error(
  $$UPDATE rights.object_visual_reference
      SET evidence_item_id = NULL
      WHERE object_visual_reference_id =
        '50000000-0000-4000-8000-000000000014'$$,
  ARRAY['23514'],
  'accepted object-visual bridge cannot lose evidence-bound decision support');

SELECT pg_temp.expect_error(
  $$INSERT INTO rights.object_visual_reference_review_decision (
      object_visual_reference_review_decision_id,
      object_visual_reference_id, outcome, evidence_item_id,
      reviewer_actor, rationale, supersedes_decision_id, decided_at
    ) VALUES (
      '60000000-0000-4000-8000-000000000007',
      '50000000-0000-4000-8000-000000000014', 'accept',
      '30000000-0000-4000-8000-000000000003',
      'competing-reviewer', 'Competing current root', NULL,
      clock_timestamp())$$,
  ARRAY['23514'], 'competing current visual bridge decision denied');

SET SESSION AUTHORIZATION gda_v49_phase2a_reviewer;
SELECT pg_temp.expect_error(
  $$SELECT rights.record_object_visual_reference_review_decision(
      '60000000-0000-4000-8000-000000000008',
      '50000000-0000-4000-8000-000000000014', 'accept',
      '30000000-0000-4000-8000-000000000003',
      'Future-dated review must not take effect',
      '50000000-0000-4000-8000-000000000017',
      clock_timestamp() + interval '1 day')$$,
  ARRAY['23514'], 'future visual bridge review decision denied');
RESET SESSION AUTHORIZATION;

SELECT pg_temp.expect_error(
  $$INSERT INTO rights.endpoint_health_observation VALUES (
      '60000000-0000-4000-8000-000000000005',
      '50000000-0000-4000-8000-000000000006', 'healthy_fresh',
      'phase2a-health-v1',
      clock_timestamp(), clock_timestamp() + interval '32 days',
      repeat('b', 64))$$,
  ARRAY['23514'], 'unbounded positive health interval denied');

SELECT pg_temp.expect_error(
  $$INSERT INTO rights.endpoint_health_observation
      SELECT '60000000-0000-4000-8000-000000000006',
        visual_locator_id, health_state, method_version, checked_at,
        valid_until, request_fingerprint
      FROM rights.endpoint_health_observation
      WHERE endpoint_health_observation_id =
        '50000000-0000-4000-8000-000000000012'$$,
  ARRAY['23505'], 'duplicate health natural identity denied');

-- The immutable relation-to-claim bridge is revision-pinned. A newer accepted
-- revision can replace a superseded revision without rewriting history.
INSERT INTO research.claim_revision (
  claim_revision_id, claim_id, revision_number, epistemic_class_id,
  status, workflow_state, claimant_agent_id, wording,
  temporal_qualifier_id, spatial_qualifier_id, analysis_run_id,
  supersedes_claim_revision_id, created_at,
  claim_date_or_version, claim_stance
) VALUES (
  '60000000-0000-4000-8000-000000000010',
  '40000000-0000-4000-8000-000000000004', 2,
  '40000000-0000-4000-8000-000000000003',
  'accepted', 'resolved',
  '20000000-0000-4000-8000-000000000003',
  'Fixture claim wording revision two', NULL, NULL, NULL,
  '40000000-0000-4000-8000-000000000005', clock_timestamp(),
  'fixture-claim-v2', 'supports'
);
INSERT INTO research.claim_evidence VALUES (
  '60000000-0000-4000-8000-000000000010',
  '30000000-0000-4000-8000-000000000003', 'supports');
INSERT INTO research.claim_review_decision VALUES (
  '60000000-0000-4000-8000-000000000011',
  '60000000-0000-4000-8000-000000000010', 'accept', false,
  'fixture-reviewer', 'Accepted successor claim revision', NULL,
  clock_timestamp());
INSERT INTO research.claim_decision_evidence VALUES (
  '60000000-0000-4000-8000-000000000011',
  '30000000-0000-4000-8000-000000000003', 'supports');
UPDATE research.claim_revision
SET status = 'superseded', workflow_state = 'superseded'
WHERE claim_revision_id = '40000000-0000-4000-8000-000000000005';
INSERT INTO research.relation_claim VALUES (
  '40000000-0000-4000-8000-000000000009',
  '40000000-0000-4000-8000-000000000004',
  '60000000-0000-4000-8000-000000000010', 'supports');
SET CONSTRAINTS ALL IMMEDIATE;
SET CONSTRAINTS ALL DEFERRED;
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM research.relation_claim
    WHERE semantic_relation_id =
      '40000000-0000-4000-8000-000000000009'
      AND claim_id = '40000000-0000-4000-8000-000000000004') = 2
  AND (SELECT status FROM research.semantic_relation
    WHERE semantic_relation_id =
      '40000000-0000-4000-8000-000000000009') = 'accepted',
  'relation support can append a successor claim revision without rewriting v1');

-- Split identity copies must be all-or-nothing against the exact release
-- object set, and a hand-crafted incomplete copy must fail the validator.
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_research_release(
  '60000000-0000-4000-8000-000000000020',
  'split-copy-negative-v1', 'schema-v49.0', 'model-v49.0',
  '60000000-0000-4000-8000-000000000021', repeat('1',64));
SELECT release.copy_research_corpus_snapshot_to_draft(
  '60000000-0000-4000-8000-000000000020',
  '40000000-0000-4000-8000-000000000002',
  '40000000-0000-4000-8000-000000000021',
  '40000000-0000-4000-8000-000000000022', repeat('6',64));
SELECT release.add_research_object_to_draft(
  '60000000-0000-4000-8000-000000000020',
  '40000000-0000-4000-8000-000000000002',
  '20000000-0000-4000-8000-000000000001');
RESET SESSION AUTHORIZATION;
INSERT INTO core.legacy_identity VALUES (
  '60000000-0000-4000-8000-000000000022', 'archive_object',
  'phase2a-split-fixture', 'legacy-split-1', clock_timestamp());
INSERT INTO core.legacy_identity_resolution (
  legacy_identity_resolution_id, legacy_identity_id, resolution_state,
  target_archive_object_id, target_source_record_id, target_trace_node_id,
  target_trace_edge_release_id, target_trace_edge_corpus_version_id,
  target_trace_edge_subject_node_id, target_trace_edge_relation_id,
  target_trace_edge_object_node_id, target_trace_edge_projection_role,
  target_folder_id, decision_evidence_item_id, effective_release_id,
  supersedes_resolution_id, effective_from, reason_code
) VALUES (
  '60000000-0000-4000-8000-000000000023',
  '60000000-0000-4000-8000-000000000022', 'split',
  NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,
  '30000000-0000-4000-8000-000000000003',
  '60000000-0000-4000-8000-000000000020', NULL,
  clock_timestamp(), 'EXPLICIT_SPLIT_FIXTURE');
INSERT INTO core.legacy_identity_split_successor VALUES
  ('60000000-0000-4000-8000-000000000023',
   '20000000-0000-4000-8000-000000000001',0),
  ('60000000-0000-4000-8000-000000000023',
   '20000000-0000-4000-8000-000000000002',1);
SET CONSTRAINTS ALL IMMEDIATE;
SET CONSTRAINTS ALL DEFERRED;
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT pg_temp.expect_error(
  $$SELECT release.copy_legacy_identity_resolution_to_draft(
      '60000000-0000-4000-8000-000000000020',
      '60000000-0000-4000-8000-000000000023', NULL)$$,
  ARRAY['23514'],
  'split builder rejects successor absent from release object set');
RESET SESSION AUTHORIZATION;
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
SELECT '60000000-0000-4000-8000-000000000020'::uuid,
  i.legacy_identity_id, r.legacy_identity_resolution_id,
  i.identity_kind, i.namespace, i.legacy_id, r.resolution_state,
  r.target_archive_object_id, r.target_source_record_id,
  r.target_trace_node_id, r.target_folder_id,
  r.target_trace_edge_corpus_version_id,
  r.target_trace_edge_subject_node_id, r.target_trace_edge_relation_id,
  r.target_trace_edge_object_node_id, r.target_trace_edge_projection_role,
  r.reason_code, r.effective_from, NULL::uuid
FROM core.legacy_identity_resolution r
JOIN core.legacy_identity i ON i.legacy_identity_id = r.legacy_identity_id
WHERE r.legacy_identity_resolution_id =
  '60000000-0000-4000-8000-000000000023';
INSERT INTO release.research_legacy_identity_split_successor VALUES (
  '60000000-0000-4000-8000-000000000020',
  '60000000-0000-4000-8000-000000000023', 1,
  '20000000-0000-4000-8000-000000000001',
  'urn:gdarchive:object:20000000-0000-4000-8000-000000000001');
SELECT pg_temp.expect_error(
  $$SELECT release.assert_legacy_resolution_projection_complete(
      '60000000-0000-4000-8000-000000000020')$$,
  ARRAY['23514'], 'incomplete copied split successor set denied');

SELECT pg_temp.assert_true(
  NOT EXISTS (
    SELECT 1 FROM research.relation_type
    WHERE implicit_transitivity OR automatic_influence_inference
  ), 'automatic influence/transitivity remains disabled');

SELECT pg_temp.assert_true(
  NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = ANY (ARRAY[
      'raw','core','provenance','research','rights',
      'workflow','release','audit','api_v1'
    ]) AND column_name IN ('target_type','target_id')
  ), 'no arbitrary string polymorphic target columns');

SELECT pg_temp.assert_true(
  EXISTS (
    SELECT 1 FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = 'core' AND t.relname = 'legacy_identity_resolution'
      AND c.contype = 'f'
      AND pg_get_constraintdef(c.oid) LIKE
        '%REFERENCES release.trace_projection_edge%'
  ), 'legacy TRACE-edge identity has release-pinned composite FK');

SELECT pg_temp.assert_true(
  EXISTS (
    SELECT 1 FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = 'rights'
      AND t.relname = 'endpoint_health_observation'
      AND c.contype = 'u'
      AND pg_get_constraintdef(c.oid) LIKE
        '%visual_locator_id, checked_at, method_version, request_fingerprint%'
  ), 'health observation natural identity includes method version');

SELECT pg_temp.assert_true(
  release.jcs_text(
    '{"z":null,"a":[true,false,"x",1.0]}'::jsonb
  ) = '{"a":[true,false,"x",1],"z":null}',
  'restricted RFC 8785 encoder sorts keys and canonicalizes safe integers');
SELECT pg_temp.expect_error(
  $$SELECT release.jcs_text('1.25'::jsonb)$$,
  ARRAY['22023'], 'manifest JCS domain rejects non-integer numbers');
SELECT pg_temp.assert_true(
  release.canonical_decimal_text(0.7500::numeric) = '0.75'
  AND release.canonical_decimal_text((-0.000)::numeric) = '0'
  AND release.canonical_decimal_text(1000.000::numeric) = '1000',
  'analysis decimals use finite normalized plain-notation strings');
SELECT pg_temp.assert_true(
  release.analysis_run_manifest_json(
    '{"score_value":0.7500,"uncertainty_lower":0.10,"uncertainty_upper":null,"threshold_value":0.500}'::jsonb
  ) = '{"score_value":"0.75","uncertainty_lower":"0.1","uncertainty_upper":null,"threshold_value":"0.5"}'::jsonb,
  'analysis manifest projection converts every numeric measurement to a canonical string');

SELECT pg_temp.assert_true(
  (SELECT count(*) FROM raw.legacy_surface_ledger
    WHERE import_disposition = 'held') = 1,
  'held source row preserved');
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM core.archive_object) = 2,
  'held operational object preserved');

SET CONSTRAINTS ALL IMMEDIATE;
ROLLBACK;
