#!/usr/bin/env python3
"""Deterministic ranking ablation and stability diagnostics."""

from __future__ import annotations

import json
import math
import statistics
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from typing import Any

import model_baselines


SCHEMA_VERSION = "trace-exploration-ablation/v1"
IMPLEMENTATION_VERSION = "trace-exploration-ablation-2026-08-24"
REQUIRED_ABLATION_FAMILIES = (
    "LEAVE_CONTEXT_OUT",
    "LEAVE_TIME_OUT",
    "LEAVE_GEOGRAPHY_OUT",
    "LEAVE_SOURCE_OUT",
    "LEAVE_CURATION_OUT",
    "LEAVE_MISSINGNESS_DIAGNOSTICS_OUT",
    "LEAVE_INTERACTIONS_OUT",
    "REMOVE_LARGEST_CURATED_CONTAINER",
    "REMOVE_DOMINANT_SOURCE",
    "CHANGE_BROAD_CONTAINER_THRESHOLD",
    "CHANGE_RARE_SUPPORT_THRESHOLD",
    "CHANGE_TEMPORAL_DECAY",
    "CHANGE_FAMILY_NORMALIZATION",
)
BROAD_CONTAINER_THRESHOLD_GRID = (0.25, 0.50, 0.75, 0.90)
RARE_SUPPORT_THRESHOLD_GRID = (2, 3, 5, 10, 20)
TEMPORAL_DECAY_GRID = (5.0, 10.0, 20.0, 40.0, 80.0)
FAMILY_NORMALIZATION_GRID = model_baselines.FAMILY_NORMALIZATIONS
USER_SELECTED_WEIGHT_TEMPLATE = {
    "context": 1.00,
    "temporal": 0.80,
    "geography": 0.65,
    "descriptive": 0.45,
    "source": 0.30,
    "curatorialResidual": 0.20,
}


class AblationError(ValueError):
    """Raised when ranking stability inputs are malformed."""


def _effective_eligible_families(
    spec: model_baselines.ModelSpec,
    declared: Sequence[str] | None = None,
) -> tuple[str, ...]:
    families = list(spec.eligible_families if declared is None else declared)
    if spec.source_treatment in {"SOURCE-1", "SOURCE-3"}:
        if "source" not in families:
            families.append("source")
    else:
        families = [family for family in families if family != "source"]
    return tuple(families)


def _user_selected_weights(families: Sequence[str]) -> tuple[tuple[str, float], ...]:
    weights = tuple(
        (family, USER_SELECTED_WEIGHT_TEMPLATE[family]) for family in families
    )
    if len({weight for _, weight in weights}) < min(2, len(weights)):
        raise AblationError("USER_SELECTED ablation weights must be non-equal")
    return weights


