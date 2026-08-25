"""Compile deterministic, non-public Research Inquiry Instances."""

from __future__ import annotations

from typing import Any

from canonical import semantic_hash
from flow_planner import plan_primary_inquiry_flow, select_tree_strategy
from strict_parse import validate_research_inquiry_instance
from tree_engine import bind_gaps_to_tree, expand_inquiry_tree


def _semantic_node_ref(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidateId": candidate["candidateId"], "senseId": candidate["senseId"], "label": candidate["label"],
        "researchStatus": candidate["researchStatus"], "round9Decision": candidate["round9Decision"],
        "round10NodeRoleDecision": candidate["round10NodeRoleDecision"], "technicalRole": candidate["technicalRole"],
        "plainLanguageGlossRef": candidate["plainLanguageGlossRef"], "argumentRoleRef": candidate["argumentRoleRef"],
        "directionalityStatus": candidate["directionalityStatus"], "qualificationStatus": candidate["qualificationStatus"],
        "contestationStatus": candidate["contestationStatus"], "lexicalAttestationIds": candidate["lexicalAttestationIds"],
        "grammarAttestationIds": candidate["grammarAttestationIds"], "sourceIds": candidate["sourceIds"],
    }


def compile_research_inquiry_instance(seed: dict[str, Any], freeze: dict[str, Any], instance_ordinal: int) -> dict[str, Any]:
    candidates = {candidate["senseId"]: candidate for candidate in freeze["candidates"]}
    nodes = [_semantic_node_ref(candidates[sense]) for sense in seed["candidateSenseIds"]]
    flow = plan_primary_inquiry_flow(seed)
    tree = expand_inquiry_tree(seed, freeze, flow)
    lexical = sorted({item for node in nodes for item in node["lexicalAttestationIds"]})
    grammar = sorted({item for node in nodes for item in node["grammarAttestationIds"]})
    sources = sorted({item for node in nodes for item in node["sourceIds"]})
    labels = [node["label"] for node in nodes]
    inclusion = f"This research preview includes {', '.join(labels)} because each is a frozen bounded Node-role candidate and the seed is one of the five governed inquiry questions."
    non_claim = "The primary carrier is an inquiry link with unresolved historical direction; it asks how to investigate the concepts and does not assert a semantic relation or historical claim."
    evidence_summary = f"Direct binding includes {len(lexical)} lexical attestations, {len(grammar)} grammar attestations, and {len(sources)} distinct source IDs for this Instance."
    limitation = "The available evidence does not authorize a historical pair rule, public export, active grammar, or semantic Image; external design-history review remains required."
    unsigned = {
        "instanceId": f"INQUIRY-INSTANCE-{instance_ordinal:03d}", "instanceVersion": "1",
        "freezePackageHash": freeze["canonicalHash"], "seedId": seed["seedId"], "seedHash": semantic_hash(seed),
        "treeStrategy": select_tree_strategy(seed), "treeStrategyVersion": "1", "rootInquiry": seed["plainLanguageResearchQuestion"],
        "semanticNodeRefs": nodes, "primaryInquiryFlow": flow, "treeItems": tree["treeItems"],
        "evidenceCoverage": {"lexicalAttestationCount": len(lexical), "grammarAttestationCount": len(grammar), "directAttestationCount": len(lexical) + len(grammar)},
        "sourceCoverage": {"distinctSourceCount": len(sources), "sourceIds": sources},
        "qualificationRefs": sorted({node["qualificationStatus"] for node in nodes}),
        "contestationRefs": sorted({node["contestationStatus"] for node in nodes}),
        "gapRefs": bind_gaps_to_tree(tree),
        "inclusionExplanation": inclusion, "nonClaimExplanation": non_claim, "evidenceSummary": evidence_summary,
        "limitationStatement": limitation, "historicalClaim": False, "semanticRelation": False, "publicExportable": False,
        "activationState": "RESEARCH_CANDIDATE_ONLY", "researchPreviewOnly": True,
    }
    instance = {**unsigned, "canonicalHash": semantic_hash(unsigned)}
    return validate_research_inquiry_instance(instance, freeze, seed)


def verify_research_inquiry_instance(instance: dict[str, Any], freeze: dict[str, Any], seed: dict[str, Any]) -> bool:
    validate_research_inquiry_instance(instance, freeze, seed)
    return True


def canonicalize_instance(instance: dict[str, Any]) -> str:
    from canonical import canonical_json
    return canonical_json(instance)


def hash_instance(instance: dict[str, Any]) -> str:
    return semantic_hash({key: value for key, value in instance.items() if key != "canonicalHash"})
