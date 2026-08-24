#!/usr/bin/env python3
"""Bounded aspect-neighborhood disagreement diagnostics for Round 7.

This module never fuses aspects and never retains cross-object pair rows.  It
accepts already-bounded rankings and emits aggregate, explanation-safe rows.
"""

from __future__ import annotations

import hashlib
import json
import math
from itertools import combinations
from typing import Any, Mapping, Sequence


class AspectDisagreementError(RuntimeError):
    """Raised when a bounded ranking contract is malformed."""


def _sha(value: Any) -> str:
    payload = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_rankings(
    rankings: Mapping[str, Mapping[str, Sequence[str]]], *, k: int
) -> tuple[str, ...]:
    if k < 1 or k > 100:
        raise AspectDisagreementError("k must be between 1 and 100")
    if len(rankings) < 2:
        raise AspectDisagreementError("at least two aspect rankings are required")
    query_sets: list[set[str]] = []
    for aspect_id, by_query in rankings.items():
        if not aspect_id or not isinstance(by_query, Mapping):
            raise AspectDisagreementError("aspect ranking is malformed")
        query_sets.append(set(by_query))
        for query_id, candidates in by_query.items():
            values = tuple(candidates[:k])
            if query_id in values or len(values) != len(set(values)):
                raise AspectDisagreementError("ranking contains self or duplicate candidates")
    return tuple(sorted(set.intersection(*query_sets))) if query_sets else ()


def analyze_aspect_disagreement(
    rankings: Mapping[str, Mapping[str, Sequence[str]]],
    *,
    model_id: str,
    k: int = 20,
    source_by_object: Mapping[str, str] | None = None,
    language_by_object: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Compare each aspect pair without creating a combined affinity score."""

    query_ids = _validate_rankings(rankings, k=k)
    rows: list[dict[str, Any]] = []
    for aspect_a, aspect_b in combinations(sorted(rankings), 2):
        overlaps: list[float] = []
        correlations: list[float] = []
        source_rates_a: list[float] = []
        source_rates_b: list[float] = []
        language_rates_a: list[float] = []
        language_rates_b: list[float] = []
        for query_id in query_ids:
            ids_a = tuple(rankings[aspect_a][query_id][:k])
            ids_b = tuple(rankings[aspect_b][query_id][:k])
            set_a, set_b = set(ids_a), set(ids_b)
            overlaps.append(len(set_a & set_b) / k)
            common = set_a & set_b
            if len(common) >= 2:
                pos_a = {value: index for index, value in enumerate(ids_a, start=1)}
                pos_b = {value: index for index, value in enumerate(ids_b, start=1)}
                left = [pos_a[value] for value in sorted(common)]
                right = [pos_b[value] for value in sorted(common)]
                mean_left = sum(left) / len(left)
                mean_right = sum(right) / len(right)
                numerator = sum((x - mean_left) * (y - mean_right) for x, y in zip(left, right))
                denominator = math.sqrt(
                    sum((x - mean_left) ** 2 for x in left)
                    * sum((y - mean_right) ** 2 for y in right)
                )
                correlations.append(numerator / denominator if denominator else 0.0)
            if source_by_object and query_id in source_by_object:
                source = source_by_object[query_id]
                source_rates_a.append(sum(source_by_object.get(value) == source for value in ids_a) / k)
                source_rates_b.append(sum(source_by_object.get(value) == source for value in ids_b) / k)
            if language_by_object and query_id in language_by_object:
                language = language_by_object[query_id]
                if language not in {"", "UNDETERMINED", "MIXED"}:
                    language_rates_a.append(sum(language_by_object.get(value) == language for value in ids_a) / k)
                    language_rates_b.append(sum(language_by_object.get(value) == language for value in ids_b) / k)
        rows.append(
            {
                "modelId": model_id,
                "aspectA": aspect_a,
                "aspectB": aspect_b,
                "k": k,
                "jointQueryCount": len(query_ids),
                "meanTopKOverlap": sum(overlaps) / len(overlaps) if overlaps else None,
                "meanCommonRankCorrelation": sum(correlations) / len(correlations) if correlations else None,
                "sourceNeighborRateA": sum(source_rates_a) / len(source_rates_a) if source_rates_a else None,
                "sourceNeighborRateB": sum(source_rates_b) / len(source_rates_b) if source_rates_b else None,
                "languageNeighborRateA": sum(language_rates_a) / len(language_rates_a) if language_rates_a else None,
                "languageNeighborRateB": sum(language_rates_b) / len(language_rates_b) if language_rates_b else None,
                "affinityFused": False,
                "historicalRelation": False,
                "semanticRelation": False,
                "probability": False,
            }
        )
    return {
        "schemaVersion": "trace-nlp-aspect-disagreement-v1",
        "modelId": model_id,
        "k": k,
        "rows": rows,
        "rowCount": len(rows),
        "queryCount": len(query_ids),
        "rowsSha256": _sha(rows),
        "aspectFusionSelected": False,
    }


def self_test() -> dict[str, Any]:
    rankings = {
        "NLP_TITLE": {"A": ("B", "C"), "B": ("A", "C")},
        "NLP_SUBJECT": {"A": ("C", "B"), "B": ("C", "A")},
    }
    result = analyze_aspect_disagreement(rankings, model_id="FIXTURE", k=2)
    if result["rowCount"] != 1 or result["rows"][0]["meanTopKOverlap"] != 1.0:
        raise AspectDisagreementError("aspect fixture failed")
    return {"status": "PASS", "checks": 2, "receiptSha256": _sha(result)}


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
