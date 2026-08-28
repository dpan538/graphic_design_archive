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

-- Cross-language vectors are copied from the frozen Checkpoint 008 v3
-- semantic fixture.  They prove that the final v49 JCS function, not the
-- earlier jsonb::text implementation, is the identity byte contract.
SELECT pg_temp.assert_true(
  release.canonical_jsonb_sha256($identity$
    {"association_kind":"PAIR","order_semantics":"UNORDERED","participants":[{"concept_id":"concept:invalid-full-clique:1","ordinal":null,"role_id":null,"sense_id":"sense:invalid-full-clique:1"},{"concept_id":"concept:invalid-full-clique:4","ordinal":null,"role_id":null,"sense_id":"sense:invalid-full-clique:4"}],"roles_meaningful":false,"scope_identity":{"actors":["SYNTHETIC-ACTOR"],"geographies":["SYNTHETIC-GEOGRAPHY"],"historical_case_ids":["case:invalid-full-clique"],"institutions":["SYNTHETIC-INSTITUTION"],"mechanisms":["SYNTHETIC-MECHANISM"],"scope_id":"scope:invalid-full-clique","time_bounds":{"end":"SYNTHETIC","start":"SYNTHETIC"}}}
  $identity$::jsonb) =
    'f7ce2e398d04ce4ae22922164170b93e12f914cea9e8662d958742b269bb11b8',
  'CP8 pair identity JCS vector and association:v3:f7ce2e398d04ce4ae2292216 prefix');

-- A complete synthetic sparse hyperedge is active without manufacturing any
-- internal pair association.  Synthetic controls never enter api_v3.
INSERT INTO exploration_v3.governed_authority VALUES (
  'authority:synthetic-db-v3','SYNTHETIC_TEST_AUTHORITY','FINAL','1',
  encode(sha256(convert_to('authority:synthetic-db-v3','UTF8')),'hex'),
  '2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.governed_scope VALUES (
  'scope:synthetic-sparse-three','SYNTHETIC_CONTROL',ARRAY['case:synthetic-sparse-three'],
  'SYNTHETIC','SYNTHETIC',ARRAY['SYNTHETIC-GEOGRAPHY'],
  ARRAY['SYNTHETIC-INSTITUTION'],ARRAY['SYNTHETIC-ACTOR'],
  ARRAY['SYNTHETIC-MECHANISM'],ARRAY['Not historical evidence.'],
  encode(sha256(convert_to('scope:synthetic-sparse-three','UTF8')),'hex'));
INSERT INTO exploration_v3.governed_scope VALUES (
  'scope:sparse-valid-five','SYNTHETIC_CONTROL',ARRAY['case:sparse-valid-five'],
  'SYNTHETIC','SYNTHETIC',ARRAY['SYNTHETIC-GEOGRAPHY'],
  ARRAY['SYNTHETIC-INSTITUTION'],ARRAY['SYNTHETIC-ACTOR'],
  ARRAY['SYNTHETIC-MECHANISM'],ARRAY['CP8 identity vector scope.'],
  encode(sha256(convert_to('scope:sparse-valid-five','UTF8')),'hex'));

SELECT pg_temp.assert_true(
  exploration_v3.association_identity_sha(
    'HIGHER_ORDER','UNORDERED',false,'scope:sparse-valid-five',
    ARRAY['concept:test:u:3','concept:test:u:1','concept:test:u:2'],
    ARRAY['sense:test:u:3','sense:test:u:1','sense:test:u:2'],
    ARRAY[NULL,NULL,NULL]::integer[],ARRAY[NULL,NULL,NULL]::text[])
    = 'da738afb1452d7b505c4c8c053dd65aa710e1b214495f817d074ca9f5cd42199',
  'CP8 unordered permutation-invariant identity vector');
SELECT pg_temp.assert_true(
  exploration_v3.association_identity_sha(
    'HIGHER_ORDER','ORDERED',false,'scope:sparse-valid-five',
    ARRAY['concept:test:o:1','concept:test:o:2','concept:test:o:3'],
    ARRAY['sense:test:o:1','sense:test:o:2','sense:test:o:3'],
    ARRAY[0,1,2],ARRAY[NULL,NULL,NULL]::text[])
    = '55f42f7802906116780ab20fbca07a9faa03fb459695744a8a6f28f64de27107'
  AND exploration_v3.association_identity_sha(
    'HIGHER_ORDER','ORDERED',false,'scope:sparse-valid-five',
    ARRAY['concept:test:o:3','concept:test:o:2','concept:test:o:1'],
    ARRAY['sense:test:o:3','sense:test:o:2','sense:test:o:1'],
    ARRAY[0,1,2],ARRAY[NULL,NULL,NULL]::text[])
    = '2398c4b25eb6ed24e827cb2843b176cf2e6c02a5efe5751d140ba824b31b6584',
  'CP8 ordered contiguous-ordinal sensitive identity vectors');
SELECT pg_temp.assert_true(
  exploration_v3.association_identity_sha(
    'HIGHER_ORDER','UNORDERED',true,'scope:sparse-valid-five',
    ARRAY['concept:test:r:3','concept:test:r:1','concept:test:r:2'],
    ARRAY['sense:test:r:3','sense:test:r:1','sense:test:r:2'],
    ARRAY[NULL,NULL,NULL]::integer[],
    ARRAY['role:gamma','role:alpha','role:beta'])
    = 'c4e0479dec6ff5616bde4c5013abdb57482850600058611e81a4c143b4ebb26b'
  AND exploration_v3.association_identity_sha(
    'HIGHER_ORDER','UNORDERED',true,'scope:sparse-valid-five',
    ARRAY['concept:test:r:1','concept:test:r:2','concept:test:r:3'],
    ARRAY['sense:test:r:1','sense:test:r:2','sense:test:r:3'],
    ARRAY[NULL,NULL,NULL]::integer[],
    ARRAY['role:beta','role:alpha','role:gamma'])
    = '14bf6810350cf10b20c16368cc075b1464558327d5cfbeb4999e46eea2e79133',
  'CP8 meaningful-role permutation and reassignment identity vectors');
INSERT INTO exploration_v3.concept
SELECT 'concept:synthetic:'||n,'SYNTHETIC_CONTROL',
  'Synthetic concept '||n,'ACTIVE',true,'authority:synthetic-db-v3','1',
  encode(sha256(convert_to('concept:synthetic:'||n,'UTF8')),'hex'),
  false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic controls are never product eligible.'
FROM generate_series(1,3) n;
INSERT INTO exploration_v3.concept_sense
SELECT 'sense:synthetic:'||n,'concept:synthetic:'||n,'SYNTHETIC_CONTROL',
  'Synthetic bounded sense '||n,'ACTIVE',true,'authority:synthetic-db-v3','1',
  encode(sha256(convert_to('sense:synthetic:'||n,'UTF8')),'hex'),
  ARRAY['crosswalk:synthetic:'||n],false,'NOT_APPLICABLE_SYNTHETIC',NULL,
  'Synthetic controls are never product eligible.'
FROM generate_series(1,3) n;
INSERT INTO exploration_v3.concept_sense_scope
SELECT 'sense:synthetic:'||n,'scope:synthetic-sparse-three'
FROM generate_series(1,3) n;
INSERT INTO exploration_v3.aggregate_seal
SELECT 'CONCEPT_SENSE', sense_id,
  exploration_v3.aggregate_content_sha('CONCEPT_SENSE', sense_id),
  '2026-08-28T00:00:00Z'
FROM exploration_v3.concept_sense WHERE sense_id LIKE 'sense:synthetic:%';
INSERT INTO exploration_v3.evidence_reference VALUES (
  'evidence:synthetic:group','SYNTHETIC_CONTROL',NULL,NULL,NULL,
  encode(sha256(convert_to('evidence:synthetic:group','UTF8')),'hex'),
  'Synthetic direct group control.',false,true,'SYNTHETIC_ONLY');
INSERT INTO exploration_v3.evidence_locator VALUES (
  'locator:synthetic:group','evidence:synthetic:group','synthetic://group-control',
  encode(sha256(convert_to('synthetic://group-control','UTF8')),'hex'),'SYNTHETIC_ONLY');
INSERT INTO exploration_v3.aggregate_seal VALUES (
  'EVIDENCE_REFERENCE','evidence:synthetic:group',
  exploration_v3.aggregate_content_sha(
    'EVIDENCE_REFERENCE','evidence:synthetic:group'),
  '2026-08-28T00:00:00Z');
SELECT pg_temp.assert_true(
  exploration_v3.aggregate_content_sha(
    'EVIDENCE_REFERENCE','evidence:synthetic:group') =
    'a2fba8b8387c7b8291d2106fc20483c5fabb0108d943f2e06d1e14f71dbf0af4',
  'independently reconstructed canonical aggregate-content digest vector');

DO $aggregate_hash_timezone_and_order$
DECLARE v_utc core.sha256_hex;
DECLARE v_other_zone core.sha256_hex;
DECLARE v_reverse_order core.sha256_hex;
DECLARE v_forward_order core.sha256_hex;
DECLARE v_message text;
BEGIN
  v_utc := exploration_v3.aggregate_content_sha(
    'EVIDENCE_REFERENCE','evidence:synthetic:group');
  PERFORM set_config('TimeZone','Pacific/Auckland',true);
  v_other_zone := exploration_v3.aggregate_content_sha(
    'EVIDENCE_REFERENCE','evidence:synthetic:group');
  IF v_utc <> v_other_zone THEN
    RAISE EXCEPTION 'AGGREGATE_HASH_TIMEZONE_VARIANCE';
  END IF;

  BEGIN
    INSERT INTO exploration_v3.evidence_reference VALUES (
      'evidence:synthetic:order-control','SYNTHETIC_CONTROL',NULL,NULL,NULL,
      repeat('4',64),'Child insertion order control.',false,true,'SYNTHETIC_ONLY');
    INSERT INTO exploration_v3.evidence_locator VALUES
      ('locator:synthetic:order:b','evidence:synthetic:order-control','synthetic://b',
        repeat('5',64),'SYNTHETIC_ONLY'),
      ('locator:synthetic:order:a','evidence:synthetic:order-control','synthetic://a',
        repeat('6',64),'SYNTHETIC_ONLY');
    v_reverse_order := exploration_v3.aggregate_content_sha(
      'EVIDENCE_REFERENCE','evidence:synthetic:order-control');
    RAISE EXCEPTION 'REVERSE_ORDER_CAPTURED';
  EXCEPTION WHEN raise_exception THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'REVERSE_ORDER_CAPTURED' THEN RAISE; END IF;
  END;
  BEGIN
    INSERT INTO exploration_v3.evidence_reference VALUES (
      'evidence:synthetic:order-control','SYNTHETIC_CONTROL',NULL,NULL,NULL,
      repeat('4',64),'Child insertion order control.',false,true,'SYNTHETIC_ONLY');
    INSERT INTO exploration_v3.evidence_locator VALUES
      ('locator:synthetic:order:a','evidence:synthetic:order-control','synthetic://a',
        repeat('6',64),'SYNTHETIC_ONLY'),
      ('locator:synthetic:order:b','evidence:synthetic:order-control','synthetic://b',
        repeat('5',64),'SYNTHETIC_ONLY');
    v_forward_order := exploration_v3.aggregate_content_sha(
      'EVIDENCE_REFERENCE','evidence:synthetic:order-control');
    RAISE EXCEPTION 'FORWARD_ORDER_CAPTURED';
  EXCEPTION WHEN raise_exception THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'FORWARD_ORDER_CAPTURED' THEN RAISE; END IF;
  END;
  IF v_reverse_order <> v_forward_order THEN
    RAISE EXCEPTION 'AGGREGATE_HASH_CHILD_ORDER_VARIANCE';
  END IF;
  PERFORM set_config('TimeZone','UTC',true);
END
$aggregate_hash_timezone_and_order$;

DO $wrong_aggregate_digest_block$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.evidence_reference VALUES (
      'evidence:synthetic:wrong-seal','SYNTHETIC_CONTROL',NULL,NULL,NULL,
      repeat('7',64),'Wrong seal hash control.',false,true,'SYNTHETIC_ONLY');
    INSERT INTO exploration_v3.evidence_locator VALUES (
      'locator:synthetic:wrong-seal','evidence:synthetic:wrong-seal',
      'synthetic://wrong-seal',repeat('8',64),'SYNTHETIC_ONLY');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'EVIDENCE_REFERENCE','evidence:synthetic:wrong-seal',repeat('0',64),
      '2026-08-28T00:00:00Z');
    RAISE EXCEPTION 'WRONG_AGGREGATE_DIGEST_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'AGGREGATE_SEAL_CONTENT_HASH_MISMATCH' THEN RAISE; END IF;
  END;
END
$wrong_aggregate_digest_block$;
INSERT INTO exploration_v3.association VALUES (
  'association:v3:d9a68bf6518292a0495c3196','SYNTHETIC_CONTROL','HIGHER_ORDER',3,
  'UNORDERED',false,'NONE',
  'd9a68bf6518292a0495c3196320e4bdd4cfa4c167a4a4d934227a19ff196580d',
  '2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.association_revision (
  association_revision_id,association_id,revision_number,scope_id,lifecycle_state,
  support_mode,evidence_complete,same_configuration,conflicts_resolved,
  rights_cleared_for_governed_use,synthesis_complete,uncertainty_status,
  uncertainty_level,uncertainty_activation_policy,uncertainty_rationale,
  activation_decision,all_activation_gates_pass,semantic_version,semantic_sha256,
  presentation_sha256,product_eligible,product_eligibility_disposition,
  product_path,product_ineligibility_reason,qualifications,explicit_non_claims,
  supersedes_association_revision_id,created_at,scope_context_qualifications
) VALUES (
  'association-revision:synthetic:sparse-three:v1',
  'association:v3:d9a68bf6518292a0495c3196',1,
  'scope:synthetic-sparse-three','ACTIVE','DIRECT_GROUP',true,true,true,true,true,
  'RESOLVED_BOUNDED','LOW','ALLOWED_BOUNDED','Fully specified synthetic oracle.',
  'ALLOW',true,'1',
  encode(sha256(convert_to('association-revision:synthetic:sparse-three:v1','UTF8')),'hex'),
  encode(sha256(convert_to('presentation:synthetic:sparse-three:v1','UTF8')),'hex'),
  false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic controls are never product eligible.',
  ARRAY['Synthetic bounded fixture.'],
  ARRAY['Does not assert causation, direction, chronology, hierarchy, influence, or similarity.'],
  NULL,'2026-08-28T00:00:00Z',ARRAY['Not historical evidence.']);
INSERT INTO exploration_v3.association_incidence
SELECT 'incidence:synthetic:'||n,'association-revision:synthetic:sparse-three:v1',
  'concept:synthetic:'||n,'sense:synthetic:'||n,NULL,NULL,
  'scope:synthetic-sparse-three',ARRAY['Exact synthetic bounded sense.']
FROM generate_series(1,3) n;
INSERT INTO exploration_v3.association_revision_evidence VALUES (
  'association-revision:synthetic:sparse-three:v1','evidence:synthetic:group','supports');
INSERT INTO exploration_v3.association_review VALUES (
  'review:synthetic:sparse-three:v1','association-revision:synthetic:sparse-three:v1',
  'FINAL','DIRECT_HIGHER_ORDER_SUPPORT','PASS',true,true,true,0,
  'authority:synthetic-db-v3','1',ARRAY['Synthetic control review.'],
  ARRAY['Does not authorize a production research claim.'],
  encode(sha256(convert_to('review:synthetic:sparse-three:v1','UTF8')),'hex'),
  '2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.aggregate_seal VALUES (
  'ASSOCIATION_REVISION','association-revision:synthetic:sparse-three:v1',
  exploration_v3.aggregate_content_sha(
    'ASSOCIATION_REVISION','association-revision:synthetic:sparse-three:v1'),
  '2026-08-28T00:00:00Z');
SET CONSTRAINTS ALL IMMEDIATE;
SET CONSTRAINTS ALL DEFERRED;

SELECT pg_temp.assert_true(
  (SELECT count(*) FROM exploration_v3.association a
    JOIN exploration_v3.association_revision r USING (association_id)
    WHERE a.association_kind='HIGHER_ORDER' AND r.lifecycle_state='ACTIVE') = 1
  AND (SELECT count(*) FROM exploration_v3.association WHERE association_kind='PAIR') = 0
  AND (SELECT count(*) FROM exploration_v3.internal_pair_link) = 0,
  'active sparse hyperedge exists without implicit pair projection');

