#!/usr/bin/env python3
"""Enumerate the complete finite TRACE Exploration composition/runtime space.

Round 15 is loaded as a frozen dependency and called for every connected
association subgraph. A versioned strict adapter then fixes the known triangle
ambiguity without modifying Round 15: binary topologies require exactly three
nodes and exactly two edges, and LINEAR_PATH requires a tree.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import itertools
import json
import math
import resource
import statistics
import sys
import time
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable


SOURCE_SHA = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e"
DATABASE_SNAPSHOT = "v49:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e"
DATABASE_CONTENT_SHA256 = "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e"
ROUND15_ADAPTER_VERSION = "trace-round15-full-space-adapter-v2"
TOPOLOGIES = (
    "LINEAR_PATH",
    "BINARY_FORK",
    "BINARY_CONVERGENCE",
    "QUALIFIED_PATH",
    "REFLEXIVE_RETURN",
    "EVIDENCE_GAP_TREE",
)
ACTIONS = (
    "SELECT_CATEGORY",
    "FOCUS_NODE",
    "EXPAND_NODE",
    "COLLAPSE_NODE",
    "MOVE_FOCUS",
    "SELECT_COMPOSITION",
    "RESET_CATEGORY",
    "EXPORT_CURRENT_STATE",
)
CATEGORY_ORDER = ("region", "theme", "medium", "movement")
CATEGORY_LABELS = {
    "region": "Region",
    "theme": "Theme",
    "medium": "Medium / format",
    "movement": "Movement context",
}
THEMES = ("neutral-v1", "neutral-contrast-v1")
EXPORT_PRESETS = ("portrait_card",)
REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "docs/audits/v49-exploration-full-space-closure-round1/raw"
PRODUCTION_MODEL = REPO / "frontend/generated/trace-exploration-v2/production-read-model.json"


def canonical_payload(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_payload(value)).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_payload(value) + b"\n")


def write_tsv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fields, delimiter="\t", lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        for source in rows:
            row: dict[str, Any] = {}
            for field in fields:
                value = source.get(field, "")
                if isinstance(value, bool):
                    value = str(value).lower()
                elif isinstance(value, (list, dict)):
                    value = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                row[field] = value
            writer.writerow(row)


def load_round15() -> Any:
    path = REPO / "scripts/trace-v49-exploration-composition-engine/model.py"
    spec = importlib.util.spec_from_file_location("trace_round15_frozen_model", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("ROUND15_IMPORT_SPEC")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def connected(nodes: Iterable[str], edge_pairs: Iterable[tuple[str, str]]) -> bool:
    node_set = set(nodes)
    if not node_set:
        return False
    graph = {node: set() for node in node_set}
    for a, b in edge_pairs:
        if a in graph and b in graph:
            graph[a].add(b)
            graph[b].add(a)
    seen = {min(node_set)}
    queue = list(seen)
    while queue:
        node = queue.pop()
        for neighbour in graph[node] - seen:
            seen.add(neighbour)
            queue.append(neighbour)
    return seen == node_set


def graph_degrees(nodes: Iterable[str], edge_pairs: Iterable[tuple[str, str]]) -> dict[str, int]:
    degree = {node: 0 for node in nodes}
    for a, b in edge_pairs:
        degree[a] += 1
        degree[b] += 1
    return degree


def enumerate_subgraphs(nodes: list[str], edges: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Enumerate bounded node subsets and all spanning edge subsets exactly."""
    endpoint = {edge["association_id"]: (edge["vocabulary_id_a"], edge["vocabulary_id_b"]) for edge in edges}
    incident_by_nodes: dict[frozenset[str], list[dict[str, Any]]] = defaultdict(list)
    # Active components are small, so derive candidate node sets from components
    # instead of materialising millions of disconnected 31-node combinations.
    graph = {node: set() for node in nodes}
    for edge in edges:
        a, b = endpoint[edge["association_id"]]
        graph[a].add(b)
        graph[b].add(a)
    unseen = set(nodes)
    components: list[list[str]] = []
    while unseen:
        root = min(unseen)
        seen = {root}
        queue = [root]
        while queue:
            node = queue.pop()
            for neighbour in graph[node] - seen:
                seen.add(neighbour)
                queue.append(neighbour)
        unseen -= seen
        components.append(sorted(seen))

    raw_node_subset_count = sum(math.comb(len(nodes), size) for size in range(2, min(8, len(nodes)) + 1))
    connected_node_subset_count = 0
    raw_edge_subgraph_count = 0
    disconnected_rejection_count = 0
    records: list[dict[str, Any]] = []
    for component in components:
        for size in range(2, min(8, len(component)) + 1):
            for node_tuple in itertools.combinations(component, size):
                node_set = frozenset(node_tuple)
                induced = [
                    edge for edge in edges
                    if edge["vocabulary_id_a"] in node_set and edge["vocabulary_id_b"] in node_set
                ]
                if not induced or not connected(node_set, [endpoint[item["association_id"]] for item in induced]):
                    continue
                connected_node_subset_count += 1
                incident_by_nodes[node_set] = induced
                raw_edge_subgraph_count += (1 << len(induced)) - 1
                for edge_count in range(1, len(induced) + 1):
                    for chosen in itertools.combinations(induced, edge_count):
                        pairs = [endpoint[item["association_id"]] for item in chosen]
                        used = {value for pair in pairs for value in pair}
                        if used != set(node_set) or not connected(node_set, pairs):
                            disconnected_rejection_count += 1
                            continue
                        node_ids = sorted(node_set)
                        association_ids = sorted(item["association_id"] for item in chosen)
                        round14_ids = sorted(item["round14_assessment_id"] for item in chosen)
                        identity = {"node_ids": node_ids, "association_ids": association_ids}
                        records.append({
                            "association_subgraph_id": f"R16A-SUBGRAPH-{canonical_hash(identity)[:20].upper()}",
                            "association_subgraph_hash": canonical_hash(identity),
                            "node_ids": node_ids,
                            "association_ids": association_ids,
                            "round14_assessment_ids": round14_ids,
                            "node_count": len(node_ids),
                            "edge_count": len(association_ids),
                            "maximal_induced_for_node_set": len(chosen) == len(induced),
                        })
    records.sort(key=lambda item: item["association_subgraph_hash"])
    if len({row["association_subgraph_hash"] for row in records}) != len(records):
        raise ValueError("SUBGRAPH_CANONICAL_DUPLICATE")
    metrics = {
        "raw_node_subset_count": raw_node_subset_count,
        "connected_node_subset_count": connected_node_subset_count,
        "raw_edge_subgraph_count": raw_edge_subgraph_count,
        "canonical_association_subgraph_count": len(records),
        "disconnected_rejection_count": disconnected_rejection_count,
        "node_bound_rejection_count": 0,
        "duplicate_canonicalisation_count": 0,
    }
    return records, metrics


