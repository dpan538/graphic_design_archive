-- Transaction-scoped Phase 2C-S fixture.  It contains exactly 32 eligible
-- public objects, four folders with eight accepted memberships each, no TRACE
-- rows, no visual-rights rows, and one separate held/proposed sentinel.
-- It is intentionally independent of Phase 2A's positive visual control.

INSERT INTO raw.source_asset(source_asset_id,authority,logical_name,sha256,byte_length,raw_bytes,media_type,received_at)
VALUES ('10000000-0000-4000-8000-000000000001','canonical_migration_input','phase2s-candidate.json',
  encode(sha256(convert_to('phase2s-candidate','UTF8')),'hex'),octet_length(convert_to('phase2s-candidate','UTF8')),
  convert_to('phase2s-candidate','UTF8'),'application/json','2026-08-16T00:00:00Z');
INSERT INTO raw.mapping_version VALUES ('10000000-0000-4000-8000-000000000002','phase2s-mapping-v1',repeat('1',64),'phase2s-parser','preserve_no_automatic_split','2026-08-16T00:00:00Z');
INSERT INTO raw.migration_batch VALUES ('10000000-0000-4000-8000-000000000003','phase2s-batch-v1','10000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000002',
  encode(sha256(convert_to('phase2s-candidate','UTF8')),'hex'),'2026-08-16T00:00:00Z',NULL);

INSERT INTO release.validation_profile VALUES ('90000000-0000-4000-8000-000000000001','research','model-v49.0',repeat('2',64),'2026-08-16T00:00:00Z');
INSERT INTO release.validation_profile_requirement(validation_profile_id,receipt_kind,requirement_ordinal)
SELECT '90000000-0000-4000-8000-000000000001'::uuid,k,ord::integer
FROM unnest(ARRAY[
  'research_frozen_asset_authority','research_migration_query_identity','research_population_and_count_parity',
  'research_corpus_missingness_concentration','research_fk_orphan_integrity','research_predicate_relation_epistemic_registry',
  'research_claim_projection_eligibility','research_unknown_relation_isolation','research_projection_fingerprint',
  'research_deterministic_asset_inventory','research_role_grant_security'
]::release.validation_receipt_kind[]) WITH ORDINALITY AS t(k,ord);

INSERT INTO provenance.source_document(source_document_id,source_kind,public_citation,created_at)
VALUES ('30000000-0000-4000-8000-000000000001','synthetic_fixture','Phase 2C-S synthetic public citation','2026-08-16T00:00:00Z');
INSERT INTO provenance.source_version(source_version_id,source_document_id,version_token,content_sha256,byte_length,supersedes_source_version_id,created_at,source_asset_id)
VALUES ('30000000-0000-4000-8000-000000000002','30000000-0000-4000-8000-000000000001','phase2s-source-v1',repeat('3',64),16,NULL,'2026-08-16T00:00:00Z','10000000-0000-4000-8000-000000000001');
INSERT INTO raw.source_record(source_record_id,source_asset_id,record_ordinal,legacy_source_record_id,raw_value,raw_fingerprint,parsed_projection,parse_error_code)
VALUES ('10000000-0000-4000-8000-000000000004','10000000-0000-4000-8000-000000000001',100,'phase2s-evidence',convert_to('{"id":"phase2s-evidence"}','UTF8'),
  encode(sha256(convert_to('{"id":"phase2s-evidence"}','UTF8')),'hex'),jsonb_build_object('id','phase2s-evidence'),NULL);
INSERT INTO provenance.evidence_item VALUES ('30000000-0000-4000-8000-000000000003','30000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000004',
  'json_pointer','/fixture/evidence',0,1,repeat('4',64),'Phase 2C-S fixture citation',NULL,'2026-08-16T00:00:00Z','10000000-0000-4000-8000-000000000001');

DO $phase2s_objects$
DECLARE i integer; v_object uuid; v_record uuid; v_ledger uuid;
BEGIN
  FOR i IN 1..33 LOOP
    v_object:=('20000000-0000-4000-8000-'||lpad((1000+i)::text,12,'0'))::uuid;
    v_record:=('10000000-0000-4000-8000-'||lpad((1000+i)::text,12,'0'))::uuid;
    v_ledger:=('10000000-0000-4000-8000-'||lpad((2000+i)::text,12,'0'))::uuid;
    INSERT INTO raw.source_record VALUES(v_record,'10000000-0000-4000-8000-000000000001',i,
      'phase2s-record-'||i,convert_to(jsonb_build_object('id',i)::text,'UTF8'),
      encode(sha256(convert_to(jsonb_build_object('id',i)::text,'UTF8')),'hex'),jsonb_build_object('id',i),NULL);
    INSERT INTO core.entity VALUES(v_object,'archive_object','active','2026-08-16T00:00:00Z',NULL);
    INSERT INTO core.archive_object(archive_object_id,operational_semantics_version,preferred_label,created_from_surface_ledger_id)
    VALUES(v_object,'operational-v49.0','Phase 2S object '||i,v_ledger);
    INSERT INTO raw.legacy_surface_ledger VALUES(v_ledger,'10000000-0000-4000-8000-000000000003',v_record,'10000000-0000-4000-8000-000000000001',i,
      'phase2s-surface-'||i,'phase2s-record-'||i,encode(sha256(convert_to(jsonb_build_object('id',i)::text,'UTF8')),'hex'),
      'accounted'::raw.import_disposition,v_object,
      CASE WHEN i=33 THEN 'HELD_SENTINEL' ELSE 'PUBLIC_FIXTURE' END);
  END LOOP;
