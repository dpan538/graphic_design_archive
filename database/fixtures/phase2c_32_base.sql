-- Phase 2C compact fixture. It extends the transaction-scoped Phase 2A base
-- to exactly 32 archive objects without reading staging or external data.
\ir phase2a_base.sql

DO $phase2c_fixture$
DECLARE i integer; object_id uuid; ledger_id uuid; record_id uuid;
BEGIN
  FOR i IN 3..32 LOOP
    object_id := ('21000000-0000-4000-8000-' || lpad(i::text, 12, '0'))::uuid;
    ledger_id := ('10000000-0000-4000-8000-' || lpad((100 + i)::text, 12, '0'))::uuid;
    record_id := ('10000000-0000-4000-8000-' || lpad((200 + i)::text, 12, '0'))::uuid;
    INSERT INTO raw.source_record (
      source_record_id, source_asset_id, record_ordinal, legacy_source_record_id,
      raw_value, raw_fingerprint, parsed_projection, parse_error_code
    ) VALUES (
      record_id, '10000000-0000-4000-8000-000000000001', i - 1,
      format('phase2c-fixture-%s', i),
      convert_to(format('{"id":"phase2c-%s"}', i), 'UTF8'),
      encode(sha256(convert_to(format('{"id":"phase2c-%s"}', i), 'UTF8')), 'hex'),
      jsonb_build_object('id', format('phase2c-%s', i)), NULL
    );
    INSERT INTO core.entity VALUES (object_id, 'archive_object', 'active', '2026-08-15T00:00:00Z', NULL);
    INSERT INTO core.archive_object (
      archive_object_id, operational_semantics_version, preferred_label,
      created_from_surface_ledger_id
    ) VALUES (object_id, 'operational-v49.0', format('Phase 2C fixture object %s', i), ledger_id);
    INSERT INTO raw.legacy_surface_ledger VALUES (
      ledger_id, '10000000-0000-4000-8000-000000000003', record_id,
      '10000000-0000-4000-8000-000000000001', i - 1,
      format('phase2c-surface-%s', i), format('phase2c-fixture-%s', i),
      encode(sha256(convert_to(format('{"id":"phase2c-%s"}', i), 'UTF8')), 'hex'),
      'accounted', object_id, 'PHASE2C_FIXTURE_ELIGIBLE'
    );
    INSERT INTO research.corpus_membership VALUES (
      '40000000-0000-4000-8000-000000000002', object_id, 'eligible',
      'PHASE2C_FIXTURE_ELIGIBLE', '30000000-0000-4000-8000-000000000003',
      'fixture-reviewer', '2026-08-15T00:00:00Z'
    );
  END LOOP;
END
$phase2c_fixture$;
