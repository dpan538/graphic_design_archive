#!/usr/bin/env python3
"""M0 raw-curated-Jaccard negative control.

This file is an explicit static/import boundary.  Production/frontend code and
scoring-eligible analysis modules must not import it.  Its only purpose is to
reproduce and document the known non-discriminative raw-curation failure.
"""

from __future__ import annotations

import json
import hashlib
import heapq
import math
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any


MODEL_ID = "M0"
MODEL_FAMILY = "RAW_CURATED_JACCARD_NEGATIVE_CONTROL"
ANALYSIS_ONLY = True
SCORING_ALLOWED = False
SHORTLIST_ELIGIBLE = False
PRODUCTION_IMPORT_ALLOWED = False


class NegativeControlError(ValueError):
    """Raised when the diagnostic input is malformed."""


@dataclass(frozen=True)
class PreparedCuratedNegativeControl:
    object_ids: tuple[str, ...]
    membership_bits: tuple[int, ...]
    membership_counts: tuple[int, ...]
    container_count: int
    prepared_sha256: str


def _members(record: Mapping[str, Any]) -> frozenset[str]:
    raw = record.get("curated_container")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise NegativeControlError("curated_container must be an array")
    values: set[str] = set()
    for value in raw:
        if isinstance(value, Mapping):
            identifier = str(value.get("id", "")).strip()
        else:
            identifier = str(value).strip()
        if not identifier:
            raise NegativeControlError("curated container identifier is blank")
        values.add(identifier)
    return frozenset(values)


