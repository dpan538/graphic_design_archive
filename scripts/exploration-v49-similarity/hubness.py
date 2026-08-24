#!/usr/bin/env python3
"""Deterministic hubness, source-bias, and family-dominance diagnostics."""

from __future__ import annotations

import json
import math
import statistics
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


SCHEMA_VERSION = "trace-exploration-hubness/v1"
IMPLEMENTATION_VERSION = "trace-exploration-hubness-2026-08-24"
HUBNESS_K_VALUES = (10, 20, 50)
HUBNESS_CORRECTIONS = (
    "LOCAL_SCALING",
    "GLOBAL_SCALING_STYLE",
    "RECIPROCAL_NEIGHBOR_FILTER",
)


class HubnessError(ValueError):
    """Raised when rankings cannot support a valid hubness diagnostic."""


def _candidate_id(row: Any) -> str:
    if isinstance(row, str):
        value = row
    elif isinstance(row, Mapping):
        value = str(row.get("candidateId", ""))
    elif isinstance(row, Sequence) and not isinstance(row, (str, bytes, bytearray)) and row:
        value = str(row[0])
    else:
        raise HubnessError("ranking rows must be candidate IDs or mappings")
    if not value:
        raise HubnessError("ranking row lacks candidate identity")
    return value


def _score(row: Any) -> float:
    if isinstance(row, Mapping):
        value = row.get("diagnosticScore")
    elif isinstance(row, Sequence) and not isinstance(row, (str, bytes, bytearray)) and len(row) >= 2:
        value = row[1]
    else:
        raise HubnessError("score transformation requires ranking mappings or compact tuples")
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        raise HubnessError("ranking row lacks a finite diagnostic score")
    return float(value)


def _gini(values: Sequence[int | float]) -> float:
    ordered = sorted(float(value) for value in values)
    n = len(ordered)
    total = sum(ordered)
    if not n or total == 0:
        return 0.0
    weighted = sum((index + 1) * value for index, value in enumerate(ordered))
    return (2 * weighted) / (n * total) - (n + 1) / n


def _skewness(values: Sequence[int | float]) -> float:
    if not values:
        return 0.0
    mean = statistics.fmean(values)
    second = statistics.fmean((value - mean) ** 2 for value in values)
    if second == 0:
        return 0.0
    third = statistics.fmean((value - mean) ** 3 for value in values)
    return third / (second ** 1.5)


def _quantile_r7(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def k_occurrence_distribution(
    rankings: Mapping[str, Sequence[Any]],
    *,
    cohort_ids: Iterable[str] | None = None,
    k_values: Sequence[int] = HUBNESS_K_VALUES,
) -> dict[str, Any]:
    if not rankings:
        raise HubnessError("hubness requires at least one query ranking")
    if any(k <= 0 for k in k_values):
        raise HubnessError("hubness k values must be positive")
    cohort = tuple(sorted(set(cohort_ids or rankings.keys())))
    if not cohort:
        raise HubnessError("hubness cohort is empty")
    cohort_set = set(cohort)
    rows: list[dict[str, Any]] = []
    count_vectors: dict[str, dict[str, int]] = {}
    for k in k_values:
        occurrences: Counter[str] = Counter()
        for query_id in sorted(rankings):
            seen: set[str] = set()
            for raw in rankings[query_id][:k]:
                candidate_id = _candidate_id(raw)
                if candidate_id == query_id:
                    raise HubnessError("self appears in a hubness ranking")
                if candidate_id not in cohort_set:
                    raise HubnessError("ranking candidate is outside the declared cohort")
                if candidate_id in seen:
                    raise HubnessError("ranking contains a duplicate candidate")
                seen.add(candidate_id)
                occurrences[candidate_id] += 1
        values = [occurrences[object_id] for object_id in cohort]
        total = sum(values)
        top_count = max(1, math.ceil(len(values) * 0.01))
        top_share = sum(sorted(values, reverse=True)[:top_count]) / total if total else 0.0
        rows.append({
            "k": k,
            "objectCount": len(cohort),
            "queryCount": len(rankings),
            "mean": statistics.fmean(values),
            "variance": statistics.pvariance(values),
            "skewness": _skewness(values),
            "gini": _gini(values),
            "top1PercentOccurrenceShare": top_share,
            "maximumOccurrence": max(values),
            "zeroOccurrenceObjectCount": sum(value == 0 for value in values),
            "totalOccurrenceCount": total,
        })
        count_vectors[str(k)] = {object_id: occurrences[object_id] for object_id in cohort}
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kValues": list(k_values),
        "rows": rows,
        "occurrenceCounts": count_vectors,
        "highHubnessIsDiagnosticNotAutomaticDisqualification": True,
    }


