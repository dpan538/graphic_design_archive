\set ON_ERROR_STOP on
SET ROLE gda_v49_phase2a_schema_owner;

-- Positive allowlist: production records are invisible until every semantic,
-- evidence, authority, coherence, and product gate has passed.
CREATE VIEW api_v3.active_association
WITH (security_barrier = true)
AS
SELECT a.association_id, r.association_revision_id,
  a.association_kind::text AS association_kind, a.arity,
  a.order_semantics::text AS order_semantics, a.roles_meaningful,
  a.pair_projection_policy::text AS pair_projection_policy,
  r.scope_id, r.support_mode::text AS support_mode,
  rv.disposition::text AS review_disposition,
  rv.global_coherence::text AS global_coherence,
  rv.review_version, rv.bounded_senses_compatible,
  rv.case_scope_compatible, rv.roles_and_topology_supported,
  rv.unsupported_bridge_count, rv.semantic_sha256 AS review_semantic_sha256,
  rv.qualifications AS review_qualifications,
  rv.explicit_non_claims AS review_explicit_non_claims,
  au.authority_kind::text AS review_authority_kind,
  au.authority_version AS review_authority_version,
  au.authority_sha256 AS review_authority_sha256,
  r.semantic_version, r.semantic_sha256, r.presentation_sha256,
  r.product_path, r.qualifications, r.scope_context_qualifications,
  r.explicit_non_claims,
  r.evidence_complete, r.same_configuration, r.conflicts_resolved,
  r.rights_cleared_for_governed_use, r.synthesis_complete,
  r.uncertainty_status::text AS uncertainty_status,
  r.uncertainty_level::text AS uncertainty_level,
  r.uncertainty_activation_policy::text AS uncertainty_activation_policy,
  (SELECT count(*) FROM exploration_v3.association_revision_evidence e
    WHERE e.association_revision_id = r.association_revision_id
      AND e.evidence_role = 'supports') AS supporting_evidence_count,
  (SELECT count(DISTINCT l.locator_id)
    FROM exploration_v3.association_revision_evidence e
    JOIN exploration_v3.evidence_locator l
      ON l.evidence_reference_id = e.evidence_reference_id
    WHERE e.association_revision_id = r.association_revision_id)
    AS evidence_locator_count
FROM exploration_v3.association a
JOIN exploration_v3.association_revision r USING (association_id)
JOIN exploration_v3.association_review rv USING (association_revision_id)
JOIN exploration_v3.governed_authority au ON au.authority_id = rv.authority_id
WHERE a.realm = 'PRODUCTION'
  AND r.lifecycle_state = 'ACTIVE' AND r.product_eligible
  AND r.activation_decision = 'ALLOW' AND r.all_activation_gates_pass
  AND r.evidence_complete AND r.same_configuration AND r.conflicts_resolved
  AND r.rights_cleared_for_governed_use AND r.synthesis_complete
  AND r.uncertainty_status = 'RESOLVED_BOUNDED'
  AND r.uncertainty_level <> 'UNKNOWN'
  AND r.uncertainty_activation_policy = 'ALLOWED_BOUNDED'
  AND rv.review_state = 'FINAL' AND rv.global_coherence = 'PASS'
  AND rv.bounded_senses_compatible AND rv.case_scope_compatible
  AND rv.roles_and_topology_supported AND rv.unsupported_bridge_count = 0
  AND au.authority_state = 'FINAL'
  AND au.authority_kind <> 'SYNTHETIC_TEST_AUTHORITY'
  AND EXISTS (
    SELECT 1 FROM exploration_v3.aggregate_seal seal
    WHERE seal.aggregate_kind = 'ASSOCIATION_REVISION'
      AND seal.aggregate_id = r.association_revision_id)
  AND EXISTS (
    SELECT 1 FROM exploration_v3.association_revision_evidence evidence
    JOIN exploration_v3.evidence_reference reference
      ON reference.evidence_reference_id = evidence.evidence_reference_id
    WHERE evidence.association_revision_id = r.association_revision_id
      AND evidence.evidence_role = 'supports'
      AND reference.realm = 'PRODUCTION'
      AND reference.rights_cleared_for_governed_use
      AND EXISTS (SELECT 1 FROM exploration_v3.evidence_locator locator
        WHERE locator.evidence_reference_id = reference.evidence_reference_id)
      AND EXISTS (SELECT 1 FROM exploration_v3.aggregate_seal evidence_seal
        WHERE evidence_seal.aggregate_kind = 'EVIDENCE_REFERENCE'
          AND evidence_seal.aggregate_id = reference.evidence_reference_id))
  AND NOT EXISTS (
    SELECT 1 FROM exploration_v3.association_revision successor
    WHERE successor.association_id = r.association_id
      AND successor.supersedes_association_revision_id = r.association_revision_id);

