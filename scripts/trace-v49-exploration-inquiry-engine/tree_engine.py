"""Flow-first bounded inquiry-tree expansion."""

from __future__ import annotations

from collections import Counter
from typing import Any

from model import MAX_SEMANTIC_NODE_COUNT, MAX_SIBLING_COUNT, MAX_TOTAL_TREE_ITEM_COUNT, MAX_TREE_DEPTH, TreeItemKind


def expand_inquiry_tree(seed: dict[str, Any], freeze: dict[str, Any], flow: dict[str, Any]) -> dict[str, Any]:
    candidates = {candidate["senseId"]: candidate for candidate in freeze["candidates"]}
    root_id = f"TREE-ROOT-{seed['seedId'].removeprefix('INQUIRY-SEED-')}"
    items: list[dict[str, Any]] = [{
        "itemId": root_id, "itemKind": TreeItemKind.INQUIRY_OPERATION.value, "parentItemId": None,
        "depth": 0, "order": 0, "label": seed["plainLanguageResearchQuestion"], "evidenceRefs": [], "gapRefs": [],
    }]
    node_ids = []
    for index, sense_id in enumerate(seed["candidateSenseIds"], start=1):
        candidate = candidates[sense_id]
        item_id = f"TREE-NODE-{seed['seedId'][-3:]}-{index}"
        node_ids.append(item_id)
        items.append({
            "itemId": item_id, "itemKind": TreeItemKind.SEMANTIC_NODE_REFERENCE.value, "parentItemId": root_id,
            "depth": 1, "order": index - 1, "label": candidate["label"], "candidateSenseId": sense_id,
            "evidenceRefs": sorted(candidate["lexicalAttestationIds"] + candidate["grammarAttestationIds"]), "gapRefs": [],
        })
    evidence_parent = node_ids[0]
    items.append({
        "itemId": f"TREE-EVIDENCE-{seed['seedId'][-3:]}", "itemKind": TreeItemKind.EVIDENCE_NOTE.value,
        "parentItemId": evidence_parent, "depth": 2, "order": 0, "label": "Direct lexical and grammar evidence bound to this inquiry",
        "evidenceRefs": list(seed["grammarAttestationRefs"]), "gapRefs": [],
    })
    note_parent = node_ids[-1]
    note_kind = TreeItemKind.CONTESTATION_NOTE.value if seed["canonicalTreeStrategy"] in {"BINARY_FORK", "REFLEXIVE_RETURN"} else TreeItemKind.QUALIFICATION_NOTE.value
    items.append({
        "itemId": f"TREE-BOUNDARY-{seed['seedId'][-3:]}", "itemKind": note_kind,
        "parentItemId": note_parent, "depth": 2, "order": 0, "label": "Qualification and contestation remain attached to the source-bounded meanings",
        "evidenceRefs": [], "gapRefs": [],
    })
    items.append({
        "itemId": f"TREE-GAP-{seed['seedId'][-3:]}", "itemKind": TreeItemKind.EVIDENCE_GAP_NOTE.value,
        "parentItemId": f"TREE-BOUNDARY-{seed['seedId'][-3:]}", "depth": 3, "order": 0,
        "label": "Unresolved evidence and external domain-review gate", "evidenceRefs": [], "gapRefs": list(seed["unresolvedGapRefs"]),
    })
    tree = {"rootInquiryId": root_id, "strategy": seed["canonicalTreeStrategy"], "primaryInquiryFlow": flow, "treeItems": items}
    validate_tree_limits(tree)
    return tree


def validate_tree_limits(tree: dict[str, Any]) -> None:
    items = tree["treeItems"]
    semantic_count = sum(item["itemKind"] == TreeItemKind.SEMANTIC_NODE_REFERENCE.value for item in items)
    siblings = Counter(item["parentItemId"] for item in items if item["parentItemId"] is not None)
    roots = [item for item in items if item["parentItemId"] is None]
    if len(roots) != 1 or roots[0]["itemKind"] != TreeItemKind.INQUIRY_OPERATION.value:
        raise ValueError("ROOT_INQUIRY_REQUIRED")
    if semantic_count > MAX_SEMANTIC_NODE_COUNT or max((item["depth"] for item in items), default=0) > MAX_TREE_DEPTH or max(siblings.values(), default=0) > MAX_SIBLING_COUNT or len(items) > MAX_TOTAL_TREE_ITEM_COUNT:
        raise ValueError("TREE_LIMIT_EXCEEDED")


def bind_evidence_to_tree(tree: dict[str, Any]) -> list[str]:
    return sorted({ref for item in tree["treeItems"] for ref in item["evidenceRefs"]})


def bind_gaps_to_tree(tree: dict[str, Any]) -> list[str]:
    return sorted({ref for item in tree["treeItems"] for ref in item["gapRefs"]})
