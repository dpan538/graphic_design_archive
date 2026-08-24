#!/usr/bin/env python3
"""Release-style provenance receipts for analysis-only affinity benchmarks."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = "trace-exploration-analysis-run-receipt/v1"
IMPLEMENTATION_VERSION = "trace-exploration-analysis-run-receipts-2026-08-24"
SOURCE_COMMIT = "0e311f0b88b4adc3cbfe2080ac98d622013cc6d3"
CONTEXT_PROJECTION_ID = "trace-context-v1"
CONTEXT_PROJECTION_SHA256 = "825f6ecaa9ae1496c8a00ea0fefa5c90319046cf9c1f08a2ef76b9b02df4baeb"
SPACETIME_PROJECTION_ID = "trace-spacetime-v1"
SPACETIME_PROJECTION_SHA256 = "f751b0f432ff684fd1000201b910aa397a4d9965468c2f7dd5022d6a4ae01c06"
EXPLORATION_SIGNAL_REGISTRY_SHA256 = "224aaea1123ad9d5730006aa5e779c17b4673fdfc9ee87988f3f96ac8ce26424"
RESEARCH_RELEASE_ID = "v49-api-contract-fresh-c"
RESEARCH_RELEASE_SHA256 = "4addfdb3cb9314587908096572242b9d63e9cef9e6e1be68c0c646491a43a90a"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class AnalysisReceiptError(ValueError):
    """Raised when a benchmark receipt is incomplete or unpinned."""


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _digest_or_hash(value: str | Mapping[str, Any] | list[Any]) -> str:
    if isinstance(value, str) and SHA256_PATTERN.fullmatch(value):
        return value
    return _sha256_json(value)


def deterministic_receipt_material(receipt: Mapping[str, Any]) -> dict[str, Any]:
    excluded = {"generatedAt", "timestampExcludedFromDeterministicHash", "receiptSha256", "analysisRunId"}
    return {key: value for key, value in receipt.items() if key not in excluded}


def build_analysis_run_receipt(
    *,
    model_id: str,
    model_family: str,
    implementation_version: str,
    parameters: Mapping[str, Any],
    research_release_id: str,
    research_release_sha256: str,
    context_projection_id: str,
    context_projection_sha256: str,
    spacetime_projection_id: str,
    spacetime_projection_sha256: str,
    exploration_signal_registry_sha256: str,
    candidate_index_sha256: str,
    input_cohort_count: int,
    output_summary: str | Mapping[str, Any] | list[Any],
    top_k_artifact: str | Mapping[str, Any] | list[Any],
    source_commit: str = SOURCE_COMMIT,
    execution_seed: int | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    if not model_id.strip() or not model_family.strip() or not implementation_version.strip():
        raise AnalysisReceiptError("model identity/family/version must be nonblank")
    if not COMMIT_PATTERN.fullmatch(source_commit):
        raise AnalysisReceiptError("source commit must be a full lowercase Git SHA")
    hashes = {
        "researchReleaseSha256": research_release_sha256,
        "contextProjectionSha256": context_projection_sha256,
        "spacetimeProjectionSha256": spacetime_projection_sha256,
        "explorationSignalRegistrySha256": exploration_signal_registry_sha256,
        "candidateIndexSha256": candidate_index_sha256,
    }
    if any(not SHA256_PATTERN.fullmatch(str(value)) for value in hashes.values()):
        raise AnalysisReceiptError("every release/projection/index pin must be a SHA-256 digest")
    if input_cohort_count <= 0:
        raise AnalysisReceiptError("input cohort count must be positive")
    if execution_seed is not None and (isinstance(execution_seed, bool) or not isinstance(execution_seed, int)):
        raise AnalysisReceiptError("execution seed must be an integer or null")
    timestamp = generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    receipt: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "modelId": model_id.strip(),
        "modelFamily": model_family.strip(),
        "implementationVersion": implementation_version.strip(),
        "parameterSet": dict(parameters),
        "sourceCommit": source_commit,
        "researchReleaseId": research_release_id.strip(),
        **hashes,
        "researchManifestSha256": research_release_sha256,
        "contextProjectionId": context_projection_id.strip(),
        "spacetimeProjectionId": spacetime_projection_id.strip(),
        "inputCohortCount": input_cohort_count,
        "executionSeed": execution_seed,
        "outputSummarySha256": _digest_or_hash(output_summary),
        "topKArtifactSha256": _digest_or_hash(top_k_artifact),
        "randomnessAffectsAffinity": False,
        "randomnessAffectsCandidateSet": False,
        "fullPairMatrixMaterialized": False,
        "historicalRelation": False,
        "semanticRelation": False,
        "probability": False,
        "generatedAt": timestamp,
        "timestampExcludedFromDeterministicHash": True,
    }
    material = deterministic_receipt_material(receipt)
    digest = _sha256_json(material)
    receipt["analysisRunId"] = f"EXP-RUN:{digest}"
    receipt["receiptSha256"] = digest
    validate_analysis_run_receipt(receipt)
    return receipt


def validate_analysis_run_receipt(receipt: Mapping[str, Any]) -> None:
    required = {
        "schemaVersion",
        "modelId",
        "modelFamily",
        "implementationVersion",
        "parameterSet",
        "sourceCommit",
        "researchReleaseId",
        "researchReleaseSha256",
        "researchManifestSha256",
        "contextProjectionId",
        "contextProjectionSha256",
        "spacetimeProjectionId",
        "spacetimeProjectionSha256",
        "explorationSignalRegistrySha256",
        "candidateIndexSha256",
        "inputCohortCount",
        "executionSeed",
        "outputSummarySha256",
        "topKArtifactSha256",
        "randomnessAffectsAffinity",
        "randomnessAffectsCandidateSet",
        "fullPairMatrixMaterialized",
        "historicalRelation",
        "semanticRelation",
        "probability",
        "generatedAt",
        "timestampExcludedFromDeterministicHash",
        "analysisRunId",
        "receiptSha256",
    }
    missing = required - set(receipt)
    if missing:
        raise AnalysisReceiptError(f"analysis receipt lacks required fields: {sorted(missing)}")
    if receipt.get("schemaVersion") != SCHEMA_VERSION:
        raise AnalysisReceiptError("analysis receipt schema changed")
    if receipt.get("sourceCommit") != SOURCE_COMMIT:
        raise AnalysisReceiptError("analysis receipt is not pinned to the required source commit")
    exact_pins = {
        "researchReleaseId": RESEARCH_RELEASE_ID,
        "researchReleaseSha256": RESEARCH_RELEASE_SHA256,
        "researchManifestSha256": RESEARCH_RELEASE_SHA256,
        "contextProjectionId": CONTEXT_PROJECTION_ID,
        "contextProjectionSha256": CONTEXT_PROJECTION_SHA256,
        "spacetimeProjectionId": SPACETIME_PROJECTION_ID,
        "spacetimeProjectionSha256": SPACETIME_PROJECTION_SHA256,
        "explorationSignalRegistrySha256": EXPLORATION_SIGNAL_REGISTRY_SHA256,
    }
    if any(receipt.get(field) != expected for field, expected in exact_pins.items()):
        raise AnalysisReceiptError("analysis receipt changed a frozen projection/signal-registry pin")
    digest_fields = (
        "researchReleaseSha256",
        "researchManifestSha256",
        "contextProjectionSha256",
        "spacetimeProjectionSha256",
        "explorationSignalRegistrySha256",
        "candidateIndexSha256",
        "outputSummarySha256",
        "topKArtifactSha256",
        "receiptSha256",
    )
    if any(not SHA256_PATTERN.fullmatch(str(receipt.get(field))) for field in digest_fields):
        raise AnalysisReceiptError("analysis receipt contains an invalid digest")
    if any(
        receipt.get(field) is not False
        for field in (
            "randomnessAffectsAffinity",
            "randomnessAffectsCandidateSet",
            "fullPairMatrixMaterialized",
            "historicalRelation",
            "semanticRelation",
            "probability",
        )
    ):
        raise AnalysisReceiptError("analysis receipt crossed a frozen boundary")
    if receipt.get("timestampExcludedFromDeterministicHash") is not True:
        raise AnalysisReceiptError("analysis timestamp is not explicitly excluded from deterministic material")
    expected = _sha256_json(deterministic_receipt_material(receipt))
    if receipt.get("receiptSha256") != expected or receipt.get("analysisRunId") != f"EXP-RUN:{expected}":
        raise AnalysisReceiptError("analysis receipt deterministic binding failed")


def analysis_run_register(receipts: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = []
    for receipt in receipts:
        validate_analysis_run_receipt(receipt)
        rows.append(dict(receipt))
    rows.sort(key=lambda row: (str(row["modelId"]), str(row["analysisRunId"])))
    ids = [str(row["analysisRunId"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise AnalysisReceiptError("analysis run register contains duplicate deterministic runs")
    payload = {
        "schemaVersion": "trace-exploration-analysis-run-register/v1",
        "analysisRunCount": len(rows),
        "rows": rows,
        "receiptFailureCount": 0,
    }
    # The register hash excludes timestamps by hashing each already-bound core.
    payload["registerSha256"] = _sha256_json(
        {
            "schemaVersion": payload["schemaVersion"],
            "receiptSha256": [row["receiptSha256"] for row in rows],
        }
    )
    return payload


def receipt_failure_count(receipts: Iterable[Mapping[str, Any]]) -> int:
    failures = 0
    for receipt in receipts:
        try:
            validate_analysis_run_receipt(receipt)
        except (AnalysisReceiptError, TypeError, ValueError):
            failures += 1
    return failures


def self_test() -> dict[str, Any]:
    digest = "b" * 64
    arguments = dict(
        model_id="M5",
        model_family="GOWER_STYLE_FAMILY_BALANCED",
        implementation_version="test-v1",
        parameters={"temporalVariant": "TEMP-4"},
        research_release_id=RESEARCH_RELEASE_ID,
        research_release_sha256=RESEARCH_RELEASE_SHA256,
        context_projection_id=CONTEXT_PROJECTION_ID,
        context_projection_sha256=CONTEXT_PROJECTION_SHA256,
        spacetime_projection_id=SPACETIME_PROJECTION_ID,
        spacetime_projection_sha256=SPACETIME_PROJECTION_SHA256,
        exploration_signal_registry_sha256=EXPLORATION_SIGNAL_REGISTRY_SHA256,
        candidate_index_sha256=digest,
        input_cohort_count=7_995,
        output_summary={"status": "PASS"},
        top_k_artifact={"rankings": []},
    )
    first = build_analysis_run_receipt(**arguments, generated_at="2026-08-24T00:00:00Z")
    second = build_analysis_run_receipt(**arguments, generated_at="2026-08-24T01:00:00Z")
    if first["receiptSha256"] != second["receiptSha256"] or first["analysisRunId"] != second["analysisRunId"]:
        raise AssertionError("timestamp entered deterministic analysis receipt material")
    register = analysis_run_register([first])
    return {
        "status": "PASS",
        "analysisRunCount": register["analysisRunCount"],
        "analysisRunReceiptFailureCount": receipt_failure_count([first]),
        "timestampExcludedFromDeterministicHash": True,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
