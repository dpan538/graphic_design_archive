\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

REVOKE ALL ON SCHEMA exploration_v3, api_v3 FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA exploration_v3, api_v3 FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA exploration_v3, api_v3 FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA exploration_v3, api_v3 FROM PUBLIC;

DO $revoke_v50_types$
DECLARE v_type record;
BEGIN
  FOR v_type IN
    SELECT n.nspname, t.typname
    FROM pg_catalog.pg_type t
    JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname IN ('exploration_v3', 'api_v3')
      AND t.typtype IN ('c', 'd', 'e')
      AND t.typname NOT LIKE '\_%'
  LOOP
    EXECUTE pg_catalog.format(
      'REVOKE ALL PRIVILEGES ON TYPE %I.%I FROM PUBLIC',
      v_type.nspname, v_type.typname);
  END LOOP;
END
$revoke_v50_types$;

-- Reviewers see only the fail-closed research queue.  No runtime role gains
-- direct DML on governed association, composition, interaction, or export rows.
GRANT USAGE ON SCHEMA exploration_v3 TO gda_v49_phase2a_reviewer;
GRANT SELECT ON exploration_v3.reviewer_association_queue
  TO gda_v49_phase2a_reviewer;

GRANT USAGE ON SCHEMA api_v3 TO gda_v49_phase2a_api_reader;
GRANT SELECT ON
  api_v3.active_association,
  api_v3.active_scope,
  api_v3.active_concept,
  api_v3.active_concept_sense,
  api_v3.association_incidence,
  api_v3.association_evidence_locator,
  api_v3.active_association_synthesis_step,
  api_v3.active_association_synthesis_step_evidence,
  api_v3.active_association_internal_pair_link,
  api_v3.product_composition,
  api_v3.product_composition_realization,
  api_v3.product_composition_realization_incidence,
  api_v3.product_composition_coherence_review,
  api_v3.product_navigation_state,
  api_v3.product_navigation_node,
  api_v3.product_navigation_path_step,
  api_v3.product_transition,
  api_v3.product_workflow,
  api_v3.product_workflow_state,
  api_v3.product_workflow_association_revision,
  api_v3.product_workflow_association_realization,
  api_v3.product_workflow_transition,
  api_v3.product_export,
  api_v3.product_export_projection_preservation
TO gda_v49_phase2a_api_reader;

GRANT USAGE ON SCHEMA audit TO gda_v49_phase2a_auditor;
GRANT SELECT ON audit.exploration_v3_inventory TO gda_v49_phase2a_auditor;

RESET ROLE;
