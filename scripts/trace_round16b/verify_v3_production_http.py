#!/usr/bin/env python3
"""Verify the governed TRACE Exploration v3 API over a built Next server.

The verifier is deliberately self-contained and uses only the Python standard
library. It launches one task-owned production server on an explicitly supplied
loopback port, exercises the read-only v3 HTTP contract, records bounded load
observations, and always terminates the process group it created.

Latency, throughput, CPU, memory, and event-loop values are observations from
the invoking environment. They are not production SLOs or capacity claims.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime as dt
from dataclasses import dataclass
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from typing import Any, Callable, Iterable, Mapping, Sequence
from urllib.parse import quote
import uuid


API_BASE = "/api/trace/v3/exploration"
API_VERSION = "trace-exploration/v3"
LOOPBACK_HOST = "127.0.0.1"
DEFAULT_NEXT_PORT = 3000
PERFORMANCE_INTERPRETATION = "OBSERVATIONAL_NO_SLO_OR_PRODUCTION_CAPACITY_CLAIM"
EXPECTED_READ_MODEL_SHA256 = "f1ae8a35895b27c15fb3d9b42828b8611633ee8ee7e2cbc825772b590304351b"
EXPECTED_MANIFEST_SHA256 = "2ee550028cb60749bee7efa456ed21ea4f0c6170bb5c68d8888017fc948fdd2c"
EXPECTED_CHECKSUMS_SHA256 = "002d13c9175354054ee550b4d55d275ea2fad1c10693991bd726897aa50e8173"
COMMON_HEADER_EXPECTATIONS = {
    "allow": "GET, HEAD, OPTIONS",
    "cache-control": "private, no-store",
    "x-content-type-options": "nosniff",
    "x-trace-api-version": API_VERSION,
    "x-trace-product-activation": "FAIL-CLOSED",
    "x-trace-transition-status": "FAIL-CLOSED-NO-ACTIVE-PRODUCT-STATE-GRAPH",
}
SURFACE_KEYS = (
    "association_realizations",
    "associations",
    "composition_coherence_reviews",
    "compositions",
    "concept_senses",
    "concepts",
    "exports",
    "incidences",
    "navigation_states",
    "scopes",
    "transitions",
    "workflows",
)
RECEIPT_NAMES = (
    "artifact-check-receipt.json",
    "startup-receipt.json",
    "functional-http-receipt.json",
    "control-export-replay-receipt.json",
    "concurrency-receipt.json",
    "sustained-read-receipt.json",
    "runtime-memory-receipt.json",
    "verification-summary.json",
    "http-cases.tsv",
    "runtime-probe.jsonl",
    "server-output.txt",
)
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


@dataclass(frozen=True)
class CollectionSpec:
    slug: str
    surface_key: str
    identity_key: str
    active_count_key: str
    control_count_key: str


COLLECTIONS = (
    CollectionSpec(
        "association-realizations",
        "association_realizations",
        "association_realization_id",
        "active_product_realization_count",
        "control_realization_count",
    ),
    CollectionSpec(
        "associations",
        "associations",
        "association_id",
        "active_product_association_count",
        "control_association_count",
    ),
    CollectionSpec(
        "composition-coherence-reviews",
        "composition_coherence_reviews",
        "composition_coherence_review_id",
        "active_product_coherence_review_count",
        "control_coherence_review_count",
    ),
    CollectionSpec(
        "compositions",
        "compositions",
        "composition_id",
        "active_product_composition_count",
        "control_composition_count",
    ),
    CollectionSpec(
        "concept-senses",
        "concept_senses",
        "sense_id",
        "active_product_sense_count",
        "control_sense_count",
    ),
    CollectionSpec(
        "concepts",
        "concepts",
        "concept_id",
        "active_product_concept_count",
        "control_concept_count",
    ),
    CollectionSpec(
        "exports",
        "exports",
        "export_id",
        "active_product_export_count",
        "control_export_count",
    ),
    CollectionSpec(
        "incidences",
        "incidences",
        "incidence_id",
        "active_product_incidence_count",
        "control_incidence_count",
    ),
    CollectionSpec(
        "navigation-states",
        "navigation_states",
        "state_id",
        "active_product_navigation_state_count",
        "control_navigation_state_count",
    ),
    CollectionSpec(
        "scopes",
        "scopes",
        "scope_id",
        "active_product_scope_count",
        "control_scope_count",
    ),
    CollectionSpec(
        "transitions",
        "transitions",
        "transition_id",
        "active_product_transition_count",
        "control_transition_count",
    ),
    CollectionSpec(
        "workflows",
        "workflows",
        "workflow_id",
        "active_product_workflow_count",
        "control_workflow_count",
    ),
)
EXPECTED_READ_PATHS = [
    "/capabilities",
    *(
        path
        for spec in COLLECTIONS
        for path in (f"/{spec.slug}", f"/{spec.slug}/{{{spec.identity_key}}}")
    ),
    *(
        path
        for spec in COLLECTIONS
        for path in (
            f"/controls/{spec.slug}",
            f"/controls/{spec.slug}/{{{spec.identity_key}}}",
        )
    ),
    "/baseline/reconciliation",
]


@dataclass(frozen=True)
class ArtifactContext:
    repo_root: Path
    frontend: Path
    manifest: dict[str, Any]
    model: dict[str, Any]
    manifest_sha256: str
    read_model_sha256: str
    checksum_ledger_sha256: str
    manifest_path: Path
    read_model_path: Path
    checksum_path: Path


@dataclass(frozen=True)
class HttpObservation:
    method: str
    path: str
    status: int | None
    reason: str
    headers: dict[str, str]
    body: bytes
    latency_ms: float
    transport_error: str | None


class VerificationFailure(RuntimeError):
    """A deterministic contract or harness invariant failed."""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def require(condition: bool, code: str) -> None:
    if not condition:
        raise VerificationFailure(code)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        + b"\n"
    )


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_case_ledger(path: Path, cases: Sequence[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=CASE_FIELDS,
            dialect="excel-tab",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in sorted(cases, key=lambda item: str(item["case_id"])):
            output_row = {key: row.get(key, "") for key in CASE_FIELDS}
            if not output_row["error"]:
                output_row["error"] = "NONE"
            writer.writerow(output_row)


def parse_json_object(raw: bytes, code: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise VerificationFailure(f"{code}:INVALID_JSON:{error}") from error
    require(isinstance(value, dict), f"{code}:JSON_OBJECT_REQUIRED")
    return value


def ensure_output_directory(path: Path) -> Path:
    resolved = path.resolve()
    if resolved.exists():
        require(resolved.is_dir(), f"OUTPUT_NOT_DIRECTORY:{resolved}")
    else:
        resolved.mkdir(parents=True, exist_ok=False)
    collisions = [name for name in RECEIPT_NAMES if (resolved / name).exists()]
    require(not collisions, f"OUTPUT_ARTIFACT_ALREADY_EXISTS:{','.join(collisions)}")
    return resolved


def load_artifact_context(repo_root: Path) -> ArtifactContext:
    root = repo_root.resolve()
    frontend = root / "frontend"
    generated = frontend / "generated/trace-exploration-v3"
    manifest_path = generated / "manifest.json"
    read_model_path = generated / "read-model.json"
    checksum_path = generated / "CHECKSUMS.sha256"
    for path in (manifest_path, read_model_path, checksum_path):
        require(path.is_file(), f"GENERATED_ARTIFACT_MISSING:{path}")

    manifest_raw = manifest_path.read_bytes()
    read_model_raw = read_model_path.read_bytes()
    checksum_raw = checksum_path.read_bytes()
    try:
        checksum_text = checksum_raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise VerificationFailure("CHECKSUM_LEDGER_NOT_ASCII") from error
    match = re.fullmatch(
        r"([0-9a-f]{64})  manifest\.json\n([0-9a-f]{64})  read-model\.json\n",
        checksum_text,
    )
    require(match is not None, "CHECKSUM_LEDGER_EXACT_TWO_LINE_FORMAT")
    assert match is not None
    listed_manifest_sha, listed_model_sha = match.groups()
    actual_manifest_sha = sha256_bytes(manifest_raw)
    actual_model_sha = sha256_bytes(read_model_raw)
    require(actual_manifest_sha == EXPECTED_MANIFEST_SHA256, "FROZEN_MANIFEST_TRUST_ANCHOR")
    require(actual_model_sha == EXPECTED_READ_MODEL_SHA256, "FROZEN_READ_MODEL_TRUST_ANCHOR")
    require(
        sha256_bytes(checksum_raw) == EXPECTED_CHECKSUMS_SHA256,
        "FROZEN_CHECKSUMS_TRUST_ANCHOR",
    )
    require(listed_manifest_sha == actual_manifest_sha, "CHECKSUM_LEDGER_MANIFEST_MISMATCH")
    require(listed_model_sha == actual_model_sha, "CHECKSUM_LEDGER_READ_MODEL_MISMATCH")

    manifest = parse_json_object(manifest_raw, "MANIFEST")
    model = parse_json_object(read_model_raw, "READ_MODEL")
    require(canonical_json_bytes(manifest) == manifest_raw, "MANIFEST_NOT_CANONICAL")
    require(canonical_json_bytes(model) == read_model_raw, "READ_MODEL_NOT_CANONICAL")
    require(manifest.get("api_version") == API_VERSION, "MANIFEST_API_VERSION")
    require(model.get("api_version") == API_VERSION, "READ_MODEL_API_VERSION")
    require(
        manifest.get("artifact_sha256") == {"read-model.json": actual_model_sha},
        "MANIFEST_READ_MODEL_SHA_BINDING",
    )
    require(
        manifest.get("artifact_bytes") == {"read-model.json": len(read_model_raw)},
        "MANIFEST_READ_MODEL_SIZE_BINDING",
    )
    require(model.get("closure_flags") == manifest.get("closure_flags"), "CLOSURE_FLAG_BINDING")
    require(model.get("fact_boundary") == manifest.get("fact_boundary"), "FACT_BOUNDARY_BINDING")
    closure_flags = model.get("closure_flags")
    require(isinstance(closure_flags, dict), "CLOSURE_FLAGS_OBJECT")
    require(closure_flags and all(value is False for value in closure_flags.values()), "CLOSURE_FLAGS_FAIL_CLOSED")

    active = model.get("active_product")
    controls = model.get("research_controls")
    capabilities = model.get("capabilities")
    counts = manifest.get("counts")
    require(isinstance(active, dict), "ACTIVE_PRODUCT_SURFACE_OBJECT")
    require(isinstance(controls, dict), "CONTROL_SURFACE_OBJECT")
    require(set(active) == set(SURFACE_KEYS), "ACTIVE_PRODUCT_SURFACE_KEYS")
    require(set(controls) == set(SURFACE_KEYS), "CONTROL_SURFACE_KEYS")
    require(isinstance(capabilities, dict), "CAPABILITIES_OBJECT")
    require(isinstance(counts, dict), "MANIFEST_COUNTS_OBJECT")
    require(capabilities == counts, "CAPABILITIES_MANIFEST_COUNT_BINDING")

    synthetic_boundary = {
        "data_class": "SYNTHETIC_CONTROL",
        "production_fact": False,
        "synthetic_control": True,
    }
    for spec in COLLECTIONS:
        active_items = active.get(spec.surface_key)
        control_items = controls.get(spec.surface_key)
        require(isinstance(active_items, list), f"ACTIVE_COLLECTION_ARRAY:{spec.surface_key}")
        require(isinstance(control_items, list), f"CONTROL_COLLECTION_ARRAY:{spec.surface_key}")
        require(active_items == [], f"ACTIVE_COLLECTION_NOT_EMPTY:{spec.surface_key}")
        require(capabilities.get(spec.active_count_key) == 0, f"ACTIVE_COUNT_NOT_ZERO:{spec.active_count_key}")
        require(
            capabilities.get(spec.control_count_key) == len(control_items),
            f"CONTROL_COUNT_MISMATCH:{spec.control_count_key}",
        )
        identifiers: list[str] = []
        for index, item in enumerate(control_items):
            require(isinstance(item, dict), f"CONTROL_RECORD_OBJECT:{spec.surface_key}:{index}")
            identifier = item.get(spec.identity_key)
            require(isinstance(identifier, str) and identifier, f"CONTROL_IDENTIFIER:{spec.surface_key}:{index}")
            identifiers.append(identifier)
            require(
                item.get("fact_boundary") == synthetic_boundary,
                f"CONTROL_FACT_BOUNDARY:{spec.surface_key}:{identifier}",
            )
        require(len(identifiers) == len(set(identifiers)), f"CONTROL_IDENTIFIER_UNIQUE:{spec.surface_key}")

    require(capabilities.get("production_activation_count") == 0, "PRODUCTION_ACTIVATION_COUNT")
    require(capabilities.get("product_activation_available") is False, "PRODUCT_ACTIVATION_AVAILABLE")
    require(capabilities.get("research_controls_only") is True, "RESEARCH_CONTROLS_ONLY")
    require(capabilities.get("read_paths") == EXPECTED_READ_PATHS, "READ_PATH_CAPABILITY_PARITY")
    require(capabilities.get("governed_product_arity_bound") is None, "GOVERNED_ARITY_BOUND_NOT_NULL")
    require(
        capabilities.get("backend_association_arity_support")
        == "PAIR_2_OR_HIGHER_ORDER_3_PLUS_NO_FIXED_SCHEMA_MAXIMUM",
        "BACKEND_ARITY_SUPPORT",
    )
    require(capabilities.get("implicit_pair_projection_allowed") is False, "PAIR_PROJECTION_FAIL_CLOSED")
    require(capabilities.get("association_and_composition_identity_separate") is True, "IDENTITY_SEPARATION")
    require(capabilities.get("transitions_available") is False, "TRANSITIONS_AVAILABLE")
    require(capabilities.get("active_product_transition_count") == 0, "ACTIVE_TRANSITION_COUNT")
    require(capabilities.get("control_transition_count") == 0, "CONTROL_TRANSITION_COUNT")
    require(
        capabilities.get("transition_derivation_policy") == "NONE_NO_V2_INHERITANCE",
        "TRANSITION_DERIVATION_POLICY",
    )
    require(
        capabilities.get("transition_status") == "FAIL_CLOSED_NO_ACTIVE_PRODUCT_STATE_GRAPH",
        "TRANSITION_STATUS",
    )
    require(controls.get("transitions") == [], "CONTROL_TRANSITIONS_NOT_EMPTY")
    derived_active_pending_review_count = sum(
        row["eligibility"]["lifecycle_state"] == "ACTIVE"
        and (
            row["review"]["review_state"] != "FINAL"
            or row["review"]["authority_state"] != "FINAL"
        )
        for row in active["associations"]
    )
    all_associations = [*active["associations"], *controls["associations"]]
    all_realizations = [
        *active["association_realizations"], *controls["association_realizations"]
    ]
    derived_implicit_projection_count = sum(
        row["association_kind"] == "HIGHER_ORDER"
        and (
            row["pair_projection_policy"] != "NONE"
            or any(
                realization["association_revision_id"] == row["association_revision_id"]
                and realization["realization_kind"] == "PAIR_EDGE"
                for realization in all_realizations
            )
        )
        for row in all_associations
    )
    require(
        capabilities.get("active_pending_review_count")
        == derived_active_pending_review_count,
        "ACTIVE_PENDING_REVIEW_DERIVATION",
    )
    require(
        capabilities.get("implicit_hyperedge_projection_count")
        == derived_implicit_projection_count,
        "IMPLICIT_HYPEREDGE_PROJECTION_DERIVATION",
    )

    return ArtifactContext(
        repo_root=root,
        frontend=frontend,
        manifest=manifest,
        model=model,
        manifest_sha256=actual_manifest_sha,
        read_model_sha256=actual_model_sha,
        checksum_ledger_sha256=sha256_bytes(checksum_raw),
        manifest_path=manifest_path,
        read_model_path=read_model_path,
        checksum_path=checksum_path,
    )


def artifact_receipt(context: ArtifactContext, mode: str) -> dict[str, Any]:
    active_counts = {
        spec.surface_key: len(context.model["active_product"][spec.surface_key])
        for spec in COLLECTIONS
    }
    control_counts = {
        spec.surface_key: len(context.model["research_controls"][spec.surface_key])
        for spec in COLLECTIONS
    }
    return {
        "schema_version": "trace-exploration-v3-production-artifact-check-v1",
        "status": "PASS",
        "mode": mode,
        "checked_utc": utc_now(),
        "api_version": API_VERSION,
        "manifest_path": str(context.manifest_path.relative_to(context.repo_root)),
        "manifest_sha256": context.manifest_sha256,
        "read_model_path": str(context.read_model_path.relative_to(context.repo_root)),
        "read_model_sha256": context.read_model_sha256,
        "read_model_bytes": context.read_model_path.stat().st_size,
        "checksum_ledger_path": str(context.checksum_path.relative_to(context.repo_root)),
        "checksum_ledger_sha256": context.checksum_ledger_sha256,
        "active_product_counts": active_counts,
        "research_control_counts": control_counts,
        "closure_flags": context.model["closure_flags"],
        "production_activation_count": context.model["capabilities"]["production_activation_count"],
        "research_controls_only": context.model["capabilities"]["research_controls_only"],
        "transition_status": context.model["capabilities"]["transition_status"],
    }


def perform_request(
    port: int,
    method: str,
    path: str,
    timeout_seconds: float,
) -> HttpObservation:
    started = time.perf_counter()
    connection: http.client.HTTPConnection | None = None
    try:
        require(path.startswith("/"), f"HTTP_PATH_NOT_ABSOLUTE:{path}")
        connection = http.client.HTTPConnection(LOOPBACK_HOST, port, timeout=timeout_seconds)
        connection.request(
            method,
            path,
            headers={
                "Accept": "application/json",
                "Connection": "close",
                "User-Agent": "TRACE-Round16B-Production-Verifier/1",
            },
        )
        response = connection.getresponse()
        body = response.read()
        headers: dict[str, str] = {}
        for name, value in response.getheaders():
            lowered = name.lower()
            headers[lowered] = f"{headers[lowered]}, {value}" if lowered in headers else value
        return HttpObservation(
            method=method,
            path=path,
            status=response.status,
            reason=response.reason,
            headers=headers,
            body=body,
            latency_ms=(time.perf_counter() - started) * 1000,
            transport_error=None,
        )
    except BaseException as error:
        return HttpObservation(
            method=method,
            path=path,
            status=None,
            reason="",
            headers={},
            body=b"",
            latency_ms=(time.perf_counter() - started) * 1000,
            transport_error=f"{type(error).__name__}:{error}",
        )
    finally:
        if connection is not None:
            connection.close()


def validate_common_headers(observation: HttpObservation, context: ArtifactContext) -> None:
    for name, expected in COMMON_HEADER_EXPECTATIONS.items():
        require(observation.headers.get(name) == expected, f"HEADER_MISMATCH:{name}")
    require(
        observation.headers.get("x-trace-read-model") == context.read_model_sha256,
        "HEADER_MISMATCH:x-trace-read-model",
    )
    vary_tokens = {
        token.strip().lower()
        for token in observation.headers.get("vary", "").split(",")
        if token.strip()
    }
    require("accept" in vary_tokens, "HEADER_MISMATCH:vary_accept")


def expected_envelope(context: ArtifactContext, data: Any) -> dict[str, Any]:
    return {
        "api_version": API_VERSION,
        "closure_flags": context.model["closure_flags"],
        "fact_boundary": context.model["fact_boundary"],
        "read_model_sha256": context.read_model_sha256,
        "data": data,
    }


def validate_exact_json(observation: HttpObservation, expected: Mapping[str, Any]) -> None:
    content_type = observation.headers.get("content-type", "").lower()
    require(content_type.startswith("application/json"), "CONTENT_TYPE_NOT_JSON")
    actual = parse_json_object(observation.body, "HTTP_RESPONSE")
    require(actual == expected, "HTTP_JSON_BODY_MISMATCH")


def validate_empty_body(observation: HttpObservation) -> None:
    require(observation.body == b"", "HTTP_BODY_NOT_EMPTY")


def validate_error_body(
    observation: HttpObservation,
    context: ArtifactContext,
    code: str,
    status: int,
    instance: str,
) -> None:
    payload = parse_json_object(observation.body, "HTTP_ERROR")
    require(
        set(payload)
        == {
            "api_version",
            "code",
            "instance",
            "message",
            "read_model_sha256",
            "retryable",
            "schema_version",
            "status",
        },
        "HTTP_ERROR_SCHEMA_KEYS",
    )
    require(payload.get("api_version") == API_VERSION, "HTTP_ERROR_API_VERSION")
    require(payload.get("code") == code, "HTTP_ERROR_CODE")
    require(payload.get("instance") == instance, "HTTP_ERROR_INSTANCE")
    require(isinstance(payload.get("message"), str) and payload["message"], "HTTP_ERROR_MESSAGE")
    require(payload.get("read_model_sha256") == context.read_model_sha256, "HTTP_ERROR_READ_MODEL_SHA")
    require(payload.get("retryable") is False, "HTTP_ERROR_RETRYABLE")
    require(payload.get("schema_version") == "trace-exploration-api-error-v3", "HTTP_ERROR_SCHEMA")
    require(payload.get("status") == status, "HTTP_ERROR_STATUS")
    content_type = observation.headers.get("content-type", "").lower()
    require(content_type.startswith("application/json"), "HTTP_ERROR_CONTENT_TYPE")


def case_row(
    case_id: str,
    phase: str,
    expected_status: int,
    observation: HttpObservation,
    error: str,
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "phase": phase,
        "method": observation.method,
        "path": observation.path,
        "expected_status": expected_status,
        "actual_status": "" if observation.status is None else observation.status,
        "outcome": "FAIL" if error else "PASS",
        "latency_ms": f"{observation.latency_ms:.6f}",
        "response_bytes": len(observation.body),
        "response_sha256": sha256_bytes(observation.body),
        "error": error,
    }


def evaluate_http_case(
    context: ArtifactContext,
    port: int,
    timeout_seconds: float,
    case_id: str,
    phase: str,
    method: str,
    path: str,
    expected_status: int,
    validator: Callable[[HttpObservation], None],
) -> tuple[HttpObservation, dict[str, Any], str]:
    observation = perform_request(port, method, path, timeout_seconds)
    error_text = ""
    try:
        require(observation.transport_error is None, f"HTTP_TRANSPORT:{observation.transport_error}")
        require(observation.status == expected_status, f"HTTP_STATUS:{observation.status}!={expected_status}")
        validate_common_headers(observation, context)
        validator(observation)
    except BaseException as error:
        error_text = f"{type(error).__name__}:{error}"
    return observation, case_row(case_id, phase, expected_status, observation, error_text), error_text


def require_http_case(
    cases: list[dict[str, Any]],
    context: ArtifactContext,
    port: int,
    timeout_seconds: float,
    case_id: str,
    phase: str,
    method: str,
    path: str,
    expected_status: int,
    validator: Callable[[HttpObservation], None],
) -> HttpObservation:
    observation, row, error = evaluate_http_case(
        context,
        port,
        timeout_seconds,
        case_id,
        phase,
        method,
        path,
        expected_status,
        validator,
    )
    cases.append(row)
    require(not error, f"HTTP_CASE_FAILED:{case_id}:{error}")
    return observation


def capabilities_body(context: ArtifactContext) -> dict[str, Any]:
    return expected_envelope(
        context,
        {
            "capabilities": context.model["capabilities"],
            "contract_version": context.model["contract_version"],
            "source_authority": context.model["source_authority"],
        },
    )


def wait_for_readiness(
    process: subprocess.Popen[str],
    context: ArtifactContext,
    port: int,
    timeout_seconds: float,
    request_timeout_seconds: float,
) -> dict[str, Any]:
    started = time.monotonic()
    deadline = started + timeout_seconds
    attempts = 0
    statuses: list[str] = []
    readiness_path = f"{API_BASE}/capabilities"
    while time.monotonic() < deadline:
        return_code = process.poll()
        if return_code is not None:
            raise VerificationFailure(f"SERVER_EXITED_BEFORE_READINESS:{return_code}")
        attempts += 1
        observation = perform_request(
            port,
            "GET",
            readiness_path,
            min(request_timeout_seconds, 2.0),
        )
        status_label = observation.transport_error or str(observation.status)
        statuses.append(status_label)
        statuses = statuses[-20:]
        if observation.status == 200 and observation.transport_error is None:
            validate_common_headers(observation, context)
            validate_exact_json(observation, capabilities_body(context))
            return {
                "attempt_count": attempts,
                "cold_start_ms": (time.monotonic() - started) * 1000,
                "first_successful_request_ms": observation.latency_ms,
                "first_response_bytes": len(observation.body),
                "first_response_sha256": sha256_bytes(observation.body),
                "recent_attempt_statuses": statuses,
                "readiness_path": readiness_path,
            }
        time.sleep(0.05)
    raise VerificationFailure(
        f"SERVER_READINESS_TIMEOUT:attempts={attempts}:recent={','.join(statuses)}"
    )


def run_functional_http(
    context: ArtifactContext,
    port: int,
    timeout_seconds: float,
    cases: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, bytes]]:
    phase = "FUNCTIONAL_HTTP"
    stable_reads: dict[str, bytes] = {}
    redirect_path = f"{API_BASE}/capabilities"

    def redirect_validator(observation: HttpObservation) -> None:
        validate_empty_body(observation)
        require(observation.headers.get("location") == redirect_path, "ROOT_REDIRECT_LOCATION")

    require_http_case(
        cases, context, port, timeout_seconds, "F001", phase, "GET", API_BASE, 308, redirect_validator
    )
    require_http_case(
        cases, context, port, timeout_seconds, "F002", phase, "HEAD", API_BASE, 308, redirect_validator
    )
    require_http_case(
        cases,
        context,
        port,
        timeout_seconds,
        "F003",
        phase,
        "OPTIONS",
        API_BASE,
        204,
        validate_empty_body,
    )

    capability_observation = require_http_case(
        cases,
        context,
        port,
        timeout_seconds,
        "F004",
        phase,
        "GET",
        redirect_path,
        200,
        lambda item: validate_exact_json(item, capabilities_body(context)),
    )
    stable_reads[redirect_path] = capability_observation.body
    require_http_case(
        cases,
        context,
        port,
        timeout_seconds,
        "F005",
        phase,
        "HEAD",
        redirect_path,
        200,
        validate_empty_body,
    )
    require_http_case(
        cases,
        context,
        port,
        timeout_seconds,
        "F006",
        phase,
        "OPTIONS",
        redirect_path,
        204,
        validate_empty_body,
    )

    case_counter = 7
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        require_http_case(
            cases,
            context,
            port,
            timeout_seconds,
            f"F{case_counter:03d}",
            phase,
            method,
            redirect_path,
            405,
            lambda item, method=method: validate_error_body(
                item,
                context,
                "METHOD_NOT_ALLOWED",
                405,
                redirect_path,
            ),
        )
        case_counter += 1

    require_http_case(
        cases,
        context,
        port,
        timeout_seconds,
        f"F{case_counter:03d}",
        phase,
        "POST",
        API_BASE,
        405,
        lambda item: validate_error_body(item, context, "METHOD_NOT_ALLOWED", 405, redirect_path),
    )
    case_counter += 1
    unknown_path = f"{API_BASE}/unknown-route/deeper"
    require_http_case(
        cases,
        context,
        port,
        timeout_seconds,
        f"F{case_counter:03d}",
        phase,
        "GET",
        unknown_path,
        404,
        lambda item: validate_error_body(item, context, "ENDPOINT_NOT_FOUND", 404, unknown_path),
    )
    case_counter += 1
    require_http_case(
        cases,
        context,
        port,
        timeout_seconds,
        f"F{case_counter:03d}",
        phase,
        "HEAD",
        unknown_path,
        404,
        validate_empty_body,
    )
    case_counter += 1
    require_http_case(
        cases,
        context,
        port,
        timeout_seconds,
        f"F{case_counter:03d}",
        phase,
        "POST",
        unknown_path,
        404,
        lambda item: validate_error_body(item, context, "ENDPOINT_NOT_FOUND", 404, unknown_path),
    )
    case_counter += 1
    require_http_case(
        cases,
        context,
        port,
        timeout_seconds,
        f"F{case_counter:03d}",
        phase,
        "OPTIONS",
        unknown_path,
        204,
        validate_empty_body,
    )
    case_counter += 1

    baseline_path = f"{API_BASE}/baseline/reconciliation"
    baseline_expected = expected_envelope(
        context,
        {"baseline_reconciliation": context.model["baseline_reconciliation"]},
    )
    baseline_observation = require_http_case(
        cases,
        context,
        port,
        timeout_seconds,
        f"F{case_counter:03d}",
        phase,
        "GET",
        baseline_path,
        200,
        lambda item: validate_exact_json(item, baseline_expected),
    )
    stable_reads[baseline_path] = baseline_observation.body
    case_counter += 1

    representatives: dict[str, str] = {}
    active = context.model["active_product"]
    controls = context.model["research_controls"]
    for spec in COLLECTIONS:
        active_path = f"{API_BASE}/{spec.slug}"
        active_expected = expected_envelope(
            context,
            {
                "collection": spec.slug,
                "count": 0,
                "data_class": "ACTIVE_PRODUCT_FACT",
                "items": active[spec.surface_key],
            },
        )
        active_observation = require_http_case(
            cases,
            context,
            port,
            timeout_seconds,
            f"F{case_counter:03d}",
            phase,
            "GET",
            active_path,
            200,
            lambda item, expected=active_expected: validate_exact_json(item, expected),
        )
        stable_reads[active_path] = active_observation.body
        case_counter += 1
        require_http_case(
            cases,
            context,
            port,
            timeout_seconds,
            f"F{case_counter:03d}",
            phase,
            "HEAD",
            active_path,
            200,
            validate_empty_body,
        )
        case_counter += 1

        control_items = controls[spec.surface_key]
        control_path = f"{API_BASE}/controls/{spec.slug}"
        control_expected = expected_envelope(
            context,
            {
                "collection": spec.slug,
                "count": len(control_items),
                "data_class": "SYNTHETIC_CONTROL",
                "items": control_items,
            },
        )
        require_http_case(
            cases,
            context,
            port,
            timeout_seconds,
            f"F{case_counter:03d}",
            phase,
            "GET",
            control_path,
            200,
            lambda item, expected=control_expected: validate_exact_json(item, expected),
        )
        case_counter += 1
        require_http_case(
            cases,
            context,
            port,
            timeout_seconds,
            f"F{case_counter:03d}",
            phase,
            "HEAD",
            control_path,
            200,
            validate_empty_body,
        )
        case_counter += 1

        representative = control_items[0] if control_items else None
        identifier = (
            representative[spec.identity_key]
            if representative is not None
            else f"{spec.identity_key}:unavailable"
        )
        if representative is not None:
            representatives[spec.slug] = identifier
        encoded_identifier = quote(identifier, safe="")
        control_item_path = f"{control_path}/{encoded_identifier}"
        if representative is not None:
            control_item_expected = expected_envelope(
                context,
                {
                    "collection": spec.slug,
                    "data_class": "SYNTHETIC_CONTROL",
                    "item": representative,
                },
            )
            control_item_validator: Callable[[HttpObservation], None] = (
                lambda item, expected=control_item_expected: validate_exact_json(item, expected)
            )
            control_item_status = 200
        else:
            unknown_code = (
                "INVALID_ASSOCIATION"
                if spec.slug == "associations"
                else "INVALID_COMPOSITION"
                if spec.slug == "compositions"
                else "INVALID_CONTROL"
            )
            control_item_validator = lambda item, code=unknown_code, instance=f"{control_path}/{identifier}": validate_error_body(
                item, context, code, 404, instance
            )
            control_item_status = 404
        require_http_case(
            cases,
            context,
            port,
            timeout_seconds,
            f"F{case_counter:03d}",
            phase,
            "GET",
            control_item_path,
            control_item_status,
            control_item_validator,
        )
        case_counter += 1
        require_http_case(
            cases,
            context,
            port,
            timeout_seconds,
            f"F{case_counter:03d}",
            phase,
            "HEAD",
            control_item_path,
            control_item_status,
            validate_empty_body,
        )
        case_counter += 1

        active_item_path = f"{active_path}/{encoded_identifier}"
        active_item_instance = f"{active_path}/{identifier}"
        active_item_code = "NOT_ACTIVE_PRODUCT_FACT" if representative is not None else (
            "INVALID_ASSOCIATION"
            if spec.slug == "associations"
            else "INVALID_COMPOSITION"
            if spec.slug == "compositions"
            else "INVALID_CONTROL"
        )
        require_http_case(
            cases,
            context,
            port,
            timeout_seconds,
            f"F{case_counter:03d}",
            phase,
            "GET",
            active_item_path,
            404,
            lambda item, instance=active_item_instance, code=active_item_code: validate_error_body(
                item, context, code, 404, instance
            ),
        )
        case_counter += 1
        require_http_case(
            cases,
            context,
            port,
            timeout_seconds,
            f"F{case_counter:03d}",
            phase,
            "HEAD",
            active_item_path,
            404,
            validate_empty_body,
        )
        case_counter += 1

        unknown_identifier = f"unknown:v3:{spec.slug}"
        unknown_code = (
            "INVALID_ASSOCIATION"
            if spec.slug == "associations"
            else "INVALID_COMPOSITION"
            if spec.slug == "compositions"
            else "INVALID_CONTROL"
        )
        for prefix in (active_path, control_path):
            unknown_path = f"{prefix}/{quote(unknown_identifier, safe='')}"
            unknown_instance = f"{prefix}/{unknown_identifier}"
            require_http_case(
                cases,
                context,
                port,
                timeout_seconds,
                f"F{case_counter:03d}",
                phase,
                "GET",
                unknown_path,
                404,
                lambda item, code=unknown_code, instance=unknown_instance: validate_error_body(
                    item, context, code, 404, instance
                ),
            )
            case_counter += 1
            require_http_case(
                cases,
                context,
                port,
                timeout_seconds,
                f"F{case_counter:03d}",
                phase,
                "HEAD",
                unknown_path,
                404,
                validate_empty_body,
            )
            case_counter += 1

    phase_cases = [item for item in cases if item["phase"] == phase]
    return (
        {
            "schema_version": "trace-exploration-v3-functional-http-receipt-v1",
            "status": "PASS",
            "checked_utc": utc_now(),
            "api_base": API_BASE,
            "read_model_sha256": context.read_model_sha256,
            "case_count": len(phase_cases),
            "pass_count": sum(item["outcome"] == "PASS" for item in phase_cases),
            "failure_count": sum(item["outcome"] == "FAIL" for item in phase_cases),
            "active_empty_collection_count": len(COLLECTIONS),
            "control_collection_count": len(COLLECTIONS),
            "representative_control_ids": representatives,
            "root_redirect_status": 308,
            "root_redirect_location": redirect_path,
            "allowed_methods": COMMON_HEADER_EXPECTATIONS["allow"],
            "unknown_route_status": 404,
            "performance_interpretation": PERFORMANCE_INTERPRETATION,
        },
        stable_reads,
    )


def validate_export_semantics(export_item: Mapping[str, Any]) -> None:
    semantic_sha = export_item.get("semantic_sha256")
    export_id = export_item.get("export_id")
    require(isinstance(semantic_sha, str) and re.fullmatch(r"[0-9a-f]{64}", semantic_sha) is not None, "EXPORT_SEMANTIC_SHA")
    require(export_id == f"export:v3:{semantic_sha[:24]}", "EXPORT_ID_SEMANTIC_BINDING")
    require(export_item.get("pair_projection_policy_preserved") is True, "EXPORT_PAIR_POLICY")
    records = export_item.get("projection_preservation_records")
    require(isinstance(records, list) and records, "EXPORT_PROJECTION_RECORDS")
    expected_kinds = sorted((record.get("realization_kind"), record.get("pair_projection_policy")) for record in records)
    require(
        expected_kinds
        == sorted(
            [
                ("PAIR_EDGE", "NOT_APPLICABLE"),
                ("PAIR_EDGE", "NOT_APPLICABLE"),
                ("HYPEREDGE_HUB", "NONE"),
            ]
        ),
        "EXPORT_PROJECTION_PRESERVATION",
    )


def run_export_replay(
    context: ArtifactContext,
    port: int,
    timeout_seconds: float,
    replay_count: int,
    cases: list[dict[str, Any]],
    phase_label: str,
    case_prefix: str,
    expected_body: bytes | None = None,
) -> tuple[dict[str, Any], bytes]:
    exports = context.model["research_controls"]["exports"]
    require(len(exports) == 1, "CONTROL_EXPORT_COUNT_NOT_ONE")
    export_item = exports[0]
    validate_export_semantics(export_item)
    export_id = export_item["export_id"]
    path = f"{API_BASE}/controls/exports"
    expected = expected_envelope(
        context,
        {
            "collection": "exports",
            "count": 1,
            "data_class": "SYNTHETIC_CONTROL",
            "items": exports,
        },
    )
    bodies: list[bytes] = []
    for index in range(replay_count):
        observation = require_http_case(
            cases,
            context,
            port,
            timeout_seconds,
            f"{case_prefix}{index + 1:03d}",
            phase_label,
            "GET",
            path,
            200,
            lambda item: validate_exact_json(item, expected),
        )
        bodies.append(observation.body)
    require(len(set(bodies)) == 1, "CONTROL_EXPORT_REPLAY_BYTES_DIVERGED")
    if expected_body is not None:
        require(bodies[0] == expected_body, "CONTROL_EXPORT_POST_LOAD_REPLAY_DIVERGED")
    return (
        {
            "export_id": export_id,
            "semantic_sha256": export_item["semantic_sha256"],
            "presentation_sha256": export_item["presentation_sha256"],
            "pair_projection_policy_preserved": True,
            "projection_preservation_record_count": len(export_item["projection_preservation_records"]),
            "replay_count": replay_count,
            "response_bytes": len(bodies[0]),
            "response_sha256": sha256_bytes(bodies[0]),
        },
        bodies[0],
    )


def percentile(values: Sequence[float], quantile: float) -> float:
    require(bool(values), "PERCENTILE_EMPTY")
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def summarize_http_observations(
    observations: Sequence[HttpObservation],
    duration_seconds: float,
) -> dict[str, Any]:
    latencies = [item.latency_ms for item in observations]
    return {
        "request_count": len(observations),
        "duration_ms": duration_seconds * 1000,
        "throughput_requests_per_second": len(observations) / duration_seconds if duration_seconds > 0 else 0,
        "response_bytes": sum(len(item.body) for item in observations),
        "latency_ms": {
            "minimum": min(latencies),
            "p50": percentile(latencies, 0.50),
            "p95": percentile(latencies, 0.95),
            "p99": percentile(latencies, 0.99),
            "maximum": max(latencies),
        },
        "performance_interpretation": PERFORMANCE_INTERPRETATION,
    }


def stable_body_validator(
    context: ArtifactContext,
    expected_body: bytes,
) -> Callable[[HttpObservation], None]:
    expected_sha = sha256_bytes(expected_body)

    def validate(observation: HttpObservation) -> None:
        require(sha256_bytes(observation.body) == expected_sha, "STABLE_READ_RESPONSE_SHA")
        require(observation.body == expected_body, "STABLE_READ_RESPONSE_BYTES")

    return validate


def run_concurrency_matrix(
    context: ArtifactContext,
    port: int,
    timeout_seconds: float,
    requests_per_level: int,
    stable_reads: Mapping[str, bytes],
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    levels = (1, 5, 10, 25, 50)
    paths = tuple(sorted(stable_reads))
    require(paths, "CONCURRENCY_STABLE_PATHS_EMPTY")
    workloads: list[dict[str, Any]] = []
    aggregate_failure_count = 0
    for level in levels:
        total_requests = max(requests_per_level, level)
        base, remainder = divmod(total_requests, level)
        worker_counts = [base + (1 if index < remainder else 0) for index in range(level)]
        require(all(count >= 1 for count in worker_counts), f"CONCURRENCY_EMPTY_WORKER:c{level}")
        barrier = threading.Barrier(level)

        def worker(worker_index: int, count: int) -> tuple[list[HttpObservation], list[dict[str, Any]], list[str]]:
            observations: list[HttpObservation] = []
            rows: list[dict[str, Any]] = []
            errors: list[str] = []
            try:
                barrier.wait(timeout=30)
            except threading.BrokenBarrierError as error:
                errors.append(f"CONCURRENCY_BARRIER:{error}")
                return observations, rows, errors
            for sequence in range(count):
                path = paths[(worker_index + sequence) % len(paths)]
                observation, row, case_error = evaluate_http_case(
                    context,
                    port,
                    timeout_seconds,
                    f"C{level:02d}-W{worker_index:02d}-R{sequence:04d}",
                    f"CONCURRENCY_C{level}",
                    "GET",
                    path,
                    200,
                    stable_body_validator(context, stable_reads[path]),
                )
                observations.append(observation)
                rows.append(row)
                if case_error:
                    errors.append(case_error)
            return observations, rows, errors

        started = time.perf_counter()
        observations: list[HttpObservation] = []
        failures: list[str] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=level) as executor:
            futures = [
                executor.submit(worker, worker_index, count)
                for worker_index, count in enumerate(worker_counts)
            ]
            for future in futures:
                worker_observations, rows, worker_failures = future.result()
                observations.extend(worker_observations)
                cases.extend(rows)
                failures.extend(worker_failures)
        duration = time.perf_counter() - started
        require(len(observations) == total_requests, f"CONCURRENCY_REQUEST_COUNT:c{level}")
        aggregate_failure_count += len(failures)
        workloads.append(
            {
                "concurrency": level,
                "status": "PASS" if not failures else "FAIL",
                "failure_count": len(failures),
                **summarize_http_observations(observations, duration),
            }
        )
    receipt = {
        "schema_version": "trace-exploration-v3-concurrency-receipt-v1",
        "status": "PASS" if aggregate_failure_count == 0 else "FAIL",
        "checked_utc": utc_now(),
        "concurrency_levels": list(levels),
        "requests_per_level": requests_per_level,
        "failure_count": aggregate_failure_count,
        "workloads": workloads,
        "performance_interpretation": PERFORMANCE_INTERPRETATION,
    }
    require(aggregate_failure_count == 0, f"CONCURRENCY_FAILURE_COUNT:{aggregate_failure_count}")
    return receipt


def run_sustained_read(
    context: ArtifactContext,
    port: int,
    timeout_seconds: float,
    duration_seconds: float,
    concurrency: int,
    request_cap: int,
    stable_reads: Mapping[str, bytes],
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    paths = tuple(sorted(stable_reads))
    require(paths, "SUSTAINED_STABLE_PATHS_EMPTY")
    base, remainder = divmod(request_cap, concurrency)
    worker_counts = [base + (1 if index < remainder else 0) for index in range(concurrency)]
    require(all(count >= 1 for count in worker_counts), "SUSTAINED_EMPTY_WORKER")
    barrier = threading.Barrier(concurrency)
    shared_start = [0.0]
    start_lock = threading.Lock()

    def worker(worker_index: int, count: int) -> tuple[list[HttpObservation], list[dict[str, Any]], list[str]]:
        observations: list[HttpObservation] = []
        rows: list[dict[str, Any]] = []
        errors: list[str] = []
        try:
            barrier.wait(timeout=30)
        except threading.BrokenBarrierError as error:
            errors.append(f"SUSTAINED_BARRIER:{error}")
            return observations, rows, errors
        with start_lock:
            if shared_start[0] == 0:
                shared_start[0] = time.perf_counter()
        start = shared_start[0]
        interval = duration_seconds / count
        for sequence in range(count):
            target = start + sequence * interval
            remaining = target - time.perf_counter()
            if remaining > 0:
                time.sleep(remaining)
            path = paths[(worker_index + sequence) % len(paths)]
            observation, row, case_error = evaluate_http_case(
                context,
                port,
                timeout_seconds,
                f"S-W{worker_index:02d}-R{sequence:05d}",
                "SUSTAINED_READ",
                "GET",
                path,
                200,
                stable_body_validator(context, stable_reads[path]),
            )
            observations.append(observation)
            rows.append(row)
            if case_error:
                errors.append(case_error)
        return observations, rows, errors

    started = time.perf_counter()
    observations: list[HttpObservation] = []
    failures: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(worker, worker_index, count)
            for worker_index, count in enumerate(worker_counts)
        ]
        for future in futures:
            worker_observations, rows, worker_failures = future.result()
            observations.extend(worker_observations)
            cases.extend(rows)
            failures.extend(worker_failures)
    observed_duration = time.perf_counter() - started
    require(len(observations) == request_cap, "SUSTAINED_REQUEST_COUNT")
    completion_ratio = observed_duration / duration_seconds
    require(completion_ratio >= 0.80, f"SUSTAINED_DURATION_UNDERRUN:{completion_ratio:.6f}")
    receipt = {
        "schema_version": "trace-exploration-v3-sustained-read-receipt-v1",
        "status": "PASS" if not failures else "FAIL",
        "checked_utc": utc_now(),
        "concurrency": concurrency,
        "planned_duration_seconds": duration_seconds,
        "observed_duration_seconds": observed_duration,
        "duration_completion_ratio": completion_ratio,
        "request_cap": request_cap,
        "termination_reason": "REQUEST_CAP_AFTER_PACED_BOUNDED_DURATION",
        "failure_count": len(failures),
        **summarize_http_observations(observations, observed_duration),
        "performance_interpretation": PERFORMANCE_INTERPRETATION,
    }
    require(not failures, f"SUSTAINED_FAILURE_COUNT:{len(failures)}")
    return receipt


def validate_full_run_arguments(args: argparse.Namespace) -> None:
    require(args.port is not None, "PORT_REQUIRED_FOR_PRODUCTION_RUN")
    require(1024 <= args.port <= 65535, f"PORT_OUT_OF_RANGE:{args.port}")
    require(args.port != DEFAULT_NEXT_PORT, "NONDEFAULT_PORT_REQUIRED")
    require(1 <= args.readiness_timeout_seconds <= 300, "READINESS_TIMEOUT_BOUNDS")
    require(0.1 <= args.request_timeout_seconds <= 60, "REQUEST_TIMEOUT_BOUNDS")
    require(50 <= args.concurrency_requests_per_level <= 5000, "CONCURRENCY_REQUEST_BOUNDS")
    require(2 <= args.sustained_duration_seconds <= 120, "SUSTAINED_DURATION_BOUNDS")
    require(1 <= args.sustained_concurrency <= 50, "SUSTAINED_CONCURRENCY_BOUNDS")
    require(
        args.sustained_concurrency <= args.sustained_request_cap <= 20000,
        "SUSTAINED_REQUEST_CAP_BOUNDS",
    )
    require(2 <= args.export_replay_count <= 25, "EXPORT_REPLAY_COUNT_BOUNDS")


def ensure_port_available(port: int) -> None:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        probe.bind((LOOPBACK_HOST, port))
    except OSError as error:
        raise VerificationFailure(f"LOOPBACK_PORT_UNAVAILABLE:{port}:{error}") from error
    finally:
        probe.close()


def launch_server(
    context: ArtifactContext,
    output_dir: Path,
    port: int,
) -> tuple[subprocess.Popen[str], Any, dict[str, Any]]:
    next_build = context.frontend / ".next"
    build_id_path = next_build / "BUILD_ID"
    required_server_files_path = next_build / "required-server-files.json"
    probe_module = context.repo_root / "scripts/trace_round16a/node_runtime_probe.cjs"
    next_cli = context.frontend / "node_modules/next/dist/bin/next"
    next_package_path = context.frontend / "node_modules/next/package.json"
    node = shutil.which("node")
    require(next_build.is_dir(), f"NEXT_BUILD_MISSING:{next_build}")
    require(build_id_path.is_file(), f"NEXT_BUILD_ID_MISSING:{build_id_path}")
    require(
        required_server_files_path.is_file(),
        f"NEXT_REQUIRED_SERVER_FILES_MISSING:{required_server_files_path}",
    )
    require(probe_module.is_file(), f"NODE_RUNTIME_PROBE_MISSING:{probe_module}")
    require(next_cli.is_file(), f"NEXT_CLI_MISSING:{next_cli}")
    require(next_package_path.is_file(), f"NEXT_PACKAGE_MISSING:{next_package_path}")
    require(node is not None, "NODE_EXECUTABLE_NOT_FOUND")
    next_package = parse_json_object(next_package_path.read_bytes(), "NEXT_PACKAGE")
    next_version = next_package.get("version")
    require(
        isinstance(next_version, str) and next_version.startswith("15."),
        f"NEXT_15_REQUIRED:{next_version}",
    )
    required_server_files = parse_json_object(
        required_server_files_path.read_bytes(), "NEXT_REQUIRED_SERVER_FILES"
    )
    built_config = required_server_files.get("config")
    require(isinstance(built_config, dict), "NEXT_BUILT_CONFIG_INVALID")
    built_experimental = built_config.get("experimental")
    require(isinstance(built_experimental, dict), "NEXT_BUILT_EXPERIMENTAL_CONFIG_INVALID")
    require(
        built_experimental.get("preloadEntriesOnStart") is False,
        "NEXT_ENTRY_PRELOAD_MUST_BE_DISABLED",
    )
    ensure_port_available(port)

    probe_path = output_dir / "runtime-probe.jsonl"
    # Use a governed text artifact rather than a globally ignored *.log name.
    server_log_path = output_dir / "server-output.txt"
    environment = os.environ.copy()
    environment["NODE_ENV"] = "production"
    environment["NEXT_TELEMETRY_DISABLED"] = "1"
    existing_options = environment.get("NODE_OPTIONS", "").strip()
    require_option = f"--require={probe_module.resolve()}"
    environment["NODE_OPTIONS"] = f"{existing_options} {require_option}".strip()
    probe_session_id = str(uuid.uuid4())
    environment["TRACE_RUNTIME_PROBE_PATH"] = str(probe_path)
    environment["TRACE_RUNTIME_PROBE_SESSION_ID"] = probe_session_id
    environment["TRACE_RUNTIME_PROBE_ROLE"] = "NEXT_PRODUCTION_SERVER_V3_VERIFIER"
    command = [
        node,
        str(next_cli),
        "start",
        "--hostname",
        LOOPBACK_HOST,
        "--port",
        str(port),
    ]
    log_handle = server_log_path.open("w", encoding="utf-8", buffering=1)
    try:
        process = subprocess.Popen(
            command,
            cwd=context.frontend,
            env=environment,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
    except BaseException:
        log_handle.close()
        raise
    metadata = {
        "build_id": build_id_path.read_text(encoding="utf-8").strip(),
        "command": command,
        "host": LOOPBACK_HOST,
        "next_version": next_version,
        "preload_entries_on_start": False,
        "port": port,
        "process_group_id": process.pid,
        "server_pid": process.pid,
        "probe_module": str(probe_module.relative_to(context.repo_root)),
        "probe_path": probe_path.name,
        "probe_session_id": probe_session_id,
        "server_log_path": server_log_path.name,
    }
    return process, log_handle, metadata


def terminate_server(process: subprocess.Popen[str] | None) -> dict[str, Any]:
    if process is None:
        return {
            "termination_requested": False,
            "terminated": True,
            "return_code": None,
            "sigkill_used": False,
        }
    pgid = process.pid
    requested = process.poll() is None
    sigkill_used = False
    if requested:
        try:
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        sigkill_used = True
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=10)

    group_still_exists = False
    try:
        os.killpg(pgid, 0)
        group_still_exists = True
    except ProcessLookupError:
        group_still_exists = False
    except PermissionError:
        group_still_exists = True
    if group_still_exists:
        sigkill_used = True
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            group_still_exists = False
        time.sleep(0.05)
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            group_still_exists = False
    return {
        "termination_requested": requested,
        "terminated": process.poll() is not None and not group_still_exists,
        "return_code": process.returncode,
        "sigkill_used": sigkill_used,
        "process_group_residual": group_still_exists,
    }


def numeric_probe_value(row: Mapping[str, Any], key: str) -> float:
    value = row.get(key)
    require(isinstance(value, (int, float)) and not isinstance(value, bool), f"PROBE_NUMERIC:{key}")
    converted = float(value)
    require(math.isfinite(converted), f"PROBE_FINITE:{key}")
    return converted


def summarize_runtime_probe(
    probe_path: Path,
    expected_session_id: str,
    require_samples: bool,
    termination: Mapping[str, Any],
) -> dict[str, Any]:
    require(probe_path.is_file(), f"RUNTIME_PROBE_LOG_MISSING:{probe_path}")
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(probe_path.read_text(encoding="utf-8").splitlines(), 1):
        require(line.strip() != "", f"RUNTIME_PROBE_BLANK_LINE:{line_number}")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise VerificationFailure(f"RUNTIME_PROBE_JSON:{line_number}:{error}") from error
        require(isinstance(row, dict), f"RUNTIME_PROBE_OBJECT:{line_number}")
        require(row.get("probe_session_id") == expected_session_id, f"RUNTIME_PROBE_SESSION:{line_number}")
        rows.append(row)
    require(rows, "RUNTIME_PROBE_EMPTY")
    phases: dict[str, int] = {}
    by_pid: dict[int, list[dict[str, Any]]] = {}
    seen_sequences: set[tuple[int, int]] = set()
    numeric_fields = (
        "rss_bytes",
        "heap_used_bytes",
        "heap_total_bytes",
        "external_bytes",
        "cpu_percent_interval",
        "event_loop_delay_mean_ms",
        "event_loop_delay_p95_ms",
        "event_loop_delay_p99_ms",
        "event_loop_delay_max_ms",
    )
    for row in rows:
        pid = row.get("pid")
        sequence = row.get("probe_sequence")
        phase = row.get("phase")
        require(isinstance(pid, int) and pid > 0, "RUNTIME_PROBE_PID")
        require(isinstance(sequence, int) and sequence > 0, "RUNTIME_PROBE_SEQUENCE")
        require(isinstance(phase, str) and phase in {"START", "SAMPLE", "EXIT"}, "RUNTIME_PROBE_PHASE")
        require((pid, sequence) not in seen_sequences, "RUNTIME_PROBE_SEQUENCE_DUPLICATE")
        seen_sequences.add((pid, sequence))
        for key in numeric_fields:
            require(numeric_probe_value(row, key) >= 0, f"RUNTIME_PROBE_NEGATIVE:{key}")
        phases[phase] = phases.get(phase, 0) + 1
        by_pid.setdefault(pid, []).append(row)
    for pid, process_rows in by_pid.items():
        sequences = [int(row["probe_sequence"]) for row in process_rows]
        require(sequences == sorted(sequences), f"RUNTIME_PROBE_SEQUENCE_ORDER:{pid}")
        require(sequences == list(range(1, len(sequences) + 1)), f"RUNTIME_PROBE_SEQUENCE_GAP:{pid}")
    if require_samples:
        require(phases.get("SAMPLE", 0) >= 1, "RUNTIME_PROBE_SAMPLE_MISSING")

    process_summaries: list[dict[str, Any]] = []
    for pid in sorted(by_pid):
        process_rows = by_pid[pid]
        process_summaries.append(
            {
                "pid": pid,
                "sample_count": len(process_rows),
                "first_phase": process_rows[0]["phase"],
                "last_phase": process_rows[-1]["phase"],
                "first_rss_bytes": int(process_rows[0]["rss_bytes"]),
                "last_rss_bytes": int(process_rows[-1]["rss_bytes"]),
                "observed_rss_change_bytes": int(process_rows[-1]["rss_bytes"])
                - int(process_rows[0]["rss_bytes"]),
                "peak_rss_bytes": max(int(row["rss_bytes"]) for row in process_rows),
                "peak_heap_used_bytes": max(int(row["heap_used_bytes"]) for row in process_rows),
                "peak_heap_total_bytes": max(int(row["heap_total_bytes"]) for row in process_rows),
                "peak_event_loop_delay_ms": max(float(row["event_loop_delay_max_ms"]) for row in process_rows),
            }
        )
    return {
        "schema_version": "trace-exploration-v3-runtime-memory-receipt-v1",
        "status": "PASS",
        "checked_utc": utc_now(),
        "probe_session_id": expected_session_id,
        "probe_row_count": len(rows),
        "probe_phase_counts": phases,
        "process_count": len(by_pid),
        "process_ids": sorted(by_pid),
        "peak_rss_bytes": max(int(row["rss_bytes"]) for row in rows),
        "peak_heap_used_bytes": max(int(row["heap_used_bytes"]) for row in rows),
        "peak_heap_total_bytes": max(int(row["heap_total_bytes"]) for row in rows),
        "peak_external_bytes": max(int(row["external_bytes"]) for row in rows),
        "peak_cpu_percent_interval": max(float(row["cpu_percent_interval"]) for row in rows),
        "peak_event_loop_delay_mean_ms": max(float(row["event_loop_delay_mean_ms"]) for row in rows),
        "peak_event_loop_delay_p95_ms": max(float(row["event_loop_delay_p95_ms"]) for row in rows),
        "peak_event_loop_delay_p99_ms": max(float(row["event_loop_delay_p99_ms"]) for row in rows),
        "peak_event_loop_delay_max_ms": max(float(row["event_loop_delay_max_ms"]) for row in rows),
        "process_summaries": process_summaries,
        "termination": dict(termination),
        "performance_interpretation": PERFORMANCE_INTERPRETATION,
    }


def receipt_hashes(output_dir: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for name in RECEIPT_NAMES:
        path = output_dir / name
        if path.is_file() and name != "verification-summary.json":
            hashes[name] = sha256_path(path)
    return hashes


def failure_receipt(schema_version: str, error: BaseException) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "status": "FAIL",
        "checked_utc": utc_now(),
        "error": f"{type(error).__name__}:{error}",
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    default_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=default_root)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--port",
        type=int,
        help="Required nondefault loopback port for a full production run.",
    )
    parser.add_argument("--readiness-timeout-seconds", type=float, default=120.0)
    parser.add_argument("--request-timeout-seconds", type=float, default=10.0)
    parser.add_argument("--concurrency-requests-per-level", type=int, default=100)
    parser.add_argument("--sustained-duration-seconds", type=float, default=10.0)
    parser.add_argument("--sustained-concurrency", type=int, default=10)
    parser.add_argument("--sustained-request-cap", type=int, default=500)
    parser.add_argument("--export-replay-count", type=int, default=5)
    parser.add_argument(
        "--check-artifacts-only",
        action="store_true",
        help="Verify the committed v3 generated artifacts without starting a server.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    output_dir: Path | None = None
    context: ArtifactContext | None = None
    process: subprocess.Popen[str] | None = None
    server_log_handle: Any = None
    server_metadata: dict[str, Any] | None = None
    cases: list[dict[str, Any]] = []
    errors: list[str] = []
    current_phase = "ARTIFACT_CHECK"
    interrupted = False
    full_run_completed = False
    termination: dict[str, Any] = {}
    started_utc = utc_now()
    try:
        output_dir = ensure_output_directory(args.output_dir)
        context = load_artifact_context(args.repo_root)
        artifact_mode = "CHECK_ARTIFACTS_ONLY" if args.check_artifacts_only else "PRODUCTION_HTTP"
        write_json(output_dir / "artifact-check-receipt.json", artifact_receipt(context, artifact_mode))
        cases.append(
            {
                "case_id": "A001",
                "phase": "ARTIFACT_CHECK",
                "method": "FILE",
                "path": str(context.checksum_path.relative_to(context.repo_root)),
                "expected_status": "SHA256_BOUND",
                "actual_status": "SHA256_BOUND",
                "outcome": "PASS",
                "latency_ms": "0.000000",
                "response_bytes": context.read_model_path.stat().st_size,
                "response_sha256": context.read_model_sha256,
                "error": "",
            }
        )
        if args.check_artifacts_only:
            full_run_completed = True
        else:
            validate_full_run_arguments(args)
            assert args.port is not None
            current_phase = "SERVER_STARTUP"
            launched_utc = utc_now()
            process, server_log_handle, server_metadata = launch_server(context, output_dir, args.port)
            readiness = wait_for_readiness(
                process,
                context,
                args.port,
                args.readiness_timeout_seconds,
                args.request_timeout_seconds,
            )
            startup = {
                "schema_version": "trace-exploration-v3-production-startup-receipt-v1",
                "status": "READY",
                "started_utc": launched_utc,
                "ready_utc": utc_now(),
                "api_version": API_VERSION,
                "read_model_sha256": context.read_model_sha256,
                **server_metadata,
                **readiness,
            }
            write_json(output_dir / "startup-receipt.json", startup)

            current_phase = "FUNCTIONAL_HTTP"
            try:
                functional_receipt, stable_reads = run_functional_http(
                    context,
                    args.port,
                    args.request_timeout_seconds,
                    cases,
                )
                write_json(output_dir / "functional-http-receipt.json", functional_receipt)
            except BaseException as error:
                write_json(
                    output_dir / "functional-http-receipt.json",
                    failure_receipt("trace-exploration-v3-functional-http-receipt-v1", error),
                )
                raise

            current_phase = "CONTROL_EXPORT_REPLAY_PRELOAD"
            export_initial, export_body = run_export_replay(
                context,
                args.port,
                args.request_timeout_seconds,
                args.export_replay_count,
                cases,
                "CONTROL_EXPORT_REPLAY_PRELOAD",
                "E-PRE-",
            )

            current_phase = "CONCURRENCY"
            try:
                concurrency_receipt = run_concurrency_matrix(
                    context,
                    args.port,
                    args.request_timeout_seconds,
                    args.concurrency_requests_per_level,
                    stable_reads,
                    cases,
                )
                write_json(output_dir / "concurrency-receipt.json", concurrency_receipt)
            except BaseException as error:
                write_json(
                    output_dir / "concurrency-receipt.json",
                    failure_receipt("trace-exploration-v3-concurrency-receipt-v1", error),
                )
                raise

            current_phase = "SUSTAINED_READ"
            try:
                sustained_receipt = run_sustained_read(
                    context,
                    args.port,
                    args.request_timeout_seconds,
                    args.sustained_duration_seconds,
                    args.sustained_concurrency,
                    args.sustained_request_cap,
                    stable_reads,
                    cases,
                )
                write_json(output_dir / "sustained-read-receipt.json", sustained_receipt)
            except BaseException as error:
                write_json(
                    output_dir / "sustained-read-receipt.json",
                    failure_receipt("trace-exploration-v3-sustained-read-receipt-v1", error),
                )
                raise

            current_phase = "CONTROL_EXPORT_REPLAY_POSTLOAD"
            export_post, _ = run_export_replay(
                context,
                args.port,
                args.request_timeout_seconds,
                2,
                cases,
                "CONTROL_EXPORT_REPLAY_POSTLOAD",
                "E-POST-",
                expected_body=export_body,
            )
            export_receipt = {
                "schema_version": "trace-exploration-v3-control-export-replay-receipt-v1",
                "status": "PASS",
                "checked_utc": utc_now(),
                "preload_replay": export_initial,
                "postload_replay": export_post,
                "preload_and_postload_bytes_equal": True,
                "performance_interpretation": PERFORMANCE_INTERPRETATION,
            }
            write_json(output_dir / "control-export-replay-receipt.json", export_receipt)
            full_run_completed = True
    except BaseException as error:
        interrupted = isinstance(error, (KeyboardInterrupt, SystemExit))
        errors.append(f"{current_phase}:{type(error).__name__}:{error}")
        if output_dir is not None and current_phase == "ARTIFACT_CHECK":
            path = output_dir / "artifact-check-receipt.json"
            if not path.exists():
                write_json(
                    path,
                    failure_receipt("trace-exploration-v3-production-artifact-check-v1", error),
                )
            cases.append(
                {
                    "case_id": "A001",
                    "phase": "ARTIFACT_CHECK",
                    "method": "FILE",
                    "path": "frontend/generated/trace-exploration-v3",
                    "expected_status": "SHA256_BOUND",
                    "actual_status": "FAIL",
                    "outcome": "FAIL",
                    "latency_ms": "0.000000",
                    "response_bytes": 0,
                    "response_sha256": sha256_bytes(b""),
                    "error": f"{type(error).__name__}:{error}",
                }
            )
        if output_dir is not None and current_phase.startswith("CONTROL_EXPORT_REPLAY"):
            path = output_dir / "control-export-replay-receipt.json"
            if not path.exists():
                write_json(
                    path,
                    failure_receipt("trace-exploration-v3-control-export-replay-receipt-v1", error),
                )
        if output_dir is not None and current_phase == "SERVER_STARTUP":
            path = output_dir / "startup-receipt.json"
            if not path.exists():
                write_json(
                    path,
                    failure_receipt("trace-exploration-v3-production-startup-receipt-v1", error),
                )
    finally:
        if not args.check_artifacts_only:
            try:
                termination = terminate_server(process)
                if not termination.get("terminated", False):
                    errors.append("SERVER_TERMINATION:PROCESS_GROUP_RESIDUAL")
            except BaseException as error:
                termination = {
                    "termination_requested": process is not None,
                    "terminated": False,
                    "error": f"{type(error).__name__}:{error}",
                }
                errors.append(f"SERVER_TERMINATION:{type(error).__name__}:{error}")
            if server_log_handle is not None:
                server_log_handle.flush()
                server_log_handle.close()

            if output_dir is not None and server_metadata is not None:
                try:
                    runtime_receipt = summarize_runtime_probe(
                        output_dir / "runtime-probe.jsonl",
                        server_metadata["probe_session_id"],
                        require_samples=full_run_completed,
                        termination=termination,
                    )
                    write_json(output_dir / "runtime-memory-receipt.json", runtime_receipt)
                except BaseException as error:
                    errors.append(f"RUNTIME_PROBE:{type(error).__name__}:{error}")
                    write_json(
                        output_dir / "runtime-memory-receipt.json",
                        failure_receipt("trace-exploration-v3-runtime-memory-receipt-v1", error),
                    )

        if output_dir is not None:
            try:
                write_case_ledger(output_dir / "http-cases.tsv", cases)
            except BaseException as error:
                errors.append(f"CASE_LEDGER:{type(error).__name__}:{error}")
            summary = {
                "schema_version": "trace-exploration-v3-production-http-verification-summary-v1",
                "status": "PASS" if not errors and full_run_completed else "FAIL",
                "mode": "CHECK_ARTIFACTS_ONLY" if args.check_artifacts_only else "PRODUCTION_HTTP",
                "started_utc": started_utc,
                "completed_utc": utc_now(),
                "api_version": API_VERSION,
                "loopback_only": True,
                "external_network_used": False,
                "port": args.port,
                "read_model_sha256": context.read_model_sha256 if context is not None else None,
                "case_count": len(cases),
                "case_pass_count": sum(item.get("outcome") == "PASS" for item in cases),
                "case_failure_count": sum(item.get("outcome") == "FAIL" for item in cases),
                "errors": errors,
                "server_termination": termination if not args.check_artifacts_only else None,
                "performance_interpretation": PERFORMANCE_INTERPRETATION,
                "artifact_sha256": receipt_hashes(output_dir),
            }
            write_json(output_dir / "verification-summary.json", summary)
            print(json.dumps(summary, ensure_ascii=False, sort_keys=True), flush=True)
    if interrupted:
        return 130
    return 0 if not errors and full_run_completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
