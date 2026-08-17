\set ON_ERROR_STOP on
\if :{?object_count}
\else
  \quit 64
\endif
\if :{?membership_count}
\else
  \quit 64
\endif
\if :{?scale_tag}
\else
  \quit 64
\endif

-- Deterministic, isolated scale source.  Every insert below names columns;
-- UUIDs, timestamps and source ordinals are deterministic and use the a* high
-- range, disjoint from the 32-object fixture's numeric namespace.
DO $catalog_preflight$
DECLARE v_actual text;
BEGIN
  SELECT string_agg(attname,',' ORDER BY attnum) INTO v_actual
  FROM pg_attribute WHERE attrelid='core.entity'::regclass
    AND attnum>0 AND NOT attisdropped;
  IF v_actual <> 'entity_id,entity_kind,lifecycle_state,created_at,withdrawn_at' THEN
    RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='PHASE2S_SCALE_CATALOG_ENTITY_COLUMNS_MISMATCH';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid='provenance.assignment_folder_membership'::regclass
    AND attname='member_ordinal' AND NOT attisdropped)
     OR NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid='provenance.assignment_review_decision'::regclass
    AND attname='supersedes_decision_id' AND NOT attisdropped) THEN
    RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='PHASE2S_SCALE_CATALOG_ASSIGNMENT_COLUMNS_MISMATCH';
  END IF;
END
$catalog_preflight$;
SELECT set_config('gda_phase2s.object_count', :'object_count', true);
SELECT set_config('gda_phase2s.membership_count', :'membership_count', true);
DO $shape$
DECLARE v_objects integer:=current_setting('gda_phase2s.object_count')::integer;
  v_memberships integer:=current_setting('gda_phase2s.membership_count')::integer;
BEGIN
  IF v_objects NOT IN (32,1000,2000,4000,8000,15923)
    OR v_memberships <> 3*v_objects + (CASE
      WHEN v_objects=15923 THEN 213
      ELSE least(v_objects,107)
    END) THEN
    RAISE EXCEPTION USING ERRCODE='22023', MESSAGE='PHASE2S_SCALE_SHAPE_NOT_AUTHORIZED';
  END IF;
END
$shape$;

INSERT INTO raw.source_asset(
  source_asset_id,authority,logical_name,sha256,byte_length,raw_bytes,media_type,received_at
) SELECT 'a0000000-0000-4000-8000-000000000001','canonical_migration_input',
  'phase2s-scale-'||:'scale_tag'||'.json',
  encode(sha256(convert_to('phase2s-scale-'||:'scale_tag','UTF8')),'hex'),
  octet_length(convert_to('phase2s-scale-'||:'scale_tag','UTF8')),
  convert_to('phase2s-scale-'||:'scale_tag','UTF8'),'application/json','2026-08-16T00:00:00Z';
INSERT INTO raw.mapping_version(
  mapping_version_id,version_token,specification_sha256,parser_version,delimiter_policy,created_at
) VALUES ('a0000000-0000-4000-8000-000000000002','phase2s-scale-map',repeat('1',64),
  'phase2s-scale-parser','preserve_no_automatic_split','2026-08-16T00:00:00Z');
INSERT INTO raw.migration_batch(
  migration_batch_id,batch_token,canonical_input_asset_id,mapping_version_id,input_sha256,started_at,completed_at
) SELECT 'a0000000-0000-4000-8000-000000000003','phase2s-scale-batch',
  'a0000000-0000-4000-8000-000000000001','a0000000-0000-4000-8000-000000000002',
  sha256,'2026-08-16T00:00:00Z',NULL FROM raw.source_asset
  WHERE source_asset_id='a0000000-0000-4000-8000-000000000001';
