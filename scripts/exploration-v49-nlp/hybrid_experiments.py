#!/usr/bin/env python3
"""Analysis-only lexical/dense rank-fusion experiments.

Weights and a production hybrid are intentionally never selected here.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence


class HybridExperimentError(RuntimeError):
    """Raised when a bounded hybrid experiment is malformed."""


def _sha(value: Any) -> str:
    return hashlib.sha256(
        (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    ).hexdigest()


def reciprocal_rank_fusion(
    rankings: Mapping[str, Sequence[str]], *, constant: int = 60, limit: int = 50
) -> tuple[str, ...]:
    if len(rankings) < 2 or constant < 1 or limit < 1:
        raise HybridExperimentError("RRF requires two rankings and positive parameters")
    scores: dict[str, float] = {}
    for method_id in sorted(rankings):
        values = tuple(rankings[method_id])
        if len(values) != len(set(values)):
            raise HybridExperimentError("RRF input contains duplicate candidates")
        for rank, candidate_id in enumerate(values, start=1):
            scores[candidate_id] = scores.get(candidate_id, 0.0) + 1.0 / (constant + rank)
    return tuple(candidate_id for candidate_id, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit])


def evaluate_hybrid_grid(
    rankings_by_method: Mapping[str, Mapping[str, Sequence[str]]],
    *,
    positive_by_query: Mapping[str, Sequence[str]],
    constants: Sequence[int] = (10, 60, 100),
    evaluation_ks: Sequence[int] = (1, 5, 10, 20),
    output_limit: int = 50,
) -> dict[str, Any]:
    methods = tuple(sorted(rankings_by_method))
    if len(methods) < 2:
        raise HybridExperimentError("hybrid evaluation needs at least two methods")
    query_ids = sorted(set.intersection(*(set(rankings_by_method[m]) for m in methods)))
    rows: list[dict[str, Any]] = []
    for left_index, left in enumerate(methods):
        for right in methods[left_index + 1 :]:
            for constant in constants:
                hit_counts = {int(k): 0 for k in evaluation_ks}
                eligible = 0
                fused_hash_rows: list[tuple[str, tuple[str, ...]]] = []
                for query_id in query_ids:
                    positives = set(positive_by_query.get(query_id, ()))
                    if not positives:
                        continue
                    eligible += 1
                    fused = reciprocal_rank_fusion(
                        {left: rankings_by_method[left][query_id], right: rankings_by_method[right][query_id]},
                        constant=int(constant),
                        limit=output_limit,
                    )
                    fused_hash_rows.append((query_id, fused))
                    for k in evaluation_ks:
                        hit_counts[int(k)] += int(bool(set(fused[: int(k)]) & positives))
                for k in evaluation_ks:
                    rows.append(
                        {
                            "hybridId": f"RRF-{left}-{right}-K{constant}",
                            "leftMethodId": left,
                            "rightMethodId": right,
                            "rrfConstant": int(constant),
                            "evaluationK": int(k),
                            "eligibleQueryCount": eligible,
                            "knownItemRecall": hit_counts[int(k)] / eligible if eligible else None,
                            "rankingIdsSha256": _sha(fused_hash_rows),
                            "weightsSelected": False,
                            "productionSelected": False,
                            "historicalRelation": False,
                            "semanticRelation": False,
                            "probability": False,
                        }
                    )
    return {
        "schemaVersion": "trace-nlp-hybrid-experiments-v1",
        "methods": list(methods),
        "rows": rows,
        "rowCount": len(rows),
        "rowsSha256": _sha(rows),
        "hybridSelected": False,
        "fusionWeightsSelected": False,
    }


def self_test() -> dict[str, Any]:
    a = {"Q": ("A", "B", "C")}
    b = {"Q": ("B", "A", "C")}
    result = evaluate_hybrid_grid({"L": a, "D": b}, positive_by_query={"Q": ("A",)}, constants=(60,), evaluation_ks=(1, 2))
    if result["rowCount"] != 2 or result["rows"][1]["knownItemRecall"] != 1.0:
        raise HybridExperimentError("hybrid fixture failed")
    return {"status": "PASS", "checks": 2, "receiptSha256": _sha(result)}


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
