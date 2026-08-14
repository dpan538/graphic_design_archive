\set ON_ERROR_STOP on
\timing on

BEGIN;
SET LOCAL TIME ZONE 'UTC';
SET CONSTRAINTS ALL DEFERRED;

INSERT INTO raw.source_asset (
  source_asset_id, authority, logical_name, sha256, byte_length,
  raw_bytes, media_type, received_at
) VALUES (
  'b1000000-0000-4000-8000-000000000001',
  'canonical_migration_input', 'phase2b-p1-delivery-probe.json',
  encode(sha256(convert_to('probe', 'UTF8')), 'hex'), 5,
  convert_to('probe', 'UTF8'), 'application/json', '2026-08-14T00:00:00Z'
);
INSERT INTO raw.source_record (
  source_record_id, source_asset_id, record_ordinal, legacy_source_record_id,
  raw_value, raw_fingerprint, parsed_projection, parse_error_code
) VALUES (
  'b2000000-0000-4000-8000-000000000001',
  'b1000000-0000-4000-8000-000000000001', 0, 'p1-delivery-probe',
  convert_to('{"probe":true}', 'UTF8'),
  encode(sha256(convert_to('{"probe":true}', 'UTF8')), 'hex'),
  '{"probe":true}'::jsonb, NULL
);
INSERT INTO core.entity (
  entity_id, entity_kind, lifecycle_state, created_at
) VALUES (
  'b3000000-0000-4000-8000-000000000001',
  'archive_object', 'active', '2026-08-14T00:00:00Z'
);
INSERT INTO core.archive_object (
  archive_object_id, operational_semantics_version, preferred_label,
  created_from_surface_ledger_id
) VALUES (
  'b3000000-0000-4000-8000-000000000001',
  'phase2b-p1-probe', 'P1 delivery probe object',
  'b4000000-0000-4000-8000-000000000001'
);

