\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL SERIALIZABLE;
SET CONSTRAINTS ALL DEFERRED;
\ir ../fixtures/phase2s_32_snapshot.sql

-- Invalid topology is rejected before it can influence the current leaf.
DO $negative_topology$
DECLARE v_state text; v_message text;
BEGIN
  BEGIN
    INSERT INTO provenance.canonical_assignment VALUES(
      '60000000-0000-4000-8000-000000009991','folder_membership','accepted',
      '60000000-0000-4000-8000-000000009990','2026-08-20T00:00:00Z');
    RAISE EXCEPTION 'ORPHAN_SUCCESSOR_NOT_REJECTED';
  EXCEPTION WHEN foreign_key_violation THEN NULL;
  END;

  BEGIN
    INSERT INTO provenance.canonical_assignment VALUES(
      '60000000-0000-4000-8000-000000009992','folder_membership','superseded',
      '60000000-0000-4000-8000-000000009992','2026-08-20T00:00:00Z');
    SET CONSTRAINTS provenance.assignment_supersession_parent IMMEDIATE;
    RAISE EXCEPTION 'ASSIGNMENT_CYCLE_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE,v_message=MESSAGE_TEXT;
    IF v_state <> '23514' OR v_message <> 'ASSIGNMENT_SUPERSESSION_CYCLE' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;

  BEGIN
    UPDATE provenance.canonical_assignment SET status='superseded'
    WHERE canonical_assignment_id='60000000-0000-4000-8000-000000001006';
    INSERT INTO provenance.canonical_assignment VALUES(
      '60000000-0000-4000-8000-000000009993','folder_membership','accepted',
      '60000000-0000-4000-8000-000000001006','2026-08-20T00:00:00Z');
    INSERT INTO provenance.assignment_folder_membership VALUES(
      '60000000-0000-4000-8000-000000009993',
      '80000000-0000-4000-8000-000000000004',
      '20000000-0000-4000-8000-000000001007','cross_object',70);
    SET CONSTRAINTS provenance.assignment_supersession_parent IMMEDIATE;
    RAISE EXCEPTION 'CROSS_OBJECT_SUPERSESSION_NOT_REJECTED';
  EXCEPTION WHEN check_violation THEN
    GET STACKED DIAGNOSTICS v_state=RETURNED_SQLSTATE,v_message=MESSAGE_TEXT;
    IF v_state <> '23514' OR v_message <> 'ASSIGNMENT_SUPERSESSION_OBJECT_MISMATCH' THEN RAISE; END IF;
  END;
  SET CONSTRAINTS ALL DEFERRED;
END
$negative_topology$;

-- One successor: object 1 moves from its root to one accepted leaf.
UPDATE provenance.canonical_assignment SET status='superseded'
WHERE canonical_assignment_id='60000000-0000-4000-8000-000000001001';
INSERT INTO provenance.canonical_assignment VALUES(
  '60000000-0000-4000-8000-000000008001','folder_membership','accepted',
  '60000000-0000-4000-8000-000000001001','2026-08-17T00:00:00Z');
INSERT INTO provenance.assignment_folder_membership VALUES(
  '60000000-0000-4000-8000-000000008001',
  '80000000-0000-4000-8000-000000000002',
  '20000000-0000-4000-8000-000000001001','primary',20);
INSERT INTO provenance.assignment_review_decision VALUES(
  '70000000-0000-4000-8000-000000008001',
  '60000000-0000-4000-8000-000000008001','accept','fixture-reviewer',
  'single successor accepted',NULL,'2026-08-17T00:00:00Z');
INSERT INTO provenance.assignment_decision_evidence VALUES(
  '70000000-0000-4000-8000-000000008001',
  '30000000-0000-4000-8000-000000000003','supports');

-- Multi-level chain: only the terminal object-2 leaf is current.
UPDATE provenance.canonical_assignment SET status='superseded'
WHERE canonical_assignment_id='60000000-0000-4000-8000-000000001002';
INSERT INTO provenance.canonical_assignment VALUES(
  '60000000-0000-4000-8000-000000008201','folder_membership','superseded',
  '60000000-0000-4000-8000-000000001002','2026-08-17T00:00:00Z');
INSERT INTO provenance.assignment_folder_membership VALUES(
  '60000000-0000-4000-8000-000000008201',
  '80000000-0000-4000-8000-000000000002',
  '20000000-0000-4000-8000-000000001002','primary',21);
INSERT INTO provenance.canonical_assignment VALUES(
  '60000000-0000-4000-8000-000000008202','folder_membership','accepted',
  '60000000-0000-4000-8000-000000008201','2026-08-18T00:00:00Z');
INSERT INTO provenance.assignment_folder_membership VALUES(
  '60000000-0000-4000-8000-000000008202',
  '80000000-0000-4000-8000-000000000003',
  '20000000-0000-4000-8000-000000001002','primary',21);
