#!/usr/bin/env python3
"""Read-only verifier for the v49 authority/research-delta checkpoint."""

from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import sqlite3
import sys
import uuid
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/audits/v49-authority-research-delta"

FROZEN_ASSETS = {
    "generated/public_surfaces_prefreeze_candidate_v48.json": {
        "bytes": 190_067_852,
        "sha256": "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48",
    },
    "data/prefreeze_candidate_v48.sqlite": {
        "bytes": 421_801_984,
        "sha256": "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e",
    },
    "generated/prefreeze_candidate_v48_transfer_manifest.json": {
        "bytes": 21_752,
        "sha256": "865358db84c15d960b3535969a32521c0ffec177f7455d21db86cd131f787d5b",
    },
    "data/prefreeze_candidate_v48_transfer_manifest.csv": {
        "bytes": 12_861,
        "sha256": "694a60657077bcab8888c4a4ef1daf6059706e544606d4862e46c57dcf6ddc18",
    },
    "frontend/public/data/trace-v48/manifest.json": {
        "bytes": 83_900,
        "sha256": "1678e211023aa324078e0478f88670d2378b6dc5c398cc5c04722605038fee23",
    },
}

EXPECTED_COUNTS = {
    "activeObjects": 15_923,
    "traceNodes": 97_889,
    "traceEdges": 255_695,
    "activeMemberships": 126_822,
    "activeTrees": 30,
    "activeRelationTypes": 20,
    "reviewObjects": 4_425,
    "auxiliaryObjects": 11,
    "influenceEdges": 0,
    "traceAssets": 580,
    "traceShards": 576,
    "searchItems": 8_636,
}

REQUIRED_AUDIT_FILES = [
    "00_EXECUTIVE_RECEIPT.md",
    "01_SCOPED_AUTHORITY_MATRIX.md",
    "02_PARENT_ASSET_DEPENDENCY_LEDGER.tsv",
    "03_GRAPH_FACT_CLASSIFICATION_RULES.json",
    "04_GRAPH_FACT_RECONCILIATION.json",
    "05_METADATA_SUPPORTED_RECONCILIATION.md",
    "05_METADATA_SUPPORTED_SYMMETRIC_DIFF.tsv",
    "06_RAW_SOURCE_EVIDENCE_DISPOSITION.tsv",
    "07_RAW_SOURCE_EVIDENCE_SUMMARY.json",
    "08_EPISTEMIC_RELATION_REGISTRY.json",
    "09_RESEARCH_CORPUS_POLICY.md",
    "10_CORPUS_MEMBERSHIP_BASELINE.tsv",
    "11_MISSINGNESS_BASELINE.json",
    "12_TRACE_PROJECTION_DELTA.md",
    "13_AUTHORITY_RESEARCH_GATE_RECEIPT.md",
    "AGENT_TASK_REGISTER.md",
    "MANIFEST.json",
    "CHECKSUMS.sha256",
]

HASH_CHUNK = 1024 * 1024
_HASH_CACHE: dict[Path, tuple[int, str]] = {}


def sha256_file(path: Path) -> tuple[int, str]:
    path = path.resolve()
    cached = _HASH_CACHE.get(path)
    if cached is not None:
        return cached
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(HASH_CHUNK)
            if not chunk:
                break
            size += len(chunk)
            digest.update(chunk)
    result = (size, digest.hexdigest())
    _HASH_CACHE[path] = result
    return result


