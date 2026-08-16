\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

-- v3 is intentionally separate from the historical candidate/manifest
-- functions.  Once built, every v3 validation query below reads only the
-- release-owned rows and this receipt; canonical data is read only inside the
-- one SERIALIZABLE construction transaction.

CREATE FUNCTION release.research_launch_component_hash_v3(
  p_release_id uuid, p_component text
) RETURNS core.sha256_hex
LANGUAGE plpgsql STABLE
SET search_path = pg_catalog
AS $function$
DECLARE v_rows jsonb;
BEGIN
  CASE p_component
    WHEN 'releaseObjects' THEN
      SELECT COALESCE(jsonb_agg(jsonb_build_array(archive_object_id, object_urn,
        legacy_surface_id, title, publication_layer, acceptance_state, workflow_state)
        ORDER BY archive_object_id), '[]'::jsonb) INTO v_rows
      FROM release.research_release_object WHERE research_release_id = p_release_id;
    WHEN 'surfacePresentation' THEN
      SELECT COALESCE(jsonb_agg(jsonb_build_array(archive_object_id, public_surface_id,
        title, title_missingness, display_date, display_date_missingness,
        normalized_year, normalized_year_missingness, place_label, place_missingness,
        medium_label, medium_missingness, type_label, type_missingness, source_label,
        description, description_missingness, public_citation_label, public_source_route,
        publication_layer) ORDER BY archive_object_id), '[]'::jsonb) INTO v_rows
      FROM release.research_surface_presentation_projection_v3 WHERE research_release_id = p_release_id;
    WHEN 'surfaceCredits' THEN
      SELECT COALESCE(jsonb_agg(jsonb_build_array(archive_object_id, credit_ordinal,
        credited_label, credit_role) ORDER BY archive_object_id, credit_ordinal), '[]'::jsonb) INTO v_rows
      FROM release.research_surface_credit_projection_v3 WHERE research_release_id = p_release_id;
    WHEN 'surfaceCitations' THEN
      SELECT COALESCE(jsonb_agg(jsonb_build_array(archive_object_id, citation_ordinal,
        citation_label, public_source_route) ORDER BY archive_object_id, citation_ordinal), '[]'::jsonb) INTO v_rows
      FROM release.research_surface_citation_projection_v3 WHERE research_release_id = p_release_id;
    WHEN 'folderTypes' THEN
      SELECT COALESCE(jsonb_agg(jsonb_build_array(folder_type_code, type_label, sort_ordinal)
        ORDER BY sort_ordinal, folder_type_code), '[]'::jsonb) INTO v_rows
      FROM release.research_folder_type_projection_v3 WHERE research_release_id = p_release_id;
    WHEN 'folders' THEN
      SELECT COALESCE(jsonb_agg(jsonb_build_array(folder_id, folder_token, folder_type_code,
        slug, label, scope_note, sort_ordinal) ORDER BY folder_type_code, sort_ordinal, folder_id), '[]'::jsonb) INTO v_rows
      FROM release.research_folder_projection_v3 WHERE research_release_id = p_release_id;
    WHEN 'folderMemberships' THEN
      SELECT COALESCE(jsonb_agg(jsonb_build_array(folder_id, archive_object_id,
        source_assignment_id, membership_role, member_ordinal, source_assignment_status,
        source_assignment_snapshot_sha256, effective_decision_id,
        effective_decision_snapshot_sha256) ORDER BY folder_id, membership_role,
        member_ordinal, archive_object_id), '[]'::jsonb) INTO v_rows
      FROM release.research_folder_membership_projection_v3 WHERE research_release_id = p_release_id;
    WHEN 'searchDocuments' THEN
      SELECT COALESCE(jsonb_agg(jsonb_build_array(archive_object_id, public_surface_id,
        title, search_document, sort_key) ORDER BY sort_key, archive_object_id), '[]'::jsonb) INTO v_rows
      FROM release.research_search_document_projection_v3 WHERE research_release_id = p_release_id;
    WHEN 'corpusSummary' THEN
      SELECT COALESCE(jsonb_agg(jsonb_build_array(corpus_version_id, corpus_token,
        corpus_version_token, corpus_label, eligible_object_count, held_object_count)
        ORDER BY corpus_version_id), '[]'::jsonb) INTO v_rows
      FROM release.research_corpus_summary_projection_v3 WHERE research_release_id = p_release_id;
    WHEN 'traceAvailability' THEN
      SELECT COALESCE(jsonb_agg(jsonb_build_array(trace_eligible_object_count,
        trace_relation_count, availability_reason) ORDER BY research_release_id), '[]'::jsonb) INTO v_rows
      FROM release.research_trace_availability_projection_v3 WHERE research_release_id = p_release_id;
    ELSE RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'UNKNOWN_LAUNCH_COMPONENT';
  END CASE;
  RETURN release.canonical_jsonb_sha256(jsonb_build_object(
    'format', 'gda-v49-research-component-jcs-v3', 'component', p_component, 'rows', v_rows));
END
$function$;

CREATE FUNCTION release.research_launch_component_manifest_sha_v3(p_release_id uuid)
RETURNS core.sha256_hex LANGUAGE sql STABLE SET search_path = pg_catalog
RETURN release.canonical_jsonb_sha256(jsonb_build_object(
  'format','gda-v49-research-component-manifest-jcs-v3',
  'components', COALESCE((SELECT jsonb_agg(jsonb_build_array(component_code,row_count,content_sha256)
    ORDER BY component_code) FROM release.research_launch_component_manifest_v3
    WHERE research_release_id=p_release_id),'[]'::jsonb)
));

