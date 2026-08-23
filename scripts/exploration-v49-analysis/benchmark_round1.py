#!/usr/bin/env python3
"""Benchmark Exploration Round 1 analysis stages without changing outputs."""

from __future__ import annotations

import argparse
import gc
import gzip
import hashlib
import json
import math
import resource
import sys
import time
import tracemalloc
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import generate_round1 as generator


SCHEMA_VERSION = "trace-exploration-round1-benchmark/v1"
DERIVATION_VERSION = "trace-exploration-round1-benchmark-v1"


class BenchmarkError(RuntimeError):
    """Raised when a benchmark run cannot reproduce the frozen workload."""


def _peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def _r7(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _distribution(values: Sequence[float]) -> dict[str, float | int]:
    if not values:
        return {"n": 0, "p50Ms": 0.0, "p95Ms": 0.0, "p99Ms": 0.0, "maxMs": 0.0}
    return {
        "n": len(values),
        "p50Ms": round(_r7(values, 0.50), 3),
        "p95Ms": round(_r7(values, 0.95), 3),
        "p99Ms": round(_r7(values, 0.99), 3),
        "maxMs": round(max(values), 3),
    }


def _timed(function: Any, *args: Any, **kwargs: Any) -> tuple[Any, float]:
    started = time.perf_counter()
    value = function(*args, **kwargs)
    return value, (time.perf_counter() - started) * 1000


def _curatorial_folder_inverted_index_benchmark(
    module: Any,
    *,
    sqlite_path: Path | str,
    ledger_path: Path | str,
) -> tuple[dict[str, Any], float]:
    """Time the ordered folder-membership scan and its two in-memory indexes.

    Ledger validation, public-ordinal construction, and immutable connection
    setup happen outside the timed interval. The measured interval includes
    SQLite row iteration, construction of object-to-folder adjacency lists,
    construction of public folder bitsets, and the deterministic membership-pair
    digest.
    """

    dispositions, _ = module._load_ledger(Path(ledger_path).resolve())
    public_ids = module._cohort_ids(dispositions, "eligible")
    public_ordinals = {
        stable_id: ordinal for ordinal, stable_id in enumerate(public_ids)
    }
    connection = module._connect_immutable(Path(sqlite_path).resolve())

    def build() -> dict[str, Any]:
        folder_type_by_id: dict[str, str] = {}
        folders_by_object: dict[str, list[str]] = defaultdict(list)
        public_folder_masks: dict[str, int] = defaultdict(int)
        pair_digest = hashlib.sha256()
        membership_count = 0
        public_membership_count = 0
        for row in connection.execute(
            """SELECT surface_id, folder_id, folder_type
               FROM object_folder_refs ORDER BY folder_id, surface_id"""
        ):
            stable_id = str(row["surface_id"])
            folder_id = str(row["folder_id"])
            folder_type = str(row["folder_type"])
            prior_type = folder_type_by_id.setdefault(folder_id, folder_type)
            if prior_type != folder_type:
                raise BenchmarkError("folder identity has inconsistent types")
            state = dispositions[stable_id]
            folders_by_object[stable_id].append(folder_id)
            if state == "eligible":
                public_folder_masks[folder_id] |= 1 << public_ordinals[stable_id]
                public_membership_count += 1
            pair_digest.update(f"{folder_id}\t{stable_id}\n".encode("utf-8"))
            membership_count += 1

        mask_membership_count = sum(
            mask.bit_count() for mask in public_folder_masks.values()
        )
        return {
            "folderCount": len(folder_type_by_id),
            "membershipCount": membership_count,
            "indexedObjectCount": len(folders_by_object),
            "publicObjectCount": len(public_ids),
            "publicFolderCount": sum(
                1 for mask in public_folder_masks.values() if mask
            ),
            "publicMembershipCount": public_membership_count,
            "publicMaskMembershipCount": mask_membership_count,
            "membershipPairSha256": pair_digest.hexdigest(),
        }

    try:
        counts, elapsed_ms = _timed(build)
    finally:
        connection.close()

    expected = {
        "folderCount": int(module.EXPECTED_FOLDER_COUNT),
        "membershipCount": int(module.EXPECTED_MEMBERSHIP_COUNT),
        "indexedObjectCount": int(module.EXPECTED_OBJECT_COUNT),
        "publicObjectCount": generator.PUBLIC_OBJECT_COUNT,
        "membershipPairSha256": str(module.EXPECTED_FOLDER_PAIR_SHA256),
    }
    for field, expected_value in expected.items():
        if counts[field] != expected_value:
            raise BenchmarkError(
                f"curatorial folder-index {field} changed: "
                f"{counts[field]!r} != {expected_value!r}"
            )
    if counts["publicMembershipCount"] != counts["publicMaskMembershipCount"]:
        raise BenchmarkError("curatorial public folder bitsets lost memberships")
    return counts, elapsed_ms


def _missingness_stage_benchmark(
    module: Any,
    records: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, float]]:
    """Time missingness normalization, vector build, and census separately."""

    normalized, normalization_ms = _timed(
        lambda: sorted(
            (module._normalize_record(record) for record in records),
            key=lambda row: row["objectId"],
        )
    )
    if len(normalized) != generator.PUBLIC_OBJECT_COUNT:
        raise BenchmarkError("missingness normalization changed cohort size")
    object_ids = [str(record["objectId"]) for record in normalized]
    if len(object_ids) != len(set(object_ids)):
        raise BenchmarkError("missingness normalization produced duplicate IDs")

    def build_vectors() -> list[dict[str, Any]]:
        vectors: list[dict[str, Any]] = []
        for record in normalized:
            creator_status = module.creator_state(record["creator"])
            active_states = module._active_states(record, creator_status)
            vectors.append({
                "objectId": record["objectId"],
                "movementContextState": (
                    "OBSERVED"
                    if record["movement_context"]
                    else "NO_PUBLISHED_MOVEMENT_CONTEXT"
                ),
                "movementContextCount": len(record["movement_context"]),
                "temporalPrecision": record["temporalPrecision"],
                "temporalUncertaintyState": (
                    "APPROXIMATE"
                    if record["temporalPrecision"] == "approximate"
                    else "RANGE"
                    if record["temporalPrecision"] == "range"
                    else "UNKNOWN_SOURCE_VALUE"
                    if record["temporalPrecision"] == "unknown"
                    else "OBSERVED"
                ),
                "temporalRangeSpanYears": (
                    record["endYear"] - record["startYear"] + 1
                    if record["temporalPrecision"] == "range"
                    else None
                ),
                "geographyMappingState": record["geographyState"],
                "geographyClass": record["geographyClass"],
                "geographyQualified": record["geographyQualified"],
                "multiRegion": record["multiRegion"],
                "creatorState": creator_status,
                "sourceState": "OBSERVED",
                "objectTypeState": "OBSERVED",
                "sourceCollectionPresent": record["sourceCollectionPresent"],
                "activeStates": list(active_states),
            })
        return vectors

    vectors, vector_ms = _timed(build_vectors)

    def build_census() -> dict[str, Any]:
        precision_counts: Counter[str] = Counter()
        geography_counts: Counter[str] = Counter()
        creator_counts: Counter[str] = Counter()
        state_counts: Counter[str] = Counter()
        cooccurrence_counts: Counter[tuple[str, str]] = Counter()
        for vector in vectors:
            precision_counts[str(vector["temporalPrecision"])] += 1
            geography_counts[str(vector["geographyMappingState"])] += 1
            creator_counts[str(vector["creatorState"])] += 1
            active_states = tuple(str(value) for value in vector["activeStates"])
            state_counts.update(active_states)
            for index, left in enumerate(active_states):
                for right in active_states[index + 1:]:
                    cooccurrence_counts[(left, right)] += 1
        field_matrix = module._field_matrix(
            vectors, precision_counts, geography_counts, creator_counts
        )
        denominator = len(vectors)
        cooccurrences = [
            {
                "stateA": left,
                "stateB": right,
                "count": count,
                "eligibleDenominator": denominator,
                "supportRate": count / denominator if denominator else 0.0,
                "interpretation": "OBSERVED_INTERSECTION_ONLY_NO_CAUSAL_INFERENCE",
            }
            for (left, right), count in sorted(cooccurrence_counts.items())
        ]
        return {
            "normalizedRecordCount": len(normalized),
            "objectVectorCount": len(vectors),
            "activeStateEventCount": sum(state_counts.values()),
            "cooccurrenceCellCount": len(cooccurrences),
            "fieldMatrix": field_matrix,
            "cooccurrences": cooccurrences,
        }

    census, census_ms = _timed(build_census)
    field_matrix = census.pop("fieldMatrix")
    cooccurrences = census.pop("cooccurrences")
    counts = {
        **census,
        "objectVectorsSha256": module.sha256_json(vectors),
        "fieldMatrixSha256": module.sha256_json(field_matrix),
        "cooccurrencesSha256": module.sha256_json(cooccurrences),
    }
    return counts, {
        "missingness_normalization_ms": normalization_ms,
        "missingness_object_vector_build_ms": vector_ms,
        "missingness_aggregate_census_ms": census_ms,
    }


