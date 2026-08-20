\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

-- Forward-only v5 closure.  The release membership parity comparison now
-- binds the complete published tuple, including member_ordinal.  This both
-- strengthens reconciliation and lets the existing folder-order index avoid
-- the quadratic prefix-only merge observed at 1k/2k.
CREATE OR REPLACE FUNCTION release.build_research_launch_snapshot_v5_internal(
  p_release_id uuid,p_migration_batch_id uuid,p_policy_id uuid,
  p_candidate_event_id uuid,p_candidate_event_sha256 core.sha256_hex,
  p_fault_point text DEFAULT NULL
) RETURNS core.sha256_hex LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog AS $function$
DECLARE
  v_asset_id uuid; v_asset_sha core.sha256_hex; v_mapping_sha core.sha256_hex;
  v_corpus_version_id uuid; v_query_sha core.sha256_hex; v_selection_sha core.sha256_hex;
  v_registry_sha core.sha256_hex; v_source_sha core.sha256_hex; v_component_sha core.sha256_hex;
  v_receipt_sha core.sha256_hex; v_fingerprint core.sha256_hex;
BEGIN
  IF p_fault_point IS NOT NULL AND p_fault_point NOT IN (
    'after_release_objects','after_folders','after_memberships',
    'after_component_hashes','after_build_receipt','before_candidate_transition'
  ) THEN RAISE EXCEPTION USING ERRCODE='22023', MESSAGE='RESEARCH_LAUNCH_V5_UNKNOWN_FAULT_POINT'; END IF;
  IF current_setting('transaction_isolation') <> 'serializable' THEN
    RAISE EXCEPTION USING ERRCODE='25001', MESSAGE='RESEARCH_LAUNCH_V5_BUILDER_REQUIRES_SERIALIZABLE';
  END IF;
  -- The closure environment permits exactly one builder writer.  A global
  -- transaction mutex prevents unrelated releases from forming an SSI pivot
  -- through page-level predicate locks on the shared projection indexes.
  -- The release-key lock remains the identity-specific correctness boundary.
  PERFORM pg_advisory_xact_lock(
    hashtextextended('release-snapshot-v5-builder',49024));
  PERFORM pg_advisory_xact_lock(hashtextextended(p_release_id::text,49024));
  PERFORM 1 FROM release.research_release WHERE research_release_id=p_release_id
    AND release_state='draft' FOR UPDATE;
  IF NOT FOUND OR EXISTS (SELECT 1 FROM release.research_launch_build_receipt_v3 WHERE research_release_id=p_release_id)
    OR EXISTS (SELECT 1 FROM release.research_launch_protocol_v4 WHERE research_release_id=p_release_id)
    OR EXISTS (SELECT 1 FROM release.research_launch_protocol_v5 WHERE research_release_id=p_release_id)
    OR EXISTS (SELECT 1 FROM release.research_release_object WHERE research_release_id=p_release_id) THEN
    RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='RESEARCH_LAUNCH_V5_REQUIRES_EMPTY_FRESH_DRAFT';
  END IF;
  SELECT b.canonical_input_asset_id,b.input_sha256,m.specification_sha256,
    p.public_corpus_version_id,p.projection_query_pack_sha256,p.selection_policy_sha256,
    p.registry_corpus_policy_sha256
  INTO v_asset_id,v_asset_sha,v_mapping_sha,v_corpus_version_id,v_query_sha,v_selection_sha,v_registry_sha
  FROM raw.migration_batch b JOIN raw.mapping_version m ON m.mapping_version_id=b.mapping_version_id
  JOIN research.launch_snapshot_policy_v3 p ON p.launch_snapshot_policy_id=p_policy_id
  WHERE b.migration_batch_id=p_migration_batch_id;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='RESEARCH_LAUNCH_V5_SOURCE_IDENTITY_NOT_RESOLVABLE'; END IF;
  IF NOT EXISTS (SELECT 1 FROM research.public_source_citation_allowlist_v3 WHERE source_asset_id=v_asset_id) THEN
    RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='RESEARCH_LAUNCH_V5_PUBLIC_CITATION_ALLOWLIST_MISSING';
  END IF;
  IF EXISTS (SELECT 1 FROM research.semantic_relation WHERE status='accepted') THEN
    RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='TRACE_NONEMPTY_PROJECTION_NOT_IMPLEMENTED';
  END IF;

  CREATE TEMPORARY TABLE gda_v5_effective_decisions ON COMMIT DROP AS
  SELECT d.assignment_review_decision_id,d.canonical_assignment_id,
    encode(sha256(convert_to(jsonb_build_object('decision',jsonb_build_array(
      d.assignment_review_decision_id,d.canonical_assignment_id,d.outcome,d.supersedes_decision_id),
      'supports',jsonb_agg(jsonb_build_array(e.evidence_item_id,e.evidence_role)
        ORDER BY e.evidence_item_id,e.evidence_role))::text,'UTF8')),'hex')::core.sha256_hex AS decision_snapshot_sha256
  FROM provenance.assignment_review_decision d
  JOIN provenance.canonical_assignment a ON a.canonical_assignment_id=d.canonical_assignment_id
  JOIN provenance.assignment_decision_evidence e ON e.assignment_review_decision_id=d.assignment_review_decision_id
    AND e.evidence_role='supports'
  WHERE a.assignment_kind='folder_membership' AND a.status='accepted'
    AND NOT EXISTS (SELECT 1 FROM provenance.canonical_assignment newer
      WHERE newer.supersedes_assignment_id=a.canonical_assignment_id)
    AND d.outcome='accept'
    AND NOT EXISTS (SELECT 1 FROM provenance.assignment_review_decision newer
      WHERE newer.supersedes_decision_id=d.assignment_review_decision_id)
  GROUP BY d.assignment_review_decision_id,d.canonical_assignment_id,d.outcome,d.supersedes_decision_id;
  IF EXISTS (SELECT 1 FROM gda_v5_effective_decisions GROUP BY canonical_assignment_id HAVING count(*)>1) THEN
    RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='MULTIPLE_EFFECTIVE_FOLDER_DECISIONS';
  END IF;
  CREATE TEMPORARY TABLE gda_v5_expected_memberships ON COMMIT DROP AS
  WITH current_assignment AS MATERIALIZED (
    SELECT a.canonical_assignment_id,a.assignment_kind,a.status,a.supersedes_assignment_id
    FROM provenance.canonical_assignment a
    WHERE a.assignment_kind='folder_membership' AND a.status='accepted'
      AND NOT EXISTS (SELECT 1 FROM provenance.canonical_assignment newer
        WHERE newer.supersedes_assignment_id=a.canonical_assignment_id)
  ), assignment_snapshots AS MATERIALIZED (
    SELECT a.canonical_assignment_id,encode(sha256(convert_to(jsonb_build_object(
      'assignment',jsonb_build_array(a.canonical_assignment_id,a.assignment_kind,a.status,a.supersedes_assignment_id),
      'memberships',jsonb_agg(jsonb_build_array(fm.folder_id,fm.archive_object_id,fm.membership_role,fm.member_ordinal)
        ORDER BY fm.folder_id,fm.membership_role,fm.member_ordinal,fm.archive_object_id))::text,'UTF8')),'hex')::core.sha256_hex AS assignment_snapshot_sha256
    FROM current_assignment a JOIN provenance.assignment_folder_membership fm ON fm.canonical_assignment_id=a.canonical_assignment_id
    GROUP BY a.canonical_assignment_id,a.assignment_kind,a.status,a.supersedes_assignment_id
  )
  SELECT fm.folder_id,fm.archive_object_id,a.canonical_assignment_id AS source_assignment_id,
    fm.membership_role,fm.member_ordinal,d.assignment_review_decision_id AS effective_decision_id,
    s.assignment_snapshot_sha256,d.decision_snapshot_sha256
  FROM current_assignment a JOIN provenance.assignment_folder_membership fm ON fm.canonical_assignment_id=a.canonical_assignment_id
  JOIN gda_v5_effective_decisions d ON d.canonical_assignment_id=a.canonical_assignment_id
  JOIN assignment_snapshots s ON s.canonical_assignment_id=a.canonical_assignment_id
  JOIN raw.legacy_surface_ledger l ON l.archive_object_id=fm.archive_object_id
    AND l.migration_batch_id=p_migration_batch_id AND l.import_disposition='accounted'
  JOIN research.corpus_membership cm ON cm.archive_object_id=fm.archive_object_id
    AND cm.corpus_version_id=v_corpus_version_id AND cm.disposition='eligible';
  CREATE UNIQUE INDEX ON gda_v5_expected_memberships(folder_id,archive_object_id,membership_role);
  CREATE UNIQUE INDEX ON gda_v5_expected_memberships(folder_id,membership_role,member_ordinal);
  IF EXISTS (SELECT 1 FROM gda_v5_expected_memberships e LEFT JOIN research.folder_publication_metadata m ON m.folder_id=e.folder_id WHERE m.folder_id IS NULL) THEN
    RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='RESEARCH_LAUNCH_V5_FOLDER_METADATA_MISSING';
  END IF;
  CREATE TEMPORARY TABLE gda_v5_expected_objects ON COMMIT DROP AS
  SELECT l.archive_object_id,l.surface_id,o.object_urn,o.preferred_label
  FROM raw.legacy_surface_ledger l JOIN core.archive_object o ON o.archive_object_id=l.archive_object_id
  JOIN research.corpus_membership cm ON cm.archive_object_id=l.archive_object_id
    AND cm.corpus_version_id=v_corpus_version_id AND cm.disposition='eligible'
  WHERE l.migration_batch_id=p_migration_batch_id AND l.import_disposition='accounted'
    AND l.archive_object_id IS NOT NULL;
  CREATE UNIQUE INDEX ON gda_v5_expected_objects(archive_object_id);

  INSERT INTO release.research_release_object(research_release_id,archive_object_id,object_urn,legacy_surface_id,title,publication_layer,acceptance_state,workflow_state)
  SELECT p_release_id,archive_object_id,object_urn,surface_id,preferred_label,'active','accepted','resolved'
  FROM gda_v5_expected_objects;
  IF p_fault_point='after_release_objects' THEN RAISE EXCEPTION USING ERRCODE='P0001',MESSAGE='RESEARCH_LAUNCH_V5_FAULT_AFTER_RELEASE_OBJECTS'; END IF;
  INSERT INTO release.research_surface_presentation_projection_v3(research_release_id,archive_object_id,public_surface_id,title,title_missingness,display_date,display_date_missingness,normalized_year,normalized_year_missingness,place_label,place_missingness,medium_label,medium_missingness,type_label,type_missingness,source_label,description,description_missingness,public_citation_label,public_source_route,publication_layer)
  SELECT p_release_id,ro.archive_object_id,ro.legacy_surface_id,ro.title,
    CASE WHEN ro.title IS NULL THEN 'missing' ELSE 'present' END,NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',allow.citation_label,NULL,'missing',allow.citation_label,
    '/sources/'||encode(sha256(convert_to(allow.citation_label,'UTF8')),'hex'),ro.publication_layer
  FROM release.research_release_object ro CROSS JOIN research.public_source_citation_allowlist_v3 allow
  WHERE ro.research_release_id=p_release_id AND allow.source_asset_id=v_asset_id;
  INSERT INTO release.research_surface_citation_projection_v3
  SELECT p_release_id,archive_object_id,0,public_citation_label,public_source_route
  FROM release.research_surface_presentation_projection_v3 WHERE research_release_id=p_release_id;

  INSERT INTO release.research_folder_type_projection_v3
  SELECT DISTINCT p_release_id,t.folder_type_code,t.type_label,t.type_sort_ordinal
  FROM research.folder_type_registry t JOIN research.folder_publication_metadata md ON md.folder_type_code=t.folder_type_code
  JOIN gda_v5_expected_memberships e ON e.folder_id=md.folder_id;
  INSERT INTO release.research_folder_projection_v3
  SELECT p_release_id,f.folder_id,f.folder_token,md.folder_type_code,md.slug,f.label,md.scope_note,md.folder_sort_ordinal
  FROM research.folder f JOIN research.folder_publication_metadata md ON md.folder_id=f.folder_id
  WHERE EXISTS (SELECT 1 FROM gda_v5_expected_memberships e WHERE e.folder_id=f.folder_id);
  IF p_fault_point='after_folders' THEN RAISE EXCEPTION USING ERRCODE='P0001',MESSAGE='RESEARCH_LAUNCH_V5_FAULT_AFTER_FOLDERS'; END IF;
  INSERT INTO release.research_folder_membership_projection_v3
  SELECT p_release_id,e.folder_id,e.archive_object_id,e.source_assignment_id,e.membership_role,e.member_ordinal,
    'accepted',e.assignment_snapshot_sha256,e.effective_decision_id,e.decision_snapshot_sha256
  FROM gda_v5_expected_memberships e;
  IF p_fault_point='after_memberships' THEN RAISE EXCEPTION USING ERRCODE='P0001',MESSAGE='RESEARCH_LAUNCH_V5_FAULT_AFTER_MEMBERSHIPS'; END IF;
  INSERT INTO release.research_search_document_projection_v3
  SELECT p_release_id,archive_object_id,public_surface_id,title,coalesce(title,'')||' '||source_label,coalesce(title,'')||' '||public_surface_id
  FROM release.research_surface_presentation_projection_v3 WHERE research_release_id=p_release_id;
  INSERT INTO release.research_corpus_summary_projection_v3
  SELECT p_release_id,cv.corpus_version_id,c.corpus_token,cv.version_token,c.label,
    count(*) FILTER (WHERE cm.disposition='eligible'),count(*) FILTER (WHERE cm.disposition='held')
  FROM research.corpus_version cv JOIN research.corpus c ON c.corpus_id=cv.corpus_id
  LEFT JOIN research.corpus_membership cm ON cm.corpus_version_id=cv.corpus_version_id
  WHERE cv.corpus_version_id=v_corpus_version_id
  GROUP BY cv.corpus_version_id,c.corpus_token,cv.version_token,c.label;
  INSERT INTO release.research_trace_availability_projection_v3 VALUES(p_release_id,0,0,'NO_ACCEPTED_SEMANTIC_RELATIONS');
  INSERT INTO release.research_launch_source_disposition_count_v3
  SELECT p_release_id,'corpusMemberships',x.disposition,count(cm.*)
  FROM (VALUES ('eligible'),('held'),('rejected'),('excluded')) x(disposition)
  LEFT JOIN research.corpus_membership cm ON cm.corpus_version_id=v_corpus_version_id AND cm.disposition::text=x.disposition
  GROUP BY x.disposition
  UNION ALL
  SELECT p_release_id,'folderAssignments',x.disposition,count(a.*)
  FROM (VALUES ('proposed'),('accepted'),('rejected'),('superseded')) x(disposition)
  LEFT JOIN provenance.canonical_assignment a ON a.assignment_kind='folder_membership' AND a.status::text=x.disposition
  GROUP BY x.disposition;
  CREATE TEMPORARY TABLE gda_v5_component_rows(
    component_code text NOT NULL,semantic_key text NOT NULL,row_digest core.sha256_hex NOT NULL
  ) ON COMMIT DROP;
  INSERT INTO gda_v5_component_rows
  SELECT 'releaseObjects',archive_object_id::text,encode(sha256(convert_to(jsonb_build_array(archive_object_id,object_urn,legacy_surface_id,title,publication_layer,acceptance_state,workflow_state)::text,'UTF8')),'hex')::core.sha256_hex FROM release.research_release_object WHERE research_release_id=p_release_id
  UNION ALL SELECT 'surfacePresentation',archive_object_id::text,encode(sha256(convert_to(jsonb_build_array(archive_object_id,public_surface_id,title,title_missingness,display_date,display_date_missingness,normalized_year,normalized_year_missingness,place_label,place_missingness,medium_label,medium_missingness,type_label,type_missingness,source_label,description,description_missingness,public_citation_label,public_source_route,publication_layer)::text,'UTF8')),'hex')::core.sha256_hex FROM release.research_surface_presentation_projection_v3 WHERE research_release_id=p_release_id
  UNION ALL SELECT 'surfaceCredits',archive_object_id::text||':'||lpad(credit_ordinal::text,12,'0'),encode(sha256(convert_to(jsonb_build_array(archive_object_id,credit_ordinal,credited_label,credit_role)::text,'UTF8')),'hex')::core.sha256_hex FROM release.research_surface_credit_projection_v3 WHERE research_release_id=p_release_id
  UNION ALL SELECT 'surfaceCitations',archive_object_id::text||':'||lpad(citation_ordinal::text,12,'0'),encode(sha256(convert_to(jsonb_build_array(archive_object_id,citation_ordinal,citation_label,public_source_route)::text,'UTF8')),'hex')::core.sha256_hex FROM release.research_surface_citation_projection_v3 WHERE research_release_id=p_release_id
  UNION ALL SELECT 'folderTypes',lpad(sort_ordinal::text,12,'0')||':'||folder_type_code,encode(sha256(convert_to(jsonb_build_array(folder_type_code,type_label,sort_ordinal)::text,'UTF8')),'hex')::core.sha256_hex FROM release.research_folder_type_projection_v3 WHERE research_release_id=p_release_id
  UNION ALL SELECT 'folders',folder_type_code||':'||lpad(sort_ordinal::text,12,'0')||':'||folder_id::text,encode(sha256(convert_to(jsonb_build_array(folder_id,folder_token,folder_type_code,slug,label,scope_note,sort_ordinal)::text,'UTF8')),'hex')::core.sha256_hex FROM release.research_folder_projection_v3 WHERE research_release_id=p_release_id
  UNION ALL SELECT 'folderMemberships',folder_id::text||':'||membership_role||':'||lpad(member_ordinal::text,12,'0')||':'||archive_object_id::text,encode(sha256(convert_to(jsonb_build_array(folder_id,archive_object_id,source_assignment_id,membership_role,member_ordinal,source_assignment_status,source_assignment_snapshot_sha256,effective_decision_id,effective_decision_snapshot_sha256)::text,'UTF8')),'hex')::core.sha256_hex FROM release.research_folder_membership_projection_v3 WHERE research_release_id=p_release_id
  UNION ALL SELECT 'searchDocuments',sort_key||':'||archive_object_id::text,encode(sha256(convert_to(jsonb_build_array(archive_object_id,public_surface_id,title,search_document,sort_key)::text,'UTF8')),'hex')::core.sha256_hex FROM release.research_search_document_projection_v3 WHERE research_release_id=p_release_id
  UNION ALL SELECT 'corpusSummary',corpus_version_id::text,encode(sha256(convert_to(jsonb_build_array(corpus_version_id,corpus_token,corpus_version_token,corpus_label,eligible_object_count,held_object_count)::text,'UTF8')),'hex')::core.sha256_hex FROM release.research_corpus_summary_projection_v3 WHERE research_release_id=p_release_id
  UNION ALL SELECT 'traceAvailability',research_release_id::text,encode(sha256(convert_to(jsonb_build_array(trace_eligible_object_count,trace_relation_count,availability_reason)::text,'UTF8')),'hex')::core.sha256_hex FROM release.research_trace_availability_projection_v3 WHERE research_release_id=p_release_id;
  CREATE UNIQUE INDEX ON gda_v5_component_rows(component_code,semantic_key);
  INSERT INTO release.research_launch_component_manifest_v3
  SELECT p_release_id,x.component_code,x.row_count,release.research_launch_component_hash_staged_v5(x.component_code)
  FROM (VALUES
    ('releaseObjects',(SELECT count(*) FROM release.research_release_object WHERE research_release_id=p_release_id)),
    ('surfacePresentation',(SELECT count(*) FROM release.research_surface_presentation_projection_v3 WHERE research_release_id=p_release_id)),
    ('surfaceCredits',0::bigint),('surfaceCitations',(SELECT count(*) FROM release.research_surface_citation_projection_v3 WHERE research_release_id=p_release_id)),
    ('folderTypes',(SELECT count(*) FROM release.research_folder_type_projection_v3 WHERE research_release_id=p_release_id)),
    ('folders',(SELECT count(*) FROM release.research_folder_projection_v3 WHERE research_release_id=p_release_id)),
    ('folderMemberships',(SELECT count(*) FROM release.research_folder_membership_projection_v3 WHERE research_release_id=p_release_id)),
    ('searchDocuments',(SELECT count(*) FROM release.research_search_document_projection_v3 WHERE research_release_id=p_release_id)),
    ('corpusSummary',(SELECT count(*) FROM release.research_corpus_summary_projection_v3 WHERE research_release_id=p_release_id)),
    ('traceAvailability',(SELECT count(*) FROM release.research_trace_availability_projection_v3 WHERE research_release_id=p_release_id))
  ) x(component_code,row_count);
  IF p_fault_point='after_component_hashes' THEN RAISE EXCEPTION USING ERRCODE='P0001',MESSAGE='RESEARCH_LAUNCH_V5_FAULT_AFTER_COMPONENT_HASHES'; END IF;
  IF (SELECT count(*) FROM gda_v5_expected_objects)<>(SELECT count(*) FROM release.research_release_object WHERE research_release_id=p_release_id)
    OR EXISTS (SELECT 1 FROM gda_v5_expected_objects e LEFT JOIN release.research_release_object r ON r.research_release_id=p_release_id AND r.archive_object_id=e.archive_object_id WHERE r.archive_object_id IS NULL)
    OR (SELECT count(*) FROM gda_v5_expected_memberships)<>(SELECT count(*) FROM release.research_folder_membership_projection_v3 WHERE research_release_id=p_release_id)
    OR EXISTS (SELECT 1 FROM gda_v5_expected_memberships e LEFT JOIN release.research_folder_membership_projection_v3 r ON r.research_release_id=p_release_id AND r.folder_id=e.folder_id AND r.archive_object_id=e.archive_object_id
      AND r.membership_role=e.membership_role AND r.member_ordinal=e.member_ordinal
      WHERE r.archive_object_id IS NULL) THEN
    RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RESEARCH_LAUNCH_V5_COPY_PARITY_MISMATCH';
  END IF;
  v_source_sha:=release.canonical_jsonb_sha256(jsonb_build_object('candidateAssetId',v_asset_id,'candidateAssetSha256',v_asset_sha,'migrationBatchId',p_migration_batch_id,'publicCorpusVersionId',v_corpus_version_id,'mappingSpecificationSha256',v_mapping_sha,'queryPackSha256',v_query_sha,'selectionPolicySha256',v_selection_sha,'registryCorpusPolicySha256',v_registry_sha,'sourceDispositions',coalesce((SELECT jsonb_agg(jsonb_build_array(source_component,source_disposition,row_count) ORDER BY source_component,source_disposition) FROM release.research_launch_source_disposition_count_v3 WHERE research_release_id=p_release_id),'[]'::jsonb)));
  v_component_sha:=release.research_launch_component_manifest_sha_v5(p_release_id);
  v_receipt_sha:=release.canonical_jsonb_sha256(jsonb_build_object('format','gda-v49-research-build-receipt-v5','source',v_source_sha,'components',v_component_sha));
  v_fingerprint:=release.canonical_jsonb_sha256(jsonb_build_object(
    'format','gda-v49-research-candidate-physical-v5','releaseId',p_release_id,
    'source',jsonb_build_object('candidateAssetId',v_asset_id,'candidateAssetSha256',v_asset_sha,
      'migrationBatchId',p_migration_batch_id,'publicCorpusVersionId',v_corpus_version_id,
      'mappingSpecificationSha256',v_mapping_sha,'projectionQueryPackSha256',v_query_sha,
      'selectionPolicySha256',v_selection_sha,'registryCorpusPolicySha256',v_registry_sha,
      'sourceSnapshotSha256',v_source_sha,'componentManifestSha256',v_component_sha,
      'contentSha256',v_component_sha),
    'components',coalesce((SELECT jsonb_agg(jsonb_build_array(component_code,row_count,content_sha256)
      ORDER BY component_code) FROM release.research_launch_component_manifest_v3
      WHERE research_release_id=p_release_id),'[]'::jsonb)));
  INSERT INTO release.research_launch_protocol_v5 VALUES(p_release_id,'release-snapshot-v5',clock_timestamp());
  INSERT INTO release.research_launch_build_receipt_v3(research_release_id,builder_version,migration_batch_id,public_corpus_version_id,candidate_asset_id,candidate_asset_sha256,mapping_specification_sha256,projection_query_pack_sha256,selection_policy_sha256,registry_corpus_policy_sha256,source_snapshot_sha256,projection_component_manifest_sha256,projection_content_sha256,build_receipt_sha256,candidate_fingerprint,built_at)
  VALUES(p_release_id,'release-snapshot-v5',p_migration_batch_id,v_corpus_version_id,v_asset_id,v_asset_sha,v_mapping_sha,v_query_sha,v_selection_sha,v_registry_sha,v_source_sha,v_component_sha,v_component_sha,v_receipt_sha,v_fingerprint,clock_timestamp());
  IF p_fault_point='after_build_receipt' THEN RAISE EXCEPTION USING ERRCODE='P0001',MESSAGE='RESEARCH_LAUNCH_V5_FAULT_AFTER_BUILD_RECEIPT'; END IF;
  IF p_fault_point='before_candidate_transition' THEN RAISE EXCEPTION USING ERRCODE='P0001',MESSAGE='RESEARCH_LAUNCH_V5_FAULT_BEFORE_CANDIDATE_TRANSITION'; END IF;
  UPDATE release.research_release SET release_state='candidate',candidate_fingerprint=v_fingerprint,candidate_at=clock_timestamp() WHERE research_release_id=p_release_id;
  INSERT INTO audit.research_release_event VALUES(p_candidate_event_id,p_release_id,'draft','candidate',session_user::text,clock_timestamp(),p_candidate_event_sha256);
  RETURN v_fingerprint;