def line_set_hash(values: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for value in sorted(set(values)):
        digest.update(value.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path, *, strict: bool = True) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        if strict:
            return json.load(handle, object_pairs_hook=strict_object)
        return json.load(handle)


def load_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        header = list(reader.fieldnames or [])
        if not header or len(header) != len(set(header)):
            raise ValueError(f"invalid or duplicate TSV header: {path}")
        rows = list(reader)
    if any(None in row for row in rows):
        raise ValueError(f"inconsistent TSV field count: {path}")
    return header, rows


class Receipt:
    def __init__(self) -> None:
        self.checks: dict[str, dict[str, Any]] = {}
        self.metrics: dict[str, Any] = {}
        self.set_hashes: dict[str, str] = {}
        self.errors: list[str] = []

    def check(
        self,
        name: str,
        actual: Any,
        expected: Any,
        *,
        detail: str | None = None,
    ) -> bool:
        passed = actual == expected
        entry: dict[str, Any] = {
            "actual": self._jsonable(actual),
            "expected": self._jsonable(expected),
            "pass": passed,
        }
        if detail:
            entry["detail"] = detail
        self.checks[name] = entry
        if not passed:
            self.errors.append(f"{name}: expected {expected!r}, got {actual!r}")
        return passed

    @staticmethod
    def _jsonable(value: Any) -> Any:
        if isinstance(value, set):
            string_values = {str(item) for item in value}
            return {"count": len(value), "sha256": line_set_hash(string_values)}
        if isinstance(value, tuple):
            return [Receipt._jsonable(item) for item in value]
        if isinstance(value, list):
            return [Receipt._jsonable(item) for item in value]
        if isinstance(value, dict):
            return {str(key): Receipt._jsonable(item) for key, item in value.items()}
        if isinstance(value, Path):
            return value.as_posix()
        return value

    def require(self, name: str, passed: bool, *, detail: str) -> bool:
        self.checks[name] = {"pass": bool(passed), "detail": detail}
        if not passed:
            self.errors.append(f"{name}: {detail}")
        return passed


def verify_frozen_assets(receipt: Receipt) -> None:
    for relative, expected in FROZEN_ASSETS.items():
        path = ROOT / relative
        receipt.require(
            f"frozen.exists:{relative}", path.is_file(), detail="frozen asset must exist"
        )
        if not path.is_file():
            continue
        size, digest = sha256_file(path)
        receipt.check(f"frozen.bytes:{relative}", size, expected["bytes"])
        receipt.check(f"frozen.sha256:{relative}", digest, expected["sha256"])


def verify_transfer_manifest(receipt: Receipt) -> None:
    path = ROOT / "generated/prefreeze_candidate_v48_transfer_manifest.json"
    manifest = load_json(path)
    files = manifest.get("files")
    receipt.check("transfer_manifest.files", len(files or []), 65)
    receipt.check("transfer_manifest.activeObjectCount", manifest.get("activeObjectCount"), 15_923)
    failures: list[str] = []
    seen: set[str] = set()
    for item in files or []:
        relative = item.get("path")
        if not isinstance(relative, str) or relative in seen:
            failures.append(str(relative))
            continue
        seen.add(relative)
        target = ROOT / relative
        if not target.is_file():
            failures.append(relative)
            continue
        size, digest = sha256_file(target)
        if size != item.get("bytes") or digest != item.get("sha256"):
            failures.append(relative)
    receipt.check("transfer_manifest.declared_asset_failures", failures, [])


def candidate_measurement(receipt: Receipt) -> dict[str, Any]:
    path = ROOT / "generated/public_surfaces_prefreeze_candidate_v48.json"
    payload = load_json(path, strict=False)
    surfaces = payload.get("surfaces")
    receipt.require(
        "candidate.surfaces_is_array",
        isinstance(surfaces, list),
        detail="top-level surfaces must be an array",
    )
    if not isinstance(surfaces, list):
        return {}

    surface_ids: list[str] = []
    source_record_ids: list[str] = []
    object_node_ids: list[str] = []
    edge_ids: list[str] = []
    edge_labels: list[str] = []
    tree_ids: list[str] = []
    metadata_ids: set[str] = set()
    tier_counts: Counter[str] = Counter()
    state_counts: Counter[str] = Counter()
    review_state_counts: Counter[str] = Counter()
    influence_state_counts: Counter[str] = Counter()
    edge_zip_mismatch = 0
    edge_count_mismatch = 0
    rows: dict[str, dict[str, Any]] = {}
    bad_rows = 0
    namespace = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")
    object_uuids: set[str] = set()

    for index, surface in enumerate(surfaces):
        try:
            surface_id = surface["surfaceId"]
            source_record_id = surface["sourceRecordId"]
            trace = surface["trace"]
            tier = trace.get("tier") or ""
            state = trace["state"]
            review_state = trace["reviewState"]
            influence_state = trace["influenceState"]
            tree_id = trace["treeId"]
            object_node_id = trace["objectNodeId"]
            row_edge_ids = trace["edgeIds"]
            row_edge_labels = trace["edgeLabels"]
            declared_edge_count = trace["edgeCount"]
            if not all(isinstance(value, str) and value for value in (
                surface_id,
                source_record_id,
                state,
                review_state,
                influence_state,
                tree_id,
                object_node_id,
            )):
                raise ValueError("blank required identifier/state")
            if not isinstance(row_edge_ids, list) or not isinstance(row_edge_labels, list):
                raise ValueError("TRACE edge fields are not arrays")
        except (KeyError, TypeError, ValueError):
            bad_rows += 1
            continue

        surface_ids.append(surface_id)
        source_record_ids.append(source_record_id)
        object_node_ids.append(object_node_id)
        edge_ids.extend(row_edge_ids)
        edge_labels.extend(row_edge_labels)
        tree_ids.append(tree_id)
        tier_counts[tier] += 1
        state_counts[state] += 1
        review_state_counts[review_state] += 1
        influence_state_counts[influence_state] += 1
        if tier == "metadata_supported":
            metadata_ids.add(surface_id)
        if len(row_edge_ids) != len(row_edge_labels):
            edge_zip_mismatch += 1
        if declared_edge_count != len(row_edge_ids):
            edge_count_mismatch += 1
        object_uuid = uuid.uuid5(
            namespace,
            "https://modern-gd-history.example/identity/v49/v48/surface/" + surface_id,
        )
        object_uuids.add(str(object_uuid))
        rows[surface_id] = {
            "sourceRecordId": source_record_id,
            "ordinal": index + 1,
            "tier": tier,
            "state": state,
            "reviewState": review_state,
            "influenceState": influence_state,
            "treeId": tree_id,
            "objectNodeId": object_node_id,
            "edgeCount": declared_edge_count,
        }

    receipt.check("candidate.rows", len(surfaces), 15_923)
    receipt.check("candidate.bad_rows", bad_rows, 0)
    receipt.check("candidate.unique_surface_ids", len(set(surface_ids)), 15_923)
    receipt.check("candidate.unique_source_record_ids", len(set(source_record_ids)), 15_923)
    receipt.check("candidate.unique_object_node_ids", len(set(object_node_ids)), 15_923)
    receipt.check("candidate.baseline_uuidv5_objects", len(object_uuids), 15_923)
    receipt.check(
        "candidate.tier_counts",
        dict(sorted(tier_counts.items())),
        {"": 4_957, "metadata_supported": 2_971, "source_verified": 7_995},
    )
    receipt.check("candidate.trace_state_counts", dict(state_counts), {"accepted": 15_923})
    receipt.check("candidate.edge_id_occurrences", len(edge_ids), 126_822)
    receipt.check("candidate.unique_edge_ids", len(set(edge_ids)), 126_822)
    receipt.check("candidate.edge_label_occurrences", len(edge_labels), 79_683)
    receipt.check("candidate.relation_label_types", len(set(edge_labels)), 20)
    receipt.check("candidate.edge_count_mismatch_rows", edge_count_mismatch, 0)
    receipt.check("candidate.edge_label_zip_mismatch_rows", edge_zip_mismatch, 9_393)
    receipt.check("candidate.research_trees", len(set(tree_ids)), 30)
    receipt.check(
        "candidate.metadata_meta_scalar",
        payload.get("meta", {}).get("traceMetadataSupportedCount"),
        2_970,
    )
    receipt.check("candidate.metadata_row_count", len(metadata_ids), 2_971)
    receipt.check("candidate.automatic_influence_inference", influence_state_counts.get("inferred", 0), 0)

    receipt.metrics.update(
        {
            "LEGACY_INPUT_SURFACES": len(surfaces),
            "ACCOUNTED_INPUT_SURFACES": len(surface_ids),
            "UNACCOUNTED_INPUT_SURFACES": len(surfaces) - len(surface_ids),
            "BASELINE_ARCHIVE_OBJECTS": len(object_uuids),
            "candidateExplicitSourceVerified": tier_counts["source_verified"],
            "candidateMissingTier": tier_counts[""],
            "candidateMetadataSupported": tier_counts["metadata_supported"],
            "candidateEdgeLabelZipMismatchRows": edge_zip_mismatch,
        }
    )
    receipt.set_hashes.update(
        {
            "candidateSurfaceIds": line_set_hash(surface_ids),
            "candidateSourceRecordIds": line_set_hash(source_record_ids),
            "candidateObjectNodeIds": line_set_hash(object_node_ids),
            "candidateEdgeIds": line_set_hash(edge_ids),
            "candidateRelationLabels": line_set_hash(edge_labels),
            "candidateMetadataSupportedSurfaceIds": line_set_hash(metadata_ids),
            "baselineArchiveObjectUuidv5": line_set_hash(object_uuids),
        }
    )

    del payload
    del surfaces
    gc.collect()
    return {
        "surfaceIds": set(surface_ids),
        "sourceRecordIds": set(source_record_ids),
        "objectNodeIds": set(object_node_ids),
        "edgeIds": set(edge_ids),
        "relationLabels": set(edge_labels),
        "metadataIds": metadata_ids,
        "rows": rows,
    }


def sqlite_measurement(receipt: Receipt, candidate: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / "data/prefreeze_candidate_v48.sqlite"
    uri = f"file:{path.as_posix()}?mode=ro&immutable=1"
    connection = sqlite3.connect(uri, uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
        receipt.check("sqlite.integrity_check", integrity, ["ok"])

        object_rows = list(
            connection.execute(
                "SELECT surface_id, source_record_id, trace_object_node_id, trace_tier, trace_state "
                "FROM objects WHERE count_eligible=1 ORDER BY surface_id"
            )
        )
        sqlite_surface_ids = {row[0] for row in object_rows}
        sqlite_source_ids = {row[1] for row in object_rows}
        sqlite_node_ids = {row[2] for row in object_rows}
        sqlite_tiers = Counter(row[3] for row in object_rows)
        sqlite_states = Counter(row[4] for row in object_rows)
        sqlite_metadata_ids = {row[0] for row in object_rows if row[3] == "metadata_supported"}
        membership_edge_ids = {
            row[0]
            for row in connection.execute("SELECT edge_id FROM object_trace_edges ORDER BY edge_id")
        }
        active_labels = {
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT e.edge_label FROM object_trace_edges m "
                "JOIN trace_edges e ON e.edge_id=m.edge_id ORDER BY e.edge_label"
            )
        }
        active_trees = {
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT e.tree_id FROM object_trace_edges m "
                "JOIN trace_edges e ON e.edge_id=m.edge_id ORDER BY e.tree_id"
            )
        }

        scalar_queries = {
            "sqlite.active_objects": "SELECT COUNT(*) FROM objects WHERE count_eligible=1",
            "sqlite.trace_nodes": "SELECT COUNT(*) FROM trace_nodes",
            "sqlite.trace_edges": "SELECT COUNT(*) FROM trace_edges",
            "sqlite.active_memberships": "SELECT COUNT(*) FROM object_trace_edges",
            "sqlite.review_objects": "SELECT COUNT(*) FROM authority_review_objects_current",
            "sqlite.influence_edges": "SELECT COUNT(*) FROM trace_edges WHERE edge_label='influenced_by'",
            "sqlite.influence_memberships": (
                "SELECT COUNT(*) FROM object_trace_edges m JOIN trace_edges e ON e.edge_id=m.edge_id "
                "WHERE e.edge_label='influenced_by'"
            ),
        }
        expected = {
            "sqlite.active_objects": 15_923,
            "sqlite.trace_nodes": 97_889,
            "sqlite.trace_edges": 255_695,
            "sqlite.active_memberships": 126_822,
            "sqlite.review_objects": 4_425,
            "sqlite.influence_edges": 0,
            "sqlite.influence_memberships": 0,
        }
        for name, query in scalar_queries.items():
            value = connection.execute(query).fetchone()[0]
            receipt.check(name, value, expected[name])
    finally:
        connection.close()

    receipt.check("sqlite.active_tree_types", len(active_trees), 30)
    receipt.check("sqlite.active_relation_types", len(active_labels), 20)
    receipt.check(
        "sqlite.trace_tier_counts",
        dict(sorted(sqlite_tiers.items())),
        {"metadata_supported": 2_971, "source_verified": 12_952},
    )
    receipt.check("sqlite.trace_state_counts", dict(sqlite_states), {"accepted": 15_923})
    receipt.check("reconcile.candidate_sqlite_surface_ids", sqlite_surface_ids, candidate["surfaceIds"])
    receipt.check("reconcile.candidate_sqlite_source_record_ids", sqlite_source_ids, candidate["sourceRecordIds"])
    receipt.check("reconcile.candidate_sqlite_object_node_ids", sqlite_node_ids, candidate["objectNodeIds"])
    receipt.check("reconcile.candidate_sqlite_membership_edge_ids", membership_edge_ids, candidate["edgeIds"])
    receipt.check("reconcile.candidate_sqlite_active_relation_labels", active_labels, candidate["relationLabels"])
    receipt.check("reconcile.candidate_sqlite_metadata_ids", sqlite_metadata_ids, candidate["metadataIds"])
    receipt.set_hashes["sqliteMetadataSupportedSurfaceIds"] = line_set_hash(sqlite_metadata_ids)
    receipt.metrics["derivedSqliteSourceVerified"] = sqlite_tiers["source_verified"]
    return {"metadataIds": sqlite_metadata_ids}


def verify_read_products(receipt: Receipt, candidate: dict[str, Any], sqlite_data: dict[str, Any]) -> None:
    search = load_json(ROOT / "frontend/public/data/archive-search-v1.json")
    search_schema = search["schema"]
    search_id_index = search_schema.index("surfaceId")
    search_ids = {item[search_id_index] for item in search["items"]}
    receipt.check("search.count_scalar", search.get("count"), 8_636)
    receipt.check("search.items", len(search["items"]), 8_636)
    receipt.check("search.unique_ids", len(search_ids), 8_636)

    catalog = load_json(ROOT / "frontend/public/data/trace-v48/catalog.json")
    catalog_schema = catalog["schema"]
    catalog_id_index = catalog_schema.index("id")
    catalog_tier_index = catalog_schema.index("tier")
    tier_dictionary = catalog["dictionaries"]["tier"]
    catalog_ids = {item[catalog_id_index] for item in catalog["items"]}
    catalog_metadata_ids = {
        item[catalog_id_index]
        for item in catalog["items"]
        if tier_dictionary[item[catalog_tier_index]] == "metadata_supported"
    }
    receipt.check("trace.catalog_items", len(catalog["items"]), 15_923)
    receipt.check("trace.catalog_unique_ids", len(catalog_ids), 15_923)
    receipt.check("reconcile.candidate_catalog_ids", catalog_ids, candidate["surfaceIds"])
    receipt.check("reconcile.candidate_catalog_metadata_ids", catalog_metadata_ids, candidate["metadataIds"])
    receipt.check("reconcile.sqlite_catalog_metadata_ids", catalog_metadata_ids, sqlite_data["metadataIds"])

    intersection = search_ids & candidate["surfaceIds"]
    search_only = search_ids - candidate["surfaceIds"]
    candidate_only = candidate["surfaceIds"] - search_ids
    union = search_ids | candidate["surfaceIds"]
    receipt.check("population.search_candidate_intersection", len(intersection), 2_585)
    receipt.check("population.search_only", len(search_only), 6_051)
    receipt.check("population.candidate_only", len(candidate_only), 13_338)
    receipt.check("population.search_candidate_union", len(union), 21_974)

    atlas = load_json(ROOT / "frontend/public/data/trace-v48/atlas.json")
    atlas_counts = atlas["counts"]
    atlas_expected = {
        "activeObjects": 15_923,
        "traceNodes": 97_889,
        "traceEdges": 255_695,
        "activeTrees": 30,
        "reviewObjects": 4_425,
        "auxiliaryObjects": 11,
        "influenceEdges": 0,
    }
    for key, expected in atlas_expected.items():
        receipt.check(f"trace.atlas_counts.{key}", atlas_counts.get(key), expected)
    receipt.check("trace.atlas_relation_types", len(atlas["relationTypes"]), 20)
    receipt.check(
        "trace.atlas_active_memberships",
        sum(item["count"] for item in atlas["relationTypes"]),
        126_822,
    )
    receipt.check("trace.atlas_research_trees", len(atlas["treeCounts"]), 30)

    review = load_json(ROOT / "frontend/public/data/trace-v48/review-catalog.json")
    auxiliary = load_json(ROOT / "frontend/public/data/trace-v48/auxiliary.json")
    receipt.check("trace.review_items", len(review["items"]), 4_425)
    receipt.check("trace.auxiliary_items", len(auxiliary["items"]), 11)
    receipt.check("trace.auxiliary_count_eligible", auxiliary.get("countEligible"), False)

    receipt.set_hashes.update(
        {
            "searchSurfaceIds": line_set_hash(search_ids),
            "traceCatalogSurfaceIds": line_set_hash(catalog_ids),
            "traceCatalogMetadataSupportedSurfaceIds": line_set_hash(catalog_metadata_ids),
        }
    )


def verify_trace_manifest(receipt: Receipt) -> None:
    base = ROOT / "frontend/public/data/trace-v48"
    manifest = load_json(base / "manifest.json")
    assets = manifest.get("assets") or []
    receipt.check("trace.manifest_assets", len(assets), 580)
    receipt.check(
        "trace.manifest_shards",
        sum(1 for item in assets if str(item.get("path", "")).startswith("neighborhoods/")),
        576,
    )
    receipt.check("trace.manifest_gate", manifest.get("gate"), "PASS")
    receipt.check("trace.manifest_failures", manifest.get("failures"), [])
    failures: list[str] = []
    seen: set[str] = set()
    for item in assets:
        relative = item.get("path")
        if not isinstance(relative, str) or relative in seen:
            failures.append(str(relative))
            continue
        seen.add(relative)
        target = base / relative
        if not target.is_file():
            failures.append(relative)
            continue
        size, digest = sha256_file(target)
        if size != item.get("bytes") or digest != item.get("sha256"):
            failures.append(relative)
    receipt.check("trace.manifest_declared_asset_failures", failures, [])


def verify_audit_outputs(receipt: Receipt, candidate: dict[str, Any]) -> None:
    missing = [name for name in REQUIRED_AUDIT_FILES if not (AUDIT_DIR / name).is_file()]
    receipt.check("audit.required_files_missing", missing, [])
    if missing:
        return

    rules = load_json(AUDIT_DIR / "03_GRAPH_FACT_CLASSIFICATION_RULES.json")
    graph = load_json(AUDIT_DIR / "04_GRAPH_FACT_RECONCILIATION.json")
    raw = load_json(AUDIT_DIR / "07_RAW_SOURCE_EVIDENCE_SUMMARY.json")
    registry = load_json(AUDIT_DIR / "08_EPISTEMIC_RELATION_REGISTRY.json")
    missingness = load_json(AUDIT_DIR / "11_MISSINGNESS_BASELINE.json")
    gate = load_json(AUDIT_DIR / "MANIFEST.json")

    receipt.check(
        "rules.unknown_default_classification",
        rules.get("failClosedPolicy", {}).get("defaultClassification"),
        "HELD_UNSUPPORTED",
    )
    receipt.check(
        "rules.unknown_default_relation_family",
        rules.get("failClosedPolicy", {}).get("defaultRelationFamily"),
        None,
    )
    receipt.check(
        "rules.unknown_creates_trace_projection",
        rules.get("failClosedPolicy", {}).get("unknownRelationCreatesTraceProjection"),
        False,
    )
    graph_gates = graph.get("gates", {})
    receipt.check("graph.UNCLASSIFIED_GRAPH_FACT", graph_gates.get("UNCLASSIFIED_GRAPH_FACT"), 0)
    receipt.check(
        "graph.SILENT_UNKNOWN_RELATION_FALLBACK",
        graph_gates.get("SILENT_UNKNOWN_RELATION_FALLBACK"),
        0,
    )
    receipt.check(
        "graph.AUTOMATIC_INFLUENCE_INFERENCE",
        graph_gates.get("AUTOMATIC_INFLUENCE_INFERENCE"),
        0,
    )
    graph_units = graph.get("graphUnits", {})
    unit_expected = {
        "activeObjectRelationMemberships": 126_822,
        "activeRelationTypes": 20,
        "activeResearchTrees": 30,
        "fullGraphEdges": 255_695,
        "influenceEdges": 0,
        "traceAssetsExcludingManifest": 580,
        "traceNodes": 97_889,
        "traceShards": 576,
    }
    for key, expected in unit_expected.items():
        receipt.check(f"graph.units.{key}", graph_units.get(key), expected)

    raw_unclassified = raw.get("gates", {}).get("UNCLASSIFIED_RAW_SOURCE")
    if raw_unclassified is None:
        raw_unclassified = raw.get("UNCLASSIFIED_RAW_SOURCE")
    receipt.check("raw.UNCLASSIFIED_RAW_SOURCE", raw_unclassified, 0)

    registry_fail_closed = registry.get("defaultUnknownRelation", {})
    receipt.check(
        "registry.unknown_default_classification",
        registry_fail_closed.get("classification"),
        "HELD_UNSUPPORTED",
    )
    receipt.check(
        "registry.unknown_default_relation_family",
        registry_fail_closed.get("relationFamily"),
        None,
    )
    receipt.check("registry.closed_relation_entries", len(registry.get("relations") or []), 40)
    registry_gates = registry.get("gates", {})
    receipt.check("registry.UNKNOWN_RELATION_FAIL_CLOSED", registry_gates.get("UNKNOWN_RELATION_FAIL_CLOSED"), True)
    receipt.check("registry.CURRENT_RELATIONS_PROJECTABLE", registry_gates.get("CURRENT_RELATIONS_PROJECTABLE"), 0)

    population = missingness.get("populationCounts", {})
    population_expected = {
        "legacyInputSurfaces": 15_923,
        "accountedInputSurfaces": 15_923,
        "unaccountedInputSurfaces": 0,
        "baselineArchiveObjects": 15_923,
        "researchEligibleObjects": 7_995,
        "traceEligibleObjects": 0,
        "heldObjects": 7_928,
        "rejectedObjects": 0,
    }
    for key, expected in population_expected.items():
        receipt.check(f"corpus.{key}", population.get(key), expected)

    _, membership_rows = load_tsv(AUDIT_DIR / "10_CORPUS_MEMBERSHIP_BASELINE.tsv")
    membership_ids = {row["surface_id"] for row in membership_rows}
    research_counts = Counter(row["research_disposition"] for row in membership_rows)
    trace_counts = Counter(row["trace_disposition"] for row in membership_rows)
    receipt.check("corpus.membership_rows", len(membership_rows), 15_923)
    receipt.check("corpus.membership_unique_surface_ids", len(membership_ids), 15_923)
    receipt.check("corpus.membership_candidate_ids", membership_ids, candidate["surfaceIds"])
    receipt.check(
        "corpus.research_dispositions",
        dict(sorted(research_counts.items())),
        {"HELD": 7_928, "RESEARCH_ELIGIBLE": 7_995},
    )
    receipt.check("corpus.trace_dispositions", dict(trace_counts), {"HELD": 15_923})

    metadata_header, metadata_rows = load_tsv(
        AUDIT_DIR / "05_METADATA_SUPPORTED_SYMMETRIC_DIFF.tsv"
    )
    receipt.require(
        "metadata.tsv_columns",
        {"comparison_id", "delta", "set_status", "condition", "status"}.issubset(metadata_header),
        detail="metadata reconciliation TSV must retain comparison identity and status",
    )
    comparison_rows = {row["comparison_id"]: row for row in metadata_rows}
    receipt.check("metadata.tsv_comparisons", len(metadata_rows), 4)
    receipt.check(
        "metadata.candidate_sqlite_set_status",
        comparison_rows.get("B_CANDIDATE_ROWS_VS_SQLITE", {}).get("set_status"),
        "EXACT_SET_MATCH",
    )
    receipt.check(
        "metadata.candidate_catalog_set_status",
        comparison_rows.get("C_CANDIDATE_ROWS_VS_TRACE_CATALOG", {}).get("set_status"),
        "EXACT_SET_MATCH",
    )

    raw_header, raw_rows = load_tsv(AUDIT_DIR / "06_RAW_SOURCE_EVIDENCE_DISPOSITION.tsv")
    receipt.require(
        "raw.tsv_nonempty",
        bool(raw_header and raw_rows),
        detail="raw source disposition must enumerate every scoped artifact",
    )
    raw_class_field = next(
        (
            name
            for name in (
                "evidence_eligibility",
                "classification",
                "disposition",
                "evidence_disposition",
            )
            if name in raw_header
        ),
        None,
    )
    receipt.require(
        "raw.tsv_classification_column",
        raw_class_field is not None,
        detail="raw source TSV needs an explicit classification/disposition column",
    )
    if raw_class_field:
        receipt.check(
            "raw.tsv_blank_classifications",
            sum(1 for row in raw_rows if not row.get(raw_class_field, "").strip()),
            0,
        )
    receipt.check("raw.tsv_rows", len(raw_rows), 1_599)
    receipt.check("raw.tsv_unique_paths", len({row.get("path") for row in raw_rows}), 1_599)
    receipt.check("raw.summary_total_artifacts", raw.get("counts", {}).get("totalArtifacts"), 1_599)
    receipt.check("raw.summary_classified_artifacts", raw.get("counts", {}).get("classifiedArtifacts"), 1_599)

    manifest_artifacts = gate.get("artifacts") or []
    manifest_failures: list[str] = []
    for item in manifest_artifacts:
        relative = item.get("path")
        if not isinstance(relative, str):
            manifest_failures.append(str(relative))
            continue
        path = ROOT / relative
        if not path.is_file():
            manifest_failures.append(relative)
            continue
        size, digest = sha256_file(path)
        if size != item.get("bytes") or digest != item.get("sha256"):
            manifest_failures.append(relative)
    receipt.check("audit.manifest_artifact_failures", manifest_failures, [])

    checksum_failures: list[str] = []
    checksum_paths: set[str] = set()
    with (AUDIT_DIR / "CHECKSUMS.sha256").open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.rstrip("\n")
            if not line:
                continue
            try:
                expected_digest, relative = line.split("  ", 1)
            except ValueError:
                checksum_failures.append(f"line:{line_number}")
                continue
            checksum_paths.add(relative)
            target = ROOT / relative
            if not target.is_file():
                checksum_failures.append(relative)
                continue
            _, actual_digest = sha256_file(target)
            if actual_digest != expected_digest:
                checksum_failures.append(relative)
    receipt.check("audit.checksum_failures", checksum_failures, [])
    receipt.require(
        "audit.checksums_cover_manifest",
        "docs/audits/v49-authority-research-delta/MANIFEST.json" in checksum_paths,
        detail="CHECKSUMS.sha256 must bind the package manifest",
    )

    receipt.metrics.update(
        {
            "RESEARCH_ELIGIBLE_OBJECTS": population.get("researchEligibleObjects"),
            "TRACE_ELIGIBLE_OBJECTS": population.get("traceEligibleObjects"),
            "HELD_OBJECTS": population.get("heldObjects"),
            "REJECTED_OBJECTS": population.get("rejectedObjects"),
            "UNCLASSIFIED_GRAPH_FACT": graph_gates.get("UNCLASSIFIED_GRAPH_FACT"),
            "UNCLASSIFIED_RAW_SOURCE": raw_unclassified,
        }
    )


def verify_no_v47_dependency(receipt: Receipt) -> None:
    allowed_inputs = set(FROZEN_ASSETS)
    allowed_inputs.update(
        {
            "frontend/public/data/archive-search-v1.json",
            "frontend/public/data/trace-v48/atlas.json",
            "frontend/public/data/trace-v48/catalog.json",
            "frontend/public/data/trace-v48/review-catalog.json",
            "frontend/public/data/trace-v48/auxiliary.json",
        }
    )
    receipt.require(
        "authority.verifier_input_boundary",
        all("_v47" not in path for path in allowed_inputs),
        detail="verifier input allowlist must not contain a v47 parent",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the complete deterministic JSON receipt",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    receipt = Receipt()
    try:
        verify_no_v47_dependency(receipt)
        verify_frozen_assets(receipt)
        verify_transfer_manifest(receipt)
        candidate = candidate_measurement(receipt)
        if candidate:
            sqlite_data = sqlite_measurement(receipt, candidate)
            verify_read_products(receipt, candidate, sqlite_data)
            verify_trace_manifest(receipt)
            verify_audit_outputs(receipt, candidate)
    except Exception as exc:  # a verifier exception is itself a failed receipt
        receipt.errors.append(f"verifier exception: {type(exc).__name__}: {exc}")

    status = "PASS" if not receipt.errors else "FAIL"
    output = {
        "schema": "v49.authority-research-verifier-receipt/v1",
        "status": status,
        "checks": dict(sorted(receipt.checks.items())),
        "metrics": dict(sorted(receipt.metrics.items())),
        "setHashes": dict(sorted(receipt.set_hashes.items())),
        "errors": receipt.errors,
    }
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=False))
    else:
        print(f"{status}: {len(receipt.checks)} checks; {len(receipt.errors)} failures")
        for error in receipt.errors:
            print(f"- {error}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
