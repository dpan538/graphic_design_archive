-- Transaction-scoped synthetic fixture. Caller must BEGIN before and ROLLBACK after.
-- No v48 asset, SQLite row, TRACE shard, or production record is read or imported.

INSERT INTO raw.source_asset (
  source_asset_id, authority, logical_name, sha256, byte_length,
  raw_bytes, media_type, received_at
) VALUES (
  '10000000-0000-4000-8000-000000000001',
  'canonical_migration_input', 'phase2a-synthetic-candidate.json',
  encode(sha256(convert_to('fixture-asset', 'UTF8')), 'hex'),
  octet_length(convert_to('fixture-asset', 'UTF8')),
  convert_to('fixture-asset', 'UTF8'), 'application/json',
  '2026-08-11T00:00:00Z'
);

INSERT INTO raw.source_asset (
  source_asset_id, authority, logical_name, sha256, byte_length,
  raw_bytes, media_type, received_at
) VALUES
  ('10000000-0000-4000-8000-000000000021',
   'immutable_reconciliation_evidence','phase2a-synthetic-reconciliation.sqlite',
   encode(sha256(convert_to('fixture-reconciliation','UTF8')),'hex'),
   octet_length(convert_to('fixture-reconciliation','UTF8')),
   convert_to('fixture-reconciliation','UTF8'),'application/vnd.sqlite3','2026-08-11T00:00:00Z'),
  ('10000000-0000-4000-8000-000000000022',
   'integrity_evidence','phase2a-synthetic-transfer.json',
   encode(sha256(convert_to('fixture-transfer-json','UTF8')),'hex'),
   octet_length(convert_to('fixture-transfer-json','UTF8')),
   convert_to('fixture-transfer-json','UTF8'),'application/json','2026-08-11T00:00:00Z'),
  ('10000000-0000-4000-8000-000000000023',
   'integrity_evidence','phase2a-synthetic-transfer.csv',
   encode(sha256(convert_to('fixture-transfer-csv','UTF8')),'hex'),
   octet_length(convert_to('fixture-transfer-csv','UTF8')),
   convert_to('fixture-transfer-csv','UTF8'),'text/csv','2026-08-11T00:00:00Z'),
  ('10000000-0000-4000-8000-000000000024',
   'integrity_evidence','phase2a-synthetic-trace-manifest.json',
   encode(sha256(convert_to('fixture-trace-manifest','UTF8')),'hex'),
   octet_length(convert_to('fixture-trace-manifest','UTF8')),
   convert_to('fixture-trace-manifest','UTF8'),'application/json','2026-08-11T00:00:00Z');

INSERT INTO release.validation_profile VALUES
  ('90000000-0000-4000-8000-000000000001','research','model-v49.0',repeat('b',64),'2026-08-11T00:00:00Z'),
  ('90000000-0000-4000-8000-000000000002','visual','model-v49.0',repeat('c',64),'2026-08-11T00:00:00Z');
INSERT INTO release.validation_profile_requirement
  (validation_profile_id,receipt_kind,requirement_ordinal)
SELECT '90000000-0000-4000-8000-000000000001'::uuid,kind,ordinality::integer
FROM unnest(ARRAY[
  'research_frozen_asset_authority','research_migration_query_identity',
  'research_population_and_count_parity','research_corpus_missingness_concentration',
  'research_fk_orphan_integrity','research_predicate_relation_epistemic_registry',
  'research_claim_projection_eligibility','research_unknown_relation_isolation',
  'research_projection_fingerprint','research_deterministic_asset_inventory',
  'research_role_grant_security']::release.validation_receipt_kind[])
  WITH ORDINALITY AS x(kind,ordinality);
INSERT INTO release.validation_profile_requirement
  (validation_profile_id,receipt_kind,requirement_ordinal)
SELECT '90000000-0000-4000-8000-000000000002'::uuid,kind,ordinality::integer
FROM unnest(ARRAY[
  'visual_legacy_disposition','visual_reference_bridge_provider_locator_identity',
  'visual_rights_policy_delivery_health_takedown','visual_attribution_review_due',
  'visual_held_pixel_non_disclosure','visual_research_compatibility',
  'visual_projection_fingerprint','visual_deterministic_asset_inventory',
  'visual_role_grant_security']::release.validation_receipt_kind[])
  WITH ORDINALITY AS x(kind,ordinality);

