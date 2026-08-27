#!/usr/bin/env python3
"""Create or verify the detached Round 16A audit-package seal.

The seal has two layers:

1. ``raw/deterministic-artifact-sha-manifest-v2.json`` is produced by the
   independent verifier's hash-only mode and covers semantic artifacts,
   governed inputs, production read-model/API sources, and generator sources.
2. ``MANIFEST.json`` plus ``SHA256SUMS.txt`` covers the complete research and
   audit package after excluding only the seal controls and append-only
   operational streams.

The operational streams are excluded from the package manifest because a
logged seal command necessarily appends to them after the child process exits.
They are governed separately by ``raw/execution-log-verification.json``.  For
the strongest terminal state, run that verifier and this seal helper directly
after the last normally logged command; no later command may mutate a sealed
non-operational artifact.  Final sealing fail-closes unless the execution-log
receipt hashes the current event and ledger bytes, so ``--stage final`` must
not be invoked inside the append-only logger.  The logged ``pre-report`` gate
provides its command evidence without creating this self-reference.

``--stage pre-report`` writes a stable machine-evidence gate receipt so the
report builder can resolve ``AUDIT_SEAL=PASS``.  That receipt is then included
inside the final package manifest and is never rewritten on a successful final
seal; this breaks the otherwise unavoidable report/seal hash cycle.
``--stage final`` additionally requires the complete 00--23 research-document
set and writes the detached ``raw/audit-package-seal.json``.  ``--stage check``
performs a read-only verification of the final seal.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Iterable


SCHEMA_VERSION = "trace-exploration-round16a-audit-seal-v2"
SOURCE_SHA = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e"
DATABASE_SNAPSHOT = "v49:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e"
REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_REL = Path("docs/audits/v49-exploration-full-space-closure-round1")
RAW_REL = AUDIT_REL / "raw"
RESEARCH_REL = Path("docs/research/trace-v49-exploration-full-space-closure-round1")
MANIFEST_REL = AUDIT_REL / "MANIFEST.json"
CHECKSUMS_REL = AUDIT_REL / "SHA256SUMS.txt"
RESULT_REL = RAW_REL / "audit-seal-result.json"
PACKAGE_RESULT_REL = RAW_REL / "audit-package-seal.json"
ARTIFACT_MANIFEST_REL = RAW_REL / "deterministic-artifact-sha-manifest-v2.json"


REQUIRED_RAW_FILES = (
    "environment.json",
    "execution-events.jsonl",
    "command-ledger.tsv",
    "checkpoint-ledger.tsv",
    "execution-log-verification.json",
    "authority-reconciliation-result.json",
    "repository-boundary-receipt.json",
    "database-identity-v2.json",
    "category-authority-v2.tsv",
    "vocabulary-candidate-universe-v2.tsv",
    "vocabulary-census-v2.tsv",
    "future-vocabulary-candidates.tsv",
    "pair-universe-v2.tsv",
    "association-census-v2.tsv",
    "association-evidence-ledger-v2.tsv",
    "association-query-log-v2.jsonl",
    "validated-association-graph-v2.json",
    "graph-statistics-v2.json",
    "exploration-parameter-universe-v2.json",
    "composition-enumeration-v2.tsv",
    "composition-rejection-ledger-v2.tsv",
    "canonical-composition-registry-v2.json",
    "composition-statistics-v2.json",
    "category-entry-census-v2.tsv",
    "state-census-v2.tsv",
    "transition-census-v2.tsv",
    "workflow-census-v2.tsv",
    "export-census-v2.tsv",
    "api-functional-validation-v2.json",
    "png-validation-v2.tsv",
    "production-http-results.json",
    "concurrency-results.json",
    "runtime-memory-results.json",
    "build-time-computation-results.json",
    "sustained-load-results.json",
    "metric-dictionary.json",
    "headline-numbers.json",
    "independent-verification.json",
    "independent-verification-cases-v2.tsv",
    "reproducibility-verification.json",
    "quantitative-audit.json",
    "api-functional-http-case-ledger-v2.tsv",
)


REQUIRED_FINAL_RAW_FILES = (
    "audit-seal-result.json",
    "deterministic-artifact-sha-manifest-v2.json",
    "regression-results.json",
    "gate-status-results.json",
    "final-gate-evidence.json",
    "BRANDING_SAFE_METRICS.md",
)


REQUIRED_FINAL_REPORTS = (
    "00_LIVE_EXECUTION_LOG.md",
    "01_AUTHORITY_AND_ARCHITECTURE_RECONCILIATION.md",
    "02_ROUND16A_GOAL_AND_METHOD.md",
    "03_VOCABULARY_UNIVERSE_METHOD.md",
    "04_ASSOCIATION_CENSUS_METHOD.md",
    "05_EVIDENCE_SEARCH_PROTOCOL.md",
    "06_VALIDATED_GRAPH_REPORT.md",
    "07_PARAMETER_UNIVERSE.md",
    "08_COMPOSITION_ENUMERATION_METHOD.md",
    "09_CANONICALISATION_POLICY.md",
    "10_TOPOLOGY_CENSUS.md",
    "11_CATEGORY_ENTRY_CENSUS.md",
    "12_STATE_AND_TRANSITION_CENSUS.md",
    "13_CANONICAL_WORKFLOW_CENSUS.md",
    "14_EXPORT_CENSUS.md",
    "15_API_AND_READ_MODEL_DECISION.md",
    "16_PRODUCTION_LOAD_METHOD.md",
    "17_PRODUCTION_LOAD_RESULTS.md",
    "18_STATISTICAL_CENSUS.md",
    "19_INDEPENDENT_VERIFICATION.md",
    "20_REPRODUCIBILITY.md",
    "21_LIMITATIONS.md",
    "22_FUNCTION3_CLOSURE_DECISION.md",
    "23_BRANDING_SAFE_METRICS.md",
)


# These paths cannot be placed inside a stable manifest while normal commands
# are still logged.  The exclusion is explicit, narrow, and machine-readable.
OPERATIONAL_EXCLUSIONS = (
    RESEARCH_REL / "00_LIVE_EXECUTION_LOG.md",
    RAW_REL / "execution-events.jsonl",
    RAW_REL / "command-ledger.tsv",
    RAW_REL / "checkpoint-ledger.tsv",
)
CONTROL_EXCLUSIONS = (MANIFEST_REL, CHECKSUMS_REL, PACKAGE_RESULT_REL)
COMMANDS_PREFIX = RAW_REL / "commands"
PACKAGE_EXTRA_RELS = (
    Path("PROJECT_LOG.md"),
    Path("docs/research/EXPLORATION_CURRENT.md"),
)


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def compact_canonical_hash(value: Any) -> str:
    content = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def read_tsv_count(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle, delimiter="\t"))


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def validate_machine_gates(
    repo: Path,
    *,
    require_current_execution_inputs: bool,
    require_final_evidence: bool,
) -> dict[str, Any]:
    raw = repo / RAW_REL
    missing = [name for name in REQUIRED_RAW_FILES if not (raw / name).is_file()]
    empty = [
        name
        for name in REQUIRED_RAW_FILES
        if (raw / name).is_file() and (raw / name).stat().st_size == 0
    ]
    require(not missing, "REQUIRED_RAW_FILES_MISSING:" + ",".join(missing))
    require(not empty, "REQUIRED_RAW_FILES_EMPTY:" + ",".join(empty))
    if require_final_evidence:
        final_missing = [
            name for name in REQUIRED_FINAL_RAW_FILES if not (raw / name).is_file()
        ]
        final_empty = [
            name
            for name in REQUIRED_FINAL_RAW_FILES
            if (raw / name).is_file() and (raw / name).stat().st_size == 0
        ]
        require(
            not final_missing,
            "REQUIRED_FINAL_RAW_FILES_MISSING:" + ",".join(final_missing),
        )
        require(
            not final_empty,
            "REQUIRED_FINAL_RAW_FILES_EMPTY:" + ",".join(final_empty),
        )

    independent = read_json(raw / "independent-verification.json")
    require(independent.get("status") == "PASS", "INDEPENDENT_VERIFICATION_NOT_PASS")
    require(independent.get("fail_count") == 0, "INDEPENDENT_FAILURE_COUNT_NONZERO")
    require(independent.get("skip_count") == 0, "INDEPENDENT_SKIP_COUNT_NONZERO")
    require(
        independent.get("generator_import_count") == 0,
        "INDEPENDENT_GENERATOR_IMPORT_COUNT_NONZERO",
    )

    reproduction = read_json(raw / "reproducibility-verification.json")
    require(reproduction.get("status") == "PASS", "REPRODUCIBILITY_NOT_PASS")
    named_reproduction_gates = (
        "VOCABULARY_CENSUS_HASH_MATCH",
        "PAIR_CENSUS_HASH_MATCH",
        "GRAPH_HASH_MATCH",
        "COMPOSITION_REGISTRY_HASH_MATCH",
        "STATE_CENSUS_HASH_MATCH",
        "TRANSITION_CENSUS_HASH_MATCH",
        "WORKFLOW_CENSUS_HASH_MATCH",
        "EXPORT_CENSUS_HASH_MATCH",
    )
    require(
        all(reproduction.get(name) is True for name in named_reproduction_gates),
        "REPRODUCIBILITY_NAMED_HASH_GATE_FAILED",
    )
    require(
        reproduction.get("all_deterministic_artifacts_match") is True,
        "REPRODUCIBILITY_ALL_DETERMINISTIC_ARTIFACTS_NOT_MATCHED",
    )
    require(
        reproduction.get("clean_worktree_reproduction") is True,
        "REPRODUCIBILITY_WORKTREE_NOT_CLEAN",
    )
    require(
        reproduction.get("network_request_count") == 0,
        "REPRODUCIBILITY_NETWORK_REQUEST_COUNT_NONZERO",
    )
    reproduction_network = reproduction.get("network_enforcement")
    require(
        isinstance(reproduction_network, dict)
        and reproduction_network.get("python_audit_hook")
        == "DENY_DNS_AND_SOCKET_CONNECT"
        and reproduction_network.get("search_replay_mode") == "MERGE_ONLY"
        and reproduction_network.get("capture_command_count") == 0
        and reproduction_network.get("unguarded_command_count") == 0
        and type(reproduction_network.get("guarded_command_count")) is int
        and reproduction_network.get("guarded_command_count", 0) > 0,
        "REPRODUCIBILITY_NETWORK_ENFORCEMENT_INVALID",
    )
    reproduction_offline = reproduction.get("offline_search_replay")
    require(
        isinstance(reproduction_offline, dict)
        and reproduction_offline.get("mode") == "MERGE_ONLY"
        and reproduction_offline.get("network_capture_enabled") is False
        and reproduction_offline.get("network_request_count") == 0
        and reproduction_offline.get("cache_unchanged") is True
        and reproduction_offline.get("shards_unchanged") is True
        and reproduction_offline.get("frozen_inputs_unchanged") is True,
        "REPRODUCIBILITY_OFFLINE_SEARCH_REPLAY_INVALID",
    )
    governed_preflight = reproduction.get("governed_source_input_preflight")
    require(
        isinstance(governed_preflight, dict)
        and governed_preflight.get("match") is True
        and governed_preflight.get("mismatch_count") == 0,
        "REPRODUCIBILITY_GOVERNED_PREFLIGHT_NOT_MATCHED",
    )
    reproduction_independent = reproduction.get("independent_verifier")
    require(
        isinstance(reproduction_independent, dict)
        and reproduction_independent.get("pass") is True,
        "REPRODUCIBILITY_INDEPENDENT_VERIFIER_NOT_PASS",
    )

    quantitative = read_json(raw / "quantitative-audit.json")
    require(quantitative.get("status") == "PASS", "QUANTITATIVE_AUDIT_NOT_PASS")
    api = read_json(raw / "api-functional-validation-v2.json")
    require(api.get("status") == "PASS", "API_FUNCTIONAL_VALIDATION_NOT_PASS")
    require(api.get("actual_production_http_tested") is True, "PRODUCTION_HTTP_NOT_TESTED")
    require(api.get("fail_count") == 0, "API_FUNCTIONAL_FAILURE_COUNT_NONZERO")
    execution = read_json(raw / "execution-log-verification.json")
    require(execution.get("status") == "PASS", "EXECUTION_LOG_VERIFICATION_NOT_PASS")
    require(
        execution.get("execution_log_sequence_gap_count") == 0,
        "EXECUTION_LOG_SEQUENCE_GAP_COUNT_NONZERO",
    )
    require(
        execution.get("execution_event_hash_failure_count") == 0,
        "EXECUTION_EVENT_HASH_FAILURE_COUNT_NONZERO",
    )
    require(execution.get("full_command_log_ready") is True, "FULL_COMMAND_LOG_NOT_READY")
    event_hash_summary = execution.get("event_output_hashes")
    require(
        isinstance(event_hash_summary, dict)
        and event_hash_summary.get("reconciliation_rule")
        == "APPEND_ONLY_LATEST_COMPLETED_WRITER_V1"
        and event_hash_summary.get("mismatch_count") == 0,
        "EXECUTION_LATEST_WRITER_RECONCILIATION_INVALID",
    )
    command_summary = execution.get("command_ledger")
    require(isinstance(command_summary, dict), "EXECUTION_COMMAND_LEDGER_SUMMARY_INVALID")
    require(
        command_summary.get("inflight_command_group_count") == 0,
        "EXECUTION_COMMAND_GROUP_STILL_INFLIGHT",
    )
    require(
        command_summary.get("unledgered_completed_artifact_count") == 0,
        "EXECUTION_UNLEDGERED_COMPLETED_ARTIFACT_COUNT_NONZERO",
    )
    require(
        command_summary.get("truncation_policy_marker_count") == 0,
        "EXECUTION_COMMAND_LOG_TRUNCATION_MARKER_COUNT_NONZERO",
    )
    execution_inputs = execution.get("inputs")
    require(isinstance(execution_inputs, list), "EXECUTION_LOG_INPUT_INVENTORY_INVALID")
    execution_inputs_by_path = {
        row.get("path"): row
        for row in execution_inputs
        if isinstance(row, dict) and isinstance(row.get("path"), str)
    }
    execution_input_freshness_matches: dict[str, bool] = {}
    for relative in (
        RAW_REL / "execution-events.jsonl",
        RAW_REL / "command-ledger.tsv",
        RAW_REL / "checkpoint-ledger.tsv",
    ):
        name = relative.as_posix()
        row = execution_inputs_by_path.get(name)
        matches = (
            isinstance(row, dict)
            and isinstance(row.get("sha256"), str)
            and (repo / relative).is_file()
            and sha256_file(repo / relative) == row["sha256"]
        )
        execution_input_freshness_matches[name] = matches
    if require_current_execution_inputs:
        stale = sorted(
            path for path, matches in execution_input_freshness_matches.items()
            if not matches
        )
        require(
            not stale,
            "EXECUTION_LOG_VERIFICATION_INPUTS_STALE:" + ",".join(stale),
        )

    png_count = read_tsv_count(raw / "png-validation-v2.tsv")
    require(png_count == 11520, f"PNG_VALIDATION_ROW_COUNT:{png_count}")
    query_count = sum(
        1
        for line in (raw / "association-query-log-v2.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    )
    require(query_count == 465, f"ASSOCIATION_QUERY_LOG_ROW_COUNT:{query_count}")

    # Parse every final runtime receipt now; domain verifiers own their detailed
    # schemas, while the seal owns exact final bytes.
    runtime_names = (
        "production-http-results.json",
        "concurrency-results.json",
        "runtime-memory-results.json",
        "build-time-computation-results.json",
        "sustained-load-results.json",
    )
    runtime_receipts = {name: read_json(raw / name) for name in runtime_names}
    runtime_failures = sorted(
        name for name, document in runtime_receipts.items()
        if document.get("status") != "PASS"
    )
    require(
        not runtime_failures,
        "RUNTIME_RECEIPT_NOT_PASS:" + ",".join(runtime_failures),
    )
    if require_final_evidence:
        regression = read_json(raw / "regression-results.json")
        gate_status = read_json(raw / "gate-status-results.json")
        final_gate = read_json(raw / "final-gate-evidence.json")
        stable_seal = read_json(raw / "audit-seal-result.json")
        require(regression.get("status") == "PASS", "REGRESSION_RESULTS_NOT_PASS")
        require(gate_status.get("status") == "PASS", "GATE_STATUS_RESULTS_NOT_PASS")
        require(not gate_status.get("failed_gates"), "GATE_STATUS_FAILED_GATES_NONEMPTY")
        require(final_gate.get("status") == "PASS", "FINAL_GATE_EVIDENCE_NOT_PASS")
        require(
            final_gate.get("closure_evidence_status") == "PASS",
            "FINAL_GATE_CLOSURE_EVIDENCE_NOT_PASS",
        )
        require(
            not final_gate.get("missing_required_metrics"),
            "FINAL_GATE_REQUIRED_METRICS_MISSING",
        )
        require(not final_gate.get("conflicts"), "FINAL_GATE_METRIC_CONFLICTS_NONEMPTY")
        require(
            not final_gate.get("criterion_failures"),
            "FINAL_GATE_CRITERION_FAILURES_NONEMPTY",
        )
        require(
            not final_gate.get("failed_source_labels"),
            "FINAL_GATE_FAILED_SOURCE_LABELS_NONEMPTY",
        )
        final_gate_sources = final_gate.get("sources")
        require(isinstance(final_gate_sources, dict), "FINAL_GATE_SOURCES_INVALID")
        for label, source in sorted(final_gate_sources.items()):
            require(
                isinstance(source, dict),
                f"FINAL_GATE_SOURCE_RECORD_INVALID:{label}",
            )
            path_text = source.get("path")
            expected_hash = source.get("sha256")
            require(
                isinstance(path_text, str) and bool(path_text),
                f"FINAL_GATE_SOURCE_PATH_INVALID:{label}",
            )
            relative = Path(path_text)
            require(
                not relative.is_absolute(),
                f"FINAL_GATE_SOURCE_PATH_NOT_REPOSITORY_RELATIVE:{label}",
            )
            candidate = repo / relative
            current = candidate.resolve()
            require(
                current.is_relative_to(repo) and current.is_file()
                and not candidate.is_symlink(),
                f"FINAL_GATE_SOURCE_FILE_INVALID:{label}:{path_text}",
            )
            require(
                isinstance(expected_hash, str)
                and sha256_file(current) == expected_hash,
                f"FINAL_GATE_SOURCE_SHA256_STALE:{label}:{path_text}",
            )
        current_event_count = sum(
            1
            for line in (raw / "execution-events.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        )
        current_command_count = read_tsv_count(raw / "command-ledger.tsv")
        gate_log = gate_status.get("log_evidence")
        require(isinstance(gate_log, dict), "GATE_STATUS_LOG_EVIDENCE_INVALID")
        require(
            gate_log.get("execution_event_count") == current_event_count,
            "GATE_STATUS_EXECUTION_EVENT_COUNT_STALE",
        )
        require(
            gate_log.get("command_ledger_row_count") == current_command_count,
            "GATE_STATUS_COMMAND_LEDGER_ROW_COUNT_STALE",
        )
        final_metrics = final_gate.get("metrics")
        require(isinstance(final_metrics, dict), "FINAL_GATE_METRICS_INVALID")
        require(
            final_metrics.get("EXECUTION_EVENT_COUNT") == current_event_count,
            "FINAL_GATE_EXECUTION_EVENT_COUNT_STALE",
        )
        require(
            final_metrics.get("COMMAND_LOG_COUNT") == current_command_count,
            "FINAL_GATE_COMMAND_LOG_COUNT_STALE",
        )
        stable_receipt = stable_seal.get("receipt")
        require(
            stable_seal.get("status") == "PASS"
            and isinstance(stable_receipt, dict)
            and stable_receipt.get("AUDIT_SEAL") == "PASS",
            "STABLE_AUDIT_SEAL_RECEIPT_NOT_PASS",
        )
    return {
        "required_raw_file_count": len(REQUIRED_RAW_FILES),
        "required_final_raw_file_count": (
            len(REQUIRED_FINAL_RAW_FILES) if require_final_evidence else 0
        ),
        "independent_case_count": independent.get("case_count"),
        "independent_failure_count": independent.get("fail_count"),
        "independent_skip_count": independent.get("skip_count"),
        "png_validation_row_count": png_count,
        "association_query_log_row_count": query_count,
        "runtime_receipt_count": len(runtime_receipts),
        "reproducibility_named_hash_gate_count": len(named_reproduction_gates),
        "execution_input_freshness_required": require_current_execution_inputs,
        "execution_input_freshness_matches": execution_input_freshness_matches,
        "final_evidence_required": require_final_evidence,
    }


def require_final_reports(repo: Path) -> None:
    missing = [
        name for name in REQUIRED_FINAL_REPORTS if not (repo / RESEARCH_REL / name).is_file()
    ]
    empty = [
        name
        for name in REQUIRED_FINAL_REPORTS
        if (repo / RESEARCH_REL / name).is_file()
        and (repo / RESEARCH_REL / name).stat().st_size == 0
    ]
    require(not missing, "REQUIRED_FINAL_REPORTS_MISSING:" + ",".join(missing))
    require(not empty, "REQUIRED_FINAL_REPORTS_EMPTY:" + ",".join(empty))
    require(
        (repo / RAW_REL / "BRANDING_SAFE_METRICS.md").read_bytes()
        == (repo / RESEARCH_REL / "23_BRANDING_SAFE_METRICS.md").read_bytes(),
        "BRANDING_SAFE_METRICS_COPY_MISMATCH",
    )


def excluded(relative: Path) -> bool:
    if relative in CONTROL_EXCLUSIONS or relative in OPERATIONAL_EXCLUSIONS:
        return True
    if relative == COMMANDS_PREFIX or COMMANDS_PREFIX in relative.parents:
        return True
    return relative.name.endswith(".lock")


def package_paths(repo: Path) -> Iterable[Path]:
    for root_rel in (AUDIT_REL, RESEARCH_REL):
        root = repo / root_rel
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(repo)
            if not excluded(relative):
                yield relative
    for relative in PACKAGE_EXTRA_RELS:
        path = repo / relative
        if path.is_file() and not excluded(relative):
            yield relative


def package_entries(repo: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for relative in sorted(set(package_paths(repo)), key=lambda path: path.as_posix()):
        path = repo / relative
        require(not path.is_symlink(), f"SEAL_SYMLINK_NOT_ALLOWED:{relative}")
        entries.append(
            {
                "path": relative.as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return entries


def artifact_manifest_command(repo: Path) -> list[str]:
    return [
        sys.executable,
        "-B",
        str(repo / "scripts/trace_round16a/verify_full_space.py"),
        "--hash-only-manifest",
        str(repo / ARTIFACT_MANIFEST_REL),
    ]


def validate_artifact_manifest_document(
    repo: Path, manifest: dict[str, Any], *, verify_current_files: bool
) -> dict[str, Any]:
    require(
        manifest.get("schema_version")
        == "trace-exploration-round16a-artifact-sha-manifest-v2",
        "ARTIFACT_SHA_MANIFEST_SCHEMA_INVALID",
    )
    require(
        manifest.get("database_snapshot") == DATABASE_SNAPSHOT,
        "ARTIFACT_SHA_MANIFEST_DATABASE_SNAPSHOT_MISMATCH",
    )
    rows = manifest.get("files")
    require(isinstance(rows, list) and bool(rows), "ARTIFACT_SHA_MANIFEST_FILES_INVALID")
    require(manifest.get("file_count") == len(rows), "ARTIFACT_SHA_MANIFEST_FILE_COUNT_MISMATCH")
    material = {key: value for key, value in manifest.items() if key != "manifest_hash"}
    require(
        manifest.get("manifest_hash") == compact_canonical_hash(material),
        "ARTIFACT_SHA_MANIFEST_CANONICAL_HASH_MISMATCH",
    )
    seen_paths: set[str] = set()
    verified_current_file_count = 0
    for index, row in enumerate(rows):
        require(isinstance(row, dict), f"ARTIFACT_SHA_MANIFEST_ROW_INVALID:{index}")
        path_text = row.get("path")
        expected_bytes = row.get("bytes")
        expected_hash = row.get("sha256")
        require(
            isinstance(path_text, str) and bool(path_text),
            f"ARTIFACT_SHA_MANIFEST_PATH_INVALID:{index}",
        )
        require(path_text not in seen_paths, f"ARTIFACT_SHA_MANIFEST_PATH_DUPLICATE:{path_text}")
        seen_paths.add(path_text)
        require(
            type(expected_bytes) is int and expected_bytes >= 0,
            f"ARTIFACT_SHA_MANIFEST_BYTE_COUNT_INVALID:{path_text}",
        )
        require(
            isinstance(expected_hash, str)
            and len(expected_hash) == 64
            and all(character in "0123456789abcdef" for character in expected_hash),
            f"ARTIFACT_SHA_MANIFEST_SHA256_INVALID:{path_text}",
        )
        relative = Path(path_text)
        require(not relative.is_absolute(), f"ARTIFACT_SHA_MANIFEST_PATH_ABSOLUTE:{path_text}")
        candidate = repo / relative
        current = candidate.resolve()
        require(current.is_relative_to(repo), f"ARTIFACT_SHA_MANIFEST_PATH_ESCAPE:{path_text}")
        if verify_current_files:
            require(current.is_file(), f"ARTIFACT_SHA_MANIFEST_CURRENT_FILE_MISSING:{path_text}")
            require(not candidate.is_symlink(), f"ARTIFACT_SHA_MANIFEST_CURRENT_FILE_SYMLINK:{path_text}")
            require(
                current.stat().st_size == expected_bytes,
                f"ARTIFACT_SHA_MANIFEST_CURRENT_BYTE_COUNT_MISMATCH:{path_text}",
            )
            require(
                sha256_file(current) == expected_hash,
                f"ARTIFACT_SHA_MANIFEST_CURRENT_SHA256_MISMATCH:{path_text}",
            )
            verified_current_file_count += 1
    return {
        "file_count": len(rows),
        "manifest_hash": manifest["manifest_hash"],
        "current_files_verified": verify_current_files,
        "verified_current_file_count": verified_current_file_count,
    }


def generate_artifact_manifest(repo: Path) -> dict[str, Any]:
    argv = artifact_manifest_command(repo)
    print(
        "AUDIT_SEAL_ARTIFACT_MANIFEST_COMMAND "
        + json.dumps(argv, ensure_ascii=False)
    )
    completed = subprocess.run(
        argv,
        cwd=repo,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.stdout:
        sys.stdout.buffer.write(completed.stdout)
    if completed.stderr:
        sys.stderr.buffer.write(completed.stderr)
    sys.stdout.flush()
    sys.stderr.flush()
    require(completed.returncode == 0, "ARTIFACT_SHA_MANIFEST_GENERATION_FAILED")
    manifest = read_json(repo / ARTIFACT_MANIFEST_REL)
    require(manifest.get("file_count", 0) > 0, "ARTIFACT_SHA_MANIFEST_EMPTY")
    validate_artifact_manifest_document(
        repo, manifest, verify_current_files=False
    )
    return manifest


def manifest_document(entries: list[dict[str, Any]], stage: str) -> dict[str, Any]:
    material = {
        "schema_version": "trace-exploration-round16a-package-manifest-v2",
        "source_sha": SOURCE_SHA,
        "database_snapshot": DATABASE_SNAPSHOT,
        "stage": stage,
        "hash_algorithm": "SHA-256",
        "path_base": "repository-root",
        "file_count": len(entries),
        "total_bytes": sum(row["bytes"] for row in entries),
        "files": entries,
        "operational_exclusions": [
            path.as_posix() for path in (*OPERATIONAL_EXCLUSIONS, COMMANDS_PREFIX)
        ],
        "control_exclusions": [path.as_posix() for path in CONTROL_EXCLUSIONS],
    }
    return {**material, "manifest_hash": canonical_hash(material)}


def checksum_bytes(manifest_content: bytes, entries: list[dict[str, Any]]) -> bytes:
    lines = [
        f"{hashlib.sha256(manifest_content).hexdigest()}  {MANIFEST_REL.as_posix()}"
    ]
    lines.extend(f"{row['sha256']}  {row['path']}" for row in entries)
    return ("\n".join(lines) + "\n").encode("utf-8")


def gate_result_document() -> dict[str, Any]:
    """Return the stable report input that is embedded by the final seal."""
    return {
        "schema_version": "trace-exploration-round16a-audit-seal-gate-v2",
        "status": "PASS",
        "AUDIT_SEAL": "PASS",
        "audit_seal": "PASS",
        "receipt": {"AUDIT_SEAL": "PASS"},
        "metrics": {"AUDIT_SEAL": "PASS"},
        "seal_stage": "PRE_REPORT_MACHINE_EVIDENCE",
        "source_sha": SOURCE_SHA,
        "database_snapshot": DATABASE_SNAPSHOT,
        "final_package_seal_path": PACKAGE_RESULT_REL.as_posix(),
        "contract": (
            "STABLE_MACHINE_GATE_RECEIPT_INCLUDED_IN_FINAL_PACKAGE_MANIFEST"
        ),
    }


def package_result_document(
    *,
    manifest: dict[str, Any],
    manifest_content: bytes,
    checksums: bytes,
    artifact_manifest: dict[str, Any],
    artifact_manifest_sha256: str,
    gate_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "AUDIT_SEAL": "PASS",
        "audit_seal": "PASS",
        "receipt": {
            "AUDIT_SEAL": "PASS",
            "AUDIT_SEAL_STAGE": "FINAL",
            "AUDIT_SEAL_PACKAGE_FILE_COUNT": manifest["file_count"],
        },
        "metrics": {
            "AUDIT_SEAL": "PASS",
            "AUDIT_SEAL_PACKAGE_FILE_COUNT": manifest["file_count"],
            "AUDIT_SEAL_PACKAGE_TOTAL_BYTES": manifest["total_bytes"],
        },
        "seal_stage": "FINAL",
        "final_research_document_gate": True,
        "source_sha": SOURCE_SHA,
        "database_snapshot": DATABASE_SNAPSHOT,
        "package_manifest_path": MANIFEST_REL.as_posix(),
        "package_manifest_sha256": hashlib.sha256(manifest_content).hexdigest(),
        "package_manifest_hash": manifest["manifest_hash"],
        "package_file_count": manifest["file_count"],
        "package_total_bytes": manifest["total_bytes"],
        "checksums_path": CHECKSUMS_REL.as_posix(),
        "checksums_sha256": hashlib.sha256(checksums).hexdigest(),
        "deterministic_artifact_manifest_path": ARTIFACT_MANIFEST_REL.as_posix(),
        "deterministic_artifact_manifest_sha256": artifact_manifest_sha256,
        "deterministic_artifact_manifest_hash": artifact_manifest.get(
            "manifest_hash"
        ),
        "deterministic_artifact_file_count": artifact_manifest.get("file_count"),
        "execution_evidence_policy": (
            "APPEND_ONLY_OPERATIONAL_STREAMS_EXCLUDED_FROM_PACKAGE_MANIFEST_AND_"
            "GOVERNED_BY_EXECUTION_LOG_VERIFICATION_JSON"
        ),
        "operational_exclusions": manifest["operational_exclusions"],
        "control_exclusions": manifest["control_exclusions"],
        "machine_gate_summary": gate_summary,
    }


def generate(repo: Path, stage: str) -> dict[str, Any]:
    gate_summary = validate_machine_gates(
        repo,
        require_current_execution_inputs=stage == "FINAL",
        require_final_evidence=stage == "FINAL",
    )
    artifact_manifest = generate_artifact_manifest(repo)
    gate_result = gate_result_document()
    atomic_write(repo / RESULT_REL, canonical_bytes(gate_result))
    if stage == "PRE_REPORT":
        return gate_result

    require(stage == "FINAL", f"UNKNOWN_SEAL_STAGE:{stage}")
    require_final_reports(repo)
    entries = package_entries(repo)
    manifest = manifest_document(entries, "FINAL")
    manifest_content = canonical_bytes(manifest)
    checksums = checksum_bytes(manifest_content, entries)
    atomic_write(repo / MANIFEST_REL, manifest_content)
    atomic_write(repo / CHECKSUMS_REL, checksums)
    result = package_result_document(
        manifest=manifest,
        manifest_content=manifest_content,
        checksums=checksums,
        artifact_manifest=artifact_manifest,
        artifact_manifest_sha256=sha256_file(repo / ARTIFACT_MANIFEST_REL),
        gate_summary=gate_summary,
    )
    atomic_write(repo / PACKAGE_RESULT_REL, canonical_bytes(result))
    return result


def check(repo: Path) -> dict[str, Any]:
    gate_summary = validate_machine_gates(
        repo,
        require_current_execution_inputs=True,
        require_final_evidence=True,
    )
    require_final_reports(repo)
    manifest_path = repo / MANIFEST_REL
    checksums_path = repo / CHECKSUMS_REL
    gate_result_path = repo / RESULT_REL
    package_result_path = repo / PACKAGE_RESULT_REL
    for path in (
        manifest_path,
        checksums_path,
        gate_result_path,
        package_result_path,
        repo / ARTIFACT_MANIFEST_REL,
    ):
        require(path.is_file(), f"SEAL_CONTROL_MISSING:{path.relative_to(repo)}")
    entries = package_entries(repo)
    expected_manifest = manifest_document(entries, "FINAL")
    expected_content = canonical_bytes(expected_manifest)
    expected_checksums = checksum_bytes(expected_content, entries)
    require(manifest_path.read_bytes() == expected_content, "PACKAGE_MANIFEST_MISMATCH")
    require(checksums_path.read_bytes() == expected_checksums, "SHA256SUMS_MISMATCH")
    require(
        gate_result_path.read_bytes() == canonical_bytes(gate_result_document()),
        "AUDIT_SEAL_GATE_RECEIPT_MISMATCH",
    )
    artifact_manifest = read_json(repo / ARTIFACT_MANIFEST_REL)
    artifact_validation = validate_artifact_manifest_document(
        repo, artifact_manifest, verify_current_files=True
    )
    result = read_json(package_result_path)
    require(result.get("status") == "PASS", "AUDIT_SEAL_RESULT_NOT_PASS")
    require(result.get("AUDIT_SEAL") == "PASS", "AUDIT_SEAL_GATE_NOT_PASS")
    require(result.get("seal_stage") == "FINAL", "AUDIT_PACKAGE_SEAL_NOT_FINAL")
    require(
        result.get("final_research_document_gate") is True,
        "AUDIT_SEAL_FINAL_RESEARCH_DOCUMENT_GATE_NOT_TRUE",
    )
    result_receipt = result.get("receipt")
    require(
        isinstance(result_receipt, dict)
        and result_receipt.get("AUDIT_SEAL") == "PASS"
        and result_receipt.get("AUDIT_SEAL_STAGE") == "FINAL",
        "AUDIT_SEAL_RESULT_RECEIPT_INVALID",
    )
    require(result.get("source_sha") == SOURCE_SHA, "AUDIT_SEAL_RESULT_SOURCE_SHA_MISMATCH")
    require(
        result.get("database_snapshot") == DATABASE_SNAPSHOT,
        "AUDIT_SEAL_RESULT_DATABASE_SNAPSHOT_MISMATCH",
    )
    require(
        result.get("package_manifest_path") == MANIFEST_REL.as_posix(),
        "AUDIT_SEAL_RESULT_MANIFEST_PATH_MISMATCH",
    )
    require(
        result.get("package_manifest_sha256") == hashlib.sha256(expected_content).hexdigest(),
        "AUDIT_SEAL_RESULT_MANIFEST_SHA_MISMATCH",
    )
    require(
        result.get("package_manifest_hash") == expected_manifest.get("manifest_hash"),
        "AUDIT_SEAL_RESULT_MANIFEST_HASH_MISMATCH",
    )
    require(
        result.get("package_file_count") == expected_manifest.get("file_count")
        and result.get("package_total_bytes") == expected_manifest.get("total_bytes"),
        "AUDIT_SEAL_RESULT_PACKAGE_SIZE_MISMATCH",
    )
    require(
        result.get("checksums_path") == CHECKSUMS_REL.as_posix(),
        "AUDIT_SEAL_RESULT_CHECKSUM_PATH_MISMATCH",
    )
    require(
        result.get("checksums_sha256") == hashlib.sha256(expected_checksums).hexdigest(),
        "AUDIT_SEAL_RESULT_CHECKSUM_SHA_MISMATCH",
    )
    require(
        result.get("deterministic_artifact_manifest_sha256")
        == sha256_file(repo / ARTIFACT_MANIFEST_REL),
        "AUDIT_SEAL_RESULT_ARTIFACT_MANIFEST_SHA_MISMATCH",
    )
    require(
        result.get("deterministic_artifact_manifest_path")
        == ARTIFACT_MANIFEST_REL.as_posix(),
        "AUDIT_SEAL_RESULT_ARTIFACT_MANIFEST_PATH_MISMATCH",
    )
    require(
        result.get("deterministic_artifact_manifest_hash")
        == artifact_manifest.get("manifest_hash"),
        "AUDIT_SEAL_RESULT_ARTIFACT_MANIFEST_HASH_MISMATCH",
    )
    require(
        result.get("deterministic_artifact_file_count")
        == artifact_manifest.get("file_count"),
        "AUDIT_SEAL_RESULT_ARTIFACT_MANIFEST_FILE_COUNT_MISMATCH",
    )
    require(
        result.get("operational_exclusions") == expected_manifest.get("operational_exclusions")
        and result.get("control_exclusions") == expected_manifest.get("control_exclusions"),
        "AUDIT_SEAL_RESULT_EXCLUSION_POLICY_MISMATCH",
    )
    require(
        result.get("machine_gate_summary") == gate_summary,
        "AUDIT_SEAL_RESULT_MACHINE_GATE_SUMMARY_STALE",
    )
    return {
        **result,
        "verification_mode": "READ_ONLY_CHECK",
        "deterministic_artifact_validation": artifact_validation,
        "machine_gate_summary": gate_summary,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--stage",
        choices=("pre-report", "final", "check"),
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo_root.resolve()
    try:
        if args.stage == "check":
            result = check(repo)
        else:
            result = generate(repo, args.stage.replace("-", "_").upper())
        exit_code = 0
    except Exception as error:
        result = {
            "schema_version": SCHEMA_VERSION,
            "status": "FAIL",
            "AUDIT_SEAL": "FAIL",
            "audit_seal": "FAIL",
            "receipt": {"AUDIT_SEAL": "FAIL"},
            "metrics": {"AUDIT_SEAL": "FAIL"},
            "seal_stage": args.stage.replace("-", "_").upper(),
            "error_codes": [f"{type(error).__name__}:{error}"],
        }
        if args.stage == "pre-report":
            atomic_write(repo / RESULT_REL, canonical_bytes(result))
        elif args.stage == "final":
            atomic_write(repo / PACKAGE_RESULT_REL, canonical_bytes(result))
        exit_code = 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