CREATE VIEW api_v3.active_scope
WITH (security_barrier = true)
AS
SELECT DISTINCT s.scope_id, s.historical_case_ids, s.time_start, s.time_end,
  s.geographies, s.institutions, s.actors, s.mechanisms,
  s.context_qualifications, s.semantic_sha256
FROM exploration_v3.governed_scope s
JOIN (
  SELECT a.scope_id FROM api_v3.active_association a
  UNION
  SELECT i.participant_scope_id
  FROM api_v3.active_association a
  JOIN exploration_v3.association_incidence i USING (association_revision_id)
) governed_active_scope ON governed_active_scope.scope_id = s.scope_id
WHERE s.realm = 'PRODUCTION';

CREATE VIEW api_v3.active_concept
WITH (security_barrier = true)
AS
SELECT DISTINCT c.concept_id, c.canonical_label, c.semantic_version,
  c.semantic_sha256, c.product_path, c.authority_id,
  au.authority_kind::text AS authority_kind,
  au.authority_version, au.authority_sha256
FROM api_v3.active_association a
JOIN exploration_v3.association_incidence i USING (association_revision_id)
JOIN exploration_v3.concept c ON c.concept_id = i.concept_id
JOIN exploration_v3.governed_authority au ON au.authority_id = c.authority_id
WHERE c.realm = 'PRODUCTION' AND c.lifecycle_state = 'ACTIVE'
  AND c.association_eligible AND c.product_eligible
  AND au.authority_state = 'FINAL'
  AND au.authority_kind <> 'SYNTHETIC_TEST_AUTHORITY';

CREATE VIEW api_v3.active_concept_sense
WITH (security_barrier = true)
AS
SELECT DISTINCT s.sense_id, s.concept_id, s.bounded_definition,
  s.semantic_version, s.semantic_sha256, s.vocabulary_crosswalk_ids,
  i.participant_scope_id, s.authority_id,
  au.authority_kind::text AS authority_kind,
  au.authority_version, au.authority_sha256
FROM api_v3.active_association a
JOIN exploration_v3.association_incidence i USING (association_revision_id)
JOIN exploration_v3.concept_sense s
  ON s.sense_id = i.sense_id AND s.concept_id = i.concept_id
JOIN exploration_v3.governed_authority au ON au.authority_id = s.authority_id
WHERE s.realm = 'PRODUCTION' AND s.lifecycle_state = 'ACTIVE'
  AND s.association_eligible AND s.product_eligible
  AND au.authority_state = 'FINAL'
  AND au.authority_kind <> 'SYNTHETIC_TEST_AUTHORITY';

-- Only stable, rights-cleared provenance identity is public.  Internal source
-- notes, access conditions, raw source IDs, and retained evidence bytes remain
-- behind the governed research boundary.
CREATE VIEW api_v3.association_evidence_locator
WITH (security_barrier = true)
AS
SELECT a.association_id, a.association_revision_id,
  e.evidence_reference_id, bridge.evidence_role::text AS evidence_role,
  e.evidence_sha256, e.negative_or_conflicting,
  l.locator_id, l.stable_locator, l.locator_sha256,
  cr.conflict_resolution_id,
  cr.resolution_state::text AS conflict_resolution_state,
  cau.authority_kind::text AS conflict_authority_kind,
  cau.authority_version AS conflict_authority_version,
  cau.authority_sha256 AS conflict_authority_sha256
FROM api_v3.active_association a
JOIN exploration_v3.association_revision_evidence bridge
  USING (association_revision_id)
JOIN exploration_v3.evidence_reference e
  ON e.evidence_reference_id = bridge.evidence_reference_id
JOIN exploration_v3.evidence_locator l
  ON l.evidence_reference_id = e.evidence_reference_id
LEFT JOIN exploration_v3.association_conflict_resolution cr
  ON cr.association_revision_id = bridge.association_revision_id
 AND cr.evidence_reference_id = bridge.evidence_reference_id
LEFT JOIN exploration_v3.governed_authority cau ON cau.authority_id = cr.authority_id
WHERE e.realm = 'PRODUCTION' AND e.rights_cleared_for_governed_use;

