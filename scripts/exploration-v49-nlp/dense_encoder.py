#!/usr/bin/env python3
"""Offline, one-model-at-a-time dense encoder for governed TRACE NLP text.

Only already-downloaded, registry-verified Qwen3-Embedding-0.6B and
multilingual-e5-large-instruct snapshots are executable.  Text is token-count
bucketed deterministically, encoded on CPU, and restored to canonical public-ID
order.  No network, implicit file output, remote code, hosted inference, or
full embedding persistence is permitted.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib
import importlib.metadata
import json
import math
import os
import platform
import re
import shutil
import statistics
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import model_registry
import field_governance
import common as governance_common
import corpus_builder
import normalization


SCHEMA_VERSION = "trace-nlp-dense-encoding/v1"
IMPLEMENTATION_VERSION = "trace-nlp-dense-encoder-2026-08-24"
PUBLIC_OBJECT_LIMIT = 7_995
PUBLIC_ID_PATTERN = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
UUID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
PRIVATE_TOKEN_PATTERN = re.compile(r"(?:\bFOL-|\bTRN-OBJ-|\bTRTREE|\bTRBRANCH)", re.I)
URL_PATTERN = re.compile(r"(?:https?://|file://)", re.I)

OFFICIAL_ASYMMETRIC_QUERY = "OFFICIAL_ASYMMETRIC_QUERY"
OFFICIAL_ASYMMETRIC_DOCUMENT = "OFFICIAL_ASYMMETRIC_DOCUMENT"
PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC = "PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC"
INPUT_MODES = (
    OFFICIAL_ASYMMETRIC_QUERY,
    OFFICIAL_ASYMMETRIC_DOCUMENT,
    PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC,
)

APPROVED_ASPECT_IDS = (
    "NLP_TITLE",
    "NLP_SUBJECT",
    "NLP_SOURCE_NARRATIVE",
    "NLP_OBJECT_SEMANTIC_COMPOSITE",
)
TITLE_COMPOSITE_ALIAS = "NLP_OBJECT_SEMANTIC_COMPOSITE"
SUPPORTED_BATCH_SIZES = (8, 16, 32)
SUPPORTED_MAX_LENGTHS = (128, 256, 512)
DEFAULT_BATCH_SIZE = 8
DEFAULT_MAX_LENGTH = 512
MAX_PILOT_DOCUMENTS = 256
DEFAULT_PEAK_RSS_LIMIT_BYTES = 10 * 1024**3
DEFAULT_MIN_AVAILABLE_RAM_BYTES = 2 * 1024**3
DEFAULT_MIN_FREE_DISK_BYTES = 2 * 1024**3
MAX_TEMP_EMBEDDING_BYTES = 128 * 1024**2

_ACTIVE_LOCK = threading.Lock()
_ACTIVE_MODEL_ID: str | None = None


class DenseEncoderError(RuntimeError):
    """Raised when dense inference would violate a resource or governance gate."""


@dataclass(frozen=True)
class PreparedRecord:
    public_object_id: str
    canonical_ordinal: int
    source_text_sha256: str
    semantic_normalized_hash: str
    prepared_text: str
    token_count: int


@dataclass
class EncodingResult:
    """In-memory result; persistence requires an explicit approved temp path."""

    object_ids: tuple[str, ...]
    available_object_ids: tuple[str, ...]
    availability_mask: Any
    embeddings: Any
    receipt: dict[str, Any]


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def _authoritative_corpus_contracts() -> dict[str, Any]:
    """Load the frozen full-corpus receipts and per-aspect identities once."""

    bundle = corpus_builder.build_corpus_bundle(include_text=False)
    documents = bundle.get("documents")
    if not isinstance(documents, list) or len(documents) != PUBLIC_OBJECT_LIMIT:
        raise DenseEncoderError("authoritative corpus builder returned an invalid cohort")
    aspect_receipts: dict[str, dict[str, dict[str, Any]]] = {}
    for document in documents:
        if not isinstance(document, Mapping):
            raise DenseEncoderError("authoritative corpus document is malformed")
        object_id = str(document.get("publicObjectId", ""))
        aspects = document.get("aspects")
        if not isinstance(aspects, Mapping):
            raise DenseEncoderError("authoritative corpus document lacks aspects")
        aspect_receipts[object_id] = {
            str(aspect_id): {
                "originalTextHash": aspect.get("originalTextHash"),
                "semanticNormalizedHash": aspect.get("semanticNormalizedHash"),
                "lexicalCasefoldedHash": aspect.get("lexicalCasefoldedHash"),
                "sourceFieldIds": tuple(aspect.get("sourceFieldIds", ())),
                "sourceFieldRoles": tuple(aspect.get("sourceFieldRoles", ())),
                "characterCount": aspect.get("characterCount"),
                "tokenCount": aspect.get("tokenCount"),
                "tokenCountMethod": aspect.get("tokenCountMethod"),
            }
            for aspect_id, aspect in aspects.items()
            if isinstance(aspect, Mapping)
        }
    return {
        "documentReceiptSha256": str(bundle.get("documentReceiptSha256", "")),
        "tokenCountReceiptSha256": str(bundle.get("tokenCountReceiptSha256", "")),
        "lexicalCorpusSha256": str(bundle.get("corpusSha256", "")),
        "aspectReceiptsById": aspect_receipts,
    }


def _assert_authoritative_aspect(
    public_id: str, aspect_id: str, aspect: Mapping[str, Any]
) -> None:
    contracts = _authoritative_corpus_contracts()
    expected = contracts["aspectReceiptsById"].get(public_id, {}).get(aspect_id)
    observed = {
        "originalTextHash": aspect.get("originalTextHash"),
        "semanticNormalizedHash": aspect.get("semanticNormalizedHash"),
        "lexicalCasefoldedHash": aspect.get("lexicalCasefoldedHash"),
        "sourceFieldIds": tuple(aspect.get("sourceFieldIds", ())),
        "sourceFieldRoles": tuple(aspect.get("sourceFieldRoles", ())),
        "characterCount": aspect.get("characterCount"),
        "tokenCount": aspect.get("tokenCount"),
        "tokenCountMethod": aspect.get("tokenCountMethod"),
    }
    if expected is None or observed != expected:
        raise DenseEncoderError("aspect identity differs from the authoritative corpus")


def _quantile_r7(values: Sequence[int | float], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _aspect_mapping(record: Mapping[str, Any], aspect_id: str) -> Mapping[str, Any]:
    raw = record.get("aspects")
    if isinstance(raw, Mapping):
        aspect = raw.get(aspect_id)
    elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        matches = [
            item
            for item in raw
            if isinstance(item, Mapping) and item.get("aspectId") == aspect_id
        ]
        if len(matches) > 1:
            raise DenseEncoderError(f"duplicate aspect {aspect_id}")
        aspect = matches[0] if matches else None
    else:
        raise DenseEncoderError("record aspects must be a mapping or array")
    if not isinstance(aspect, Mapping):
        raise DenseEncoderError(f"record lacks requested aspect {aspect_id}")
    if aspect.get("aspectId", aspect_id) != aspect_id:
        raise DenseEncoderError("aspect mapping identity conflicts with its key")
    return aspect


def _validate_identity_and_pins(record: Mapping[str, Any]) -> str:
    if not isinstance(record, Mapping):
        raise DenseEncoderError("every corpus record must be a mapping")
    public_id = str(record.get("publicObjectId", "")).strip()
    alias = str(record.get("objectId", "")).strip()
    if public_id != alias or not PUBLIC_ID_PATTERN.fullmatch(public_id):
        raise DenseEncoderError("publicObjectId/objectId must be equal public surface IDs")
    try:
        governance_common.ensure_public_object_id(public_id)
    except governance_common.NlpBoundaryError as exc:
        # Keep held and unknown identities indistinguishable to callers.
        raise DenseEncoderError("object is not available in the public NLP cohort") from exc
    if record.get("held") is True or record.get("isHeld") is True:
        raise DenseEncoderError("held records cannot enter dense inference")
    required_pins = {
        "policyVersion": governance_common.CORPUS_POLICY_VERSION,
        "policySha256": field_governance.corpus_policy_sha256(),
        "fieldRegistryVersion": governance_common.REGISTRY_VERSION,
        "fieldRegistrySha256": field_governance.registry_sha256(),
        "normalizationVersion": governance_common.NORMALIZATION_VERSION,
        "aspectDocumentVersion": governance_common.ASPECT_DOCUMENT_VERSION,
    }
    if any(record.get(key) != value for key, value in required_pins.items()):
        raise DenseEncoderError("corpus record governance/version pins are absent or stale")
    return public_id


def _aspect_exists(record: Mapping[str, Any], aspect_id: str) -> bool:
    raw = record.get("aspects")
    if isinstance(raw, Mapping):
        return aspect_id in raw
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        return any(
            isinstance(item, Mapping) and item.get("aspectId") == aspect_id
            for item in raw
        )
    raise DenseEncoderError("record aspects must be a mapping or array")


def _validate_record(record: Mapping[str, Any], aspect_id: str) -> tuple[str, Mapping[str, Any], str]:
    public_id = _validate_identity_and_pins(record)
    aspect = _aspect_mapping(record, aspect_id)
    text = aspect.get("semanticNormalized")
    if not isinstance(text, str) or not text.strip():
        raise DenseEncoderError("semanticNormalized must be non-blank text")
    if UUID_PATTERN.search(text) or PRIVATE_TOKEN_PATTERN.search(text) or URL_PATTERN.search(text):
        raise DenseEncoderError("model input contains a private identifier or URL")
    if normalization.disallowed_controls(text):
        raise DenseEncoderError("model input contains a disallowed control character")
    if aspect.get("truncated") is not False:
        raise DenseEncoderError("corpus-builder text must be untruncated before model tokenization")
    if (
        aspect.get("modelInputTokenCap")
        != field_governance.model_input_token_caps()[aspect_id]
        or aspect.get("modelInputTruncationPolicy") != "HEAD_AT_MODEL_INPUT_ONLY"
    ):
        raise DenseEncoderError("aspect lacks the governed model-input truncation contract")
    declared_hash = str(aspect.get("semanticNormalizedHash", ""))
    actual_hash = _sha256_text(text)
    if not re.fullmatch(r"[0-9a-f]{64}", declared_hash):
        raise DenseEncoderError("aspect lacks semanticNormalizedHash")
    if declared_hash != actual_hash:
        raise DenseEncoderError("semanticNormalizedHash does not match model input")
    token_count = aspect.get("tokenCount")
    if (
        isinstance(token_count, bool)
        or not isinstance(token_count, int)
        or token_count != corpus_builder.lexical_token_count(str(aspect.get("lexicalCasefolded", "")))
        or aspect.get("tokenCountMethod") != corpus_builder.LEXICAL_TOKEN_COUNT_METHOD
    ):
        raise DenseEncoderError("aspect lexical token count is absent or inconsistent")
    if aspect_id == TITLE_COMPOSITE_ALIAS:
        if (
            aspect.get("compositePolicy") != "TITLE_ONLY"
            or tuple(aspect.get("includedAspectIds", ())) != ("NLP_TITLE",)
            or tuple(aspect.get("sourceFieldIds", ())) != ("NLP-FIELD-001",)
        ):
            raise DenseEncoderError("v1 semantic composite must remain title-only")
    return public_id, aspect, text


def prepare_model_text(
    spec: model_registry.ModelSpec,
    text: str,
    mode: str,
    *,
    task_description: str = model_registry.OFFICIAL_ARCHIVE_RETRIEVAL_TASK,
    allow_instruction_sensitivity: bool = False,
) -> str:
    if mode not in INPUT_MODES:
        raise DenseEncoderError(f"unsupported input mode: {mode}")
    if mode == OFFICIAL_ASYMMETRIC_QUERY:
        if spec.query_template is None:
            raise DenseEncoderError("candidate has no official query template")
        if (
            task_description != model_registry.OFFICIAL_ARCHIVE_RETRIEVAL_TASK
            and not allow_instruction_sensitivity
        ):
            raise DenseEncoderError("non-default instructions require a declared sensitivity run")
        if re.search(r"\b(influence|canonical(?:ity)?|importance|expert judgment)\b", task_description, re.I):
            raise DenseEncoderError("instruction introduces prohibited historical judgment")
        return spec.query_template.format(task_description=task_description, query=text)
    # Official document input and the separately declared symmetric diagnostic
    # are both plain text.  They remain different modes in every receipt.
    return text


def _offline_environment() -> dict[str, str]:
    values = {
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HF_DATASETS_OFFLINE": "1",
        "TOKENIZERS_PARALLELISM": "false",
        "WANDB_MODE": "offline",
    }
    for key, value in values.items():
        existing = os.environ.get(key)
        if existing is not None and existing != value:
            raise DenseEncoderError(f"conflicting offline environment setting: {key}")
        os.environ[key] = value
    return values


def runtime_versions() -> dict[str, Any]:
    packages: dict[str, str] = {}
    imports_confirmed: dict[str, bool] = {}
    import_names = {
        "torch": "torch",
        "transformers": "transformers",
        "tokenizers": "tokenizers",
        "numpy": "numpy",
        "scipy": "scipy",
        "huggingface-hub": "huggingface_hub",
        "safetensors": "safetensors",
        "accelerate": "accelerate",
        "psutil": "psutil",
    }
    for distribution in model_registry.RUNTIME_PINS:
        if distribution == "python":
            continue
        try:
            importlib.import_module(import_names[distribution])
            packages[distribution] = importlib.metadata.version(distribution)
            imports_confirmed[distribution] = True
        except (ImportError, importlib.metadata.PackageNotFoundError):
            packages[distribution] = "ABSENT"
            imports_confirmed[distribution] = False
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "environmentPrefix": sys.prefix,
        "basePrefix": sys.base_prefix,
        "packages": dict(sorted(packages.items())),
        "packageImportsConfirmed": dict(sorted(imports_confirmed.items())),
    }


def resource_snapshot(path: str | Path) -> dict[str, Any]:
    target = Path(path).expanduser().resolve()
    disk = shutil.disk_usage(target)
    try:
        psutil = importlib.import_module("psutil")
        memory = psutil.virtual_memory()
        rss = psutil.Process().memory_info().rss
        total_memory = int(memory.total)
        available_memory = int(memory.available)
    except (ImportError, AttributeError):
        total_memory = int(os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE"))
        available_memory = 0
        rss = 0
    return {
        "cpuLogicalCount": os.cpu_count(),
        "ramTotalBytes": total_memory,
        "ramAvailableBytes": available_memory,
        "processRssBytes": int(rss),
        "diskFreeBytes": int(disk.free),
        "diskTotalBytes": int(disk.total),
        "device": "cpu",
        "cuda": False,
        "mpsUsed": False,
        "vramBytes": None,
    }


def _preflight_resources(
    snapshot_path: Path,
    *,
    minimum_available_ram_bytes: int,
    minimum_free_disk_bytes: int,
) -> dict[str, Any]:
    snapshot = resource_snapshot(snapshot_path)
    if snapshot["diskFreeBytes"] < minimum_free_disk_bytes:
        raise DenseEncoderError("disk preflight failed")
    if (
        snapshot["ramAvailableBytes"]
        and snapshot["ramAvailableBytes"] < minimum_available_ram_bytes
    ):
        raise DenseEncoderError("available-memory preflight failed")
    return snapshot


def _current_rss_bytes() -> int:
    try:
        return int(importlib.import_module("psutil").Process().memory_info().rss)
    except (ImportError, AttributeError):
        return 0


def _token_lengths(tokenizer: Any, texts: Sequence[str], *, chunk_size: int = 128) -> list[int]:
    lengths: list[int] = []
    for start in range(0, len(texts), chunk_size):
        encoded = tokenizer(
            list(texts[start : start + chunk_size]),
            add_special_tokens=True,
            padding=False,
            truncation=False,
            return_attention_mask=False,
        )
        input_ids = encoded.get("input_ids")
        if not isinstance(input_ids, Sequence) or len(input_ids) != min(
            chunk_size, len(texts) - start
        ):
            raise DenseEncoderError("tokenizer returned an unexpected token census")
        lengths.extend(len(row) for row in input_ids)
    return lengths


def deterministic_length_order(records: Sequence[PreparedRecord]) -> tuple[int, ...]:
    """Return canonical ordinals sorted by full token count then public ID."""

    return tuple(
        row.canonical_ordinal
        for row in sorted(records, key=lambda row: (row.token_count, row.public_object_id))
    )


def _truncation_receipt(records: Sequence[PreparedRecord], max_length: int) -> dict[str, Any]:
    lengths = [record.token_count for record in records]
    removed = [max(0, value - max_length) for value in lengths]
    return {
        "tokenCountP50": _quantile_r7(lengths, 0.50),
        "tokenCountP90": _quantile_r7(lengths, 0.90),
        "tokenCountP95": _quantile_r7(lengths, 0.95),
        "tokenCountP99": _quantile_r7(lengths, 0.99),
        "tokenCountMax": max(lengths, default=0),
        "documentsTruncated": sum(value > 0 for value in removed),
        "tokensRemoved": sum(removed),
        "percentDocumentsTruncated": (
            100.0 * sum(value > 0 for value in removed) / len(records) if records else 0.0
        ),
        "maxLength": max_length,
        "truncationDirection": "HEAD",
        "applicationStage": "MODEL_INPUT_ONLY",
        "fullNormalizedHashesPreserved": True,
        "corpusTextOverwritten": False,
        "silentTruncation": False,
    }


class LocalDenseEncoder:
    """A verified local encoder holding the process-wide one-model lock."""

    def __init__(
        self,
        *,
        spec: model_registry.ModelSpec,
        snapshot_path: Path,
        tokenizer: Any,
        model: Any,
        torch_module: Any,
        artifact_receipt: Mapping[str, Any],
        load_resource_before: Mapping[str, Any],
        batch_size: int,
        max_length: int,
        peak_rss_limit_bytes: int,
    ) -> None:
        self.spec = spec
        self.snapshot_path = snapshot_path
        self.tokenizer = tokenizer
        self.model = model
        self.torch = torch_module
        self.artifact_receipt = dict(artifact_receipt)
        self.load_resource_before = dict(load_resource_before)
        self.batch_size = batch_size
        self.max_length = max_length
        self.peak_rss_limit_bytes = peak_rss_limit_bytes
        self._closed = False

    def __enter__(self) -> "LocalDenseEncoder":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def close(self) -> None:
        global _ACTIVE_MODEL_ID
        if self._closed:
            return
        self.model = None
        self.tokenizer = None
        gc.collect()
        _ACTIVE_MODEL_ID = None
        _ACTIVE_LOCK.release()
        self._closed = True

    def _pool(self, outputs: Any, attention_mask: Any) -> Any:
        hidden = outputs.last_hidden_state
        if self.spec.candidate_id == "NLP-D1":
            left_padded = bool((attention_mask[:, -1].sum() == attention_mask.shape[0]).item())
            if left_padded:
                return hidden[:, -1]
            sequence_lengths = attention_mask.sum(dim=1) - 1
            rows = self.torch.arange(hidden.shape[0], device=hidden.device)
            return hidden[rows, sequence_lengths]
        if self.spec.candidate_id == "NLP-D3":
            mask = attention_mask.unsqueeze(-1).to(hidden.dtype)
            return (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        raise DenseEncoderError("encoder pooling is not approved for this candidate")

    def encode_records(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        aspect_id: str,
        mode: str,
        full_corpus: bool,
        corpus_sha256: str | None = None,
        expected_object_count: int | None = None,
        task_description: str = model_registry.OFFICIAL_ARCHIVE_RETRIEVAL_TASK,
        allow_instruction_sensitivity: bool = False,
    ) -> EncodingResult:
        if self._closed:
            raise DenseEncoderError("encoder is closed")
        if aspect_id not in APPROVED_ASPECT_IDS:
            raise DenseEncoderError(f"aspect is not governed for this runner: {aspect_id}")
        authoritative_cap = field_governance.effective_model_input_token_cap(
            aspect_id, self.spec.maximum_input_tokens
        )
        if self.max_length > authoritative_cap:
            raise DenseEncoderError(
                f"max length {self.max_length} exceeds governed {aspect_id} cap {authoritative_cap}"
            )
        raw_records = list(records)
        if not raw_records:
            raise DenseEncoderError("dense encoding requires at least one record")
        if len(raw_records) > PUBLIC_OBJECT_LIMIT:
            raise DenseEncoderError("dense input exceeds the 7,995-object public boundary")
        if full_corpus and len(raw_records) != PUBLIC_OBJECT_LIMIT:
            raise DenseEncoderError(
                "full-corpus encoding requires the complete 7,995-object public cohort"
            )
        if not full_corpus and len(raw_records) > MAX_PILOT_DOCUMENTS:
            raise DenseEncoderError("pilot input exceeds the deterministic 256-document cap")
        if expected_object_count is not None and len(raw_records) != expected_object_count:
            raise DenseEncoderError("input count differs from the declared aspect cohort")

        ids = [_validate_identity_and_pins(record) for record in raw_records]
        if ids != sorted(ids) or len(ids) != len(set(ids)):
            raise DenseEncoderError("dense inputs must be sorted by unique public object ID")
        authoritative_ids = governance_common.load_public_ids()
        actual_full_public_cohort = tuple(ids) == authoritative_ids
        if bool(full_corpus) != actual_full_public_cohort:
            raise DenseEncoderError("full-corpus declaration differs from the authoritative public cohort")
        corpus_contracts = _authoritative_corpus_contracts()
        document_receipt_sha = corpus_contracts["documentReceiptSha256"]
        lexical_corpus_sha = corpus_contracts["lexicalCorpusSha256"]
        token_count_receipt_sha = corpus_contracts["tokenCountReceiptSha256"]
        for label, value in (
            ("documentReceiptSha256", document_receipt_sha),
            ("lexicalCorpusSha256", lexical_corpus_sha),
            ("tokenCountReceiptSha256", token_count_receipt_sha),
        ):
            if not re.fullmatch(r"[0-9a-f]{64}", value):
                raise DenseEncoderError(f"authoritative {label} is invalid")
        # The existing dense-encoding corpusSha256 contract is the corpus
        # builder's document receipt (69aa...).  Lexical index identity and the
        # new token-count contract remain separately named/bound below.
        if corpus_sha256 is not None and corpus_sha256 != document_receipt_sha:
            raise DenseEncoderError(
                "corpusSha256 does not match the authoritative document receipt"
            )
        if full_corpus and corpus_builder.corpus_identity_sha256(raw_records) != lexical_corpus_sha:
            raise DenseEncoderError("full dense corpus differs from the authoritative lexical identity")
        validated: list[tuple[int, str, Mapping[str, Any], str]] = []
        for canonical_ordinal, record in enumerate(raw_records):
            if not _aspect_exists(record, aspect_id):
                continue
            public_id, aspect, text = _validate_record(record, aspect_id)
            _assert_authoritative_aspect(public_id, aspect_id, aspect)
            validated.append((canonical_ordinal, public_id, aspect, text))
        if not validated:
            raise DenseEncoderError("requested aspect has no available model inputs")
        prepared_texts = [
            prepare_model_text(
                self.spec,
                text,
                mode,
                task_description=task_description,
                allow_instruction_sensitivity=allow_instruction_sensitivity,
            )
            for _, _, _, text in validated
        ]
        token_counts = _token_lengths(self.tokenizer, prepared_texts)
        prepared = [
            PreparedRecord(
                public_object_id=public_id,
                canonical_ordinal=canonical_ordinal,
                source_text_sha256=_sha256_text(prepared_texts[available_ordinal]),
                semantic_normalized_hash=str(aspect["semanticNormalizedHash"]),
                prepared_text=prepared_texts[available_ordinal],
                token_count=token_counts[available_ordinal],
            )
            for available_ordinal, (canonical_ordinal, public_id, aspect, _) in enumerate(validated)
        ]
        prepared_by_ordinal = {row.canonical_ordinal: row for row in prepared}
        encoding_order = deterministic_length_order(prepared)
        permutation_material = [
            {
                "encodingOrdinal": encoding_ordinal,
                "canonicalOrdinal": canonical_ordinal,
                "publicObjectId": prepared_by_ordinal[canonical_ordinal].public_object_id,
                "tokenCount": prepared_by_ordinal[canonical_ordinal].token_count,
            }
            for encoding_ordinal, canonical_ordinal in enumerate(encoding_order)
        ]
        permutation_sha256 = _sha256_json(permutation_material)
        semantic_input_material = [
            {
                "publicObjectId": row.public_object_id,
                "semanticNormalizedHash": row.semantic_normalized_hash,
                "preparedTextSha256": row.source_text_sha256,
            }
            for row in prepared
        ]
        inferred_corpus_sha = _sha256_json(semantic_input_material)

        np = importlib.import_module("numpy")
        # Full-corpus aspect indices retain all 7,995 canonical rows.  Missing
        # aspect rows are explicit zeros and are excluded from default queries.
        output = np.zeros(
            (len(raw_records), int(self.spec.embedding_dimension or 0)), dtype=np.float32
        )
        availability_mask = np.zeros(len(raw_records), dtype=np.bool_)
        for row in prepared:
            availability_mask[row.canonical_ordinal] = True
        started = time.perf_counter()
        peak_rss = _current_rss_bytes()
        encoded_count = 0
        for start in range(0, len(encoding_order), self.batch_size):
            batch_ordinals = encoding_order[start : start + self.batch_size]
            batch_text = [prepared_by_ordinal[ordinal].prepared_text for ordinal in batch_ordinals]
            tokens = self.tokenizer(
                batch_text,
                max_length=self.max_length,
                padding=True,
                truncation=True,
                return_tensors="pt",
            )
            tokens = {key: value.to("cpu") for key, value in tokens.items()}
            with self.torch.inference_mode():
                model_output = self.model(**tokens)
                pooled = self._pool(model_output, tokens["attention_mask"])
                normalized = self.torch.nn.functional.normalize(
                    pooled.float(), p=2, dim=1
                )
            vectors = normalized.detach().cpu().numpy().astype(np.float32, copy=False)
            if vectors.shape != (len(batch_ordinals), self.spec.embedding_dimension):
                raise DenseEncoderError("model returned an unexpected embedding shape")
            for row_index, canonical_ordinal in enumerate(batch_ordinals):
                output[canonical_ordinal] = vectors[row_index]
            encoded_count += len(batch_ordinals)
            peak_rss = max(peak_rss, _current_rss_bytes())
            if peak_rss > self.peak_rss_limit_bytes:
                raise DenseEncoderError("peak RSS gate exceeded; partial embeddings are discarded")
        elapsed = time.perf_counter() - started
        if encoded_count != len(prepared) or not np.isfinite(output).all():
            raise DenseEncoderError("dense encoding produced incomplete or non-finite output")
        norms = np.linalg.norm(output[availability_mask], axis=1)
        if not np.allclose(norms, 1.0, rtol=0.0, atol=2e-4):
            raise DenseEncoderError("dense embeddings are not L2-normalized")
        if np.any(output[~availability_mask] != 0.0):
            raise DenseEncoderError("unavailable aspect rows are not exact zeros")
        embedding_observation_sha = hashlib.sha256(
            output.astype("<f4", copy=False).tobytes(order="C")
        ).hexdigest()
        token_receipt = _truncation_receipt(prepared, self.max_length)
        receipt = {
            "schemaVersion": SCHEMA_VERSION,
            "implementationVersion": IMPLEMENTATION_VERSION,
            "methodId": self.spec.candidate_id,
            "modelId": self.spec.model_id,
            "modelRevision": self.spec.revision,
            "tokenizerRevision": self.spec.tokenizer_revision,
            "artifactVerificationSha256": self.artifact_receipt[
                "verificationSha256"
            ],
            "corpusSha256": document_receipt_sha,
            "lexicalCorpusSha256": lexical_corpus_sha,
            "tokenCountReceiptSha256": token_count_receipt_sha,
            "corpusIdentityContractsDistinct": True,
            "corpusSliceSha256": inferred_corpus_sha,
            "inputVariant": mode,
            "aspectIds": [aspect_id],
            "fullCorpus": bool(full_corpus),
            "fullPublicCohort": actual_full_public_cohort,
            "fullAspectCohort": bool(full_corpus),
            "objectCount": len(raw_records),
            "aspectAvailableObjectCount": len(prepared),
            "aspectUnavailableObjectCount": len(raw_records) - len(prepared),
            "defaultQueryCount": len(prepared),
            "defaultQueryPublicIdsSha256": _sha256_json(
                [row.public_object_id for row in prepared]
            ),
            "missingAspectRowsZero": True,
            "canonicalPublicIdsSha256": _sha256_json(ids),
            "semanticInputSha256": inferred_corpus_sha,
            "lengthBucketed": True,
            "lengthBucketPermutationSha256": permutation_sha256,
            "canonicalOrderRestored": True,
            "batchSize": self.batch_size,
            "maxLength": self.max_length,
            "governedEffectiveMaxLength": authoritative_cap,
            "officialModelMaximumInputTokens": self.spec.maximum_input_tokens,
            "pooling": self.spec.pooling,
            "normalization": self.spec.normalization,
            "weightDtype": self.spec.weight_dtype,
            "executionDtype": self.spec.execution_dtype_cpu,
            "device": "cpu",
            "localFilesOnly": True,
            "trustRemoteCode": False,
            "hostedInferenceCalls": 0,
            "tokenization": token_receipt,
            "tokenizerPaddingSide": self.tokenizer.padding_side,
            "tokenizerTruncationSide": self.tokenizer.truncation_side,
            "embeddingDimension": self.spec.embedding_dimension,
            "embeddingBytesInMemory": int(output.nbytes),
            "embeddingObservationSha256": embedding_observation_sha,
            "performance": {
                "denseCorpusEncodingMs": round(elapsed * 1000.0, 3),
                "documentsPerSecond": len(prepared) / elapsed if elapsed else None,
                "peakRssBytes": peak_rss,
                "peakVramBytes": None,
            },
            "determinism": {
                "semanticDeterminism": "pinned input hashes, templates, tokenizer revision, and canonical IDs",
                "rankingDeterminism": "not computed by encoder; canonical order restored",
                "floatingPointObservation": "hardware/runtime-specific bytes; hash recorded, byte identity not promised cross-hardware",
                "seedUsed": False,
            },
            "symmetricDiagnosticEquivalentToOfficialRetrieval": False,
            "historicalRelationProduced": False,
            "probabilityProduced": False,
            "implicitOutputWrites": 0,
            "runtime": runtime_versions(),
        }
        return EncodingResult(
            tuple(ids),
            tuple(row.public_object_id for row in prepared),
            availability_mask,
            output,
            receipt,
        )


def load_verified_encoder(
    candidate_id: str,
    snapshot_path: str | Path,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_length: int = DEFAULT_MAX_LENGTH,
    cpu_only: bool = True,
    peak_rss_limit_bytes: int = DEFAULT_PEAK_RSS_LIMIT_BYTES,
    minimum_available_ram_bytes: int = DEFAULT_MIN_AVAILABLE_RAM_BYTES,
    minimum_free_disk_bytes: int = DEFAULT_MIN_FREE_DISK_BYTES,
    enforce_runtime_pins: bool = False,
) -> LocalDenseEncoder:
    """Load one reviewed dense candidate from an exact local snapshot."""

    global _ACTIVE_MODEL_ID
    if candidate_id not in model_registry.FULL_CORPUS_EXECUTION_SHORTLIST:
        raise DenseEncoderError("candidate is not execution-ready in this round")
    if batch_size not in SUPPORTED_BATCH_SIZES:
        raise DenseEncoderError("batch size must be one of 8, 16, or 32")
    if max_length not in SUPPORTED_MAX_LENGTHS:
        raise DenseEncoderError("max length must be one of 128, 256, or 512")
    if not cpu_only:
        raise DenseEncoderError("this host contract permits CPU-only dense inference")
    spec = model_registry.get_model(candidate_id)
    if spec.trust_remote_code_required or spec.pickle_weight_present:
        raise DenseEncoderError("remote code and pickle weights are not executable")
    root = Path(snapshot_path).expanduser().resolve()
    artifact_receipt = model_registry.verify_local_snapshot(candidate_id, root)
    offline = _offline_environment()
    before = _preflight_resources(
        root,
        minimum_available_ram_bytes=minimum_available_ram_bytes,
        minimum_free_disk_bytes=minimum_free_disk_bytes,
    )
    observed = runtime_versions()
    mismatches = {
        name: {"expected": expected, "observed": observed_value}
        for name, expected in model_registry.RUNTIME_PINS.items()
        for observed_value in [
            observed["python"]
            if name == "python"
            else observed["packages"].get(name, "ABSENT")
        ]
        if observed_value != expected
    }
    if enforce_runtime_pins and mismatches:
        raise DenseEncoderError(f"runtime pin mismatch: {sorted(mismatches)}")
    if not _ACTIVE_LOCK.acquire(blocking=False):
        raise DenseEncoderError(f"another model is already resident: {_ACTIVE_MODEL_ID}")
    _ACTIVE_MODEL_ID = candidate_id
    try:
        torch = importlib.import_module("torch")
        transformers = importlib.import_module("transformers")
        torch.use_deterministic_algorithms(True)
        torch.set_num_threads(min(8, max(1, os.cpu_count() or 1)))
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            str(root),
            local_files_only=True,
            trust_remote_code=False,
            use_fast=True,
        )
        tokenizer.truncation_side = "right"
        tokenizer.padding_side = "left" if candidate_id == "NLP-D1" else "right"
        model = transformers.AutoModel.from_pretrained(
            str(root),
            local_files_only=True,
            trust_remote_code=False,
            dtype=torch.float32,
            low_cpu_mem_usage=True,
        )
        model.to("cpu")
        model.eval()
        if next(model.parameters()).device.type != "cpu":
            raise DenseEncoderError("model escaped the CPU-only device gate")
        if getattr(model.config, "hidden_size", None) != spec.embedding_dimension:
            raise DenseEncoderError("loaded model dimension differs from the registry")
        peak_after_load = _current_rss_bytes()
        if peak_after_load > peak_rss_limit_bytes:
            raise DenseEncoderError("model load exceeds the peak RSS gate")
        artifact_receipt = {
            **artifact_receipt,
            "offlineEnvironment": offline,
            "runtimePinMismatches": mismatches,
        }
        return LocalDenseEncoder(
            spec=spec,
            snapshot_path=root,
            tokenizer=tokenizer,
            model=model,
            torch_module=torch,
            artifact_receipt=artifact_receipt,
            load_resource_before=before,
            batch_size=batch_size,
            max_length=max_length,
            peak_rss_limit_bytes=peak_rss_limit_bytes,
        )
    except BaseException:
        _ACTIVE_MODEL_ID = None
        _ACTIVE_LOCK.release()
        raise


def encode_records(
    encoder: LocalDenseEncoder,
    records: Iterable[Mapping[str, Any]],
    **kwargs: Any,
) -> EncodingResult:
    """Functional wrapper around :meth:`LocalDenseEncoder.encode_records`."""

    return encoder.encode_records(records, **kwargs)


def load_governed_corpus_records() -> list[Mapping[str, Any]]:
    """Load the fixed corpus-builder API without redefining field semantics."""

    corpus_builder = importlib.import_module("corpus_builder")
    bundle = corpus_builder.build_corpus_bundle(include_text=True)
    if bundle.get("schemaVersion") != "trace-nlp-corpus-bundle/v1":
        raise DenseEncoderError("corpus bundle schema changed")
    documents = bundle.get("documents")
    if documents is None:
        documents = list(corpus_builder.iter_corpus_documents())
    if not isinstance(documents, Sequence):
        raise DenseEncoderError("corpus builder did not provide documents")
    return list(documents)


def _approved_temp_path(path: str | Path, *, suffix: str) -> Path:
    raw = Path(path).expanduser()
    if not raw.is_absolute():
        raise DenseEncoderError("temporary output path must be explicit and absolute")
    target = raw.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if target != temp_root and temp_root not in target.parents:
        raise DenseEncoderError("full embeddings may be written only below the OS temp root")
    if target.suffix != suffix:
        raise DenseEncoderError(f"temporary output must use {suffix}")
    if target.exists():
        raise DenseEncoderError("temporary output already exists; refusing overwrite")
    return target


def write_embeddings_temp(result: EncodingResult, path: str | Path) -> dict[str, Any]:
    """Persist one bounded embedding block only to an explicit temp `.npz`."""

    target = _approved_temp_path(path, suffix=".npz")
    if int(result.embeddings.nbytes) > MAX_TEMP_EMBEDDING_BYTES:
        raise DenseEncoderError("embedding block exceeds the bounded temp-output limit")
    target.parent.mkdir(parents=True, exist_ok=True)
    np = importlib.import_module("numpy")
    np.savez(
        target,
        public_object_ids=np.asarray(result.object_ids),
        availability_mask=result.availability_mask,
        embeddings=result.embeddings.astype("<f4", copy=False),
    )
    digest = hashlib.sha256()
    with target.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "schemaVersion": "trace-nlp-temp-embedding-receipt/v1",
        "path": str(target),
        "byteCount": target.stat().st_size,
        "sha256": digest.hexdigest(),
        "objectCount": len(result.object_ids),
        "embeddingDimension": int(result.embeddings.shape[1]),
        "temporary": True,
        "committable": False,
    }


def run_self_tests() -> dict[str, Any]:
    spec = model_registry.get_model("NLP-D1")
    plain = "A short governed title"
    query = prepare_model_text(spec, plain, OFFICIAL_ASYMMETRIC_QUERY)
    if query != (
        "Instruct: Given a web search query, retrieve relevant passages that answer the query\n"
        "Query:A short governed title"
    ):
        raise AssertionError("Qwen official query template changed")
    if prepare_model_text(spec, plain, OFFICIAL_ASYMMETRIC_DOCUMENT) != plain:
        raise AssertionError("official document input is not plain")
    if prepare_model_text(spec, plain, PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC) != plain:
        raise AssertionError("symmetric diagnostic is not plain/plain")
    rows = (
        PreparedRecord("SURF-B", 1, "a" * 64, "b" * 64, "b", 2),
        PreparedRecord("SURF-A", 0, "a" * 64, "b" * 64, "a", 2),
        PreparedRecord("SURF-C", 2, "a" * 64, "b" * 64, "c", 1),
    )
    if deterministic_length_order(rows) != (2, 0, 1):
        raise AssertionError("length bucketing is not token-count/public-ID deterministic")
    if _truncation_receipt(rows, 1)["documentsTruncated"] != 2:
        raise AssertionError("truncation receipt changed")
    try:
        prepare_model_text(
            spec,
            plain,
            OFFICIAL_ASYMMETRIC_QUERY,
            task_description="Find canonical influence",
            allow_instruction_sensitivity=True,
        )
    except DenseEncoderError:
        pass
    else:
        raise AssertionError("prohibited historical-judgment instruction was accepted")
    try:
        _approved_temp_path(Path.cwd() / "embeddings.npz", suffix=".npz")
    except DenseEncoderError:
        pass
    else:
        raise AssertionError("repository embedding output was accepted")
    forged = {
        "publicObjectId": "SURF-NOTINLEDGER",
        "objectId": "SURF-NOTINLEDGER",
        "policyVersion": governance_common.CORPUS_POLICY_VERSION,
        "policySha256": field_governance.corpus_policy_sha256(),
        "fieldRegistryVersion": governance_common.REGISTRY_VERSION,
        "fieldRegistrySha256": field_governance.registry_sha256(),
        "normalizationVersion": governance_common.NORMALIZATION_VERSION,
        "aspectDocumentVersion": governance_common.ASPECT_DOCUMENT_VERSION,
    }
    try:
        _validate_identity_and_pins(forged)
    except DenseEncoderError:
        pass
    else:
        raise AssertionError("non-ledger identity entered dense inference")
    contracts = _authoritative_corpus_contracts()
    expected_contracts = {
        "documentReceiptSha256": "69aa8f290f7390bdb8ce7c0a3cf4ecdfb7426c908804bf48f9126c0eec4fdac8",
        "lexicalCorpusSha256": "7cde5cfdcf0a0bfd4762f9e23c3b50287a0b9071cbf0bd21102bca4ae2ee024c",
        "tokenCountReceiptSha256": "511eee824342ded9c6ac4606af3f99dea79844663ebd550cbbca2ac2ba2cecca",
    }
    if any(contracts[key] != value for key, value in expected_contracts.items()):
        raise AssertionError("dense corpus identity contracts changed")
    first_id = governance_common.load_public_ids()[0]
    forged_aspect = dict(contracts["aspectReceiptsById"][first_id]["NLP_TITLE"])
    forged_aspect["semanticNormalizedHash"] = "f" * 64
    try:
        _assert_authoritative_aspect(first_id, "NLP_TITLE", forged_aspect)
    except DenseEncoderError:
        pass
    else:
        raise AssertionError("caller-forged aspect identity entered dense inference")
    return {
        "schemaVersion": "trace-nlp-dense-encoder-self-test/v1",
        "status": "PASS",
        "supportedCandidates": list(model_registry.FULL_CORPUS_EXECUTION_SHORTLIST),
        "inputModes": list(INPUT_MODES),
        "batchSizes": list(SUPPORTED_BATCH_SIZES),
        "maxLengths": list(SUPPORTED_MAX_LENGTHS),
        "lengthBucketed": True,
        "canonicalOrderRestored": True,
        "networkCalls": 0,
        "modelLoads": 0,
        "nonLedgerIdentityRejected": True,
        "forgedAspectIdentityRejected": True,
        **expected_contracts,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--runtime", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.self_test:
        print(json.dumps(run_self_tests(), sort_keys=True))
        return 0
    if args.runtime:
        print(json.dumps(runtime_versions(), sort_keys=True, indent=2))
        return 0
    raise SystemExit("dense inference requires an explicit Python call; use --self-test")


if __name__ == "__main__":
    raise SystemExit(main())