INSERT INTO provenance.assignment_review_decision VALUES(
  '70000000-0000-4000-8000-000000008202',
  '60000000-0000-4000-8000-000000008202','accept','fixture-reviewer',
  'multi-level terminal leaf accepted',NULL,'2026-08-18T00:00:00Z');
INSERT INTO provenance.assignment_decision_evidence VALUES(
  '70000000-0000-4000-8000-000000008202',
  '30000000-0000-4000-8000-000000000003','supports');

-- Non-conflicting branch semantics are explicit: both same-object leaves
-- publish, while the superseded root does not.
UPDATE provenance.canonical_assignment SET status='superseded'
WHERE canonical_assignment_id='60000000-0000-4000-8000-000000001003';
INSERT INTO provenance.canonical_assignment VALUES
  ('60000000-0000-4000-8000-000000008301','folder_membership','accepted',
    '60000000-0000-4000-8000-000000001003','2026-08-19T00:00:00Z'),
  ('60000000-0000-4000-8000-000000008302','folder_membership','accepted',
    '60000000-0000-4000-8000-000000001003','2026-08-19T00:00:00Z');
INSERT INTO provenance.assignment_folder_membership VALUES
  ('60000000-0000-4000-8000-000000008301',
    '80000000-0000-4000-8000-000000000002',
    '20000000-0000-4000-8000-000000001003','branch_a',30),
  ('60000000-0000-4000-8000-000000008302',
    '80000000-0000-4000-8000-000000000003',
    '20000000-0000-4000-8000-000000001003','branch_b',30);
INSERT INTO provenance.assignment_review_decision VALUES
  ('70000000-0000-4000-8000-000000008301',
    '60000000-0000-4000-8000-000000008301','accept','fixture-reviewer',
    'branch A accepted',NULL,'2026-08-19T00:00:00Z'),
  ('70000000-0000-4000-8000-000000008302',
    '60000000-0000-4000-8000-000000008302','accept','fixture-reviewer',
    'branch B accepted',NULL,'2026-08-19T00:00:00Z');
INSERT INTO provenance.assignment_decision_evidence
SELECT d,'30000000-0000-4000-8000-000000000003'::uuid,'supports'::provenance.evidence_role
FROM unnest(ARRAY[
  '70000000-0000-4000-8000-000000008301'::uuid,
  '70000000-0000-4000-8000-000000008302'::uuid]) AS d;

-- Equal timestamps do not choose by position or time: topology chooses the
-- new decision leaf deterministically.
INSERT INTO provenance.assignment_review_decision VALUES(
  '70000000-0000-4000-8000-000000008401',
  '60000000-0000-4000-8000-000000001004','accept','fixture-reviewer',
  'equal timestamp decision successor',
  '70000000-0000-4000-8000-000000001004','2026-08-16T00:00:00Z');
INSERT INTO provenance.assignment_decision_evidence VALUES(
  '70000000-0000-4000-8000-000000008401',
  '30000000-0000-4000-8000-000000000003','supports');

-- The schema has no invented withdrawn/failed assignment states.  A
-- withdrawn workflow candidate is represented by rejected disposition, and
-- a failed review is an accepted assignment whose current decision rejects.
INSERT INTO provenance.canonical_assignment VALUES
  ('60000000-0000-4000-8000-000000008501','folder_membership','rejected',NULL,'2026-08-20T00:00:00Z'),
  ('60000000-0000-4000-8000-000000008502','folder_membership','rejected',NULL,'2026-08-20T00:00:00Z');
INSERT INTO provenance.assignment_folder_membership VALUES
  ('60000000-0000-4000-8000-000000008501',
    '80000000-0000-4000-8000-000000000004',
    '20000000-0000-4000-8000-000000001005','withdrawn_candidate',90),
  ('60000000-0000-4000-8000-000000008502',
    '80000000-0000-4000-8000-000000000004',
    '20000000-0000-4000-8000-000000001006','failed_review',91);
INSERT INTO provenance.assignment_review_decision VALUES(
  '70000000-0000-4000-8000-000000008502',
  '60000000-0000-4000-8000-000000008502','reject','fixture-reviewer',
  'failed review candidate',NULL,'2026-08-20T00:00:00Z');
INSERT INTO provenance.assignment_decision_evidence VALUES(
  '70000000-0000-4000-8000-000000008502',
  '30000000-0000-4000-8000-000000000003','supports');

SET CONSTRAINTS ALL IMMEDIATE;
SET CONSTRAINTS ALL DEFERRED;

SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.create_research_release(
  '93000000-0000-4000-8000-000000001001','db-closure-leaf-v1',
  'schema-v49.0','model-v49.0',
  '93000000-0000-4000-8000-000000001002',repeat('1',64));
SELECT release.build_research_launch_snapshot_v5(
  '93000000-0000-4000-8000-000000001001',
  '10000000-0000-4000-8000-000000000003',
  '80000000-0000-4000-8000-000000000010',
  '93000000-0000-4000-8000-000000001003',repeat('2',64)) AS candidate_fingerprint \gset