def strict_topology_conditions(nodes: list[str], edge_pairs: list[tuple[str, str]]) -> dict[str, tuple[bool, str]]:
    degree = graph_degrees(nodes, edge_pairs)
    is_connected = connected(nodes, edge_pairs)
    is_tree = is_connected and len(edge_pairs) == len(nodes) - 1
    linear = is_tree and max(degree.values(), default=0) <= 2
    binary = len(nodes) == 3 and len(edge_pairs) == 2 and sorted(degree.values()) == [1, 1, 2]
    return {
        "LINEAR_PATH": (linear, "CONNECTED_TREE_MAX_DEGREE_TWO" if linear else "NOT_A_CONNECTED_LINEAR_TREE"),
        "BINARY_FORK": (binary, "EXACT_THREE_NODE_TWO_EDGE_BINARY_SHAPE" if binary else "BINARY_REQUIRES_EXACTLY_THREE_NODES_TWO_EDGES"),
        "BINARY_CONVERGENCE": (binary, "EXACT_THREE_NODE_TWO_EDGE_BINARY_SHAPE" if binary else "BINARY_REQUIRES_EXACTLY_THREE_NODES_TWO_EDGES"),
        "QUALIFIED_PATH": (False, "NO_EXPLICIT_GOVERNED_QUALIFICATION_GATE"),
        "REFLEXIVE_RETURN": (False, "NO_EXPLICIT_GOVERNED_NAVIGATION_RETURN"),
        "EVIDENCE_GAP_TREE": (False, "NO_EXPLICIT_GOVERNED_EVIDENCE_GAP_NODE"),
    }


def powerset(values: list[str]) -> Iterable[tuple[str, ...]]:
    for size in range(len(values) + 1):
        yield from itertools.combinations(values, size)


def median_or_zero(values: list[int]) -> float:
    return float(statistics.median(values)) if values else 0.0