CREATE VIEW api_v3.association_incidence
WITH (security_barrier = true)
AS
SELECT active.association_id, active.association_revision_id,
  i.incidence_id, i.concept_id, i.sense_id, i.ordinal, i.role_id,
  i.participant_scope_id, i.qualifications
FROM api_v3.active_association active
JOIN exploration_v3.association_incidence i USING (association_revision_id);

CREATE VIEW api_v3.active_association_synthesis_step
WITH (security_barrier = true)
AS
SELECT active.association_id, active.association_revision_id,
  step.step_ordinal, step.synthesis_statement, step.bridge_supported
FROM api_v3.active_association active
JOIN exploration_v3.association_synthesis_step step USING (association_revision_id);

CREATE VIEW api_v3.active_association_synthesis_step_evidence
WITH (security_barrier = true)
AS
SELECT step.association_id, step.association_revision_id, step.step_ordinal,
  evidence.evidence_reference_id
FROM api_v3.active_association_synthesis_step step
JOIN exploration_v3.association_synthesis_step_evidence evidence
  USING (association_revision_id, step_ordinal)
JOIN exploration_v3.association_revision_evidence governed_evidence
  ON governed_evidence.association_revision_id = evidence.association_revision_id
 AND governed_evidence.evidence_reference_id = evidence.evidence_reference_id
 AND governed_evidence.evidence_role IN ('supports','contextualises');

CREATE VIEW api_v3.active_association_internal_pair_link
WITH (security_barrier = true)
AS
SELECT higher.association_id AS higher_order_association_id,
  higher.association_revision_id AS higher_order_revision_id,
  pair.association_id AS pair_association_id,
  pair.association_revision_id AS pair_revision_id,
  link.higher_incidence_a, link.higher_incidence_b,
  link.pair_incidence_a, link.pair_incidence_b
FROM api_v3.active_association higher
JOIN exploration_v3.internal_pair_link link
  ON link.higher_order_revision_id = higher.association_revision_id
JOIN api_v3.active_association pair
  ON pair.association_revision_id = link.pair_revision_id
WHERE higher.association_kind = 'HIGHER_ORDER' AND pair.association_kind = 'PAIR';

CREATE VIEW api_v3.product_composition
WITH (security_barrier = true)
AS
SELECT c.composition_id, r.composition_revision_id, r.topology_family,
  r.semantic_sha256, r.presentation_sha256, r.product_path,
  rv.composition_coherence_review_id,
  rv.global_coherence::text AS global_coherence,
  (SELECT count(*) FROM exploration_v3.composition_node n
    WHERE n.composition_revision_id = r.composition_revision_id) AS node_count,
  (SELECT count(*) FROM exploration_v3.association_realization ar
    WHERE ar.composition_revision_id = r.composition_revision_id)
    AS association_realization_count
FROM exploration_v3.composition c
JOIN exploration_v3.composition_revision r USING (composition_id)
JOIN exploration_v3.composition_coherence_review rv USING (composition_revision_id)
JOIN exploration_v3.governed_authority au ON au.authority_id = rv.authority_id
WHERE c.realm = 'PRODUCTION' AND r.product_eligible
  AND r.association_trace_complete AND r.renderability = 'PASS'
  AND rv.review_state = 'FINAL' AND rv.decision = 'COHERENT'
  AND rv.global_coherence = 'PASS' AND rv.bounded_senses_compatible
  AND rv.case_scope_compatible AND rv.roles_and_topology_supported
  AND rv.same_configuration AND rv.unsupported_bridge_count = 0
  AND au.authority_state = 'FINAL'
  AND au.authority_kind <> 'SYNTHETIC_TEST_AUTHORITY'
  AND EXISTS (
    SELECT 1 FROM exploration_v3.aggregate_seal seal
    WHERE seal.aggregate_kind = 'COMPOSITION_REVISION'
      AND seal.aggregate_id = r.composition_revision_id)
  AND NOT EXISTS (
    SELECT 1 FROM exploration_v3.association_realization realization
    WHERE realization.composition_revision_id = r.composition_revision_id
      AND NOT EXISTS (
        SELECT 1 FROM api_v3.active_association active
        WHERE active.association_revision_id = realization.association_revision_id))
  AND NOT EXISTS (
    SELECT 1 FROM exploration_v3.composition_revision successor
    WHERE successor.composition_id = r.composition_id
      AND successor.supersedes_composition_revision_id = r.composition_revision_id);