INSERT INTO raw.mapping_version VALUES (
  '10000000-0000-4000-8000-000000000002',
  'phase2a-fixture-mapping-v1', repeat('1', 64),
  'fixture-parser-v1', 'preserve_no_automatic_split',
  '2026-08-11T00:00:00Z'
);

INSERT INTO raw.migration_batch VALUES (
  '10000000-0000-4000-8000-000000000003',
  'phase2a-fixture-batch-v1',
  '10000000-0000-4000-8000-000000000001',
  '10000000-0000-4000-8000-000000000002',
  encode(sha256(convert_to('fixture-asset', 'UTF8')), 'hex'),
  '2026-08-11T00:00:00Z', NULL
);

INSERT INTO raw.source_record (
  source_record_id, source_asset_id, record_ordinal, legacy_source_record_id,
  raw_value, raw_fingerprint, parsed_projection, parse_error_code
) VALUES
  (
    '10000000-0000-4000-8000-000000000004',
    '10000000-0000-4000-8000-000000000001', 0,
    'fixture-source-record-a', convert_to('{"id":"fixture-a"}', 'UTF8'),
    encode(sha256(convert_to('{"id":"fixture-a"}', 'UTF8')), 'hex'),
    '{"id":"fixture-a"}'::jsonb, NULL
  ),
  (
    '10000000-0000-4000-8000-000000000006',
    '10000000-0000-4000-8000-000000000001', 1,
    'fixture-source-record-b', convert_to('{"id":"fixture-b"}', 'UTF8'),
    encode(sha256(convert_to('{"id":"fixture-b"}', 'UTF8')), 'hex'),
    '{"id":"fixture-b"}'::jsonb, NULL
  );

INSERT INTO raw.field_literal VALUES (
  '10000000-0000-4000-8000-000000000005',
  '10000000-0000-4000-8000-000000000004',
  '/title', 0, 'Fixture title', NULL, NULL, NULL
);

INSERT INTO core.entity VALUES
  ('20000000-0000-4000-8000-000000000001', 'archive_object', 'active', '2026-08-11T00:00:00Z', NULL),
  ('20000000-0000-4000-8000-000000000002', 'archive_object', 'active', '2026-08-11T00:00:00Z', NULL),
  ('20000000-0000-4000-8000-000000000003', 'agent', 'active', '2026-08-11T00:00:00Z', NULL);

INSERT INTO core.archive_object (
  archive_object_id, operational_semantics_version, preferred_label,
  created_from_surface_ledger_id
) VALUES
  ('20000000-0000-4000-8000-000000000001', 'operational-v49.0', 'Fixture object A',
   '10000000-0000-4000-8000-000000000011'),
  ('20000000-0000-4000-8000-000000000002', 'operational-v49.0', 'Fixture held object B',
   '10000000-0000-4000-8000-000000000012');
INSERT INTO core.agent VALUES (
  '20000000-0000-4000-8000-000000000003', 'Fixture claimant');

INSERT INTO raw.legacy_surface_ledger VALUES
  (
    '10000000-0000-4000-8000-000000000011',
    '10000000-0000-4000-8000-000000000003',
    '10000000-0000-4000-8000-000000000004',
    '10000000-0000-4000-8000-000000000001', 0,
    'fixture-surface-a', 'fixture-source-record-a',
    encode(sha256(convert_to('{"id":"fixture-a"}', 'UTF8')), 'hex'),
    'accounted', '20000000-0000-4000-8000-000000000001', 'ACCOUNTED_FIXTURE'
  ),
  (
    '10000000-0000-4000-8000-000000000012',
    '10000000-0000-4000-8000-000000000003',
    '10000000-0000-4000-8000-000000000006',
    '10000000-0000-4000-8000-000000000001', 1,
    'fixture-surface-b', 'fixture-source-record-b',
    encode(sha256(convert_to('{"id":"fixture-b"}', 'UTF8')), 'hex'),
    'held', '20000000-0000-4000-8000-000000000002', 'HELD_FIXTURE'
  );