def raw_curated_jaccard(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    left_values = _members(left)
    right_values = _members(right)
    shared = left_values & right_values
    union = left_values | right_values
    score = len(shared) / len(union) if union else 0.0
    return {
        "modelId": MODEL_ID,
        "diagnosticScore": score,
        "sharedContainerCount": len(shared),
        "unionContainerCount": len(union),
        "numerator": len(shared),
        "denominator": len(union),
        "diagnosticOnly": True,
        "scoringAllowed": False,
        "shortlistEligible": False,
        "productionImportAllowed": False,
        "historicalRelation": False,
        "semanticRelation": False,
        "probability": False,
    }


def prepare_curated_negative_control(
    records: Sequence[Mapping[str, Any]],
) -> PreparedCuratedNegativeControl:
    rows = sorted(
        ((str(record.get("objectId", "")), _members(record)) for record in records),
        key=lambda row: row[0],
    )
    object_ids = tuple(row[0] for row in rows)
    if any(not value for value in object_ids) or len(object_ids) != len(set(object_ids)):
        raise NegativeControlError("negative-control cohort identities are blank or duplicated")
    containers = tuple(sorted({value for _, memberships in rows for value in memberships}))
    ordinal = {value: index for index, value in enumerate(containers)}
    bits = tuple(
        sum(1 << ordinal[value] for value in memberships)
        for _, memberships in rows
    )
    counts = tuple(value.bit_count() for value in bits)
    material = {
        "modelId": MODEL_ID,
        "objectIds": object_ids,
        "membershipBitsHex": [format(value, "x") for value in bits],
        "analysisOnly": True,
        "productionImportAllowed": False,
    }
    digest = hashlib.sha256(
        (json.dumps(material, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    ).hexdigest()
    return PreparedCuratedNegativeControl(
        object_ids=object_ids,
        membership_bits=bits,
        membership_counts=counts,
        container_count=len(containers),
        prepared_sha256=digest,
    )


def _histogram_quantile(histogram: Mapping[tuple[int, int], int], probability: float) -> float:
    scored = sorted(
        ((shared / union if union else 0.0, count) for (shared, union), count in histogram.items()),
        key=lambda row: row[0],
    )
    total = sum(count for _, count in scored)
    if not total:
        return 0.0

    def at(index: int) -> float:
        cumulative = 0
        for score, count in scored:
            cumulative += count
            if cumulative > index:
                return score
        return scored[-1][0]

    position = (total - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return at(lower)
    low = at(lower)
    high = at(upper)
    return low + (high - low) * (position - lower)


def stream_exhaustive_m0_top_k(
    prepared: PreparedCuratedNegativeControl,
    *,
    k: int = 50,
    query_ids: Iterable[str] | None = None,
    block_size: int = 256,
    checkpoint: Callable[[Mapping[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Visit every unordered pair with compact bitsets and bounded heaps only."""

    if k <= 0 or block_size <= 0:
        raise NegativeControlError("k and block size must be positive")
    object_ids = prepared.object_ids
    n = len(object_ids)
    selected = set(object_ids if query_ids is None else (str(value) for value in query_ids))
    if not selected or selected - set(object_ids):
        raise NegativeControlError("negative-control query set is empty or outside the cohort")
    ordinals = {value: index for index, value in enumerate(object_ids)}
    heaps: dict[str, list[tuple[float, int, str]]] = {value: [] for value in sorted(selected)}
    histogram: Counter[tuple[int, int]] = Counter()
    pair_count = 0
    started = time.perf_counter()

    def push(query_id: str, candidate_id: str, score: float) -> None:
        entry = (score, -ordinals[candidate_id], candidate_id)
        heap = heaps[query_id]
        if len(heap) < k:
            heapq.heappush(heap, entry)
        elif entry[:2] > heap[0][:2]:
            heapq.heapreplace(heap, entry)

    for block_start in range(0, n, block_size):
        block_end = min(n, block_start + block_size)
        for left_ordinal in range(block_start, block_end):
            left_id = object_ids[left_ordinal]
            left_bits = prepared.membership_bits[left_ordinal]
            left_count = prepared.membership_counts[left_ordinal]
            for right_ordinal in range(left_ordinal + 1, n):
                right_id = object_ids[right_ordinal]
                shared = (left_bits & prepared.membership_bits[right_ordinal]).bit_count()
                union = left_count + prepared.membership_counts[right_ordinal] - shared
                score = shared / union if union else 0.0
                histogram[(shared, union)] += 1
                pair_count += 1
                if left_id in selected:
                    push(left_id, right_id, score)
                if right_id in selected:
                    push(right_id, left_id, score)
        if checkpoint is not None:
            checkpoint({
                "completedObjectPrefixCount": block_end,
                "objectCount": n,
                "unorderedPairVisits": pair_count,
                "pairRowsRetained": 0,
            })
    rankings = {
        query_id: tuple(
            (candidate_id, score)
            for score, _, candidate_id in sorted(heaps[query_id], key=lambda row: (-row[0], row[2]))
        )
        for query_id in sorted(selected)
    }
    hash_material = {
        "modelId": MODEL_ID,
        "preparedSha256": prepared.prepared_sha256,
        "k": k,
        "queryIds": sorted(selected),
        "rankings": rankings,
        "unorderedPairVisits": pair_count,
    }
    ranking_sha256 = hashlib.sha256(
        (json.dumps(hash_material, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    ).hexdigest()
    return {
        "modelId": MODEL_ID,
        "diagnosticOnly": True,
        "shortlistEligible": False,
        "productionImportAllowed": False,
        "objectCount": n,
        "queryCount": len(selected),
        "expectedPairCount": n * (n - 1) // 2,
        "unorderedPairVisits": pair_count,
        "k": k,
        "compactRankings": rankings,
        "rankingSha256": ranking_sha256,
        "scoreDistribution": {
            "p50": _histogram_quantile(histogram, 0.50),
            "p90": _histogram_quantile(histogram, 0.90),
            "p95": _histogram_quantile(histogram, 0.95),
            "p99": _histogram_quantile(histogram, 0.99),
            "max": max((shared / union if union else 0.0 for shared, union in histogram), default=0.0),
            "exactSupportUnionBinCount": len(histogram),
        },
        "elapsedMs": (time.perf_counter() - started) * 1000,
        "pairRowsRetained": 0,
        "fullPairMatrixMaterialized": False,
    }


def self_test() -> dict[str, Any]:
    token = lambda value: {"id": value, "label": value}
    result = raw_curated_jaccard(
        {"curated_container": [token("A"), token("B")]},
        {"curated_container": [token("B"), token("C")]},
    )
    if result["diagnosticScore"] != 1 / 3 or result["scoringAllowed"]:
        raise AssertionError("negative-control boundary failed")
    prepared = prepare_curated_negative_control(
        [
            {"objectId": "SURF-N1", "curated_container": [token("A"), token("B")]},
            {"objectId": "SURF-N2", "curated_container": [token("B"), token("C")]},
            {"objectId": "SURF-N3", "curated_container": [token("A")]},
        ]
    )
    streamed = stream_exhaustive_m0_top_k(prepared, k=2)
    if streamed["unorderedPairVisits"] != 3 or streamed["pairRowsRetained"] != 0:
        raise AssertionError("negative-control exhaustive streamer is not bounded/exact")
    return {
        "status": "PASS",
        "modelId": MODEL_ID,
        "analysisOnly": ANALYSIS_ONLY,
        "productionImportAllowed": PRODUCTION_IMPORT_ALLOWED,
        "exhaustiveStreamer": "PASS",
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
