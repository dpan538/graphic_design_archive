#!/usr/bin/env python3
"""Deterministic BM25F-style isolated NLP research baseline.

The vocabulary is shared so a query term can match any declared field, while
term frequency, length normalization, weights, and contribution paths remain
field-specific.  The frozen v1 object-semantic composite contains title only;
subject and source narrative are evaluated as separate diagnostic aspects.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass
from typing import Iterable, Mapping

import numpy as np

import lexical_common as common


IMPLEMENTATION_VERSION = "trace-nlp-lexical-bm25f-2026-08-24"


@dataclass(frozen=True)
class Bm25fIndex:
    spec: common.LexicalSpec
    object_ids: tuple[str, ...]
    object_ordinals: Mapping[str, int]
    postings: Mapping[str, Mapping[str, tuple[np.ndarray, np.ndarray]]]
    document_frequencies: Mapping[str, int]
    document_lengths: Mapping[str, np.ndarray]
    average_field_lengths: Mapping[str, float]
    index_sha256: str
    index_bytes: int
    build_ms: float


def default_spec(
    *,
    aspect_ids: tuple[str, ...] = ("NLP_TITLE",),
    input_variant: str = "ORIGINAL_APPROVED",
) -> common.LexicalSpec:
    return common.LexicalSpec(
        method_id="NLP-L0-BM25F-EQUAL",
        implementation_version=IMPLEMENTATION_VERSION,
        aspect_ids=aspect_ids,
        field_weights=tuple((aspect_id, 1.0) for aspect_id in aspect_ids),
        input_variant=input_variant,
        analyzer="UNICODE_WORD_UNIGRAM",
        ngram_min=1,
        ngram_max=1,
        sublinear_tf=False,
        idf_mode="ROBERTSON_POSITIVE",
        fixed_field_denominator=False,
        k1=1.2,
        b_by_field=tuple((aspect_id, 0.75) for aspect_id in aspect_ids),
    )


def build_index(
    corpus: common.CorpusBundle,
    spec: common.LexicalSpec | None = None,
) -> Bm25fIndex:
    resolved = spec or default_spec()
    common.validate_spec(resolved)
    if resolved.analyzer != "UNICODE_WORD_UNIGRAM":
        raise common.LexicalContractError("BM25F received another analyzer")
    started = time.perf_counter()
    posting_lists: dict[str, dict[str, list[tuple[int, int]]]] = {
        aspect_id: {} for aspect_id in resolved.aspect_ids
    }
    document_frequencies: dict[str, int] = {}
    lengths = {
        aspect_id: np.zeros(len(corpus.documents), dtype=np.int64)
        for aspect_id in resolved.aspect_ids
    }
    for ordinal, document in enumerate(corpus.documents):
        document_terms: set[str] = set()
        for aspect_id in resolved.aspect_ids:
            aspect = document.aspects.get(aspect_id)
            tokens = common.word_tokens(aspect.lexical_casefolded if aspect is not None else "")
            lengths[aspect_id][ordinal] = len(tokens)
            counts: dict[str, int] = {}
            for token in tokens:
                counts[token] = counts.get(token, 0) + 1
            document_terms.update(counts)
            field_postings = posting_lists[aspect_id]
            for token, count in counts.items():
                field_postings.setdefault(token, []).append((ordinal, count))
        for token in document_terms:
            document_frequencies[token] = document_frequencies.get(token, 0) + 1
    postings: dict[str, dict[str, tuple[np.ndarray, np.ndarray]]] = {}
    digest = hashlib.sha256()
    digest.update(
        common.canonical_json_bytes(
            {"corpusSha256": corpus.corpus_sha256, "parameters": resolved.parameters()}
        )
    )
    index_bytes = 0
    for aspect_id in resolved.aspect_ids:
        frozen_field = {}
        for token in sorted(posting_lists[aspect_id]):
            values = posting_lists[aspect_id][token]
            ordinals = np.asarray([value[0] for value in values], dtype=np.int32)
            frequencies = np.asarray([value[1] for value in values], dtype=np.float64)
            frozen_field[token] = (ordinals, frequencies)
            encoded = token.encode("utf-8")
            digest.update(len(encoded).to_bytes(8, "big"))
            digest.update(encoded)
            digest.update(ordinals.tobytes(order="C"))
            digest.update(frequencies.tobytes(order="C"))
            index_bytes += len(encoded) + ordinals.nbytes + frequencies.nbytes
        postings[aspect_id] = frozen_field
        digest.update(lengths[aspect_id].tobytes(order="C"))
        index_bytes += lengths[aspect_id].nbytes
    digest.update(
        common.canonical_json_bytes(
            {token: document_frequencies[token] for token in sorted(document_frequencies)}
        )
    )
    averages = {
        aspect_id: float(np.mean(values)) if len(values) else 0.0
        for aspect_id, values in lengths.items()
    }
    return Bm25fIndex(
        spec=resolved,
        object_ids=corpus.object_ids,
        object_ordinals={value: index for index, value in enumerate(corpus.object_ids)},
        postings=postings,
        document_frequencies=dict(sorted(document_frequencies.items())),
        document_lengths=lengths,
        average_field_lengths=averages,
        index_sha256=digest.hexdigest(),
        index_bytes=index_bytes,
        build_ms=(time.perf_counter() - started) * 1000.0,
    )


def _positive_robertson_idf(document_count: int, document_frequency: int) -> float:
    return math.log(1.0 + (document_count - document_frequency + 0.5) / (document_frequency + 0.5))


def score_query(
    index: Bm25fIndex,
    corpus: common.CorpusBundle,
    query_id: str,
) -> np.ndarray:
    query_ordinal = index.object_ordinals.get(query_id)
    if query_ordinal is None or corpus.object_ids != index.object_ids:
        raise common.LexicalContractError("BM25F query/corpus differs from index")
    query_terms: set[str] = set()
    for aspect_id in index.spec.aspect_ids:
        aspect = corpus.documents_by_id[query_id].aspects.get(aspect_id)
        query_terms.update(common.word_tokens(aspect.lexical_casefolded if aspect is not None else ""))
    weights = dict(index.spec.field_weights)
    b_values = dict(index.spec.b_by_field)
    scores = np.zeros(len(index.object_ids), dtype=np.float64)
    for term in sorted(query_terms):
        document_frequency = index.document_frequencies.get(term)
        if not document_frequency:
            continue
        combined_tf = np.zeros(len(index.object_ids), dtype=np.float64)
        for aspect_id in index.spec.aspect_ids:
            posting = index.postings[aspect_id].get(term)
            if posting is None:
                continue
            ordinals, frequencies = posting
            average_length = index.average_field_lengths[aspect_id]
            if average_length <= 0:
                continue
            length_ratio = index.document_lengths[aspect_id][ordinals] / average_length
            normalization = 1.0 - b_values[aspect_id] + b_values[aspect_id] * length_ratio
            combined_tf[ordinals] += weights[aspect_id] * frequencies / normalization
        nonzero = combined_tf > 0
        idf = _positive_robertson_idf(len(index.object_ids), document_frequency)
        scores[nonzero] += idf * (
            (index.spec.k1 + 1.0) * combined_tf[nonzero]
            / (index.spec.k1 + combined_tf[nonzero])
        )
    return scores


def run_exact_top_k(
    corpus: common.CorpusBundle,
    *,
    spec: common.LexicalSpec | None = None,
    index: Bm25fIndex | None = None,
    query_ids: Iterable[str] | None = None,
    k: int = common.DEFAULT_TOP_K,
) -> dict:
    resolved_index = index or build_index(corpus, spec)
    available = common.aspect_available_query_ids(corpus, resolved_index.spec.aspect_ids)
    selected = tuple(available if query_ids is None else sorted(set(query_ids)))
    if not selected or set(selected) - set(available):
        raise common.LexicalContractError("BM25F query set is empty or has an unavailable aspect")
    rankings = {}
    query_ms = []
    for query_id in selected:
        started = time.perf_counter()
        scores = score_query(resolved_index, corpus, query_id)
        rankings[query_id] = common.stable_top_k(scores, corpus.object_ids, query_id, k=k)
        query_ms.append((time.perf_counter() - started) * 1000.0)
    return common.ranking_receipt(
        corpus=corpus,
        spec=resolved_index.spec,
        index_sha256=resolved_index.index_sha256,
        index_bytes=resolved_index.index_bytes,
        build_ms=resolved_index.build_ms,
        rankings=rankings,
        query_ms=query_ms,
        top_k=k,
        full_corpus=selected == corpus.object_ids,
    )


def self_test() -> dict:
    rare = _positive_robertson_idf(100, 1)
    common_idf = _positive_robertson_idf(100, 99)
    if not rare > common_idf > 0:
        raise common.LexicalContractError("BM25F positive IDF self-test failed")
    spec = default_spec(aspect_ids=("NLP_TITLE", "NLP_SUBJECT"))
    common.validate_spec(spec)
    if dict(spec.field_weights) != {"NLP_TITLE": 1.0, "NLP_SUBJECT": 1.0}:
        raise common.LexicalContractError("BM25F equal-field self-test failed")
    return {
        "schemaVersion": "trace-nlp-bm25f-self-test/v1",
        "positiveIdf": "PASS",
        "equalFieldBaseline": "PASS",
        "asymmetric": True,
        "seedAffectsResult": False,
        "pairMatrixMaterialized": False,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