INSERT INTO provenance.source_document (
  source_document_id, source_kind, public_citation, created_at
) VALUES (
  '30000000-0000-4000-8000-000000000001',
  'synthetic_fixture', 'Synthetic Phase 2A evidence',
  '2026-08-11T00:00:00Z'
);
INSERT INTO provenance.source_version (
  source_version_id,source_document_id,version_token,content_sha256,
  byte_length,supersedes_source_version_id,created_at,source_asset_id
) VALUES (
  '30000000-0000-4000-8000-000000000002',
  '30000000-0000-4000-8000-000000000001',
  'fixture-source-v1', repeat('4', 64), 16, NULL,
  '2026-08-11T00:00:00Z','10000000-0000-4000-8000-000000000001'
);
INSERT INTO provenance.evidence_item (
  evidence_item_id, source_version_id, source_record_id, locator_scheme,
  internal_locator, span_start, span_end, content_sha256, stable_citation,
  supersedes_evidence_item_id, created_at, source_asset_id
) VALUES (
  '30000000-0000-4000-8000-000000000003',
  '30000000-0000-4000-8000-000000000002',
  '10000000-0000-4000-8000-000000000004',
  'json_pointer', '/fixture/evidence', 0, 7, repeat('5', 64),
  'Synthetic fixture, locator 1', NULL, '2026-08-11T00:00:00Z',
  '10000000-0000-4000-8000-000000000001'
);
INSERT INTO provenance.object_source_record VALUES
  ('20000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000004', 'primary'),
  ('20000000-0000-4000-8000-000000000002', '10000000-0000-4000-8000-000000000006', 'primary');

INSERT INTO provenance.predicate_evidence_profile VALUES (
  '30000000-0000-4000-8000-000000000009','fixture-assertion-profile-v1',
  repeat('d',64),true,true,1,'Fixture evidence and review are mandatory');
INSERT INTO provenance.assertion_predicate VALUES (
  '30000000-0000-4000-8000-000000000004',
  'fixture_documented_label', true, 'Fixture active predicate',
  'fixture-predicate-registry-v1','entity','literal',
  '30000000-0000-4000-8000-000000000009'
);
INSERT INTO provenance.assignment_predicate_compatibility VALUES (
  'entity_name','30000000-0000-4000-8000-000000000004',
  'fixture-assignment-compat-v1',repeat('e',64));
INSERT INTO provenance.assertion VALUES (
  '30000000-0000-4000-8000-000000000005',
  '30000000-0000-4000-8000-000000000004',
  'entity', 'literal', 'accepted',
  '20000000-0000-4000-8000-000000000003',
  'Fixture label', NULL, '2026-08-11T00:00:00Z'
);
INSERT INTO provenance.assertion_subject_entity VALUES (
  '30000000-0000-4000-8000-000000000005',
  '20000000-0000-4000-8000-000000000001');
INSERT INTO provenance.assertion_value_literal VALUES (
  '30000000-0000-4000-8000-000000000005',
  '10000000-0000-4000-8000-000000000005',
  'Fixture title', 'en', NULL);
INSERT INTO provenance.assertion_evidence VALUES (
  '30000000-0000-4000-8000-000000000005',
  '30000000-0000-4000-8000-000000000003', 'supports');
INSERT INTO provenance.assertion_review_decision VALUES (
  '30000000-0000-4000-8000-000000000007',
  '30000000-0000-4000-8000-000000000005', 'accept',
  'fixture-reviewer', 'Fixture assertion reviewed', NULL,
  '2026-08-11T00:00:00Z');
INSERT INTO provenance.assertion_decision_evidence VALUES (
  '30000000-0000-4000-8000-000000000007',
  '30000000-0000-4000-8000-000000000003', 'supports');

INSERT INTO provenance.canonical_assignment VALUES (
  '30000000-0000-4000-8000-000000000006',
  'entity_name', 'accepted', NULL, '2026-08-11T00:00:00Z');
INSERT INTO provenance.assignment_entity_name VALUES (
  '30000000-0000-4000-8000-000000000006',
  '20000000-0000-4000-8000-000000000001',
  '10000000-0000-4000-8000-000000000005');