RESET SESSION AUTHORIZATION;

DO $leaf_assertions$
BEGIN
  IF (SELECT count(*) FROM release.research_release_object
      WHERE research_release_id='93000000-0000-4000-8000-000000001001') <> 32 THEN
    RAISE EXCEPTION 'CURRENT_LEAF_OBJECT_COUNT_MISMATCH';
  END IF;
  IF (SELECT count(*) FROM release.research_folder_membership_projection_v3
      WHERE research_release_id='93000000-0000-4000-8000-000000001001') <> 33 THEN
    RAISE EXCEPTION 'CURRENT_LEAF_MEMBERSHIP_COUNT_MISMATCH';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM release.research_folder_membership_projection_v3
      WHERE research_release_id='93000000-0000-4000-8000-000000001001'
        AND source_assignment_id='60000000-0000-4000-8000-000000001010') THEN
    RAISE EXCEPTION 'NO_SUCCESSOR_ASSIGNMENT_NOT_PUBLISHED';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM release.research_folder_membership_projection_v3
      WHERE research_release_id='93000000-0000-4000-8000-000000001001'
        AND source_assignment_id='60000000-0000-4000-8000-000000008001') THEN
    RAISE EXCEPTION 'ONE_SUCCESSOR_LEAF_NOT_PUBLISHED';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM release.research_folder_membership_projection_v3
      WHERE research_release_id='93000000-0000-4000-8000-000000001001'
        AND source_assignment_id='60000000-0000-4000-8000-000000008202') THEN
    RAISE EXCEPTION 'MULTILEVEL_LEAF_NOT_PUBLISHED';
  END IF;
  IF (SELECT count(*) FROM release.research_folder_membership_projection_v3
      WHERE research_release_id='93000000-0000-4000-8000-000000001001'
        AND source_assignment_id IN (
          '60000000-0000-4000-8000-000000008301',
          '60000000-0000-4000-8000-000000008302')) <> 2 THEN
    RAISE EXCEPTION 'BRANCH_LEAF_SEMANTICS_MISMATCH';
  END IF;
  IF EXISTS (SELECT 1 FROM release.research_folder_membership_projection_v3
      WHERE research_release_id='93000000-0000-4000-8000-000000001001'
        AND source_assignment_id IN (
          '60000000-0000-4000-8000-000000001001',
          '60000000-0000-4000-8000-000000001002',
          '60000000-0000-4000-8000-000000008201',
          '60000000-0000-4000-8000-000000001003',
          '60000000-0000-4000-8000-000000008501',
          '60000000-0000-4000-8000-000000008502')) THEN
    RAISE EXCEPTION 'NONCURRENT_OR_FAILED_ASSIGNMENT_LEAKED';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM release.research_folder_membership_projection_v3
      WHERE research_release_id='93000000-0000-4000-8000-000000001001'
        AND source_assignment_id='60000000-0000-4000-8000-000000001004'
        AND effective_decision_id='70000000-0000-4000-8000-000000008401') THEN
    RAISE EXCEPTION 'EQUAL_TIMESTAMP_DECISION_LEAF_MISMATCH';
  END IF;
  IF EXISTS (SELECT 1 FROM release.research_folder_membership_projection_v3
      WHERE research_release_id='93000000-0000-4000-8000-000000001001'
        AND effective_decision_id='70000000-0000-4000-8000-000000001004') THEN
    RAISE EXCEPTION 'SUPERSEDED_DECISION_LEAKED';
  END IF;
END
$leaf_assertions$;

SELECT release.canonical_jsonb_sha256(jsonb_build_object(
  'format','gda-v49-research-validation-v5',
  'releaseId','93000000-0000-4000-8000-000000001001'::uuid,
  'candidateFingerprint',:'candidate_fingerprint'::core.sha256_hex,
  'componentManifestSha256',release.research_launch_component_manifest_sha_v5(
    '93000000-0000-4000-8000-000000001001'))) AS validation_sha \gset
SET SESSION AUTHORIZATION gda_v49_phase2a_publisher;
SELECT release.validate_research_launch_snapshot_v5(
  '93000000-0000-4000-8000-000000001001',:'validation_sha',
  '93000000-0000-4000-8000-000000001004',repeat('3',64));
SELECT release.seal_research_launch_snapshot_v5(
  '93000000-0000-4000-8000-000000001001',
  '93000000-0000-4000-8000-000000001005',
  '93000000-0000-4000-8000-000000001006',repeat('4',64));
RESET SESSION AUTHORIZATION;

DO $lifecycle_assertion$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM release.research_release
      WHERE research_release_id='93000000-0000-4000-8000-000000001001'
        AND release_state='sealed' AND manifest_sha256 IS NOT NULL) THEN
    RAISE EXCEPTION 'VALIDATED_SEALED_LIFECYCLE_MISMATCH';
  END IF;
END
$lifecycle_assertion$;

ROLLBACK;
\echo V49_DB_CLOSURE_CURRENT_LEAF=PASS
