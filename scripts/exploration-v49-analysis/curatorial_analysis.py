#!/usr/bin/env python3
"""Deterministic TRACE v49 curatorial/source-structure diagnostics.

This module measures project-curated structural overlap. It does not create a
similarity score, ranking, semantic relation, historical relation, or public
projection. Public pair statistics use only the eligibility-ledger public
cohort; held rows are retained solely in separate aggregate census fields.

The co-membership implementation is an inverted index of Python integer
bitsets. It derives exact >=1/>=2/>=3 fanout and shared-container histograms
without materializing object-pair rows or an object-by-object matrix.

``candidate_summary`` is deliberately supplied by the central Round 5 source
inventory pass. This module never loads or shells out over the 190 MB candidate
JSON. If provided, the summary must be aggregate-only. Its optional
``duplicate_membership_views`` mapping can contain entries shaped as::

    {"folder": {"pair_count": 47982, "pair_sha256": "..."}, ...}

The central inventory's camelCase ``folderStructures`` receipt is also
accepted. All supplied receipts are checked against the immutable SQLite
membership pair set.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import re
import resource
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


FORMAT = "trace-v49-curatorial-analysis/v1"
DERIVATION_VERSION = "trace-v49-curatorial-bitset-v1"

EXPECTED_SQLITE_SHA256 = "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e"
EXPECTED_LEDGER_SHA256 = "48f98f68ca2ec0cef96c82ecc9c01e4129eb9a3f91e08b07ad9a59644a9d4e01"
EXPECTED_FOLDER_PAIR_SHA256 = "b2ddbe94f4d569f6b9970246855b535374b7c1a9b8ac047de58899c860bd4573"
EXPECTED_OBJECT_COUNT = 15_923
EXPECTED_PUBLIC_COUNT = 7_995
EXPECTED_HELD_COUNT = 7_928
EXPECTED_FOLDER_COUNT = 185
EXPECTED_MEMBERSHIP_COUNT = 47_982
EXPECTED_FOLDER_TYPES = frozenset({"medium", "movement", "region", "theme"})

_FORBIDDEN_AGGREGATE_KEYS = frozenset(
    {
        "archiveobjectuuid",
        "rawrecorduuid",
        "surfaceid",
        "folderid",
        "anchor surface id".replace(" ", ""),
        "sourceurl",
        "recordurl",
        "privateurl",
        "title",
    }
)
_UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
_INTERNAL_ID_RE = re.compile(
    r"\b(?:SURF|FOL|TRN-OBJ|TRTREE|TRBRANCH|DOS-SURF)-?[A-Z0-9#_-]+\b"
)
_URL_RE = re.compile(r"https?://", re.IGNORECASE)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _number(value: float) -> int | float:
    if float(value).is_integer():
        return int(value)
    return round(value, 6)


def _r7_quantile(values: Sequence[int], probability: float) -> int | float:
    """R-7/linear quantile, matching the prior TRACE census convention."""

    if not values:
        return 0
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return _number(ordered[lower] + (ordered[upper] - ordered[lower]) * fraction)


def _distribution(values: Sequence[int], *, include_zero: bool = True) -> dict[str, Any]:
    materialized = list(values)
    if not materialized:
        return {
            "n": 0,
            "min": 0,
            "p50": 0,
            "p90": 0,
            "p95": 0,
            "p99": 0,
            "max": 0,
            "mean": 0,
            "zero_count": 0,
        }
    result = {
        "n": len(materialized),
        "min": min(materialized),
        "p50": _r7_quantile(materialized, 0.50),
        "p90": _r7_quantile(materialized, 0.90),
        "p95": _r7_quantile(materialized, 0.95),
        "p99": _r7_quantile(materialized, 0.99),
        "max": max(materialized),
        "mean": _number(sum(materialized) / len(materialized)),
    }
    if include_zero:
        result["zero_count"] = sum(value == 0 for value in materialized)
    return result


def _weighted_value_at(
    ordered_histogram: Sequence[tuple[Fraction, int]], index: int
) -> Fraction:
    cursor = 0
    for value, count in ordered_histogram:
        next_cursor = cursor + count
        if index < next_cursor:
            return value
        cursor = next_cursor
    raise AssertionError("weighted histogram index escaped population")


def _weighted_r7_quantile(
    histogram: Mapping[Fraction, int], probability: float
) -> int | float:
    ordered = sorted((value, count) for value, count in histogram.items() if count)
    total = sum(count for _, count in ordered)
    if total == 0:
        return 0
    position = (total - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    left = _weighted_value_at(ordered, lower)
    right = _weighted_value_at(ordered, upper)
    if lower == upper:
        return _number(float(left))
    interpolated = float(left) + (float(right) - float(left)) * (position - lower)
    return _number(interpolated)


def _peak_rss_bytes() -> int:
    raw = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # Darwin reports bytes; Linux and most BSD-derived Python builds report KiB.
    return raw if sys.platform == "darwin" else raw * 1024


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


def _sanitize_candidate_summary(value: Any, path: tuple[str, ...] = ()) -> Any:
    """Copy a JSON-like aggregate summary while rejecting private row material."""

    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"non-finite aggregate at {'.'.join(path)}")
        return value
    if isinstance(value, str):
        if _URL_RE.search(value) or _UUID_RE.search(value) or _INTERNAL_ID_RE.search(value):
            raise ValueError(f"private/raw value entered candidate summary at {'.'.join(path)}")
        return value
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for raw_key in sorted(value, key=lambda item: str(item)):
            key = str(raw_key)
            if _normalize_key(key) in _FORBIDDEN_AGGREGATE_KEYS:
                raise ValueError(f"row-level key {key!r} is forbidden in candidate summary")
            result[key] = _sanitize_candidate_summary(value[raw_key], path + (key,))
        return result
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [
            _sanitize_candidate_summary(item, path + (str(index),))
            for index, item in enumerate(value)
        ]
    raise TypeError(f"candidate summary is not JSON-like at {'.'.join(path)}")


def _load_ledger(path: Path) -> tuple[dict[str, str], dict[str, Any]]:
    dispositions: dict[str, str] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"surface_id_exact", "research_disposition"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise AssertionError("eligibility ledger schema is missing required columns")
        for row in reader:
            stable_id = row["surface_id_exact"]
            disposition = row["research_disposition"]
            if stable_id in dispositions:
                raise AssertionError("duplicate eligibility-ledger stable ID")
            if disposition not in {"eligible", "held"}:
                raise AssertionError(f"unexpected research disposition: {disposition!r}")
            dispositions[stable_id] = disposition
    counts = Counter(dispositions.values())
    if len(dispositions) != EXPECTED_OBJECT_COUNT:
        raise AssertionError("eligibility ledger object count changed")
    if counts["eligible"] != EXPECTED_PUBLIC_COUNT or counts["held"] != EXPECTED_HELD_COUNT:
        raise AssertionError("eligibility ledger public/held partition changed")
    return dispositions, {
        "all_object_count": len(dispositions),
        "public_object_count": counts["eligible"],
        "held_object_count": counts["held"],
        "partition_complete": True,
        "partition_overlap_count": 0,
    }


def _connect_immutable(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro&immutable=1", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    if connection.execute("PRAGMA query_only").fetchone()[0] != 1:
        raise AssertionError("SQLite connection is not query-only")
    if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
        raise AssertionError("immutable SQLite quick_check failed")
    return connection


def _cohort_ids(dispositions: Mapping[str, str], cohort: str) -> list[str]:
    if cohort == "all":
        return sorted(dispositions)
    return sorted(stable_id for stable_id, state in dispositions.items() if state == cohort)


def _structure_census(
    rows: Iterable[tuple[str, str]], dispositions: Mapping[str, str]
) -> dict[str, Any]:
    containers: dict[str, set[str]] = defaultdict(set)
    per_object: Counter[tuple[str, str]] = Counter()
    for stable_id, raw_value in rows:
        value = str(raw_value or "").strip()
        if not value:
            continue
        state = dispositions[stable_id]
        containers[value].add(stable_id)
        per_object[(state, stable_id)] += 1

    result: dict[str, Any] = {}
    for cohort in ("all", "eligible", "held"):
        ids = _cohort_ids(dispositions, cohort)
        if cohort == "all":
            cohort_containers = {
                value: members for value, members in containers.items() if members
            }
            object_counts = [
                per_object[(dispositions[stable_id], stable_id)] for stable_id in ids
            ]
        else:
            cohort_containers = {
                value: {stable_id for stable_id in members if dispositions[stable_id] == cohort}
                for value, members in containers.items()
            }
            cohort_containers = {
                value: members for value, members in cohort_containers.items() if members
            }
            object_counts = [per_object[(cohort, stable_id)] for stable_id in ids]
        sizes = [len(members) for members in cohort_containers.values()]
        result[cohort] = {
            "container_count": len(sizes),
            "membership_count": sum(sizes),
            "object_coverage": sum(value > 0 for value in object_counts),
            "objects_without_membership": sum(value == 0 for value in object_counts),
            "memberships_per_object": _distribution(object_counts),
            "container_size": _distribution(sizes),
            "raw_pair_event_count": sum(size * (size - 1) // 2 for size in sizes),
        }
    return result


def _candidate_duplicate_view_receipt(
    candidate_summary: Mapping[str, Any] | None,
    *,
    pair_count: int,
    pair_sha256: str,
) -> dict[str, Any]:
    if candidate_summary is None:
        return {
            "status": "NOT_SUPPLIED",
            "summary_receipt": None,
            "view_count": 0,
            "views": {},
        }

    folder_structures = candidate_summary.get("folderStructures")
    summary_receipt: dict[str, Any] | None = None
    if folder_structures is not None:
        if not isinstance(folder_structures, Mapping):
            raise TypeError("candidate folderStructures must be a mapping")
        summary_count = folder_structures.get("membershipCount")
        summary_sha = folder_structures.get("membershipPairSha256")
        if summary_count is not None or summary_sha is not None:
            if summary_count is None or summary_sha is None:
                raise AssertionError("candidate folderStructures receipt is incomplete")
            if int(summary_count) != pair_count or summary_sha != pair_sha256:
                raise AssertionError("candidate folderStructures receipt differs from SQLite")
            summary_receipt = {
                "pair_count": int(summary_count),
                "pair_sha256": str(summary_sha),
                "matches_sqlite": True,
            }

    raw_views = candidate_summary.get("duplicate_membership_views")
    if raw_views is None:
        raw_views = candidate_summary.get("duplicate_view_pair_receipts")
    if raw_views is None and isinstance(folder_structures, Mapping):
        raw_views = folder_structures.get("duplicateRepresentationIntegrity")
    if raw_views is None:
        return {
            "status": "PASS" if summary_receipt is not None else "NOT_SUPPLIED",
            "summary_receipt": summary_receipt,
            "view_count": 0,
            "views": {},
        }
    if not isinstance(raw_views, Mapping):
        raise TypeError("candidate duplicate membership views must be a mapping")

    views: dict[str, Any] = {}
    for name in sorted(raw_views):
        raw_receipt = raw_views[name]
        if not isinstance(raw_receipt, Mapping):
            raise TypeError("candidate duplicate view receipt must be a mapping")
        supplied_count = raw_receipt.get(
            "pair_count",
            raw_receipt.get(
                "membership_pair_count",
                raw_receipt.get("membershipCount"),
            ),
        )
        supplied_sha = raw_receipt.get(
            "pair_sha256",
            raw_receipt.get(
                "pair_set_sha256",
                raw_receipt.get("pairSha256"),
            ),
        )
        if supplied_count is None or supplied_sha is None:
            raise AssertionError(f"candidate membership view {name!r} receipt is incomplete")
        if int(supplied_count) != pair_count or supplied_sha != pair_sha256:
            raise AssertionError(f"candidate membership view {name!r} differs from SQLite")
        views[str(name)] = {
            "pair_count": int(supplied_count),
            "pair_sha256": str(supplied_sha),
            "matches_sqlite": True,
        }
    return {
        "status": "PASS",
        "summary_receipt": summary_receipt,
        "view_count": len(views),
        "views": views,
    }


def _co_membership_bitset_analysis(
    public_ids: Sequence[str],
    folders_by_object: Mapping[str, Sequence[str]],
    public_folder_masks: Mapping[str, int],
) -> dict[str, Any]:
    object_count = len(public_ids)
    all_mask = (1 << object_count) - 1
    degrees = [len(folders_by_object.get(stable_id, ())) for stable_id in public_ids]
    degree_masks: dict[int, int] = defaultdict(int)
    for ordinal, degree in enumerate(degrees):
        degree_masks[degree] |= 1 << ordinal

    fanout_ge1: list[int] = []
    fanout_ge2: list[int] = []
    fanout_ge3: list[int] = []
    directed_exact_shared: Counter[int] = Counter()
    directed_degree_shared: Counter[tuple[int, int, int]] = Counter()

    started = time.perf_counter()
    for ordinal, stable_id in enumerate(public_ids):
        folder_masks = [
            public_folder_masks[folder_id]
            for folder_id in folders_by_object.get(stable_id, ())
        ]
        at_least_masks: list[int] = []
        for shared_count in range(1, len(folder_masks) + 1):
            at_least = 0
            for combination in itertools.combinations(folder_masks, shared_count):
                intersection = combination[0]
                for mask in combination[1:]:
                    intersection &= mask
                at_least |= intersection
            at_least &= all_mask ^ (1 << ordinal)
            at_least_masks.append(at_least)

        fanout_ge1.append(at_least_masks[0].bit_count() if at_least_masks else 0)
        fanout_ge2.append(at_least_masks[1].bit_count() if len(at_least_masks) > 1 else 0)
        fanout_ge3.append(at_least_masks[2].bit_count() if len(at_least_masks) > 2 else 0)

        object_degree = len(folder_masks)
        for index, at_least in enumerate(at_least_masks):
            shared_count = index + 1
            next_at_least = at_least_masks[index + 1] if index + 1 < len(at_least_masks) else 0
            exact = at_least & ~next_at_least & all_mask
            directed_exact_shared[shared_count] += exact.bit_count()
            for neighbor_degree, degree_mask in degree_masks.items():
                count = (exact & degree_mask).bit_count()
                if count:
                    key = (
                        min(object_degree, neighbor_degree),
                        max(object_degree, neighbor_degree),
                        shared_count,
                    )
                    directed_degree_shared[key] += count

    core_ms = (time.perf_counter() - started) * 1000
    if any(count % 2 for count in directed_exact_shared.values()):
        raise AssertionError("directed shared-container counts are not pair-symmetric")
    if any(count % 2 for count in directed_degree_shared.values()):
        raise AssertionError("degree/shared histogram is not pair-symmetric")

    shared_histogram = {
        shared_count: count // 2
        for shared_count, count in sorted(directed_exact_shared.items())
    }
    degree_shared_histogram = {
        key: count // 2 for key, count in sorted(directed_degree_shared.items())
    }
    unique_ge1 = sum(shared_histogram.values())
    unique_ge2 = sum(count for shared, count in shared_histogram.items() if shared >= 2)
    unique_ge3 = sum(count for shared, count in shared_histogram.items() if shared >= 3)
    if sum(fanout_ge1) // 2 != unique_ge1:
        raise AssertionError("fanout >=1 does not reconcile to unique pairs")
    if sum(fanout_ge2) // 2 != unique_ge2:
        raise AssertionError("fanout >=2 does not reconcile to unique pairs")
    if sum(fanout_ge3) // 2 != unique_ge3:
        raise AssertionError("fanout >=3 does not reconcile to unique pairs")

    jaccard_histogram: Counter[Fraction] = Counter()
    for (left_degree, right_degree, shared_count), count in degree_shared_histogram.items():
        jaccard_histogram[
            Fraction(shared_count, left_degree + right_degree - shared_count)
        ] += count

    jaccard_rows = [
        {
            "numerator": value.numerator,
            "denominator": value.denominator,
            "value": _number(float(value)),
            "pair_count": count,
        }
        for value, count in sorted(jaccard_histogram.items())
    ]
    return {
        "algorithm": {
            "id": DERIVATION_VERSION,
            "public_id_order": "surface_id_exact Unicode code-point ascending",
            "index": "per-folder arbitrary-precision integer membership bitset",
            "threshold_method": "OR of k-way container-bitset intersections",
            "global_pair_method": "half of exact directed fanout sums",
            "matrix_materialized": False,
            "pair_rows_materialized": False,
            "pair_identifiers_emitted": False,
            "time_complexity": "O(objects * combinations(memberships_per_object)) bitset operations",
            "working_memory": "O(nonempty_containers * public_objects / 8)",
        },
        "unique_pair_count_ge1": unique_ge1,
        "unique_pair_count_ge2": unique_ge2,
        "unique_pair_count_ge3": unique_ge3,
        "shared_container_count_histogram": {
            str(shared): count for shared, count in shared_histogram.items()
        },
        "fanout_ge1": _distribution(fanout_ge1),
        "fanout_ge2": _distribution(fanout_ge2),
        "fanout_ge3": _distribution(fanout_ge3),
        "degree_shared_container_histogram": [
            {
                "left_membership_count": left,
                "right_membership_count": right,
                "shared_container_count": shared,
                "pair_count": count,
            }
            for (left, right, shared), count in degree_shared_histogram.items()
        ],
        "jaccard_structural_diagnostic": {
            "classification": "STRUCTURAL_DIAGNOSTIC",
            "historical_relation": False,
            "semantic_relation": False,
            "final_similarity_metric": False,
            "histogram": jaccard_rows,
            "p50": _weighted_r7_quantile(jaccard_histogram, 0.50),
            "p90": _weighted_r7_quantile(jaccard_histogram, 0.90),
            "p95": _weighted_r7_quantile(jaccard_histogram, 0.95),
            "p99": _weighted_r7_quantile(jaccard_histogram, 0.99),
            "max": _number(float(max(jaccard_histogram, default=Fraction(0, 1)))),
        },
        "_core_ms": core_ms,
    }


def analyze(
    *,
    sqlite_path: Path | str,
    ledger_path: Path | str,
    candidate_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return an aggregate-only deterministic curatorial analysis receipt."""

    total_started = time.perf_counter()
    sqlite_file = Path(sqlite_path).resolve()
    ledger_file = Path(ledger_path).resolve()

    hash_started = time.perf_counter()
    sqlite_sha256 = _sha256_file(sqlite_file)
    ledger_sha256 = _sha256_file(ledger_file)
    hash_ms = (time.perf_counter() - hash_started) * 1000
    if sqlite_sha256 != EXPECTED_SQLITE_SHA256:
        raise AssertionError("immutable SQLite SHA-256 differs from frozen source")
    if ledger_sha256 != EXPECTED_LEDGER_SHA256:
        raise AssertionError("eligibility ledger SHA-256 differs from authoritative source")

    ledger_started = time.perf_counter()
    dispositions, cohort = _load_ledger(ledger_file)
    public_ids = _cohort_ids(dispositions, "eligible")
    held_ids = _cohort_ids(dispositions, "held")
    public_ordinals = {stable_id: index for index, stable_id in enumerate(public_ids)}
    ledger_ms = (time.perf_counter() - ledger_started) * 1000

    sanitized_candidate = (
        _sanitize_candidate_summary(candidate_summary) if candidate_summary is not None else None
    )

    sqlite_started = time.perf_counter()
    connection = _connect_immutable(sqlite_file)
    object_rows = list(
        connection.execute(
            """SELECT surface_id, source_document_id, source_name, trace_tree_id
               FROM objects ORDER BY surface_id"""
        )
    )
    object_ids = {row["surface_id"] for row in object_rows}
    if object_ids != set(dispositions):
        raise AssertionError("SQLite objects do not match authoritative eligibility ledger")

    folder_type_by_id: dict[str, str] = {}
    folders_by_object: dict[str, list[str]] = defaultdict(list)
    folder_counts: dict[str, Counter[str]] = defaultdict(Counter)
    public_folder_masks: dict[str, int] = defaultdict(int)
    pair_digest = hashlib.sha256()
    membership_count = 0
    for row in connection.execute(
        """SELECT surface_id, folder_id, folder_type
           FROM object_folder_refs ORDER BY folder_id, surface_id"""
    ):
        stable_id = row["surface_id"]
        folder_id = row["folder_id"]
        folder_type = row["folder_type"]
        prior_type = folder_type_by_id.setdefault(folder_id, folder_type)
        if prior_type != folder_type:
            raise AssertionError("folder identity has inconsistent types")
        state = dispositions[stable_id]
        folders_by_object[stable_id].append(folder_id)
        folder_counts[folder_id]["all"] += 1
        folder_counts[folder_id][state] += 1
        if state == "eligible":
            public_folder_masks[folder_id] |= 1 << public_ordinals[stable_id]
        pair_digest.update(f"{folder_id}\t{stable_id}\n".encode("utf-8"))
        membership_count += 1

    if len(folder_type_by_id) != EXPECTED_FOLDER_COUNT:
        raise AssertionError("folder count changed")
    if membership_count != EXPECTED_MEMBERSHIP_COUNT:
        raise AssertionError("folder membership count changed")
    if set(folder_type_by_id.values()) != EXPECTED_FOLDER_TYPES:
        raise AssertionError("observed folder-type vocabulary changed")
    folder_pair_sha256 = pair_digest.hexdigest()
    if folder_pair_sha256 != EXPECTED_FOLDER_PAIR_SHA256:
        raise AssertionError("sorted folder/object membership pair set changed")

    collection_rows = [
        (row["surface_id"], row["value"])
        for row in connection.execute(
            """SELECT surface_id, value FROM object_metadata_rows
               WHERE table_kind='SOURCE' AND label='Source collection'
               ORDER BY surface_id, row_order"""
        )
    ]
    legacy_table_names = (
        "source_documents",
        "object_metadata_rows",
        "capture_records",
        "trace_nodes",
        "trace_edges",
        "object_trace_edges",
    )
    legacy_table_counts = {
        table: int(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0])
        for table in legacy_table_names
    }
    trace_edge_memberships: list[tuple[str, str]] = [
        (row["surface_id"], row["edge_id"])
        for row in connection.execute(
            "SELECT surface_id, edge_id FROM object_trace_edges ORDER BY surface_id, edge_id"
        )
    ]
    connection.close()
    sqlite_ms = (time.perf_counter() - sqlite_started) * 1000

    all_ids = sorted(dispositions)
    folder_ids = sorted(folder_type_by_id)
    object_membership_values = {
        "all": [len(folders_by_object.get(stable_id, ())) for stable_id in all_ids],
        "eligible": [len(folders_by_object.get(stable_id, ())) for stable_id in public_ids],
        "held": [len(folders_by_object.get(stable_id, ())) for stable_id in held_ids],
    }
    folder_census_by_cohort: dict[str, Any] = {}
    for state in ("all", "eligible", "held"):
        object_values = object_membership_values[state]
        all_known_container_sizes = [
            folder_counts[folder_id][state] for folder_id in folder_ids
        ]
        populated_container_sizes = [
            size for size in all_known_container_sizes if size > 0
        ]
        folder_census_by_cohort[state] = {
            "object_count": len(object_values),
            "membership_count": sum(object_values),
            "nonempty_container_count": len(populated_container_sizes),
            "objects_with_multiple_memberships": sum(value > 1 for value in object_values),
            "objects_without_membership": sum(value == 0 for value in object_values),
            "memberships_per_object": _distribution(object_values),
            "container_size": _distribution(populated_container_sizes),
            "all_known_container_size_including_zero": _distribution(
                all_known_container_sizes
            ),
            "raw_pair_event_count": sum(
                size * (size - 1) // 2 for size in all_known_container_sizes
            ),
        }

    folder_type_rows: dict[str, Any] = {}
    for folder_type in sorted(EXPECTED_FOLDER_TYPES):
        typed_folder_ids = [
            folder_id
            for folder_id in folder_ids
            if folder_type_by_id[folder_id] == folder_type
        ]
        row: dict[str, Any] = {"container_count": len(typed_folder_ids)}
        for state, ids in (("public", public_ids), ("held", held_ids)):
            source_state = "eligible" if state == "public" else "held"
            sizes = [folder_counts[folder_id][source_state] for folder_id in typed_folder_ids]
            row[state] = {
                "membership_count": sum(sizes),
                "object_coverage": sum(
                    any(
                        folder_type_by_id[folder_id] == folder_type
                        for folder_id in folders_by_object.get(stable_id, ())
                    )
                    for stable_id in ids
                ),
                "nonempty_container_count": sum(size > 0 for size in sizes),
                "container_size": _distribution(sizes),
                "raw_pair_event_count": sum(size * (size - 1) // 2 for size in sizes),
            }
        folder_type_rows[folder_type] = row

    public_pair_events = folder_census_by_cohort["eligible"]["raw_pair_event_count"]
    held_pair_events = folder_census_by_cohort["held"]["raw_pair_event_count"]
    all_pair_events = folder_census_by_cohort["all"]["raw_pair_event_count"]
    cross_cohort_pair_events = sum(
        folder_counts[folder_id]["eligible"] * folder_counts[folder_id]["held"]
        for folder_id in folder_ids
    )
    if all_pair_events != public_pair_events + held_pair_events + cross_cohort_pair_events:
        raise AssertionError("all-cohort pair events do not reconcile")

    largest_pair_producers = sorted(
        folder_ids,
        key=lambda folder_id: (
            -folder_counts[folder_id]["eligible"],
            folder_type_by_id[folder_id],
            folder_id,
        ),
    )[:15]
    sanitized_largest = [
        {
            "rank": rank,
            "folder_type": folder_type_by_id[folder_id],
            "public_members": folder_counts[folder_id]["eligible"],
            "held_members": folder_counts[folder_id]["held"],
            "all_members": folder_counts[folder_id]["all"],
            "public_raw_pair_events": folder_counts[folder_id]["eligible"]
            * (folder_counts[folder_id]["eligible"] - 1)
            // 2,
        }
        for rank, folder_id in enumerate(largest_pair_producers, start=1)
    ]

    co_membership = _co_membership_bitset_analysis(
        public_ids, folders_by_object, public_folder_masks
    )
    co_membership_core_ms = float(co_membership.pop("_core_ms"))
    if sum(
        int(shared) * count
        for shared, count in co_membership["shared_container_count_histogram"].items()
    ) != public_pair_events:
        raise AssertionError("raw pair events do not reconcile to shared-container histogram")

    possible_public_pairs = EXPECTED_PUBLIC_COUNT * (EXPECTED_PUBLIC_COUNT - 1) // 2
    pair_explosion = {
        "risk": "HIGH",
        "risk_policy": "HIGH when exact unique pairs or raw pair events exceed 10,000,000",
        "possible_public_pair_count": possible_public_pairs,
        "public_raw_pair_event_count": public_pair_events,
        "public_unique_pair_count": co_membership["unique_pair_count_ge1"],
        "public_unique_pair_support_rate": _number(
            co_membership["unique_pair_count_ge1"] / possible_public_pairs
        ),
        "raw_event_to_unique_pair_ratio": _number(
            public_pair_events / co_membership["unique_pair_count_ge1"]
        ),
        "materialization_estimates_bytes": {
            "upper_triangle_uint8": possible_public_pairs,
            "upper_triangle_uint64": possible_public_pairs * 8,
            "upper_triangle_16_byte_record": possible_public_pairs * 16,
            "raw_event_uint64": public_pair_events * 8,
            "raw_event_16_byte_record": public_pair_events * 16,
            "dense_uint8_matrix": EXPECTED_PUBLIC_COUNT**2,
            "dense_float64_matrix": EXPECTED_PUBLIC_COUNT**2 * 8,
        },
        "folder_bitset_payload_bytes": len(public_folder_masks)
        * math.ceil(EXPECTED_PUBLIC_COUNT / 8),
        "full_pair_matrix_committed": False,
        "full_pair_rows_committed": False,
        "recommended_future_architecture": "precomputed aggregate index plus on-demand object fanout",
    }

    source_structure_census = {
        "source_document": _structure_census(
            ((row["surface_id"], row["source_document_id"]) for row in object_rows),
            dispositions,
        ),
        "source_name": _structure_census(
            ((row["surface_id"], row["source_name"]) for row in object_rows),
            dispositions,
        ),
        "source_collection": _structure_census(collection_rows, dispositions),
    }
    legacy_tree_census = _structure_census(
        ((row["surface_id"], row["trace_tree_id"]) for row in object_rows),
        dispositions,
    )
    legacy_edge_membership_census = _structure_census(
        trace_edge_memberships, dispositions
    )

    duplicate_view_receipt = _candidate_duplicate_view_receipt(
        sanitized_candidate,
        pair_count=membership_count,
        pair_sha256=folder_pair_sha256,
    )

    structure_classification = [
        {
            "structure": "sqlite.object_folder_refs",
            "classifications": ["POPULATED", "LEGACY_ONLY", "CANDIDATE", "INTERNAL_ONLY", "UNSAFE"],
            "row_count": membership_count,
            "semantic_relation": False,
            "historical_relation": False,
        },
        {
            "structure": "sqlite.source_documents",
            "classifications": ["POPULATED", "LEGACY_ONLY", "INTERNAL_ONLY", "UNSAFE"],
            "row_count": legacy_table_counts["source_documents"],
            "semantic_relation": False,
            "historical_relation": False,
        },
        {
            "structure": "sqlite.object_metadata_rows/source_collection",
            "classifications": ["POPULATED", "LEGACY_ONLY", "CANDIDATE", "INTERNAL_ONLY", "UNSAFE"],
            "row_count": len(collection_rows),
            "semantic_relation": False,
            "historical_relation": False,
        },
        {
            "structure": "sqlite.objects/trace_tree_id",
            "classifications": ["POPULATED", "LEGACY_ONLY", "INTERNAL_ONLY", "UNSAFE"],
            "row_count": sum(bool(str(row["trace_tree_id"] or "").strip()) for row in object_rows),
            "semantic_relation": False,
            "historical_relation": False,
        },
        {
            "structure": "sqlite.trace_nodes",
            "classifications": ["POPULATED", "LEGACY_ONLY", "INTERNAL_ONLY", "UNSAFE"],
            "row_count": legacy_table_counts["trace_nodes"],
            "semantic_relation": False,
            "historical_relation": False,
        },
        {
            "structure": "sqlite.trace_edges",
            "classifications": ["POPULATED", "LEGACY_ONLY", "INTERNAL_ONLY", "UNSAFE"],
            "row_count": legacy_table_counts["trace_edges"],
            "semantic_relation": False,
            "historical_relation": False,
        },
        {
            "structure": "sqlite.object_trace_edges",
            "classifications": ["POPULATED", "LEGACY_ONLY", "INTERNAL_ONLY", "UNSAFE"],
            "row_count": legacy_table_counts["object_trace_edges"],
            "semantic_relation": False,
            "historical_relation": False,
        },
        {
            "structure": "candidate_summary",
            "classifications": ["UNKNOWN"] if sanitized_candidate is None else ["CANDIDATE", "INTERNAL_ONLY"],
            "row_count": 0 if sanitized_candidate is None else None,
            "semantic_relation": False,
            "historical_relation": False,
        },
    ]

    deterministic_payload: dict[str, Any] = {
        "format": FORMAT,
        "derivation_version": DERIVATION_VERSION,
        "semantic_boundary": {
            "analysis_role": "exploratory_derived_signal",
            "classification": "STRUCTURAL_DIAGNOSTIC",
            "similarity_model_selected": False,
            "ranking_selected": False,
            "probability_model_selected": False,
            "semantic_relation": False,
            "historical_relation": False,
            "held_rows_in_public_statistics": 0,
            "raw_identifiers_emitted": 0,
        },
        "source_receipt": {
            "sqlite_sha256": sqlite_sha256,
            "ledger_sha256": ledger_sha256,
            "sqlite_open_mode": "mode=ro&immutable=1;PRAGMA query_only=ON",
            "sqlite_quick_check": "ok",
            "candidate_summary_supplied": sanitized_candidate is not None,
        },
        "cohort": cohort,
        "structure_classification": structure_classification,
        "folder_census": {
            "folder_count": len(folder_ids),
            "observed_folder_type_count": len(EXPECTED_FOLDER_TYPES),
            "observed_folder_types": sorted(EXPECTED_FOLDER_TYPES),
            "membership_pair_count": membership_count,
            "membership_pair_sha256": folder_pair_sha256,
            "pair_semantics": "project-curated container membership; not historical relation",
            "by_cohort": folder_census_by_cohort,
            "by_type": folder_type_rows,
            "cross_public_held_pair_event_count": cross_cohort_pair_events,
            "largest_public_pair_producers": sanitized_largest,
        },
        "duplicate_membership_view_integrity": duplicate_view_receipt,
        "co_membership": co_membership,
        "pair_explosion": pair_explosion,
        "source_structure_census": source_structure_census,
        "legacy_structure_census": {
            "sqlite_table_counts": legacy_table_counts,
            "trace_tree_membership": legacy_tree_census,
            "object_trace_edge_membership": legacy_edge_membership_census,
            "classification": "LEGACY_ONLY_UNSAFE_NOT_V49_GOVERNED",
        },
        "candidate_structure_summary": sanitized_candidate,
        "invariants": {
            "CURATORIAL_COUNTS_RECONCILE": True,
            "PUBLIC_HELD_PARTITION_COMPLETE": True,
            "HELD_EXPLORATION_OBJECT_COUNT": 0,
            "PAIR_EVENTS_RECONCILE": True,
            "PAIR_MATRIX_MATERIALIZED": False,
            "PAIR_ROWS_EMITTED": False,
            "STRUCTURAL_DIAGNOSTIC_ONLY": True,
            "SIMILARITY_MODEL_SELECTED": False,
        },
    }
    deterministic_sha256 = hashlib.sha256(_canonical_bytes(deterministic_payload)).hexdigest()
    result = dict(deterministic_payload)
    result["deterministic_receipt"] = {
        "canonicalization": "recursive key sort; compact JSON; final LF; UTF-8",
        "sha256": deterministic_sha256,
    }
    result["performance"] = {
        "input_hash_ms": round(hash_ms, 3),
        "ledger_load_ms": round(ledger_ms, 3),
        "sqlite_load_and_census_ms": round(sqlite_ms, 3),
        "co_membership_core_ms": round(co_membership_core_ms, 3),
        "total_analysis_ms": round((time.perf_counter() - total_started) * 1000, 3),
        "peak_rss_bytes": _peak_rss_bytes(),
    }
    return result


def _load_candidate_summary(path: Path | None) -> Mapping[str, Any] | None:
    if path is None:
        return None
    value = json.loads(path.read_text("utf-8"))
    if not isinstance(value, Mapping):
        raise TypeError("candidate summary JSON must contain an object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--candidate-summary", type=Path)
    parser.add_argument("--output", default="-", help="canonical JSON path or '-' for stdout")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run twice and require identical deterministic receipt SHA-256",
    )
    args = parser.parse_args()

    candidate_summary = _load_candidate_summary(args.candidate_summary)
    result = analyze(
        sqlite_path=args.sqlite,
        ledger_path=args.ledger,
        candidate_summary=candidate_summary,
    )
    if args.self_test:
        second = analyze(
            sqlite_path=args.sqlite,
            ledger_path=args.ledger,
            candidate_summary=candidate_summary,
        )
        first_sha = result["deterministic_receipt"]["sha256"]
        second_sha = second["deterministic_receipt"]["sha256"]
        if first_sha != second_sha:
            raise AssertionError("two-run deterministic receipt mismatch")
        result["self_test"] = {
            "status": "PASS",
            "run_count": 2,
            "deterministic_receipt_sha256": first_sha,
        }

    payload = _json_bytes(result)
    if args.output == "-":
        sys.stdout.buffer.write(payload)
    else:
        output_path = Path(args.output)
        if not output_path.parent.exists():
            raise FileNotFoundError(f"output parent does not exist: {output_path.parent}")
        output_path.write_bytes(payload)
        print(
            "CURATORIAL_ANALYSIS=PASS "
            f"OUTPUT={output_path} "
            f"SHA256={result['deterministic_receipt']['sha256']} "
            f"PUBLIC_PAIRS={result['co_membership']['unique_pair_count_ge1']}"
        )


if __name__ == "__main__":
    main()
