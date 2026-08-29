#!/usr/bin/env python3
"""Aggregate measured production workloads, runtime probes, and build costs."""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import datetime as dt
import json
import math
from pathlib import Path
import statistics
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "docs/audits/v49-exploration-full-space-closure-round1/raw"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def percentile(values: Iterable[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, max(0, math.ceil(len(ordered) * probability) - 1))
    return float(ordered[index])


def directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file()) if path.exists() else 0


def parse_utc(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(dt.timezone.utc)


def aggregate_probe_samples(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate all instrumented Node processes into one server sample per UTC second."""
    buckets: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        stamp = parse_utc(str(row["timestamp_utc"])).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        pid = int(row["pid"])
        prior = buckets[stamp].get(pid)
        if prior is None or int(row["probe_sequence"]) > int(prior["probe_sequence"]):
            buckets[stamp][pid] = row
    result: list[dict[str, Any]] = []
    for stamp, samples_by_pid in sorted(buckets.items()):
        samples = list(samples_by_pid.values())
        result.append({
            "timestamp_utc": stamp,
            "process_sample_count": len(samples),
            "cpu_percent_interval": sum(float(row["cpu_percent_interval"]) for row in samples),
            "rss_bytes": sum(int(row["rss_bytes"]) for row in samples),
            "heap_used_bytes": sum(int(row["heap_used_bytes"]) for row in samples),
            "heap_total_bytes": sum(int(row["heap_total_bytes"]) for row in samples),
            "event_loop_delay_mean_ms": max(float(row["event_loop_delay_mean_ms"]) for row in samples),
            "event_loop_delay_p95_ms": max(float(row["event_loop_delay_p95_ms"]) for row in samples),
            "event_loop_delay_p99_ms": max(float(row["event_loop_delay_p99_ms"]) for row in samples),
            "event_loop_delay_max_ms": max(float(row["event_loop_delay_max_ms"]) for row in samples),
        })
    return result


def resource_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("NO_RUNTIME_SAMPLES_FOR_WORKLOAD")
    return {
        "sample_count": len(rows),
        "server_cpu_percent_peak": max(float(row["cpu_percent_interval"]) for row in rows),
        "server_cpu_percent_mean": statistics.fmean(float(row["cpu_percent_interval"]) for row in rows),
        "server_rss_bytes_peak": max(int(row["rss_bytes"]) for row in rows),
        "server_heap_used_bytes_peak": max(int(row["heap_used_bytes"]) for row in rows),
        "server_heap_total_bytes_peak": max(int(row["heap_total_bytes"]) for row in rows),
        "server_event_loop_delay_ms_peak": max(float(row["event_loop_delay_max_ms"]) for row in rows),
        "server_event_loop_delay_p95_ms_peak": max(float(row["event_loop_delay_p95_ms"]) for row in rows),
    }


def linear_slope_bytes_per_second(rows: list[dict[str, Any]]) -> float:
    if len(rows) < 2:
        return 0.0
    origin = parse_utc(str(rows[0]["timestamp_utc"]))
    xs = [(parse_utc(str(row["timestamp_utc"])) - origin).total_seconds() for row in rows]
    ys = [float(row["rss_bytes"]) for row in rows]
    x_mean = statistics.fmean(xs)
    y_mean = statistics.fmean(ys)
    denominator = sum((value - x_mean) ** 2 for value in xs)
    return 0.0 if denominator == 0 else sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator


def stream_export_http_counts(path: Path) -> tuple[int, int, int]:
    request_count = success_count = failure_count = 0
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            requests = int(row.get("http_request_count", "0"))
            statuses = row.get("http_status", "").split(";")
            if requests != len(statuses):
                raise ValueError(f"EXPORT_HTTP_REQUEST_COUNT_MISMATCH:{row.get('export_variant_id')}")
            request_count += requests
            row_successes = sum(status == "200" for status in statuses)
            success_count += row_successes
            failure_count += requests - row_successes
            if row.get("error_code"):
                raise ValueError(f"EXPORT_VALIDATION_FAILURE:{row.get('export_variant_id')}")
    return request_count, success_count, failure_count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--workload-dir", type=Path)
    parser.add_argument("--startup", type=Path)
    parser.add_argument("--probe", type=Path)
    parser.add_argument("--model-load", type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    raw = repo / "docs/audits/v49-exploration-full-space-closure-round1/raw"
    workload_dir = (args.workload_dir or (raw / "workloads-v2")).resolve()
    startup_path = (args.startup or (raw / "production-server-startup-v2.json")).resolve()
    probe_path = (args.probe or (raw / "runtime-probe-v2.jsonl")).resolve()
    model_load_path = (args.model_load or (raw / "production-model-load-v2.json")).resolve()
    workloads = [read_json(path) for path in sorted(workload_dir.glob("*.json"))]
    if not workloads:
        raise ValueError("NO_PRODUCTION_WORKLOADS")
    startup = read_json(startup_path)
    if startup.get("status") != "READY" or not startup.get("probe_session_id"):
        raise ValueError("PRODUCTION_STARTUP_RECEIPT_INVALID")
    all_probes = jsonl(probe_path)
    probes = [row for row in all_probes if row.get("probe_session_id") == startup["probe_session_id"]]
    if not probes:
        raise ValueError("NO_RUNTIME_PROBE_SAMPLES")
    probe_sequences: dict[int, list[int]] = defaultdict(list)
    for row in probes:
        probe_sequences[int(row["pid"])].append(int(row["probe_sequence"]))
    for pid, sequences in probe_sequences.items():
        ordered = sorted(sequences)
        if len(ordered) != len(set(ordered)) or ordered != list(range(1, max(ordered) + 1)):
            raise ValueError(f"RUNTIME_PROBE_SEQUENCE_GAP:{pid}")
    aggregate_probes = aggregate_probe_samples(probes)
    model_load = read_json(model_load_path)
    if model_load.get("status") != "PASS" or model_load.get("audit_to_production_equivalence_mismatch_count") != 0:
        raise ValueError("PRODUCTION_MODEL_LOAD_VALIDATION_FAILED")
    functional = read_json(raw / "api-functional-validation-v2.json")
    if functional["status"] != "PASS":
        raise ValueError("API_FUNCTIONAL_VALIDATION_FAILED")

    workload_ids: set[str] = set()
    workload_summaries: list[dict[str, Any]] = []
    by_mode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for workload in workloads:
        if workload.get("schema_version") != "trace-exploration-http-workload-v2":
            raise ValueError("WORKLOAD_SCHEMA_VERSION_INVALID")
        workload_id = str(workload.get("workload_id", ""))
        if not workload_id or workload_id in workload_ids:
            raise ValueError(f"WORKLOAD_ID_INVALID_OR_DUPLICATE:{workload_id}")
        workload_ids.add(workload_id)
        rows = workload.get("observations")
        if not isinstance(rows, list) or not rows or int(workload.get("request_count", -1)) != len(rows):
            raise ValueError(f"WORKLOAD_OBSERVATION_COVERAGE:{workload_id}")
        successes = sum(bool(row.get("success")) for row in rows)
        failures = len(rows) - successes
        timeouts = sum(bool(row.get("timeout")) for row in rows)
        if (successes != int(workload.get("success_count", -1))
                or failures != int(workload.get("failure_count", -1))
                or timeouts != int(workload.get("timeout_count", -1))):
            raise ValueError(f"WORKLOAD_COUNT_RECONCILIATION:{workload_id}")
        criterion = workload.get("termination_criterion", {})
        if (len(rows) < int(criterion.get("minimum_request_count", -1))
                or float(workload.get("duration_ms", -1)) < float(criterion.get("minimum_duration_ms", -1))):
            raise ValueError(f"WORKLOAD_TERMINATION_CRITERION_NOT_MET:{workload_id}")
        if workload.get("status") != "PASS" or failures or timeouts or int(workload.get("unexpected_5xx_count", -1)):
            raise ValueError(f"WORKLOAD_FAILURE:{workload_id}")
        for field in ("response_validation_failure_count", "state_corruption_count", "semantic_hash_mismatch_count", "png_corruption_count"):
            if int(workload.get(field, -1)) != 0:
                raise ValueError(f"WORKLOAD_INTEGRITY_FAILURE:{workload_id}:{field}")
        start = parse_utc(str(workload["started_utc"])) - dt.timedelta(seconds=1.1)
        end = parse_utc(str(workload["ended_utc"])) + dt.timedelta(seconds=1.1)
        interval_probes = [row for row in aggregate_probes if start <= parse_utc(str(row["timestamp_utc"])) <= end]
        summary = {key: value for key, value in workload.items() if key != "observations"}
        summary["server_runtime"] = resource_summary(interval_probes)
        workload_summaries.append(summary)
        by_mode[workload["mode"]].append(workload)

    def observations(mode: str) -> list[dict[str, Any]]:
        return [item for workload in by_mode.get(mode, []) for item in workload["observations"]]

    json_observations = observations("json")
    png_observations = observations("png")
    mixed_observations = observations("mixed")
    all_observations = [item for workload in workloads for item in workload["observations"]]

    def latency_summary(rows: list[dict[str, Any]], mode: str) -> dict[str, Any]:
        latencies = [float(row["elapsed_ms"]) for row in rows]
        duration_ms = sum(float(workload["duration_ms"]) for workload in by_mode.get(mode, []))
        sizes = [int(row["response_bytes"]) for row in rows]
        return {
            "request_count": len(rows),
            "success_count": sum(bool(row["success"]) for row in rows),
            "failure_count": sum(not bool(row["success"]) for row in rows),
            "timeout_count": sum(bool(row["timeout"]) for row in rows),
            "p50_ms": percentile(latencies, 0.50),
            "p95_ms": percentile(latencies, 0.95),
            "p99_ms": percentile(latencies, 0.99),
            "maximum_ms": max(latencies, default=0.0),
            "requests_per_second": len(rows) / (duration_ms / 1000) if duration_ms > 0 else 0.0,
            "response_bytes": sum(sizes),
            "response_bytes_mean": statistics.fmean(sizes) if sizes else 0.0,
            "response_bytes_minimum": min(sizes, default=0),
            "response_bytes_maximum": max(sizes, default=0),
            "client_side_error_count": sum(bool(row.get("error")) for row in rows),
            "server_side_error_count": sum(int(row.get("status", 0)) >= 500 for row in rows),
            "response_validation_failure_count": sum(not bool(row.get("response_valid")) for row in rows),
        }

    functional_ledger = raw / "api-functional-http-case-ledger-v2.tsv"
    functional_family_data: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "latencies": [], "response_bytes": 0, "case_count": 0, "pass_count": 0, "failure_count": 0,
    })
    functional_ledger_count = 0
    with functional_ledger.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            functional_ledger_count += 1
            family = functional_family_data[str(row["case_family"])]
            passed = row["pass"].lower() == "true"
            family["latencies"].append(float(row["elapsed_ms"]))
            family["response_bytes"] += int(row["response_bytes"])
            family["case_count"] += 1
            family["pass_count"] += int(passed)
            family["failure_count"] += int(not passed)
    if functional_ledger_count != int(functional["case_count"]):
        raise ValueError("FUNCTIONAL_HTTP_LEDGER_COVERAGE_MISMATCH")
    response_families = {}
    for family_name, values in sorted(functional_family_data.items()):
        latencies = values.pop("latencies")
        response_families[family_name] = {
            **values,
            "p50_ms": percentile(latencies, 0.50),
            "p95_ms": percentile(latencies, 0.95),
            "p99_ms": percentile(latencies, 0.99),
            "maximum_ms": max(latencies, default=0.0),
        }

    export_request_count, export_success_count, export_failure_count = stream_export_http_counts(raw / "png-validation-v2.tsv")
    workload_success_count = sum(bool(item["success"]) for item in all_observations)
    workload_failure_count = len(all_observations) - workload_success_count
    production_http = {
        "schema_version": "trace-exploration-production-http-results-v2",
        "status": "PASS" if not workload_failure_count and not functional["fail_count"] and not export_failure_count else "FAIL",
        "actual_production_http_tested": True,
        "cold_start_ms": startup["cold_start_ms"],
        "first_request_ms": startup["first_successful_request_ms"],
        "first_request_including_model_import_ms": startup["first_request_including_model_import_ms"],
        "production_model_load_ms": model_load["production_model_load_ms"],
        "production_model_rss_delta_bytes": model_load["rss_delta_bytes"],
        "production_model_heap_delta_bytes": model_load["heap_delta_bytes"],
        "json_api": latency_summary(json_observations, "json"),
        "png_api": latency_summary(png_observations, "png"),
        "mixed_api": latency_summary(mixed_observations, "mixed"),
        "response_families": response_families,
        "exhaustive_export_http": {
            "request_count": export_request_count,
            "success_count": export_success_count,
            "failure_count": export_failure_count,
        },
        "total_http_request_count": len(all_observations) + functional["case_count"] + export_request_count,
        "http_success_count": workload_success_count + functional["pass_count"] + export_success_count,
        "http_failure_count": workload_failure_count + functional["fail_count"] + export_failure_count,
        "http_timeout_count": sum(bool(item["timeout"]) for item in all_observations),
        "unexpected_5xx_count": sum(int(item["status"]) >= 500 for item in all_observations) + functional["unexpected_5xx_count"],
        "state_corruption_count": sum(int(workload["state_corruption_count"]) for workload in workloads),
        "semantic_hash_mismatch_count": sum(int(workload["semantic_hash_mismatch_count"]) for workload in workloads),
        "png_corruption_count": sum(int(workload["png_corruption_count"]) for workload in workloads),
        "functional_case_count": functional["case_count"],
    }
    write_json(raw / "production-http-results.json", production_http)
    if (production_http["status"] != "PASS" or production_http["unexpected_5xx_count"]
            or production_http["http_timeout_count"] or production_http["state_corruption_count"]
            or production_http["semantic_hash_mismatch_count"] or production_http["png_corruption_count"]):
        raise ValueError("PRODUCTION_HTTP_FAILURE")

    required_json = {1, 5, 10, 25, 50}
    required_png = {1, 2, 5, 10}
    observed_json = {int(item["concurrency"]) for item in workloads if item["mode"] == "json"}
    observed_png = {int(item["concurrency"]) for item in workloads if item["mode"] == "png"}
    if not required_json <= observed_json or not required_png <= observed_png:
        raise ValueError(f"CONCURRENCY_COVERAGE:json={observed_json}:png={observed_png}")
    scenarios = {str(item.get("scenario")) for item in workloads}
    required_scenarios = {"warm_steady_state", "burst_load", "sustained_mixed_load", "concurrent_png_load"}
    if not required_scenarios <= scenarios:
        raise ValueError(f"LOAD_SCENARIO_COVERAGE:{sorted(scenarios)}")
    concurrency = {
        "schema_version": "trace-exploration-concurrency-results-v2",
        "status": "PASS",
        "concurrency_test_completed": True,
        "concurrent_png_test_completed": True,
        "json_concurrency_levels": sorted(observed_json),
        "png_concurrency_levels": sorted(observed_png),
        "scenarios": sorted(scenarios),
        "workloads": workload_summaries,
        "failure_count": sum(int(item["failure_count"]) for item in workloads),
        "timeout_count": sum(int(item["timeout_count"]) for item in workloads),
        "unexpected_5xx_count": sum(int(item["unexpected_5xx_count"]) for item in workloads),
    }
    write_json(raw / "concurrency-results.json", concurrency)
    if concurrency["failure_count"] or concurrency["timeout_count"] or concurrency["unexpected_5xx_count"]:
        raise ValueError("CONCURRENCY_FAILURE")

    sustained_candidates = [item for item in workloads if item["mode"] == "mixed" and int(item["termination_criterion"]["minimum_duration_ms"]) >= 300_000 and int(item["termination_criterion"]["minimum_request_count"]) >= 10_000]
    if not sustained_candidates:
        raise ValueError("SUSTAINED_LOAD_MISSING")
    sustained = max(sustained_candidates, key=lambda item: str(item["ended_utc"]))
    sustained_start = parse_utc(str(sustained["started_utc"]))
    sustained_end = parse_utc(str(sustained["ended_utc"]))
    sustained_probes = [row for row in aggregate_probes if sustained_start <= parse_utc(str(row["timestamp_utc"])) <= sustained_end]
    expected_sustained_samples = max(60, math.floor((sustained_end - sustained_start).total_seconds()))
    minimum_sustained_samples = math.floor(expected_sustained_samples * 0.80)
    if len(sustained_probes) < minimum_sustained_samples:
        raise ValueError(f"SUSTAINED_RUNTIME_SAMPLE_COVERAGE:{len(sustained_probes)}")
    window_size = max(10, len(sustained_probes) // 5)
    first_window_rss = statistics.median(int(row["rss_bytes"]) for row in sustained_probes[:window_size])
    last_window_rss = statistics.median(int(row["rss_bytes"]) for row in sustained_probes[-window_size:])
    sustained_rss_growth = int(last_window_rss - first_window_rss)
    material_growth_threshold = max(16 * 1024 * 1024, int(first_window_rss * 0.10))
    rss_slope = linear_slope_bytes_per_second(sustained_probes)
    unbounded_growth = sustained_rss_growth > material_growth_threshold and rss_slope > 0
    stability = {
        "criterion_version": "trace-runtime-memory-stability-v2",
        "criterion": "Compare the first and final 20% windows; flag growth only when the final median exceeds the initial median with a positive OLS trend and by more than max(16 MiB, 10% of the initial median).",
        "sustained_sample_count": len(sustained_probes),
        "minimum_required_sample_count": minimum_sustained_samples,
        "window_sample_count": window_size,
        "first_window_median_rss_bytes": int(first_window_rss),
        "last_window_median_rss_bytes": int(last_window_rss),
        "rss_growth_bytes": sustained_rss_growth,
        "material_growth_threshold_bytes": material_growth_threshold,
        "rss_linear_slope_bytes_per_second": rss_slope,
        "unbounded_memory_growth_detected": unbounded_growth,
    }
    runtime = {
        "schema_version": "trace-exploration-runtime-memory-results-v2",
        "status": "FAIL" if unbounded_growth else "PASS",
        "probe_session_id": startup["probe_session_id"],
        "raw_sample_count": len(probes),
        "aggregate_sample_count": len(aggregate_probes),
        "process_ids": sorted({int(row["pid"]) for row in probes}),
        "peak_rss_bytes": max(int(row["rss_bytes"]) for row in aggregate_probes),
        "peak_heap_used_bytes": max(int(row["heap_used_bytes"]) for row in aggregate_probes),
        "peak_heap_total_bytes": max(int(row["heap_total_bytes"]) for row in aggregate_probes),
        "peak_cpu_percent": max(float(row["cpu_percent_interval"]) for row in aggregate_probes),
        "peak_event_loop_delay_ms": max(float(row["event_loop_delay_max_ms"]) for row in aggregate_probes),
        "p95_event_loop_delay_ms": percentile([float(row["event_loop_delay_p95_ms"]) for row in aggregate_probes], 0.95),
        "first_rss_bytes": int(aggregate_probes[0]["rss_bytes"]),
        "last_rss_bytes": int(aggregate_probes[-1]["rss_bytes"]),
        "rss_growth_bytes": sustained_rss_growth,
        "unbounded_memory_growth_detected": unbounded_growth,
        "memory_stability": stability,
        "production_model_load": model_load,
        "aggregate_samples": aggregate_probes,
        "raw_samples": probes,
    }
    write_json(raw / "runtime-memory-results.json", runtime)
    if runtime["status"] != "PASS":
        raise ValueError("UNBOUNDED_MEMORY_GROWTH_DETECTED")

    sustained_output = {
        "schema_version": "trace-exploration-sustained-load-results-v2",
        "status": "PASS" if not sustained["failure_count"] and not sustained["timeout_count"] and not sustained["unexpected_5xx_count"] and not unbounded_growth else "FAIL",
        "sustained_load_test_completed": True,
        **{key: value for key, value in sustained.items() if key != "observations"},
        "server_runtime": resource_summary(sustained_probes),
        "runtime_stability": stability,
    }
    write_json(raw / "sustained-load-results.json", sustained_output)
    if sustained_output["status"] != "PASS":
        raise ValueError("SUSTAINED_LOAD_FAILURE")

    events = jsonl(raw / "execution-events.jsonl")
    finished = [row for row in events if row["status"] in {"PASS", "FAIL"}]
    passed_events = [row for row in finished if row["status"] == "PASS"]

    def latest_pass_duration(operation_ids: set[str]) -> int:
        matches = [row for row in passed_events if row["operation_id"] in operation_ids]
        if not matches:
            raise ValueError(f"BUILD_TIMING_EVENT_MISSING:{sorted(operation_ids)}")
        return int(max(matches, key=lambda row: int(row["sequence"]))["duration_ms"])

    space_performance = read_json(raw / "space-generation-performance-v2.json")
    if (space_performance.get("schema_version") != "trace-exploration-space-generation-performance-v2"
            or space_performance.get("timing_values_are_nondeterministic") is not True):
        raise ValueError("SPACE_BUILD_PERFORMANCE_RECEIPT_INVALID")
    search_duration = sum(int(row["duration_ms"]) for row in finished if row["operation_id"].startswith("association-search-batch"))
    export_validation_duration = sum(
        int(row["duration_ms"])
        for row in finished
        if row["operation_id"].startswith(("png-export-part", "export-validation-part"))
    )
    if search_duration <= 0:
        raise ValueError("EXTERNAL_EVIDENCE_TIMING_MISSING")
    if export_validation_duration <= 0:
        raise ValueError("EXPORT_VALIDATION_TIMING_MISSING")
    required_space_timings = (
        "composition_enumeration_duration_ms", "canonicalisation_duration_ms", "state_generation_duration_ms",
        "transition_generation_duration_ms", "workflow_generation_duration_ms", "enumeration_peak_rss_bytes",
        "temporary_storage_bytes",
    )
    missing_space_timings = [field for field in required_space_timings if field not in space_performance]
    if missing_space_timings:
        raise ValueError(f"SPACE_BUILD_TIMING_MISSING:{missing_space_timings}")
    production_model = repo / "frontend/generated/trace-exploration-v2/production-read-model.json"
    build_time = {
        "schema_version": "trace-exploration-build-time-computation-results-v2",
        "status": "PASS",
        "vocabulary_census_duration_ms": latest_pass_duration({"vocabulary-eligibility-census"}),
        "pair_census_duration_ms": latest_pass_duration({"pair-universe-enumeration"}),
        "external_evidence_processing_duration_ms": search_duration,
        "graph_build_duration_ms": latest_pass_duration({"association-census-proof1", "association-census-pass1"}),
        "composition_enumeration_duration_ms": space_performance["composition_enumeration_duration_ms"],
        "canonicalisation_duration_ms": space_performance["canonicalisation_duration_ms"],
        "state_generation_duration_ms": space_performance["state_generation_duration_ms"],
        "transition_generation_duration_ms": space_performance["transition_generation_duration_ms"],
        "workflow_generation_duration_ms": space_performance["workflow_generation_duration_ms"],
        "export_validation_duration_ms": export_validation_duration,
        "export_census_generation_duration_ms": space_performance.get("export_census_generation_duration_ms", 0),
        "artifact_serialization_duration_ms": space_performance.get("artifact_serialization_duration_ms", 0),
        "enumeration_peak_rss_bytes": space_performance["enumeration_peak_rss_bytes"],
        "enumeration_temp_storage_bytes": space_performance["temporary_storage_bytes"],
        "external_evidence_cache_bytes": directory_bytes(raw / "association-query-cache-v2"),
        "final_audit_storage_bytes": directory_bytes(raw),
        "full_audit_census_bytes": directory_bytes(raw),
        "production_read_model_bytes": production_model.stat().st_size,
        "production_model_load_ms": model_load["production_model_load_ms"],
        "production_model_rss_delta_bytes": model_load["rss_delta_bytes"],
        "production_model_heap_delta_bytes": model_load["heap_delta_bytes"],
    }
    write_json(raw / "build-time-computation-results.json", build_time)
    print(json.dumps({
        "status": "PASS",
        "workload_count": len(workloads),
        "total_http_request_count": production_http["total_http_request_count"],
        "peak_rss_bytes": runtime["peak_rss_bytes"],
        "sustained_request_count": sustained["request_count"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