INSERT INTO rights.external_visual_reference (
  external_visual_reference_id, source_asset_id, source_record_id,
  source_field_or_json_pointer, source_occurrence_ordinal,
  provider_object_id, reference_fingerprint, created_at
)
SELECT
  ('b5000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid,
  'b1000000-0000-4000-8000-000000000001'::uuid,
  'b2000000-0000-4000-8000-000000000001'::uuid,
  '/probe/' || g::text, g, NULL,
  encode(sha256(convert_to('reference-' || g::text, 'UTF8')), 'hex'),
  '2026-08-14T00:00:00Z'
FROM generate_series(1, :scale::integer) AS g;

INSERT INTO rights.object_visual_reference (
  object_visual_reference_id, archive_object_id, external_visual_reference_id,
  reference_role, ordinal, acceptance_state, evidence_item_id
)
SELECT
  ('b6000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid,
  'b3000000-0000-4000-8000-000000000001'::uuid,
  ('b5000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid,
  'source_record_visual', g, 'proposed', NULL
FROM generate_series(1, :scale::integer) AS g;

INSERT INTO rights.rights_assessment (
  rights_assessment_id, subject_kind, assessed_state, reviewer_actor,
  rationale, assessed_at, supersedes_rights_assessment_id
)
SELECT
  ('b7000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid,
  'external_visual_reference', 'unknown', 'phase2b-p1-probe',
  'bounded P1 delivery diagnosis', '2026-08-14T00:01:00Z', NULL
FROM generate_series(1, :scale::integer) AS g;
INSERT INTO rights.rights_assessment_visual_reference (
  rights_assessment_id, external_visual_reference_id
)
SELECT
  ('b7000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid,
  ('b5000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid
FROM generate_series(1, :scale::integer) AS g;

INSERT INTO rights.provider_policy_evaluation (
  provider_policy_evaluation_id, object_visual_reference_id,
  evaluated_state, evaluator_actor, evaluated_at,
  supersedes_provider_policy_evaluation_id
)
SELECT
  ('b8000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid,
  ('b6000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid,
  'unknown', 'phase2b-p1-probe', '2026-08-14T00:02:00Z', NULL
FROM generate_series(1, :scale::integer) AS g;

INSERT INTO rights.delivery_assessment (
  delivery_assessment_id, object_visual_reference_id, attribution_bundle_id,
  delivery_mode, reason_code, assessor_actor, assessed_at,
  supersedes_delivery_assessment_id, machine_reason_code
)
SELECT
  ('b9000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid,
  ('b6000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid,
  NULL, 'blocked', 'RD-001', 'phase2b-p1-probe',
  '2026-08-14T00:03:00Z', NULL,
  rights.machine_reason_for_rule('RD-001')
FROM generate_series(1, :scale::integer) AS g;
INSERT INTO rights.delivery_rights_assessment (
  delivery_assessment_id, rights_assessment_id, evidence_role
)
SELECT
  ('b9000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid,
  ('b7000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid,
  'contextualises'
FROM generate_series(1, :scale::integer) AS g;
INSERT INTO rights.delivery_policy_evaluation (
  delivery_assessment_id, provider_policy_evaluation_id
)
SELECT
  ('b9000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid,
  ('b8000000-0000-4000-8000-' || lpad(g::text, 12, '0'))::uuid
FROM generate_series(1, :scale::integer) AS g;

ANALYZE rights.rights_assessment;
ANALYZE rights.rights_assessment_visual_reference;
ANALYZE rights.delivery_assessment;
ANALYZE rights.delivery_rights_assessment;
ANALYZE rights.delivery_policy_evaluation;

\echo P1_DELIVERY_POSTFIX_DIRECT_EXPLAIN_BEGIN scale=:scale
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS, TIMING, SUMMARY, FORMAT JSON)
WITH applicable(rights_assessment_id) AS (
  SELECT t.rights_assessment_id
  FROM rights.object_visual_reference b
  JOIN rights.rights_assessment_visual_reference t
    ON t.external_visual_reference_id=b.external_visual_reference_id
  JOIN rights.rights_assessment a
    ON a.rights_assessment_id=t.rights_assessment_id
   AND a.subject_kind='external_visual_reference'
  WHERE b.object_visual_reference_id=
    'b6000000-0000-4000-8000-000000000001'::uuid
)
SELECT EXISTS (
  SELECT 1 FROM applicable p
  JOIN rights.rights_assessment a
    ON a.rights_assessment_id=p.rights_assessment_id
  WHERE NOT EXISTS (
    SELECT 1 FROM rights.rights_assessment newer
    WHERE newer.supersedes_rights_assessment_id=a.rights_assessment_id)
    AND NOT EXISTS (
      SELECT 1 FROM rights.delivery_rights_assessment linked
      WHERE linked.delivery_assessment_id=
          'b9000000-0000-4000-8000-000000000001'::uuid
        AND linked.rights_assessment_id=a.rights_assessment_id)
);
\echo P1_DELIVERY_POSTFIX_DIRECT_EXPLAIN_END scale=:scale

SELECT clock_timestamp() AS group_started,
       pg_current_wal_lsn() AS group_wal_started
\gset
\echo P1_NAMED_CONSTRAINT_BEGIN constraint=rights.delivery_assessment_validation scale=:scale
SET CONSTRAINTS rights.delivery_assessment_validation IMMEDIATE;
SELECT :scale::bigint AS scale,
  extract(epoch FROM (clock_timestamp()-:'group_started'::timestamptz)) AS named_constraint_seconds,
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'group_wal_started'::pg_lsn) AS named_constraint_wal_bytes;
\echo P1_NAMED_CONSTRAINT_END constraint=rights.delivery_assessment_validation scale=:scale

SELECT clock_timestamp() AS group_started,
       pg_current_wal_lsn() AS group_wal_started
\gset
\echo P1_NAMED_CONSTRAINT_BEGIN constraint=rights.delivery_rights_validation scale=:scale
SET CONSTRAINTS rights.delivery_rights_validation IMMEDIATE;
SELECT :scale::bigint AS scale,
  extract(epoch FROM (clock_timestamp()-:'group_started'::timestamptz)) AS named_constraint_seconds,
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'group_wal_started'::pg_lsn) AS named_constraint_wal_bytes;
\echo P1_NAMED_CONSTRAINT_END constraint=rights.delivery_rights_validation scale=:scale

SELECT clock_timestamp() AS group_started,
       pg_current_wal_lsn() AS group_wal_started
\gset
\echo P1_NAMED_CONSTRAINT_BEGIN constraint=rights.delivery_policy_validation scale=:scale
SET CONSTRAINTS rights.delivery_policy_validation IMMEDIATE;
SELECT :scale::bigint AS scale,
  extract(epoch FROM (clock_timestamp()-:'group_started'::timestamptz)) AS named_constraint_seconds,
  pg_wal_lsn_diff(pg_current_wal_lsn(), :'group_wal_started'::pg_lsn) AS named_constraint_wal_bytes;
\echo P1_NAMED_CONSTRAINT_END constraint=rights.delivery_policy_validation scale=:scale

ROLLBACK;
