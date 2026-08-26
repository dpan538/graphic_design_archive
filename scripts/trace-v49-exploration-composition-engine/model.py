"""Normative TRACE v49 Round 15 bounded-composition engine.

The engine composes frozen Round 14 generic associations. It never infers a
typed, causal, directional, hierarchical, temporal, or quantitative relation.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


METHOD_VERSION = "trace-evidence-governed-composition-v1"
ARBITRATION_METHOD = "PARETO_MINIMAL_SUFFICIENT_V1"
ARBITRATION_VERSION = "1"
SEMANTIC_VERSION = "bounded-semantic-image-v1"
MAX_NODE_COUNT = 8
MAX_ADMITTED_DEGREE = 2
TOPOLOGIES = (
    "LINEAR_PATH",
    "BINARY_FORK",
    "BINARY_CONVERGENCE",
    "QUALIFIED_PATH",
    "REFLEXIVE_RETURN",
    "EVIDENCE_GAP_TREE",
)
SEMANTIC_STATES = (
    "ADMITTED",
    "PRUNED",
    "SPLIT_BOUNDARY",
    "EVIDENCE_GAP",
    "UNRESOLVED",
    "INELIGIBLE_CONTROL",
)
STRENGTH_RANK = {"WEAK": 0, "MODERATE": 1, "STRONG": 2}
CONFIDENCE_RANK = {"LOW": 0, "MODERATE": 1, "HIGH": 2}


@dataclass(frozen=True)
class FrozenInput:
    package: dict[str, Any]
    assessments: dict[str, dict[str, Any]]
    provenance: dict[str, tuple[dict[str, str], ...]]


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def pair_key(a: str, b: str) -> str:
    return "|".join(sorted((a, b)))


def load_frozen_input(repo: Path) -> FrozenInput:
    package_path = repo / "scripts/trace-v49-exploration-association-calibration/fixtures/association-assessments-v1.json"
    provenance_path = repo / "docs/audits/v49-exploration-association-calibration-round1/raw/evidence-provenance.tsv"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    assessments = {item["assessmentId"]: item for item in package["assessments"]}
    provenance: dict[str, list[dict[str, str]]] = defaultdict(list)
    with provenance_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            provenance[row["assessment_id"]].append(row)
    return FrozenInput(package, assessments, {key: tuple(value) for key, value in provenance.items()})


def _adjacency(nodes: Iterable[str], assessments: Iterable[dict[str, Any]]) -> dict[str, set[str]]:
    graph = {node: set() for node in nodes}
    for item in assessments:
        a, b = item["nodeA"], item["nodeB"]
        if a in graph and b in graph and a != b:
            graph[a].add(b)
            graph[b].add(a)
    return graph


def _distances(graph: dict[str, set[str]], seeds: list[str]) -> dict[str, int]:
    distance = {seed: 0 for seed in seeds}
    queue = deque(seeds)
    while queue:
        node = queue.popleft()
        for neighbour in sorted(graph[node]):
            if neighbour not in distance:
                distance[neighbour] = distance[node] + 1
                queue.append(neighbour)
    return distance


def _components(nodes: Iterable[str], assessment_ids: Iterable[str], assessments: dict[str, dict[str, Any]]) -> list[list[str]]:
    node_set = set(nodes)
    graph = {node: set() for node in node_set}
    for association_id in assessment_ids:
        item = assessments[association_id]
        a, b = item["nodeA"], item["nodeB"]
        if a in graph and b in graph:
            graph[a].add(b)
            graph[b].add(a)
    result: list[list[str]] = []
    unseen = set(node_set)
    while unseen:
        start = min(unseen)
        queue = [start]
        component: set[str] = set()
        while queue:
            node = queue.pop()
            if node in component:
                continue
            component.add(node)
            queue.extend(sorted(graph[node] - component, reverse=True))
        unseen -= component
        result.append(sorted(component))
    return sorted(result, key=lambda value: (value[0], len(value)))


def _evidence_vector(item: dict[str, Any]) -> tuple[int, ...]:
    dimensions = item["rubricDimensions"]
    return (
        STRENGTH_RANK[item["associationStrength"]],
        CONFIDENCE_RANK[item["evidenceConfidence"]],
        dimensions["D1"], dimensions["D5"], dimensions["D7"],
        dimensions["D2"], dimensions["D6"], dimensions["D4"], dimensions["D3"],
    )


def _admit(
    eligible: list[dict[str, Any]],
) -> tuple[set[str], dict[str, tuple[str, str, str]]]:
    """Admit by strict ordinal evidence groups without identity tie-breaking."""
    by_vector: dict[tuple[int, ...], list[dict[str, Any]]] = defaultdict(list)
    for item in eligible:
        by_vector[_evidence_vector(item)].append(item)
    admitted: set[str] = set()
    degree: Counter[str] = Counter()
    decisions: dict[str, tuple[str, str, str]] = {}
    capacity_blocked = False
    for vector in sorted(by_vector, reverse=True):
        group = sorted(by_vector[vector], key=lambda item: item["assessmentId"])
        if capacity_blocked:
            for item in group:
                decisions[item["assessmentId"]] = (
                    "PRUNED",
                    "BOUND_SATISFIED_BY_STRICTLY_STRONGER_EVIDENCE",
                    "Qualified association was not admitted because strictly stronger ordinal evidence already filled the topology-bounded neighbourhood; this is not historical rejection.",
                )
            continue
        proposed_degree = degree.copy()
        for item in group:
            proposed_degree[item["nodeA"]] += 1
            proposed_degree[item["nodeB"]] += 1
        if all(value <= MAX_ADMITTED_DEGREE for value in proposed_degree.values()):
            for item in group:
                admitted.add(item["assessmentId"])
                degree[item["nodeA"]] += 1
                degree[item["nodeB"]] += 1
                decisions[item["assessmentId"]] = (
                    "ADMITTED",
                    "QUALIFIED_WITHIN_TOPOLOGY_BOUND",
                    "Qualified association was admitted because its ordinal evidence group fits the topology-derived degree bound.",
                )
            continue
        individually_possible = [
            item for item in group
            if degree[item["nodeA"]] < MAX_ADMITTED_DEGREE and degree[item["nodeB"]] < MAX_ADMITTED_DEGREE
        ]
        for item in group:
            if item in individually_possible:
                decisions[item["assessmentId"]] = (
                    "UNRESOLVED",
                    "EQUAL_EVIDENCE_CAPACITY_TIE",
                    "Qualified association shares the cutoff evidence vector with competing candidates; identity order is forbidden as a historical tie-break, so admission remains unresolved.",
                )
            else:
                decisions[item["assessmentId"]] = (
                    "PRUNED",
                    "TOPOLOGY_DEGREE_BOUND",
                    "Qualified association was not admitted because the topology-derived local degree bound was already reached; this is not historical rejection.",
                )
        capacity_blocked = True
    return admitted, decisions


def _linear_shape(nodes: list[str], admitted: set[str], assessments: dict[str, dict[str, Any]]) -> bool:
    used = {node for association_id in admitted for node in (assessments[association_id]["nodeA"], assessments[association_id]["nodeB"])}
    if not used:
        return len(nodes) == 1
    components = _components(used, admitted, assessments)
    degree: Counter[str] = Counter()
    for association_id in admitted:
        item = assessments[association_id]
        degree[item["nodeA"]] += 1
        degree[item["nodeB"]] += 1
    return len(components) == 1 and len(admitted) == len(used) - 1 and max(degree.values(), default=0) <= 2


def _topology(
    fixture: dict[str, Any], admitted: set[str], assessments: dict[str, dict[str, Any]],
) -> tuple[str, list[str], str, str]:
    request = fixture["topologyRequest"]
    nodes = sorted(set(fixture["nodeIds"]))
    gaps = sorted(set(fixture["evidenceGapNodeIds"]))
    used = {node for association_id in admitted for node in (assessments[association_id]["nodeA"], assessments[association_id]["nodeB"])}
    degree: Counter[str] = Counter()
    for association_id in admitted:
        item = assessments[association_id]
        degree[item["nodeA"]] += 1
        degree[item["nodeB"]] += 1
    linear = _linear_shape(nodes, admitted, assessments)
    binary = len(used) == 3 and max(degree.values(), default=0) == 2
    candidates: list[str] = []
    if linear:
        candidates.append("LINEAR_PATH")
    if binary:
        candidates.extend(["BINARY_FORK", "BINARY_CONVERGENCE"])
    if fixture["qualificationGate"] and linear:
        candidates.append("QUALIFIED_PATH")
    if fixture["navigationReturn"] and admitted:
        candidates.append("REFLEXIVE_RETURN")
    if gaps:
        candidates.append("EVIDENCE_GAP_TREE")
    candidates = sorted(set(candidates), key=lambda value: TOPOLOGIES.index(value))
    if request != "AUTO":
        if request not in TOPOLOGIES:
            raise ValueError("UNKNOWN_TOPOLOGY_REQUEST")
        conditions = {
            "LINEAR_PATH": linear,
            "BINARY_FORK": binary,
            "BINARY_CONVERGENCE": binary,
            "QUALIFIED_PATH": fixture["qualificationGate"] and linear,
            "REFLEXIVE_RETURN": bool(fixture["navigationReturn"] and admitted),
            "EVIDENCE_GAP_TREE": bool(gaps),
        }
        if not conditions[request]:
            raise ValueError(f"INVALID_TOPOLOGY_CONFIGURATION:{request}")
        return request, candidates or [request], "EXPLICIT_INQUIRY_TOPOLOGY", "Topology follows an explicit inquiry-structure request and makes no historical directional claim."
    if len(candidates) == 1:
        return candidates[0], candidates, "UNAMBIGUOUS_STRUCTURAL_ENTRY", "Exactly one topology satisfies the declared structural entry conditions."
    return (
        "UNRESOLVED", candidates, "MULTIPLE_VALID_TOPOLOGIES" if candidates else "NO_VALID_TOPOLOGY",
        "Multiple semantically non-equivalent topology presentations remain valid; implementation order is not used to select one." if candidates else "No topology satisfies the bounded structural entry conditions; no historical absence is asserted.",
    )


def _presentation_hints(
    fixture: dict[str, Any], semantic_core: dict[str, Any], assessments: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    seed = fixture["visualSeed"]
    nodes = semantic_core["node_ids"]
    positions: list[dict[str, Any]] = []
    rotation = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) % 360
    for index, node in enumerate(nodes):
        token = int(hashlib.sha256(f"{seed}|{node}".encode()).hexdigest()[:8], 16)
        angle = math.radians(rotation + (360 * index / max(1, len(nodes))))
        radius = 215 + (token % 5 - 2)
        positions.append({
            "node_id": node,
            "x": round(360 + math.cos(angle) * radius),
            "y": round(270 + math.sin(angle) * radius),
            "layout_role": "SEED" if node in semantic_core["seed_node_ids"] else "PEER",
            "relative_layer": 0,
            "branch_slot": index,
            "node_radius": 16,
        })
    edges = []
    for association_id in semantic_core["admitted_association_ids"]:
        item = assessments[association_id]
        edges.append({
            "association_id": association_id,
            "source_node_id": min(item["nodeA"], item["nodeB"]),
            "target_node_id": max(item["nodeA"], item["nodeB"]),
            "stroke_width": 2,
            "arrowhead": False,
            "support_class_label": item["evidenceStatus"],
        })
    return {
        "layout_engine": "DETERMINISTIC_RESEARCH_CIRCLE_V1",
        "optional_seed": seed,
        "node_positions": positions,
        "edge_hints": edges,
        "visual_gap_hint": bool(semantic_core["evidence_gap_node_ids"]),
        "cosmetic_order": nodes,
        "semantic_mutation_permitted": False,
    }


def compose(fixture: dict[str, Any], frozen: FrozenInput) -> dict[str, Any]:
    required = {
        "fixtureId", "fixtureFamily", "seedNodeIds", "nodeIds", "associationIds",
        "topologyRequest", "evidenceGapNodeIds", "qualificationGate",
        "navigationReturn", "synthetic", "visualSeed", "description",
    }
    if set(fixture) != required:
        raise ValueError("FIXTURE_FIELD_CONTRACT")
    node_ids = sorted(set(fixture["nodeIds"]))
    seed_ids = sorted(set(fixture["seedNodeIds"]))
    association_ids = sorted(set(fixture["associationIds"]))
    if not seed_ids or not set(seed_ids) <= set(node_ids) or len(node_ids) > MAX_NODE_COUNT:
        raise ValueError("BOUNDED_NODE_CONTRACT")
    if any(association_id not in frozen.assessments for association_id in association_ids):
        raise ValueError("UNKNOWN_FROZEN_ASSOCIATION")
    inputs = [frozen.assessments[association_id] for association_id in association_ids]
    if any(item["nodeA"] not in node_ids or item["nodeB"] not in node_ids for item in inputs):
        raise ValueError("ASSOCIATION_NODE_BINDING")

    eligible = [item for item in inputs if item["activeForProximity"]]
    controls = [item for item in inputs if not item["activeForProximity"]]
    eligible_graph = _adjacency(node_ids, eligible)
    distance = _distances(eligible_graph, seed_ids)
    admitted, decisions = _admit(eligible)
    candidate_records: list[dict[str, Any]] = []
    for item in sorted(inputs, key=lambda value: value["assessmentId"]):
        association_id = item["assessmentId"]
        endpoint_distance = min(distance.get(item["nodeA"], 99), distance.get(item["nodeB"], 99))
        neighbourhood_role = "DIRECT_NEIGHBOUR" if endpoint_distance == 0 else "SKIP_ONE_NEIGHBOUR" if endpoint_distance == 1 else "OUTSIDE_BOUNDED_NEIGHBOURHOOD"
        if item["activeForProximity"]:
            state, reason_code, explanation = decisions[association_id]
            semantic_eligibility = "QUALIFIED"
            composition_eligibility = "ELIGIBLE_DIRECT" if neighbourhood_role == "DIRECT_NEIGHBOUR" else "ELIGIBLE_SKIP_ONE"
        else:
            state, reason_code = "INELIGIBLE_CONTROL", "ROUND14_ASSOCIATION_NOT_QUALIFIED"
            explanation = "Frozen Round 14 association did not qualify; composition cannot admit it and its presence does not change the semantic result."
            semantic_eligibility, composition_eligibility = "NOT_QUALIFIED", "INELIGIBLE"
        candidate_records.append({
            "assessment_id": association_id,
            "node_ids": sorted([item["nodeA"], item["nodeB"]]),
            "semantic_eligibility": semantic_eligibility,
            "composition_eligibility": composition_eligibility,
            "neighbourhood_role": neighbourhood_role,
            "topology_role": "SEMANTIC_CONNECTION" if state == "ADMITTED" else "COMPOSITION_BOUNDARY",
            "presentation_role": state,
            "decision_state": state,
            "reason_code": reason_code,
            "explanation": explanation,
        })

    qualified_ids = sorted(item["assessmentId"] for item in eligible)
    admitted_ids = sorted(admitted)
    active_nodes = sorted({node for association_id in qualified_ids for node in (
        frozen.assessments[association_id]["nodeA"], frozen.assessments[association_id]["nodeB"],
    )} | set(fixture["evidenceGapNodeIds"]))
    split_components = _components(active_nodes, admitted_ids, frozen.assessments) if active_nodes else []
    split_count = max(0, len(split_components) - 1)
    topology_type, topology_candidates, topology_reason_code, topology_explanation = _topology(fixture, admitted, frozen.assessments)

    association_states = [
        {"assessment_id": item["assessment_id"], "state": item["decision_state"], "reason_code": item["reason_code"]}
        for item in candidate_records if item["semantic_eligibility"] == "QUALIFIED"
    ]
    for index in range(split_count):
        association_states.append({"assessment_id": f"SPLIT-{index + 1}", "state": "SPLIT_BOUNDARY", "reason_code": "NO_QUALIFIED_BRIDGE_IN_INPUT"})
    for node in sorted(set(fixture["evidenceGapNodeIds"])):
        association_states.append({"assessment_id": f"GAP-{node}", "state": "EVIDENCE_GAP", "reason_code": "EXPLICIT_UNRESOLVED_EVIDENCE"})
    if topology_type == "UNRESOLVED":
        association_states.append({"assessment_id": "TOPOLOGY", "state": "UNRESOLVED", "reason_code": topology_reason_code})

    semantic_core = {
        "semantic_image_id": f"R15-IMAGE-{fixture['fixtureId'].removeprefix('R15-COMP-')}",
        "seed_node_ids": seed_ids,
        "node_ids": node_ids,
        "qualified_association_ids": qualified_ids,
        "admitted_association_ids": admitted_ids,
        "association_states": sorted(association_states, key=lambda value: (value["assessment_id"], value["state"])),
        "topology_type": topology_type,
        "topology_candidates": topology_candidates,
        "neighbourhood_depth": 2,
        "evidence_gap_node_ids": sorted(set(fixture["evidenceGapNodeIds"])),
        "split_components": split_components,
        "semantic_version": SEMANTIC_VERSION,
    }
    evidence_core = []
    for association_id in qualified_ids:
        item = frozen.assessments[association_id]
        rows = frozen.provenance[association_id]
        evidence_core.append({
            "assessment_id": association_id,
            "support_status": item["evidenceStatus"],
            "strength": item["associationStrength"],
            "confidence": item["evidenceConfidence"],
            "mandatory_dimension_results": {key: item["rubricDimensions"][key] for key in ("D1", "D5", "D7")},
            "provenance_refs": sorted(row["evidence_id"] for row in rows),
            "qualification": item["qualification"],
        })
    pruning_codes = sorted({item["reason_code"] for item in candidate_records if item["decision_state"] == "PRUNED"})
    composition_core = {
        "candidate_count": len(inputs),
        "admitted_count": len(admitted_ids),
        "pruned_count": sum(item["decision_state"] == "PRUNED" for item in candidate_records),
        "split_count": split_count,
        "evidence_gap_count": len(set(fixture["evidenceGapNodeIds"])),
        "unresolved_count": sum(item["decision_state"] == "UNRESOLVED" for item in candidate_records) + (topology_type == "UNRESOLVED"),
        "arbitration_method": ARBITRATION_METHOD,
        "arbitration_version": ARBITRATION_VERSION,
        "degree_bound": MAX_ADMITTED_DEGREE,
        "pruning_reason_codes": pruning_codes,
        "split_reason_codes": ["NO_QUALIFIED_BRIDGE_IN_INPUT"] if split_count else [],
        "topology_reason_code": topology_reason_code,
        "topology_explanation": topology_explanation,
        "candidate_decisions": candidate_records,
    }
    provenance = []
    for association_id in admitted_ids:
        rows = frozen.provenance[association_id]
        provenance.append({
            "assessment_id": association_id,
            "evidence_ids": sorted(row["evidence_id"] for row in rows),
            "source_ids": sorted({row["source_id"] for row in rows}),
            "source_urls": sorted({row["stable_url"] for row in rows}),
        })
    presentation_hints = _presentation_hints(fixture, semantic_core, frozen.assessments)
    audit = {
        "fixture_id": fixture["fixtureId"],
        "fixture_family": fixture["fixtureFamily"],
        "synthetic": fixture["synthetic"],
        "duplicate_input_count": len(fixture["associationIds"]) - len(association_ids),
        "failed_association_control_count": len(controls),
        "hard_negative_control_count": sum(item["hardNegative"] for item in controls),
        "unsupported_rendered_edge_count": 0,
        "typed_historical_relation_emission_count": 0,
        "causal_relation_emission_count": 0,
        "directional_relation_emission_count": 0,
        "negative_language_violation_count": 0,
        "explicit_non_claims": [
            "Association is not a typed historical relation.",
            "Topology and geometry are not historical facts.",
            "Pruning, split, and evidence-gap states are not negative historical evidence.",
        ],
    }
    image = {
        "schema_version": SEMANTIC_VERSION,
        "semantic_core": semantic_core,
        "evidence_core": evidence_core,
        "composition_core": composition_core,
        "presentation_hints": presentation_hints,
        "provenance": provenance,
        "audit": audit,
        "semantic_core_hash": canonical_hash(semantic_core),
        "presentation_hash": canonical_hash(presentation_hints),
    }
    validate_image(image, frozen)
    return image


def validate_image(image: dict[str, Any], frozen: FrozenInput) -> None:
    admitted = image["semantic_core"]["admitted_association_ids"]
    qualified = set(image["semantic_core"]["qualified_association_ids"])
    if not set(admitted) <= qualified:
        raise ValueError("ADMITTED_NOT_QUALIFIED")
    if any(not frozen.assessments[association_id]["activeForProximity"] for association_id in admitted):
        raise ValueError("FAILED_ASSOCIATION_LEAK")
    if canonical_hash(image["semantic_core"]) != image["semantic_core_hash"]:
        raise ValueError("SEMANTIC_HASH_MISMATCH")
    if canonical_hash(image["presentation_hints"]) != image["presentation_hash"]:
        raise ValueError("PRESENTATION_HASH_MISMATCH")
    provenance_ids = {item["assessment_id"] for item in image["provenance"]}
    if provenance_ids != set(admitted):
        raise ValueError("PROVENANCE_COMPLETENESS")
    if any(not item["evidence_ids"] or not item["source_ids"] or not item["source_urls"] for item in image["provenance"]):
        raise ValueError("PROVENANCE_CHAIN_INCOMPLETE")
    if any(item["arrowhead"] or item["stroke_width"] != 2 for item in image["presentation_hints"]["edge_hints"]):
        raise ValueError("VISUAL_SEMANTIC_LEAKAGE")
