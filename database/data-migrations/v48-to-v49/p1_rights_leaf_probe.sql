\set ON_ERROR_STOP on
\timing on

BEGIN;
SET LOCAL TIME ZONE 'UTC';
SET CONSTRAINTS ALL DEFERRED;

INSERT INTO raw.source_asset (
  source_asset_id, authority, logical_name, sha256, byte_length,
  raw_bytes, media_type, received_at
) VALUES (
  'a1000000-0000-4000-8000-000000000001',
  'canonical_migration_input', 'phase2b-p1-rights-leaf-probe.json',
  encode(sha256(convert_to('probe', 'UTF8')), 'hex'), 5,
  convert_to('probe', 'UTF8'), 'application/json', '2026-08-14T00:00:00Z'
);

INSERT INTO raw.source_record (
  source_record_id, source_asset_id, record_ordinal, legacy_source_record_id,
  raw_value, raw_fingerprint, parsed_projection, parse_error_code
) VALUES (
  'a2000000-0000-4000-8000-000000000001',
  'a1000000-0000-4000-8000-000000000001', 0, 'p1-probe',
  convert_to('{"probe":true}', 'UTF8'),
  encode(sha256(convert_to('{"probe":true}', 'UTF8')), 'hex'),
  '{"probe":true}'::jsonb, NULL
);

INSERT INTO rights.external_visual_reference (
  external_visual_reference_id, source_asset_id, source_record_id,
  source_field_or_json_pointer, source_occurrence_ordinal,
  provider_object_id, reference_fingerprint, created_at
)
SELECT
  ('a3000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid,
  'a1000000-0000-4000-8000-000000000001'::uuid,
  'a2000000-0000-4000-8000-000000000001'::uuid,
  '/probe/' || g::text, g,
  NULL,
  encode(sha256(convert_to('reference-' || g::text, 'UTF8')), 'hex'),
  '2026-08-14T00:00:00Z'
FROM generate_series(1, :scale::integer) AS g;

INSERT INTO rights.rights_assessment (
  rights_assessment_id, subject_kind, assessed_state, reviewer_actor,
  rationale, assessed_at, supersedes_rights_assessment_id
)
SELECT
  ('a4000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid,
  'external_visual_reference', 'unknown', 'phase2b-p1-probe',
  'bounded P1 performance diagnosis', '2026-08-14T00:01:00Z', NULL
FROM generate_series(1, :scale::integer) AS g;

INSERT INTO rights.rights_assessment_visual_reference (
  rights_assessment_id, external_visual_reference_id
)
SELECT
  ('a4000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid,
  ('a3000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid
FROM generate_series(1, :scale::integer) AS g;

ANALYZE rights.rights_assessment;
ANALYZE rights.rights_assessment_visual_reference;

\echo P1_POSTFIX_DIRECT_EXPLAIN_BEGIN scale=:scale
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS, TIMING, SUMMARY, FORMAT JSON)
SELECT count(*)
FROM rights.rights_assessment_visual_reference t
JOIN rights.rights_assessment x
  ON x.rights_assessment_id=t.rights_assessment_id
 AND x.subject_kind='external_visual_reference'
WHERE t.external_visual_reference_id=
      'a3000000-0000-4000-8000-000000000001'::uuid
  AND NOT EXISTS (
    SELECT 1 FROM rights.rights_assessment newer
    WHERE newer.supersedes_rights_assessment_id=x.rights_assessment_id
  );
\echo P1_POSTFIX_DIRECT_EXPLAIN_END scale=:scale

SELECT clock_timestamp() AS leaf_started,
       pg_current_wal_lsn() AS leaf_wal_started
\gset
\echo P1_NAMED_CONSTRAINT_BEGIN constraint=rights.rights_assessment_one_current_leaf scale=:scale
SET CONSTRAINTS rights.rights_assessment_one_current_leaf IMMEDIATE;
SELECT
  :scale::bigint AS scale,
  extract(epoch FROM (clock_timestamp()-:'leaf_started'::timestamptz)) AS named_constraint_seconds,
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'leaf_wal_started'::pg_lsn) AS named_constraint_wal_bytes,
  (SELECT count(*) FROM rights.rights_assessment) AS assessment_rows,
  (SELECT count(*) FROM rights.rights_assessment_visual_reference) AS typed_subject_rows;
\echo P1_NAMED_CONSTRAINT_END constraint=rights.rights_assessment_one_current_leaf scale=:scale

ROLLBACK;