CREATE FUNCTION release.research_launch_content_sha_v3(p_release_id uuid)
RETURNS core.sha256_hex LANGUAGE sql STABLE SET search_path = pg_catalog
RETURN release.research_launch_component_manifest_sha_v3(p_release_id);

CREATE FUNCTION release.compute_research_launch_candidate_fingerprint_v3(p_release_id uuid)
RETURNS core.sha256_hex LANGUAGE sql STABLE SET search_path = pg_catalog
RETURN release.canonical_jsonb_sha256(jsonb_build_object(
  'format','gda-v49-research-candidate-physical-v3',
  'releaseId',p_release_id,
  'source',(SELECT jsonb_build_object('candidateAssetId',candidate_asset_id,
    'candidateAssetSha256',candidate_asset_sha256,'migrationBatchId',migration_batch_id,
    'publicCorpusVersionId',public_corpus_version_id,
    'mappingSpecificationSha256',mapping_specification_sha256,
    'projectionQueryPackSha256',projection_query_pack_sha256,
    'selectionPolicySha256',selection_policy_sha256,
    'registryCorpusPolicySha256',registry_corpus_policy_sha256,
    'sourceSnapshotSha256',source_snapshot_sha256,
    'componentManifestSha256',projection_component_manifest_sha256,
    'contentSha256',projection_content_sha256)
    FROM release.research_launch_build_receipt_v3 WHERE research_release_id=p_release_id),
  'components',COALESCE((SELECT jsonb_agg(jsonb_build_array(component_code,row_count,content_sha256)
    ORDER BY component_code) FROM release.research_launch_component_manifest_v3
    WHERE research_release_id=p_release_id),'[]'::jsonb)
));

CREATE FUNCTION release.build_research_launch_manifest_bytes_v3(p_release_id uuid)
RETURNS bytea LANGUAGE sql STABLE SET search_path = pg_catalog
RETURN convert_to(jsonb_build_object(
  'format','gda-v49-research-release-manifest-jcs-v3',
  'archiveSnapshotSha256',(SELECT source_snapshot_sha256 FROM release.research_launch_build_receipt_v3 WHERE research_release_id=p_release_id),
  'folderTypeCount',(SELECT row_count FROM release.research_launch_component_manifest_v3 WHERE research_release_id=p_release_id AND component_code='folderTypes'),
  'folderCount',(SELECT row_count FROM release.research_launch_component_manifest_v3 WHERE research_release_id=p_release_id AND component_code='folders'),
  'folderObjectMembershipCount',(SELECT row_count FROM release.research_launch_component_manifest_v3 WHERE research_release_id=p_release_id AND component_code='folderMemberships'),
  'publicFolderSurfaceCount',(SELECT count(DISTINCT archive_object_id) FROM release.research_folder_membership_projection_v3 WHERE research_release_id=p_release_id),
  'surfacePresentationCount',(SELECT row_count FROM release.research_launch_component_manifest_v3 WHERE research_release_id=p_release_id AND component_code='surfacePresentation'),
  'searchDocumentCount',(SELECT row_count FROM release.research_launch_component_manifest_v3 WHERE research_release_id=p_release_id AND component_code='searchDocuments'),
  'traceEligibleObjectCount',(SELECT trace_eligible_object_count FROM release.research_trace_availability_projection_v3 WHERE research_release_id=p_release_id),
  'builderVersion',(SELECT builder_version FROM release.research_launch_build_receipt_v3 WHERE research_release_id=p_release_id),
  'projectionQueryPackSha256',(SELECT projection_query_pack_sha256 FROM release.research_launch_build_receipt_v3 WHERE research_release_id=p_release_id),
  'componentManifestSha256',release.research_launch_component_manifest_sha_v3(p_release_id),
  'candidateFingerprint',release.compute_research_launch_candidate_fingerprint_v3(p_release_id)
)::text,'UTF8');

CREATE FUNCTION release.research_launch_assignment_snapshot_sha_v3(
  p_assignment_id uuid
) RETURNS core.sha256_hex LANGUAGE sql STABLE SET search_path = pg_catalog
RETURN release.canonical_jsonb_sha256(jsonb_build_object(
  'assignment',(SELECT jsonb_build_array(a.canonical_assignment_id,a.assignment_kind,a.status)
    FROM provenance.canonical_assignment a WHERE a.canonical_assignment_id=p_assignment_id),
  'membership',(SELECT jsonb_build_array(m.folder_id,m.archive_object_id,m.membership_role,m.member_ordinal)
    FROM provenance.assignment_folder_membership m WHERE m.canonical_assignment_id=p_assignment_id)
));

CREATE FUNCTION release.research_launch_decision_snapshot_sha_v3(
  p_decision_id uuid
) RETURNS core.sha256_hex LANGUAGE sql STABLE SET search_path = pg_catalog
RETURN release.canonical_jsonb_sha256(jsonb_build_object(
  'decision',(SELECT jsonb_build_array(d.assignment_review_decision_id,d.canonical_assignment_id,d.outcome)
    FROM provenance.assignment_review_decision d WHERE d.assignment_review_decision_id=p_decision_id),
  'evidence',COALESCE((SELECT jsonb_agg(jsonb_build_array(e.evidence_item_id,e.evidence_role)
    ORDER BY e.evidence_item_id,e.evidence_role) FROM provenance.assignment_decision_evidence e
    WHERE e.assignment_review_decision_id=p_decision_id),'[]'::jsonb)
));

