#!/usr/bin/env python3
"""Build the governed TRACE NLP aspect corpus in memory or local-only storage."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections.abc import Callable, Iterable, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterator, Mapping

from common import (
    ASPECT_DOCUMENT_VERSION,
    CANONICAL_OBJECT_COUNT,
    CORPUS_POLICY_VERSION,
    EXPECTED_SHA256,
    HELD_OBJECT_COUNT,
    NORMALIZATION_VERSION,
    PUBLIC_OBJECT_COUNT,
    REGISTRY_VERSION,
    NlpBoundaryError,
    contains_private_token,
    ensure_public_object_id,
    load_context_records,
    load_public_boundary,
    load_public_canonical_surfaces,
    sha256_json,
    sha256_text,
)
from field_governance import (
    corpus_policy_sha256,
    effective_model_input_token_cap,
    field_decision,
    model_input_token_caps,
    registry_sha256,
)
from language_script_audit import classify_unicode
from normalization import DisallowedControlError, NormalizationResult, normalize_text


CORPUS_BUNDLE_SCHEMA_VERSION = "trace-nlp-corpus-bundle/v1"
CORPUS_DOCUMENT_SCHEMA_VERSION = "trace-nlp-aspect-document/v1"
TOKENIZER_LENGTH_CENSUS_SCHEMA_VERSION = "trace-nlp-tokenizer-length-census/v1"
TOKEN_TRUNCATION_RECEIPT_SCHEMA_VERSION = "trace-nlp-token-truncation-receipt/v1"
EXPECTED_ASPECT_IDS = frozenset(
    {
        "NLP_TITLE",
        "NLP_SUBJECT",
        "NLP_SOURCE_NARRATIVE",
        "NLP_OBJECT_SEMANTIC_COMPOSITE",
    }
)
LEXICAL_TOKEN_COUNT_METHOD = "TRACE_UNICODE_WORD_TOKENS_V1"


class CorpusBuildError(RuntimeError):
    """Raised when a field, identity, or local-artifact contract is violated."""


def lexical_token_count(text: str) -> int:
    """Count governed Unicode word tokens without importing the lexical index."""

    normalized = unicodedata.normalize("NFC", text).casefold()
    count = 0
    in_token = False
    for index, character in enumerate(normalized):
        admitted = unicodedata.category(character)[:1] in {"L", "M", "N"}
        if admitted:
            if not in_token:
                count += 1
                in_token = True
            continue
        if (
            character in {"'", "’", "-"}
            and in_token
            and index + 1 < len(normalized)
            and unicodedata.category(normalized[index + 1])[:1] in {"L", "M", "N"}
        ):
            continue
        in_token = False
    return count


def _context_by_id() -> dict[str, Mapping[str, Any]]:
    return {
        record["selectedRecord"]["surfaceId"]: record
        for record in load_context_records()
    }


def _aspect_from_text(
    *,
    aspect_id: str,
    field_id: str,
    original_text: str,
    source_artifact_sha256: str,
    include_text: bool,
    structured_labels_masked: bool = False,
    source_identity_masked: bool = False,
) -> dict[str, Any]:
    if aspect_id not in EXPECTED_ASPECT_IDS:
        raise CorpusBuildError(f"unexpected NLP aspect: {aspect_id}")
    decision = field_decision(field_id)
    if not decision.authoritative_for_aspect or decision.aspect_id != aspect_id:
        raise CorpusBuildError(f"field is not authoritative for aspect: {field_id}/{aspect_id}")
    if contains_private_token(original_text):
        raise CorpusBuildError("included source text contains a private identifier")
    normalized = normalize_text(original_text, remove_urls=True, reject_controls=True)
    script_state = classify_unicode(normalized.semantic_normalized)
    aspect: dict[str, Any] = {
        "aspectId": aspect_id,
        "sourceFieldIds": [field_id],
        "sourceFieldRoles": [decision.primary_role],
        "sourceArtifactSha256": source_artifact_sha256,
        "originalSourceHashes": [normalized.original_text_hash],
        "originalTextHash": normalized.original_text_hash,
        "semanticNormalizedHash": normalized.semantic_normalized_hash,
        "lexicalCasefoldedHash": normalized.lexical_casefolded_hash,
        "characterCount": len(normalized.semantic_normalized),
        "codePointCount": len(normalized.semantic_normalized),
        "tokenCount": lexical_token_count(normalized.lexical_casefolded),
        "tokenCountMethod": LEXICAL_TOKEN_COUNT_METHOD,
        "languageScriptState": script_state.primary_state,
        "scriptClasses": list(script_state.scripts),
        "modelInputTokenCap": effective_model_input_token_cap(aspect_id),
        "modelInputTruncationPolicy": "HEAD_AT_MODEL_INPUT_ONLY",
        "truncated": False,
        "boilerplateRemoved": False,
        "sourceIdentityMasked": source_identity_masked,
        "structuredLabelsMasked": structured_labels_masked,
        "urlRemovedCount": normalized.url_removed_count,
        "markupRemoved": normalized.markup_removed,
        "htmlEntityDecoded": normalized.html_entity_decoded,
        "publicSafe": decision.public_safe,
        "rightsSafe": decision.rights_safe,
        "historicalRelation": False,
        "semanticRelation": False,
        "probability": False,
    }
    if include_text:
        # Full originals remain local/untracked; their hash is always bound here.
        aspect["displayOriginal"] = normalized.display_original
        aspect["semanticNormalized"] = normalized.semantic_normalized
        aspect["lexicalCasefolded"] = normalized.lexical_casefolded
    return aspect


def _title_composite(title_aspect: Mapping[str, Any], *, include_text: bool) -> dict[str, Any]:
    composite = deepcopy(dict(title_aspect))
    composite["aspectId"] = "NLP_OBJECT_SEMANTIC_COMPOSITE"
    composite["compositePolicy"] = "TITLE_ONLY"
    composite["includedAspectIds"] = ["NLP_TITLE"]
    if set(composite["sourceFieldIds"]) != {"NLP-FIELD-001"}:
        raise CorpusBuildError("v1 object-semantic composite is not title-only")
    if not include_text:
        for key in ("displayOriginal", "semanticNormalized", "lexicalCasefolded"):
            composite.pop(key, None)
    return composite


def load_aspect_documents(*, include_text: bool = True) -> tuple[dict[str, Any], ...]:
    """Return the bounded 7,995-document public corpus without writing files."""

    context = _context_by_id()
    surfaces = {
        surface["surfaceId"]: surface for surface in load_public_canonical_surfaces()
    }
    if set(context) != set(surfaces) or len(context) != PUBLIC_OBJECT_COUNT:
        raise CorpusBuildError("Context and canonical public cohorts do not reconcile")

    documents: list[dict[str, Any]] = []
    for object_id in sorted(context):
        ensure_public_object_id(object_id)
        selected = context[object_id]["selectedRecord"]
        surface = surfaces[object_id]
        aspects: dict[str, dict[str, Any]] = {}

        title = _aspect_from_text(
            aspect_id="NLP_TITLE",
            field_id="NLP-FIELD-001",
            original_text=str(selected["title"]),
            source_artifact_sha256=EXPECTED_SHA256["contextRecords"],
            include_text=include_text,
        )
        aspects["NLP_TITLE"] = title
        aspects["NLP_OBJECT_SEMANTIC_COMPOSITE"] = _title_composite(
            title, include_text=include_text
        )

        subject = str(surface.get("sourceSubjects") or "").strip()
        if subject:
            try:
                aspects["NLP_SUBJECT"] = _aspect_from_text(
                    aspect_id="NLP_SUBJECT",
                    field_id="NLP-FIELD-003",
                    original_text=subject,
                    source_artifact_sha256=EXPECTED_SHA256["canonical"],
                    include_text=include_text,
                )
            except DisallowedControlError:
                # The field remains registered but the unsafe value is held out.
                pass

        narrative = str(surface.get("sourceDescription") or "").strip()
        if narrative:
            try:
                aspects["NLP_SOURCE_NARRATIVE"] = _aspect_from_text(
                    aspect_id="NLP_SOURCE_NARRATIVE",
                    field_id="NLP-FIELD-004",
                    original_text=narrative,
                    source_artifact_sha256=EXPECTED_SHA256["canonical"],
                    include_text=include_text,
                )
            except DisallowedControlError:
                pass

        if not set(aspects).issubset(EXPECTED_ASPECT_IDS):
            raise CorpusBuildError("document contains an unexpected aspect")
        document = {
            "schemaVersion": CORPUS_DOCUMENT_SCHEMA_VERSION,
            "publicObjectId": object_id,
            "objectId": object_id,
            "policyVersion": CORPUS_POLICY_VERSION,
            "policySha256": corpus_policy_sha256(),
            "fieldRegistryVersion": REGISTRY_VERSION,
            "fieldRegistrySha256": registry_sha256(),
            "normalizationVersion": NORMALIZATION_VERSION,
            "aspectDocumentVersion": ASPECT_DOCUMENT_VERSION,
            "aspects": {key: aspects[key] for key in sorted(aspects)},
            "historicalRelation": False,
            "semanticRelation": False,
            "probability": False,
        }
        documents.append(document)

    if len(documents) != PUBLIC_OBJECT_COUNT:
        raise CorpusBuildError("public NLP document count changed")
    identifiers = [document["publicObjectId"] for document in documents]
    if identifiers != sorted(identifiers) or len(set(identifiers)) != PUBLIC_OBJECT_COUNT:
        raise CorpusBuildError("public NLP document identities are not sorted and unique")
    return tuple(documents)


def iter_corpus_documents(*, include_text: bool = True) -> Iterator[dict[str, Any]]:
    yield from load_aspect_documents(include_text=include_text)


def _quantile_r7(values: Sequence[int], probability: float) -> int | float:
    ordered = sorted(values)
    if not ordered:
        return 0
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        value = float(ordered[lower])
    else:
        value = ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
    return int(value) if value.is_integer() else round(value, 6)


def _token_summary(lengths: Sequence[int], cap: int) -> dict[str, Any]:
    removed = [max(0, length - cap) for length in lengths]
    count_before = sum(lengths)
    count_removed = sum(removed)
    document_count = len(lengths)
    documents_truncated = sum(value > 0 for value in removed)
    return {
        "documentCount": document_count,
        "effectiveTokenCap": cap,
        "tokenCountP50": _quantile_r7(lengths, 0.50),
        "tokenCountP90": _quantile_r7(lengths, 0.90),
        "tokenCountP95": _quantile_r7(lengths, 0.95),
        "tokenCountP99": _quantile_r7(lengths, 0.99),
        "tokenCountMax": max(lengths, default=0),
        "tokenCountBefore": count_before,
        "tokenCountAfter": count_before - count_removed,
        "documentsTruncated": documents_truncated,
        "tokensRemoved": count_removed,
        "documentTruncationRate": (
            documents_truncated / document_count if document_count else 0.0
        ),
        "tokenRemovalRate": count_removed / count_before if count_before else 0.0,
    }


def head_truncate_model_input_tokens(
    tokens: Sequence[Any],
    *,
    aspect_id: str,
    semantic_normalized_hash: str,
    official_model_max_tokens: int | None = None,
) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """Return a non-mutating head slice and an explicit per-input receipt.

    ``tokens`` must already represent the final tokenizer-specific model input,
    including any required template and special tokens.  This function never
    changes the governed corpus document or its full normalized hashes.
    """

    if isinstance(tokens, (str, bytes, bytearray)) or not isinstance(tokens, Sequence):
        raise CorpusBuildError("model-input tokens must be a non-text sequence")
    if not isinstance(semantic_normalized_hash, str) or not re.fullmatch(
        r"[0-9a-f]{64}", semantic_normalized_hash
    ):
        raise CorpusBuildError("full semantic-normalized hash is missing or invalid")
    cap = effective_model_input_token_cap(aspect_id, official_model_max_tokens)
    original = tuple(tokens)
    model_input = original[:cap]
    removed = len(original) - len(model_input)
    receipt = {
        "schemaVersion": TOKEN_TRUNCATION_RECEIPT_SCHEMA_VERSION,
        "policyVersion": CORPUS_POLICY_VERSION,
        "policySha256": corpus_policy_sha256(),
        "aspectId": aspect_id,
        "governedAspectTokenCap": model_input_token_caps()[aspect_id],
        "officialModelMaxTokens": official_model_max_tokens,
        "effectiveTokenCap": cap,
        "semanticNormalizedHash": semantic_normalized_hash,
        "tokenCountBefore": len(original),
        "tokenCountAfter": len(model_input),
        "tokensRemoved": removed,
        "truncated": bool(removed),
        "truncationDirection": "HEAD",
        "applicationStage": "MODEL_INPUT_ONLY",
        "fullNormalizedHashPreserved": True,
        "corpusTextOverwritten": False,
    }
    return model_input, receipt


def build_tokenizer_length_census(
    *,
    tokenize_final_model_input: Callable[[str], Sequence[Any]],
    tokenizer_id: str,
    tokenizer_revision: str,
    documents: Iterable[Mapping[str, Any]] | None = None,
    prepare_model_input: Callable[[str, str], str] | None = None,
    official_model_max_tokens: int | None = None,
) -> dict[str, Any]:
    """Census final prepared input lengths without mutating corpus documents.

    The tokenizer callback must include any tokenizer-required special tokens in
    its returned sequence.  ``prepare_model_input`` receives ``(aspect_id,
    semantic_normalized)`` and may add a pinned model template before counting.
    """

    if not isinstance(tokenizer_id, str) or not tokenizer_id.strip():
        raise CorpusBuildError("tokenizer identity is required")
    if not isinstance(tokenizer_revision, str) or not tokenizer_revision.strip():
        raise CorpusBuildError("tokenizer revision is required")
    if not callable(tokenize_final_model_input):
        raise CorpusBuildError("tokenizer callback is required")
    if prepare_model_input is not None and not callable(prepare_model_input):
        raise CorpusBuildError("model-input preparation callback is invalid")

    corpus = tuple(documents) if documents is not None else load_aspect_documents(include_text=True)
    if len(corpus) > PUBLIC_OBJECT_COUNT:
        raise CorpusBuildError("tokenizer census exceeds the public object boundary")
    lengths_by_aspect: dict[str, list[int]] = {
        aspect_id: [] for aspect_id in sorted(EXPECTED_ASPECT_IDS)
    }
    receipt_material: list[dict[str, Any]] = []
    object_ids: list[str] = []
    for document in corpus:
        if not isinstance(document, Mapping):
            raise CorpusBuildError("tokenizer census documents must be mappings")
        object_id = ensure_public_object_id(document.get("publicObjectId"))
        if document.get("objectId") != object_id:
            raise CorpusBuildError("tokenizer census received conflicting object identity")
        required_pins = {
            "policyVersion": CORPUS_POLICY_VERSION,
            "policySha256": corpus_policy_sha256(),
            "fieldRegistryVersion": REGISTRY_VERSION,
            "fieldRegistrySha256": registry_sha256(),
            "normalizationVersion": NORMALIZATION_VERSION,
        }
        if any(document.get(key) != value for key, value in required_pins.items()):
            raise CorpusBuildError("tokenizer census received a stale corpus governance pin")
        object_ids.append(object_id)
        aspects = document.get("aspects")
        if not isinstance(aspects, Mapping):
            raise CorpusBuildError("tokenizer census requires aspect mappings")
        for aspect_id, aspect in sorted(aspects.items()):
            if aspect_id not in EXPECTED_ASPECT_IDS or not isinstance(aspect, Mapping):
                raise CorpusBuildError("tokenizer census received an unexpected aspect")
            if aspect.get("modelInputTokenCap") != model_input_token_caps()[aspect_id]:
                raise CorpusBuildError("tokenizer census received a stale aspect token cap")
            if aspect.get("truncated") is not False:
                raise CorpusBuildError("tokenizer census cannot consume a truncated base corpus")
            text = aspect.get("semanticNormalized")
            semantic_hash = aspect.get("semanticNormalizedHash")
            if not isinstance(text, str) or not text:
                raise CorpusBuildError("tokenizer census requires include_text=True documents")
            if (
                not isinstance(semantic_hash, str)
                or not re.fullmatch(r"[0-9a-f]{64}", semantic_hash)
                or sha256_text(text) != semantic_hash
            ):
                raise CorpusBuildError("tokenizer census received an invalid semantic hash")
            prepared = prepare_model_input(aspect_id, text) if prepare_model_input else text
            if not isinstance(prepared, str) or not prepared:
                raise CorpusBuildError("prepared model input must be non-empty text")
            token_values = tokenize_final_model_input(prepared)
            if isinstance(token_values, (str, bytes, bytearray)) or not isinstance(
                token_values, Sequence
            ):
                raise CorpusBuildError("tokenizer callback must return a non-text sequence")
            length = len(token_values)
            cap = effective_model_input_token_cap(aspect_id, official_model_max_tokens)
            lengths_by_aspect[aspect_id].append(length)
            receipt_material.append(
                {
                    "publicObjectId": object_id,
                    "aspectId": aspect_id,
                    "semanticNormalizedHash": semantic_hash,
                    "preparedModelInputHash": sha256_text(prepared),
                    "tokenCountBefore": length,
                    "tokenCountAfter": min(length, cap),
                    "tokensRemoved": max(0, length - cap),
                    "effectiveTokenCap": cap,
                }
            )
    if object_ids != sorted(object_ids) or len(object_ids) != len(set(object_ids)):
        raise CorpusBuildError("tokenizer census inputs must be sorted unique public objects")

    by_aspect = {
        aspect_id: _token_summary(
            lengths_by_aspect[aspect_id],
            effective_model_input_token_cap(aspect_id, official_model_max_tokens),
        )
        for aspect_id in sorted(EXPECTED_ASPECT_IDS)
    }
    all_lengths = [
        length for aspect_id in sorted(lengths_by_aspect) for length in lengths_by_aspect[aspect_id]
    ]
    total_before = sum(row["tokenCountBefore"] for row in receipt_material)
    total_after = sum(row["tokenCountAfter"] for row in receipt_material)
    total_removed = total_before - total_after
    documents_truncated = sum(row["tokensRemoved"] > 0 for row in receipt_material)
    return {
        "schemaVersion": TOKENIZER_LENGTH_CENSUS_SCHEMA_VERSION,
        "policyVersion": CORPUS_POLICY_VERSION,
        "policySha256": corpus_policy_sha256(),
        "tokenizerId": tokenizer_id.strip(),
        "tokenizerRevision": tokenizer_revision.strip(),
        "officialModelMaxTokens": official_model_max_tokens,
        "governedAspectTokenCaps": model_input_token_caps(),
        "effectiveAspectTokenCaps": {
            aspect_id: effective_model_input_token_cap(aspect_id, official_model_max_tokens)
            for aspect_id in sorted(EXPECTED_ASPECT_IDS)
        },
        "publicObjectCount": len(object_ids),
        "documentCount": len(receipt_material),
        "tokenCountP50": _quantile_r7(all_lengths, 0.50),
        "tokenCountP95": _quantile_r7(all_lengths, 0.95),
        "tokenCountP99": _quantile_r7(all_lengths, 0.99),
        "tokenCountMax": max(all_lengths, default=0),
        "tokenCountBefore": total_before,
        "tokenCountAfter": total_after,
        "documentsTruncated": documents_truncated,
        "tokensRemoved": total_removed,
        "documentTruncationRate": (
            documents_truncated / len(receipt_material) if receipt_material else 0.0
        ),
        "tokenRemovalRate": total_removed / total_before if total_before else 0.0,
        "byAspect": by_aspect,
        "truncationDirection": "HEAD",
        "applicationStage": "MODEL_INPUT_ONLY",
        "fullNormalizedHashesPreserved": True,
        "corpusTextOverwritten": False,
        "recordLengthReceiptSha256": sha256_json(receipt_material),
    }


def _document_receipt(document: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "publicObjectId": document["publicObjectId"],
        "aspects": {
            aspect_id: {
                "originalTextHash": aspect["originalTextHash"],
                "semanticNormalizedHash": aspect["semanticNormalizedHash"],
                "lexicalCasefoldedHash": aspect["lexicalCasefoldedHash"],
                "characterCount": aspect["characterCount"],
                "languageScriptState": aspect["languageScriptState"],
                "modelInputTokenCap": aspect["modelInputTokenCap"],
            }
            for aspect_id, aspect in sorted(document["aspects"].items())
        },
    }


def _token_count_receipt(document: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "publicObjectId": document["publicObjectId"],
        "aspects": {
            aspect_id: {
                "lexicalCasefoldedHash": aspect["lexicalCasefoldedHash"],
                "tokenCount": aspect["tokenCount"],
                "tokenCountMethod": aspect["tokenCountMethod"],
            }
            for aspect_id, aspect in sorted(document["aspects"].items())
        },
    }


def corpus_identity_sha256(documents: Iterable[Mapping[str, Any]]) -> str:
    """Return the frozen lexical corpus identity (intentionally excludes counts)."""

    ordered = sorted(tuple(documents), key=lambda row: str(row["publicObjectId"]))
    material = {
        "schemaVersion": CORPUS_BUNDLE_SCHEMA_VERSION,
        "policyVersion": CORPUS_POLICY_VERSION,
        "policySha256": corpus_policy_sha256(),
        "fieldRegistryVersion": REGISTRY_VERSION,
        "fieldRegistrySha256": registry_sha256(),
        "normalizationVersion": NORMALIZATION_VERSION,
        "objectIds": [document["publicObjectId"] for document in ordered],
        "documents": [
            {
                "objectId": document["publicObjectId"],
                "aspects": {
                    aspect_id: {
                        "originalTextHash": aspect["originalTextHash"],
                        "semanticNormalizedHash": aspect["semanticNormalizedHash"],
                        "lexicalCasefoldedHash": aspect["lexicalCasefoldedHash"],
                        "sourceFieldIds": list(aspect["sourceFieldIds"]),
                        "sourceFieldRoles": list(aspect["sourceFieldRoles"]),
                    }
                    for aspect_id, aspect in sorted(document["aspects"].items())
                },
            }
            for document in ordered
        ],
    }
    return sha256_json(material)


def build_corpus_bundle(*, include_text: bool = True) -> dict[str, Any]:
    documents = load_aspect_documents(include_text=include_text)
    aspect_counts: dict[str, int] = {aspect_id: 0 for aspect_id in EXPECTED_ASPECT_IDS}
    url_removed = 0
    for document in documents:
        for aspect_id, aspect in document["aspects"].items():
            aspect_counts[aspect_id] += 1
            url_removed += int(aspect["urlRemovedCount"])
    receipts = [_document_receipt(document) for document in documents]
    token_count_receipts = [_token_count_receipt(document) for document in documents]
    return {
        "schemaVersion": CORPUS_BUNDLE_SCHEMA_VERSION,
        "policyVersion": CORPUS_POLICY_VERSION,
        "policySha256": corpus_policy_sha256(),
        "fieldRegistryVersion": REGISTRY_VERSION,
        "fieldRegistrySha256": registry_sha256(),
        "normalizationVersion": NORMALIZATION_VERSION,
        "boundary": {
            "canonicalObjectCount": CANONICAL_OBJECT_COUNT,
            "publicObjectCount": PUBLIC_OBJECT_COUNT,
            "heldObjectCount": HELD_OBJECT_COUNT,
            "heldObjectsIncluded": 0,
        },
        "aspectDocumentCounts": {key: aspect_counts[key] for key in sorted(aspect_counts)},
        "urlRemovedCount": url_removed,
        "documentReceiptSha256": sha256_json(receipts),
        # Token counts are a separately bound deterministic receipt so adding the
        # mandatory per-document field does not redefine the frozen corpus-text
        # identity or the pre-existing documentReceiptSha256 contract.
        "tokenCountMethod": LEXICAL_TOKEN_COUNT_METHOD,
        "tokenCountReceiptSha256": sha256_json(token_count_receipts),
        "corpusSha256": corpus_identity_sha256(documents),
        "documents": list(documents),
    }


def _assert_local_output_path(output_dir: Path) -> Path:
    resolved = output_dir.expanduser().resolve()
    root = Path(__file__).resolve().parents[2]
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        # Explicit temporary/external directories are local research outputs too.
        return resolved
    if not relative.parts or relative.parts[0] != ".local":
        raise CorpusBuildError("full corpus output inside the repository must be under .local/")
    return resolved


def build_local_documents(output_dir: str | Path, *, include_text: bool = True) -> dict[str, Any]:
    """Write a local-only JSONL corpus; callers must never stage this output."""

    target = _assert_local_output_path(Path(output_dir))
    target.mkdir(parents=True, exist_ok=True)
    bundle = build_corpus_bundle(include_text=include_text)
    documents_path = target / "documents.jsonl"
    with documents_path.open("w", encoding="utf-8", newline="\n") as handle:
        for document in bundle["documents"]:
            handle.write(
                json.dumps(
                    document,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
                + "\n"
            )
    manifest = {key: value for key, value in bundle.items() if key != "documents"}
    manifest["documentsPath"] = documents_path.name
    manifest["documentsSha256"] = __import__("hashlib").sha256(
        documents_path.read_bytes()
    ).hexdigest()
    manifest_path = target / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def self_test() -> dict[str, Any]:
    first = build_corpus_bundle(include_text=False)
    second = build_corpus_bundle(include_text=False)
    for receipt_key in (
        "documentReceiptSha256",
        "tokenCountReceiptSha256",
        "corpusSha256",
    ):
        if first[receipt_key] != second[receipt_key]:
            raise AssertionError(f"corpus {receipt_key} is not deterministic")
    expected = {
        "NLP_OBJECT_SEMANTIC_COMPOSITE": PUBLIC_OBJECT_COUNT,
        "NLP_SOURCE_NARRATIVE": 7_431,
        "NLP_SUBJECT": 7_838,
        "NLP_TITLE": PUBLIC_OBJECT_COUNT,
    }
    if first["aspectDocumentCounts"] != expected:
        raise AssertionError(
            f"aspect coverage changed: {first['aspectDocumentCounts']} != {expected}"
        )
    if first["boundary"]["heldObjectsIncluded"] != 0:
        raise AssertionError("held objects entered the corpus")
    for document in first["documents"]:
        for aspect_id, aspect in document["aspects"].items():
            if aspect["modelInputTokenCap"] != effective_model_input_token_cap(aspect_id):
                raise AssertionError("aspect model-input token cap differs from policy")
            if aspect["tokenCount"] < 1 or aspect["tokenCountMethod"] != LEXICAL_TOKEN_COUNT_METHOD:
                raise AssertionError("aspect lexical token-count contract changed")
            if aspect["truncated"] is not False:
                raise AssertionError("base corpus was silently truncated")
    head, truncation_receipt = head_truncate_model_input_tokens(
        tuple(range(300)),
        aspect_id="NLP_TITLE",
        semantic_normalized_hash="a" * 64,
    )
    if (
        len(head) != 256
        or head != tuple(range(256))
        or truncation_receipt["tokensRemoved"] != 44
        or truncation_receipt["corpusTextOverwritten"] is not False
    ):
        raise AssertionError("head-only model-input truncation contract changed")
    sample_id = first["documents"][0]["publicObjectId"]
    sample_aspect = _aspect_from_text(
        aspect_id="NLP_TITLE",
        field_id="NLP-FIELD-001",
        original_text="one two three",
        source_artifact_sha256=EXPECTED_SHA256["contextRecords"],
        include_text=True,
    )
    sample_document = {
        "publicObjectId": sample_id,
        "objectId": sample_id,
        "policyVersion": CORPUS_POLICY_VERSION,
        "policySha256": corpus_policy_sha256(),
        "fieldRegistryVersion": REGISTRY_VERSION,
        "fieldRegistrySha256": registry_sha256(),
        "normalizationVersion": NORMALIZATION_VERSION,
        "aspects": {"NLP_TITLE": sample_aspect},
    }
    census = build_tokenizer_length_census(
        tokenize_final_model_input=lambda text: tuple(text.split()),
        tokenizer_id="SELF_TEST_WHITESPACE",
        tokenizer_revision="immutable-self-test-v1",
        documents=(sample_document,),
        official_model_max_tokens=2,
    )
    if (
        census["documentCount"] != 1
        or census["tokenCountBefore"] != 3
        or census["tokenCountAfter"] != 2
        or census["documentsTruncated"] != 1
        or census["tokensRemoved"] != 1
        or census["documentTruncationRate"] != 1.0
        or census["tokenRemovalRate"] != 1 / 3
        or census["corpusTextOverwritten"] is not False
    ):
        raise AssertionError("tokenizer-specific length census contract changed")
    return {
        "status": "PASS",
        "publicDocumentCount": len(first["documents"]),
        "aspectDocumentCounts": first["aspectDocumentCounts"],
        "documentReceiptSha256": first["documentReceiptSha256"],
        "tokenCountReceiptSha256": first["tokenCountReceiptSha256"],
        "corpusSha256": first["corpusSha256"],
        "urlRemovedCount": first["urlRemovedCount"],
        "policySha256": first["policySha256"],
        "fieldRegistrySha256": first["fieldRegistrySha256"],
        "modelInputTokenCaps": model_input_token_caps(),
        "headTruncationSelfTestTokensRemoved": truncation_receipt["tokensRemoved"],
        "tokenizerLengthCensusSelfTestSha256": census["recordLengthReceiptSha256"],
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), ensure_ascii=False, sort_keys=True))