END
$function$;

CREATE OR REPLACE FUNCTION provenance.enforce_provenance_supersession_parent()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := pg_catalog.to_jsonb(NEW);
BEGIN
  IF TG_TABLE_NAME = 'source_version'
    AND v_row->>'supersedes_source_version_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM provenance.source_version prior
      WHERE prior.source_version_id = (v_row->>'supersedes_source_version_id')::uuid
        AND prior.source_document_id = (v_row->>'source_document_id')::uuid
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'SOURCE_VERSION_SUPERSESSION_PARENT_MISMATCH';
  ELSIF TG_TABLE_NAME = 'evidence_item'
    AND v_row->>'supersedes_evidence_item_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1
      FROM provenance.evidence_item prior
      JOIN provenance.source_version oldv ON oldv.source_version_id = prior.source_version_id
      JOIN provenance.source_version newv ON newv.source_version_id = (v_row->>'source_version_id')::uuid
      WHERE prior.evidence_item_id = (v_row->>'supersedes_evidence_item_id')::uuid
        AND oldv.source_document_id = newv.source_document_id
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'EVIDENCE_SUPERSESSION_SOURCE_MISMATCH';
  ELSIF TG_TABLE_NAME = 'assertion'
    AND v_row->>'supersedes_assertion_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM provenance.assertion prior
      WHERE prior.assertion_id = (v_row->>'supersedes_assertion_id')::uuid
        AND prior.assertion_predicate_id = (v_row->>'assertion_predicate_id')::uuid
        AND prior.subject_kind::text = v_row->>'subject_kind'
        AND prior.value_kind::text = v_row->>'value_kind'
        AND prior.status = 'superseded'
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ASSERTION_SUPERSESSION_IDENTITY_MISMATCH';
  ELSIF TG_TABLE_NAME = 'canonical_assignment'
    AND v_row->>'supersedes_assignment_id' IS NOT NULL
    AND (v_row->>'canonical_assignment_id')::uuid =
      (v_row->>'supersedes_assignment_id')::uuid THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ASSIGNMENT_SUPERSESSION_CYCLE';
  ELSIF TG_TABLE_NAME = 'canonical_assignment'
    AND v_row->>'supersedes_assignment_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM provenance.canonical_assignment prior
      WHERE prior.canonical_assignment_id = (v_row->>'supersedes_assignment_id')::uuid
        AND prior.assignment_kind::text = v_row->>'assignment_kind'
        AND prior.status = 'superseded'
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ASSIGNMENT_SUPERSESSION_KIND_MISMATCH';
  ELSIF TG_TABLE_NAME = 'canonical_assignment'
    AND v_row->>'supersedes_assignment_id' IS NOT NULL
    AND v_row->>'assignment_kind' = 'folder_membership'
    AND NOT EXISTS (
      SELECT 1
      FROM provenance.assignment_folder_membership prior_membership
      JOIN provenance.assignment_folder_membership new_membership
        ON new_membership.canonical_assignment_id =
          (v_row->>'canonical_assignment_id')::uuid
      WHERE prior_membership.canonical_assignment_id =
          (v_row->>'supersedes_assignment_id')::uuid
        AND prior_membership.archive_object_id = new_membership.archive_object_id
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ASSIGNMENT_SUPERSESSION_OBJECT_MISMATCH';
  ELSIF TG_TABLE_NAME = 'assignment_review_decision'
    AND v_row->>'supersedes_decision_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM provenance.assignment_review_decision prior
      WHERE prior.assignment_review_decision_id = (v_row->>'supersedes_decision_id')::uuid
        AND prior.canonical_assignment_id = (v_row->>'canonical_assignment_id')::uuid
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ASSIGNMENT_DECISION_SUPERSESSION_PARENT_MISMATCH';
  ELSIF TG_TABLE_NAME = 'assertion_review_decision'
    AND v_row->>'supersedes_decision_id' IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM provenance.assertion_review_decision prior
      WHERE prior.assertion_review_decision_id = (v_row->>'supersedes_decision_id')::uuid
        AND prior.assertion_id = (v_row->>'assertion_id')::uuid
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'ASSERTION_DECISION_SUPERSESSION_PARENT_MISMATCH';
  END IF;
  RETURN NULL;
END
$function$;


CREATE OR REPLACE FUNCTION provenance.enforce_one_current_review_decision()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
DECLARE
  v_row jsonb := to_jsonb(NEW);
  v_parent_id uuid;
  v_current_count integer;
BEGIN
  IF TG_TABLE_NAME = 'assertion_review_decision' THEN
    v_parent_id := (v_row ->> 'assertion_id')::uuid;
    SELECT count(*) INTO v_current_count
    FROM provenance.assertion_review_decision d
    WHERE d.assertion_id = v_parent_id
      AND NOT EXISTS (
        SELECT 1 FROM provenance.assertion_review_decision newer
        WHERE newer.supersedes_decision_id = d.assertion_review_decision_id);
    IF v_row ->> 'supersedes_decision_id' IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM provenance.assertion_review_decision prior
      WHERE prior.assertion_review_decision_id =
          (v_row ->> 'supersedes_decision_id')::uuid
        AND prior.assertion_id = v_parent_id
        AND (
          prior.decided_at < (v_row ->> 'decided_at')::timestamptz
          OR (prior.decided_at = (v_row ->> 'decided_at')::timestamptz
            AND prior.assertion_review_decision_id <
              (v_row ->> 'assertion_review_decision_id')::uuid)
        )
    ) THEN
      RAISE EXCEPTION USING ERRCODE = '23514',
        MESSAGE = 'ASSERTION_DECISION_SUPERSESSION_ORDER_MISMATCH';
    END IF;
  ELSE
    v_parent_id := (v_row ->> 'canonical_assignment_id')::uuid;
    SELECT count(*) INTO v_current_count
    FROM provenance.assignment_review_decision d
    WHERE d.canonical_assignment_id = v_parent_id
      AND NOT EXISTS (
        SELECT 1 FROM provenance.assignment_review_decision newer
        WHERE newer.supersedes_decision_id = d.assignment_review_decision_id);
    IF v_row ->> 'supersedes_decision_id' IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM provenance.assignment_review_decision prior
      WHERE prior.assignment_review_decision_id =
          (v_row ->> 'supersedes_decision_id')::uuid
        AND prior.canonical_assignment_id = v_parent_id
        AND (
          prior.decided_at < (v_row ->> 'decided_at')::timestamptz
          OR (prior.decided_at = (v_row ->> 'decided_at')::timestamptz
            AND prior.assignment_review_decision_id <
              (v_row ->> 'assignment_review_decision_id')::uuid)
        )
    ) THEN
      RAISE EXCEPTION USING ERRCODE = '23514',
        MESSAGE = 'ASSIGNMENT_DECISION_SUPERSESSION_ORDER_MISMATCH';
    END IF;
  END IF;
  IF v_current_count <> 1 THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      MESSAGE = 'PROVENANCE_REVIEW_REQUIRES_ONE_CURRENT_DECISION';
  END IF;
  RETURN NULL;