def _cross_stage_benchmark(
    module: Any,
    records: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, float]]:
    normalized, normalize_ms = _timed(
        lambda: sorted(
            (module._normalize_record(record) for record in records),
            key=lambda row: row["objectId"],
        )
    )
    if len(normalized) != generator.PUBLIC_OBJECT_COUNT:
        raise BenchmarkError("cross-dimensional normalization changed cohort size")
    labels = module._validate_label_registry(normalized)
    extensions = module._normalize_extension_pairs(generator.CURATORIAL_EXTENSION_PAIRS)
    pair_specs = tuple(module.BASE_PAIR_SPECS) + extensions
    frequency_dimensions = list(module.BASE_FREQUENCY_DIMENSIONS)
    for dimension in sorted({value for pair in extensions for value in pair}):
        if dimension not in frequency_dimensions:
            frequency_dimensions.append(dimension)

    frequency_result, frequency_ms = _timed(
        module._frequency_rows,
        normalized,
        frequency_dimensions,
        labels,
    )
    frequency_rows, marginals, coverage = frequency_result
    pair_result, pair_ms = _timed(
        module._pair_rows,
        normalized,
        pair_specs,
        labels,
        marginals,
        coverage,
        generator.RARE_MAX_COUNT,
    )
    pair_rows, pair_density = pair_result
    triple_result, triple_ms = _timed(
        module._triple_rows,
        normalized,
        module.BASE_TRIPLE_SPECS,
        labels,
        marginals,
        coverage,
        generator.RARE_MAX_COUNT,
    )
    triple_rows, triple_density = triple_result
    concentration_rows, concentration_ms = _timed(
        module._source_concentration_rows,
        normalized,
        labels,
        generator.MINIMUM_SUBSET_SUPPORT,
    )
    dimension_concentration_rows, dimension_concentration_ms = _timed(
        module._dimension_concentration_rows,
        normalized,
        labels,
        generator.DERIVATION_VERSION,
    )
    dimension_assignments = {
        str(row["dimension"]): int(row["assignmentCount"])
        for row in dimension_concentration_rows
    }
    counts = {
        "normalizedRecordCount": len(normalized),
        "frequencyRowCount": len(frequency_rows),
        "pairObservedCellCount": len(pair_rows),
        "pairSummaryCount": len(pair_density),
        "tripleObservedCellCount": len(triple_rows),
        "tripleSummaryCount": len(triple_density),
        "sourceConcentrationRowCount": len(concentration_rows),
        "dimensionConcentrationRowCount": len(dimension_concentration_rows),
        "dimensionConcentrationAssignmentCounts": dimension_assignments,
    }
    expected = {
        "normalizedRecordCount": 7_995,
        "frequencyRowCount": 3_364,
        "pairObservedCellCount": 6_146,
        "pairSummaryCount": 18,
        "tripleObservedCellCount": 2_399,
        "tripleSummaryCount": 6,
        "sourceConcentrationRowCount": 59,
        "dimensionConcentrationRowCount": 4,
        "dimensionConcentrationAssignmentCounts": {
            "source": 7_995,
            "decade": 8_033,
            "geography": 7_996,
            "curated_container": 24_102,
        },
    }
    if counts != expected:
        raise BenchmarkError(f"cross workload shape changed: {counts}")
    return counts, {
        "cross_normalization_index_ms": normalize_ms,
        "one_dimension_frequency_ms": frequency_ms,
        "two_dimension_observed_cells_ms": pair_ms,
        "three_dimension_observed_cells_ms": triple_ms,
        "source_concentration_ms": concentration_ms,
        "dimension_concentration_ms": dimension_concentration_ms,
    }


