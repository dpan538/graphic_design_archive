#!/usr/bin/env python3
"""Orchestrate the mandatory full-cohort L0--L3 lexical baselines in memory."""

from __future__ import annotations

import json
import time
from dataclasses import replace
from typing import Iterable, Mapping

import numpy as np

import lexical_bm25f
import lexical_char_ngram
import lexical_common as common
import lexical_word_ngram


IMPLEMENTATION_VERSION = "trace-nlp-lexical-evaluation-2026-08-24"
ASPECT_PURPOSE = {
    "NLP_TITLE": "OBJECT_SEMANTIC",
    "NLP_OBJECT_SEMANTIC_COMPOSITE": "OBJECT_SEMANTIC_TITLE_ONLY",
    "NLP_SUBJECT": "LEAKAGE_GATED_SUBJECT_DIAGNOSTIC",
    "NLP_SOURCE_NARRATIVE": "SOURCE_NARRATIVE_DIAGNOSTIC_ONLY",
}
RRF_K = 60


def _aspect_spec(spec: common.LexicalSpec, aspect_id: str) -> common.LexicalSpec:
    suffix = aspect_id.removeprefix("NLP_")
    return replace(
        spec,
        method_id=f"{spec.method_id}-{suffix}",
        aspect_ids=(aspect_id,),
        field_weights=((aspect_id, 1.0),),
        b_by_field=((aspect_id, 0.75),) if spec.b_by_field else (),
    )


def _full_rank_vector(scores: np.ndarray, object_ids: tuple[str, ...], query_id: str) -> np.ndarray:
    work = np.asarray(scores, dtype=np.float64).copy()
    query_ordinal = object_ids.index(query_id)
    work[query_ordinal] = -np.inf
    order = np.argsort(-work, kind="stable")
    ranks = np.empty(len(object_ids), dtype=np.int32)
    ranks[order] = np.arange(1, len(object_ids) + 1, dtype=np.int32)
    ranks[query_ordinal] = np.iinfo(np.int32).max
    return ranks


def reciprocal_rank_fusion_scores(
    left_scores: np.ndarray,
    right_scores: np.ndarray,
    object_ids: tuple[str, ...],
    query_id: str,
    *,
    rrf_k: int = RRF_K,
) -> np.ndarray:
    if rrf_k <= 0 or left_scores.shape != right_scores.shape:
        raise common.LexicalContractError("RRF inputs or constant are invalid")
    left_ranks = _full_rank_vector(left_scores, object_ids, query_id)
    right_ranks = _full_rank_vector(right_scores, object_ids, query_id)
    fused = 1.0 / (rrf_k + left_ranks.astype(np.float64))
    fused += 1.0 / (rrf_k + right_ranks.astype(np.float64))
    fused[object_ids.index(query_id)] = -np.inf
    return fused


