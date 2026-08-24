#!/usr/bin/env python3
"""Deterministic, bounded receipts for local TRACE NLP model runs.

Receipts separate semantic inputs, ranking order, and hardware-dependent
floating-point observations.  They contain no corpus text, full embeddings,
full rankings, generated text, internal UUIDs, or model weights.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import common as governance_common
import corpus_builder
import evaluation_registry
import field_governance
import model_registry


SCHEMA_VERSION = "trace-nlp-model-run-receipt/v1"
IMPLEMENTATION_VERSION = "trace-nlp-model-run-receipts-2026-08-24"
RUN_SCOPES = ("PILOT", "FULL_CORPUS")
RUN_PHASES = ("ENCODING", "INDEXING", "EVALUATION")
RUN_STATUSES = ("COMPLETED", "STOPPED_RESOURCE_GATE", "FAILED_CLOSED")
MAX_RECEIPT_BYTES = 1024 * 1024
MAX_REVIEW_ROWS = 100
TOKEN_COUNT_METHOD = "TRACE_UNICODE_WORD_TOKENS_V1"

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_UUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.I,
)
_PRIVATE = re.compile(r"(?:\bFOL-|\bTRN-OBJ-|\bTRTREE|\bTRBRANCH|file://)", re.I)
_PUBLIC_ID = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
_FORBIDDEN_KEYS = frozenset(
    {
        "text",
        "displayoriginal",
        "semanticnormalized",
        "lexicalcasefolded",
        "documents",
        "embeddings",
        "embeddingmatrix",
        "vectors",
        "pairmatrix",
        "rankings",
        "modelweights",
    }
)


class ModelRunReceiptError(ValueError):
    """Raised when a run receipt would violate provenance/output boundaries."""


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _sha256_json_no_lf(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ModelRunReceiptError(f"{field} must be a nonnegative integer")
    return value


def _require_sha256(value: Any, field: str) -> str:
    normalized = str(value or "")
    if not _SHA256.fullmatch(normalized):
        raise ModelRunReceiptError(f"{field} must be a lowercase SHA-256")
    return normalized


def _scan_bounded(value: Any, *, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            if normalized in _FORBIDDEN_KEYS:
                raise ModelRunReceiptError(f"forbidden full-data key at {path}.{key}")
            _scan_bounded(child, path=f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if len(value) > MAX_REVIEW_ROWS:
            raise ModelRunReceiptError(f"unbounded array at {path}")
        for index, child in enumerate(value):
            _scan_bounded(child, path=f"{path}[{index}]")
    elif isinstance(value, str):
        if _UUID.search(value) or _PRIVATE.search(value):
            raise ModelRunReceiptError(f"private identifier/path in receipt at {path}")


def _corpus_pins(corpus_bundle_receipt: Mapping[str, Any]) -> dict[str, Any]:
    if (
        corpus_bundle_receipt.get("schemaVersion") != "trace-nlp-corpus-bundle/v1"
        or corpus_bundle_receipt.get("policyVersion")
        != governance_common.CORPUS_POLICY_VERSION
        or corpus_bundle_receipt.get("policySha256")
        != field_governance.corpus_policy_sha256()
        or corpus_bundle_receipt.get("fieldRegistryVersion")
        != governance_common.REGISTRY_VERSION
        or corpus_bundle_receipt.get("fieldRegistrySha256")
        != field_governance.registry_sha256()
        or corpus_bundle_receipt.get("normalizationVersion")
        != governance_common.NORMALIZATION_VERSION
    ):
        raise ModelRunReceiptError("corpus governance pins differ from authority")
    boundary = corpus_bundle_receipt.get("boundary")
    if not isinstance(boundary, Mapping):
        raise ModelRunReceiptError("corpus receipt lacks boundary counts")
    public_count = _nonnegative_int(boundary.get("publicObjectCount"), "publicObjectCount")
    held_count = _nonnegative_int(boundary.get("heldObjectCount"), "heldObjectCount")
    held_included = _nonnegative_int(
        boundary.get("heldObjectsIncluded"), "heldObjectsIncluded"
    )
    aspect_counts_raw = corpus_bundle_receipt.get("aspectDocumentCounts")
    if not isinstance(aspect_counts_raw, Mapping) or not aspect_counts_raw:
        raise ModelRunReceiptError("corpus receipt lacks aspect-document counts")
    aspect_counts = {
        str(key): _nonnegative_int(value, f"aspectDocumentCounts.{key}")
        for key, value in sorted(aspect_counts_raw.items())
    }
    if any(value > public_count for value in aspect_counts.values()):
        raise ModelRunReceiptError("an aspect-document count exceeds the public cohort")

    declared_document_sha = _require_sha256(
        corpus_bundle_receipt.get("documentReceiptSha256"),
        "documentReceiptSha256",
    )
    declared_lexical_sha = _require_sha256(
        corpus_bundle_receipt.get("corpusSha256"), "lexical corpusSha256"
    )
    declared_token_count_sha = _require_sha256(
        corpus_bundle_receipt.get("tokenCountReceiptSha256"),
        "tokenCountReceiptSha256",
    )
    token_count_method = str(corpus_bundle_receipt.get("tokenCountMethod", "")).strip()
    if token_count_method != TOKEN_COUNT_METHOD:
        raise ModelRunReceiptError("corpus token-count method differs from authority")
    raw_documents = corpus_bundle_receipt.get("documents")
    if not isinstance(raw_documents, list) or len(raw_documents) != public_count:
        raise ModelRunReceiptError("corpus documents do not match the public cohort")
    ids: list[str] = []
    document_receipts: list[dict[str, Any]] = []
    token_count_receipts: list[dict[str, Any]] = []
    lexical_documents: list[dict[str, Any]] = []
    observed_aspect_counts: dict[str, int] = {key: 0 for key in aspect_counts}
    for raw_document in raw_documents:
        if not isinstance(raw_document, Mapping):
            raise ModelRunReceiptError("corpus document is not a mapping")
        public_id = str(raw_document.get("publicObjectId", ""))
        if (
            not _PUBLIC_ID.fullmatch(public_id)
            or raw_document.get("objectId", public_id) != public_id
        ):
            raise ModelRunReceiptError("corpus receipt contains a non-public identity")
        raw_aspects = raw_document.get("aspects")
        if not isinstance(raw_aspects, Mapping):
            raise ModelRunReceiptError("corpus receipt document lacks aspects")
        receipt_aspects: dict[str, dict[str, Any]] = {}
        token_aspects: dict[str, dict[str, Any]] = {}
        lexical_aspects: dict[str, dict[str, Any]] = {}
        for aspect_id, raw_aspect in sorted(raw_aspects.items()):
            if aspect_id not in aspect_counts or not isinstance(raw_aspect, Mapping):
                raise ModelRunReceiptError("corpus receipt contains an unknown aspect")
            observed_aspect_counts[aspect_id] += 1
            original_hash = _require_sha256(
                raw_aspect.get("originalTextHash"), "originalTextHash"
            )
            semantic_hash = _require_sha256(
                raw_aspect.get("semanticNormalizedHash"),
                "semanticNormalizedHash",
            )
            lexical_hash = _require_sha256(
                raw_aspect.get("lexicalCasefoldedHash"),
                "lexicalCasefoldedHash",
            )
            source_field_ids = raw_aspect.get("sourceFieldIds")
            source_field_roles = raw_aspect.get("sourceFieldRoles")
            if (
                not isinstance(source_field_ids, list)
                or not source_field_ids
                or not isinstance(source_field_roles, list)
                or not source_field_roles
                or any(not isinstance(value, str) or not value for value in source_field_ids)
                or any(not isinstance(value, str) or not value for value in source_field_roles)
            ):
                raise ModelRunReceiptError("corpus lexical source-field provenance is invalid")
            aspect_token_method = str(raw_aspect.get("tokenCountMethod", "")).strip()
            if aspect_token_method != token_count_method:
                raise ModelRunReceiptError("corpus aspect token-count method differs")
            receipt_aspects[str(aspect_id)] = {
                "originalTextHash": original_hash,
                "semanticNormalizedHash": semantic_hash,
                "lexicalCasefoldedHash": lexical_hash,
                "characterCount": _nonnegative_int(
                    raw_aspect.get("characterCount"), "characterCount"
                ),
                "languageScriptState": raw_aspect.get("languageScriptState"),
                "modelInputTokenCap": _nonnegative_int(
                    raw_aspect.get("modelInputTokenCap"), "modelInputTokenCap"
                ),
            }
            token_aspects[str(aspect_id)] = {
                "lexicalCasefoldedHash": lexical_hash,
                "tokenCount": _nonnegative_int(
                    raw_aspect.get("tokenCount"), "tokenCount"
                ),
                "tokenCountMethod": aspect_token_method,
            }
            lexical_aspects[str(aspect_id)] = {
                "originalTextHash": original_hash,
                "semanticNormalizedHash": semantic_hash,
                "lexicalCasefoldedHash": lexical_hash,
                "sourceFieldIds": list(source_field_ids),
                "sourceFieldRoles": list(source_field_roles),
            }
        ids.append(public_id)
        document_receipts.append(
            {"publicObjectId": public_id, "aspects": receipt_aspects}
        )
        token_count_receipts.append(
            {"publicObjectId": public_id, "aspects": token_aspects}
        )
        lexical_documents.append({"objectId": public_id, "aspects": lexical_aspects})
    if tuple(ids) != governance_common.load_public_ids():
        raise ModelRunReceiptError("corpus receipt identities differ from the public ledger")
    if observed_aspect_counts != aspect_counts:
        raise ModelRunReceiptError("corpus aspect counts differ from its documents")
    if sha256_json(document_receipts) != declared_document_sha:
        raise ModelRunReceiptError("corpus document receipt SHA-256 is unauthenticated")
    if sha256_json(token_count_receipts) != declared_token_count_sha:
        raise ModelRunReceiptError("corpus token-count receipt SHA-256 is unauthenticated")
    lexical_material = {
        "schemaVersion": corpus_bundle_receipt.get("schemaVersion"),
        "policyVersion": corpus_bundle_receipt.get("policyVersion"),
        "policySha256": corpus_bundle_receipt.get("policySha256"),
        "fieldRegistryVersion": corpus_bundle_receipt.get("fieldRegistryVersion"),
        "fieldRegistrySha256": corpus_bundle_receipt.get("fieldRegistrySha256"),
        "normalizationVersion": corpus_bundle_receipt.get("normalizationVersion"),
        "objectIds": ids,
        "documents": lexical_documents,
    }
    if sha256_json(lexical_material) != declared_lexical_sha:
        raise ModelRunReceiptError("lexical corpus SHA-256 is unauthenticated")
    canonical_ids_sha = _sha256_json_no_lf(ids)

    pins = {
        "schemaVersion": corpus_bundle_receipt.get("schemaVersion"),
        "policyVersion": corpus_bundle_receipt.get("policyVersion"),
        "policySha256": _require_sha256(
            corpus_bundle_receipt.get("policySha256"), "policySha256"
        ),
        "fieldRegistryVersion": corpus_bundle_receipt.get("fieldRegistryVersion"),
        "fieldRegistrySha256": _require_sha256(
            corpus_bundle_receipt.get("fieldRegistrySha256"), "fieldRegistrySha256"
        ),
        "normalizationVersion": corpus_bundle_receipt.get("normalizationVersion"),
        "documentReceiptSha256": declared_document_sha,
        "lexicalCorpusSha256": declared_lexical_sha,
        "tokenCountMethod": token_count_method,
        "tokenCountReceiptSha256": declared_token_count_sha,
        "canonicalPublicIdsSha256": canonical_ids_sha,
        "boundary": {
            "publicObjectCount": public_count,
            "heldObjectCount": held_count,
            "heldObjectsIncluded": held_included,
        },
        "aspectDocumentCounts": aspect_counts,
    }
    if (
        pins["schemaVersion"] != "trace-nlp-corpus-bundle/v1"
        or public_count != 7_995
        or held_count != 7_928
        or held_included != 0
    ):
        raise ModelRunReceiptError("corpus boundary/schema changed")
    return pins


def _artifact_pins(
    candidate_id: str,
    artifact_verification: Mapping[str, Any],
    *,
    require_execution_ready: bool,
) -> dict[str, Any]:
    spec = model_registry.get_model(candidate_id)
    if require_execution_ready and (
        spec.execution_state != model_registry.EXECUTION_READY
        or candidate_id not in model_registry.FULL_CORPUS_EXECUTION_SHORTLIST
        or not spec.production_eligible
        or spec.trust_remote_code_required
        or spec.pickle_weight_present
    ):
        raise ModelRunReceiptError("completed run uses a non-executable candidate")
    if (
        artifact_verification.get("schemaVersion")
        != "trace-nlp-model-artifact-verification/v1"
        or artifact_verification.get("candidateId") != candidate_id
        or artifact_verification.get("modelId") != spec.model_id
        or artifact_verification.get("revision") != spec.revision
        or artifact_verification.get("tokenizerRevision") != spec.tokenizer_revision
    ):
        raise ModelRunReceiptError("artifact verification does not match the candidate")
    expected_artifacts = [
        {
            "relativePath": artifact.relative_path,
            "byteCount": artifact.byte_count,
            "digestAlgorithm": artifact.digest_algorithm,
            "digest": artifact.digest,
            "role": artifact.role,
        }
        for artifact in spec.artifacts
        if artifact.required_for_execution
    ]
    expected_artifacts.sort(key=lambda row: row["relativePath"])
    raw_artifacts = artifact_verification.get("artifacts")
    if not isinstance(raw_artifacts, list):
        raise ModelRunReceiptError("artifact verification lacks exact artifact rows")
    observed_artifacts = [dict(row) for row in raw_artifacts if isinstance(row, Mapping)]
    observed_artifacts.sort(key=lambda row: str(row.get("relativePath", "")))
    if len(observed_artifacts) != len(raw_artifacts) or observed_artifacts != expected_artifacts:
        raise ModelRunReceiptError("artifact verification rows differ from the registry")
    artifact_count = _nonnegative_int(
        artifact_verification.get("artifactCount"), "artifactCount"
    )
    verified_bytes = _nonnegative_int(
        artifact_verification.get("verifiedBytes"), "verifiedBytes"
    )
    if artifact_count != len(expected_artifacts) or verified_bytes != spec.minimal_snapshot_bytes:
        raise ModelRunReceiptError("artifact verification count/bytes differ from the registry")
    if (
        artifact_verification.get("offlineOnly") is not True
        or artifact_verification.get("trustRemoteCode") is not False
    ):
        raise ModelRunReceiptError("artifact verification is not offline/no-remote-code")
    verification_material = {
        "schemaVersion": "trace-nlp-model-artifact-verification/v1",
        "candidateId": candidate_id,
        "modelId": spec.model_id,
        "revision": spec.revision,
        "tokenizerRevision": spec.tokenizer_revision,
        "artifactCount": artifact_count,
        "verifiedBytes": verified_bytes,
        "artifacts": observed_artifacts,
        "offlineOnly": True,
        "trustRemoteCode": False,
    }
    verification_sha = _require_sha256(
        artifact_verification.get("verificationSha256"),
        "artifact verification SHA-256",
    )
    if _sha256_json_no_lf(verification_material) != verification_sha:
        raise ModelRunReceiptError("artifact verification SHA-256 is unauthenticated")
    return {
        "candidateId": candidate_id,
        "modelId": spec.model_id,
        "revision": spec.revision,
        "tokenizerRevision": spec.tokenizer_revision,
        "licenseSpdx": spec.license_spdx,
        "eligibility": spec.eligibility,
        "productionEligible": spec.production_eligible,
        "trustRemoteCodeRequired": spec.trust_remote_code_required,
        "customCodeReviewed": spec.custom_code_reviewed,
        "executionState": spec.execution_state,
        "artifactCount": artifact_count,
        "verifiedBytes": verified_bytes,
        "verificationSha256": verification_sha,
    }


def _encoding_pins(
    candidate_id: str, encoding_receipt: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    spec = model_registry.get_model(candidate_id)
    if (
        encoding_receipt.get("methodId") != candidate_id
        or encoding_receipt.get("modelId") != spec.model_id
        or encoding_receipt.get("modelRevision") != spec.revision
        or encoding_receipt.get("tokenizerRevision") != spec.tokenizer_revision
    ):
        raise ModelRunReceiptError("encoding receipt does not match the candidate")
    tokenization = encoding_receipt.get("tokenization")
    performance = encoding_receipt.get("performance")
    runtime = encoding_receipt.get("runtime")
    if not isinstance(tokenization, Mapping) or not isinstance(performance, Mapping):
        raise ModelRunReceiptError("encoding receipt lacks tokenization/performance")
    if not isinstance(runtime, Mapping):
        raise ModelRunReceiptError("encoding receipt lacks actual runtime evidence")
    semantic = {
        "artifactVerificationSha256": _require_sha256(
            encoding_receipt.get("artifactVerificationSha256"),
            "encoding artifact verification SHA-256",
        ),
        "corpusSha256": _require_sha256(
            encoding_receipt.get("corpusSha256"), "encoding corpusSha256"
        ),
        "lexicalCorpusSha256": _require_sha256(
            encoding_receipt.get("lexicalCorpusSha256"),
            "encoding lexicalCorpusSha256",
        ),
        "tokenCountReceiptSha256": _require_sha256(
            encoding_receipt.get("tokenCountReceiptSha256"),
            "encoding tokenCountReceiptSha256",
        ),
        "corpusSliceSha256": _require_sha256(
            encoding_receipt.get("corpusSliceSha256"), "corpus slice SHA-256"
        ),
        "inputVariant": encoding_receipt.get("inputVariant"),
        "aspectIds": encoding_receipt.get("aspectIds"),
        "fullCorpus": encoding_receipt.get("fullCorpus"),
        "fullPublicCohort": encoding_receipt.get("fullPublicCohort"),
        "fullAspectCohort": encoding_receipt.get("fullAspectCohort"),
        "objectCount": encoding_receipt.get("objectCount"),
        "aspectAvailableObjectCount": encoding_receipt.get(
            "aspectAvailableObjectCount"
        ),
        "aspectUnavailableObjectCount": encoding_receipt.get(
            "aspectUnavailableObjectCount"
        ),
        "defaultQueryCount": encoding_receipt.get("defaultQueryCount"),
        "defaultQueryPublicIdsSha256": _require_sha256(
            encoding_receipt.get("defaultQueryPublicIdsSha256"),
            "default query ID SHA-256",
        ),
        "missingAspectRowsZero": encoding_receipt.get("missingAspectRowsZero"),
        "canonicalPublicIdsSha256": _require_sha256(
            encoding_receipt.get("canonicalPublicIdsSha256"), "canonical ID SHA-256"
        ),
        "semanticInputSha256": _require_sha256(
            encoding_receipt.get("semanticInputSha256"), "semantic input SHA-256"
        ),
        "lengthBucketed": encoding_receipt.get("lengthBucketed"),
        "lengthBucketPermutationSha256": _require_sha256(
            encoding_receipt.get("lengthBucketPermutationSha256"),
            "length-bucket permutation SHA-256",
        ),
        "canonicalOrderRestored": encoding_receipt.get("canonicalOrderRestored"),
        "batchSize": encoding_receipt.get("batchSize"),
        "maxLength": encoding_receipt.get("maxLength"),
        "governedEffectiveMaxLength": encoding_receipt.get(
            "governedEffectiveMaxLength"
        ),
        "officialModelMaximumInputTokens": encoding_receipt.get(
            "officialModelMaximumInputTokens"
        ),
        "pooling": encoding_receipt.get("pooling"),
        "normalization": encoding_receipt.get("normalization"),
        "weightDtype": encoding_receipt.get("weightDtype"),
        "executionDtype": encoding_receipt.get("executionDtype"),
        "device": encoding_receipt.get("device"),
        "localFilesOnly": encoding_receipt.get("localFilesOnly"),
        "trustRemoteCode": encoding_receipt.get("trustRemoteCode"),
        "tokenization": dict(tokenization),
        "tokenizerPaddingSide": encoding_receipt.get("tokenizerPaddingSide"),
        "tokenizerTruncationSide": encoding_receipt.get("tokenizerTruncationSide"),
    }
    if (
        semantic["device"] != "cpu"
        or semantic["localFilesOnly"] is not True
        or semantic["trustRemoteCode"] is not False
        or semantic["lengthBucketed"] is not True
        or semantic["canonicalOrderRestored"] is not True
    ):
        raise ModelRunReceiptError("offline/CPU/order execution contract changed")
    count_fields = (
        "objectCount",
        "aspectAvailableObjectCount",
        "aspectUnavailableObjectCount",
        "defaultQueryCount",
        "batchSize",
        "maxLength",
        "governedEffectiveMaxLength",
        "officialModelMaximumInputTokens",
    )
    for field in count_fields:
        semantic[field] = _nonnegative_int(semantic[field], f"encoding {field}")
    if semantic["objectCount"] <= 0:
        raise ModelRunReceiptError("encoding object count must be positive")
    if (
        semantic["aspectAvailableObjectCount"]
        + semantic["aspectUnavailableObjectCount"]
        != semantic["objectCount"]
        or semantic["defaultQueryCount"] != semantic["aspectAvailableObjectCount"]
    ):
        raise ModelRunReceiptError("encoding cohort counts are not conserved")
    if (
        semantic["semanticInputSha256"] != semantic["corpusSliceSha256"]
        or semantic["missingAspectRowsZero"] is not True
    ):
        raise ModelRunReceiptError("encoding semantic slice/missingness contract changed")
    aspect_ids = semantic["aspectIds"]
    if (
        not isinstance(aspect_ids, list)
        or len(aspect_ids) != 1
        or not isinstance(aspect_ids[0], str)
        or not aspect_ids[0]
    ):
        raise ModelRunReceiptError("dense encoding must identify exactly one aspect")
    if any(
        not isinstance(semantic[field], bool)
        for field in ("fullCorpus", "fullPublicCohort", "fullAspectCohort")
    ):
        raise ModelRunReceiptError("encoding full-cohort declarations must be booleans")
    if (
        semantic["fullCorpus"] is not semantic["fullPublicCohort"]
        or semantic["fullCorpus"] is not semantic["fullAspectCohort"]
        or semantic["fullCorpus"] is not (semantic["objectCount"] == 7_995)
    ):
        raise ModelRunReceiptError("encoding full-cohort declarations conflict")
    if (
        semantic["pooling"] != spec.pooling
        or semantic["normalization"] != spec.normalization
        or semantic["weightDtype"] != spec.weight_dtype
        or semantic["executionDtype"] != spec.execution_dtype_cpu
        or semantic["officialModelMaximumInputTokens"] != spec.maximum_input_tokens
        or semantic["maxLength"] <= 0
        or semantic["maxLength"] > semantic["governedEffectiveMaxLength"]
    ):
        raise ModelRunReceiptError("encoding model semantics differ from the registry")
    if (
        encoding_receipt.get("hostedInferenceCalls") != 0
        or encoding_receipt.get("implicitOutputWrites") != 0
    ):
        raise ModelRunReceiptError("encoding receipt does not prove local/no-write execution")
    packages = runtime.get("packages")
    if (
        runtime.get("python") != model_registry.RUNTIME_PINS["python"]
        or not isinstance(packages, Mapping)
        or any(
            packages.get(name) != expected
            for name, expected in model_registry.RUNTIME_PINS.items()
            if name != "python"
        )
    ):
        raise ModelRunReceiptError("encoding runtime differs from exact executed pins")
    floating = {
        "embeddingObservationSha256": _require_sha256(
            encoding_receipt.get("embeddingObservationSha256"),
            "embedding observation SHA-256",
        ),
        "embeddingDimension": _nonnegative_int(
            encoding_receipt.get("embeddingDimension"), "embeddingDimension"
        ),
        "embeddingBytesInMemory": _nonnegative_int(
            encoding_receipt.get("embeddingBytesInMemory"), "embeddingBytesInMemory"
        ),
        "performance": dict(performance),
        "runtime": dict(runtime),
        "crossHardwareByteIdentityPromised": False,
    }
    if floating["embeddingDimension"] != spec.embedding_dimension:
        raise ModelRunReceiptError("encoding dimension differs from the registry")
    expected_embedding_bytes = (
        semantic["objectCount"] * floating["embeddingDimension"] * 4
    )
    if floating["embeddingBytesInMemory"] != expected_embedding_bytes:
        raise ModelRunReceiptError("encoding byte count differs from float32 cohort shape")
    return semantic, floating


def _ranking_pins(
    ranking_summary: Mapping[str, Any] | None,
    *,
    candidate_id: str,
    semantic: Mapping[str, Any],
    floating: Mapping[str, Any],
) -> dict[str, Any] | None:
    if ranking_summary is None:
        return None
    if "rankings" in ranking_summary:
        raise ModelRunReceiptError("full rankings cannot enter a run receipt")
    method_id = ranking_summary.get("methodId")
    top_k = _nonnegative_int(ranking_summary.get("topK"), "ranking topK")
    query_count = _nonnegative_int(
        ranking_summary.get("queryCount"), "ranking queryCount"
    )
    object_count = _nonnegative_int(
        ranking_summary.get("objectCount"), "ranking objectCount"
    )
    if method_id != candidate_id:
        raise ModelRunReceiptError("ranking method differs from the encoded candidate")
    if not 1 <= top_k <= 50 or top_k >= object_count:
        raise ModelRunReceiptError("ranking top-k is outside the bounded cohort")
    if query_count <= 0 or query_count > int(semantic["aspectAvailableObjectCount"]):
        raise ModelRunReceiptError("ranking query count is outside the encoded cohort")
    if object_count != semantic["objectCount"]:
        raise ModelRunReceiptError("ranking object count differs from encoding")
    if (
        ranking_summary.get("corpusSha256") != semantic["lexicalCorpusSha256"]
        or ranking_summary.get("inputVariant") != semantic["inputVariant"]
        or ranking_summary.get("aspectIds") != semantic["aspectIds"]
        or ranking_summary.get("fullCorpus") is not semantic["fullCorpus"]
    ):
        raise ModelRunReceiptError("ranking identity is not cross-bound to encoding")
    if semantic["fullAspectCohort"] and query_count != semantic["aspectAvailableObjectCount"]:
        raise ModelRunReceiptError("full-aspect ranking omits encoded queries")
    if (
        ranking_summary.get("pairMatrixMaterialized") is not False
        or ranking_summary.get("fullRankingsCommitted") is not False
    ):
        raise ModelRunReceiptError("ranking summary violates matrix/retention boundaries")
    embedding_sha = _require_sha256(
        ranking_summary.get("embeddingObservationSha256"),
        "ranking embedding observation SHA-256",
    )
    if embedding_sha != floating["embeddingObservationSha256"]:
        raise ModelRunReceiptError("ranking embedding hash differs from encoding")
    return {
        "methodId": method_id,
        "corpusSha256": semantic["lexicalCorpusSha256"],
        "inputVariant": semantic["inputVariant"],
        "aspectIds": list(semantic["aspectIds"]),
        "fullCorpus": semantic["fullCorpus"],
        "objectCount": object_count,
        "embeddingObservationSha256": embedding_sha,
        "indexSha256": _require_sha256(
            ranking_summary.get("indexSha256"), "index SHA-256"
        ),
        "rankingIdsSha256": _require_sha256(
            ranking_summary.get("rankingIdsSha256"), "ranking ID SHA-256"
        ),
        "scoreObservationSha256": _require_sha256(
            ranking_summary.get("scoreObservationSha256"),
            "score observation SHA-256",
        ),
        "topK": top_k,
        "queryCount": query_count,
        "tieBreak": "score-desc/public-ID-asc",
        "pairMatrixMaterialized": ranking_summary.get("pairMatrixMaterialized"),
        "fullRankingsCommitted": ranking_summary.get("fullRankingsCommitted"),
    }


def _bounded_optional(value: Mapping[str, Any] | None, label: str) -> dict[str, Any] | None:
    if value is None:
        return None
    copied = json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
    _scan_bounded(copied, path=f"$.{label}")
    return copied


def _authenticated_summary(
    value: Mapping[str, Any] | None,
    *,
    label: str,
    digest_field: str,
) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ModelRunReceiptError(f"{label} summary is not a mapping")
    copied = json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
    supplied_digest = _require_sha256(copied.pop(digest_field, None), digest_field)
    if _sha256_json_no_lf(copied) != supplied_digest:
        raise ModelRunReceiptError(f"{label} summary digest is unauthenticated")
    authenticated = {**copied, digest_field: supplied_digest}
    _scan_bounded(authenticated, path=f"$.{label}")
    return authenticated


def _bound_evaluation_summaries(
    *,
    candidate_id: str,
    semantic: Mapping[str, Any],
    ranking: Mapping[str, Any] | None,
    cross_language_summary: Mapping[str, Any] | None,
    hubness_anisotropy_summary: Mapping[str, Any] | None,
    robustness_summary: Mapping[str, Any] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    if ranking is None and any(
        value is not None
        for value in (
            cross_language_summary,
            hubness_anisotropy_summary,
            robustness_summary,
        )
    ):
        raise ModelRunReceiptError("evaluation summaries lack a ranking receipt")
    expected = {
        "methodId": candidate_id,
        "corpusSha256": semantic["lexicalCorpusSha256"],
        "inputVariant": semantic["inputVariant"],
        "aspectId": semantic["aspectIds"][0],
    }
    cross = _authenticated_summary(
        cross_language_summary,
        label="crossLanguage",
        digest_field="receiptSha256",
    )
    if cross is not None and (
        cross.get("schemaVersion") != "trace-nlp-cross-language-evaluation/v1"
        or cross.get("status") not in {"PASS", "NOT_RUN"}
        or any(cross.get(key) != value for key, value in expected.items())
        or cross.get("evaluationRegistrySha256")
        != evaluation_registry.evaluation_registry_sha256()
    ):
        raise ModelRunReceiptError("cross-language summary is not governance-bound")
    hubness = _authenticated_summary(
        hubness_anisotropy_summary,
        label="hubnessAnisotropy",
        digest_field="diagnosticSha256",
    )
    if hubness is not None and (
        hubness.get("schemaVersion") != "trace-nlp-hubness-anisotropy/v1"
        or hubness.get("status") not in {"PASS", "NOT_RUN"}
        or any(hubness.get(key) != value for key, value in expected.items())
        or hubness.get("indexSha256") != ranking["indexSha256"]
    ):
        raise ModelRunReceiptError("hubness/anisotropy summary is not ranking-bound")
    if hubness is not None:
        hubness_rows = hubness.get("hubness")
        anisotropy = hubness.get("anisotropy")
        if (
            not isinstance(hubness_rows, Mapping)
            or not isinstance(anisotropy, Mapping)
            or hubness.get("coreDiagnosticsComputed") is not True
            or anisotropy.get("pairMatrixMaterialized") is not False
            or hubness["status"] == "PASS"
            and (
                hubness_rows.get("associationStatus") != "PASS"
                or anisotropy.get("status") != "PASS"
            )
        ):
            raise ModelRunReceiptError("hubness/anisotropy summary shape is incomplete")
    robustness = _authenticated_summary(
        robustness_summary,
        label="robustness",
        digest_field="suiteSha256",
    )
    if robustness is not None and (
        robustness.get("schemaVersion")
        != "trace-nlp-robustness-ablation-suite/v1"
        or robustness.get("status")
        not in {"COMPLETED", "NOT_RUN", "STOPPED_RECOVERABLE_CHECKPOINT"}
        or any(robustness.get(key) != value for key, value in expected.items())
        or robustness.get("indexSha256") != ranking["indexSha256"]
        or robustness.get("rankingIdsSha256") != ranking["rankingIdsSha256"]
        or robustness.get("selectionPerformed") is not False
        or robustness.get("fusionSelected") is not False
    ):
        raise ModelRunReceiptError("robustness summary is not ranking-bound")
    if robustness is not None:
        declared = robustness.get("declaredAblationIds")
        executed = robustness.get("executedAblationIds")
        not_run = robustness.get("notRunAblationIds")
        comparisons = robustness.get("comparisons")
        if any(
            not isinstance(value, list)
            for value in (declared, executed, not_run, comparisons)
        ) or robustness["status"] == "COMPLETED" and (
            not_run or executed != declared or len(comparisons) != len(executed)
        ):
            raise ModelRunReceiptError("robustness suite completion is not conserved")
    return cross, hubness, robustness


def build_model_run_receipt(
    *,
    candidate_id: str,
    run_scope: str,
    run_phase: str,
    status: str,
    corpus_bundle_receipt: Mapping[str, Any],
    artifact_verification: Mapping[str, Any],
    encoding_receipt: Mapping[str, Any],
    ranking_summary: Mapping[str, Any] | None = None,
    cross_language_summary: Mapping[str, Any] | None = None,
    hubness_anisotropy_summary: Mapping[str, Any] | None = None,
    robustness_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if run_scope not in RUN_SCOPES or run_phase not in RUN_PHASES or status not in RUN_STATUSES:
        raise ModelRunReceiptError("invalid run scope, phase, or status")
    corpus = _corpus_pins(corpus_bundle_receipt)
    artifact = _artifact_pins(
        candidate_id,
        artifact_verification,
        require_execution_ready=status == "COMPLETED",
    )
    semantic, floating = _encoding_pins(candidate_id, encoding_receipt)
    if semantic["artifactVerificationSha256"] != artifact["verificationSha256"]:
        raise ModelRunReceiptError("encoding is not bound to the verified model artifacts")
    if semantic["corpusSha256"] != corpus["documentReceiptSha256"]:
        raise ModelRunReceiptError("encoding is not bound to the governed corpus receipt")
    if semantic["lexicalCorpusSha256"] != corpus["lexicalCorpusSha256"]:
        raise ModelRunReceiptError("encoding is not bound to the lexical corpus identity")
    if semantic["tokenCountReceiptSha256"] != corpus["tokenCountReceiptSha256"]:
        raise ModelRunReceiptError("encoding is not bound to the token-count receipt")
    if (
        semantic["fullCorpus"]
        and (
            corpus["canonicalPublicIdsSha256"] is None
            or semantic["canonicalPublicIdsSha256"]
            != corpus["canonicalPublicIdsSha256"]
        )
    ):
        raise ModelRunReceiptError("encoding public-ID cohort differs from corpus")
    aspect_id = semantic["aspectIds"][0]
    expected_aspect_count = corpus["aspectDocumentCounts"].get(aspect_id)
    if expected_aspect_count is None:
        raise ModelRunReceiptError("encoding aspect is absent from corpus governance")
    if semantic["fullCorpus"] and (
        semantic["objectCount"] != corpus["boundary"]["publicObjectCount"]
        or semantic["aspectAvailableObjectCount"] != expected_aspect_count
    ):
        raise ModelRunReceiptError("encoding cohort counts differ from corpus governance")
    ranking = _ranking_pins(
        ranking_summary,
        candidate_id=candidate_id,
        semantic=semantic,
        floating=floating,
    )
    cross_language, hubness_anisotropy, robustness = _bound_evaluation_summaries(
        candidate_id=candidate_id,
        semantic=semantic,
        ranking=ranking,
        cross_language_summary=cross_language_summary,
        hubness_anisotropy_summary=hubness_anisotropy_summary,
        robustness_summary=robustness_summary,
    )
    if run_scope == "FULL_CORPUS" and (
        semantic["fullCorpus"] is not True
        or semantic["fullPublicCohort"] is not True
        or semantic["fullAspectCohort"] is not True
        or semantic["objectCount"] != 7_995
        or semantic["defaultQueryCount"] != semantic["aspectAvailableObjectCount"]
        or semantic["missingAspectRowsZero"] is not True
    ):
        raise ModelRunReceiptError("full-corpus receipt is bound to a pilot encoding")
    if run_phase in {"INDEXING", "EVALUATION"} and ranking is None:
        raise ModelRunReceiptError("index/evaluation phase lacks a bounded ranking summary")
    if run_phase == "EVALUATION" and status == "COMPLETED":
        if hubness_anisotropy is None or robustness is None:
            raise ModelRunReceiptError(
                "completed shortlist evaluation cannot omit hubness or robustness"
            )
        if hubness_anisotropy.get("status") != "PASS":
            raise ModelRunReceiptError(
                "completed shortlist evaluation has incomplete hubness/anisotropy"
            )
        if robustness.get("status") != "COMPLETED":
            raise ModelRunReceiptError(
                "completed shortlist evaluation has incomplete robustness"
            )
    plan = {
        "candidateId": candidate_id,
        "runScope": run_scope,
        "runPhase": run_phase,
        "modelRevision": artifact["revision"],
        "tokenizerRevision": artifact["tokenizerRevision"],
        "corpusPolicySha256": corpus["policySha256"],
        "fieldRegistrySha256": corpus["fieldRegistrySha256"],
        "corpusDocumentReceiptSha256": corpus["documentReceiptSha256"],
        "lexicalCorpusSha256": corpus["lexicalCorpusSha256"],
        "tokenCountReceiptSha256": corpus["tokenCountReceiptSha256"],
        "inputVariant": semantic["inputVariant"],
        "aspectIds": semantic["aspectIds"],
        "batchSize": semantic["batchSize"],
        "maxLength": semantic["maxLength"],
        "device": semantic["device"],
        "localFilesOnly": True,
    }
    plan_sha = sha256_json(plan)
    semantic_receipt = {
        "modelArtifacts": artifact,
        "corpus": corpus,
        "encoding": semantic,
    }
    ranking_receipt = ranking
    floating_receipt = floating
    material = {
        "schemaVersion": SCHEMA_VERSION,
        "implementationVersion": IMPLEMENTATION_VERSION,
        "runId": f"{candidate_id}-{run_scope}-{plan_sha[:16]}",
        "status": status,
        "plan": plan,
        "planSha256": plan_sha,
        "semanticReceipt": semantic_receipt,
        "semanticReceiptSha256": sha256_json(semantic_receipt),
        "rankingReceipt": ranking_receipt,
        "rankingReceiptSha256": (
            sha256_json(ranking_receipt) if ranking_receipt is not None else None
        ),
        "floatingPointObservation": floating_receipt,
        "floatingPointObservationSha256": sha256_json(floating_receipt),
        "crossLanguage": cross_language,
        "hubnessAnisotropy": hubness_anisotropy,
        "robustness": robustness,
        "externalInferenceApiCallCount": 0,
        "generatedTextTransformationCount": 0,
        "heldObjectsIncluded": 0,
        "modelWeightsCommitted": False,
        "fullEmbeddingMatrixCommitted": False,
        "fullRankingsCommitted": False,
        "historicalRelationProduced": False,
        "probabilityProduced": False,
        "structuredNlpFusionSelected": False,
    }
    _scan_bounded(material)
    encoded = canonical_json_bytes(material)
    if len(encoded) > MAX_RECEIPT_BYTES:
        raise ModelRunReceiptError("bounded run receipt exceeds 1 MiB")
    return {
        **material,
        "runReceiptSha256": hashlib.sha256(encoded).hexdigest(),
        "runReceiptBytes": len(encoded),
    }


def _approved_temp_path(path: str | Path) -> Path:
    raw = Path(path).expanduser()
    if not raw.is_absolute():
        raise ModelRunReceiptError("receipt output path must be explicit and absolute")
    target = raw.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if target != temp_root and temp_root not in target.parents:
        raise ModelRunReceiptError("run receipt may be written only below the OS temp root")
    if target.suffix != ".json" or target.exists():
        raise ModelRunReceiptError("receipt path must be a new .json temp file")
    return target


def write_run_receipt_temp(receipt: Mapping[str, Any], path: str | Path) -> dict[str, Any]:
    target = _approved_temp_path(path)
    payload = canonical_json_bytes(receipt)
    if len(payload) > MAX_RECEIPT_BYTES:
        raise ModelRunReceiptError("bounded run receipt exceeds 1 MiB")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as handle:
        handle.write(payload)
    return {
        "path": str(target),
        "byteCount": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "temporary": True,
        "committableAfterAudit": True,
    }


def run_self_tests() -> dict[str, Any]:
    def artifact_receipt(candidate_id: str) -> dict[str, Any]:
        candidate = model_registry.get_model(candidate_id)
        rows = [
            {
                "relativePath": item.relative_path,
                "byteCount": item.byte_count,
                "digestAlgorithm": item.digest_algorithm,
                "digest": item.digest,
                "role": item.role,
            }
            for item in candidate.artifacts
            if item.required_for_execution
        ]
        rows.sort(key=lambda row: row["relativePath"])
        material = {
            "schemaVersion": "trace-nlp-model-artifact-verification/v1",
            "candidateId": candidate_id,
            "modelId": candidate.model_id,
            "revision": candidate.revision,
            "tokenizerRevision": candidate.tokenizer_revision,
            "artifactCount": len(rows),
            "verifiedBytes": candidate.minimal_snapshot_bytes,
            "artifacts": rows,
            "offlineOnly": True,
            "trustRemoteCode": False,
        }
        return {**material, "verificationSha256": _sha256_json_no_lf(material)}

    rejected: list[str] = []

    def require_rejection(label: str, callback: Any) -> None:
        try:
            callback()
        except ModelRunReceiptError:
            rejected.append(label)
        else:
            raise AssertionError(f"adversarial receipt was accepted: {label}")

    corpus = corpus_builder.build_corpus_bundle(include_text=False)
    spec = model_registry.get_model("NLP-D1")
    artifact = artifact_receipt("NLP-D1")
    encoding = {
        "methodId": "NLP-D1",
        "modelId": spec.model_id,
        "modelRevision": spec.revision,
        "tokenizerRevision": spec.tokenizer_revision,
        "artifactVerificationSha256": artifact["verificationSha256"],
        "corpusSha256": corpus["documentReceiptSha256"],
        "lexicalCorpusSha256": corpus["corpusSha256"],
        "tokenCountReceiptSha256": corpus["tokenCountReceiptSha256"],
        "corpusSliceSha256": "2" * 64,
        "inputVariant": "PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC",
        "aspectIds": ["NLP_TITLE"],
        "fullCorpus": True,
        "fullPublicCohort": True,
        "fullAspectCohort": True,
        "objectCount": 7_995,
        "aspectAvailableObjectCount": 7_995,
        "aspectUnavailableObjectCount": 0,
        "defaultQueryCount": 7_995,
        "defaultQueryPublicIdsSha256": "0" * 64,
        "missingAspectRowsZero": True,
        "canonicalPublicIdsSha256": _sha256_json_no_lf(
            list(governance_common.load_public_ids())
        ),
        "semanticInputSha256": "2" * 64,
        "lengthBucketed": True,
        "lengthBucketPermutationSha256": "3" * 64,
        "canonicalOrderRestored": True,
        "batchSize": 8,
        "maxLength": 256,
        "governedEffectiveMaxLength": 256,
        "officialModelMaximumInputTokens": 32_768,
        "pooling": spec.pooling,
        "normalization": spec.normalization,
        "weightDtype": spec.weight_dtype,
        "executionDtype": spec.execution_dtype_cpu,
        "device": "cpu",
        "localFilesOnly": True,
        "trustRemoteCode": False,
        "hostedInferenceCalls": 0,
        "implicitOutputWrites": 0,
        "tokenization": {"documentsTruncated": 0, "tokensRemoved": 0},
        "tokenizerPaddingSide": "left",
        "tokenizerTruncationSide": "right",
        "embeddingObservationSha256": "4" * 64,
        "embeddingDimension": 1_024,
        "embeddingBytesInMemory": 7_995 * 1_024 * 4,
        "performance": {"peakRssBytes": 1_000, "peakVramBytes": None},
        "runtime": {
            "python": "3.13.5",
            "packages": dict(model_registry.RUNTIME_PINS),
        },
    }
    first = build_model_run_receipt(
        candidate_id="NLP-D1",
        run_scope="FULL_CORPUS",
        run_phase="ENCODING",
        status="COMPLETED",
        corpus_bundle_receipt=corpus,
        artifact_verification=artifact,
        encoding_receipt=encoding,
    )
    second = build_model_run_receipt(
        candidate_id="NLP-D1",
        run_scope="FULL_CORPUS",
        run_phase="ENCODING",
        status="COMPLETED",
        corpus_bundle_receipt=corpus,
        artifact_verification=artifact,
        encoding_receipt=encoding,
    )
    if first != second:
        raise AssertionError("identical model-run inputs produced different receipts")
    try:
        _scan_bounded({"embeddings": [[1.0, 0.0]]})
    except ModelRunReceiptError:
        pass
    else:
        raise AssertionError("full embeddings entered a run receipt")

    bad_ledger_corpus = dict(corpus)
    bad_ledger_documents = list(corpus["documents"])
    bad_last_document = dict(bad_ledger_documents[-1])
    bad_last_document["publicObjectId"] = "SURF-NOTINLEDGER"
    bad_last_document["objectId"] = "SURF-NOTINLEDGER"
    bad_ledger_documents[-1] = bad_last_document
    bad_ledger_corpus["documents"] = bad_ledger_documents
    require_rejection(
        "NONAUTHORITATIVE_CORPUS_LEDGER",
        lambda: _corpus_pins(bad_ledger_corpus),
    )

    require_rejection(
        "BLOCKED_CANDIDATE_COMPLETED",
        lambda: _artifact_pins(
            "NLP-D4",
            artifact_receipt("NLP-D4"),
            require_execution_ready=True,
        ),
    )
    bad_artifact = dict(artifact)
    bad_artifact["verifiedBytes"] = 1
    require_rejection(
        "FORGED_ARTIFACT_BYTES",
        lambda: build_model_run_receipt(
            candidate_id="NLP-D1",
            run_scope="FULL_CORPUS",
            run_phase="ENCODING",
            status="COMPLETED",
            corpus_bundle_receipt=corpus,
            artifact_verification=bad_artifact,
            encoding_receipt=encoding,
        ),
    )
    bad_encoding = dict(encoding)
    bad_encoding["artifactVerificationSha256"] = "9" * 64
    require_rejection(
        "ARTIFACT_ENCODING_HASH_MISMATCH",
        lambda: build_model_run_receipt(
            candidate_id="NLP-D1",
            run_scope="FULL_CORPUS",
            run_phase="ENCODING",
            status="COMPLETED",
            corpus_bundle_receipt=corpus,
            artifact_verification=artifact,
            encoding_receipt=bad_encoding,
        ),
    )
    bad_lexical_identity = dict(encoding)
    bad_lexical_identity["lexicalCorpusSha256"] = "8" * 64
    require_rejection(
        "LEXICAL_CORPUS_HASH_MISMATCH",
        lambda: build_model_run_receipt(
            candidate_id="NLP-D1",
            run_scope="FULL_CORPUS",
            run_phase="ENCODING",
            status="COMPLETED",
            corpus_bundle_receipt=corpus,
            artifact_verification=artifact,
            encoding_receipt=bad_lexical_identity,
        ),
    )
    bad_token_count_identity = dict(encoding)
    bad_token_count_identity["tokenCountReceiptSha256"] = "9" * 64
    require_rejection(
        "TOKEN_COUNT_HASH_MISMATCH",
        lambda: build_model_run_receipt(
            candidate_id="NLP-D1",
            run_scope="FULL_CORPUS",
            run_phase="ENCODING",
            status="COMPLETED",
            corpus_bundle_receipt=corpus,
            artifact_verification=artifact,
            encoding_receipt=bad_token_count_identity,
        ),
    )
    bad_counts = dict(encoding)
    bad_counts["aspectUnavailableObjectCount"] = 1
    require_rejection(
        "NONCONSERVING_COHORT_COUNTS",
        lambda: build_model_run_receipt(
            candidate_id="NLP-D1",
            run_scope="FULL_CORPUS",
            run_phase="ENCODING",
            status="COMPLETED",
            corpus_bundle_receipt=corpus,
            artifact_verification=artifact,
            encoding_receipt=bad_counts,
        ),
    )
    ranking = {
        "methodId": "NLP-D1",
        "corpusSha256": encoding["lexicalCorpusSha256"],
        "inputVariant": encoding["inputVariant"],
        "aspectIds": encoding["aspectIds"],
        "fullCorpus": True,
        "objectCount": 7_995,
        "queryCount": 7_995,
        "topK": 50,
        "indexSha256": "5" * 64,
        "rankingIdsSha256": "6" * 64,
        "scoreObservationSha256": "7" * 64,
        "embeddingObservationSha256": encoding["embeddingObservationSha256"],
        "pairMatrixMaterialized": False,
        "fullRankingsCommitted": False,
    }
    bad_ranking = {**ranking, "methodId": "UNRELATED", "topK": 9_999}
    require_rejection(
        "UNCROSSBOUND_UNBOUNDED_RANKING",
        lambda: build_model_run_receipt(
            candidate_id="NLP-D1",
            run_scope="FULL_CORPUS",
            run_phase="INDEXING",
            status="COMPLETED",
            corpus_bundle_receipt=corpus,
            artifact_verification=artifact,
            encoding_receipt=encoding,
            ranking_summary=bad_ranking,
        ),
    )
    semantic_pins, floating_pins = _encoding_pins("NLP-D1", encoding)
    bad_ranking_identity = {**ranking, "corpusSha256": encoding["corpusSha256"]}
    require_rejection(
        "RANKING_DOCUMENT_HASH_SUBSTITUTION",
        lambda: _ranking_pins(
            bad_ranking_identity,
            candidate_id="NLP-D1",
            semantic=semantic_pins,
            floating=floating_pins,
        ),
    )
    ranking_pins = _ranking_pins(
        ranking,
        candidate_id="NLP-D1",
        semantic=semantic_pins,
        floating=floating_pins,
    )
    require_rejection(
        "FORGED_HUBNESS_PASS",
        lambda: _bound_evaluation_summaries(
            candidate_id="NLP-D1",
            semantic=semantic_pins,
            ranking=ranking_pins,
            cross_language_summary=None,
            hubness_anisotropy_summary={"status": "PASS"},
            robustness_summary=None,
        ),
    )
    retained_ranking = {**ranking, "fullRankingsCommitted": True}
    require_rejection(
        "FULL_RANKING_RETENTION",
        lambda: build_model_run_receipt(
            candidate_id="NLP-D1",
            run_scope="FULL_CORPUS",
            run_phase="INDEXING",
            status="COMPLETED",
            corpus_bundle_receipt=corpus,
            artifact_verification=artifact,
            encoding_receipt=encoding,
            ranking_summary=retained_ranking,
        ),
    )
    return {
        "schemaVersion": "trace-nlp-model-run-receipts-self-test/v1",
        "status": "PASS",
        "runReceiptSha256": first["runReceiptSha256"],
        "deterministicRepeat": True,
        "receiptBytes": first["runReceiptBytes"],
        "adversarialRejectionCount": len(rejected),
        "adversarialRejections": rejected,
        "networkCalls": 0,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.self_test:
        print(json.dumps(run_self_tests(), sort_keys=True))
        return 0
    raise SystemExit("run receipt construction requires explicit observed inputs")


if __name__ == "__main__":
    raise SystemExit(main())
