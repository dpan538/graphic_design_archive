#!/usr/bin/env python3
"""Read-only reconciliation for the v49 Phase 2B population rehearsal.

This program is intentionally not an importer.  It never parses the Candidate
JSON into records, never connects to PostgreSQL, and never writes a file.  The
Candidate is hashed only; its already-extracted surface IDs arrive through the
required surface-row ledger.  SQLite is opened only with ``mode=ro`` and
``immutable=1`` and is additionally placed in ``query_only`` mode.

The JSON written to stdout is deliberately receipt-generator friendly.  A
non-zero status means one or more integrity or reconciliation checks failed;
the output still contains every completed check so a failure receipt remains
auditable.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, NoReturn
from urllib.parse import quote


HASH_CHUNK_BYTES = 1024 * 1024
EXPECTED_SURFACE_COUNT = 15_923

FROZEN_ASSETS: dict[str, dict[str, Any]] = {
    "generated/public_surfaces_prefreeze_candidate_v48.json": {
        "bytes": 190_067_852,
        "sha256": "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48",
        "authorityRole": "sole_canonical_population_input",
        "populationInput": True,
        "reconciliationOnly": False,
        "integrityOnly": False,
    },
    "data/prefreeze_candidate_v48.sqlite": {
        "bytes": 421_801_984,
        "sha256": "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e",
        "authorityRole": "immutable_reconciliation_only",
        "populationInput": False,
        "reconciliationOnly": True,
        "integrityOnly": False,
    },
    "generated/prefreeze_candidate_v48_transfer_manifest.json": {
        "bytes": 21_752,
        "sha256": "865358db84c15d960b3535969a32521c0ffec177f7455d21db86cd131f787d5b",
        "authorityRole": "transfer_integrity_only",
        "populationInput": False,
        "reconciliationOnly": False,
        "integrityOnly": True,
    },
    "data/prefreeze_candidate_v48_transfer_manifest.csv": {
        "bytes": 12_861,
        "sha256": "694a60657077bcab8888c4a4ef1daf6059706e544606d4862e46c57dcf6ddc18",
        "authorityRole": "transfer_integrity_only",
        "populationInput": False,
        "reconciliationOnly": False,
        "integrityOnly": True,
    },
    "frontend/public/data/trace-v48/manifest.json": {
        "bytes": 83_900,
        "sha256": "1678e211023aa324078e0478f88670d2378b6dc5c398cc5c04722605038fee23",
        "authorityRole": "legacy_trace_product_reconciliation_only",
        "populationInput": False,
        "reconciliationOnly": True,
        "integrityOnly": False,
    },
}

SEARCH_RELATIVE = "frontend/public/data/archive-search-v1.json"
GRAPH_AUDIT_RELATIVE = "docs/audits/v49-authority-research-delta/04_GRAPH_FACT_RECONCILIATION.json"

EXPECTED_SEARCH_METRICS = {
    "searchIds": 8_636,
    "canonicalIds": 15_923,
    "intersection": 2_585,
    "searchOnly": 6_051,
    "canonicalOnly": 13_338,
    "union": 21_974,
}

EXPECTED_TRACE_METRICS = {
    "activeObjects": 15_923,
    "traceNodes": 97_889,
    "traceEdges": 255_695,
    "activeTrees": 30,
    "sourceVerified": 12_952,
    "metadataSupported": 2_971,
    "reviewObjects": 4_425,
    "auxiliaryObjects": 11,
    "influenceEdges": 0,
    "manifestAssets": 580,
    "neighborhoodShards": 576,
}

EXPECTED_GRAPH_AUDIT_METRICS = {
    "legacyGraphEdgesReconciled": 255_695,
    "legacyMembershipsReconciled": 126_822,
    "legacyNodesReconciled": 97_889,
    "activeRelationTypes": 20,
    "activeTrees": 30,
    "influenceEdges": 0,
    "edgeToLabelMappingsAuthorized": 0,
    "unsafePairingRows": 9_393,
}

EXPECTED_SQLITE_COUNTS = {
    "activeObjects": 15_923,
    "traceNodes": 97_889,
    "traceEdges": 255_695,
    "activeMemberships": 126_822,
    "reviewObjects": 4_425,
    "influenceEdges": 0,
    "influenceMemberships": 0,
}

EXPECTED_TRANSFER_METRICS = {"declaredFiles": 65, "declaredBytes": 613_077_245}

EXPECTED_VISUAL_HASHES = {
    "surfaceOrdinalIdSequenceSha256": "0ded26112f66e9b269dd6f7ca5978d9454e254e52241ca121f63c56368eab418",
    "surfaceIdSetSha256": "7bae71cb2915a6ea6a9c9c43024a0a84bab5200edffad96298f398a7b8053d46",
    "sourceRecordIdSetSha256": "16795db4223fd1e00ef362ba0a29b7a521a38ccf56638e9928d70a3343112f2e",
    "rawVisualBundleSequenceSha256": "265cc790ffcc5b4c4dddf5ddbb29a894f35f92e166df474a744dafa0b7e8743e",
    "externalLocatorOccurrenceSequenceSha256": "1bbd68dfaf8661a1976fea56a2d121d807a42b5ed8a735094dda9868dcec5812",
    "externalLocatorValueSetSha256": "434dafb489119676615a6cd604a65286f17e2d8f2f18e48bf5e06943b6439e28",
    "classifiedSurfaceSequenceSha256": "2ba50afc2175e350895f9b7b76615ba72cf2175cf4599b13b49f5ee107242abc",
}


class ReconciliationError(RuntimeError):
    """Expected, receipt-worthy validation error."""


class Receipt:
    """Collect checks without suppressing the remainder of the evidence."""

    def __init__(self) -> None:
        self.checks: dict[str, dict[str, Any]] = {}
        self.errors: list[str] = []

    def equal(self, name: str, actual: Any, expected: Any) -> bool:
        passed = actual == expected
        self.checks[name] = {"pass": passed, "actual": actual, "expected": expected}
        if not passed:
            self.errors.append(f"{name}: expected {expected!r}, got {actual!r}")
        return passed

    def require(self, name: str, passed: bool, detail: str) -> bool:
        self.checks[name] = {"pass": bool(passed), "detail": detail}
        if not passed:
            self.errors.append(f"{name}: {detail}")
        return passed


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReconciliationError(f"DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def reject_nonfinite(value: str) -> NoReturn:
    raise ReconciliationError(f"UNSUPPORTED_JSON_CONSTANT:{value}")


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(
                handle,
                object_pairs_hook=strict_object,
                parse_constant=reject_nonfinite,
            )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReconciliationError(f"JSON_READ_FAILED:{path}:{error}") from error


def sha256_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("rb") as handle:
            while block := handle.read(HASH_CHUNK_BYTES):
                size += len(block)
                digest.update(block)
    except OSError as error:
        raise ReconciliationError(f"FILE_READ_FAILED:{path}:{error}") from error
    return size, digest.hexdigest()


def stable_set_hash(values: Iterable[str]) -> str:
    ordered = sorted(set(values))
    return hashlib.sha256(("\n".join(ordered) + ("\n" if ordered else "")).encode("utf-8")).hexdigest()


def assert_regular_file(path: Path, label: str) -> Path:
    resolved = path.resolve(strict=False)
    if not resolved.is_file():
        raise ReconciliationError(f"MISSING_{label}:{resolved}")
    return resolved


def repo_asset(repo_root: Path, relative: str) -> Path:
    path = assert_regular_file(repo_root / relative, relative.replace("/", "_"))
    try:
        path.relative_to(repo_root)
    except ValueError as error:
        raise ReconciliationError(f"REPO_ASSET_ESCAPES_ROOT:{relative}:{path}") from error
    return path


def verify_frozen_assets(repo_root: Path, receipt: Receipt) -> tuple[dict[str, dict[str, Any]], dict[str, Path]]:
    evidence: dict[str, dict[str, Any]] = {}
    paths: dict[str, Path] = {}
    for relative, expected in FROZEN_ASSETS.items():
        path = repo_asset(repo_root, relative)
        size, digest = sha256_file(path)
        receipt.equal(f"frozen.{relative}.bytes", size, expected["bytes"])
        receipt.equal(f"frozen.{relative}.sha256", digest, expected["sha256"])
        evidence[relative] = {
            "path": relative,
            "bytes": size,
            "sha256": digest,
            "authorityRole": expected["authorityRole"],
            "populationInput": expected["populationInput"],
            "reconciliationOnly": expected["reconciliationOnly"],
            "integrityOnly": expected["integrityOnly"],
        }
        paths[relative] = path
    receipt.equal(
        "authority.canonical_population_input_artifacts",
        sum(1 for item in evidence.values() if item["populationInput"]),
        1,
    )
    return evidence, paths


def read_surface_ledger(path: Path, receipt: Receipt) -> tuple[set[str], dict[str, Any]]:
    path = assert_regular_file(path, "SURFACE_LEDGER")
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            header = reader.fieldnames
            if not header or len(header) != len(set(header)):
                raise ReconciliationError("SURFACE_LEDGER_BAD_HEADER")
            required = {"source_ordinal", "surface_id_exact"}
            missing = sorted(required - set(header))
            if missing:
                raise ReconciliationError("SURFACE_LEDGER_MISSING_COLUMNS:" + ",".join(missing))
            ids: list[str] = []
            ordinals: list[int] = []
            ragged_rows = 0
            for line_number, row in enumerate(reader, start=2):
                if None in row:
                    ragged_rows += 1
                    continue
                raw_ordinal = row["source_ordinal"]
                surface_id = row["surface_id_exact"]
                if raw_ordinal is None or not raw_ordinal.isdecimal():
                    raise ReconciliationError(f"SURFACE_LEDGER_BAD_ORDINAL:{line_number}")
                if surface_id is None or surface_id == "":
                    raise ReconciliationError(f"SURFACE_LEDGER_EMPTY_SURFACE_ID:{line_number}")
                ordinals.append(int(raw_ordinal))
                ids.append(surface_id)
    except (OSError, UnicodeError, csv.Error) as error:
        raise ReconciliationError(f"SURFACE_LEDGER_READ_FAILED:{path}:{error}") from error

    receipt.equal("surfaceLedger.raggedRows", ragged_rows, 0)
    receipt.equal("surfaceLedger.rows", len(ids), EXPECTED_SURFACE_COUNT)
    receipt.equal("surfaceLedger.uniqueSurfaceIds", len(set(ids)), EXPECTED_SURFACE_COUNT)
    receipt.equal("surfaceLedger.ordinals", sorted(ordinals), list(range(EXPECTED_SURFACE_COUNT)))
    return set(ids), {
        "path": str(path),
        "rows": len(ids),
        "uniqueSurfaceIds": len(set(ids)),
        "surfaceIdSetSha256": stable_set_hash(ids),
    }


def read_search_ids(path: Path, receipt: Receipt) -> set[str]:
    search = load_json(assert_regular_file(path, "SEARCH_INDEX"))
    if not isinstance(search, dict):
        raise ReconciliationError("SEARCH_INDEX_NOT_OBJECT")
    schema = search.get("schema")
    rows = search.get("items")
    if not isinstance(schema, list) or not all(isinstance(value, str) for value in schema):
        raise ReconciliationError("SEARCH_INDEX_BAD_SCHEMA")
    if schema.count("surfaceId") != 1:
        raise ReconciliationError("SEARCH_INDEX_SURFACE_ID_COLUMN")
    if not isinstance(rows, list):
        raise ReconciliationError("SEARCH_INDEX_ITEMS_NOT_ARRAY")
    surface_id_index = schema.index("surfaceId")
    ids: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != len(schema):
            raise ReconciliationError(f"SEARCH_INDEX_BAD_ROW:{index}")
        value = row[surface_id_index]
        if not isinstance(value, str) or value == "":
            raise ReconciliationError(f"SEARCH_INDEX_BAD_SURFACE_ID:{index}")
        ids.append(value)
    receipt.equal("search.countScalar", search.get("count"), EXPECTED_SEARCH_METRICS["searchIds"])
    receipt.equal("search.itemRows", len(rows), EXPECTED_SEARCH_METRICS["searchIds"])
    receipt.equal("search.uniqueIds", len(set(ids)), EXPECTED_SEARCH_METRICS["searchIds"])
    return set(ids)


def verify_search(repo_root: Path, candidate_ids: set[str], receipt: Receipt) -> dict[str, Any]:
    search_path = repo_asset(repo_root, SEARCH_RELATIVE)
    search_ids = read_search_ids(search_path, receipt)
    metrics = {
        "searchIds": len(search_ids),
        "canonicalIds": len(candidate_ids),
        "intersection": len(search_ids & candidate_ids),
        "searchOnly": len(search_ids - candidate_ids),
        "canonicalOnly": len(candidate_ids - search_ids),
        "union": len(search_ids | candidate_ids),
        "searchIdSetSha256": stable_set_hash(search_ids),
        "authorityRole": "derived_search_reconciliation_only",
        "canonicalRowsCreated": 0,
        "fieldsBackfilled": 0,
    }
    for name, expected in EXPECTED_SEARCH_METRICS.items():
        receipt.equal(f"search.{name}", metrics[name], expected)
    return metrics


def sqlite_uri(path: Path) -> str:
    # ``quote(..., safe='/')`` preserves the absolute hierarchy while binding
    # both required SQLite URI read-only options.  No user-provided fragment is
    # accepted or appended.
    return f"file:{quote(path.as_posix(), safe='/')}?mode=ro&immutable=1"


def query_sqlite(sqlite_path: Path, candidate_ids: set[str], receipt: Receipt) -> dict[str, Any]:
    uri = sqlite_uri(sqlite_path)
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(uri, uri=True, isolation_level=None)
        connection.execute("PRAGMA query_only=ON")
        receipt.equal("sqlite.queryOnly", connection.execute("PRAGMA query_only").fetchone()[0], 1)
        integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
        receipt.equal("sqlite.integrityCheck", integrity, ["ok"])

        object_rows = list(
            connection.execute(
                "SELECT surface_id, source_record_id, trace_tier "
                "FROM objects WHERE count_eligible=1 ORDER BY surface_id"
            )
        )
        sqlite_surface_ids = {row[0] for row in object_rows}
        tiers = Counter(row[2] for row in object_rows)
        scalar_queries = {
            "activeObjects": "SELECT COUNT(*) FROM objects WHERE count_eligible=1",
            "traceNodes": "SELECT COUNT(*) FROM trace_nodes",
            "traceEdges": "SELECT COUNT(*) FROM trace_edges",
            "activeMemberships": "SELECT COUNT(*) FROM object_trace_edges",
            "reviewObjects": "SELECT COUNT(*) FROM authority_review_objects_current",
            "influenceEdges": "SELECT COUNT(*) FROM trace_edges WHERE edge_label='influenced_by'",
            "influenceMemberships": (
                "SELECT COUNT(*) FROM object_trace_edges m JOIN trace_edges e ON e.edge_id=m.edge_id "
                "WHERE e.edge_label='influenced_by'"
            ),
        }
        metrics = {name: connection.execute(sql).fetchone()[0] for name, sql in scalar_queries.items()}
        for name, expected in EXPECTED_SQLITE_COUNTS.items():
            receipt.equal(f"sqlite.{name}", metrics[name], expected)
        # Keep the receipt compact and JSON-serializable while still proving
        # exact set equality; emitting both 15,923-ID Python sets would also
        # make a reconciliation report needlessly huge.
        receipt.equal(
            "sqlite.activeObjectSurfaceIdSetSha256MatchesLedger",
            stable_set_hash(sqlite_surface_ids),
            stable_set_hash(candidate_ids),
        )
        receipt.equal(
            "sqlite.activeObjectSurfaceIdCountMatchesLedger",
            len(sqlite_surface_ids), len(candidate_ids),
        )
        receipt.equal(
            "sqlite.tierCounts",
            dict(sorted(tiers.items())),
            {"metadata_supported": 2_971, "source_verified": 12_952},
        )
        metrics.update(
            {
                "activeObjectSurfaceIdSetSha256": stable_set_hash(sqlite_surface_ids),
                "sqliteOpenUri": uri,
                "authorityRole": "immutable_reconciliation_only",
                "canonicalRowsCreated": 0,
                "fieldsBackfilled": 0,
                "sqliteCanonicalWrites": 0,
            }
        )
        return metrics
    except sqlite3.Error as error:
        raise ReconciliationError(f"SQLITE_READ_ONLY_RECONCILIATION_FAILED:{error}") from error
    finally:
        if connection is not None:
            connection.close()


def extract_trace_manifest_metrics(manifest: Any) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise ReconciliationError("TRACE_MANIFEST_NOT_OBJECT")
    counts = manifest.get("counts")
    assets = manifest.get("assets")
    if not isinstance(counts, dict) or not isinstance(assets, list):
        raise ReconciliationError("TRACE_MANIFEST_BAD_SHAPE")
    metric_names = (
        "activeObjects",
        "traceNodes",
        "traceEdges",
        "activeTrees",
        "sourceVerified",
        "metadataSupported",
        "reviewObjects",
        "auxiliaryObjects",
        "influenceEdges",
    )
    result = {name: counts.get(name) for name in metric_names}
    result["manifestAssets"] = len(assets)
    result["neighborhoodShards"] = sum(
        1 for asset in assets if isinstance(asset, dict) and str(asset.get("path", "")).startswith("neighborhoods/")
    )
    return result


def graph_audit_metrics(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if not isinstance(data, dict):
        raise ReconciliationError("GRAPH_AUDIT_NOT_OBJECT")
    graph_units = data.get("graphUnits")
    candidate = data.get("candidateAuthorityMeasurement")
    if not isinstance(graph_units, dict) or not isinstance(candidate, dict):
        raise ReconciliationError("GRAPH_AUDIT_BAD_SHAPE")
    edge_to_label = candidate.get("edgeToLabelMapping")
    if not isinstance(edge_to_label, dict):
        raise ReconciliationError("GRAPH_AUDIT_EDGE_TO_LABEL_SHAPE")
    return {
        "legacyGraphEdgesReconciled": graph_units.get("fullGraphEdges"),
        "legacyMembershipsReconciled": graph_units.get("activeObjectRelationMemberships"),
        "legacyNodesReconciled": graph_units.get("traceNodes"),
        "activeRelationTypes": graph_units.get("activeRelationTypes"),
        "activeTrees": graph_units.get("activeResearchTrees"),
        "influenceEdges": graph_units.get("influenceEdges"),
        "edgeToLabelMappingsAuthorized": edge_to_label.get("mappingFactsAuthorized"),
        "unsafePairingRows": edge_to_label.get("surfacesWithLengthMismatch"),
    }


def verify_trace(repo_root: Path, receipt: Receipt) -> dict[str, Any]:
    manifest_path = repo_asset(repo_root, "frontend/public/data/trace-v48/manifest.json")
    manifest_metrics = extract_trace_manifest_metrics(load_json(manifest_path))
    for name, expected in EXPECTED_TRACE_METRICS.items():
        receipt.equal(f"trace.manifest.{name}", manifest_metrics[name], expected)

    graph_path = repo_asset(repo_root, GRAPH_AUDIT_RELATIVE)
    graph_metrics = graph_audit_metrics(graph_path)
    for name, expected in EXPECTED_GRAPH_AUDIT_METRICS.items():
        receipt.equal(f"trace.graphAudit.{name}", graph_metrics[name], expected)

    return {
        "authorityRole": "legacy_trace_product_reconciliation_only",
        "manifest": manifest_metrics,
        "historicalGraphAudit": graph_metrics,
        "canonicalRowsCreated": 0,
        "fieldsBackfilled": 0,
        "traceImportedCanonicalRows": 0,
        "legacyGraphEdgesImported": 0,
        "acceptedSemanticRelations": 0,
        "traceProjectionEdges": 0,
    }


def verify_transfer_manifest(repo_root: Path, receipt: Receipt) -> dict[str, Any]:
    path = repo_asset(repo_root, "generated/prefreeze_candidate_v48_transfer_manifest.json")
    data = load_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("files"), list):
        raise ReconciliationError("TRANSFER_MANIFEST_BAD_SHAPE")
    rows = data["files"]
    bytes_total = 0
    for index, item in enumerate(rows):
        if not isinstance(item, dict) or not isinstance(item.get("bytes"), int):
            raise ReconciliationError(f"TRANSFER_MANIFEST_BAD_FILE_ROW:{index}")
        bytes_total += item["bytes"]
    metrics = {"declaredFiles": len(rows), "declaredBytes": bytes_total}
    for name, expected in EXPECTED_TRANSFER_METRICS.items():
        receipt.equal(f"transfer.{name}", metrics[name], expected)
    return {
        "authorityRole": "transfer_integrity_only",
        **metrics,
        "canonicalRowsCreated": 0,
        "fieldsBackfilled": 0,
    }


def collect_expected_hash_values(value: Any, found: dict[str, set[str]]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in EXPECTED_VISUAL_HASHES and isinstance(child, str):
                found[key].add(child)
            collect_expected_hash_values(child, found)
    elif isinstance(value, list):
        for child in value:
            collect_expected_hash_values(child, found)


def verify_visual_hashes(path: Path, receipt: Receipt) -> dict[str, Any]:
    data = load_json(assert_regular_file(path, "VISUAL_HASH_SOURCE"))
    found: dict[str, set[str]] = {name: set() for name in EXPECTED_VISUAL_HASHES}
    collect_expected_hash_values(data, found)
    values: dict[str, str | None] = {}
    for name, expected in EXPECTED_VISUAL_HASHES.items():
        candidates = found[name]
        if len(candidates) != 1:
            receipt.require(
                f"visual.{name}.unambiguous",
                False,
                f"expected exactly one value in {path}; got {sorted(candidates)!r}",
            )
            values[name] = None
        else:
            actual = next(iter(candidates))
            receipt.equal(f"visual.{name}", actual, expected)
            values[name] = actual
    return {
        "source": str(path),
        "hashes": values,
        "authorityRole": "phase1d_visual_parity_reconciliation_only",
        "canonicalRowsCreated": 0,
        "fieldsBackfilled": 0,
        "rightsAuditPermissionUpgrades": 0,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only Phase 2B reconciliation; emits one JSON receipt to stdout."
    )
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument(
        "--surface-ledger",
        required=True,
        type=Path,
        help="TSV generated by the Candidate extractor; requires source_ordinal and surface_id_exact.",
    )
    visual_group = parser.add_mutually_exclusive_group(required=True)
    visual_group.add_argument(
        "--stage-manifest",
        type=Path,
        help="Extractor staging manifest containing all seven Phase 1D visual parity hashes.",
    )
    visual_group.add_argument(
        "--visual-hashes",
        type=Path,
        help="JSON object/receipt containing all seven Phase 1D visual parity hashes.",
    )
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = args.repo_root.resolve(strict=False)
    if not repo_root.is_dir():
        raise ReconciliationError(f"MISSING_REPO_ROOT:{repo_root}")
    receipt = Receipt()
    assets, paths = verify_frozen_assets(repo_root, receipt)
    candidate_ids, ledger = read_surface_ledger(args.surface_ledger, receipt)
    search = verify_search(repo_root, candidate_ids, receipt)
    sqlite_metrics = query_sqlite(
        paths["data/prefreeze_candidate_v48.sqlite"], candidate_ids, receipt
    )
    trace = verify_trace(repo_root, receipt)
    transfer = verify_transfer_manifest(repo_root, receipt)
    visual_source = args.stage_manifest or args.visual_hashes
    assert visual_source is not None
    visual = verify_visual_hashes(visual_source, receipt)
    return {
        "schema": "gda-v49-phase2b-read-only-reconciliation/v1",
        "status": "PASS" if not receipt.errors else "FAIL",
        "checks": receipt.checks,
        "errors": receipt.errors,
        "artifactAuthorityLedger": assets,
        "surfaceLedger": ledger,
        "searchReconciliation": search,
        "sqliteReconciliation": sqlite_metrics,
        "traceReconciliation": trace,
        "transferIntegrity": transfer,
        "visualParity": visual,
        "boundaryProof": {
            "canonicalPopulationInputArtifacts": 1,
            "canonicalRowsCreated": 0,
            "fieldsBackfilled": 0,
            "sqliteCanonicalWrites": 0,
            "searchImportedRows": 0,
            "searchOnlyCanonicalInserts": 0,
            "traceImportedCanonicalRows": 0,
            "legacyGraphEdgesImported": 0,
            "rightsAuditPermissionUpgrades": 0,
            "enforcement": [
                "This CLI imports no PostgreSQL driver and opens no PostgreSQL connection.",
                "The Candidate JSON is SHA-256 streamed only; no Candidate record is parsed here.",
                "SQLite uses a fixed file: URI with mode=ro&immutable=1 and PRAGMA query_only=ON.",
                "All outputs are JSON written to stdout; this CLI accepts no output path and writes no files.",
            ],
        },
        "inputs": {
            "surfaceLedger": str(assert_regular_file(args.surface_ledger, "SURFACE_LEDGER")),
            "visualHashSource": str(assert_regular_file(visual_source, "VISUAL_HASH_SOURCE")),
        },
    }


def main(argv: list[str]) -> int:
    try:
        result = run(parse_args(argv))
    except (ReconciliationError, OSError, ValueError) as error:
        result = {
            "schema": "gda-v49-phase2b-read-only-reconciliation/v1",
            "status": "FAIL",
            "fatalError": str(error),
        }
    json.dump(result, sys.stdout, ensure_ascii=False, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
