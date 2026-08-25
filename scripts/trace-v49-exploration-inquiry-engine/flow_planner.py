"""Plan one and only one primary research-inquiry flow per seed."""

from __future__ import annotations

from typing import Any

from model import InquiryLinkKind, InquiryTreeStrategy


LINK_KIND_BY_STRATEGY = {
    InquiryTreeStrategy.LINEAR_PATH.value: InquiryLinkKind.OPEN_QUESTION.value,
    InquiryTreeStrategy.BINARY_FORK.value: InquiryLinkKind.CONTRAST_QUESTION.value,
    InquiryTreeStrategy.BINARY_CONVERGENCE.value: InquiryLinkKind.CONDITION_QUESTION.value,
    InquiryTreeStrategy.QUALIFIED_PATH.value: InquiryLinkKind.QUALIFICATION_QUESTION.value,
    InquiryTreeStrategy.REFLEXIVE_RETURN.value: InquiryLinkKind.REFLEXIVE_QUESTION.value,
    InquiryTreeStrategy.EVIDENCE_GAP_TREE.value: InquiryLinkKind.EVIDENCE_GAP_QUESTION.value,
}


def select_tree_strategy(seed: dict[str, Any]) -> str:
    selected = seed["canonicalTreeStrategy"]
    if selected not in seed["allowedTreeStrategies"]:
        raise ValueError("canonical strategy is not authorized by the seed")
    return selected


def plan_primary_inquiry_flow(seed: dict[str, Any]) -> dict[str, Any]:
    strategy = select_tree_strategy(seed)
    navigation = "RETURN_TO_ROOT" if strategy == InquiryTreeStrategy.REFLEXIVE_RETURN.value else "CONVERGE_ON_ROOT" if strategy == InquiryTreeStrategy.BINARY_CONVERGENCE.value else "ROOT_TO_CHILDREN"
    return {
        "flowId": f"PRIMARY-FLOW-{seed['seedId'].removeprefix('INQUIRY-SEED-')}",
        "origin": "RESEARCH_INQUIRY",
        "carrierKind": "INQUIRY_LINK",
        "linkKind": LINK_KIND_BY_STRATEGY[strategy],
        "candidateSenseIds": list(seed["candidateSenseIds"]),
        "navigationDirection": navigation,
        "historicalDirectionStatus": "UNRESOLVED_OR_NOT_APPLICABLE",
        "historicalClaim": False,
        "semanticRelation": False,
        "evidenceBackedHistoricalFlow": False,
    }
