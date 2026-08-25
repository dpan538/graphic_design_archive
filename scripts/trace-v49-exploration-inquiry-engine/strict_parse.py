"""Strict runtime parsing and structural-contamination rejection."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Iterable

from canonical import semantic_hash, without_hash
from model import (
    CandidateResearchStatus,
    InquiryLinkKind,
    InquirySeedKind,
    InquiryTreeStrategy,
    MAX_SEMANTIC_NODE_COUNT,
    MAX_SIBLING_COUNT,
    MAX_TOTAL_TREE_ITEM_COUNT,
    MAX_TREE_DEPTH,
    TreeItemKind,
)


class StrictValidationError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


CONTAMINATION_KEY_CODES = {
    "archiveobjectid": "ARCHIVE_OBJECT_CONTAMINATION",
    "objectid": "ARCHIVE_OBJECT_CONTAMINATION",
    "recordid": "ARCHIVE_OBJECT_CONTAMINATION",
    "surfaceid": "ARCHIVE_OBJECT_CONTAMINATION",
    "objecttitle": "ARCHIVE_OBJECT_CONTAMINATION",
    "thumbnail": "ARCHIVE_OBJECT_CONTAMINATION",
    "recordurl": "ARCHIVE_OBJECT_CONTAMINATION",
    "objecthref": "ARCHIVE_OBJECT_CONTAMINATION",
    "contextdto": "CONTEXT_CONTAMINATION",
    "contextpayload": "CONTEXT_CONTAMINATION",
    "spacetimepayload": "SPACETIME_CONTAMINATION",
    "spacetimedto": "SPACETIME_CONTAMINATION",
    "modelid": "EXTERNAL_MODEL_CONTAMINATION",
    "modelprovenance": "EXTERNAL_MODEL_CONTAMINATION",
    "embeddingmodel": "EXTERNAL_MODEL_CONTAMINATION",
    "vectorref": "VECTOR_REFERENCE_CONTAMINATION",
    "vectorreference": "VECTOR_REFERENCE_CONTAMINATION",
}
PROHIBITED_CLAIM = re.compile(r"\b(caused|led to|became|influenced)\b", re.IGNORECASE)


def detect_structural_contamination(value: Any) -> list[str]:
    failures: set[str] = set()

    def visit(current: Any) -> None:
        if isinstance(current, dict):
            normalized = {str(key).replace("_", "").replace("-", "").lower() for key in current}
            for key in normalized:
                if key in CONTAMINATION_KEY_CODES:
                    failures.add(CONTAMINATION_KEY_CODES[key])
            if {"contextkind", "termid"} <= normalized or {"representations", "contextkind"} <= normalized:
                failures.add("CONTEXT_CONTAMINATION")
            if {"periodid", "geographyid"} <= normalized or {"latitude", "longitude", "periodid"} <= normalized:
                failures.add("SPACETIME_CONTAMINATION")
            if any(token in normalized for token in {"qwen", "bge", "e5", "jina", "fasttext", "vectordb", "annindex"}):
                failures.add("EXTERNAL_MODEL_CONTAMINATION")
            for child in current.values():
                visit(child)
        elif isinstance(current, list):
            for child in current:
                visit(child)

    visit(value)
    return sorted(failures)


def require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise StrictValidationError(code, message)


def exact_keys(value: Any, required: Iterable[str], optional: Iterable[str] = ()) -> dict[str, Any]:
    require(isinstance(value, dict), "INVALID_TYPE", "expected object")
    required_set, allowed = set(required), set(required) | set(optional)
    unknown = sorted(set(value) - allowed)
    missing = sorted(required_set - set(value))
    require(not unknown, "UNKNOWN_FIELD", f"unknown fields: {unknown}")
    require(not missing, "MISSING_FIELD", f"missing fields: {missing}")
    return value


def unique_nonempty(values: Any, field: str) -> list[str]:
    require(isinstance(values, list), "INVALID_TYPE", f"{field} must be an array")
    require(all(isinstance(item, str) and item.strip() for item in values), "EMPTY_VALUE", f"{field} contains an empty value")
    require(len(values) == len(set(values)), "DUPLICATE_ID", f"{field} contains duplicates")
    return values


FREEZE_KEYS = {
    "packageId", "version", "round9CandidateRegistrySha256", "round10InputTermSha256",
    "round10CommitSha", "round11CommitSha", "active", "candidates", "canonicalHash",
}
CANDIDATE_KEYS = {
    "candidateId", "senseId", "label", "researchStatus", "round9Decision",
    "round10NodeRoleDecision", "technicalRole", "plainLanguageGlossRef", "argumentRoleRef",
    "directionalityStatus", "qualificationStatus", "contestationStatus",
    "lexicalAttestationIds", "grammarAttestationIds", "sourceIds", "pairQuestionIds",
    "clusterHandoffIds", "observedChainIds", "vocabularyGapIds", "active",
}


def validate_candidate_freeze(value: Any) -> dict[str, Any]:
    exact_keys(value, FREEZE_KEYS)
    require(not detect_structural_contamination(value), "STRUCTURAL_CONTAMINATION", "freeze contains prohibited input")
    require(value["packageId"] == "trace-exploration-research-candidates-v1", "PACKAGE_ID_MISMATCH", "freeze package ID changed")
    require(value["version"] == "1" and value["active"] is False, "STATUS_MUTATION", "freeze status/version changed")
    candidates = value["candidates"]
    require(isinstance(candidates, list) and len(candidates) == 16, "CANDIDATE_COUNT", "freeze must contain 16 candidates")
    ids, senses, labels, statuses = [], [], [], []
    for candidate in candidates:
        exact_keys(candidate, CANDIDATE_KEYS)
        ids.append(candidate["candidateId"]); senses.append(candidate["senseId"]); labels.append(candidate["label"]); statuses.append(candidate["researchStatus"])
        require(all(isinstance(candidate[key], str) and candidate[key].strip() for key in CANDIDATE_KEYS - {"active", "lexicalAttestationIds", "grammarAttestationIds", "sourceIds", "pairQuestionIds", "clusterHandoffIds", "observedChainIds", "vocabularyGapIds"}), "EMPTY_VALUE", "candidate contains empty identity/evidence reference")
        require(candidate["active"] is False, "STATUS_MUTATION", "candidate became active")
        for key in ("lexicalAttestationIds", "grammarAttestationIds", "sourceIds", "pairQuestionIds", "clusterHandoffIds", "observedChainIds", "vocabularyGapIds"):
            unique_nonempty(candidate[key], key)
        require(candidate["lexicalAttestationIds"] and candidate["grammarAttestationIds"] and candidate["sourceIds"], "EVIDENCE_ORPHAN", "candidate lacks direct evidence")
    require(len(ids) == len(set(ids)) == 16 and len(senses) == len(set(senses)) == 16, "DUPLICATE_ID", "duplicate candidate/sense identity")
    require(len(labels) == len(set(labels)) == 16, "DUPLICATE_SEMANTIC_ID", "duplicate candidate label")
    counts = Counter(statuses)
    require(counts[CandidateResearchStatus.BOUNDED.value] == 8 and counts[CandidateResearchStatus.DEFERRED.value] == 8, "STATUS_COUNT", "freeze status split is not 8/8")
    require(semantic_hash(without_hash(value)) == value["canonicalHash"], "HASH_MISMATCH", "freeze canonical hash mismatch")
    return value


SEED_KEYS = {
    "seedId", "seedKind", "candidateSenseIds", "researchStatus", "pairDecision", "evidenceRefs",
    "grammarAttestationRefs", "unresolvedGapRefs", "allowedTreeStrategies", "canonicalTreeStrategy",
    "plainLanguageResearchQuestion", "historicalClaim", "publicExportable", "allowedOrigins",
}


def validate_inquiry_seed(value: Any, freeze: dict[str, Any]) -> dict[str, Any]:
    exact_keys(value, SEED_KEYS)
    require(not detect_structural_contamination(value), "STRUCTURAL_CONTAMINATION", "seed contains prohibited input")
    senses = unique_nonempty(value["candidateSenseIds"], "candidateSenseIds")
    known = {candidate["senseId"]: candidate for candidate in freeze["candidates"]}
    require(all(sense in known for sense in senses), "DANGLING_REFERENCE", "seed references an unknown sense")
    require(all(known[sense]["researchStatus"] == CandidateResearchStatus.BOUNDED.value for sense in senses), "DEFERRED_CANDIDATE_USE", "deferred candidate entered a seed")
    require(value["seedKind"] in {item.value for item in InquirySeedKind}, "INVALID_ENUM", "invalid seed kind")
    expected_count = 2 if value["seedKind"] == InquirySeedKind.PAIR.value else 1
    require(len(senses) == expected_count, "ARITY_MISMATCH", "seed kind/sense count mismatch")
    require(value["historicalClaim"] is False and value["publicExportable"] is False, "STATUS_MUTATION", "seed crossed research boundary")
    require(value["allowedOrigins"] == ["RESEARCH_INQUIRY"], "ORIGIN_POLICY_VIOLATION", "seed origin is not inquiry-only")
    strategies = unique_nonempty(value["allowedTreeStrategies"], "allowedTreeStrategies")
    require(all(item in {strategy.value for strategy in InquiryTreeStrategy} for item in strategies), "INVALID_ENUM", "invalid tree strategy")
    require(value["canonicalTreeStrategy"] in strategies, "STRATEGY_NOT_ALLOWED", "canonical strategy is not allowed")
    require(value["plainLanguageResearchQuestion"].strip().endswith("?"), "QUESTION_FORM_REQUIRED", "root inquiry is not a question")
    require(not PROHIBITED_CLAIM.search(value["plainLanguageResearchQuestion"]), "HISTORICAL_CLAIM_REJECTED", "seed emits a declarative historical claim")
    unique_nonempty(value["evidenceRefs"], "evidenceRefs")
    unique_nonempty(value["grammarAttestationRefs"], "grammarAttestationRefs")
    unique_nonempty(value["unresolvedGapRefs"], "unresolvedGapRefs")
    return value


INSTANCE_KEYS = {
    "instanceId", "instanceVersion", "freezePackageHash", "seedId", "seedHash", "treeStrategy",
    "treeStrategyVersion", "rootInquiry", "semanticNodeRefs", "primaryInquiryFlow", "treeItems",
    "evidenceCoverage", "sourceCoverage", "qualificationRefs", "contestationRefs", "gapRefs",
    "inclusionExplanation", "nonClaimExplanation", "evidenceSummary", "limitationStatement",
    "historicalClaim", "semanticRelation", "publicExportable", "activationState", "researchPreviewOnly",
    "canonicalHash",
}
FLOW_KEYS = {
    "flowId", "origin", "carrierKind", "linkKind", "candidateSenseIds", "navigationDirection",
    "historicalDirectionStatus", "historicalClaim", "semanticRelation", "evidenceBackedHistoricalFlow",
}
TREE_ITEM_KEYS = {"itemId", "itemKind", "parentItemId", "depth", "order", "label", "candidateSenseId", "evidenceRefs", "gapRefs"}


def validate_inquiry_tree(value: Any) -> dict[str, Any]:
    exact_keys(value, {"rootInquiryId", "strategy", "primaryInquiryFlow", "treeItems"})
    contamination = detect_structural_contamination(value)
    require(not contamination, contamination[0] if contamination else "STRUCTURAL_CONTAMINATION", f"tree contamination: {contamination}")
    require(value["strategy"] in {item.value for item in InquiryTreeStrategy}, "INVALID_ENUM", "invalid tree strategy")
    flow = exact_keys(value["primaryInquiryFlow"], FLOW_KEYS)
    require(flow["origin"] == "RESEARCH_INQUIRY" and flow["carrierKind"] == "INQUIRY_LINK", "ORIGIN_POLICY_VIOLATION", "tree flow origin/carrier changed")
    require(flow["linkKind"] in {item.value for item in InquiryLinkKind}, "INVALID_ENUM", "invalid inquiry link kind")
    require(flow["historicalClaim"] is False and flow["semanticRelation"] is False and flow["evidenceBackedHistoricalFlow"] is False, "CARRIER_SEPARATION", "inquiry carrier became a historical Flow")
    items = value["treeItems"]
    require(isinstance(items, list) and 1 <= len(items) <= MAX_TOTAL_TREE_ITEM_COUNT, "TREE_LIMIT", "tree item count exceeds limit")
    ids = [item.get("itemId") for item in items]
    require(len(ids) == len(set(ids)), "DUPLICATE_ID", "duplicate tree item ID")
    id_set, children, roots = set(ids), defaultdict(list), []
    for item in items:
        exact_keys(item, TREE_ITEM_KEYS - {"candidateSenseId"}, {"candidateSenseId"})
        require(item["itemKind"] in {kind.value for kind in TreeItemKind}, "INVALID_ENUM", "invalid tree item kind")
        require(isinstance(item["depth"], int) and 0 <= item["depth"] <= MAX_TREE_DEPTH, "TREE_LIMIT", "tree depth exceeds limit")
        require(isinstance(item["label"], str) and item["label"].strip(), "EMPTY_VALUE", "tree item label is empty")
        if item["evidenceRefs"]: unique_nonempty(item["evidenceRefs"], "evidenceRefs")
        if item["gapRefs"]: unique_nonempty(item["gapRefs"], "gapRefs")
        if item["parentItemId"] is None:
            roots.append(item)
        else:
            require(item["parentItemId"] in id_set, "DANGLING_REFERENCE", "tree item has dangling parent")
            children[item["parentItemId"]].append(item)
    require(len(roots) == 1 and roots[0]["itemId"] == value["rootInquiryId"] and roots[0]["itemKind"] == TreeItemKind.INQUIRY_OPERATION.value, "ROOT_INQUIRY_REQUIRED", "tree lacks exactly one root inquiry")
    require(max((len(group) for group in children.values()), default=0) <= MAX_SIBLING_COUNT, "TREE_LIMIT", "sibling count exceeds limit")
    return value


def validate_research_inquiry_instance(value: Any, freeze: dict[str, Any], seed: dict[str, Any]) -> dict[str, Any]:
    exact_keys(value, INSTANCE_KEYS)
    contamination = detect_structural_contamination(value)
    require(not contamination, contamination[0] if contamination else "STRUCTURAL_CONTAMINATION", f"instance contamination: {contamination}")
    require(value["freezePackageHash"] == freeze["canonicalHash"], "HASH_MISMATCH", "freeze binding mismatch")
    require(value["seedId"] == seed["seedId"] and value["seedHash"] == semantic_hash(seed), "HASH_MISMATCH", "seed binding mismatch")
    require(value["rootInquiry"] == seed["plainLanguageResearchQuestion"] and value["rootInquiry"].endswith("?"), "QUESTION_FORM_REQUIRED", "root inquiry mismatch")
    require(value["treeStrategy"] == seed["canonicalTreeStrategy"], "STRATEGY_MISMATCH", "tree strategy mismatch")
    require(value["historicalClaim"] is False and value["semanticRelation"] is False and value["publicExportable"] is False, "STATUS_MUTATION", "instance crossed research boundary")
    require(value["activationState"] == "RESEARCH_CANDIDATE_ONLY" and value["researchPreviewOnly"] is True, "STATUS_MUTATION", "instance activation state changed")
    require(not any(PROHIBITED_CLAIM.search(value[key]) for key in ("rootInquiry", "inclusionExplanation", "nonClaimExplanation", "evidenceSummary", "limitationStatement")), "HISTORICAL_CLAIM_REJECTED", "instance emits prohibited declarative relation")

    nodes = value["semanticNodeRefs"]
    require(isinstance(nodes, list) and 1 <= len(nodes) <= MAX_SEMANTIC_NODE_COUNT, "TREE_LIMIT", "semantic Node count exceeds limit")
    sense_ids = [node.get("senseId") for node in nodes]
    require(len(sense_ids) == len(set(sense_ids)) and sense_ids == seed["candidateSenseIds"], "DUPLICATE_SEMANTIC_ID", "semantic Node identity/order mismatch")
    known = {candidate["senseId"]: candidate for candidate in freeze["candidates"]}
    require(all(sense in known for sense in sense_ids), "DANGLING_REFERENCE", "instance contains dangling Node")

    validate_inquiry_tree({"rootInquiryId": next((item["itemId"] for item in value["treeItems"] if item.get("parentItemId") is None), ""), "strategy": value["treeStrategy"], "primaryInquiryFlow": value["primaryInquiryFlow"], "treeItems": value["treeItems"]})
    flow = exact_keys(value["primaryInquiryFlow"], FLOW_KEYS)
    require(flow["origin"] == "RESEARCH_INQUIRY" and flow["carrierKind"] == "INQUIRY_LINK", "ORIGIN_POLICY_VIOLATION", "primary flow used the wrong origin/carrier")
    require(flow["linkKind"] in {item.value for item in InquiryLinkKind}, "INVALID_ENUM", "invalid inquiry link kind")
    require(flow["candidateSenseIds"] == sense_ids, "DANGLING_REFERENCE", "primary flow does not bind the instance Nodes")
    require(flow["historicalDirectionStatus"] == "UNRESOLVED_OR_NOT_APPLICABLE", "HISTORICAL_DIRECTION_PROHIBITED", "historical direction was asserted")
    require(flow["historicalClaim"] is False and flow["semanticRelation"] is False and flow["evidenceBackedHistoricalFlow"] is False, "CARRIER_SEPARATION", "inquiry carrier became a historical Flow")

    items = value["treeItems"]
    require(isinstance(items, list) and 1 <= len(items) <= MAX_TOTAL_TREE_ITEM_COUNT, "TREE_LIMIT", "tree item count exceeds limit")
    item_ids = [item.get("itemId") for item in items]
    require(len(item_ids) == len(set(item_ids)), "DUPLICATE_ID", "duplicate tree item ID")
    id_set, children = set(item_ids), defaultdict(list)
    roots = []
    for item in items:
        exact_keys(item, TREE_ITEM_KEYS - {"candidateSenseId"}, {"candidateSenseId"})
        require(item["itemKind"] in {kind.value for kind in TreeItemKind}, "INVALID_ENUM", "invalid tree item kind")
        require(isinstance(item["depth"], int) and 0 <= item["depth"] <= MAX_TREE_DEPTH, "TREE_LIMIT", "tree depth exceeds limit")
        unique_nonempty(item["evidenceRefs"], "evidenceRefs") if item["evidenceRefs"] else None
        unique_nonempty(item["gapRefs"], "gapRefs") if item["gapRefs"] else None
        parent = item["parentItemId"]
        if parent is None:
            roots.append(item)
        else:
            require(parent in id_set, "DANGLING_REFERENCE", "tree item has dangling parent")
            children[parent].append(item)
        if item["itemKind"] == TreeItemKind.SEMANTIC_NODE_REFERENCE.value:
            require(item.get("candidateSenseId") in sense_ids, "DANGLING_REFERENCE", "tree Node reference is dangling")
    require(len(roots) == 1 and roots[0]["depth"] == 0 and roots[0]["itemKind"] == TreeItemKind.INQUIRY_OPERATION.value, "ROOT_INQUIRY_REQUIRED", "tree lacks exactly one root inquiry")
    require(max((len(group) for group in children.values()), default=0) <= MAX_SIBLING_COUNT, "TREE_LIMIT", "sibling count exceeds limit")
    require(semantic_hash(without_hash(value)) == value["canonicalHash"], "HASH_MISMATCH", "instance canonical hash mismatch")
    return value