INSERT INTO provenance.assignment_assertion VALUES (
  '30000000-0000-4000-8000-000000000006',
  '30000000-0000-4000-8000-000000000005', 'supports');
INSERT INTO provenance.assignment_review_decision VALUES (
  '30000000-0000-4000-8000-000000000008',
  '30000000-0000-4000-8000-000000000006', 'accept',
  'fixture-reviewer', 'Fixture assignment reviewed', NULL,
  '2026-08-11T00:00:00Z');
INSERT INTO provenance.assignment_decision_evidence VALUES (
  '30000000-0000-4000-8000-000000000008',
  '30000000-0000-4000-8000-000000000003', 'supports');

INSERT INTO research.corpus VALUES (
  '40000000-0000-4000-8000-000000000001',
  'phase2a-fixture-corpus', 'Fixture research corpus',
  '2026-08-11T00:00:00Z');
INSERT INTO research.corpus_version VALUES (
  '40000000-0000-4000-8000-000000000002',
  '40000000-0000-4000-8000-000000000001',
  'fixture-corpus-v1', 'fixture-policy-v1', repeat('6', 64),
  'synthetic phase2a objects', '2026-08-11T00:00:00Z');
INSERT INTO research.corpus_membership VALUES
  ('40000000-0000-4000-8000-000000000002', '20000000-0000-4000-8000-000000000001',
   'eligible', 'EXPLICIT_FIXTURE_ELIGIBLE', '30000000-0000-4000-8000-000000000003',
   'fixture-reviewer', '2026-08-11T00:00:00Z'),
  ('40000000-0000-4000-8000-000000000002', '20000000-0000-4000-8000-000000000002',
   'held', 'EXPLICIT_FIXTURE_HELD', '30000000-0000-4000-8000-000000000003',
   'fixture-reviewer', '2026-08-11T00:00:00Z');

INSERT INTO research.missingness_snapshot VALUES (
  '40000000-0000-4000-8000-000000000021',
  '40000000-0000-4000-8000-000000000002','fixture-missingness-v1',
  repeat('1',64),'fixture-missingness-method-v1','archive_object',2,
  '2026-08-11T00:00:00Z');
INSERT INTO research.missingness_observation VALUES (
  '40000000-0000-4000-8000-000000000021','held','archive_object',1,
  'Synthetic held control');
INSERT INTO research.coverage_snapshot VALUES (
  '40000000-0000-4000-8000-000000000022',
  '40000000-0000-4000-8000-000000000002','fixture-coverage-v1',
  repeat('2',64),'fixture-coverage-method-v1','archive_object',1,2,
  '2026-08-11T00:00:00Z');

INSERT INTO research.epistemic_class VALUES (
  '40000000-0000-4000-8000-000000000003',
  'documented_source_statement', true, false, true,
  'Evidence-backed documented fixture statement',
  'fixture-epistemic-profile-v1',repeat('3',64));
INSERT INTO research.claim (claim_id, created_at) VALUES (
  '40000000-0000-4000-8000-000000000004',
  '2026-08-11T00:00:00Z');
INSERT INTO research.claim_revision (
  claim_revision_id,claim_id,revision_number,epistemic_class_id,status,
  workflow_state,claimant_agent_id,wording,temporal_qualifier_id,
  spatial_qualifier_id,analysis_run_id,supersedes_claim_revision_id,
  created_at,claim_date_or_version,claim_stance
) VALUES (
  '40000000-0000-4000-8000-000000000005',
  '40000000-0000-4000-8000-000000000004', 1,
  '40000000-0000-4000-8000-000000000003', 'accepted', 'resolved',
  '20000000-0000-4000-8000-000000000003',
  'Fixture claim wording', NULL, NULL, NULL, NULL,
  '2026-08-11T00:00:00Z','fixture-claim-v1','supports');
INSERT INTO research.claim_evidence VALUES (
  '40000000-0000-4000-8000-000000000005',
  '30000000-0000-4000-8000-000000000003', 'supports');
INSERT INTO research.claim_review_decision VALUES (
  '40000000-0000-4000-8000-000000000011',
  '40000000-0000-4000-8000-000000000005', 'accept', false,
  'fixture-reviewer', 'Fixture claim reviewed', NULL,
  '2026-08-11T00:00:00Z');