def _file_metrics(
    research: Mapping[str, bytes],
    raw: Mapping[str, bytes],
    generation: Mapping[str, Any],
) -> list[dict[str, Any]]:
    row_counts = generation["rowCounts"]
    rows: list[dict[str, Any]] = []
    for group, files in (("RESEARCH_TSV", research), ("AUDIT_RAW_JSON", raw)):
        for filename, payload in sorted(files.items()):
            compressed = gzip.compress(payload, compresslevel=9, mtime=0)
            rows.append({
                "group": group,
                "filename": filename,
                "rowCount": row_counts.get(filename),
                "rawBytes": len(payload),
                "gzipBytes": len(compressed),
                "gzipRatio": round(len(compressed) / len(payload), 9) if payload else 0.0,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "gzipSha256": hashlib.sha256(compressed).hexdigest(),
            })
    return rows


def _benchmark_body(iterations: int) -> dict[str, Any]:
    if isinstance(iterations, bool) or not isinstance(iterations, int) or not 1 <= iterations <= 20:
        raise BenchmarkError("iterations must be an integer from 1 through 20")
    modules = generator._import_modules()
    common = modules["common"]
    timings: dict[str, list[float]] = {
        "source_inventory_ms": [],
        "curatorial_index_and_co_membership_ms": [],
        "curatorial_folder_inverted_index_ms": [],
        "curatorial_co_membership_core_ms": [],
        "normalized_public_record_load_ms": [],
        "missingness_end_to_end_ms": [],
        "missingness_normalization_ms": [],
        "missingness_object_vector_build_ms": [],
        "missingness_aggregate_census_ms": [],
        "cross_normalization_index_ms": [],
        "one_dimension_frequency_ms": [],
        "two_dimension_observed_cells_ms": [],
        "three_dimension_observed_cells_ms": [],
        "source_concentration_ms": [],
        "dimension_concentration_ms": [],
    }
    last_source: Mapping[str, Any] | None = None
    last_curatorial: Mapping[str, Any] | None = None
    last_loaded: Mapping[str, Any] | None = None
    last_missingness: Mapping[str, Any] | None = None
    last_curatorial_folder_counts: Mapping[str, Any] | None = None
    last_missingness_stage_counts: Mapping[str, Any] | None = None
    last_cross_counts: Mapping[str, Any] | None = None

    benchmark_started = time.perf_counter()
    for _ in range(iterations):
        gc.collect()
        last_source, elapsed = _timed(
            modules["source_inventory"].analyze,
            candidate_path=common.CANDIDATE_PATH,
            ledger_path=common.LEDGER_PATH,
        )
        timings["source_inventory_ms"].append(elapsed)

        gc.collect()
        last_curatorial, elapsed = _timed(
            modules["curatorial_analysis"].analyze,
            sqlite_path=common.SQLITE_PATH,
            ledger_path=common.LEDGER_PATH,
            candidate_summary=last_source,
        )
        timings["curatorial_index_and_co_membership_ms"].append(elapsed)
        timings["curatorial_co_membership_core_ms"].append(
            float(last_curatorial["performance"]["co_membership_core_ms"])
        )

        gc.collect()
        last_curatorial_folder_counts, elapsed = (
            _curatorial_folder_inverted_index_benchmark(
                modules["curatorial_analysis"],
                sqlite_path=common.SQLITE_PATH,
                ledger_path=common.LEDGER_PATH,
            )
        )
        timings["curatorial_folder_inverted_index_ms"].append(elapsed)

        gc.collect()
        last_loaded, elapsed = _timed(common.load_normalized_public_records)
        timings["normalized_public_record_load_ms"].append(elapsed)
        records = last_loaded["records"]

        gc.collect()
        last_missingness, elapsed = _timed(
            modules["missingness_analysis"].analyze,
            records,
            expected_count=generator.PUBLIC_OBJECT_COUNT,
            include_object_vectors=False,
        )
        timings["missingness_end_to_end_ms"].append(elapsed)

        gc.collect()
        last_missingness_stage_counts, missingness_timings = (
            _missingness_stage_benchmark(
                modules["missingness_analysis"], records
            )
        )
        for name, value in missingness_timings.items():
            timings[name].append(value)
        expected_missingness_hashes = {
            "objectVectorsSha256": last_missingness["hashes"]["objectVectorsSha256"],
            "fieldMatrixSha256": last_missingness["hashes"]["fieldMatrixSha256"],
            "cooccurrencesSha256": last_missingness["hashes"]["cooccurrencesSha256"],
        }
        for field, expected_hash in expected_missingness_hashes.items():
            if last_missingness_stage_counts[field] != expected_hash:
                raise BenchmarkError(
                    f"isolated missingness {field} differs from full analysis"
                )

        gc.collect()
        last_cross_counts, cross_timings = _cross_stage_benchmark(
            modules["cross_dimensional_analysis"], records
        )
        for name, value in cross_timings.items():
            timings[name].append(value)

    if any(value is None for value in (
        last_source,
        last_curatorial,
        last_loaded,
        last_missingness,
        last_curatorial_folder_counts,
        last_missingness_stage_counts,
        last_cross_counts,
    )):
        raise BenchmarkError("benchmark did not complete an iteration")
    assert last_source is not None
    assert last_curatorial is not None
    assert last_loaded is not None
    assert last_missingness is not None
    assert last_curatorial_folder_counts is not None
    assert last_missingness_stage_counts is not None

    records = last_loaded["records"]
    cross_result = modules["cross_dimensional_analysis"].analyze(
        records,
        expected_count=generator.PUBLIC_OBJECT_COUNT,
        extension_pairs=generator.CURATORIAL_EXTENSION_PAIRS,
        minimum_subset_support=generator.MINIMUM_SUBSET_SUPPORT,
        rare_max_count=generator.RARE_MAX_COUNT,
    )
    public_ids = set(last_loaded["publicObjectIds"])
    held_ids = set(last_loaded["heldObjectIds"])
    enrichment = generator.enrich_analysis(
        modules=modules,
        records=records,
        source=last_source,
        curatorial=last_curatorial,
        missingness=last_missingness,
        cross=cross_result,
        public_ids=public_ids,
        held_ids=held_ids,
    )
    cross_result = enrichment["cross"]
    registry_result = enrichment["registry"]
    pathological_result = generator._call_pathological(
        modules["pathological_samples"],
        records,
        public_ids,
        held_ids,
    )
    derived = {
        "source": last_source,
        "curatorial": last_curatorial,
        "missingness": last_missingness,
        "cross": cross_result,
        "registry": registry_result,
        "pathological": pathological_result,
        "curatorialSupport": enrichment["curatorialSupport"],
        "structureDistributions": enrichment["structureDistributions"],
        "receipts": last_loaded["receipts"],
        "publicObjectIds": public_ids,
        "heldObjectIds": held_ids,
    }
    output_started = time.perf_counter()
    research, raw, generation = generator.build_output_files(derived)
    generator.validate_output_safety(research, raw)
    output_projection_ms = (time.perf_counter() - output_started) * 1000
    file_metrics = _file_metrics(research, raw, generation)
    total_ms = (time.perf_counter() - benchmark_started) * 1000

    deterministic_payload = {
        "schemaVersion": SCHEMA_VERSION,
        "derivationVersion": DERIVATION_VERSION,
        "iterations": iterations,
        "inputReceipts": last_loaded["receipts"],
        "population": {
            "publicObjectCount": generator.PUBLIC_OBJECT_COUNT,
            "heldObjectsInStatistics": 0,
        },
        "workloadCounts": last_cross_counts,
        "stageWorkloadCounts": {
            "crossDimensional": last_cross_counts,
            "curatorialFolderInvertedIndex": last_curatorial_folder_counts,
            "missingness": last_missingness_stage_counts,
        },
        "outputFileMetrics": file_metrics,
        "outputRowCounts": generation["rowCounts"],
        "deterministicBundleSha256": generation["deterministicBundleSha256"],
        "measurementPolicy": {
            "quantile": "R7_LINEAR",
            "gzip": "gzip level 9 mtime 0",
            "timingsIncludedInDeterministicHash": False,
            "memoryMeasurementsIncludedInDeterministicHash": False,
            "rssMeasurement": (
                "resource.getrusage(RUSAGE_SELF).ru_maxrss process-lifetime "
                "high-water mark normalized to bytes after timed and memory passes"
            ),
            "pythonHeapMeasurement": (
                "dedicated one-iteration warm-process benchmark-body replay after "
                "the timed pass; peak bytes currently traced by tracemalloc, with "
                "pre-trace and native allocations excluded; memory replay excluded "
                "from stage and total timings"
            ),
            "explorationAnalysisPeakHeapBytes": (
                "alias of pythonTracemallocPeakBytes from the dedicated replay; "
                "Python-traced allocation peak, not process RSS"
            ),
            "stageIsolation": {
                "curatorialFolderInvertedIndex": (
                    "ordered object_folder_refs scan plus object adjacency, "
                    "public folder bitsets, and pair digest; excludes ledger "
                    "load, public ordinal construction, and immutable connection "
                    "validation"
                ),
                "missingnessNormalization": (
                    "record validation/normalization and public-ID ordering"
                ),
                "missingnessObjectVectorBuild": (
                    "per-object diagnostic vector and active-state derivation; "
                    "excludes normalization, aggregate census, and hashing"
                ),
                "missingnessAggregateCensus": (
                    "state counters, co-occurrence cells, and field matrix "
                    "derived from vectors; excludes vector construction and hashing"
                ),
                "dimensionConcentration": (
                    "four native public-only dimension concentration rows over "
                    "source, decade, geography, and curated-container assignments"
                ),
            },
            "fullObjectPairMatrixMaterialized": False,
            "normalizedRowsEmitted": False,
        },
    }
    deterministic_sha = hashlib.sha256(
        generator.canonical_json_bytes(deterministic_payload)
    ).hexdigest()
    return {
        **deterministic_payload,
        "deterministicPayloadSha256": deterministic_sha,
        "performance": {
            "stageDistributions": {
                name: _distribution(values) for name, values in sorted(timings.items())
            },
            "outputProjectionMs": round(output_projection_ms, 3),
            "totalBenchmarkMs": round(total_ms, 3),
            "peakRssBytes": _peak_rss_bytes(),
        },
    }


