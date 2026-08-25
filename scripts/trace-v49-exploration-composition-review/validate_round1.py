#!/usr/bin/env python3
"""Exhaustive validation for TRACE v49 Round 13 generated artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
ENGINE = Path(__file__).resolve().parent
REPO = ENGINE.parents[1]
sys.path.insert(0, str(ENGINE))
ROUND12_ENGINE = REPO / "scripts/trace-v49-exploration-inquiry-engine"
sys.path.insert(0, str(ROUND12_ENGINE))

from canonical_v2 import semantic_hash  # noqa: E402
from instance_v2 import compile_instance_v2, detect_contamination, validate_instance_v2  # noqa: E402
from topology import STRATEGIES, assert_no_duplicate_topologies, build_tree, topology_signature, validate_tree  # noqa: E402


SOURCE_SHA = "83f1fba3464f5828fcfd15a1c557035bb1341bf3"
FREEZE_HASH = "b7d42015862e12fd54bc05a9ed0a53223771fc03954c112e72652c0349fb6f90"
RESEARCH = REPO / "docs/research/trace-v49-exploration-composition-review-round1"
AUDIT = REPO / "docs/audits/v49-exploration-composition-review-round1"
V1_DIR = REPO / "docs/research/trace-v49-exploration-inquiry-flow-round1/12_RESEARCH_INSTANCES"
V2_DIR = RESEARCH / "12_RESEARCH_INSTANCES_V2"
FREEZE_PATH = REPO / "docs/research/trace-v49-exploration-inquiry-flow-round1/02_RESEARCH_CANDIDATE_FREEZE.json"


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def validate_input_freeze() -> dict[str, Any]:
    require(git("merge-base", "--is-ancestor", SOURCE_SHA, "HEAD").returncode == 0, "SOURCE_SHA_NOT_ANCESTOR")
    immutable_paths = [
        "docs/research/trace-v49-exploration-inquiry-flow-round1/02_RESEARCH_CANDIDATE_FREEZE.json",
        "docs/research/trace-v49-exploration-inquiry-flow-round1/12_RESEARCH_INSTANCES",
    ]
    require(git("diff", "--quiet", SOURCE_SHA, "--", *immutable_paths).returncode == 0, "ROUND12_FREEZE_OR_V1_MUTATION")
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    require(freeze["packageId"] == "trace-exploration-research-candidates-v1", "FREEZE_PACKAGE_ID")
    require(freeze["canonicalHash"] == FREEZE_HASH, "FREEZE_HASH_FIELD")
    from canonical import semantic_hash as round12_hash  # noqa: PLC0415
    require(round12_hash({key: value for key, value in freeze.items() if key != "canonicalHash"}) == FREEZE_HASH, "FREEZE_CANONICAL_HASH")
    require(len(freeze["candidates"]) == 16, "FREEZE_CANDIDATE_COUNT")
    counts = Counter(item["researchStatus"] for item in freeze["candidates"])
    require(counts == {"BOUNDED_NODE_ROLE_CANDIDATE": 8, "DEFERRED_NODE_ROLE_CANDIDATE": 8}, "FREEZE_STATUS_COUNTS")
    v1_files = sorted(V1_DIR.glob("INQUIRY-INSTANCE-*.json"))
    require(len(v1_files) == 5, "INSTANCE_V1_COUNT")
    return {"freeze": freeze, "v1Files": v1_files, "v1Hashes": [sha256(path) for path in v1_files]}


def validate_sources_and_evidence() -> dict[str, Any]:
    sources = read_tsv(RESEARCH / "03_COMPOSITION_SCHOLARLY_SOURCE_REGISTRY.tsv")
    evidence = read_tsv(RESEARCH / "04_COMPOSITION_EVIDENCE_REGISTRY.tsv")
    require(len(sources) == 30, "SOURCE_COUNT")
    require(len({row["source_id"] for row in sources}) == len(sources), "DUPLICATE_SOURCE_ID")
    require(all(row["source_metadata_verified"] == "true" and row["stable_url"].startswith("https://") for row in sources), "SOURCE_METADATA_VERIFICATION")
    require(all(row["peer_reviewed"] in {"true", "false", "unknown"} and row["design_history_usage"] in {"true", "false"} for row in sources), "SOURCE_REVIEW_ENUM")
    required = {
        "evidence_id", "pair_or_gap_id", "candidate_sense_ids", "source_id", "source_type",
        "peer_reviewed", "design_history_usage", "exact_attested_terms", "bounded_context", "locator",
        "composition_kind", "subject_role", "target_role", "additional_roles", "directionality",
        "qualification", "negation", "contestation", "same_source_cluster", "source_metadata_verified",
        "evidence_verified", "semantic_review", "adversarial_review",
    }
    require(set(evidence[0]) == required, "EVIDENCE_SCHEMA")
    source_ids = {row["source_id"] for row in sources}
    source_by_id = {row["source_id"]: row for row in sources}
    require(len(evidence) == 29 and len({row["evidence_id"] for row in evidence}) == 29, "EVIDENCE_ROW_ID_COUNT")
    require({row["pair_or_gap_id"] for row in evidence} == {"PAIR-A", "PAIR-B", "PAIR-C", "GAP-001", "GAP-002", "GAP-003", "GAP-004", "GAP-005", "GAP-006"}, "EVIDENCE_SCOPE")
    require(all(row["source_id"] in source_ids for row in evidence), "DANGLING_SOURCE_REFERENCE")
    for row in evidence:
        source = source_by_id[row["source_id"]]
        require(row["source_type"] == source["source_type"], f"EVIDENCE_SOURCE_TYPE_MISMATCH:{row['evidence_id']}")
        require(row["peer_reviewed"] == source["peer_reviewed"], f"EVIDENCE_PEER_REVIEW_MISMATCH:{row['evidence_id']}")
        require(row["design_history_usage"] == source["design_history_usage"], f"EVIDENCE_DESIGN_HISTORY_MISMATCH:{row['evidence_id']}")
        require(row["source_metadata_verified"] == source["source_metadata_verified"], f"EVIDENCE_SOURCE_VERIFICATION_MISMATCH:{row['evidence_id']}")
    pair_senses = {
        "PAIR-A": {"REL-CAND-0005#SENSE-A", "REL-CAND-0006#SENSE-A"},
        "PAIR-B": {"REL-CAND-0011#SENSE-A", "REL-CAND-0010#SENSE-A"},
        "PAIR-C": {"REL-CAND-0032#SENSE-A", "REL-CAND-0033#SENSE-A"},
    }
    for row in evidence:
        if row["pair_or_gap_id"] in pair_senses:
            require(set(row["candidate_sense_ids"].split(";")) == pair_senses[row["pair_or_gap_id"]], f"PAIR_SENSE_BINDING:{row['evidence_id']}")
    require(all(row["source_metadata_verified"] == "true" and row["evidence_verified"] == "true" for row in evidence), "UNVERIFIED_EVIDENCE")
    require(all(row["exact_attested_terms"] and row["locator"] and row["bounded_context"] and row["qualification"] and row["contestation"] for row in evidence), "INCOMPLETE_EVIDENCE")
    require(all(row["semantic_review"].startswith("PASS") and row["adversarial_review"].startswith("PASS") for row in evidence), "EVIDENCE_REVIEW")
    return {"sources": sources, "evidence": evidence}


def validate_decisions(evidence: list[dict[str, str]], sources: list[dict[str, str]]) -> dict[str, Any]:
    pairs = read_tsv(RESEARCH / "05_PAIR_DECISION_REGISTRY.tsv")
    require(len(pairs) == 3 and {row["pair_id"] for row in pairs} == {"PAIR-A", "PAIR-B", "PAIR-C"}, "PAIR_DECISION_SCOPE")
    allowed = {"PAIR_ACTIVATION_CANDIDATE", "INQUIRY_ONLY_SUPPORTED", "DEFER_MORE_EVIDENCE", "REJECT_COMPOSITION", "REJECT_FLATTENING_RISK", "REJECT_DIRECTIONALITY_RISK"}
    require(all(row["final_status"] in allowed for row in pairs), "PAIR_DECISION_ENUM")
    require(Counter(row["final_status"] for row in pairs) == {"INQUIRY_ONLY_SUPPORTED": 1, "DEFER_MORE_EVIDENCE": 2}, "PAIR_DECISION_COUNTS")
    require(all(row["activation_candidate"] == "false" and row["semantic_review"].startswith("PASS") and row["adversarial_review"] == "PASS" for row in pairs), "PAIR_FULL_VERIFICATION")
    evidence_by_id = {row["evidence_id"]: row for row in evidence}
    source_by_id = {row["source_id"]: row for row in sources}
    for pair in pairs:
        bound_ids = pair["evidence_ids"].split(";")
        require(len(bound_ids) == len(set(bound_ids)) and all(evidence_id in evidence_by_id for evidence_id in bound_ids), f"PAIR_EVIDENCE_BINDING:{pair['pair_id']}")
        bound = [evidence_by_id[evidence_id] for evidence_id in bound_ids]
        require(all(row["pair_or_gap_id"] == pair["pair_id"] for row in bound), f"PAIR_CROSS_SCOPE_EVIDENCE:{pair['pair_id']}")
        composition = [row for row in bound if row["composition_kind"] != "SUPPORTING_ENVIRONMENT"]
        require(int(pair["independent_composition_attestation_count"]) == len(composition), f"PAIR_ATTESTATION_COUNT:{pair['pair_id']}")
        clusters = {source_by_id[row["source_id"]]["source_cluster"] for row in composition}
        require(pair["outside_source_cluster_present"] == str(len(clusters) >= 2).lower(), f"PAIR_CLUSTER_GATE:{pair['pair_id']}")
        design_article = any(row["peer_reviewed"] == "true" and row["design_history_usage"] == "true" and row["source_type"] == "ARTICLE" for row in composition)
        require(pair["peer_reviewed_design_history_article_present"] == str(design_article).lower(), f"PAIR_DESIGN_HISTORY_GATE:{pair['pair_id']}")
        require(all(row["subject_role"] and row["target_role"] and row["directionality"] for row in bound), f"PAIR_ROLE_DATA:{pair['pair_id']}")
        if pair["final_status"] == "PAIR_ACTIVATION_CANDIDATE":
            require(len(composition) >= 2 and design_article and len(clusters) >= 2 and pair["explicit_role_mapping"] == "true", f"PAIR_ACTIVATION_GATE:{pair['pair_id']}")
        if pair["pair_id"] == "PAIR-C":
            require(pair["final_status"] == "DEFER_MORE_EVIDENCE" and not design_article, "PAIR_C_DESIGN_HISTORY_DEFERRAL")
    require(all("co-occurrence" not in row["natural_language_explanation"].lower() or row["final_status"] != "PAIR_ACTIVATION_CANDIDATE" for row in pairs), "CO_OCCURRENCE_ONLY_PASS")
    gaps = read_tsv(RESEARCH / "07_VOCABULARY_GAP_DECISIONS.tsv")
    require(len(gaps) == 6 and {row["gap_id"] for row in gaps} == {f"GAP-{index:03d}" for index in range(1, 7)}, "GAP_DECISION_SCOPE")
    require(Counter(row["final_decision"] for row in gaps) == {"SOURCE_ATTESTED_SPLIT_CANDIDATE": 4, "STRUCTURAL_ANNOTATION_CANDIDATE": 1, "NEEDS_ADDITIONAL_EVIDENCE": 1}, "GAP_DECISION_COUNTS")
    require(all(row["verified"] == "true" and row["reason"] and row["scope_out"] for row in gaps), "GAP_FULL_VERIFICATION")
    gap_by_id = {row["gap_id"]: row for row in gaps}
    for gap in gaps:
        gap_evidence = [row for row in evidence if row["pair_or_gap_id"] == gap["gap_id"]]
        declared_candidates = set(gap["candidate_ids"].split(";"))
        observed_candidates = {candidate for row in gap_evidence for candidate in row["candidate_sense_ids"].split(";")}
        observed_terms = {term.strip().casefold() for row in gap_evidence for term in row["exact_attested_terms"].split(";")}
        declared_terms = {term.strip().casefold() for term in gap["attested_terms"].split(";")}
        require(observed_candidates == declared_candidates, f"GAP_CANDIDATE_BINDING:{gap['gap_id']}")
        require(declared_terms <= observed_terms, f"GAP_ATTESTED_TERM_BINDING:{gap['gap_id']}")
    package = json.loads((RESEARCH / "14_ACTIVATION_CANDIDATE_PACKAGE.json").read_text(encoding="utf-8"))
    node_candidates = {row["candidateId"]: row for row in package["nodeActivationCandidates"]}
    annotation_candidates = {row["candidateId"]: row for row in package["structuralAnnotationCandidates"]}
    candidate_contracts = {
        "R13-SPLIT-001": {"label": "cultural transfer", "gapId": "GAP-002", "argumentRoles": "source;transferred content;carrier or institution;receiving actors and agency;receiving context;contested reception", "directionality": "SOURCE_BOUNDED_CONTESTED_TRANSFER_WITH_RECEIVING_AGENCY"},
        "R13-SPLIT-002": {"label": "cultural negotiation", "gapId": "GAP-002", "argumentRoles": "participants;contact zone;shared issue;power regime;acts of borrowing, adaptation, or rejection", "directionality": "MULTIDIRECTIONAL"},
        "R13-SPLIT-003": {"label": "cultural adaptation", "gapId": "GAP-002", "argumentRoles": "source work;adapter;target context;retained and modified features;adapted artifact", "directionality": "SOURCE_TO_ADAPTED_VERSION"},
        "R13-SPLIT-004": {"label": "cultural transformation", "gapId": "GAP-002", "argumentRoles": "historical state C0;actors and forces;material evidence;time;historical state C1", "directionality": "STATE_T0_TO_STATE_T1"},
        "R13-SPLIT-005": {"label": "material displacement", "gapId": "GAP-003", "argumentRoles": "moved material;production site;designed destination;supply chain;labor and ecological effects", "directionality": "ORIGIN_TO_RECEIVING_CONTEXT"},
        "R13-SPLIT-006": {"label": "mobile object", "gapId": "GAP-004", "argumentRoles": "moved entity;origin;carrier;route;receiving context;reception change", "directionality": "ITINERARY_WITHOUT_TRANSITIVITY"},
        "R13-SPLIT-007": {"label": "design diplomacy", "gapId": "GAP-005", "argumentRoles": "state or institution;designers and curators;designed media or exposition;negotiating counterpart;foreign public;contingent reception", "directionality": "INTENTIONAL_OUTWARD_WITH_NEGOTIATION_AND_CONTEXTUAL_RECEPTION"},
    }
    require(set(node_candidates) == set(candidate_contracts), "NODE_CANDIDATE_CONTRACT_SCOPE")
    for candidate_id, contract in candidate_contracts.items():
        candidate = node_candidates[candidate_id]
        require(all(candidate[key] == expected for key, expected in contract.items()) and candidate["active"] is False, f"NODE_CANDIDATE_CONTRACT:{candidate_id}")
    annotation_contract = annotation_candidates.get("R13-ANNOT-001", {})
    require(
        annotation_contract.get("label") == "coloniality"
        and annotation_contract.get("representation") == "SOURCE_BOUNDED_STRUCTURAL_ANNOTATION"
        and annotation_contract.get("universalNode") is False
        and annotation_contract.get("edge") is False
        and annotation_contract.get("active") is False,
        "STRUCTURAL_ANNOTATION_CONTRACT",
    )
    expected_nodes = {candidate for gap in gaps if gap["final_decision"] == "SOURCE_ATTESTED_SPLIT_CANDIDATE" for candidate in gap["candidate_ids"].split(";")}
    expected_annotations = {candidate for gap in gaps if gap["final_decision"] == "STRUCTURAL_ANNOTATION_CANDIDATE" for candidate in gap["candidate_ids"].split(";")}
    require(set(node_candidates) == expected_nodes and set(annotation_candidates) == expected_annotations, "GAP_ACTIVATION_CANDIDATE_BINDING")
    for gap in gaps:
        declared = set(gap["candidate_ids"].split(";"))
        if gap["final_decision"] == "SOURCE_ATTESTED_SPLIT_CANDIDATE":
            require(all(node_candidates[candidate]["gapId"] == gap["gap_id"] for candidate in declared), f"NODE_CANDIDATE_GAP_OWNERSHIP:{gap['gap_id']}")
        elif gap["final_decision"] == "STRUCTURAL_ANNOTATION_CANDIDATE":
            require(declared <= set(annotation_candidates), f"ANNOTATION_CANDIDATE_GAP_OWNERSHIP:{gap['gap_id']}")
        else:
            require(not declared & (set(node_candidates) | set(annotation_candidates)), f"DEFERRED_GAP_ACTIVATION_LEAK:{gap['gap_id']}")
    for candidate_id, candidate in node_candidates.items():
        rows = [row for row in evidence if candidate_id in row["candidate_sense_ids"].split(";")]
        exact_terms = {term.strip().casefold() for row in rows for term in row["exact_attested_terms"].split(";")}
        clusters = {source_by_id[row["source_id"]]["source_cluster"] for row in rows}
        require(candidate["label"].casefold() in exact_terms, f"UNATTESTED_CANDIDATE_LABEL:{candidate_id}")
        require(len({row["source_id"] for row in rows}) >= 2 and len(clusters) >= 2, f"CANDIDATE_SOURCE_INDEPENDENCE:{candidate_id}")
        require(any(row["peer_reviewed"] == "true" and row["design_history_usage"] == "true" for row in rows), f"CANDIDATE_DESIGN_HISTORY_GATE:{candidate_id}")
    for candidate_id in annotation_candidates:
        rows = [row for row in evidence if candidate_id in row["candidate_sense_ids"].split(";")]
        require(len({row["source_id"] for row in rows}) >= 2 and any(row["design_history_usage"] == "true" for row in rows), f"ANNOTATION_EVIDENCE_GATE:{candidate_id}")
    require("R13-SPLIT-" not in FREEZE_PATH.read_text(encoding="utf-8") and "R13-ANNOT-" not in FREEZE_PATH.read_text(encoding="utf-8"), "ROUND12_FREEZE_APPEND")
    return {"pairs": pairs, "gaps": gaps}


def validate_topologies() -> dict[str, Any]:
    fixture_package = json.loads((ENGINE / "fixtures/tree-strategy-conformance-v2.json").read_text(encoding="utf-8"))
    require(fixture_package["syntheticOnly"] is True and fixture_package["historicalClaim"] is False, "SYNTHETIC_FIXTURE_BOUNDARY")
    require(len(fixture_package["fixtures"]) == 6, "TREE_FIXTURE_COUNT")
    fixtures: dict[str, list[dict[str, Any]]] = {}
    for fixture in fixture_package["fixtures"]:
        require(fixture["strategy"] in STRATEGIES and fixture["productionEligible"] is False, "TREE_FIXTURE_STATUS")
        require(topology_signature(fixture["treeItems"]) == fixture["topologySignature"], "TREE_FIXTURE_SIGNATURE")
        fixtures[fixture["strategy"]] = fixture["treeItems"]
    require(set(fixtures) == set(STRATEGIES), "TREE_STRATEGY_COVERAGE")
    assert_no_duplicate_topologies(fixtures)
    require(len({topology_signature(items) for items in fixtures.values()}) == 6, "TREE_TOPOLOGY_DUPLICATE")
    rows = read_tsv(RESEARCH / "10_TREE_STRATEGY_CONFORMANCE.tsv")
    require(len(rows) == 6 and all(row["topology_unique"] == "true" and row["validation_status"] == "PASS" and row["production_eligible"] == "false" for row in rows), "TREE_CONFORMANCE_ROWS")
    negative = json.loads((ENGINE / "fixtures/tree-strategy-negative-v2.json").read_text(encoding="utf-8"))
    require(negative["syntheticOnly"] is True and len(negative["cases"]) == 12, "NEGATIVE_FIXTURE_COUNT")
    for case in negative["cases"]:
        try:
            validate_tree(case["strategy"], case["treeItems"])
        except ValueError as error:
            require(str(error) == case["expectedError"], f"NEGATIVE_FIXTURE_ERROR:{case['caseId']}")
        else:
            raise ValueError(f"NEGATIVE_FIXTURE_ACCEPTED:{case['caseId']}")
    return {"fixtures": fixtures}


def validate_instances(v1_files: list[Path]) -> dict[str, Any]:
    v1 = [json.loads(path.read_text(encoding="utf-8")) for path in v1_files]
    v2_files = sorted(V2_DIR.glob("INQUIRY-INSTANCE-*.v2.json"))
    require(len(v2_files) == 5, "INSTANCE_V2_COUNT")
    v2 = [json.loads(path.read_text(encoding="utf-8")) for path in v2_files]
    for parent, child in zip(v1, v2, strict=True):
        validate_instance_v2(child, parent)
        require(compile_instance_v2(parent) == child, "INSTANCE_V2_NONDETERMINISM")
        require(not detect_contamination(child), "INSTANCE_V2_CONTAMINATION")
    sense_ids = {node["senseId"] for instance in v2 for node in instance["semanticNodeRefs"]}
    require(len(sense_ids) == 8, "INSTANCE_V2_BOUNDED_NODE_COVERAGE")
    diffs = read_tsv(RESEARCH / "13_INSTANCE_V1_V2_DIFF.tsv")
    require(len(diffs) == 5 and all(row["semantic_node_change_count"] == "0" and row["research_question_change_count"] == "0" and row["historical_claim_change_count"] == "0" and row["v1_mutated"] == "false" for row in diffs), "INSTANCE_V1_V2_DIFF")
    require(all(instance["historicalClaim"] is False and instance["semanticRelation"] is False and instance["publicExportable"] is False for instance in v2), "HISTORICAL_CLAIM_EMISSION")
    return {"v2": v2, "senseIds": sorted(sense_ids)}


def validate_activation_and_review(
    sources: list[dict[str, str]],
    evidence: list[dict[str, str]],
    pairs: list[dict[str, str]],
    gaps: list[dict[str, str]],
    instances: list[dict[str, Any]],
) -> dict[str, Any]:
    package = json.loads((RESEARCH / "14_ACTIVATION_CANDIDATE_PACKAGE.json").read_text(encoding="utf-8"))
    require(package["packageId"] == "trace-exploration-inquiry-grammar-activation-candidates-v1", "ACTIVATION_PACKAGE_ID")
    require(package["active"] is False and package["requiresExternalHumanReview"] is True and package["requiresSeparateActivationDecision"] is True and package["feedsRealImageCompiler"] is False, "ACTIVATION_PACKAGE_BOUNDARY")
    require(len(package["nodeActivationCandidates"]) == 7 and len(package["pairCompositionCandidates"]) == 0 and len(package["inquiryGrammarCandidates"]) == 6 and len(package["structuralAnnotationCandidates"]) == 1, "ACTIVATION_CANDIDATE_COUNTS")
    unsigned = {key: value for key, value in package.items() if key != "canonicalHash"}
    require(semantic_hash(unsigned) == package["canonicalHash"], "ACTIVATION_PACKAGE_HASH")
    require(all(item["active"] is False for key in ("nodeActivationCandidates", "inquiryGrammarCandidates", "structuralAnnotationCandidates") for item in package[key]), "ACTIVE_CANDIDATE")
    reviews = read_tsv(RESEARCH / "16_EXTERNAL_DOMAIN_REVIEW_REGISTRY.tsv")
    require(len(reviews) == 36 and len({row["review_unit_id"] for row in reviews}) == 36, "EXTERNAL_REVIEW_UNIT_COUNT")
    review_fields = {
        "review_unit_id", "review_unit_type", "subject_id", "plain_language_definition", "source_ids",
        "evidence_ids", "bounded_context", "role_structure", "directionality", "qualification",
        "contestation", "current_system_decision", "alternative_decisions", "reviewer_questions",
        "reviewer_answer_status",
    }
    require(set(reviews[0]) == review_fields, "EXTERNAL_REVIEW_SCHEMA")
    require(all(row["reviewer_answer_status"] == "NOT_COMPLETED" and row["reviewer_questions"] for row in reviews), "FABRICATED_EXTERNAL_REVIEW")
    require(all(row["plain_language_definition"] and row["source_ids"] and row["evidence_ids"] and row["bounded_context"] and row["role_structure"] and row["directionality"] and row["qualification"] and row["contestation"] for row in reviews), "INCOMPLETE_EXTERNAL_REVIEW_UNIT")
    review_type_counts = Counter(row["review_unit_type"] for row in reviews)
    require(review_type_counts == {"BOUNDED_NODE_ROLE": 8, "PAIR_RESEARCH_QUESTION": 3, "RESEARCH_INQUIRY_INSTANCE_V2": 5, "VOCABULARY_GAP": 6, "NODE_ACTIVATION_CANDIDATE": 7, "INQUIRY_GRAMMAR_ACTIVATION_CANDIDATE": 6, "STRUCTURAL_ANNOTATION_CANDIDATE": 1}, "EXTERNAL_REVIEW_TYPE_COUNTS")
    reviews_by_subject = {row["subject_id"]: row for row in reviews}
    require(len(reviews_by_subject) == 36, "EXTERNAL_REVIEW_SUBJECT_UNIQUENESS")
    evidence_by_id = {row["evidence_id"]: row for row in evidence}

    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    bounded = [item for item in freeze["candidates"] if item["researchStatus"] == "BOUNDED_NODE_ROLE_CANDIDATE"]
    glosses = {row["sense_id"]: row for row in read_tsv(REPO / "docs/research/trace-v49-design-history-relation-vocabulary-round1/07_SEMANTIC_GLOSS_REGISTRY.tsv")}
    role_rows = {row["candidate_id"]: row for row in read_tsv(REPO / "docs/research/trace-v49-design-history-relation-grammar-round1/06_ARGUMENT_ROLE_REGISTRY.tsv")}
    for item in bounded:
        review = reviews_by_subject[item["senseId"]]
        role = role_rows[item["candidateId"]]
        require(review["review_unit_type"] == "BOUNDED_NODE_ROLE", f"NODE_REVIEW_TYPE:{item['senseId']}")
        require(set(review["source_ids"].split(";")) == set(item["sourceIds"]), f"NODE_REVIEW_SOURCES:{item['senseId']}")
        require(set(review["evidence_ids"].split(";")) == set(item["lexicalAttestationIds"] + item["grammarAttestationIds"]), f"NODE_REVIEW_EVIDENCE:{item['senseId']}")
        require(review["plain_language_definition"] == glosses[item["senseId"]]["plain_language_gloss"], f"NODE_REVIEW_DEFINITION:{item['senseId']}")
        require(review["role_structure"] == f"subject={role['subject_role']}; target={role['target_role']}; additional={role['additional_party_roles']}", f"NODE_REVIEW_ROLES:{item['senseId']}")
        require(review["directionality"] == item["directionalityStatus"] and review["current_system_decision"] == "BOUNDED_NODE_ROLE_CANDIDATE_NOT_ACTIVE", f"NODE_REVIEW_DECISION:{item['senseId']}")

    for pair in pairs:
        review = reviews_by_subject[pair["pair_id"]]
        rows = [evidence_by_id[evidence_id] for evidence_id in pair["evidence_ids"].split(";")]
        expected_sources = list(dict.fromkeys(row["source_id"] for row in rows))
        expected_roles = " | ".join(f"{row['evidence_id']}: subject={row['subject_role']}; target={row['target_role']}; additional={row['additional_roles']}" for row in rows)
        require(review["review_unit_type"] == "PAIR_RESEARCH_QUESTION", f"PAIR_REVIEW_TYPE:{pair['pair_id']}")
        require(set(review["evidence_ids"].split(";")) == set(pair["evidence_ids"].split(";")), f"PAIR_REVIEW_EVIDENCE:{pair['pair_id']}")
        require(set(review["source_ids"].split(";")) == set(expected_sources), f"PAIR_REVIEW_SOURCES:{pair['pair_id']}")
        require(review["role_structure"] == expected_roles and review["directionality"] == pair["directionality"], f"PAIR_REVIEW_SEMANTICS:{pair['pair_id']}")
        require(review["plain_language_definition"] == pair["natural_language_explanation"] and review["current_system_decision"] == pair["final_status"], f"PAIR_REVIEW_DECISION:{pair['pair_id']}")

    for instance in instances:
        review = reviews_by_subject[instance["instanceId"]]
        expected_evidence = {reference for item in instance["treeItems"] for reference in item["evidenceRefs"]}
        expected_roles = " | ".join(f"{item['inquiryRole']}:{item['itemKind']}" for item in instance["treeItems"])
        require(review["review_unit_type"] == "RESEARCH_INQUIRY_INSTANCE_V2", f"INSTANCE_REVIEW_TYPE:{instance['instanceId']}")
        require(set(review["source_ids"].split(";")) == set(instance["sourceCoverage"]["sourceIds"]), f"INSTANCE_REVIEW_SOURCES:{instance['instanceId']}")
        require(set(review["evidence_ids"].split(";")) == expected_evidence, f"INSTANCE_REVIEW_EVIDENCE:{instance['instanceId']}")
        require(review["role_structure"] == expected_roles and review["directionality"] == "INQUIRY_NAVIGATION_ONLY_NO_HISTORICAL_DIRECTION", f"INSTANCE_REVIEW_SEMANTICS:{instance['instanceId']}")
        require(review["current_system_decision"] == "RESEARCH_CANDIDATE_ONLY", f"INSTANCE_REVIEW_DECISION:{instance['instanceId']}")

    for gap in gaps:
        review = reviews_by_subject[gap["gap_id"]]
        rows = [row for row in evidence if row["pair_or_gap_id"] == gap["gap_id"]]
        expected_sources = list(dict.fromkeys(row["source_id"] for row in rows))
        expected_roles = " | ".join(f"{row['evidence_id']}: subject={row['subject_role']}; target={row['target_role']}; additional={row['additional_roles']}" for row in rows)
        expected_direction = ";".join(dict.fromkeys(row["directionality"] for row in rows))
        require(review["review_unit_type"] == "VOCABULARY_GAP", f"GAP_REVIEW_TYPE:{gap['gap_id']}")
        require(set(review["source_ids"].split(";")) == set(expected_sources) and set(review["evidence_ids"].split(";")) == {row["evidence_id"] for row in rows}, f"GAP_REVIEW_BINDING:{gap['gap_id']}")
        require(review["role_structure"] == expected_roles and review["directionality"] == expected_direction, f"GAP_REVIEW_SEMANTICS:{gap['gap_id']}")
        require(review["plain_language_definition"] == gap["gap_name"] and review["current_system_decision"] == gap["final_decision"], f"GAP_REVIEW_DECISION:{gap['gap_id']}")

    for candidate in package["nodeActivationCandidates"]:
        review = reviews_by_subject[candidate["candidateId"]]
        rows = [row for row in evidence if candidate["candidateId"] in row["candidate_sense_ids"].split(";")]
        require(review["review_unit_type"] == "NODE_ACTIVATION_CANDIDATE", f"ACTIVATION_REVIEW_TYPE:{candidate['candidateId']}")
        require(set(review["source_ids"].split(";")) == {row["source_id"] for row in rows} and set(review["evidence_ids"].split(";")) == {row["evidence_id"] for row in rows}, f"ACTIVATION_REVIEW_BINDING:{candidate['candidateId']}")
        require(review["role_structure"] == candidate["argumentRoles"] and review["directionality"] == candidate["directionality"] and review["plain_language_definition"] == candidate["label"], f"ACTIVATION_REVIEW_SEMANTICS:{candidate['candidateId']}")
        require(review["current_system_decision"] == "ACTIVE_FALSE", f"ACTIVATION_REVIEW_DECISION:{candidate['candidateId']}")

    for candidate in package["inquiryGrammarCandidates"]:
        review = reviews_by_subject[candidate["candidateId"]]
        require(review["review_unit_type"] == "INQUIRY_GRAMMAR_ACTIVATION_CANDIDATE", f"INQUIRY_REVIEW_TYPE:{candidate['candidateId']}")
        require(review["source_ids"] == "NOT_APPLICABLE_SYNTHETIC_TOPOLOGY" and review["evidence_ids"] == f"TREE-CONF-{candidate['candidateId'][-3:]}", f"INQUIRY_REVIEW_BINDING:{candidate['candidateId']}")
        require(review["role_structure"] == "strategy-specific inquiry operations and bounded navigation; no semantic edge roles" and review["directionality"] == "INQUIRY_NAVIGATION_ONLY_NO_HISTORICAL_DIRECTION", f"INQUIRY_REVIEW_SEMANTICS:{candidate['candidateId']}")

    annotation = package["structuralAnnotationCandidates"][0]
    annotation_review = reviews_by_subject[annotation["candidateId"]]
    annotation_rows = [row for row in evidence if annotation["candidateId"] in row["candidate_sense_ids"].split(";")]
    require(annotation_review["review_unit_type"] == "STRUCTURAL_ANNOTATION_CANDIDATE", "ANNOTATION_REVIEW_TYPE")
    require(set(annotation_review["source_ids"].split(";")) == {row["source_id"] for row in annotation_rows} and set(annotation_review["evidence_ids"].split(";")) == {row["evidence_id"] for row in annotation_rows}, "ANNOTATION_REVIEW_BINDING")
    require(annotation_review["role_structure"] == "source;geography;period;mechanism;affected actors or objects;beneficiary or control structure;continuity claim" and annotation_review["directionality"] == "STRUCTURAL_NON_EDGE", "ANNOTATION_REVIEW_SEMANTICS")

    packet = (RESEARCH / "15_EXTERNAL_DOMAIN_REVIEW_PACKET.md").read_text(encoding="utf-8")
    for row in reviews:
        heading = f"## {row['review_unit_id']} — {row['subject_id']}"
        require(heading in packet, f"MARKDOWN_REVIEW_UNIT:{row['review_unit_id']}")
        section = packet.split(heading, 1)[1].split("\n## ", 1)[0]
        for field in ("plain_language_definition", "source_ids", "evidence_ids", "bounded_context", "role_structure", "directionality", "qualification", "contestation", "current_system_decision", "alternative_decisions"):
            require(row[field] in section, f"MARKDOWN_REVIEW_FIELD:{row['review_unit_id']}:{field}")
        require(all(question in section for question in row["reviewer_questions"].split(";")), f"MARKDOWN_REVIEW_QUESTIONS:{row['review_unit_id']}")
    boundary = json.loads((AUDIT / "raw/activation-boundary.json").read_text(encoding="utf-8"))
    require(boundary == {"status": "PASS", "activeVocabularyState": "UNRESOLVED", "activeGrammarState": "UNRESOLVED", "activeRelationTypeCount": 0, "activePairRuleCount": 0, "activeClusterRuleCount": 0, "activeChainRuleCount": 0, "realSemanticImageCount": 0, "externalReviewCompleted": False}, "ACTIVE_BOUNDARY_RECEIPT")
    return {"package": package, "reviews": reviews}


def validate_product_boundary() -> None:
    round13_paths = [path for root in (RESEARCH, AUDIT) for path in root.rglob("*") if path.is_file()]
    prohibited_keys = ["archiveObjectId", "contextDTO", "contextPayload", "spacetimeDTO", "spacetimePayload", "embeddingModel", "vectorReference"]
    for path in round13_paths:
        if path.suffix not in {".json", ".tsv", ".md"}:
            continue
        text = path.read_text(encoding="utf-8")
        require(not any(key in text for key in prohibited_keys), f"PRODUCT_BOUNDARY:{path.name}")
    changed = git("status", "--short").stdout
    require("frontend/src/app" not in changed and "frontend/src/pages" not in changed, "PUBLIC_ROUTE_ADDED")
    require("renderer" not in changed.lower() and "png" not in changed.lower(), "RENDERER_OR_PNG_ADDED")


def validate_audit_seal() -> dict[str, Any]:
    manifest = read_tsv(AUDIT / "MANIFEST.tsv")
    require(manifest and len({row["path"] for row in manifest}) == len(manifest), "MANIFEST_DUPLICATE")
    for row in manifest:
        path = REPO / row["path"]
        require(path.is_file(), "MANIFEST_MISSING_FILE")
        require(int(row["byte_size"]) == path.stat().st_size and row["sha256"] == sha256(path), "MANIFEST_HASH_MISMATCH")
    checksum_rows = [line.split("  ", 1) for line in (AUDIT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines() if line]
    require(len(checksum_rows) == len(manifest), "CHECKSUM_ROW_COUNT")
    require({path: digest for digest, path in checksum_rows} == {row["path"]: row["sha256"] for row in manifest}, "CHECKSUM_MANIFEST_MISMATCH")
    return {"manifestRowCount": len(manifest)}


def main() -> int:
    freeze = validate_input_freeze()
    evidence = validate_sources_and_evidence()
    decisions = validate_decisions(evidence["evidence"], evidence["sources"])
    topologies = validate_topologies()
    instances = validate_instances(freeze["v1Files"])
    activation = validate_activation_and_review(evidence["sources"], evidence["evidence"], decisions["pairs"], decisions["gaps"], instances["v2"])
    validate_product_boundary()
    seal = validate_audit_seal()
    result = {
        "status": "PASS", "sourceSha": SOURCE_SHA, "freezeCanonicalHash": FREEZE_HASH,
        "round12InstanceV1Count": len(freeze["v1Files"]), "round12InstanceV1MutationCount": 0,
        "sourceCount": len(evidence["sources"]), "compositionEvidenceRowCount": len(evidence["evidence"]),
        "pairDecisionCount": len(decisions["pairs"]), "gapDecisionCount": len(decisions["gaps"]),
        "treeStrategyCount": len(topologies["fixtures"]), "treeTopologyDuplicateCount": 0,
        "researchInstanceV2Count": len(instances["v2"]), "boundedNodeCoverage": "8/8",
        "nodeActivationCandidateCount": len(activation["package"]["nodeActivationCandidates"]),
        "pairActivationCandidateCount": 0,
        "inquiryGrammarActivationCandidateCount": len(activation["package"]["inquiryGrammarCandidates"]),
        "structuralAnnotationCandidateCount": len(activation["package"]["structuralAnnotationCandidates"]),
        "externalReviewUnitCount": len(activation["reviews"]), "externalHumanReviewCompleted": False,
        "activeRelationTypeCount": 0, "activePairRuleCount": 0, "activeClusterRuleCount": 0,
        "activeChainRuleCount": 0, "realSemanticImageCount": 0,
        "archiveObjectReferenceCount": 0, "contextInputReferenceCount": 0, "spacetimeInputReferenceCount": 0,
        "externalModelInferenceCount": 0, "vectorDatabaseReferenceCount": 0,
        **seal,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
