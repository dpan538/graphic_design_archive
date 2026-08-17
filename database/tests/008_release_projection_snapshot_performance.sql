\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL SERIALIZABLE;
SET CONSTRAINTS ALL DEFERRED;
\ir ../fixtures/phase2s_32_snapshot.sql

-- A two-level chain proves current means "no newer row points here", not a
-- NULL supersedes pointer.  The accepted leaf alone may enter the snapshot.
UPDATE provenance.canonical_assignment
SET status='superseded'
WHERE canonical_assignment_id='60000000-0000-4000-8000-000000001001';
INSERT INTO provenance.canonical_assignment(
  canonical_assignment_id,assignment_kind,status,supersedes_assignment_id,created_at
) VALUES ('60000000-0000-4000-8000-000000008001','folder_membership','accepted',
  '60000000-0000-4000-8000-000000001001','2026-08-17T00:00:00Z');
INSERT INTO provenance.assignment_folder_membership(
  canonical_assignment_id,folder_id,archive_object_id,membership_role,member_ordinal
) VALUES ('60000000-0000-4000-8000-000000008001',
  '80000000-0000-4000-8000-000000000002',
  '20000000-0000-4000-8000-000000001001','primary',8);
INSERT INTO provenance.assignment_review_decision(
  assignment_review_decision_id,canonical_assignment_id,outcome,reviewer_actor,rationale,
  supersedes_decision_id,decided_at
) VALUES ('70000000-0000-4000-8000-000000008001',
  '60000000-0000-4000-8000-000000008001','accept','fixture-reviewer',
  'Current accepted leaf',NULL,'2026-08-17T00:00:00Z');
INSERT INTO provenance.assignment_decision_evidence(
  assignment_review_decision_id,evidence_item_id,evidence_role
) VALUES ('70000000-0000-4000-8000-000000008001',
  '30000000-0000-4000-8000-000000000003','supports');

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_research_release(
  '92000000-0000-4000-8000-000000001001','phase2sp-v5-r1','schema-v49.0','model-v49.0',
  '92000000-0000-4000-8000-000000001002',repeat('1',64));
SELECT release.build_research_launch_snapshot_v5(
  '92000000-0000-4000-8000-000000001001',
  '10000000-0000-4000-8000-000000000003',
  '80000000-0000-4000-8000-000000000010',
  '92000000-0000-4000-8000-000000001003',repeat('2',64)) AS candidate_fingerprint \gset
RESET SESSION AUTHORIZATION;

DO $assertions$
BEGIN
  IF (SELECT count(*) FROM release.research_release_object
    WHERE research_release_id='92000000-0000-4000-8000-000000001001') <> 32 THEN
    RAISE EXCEPTION 'expected 32 public objects';
  END IF;
  IF (SELECT count(*) FROM release.research_folder_membership_projection_v3
    WHERE research_release_id='92000000-0000-4000-8000-000000001001') <> 32 THEN
    RAISE EXCEPTION 'expected 32 public memberships';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM release.research_folder_membership_projection_v3
    WHERE research_release_id='92000000-0000-4000-8000-000000001001'
      AND source_assignment_id='60000000-0000-4000-8000-000000008001') THEN
    RAISE EXCEPTION 'current assignment leaf was not published';
  END IF;
  IF EXISTS (SELECT 1 FROM release.research_folder_membership_projection_v3
    WHERE research_release_id='92000000-0000-4000-8000-000000001001'
      AND source_assignment_id='60000000-0000-4000-8000-000000001001') THEN
    RAISE EXCEPTION 'superseded assignment root leaked';
  END IF;
  IF EXISTS (SELECT 1 FROM release.research_release_object
    WHERE research_release_id='92000000-0000-4000-8000-000000001001'
      AND archive_object_id='20000000-0000-4000-8000-000000001033') THEN
    RAISE EXCEPTION 'held object leaked';
  END IF;
END
$assertions$;

SELECT release.canonical_jsonb_sha256(jsonb_build_object(
  'format','gda-v49-research-validation-v5',
  'releaseId','92000000-0000-4000-8000-000000001001'::uuid,
  'candidateFingerprint',:'candidate_fingerprint'::core.sha256_hex,
  'componentManifestSha256',release.research_launch_component_manifest_sha_v5(
    '92000000-0000-4000-8000-000000001001')))
  AS validation_sha \gset
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.validate_research_launch_snapshot_v5(
  '92000000-0000-4000-8000-000000001001',:'validation_sha',
  '92000000-0000-4000-8000-000000001004',repeat('3',64));
SELECT release.seal_research_launch_snapshot_v5(
  '92000000-0000-4000-8000-000000001001',
  '92000000-0000-4000-8000-000000001005',
  '92000000-0000-4000-8000-000000001006',repeat('4',64));
RESET SESSION AUTHORIZATION;

DO $fault_contract$
DECLARE v_state text; v_message text;
BEGIN
  BEGIN
    PERFORM release.build_research_launch_snapshot_v5_internal(
      '92000000-0000-4000-8000-000000009901',
      '10000000-0000-4000-8000-000000000003',
      '80000000-0000-4000-8000-000000000010',
      '92000000-0000-4000-8000-000000009902',repeat('5',64),'not-a-fault');
  EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE,v_message=MESSAGE_TEXT;
  END;
  IF v_state <> '22023' OR v_message <> 'RESEARCH_LAUNCH_V5_UNKNOWN_FAULT_POINT' THEN
    RAISE EXCEPTION 'unknown fault contract failed: %, %',v_state,v_message;
  END IF;
END
$fault_contract$;
ROLLBACK;
\echo PHASE2SP_FOCUSED_V5=PASS
