#!/usr/bin/env python3
"""Bounded hubness and anisotropy diagnostics for TRACE NLP embeddings.

Diagnostics stream exact top-k queries and use algebraic or deterministic
bounded observations; they never create an all-pairs matrix.  High hubness or
anisotropy is reported as a research diagnostic, not an automatic rejection.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import statistics
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


SCHEMA_VERSION = "trace-nlp-hubness-anisotropy/v1"
IMPLEMENTATION_VERSION = "trace-nlp-hubness-anisotropy-2026-08-24"
DEFAULT_K_VALUES = (10, 20, 50)
MAX_K = 50
MAX_TOP_HUB_ROWS = 25
MAX_ANISOTROPY_PAIR_OBSERVATIONS = 20_000
REQUIRED_ASSOCIATION_DIMENSIONS = (
    "SOURCE",
    "LANGUAGE",
    "TEXT_LENGTH",
    "BOILERPLATE",
    "GENERIC_TITLE",
    "METADATA_COMPLETENESS",
)


class HubnessAnisotropyError(ValueError):
    """Raised when embeddings/rankings cannot support bounded diagnostics."""


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


def _quantile_r7(values: Sequence[int | float], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _distribution(values: Sequence[int | float]) -> dict[str, Any]:
    numeric = [float(value) for value in values]
    if not numeric or any(not math.isfinite(value) for value in numeric):
        raise HubnessAnisotropyError("diagnostic distribution is empty or non-finite")
    return {
        "count": len(numeric),
        "minimum": min(numeric),
        "p01": _quantile_r7(numeric, 0.01),
        "p05": _quantile_r7(numeric, 0.05),
        "p50": _quantile_r7(numeric, 0.50),
        "p95": _quantile_r7(numeric, 0.95),
        "p99": _quantile_r7(numeric, 0.99),
        "maximum": max(numeric),
        "mean": statistics.fmean(numeric),
        "standardDeviation": statistics.pstdev(numeric),
    }


def _categorical_association(
    object_ids: Sequence[str],
    occurrences: Sequence[int],
    labels: Mapping[str, Any],
    *,
    dimension: str,
    k: int,
) -> dict[str, Any]:
    missing = [object_id for object_id in object_ids if object_id not in labels]
    if missing:
        raise HubnessAnisotropyError(f"{dimension} association labels are incomplete")
    groups: dict[str, list[float]] = {}
    for object_id, occurrence in zip(object_ids, occurrences):
        label = str(labels[object_id]).strip()
        if not label:
            raise HubnessAnisotropyError(f"{dimension} association contains a blank label")
        groups.setdefault(label, []).append(float(occurrence))
    overall = statistics.fmean(occurrences)
    total_ss = sum((float(value) - overall) ** 2 for value in occurrences)
    between_ss = sum(
        len(values) * (statistics.fmean(values) - overall) ** 2
        for values in groups.values()
    )
    group_summary = [
        [label, len(values), statistics.fmean(values)]
        for label, values in sorted(groups.items())
    ]
    return {
        "dimension": dimension,
        "associationType": "CATEGORICAL_ETA_SQUARED",
        "k": k,
        "objectCount": len(object_ids),
        "groupCount": len(groups),
        "etaSquared": between_ss / total_ss if total_ss else 0.0,
        "groupSummarySha256": _sha256_json(group_summary),
        "fullGroupRowsRetained": False,
    }


def _numeric_association(
    object_ids: Sequence[str],
    occurrences: Sequence[int],
    values_by_object: Mapping[str, Any],
    *,
    dimension: str,
    k: int,
) -> dict[str, Any]:
    missing = [object_id for object_id in object_ids if object_id not in values_by_object]
    if missing:
        raise HubnessAnisotropyError(f"{dimension} association values are incomplete")
    values = [float(values_by_object[object_id]) for object_id in object_ids]
    if any(not math.isfinite(value) for value in values):
        raise HubnessAnisotropyError(f"{dimension} association contains a non-finite value")
    left_mean = statistics.fmean(values)
    right = [float(value) for value in occurrences]
    right_mean = statistics.fmean(right)
    numerator = sum(
        (left - left_mean) * (observed - right_mean)
        for left, observed in zip(values, right)
    )
    denominator = math.sqrt(
        sum((value - left_mean) ** 2 for value in values)
        * sum((value - right_mean) ** 2 for value in right)
    )
    return {
        "dimension": dimension,
        "associationType": "PEARSON_CORRELATION",
        "k": k,
        "objectCount": len(object_ids),
        "pearsonCorrelation": numerator / denominator if denominator else 0.0,
        "valueDistribution": _distribution(values),
    }


def _first_pc_variance_share(vectors: Any, *, iterations: int = 32) -> dict[str, Any]:
    np = importlib.import_module("numpy")
    numeric = vectors.astype(np.float64)
    centered = numeric - numeric.mean(axis=0)
    total_variance = float(np.einsum("ij,ij->", centered, centered))
    if total_variance == 0.0:
        return {
            "share": 0.0,
            "method": "DETERMINISTIC_POWER_ITERATION",
            "iterations": 0,
            "convergedVectorNorm": 0.0,
        }
    direction = np.arange(1, centered.shape[1] + 1, dtype=np.float64)
    direction /= np.linalg.norm(direction)
    completed = 0
    for completed in range(1, iterations + 1):
        updated = centered.T @ (centered @ direction)
        norm = float(np.linalg.norm(updated))
        if norm == 0.0:
            break
        direction = updated / norm
    projection = centered @ direction
    explained = float(projection @ projection)
    return {
        "share": min(1.0, max(0.0, explained / total_variance)),
        "method": "DETERMINISTIC_POWER_ITERATION",
        "iterations": completed,
        "convergedVectorNorm": float(np.linalg.norm(direction)),
    }


def _gini(values: Sequence[int | float]) -> float:
    ordered = sorted(float(value) for value in values)
    total = sum(ordered)
    n = len(ordered)
    if not n or total == 0:
        return 0.0
    weighted = sum((index + 1) * value for index, value in enumerate(ordered))
    return (2.0 * weighted) / (n * total) - (n + 1.0) / n


def _skewness(values: Sequence[int | float]) -> float:
    if not values:
        return 0.0
    mean = statistics.fmean(values)
    variance = statistics.fmean((float(value) - mean) ** 2 for value in values)
    if variance == 0:
        return 0.0
    third = statistics.fmean((float(value) - mean) ** 3 for value in values)
    return third / variance**1.5


def _candidate_id(row: Any) -> str:
    if isinstance(row, Mapping):
        value = row.get("candidatePublicId", row.get("candidateId"))
    elif isinstance(row, str):
        value = row
    else:
        raise HubnessAnisotropyError("ranking row lacks a public candidate ID")
    value = str(value or "")
    if not value:
        raise HubnessAnisotropyError("ranking row lacks a public candidate ID")
    return value


def evaluate_hubness(
    index: Any,
    *,
    query_ids: Iterable[str] | None = None,
    k_values: Sequence[int] = DEFAULT_K_VALUES,
    top_hub_rows: int = MAX_TOP_HUB_ROWS,
    source_by_object: Mapping[str, Any] | None = None,
    language_by_object: Mapping[str, Any] | None = None,
    text_length_by_object: Mapping[str, Any] | None = None,
    boilerplate_by_object: Mapping[str, Any] | None = None,
    generic_title_by_object: Mapping[str, Any] | None = None,
    metadata_completeness_by_object: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    object_ids = tuple(getattr(index, "available_object_ids", index.object_ids))
    queries = tuple(sorted(set(query_ids or object_ids)))
    if not object_ids or not queries or any(value not in set(object_ids) for value in queries):
        raise HubnessAnisotropyError("hubness cohort is empty or outside the index")
    if tuple(sorted(set(k_values))) != tuple(k_values) or any(
        k <= 0 or k > MAX_K or k >= len(object_ids) for k in k_values
    ):
        raise HubnessAnisotropyError("hubness k values are invalid")
    if not 0 <= top_hub_rows <= MAX_TOP_HUB_ROWS:
        raise HubnessAnisotropyError("top-hub row bound exceeds 25")
    counts_by_k = {k: Counter() for k in k_values}
    maximum_k = max(k_values)
    for query_id in queries:
        ranking = index.query_id(query_id, top_k=maximum_k)
        seen: set[str] = set()
        for ordinal, row in enumerate(ranking, start=1):
            candidate_id = _candidate_id(row)
            if candidate_id == query_id or candidate_id in seen:
                raise HubnessAnisotropyError("hubness ranking contains self/duplicate")
            seen.add(candidate_id)
            for k in k_values:
                if ordinal <= k:
                    counts_by_k[k][candidate_id] += 1
    rows: list[dict[str, Any]] = []
    top_rows: dict[str, list[dict[str, Any]]] = {}
    reliable_language_labels = language_by_object
    if language_by_object is not None and any(
        str(value).startswith("SCRIPT_STATE_ONLY:")
        for value in language_by_object.values()
    ):
        reliable_language_labels = None
    association_inputs = {
        "SOURCE": source_by_object,
        "LANGUAGE": reliable_language_labels,
        "TEXT_LENGTH": text_length_by_object,
        "BOILERPLATE": boilerplate_by_object,
        "GENERIC_TITLE": generic_title_by_object,
        "METADATA_COMPLETENESS": metadata_completeness_by_object,
    }
    missing_associations = [
        dimension for dimension, values in association_inputs.items() if values is None
    ]
    association_rows: list[dict[str, Any]] = []
    for k in k_values:
        counts = counts_by_k[k]
        values = [counts[object_id] for object_id in object_ids]
        total = sum(values)
        top_one_percent = max(1, math.ceil(len(values) * 0.01))
        ordered = sorted(
            ((object_id, counts[object_id]) for object_id in object_ids),
            key=lambda item: (-item[1], item[0]),
        )
        retained = ordered[:top_hub_rows]
        top_rows[str(k)] = [
            {"publicObjectId": object_id, "kOccurrenceCount": count}
            for object_id, count in retained
        ]
        rows.append(
            {
                "k": k,
                "objectCount": len(object_ids),
                "queryCount": len(queries),
                "meanKOccurrence": statistics.fmean(values),
                "varianceKOccurrence": statistics.pvariance(values),
                "skewness": _skewness(values),
                "gini": _gini(values),
                "top1PercentOccurrenceShare": (
                    sum(sorted(values, reverse=True)[:top_one_percent]) / total
                    if total
                    else 0.0
                ),
                "maximumOccurrence": max(values),
                "zeroOccurrenceObjectCount": sum(value == 0 for value in values),
                "totalOccurrenceCount": total,
                "expectedOccurrenceCount": len(queries) * k,
            }
        )
        if total != len(queries) * k:
            raise HubnessAnisotropyError("hubness occurrence accounting failed")
        for dimension, labels in association_inputs.items():
            if labels is None:
                continue
            if dimension in {"TEXT_LENGTH", "METADATA_COMPLETENESS"}:
                association_rows.append(
                    _numeric_association(
                        object_ids,
                        values,
                        labels,
                        dimension=dimension,
                        k=k,
                    )
                )
            else:
                association_rows.append(
                    _categorical_association(
                        object_ids,
                        values,
                        labels,
                        dimension=dimension,
                        k=k,
                    )
                )
    return {
        "kValues": list(k_values),
        "rows": rows,
        "topHubRows": top_rows,
        "topHubRowLimitPerK": top_hub_rows,
        "fullOccurrenceVectorsRetained": False,
        "requiredAssociationDimensions": list(REQUIRED_ASSOCIATION_DIMENSIONS),
        "associationStatus": "PASS" if not missing_associations else "NOT_RUN",
        "missingAssociationDimensions": missing_associations,
        "associationRows": association_rows,
        "associationRowsSha256": _sha256_json(association_rows),
        "hubnessIsDiagnosticNotAutomaticDisqualification": True,
    }


def _deterministic_pairs(object_ids: Sequence[str], limit: int) -> tuple[tuple[int, int], ...]:
    n = len(object_ids)
    possible = n * (n - 1) // 2
    target = min(limit, possible)
    if target <= 0:
        return ()
    pairs: set[tuple[int, int]] = set()
    salt = 0
    # Stable hash-derived partners provide a broad, seedless observation set.
    while len(pairs) < target:
        before = len(pairs)
        for left, object_id in enumerate(object_ids):
            digest = hashlib.sha256(
                f"{SCHEMA_VERSION}\0{salt}\0{object_id}".encode("utf-8")
            ).digest()
            right = int.from_bytes(digest[:8], "big") % (n - 1)
            if right >= left:
                right += 1
            pair = (left, right) if left < right else (right, left)
            pairs.add(pair)
            if len(pairs) >= target:
                break
        salt += 1
        if len(pairs) == before or salt > max(16, target * 2):
            # Deterministic lexicographic completion is a total fallback for
            # tiny/high-collision cohorts, never a random sample.
            for left in range(n):
                for right in range(left + 1, n):
                    pairs.add((left, right))
                    if len(pairs) >= target:
                        break
                if len(pairs) >= target:
                    break
    return tuple(sorted(pairs))


def evaluate_anisotropy(
    index: Any,
    *,
    maximum_pair_observations: int = MAX_ANISOTROPY_PAIR_OBSERVATIONS,
    pre_normalization_norms: Sequence[int | float] | None = None,
) -> dict[str, Any]:
    np = importlib.import_module("numpy")
    all_vectors = np.asarray(index.vectors, dtype=np.float32)
    if hasattr(index, "availability_mask"):
        vectors = all_vectors[np.asarray(index.availability_mask, dtype=np.bool_)]
        object_ids = tuple(index.available_object_ids)
    else:
        vectors = all_vectors
        object_ids = tuple(index.object_ids)
    if vectors.ndim != 2 or vectors.shape[0] != len(object_ids) or len(object_ids) < 2:
        raise HubnessAnisotropyError("anisotropy requires at least two indexed vectors")
    if not 1 <= maximum_pair_observations <= MAX_ANISOTROPY_PAIR_OBSERVATIONS:
        raise HubnessAnisotropyError("anisotropy observation bound is invalid")
    vectors64 = vectors.astype(np.float64)
    post_norms = np.linalg.norm(vectors64, axis=1)
    if not np.allclose(post_norms, 1.0, rtol=0.0, atol=2e-4):
        raise HubnessAnisotropyError("anisotropy input is not L2-normalized")
    if pre_normalization_norms is None:
        pre_norm_distribution = None
        missing_required_inputs = ["PRE_NORMALIZATION_NORMS"]
    else:
        pre_norms = [float(value) for value in pre_normalization_norms]
        if len(pre_norms) != len(object_ids) or any(
            not math.isfinite(value) or value <= 0 for value in pre_norms
        ):
            raise HubnessAnisotropyError("pre-normalization norms are invalid")
        pre_norm_distribution = _distribution(pre_norms)
        missing_required_inputs = []

    # For normalized vectors the exact off-diagonal mean cosine follows from
    # ||sum(x_i)||^2, so no pair matrix is needed.
    vector_sum = vectors64.sum(axis=0)
    n = len(object_ids)
    sum_squared_norms = float(np.einsum("ij,ij->", vectors64, vectors64))
    exact_mean_pair_cosine = (
        float(vector_sum @ vector_sum) - sum_squared_norms
    ) / (n * (n - 1))
    centroid = vectors64.mean(axis=0)
    pairs = _deterministic_pairs(object_ids, maximum_pair_observations)
    observations = [
        float(vectors64[left] @ vectors64[right])
        for left, right in pairs
    ]
    pair_material = [
        [object_ids[left], object_ids[right]] for left, right in pairs
    ]
    nearest_neighbor_distances: list[float] = []
    for object_id in object_ids:
        ranking = index.query_id(object_id, top_k=1)
        if len(ranking) != 1 or not isinstance(ranking[0], Mapping):
            raise HubnessAnisotropyError("nearest-neighbor diagnostic lacks a ranking row")
        score = ranking[0].get("score")
        if not isinstance(score, (int, float)) or not math.isfinite(float(score)):
            raise HubnessAnisotropyError("nearest-neighbor diagnostic lacks a finite cosine")
        nearest_neighbor_distances.append(1.0 - float(score))
    first_pc = _first_pc_variance_share(vectors)
    return {
        "status": "PASS" if not missing_required_inputs else "NOT_RUN",
        "reason": (
            None
            if not missing_required_inputs
            else "REQUIRED_PRE_NORMALIZATION_NORMS_UNAVAILABLE"
        ),
        "missingRequiredInputs": missing_required_inputs,
        "objectCount": n,
        "embeddingDimension": int(vectors.shape[1]),
        "centroidNorm": float(np.linalg.norm(centroid)),
        "exactMeanOffDiagonalCosine": exact_mean_pair_cosine,
        "pairObservationMethod": "stable SHA-256 partner mapping with lexicographic completion",
        "pairObservationCount": len(observations),
        "pairSelectionSha256": _sha256_json(pair_material),
        "pairCosineObservationSha256": _sha256_json(observations),
        "sampleCosineMean": statistics.fmean(observations),
        "sampleCosineStdDev": statistics.pstdev(observations),
        "sampleCosineP01": _quantile_r7(observations, 0.01),
        "sampleCosineP05": _quantile_r7(observations, 0.05),
        "sampleCosineP50": _quantile_r7(observations, 0.50),
        "sampleCosineP95": _quantile_r7(observations, 0.95),
        "sampleCosineP99": _quantile_r7(observations, 0.99),
        "nearestNeighborCosineDistanceDistribution": _distribution(
            nearest_neighbor_distances
        ),
        "preNormalizationNormDistribution": pre_norm_distribution,
        "postNormalizationNormDistribution": _distribution(post_norms.tolist()),
        "firstPrincipalComponentExplainedVarianceShare": first_pc["share"],
        "firstPrincipalComponentMethod": first_pc["method"],
        "firstPrincipalComponentIterations": first_pc["iterations"],
        "firstPrincipalComponentVectorNorm": first_pc["convergedVectorNorm"],
        "pairMatrixMaterialized": False,
        "anisotropyIsDiagnosticNotAutomaticDisqualification": True,
    }


def evaluate_hubness_and_anisotropy(
    index: Any,
    *,
    method_id: str,
    corpus_sha256: str,
    input_variant: str,
    aspect_id: str,
    query_ids: Iterable[str] | None = None,
    k_values: Sequence[int] = DEFAULT_K_VALUES,
    source_by_object: Mapping[str, Any] | None = None,
    language_by_object: Mapping[str, Any] | None = None,
    text_length_by_object: Mapping[str, Any] | None = None,
    boilerplate_by_object: Mapping[str, Any] | None = None,
    generic_title_by_object: Mapping[str, Any] | None = None,
    metadata_completeness_by_object: Mapping[str, Any] | None = None,
    pre_normalization_norms: Sequence[int | float] | None = None,
    require_complete: bool = False,
) -> dict[str, Any]:
    hubness = evaluate_hubness(
        index,
        query_ids=query_ids,
        k_values=k_values,
        source_by_object=source_by_object,
        language_by_object=language_by_object,
        text_length_by_object=text_length_by_object,
        boilerplate_by_object=boilerplate_by_object,
        generic_title_by_object=generic_title_by_object,
        metadata_completeness_by_object=metadata_completeness_by_object,
    )
    anisotropy = evaluate_anisotropy(
        index, pre_normalization_norms=pre_normalization_norms
    )
    complete = (
        hubness["associationStatus"] == "PASS" and anisotropy["status"] == "PASS"
    )
    missing = [
        *hubness["missingAssociationDimensions"],
        *anisotropy["missingRequiredInputs"],
    ]
    if require_complete and not complete:
        raise HubnessAnisotropyError(
            "completed hubness/anisotropy claim lacks required diagnostics: "
            + ", ".join(missing)
        )
    material = {
        "schemaVersion": SCHEMA_VERSION,
        "implementationVersion": IMPLEMENTATION_VERSION,
        "status": "PASS" if complete else "NOT_RUN",
        "reason": None if complete else "REQUIRED_DIAGNOSTIC_INPUTS_UNAVAILABLE",
        "missingRequiredDiagnostics": missing,
        "coreDiagnosticsComputed": True,
        "methodId": method_id,
        "corpusSha256": corpus_sha256,
        "inputVariant": input_variant,
        "aspectId": aspect_id,
        "indexSha256": index.index_sha256,
        "hubness": hubness,
        "anisotropy": anisotropy,
        "hubnessReportOmitted": False,
        "seedUsed": False,
        "historicalRelationProduced": False,
        "probabilityProduced": False,
    }
    return {**material, "diagnosticSha256": _sha256_json(material)}


def run_self_tests() -> dict[str, Any]:
    np = importlib.import_module("numpy")

    class FixtureIndex:
        def __init__(self, ids: Sequence[str], vectors: Any) -> None:
            self.object_ids = tuple(ids)
            self.available_object_ids = tuple(ids)
            self.vectors = np.asarray(vectors, dtype=np.float32)
            self.availability_mask = np.ones(len(ids), dtype=np.bool_)
            self.index_sha256 = _sha256_json(
                [self.object_ids, self.vectors.astype("<f4").tolist()]
            )

        def query_id(self, query_id: str, *, top_k: int) -> tuple[dict[str, Any], ...]:
            query_ordinal = self.object_ids.index(query_id)
            scores = self.vectors @ self.vectors[query_ordinal]
            order = sorted(
                (ordinal for ordinal in range(len(self.object_ids)) if ordinal != query_ordinal),
                key=lambda ordinal: (-float(scores[ordinal]), self.object_ids[ordinal]),
            )[:top_k]
            return tuple(
                {
                    "rank": rank,
                    "candidatePublicId": self.object_ids[ordinal],
                    "score": float(scores[ordinal]),
                }
                for rank, ordinal in enumerate(order, start=1)
            )

    ids = ("SURF-A", "SURF-B", "SURF-C", "SURF-D")
    vectors = np.eye(4, dtype=np.float32)
    index = FixtureIndex(ids, vectors)
    associations = {
        "source_by_object": {"SURF-A": "S1", "SURF-B": "S1", "SURF-C": "S2", "SURF-D": "S2"},
        "language_by_object": {"SURF-A": "en", "SURF-B": "fr", "SURF-C": "en", "SURF-D": "fr"},
        "text_length_by_object": {value: ordinal + 1 for ordinal, value in enumerate(ids)},
        "boilerplate_by_object": {"SURF-A": False, "SURF-B": False, "SURF-C": True, "SURF-D": True},
        "generic_title_by_object": {
            "SURF-A": True,
            "SURF-B": False,
            "SURF-C": False,
            "SURF-D": True,
        },
        "metadata_completeness_by_object": {
            value: (ordinal + 1) / 4 for ordinal, value in enumerate(ids)
        },
    }
    hubness = evaluate_hubness(
        index, k_values=(1, 2), top_hub_rows=2, **associations
    )
    if any(
        row["totalOccurrenceCount"] != row["expectedOccurrenceCount"]
        for row in hubness["rows"]
    ):
        raise AssertionError("hubness occurrence conservation changed")
    if hubness["associationStatus"] != "PASS" or len(hubness["associationRows"]) != 12:
        raise AssertionError("required hubness associations were omitted")
    proxy_associations = dict(associations)
    proxy_associations["language_by_object"] = {
        value: "SCRIPT_STATE_ONLY:LATIN" for value in ids
    }
    proxy_hubness = evaluate_hubness(
        index, k_values=(1, 2), top_hub_rows=2, **proxy_associations
    )
    if (
        proxy_hubness["associationStatus"] != "NOT_RUN"
        or "LANGUAGE" not in proxy_hubness["missingAssociationDimensions"]
    ):
        raise AssertionError("script-state proxy masqueraded as language")
    anisotropy = evaluate_anisotropy(
        index, maximum_pair_observations=6, pre_normalization_norms=(1, 1, 1, 1)
    )
    if anisotropy["exactMeanOffDiagonalCosine"] != 0.0:
        raise AssertionError("orthogonal anisotropy baseline changed")
    if (
        anisotropy["pairObservationCount"] != 6
        or anisotropy["status"] != "PASS"
        or anisotropy["nearestNeighborCosineDistanceDistribution"]["count"] != 4
        or anisotropy["preNormalizationNormDistribution"] is None
        or anisotropy["postNormalizationNormDistribution"]["count"] != 4
        or not 0.0 <= anisotropy["firstPrincipalComponentExplainedVarianceShare"] <= 1.0
    ):
        raise AssertionError("deterministic pair completion changed")
    complete = evaluate_hubness_and_anisotropy(
        index,
        method_id="FIXTURE",
        corpus_sha256="a" * 64,
        input_variant="FIXTURE",
        aspect_id="NLP_TITLE",
        k_values=(1, 2),
        pre_normalization_norms=(1, 1, 1, 1),
        require_complete=True,
        **associations,
    )
    if complete["status"] != "PASS":
        raise AssertionError("complete diagnostic inputs did not produce PASS")
    incomplete = evaluate_hubness_and_anisotropy(
        index,
        method_id="FIXTURE",
        corpus_sha256="a" * 64,
        input_variant="FIXTURE",
        aspect_id="NLP_TITLE",
        k_values=(1, 2),
    )
    if incomplete["status"] != "NOT_RUN" or not incomplete["missingRequiredDiagnostics"]:
        raise AssertionError("incomplete diagnostics produced a false PASS")
    scaled = FixtureIndex(
        ("SURF-A", "SURF-B"),
        np.asarray([[1.0001, 0.0], [0.0, 1.0001]], dtype=np.float32),
    )
    corrected = evaluate_anisotropy(
        scaled,
        maximum_pair_observations=1,
        pre_normalization_norms=(1.0001, 1.0001),
    )
    if not math.isclose(
        corrected["exactMeanOffDiagonalCosine"], 0.0, rel_tol=0.0, abs_tol=1e-15
    ):
        raise AssertionError("exact off-diagonal mean still assumes exact unit norms")
    return {
        "schemaVersion": "trace-nlp-hubness-anisotropy-self-test/v1",
        "status": "PASS",
        "hubnessKValues": [1, 2],
        "pairObservationCount": 6,
        "associationRowCount": len(hubness["associationRows"]),
        "scriptStateLanguageProxyRejected": True,
        "nearestNeighborDistanceDistribution": "PASS",
        "normDistributions": "PASS",
        "firstPrincipalComponentShare": "PASS",
        "incompleteClaimStatus": incomplete["status"],
        "nonUnitNormExactMeanAdversary": "PASS",
        "pairMatrixMaterialized": False,
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
    raise SystemExit("hubness/anisotropy evaluation requires an exact in-memory index")


if __name__ == "__main__":
    raise SystemExit(main())
