#!/usr/bin/env python3
"""Consolidate the final Round 16A gate receipts without rerunning any gate.

This program is deliberately a report-layer aggregator.  It reads independent
receipts produced by the repository-boundary, regression, runtime, execution-
log, reproduction, and final gate-command validators; rejects missing or
conflicting values; and writes one provenance-bearing evidence document for
``build_research_reports.py``.

Input contracts
---------------

``repository-boundary-receipt.json`` is produced by
``verify_repository_boundary.py`` and must contain a scalar ``receipt`` map.

``regression-results.json`` must contain a terminal ``status`` and a scalar
``receipt`` map containing ``ROUND8_REGRESSION`` through
``ROUND16_REGRESSION``.

``gate-status-results.json`` must contain a terminal ``status`` and a scalar
``receipt`` map containing the authority, database-freeze, repository,
typecheck, production-build, API-schema, audit-seal, product-boundary, and
continuous-log gates listed in ``REQUIRED_DECLARED_METRICS`` below.  This is a
summary of already logged commands, not permission to infer a pass from the
mere presence of a build artifact.

The remaining inputs use the schemas emitted by the Round 16A validators and
runtime summarizer.  Scalar keys under an explicit ``receipt`` or ``metrics``
map are accepted verbatim after upper-snake normalization.  Known runtime and
execution-log fields are mapped explicitly.  If two sources provide unequal
values for the same metric, aggregation fails closed.

Git integration fields are intentionally not accepted here: a committed
pre-integration research report cannot contain its own final commit SHA.  The
renderer accepts a separate final integration receipt when emitting the final
machine-readable response after the branch is committed, pushed, and (only on
full pass) fast-forwarded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping


REPO = Path(__file__).resolve().parents[2]
RAW_RELATIVE = Path("docs/audits/v49-exploration-full-space-closure-round1/raw")
SCHEMA_VERSION = "trace-round16a-final-gate-evidence/v1"

DEFAULT_INPUTS = {
    "repository_boundary": "repository-boundary-receipt.json",
    "execution_log": "execution-log-verification.json",
    "regression": "regression-results.json",
    "gate_status": "gate-status-results.json",
    "audit_seal": "audit-seal-result.json",
    "api_functional": "api-functional-validation-v2.json",
    "production_http": "production-http-results.json",
    "concurrency": "concurrency-results.json",
    "runtime_memory": "runtime-memory-results.json",
    "build_time": "build-time-computation-results.json",
    "sustained_load": "sustained-load-results.json",
    "independent": "independent-verification.json",
    "reproduction": "reproducibility-verification.json",
}

REQUIRED_DECLARED_METRICS = {
    "ACTIVE_EXPLORATION_AUTHORITY_COUNT",
    "AUTHORITY_CONTRADICTION_COUNT",
    "AUTHORITY_RECONCILIATION_READY",
    "CONTEXT_OVERRIDE_OF_ASSOCIATION_DECISION_COUNT",
    "SPACETIME_OVERRIDE_OF_ASSOCIATION_DECISION_COUNT",
    "CONTINUOUS_PROCESS_LOG_READY",
    "DATABASE_FREEZE",
    "REPOSITORY_HYGIENE",
    "TYPECHECK",
    "PRODUCTION_BUILD",
    "API_SCHEMA_VALIDATION",
    "FINAL_EXPLORATION_FRONTEND_IMPLEMENTED",
    "PUBLIC_EXPLORATION_PAGE_ADDED",
    "PROJECT_FRONTEND_DESIGN_SAFE_TO_BEGIN",
    "DEPLOYED",
    "EXTERNAL_HUMAN_DOMAIN_REVIEW_COMPLETED",
    "FORCE_PUSH_USED",
    "MERGE_COMMIT_CREATED",
    "HISTORY_REWRITTEN",
}

REQUIRED_BOUNDARY_METRICS = {
    "SEARCH_STATUS",
    "SEARCH_CODE_MUTATION_COUNT",
    "SEARCH_SCHEMA_MUTATION_COUNT",
    "SEARCH_API_MUTATION_COUNT",
    "SEARCH_INDEX_MUTATION_COUNT",
    "SEARCH_MUTATION_COUNT",
    "SEARCH_RUNTIME_DEPENDENCY_COUNT",
    "SEARCH_SEMANTIC_INPUT_COUNT",
    "CONTEXT_CODE_MUTATION_COUNT",
    "CONTEXT_MUTATION_COUNT",
    "CONTEXT_SEMANTIC_INPUT_COUNT",
    "SPACETIME_CODE_MUTATION_COUNT",
    "SPACETIME_MUTATION_COUNT",
    "SPACETIME_SEMANTIC_INPUT_COUNT",
    "PUBLIC_EXPLORATION_ARCHIVE_OBJECT_ID_COUNT",
    "PUBLIC_EXPLORATION_ARCHIVE_OBJECT_TITLE_COUNT",
    "PUBLIC_EXPLORATION_RECORD_LINK_COUNT",
    "PUBLIC_EXPLORATION_CONTEXT_REFERENCE_COUNT",
    "PUBLIC_EXPLORATION_SPACETIME_REFERENCE_COUNT",
}

REQUIRED_REGRESSION_METRICS = {f"ROUND{number}_REGRESSION" for number in range(8, 17)}

REQUIRED_AGGREGATED_METRICS = (
    REQUIRED_DECLARED_METRICS
    | REQUIRED_BOUNDARY_METRICS
    | REQUIRED_REGRESSION_METRICS
    | {
        "EXECUTION_EVENT_COUNT",
        "EXECUTION_LOG_SEQUENCE_GAP_COUNT",
        "EXECUTION_EVENT_HASH_FAILURE_COUNT",
        "COMMAND_LOG_COUNT",
        "CHECKPOINT_COMMIT_COUNT",
        "FULL_COMMAND_LOG_READY",
        "ACTUAL_PRODUCTION_HTTP_TESTED",
        "API_FAILURE_COUNT",
        "STALE_STATE_ACCEPTED_COUNT",
        "INVALID_TARGET_ACCEPTED_COUNT",
        "PUBLIC_EXPLORATION_ARCHIVE_OBJECT_ID_COUNT",
        "PUBLIC_EXPLORATION_ARCHIVE_OBJECT_TITLE_COUNT",
        "PUBLIC_EXPLORATION_RECORD_LINK_COUNT",
        "PUBLIC_EXPLORATION_CONTEXT_REFERENCE_COUNT",
        "PUBLIC_EXPLORATION_SPACETIME_REFERENCE_COUNT",
        "HELD_DATA_LEAK_COUNT",
        "CONCURRENCY_TEST_COMPLETED",
        "CONCURRENT_PNG_TEST_COMPLETED",
        "SUSTAINED_LOAD_TEST_COMPLETED",
        "COLD_START_MS",
        "FIRST_REQUEST_MS",
        "JSON_API_P50_MS",
        "JSON_API_P95_MS",
        "JSON_API_P99_MS",
        "JSON_API_MAX_MS",
        "PNG_P50_MS",
        "PNG_P95_MS",
        "PNG_P99_MS",
        "PNG_MAX_MS",
        "PEAK_RSS_BYTES",
        "PEAK_HEAP_USED_BYTES",
        "PEAK_CPU_PERCENT",
        "PEAK_EVENT_LOOP_DELAY_MS",
        "TOTAL_HTTP_REQUEST_COUNT",
        "HTTP_SUCCESS_COUNT",
        "HTTP_FAILURE_COUNT",
        "HTTP_TIMEOUT_COUNT",
        "UNEXPECTED_5XX_COUNT",
        "STATE_CORRUPTION_COUNT",
        "SEMANTIC_HASH_MISMATCH_COUNT",
        "PNG_CORRUPTION_COUNT",
        "UNBOUNDED_MEMORY_GROWTH_COUNT",
        "FULL_AUDIT_CENSUS_BYTES",
        "PRODUCTION_MODEL_LOAD_MS",
        "PRODUCTION_MODEL_RSS_DELTA_BYTES",
        "PRODUCTION_MODEL_HEAP_DELTA_BYTES",
        "VOCABULARY_CENSUS_DURATION_MS",
        "PAIR_CENSUS_DURATION_MS",
        "GRAPH_BUILD_DURATION_MS",
        "COMPOSITION_ENUMERATION_DURATION_MS",
        "STATE_GENERATION_DURATION_MS",
        "TRANSITION_GENERATION_DURATION_MS",
        "WORKFLOW_GENERATION_DURATION_MS",
        "EXPORT_VALIDATION_DURATION_MS",
        "ENUMERATION_PEAK_RSS_BYTES",
        "ENUMERATION_TEMP_STORAGE_BYTES",
        "INDEPENDENT_COUNT_MISMATCH_COUNT",
        "INDEPENDENT_HASH_MISMATCH_COUNT",
        "AUDIT_SEAL",
        "REPRODUCIBILITY_VERIFICATION",
        "VOCABULARY_CENSUS_HASH_MATCH",
        "PAIR_CENSUS_HASH_MATCH",
        "GRAPH_HASH_MATCH",
        "COMPOSITION_REGISTRY_HASH_MATCH",
        "STATE_CENSUS_HASH_MATCH",
        "TRANSITION_CENSUS_HASH_MATCH",
        "WORKFLOW_CENSUS_HASH_MATCH",
        "EXPORT_CENSUS_HASH_MATCH",
        "FINAL_GATE_SOURCE_FAILURE_COUNT",
        "FINAL_GATE_CRITERION_FAILURE_COUNT",
    }
)

GENERIC_KEYS = {
    "STATUS", "FORMAT", "SCHEMA_VERSION", "VERSION", "SOURCE_SHA",
    "DATABASE_SNAPSHOT", "DATABASE_SNAPSHOT_ID",
}


def normalize(name: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_")


def scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class Collector:
    def __init__(self) -> None:
        self.values: dict[str, Any] = {}
        self.sources: dict[str, list[str]] = {}
        self.conflicts: list[dict[str, Any]] = []

    def add(self, name: str, value: Any, source: str) -> None:
        key = normalize(name)
        if value is None or not key or key in GENERIC_KEYS or not scalar(value):
            return
        if key in self.values and canonical(self.values[key]) != canonical(value):
            self.conflicts.append({
                "metric": key,
                "existing_value": self.values[key],
                "existing_sources": self.sources[key],
                "conflicting_value": value,
                "conflicting_source": source,
            })
            return
        self.values.setdefault(key, value)
        self.sources.setdefault(key, []).append(source)

    def explicit_map(self, value: Any, source: str) -> None:
        if not isinstance(value, Mapping):
            return
        for key, child in value.items():
            if scalar(child):
                self.add(str(key), child, source)


def required_status(document: Mapping[str, Any], label: str) -> str:
    status_value = document.get("status", document.get("format_status", ""))
    if label == "repository_boundary" and not status_value:
        status_value = nested(document, "receipt", "REPOSITORY_BOUNDARY", default="")
    status = str(status_value).upper()
    if status not in {"PASS", "FAIL"}:
        raise ValueError(f"ROUND16A_EVIDENCE_STATUS_GATE:{label}:{status or 'MISSING'}")
    return status


def nested(document: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    value: Any = document
    for key in keys:
        if not isinstance(value, Mapping) or key not in value:
            return default
        value = value[key]
    return value


def ingest_explicit(collector: Collector, document: Mapping[str, Any], label: str) -> None:
    collector.explicit_map(document.get("receipt"), f"{label}#/receipt")
    collector.explicit_map(document.get("metrics"), f"{label}#/metrics")
    collector.explicit_map(document.get("headlines"), f"{label}#/headlines")


def ingest_execution_log(collector: Collector, document: Mapping[str, Any], label: str) -> None:
    collector.add("EXECUTION_EVENT_COUNT", nested(document, "execution_events", "event_count"), label)
    collector.add("EXECUTION_LOG_SEQUENCE_GAP_COUNT", document.get("execution_log_sequence_gap_count"), label)
    collector.add("EXECUTION_EVENT_HASH_FAILURE_COUNT", document.get("execution_event_hash_failure_count"), label)
    collector.add("COMMAND_LOG_COUNT", nested(document, "command_ledger", "row_count"), label)
    collector.add("CHECKPOINT_COMMIT_COUNT", nested(document, "checkpoint_ledger", "row_count"), label)
    collector.add("FULL_COMMAND_LOG_READY", document.get("full_command_log_ready"), label)


def ingest_api(collector: Collector, document: Mapping[str, Any], label: str) -> None:
    mapping = {
        "ACTUAL_PRODUCTION_HTTP_TESTED": "actual_production_http_tested",
        "API_FAILURE_COUNT": "fail_count",
        "UNEXPECTED_5XX_COUNT": "unexpected_5xx_count",
        "STALE_STATE_ACCEPTED_COUNT": "stale_state_accepted_count",
        "INVALID_TARGET_ACCEPTED_COUNT": "invalid_target_accepted_count",
        "PUBLIC_EXPLORATION_ARCHIVE_OBJECT_ID_COUNT": "public_archive_object_id_count",
        "PUBLIC_EXPLORATION_ARCHIVE_OBJECT_TITLE_COUNT": "public_archive_object_title_count",
        "PUBLIC_EXPLORATION_RECORD_LINK_COUNT": "public_record_link_count",
        "PUBLIC_EXPLORATION_CONTEXT_REFERENCE_COUNT": "public_context_reference_count",
        "PUBLIC_EXPLORATION_SPACETIME_REFERENCE_COUNT": "public_spacetime_reference_count",
        "HELD_DATA_LEAK_COUNT": "held_data_leak_count",
    }
    for metric, key in mapping.items():
        collector.add(metric, document.get(key), label)


def ingest_production_http(collector: Collector, document: Mapping[str, Any], label: str) -> None:
    direct = {
        "ACTUAL_PRODUCTION_HTTP_TESTED": "actual_production_http_tested",
        "COLD_START_MS": "cold_start_ms",
        "FIRST_REQUEST_MS": "first_request_ms",
        "PRODUCTION_MODEL_LOAD_MS": "production_model_load_ms",
        "PRODUCTION_MODEL_RSS_DELTA_BYTES": "production_model_rss_delta_bytes",
        "PRODUCTION_MODEL_HEAP_DELTA_BYTES": "production_model_heap_delta_bytes",
        "TOTAL_HTTP_REQUEST_COUNT": "total_http_request_count",
        "HTTP_SUCCESS_COUNT": "http_success_count",
        "HTTP_FAILURE_COUNT": "http_failure_count",
        "HTTP_TIMEOUT_COUNT": "http_timeout_count",
        "UNEXPECTED_5XX_COUNT": "unexpected_5xx_count",
        "STATE_CORRUPTION_COUNT": "state_corruption_count",
        "SEMANTIC_HASH_MISMATCH_COUNT": "semantic_hash_mismatch_count",
        "PNG_CORRUPTION_COUNT": "png_corruption_count",
    }
    for metric, key in direct.items():
        collector.add(metric, document.get(key), label)
    for prefix, key in (("JSON_API", "json_api"), ("PNG", "png_api")):
        block = document.get(key, {})
        for suffix, leaf in (("P50_MS", "p50_ms"), ("P95_MS", "p95_ms"), ("P99_MS", "p99_ms"), ("MAX_MS", "maximum_ms")):
            collector.add(f"{prefix}_{suffix}", nested(block, leaf) if isinstance(block, Mapping) else None, label)


def ingest_concurrency(collector: Collector, document: Mapping[str, Any], label: str) -> None:
    collector.add("CONCURRENCY_TEST_COMPLETED", document.get("concurrency_test_completed"), label)
    collector.add("CONCURRENT_PNG_TEST_COMPLETED", document.get("concurrent_png_test_completed"), label)


def ingest_runtime(collector: Collector, document: Mapping[str, Any], label: str) -> None:
    mapping = {
        "PEAK_RSS_BYTES": "peak_rss_bytes",
        "PEAK_HEAP_USED_BYTES": "peak_heap_used_bytes",
        "PEAK_CPU_PERCENT": "peak_cpu_percent",
        "PEAK_EVENT_LOOP_DELAY_MS": "peak_event_loop_delay_ms",
    }
    for metric, key in mapping.items():
        collector.add(metric, document.get(key), label)
    detected = document.get("unbounded_memory_growth_detected")
    if isinstance(detected, bool):
        collector.add("UNBOUNDED_MEMORY_GROWTH_COUNT", int(detected), label)


def ingest_build_time(collector: Collector, document: Mapping[str, Any], label: str) -> None:
    for key, value in document.items():
        if key.endswith(("_duration_ms", "_bytes")) and scalar(value):
            collector.add(key, value, label)


def ingest_sustained(collector: Collector, document: Mapping[str, Any], label: str) -> None:
    collector.add("SUSTAINED_LOAD_TEST_COMPLETED", document.get("sustained_load_test_completed"), label)
    collector.add("SUSTAINED_MINIMUM_REQUEST_COUNT", nested(document, "termination_criterion", "minimum_request_count"), label)
    collector.add("SUSTAINED_MINIMUM_DURATION_MS", nested(document, "termination_criterion", "minimum_duration_ms"), label)
    collector.add("SUSTAINED_REQUEST_COUNT", document.get("request_count"), label)
    collector.add("SUSTAINED_DURATION_MS", document.get("duration_ms"), label)


def ingest_reproduction(collector: Collector, document: Mapping[str, Any], label: str) -> None:
    status = document.get("reproducibility_verification", document.get("status"))
    collector.add("REPRODUCIBILITY_VERIFICATION", status, label)
    collector.explicit_map(document, f"{label}#/")
    ingest_explicit(collector, document, label)
    # Accept either a flat match map or per-artifact records.
    for container_name in ("hash_matches", "artifact_hash_matches", "matches"):
        container = document.get(container_name)
        if isinstance(container, Mapping):
            collector.explicit_map(container, f"{label}#/{container_name}")
    artifacts = document.get("artifacts")
    if isinstance(artifacts, list):
        for row in artifacts:
            if not isinstance(row, Mapping):
                continue
            metric = row.get("metric_name", row.get("hash_match_metric"))
            if metric:
                collector.add(str(metric), row.get("match", row.get("value")), f"{label}#/artifacts")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO)
    for label, filename in DEFAULT_INPUTS.items():
        parser.add_argument(f"--{label.replace('_', '-')}", type=Path, default=Path(filename))
    parser.add_argument("--output", type=Path, default=Path("final-gate-evidence.json"))
    return parser.parse_args()


def resolve(repo: Path, value: Path) -> Path:
    if value.is_absolute():
        return value.resolve()
    direct = (repo / value).resolve()
    if direct.is_file():
        return direct
    return (repo / RAW_RELATIVE / value).resolve()


def write_json(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    raw = repo / RAW_RELATIVE
    paths = {label: resolve(repo, getattr(args, label)) for label in DEFAULT_INPUTS}
    missing_paths = [path.relative_to(repo).as_posix() if path.is_relative_to(repo) else str(path) for path in paths.values() if not path.is_file()]
    if missing_paths:
        raise FileNotFoundError(f"ROUND16A_FINAL_GATE_INPUT_MISSING:{missing_paths}")

    documents: dict[str, Mapping[str, Any]] = {}
    source_records: dict[str, Any] = {}
    failed_sources: list[str] = []
    for label, path in paths.items():
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, Mapping):
            raise ValueError(f"ROUND16A_FINAL_GATE_INPUT_NOT_OBJECT:{label}")
        documents[label] = value
        evidence_status = required_status(value, label)
        if evidence_status == "FAIL":
            failed_sources.append(label)
        source_records[label] = {
            "path": path.relative_to(repo).as_posix() if path.is_relative_to(repo) else str(path),
            "sha256": sha256(path),
            "schema_version": value.get("schema_version", value.get("format", "NOT_RECORDED")),
            "status": evidence_status,
        }

    collector = Collector()
    for label, document in documents.items():
        ingest_explicit(collector, document, label)
    ingest_execution_log(collector, documents["execution_log"], "execution_log")
    ingest_api(collector, documents["api_functional"], "api_functional")
    ingest_production_http(collector, documents["production_http"], "production_http")
    ingest_concurrency(collector, documents["concurrency"], "concurrency")
    ingest_runtime(collector, documents["runtime_memory"], "runtime_memory")
    ingest_build_time(collector, documents["build_time"], "build_time")
    ingest_sustained(collector, documents["sustained_load"], "sustained_load")
    ingest_reproduction(collector, documents["reproduction"], "reproduction")

    # The sustained dual criterion is a closure condition, not a marketing SLO.
    criterion_failures: list[str] = []
    if collector.values.get("SUSTAINED_MINIMUM_REQUEST_COUNT", 0) < 10_000:
        criterion_failures.append("SUSTAINED_MINIMUM_REQUEST_COUNT_LT_10000")
    if collector.values.get("SUSTAINED_MINIMUM_DURATION_MS", 0) < 300_000:
        criterion_failures.append("SUSTAINED_MINIMUM_DURATION_MS_LT_300000")
    if collector.values.get("SUSTAINED_REQUEST_COUNT", 0) < collector.values.get("SUSTAINED_MINIMUM_REQUEST_COUNT", 10**30):
        criterion_failures.append("SUSTAINED_REQUEST_COUNT_CRITERION_NOT_MET")
    if collector.values.get("SUSTAINED_DURATION_MS", 0) < collector.values.get("SUSTAINED_MINIMUM_DURATION_MS", 10**30):
        criterion_failures.append("SUSTAINED_DURATION_CRITERION_NOT_MET")

    collector.add("FINAL_GATE_SOURCE_FAILURE_COUNT", len(failed_sources), "computed by build_final_gate_evidence.py")
    collector.add("FINAL_GATE_CRITERION_FAILURE_COUNT", len(criterion_failures), "computed by build_final_gate_evidence.py")

    missing_metrics = sorted(metric for metric in REQUIRED_AGGREGATED_METRICS if metric not in collector.values)
    status = "PASS" if not missing_metrics and not collector.conflicts else "FAIL"
    closure_evidence_status = "PASS" if status == "PASS" and not failed_sources and not criterion_failures else "FAIL"
    document = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "closure_evidence_status": closure_evidence_status,
        "failed_source_labels": sorted(failed_sources),
        "sources": source_records,
        "metrics": dict(sorted(collector.values.items())),
        "metric_sources": {key: sorted(set(value)) for key, value in sorted(collector.sources.items())},
        "missing_required_metrics": missing_metrics,
        "conflicts": collector.conflicts,
        "criterion_failures": criterion_failures,
    }
    output = resolve(repo, args.output)
    if not output.parent.is_dir():
        raise FileNotFoundError(f"ROUND16A_FINAL_GATE_OUTPUT_PARENT_MISSING:{output.parent}")
    write_json(output, document)
    print(json.dumps({
        "status": status,
        "closure_evidence_status": closure_evidence_status,
        "output": output.relative_to(repo).as_posix() if output.is_relative_to(repo) else str(output),
        "metric_count": len(collector.values),
        "missing_required_metric_count": len(missing_metrics),
        "conflict_count": len(collector.conflicts),
        "criterion_failure_count": len(criterion_failures),
    }, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