INSERT INTO release.validation_profile(
  validation_profile_id,boundary_kind,profile_token,profile_sha256,approved_at
) VALUES ('a9000000-0000-4000-8000-000000000001','research','model-v49.0',repeat('2',64),'2026-08-16T00:00:00Z');
INSERT INTO release.validation_profile_requirement(
  validation_profile_id,receipt_kind,requirement_ordinal
)
SELECT 'a9000000-0000-4000-8000-000000000001'::uuid,k,ord::integer
FROM unnest(ARRAY[
  'research_frozen_asset_authority','research_migration_query_identity','research_population_and_count_parity',
  'research_corpus_missingness_concentration','research_fk_orphan_integrity','research_predicate_relation_epistemic_registry',
  'research_claim_projection_eligibility','research_unknown_relation_isolation','research_projection_fingerprint',
  'research_deterministic_asset_inventory','research_role_grant_security'
]::release.validation_receipt_kind[]) WITH ORDINALITY AS t(k,ord);
INSERT INTO provenance.source_document(
  source_document_id,source_kind,public_citation,created_at
) VALUES ('a3000000-0000-4000-8000-000000000001','synthetic_fixture','Phase 2C-S deterministic scale citation','2026-08-16T00:00:00Z');
INSERT INTO provenance.source_version(
  source_version_id,source_document_id,version_token,content_sha256,byte_length,supersedes_source_version_id,created_at,source_asset_id
) VALUES ('a3000000-0000-4000-8000-000000000002','a3000000-0000-4000-8000-000000000001',
  'phase2s-scale-source',repeat('3',64),16,NULL,'2026-08-16T00:00:00Z','a0000000-0000-4000-8000-000000000001');
INSERT INTO raw.source_record(
  source_record_id,source_asset_id,record_ordinal,legacy_source_record_id,raw_value,raw_fingerprint,parsed_projection,parse_error_code
) VALUES ('a1000000-0000-4000-8000-000000000001','a0000000-0000-4000-8000-000000000001',999999,
  'phase2s-scale-evidence',convert_to('{"id":"phase2s-scale-evidence"}','UTF8'),
  encode(sha256(convert_to('{"id":"phase2s-scale-evidence"}','UTF8')),'hex'),
  jsonb_build_object('id','phase2s-scale-evidence'),NULL);
INSERT INTO provenance.evidence_item(
  evidence_item_id,source_version_id,source_record_id,locator_scheme,internal_locator,span_start,span_end,
  content_sha256,stable_citation,supersedes_evidence_item_id,created_at,source_asset_id
) VALUES ('a3000000-0000-4000-8000-000000000003','a3000000-0000-4000-8000-000000000002',
  'a1000000-0000-4000-8000-000000000001','json_pointer','/scale/evidence',0,1,repeat('4',64),
  'Phase 2C-S deterministic scale citation',NULL,'2026-08-16T00:00:00Z','a0000000-0000-4000-8000-000000000001');

INSERT INTO research.corpus(corpus_id,corpus_token,label,created_at)
VALUES ('a4000000-0000-4000-8000-000000000001','phase2s-scale-corpus','Phase 2C-S Scale Corpus','2026-08-16T00:00:00Z');
INSERT INTO research.corpus_version(
  corpus_version_id,corpus_id,version_token,policy_version,policy_sha256,population_frame,created_at
) VALUES ('a4000000-0000-4000-8000-000000000002','a4000000-0000-4000-8000-000000000001',
  'phase2s-scale-corpus-v1','phase2s-scale-policy',repeat('5',64),'deterministic scale public objects','2026-08-16T00:00:00Z');
INSERT INTO research.launch_snapshot_policy_v3(
  launch_snapshot_policy_id,policy_token,public_corpus_version_id,projection_query_pack_sha256,
  selection_policy_sha256,registry_corpus_policy_sha256,created_at
) VALUES ('a8000000-0000-4000-8000-000000000010','phase2s-scale-policy-v3',
  'a4000000-0000-4000-8000-000000000002',repeat('a',64),repeat('b',64),repeat('c',64),'2026-08-16T00:00:00Z');
INSERT INTO research.public_source_citation_allowlist_v3(source_asset_id,citation_label,created_at)
VALUES ('a0000000-0000-4000-8000-000000000001','Phase 2C-S deterministic scale citation','2026-08-16T00:00:00Z');
INSERT INTO research.folder_type_registry(folder_type_code,type_label,type_sort_ordinal)
VALUES ('region','Region',0);
INSERT INTO research.folder(folder_id,folder_token,label,created_at) VALUES
  ('a8000000-0000-4000-8000-000000000001','scale-region-alpha','Scale Region Alpha','2026-08-16T00:00:00Z'),
  ('a8000000-0000-4000-8000-000000000002','scale-region-beta','Scale Region Beta','2026-08-16T00:00:00Z'),
  ('a8000000-0000-4000-8000-000000000003','scale-region-gamma','Scale Region Gamma','2026-08-16T00:00:00Z'),
  ('a8000000-0000-4000-8000-000000000004','scale-region-delta','Scale Region Delta','2026-08-16T00:00:00Z');