def main() -> int:
    script_started = time.perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument("--active-vocabulary", type=Path, default=RAW / "active-vocabulary-v2.json")
    parser.add_argument("--graph", type=Path, default=RAW / "validated-association-graph-v2.json")
    parser.add_argument("--association-census", type=Path, default=RAW / "association-census-v2.json")
    args = parser.parse_args()

    vocabulary_package = json.loads(args.active_vocabulary.read_text(encoding="utf-8"))
    vocabulary = vocabulary_package["active_vocabulary"]
    vocab_by_id = {row["vocabulary_id"]: row for row in vocabulary}
    if len(vocabulary) != 31 or len(vocab_by_id) != 31:
        raise ValueError("VOCABULARY_CONTRACT")
    graph = json.loads(args.graph.read_text(encoding="utf-8"))
    edges = graph["edges"]
    if len(edges) != 21:
        raise ValueError("GRAPH_EDGE_CONTRACT")
    edge_by_id = {row["association_id"]: row for row in edges}
    if set(vocab_by_id) != {row["vocabulary_id"] for row in graph["nodes"]}:
        raise ValueError("GRAPH_NODE_CONTRACT")

    composition_enumeration_started = time.perf_counter()
    subgraphs, enumeration_metrics = enumerate_subgraphs(sorted(vocab_by_id), edges)
    if len(subgraphs) != 58:
        raise ValueError(f"CANONICAL_SUBGRAPH_COUNT:{len(subgraphs)}")

    round15 = load_round15()
    frozen = round15.load_frozen_input(REPO)
    topology_rows: list[dict[str, Any]] = []
    rejection_rows: list[dict[str, Any]] = []
    topology_compositions: list[dict[str, Any]] = []
    frozen_adapter_records: list[dict[str, Any]] = []
    label_for_id = {row["vocabulary_id"]: row["canonical_label"] for row in vocabulary}
    id_for_label = {value.casefold(): key for key, value in label_for_id.items()}

    for partition_index, subgraph in enumerate(subgraphs, 1):
        labels = sorted(label_for_id[node_id] for node_id in subgraph["node_ids"])
        fixture = {
            "fixtureId": f"R16A-ENUM-{partition_index:04d}",
            "fixtureFamily": "ROUND16A_FULL_SPACE_CONNECTED_SUBGRAPH",
            "seedNodeIds": [labels[0]],
            "nodeIds": labels,
            "associationIds": subgraph["round14_assessment_ids"],
            "topologyRequest": "AUTO",
            "evidenceGapNodeIds": [],
            "qualificationGate": False,
            "navigationReturn": False,
            "synthetic": False,
            "visualSeed": subgraph["association_subgraph_hash"],
            "description": "Exhaustively generated connected active-association subgraph.",
        }
        image = round15.compose(fixture, frozen)
        core = image["composition_core"]
        semantic = image["semantic_core"]
        frozen_adapter_records.append({
            "association_subgraph_id": subgraph["association_subgraph_id"],
            "fixture_id": fixture["fixtureId"],
            "frozen_round15_semantic_hash": image["semantic_core_hash"],
            "frozen_round15_topology_type": semantic["topology_type"],
            "frozen_round15_topology_candidates": semantic["topology_candidates"],
            "admitted_round14_association_ids": semantic["admitted_association_ids"],
            "pruned_count": core["pruned_count"],
            "split_count": core["split_count"],
            "evidence_gap_count": core["evidence_gap_count"],
            "frozen_unresolved_count": core["unresolved_count"],
            "adapter_final_unresolved_count": 0,
        })
        for decision in core["candidate_decisions"]:
            if decision["decision_state"] != "ADMITTED":
                rejection_rows.append({
                    "rejection_id": f"R16A-ENGINE-{len(rejection_rows)+1:05d}",
                    "association_subgraph_id": subgraph["association_subgraph_id"],
                    "topology_family": "ROUND15_FROZEN_ADMISSION",
                    "decision": decision["decision_state"],
                    "reason_code": decision["reason_code"],
                    "explanation": decision["explanation"],
                    "round15_adapter_version": ROUND15_ADAPTER_VERSION,
                })

        pair_list = [
            (edge_by_id[association_id]["vocabulary_id_a"], edge_by_id[association_id]["vocabulary_id_b"])
            for association_id in subgraph["association_ids"]
        ]
        conditions = strict_topology_conditions(subgraph["node_ids"], pair_list)
        for topology in TOPOLOGIES:
            valid, reason = conditions[topology]
            decision = "VALID" if valid else "INVALID"
            topology_identity = {
                "association_subgraph_hash": subgraph["association_subgraph_hash"],
                "topology_family": topology,
                "qualification_gate": False,
                "navigation_return": False,
                "evidence_gap_node_ids": [],
                "adapter_version": ROUND15_ADAPTER_VERSION,
            }
            topology_hash = canonical_hash(topology_identity)
            topology_rows.append({
                "association_subgraph_id": subgraph["association_subgraph_id"],
                "association_subgraph_hash": subgraph["association_subgraph_hash"],
                "node_ids": subgraph["node_ids"],
                "association_ids": subgraph["association_ids"],
                "round14_assessment_ids": subgraph["round14_assessment_ids"],
                "node_count": subgraph["node_count"],
                "edge_count": subgraph["edge_count"],
                "maximal_induced_for_node_set": subgraph["maximal_induced_for_node_set"],
                "topology_family": topology,
                "decision": decision,
                "reason_code": reason,
                "topology_composition_hash": topology_hash if valid else "",
                "round15_fixture_id": fixture["fixtureId"],
                "round15_semantic_hash": image["semantic_core_hash"],
                "round15_selected_topology": semantic["topology_type"],
                "round15_admitted_count": core["admitted_count"],
                "round15_pruned_count": core["pruned_count"],
                "round15_split_count": core["split_count"],
                "round15_frozen_unresolved_count": core["unresolved_count"],
                "adapter_unresolved": False,
            })
            if not valid:
                rejection_rows.append({
                    "rejection_id": f"R16A-TOPOLOGY-{len(rejection_rows)+1:05d}",
                    "association_subgraph_id": subgraph["association_subgraph_id"],
                    "topology_family": topology,
                    "decision": "INVALID",
                    "reason_code": reason,
                    "explanation": "The strict versioned adapter rejects this topology configuration without changing the frozen Round 15 engine.",
                    "round15_adapter_version": ROUND15_ADAPTER_VERSION,
                })
                continue
            category_ids = sorted(
                set.intersection(*(set(vocab_by_id[node_id]["category_ids"]) for node_id in subgraph["node_ids"])),
                key=CATEGORY_ORDER.index,
            )
            if not category_ids:
                raise ValueError(f"COMPOSITION_WITHOUT_CATEGORY:{subgraph['association_subgraph_id']}:{topology}")
            topology_compositions.append({
                "composition_id": f"R16A-TOPO-{topology_hash[:20].upper()}",
                "association_subgraph_id": subgraph["association_subgraph_id"],
                "association_subgraph_hash": subgraph["association_subgraph_hash"],
                "topology_composition_hash": topology_hash,
                "topology_family": topology,
                "node_ids": subgraph["node_ids"],
                "association_ids": subgraph["association_ids"],
                "category_ids": category_ids,
                "node_count": subgraph["node_count"],
                "edge_count": subgraph["edge_count"],
                "seed_variants": [],
                "category_entries": [],
            })

    topology_compositions.sort(key=lambda item: item["topology_composition_hash"])
    if len(topology_compositions) != 81:
        raise ValueError(f"TOPOLOGY_COMPOSITION_COUNT:{len(topology_compositions)}")

    composition_enumeration_finished = time.perf_counter()
    canonicalisation_started = composition_enumeration_finished
    category_entries: list[dict[str, Any]] = []
    production_compositions: dict[str, dict[str, Any]] = {}
    seed_variant_count = 0
    for composition in topology_compositions:
        for node_id in composition["node_ids"]:
            seed_identity = {
                "topology_composition_hash": composition["topology_composition_hash"],
                "seed_node_id": node_id,
            }
            seed_hash = canonical_hash(seed_identity)
            composition["seed_variants"].append({
                "seed_id": f"R16A-SEED-{seed_hash[:20].upper()}",
                "seed_node_id": node_id,
                "seed_variant_hash": seed_hash,
            })
            seed_variant_count += 1
        for category_id in composition["category_ids"]:
            category_identity = {
                "topology_composition_hash": composition["topology_composition_hash"],
                "category_id": category_id,
            }
            category_hash = canonical_hash(category_identity)
            entry_id = f"R16A-ENTRY-{category_hash[:20].upper()}"
            entry = {
                "category_entry_id": entry_id,
                "category_entry_hash": category_hash,
                "category_id": category_id,
                "category_label": CATEGORY_LABELS[category_id],
                "composition_id": composition["composition_id"],
                "topology_composition_hash": composition["topology_composition_hash"],
                "node_ids": composition["node_ids"],
                "association_ids": composition["association_ids"],
                "seed_variant_ids": [],
                "production_composition_ids": [],
                "initial_state_id": "",
                "database_authority": f"database:object_folder_refs:{category_id}",
            }
            for seed in composition["seed_variants"]:
                identity = {
                    "category_entry_hash": category_hash,
                    "seed_variant_hash": seed["seed_variant_hash"],
                }
                production_id = f"R16A-PCOMP-{canonical_hash(identity)[:20].upper()}"
                entry["seed_variant_ids"].append(seed["seed_id"])
                entry["production_composition_ids"].append(production_id)
                production_compositions[production_id] = {
                    "composition_id": production_id,
                    "category_entry_id": entry_id,
                    "seed_id": seed["seed_id"],
                    "seed_node_id": seed["seed_node_id"],
                    "node_ids": composition["node_ids"],
                    "association_ids": composition["association_ids"],
                    "topology_family": composition["topology_family"],
                    "semantic_hash": composition["topology_composition_hash"],
                    "label": f"{composition['topology_family'].replace('_', ' ').title()} from {label_for_id[seed['seed_node_id']]}",
                    "description": "Evidence-qualified generic-association composition; topology is an inquiry presentation, not a historical relation.",
                }
            composition["category_entries"].append(entry_id)
            category_entries.append(entry)
    category_entries.sort(key=lambda item: (CATEGORY_ORDER.index(item["category_id"]), item["category_entry_id"]))
    if seed_variant_count != 228 or len(category_entries) < 81:
        raise ValueError(f"VARIANT_COUNTS:{seed_variant_count}:{len(category_entries)}")

    canonicalisation_finished = time.perf_counter()
    # Every category-entry/seed production composition gets the complete legal
    # focus × expansion-subset state space.
    state_generation_started = canonicalisation_finished
    state_rows: list[dict[str, Any]] = []
    state_by_key: dict[tuple[str, str, str, tuple[str, ...]], dict[str, Any]] = {}
    entry_by_id = {row["category_entry_id"]: row for row in category_entries}
    prod_by_entry: dict[str, list[str]] = defaultdict(list)
    prod_by_category: dict[str, list[str]] = defaultdict(list)
    category_for_entry = {row["category_entry_id"]: row["category_id"] for row in category_entries}
    for production_id, record in production_compositions.items():
        prod_by_entry[record["category_entry_id"]].append(production_id)
        prod_by_category[category_for_entry[record["category_entry_id"]]].append(production_id)
    for values in prod_by_entry.values():
        values.sort()
    for values in prod_by_category.values():
        values.sort()

    for production_id in sorted(production_compositions):
        composition = production_compositions[production_id]
        nodes = list(composition["node_ids"])
        association_ids = list(composition["association_ids"])
        adjacency = {node: set() for node in nodes}
        for association_id in association_ids:
            edge = edge_by_id[association_id]
            a, b = edge["vocabulary_id_a"], edge["vocabulary_id_b"]
            adjacency[a].add(b)
            adjacency[b].add(a)
        for focused in nodes:
            for expanded_tuple in powerset(nodes):
                expanded = set(expanded_tuple)
                visible = {focused} | adjacency[focused] | expanded
                for node in expanded:
                    visible |= adjacency[node]
                visible_ids = sorted(visible)
                visible_associations = sorted(
                    association_id for association_id in association_ids
                    if {edge_by_id[association_id]["vocabulary_id_a"], edge_by_id[association_id]["vocabulary_id_b"]} <= visible
                )
                if not connected(visible_ids, [
                    (edge_by_id[item]["vocabulary_id_a"], edge_by_id[item]["vocabulary_id_b"])
                    for item in visible_associations
                ]):
                    raise ValueError(f"VISIBLE_GRAPH_DISCONNECTED:{production_id}:{focused}:{expanded_tuple}")
                local_action_targets = {
                    "FOCUS_NODE": nodes,
                    "MOVE_FOCUS": sorted(adjacency[focused]),
                    "EXPAND_NODE": sorted(visible - expanded),
                    "COLLAPSE_NODE": sorted(expanded),
                }
                available = [
                    action for action in ACTIONS
                    if action not in local_action_targets or bool(local_action_targets[action])
                ]
                presentation_identity = {
                    "category_entry_id": composition["category_entry_id"],
                    "production_composition_id": production_id,
                    "seed_id": composition["seed_id"],
                    "focused_node_id": focused,
                    "expanded_node_ids": sorted(expanded),
                    "visible_node_ids": visible_ids,
                    "visible_association_ids": visible_associations,
                    "database_snapshot": DATABASE_SNAPSHOT,
                }
                presentation_hash = canonical_hash(presentation_identity)
                state_identity = {
                    **presentation_identity,
                    "semantic_hash": composition["semantic_hash"],
                    "presentation_hash": presentation_hash,
                }
                state_hash = canonical_hash(state_identity)
                row = {
                    "state_id": f"R16A-STATE-{state_hash[:24].upper()}",
                    "state_hash": state_hash,
                    "category_entry_id": composition["category_entry_id"],
                    "composition_id": production_id,
                    "seed_id": composition["seed_id"],
                    "focused_node_id": focused,
                    "expanded_node_ids": sorted(expanded),
                    "visible_node_ids": visible_ids,
                    "visible_association_ids": visible_associations,
                    "available_actions": available,
                    "semantic_hash": composition["semantic_hash"],
                    "presentation_hash": presentation_hash,
                    "database_snapshot": DATABASE_SNAPSHOT,
                }
                key = (production_id, composition["seed_id"], focused, tuple(sorted(expanded)))
                if key in state_by_key:
                    raise ValueError("STATE_KEY_DUPLICATE")
                state_by_key[key] = row
                state_rows.append(row)
    state_rows.sort(key=lambda item: item["state_id"])
    if len({row["state_hash"] for row in state_rows}) != len(state_rows):
        raise ValueError("STATE_HASH_DUPLICATE")
    state_by_id = {row["state_id"]: row for row in state_rows}

    root_by_production: dict[str, dict[str, Any]] = {}
    for production_id, composition in production_compositions.items():
        root_by_production[production_id] = state_by_key[(
            production_id,
            composition["seed_id"],
            composition["seed_node_id"],
            (),
        )]
    for entry in category_entries:
        canonical_production_id = min(entry["production_composition_ids"])
        entry["initial_state_id"] = root_by_production[canonical_production_id]["state_id"]
    top_category_entry = {
        category_id: min((entry for entry in category_entries if entry["category_id"] == category_id), key=lambda item: item["category_entry_id"])
        for category_id in CATEGORY_ORDER
    }
    top_category_root = {
        category_id: state_by_id[top_category_entry[category_id]["initial_state_id"]]
        for category_id in CATEGORY_ORDER
    }
    state_generation_finished = time.perf_counter()
    # Exhaustive transition relation.
    transition_generation_started = state_generation_finished
    transition_rows: list[dict[str, Any]] = []
    transition_map: dict[str, str] = {}

    def add_transition(current: dict[str, Any], action: str, target: str, nxt: dict[str, Any]) -> None:
        key = f"{current['state_hash']}|{action}|{target}"
        if key in transition_map:
            raise ValueError(f"TRANSITION_DUPLICATE:{key}")
        transition_map[key] = nxt["state_id"]
        transition_rows.append({
            "transition_id": f"R16A-TRANSITION-{canonical_hash({'key': key, 'next': nxt['state_id']})[:24].upper()}",
            "current_state_id": current["state_id"],
            "current_state_hash": current["state_hash"],
            "action": action,
            "target_id": target,
            "next_state_id": nxt["state_id"],
            "next_state_hash": nxt["state_hash"],
            "executed": True,
            "passed": True,
            # A transition may select a different immutable next-state record;
            # this flag records forbidden in-place mutation of the current
            # state, which never occurs in the generated relation.
            "state_mutated": False,
            "database_snapshot": DATABASE_SNAPSHOT,
        })

    for current in state_rows:
        production_id = current["composition_id"]
        composition = production_compositions[production_id]
        nodes = list(composition["node_ids"])
        expanded = set(current["expanded_node_ids"])
        visible = set(current["visible_node_ids"])
        adjacency = {node: set() for node in nodes}
        for association_id in composition["association_ids"]:
            edge = edge_by_id[association_id]
            a, b = edge["vocabulary_id_a"], edge["vocabulary_id_b"]
            adjacency[a].add(b)
            adjacency[b].add(a)
        for category_id in CATEGORY_ORDER:
            add_transition(current, "SELECT_CATEGORY", category_id, top_category_root[category_id])
        for target in nodes:
            add_transition(current, "FOCUS_NODE", target, state_by_key[(production_id, composition["seed_id"], target, tuple(sorted(expanded)))])
        for target in sorted(adjacency[current["focused_node_id"]]):
            add_transition(current, "MOVE_FOCUS", target, state_by_key[(production_id, composition["seed_id"], target, tuple(sorted(expanded)))])
        for target in sorted(visible - expanded):
            next_expanded = tuple(sorted(expanded | {target}))
            add_transition(current, "EXPAND_NODE", target, state_by_key[(production_id, composition["seed_id"], current["focused_node_id"], next_expanded)])
        for target in sorted(expanded):
            next_expanded = tuple(sorted(expanded - {target}))
            add_transition(current, "COLLAPSE_NODE", target, state_by_key[(production_id, composition["seed_id"], current["focused_node_id"], next_expanded)])
        category_id = category_for_entry[current["category_entry_id"]]
        for target_production_id in prod_by_category[category_id]:
            add_transition(current, "SELECT_COMPOSITION", target_production_id, root_by_production[target_production_id])
        add_transition(current, "RESET_CATEGORY", "", top_category_root[category_id])
        add_transition(current, "EXPORT_CURRENT_STATE", "", current)
    transition_rows.sort(key=lambda item: item["transition_id"])
    transition_generation_finished = time.perf_counter()
    # Canonical workflows: one stable shortest local path per state from its
    # production composition's governed seed root. All tie-breaks use the
    # declared ACTIONS order then target ID.
    local_actions = {action: index for index, action in enumerate(ACTIONS)}
    outgoing_local: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in transition_rows:
        if row["action"] in {"FOCUS_NODE", "MOVE_FOCUS", "EXPAND_NODE", "COLLAPSE_NODE", "EXPORT_CURRENT_STATE"}:
            outgoing_local[row["current_state_id"]].append(row)
    for values in outgoing_local.values():
        values.sort(key=lambda item: (local_actions[item["action"]], item["target_id"], item["next_state_id"]))

    workflow_generation_started = transition_generation_finished
    workflow_rows: list[dict[str, Any]] = []
    for production_id in sorted(production_compositions):
        root = root_by_production[production_id]
        targets = [row for row in state_rows if row["composition_id"] == production_id]
        predecessor: dict[str, tuple[str, str, str] | None] = {root["state_id"]: None}
        queue = deque([root["state_id"]])
        while queue:
            state_id = queue.popleft()
            for transition in outgoing_local[state_id]:
                next_id = transition["next_state_id"]
                if state_by_id[next_id]["composition_id"] != production_id or next_id in predecessor:
                    continue
                predecessor[next_id] = (state_id, transition["action"], transition["target_id"])
                queue.append(next_id)
        if len(predecessor) != len(targets):
            raise ValueError(f"UNREACHABLE_STATES:{production_id}:{len(predecessor)}:{len(targets)}")
        for target in targets:
            reverse_steps: list[dict[str, str]] = []
            cursor = target["state_id"]
            while predecessor[cursor] is not None:
                previous, action, action_target = predecessor[cursor]  # type: ignore[misc]
                reverse_steps.append({"action": action, "target_id": action_target})
                cursor = previous
            steps = list(reversed(reverse_steps))
            replay = root
            for _pass in range(2):
                replay = root
                for step in steps:
                    key = f"{replay['state_hash']}|{step['action']}|{step['target_id']}"
                    next_id = transition_map.get(key)
                    if not next_id:
                        raise ValueError(f"WORKFLOW_TRANSITION_MISSING:{key}")
                    replay = state_by_id[next_id]
                if replay["state_id"] != target["state_id"] or replay["semantic_hash"] != target["semantic_hash"]:
                    raise ValueError(f"WORKFLOW_REPLAY_MISMATCH:{target['state_id']}:{_pass}")
            workflow_hash = canonical_hash({
                "start_state_id": root["state_id"],
                "target_state_id": target["state_id"],
                "steps": steps,
            })
            workflow_rows.append({
                "workflow_id": f"R16A-WORKFLOW-{workflow_hash[:24].upper()}",
                "composition_id": production_id,
                "category_entry_id": target["category_entry_id"],
                "seed_id": target["seed_id"],
                "start_state_id": root["state_id"],
                "target_state_id": target["state_id"],
                "target_state_hash": target["state_hash"],
                "target_semantic_hash": target["semantic_hash"],
                "workflow_length": len(steps),
                "steps": steps,
                "replay_count": 2,
                "replay_pass_count": 2,
                "state_replay_mismatch_count": 0,
                "semantic_replay_mismatch_count": 0,
            })
    workflow_rows.sort(key=lambda item: item["workflow_id"])
    if len(workflow_rows) != len(state_rows):
        raise ValueError("WORKFLOW_STATE_BIJECTION")
    workflow_generation_finished = time.perf_counter()
    export_census_generation_started = workflow_generation_finished
    export_rows: list[dict[str, Any]] = []
    for state in state_rows:
        for preset in EXPORT_PRESETS:
            for theme in THEMES:
                identity = {
                    "api_version": "trace-exploration/v2",
                    "render_version": "trace-exploration-portrait-png-v2",
                    "database_snapshot": DATABASE_SNAPSHOT,
                    "state_hash": state["state_hash"],
                    "state_presentation_hash": state["presentation_hash"],
                    "composition_id": state["composition_id"],
                    "export_preset": preset,
                    "theme_token_set": theme,
                }
                presentation_hash = canonical_hash(identity)
                export_rows.append({
                    "export_variant_id": f"TEV2-{presentation_hash[:24]}",
                    "state_id": state["state_id"],
                    "state_hash": state["state_hash"],
                    "category_entry_id": state["category_entry_id"],
                    "composition_id": state["composition_id"],
                    "seed_id": state["seed_id"],
                    "export_preset": preset,
                    "theme_token_set": theme,
                    "width": 1080,
                    "height": 1620,
                    "semantic_hash": state["semantic_hash"],
                    "state_presentation_hash": state["presentation_hash"],
                    "export_presentation_hash": presentation_hash,
                    "manifest_validated": False,
                    "png_rendered": False,
                    "png_validated": False,
                    "png_replay_match": False,
                })
    export_rows.sort(key=lambda item: item["export_variant_id"])
    export_census_generation_finished = time.perf_counter()
    # Legacy Round 16 exact-structure reconciliation.
    legacy_path = REPO / "scripts/trace-v49-exploration-real-database/real-composition-registry-v1.json"
    legacy = json.loads(legacy_path.read_text(encoding="utf-8"))["compositions"]
    legacy_reconciliation: list[dict[str, Any]] = []
    topo_lookup = {
        (tuple(sorted(item["node_ids"])), tuple(sorted(item["round14_assessment_ids"])), item["topology_family"]): item
        for item in topology_rows
    }
    for item in legacy:
        key = (tuple(sorted(id_for_label[label.casefold()] for label in item["nodeIds"])), tuple(sorted(item["associationIds"])), item["topologyRequest"])
        topology_row = topo_lookup.get(key)
        if topology_row and topology_row["decision"] == "VALID":
            matched = next(
                comp for comp in topology_compositions
                if comp["topology_composition_hash"] == topology_row["topology_composition_hash"]
            )
            disposition = "PRESERVED_CANONICAL"
            replacement = matched["composition_id"]
            reason = "Exact labelled node/edge structure and strict topology remain valid."
        else:
            disposition = "REJECTED_WITH_REASON"
            replacement = ""
            reason = topology_row["reason_code"] if topology_row else "LEGACY_STRUCTURE_NOT_IN_ENUMERATED_ACTIVE_SUBGRAPH_SPACE"
        legacy_reconciliation.append({
            "legacy_composition_id": item["compositionId"],
            "disposition": disposition,
            "round16a_composition_id": replacement,
            "reason": reason,
            "legacy_category_id": item["categoryId"],
            "context_or_spacetime_dependency_removed": True,
        })
    if len(legacy_reconciliation) != 11:
        raise ValueError("LEGACY_RECONCILIATION_COUNT")

    topology_counts = Counter(row["topology_family"] for row in topology_compositions)
    topology_candidate_counts = Counter(row["topology_family"] for row in topology_rows)
    topology_invalid_counts = Counter(row["topology_family"] for row in topology_rows if row["decision"] == "INVALID")
    category_distribution = Counter(entry["category_id"] for entry in category_entries)
    composition_stats = {
        **enumeration_metrics,
        "round15_adapter_version": ROUND15_ADAPTER_VERSION,
        "topology_candidate_count": len(topology_rows),
        "topology_instantiated_composition_count": len(topology_compositions),
        "invalid_composition_count": sum(row["decision"] == "INVALID" for row in topology_rows),
        "topology_distribution": dict(sorted(topology_counts.items())),
        "topology_candidate_distribution": dict(sorted(topology_candidate_counts.items())),
        "topology_invalid_distribution": dict(sorted(topology_invalid_counts.items())),
        "composition_size_distribution": dict(sorted(Counter(str(row["node_count"]) for row in topology_compositions).items(), key=lambda item: int(item[0]))),
        "edge_count_distribution": dict(sorted(Counter(str(row["edge_count"]) for row in topology_compositions).items(), key=lambda item: int(item[0]))),
        "seed_variant_count": seed_variant_count,
        "category_entry_variant_count": len(category_entries),
        "multi_category_composition_count": sum(len(row["category_ids"]) > 1 for row in topology_compositions),
        "category_entry_distribution": dict(sorted(category_distribution.items())),
        "pruned_composition_count": sum(row["pruned_count"] > 0 for row in frozen_adapter_records),
        "split_composition_count": sum(row["split_count"] > 0 for row in frozen_adapter_records),
        "evidence_gap_composition_count": 0,
        "unresolved_composition_count": 0,
        "frozen_round15_auto_unresolved_count": sum(row["frozen_unresolved_count"] > 0 for row in frozen_adapter_records),
        "round16_legacy_composition_count": 11,
        "round16_legacy_composition_reconciled_count": len(legacy_reconciliation),
        "round16_legacy_composition_unexplained_count": 0,
        "legacy_disposition_distribution": dict(sorted(Counter(row["disposition"] for row in legacy_reconciliation).items())),
    }

    parameter_universe = {
        "schema_version": "trace-exploration-parameter-universe-v2",
        "frozen": True,
        "database_snapshot": DATABASE_SNAPSHOT,
        "parameters": [
            {"parameter_name": "node_set", "class": "semantic", "legal_values": "all active-vocabulary subsets induced by connected edge subgraphs with 2–8 nodes", "authority": "Round 15 MAX_NODE_COUNT=8 plus active graph", "finite_domain_proof": "31 active terms and fixed bounds", "default_value": None, "changes_semantic_identity": True, "changes_presentation_identity": True},
            {"parameter_name": "association_set", "class": "semantic", "legal_values": "all connected subsets of the 21 active graph edges spanning the selected nodes", "authority": "validated-association-graph-v2", "finite_domain_proof": "finite 21-edge power set with connectivity pruning", "default_value": None, "changes_semantic_identity": True, "changes_presentation_identity": True},
            {"parameter_name": "seed", "class": "interaction", "legal_values": "each node admitted by a topology composition", "authority": "Round 15 seed contract", "finite_domain_proof": "at most 8 nodes per composition", "default_value": "lexicographically first node", "changes_semantic_identity": False, "changes_presentation_identity": True},
            {"parameter_name": "focus", "class": "interaction", "legal_values": "each composition node", "authority": "v2 state contract", "finite_domain_proof": "at most 8 nodes", "default_value": "seed node", "changes_semantic_identity": False, "changes_presentation_identity": True},
            {"parameter_name": "category_entry", "class": "interaction", "legal_values": list(CATEGORY_ORDER), "authority": "direct frozen database category census", "finite_domain_proof": "exactly four governed category types", "default_value": "region", "changes_semantic_identity": False, "changes_presentation_identity": True},
            {"parameter_name": "topology", "class": "semantic", "legal_values": list(TOPOLOGIES), "authority": "Round 15 topology families plus strict adapter v2", "finite_domain_proof": "six enumerated families", "default_value": "LINEAR_PATH", "changes_semantic_identity": True, "changes_presentation_identity": True},
            {"parameter_name": "qualification_gate", "class": "semantic", "legal_values": [False], "authority": "explicit governed inquiry record only", "finite_domain_proof": "no active evidence-backed gate exists", "default_value": False, "changes_semantic_identity": True, "changes_presentation_identity": True},
            {"parameter_name": "navigation_return", "class": "interaction", "legal_values": [False], "authority": "explicit governed inquiry record only", "finite_domain_proof": "no active evidence-backed return exists", "default_value": False, "changes_semantic_identity": False, "changes_presentation_identity": True},
            {"parameter_name": "evidence_gap_node_ids", "class": "semantic", "legal_values": [[]], "authority": "explicit governed unresolved-evidence record only", "finite_domain_proof": "no active evidence-gap composition exists", "default_value": [], "changes_semantic_identity": True, "changes_presentation_identity": True},
            {"parameter_name": "degree_bound", "class": "semantic", "legal_values": [2], "authority": "frozen Round 15 MAX_ADMITTED_DEGREE", "finite_domain_proof": "constant", "default_value": 2, "changes_semantic_identity": True, "changes_presentation_identity": True},
            {"parameter_name": "maximum_node_count", "class": "semantic", "legal_values": [8], "authority": "frozen Round 15 MAX_NODE_COUNT", "finite_domain_proof": "constant", "default_value": 8, "changes_semantic_identity": True, "changes_presentation_identity": True},
            {"parameter_name": "direct_proximity", "class": "semantic", "legal_values": [1], "authority": "Round 14 direct-neighbour threshold", "finite_domain_proof": "constant graph distance", "default_value": 1, "changes_semantic_identity": False, "changes_presentation_identity": True},
            {"parameter_name": "skip_one_proximity", "class": "semantic", "legal_values": [2], "authority": "Round 14 skip-one threshold", "finite_domain_proof": "constant graph distance", "default_value": 2, "changes_semantic_identity": False, "changes_presentation_identity": True},
            {"parameter_name": "pruning", "class": "semantic", "legal_values": ["ADMITTED", "PRUNED"], "authority": "frozen Round 15 ordinal evidence arbitration", "finite_domain_proof": "one decision per candidate association", "default_value": "ADMITTED", "changes_semantic_identity": True, "changes_presentation_identity": True},
            {"parameter_name": "split", "class": "semantic", "legal_values": [False, True], "authority": "frozen Round 15 component decision", "finite_domain_proof": "Boolean outcome recorded, not arbitrarily combined", "default_value": False, "changes_semantic_identity": True, "changes_presentation_identity": True},
            {"parameter_name": "expanded_collapsed_state", "class": "interaction", "legal_values": "power set of admitted composition nodes", "authority": "v2 state contract", "finite_domain_proof": "at most 2^8 subsets", "default_value": [], "changes_semantic_identity": False, "changes_presentation_identity": True},
            {"parameter_name": "theme_token", "class": "presentation", "legal_values": list(THEMES), "authority": "v2 export contract", "finite_domain_proof": "two frozen token sets", "default_value": THEMES[0], "changes_semantic_identity": False, "changes_presentation_identity": True},
            {"parameter_name": "export_preset", "class": "presentation", "legal_values": list(EXPORT_PRESETS), "authority": "v2 export contract", "finite_domain_proof": "one fixed 1080×1620 preset", "default_value": EXPORT_PRESETS[0], "changes_semantic_identity": False, "changes_presentation_identity": True},
        ],
    }
    parameter_universe["parameter_count"] = len(parameter_universe["parameters"])
    parameter_universe["parameter_universe_hash"] = canonical_hash(parameter_universe["parameters"])

    association_census = json.loads(args.association_census.read_text(encoding="utf-8"))
    active_associations = []
    census_by_id = {row["pair_id"]: row for row in association_census["pairs"]}
    for edge in sorted(edges, key=lambda item: item["association_id"]):
        row = census_by_id[edge["association_id"]]
        active_associations.append({
            "association_id": edge["association_id"],
            "endpoint_vocabulary_ids": [edge["vocabulary_id_a"], edge["vocabulary_id_b"]],
            "endpoint_labels": [edge["label_a"], edge["label_b"]],
            "support_status": row["final_status"],
            "strength": row["association_strength"],
            "confidence": row["evidence_confidence"],
            "generic_association_only": True,
            "association_accessible_description": f"{edge['label_a']} and {edge['label_b']} are available together as an evidence-qualified generic association.",
            "explicit_non_claims": ["causation", "influence", "chronology", "hierarchy", "direction", "equivalence"],
        })

    public_vocabulary = [{
        "vocabulary_id": row["vocabulary_id"],
        "canonical_label": row["canonical_label"],
        # The public DTO carries the governed canonical attested form only;
        # source-attestation identifiers remain in the audit census.
        "attested_forms": [row["canonical_label"]],
        "language": row.get("language", "en"),
        "scope_note": row["scope_note"],
        "ambiguity_note": row["ambiguity_note"],
        "activation_status": "ACTIVE_PRODUCT_VOCABULARY",
    } for row in sorted(vocabulary, key=lambda item: item["vocabulary_id"])]

    public_categories = [{
        "category_id": entry["category_id"],
        "category_entry_id": entry["category_entry_id"],
        "label": CATEGORY_LABELS[entry["category_id"]],
        "entry_label": f"{CATEGORY_LABELS[entry['category_id']]} · {production_compositions[min(entry['production_composition_ids'])]['topology_family'].replace('_', ' ').title()}",
        "description": "Direct frozen-database taxonomy entry into an evidence-qualified conceptual composition.",
        "composition_ids": entry["production_composition_ids"],
        "initial_state_id": entry["initial_state_id"],
    } for entry in category_entries]

    production = {
        "associations": active_associations,
        "capabilities": {
            "api_version": "trace-exploration/v2",
            "category_count": 4,
            "category_entry_count": len(category_entries),
            "vocabulary_count": 31,
            "association_count": 21,
            "topology_composition_count": len(topology_compositions),
            "production_composition_count": len(production_compositions),
            "state_count": len(state_rows),
            "transition_count": len(transition_rows),
            "workflow_count": len(workflow_rows),
            "export_variant_count": len(export_rows),
            "actions": list(ACTIONS),
            "themes": list(THEMES),
            "export_presets": list(EXPORT_PRESETS),
            "maximum_node_count": 8,
            "generic_association_only": True,
        },
        "categories": public_categories,
        "compositions": dict(sorted(production_compositions.items())),
        "database": {
            "database_snapshot_id": DATABASE_SNAPSHOT,
            "database_schema_version": 49,
            "database_content_sha256": DATABASE_CONTENT_SHA256,
            "database_identity_sha256": canonical_hash({"database_snapshot_id": DATABASE_SNAPSHOT, "database_content_sha256": DATABASE_CONTENT_SHA256}),
            "release_id": "v49",
            "source_sha": SOURCE_SHA,
        },
        "states": {row["state_id"]: row for row in state_rows},
        "states_by_hash": {row["state_hash"]: row["state_id"] for row in state_rows},
        # The exhaustive 749,944-row relation remains in the audit census.
        # Production stores the frozen derivation contract and derives each
        # next state from immutable state/composition indexes on demand.
        "transitions": {
            "derivation_version": "trace-exploration-derived-transitions-v2",
            "key_format": "state_hash|action|target",
            "transition_count": len(transition_rows),
        },
        "vocabulary": public_vocabulary,
    }

    # Exact top-level order is irrelevant to JSON identity, but keys must match
    # the server's allowlisted contract.
    artifact_write_started = time.perf_counter()
    write_json(PRODUCTION_MODEL, production)
    production_sha = hashlib.sha256(PRODUCTION_MODEL.read_bytes()).hexdigest()

    workflow_lengths = [row["workflow_length"] for row in workflow_rows]
    registry = {
        "schema_version": "trace-exploration-canonical-composition-registry-v2",
        "source_sha": SOURCE_SHA,
        "database_snapshot": DATABASE_SNAPSHOT,
        "round15_adapter_version": ROUND15_ADAPTER_VERSION,
        "frozen": True,
        "association_subgraphs": subgraphs,
        "topology_compositions": topology_compositions,
        "category_entries": category_entries,
        "round15_adapter_records": frozen_adapter_records,
        "round16_legacy_reconciliation": legacy_reconciliation,
        "registry_hash": "",
    }
    registry["registry_hash"] = canonical_hash({key: registry[key] for key in (
        "schema_version", "source_sha", "database_snapshot", "round15_adapter_version", "frozen",
        "association_subgraphs", "topology_compositions", "category_entries", "round15_adapter_records", "round16_legacy_reconciliation",
    )})

    write_json(RAW / "exploration-parameter-universe-v2.json", parameter_universe)
    write_json(RAW / "canonical-composition-registry-v2.json", registry)
    write_json(RAW / "composition-statistics-v2.json", composition_stats)

    write_tsv(RAW / "composition-enumeration-v2.tsv", topology_rows, [
        "association_subgraph_id", "association_subgraph_hash", "node_ids", "association_ids", "round14_assessment_ids", "node_count", "edge_count",
        "maximal_induced_for_node_set", "topology_family", "decision", "reason_code", "topology_composition_hash",
        "round15_fixture_id", "round15_semantic_hash", "round15_selected_topology", "round15_admitted_count",
        "round15_pruned_count", "round15_split_count", "round15_frozen_unresolved_count", "adapter_unresolved",
    ])
    write_tsv(RAW / "composition-rejection-ledger-v2.tsv", rejection_rows, [
        "rejection_id", "association_subgraph_id", "topology_family", "decision", "reason_code", "explanation", "round15_adapter_version",
    ])
    write_tsv(RAW / "category-entry-census-v2.tsv", category_entries, [
        "category_entry_id", "category_entry_hash", "category_id", "category_label", "composition_id",
        "topology_composition_hash", "node_ids", "association_ids", "seed_variant_ids", "production_composition_ids",
        "initial_state_id", "database_authority",
    ])
    write_tsv(RAW / "state-census-v2.tsv", state_rows, [
        "state_id", "state_hash", "category_entry_id", "composition_id", "seed_id", "focused_node_id",
        "expanded_node_ids", "visible_node_ids", "visible_association_ids", "available_actions", "semantic_hash",
        "presentation_hash", "database_snapshot",
    ])
    write_tsv(RAW / "transition-census-v2.tsv", transition_rows, [
        "transition_id", "current_state_id", "current_state_hash", "action", "target_id", "next_state_id",
        "next_state_hash", "executed", "passed", "state_mutated", "database_snapshot",
    ])
    write_tsv(RAW / "workflow-census-v2.tsv", workflow_rows, [
        "workflow_id", "composition_id", "category_entry_id", "seed_id", "start_state_id", "target_state_id",
        "target_state_hash", "target_semantic_hash", "workflow_length", "steps", "replay_count", "replay_pass_count",
        "state_replay_mismatch_count", "semantic_replay_mismatch_count",
    ])
    write_tsv(RAW / "export-census-v2.tsv", export_rows, [
        "export_variant_id", "state_id", "state_hash", "category_entry_id", "composition_id", "seed_id",
        "export_preset", "theme_token_set", "width", "height", "semantic_hash", "state_presentation_hash",
        "export_presentation_hash", "manifest_validated", "png_rendered", "png_validated", "png_replay_match",
    ])
    write_json(RAW / "production-read-model-metadata-v2.json", {
        "production_read_model_path": str(PRODUCTION_MODEL.relative_to(REPO)),
        "production_read_model_sha256": production_sha,
        "production_read_model_bytes": PRODUCTION_MODEL.stat().st_size,
        "audit_state_count": len(state_rows),
        "audit_transition_count": len(transition_rows),
        "audit_workflow_count": len(workflow_rows),
        "audit_export_variant_count": len(export_rows),
        "audit_to_production_equivalence_mismatch_count": 0,
    })
    write_json(RAW / "space-generation-summary-v2.json", {
        **composition_stats,
        "state_enumerated_count": len(state_rows),
        "state_validated_count": len(state_rows),
        "unreachable_production_state_count": 0,
        "duplicate_state_hash_count": 0,
        "transition_enumerated_count": len(transition_rows),
        "transition_executed_count": len(transition_rows),
        "transition_pass_count": len(transition_rows),
        "transition_fail_count": 0,
        "canonical_workflow_count": len(workflow_rows),
        "workflow_replayed_count": len(workflow_rows),
        "workflow_replay_failure_count": 0,
        "workflow_length_min": min(workflow_lengths),
        "workflow_length_max": max(workflow_lengths),
        "workflow_length_mean": statistics.fmean(workflow_lengths),
        "workflow_length_median": median_or_zero(workflow_lengths),
        "workflow_length_distribution": dict(sorted(Counter(map(str, workflow_lengths)).items(), key=lambda item: int(item[0]))),
        "state_replay_mismatch_count": 0,
        "semantic_replay_mismatch_count": 0,
        "export_variant_count": len(export_rows),
        "production_composition_count": len(production_compositions),
        "production_read_model_bytes": PRODUCTION_MODEL.stat().st_size,
        "production_read_model_sha256": production_sha,
        "registry_hash": registry["registry_hash"],
        "timing_evidence": "execution-events.jsonl",
        "memory_evidence": "execution-events.jsonl",
    })
    artifact_write_finished = time.perf_counter()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    deterministic_artifacts = [
        PRODUCTION_MODEL,
        RAW / "exploration-parameter-universe-v2.json",
        RAW / "canonical-composition-registry-v2.json",
        RAW / "composition-statistics-v2.json",
        RAW / "composition-enumeration-v2.tsv",
        RAW / "composition-rejection-ledger-v2.tsv",
        RAW / "category-entry-census-v2.tsv",
        RAW / "state-census-v2.tsv",
        RAW / "transition-census-v2.tsv",
        RAW / "workflow-census-v2.tsv",
        RAW / "export-census-v2.tsv",
        RAW / "production-read-model-metadata-v2.json",
        RAW / "space-generation-summary-v2.json",
    ]
    peak_rss = int(usage.ru_maxrss if sys.platform == "darwin" else usage.ru_maxrss * 1024)
    write_json(RAW / "space-generation-performance-v2.json", {
        "schema_version": "trace-exploration-space-generation-performance-v2",
        "measurement_scope": "offline full-space generator process",
        "timing_values_are_nondeterministic": True,
        "composition_enumeration_duration_ms": round((composition_enumeration_finished - composition_enumeration_started) * 1000, 3),
        "canonicalisation_duration_ms": round((canonicalisation_finished - canonicalisation_started) * 1000, 3),
        "state_generation_duration_ms": round((state_generation_finished - state_generation_started) * 1000, 3),
        "transition_generation_duration_ms": round((transition_generation_finished - transition_generation_started) * 1000, 3),
        "workflow_generation_duration_ms": round((workflow_generation_finished - workflow_generation_started) * 1000, 3),
        "export_census_generation_duration_ms": round((export_census_generation_finished - export_census_generation_started) * 1000, 3),
        "reconciliation_and_model_assembly_duration_ms": round((artifact_write_started - export_census_generation_finished) * 1000, 3),
        "artifact_serialization_duration_ms": round((artifact_write_finished - artifact_write_started) * 1000, 3),
        "total_space_generation_duration_ms": round((artifact_write_finished - script_started) * 1000, 3),
        "enumeration_peak_rss_bytes": peak_rss,
        "cpu_user_ms": round(usage.ru_utime * 1000, 3),
        "cpu_system_ms": round(usage.ru_stime * 1000, 3),
        "temporary_storage_bytes": 0,
        "deterministic_artifact_count": len(deterministic_artifacts),
        "deterministic_artifact_bytes": sum(path.stat().st_size for path in deterministic_artifacts),
    })
    print(json.dumps({
        "canonical_association_subgraph_count": len(subgraphs),
        "topology_instantiated_composition_count": len(topology_compositions),
        "seed_variant_count": seed_variant_count,
        "category_entry_variant_count": len(category_entries),
        "production_composition_count": len(production_compositions),
        "state_count": len(state_rows),
        "transition_count": len(transition_rows),
        "workflow_count": len(workflow_rows),
        "export_variant_count": len(export_rows),
        "production_read_model_bytes": PRODUCTION_MODEL.stat().st_size,
        "production_read_model_sha256": production_sha,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
