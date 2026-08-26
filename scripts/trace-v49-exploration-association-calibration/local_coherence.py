"""Graph-distance validation and deterministic repair for Round 14."""

from __future__ import annotations

from collections import deque
from typing import Any


STRATEGIES = (
    "LINEAR_PATH",
    "BINARY_FORK",
    "BINARY_CONVERGENCE",
    "QUALIFIED_PATH",
    "REFLEXIVE_RETURN",
    "EVIDENCE_GAP_TREE",
)
MAX_ACTIVE_CONCEPT_NODES = 8


def pair_key(a: str, b: str) -> str:
    return "|".join(sorted((a, b)))


def adjacency(nodes: list[str], edges: list[tuple[str, str]]) -> dict[str, set[str]]:
    graph = {node: set() for node in nodes}
    for a, b in edges:
        if a == b or a not in graph or b not in graph:
            raise ValueError("INVALID_SEMANTIC_EDGE")
        graph[a].add(b)
        graph[b].add(a)
    return graph


def shortest_path(graph: dict[str, set[str]], start: str, end: str) -> list[str] | None:
    queue: deque[list[str]] = deque([[start]])
    seen = {start}
    while queue:
        path = queue.popleft()
        node = path[-1]
        if node == end:
            return path
        for neighbour in sorted(graph[node]):
            if neighbour not in seen:
                seen.add(neighbour)
                queue.append(path + [neighbour])
    return None


def local_pairs(nodes: list[str], edges: list[tuple[str, str]]) -> tuple[list[str], list[str]]:
    graph = adjacency(nodes, edges)
    direct: list[str] = []
    skip: list[str] = []
    for index, a in enumerate(nodes):
        for b in nodes[index + 1 :]:
            path = shortest_path(graph, a, b)
            if path and len(path) == 2:
                direct.append(pair_key(a, b))
            elif path and len(path) == 3:
                skip.append(pair_key(a, b))
    return sorted(direct), sorted(skip)


def components(nodes: list[str], edges: list[tuple[str, str]], removed: set[str] | None = None) -> list[list[str]]:
    removed = removed or set()
    remaining = [node for node in nodes if node not in removed]
    graph = adjacency(remaining, [(a, b) for a, b in edges if a not in removed and b not in removed])
    result: list[list[str]] = []
    unseen = set(remaining)
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
    return sorted(result, key=lambda item: (item[0], len(item)))


def validate_local_composition(fixture: dict[str, Any], decisions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    strategy = fixture["strategy"]
    if strategy not in STRATEGIES:
        raise ValueError("UNKNOWN_TREE_STRATEGY")
    nodes = fixture["nodes"]
    edges = [tuple(edge) for edge in fixture["semanticEdges"]]
    if len(nodes) > MAX_ACTIVE_CONCEPT_NODES:
        return {
            "result": "REJECT_COMPLEXITY_LIMIT",
            "directPairs": [],
            "skipOnePairs": [],
            "failedDirectPairs": [],
            "failedSkipOnePairs": [],
            "prunedNodes": [],
            "prunedBranches": 0,
            "components": [],
        }
    direct, skip = local_pairs(nodes, edges)
    bindings = fixture["pairBindings"]
    expected_keys = set(direct + skip)
    if set(bindings) != expected_keys:
        raise ValueError("LOCAL_PAIR_BINDING_COVERAGE")
    for key, assessment_id in bindings.items():
        decision = decisions[assessment_id]
        if pair_key(decision["nodeA"], decision["nodeB"]) != key:
            raise ValueError("LOCAL_PAIR_NODE_BINDING_MISMATCH")
    failed_direct = [key for key in direct if not decisions[bindings[key]]["directNeighbourPass"]]
    failed_skip = [key for key in skip if not decisions[bindings[key]]["skipOnePass"]]
    if not failed_direct and not failed_skip:
        return {
            "result": "PASS",
            "directPairs": direct,
            "skipOnePairs": skip,
            "failedDirectPairs": [],
            "failedSkipOnePairs": [],
            "prunedNodes": [],
            "prunedBranches": 0,
            "components": [sorted(nodes)],
        }

    graph = adjacency(nodes, edges)
    pruned: set[str] = set()
    retained_edges = set(pair_key(a, b) for a, b in edges)
    internal_failure = False
    for key in failed_direct:
        a, b = key.split("|")
        leaves = [node for node in (a, b) if len(graph[node]) == 1]
        if leaves:
            pruned.add(max(leaves))
        else:
            retained_edges.discard(key)
            internal_failure = True

    if failed_skip:
        interim_nodes = [node for node in nodes if node not in pruned]
        interim_edges = [tuple(key.split("|")) for key in sorted(retained_edges) if not set(key.split("|")) & pruned]
        interim_graph = adjacency(interim_nodes, interim_edges)
        for key in failed_skip:
            a, b = key.split("|")
            if a in pruned or b in pruned:
                continue
            path = shortest_path(interim_graph, a, b)
            if path and len(path) == 3:
                removed_edge = pair_key(path[1], path[2])
                retained_edges.discard(removed_edge)
                interim_graph[path[1]].discard(path[2])
                interim_graph[path[2]].discard(path[1])
                internal_failure = True

    final_edges = [tuple(key.split("|")) for key in sorted(retained_edges) if not set(key.split("|")) & pruned]
    final_components = components(nodes, final_edges, pruned)
    result = "SPLIT" if internal_failure and len(final_components) > 1 else "PRUNED"
    return {
        "result": result,
        "directPairs": direct,
        "skipOnePairs": skip,
        "failedDirectPairs": failed_direct,
        "failedSkipOnePairs": failed_skip,
        "prunedNodes": sorted(pruned),
        "prunedBranches": len(pruned),
        "components": final_components,
    }


def repair_boolean_graph(nodes: list[str], edges: list[tuple[str, str]], pair_pass: dict[str, bool]) -> dict[str, Any]:
    """Synthetic-only helper used to validate pruning behaviours without making historical claims."""
    direct, skip = local_pairs(nodes, edges)
    fixture = {
        "strategy": "LINEAR_PATH",
        "nodes": nodes,
        "semanticEdges": [list(edge) for edge in edges],
        "pairBindings": {key: key for key in direct + skip},
    }
    decisions = {
        key: {
            "nodeA": key.split("|")[0],
            "nodeB": key.split("|")[1],
            "directNeighbourPass": pair_pass[key],
            "skipOnePass": pair_pass[key],
        }
        for key in direct + skip
    }
    return validate_local_composition(fixture, decisions)
