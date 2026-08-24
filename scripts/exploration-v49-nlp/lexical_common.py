#!/usr/bin/env python3
"""Shared fail-closed contracts for isolated Round 7 lexical research.

This module consumes the governed, in-memory corpus bundle.  It never writes
text, rankings, indexes, or matrices and it never imports the frozen Search
implementation.  All result flags deliberately preserve the Round 7
scientific interpretation boundary.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
import sys
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np
from scipy import sparse

import common as governance_common
import field_governance


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
SOURCE_COMMIT = "580587a74f400d8a04d995937f4efb31e6621dd8"
CORPUS_SCHEMA_VERSION = "trace-nlp-corpus-bundle/v1"
CORPUS_POLICY_VERSION = "trace-nlp-corpus-v1"
FIELD_REGISTRY_VERSION = "trace-nlp-text-field-registry-v1"
NORMALIZATION_VERSION = "trace-nlp-normalization-v1"
LEXICAL_RESULT_SCHEMA_VERSION = "trace-nlp-lexical-top-k/v1"
IMPLEMENTATION_VERSION = "trace-nlp-lexical-common-2026-08-24"

CANONICAL_OBJECT_COUNT = 15_923
PUBLIC_OBJECT_COUNT = 7_995
HELD_OBJECT_COUNT = 7_928
DEFAULT_TOP_K = 50
ALLOWED_ASPECTS = frozenset(
    {
        "NLP_TITLE",
        "NLP_SUBJECT",
        "NLP_SOURCE_NARRATIVE",
        "NLP_OBJECT_SEMANTIC_COMPOSITE",
    }
)
PUBLIC_ID_RE = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
PRIVATE_TEXT_RE = re.compile(
    r"(?:\bFOL-|\bTRN-OBJ-|\bTRTREE|\bTRB\d|https?://|file://)",
    re.IGNORECASE,
)
LEXICAL_TOKEN_COUNT_METHOD = "TRACE_UNICODE_WORD_TOKENS_V1"
FROZEN_DOCUMENT_RECEIPT_SHA256 = "69aa8f290f7390bdb8ce7c0a3cf4ecdfb7426c908804bf48f9126c0eec4fdac8"
FROZEN_TOKEN_COUNT_RECEIPT_SHA256 = "511eee824342ded9c6ac4606af3f99dea79844663ebd550cbbca2ac2ba2cecca"
FROZEN_CORPUS_SHA256 = "7cde5cfdcf0a0bfd4762f9e23c3b50287a0b9071cbf0bd21102bca4ae2ee024c"
ASPECT_SOURCE_CONTRACT = {
    "NLP_TITLE": (("NLP-FIELD-001",), ("OBJECT_TITLE",)),
    "NLP_SUBJECT": (("NLP-FIELD-003",), ("OBJECT_SUBJECT_TERMS",)),
    "NLP_SOURCE_NARRATIVE": (("NLP-FIELD-004",), ("SOURCE_NARRATIVE",)),
    "NLP_OBJECT_SEMANTIC_COMPOSITE": (("NLP-FIELD-001",), ("OBJECT_TITLE",)),
}


class LexicalContractError(RuntimeError):
    """Raised when governed corpus or bounded-ranking input is invalid."""


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


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def _required_sha(value: Any, name: str) -> str:
    normalized = str(value or "")
    if not SHA256_RE.fullmatch(normalized):
        raise LexicalContractError(f"{name} is not a SHA-256 digest")
    return normalized


def quantile_r7(values: Iterable[float | int], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


@dataclass(frozen=True)
class AspectDocument:
    aspect_id: str
    source_field_ids: tuple[str, ...]
    source_field_roles: tuple[str, ...]
    original_source_hashes: tuple[str, ...]
    original_text_hash: str
    display_original: str
    semantic_normalized_hash: str
    lexical_casefolded_hash: str
    semantic_normalized: str
    lexical_casefolded: str
    character_count: int
    token_count: int
    token_count_method: str
    language_script_state: str
    truncated: bool
    boilerplate_removed: bool
    source_identity_masked: bool
    structured_labels_masked: bool
    url_removed_count: int


@dataclass(frozen=True)
class LexicalDocument:
    object_id: str
    policy_version: str
    policy_sha256: str
    field_registry_version: str
    field_registry_sha256: str
    normalization_version: str
    aspects: Mapping[str, AspectDocument]


@dataclass(frozen=True)
class CorpusBundle:
    documents: tuple[LexicalDocument, ...]
    object_ids: tuple[str, ...]
    documents_by_id: Mapping[str, LexicalDocument]
    policy_version: str
    policy_sha256: str
    field_registry_version: str
    field_registry_sha256: str
    normalization_version: str
    corpus_sha256: str
    canonical_object_count: int
    public_object_count: int
    held_object_count: int


@dataclass(frozen=True)
class LexicalSpec:
    method_id: str
    implementation_version: str
    aspect_ids: tuple[str, ...]
    field_weights: tuple[tuple[str, float], ...]
    input_variant: str = "ORIGINAL_APPROVED"
    analyzer: str = "WORD_UNIGRAM"
    ngram_min: int = 1
    ngram_max: int = 1
    sublinear_tf: bool = True
    idf_mode: str = "SMOOTHED"
    fixed_field_denominator: bool = True
    k1: float = 1.2
    b_by_field: tuple[tuple[str, float], ...] = ()

    def parameters(self) -> dict[str, Any]:
        return {
            "aspectIds": list(self.aspect_ids),
            "fieldWeights": dict(self.field_weights),
            "inputVariant": self.input_variant,
            "analyzer": self.analyzer,
            "ngramRange": [self.ngram_min, self.ngram_max],
            "sublinearTf": self.sublinear_tf,
            "idfMode": self.idf_mode,
            "fixedFieldDenominator": self.fixed_field_denominator,
            "k1": self.k1,
            "bByField": dict(self.b_by_field),
        }


@dataclass(frozen=True)
class SparseFieldIndex:
    spec: LexicalSpec
    object_ids: tuple[str, ...]
    object_ordinals: Mapping[str, int]
    matrices: Mapping[str, sparse.csr_matrix]
    vocabularies: Mapping[str, tuple[str, ...]]
    document_frequencies: Mapping[str, np.ndarray]
    field_nonempty: Mapping[str, np.ndarray]
    index_sha256: str
    index_bytes: int
    build_ms: float


def _coerce_aspect(raw: Mapping[str, Any], expected_id: str) -> AspectDocument:
    aspect_id = str(raw.get("aspectId", ""))
    if aspect_id != expected_id or aspect_id not in ALLOWED_ASPECTS:
        raise LexicalContractError("corpus aspect identity is missing or unsupported")
    source_hashes = tuple(str(value) for value in raw.get("originalSourceHashes", ()))
    if not source_hashes or any(not SHA256_RE.fullmatch(value) for value in source_hashes):
        raise LexicalContractError("aspect original source hashes are absent or invalid")
    semantic = raw.get("semanticNormalized")
    lexical = raw.get("lexicalCasefolded")
    display_original = raw.get("displayOriginal")
    if (
        not isinstance(display_original, str)
        or not isinstance(semantic, str)
        or not isinstance(lexical, str)
    ):
        raise LexicalContractError("governed corpus adapter requires include_text=True")
    if UUID_RE.search(semantic) or UUID_RE.search(lexical):
        raise LexicalContractError("internal UUID entered a lexical aspect")
    if PRIVATE_TEXT_RE.search(semantic) or PRIVATE_TEXT_RE.search(lexical):
        raise LexicalContractError("URL or private control identity entered a lexical aspect")
    character_count = raw.get("characterCount")
    if isinstance(character_count, bool) or not isinstance(character_count, int) or character_count < 0:
        raise LexicalContractError("aspect character count is invalid")
    if character_count != len(semantic):
        raise LexicalContractError("aspect character count differs from semantic text")
    if unicodedata.normalize("NFC", semantic) != semantic:
        raise LexicalContractError("semantic text is not NFC")
    if lexical != semantic.casefold():
        raise LexicalContractError("lexical casefolded text differs from the governed semantic view")
    semantic_hash = _required_sha(raw.get("semanticNormalizedHash"), "semanticNormalizedHash")
    lexical_hash = _required_sha(raw.get("lexicalCasefoldedHash"), "lexicalCasefoldedHash")
    if semantic_hash != sha256_bytes(semantic.encode("utf-8")):
        raise LexicalContractError("semanticNormalizedHash does not match semantic text")
    if lexical_hash != sha256_bytes(lexical.encode("utf-8")):
        raise LexicalContractError("lexicalCasefoldedHash does not match lexical text")
    original_text_hash = _required_sha(raw.get("originalTextHash"), "originalTextHash")
    if original_text_hash != sha256_bytes(display_original.encode("utf-8")):
        raise LexicalContractError("originalTextHash does not match DISPLAY_ORIGINAL")
    if original_text_hash not in source_hashes:
        raise LexicalContractError("original source hashes do not bind DISPLAY_ORIGINAL")
    token_count = raw.get("tokenCount")
    if (
        isinstance(token_count, bool)
        or not isinstance(token_count, int)
        or token_count != len(word_tokens(lexical))
        or raw.get("tokenCountMethod") != LEXICAL_TOKEN_COUNT_METHOD
    ):
        raise LexicalContractError("aspect lexical token count is absent or inconsistent")
    source_field_ids = tuple(str(value) for value in raw.get("sourceFieldIds", ()))
    source_field_roles = tuple(str(value) for value in raw.get("sourceFieldRoles", ()))
    if (source_field_ids, source_field_roles) != ASPECT_SOURCE_CONTRACT[aspect_id]:
        raise LexicalContractError("aspect source field governance differs from its frozen contract")
    boolean_fields = {
        name: raw.get(name)
        for name in (
            "truncated",
            "boilerplateRemoved",
            "sourceIdentityMasked",
            "structuredLabelsMasked",
        )
    }
    if any(not isinstance(value, bool) for value in boolean_fields.values()):
        raise LexicalContractError("aspect transformation flags must be booleans")
    if boolean_fields["truncated"] or boolean_fields["boilerplateRemoved"]:
        raise LexicalContractError("base corpus cannot be silently truncated or boilerplate-modified")
    url_count = raw.get("urlRemovedCount")
    if isinstance(url_count, bool) or not isinstance(url_count, int) or url_count < 0:
        raise LexicalContractError("aspect URL-removal count is invalid")
    return AspectDocument(
        aspect_id=aspect_id,
        source_field_ids=source_field_ids,
        source_field_roles=source_field_roles,
        original_source_hashes=source_hashes,
        original_text_hash=original_text_hash,
        display_original=display_original,
        semantic_normalized_hash=semantic_hash,
        lexical_casefolded_hash=lexical_hash,
        semantic_normalized=semantic,
        lexical_casefolded=lexical,
        character_count=character_count,
        token_count=token_count,
        token_count_method=LEXICAL_TOKEN_COUNT_METHOD,
        language_script_state=str(raw.get("languageScriptState", "")),
        truncated=boolean_fields["truncated"],
        boilerplate_removed=boolean_fields["boilerplateRemoved"],
        source_identity_masked=boolean_fields["sourceIdentityMasked"],
        structured_labels_masked=boolean_fields["structuredLabelsMasked"],
        url_removed_count=url_count,
    )


def coerce_corpus_bundle(
    payload: Mapping[str, Any],
    *,
    require_all_aspects: bool = False,
) -> CorpusBundle:
    """Validate and freeze a corpus-builder payload without retaining raw mappings."""

    if payload.get("schemaVersion") != CORPUS_SCHEMA_VERSION:
        raise LexicalContractError("corpus schema version changed")
    if payload.get("policyVersion") != CORPUS_POLICY_VERSION:
        raise LexicalContractError("corpus policy version changed")
    if payload.get("fieldRegistryVersion") != FIELD_REGISTRY_VERSION:
        raise LexicalContractError("text-field registry version changed")
    if payload.get("normalizationVersion") != NORMALIZATION_VERSION:
        raise LexicalContractError("normalization version changed")
    policy_sha = _required_sha(payload.get("policySha256"), "policySha256")
    registry_sha = _required_sha(payload.get("fieldRegistrySha256"), "fieldRegistrySha256")
    if policy_sha != field_governance.corpus_policy_sha256():
        raise LexicalContractError("corpus policy hash differs from the frozen registry")
    if registry_sha != field_governance.registry_sha256():
        raise LexicalContractError("text-field registry hash differs from the frozen registry")
    if _required_sha(
        payload.get("documentReceiptSha256"), "documentReceiptSha256"
    ) != FROZEN_DOCUMENT_RECEIPT_SHA256:
        raise LexicalContractError("document receipt differs from the frozen governed corpus")
    declared_corpus_sha = _required_sha(payload.get("corpusSha256"), "corpusSha256")
    if declared_corpus_sha != FROZEN_CORPUS_SHA256:
        raise LexicalContractError("corpus receipt differs from the frozen governed corpus")
    boundary = payload.get("boundary")
    if not isinstance(boundary, Mapping):
        raise LexicalContractError("corpus boundary receipt is missing")
    expected_boundary = {
        "canonicalObjectCount": CANONICAL_OBJECT_COUNT,
        "publicObjectCount": PUBLIC_OBJECT_COUNT,
        "heldObjectCount": HELD_OBJECT_COUNT,
        "heldObjectsIncluded": 0,
    }
    if any(boundary.get(key) != value for key, value in expected_boundary.items()):
        raise LexicalContractError("corpus public/held boundary changed")
    raw_documents = payload.get("documents")
    if not isinstance(raw_documents, list) or len(raw_documents) != PUBLIC_OBJECT_COUNT:
        raise LexicalContractError("corpus document count changed")
    documents: list[LexicalDocument] = []
    expected_aspects = ALLOWED_ASPECTS if require_all_aspects else frozenset()
    for raw_document in raw_documents:
        if not isinstance(raw_document, Mapping):
            raise LexicalContractError("corpus document is not a mapping")
        object_id = str(raw_document.get("publicObjectId", ""))
        if not PUBLIC_ID_RE.fullmatch(object_id) or raw_document.get("objectId") != object_id:
            raise LexicalContractError("corpus contains an invalid or aliased public object ID")
        if (
            raw_document.get("policyVersion") != CORPUS_POLICY_VERSION
            or raw_document.get("policySha256") != policy_sha
            or raw_document.get("fieldRegistryVersion") != FIELD_REGISTRY_VERSION
            or raw_document.get("fieldRegistrySha256") != registry_sha
            or raw_document.get("normalizationVersion") != NORMALIZATION_VERSION
        ):
            raise LexicalContractError("document governance pins differ from bundle pins")
        raw_aspects = raw_document.get("aspects")
        if isinstance(raw_aspects, list):
            aspect_map = {str(row.get("aspectId", "")): row for row in raw_aspects if isinstance(row, Mapping)}
            if len(aspect_map) != len(raw_aspects):
                raise LexicalContractError("corpus aspect list has duplicates or invalid entries")
        elif isinstance(raw_aspects, Mapping):
            aspect_map = {str(key): value for key, value in raw_aspects.items()}
        else:
            raise LexicalContractError("corpus aspects are absent")
        if set(aspect_map) - ALLOWED_ASPECTS:
            raise LexicalContractError("corpus contains an ungoverned text aspect")
        if require_all_aspects and set(aspect_map) != expected_aspects:
            raise LexicalContractError("corpus does not expose all four frozen aspect contracts")
        aspects = {
            aspect_id: _coerce_aspect(raw, aspect_id)
            for aspect_id, raw in sorted(aspect_map.items())
            if isinstance(raw, Mapping)
        }
        title = aspects.get("NLP_TITLE")
        composite = aspects.get("NLP_OBJECT_SEMANTIC_COMPOSITE")
        if title is None or composite is None:
            raise LexicalContractError("title and title-only semantic composite are required")
        if (
            title.semantic_normalized != composite.semantic_normalized
            or title.lexical_casefolded != composite.lexical_casefolded
            or title.semantic_normalized_hash != composite.semantic_normalized_hash
            or title.lexical_casefolded_hash != composite.lexical_casefolded_hash
        ):
            raise LexicalContractError("v1 object-semantic composite is not an exact title copy")
        documents.append(
            LexicalDocument(
                object_id=object_id,
                policy_version=CORPUS_POLICY_VERSION,
                policy_sha256=policy_sha,
                field_registry_version=FIELD_REGISTRY_VERSION,
                field_registry_sha256=registry_sha,
                normalization_version=NORMALIZATION_VERSION,
                aspects=aspects,
            )
        )
    documents.sort(key=lambda value: value.object_id)
    object_ids = tuple(value.object_id for value in documents)
    if len(set(object_ids)) != PUBLIC_OBJECT_COUNT:
        raise LexicalContractError("corpus public identities are not unique")
    if object_ids != governance_common.load_public_ids():
        raise LexicalContractError("corpus identities differ from the authoritative public ledger")
    if payload.get("tokenCountMethod") != LEXICAL_TOKEN_COUNT_METHOD:
        raise LexicalContractError("corpus lexical token-count method changed")
    token_count_material = [
        {
            "publicObjectId": document.object_id,
            "aspects": {
                aspect_id: {
                    "lexicalCasefoldedHash": aspect.lexical_casefolded_hash,
                    "tokenCount": aspect.token_count,
                    "tokenCountMethod": aspect.token_count_method,
                }
                for aspect_id, aspect in sorted(document.aspects.items())
            },
        }
        for document in documents
    ]
    declared_token_count_sha = _required_sha(
        payload.get("tokenCountReceiptSha256"), "tokenCountReceiptSha256"
    )
    if (
        declared_token_count_sha != sha256_json(token_count_material)
        or declared_token_count_sha != FROZEN_TOKEN_COUNT_RECEIPT_SHA256
    ):
        raise LexicalContractError("token-count receipt differs from governed aspect documents")
    material = {
        "schemaVersion": CORPUS_SCHEMA_VERSION,
        "policyVersion": CORPUS_POLICY_VERSION,
        "policySha256": policy_sha,
        "fieldRegistryVersion": FIELD_REGISTRY_VERSION,
        "fieldRegistrySha256": registry_sha,
        "normalizationVersion": NORMALIZATION_VERSION,
        "objectIds": object_ids,
        "documents": [
            {
                "objectId": document.object_id,
                "aspects": {
                    aspect_id: {
                        "originalTextHash": aspect.original_text_hash,
                        "semanticNormalizedHash": aspect.semantic_normalized_hash,
                        "lexicalCasefoldedHash": aspect.lexical_casefolded_hash,
                        "sourceFieldIds": aspect.source_field_ids,
                        "sourceFieldRoles": aspect.source_field_roles,
                    }
                    for aspect_id, aspect in sorted(document.aspects.items())
                },
            }
            for document in documents
        ],
    }
    corpus_sha = sha256_json(material)
    if declared_corpus_sha != corpus_sha:
        raise LexicalContractError("declared corpus SHA-256 differs from governed documents")
    return CorpusBundle(
        documents=tuple(documents),
        object_ids=object_ids,
        documents_by_id={value.object_id: value for value in documents},
        policy_version=CORPUS_POLICY_VERSION,
        policy_sha256=policy_sha,
        field_registry_version=FIELD_REGISTRY_VERSION,
        field_registry_sha256=registry_sha,
        normalization_version=NORMALIZATION_VERSION,
        corpus_sha256=corpus_sha,
        canonical_object_count=int(boundary["canonicalObjectCount"]),
        public_object_count=PUBLIC_OBJECT_COUNT,
        held_object_count=HELD_OBJECT_COUNT,
    )


def load_governed_corpus() -> CorpusBundle:
    """Load text only through the centrally governed corpus-builder API."""

    try:
        import corpus_builder  # type: ignore
    except ImportError as error:
        raise LexicalContractError("governed corpus_builder API is unavailable") from error
    builder = getattr(corpus_builder, "build_corpus_bundle", None)
    if not callable(builder):
        raise LexicalContractError("corpus_builder.build_corpus_bundle is unavailable")
    payload = builder(include_text=True)
    if not isinstance(payload, Mapping):
        raise LexicalContractError("corpus builder returned a non-mapping payload")
    return coerce_corpus_bundle(payload)


def _load_round6_common() -> Any:
    path = ROOT / "scripts/exploration-v49-similarity/common.py"
    spec = importlib.util.spec_from_file_location("trace_round6_common_for_nlp", path)
    if spec is None or spec.loader is None:
        raise LexicalContractError("Round 6 frozen input loader is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_structured_public_records() -> Mapping[str, Mapping[str, Any]]:
    """Return Round 6 public-only structured records for diagnostics only."""

    module = _load_round6_common()
    loaded = module.load_normalized_public_records()
    rows = loaded.get("records")
    if not isinstance(rows, list) or len(rows) != PUBLIC_OBJECT_COUNT:
        raise LexicalContractError("Round 6 structured cohort changed")
    result = {str(row.get("objectId", "")): row for row in rows if isinstance(row, Mapping)}
    if tuple(sorted(result)) != tuple(str(row["objectId"]) for row in rows):
        raise LexicalContractError("Round 6 structured identities are not sorted and unique")
    return result


def validate_spec(spec: LexicalSpec) -> None:
    if not spec.method_id or not spec.implementation_version:
        raise LexicalContractError("lexical method identity/version is blank")
    if not spec.aspect_ids or len(set(spec.aspect_ids)) != len(spec.aspect_ids):
        raise LexicalContractError("lexical aspect list is empty or duplicated")
    if set(spec.aspect_ids) - ALLOWED_ASPECTS:
        raise LexicalContractError("lexical method references an ungoverned aspect")
    weights = dict(spec.field_weights)
    if set(weights) != set(spec.aspect_ids):
        raise LexicalContractError("lexical field weights must cover each aspect exactly")
    if any(not math.isfinite(float(value)) or float(value) <= 0 for value in weights.values()):
        raise LexicalContractError("lexical field weights must be finite and positive")
    if spec.ngram_min < 1 or spec.ngram_max < spec.ngram_min:
        raise LexicalContractError("lexical n-gram range is invalid")
    if not math.isfinite(spec.k1) or spec.k1 <= 0:
        raise LexicalContractError("BM25F k1 must be finite and positive")
    b_values = dict(spec.b_by_field)
    if b_values and set(b_values) != set(spec.aspect_ids):
        raise LexicalContractError("BM25F b declarations must cover every field")
    if any(not math.isfinite(value) or value < 0 or value > 1 for value in b_values.values()):
        raise LexicalContractError("BM25F b values must be in [0,1]")


def word_tokens(text: str) -> tuple[str, ...]:
    """Deterministic Unicode lexer using only pinned Python Unicode tables."""

    normalized = unicodedata.normalize("NFC", text).casefold()
    tokens: list[str] = []
    current: list[str] = []

    def admitted(character: str) -> bool:
        return unicodedata.category(character)[:1] in {"L", "M", "N"}

    for index, character in enumerate(normalized):
        if admitted(character):
            current.append(character)
            continue
        if (
            character in {"'", "’", "-"}
            and current
            and index + 1 < len(normalized)
            and admitted(normalized[index + 1])
        ):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)


def word_ngrams(text: str, minimum: int = 1, maximum: int = 2) -> tuple[str, ...]:
    tokens = word_tokens(text)
    return tuple(
        "\x1e".join(tokens[index : index + size])
        for size in range(minimum, maximum + 1)
        for index in range(max(0, len(tokens) - size + 1))
    )


def character_ngrams(text: str, minimum: int = 3, maximum: int = 5) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFC", text).casefold()
    return tuple(
        normalized[index : index + size]
        for size in range(minimum, maximum + 1)
        for index in range(max(0, len(normalized) - size + 1))
    )


def build_sparse_tfidf_index(
    corpus: CorpusBundle,
    spec: LexicalSpec,
    analyzer: Callable[[str], Sequence[str]],
) -> SparseFieldIndex:
    """Build deterministic CSR TF-IDF field blocks without sklearn."""

    validate_spec(spec)
    started = time.perf_counter()
    matrices: dict[str, sparse.csr_matrix] = {}
    vocabularies: dict[str, tuple[str, ...]] = {}
    dfs_by_field: dict[str, np.ndarray] = {}
    nonempty_by_field: dict[str, np.ndarray] = {}
    digest = hashlib.sha256()
    digest.update(canonical_json_bytes({"corpusSha256": corpus.corpus_sha256, "spec": spec.parameters()}))
    index_bytes = 0
    for aspect_id in spec.aspect_ids:
        document_frequencies: dict[str, int] = {}
        nnz_per_document = np.zeros(len(corpus.documents), dtype=np.int64)
        field_nonempty = np.zeros(len(corpus.documents), dtype=np.bool_)
        for ordinal, document in enumerate(corpus.documents):
            aspect = document.aspects.get(aspect_id)
            terms = set(analyzer(aspect.lexical_casefolded if aspect is not None else ""))
            nnz_per_document[ordinal] = len(terms)
            field_nonempty[ordinal] = bool(terms)
            for term in terms:
                document_frequencies[term] = document_frequencies.get(term, 0) + 1
        vocabulary = tuple(sorted(document_frequencies))
        term_ordinals = {term: index for index, term in enumerate(vocabulary)}
        indptr = np.empty(len(corpus.documents) + 1, dtype=np.int64)
        indptr[0] = 0
        np.cumsum(nnz_per_document, out=indptr[1:])
        indices = np.empty(int(indptr[-1]), dtype=np.int32)
        data = np.empty(int(indptr[-1]), dtype=np.float64)
        dfs = np.asarray([document_frequencies[term] for term in vocabulary], dtype=np.int64)
        idf = np.log((1.0 + len(corpus.documents)) / (1.0 + dfs.astype(np.float64))) + 1.0
        cursor = 0
        for document in corpus.documents:
            counts: dict[str, int] = {}
            aspect = document.aspects.get(aspect_id)
            for term in analyzer(aspect.lexical_casefolded if aspect is not None else ""):
                counts[term] = counts.get(term, 0) + 1
            ordered = sorted((term_ordinals[term], count) for term, count in counts.items())
            for term_ordinal, count in ordered:
                indices[cursor] = term_ordinal
                tf = 1.0 + math.log(count) if spec.sublinear_tf else float(count)
                data[cursor] = tf * idf[term_ordinal]
                cursor += 1
        matrix = sparse.csr_matrix(
            (data, indices, indptr),
            shape=(len(corpus.documents), len(vocabulary)),
            dtype=np.float64,
        )
        norms = np.sqrt(matrix.multiply(matrix).sum(axis=1)).A1
        inverse = np.zeros_like(norms)
        np.divide(1.0, norms, out=inverse, where=norms > 0)
        matrix = sparse.diags(inverse, format="csr") @ matrix
        matrix.sort_indices()
        matrices[aspect_id] = matrix
        vocabularies[aspect_id] = vocabulary
        dfs_by_field[aspect_id] = dfs
        nonempty_by_field[aspect_id] = field_nonempty
        for value in (matrix.data, matrix.indices, matrix.indptr, dfs, field_nonempty):
            digest.update(value.tobytes(order="C"))
            index_bytes += value.nbytes
        for term in vocabulary:
            encoded = term.encode("utf-8")
            digest.update(len(encoded).to_bytes(8, "big"))
            digest.update(encoded)
            index_bytes += len(encoded)
    return SparseFieldIndex(
        spec=spec,
        object_ids=corpus.object_ids,
        object_ordinals={value: index for index, value in enumerate(corpus.object_ids)},
        matrices=matrices,
        vocabularies=vocabularies,
        document_frequencies=dfs_by_field,
        field_nonempty=nonempty_by_field,
        index_sha256=digest.hexdigest(),
        index_bytes=index_bytes,
        build_ms=(time.perf_counter() - started) * 1000.0,
    )


def sparse_score_query(index: SparseFieldIndex, query_id: str) -> np.ndarray:
    ordinal = index.object_ordinals.get(query_id)
    if ordinal is None:
        raise LexicalContractError("lexical query is outside the public corpus")
    weights = dict(index.spec.field_weights)
    denominator = sum(weights.values())
    scores = np.zeros(len(index.object_ids), dtype=np.float64)
    for aspect_id in index.spec.aspect_ids:
        matrix = index.matrices[aspect_id]
        if matrix[ordinal].nnz:
            scores += float(weights[aspect_id]) * (matrix[ordinal] @ matrix.T).toarray().ravel()
    if index.spec.fixed_field_denominator:
        scores /= denominator
    return scores


def aspect_available_query_ids(
    corpus: CorpusBundle,
    aspect_ids: Sequence[str],
) -> tuple[str, ...]:
    """Return public IDs with at least one non-empty requested text aspect.

    Missing-aspect rows remain in every candidate index as zero vectors.  They
    are not valid queries, because ranking an empty query would manufacture an
    arbitrary public-ID-ordered neighborhood from an all-zero score vector.
    """

    requested = tuple(aspect_ids)
    if not requested or set(requested) - ALLOWED_ASPECTS:
        raise LexicalContractError("aspect-availability request is absent or ungoverned")
    return tuple(
        document.object_id
        for document in corpus.documents
        if any(
            (aspect := document.aspects.get(aspect_id)) is not None
            and aspect.character_count > 0
            and bool(aspect.lexical_casefolded)
            for aspect_id in requested
        )
    )


def stable_top_k(
    scores: np.ndarray,
    object_ids: Sequence[str],
    query_id: str,
    *,
    k: int = DEFAULT_TOP_K,
) -> list[dict[str, Any]]:
    if scores.ndim != 1 or len(scores) != len(object_ids):
        raise LexicalContractError("score vector shape differs from corpus")
    if tuple(object_ids) != tuple(sorted(object_ids)):
        raise LexicalContractError("stable ranking requires sorted public IDs")
    if k <= 0 or k >= len(object_ids):
        raise LexicalContractError("bounded top-k is outside corpus bounds")
    try:
        query_ordinal = object_ids.index(query_id)  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        positions = {value: index for index, value in enumerate(object_ids)}
        if query_id not in positions:
            raise LexicalContractError("query ID is outside corpus")
        query_ordinal = positions[query_id]
    work = np.asarray(scores, dtype=np.float64).copy()
    query_score = float(work[query_ordinal])
    work[query_ordinal] = 0.0
    if (not math.isfinite(query_score) and query_score != -math.inf) or not np.isfinite(work).all():
        raise LexicalContractError("lexical scorer emitted a non-finite score")
    work[query_ordinal] = -np.inf
    # Select only the bounded top-k slab.  Boundary-score ties are resolved by
    # the already ascending public-ID ordinals before the small final sort, so
    # argpartition cannot make equal-score results nondeterministic.
    partition = np.argpartition(-work, k - 1)[:k]
    boundary_score = float(np.min(work[partition]))
    above = np.flatnonzero(work > boundary_score)
    tied = np.flatnonzero(work == boundary_score)
    needed = k - len(above)
    selected = np.concatenate((above, tied[:needed])).astype(np.int64, copy=False)
    order = selected[np.lexsort((selected, -work[selected]))]
    if len(order) != k:
        raise LexicalContractError("bounded top-k selection returned the wrong row count")
    return [
        {
            "rank": rank,
            "candidatePublicId": str(object_ids[int(ordinal)]),
            "candidateId": str(object_ids[int(ordinal)]),
            "score": float(work[int(ordinal)]),
            "historicalRelation": False,
            "semanticRelation": False,
            "probability": False,
        }
        for rank, ordinal in enumerate(order, start=1)
    ]


def ranking_receipt(
    *,
    corpus: CorpusBundle,
    spec: LexicalSpec,
    index_sha256: str,
    index_bytes: int,
    build_ms: float,
    rankings: Mapping[str, Sequence[Mapping[str, Any]]],
    query_ms: Sequence[float],
    top_k: int,
    full_corpus: bool,
) -> dict[str, Any]:
    ordered_query_ids = tuple(sorted(rankings))
    available_query_ids = aspect_available_query_ids(corpus, spec.aspect_ids)
    full_public_cohort = ordered_query_ids == corpus.object_ids
    full_aspect_cohort = ordered_query_ids == available_query_ids
    if full_corpus != full_public_cohort:
        raise LexicalContractError("lexical full-public-cohort declaration is inconsistent")
    if set(ordered_query_ids) - set(available_query_ids):
        raise LexicalContractError("lexical result contains an unavailable-aspect query")
    ids_material = [
        [query_id, [str(row["candidatePublicId"]) for row in rankings[query_id]]]
        for query_id in ordered_query_ids
    ]
    score_material = [
        [query_id, [format(float(row["score"]), ".12g") for row in rankings[query_id]]]
        for query_id in ordered_query_ids
    ]
    return {
        "schemaVersion": LEXICAL_RESULT_SCHEMA_VERSION,
        "methodId": spec.method_id,
        "implementationVersion": spec.implementation_version,
        "sourceCommit": SOURCE_COMMIT,
        "corpusPolicyVersion": corpus.policy_version,
        "corpusPolicySha256": corpus.policy_sha256,
        "fieldRegistryVersion": corpus.field_registry_version,
        "fieldRegistrySha256": corpus.field_registry_sha256,
        "normalizationVersion": corpus.normalization_version,
        "corpusSha256": corpus.corpus_sha256,
        "inputVariant": spec.input_variant,
        "aspectIds": list(spec.aspect_ids),
        "parameters": spec.parameters(),
        "fullPublicCohort": full_public_cohort,
        "fullAspectCohort": full_aspect_cohort,
        "objectCount": corpus.public_object_count,
        "candidateObjectCount": corpus.public_object_count,
        "aspectAvailableQueryCount": len(available_query_ids),
        "aspectUnavailableQueryCount": corpus.public_object_count - len(available_query_ids),
        "queryCount": len(rankings),
        "topK": top_k,
        "indexSha256": index_sha256,
        "indexBytes": index_bytes,
        "indexBuildMs": build_ms,
        "objectLocalExactQueryP50Ms": quantile_r7(query_ms, 0.50),
        "objectLocalExactQueryP95Ms": quantile_r7(query_ms, 0.95),
        "rankingIdsSha256": sha256_json(ids_material),
        "scoreObservationSha256": sha256_json(score_material),
        "semanticDeterminismMaterialSha256": sha256_json(
            {
                "corpusSha256": corpus.corpus_sha256,
                "indexSha256": index_sha256,
                "parameters": spec.parameters(),
            }
        ),
        "rankingDeterministic": True,
        "floatingPointObservationHardwareScoped": True,
        "pairMatrixMaterialized": False,
        "fullRankingsSaved": False,
        "randomnessAffectsCorpus": False,
        "randomnessAffectsScores": False,
        "historicalRelation": False,
        "semanticRelation": False,
        "probability": False,
        # Kept in memory for downstream aggregate evaluation. Evidence writers
        # must deliberately strip this key before serializing a run receipt.
        "rankings": {key: list(rankings[key]) for key in ordered_query_ids},
    }


def strip_rankings(result: Mapping[str, Any]) -> dict[str, Any]:
    """Return the bounded aggregate receipt safe for committed evidence."""

    return {key: value for key, value in result.items() if key != "rankings"}


def self_test() -> dict[str, Any]:
    ids = ("SURF-A", "SURF-B", "SURF-C")
    rows = stable_top_k(np.asarray([1.0, 0.5, 0.5]), ids, "SURF-A", k=2)
    if [row["candidatePublicId"] for row in rows] != ["SURF-B", "SURF-C"]:
        raise LexicalContractError("stable tie break self-test failed")
    if word_tokens("L’été—co-op 中文") != ("l’été", "co-op", "中文"):
        raise LexicalContractError("Unicode word lexer self-test failed")
    if character_ngrams("abcd", 3, 3) != ("abc", "bcd"):
        raise LexicalContractError("character n-gram self-test failed")
    import corpus_builder

    aspect = corpus_builder._aspect_from_text(
        aspect_id="NLP_TITLE",
        field_id="NLP-FIELD-001",
        original_text="abc",
        source_artifact_sha256="a" * 64,
        include_text=True,
    )
    _coerce_aspect(aspect, "NLP_TITLE")
    for field, replacement in (
        ("semanticNormalized", "xyz"),
        ("displayOriginal", "xyz"),
        ("tokenCount", 99),
    ):
        adversarial = dict(aspect)
        adversarial[field] = replacement
        try:
            _coerce_aspect(adversarial, "NLP_TITLE")
        except LexicalContractError:
            pass
        else:
            raise LexicalContractError(f"stale aspect integrity field was accepted: {field}")
    return {
        "schemaVersion": "trace-nlp-lexical-common-self-test/v1",
        "stableTieBreak": "PASS",
        "unicodeLexer": "PASS",
        "characterNgrams": "PASS",
        "staleTextHashesRejected": True,
        "staleTokenCountRejected": True,
        "seedAffectsResult": False,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