INSERT INTO research.claim_decision_evidence VALUES (
  '40000000-0000-4000-8000-000000000011',
  '30000000-0000-4000-8000-000000000003', 'supports');

INSERT INTO research.relation_type VALUES (
  '40000000-0000-4000-8000-000000000006',
  'fixture_related_to', true, 'archive_object', 'archive_object',
  true, 'fixture-evidence-v1', false, false,
  'Evidence-bound fixture relation','fixture-relation-registry-v1');
INSERT INTO research.relation_endpoint VALUES
  ('40000000-0000-4000-8000-000000000007', 'entity'),
  ('40000000-0000-4000-8000-000000000008', 'entity');
INSERT INTO research.relation_endpoint_entity VALUES
  ('40000000-0000-4000-8000-000000000007', '20000000-0000-4000-8000-000000000001'),
  ('40000000-0000-4000-8000-000000000008', '20000000-0000-4000-8000-000000000002');
INSERT INTO research.semantic_relation (
  semantic_relation_id, subject_endpoint_id, relation_type_id,
  object_endpoint_id, origin, status, temporal_qualifier_id,
  spatial_qualifier_id, supersedes_semantic_relation_id, created_at
) VALUES (
  '40000000-0000-4000-8000-000000000009',
  '40000000-0000-4000-8000-000000000007',
  '40000000-0000-4000-8000-000000000006',
  '40000000-0000-4000-8000-000000000008',
  'curator_created', 'accepted', NULL, NULL, NULL,
  '2026-08-11T00:00:00Z');
INSERT INTO research.relation_claim VALUES (
  '40000000-0000-4000-8000-000000000009',
  '40000000-0000-4000-8000-000000000004',
  '40000000-0000-4000-8000-000000000005', 'supports');
INSERT INTO research.relation_review_decision VALUES (
  '40000000-0000-4000-8000-000000000010',
  '40000000-0000-4000-8000-000000000009', 'accept',
  'fixture-reviewer', NULL, 'Fixture evidence reviewed', NULL,
  '2026-08-11T00:00:00Z');
INSERT INTO research.relation_decision_evidence VALUES (
  '40000000-0000-4000-8000-000000000010',
  '30000000-0000-4000-8000-000000000003', 'supports');

INSERT INTO rights.provider VALUES (
  '50000000-0000-4000-8000-000000000001',
  'fixture_provider', 'Fixture Provider', '2026-08-11T00:00:00Z');
INSERT INTO rights.provider_object VALUES (
  '50000000-0000-4000-8000-000000000002',
  '50000000-0000-4000-8000-000000000001',
  'fixture-provider-object', '2026-08-11T00:00:00Z');
INSERT INTO rights.provider_policy_scope VALUES (
  '50000000-0000-4000-8000-000000000016',
  '50000000-0000-4000-8000-000000000001','fixture-display-scope',
  'Fixture remote-display policy scope','2026-08-11T00:00:00Z');
INSERT INTO rights.provider_policy_version (
  provider_policy_version_id,provider_id,version_token,policy_sha256,
  policy_state,effective_from,effective_until,review_due,
  source_evidence_item_id,policy_scope_id
) VALUES (
  '50000000-0000-4000-8000-000000000003',
  '50000000-0000-4000-8000-000000000001',
  'fixture-policy-v1', repeat('7', 64), 'remote_display_allowed',
  clock_timestamp() - interval '1 day', clock_timestamp() + interval '7 days',
  clock_timestamp() + interval '5 days',
  '30000000-0000-4000-8000-000000000003',
  '50000000-0000-4000-8000-000000000016');

INSERT INTO rights.external_visual_reference (
  external_visual_reference_id, source_asset_id, source_record_id,
  source_field_or_json_pointer, source_occurrence_ordinal,
  provider_object_id, reference_fingerprint, created_at
) VALUES (
  '50000000-0000-4000-8000-000000000004',
  '10000000-0000-4000-8000-000000000001',
  '10000000-0000-4000-8000-000000000004', '/image/url', 0,
  '50000000-0000-4000-8000-000000000002', repeat('8', 64),
  '2026-08-11T00:00:00Z');
