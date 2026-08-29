#!/usr/bin/env python3
"""Independently verify the Checkpoint 016 production-HTTP evidence bundle.

This verifier does not import or execute the primary HTTP verifier.  It reads
the committed v3 model and the completed fresh-checkout output directory,
reconstructs the expected case identities and distributions, validates every
receipt against the case ledger and runtime probe, and writes one deterministic
independent-verification receipt.

Run-specific timestamps, process identifiers, build identifiers, timings, and
memory observations are validated for type, range, ordering, and internal
consistency; they are deliberately not pinned to Checkpoint 015 values.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
import datetime as dt
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Mapping, Sequence
import uuid


VERIFIER_VERSION = "trace-round16b-v3-production-http-checkpoint016-independent-verifier-v1"
API_BASE = "/api/trace/v3/exploration"
API_VERSION = "trace-exploration/v3"
PERFORMANCE_INTERPRETATION = "OBSERVATIONAL_NO_SLO_OR_PRODUCTION_CAPACITY_CLAIM"

EXPECTED_READ_MODEL_SHA256 = "f1ae8a35895b27c15fb3d9b42828b8611633ee8ee7e2cbc825772b590304351b"
EXPECTED_MANIFEST_SHA256 = "2ee550028cb60749bee7efa456ed21ea4f0c6170bb5c68d8888017fc948fdd2c"
EXPECTED_CHECKSUMS_SHA256 = "002d13c9175354054ee550b4d55d275ea2fad1c10693991bd726897aa50e8173"
EXPECTED_READ_MODEL_BYTES = 151_170
EXPECTED_CAPABILITIES_RESPONSE_SHA256 = (
    "01eac840347efa58ff68d4431a463f7d7dd610dacc575ad788217bbd1b9cacab"
)
EXPECTED_CAPABILITIES_RESPONSE_BYTES = 4_005
EXPECTED_EXPORT_SEMANTIC_SHA256 = (
    "cc480debb3605e2a471cad9a1cb0cbbe463f88a5753c98f2bf519338c4844827"
)
EXPECTED_EXPORT_PRESENTATION_SHA256 = (
    "9ee6e1855ec26c4a6e40baec4b33f927ffaf296693dc6d4d3ace51179fc517c4"
)
EXPECTED_EXPORT_RESPONSE_SHA256 = (
    "9a1871de01e723a24ffb410dc33af0724db978abdf99e9b262050285754c8259"
)
EXPECTED_EXPORT_RESPONSE_BYTES = 2_384
EXPECTED_EXPORT_PROJECTION_RECORD_COUNT = 3

PHASE_COUNTS = {
    "ARTIFACT_CHECK": 1,
    "FUNCTIONAL_HTTP": 160,
    "CONCURRENCY_C1": 100,
    "CONCURRENCY_C5": 100,
    "CONCURRENCY_C10": 100,
    "CONCURRENCY_C25": 100,
    "CONCURRENCY_C50": 100,
    "SUSTAINED_READ": 500,
    "CONTROL_EXPORT_REPLAY_PRELOAD": 5,
    "CONTROL_EXPORT_REPLAY_POSTLOAD": 2,
}
TOTAL_CASE_COUNT = sum(PHASE_COUNTS.values())
CONCURRENCY_LEVELS = (1, 5, 10, 25, 50)

CASE_FIELDS = (
    "case_id",
    "phase",
    "method",
    "path",
    "expected_status",
    "actual_status",
    "outcome",
    "latency_ms",
    "response_bytes",
    "response_sha256",
    "error",
)

SUMMARY_HASHED_ARTIFACTS = (
    "artifact-check-receipt.json",
    "concurrency-receipt.json",
    "control-export-replay-receipt.json",
    "functional-http-receipt.json",
    "http-cases.tsv",
    "runtime-memory-receipt.json",
    "runtime-probe.jsonl",
    "server-output.txt",
    "startup-receipt.json",
    "sustained-read-receipt.json",
)
OUTPUT_ARTIFACTS = frozenset((*SUMMARY_HASHED_ARTIFACTS, "verification-summary.json"))

SURFACE_SPECS = (
    ("association-realizations", "association_realizations", "association_realization_id"),
    ("associations", "associations", "association_id"),
    (
        "composition-coherence-reviews",
        "composition_coherence_reviews",
        "composition_coherence_review_id",
    ),
    ("compositions", "compositions", "composition_id"),
    ("concept-senses", "concept_senses", "sense_id"),
    ("concepts", "concepts", "concept_id"),
    ("exports", "exports", "export_id"),
    ("incidences", "incidences", "incidence_id"),
    ("navigation-states", "navigation_states", "state_id"),
    ("scopes", "scopes", "scope_id"),
    ("transitions", "transitions", "transition_id"),
    ("workflows", "workflows", "workflow_id"),
)
SURFACE_KEYS = tuple(item[1] for item in SURFACE_SPECS)
EXPECTED_CONTROL_COUNTS = {
    "association_realizations": 10,
    "associations": 14,
    "composition_coherence_reviews": 2,
    "compositions": 2,
    "concept_senses": 21,
    "concepts": 21,
    "exports": 1,
    "incidences": 37,
    "navigation_states": 1,
    "scopes": 6,
    "transitions": 0,
    "workflows": 1,
}
EXPECTED_CLOSURE_FLAGS = {
    "computational_space_closure": False,
    "function3_closure": False,
    "global_composition_coherence_closure": False,
    "higher_order_association_closure": False,
    "pair_association_closure": False,
    "product_association_reachability_closure": False,
}
EXPECTED_LOAD_PATHS = frozenset(
    {
        f"{API_BASE}/capabilities",
        f"{API_BASE}/baseline/reconciliation",
        *(f"{API_BASE}/{slug}" for slug, _, _ in SURFACE_SPECS),
    }
)
EXPECTED_FUNCTIONAL_METHOD_STATUS_COUNTS = {
    ("DELETE", "405"): 1,
    ("GET", "200"): 37,
    ("GET", "308"): 1,
    ("GET", "404"): 38,
    ("HEAD", "200"): 36,
    ("HEAD", "308"): 1,
    ("HEAD", "404"): 38,
    ("OPTIONS", "204"): 3,
    ("PATCH", "405"): 1,
    ("POST", "404"): 1,
    ("POST", "405"): 2,
    ("PUT", "405"): 1,
}


class VerificationFailure(RuntimeError):
    """Fail-closed validation error with a stable diagnostic code."""


@dataclass(frozen=True)
class CaseRow:
    case_id: str
    phase: str
    method: str
    path: str
    expected_status: str
    actual_status: str
    outcome: str
    latency_ms: float
    response_bytes: int
    response_sha256: str
    error: str


def require(condition: bool, code: str) -> None:
    if not condition:
        raise VerificationFailure(code)


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def finite_number(value: Any, code: str, *, minimum: float | None = None) -> float:
    require(is_number(value), f"{code}:NOT_NUMBER")
    converted = float(value)
    require(math.isfinite(converted), f"{code}:NOT_FINITE")
    if minimum is not None:
        require(converted >= minimum, f"{code}:BELOW_MINIMUM")
    return converted


def exact_keys(value: Mapping[str, Any], expected: Iterable[str], code: str) -> None:
    expected_set = set(expected)
    observed_set = set(value)
    require(
        observed_set == expected_set,
        f"{code}:KEYS:missing={sorted(expected_set - observed_set)}:extra={sorted(observed_set - expected_set)}",
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reject_json_constant(value: str) -> None:
    raise VerificationFailure(f"JSON_NONFINITE_CONSTANT:{value}")


def unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"JSON_DUPLICATE_KEY:{key}")
        result[key] = value
    return result


def parse_json_bytes(raw: bytes, code: str) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise VerificationFailure(f"{code}:UTF8:{error}") from error
    try:
        value = json.loads(
            text,
            object_pairs_hook=unique_json_object,
            parse_constant=reject_json_constant,
        )
    except json.JSONDecodeError as error:
        raise VerificationFailure(f"{code}:JSON:{error}") from error
    require(isinstance(value, dict), f"{code}:OBJECT_REQUIRED")
    return value


def read_receipt(path: Path, code: str) -> dict[str, Any]:
    raw = path.read_bytes()
    value = parse_json_bytes(raw, code)
    expected = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    require(raw == expected, f"{code}:NONCANONICAL_JSON")
    return value


def parse_utc(value: Any, code: str) -> dt.datetime:
    require(isinstance(value, str) and value.endswith("Z"), f"{code}:UTC_Z_REQUIRED")
    try:
        parsed = dt.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise VerificationFailure(f"{code}:INVALID:{error}") from error
    require(parsed.utcoffset() == dt.timedelta(0), f"{code}:OFFSET")
    return parsed


def resolve_from_repo(repo: Path, value: Path) -> Path:
    return value.resolve() if value.is_absolute() else (repo / value).resolve()


def path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def read_governed_model(repo: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    generated = repo / "frontend/generated/trace-exploration-v3"
    paths = {
        "read-model.json": generated / "read-model.json",
        "manifest.json": generated / "manifest.json",
        "CHECKSUMS.sha256": generated / "CHECKSUMS.sha256",
    }
    for name, path in paths.items():
        require(path.is_file() and not path.is_symlink(), f"GOVERNED_{name}:MISSING_OR_SYMLINK")
    hashes = {name: sha256_file(path) for name, path in paths.items()}
    require(hashes["read-model.json"] == EXPECTED_READ_MODEL_SHA256, "READ_MODEL_TRUST_ANCHOR")
    require(hashes["manifest.json"] == EXPECTED_MANIFEST_SHA256, "MANIFEST_TRUST_ANCHOR")
    require(hashes["CHECKSUMS.sha256"] == EXPECTED_CHECKSUMS_SHA256, "CHECKSUMS_TRUST_ANCHOR")
    require(paths["read-model.json"].stat().st_size == EXPECTED_READ_MODEL_BYTES, "READ_MODEL_BYTES")
    expected_checksums = (
        f"{EXPECTED_MANIFEST_SHA256}  manifest.json\n"
        f"{EXPECTED_READ_MODEL_SHA256}  read-model.json\n"
    ).encode("ascii")
    require(paths["CHECKSUMS.sha256"].read_bytes() == expected_checksums, "CHECKSUM_LEDGER_CONTENT")
    model = parse_json_bytes(paths["read-model.json"].read_bytes(), "READ_MODEL")
    manifest = parse_json_bytes(paths["manifest.json"].read_bytes(), "MANIFEST")
    require(model.get("api_version") == API_VERSION, "READ_MODEL_API_VERSION")
    require(manifest.get("api_version") == API_VERSION, "MANIFEST_API_VERSION")
    require(model.get("closure_flags") == EXPECTED_CLOSURE_FLAGS, "READ_MODEL_CLOSURE_FLAGS")
    active = model.get("active_product")
    controls = model.get("research_controls")
    require(isinstance(active, dict) and set(active) == set(SURFACE_KEYS), "ACTIVE_SURFACES")
    require(isinstance(controls, dict) and set(controls) == set(SURFACE_KEYS), "CONTROL_SURFACES")
    for key in SURFACE_KEYS:
        require(active[key] == [], f"ACTIVE_SURFACE_NOT_EMPTY:{key}")
        require(isinstance(controls[key], list), f"CONTROL_SURFACE_NOT_LIST:{key}")
        require(len(controls[key]) == EXPECTED_CONTROL_COUNTS[key], f"CONTROL_COUNT:{key}")
    exports = controls["exports"]
    require(len(exports) == 1 and isinstance(exports[0], dict), "GOVERNED_EXPORT_COUNT")
    export = exports[0]
    require(export.get("semantic_sha256") == EXPECTED_EXPORT_SEMANTIC_SHA256, "EXPORT_SEMANTIC")
    require(
        export.get("presentation_sha256") == EXPECTED_EXPORT_PRESENTATION_SHA256,
        "EXPORT_PRESENTATION",
    )
    require(export.get("pair_projection_policy_preserved") is True, "EXPORT_PAIR_POLICY")
    projection_records = export.get("projection_preservation_records")
    require(
        isinstance(projection_records, list)
        and len(projection_records) == EXPECTED_EXPORT_PROJECTION_RECORD_COUNT,
        "EXPORT_PROJECTION_RECORDS",
    )
    require(
        export.get("export_id") == f"export:v3:{EXPECTED_EXPORT_SEMANTIC_SHA256[:24]}",
        "EXPORT_ID_BINDING",
    )
    return model, manifest, hashes


def expected_case_ids() -> set[str]:
    result = {"A001", *(f"F{index:03d}" for index in range(1, 161))}
    result.update(f"E-PRE-{index:03d}" for index in range(1, 6))
    result.update(f"E-POST-{index:03d}" for index in range(1, 3))
    for level in CONCURRENCY_LEVELS:
        per_worker = 100 // level
        result.update(
            f"C{level:02d}-W{worker:02d}-R{sequence:04d}"
            for worker in range(level)
            for sequence in range(per_worker)
        )
    result.update(
        f"S-W{worker:02d}-R{sequence:05d}"
        for worker in range(10)
        for sequence in range(50)
    )
    require(len(result) == TOTAL_CASE_COUNT, "INTERNAL_EXPECTED_CASE_ID_COUNT")
    return result


def read_cases(path: Path) -> list[CaseRow]:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise VerificationFailure(f"CASE_LEDGER_UTF8:{error}") from error
    require(text.endswith("\n") and "\r" not in text, "CASE_LEDGER_NEWLINES")
    require(all(line != "" for line in text.splitlines()), "CASE_LEDGER_BLANK_LINE")
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    require(tuple(reader.fieldnames or ()) == CASE_FIELDS, "CASE_LEDGER_HEADER")
    rows: list[CaseRow] = []
    for line_number, row in enumerate(reader, 2):
        require(None not in row, f"CASE_EXTRA_COLUMNS:{line_number}")
        exact_keys(row, CASE_FIELDS, f"CASE_ROW:{line_number}")
        require(all(isinstance(value, str) for value in row.values()), f"CASE_STRING:{line_number}")
        try:
            latency = float(row["latency_ms"])
            response_bytes = int(row["response_bytes"])
        except ValueError as error:
            raise VerificationFailure(f"CASE_NUMERIC:{line_number}:{error}") from error
        require(math.isfinite(latency) and latency >= 0, f"CASE_LATENCY:{line_number}")
        require(response_bytes >= 0 and str(response_bytes) == row["response_bytes"], f"CASE_BYTES:{line_number}")
        require(re.fullmatch(r"[0-9a-f]{64}", row["response_sha256"]) is not None, f"CASE_SHA:{line_number}")
        require(row["expected_status"] == row["actual_status"], f"CASE_STATUS:{line_number}")
        require(row["outcome"] == "PASS" and row["error"] == "NONE", f"CASE_OUTCOME:{line_number}")
        rows.append(
            CaseRow(
                case_id=row["case_id"],
                phase=row["phase"],
                method=row["method"],
                path=row["path"],
                expected_status=row["expected_status"],
                actual_status=row["actual_status"],
                outcome=row["outcome"],
                latency_ms=latency,
                response_bytes=response_bytes,
                response_sha256=row["response_sha256"],
                error=row["error"],
            )
        )
    identifiers = [row.case_id for row in rows]
    require(len(rows) == TOTAL_CASE_COUNT, "CASE_COUNT")
    require(len(set(identifiers)) == TOTAL_CASE_COUNT, "CASE_ID_DUPLICATE")
    require(identifiers == sorted(identifiers), "CASE_LEDGER_SORT_ORDER")
    require(set(identifiers) == expected_case_ids(), "CASE_ID_UNIVERSE")
    require(Counter(row.phase for row in rows) == Counter(PHASE_COUNTS), "CASE_PHASE_DISTRIBUTION")
    return rows


def validate_case_semantics(rows: Sequence[CaseRow]) -> dict[str, list[CaseRow]]:
    by_phase: dict[str, list[CaseRow]] = defaultdict(list)
    for row in rows:
        by_phase[row.phase].append(row)
    artifact = by_phase["ARTIFACT_CHECK"]
    require(
        artifact
        == [
            CaseRow(
                "A001",
                "ARTIFACT_CHECK",
                "FILE",
                "frontend/generated/trace-exploration-v3/CHECKSUMS.sha256",
                "SHA256_BOUND",
                "SHA256_BOUND",
                "PASS",
                0.0,
                EXPECTED_READ_MODEL_BYTES,
                EXPECTED_READ_MODEL_SHA256,
                "NONE",
            )
        ],
        "ARTIFACT_CASE",
    )
    functional = by_phase["FUNCTIONAL_HTTP"]
    require(
        Counter((row.method, row.expected_status) for row in functional)
        == Counter(EXPECTED_FUNCTIONAL_METHOD_STATUS_COUNTS),
        "FUNCTIONAL_METHOD_STATUS_DISTRIBUTION",
    )
    require(all(row.path.startswith(API_BASE) for row in functional), "FUNCTIONAL_PATH_BOUNDARY")
    require(
        all(row.response_bytes == 0 for row in functional if row.method == "HEAD"),
        "FUNCTIONAL_HEAD_BODY",
    )
    require(
        all(
            row.response_sha256 == hashlib.sha256(b"").hexdigest()
            for row in functional
            if row.method == "HEAD"
        ),
        "FUNCTIONAL_HEAD_SHA",
    )

    stable_functional = {
        row.path: (row.response_bytes, row.response_sha256)
        for row in functional
        if row.method == "GET" and row.actual_status == "200" and row.path in EXPECTED_LOAD_PATHS
    }
    require(set(stable_functional) == EXPECTED_LOAD_PATHS, "FUNCTIONAL_STABLE_PATH_UNIVERSE")
    load_phases = {f"CONCURRENCY_C{level}" for level in CONCURRENCY_LEVELS} | {"SUSTAINED_READ"}
    for phase in sorted(load_phases):
        phase_rows = by_phase[phase]
        require(all(row.method == "GET" and row.actual_status == "200" for row in phase_rows), f"{phase}:HTTP")
        require(set(row.path for row in phase_rows) == EXPECTED_LOAD_PATHS, f"{phase}:PATHS")
        require(
            all((row.response_bytes, row.response_sha256) == stable_functional[row.path] for row in phase_rows),
            f"{phase}:STABLE_BYTES",
        )

    for phase, count in (
        ("CONTROL_EXPORT_REPLAY_PRELOAD", 5),
        ("CONTROL_EXPORT_REPLAY_POSTLOAD", 2),
    ):
        phase_rows = by_phase[phase]
        require(len(phase_rows) == count, f"{phase}:COUNT")
        for row in phase_rows:
            require(row.method == "GET", f"{phase}:METHOD")
            require(row.path == f"{API_BASE}/controls/exports", f"{phase}:PATH")
            require(row.actual_status == "200", f"{phase}:STATUS")
            require(row.response_bytes == EXPECTED_EXPORT_RESPONSE_BYTES, f"{phase}:BYTES")
            require(row.response_sha256 == EXPECTED_EXPORT_RESPONSE_SHA256, f"{phase}:SHA")
    return by_phase


def validate_summary(summary: Mapping[str, Any], output_dir: Path) -> dict[str, str]:
    exact_keys(
        summary,
        (
            "schema_version",
            "status",
            "mode",
            "started_utc",
            "completed_utc",
            "api_version",
            "loopback_only",
            "external_network_used",
            "port",
            "read_model_sha256",
            "case_count",
            "case_pass_count",
            "case_failure_count",
            "errors",
            "server_termination",
            "performance_interpretation",
            "artifact_sha256",
        ),
        "SUMMARY",
    )
    require(
        summary["schema_version"] == "trace-exploration-v3-production-http-verification-summary-v1",
        "SUMMARY_SCHEMA",
    )
    require(summary["status"] == "PASS" and summary["mode"] == "PRODUCTION_HTTP", "SUMMARY_STATUS")
    require(summary["api_version"] == API_VERSION, "SUMMARY_API")
    require(summary["loopback_only"] is True and summary["external_network_used"] is False, "SUMMARY_NETWORK")
    require(is_int(summary["port"]) and 1024 <= summary["port"] <= 65535 and summary["port"] != 3000, "SUMMARY_PORT")
    require(summary["read_model_sha256"] == EXPECTED_READ_MODEL_SHA256, "SUMMARY_READ_MODEL")
    require(
        (summary["case_count"], summary["case_pass_count"], summary["case_failure_count"])
        == (TOTAL_CASE_COUNT, TOTAL_CASE_COUNT, 0),
        "SUMMARY_COUNTS",
    )
    require(summary["errors"] == [], "SUMMARY_ERRORS")
    require(summary["performance_interpretation"] == PERFORMANCE_INTERPRETATION, "SUMMARY_PERFORMANCE_LABEL")
    started = parse_utc(summary["started_utc"], "SUMMARY_STARTED")
    completed = parse_utc(summary["completed_utc"], "SUMMARY_COMPLETED")
    require(completed >= started, "SUMMARY_TIME_ORDER")
    termination = summary["server_termination"]
    require(isinstance(termination, dict), "SUMMARY_TERMINATION_OBJECT")
    exact_keys(
        termination,
        ("termination_requested", "terminated", "return_code", "sigkill_used", "process_group_residual"),
        "SUMMARY_TERMINATION",
    )
    require(termination["termination_requested"] is True, "SUMMARY_TERMINATION_REQUESTED")
    require(termination["terminated"] is True, "SUMMARY_TERMINATED")
    require(termination["process_group_residual"] is False, "SUMMARY_GROUP_RESIDUAL")
    require(isinstance(termination["sigkill_used"], bool), "SUMMARY_SIGKILL_TYPE")
    require(is_int(termination["return_code"]), "SUMMARY_RETURN_CODE")
    hashes = summary["artifact_sha256"]
    require(isinstance(hashes, dict), "SUMMARY_ARTIFACT_HASH_OBJECT")
    exact_keys(hashes, SUMMARY_HASHED_ARTIFACTS, "SUMMARY_ARTIFACT_HASH")
    actual: dict[str, str] = {}
    for name in SUMMARY_HASHED_ARTIFACTS:
        require(isinstance(hashes[name], str) and re.fullmatch(r"[0-9a-f]{64}", hashes[name]) is not None, f"SUMMARY_HASH_FORMAT:{name}")
        actual[name] = sha256_file(output_dir / name)
        require(actual[name] == hashes[name], f"SUMMARY_HASH_MISMATCH:{name}")
    return actual


def validate_artifact_receipt(
    receipt: Mapping[str, Any],
    repo: Path,
    model: Mapping[str, Any],
    governed_hashes: Mapping[str, str],
) -> None:
    exact_keys(
        receipt,
        (
            "schema_version",
            "status",
            "mode",
            "checked_utc",
            "api_version",
            "manifest_path",
            "manifest_sha256",
            "read_model_path",
            "read_model_sha256",
            "read_model_bytes",
            "checksum_ledger_path",
            "checksum_ledger_sha256",
            "active_product_counts",
            "research_control_counts",
            "closure_flags",
            "production_activation_count",
            "research_controls_only",
            "transition_status",
        ),
        "ARTIFACT_RECEIPT",
    )
    require(receipt["schema_version"] == "trace-exploration-v3-production-artifact-check-v1", "ARTIFACT_SCHEMA")
    require(receipt["status"] == "PASS" and receipt["mode"] == "PRODUCTION_HTTP", "ARTIFACT_STATUS")
    parse_utc(receipt["checked_utc"], "ARTIFACT_CHECKED")
    require(receipt["api_version"] == API_VERSION, "ARTIFACT_API")
    require(receipt["manifest_path"] == "frontend/generated/trace-exploration-v3/manifest.json", "ARTIFACT_MANIFEST_PATH")
    require(receipt["read_model_path"] == "frontend/generated/trace-exploration-v3/read-model.json", "ARTIFACT_MODEL_PATH")
    require(receipt["checksum_ledger_path"] == "frontend/generated/trace-exploration-v3/CHECKSUMS.sha256", "ARTIFACT_CHECKSUM_PATH")
    require(receipt["manifest_sha256"] == governed_hashes["manifest.json"], "ARTIFACT_MANIFEST_SHA")
    require(receipt["read_model_sha256"] == governed_hashes["read-model.json"], "ARTIFACT_MODEL_SHA")
    require(receipt["checksum_ledger_sha256"] == governed_hashes["CHECKSUMS.sha256"], "ARTIFACT_CHECKSUM_SHA")
    require(receipt["read_model_bytes"] == EXPECTED_READ_MODEL_BYTES, "ARTIFACT_MODEL_BYTES")
    expected_active = {key: len(model["active_product"][key]) for key in SURFACE_KEYS}
    expected_controls = {key: len(model["research_controls"][key]) for key in SURFACE_KEYS}
    require(receipt["active_product_counts"] == expected_active, "ARTIFACT_ACTIVE_COUNTS")
    require(receipt["research_control_counts"] == expected_controls, "ARTIFACT_CONTROL_COUNTS")
    require(receipt["closure_flags"] == EXPECTED_CLOSURE_FLAGS, "ARTIFACT_CLOSURE")
    require(receipt["production_activation_count"] == 0, "ARTIFACT_ACTIVATION")
    require(receipt["research_controls_only"] is True, "ARTIFACT_CONTROL_BOUNDARY")
    require(
        receipt["transition_status"] == "FAIL_CLOSED_NO_ACTIVE_PRODUCT_STATE_GRAPH",
        "ARTIFACT_TRANSITION_STATUS",
    )
    require((repo / receipt["read_model_path"]).is_file(), "ARTIFACT_REPO_BINDING")


def validate_functional_receipt(
    receipt: Mapping[str, Any],
    model: Mapping[str, Any],
) -> None:
    exact_keys(
        receipt,
        (
            "schema_version",
            "status",
            "checked_utc",
            "api_base",
            "allowed_methods",
            "root_redirect_status",
            "root_redirect_location",
            "unknown_route_status",
            "case_count",
            "pass_count",
            "failure_count",
            "active_empty_collection_count",
            "control_collection_count",
            "representative_control_ids",
            "read_model_sha256",
            "performance_interpretation",
        ),
        "FUNCTIONAL_RECEIPT",
    )
    require(receipt["schema_version"] == "trace-exploration-v3-functional-http-receipt-v1", "FUNCTIONAL_SCHEMA")
    require(receipt["status"] == "PASS", "FUNCTIONAL_STATUS")
    parse_utc(receipt["checked_utc"], "FUNCTIONAL_CHECKED")
    require(receipt["api_base"] == API_BASE, "FUNCTIONAL_BASE")
    require(receipt["allowed_methods"] == "GET, HEAD, OPTIONS", "FUNCTIONAL_METHODS")
    require((receipt["root_redirect_status"], receipt["root_redirect_location"]) == (308, f"{API_BASE}/capabilities"), "FUNCTIONAL_REDIRECT")
    require(receipt["unknown_route_status"] == 404, "FUNCTIONAL_UNKNOWN_ROUTE")
    require((receipt["case_count"], receipt["pass_count"], receipt["failure_count"]) == (160, 160, 0), "FUNCTIONAL_COUNTS")
    require((receipt["active_empty_collection_count"], receipt["control_collection_count"]) == (12, 12), "FUNCTIONAL_COLLECTION_COUNTS")
    require(receipt["read_model_sha256"] == EXPECTED_READ_MODEL_SHA256, "FUNCTIONAL_MODEL_SHA")
    require(receipt["performance_interpretation"] == PERFORMANCE_INTERPRETATION, "FUNCTIONAL_PERFORMANCE_LABEL")
    representatives = {
        slug: model["research_controls"][surface][0][identity]
        for slug, surface, identity in SURFACE_SPECS
        if model["research_controls"][surface]
    }
    require(receipt["representative_control_ids"] == representatives, "FUNCTIONAL_REPRESENTATIVES")


def percentile(values: Sequence[float], quantile: float) -> float:
    ordered = sorted(values)
    require(bool(ordered), "PERCENTILE_EMPTY")
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def validate_latency_summary(value: Any, rows: Sequence[CaseRow], code: str) -> None:
    require(isinstance(value, dict), f"{code}:OBJECT")
    exact_keys(value, ("minimum", "p50", "p95", "p99", "maximum"), code)
    observed = {
        "minimum": min(row.latency_ms for row in rows),
        "p50": percentile([row.latency_ms for row in rows], 0.50),
        "p95": percentile([row.latency_ms for row in rows], 0.95),
        "p99": percentile([row.latency_ms for row in rows], 0.99),
        "maximum": max(row.latency_ms for row in rows),
    }
    values: dict[str, float] = {}
    for key in observed:
        values[key] = finite_number(value[key], f"{code}:{key}", minimum=0)
        require(math.isclose(values[key], observed[key], rel_tol=0, abs_tol=0.001), f"{code}:{key}:CASE_MISMATCH")
    require(values["minimum"] <= values["p50"] <= values["p95"] <= values["p99"] <= values["maximum"], f"{code}:ORDER")


def validate_concurrency_receipt(receipt: Mapping[str, Any], by_phase: Mapping[str, Sequence[CaseRow]]) -> None:
    exact_keys(
        receipt,
        (
            "schema_version",
            "status",
            "checked_utc",
            "concurrency_levels",
            "requests_per_level",
            "failure_count",
            "workloads",
            "performance_interpretation",
        ),
        "CONCURRENCY_RECEIPT",
    )
    require(receipt["schema_version"] == "trace-exploration-v3-concurrency-receipt-v1", "CONCURRENCY_SCHEMA")
    require(receipt["status"] == "PASS" and receipt["failure_count"] == 0, "CONCURRENCY_STATUS")
    parse_utc(receipt["checked_utc"], "CONCURRENCY_CHECKED")
    require(receipt["concurrency_levels"] == list(CONCURRENCY_LEVELS), "CONCURRENCY_LEVELS")
    require(receipt["requests_per_level"] == 100, "CONCURRENCY_REQUESTS_PER_LEVEL")
    require(receipt["performance_interpretation"] == PERFORMANCE_INTERPRETATION, "CONCURRENCY_PERFORMANCE_LABEL")
    workloads = receipt["workloads"]
    require(isinstance(workloads, list) and len(workloads) == len(CONCURRENCY_LEVELS), "CONCURRENCY_WORKLOADS")
    for expected_level, workload in zip(CONCURRENCY_LEVELS, workloads, strict=True):
        require(isinstance(workload, dict), f"CONCURRENCY_C{expected_level}:OBJECT")
        exact_keys(
            workload,
            (
                "concurrency",
                "status",
                "failure_count",
                "request_count",
                "duration_ms",
                "throughput_requests_per_second",
                "response_bytes",
                "latency_ms",
                "performance_interpretation",
            ),
            f"CONCURRENCY_C{expected_level}",
        )
        rows = by_phase[f"CONCURRENCY_C{expected_level}"]
        require(workload["concurrency"] == expected_level, f"CONCURRENCY_C{expected_level}:LEVEL")
        require(workload["status"] == "PASS" and workload["failure_count"] == 0, f"CONCURRENCY_C{expected_level}:STATUS")
        require(workload["request_count"] == len(rows) == 100, f"CONCURRENCY_C{expected_level}:COUNT")
        require(workload["response_bytes"] == sum(row.response_bytes for row in rows), f"CONCURRENCY_C{expected_level}:BYTES")
        duration = finite_number(workload["duration_ms"], f"CONCURRENCY_C{expected_level}:DURATION", minimum=0.000001)
        throughput = finite_number(workload["throughput_requests_per_second"], f"CONCURRENCY_C{expected_level}:THROUGHPUT", minimum=0)
        require(math.isclose(throughput, 100_000 / duration, rel_tol=1e-12, abs_tol=1e-9), f"CONCURRENCY_C{expected_level}:THROUGHPUT_BINDING")
        require(workload["performance_interpretation"] == PERFORMANCE_INTERPRETATION, f"CONCURRENCY_C{expected_level}:PERFORMANCE_LABEL")
        validate_latency_summary(workload["latency_ms"], rows, f"CONCURRENCY_C{expected_level}:LATENCY")


def validate_sustained_receipt(receipt: Mapping[str, Any], rows: Sequence[CaseRow]) -> None:
    exact_keys(
        receipt,
        (
            "schema_version",
            "status",
            "checked_utc",
            "concurrency",
            "planned_duration_seconds",
            "observed_duration_seconds",
            "duration_completion_ratio",
            "request_cap",
            "termination_reason",
            "failure_count",
            "request_count",
            "duration_ms",
            "throughput_requests_per_second",
            "response_bytes",
            "latency_ms",
            "performance_interpretation",
        ),
        "SUSTAINED_RECEIPT",
    )
    require(receipt["schema_version"] == "trace-exploration-v3-sustained-read-receipt-v1", "SUSTAINED_SCHEMA")
    require(receipt["status"] == "PASS" and receipt["failure_count"] == 0, "SUSTAINED_STATUS")
    parse_utc(receipt["checked_utc"], "SUSTAINED_CHECKED")
    require(receipt["concurrency"] == 10, "SUSTAINED_CONCURRENCY")
    planned = finite_number(receipt["planned_duration_seconds"], "SUSTAINED_PLANNED", minimum=2)
    observed = finite_number(receipt["observed_duration_seconds"], "SUSTAINED_OBSERVED", minimum=0.000001)
    ratio = finite_number(receipt["duration_completion_ratio"], "SUSTAINED_RATIO", minimum=0.8)
    duration_ms = finite_number(receipt["duration_ms"], "SUSTAINED_DURATION_MS", minimum=0.001)
    throughput = finite_number(receipt["throughput_requests_per_second"], "SUSTAINED_THROUGHPUT", minimum=0)
    require(math.isclose(planned, 10.0, rel_tol=0, abs_tol=0), "SUSTAINED_PLANNED_VALUE")
    require(math.isclose(ratio, observed / planned, rel_tol=1e-12, abs_tol=1e-12), "SUSTAINED_RATIO_BINDING")
    require(math.isclose(duration_ms, observed * 1000, rel_tol=1e-12, abs_tol=1e-9), "SUSTAINED_DURATION_BINDING")
    require(math.isclose(throughput, len(rows) / observed, rel_tol=1e-12, abs_tol=1e-9), "SUSTAINED_THROUGHPUT_BINDING")
    require(receipt["request_cap"] == receipt["request_count"] == len(rows) == 500, "SUSTAINED_COUNT")
    require(receipt["response_bytes"] == sum(row.response_bytes for row in rows), "SUSTAINED_BYTES")
    require(receipt["termination_reason"] == "REQUEST_CAP_AFTER_PACED_BOUNDED_DURATION", "SUSTAINED_TERMINATION_REASON")
    require(receipt["performance_interpretation"] == PERFORMANCE_INTERPRETATION, "SUSTAINED_PERFORMANCE_LABEL")
    validate_latency_summary(receipt["latency_ms"], rows, "SUSTAINED_LATENCY")


def validate_export_receipt(receipt: Mapping[str, Any], governed_export: Mapping[str, Any]) -> None:
    exact_keys(
        receipt,
        (
            "schema_version",
            "status",
            "checked_utc",
            "preload_replay",
            "postload_replay",
            "preload_and_postload_bytes_equal",
            "performance_interpretation",
        ),
        "EXPORT_RECEIPT",
    )
    require(receipt["schema_version"] == "trace-exploration-v3-control-export-replay-receipt-v1", "EXPORT_SCHEMA")
    require(receipt["status"] == "PASS" and receipt["preload_and_postload_bytes_equal"] is True, "EXPORT_STATUS")
    parse_utc(receipt["checked_utc"], "EXPORT_CHECKED")
    require(receipt["performance_interpretation"] == PERFORMANCE_INTERPRETATION, "EXPORT_PERFORMANCE_LABEL")
    expected_id = governed_export["export_id"]
    for key, replay_count in (("preload_replay", 5), ("postload_replay", 2)):
        replay = receipt[key]
        require(isinstance(replay, dict), f"EXPORT_{key}:OBJECT")
        exact_keys(
            replay,
            (
                "export_id",
                "semantic_sha256",
                "presentation_sha256",
                "pair_projection_policy_preserved",
                "projection_preservation_record_count",
                "replay_count",
                "response_bytes",
                "response_sha256",
            ),
            f"EXPORT_{key}",
        )
        require(replay["export_id"] == expected_id, f"EXPORT_{key}:ID")
        require(replay["semantic_sha256"] == EXPECTED_EXPORT_SEMANTIC_SHA256, f"EXPORT_{key}:SEMANTIC")
        require(replay["presentation_sha256"] == EXPECTED_EXPORT_PRESENTATION_SHA256, f"EXPORT_{key}:PRESENTATION")
        require(replay["pair_projection_policy_preserved"] is True, f"EXPORT_{key}:PAIR_POLICY")
        require(replay["projection_preservation_record_count"] == EXPECTED_EXPORT_PROJECTION_RECORD_COUNT, f"EXPORT_{key}:PROJECTION_COUNT")
        require(replay["replay_count"] == replay_count, f"EXPORT_{key}:REPLAY_COUNT")
        require(replay["response_bytes"] == EXPECTED_EXPORT_RESPONSE_BYTES, f"EXPORT_{key}:BYTES")
        require(replay["response_sha256"] == EXPECTED_EXPORT_RESPONSE_SHA256, f"EXPORT_{key}:RESPONSE_SHA")
    require(receipt["preload_replay"]["response_sha256"] == receipt["postload_replay"]["response_sha256"], "EXPORT_PRE_POST_SHA")


PROBE_KEYS = (
    "timestamp_utc",
    "probe_session_id",
    "probe_sequence",
    "process_role",
    "phase",
    "pid",
    "ppid",
    "process_uptime_ms",
    "cpu_percent_interval",
    "cpu_user_micros_total",
    "cpu_system_micros_total",
    "rss_bytes",
    "heap_used_bytes",
    "heap_total_bytes",
    "external_bytes",
    "event_loop_delay_mean_ms",
    "event_loop_delay_p95_ms",
    "event_loop_delay_p99_ms",
    "event_loop_delay_max_ms",
)
PROBE_METRICS = (
    "process_uptime_ms",
    "cpu_percent_interval",
    "cpu_user_micros_total",
    "cpu_system_micros_total",
    "rss_bytes",
    "heap_used_bytes",
    "heap_total_bytes",
    "external_bytes",
    "event_loop_delay_mean_ms",
    "event_loop_delay_p95_ms",
    "event_loop_delay_p99_ms",
    "event_loop_delay_max_ms",
)


def read_runtime_probe(path: Path, session_id: str) -> list[dict[str, Any]]:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise VerificationFailure(f"RUNTIME_PROBE_UTF8:{error}") from error
    require(text.endswith("\n") and "\r" not in text, "RUNTIME_PROBE_NEWLINES")
    lines = text.splitlines()
    require(lines and all(lines), "RUNTIME_PROBE_EMPTY_OR_BLANK")
    rows: list[dict[str, Any]] = []
    last_sequence: dict[int, int] = {}
    last_timestamp: dict[int, dt.datetime] = {}
    for line_number, line in enumerate(lines, 1):
        row = parse_json_bytes(line.encode("utf-8"), f"RUNTIME_PROBE:{line_number}")
        exact_keys(row, PROBE_KEYS, f"RUNTIME_PROBE:{line_number}")
        require(row["probe_session_id"] == session_id, f"RUNTIME_PROBE:{line_number}:SESSION")
        require(row["process_role"] == "NEXT_PRODUCTION_SERVER_V3_VERIFIER", f"RUNTIME_PROBE:{line_number}:ROLE")
        require(row["phase"] in {"START", "SAMPLE", "EXIT"}, f"RUNTIME_PROBE:{line_number}:PHASE")
        require(is_int(row["pid"]) and row["pid"] > 0, f"RUNTIME_PROBE:{line_number}:PID")
        require(is_int(row["ppid"]) and row["ppid"] > 0, f"RUNTIME_PROBE:{line_number}:PPID")
        require(is_int(row["probe_sequence"]) and row["probe_sequence"] > 0, f"RUNTIME_PROBE:{line_number}:SEQUENCE")
        pid = row["pid"]
        require(row["probe_sequence"] == last_sequence.get(pid, 0) + 1, f"RUNTIME_PROBE:{line_number}:SEQUENCE_ORDER")
        last_sequence[pid] = row["probe_sequence"]
        timestamp = parse_utc(row["timestamp_utc"], f"RUNTIME_PROBE:{line_number}:TIME")
        require(timestamp >= last_timestamp.get(pid, timestamp), f"RUNTIME_PROBE:{line_number}:TIME_ORDER")
        last_timestamp[pid] = timestamp
        for metric in PROBE_METRICS:
            finite_number(row[metric], f"RUNTIME_PROBE:{line_number}:{metric}", minimum=0)
        rows.append(row)
    return rows


def validate_runtime_receipt(
    receipt: Mapping[str, Any],
    probe_rows: Sequence[Mapping[str, Any]],
    startup: Mapping[str, Any],
    summary: Mapping[str, Any],
) -> None:
    exact_keys(
        receipt,
        (
            "schema_version",
            "status",
            "checked_utc",
            "probe_session_id",
            "probe_row_count",
            "probe_phase_counts",
            "process_count",
            "process_ids",
            "peak_rss_bytes",
            "peak_heap_used_bytes",
            "peak_heap_total_bytes",
            "peak_external_bytes",
            "peak_cpu_percent_interval",
            "peak_event_loop_delay_mean_ms",
            "peak_event_loop_delay_p95_ms",
            "peak_event_loop_delay_p99_ms",
            "peak_event_loop_delay_max_ms",
            "process_summaries",
            "termination",
            "performance_interpretation",
        ),
        "RUNTIME_RECEIPT",
    )
    require(receipt["schema_version"] == "trace-exploration-v3-runtime-memory-receipt-v1", "RUNTIME_SCHEMA")
    require(receipt["status"] == "PASS", "RUNTIME_STATUS")
    parse_utc(receipt["checked_utc"], "RUNTIME_CHECKED")
    require(receipt["probe_session_id"] == startup["probe_session_id"], "RUNTIME_SESSION")
    require(receipt["probe_row_count"] == len(probe_rows), "RUNTIME_ROW_COUNT")
    phase_counts = Counter(row["phase"] for row in probe_rows)
    require(receipt["probe_phase_counts"] == dict(phase_counts), "RUNTIME_PHASE_COUNTS")
    process_ids = sorted({row["pid"] for row in probe_rows})
    require(receipt["process_ids"] == process_ids, "RUNTIME_PROCESS_IDS")
    require(receipt["process_count"] == len(process_ids) >= 1, "RUNTIME_PROCESS_COUNT")
    require(startup["server_pid"] in process_ids, "RUNTIME_SERVER_PID_COVERAGE")
    require(phase_counts == Counter({"START": len(process_ids), "EXIT": len(process_ids), "SAMPLE": len(probe_rows) - 2 * len(process_ids)}), "RUNTIME_PHASE_LIFECYCLE")
    require(phase_counts["SAMPLE"] >= 1, "RUNTIME_SAMPLE_REQUIRED")

    global_fields = {
        "peak_rss_bytes": "rss_bytes",
        "peak_heap_used_bytes": "heap_used_bytes",
        "peak_heap_total_bytes": "heap_total_bytes",
        "peak_external_bytes": "external_bytes",
        "peak_cpu_percent_interval": "cpu_percent_interval",
        "peak_event_loop_delay_mean_ms": "event_loop_delay_mean_ms",
        "peak_event_loop_delay_p95_ms": "event_loop_delay_p95_ms",
        "peak_event_loop_delay_p99_ms": "event_loop_delay_p99_ms",
        "peak_event_loop_delay_max_ms": "event_loop_delay_max_ms",
    }
    for receipt_key, probe_key in global_fields.items():
        require(receipt[receipt_key] == max(row[probe_key] for row in probe_rows), f"RUNTIME_PEAK:{receipt_key}")

    summaries = receipt["process_summaries"]
    require(isinstance(summaries, list) and len(summaries) == len(process_ids), "RUNTIME_PROCESS_SUMMARIES")
    require([item.get("pid") for item in summaries if isinstance(item, dict)] == process_ids, "RUNTIME_SUMMARY_ORDER")
    for process_summary in summaries:
        require(isinstance(process_summary, dict), "RUNTIME_PROCESS_SUMMARY_OBJECT")
        exact_keys(
            process_summary,
            (
                "pid",
                "sample_count",
                "first_phase",
                "last_phase",
                "first_rss_bytes",
                "last_rss_bytes",
                "observed_rss_change_bytes",
                "peak_rss_bytes",
                "peak_heap_used_bytes",
                "peak_heap_total_bytes",
                "peak_event_loop_delay_ms",
            ),
            "RUNTIME_PROCESS_SUMMARY",
        )
        rows = [row for row in probe_rows if row["pid"] == process_summary["pid"]]
        require(process_summary["sample_count"] == len(rows), "RUNTIME_PROCESS_SAMPLE_COUNT")
        require((process_summary["first_phase"], process_summary["last_phase"]) == ("START", "EXIT"), "RUNTIME_PROCESS_PHASE_BOUNDARY")
        require(process_summary["first_rss_bytes"] == rows[0]["rss_bytes"], "RUNTIME_PROCESS_FIRST_RSS")
        require(process_summary["last_rss_bytes"] == rows[-1]["rss_bytes"], "RUNTIME_PROCESS_LAST_RSS")
        require(process_summary["observed_rss_change_bytes"] == rows[-1]["rss_bytes"] - rows[0]["rss_bytes"], "RUNTIME_PROCESS_RSS_CHANGE")
        require(process_summary["peak_rss_bytes"] == max(row["rss_bytes"] for row in rows), "RUNTIME_PROCESS_PEAK_RSS")
        require(process_summary["peak_heap_used_bytes"] == max(row["heap_used_bytes"] for row in rows), "RUNTIME_PROCESS_PEAK_HEAP_USED")
        require(process_summary["peak_heap_total_bytes"] == max(row["heap_total_bytes"] for row in rows), "RUNTIME_PROCESS_PEAK_HEAP_TOTAL")
        require(process_summary["peak_event_loop_delay_ms"] == max(row["event_loop_delay_max_ms"] for row in rows), "RUNTIME_PROCESS_PEAK_EVENT_LOOP")
    require(receipt["termination"] == summary["server_termination"], "RUNTIME_TERMINATION_BINDING")
    require(receipt["performance_interpretation"] == PERFORMANCE_INTERPRETATION, "RUNTIME_PERFORMANCE_LABEL")


def validate_startup(startup: Mapping[str, Any], summary: Mapping[str, Any], server_output: str) -> None:
    exact_keys(
        startup,
        (
            "schema_version",
            "status",
            "started_utc",
            "ready_utc",
            "api_version",
            "read_model_sha256",
            "build_id",
            "command",
            "host",
            "next_version",
            "preload_entries_on_start",
            "port",
            "process_group_id",
            "server_pid",
            "probe_module",
            "probe_path",
            "probe_session_id",
            "server_log_path",
            "attempt_count",
            "cold_start_ms",
            "first_response_bytes",
            "first_response_sha256",
            "first_successful_request_ms",
            "readiness_path",
            "recent_attempt_statuses",
        ),
        "STARTUP",
    )
    require(startup["schema_version"] == "trace-exploration-v3-production-startup-receipt-v1", "STARTUP_SCHEMA")
    require(startup["status"] == "READY", "STARTUP_STATUS")
    started = parse_utc(startup["started_utc"], "STARTUP_STARTED")
    ready = parse_utc(startup["ready_utc"], "STARTUP_READY")
    require(ready >= started, "STARTUP_TIME_ORDER")
    require(startup["api_version"] == API_VERSION, "STARTUP_API")
    require(startup["read_model_sha256"] == EXPECTED_READ_MODEL_SHA256, "STARTUP_MODEL_SHA")
    require(isinstance(startup["build_id"], str) and startup["build_id"].strip() == startup["build_id"] and startup["build_id"], "STARTUP_BUILD_ID")
    require(startup["host"] == "127.0.0.1" and startup["port"] == summary["port"], "STARTUP_ENDPOINT")
    require(isinstance(startup["next_version"], str) and startup["next_version"].startswith("15."), "STARTUP_NEXT_VERSION")
    require(startup["preload_entries_on_start"] is False, "STARTUP_PRELOAD")
    require(is_int(startup["server_pid"]) and startup["server_pid"] > 0, "STARTUP_PID")
    require(startup["process_group_id"] == startup["server_pid"], "STARTUP_PROCESS_GROUP")
    require(startup["probe_module"] == "scripts/trace_round16a/node_runtime_probe.cjs", "STARTUP_PROBE_MODULE")
    require(startup["probe_path"] == "runtime-probe.jsonl", "STARTUP_PROBE_PATH")
    require(startup["server_log_path"] == "server-output.txt", "STARTUP_LOG_PATH")
    require(startup["readiness_path"] == f"{API_BASE}/capabilities", "STARTUP_READINESS_PATH")
    try:
        session = uuid.UUID(startup["probe_session_id"])
    except (AttributeError, ValueError) as error:
        raise VerificationFailure(f"STARTUP_SESSION_UUID:{error}") from error
    require(session.version == 4, "STARTUP_SESSION_UUID_VERSION")
    command = startup["command"]
    require(isinstance(command, list) and len(command) == 7 and all(isinstance(item, str) for item in command), "STARTUP_COMMAND")
    require(Path(command[0]).name == "node", "STARTUP_COMMAND_NODE")
    require(command[1].endswith("/node_modules/next/dist/bin/next"), "STARTUP_COMMAND_NEXT")
    require(command[2:] == ["start", "--hostname", "127.0.0.1", "--port", str(summary["port"])], "STARTUP_COMMAND_ARGUMENTS")
    require(is_int(startup["attempt_count"]) and startup["attempt_count"] >= 1, "STARTUP_ATTEMPTS")
    recent = startup["recent_attempt_statuses"]
    require(isinstance(recent, list) and recent and len(recent) <= startup["attempt_count"], "STARTUP_RECENT_ATTEMPTS")
    require(all(isinstance(item, str) and item for item in recent) and recent[-1] == "200", "STARTUP_RECENT_STATUS")
    finite_number(startup["cold_start_ms"], "STARTUP_COLD_START", minimum=0)
    finite_number(startup["first_successful_request_ms"], "STARTUP_FIRST_REQUEST", minimum=0)
    require(startup["first_response_bytes"] == EXPECTED_CAPABILITIES_RESPONSE_BYTES, "STARTUP_FIRST_RESPONSE_BYTES")
    require(startup["first_response_sha256"] == EXPECTED_CAPABILITIES_RESPONSE_SHA256, "STARTUP_FIRST_RESPONSE_SHA")
    require("Next.js 15." in server_output, "SERVER_OUTPUT_NEXT_VERSION")
    require(f"http://127.0.0.1:{summary['port']}" in server_output, "SERVER_OUTPUT_LOOPBACK")
    require("Ready" in server_output, "SERVER_OUTPUT_READY")


def verify(repo: Path, output_dir: Path) -> dict[str, Any]:
    require(repo.is_dir(), "REPO_NOT_DIRECTORY")
    require(output_dir.is_dir() and not output_dir.is_symlink(), "OUTPUT_DIRECTORY_INVALID")
    entries = list(output_dir.iterdir())
    require(all(path.is_file() and not path.is_symlink() for path in entries), "OUTPUT_NONREGULAR_ENTRY")
    require({path.name for path in entries} == OUTPUT_ARTIFACTS, "OUTPUT_FILE_UNIVERSE")

    model, _manifest, governed_hashes = read_governed_model(repo)
    cases = read_cases(output_dir / "http-cases.tsv")
    by_phase = validate_case_semantics(cases)

    summary = read_receipt(output_dir / "verification-summary.json", "SUMMARY")
    hashed_artifacts = validate_summary(summary, output_dir)
    artifact = read_receipt(output_dir / "artifact-check-receipt.json", "ARTIFACT_RECEIPT")
    functional = read_receipt(output_dir / "functional-http-receipt.json", "FUNCTIONAL_RECEIPT")
    concurrency = read_receipt(output_dir / "concurrency-receipt.json", "CONCURRENCY_RECEIPT")
    sustained = read_receipt(output_dir / "sustained-read-receipt.json", "SUSTAINED_RECEIPT")
    export = read_receipt(output_dir / "control-export-replay-receipt.json", "EXPORT_RECEIPT")
    startup = read_receipt(output_dir / "startup-receipt.json", "STARTUP_RECEIPT")
    runtime = read_receipt(output_dir / "runtime-memory-receipt.json", "RUNTIME_RECEIPT")

    validate_artifact_receipt(artifact, repo, model, governed_hashes)
    validate_functional_receipt(functional, model)
    validate_concurrency_receipt(concurrency, by_phase)
    validate_sustained_receipt(sustained, by_phase["SUSTAINED_READ"])
    validate_export_receipt(export, model["research_controls"]["exports"][0])
    try:
        server_output = (output_dir / "server-output.txt").read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise VerificationFailure(f"SERVER_OUTPUT_UTF8:{error}") from error
    require(server_output and "\x00" not in server_output, "SERVER_OUTPUT_INVALID")
    validate_startup(startup, summary, server_output)
    probe_rows = read_runtime_probe(output_dir / "runtime-probe.jsonl", startup["probe_session_id"])
    validate_runtime_receipt(runtime, probe_rows, startup, summary)

    all_artifact_hashes = {
        **hashed_artifacts,
        "verification-summary.json": sha256_file(output_dir / "verification-summary.json"),
    }
    return {
        "receipt_version": VERIFIER_VERSION,
        "status": "PASS",
        "output_directory_name": output_dir.name,
        "api_version": API_VERSION,
        "governed_artifact_sha256": governed_hashes,
        "case_count": len(cases),
        "case_pass_count": len(cases),
        "case_failure_count": 0,
        "phase_counts": dict(sorted(PHASE_COUNTS.items())),
        "functional_case_count": len(by_phase["FUNCTIONAL_HTTP"]),
        "concurrency_case_count": sum(len(by_phase[f"CONCURRENCY_C{level}"]) for level in CONCURRENCY_LEVELS),
        "sustained_case_count": len(by_phase["SUSTAINED_READ"]),
        "export_case_count": len(by_phase["CONTROL_EXPORT_REPLAY_PRELOAD"])
        + len(by_phase["CONTROL_EXPORT_REPLAY_POSTLOAD"]),
        "stable_export": {
            "semantic_sha256": EXPECTED_EXPORT_SEMANTIC_SHA256,
            "presentation_sha256": EXPECTED_EXPORT_PRESENTATION_SHA256,
            "response_sha256": EXPECTED_EXPORT_RESPONSE_SHA256,
            "response_bytes": EXPECTED_EXPORT_RESPONSE_BYTES,
            "projection_preservation_record_count": EXPECTED_EXPORT_PROJECTION_RECORD_COUNT,
        },
        "runtime_validation": {
            "process_count": runtime["process_count"],
            "probe_row_count": runtime["probe_row_count"],
            "sample_count": runtime["probe_phase_counts"]["SAMPLE"],
            "terminated": runtime["termination"]["terminated"],
            "process_group_residual": runtime["termination"]["process_group_residual"],
            "performance_interpretation": PERFORMANCE_INTERPRETATION,
        },
        "run_identity_observed_not_pinned": {
            "port": summary["port"],
            "build_id": startup["build_id"],
            "server_pid": startup["server_pid"],
            "process_group_id": startup["process_group_id"],
            "probe_session_id": startup["probe_session_id"],
            "started_utc": summary["started_utc"],
            "completed_utc": summary["completed_utc"],
        },
        "source_artifact_sha256": dict(sorted(all_artifact_hashes.items())),
    }


def receipt_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    repo = args.repo.resolve()
    output_dir = resolve_from_repo(repo, args.output_dir)
    output = resolve_from_repo(repo, args.output)
    try:
        require(not path_is_within(output, output_dir), "OUTPUT_RECEIPT_INSIDE_SOURCE_DIRECTORY")
        require(not output.is_dir() and not output.is_symlink(), "OUTPUT_RECEIPT_TARGET_INVALID")
        receipt = verify(repo, output_dir)
        encoded = receipt_bytes(receipt)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(encoded)
    except (OSError, VerificationFailure) as error:
        print(f"FAIL {VERIFIER_VERSION} {type(error).__name__}:{error}", file=sys.stderr)
        return 1
    print(
        f"PASS {VERIFIER_VERSION} cases={receipt['case_count']} "
        f"output={output} sha256={sha256_bytes(encoded)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
