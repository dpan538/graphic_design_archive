#!/usr/bin/env python3
"""Mechanically verified cross-language retrieval evaluation for TRACE NLP.

Only externally verified multilingual/title-variant positives are eligible.
Model proximity can measure their rank but can never create a positive pair.
When no governed positive exists, the result is explicitly NOT_RUN.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import common as governance_common
import evaluation_registry as governed_evaluation_registry


SCHEMA_VERSION = "trace-nlp-cross-language-evaluation/v1"
IMPLEMENTATION_VERSION = "trace-nlp-cross-language-evaluation-2026-08-24"
PUBLIC_ID_PATTERN = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
DEFAULT_K_VALUES = (1, 5, 10, 20)
MAX_REVIEW_ROWS = 50

APPROVED_POSITIVE_CLASSES = frozenset(
    {
        "VERIFIED_TITLE_LANGUAGE_VARIANT_POSITIVE",
        "VERIFIED_MULTILINGUAL_REPRESENTATION_POSITIVE",
        "CROSS_LANGUAGE_POSITIVE",
    }
)
APPROVED_TASKS = frozenset(
    {
        "NLP_TASK_B_VERIFIED_TITLE_LANGUAGE_VARIANT",
        "NLP_TASK_D_CROSS_LANGUAGE_CONSISTENCY",
        "NLP_TASK_D_CROSS_LINGUAL_CONSISTENCY",
    }
)


class CrossLanguageEvalError(ValueError):
    """Raised when cross-language evaluation evidence is malformed."""


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


def _field(row: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in row:
            return row[name]
    return None


def _verified_pair(row: Mapping[str, Any]) -> dict[str, Any] | None:
    pair_class = str(_field(row, "pair_class", "pairClass") or "").strip()
    task = str(_field(row, "task", "taskId") or "").strip()
    if pair_class not in APPROVED_POSITIVE_CLASSES or task not in APPROVED_TASKS:
        return None
    pair_id = str(_field(row, "pair_id", "pairId") or "").strip()
    left = str(
        _field(row, "public_object_id_a", "publicObjectIdA", "leftPublicObjectId")
        or ""
    ).strip()
    right = str(
        _field(row, "public_object_id_b", "publicObjectIdB", "rightPublicObjectId")
        or ""
    ).strip()
    source = str(_field(row, "verification_source", "verificationSource") or "").strip()
    strength = str(
        _field(row, "verification_strength", "verificationStrength") or ""
    ).strip()
    language_script = str(
        _field(row, "language_script", "languageScript") or ""
    ).strip()
    if not pair_id or left == right:
        raise CrossLanguageEvalError("verified cross-language pair has invalid identity")
    if not PUBLIC_ID_PATTERN.fullmatch(left) or not PUBLIC_ID_PATTERN.fullmatch(right):
        raise CrossLanguageEvalError("verified pair contains a non-public identity")
    try:
        governance_common.ensure_public_object_id(left)
        governance_common.ensure_public_object_id(right)
    except governance_common.NlpBoundaryError as exc:
        raise CrossLanguageEvalError("verified pair is outside the authoritative public cohort") from exc
    if not source or not strength:
        raise CrossLanguageEvalError("positive pair lacks external verification evidence")
    if re.search(r"(?:model output|embedding|nearest neighbou?r|generated translation)", source, re.I):
        raise CrossLanguageEvalError("model/generated evidence cannot verify a positive pair")
    if not language_script:
        raise CrossLanguageEvalError("verified cross-language pair lacks language/script evidence")
    return {
        "pairId": pair_id,
        "leftPublicObjectId": left,
        "rightPublicObjectId": right,
        "task": task,
        "pairClass": pair_class,
        "verificationSourceSha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "verificationStrength": strength,
        "languageScript": language_script,
    }


def verified_cross_language_pairs(
    pair_rows: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    pairs = [pair for row in pair_rows if (pair := _verified_pair(row)) is not None]
    pairs.sort(key=lambda row: row["pairId"])
    if len({row["pairId"] for row in pairs}) != len(pairs):
        raise CrossLanguageEvalError("cross-language pair IDs are not unique")
    endpoints = [
        tuple(sorted((row["leftPublicObjectId"], row["rightPublicObjectId"])))
        for row in pairs
    ]
    if len(endpoints) != len(set(endpoints)):
        raise CrossLanguageEvalError("cross-language endpoint pair is duplicated")
    return tuple(pairs)


def evaluate_cross_language(
    index: Any,
    pair_rows: Iterable[Mapping[str, Any]],
    *,
    method_id: str,
    corpus_sha256: str,
    evaluation_registry_sha256: str,
    input_variant: str,
    aspect_id: str,
    k_values: Sequence[int] = DEFAULT_K_VALUES,
    max_review_rows: int = MAX_REVIEW_ROWS,
) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{64}", corpus_sha256):
        raise CrossLanguageEvalError("corpusSha256 must be a lowercase SHA-256")
    authoritative_registry_sha = governed_evaluation_registry.evaluation_registry_sha256()
    if evaluation_registry_sha256 != authoritative_registry_sha:
        raise CrossLanguageEvalError("evaluation registry SHA differs from the governed registry")
    if tuple(sorted(set(k_values))) != tuple(k_values) or any(k <= 0 for k in k_values):
        raise CrossLanguageEvalError("k values must be unique, sorted, and positive")
    if max(k_values, default=0) > 50:
        raise CrossLanguageEvalError("cross-language evaluation top-k exceeds 50")
    if not 0 <= max_review_rows <= MAX_REVIEW_ROWS:
        raise CrossLanguageEvalError("review-row bound exceeds 50")
    supplied_rows = tuple(dict(row) for row in pair_rows)
    authoritative_rows = governed_evaluation_registry.build_evaluation_registry()
    if supplied_rows != authoritative_rows:
        raise CrossLanguageEvalError("cross-language rows differ from the governed evaluation registry")
    object_ids = tuple(getattr(index, "object_ids", ()))
    if object_ids != governance_common.load_public_ids():
        raise CrossLanguageEvalError("cross-language index is not the full authoritative public cohort")
    if getattr(index, "corpus_sha256", None) != corpus_sha256:
        raise CrossLanguageEvalError("cross-language corpus SHA differs from the indexed corpus")
    pairs = verified_cross_language_pairs(supplied_rows)
    base = {
        "schemaVersion": SCHEMA_VERSION,
        "implementationVersion": IMPLEMENTATION_VERSION,
        "methodId": method_id,
        "corpusSha256": corpus_sha256,
        "evaluationRegistrySha256": evaluation_registry_sha256,
        "inputVariant": input_variant,
        "aspectId": aspect_id,
        "kValues": list(k_values),
        "verifiedPairCount": len(pairs),
        "positivePairCreationSource": "external governed verification only",
        "modelCreatedPositivePairCount": 0,
        "generatedTranslationCount": 0,
        "historicalRelationProduced": False,
        "probabilityProduced": False,
    }
    if not pairs:
        return {
            **base,
            "status": "NOT_RUN",
            "reason": "NO_MECHANICALLY_VERIFIED_CROSS_LANGUAGE_POSITIVES",
            "directionalQueryCount": 0,
            "metrics": None,
            "reviewRows": [],
            "reviewRowsTruncated": False,
        }

    directional: list[dict[str, Any]] = []
    for pair in pairs:
        for query_key, target_key, direction in (
            ("leftPublicObjectId", "rightPublicObjectId", "A_TO_B"),
            ("rightPublicObjectId", "leftPublicObjectId", "B_TO_A"),
        ):
            observation = index.rank_target(pair[query_key], pair[target_key])
            rank = observation.get("rank")
            score = observation.get("score")
            if not isinstance(rank, int) or rank <= 0:
                raise CrossLanguageEvalError("index returned an invalid target rank")
            if not isinstance(score, (int, float)) or not math.isfinite(float(score)):
                raise CrossLanguageEvalError("index returned an invalid score observation")
            directional.append(
                {
                    "pairId": pair["pairId"],
                    "direction": direction,
                    "queryPublicObjectId": pair[query_key],
                    "targetPublicObjectId": pair[target_key],
                    "rank": rank,
                    "cosineObservation": float(score),
                    "historicalRelation": False,
                    "semanticRelation": False,
                    "probability": False,
                }
            )
    ranks = [row["rank"] for row in directional]
    reciprocal = [1.0 / rank for rank in ranks]
    metrics = {
        "meanReciprocalRank": statistics_fmean(reciprocal),
        "medianRank": _median(ranks),
        "maximumRank": max(ranks),
        "meanCosineObservation": statistics_fmean(
            [row["cosineObservation"] for row in directional]
        ),
        **{
            f"recallAt{k}": sum(rank <= k for rank in ranks) / len(ranks)
            for k in k_values
        },
    }
    review = sorted(directional, key=lambda row: (-row["rank"], row["pairId"], row["direction"]))
    retained = review[:max_review_rows]
    return {
        **base,
        "status": "PASS",
        "directionalQueryCount": len(directional),
        "directionalObservationSha256": _sha256_json(directional),
        "metrics": metrics,
        "reviewRows": retained,
        "reviewRowsSha256": _sha256_json(retained),
        "reviewRowsTruncated": len(retained) < len(review),
    }


def statistics_fmean(values: Sequence[int | float]) -> float:
    return sum(float(value) for value in values) / len(values) if values else 0.0


def _median(values: Sequence[int | float]) -> float:
    ordered = sorted(float(value) for value in values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


class _SelfTestIndex:
    def __init__(self, corpus_sha256: str) -> None:
        self.object_ids = governance_common.load_public_ids()
        self.corpus_sha256 = corpus_sha256
        self.values = {
            ("SURF-A", "SURF-B"): (2, 0.8),
            ("SURF-B", "SURF-A"): (4, 0.7),
        }

    def rank_target(self, query_id: str, target_id: str) -> dict[str, Any]:
        rank, score = self.values[(query_id, target_id)]
        return {"rank": rank, "score": score}


def run_self_tests() -> dict[str, Any]:
    positive = {
        "pair_id": "NLP-PAIR-TEST",
        "public_object_id_a": "SURF-A",
        "public_object_id_b": "SURF-B",
        "task": "NLP_TASK_D_CROSS_LANGUAGE_CONSISTENCY",
        "pair_class": "VERIFIED_MULTILINGUAL_REPRESENTATION_POSITIVE",
        "verification_source": "SHA-pinned archive alternate-title identity",
        "verification_strength": "MECHANICAL_SOURCE_IDENTITY",
        "language_script": "Latin,Han",
    }
    registry_rows = governed_evaluation_registry.build_evaluation_registry()
    registry_sha = governed_evaluation_registry.evaluation_registry_sha256()
    not_run = evaluate_cross_language(
        _SelfTestIndex("a" * 64),
        registry_rows,
        method_id="NLP-TEST",
        corpus_sha256="a" * 64,
        evaluation_registry_sha256=registry_sha,
        input_variant="PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC",
        aspect_id="NLP_TITLE",
    )
    if not_run["status"] != "NOT_RUN":
        raise AssertionError("unverified control became a cross-language positive")
    try:
        evaluate_cross_language(
            _SelfTestIndex("a" * 64),
            [positive],
            method_id="NLP-TEST",
            corpus_sha256="a" * 64,
            evaluation_registry_sha256=registry_sha,
            input_variant="PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC",
            aspect_id="NLP_TITLE",
        )
    except CrossLanguageEvalError:
        pass
    else:
        raise AssertionError("caller-asserted positive bypassed the governed registry")
    return {
        "schemaVersion": "trace-nlp-cross-language-self-test/v1",
        "status": "PASS",
        "verifiedPairCount": 0,
        "callerAssertedPositiveRejected": True,
        "modelCreatedPositivePairCount": 0,
        "generatedTranslationCount": 0,
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
    raise SystemExit("cross-language evaluation requires an exact in-memory index")


if __name__ == "__main__":
    raise SystemExit(main())