INSERT INTO rights.object_visual_reference VALUES (
  '50000000-0000-4000-8000-000000000014',
  '20000000-0000-4000-8000-000000000001',
  '50000000-0000-4000-8000-000000000004',
  'primary_depiction', 0, 'accepted',
  '30000000-0000-4000-8000-000000000003');
INSERT INTO rights.object_visual_reference_review_decision (
  object_visual_reference_review_decision_id,
  object_visual_reference_id, outcome, evidence_item_id,
  reviewer_actor, rationale, supersedes_decision_id, decided_at
) VALUES (
  '50000000-0000-4000-8000-000000000017',
  '50000000-0000-4000-8000-000000000014', 'accept',
  '30000000-0000-4000-8000-000000000003',
  'fixture-reviewer', 'Evidence-bound fixture bridge acceptance',
  NULL, '2026-08-11T00:00:00Z'
);

INSERT INTO rights.visual_locator (
  visual_locator_id, external_visual_reference_id, locator_role,
  source_asset_id, source_record_id, source_field_or_json_pointer,
  occurrence_ordinal, source_evidence_item_id, visibility,
  raw_locator, locator_fingerprint, supersedes_visual_locator_id, created_at
) VALUES
  (
    '50000000-0000-4000-8000-000000000005',
    '50000000-0000-4000-8000-000000000004', 'canonical_record',
    '10000000-0000-4000-8000-000000000001',
    '10000000-0000-4000-8000-000000000004', '/record/url', 0,
    '30000000-0000-4000-8000-000000000003', 'public_candidate',
    'https://provider.invalid/record/fixture',
    encode(sha256(convert_to('https://provider.invalid/record/fixture', 'UTF8')), 'hex'),
    NULL, '2026-08-11T00:00:00Z'
  ),
  (
    '50000000-0000-4000-8000-000000000006',
    '50000000-0000-4000-8000-000000000004', 'direct_image',
    '10000000-0000-4000-8000-000000000001',
    '10000000-0000-4000-8000-000000000004', '/image/url', 0,
    '30000000-0000-4000-8000-000000000003', 'public_candidate',
    'https://provider.invalid/pixel/fixture.jpg',
    encode(sha256(convert_to('https://provider.invalid/pixel/fixture.jpg', 'UTF8')), 'hex'),
    NULL, '2026-08-11T00:00:00Z'
  );

INSERT INTO rights.rights_observation VALUES (
  '50000000-0000-4000-8000-000000000007',
  'external_visual_reference', 'permitted',
  '30000000-0000-4000-8000-000000000003',
  'Synthetic permission evidence', clock_timestamp() - interval '5 minutes', NULL);
INSERT INTO rights.rights_observation_visual_reference VALUES (
  '50000000-0000-4000-8000-000000000007',
  '50000000-0000-4000-8000-000000000004');
INSERT INTO rights.rights_assessment VALUES (
  '50000000-0000-4000-8000-000000000008',
  'external_visual_reference', 'permitted', 'fixture-reviewer',
  'Synthetic positive control', clock_timestamp() - interval '4 minutes', NULL);
INSERT INTO rights.rights_assessment_visual_reference VALUES (
  '50000000-0000-4000-8000-000000000008',
  '50000000-0000-4000-8000-000000000004');
INSERT INTO rights.rights_assessment_observation VALUES (
  '50000000-0000-4000-8000-000000000008',
  '50000000-0000-4000-8000-000000000007', 'supports');

INSERT INTO rights.provider_policy_evaluation VALUES (
  '50000000-0000-4000-8000-000000000009',
  '50000000-0000-4000-8000-000000000014',
  'remote_display_allowed', 'fixture-reviewer',
  clock_timestamp() - interval '4 minutes', NULL);
INSERT INTO rights.provider_policy_evaluation_version VALUES (
  '50000000-0000-4000-8000-000000000009',
  '50000000-0000-4000-8000-000000000003');

