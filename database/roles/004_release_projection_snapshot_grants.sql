\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

-- Production publishing is forward-only from the v3 atomic builder.  These
-- revocations preserve historical functions and auditability while preventing
-- a publisher from assembling a v3 release through piecemeal writes.
REVOKE EXECUTE ON FUNCTION
  release.add_research_object_to_draft(uuid,uuid,uuid),
  release.add_research_claim_to_draft(uuid,uuid),
  release.add_research_relation_to_draft(uuid,uuid,uuid),
  release.add_trace_node_to_draft(uuid,uuid,uuid,uuid),
  release.add_trace_edge_to_draft(uuid,uuid,uuid,uuid,uuid,text),
  release.add_research_source_lineage_to_draft(uuid,release.research_source_role,uuid,text),
  release.set_research_projection_set_to_draft(uuid,text,core.sha256_hex,core.sha256_hex),
  release.set_research_registry_snapshot_to_draft(uuid,core.sha256_hex,core.sha256_hex,core.sha256_hex),
  release.copy_research_corpus_snapshot_to_draft(uuid,uuid,uuid,uuid,core.sha256_hex),
  release.add_research_count_snapshot_to_draft(uuid,core.release_token,text,text,core.sha256_hex,bigint),
  release.add_research_asset_to_draft(uuid,text,core.release_token,text,text,text,bigint,bigint,core.sha256_hex,text,text,core.sha256_hex),
  release.add_research_asset_dependency_to_draft(uuid,text,text),
  release.add_research_membership_projection_to_draft(uuid,uuid,uuid,uuid,text,release.publication_layer,text,release.count_eligibility,text),
  release.add_research_metric_eligibility_to_draft(uuid,uuid,text,release.count_eligibility,text),
  release.copy_research_folder_to_draft(uuid,uuid),
  release.copy_legacy_identity_resolution_to_draft(uuid,uuid,uuid),
  release.copy_trace_tree_to_draft(uuid,uuid,uuid),
  release.copy_trace_branch_to_draft(uuid,uuid,uuid,uuid),
  release.copy_trace_node_placement_to_draft(uuid,uuid,uuid,uuid,uuid,core.release_token),
  release.add_trace_edge_placement_to_draft(uuid,uuid,uuid,uuid,uuid,text,uuid,uuid,core.release_token)
FROM gda_v49_phase2a_publisher;

-- The legacy lifecycle invokes validators that read mutable canonical tables.
-- It remains present for historical releases, but a current publisher cannot
-- use it to close, validate, or seal a v3 launch snapshot.
REVOKE EXECUTE ON FUNCTION
  release.close_research_candidate(uuid,core.sha256_hex,uuid,core.sha256_hex),
  release.validate_research_release(uuid,uuid,core.release_token,core.sha256_hex,uuid,core.sha256_hex),
  release.seal_research_release(uuid,uuid,uuid,core.sha256_hex)
FROM gda_v49_phase2a_publisher;

GRANT EXECUTE ON FUNCTION
  release.build_research_launch_snapshot_v3(uuid,uuid,uuid,uuid,core.sha256_hex,text),
  release.validate_research_launch_snapshot_v3(uuid,core.sha256_hex,uuid,core.sha256_hex),
  release.seal_research_launch_snapshot_v3(uuid,uuid,uuid,core.sha256_hex)
TO gda_v49_phase2a_publisher;

-- api_reader receives no direct privilege on raw/core/provenance/research,
-- release snapshot tables, or write path.  011 will expose explicit api_v1
-- views; leaving this role view-only makes accidental base reads fail closed.
REVOKE ALL ON ALL TABLES IN SCHEMA raw, core, provenance, research, rights,
  workflow, release, audit FROM gda_v49_phase2a_api_reader;

RESET ROLE;
