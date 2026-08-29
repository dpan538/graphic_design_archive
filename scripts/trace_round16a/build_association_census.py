#!/usr/bin/env python3
"""Build the exhaustive Round 16A pair dispositions and validated graph.

The script is deliberately conservative. Crossref metadata is a discovery
channel, never association evidence. Only frozen, locator-bearing Round 14
evidence can retain an active edge in this round.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import resource
import statistics
import sys
import time
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable


SOURCE_SHA = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e"
DATABASE_SNAPSHOT = "v49:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e"
METHOD_VERSION = "trace-generic-association-rubric-v1-round16a-census-clarification-v2"
FINAL_STATUSES = {
    "ACTIVE_EXTERNALLY_SUPPORTED",
    "ACTIVE_SOURCE_SUPPORTED",
    "INACTIVE_INSUFFICIENT_EVIDENCE",
    "INACTIVE_CONFLICTING_SCOPE",
    "INACTIVE_COOCCURRENCE_ONLY",
    "INACTIVE_HARD_NEGATIVE",
}
ACTIVE_STATUSES = {"ACTIVE_EXTERNALLY_SUPPORTED", "ACTIVE_SOURCE_SUPPORTED"}
STRENGTH_RANK = {"NONE": 0, "WEAK": 1, "MODERATE": 2, "STRONG": 3}
CONFIDENCE_RANK = {"NONE": 0, "LOW": 1, "MODERATE": 2, "HIGH": 3}
REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "docs/audits/v49-exploration-full-space-closure-round1/raw"


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).rstrip(b"\n")).hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


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


def boolish(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def load_queries(path: Path) -> dict[str, dict[str, Any]]:
    queries: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            pair_id = row.get("pair_id")
            if not pair_id or pair_id in queries:
                raise ValueError(f"QUERY_LOG_PAIR_ID:{number}:{pair_id}")
            queries[pair_id] = row
    return queries


def round14_status(row: dict[str, str]) -> str:
    strength_ok = STRENGTH_RANK.get(row["association_strength"], -1) >= STRENGTH_RANK["MODERATE"]
    confidence_ok = CONFIDENCE_RANK.get(row["evidence_confidence"], -1) >= CONFIDENCE_RANK["MODERATE"]
    dimensions_ok = all(int(row[key]) >= 1 for key in ("d1", "d5", "d7"))
    evidence_ok = row["evidence_status"] in {"EXTERNALLY_SUPPORTED", "SOURCE_SUPPORTED"}
    active = strength_ok and confidence_ok and dimensions_ok and evidence_ok and not boolish(row["cooccurrence_only"]) and not boolish(row["hard_negative"])
    if active:
        return "ACTIVE_EXTERNALLY_SUPPORTED" if row["evidence_status"] == "EXTERNALLY_SUPPORTED" else "ACTIVE_SOURCE_SUPPORTED"
    if boolish(row["hard_negative"]):
        return "INACTIVE_HARD_NEGATIVE"
    if boolish(row["cooccurrence_only"]):
        return "INACTIVE_COOCCURRENCE_ONLY"
    # The only Round 14 qualified-scope control is R14-ASSOC-022. Keying
    # against the governed assessment ID avoids semantic keyword inference.
    if row["assessment_id"] == "R14-ASSOC-022":
        return "INACTIVE_CONFLICTING_SCOPE"
    return "INACTIVE_INSUFFICIENT_EVIDENCE"


def components(nodes: list[str], edges: list[dict[str, Any]]) -> list[list[str]]:
    graph = {node: set() for node in nodes}
    for edge in edges:
        a, b = edge["vocabulary_id_a"], edge["vocabulary_id_b"]
        graph[a].add(b)
        graph[b].add(a)
    unseen = set(nodes)
    result: list[list[str]] = []
    while unseen:
        root = min(unseen)
        seen = {root}
        queue = deque([root])
        while queue:
            node = queue.popleft()
            for neighbour in sorted(graph[node] - seen):
                seen.add(neighbour)
                queue.append(neighbour)
        unseen -= seen
        result.append(sorted(seen))
    return sorted(result, key=lambda part: (len(part), part))


def articulation_and_bridges(nodes: list[str], edges: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    graph = {node: set() for node in nodes}
    edge_id: dict[frozenset[str], str] = {}
    for edge in edges:
        a, b = edge["vocabulary_id_a"], edge["vocabulary_id_b"]
        graph[a].add(b)
        graph[b].add(a)
        edge_id[frozenset((a, b))] = edge["association_id"]
    clock = 0
    disc: dict[str, int] = {}
    low: dict[str, int] = {}
    parent: dict[str, str | None] = {}
    cuts: set[str] = set()
    bridges: set[str] = set()

    def visit(node: str) -> None:
        nonlocal clock
        clock += 1
        disc[node] = low[node] = clock
        children = 0
        for neighbour in sorted(graph[node]):
            if neighbour not in disc:
                parent[neighbour] = node
                children += 1
                visit(neighbour)
                low[node] = min(low[node], low[neighbour])
                if parent[node] is None and children > 1:
                    cuts.add(node)
                if parent[node] is not None and low[neighbour] >= disc[node]:
                    cuts.add(node)
                if low[neighbour] > disc[node]:
                    bridges.add(edge_id[frozenset((node, neighbour))])
            elif neighbour != parent[node]:
                low[node] = min(low[node], disc[neighbour])

    for node in sorted(nodes):
        if node not in disc:
            parent[node] = None
            visit(node)
    return sorted(cuts), sorted(bridges)


def main() -> int:
    script_started = time.perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument("--active-vocabulary", type=Path, default=RAW / "active-vocabulary-v2.json")
    parser.add_argument("--pair-universe", type=Path, default=RAW / "pair-universe-v2.tsv")
    parser.add_argument("--query-log", type=Path, default=RAW / "association-query-log-v2.jsonl")
    args = parser.parse_args()

    active_package = json.loads(args.active_vocabulary.read_text(encoding="utf-8"))
    vocabulary = active_package["active_vocabulary"]
    if active_package["active_vocabulary_count"] != 31 or len(vocabulary) != 31:
        raise ValueError("ACTIVE_VOCABULARY_COUNT")
    by_label = {row["canonical_label"].casefold(): row for row in vocabulary}
    by_id = {row["vocabulary_id"]: row for row in vocabulary}
    if len(by_label) != 31 or len(by_id) != 31:
        raise ValueError("ACTIVE_VOCABULARY_UNIQUENESS")

    pairs = read_tsv(args.pair_universe)
    if len(pairs) != 465:
        raise ValueError(f"PAIR_COUNT:{len(pairs)}")
    pair_by_key: dict[str, dict[str, str]] = {}
    for row in pairs:
        expected = "|".join(sorted((row["vocabulary_id_a"], row["vocabulary_id_b"])))
        if row["canonical_pair_key"] != expected or expected in pair_by_key:
            raise ValueError(f"PAIR_CANONICAL_ID:{row.get('pair_id')}")
        pair_by_key[expected] = row

    queries = load_queries(args.query_log)
    if set(queries) != {row["pair_id"] for row in pairs}:
        missing = sorted({row["pair_id"] for row in pairs} - set(queries))
        extra = sorted(set(queries) - {row["pair_id"] for row in pairs})
        raise ValueError(f"QUERY_LOG_COVERAGE:missing={missing[:3]}:extra={extra[:3]}")

    r14_path = REPO / "docs/audits/v49-exploration-association-calibration-round1/raw/association-calibration.tsv"
    r14_evidence_path = REPO / "docs/audits/v49-exploration-association-calibration-round1/raw/evidence-provenance.tsv"
    r14 = read_tsv(r14_path)
    r14_evidence = read_tsv(r14_evidence_path)
    evidence_by_assessment: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in r14_evidence:
        evidence_by_assessment[row["assessment_id"]].append(row)

    r14_by_active_pair: dict[str, dict[str, str]] = {}
    reconciliation: list[dict[str, Any]] = []
    for row in r14:
        a = by_label.get(row["node_a"].casefold())
        b = by_label.get(row["node_b"].casefold())
        status = round14_status(row)
        if a and b:
            key = "|".join(sorted((a["vocabulary_id"], b["vocabulary_id"])))
            if key in r14_by_active_pair:
                raise ValueError(f"ROUND14_DUPLICATE_ACTIVE_PAIR:{row['assessment_id']}")
            r14_by_active_pair[key] = row
            pair_id = pair_by_key[key]["pair_id"]
            endpoint_disposition = "BOTH_ENDPOINTS_ACTIVE"
        else:
            pair_id = ""
            endpoint_disposition = "ENDPOINT_OUTSIDE_FINAL_ACTIVE_VOCABULARY"
        reconciliation.append({
            "assessment_id": row["assessment_id"],
            "node_a": row["node_a"],
            "node_b": row["node_b"],
            "round14_status": status,
            "round16a_pair_id": pair_id,
            "endpoint_disposition": endpoint_disposition,
            "decision_reconciliation": "PRESERVED",
            "new_evidence_changed_decision": False,
            "method_changed_decision": False,
            "explanation": "The Round 14 disposition is preserved; inactive endpoints remain governed vocabulary-census controls rather than entering the active pair universe." if not pair_id else "The governed Round 14 disposition maps directly to the exhaustive Round 16A pair row.",
        })
    if len(r14) != 35 or len(r14_by_active_pair) != 31:
        raise ValueError(f"ROUND14_RECONCILIATION:{len(r14)}:{len(r14_by_active_pair)}")

    census: list[dict[str, Any]] = []
    evidence_ledger: list[dict[str, Any]] = []
    for pair in sorted(pairs, key=lambda row: row["pair_id"]):
        key = pair["canonical_pair_key"]
        governed = r14_by_active_pair.get(key)
        query = queries[pair["pair_id"]]
        candidates = query.get("candidate_results", [])
        if not isinstance(candidates, list):
            raise ValueError(f"QUERY_CANDIDATES:{pair['pair_id']}")
        if governed:
            status = round14_status(governed)
            assessment_id = governed["assessment_id"]
            strength = governed["association_strength"]
            confidence = governed["evidence_confidence"]
            evidence_status = governed["evidence_status"]
            dvalues = {f"d{index}": int(governed[f"d{index}"]) for index in range(1, 8)}
            evidence_refs = sorted(filter(None, governed["evidence_refs"].split(";")))
            qualification = governed["qualification"]
            if status == "ACTIVE_SOURCE_SUPPORTED":
                qualification = (
                    "Final source-supported case under the Round 16A bounded-source policy: locator-bearing governed source evidence is sufficient for generic proximity; "
                    "no typed, causal, directional, or universal historical relation is claimed."
                )
            reason = governed["decision_reason"]
            historical_scope = governed["historical_scope"]
            context_scope = governed["context_scope"]
        else:
            status = "INACTIVE_INSUFFICIENT_EVIDENCE"
            assessment_id = ""
            strength = confidence = evidence_status = "NONE"
            dvalues = {f"d{index}": 0 for index in range(1, 8)}
            evidence_refs = []
            qualification = "No qualifying association evidence was found under the documented protocol; this is not a claim that no historical relationship exists."
            reason = "Frozen evidence registries contain no qualifying locator-bearing association evidence, and Crossref discovery metadata was not treated as source text."
            historical_scope = "UNESTABLISHED"
            context_scope = "UNESTABLISHED"
        if status not in FINAL_STATUSES:
            raise ValueError(f"FINAL_STATUS:{pair['pair_id']}:{status}")
        row: dict[str, Any] = {
            **pair,
            "final_status": status,
            "active": status in ACTIVE_STATUSES,
            "round14_assessment_id": assessment_id,
            "method_version": METHOD_VERSION,
            "association_strength": strength,
            "evidence_confidence": confidence,
            "evidence_status": evidence_status,
            **dvalues,
            "cooccurrence_only": boolish(governed["cooccurrence_only"]) if governed else False,
            "hard_negative": boolish(governed["hard_negative"]) if governed else False,
            "historical_scope": historical_scope,
            "context_scope": context_scope,
            "qualification": qualification,
            "decision_reason": reason,
            "accepted_evidence_refs": evidence_refs,
            "external_query_id": query["query_id"],
            "external_result_count": int(query.get("result_count", len(candidates))),
            "external_accepted_source_ids": query.get("accepted_source_ids", []),
            "external_rejected_source_ids": query.get("rejected_source_ids", []),
            "database_text_cooccurrence_used": False,
            "database_metadata_relation_inferred": False,
            "typed_relation_emitted": False,
            "causal_relation_emitted": False,
            "directional_relation_emitted": False,
        }
        census.append(row)

        if governed:
            for evidence in sorted(evidence_by_assessment[assessment_id], key=lambda item: item["evidence_id"]):
                evidence_ledger.append({
                    "ledger_id": f"R16A-{evidence['evidence_id']}",
                    "pair_id": pair["pair_id"],
                    "evidence_channel": evidence["evidence_channel"],
                    "source_id": evidence["source_id"],
                    "source_kind": evidence["source_kind"],
                    "creator": evidence["creator"],
                    "year": evidence["year"],
                    "title": evidence["title"],
                    "locator": evidence["locator"],
                    "stable_url": evidence["stable_url"],
                    "doi": evidence["doi"],
                    "domain_alignment": evidence["domain_alignment"],
                    "review_disposition": "ACCEPTED_GOVERNED_EVIDENCE" if evidence["evidence_verified"] == "true" else "REJECTED_NOT_VERIFIED",
                    "rejection_reason": "" if evidence["evidence_verified"] == "true" else "FROZEN_EVIDENCE_NOT_VERIFIED",
                    "supports_active_edge": status in ACTIVE_STATUSES and evidence["evidence_verified"] == "true",
                    "association_context": evidence["association_context"],
                    "source_metadata_verified": evidence["source_metadata_verified"],
                    "evidence_verified": evidence["evidence_verified"],
                })
        for index, candidate in enumerate(candidates, 1):
            source_id = candidate.get("candidate_source_id") or candidate.get("doi") or f"RESULT-{index:02d}"
            title = candidate.get("title", "")
            if isinstance(title, list):
                title = "; ".join(str(item) for item in title)
            evidence_ledger.append({
                "ledger_id": f"R16A-{pair['pair_id']}-XREF-{index:02d}",
                "pair_id": pair["pair_id"],
                "evidence_channel": "CROSSREF_DISCOVERY_METADATA",
                "source_id": source_id,
                "source_kind": candidate.get("type", ""),
                "creator": "; ".join(
                    " ".join(filter(None, (str(author.get("given", "")), str(author.get("family", ""))))).strip()
                    for author in candidate.get("authors", []) if isinstance(author, dict)
                ),
                "year": "",
                "title": title,
                "locator": "",
                "stable_url": candidate.get("url", ""),
                "doi": candidate.get("doi", ""),
                "domain_alignment": "NOT_TEXT_VERIFIED",
                "review_disposition": "REJECTED_METADATA_ONLY_NOT_EVIDENCE",
                "rejection_reason": "RESULT_METADATA_AND_SNIPPETS_ARE_NOT_LOCATOR_BEARING_SOURCE_TEXT",
                "supports_active_edge": False,
                "association_context": "",
                "source_metadata_verified": True,
                "evidence_verified": False,
            })

    if len(census) != 465 or len({row["pair_id"] for row in census}) != 465:
        raise ValueError("CENSUS_COMPLETENESS")
    status_counts = Counter(row["final_status"] for row in census)
    if sum(status_counts.values()) != 465 or status_counts["ACTIVE_EXTERNALLY_SUPPORTED"] != 18 or status_counts["ACTIVE_SOURCE_SUPPORTED"] != 3:
        raise ValueError(f"CENSUS_RECONCILIATION:{dict(status_counts)}")

    pair_census_finished = time.perf_counter()
    graph_build_started = pair_census_finished
    active_edges: list[dict[str, Any]] = []
    for row in census:
        if not row["active"]:
            continue
        a, b = by_id[row["vocabulary_id_a"]], by_id[row["vocabulary_id_b"]]
        active_edges.append({
            "association_id": row["pair_id"],
            "round14_assessment_id": row["round14_assessment_id"],
            "vocabulary_id_a": row["vocabulary_id_a"],
            "vocabulary_id_b": row["vocabulary_id_b"],
            "label_a": row["label_a"],
            "label_b": row["label_b"],
            "support_status": row["final_status"],
            "strength": row["association_strength"],
            "confidence": row["evidence_confidence"],
            "d1": row["d1"], "d5": row["d5"], "d7": row["d7"],
            "qualification": row["qualification"],
            "evidence_refs": row["accepted_evidence_refs"],
            "shared_category_ids": sorted(set(a["category_ids"]) & set(b["category_ids"])),
        })
    if len(active_edges) != 21:
        raise ValueError("ACTIVE_EDGE_COUNT")

    node_ids = sorted(by_id)
    degree = Counter({node: 0 for node in node_ids})
    for edge in active_edges:
        degree[edge["vocabulary_id_a"]] += 1
        degree[edge["vocabulary_id_b"]] += 1
    component_rows = components(node_ids, active_edges)
    cuts, bridges = articulation_and_bridges(node_ids, active_edges)
    degree_values = sorted(degree.values())
    density = 2 * len(active_edges) / (len(node_ids) * (len(node_ids) - 1))
    graph_stats = {
        "schema_version": "trace-exploration-graph-statistics-v2",
        "database_snapshot": DATABASE_SNAPSHOT,
        "graph_node_count": len(node_ids),
        "graph_edge_count": len(active_edges),
        "graph_density": density,
        "degree_min": min(degree_values),
        "degree_max": max(degree_values),
        "degree_mean": statistics.fmean(degree_values),
        "degree_median": statistics.median(degree_values),
        "degree_distribution": dict(sorted(Counter(map(str, degree_values)).items(), key=lambda item: int(item[0]))),
        "connected_component_count": len(component_rows),
        "connected_component_size_distribution": dict(sorted(Counter(map(lambda part: str(len(part)), component_rows)).items(), key=lambda item: int(item[0]))),
        "components": component_rows,
        "isolated_active_node_count": sum(value == 0 for value in degree_values),
        "within_category_edge_count": sum(bool(edge["shared_category_ids"]) for edge in active_edges),
        "cross_category_edge_count": sum(not edge["shared_category_ids"] for edge in active_edges),
        "externally_supported_edge_count": status_counts["ACTIVE_EXTERNALLY_SUPPORTED"],
        "source_supported_edge_count": status_counts["ACTIVE_SOURCE_SUPPORTED"],
        "strength_distribution": dict(sorted(Counter(edge["strength"] for edge in active_edges).items())),
        "confidence_distribution": dict(sorted(Counter(edge["confidence"] for edge in active_edges).items())),
        "articulation_point_ids": cuts,
        "bridge_association_ids": bridges,
        "centrality_non_claim": "Graph centrality is a computational property of the governed evidence-qualified graph, not historical importance.",
    }
    graph = {
        "schema_version": "trace-exploration-validated-association-graph-v2",
        "source_sha": SOURCE_SHA,
        "database_snapshot": DATABASE_SNAPSHOT,
        "method_version": METHOD_VERSION,
        "frozen": True,
        "nodes": [{
            "vocabulary_id": row["vocabulary_id"],
            "canonical_label": row["canonical_label"],
            "category_ids": row["category_ids"],
            "isolated": degree[row["vocabulary_id"]] == 0,
            "degree": degree[row["vocabulary_id"]],
        } for row in sorted(vocabulary, key=lambda item: item["vocabulary_id"])],
        "edges": sorted(active_edges, key=lambda item: item["association_id"]),
        "graph_hash": "",
    }
    graph["graph_hash"] = digest({key: graph[key] for key in ("schema_version", "source_sha", "database_snapshot", "method_version", "frozen", "nodes", "edges")})
    graph_build_finished = time.perf_counter()

    tsv_fields = [
        "pair_id", "vocabulary_id_a", "vocabulary_id_b", "label_a", "label_b", "canonical_pair_key",
        "final_status", "active", "round14_assessment_id", "method_version", "association_strength",
        "evidence_confidence", "evidence_status", "d1", "d2", "d3", "d4", "d5", "d6", "d7",
        "cooccurrence_only", "hard_negative", "historical_scope", "context_scope", "qualification",
        "decision_reason", "accepted_evidence_refs", "external_query_id", "external_result_count",
        "external_accepted_source_ids", "external_rejected_source_ids", "database_text_cooccurrence_used",
        "database_metadata_relation_inferred", "typed_relation_emitted", "causal_relation_emitted", "directional_relation_emitted",
    ]
    evidence_fields = [
        "ledger_id", "pair_id", "evidence_channel", "source_id", "source_kind", "creator", "year", "title",
        "locator", "stable_url", "doi", "domain_alignment", "review_disposition", "rejection_reason",
        "supports_active_edge", "association_context", "source_metadata_verified", "evidence_verified",
    ]
    artifact_write_started = time.perf_counter()
    write_tsv(RAW / "association-census-v2.tsv", census, tsv_fields)
    write_tsv(RAW / "association-evidence-ledger-v2.tsv", evidence_ledger, evidence_fields)
    (RAW / "association-census-v2.json").write_bytes(canonical_json({
        "schema_version": "trace-exploration-association-census-v2",
        "source_sha": SOURCE_SHA,
        "database_snapshot": DATABASE_SNAPSHOT,
        "method_version": METHOD_VERSION,
        "pair_count": 465,
        "status_counts": dict(sorted(status_counts.items())),
        "unresolved_pair_count": 0,
        "active_association_with_pending_validation_count": 0,
        "round14_reconciliation": reconciliation,
        "pairs": census,
        "census_hash": digest(census),
    }))
    (RAW / "validated-association-graph-v2.json").write_bytes(canonical_json(graph))
    (RAW / "graph-statistics-v2.json").write_bytes(canonical_json(graph_stats))
    (RAW / "association-build-summary-v2.json").write_bytes(canonical_json({
        "schema_version": "trace-exploration-association-build-summary-v2",
        "timing_evidence": "execution-events.jsonl",
        "pair_count": len(census),
        "evidence_ledger_count": len(evidence_ledger),
        "graph_node_count": len(node_ids),
        "graph_edge_count": len(active_edges),
    }))
    artifact_write_finished = time.perf_counter()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    peak_rss = int(usage.ru_maxrss if sys.platform == "darwin" else usage.ru_maxrss * 1024)
    (RAW / "association-build-performance-v2.json").write_bytes(canonical_json({
        "schema_version": "trace-exploration-association-build-performance-v2",
        "measurement_scope": "offline association census and graph builder process",
        "timing_values_are_nondeterministic": True,
        "pair_census_duration_ms": round((pair_census_finished - script_started) * 1000, 3),
        "graph_build_duration_ms": round((graph_build_finished - graph_build_started) * 1000, 3),
        "artifact_serialization_duration_ms": round((artifact_write_finished - artifact_write_started) * 1000, 3),
        "total_duration_ms": round((artifact_write_finished - script_started) * 1000, 3),
        "peak_rss_bytes": peak_rss,
        "cpu_user_ms": round(usage.ru_utime * 1000, 3),
        "cpu_system_ms": round(usage.ru_stime * 1000, 3),
        "temporary_storage_bytes": 0,
    }))
    print(json.dumps({
        "pair_count": len(census),
        "status_counts": dict(sorted(status_counts.items())),
        "evidence_ledger_count": len(evidence_ledger),
        "graph_node_count": len(node_ids),
        "graph_edge_count": len(active_edges),
        "connected_component_count": len(component_rows),
        "isolated_active_node_count": graph_stats["isolated_active_node_count"],
        "graph_hash": graph["graph_hash"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