def _scalar_member(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if isinstance(value, Mapping):
        return str(value.get("id", ""))
    return str(value if value is not None else "")


def source_bias_diagnostics(
    rankings: Mapping[str, Sequence[Any]],
    records_by_id: Mapping[str, Mapping[str, Any]],
    *,
    k: int = 20,
) -> dict[str, Any]:
    if k <= 0:
        raise HubnessError("source diagnostic k must be positive")
    occurrence_sources: Counter[str] = Counter()
    top1_sources: Counter[str] = Counter()
    cross_source = 0
    evaluated = 0
    for query_id in sorted(rankings):
        if query_id not in records_by_id:
            raise HubnessError("source diagnostic lacks a query record")
        query_source = _scalar_member(records_by_id[query_id], "source")
        for ordinal, raw in enumerate(rankings[query_id][:k]):
            candidate_id = _candidate_id(raw)
            if candidate_id not in records_by_id:
                raise HubnessError("source diagnostic lacks a candidate record")
            candidate_source = _scalar_member(records_by_id[candidate_id], "source")
            occurrence_sources[candidate_source] += 1
            if ordinal == 0:
                top1_sources[candidate_source] += 1
            cross_source += int(query_source != candidate_source)
            evaluated += 1
    total_top1 = sum(top1_sources.values())
    total_occurrences = sum(occurrence_sources.values())
    shares = [count / total_occurrences for count in occurrence_sources.values()] if total_occurrences else []
    return {
        "k": k,
        "queryCount": len(rankings),
        "resultTop1SourceShare": max(top1_sources.values(), default=0) / total_top1 if total_top1 else 0.0,
        "resultHhi": sum(share * share for share in shares),
        "crossSourceRate": cross_source / evaluated if evaluated else 0.0,
        "evaluatedResultCount": evaluated,
        "sameSourceIsHistoricalRelation": False,
    }


def family_dominance_diagnostics(
    ranking_profiles: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    maximum_shares: list[float] = []
    source_dominated = 0
    curation_dominated = 0
    count = 0
    for row in ranking_profiles:
        profile = row.get("profile", row)
        if not isinstance(profile, Mapping):
            raise HubnessError("family dominance row lacks a profile")
        declared_shares = profile.get("familyContributionShares")
        if not isinstance(declared_shares, Mapping):
            raise HubnessError("profile lacks actual weighted/capped family contribution shares")
        shares = {
            str(family): max(0.0, float(value))
            for family, value in declared_shares.items()
            if value is not None and float(value) > 0
        }
        share_total = sum(shares.values())
        if shares and not math.isclose(
            share_total,
            1.0,
            rel_tol=0.0,
            abs_tol=2e-9,
        ):
            raise HubnessError("declared family contribution shares do not sum to one")
        if any(value > 1.0 + 2e-9 for value in shares.values()):
            raise HubnessError("family contribution share exceeds one")
        maximum = max(shares.values(), default=0.0)
        maximum_shares.append(maximum)
        source_dominated += int(shares.get("source", 0.0) > 0.8)
        curation_dominated += int(shares.get("curatorialResidual", 0.0) > 0.8)
        count += 1
    return {
        "resultCount": count,
        "medianMaximumFamilyShare": _quantile_r7(maximum_shares, 0.50),
        "p95MaximumFamilyShare": _quantile_r7(maximum_shares, 0.95),
        "oneFamilyOver80PercentRate": sum(value > 0.8 for value in maximum_shares) / count if count else 0.0,
        "sourceDominatedQueryRate": source_dominated / count if count else 0.0,
        "curationDominatedQueryRate": curation_dominated / count if count else 0.0,
    }


def _ranks(values: Mapping[str, float]) -> dict[str, float]:
    ordered = sorted(values.items(), key=lambda item: (item[1], item[0]))
    ranks: dict[str, float] = {}
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][1] == ordered[index][1]:
            end += 1
        rank = (index + 1 + end) / 2
        for position in range(index, end):
            ranks[ordered[position][0]] = rank
        index = end
    return ranks


def spearman_correlation(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    keys = sorted(set(left) & set(right))
    if len(keys) < 2:
        return 0.0
    left_ranks = _ranks({key: float(left[key]) for key in keys})
    right_ranks = _ranks({key: float(right[key]) for key in keys})
    left_mean = statistics.fmean(left_ranks.values())
    right_mean = statistics.fmean(right_ranks.values())
    numerator = sum((left_ranks[key] - left_mean) * (right_ranks[key] - right_mean) for key in keys)
    left_denominator = math.sqrt(sum((left_ranks[key] - left_mean) ** 2 for key in keys))
    right_denominator = math.sqrt(sum((right_ranks[key] - right_mean) ** 2 for key in keys))
    denominator = left_denominator * right_denominator
    return numerator / denominator if denominator else 0.0


def hub_attribute_correlations(
    occurrence_counts: Mapping[str, int],
    records_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, float]:
    def values(record: Mapping[str, Any], field: str) -> tuple[str, ...]:
        raw = record.get(field)
        if isinstance(raw, Mapping):
            raw = (raw,)
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
            raw = (raw,) if raw is not None else ()
        output = []
        for value in raw:
            output.append(str(value.get("id", "")) if isinstance(value, Mapping) else str(value))
        return tuple(value for value in output if value)

    dimension_counts: dict[str, Counter[str]] = {
        field: Counter(
            value
            for object_id in occurrence_counts
            for value in values(records_by_id[object_id], field)
        )
        for field in ("source", "medium", "theme", "geography", "decade")
    }
    dominant = {
        field: min(
            (value for value, count in counts.items() if count == max(counts.values(), default=0)),
            default="",
        )
        for field, counts in dimension_counts.items()
    }
    attributes: dict[str, dict[str, float]] = {
        "curatedMembershipCount": {},
        "contextValueCount": {},
        "metadataObservability": {},
        "geographyValueCount": {},
        "decadeValueCount": {},
        "dominantSourceIndicator": {},
        "commonMediumIndicator": {},
        "commonThemeIndicator": {},
        "dominantGeographyIndicator": {},
        "dominantDecadeIndicator": {},
    }
    for object_id in occurrence_counts:
        record = records_by_id.get(object_id)
        if record is None:
            raise HubnessError("hub attribute diagnostic lacks a public record")
        sequence_count = lambda field: len(record.get(field, ())) if isinstance(record.get(field), Sequence) else 0
        attributes["curatedMembershipCount"][object_id] = float(sequence_count("curated_container"))
        attributes["contextValueCount"][object_id] = float(
            sequence_count("medium") + sequence_count("theme") + sequence_count("movement_context")
        )
        attributes["metadataObservability"][object_id] = float(
            sum(bool(record.get(field)) for field in ("medium", "theme", "geography", "source", "object_type", "creator"))
        )
        attributes["geographyValueCount"][object_id] = float(sequence_count("geography"))
        attributes["decadeValueCount"][object_id] = float(sequence_count("decade"))
        attributes["dominantSourceIndicator"][object_id] = float(dominant["source"] in values(record, "source"))
        attributes["commonMediumIndicator"][object_id] = float(dominant["medium"] in values(record, "medium"))
        attributes["commonThemeIndicator"][object_id] = float(dominant["theme"] in values(record, "theme"))
        attributes["dominantGeographyIndicator"][object_id] = float(dominant["geography"] in values(record, "geography"))
        attributes["dominantDecadeIndicator"][object_id] = float(dominant["decade"] in values(record, "decade"))
    occurrence = {key: float(value) for key, value in occurrence_counts.items()}
    return {
        name: spearman_correlation(occurrence, values) for name, values in attributes.items()
    }


def hub_categorical_associations(
    occurrence_counts: Mapping[str, int],
    records_by_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Report explicit source/common-value/geography/decade hub associations."""

    def values(record: Mapping[str, Any], field: str) -> tuple[str, ...]:
        raw = record.get(field)
        if isinstance(raw, Mapping):
            raw = (raw,)
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
            raw = (raw,) if raw is not None else ()
        return tuple(
            sorted(
                {
                    str(value.get("id", "")) if isinstance(value, Mapping) else str(value)
                    for value in raw
                    if value is not None
                }
                - {""}
            )
        )

    rows: list[dict[str, Any]] = []
    for field in ("source", "medium", "theme", "geography", "decade"):
        members: dict[str, list[str]] = defaultdict(list)
        for object_id in sorted(occurrence_counts):
            record = records_by_id.get(object_id)
            if record is None:
                raise HubnessError("hub categorical association lacks a public record")
            for value in values(record, field):
                members[value].append(object_id)
        for value, object_ids in sorted(members.items()):
            occurrences = [occurrence_counts[object_id] for object_id in object_ids]
            rows.append({
                "dimension": field,
                "valueId": value,
                "objectSupport": len(object_ids),
                "occurrenceCount": sum(occurrences),
                "meanOccurrence": statistics.fmean(occurrences),
                "maximumOccurrence": max(occurrences),
                "interpretation": "CORPUS_ASSOCIATION_NOT_HISTORICAL_RELATION",
            })
    return rows


def reciprocal_neighbor_filter(
    rankings: Mapping[str, Sequence[Any]],
    *,
    k: int = 20,
) -> dict[str, list[dict[str, Any]]]:
    if k <= 0:
        raise HubnessError("reciprocal-neighbor k must be positive")
    neighbor_sets = {
        query_id: {_candidate_id(row) for row in rows[:k]}
        for query_id, rows in rankings.items()
    }
    output: dict[str, list[dict[str, Any]]] = {}
    for query_id in sorted(rankings):
        rows: list[dict[str, Any]] = []
        for raw in rankings[query_id]:
            candidate_id = _candidate_id(raw)
            if query_id in neighbor_sets.get(candidate_id, set()):
                row = dict(raw) if isinstance(raw, Mapping) else {"candidateId": candidate_id}
                row["hubnessCorrection"] = "RECIPROCAL_NEIGHBOR_FILTER"
                row["originalScoreChanged"] = False
                rows.append(row)
        output[query_id] = rows
    return output


def local_scaling(
    rankings: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    scale_k: int = 20,
) -> dict[str, list[dict[str, Any]]]:
    """Analysis-only local scaling over available similarity rows."""

    if scale_k <= 0:
        raise HubnessError("local scale k must be positive")
    scales = {
        query_id: max(1e-12, _score(rows[min(scale_k, len(rows)) - 1])) if rows else 1e-12
        for query_id, rows in rankings.items()
    }
    output: dict[str, list[dict[str, Any]]] = {}
    for query_id in sorted(rankings):
        transformed: list[dict[str, Any]] = []
        for raw in rankings[query_id]:
            candidate_id = _candidate_id(raw)
            denominator = math.sqrt(scales[query_id] * scales.get(candidate_id, scales[query_id]))
            row = dict(raw)
            row["transformedDiagnosticScore"] = min(1.0, _score(raw) / denominator) if denominator else 0.0
            row["hubnessCorrection"] = "LOCAL_SCALING"
            transformed.append(row)
        transformed.sort(key=lambda row: (-float(row["transformedDiagnosticScore"]), str(row["candidateId"])))
        output[query_id] = transformed
    return output


def global_scaling_style(
    rankings: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    """Mutual-proximity/global-scaling style empirical transformation.

    Unlike a single global CDF (which cannot change rank order), this combines
    the query-specific and candidate-specific empirical score percentiles.
    The experiment remains analysis-only and is not a calibrated probability.
    """

    distributions = {
        query_id: sorted(_score(row) for row in rows)
        for query_id, rows in rankings.items()
    }

    def percentile(distribution: Sequence[float], score: float) -> float:
        if not distribution:
            return 0.0
        # Deterministic right-continuous empirical CDF.
        low = 0
        high = len(distribution)
        while low < high:
            middle = (low + high) // 2
            if distribution[middle] <= score:
                low = middle + 1
            else:
                high = middle
        return low / len(distribution)

    output: dict[str, list[dict[str, Any]]] = {}
    for query_id in sorted(rankings):
        rows = []
        for raw in rankings[query_id]:
            row = dict(raw)
            candidate_id = _candidate_id(raw)
            score = _score(raw)
            query_percentile = percentile(distributions[query_id], score)
            candidate_percentile = percentile(
                distributions.get(candidate_id, distributions[query_id]), score
            )
            row["transformedDiagnosticScore"] = query_percentile * candidate_percentile
            row["hubnessCorrection"] = "MUTUAL_PROXIMITY_GLOBAL_SCALING_STYLE"
            rows.append(row)
        rows.sort(key=lambda row: (-float(row["transformedDiagnosticScore"]), str(row["candidateId"])))
        output[query_id] = rows
    return output


def self_test() -> dict[str, Any]:
    cohort = tuple(f"SURF-H{index}" for index in range(1, 6))
    rankings = {
        query: [candidate for candidate in cohort if candidate != query]
        for query in cohort
    }
    result = k_occurrence_distribution(rankings, cohort_ids=cohort, k_values=(2,))
    row = result["rows"][0]
    if row["maximumOccurrence"] != 4 or row["zeroOccurrenceObjectCount"] != 0:
        # With lexical top-2, H1/H2 appear four times and all others can be zero;
        # assert only total conservation here instead of uniformity.
        if row["totalOccurrenceCount"] != 10:
            raise AssertionError("hubness occurrence counts do not conserve k selections")
    mapped = {
        query: [
            {"candidateId": candidate, "diagnosticScore": 1 / (rank + 1)}
            for rank, candidate in enumerate(values)
        ]
        for query, values in rankings.items()
    }
    reciprocal = reciprocal_neighbor_filter(mapped, k=2)
    if any(query in {_candidate_id(row) for row in rows} for query, rows in reciprocal.items()):
        raise AssertionError("hub correction introduced self")
    return {
        "status": "PASS",
        "hubnessKValues": list(HUBNESS_K_VALUES),
        "hubnessCorrectionVariantCount": len(HUBNESS_CORRECTIONS),
        "randomnessUsed": False,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
