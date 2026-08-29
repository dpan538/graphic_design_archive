#!/usr/bin/env python3
"""Build the deterministic Round 16B higher-order method checkpoint."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw"
SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
METHOD_VERSION = "trace-round16b-higher-order-association-method-v1"


def surface(
    surface_id: str,
    round_id: str,
    path: str,
    selector: str,
    authority: str,
    triggers: str,
    boundary: str,
) -> dict[str, str]:
    return {
        "surface_id": surface_id,
        "round": round_id,
        "path": path,
        "record_selector": selector,
        "evidence_authority": authority,
        "candidate_trigger_ids": triggers,
        "use_boundary": boundary,
    }


SURFACES = [
    surface("SURF-R09-001", "ROUND9", "docs/research/trace-v49-design-history-relation-vocabulary-round1/03_SCHOLARLY_SOURCE_REGISTRY.tsv", "tsv_rows", "BIBLIOGRAPHIC_IDENTITY", "TRG-002;TRG-003;TRG-006", "Discovery identity; a source row alone is not association evidence."),
    surface("SURF-R09-002", "ROUND9", "docs/research/trace-v49-design-history-relation-vocabulary-round1/04_RAW_CANDIDATE_TERM_REGISTRY.tsv", "tsv_rows", "GOVERNED_VOCABULARY_DISCOVERY", "TRG-006;TRG-012", "Candidate terms require bounded-sense and disposition reconciliation."),
    surface("SURF-R09-003", "ROUND9", "docs/research/trace-v49-design-history-relation-vocabulary-round1/05_TERM_ATTESTATION_REGISTRY.tsv", "tsv_rows", "LOCATOR_BEARING_CONCEPT_EVIDENCE", "TRG-002;TRG-003;TRG-005;TRG-006", "Concept attestation can trigger a group review but cannot alone validate a group."),
    surface("SURF-R09-004", "ROUND9", "docs/research/trace-v49-design-history-relation-vocabulary-round1/07_SEMANTIC_GLOSS_REGISTRY.tsv", "tsv_rows", "GOVERNED_BOUNDED_SENSE", "TRG-002;TRG-003;TRG-005;TRG-006", "Exact sense identity governs matching; labels alone are insufficient."),
    surface("SURF-R09-005", "ROUND9", "docs/research/trace-v49-design-history-relation-vocabulary-round1/12_REJECTED_AND_DEFERRED_TERMS.tsv", "tsv_rows", "NEGATIVE_AND_DEFERRED_CONTROL", "TRG-006;TRG-007;TRG-012", "Rejected or deferred senses cannot become active without a new governed decision."),
    surface("SURF-R10-001", "ROUND10", "docs/research/trace-v49-design-history-relation-grammar-round1/03_GRAMMAR_SCHOLARLY_SOURCE_REGISTRY.tsv", "tsv_rows", "BIBLIOGRAPHIC_IDENTITY", "TRG-001;TRG-002;TRG-003", "Source identity only until locator-bearing grammar evidence is reviewed."),
    surface("SURF-R10-002", "ROUND10", "docs/research/trace-v49-design-history-relation-grammar-round1/06_ARGUMENT_ROLE_REGISTRY.tsv", "tsv_rows", "GOVERNED_ROLE_AND_ARITY_DISCOVERY", "TRG-001;TRG-012", "Arity and role language trigger participant review; they do not create a hyperedge."),
    surface("SURF-R10-003", "ROUND10", "docs/research/trace-v49-design-history-relation-grammar-round1/07_GRAMMAR_ATTESTATION_REGISTRY.tsv", "tsv_rows", "LOCATOR_BEARING_GRAMMAR_EVIDENCE", "TRG-001;TRG-002;TRG-003", "Review exact senses, roles, parties, case, and qualifications as a whole."),
    surface("SURF-R10-004", "ROUND10", "docs/research/trace-v49-design-history-relation-grammar-round1/08_ORDERED_PAIR_COMPATIBILITY_MATRIX.tsv", "tsv_rows", "PAIRWISE_NEGATIVE_CONTROL", "TRG-007;TRG-011", "Pair decisions cannot decide a higher-order group, but they constrain pair projection."),
    surface("SURF-R10-005", "ROUND10", "docs/research/trace-v49-design-history-relation-grammar-round1/14_CLUSTER_EVIDENCE_HANDOFF.tsv", "tsv_rows", "EXPLICIT_GROUP_NEAR_MISS", "TRG-001;TRG-007", "Deferred clusters are mandatory negative or inquiry candidates."),
    surface("SURF-R10-006", "ROUND10", "docs/research/trace-v49-design-history-relation-grammar-round1/15_OBSERVED_RELATION_CHAIN_REGISTRY.tsv", "tsv_rows", "SOURCE_BOUNDED_CHAIN_CONTROL", "TRG-003;TRG-007;TRG-011", "Observed chains do not authorize transitivity or direction beyond their locus."),
    surface("SURF-R10-007", "ROUND10", "docs/research/trace-v49-design-history-relation-grammar-round1/20_VOCABULARY_GAP_REGISTER.tsv", "tsv_rows", "OPEN_GAP_DISCOVERY", "TRG-006;TRG-012", "Open gaps remain inquiry-only until independently resolved."),
    surface("SURF-R11-001", "ROUND11", "docs/research/trace-v49-exploration-constraint-kernel-round1/04_CONSTRAINT_REGISTRY.tsv", "tsv_rows", "MODEL_CONSTRAINT", "TRG-007;TRG-012", "Constraint mechanics are not historical association evidence."),
    surface("SURF-R11-002", "ROUND11", "docs/research/trace-v49-exploration-constraint-kernel-round1/08_SYNTHETIC_FIXTURE_REGISTRY.tsv", "tsv_rows", "SYNTHETIC_NEGATIVE_CONTROL", "TRG-007", "Synthetic fixtures test logic only and cannot activate research claims."),
    surface("SURF-R11-003", "ROUND11", "docs/research/trace-v49-exploration-constraint-kernel-round1/15_ADVERSARIAL_TEST_MATRIX.tsv", "tsv_rows", "ADVERSARIAL_CONTROL", "TRG-007;TRG-012", "Test cases expose failure classes rather than supply evidence."),
    surface("SURF-R12-001", "ROUND12", "docs/research/trace-v49-exploration-inquiry-flow-round1/02_RESEARCH_CANDIDATE_FREEZE.json", "json:candidates", "RESEARCH_ONLY_CANDIDATES", "TRG-006;TRG-008", "Inactive inquiry candidates require fresh group review."),
    surface("SURF-R12-002", "ROUND12", "docs/research/trace-v49-exploration-inquiry-flow-round1/05_PAIR_QUESTION_EVIDENCE_COVERAGE.tsv", "tsv_rows", "PAIR_INQUIRY_CONTROL", "TRG-006;TRG-007", "Pair questions cannot prove group coherence."),
    surface("SURF-R12-003", "ROUND12", "docs/research/trace-v49-exploration-inquiry-flow-round1/08_INQUIRY_SEED_REGISTRY.tsv", "tsv_rows", "RESEARCH_ONLY_PRODUCT_SEED", "TRG-004;TRG-006", "A renderable inquiry seed is not an active association."),
    surface("SURF-R12-004", "ROUND12", "docs/research/trace-v49-exploration-inquiry-flow-round1/11_RESEARCH_INSTANCE_REGISTRY.tsv", "tsv_rows", "RESEARCH_ONLY_PRODUCT_INSTANCE", "TRG-004;TRG-006", "Instance structure triggers reconciliation only."),
    surface("SURF-R13-001", "ROUND13", "docs/research/trace-v49-exploration-composition-review-round1/03_COMPOSITION_SCHOLARLY_SOURCE_REGISTRY.tsv", "tsv_rows", "BIBLIOGRAPHIC_IDENTITY", "TRG-002;TRG-003;TRG-010", "Metadata and source-family identity remain discovery only."),
    surface("SURF-R13-002", "ROUND13", "docs/research/trace-v49-exploration-composition-review-round1/04_COMPOSITION_EVIDENCE_REGISTRY.tsv", "tsv_rows", "LOCATOR_BEARING_PAIR_AND_GAP_EVIDENCE", "TRG-002;TRG-003;TRG-006;TRG-011", "Multi-concept loci trigger whole-group review; pair rows remain pair claims."),
    surface("SURF-R13-003", "ROUND13", "docs/research/trace-v49-exploration-composition-review-round1/05_PAIR_DECISION_REGISTRY.tsv", "tsv_rows", "GOVERNED_PAIR_DECISION", "TRG-003;TRG-007", "Pair disposition does not transfer to a group."),
    surface("SURF-R13-004", "ROUND13", "docs/research/trace-v49-exploration-composition-review-round1/07_VOCABULARY_GAP_DECISIONS.tsv", "tsv_rows", "GOVERNED_GAP_DECISION", "TRG-006;TRG-012", "Gap status and sense boundaries must be retained."),
    surface("SURF-R13-005", "ROUND13", "docs/research/trace-v49-exploration-composition-review-round1/14_ACTIVATION_CANDIDATE_PACKAGE.json", "json:file", "INACTIVE_ACTIVATION_PACKAGE", "TRG-006;TRG-008", "Package is explicitly inactive and human-review dependent."),
    surface("SURF-R13-006", "ROUND13", "docs/research/trace-v49-exploration-composition-review-round1/16_EXTERNAL_DOMAIN_REVIEW_REGISTRY.tsv", "tsv_rows", "PENDING_HUMAN_REVIEW", "TRG-006;TRG-012", "NOT_COMPLETED review units cannot authorize active facts."),
    surface("SURF-R14-001", "ROUND14", "scripts/trace-v49-exploration-association-calibration/fixtures/association-assessments-v1.json", "json:assessments", "GOVERNED_PAIR_ASSESSMENTS", "TRG-002;TRG-003;TRG-007;TRG-008", "Pair assessments supply pair evidence and controls, never automatic group support."),
    surface("SURF-R14-002", "ROUND14", "docs/audits/v49-exploration-association-calibration-round1/raw/evidence-provenance.tsv", "tsv_rows", "LOCATOR_BEARING_PAIR_PROVENANCE", "TRG-002;TRG-003;TRG-011", "Concept-only rows are discovery; association-support rows remain bounded to their pair claims."),
    surface("SURF-R14-003", "ROUND14", "scripts/trace-v49-exploration-association-calibration/fixtures/nary-local-coherence-v1.json", "json:fixtures", "SYNTHETIC_PAIR_LOCAL_NARY_CONTROL", "TRG-007", "These are pair-binding fixtures, not higher-order evidence."),
    surface("SURF-R14-004", "ROUND14", "docs/audits/v49-exploration-association-calibration-round1/raw/nary-validation.tsv", "tsv_rows", "SYNTHETIC_PAIR_LOCAL_RESULT", "TRG-007", "Results test local pair coherence only."),
    surface("SURF-R15-001", "ROUND15", "scripts/trace-v49-exploration-composition-engine/fixtures/composition-fixtures-v1.json", "json:fixtures", "RESEARCHER_AUTHORED_COMPOSITION_CONTROL", "TRG-004;TRG-007", "Every three-plus-node fixture requires global-coherence reconciliation."),
    surface("SURF-R15-002", "ROUND15", "docs/audits/v49-exploration-composition-engine-round1/raw/composition-decision-audit.json", "json:images", "PAIR_DERIVED_COMPOSITION_RESULT", "TRG-004;TRG-007", "Admission or renderability is not a group-evidence disposition."),
    surface("SURF-R16-001", "ROUND16", "scripts/trace-v49-exploration-real-database/real-composition-registry-v1.json", "json:compositions", "LEGACY_PRODUCT_COMPOSITION", "TRG-004;TRG-008", "All eleven legacy compositions require explicit global reconciliation."),
    surface("SURF-R16-002", "ROUND16", "scripts/trace-v49-exploration-real-database/scholarly-source-additions-v1.tsv", "tsv_rows", "VOCABULARY_SUPPORT_ONLY", "TRG-002;TRG-005;TRG-006", "The source rows explicitly do not validate associations."),
    surface("SURF-R16A-001", "ROUND16A", "docs/audits/v49-exploration-full-space-closure-round1/raw/vocabulary-census-v2.json", "json:candidates", "GOVERNED_VOCABULARY_BASELINE", "TRG-005;TRG-006;TRG-012", "Retain all active, research-only, rejected, and merged dispositions."),
    surface("SURF-R16A-002", "ROUND16A", "docs/audits/v49-exploration-full-space-closure-round1/raw/association-census-v2.tsv", "tsv_rows", "COMPLETE_PAIR_BASELINE", "TRG-003;TRG-007;TRG-008", "Complete only for the unordered active-vocabulary pair universe."),
    surface("SURF-R16A-003", "ROUND16A", "docs/audits/v49-exploration-full-space-closure-round1/raw/association-evidence-ledger-v2.tsv", "tsv_rows", "PAIR_EVIDENCE_BASELINE", "TRG-002;TRG-003;TRG-007", "Evidence is keyed to pairs and must not be lifted to groups automatically."),
    surface("SURF-R16A-004", "ROUND16A", "docs/audits/v49-exploration-full-space-closure-round1/raw/validated-association-graph-v2.json", "json:edges", "ACTIVE_PAIR_GRAPH_BASELINE", "TRG-003;TRG-005;TRG-008", "Graph connectivity is a candidate trigger, not global validation."),
    surface("SURF-R16A-005", "ROUND16A", "docs/audits/v49-exploration-full-space-closure-round1/raw/exploration-parameter-universe-v2.json", "json:parameters", "PAIR_DERIVED_PARAMETER_BASELINE", "TRG-004;TRG-012", "Existing node and topology bounds require independent justification."),
    surface("SURF-R16A-006", "ROUND16A", "docs/audits/v49-exploration-full-space-closure-round1/raw/canonical-composition-registry-v2.json", "json:topology_compositions", "PAIR_DERIVED_COMPOSITION_BASELINE", "TRG-004;TRG-008", "Every prior three-plus-node composition requires a group-level disposition."),
    surface("SURF-R16A-007", "ROUND16A", "docs/audits/v49-exploration-full-space-closure-round1/raw/composition-rejection-ledger-v2.tsv", "tsv_rows", "PAIR_DERIVED_REJECTION_BASELINE", "TRG-004;TRG-007", "A topology rejection is not a historical group rejection."),
    surface("SURF-R16A-008", "ROUND16A", "docs/audits/v49-exploration-full-space-closure-round1/raw/workflow-census-v2.tsv", "tsv_rows", "PAIR_DERIVED_WORKFLOW_BASELINE", "TRG-004", "Workflow counts are baseline measurements, not association counts."),
    surface("SURF-R16A-009", "ROUND16A", "docs/audits/v49-exploration-full-space-closure-round1/raw/export-census-v2.tsv", "tsv_rows", "PAIR_DERIVED_EXPORT_BASELINE", "TRG-004", "Export counts are baseline measurements, not association counts."),
    surface("SURF-R16A-010", "ROUND16A", "docs/audits/v49-exploration-full-space-closure-round1/raw/association-query-log-v2.jsonl", "jsonl_rows", "METADATA_DISCOVERY_ONLY", "TRG-010;TRG-012", "Crossref metadata produced no accepted locator-bearing evidence."),
    surface("SURF-DB-001", "V49_DATABASE", "data/prefreeze_candidate_v48.sqlite", "file", "ARCHIVE_METADATA_AND_PROVENANCE_DISCOVERY_ONLY", "TRG-009;TRG-012", "Database co-occurrence, categories, and provenance can trigger source review but cannot validate an association."),
]


TRIGGERS = [
    ("TRG-001", "EXPLICIT_NARY_GRAMMAR", "A governed role/grammar record declares 3, 3+, MULTIPARTY, STRUCTURAL, or unresolved 2+ participation.", "Review the locator-bearing source to identify exact governed participant senses; never treat the relation label or role prose as an automatic member list.", "Every qualifying grammar record is accounted for by a candidate, an evidence-insufficient review record, or a structural-not-association exclusion.", "false"),
    ("TRG-002", "SAME_LOCATOR_MULTI_CONCEPT", "One locator-bearing evidence record or bounded locus identifies at least three governed senses in one passage, section, figure, case description, or argument unit.", "Create the exact maximal locus-bound set, then review meaningful nested sets only when the source makes a distinct configuration claim.", "Every multi-sense locus is linked to at least one reviewed candidate or a co-occurrence/concept-only exclusion.", "false"),
    ("TRG-003", "SHARED_CASE_SOURCE_BUNDLE", "Two or more evidence records share an explicitly identified case plus compatible time, geography, institution, actor set, and mechanism.", "Document every synthesis edge and scope equality; publisher, author, keyword, or source family alone is insufficient.", "Every admitted bundle has a case identity, compatibility decision, source list, locators, and synthesis ledger.", "false"),
    ("TRG-004", "PRIOR_PRODUCT_OR_COMPOSITION", "A Round 12–16A inquiry, fixture, legacy composition, subgraph, topology composition, workflow, or export contains at least three concepts.", "Generate one reconciliation candidate per distinct semantic node/association set, retaining all prior identifiers and outcomes.", "Every prior three-plus-node structure receives an explicit retained/corrected/hyperedge/split/merged/inquiry/rejected reconciliation.", "false"),
    ("TRG-005", "ISOLATED_ACTIVE_VOCABULARY", "An active vocabulary concept has no active pair path or no product-visible composition path.", "Search local bounded evidence and legitimate external discovery for exact co-participating senses; otherwise reclassify or record a non-product policy.", "Every isolated active term has an association candidate or an explicit reviewed vocabulary/product disposition.", "false"),
    ("TRG-006", "RESEARCH_ONLY_BOUNDED_SENSE", "A research-only or deferred concept has a bounded sense and a source locus suggesting multi-concept participation.", "Retain inquiry status until group evidence and authority are complete; unresolved umbrella labels do not qualify.", "Every triggered bounded research-only sense is reviewed without silently promoting it to active.", "false"),
    ("TRG-007", "NEGATIVE_OR_NEAR_MISS_CONTROL", "A prior cluster, chain, hard negative, co-occurrence control, split/prune fixture, unsupported bridge, or conflict record bears on group validity.", "Generate the exact control structure with its expected failure or inquiry condition.", "All governed negative-control classes are represented in the candidate and independent-verifier fixtures.", "false"),
    ("TRG-008", "OVERLAP_AND_RECONCILIATION", "Two candidate associations overlap, nest, conflict, or map differently to one or more prior product compositions.", "Review whether they are distinct scopes, duplicates, a required split/merge, or incompatible structures.", "Every overlap has an explicit identity, scope, and reconciliation decision.", "false"),
    ("TRG-009", "DATABASE_PROVENANCE_DISCOVERY", "Archive objects, source documents, TRACE nodes/edges, or provenance records identify a bounded common case or source family involving at least three exact concepts.", "Use database records only to locate reviewable sources; categories, similarity, and co-occurrence never count as association evidence.", "Every database-triggered candidate records the query and remains non-active until locator-bearing scholarly evidence is reviewed.", "false"),
    ("TRG-010", "ADAPTIVE_EXTERNAL_SEARCH", "Local evidence leaves a triggered group unresolved or gap review identifies a plausible omitted historical configuration.", "Search the complete group, meaningful subsets, variants, case, institution, period, geography, actors, mechanisms, citations, and falsification terms; record every query and decision.", "Every external result is linked to a stable reviewable locator or classified metadata-only/access-blocked/rejected.", "true"),
    ("TRG-011", "COUNTEREVIDENCE_AND_FALSIFICATION", "A proposed active or product-visible group has scope, role, topology, case-compatibility, or bounded-sense assumptions that can be challenged.", "Run candidate-specific counterexample and incompatibility searches before final disposition.", "Every active disposition has a completed counterevidence field and no unresolved hard conflict.", "true"),
    ("TRG-012", "RECURSIVE_GAP_DISCOVERY", "A fresh pre-closure audit finds an unrepresented arity, source pattern, structural class, product path, exclusion proof, or verifier assumption.", "Append the gap, expand method/model/artifacts/tests, regenerate affected ledgers, and create a new verified checkpoint.", "Closure requires a final gap audit with zero unresolved closure-blocking gaps and explicit audit coverage.", "true"),
]


DISPOSITIONS = [
    ("DIRECT_HIGHER_ORDER_SUPPORT", "FINAL_SUPPORTING", "Locator-bearing evidence directly treats the exact concept set as one bounded historical configuration.", "true", "Evidence, rights, coherence, review, and product-policy gates must all pass."),
    ("COHERENT_COMPOSITE_SUPPORT", "FINAL_SUPPORTING", "A documented same-case source bundle coherently supports the complete group without unsupported bridges.", "true", "Every synthesis step and scope equality must be explicit; unrelated pair sources are forbidden."),
    ("MIXED_DIRECT_AND_COMPOSITE_SUPPORT", "FINAL_SUPPORTING", "Direct group evidence and compatible composite evidence jointly support the exact bounded configuration.", "true", "Direct and composite claims must be separately traceable and mutually scope-compatible."),
    ("PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE", "FINAL_NON_SUPPORTING", "Some or all pair claims are supported, but the group has not passed independent global-coherence review.", "false", "No group-active or product-active status; pair records remain separately governed."),
    ("INQUIRY_ONLY_OR_UNRESOLVED", "FINAL_NON_SUPPORTING", "The structure has bounded research value but unresolved evidence, authority, sense, rights, or review requirements.", "false", "May be exposed only through an explicitly research-only path."),
    ("INSUFFICIENT_EVIDENCE", "FINAL_NON_SUPPORTING", "Reviewable material does not support the proposed exact group.", "false", "Record searched sources, locators, and rejection reasons."),
    ("COOCCURRENCE_ONLY", "FINAL_NON_SUPPORTING", "Concept labels share metadata, source, category, or passage without one coherent configuration.", "false", "Co-occurrence is never association support."),
    ("BOUNDED_SENSE_OR_SCOPE_CONFLICT", "FINAL_NON_SUPPORTING", "At least one member sense or time/place/institution/actor/case/mechanism scope conflicts with the group.", "false", "Split or reformulate only through a new candidate identity."),
    ("TOPOLOGY_OR_ROLE_CONFLICT", "FINAL_NON_SUPPORTING", "The proposed roles, order, or render topology are unsupported or contradictory.", "false", "A semantic group may survive only with corrected separately governed realization."),
    ("HARD_NEGATIVE", "FINAL_NON_SUPPORTING", "Direct negative evidence defeats the exact proposed group under its bounded scope.", "false", "A negative pair blocks pair projection but does not automatically defeat a separately supported hyperedge."),
    ("PENDING_GOVERNED_REVIEW", "NONFINAL", "The candidate has been generated but one or more mandatory review gates are incomplete.", "false", "Any pending candidate blocks candidate-universe closure."),
    ("DUPLICATE_IDENTITY_MERGED", "FINAL_ADMINISTRATIVE", "The candidate duplicates an exact canonical participant, role/order, scope, and authority identity.", "false", "Point to the surviving candidate; never merge merely overlapping or nested groups."),
]


EXCLUSIONS = [
    ("NO_GOVERNED_TRIGGER", "All mathematical subsets absent from every audited trigger output.", "Recompute all finite trigger outputs and prove the subset key is absent; report the rule-level complement count, not a historical claim.", "A new source pattern or gap finding invalidates this exclusion until regeneration."),
    ("METADATA_DISCOVERY_ONLY", "Search result, title, abstract index, keyword, citation, or database metadata without a reviewable evidence locator.", "Record query/result identity and absence of qualifying locator-bearing review.", "A later reviewed source may generate a new candidate."),
    ("COOCCURRENCE_OR_CONCEPT_ONLY", "Terms are present but do not participate in one bounded configuration.", "Record locus and reviewer reason distinguishing presence from participation.", "Direct group evidence reopens the structure."),
    ("VOCABULARY_SUPPORT_ONLY", "A source supports concept eligibility but explicitly does not support an association.", "Preserve source scope note and forbid association activation.", "Separate association evidence may create a candidate."),
    ("INCOMPATIBLE_CASE_OR_SCOPE", "Evidence crosses incompatible time, place, institution, actor, case, mechanism, or bounded sense.", "Record each conflicting dimension and source locator.", "Only a newly bounded compatible candidate may proceed."),
    ("PAIR_DERIVED_WITHOUT_GROUP_REVIEW", "A connected graph or composition exists only because pair edges compose.", "Link all pair records and the missing global review gate.", "Completed group review replaces this class with a substantive disposition."),
    ("TOPOLOGY_OR_ROLE_CONFLICT", "Proposed order, role, direction, or render topology exceeds the evidence.", "Record supported semantics separately from rejected realization.", "A corrected realization requires a distinct reviewed mapping."),
    ("UNRESOLVED_SENSE", "At least one label lacks a governed bounded sense.", "Link the gap or vocabulary decision.", "A later governed sense decision may trigger review."),
    ("STRUCTURAL_ANNOTATION_NOT_ASSOCIATION", "The item is a context, condition, or analytic annotation rather than a participating association member.", "Link the governing structural decision.", "A different bounded sense requires a new authority decision."),
    ("ALIAS_OR_MERGED_IDENTITY", "A label is an alias or merged vocabulary identity.", "Canonicalize to the governed vocabulary/sense ID and prove no semantic distinction remains.", "A newly governed distinct sense creates a new identity."),
    ("RIGHTS_OR_ACCESS_BLOCKED", "Evidence cannot be lawfully or reliably reviewed at a stable locator.", "Record access condition, attempt, and non-retention decision.", "Legitimate later access may reopen review; never activate while blocked."),
    ("CATEGORY_OR_DATABASE_COINCIDENCE_ONLY", "Shared product category, archive folder, similarity edge, or database join lacks group evidence.", "Record the mechanical discovery path and absence of historical support.", "Reviewable same-case evidence may create a candidate."),
    ("DUPLICATE_CANDIDATE_IDENTITY", "An exact canonical candidate identity already exists.", "Link the surviving ID and canonical identity hash.", "Different role, order, scope, case, or authority prevents this exclusion."),
    ("OUTSIDE_AUTHORIZED_FUNCTION3_SCOPE", "The structure does not concern governed Exploration vocabulary associations or their product realizations.", "State the governing boundary without evaluating the historical claim.", "A changed authority requires a new round or explicit authorization."),
]


GAPS = [
    ("GAP-001", "CHECKPOINT-001", "Round 16A input inventory omitted Round 10 n-ary grammar surfaces and Round 15/legacy multi-node structures.", "CLOSURE_BLOCKING", "RESOLVED_METHOD_SCOPE", "SURF-R10-002;SURF-R10-003;SURF-R10-005;SURF-R10-006;SURF-R15-001;SURF-R15-002;SURF-R16-001", "Generate and review their candidates."),
    ("GAP-002", "CHECKPOINT-001", "Association identity and production contracts are binary-only.", "CLOSURE_BLOCKING", "OPEN", "future model/schema/API checkpoint", "Introduce first-class association membership and separate composition realization."),
    ("GAP-003", "CHECKPOINT-001", "No prior three-plus-node composition has a complete independent historical group-coherence disposition.", "CLOSURE_BLOCKING", "OPEN", "TRG-004", "Reconcile every prior structure without silent loss."),
    ("GAP-004", "CHECKPOINT-001", "Five active vocabulary concepts are isolated in the active pair graph.", "CLOSURE_BLOCKING", "OPEN", "TRG-005", "Find bounded higher-order paths or change vocabulary/product eligibility explicitly."),
    ("GAP-005", "CHECKPOINT-001", "Round 13 external domain review units remain NOT_COMPLETED.", "CLOSURE_BLOCKING", "OPEN", "SURF-R13-006", "Keep affected claims inactive and report external human-review status truthfully."),
    ("GAP-006", "CHECKPOINT-001", "Scholarly registries lack explicit license, access-condition, and redistribution fields.", "CLOSURE_BLOCKING", "METHOD_CONTROL_ADDED_REVIEW_OPEN", "scholarly-source-rights-ledger.tsv", "Populate a source-rights/access ledger before evidence activation."),
    ("GAP-007", "CHECKPOINT-001", "The inherited eight-node and degree-two limits are product/topology settings, not historical association-arity authority.", "CLOSURE_BLOCKING", "OPEN", "TRG-012", "Audit product bounds separately from research identity and preserve out-of-bound research associations."),
    ("GAP-008", "CHECKPOINT-001", "Round 16A independent verification is implementation-independent but shares the pair-graph ontology.", "CLOSURE_BLOCKING", "OPEN", "future independent verifier", "Reconstruct incidence semantics and candidate/exclusion coverage without generator imports."),
    ("GAP-009", "CHECKPOINT-001", "Round 16A external search is pair-only metadata discovery and accepted no locator-bearing evidence.", "CLOSURE_BLOCKING", "OPEN", "TRG-010;TRG-011", "Use adaptive candidate-specific search and preserve results/locators/rejections."),
    ("GAP-010", "CHECKPOINT-001", "Round 16A reports graph edges as associations and can blur association, composition, state, workflow, and export counts.", "CLOSURE_BLOCKING", "OPEN", "baseline-reconciliation-plan.tsv", "Publish separate metric definitions and regenerate all affected counts."),
    ("GAP-011", "CHECKPOINT-001", "The frozen database can expose common provenance but not historical association evidence.", "CONTROL_REQUIRED", "METHOD_CONTROL_ADDED", "TRG-009;CATEGORY_OR_DATABASE_COINCIDENCE_ONLY", "Require locator-bearing scholarly follow-up for every database trigger."),
    ("GAP-012", "CHECKPOINT-001", "No current verifier proves trigger completeness or the rule-level complement of arbitrary subsets.", "CLOSURE_BLOCKING", "OPEN", "future candidate coverage verifier", "Independently regenerate trigger outputs and exclusion complement."),
    ("GAP-013", "CHECKPOINT-001", "Round 9 sense IDs, Round 13 split IDs, Round 14 labels, and Round 16A TRV IDs lack one stable governed concept-sense crosswalk.", "CLOSURE_BLOCKING", "OPEN", "concept-sense-crosswalk.tsv", "Build and independently verify exact cross-round sense mappings before canonical candidate identity is frozen."),
    ("GAP-014", "CHECKPOINT-001", "Method triggers have governed conditions and coverage rules but do not yet have executable occurrence selectors and a complete occurrence ledger.", "CLOSURE_BLOCKING", "OPEN", "candidate-trigger-occurrence-ledger.tsv", "Implement independently testable selectors; map every occurrence to a candidate, control, duplicate, reconciliation obligation, or proved exclusion."),
]


BASELINE = [
    ("VOCABULARY_CANDIDATES", "65", "vocabulary-census-v2.json", "Retain all four Round 16A vocabulary dispositions; do not silently drop candidates."),
    ("ACTIVE_VOCABULARY", "31", "vocabulary-census-v2.json", "Reassess product reachability, including five isolated active concepts."),
    ("UNORDERED_PAIR_UNIVERSE", "465", "association-census-v2.tsv", "Preserve as complete pair-only baseline, not total association universe."),
    ("ACTIVE_PAIR_ASSOCIATIONS", "21", "validated-association-graph-v2.json", "Keep separately counted pair objects; do not infer group edges."),
    ("CANONICAL_PAIR_EDGE_SUBGRAPHS", "58", "canonical-composition-registry-v2.json", "Review every three-plus-node semantic set for global coherence."),
    ("TOPOLOGY_COMPOSITIONS", "81", "canonical-composition-registry-v2.json", "Reconcile topology as render realization, not association identity."),
    ("PRODUCTION_COMPOSITIONS", "228", "space-generation-summary-v2.json", "Trace each product composition to reviewed association objects."),
    ("STATES", "5760", "state-census-v2.tsv", "Regenerate only after v3 visibility/navigation semantics are frozen."),
    ("TRANSITIONS", "749944", "transition-census-v2.tsv", "Regenerate from higher-order-aware legal actions; baseline remains reproducible."),
    ("WORKFLOWS", "5760", "workflow-census-v2.tsv", "Regenerate and replay; never call this an association count."),
    ("EXPORTS", "11520", "export-census-v2.tsv", "Regenerate manifests from governed realizations; never call this an association count."),
    ("LEGACY_COMPOSITIONS", "11", "real-composition-registry-v1.json", "Retain identifiers and issue one explicit new disposition for every record."),
]


RIGHTS_POLICY = {
    "format": "trace-round16b-scholarly-source-rights-policy-v1",
    "source_sha": SOURCE_SHA,
    "status": "ACTIVE_METHOD_CONTROL",
    "permitted_committed_material": [
        "bibliographic_identity",
        "stable_locator",
        "retrieval_timestamp",
        "access_condition",
        "license_or_rights_status",
        "content_hash_when_lawfully_obtained",
        "bounded_research_note",
        "compliant_short_extract",
        "review_and_rejection_decision",
    ],
    "prohibited_without_explicit_redistribution_authority": [
        "copyrighted_full_text",
        "publisher_pdf",
        "ebook_or_chapter_file",
        "bulk_scraped_proprietary_content",
    ],
    "metadata_is_not_evidence": True,
    "public_access_is_not_redistribution_permission": True,
    "archive_object_rights_do_not_govern_scholarly_text_rights": True,
    "activation_gate": "Every supporting evidence record must have a stable evidence locator, completed rights/access review, and lawful retained representation.",
    "required_ledger_fields": [
        "source_id", "bibliographic_identity", "stable_url", "doi_or_identifier",
        "retrieved_at_utc", "access_status", "access_condition", "license_identifier",
        "copyright_or_rights_holder", "redistribution_authorized", "retained_material_type",
        "retained_path_or_locator", "retained_sha256", "extract_word_count",
        "reviewer", "review_status", "notes",
    ],
}


METHOD = {
    "format": METHOD_VERSION,
    "version": 1,
    "source_sha": SOURCE_SHA,
    "source_tree": SOURCE_TREE,
    "frozen_date": "2026-08-28",
    "association_object_boundary": {
        "vocabulary_concept": "A governed bounded concept identity.",
        "pairwise_association": "A two-member evidence-bearing semantic object.",
        "higher_order_association": "A three-or-more-member evidence-bearing semantic object that does not imply its pair projections.",
        "composition": "A governed visual or navigational realization supported by one or more association objects.",
        "interaction_state": "An immutable reachable product state over a composition.",
        "workflow": "A legal action path through interaction states.",
        "export": "A governed representation of one state and realization.",
    },
    "research_arity_policy": {
        "minimum_association_arity": 2,
        "higher_order_minimum_arity": 3,
        "research_schema_maximum_arity": None,
        "product_maximum_arity": "UNRESOLVED_REQUIRES_BOUND_AUDIT",
        "rule": "Discovery is trigger-bounded rather than subset-enumeration-bounded. A source-supported group outside the current product bound remains a research association and cannot be truncated or projected into pairs.",
    },
    "canonical_identity": {
        "candidate_prefix": "R16B-CAND:",
        "association_prefix": "R16B-ASSOC:",
        "hash": "sha256(canonical-json)",
        "unordered_participants": "Sort by vocabulary_id, sense_id, role-or-empty, then participant authority; preserve no incidental source ordering.",
        "ordered_participants": "Preserve governed position and role only when evidence and authority support them.",
        "association_identity_fields": [
            "association class", "participant sense IDs", "order semantics",
            "governed stable role IDs and bindings", "stable time scope IDs",
            "stable geography IDs", "stable institution IDs", "stable actor-set IDs",
            "stable case IDs", "stable mechanism IDs", "stable context IDs",
        ],
        "association_revision_fields": [
            "association_id", "evidence and evidence-bundle hashes", "current disposition",
            "review authority", "review timestamp", "qualifications", "non-claims",
            "uncertainty", "activation status", "product eligibility", "revision version",
        ],
        "non_identity_fields": [
            "labels", "free-text prose", "search rank", "retrieval order", "UI category",
            "render seed", "file order", "evidence status", "authority", "review authority", "version",
        ],
        "revision_rule": "association_id hashes stable semantic identity; association_revision_id hashes the canonical append-only revision content. Evidence, review, authority, timestamp, and version never alter association_id.",
    },
    "lifecycle_states": ["DISCOVERED", "EVIDENCE_REVIEW_IN_PROGRESS", "GOVERNED_REVIEW_COMPLETE", "SUPERSEDED"],
    "activation_invariants": [
        "Declared arity equals participant count; participant sense IDs are unique and resolve through the governed crosswalk.",
        "Order constraints are acyclic and roles use governed role IDs; labels and role prose are display snapshots only.",
        "PENDING_GOVERNED_REVIEW is never active.",
        "Metadata, titles, keywords, categories, and database co-occurrence are never association evidence.",
        "Pair connectivity never creates group support.",
        "Group support never creates internal pair associations.",
        "Every active group passes evidence, rights, bounded-sense, scope, counterevidence, global-coherence, authority, and product-eligibility gates.",
        "No causal, directional, chronological, hierarchical, influence, similarity, or typed claim is inferred without explicit evidence and authority.",
        "Composition identity and association identity remain separate and have separate counts.",
        "Render topology is realization metadata and never participates in historical association identity.",
    ],
    "global_coherence_dimensions": [
        "bounded_senses", "same_case", "time", "geography", "institution", "actors",
        "mechanism", "source_bundle_synthesis", "roles", "order", "topology",
        "decorative_or_incidental_member", "counterevidence", "split_or_merge_need",
    ],
    "candidate_universe_definition": "The exact canonical union of all deterministic trigger outputs. Mathematical subsets outside that union are excluded at rule level as NO_GOVERNED_TRIGGER and are not historical negatives.",
    "closure_gates": [
        "every trigger output has one final disposition",
        "every concrete exclusion has a proof and reopening condition",
        "the rule-level no-trigger complement is independently reconstructed",
        "every prior three-plus-node structure is reconciled",
        "every active association has completed review and product disposition",
        "no active evidence record is metadata-only, access-blocked, or pending human review",
        "all isolated active vocabulary has an explicit resolution",
        "independent incidence-semantic verification passes",
        "clean offline deterministic reproduction passes",
        "a final recursive gap audit has zero unresolved closure-blocking gaps",
    ],
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_records(path: Path, selector: str) -> int:
    if selector == "tsv_rows":
        with path.open(encoding="utf-8", newline="") as handle:
            return sum(1 for _ in csv.DictReader(handle, dialect="excel-tab"))
    if selector == "jsonl_rows":
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    if selector == "file":
        return 1
    if selector.startswith("json:"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        key = selector.split(":", 1)[1]
        if key == "file":
            return 1
        value: Any = payload[key]
        return len(value)
    raise ValueError(f"unknown selector {selector}")


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, dialect="excel-tab", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(buffer.getvalue(), encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    inventory: list[dict[str, Any]] = []
    for item in SURFACES:
        path = REPO / item["path"]
        if not path.is_file():
            raise FileNotFoundError(path)
        inventory.append({
            **item,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "record_count": count_records(path, item["record_selector"]),
        })
    write_tsv(
        RAW / "evidence-surface-inventory.tsv",
        ["surface_id", "round", "path", "record_selector", "record_count", "bytes", "sha256", "evidence_authority", "candidate_trigger_ids", "use_boundary"],
        inventory,
    )
    field_contract_rows: list[dict[str, Any]] = []
    for item in inventory:
        path = REPO / item["path"]
        selector = item["record_selector"]
        top_fields: list[str] = []
        record_fields: list[str] = []
        if selector == "tsv_rows":
            with path.open(encoding="utf-8", newline="") as handle:
                record_fields = next(csv.reader(handle, dialect="excel-tab"))
        elif selector.startswith("json:"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            top_fields = sorted(payload) if isinstance(payload, dict) else []
            key = selector.split(":", 1)[1]
            if key != "file" and isinstance(payload.get(key), list):
                record_fields = sorted({field for row in payload[key] if isinstance(row, dict) for field in row})
        elif selector == "jsonl_rows":
            record_fields = sorted({
                field
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
                for field in json.loads(line)
            })
        contract_payload = {
            "surface_id": item["surface_id"],
            "record_selector": selector,
            "top_level_fields": top_fields,
            "record_fields": record_fields,
        }
        contract_hash = hashlib.sha256(
            json.dumps(contract_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        field_contract_rows.append({
            "surface_id": item["surface_id"],
            "record_selector": selector,
            "top_level_fields_json": json.dumps(top_fields, separators=(",", ":")),
            "record_fields_json": json.dumps(record_fields, separators=(",", ":")),
            "contract_sha256": contract_hash,
        })
    write_tsv(
        RAW / "evidence-surface-field-contract.tsv",
        ["surface_id", "record_selector", "top_level_fields_json", "record_fields_json", "contract_sha256"],
        field_contract_rows,
    )
    trigger_rows = [dict(zip(
        ["trigger_id", "trigger_name", "trigger_condition", "generation_rule", "coverage_proof", "external_search_required"], row
    )) for row in TRIGGERS]
    write_tsv(RAW / "candidate-trigger-registry.tsv", list(trigger_rows[0]), trigger_rows)
    disposition_rows = [dict(zip(
        ["disposition", "status_class", "meaning", "potentially_active", "mandatory_condition"], row
    )) for row in DISPOSITIONS]
    write_tsv(RAW / "association-disposition-taxonomy.tsv", list(disposition_rows[0]), disposition_rows)
    exclusion_rows = [dict(zip(
        ["exclusion_class", "meaning", "proof_required", "reopening_condition"], row
    )) for row in EXCLUSIONS]
    write_tsv(RAW / "exclusion-class-registry.tsv", list(exclusion_rows[0]), exclusion_rows)
    gap_rows = [dict(zip(
        ["gap_id", "discovered_checkpoint", "gap", "severity", "status", "governing_artifact_or_trigger", "required_next_action"], row
    )) for row in GAPS]
    write_tsv(RAW / "recursive-gap-ledger.tsv", list(gap_rows[0]), gap_rows)
    baseline_rows = [dict(zip(
        ["round16a_metric", "baseline_value", "source_artifact", "round16b_reconciliation_requirement"], row
    )) for row in BASELINE]
    write_tsv(RAW / "round16a-baseline-reconciliation-plan.tsv", list(baseline_rows[0]), baseline_rows)
    write_json(RAW / "higher-order-association-method-v1.json", METHOD)
    write_json(RAW / "scholarly-source-rights-policy.json", RIGHTS_POLICY)
    write_tsv(
        RAW / "concept-sense-crosswalk.tsv",
        [
            "participant_sense_id", "vocabulary_id", "canonical_label", "source_system",
            "source_concept_id", "source_sense_id", "bounded_sense", "scope_note",
            "disposition", "authority_path", "authority_record_id", "source_sha",
            "crosswalk_status", "crosswalk_reason",
        ],
        [],
    )
    write_tsv(
        RAW / "scholarly-source-rights-ledger.tsv",
        RIGHTS_POLICY["required_ledger_fields"],
        [],
    )
    write_tsv(
        RAW / "candidate-trigger-occurrence-ledger.tsv",
        [
            "trigger_occurrence_id", "trigger_id", "input_surface_id",
            "input_record_refs_json", "participant_sense_ids_json", "scope_hypothesis_id",
            "emission_kind", "candidate_id", "disposition_or_exclusion_ref",
            "selector_version", "occurrence_sha256",
        ],
        [],
    )
    write_tsv(
        RAW / "association-evidence-ledger.tsv",
        [
            "evidence_id", "candidate_id", "source_id", "source_version_id", "evidence_channel",
            "locator_scheme", "locator_value", "hash_scope", "evidence_sha256", "rights_record_id",
            "participating_sense_ids_json", "incidental_sense_ids_json", "exact_group_supported",
            "support_role", "case_ids_json", "context_ids_json", "temporal_ids_json",
            "geography_ids_json", "institution_ids_json", "actor_ids_json", "mechanism_ids_json",
            "observed_order_semantics", "observed_role_bindings_json", "qualification",
            "explicit_nonclaims_json", "counterevidence_refs_json", "content_review_status",
            "evidence_verified", "semantic_review", "adversarial_review", "reviewer_id", "reviewed_at_utc",
        ],
        [],
    )
    write_tsv(
        RAW / "candidate-exclusion-ledger.tsv",
        [
            "exclusion_id", "subject_kind", "subject_canonical_key", "candidate_id",
            "participant_sense_ids_json", "exclusion_class", "proof_input_refs_json",
            "proof_facts_json", "predicate_version", "machine_result", "reviewer_result",
            "final_status", "successor_candidate_ids_json", "merge_target_id", "checkpoint_id",
            "content_sha256",
        ],
        [],
    )
    governed_outputs = [
        "association-disposition-taxonomy.tsv",
        "association-evidence-ledger.tsv",
        "candidate-trigger-registry.tsv",
        "candidate-trigger-occurrence-ledger.tsv",
        "candidate-exclusion-ledger.tsv",
        "concept-sense-crosswalk.tsv",
        "evidence-surface-field-contract.tsv",
        "evidence-surface-inventory.tsv",
        "exclusion-class-registry.tsv",
        "higher-order-association-method-v1.json",
        "recursive-gap-ledger.tsv",
        "round16a-baseline-reconciliation-plan.tsv",
        "scholarly-source-rights-policy.json",
        "scholarly-source-rights-ledger.tsv",
    ]
    output_hashes = {name: sha256_file(RAW / name) for name in governed_outputs}
    schema_paths = [
        "schemas/trace/exploration/governed-association-v1.schema.json",
        "schemas/trace/exploration/higher-order-association-candidate-v1.schema.json",
        "schemas/trace/exploration/higher-order-association-review-v1.schema.json",
    ]
    receipt = {
        "format": "trace-round16b-method-build-receipt-v1",
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "method_version": METHOD_VERSION,
        "status": "PASS",
        "evidence_surface_count": len(inventory),
        "candidate_trigger_count": len(trigger_rows),
        "disposition_count": len(disposition_rows),
        "exclusion_class_count": len(exclusion_rows),
        "initial_gap_count": len(gap_rows),
        "initial_open_closure_blocking_gap_count": sum(
            row["severity"] == "CLOSURE_BLOCKING" and row["status"] == "OPEN" for row in gap_rows
        ),
        "round16a_baseline_metric_count": len(baseline_rows),
        "concept_sense_crosswalk_record_count": 0,
        "scholarly_source_rights_record_count": 0,
        "trigger_occurrence_record_count": 0,
        "association_evidence_record_count": 0,
        "candidate_exclusion_record_count": 0,
        "output_sha256": output_hashes,
        "schema_sha256": {path: sha256_file(REPO / path) for path in schema_paths},
    }
    write_json(RAW / "method-build-receipt.json", receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