INSERT INTO research.folder_publication_metadata(
  folder_id,folder_type_code,slug,scope_note,folder_sort_ordinal
) VALUES
  ('a8000000-0000-4000-8000-000000000001','region','alpha','Deterministic scale alpha',0),
  ('a8000000-0000-4000-8000-000000000002','region','beta','Deterministic scale beta',1),
  ('a8000000-0000-4000-8000-000000000003','region','gamma','Deterministic scale gamma',2),
  ('a8000000-0000-4000-8000-000000000004','region','delta','Deterministic scale delta',3);

WITH n AS (SELECT i,
  ('a2000000-0000-4000-8000-'||lpad((1000000+i)::text,12,'0'))::uuid AS object_id,
  ('a1000000-0000-4000-8000-'||lpad((1000000+i)::text,12,'0'))::uuid AS record_id,
  ('a5000000-0000-4000-8000-'||lpad((1000000+i)::text,12,'0'))::uuid AS ledger_id
  FROM generate_series(1,:'object_count'::integer) AS g(i))
INSERT INTO raw.source_record(
  source_record_id,source_asset_id,record_ordinal,legacy_source_record_id,raw_value,raw_fingerprint,parsed_projection,parse_error_code
)
SELECT record_id,'a0000000-0000-4000-8000-000000000001',1000000+i,'phase2s-scale-record-'||i,
  convert_to(jsonb_build_object('id',i)::text,'UTF8'),
  encode(sha256(convert_to(jsonb_build_object('id',i)::text,'UTF8')),'hex'),jsonb_build_object('id',i),NULL FROM n;
WITH n AS (SELECT i,
  ('a2000000-0000-4000-8000-'||lpad((1000000+i)::text,12,'0'))::uuid AS object_id
  FROM generate_series(1,:'object_count'::integer) AS g(i))
INSERT INTO core.entity(entity_id,entity_kind,lifecycle_state,created_at,withdrawn_at)
SELECT object_id,'archive_object','active','2026-08-16T00:00:00Z',NULL FROM n;
WITH n AS (SELECT i,
  ('a2000000-0000-4000-8000-'||lpad((1000000+i)::text,12,'0'))::uuid AS object_id,
  ('a5000000-0000-4000-8000-'||lpad((1000000+i)::text,12,'0'))::uuid AS ledger_id
  FROM generate_series(1,:'object_count'::integer) AS g(i))
INSERT INTO core.archive_object(
  archive_object_id,operational_semantics_version,preferred_label,created_from_surface_ledger_id
) SELECT object_id,'operational-v49.0','Phase 2S scale object '||i,ledger_id FROM n;
WITH n AS (SELECT i,
  ('a1000000-0000-4000-8000-'||lpad((1000000+i)::text,12,'0'))::uuid AS record_id,
  ('a2000000-0000-4000-8000-'||lpad((1000000+i)::text,12,'0'))::uuid AS object_id,
  ('a5000000-0000-4000-8000-'||lpad((1000000+i)::text,12,'0'))::uuid AS ledger_id
  FROM generate_series(1,:'object_count'::integer) AS g(i))
INSERT INTO raw.legacy_surface_ledger(
  legacy_surface_ledger_id,migration_batch_id,source_record_id,canonical_input_asset_id,input_ordinal,surface_id,
  legacy_source_record_id,source_fingerprint,import_disposition,archive_object_id,reason_code
) SELECT ledger_id,'a0000000-0000-4000-8000-000000000003',record_id,
  'a0000000-0000-4000-8000-000000000001',1000000+i,'phase2s-scale-surface-'||i,
  'phase2s-scale-record-'||i,
  encode(sha256(convert_to(jsonb_build_object('id',i)::text,'UTF8')),'hex'),'accounted',object_id,'SCALE_PUBLIC' FROM n;
WITH n AS (SELECT i,
  ('a2000000-0000-4000-8000-'||lpad((1000000+i)::text,12,'0'))::uuid AS object_id
  FROM generate_series(1,:'object_count'::integer) AS g(i))
