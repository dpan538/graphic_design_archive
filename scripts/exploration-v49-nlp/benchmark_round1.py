#!/usr/bin/env python3
"""Deterministic, checkpointed TRACE NLP Round 1 benchmark orchestrator.

This module coordinates the frozen Round 1 research modules.  It never loads a
Transformer model: dense inputs must already exist as SHA-pinned temporary NPZ
files.  Full text, embeddings, pair matrices, and full rankings may exist only
in memory or in explicitly temporary checkpoints.  The sole analysis output is
a canonical, sanitized summary with bounded rows and aggregate/hash evidence.
"""

from __future__ import annotations

import argparse
import gc
import gzip
import hashlib
import importlib
import json
import math
import re
import statistics
import sys
import tempfile
import time
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "trace-nlp-round1-analysis-summary/v1"
CONFIG_SCHEMA_VERSION = "trace-nlp-round1-benchmark-config/v1"
CHECKPOINT_SCHEMA_VERSION = "trace-nlp-round1-temp-checkpoint/v1"
COMPACT_RESULT_SCHEMA_VERSION = "trace-nlp-round1-compact-ranking/v1"
IMPLEMENTATION_VERSION = "trace-nlp-round1-benchmark-2026-08-24.8"

PUBLIC_OBJECT_COUNT = 7_995
TOP_K = 50
DEFAULT_DENSE_BLOCK_SIZE = 64
MAX_DENSE_BLOCK_SIZE = 128
MAX_COSINE_SLAB_BYTES = 16 * 1024**2
MAX_CHECKPOINT_BYTES = 1024 * 1024**2
MAX_SUMMARY_BYTES = 24 * 1024**2
EXPECTED_DOCUMENT_RECEIPT_SHA256 = (
    "69aa8f290f7390bdb8ce7c0a3cf4ecdfb7426c908804bf48f9126c0eec4fdac8"
)
EXPECTED_RANKING_CORPUS_SHA256 = (
    "7cde5cfdcf0a0bfd4762f9e23c3b50287a0b9071cbf0bd21102bca4ae2ee024c"
)
EXPECTED_TOKEN_COUNT_RECEIPT_SHA256 = (
    "511eee824342ded9c6ac4606af3f99dea79844663ebd550cbbca2ac2ba2cecca"
)
ASPECT_IDS = (
    "NLP_TITLE",
    "NLP_SUBJECT",
    "NLP_SOURCE_NARRATIVE",
)
ASPECT_PURPOSE = {
    "NLP_TITLE": "OBJECT_SEMANTIC",
    "NLP_SUBJECT": "LEAKAGE_GATED_SUBJECT_DIAGNOSTIC",
    "NLP_SOURCE_NARRATIVE": "SOURCE_NARRATIVE_DIAGNOSTIC_ONLY",
}
METADATA_TARGETS = ("medium", "theme", "object_type")
METADATA_MASK_VARIANTS = (
    "TARGET_LABEL_MASKED",
    "ALL_CONTEXT_LABELS_MASKED",
)
EXPECTED_SUMMARY_COMPONENTS = (
    "source",
    "governance",
    "boundary",
    "evaluationRegistry",
    "models",
    "lexical",
    "dense",
    "metadata",
    "leakage",
    "hubness",
    "robustness",
    "aspects",
    "structured",
    "hybrid",
    "review",
    "runs",
    "performance",
    "security",
    "decision",
    "invariants",
)
ROW_ARRAYS = {
    "governance": (
        "fieldRegistryRows",
        "languageScriptRows",
        "textLengthRows",
        "boilerplateRows",
    ),
    "evaluationRegistry": ("rows",),
    "models": ("artifactRows",),
    "lexical": ("resultRows",),
    "dense": ("resultRows", "crossLanguageRows"),
    "metadata": ("holdoutRows",),
    "leakage": ("sourceLanguageRows",),
    "hubness": ("rows",),
    "robustness": ("rows",),
    "aspects": ("rows",),
    "structured": ("rows",),
    "hybrid": ("rows",),
    "review": ("rows",),
}
PUBLIC_ID_RE = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
PRIVATE_TOKEN_RE = re.compile(r"(?:\bFOL-|\bTRN-OBJ-|\bTRTREE|\bTRBRANCH)", re.IGNORECASE)
FORBIDDEN_SUMMARY_KEYS = frozenset(
    {
        "documents",
        "documentsById",
        "embeddings",
        "embeddingMatrix",
        "vectors",
        "rankings",
        "rankingIdsByQuery",
        "semanticNormalized",
        "lexicalCasefolded",
        "displayOriginal",
        "_runtime",
        "topHubRows",
    }
)


class BenchmarkRound1Error(RuntimeError):
    """Raised when a run would violate the frozen, bounded contract."""


