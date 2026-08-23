#!/usr/bin/env python3
"""Generate deterministic TRACE v49 Round 1 census artifacts.

The v49 PostgreSQL release is represented by its frozen verifier and release
receipts. Object-local diagnostics are computed against the immutable v48
SQLite reconciliation artifact, joined to the audited v49 eligibility ledger.
The SQLite database is never used as publication authority and is opened
immutable/query-only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "docs/research/trace-v49-round1"
AUDIT = ROOT / "docs/audits/v49-trace-census-preprogram-round1"
RAW = AUDIT / "raw"
FREEZE_PATH = ROOT / "database/FREEZE_V49.json"
VERIFIER_PATH = ROOT / "docs/audits/v49-api-read-contract-closure/raw/fresh-c/fresh-c-verifier.json"
PROFILE_PATH = ROOT / "docs/statistics/v49-release-data-profile.csv"
LEDGER_PATH = ROOT / "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv"
SQLITE_PATH = ROOT / "data/prefreeze_candidate_v48.sqlite"
CANONICAL_PATH = ROOT / "generated/public_surfaces_prefreeze_candidate_v48.json"
SEARCH_MANIFEST_PATH = ROOT / "frontend/generated/search-v49/manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def tsv_bytes(headers: list[str], rows: Iterable[dict[str, Any]]) -> bytes:
    lines = ["\t".join(headers)]
    for row in rows:
        cells = []
        for header in headers:
            value = row.get(header, "")
            text = "" if value is None else str(value)
            cells.append(text.replace("\t", " ").replace("\r", " ").replace("\n", " "))
        lines.append("\t".join(cells))
    return ("\n".join(lines) + "\n").encode("utf-8")


def quantile(values: list[int], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def printable_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def distribution(metric: str, values: list[int], population: str = "public_object") -> dict[str, Any]:
    total = sum(values)
    return {
        "population": population,
        "metric": metric,
        "n": len(values),
        "min": min(values, default=0),
        "p25": printable_number(quantile(values, 0.25)),
        "median": printable_number(quantile(values, 0.50)),
        "mean": printable_number(total / len(values) if values else 0),
        "p75": printable_number(quantile(values, 0.75)),
        "p90": printable_number(quantile(values, 0.90)),
        "p95": printable_number(quantile(values, 0.95)),
        "p99": printable_number(quantile(values, 0.99)),
        "max": max(values, default=0),
        "zero_count": sum(value == 0 for value in values),
        "nonzero_count": sum(value > 0 for value in values),
    }


def is_present(value: Any) -> bool:
    return bool(str(value or "").strip()) and str(value).strip().lower() not in {
        "none", "unknown", "unresolved", "n/a", "not known"
    }


APPROXIMATE_RE = re.compile(
    r"\b(ca\.?|circa|about|approx|around|before|after|early|mid|late|between|century|decade)\b|s$|\?|–|-",
    re.IGNORECASE,
)
EXACT_YEAR_RE = re.compile(r"^\d{4}$")


def time_precision(date_text: str, start: int | None, end: int | None) -> str:
    text = (date_text or "").strip()
    if start is None or not text or text.lower() in {"unknown", "n/a", "none"}:
        return "unknown"
    if EXACT_YEAR_RE.fullmatch(text) and (end is None or start == end):
        return "year"
    if end is not None and end != start:
        return "range"
    if APPROXIMATE_RE.search(text):
        return "approximate"
    if re.search(r"\d{4}-\d{2}-\d{2}|\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b|[A-Za-z]+\s+\d{1,2},\s*\d{4}", text):
        return "day"
    return "approximate"


def table_count(count_vector: dict[str, int], schema: str, table: str) -> int:
    return int(count_vector.get(f"{schema}_{table}", 0))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    freeze = json.loads(FREEZE_PATH.read_text("utf-8"))
    verifier = json.loads(VERIFIER_PATH.read_text("utf-8"))
    search_manifest = json.loads(SEARCH_MANIFEST_PATH.read_text("utf-8"))

    input_hashes = {
        "database/FREEZE_V49.json": sha256(FREEZE_PATH),
        "fresh-c-verifier.json": sha256(VERIFIER_PATH),
        "18_SURFACE_ROW_LEDGER.tsv": sha256(LEDGER_PATH),
        "data/prefreeze_candidate_v48.sqlite": sha256(SQLITE_PATH),
        "generated/public_surfaces_prefreeze_candidate_v48.json": sha256(CANONICAL_PATH),
        "frontend/generated/search-v49/manifest.json": sha256(SEARCH_MANIFEST_PATH),
    }
    expected = freeze["perFileSha256"]
    assert input_hashes["data/prefreeze_candidate_v48.sqlite"] == expected["data/prefreeze_candidate_v48.sqlite"]
    assert input_hashes["generated/public_surfaces_prefreeze_candidate_v48.json"] == expected["generated/public_surfaces_prefreeze_candidate_v48.json"]
    assert verifier["status"] == "PASS"
    assert verifier["schemaShaAfter"] == freeze["schemaHash"]
    assert verifier["metrics"]["operationalObjects"] == freeze["objectCount"]
    assert verifier["metrics"]["folderMembershipAssignments"] == freeze["relationshipCount"]
    assert search_manifest["document_count"] == freeze["eligibleCount"]

    ledger: dict[str, dict[str, str]] = {}
    with LEDGER_PATH.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            ledger[row["surface_id_exact"]] = row
    eligible_ids = {stable_id for stable_id, row in ledger.items() if row["research_disposition"] == "eligible"}
    held_ids = {stable_id for stable_id, row in ledger.items() if row["research_disposition"] == "held"}
    assert len(ledger) == freeze["objectCount"]
    assert len(eligible_ids) == freeze["eligibleCount"]
    assert len(held_ids) == freeze["heldCount"]
    assert not eligible_ids.intersection(held_ids)

    uri = f"file:{SQLITE_PATH}?mode=ro&immutable=1"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    assert connection.execute("PRAGMA query_only").fetchone()[0] == 1
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

    objects = {
        row["surface_id"]: dict(row)
        for row in connection.execute(
            """SELECT surface_id, creator, date_text, date_start, date_end, region,
                      medium, object_type, source_name, source_url, source_document_id,
                      authority_geography_role, trace_object_node_id
               FROM objects ORDER BY surface_id"""
        )
    }
    assert len(objects) == freeze["objectCount"]
    assert set(objects) == set(ledger)

    folders: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in connection.execute(
        "SELECT surface_id, folder_id, folder_type FROM object_folder_refs ORDER BY surface_id, folder_id"
    ):
        folders[row["surface_id"]].append(dict(row))
    assert sum(map(len, folders.values())) == freeze["relationshipCount"]
    sorted_folder_pairs = sorted(
        (folder["folder_id"], stable_id)
        for stable_id, memberships in folders.items()
        for folder in memberships
    )
    folder_pair_sha256 = hashlib.sha256(
        "".join(f"{folder_id}\t{stable_id}\n" for folder_id, stable_id in sorted_folder_pairs).encode("utf-8")
    ).hexdigest()
    assert folder_pair_sha256 == "b2ddbe94f4d569f6b9970246855b535374b7c1a9b8ac047de58899c860bd4573"

    collections: dict[str, set[str]] = defaultdict(set)
    for row in connection.execute(
        """SELECT surface_id, value FROM object_metadata_rows
           WHERE table_kind='SOURCE' AND label='Source collection'
           ORDER BY surface_id, row_order"""
    ):
        if is_present(row["value"]):
            collections[row["surface_id"]].add(row["value"].strip())

    legacy_counts = {
        table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        for table in (
            "source_documents", "object_folder_refs", "object_metadata_rows", "capture_records",
            "trace_nodes", "trace_edges", "object_trace_edges", "search_documents"
        )
    }
    legacy_edge_states = {
        row["review_state"]: row["count"]
        for row in connection.execute(
            "SELECT review_state, count(*) AS count FROM trace_edges GROUP BY review_state ORDER BY review_state"
        )
    }

    legacy_node_names = [
        row["node_id"] for row in connection.execute("SELECT node_id FROM trace_nodes ORDER BY node_id")
    ]
    legacy_node_index = {node_id: index for index, node_id in enumerate(legacy_node_names)}
    legacy_edge_nodes: list[tuple[int, int]] = []
    legacy_edge_index: dict[str, int] = {}
    legacy_adjacency: list[list[int]] = [[] for _ in legacy_node_names]
    legacy_relation_labels = Counter()
    for row in connection.execute(
        "SELECT edge_id, subject_node_id, object_node_id, edge_label FROM trace_edges ORDER BY edge_id"
    ):
        edge_number = len(legacy_edge_nodes)
        subject = legacy_node_index[row["subject_node_id"]]
        object_id = legacy_node_index[row["object_node_id"]]
        legacy_edge_index[row["edge_id"]] = edge_number
        legacy_edge_nodes.append((subject, object_id))
        legacy_adjacency[subject].append(edge_number)
        legacy_adjacency[object_id].append(edge_number)
        legacy_relation_labels[row["edge_label"]] += 1
    legacy_memberships: dict[str, list[int]] = defaultdict(list)
    for row in connection.execute(
        "SELECT surface_id, edge_id FROM object_trace_edges ORDER BY surface_id, edge_id"
    ):
        legacy_memberships[row["surface_id"]].append(legacy_edge_index[row["edge_id"]])

    # Analysis-only legacy capacity diagnostic. Expansion is undirected because
    # v48 labels were not promoted to the v49 directionality registry. Strict
    # caps make the diagnostic safe even if a later legacy artifact grows.
    legacy_local: list[dict[str, Any]] = []
    two_hop_node_cap = 10_000
    two_hop_edge_cap = 50_000
    for stable_id in sorted(eligible_ids):
        root_name = objects[stable_id]["trace_object_node_id"]
        root = legacy_node_index.get(root_name) if root_name else None
        local_edge_ids = legacy_memberships.get(stable_id, [])
        one_nodes = {root} if root is not None else set()
        for edge_id in local_edge_ids:
            subject, object_id = legacy_edge_nodes[edge_id]
            one_nodes.update((subject, object_id))
        two_edge_ids: set[int] = set(local_edge_ids)
        capped = False
        for node_id in sorted(one_nodes):
            two_edge_ids.update(legacy_adjacency[node_id])
            if len(two_edge_ids) > two_hop_edge_cap:
                two_edge_ids = set(sorted(two_edge_ids)[:two_hop_edge_cap])
                capped = True
                break
        two_nodes = set(one_nodes)
        for edge_id in sorted(two_edge_ids):
            subject, object_id = legacy_edge_nodes[edge_id]
            two_nodes.update((subject, object_id))
            if len(two_nodes) > two_hop_node_cap:
                two_nodes = set(sorted(two_nodes)[:two_hop_node_cap])
                capped = True
                break
        legacy_local.append({
            "stable_id": stable_id,
            "one_hop_nodes": len(one_nodes),
            "one_hop_edges": len(local_edge_ids),
            "two_hop_nodes": len(two_nodes),
            "two_hop_edges": len(two_edge_ids),
            "capped": capped,
        })

    # Weakly connected component diagnostics for the retained v48 graph only.
    parent = list(range(len(legacy_node_names)))
    size = [1] * len(legacy_node_names)

    def find(node_id: int) -> int:
        cursor = node_id
        while parent[cursor] != cursor:
            parent[cursor] = parent[parent[cursor]]
            cursor = parent[cursor]
        return cursor

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        if size[left_root] < size[right_root] or (size[left_root] == size[right_root] and left_root > right_root):
            left_root, right_root = right_root, left_root
        parent[right_root] = left_root
        size[left_root] += size[right_root]

    for subject, object_id in legacy_edge_nodes:
        union(subject, object_id)
    component_sizes = Counter(find(node_id) for node_id in range(len(legacy_node_names)))
    legacy_degrees = [len(edges) for edges in legacy_adjacency]
    legacy_global = {
        "classification": "LAYOUT/PERFORMANCE DIAGNOSTIC ONLY; NOT HISTORICAL INTERPRETATION",
        "nodes": len(legacy_node_names),
        "edges": len(legacy_edge_nodes),
        "isolated_nodes": sum(value == 0 for value in legacy_degrees),
        "weak_components": len(component_sizes),
        "largest_component": max(component_sizes.values(), default=0),
        "component_size_distribution": dict(sorted(Counter(component_sizes.values()).items())),
        "degree": distribution("legacy_global_undirected_degree", legacy_degrees, "legacy_v48_trace_node"),
        "relation_label_distribution": dict(sorted(legacy_relation_labels.items())),
        "directed_cycles": "NOT_CALCULATED_DIRECTIONALITY_NOT_V49_VERIFIED",
        "two_hop_node_cap": two_hop_node_cap,
        "two_hop_edge_cap": two_hop_edge_cap,
        "capped_public_object_count": sum(row["capped"] for row in legacy_local),
    }
    connection.close()

    public_metrics: list[dict[str, Any]] = []
    folder_type_totals = Counter()
    folder_type_public = Counter()
    folder_type_held = Counter()
    place_role_public = Counter()
    time_precision_public = Counter()
    year_public = Counter()
    decade_public = Counter()
    raw_region_public = Counter()
    unique_public_regions = set()
    unique_public_sources = set()
    unique_public_media = set()
    unique_public_types = set()

    for stable_id in sorted(objects):
        record = objects[stable_id]
        record_folders = folders.get(stable_id, [])
        for folder in record_folders:
            folder_type_totals[folder["folder_type"]] += 1
            if stable_id in eligible_ids:
                folder_type_public[folder["folder_type"]] += 1
            else:
                folder_type_held[folder["folder_type"]] += 1
        if stable_id not in eligible_ids:
            continue

        context_assignments = sum(folder["folder_type"] in {"medium", "theme", "movement"} for folder in record_folders)
        place_present = is_present(record["region"]) and record["region"] != "Unresolved region"
        precision = time_precision(record["date_text"], record["date_start"], record["date_end"])
        time_present = precision != "unknown"
        source_present = is_present(record["source_name"]) and is_present(record["source_url"])
        collection_count = len(collections.get(stable_id, set()))
        creator_count = 1 if is_present(record["creator"]) else 0
        broad_region = bool(re.search(r"/|transnational|global|region", record["region"] or "", re.IGNORECASE))
        place_role = record["authority_geography_role"].strip() or "unregistered_object_region_role"

        folder_count_by_type = Counter(folder["folder_type"] for folder in record_folders)
        metric = {
            "stable_id": stable_id,
            "accepted_semantic_relation_count": 0,
            "candidate_held_semantic_relation_count": 0,
            "context_assignment_count": context_assignments,
            "folder_membership_count": len(record_folders),
            "medium_assignment_count": folder_count_by_type["medium"],
            "theme_assignment_count": folder_count_by_type["theme"],
            "movement_assignment_count": folder_count_by_type["movement"],
            "place_count": 1 if place_present else 0,
            "time_count": 1 if time_present else 0,
            "source_record_count": 1 if source_present else 0,
            "legacy_source_document_ref_count": 1 if is_present(record["source_document_id"]) else 0,
            "evidence_item_count": 0,
            "claim_count": 0,
            "trace_node_count": 1,
            "tree_membership_count": 0,
            "collection_count": collection_count,
            "creator_count": creator_count,
            "time_precision": precision,
            "broad_region": broad_region,
            "place_role": place_role,
        }
        public_metrics.append(metric)
        time_precision_public[precision] += 1
        place_role_public[place_role] += 1
        if record["date_start"] is not None:
            year = int(record["date_start"])
            year_public[str(year)] += 1
            decade_public[f"{(year // 10) * 10}s"] += 1
        else:
            year_public["UNKNOWN"] += 1
            decade_public["UNKNOWN"] += 1
        raw_region_public[(record["region"] or "UNKNOWN").strip() or "UNKNOWN"] += 1
        if place_present:
            unique_public_regions.add(record["region"])
        if source_present:
            unique_public_sources.add(record["source_name"])
        if is_present(record["medium"]):
            unique_public_media.add(record["medium"])
        if is_present(record["object_type"]):
            unique_public_types.add(record["object_type"])

    assert len(public_metrics) == freeze["eligibleCount"]
    by_id = {row["stable_id"]: row for row in public_metrics}

    density_metrics = [
        "accepted_semantic_relation_count", "candidate_held_semantic_relation_count",
        "context_assignment_count", "folder_membership_count", "medium_assignment_count",
        "theme_assignment_count", "movement_assignment_count", "place_count", "time_count",
        "source_record_count", "legacy_source_document_ref_count", "evidence_item_count", "claim_count",
        "trace_node_count", "tree_membership_count", "collection_count", "creator_count",
    ]
    density_rows = [
        distribution(metric, [int(row[metric]) for row in public_metrics])
        for metric in density_metrics
    ]

    # The accepted v49 semantic graph is empty. A local neighborhood therefore
    # contains only the selected object/root and no graph edge.
    neighborhood_rows = []
    for metric, values in {
        "selected_object_nodes": [1] * len(public_metrics),
        "incoming_semantic_edges": [0] * len(public_metrics),
        "outgoing_semantic_edges": [0] * len(public_metrics),
        "unique_semantic_neighbors": [0] * len(public_metrics),
        "relation_type_diversity": [0] * len(public_metrics),
        "one_hop_nodes": [1] * len(public_metrics),
        "one_hop_edges": [0] * len(public_metrics),
        "two_hop_nodes_capped": [1] * len(public_metrics),
        "two_hop_edges_capped": [0] * len(public_metrics),
    }.items():
        row = distribution(metric, values)
        neighborhood_rows.append({
            "population": row["population"], "metric": metric, "n": row["n"],
            "p50": row["median"], "p90": row["p90"], "p95": row["p95"],
            "p99": row["p99"], "max": row["max"],
            "diagnostic_note": "accepted v49 semantic graph; selected object retained; no 2-hop expansion required",
        })

    for metric in ("one_hop_nodes", "one_hop_edges", "two_hop_nodes", "two_hop_edges"):
        row = distribution(
            f"legacy_{metric}", [int(item[metric]) for item in legacy_local],
            "legacy_v48_public_eligible_reconciliation_only",
        )
        neighborhood_rows.append({
            "population": row["population"], "metric": row["metric"], "n": row["n"],
            "p50": row["median"], "p90": row["p90"], "p95": row["p95"],
            "p99": row["p99"], "max": row["max"],
            "diagnostic_note": "LEGACY v48 capacity diagnostic only; not a v49 relation or publication candidate; 2-hop caps nodes=10000 edges=50000",
        })

    public_folder_assignments = sum(len(folders.get(stable_id, [])) for stable_id in eligible_ids)
    held_folder_assignments = sum(len(folders.get(stable_id, [])) for stable_id in held_ids)
    assert public_folder_assignments + held_folder_assignments == freeze["relationshipCount"]

    context_coverage = sum(row["context_assignment_count"] > 0 for row in public_metrics)
    time_coverage = sum(row["time_count"] > 0 for row in public_metrics)
    place_coverage = sum(row["place_count"] > 0 for row in public_metrics)
    both_coverage = sum(row["time_count"] > 0 and row["place_count"] > 0 for row in public_metrics)
    source_coverage = sum(row["source_record_count"] > 0 for row in public_metrics)
    all_three = sum(
        row["context_assignment_count"] > 0
        and row["time_count"] > 0
        and row["place_count"] > 0
        and row["source_record_count"] > 0
        for row in public_metrics
    )
    none = sum(
        row["context_assignment_count"] == 0
        and row["time_count"] == 0
        and row["place_count"] == 0
        and row["source_record_count"] == 0
        for row in public_metrics
    )

    census_specs = [
        ("research", "relation_type", "semantic predicate registry", 0, "none", "not projected", "SEMANTIC_RELATION", "No rows exist."),
        ("research", "epistemic_class", "epistemic policy registry", 0, "none", "not projected", "SEMANTIC_POLICY", "No rows exist."),
        ("research", "claim", "stable claim identity", 0, "none", "not projected", "CLAIM", "No rows exist."),
        ("research", "claim_revision", "versioned claim wording/state", 0, "none", "not projected", "CLAIM", "No rows exist."),
        ("research", "claim_evidence", "claim-to-evidence bridge", 0, "none", "not projected", "EVIDENCE_BRIDGE", "No rows exist."),
        ("research", "semantic_relation", "typed subject-predicate-object proposition", 0, "none", "not projected", "SEMANTIC_RELATION", "Canonical accepted/candidate relation set is empty."),
        ("research", "relation_claim", "relation-to-claim bridge", 0, "none", "not projected", "CLAIM_BRIDGE", "No rows exist."),
        ("research", "analysis_run", "deterministic/computed analysis provenance", 0, "none", "not projected", "ANALYSIS_PROVENANCE", "No rows exist."),
        ("research", "trace_tree", "working TRACE tree", 0, "none", "not projected", "CURATED_STRUCTURE", "No rows exist."),
        ("research", "trace_branch", "working TRACE branch", 0, "none", "not projected", "CURATED_STRUCTURE", "No rows exist."),
        ("research", "trace_node", "canonical object-root TRACE node", table_count(verifier["countVector"], "research", "trace_node"), "root", "not projected", "IDENTITY_BRIDGE", "Exactly one internal root per canonical object; not an edge."),
        ("research", "object_trace_node", "object-to-root-node identity bridge", table_count(verifier["countVector"], "research", "object_trace_node"), "root", "not projected", "IDENTITY_BRIDGE", "Exactly one per object; not a semantic relation."),
        ("research", "object_relation_membership", "object-to-semantic-relation membership", 0, "none", "not projected", "SEMANTIC_MEMBERSHIP", "No rows exist."),
        ("research", "trace_node_tree_membership", "TRACE node placement in tree", 0, "none", "not projected", "CURATED_MEMBERSHIP", "No rows exist."),
        ("provenance", "assignment_object_tree_membership", "governed object/tree assignment", 0, "none", "not projected", "CURATED_MEMBERSHIP", "No rows exist."),
        ("provenance", "canonical_assignment", "typed assignment lifecycle row", table_count(verifier["countVector"], "provenance", "canonical_assignment"), "proposed", "not projected", "CONTROLLED_ASSIGNMENT", "All rows are folder_membership/proposed."),
        ("provenance", "assignment_folder_membership", "curated folder membership subtype", table_count(verifier["countVector"], "provenance", "assignment_folder_membership"), "proposed", "not projected", "CURATED_MEMBERSHIP", "This is the complete 47,982 headline count."),
        ("provenance", "assignment_object_agent_credit", "normalized object-agent credit", 0, "none", "not projected", "CONTROLLED_ASSIGNMENT", "Table exists but was not populated."),
        ("provenance", "assignment_object_medium", "normalized object-medium assignment", 0, "none", "not projected", "CONTROLLED_ASSIGNMENT", "Table exists but was not populated."),
        ("provenance", "assignment_object_type", "normalized object-type assignment", 0, "none", "not projected", "CONTROLLED_ASSIGNMENT", "Table exists but was not populated."),
        ("provenance", "assignment_object_subject", "normalized object-subject assignment", 0, "none", "not projected", "CONTROLLED_ASSIGNMENT", "Table exists but was not populated."),
        ("provenance", "assignment_object_place", "normalized object-place assignment", 0, "none", "not projected", "CONTROLLED_ASSIGNMENT", "Table exists but was not populated."),
        ("provenance", "assignment_object_temporal", "normalized object-time assignment", 0, "none", "not projected", "CONTROLLED_ASSIGNMENT", "Table exists but was not populated."),
        ("provenance", "assignment_object_collection", "normalized object-collection assignment", 0, "none", "not projected", "CONTROLLED_ASSIGNMENT", "Table exists but was not populated."),
        ("provenance", "assignment_object_source_record", "governed source-record assignment", 0, "none", "not projected", "SOURCE_ASSOCIATION", "Table exists but was not populated."),
        ("provenance", "object_source_record", "object-to-raw-source-record bridge", table_count(verifier["countVector"], "provenance", "object_source_record"), "active", "not projected", "SOURCE_ASSOCIATION", "One internal bridge per canonical object."),
        ("provenance", "source_document", "normalized source document", 0, "none", "not projected", "SOURCE", "No rows exist."),
        ("provenance", "source_version", "versioned source document", 0, "none", "not projected", "SOURCE", "No rows exist."),
        ("provenance", "evidence_item", "located source evidence occurrence", 0, "none", "not projected", "EVIDENCE", "No rows exist."),
        ("provenance", "object_evidence", "object-to-evidence bridge", 0, "none", "not projected", "EVIDENCE_BRIDGE", "No rows exist."),
        ("provenance", "assertion", "typed assertion", 0, "none", "not projected", "ASSERTION", "No rows exist."),
        ("provenance", "assertion_evidence", "assertion-to-evidence bridge", 0, "none", "not projected", "EVIDENCE_BRIDGE", "No rows exist."),
        ("raw", "source_record", "canonical raw source record", table_count(verifier["countVector"], "raw", "source_record"), "active", "restricted", "RAW_PROVENANCE", "One per object; raw payload is not public-safe."),
        ("raw", "field_literal", "path-addressed raw field occurrence", table_count(verifier["countVector"], "raw", "field_literal"), "active", "restricted", "RAW_PROVENANCE", "Internal field-occurrence evidence, not semantic assignments."),
        ("raw", "fail_closed_delta", "held-object release exclusion", table_count(verifier["countVector"], "raw", "fail_closed_delta"), "held", "excluded", "PUBLICATION_GUARD", "Exactly the 7,928 held objects."),
        ("research", "corpus_membership", "public corpus eligibility decision", table_count(verifier["countVector"], "research", "corpus_membership"), "eligible", "public selection input", "PUBLICATION_DECISION", "Contains the 7,995 eligible rows only."),
        ("release", "research_trace_availability_projection_v3", "sealed release TRACE availability row", 1, "active", "public", "AVAILABILITY", "Explicit NO_ACCEPTED_SEMANTIC_RELATIONS state; counts are both zero."),
        ("release", "research_folder_membership_projection_v3", "sealed public folder membership", 0, "none", "public", "CURATED_MEMBERSHIP", "Release receipt folderMembershipCount=0."),
        ("release", "trace_projection_node", "release-owned TRACE node", 0, "none", "public", "IDENTITY_BRIDGE", "Release receipt traceEligibleObjectCount=0."),
        ("release", "trace_projection_edge", "release-owned accepted semantic edge", 0, "none", "public", "SEMANTIC_RELATION", "Release receipt relationCount=0."),
        ("release", "object_relation_membership_projection", "release-owned object/relation membership", 0, "none", "public", "SEMANTIC_MEMBERSHIP", "No published relation memberships."),
    ]
    census_rows = [
        {
            "schema": schema, "structure": table, "row_count": count, "semantic_meaning": meaning,
            "database_state": state, "normalized_analysis_state": (
                "accepted" if state == "accepted" else "held" if state == "held" else
                "review" if state in {"proposed", "queued"} else "active" if state in {"active", "root", "eligible"} else "empty"
            ),
            "public_eligibility": publication, "trace_category": category, "notes": notes,
        }
        for schema, table, meaning, count, state, publication, category, notes in census_specs
    ]

    boundary_rows = [
        {"structure": "research.semantic_relation", "endpoint_category": "PUBLIC_TO_PUBLIC", "row_count": 0, "public_projection_allowed": "NO_ROWS", "notes": "No binary semantic relations exist."},
        {"structure": "research.semantic_relation", "endpoint_category": "PUBLIC_TO_HELD", "row_count": 0, "public_projection_allowed": "NO", "notes": "Invariant guard remains mandatory."},
        {"structure": "research.semantic_relation", "endpoint_category": "HELD_TO_PUBLIC", "row_count": 0, "public_projection_allowed": "NO", "notes": "Invariant guard remains mandatory."},
        {"structure": "research.semantic_relation", "endpoint_category": "HELD_TO_HELD", "row_count": 0, "public_projection_allowed": "NO", "notes": "No binary semantic relations exist."},
        {"structure": "research.semantic_relation", "endpoint_category": "UNKNOWN", "row_count": 0, "public_projection_allowed": "NO", "notes": "No unresolved endpoints."},
        {"structure": "research.object_trace_node", "endpoint_category": "PUBLIC_OBJECT_ROOT", "row_count": len(eligible_ids), "public_projection_allowed": "REQUIRES_PUBLIC_PROJECTION", "notes": "Identity bridge only; not a TRACE eligibility decision."},
        {"structure": "research.object_trace_node", "endpoint_category": "HELD_OBJECT_ROOT", "row_count": len(held_ids), "public_projection_allowed": "NO", "notes": "Must remain excluded."},
        {"structure": "provenance.assignment_folder_membership", "endpoint_category": "PUBLIC_OBJECT_TO_FOLDER", "row_count": public_folder_assignments, "public_projection_allowed": "NO_PROPOSED_STATE", "notes": "Proposed curated membership, not a semantic edge."},
        {"structure": "provenance.assignment_folder_membership", "endpoint_category": "HELD_OBJECT_TO_FOLDER", "row_count": held_folder_assignments, "public_projection_allowed": "NO", "notes": "Held object endpoint."},
        {"structure": "provenance.object_source_record", "endpoint_category": "PUBLIC_OBJECT_TO_RESTRICTED_RAW_RECORD", "row_count": len(eligible_ids), "public_projection_allowed": "REQUIRES_SAFE_SERIALIZER", "notes": "Raw source record fields cannot be copied directly."},
        {"structure": "provenance.object_source_record", "endpoint_category": "HELD_OBJECT_TO_RESTRICTED_RAW_RECORD", "row_count": len(held_ids), "public_projection_allowed": "NO", "notes": "Held object and raw record remain excluded."},
    ]

    readiness_rows = [
        {"domain": "context", "data_concept": "folder membership", "source": "provenance.assignment_folder_membership", "total": freeze["relationshipCount"], "public_total": public_folder_assignments, "coverage_percent": printable_number(100 * sum(by_id[x]["folder_membership_count"] > 0 for x in by_id) / len(by_id)), "review_completeness": "0% accepted; all proposed", "evidence_completeness": "not satisfied", "stable_ids": "internal UUID + frozen folder token", "public_safe": "no", "aggregation_ready": "analysis-only", "object_local_ready": "preprogram-only", "semantic_edge_ready": "no", "api_ready": "no", "blocker": "REVIEW,PUBLICATION,API", "recommendation": "REQUIRES_SEMANTIC_REVIEW"},
        {"domain": "context", "data_concept": "raw medium/type labels", "source": "raw.field_literal + v48 reconciliation", "total": freeze["objectCount"], "public_total": len(eligible_ids), "coverage_percent": "100", "review_completeness": "raw only", "evidence_completeness": "source record only", "stable_ids": "object only", "public_safe": "no", "aggregation_ready": "analysis-only", "object_local_ready": "preprogram-only", "semantic_edge_ready": "no", "api_ready": "no", "blocker": "PUBLICATION,API", "recommendation": "REQUIRES_PUBLIC_PROJECTION"},
        {"domain": "spacetime", "data_concept": "raw temporal value", "source": "raw.field_literal + v48 reconciliation", "total": freeze["objectCount"], "public_total": time_coverage, "coverage_percent": printable_number(100 * time_coverage / len(by_id)), "review_completeness": "raw only", "evidence_completeness": "no evidence_item", "stable_ids": "object only", "public_safe": "no", "aggregation_ready": "analysis-only", "object_local_ready": "preprogram-only", "semantic_edge_ready": "no", "api_ready": "no", "blocker": "PUBLICATION,API", "recommendation": "REQUIRES_PUBLIC_PROJECTION"},
        {"domain": "spacetime", "data_concept": "untyped object region label", "source": "raw.field_literal + v48 reconciliation", "total": freeze["objectCount"], "public_total": place_coverage, "coverage_percent": printable_number(100 * place_coverage / len(by_id)), "review_completeness": "role unresolved", "evidence_completeness": "no coordinate evidence", "stable_ids": "object only", "public_safe": "no", "aggregation_ready": "analysis-only", "object_local_ready": "preprogram-only", "semantic_edge_ready": "no", "api_ready": "no", "blocker": "SEMANTIC,PUBLICATION,API", "recommendation": "REQUIRES_SEMANTIC_REVIEW"},
        {"domain": "sources", "data_concept": "object/raw-source-record association", "source": "provenance.object_source_record", "total": freeze["objectCount"], "public_total": source_coverage, "coverage_percent": printable_number(100 * source_coverage / len(by_id)), "review_completeness": "active bridge", "evidence_completeness": "no evidence_item/assertion/claim", "stable_ids": "internal source-record UUID forbidden", "public_safe": "no", "aggregation_ready": "analysis-only", "object_local_ready": "preprogram-only", "semantic_edge_ready": "no", "api_ready": "no", "blocker": "PUBLICATION,API", "recommendation": "REQUIRES_PUBLIC_PROJECTION"},
        {"domain": "sources", "data_concept": "evidence and claims", "source": "provenance.evidence_item + research.claim", "total": 0, "public_total": 0, "coverage_percent": "0", "review_completeness": "empty", "evidence_completeness": "empty", "stable_ids": "schema supports IDs; no rows", "public_safe": "no rows", "aggregation_ready": "no", "object_local_ready": "no", "semantic_edge_ready": "no", "api_ready": "no", "blocker": "DATA", "recommendation": "NOT_SUPPORTED"},
        {"domain": "cross-domain", "data_concept": "accepted semantic relation", "source": "research.semantic_relation", "total": 0, "public_total": 0, "coverage_percent": "0", "review_completeness": "empty", "evidence_completeness": "empty", "stable_ids": "schema supports URNs; no rows", "public_safe": "no rows", "aggregation_ready": "no", "object_local_ready": "no", "semantic_edge_ready": "no", "api_ready": "empty contract only", "blocker": "DATA,SEMANTIC,REVIEW", "recommendation": "NOT_SUPPORTED"},
    ]

    used: set[str] = set()
    samples: list[dict[str, Any]] = []

    def pick(reason: str, candidates: Iterable[dict[str, Any]], key) -> None:
        ordered = sorted((row for row in candidates if row["stable_id"] not in used), key=key)
        if not ordered:
            return
        row = ordered[0]
        used.add(row["stable_id"])
        samples.append({
            "stable_id": row["stable_id"], "selection_reason": reason,
            "public_boundary": "v49 eligible stable ID; no title, URL, evidence, or internal UUID serialized",
            "context_assignments": row["context_assignment_count"], "folder_memberships": row["folder_membership_count"],
            "time_observations": row["time_count"], "time_precision": row["time_precision"],
            "place_observations": row["place_count"], "source_associations": row["source_record_count"],
            "accepted_semantic_edges": 0,
        })

    context_values = [row["context_assignment_count"] for row in public_metrics]
    folder_values = [row["folder_membership_count"] for row in public_metrics]
    collection_values = [row["collection_count"] for row in public_metrics]
    pick("minimal measured local data", public_metrics, lambda row: (sum(int(row[name]) for name in ("context_assignment_count", "place_count", "time_count", "source_record_count", "collection_count", "creator_count")), row["stable_id"]))
    for label, target in (("median context workload", quantile(context_values, .5)), ("P95 context workload", quantile(context_values, .95)), ("maximum context workload", max(context_values))):
        pick(label, public_metrics, lambda row, target=target: (abs(row["context_assignment_count"] - target), row["stable_id"]))
    pick("P99 folder-membership workload", public_metrics, lambda row: (abs(row["folder_membership_count"] - quantile(folder_values, .99)), row["stable_id"]))
    pick("movement-assignment case", (row for row in public_metrics if row["movement_assignment_count"] > 0), lambda row: (-row["movement_assignment_count"], row["stable_id"]))
    pick("approximate-date case", (row for row in public_metrics if row["time_precision"] == "approximate"), lambda row: row["stable_id"])
    pick("range-date case", (row for row in public_metrics if row["time_precision"] == "range"), lambda row: row["stable_id"])
    pick("exact-year case", (row for row in public_metrics if row["time_precision"] == "year"), lambda row: row["stable_id"])
    pick("broad/unmapped-region stress case", (row for row in public_metrics if row["broad_region"]), lambda row: row["stable_id"])
    pick("median source-association workload", public_metrics, lambda row: (abs(row["source_record_count"] - 1), row["stable_id"]))
    pick("maximum source-association workload", public_metrics, lambda row: (-row["source_record_count"], row["stable_id"]))
    pick("maximum collection-context workload", public_metrics, lambda row: (-row["collection_count"], row["stable_id"]))
    pick("zero collection-context case", (row for row in public_metrics if row["collection_count"] == 0), lambda row: row["stable_id"])
    pick("creator-missingness case", (row for row in public_metrics if row["creator_count"] == 0), lambda row: row["stable_id"])
    pick("zero accepted-TRACE relation case", public_metrics, lambda row: row["stable_id"])

    summary = {
        "format": "gda-trace-v49-round1-census/v1",
        "source_branch": "feat/v49-fuzzy-search-round1-20260823",
        "source_sha": "f9bdfdd293023592ddc6af92858a24857c5a532a",
        "database": {
            "version": freeze["version"], "frozen": freeze["freezeStatus"] == "FROZEN",
            "schema_sha256": freeze["schemaHash"], "release_projection_digest": freeze["releaseProjectionDigest"],
            "canonical_objects": freeze["objectCount"], "public_objects": len(eligible_ids), "held_objects": len(held_ids),
            "reported_relationship_count": freeze["relationshipCount"],
            "relationship_actual_meaning": "proposed curated folder-membership assignments in provenance.assignment_folder_membership",
        },
        "v49_semantics": {
            "relation_types": 0, "semantic_relations": 0, "accepted_semantic_relations": 0,
            "held_review_relations": 0, "rejected_relations": 0, "unknown_relation_state": 0,
            "public_public_relations": 0, "public_held_relations": 0, "held_held_relations": 0,
            "unresolved_endpoint_relations": 0, "evidence_complete_public_relations": 0,
            "trace_root_nodes": freeze["objectCount"], "public_root_nodes": len(eligible_ids), "held_root_nodes": len(held_ids),
            "public_trace_eligible_objects": 0,
        },
        "public_candidate_coverage": {
            "objects_with_any_internal_trace_adjacent_data": len(by_id) - none,
            "objects_with_no_internal_trace_adjacent_data": none,
            "context": context_coverage, "time": time_coverage, "place": place_coverage,
            "time_and_place": both_coverage, "source_association": source_coverage,
            "all_three_domains": all_three,
            "currently_public_projected_domain_datasets": 0,
            "denominator": len(by_id),
        },
        "folder_assignments": {
            "total": freeze["relationshipCount"], "public_object_endpoint": public_folder_assignments,
            "held_object_endpoint": held_folder_assignments, "by_type_total": dict(sorted(folder_type_totals.items())),
            "by_type_public": dict(sorted(folder_type_public.items())), "by_type_held": dict(sorted(folder_type_held.items())),
            "sorted_pair_set_sha256": folder_pair_sha256,
        },
        "spacetime": {
            "time_precision_public": dict(sorted(time_precision_public.items())),
            "place_role_public": dict(sorted(place_role_public.items())),
            "unique_public_region_labels": len(unique_public_regions), "coordinate_rows": 0,
            "exact_registered_place_roles": 0, "unmapped_coordinate_objects": place_coverage,
            "year_distribution_public": dict(sorted(year_public.items())),
            "decade_distribution_public": dict(sorted(decade_public.items())),
            "raw_region_distribution_public": dict(sorted(raw_region_public.items())),
        },
        "context": {
            "unique_public_raw_medium_labels": len(unique_public_media),
            "unique_public_raw_type_labels": len(unique_public_types),
        },
        "sources": {
            "unique_public_raw_source_labels": len(unique_public_sources),
            "object_source_record_bridges_public": source_coverage,
            "provenance_source_documents": 0, "evidence_items": 0, "assertions": 0,
            "claims": 0, "claims_with_evidence": 0, "relations_with_claim": 0,
            "relations_with_evidence": 0, "relations_fully_evidence_complete": 0,
        },
        "legacy_v48_reconciliation_only": {
            **legacy_counts,
            "edge_states": legacy_edge_states,
            "global_graph": legacy_global,
            "public_eligible_local_capacity": {
                metric: distribution(
                    f"legacy_{metric}", [int(item[metric]) for item in legacy_local],
                    "legacy_v48_public_eligible_reconciliation_only",
                )
                for metric in ("one_hop_nodes", "one_hop_edges", "two_hop_nodes", "two_hop_edges")
            },
        },
        "density": {row["metric"]: row for row in density_rows},
        "neighborhood": {row["metric"]: row for row in neighborhood_rows},
        "sample_count": len(samples),
        "input_hashes": input_hashes,
    }

    relationship_rows = [
        {"source_table": "provenance.canonical_assignment", "row_count": 47982, "semantic_meaning": "governed assignment lifecycle row; assignment_kind=folder_membership", "accepted_review_held": "proposed=47982; accepted=0; rejected=0; superseded=0", "public_restricted": "not public-projected", "trace_mark": "only after explicit membership review", "trace_edge": "NO", "evidence_required": "review/evidence required before acceptance", "notes": "Lifecycle parent of assignment_folder_membership."},
        {"source_table": "provenance.assignment_folder_membership", "row_count": 47982, "semantic_meaning": "curated folder-to-object membership subtype", "accepted_review_held": "proposed=47982", "public_restricted": f"public endpoint={public_folder_assignments}; held endpoint={held_folder_assignments}; none published", "trace_mark": "possible non-semantic membership mark after review", "trace_edge": "NO", "evidence_required": "yes before acceptance/publication", "notes": "Exact source of headline 47,982; same rows, not additive."},
        {"source_table": "research.semantic_relation", "row_count": 0, "semantic_meaning": "typed semantic proposition", "accepted_review_held": "all states=0", "public_restricted": "0 public-public", "trace_mark": "NO_ROWS", "trace_edge": "NO_ROWS", "evidence_required": "relation-type policy; registry empty", "notes": "The only structure that would constitute semantic TRACE edges."},
        {"source_table": "research.object_relation_membership", "row_count": 0, "semantic_meaning": "object participation in semantic relation", "accepted_review_held": "empty", "public_restricted": "empty", "trace_mark": "NO_ROWS", "trace_edge": "NO", "evidence_required": "inherits semantic relation", "notes": "Not interchangeable with folder membership."},
        {"source_table": "research.object_trace_node", "row_count": 15923, "semantic_meaning": "object-to-root TRACE node identity bridge", "accepted_review_held": "root identity only", "public_restricted": "7995 public object endpoints; 7928 held object endpoints; none published", "trace_mark": "identity anchor only", "trace_edge": "NO", "evidence_required": "not evidence of relationship", "notes": "One root per canonical object."},
        {"source_table": "legacy v48 trace_edges", "row_count": legacy_counts["trace_edges"], "semantic_meaning": "legacy implementation candidate graph row", "accepted_review_held": "legacy review vocabulary only", "public_restricted": "not imported to v49", "trace_mark": "LEGACY_ONLY", "trace_edge": "NO_PROMOTION", "evidence_required": "row-by-row v49 review required", "notes": "Reconciliation evidence only."},
    ]

    spacetime_rows = []
    for value, count in sorted(time_precision_public.items()):
        spacetime_rows.append({"dimension": "time_precision", "value": value, "public_count": count, "denominator": len(by_id), "unknown": time_precision_public.get("unknown", 0), "unmapped": 0, "held_excluded": len(held_ids), "notes": "Diagnostic classification of raw legacy date label; not a v49 normalized temporal assignment."})
    for value, count in sorted(year_public.items()):
        spacetime_rows.append({"dimension": "date_start_year", "value": value, "public_count": count, "denominator": len(by_id), "unknown": year_public.get("UNKNOWN", 0), "unmapped": 0, "held_excluded": len(held_ids), "notes": "Analysis-only raw start-year distribution; range/approximate precision remains in time_precision."})
    for value, count in sorted(decade_public.items()):
        spacetime_rows.append({"dimension": "date_start_decade", "value": value, "public_count": count, "denominator": len(by_id), "unknown": decade_public.get("UNKNOWN", 0), "unmapped": 0, "held_excluded": len(held_ids), "notes": "Analysis-only decade from raw date_start; not a normalized temporal assignment."})
    for value, count in sorted(place_role_public.items()):
        spacetime_rows.append({"dimension": "authority_geography_role", "value": value, "public_count": count, "denominator": len(by_id), "unknown": place_role_public.get("unregistered_object_region_role", 0), "unmapped": place_coverage, "held_excluded": len(held_ids), "notes": "Authority/source geography role, not creation/publication/subject place role."})
    for value, count in sorted(raw_region_public.items()):
        spacetime_rows.append({"dimension": "raw_region_label_trimmed", "value": value, "public_count": count, "denominator": len(by_id), "unknown": raw_region_public.get("UNKNOWN", 0), "unmapped": place_coverage, "held_excluded": len(held_ids), "notes": "Exact trimmed raw region label; no governed normalization or object-place role; analysis-only."})

    source_stage_rows = [
        {"stage": "public archive object", "total_records": len(by_id), "public_object_coverage": len(by_id), "objects_with_at_least_one": len(by_id), "objects_with_zero": 0, "median_per_object": 1, "p95_per_object": 1, "max_per_object": 1, "stable_id": "public surface stable ID", "public_safe_fields": "stable ID/title in sealed surface", "rights_constraints": "held excluded"},
        {"stage": "raw source record association", "total_records": verifier["countVector"]["provenance_object_source_record"], "public_object_coverage": source_coverage, "objects_with_at_least_one": source_coverage, "objects_with_zero": len(by_id)-source_coverage, "median_per_object": 1, "p95_per_object": 1, "max_per_object": 1, "stable_id": "internal UUID only", "public_safe_fields": "none without serializer", "rights_constraints": "raw payload/URL restricted"},
        {"stage": "normalized source document", "total_records": 0, "public_object_coverage": 0, "objects_with_at_least_one": 0, "objects_with_zero": len(by_id), "median_per_object": 0, "p95_per_object": 0, "max_per_object": 0, "stable_id": "schema UUID; no rows", "public_safe_fields": "none", "rights_constraints": "not populated"},
        {"stage": "assertion", "total_records": 0, "public_object_coverage": 0, "objects_with_at_least_one": 0, "objects_with_zero": len(by_id), "median_per_object": 0, "p95_per_object": 0, "max_per_object": 0, "stable_id": "schema UUID; no rows", "public_safe_fields": "none", "rights_constraints": "not populated"},
        {"stage": "evidence item", "total_records": 0, "public_object_coverage": 0, "objects_with_at_least_one": 0, "objects_with_zero": len(by_id), "median_per_object": 0, "p95_per_object": 0, "max_per_object": 0, "stable_id": "schema UUID; no rows", "public_safe_fields": "none", "rights_constraints": "not populated"},
        {"stage": "locator/citation evidence", "total_records": 0, "public_object_coverage": 0, "objects_with_at_least_one": 0, "objects_with_zero": len(by_id), "median_per_object": 0, "p95_per_object": 0, "max_per_object": 0, "stable_id": "no public evidence IDs", "public_safe_fields": "generic release citation is not object evidence", "rights_constraints": "no object-safe serializer"},
        {"stage": "claim", "total_records": 0, "public_object_coverage": 0, "objects_with_at_least_one": 0, "objects_with_zero": len(by_id), "median_per_object": 0, "p95_per_object": 0, "max_per_object": 0, "stable_id": "schema URN; no rows", "public_safe_fields": "none", "rights_constraints": "not populated"},
        {"stage": "semantic relation", "total_records": 0, "public_object_coverage": 0, "objects_with_at_least_one": 0, "objects_with_zero": len(by_id), "median_per_object": 0, "p95_per_object": 0, "max_per_object": 0, "stable_id": "schema URN; no rows", "public_safe_fields": "none", "rights_constraints": "not populated"},
    ]

    pathological_rows = [
        {
            "stable_id": row["stable_id"],
            "one_hop_nodes": row["one_hop_nodes"],
            "one_hop_edges": row["one_hop_edges"],
            "two_hop_nodes": row["two_hop_nodes"],
            "two_hop_edges": row["two_hop_edges"],
            "capped": str(row["capped"]).lower(),
            "interpretation": "LAYOUT/PERFORMANCE DIAGNOSTIC ONLY; NOT HISTORICAL IMPORTANCE",
        }
        for row in sorted(
            legacy_local,
            key=lambda item: (-item["two_hop_edges"], -item["two_hop_nodes"], -item["one_hop_edges"], item["stable_id"]),
        )[:20]
    ]

    outputs: dict[Path, bytes] = {
        RESEARCH / "03_TRACE_CENSUS.tsv": tsv_bytes(list(census_rows[0]), census_rows),
        RESEARCH / "05_PUBLIC_HELD_TRACE_BOUNDARY.tsv": tsv_bytes(list(boundary_rows[0]), boundary_rows),
        RESEARCH / "06_OBJECT_LOCAL_DENSITY_STATS.tsv": tsv_bytes(list(density_rows[0]), density_rows),
        RESEARCH / "07_NEIGHBORHOOD_CAPACITY.tsv": tsv_bytes(list(neighborhood_rows[0]), neighborhood_rows),
        RESEARCH / "11_THREE_DOMAIN_READINESS_MATRIX.tsv": tsv_bytes(list(readiness_rows[0]), readiness_rows),
        RESEARCH / "12_TRACE_PROGRAMMING_SAMPLE_REGISTER.tsv": tsv_bytes(list(samples[0]), samples),
        RAW / "relationship-count-reconciliation.tsv": tsv_bytes(list(relationship_rows[0]), relationship_rows),
        RAW / "spacetime-distributions.tsv": tsv_bytes(list(spacetime_rows[0]), spacetime_rows),
        RAW / "sources-evidence-stage-counts.tsv": tsv_bytes(list(source_stage_rows[0]), source_stage_rows),
        RAW / "legacy-v48-pathological-public-objects.tsv": tsv_bytes(list(pathological_rows[0]), pathological_rows),
        RAW / "legacy-v48-global-graph-diagnostics.json": json_bytes(legacy_global),
        RAW / "trace-census-summary.json": json_bytes(summary),
        RAW / "input-checksums.json": json_bytes(input_hashes),
    }
    checksum_lines = []
    for path, content in sorted(outputs.items(), key=lambda item: str(item[0].relative_to(ROOT))):
        checksum_lines.append(f"{hashlib.sha256(content).hexdigest()}  {path.relative_to(ROOT)}")
    outputs[AUDIT / "CHECKSUMS.sha256"] = ("\n".join(checksum_lines) + "\n").encode("utf-8")

    package_roots = [
        RESEARCH,
        AUDIT,
        ROOT / "frontend/src/features/trace-v49",
        ROOT / "scripts/trace-v49-analysis",
    ]
    package_paths = {
        path
        for package_root in package_roots
        for path in package_root.rglob("*")
        if path.is_file() and path.name != "PACKAGE_CHECKSUMS.sha256"
    }
    package_paths.add(ROOT / "frontend/scripts/verify-trace-v49-preprogram.mjs")
    package_lines = []
    for path in sorted(package_paths, key=lambda item: str(item.relative_to(ROOT))):
        content = outputs.get(path, path.read_bytes())
        package_lines.append(f"{hashlib.sha256(content).hexdigest()}  {path.relative_to(ROOT)}")
    outputs[AUDIT / "PACKAGE_CHECKSUMS.sha256"] = ("\n".join(package_lines) + "\n").encode("utf-8")

    mismatches = []
    for path, content in outputs.items():
        if args.check:
            if not path.exists() or path.read_bytes() != content:
                mismatches.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    if mismatches:
        raise SystemExit("TRACE statistics drift: " + ", ".join(mismatches))
    print(
        "TRACE_V49_STATS=PASS "
        f"OBJECTS={freeze['objectCount']} PUBLIC={len(eligible_ids)} HELD={len(held_ids)} "
        f"FOLDER_ASSIGNMENTS={freeze['relationshipCount']} SEMANTIC_RELATIONS=0 "
        f"SAMPLES={len(samples)} CHECK={str(args.check).lower()}"
    )


if __name__ == "__main__":
    main()