def run_lexical_suite(
    corpus: common.CorpusBundle | None = None,
    *,
    aspect_id: str = "NLP_TITLE",
    aspect_purpose: str = "OBJECT_SEMANTIC",
    query_ids: Iterable[str] | None = None,
    k: int = common.DEFAULT_TOP_K,
) -> dict:
    corpus = corpus or common.load_governed_corpus()
    expected_purpose = ASPECT_PURPOSE.get(aspect_id)
    if expected_purpose is None or aspect_purpose != expected_purpose:
        raise common.LexicalContractError("aspect purpose is absent or conflicts with frozen governance")
    available_query_ids = common.aspect_available_query_ids(corpus, (aspect_id,))
    selected = tuple(available_query_ids if query_ids is None else sorted(set(query_ids)))
    if not selected or set(selected) - set(available_query_ids):
        raise common.LexicalContractError("lexical suite query set includes an unavailable aspect")

    l0_spec = _aspect_spec(lexical_bm25f.default_spec(), aspect_id)
    l1_spec = _aspect_spec(lexical_char_ngram.default_spec(), aspect_id)
    l2_spec = _aspect_spec(lexical_word_ngram.default_spec(), aspect_id)
    l0_index = lexical_bm25f.build_index(corpus, l0_spec)
    l1_index = lexical_char_ngram.build_index(corpus, l1_spec)
    l2_index = lexical_word_ngram.build_index(corpus, l2_spec)

    rankings = {"NLP-L0": {}, "NLP-L1": {}, "NLP-L2": {}, "NLP-L3": {}}
    timings = {key: [] for key in rankings}
    for query_id in selected:
        started = time.perf_counter()
        l0_scores = lexical_bm25f.score_query(l0_index, corpus, query_id)
        rankings["NLP-L0"][query_id] = common.stable_top_k(
            l0_scores, corpus.object_ids, query_id, k=k
        )
        timings["NLP-L0"].append((time.perf_counter() - started) * 1000.0)

        started = time.perf_counter()
        l1_scores = lexical_char_ngram.score_query(l1_index, query_id)
        rankings["NLP-L1"][query_id] = common.stable_top_k(
            l1_scores, corpus.object_ids, query_id, k=k
        )
        timings["NLP-L1"].append((time.perf_counter() - started) * 1000.0)

        started = time.perf_counter()
        l2_scores = lexical_word_ngram.score_query(l2_index, query_id)
        rankings["NLP-L2"][query_id] = common.stable_top_k(
            l2_scores, corpus.object_ids, query_id, k=k
        )
        timings["NLP-L2"].append((time.perf_counter() - started) * 1000.0)

        started = time.perf_counter()
        l3_scores = reciprocal_rank_fusion_scores(
            l0_scores, l1_scores, corpus.object_ids, query_id
        )
        rankings["NLP-L3"][query_id] = common.stable_top_k(
            l3_scores, corpus.object_ids, query_id, k=k
        )
        timings["NLP-L3"].append((time.perf_counter() - started) * 1000.0)

    full_public_cohort = selected == corpus.object_ids
    full_aspect_cohort = selected == available_query_ids
    l3_spec = common.LexicalSpec(
        method_id=f"NLP-L3-RRF-L0-L1-K{RRF_K}-{aspect_id.removeprefix('NLP_')}",
        implementation_version=IMPLEMENTATION_VERSION,
        aspect_ids=(aspect_id,),
        field_weights=((aspect_id, 1.0),),
        input_variant="ORIGINAL_APPROVED",
        analyzer="RECIPROCAL_RANK_FUSION",
        ngram_min=1,
        ngram_max=1,
        sublinear_tf=False,
        idf_mode="INHERITED_L0_L1",
        fixed_field_denominator=True,
    )
    l3_index_sha = common.sha256_json(
        {
            "leftIndexSha256": l0_index.index_sha256,
            "rightIndexSha256": l1_index.index_sha256,
            "rrfK": RRF_K,
        }
    )
    receipts = {
        "NLP-L0": common.ranking_receipt(
            corpus=corpus,
            spec=l0_spec,
            index_sha256=l0_index.index_sha256,
            index_bytes=l0_index.index_bytes,
            build_ms=l0_index.build_ms,
            rankings=rankings["NLP-L0"],
            query_ms=timings["NLP-L0"],
            top_k=k,
            full_corpus=full_public_cohort,
        ),
        "NLP-L1": common.ranking_receipt(
            corpus=corpus,
            spec=l1_spec,
            index_sha256=l1_index.index_sha256,
            index_bytes=l1_index.index_bytes,
            build_ms=l1_index.build_ms,
            rankings=rankings["NLP-L1"],
            query_ms=timings["NLP-L1"],
            top_k=k,
            full_corpus=full_public_cohort,
        ),
        "NLP-L2": common.ranking_receipt(
            corpus=corpus,
            spec=l2_spec,
            index_sha256=l2_index.index_sha256,
            index_bytes=l2_index.index_bytes,
            build_ms=l2_index.build_ms,
            rankings=rankings["NLP-L2"],
            query_ms=timings["NLP-L2"],
            top_k=k,
            full_corpus=full_public_cohort,
        ),
        "NLP-L3": common.ranking_receipt(
            corpus=corpus,
            spec=l3_spec,
            index_sha256=l3_index_sha,
            index_bytes=l0_index.index_bytes + l1_index.index_bytes,
            build_ms=l0_index.build_ms + l1_index.build_ms,
            rankings=rankings["NLP-L3"],
            query_ms=timings["NLP-L3"],
            top_k=k,
            full_corpus=full_public_cohort,
        ),
    }
    return {
        "schemaVersion": "trace-nlp-lexical-suite/v1",
        "implementationVersion": IMPLEMENTATION_VERSION,
        "corpusSha256": corpus.corpus_sha256,
        "aspectId": aspect_id,
        "aspectPurpose": aspect_purpose,
        "modelCount": 4,
        "candidateObjectCount": corpus.public_object_count,
        "aspectAvailableQueryCount": len(available_query_ids),
        "aspectUnavailableQueryCount": corpus.public_object_count - len(available_query_ids),
        "fullPublicCohortModelCount": 4 if full_public_cohort else 0,
        "fullAspectCohortModelCount": 4 if full_aspect_cohort else 0,
        "rrfK": RRF_K,
        "fusionWeightsSelected": False,
        "pairMatrixMaterialized": False,
        "fullRankingsSaved": False,
        "models": receipts,
        "suiteRankingSha256": common.sha256_json(
            {key: value["rankingIdsSha256"] for key, value in sorted(receipts.items())}
        ),
    }


def strip_suite_rankings(suite: Mapping) -> dict:
    output = dict(suite)
    output["models"] = {
        key: common.strip_rankings(value) for key, value in suite["models"].items()
    }
    return output


def self_test() -> dict:
    object_ids = ("SURF-A", "SURF-B", "SURF-C", "SURF-D")
    left = np.asarray([1.0, 0.9, 0.1, 0.0])
    right = np.asarray([1.0, 0.1, 0.9, 0.0])
    fused = reciprocal_rank_fusion_scores(left, right, object_ids, "SURF-A")
    rows = common.stable_top_k(fused, object_ids, "SURF-A", k=3)
    if [row["candidatePublicId"] for row in rows[:2]] != ["SURF-B", "SURF-C"]:
        raise common.LexicalContractError("RRF deterministic tie self-test failed")
    if ASPECT_PURPOSE["NLP_SOURCE_NARRATIVE"] != "SOURCE_NARRATIVE_DIAGNOSTIC_ONLY":
        raise common.LexicalContractError("source narrative governance self-test failed")
    return {
        "schemaVersion": "trace-nlp-lexical-eval-self-test/v1",
        "modelCount": 4,
        "rrfUsesFullRanksBeforeTruncation": True,
        "stableTieBreak": "PASS",
        "sourceNarrativeIsolated": True,
        "pairMatrixMaterialized": False,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
