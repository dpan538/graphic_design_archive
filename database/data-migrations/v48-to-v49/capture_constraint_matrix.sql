-- Read-only Phase 2B-P catalog inventory.  Run with psql -X -A -F $'\t'.
WITH expected_rows(table_schema, table_name, expected_rows) AS (
  VALUES
    ('raw','source_asset',1::bigint),
    ('raw','mapping_version',1),
    ('raw','migration_batch',1),
    ('raw','source_record',15923),
    ('raw','field_literal',3559820),
    ('core','entity',15923),
    ('core','archive_object',15923),
    ('raw','legacy_surface_ledger',15923),
    ('provenance','object_source_record',15923),
    ('core','legacy_identity',15923),
    ('research','folder',185),
    ('provenance','canonical_assignment',47982),
    ('provenance','assignment_folder_membership',47982),
    ('research','trace_node',15923),
    ('research','object_trace_node',15923),
    ('research','corpus',1),
    ('research','corpus_version',1),
    ('research','corpus_membership',15923),
    ('raw','fail_closed_delta',7928),
    ('rights','external_visual_reference',15788),
    ('rights','object_visual_reference',15788),
    ('rights','visual_locator',15790),
    ('rights','rights_observation',15788),
    ('rights','rights_observation_visual_reference',15788),
    ('rights','rights_assessment',15788),
    ('rights','rights_assessment_visual_reference',15788),
    ('rights','rights_assessment_observation',15788),
    ('rights','provider_policy_evaluation',15788),
    ('rights','delivery_assessment',15788),
    ('rights','delivery_rights_assessment',15788),
    ('rights','delivery_policy_evaluation',15788),
    ('rights','legacy_visual_surface_disposition',15923),
    ('rights','legacy_visual_surface_classification',15923)
),
fk_rows AS (
  SELECT
    n.nspname::text AS table_schema,
    rel.relname::text AS table_name,
    'FOREIGN_KEY'::text AS catalog_kind,
    c.conname::text AS constraint_name,
    pg_get_constraintdef(c.oid, true)::text AS definition,
    COALESCE((
      SELECT string_agg(a.attname, ',' ORDER BY key.ord)
      FROM unnest(c.conkey) WITH ORDINALITY key(attnum, ord)
      JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=key.attnum
    ), '') AS columns,
    rn.nspname::text AS referenced_schema,
    rrel.relname::text AS referenced_table,
    COALESCE((
      SELECT string_agg(a.attname, ',' ORDER BY key.ord)
      FROM unnest(c.confkey) WITH ORDINALITY key(attnum, ord)
      JOIN pg_attribute a ON a.attrelid=c.confrelid AND a.attnum=key.attnum
    ), '') AS referenced_columns,
    c.condeferrable AS deferrable,
    c.condeferred AS initially_deferred,
    ''::text AS trigger_function,
    'INSERT,UPDATE'::text AS trigger_events,
    COALESCE(er.expected_rows,0)::bigint AS expected_event_count,
    COALESCE((
      SELECT string_agg(pg_get_indexdef(i.indexrelid), ' || ' ORDER BY i.indexrelid)
      FROM pg_index i WHERE i.indrelid=c.conrelid AND i.indisvalid
    ), '') AS table_indexes,
    COALESCE((
      SELECT string_agg(pg_get_indexdef(i.indexrelid), ' || ' ORDER BY i.indexrelid)
      FROM pg_index i WHERE i.indrelid=c.confrelid AND i.indisvalid
    ), '') AS referenced_indexes,
    EXISTS (
      SELECT 1 FROM pg_index i
      WHERE i.indrelid=c.conrelid AND i.indisvalid
        AND i.indnkeyatts >= cardinality(c.conkey)
        AND NOT EXISTS (
          SELECT 1 FROM unnest(c.conkey) WITH ORDINALITY key(attnum, ord)
          WHERE i.indkey[key.ord::integer - 1] <> key.attnum
        )
    ) AS child_fk_leading_index_covered,
    'INDEX_PROBE'::text AS pre_remediation_complexity,
    CASE WHEN COALESCE(er.expected_rows,0)>0 THEN 'P1' ELSE 'P2' END::text AS risk_priority
  FROM pg_constraint c
  JOIN pg_class rel ON rel.oid=c.conrelid
  JOIN pg_namespace n ON n.oid=rel.relnamespace
  JOIN pg_class rrel ON rrel.oid=c.confrelid
  JOIN pg_namespace rn ON rn.oid=rrel.relnamespace
  LEFT JOIN expected_rows er ON er.table_schema=n.nspname AND er.table_name=rel.relname
  WHERE c.contype='f'
    AND n.nspname=ANY(ARRAY['raw','core','provenance','research','rights','workflow','release','audit'])
),
trigger_rows AS (
  SELECT
    n.nspname::text AS table_schema,
    rel.relname::text AS table_name,
    'CONSTRAINT_TRIGGER'::text AS catalog_kind,
    t.tgname::text AS constraint_name,
    pg_get_triggerdef(t.oid, true)::text AS definition,
    ''::text AS columns,
    ''::text AS referenced_schema,
    ''::text AS referenced_table,
    ''::text AS referenced_columns,
    t.tgdeferrable AS deferrable,
    t.tginitdeferred AS initially_deferred,
    pn.nspname||'.'||p.proname||'('||pg_get_function_identity_arguments(p.oid)||')' AS trigger_function,
    concat_ws(',',
      CASE WHEN (t.tgtype & 4)<>0 THEN 'INSERT' END,
      CASE WHEN (t.tgtype & 16)<>0 THEN 'UPDATE' END,
      CASE WHEN (t.tgtype & 8)<>0 THEN 'DELETE' END,
      CASE WHEN (t.tgtype & 32)<>0 THEN 'TRUNCATE' END
    ) AS trigger_events,
    COALESCE(er.expected_rows,0)::bigint AS expected_event_count,
    COALESCE((
      SELECT string_agg(pg_get_indexdef(i.indexrelid), ' || ' ORDER BY i.indexrelid)
      FROM pg_index i WHERE i.indrelid=t.tgrelid AND i.indisvalid
    ), '') AS table_indexes,
    ''::text AS referenced_indexes,
    NULL::boolean AS child_fk_leading_index_covered,
    CASE
      WHEN t.tgname IN (
        'rights_assessment_one_current_leaf',
        'delivery_assessment_validation',
        'delivery_rights_validation',
        'delivery_policy_validation'
      ) THEN 'THETA_N_SQUARED'
      ELSE 'ROW_EVENT_FUNCTION'
    END::text AS pre_remediation_complexity,
    CASE
      WHEN t.tgname IN (
        'rights_assessment_one_current_leaf',
        'delivery_assessment_validation',
        'delivery_rights_validation',
        'delivery_policy_validation'
      ) THEN 'P0'
      WHEN COALESCE(er.expected_rows,0)>0 THEN 'P1'
      ELSE 'P2'
    END::text AS risk_priority
  FROM pg_trigger t
  JOIN pg_class rel ON rel.oid=t.tgrelid
  JOIN pg_namespace n ON n.oid=rel.relnamespace
  JOIN pg_proc p ON p.oid=t.tgfoid
  JOIN pg_namespace pn ON pn.oid=p.pronamespace
  LEFT JOIN expected_rows er ON er.table_schema=n.nspname AND er.table_name=rel.relname
  WHERE NOT t.tgisinternal AND t.tgdeferrable
    AND n.nspname=ANY(ARRAY['raw','core','provenance','research','rights','workflow','release','audit'])
)
SELECT * FROM fk_rows
UNION ALL
SELECT * FROM trigger_rows
ORDER BY risk_priority, table_schema, table_name, catalog_kind, constraint_name;