def declared_ablation_variants(base_spec: model_baselines.ModelSpec) -> tuple[dict[str, Any], ...]:
    """Return the complete non-learned sensitivity grid for one model."""

    variants: list[dict[str, Any]] = []
    family_map = {
        "LEAVE_CONTEXT_OUT": "context",
        "LEAVE_TIME_OUT": "temporal",
        "LEAVE_GEOGRAPHY_OUT": "geography",
        "LEAVE_SOURCE_OUT": "source",
        "LEAVE_CURATION_OUT": "curatorialResidual",
    }
    for ablation_id, family in family_map.items():
        eligible = tuple(value for value in base_spec.eligible_families if value != family)
        source_treatment = (
            "SOURCE-0" if ablation_id == "LEAVE_SOURCE_OUT" else base_spec.source_treatment
        )
        effective = _effective_eligible_families(
            replace(base_spec, source_treatment=source_treatment),
            eligible,
        )
        variants.append({
            "ablationId": ablation_id,
            "ablationFamily": ablation_id,
            "modelSpec": replace(
                base_spec,
                variant_id=f"{base_spec.variant_id}::{ablation_id}",
                eligible_families=eligible,
                source_treatment=source_treatment,
                family_weights=(
                    _user_selected_weights(effective)
                    if base_spec.family_normalization == "USER_SELECTED"
                    else ()
                ),
            ),
            "candidatePolicyOverrides": {},
            "dataPerturbation": None,
        })
    variants.extend(
        (
            {
                "ablationId": "LEAVE_MISSINGNESS_DIAGNOSTICS_OUT",
                "ablationFamily": "LEAVE_MISSINGNESS_DIAGNOSTICS_OUT",
                "modelSpec": replace(
                    base_spec,
                    variant_id=f"{base_spec.variant_id}::LEAVE_MISSINGNESS_DIAGNOSTICS_OUT",
                    missingness_variant="MISSING-C",
                ),
                "candidatePolicyOverrides": {},
                "dataPerturbation": "OMIT_MISSINGNESS_EXPLORATION_CHANNEL_ONLY",
            },
            {
                "ablationId": "LEAVE_INTERACTIONS_OUT",
                "ablationFamily": "LEAVE_INTERACTIONS_OUT",
                "modelSpec": replace(
                    base_spec,
                    variant_id=f"{base_spec.variant_id}::LEAVE_INTERACTIONS_OUT",
                    interaction_policy="NO_INTERACTION_CONTRIBUTION",
                ),
                "candidatePolicyOverrides": {"include_interactions": False},
                "dataPerturbation": None,
            },
            {
                "ablationId": "REMOVE_LARGEST_CURATED_CONTAINER",
                "ablationFamily": "REMOVE_LARGEST_CURATED_CONTAINER",
                "modelSpec": replace(base_spec, variant_id=f"{base_spec.variant_id}::REMOVE_LARGEST_CURATED_CONTAINER"),
                "candidatePolicyOverrides": {},
                "dataPerturbation": "REMOVE_DETERMINISTIC_MAX_SUPPORT_CURATED_CONTAINER",
            },
            {
                "ablationId": "REMOVE_DOMINANT_SOURCE",
                "ablationFamily": "REMOVE_DOMINANT_SOURCE",
                "modelSpec": replace(base_spec, variant_id=f"{base_spec.variant_id}::REMOVE_DOMINANT_SOURCE"),
                "candidatePolicyOverrides": {"include_source": False},
                "dataPerturbation": "REMOVE_DETERMINISTIC_MAX_SUPPORT_SOURCE",
            },
        )
    )
    for threshold in BROAD_CONTAINER_THRESHOLD_GRID:
        variants.append({
            "ablationId": f"BROAD_CONTAINER_STOP_{int(threshold * 100)}PCT",
            "ablationFamily": "CHANGE_BROAD_CONTAINER_THRESHOLD",
            "modelSpec": replace(base_spec, variant_id=f"{base_spec.variant_id}::BROAD-{threshold:.2f}"),
            "candidatePolicyOverrides": {"broad_container_stop_ratio": threshold},
            "dataPerturbation": None,
        })
    for threshold in RARE_SUPPORT_THRESHOLD_GRID:
        variants.append({
            "ablationId": f"RARE_SUPPORT_{threshold}",
            "ablationFamily": "CHANGE_RARE_SUPPORT_THRESHOLD",
            "modelSpec": replace(base_spec, variant_id=f"{base_spec.variant_id}::RARE-{threshold}"),
            "candidatePolicyOverrides": {"rare_support_threshold": threshold},
            "dataPerturbation": None,
        })
    for decay in TEMPORAL_DECAY_GRID:
        variants.append({
            "ablationId": f"TEMPORAL_DECAY_{int(decay)}Y",
            "ablationFamily": "CHANGE_TEMPORAL_DECAY",
            "modelSpec": replace(
                base_spec,
                variant_id=f"{base_spec.variant_id}::TEMP-DECAY-{int(decay)}",
                temporal_variant="TEMP-3",
                temporal_decay_years=decay,
            ),
            "candidatePolicyOverrides": {},
            "dataPerturbation": None,
        })
    for normalization in FAMILY_NORMALIZATION_GRID:
        effective = _effective_eligible_families(base_spec)
        variants.append({
            "ablationId": f"FAMILY_NORMALIZATION_{normalization}",
            "ablationFamily": "CHANGE_FAMILY_NORMALIZATION",
            "modelSpec": replace(
                base_spec,
                variant_id=f"{base_spec.variant_id}::NORM-{normalization}",
                family_normalization=normalization,
                family_cap=(0.60 if normalization == "CAPPED_FAMILY" else base_spec.family_cap),
                family_weights=(
                    _user_selected_weights(effective)
                    if normalization == "USER_SELECTED"
                    else ()
                ),
            ),
            "candidatePolicyOverrides": {},
            "dataPerturbation": None,
        })
    observed_families = {row["ablationFamily"] for row in variants}
    if observed_families != set(REQUIRED_ABLATION_FAMILIES):
        raise AssertionError("declared ablation grid lost a required family")
    for row in variants:
        model_baselines._validate_spec(row["modelSpec"])
    return tuple(variants)