def benchmark(iterations: int = 3) -> dict[str, Any]:
    if isinstance(iterations, bool) or not isinstance(iterations, int) or not 1 <= iterations <= 20:
        raise BenchmarkError("iterations must be an integer from 1 through 20")
    result = _benchmark_body(iterations)
    owned_trace = not tracemalloc.is_tracing()
    if owned_trace:
        tracemalloc.start(1)
    tracemalloc.reset_peak()
    try:
        memory_probe = _benchmark_body(1)
        del memory_probe
        gc.collect()
        current_bytes, peak_bytes = tracemalloc.get_traced_memory()
        result["performance"].update({
            "memoryProbeIterations": 1,
            "pythonTracemallocCurrentBytes": current_bytes,
            "pythonTracemallocPeakBytes": peak_bytes,
            "explorationAnalysisPeakHeapBytes": peak_bytes,
            "tracemallocTracebackLimit": tracemalloc.get_traceback_limit(),
            "peakRssBytes": _peak_rss_bytes(),
        })
        return result
    finally:
        if owned_trace:
            tracemalloc.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = benchmark(args.iterations)
    payload = generator.canonical_json_bytes(result, pretty=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(payload)
    print(json.dumps({
        "status": "PASS",
        "iterations": result["iterations"],
        "deterministicPayloadSha256": result["deterministicPayloadSha256"],
        "peakRssBytes": result["performance"]["peakRssBytes"],
        "pythonTracemallocPeakBytes": result["performance"]["pythonTracemallocPeakBytes"],
        "explorationAnalysisPeakHeapBytes": result["performance"]["explorationAnalysisPeakHeapBytes"],
        "rowCounts": result["outputRowCounts"],
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