END $phase2s_objects$;

INSERT INTO research.corpus VALUES ('40000000-0000-4000-8000-000000000001','phase2s-corpus','Phase 2C-S Corpus','2026-08-16T00:00:00Z');
INSERT INTO research.corpus_version VALUES ('40000000-0000-4000-8000-000000000002','40000000-0000-4000-8000-000000000001','phase2s-corpus-v1','phase2s-policy-v1',repeat('5',64),'synthetic phase2s public objects','2026-08-16T00:00:00Z');
INSERT INTO research.corpus_membership
SELECT '40000000-0000-4000-8000-000000000002',('20000000-0000-4000-8000-'||lpad((1000+i)::text,12,'0'))::uuid,
  CASE WHEN i=33 THEN 'held'::research.membership_disposition ELSE 'eligible'::research.membership_disposition END,
  CASE WHEN i=33 THEN 'HELD_SENTINEL' ELSE 'PUBLIC_FIXTURE' END,'30000000-0000-4000-8000-000000000003','fixture-reviewer','2026-08-16T00:00:00Z'
FROM generate_series(1,33) AS i;

INSERT INTO research.launch_snapshot_policy_v3 VALUES ('80000000-0000-4000-8000-000000000010','phase2s-policy-v3','40000000-0000-4000-8000-000000000002',repeat('a',64),repeat('b',64),repeat('c',64),'2026-08-16T00:00:00Z');
INSERT INTO research.public_source_citation_allowlist_v3 VALUES ('10000000-0000-4000-8000-000000000001','Phase 2C-S synthetic public citation','2026-08-16T00:00:00Z');
INSERT INTO research.folder_type_registry VALUES ('region','Region',0);
INSERT INTO research.folder VALUES
  ('80000000-0000-4000-8000-000000000001','region-alpha','Region Alpha','2026-08-16T00:00:00Z'),
  ('80000000-0000-4000-8000-000000000002','region-beta','Region Beta','2026-08-16T00:00:00Z'),
  ('80000000-0000-4000-8000-000000000003','region-gamma','Region Gamma','2026-08-16T00:00:00Z'),
  ('80000000-0000-4000-8000-000000000004','region-delta','Region Delta','2026-08-16T00:00:00Z');
INSERT INTO research.folder_publication_metadata VALUES
  ('80000000-0000-4000-8000-000000000001','region','alpha','Synthetic region scope alpha',0),
  ('80000000-0000-4000-8000-000000000002','region','beta','Synthetic region scope beta',1),
  ('80000000-0000-4000-8000-000000000003','region','gamma','Synthetic region scope gamma',2),
  ('80000000-0000-4000-8000-000000000004','region','delta','Synthetic region scope delta',3);

DO $phase2s_memberships$
DECLARE i integer; v_object uuid; v_folder uuid; v_assignment uuid; v_decision uuid;
BEGIN
  FOR i IN 1..32 LOOP
    v_object:=('20000000-0000-4000-8000-'||lpad((1000+i)::text,12,'0'))::uuid;
    v_folder:=('80000000-0000-4000-8000-'||lpad((((i-1)/8)+1)::text,12,'0'))::uuid;
    v_assignment:=('60000000-0000-4000-8000-'||lpad((1000+i)::text,12,'0'))::uuid;
    v_decision:=('70000000-0000-4000-8000-'||lpad((1000+i)::text,12,'0'))::uuid;
    INSERT INTO provenance.canonical_assignment VALUES(v_assignment,'folder_membership','accepted',NULL,'2026-08-16T00:00:00Z');
    INSERT INTO provenance.assignment_folder_membership VALUES(v_assignment,v_folder,v_object,'primary',(i-1)%8);
    INSERT INTO provenance.assignment_review_decision VALUES(v_decision,v_assignment,'accept','fixture-reviewer','Synthetic accepted folder membership',NULL,'2026-08-16T00:00:00Z');
    INSERT INTO provenance.assignment_decision_evidence VALUES(v_decision,'30000000-0000-4000-8000-000000000003','supports');
  END LOOP;
  INSERT INTO provenance.canonical_assignment VALUES('60000000-0000-4000-8000-000000009999','folder_membership','proposed',NULL,'2026-08-16T00:00:00Z');
  INSERT INTO provenance.assignment_folder_membership VALUES('60000000-0000-4000-8000-000000009999','80000000-0000-4000-8000-000000000001',
    '20000000-0000-4000-8000-000000001033','held_sentinel',99);
END $phase2s_memberships$;
