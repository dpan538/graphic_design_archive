"""Compile and validate deterministic Round 13 Research Inquiry Instance v2 artifacts."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from canonical_v2 import semantic_hash
from topology import build_tree, validate_tree


CLAIM = re.compile(r"\b(caused|led to|became|influenced)\b", re.IGNORECASE)
PROHIBITED_KEYS = {
    "archiveobjectid",
    "objectid",
    "recordid",
    "surfaceid",
    "objecttitle",
    "recordurl",
    "objecthref",
    "contextdto",
    "contextpayload",
    "spacetimedto",
    "spacetimepayload",
    "modelid",
    "modelprovenance",
    "embeddingmodel",
    "vectorref",
    "vectorreference",
}


def _normalized_key(key: str) -> str:
    return key.replace("_", "").replace("-", "").lower()


def detect_contamination(value: Any) -> list[str]:
    failures: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if _normalized_key(str(key)) in PROHIBITED_KEYS:
                failures.add(_normalized_key(str(key)))
            failures.update(detect_contamination(child))
    elif isinstance(value, list):
        for child in value:
            failures.update(detect_contamination(child))
    return sorted(failures)


def compile_instance_v2(v1: dict[str, Any]) -> dict[str, Any]:
    nodes = v1["semanticNodeRefs"]
    tree_items = build_tree(
        v1["treeStrategy"],
        f"V2-{v1['instanceId']}",
        v1["rootInquiry"],
        nodes,
        v1["primaryInquiryFlow"]["candidateSenseIds"] and v1["evidenceCoverage"]["directAttestationCount"] and [
            reference
            for node in nodes
            for reference in node["grammarAttestationIds"]
        ],
        v1["gapRefs"],
    )
    unsigned = {
        "instanceId": v1["instanceId"],
        "instanceVersion": "2",
        "parentInstanceHash": v1["canonicalHash"],
        "parentInstanceVersion": "1",
        "freezePackageHash": v1["freezePackageHash"],
        "seedId": v1["seedId"],
        "seedHash": v1["seedHash"],
        "treeStrategy": v1["treeStrategy"],
        "treeStrategyVersion": "2",
        "rootInquiry": v1["rootInquiry"],
        "semanticNodeRefs": v1["semanticNodeRefs"],
        "primaryInquiryFlow": v1["primaryInquiryFlow"],
        "treeItems": tree_items,
        "evidenceCoverage": v1["evidenceCoverage"],
        "sourceCoverage": v1["sourceCoverage"],
        "qualificationRefs": v1["qualificationRefs"],
        "contestationRefs": v1["contestationRefs"],
        "gapRefs": v1["gapRefs"],
        "inclusionExplanation": v1["inclusionExplanation"],
        "nonClaimExplanation": v1["nonClaimExplanation"],
        "evidenceSummary": v1["evidenceSummary"],
        "limitationStatement": v1["limitationStatement"],
        "topologyChange": {
            "changed": True,
            "summary": "Enum-only presentation was replaced by a strategy-specific canonical inquiry topology.",
            "semanticContentUnchanged": True,
            "evidenceBindingChange": "UNCHANGED",
        },
        "historicalClaim": False,
        "semanticRelation": False,
        "publicExportable": False,
        "activationState": "RESEARCH_CANDIDATE_ONLY",
        "researchPreviewOnly": True,
    }
    value = {**unsigned, "canonicalHash": semantic_hash(unsigned)}
    return validate_instance_v2(value, v1)


def validate_instance_v2(value: dict[str, Any], v1: dict[str, Any]) -> dict[str, Any]:
    expected_keys = {
        "instanceId", "instanceVersion", "parentInstanceHash", "parentInstanceVersion",
        "freezePackageHash", "seedId", "seedHash", "treeStrategy", "treeStrategyVersion",
        "rootInquiry", "semanticNodeRefs", "primaryInquiryFlow", "treeItems", "evidenceCoverage",
        "sourceCoverage", "qualificationRefs", "contestationRefs", "gapRefs", "inclusionExplanation",
        "nonClaimExplanation", "evidenceSummary", "limitationStatement", "topologyChange",
        "historicalClaim", "semanticRelation", "publicExportable", "activationState",
        "researchPreviewOnly", "canonicalHash",
    }
    if set(value) != expected_keys:
        raise ValueError("V2_EXACT_FIELD_FAILURE")
    if detect_contamination(value):
        raise ValueError("STRUCTURAL_CONTAMINATION")
    if value["instanceVersion"] != "2" or value["parentInstanceVersion"] != "1" or value["treeStrategyVersion"] != "2":
        raise ValueError("V2_VERSION_FAILURE")
    if value["parentInstanceHash"] != v1["canonicalHash"]:
        raise ValueError("PARENT_INSTANCE_HASH_MISMATCH")
    preserved = (
        "instanceId", "freezePackageHash", "seedId", "seedHash", "treeStrategy", "rootInquiry",
        "semanticNodeRefs", "primaryInquiryFlow", "evidenceCoverage", "sourceCoverage",
        "qualificationRefs", "contestationRefs", "gapRefs", "inclusionExplanation",
        "nonClaimExplanation", "evidenceSummary", "limitationStatement", "historicalClaim",
        "semanticRelation", "publicExportable", "activationState", "researchPreviewOnly",
    )
    if any(value[key] != v1[key] for key in preserved):
        raise ValueError("V1_V2_SEMANTIC_PRESERVATION_FAILURE")
    if value["historicalClaim"] is not False or value["semanticRelation"] is not False or value["publicExportable"] is not False:
        raise ValueError("ACTIVE_BOUNDARY_FAILURE")
    if value["activationState"] != "RESEARCH_CANDIDATE_ONLY" or value["researchPreviewOnly"] is not True:
        raise ValueError("ACTIVATION_STATE_FAILURE")
    if not value["rootInquiry"].endswith("?") or CLAIM.search(value["rootInquiry"]):
        raise ValueError("QUESTION_FORM_FAILURE")
    topology = value["topologyChange"]
    if topology != {
        "changed": True,
        "summary": "Enum-only presentation was replaced by a strategy-specific canonical inquiry topology.",
        "semanticContentUnchanged": True,
        "evidenceBindingChange": "UNCHANGED",
    }:
        raise ValueError("TOPOLOGY_CHANGE_RECEIPT_FAILURE")
    validate_tree(value["treeStrategy"], value["treeItems"])
    sense_ids = [node["senseId"] for node in value["semanticNodeRefs"]]
    tree_senses = [item["candidateSenseId"] for item in value["treeItems"] if item["itemKind"] == "SEMANTIC_NODE_REFERENCE"]
    if Counter(sense_ids) != Counter(tree_senses):
        raise ValueError("TREE_SEMANTIC_NODE_MISMATCH")
    for binding_key in ("evidenceRefs", "gapRefs"):
        parent_bindings = {
            reference
            for item in v1["treeItems"]
            for reference in item.get(binding_key, [])
        }
        child_bindings = {
            reference
            for item in value["treeItems"]
            for reference in item.get(binding_key, [])
        }
        if parent_bindings != child_bindings:
            raise ValueError(f"TREE_{binding_key.upper()}_PRESERVATION_FAILURE")
    unsigned = {key: item for key, item in value.items() if key != "canonicalHash"}
    if semantic_hash(unsigned) != value["canonicalHash"]:
        raise ValueError("V2_HASH_MISMATCH")
    return value
