#!/usr/bin/env python3
"""Explicit missingness and comparability channels for Exploration affinity.

Missing or unknown values never create positive base affinity.  Comparability
is returned alongside affinity and is never renamed confidence or hidden in a
score denominator.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any


SCHEMA_VERSION = "trace-exploration-missingness-comparability/v1"
IMPLEMENTATION_VERSION = "trace-exploration-missingness-comparability-2026-08-24"
MISSINGNESS_VARIANTS = ("MISSING-A", "MISSING-B", "MISSING-C", "MISSING-D")
DEFAULT_ELIGIBLE_FAMILIES = (
    "context",
    "temporal",
    "geography",
    "source",
    "descriptive",
)
OPTIONAL_FAMILIES = ("curatorialResidual",)
UNKNOWN_PATTERNS = (
    re.compile(r"^unknown$", re.IGNORECASE),
    re.compile(r"^unknown;", re.IGNORECASE),
    re.compile(r"^(?:not[ _-]?governed|not[ _-]?available)$", re.IGNORECASE),
    re.compile(r"^no[ _-]?published[ _-]?movement[ _-]?context$", re.IGNORECASE),
)


class ComparabilityError(ValueError):
    """Raised when a missingness/comparability contract is invalid."""


@dataclass(frozen=True)
class ComparabilityProfile:
    observed_family_count: int
    eligible_family_count: int
    ratio: float
    jointly_observable_families: tuple[str, ...]
    unavailable_families: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "observedFamilyCount": self.observed_family_count,
            "eligibleFamilyCount": self.eligible_family_count,
            "ratio": self.ratio,
        }


def _label(value: Any) -> str:
    if isinstance(value, Mapping):
        return str(value.get("label", value.get("id", ""))).strip()
    return str(value if value is not None else "").strip()


def _sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return (value,)


def is_unknown_state(value: Any) -> bool:
    label = _label(value)
    return not label or any(pattern.search(label) for pattern in UNKNOWN_PATTERNS)


def observed_values(record: Mapping[str, Any], field: str) -> tuple[str, ...]:
    values = []
    for value in _sequence(record.get(field)):
        label = _label(value)
        if label and not is_unknown_state(value):
            values.append(label)
    return tuple(sorted(set(values)))


def family_availability(
    record: Mapping[str, Any],
    *,
    eligible_families: Sequence[str] = DEFAULT_ELIGIBLE_FAMILIES,
) -> dict[str, bool]:
    """Classify family availability without treating N/A as generic missing."""

    availability: dict[str, bool] = {}
    context_values = (
        observed_values(record, "medium")
        + observed_values(record, "theme")
        + observed_values(record, "movement_context")
    )
    availability["context"] = bool(context_values)

    precision = str(record.get("temporalPrecision", "")).strip()
    start = record.get("startYear")
    end = record.get("endYear")
    availability["temporal"] = (
        bool(precision)
        and not is_unknown_state(precision)
        and isinstance(start, int)
        and not isinstance(start, bool)
        and isinstance(end, int)
        and not isinstance(end, bool)
        and end >= start
    )
    availability["geography"] = bool(observed_values(record, "geography"))
    availability["source"] = bool(observed_values(record, "source"))
    availability["descriptive"] = bool(
        observed_values(record, "object_type") or observed_values(record, "creator")
    )
    availability["curatorialResidual"] = bool(
        observed_values(record, "curatorialResidual")
        or observed_values(record, "residual_curated_container")
    )
    unknown = set(eligible_families) - set(availability)
    if unknown:
        raise ComparabilityError(f"unsupported eligible family/families: {sorted(unknown)}")
    return {family: availability[family] for family in eligible_families}


def missingness_state_vector(record: Mapping[str, Any]) -> dict[str, str]:
    """Return an uncertainty state channel that is never base affinity input."""

    movement = observed_values(record, "movement_context")
    precision = str(record.get("temporalPrecision", "")).strip().casefold()
    geography_states = tuple(
        sorted(
            {
                _label(value)
                for value in _sequence(
                    record.get("geographyMappingStates", record.get("geography_mapping_state"))
                )
                if _label(value)
            }
        )
    )
    creator_values = observed_values(record, "creator")
    raw_creator = _label(record.get("creator"))
    if raw_creator.casefold() == "unknown":
        creator_state = "UNKNOWN_SOURCE_VALUE"
    elif raw_creator.casefold().startswith("unknown;"):
        creator_state = "QUALIFIED_UNKNOWN_SOURCE_VALUE"
    elif creator_values:
        creator_state = "OBSERVED"
    else:
        creator_state = "NOT_GOVERNED"
    temporal_state = {
        "approximate": "APPROXIMATE",
        "range": "RANGE",
        "unknown": "UNKNOWN_SOURCE_VALUE",
    }.get(precision, "OBSERVED" if precision else "NOT_GOVERNED")
    return {
        "movementContextState": "OBSERVED" if movement else "NO_PUBLISHED_MOVEMENT_CONTEXT",
        "temporalUncertaintyState": temporal_state,
        "geographyMappingState": ";".join(geography_states) if geography_states else "NOT_GOVERNED",
        "geographyQualificationState": (
            "QUALIFIED" if bool(record.get("geographyQualified", False)) else "UNQUALIFIED"
        ),
        "creatorState": creator_state,
        "sourceState": "OBSERVED" if observed_values(record, "source") else "NOT_GOVERNED",
        "objectTypeState": (
            "OBSERVED" if observed_values(record, "object_type") else "NOT_GOVERNED"
        ),
    }


def compute_comparability(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    *,
    eligible_families: Sequence[str] = DEFAULT_ELIGIBLE_FAMILIES,
) -> ComparabilityProfile:
    if not eligible_families or len(set(eligible_families)) != len(eligible_families):
        raise ComparabilityError("eligible families must be nonempty and unique")
    left_availability = family_availability(left, eligible_families=eligible_families)
    right_availability = family_availability(right, eligible_families=eligible_families)

    def pairwise_available(family: str) -> bool:
        # A family is jointly observable only when at least one comparable
        # subfield exists on both sides.  "medium only" versus "theme only"
        # is not a jointly observable Context family.
        subfields = {
            "context": ("medium", "theme", "movement_context"),
            "descriptive": ("object_type", "creator"),
        }.get(family)
        if subfields is not None:
            return any(observed_values(left, field) and observed_values(right, field) for field in subfields)
        return left_availability[family] and right_availability[family]

    jointly = tuple(family for family in eligible_families if pairwise_available(family))
    unavailable = tuple(family for family in eligible_families if family not in jointly)
    return ComparabilityProfile(
        observed_family_count=len(jointly),
        eligible_family_count=len(eligible_families),
        ratio=len(jointly) / len(eligible_families),
        jointly_observable_families=jointly,
        unavailable_families=unavailable,
    )


def aggregate_family_affinity(
    family_scores: Mapping[str, float | None],
    comparability: ComparabilityProfile,
    *,
    variant: str = "MISSING-C",
    family_weights: Mapping[str, float] | None = None,
    family_cap: float = 1.0,
) -> dict[str, Any]:
    """Aggregate observed family scores while preserving comparability.

    MISSING-A performs available-family renormalization; MISSING-B uses the
    full eligible denominator as a conservative lower bound; MISSING-C keeps
    observed affinity and comparability as two channels; MISSING-D adds only a
    separate uncertainty-state diagnostic.
    """

    if variant not in MISSINGNESS_VARIANTS:
        raise ComparabilityError(f"unsupported missingness variant: {variant}")
    if not 0 < family_cap <= 1:
        raise ComparabilityError("family contribution cap must be in (0, 1]")
    all_families = (
        comparability.jointly_observable_families + comparability.unavailable_families
    )
    weights = {family: 1.0 for family in all_families}
    if family_weights is not None:
        for family, weight in family_weights.items():
            if not isinstance(weight, (int, float)) or isinstance(weight, bool) or weight < 0:
                raise ComparabilityError("family weights must be finite nonnegative numbers")
            if not math.isfinite(float(weight)):
                raise ComparabilityError("family weights must be finite")
            if family in weights:
                weights[family] = float(weight)

    observed: dict[str, float] = {}
    for family in comparability.jointly_observable_families:
        raw = family_scores.get(family)
        if raw is None:
            continue
        score = float(raw)
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ComparabilityError("family scores must be finite values in [0, 1]")
        observed[family] = min(score, family_cap)
    numerator = sum(observed[family] * weights[family] for family in observed)
    observed_weight = sum(weights[family] for family in observed)
    eligible_weight = sum(weights[family] for family in all_families)
    if variant == "MISSING-B":
        affinity = numerator / eligible_weight if eligible_weight else 0.0
    else:
        affinity = numerator / observed_weight if observed_weight else 0.0
    return {
        "affinity": affinity,
        "observedNumerator": numerator,
        "observedWeightDenominator": observed_weight,
        "eligibleWeightDenominator": eligible_weight,
        "missingnessVariant": variant,
        "comparability": comparability.as_dict(),
        "jointlyObservableFamilies": list(comparability.jointly_observable_families),
        "unavailableFamilies": list(comparability.unavailable_families),
        "uncertaintyIncludedInAffinity": False,
    }


def compare_missingness_states(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare uncertainty states for MISSING-D exploration only.

    Matching states are reported but the positive-affinity credit is hard-coded
    to zero.  This prevents shared unknowns from becoming evidence.
    """

    left_states = missingness_state_vector(left)
    right_states = missingness_state_vector(right)
    matches = tuple(
        sorted(
            field
            for field in left_states
            if left_states[field] == right_states[field]
        )
    )
    shared_unknowns = tuple(
        field
        for field in matches
        if left_states[field]
        in {
            "UNKNOWN_SOURCE_VALUE",
            "QUALIFIED_UNKNOWN_SOURCE_VALUE",
            "NO_PUBLISHED_MOVEMENT_CONTEXT",
            "NOT_GOVERNED",
        }
    )
    return {
        "channel": "MISSINGNESS_ORIENTED_EXPLORATION_ONLY",
        "matchingStateFields": list(matches),
        "sharedUnknownStateFields": list(shared_unknowns),
        "positiveAffinityCredit": 0.0,
        "historicalRelation": False,
        "semanticRelation": False,
    }