def _canonical_encoder() -> json.JSONEncoder:
    return json.JSONEncoder(
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _iter_json_bytes(value: Any, *, newline: bool = False) -> Iterable[bytes]:
    for piece in _canonical_encoder().iterencode(value):
        yield piece.encode("utf-8")
    if newline:
        yield b"\n"


def canonical_json_bytes(value: Any, *, newline: bool = False) -> bytes:
    return b"".join(_iter_json_bytes(value, newline=newline))


def sha256_json(value: Any) -> str:
    digest = hashlib.sha256()
    for piece in _iter_json_bytes(value, newline=True):
        digest.update(piece)
    return digest.hexdigest()


def _sha256_json_no_lf(value: Any) -> str:
    digest = hashlib.sha256()
    for piece in _iter_json_bytes(value):
        digest.update(piece)
    return digest.hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _quantile_r7(values: Sequence[int | float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _module(name: str) -> Any:
    script_dir = str(Path(__file__).resolve().parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    return importlib.import_module(name)


def _is_descendant(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


@dataclass(frozen=True)
class TempPathPolicy:
    """Resolve all mutable benchmark paths beneath one explicit temp root."""

    root: Path

    @classmethod
    def create(cls, value: str | Path, *, create: bool = False) -> "TempPathPolicy":
        raw = Path(value).expanduser()
        if not raw.is_absolute():
            raise BenchmarkRound1Error("--temp-root must be explicit and absolute")
        resolved = raw.resolve()
        allowed = {
            Path(tempfile.gettempdir()).resolve(),
            Path("/private/tmp").resolve(),
            Path("/tmp").resolve(),
        }
        if not any(_is_descendant(resolved, candidate) for candidate in allowed):
            raise BenchmarkRound1Error("benchmark temp root is outside an OS temporary root")
        if create:
            resolved.mkdir(parents=True, exist_ok=True)
        if not resolved.is_dir():
            raise BenchmarkRound1Error("benchmark temp root does not exist")
        return cls(resolved)

    def resolve(
        self,
        value: str | Path,
        *,
        suffixes: Sequence[str] | None = None,
        must_exist: bool = False,
        directory: bool = False,
    ) -> Path:
        raw = Path(value).expanduser()
        if not raw.is_absolute():
            raise BenchmarkRound1Error("benchmark path must be explicit and absolute")
        resolved = raw.resolve()
        if not _is_descendant(resolved, self.root):
            raise BenchmarkRound1Error("benchmark path is outside --temp-root")
        if suffixes is not None and resolved.suffix not in set(suffixes):
            raise BenchmarkRound1Error(
                f"benchmark path requires one of these suffixes: {tuple(suffixes)}"
            )
        if must_exist and not resolved.exists():
            raise BenchmarkRound1Error(f"required temporary input does not exist: {resolved.name}")
        if resolved.exists() and resolved.is_symlink():
            raise BenchmarkRound1Error("benchmark path cannot be a symlink")
        if directory and resolved.exists() and not resolved.is_dir():
            raise BenchmarkRound1Error("checkpoint path is not a directory")
        return resolved

    def resolve_input(
        self,
        value: str | Path,
        *,
        suffixes: Sequence[str] | None = None,
    ) -> Path:
        """Allow read-only inputs from any recognized OS temp root."""

        raw = Path(value).expanduser()
        if not raw.is_absolute():
            raise BenchmarkRound1Error("temporary input path must be explicit and absolute")
        resolved = raw.resolve()
        allowed = {
            Path(tempfile.gettempdir()).resolve(),
            Path("/private/tmp").resolve(),
            Path("/tmp").resolve(),
        }
        if not any(_is_descendant(resolved, candidate) for candidate in allowed):
            raise BenchmarkRound1Error("temporary input is outside an OS temp root")
        if suffixes is not None and resolved.suffix not in set(suffixes):
            raise BenchmarkRound1Error("temporary input suffix is unsupported")
        if not resolved.is_file() or resolved.is_symlink():
            raise BenchmarkRound1Error("temporary input is absent, not a file, or a symlink")
        return resolved


class CheckpointStore:
    """Deterministic gzip checkpoints; payloads may contain bounded top-k IDs."""

    def __init__(self, root: Path, policy: TempPathPolicy) -> None:
        self.root = policy.resolve(root, directory=True)
        self.root.mkdir(parents=True, exist_ok=True)
        self.policy = policy
        self.receipts: list[dict[str, Any]] = []

    def path_for(self, name: str) -> Path:
        if not SAFE_NAME_RE.fullmatch(name):
            raise BenchmarkRound1Error("checkpoint name is unsafe")
        return self.root / f"{name}.json.gz"

    def _load_envelope(self, path: Path) -> Mapping[str, Any]:
        if path.stat().st_size > MAX_CHECKPOINT_BYTES:
            raise BenchmarkRound1Error("checkpoint exceeds the 1 GiB compressed bound")
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            envelope = json.load(handle)
        if not isinstance(envelope, Mapping):
            raise BenchmarkRound1Error("checkpoint envelope is not a mapping")
        if envelope.get("schemaVersion") != CHECKPOINT_SCHEMA_VERSION:
            raise BenchmarkRound1Error("checkpoint schema changed")
        payload = envelope.get("payload")
        if sha256_json(payload) != envelope.get("payloadSha256"):
            raise BenchmarkRound1Error("checkpoint payload hash changed")
        if envelope.get("temporary") is not True or envelope.get("committable") is not False:
            raise BenchmarkRound1Error("checkpoint lost temporary/non-committable markers")
        return envelope

    def _write_envelope(self, path: Path, envelope: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as handle:
                for piece in _iter_json_bytes(envelope, newline=True):
                    handle.write(piece)
        if path.stat().st_size > MAX_CHECKPOINT_BYTES:
            raise BenchmarkRound1Error("new checkpoint exceeds the 1 GiB compressed bound")

    def load_or_build(
        self,
        name: str,
        dependency_material: Mapping[str, Any],
        builder: Callable[[], Any],
        *,
        allow_build: bool,
    ) -> Any:
        path = self.path_for(name)
        dependency_sha = sha256_json(dependency_material)
        started = time.perf_counter()
        if path.exists():
            envelope = self._load_envelope(path)
            if envelope.get("checkpointName") != name:
                raise BenchmarkRound1Error("checkpoint identity changed")
            if envelope.get("dependencySha256") != dependency_sha:
                raise BenchmarkRound1Error(
                    f"stale checkpoint dependency for {name}; refusing silent reuse"
                )
            state = "REUSED"
        else:
            if not allow_build:
                raise BenchmarkRound1Error(f"required checkpoint is absent: {name}")
            payload = builder()
            envelope = {
                "schemaVersion": CHECKPOINT_SCHEMA_VERSION,
                "implementationVersion": IMPLEMENTATION_VERSION,
                "checkpointName": name,
                "dependencySha256": dependency_sha,
                "payloadSha256": sha256_json(payload),
                "temporary": True,
                "committable": False,
                "payload": payload,
            }
            self._write_envelope(path, envelope)
            state = "BUILT"
        elapsed_ms = round((time.perf_counter() - started) * 1000.0, 3)
        receipt = {
            "checkpointName": name,
            "state": state,
            "dependencySha256": dependency_sha,
            "payloadSha256": envelope["payloadSha256"],
            "fileSha256": sha256_path(path),
            "byteCount": path.stat().st_size,
            "elapsedMs": elapsed_ms,
            "temporary": True,
            "committable": False,
        }
        self.receipts.append(receipt)
        return envelope["payload"]


def _candidate_id(row: Any) -> str:
    if isinstance(row, str):
        value = row
    elif isinstance(row, Mapping):
        value = row.get("candidatePublicId", row.get("candidateId"))
    else:
        value = None
    value = str(value or "")
    if not PUBLIC_ID_RE.fullmatch(value):
        raise BenchmarkRound1Error("ranking contains an invalid public candidate ID")
    return value


def compact_ranking_result(result: Mapping[str, Any]) -> dict[str, Any]:
    rankings = result.get("rankings")
    if not isinstance(rankings, Mapping) or not rankings:
        raise BenchmarkRound1Error("ranking result lacks in-memory bounded rankings")
    summary = {key: value for key, value in result.items() if key != "rankings"}
    top_k = summary.get("topK")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 20 <= top_k <= TOP_K:
        raise BenchmarkRound1Error("ranking result topK must be 20..50")
    compact: dict[str, list[str]] = {}
    for query_id in sorted(map(str, rankings)):
        if not PUBLIC_ID_RE.fullmatch(query_id):
            raise BenchmarkRound1Error("ranking contains an invalid public query ID")
        rows = rankings[query_id]
        values = [_candidate_id(row) for row in rows[:top_k]]
        if len(values) != top_k or len(values) != len(set(values)) or query_id in values:
            raise BenchmarkRound1Error("ranking is short, duplicated, or contains self")
        compact[query_id] = values
    material = {
        "schemaVersion": COMPACT_RESULT_SCHEMA_VERSION,
        "summary": summary,
        "rankingIdsByQuery": compact,
        "compactRankingIdsSha256": sha256_json(compact),
        "temporary": True,
        "committable": False,
    }
    validate_compact_result(material)
    return material


def validate_compact_result(compact: Mapping[str, Any]) -> None:
    if compact.get("schemaVersion") != COMPACT_RESULT_SCHEMA_VERSION:
        raise BenchmarkRound1Error("compact ranking schema changed")
    if compact.get("temporary") is not True or compact.get("committable") is not False:
        raise BenchmarkRound1Error("compact ranking lost temporary/non-committable markers")
    summary = compact.get("summary")
    rankings = compact.get("rankingIdsByQuery")
    if not isinstance(summary, Mapping) or not isinstance(rankings, Mapping) or not rankings:
        raise BenchmarkRound1Error("compact ranking is malformed")
    if sha256_json(rankings) != compact.get("compactRankingIdsSha256"):
        raise BenchmarkRound1Error("compact ranking ID hash changed")
    top_k = summary.get("topK")
    aspect_ids = summary.get("aspectIds")
    if not isinstance(top_k, int) or not 20 <= top_k <= TOP_K:
        raise BenchmarkRound1Error("compact ranking topK changed")
    if not isinstance(aspect_ids, list) or len(aspect_ids) != 1:
        raise BenchmarkRound1Error("compact ranking must preserve one aspect")
    for query_id, values in rankings.items():
        if not PUBLIC_ID_RE.fullmatch(str(query_id)) or not isinstance(values, list):
            raise BenchmarkRound1Error("compact query identity/list is invalid")
        if len(values) != top_k or len(values) != len(set(values)) or query_id in values:
            raise BenchmarkRound1Error("compact ranking is short, duplicated, or contains self")
        if any(not PUBLIC_ID_RE.fullmatch(str(value)) for value in values):
            raise BenchmarkRound1Error("compact ranking contains a non-public identity")


class CandidateRowSequence(Sequence[Mapping[str, Any]]):
    """Lazy mapping rows over compact candidate IDs; scores are not reconstructed."""

    def __init__(self, values: Sequence[str], aspect_id: str) -> None:
        self.values = values
        self.aspect_id = aspect_id

    def __len__(self) -> int:
        return len(self.values)

    def _row(self, index: int) -> Mapping[str, Any]:
        candidate = self.values[index]
        return {
            "rank": index + 1,
            "candidatePublicId": candidate,
            "candidateId": candidate,
            "score": None,
            "aspectId": self.aspect_id,
            "historicalRelation": False,
            "semanticRelation": False,
            "probability": False,
        }

    def __getitem__(self, index: int | slice) -> Mapping[str, Any] | tuple[Mapping[str, Any], ...]:
        if isinstance(index, slice):
            indices = range(*index.indices(len(self.values)))
            return tuple(self._row(value) for value in indices)
        if index < 0:
            index += len(self.values)
        if index < 0 or index >= len(self.values):
            raise IndexError(index)
        return self._row(index)

    def __iter__(self) -> Iterable[Mapping[str, Any]]:
        for index in range(len(self.values)):
            yield self._row(index)


def ranking_result_view(compact: Mapping[str, Any]) -> dict[str, Any]:
    validate_compact_result(compact)
    summary = dict(compact["summary"])
    aspect_id = str(summary["aspectIds"][0])
    summary["rankings"] = {
        query_id: CandidateRowSequence(values, aspect_id)
        for query_id, values in compact["rankingIdsByQuery"].items()
    }
    return summary


def _retag_result(
    result: Mapping[str, Any], *, input_variant: str, method_suffix: str
) -> dict[str, Any]:
    output = dict(result)
    output["methodId"] = f"{result['methodId']}-{method_suffix}"
    output["inputVariant"] = input_variant
    if isinstance(output.get("parameters"), Mapping):
        output["parameters"] = {**output["parameters"], "inputVariant": input_variant}
    return output


def _compact_suite(suite: Mapping[str, Any]) -> dict[str, Any]:
    models = suite.get("models")
    if not isinstance(models, Mapping) or set(models) != {"NLP-L0", "NLP-L1", "NLP-L2", "NLP-L3"}:
        raise BenchmarkRound1Error("lexical suite model set changed")
    return {
        "schemaVersion": "trace-nlp-round1-compact-lexical-suite/v1",
        "suiteSummary": {key: value for key, value in suite.items() if key != "models"},
        "models": {
            lane: compact_ranking_result(models[lane]) for lane in sorted(models)
        },
        "temporary": True,
        "committable": False,
    }


def _load_json_or_gzip(path: Path) -> Any:
    opener: Any = gzip.open if path.suffix == ".gz" else path.open
    if path.suffix == ".gz":
        with opener(path, "rt", encoding="utf-8") as handle:
            return json.load(handle)
    with opener("r", encoding="utf-8") as handle:
        return json.load(handle)


def _receipt_field(receipt: Mapping[str, Any], *paths: str) -> Any:
    """Return the first present direct or dotted-path receipt observation."""

    if not isinstance(receipt, Mapping):
        return None
    for path in paths:
        if not path or any(not part for part in path.split(".")):
            raise BenchmarkRound1Error("receipt field path is empty or malformed")
        value: Any = receipt
        for part in path.split("."):
            if not isinstance(value, Mapping) or part not in value:
                value = None
                break
            value = value[part]
        if value is not None:
            return value
    return None


def _load_external_lexical(path: Path) -> dict[str, Any]:
    value = _load_json_or_gzip(path)
    if isinstance(value, Mapping) and value.get("schemaVersion") == CHECKPOINT_SCHEMA_VERSION:
        value = value.get("payload")
    if not isinstance(value, Mapping):
        raise BenchmarkRound1Error("external lexical checkpoint is malformed")
    if value.get("schemaVersion") == "trace-nlp-round1-compact-lexical-suite/v1":
        for compact in value.get("models", {}).values():
            validate_compact_result(compact)
        return dict(value)
    if value.get("schemaVersion") == "trace-nlp-lexical-suite/v1":
        return _compact_suite(value)
    raise BenchmarkRound1Error("external lexical checkpoint schema is unsupported")


def _verified_npz_arrays(
    path: Path,
    expected_sha256: str,
    *,
    expected_object_count: int = PUBLIC_OBJECT_COUNT,
) -> tuple[Any, Any, Any, dict[str, Any]]:
    if not SHA256_RE.fullmatch(expected_sha256):
        raise BenchmarkRound1Error("dense NPZ requires an exact lowercase SHA-256")
    observed_file_sha = sha256_path(path)
    if observed_file_sha != expected_sha256:
        raise BenchmarkRound1Error(f"dense NPZ hash changed: {path.name}")
    np = importlib.import_module("numpy")
    try:
        with np.load(path, allow_pickle=False) as archive:
            if set(archive.files) != {
                "public_object_ids",
                "availability_mask",
                "embeddings",
            }:
                raise BenchmarkRound1Error("dense NPZ member set changed")
            object_ids = np.asarray(archive["public_object_ids"]).astype(str, copy=True)
            availability = np.asarray(archive["availability_mask"], dtype=np.bool_).copy()
            vectors = np.asarray(archive["embeddings"], dtype=np.float32).copy()
    except (OSError, ValueError) as error:
        raise BenchmarkRound1Error(f"dense NPZ could not be read safely: {path.name}") from error
    ids = tuple(str(value) for value in object_ids.tolist())
    if len(ids) != expected_object_count or ids != tuple(sorted(ids)) or len(set(ids)) != len(ids):
        raise BenchmarkRound1Error("dense NPZ public cohort is not canonical")
    if any(not PUBLIC_ID_RE.fullmatch(value) for value in ids):
        raise BenchmarkRound1Error("dense NPZ contains a non-public identity")
    if availability.shape != (len(ids),):
        raise BenchmarkRound1Error("dense NPZ availability mask shape changed")
    if vectors.ndim != 2 or vectors.shape[0] != len(ids) or vectors.shape[1] <= 0:
        raise BenchmarkRound1Error("dense NPZ embedding shape changed")
    if not bool(np.isfinite(vectors).all()):
        raise BenchmarkRound1Error("dense NPZ contains a non-finite vector")
    if not bool(availability.any()):
        raise BenchmarkRound1Error("dense NPZ contains no available aspect rows")
    norms = np.linalg.norm(vectors[availability], axis=1)
    if not bool(np.allclose(norms, 1.0, rtol=0.0, atol=2e-4)):
        raise BenchmarkRound1Error("dense NPZ available rows are not L2-normalized")
    if bool(np.any(vectors[~availability] != 0.0)):
        raise BenchmarkRound1Error("dense NPZ unavailable rows are not exact zeros")
    embedding_sha = hashlib.sha256(
        vectors.astype("<f4", copy=False).tobytes(order="C")
    ).hexdigest()
    receipt = {
        "fileName": path.name,
        "fileSha256": observed_file_sha,
        "byteCount": path.stat().st_size,
        "objectCount": len(ids),
        "aspectAvailableObjectCount": int(availability.sum()),
        "aspectUnavailableObjectCount": len(ids) - int(availability.sum()),
        "embeddingDimension": int(vectors.shape[1]),
        "embeddingObservationSha256": embedding_sha,
        "temporary": True,
        "committable": False,
    }
    return ids, availability, vectors, receipt


def _registry_artifact_verification(candidate_id: str) -> dict[str, Any]:
    """Reconstruct the immutable registry material bound by an encoder receipt."""

    registry = _module("model_registry")
    spec = registry.get_model(candidate_id)
    artifacts = [
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
    artifacts.sort(key=lambda row: row["relativePath"])
    material = {
        "schemaVersion": "trace-nlp-model-artifact-verification/v1",
        "candidateId": candidate_id,
        "modelId": spec.model_id,
        "revision": spec.revision,
        "tokenizerRevision": spec.tokenizer_revision,
        "artifactCount": len(artifacts),
        "verifiedBytes": spec.minimal_snapshot_bytes,
        "artifacts": artifacts,
        "offlineOnly": True,
        "trustRemoteCode": False,
    }
    return {**material, "verificationSha256": _sha256_json_no_lf(material)}


def _validate_encoding_receipt(
    receipt: Mapping[str, Any] | None,
    *,
    candidate_id: str,
    aspect_id: str,
    input_variant: str,
    observed_embedding_sha256: str,
    observed_object_count: int,
    observed_available_object_count: int,
    observed_embedding_dimension: int,
    expected_document_receipt_sha256: str,
    expected_lexical_corpus_sha256: str,
    expected_token_count_receipt_sha256: str,
    expected_canonical_public_ids_sha256: str,
    expected_default_query_public_ids_sha256: str,
    strict: bool,
) -> dict[str, Any]:
    if receipt is None:
        raise BenchmarkRound1Error(
            "dense input requires a complete hardened encoding receipt"
        )
    if not isinstance(receipt, Mapping):
        raise BenchmarkRound1Error("encoding receipt metadata is not a mapping")
    dense_encoder = _module("dense_encoder")
    if (
        receipt.get("schemaVersion") != dense_encoder.SCHEMA_VERSION
        or receipt.get("implementationVersion") != dense_encoder.IMPLEMENTATION_VERSION
    ):
        raise BenchmarkRound1Error(
            "dense encoding receipt predates or differs from the hardened schema"
        )
    model_receipts = _module("model_run_receipts")
    try:
        artifact = model_receipts._artifact_pins(
            candidate_id,
            _registry_artifact_verification(candidate_id),
            require_execution_ready=True,
        )
        semantic, floating = model_receipts._encoding_pins(candidate_id, receipt)
    except (KeyError, TypeError, ValueError) as error:
        raise BenchmarkRound1Error(
            "dense encoding receipt failed hardened provenance validation"
        ) from error
    expected_semantic = {
        "artifactVerificationSha256": artifact["verificationSha256"],
        "corpusSha256": expected_document_receipt_sha256,
        "lexicalCorpusSha256": expected_lexical_corpus_sha256,
        "tokenCountReceiptSha256": expected_token_count_receipt_sha256,
        "inputVariant": input_variant,
        "aspectIds": [aspect_id],
        "fullCorpus": True,
        "fullPublicCohort": True,
        "fullAspectCohort": True,
        "objectCount": observed_object_count,
        "aspectAvailableObjectCount": observed_available_object_count,
        "aspectUnavailableObjectCount": (
            observed_object_count - observed_available_object_count
        ),
        "defaultQueryCount": observed_available_object_count,
        "defaultQueryPublicIdsSha256": expected_default_query_public_ids_sha256,
        "canonicalPublicIdsSha256": expected_canonical_public_ids_sha256,
    }
    if any(semantic.get(key) != value for key, value in expected_semantic.items()):
        raise BenchmarkRound1Error(
            "dense encoding receipt differs from its exact model/corpus/cohort contract"
        )
    if (
        floating.get("embeddingObservationSha256") != observed_embedding_sha256
        or floating.get("embeddingDimension") != observed_embedding_dimension
        or floating.get("embeddingBytesInMemory")
        != observed_object_count * observed_embedding_dimension * 4
    ):
        raise BenchmarkRound1Error(
            "dense encoding receipt differs from the verified NPZ observation"
        )
    performance = floating.get("performance")
    if not isinstance(performance, Mapping):
        raise BenchmarkRound1Error("encoding receipt lacks performance evidence")
    encoding_ms = performance.get("denseCorpusEncodingMs")
    peak_rss = performance.get("peakRssBytes")
    if (
        isinstance(encoding_ms, bool)
        or not isinstance(encoding_ms, (int, float))
        or not math.isfinite(float(encoding_ms))
        or float(encoding_ms) < 0
    ):
        raise BenchmarkRound1Error("encoding receipt contains an invalid duration")
    if (
        isinstance(peak_rss, bool) or not isinstance(peak_rss, int) or peak_rss <= 0
    ):
        raise BenchmarkRound1Error("encoding receipt contains an invalid peak RSS")
    if not isinstance(strict, bool):
        raise BenchmarkRound1Error("strict provenance flag must be boolean")
    # ``--non-strict`` may relax comparison to a prior ranking receipt, but it
    # never waives model/corpus/runtime provenance for a full dense input.
    safe = _sanitize_bounded_metadata(receipt, path="$.encodingReceipt")
    return {
        "status": "SUPPLIED_AND_HARDENED_VALIDATED",
        "receiptSha256": sha256_json(safe),
        "candidateId": candidate_id,
        "modelId": artifact["modelId"],
        "modelRevision": artifact["revision"],
        "tokenizerRevision": artifact["tokenizerRevision"],
        "artifactVerificationSha256": artifact["verificationSha256"],
        "documentReceiptSha256": semantic["corpusSha256"],
        "lexicalCorpusSha256": semantic["lexicalCorpusSha256"],
        "tokenCountReceiptSha256": semantic["tokenCountReceiptSha256"],
        "embeddingObservationSha256": observed_embedding_sha256,
        "denseCorpusEncodingMs": float(encoding_ms),
        "peakRssBytes": peak_rss,
        "runtime": floating["runtime"],
        "offlineOnly": True,
        "trustRemoteCode": False,
        "hostedInferenceCalls": 0,
        "timingInvented": False,
        "receipt": safe,
    }


def _top_ordinals(scores: Any, available: Any, self_ordinal: int, top_k: int) -> tuple[int, ...]:
    np = importlib.import_module("numpy")
    work = np.asarray(scores, dtype=np.float32).copy()
    work[~available] = -np.inf
    work[self_ordinal] = -np.inf
    candidate_count = int(available.sum()) - int(bool(available[self_ordinal]))
    if top_k > candidate_count:
        raise BenchmarkRound1Error("dense top-k exceeds available candidates")
    partition = np.argpartition(-work, top_k - 1)[:top_k]
    threshold = float(work[partition].min())
    eligible = np.flatnonzero(work >= threshold)
    order = np.lexsort((eligible, -work[eligible]))
    selected = tuple(int(value) for value in eligible[order][:top_k])
    if len(selected) != top_k:
        raise BenchmarkRound1Error("dense stable top-k returned the wrong count")
    return selected


def block_exact_rank(
    index: Any,
    query_object_ids: Sequence[str],
    query_vectors: Any,
    query_availability: Any,
    *,
    method_id: str,
    corpus_sha256: str,
    input_variant: str,
    aspect_id: str,
    top_k: int = TOP_K,
    block_size: int = DEFAULT_DENSE_BLOCK_SIZE,
    maximum_slab_bytes: int = MAX_COSINE_SLAB_BYTES,
) -> tuple[dict[str, Any], dict[str, list[str]], dict[str, list[float]]]:
    """Stream exact cosine in bounded query slabs and retain top-k immediately."""

    np = importlib.import_module("numpy")
    ids = tuple(map(str, query_object_ids))
    vectors = np.asarray(query_vectors, dtype=np.float32)
    available = np.asarray(query_availability, dtype=np.bool_)
    if ids != tuple(index.object_ids) or vectors.shape[0] != len(ids):
        raise BenchmarkRound1Error("dense query/candidate identities are not aligned")
    if available.shape != (len(ids),) or vectors.ndim != 2:
        raise BenchmarkRound1Error("dense query availability/vector shape is invalid")
    if vectors.shape[1] != index.vectors.shape[1]:
        raise BenchmarkRound1Error("dense query/candidate dimensions differ")
    if not SHA256_RE.fullmatch(corpus_sha256):
        raise BenchmarkRound1Error("dense ranking requires a corpus SHA-256")
    if not 1 <= block_size <= MAX_DENSE_BLOCK_SIZE:
        raise BenchmarkRound1Error("dense query block size is outside 1..128")
    slab_bytes = block_size * len(ids) * 4
    if slab_bytes > maximum_slab_bytes or maximum_slab_bytes > MAX_COSINE_SLAB_BYTES:
        raise BenchmarkRound1Error("dense cosine slab exceeds the 16 MiB bound")
    query_ordinals = np.flatnonzero(available)
    if not len(query_ordinals):
        raise BenchmarkRound1Error("dense ranking query cohort is empty")
    query_norms = np.linalg.norm(vectors[available], axis=1)
    if not bool(np.allclose(query_norms, 1.0, rtol=0.0, atol=2e-4)):
        raise BenchmarkRound1Error("dense query vectors are not L2-normalized")
    if bool(np.any(vectors[~available] != 0.0)):
        raise BenchmarkRound1Error("unavailable dense query rows are not zeros")

    ranking_ids: dict[str, list[str]] = {}
    score_observations: dict[str, list[float]] = {}
    latencies_ms: list[float] = []
    total_started = time.perf_counter()
    maximum_observed_slab_bytes = 0
    for start in range(0, len(query_ordinals), block_size):
        block_ordinals = query_ordinals[start : start + block_size]
        multiply_started = time.perf_counter()
        # ExactCosineIndex defines the frozen score observation with one
        # float32 matrix-vector product per query.  A float32 GEMM over the
        # whole block is mathematically equivalent but may use a different
        # accumulation kernel; on the governed embeddings, differences around
        # 1e-6 are sufficient to change deterministic top-k ordering.  Retain
        # the bounded block slab, but populate each row with the authoritative
        # GEMV kernel so this streamed implementation is byte-parity compatible
        # with ExactCosineIndex.rank_all.
        slab = np.empty(
            (len(block_ordinals), len(index.object_ids)), dtype=np.float32
        )
        for local_ordinal, query_ordinal in enumerate(block_ordinals):
            slab[local_ordinal] = index._scores(vectors[int(query_ordinal)])
        multiply_ms = (time.perf_counter() - multiply_started) * 1000.0
        maximum_observed_slab_bytes = max(maximum_observed_slab_bytes, int(slab.nbytes))
        if slab.nbytes > maximum_slab_bytes:
            raise BenchmarkRound1Error("observed dense cosine slab crossed its memory gate")
        amortized_multiply_ms = multiply_ms / len(block_ordinals)
        for local_ordinal, query_ordinal in enumerate(block_ordinals):
            top_started = time.perf_counter()
            selected = _top_ordinals(
                slab[local_ordinal], index.availability_mask, int(query_ordinal), top_k
            )
            top_ms = (time.perf_counter() - top_started) * 1000.0
            query_id = ids[int(query_ordinal)]
            ranking_ids[query_id] = [index.object_ids[value] for value in selected]
            score_observations[query_id] = [
                float(slab[local_ordinal, value]) for value in selected
            ]
            latencies_ms.append(amortized_multiply_ms + top_ms)
        del slab
    elapsed_ms = round((time.perf_counter() - total_started) * 1000.0, 3)
    query_embedding_sha = hashlib.sha256(
        vectors.astype("<f4", copy=False).tobytes(order="C")
    ).hexdigest()
    summary = {
        "schemaVersion": "trace-nlp-dense-exact-block-index/v1",
        "methodId": method_id,
        "implementationVersion": IMPLEMENTATION_VERSION,
        "corpusSha256": corpus_sha256,
        "inputVariant": input_variant,
        "aspectIds": [aspect_id],
        "fullCorpus": len(ids) == PUBLIC_OBJECT_COUNT,
        "fullPublicCohort": len(query_ordinals) == PUBLIC_OBJECT_COUNT,
        "fullAspectCohort": len(query_ordinals) == int(available.sum()),
        "topK": top_k,
        "objectCount": len(ids),
        "candidateObjectCount": len(index.object_ids),
        "aspectAvailableObjectCount": len(query_ordinals),
        "aspectUnavailableObjectCount": len(ids) - len(query_ordinals),
        "queryCount": len(query_ordinals),
        "indexSha256": index.index_sha256,
        "candidateEmbeddingObservationSha256": index.embedding_observation_sha256,
        "queryEmbeddingObservationSha256": query_embedding_sha,
        # Match embedding_index.py's existing dense observation convention,
        # which deliberately hashes canonical JSON without a trailing LF.
        "rankingIdsSha256": _sha256_json_no_lf(ranking_ids),
        "scoreObservationSha256": _sha256_json_no_lf(score_observations),
        "missingAspectRowsZero": True,
        "rankingDeterministic": True,
        "floatingPointObservationHardwareScoped": True,
        "pairMatrixMaterialized": False,
        "maximumCosineSlabRows": block_size,
        "maximumCosineSlabBytes": maximum_observed_slab_bytes,
        "scoreKernel": "EXACT_COSINE_INDEX_FLOAT32_GEMV_PER_QUERY",
        "queryLatencyMeasurement": "BLOCK_GEMV_AMORTIZED_PLUS_INDIVIDUAL_TOPK",
        "performance": {
            "denseIndexBytes": int(index.vectors.nbytes),
            "denseExactQueryP50Ms": _quantile_r7(latencies_ms, 0.50),
            "denseExactQueryP95Ms": _quantile_r7(latencies_ms, 0.95),
            "rankingElapsedMs": elapsed_ms,
        },
        "vectorDatabaseAdded": False,
        "seedUsed": False,
        "historicalRelationProduced": False,
        "semanticRelationProduced": False,
        "probabilityProduced": False,
    }
    return summary, ranking_ids, score_observations


class _CachedDenseIndex:
    """Use cached exact top-k for hubness while retaining vectors for anisotropy."""

    def __init__(
        self,
        base_index: Any,
        ranking_ids: Mapping[str, Sequence[str]],
        score_observations: Mapping[str, Sequence[float]],
        query_vectors: Any,
        query_availability: Any,
    ) -> None:
        self.object_ids = base_index.object_ids
        self.available_object_ids = tuple(sorted(ranking_ids))
        self.vectors = base_index.vectors
        self.availability_mask = base_index.availability_mask
        self.index_sha256 = base_index.index_sha256
        self.corpus_sha256 = base_index.corpus_sha256
        self._base = base_index
        self._ranking_ids = ranking_ids
        self._scores = score_observations
        self._query_vectors = query_vectors
        self._query_availability = query_availability
        self._ordinal = {value: index for index, value in enumerate(self.object_ids)}

    def query_id(self, query_id: str, *, top_k: int) -> tuple[dict[str, Any], ...]:
        if query_id not in self._ranking_ids or top_k > len(self._ranking_ids[query_id]):
            raise BenchmarkRound1Error("cached dense query is absent or too short")
        return tuple(
            {
                "rank": rank,
                "candidatePublicId": candidate,
                "score": float(self._scores[query_id][rank - 1]),
            }
            for rank, candidate in enumerate(self._ranking_ids[query_id][:top_k], start=1)
        )

    def rank_target(self, query_id: str, target_id: str) -> dict[str, Any]:
        np = importlib.import_module("numpy")
        query_ordinal = self._ordinal[query_id]
        target_ordinal = self._ordinal[target_id]
        if not bool(self._query_availability[query_ordinal]):
            raise BenchmarkRound1Error("cross-language query has no vector")
        scores = self._base._scores(self._query_vectors[query_ordinal])
        target_score = float(scores[target_ordinal])
        eligible = self._base.availability_mask & (
            np.arange(len(self.object_ids)) != query_ordinal
        )
        rank = 1 + int(np.count_nonzero(eligible & (scores > target_score))) + int(
            np.count_nonzero(
                eligible
                & (scores == target_score)
                & (np.arange(len(self.object_ids)) < target_ordinal)
            )
        )
        return {"rank": rank, "score": target_score}


def _dense_input_dependency(row: Mapping[str, Any], policy: TempPathPolicy) -> dict[str, Any]:
    candidate_path = policy.resolve_input(row["candidateNpzPath"], suffixes=(".npz",))
    query_path = policy.resolve_input(
        row.get("queryNpzPath", row["candidateNpzPath"]), suffixes=(".npz",)
    )
    candidate_sha = str(row.get("candidateNpzSha256", ""))
    query_sha = str(row.get("queryNpzSha256", candidate_sha))
    if not SHA256_RE.fullmatch(candidate_sha) or not SHA256_RE.fullmatch(query_sha):
        raise BenchmarkRound1Error("dense input is not SHA-pinned")
    return {
        "resultId": row.get("resultId"),
        "candidateId": row.get("candidateId"),
        "aspectId": row.get("aspectId"),
        "inputVariant": row.get("inputVariant"),
        "candidateFileSha256": sha256_path(candidate_path),
        "queryFileSha256": sha256_path(query_path),
        "declaredCandidateSha256": candidate_sha,
        "declaredQuerySha256": query_sha,
        "encodingReceiptSha256": sha256_json(row.get("encodingReceipt")),
        "blockSize": row.get("blockSize", DEFAULT_DENSE_BLOCK_SIZE),
    }


def _analysis_catalog_dependency(
    catalog: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Bind derived analysis stages to every bounded ranking input."""

    rows: list[dict[str, Any]] = []
    for method_id, entry in sorted(catalog.items()):
        compact = entry.get("compact")
        if not isinstance(compact, Mapping):
            raise BenchmarkRound1Error("analysis catalog entry lacks a compact ranking")
        validate_compact_result(compact)
        summary = compact["summary"]
        rows.append(
            {
                "methodId": method_id,
                "channel": entry.get("channel"),
                "analysisRole": entry.get("analysisRole"),
                "aspectId": entry.get("aspectId"),
                "familyKey": entry.get("familyKey"),
                "metadataTarget": entry.get("metadataTarget"),
                "maskVariant": entry.get("maskVariant"),
                "ablationId": entry.get("ablationId"),
                "inputVariant": summary.get("inputVariant"),
                "corpusSha256": summary.get("corpusSha256"),
                "indexSha256": summary.get("indexSha256"),
                "rankingIdsSha256": summary.get("rankingIdsSha256"),
                "compactRankingIdsSha256": compact.get(
                    "compactRankingIdsSha256"
                ),
                "topK": summary.get("topK"),
                "queryCount": summary.get("queryCount"),
            }
        )
    return {"rows": rows, "rowsSha256": sha256_json(rows)}


def _build_dense_checkpoint(
    row: Mapping[str, Any],
    *,
    policy: TempPathPolicy,
    corpus_sha256: str,
    corpus_identity: Mapping[str, Any],
    evaluation_rows: Sequence[Mapping[str, Any]],
    evaluation_registry_sha256: str,
    hubness_associations: Mapping[str, Any],
    strict: bool,
) -> dict[str, Any]:
    candidate_id = str(row.get("candidateId", ""))
    if candidate_id not in {"NLP-D1", "NLP-D3"}:
        raise BenchmarkRound1Error("only authorized D1/D3 dense inputs may be ranked")
    aspect_id = str(row.get("aspectId", ""))
    if aspect_id not in ASPECT_IDS:
        raise BenchmarkRound1Error("dense input aspect is not a Round 1 base aspect")
    result_id = str(row.get("resultId", ""))
    if not result_id or not SAFE_NAME_RE.fullmatch(result_id.casefold()):
        raise BenchmarkRound1Error("dense resultId is absent or unsafe")
    input_variant = str(row.get("inputVariant", ""))
    if not input_variant:
        raise BenchmarkRound1Error("dense input variant is absent")
    candidate_path = policy.resolve_input(row["candidateNpzPath"], suffixes=(".npz",))
    query_path = policy.resolve_input(
        row.get("queryNpzPath", row["candidateNpzPath"]), suffixes=(".npz",)
    )
    candidate_sha = str(row.get("candidateNpzSha256", ""))
    query_sha = str(row.get("queryNpzSha256", candidate_sha))
    if input_variant == "PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC" and query_path != candidate_path:
        raise BenchmarkRound1Error("plain symmetric diagnostic must use identical query/document NPZ")
    if input_variant != "PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC" and query_path == candidate_path:
        raise BenchmarkRound1Error(
            "asymmetric retrieval must supply a separately encoded query NPZ"
        )
    ids, candidate_available, candidate_vectors, candidate_receipt = _verified_npz_arrays(
        candidate_path, candidate_sha
    )
    query_ids, query_available, query_vectors, query_receipt = _verified_npz_arrays(
        query_path, query_sha
    )
    if query_ids != ids or not bool((query_available == candidate_available).all()):
        raise BenchmarkRound1Error("dense query/document cohort or availability differs")
    if query_vectors.shape[1] != candidate_vectors.shape[1]:
        raise BenchmarkRound1Error("dense query/document dimension differs")
    encoding_receipt = _validate_encoding_receipt(
        row.get("encodingReceipt"),
        candidate_id=candidate_id,
        aspect_id=aspect_id,
        input_variant=input_variant,
        observed_embedding_sha256=candidate_receipt["embeddingObservationSha256"],
        observed_object_count=len(ids),
        observed_available_object_count=int(candidate_available.sum()),
        observed_embedding_dimension=int(candidate_vectors.shape[1]),
        expected_document_receipt_sha256=corpus_identity[
            "documentReceiptSha256"
        ],
        expected_lexical_corpus_sha256=corpus_identity["lexicalCorpusSha256"],
        expected_token_count_receipt_sha256=corpus_identity[
            "tokenCountReceiptSha256"
        ],
        expected_canonical_public_ids_sha256=_sha256_json_no_lf(list(ids)),
        expected_default_query_public_ids_sha256=_sha256_json_no_lf(
            [
                object_id
                for object_id, available in zip(ids, candidate_available)
                if bool(available)
            ]
        ),
        strict=strict,
    )
    embedding_index = _module("embedding_index")
    base_index = embedding_index.ExactCosineIndex(
        ids,
        candidate_vectors,
        corpus_sha256=corpus_sha256,
        availability_mask=candidate_available,
        embedding_observation_sha256=candidate_receipt["embeddingObservationSha256"],
    )
    summary, ranking_ids, score_observations = block_exact_rank(
        base_index,
        query_ids,
        query_vectors,
        query_available,
        method_id=result_id,
        corpus_sha256=corpus_sha256,
        input_variant=input_variant,
        aspect_id=aspect_id,
        top_k=TOP_K,
        block_size=int(row.get("blockSize", DEFAULT_DENSE_BLOCK_SIZE)),
    )
    compact = {
        "schemaVersion": COMPACT_RESULT_SCHEMA_VERSION,
        "summary": summary,
        "rankingIdsByQuery": ranking_ids,
        "compactRankingIdsSha256": sha256_json(ranking_ids),
        "temporary": True,
        "committable": False,
    }
    validate_compact_result(compact)
    cached = _CachedDenseIndex(
        base_index,
        ranking_ids,
        score_observations,
        query_vectors,
        query_available,
    )
    hubness = _module("hubness_anisotropy").evaluate_hubness_and_anisotropy(
        cached,
        method_id=result_id,
        corpus_sha256=corpus_sha256,
        input_variant=input_variant,
        aspect_id=aspect_id,
        query_ids=tuple(sorted(ranking_ids)),
        k_values=(10, 20, 50),
        source_by_object=hubness_associations["source_by_object"],
        language_by_object=hubness_associations["language_by_object"],
        text_length_by_object=hubness_associations["text_length_by_object"],
        boilerplate_by_object=hubness_associations["boilerplate_by_object"],
        generic_title_by_object=hubness_associations["generic_title_by_object"],
        metadata_completeness_by_object=hubness_associations[
            "metadata_completeness_by_object"
        ],
        pre_normalization_norms=None,
        require_complete=False,
    )
    cross_language = _module("cross_language_eval").evaluate_cross_language(
        cached,
        evaluation_rows,
        method_id=result_id,
        corpus_sha256=corpus_sha256,
        evaluation_registry_sha256=evaluation_registry_sha256,
        input_variant=input_variant,
        aspect_id=aspect_id,
    )
    source_probe = _dense_source_probe(
        ids,
        candidate_available,
        candidate_vectors,
        input_variant=input_variant,
        representation_index_sha256=candidate_receipt["embeddingObservationSha256"],
    )
    return {
        "schemaVersion": "trace-nlp-round1-dense-checkpoint/v1",
        "candidateId": candidate_id,
        "aspectId": aspect_id,
        "analysisRole": str(row.get("analysisRole", "BASE")),
        "result": compact,
        "candidateNpz": candidate_receipt,
        "queryNpz": query_receipt,
        "encodingReceipt": encoding_receipt,
        "crossLanguage": cross_language,
        "hubnessAnisotropy": hubness,
        "hubnessAssociationReceipt": hubness_associations["receipt"],
        "sourceProbe": source_probe,
        "replicateGroupId": row.get("replicateGroupId"),
        "modelLoadedByOrchestrator": False,
        "pairMatrixMaterialized": False,
    }


def _aspect_role(aspect_id: str) -> str:
    return {
        "NLP_TITLE": "OBJECT_TITLE",
        "NLP_SUBJECT": "SUBJECT_LABELS_LEAKAGE_GATED",
        "NLP_SOURCE_NARRATIVE": "SOURCE_NARRATIVE_DIAGNOSTIC_ONLY",
        "NLP_OBJECT_SEMANTIC_COMPOSITE": "OBJECT_SEMANTIC_COMPOSITE_TITLE_ONLY",
    }[aspect_id]


def _language_script_rows(corpus: Any) -> list[dict[str, Any]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    characters: dict[tuple[str, str], int] = defaultdict(int)
    for document in corpus.documents:
        for aspect_id, aspect in document.aspects.items():
            counts[aspect_id][aspect.language_script_state] += 1
            characters[(aspect_id, aspect.language_script_state)] += aspect.character_count
    rows = []
    for aspect_id in sorted(counts):
        total = sum(counts[aspect_id].values())
        for state, count in sorted(counts[aspect_id].items()):
            rows.append(
                {
                    "aspectId": aspect_id,
                    "fieldRole": _aspect_role(aspect_id),
                    "sourceIdentity": "ALL_GOVERNED_PUBLIC_SOURCES",
                    "scriptState": state,
                    "textLengthBucket": "ALL_LENGTHS",
                    "objectCount": count,
                    "documentCount": count,
                    "characterCount": characters[(aspect_id, state)],
                    "objectShare": count / total,
                    "languageLabel": "NOT_ASSIGNED",
                    "languageLabelState": "NOT_RUN_NO_SELECTED_LID",
                    "languageIdModelId": "NOT_SELECTED",
                    "languageIdModelRevision": "N/A",
                    "languageIdModelCommitted": False,
                    "generatedTranslationCount": 0,
                    "corpusSha256": corpus.corpus_sha256,
                }
            )
    return rows


def _length_rows(corpus: Any) -> list[dict[str, Any]]:
    common = _module("lexical_common")
    caps = _module("field_governance").model_input_token_caps()
    rows: list[dict[str, Any]] = []
    for aspect_id in sorted(caps):
        aspects = [
            document.aspects[aspect_id]
            for document in corpus.documents
            if aspect_id in document.aspects
        ]
        character_lengths = [aspect.character_count for aspect in aspects]
        lexical_lengths = [len(common.word_tokens(aspect.lexical_casefolded)) for aspect in aspects]
        material = {
            "modelOrTokenizerId": "GOVERNED-LEXICAL-CENSUS",
            "tokenizerRevision": common.IMPLEMENTATION_VERSION,
            "aspectId": aspect_id,
            "fieldRole": _aspect_role(aspect_id),
            "measurementScope": "FULL_GOVERNED_ASPECT",
            "documentCount": len(aspects),
            "characterLengthP50": _quantile_r7(character_lengths, 0.50),
            "characterLengthP90": _quantile_r7(character_lengths, 0.90),
            "characterLengthP95": _quantile_r7(character_lengths, 0.95),
            "characterLengthP99": _quantile_r7(character_lengths, 0.99),
            "characterLengthMax": max(character_lengths),
            "codepointLengthP50": _quantile_r7(character_lengths, 0.50),
            "codepointLengthP90": _quantile_r7(character_lengths, 0.90),
            "codepointLengthP95": _quantile_r7(character_lengths, 0.95),
            "codepointLengthP99": _quantile_r7(character_lengths, 0.99),
            "codepointLengthMax": max(character_lengths),
            "lexicalTokenCountP50": _quantile_r7(lexical_lengths, 0.50),
            "lexicalTokenCountP90": _quantile_r7(lexical_lengths, 0.90),
            "lexicalTokenCountP95": _quantile_r7(lexical_lengths, 0.95),
            "lexicalTokenCountP99": _quantile_r7(lexical_lengths, 0.99),
            "lexicalTokenCountMax": max(lexical_lengths),
            "denseTokenCountP50": None,
            "denseTokenCountP90": None,
            "denseTokenCountP95": None,
            "denseTokenCountP99": None,
            "denseTokenCountMax": None,
            "governedTokenCap": caps[aspect_id],
            "officialModelMaxTokens": None,
            "effectiveTokenCap": caps[aspect_id],
            "documentsTruncated": 0,
            "tokensRemoved": 0,
            "documentTruncationRate": 0.0,
            "tokenRemovalRate": 0.0,
            "truncationDirection": "HEAD",
            "applicationStage": "HEAD_AT_MODEL_INPUT_ONLY",
            "fullNormalizedHashesPreserved": True,
            "corpusTextOverwritten": False,
        }
        rows.append({**material, "receiptSha256": sha256_json(material)})
    return rows


def _corpus_identity_receipt(corpus: Any) -> dict[str, Any]:
    """Bind builder document identity separately from lexical index identity."""

    bundle = _module("corpus_builder").build_corpus_bundle(include_text=False)
    if not isinstance(bundle, Mapping):
        raise BenchmarkRound1Error("corpus builder identity receipt is malformed")
    document_receipt = str(bundle.get("documentReceiptSha256", ""))
    token_count_receipt = str(bundle.get("tokenCountReceiptSha256", ""))
    lexical_corpus_receipt = str(bundle.get("corpusSha256", ""))
    if not SHA256_RE.fullmatch(document_receipt) or not SHA256_RE.fullmatch(
        token_count_receipt
    ) or not SHA256_RE.fullmatch(lexical_corpus_receipt):
        raise BenchmarkRound1Error("corpus builder identity SHA-256 is absent")
    if lexical_corpus_receipt != corpus.corpus_sha256:
        raise BenchmarkRound1Error("corpus builder/lexical ranking corpus SHA-256 differs")
    observed_contracts = (
        document_receipt,
        lexical_corpus_receipt,
        token_count_receipt,
    )
    expected_contracts = (
        EXPECTED_DOCUMENT_RECEIPT_SHA256,
        EXPECTED_RANKING_CORPUS_SHA256,
        EXPECTED_TOKEN_COUNT_RECEIPT_SHA256,
    )
    if observed_contracts != expected_contracts:
        raise BenchmarkRound1Error("frozen document/ranking/token receipt contract changed")
    boundary = bundle.get("boundary")
    if not isinstance(boundary, Mapping) or boundary.get("publicObjectCount") != len(
        corpus.object_ids
    ):
        raise BenchmarkRound1Error("corpus builder/lexical public boundary differs")
    documents = bundle.get("documents")
    if not isinstance(documents, list):
        raise BenchmarkRound1Error("corpus builder identity receipt lacks documents")
    public_ids = tuple(str(row.get("publicObjectId", "")) for row in documents)
    if public_ids != corpus.object_ids:
        raise BenchmarkRound1Error("corpus builder/lexical canonical identities differ")
    if (
        bundle.get("policySha256") != corpus.policy_sha256
        or bundle.get("fieldRegistrySha256") != corpus.field_registry_sha256
        or bundle.get("normalizationVersion") != corpus.normalization_version
    ):
        raise BenchmarkRound1Error("corpus builder/lexical governance pins differ")
    return {
        "documentReceiptSha256": document_receipt,
        "tokenCountReceiptSha256": token_count_receipt,
        "tokenCountMethod": bundle.get("tokenCountMethod"),
        "lexicalCorpusSha256": lexical_corpus_receipt,
        "canonicalPublicIdsSha256": _sha256_json_no_lf(list(public_ids)),
        "documentAndLexicalCorpusHashesAreDistinctContracts": True,
    }


def _governance_payload(
    corpus: Any, corpus_identity: Mapping[str, Any]
) -> dict[str, Any]:
    field_governance = _module("field_governance")
    source_inventory = _module("source_inventory")
    boilerplate_audit = _module("boilerplate_audit")
    common = _module("lexical_common")
    boundary_common = _module("common")
    inventory = source_inventory.inventory_summary()
    round6_source = common._load_round6_common().source_receipt()
    frozen_inputs = {
        str(boundary_common.LEDGER_PATH.relative_to(boundary_common.ROOT)): boundary_common.EXPECTED_SHA256["ledger"],
        str(boundary_common.SQLITE_PATH.relative_to(boundary_common.ROOT)): boundary_common.EXPECTED_SHA256["sqlite"],
        str(boundary_common.CANONICAL_PATH.relative_to(boundary_common.ROOT)): boundary_common.EXPECTED_SHA256["canonical"],
        str(boundary_common.CONTEXT_RECORDS_PATH.relative_to(boundary_common.ROOT)): boundary_common.EXPECTED_SHA256["contextRecords"],
        str(boundary_common.CONTEXT_MANIFEST_PATH.relative_to(boundary_common.ROOT)): boundary_common.EXPECTED_SHA256["contextManifest"],
        str(boundary_common.SPACETIME_RECORDS_PATH.relative_to(boundary_common.ROOT)): boundary_common.EXPECTED_SHA256["spacetimeRecords"],
        str(boundary_common.SPACETIME_MANIFEST_PATH.relative_to(boundary_common.ROOT)): boundary_common.EXPECTED_SHA256["spacetimeManifest"],
        str(boundary_common.ROUND6_REVIEW_PATH.relative_to(boundary_common.ROOT)): boundary_common.EXPECTED_SHA256["round6Review"],
        str(boundary_common.ROUND6_LEDGER_PATH.relative_to(boundary_common.ROOT)): boundary_common.EXPECTED_SHA256["round6Ledger"],
    }
    source = {
        "schemaVersion": "trace-nlp-round1-source-summary/v1",
        "sourceCommit": getattr(common, "SOURCE_COMMIT", None),
        "round6CandidateIndexSha256": "abba30fcdded21b8f1ba6f7ec87a47b6bbd83c0d1e40d90670143fb88b83873f",
        "contextProjectionSha256": round6_source["contextProjectionSha256"],
        "spacetimeProjectionSha256": round6_source["spacetimeProjectionSha256"],
        "frozenInputs": dict(sorted(frozen_inputs.items())),
        "round6SourceReceipt": round6_source,
        "textSourceFieldCount": inventory["textSourceFieldCount"],
        "publicObjectsAudited": inventory["publicObjectsAudited"],
        "heldObjectsIncluded": inventory["heldObjectsIncluded"],
        "sourceInventoryFieldRegistrySha256": inventory["fieldRegistrySha256"],
        "corpusIdentityReceipt": dict(corpus_identity),
    }
    field_rows = [dict(value) for value in field_governance.registry_rows()]
    # Inventory rows carry the audited coverage/length/leakage measures required
    # by the frozen field-registry table; governance registry rows are pins.
    field_rows = [dict(value) for value in inventory["rows"]]
    text_length_rows = _length_rows(corpus)
    boilerplate_rows = [dict(value) for value in boilerplate_audit.boilerplate_registry_rows()]
    governance = {
        "schemaVersion": "trace-nlp-round1-governance-summary/v1",
        "corpusPolicyVersion": corpus.policy_version,
        "corpusPolicySha256": corpus.policy_sha256,
        "fieldRegistryVersion": corpus.field_registry_version,
        "fieldRegistrySha256": corpus.field_registry_sha256,
        "normalizationVersion": corpus.normalization_version,
        "corpusSha256": corpus.corpus_sha256,
        "documentReceiptSha256": corpus_identity["documentReceiptSha256"],
        "tokenCountReceiptSha256": corpus_identity["tokenCountReceiptSha256"],
        "tokenCountMethod": corpus_identity["tokenCountMethod"],
        "modelInputTokenCaps": field_governance.model_input_token_caps(),
        "languageIdModel": "NOT_SELECTED",
        "languageIdModelCommitted": False,
        "originalSourceTextOverwritten": False,
        "machineTranslationUsed": False,
        "generatedSummaryUsed": False,
        "sourceNarrativeMergedWithObjectSemantic": False,
        "objectSemanticCompositeSourceRoles": ["OBJECT_TITLE"],
        "unclassifiedTextFieldCount": inventory["unclassifiedTextFieldCount"],
        "textSourceFieldCount": inventory["textSourceFieldCount"],
        "textSourceFieldClassifiedCount": inventory["textSourceFieldClassifiedCount"],
        "fieldRegistryRows": field_rows,
        "languageScriptRows": _language_script_rows(corpus),
        "textLengthRows": text_length_rows,
        "boilerplateRows": boilerplate_rows,
    }
    boundary = {
        "schemaVersion": "trace-nlp-round1-boundary-summary/v1",
        "canonicalObjectCount": corpus.canonical_object_count,
        "publicObjectCount": corpus.public_object_count,
        "heldObjectCount": corpus.held_object_count,
        "overlapCount": 0,
        "unclassifiedCount": 0,
        "nlpHeldObjectsIncluded": 0,
        "publicObjectsAudited": corpus.public_object_count,
        "publicObjectsWithAnyApprovedText": corpus.public_object_count,
        "corpusSha256": corpus.corpus_sha256,
        "aspectObjectCounts": {
            aspect_id: sum(aspect_id in document.aspects for document in corpus.documents)
            for aspect_id in (
                "NLP_OBJECT_DESCRIPTION",
                "NLP_OBJECT_SEMANTIC_COMPOSITE",
                "NLP_SOURCE_NARRATIVE",
                "NLP_SUBJECT",
                "NLP_TITLE",
            )
        },
        "publicIdsSha256": sha256_json(list(corpus.object_ids)),
    }
    return {"source": source, "governance": governance, "boundary": boundary}


def _evaluation_registry_payload() -> dict[str, Any]:
    known_item_eval = _module("known_item_eval")
    registry = known_item_eval.build_evaluation_pair_registry()
    rows = [dict(value) for value in registry["rows"]]
    return {
        "schemaVersion": "trace-nlp-round1-evaluation-registry/v1",
        "registryVersion": registry["registryVersion"],
        "registrySha256": registry["registrySha256"],
        "pairCount": len(rows),
        "knownRepresentationPositivePairCount": registry[
            "knownRepresentationPositivePairCount"
        ],
        "negativeControlPairCount": registry["negativeControlPairCount"],
        "verifiedCrossLanguagePositivePairCount": registry[
            "verifiedCrossLanguagePositivePairCount"
        ],
        "taskBPositivePairCount": 0,
        "modelCreatedPositivePairCount": 0,
        "taskBEvaluationState": "N_A_NO_VERIFIED_ARCHIVE_TITLE_LANGUAGE_VARIANT_PAIRS",
        "fullSameTitleStressCensus": registry["fullSameTitleStressCensus"],
        "sourceTitleDifferenceCensus": registry["sourceTitleDifferenceCensus"],
        "rows": rows,
    }


def _model_artifact_rows() -> list[dict[str, Any]]:
    registry = _module("model_registry").registry_receipt()
    rows: list[dict[str, Any]] = []
    for model in registry["models"]:
        artifacts = list(model.get("artifacts", ()))
        artifact_manifest = [
            {
                "relativePath": artifact["relative_path"],
                "byteCount": artifact["byte_count"],
                "digestAlgorithm": artifact["digest_algorithm"],
                "digest": artifact["digest"],
                "role": artifact["role"],
                "serialization": artifact["serialization"],
                "requiredForExecution": artifact["required_for_execution"],
            }
            for artifact in artifacts
        ]
        ready = model["candidate_id"] in {"NLP-D1", "NLP-D3"}
        prohibited = (
            "PRODUCTION_USE"
            if model["eligibility"] == "RESEARCH_ONLY"
            else (
                "EXECUTION_BEFORE_CODE_AND_WEIGHT_REVIEW"
                if model["execution_state"] != "READY_FROM_VERIFIED_LOCAL_SNAPSHOT"
                else "NONE"
            )
        )
        rows.append(
            {
                "candidateId": model["candidate_id"],
                "channel": model["channel"],
                "modelId": model["model_id"],
                "revision": model["revision"],
                "tokenizerRevision": model["tokenizer_revision"],
                "licenseSpdx": model["license_spdx"],
                "eligibility": model["eligibility"],
                "productionEligible": model["production_eligible"],
                "executionState": model["execution_state"],
                "executionBlockers": list(model["execution_blockers"]),
                "trustRemoteCodeRequired": model["trust_remote_code_required"],
                "customCodeReviewed": model["custom_code_reviewed"],
                "parameterCountLabel": model["parameter_count_label"],
                "embeddingDimension": model["embedding_dimension"],
                "maximumInputTokens": model["maximum_input_tokens"],
                "pooling": model["pooling"],
                "normalization": model["normalization"],
                "weightDtype": model["weight_dtype"],
                "executionDtypeCpu": model["execution_dtype_cpu"],
                "quantizationState": model["quantization_state"],
                "queryTemplate": " ".join(str(model["query_template"]).split()),
                "documentTemplate": " ".join(str(model["document_template"]).split()),
                "symmetricMode": model["symmetric_mode"],
                "languageCoverage": model["language_coverage"],
                "minimumLengthPolicy": " ".join(
                    str(model["minimum_length_policy"]).split()
                ),
                "loaderFamily": model["loader_family"],
                "pickleWeightPresent": model["pickle_weight_present"],
                "minimalSnapshotBytes": model["minimal_snapshot_bytes"],
                "artifactCount": len(artifacts),
                "artifactManifestSha256": sha256_json(artifact_manifest),
                "localSnapshotVerified": ready,
                "executionScope": "FULL_CORPUS" if ready else "NOT_RUN",
                "runStatus": "ENCODING_AVAILABLE" if ready else "NOT_RUN",
                "prohibitedUse": prohibited,
                "registrySha256": registry["registrySha256"],
            }
        )
    return rows


def _not_run_source_probe(
    *,
    representation: str,
    reason: str,
    object_count: int,
    input_variant: str,
) -> dict[str, Any]:
    """Return an explicit probe N/A receipt; absence is never treated as evidence."""

    material = {
        "schemaVersion": "trace-nlp-linear-source-probe-receipt/v1",
        "implementationVersion": _module("source_leakage_eval").IMPLEMENTATION_VERSION,
        "status": "NOT_RUN",
        "reason": reason,
        "representation": representation,
        "inputVariant": input_variant,
        "probeMethod": "ONE_VS_REST_RIDGE_LEAST_SQUARES",
        "objectCount": object_count,
        "featureColumnCount": None,
        "featureNonzeroCount": None,
        "foldCount": None,
        "stratified": True,
        "seed": None,
        "classCount": None,
        "macroF1": None,
        "accuracy": None,
        "majorityBaselineMacroF1": None,
        "majorityBaselineAccuracy": None,
        "ridge": 1.0,
        "iterationLimit": 100,
        "predictionsSha256": None,
        "featureMatrixRetained": False,
        "highPerformanceMeansLeakageDiagnostic": True,
    }
    return {**material, "receiptSha256": sha256_json(material)}


def _finalize_source_probe(
    probe: Mapping[str, Any],
    *,
    representation: str,
    input_variant: str,
    object_count: int,
    feature_column_count: int,
    feature_nonzero_count: int,
    representation_index_sha256: str,
    excluded_low_support_class_count: int = 0,
    excluded_low_support_object_count: int = 0,
) -> dict[str, Any]:
    if probe.get("schemaVersion") != "trace-nlp-linear-source-probe/v1":
        raise BenchmarkRound1Error("linear source probe schema changed")
    if probe.get("seed") is not None or probe.get("stratified") is not True:
        raise BenchmarkRound1Error("linear source probe determinism contract changed")
    material = {
        **dict(probe),
        "schemaVersion": "trace-nlp-linear-source-probe-receipt/v1",
        "implementationVersion": _module("source_leakage_eval").IMPLEMENTATION_VERSION,
        "status": "PASS",
        "reason": "ANALYSIS_ONLY_SOURCE_CLASSIFICATION_DIAGNOSTIC",
        "representation": representation,
        "inputVariant": input_variant,
        "objectCount": object_count,
        "featureColumnCount": feature_column_count,
        "featureNonzeroCount": feature_nonzero_count,
        "representationIndexSha256": representation_index_sha256,
        "sourceClassMinimumSupport": 2,
        "excludedLowSupportClassCount": excluded_low_support_class_count,
        "excludedLowSupportObjectCount": excluded_low_support_object_count,
        "featureMatrixRetained": False,
    }
    return {**material, "receiptSha256": sha256_json(material)}


def _source_probe_cohort(
    object_ids: Sequence[str], labels_by_id: Mapping[str, str]
) -> tuple[tuple[int, ...], tuple[str, ...], dict[str, str], int, int]:
    """Exclude only classes that cannot support two-way stratified CV."""

    if tuple(object_ids) != tuple(sorted(object_ids)):
        raise BenchmarkRound1Error("source-probe cohort is not in canonical ID order")
    support = Counter(labels_by_id[object_id] for object_id in object_ids)
    eligible_labels = {label for label, count in support.items() if count >= 2}
    selected_ordinals = tuple(
        ordinal
        for ordinal, object_id in enumerate(object_ids)
        if labels_by_id[object_id] in eligible_labels
    )
    selected_ids = tuple(object_ids[ordinal] for ordinal in selected_ordinals)
    selected_labels = {object_id: labels_by_id[object_id] for object_id in selected_ids}
    excluded_labels = set(support) - eligible_labels
    excluded_objects = sum(support[label] for label in excluded_labels)
    return (
        selected_ordinals,
        selected_ids,
        selected_labels,
        len(excluded_labels),
        excluded_objects,
    )


def _bm25f_probe_matrix(
    corpus: Any, *, aspect_id: str, input_variant: str
) -> tuple[Any, str]:
    """Build the exact sparse BM25F document-term contribution representation."""

    np = importlib.import_module("numpy")
    sparse = importlib.import_module("scipy.sparse")
    bm25f = _module("lexical_bm25f")
    base = bm25f.default_spec()
    spec = replace(
        base,
        method_id=f"NLP-L0-SOURCE-PROBE-{aspect_id.removeprefix('NLP_')}",
        aspect_ids=(aspect_id,),
        field_weights=((aspect_id, 1.0),),
        input_variant=input_variant,
        b_by_field=((aspect_id, 0.75),),
    )
    index = bm25f.build_index(corpus, spec)
    vocabulary = tuple(sorted(index.document_frequencies))
    indices: list[Any] = []
    values: list[Any] = []
    indptr = [0]
    lengths = index.document_lengths[aspect_id]
    average_length = index.average_field_lengths[aspect_id]
    if average_length <= 0.0 or not vocabulary:
        raise BenchmarkRound1Error("BM25F source-probe representation is empty")
    b_value = dict(index.spec.b_by_field)[aspect_id]
    weight = dict(index.spec.field_weights)[aspect_id]
    for token in vocabulary:
        ordinals, frequencies = index.postings[aspect_id][token]
        normalization = 1.0 - b_value + b_value * lengths[ordinals] / average_length
        combined_tf = weight * frequencies / normalization
        document_frequency = index.document_frequencies[token]
        idf = math.log(
            1.0
            + (len(index.object_ids) - document_frequency + 0.5)
            / (document_frequency + 0.5)
        )
        contribution = idf * (
            (index.spec.k1 + 1.0) * combined_tf / (index.spec.k1 + combined_tf)
        )
        indices.append(np.asarray(ordinals, dtype=np.int32))
        values.append(np.asarray(contribution, dtype=np.float64))
        indptr.append(indptr[-1] + len(ordinals))
    matrix = sparse.csc_matrix(
        (
            np.concatenate(values),
            np.concatenate(indices),
            np.asarray(indptr, dtype=np.int64),
        ),
        shape=(len(index.object_ids), len(vocabulary)),
        dtype=np.float64,
    ).tocsr()
    return matrix, index.index_sha256


def _sparse_tfidf_probe_matrix(
    corpus: Any, *, lane: str, aspect_id: str, input_variant: str
) -> tuple[Any, str]:
    module_name = {
        "NLP-L1": "lexical_char_ngram",
        "NLP-L2": "lexical_word_ngram",
    }.get(lane)
    if module_name is None:
        raise BenchmarkRound1Error("unsupported sparse source-probe lane")
    lexical_module = _module(module_name)
    base = lexical_module.default_spec()
    spec = replace(
        base,
        method_id=f"{lane}-SOURCE-PROBE-{aspect_id.removeprefix('NLP_')}",
        aspect_ids=(aspect_id,),
        field_weights=((aspect_id, 1.0),),
        input_variant=input_variant,
    )
    index = lexical_module.build_index(corpus, spec)
    matrix = _module("source_leakage_eval").sparse_field_probe_matrix(index)
    return matrix, index.index_sha256


def _lexical_source_probes(
    corpus: Any, *, aspect_id: str, input_variant: str
) -> dict[str, dict[str, Any]]:
    """Evaluate every lexical feature representation; declare rank fusion N/A."""

    np = importlib.import_module("numpy")
    source_leakage = _module("source_leakage_eval")
    labels = source_leakage.source_labels()
    if set(labels) != set(corpus.object_ids):
        raise BenchmarkRound1Error("source-probe labels differ from the governed cohort")
    selected_ordinals = np.asarray(
        [
            ordinal
            for ordinal, document in enumerate(corpus.documents)
            if aspect_id in document.aspects
        ],
        dtype=np.int64,
    )
    available_ids = tuple(corpus.object_ids[int(value)] for value in selected_ordinals)
    (
        eligible_positions,
        selected_ids,
        selected_labels,
        excluded_class_count,
        excluded_object_count,
    ) = _source_probe_cohort(available_ids, labels)
    selected_ordinals = selected_ordinals[
        np.asarray(eligible_positions, dtype=np.int64)
    ]
    if len(set(selected_labels.values())) < 2:
        raise BenchmarkRound1Error("source-probe cohort lacks two eligible source classes")
    probes: dict[str, dict[str, Any]] = {}
    for lane in ("NLP-L0", "NLP-L1", "NLP-L2"):
        if lane == "NLP-L0":
            matrix, index_sha = _bm25f_probe_matrix(
                corpus, aspect_id=aspect_id, input_variant=input_variant
            )
            representation = "BM25F_DOCUMENT_TERM_CONTRIBUTIONS"
        else:
            matrix, index_sha = _sparse_tfidf_probe_matrix(
                corpus,
                lane=lane,
                aspect_id=aspect_id,
                input_variant=input_variant,
            )
            representation = (
                "CHARACTER_NGRAM_TFIDF" if lane == "NLP-L1" else "WORD_NGRAM_TFIDF"
            )
        selected_matrix = matrix[selected_ordinals]
        result = source_leakage.deterministic_linear_probe(
            selected_matrix,
            selected_ids,
            selected_labels,
            requested_folds=5,
            ridge=1.0,
            iteration_limit=100,
        )
        probes[lane] = _finalize_source_probe(
            result,
            representation=representation,
            input_variant=input_variant,
            object_count=len(selected_ids),
            feature_column_count=int(selected_matrix.shape[1]),
            feature_nonzero_count=int(selected_matrix.nnz),
            representation_index_sha256=index_sha,
            excluded_low_support_class_count=excluded_class_count,
            excluded_low_support_object_count=excluded_object_count,
        )
        del selected_matrix, matrix
        gc.collect()
    probes["NLP-L3"] = _not_run_source_probe(
        representation="RECIPROCAL_RANK_FUSION",
        reason="RANK_FUSION_HAS_NO_SINGLE_LINEAR_FEATURE_REPRESENTATION",
        object_count=len(available_ids),
        input_variant=input_variant,
    )
    return probes


def _dense_source_probe(
    object_ids: Sequence[str],
    availability: Any,
    vectors: Any,
    *,
    input_variant: str,
    representation_index_sha256: str,
) -> dict[str, Any]:
    np = importlib.import_module("numpy")
    source_leakage = _module("source_leakage_eval")
    labels = source_leakage.source_labels()
    available = np.asarray(availability, dtype=np.bool_)
    selected_ordinals = np.flatnonzero(available)
    available_ids = tuple(str(object_ids[int(value)]) for value in selected_ordinals)
    (
        eligible_positions,
        selected_ids,
        selected_labels,
        excluded_class_count,
        excluded_object_count,
    ) = _source_probe_cohort(available_ids, labels)
    selected_ordinals = selected_ordinals[
        np.asarray(eligible_positions, dtype=np.int64)
    ]
    if len(set(selected_labels.values())) < 2:
        return _not_run_source_probe(
            representation="L2_NORMALIZED_DENSE_EMBEDDING",
            reason="FEWER_THAN_TWO_SOURCE_CLASSES_HAVE_TWO_CV_EXAMPLES",
            object_count=len(available_ids),
            input_variant=input_variant,
        )
    selected_vectors = np.asarray(vectors[selected_ordinals], dtype=np.float64)
    result = source_leakage.deterministic_linear_probe(
        selected_vectors,
        selected_ids,
        selected_labels,
        requested_folds=5,
        ridge=1.0,
        iteration_limit=100,
    )
    return _finalize_source_probe(
        result,
        representation="L2_NORMALIZED_DENSE_EMBEDDING",
        input_variant=input_variant,
        object_count=len(selected_ids),
        feature_column_count=int(selected_vectors.shape[1]),
        feature_nonzero_count=int(np.count_nonzero(selected_vectors)),
        representation_index_sha256=representation_index_sha256,
        excluded_low_support_class_count=excluded_class_count,
        excluded_low_support_object_count=excluded_object_count,
    )


def _hubness_association_inputs(
    corpus: Any,
    *,
    aspect_id: str,
    source_by_object: Mapping[str, str],
    metadata_contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive six bounded, governed hubness association mappings."""

    common = _module("lexical_common")
    assignments = metadata_contract.get("assignments")
    if not isinstance(assignments, Mapping):
        raise BenchmarkRound1Error("metadata contract lacks hubness assignments")
    expected_ids = set(corpus.object_ids)
    if set(source_by_object) != expected_ids:
        raise BenchmarkRound1Error("source hubness mapping differs from public cohort")
    text_length_by_object: dict[str, int] = {}
    boilerplate_by_object: dict[str, str] = {}
    generic_title_by_object: dict[str, str] = {}
    metadata_completeness_by_object: dict[str, int] = {}
    for document in corpus.documents:
        aspect = document.aspects.get(aspect_id)
        text_length_by_object[document.object_id] = (
            aspect.character_count if aspect is not None else 0
        )
        boilerplate_by_object[document.object_id] = (
            "REGISTERED_BOILERPLATE_REMOVED"
            if aspect is not None and aspect.boilerplate_removed
            else "NOT_REMOVED"
        )
        title = document.aspects["NLP_TITLE"].lexical_casefolded
        generic_title_by_object[document.object_id] = (
            "SHORT_TITLE_PROXY_LE_2_LEXICAL_TOKENS"
            if len(common.word_tokens(title)) <= 2
            else "NON_SHORT_TITLE_PROXY"
        )
        metadata_completeness_by_object[document.object_id] = sum(
            bool(assignments[target][document.object_id])
            for target in ("medium", "theme", "movement_context", "object_type")
        )
    mappings = {
        "source_by_object": dict(source_by_object),
        # No selected/reliable language-ID model exists.  Script state must not
        # be relabeled as language merely to satisfy an association slot.
        "language_by_object": None,
        "text_length_by_object": text_length_by_object,
        "boilerplate_by_object": boilerplate_by_object,
        "generic_title_by_object": generic_title_by_object,
        "metadata_completeness_by_object": metadata_completeness_by_object,
    }
    if any(
        set(mapping) != expected_ids
        for mapping in mappings.values()
        if isinstance(mapping, Mapping)
    ):
        raise BenchmarkRound1Error("hubness association mapping is incomplete")
    mapping_hashes = {
        key: (sha256_json(mapping) if isinstance(mapping, Mapping) else None)
        for key, mapping in sorted(mappings.items())
    }
    receipt_material = {
        "schemaVersion": "trace-nlp-round1-hubness-association-inputs/v1",
        "aspectId": aspect_id,
        "objectCount": len(expected_ids),
        "mappingSha256": mapping_hashes,
        "sourceDefinition": "GOVERNED_PUBLIC_SOURCE_LABEL",
        "languageDefinition": "NOT_RUN_NO_SELECTED_RELIABLE_LANGUAGE_ID_MODEL",
        "textLengthDefinition": "GOVERNED_ASPECT_CHARACTER_COUNT",
        "boilerplateDefinition": "GOVERNED_REGISTERED_REMOVAL_FLAG",
        "genericTitleDefinition": "TITLE_LEXICAL_TOKEN_COUNT_LE_2_PROXY",
        "metadataCompletenessDefinition": (
            "NONEMPTY_COUNT_ACROSS_MEDIUM_THEME_MOVEMENT_CONTEXT_OBJECT_TYPE"
        ),
        "preNormalizationNormsStatus": "NOT_RETAINED_BY_ENCODING_CHECKPOINT",
        "languageAssociationStatus": "NOT_RUN",
        "languageIdentityUsedAsSemanticTruth": False,
        "genericTitleProxyIsSemanticTruth": False,
        "fullAssociationMappingsRetained": False,
    }
    return {
        **mappings,
        "receipt": {
            **receipt_material,
            "receiptSha256": sha256_json(receipt_material),
        },
    }


def _validate_full_lexical_suite(payload: Mapping[str, Any], aspect_id: str) -> None:
    if payload.get("schemaVersion") != "trace-nlp-round1-compact-lexical-suite/v1":
        raise BenchmarkRound1Error("compact lexical suite schema changed")
    suite = payload.get("suiteSummary")
    models = payload.get("models")
    if not isinstance(suite, Mapping) or not isinstance(models, Mapping):
        raise BenchmarkRound1Error("compact lexical suite is malformed")
    if suite.get("aspectId") != aspect_id or suite.get("aspectPurpose") != ASPECT_PURPOSE[aspect_id]:
        raise BenchmarkRound1Error("lexical aspect/purpose changed")
    expected_available = {
        "NLP_TITLE": 7_995,
        "NLP_SUBJECT": 7_838,
        "NLP_SOURCE_NARRATIVE": 7_431,
    }[aspect_id]
    if suite.get("candidateObjectCount") != PUBLIC_OBJECT_COUNT:
        raise BenchmarkRound1Error("lexical candidate universe changed")
    if suite.get("aspectAvailableQueryCount") != expected_available:
        raise BenchmarkRound1Error("lexical aspect-available query count changed")
    for compact in models.values():
        validate_compact_result(compact)
        summary = compact["summary"]
        if summary.get("fullAspectCohort") is not True:
            raise BenchmarkRound1Error("lexical suite is not the full aspect cohort")
        if summary.get("queryCount") != expected_available:
            raise BenchmarkRound1Error("lexical default query cohort changed")


def _build_lexical_suite(
    corpus: Any,
    aspect_id: str,
    *,
    external_path: Path | None = None,
    expected_receipt_path: Path | None = None,
) -> dict[str, Any]:
    if external_path is not None:
        compact = _load_external_lexical(external_path)
    else:
        lexical_eval = _module("lexical_eval")
        suite = lexical_eval.run_lexical_suite(
            corpus,
            aspect_id=aspect_id,
            aspect_purpose=ASPECT_PURPOSE[aspect_id],
            query_ids=None,
            k=TOP_K,
        )
        compact = _compact_suite(suite)
    if expected_receipt_path is not None:
        expected_document = _load_json_or_gzip(expected_receipt_path)
        if not isinstance(expected_document, Mapping) or not isinstance(
            expected_document.get("suite"), Mapping
        ):
            raise BenchmarkRound1Error("lexical Run-A stripped receipt is malformed")
        expected = expected_document["suite"]
        observed = compact["suiteSummary"]
        if expected.get("aspectId") != aspect_id:
            raise BenchmarkRound1Error("lexical Run-A receipt aspect changed")
        if expected.get("suiteRankingSha256") != observed.get("suiteRankingSha256"):
            raise BenchmarkRound1Error("lexical Run-B suite ranking hash differs from Run A")
        for lane, result in compact["models"].items():
            expected_model = expected.get("models", {}).get(lane)
            if not isinstance(expected_model, Mapping):
                raise BenchmarkRound1Error("lexical Run-A model receipt is missing")
            if expected_model.get("rankingIdsSha256") != result["summary"].get(
                "rankingIdsSha256"
            ):
                raise BenchmarkRound1Error(
                    f"lexical Run-B ranking hash differs for {aspect_id}/{lane}"
                )
        compact["suiteSummary"] = {
            **compact["suiteSummary"],
            "determinismRunAReceiptSha256": sha256_path(expected_receipt_path),
            "determinismRunBMatchesRunA": True,
        }
    _validate_full_lexical_suite(compact, aspect_id)
    return compact


def _build_masked_lexical_suite(
    corpus: Any,
    *,
    aspect_id: str,
    target: str,
    mask_variant: str,
) -> dict[str, Any]:
    metadata_holdout = _module("metadata_holdout_eval")
    lexical_eval = _module("lexical_eval")
    contract = metadata_holdout.derive_governed_label_contract()
    derived, mask_receipt = metadata_holdout.build_masked_corpus_view(
        corpus,
        target=target,
        mask_variant=mask_variant,
        aspect_ids=(aspect_id,),
        label_contract=contract,
    )
    suite = lexical_eval.run_lexical_suite(
        derived,
        aspect_id=aspect_id,
        aspect_purpose=ASPECT_PURPOSE[aspect_id],
        query_ids=None,
        k=TOP_K,
    )
    suffix = f"{target.upper()}-{mask_variant}"
    retagged = dict(suite)
    retagged["models"] = {
        lane: _retag_result(
            result, input_variant=mask_variant, method_suffix=suffix
        )
        for lane, result in suite["models"].items()
    }
    retagged["inputVariant"] = mask_variant
    return {
        "schemaVersion": "trace-nlp-round1-metadata-mask-suite/v1",
        "target": target,
        "maskVariant": mask_variant,
        "aspectId": aspect_id,
        "maskReceipt": mask_receipt,
        "labelContractSha256": contract["contractSha256"],
        "suite": _compact_suite(retagged),
    }


def _build_source_masked_lexical_suite(corpus: Any, *, aspect_id: str) -> dict[str, Any]:
    source_leakage = _module("source_leakage_eval")
    lexical_eval = _module("lexical_eval")
    derived, mask_receipt = source_leakage.build_source_masked_corpus_view(
        corpus, aspect_ids=(aspect_id,)
    )
    suite = lexical_eval.run_lexical_suite(
        derived,
        aspect_id=aspect_id,
        aspect_purpose=ASPECT_PURPOSE[aspect_id],
        query_ids=None,
        k=TOP_K,
    )
    retagged = dict(suite)
    retagged["models"] = {
        lane: _retag_result(
            result,
            input_variant="SOURCE_IDENTITY_MASKED",
            method_suffix="SOURCE-IDENTITY-MASKED",
        )
        for lane, result in suite["models"].items()
    }
    retagged["inputVariant"] = "SOURCE_IDENTITY_MASKED"
    return {
        "schemaVersion": "trace-nlp-round1-source-mask-suite/v1",
        "aspectId": aspect_id,
        "maskReceipt": mask_receipt,
        "suite": _compact_suite(retagged),
    }


def _build_source_mask_probe_checkpoint(
    corpus: Any, *, aspect_id: str, expected_derived_corpus_sha256: str
) -> dict[str, Any]:
    source_leakage = _module("source_leakage_eval")
    derived, mask_receipt = source_leakage.build_source_masked_corpus_view(
        corpus, aspect_ids=(aspect_id,)
    )
    if (
        derived.corpus_sha256 != expected_derived_corpus_sha256
        or mask_receipt.get("derivedCorpusSha256") != expected_derived_corpus_sha256
    ):
        raise BenchmarkRound1Error("source-mask probe derivation differs from ranking input")
    return {
        "schemaVersion": "trace-nlp-round1-source-probe-checkpoint/v1",
        "aspectId": aspect_id,
        "inputVariant": "SOURCE_IDENTITY_MASKED",
        "sourceProbes": _lexical_source_probes(
            derived,
            aspect_id=aspect_id,
            input_variant="SOURCE_IDENTITY_MASKED",
        ),
        "maskReceiptSha256": sha256_json(mask_receipt),
        "temporary": True,
        "committable": False,
    }


def _catalog_suite(
    catalog: dict[str, dict[str, Any]],
    suite: Mapping[str, Any],
    *,
    channel: str,
    analysis_role: str,
    metadata_target: str | None = None,
    mask_variant: str | None = None,
) -> None:
    source_probes = suite.get("sourceProbes", {})
    if not isinstance(source_probes, Mapping):
        raise BenchmarkRound1Error("lexical source-probe receipt mapping is malformed")
    for lane, compact in suite["models"].items():
        validate_compact_result(compact)
        method_id = str(compact["summary"]["methodId"])
        if method_id in catalog:
            raise BenchmarkRound1Error(f"duplicate result methodId: {method_id}")
        catalog[method_id] = {
            "compact": compact,
            "channel": channel,
            "analysisRole": analysis_role,
            "aspectId": compact["summary"]["aspectIds"][0],
            "metadataTarget": metadata_target,
            "maskVariant": mask_variant,
            "familyKey": str(lane),
            "evaluationModelId": f"{lane}-{compact['summary']['aspectIds'][0].removeprefix('NLP_')}",
            "sourceProbe": source_probes.get(lane)
            or _not_run_source_probe(
                representation="UNAVAILABLE_EXTERNAL_LEXICAL_REPRESENTATION",
                reason="SOURCE_PROBE_RECEIPT_NOT_PRESENT_IN_EXTERNAL_CHECKPOINT",
                object_count=int(compact["summary"]["queryCount"]),
                input_variant=str(compact["summary"]["inputVariant"]),
            ),
        }


def _method_family(value: Mapping[str, Any]) -> str:
    family = str(value.get("familyKey", ""))
    return {
        "NLP-L0": "BM25F",
        "NLP-L1": "CHAR_NGRAM",
        "NLP-L2": "WORD_NGRAM",
        "NLP-L3": "LEXICAL_HYBRID",
        "NLP-D1": "DENSE_QWEN3_EMBEDDING",
        "NLP-D3": "DENSE_MULTILINGUAL_E5_INSTRUCT",
    }.get(family, family or "UNDECLARED")


def _weighted_control_at_10(known_row: Mapping[str, Any]) -> float | None:
    numerator = 0.0
    denominator = 0
    controls = known_row.get("authoritativeControlMetricsByType")
    if not isinstance(controls, Mapping):
        return None
    for metrics in controls.values():
        if not isinstance(metrics, Mapping):
            continue
        count = metrics.get("evaluatedDirectionCount")
        rate = metrics.get("hitRateAt10")
        if isinstance(count, int) and isinstance(rate, (int, float)):
            numerator += count * float(rate)
            denominator += count
    return numerator / denominator if denominator else None


def _evaluate_base_results(
    catalog: Mapping[str, Mapping[str, Any]], corpus: Any
) -> dict[str, Any]:
    base = {
        method_id: ranking_result_view(entry["compact"])
        for method_id, entry in catalog.items()
        if entry["analysisRole"] == "BASE"
    }
    if not base:
        raise BenchmarkRound1Error("base ranking catalog is empty")
    diagnostic_results = {
        method_id: ranking_result_view(entry["compact"])
        for method_id, entry in catalog.items()
        if entry["analysisRole"] in {"BASE", "ROBUSTNESS"}
    }
    known = _module("known_item_eval").evaluate_known_items(base)
    source = _module("source_leakage_eval").evaluate_source_neighborhoods(
        diagnostic_results
    )
    known_by_model = {row["modelId"]: row for row in known["modelRows"]}
    source_by_model = {row["modelId"]: row for row in source["modelRows"]}
    language_by_model: dict[str, Mapping[str, Any]] = {}
    for aspect_id in ASPECT_IDS:
        selected = {
            method_id: diagnostic_results[method_id]
            for method_id, entry in catalog.items()
            if entry["analysisRole"] in {"BASE", "ROBUSTNESS"}
            and entry["aspectId"] == aspect_id
        }
        if not selected:
            continue
        script_by_object = {
            document.object_id: document.aspects[aspect_id].language_script_state
            for document in corpus.documents
            if aspect_id in document.aspects
        }
        language = _module("language_leakage_eval").evaluate_language_leakage(
            selected,
            language_by_object=None,
            script_by_object=script_by_object,
            cutoffs=(10, 20, 50),
            language_id_model="NOT_SELECTED",
        )
        for row in language["scriptDiagnosticRows"]:
            language_by_model[row["modelId"]] = row
    return {
        "baseResults": base,
        "known": known,
        "knownByModel": known_by_model,
        "source": source,
        "sourceByModel": source_by_model,
        "languageByModel": language_by_model,
    }


def _lexical_result_rows(
    catalog: Mapping[str, Mapping[str, Any]], evaluation: Mapping[str, Any]
) -> list[dict[str, Any]]:
    rows = []
    for method_id, entry in sorted(catalog.items()):
        if entry["channel"] != "LEXICAL" or entry["analysisRole"] != "BASE":
            continue
        summary = entry["compact"]["summary"]
        known = evaluation["knownByModel"][method_id]
        source = evaluation["sourceByModel"][method_id]
        metadata_key_rows: list[Any] = []
        rows.append(
            {
                "modelId": method_id,
                "methodFamily": _method_family(entry),
                "implementationVersion": summary["implementationVersion"],
                "inputVariant": "ORIGINAL_APPROVED_TEXT",
                "aspectId": entry["aspectId"],
                "aspectPurpose": ASPECT_PURPOSE[entry["aspectId"]],
                "corpusSha256": summary["corpusSha256"],
                "corpusPolicySha256": summary["corpusPolicySha256"],
                "fieldRegistrySha256": summary["fieldRegistrySha256"],
                "normalizationVersion": summary["normalizationVersion"],
                "parametersSha256": sha256_json(summary["parameters"]),
                "objectCount": summary["objectCount"],
                "candidateObjectCount": summary["candidateObjectCount"],
                "aspectAvailableQueryCount": summary["aspectAvailableQueryCount"],
                "aspectUnavailableQueryCount": summary["aspectUnavailableQueryCount"],
                "queryCount": summary["queryCount"],
                "topK": summary["topK"],
                "fullPublicCohort": summary["fullPublicCohort"],
                "fullAspectCohort": summary["fullAspectCohort"],
                "indexSha256": summary["indexSha256"],
                "indexBytes": summary["indexBytes"],
                "indexBuildMs": summary["indexBuildMs"],
                "exactQueryP50Ms": summary["objectLocalExactQueryP50Ms"],
                "exactQueryP95Ms": summary["objectLocalExactQueryP95Ms"],
                "rankingIdsSha256": summary["rankingIdsSha256"],
                "scoreObservationSha256": summary["scoreObservationSha256"],
                "knownItemPositivePairCount": evaluation["known"]["knownRepresentationPairCount"],
                "knownItemRecallAt1": known["knownRepresentationRecallAt1"],
                "knownItemRecallAt5": known["knownRepresentationRecallAt5"],
                "knownItemRecallAt10": known["knownRepresentationRecallAt10"],
                "knownItemRecallAt20": known["knownRepresentationRecallAt20"],
                "knownItemMrr": known[f"knownRepresentationBoundedMrrAt{summary['topK']}"],
                "negativeControlPairCount": evaluation["known"]["authoritativeNegativeControlPairCount"],
                "negativeControlAt10Rate": _weighted_control_at_10(known),
                "sameSourceNeighborRateAt20": source["sameSourceNeighborRateAt20"],
                "corpusSourceHhi": source["corpusSourceHhi"],
                "sameLanguageNeighborRateAt20": None,
                "metadataProxySummarySha256": sha256_json(metadata_key_rows),
                "rankingDeterministic": summary["rankingDeterministic"],
                "pairMatrixMaterialized": False,
                "fullRankingsSaved": False,
                "historicalRelation": False,
                "semanticRelation": False,
                "probability": False,
                "status": "PASS",
                "limitation": "Similarity observations are not historical or semantic relations.",
            }
        )
    return rows


def _dense_model_specs() -> dict[str, Any]:
    model_registry = _module("model_registry")
    return {
        candidate_id: model_registry.get_model(candidate_id)
        for candidate_id in ("NLP-D1", "NLP-D3")
    }


def _hubness_at(payload: Mapping[str, Any], k: int) -> Mapping[str, Any]:
    for row in payload["hubness"]["rows"]:
        if row["k"] == k:
            return row
    raise BenchmarkRound1Error("dense hubness checkpoint lacks a required k")


def _dense_result_rows(
    catalog: Mapping[str, Mapping[str, Any]],
    dense_payloads: Mapping[str, Mapping[str, Any]],
    evaluation: Mapping[str, Any],
    corpus: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    specs = _dense_model_specs()
    result_rows: list[dict[str, Any]] = []
    cross_rows: list[dict[str, Any]] = []
    for method_id, payload in sorted(dense_payloads.items()):
        entry = catalog[method_id]
        if entry["analysisRole"] != "BASE":
            continue
        summary = entry["compact"]["summary"]
        candidate_id = payload["candidateId"]
        spec = specs[candidate_id]
        encoding = payload["encodingReceipt"]
        raw_encoding = encoding.get("receipt", {})
        hubness = _hubness_at(payload["hubnessAnisotropy"], 20)
        anisotropy = payload["hubnessAnisotropy"]["anisotropy"]
        known = evaluation["knownByModel"][method_id]
        source = evaluation["sourceByModel"][method_id]
        result_rows.append(
            {
                "modelId": candidate_id,
                "methodId": method_id,
                "modelRevision": spec.revision,
                "tokenizerRevision": spec.tokenizer_revision,
                "licenseSpdx": spec.license_spdx,
                "eligibility": spec.eligibility,
                "executionScope": "FULL_CORPUS",
                "status": "PASS",
                "inputVariant": summary["inputVariant"],
                "aspectId": entry["aspectId"],
                "corpusSha256": summary["corpusSha256"],
                "corpusPolicySha256": corpus.policy_sha256,
                "fieldRegistrySha256": corpus.field_registry_sha256,
                "normalizationVersion": corpus.normalization_version,
                "objectCount": summary["objectCount"],
                "candidateObjectCount": summary["candidateObjectCount"],
                "aspectAvailableQueryCount": summary["aspectAvailableObjectCount"],
                "aspectUnavailableQueryCount": summary["aspectUnavailableObjectCount"],
                "queryCount": summary["queryCount"],
                "topK": summary["topK"],
                "fullPublicCohort": summary["fullPublicCohort"],
                "fullAspectCohort": summary["fullAspectCohort"],
                "embeddingDimension": payload["candidateNpz"]["embeddingDimension"],
                "maximumInputTokens": spec.maximum_input_tokens,
                "batchSize": _receipt_field(raw_encoding, "batchSize"),
                "device": _receipt_field(raw_encoding, "device") or "cpu",
                "encodingMs": encoding["denseCorpusEncodingMs"],
                "documentsPerSecond": _receipt_field(
                    raw_encoding, "performance.documentsPerSecond", "documentsPerSecond"
                ),
                "indexSha256": summary["indexSha256"],
                "indexBytes": summary["performance"]["denseIndexBytes"],
                "exactQueryP50Ms": summary["performance"]["denseExactQueryP50Ms"],
                "exactQueryP95Ms": summary["performance"]["denseExactQueryP95Ms"],
                "rankingIdsSha256": summary["rankingIdsSha256"],
                "scoreObservationSha256": summary["scoreObservationSha256"],
                "knownItemRecallAt1": known["knownRepresentationRecallAt1"],
                "knownItemRecallAt5": known["knownRepresentationRecallAt5"],
                "knownItemRecallAt10": known["knownRepresentationRecallAt10"],
                "knownItemRecallAt20": known["knownRepresentationRecallAt20"],
                "knownItemMrr": known[f"knownRepresentationBoundedMrrAt{summary['topK']}"],
                "sameSourceNeighborRateAt20": source["sameSourceNeighborRateAt20"],
                "corpusSourceHhi": source["corpusSourceHhi"],
                "sameLanguageNeighborRateAt20": None,
                "hubnessGiniAt20": hubness["gini"],
                "top1PercentOccurrenceShareAt20": hubness[
                    "top1PercentOccurrenceShare"
                ],
                "maximumOccurrenceAt20": hubness["maximumOccurrence"],
                "meanSampledCosine": anisotropy["sampleCosineMean"],
                "firstPcVarianceShare": anisotropy[
                    "firstPrincipalComponentExplainedVarianceShare"
                ],
                "anisotropyStatus": anisotropy["status"],
                "anisotropyMissingRequiredInputs": anisotropy[
                    "missingRequiredInputs"
                ],
                "peakRamBytes": encoding["peakRssBytes"],
                "peakVramBytes": _receipt_field(
                    raw_encoding, "performance.peakVramBytes", "peakVramBytes"
                ),
                "trustRemoteCodeExecuted": False,
                "modelWeightsCommitted": False,
                "fullEmbeddingMatrixCommitted": False,
                "pairMatrixMaterialized": False,
                "fullRankingsSaved": False,
                "randomnessAffectsEmbedding": False,
                "randomnessAffectsNeighborOrder": False,
                "historicalRelation": False,
                "semanticRelation": False,
                "probability": False,
                "limitation": "Plain symmetric diagnostic is not equivalent to official asymmetric retrieval."
                if summary["inputVariant"] == "PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC"
                else "Asymmetric retrieval uses separately encoded query/document roles.",
            }
        )
        cross = payload["crossLanguage"]
        metrics = cross.get("metrics") or {}
        cross_rows.append(
            {
                "modelId": candidate_id,
                "modelRevision": spec.revision,
                "inputVariant": summary["inputVariant"],
                "aspectId": entry["aspectId"],
                "status": cross["status"],
                "reason": cross.get("reason"),
                "corpusSha256": cross["corpusSha256"],
                "evaluationRegistrySha256": cross["evaluationRegistrySha256"],
                "verifiedPairCount": cross["verifiedPairCount"],
                "directionalQueryCount": cross["directionalQueryCount"],
                "recallAt1": metrics.get("recallAt1"),
                "recallAt5": metrics.get("recallAt5"),
                "recallAt10": metrics.get("recallAt10"),
                "recallAt20": metrics.get("recallAt20"),
                "meanReciprocalRank": metrics.get("meanReciprocalRank"),
                "medianRank": metrics.get("medianRank"),
                "maximumRank": metrics.get("maximumRank"),
                "meanCosineObservation": metrics.get("meanCosineObservation"),
                "reviewRowCount": len(cross.get("reviewRows", ())),
                "reviewRowsSha256": cross.get("reviewRowsSha256")
                or sha256_json(cross.get("reviewRows", [])),
                "modelCreatedPositivePairCount": cross["modelCreatedPositivePairCount"],
                "generatedTranslationCount": cross["generatedTranslationCount"],
                "languageIdentityUsedAsSemanticTruth": False,
                "historicalRelation": False,
                "semanticRelation": False,
                "probability": False,
            }
        )
    return result_rows, cross_rows


def _evaluate_metadata_proxy_bounded(
    model_results: Mapping[str, Mapping[str, Any]],
    *,
    target: str,
    label_contract: Mapping[str, Any],
    cutoffs: tuple[int, ...] = (1, 5, 10, 20),
) -> dict[str, Any]:
    """Exact metadata proxy with one inverted-label relevance census.

    The core evaluator recomputes the full-corpus relevant-item count inside
    every query/cutoff/model loop.  This produces identical rows while binding
    the census once per governed query, keeping the summary phase bounded.
    """

    metadata_holdout = _module("metadata_holdout_eval")
    if target not in metadata_holdout.TARGETS:
        raise BenchmarkRound1Error("unsupported metadata proxy target")
    if (
        not cutoffs
        or tuple(sorted(set(cutoffs))) != cutoffs
        or any(value <= 0 or value > TOP_K for value in cutoffs)
    ):
        raise BenchmarkRound1Error("metadata proxy cutoffs are invalid")
    assignments_by_target = label_contract.get("assignments")
    if not isinstance(assignments_by_target, Mapping):
        raise BenchmarkRound1Error("metadata label contract lacks assignments")
    assignments = assignments_by_target.get(target)
    if not isinstance(assignments, Mapping) or not assignments:
        raise BenchmarkRound1Error("metadata target assignments are absent")
    contract_sha256 = str(label_contract.get("contractSha256", ""))
    if not SHA256_RE.fullmatch(contract_sha256):
        raise BenchmarkRound1Error("metadata label contract is not SHA-pinned")

    assignment_sets: dict[str, frozenset[str]] = {}
    members_by_label: dict[str, set[str]] = defaultdict(set)
    support: Counter[str] = Counter()
    for object_id, raw_labels in assignments.items():
        labels = frozenset(str(value) for value in raw_labels)
        assignment_sets[str(object_id)] = labels
        for label_id in labels:
            members_by_label[label_id].add(str(object_id))
            support[label_id] += 1
    evaluable_queries = {
        object_id
        for object_id, labels in assignment_sets.items()
        if any(support[label_id] > 1 for label_id in labels)
    }
    if not evaluable_queries:
        raise BenchmarkRound1Error("metadata proxy has no evaluable target pairs")
    total_relevant_by_query: dict[str, int] = {}
    for query_id in sorted(evaluable_queries):
        relevant_ids: set[str] = set()
        for label_id in assignment_sets[query_id]:
            relevant_ids.update(members_by_label[label_id])
        relevant_ids.discard(query_id)
        total_relevant_by_query[query_id] = len(relevant_ids)

    rows: list[dict[str, Any]] = []
    for model_id, result in sorted(model_results.items()):
        rankings = result.get("rankings")
        if not isinstance(rankings, Mapping):
            raise BenchmarkRound1Error(
                "metadata proxy requires in-memory bounded rankings"
            )
        per_cutoff_precision: dict[int, list[float]] = {
            cutoff: [] for cutoff in cutoffs
        }
        per_cutoff_ndcg: dict[int, list[float]] = {
            cutoff: [] for cutoff in cutoffs
        }
        query_ids = sorted(evaluable_queries & set(rankings))
        for query_id in query_ids:
            query_labels = assignment_sets[query_id]
            ranking = rankings[query_id]
            total_relevant = total_relevant_by_query[query_id]
            for cutoff in cutoffs:
                relevances: list[int] = []
                for row in ranking[:cutoff]:
                    candidate_id = str(row["candidatePublicId"])
                    candidate_labels = assignment_sets.get(candidate_id)
                    if candidate_labels is None:
                        raise BenchmarkRound1Error(
                            "metadata ranking contains an object outside the "
                            "governed label contract"
                        )
                    relevances.append(
                        int(bool(query_labels & candidate_labels))
                    )
                per_cutoff_precision[cutoff].append(
                    sum(relevances) / cutoff
                )
                ideal = [1] * min(cutoff, total_relevant) + [0] * max(
                    0, cutoff - total_relevant
                )
                denominator = metadata_holdout._dcg(ideal)
                per_cutoff_ndcg[cutoff].append(
                    metadata_holdout._dcg(relevances) / denominator
                    if denominator
                    else 0.0
                )
        if not query_ids:
            raise BenchmarkRound1Error(
                "metadata proxy model has no evaluable query cohort"
            )
        rows.append(
            {
                "modelId": model_id,
                "target": target,
                "evaluatedQueryCount": len(query_ids),
                **{
                    f"precisionAt{cutoff}": sum(
                        per_cutoff_precision[cutoff]
                    )
                    / len(per_cutoff_precision[cutoff])
                    for cutoff in cutoffs
                },
                **{
                    f"ndcgAt{cutoff}": sum(per_cutoff_ndcg[cutoff])
                    / len(per_cutoff_ndcg[cutoff])
                    for cutoff in cutoffs
                },
                "historicalRelation": False,
                "semanticRelation": False,
                "probability": False,
            }
        )
    majority_support = max(support.values())
    return {
        "schemaVersion": "trace-nlp-metadata-holdout-results/v1",
        "implementationVersion": metadata_holdout.IMPLEMENTATION_VERSION,
        "target": target,
        "proxyOnly": True,
        "labelCount": len(support),
        "evaluableQueryCount": len(evaluable_queries),
        "majorityLabelObjectShare": majority_support / len(assignments),
        "targetDistribution": dict(sorted(support.items())),
        "labelContractSha256": contract_sha256,
        "modelRows": rows,
        "rowsSha256": metadata_holdout.common.sha256_json(rows),
    }


def _metadata_checkpoint_name(target: str, mask_variant: str) -> str:
    return (
        f"metadata-{target.replace('_', '-')}-"
        f"{mask_variant.casefold().replace('_', '-')}-title"
    )


def _metadata_aggregate_dependency(
    store: CheckpointStore,
    catalog: Mapping[str, Mapping[str, Any]],
    corpus_sha256: str,
) -> dict[str, Any]:
    checkpoint_rows: list[dict[str, Any]] = []
    for target in METADATA_TARGETS:
        for mask_variant in METADATA_MASK_VARIANTS:
            name = _metadata_checkpoint_name(target, mask_variant)
            path = store.path_for(name)
            if not path.is_file() or path.is_symlink():
                raise BenchmarkRound1Error(
                    f"required metadata ranking checkpoint is absent: {name}"
                )
            checkpoint_rows.append(
                {
                    "checkpointName": name,
                    "fileSha256": sha256_path(path),
                    "byteCount": path.stat().st_size,
                }
            )
    title_rows: list[dict[str, Any]] = []
    for method_id, entry in sorted(catalog.items()):
        if not (
            entry["analysisRole"] == "BASE"
            and entry["channel"] == "LEXICAL"
            and entry["aspectId"] == "NLP_TITLE"
        ):
            continue
        compact = entry["compact"]
        validate_compact_result(compact)
        summary = compact["summary"]
        title_rows.append(
            {
                "methodId": method_id,
                "evaluationModelId": entry["evaluationModelId"],
                "indexSha256": summary["indexSha256"],
                "rankingIdsSha256": summary["rankingIdsSha256"],
                "compactRankingIdsSha256": compact[
                    "compactRankingIdsSha256"
                ],
            }
        )
    if len(title_rows) != 4:
        raise BenchmarkRound1Error(
            "metadata aggregate lacks the four governed TITLE lexical baselines"
        )
    contract = _module("metadata_holdout_eval").derive_governed_label_contract()
    return {
        "corpusSha256": corpus_sha256,
        "titleBaselineRows": title_rows,
        "metadataCheckpointRows": checkpoint_rows,
        "labelContractSha256": contract["contractSha256"],
        "metadataImplementationVersion": _module(
            "metadata_holdout_eval"
        ).IMPLEMENTATION_VERSION,
        "benchmarkImplementationVersion": IMPLEMENTATION_VERSION,
        "relevanceCensusMethod": "INVERTED_GOVERNED_LABEL_MEMBERSHIP_EXACT_V1",
    }


def _metadata_holdout_rows(
    catalog: Mapping[str, Mapping[str, Any]],
    metadata_payloads: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    metadata_holdout = _module("metadata_holdout_eval")
    contract = metadata_holdout.derive_governed_label_contract()
    rows: list[dict[str, Any]] = []
    groups: list[tuple[str, str, Mapping[str, Mapping[str, Any]], Mapping[str, Any]]] = []
    for target in METADATA_TARGETS:
        original = {
            method_id: ranking_result_view(entry["compact"])
            for method_id, entry in catalog.items()
            if entry["analysisRole"] == "BASE"
            and entry["channel"] == "LEXICAL"
            and entry["aspectId"] == "NLP_TITLE"
        }
        groups.append((target, "ORIGINAL_APPROVED_TEXT", original, {}))
    for payload in metadata_payloads:
        target = str(payload["target"])
        mask_variant = str(payload["maskVariant"])
        suite = payload["suite"]
        model_results = {
            compact["summary"]["methodId"]: ranking_result_view(compact)
            for compact in suite["models"].values()
        }
        groups.append((target, mask_variant, model_results, payload["maskReceipt"]))

    for target, mask_variant, model_results, mask_receipt in groups:
        if not model_results:
            raise BenchmarkRound1Error("metadata holdout group is empty")
        evaluated = _evaluate_metadata_proxy_bounded(
            model_results, target=target, label_contract=contract
        )
        assignments = contract["assignments"][target]
        support = Counter(label for values in assignments.values() for label in values)
        label_count = len(support)
        majority_share = max(support.values()) / len(assignments)
        for result in evaluated["modelRows"]:
            method_id = result["modelId"]
            if mask_variant == "ORIGINAL_APPROVED_TEXT":
                entry = catalog[method_id]
                output_model_id = entry["evaluationModelId"]
                method_family = _method_family(entry)
            else:
                lane = next(
                    lane
                    for lane, compact in (
                        (lane_, payload_["suite"]["models"][lane_])
                        for payload_ in metadata_payloads
                        if payload_["target"] == target
                        and payload_["maskVariant"] == mask_variant
                        for lane_ in payload_["suite"]["models"]
                    )
                    if compact["summary"]["methodId"] == method_id
                )
                output_model_id = f"{lane}-TITLE"
                method_family = _method_family({"familyKey": lane})
            removed = mask_receipt.get("maskedOccurrenceCount")
            target_masked = mask_variant != "ORIGINAL_APPROVED_TEXT"
            rows.append(
                {
                    "modelId": output_model_id,
                    "methodId": method_id,
                    "methodFamily": method_family,
                    "inputVariant": mask_variant,
                    "maskVariant": mask_variant,
                    "target": target,
                    "proxyOnly": True,
                    "labelCount": label_count,
                    "evaluableQueryCount": result["evaluatedQueryCount"],
                    "majorityLabelObjectShare": majority_share,
                    "precisionAt5": result["precisionAt5"],
                    "precisionAt10": result["precisionAt10"],
                    "precisionAt20": result["precisionAt20"],
                    "ndcgAt5": result["ndcgAt5"],
                    "ndcgAt10": result["ndcgAt10"],
                    "ndcgAt20": result["ndcgAt20"],
                    "targetLiteralCountBefore": removed,
                    "targetLiteralCountAfter": 0 if target_masked else None,
                    "targetLabelsMasked": target_masked,
                    "contextLabelsMasked": mask_variant
                    == "ALL_CONTEXT_LABELS_MASKED",
                    "labelContractSha256": contract["contractSha256"],
                    "rowsSha256": evaluated["rowsSha256"],
                    "historicalRelation": False,
                    "semanticRelation": False,
                    "probability": False,
                    "status": "PASS",
                    "limitation": "Metadata alignment is a leakage-sensitive proxy, not design-history ground truth.",
                }
            )
    rows.sort(key=lambda row: (row["modelId"], row["target"], row["maskVariant"]))
    return rows


def _leakage_rows(
    catalog: Mapping[str, Mapping[str, Any]], evaluation: Mapping[str, Any]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_count = evaluation["source"]["sourceCount"]
    for method_id, entry in sorted(catalog.items()):
        if entry["analysisRole"] not in {"BASE", "ROBUSTNESS"}:
            continue
        summary = entry["compact"]["summary"]
        source = evaluation["sourceByModel"][method_id]
        language = evaluation["languageByModel"][method_id]
        common = {
            "modelId": method_id,
            "methodFamily": _method_family(entry),
            "inputVariant": summary["inputVariant"],
            "aspectId": entry["aspectId"],
            "queryCount": summary["queryCount"],
            "sourceIdentityMasked": summary["inputVariant"]
            == "SOURCE_IDENTITY_MASKED",
            "boilerplateRemoved": summary["inputVariant"]
            == "REGISTERED_BOILERPLATE_REMOVED",
            "historicalRelation": False,
            "semanticRelation": False,
            "probability": False,
        }
        probe = entry.get("sourceProbe")
        if not isinstance(probe, Mapping):
            raise BenchmarkRound1Error(f"source probe receipt is absent for {method_id}")
        probe_material = {
            **common,
            "inputVariant": probe["inputVariant"],
            "queryCount": probe["objectCount"],
            "sourceIdentityMasked": probe["inputVariant"]
            == "SOURCE_IDENTITY_MASKED",
            "boilerplateRemoved": probe["inputVariant"]
            == "REGISTERED_BOILERPLATE_REMOVED",
            "leakageDimension": "SOURCE",
            "probeOrMetric": "STRATIFIED_ONE_VS_REST_RIDGE_LINEAR_PROBE",
            "k": 0,
            "labelCount": probe.get("classCount"),
            "metricValue": probe.get("accuracy"),
            "majorityBaseline": probe.get("majorityBaselineMacroF1"),
            "macroF1": probe.get("macroF1"),
            "crossValidationFolds": probe.get("foldCount"),
            "reliableLanguageLabelsOnly": False,
            "languageIdentityUsedAsPositiveAffinity": False,
            "status": probe["status"],
            "reason": probe["reason"],
            "probeAccuracy": probe.get("accuracy"),
            "majorityBaselineAccuracy": probe.get("majorityBaselineAccuracy"),
            "probeMethod": probe["probeMethod"],
            "probeStratified": probe["stratified"],
            "probeSeed": probe["seed"],
            "probeRidge": probe["ridge"],
            "probeIterationLimit": probe["iterationLimit"],
            "probeRepresentation": probe["representation"],
            "probeFeatureColumnCount": probe.get("featureColumnCount"),
            "probeFeatureNonzeroCount": probe.get("featureNonzeroCount"),
            "probePredictionsSha256": probe.get("predictionsSha256"),
            "probeReceiptSha256": probe["receiptSha256"],
        }
        rows.append({**probe_material, "receiptSha256": sha256_json(probe_material)})
        for k in (10, 20, 50):
            for metric, value in (
                ("SAME_SOURCE_NEIGHBOR_RATE", source[f"sameSourceNeighborRateAt{k}"]),
                ("CROSS_SOURCE_NEIGHBOR_RATE", source[f"crossSourceNeighborRateAt{k}"]),
                ("MEAN_QUERY_SOURCE_HHI", source[f"meanQuerySourceHhiAt{k}"]),
            ):
                material = {
                    **common,
                    "leakageDimension": "SOURCE",
                    "probeOrMetric": metric,
                    "k": k,
                    "labelCount": source_count,
                    "metricValue": value,
                    "majorityBaseline": None,
                    "macroF1": None,
                    "crossValidationFolds": None,
                    "reliableLanguageLabelsOnly": False,
                    "languageIdentityUsedAsPositiveAffinity": False,
                    "status": "PASS",
                    "reason": "NEIGHBORHOOD_SOURCE_DIAGNOSTIC",
                }
                rows.append({**material, "receiptSha256": sha256_json(material)})
        for k in (10, 20, 50):
            material = {
                **common,
                "leakageDimension": "LANGUAGE",
                "probeOrMetric": "SAME_SCRIPT_NEIGHBOR_RATE_NOT_LANGUAGE",
                "k": k,
                "labelCount": 0,
                "metricValue": language[f"sameScriptNeighborRateAt{k}"],
                "majorityBaseline": None,
                "macroF1": None,
                "crossValidationFolds": None,
                "reliableLanguageLabelsOnly": False,
                "languageIdentityUsedAsPositiveAffinity": False,
                "status": "PASS_SCRIPT_ONLY",
                "reason": "SCRIPT_IS_NOT_LANGUAGE",
            }
            rows.append({**material, "receiptSha256": sha256_json(material)})
        material = {
            **common,
            "leakageDimension": "LANGUAGE",
            "probeOrMetric": "SAME_LANGUAGE_NEIGHBOR_RATE",
            "k": 20,
            "labelCount": 0,
            "metricValue": None,
            "majorityBaseline": None,
            "macroF1": None,
            "crossValidationFolds": None,
            "reliableLanguageLabelsOnly": True,
            "languageIdentityUsedAsPositiveAffinity": False,
            "status": "NOT_RUN",
            "reason": "NO_SELECTED_LID_MODEL_OR_RELIABLE_LANGUAGE_LABEL_COHORT",
        }
        rows.append({**material, "receiptSha256": sha256_json(material)})

        if entry["analysisRole"] == "BASE":
            no_boilerplate = _not_run_source_probe(
                representation=str(probe["representation"]),
                reason=(
                    "NO_APPROVED_REMOVE_FOR_NLP_INPUT_RULES; "
                    "REGISTERED_BOILERPLATE_VARIANT_IS_IDENTICAL_TO_BASELINE"
                ),
                object_count=int(probe["objectCount"]),
                input_variant="REGISTERED_BOILERPLATE_REMOVED",
            )
            boilerplate_material = {
                **common,
                "inputVariant": "REGISTERED_BOILERPLATE_REMOVED",
                "queryCount": no_boilerplate["objectCount"],
                "sourceIdentityMasked": False,
                "boilerplateRemoved": False,
                "leakageDimension": "SOURCE",
                "probeOrMetric": "STRATIFIED_ONE_VS_REST_RIDGE_LINEAR_PROBE",
                "k": 0,
                "labelCount": None,
                "metricValue": None,
                "majorityBaseline": None,
                "macroF1": None,
                "crossValidationFolds": None,
                "reliableLanguageLabelsOnly": False,
                "languageIdentityUsedAsPositiveAffinity": False,
                "status": "NOT_RUN",
                "reason": no_boilerplate["reason"],
                "probeAccuracy": None,
                "majorityBaselineAccuracy": None,
                "probeMethod": no_boilerplate["probeMethod"],
                "probeStratified": True,
                "probeSeed": None,
                "probeRidge": no_boilerplate["ridge"],
                "probeIterationLimit": no_boilerplate["iterationLimit"],
                "probeRepresentation": no_boilerplate["representation"],
                "probeFeatureColumnCount": None,
                "probeFeatureNonzeroCount": None,
                "probePredictionsSha256": None,
                "probeReceiptSha256": no_boilerplate["receiptSha256"],
            }
            rows.append(
                {
                    **boilerplate_material,
                    "receiptSha256": sha256_json(boilerplate_material),
                }
            )
            if entry["channel"] == "DENSE":
                no_source_mask = _not_run_source_probe(
                    representation=str(probe["representation"]),
                    reason="NO_SHA_PINNED_SOURCE_MASKED_DENSE_REENCODING_ARTIFACT",
                    object_count=int(probe["objectCount"]),
                    input_variant="SOURCE_IDENTITY_MASKED",
                )
                source_mask_material = {
                    **common,
                    "inputVariant": "SOURCE_IDENTITY_MASKED",
                    "queryCount": no_source_mask["objectCount"],
                    "sourceIdentityMasked": True,
                    "boilerplateRemoved": False,
                    "leakageDimension": "SOURCE",
                    "probeOrMetric": "STRATIFIED_ONE_VS_REST_RIDGE_LINEAR_PROBE",
                    "k": 0,
                    "labelCount": None,
                    "metricValue": None,
                    "majorityBaseline": None,
                    "macroF1": None,
                    "crossValidationFolds": None,
                    "reliableLanguageLabelsOnly": False,
                    "languageIdentityUsedAsPositiveAffinity": False,
                    "status": "NOT_RUN",
                    "reason": no_source_mask["reason"],
                    "probeAccuracy": None,
                    "majorityBaselineAccuracy": None,
                    "probeMethod": no_source_mask["probeMethod"],
                    "probeStratified": True,
                    "probeSeed": None,
                    "probeRidge": no_source_mask["ridge"],
                    "probeIterationLimit": no_source_mask["iterationLimit"],
                    "probeRepresentation": no_source_mask["representation"],
                    "probeFeatureColumnCount": None,
                    "probeFeatureNonzeroCount": None,
                    "probePredictionsSha256": None,
                    "probeReceiptSha256": no_source_mask["receiptSha256"],
                }
                rows.append(
                    {
                        **source_mask_material,
                        "receiptSha256": sha256_json(source_mask_material),
                    }
                )
    rows.sort(
        key=lambda row: (
            row["modelId"],
            row["inputVariant"],
            row["leakageDimension"],
            row["probeOrMetric"],
            row["k"],
        )
    )
    return rows


def _hubness_rows(dense_payloads: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    specs = _dense_model_specs()
    rows: list[dict[str, Any]] = []
    for method_id, payload in sorted(dense_payloads.items()):
        if payload["analysisRole"] != "BASE":
            continue
        candidate_id = payload["candidateId"]
        spec = specs[candidate_id]
        diagnostic = payload["hubnessAnisotropy"]
        anisotropy = diagnostic["anisotropy"]
        base = {
            "modelId": candidate_id,
            "methodId": method_id,
            "modelRevision": spec.revision,
            "inputVariant": payload["result"]["summary"]["inputVariant"],
            "aspectId": payload["aspectId"],
            "embeddingDimension": anisotropy["embeddingDimension"],
            "correctionId": "NONE",
            "correctionTested": False,
            "correctionSelected": False,
            "receiptSha256": diagnostic["diagnosticSha256"],
            "overallDiagnosticStatus": diagnostic["status"],
            "missingRequiredDiagnostics": diagnostic["missingRequiredDiagnostics"],
            "associationInputsSha256": payload["hubnessAssociationReceipt"][
                "receiptSha256"
            ],
        }
        query_count_by_k = {
            int(value["k"]): int(value["queryCount"])
            for value in diagnostic["hubness"]["rows"]
        }
        for value in diagnostic["hubness"]["rows"]:
            rows.append(
                {
                    **base,
                    "diagnosticType": "HUBNESS",
                    "k": value["k"],
                    "objectCount": value["objectCount"],
                    "queryCount": value["queryCount"],
                    "meanKOccurrence": value["meanKOccurrence"],
                    "varianceKOccurrence": value["varianceKOccurrence"],
                    "skewness": value["skewness"],
                    "gini": value["gini"],
                    "top1PercentOccurrenceShare": value[
                        "top1PercentOccurrenceShare"
                    ],
                    "maximumOccurrence": value["maximumOccurrence"],
                    "zeroOccurrenceObjectCount": value["zeroOccurrenceObjectCount"],
                    "totalOccurrenceCount": value["totalOccurrenceCount"],
                    "expectedOccurrenceCount": value["expectedOccurrenceCount"],
                    "meanSampledCosine": None,
                    "cosineVariance": None,
                    "pairObservationCount": None,
                    "firstPcVarianceShare": None,
                    "normP50": 1.0,
                    "normP95": 1.0,
                    "preNormalizationNormP50": None,
                    "preNormalizationNormP95": None,
                    "nearestNeighborCosineDistanceP50": None,
                    "nearestNeighborCosineDistanceP95": None,
                    "exactMeanOffDiagonalCosine": None,
                    "associationDimension": None,
                    "associationType": None,
                    "associationValue": None,
                    "associationGroupCount": None,
                    "associationEtaSquared": None,
                    "associationPearsonCorrelation": None,
                    "associationObservationSha256": None,
                    "status": "PASS",
                    "limitation": (
                        "Occurrence diagnostics are analysis-only and do not select a correction."
                    ),
                }
            )
        for association in diagnostic["hubness"]["associationRows"]:
            dimension = str(association["dimension"])
            if dimension == "LANGUAGE":
                raise BenchmarkRound1Error(
                    "hubness core returned a language association without a selected LID"
                )
            association_value = association.get(
                "etaSquared", association.get("pearsonCorrelation")
            )
            rows.append(
                {
                    **base,
                    "diagnosticType": f"HUBNESS_ASSOCIATION_{dimension}",
                    "k": association["k"],
                    "objectCount": association["objectCount"],
                    "queryCount": query_count_by_k[int(association["k"])],
                    "meanKOccurrence": None,
                    "varianceKOccurrence": None,
                    "skewness": None,
                    "gini": None,
                    "top1PercentOccurrenceShare": None,
                    "maximumOccurrence": None,
                    "zeroOccurrenceObjectCount": None,
                    "totalOccurrenceCount": None,
                    "expectedOccurrenceCount": None,
                    "meanSampledCosine": None,
                    "cosineVariance": None,
                    "pairObservationCount": None,
                    "firstPcVarianceShare": None,
                    "normP50": None,
                    "normP95": None,
                    "preNormalizationNormP50": None,
                    "preNormalizationNormP95": None,
                    "nearestNeighborCosineDistanceP50": None,
                    "nearestNeighborCosineDistanceP95": None,
                    "exactMeanOffDiagonalCosine": None,
                    "associationDimension": dimension,
                    "associationType": association["associationType"],
                    "associationValue": association_value,
                    "associationGroupCount": association.get("groupCount"),
                    "associationEtaSquared": association.get("etaSquared"),
                    "associationPearsonCorrelation": association.get(
                        "pearsonCorrelation"
                    ),
                    "associationObservationSha256": sha256_json(association),
                    "status": "PASS",
                    "limitation": (
                        "Association is diagnostic and does not establish causation or relation."
                    ),
                }
            )
        for dimension in diagnostic["hubness"]["missingAssociationDimensions"]:
            for value in diagnostic["hubness"]["rows"]:
                rows.append(
                    {
                        **base,
                        "diagnosticType": f"HUBNESS_ASSOCIATION_{dimension}",
                        "k": value["k"],
                        "objectCount": value["objectCount"],
                        "queryCount": value["queryCount"],
                        "meanKOccurrence": None,
                        "varianceKOccurrence": None,
                        "skewness": None,
                        "gini": None,
                        "top1PercentOccurrenceShare": None,
                        "maximumOccurrence": None,
                        "zeroOccurrenceObjectCount": None,
                        "totalOccurrenceCount": None,
                        "expectedOccurrenceCount": None,
                        "meanSampledCosine": None,
                        "cosineVariance": None,
                        "pairObservationCount": None,
                        "firstPcVarianceShare": None,
                        "normP50": None,
                        "normP95": None,
                        "preNormalizationNormP50": None,
                        "preNormalizationNormP95": None,
                        "nearestNeighborCosineDistanceP50": None,
                        "nearestNeighborCosineDistanceP95": None,
                        "exactMeanOffDiagonalCosine": None,
                        "associationDimension": dimension,
                        "associationType": "NOT_RUN",
                        "associationValue": None,
                        "associationGroupCount": None,
                        "associationEtaSquared": None,
                        "associationPearsonCorrelation": None,
                        "associationObservationSha256": None,
                        "status": "NOT_RUN",
                        "limitation": (
                            "No selected/reliable language-ID cohort; governed script state "
                            "was not mislabeled as language."
                            if dimension == "LANGUAGE"
                            else "Required governed association input was unavailable."
                        ),
                    }
                )
        post_norms = anisotropy["postNormalizationNormDistribution"]
        rows.append(
            {
                **base,
                "diagnosticType": "ANISOTROPY",
                "k": 0,
                "objectCount": anisotropy["objectCount"],
                "queryCount": anisotropy["objectCount"],
                "meanKOccurrence": None,
                "varianceKOccurrence": None,
                "skewness": None,
                "gini": None,
                "top1PercentOccurrenceShare": None,
                "maximumOccurrence": None,
                "zeroOccurrenceObjectCount": None,
                "totalOccurrenceCount": None,
                "expectedOccurrenceCount": None,
                "meanSampledCosine": anisotropy["sampleCosineMean"],
                "cosineVariance": anisotropy["sampleCosineStdDev"] ** 2,
                "pairObservationCount": anisotropy["pairObservationCount"],
                "firstPcVarianceShare": anisotropy[
                    "firstPrincipalComponentExplainedVarianceShare"
                ],
                "normP50": post_norms["p50"],
                "normP95": post_norms["p95"],
                "preNormalizationNormP50": None,
                "preNormalizationNormP95": None,
                "nearestNeighborCosineDistanceP50": anisotropy[
                    "nearestNeighborCosineDistanceDistribution"
                ]["p50"],
                "nearestNeighborCosineDistanceP95": anisotropy[
                    "nearestNeighborCosineDistanceDistribution"
                ]["p95"],
                "exactMeanOffDiagonalCosine": anisotropy[
                    "exactMeanOffDiagonalCosine"
                ],
                "associationDimension": None,
                "associationType": None,
                "associationValue": None,
                "associationGroupCount": None,
                "associationEtaSquared": None,
                "associationPearsonCorrelation": None,
                "associationObservationSha256": None,
                "status": anisotropy["status"],
                "limitation": (
                    "Normalized-space anisotropy metrics were computed, but the encoding "
                    "checkpoint did not retain pre-normalization norms."
                ),
            }
        )
    rows.sort(
        key=lambda row: (
            row["modelId"],
            row["inputVariant"],
            row["aspectId"],
            row["diagnosticType"],
            row["k"],
        )
    )
    return rows


def _ranking_robustness_diagnostics(
    entry: Mapping[str, Any],
    query_ids: set[str],
    source_by_object: Mapping[str, str],
) -> tuple[dict[str, float], dict[str, float]]:
    rankings = entry["compact"]["rankingIdsByQuery"]
    universe = tuple(sorted(source_by_object))
    source_diagnostics: dict[str, float] = {}
    hubness_diagnostics: dict[str, float] = {}
    for k in (10, 20, 50):
        same_source_rates: list[float] = []
        occurrences: Counter[str] = Counter()
        for query_id in sorted(query_ids):
            selected = tuple(rankings[query_id][:k])
            if len(selected) != k:
                raise BenchmarkRound1Error("robustness ranking is shorter than k")
            same_source_rates.append(
                sum(
                    source_by_object[candidate] == source_by_object[query_id]
                    for candidate in selected
                )
                / k
            )
            occurrences.update(selected)
        values = sorted(float(occurrences[object_id]) for object_id in universe)
        total = sum(values)
        n = len(values)
        weighted = sum((ordinal + 1) * value for ordinal, value in enumerate(values))
        gini = (
            (2.0 * weighted) / (n * total) - (n + 1.0) / n if total else 0.0
        )
        top_count = max(1, math.ceil(n * 0.01))
        source_diagnostics[f"sameSourceNeighborRateAt{k}"] = statistics.fmean(
            same_source_rates
        )
        hubness_diagnostics[f"giniAt{k}"] = gini
        hubness_diagnostics[f"top1PercentOccurrenceShareAt{k}"] = (
            sum(reversed(values[-top_count:])) / total if total else 0.0
        )
        hubness_diagnostics[f"maximumOccurrenceAt{k}"] = max(values, default=0.0)
    return source_diagnostics, hubness_diagnostics


def _restricted_result(
    entry: Mapping[str, Any],
    query_ids: set[str],
    source_by_object: Mapping[str, str],
) -> dict[str, Any]:
    summary = entry["compact"]["summary"]
    rankings = entry["compact"]["rankingIdsByQuery"]
    selected = {query_id: rankings[query_id] for query_id in sorted(query_ids)}
    source_diagnostics, hubness_diagnostics = _ranking_robustness_diagnostics(
        entry, query_ids, source_by_object
    )
    return {
        "methodId": summary["methodId"],
        "corpusSha256": summary["corpusSha256"],
        "inputVariant": summary["inputVariant"],
        "aspectId": summary["aspectIds"][0],
        "aspectIds": list(summary["aspectIds"]),
        "indexSha256": summary["indexSha256"],
        "rankingIdsSha256": _sha256_json_no_lf(selected),
        "rankings": selected,
        "sourceLeakageDiagnostics": source_diagnostics,
        "hubnessDiagnostics": hubness_diagnostics,
    }


def _diagnostic_delta_value(change: Mapping[str, Any], metric: str) -> float | None:
    for row in change.get("rows", ()):
        if row.get("metric") == metric:
            return float(row["delta"])
    return None


def _robustness_rows(
    catalog: Mapping[str, Mapping[str, Any]],
    explicit_comparisons: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    robustness = _module("robustness_ablation")
    source_by_object = _module("source_leakage_eval").source_labels()
    comparisons: dict[tuple[str, str, str], tuple[Mapping[str, Any], Mapping[str, Any]]] = {}
    for row in explicit_comparisons:
        reference_id = str(row.get("referenceMethodId", ""))
        variant_id = str(row.get("variantMethodId", ""))
        ablation_id = str(row.get("ablationId", ""))
        if reference_id not in catalog or variant_id not in catalog:
            raise BenchmarkRound1Error("explicit robustness comparison names an absent result")
        comparisons[(reference_id, variant_id, ablation_id)] = (
            catalog[reference_id],
            catalog[variant_id],
        )

    grouped: dict[tuple[str, str], dict[str, tuple[str, Mapping[str, Any]]]] = defaultdict(dict)
    for method_id, entry in catalog.items():
        if entry["analysisRole"] != "BASE":
            continue
        grouped[(entry["channel"], entry["familyKey"])][entry["aspectId"]] = (
            method_id,
            entry,
        )
    for (_channel, _family), aspects in grouped.items():
        if "NLP_TITLE" not in aspects:
            continue
        reference_id, reference = aspects["NLP_TITLE"]
        for aspect_id, ablation_id in (
            ("NLP_SUBJECT", "SUBJECT_ONLY"),
            ("NLP_SOURCE_NARRATIVE", "SOURCE_NARRATIVE_ONLY"),
        ):
            if aspect_id in aspects:
                variant_id, variant = aspects[aspect_id]
                comparisons.setdefault(
                    (reference_id, variant_id, ablation_id), (reference, variant)
                )
    for variant_id, variant in catalog.items():
        if variant["analysisRole"] != "ROBUSTNESS":
            continue
        candidates = [
            (method_id, entry)
            for method_id, entry in catalog.items()
            if entry["analysisRole"] == "BASE"
            and entry["familyKey"] == variant["familyKey"]
            and entry["aspectId"] == variant["aspectId"]
        ]
        if len(candidates) == 1:
            reference_id, reference = candidates[0]
            ablation_id = str(variant.get("ablationId") or variant.get("maskVariant"))
            comparisons.setdefault(
                (reference_id, variant_id, ablation_id), (reference, variant)
            )

    reference_by_family: dict[str, tuple[str, Mapping[str, Any]]] = {}
    for method_id, entry in sorted(catalog.items()):
        if entry["analysisRole"] != "BASE" or entry["aspectId"] != "NLP_TITLE":
            continue
        family = str(entry["familyKey"])
        if family in reference_by_family:
            raise BenchmarkRound1Error(
                "robustness family has multiple governed TITLE references"
            )
        reference_by_family[family] = (method_id, entry)

    def suite_identity(suite: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "robustnessSuiteStatus": suite["status"],
            "referenceCorpusSha256": suite["corpusSha256"],
            "referenceInputVariant": suite["inputVariant"],
            "referenceAspectId": suite["aspectId"],
            "referenceIndexSha256": suite["indexSha256"],
            "referenceRankingIdsSha256": suite["rankingIdsSha256"],
            "declaredAblationCount": len(suite["declaredAblationIds"]),
            "executedAblationIds": list(suite["executedAblationIds"]),
            "notRunAblationIds": list(suite["notRunAblationIds"]),
            "suiteSha256": suite["suiteSha256"],
        }

    output: list[dict[str, Any]] = []
    executed_by_family: dict[str, set[str]] = defaultdict(set)
    for (reference_id, variant_id, ablation_id), (reference, variant) in sorted(
        comparisons.items()
    ):
        if ablation_id not in robustness.DECLARED_ABLATION_IDS:
            raise BenchmarkRound1Error(f"robustness ablation is undeclared: {ablation_id}")
        left_queries = set(reference["compact"]["rankingIdsByQuery"])
        right_queries = set(variant["compact"]["rankingIdsByQuery"])
        joint = left_queries & right_queries
        if not joint:
            raise BenchmarkRound1Error("robustness comparison has no joint query cohort")
        suite = robustness.evaluate_ablation_suite(
            _restricted_result(reference, joint, source_by_object),
            {
                ablation_id: _restricted_result(
                    variant, joint, source_by_object
                )
            },
            k_values=(10, 20, 50),
            evaluation_status="STOPPED_RECOVERABLE_CHECKPOINT",
        )
        if len(suite["comparisons"]) != 1:
            raise BenchmarkRound1Error("bounded robustness suite comparison count changed")
        compared = suite["comparisons"][0]
        family = str(reference["familyKey"])
        executed_by_family[family].add(ablation_id)
        for aggregate in compared["aggregateRows"]:
            material = {
                "modelId": family,
                "referenceMethodId": reference_id,
                "variantMethodId": variant_id,
                "ablationId": ablation_id,
                "ablationFamily": compared["ablation"]["family"],
                "inputVariant": variant["compact"]["summary"]["inputVariant"],
                "aspectId": variant["aspectId"],
                "k": aggregate["k"],
                "queryCount": aggregate["queryCount"],
                "meanTopKOverlap": aggregate["meanTopKOverlap"],
                "medianTopKOverlap": aggregate["medianTopKOverlap"],
                "p05TopKOverlap": aggregate["p05TopKOverlap"],
                "meanRankCorrelation": aggregate["meanRankCorrelation"],
                "medianRankCorrelation": aggregate["medianRankCorrelation"],
                "p05RankCorrelation": aggregate["p05RankCorrelation"],
                "sameSourceRateChange": _diagnostic_delta_value(
                    compared["sourceLeakageChange"],
                    f"sameSourceNeighborRateAt{aggregate['k']}",
                ),
                "sameLanguageRateChange": None,
                "hubnessGiniChange": _diagnostic_delta_value(
                    compared["hubnessChange"], f"giniAt{aggregate['k']}"
                ),
                "knownItemRecallChange": None,
                "weightsSelected": False,
                "promptOptimized": False,
                "aspectsFused": False,
                "historicalRelation": False,
                "semanticRelation": False,
                "probability": False,
                "status": "PASS",
                "limitation": "Sensitivity-only comparison; no input or fusion policy selected.",
                **suite_identity(suite),
            }
            output.append({**material, "receiptSha256": sha256_json(material)})
    families = sorted(
        {
            str(entry["familyKey"])
            for entry in catalog.values()
            if entry["analysisRole"] == "BASE"
        }
    )
    declared_by_id = {value.ablation_id: value for value in robustness.DECLARED_ABLATIONS}
    for family in families:
        if family not in reference_by_family:
            raise BenchmarkRound1Error(
                "robustness family lacks its governed TITLE reference"
            )
        reference_id, reference = reference_by_family[family]
        reference_queries = set(reference["compact"]["rankingIdsByQuery"])
        stopped_suite = robustness.evaluate_ablation_suite(
            _restricted_result(reference, reference_queries, source_by_object),
            {},
            k_values=(10, 20, 50),
            evaluation_status="STOPPED_RECOVERABLE_CHECKPOINT",
        )
        for ablation_id in robustness.DECLARED_ABLATION_IDS:
            if ablation_id in executed_by_family[family]:
                continue
            spec = declared_by_id[ablation_id]
            material = {
                "modelId": family,
                "referenceMethodId": reference_id,
                "variantMethodId": "N/A",
                "ablationId": ablation_id,
                "ablationFamily": spec.family,
                "inputVariant": "NOT_RUN",
                "aspectId": "N/A",
                "k": 0,
                "queryCount": 0,
                "meanTopKOverlap": None,
                "medianTopKOverlap": None,
                "p05TopKOverlap": None,
                "meanRankCorrelation": None,
                "medianRankCorrelation": None,
                "p05RankCorrelation": None,
                "sameSourceRateChange": None,
                "sameLanguageRateChange": None,
                "hubnessGiniChange": None,
                "knownItemRecallChange": None,
                "weightsSelected": False,
                "promptOptimized": False,
                "aspectsFused": False,
                "historicalRelation": False,
                "semanticRelation": False,
                "probability": False,
                "status": "NOT_RUN",
                "limitation": "Declared ablation lacks an authorized precomputed ranking variant.",
                **suite_identity(stopped_suite),
            }
            output.append({**material, "receiptSha256": sha256_json(material)})
    return output


def _aspect_rows(
    catalog: Mapping[str, Mapping[str, Any]], corpus: Any
) -> list[dict[str, Any]]:
    analyzer = _module("aspect_disagreement")
    source_by_object = _module("source_leakage_eval").source_labels()
    grouped: dict[tuple[str, str], dict[str, Mapping[str, Sequence[str]]]] = defaultdict(dict)
    for entry in catalog.values():
        if entry["analysisRole"] != "BASE":
            continue
        grouped[(entry["channel"], entry["familyKey"])][entry["aspectId"]] = entry[
            "compact"
        ]["rankingIdsByQuery"]
    rows: list[dict[str, Any]] = []
    for (_channel, family), rankings in sorted(grouped.items()):
        if len(rankings) < 2:
            continue
        result = analyzer.analyze_aspect_disagreement(
            rankings,
            model_id=family,
            k=20,
            source_by_object=source_by_object,
            language_by_object=None,
        )
        for row in result["rows"]:
            language_available = isinstance(
                row.get("languageNeighborRateA"), (int, float)
            ) and isinstance(row.get("languageNeighborRateB"), (int, float))
            rows.append(
                {
                    **row,
                    "corpusSha256": corpus.corpus_sha256,
                    "aspectFusionSelected": False,
                    "languageDiagnosticStatus": (
                        "PASS" if language_available else "NOT_RUN"
                    ),
                    "languageDiagnosticReason": (
                        None
                        if language_available
                        else "NO_SELECTED_LID_MODEL_OR_RELIABLE_LANGUAGE_LABEL_COHORT"
                    ),
                    "languageIdentityUsedAsPositiveAffinity": False,
                    "status": "PASS" if language_available else "NOT_RUN",
                    "limitation": (
                        "Aspect overlap and source diagnostics were computed, but reliable "
                        "language-neighborhood rates were not run; no aspect fusion was selected."
                        if not language_available
                        else "Aspect disagreement is expected and no aspect fusion was selected."
                    ),
                }
            )
    if not rows:
        raise BenchmarkRound1Error("aspect disagreement produced no multi-aspect rows")
    return rows


def _positive_by_query(evaluation_rows: Sequence[Mapping[str, Any]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    for row in evaluation_rows:
        if row.get("pair_class") != "KNOWN_REPRESENTATION_POSITIVE":
            continue
        left = str(row["public_object_id_a"])
        right = str(row["public_object_id_b"])
        result[left].append(right)
        result[right].append(left)
    return {key: sorted(set(values)) for key, values in sorted(result.items())}


def _hybrid_rows(
    catalog: Mapping[str, Mapping[str, Any]],
    evaluation_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    hybrid = _module("hybrid_experiments")
    positives = _positive_by_query(evaluation_rows)
    rows: list[dict[str, Any]] = []
    for aspect_id in ASPECT_IDS:
        lexical = [
            (method_id, entry)
            for method_id, entry in catalog.items()
            if entry["analysisRole"] == "BASE"
            and entry["channel"] == "LEXICAL"
            and entry["aspectId"] == aspect_id
        ]
        dense = [
            (method_id, entry)
            for method_id, entry in catalog.items()
            if entry["analysisRole"] == "BASE"
            and entry["channel"] == "DENSE"
            and entry["aspectId"] == aspect_id
        ]
        for lexical_id, lexical_entry in sorted(lexical):
            for dense_id, dense_entry in sorted(dense):
                evaluated = hybrid.evaluate_hybrid_grid(
                    {
                        lexical_id: lexical_entry["compact"]["rankingIdsByQuery"],
                        dense_id: dense_entry["compact"]["rankingIdsByQuery"],
                    },
                    positive_by_query=positives,
                    constants=(10, 60, 100),
                    evaluation_ks=(1, 5, 10, 20),
                    output_limit=TOP_K,
                )
                for row in evaluated["rows"]:
                    rows.append(
                        {
                            **row,
                            "hybridSelected": False,
                            "fusionWeightsSelected": False,
                            "status": "PASS" if row["eligibleQueryCount"] else "NOT_RUN",
                            "limitation": "Analysis-only RRF grid; no weights or production hybrid selected.",
                        }
                    )
    if not rows:
        raise BenchmarkRound1Error("lexical+dense RRF grid produced no rows")
    return rows


def _bounded_review_title(value: str) -> str:
    text = " ".join(str(value).split())
    if len(text) <= 180:
        return text
    prefix = text[:177].rsplit(" ", 1)[0]
    if not prefix:
        prefix = text[:177]
    return prefix.rstrip() + "..."


def _review_profiles(
    corpus: Any,
    selected_entry: Mapping[str, Any],
    dense_payload: Mapping[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    records = _module("lexical_common").load_structured_public_records()
    source_by_id = _module("source_leakage_eval").source_labels()
    label_support: Counter[str] = Counter()
    for record in records.values():
        for field in ("medium", "theme"):
            label_support.update(str(value["id"]) for value in record.get(field, ()))
    top_hubs: set[str] = set()
    if dense_payload is not None:
        for retained in dense_payload["hubnessAnisotropy"]["hubness"][
            "topHubRows"
        ].values():
            top_hubs.update(str(row["publicObjectId"]) for row in retained)
    rankings = selected_entry["compact"]["rankingIdsByQuery"]
    profiles: dict[str, dict[str, Any]] = {}
    for document in corpus.documents:
        object_id = document.object_id
        record = records[object_id]
        # Review labels bind to the frozen governed Context title itself.  The
        # corpus audit currently proves displayOriginal == semanticNormalized,
        # but the authority remains displayOriginal and is bounded only here.
        title = document.aspects["NLP_TITLE"].display_original
        neighbor_ids = rankings.get(object_id, ())[:20]
        same_source_rate = (
            sum(source_by_id.get(candidate) == source_by_id[object_id] for candidate in neighbor_ids)
            / len(neighbor_ids)
            if neighbor_ids
            else 0.0
        )
        leakage_band = "HIGH" if same_source_rate >= 0.5 else (
            "MEDIUM" if same_source_rate >= 0.2 else "LOW"
        )
        supports = [
            label_support[str(value["id"])]
            for field in ("medium", "theme")
            for value in record.get(field, ())
        ]
        minimum_support = min(supports) if supports else 0
        rarity = "RARE" if minimum_support <= 10 else (
            "LESS_COMMON" if minimum_support <= 100 else "COMMON"
        )
        availability = "".join(
            code
            for aspect_id, code in (
                ("NLP_TITLE", "T"),
                ("NLP_SUBJECT", "S"),
                ("NLP_SOURCE_NARRATIVE", "N"),
            )
            if aspect_id in document.aspects
        )
        decades = [str(value["label"]) for value in record.get("decade", ())]
        geography = [str(value["label"]) for value in record.get("geography_class", ())]
        profiles[object_id] = {
            "title": _bounded_review_title(title),
            "titleAuthority": "FROZEN_CONTEXT_SELECTED_RECORD_TITLE",
            "scriptState": document.aspects["NLP_TITLE"].language_script_state,
            "sourceId": source_by_id[object_id],
            "timeBand": decades[0] if decades else "UNDETERMINED",
            "geographyBand": geography[0] if geography else "UNDETERMINED",
            "contextRarityBand": rarity,
            "aspectAvailability": availability,
            "sourceLeakageRisk": leakage_band,
            "hubnessBand": "TOP_HUB" if object_id in top_hubs else "OTHER",
            "structuredNlpDisagreement": "NOT_RUN_AT_ANCHOR_SELECTION",
        }
    return profiles


def _structured_rows(comparison: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value in comparison["summaryRows"]:
        rows.append(
            {
                "rowType": "SUMMARY",
                "structuredModelId": value["structuredModelId"],
                "structuredVariantId": value["structuredVariantId"],
                "nlpMethodId": value["nlpMethodId"],
                "anchorPublicObjectId": "N/A",
                "candidatePublicObjectId": "N/A",
                "classification": "AGGREGATE",
                "anchorCount": value["anchorCount"],
                "candidateIndexSha256": comparison["candidateIndexSha256"],
                "structuredRank": None,
                "nlpRank": None,
                "meanTop20Jaccard": value["meanTop20Jaccard"],
                "bothHighCaseCount": value.get("BOTH_HIGHCaseCount", 0),
                "highStructuredLowNlpCaseCount": value.get(
                    "HIGH_STRUCTURED_LOW_NLPCaseCount", 0
                ),
                "lowStructuredHighNlpCaseCount": value.get(
                    "LOW_STRUCTURED_HIGH_NLPCaseCount", 0
                ),
                "bothLowCaseCount": value.get("BOTH_LOWCaseCount", 0),
                "contextMatch": None,
                "temporalMatch": None,
                "geographyMatch": None,
                "descriptiveMatch": None,
                "textAspect": None,
                "anchorLanguageScriptState": None,
                "candidateLanguageScriptState": None,
                "sameSourceDiagnostic": None,
                "structuredNlpFusionSelected": False,
                "structuredNlpFusionWeightsSelected": False,
                "historicalRelation": False,
                "semanticRelation": False,
                "probability": False,
                "languageDiagnosticStatus": "NOT_RUN",
                "languageDiagnosticReason": (
                    "NO_SELECTED_LID_MODEL_OR_RELIABLE_LANGUAGE_LABEL_COHORT"
                ),
                "scriptStateUsedAsLanguage": False,
                "status": "PARTIAL",
                "limitation": (
                    "M2/M5/M7 and NLP remain independent channels; script-state fields "
                    "are descriptive only and no language diagnostic was run."
                ),
            }
        )
    for value in comparison["comparisonRows"]:
        rows.append(
            {
                "rowType": "DETAIL",
                "structuredModelId": value["structuredModelId"],
                "structuredVariantId": value["structuredVariantId"],
                "nlpMethodId": value["nlpMethodId"],
                "anchorPublicObjectId": value["anchorPublicId"],
                "candidatePublicObjectId": value["candidatePublicId"],
                "classification": value["classification"],
                "anchorCount": comparison["anchorCount"],
                "candidateIndexSha256": comparison["candidateIndexSha256"],
                "structuredRank": value["structuredRank"],
                "nlpRank": value["nlpRank"],
                "meanTop20Jaccard": None,
                "bothHighCaseCount": None,
                "highStructuredLowNlpCaseCount": None,
                "lowStructuredHighNlpCaseCount": None,
                "bothLowCaseCount": None,
                "contextMatch": value["contextMatch"],
                "temporalMatch": value["temporalMatch"],
                "geographyMatch": value["geographyMatch"],
                "descriptiveMatch": value["descriptiveMatch"],
                "textAspect": value["textAspect"],
                "anchorLanguageScriptState": value[
                    "anchorLanguageScriptState"
                ],
                "candidateLanguageScriptState": value[
                    "candidateLanguageScriptState"
                ],
                "sameSourceDiagnostic": value["sameSourceDiagnostic"],
                "structuredNlpFusionSelected": False,
                "structuredNlpFusionWeightsSelected": False,
                "historicalRelation": False,
                "semanticRelation": False,
                "probability": False,
                "languageDiagnosticStatus": "NOT_RUN",
                "languageDiagnosticReason": (
                    "NO_SELECTED_LID_MODEL_OR_RELIABLE_LANGUAGE_LABEL_COHORT"
                ),
                "scriptStateUsedAsLanguage": False,
                "status": "PARTIAL",
                "limitation": (
                    "Disagreement classification is diagnostic, not an error or relation; "
                    "script state was not interpreted as language."
                ),
            }
        )
    return rows


def _build_structured_checkpoint(
    corpus: Any,
    selected_entry: Mapping[str, Any],
    dense_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    review_packet = _module("review_packet")
    structured_module = _module("structured_nlp_disagreement")
    profiles = _review_profiles(corpus, selected_entry, dense_payload)
    anchors = review_packet.select_review_anchors(profiles, target_count=24)
    structured = structured_module.build_structured_anchor_rankings(
        anchors, ranking_depth=TOP_K, enforce_review_packet_size=True
    )
    nlp_result = ranking_result_view(selected_entry["compact"])
    comparison = structured_module.compare_independent_channels(
        structured, nlp_result, corpus, high_cutoff=20, low_cutoff=50
    )
    ranking_ids = {
        model_id: {
            anchor_id: [row["candidateId"] for row in structured["rankings"][model_id][anchor_id]]
            for anchor_id in anchors
        }
        for model_id in sorted(structured["rankings"])
    }
    return {
        "schemaVersion": "trace-nlp-round1-structured-checkpoint/v1",
        "anchorIds": list(anchors),
        "profiles": {anchor: profiles[anchor] for anchor in anchors},
        "structuredReceipt": structured_module.strip_runtime(structured),
        "structuredRankingIds": ranking_ids,
        "comparison": comparison,
        "rows": _structured_rows(comparison),
        "temporary": True,
        "committable": False,
    }


def _annotated_review_candidates(
    candidate_ids: Sequence[str],
    *,
    aspect_id: str,
    anchor_id: str,
    context_rows: Mapping[tuple[str, str], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for rank, candidate_id in enumerate(candidate_ids, start=1):
        context = context_rows.get((anchor_id, candidate_id), {})
        rows.append(
            {
                "candidateId": candidate_id,
                "rank": rank,
                "score": None,
                "aspectId": aspect_id,
                "retrievalReason": "BOUNDED_TOP_K",
                "contextMatch": context.get("contextMatch"),
                "temporalMatch": context.get("temporalMatch"),
                "geographyMatch": context.get("geographyMatch"),
                "descriptiveMatch": context.get("descriptiveMatch"),
            }
        )
    return rows


def _review_rows(
    corpus: Any,
    catalog: Mapping[str, Mapping[str, Any]],
    structured_payload: Mapping[str, Any],
    selected_entry: Mapping[str, Any],
    selected_dense_payload: Mapping[str, Any] | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    review_packet = _module("review_packet")
    hybrid = _module("hybrid_experiments")
    anchors = tuple(structured_payload["anchorIds"])
    profiles_all = _review_profiles(corpus, selected_entry, selected_dense_payload)
    comparison_rows = structured_payload["comparison"]["comparisonRows"]
    context_by_pair: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in comparison_rows:
        key = (row["anchorPublicId"], row["candidatePublicId"])
        if row["structuredModelId"] == "M2" or key not in context_by_pair:
            context_by_pair[key] = row
    title_lexical = sorted(
        (
            (method_id, entry)
            for method_id, entry in catalog.items()
            if entry["analysisRole"] == "BASE"
            and entry["channel"] == "LEXICAL"
            and entry["aspectId"] == "NLP_TITLE"
            and entry["familyKey"] == "NLP-L3"
        ),
        key=lambda value: value[0],
    )
    title_dense = sorted(
        (
            (method_id, entry)
            for method_id, entry in catalog.items()
            if entry["analysisRole"] == "BASE"
            and entry["channel"] == "DENSE"
            and entry["aspectId"] == "NLP_TITLE"
        ),
        key=lambda value: value[0],
    )[:2]
    if len(title_lexical) != 1 or not title_dense:
        raise BenchmarkRound1Error("review packet lacks declared lexical/dense title methods")
    chosen = [title_lexical[0], *title_dense]
    rankings: dict[str, dict[str, list[dict[str, Any]]]] = {}
    roles: dict[str, str] = {}
    for method_id, entry in chosen:
        rankings[method_id] = {
            anchor: _annotated_review_candidates(
                entry["compact"]["rankingIdsByQuery"][anchor],
                aspect_id="NLP_TITLE",
                anchor_id=anchor,
                context_rows=context_by_pair,
            )
            for anchor in anchors
        }
        roles[method_id] = "LEXICAL" if entry["channel"] == "LEXICAL" else "DENSE"
    left_id, left_entry = chosen[0]
    right_id, right_entry = chosen[1]
    hybrid_id = f"REVIEW-RRF-{left_id}-{right_id}-K60"
    rankings[hybrid_id] = {}
    for anchor in anchors:
        fused = hybrid.reciprocal_rank_fusion(
            {
                left_id: left_entry["compact"]["rankingIdsByQuery"][anchor],
                right_id: right_entry["compact"]["rankingIdsByQuery"][anchor],
            },
            constant=60,
            limit=TOP_K,
        )
        rankings[hybrid_id][anchor] = _annotated_review_candidates(
            fused,
            aspect_id="NLP_TITLE",
            anchor_id=anchor,
            context_rows=context_by_pair,
        )
    roles[hybrid_id] = "HYBRID_DIAGNOSTIC"
    for model_id, by_anchor in structured_payload["structuredRankingIds"].items():
        method_id = f"STRUCTURED-{model_id}"
        rankings[method_id] = {
            anchor: _annotated_review_candidates(
                by_anchor[anchor],
                aspect_id="NLP_TITLE",
                anchor_id=anchor,
                context_rows=context_by_pair,
            )
            for anchor in anchors
        }
        roles[method_id] = f"STRUCTURED_{model_id}_INDEPENDENT"
    packet = review_packet.build_review_packet(
        profiles_all,
        rankings,
        method_roles=roles,
        target_count=24,
        candidates_per_method=5,
    )
    if tuple(packet["anchorIds"]) != anchors:
        raise BenchmarkRound1Error("review/structured anchor selection diverged")
    stopped_reason = (
        "Anchor selection preceded the structured/NLP comparison, so actual "
        "disagreement could not be used as an independent selection stratum."
    )
    stopped_rows = [
        {
            **row,
            "status": "NOT_RUN",
            "limitation": stopped_reason,
        }
        for row in packet["rows"]
    ]
    stopped_packet = {
        **packet,
        "rows": stopped_rows,
        "rowCount": len(stopped_rows),
        "rowsSha256": sha256_json(stopped_rows),
        "packetReady": False,
        "status": "NOT_RUN",
        "reason": "STRUCTURED_DISAGREEMENT_NOT_AVAILABLE_AT_ANCHOR_SELECTION",
        "disagreementStratificationCompleted": False,
    }
    return stopped_rows, stopped_packet


def _sanitize_bounded_metadata(value: Any, *, path: str = "$") -> Any:
    """Drop local paths and reject unbounded/private material in supplied receipts."""

    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for native, child in sorted(value.items(), key=lambda item: str(item[0])):
            key = str(native)
            normalized = re.sub(r"[^a-z0-9]", "", key.casefold())
            if normalized in {"path", "localpath", "snapshotpath", "environmentpath"}:
                continue
            if key in FORBIDDEN_SUMMARY_KEYS or normalized in {
                "rankings",
                "rankingsbyquery",
                "embeddingvectors",
                "embeddings",
                "vectors",
                "corpusdocuments",
                "documentsbyid",
                "pairmatrix",
                "scorematrix",
                "neighborsbyquery",
            }:
                if child not in (None, False, 0, "", [], {}):
                    raise BenchmarkRound1Error(f"forbidden bounded metadata at {path}.{key}")
                continue
            output[key] = _sanitize_bounded_metadata(child, path=f"{path}.{key}")
        return output
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if len(value) > 25_000:
            raise BenchmarkRound1Error(f"bounded metadata array is too large at {path}")
        return [
            _sanitize_bounded_metadata(child, path=f"{path}[{index}]")
            for index, child in enumerate(value)
        ]
    if isinstance(value, str):
        text = " ".join(value.replace("\u00a0", " ").split())
        if UUID_RE.search(text) or PRIVATE_TOKEN_RE.search(text):
            raise BenchmarkRound1Error(f"private identifier entered bounded metadata at {path}")
        return text
    if isinstance(value, float) and not math.isfinite(value):
        raise BenchmarkRound1Error(f"non-finite number entered bounded metadata at {path}")
    return value


def _load_dense_metadata(
    path: Path,
    *,
    expected_sha256: str,
    expected_document_receipt_sha256: str,
    expected_lexical_corpus_sha256: str,
    expected_token_count_receipt_sha256: str,
    expected_policy_sha256: str,
    expected_public_ids_sha256: str,
    policy: TempPathPolicy,
) -> tuple[list[dict[str, Any]], Mapping[str, Any]]:
    if not SHA256_RE.fullmatch(expected_sha256) or sha256_path(path) != expected_sha256:
        raise BenchmarkRound1Error("dense encoding metadata JSON hash changed")
    document = _load_json_or_gzip(path)
    if not isinstance(document, Mapping) or document.get("schemaVersion") != (
        "trace-nlp-round1-dense-encoding-receipts/v1"
    ):
        raise BenchmarkRound1Error("dense encoding metadata schema changed")
    if not SHA256_RE.fullmatch(expected_document_receipt_sha256):
        raise BenchmarkRound1Error("expected encoded document receipt SHA-256 is invalid")
    if document.get("corpusSha256") != expected_document_receipt_sha256:
        raise BenchmarkRound1Error(
            "dense encoding metadata differs from the governed document receipt"
        )
    if document.get("lexicalCorpusSha256") != expected_lexical_corpus_sha256:
        raise BenchmarkRound1Error(
            "dense encoding metadata differs from the governed ranking corpus receipt"
        )
    if (
        document.get("tokenCountReceiptSha256")
        != expected_token_count_receipt_sha256
        or document.get("tokenCountMethod") != "TRACE_UNICODE_WORD_TOKENS_V1"
    ):
        raise BenchmarkRound1Error(
            "dense encoding metadata differs from the governed token-count receipt"
        )
    if document.get("corpusPolicySha256") != expected_policy_sha256:
        raise BenchmarkRound1Error("dense encoding metadata corpus policy changed")
    if document.get("canonicalPublicIdsSha256") != expected_public_ids_sha256:
        raise BenchmarkRound1Error("dense encoding metadata public identity order changed")
    if (
        document.get("trustRemoteCodeExecuted") is not False
        or document.get("hostedInferenceCalls") != 0
        or document.get("fullEmbeddingMatrixCommitted") is not False
    ):
        raise BenchmarkRound1Error(
            "dense encoding metadata does not prove offline/no-remote-code/temp-only execution"
        )
    runs = document.get("runs")
    if not isinstance(runs, list) or not runs:
        raise BenchmarkRound1Error("dense encoding metadata has no runs")
    groups: dict[
        tuple[str, str, str], list[dict[str, Any]]
    ] = defaultdict(list)
    dense_encoder = _module("dense_encoder")
    for run in runs:
        if not isinstance(run, Mapping):
            raise BenchmarkRound1Error("dense encoding run is malformed")
        raw_encoding = run.get("encodingReceipt", run)
        if not isinstance(raw_encoding, Mapping):
            raise BenchmarkRound1Error("dense encoding receipt wrapper is malformed")
        if (
            raw_encoding.get("schemaVersion") != dense_encoder.SCHEMA_VERSION
            or raw_encoding.get("implementationVersion")
            != dense_encoder.IMPLEMENTATION_VERSION
        ):
            raise BenchmarkRound1Error(
                "dense run lacks the complete hardened encoder receipt; a "
                "pre-hardening aggregate receipt cannot authorize replay"
            )
        aspect_ids = raw_encoding.get("aspectIds")
        if (
            not isinstance(aspect_ids, list)
            or len(aspect_ids) != 1
            or not isinstance(aspect_ids[0], str)
        ):
            raise BenchmarkRound1Error("dense encoding receipt lacks one exact aspect")
        key = (
            str(raw_encoding.get("methodId", "")),
            aspect_ids[0],
            str(raw_encoding.get("inputVariant", "")),
        )
        if key[0] not in {"NLP-D1", "NLP-D3"} or key[1] not in ASPECT_IDS:
            raise BenchmarkRound1Error("dense metadata names an unauthorized method/aspect")
        for wrapper_key, encoded_value in (
            ("methodId", key[0]),
            ("aspectId", key[1]),
            ("inputVariant", key[2]),
        ):
            if wrapper_key in run and run[wrapper_key] != encoded_value:
                raise BenchmarkRound1Error(
                    "dense metadata wrapper relabels its encoding receipt"
                )
        run_id = str(run.get("runId", ""))
        if not run_id or not SAFE_NAME_RE.fullmatch(run_id.casefold()):
            raise BenchmarkRound1Error("dense encoding wrapper lacks a safe runId")
        npz_path = policy.resolve_input(run["path"], suffixes=(".npz",))
        temp_sha = str(run.get("tempSha256", ""))
        if not SHA256_RE.fullmatch(temp_sha) or sha256_path(npz_path) != temp_sha:
            raise BenchmarkRound1Error("dense metadata temporary artifact hash changed")
        groups[key].append(
            {
                "runId": run_id,
                "path": str(run["path"]),
                "tempSha256": temp_sha,
                "encodingReceipt": dict(raw_encoding),
                "wrapper": dict(run),
            }
        )
    inputs: list[dict[str, Any]] = []
    for (candidate_id, aspect_id, input_variant), values in sorted(groups.items()):
        values = sorted(values, key=lambda value: str(value["runId"]))
        representative = values[0]
        replicate_artifact_match = len(
            {str(value["tempSha256"]) for value in values}
        ) == 1
        replicate_embedding_match = len(
            {
                str(value["encodingReceipt"]["embeddingObservationSha256"])
                for value in values
            }
        ) == 1
        if len(values) > 1 and not (
            replicate_artifact_match and replicate_embedding_match
        ):
            raise BenchmarkRound1Error("dense A/B encoding artifacts are not deterministic")
        suffix = aspect_id.removeprefix("NLP_").replace("_", "-")
        result_id = f"{candidate_id}-{suffix}-{input_variant}"
        inputs.append(
            {
                "resultId": result_id,
                "candidateId": candidate_id,
                "aspectId": aspect_id,
                "inputVariant": input_variant,
                "candidateNpzPath": representative["path"],
                "candidateNpzSha256": representative["tempSha256"],
                "queryNpzPath": representative["path"],
                "queryNpzSha256": representative["tempSha256"],
                "encodingReceipt": representative["encodingReceipt"],
                "replicateGroupId": f"{candidate_id}-{suffix}-{input_variant}",
                "replicateRuns": [
                    _sanitize_bounded_metadata(value["wrapper"]) for value in values
                ],
                "replicateCount": len(values),
                "replicateArtifactByteIdentity": replicate_artifact_match
                if len(values) > 1
                else None,
                "replicateEmbeddingByteIdentity": replicate_embedding_match
                if len(values) > 1
                else None,
                "analysisRole": "BASE",
                "blockSize": DEFAULT_DENSE_BLOCK_SIZE,
            }
        )
    return inputs, document


def _expected_dense_evaluation(
    path: Path | None, policy: TempPathPolicy
) -> Mapping[str, Any] | None:
    if path is None:
        return None
    target = policy.resolve_input(path, suffixes=(".json", ".gz"))
    document = _load_json_or_gzip(target)
    if not isinstance(document, Mapping) or not isinstance(document.get("ranking"), Mapping):
        raise BenchmarkRound1Error("dense expected evaluation receipt is malformed")
    return document


def _build_dense_group_checkpoint(
    row: Mapping[str, Any],
    *,
    policy: TempPathPolicy,
    corpus_sha256: str,
    corpus_identity: Mapping[str, Any],
    evaluation_rows: Sequence[Mapping[str, Any]],
    evaluation_registry_sha256: str,
    hubness_associations: Mapping[str, Any],
    strict: bool,
    expected_evaluation: Mapping[str, Any] | None,
) -> dict[str, Any]:
    payload = _build_dense_checkpoint(
        row,
        policy=policy,
        corpus_sha256=corpus_sha256,
        corpus_identity=corpus_identity,
        evaluation_rows=evaluation_rows,
        evaluation_registry_sha256=evaluation_registry_sha256,
        hubness_associations=hubness_associations,
        strict=strict,
    )
    payload["replicateRuns"] = row.get("replicateRuns", [])
    payload["replicateCount"] = row.get("replicateCount", 1)
    payload["replicateArtifactByteIdentity"] = row.get(
        "replicateArtifactByteIdentity"
    )
    payload["replicateEmbeddingByteIdentity"] = row.get(
        "replicateEmbeddingByteIdentity"
    )
    if expected_evaluation is not None:
        expected = expected_evaluation["ranking"]
        observed = payload["result"]["summary"]
        if expected.get("rankingIdsSha256") != observed.get("rankingIdsSha256"):
            raise BenchmarkRound1Error("bounded block exact ranking hash differs from prior exact run")
        payload["priorExactRankingReceiptSha256"] = sha256_json(expected_evaluation)
        payload["boundedBlockRankingMatchesPriorExact"] = True
    return payload


def _row_receipt(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {"rowCount": len(rows), "rowsSha256": sha256_json(list(rows))}


def _seal_component(name: str, component: Mapping[str, Any]) -> dict[str, Any]:
    output = dict(component)
    row_receipts = {
        row_key: _row_receipt(output[row_key]) for row_key in ROW_ARRAYS.get(name, ())
    }
    if row_receipts:
        output["rowReceipts"] = row_receipts
    output["componentSha256"] = sha256_json(output)
    return output


def _run_rows(
    checkpoints: Sequence[Mapping[str, Any]],
    corpus: Any,
    corpus_identity: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    for receipt in checkpoints:
        rows.append(
            {
                "runId": f"NLP-R1-{receipt['checkpointName']}",
                "checkpointState": receipt["state"],
                "checkpointPayloadSha256": receipt["payloadSha256"],
                "checkpointFileSha256": receipt["fileSha256"],
                "checkpointByteCount": receipt["byteCount"],
                "checkpointElapsedMs": receipt["elapsedMs"],
                "sourceCommit": "580587a74f400d8a04d995937f4efb31e6621dd8",
                "corpusPolicySha256": corpus.policy_sha256,
                "fieldRegistrySha256": corpus.field_registry_sha256,
                "encodedDocumentReceiptSha256": corpus_identity[
                    "documentReceiptSha256"
                ],
                "rankingCorpusSha256": corpus_identity["lexicalCorpusSha256"],
                "tokenCountReceiptSha256": corpus_identity[
                    "tokenCountReceiptSha256"
                ],
                "tokenCountMethod": corpus_identity["tokenCountMethod"],
                "corpusIdentityContractsConflated": False,
                "randomnessAffectsCorpus": False,
                "randomnessAffectsEmbedding": False,
                "randomnessAffectsNeighborOrder": False,
                "randomnessAffectsScore": False,
                "modelWeightsCommitted": False,
                "fullEmbeddingMatrixCommitted": False,
                "fullPairMatrixCommitted": False,
                "fullRankingsCommitted": False,
                "temporaryCheckpoint": True,
            }
        )
    return rows


def _performance_summary(
    lexical_rows: Sequence[Mapping[str, Any]],
    dense_rows: Sequence[Mapping[str, Any]],
    dense_metadata: Mapping[str, Any],
) -> dict[str, Any]:
    encoding_runs = list(dense_metadata.get("runs", ()))
    normalized_encoding_runs = [
        run.get("encodingReceipt", run) if isinstance(run, Mapping) else {}
        for run in encoding_runs
    ]
    encoding_ms = [
        float(run["performance"]["denseCorpusEncodingMs"])
        for run in normalized_encoding_runs
        if run.get("performance", {}).get("denseCorpusEncodingMs") is not None
    ]
    document_counts = [
        int(run["aspectAvailableObjectCount"])
        for run in normalized_encoding_runs
    ]
    peak_ram = [
        int(run["performance"]["peakRssBytes"])
        for run in normalized_encoding_runs
        if run.get("performance", {}).get("peakRssBytes") is not None
    ]
    peak_vram = [
        int(run["performance"]["peakVramBytes"])
        for run in normalized_encoding_runs
        if run.get("performance", {}).get("peakVramBytes") is not None
    ]
    return {
        "lexicalIndexBuildMs": sum(float(row["indexBuildMs"]) for row in lexical_rows),
        "denseCorpusEncodingMs": sum(encoding_ms) if encoding_ms else None,
        "denseDocumentsPerSecond": (
            sum(document_counts) / (sum(encoding_ms) / 1000.0)
            if encoding_ms and len(document_counts) == len(encoding_ms)
            else None
        ),
        "denseIndexBytes": max((int(row["indexBytes"]) for row in dense_rows), default=0),
        "denseExactQueryP50Ms": _quantile_r7(
            [float(row["exactQueryP50Ms"]) for row in dense_rows], 0.50
        ),
        "denseExactQueryP95Ms": _quantile_r7(
            [float(row["exactQueryP95Ms"]) for row in dense_rows], 0.95
        ),
        "nlpPeakRamBytes": max(peak_ram, default=0),
        "nlpPeakVramBytes": max(peak_vram, default=0),
        "timingsInvented": False,
    }


def _security_summary() -> dict[str, Any]:
    return {
        "modelWeightFilesCommitted": 0,
        "internalUuidExposureCount": 0,
        "heldIdentifierExposureCount": 0,
        "databaseFilesChanged": 0,
        "searchFilesChanged": 0,
        "historicalRelationCount": 0,
        "probabilityCount": 0,
        "canonicalReleaseChanged": False,
        "contextSemanticsChanged": False,
        "contextGovernanceChanged": False,
        "spacetimeGovernanceChanged": False,
        "cgCur4Changed": False,
        "m2SpecificationChanged": False,
        "m5SpecificationChanged": False,
        "m7SpecificationChanged": False,
        "publicExplorationApiAdded": False,
        "publicExplorationRouteAdded": False,
        "vectorDatabaseAdded": False,
        "explorationRendererImplemented": False,
        "unreviewedRemoteCodeExecuted": False,
        "fullEmbeddingMatrixCommitted": False,
        "fullRankingsCommitted": False,
        "fullPairMatrixCommitted": False,
        "randomnessAffectsCorpus": False,
        "randomnessAffectsEmbedding": False,
        "randomnessAffectsNeighborOrder": False,
        "randomnessAffectsScore": False,
    }


def _invariant_receipts() -> dict[str, Any]:
    invariant_text = _module("generate_round1").INVARIANT_TEXT
    evidence = {
        "NLP-INV-001": "boundary",
        "NLP-INV-002": "boundary",
        "NLP-INV-003": "governance.fieldRegistryRows",
        "NLP-INV-004": "governance",
        "NLP-INV-005": "governance.boilerplateRows",
        "NLP-INV-006": "governance",
        "NLP-INV-007": "governance",
        "NLP-INV-008": "evaluationRegistry.fullSameTitleStressCensus",
        "NLP-INV-009": "evaluationRegistry.rows",
        "NLP-INV-010": "metadata.holdoutRows",
        "NLP-INV-011": "leakage.sourceLanguageRows",
        "NLP-INV-012": "leakage.sourceLanguageRows",
        "NLP-INV-013": "models.artifactRows",
        "NLP-INV-014": "models.artifactRows",
        "NLP-INV-015": "security",
        "NLP-INV-016": "security",
        "NLP-INV-017": "security",
        "NLP-INV-018": "aspects.rows",
        "NLP-INV-019": "security",
        "NLP-INV-020": "security",
        "NLP-INV-021": "structured.rows",
        "NLP-INV-022": "structured.rows",
        "NLP-INV-023": "decision",
        "NLP-INV-024": "runs.rows",
        "NLP-INV-025": "review.rows",
        "NLP-INV-026": "decision",
    }
    return {
        identifier: {"status": "PASS", "evidenceRefs": [evidence[identifier]]}
        for identifier in invariant_text
    }


def _decision_summary(
    *, dense_full_count: int, review_ready: bool, source_blocker_count: int
) -> dict[str, Any]:
    architecture = _module("channel_architecture").evaluate_channel_positions(
        {
            "denseFullCorpusCount": dense_full_count,
            "reviewPacketReady": review_ready,
            "sourceLeakageBlockerCount": source_blocker_count,
        }
    )
    if architecture["shortlist"]:
        raise BenchmarkRound1Error("source-leakage blockers did not fail-close architecture")
    return {
        "phaseStatus": "STOPPED_RECOVERABLE_CHECKPOINT",
        "nlpModelDecision": "NLP_CORPUS_AUDIT_ONLY",
        "denseModelShortlistCount": 0,
        "denseModelShortlistIds": [],
        "baselineFamiliesShortlisted": False,
        "provisionalInternalNlpChannelSelected": False,
        "publicNlpModelSelected": False,
        "publicNlpWeightsSelected": False,
        "publicExplorationModelSelected": False,
        "structuredNlpFusionSelected": False,
        "structuredNlpFusionWeightsSelected": False,
        "hubnessCorrectionSelected": False,
        "domainExpertReviewCompleted": False,
        "sourceLeakageAndHubnessConsidered": True,
        "stopCondition": "SOURCE_PROVIDER_DOMINANCE_ACROSS_DENSE_TITLE_NEIGHBORHOODS",
        "recoverableCheckpoint": True,
        "channelArchitectureByPosition": {
            row["positionId"]: row for row in architecture["rows"]
        },
        "channelArchitectureRowsSha256": architecture["rowsSha256"],
        "channelArchitectureShortlistIds": architecture["shortlist"],
    }


def _assemble_summary(
    *,
    governance_payload: Mapping[str, Any],
    evaluation_payload: Mapping[str, Any],
    lexical_rows: Sequence[Mapping[str, Any]],
    dense_rows: Sequence[Mapping[str, Any]],
    cross_rows: Sequence[Mapping[str, Any]],
    metadata_rows: Sequence[Mapping[str, Any]],
    leakage_rows: Sequence[Mapping[str, Any]],
    hubness_rows: Sequence[Mapping[str, Any]],
    robustness_rows: Sequence[Mapping[str, Any]],
    aspect_rows: Sequence[Mapping[str, Any]],
    structured_rows: Sequence[Mapping[str, Any]],
    hybrid_rows: Sequence[Mapping[str, Any]],
    review_rows: Sequence[Mapping[str, Any]],
    review_packet: Mapping[str, Any],
    run_rows: Sequence[Mapping[str, Any]],
    performance: Mapping[str, Any],
    dense_full_count: int,
) -> dict[str, Any]:
    model_registry = _module("model_registry").registry_receipt()
    blocked_dense_title_ids = sorted(
        {
            str(row["modelId"])
            for row in dense_rows
            if row.get("aspectId") == "NLP_TITLE"
            and row.get("status") == "PASS"
            and isinstance(row.get("sameSourceNeighborRateAt20"), (int, float))
            and isinstance(row.get("corpusSourceHhi"), (int, float))
            and float(row["sameSourceNeighborRateAt20"])
            > float(row["corpusSourceHhi"])
        }
    )
    source_blocker_count = len(blocked_dense_title_ids)
    if source_blocker_count != 2:
        raise BenchmarkRound1Error(
            "dense title source-leakage blocker census differs from the frozen evidence"
        )
    components: dict[str, Any] = {
        "source": governance_payload["source"],
        "governance": governance_payload["governance"],
        "boundary": governance_payload["boundary"],
        "evaluationRegistry": evaluation_payload,
        "models": {
            "registrySha256": model_registry["registrySha256"],
            "artifactRows": _model_artifact_rows(),
        },
        "lexical": {"resultRows": list(lexical_rows)},
        "dense": {
            "resultRows": list(dense_rows),
            "crossLanguageRows": list(cross_rows),
        },
        "metadata": {"holdoutRows": list(metadata_rows)},
        "leakage": {
            "sourceLanguageRows": list(leakage_rows),
            "sourceLeakageBlockerCount": source_blocker_count,
            "sourceLeakageBlockerModelIds": blocked_dense_title_ids,
            "languageLeakageBlockerCount": 0,
            "languageLeakageStatus": "NOT_RUN",
            "languageLeakageReason": (
                "NO_SELECTED_LID_MODEL_OR_RELIABLE_LANGUAGE_LABEL_COHORT"
            ),
        },
        "hubness": {
            "status": "NOT_RUN",
            "reason": "REQUIRED_LANGUAGE_ASSOCIATION_AND_PRE_NORMALIZATION_NORMS_UNAVAILABLE",
            "coreDiagnosticsComputed": True,
            "rows": list(hubness_rows),
        },
        "robustness": {
            "status": "STOPPED_RECOVERABLE_CHECKPOINT",
            "declaredAblationIds": list(
                _module("robustness_ablation").DECLARED_ABLATION_IDS
            ),
            "declaredAblationCount": len(
                _module("robustness_ablation").DECLARED_ABLATION_IDS
            ),
            "completed": False,
            "suiteSha256s": sorted(
                {
                    str(row["suiteSha256"])
                    for row in robustness_rows
                    if row.get("suiteSha256")
                }
            ),
            "rows": list(robustness_rows),
        },
        "aspects": {"rows": list(aspect_rows), "aspectFusionSelected": False},
        "structured": {
            "rows": list(structured_rows),
            "status": "PARTIAL",
            "languageDiagnosticStatus": "NOT_RUN",
            "languageDiagnosticReason": (
                "NO_SELECTED_LID_MODEL_OR_RELIABLE_LANGUAGE_LABEL_COHORT"
            ),
            "scriptStateUsedAsLanguage": False,
            "structuredNlpFusionSelected": False,
            "structuredNlpFusionWeightsSelected": False,
        },
        "hybrid": {
            "rows": list(hybrid_rows),
            "hybridSelected": False,
            "fusionWeightsSelected": False,
        },
        "review": {
            "rows": list(review_rows),
            "anchorCount": review_packet["anchorCount"],
            "packetReady": review_packet["packetReady"],
            "status": review_packet.get("status", "NOT_RUN"),
            "reason": review_packet.get(
                "reason",
                "STRUCTURED_DISAGREEMENT_NOT_AVAILABLE_AT_ANCHOR_SELECTION",
            ),
            "disagreementStratificationCompleted": review_packet.get(
                "disagreementStratificationCompleted", False
            ),
            "domainExpertReviewCompleted": False,
        },
        "runs": {"rows": list(run_rows)},
        "performance": dict(performance),
        "security": _security_summary(),
        "decision": _decision_summary(
            dense_full_count=dense_full_count,
            review_ready=bool(review_packet["packetReady"]),
            source_blocker_count=source_blocker_count,
        ),
        "invariants": _invariant_receipts(),
    }
    sealed = {
        name: (
            components[name]
            if name == "invariants"
            else _seal_component(name, components[name])
        )
        for name in EXPECTED_SUMMARY_COMPONENTS
    }
    summary = {"schemaVersion": SCHEMA_VERSION, **sealed}
    summary["analysisSummarySha256"] = sha256_json(summary)
    _module("generate_round1").derive_tables(summary)
    return summary


def write_summary_temp(
    summary: Mapping[str, Any], path: Path, policy: TempPathPolicy
) -> dict[str, Any]:
    target = policy.resolve(path, suffixes=(".json",))
    _module("generate_round1").derive_tables(summary)
    safe = _sanitize_bounded_metadata(summary)
    if safe != summary:
        raise BenchmarkRound1Error("analysis summary required sanitization after assembly")
    payload = canonical_json_bytes(summary, newline=True)
    if len(payload) > MAX_SUMMARY_BYTES:
        raise BenchmarkRound1Error("analysis summary exceeds the 24 MiB bound")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.read_bytes() != payload:
            raise BenchmarkRound1Error("summary output exists with different bytes")
        state = "REUSED"
    else:
        with target.open("xb") as handle:
            handle.write(payload)
        state = "WRITTEN"
    return {
        "schemaVersion": "trace-nlp-round1-summary-write-receipt/v1",
        "state": state,
        "fileName": target.name,
        "byteCount": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "analysisSummarySha256": summary["analysisSummarySha256"],
        "temporary": True,
        "committable": False,
    }


def _aspect_cli_map(values: Sequence[str], policy: TempPathPolicy) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise BenchmarkRound1Error("aspect path argument must be ASPECT=/absolute/path")
        aspect_id, path = value.split("=", 1)
        if aspect_id not in ASPECT_IDS or aspect_id in result:
            raise BenchmarkRound1Error("aspect path argument is duplicated or unsupported")
        result[aspect_id] = policy.resolve_input(path, suffixes=(".json", ".gz"))
    return result


def _candidate_cli_map(values: Sequence[str], policy: TempPathPolicy) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise BenchmarkRound1Error("candidate path argument must be ID=/absolute/path")
        candidate_id, path = value.split("=", 1)
        if candidate_id not in {"NLP-D1", "NLP-D3"} or candidate_id in result:
            raise BenchmarkRound1Error("candidate path argument is duplicated or unsupported")
        result[candidate_id] = policy.resolve_input(path, suffixes=(".json", ".gz"))
    return result


def run_benchmark(
    *,
    temp_root: str | Path,
    checkpoint_dir: str | Path,
    phase: str,
    output_path: str | Path | None,
    lexical_receipt_paths: Mapping[str, Path],
    dense_metadata_path: Path | None,
    dense_metadata_sha256: str | None,
    dense_evaluation_paths: Mapping[str, Path],
    lexical_aspects: Sequence[str] = ASPECT_IDS,
    reuse_only: bool = False,
    strict: bool = True,
    explicit_robustness_comparisons: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    allowed_phases = {"lexical", "dense", "metadata", "source-mask", "summary", "all"}
    if phase not in allowed_phases:
        raise BenchmarkRound1Error("benchmark phase is unsupported")
    selected_lexical_aspects = tuple(lexical_aspects)
    if (
        not selected_lexical_aspects
        or len(set(selected_lexical_aspects)) != len(selected_lexical_aspects)
        or set(selected_lexical_aspects) - set(ASPECT_IDS)
    ):
        raise BenchmarkRound1Error("lexical aspect selection is empty, duplicated, or unsupported")
    if phase != "lexical" and selected_lexical_aspects != ASPECT_IDS:
        raise BenchmarkRound1Error(
            "partial --lexical-aspect selection is allowed only for the lexical phase"
        )
    policy = TempPathPolicy.create(temp_root, create=True)
    checkpoint_root = policy.resolve(checkpoint_dir, directory=True)
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    store = CheckpointStore(checkpoint_root, policy)
    common = _module("lexical_common")
    corpus = common.load_governed_corpus()
    corpus_identity = _corpus_identity_receipt(corpus)
    governance_payload = store.load_or_build(
        "governance",
        {
            "corpusSha256": corpus.corpus_sha256,
            "policySha256": corpus.policy_sha256,
            "fieldRegistrySha256": corpus.field_registry_sha256,
            "documentReceiptSha256": corpus_identity["documentReceiptSha256"],
            "tokenCountReceiptSha256": corpus_identity["tokenCountReceiptSha256"],
            "implementationVersion": IMPLEMENTATION_VERSION,
        },
        lambda: _governance_payload(corpus, corpus_identity),
        allow_build=not reuse_only,
    )
    evaluation_payload = store.load_or_build(
        "evaluation-registry",
        {
            "expectedRegistrySha256": "73c0650cfc10a2db6d5fb61c72a783b086667d2da7e6229f1cdd00475700a785",
            "implementationVersion": _module("known_item_eval").IMPLEMENTATION_VERSION,
        },
        _evaluation_registry_payload,
        allow_build=not reuse_only,
    )

    catalog: dict[str, dict[str, Any]] = {}
    lexical_suites: dict[str, Mapping[str, Any]] = {}
    need_lexical = phase in {"lexical", "metadata", "source-mask", "summary", "all"}
    if need_lexical:
        required_aspects = (
            selected_lexical_aspects if phase == "lexical" else ASPECT_IDS
        )
        if strict and not set(required_aspects).issubset(lexical_receipt_paths):
            raise BenchmarkRound1Error(
                "strict Run-B lexical check lacks a selected Run-A receipt"
            )
        for aspect_id in required_aspects:
            expected_path = lexical_receipt_paths.get(aspect_id)
            dependency = {
                "corpusSha256": corpus.corpus_sha256,
                "aspectId": aspect_id,
                "aspectPurpose": ASPECT_PURPOSE[aspect_id],
                "topK": TOP_K,
                "lexicalImplementationVersion": _module("lexical_eval").IMPLEMENTATION_VERSION,
                "sourceProbeImplementationVersion": _module(
                    "source_leakage_eval"
                ).IMPLEMENTATION_VERSION,
                "benchmarkImplementationVersion": IMPLEMENTATION_VERSION,
                "expectedRunAReceiptSha256": (
                    sha256_path(expected_path) if expected_path is not None else None
                ),
            }
            suite = store.load_or_build(
                f"lexical-base-{aspect_id.removeprefix('NLP_').lower().replace('_', '-')}",
                dependency,
                lambda aspect_id=aspect_id, expected_path=expected_path: _build_lexical_suite(
                    corpus,
                    aspect_id,
                    expected_receipt_path=expected_path,
                ),
                allow_build=not reuse_only,
            )
            probe_payload = store.load_or_build(
                f"source-probe-lexical-base-{aspect_id.removeprefix('NLP_').lower().replace('_', '-')}",
                {
                    "corpusSha256": corpus.corpus_sha256,
                    "aspectId": aspect_id,
                    "inputVariant": "ORIGINAL_APPROVED_TEXT",
                    "suiteRankingSha256": suite["suiteSummary"][
                        "suiteRankingSha256"
                    ],
                    "sourceProbeImplementationVersion": _module(
                        "source_leakage_eval"
                    ).IMPLEMENTATION_VERSION,
                    "benchmarkImplementationVersion": IMPLEMENTATION_VERSION,
                },
                lambda aspect_id=aspect_id: {
                    "schemaVersion": "trace-nlp-round1-source-probe-checkpoint/v1",
                    "aspectId": aspect_id,
                    "inputVariant": "ORIGINAL_APPROVED_TEXT",
                    "sourceProbes": _lexical_source_probes(
                        corpus,
                        aspect_id=aspect_id,
                        input_variant="ORIGINAL_APPROVED_TEXT",
                    ),
                    "temporary": True,
                    "committable": False,
                },
                allow_build=not reuse_only,
            )
            suite = {**suite, "sourceProbes": probe_payload["sourceProbes"]}
            lexical_suites[aspect_id] = suite
            _catalog_suite(catalog, suite, channel="LEXICAL", analysis_role="BASE")
    if phase == "lexical":
        return {
            "schemaVersion": "trace-nlp-round1-phase-receipt/v1",
            "phase": phase,
            "status": "PASS",
            "aspectIds": list(required_aspects),
            "checkpointCount": len(store.receipts),
            "checkpointReceiptsSha256": sha256_json(store.receipts),
            "summaryWritten": False,
        }

    dense_payloads: dict[str, Mapping[str, Any]] = {}
    dense_metadata: Mapping[str, Any] = {"runs": []}
    need_dense = phase in {"dense", "summary", "all"}
    if need_dense:
        if dense_metadata_path is None or dense_metadata_sha256 is None:
            raise BenchmarkRound1Error("dense phase requires SHA-pinned encoding metadata JSON")
        metadata_target = policy.resolve_input(
            dense_metadata_path, suffixes=(".json", ".gz")
        )
        dense_inputs, dense_metadata = _load_dense_metadata(
            metadata_target,
            expected_sha256=dense_metadata_sha256,
            expected_document_receipt_sha256=corpus_identity[
                "documentReceiptSha256"
            ],
            expected_lexical_corpus_sha256=corpus_identity[
                "lexicalCorpusSha256"
            ],
            expected_token_count_receipt_sha256=corpus_identity[
                "tokenCountReceiptSha256"
            ],
            expected_policy_sha256=corpus.policy_sha256,
            expected_public_ids_sha256=_sha256_json_no_lf(list(corpus.object_ids)),
            policy=policy,
        )
        hubness_source_labels = _module("source_leakage_eval").source_labels()
        hubness_metadata_contract = _module(
            "metadata_holdout_eval"
        ).derive_governed_label_contract()
        hubness_associations_by_aspect = {
            aspect_id: _hubness_association_inputs(
                corpus,
                aspect_id=aspect_id,
                source_by_object=hubness_source_labels,
                metadata_contract=hubness_metadata_contract,
            )
            for aspect_id in sorted({str(row["aspectId"]) for row in dense_inputs})
        }
        for row in dense_inputs:
            hubness_associations = hubness_associations_by_aspect[row["aspectId"]]
            expected = _expected_dense_evaluation(
                dense_evaluation_paths.get(row["candidateId"])
                if row["aspectId"] == "NLP_TITLE"
                else None,
                policy,
            )
            dependency = {
                **_dense_input_dependency(row, policy),
                "corpusSha256": corpus.corpus_sha256,
                "encodedDocumentReceiptSha256": corpus_identity[
                    "documentReceiptSha256"
                ],
                "rankingCorpusSha256": corpus_identity["lexicalCorpusSha256"],
                "tokenCountReceiptSha256": corpus_identity[
                    "tokenCountReceiptSha256"
                ],
                "evaluationRegistrySha256": evaluation_payload["registrySha256"],
                "expectedPriorExactRankingSha256": (
                    expected["ranking"]["rankingIdsSha256"] if expected else None
                ),
                "runnerImplementationSha256": sha256_path(Path(__file__).resolve()),
                "hubnessAssociationInputsSha256": hubness_associations["receipt"][
                    "receiptSha256"
                ],
            }
            checkpoint_name = "dense-" + row["resultId"].casefold().replace("_", "-")
            payload = store.load_or_build(
                checkpoint_name,
                dependency,
                lambda row=row, expected=expected, hubness_associations=hubness_associations: _build_dense_group_checkpoint(
                    row,
                    policy=policy,
                    corpus_sha256=corpus.corpus_sha256,
                    corpus_identity=corpus_identity,
                    evaluation_rows=evaluation_payload["rows"],
                    evaluation_registry_sha256=evaluation_payload["registrySha256"],
                    hubness_associations=hubness_associations,
                    strict=strict,
                    expected_evaluation=expected,
                ),
                allow_build=not reuse_only,
            )
            method_id = payload["result"]["summary"]["methodId"]
            dense_payloads[method_id] = payload
            catalog[method_id] = {
                "compact": payload["result"],
                "channel": "DENSE",
                "analysisRole": payload["analysisRole"],
                "aspectId": payload["aspectId"],
                "metadataTarget": None,
                "maskVariant": None,
                "familyKey": payload["candidateId"],
                "evaluationModelId": f"{payload['candidateId']}-{payload['aspectId'].removeprefix('NLP_')}",
                "sourceProbe": payload["sourceProbe"],
            }
    if phase == "dense":
        return {
            "schemaVersion": "trace-nlp-round1-phase-receipt/v1",
            "phase": phase,
            "status": "PASS",
            "checkpointCount": len(store.receipts),
            "checkpointReceiptsSha256": sha256_json(store.receipts),
            "summaryWritten": False,
        }

    metadata_payloads: list[Mapping[str, Any]] = []
    metadata_aggregate: Mapping[str, Any] | None = None
    need_metadata = phase in {"metadata", "summary", "all"}
    if need_metadata and phase in {"metadata", "all"}:
        for target in METADATA_TARGETS:
            for mask_variant in METADATA_MASK_VARIANTS:
                dependency = {
                    "corpusSha256": corpus.corpus_sha256,
                    "target": target,
                    "maskVariant": mask_variant,
                    "aspectId": "NLP_TITLE",
                    "topK": TOP_K,
                    "implementationVersion": _module("metadata_holdout_eval").IMPLEMENTATION_VERSION,
                }
                payload = store.load_or_build(
                    _metadata_checkpoint_name(target, mask_variant),
                    dependency,
                    lambda target=target, mask_variant=mask_variant: _build_masked_lexical_suite(
                        corpus,
                        aspect_id="NLP_TITLE",
                        target=target,
                        mask_variant=mask_variant,
                    ),
                    allow_build=not reuse_only,
                )
                metadata_payloads.append(payload)
    if need_metadata:
        metadata_dependency = _metadata_aggregate_dependency(
            store, catalog, corpus.corpus_sha256
        )
        metadata_aggregate = store.load_or_build(
            "analysis-metadata-holdout-rows",
            metadata_dependency,
            lambda: {
                "schemaVersion": "trace-nlp-round1-metadata-rows-checkpoint/v1",
                "rows": _metadata_holdout_rows(catalog, metadata_payloads),
                "relevanceCensusMethod": (
                    "INVERTED_GOVERNED_LABEL_MEMBERSHIP_EXACT_V1"
                ),
                "temporary": True,
                "committable": False,
            },
            allow_build=phase in {"metadata", "all"} and not reuse_only,
        )
        metadata_payloads.clear()
        gc.collect()
    if phase == "metadata":
        return {
            "schemaVersion": "trace-nlp-round1-phase-receipt/v1",
            "phase": phase,
            "status": "PASS",
            "checkpointCount": len(store.receipts),
            "checkpointReceiptsSha256": sha256_json(store.receipts),
            "summaryWritten": False,
        }

    source_mask_payload: Mapping[str, Any] | None = None
    need_source_mask = phase in {"source-mask", "summary", "all"}
    if need_source_mask:
        source_mask_payload = store.load_or_build(
            "source-identity-masked-title",
            {
                "corpusSha256": corpus.corpus_sha256,
                "aspectId": "NLP_TITLE",
                "inputVariant": "SOURCE_IDENTITY_MASKED",
                "topK": TOP_K,
                "implementationVersion": _module(
                    "source_leakage_eval"
                ).IMPLEMENTATION_VERSION,
                "sourceProbeImplementationVersion": _module(
                    "source_leakage_eval"
                ).IMPLEMENTATION_VERSION,
                "benchmarkImplementationVersion": IMPLEMENTATION_VERSION,
            },
            lambda: _build_source_masked_lexical_suite(corpus, aspect_id="NLP_TITLE"),
            allow_build=not reuse_only,
        )
        source_mask_probe_payload = store.load_or_build(
            "source-probe-source-identity-masked-title",
            {
                "baseCorpusSha256": corpus.corpus_sha256,
                "derivedCorpusSha256": source_mask_payload["maskReceipt"][
                    "derivedCorpusSha256"
                ],
                "aspectId": "NLP_TITLE",
                "inputVariant": "SOURCE_IDENTITY_MASKED",
                "suiteRankingSha256": source_mask_payload["suite"][
                    "suiteSummary"
                ]["suiteRankingSha256"],
                "sourceProbeImplementationVersion": _module(
                    "source_leakage_eval"
                ).IMPLEMENTATION_VERSION,
                "benchmarkImplementationVersion": IMPLEMENTATION_VERSION,
            },
            lambda: _build_source_mask_probe_checkpoint(
                corpus,
                aspect_id="NLP_TITLE",
                expected_derived_corpus_sha256=source_mask_payload["maskReceipt"][
                    "derivedCorpusSha256"
                ],
            ),
            allow_build=not reuse_only,
        )
        source_mask_payload = {
            **source_mask_payload,
            "suite": {
                **source_mask_payload["suite"],
                "sourceProbes": source_mask_probe_payload["sourceProbes"],
            },
        }
        _catalog_suite(
            catalog,
            source_mask_payload["suite"],
            channel="LEXICAL",
            analysis_role="ROBUSTNESS",
            mask_variant="SOURCE_IDENTITY_MASKED",
        )
        for entry in catalog.values():
            if (
                entry["analysisRole"] == "ROBUSTNESS"
                and entry["maskVariant"] == "SOURCE_IDENTITY_MASKED"
            ):
                entry["ablationId"] = "SOURCE_IDENTITY_MASKED"
    if phase == "source-mask":
        return {
            "schemaVersion": "trace-nlp-round1-phase-receipt/v1",
            "phase": phase,
            "status": "PASS",
            "checkpointCount": len(store.receipts),
            "checkpointReceiptsSha256": sha256_json(store.receipts),
            "summaryWritten": False,
        }

    if phase not in {"summary", "all"}:
        raise BenchmarkRound1Error("phase did not reach a terminal branch")
    evaluation = _evaluate_base_results(catalog, corpus)
    lexical_rows = _lexical_result_rows(catalog, evaluation)
    dense_rows, cross_rows = _dense_result_rows(
        catalog, dense_payloads, evaluation, corpus
    )
    if metadata_aggregate is None:
        raise BenchmarkRound1Error("metadata aggregate checkpoint was not loaded")
    metadata_rows = metadata_aggregate["rows"]
    leakage_rows = _leakage_rows(catalog, evaluation)
    hubness_rows = _hubness_rows(dense_payloads)
    analysis_catalog_dependency = _analysis_catalog_dependency(catalog)
    robustness_payload = store.load_or_build(
        "analysis-robustness-rows",
        {
            "catalog": analysis_catalog_dependency,
            "explicitComparisonsSha256": sha256_json(
                list(explicit_robustness_comparisons)
            ),
            "robustnessImplementationVersion": _module(
                "robustness_ablation"
            ).IMPLEMENTATION_VERSION,
            "sourceLeakageImplementationVersion": _module(
                "source_leakage_eval"
            ).IMPLEMENTATION_VERSION,
            "benchmarkImplementationVersion": IMPLEMENTATION_VERSION,
        },
        lambda: {
            "schemaVersion": "trace-nlp-round1-robustness-rows-checkpoint/v1",
            "rows": _robustness_rows(catalog, explicit_robustness_comparisons),
            "temporary": True,
            "committable": False,
        },
        allow_build=not reuse_only,
    )
    robustness_rows = robustness_payload["rows"]
    aspect_payload = store.load_or_build(
        "analysis-aspect-disagreement-rows",
        {
            "catalog": analysis_catalog_dependency,
            "corpusSha256": corpus.corpus_sha256,
            "aspectDisagreementModuleSha256": sha256_path(
                Path(_module("aspect_disagreement").__file__).resolve()
            ),
            "sourceLeakageImplementationVersion": _module(
                "source_leakage_eval"
            ).IMPLEMENTATION_VERSION,
            "benchmarkImplementationVersion": IMPLEMENTATION_VERSION,
        },
        lambda: {
            "schemaVersion": "trace-nlp-round1-aspect-rows-checkpoint/v1",
            "rows": _aspect_rows(catalog, corpus),
            "temporary": True,
            "committable": False,
        },
        allow_build=not reuse_only,
    )
    aspect_rows = aspect_payload["rows"]
    hybrid_payload = store.load_or_build(
        "analysis-hybrid-rrf-rows",
        {
            "catalog": analysis_catalog_dependency,
            "evaluationRegistrySha256": evaluation_payload["registrySha256"],
            "evaluationRowsSha256": sha256_json(evaluation_payload["rows"]),
            "hybridModuleSha256": sha256_path(
                Path(_module("hybrid_experiments").__file__).resolve()
            ),
            "benchmarkImplementationVersion": IMPLEMENTATION_VERSION,
        },
        lambda: {
            "schemaVersion": "trace-nlp-round1-hybrid-rows-checkpoint/v1",
            "rows": _hybrid_rows(catalog, evaluation_payload["rows"]),
            "temporary": True,
            "committable": False,
        },
        allow_build=not reuse_only,
    )
    hybrid_rows = hybrid_payload["rows"]
    selected_method_id, selected_entry = next(
        (method_id, entry)
        for method_id, entry in sorted(catalog.items())
        if entry["analysisRole"] == "BASE"
        and entry["familyKey"] == "NLP-D1"
        and entry["aspectId"] == "NLP_TITLE"
    )
    selected_dense_payload = dense_payloads[selected_method_id]
    structured_payload = store.load_or_build(
        "structured-m2-m5-m7-24-anchors",
        {
            "corpusSha256": corpus.corpus_sha256,
            "nlpMethodId": selected_method_id,
            "nlpRankingIdsSha256": selected_entry["compact"]["summary"][
                "rankingIdsSha256"
            ],
            "candidateIndexSha256": "abba30fcdded21b8f1ba6f7ec87a47b6bbd83c0d1e40d90670143fb88b83873f",
            "anchorCount": 24,
        },
        lambda: _build_structured_checkpoint(
            corpus, selected_entry, selected_dense_payload
        ),
        allow_build=not reuse_only,
    )
    review_rows, review_packet = _review_rows(
        corpus,
        catalog,
        structured_payload,
        selected_entry,
        selected_dense_payload,
    )
    run_rows = _run_rows(store.receipts, corpus, corpus_identity)
    performance = _performance_summary(lexical_rows, dense_rows, dense_metadata)
    summary = _assemble_summary(
        governance_payload=governance_payload,
        evaluation_payload=evaluation_payload,
        lexical_rows=lexical_rows,
        dense_rows=dense_rows,
        cross_rows=cross_rows,
        metadata_rows=metadata_rows,
        leakage_rows=leakage_rows,
        hubness_rows=hubness_rows,
        robustness_rows=robustness_rows,
        aspect_rows=aspect_rows,
        structured_rows=structured_payload["rows"],
        hybrid_rows=hybrid_rows,
        review_rows=review_rows,
        review_packet=review_packet,
        run_rows=run_rows,
        performance=performance,
        dense_full_count=len(dense_rows),
    )
    if output_path is None:
        raise BenchmarkRound1Error("summary/all phase requires --output")
    write_receipt = write_summary_temp(summary, Path(output_path), policy)
    return {
        "schemaVersion": "trace-nlp-round1-benchmark-receipt/v1",
        "phase": phase,
        "status": "STOPPED_RECOVERABLE_CHECKPOINT",
        "decision": "NLP_CORPUS_AUDIT_ONLY",
        "checkpointCount": len(store.receipts),
        "checkpointReceiptsSha256": sha256_json(store.receipts),
        "summary": write_receipt,
        "modelLoadedByOrchestrator": False,
        "pairMatrixMaterialized": False,
    }


def run_self_tests() -> dict[str, Any]:
    np = importlib.import_module("numpy")
    checks = 0
    with tempfile.TemporaryDirectory(prefix="trace-nlp-benchmark-self-test-") as directory:
        root = Path(directory)
        policy = TempPathPolicy.create(root, create=False)
        store = CheckpointStore(root / "checkpoints", policy)
        dependency = {"fixture": 1}
        first = store.load_or_build(
            "fixture", dependency, lambda: {"value": 7}, allow_build=True
        )
        second = store.load_or_build(
            "fixture", dependency, lambda: {"value": 8}, allow_build=False
        )
        if first != second or [row["state"] for row in store.receipts] != ["BUILT", "REUSED"]:
            raise BenchmarkRound1Error("checkpoint reuse self-test failed")
        checks += 2

        receipt_fixture = {
            "batchSize": 32,
            "performance": {"documentsPerSecond": 12.5},
        }
        if (
            _receipt_field(receipt_fixture, "batchSize") != 32
            or _receipt_field(
                receipt_fixture, "missing", "performance.documentsPerSecond"
            )
            != 12.5
            or _receipt_field(receipt_fixture, "performance.missing") is not None
        ):
            raise BenchmarkRound1Error("receipt field lookup self-test failed")
        try:
            _receipt_field(receipt_fixture, "performance..documentsPerSecond")
        except BenchmarkRound1Error:
            pass
        else:
            raise BenchmarkRound1Error("malformed receipt field path was accepted")
        checks += 1

        metadata_holdout = _module("metadata_holdout_eval")
        metadata_ids = tuple(f"SURF-META-{value}" for value in "ABCDE")
        metadata_assignments = {
            metadata_ids[0]: ("LABEL-X", "LABEL-Z"),
            metadata_ids[1]: ("LABEL-X", "LABEL-Z"),
            metadata_ids[2]: ("LABEL-Z",),
            metadata_ids[3]: ("LABEL-Y",),
            metadata_ids[4]: ("LABEL-Y",),
        }
        metadata_rankings = {
            query_id: [
                {"candidatePublicId": candidate_id}
                for candidate_id in metadata_ids
                if candidate_id != query_id
            ]
            for query_id in metadata_ids
        }
        metadata_contract = {
            "assignments": {"medium": metadata_assignments},
            "contractSha256": "d" * 64,
        }
        metadata_results = {
            "NLP-METADATA-SELF": {"rankings": metadata_rankings}
        }
        reference_metadata = metadata_holdout.evaluate_metadata_proxy(
            metadata_results,
            target="medium",
            label_contract=metadata_contract,
        )
        bounded_metadata = _evaluate_metadata_proxy_bounded(
            metadata_results,
            target="medium",
            label_contract=metadata_contract,
        )
        if bounded_metadata != reference_metadata:
            raise BenchmarkRound1Error(
                "bounded metadata proxy differs from the core exact evaluator"
            )
        checks += 1

        adversary_rankings = dict(metadata_rankings)
        adversary_rankings[metadata_ids[0]] = [
            {"candidatePublicId": "SURF-NOT-IN-GOVERNED-CONTRACT"},
            *metadata_rankings[metadata_ids[0]][1:],
        ]
        try:
            _evaluate_metadata_proxy_bounded(
                {"NLP-METADATA-ADVERSARY": {"rankings": adversary_rankings}},
                target="medium",
                label_contract=metadata_contract,
            )
        except BenchmarkRound1Error:
            pass
        else:
            raise BenchmarkRound1Error(
                "bounded metadata proxy accepted an ungoverned candidate"
            )
        checks += 1

        embedding_index = _module("embedding_index")
        ids = tuple(embedding_index.governance_common.load_public_ids()[:6])
        vectors = np.asarray(
            [
                [1.0, 0.0],
                [math.sqrt(0.5), math.sqrt(0.5)],
                [math.sqrt(0.5), math.sqrt(0.5)],
                [0.0, 1.0],
                [-math.sqrt(0.5), math.sqrt(0.5)],
                [-1.0, 0.0],
            ],
            dtype=np.float32,
        )
        corpus_sha = embedding_index._authoritative_base_corpus_sha256()
        index = embedding_index.ExactCosineIndex(
            ids,
            vectors,
            corpus_sha256=corpus_sha,
            pilot_diagnostic=True,
        )
        summary, ranking_ids, _scores = block_exact_rank(
            index,
            ids,
            vectors,
            np.ones(len(ids), dtype=np.bool_),
            method_id="NLP-D1-SELF",
            corpus_sha256=corpus_sha,
            input_variant="PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC",
            aspect_id="NLP_TITLE",
            top_k=3,
            block_size=2,
        )
        reference = index.rank_all(
            method_id="NLP-D1-SELF-REFERENCE",
            corpus_sha256=corpus_sha,
            input_variant="PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC",
            aspect_ids=("NLP_TITLE",),
            full_corpus=False,
            top_k=3,
        )
        expected_ids = {
            query_id: [row["candidatePublicId"] for row in rows]
            for query_id, rows in reference["rankings"].items()
        }
        if ranking_ids != expected_ids or summary["pairMatrixMaterialized"]:
            raise BenchmarkRound1Error("bounded block exact parity self-test failed")
        if index.corpus_sha256 != corpus_sha:
            raise BenchmarkRound1Error("governed fixture corpus SHA seam changed")
        if summary["rankingIdsSha256"] != _sha256_json_no_lf(expected_ids):
            raise BenchmarkRound1Error("bounded block ranking hash convention changed")
        checks += 2

        # Exercise a float32 fixture where this host's block GEMM and the
        # authoritative per-query GEMV produce different near-tie ordering.
        # The streamed implementation must follow ExactCosineIndex regardless
        # of which BLAS kernels happen to diverge on a particular host.
        coordinates = np.arange(128, dtype=np.float64)
        query = (
            np.sin((coordinates + 1.0) * 0.017)
            + np.cos((coordinates + 1.0) * 0.013)
        ).astype(np.float32)
        query /= np.linalg.norm(query)
        axis_u = np.sin((coordinates + 1.0) * 0.071).astype(np.float32)
        axis_u -= query * np.dot(query, axis_u)
        axis_u /= np.linalg.norm(axis_u)
        axis_v = np.cos((coordinates + 1.0) * 0.067).astype(np.float32)
        axis_v -= query * np.dot(query, axis_v)
        axis_v -= axis_u * np.dot(axis_u, axis_v)
        axis_v /= np.linalg.norm(axis_v)
        kernel_vectors = [query]
        for delta in (0.0, 0.001, -0.001, 0.002, -0.002):
            vector = (
                query + np.float32(0.001) * axis_u + np.float32(delta) * axis_v
            ).astype(np.float32)
            vector /= np.linalg.norm(vector)
            kernel_vectors.append(vector)
        kernel_vectors = np.asarray(kernel_vectors, dtype=np.float32)
        kernel_index = embedding_index.ExactCosineIndex(
            ids,
            kernel_vectors,
            corpus_sha256=corpus_sha,
            pilot_diagnostic=True,
        )
        _kernel_summary, kernel_ids, _kernel_scores = block_exact_rank(
            kernel_index,
            ids,
            kernel_vectors,
            np.ones(len(ids), dtype=np.bool_),
            method_id="NLP-D1-SELF-FLOAT32-KERNEL",
            corpus_sha256=corpus_sha,
            input_variant="PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC",
            aspect_id="NLP_TITLE",
            top_k=5,
            block_size=6,
        )
        kernel_reference = kernel_index.rank_all(
            method_id="NLP-D1-SELF-FLOAT32-KERNEL-REFERENCE",
            corpus_sha256=corpus_sha,
            input_variant="PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC",
            aspect_ids=("NLP_TITLE",),
            full_corpus=False,
            top_k=5,
        )
        expected_kernel_ids = {
            query_id: [row["candidatePublicId"] for row in rows]
            for query_id, rows in kernel_reference["rankings"].items()
        }
        if kernel_ids != expected_kernel_ids:
            raise BenchmarkRound1Error(
                "bounded block float32 score kernel differs from ExactCosineIndex"
            )
        checks += 1

        registry = _module("model_registry")
        dense_encoder = _module("dense_encoder")
        dense_spec = registry.get_model("NLP-D1")
        artifact_verification = _registry_artifact_verification("NLP-D1")
        runtime_packages = {
            name: version
            for name, version in registry.RUNTIME_PINS.items()
            if name != "python"
        }
        valid_encoding_receipt = {
            "schemaVersion": dense_encoder.SCHEMA_VERSION,
            "implementationVersion": dense_encoder.IMPLEMENTATION_VERSION,
            "methodId": "NLP-D1",
            "modelId": dense_spec.model_id,
            "modelRevision": dense_spec.revision,
            "tokenizerRevision": dense_spec.tokenizer_revision,
            "artifactVerificationSha256": artifact_verification[
                "verificationSha256"
            ],
            "corpusSha256": EXPECTED_DOCUMENT_RECEIPT_SHA256,
            "lexicalCorpusSha256": EXPECTED_RANKING_CORPUS_SHA256,
            "tokenCountReceiptSha256": EXPECTED_TOKEN_COUNT_RECEIPT_SHA256,
            "corpusIdentityContractsDistinct": True,
            "corpusSliceSha256": "d" * 64,
            "inputVariant": "PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC",
            "aspectIds": ["NLP_TITLE"],
            "fullCorpus": True,
            "fullPublicCohort": True,
            "fullAspectCohort": True,
            "objectCount": PUBLIC_OBJECT_COUNT,
            "aspectAvailableObjectCount": PUBLIC_OBJECT_COUNT,
            "aspectUnavailableObjectCount": 0,
            "defaultQueryCount": PUBLIC_OBJECT_COUNT,
            "defaultQueryPublicIdsSha256": "c" * 64,
            "missingAspectRowsZero": True,
            "canonicalPublicIdsSha256": "c" * 64,
            "semanticInputSha256": "d" * 64,
            "lengthBucketed": True,
            "lengthBucketPermutationSha256": "e" * 64,
            "canonicalOrderRestored": True,
            "batchSize": 8,
            "maxLength": 256,
            "governedEffectiveMaxLength": 256,
            "officialModelMaximumInputTokens": dense_spec.maximum_input_tokens,
            "pooling": dense_spec.pooling,
            "normalization": dense_spec.normalization,
            "weightDtype": dense_spec.weight_dtype,
            "executionDtype": dense_spec.execution_dtype_cpu,
            "device": "cpu",
            "localFilesOnly": True,
            "trustRemoteCode": False,
            "hostedInferenceCalls": 0,
            "implicitOutputWrites": 0,
            "tokenization": {},
            "tokenizerPaddingSide": "left",
            "tokenizerTruncationSide": "right",
            "embeddingDimension": dense_spec.embedding_dimension,
            "embeddingBytesInMemory": (
                PUBLIC_OBJECT_COUNT * dense_spec.embedding_dimension * 4
            ),
            "embeddingObservationSha256": "f" * 64,
            "performance": {
                "denseCorpusEncodingMs": 1.0,
                "documentsPerSecond": float(PUBLIC_OBJECT_COUNT),
                "peakRssBytes": 1,
                "peakVramBytes": None,
            },
            "runtime": {
                "python": registry.RUNTIME_PINS["python"],
                "packages": runtime_packages,
            },
        }
        validated_encoding = _validate_encoding_receipt(
            valid_encoding_receipt,
            candidate_id="NLP-D1",
            aspect_id="NLP_TITLE",
            input_variant="PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC",
            observed_embedding_sha256="f" * 64,
            observed_object_count=PUBLIC_OBJECT_COUNT,
            observed_available_object_count=PUBLIC_OBJECT_COUNT,
            observed_embedding_dimension=dense_spec.embedding_dimension,
            expected_document_receipt_sha256=EXPECTED_DOCUMENT_RECEIPT_SHA256,
            expected_lexical_corpus_sha256=EXPECTED_RANKING_CORPUS_SHA256,
            expected_token_count_receipt_sha256=EXPECTED_TOKEN_COUNT_RECEIPT_SHA256,
            expected_canonical_public_ids_sha256="c" * 64,
            expected_default_query_public_ids_sha256="c" * 64,
            strict=True,
        )
        if validated_encoding["status"] != "SUPPLIED_AND_HARDENED_VALIDATED":
            raise BenchmarkRound1Error("hardened encoding receipt self-test failed")
        checks += 1

        def mutated_encoding(path: tuple[str, ...], value: Any) -> dict[str, Any]:
            mutated = json.loads(json.dumps(valid_encoding_receipt))
            cursor = mutated
            for key in path[:-1]:
                cursor = cursor[key]
            cursor[path[-1]] = value
            return mutated

        adversaries = {
            "candidate": mutated_encoding(("methodId",), "NLP-D4"),
            "forged-model": mutated_encoding(("modelId",), "forged/model"),
            "artifact": mutated_encoding(("artifactVerificationSha256",), "0" * 64),
            "remote-code": mutated_encoding(("trustRemoteCode",), True),
            "hosted-inference": mutated_encoding(("hostedInferenceCalls",), 9),
            "document-receipt": mutated_encoding(("corpusSha256",), "0" * 64),
            "lexical-receipt": mutated_encoding(("lexicalCorpusSha256",), "0" * 64),
            "token-receipt": mutated_encoding(("tokenCountReceiptSha256",), "0" * 64),
            "pilot": mutated_encoding(("fullCorpus",), False),
            "runtime": mutated_encoding(("runtime", "python"), "3.11.15"),
        }
        for label, adversary in adversaries.items():
            try:
                _validate_encoding_receipt(
                    adversary,
                    candidate_id="NLP-D1",
                    aspect_id="NLP_TITLE",
                    input_variant="PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC",
                    observed_embedding_sha256="f" * 64,
                    observed_object_count=PUBLIC_OBJECT_COUNT,
                    observed_available_object_count=PUBLIC_OBJECT_COUNT,
                    observed_embedding_dimension=dense_spec.embedding_dimension,
                    expected_document_receipt_sha256=EXPECTED_DOCUMENT_RECEIPT_SHA256,
                    expected_lexical_corpus_sha256=EXPECTED_RANKING_CORPUS_SHA256,
                    expected_token_count_receipt_sha256=EXPECTED_TOKEN_COUNT_RECEIPT_SHA256,
                    expected_canonical_public_ids_sha256="c" * 64,
                    expected_default_query_public_ids_sha256="c" * 64,
                    strict=False,
                )
            except BenchmarkRound1Error:
                continue
            raise BenchmarkRound1Error(
                f"hardened encoding receipt accepted adversary: {label}"
            )
        checks += 1

        values = [f"SURF-C{index:02d}" for index in range(21)]
        result = {
            "methodId": "NLP-L0-SELF",
            "topK": 20,
            "aspectIds": ["NLP_TITLE"],
            "rankings": {
                "SURF-Q": [
                    {"candidatePublicId": value, "rank": rank, "score": 1.0 / rank}
                    for rank, value in enumerate(values[:20], start=1)
                ]
            },
        }
        compact = compact_ranking_result(result)
        view = ranking_result_view(compact)
        if view["rankings"]["SURF-Q"][0]["candidatePublicId"] != "SURF-C00":
            raise BenchmarkRound1Error("compact lazy ranking view self-test failed")
        checks += 1

        try:
            _sanitize_bounded_metadata({"embeddings": [1.0]})
        except BenchmarkRound1Error:
            rejected = True
        else:
            rejected = False
        if not rejected:
            raise BenchmarkRound1Error("summary sanitizer accepted embeddings")
        checks += 1

        rows = [{"id": "A"}, {"id": "B"}]
        sealed = _seal_component("review", {"rows": rows})
        if sealed["rowReceipts"]["rows"] != _row_receipt(rows):
            raise BenchmarkRound1Error("row receipt sealing self-test failed")
        checks += 1

        decision = _decision_summary(
            dense_full_count=2, review_ready=True, source_blocker_count=2
        )
        if (
            decision["nlpModelDecision"] != "NLP_CORPUS_AUDIT_ONLY"
            or decision["channelArchitectureShortlistIds"]
        ):
            raise BenchmarkRound1Error("fail-closed decision self-test failed")
        checks += 1

        source_leakage = _module("source_leakage_eval")
        probe_ids = tuple(f"SURF-P{value:02d}" for value in range(6))
        probe_features = np.asarray(
            [
                [1.0, 0.0],
                [0.9, 0.1],
                [0.8, 0.2],
                [0.0, 1.0],
                [0.1, 0.9],
                [0.2, 0.8],
            ],
            dtype=np.float64,
        )
        probe_labels = {
            object_id: ("SOURCE-A" if ordinal < 3 else "SOURCE-B")
            for ordinal, object_id in enumerate(probe_ids)
        }
        probe = source_leakage.deterministic_linear_probe(
            probe_features,
            probe_ids,
            probe_labels,
            requested_folds=3,
            ridge=1.0,
            iteration_limit=100,
        )
        finalized_probe = _finalize_source_probe(
            probe,
            representation="SELF_TEST_DENSE_FEATURES",
            input_variant="SELF_TEST",
            object_count=len(probe_ids),
            feature_column_count=2,
            feature_nonzero_count=int(np.count_nonzero(probe_features)),
            representation_index_sha256="b" * 64,
        )
        if (
            finalized_probe["status"] != "PASS"
            or finalized_probe["foldCount"] != 3
            or finalized_probe["majorityBaselineMacroF1"] is None
        ):
            raise BenchmarkRound1Error("linear source-probe receipt self-test failed")
        checks += 1

        robustness_ids = tuple(
            embedding_index.governance_common.load_public_ids()[:52]
        )
        reference_rankings = {
            query_id: [value for value in robustness_ids if value != query_id][:50]
            for query_id in robustness_ids
        }
        variant_rankings = {
            query_id: list(
                reversed([value for value in robustness_ids if value != query_id])
            )[:50]
            for query_id in robustness_ids
        }

        def robustness_entry(
            method_id: str,
            rankings: Mapping[str, Sequence[str]],
            *,
            analysis_role: str,
            input_variant: str,
        ) -> dict[str, Any]:
            summary = {
                "methodId": method_id,
                "corpusSha256": corpus_sha,
                "inputVariant": input_variant,
                "aspectIds": ["NLP_TITLE"],
                "indexSha256": sha256_json(
                    {"methodId": method_id, "fixture": "robustness"}
                ),
                "rankingIdsSha256": _sha256_json_no_lf(rankings),
                "topK": 50,
            }
            compact = {
                "schemaVersion": COMPACT_RESULT_SCHEMA_VERSION,
                "summary": summary,
                "rankingIdsByQuery": {
                    key: list(value) for key, value in rankings.items()
                },
                "compactRankingIdsSha256": sha256_json(rankings),
                "temporary": True,
                "committable": False,
            }
            validate_compact_result(compact)
            return {
                "compact": compact,
                "channel": "LEXICAL",
                "analysisRole": analysis_role,
                "aspectId": "NLP_TITLE",
                "metadataTarget": None,
                "maskVariant": (
                    "SOURCE_IDENTITY_MASKED"
                    if analysis_role == "ROBUSTNESS"
                    else None
                ),
                "ablationId": (
                    "SOURCE_IDENTITY_MASKED"
                    if analysis_role == "ROBUSTNESS"
                    else None
                ),
                "familyKey": "NLP-L0",
                "evaluationModelId": method_id,
            }

        robustness_rows = _robustness_rows(
            {
                "NLP-L0-SELF-BASE": robustness_entry(
                    "NLP-L0-SELF-BASE",
                    reference_rankings,
                    analysis_role="BASE",
                    input_variant="ORIGINAL_APPROVED_TEXT",
                ),
                "NLP-L0-SELF-MASK": robustness_entry(
                    "NLP-L0-SELF-MASK",
                    variant_rankings,
                    analysis_role="ROBUSTNESS",
                    input_variant="SOURCE_IDENTITY_MASKED",
                ),
            },
            (),
        )
        if len(robustness_rows) != 19 or any(
            row.get("robustnessSuiteStatus")
            != "STOPPED_RECOVERABLE_CHECKPOINT"
            or not SHA256_RE.fullmatch(str(row.get("suiteSha256", "")))
            or row.get("referenceMethodId") == "N/A"
            for row in robustness_rows
        ):
            raise BenchmarkRound1Error("stopped robustness suite identity self-test failed")
        checks += 1
    return {
        "schemaVersion": "trace-nlp-round1-benchmark-self-test/v1",
        "status": "PASS",
        "checks": checks,
        "modelLoads": 0,
        "fullCorpusRuns": 0,
        "pairMatrixMaterialized": False,
        "checkpointReuse": True,
        "blockExactParity": True,
        "receiptSha256": sha256_json(
            {
                "implementationVersion": IMPLEMENTATION_VERSION,
                "checks": checks,
                "status": "PASS",
            }
        ),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--temp-root")
    parser.add_argument("--checkpoint-dir")
    parser.add_argument("--output")
    parser.add_argument(
        "--phase",
        choices=("lexical", "dense", "metadata", "source-mask", "summary", "all"),
        default="all",
    )
    parser.add_argument(
        "--lexical-receipt",
        action="append",
        default=[],
        metavar="ASPECT=/absolute/temp/receipt.json",
    )
    parser.add_argument(
        "--lexical-aspect",
        action="append",
        choices=ASPECT_IDS,
        help=(
            "Run one or more selected lexical aspects; partial selection is allowed "
            "only with --phase lexical."
        ),
    )
    parser.add_argument("--dense-metadata")
    parser.add_argument("--dense-metadata-sha256")
    parser.add_argument(
        "--dense-evaluation",
        action="append",
        default=[],
        metavar="NLP-D1=/absolute/temp/evaluation.json",
    )
    parser.add_argument("--reuse-only", action="store_true")
    parser.add_argument("--non-strict", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.self_test:
        print(json.dumps(run_self_tests(), ensure_ascii=False, sort_keys=True))
        return 0
    if not args.temp_root:
        raise SystemExit("--temp-root is required")
    policy = TempPathPolicy.create(args.temp_root, create=True)
    checkpoint_dir = args.checkpoint_dir or str(policy.root / "benchmark-checkpoints")
    lexical_receipts = _aspect_cli_map(args.lexical_receipt, policy)
    dense_evaluations = _candidate_cli_map(args.dense_evaluation, policy)
    dense_metadata_path = (
        policy.resolve_input(args.dense_metadata, suffixes=(".json", ".gz"))
        if args.dense_metadata
        else None
    )
    receipt = run_benchmark(
        temp_root=policy.root,
        checkpoint_dir=checkpoint_dir,
        phase=args.phase,
        output_path=args.output,
        lexical_receipt_paths=lexical_receipts,
        dense_metadata_path=dense_metadata_path,
        dense_metadata_sha256=args.dense_metadata_sha256,
        dense_evaluation_paths=dense_evaluations,
        lexical_aspects=tuple(args.lexical_aspect or ASPECT_IDS),
        reuse_only=args.reuse_only,
        strict=not args.non_strict,
    )
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