CREATE VIEW api_v3.product_composition_realization
WITH (security_barrier = true)
AS
SELECT c.composition_id, c.composition_revision_id,
  ar.association_realization_id, ar.association_revision_id,
  ar.realization_kind::text AS realization_kind,
  ar.semantic_sha256, ar.presentation_sha256, ar.layout, ar.style
FROM api_v3.product_composition c
JOIN exploration_v3.association_realization ar USING (composition_revision_id)
JOIN api_v3.active_association a USING (association_revision_id);

CREATE VIEW api_v3.product_composition_realization_incidence
WITH (security_barrier = true)
AS
SELECT r.composition_id, r.composition_revision_id,
  r.association_realization_id, r.association_revision_id,
  incidence.incidence_id, incidence.concept_id, incidence.sense_id,
  incidence.ordinal, incidence.role_id, incidence.participant_scope_id
FROM api_v3.product_composition_realization r
JOIN exploration_v3.realization_incidence mapping
  USING (association_realization_id)
JOIN api_v3.association_incidence incidence
  ON incidence.association_revision_id = r.association_revision_id
 AND incidence.incidence_id = mapping.incidence_id;

CREATE VIEW api_v3.product_composition_coherence_review
WITH (security_barrier = true)
AS
SELECT c.composition_id, c.composition_revision_id,
  rv.composition_coherence_review_id, rv.review_version,
  rv.global_coherence::text AS global_coherence,
  rv.bounded_senses_compatible, rv.case_scope_compatible,
  rv.roles_and_topology_supported, rv.same_configuration,
  rv.unsupported_bridge_count, rv.decision::text AS decision,
  rv.reasons, rv.semantic_sha256,
  au.authority_kind::text AS authority_kind,
  au.authority_version, au.authority_sha256
FROM api_v3.product_composition c
JOIN exploration_v3.composition_coherence_review rv USING (composition_revision_id)
JOIN exploration_v3.governed_authority au ON au.authority_id = rv.authority_id
WHERE rv.realm = 'PRODUCTION' AND rv.review_state = 'FINAL'
  AND au.authority_state = 'FINAL'
  AND au.authority_kind <> 'SYNTHETIC_TEST_AUTHORITY';

CREATE VIEW api_v3.product_navigation_state
WITH (security_barrier = true)
AS
SELECT s.state_id, s.composition_revision_id, s.focus_navigation_node_id,
  s.semantic_sha256, s.presentation_sha256, s.focus_style, s.viewport
FROM exploration_v3.navigation_state s
JOIN api_v3.product_composition c USING (composition_revision_id)
WHERE s.realm = 'PRODUCTION' AND s.bipartite_alternation_valid;

CREATE VIEW api_v3.product_navigation_node
WITH (security_barrier = true)
AS
SELECT s.state_id, s.composition_revision_id,
  n.navigation_node_id, n.node_kind::text AS node_kind,
  n.concept_id, n.association_revision_id
FROM api_v3.product_navigation_state s
JOIN exploration_v3.navigation_node n USING (state_id)
WHERE (n.node_kind = 'CONCEPT' AND EXISTS (
    SELECT 1 FROM api_v3.active_concept c WHERE c.concept_id = n.concept_id))
  OR (n.node_kind = 'ASSOCIATION' AND EXISTS (
    SELECT 1 FROM api_v3.active_association a
    WHERE a.association_revision_id = n.association_revision_id));

CREATE VIEW api_v3.product_navigation_path_step
WITH (security_barrier = true)
AS
SELECT s.state_id, s.composition_revision_id, p.step_ordinal,
  p.from_navigation_node_id, p.incidence_id, p.to_navigation_node_id
FROM api_v3.product_navigation_state s
JOIN exploration_v3.navigation_path_step p USING (state_id)
JOIN api_v3.product_navigation_node source_node
  ON source_node.state_id = p.state_id
 AND source_node.navigation_node_id = p.from_navigation_node_id
JOIN api_v3.product_navigation_node target_node
  ON target_node.state_id = p.state_id
 AND target_node.navigation_node_id = p.to_navigation_node_id
JOIN api_v3.association_incidence active_incidence
  ON active_incidence.incidence_id = p.incidence_id
 AND active_incidence.association_revision_id = COALESCE(
   source_node.association_revision_id, target_node.association_revision_id);

CREATE VIEW api_v3.product_transition
WITH (security_barrier = true)
AS
SELECT t.transition_id, t.from_state_id, t.to_state_id,
  t.transition_kind::text AS transition_kind, t.incidence_id,
  t.association_revision_id, t.association_realization_id,
  t.state_mutated, t.semantic_sha256, t.product_path