def _candidate_id(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        identifier = str(value.get("candidateId", ""))
        if identifier:
            return identifier
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and value:
        return str(value[0])
    raise AblationError("ranking row lacks candidateId")


def top_k_overlap(reference: Sequence[Any], candidate: Sequence[Any], *, k: int = 20) -> float:
    if k <= 0:
        raise AblationError("top-k overlap requires positive k")
    left = {_candidate_id(value) for value in reference[:k]}
    right = {_candidate_id(value) for value in candidate[:k]}
    denominator = max(1, min(k, len(left), len(right)))
    return len(left & right) / denominator


def rank_correlation(reference: Sequence[Any], candidate: Sequence[Any], *, k: int = 20) -> float:
    """Spearman correlation with absent members assigned deterministic k+1."""

    if k <= 1:
        raise AblationError("rank correlation requires k greater than one")
    reference_ids = [_candidate_id(value) for value in reference[:k]]
    candidate_ids = [_candidate_id(value) for value in candidate[:k]]
    universe = sorted(set(reference_ids) | set(candidate_ids))
    if len(universe) < 2:
        return 1.0
    left_rank = {value: rank + 1 for rank, value in enumerate(reference_ids)}
    right_rank = {value: rank + 1 for rank, value in enumerate(candidate_ids)}
    absent = k + 1
    left = [float(left_rank.get(value, absent)) for value in universe]
    right = [float(right_rank.get(value, absent)) for value in universe]
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right))
    denominator = math.sqrt(
        sum((a - left_mean) ** 2 for a in left)
        * sum((b - right_mean) ** 2 for b in right)
    )
    return numerator / denominator if denominator else 0.0


def compare_rankings(
    reference: Mapping[str, Sequence[Any]],
    candidate: Mapping[str, Sequence[Any]],
    *,
    k_values: Sequence[int] = (10, 20, 50),
) -> dict[str, Any]:
    if set(reference) != set(candidate):
        raise AblationError("ablation/reference query sets differ")
    rows: list[dict[str, Any]] = []
    for k in k_values:
        overlaps = [top_k_overlap(reference[query], candidate[query], k=k) for query in sorted(reference)]
        correlations = [rank_correlation(reference[query], candidate[query], k=max(2, k)) for query in sorted(reference)]
        rows.append({
            "k": k,
            "queryCount": len(reference),
            "meanTopKOverlap": statistics.fmean(overlaps) if overlaps else 0.0,
            "minimumTopKOverlap": min(overlaps, default=0.0),
            "meanRankCorrelation": statistics.fmean(correlations) if correlations else 0.0,
            "minimumRankCorrelation": min(correlations, default=0.0),
        })
    return {"rows": rows, "queryCount": len(reference)}


def evaluate_ablation_grid(
    reference_rankings: Mapping[str, Sequence[Any]],
    variants: Sequence[Mapping[str, Any]],
    ranking_provider: Callable[[Mapping[str, Any]], Mapping[str, Sequence[Any]]],
    *,
    k_values: Sequence[int] = (10, 20, 50),
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for variant in variants:
        rankings = ranking_provider(variant)
        comparison = compare_rankings(reference_rankings, rankings, k_values=k_values)
        results.append({
            "ablationId": str(variant["ablationId"]),
            "ablationFamily": str(variant["ablationFamily"]),
            "comparison": comparison,
        })
    return {
        "schemaVersion": SCHEMA_VERSION,
        "ablationVariantCount": len(results),
        "requiredAblationFamilyCount": len(REQUIRED_ABLATION_FAMILIES),
        "rows": results,
        "learnedWeightsUsed": False,
        "historicalLabelsUsed": False,
    }


def collapse_failure_count(
    evaluation: Mapping[str, Any],
    *,
    k: int = 20,
    overlap_floor: float = 0.50,
) -> int:
    failures = 0
    for result in evaluation.get("rows", ()):
        rows = result.get("comparison", {}).get("rows", ())
        target = next((row for row in rows if int(row.get("k", -1)) == k), None)
        if target is None or float(target.get("meanTopKOverlap", 0.0)) < overlap_floor:
            failures += 1
    return failures


def self_test() -> dict[str, Any]:
    spec = model_baselines.default_model_specs()[4]
    variants = declared_ablation_variants(spec)
    reference = {
        "SURF-A": ["SURF-B", "SURF-C", "SURF-D"],
        "SURF-B": ["SURF-A", "SURF-C", "SURF-D"],
    }
    identical = compare_rankings(reference, reference, k_values=(2,))
    if identical["rows"][0]["meanTopKOverlap"] != 1 or not math.isclose(
        identical["rows"][0]["meanRankCorrelation"], 1.0
    ):
        raise AssertionError("identical rankings are not perfectly stable")
    user_variant = next(
        row["modelSpec"]
        for row in variants
        if row["ablationId"] == "FAMILY_NORMALIZATION_USER_SELECTED"
    )
    declared_weights = dict(user_variant.family_weights)
    expected_families = set(_effective_eligible_families(user_variant))
    if (
        set(declared_weights) != expected_families
        or len(set(declared_weights.values())) < 2
        or user_variant.parameters() == spec.parameters()
    ):
        raise AssertionError("USER_SELECTED ablation collapsed to equal-family scoring")
    return {
        "status": "PASS",
        "ablationVariantCount": len(variants),
        "requiredAblationFamilyCount": len(REQUIRED_ABLATION_FAMILIES),
        "learnedWeightsUsed": False,
        "userSelectedWeightsComplete": True,
        "userSelectedWeightsNonEqual": True,
        "userSelectedConfigurationChanged": True,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