CREATE FUNCTION release.guard_research_launch_snapshot_mutation_v3()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog AS $function$
DECLARE v_release_id uuid;
BEGIN
  IF TG_OP='DELETE' THEN
    v_release_id := (to_jsonb(OLD)->>'research_release_id')::uuid;
  ELSE
    v_release_id := (to_jsonb(NEW)->>'research_release_id')::uuid;
  END IF;
  IF TG_OP='UPDATE' AND (to_jsonb(NEW)->>'research_release_id') IS DISTINCT FROM
      (to_jsonb(OLD)->>'research_release_id') THEN
    RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='RESEARCH_LAUNCH_V3_REPARENT_DENIED';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM release.research_release r WHERE r.research_release_id=v_release_id AND r.release_state='draft') THEN
    RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='RESEARCH_LAUNCH_V3_PROJECTION_CLOSED';
  END IF;
  IF EXISTS (SELECT 1 FROM release.research_launch_build_receipt_v3 b WHERE b.research_release_id=v_release_id) THEN
    RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='RESEARCH_LAUNCH_V3_POST_BUILD_MUTATION_DENIED';
  END IF;
  IF TG_OP='DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END
$function$;

-- Construction is the sole canonical-read boundary.  It requires a caller to
-- begin SERIALIZABLE before invocation, acquires a per-release xact lock, and
-- inserts each component set-wise.  Any error is transaction-atomic.
CREATE FUNCTION release.build_research_launch_snapshot_v3(
  p_release_id uuid, p_migration_batch_id uuid, p_policy_id uuid,
  p_candidate_event_id uuid, p_candidate_event_sha256 core.sha256_hex,
  p_fault_point text DEFAULT NULL
) RETURNS core.sha256_hex
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $function$
DECLARE
  v_asset_id uuid; v_asset_sha core.sha256_hex; v_mapping_sha core.sha256_hex; v_corpus_version_id uuid;
  v_query_sha core.sha256_hex; v_selection_sha core.sha256_hex; v_registry_sha core.sha256_hex;
  v_source_sha core.sha256_hex; v_component_sha core.sha256_hex; v_content_sha core.sha256_hex;
  v_receipt_sha core.sha256_hex; v_fingerprint core.sha256_hex;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  IF current_setting('transaction_isolation') <> 'serializable' THEN
    RAISE EXCEPTION USING ERRCODE='25001', MESSAGE='RESEARCH_LAUNCH_V3_BUILDER_REQUIRES_SERIALIZABLE';
  END IF;
  PERFORM pg_advisory_xact_lock(hashtextextended(p_release_id::text, 49023));
  PERFORM 1 FROM release.research_release
    WHERE research_release_id=p_release_id AND release_state='draft' FOR UPDATE;
  IF NOT FOUND OR EXISTS (SELECT 1 FROM release.research_launch_build_receipt_v3 WHERE research_release_id=p_release_id)
    OR EXISTS (SELECT 1 FROM release.research_release_object WHERE research_release_id=p_release_id) THEN
    RAISE EXCEPTION USING ERRCODE='55000', MESSAGE='RESEARCH_LAUNCH_V3_REQUIRES_EMPTY_FRESH_DRAFT';
  END IF;
  SELECT b.canonical_input_asset_id,b.input_sha256,m.specification_sha256,p.public_corpus_version_id,
      p.projection_query_pack_sha256,p.selection_policy_sha256,p.registry_corpus_policy_sha256
    INTO v_asset_id,v_asset_sha,v_mapping_sha,v_corpus_version_id,v_query_sha,v_selection_sha,v_registry_sha
  FROM raw.migration_batch b JOIN raw.mapping_version m ON m.mapping_version_id=b.mapping_version_id
  JOIN research.launch_snapshot_policy_v3 p ON p.launch_snapshot_policy_id=p_policy_id
  WHERE b.migration_batch_id=p_migration_batch_id;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='RESEARCH_LAUNCH_V3_SOURCE_IDENTITY_NOT_RESOLVABLE'; END IF;
  IF EXISTS (
    SELECT 1 FROM provenance.assignment_folder_membership fm
    JOIN provenance.canonical_assignment a ON a.canonical_assignment_id=fm.canonical_assignment_id
    JOIN raw.legacy_surface_ledger l ON l.archive_object_id=fm.archive_object_id
    JOIN research.corpus_membership cm ON cm.archive_object_id=fm.archive_object_id
      AND cm.corpus_version_id=v_corpus_version_id AND cm.disposition='eligible'
    WHERE a.assignment_kind='folder_membership' AND a.status='accepted'
      AND l.migration_batch_id=p_migration_batch_id AND l.import_disposition='accounted'
      AND NOT EXISTS (SELECT 1 FROM research.folder_publication_metadata md WHERE md.folder_id=fm.folder_id)
  ) THEN RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='RESEARCH_LAUNCH_V3_FOLDER_METADATA_MISSING'; END IF;
  IF NOT EXISTS (SELECT 1 FROM research.public_source_citation_allowlist_v3 WHERE source_asset_id=v_asset_id) THEN
    RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='RESEARCH_LAUNCH_V3_PUBLIC_CITATION_ALLOWLIST_MISSING';
  END IF;

  INSERT INTO release.research_release_object(research_release_id,archive_object_id,object_urn,legacy_surface_id,title,publication_layer,acceptance_state,workflow_state)
  SELECT p_release_id,o.archive_object_id,o.object_urn,l.surface_id,o.preferred_label,
    'active','accepted','resolved'
  FROM raw.legacy_surface_ledger l JOIN core.archive_object o ON o.archive_object_id=l.archive_object_id
  JOIN research.corpus_membership cm ON cm.archive_object_id=l.archive_object_id
    AND cm.corpus_version_id=v_corpus_version_id AND cm.disposition='eligible'
  WHERE l.migration_batch_id=p_migration_batch_id AND l.import_disposition='accounted' AND l.archive_object_id IS NOT NULL;
  IF p_fault_point='after_release_objects' THEN RAISE EXCEPTION USING ERRCODE='P0001', MESSAGE='RESEARCH_LAUNCH_V3_FAULT_AFTER_OBJECTS'; END IF;

  INSERT INTO release.research_surface_presentation_projection_v3(
    research_release_id,archive_object_id,public_surface_id,title,title_missingness,display_date,display_date_missingness,
    normalized_year,normalized_year_missingness,place_label,place_missingness,medium_label,medium_missingness,type_label,type_missingness,
    source_label,description,description_missingness,public_citation_label,public_source_route,publication_layer)
  SELECT p_release_id,ro.archive_object_id,ro.legacy_surface_id,ro.title,
    CASE WHEN ro.title IS NULL THEN 'missing' ELSE 'present' END,NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',NULL,'missing',
    allow.citation_label,NULL,'missing',allow.citation_label,
    '/sources/'||encode(sha256(convert_to(allow.citation_label,'UTF8')),'hex'),ro.publication_layer
  FROM release.research_release_object ro CROSS JOIN research.public_source_citation_allowlist_v3 allow
  WHERE ro.research_release_id=p_release_id AND allow.source_asset_id=v_asset_id;

  INSERT INTO release.research_surface_citation_projection_v3
  SELECT p_release_id,s.archive_object_id,0,s.public_citation_label,s.public_source_route
  FROM release.research_surface_presentation_projection_v3 s WHERE s.research_release_id=p_release_id;

  INSERT INTO release.research_surface_credit_projection_v3
  SELECT p_release_id,c.archive_object_id,row_number() OVER (PARTITION BY c.archive_object_id ORDER BY ag.preferred_name,c.credit_role)-1,
    ag.preferred_name,c.credit_role
  FROM provenance.assignment_object_agent_credit c JOIN provenance.canonical_assignment a ON a.canonical_assignment_id=c.canonical_assignment_id
  JOIN core.agent ag ON ag.agent_id=c.agent_id JOIN release.research_release_object ro
    ON ro.research_release_id=p_release_id AND ro.archive_object_id=c.archive_object_id
  WHERE a.status='accepted' AND EXISTS (SELECT 1 FROM provenance.assignment_review_decision d JOIN provenance.assignment_decision_evidence e ON e.assignment_review_decision_id=d.assignment_review_decision_id AND e.evidence_role='supports' WHERE d.canonical_assignment_id=a.canonical_assignment_id AND d.outcome='accept' AND NOT EXISTS (SELECT 1 FROM provenance.assignment_review_decision n WHERE n.supersedes_decision_id=d.assignment_review_decision_id));

  INSERT INTO release.research_folder_type_projection_v3
  SELECT p_release_id,t.folder_type_code,t.type_label,t.type_sort_ordinal
  FROM research.folder_type_registry t WHERE EXISTS (
    SELECT 1 FROM research.folder_publication_metadata md JOIN provenance.assignment_folder_membership fm ON fm.folder_id=md.folder_id
    JOIN provenance.canonical_assignment a ON a.canonical_assignment_id=fm.canonical_assignment_id
    JOIN release.research_release_object ro ON ro.research_release_id=p_release_id AND ro.archive_object_id=fm.archive_object_id
    WHERE md.folder_type_code=t.folder_type_code AND a.status='accepted'
  );
  INSERT INTO release.research_folder_projection_v3
  SELECT p_release_id,f.folder_id,f.folder_token,md.folder_type_code,md.slug,f.label,md.scope_note,md.folder_sort_ordinal
  FROM research.folder f JOIN research.folder_publication_metadata md ON md.folder_id=f.folder_id
  WHERE EXISTS (SELECT 1 FROM provenance.assignment_folder_membership fm JOIN provenance.canonical_assignment a ON a.canonical_assignment_id=fm.canonical_assignment_id JOIN release.research_release_object ro ON ro.research_release_id=p_release_id AND ro.archive_object_id=fm.archive_object_id WHERE fm.folder_id=f.folder_id AND a.status='accepted');
  IF p_fault_point='after_folders' THEN RAISE EXCEPTION USING ERRCODE='P0001', MESSAGE='RESEARCH_LAUNCH_V3_FAULT_AFTER_FOLDERS'; END IF;

  INSERT INTO release.research_folder_membership_projection_v3
  SELECT p_release_id,fm.folder_id,fm.archive_object_id,a.canonical_assignment_id,fm.membership_role,fm.member_ordinal,a.status,
    release.research_launch_assignment_snapshot_sha_v3(a.canonical_assignment_id),d.assignment_review_decision_id,
    release.research_launch_decision_snapshot_sha_v3(d.assignment_review_decision_id)
  FROM provenance.assignment_folder_membership fm JOIN provenance.canonical_assignment a ON a.canonical_assignment_id=fm.canonical_assignment_id
  JOIN release.research_folder_projection_v3 f ON f.research_release_id=p_release_id AND f.folder_id=fm.folder_id
  JOIN release.research_release_object ro ON ro.research_release_id=p_release_id AND ro.archive_object_id=fm.archive_object_id
  JOIN LATERAL (SELECT d.assignment_review_decision_id FROM provenance.assignment_review_decision d
    WHERE d.canonical_assignment_id=a.canonical_assignment_id AND d.outcome='accept'
      AND NOT EXISTS (SELECT 1 FROM provenance.assignment_review_decision newer WHERE newer.supersedes_decision_id=d.assignment_review_decision_id)
      AND EXISTS (SELECT 1 FROM provenance.assignment_decision_evidence e WHERE e.assignment_review_decision_id=d.assignment_review_decision_id AND e.evidence_role='supports')) d ON true
  WHERE a.assignment_kind='folder_membership' AND a.status='accepted';
  IF p_fault_point='after_memberships' THEN RAISE EXCEPTION USING ERRCODE='P0001', MESSAGE='RESEARCH_LAUNCH_V3_FAULT_AFTER_MEMBERSHIPS'; END IF;

  INSERT INTO release.research_search_document_projection_v3
  SELECT p_release_id,s.archive_object_id,s.public_surface_id,s.title,
    coalesce(s.title,'')||' '||s.source_label,coalesce(s.title,'')||' '||s.public_surface_id
  FROM release.research_surface_presentation_projection_v3 s WHERE s.research_release_id=p_release_id;
  INSERT INTO release.research_corpus_summary_projection_v3
  SELECT p_release_id,cv.corpus_version_id,c.corpus_token,cv.version_token,c.label,
    count(*) FILTER (WHERE cm.disposition='eligible'),count(*) FILTER (WHERE cm.disposition='held')
  FROM research.corpus_version cv JOIN research.corpus c ON c.corpus_id=cv.corpus_id
  LEFT JOIN research.corpus_membership cm ON cm.corpus_version_id=cv.corpus_version_id
  WHERE cv.corpus_version_id=v_corpus_version_id
  GROUP BY cv.corpus_version_id,c.corpus_token,cv.version_token,c.label;

  INSERT INTO release.research_launch_source_disposition_count_v3
  SELECT p_release_id,'corpusMemberships',x.disposition,
    (SELECT count(*) FROM research.corpus_membership cm
      WHERE cm.corpus_version_id=v_corpus_version_id AND cm.disposition::text=x.disposition)
  FROM (VALUES ('eligible'),('held'),('rejected'),('excluded')) AS x(disposition)
  UNION ALL
  SELECT p_release_id,'folderAssignments',x.disposition,
    (SELECT count(*) FROM provenance.assignment_folder_membership fm
      JOIN provenance.canonical_assignment a ON a.canonical_assignment_id=fm.canonical_assignment_id
      JOIN research.corpus_membership cm ON cm.archive_object_id=fm.archive_object_id
        AND cm.corpus_version_id=v_corpus_version_id
      WHERE a.assignment_kind='folder_membership' AND a.status::text=x.disposition)
  FROM (VALUES ('proposed'),('accepted'),('rejected'),('superseded')) AS x(disposition);
  INSERT INTO release.research_trace_availability_projection_v3
  SELECT p_release_id,count(DISTINCT otn.archive_object_id),count(DISTINCT orm.semantic_relation_id),
    CASE WHEN count(DISTINCT otn.archive_object_id)=0 THEN 'no validated TRACE evidence in this release' ELSE 'validated TRACE evidence available' END
  FROM release.research_release_object ro
  LEFT JOIN research.object_trace_node otn ON otn.archive_object_id=ro.archive_object_id
  LEFT JOIN research.object_relation_membership orm ON orm.archive_object_id=ro.archive_object_id
  WHERE ro.research_release_id=p_release_id;

  INSERT INTO release.research_launch_component_manifest_v3
  SELECT p_release_id,x.component_code,x.row_count,release.research_launch_component_hash_v3(p_release_id,x.component_code)
  FROM (VALUES
    ('releaseObjects',(SELECT count(*) FROM release.research_release_object WHERE research_release_id=p_release_id)),
    ('surfacePresentation',(SELECT count(*) FROM release.research_surface_presentation_projection_v3 WHERE research_release_id=p_release_id)),
    ('surfaceCredits',(SELECT count(*) FROM release.research_surface_credit_projection_v3 WHERE research_release_id=p_release_id)),
    ('surfaceCitations',(SELECT count(*) FROM release.research_surface_citation_projection_v3 WHERE research_release_id=p_release_id)),
    ('folderTypes',(SELECT count(*) FROM release.research_folder_type_projection_v3 WHERE research_release_id=p_release_id)),
    ('folders',(SELECT count(*) FROM release.research_folder_projection_v3 WHERE research_release_id=p_release_id)),
    ('folderMemberships',(SELECT count(*) FROM release.research_folder_membership_projection_v3 WHERE research_release_id=p_release_id)),
    ('searchDocuments',(SELECT count(*) FROM release.research_search_document_projection_v3 WHERE research_release_id=p_release_id)),
    ('corpusSummary',(SELECT count(*) FROM release.research_corpus_summary_projection_v3 WHERE research_release_id=p_release_id)),
    ('traceAvailability',(SELECT count(*) FROM release.research_trace_availability_projection_v3 WHERE research_release_id=p_release_id))
  ) AS x(component_code,row_count);
  IF p_fault_point='after_component_hashes' THEN RAISE EXCEPTION USING ERRCODE='P0001', MESSAGE='RESEARCH_LAUNCH_V3_FAULT_AFTER_COMPONENT_HASHES'; END IF;

  IF EXISTS ((SELECT l.archive_object_id FROM raw.legacy_surface_ledger l JOIN research.corpus_membership cm ON cm.archive_object_id=l.archive_object_id AND cm.corpus_version_id=v_corpus_version_id AND cm.disposition='eligible' WHERE l.migration_batch_id=p_migration_batch_id AND l.import_disposition='accounted' AND l.archive_object_id IS NOT NULL)
    EXCEPT (SELECT archive_object_id FROM release.research_release_object WHERE research_release_id=p_release_id))
    OR EXISTS ((SELECT archive_object_id FROM release.research_release_object WHERE research_release_id=p_release_id)
    EXCEPT (SELECT l.archive_object_id FROM raw.legacy_surface_ledger l JOIN research.corpus_membership cm ON cm.archive_object_id=l.archive_object_id AND cm.corpus_version_id=v_corpus_version_id AND cm.disposition='eligible' WHERE l.migration_batch_id=p_migration_batch_id AND l.import_disposition='accounted' AND l.archive_object_id IS NOT NULL)) THEN
    RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='RESEARCH_LAUNCH_V3_OBJECT_COPY_PARITY_MISMATCH';
  END IF;
  IF EXISTS ((SELECT fm.folder_id,fm.archive_object_id,fm.membership_role,fm.member_ordinal FROM provenance.assignment_folder_membership fm JOIN provenance.canonical_assignment a ON a.canonical_assignment_id=fm.canonical_assignment_id JOIN release.research_release_object ro ON ro.research_release_id=p_release_id AND ro.archive_object_id=fm.archive_object_id WHERE a.status='accepted' AND EXISTS (SELECT 1 FROM provenance.assignment_review_decision d JOIN provenance.assignment_decision_evidence e ON e.assignment_review_decision_id=d.assignment_review_decision_id AND e.evidence_role='supports' WHERE d.canonical_assignment_id=a.canonical_assignment_id AND d.outcome='accept' AND NOT EXISTS (SELECT 1 FROM provenance.assignment_review_decision n WHERE n.supersedes_decision_id=d.assignment_review_decision_id)))
      EXCEPT (SELECT folder_id,archive_object_id,membership_role,member_ordinal FROM release.research_folder_membership_projection_v3 WHERE research_release_id=p_release_id)) THEN
    RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='RESEARCH_LAUNCH_V3_FOLDER_COPY_PARITY_MISMATCH';
  END IF;
  IF EXISTS ((SELECT folder_id,archive_object_id,membership_role,member_ordinal FROM release.research_folder_membership_projection_v3 WHERE research_release_id=p_release_id)
      EXCEPT (SELECT fm.folder_id,fm.archive_object_id,fm.membership_role,fm.member_ordinal FROM provenance.assignment_folder_membership fm JOIN provenance.canonical_assignment a ON a.canonical_assignment_id=fm.canonical_assignment_id JOIN release.research_release_object ro ON ro.research_release_id=p_release_id AND ro.archive_object_id=fm.archive_object_id WHERE a.status='accepted' AND EXISTS (SELECT 1 FROM provenance.assignment_review_decision d JOIN provenance.assignment_decision_evidence e ON e.assignment_review_decision_id=d.assignment_review_decision_id AND e.evidence_role='supports' WHERE d.canonical_assignment_id=a.canonical_assignment_id AND d.outcome='accept' AND NOT EXISTS (SELECT 1 FROM provenance.assignment_review_decision n WHERE n.supersedes_decision_id=d.assignment_review_decision_id)))) THEN
    RAISE EXCEPTION USING ERRCODE='23514', MESSAGE='RESEARCH_LAUNCH_V3_FOLDER_COPY_REVERSE_PARITY_MISMATCH';
  END IF;
  v_source_sha:=release.canonical_jsonb_sha256(jsonb_build_object('candidateAssetId',v_asset_id,'candidateAssetSha256',v_asset_sha,'migrationBatchId',p_migration_batch_id,'publicCorpusVersionId',v_corpus_version_id,'mappingSpecificationSha256',v_mapping_sha,'queryPackSha256',v_query_sha,'selectionPolicySha256',v_selection_sha,'registryCorpusPolicySha256',v_registry_sha,'sourceDispositions',COALESCE((SELECT jsonb_agg(jsonb_build_array(source_component,source_disposition,row_count) ORDER BY source_component,source_disposition) FROM release.research_launch_source_disposition_count_v3 WHERE research_release_id=p_release_id),'[]'::jsonb)));
  v_component_sha:=release.research_launch_component_manifest_sha_v3(p_release_id); v_content_sha:=release.research_launch_content_sha_v3(p_release_id);
  v_receipt_sha:=release.canonical_jsonb_sha256(jsonb_build_object('format','gda-v49-research-build-receipt-v3','source',v_source_sha,'components',v_component_sha,'content',v_content_sha));
  -- Fingerprint material is computed before the append-only receipt exists;
  -- the public helper below recomputes this exact representation from it.
  v_fingerprint:=release.canonical_jsonb_sha256(jsonb_build_object(
    'format','gda-v49-research-candidate-physical-v3','releaseId',p_release_id,
    'source',jsonb_build_object('candidateAssetId',v_asset_id,'candidateAssetSha256',v_asset_sha,
      'migrationBatchId',p_migration_batch_id,'publicCorpusVersionId',v_corpus_version_id,'mappingSpecificationSha256',v_mapping_sha,
      'projectionQueryPackSha256',v_query_sha,'selectionPolicySha256',v_selection_sha,
      'registryCorpusPolicySha256',v_registry_sha,'sourceSnapshotSha256',v_source_sha,
      'componentManifestSha256',v_component_sha,'contentSha256',v_content_sha),
    'components',COALESCE((SELECT jsonb_agg(jsonb_build_array(component_code,row_count,content_sha256)
      ORDER BY component_code) FROM release.research_launch_component_manifest_v3
      WHERE research_release_id=p_release_id),'[]'::jsonb)));
  INSERT INTO release.research_launch_build_receipt_v3(
    research_release_id,builder_version,migration_batch_id,public_corpus_version_id,
    candidate_asset_id,candidate_asset_sha256,mapping_specification_sha256,
    projection_query_pack_sha256,selection_policy_sha256,registry_corpus_policy_sha256,
    source_snapshot_sha256,projection_component_manifest_sha256,projection_content_sha256,
    build_receipt_sha256,candidate_fingerprint,built_at
  ) VALUES(p_release_id,'release-snapshot-v3',p_migration_batch_id,v_corpus_version_id,
    v_asset_id,v_asset_sha,v_mapping_sha,v_query_sha,v_selection_sha,v_registry_sha,
    v_source_sha,v_component_sha,v_content_sha,v_receipt_sha,v_fingerprint,clock_timestamp());
  IF p_fault_point='after_build_receipt' THEN RAISE EXCEPTION USING ERRCODE='P0001', MESSAGE='RESEARCH_LAUNCH_V3_FAULT_AFTER_RECEIPT'; END IF;
  IF p_fault_point='before_candidate_transition' THEN RAISE EXCEPTION USING ERRCODE='P0001', MESSAGE='RESEARCH_LAUNCH_V3_FAULT_BEFORE_CANDIDATE'; END IF;
  UPDATE release.research_release SET release_state='candidate',candidate_fingerprint=v_fingerprint,candidate_at=clock_timestamp() WHERE research_release_id=p_release_id;
  INSERT INTO audit.research_release_event VALUES(p_candidate_event_id,p_release_id,'draft','candidate',session_user::text,clock_timestamp(),p_candidate_event_sha256);
  RETURN v_fingerprint;
