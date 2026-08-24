#!/usr/bin/env python3
"""Deterministic field-separated character 3--5 gram TF-IDF baseline."""

from __future__ import annotations

import json
import time
from typing import Iterable

import lexical_common as common


IMPLEMENTATION_VERSION = "trace-nlp-lexical-char-ngram-2026-08-24"


def default_spec(
    *,
    aspect_ids: tuple[str, ...] = ("NLP_TITLE",),
    input_variant: str = "ORIGINAL_APPROVED",
) -> common.LexicalSpec:
    return common.LexicalSpec(
        method_id="NLP-L1-CHAR-3-5",
        implementation_version=IMPLEMENTATION_VERSION,
        aspect_ids=aspect_ids,
        field_weights=tuple((aspect_id, 1.0) for aspect_id in aspect_ids),
        input_variant=input_variant,
        analyzer="UNICODE_CHARACTER_NGRAM",
        ngram_min=3,
        ngram_max=5,
        sublinear_tf=True,
        idf_mode="SMOOTHED",
        fixed_field_denominator=True,
    )


def build_index(
    corpus: common.CorpusBundle,
    spec: common.LexicalSpec | None = None,
) -> common.SparseFieldIndex:
    resolved = spec or default_spec()
    if resolved.analyzer != "UNICODE_CHARACTER_NGRAM":
        raise common.LexicalContractError("character baseline received another analyzer")
    return common.build_sparse_tfidf_index(
        corpus,
        resolved,
        lambda text: common.character_ngrams(text, resolved.ngram_min, resolved.ngram_max),
    )


def score_query(index: common.SparseFieldIndex, query_id: str):
    return common.sparse_score_query(index, query_id)


def run_exact_top_k(
    corpus: common.CorpusBundle,
    *,
    spec: common.LexicalSpec | None = None,
    index: common.SparseFieldIndex | None = None,
    query_ids: Iterable[str] | None = None,
    k: int = common.DEFAULT_TOP_K,
) -> dict:
    resolved_index = index or build_index(corpus, spec)
    available = common.aspect_available_query_ids(corpus, resolved_index.spec.aspect_ids)
    selected = tuple(available if query_ids is None else sorted(set(query_ids)))
    if not selected or set(selected) - set(available):
        raise common.LexicalContractError("character query set is empty or has an unavailable aspect")
    rankings = {}
    query_ms = []
    for query_id in selected:
        started = time.perf_counter()
        scores = score_query(resolved_index, query_id)
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
    common_result = common.self_test()
    if common.character_ngrams("Åb", 3, 5):
        raise common.LexicalContractError("short character input created an n-gram")
    grams = common.character_ngrams("ＡＢＣ", 3, 3)
    if grams != ("ａｂｃ",):
        raise common.LexicalContractError("character baseline silently compatibility-folded text")
    return {
        "schemaVersion": "trace-nlp-char-ngram-self-test/v1",
        "common": common_result,
        "ngramRange": [3, 5],
        "compatibilityFolded": False,
        "seedAffectsResult": False,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), ensure_ascii=False, sort_keys=True))
