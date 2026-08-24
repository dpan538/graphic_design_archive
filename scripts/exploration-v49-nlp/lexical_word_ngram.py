#!/usr/bin/env python3
"""Deterministic field-separated Unicode word 1--2 gram TF-IDF baseline."""

from __future__ import annotations

import json
import time
from typing import Iterable

import lexical_common as common


IMPLEMENTATION_VERSION = "trace-nlp-lexical-word-ngram-2026-08-24"


def default_spec(
    *,
    aspect_ids: tuple[str, ...] = ("NLP_TITLE",),
    input_variant: str = "ORIGINAL_APPROVED",
) -> common.LexicalSpec:
    return common.LexicalSpec(
        method_id="NLP-L2-WORD-1-2",
        implementation_version=IMPLEMENTATION_VERSION,
        aspect_ids=aspect_ids,
        field_weights=tuple((aspect_id, 1.0) for aspect_id in aspect_ids),
        input_variant=input_variant,
        analyzer="UNICODE_WORD_NGRAM",
        ngram_min=1,
        ngram_max=2,
        sublinear_tf=True,
        idf_mode="SMOOTHED",
        fixed_field_denominator=True,
    )


def build_index(
    corpus: common.CorpusBundle,
    spec: common.LexicalSpec | None = None,
) -> common.SparseFieldIndex:
    resolved = spec or default_spec()
    if resolved.analyzer != "UNICODE_WORD_NGRAM":
        raise common.LexicalContractError("word baseline received another analyzer")
    return common.build_sparse_tfidf_index(
        corpus,
        resolved,
        lambda text: common.word_ngrams(text, resolved.ngram_min, resolved.ngram_max),
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
        raise common.LexicalContractError("word query set is empty or has an unavailable aspect")
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
    expected = ("l’été", "co-op", "中文", "l’été\x1eco-op", "co-op\x1e中文")
    if common.word_ngrams("L’été co-op 中文", 1, 2) != expected:
        raise common.LexicalContractError("Unicode word 1--2 gram self-test failed")
    return {
        "schemaVersion": "trace-nlp-word-ngram-self-test/v1",
        "common": common_result,
        "ngramRange": [1, 2],
        "hanSegmentationIntroduced": False,
        "seedAffectsResult": False,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), ensure_ascii=False, sort_keys=True))