END
$function$;

CREATE FUNCTION release.validate_research_launch_snapshot_v3(
  p_release_id uuid,p_validation_receipt_sha256 core.sha256_hex,p_event_id uuid,p_event_sha256 core.sha256_hex
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $function$
DECLARE v_fingerprint core.sha256_hex; v_expected core.sha256_hex; x record;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  SELECT candidate_fingerprint INTO v_fingerprint FROM release.research_release WHERE research_release_id=p_release_id AND release_state='candidate' FOR UPDATE;
  IF NOT FOUND OR NOT EXISTS (SELECT 1 FROM release.research_launch_build_receipt_v3 WHERE research_release_id=p_release_id) THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='RESEARCH_LAUNCH_V3_NOT_VALIDATABLE'; END IF;
  IF (SELECT count(*) FROM release.research_launch_component_manifest_v3 WHERE research_release_id=p_release_id)<>10 THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RESEARCH_LAUNCH_V3_COMPONENT_REGISTRY_INCOMPLETE'; END IF;
  FOR x IN SELECT component_code,content_sha256 FROM release.research_launch_component_manifest_v3 WHERE research_release_id=p_release_id LOOP
    IF x.content_sha256 IS DISTINCT FROM release.research_launch_component_hash_v3(p_release_id,x.component_code) THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RESEARCH_LAUNCH_V3_COMPONENT_HASH_MISMATCH'; END IF;
  END LOOP;
  IF v_fingerprint IS DISTINCT FROM release.compute_research_launch_candidate_fingerprint_v3(p_release_id) OR v_fingerprint IS DISTINCT FROM (SELECT candidate_fingerprint FROM release.research_launch_build_receipt_v3 WHERE research_release_id=p_release_id) THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RESEARCH_LAUNCH_V3_FINGERPRINT_MISMATCH'; END IF;
  v_expected:=release.canonical_jsonb_sha256(jsonb_build_object('format','gda-v49-research-validation-v3','releaseId',p_release_id,'candidateFingerprint',v_fingerprint,'componentManifestSha256',release.research_launch_component_manifest_sha_v3(p_release_id)));
  IF p_validation_receipt_sha256 IS DISTINCT FROM v_expected THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RESEARCH_LAUNCH_V3_VALIDATION_RECEIPT_MISMATCH'; END IF;
  INSERT INTO release.research_launch_validation_v3 VALUES(p_release_id,v_fingerprint,p_validation_receipt_sha256,clock_timestamp());
  UPDATE release.research_release SET release_state='validated',validated_at=clock_timestamp() WHERE research_release_id=p_release_id;
  INSERT INTO audit.research_release_event VALUES(p_event_id,p_release_id,'candidate','validated',session_user::text,clock_timestamp(),p_event_sha256);
END
$function$;

CREATE FUNCTION release.seal_research_launch_snapshot_v3(
  p_release_id uuid,p_seal_event_id uuid,p_release_event_id uuid,p_event_sha256 core.sha256_hex
) RETURNS core.sha256_hex LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $function$
DECLARE v_bytes bytea; v_sha core.sha256_hex; v_fingerprint core.sha256_hex;
BEGIN
  PERFORM release.require_session_actor('gda_v49_phase2a_publisher');
  IF current_setting('transaction_isolation')<>'serializable' THEN RAISE EXCEPTION USING ERRCODE='25001',MESSAGE='RESEARCH_LAUNCH_V3_SEAL_REQUIRES_SERIALIZABLE'; END IF;
  SELECT candidate_fingerprint INTO v_fingerprint FROM release.research_release WHERE research_release_id=p_release_id AND release_state='validated' FOR UPDATE;
  IF NOT FOUND OR NOT EXISTS (SELECT 1 FROM release.research_launch_validation_v3 WHERE research_release_id=p_release_id AND candidate_fingerprint=v_fingerprint) THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='RESEARCH_LAUNCH_V3_PASS_RECEIPT_REQUIRED'; END IF;
  PERFORM release.validate_research_launch_snapshot_v3_integrity(p_release_id);
  v_bytes:=release.build_research_launch_manifest_bytes_v3(p_release_id); v_sha:=encode(sha256(v_bytes),'hex')::core.sha256_hex;
  INSERT INTO release.research_launch_manifest_v3 VALUES(p_release_id,v_bytes,v_sha,clock_timestamp());
  INSERT INTO release.research_release_manifest VALUES(p_release_id,v_bytes,v_sha,octet_length(v_bytes),clock_timestamp());
  UPDATE release.research_release SET release_state='sealed',manifest_sha256=v_sha,sealed_at=clock_timestamp() WHERE research_release_id=p_release_id;
  INSERT INTO audit.research_release_event VALUES(p_release_event_id,p_release_id,'validated','sealed',session_user::text,clock_timestamp(),p_event_sha256);
  INSERT INTO audit.research_seal_event(
    research_seal_event_id,research_release_id,manifest_sha256,actor,sealed_at,
    seal_transaction_id,candidate_fingerprint,seal_function_version
  ) VALUES(p_seal_event_id,p_release_id,v_sha,session_user::text,clock_timestamp(),
    txid_current(),v_fingerprint,'release-snapshot-v3');
  RETURN v_sha;
END
$function$;

CREATE FUNCTION release.validate_research_launch_snapshot_v3_integrity(p_release_id uuid)
RETURNS void LANGUAGE plpgsql STABLE SET search_path=pg_catalog AS $function$
DECLARE x record;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM release.research_launch_build_receipt_v3 WHERE research_release_id=p_release_id) THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RESEARCH_LAUNCH_V3_BUILD_RECEIPT_MISSING'; END IF;
  FOR x IN SELECT component_code,content_sha256 FROM release.research_launch_component_manifest_v3 WHERE research_release_id=p_release_id LOOP
    IF x.content_sha256 IS DISTINCT FROM release.research_launch_component_hash_v3(p_release_id,x.component_code) THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RESEARCH_LAUNCH_V3_COMPONENT_TAMPER'; END IF;
  END LOOP;
  IF (SELECT candidate_fingerprint FROM release.research_release WHERE research_release_id=p_release_id) IS DISTINCT FROM release.compute_research_launch_candidate_fingerprint_v3(p_release_id) THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='RESEARCH_LAUNCH_V3_FINGERPRINT_TAMPER'; END IF;