INSERT INTO exploration_v3.governed_scope VALUES (
  'scope:synthetic-identity-drift','SYNTHETIC_CONTROL',ARRAY['case:identity-drift'],
  'SYNTHETIC','SYNTHETIC',ARRAY['SYNTHETIC-GEOGRAPHY'],
  ARRAY['SYNTHETIC-INSTITUTION'],ARRAY['SYNTHETIC-ACTOR'],
  ARRAY['SYNTHETIC-MECHANISM'],ARRAY['Stable-identity scope negative.'],
  encode(sha256(convert_to('scope:synthetic-identity-drift','UTF8')),'hex'));
INSERT INTO exploration_v3.concept_sense VALUES (
  'sense:synthetic:1:drift','concept:synthetic:1','SYNTHETIC_CONTROL',
  'Changed synthetic bounded sense','INQUIRY_ONLY',false,'authority:synthetic-db-v3','1',
  encode(sha256(convert_to('sense:synthetic:1:drift','UTF8')),'hex'),ARRAY[]::text[],
  false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic identity negative control.');

CREATE FUNCTION pg_temp.stage_identity_revision(
  p_revision_id text,
  p_scope_id text,
  p_first_sense_id text,
  p_scope_context_qualifications text[] DEFAULT ARRAY[]::text[]
) RETURNS void LANGUAGE plpgsql AS $function$
BEGIN
  INSERT INTO exploration_v3.association_revision (
    association_revision_id,association_id,revision_number,scope_id,lifecycle_state,
    support_mode,evidence_complete,same_configuration,conflicts_resolved,
    rights_cleared_for_governed_use,synthesis_complete,uncertainty_status,
    uncertainty_level,uncertainty_activation_policy,uncertainty_rationale,
    activation_decision,all_activation_gates_pass,semantic_version,semantic_sha256,
    presentation_sha256,product_eligible,product_eligibility_disposition,
    product_path,product_ineligibility_reason,qualifications,explicit_non_claims,
    supersedes_association_revision_id,created_at,scope_context_qualifications
  ) VALUES (
    p_revision_id,'association:v3:d9a68bf6518292a0495c3196',2,p_scope_id,
    'INQUIRY_ONLY','NONE',false,true,true,true,false,'UNRESOLVED','HIGH',
    'BLOCKS_ACTIVATION','Stable identity revision test.','NOT_REQUESTED',false,'2',
    encode(sha256(convert_to(p_revision_id,'UTF8')),'hex'),
    encode(sha256(convert_to('presentation:'||p_revision_id,'UTF8')),'hex'),
    false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic identity test.',ARRAY[]::text[],
    ARRAY['No research claim.'],'association-revision:synthetic:sparse-three:v1',
    '2026-08-28T00:00:00Z',p_scope_context_qualifications);
  INSERT INTO exploration_v3.association_incidence VALUES
    ('incidence:'||p_revision_id||':1',p_revision_id,'concept:synthetic:1',
      p_first_sense_id,NULL,NULL,p_scope_id,ARRAY[]::text[]),
    ('incidence:'||p_revision_id||':2',p_revision_id,'concept:synthetic:2',
      'sense:synthetic:2',NULL,NULL,p_scope_id,ARRAY[]::text[]),
    ('incidence:'||p_revision_id||':3',p_revision_id,'concept:synthetic:3',
      'sense:synthetic:3',NULL,NULL,p_scope_id,ARRAY[]::text[]);
END
$function$;

DO $stable_identity_same_revision$
DECLARE v_message text;
BEGIN
  BEGIN
    PERFORM pg_temp.stage_identity_revision(
      'association-revision:synthetic:identity-same:v2',
      'scope:synthetic-sparse-three','sense:synthetic:1',
      ARRAY['Qualification-only successor preserves stable association identity.']);
    SET CONSTRAINTS ALL IMMEDIATE;
    PERFORM pg_temp.assert_true(
      exploration_v3.association_revision_identity_sha(
        'association-revision:synthetic:identity-same:v2') =
          'd9a68bf6518292a0495c3196320e4bdd4cfa4c167a4a4d934227a19ff196580d'
      AND (SELECT scope_context_qualifications
        FROM exploration_v3.association_revision
        WHERE association_revision_id =
          'association-revision:synthetic:identity-same:v2') =
        ARRAY['Qualification-only successor preserves stable association identity.']
      AND (SELECT scope_context_qualifications
        FROM exploration_v3.association_revision
        WHERE association_revision_id =
          'association-revision:synthetic:identity-same:v2') <>
        (SELECT scope_context_qualifications
        FROM exploration_v3.association_revision
        WHERE association_revision_id =
          'association-revision:synthetic:sparse-three:v1')
      AND release.canonical_jsonb_sha256(jsonb_build_object(
        'scope_id','scope:synthetic-sparse-three',
        'context_qualifications',(SELECT scope_context_qualifications
          FROM exploration_v3.association_revision
          WHERE association_revision_id =
            'association-revision:synthetic:identity-same:v2'))) <>
        release.canonical_jsonb_sha256(jsonb_build_object(
        'scope_id','scope:synthetic-sparse-three',
        'context_qualifications',(SELECT scope_context_qualifications
          FROM exploration_v3.association_revision
          WHERE association_revision_id =
            'association-revision:synthetic:sparse-three:v1')))
      AND (SELECT semantic_sha256 FROM exploration_v3.association_revision
        WHERE association_revision_id =
          'association-revision:synthetic:identity-same:v2') <>
        (SELECT semantic_sha256 FROM exploration_v3.association_revision
        WHERE association_revision_id =
          'association-revision:synthetic:sparse-three:v1')
      AND exploration_v3.aggregate_content_sha(
        'ASSOCIATION_REVISION','association-revision:synthetic:identity-same:v2') <>
        exploration_v3.aggregate_content_sha(
        'ASSOCIATION_REVISION','association-revision:synthetic:sparse-three:v1')
      AND EXISTS (SELECT 1 FROM exploration_v3.association_revision head
        WHERE head.association_revision_id =
          'association-revision:synthetic:identity-same:v2'
          AND NOT EXISTS (SELECT 1 FROM exploration_v3.association_revision next
            WHERE next.supersedes_association_revision_id =
              head.association_revision_id))
      AND EXISTS (SELECT 1 FROM exploration_v3.association_revision old
        WHERE old.association_revision_id =
          'association-revision:synthetic:sparse-three:v1'
          AND EXISTS (SELECT 1 FROM exploration_v3.association_revision next
            WHERE next.supersedes_association_revision_id =
              old.association_revision_id)),
      'qualification-only successor preserves identity, changes revision scope semantics, and becomes current head');
    RAISE EXCEPTION 'VALID_IDENTICAL_IDENTITY_REVISION_ACCEPTED';
  EXCEPTION WHEN raise_exception THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'VALID_IDENTICAL_IDENTITY_REVISION_ACCEPTED' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$stable_identity_same_revision$;

DO $stable_identity_sense_drift$
DECLARE v_message text;
BEGIN
  BEGIN
    PERFORM pg_temp.stage_identity_revision(
      'association-revision:synthetic:identity-sense-drift:v2',
      'scope:synthetic-sparse-three','sense:synthetic:1:drift');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'ASSOCIATION_SENSE_IDENTITY_DRIFT_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'ASSOCIATION_STABLE_IDENTITY_MISMATCH' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$stable_identity_sense_drift$;

DO $stable_identity_scope_drift$
DECLARE v_message text;
BEGIN
  BEGIN
    PERFORM pg_temp.stage_identity_revision(
      'association-revision:synthetic:identity-scope-drift:v2',
      'scope:synthetic-identity-drift','sense:synthetic:1');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'ASSOCIATION_SCOPE_IDENTITY_DRIFT_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'ASSOCIATION_STABLE_IDENTITY_MISMATCH' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$stable_identity_scope_drift$;

-- Activation before final governed review must fail at the deferred boundary.
DO $activation_before_review$
DECLARE v_state text; v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.association_revision (
      association_revision_id,association_id,revision_number,scope_id,lifecycle_state,
      support_mode,evidence_complete,same_configuration,conflicts_resolved,
      rights_cleared_for_governed_use,synthesis_complete,uncertainty_status,
      uncertainty_level,uncertainty_activation_policy,uncertainty_rationale,
      activation_decision,all_activation_gates_pass,semantic_version,semantic_sha256,
      presentation_sha256,product_eligible,product_eligibility_disposition,
      product_path,product_ineligibility_reason,qualifications,explicit_non_claims,
      supersedes_association_revision_id,created_at
    ) VALUES (
      'association-revision:synthetic:unreviewed:v2',
      'association:v3:d9a68bf6518292a0495c3196',2,
      'scope:synthetic-sparse-three','ACTIVE','DIRECT_GROUP',true,true,true,true,true,
      'RESOLVED_BOUNDED','LOW','ALLOWED_BOUNDED','Missing-review negative control.',
      'ALLOW',true,'1',repeat('a',64),repeat('b',64),false,'NOT_APPLICABLE_SYNTHETIC',
      NULL,'Synthetic controls are never product eligible.',ARRAY[]::text[],
      ARRAY['No production claim.'],
      'association-revision:synthetic:sparse-three:v1','2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.association_incidence
    SELECT 'incidence:unreviewed:'||n,'association-revision:synthetic:unreviewed:v2',
      'concept:synthetic:'||n,'sense:synthetic:'||n,NULL,NULL,
      'scope:synthetic-sparse-three',ARRAY[]::text[]
    FROM generate_series(1,3) n;
    INSERT INTO exploration_v3.association_revision_evidence VALUES (
      'association-revision:synthetic:unreviewed:v2','evidence:synthetic:group','supports');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'ACTIVATION_BEFORE_REVIEW_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE,v_message=MESSAGE_TEXT;
    IF v_state <> '23514' OR v_message <> 'ACTIVE_ASSOCIATION_REVIEW_MISSING' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$activation_before_review$;

-- FINAL support dispositions are fact-derived even for inactive research
-- controls; an inactive row cannot carry a positive disposition with FAIL.
DO $inactive_final_positive_fail_block$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.association_revision (
      association_revision_id,association_id,revision_number,scope_id,lifecycle_state,
      support_mode,evidence_complete,same_configuration,conflicts_resolved,
      rights_cleared_for_governed_use,synthesis_complete,uncertainty_status,
      uncertainty_level,uncertainty_activation_policy,uncertainty_rationale,
      activation_decision,all_activation_gates_pass,semantic_version,semantic_sha256,
      presentation_sha256,product_eligible,product_eligibility_disposition,
      product_path,product_ineligibility_reason,qualifications,explicit_non_claims,
      supersedes_association_revision_id,created_at
    ) VALUES (
      'association-revision:synthetic:positive-fail:v2',
      'association:v3:d9a68bf6518292a0495c3196',2,'scope:synthetic-sparse-three',
      'INACTIVE','DIRECT_GROUP',true,true,true,true,true,'RESOLVED_BOUNDED','LOW',
      'ALLOWED_BOUNDED','Inactive positive-disposition parity negative.',
      'NOT_REQUESTED',false,'2',repeat('1',64),repeat('2',64),false,
      'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic negative.',ARRAY[]::text[],
      ARRAY['No production claim.'],'association-revision:synthetic:sparse-three:v1',
      '2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.association_incidence
    SELECT 'incidence:positive-fail:'||n,
      'association-revision:synthetic:positive-fail:v2','concept:synthetic:'||n,
      'sense:synthetic:'||n,NULL,NULL,'scope:synthetic-sparse-three',ARRAY[]::text[]
    FROM generate_series(1,3) n;
    INSERT INTO exploration_v3.association_revision_evidence VALUES (
      'association-revision:synthetic:positive-fail:v2',
      'evidence:synthetic:group','supports');
    INSERT INTO exploration_v3.association_review VALUES (
      'review:synthetic:positive-fail:v2',
      'association-revision:synthetic:positive-fail:v2','FINAL',
      'DIRECT_HIGHER_ORDER_SUPPORT','FAIL',false,true,true,1,
      'authority:synthetic-db-v3','2',ARRAY['Intentional parity negative.'],
      ARRAY['No production claim.'],repeat('3',64),'2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'ASSOCIATION_REVISION','association-revision:synthetic:positive-fail:v2',
      exploration_v3.aggregate_content_sha(
        'ASSOCIATION_REVISION','association-revision:synthetic:positive-fail:v2'),
      '2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'INACTIVE_FINAL_POSITIVE_FAIL_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'FINAL_ASSOCIATION_DISPOSITION_PARITY_INVALID' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$inactive_final_positive_fail_block$;

-- A coherent composition preserves the hyperedge as one realization.
INSERT INTO exploration_v3.composition VALUES (
  'composition:synthetic:sparse-three','SYNTHETIC_CONTROL','2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.composition_revision VALUES (
  'composition-revision:synthetic:sparse-three:v1','composition:synthetic:sparse-three',1,
  'HYPEREDGE_HUB',true,'PASS',
  encode(sha256(convert_to('composition-revision:synthetic:sparse-three:v1','UTF8')),'hex'),
  encode(sha256(convert_to('composition-presentation:synthetic:sparse-three:v1','UTF8')),'hex'),
  false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic compositions are never product eligible.',
  NULL,'2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.composition_node
SELECT 'composition-revision:synthetic:sparse-three:v1','concept:synthetic:'||n
FROM generate_series(1,3) n;
INSERT INTO exploration_v3.association_realization VALUES (
  'realization:synthetic:sparse-three','composition-revision:synthetic:sparse-three:v1',
  'association-revision:synthetic:sparse-three:v1','HYPEREDGE_HUB',
  encode(sha256(convert_to('realization:synthetic:sparse-three','UTF8')),'hex'),
  encode(sha256(convert_to('realization-presentation:synthetic:sparse-three','UTF8')),'hex'),
  'SYNTHETIC_HUB','NEUTRAL_CONTROL');
INSERT INTO exploration_v3.realization_incidence
SELECT 'realization:synthetic:sparse-three','incidence:synthetic:'||n
FROM generate_series(1,3) n;
INSERT INTO exploration_v3.composition_coherence_review VALUES (
  'composition-review:synthetic:sparse-three:v1',
  'composition-revision:synthetic:sparse-three:v1','SYNTHETIC_CONTROL','FINAL',
  'authority:synthetic-db-v3','1','PASS',true,true,true,true,0,'COHERENT',
  ARRAY['Synthetic global coherence oracle passes.'],
  encode(sha256(convert_to('composition-review:synthetic:sparse-three:v1','UTF8')),'hex'),
  '2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.composition_review_realization VALUES (
  'composition-review:synthetic:sparse-three:v1','realization:synthetic:sparse-three');
INSERT INTO exploration_v3.aggregate_seal VALUES (
  'COMPOSITION_REVISION','composition-revision:synthetic:sparse-three:v1',
  exploration_v3.aggregate_content_sha(
    'COMPOSITION_REVISION','composition-revision:synthetic:sparse-three:v1'),
  '2026-08-28T00:00:00Z');
SET CONSTRAINTS ALL IMMEDIATE;
SET CONSTRAINTS ALL DEFERRED;

-- The same higher-order revision cannot be rendered as a pair edge.
DO $hyperedge_pair_projection$
DECLARE v_state text; v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.composition VALUES (
      'composition:synthetic:bad-projection','SYNTHETIC_CONTROL','2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.composition_revision VALUES (
      'composition-revision:synthetic:bad-projection:v1','composition:synthetic:bad-projection',1,
      'PAIR_EDGE',true,'PASS',repeat('c',64),repeat('d',64),false,
      'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic negative control.',NULL,
      '2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.composition_node
    SELECT 'composition-revision:synthetic:bad-projection:v1','concept:synthetic:'||n
    FROM generate_series(1,3) n;
    INSERT INTO exploration_v3.association_realization VALUES (
      'realization:synthetic:bad-projection',
      'composition-revision:synthetic:bad-projection:v1',
      'association-revision:synthetic:sparse-three:v1','PAIR_EDGE',
      repeat('e',64),repeat('f',64),'BAD_PAIR_EDGE','NEGATIVE_CONTROL');
    INSERT INTO exploration_v3.realization_incidence
    SELECT 'realization:synthetic:bad-projection','incidence:synthetic:'||n
    FROM generate_series(1,3) n;
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'HYPEREDGE_PAIR_PROJECTION_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE,v_message=MESSAGE_TEXT;
    IF v_state <> '23514' OR v_message <> 'REALIZATION_KIND_ASSOCIATION_MISMATCH' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$hyperedge_pair_projection$;

-- COHERENT is a semantic decision with exact gate parity even when the
-- composition is deliberately not product eligible.
DO $nonproduct_coherent_review_parity$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.composition VALUES (
      'composition:synthetic:bad-coherence','SYNTHETIC_CONTROL','2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.composition_revision VALUES (
      'composition-revision:synthetic:bad-coherence:v1',
      'composition:synthetic:bad-coherence',1,'HYPEREDGE_HUB',true,'PASS',
      encode(sha256(convert_to('composition-revision:synthetic:bad-coherence:v1','UTF8')),'hex'),
      encode(sha256(convert_to('composition-presentation:synthetic:bad-coherence:v1','UTF8')),'hex'),
      false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic negative control.',NULL,
      '2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.composition_node
    SELECT 'composition-revision:synthetic:bad-coherence:v1','concept:synthetic:'||n
    FROM generate_series(1,3) n;
    INSERT INTO exploration_v3.association_realization VALUES (
      'realization:synthetic:bad-coherence',
      'composition-revision:synthetic:bad-coherence:v1',
      'association-revision:synthetic:sparse-three:v1','HYPEREDGE_HUB',
      encode(sha256(convert_to('realization:synthetic:bad-coherence','UTF8')),'hex'),
      encode(sha256(convert_to('realization-presentation:synthetic:bad-coherence','UTF8')),'hex'),
      'SYNTHETIC_HUB','NEGATIVE_CONTROL');
    INSERT INTO exploration_v3.realization_incidence
    SELECT 'realization:synthetic:bad-coherence','incidence:synthetic:'||n
    FROM generate_series(1,3) n;
    INSERT INTO exploration_v3.composition_coherence_review VALUES (
      'composition-review:synthetic:bad-coherence:v1',
      'composition-revision:synthetic:bad-coherence:v1','SYNTHETIC_CONTROL','FINAL',
      'authority:synthetic-db-v3','1','FAIL',true,true,true,true,1,'COHERENT',
      ARRAY['Intentionally inconsistent coherent-decision negative.'],
      encode(sha256(convert_to('composition-review:synthetic:bad-coherence:v1','UTF8')),'hex'),
      '2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.composition_review_realization VALUES (
      'composition-review:synthetic:bad-coherence:v1',
      'realization:synthetic:bad-coherence');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'COMPOSITION_REVISION','composition-revision:synthetic:bad-coherence:v1',
      exploration_v3.aggregate_content_sha(
        'COMPOSITION_REVISION','composition-revision:synthetic:bad-coherence:v1'),
      '2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'NONPRODUCT_COHERENT_REVIEW_PARITY_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'FINAL_COMPOSITION_REVIEW_PARITY_INVALID' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$nonproduct_coherent_review_parity$;

DO $nonproduct_incoherent_pass_parity$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.composition VALUES (
      'composition:synthetic:incoherent-pass','SYNTHETIC_CONTROL',
      '2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.composition_revision VALUES (
      'composition-revision:synthetic:incoherent-pass:v1',
      'composition:synthetic:incoherent-pass',1,'HYPEREDGE_HUB',true,'PASS',
      repeat('4',64),repeat('5',64),false,'NOT_APPLICABLE_SYNTHETIC',NULL,
      'Synthetic negative control.',NULL,'2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.composition_node
    SELECT 'composition-revision:synthetic:incoherent-pass:v1','concept:synthetic:'||n
    FROM generate_series(1,3) n;
    INSERT INTO exploration_v3.association_realization VALUES (
      'realization:synthetic:incoherent-pass',
      'composition-revision:synthetic:incoherent-pass:v1',
      'association-revision:synthetic:sparse-three:v1','HYPEREDGE_HUB',
      repeat('6',64),repeat('7',64),'SYNTHETIC_HUB','NEGATIVE_CONTROL');
    INSERT INTO exploration_v3.realization_incidence
    SELECT 'realization:synthetic:incoherent-pass','incidence:synthetic:'||n
    FROM generate_series(1,3) n;
    INSERT INTO exploration_v3.composition_coherence_review VALUES (
      'composition-review:synthetic:incoherent-pass:v1',
      'composition-revision:synthetic:incoherent-pass:v1','SYNTHETIC_CONTROL','FINAL',
      'authority:synthetic-db-v3','1','PASS',true,true,true,true,0,'INCOHERENT',
      ARRAY['Intentional INCOHERENT-with-PASS negative.'],repeat('8',64),
      '2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.composition_review_realization VALUES (
      'composition-review:synthetic:incoherent-pass:v1',
      'realization:synthetic:incoherent-pass');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'COMPOSITION_REVISION','composition-revision:synthetic:incoherent-pass:v1',
      exploration_v3.aggregate_content_sha(
        'COMPOSITION_REVISION','composition-revision:synthetic:incoherent-pass:v1'),
      '2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'INCOHERENT_WITH_PASS_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'FINAL_COMPOSITION_REVIEW_PARITY_INVALID' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$nonproduct_incoherent_pass_parity$;

-- Bipartite state, explicit transition, workflow, and export remain distinct.
INSERT INTO exploration_v3.navigation_state VALUES (
  'state:synthetic:sparse-three','SYNTHETIC_CONTROL',
  'composition-revision:synthetic:sparse-three:v1','nav:synthetic:concept:3',true,
  encode(sha256(convert_to('state:synthetic:sparse-three','UTF8')),'hex'),
  encode(sha256(convert_to('state-presentation:synthetic:sparse-three','UTF8')),'hex'),
  'SYNTHETIC_FOCUS','SYNTHETIC');
INSERT INTO exploration_v3.navigation_node VALUES
  ('state:synthetic:sparse-three','nav:synthetic:concept:1','CONCEPT','concept:synthetic:1',NULL),
  ('state:synthetic:sparse-three','nav:synthetic:association','ASSOCIATION',NULL,
    'association-revision:synthetic:sparse-three:v1'),
  ('state:synthetic:sparse-three','nav:synthetic:concept:3','CONCEPT','concept:synthetic:3',NULL);
INSERT INTO exploration_v3.navigation_path_step VALUES
  ('state:synthetic:sparse-three',0,'nav:synthetic:concept:1','incidence:synthetic:1',
    'nav:synthetic:association'),
  ('state:synthetic:sparse-three',1,'nav:synthetic:association','incidence:synthetic:3',
    'nav:synthetic:concept:3');
INSERT INTO exploration_v3.aggregate_seal VALUES (
  'NAVIGATION_STATE','state:synthetic:sparse-three',
  exploration_v3.aggregate_content_sha(
    'NAVIGATION_STATE','state:synthetic:sparse-three'),
  '2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.interaction_transition VALUES (
  'transition:synthetic:follow','SYNTHETIC_CONTROL','state:synthetic:sparse-three',
  'state:synthetic:sparse-three','FOLLOW_INCIDENCE','incidence:synthetic:1',
  'association-revision:synthetic:sparse-three:v1','realization:synthetic:sparse-three',
  false,encode(sha256(convert_to('transition:synthetic:follow','UTF8')),'hex'),
  false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic transitions are never product eligible.');
INSERT INTO exploration_v3.exploration_workflow VALUES (
  'workflow:synthetic:sparse-three','SYNTHETIC_CONTROL','state:synthetic:sparse-three',
  'FOLLOW_INCIDENCE',true,
  encode(sha256(convert_to('workflow:synthetic:sparse-three','UTF8')),'hex'),
  false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic workflows are never product eligible.');
INSERT INTO exploration_v3.workflow_state VALUES (
  'workflow:synthetic:sparse-three','state:synthetic:sparse-three');
INSERT INTO exploration_v3.workflow_association_revision VALUES (
  'workflow:synthetic:sparse-three','association-revision:synthetic:sparse-three:v1');
INSERT INTO exploration_v3.workflow_association_realization VALUES (
  'workflow:synthetic:sparse-three','realization:synthetic:sparse-three');
INSERT INTO exploration_v3.workflow_transition VALUES (
  'workflow:synthetic:sparse-three','transition:synthetic:follow');
INSERT INTO exploration_v3.aggregate_seal VALUES (
  'WORKFLOW','workflow:synthetic:sparse-three',
  exploration_v3.aggregate_content_sha('WORKFLOW','workflow:synthetic:sparse-three'),
  '2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.export_manifest VALUES (
  'export:synthetic:sparse-three','SYNTHETIC_CONTROL','workflow:synthetic:sparse-three',
  'state:synthetic:sparse-three','composition-revision:synthetic:sparse-three:v1',
  encode(sha256(convert_to('export:synthetic:sparse-three','UTF8')),'hex'),
  encode(sha256(convert_to('export-presentation:synthetic:sparse-three','UTF8')),'hex'),
  'TRACE_V3_SYNTHETIC_JSON','NEUTRAL',true,false,'NOT_APPLICABLE_SYNTHETIC',NULL,
  'Synthetic exports are never product eligible.');
INSERT INTO exploration_v3.export_projection_preservation VALUES (
  'export:synthetic:sparse-three','association-revision:synthetic:sparse-three:v1',
  'realization:synthetic:sparse-three','NONE','HYPEREDGE_HUB');
INSERT INTO exploration_v3.aggregate_seal VALUES (
  'EXPORT','export:synthetic:sparse-three',
  exploration_v3.aggregate_content_sha('EXPORT','export:synthetic:sparse-three'),
  '2026-08-28T00:00:00Z');
SET CONSTRAINTS ALL IMMEDIATE;
SET CONSTRAINTS ALL DEFERRED;

SELECT pg_temp.assert_true(
  (SELECT count(*) FROM exploration_v3.navigation_state) = 1
  AND (SELECT count(*) FROM exploration_v3.interaction_transition) = 1
  AND (SELECT count(*) FROM exploration_v3.exploration_workflow) = 1
  AND (SELECT count(*) FROM exploration_v3.export_manifest) = 1,
  'state transition workflow and export are distinct records');

DO $navigation_continuity_block$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.navigation_state VALUES (
      'state:synthetic:discontinuous','SYNTHETIC_CONTROL',
      'composition-revision:synthetic:sparse-three:v1','nav:discontinuous:association',true,
      encode(sha256(convert_to('state:synthetic:discontinuous','UTF8')),'hex'),
      encode(sha256(convert_to('state-presentation:synthetic:discontinuous','UTF8')),'hex'),
      'SYNTHETIC_FOCUS','SYNTHETIC');
    INSERT INTO exploration_v3.navigation_node VALUES
      ('state:synthetic:discontinuous','nav:discontinuous:concept:1','CONCEPT',
        'concept:synthetic:1',NULL),
      ('state:synthetic:discontinuous','nav:discontinuous:association','ASSOCIATION',NULL,
        'association-revision:synthetic:sparse-three:v1'),
      ('state:synthetic:discontinuous','nav:discontinuous:concept:3','CONCEPT',
        'concept:synthetic:3',NULL);
    INSERT INTO exploration_v3.navigation_path_step VALUES
      ('state:synthetic:discontinuous',0,'nav:discontinuous:concept:1',
        'incidence:synthetic:1','nav:discontinuous:association'),
      ('state:synthetic:discontinuous',1,'nav:discontinuous:concept:3',
        'incidence:synthetic:3','nav:discontinuous:association');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'NAVIGATION_STATE','state:synthetic:discontinuous',
      exploration_v3.aggregate_content_sha(
        'NAVIGATION_STATE','state:synthetic:discontinuous'),
      '2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'NAVIGATION_DISCONTINUITY_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'NAVIGATION_PATH_CONTINUITY_OR_TERMINAL_FOCUS_INVALID' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$navigation_continuity_block$;

DO $navigation_terminal_focus_block$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.navigation_state VALUES (
      'state:synthetic:wrong-terminal','SYNTHETIC_CONTROL',
      'composition-revision:synthetic:sparse-three:v1','nav:wrong-terminal:concept:1',true,
      encode(sha256(convert_to('state:synthetic:wrong-terminal','UTF8')),'hex'),
      encode(sha256(convert_to('state-presentation:synthetic:wrong-terminal','UTF8')),'hex'),
      'SYNTHETIC_FOCUS','SYNTHETIC');
    INSERT INTO exploration_v3.navigation_node VALUES
      ('state:synthetic:wrong-terminal','nav:wrong-terminal:concept:1','CONCEPT',
        'concept:synthetic:1',NULL),
      ('state:synthetic:wrong-terminal','nav:wrong-terminal:association','ASSOCIATION',NULL,
        'association-revision:synthetic:sparse-three:v1'),
      ('state:synthetic:wrong-terminal','nav:wrong-terminal:concept:3','CONCEPT',
        'concept:synthetic:3',NULL);
    INSERT INTO exploration_v3.navigation_path_step VALUES
      ('state:synthetic:wrong-terminal',0,'nav:wrong-terminal:concept:1',
        'incidence:synthetic:1','nav:wrong-terminal:association'),
      ('state:synthetic:wrong-terminal',1,'nav:wrong-terminal:association',
        'incidence:synthetic:3','nav:wrong-terminal:concept:3');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'NAVIGATION_STATE','state:synthetic:wrong-terminal',
      exploration_v3.aggregate_content_sha(
        'NAVIGATION_STATE','state:synthetic:wrong-terminal'),
      '2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'NAVIGATION_TERMINAL_FOCUS_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'NAVIGATION_PATH_CONTINUITY_OR_TERMINAL_FOCUS_INVALID' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$navigation_terminal_focus_block$;

-- A two-realization control makes workflow set equality and graph reachability
-- independently observable.  The added pair is inquiry-only and does not
-- project from the active higher-order association.
INSERT INTO exploration_v3.association VALUES (
  'association:v3:2547f3c293c88d2eb9c97a74','SYNTHETIC_CONTROL','PAIR',2,
  'UNORDERED',false,'NOT_APPLICABLE',
  '2547f3c293c88d2eb9c97a7479adb46bfe65688ddbc0e6706532dded2fc76654',
  '2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.association_revision (
  association_revision_id,association_id,revision_number,scope_id,lifecycle_state,
  support_mode,evidence_complete,same_configuration,conflicts_resolved,
  rights_cleared_for_governed_use,synthesis_complete,uncertainty_status,
  uncertainty_level,uncertainty_activation_policy,uncertainty_rationale,
  activation_decision,all_activation_gates_pass,semantic_version,semantic_sha256,
  presentation_sha256,product_eligible,product_eligibility_disposition,
  product_path,product_ineligibility_reason,qualifications,explicit_non_claims,
  supersedes_association_revision_id,created_at,scope_context_qualifications
) VALUES (
  'association-revision:synthetic:workflow-pair:v1',
  'association:v3:2547f3c293c88d2eb9c97a74',1,'scope:synthetic-sparse-three',
  'INQUIRY_ONLY','NONE',false,true,true,true,false,'UNRESOLVED','HIGH',
  'BLOCKS_ACTIVATION','Inquiry-only workflow set-control pair.',
  'NOT_REQUESTED',false,'1',
  encode(sha256(convert_to('association-revision:synthetic:workflow-pair:v1','UTF8')),'hex'),
  encode(sha256(convert_to('presentation:synthetic:workflow-pair:v1','UTF8')),'hex'),
  false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic controls are never product eligible.',
  ARRAY['Inquiry-only set-coverage fixture.'],
  ARRAY['Does not create an active pair claim.'],NULL,'2026-08-28T00:00:00Z',
  ARRAY['Not historical evidence.']);
INSERT INTO exploration_v3.association_incidence VALUES
  ('incidence:synthetic:workflow-pair:1',
    'association-revision:synthetic:workflow-pair:v1','concept:synthetic:1',
    'sense:synthetic:1',NULL,NULL,'scope:synthetic-sparse-three',ARRAY[]::text[]),
  ('incidence:synthetic:workflow-pair:2',
    'association-revision:synthetic:workflow-pair:v1','concept:synthetic:2',
    'sense:synthetic:2',NULL,NULL,'scope:synthetic-sparse-three',ARRAY[]::text[]);

INSERT INTO exploration_v3.composition VALUES (
  'composition:synthetic:workflow-two','SYNTHETIC_CONTROL','2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.composition_revision VALUES (
  'composition-revision:synthetic:workflow-two:v1',
  'composition:synthetic:workflow-two',1,'HYPEREDGE_WITH_PAIR_CONTEXT',true,'PASS',
  encode(sha256(convert_to('composition-revision:synthetic:workflow-two:v1','UTF8')),'hex'),
  encode(sha256(convert_to('composition-presentation:synthetic:workflow-two:v1','UTF8')),'hex'),
  false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic controls are never product eligible.',
  NULL,'2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.composition_node
SELECT 'composition-revision:synthetic:workflow-two:v1','concept:synthetic:'||n
FROM generate_series(1,3) n;
INSERT INTO exploration_v3.association_realization VALUES
  ('realization:synthetic:workflow-two:hyperedge',
    'composition-revision:synthetic:workflow-two:v1',
    'association-revision:synthetic:sparse-three:v1','HYPEREDGE_HUB',
    encode(sha256(convert_to('realization:synthetic:workflow-two:hyperedge','UTF8')),'hex'),
    encode(sha256(convert_to('realization-presentation:synthetic:workflow-two:hyperedge','UTF8')),'hex'),
    'SYNTHETIC_HUB','NEUTRAL_CONTROL'),
  ('realization:synthetic:workflow-two:pair',
    'composition-revision:synthetic:workflow-two:v1',
    'association-revision:synthetic:workflow-pair:v1','PAIR_EDGE',
    encode(sha256(convert_to('realization:synthetic:workflow-two:pair','UTF8')),'hex'),
    encode(sha256(convert_to('realization-presentation:synthetic:workflow-two:pair','UTF8')),'hex'),
    'SYNTHETIC_PAIR_EDGE','NEUTRAL_CONTROL');
INSERT INTO exploration_v3.realization_incidence
SELECT 'realization:synthetic:workflow-two:hyperedge','incidence:synthetic:'||n
FROM generate_series(1,3) n;
INSERT INTO exploration_v3.realization_incidence VALUES
  ('realization:synthetic:workflow-two:pair','incidence:synthetic:workflow-pair:1'),
  ('realization:synthetic:workflow-two:pair','incidence:synthetic:workflow-pair:2');

INSERT INTO exploration_v3.navigation_state VALUES
  ('state:synthetic:workflow-two:a','SYNTHETIC_CONTROL',
    'composition-revision:synthetic:workflow-two:v1','nav:workflow-two:a:concept:3',true,
    encode(sha256(convert_to('state:synthetic:workflow-two:a','UTF8')),'hex'),
    encode(sha256(convert_to('state-presentation:synthetic:workflow-two:a','UTF8')),'hex'),
    'SYNTHETIC_FOCUS','SYNTHETIC'),
  ('state:synthetic:workflow-two:b','SYNTHETIC_CONTROL',
    'composition-revision:synthetic:workflow-two:v1','nav:workflow-two:b:concept:3',true,
    encode(sha256(convert_to('state:synthetic:workflow-two:b','UTF8')),'hex'),
    encode(sha256(convert_to('state-presentation:synthetic:workflow-two:b','UTF8')),'hex'),
    'SYNTHETIC_FOCUS','SYNTHETIC');
INSERT INTO exploration_v3.navigation_node VALUES
  ('state:synthetic:workflow-two:a','nav:workflow-two:a:concept:1','CONCEPT',
    'concept:synthetic:1',NULL),
  ('state:synthetic:workflow-two:a','nav:workflow-two:a:association','ASSOCIATION',NULL,
    'association-revision:synthetic:sparse-three:v1'),
  ('state:synthetic:workflow-two:a','nav:workflow-two:a:concept:3','CONCEPT',
    'concept:synthetic:3',NULL),
  ('state:synthetic:workflow-two:b','nav:workflow-two:b:concept:1','CONCEPT',
    'concept:synthetic:1',NULL),
  ('state:synthetic:workflow-two:b','nav:workflow-two:b:association','ASSOCIATION',NULL,
    'association-revision:synthetic:sparse-three:v1'),
  ('state:synthetic:workflow-two:b','nav:workflow-two:b:concept:3','CONCEPT',
    'concept:synthetic:3',NULL);
INSERT INTO exploration_v3.navigation_path_step VALUES
  ('state:synthetic:workflow-two:a',0,'nav:workflow-two:a:concept:1',
    'incidence:synthetic:1','nav:workflow-two:a:association'),
  ('state:synthetic:workflow-two:a',1,'nav:workflow-two:a:association',
    'incidence:synthetic:3','nav:workflow-two:a:concept:3'),
  ('state:synthetic:workflow-two:b',0,'nav:workflow-two:b:concept:1',
    'incidence:synthetic:1','nav:workflow-two:b:association'),
  ('state:synthetic:workflow-two:b',1,'nav:workflow-two:b:association',
    'incidence:synthetic:3','nav:workflow-two:b:concept:3');
INSERT INTO exploration_v3.aggregate_seal VALUES
  ('NAVIGATION_STATE','state:synthetic:workflow-two:a',
    exploration_v3.aggregate_content_sha(
      'NAVIGATION_STATE','state:synthetic:workflow-two:a'),
    '2026-08-28T00:00:00Z'),
  ('NAVIGATION_STATE','state:synthetic:workflow-two:b',
    exploration_v3.aggregate_content_sha(
      'NAVIGATION_STATE','state:synthetic:workflow-two:b'),
    '2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.interaction_transition VALUES
  ('transition:synthetic:workflow-two:a-to-b','SYNTHETIC_CONTROL',
    'state:synthetic:workflow-two:a','state:synthetic:workflow-two:b','MOVE_FOCUS',
    NULL,NULL,NULL,true,
    encode(sha256(convert_to('transition:synthetic:workflow-two:a-to-b','UTF8')),'hex'),
    false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic transitions are never product eligible.'),
  ('transition:synthetic:workflow-two:a-self','SYNTHETIC_CONTROL',
    'state:synthetic:workflow-two:a','state:synthetic:workflow-two:a','MOVE_FOCUS',
    NULL,NULL,NULL,false,
    encode(sha256(convert_to('transition:synthetic:workflow-two:a-self','UTF8')),'hex'),
    false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic transitions are never product eligible.');
SET CONSTRAINTS ALL IMMEDIATE;
SET CONSTRAINTS ALL DEFERRED;

INSERT INTO exploration_v3.exploration_workflow VALUES (
  'workflow:synthetic:workflow-two:valid','SYNTHETIC_CONTROL',
  'state:synthetic:workflow-two:a','MOVE_FOCUS',true,
  encode(sha256(convert_to('workflow:synthetic:workflow-two:valid','UTF8')),'hex'),
  false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic workflows are never product eligible.');
INSERT INTO exploration_v3.workflow_state VALUES
  ('workflow:synthetic:workflow-two:valid','state:synthetic:workflow-two:a'),
  ('workflow:synthetic:workflow-two:valid','state:synthetic:workflow-two:b');
INSERT INTO exploration_v3.workflow_association_revision VALUES
  ('workflow:synthetic:workflow-two:valid','association-revision:synthetic:sparse-three:v1'),
  ('workflow:synthetic:workflow-two:valid','association-revision:synthetic:workflow-pair:v1');
INSERT INTO exploration_v3.workflow_association_realization VALUES
  ('workflow:synthetic:workflow-two:valid','realization:synthetic:workflow-two:hyperedge'),
  ('workflow:synthetic:workflow-two:valid','realization:synthetic:workflow-two:pair');
INSERT INTO exploration_v3.workflow_transition VALUES (
  'workflow:synthetic:workflow-two:valid','transition:synthetic:workflow-two:a-to-b');
INSERT INTO exploration_v3.aggregate_seal VALUES (
  'WORKFLOW','workflow:synthetic:workflow-two:valid',
  exploration_v3.aggregate_content_sha(
    'WORKFLOW','workflow:synthetic:workflow-two:valid'),
  '2026-08-28T00:00:00Z');
SET CONSTRAINTS ALL IMMEDIATE;
SET CONSTRAINTS ALL DEFERRED;

DO $workflow_realization_coverage_block$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.exploration_workflow VALUES (
      'workflow:synthetic:workflow-two:omission','SYNTHETIC_CONTROL',
      'state:synthetic:workflow-two:a','MOVE_FOCUS',true,
      encode(sha256(convert_to('workflow:synthetic:workflow-two:omission','UTF8')),'hex'),
      false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic negative control.');
    INSERT INTO exploration_v3.workflow_state VALUES
      ('workflow:synthetic:workflow-two:omission','state:synthetic:workflow-two:a'),
      ('workflow:synthetic:workflow-two:omission','state:synthetic:workflow-two:b');
    INSERT INTO exploration_v3.workflow_association_revision VALUES (
      'workflow:synthetic:workflow-two:omission','association-revision:synthetic:sparse-three:v1');
    INSERT INTO exploration_v3.workflow_association_realization VALUES (
      'workflow:synthetic:workflow-two:omission','realization:synthetic:workflow-two:hyperedge');
    INSERT INTO exploration_v3.workflow_transition VALUES (
      'workflow:synthetic:workflow-two:omission','transition:synthetic:workflow-two:a-to-b');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'WORKFLOW','workflow:synthetic:workflow-two:omission',
      exploration_v3.aggregate_content_sha(
        'WORKFLOW','workflow:synthetic:workflow-two:omission'),
      '2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'WORKFLOW_REALIZATION_OMISSION_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'WORKFLOW_TRACE_INVALID' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$workflow_realization_coverage_block$;

DO $workflow_reachability_block$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.exploration_workflow VALUES (
      'workflow:synthetic:workflow-two:disconnected','SYNTHETIC_CONTROL',
      'state:synthetic:workflow-two:a','MOVE_FOCUS',true,
      encode(sha256(convert_to('workflow:synthetic:workflow-two:disconnected','UTF8')),'hex'),
      false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic negative control.');
    INSERT INTO exploration_v3.workflow_state VALUES
      ('workflow:synthetic:workflow-two:disconnected','state:synthetic:workflow-two:a'),
      ('workflow:synthetic:workflow-two:disconnected','state:synthetic:workflow-two:b');
    INSERT INTO exploration_v3.workflow_association_revision VALUES
      ('workflow:synthetic:workflow-two:disconnected','association-revision:synthetic:sparse-three:v1'),
      ('workflow:synthetic:workflow-two:disconnected','association-revision:synthetic:workflow-pair:v1');
    INSERT INTO exploration_v3.workflow_association_realization VALUES
      ('workflow:synthetic:workflow-two:disconnected','realization:synthetic:workflow-two:hyperedge'),
      ('workflow:synthetic:workflow-two:disconnected','realization:synthetic:workflow-two:pair');
    INSERT INTO exploration_v3.workflow_transition VALUES (
      'workflow:synthetic:workflow-two:disconnected','transition:synthetic:workflow-two:a-self');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'WORKFLOW','workflow:synthetic:workflow-two:disconnected',
      exploration_v3.aggregate_content_sha(
        'WORKFLOW','workflow:synthetic:workflow-two:disconnected'),
      '2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'WORKFLOW_DISCONNECTED_GRAPH_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'WORKFLOW_REACHABILITY_ASSERTION_MISMATCH' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$workflow_reachability_block$;

DO $export_exact_realization_coverage_block$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.export_manifest VALUES (
      'export:synthetic:workflow-two:omission','SYNTHETIC_CONTROL',
      'workflow:synthetic:workflow-two:valid','state:synthetic:workflow-two:a',
      'composition-revision:synthetic:workflow-two:v1',
      encode(sha256(convert_to('export:synthetic:workflow-two:omission','UTF8')),'hex'),
      encode(sha256(convert_to('export-presentation:synthetic:workflow-two:omission','UTF8')),'hex'),
      'TRACE_V3_SYNTHETIC_JSON','NEUTRAL',true,false,'NOT_APPLICABLE_SYNTHETIC',NULL,
      'Synthetic negative control.');
    INSERT INTO exploration_v3.export_projection_preservation VALUES (
      'export:synthetic:workflow-two:omission',
      'association-revision:synthetic:sparse-three:v1',
      'realization:synthetic:workflow-two:hyperedge','NONE','HYPEREDGE_HUB');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'EXPORT','export:synthetic:workflow-two:omission',
      exploration_v3.aggregate_content_sha(
        'EXPORT','export:synthetic:workflow-two:omission'),
      '2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'EXPORT_REALIZATION_OMISSION_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'EXPORT_PROJECTION_PRESERVATION_INVALID' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$export_exact_realization_coverage_block$;

-- Production-but-ineligible pair fixture proves product transitions,
-- workflows, and exports cannot outrun association/composition review gates.
INSERT INTO exploration_v3.governed_authority VALUES (
  'authority:production-db-v3','EXTERNAL_HUMAN_REVIEW','FINAL','1',
  encode(sha256(convert_to('authority:production-db-v3','UTF8')),'hex'),
  '2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.governed_scope VALUES (
  'scope:production-pair','PRODUCTION',ARRAY['case:production-control'],NULL,NULL,
  ARRAY[]::text[],ARRAY[]::text[],ARRAY[]::text[],ARRAY[]::text[],
  ARRAY['Database fail-closed production control.'],
  encode(sha256(convert_to('scope:production-pair','UTF8')),'hex'));
DO $bidirectional_product_tuple_block$
DECLARE v_state text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.concept VALUES (
      'concept:negative:false-eligible','PRODUCTION','Invalid false eligible tuple',
      'INACTIVE',false,'authority:production-db-v3','1',repeat('8',64),
      false,'ELIGIBLE','/trace/v3/invalid',NULL);
    RAISE EXCEPTION 'FALSE_ELIGIBLE_PRODUCT_TUPLE_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE;
    IF v_state <> '23514' THEN RAISE; END IF;
  END;
END
$bidirectional_product_tuple_block$;
INSERT INTO exploration_v3.concept
SELECT 'concept:production:'||n,'PRODUCTION','Production control concept '||n,
  'ACTIVE',true,'authority:production-db-v3','1',
  encode(sha256(convert_to('concept:production:'||n,'UTF8')),'hex'),
  false,'INELIGIBLE',NULL,'No product activation in Round 16B.'
FROM generate_series(1,2) n;
INSERT INTO exploration_v3.concept_sense
SELECT 'sense:production:'||n,'concept:production:'||n,'PRODUCTION',
  'Production control bounded sense '||n,'ACTIVE',true,'authority:production-db-v3','1',
  encode(sha256(convert_to('sense:production:'||n,'UTF8')),'hex'),ARRAY[]::text[],
  false,'INELIGIBLE',NULL,'No product activation in Round 16B.'
FROM generate_series(1,2) n;
INSERT INTO exploration_v3.concept_sense_scope
SELECT 'sense:production:'||n,'scope:production-pair' FROM generate_series(1,2) n;
INSERT INTO exploration_v3.aggregate_seal
SELECT 'CONCEPT_SENSE', sense_id,
  exploration_v3.aggregate_content_sha('CONCEPT_SENSE', sense_id),
  '2026-08-28T00:00:00Z'
FROM exploration_v3.concept_sense WHERE sense_id LIKE 'sense:production:%';

DO $production_sense_synthetic_scope_block$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.concept_sense VALUES (
      'sense:negative:synthetic-scope','concept:production:1','PRODUCTION',
      'Production sense with forbidden synthetic scope','INQUIRY_ONLY',false,
      'authority:production-db-v3','1',repeat('7',64),ARRAY[]::text[],
      false,'INELIGIBLE',NULL,'Negative realm control.');
    INSERT INTO exploration_v3.concept_sense_scope VALUES (
      'sense:negative:synthetic-scope','scope:synthetic-sparse-three');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'PRODUCTION_SENSE_SYNTHETIC_SCOPE_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'CONCEPT_SENSE_SCOPE_REALM_MISMATCH' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$production_sense_synthetic_scope_block$;

DO $cross_realm_export_block$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.export_manifest VALUES (
      'export:negative:cross-realm','PRODUCTION','workflow:synthetic:sparse-three',
      'state:synthetic:sparse-three','composition-revision:synthetic:sparse-three:v1',
      repeat('6',64),repeat('5',64),'TRACE_V3_JSON','NEUTRAL',true,
      false,'INELIGIBLE',NULL,'Cross-realm export negative.');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'CROSS_REALM_EXPORT_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'EXPORT_REALM_MISMATCH' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$cross_realm_export_block$;

DO $composition_node_realm_block$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.composition VALUES (
      'composition:negative:node-realm','SYNTHETIC_CONTROL','2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.composition_revision VALUES (
      'composition-revision:negative:node-realm:v1',
      'composition:negative:node-realm',1,'NEGATIVE_CONTROL',false,'FAIL',
      repeat('a',64),repeat('b',64),false,'NOT_APPLICABLE_SYNTHETIC',NULL,
      'Synthetic negative control.',NULL,'2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.composition_node VALUES (
      'composition-revision:negative:node-realm:v1','concept:production:1');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'COMPOSITION_NODE_REALM_MISMATCH_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'COMPOSITION_NODE_REALM_MISMATCH' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$composition_node_realm_block$;

-- Vocabulary activation is fail-closed even when no association references
-- the isolated concept or sense.
DO $isolated_active_concept_eligibility$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.concept VALUES (
      'concept:negative:active-ineligible','PRODUCTION','Isolated ineligible concept',
      'ACTIVE',false,'authority:production-db-v3','1',repeat('5',64),
      false,'INELIGIBLE',NULL,'Negative control.');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'ISOLATED_ACTIVE_CONCEPT_INELIGIBILITY_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'ACTIVE_CONCEPT_AUTHORITY_OR_ELIGIBILITY_INVALID' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$isolated_active_concept_eligibility$;

DO $isolated_active_concept_pending_authority$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.governed_authority VALUES (
      'authority:negative:pending-concept','RESEARCH_REVIEW','PENDING','1',repeat('6',64),NULL);
    INSERT INTO exploration_v3.concept VALUES (
      'concept:negative:pending-authority','PRODUCTION','Pending-authority concept',
      'ACTIVE',true,'authority:negative:pending-concept','1',repeat('7',64),
      false,'INELIGIBLE',NULL,'Negative control.');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'ISOLATED_ACTIVE_CONCEPT_PENDING_AUTHORITY_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'ACTIVE_CONCEPT_AUTHORITY_OR_ELIGIBILITY_INVALID' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$isolated_active_concept_pending_authority$;

DO $production_concept_synthetic_authority$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.concept VALUES (
      'concept:negative:synthetic-authority','PRODUCTION','Synthetic-authority concept',
      'INQUIRY_ONLY',false,'authority:synthetic-db-v3','1',repeat('8',64),
      false,'INELIGIBLE',NULL,'Negative control.');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'PRODUCTION_CONCEPT_SYNTHETIC_AUTHORITY_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'PRODUCTION_CONCEPT_SYNTHETIC_AUTHORITY_FORBIDDEN' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$production_concept_synthetic_authority$;

DO $isolated_active_sense_eligibility$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.concept_sense VALUES (
      'sense:negative:active-ineligible','concept:production:1','PRODUCTION',
      'Isolated ineligible bounded sense','ACTIVE',false,'authority:production-db-v3','1',
      repeat('9',64),ARRAY[]::text[],false,'INELIGIBLE',NULL,'Negative control.');
    INSERT INTO exploration_v3.concept_sense_scope VALUES (
      'sense:negative:active-ineligible','scope:production-pair');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'CONCEPT_SENSE','sense:negative:active-ineligible',
      exploration_v3.aggregate_content_sha(
        'CONCEPT_SENSE','sense:negative:active-ineligible'),
      '2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'ISOLATED_ACTIVE_SENSE_INELIGIBILITY_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'ACTIVE_CONCEPT_SENSE_AUTHORITY_ELIGIBILITY_OR_SCOPE_INVALID' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$isolated_active_sense_eligibility$;

DO $isolated_active_sense_pending_authority$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.governed_authority VALUES (
      'authority:negative:pending-sense','RESEARCH_REVIEW','PENDING','1',
      encode(sha256(convert_to('authority:negative:pending-sense','UTF8')),'hex'),NULL);
    INSERT INTO exploration_v3.concept_sense VALUES (
      'sense:negative:pending-authority','concept:production:1','PRODUCTION',
      'Pending-authority bounded sense','ACTIVE',true,
      'authority:negative:pending-sense','1',
      encode(sha256(convert_to('sense:negative:pending-authority','UTF8')),'hex'),
      ARRAY[]::text[],false,'INELIGIBLE',NULL,'Negative control.');
    INSERT INTO exploration_v3.concept_sense_scope VALUES (
      'sense:negative:pending-authority','scope:production-pair');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'CONCEPT_SENSE','sense:negative:pending-authority',
      exploration_v3.aggregate_content_sha(
        'CONCEPT_SENSE','sense:negative:pending-authority'),
      '2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'ISOLATED_ACTIVE_SENSE_PENDING_AUTHORITY_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'ACTIVE_CONCEPT_SENSE_AUTHORITY_ELIGIBILITY_OR_SCOPE_INVALID' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$isolated_active_sense_pending_authority$;

DO $production_sense_synthetic_authority$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.concept_sense VALUES (
      'sense:negative:synthetic-authority','concept:production:1','PRODUCTION',
      'Synthetic-authority bounded sense','INQUIRY_ONLY',false,
      'authority:synthetic-db-v3','1',repeat('0',64),ARRAY[]::text[],
      false,'INELIGIBLE',NULL,'Negative control.');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'PRODUCTION_SENSE_SYNTHETIC_AUTHORITY_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'PRODUCTION_CONCEPT_SENSE_SYNTHETIC_AUTHORITY_FORBIDDEN' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$production_sense_synthetic_authority$;
INSERT INTO exploration_v3.evidence_reference VALUES (
  'evidence:production:pair','PRODUCTION',NULL,NULL,NULL,
  encode(sha256(convert_to('evidence:production:pair','UTF8')),'hex'),
  'Governed database fixture, not a historical activation.',false,true,'TEST_FIXTURE');
INSERT INTO exploration_v3.evidence_locator VALUES (
  'locator:production:pair','evidence:production:pair','fixture://production-pair',
  encode(sha256(convert_to('fixture://production-pair','UTF8')),'hex'),'TEST_FIXTURE');
INSERT INTO exploration_v3.aggregate_seal VALUES (
  'EVIDENCE_REFERENCE','evidence:production:pair',
  exploration_v3.aggregate_content_sha(
    'EVIDENCE_REFERENCE','evidence:production:pair'),
  '2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.association VALUES (
  'association:v3:7ac18df99d0b7f52125f20b4','PRODUCTION','PAIR',2,'UNORDERED',false,
  'NOT_APPLICABLE','7ac18df99d0b7f52125f20b496388099cdaf7a8779bd63256483399f2339edd7',
  '2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.association_revision (
  association_revision_id,association_id,revision_number,scope_id,lifecycle_state,
  support_mode,evidence_complete,same_configuration,conflicts_resolved,
  rights_cleared_for_governed_use,synthesis_complete,uncertainty_status,
  uncertainty_level,uncertainty_activation_policy,uncertainty_rationale,
  activation_decision,all_activation_gates_pass,semantic_version,semantic_sha256,
  presentation_sha256,product_eligible,product_eligibility_disposition,
  product_path,product_ineligibility_reason,qualifications,explicit_non_claims,
  supersedes_association_revision_id,created_at,scope_context_qualifications
) VALUES (
  'association-revision:production:pair:v1','association:v3:7ac18df99d0b7f52125f20b4',1,
  'scope:production-pair','ACTIVE','DIRECT_PAIR',true,true,true,true,true,
  'RESOLVED_BOUNDED','LOW','ALLOWED_BOUNDED','Database product-gate fixture.',
  'ALLOW',true,'1',
  encode(sha256(convert_to('association-revision:production:pair:v1','UTF8')),'hex'),
  encode(sha256(convert_to('presentation:production:pair:v1','UTF8')),'hex'),
  false,'INELIGIBLE',NULL,'No product activation in Round 16B.',ARRAY[]::text[],
  ARRAY['Database fixture is not a historical claim.'],NULL,'2026-08-28T00:00:00Z',
  ARRAY['Database fail-closed production control.']);
INSERT INTO exploration_v3.association_incidence
SELECT 'incidence:production:'||n,'association-revision:production:pair:v1',
  'concept:production:'||n,'sense:production:'||n,NULL,NULL,'scope:production-pair',
  ARRAY[]::text[] FROM generate_series(1,2) n;
INSERT INTO exploration_v3.association_revision_evidence VALUES (
  'association-revision:production:pair:v1','evidence:production:pair','supports');
INSERT INTO exploration_v3.evidence_reference VALUES (
  'evidence:production:resolved-conflict','PRODUCTION',NULL,NULL,NULL,
  encode(sha256(convert_to('evidence:production:resolved-conflict','UTF8')),'hex'),
  'Governed contradictory control requiring exact resolution.',true,true,'TEST_FIXTURE');
INSERT INTO exploration_v3.evidence_locator VALUES (
  'locator:production:resolved-conflict','evidence:production:resolved-conflict',
  'fixture://production-resolved-conflict',
  encode(sha256(convert_to('fixture://production-resolved-conflict','UTF8')),'hex'),
  'TEST_FIXTURE');
INSERT INTO exploration_v3.aggregate_seal VALUES (
  'EVIDENCE_REFERENCE','evidence:production:resolved-conflict',
  exploration_v3.aggregate_content_sha(
    'EVIDENCE_REFERENCE','evidence:production:resolved-conflict'),
  '2026-08-28T00:00:00Z');

DO $unresolved_conflict_block$
DECLARE v_state text; v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.association_revision_evidence VALUES (
      'association-revision:production:pair:v1',
      'evidence:production:resolved-conflict','contradicts');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'UNRESOLVED_CONFLICT_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE,v_message=MESSAGE_TEXT;
    IF v_state <> '23514' OR v_message <> 'ACTIVE_ASSOCIATION_CONFLICT_UNRESOLVED' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$unresolved_conflict_block$;

INSERT INTO exploration_v3.association_revision_evidence VALUES (
  'association-revision:production:pair:v1',
  'evidence:production:resolved-conflict','contradicts');
INSERT INTO exploration_v3.association_conflict_resolution VALUES (
  'conflict-resolution:production:pair:v1',
  'association-revision:production:pair:v1',
  'evidence:production:resolved-conflict','authority:production-db-v3','FINAL',
  'External human authority bounded the contradictory evidence without erasing it.',
  '2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.association_review VALUES (
  'review:production:pair:v1','association-revision:production:pair:v1','FINAL',
  'DIRECT_PAIRWISE_SUPPORT','PASS',true,true,true,0,'authority:production-db-v3','1',
  ARRAY['Database fixture.'],ARRAY['Not a historical activation.'],
  encode(sha256(convert_to('review:production:pair:v1','UTF8')),'hex'),
  '2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.aggregate_seal VALUES (
  'ASSOCIATION_REVISION','association-revision:production:pair:v1',
  exploration_v3.aggregate_content_sha(
    'ASSOCIATION_REVISION','association-revision:production:pair:v1'),
  '2026-08-28T00:00:00Z');
SET CONSTRAINTS ALL IMMEDIATE;
SET CONSTRAINTS ALL DEFERRED;

CREATE FUNCTION pg_temp.stage_production_inactive_pair_v2(p_revision_id text)
RETURNS void LANGUAGE plpgsql AS $function$
BEGIN
  INSERT INTO exploration_v3.association_revision (
    association_revision_id,association_id,revision_number,scope_id,lifecycle_state,
    support_mode,evidence_complete,same_configuration,conflicts_resolved,
    rights_cleared_for_governed_use,synthesis_complete,uncertainty_status,
    uncertainty_level,uncertainty_activation_policy,uncertainty_rationale,
    activation_decision,all_activation_gates_pass,semantic_version,semantic_sha256,
    presentation_sha256,product_eligible,product_eligibility_disposition,
    product_path,product_ineligibility_reason,qualifications,explicit_non_claims,
    supersedes_association_revision_id,created_at,scope_context_qualifications
  ) VALUES (
    p_revision_id,'association:v3:7ac18df99d0b7f52125f20b4',2,
    'scope:production-pair','INACTIVE','NONE',false,true,true,true,false,
    'UNRESOLVED','HIGH','BLOCKS_ACTIVATION','Inactive final-decision negative.',
    'NOT_REQUESTED',false,'2',
    encode(sha256(convert_to(p_revision_id,'UTF8')),'hex'),
    encode(sha256(convert_to('presentation:'||p_revision_id,'UTF8')),'hex'),
    false,'INELIGIBLE',NULL,'Inactive production control.',ARRAY[]::text[],
    ARRAY['No active or product claim.'],'association-revision:production:pair:v1',
    '2026-08-28T00:00:00Z',ARRAY['Database fail-closed production control.']);
  INSERT INTO exploration_v3.association_incidence
  SELECT 'incidence:'||p_revision_id||':'||n,p_revision_id,
    'concept:production:'||n,'sense:production:'||n,NULL,NULL,
    'scope:production-pair',ARRAY[]::text[] FROM generate_series(1,2) n;
END
$function$;

-- A final production conflict resolution cannot use synthetic authority even
-- when the association is inactive and has no positive final disposition.
DO $inactive_final_synthetic_conflict_authority_block$
DECLARE v_message text;
BEGIN
  BEGIN
    PERFORM pg_temp.stage_production_inactive_pair_v2(
      'association-revision:production:synthetic-resolution:v2');
    INSERT INTO exploration_v3.association_revision_evidence VALUES (
      'association-revision:production:synthetic-resolution:v2',
      'evidence:production:resolved-conflict','contradicts');
    INSERT INTO exploration_v3.association_conflict_resolution VALUES (
      'conflict-resolution:production:synthetic-authority:v2',
      'association-revision:production:synthetic-resolution:v2',
      'evidence:production:resolved-conflict','authority:synthetic-db-v3','FINAL',
      'Synthetic authority must never finalize a production resolution.',
      '2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'INACTIVE_FINAL_SYNTHETIC_CONFLICT_AUTHORITY_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'FINAL_CONFLICT_RESOLUTION_AUTHORITY_INVALID' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$inactive_final_synthetic_conflict_authority_block$;

-- Negative and inquiry dispositions remain governed claims: a final
-- production review cannot cite evidence from the synthetic-control realm.
DO $inactive_final_cross_realm_evidence_block$
DECLARE v_message text;
BEGIN
  BEGIN
    PERFORM pg_temp.stage_production_inactive_pair_v2(
      'association-revision:production:cross-realm-evidence:v2');
    INSERT INTO exploration_v3.association_revision_evidence VALUES (
      'association-revision:production:cross-realm-evidence:v2',
      'evidence:synthetic:group','contradicts');
    INSERT INTO exploration_v3.association_review VALUES (
      'review:production:cross-realm-evidence:v2',
      'association-revision:production:cross-realm-evidence:v2','FINAL',
      'HARD_NEGATIVE','FAIL',false,true,true,0,'authority:production-db-v3','2',
      ARRAY['Intentional cross-realm negative.'],ARRAY['No active claim.'],
      encode(sha256(convert_to(
        'review:production:cross-realm-evidence:v2','UTF8')),'hex'),
      '2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'ASSOCIATION_REVISION',
      'association-revision:production:cross-realm-evidence:v2',
      exploration_v3.aggregate_content_sha('ASSOCIATION_REVISION',
        'association-revision:production:cross-realm-evidence:v2'),
      '2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'INACTIVE_FINAL_CROSS_REALM_EVIDENCE_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'FINAL_ASSOCIATION_EVIDENCE_TRACE_INVALID' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$inactive_final_cross_realm_evidence_block$;

-- Even an otherwise final active association cannot become product-visible
-- while one of its exact concept/sense participants is product-ineligible.
DO $product_participant_block$
DECLARE v_state text; v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.association_revision (
      association_revision_id,association_id,revision_number,scope_id,lifecycle_state,
      support_mode,evidence_complete,same_configuration,conflicts_resolved,
      rights_cleared_for_governed_use,synthesis_complete,uncertainty_status,
      uncertainty_level,uncertainty_activation_policy,uncertainty_rationale,
      activation_decision,all_activation_gates_pass,semantic_version,semantic_sha256,
      presentation_sha256,product_eligible,product_eligibility_disposition,
      product_path,product_ineligibility_reason,qualifications,explicit_non_claims,
      supersedes_association_revision_id,created_at
    ) VALUES (
      'association-revision:production:pair:product-leak:v2',
      'association:v3:7ac18df99d0b7f52125f20b4',2,
      'scope:production-pair','ACTIVE','DIRECT_PAIR',true,true,true,true,true,
      'RESOLVED_BOUNDED','LOW','ALLOWED_BOUNDED','Product-participant negative control.',
      'ALLOW',true,'2',
      encode(sha256(convert_to('association-revision:production:pair:product-leak:v2','UTF8')),'hex'),
      encode(sha256(convert_to('presentation:production:pair:product-leak:v2','UTF8')),'hex'),
      true,'ELIGIBLE','/trace/v3/associations/product-leak',NULL,ARRAY[]::text[],
      ARRAY['Database fixture is not a historical claim.'],
      'association-revision:production:pair:v1','2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.association_incidence
    SELECT 'incidence:production:product-leak:'||n,
      'association-revision:production:pair:product-leak:v2',
      'concept:production:'||n,'sense:production:'||n,NULL,NULL,
      'scope:production-pair',ARRAY[]::text[] FROM generate_series(1,2) n;
    INSERT INTO exploration_v3.association_revision_evidence VALUES (
      'association-revision:production:pair:product-leak:v2',
      'evidence:production:pair','supports');
    INSERT INTO exploration_v3.association_review VALUES (
      'review:production:pair:product-leak:v2',
      'association-revision:production:pair:product-leak:v2','FINAL',
      'DIRECT_PAIRWISE_SUPPORT','PASS',true,true,true,0,
      'authority:production-db-v3','2',ARRAY['Product-participant negative control.'],
      ARRAY['Not a historical activation.'],
      encode(sha256(convert_to('review:production:pair:product-leak:v2','UTF8')),'hex'),
      '2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'ASSOCIATION_REVISION','association-revision:production:pair:product-leak:v2',
      exploration_v3.aggregate_content_sha(
        'ASSOCIATION_REVISION','association-revision:production:pair:product-leak:v2'),
      '2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'PRODUCT_PARTICIPANT_LEAK_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE,v_message=MESSAGE_TEXT;
    IF v_state <> '23514'
      OR v_message <> 'ACTIVE_PRODUCT_ASSOCIATION_PARTICIPANT_INELIGIBLE' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$product_participant_block$;

INSERT INTO exploration_v3.composition VALUES (
  'composition:production:pair','PRODUCTION','2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.composition_revision VALUES (
  'composition-revision:production:pair:v1','composition:production:pair',1,'PAIR_EDGE',
  true,'PASS',encode(sha256(convert_to('composition-revision:production:pair:v1','UTF8')),'hex'),
  encode(sha256(convert_to('composition-presentation:production:pair:v1','UTF8')),'hex'),
  false,'INELIGIBLE',NULL,'No product activation in Round 16B.',NULL,
  '2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.composition_node
SELECT 'composition-revision:production:pair:v1','concept:production:'||n
FROM generate_series(1,2) n;
INSERT INTO exploration_v3.association_realization VALUES (
  'realization:production:pair','composition-revision:production:pair:v1',
  'association-revision:production:pair:v1','PAIR_EDGE',
  encode(sha256(convert_to('realization:production:pair','UTF8')),'hex'),
  encode(sha256(convert_to('realization-presentation:production:pair','UTF8')),'hex'),
  'PAIR_EDGE','NEUTRAL');
INSERT INTO exploration_v3.realization_incidence
SELECT 'realization:production:pair','incidence:production:'||n
FROM generate_series(1,2) n;
INSERT INTO exploration_v3.composition_coherence_review VALUES (
  'composition-review:production:pair:v1','composition-revision:production:pair:v1',
  'PRODUCTION','FINAL','authority:production-db-v3','1','PASS',true,true,true,true,0,
  'COHERENT',ARRAY['Database fixture passes semantic coherence but is product-ineligible.'],
  encode(sha256(convert_to('composition-review:production:pair:v1','UTF8')),'hex'),
  '2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.composition_review_realization VALUES (
  'composition-review:production:pair:v1','realization:production:pair');
INSERT INTO exploration_v3.aggregate_seal VALUES (
  'COMPOSITION_REVISION','composition-revision:production:pair:v1',
  exploration_v3.aggregate_content_sha(
    'COMPOSITION_REVISION','composition-revision:production:pair:v1'),
  '2026-08-28T00:00:00Z');
INSERT INTO exploration_v3.navigation_state VALUES (
  'state:production:pair','PRODUCTION','composition-revision:production:pair:v1',
  'nav:production:concept:2',true,
  encode(sha256(convert_to('state:production:pair','UTF8')),'hex'),
  encode(sha256(convert_to('state-presentation:production:pair','UTF8')),'hex'),
  'FOCUS','TEST');
INSERT INTO exploration_v3.navigation_node VALUES
  ('state:production:pair','nav:production:concept:1','CONCEPT','concept:production:1',NULL),
  ('state:production:pair','nav:production:association','ASSOCIATION',NULL,
    'association-revision:production:pair:v1'),
  ('state:production:pair','nav:production:concept:2','CONCEPT','concept:production:2',NULL);
INSERT INTO exploration_v3.navigation_path_step VALUES
  ('state:production:pair',0,'nav:production:concept:1','incidence:production:1',
    'nav:production:association'),
  ('state:production:pair',1,'nav:production:association','incidence:production:2',
    'nav:production:concept:2');
INSERT INTO exploration_v3.aggregate_seal VALUES (
  'NAVIGATION_STATE','state:production:pair',
  exploration_v3.aggregate_content_sha('NAVIGATION_STATE','state:production:pair'),
  '2026-08-28T00:00:00Z');

DO $partial_transition_trace_block$
DECLARE v_state text; v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.interaction_transition VALUES (
      'transition:production:partial-trace','PRODUCTION','state:production:pair',
      'state:production:pair','MOVE_FOCUS',NULL,
      'association-revision:production:pair:v1',NULL,true,
      encode(sha256(convert_to('transition:production:partial-trace','UTF8')),'hex'),
      false,'INELIGIBLE',NULL,'Partial association traces are forbidden.');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'PARTIAL_TRANSITION_TRACE_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE,v_message=MESSAGE_TEXT;
    IF v_state <> '23514' OR v_message <> 'TRANSITION_TRACE_PARTIAL' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$partial_transition_trace_block$;

INSERT INTO exploration_v3.interaction_transition VALUES (
  'transition:production:ineligible','PRODUCTION','state:production:pair',
  'state:production:pair','FOLLOW_INCIDENCE','incidence:production:1',
  'association-revision:production:pair:v1','realization:production:pair',false,
  encode(sha256(convert_to('transition:production:ineligible','UTF8')),'hex'),
  false,'INELIGIBLE',NULL,'Referenced composition is not product eligible.');
INSERT INTO exploration_v3.exploration_workflow VALUES (
  'workflow:production:ineligible','PRODUCTION','state:production:pair','FOLLOW_INCIDENCE',
  true,encode(sha256(convert_to('workflow:production:ineligible','UTF8')),'hex'),
  false,'INELIGIBLE',NULL,'Dependencies are not product eligible.');
INSERT INTO exploration_v3.workflow_state VALUES (
  'workflow:production:ineligible','state:production:pair');
INSERT INTO exploration_v3.workflow_association_revision VALUES (
  'workflow:production:ineligible','association-revision:production:pair:v1');
INSERT INTO exploration_v3.workflow_association_realization VALUES (
  'workflow:production:ineligible','realization:production:pair');
INSERT INTO exploration_v3.workflow_transition VALUES (
  'workflow:production:ineligible','transition:production:ineligible');
INSERT INTO exploration_v3.aggregate_seal VALUES (
  'WORKFLOW','workflow:production:ineligible',
  exploration_v3.aggregate_content_sha('WORKFLOW','workflow:production:ineligible'),
  '2026-08-28T00:00:00Z');
SET CONSTRAINTS ALL IMMEDIATE;
SET CONSTRAINTS ALL DEFERRED;

-- Every reviewed/hash-bound aggregate rejects child membership changes after
-- its explicit seal.  The INSERT guard fires before duplicate/FK checks.
DO $sealed_membership_blocks$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.association_revision_evidence VALUES (
      'association-revision:synthetic:sparse-three:v1',
      'evidence:synthetic:group','contextualises');
    RAISE EXCEPTION 'SEALED_ASSOCIATION_CHILD_INSERT_NOT_REJECTED';
  EXCEPTION WHEN object_not_in_prerequisite_state THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'SEALED_AGGREGATE_CHILD_INSERT_FORBIDDEN' THEN RAISE; END IF;
  END;
  BEGIN
    INSERT INTO exploration_v3.composition_node VALUES (
      'composition-revision:synthetic:sparse-three:v1','concept:synthetic:1');
    RAISE EXCEPTION 'SEALED_COMPOSITION_CHILD_INSERT_NOT_REJECTED';
  EXCEPTION WHEN object_not_in_prerequisite_state THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'SEALED_AGGREGATE_CHILD_INSERT_FORBIDDEN' THEN RAISE; END IF;
  END;
  BEGIN
    INSERT INTO exploration_v3.navigation_node VALUES (
      'state:synthetic:sparse-three','nav:synthetic:concept:2','CONCEPT',
      'concept:synthetic:2',NULL);
    RAISE EXCEPTION 'SEALED_NAVIGATION_CHILD_INSERT_NOT_REJECTED';
  EXCEPTION WHEN object_not_in_prerequisite_state THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'SEALED_AGGREGATE_CHILD_INSERT_FORBIDDEN' THEN RAISE; END IF;
  END;
  BEGIN
    INSERT INTO exploration_v3.workflow_state VALUES (
      'workflow:synthetic:sparse-three','state:synthetic:sparse-three');
    RAISE EXCEPTION 'SEALED_WORKFLOW_CHILD_INSERT_NOT_REJECTED';
  EXCEPTION WHEN object_not_in_prerequisite_state THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'SEALED_AGGREGATE_CHILD_INSERT_FORBIDDEN' THEN RAISE; END IF;
  END;
  BEGIN
    INSERT INTO exploration_v3.export_projection_preservation VALUES (
      'export:synthetic:sparse-three','association-revision:synthetic:sparse-three:v1',
      'realization:synthetic:sparse-three','NONE','HYPEREDGE_HUB');
    RAISE EXCEPTION 'SEALED_EXPORT_CHILD_INSERT_NOT_REJECTED';
  EXCEPTION WHEN object_not_in_prerequisite_state THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'SEALED_AGGREGATE_CHILD_INSERT_FORBIDDEN' THEN RAISE; END IF;
  END;
END
$sealed_membership_blocks$;

SELECT pg_temp.assert_true(
  position('acquire_aggregate_membership_lock' in pg_get_functiondef(
    'exploration_v3.enforce_aggregate_seal_insert()'::regprocedure)) > 0
  AND position('acquire_aggregate_membership_lock' in pg_get_functiondef(
    'exploration_v3.reject_sealed_child_insert()'::regprocedure)) > 0,
  'seal and every governed child append share the same fail-fast membership lock primitive');

DO $product_transition_block$
DECLARE v_state text; v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.interaction_transition VALUES (
      'transition:production:blocked','PRODUCTION','state:production:pair',
      'state:production:pair','FOLLOW_INCIDENCE','incidence:production:1',
      'association-revision:production:pair:v1','realization:production:pair',false,
      repeat('1',64),true,'ELIGIBLE','/trace/v3/transitions/blocked',NULL);
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'PRODUCT_TRANSITION_LEAK_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE,v_message=MESSAGE_TEXT;
    IF v_state <> '23514' OR v_message <> 'PRODUCT_TRANSITION_COMPOSITION_INELIGIBLE' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$product_transition_block$;

DO $product_workflow_block$
DECLARE v_state text; v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.exploration_workflow VALUES (
      'workflow:production:blocked','PRODUCTION','state:production:pair','FOLLOW_INCIDENCE',
      true,repeat('2',64),true,'ELIGIBLE','/trace/v3/workflows/blocked',NULL);
    INSERT INTO exploration_v3.workflow_state VALUES (
      'workflow:production:blocked','state:production:pair');
    INSERT INTO exploration_v3.workflow_association_revision VALUES (
      'workflow:production:blocked','association-revision:production:pair:v1');
    INSERT INTO exploration_v3.workflow_association_realization VALUES (
      'workflow:production:blocked','realization:production:pair');
    INSERT INTO exploration_v3.workflow_transition VALUES (
      'workflow:production:blocked','transition:production:ineligible');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'WORKFLOW','workflow:production:blocked',
      exploration_v3.aggregate_content_sha('WORKFLOW','workflow:production:blocked'),
      '2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'PRODUCT_WORKFLOW_LEAK_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE,v_message=MESSAGE_TEXT;
    IF v_state <> '23514' OR v_message <> 'PRODUCT_WORKFLOW_DEPENDENCY_INELIGIBLE' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$product_workflow_block$;

DO $product_export_block$
DECLARE v_state text; v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.export_manifest VALUES (
      'export:production:blocked','PRODUCTION','workflow:production:ineligible',
      'state:production:pair','composition-revision:production:pair:v1',repeat('3',64),
      repeat('4',64),'TRACE_V3_JSON','NEUTRAL',true,true,'ELIGIBLE',
      '/trace/v3/exports/blocked',NULL);
    INSERT INTO exploration_v3.export_projection_preservation VALUES (
      'export:production:blocked','association-revision:production:pair:v1',
      'realization:production:pair','NOT_APPLICABLE','PAIR_EDGE');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'EXPORT','export:production:blocked',
      exploration_v3.aggregate_content_sha('EXPORT','export:production:blocked'),
      '2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'PRODUCT_EXPORT_LEAK_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE,v_message=MESSAGE_TEXT;
    IF v_state <> '23514' OR v_message <> 'PRODUCT_EXPORT_DEPENDENCY_INELIGIBLE' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$product_export_block$;

DO $association_cross_parent_lineage_block$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.association VALUES (
      'association:synthetic:cross-parent','SYNTHETIC_CONTROL','HIGHER_ORDER',3,
      'UNORDERED',false,'NONE',
      encode(sha256(convert_to('association:synthetic:cross-parent','UTF8')),'hex'),
      '2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.association_revision (
      association_revision_id,association_id,revision_number,scope_id,lifecycle_state,
      support_mode,evidence_complete,same_configuration,conflicts_resolved,
      rights_cleared_for_governed_use,synthesis_complete,uncertainty_status,
      uncertainty_level,uncertainty_activation_policy,uncertainty_rationale,
      activation_decision,all_activation_gates_pass,semantic_version,semantic_sha256,
      presentation_sha256,product_eligible,product_eligibility_disposition,
      product_path,product_ineligibility_reason,qualifications,explicit_non_claims,
      supersedes_association_revision_id,created_at
    ) VALUES (
      'association-revision:synthetic:cross-parent:v2',
      'association:synthetic:cross-parent',2,'scope:synthetic-sparse-three',
      'INQUIRY_ONLY','NONE',false,true,true,true,false,'UNRESOLVED','HIGH',
      'BLOCKS_ACTIVATION','Cross-parent lineage negative.','NOT_REQUESTED',false,'2',
      encode(sha256(convert_to('association-revision:synthetic:cross-parent:v2','UTF8')),'hex'),
      encode(sha256(convert_to('presentation:synthetic:cross-parent:v2','UTF8')),'hex'),
      false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic negative control.',ARRAY[]::text[],
      ARRAY['No claim.'],'association-revision:synthetic:sparse-three:v1',
      '2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'ASSOCIATION_CROSS_PARENT_LINEAGE_NOT_REJECTED';
  EXCEPTION
    WHEN check_violation THEN
      GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
      IF v_message <> 'ASSOCIATION_REVISION_LINEAGE_INVALID' THEN RAISE; END IF;
    WHEN foreign_key_violation THEN NULL;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$association_cross_parent_lineage_block$;

DO $association_nonmonotonic_lineage_block$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.association_revision (
      association_revision_id,association_id,revision_number,scope_id,lifecycle_state,
      support_mode,evidence_complete,same_configuration,conflicts_resolved,
      rights_cleared_for_governed_use,synthesis_complete,uncertainty_status,
      uncertainty_level,uncertainty_activation_policy,uncertainty_rationale,
      activation_decision,all_activation_gates_pass,semantic_version,semantic_sha256,
      presentation_sha256,product_eligible,product_eligibility_disposition,
      product_path,product_ineligibility_reason,qualifications,explicit_non_claims,
      supersedes_association_revision_id,created_at
    ) VALUES (
      'association-revision:synthetic:sparse-three:v3',
      'association:v3:d9a68bf6518292a0495c3196',3,'scope:synthetic-sparse-three',
      'INQUIRY_ONLY','NONE',false,true,true,true,false,'UNRESOLVED','HIGH',
      'BLOCKS_ACTIVATION','Nonmonotonic lineage negative.','NOT_REQUESTED',false,'3',
      encode(sha256(convert_to('association-revision:synthetic:sparse-three:v3','UTF8')),'hex'),
      encode(sha256(convert_to('presentation:synthetic:sparse-three:v3','UTF8')),'hex'),
      false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic negative control.',ARRAY[]::text[],
      ARRAY['No claim.'],'association-revision:synthetic:sparse-three:v1',
      '2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'ASSOCIATION_NONMONOTONIC_LINEAGE_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'ASSOCIATION_REVISION_LINEAGE_INVALID' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$association_nonmonotonic_lineage_block$;

DO $composition_cross_parent_lineage_block$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.composition VALUES (
      'composition:synthetic:cross-parent','SYNTHETIC_CONTROL','2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.composition_revision VALUES (
      'composition-revision:synthetic:cross-parent:v2',
      'composition:synthetic:cross-parent',2,'HYPEREDGE_HUB',true,'PASS',
      encode(sha256(convert_to('composition-revision:synthetic:cross-parent:v2','UTF8')),'hex'),
      encode(sha256(convert_to('composition-presentation:synthetic:cross-parent:v2','UTF8')),'hex'),
      false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic negative control.',
      'composition-revision:synthetic:sparse-three:v1','2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'COMPOSITION_CROSS_PARENT_LINEAGE_NOT_REJECTED';
  EXCEPTION
    WHEN check_violation THEN
      GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
      IF v_message <> 'COMPOSITION_REVISION_LINEAGE_INVALID' THEN RAISE; END IF;
    WHEN foreign_key_violation THEN NULL;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$composition_cross_parent_lineage_block$;

DO $composition_nonmonotonic_lineage_block$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.composition_revision VALUES (
      'composition-revision:synthetic:sparse-three:v3',
      'composition:synthetic:sparse-three',3,'HYPEREDGE_HUB',true,'PASS',
      encode(sha256(convert_to('composition-revision:synthetic:sparse-three:v3','UTF8')),'hex'),
      encode(sha256(convert_to('composition-presentation:synthetic:sparse-three:v3','UTF8')),'hex'),
      false,'NOT_APPLICABLE_SYNTHETIC',NULL,'Synthetic negative control.',
      'composition-revision:synthetic:sparse-three:v1','2026-08-28T00:00:00Z');
    SET CONSTRAINTS ALL IMMEDIATE;
    RAISE EXCEPTION 'COMPOSITION_NONMONOTONIC_LINEAGE_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'COMPOSITION_REVISION_LINEAGE_INVALID' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$composition_nonmonotonic_lineage_block$;

-- A transaction-local production fixture proves every positive API projection
-- with exact rows and child traces.  The explicit exception rolls the fixture
-- back before the round's zero-production boundary assertion.
DO $positive_api_and_current_head_fixture$
DECLARE v_message text;
BEGIN
  BEGIN
    INSERT INTO exploration_v3.governed_authority VALUES (
      'authority:positive-api','EXTERNAL_HUMAN_REVIEW','FINAL','1',
      encode(sha256(convert_to('authority:positive-api','UTF8')),'hex'),
      '2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.governed_scope VALUES (
      'scope:positive-api','PRODUCTION',ARRAY['case:positive-api'],'1919','1933',
      ARRAY['EUROPE'],ARRAY['INSTITUTION:POSITIVE'],ARRAY['ACTOR:POSITIVE'],
      ARRAY['MECHANISM:POSITIVE'],ARRAY['Transaction-local API fixture.'],
      encode(sha256(convert_to('scope:positive-api','UTF8')),'hex'));
    INSERT INTO exploration_v3.concept
    SELECT 'concept:positive:'||n,'PRODUCTION','Positive concept '||n,
      'ACTIVE',true,'authority:positive-api','1',
      encode(sha256(convert_to('concept:positive:'||n,'UTF8')),'hex'),
      true,'ELIGIBLE','/trace/v3/concepts/'||n,NULL
    FROM generate_series(1,3) n;
    INSERT INTO exploration_v3.concept_sense
    SELECT 'sense:positive:'||n,'concept:positive:'||n,'PRODUCTION',
      'Positive bounded sense '||n,'ACTIVE',true,'authority:positive-api','1',
      encode(sha256(convert_to('sense:positive:'||n,'UTF8')),'hex'),ARRAY[]::text[],
      true,'ELIGIBLE','/trace/v3/senses/'||n,NULL
    FROM generate_series(1,3) n;
    INSERT INTO exploration_v3.concept_sense_scope
    SELECT 'sense:positive:'||n,'scope:positive-api' FROM generate_series(1,3) n;
    INSERT INTO exploration_v3.aggregate_seal
    SELECT 'CONCEPT_SENSE',sense_id,
      exploration_v3.aggregate_content_sha('CONCEPT_SENSE',sense_id),
      '2026-08-28T00:00:00Z'
    FROM exploration_v3.concept_sense WHERE sense_id LIKE 'sense:positive:%';
    INSERT INTO exploration_v3.evidence_reference VALUES (
      'evidence:positive-api','PRODUCTION',NULL,NULL,NULL,
      encode(sha256(convert_to('evidence:positive-api','UTF8')),'hex'),
      'Rights-cleared transaction-local evidence.',false,true,'TEST_FIXTURE');
    INSERT INTO exploration_v3.evidence_locator VALUES (
      'locator:positive-api','evidence:positive-api','fixture://positive-api',
      encode(sha256(convert_to('fixture://positive-api','UTF8')),'hex'),'TEST_FIXTURE');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'EVIDENCE_REFERENCE','evidence:positive-api',
      exploration_v3.aggregate_content_sha(
        'EVIDENCE_REFERENCE','evidence:positive-api'),'2026-08-28T00:00:00Z');

    INSERT INTO exploration_v3.association VALUES (
      'association:v3:c8d1a499b5f8fe1ed4541329','PRODUCTION','PAIR',2,
      'UNORDERED',false,'NOT_APPLICABLE',
      'c8d1a499b5f8fe1ed4541329c0392a3d6217a674fd34d0ecf00012c25aea6fc2',
      '2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.association_revision VALUES (
      'association-revision:positive:pair:v1',
      'association:v3:c8d1a499b5f8fe1ed4541329',1,'scope:positive-api','ACTIVE',
      'DIRECT_PAIR',true,true,true,true,true,'RESOLVED_BOUNDED','LOW',
      'ALLOWED_BOUNDED','Positive pair fixture.','ALLOW',true,'1',
      encode(sha256(convert_to('association-revision:positive:pair:v1','UTF8')),'hex'),
      encode(sha256(convert_to('presentation:positive:pair:v1','UTF8')),'hex'),
      true,'ELIGIBLE','/trace/v3/associations/positive-pair',NULL,ARRAY[]::text[],
      ARRAY['No causal, directional, chronological, or hierarchical claim.'],
      NULL,'2026-08-28T00:00:00Z',ARRAY['Transaction-local API fixture.']);
    INSERT INTO exploration_v3.association_incidence VALUES
      ('incidence:positive:pair:1','association-revision:positive:pair:v1',
        'concept:positive:1','sense:positive:1',NULL,NULL,'scope:positive-api',ARRAY[]::text[]),
      ('incidence:positive:pair:2','association-revision:positive:pair:v1',
        'concept:positive:2','sense:positive:2',NULL,NULL,'scope:positive-api',ARRAY[]::text[]);
    INSERT INTO exploration_v3.association_revision_evidence VALUES (
      'association-revision:positive:pair:v1','evidence:positive-api','supports');
    INSERT INTO exploration_v3.association_review VALUES (
      'review:positive:pair:v1','association-revision:positive:pair:v1','FINAL',
      'DIRECT_PAIRWISE_SUPPORT','PASS',true,true,true,0,'authority:positive-api','1',
      ARRAY['Transaction-local positive fixture.'],ARRAY['No production data imported.'],
      encode(sha256(convert_to('review:positive:pair:v1','UTF8')),'hex'),
      '2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'ASSOCIATION_REVISION','association-revision:positive:pair:v1',
      exploration_v3.aggregate_content_sha(
        'ASSOCIATION_REVISION','association-revision:positive:pair:v1'),
      '2026-08-28T00:00:00Z');

    INSERT INTO exploration_v3.association VALUES (
      'association:v3:9c7c470b1bf49a8cc27c0902','PRODUCTION','HIGHER_ORDER',3,
      'UNORDERED',false,'NONE',
      '9c7c470b1bf49a8cc27c0902aa32eda228b9b01a3bf343253c165f65e01db655',
      '2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.association_revision VALUES (
      'association-revision:positive:higher:v1',
      'association:v3:9c7c470b1bf49a8cc27c0902',1,'scope:positive-api','ACTIVE',
      'COHERENT_COMPOSITE',true,true,true,true,true,'RESOLVED_BOUNDED','LOW',
      'ALLOWED_BOUNDED','Positive higher-order fixture.','ALLOW',true,'1',
      encode(sha256(convert_to('association-revision:positive:higher:v1','UTF8')),'hex'),
      encode(sha256(convert_to('presentation:positive:higher:v1','UTF8')),'hex'),
      true,'ELIGIBLE','/trace/v3/associations/positive-higher',NULL,ARRAY[]::text[],
      ARRAY['No implicit projection beyond the explicit pair link.'],
      NULL,'2026-08-28T00:00:00Z',ARRAY['Transaction-local API fixture.']);
    INSERT INTO exploration_v3.association_incidence
    SELECT 'incidence:positive:higher:'||n,'association-revision:positive:higher:v1',
      'concept:positive:'||n,'sense:positive:'||n,NULL,NULL,'scope:positive-api',
      ARRAY[]::text[] FROM generate_series(1,3) n;
    INSERT INTO exploration_v3.association_revision_evidence VALUES (
      'association-revision:positive:higher:v1','evidence:positive-api','supports');
    INSERT INTO exploration_v3.association_synthesis_step VALUES (
      'association-revision:positive:higher:v1',0,
      'The exact source bundle supports one coherent bounded configuration.',true);
    INSERT INTO exploration_v3.association_synthesis_step_evidence VALUES (
      'association-revision:positive:higher:v1',0,'evidence:positive-api');
    INSERT INTO exploration_v3.internal_pair_link VALUES (
      'association-revision:positive:higher:v1','association-revision:positive:pair:v1',
      'incidence:positive:higher:1','incidence:positive:higher:2',
      'incidence:positive:pair:1','incidence:positive:pair:2');
    INSERT INTO exploration_v3.association_review VALUES (
      'review:positive:higher:v1','association-revision:positive:higher:v1','FINAL',
      'COHERENT_COMPOSITE_SUPPORT','PASS',true,true,true,0,'authority:positive-api','1',
      ARRAY['Transaction-local positive fixture.'],ARRAY['No implicit pair projection.'],
      encode(sha256(convert_to('review:positive:higher:v1','UTF8')),'hex'),
      '2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'ASSOCIATION_REVISION','association-revision:positive:higher:v1',
      exploration_v3.aggregate_content_sha(
        'ASSOCIATION_REVISION','association-revision:positive:higher:v1'),
      '2026-08-28T00:00:00Z');

    INSERT INTO exploration_v3.composition VALUES (
      'composition:positive','PRODUCTION','2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.composition_revision VALUES (
      'composition-revision:positive:v1','composition:positive',1,
      'HYPEREDGE_WITH_EXPLICIT_PAIR',true,'PASS',
      encode(sha256(convert_to('composition-revision:positive:v1','UTF8')),'hex'),
      encode(sha256(convert_to('composition-presentation:positive:v1','UTF8')),'hex'),
      true,'ELIGIBLE','/trace/v3/compositions/positive',NULL,NULL,
      '2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.composition_node
    SELECT 'composition-revision:positive:v1','concept:positive:'||n
    FROM generate_series(1,3) n;
    INSERT INTO exploration_v3.association_realization VALUES
      ('realization:positive:pair','composition-revision:positive:v1',
        'association-revision:positive:pair:v1','PAIR_EDGE',repeat('a',64),repeat('b',64),
        'PAIR_EDGE','POSITIVE'),
      ('realization:positive:higher','composition-revision:positive:v1',
        'association-revision:positive:higher:v1','HYPEREDGE_HUB',repeat('c',64),repeat('d',64),
        'HYPEREDGE_HUB','POSITIVE');
    INSERT INTO exploration_v3.realization_incidence VALUES
      ('realization:positive:pair','incidence:positive:pair:1'),
      ('realization:positive:pair','incidence:positive:pair:2'),
      ('realization:positive:higher','incidence:positive:higher:1'),
      ('realization:positive:higher','incidence:positive:higher:2'),
      ('realization:positive:higher','incidence:positive:higher:3');
    INSERT INTO exploration_v3.composition_coherence_review VALUES (
      'composition-review:positive:v1','composition-revision:positive:v1','PRODUCTION',
      'FINAL','authority:positive-api','1','PASS',true,true,true,true,0,'COHERENT',
      ARRAY['Exact positive API fixture.'],repeat('e',64),'2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.composition_review_realization VALUES
      ('composition-review:positive:v1','realization:positive:pair'),
      ('composition-review:positive:v1','realization:positive:higher');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'COMPOSITION_REVISION','composition-revision:positive:v1',
      exploration_v3.aggregate_content_sha(
        'COMPOSITION_REVISION','composition-revision:positive:v1'),
      '2026-08-28T00:00:00Z');

    INSERT INTO exploration_v3.navigation_state VALUES (
      'state:positive','PRODUCTION','composition-revision:positive:v1',
      'nav:positive:concept:3',true,repeat('f',64),repeat('0',64),'FOCUS','TEST');
    INSERT INTO exploration_v3.navigation_node VALUES
      ('state:positive','nav:positive:concept:1','CONCEPT','concept:positive:1',NULL),
      ('state:positive','nav:positive:association','ASSOCIATION',NULL,
        'association-revision:positive:higher:v1'),
      ('state:positive','nav:positive:concept:3','CONCEPT','concept:positive:3',NULL);
    INSERT INTO exploration_v3.navigation_path_step VALUES
      ('state:positive',0,'nav:positive:concept:1','incidence:positive:higher:1',
        'nav:positive:association'),
      ('state:positive',1,'nav:positive:association','incidence:positive:higher:3',
        'nav:positive:concept:3');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'NAVIGATION_STATE','state:positive',
      exploration_v3.aggregate_content_sha('NAVIGATION_STATE','state:positive'),
      '2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.interaction_transition VALUES (
      'transition:positive','PRODUCTION','state:positive','state:positive',
      'FOLLOW_INCIDENCE','incidence:positive:higher:1',
      'association-revision:positive:higher:v1','realization:positive:higher',false,
      repeat('1',64),true,'ELIGIBLE','/trace/v3/transitions/positive',NULL);
    INSERT INTO exploration_v3.exploration_workflow VALUES (
      'workflow:positive','PRODUCTION','state:positive','FOLLOW_INCIDENCE',true,
      repeat('2',64),true,'ELIGIBLE','/trace/v3/workflows/positive',NULL);
    INSERT INTO exploration_v3.workflow_state VALUES ('workflow:positive','state:positive');
    INSERT INTO exploration_v3.workflow_association_revision VALUES
      ('workflow:positive','association-revision:positive:pair:v1'),
      ('workflow:positive','association-revision:positive:higher:v1');
    INSERT INTO exploration_v3.workflow_association_realization VALUES
      ('workflow:positive','realization:positive:pair'),
      ('workflow:positive','realization:positive:higher');
    INSERT INTO exploration_v3.workflow_transition VALUES (
      'workflow:positive','transition:positive');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'WORKFLOW','workflow:positive',
      exploration_v3.aggregate_content_sha('WORKFLOW','workflow:positive'),
      '2026-08-28T00:00:00Z');
    INSERT INTO exploration_v3.export_manifest VALUES (
      'export:positive','PRODUCTION','workflow:positive','state:positive',
      'composition-revision:positive:v1',repeat('3',64),repeat('4',64),
      'TRACE_V3_JSON','NEUTRAL',true,true,'ELIGIBLE','/trace/v3/exports/positive',NULL);
    INSERT INTO exploration_v3.export_projection_preservation VALUES
      ('export:positive','association-revision:positive:pair:v1',
        'realization:positive:pair','NOT_APPLICABLE','PAIR_EDGE'),
      ('export:positive','association-revision:positive:higher:v1',
        'realization:positive:higher','NONE','HYPEREDGE_HUB');
    INSERT INTO exploration_v3.aggregate_seal VALUES (
      'EXPORT','export:positive',
      exploration_v3.aggregate_content_sha('EXPORT','export:positive'),
      '2026-08-28T00:00:00Z');

    SET CONSTRAINTS ALL IMMEDIATE;
    PERFORM pg_temp.assert_true(
      (SELECT array_agg(association_revision_id ORDER BY association_revision_id)
        FROM api_v3.active_association) = ARRAY[
          'association-revision:positive:higher:v1',
          'association-revision:positive:pair:v1']
      AND NOT EXISTS (SELECT 1 FROM api_v3.active_association
        WHERE scope_context_qualifications <>
          ARRAY['Transaction-local API fixture.'])
      AND (SELECT array_agg(scope_id) FROM api_v3.active_scope) = ARRAY['scope:positive-api']
      AND (SELECT array_agg(concept_id ORDER BY concept_id) FROM api_v3.active_concept) =
        ARRAY['concept:positive:1','concept:positive:2','concept:positive:3']
      AND (SELECT array_agg(sense_id ORDER BY sense_id) FROM api_v3.active_concept_sense) =
        ARRAY['sense:positive:1','sense:positive:2','sense:positive:3']
      AND (SELECT array_agg(format('%s|%s|%s|%s|%s',association_revision_id,
          incidence_id,concept_id,sense_id,participant_scope_id) ORDER BY incidence_id)
        FROM api_v3.association_incidence) = ARRAY[
          'association-revision:positive:higher:v1|incidence:positive:higher:1|concept:positive:1|sense:positive:1|scope:positive-api',
          'association-revision:positive:higher:v1|incidence:positive:higher:2|concept:positive:2|sense:positive:2|scope:positive-api',
          'association-revision:positive:higher:v1|incidence:positive:higher:3|concept:positive:3|sense:positive:3|scope:positive-api',
          'association-revision:positive:pair:v1|incidence:positive:pair:1|concept:positive:1|sense:positive:1|scope:positive-api',
          'association-revision:positive:pair:v1|incidence:positive:pair:2|concept:positive:2|sense:positive:2|scope:positive-api']
      AND (SELECT array_agg(format('%s|%s|%s',association_revision_id,
          evidence_reference_id,locator_id) ORDER BY association_revision_id)
        FROM api_v3.association_evidence_locator) = ARRAY[
          'association-revision:positive:higher:v1|evidence:positive-api|locator:positive-api',
          'association-revision:positive:pair:v1|evidence:positive-api|locator:positive-api']
      AND (SELECT array_agg(format('%s|%s|%s|%s',association_revision_id,
          step_ordinal,synthesis_statement,bridge_supported) ORDER BY step_ordinal)
        FROM api_v3.active_association_synthesis_step) = ARRAY[
          'association-revision:positive:higher:v1|0|The exact source bundle supports one coherent bounded configuration.|t']
      AND (SELECT array_agg(format('%s|%s|%s',association_revision_id,
          step_ordinal,evidence_reference_id) ORDER BY step_ordinal)
        FROM api_v3.active_association_synthesis_step_evidence) = ARRAY[
          'association-revision:positive:higher:v1|0|evidence:positive-api']
      AND (SELECT array_agg(format('%s|%s|%s|%s|%s|%s',higher_order_revision_id,
          pair_revision_id,higher_incidence_a,higher_incidence_b,
          pair_incidence_a,pair_incidence_b))
        FROM api_v3.active_association_internal_pair_link) = ARRAY[
          'association-revision:positive:higher:v1|association-revision:positive:pair:v1|incidence:positive:higher:1|incidence:positive:higher:2|incidence:positive:pair:1|incidence:positive:pair:2']
      AND (SELECT array_agg(composition_revision_id) FROM api_v3.product_composition) =
        ARRAY['composition-revision:positive:v1']
      AND (SELECT array_agg(format('%s|%s|%s',association_realization_id,
          association_revision_id,realization_kind) ORDER BY association_realization_id)
        FROM api_v3.product_composition_realization) = ARRAY[
          'realization:positive:higher|association-revision:positive:higher:v1|HYPEREDGE_HUB',
          'realization:positive:pair|association-revision:positive:pair:v1|PAIR_EDGE']
      AND (SELECT array_agg(format('%s|%s|%s',association_realization_id,
          association_revision_id,incidence_id)
          ORDER BY association_realization_id,incidence_id)
        FROM api_v3.product_composition_realization_incidence) = ARRAY[
          'realization:positive:higher|association-revision:positive:higher:v1|incidence:positive:higher:1',
          'realization:positive:higher|association-revision:positive:higher:v1|incidence:positive:higher:2',
          'realization:positive:higher|association-revision:positive:higher:v1|incidence:positive:higher:3',
          'realization:positive:pair|association-revision:positive:pair:v1|incidence:positive:pair:1',
          'realization:positive:pair|association-revision:positive:pair:v1|incidence:positive:pair:2']
      AND (SELECT array_agg(format('%s|%s|%s',composition_revision_id,
          composition_coherence_review_id,decision))
        FROM api_v3.product_composition_coherence_review) = ARRAY[
          'composition-revision:positive:v1|composition-review:positive:v1|COHERENT']
      AND (SELECT array_agg(state_id) FROM api_v3.product_navigation_state) = ARRAY['state:positive']
      AND (SELECT array_agg(format('%s|%s|%s|%s',navigation_node_id,node_kind,
          coalesce(concept_id,''),coalesce(association_revision_id,''))
          ORDER BY navigation_node_id) FROM api_v3.product_navigation_node) = ARRAY[
          'nav:positive:association|ASSOCIATION||association-revision:positive:higher:v1',
          'nav:positive:concept:1|CONCEPT|concept:positive:1|',
          'nav:positive:concept:3|CONCEPT|concept:positive:3|']
      AND (SELECT array_agg(format('%s|%s|%s|%s',step_ordinal,
          from_navigation_node_id,incidence_id,to_navigation_node_id) ORDER BY step_ordinal)
        FROM api_v3.product_navigation_path_step) = ARRAY[
          '0|nav:positive:concept:1|incidence:positive:higher:1|nav:positive:association',
          '1|nav:positive:association|incidence:positive:higher:3|nav:positive:concept:3']
      AND (SELECT array_agg(format('%s|%s|%s|%s',transition_id,incidence_id,
          association_revision_id,association_realization_id))
        FROM api_v3.product_transition) = ARRAY[
          'transition:positive|incidence:positive:higher:1|association-revision:positive:higher:v1|realization:positive:higher']
      AND (SELECT array_agg(workflow_id) FROM api_v3.product_workflow) = ARRAY['workflow:positive']
      AND (SELECT array_agg(format('%s|%s',workflow_id,state_id))
        FROM api_v3.product_workflow_state) = ARRAY['workflow:positive|state:positive']
      AND (SELECT array_agg(format('%s|%s',workflow_id,association_revision_id)
          ORDER BY association_revision_id)
        FROM api_v3.product_workflow_association_revision) = ARRAY[
          'workflow:positive|association-revision:positive:higher:v1',
          'workflow:positive|association-revision:positive:pair:v1']
      AND (SELECT array_agg(format('%s|%s|%s',workflow_id,
          association_realization_id,association_revision_id)
          ORDER BY association_realization_id)
        FROM api_v3.product_workflow_association_realization) = ARRAY[
          'workflow:positive|realization:positive:higher|association-revision:positive:higher:v1',
          'workflow:positive|realization:positive:pair|association-revision:positive:pair:v1']
      AND (SELECT array_agg(format('%s|%s',workflow_id,transition_id))
        FROM api_v3.product_workflow_transition) = ARRAY[
          'workflow:positive|transition:positive']
      AND (SELECT array_agg(export_id) FROM api_v3.product_export) = ARRAY['export:positive']
      AND (SELECT array_agg(format('%s|%s|%s|%s',export_id,
          association_revision_id,association_realization_id,realization_kind)
          ORDER BY association_realization_id)
        FROM api_v3.product_export_projection_preservation) = ARRAY[
          'export:positive|association-revision:positive:higher:v1|realization:positive:higher|HYPEREDGE_HUB',
          'export:positive|association-revision:positive:pair:v1|realization:positive:pair|PAIR_EDGE'],
      'every api_v3 view returns the exact positive fixture rows and child traces');

    SET CONSTRAINTS ALL DEFERRED;
    INSERT INTO exploration_v3.association_revision VALUES (
      'association-revision:positive:higher:v2',
      'association:v3:9c7c470b1bf49a8cc27c0902',2,'scope:positive-api','INACTIVE',
      'NONE',false,true,true,true,false,'UNRESOLVED','HIGH','BLOCKS_ACTIVATION',
      'Superseding inactive head.','NOT_REQUESTED',false,'2',repeat('5',64),repeat('6',64),
      false,'INELIGIBLE',NULL,'Superseding head is inactive.',ARRAY[]::text[],
      ARRAY['No active claim.'],'association-revision:positive:higher:v1',
      '2026-08-28T00:00:00Z',
      ARRAY['Revised transaction-local API fixture.']);
    INSERT INTO exploration_v3.association_incidence
    SELECT 'incidence:positive:higher:v2:'||n,'association-revision:positive:higher:v2',
      'concept:positive:'||n,'sense:positive:'||n,NULL,NULL,'scope:positive-api',
      ARRAY[]::text[] FROM generate_series(1,3) n;
    SET CONSTRAINTS ALL IMMEDIATE;
    PERFORM pg_temp.assert_true(
      (SELECT count(*) FROM api_v3.active_association
        WHERE association_revision_id='association-revision:positive:higher:v1') = 0
      AND (SELECT array_agg(association_revision_id)
        FROM api_v3.active_association) =
          ARRAY['association-revision:positive:pair:v1']
      AND NOT EXISTS (SELECT 1 FROM api_v3.association_incidence
        WHERE association_revision_id='association-revision:positive:higher:v1')
      AND NOT EXISTS (SELECT 1 FROM api_v3.association_evidence_locator
        WHERE association_revision_id='association-revision:positive:higher:v1')
      AND (SELECT array_agg(concept_id ORDER BY concept_id)
        FROM api_v3.active_concept) =
          ARRAY['concept:positive:1','concept:positive:2']
      AND (SELECT array_agg(sense_id ORDER BY sense_id)
        FROM api_v3.active_concept_sense) =
          ARRAY['sense:positive:1','sense:positive:2']
      AND (SELECT array_agg(scope_id) FROM api_v3.active_scope) =
          ARRAY['scope:positive-api']
      AND (SELECT count(*) FROM api_v3.active_association_synthesis_step) = 0
      AND (SELECT count(*) FROM api_v3.active_association_synthesis_step_evidence) = 0
      AND (SELECT count(*) FROM api_v3.active_association_internal_pair_link) = 0
      AND (SELECT count(*) FROM api_v3.product_composition) = 0
      AND (SELECT count(*) FROM api_v3.product_composition_realization) = 0
      AND (SELECT count(*) FROM api_v3.product_composition_realization_incidence) = 0
      AND (SELECT count(*) FROM api_v3.product_composition_coherence_review) = 0
      AND (SELECT count(*) FROM api_v3.product_navigation_state) = 0
      AND (SELECT count(*) FROM api_v3.product_navigation_node) = 0
      AND (SELECT count(*) FROM api_v3.product_navigation_path_step) = 0
      AND (SELECT count(*) FROM api_v3.product_transition) = 0
      AND (SELECT count(*) FROM api_v3.product_workflow) = 0
      AND (SELECT count(*) FROM api_v3.product_workflow_state) = 0
      AND (SELECT count(*) FROM api_v3.product_workflow_association_revision) = 0
      AND (SELECT count(*) FROM api_v3.product_workflow_association_realization) = 0
      AND (SELECT count(*) FROM api_v3.product_workflow_transition) = 0
      AND (SELECT count(*) FROM api_v3.product_export) = 0
      AND (SELECT count(*) FROM api_v3.product_export_projection_preservation) = 0,
      'inactive current association head hides the entire superseded product chain');
    RAISE EXCEPTION 'POSITIVE_API_AND_CURRENT_HEAD_FIXTURE_VERIFIED';
  EXCEPTION WHEN raise_exception THEN
    GET STACKED DIAGNOSTICS v_message=MESSAGE_TEXT;
    IF v_message <> 'POSITIVE_API_AND_CURRENT_HEAD_FIXTURE_VERIFIED' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$positive_api_and_current_head_fixture$;

DO $append_only_block$
BEGIN
  BEGIN
    UPDATE exploration_v3.association SET arity=4
    WHERE association_id='association:v3:d9a68bf6518292a0495c3196';
    RAISE EXCEPTION 'APPEND_ONLY_UPDATE_NOT_REJECTED';
  EXCEPTION WHEN object_not_in_prerequisite_state THEN NULL;
  END;
END
$append_only_block$;

SELECT pg_temp.assert_true(
  (SELECT implicit_projected_pair_count FROM audit.exploration_v3_inventory) = 0
  AND (SELECT active_pending_or_incoherent_count FROM audit.exploration_v3_inventory) = 0,
  'audit inventory proves no implicit pairs or invalid active production records');
SELECT pg_temp.assert_true(
  (SELECT count(*) FROM api_v3.active_association) = 0
  AND (SELECT count(*) FROM api_v3.active_scope) = 0
  AND (SELECT count(*) FROM api_v3.active_concept) = 0
  AND (SELECT count(*) FROM api_v3.active_concept_sense) = 0
  AND (SELECT count(*) FROM api_v3.association_incidence) = 0
  AND (SELECT count(*) FROM api_v3.association_evidence_locator) = 0
  AND (SELECT count(*) FROM api_v3.active_association_synthesis_step) = 0
  AND (SELECT count(*) FROM api_v3.active_association_synthesis_step_evidence) = 0
  AND (SELECT count(*) FROM api_v3.active_association_internal_pair_link) = 0
  AND (SELECT count(*) FROM api_v3.product_composition) = 0
  AND (SELECT count(*) FROM api_v3.product_composition_realization) = 0
  AND (SELECT count(*) FROM api_v3.product_composition_realization_incidence) = 0
  AND (SELECT count(*) FROM api_v3.product_composition_coherence_review) = 0
  AND (SELECT count(*) FROM api_v3.product_navigation_state) = 0
  AND (SELECT count(*) FROM api_v3.product_navigation_node) = 0
  AND (SELECT count(*) FROM api_v3.product_navigation_path_step) = 0
  AND (SELECT count(*) FROM api_v3.product_transition) = 0
  AND (SELECT count(*) FROM api_v3.product_workflow) = 0
  AND (SELECT count(*) FROM api_v3.product_workflow_state) = 0
  AND (SELECT count(*) FROM api_v3.product_workflow_association_revision) = 0
  AND (SELECT count(*) FROM api_v3.product_workflow_association_realization) = 0
  AND (SELECT count(*) FROM api_v3.product_workflow_transition) = 0
  AND (SELECT count(*) FROM api_v3.product_export) = 0
  AND (SELECT count(*) FROM api_v3.product_export_projection_preservation) = 0,
  'positive API allowlist exposes no synthetic or product-ineligible records');
SELECT pg_temp.assert_true(
  has_table_privilege('gda_v49_phase2a_api_reader','api_v3.active_association','SELECT')
  AND has_table_privilege('gda_v49_phase2a_api_reader',
    'api_v3.product_navigation_path_step','SELECT')
  AND has_table_privilege('gda_v49_phase2a_api_reader',
    'api_v3.active_association_synthesis_step_evidence','SELECT')
  AND has_table_privilege('gda_v49_phase2a_api_reader',
    'api_v3.active_association_internal_pair_link','SELECT')
  AND has_table_privilege('gda_v49_phase2a_api_reader',
    'api_v3.product_composition_realization_incidence','SELECT')
  AND has_table_privilege('gda_v49_phase2a_api_reader',
    'api_v3.product_workflow_association_realization','SELECT')
  AND has_table_privilege('gda_v49_phase2a_api_reader',
    'api_v3.product_export_projection_preservation','SELECT')
  AND NOT has_table_privilege('gda_v49_phase2a_api_reader',
    'exploration_v3.association','SELECT')
  AND NOT has_table_privilege('gda_v49_phase2a_reviewer',
    'exploration_v3.association_revision','INSERT')
  AND has_table_privilege('gda_v49_phase2a_reviewer',
    'exploration_v3.reviewer_association_queue','SELECT')
  AND NOT has_schema_privilege('public','api_v3','USAGE'),
  'runtime roles retain positive allowlists and no direct governed DML');
SELECT pg_temp.assert_true(
  NOT EXISTS (
    SELECT 1 FROM pg_catalog.pg_proc p
    JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
    WHERE n.nspname='exploration_v3' AND p.prosecdef),
  'v50 validation functions are invoker-rights only');

ROLLBACK;
\echo V50_EXPLORATION_V3_HIGHER_ORDER_ASSOCIATION_TESTS=PASS