def comparability_distribution(profiles: Iterable[ComparabilityProfile]) -> dict[str, float | int]:
    values = sorted(profile.ratio for profile in profiles)
    if not values:
        return {"count": 0, "p50": 0.0, "p95": 0.0, "min": 0.0, "max": 0.0}

    def r7(probability: float) -> float:
        position = (len(values) - 1) * probability
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return values[lower]
        return values[lower] + (values[upper] - values[lower]) * (position - lower)

    return {
        "count": len(values),
        "p50": r7(0.50),
        "p95": r7(0.95),
        "min": min(values),
        "max": max(values),
    }


def self_test() -> dict[str, Any]:
    token = lambda value, label=None: {"id": value, "label": label or value}
    base = {
        "medium": [token("M1")],
        "theme": [token("T1")],
        "movement_context": [],
        "geography": [token("G1")],
        "source": token("S1"),
        "object_type": token("OT1"),
        "creator": token("unknown", "Unknown"),
        "startYear": 1900,
        "endYear": 1900,
        "temporalPrecision": "year",
        "geographyMappingStates": ["mapped"],
        "geographyQualified": False,
    }
    other = dict(base)
    profile = compute_comparability(base, other)
    diagnostic = compare_missingness_states(base, other)
    if diagnostic["positiveAffinityCredit"] != 0:
        raise AssertionError("shared unknown state received affinity credit")
    a = aggregate_family_affinity(
        {family: 0.8 for family in profile.jointly_observable_families},
        profile,
        variant="MISSING-A",
    )
    b_profile = ComparabilityProfile(2, 5, 0.4, ("context", "temporal"), ("geography", "source", "descriptive"))
    b = aggregate_family_affinity(
        {"context": 0.8, "temporal": 0.8}, b_profile, variant="MISSING-B"
    )
    if not math.isclose(a["affinity"], 0.8) or not b["affinity"] < 0.8:
        raise AssertionError("missingness variants do not preserve their denominators")
    return {
        "status": "PASS",
        "missingnessVariantCount": len(MISSINGNESS_VARIANTS),
        "sharedUnknownPositiveCreditCount": 0,
        "comparabilityChannelImplemented": True,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