END
$function$;

-- Receipt-aware guards are attached after historical functions.  They also
-- cover release_object, preventing piecemeal builders from altering a v3
-- snapshot after the single-use receipt is written.
CREATE TRIGGER guard_research_launch_v3_folder_type BEFORE INSERT OR UPDATE OR DELETE ON release.research_folder_type_projection_v3 FOR EACH ROW EXECUTE FUNCTION release.guard_research_launch_snapshot_mutation_v3();
CREATE TRIGGER guard_research_launch_v3_folder BEFORE INSERT OR UPDATE OR DELETE ON release.research_folder_projection_v3 FOR EACH ROW EXECUTE FUNCTION release.guard_research_launch_snapshot_mutation_v3();
CREATE TRIGGER guard_research_launch_v3_member BEFORE INSERT OR UPDATE OR DELETE ON release.research_folder_membership_projection_v3 FOR EACH ROW EXECUTE FUNCTION release.guard_research_launch_snapshot_mutation_v3();
CREATE TRIGGER guard_research_launch_v3_surface BEFORE INSERT OR UPDATE OR DELETE ON release.research_surface_presentation_projection_v3 FOR EACH ROW EXECUTE FUNCTION release.guard_research_launch_snapshot_mutation_v3();
CREATE TRIGGER guard_research_launch_v3_credit BEFORE INSERT OR UPDATE OR DELETE ON release.research_surface_credit_projection_v3 FOR EACH ROW EXECUTE FUNCTION release.guard_research_launch_snapshot_mutation_v3();
CREATE TRIGGER guard_research_launch_v3_citation BEFORE INSERT OR UPDATE OR DELETE ON release.research_surface_citation_projection_v3 FOR EACH ROW EXECUTE FUNCTION release.guard_research_launch_snapshot_mutation_v3();
CREATE TRIGGER guard_research_launch_v3_search BEFORE INSERT OR UPDATE OR DELETE ON release.research_search_document_projection_v3 FOR EACH ROW EXECUTE FUNCTION release.guard_research_launch_snapshot_mutation_v3();
CREATE TRIGGER guard_research_launch_v3_corpus BEFORE INSERT OR UPDATE OR DELETE ON release.research_corpus_summary_projection_v3 FOR EACH ROW EXECUTE FUNCTION release.guard_research_launch_snapshot_mutation_v3();
CREATE TRIGGER guard_research_launch_v3_trace BEFORE INSERT OR UPDATE OR DELETE ON release.research_trace_availability_projection_v3 FOR EACH ROW EXECUTE FUNCTION release.guard_research_launch_snapshot_mutation_v3();
CREATE TRIGGER guard_research_launch_v3_component BEFORE INSERT OR UPDATE OR DELETE ON release.research_launch_component_manifest_v3 FOR EACH ROW EXECUTE FUNCTION release.guard_research_launch_snapshot_mutation_v3();
CREATE TRIGGER guard_research_launch_v3_source_disposition BEFORE INSERT OR UPDATE OR DELETE ON release.research_launch_source_disposition_count_v3 FOR EACH ROW EXECUTE FUNCTION release.guard_research_launch_snapshot_mutation_v3();
CREATE TRIGGER guard_research_launch_v3_release_object BEFORE INSERT OR UPDATE OR DELETE ON release.research_release_object FOR EACH ROW EXECUTE FUNCTION release.guard_research_launch_snapshot_mutation_v3();

CREATE TRIGGER research_launch_v3_receipt_append_only BEFORE UPDATE OR DELETE ON release.research_launch_build_receipt_v3 FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER research_launch_v3_validation_append_only BEFORE UPDATE OR DELETE ON release.research_launch_validation_v3 FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();
CREATE TRIGGER research_launch_v3_manifest_append_only BEFORE UPDATE OR DELETE ON release.research_launch_manifest_v3 FOR EACH ROW EXECUTE FUNCTION audit.reject_update_delete();

RESET ROLE;