INSERT INTO rights.attribution_bundle (
  attribution_bundle_id, object_visual_reference_id, attribution_state,
  bundle_sha256, evidence_item_id, validated_by, validated_at,
  supersedes_attribution_bundle_id
) VALUES (
  '50000000-0000-4000-8000-000000000015',
  '50000000-0000-4000-8000-000000000014', 'complete',
  release.canonical_jsonb_sha256(jsonb_build_object(
    'bundleId', '50000000-0000-4000-8000-000000000015'::uuid,
    'bridgeId', '50000000-0000-4000-8000-000000000014'::uuid,
    'state', 'complete'::rights.attribution_state,
    'evidenceId', '30000000-0000-4000-8000-000000000003'::uuid,
    'validatedBy', 'fixture-reviewer',
    'validatedAtUs',
      (extract(epoch FROM '2026-08-11T00:01:00Z'::timestamptz) * 1000000)::bigint,
    'supersedesBundleId', NULL,
    'values', jsonb_build_array(
      jsonb_build_array('attribution', 0, NULL, 'Fixture attribution'),
      jsonb_build_array('required_statement', 0, NULL, 'Fixture required statement')
    )
  )),
  '30000000-0000-4000-8000-000000000003',
  'fixture-reviewer', '2026-08-11T00:01:00Z', NULL);
INSERT INTO rights.attribution_bundle_value VALUES
  ('50000000-0000-4000-8000-000000000015', 'attribution', 0, NULL, 'Fixture attribution'),
  ('50000000-0000-4000-8000-000000000015', 'required_statement', 0, NULL, 'Fixture required statement');

INSERT INTO rights.endpoint_health_observation VALUES
  (
    '50000000-0000-4000-8000-000000000011',
    '50000000-0000-4000-8000-000000000005', 'healthy_fresh',
    'phase2a-health-v1',
    clock_timestamp() - interval '3 minutes',
    clock_timestamp() + interval '1 day', repeat('9', 64)
  ),
  (
    '50000000-0000-4000-8000-000000000012',
    '50000000-0000-4000-8000-000000000006', 'healthy_fresh',
    'phase2a-health-v1',
    clock_timestamp() - interval '3 minutes',
    clock_timestamp() + interval '1 day', repeat('a', 64)
  );

INSERT INTO rights.delivery_assessment VALUES (
  '50000000-0000-4000-8000-000000000010',
  '50000000-0000-4000-8000-000000000014',
  '50000000-0000-4000-8000-000000000015',
  'remote_image', 'RD-080', 'fixture-reviewer',
  clock_timestamp() - interval '1 minute', NULL,
  'REMOTE_IMAGE_ALL_GATES_PASS');
INSERT INTO rights.delivery_rights_assessment VALUES (
  '50000000-0000-4000-8000-000000000010',
  '50000000-0000-4000-8000-000000000008', 'supports');
INSERT INTO rights.delivery_policy_evaluation VALUES (
  '50000000-0000-4000-8000-000000000010',
  '50000000-0000-4000-8000-000000000009');
INSERT INTO rights.delivery_locator_qualification VALUES
  (
    '50000000-0000-4000-8000-000000000010',
    '50000000-0000-4000-8000-000000000005',
    '50000000-0000-4000-8000-000000000011', 'canonical_record'
  ),
  (
    '50000000-0000-4000-8000-000000000010',
    '50000000-0000-4000-8000-000000000006',
    '50000000-0000-4000-8000-000000000012', 'direct_image'
  );

INSERT INTO rights.legacy_visual_surface_disposition VALUES
  ('10000000-0000-4000-8000-000000000011',
   encode(sha256(convert_to('{"id":"fixture-a"}','UTF8')),'hex'),1,2,
   repeat('4',64),'2026-08-11T00:00:00Z'),
  ('10000000-0000-4000-8000-000000000012',
   encode(sha256(convert_to('{"id":"fixture-b"}','UTF8')),'hex'),0,0,
   repeat('5',64),'2026-08-11T00:00:00Z');
INSERT INTO rights.legacy_visual_surface_classification VALUES
  ('10000000-0000-4000-8000-000000000011','evidence_present',
   '30000000-0000-4000-8000-000000000003'),
  ('10000000-0000-4000-8000-000000000011','rights_unknown',
   '30000000-0000-4000-8000-000000000003'),
  ('10000000-0000-4000-8000-000000000012','no_visual_reference',NULL);

SET CONSTRAINTS ALL IMMEDIATE;
SET CONSTRAINTS ALL DEFERRED;