END
$function$;


-- A v5 seal uses the v5 physical candidate fingerprint and manifest builder.
-- The historical generic verification entry point intentionally remains
-- unchanged because it proves the earlier logical-release contract.  This
-- forward-only entry point gives a v5 sealed release an equivalent controlled
-- verification path before it can enter the exact-pair API views or CAS.
CREATE FUNCTION release.record_research_launch_verification_v5(
  p_verification_id uuid,p_release_id uuid,p_manifest_sha256 core.sha256_hex,
  p_verifier_version core.release_token,p_sidecar_sha256 core.sha256_hex,
  p_audit_event_id uuid,p_audit_receipt_sha256 core.sha256_hex
) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $function$
DECLARE
  v_expected core.sha256_hex;
  v_seal audit.research_seal_event%ROWTYPE;
  v_now timestamptz:=clock_timestamp();
BEGIN
  PERFORM rights.require_reviewer();
  PERFORM release.validate_research_launch_snapshot_v5_integrity(p_release_id);
  IF NOT EXISTS (
    SELECT 1
    FROM release.research_release r
    JOIN release.research_launch_manifest_v3 lm USING(research_release_id)
    JOIN release.research_release_manifest m USING(research_release_id)
    WHERE r.research_release_id=p_release_id
      AND r.release_state='sealed'
      AND r.manifest_sha256=p_manifest_sha256
      AND lm.manifest_sha256=p_manifest_sha256
      AND m.manifest_sha256=p_manifest_sha256
      AND lm.manifest_bytes=m.manifest_bytes
      AND m.manifest_bytes=release.build_research_launch_manifest_bytes_v5(p_release_id)
      AND encode(sha256(m.manifest_bytes),'hex')=p_manifest_sha256
      AND r.candidate_fingerprint=
        release.compute_research_launch_candidate_fingerprint_v5(p_release_id)
  ) THEN
    RAISE EXCEPTION USING ERRCODE='23514',
      MESSAGE='SEALED_RESEARCH_LAUNCH_V5_DETACHED_INTEGRITY_FAILURE';
  END IF;
  SELECT * INTO STRICT v_seal FROM audit.research_seal_event
  WHERE research_release_id=p_release_id
    AND seal_function_version='release-snapshot-v5';
  v_expected:=release.compute_research_verification_sidecar_sha(
    p_release_id,p_manifest_sha256,p_verifier_version);
  IF p_sidecar_sha256 IS DISTINCT FROM v_expected THEN
    RAISE EXCEPTION USING ERRCODE='23514',
      MESSAGE='RESEARCH_LAUNCH_V5_VERIFICATION_SIDECAR_MISMATCH';
  END IF;
  INSERT INTO release.research_release_verification(
    research_release_verification_id,research_release_id,manifest_sha256,
    verifier_version,sidecar_sha256,verified,verified_at,seal_transaction_id,
    candidate_fingerprint,seal_function_version,attestation_sha256)
  VALUES(p_verification_id,p_release_id,p_manifest_sha256,p_verifier_version,
    p_sidecar_sha256,true,v_now,v_seal.seal_transaction_id,
    v_seal.candidate_fingerprint,v_seal.seal_function_version,NULL);
  INSERT INTO audit.verification_receipt_event VALUES(
    p_audit_event_id,p_verification_id,NULL,p_audit_receipt_sha256,
    session_user::text,v_now);
END
$function$;


RESET ROLE;