FROM exploration_v3.interaction_transition t
JOIN api_v3.product_navigation_state f ON f.state_id = t.from_state_id
JOIN api_v3.product_navigation_state target ON target.state_id = t.to_state_id
WHERE t.realm = 'PRODUCTION' AND t.product_eligible
  AND (t.association_revision_id IS NULL OR EXISTS (
    SELECT 1 FROM api_v3.active_association active
    JOIN api_v3.association_incidence incidence
      ON incidence.association_revision_id = active.association_revision_id
    JOIN api_v3.product_composition_realization realization
      ON realization.association_revision_id = active.association_revision_id
     AND realization.association_realization_id = t.association_realization_id
    WHERE active.association_revision_id = t.association_revision_id
      AND incidence.incidence_id = t.incidence_id));

CREATE VIEW api_v3.product_workflow
WITH (security_barrier = true)
AS
SELECT w.workflow_id, w.initial_state_id,
  w.transition_kind::text AS transition_kind, w.reachable,
  w.semantic_sha256, w.product_path
FROM exploration_v3.exploration_workflow w
JOIN api_v3.product_navigation_state s ON s.state_id = w.initial_state_id
WHERE w.realm = 'PRODUCTION' AND w.product_eligible AND w.reachable
  AND NOT EXISTS (
    SELECT 1 FROM exploration_v3.workflow_transition wt
    LEFT JOIN api_v3.product_transition t ON t.transition_id = wt.transition_id
    WHERE wt.workflow_id = w.workflow_id AND t.transition_id IS NULL)
  AND NOT EXISTS (
    SELECT 1 FROM exploration_v3.workflow_state ws
    LEFT JOIN api_v3.product_navigation_state state ON state.state_id = ws.state_id
    WHERE ws.workflow_id = w.workflow_id AND state.state_id IS NULL)
  AND NOT EXISTS (
    SELECT 1 FROM exploration_v3.workflow_association_revision wr
    LEFT JOIN api_v3.active_association active
      ON active.association_revision_id = wr.association_revision_id
    WHERE wr.workflow_id = w.workflow_id AND active.association_revision_id IS NULL)
  AND NOT EXISTS (
    SELECT 1 FROM exploration_v3.workflow_association_realization wr
    LEFT JOIN api_v3.product_composition_realization realization
      ON realization.association_realization_id = wr.association_realization_id
    WHERE wr.workflow_id = w.workflow_id
      AND realization.association_realization_id IS NULL);

CREATE VIEW api_v3.product_workflow_state
WITH (security_barrier = true)
AS
SELECT w.workflow_id, s.state_id, s.composition_revision_id,
  s.focus_navigation_node_id
FROM api_v3.product_workflow w
JOIN exploration_v3.workflow_state ws USING (workflow_id)
JOIN api_v3.product_navigation_state s ON s.state_id = ws.state_id;

CREATE VIEW api_v3.product_workflow_association_revision
WITH (security_barrier = true)
AS
SELECT w.workflow_id, a.association_id, a.association_revision_id
FROM api_v3.product_workflow w
JOIN exploration_v3.workflow_association_revision wr USING (workflow_id)
JOIN api_v3.active_association a USING (association_revision_id);

CREATE VIEW api_v3.product_workflow_association_realization
WITH (security_barrier = true)
AS
SELECT w.workflow_id, r.composition_revision_id,
  r.association_realization_id, r.association_revision_id,
  r.realization_kind
FROM api_v3.product_workflow w
JOIN exploration_v3.workflow_association_realization wr USING (workflow_id)
JOIN api_v3.product_composition_realization r
  USING (association_realization_id);

CREATE VIEW api_v3.product_workflow_transition
WITH (security_barrier = true)
AS
SELECT w.workflow_id, t.transition_id, t.from_state_id, t.to_state_id,
  t.transition_kind, t.incidence_id, t.association_revision_id,
  t.association_realization_id
FROM api_v3.product_workflow w
JOIN exploration_v3.workflow_transition wt USING (workflow_id)
JOIN api_v3.product_transition t USING (transition_id);

CREATE VIEW api_v3.product_export
WITH (security_barrier = true)
AS
SELECT e.export_id, e.workflow_id, e.state_id, e.composition_revision_id,
  e.semantic_sha256, e.presentation_sha256, e.export_format, e.theme,
  e.pair_projection_policy_preserved, e.product_path