INSERT INTO research.corpus_membership(
  corpus_version_id,archive_object_id,disposition,reason_code,evidence_item_id,decided_by,decided_at
) SELECT 'a4000000-0000-4000-8000-000000000002',object_id,'eligible','SCALE_PUBLIC',
  'a3000000-0000-4000-8000-000000000003','fixture-reviewer','2026-08-16T00:00:00Z' FROM n;

WITH m AS (
  SELECT i,folder_no,
    ('a2000000-0000-4000-8000-'||lpad((1000000+i)::text,12,'0'))::uuid AS object_id,
    ('a6000000-0000-4000-8000-'||lpad((1000000 + (folder_no*200000) + i)::text,12,'0'))::uuid AS assignment_id
  FROM generate_series(1,:'object_count'::integer) g(i) CROSS JOIN generate_series(1,3) folder_no
  UNION ALL
  SELECT i,4,
    ('a2000000-0000-4000-8000-'||lpad((1000000+i)::text,12,'0'))::uuid,
    ('a6000000-0000-4000-8000-'||lpad((1000000 + 4*200000 + i)::text,12,'0'))::uuid
  FROM generate_series(1,(:'membership_count'::integer - 3*:'object_count'::integer)) g(i)
)
INSERT INTO provenance.canonical_assignment(
  canonical_assignment_id,assignment_kind,status,supersedes_assignment_id,created_at
) SELECT assignment_id,'folder_membership','accepted',NULL,'2026-08-16T00:00:00Z' FROM m;
WITH m AS (
  SELECT i,folder_no,
    ('a2000000-0000-4000-8000-'||lpad((1000000+i)::text,12,'0'))::uuid AS object_id,
    ('a6000000-0000-4000-8000-'||lpad((1000000 + (folder_no*200000) + i)::text,12,'0'))::uuid AS assignment_id
  FROM generate_series(1,:'object_count'::integer) g(i) CROSS JOIN generate_series(1,3) folder_no
  UNION ALL
  SELECT i,4,
    ('a2000000-0000-4000-8000-'||lpad((1000000+i)::text,12,'0'))::uuid,
    ('a6000000-0000-4000-8000-'||lpad((1000000 + 4*200000 + i)::text,12,'0'))::uuid
  FROM generate_series(1,(:'membership_count'::integer - 3*:'object_count'::integer)) g(i)
)
INSERT INTO provenance.assignment_folder_membership(
  canonical_assignment_id,folder_id,archive_object_id,membership_role,member_ordinal
) SELECT assignment_id,('a8000000-0000-4000-8000-'||lpad(folder_no::text,12,'0'))::uuid,
  object_id,'primary',i-1 FROM m;
WITH m AS (
  SELECT i,folder_no,
    ('a6000000-0000-4000-8000-'||lpad((1000000 + (folder_no*200000) + i)::text,12,'0'))::uuid AS assignment_id
  FROM generate_series(1,:'object_count'::integer) g(i) CROSS JOIN generate_series(1,3) folder_no
  UNION ALL SELECT i,4,
    ('a6000000-0000-4000-8000-'||lpad((1000000 + 4*200000 + i)::text,12,'0'))::uuid
  FROM generate_series(1,(:'membership_count'::integer - 3*:'object_count'::integer)) g(i)
)
INSERT INTO provenance.assignment_review_decision(
  assignment_review_decision_id,canonical_assignment_id,outcome,reviewer_actor,rationale,supersedes_decision_id,decided_at
) SELECT ('a7000000-0000-4000-8000-'||lpad((1000000+row_number() OVER (ORDER BY assignment_id))::text,12,'0'))::uuid,
  assignment_id,'accept','fixture-reviewer','Deterministic scale acceptance',NULL,'2026-08-16T00:00:00Z' FROM m;
INSERT INTO provenance.assignment_decision_evidence(
  assignment_review_decision_id,evidence_item_id,evidence_role
)
SELECT assignment_review_decision_id,'a3000000-0000-4000-8000-000000000003','supports'
FROM provenance.assignment_review_decision
WHERE assignment_review_decision_id::text LIKE 'a7000000-0000-4000-8000-%';
