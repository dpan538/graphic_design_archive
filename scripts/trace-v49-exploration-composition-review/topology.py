"""Distinct inquiry-only topology functions for TRACE v49 Round 13."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Callable


STRATEGIES = (
    "LINEAR_PATH",
    "BINARY_FORK",
    "BINARY_CONVERGENCE",
    "QUALIFIED_PATH",
    "REFLEXIVE_RETURN",
    "EVIDENCE_GAP_TREE",
)
ITEM_KINDS = {
    "SEMANTIC_NODE_REFERENCE",
    "INQUIRY_OPERATION",
    "EVIDENCE_NOTE",
    "QUALIFICATION_NOTE",
    "CONTESTATION_NOTE",
    "EVIDENCE_GAP_NOTE",
}
MAX_SEMANTIC_NODE_COUNT = 2
MAX_SIBLING_COUNT = 2
MAX_TREE_DEPTH = 4
MAX_TOTAL_TREE_ITEM_COUNT = 7


def _item(
    item_id: str,
    kind: str,
    parent: str | None,
    depth: int,
    order: int,
    label: str,
    role: str,
    *,
    branch_status: str = "PRIMARY",
    sense_id: str | None = None,
    evidence_refs: list[str] | None = None,
    gap_refs: list[str] | None = None,
    convergence_sources: list[str] | None = None,
    navigation_target: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "itemId": item_id,
        "itemKind": kind,
        "parentItemId": parent,
        "depth": depth,
        "order": order,
        "label": label,
        "inquiryRole": role,
        "branchStatus": branch_status,
        "evidenceRefs": sorted(set(evidence_refs or [])),
        "gapRefs": sorted(set(gap_refs or [])),
        "convergenceSourceItemIds": sorted(set(convergence_sources or [])),
        "navigationTargetItemId": navigation_target,
    }
    if sense_id is not None:
        value["candidateSenseId"] = sense_id
    return value


def _root(prefix: str, question: str) -> dict[str, Any]:
    return _item(f"{prefix}-ROOT", "INQUIRY_OPERATION", None, 0, 0, question, "ROOT_INQUIRY")


def _node(prefix: str, index: int, parent: str, depth: int, order: int, node: dict[str, Any], role: str) -> dict[str, Any]:
    return _item(
        f"{prefix}-NODE-{index}",
        "SEMANTIC_NODE_REFERENCE",
        parent,
        depth,
        order,
        node["label"],
        role,
        sense_id=node["senseId"],
        evidence_refs=sorted(set(node["lexicalAttestationIds"] + node["grammarAttestationIds"])),
    )


def linear_path(prefix: str, question: str, nodes: list[dict[str, Any]], evidence_refs: list[str], gap_refs: list[str]) -> list[dict[str, Any]]:
    root = _root(prefix, question)
    first = _node(prefix, 1, root["itemId"], 1, 0, nodes[0], "STARTING_CONCEPT_QUESTION")
    evidence = _item(f"{prefix}-EVIDENCE", "EVIDENCE_NOTE", first["itemId"], 2, 0, "Check the bounded evidence before continuing", "EVIDENCE_CHECK", evidence_refs=evidence_refs)
    if len(nodes) == 2:
        continuation = _node(prefix, 2, evidence["itemId"], 3, 0, nodes[1], "FOLLOWING_CONCEPT_QUESTION")
    else:
        continuation = _item(f"{prefix}-FOLLOW", "INQUIRY_OPERATION", evidence["itemId"], 3, 0, "Continue the same bounded inquiry", "FOLLOWING_QUESTION")
    boundary = _item(f"{prefix}-BOUNDARY", "QUALIFICATION_NOTE", continuation["itemId"], 4, 0, "Keep the inquiry sequence distinct from historical succession", "SEQUENCE_BOUNDARY", gap_refs=gap_refs)
    return [root, first, evidence, continuation, boundary]


def binary_fork(prefix: str, question: str, nodes: list[dict[str, Any]], evidence_refs: list[str], gap_refs: list[str]) -> list[dict[str, Any]]:
    root = _root(prefix, question)
    left = _item(f"{prefix}-BRANCH-A", "INQUIRY_OPERATION", root["itemId"], 1, 0, "Examine the first bounded interpretation", "ALTERNATIVE_BRANCH_A", branch_status="ALTERNATIVE")
    right = _item(f"{prefix}-BRANCH-B", "INQUIRY_OPERATION", root["itemId"], 1, 1, "Examine the second bounded interpretation", "ALTERNATIVE_BRANCH_B", branch_status="ALTERNATIVE")
    left_child = _node(prefix, 1, left["itemId"], 2, 0, nodes[0], "BRANCH_A_CONCEPT")
    if len(nodes) == 2:
        right_child = _node(prefix, 2, right["itemId"], 2, 0, nodes[1], "BRANCH_B_CONCEPT")
        right_child["gapRefs"] = sorted(set(gap_refs))
    else:
        right_child = _item(f"{prefix}-CONTEST", "CONTESTATION_NOTE", right["itemId"], 2, 0, "Test a competing interpretation without inventing a second concept", "BRANCH_B_CONTESTATION", branch_status="ALTERNATIVE", evidence_refs=evidence_refs, gap_refs=gap_refs)
    return [root, left, right, left_child, right_child]


def binary_convergence(prefix: str, question: str, nodes: list[dict[str, Any]], evidence_refs: list[str], gap_refs: list[str]) -> list[dict[str, Any]]:
    if len(nodes) != 2:
        raise ValueError("BINARY_CONVERGENCE_REQUIRES_TWO_NODES")
    root = _root(prefix, question)
    left = _item(f"{prefix}-BRANCH-A", "INQUIRY_OPERATION", root["itemId"], 1, 0, "Develop the first bounded question branch", "CONVERGENCE_BRANCH_A", branch_status="CONVERGING")
    right = _item(f"{prefix}-BRANCH-B", "INQUIRY_OPERATION", root["itemId"], 1, 1, "Develop the second bounded question branch", "CONVERGENCE_BRANCH_B", branch_status="CONVERGING")
    left_node = _node(prefix, 1, left["itemId"], 2, 0, nodes[0], "CONVERGENCE_INPUT_A")
    right_node = _node(prefix, 2, right["itemId"], 2, 0, nodes[1], "CONVERGENCE_INPUT_B")
    convergence = _item(
        f"{prefix}-CONVERGENCE",
        "INQUIRY_OPERATION",
        left_node["itemId"],
        3,
        0,
        "Bring both question branches to one shared unresolved review problem",
        "SHARED_REVIEW_PROBLEM",
        branch_status="CONVERGENCE",
        evidence_refs=evidence_refs,
        gap_refs=gap_refs,
        convergence_sources=[left_node["itemId"], right_node["itemId"]],
    )
    return [root, left, right, left_node, right_node, convergence]


def qualified_path(prefix: str, question: str, nodes: list[dict[str, Any]], evidence_refs: list[str], gap_refs: list[str]) -> list[dict[str, Any]]:
    root = _root(prefix, question)
    first = _node(prefix, 1, root["itemId"], 1, 0, nodes[0], "PRIMARY_CONCEPT_QUESTION")
    qualification = _item(f"{prefix}-QUALIFICATION", "QUALIFICATION_NOTE", first["itemId"], 2, 0, "Apply the explicit source, regime, role, and scope qualification", "MANDATORY_QUALIFICATION_GATE", branch_status="GATE", evidence_refs=evidence_refs, gap_refs=gap_refs)
    if len(nodes) == 2:
        continuation = _node(prefix, 2, qualification["itemId"], 3, 0, nodes[1], "QUALIFIED_CONTINUATION")
    else:
        continuation = _item(f"{prefix}-CONTINUE", "INQUIRY_OPERATION", qualification["itemId"], 3, 0, "Continue only within the qualified scope", "QUALIFIED_CONTINUATION", branch_status="GATED")
    boundary = _item(f"{prefix}-BOUNDARY", "CONTESTATION_NOTE", continuation["itemId"], 4, 0, "Review whether the qualification prevents flattening", "QUALIFICATION_REVIEW", branch_status="GATED")
    return [root, first, qualification, continuation, boundary]


def reflexive_return(prefix: str, question: str, nodes: list[dict[str, Any]], evidence_refs: list[str], gap_refs: list[str]) -> list[dict[str, Any]]:
    root = _root(prefix, question)
    concept = _node(prefix, 1, root["itemId"], 1, 0, nodes[0], "REFLEXIVE_CONCEPT_QUESTION")
    reflexive = _item(f"{prefix}-REFLEXIVE", "INQUIRY_OPERATION", concept["itemId"], 2, 0, "Examine actor position, audience, gaze, and power", "SELF_POSITIONING_QUESTION", evidence_refs=evidence_refs)
    return_item = _item(f"{prefix}-RETURN", "CONTESTATION_NOTE", reflexive["itemId"], 3, 0, "Return navigation to the root inquiry without a semantic self-loop", "NAVIGATION_RETURN", branch_status="RETURN", gap_refs=gap_refs, navigation_target=root["itemId"])
    boundary = _item(f"{prefix}-NO-LOOP", "QUALIFICATION_NOTE", return_item["itemId"], 4, 0, "The return is navigational and never a historical relation", "RETURN_BOUNDARY", branch_status="RETURN")
    return [root, concept, reflexive, return_item, boundary]


def evidence_gap_tree(prefix: str, question: str, nodes: list[dict[str, Any]], evidence_refs: list[str], gap_refs: list[str]) -> list[dict[str, Any]]:
    root = _root(prefix, question)
    supported = _item(f"{prefix}-SUPPORTED", "INQUIRY_OPERATION", root["itemId"], 1, 0, "Follow the source-supported branch", "SUPPORTED_BRANCH", branch_status="SUPPORTED")
    unresolved = _item(f"{prefix}-UNRESOLVED", "INQUIRY_OPERATION", root["itemId"], 1, 1, "Follow the missing-evidence branch", "UNRESOLVED_BRANCH", branch_status="UNRESOLVED")
    supported_node = _node(prefix, 1, supported["itemId"], 2, 0, nodes[0], "SUPPORTED_CONCEPT")
    evidence = _item(f"{prefix}-EVIDENCE", "EVIDENCE_NOTE", supported_node["itemId"], 3, 0, "Inspect the bounded support", "SUPPORTED_EVIDENCE", branch_status="SUPPORTED", evidence_refs=evidence_refs)
    gap = _item(f"{prefix}-GAP", "EVIDENCE_GAP_NOTE", unresolved["itemId"], 2, 0, "Record the unresolved evidence as a first-class branch", "FIRST_CLASS_EVIDENCE_GAP", branch_status="UNRESOLVED", gap_refs=gap_refs or ["SYNTHETIC-EVIDENCE-GAP"])
    return [root, supported, unresolved, supported_node, evidence, gap]


BUILDERS: dict[str, Callable[[str, str, list[dict[str, Any]], list[str], list[str]], list[dict[str, Any]]]] = {
    "LINEAR_PATH": linear_path,
    "BINARY_FORK": binary_fork,
    "BINARY_CONVERGENCE": binary_convergence,
    "QUALIFIED_PATH": qualified_path,
    "REFLEXIVE_RETURN": reflexive_return,
    "EVIDENCE_GAP_TREE": evidence_gap_tree,
}


def build_tree(strategy: str, prefix: str, question: str, nodes: list[dict[str, Any]], evidence_refs: list[str], gap_refs: list[str]) -> list[dict[str, Any]]:
    if strategy not in BUILDERS:
        raise ValueError("UNKNOWN_TREE_STRATEGY")
    items = BUILDERS[strategy](prefix, question, nodes, evidence_refs, gap_refs)
    validate_tree(strategy, items)
    return items


def validate_tree(strategy: str, items: list[dict[str, Any]]) -> None:
    if strategy not in STRATEGIES:
        raise ValueError("UNKNOWN_TREE_STRATEGY")
    if not 1 <= len(items) <= MAX_TOTAL_TREE_ITEM_COUNT:
        raise ValueError("TREE_ITEM_LIMIT")
    ids = [item["itemId"] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("DUPLICATE_TREE_ITEM")
    by_id = {item["itemId"]: item for item in items}
    roots = [item for item in items if item["parentItemId"] is None]
    if len(roots) != 1 or roots[0]["itemKind"] != "INQUIRY_OPERATION" or roots[0]["depth"] != 0:
        raise ValueError("ROOT_INQUIRY_REQUIRED")
    children: Counter[str] = Counter()
    semantic_count = 0
    for item in items:
        if item["itemKind"] not in ITEM_KINDS:
            raise ValueError("UNKNOWN_TREE_ITEM_KIND")
        if not 0 <= item["depth"] <= MAX_TREE_DEPTH:
            raise ValueError("TREE_DEPTH_LIMIT")
        parent = item["parentItemId"]
        if parent is not None:
            if parent not in by_id or by_id[parent]["depth"] + 1 != item["depth"]:
                raise ValueError("INVALID_PARENT")
            children[parent] += 1
        if item["itemKind"] == "SEMANTIC_NODE_REFERENCE":
            semantic_count += 1
        if item["navigationTargetItemId"] is not None and item["navigationTargetItemId"] not in by_id:
            raise ValueError("DANGLING_NAVIGATION_TARGET")
        if any(source not in by_id for source in item["convergenceSourceItemIds"]):
            raise ValueError("DANGLING_CONVERGENCE_SOURCE")
    if semantic_count > MAX_SEMANTIC_NODE_COUNT or max(children.values(), default=0) > MAX_SIBLING_COUNT:
        raise ValueError("TREE_LIMIT")
    root = roots[0]
    root_id = root["itemId"]

    def descendants_of(item: dict[str, Any], ancestor_id: str) -> bool:
        parent = item["parentItemId"]
        while parent is not None:
            if parent == ancestor_id:
                return True
            parent = by_id[parent]["parentItemId"]
        return False

    convergence = [item for item in items if item["branchStatus"] == "CONVERGENCE"]
    returns = [item for item in items if item["branchStatus"] == "RETURN" and item["navigationTargetItemId"] is not None]
    gaps = [item for item in items if item["itemKind"] == "EVIDENCE_GAP_NOTE"]
    qualifications = [item for item in items if item["branchStatus"] == "GATE"]
    navigation_items = [item for item in items if item["navigationTargetItemId"] is not None]
    if any(item["itemKind"] == "SEMANTIC_NODE_REFERENCE" for item in navigation_items):
        raise ValueError("SEMANTIC_NAVIGATION_FORBIDDEN")
    if strategy != "REFLEXIVE_RETURN" and navigation_items:
        raise ValueError("UNEXPECTED_NAVIGATION")
    if strategy != "BINARY_CONVERGENCE" and any(item["convergenceSourceItemIds"] for item in items):
        raise ValueError("UNEXPECTED_CONVERGENCE_SOURCE")

    roles = Counter(item["inquiryRole"] for item in items)

    def one(role: str) -> dict[str, Any]:
        matches = [item for item in items if item["inquiryRole"] == role]
        if len(matches) != 1:
            raise ValueError(f"{strategy}_ROLE_CARDINALITY")
        return matches[0]

    def role_contract(expected: dict[str, set[str]]) -> bool:
        return roles == Counter({role: 1 for role in expected}) and all(one(role)["itemKind"] in kinds for role, kinds in expected.items())

    if strategy == "LINEAR_PATH":
        follow_role = "FOLLOWING_CONCEPT_QUESTION" if roles["FOLLOWING_CONCEPT_QUESTION"] else "FOLLOWING_QUESTION"
        expected = {
            "ROOT_INQUIRY": {"INQUIRY_OPERATION"},
            "STARTING_CONCEPT_QUESTION": {"SEMANTIC_NODE_REFERENCE"},
            "EVIDENCE_CHECK": {"EVIDENCE_NOTE"},
            follow_role: {"SEMANTIC_NODE_REFERENCE"} if follow_role == "FOLLOWING_CONCEPT_QUESTION" else {"INQUIRY_OPERATION"},
            "SEQUENCE_BOUNDARY": {"QUALIFICATION_NOTE"},
        }
        if (
            not role_contract(expected)
            or one("STARTING_CONCEPT_QUESTION")["parentItemId"] != root_id
            or one("EVIDENCE_CHECK")["parentItemId"] != one("STARTING_CONCEPT_QUESTION")["itemId"]
            or one(follow_role)["parentItemId"] != one("EVIDENCE_CHECK")["itemId"]
            or one("SEQUENCE_BOUNDARY")["parentItemId"] != one(follow_role)["itemId"]
            or any(count > 1 for count in children.values())
        ):
            raise ValueError("LINEAR_PATH_TOPOLOGY")
    elif strategy == "BINARY_FORK":
        right_role = "BRANCH_B_CONCEPT" if roles["BRANCH_B_CONCEPT"] else "BRANCH_B_CONTESTATION"
        expected = {
            "ROOT_INQUIRY": {"INQUIRY_OPERATION"},
            "ALTERNATIVE_BRANCH_A": {"INQUIRY_OPERATION"},
            "ALTERNATIVE_BRANCH_B": {"INQUIRY_OPERATION"},
            "BRANCH_A_CONCEPT": {"SEMANTIC_NODE_REFERENCE"},
            right_role: {"SEMANTIC_NODE_REFERENCE"} if right_role == "BRANCH_B_CONCEPT" else {"CONTESTATION_NOTE"},
        }
        left = one("ALTERNATIVE_BRANCH_A")
        right = one("ALTERNATIVE_BRANCH_B")
        if (
            not role_contract(expected)
            or left["parentItemId"] != root_id
            or right["parentItemId"] != root_id
            or left["branchStatus"] != "ALTERNATIVE"
            or right["branchStatus"] != "ALTERNATIVE"
            or one("BRANCH_A_CONCEPT")["parentItemId"] != left["itemId"]
            or one(right_role)["parentItemId"] != right["itemId"]
            or convergence
            or returns
        ):
            raise ValueError("BINARY_FORK_TOPOLOGY")
    elif strategy == "BINARY_CONVERGENCE":
        expected = {
            "ROOT_INQUIRY": {"INQUIRY_OPERATION"},
            "CONVERGENCE_BRANCH_A": {"INQUIRY_OPERATION"},
            "CONVERGENCE_BRANCH_B": {"INQUIRY_OPERATION"},
            "CONVERGENCE_INPUT_A": {"SEMANTIC_NODE_REFERENCE"},
            "CONVERGENCE_INPUT_B": {"SEMANTIC_NODE_REFERENCE"},
            "SHARED_REVIEW_PROBLEM": {"INQUIRY_OPERATION"},
        }
        left = one("CONVERGENCE_BRANCH_A")
        right = one("CONVERGENCE_BRANCH_B")
        input_a = one("CONVERGENCE_INPUT_A")
        input_b = one("CONVERGENCE_INPUT_B")
        shared = one("SHARED_REVIEW_PROBLEM")
        if (
            not role_contract(expected)
            or left["parentItemId"] != root_id
            or right["parentItemId"] != root_id
            or left["branchStatus"] != "CONVERGING"
            or right["branchStatus"] != "CONVERGING"
            or input_a["parentItemId"] != left["itemId"]
            or input_b["parentItemId"] != right["itemId"]
            or shared["branchStatus"] != "CONVERGENCE"
            or len(convergence) != 1
            or set(shared["convergenceSourceItemIds"]) != {input_a["itemId"], input_b["itemId"]}
        ):
            raise ValueError("BINARY_CONVERGENCE_TOPOLOGY")
    elif strategy == "QUALIFIED_PATH":
        continuation = one("QUALIFIED_CONTINUATION")
        expected = {
            "ROOT_INQUIRY": {"INQUIRY_OPERATION"},
            "PRIMARY_CONCEPT_QUESTION": {"SEMANTIC_NODE_REFERENCE"},
            "MANDATORY_QUALIFICATION_GATE": {"QUALIFICATION_NOTE"},
            "QUALIFIED_CONTINUATION": {"SEMANTIC_NODE_REFERENCE", "INQUIRY_OPERATION"},
            "QUALIFICATION_REVIEW": {"CONTESTATION_NOTE"},
        }
        if (
            not role_contract(expected)
            or one("PRIMARY_CONCEPT_QUESTION")["parentItemId"] != root_id
            or one("MANDATORY_QUALIFICATION_GATE")["parentItemId"] != one("PRIMARY_CONCEPT_QUESTION")["itemId"]
            or continuation["parentItemId"] != one("MANDATORY_QUALIFICATION_GATE")["itemId"]
            or one("QUALIFICATION_REVIEW")["parentItemId"] != continuation["itemId"]
            or not descendants_of(continuation, one("MANDATORY_QUALIFICATION_GATE")["itemId"])
            or any(count > 1 for count in children.values())
        ):
            raise ValueError("QUALIFIED_PATH_TOPOLOGY")
    elif strategy == "REFLEXIVE_RETURN":
        expected = {
            "ROOT_INQUIRY": {"INQUIRY_OPERATION"},
            "REFLEXIVE_CONCEPT_QUESTION": {"SEMANTIC_NODE_REFERENCE"},
            "SELF_POSITIONING_QUESTION": {"INQUIRY_OPERATION"},
            "NAVIGATION_RETURN": {"CONTESTATION_NOTE"},
            "RETURN_BOUNDARY": {"QUALIFICATION_NOTE"},
        }
        return_item = one("NAVIGATION_RETURN")
        if (
            not role_contract(expected)
            or one("REFLEXIVE_CONCEPT_QUESTION")["parentItemId"] != root_id
            or one("SELF_POSITIONING_QUESTION")["parentItemId"] != one("REFLEXIVE_CONCEPT_QUESTION")["itemId"]
            or return_item["parentItemId"] != one("SELF_POSITIONING_QUESTION")["itemId"]
            or one("RETURN_BOUNDARY")["parentItemId"] != return_item["itemId"]
            or len(returns) != 1
            or len(navigation_items) != 1
            or return_item["navigationTargetItemId"] != root_id
            or any(count > 1 for count in children.values())
        ):
            raise ValueError("REFLEXIVE_RETURN_TOPOLOGY")
    elif strategy == "EVIDENCE_GAP_TREE":
        expected = {
            "ROOT_INQUIRY": {"INQUIRY_OPERATION"},
            "SUPPORTED_BRANCH": {"INQUIRY_OPERATION"},
            "UNRESOLVED_BRANCH": {"INQUIRY_OPERATION"},
            "SUPPORTED_CONCEPT": {"SEMANTIC_NODE_REFERENCE"},
            "SUPPORTED_EVIDENCE": {"EVIDENCE_NOTE"},
            "FIRST_CLASS_EVIDENCE_GAP": {"EVIDENCE_GAP_NOTE"},
        }
        supported = one("SUPPORTED_BRANCH")
        unresolved = one("UNRESOLVED_BRANCH")
        gap = one("FIRST_CLASS_EVIDENCE_GAP")
        if (
            not role_contract(expected)
            or supported["parentItemId"] != root_id
            or unresolved["parentItemId"] != root_id
            or supported["branchStatus"] != "SUPPORTED"
            or unresolved["branchStatus"] != "UNRESOLVED"
            or one("SUPPORTED_CONCEPT")["parentItemId"] != supported["itemId"]
            or one("SUPPORTED_EVIDENCE")["parentItemId"] != one("SUPPORTED_CONCEPT")["itemId"]
            or gap["parentItemId"] != unresolved["itemId"]
            or gap["branchStatus"] != "UNRESOLVED"
            or not gap["gapRefs"]
            or len(gaps) != 1
        ):
            raise ValueError("EVIDENCE_GAP_TREE_TOPOLOGY")


def topology_signature(items: list[dict[str, Any]]) -> str:
    by_id = {item["itemId"]: index for index, item in enumerate(items)}
    rows = []
    for item in items:
        rows.append(
            "|".join(
                [
                    item["itemKind"],
                    str(by_id[item["parentItemId"]]) if item["parentItemId"] is not None else "ROOT",
                    str(item["depth"]),
                    item["branchStatus"],
                    ",".join(str(by_id[source]) for source in item["convergenceSourceItemIds"]),
                    str(by_id[item["navigationTargetItemId"]]) if item["navigationTargetItemId"] is not None else "",
                ]
            )
        )
    return ";".join(rows)


def assert_no_duplicate_topologies(fixtures: dict[str, list[dict[str, Any]]]) -> None:
    signatures: dict[str, list[str]] = defaultdict(list)
    for strategy, items in fixtures.items():
        validate_tree(strategy, items)
        signatures[topology_signature(items)].append(strategy)
    duplicates = [values for values in signatures.values() if len(values) > 1]
    if duplicates:
        raise ValueError(f"DUPLICATE_TREE_TOPOLOGY:{duplicates}")