FROM exploration_v3.export_manifest e
JOIN api_v3.product_workflow w USING (workflow_id)
JOIN api_v3.product_navigation_state s USING (state_id, composition_revision_id)
WHERE e.realm = 'PRODUCTION' AND e.product_eligible
  AND e.pair_projection_policy_preserved
  AND NOT EXISTS (
    SELECT 1 FROM exploration_v3.export_projection_preservation preservation
    WHERE preservation.export_id = e.export_id
      AND NOT EXISTS (
        SELECT 1 FROM api_v3.active_association active
        JOIN api_v3.product_composition_realization realization
          ON realization.association_revision_id = active.association_revision_id
        WHERE active.association_revision_id = preservation.association_revision_id
          AND realization.composition_revision_id = e.composition_revision_id
          AND realization.association_realization_id =
            preservation.association_realization_id));

CREATE VIEW api_v3.product_export_projection_preservation
WITH (security_barrier = true)
AS
SELECT e.export_id, e.workflow_id, e.state_id, e.composition_revision_id,
  p.association_revision_id, p.association_realization_id,
  p.pair_projection_policy::text AS pair_projection_policy,
  p.realization_kind::text AS realization_kind
FROM api_v3.product_export e
JOIN exploration_v3.export_projection_preservation p USING (export_id)
JOIN api_v3.active_association a USING (association_revision_id)
JOIN api_v3.product_composition_realization r
  ON r.composition_revision_id = e.composition_revision_id
 AND r.association_revision_id = p.association_revision_id
 AND r.association_realization_id = p.association_realization_id;

CREATE VIEW exploration_v3.reviewer_association_queue
WITH (security_barrier = true)
AS
SELECT a.association_id, r.association_revision_id,
  a.association_kind::text AS association_kind, a.arity,
  r.lifecycle_state::text AS lifecycle_state,
  coalesce(rv.review_state::text, 'MISSING') AS review_state,
  rv.disposition::text AS disposition,
  rv.global_coherence::text AS global_coherence,
  r.evidence_complete, r.same_configuration, r.conflicts_resolved,
  r.rights_cleared_for_governed_use, r.synthesis_complete,
  r.created_at
FROM exploration_v3.association a
JOIN exploration_v3.association_revision r USING (association_id)
LEFT JOIN exploration_v3.association_review rv USING (association_revision_id)
WHERE a.realm = 'PRODUCTION'
  AND (r.lifecycle_state <> 'ACTIVE' OR rv.review_state IS DISTINCT FROM 'FINAL'
    OR rv.global_coherence IS DISTINCT FROM 'PASS');

CREATE VIEW audit.exploration_v3_inventory
WITH (security_barrier = true)
AS
SELECT
  (SELECT count(*) FROM exploration_v3.concept) AS concept_count,
  (SELECT count(*) FROM exploration_v3.concept_sense) AS concept_sense_count,
  (SELECT count(*) FROM exploration_v3.association a
    WHERE a.association_kind = 'PAIR') AS pair_association_count,
  (SELECT count(*) FROM exploration_v3.association a
    WHERE a.association_kind = 'HIGHER_ORDER') AS higher_order_association_count,
  (SELECT count(*) FROM exploration_v3.association_incidence) AS incidence_count,
  (SELECT count(*) FROM exploration_v3.association_revision r
    JOIN exploration_v3.association a USING (association_id)
    WHERE a.realm = 'PRODUCTION' AND r.lifecycle_state = 'ACTIVE')
    AS production_active_association_count,
  (SELECT count(*) FROM exploration_v3.association_revision r
    JOIN exploration_v3.association a USING (association_id)
    LEFT JOIN exploration_v3.association_review rv USING (association_revision_id)
    WHERE a.realm = 'PRODUCTION' AND r.lifecycle_state = 'ACTIVE'
      AND (rv.review_state IS DISTINCT FROM 'FINAL'
        OR rv.global_coherence IS DISTINCT FROM 'PASS'))
    AS active_pending_or_incoherent_count,
  (SELECT count(*) FROM exploration_v3.internal_pair_link) AS explicit_internal_pair_link_count,
  0::bigint AS implicit_projected_pair_count,
  (SELECT count(*) FROM exploration_v3.composition_revision) AS composition_revision_count,
  (SELECT count(*) FROM exploration_v3.navigation_state) AS navigation_state_count,
  (SELECT count(*) FROM exploration_v3.interaction_transition) AS transition_count,
  (SELECT count(*) FROM exploration_v3.exploration_workflow) AS workflow_count,
  (SELECT count(*) FROM exploration_v3.export_manifest) AS export_count;

RESET ROLE;
