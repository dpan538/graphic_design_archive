#!/usr/bin/env python3
"""Observed-only cross-dimensional and source-composition analysis.

The module consumes centrally normalized public records. It deliberately does
not choose similarity functions, feature weights, clusters, probabilities,
templates, UI behavior, or API behavior. Conditional rates and lift are
analysis diagnostics, never predictive claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from itertools import product
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "trace-exploration-cross-dimensional-analysis/v1"
DEFAULT_DERIVATION_VERSION = "trace-exploration-cross-dimensional-v1"
DEFAULT_MINIMUM_SUBSET_SUPPORT = 30
DEFAULT_RARE_MAX_COUNT = 20

REQUIRED_RECORD_KEYS = (
    "objectId",
    "medium",
    "theme",
    "movement_context",
    "decade",
    "geography",
    "source",
    "object_type",
    "creator",
    "temporalPrecision",
    "startYear",
    "endYear",
    "geographyClass",
    "geographyQualified",
    "multiRegion",
)
OPTIONAL_RECORD_KEYS = (
    "geographyState",
    "geographyMappingState",
    "geographyMappingStates",
    "geography_class",
    "geography_mapping_state",
    "sourceCollectionPresent",
    "curated_container",
    "curated_container_type",
)
REQUIRED_RECORD_KEY_ALIASES = {
    "geography_state": (
        "geographyState",
        "geographyMappingState",
        "geographyMappingStates",
        "geography_mapping_state",
    ),
    "geography_class": ("geographyClass", "geography_class"),
}

DIMENSION_SPECS: dict[str, dict[str, str]] = {
    "medium": {"shape": "array", "derivationLevel": "DIRECT_GOVERNED", "signalStatus": "HIGH_POTENTIAL"},
    "theme": {"shape": "array", "derivationLevel": "DIRECT_GOVERNED", "signalStatus": "HIGH_POTENTIAL"},
    "movement_context": {"shape": "array", "derivationLevel": "DIRECT_GOVERNED", "signalStatus": "SUPPORTING"},
    "decade": {"shape": "array", "derivationLevel": "DIRECT_GOVERNED", "signalStatus": "HIGH_POTENTIAL"},
    "geography": {"shape": "array", "derivationLevel": "DIRECT_GOVERNED", "signalStatus": "HIGH_POTENTIAL"},
    "source": {"shape": "scalar", "derivationLevel": "PUBLIC_METADATA", "signalStatus": "SUPPORTING"},
    "object_type": {"shape": "scalar", "derivationLevel": "PUBLIC_METADATA", "signalStatus": "SUPPORTING"},
    "creator": {
        "shape": "scalar",
        "derivationLevel": "PUBLIC_METADATA",
        "signalStatus": "RESEARCH_ONLY_HIGH_CARDINALITY",
    },
    "temporal_precision": {"shape": "scalar", "derivationLevel": "DIRECT_GOVERNED", "signalStatus": "SUPPORTING"},
    "geography_mapping_state": {"shape": "scalar", "derivationLevel": "DIRECT_GOVERNED", "signalStatus": "SUPPORTING"},
    "geography_class": {"shape": "scalar", "derivationLevel": "DIRECT_GOVERNED", "signalStatus": "SUPPORTING"},
    "curated_container": {
        "shape": "optional_array",
        "derivationLevel": "ANALYSIS_ONLY_CURATED",
        "signalStatus": "RESEARCH_ONLY_NEEDS_MORE_DATA",
    },
    "curated_container_type": {
        "shape": "optional_array",
        "derivationLevel": "ANALYSIS_ONLY_CURATED",
        "signalStatus": "RESEARCH_ONLY_NEEDS_MORE_DATA",
    },
}

BASE_FREQUENCY_DIMENSIONS = (
    "medium",
    "theme",
    "movement_context",
    "decade",
    "geography",
    "source",
    "object_type",
    "creator",
    "temporal_precision",
    "geography_mapping_state",
    "geography_class",
)

BASE_PAIR_SPECS = (
    ("medium", "theme"),
    ("medium", "movement_context"),
    ("theme", "movement_context"),
    ("medium", "decade"),
    ("theme", "decade"),
    ("medium", "geography"),
    ("theme", "geography"),
    ("decade", "geography"),
    ("source", "medium"),
    ("source", "theme"),
    ("source", "decade"),
    ("source", "geography"),
    ("object_type", "medium"),
    ("creator", "medium"),
)

BASE_TRIPLE_SPECS = (
    ("medium", "theme", "decade"),
    ("medium", "theme", "geography"),
    ("theme", "decade", "geography"),
    ("medium", "decade", "geography"),
    ("source", "theme", "decade"),
    ("source", "medium", "geography"),
)

SOURCE_SUBSET_DIMENSIONS = ("medium", "theme", "decade", "geography")
DIMENSION_CONCENTRATION_SPECS = (
    {
        "diagnosticId": "CONCENTRATION_SOURCE",
        "family": "SOURCE",
        "dimension": "source",
        "governanceState": "PUBLIC_METADATA_DERIVED",
        "interpretationBoundary": (
            "CORPUS_COMPOSITION_NOT_SOURCE_AUTHORITY_OR_HISTORICAL_REPRESENTATIVENESS"
        ),
    },
    {
        "diagnosticId": "CONCENTRATION_TEMPORAL",
        "family": "TEMPORAL",
        "dimension": "decade",
        "governanceState": "PUBLIC_GOVERNED_DERIVED",
        "interpretationBoundary": (
            "CORPUS_DISTRIBUTION_NOT_HISTORICAL_IMPORTANCE_OR_RELATION"
        ),
    },
    {
        "diagnosticId": "CONCENTRATION_GEOGRAPHIC",
        "family": "GEOGRAPHIC",
        "dimension": "geography",
        "governanceState": "PUBLIC_GOVERNED_DERIVED",
        "interpretationBoundary": (
            "CORPUS_DISTRIBUTION_NOT_HISTORICAL_DISTANCE_OR_REPRESENTATIVENESS"
        ),
    },
    {
        "diagnosticId": "CONCENTRATION_CURATORIAL",
        "family": "CURATORIAL",
        "dimension": "curated_container",
        "governanceState": "ANALYSIS_ONLY_CURATORIAL_DERIVED",
        "interpretationBoundary": (
            "PROJECT_CURATORIAL_DISTRIBUTION_NOT_HISTORICAL_RELATION_OR_IMPORTANCE"
        ),
    },
)
CURATORIAL_DIMENSIONS = frozenset({"curated_container", "curated_container_type"})
TEMPORAL_PRECISIONS = frozenset({"year", "approximate", "day", "month", "range", "unknown"})
GEOGRAPHY_STATES = frozenset({"mapped", "aggregate_only", "unmapped"})
UUID_PATTERN = re.compile(
    r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[1-5][0-9A-Fa-f]{3}"
    r"-[89ABab][0-9A-Fa-f]{3}-[0-9A-Fa-f]{12}(?![0-9A-Fa-f])"
)
URL_PATTERN = re.compile(r"(?:https?://|file://)", re.IGNORECASE)
PUBLIC_ID_PATTERN = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")


class AnalysisInputError(ValueError):
    """Raised when normalized public input violates the analysis contract."""


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n").encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AnalysisInputError(f"{field} must be nonblank text")
    text = value.strip()
    if URL_PATTERN.search(text):
        raise AnalysisInputError(f"{field} contains a URL")
    if UUID_PATTERN.search(text):
        raise AnalysisInputError(f"{field} contains an internal UUID")
    return text


def derived_value_id(namespace: str, label: str) -> str:
    """Create a stable analysis-only identifier for a safe display label."""

    safe_namespace = re.sub(r"[^a-z0-9_]+", "_", namespace.casefold()).strip("_")
    if not safe_namespace:
        raise AnalysisInputError("dimension namespace must contain a safe character")
    digest = hashlib.sha256(f"{safe_namespace}\0{label}".encode("utf-8")).hexdigest()
    return f"analysis:{safe_namespace}:sha256:{digest[:24]}"


def normalize_dimension_member(value: Any, namespace: str) -> dict[str, str]:
    """Normalize a safe string or governed ``{id,label}`` dimension member."""

    if isinstance(value, str):
        label = _require_text(value, f"{namespace}.label")
        return {"valueId": derived_value_id(namespace, label), "valueLabel": label}
    if isinstance(value, Mapping):
        if "id" not in value or "label" not in value:
            raise AnalysisInputError(f"{namespace} mapping members require id and label")
        return {
            "valueId": _require_text(value["id"], f"{namespace}.id"),
            "valueLabel": _require_text(value["label"], f"{namespace}.label"),
        }
    raise AnalysisInputError(f"{namespace} members must be text or {{id,label}} mappings")


def _dimension_array(value: Any, dimension: str) -> tuple[dict[str, str], ...]:
    if not isinstance(value, (list, tuple)):
        raise AnalysisInputError(f"{dimension} must be an array")
    by_id: dict[str, str] = {}
    for item in value:
        member = normalize_dimension_member(item, dimension)
        previous = by_id.setdefault(member["valueId"], member["valueLabel"])
        if previous != member["valueLabel"]:
            raise AnalysisInputError(f"{dimension} reuses a value ID with conflicting labels")
    return tuple(
        {"valueId": value_id, "valueLabel": label}
        for value_id, label in sorted(by_id.items())
    )


def _scalar_dimension(value: Any, dimension: str) -> tuple[dict[str, str], ...]:
    return (normalize_dimension_member(value, dimension),)


def _mapping_state(record: Mapping[str, Any]) -> str:
    value = record.get("geographyState", record.get("geographyMappingState"))
    if value is None:
        values = record.get("geographyMappingStates", record.get("geography_mapping_state"))
        if not isinstance(values, (list, tuple)):
            raise AnalysisInputError("geography mapping state is required")
        labels = {
            normalize_dimension_member(item, "geography_mapping_state")["valueLabel"]
            for item in values
        }
        if len(labels) != 1:
            raise AnalysisInputError("object-level geography state requires one governed state")
        value = next(iter(labels))
    if value not in GEOGRAPHY_STATES:
        raise AnalysisInputError("geography state must be mapped, aggregate_only, or unmapped")
    return str(value)


def _require_year(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9999:
        raise AnalysisInputError(f"{field} must be an integer year from 0 through 9999")
    return value


def _normalize_record(record: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise AnalysisInputError("every record must be an object")
    missing = [
        key for key in REQUIRED_RECORD_KEYS
        if key not in record and not (
            key == "geographyClass" and "geography_class" in record
        )
    ]
    if missing:
        raise AnalysisInputError(f"record is missing required keys: {', '.join(missing)}")
    if record.get("held") is True or record.get("isHeld") is True:
        raise AnalysisInputError("held record entered the public analysis cohort")
    if record.get("researchDisposition") == "held":
        raise AnalysisInputError("held disposition entered the public analysis cohort")

    object_id = _require_text(record["objectId"], "objectId")
    if not PUBLIC_ID_PATTERN.fullmatch(object_id):
        raise AnalysisInputError("objectId must be a public SURF identifier")
    dimensions = {
        "medium": _dimension_array(record["medium"], "medium"),
        "theme": _dimension_array(record["theme"], "theme"),
        "movement_context": _dimension_array(record["movement_context"], "movement_context"),
        "decade": _dimension_array(record["decade"], "decade"),
        "geography": _dimension_array(record["geography"], "geography"),
        "source": _scalar_dimension(record["source"], "source"),
        "object_type": _scalar_dimension(record["object_type"], "object_type"),
        "creator": _scalar_dimension(record["creator"], "creator"),
    }
    for required_dimension in ("medium", "theme", "decade", "geography"):
        if not dimensions[required_dimension]:
            raise AnalysisInputError(f"governed {required_dimension} must be present")

    temporal_precision = _require_text(record["temporalPrecision"], "temporalPrecision")
    if temporal_precision not in TEMPORAL_PRECISIONS:
        raise AnalysisInputError(f"unsupported temporal precision: {temporal_precision}")
    start_year = _require_year(record["startYear"], "startYear")
    end_year = _require_year(record["endYear"], "endYear")
    if end_year < start_year:
        raise AnalysisInputError("endYear precedes startYear")
    if temporal_precision == "range" and end_year == start_year:
        raise AnalysisInputError("range precision requires a nonzero inclusive span")

    geography_state = _mapping_state(record)
    if "geographyClass" in record:
        geography_class_members = _scalar_dimension(
            record["geographyClass"], "geography_class"
        )
    else:
        geography_class_members = _dimension_array(
            record["geography_class"], "geography_class"
        )
        if not geography_class_members:
            raise AnalysisInputError("governed geography class must be present")
    geography_qualified = record["geographyQualified"]
    multi_region = record["multiRegion"]
    if not isinstance(geography_qualified, bool) or not isinstance(multi_region, bool):
        raise AnalysisInputError("geographyQualified and multiRegion must be boolean")
    if multi_region != (len(dimensions["geography"]) > 1):
        raise AnalysisInputError("multiRegion does not match governed geography cardinality")

    dimensions.update({
        "temporal_precision": _scalar_dimension(temporal_precision, "temporal_precision"),
        "geography_mapping_state": _scalar_dimension(geography_state, "geography_mapping_state"),
        "geography_class": geography_class_members,
        "curated_container": _dimension_array(record.get("curated_container", []), "curated_container"),
        "curated_container_type": _dimension_array(
            record.get("curated_container_type", []), "curated_container_type"
        ),
    })
    return {"objectId": object_id, "dimensions": dimensions}


def _validate_label_registry(records: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, str]]:
    registry: dict[str, dict[str, str]] = {dimension: {} for dimension in DIMENSION_SPECS}
    for record in records:
        for dimension, members in record["dimensions"].items():
            for member in members:
                previous = registry[dimension].setdefault(member["valueId"], member["valueLabel"])
                if previous != member["valueLabel"]:
                    raise AnalysisInputError(
                        f"{dimension} value ID maps to conflicting labels across records"
                    )
    return registry


def _pair_id(left: str, right: str) -> str:
    return f"{left}__{right}"


def _triple_id(first: str, second: str, third: str) -> str:
    return f"{first}__{second}__{third}"


def _normalize_extension_pairs(
    extension_pairs: Iterable[Sequence[str] | Mapping[str, str]],
) -> tuple[tuple[str, str], ...]:
    base_keys = {frozenset(pair) for pair in BASE_PAIR_SPECS}
    normalized: set[tuple[str, str]] = set()
    extension_keys: set[frozenset[str]] = set()
    for pair in extension_pairs:
        if isinstance(pair, Mapping):
            left, right = pair.get("dimensionA"), pair.get("dimensionB")
        elif isinstance(pair, Sequence) and not isinstance(pair, str) and len(pair) == 2:
            left, right = pair
        else:
            raise AnalysisInputError("extension pairs require two dimensions")
        if left not in DIMENSION_SPECS or right not in DIMENSION_SPECS:
            raise AnalysisInputError("extension pair references an unknown dimension")
        if left == right:
            raise AnalysisInputError("extension pair dimensions must differ")
        if not ({str(left), str(right)} & CURATORIAL_DIMENSIONS):
            raise AnalysisInputError("extension pairs must include a curatorial dimension")
        semantic_key = frozenset((str(left), str(right)))
        if semantic_key in base_keys:
            raise AnalysisInputError("extension pair duplicates a frozen base pair")
        if semantic_key in extension_keys:
            raise AnalysisInputError("extension pair duplicates another extension pair")
        extension_keys.add(semantic_key)
        normalized.add((str(left), str(right)))
    return tuple(sorted(normalized, key=lambda pair: _pair_id(*pair)))


def rarity_band(count: int) -> str:
    if count == 1:
        return "SINGLETON"
    if count <= 5:
        return "COUNT_2_TO_5"
    if count <= 20:
        return "COUNT_6_TO_20"
    if count <= 99:
        return "COUNT_21_TO_99"
    return "COUNT_100_PLUS"


def _frequency_rows(
    records: Sequence[Mapping[str, Any]],
    dimensions: Sequence[str],
    labels: Mapping[str, Mapping[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, Counter[str]], dict[str, int]]:
    denominator = len(records)
    counters: dict[str, Counter[str]] = {}
    coverage: dict[str, int] = {}
    rows: list[dict[str, Any]] = []
    for dimension in dimensions:
        counter: Counter[str] = Counter()
        observed_objects = 0
        for record in records:
            members = record["dimensions"][dimension]
            if members:
                observed_objects += 1
            counter.update(member["valueId"] for member in members)
        counters[dimension] = counter
        coverage[dimension] = observed_objects
        assignment_denominator = sum(counter.values())
        spec = DIMENSION_SPECS[dimension]
        for value_id, count in sorted(counter.items()):
            rows.append({
                "dimension": dimension,
                "valueId": value_id,
                "valueLabel": labels[dimension][value_id],
                "objectCount": count,
                "eligibleDenominator": denominator,
                "observedObjectDenominator": observed_objects,
                "objectSupportRate": count / denominator if denominator else 0.0,
                "dimensionAssignmentDenominator": assignment_denominator,
                "assignmentShare": count / assignment_denominator if assignment_denominator else 0.0,
                "rarityBand": rarity_band(count),
                "derivationLevel": spec["derivationLevel"],
                "signalStatus": spec["signalStatus"],
            })
    return rows, counters, coverage


def _pair_rows(
    records: Sequence[Mapping[str, Any]],
    specs: Sequence[tuple[str, str]],
    labels: Mapping[str, Mapping[str, str]],
    marginal_counts: Mapping[str, Counter[str]],
    coverage: Mapping[str, int],
    rare_max_count: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    denominator = len(records)
    rows: list[dict[str, Any]] = []
    density_rows: list[dict[str, Any]] = []
    for left, right in specs:
        counts: Counter[tuple[str, str]] = Counter()
        joint_observable = 0
        for record in records:
            left_members = record["dimensions"][left]
            right_members = record["dimensions"][right]
            if left_members and right_members:
                joint_observable += 1
            counts.update(
                (left_member["valueId"], right_member["valueId"])
                for left_member, right_member in product(left_members, right_members)
            )
        spec_id = _pair_id(left, right)
        for (left_id, right_id), count in sorted(counts.items()):
            left_count = marginal_counts[left][left_id]
            right_count = marginal_counts[right][right_id]
            high_cardinality = "creator" in (left, right)
            rows.append({
                "pairId": spec_id,
                "dimensionA": left,
                "valueAId": left_id,
                "valueALabel": labels[left][left_id],
                "dimensionB": right,
                "valueBId": right_id,
                "valueBLabel": labels[right][right_id],
                "objectCount": count,
                "eligibleDenominator": denominator,
                "jointObservableDenominator": joint_observable,
                "supportRateEligible": count / denominator if denominator else 0.0,
                "supportRateJointObservable": count / joint_observable if joint_observable else 0.0,
                "dimensionAValueObjectCount": left_count,
                "dimensionBValueObjectCount": right_count,
                "conditionalObservedRateAGivenB": count / right_count,
                "conditionalObservedRateBGivenA": count / left_count,
                "liftDiagnostic": (
                    count * denominator / (left_count * right_count)
                    if left_count and right_count and denominator else 0.0
                ),
                "liftReferenceDenominator": denominator,
                "diagnosticStatus": "ANALYSIS_DIAGNOSTIC",
                "rarityBand": rarity_band(count),
                "signalStatus": (
                    "RESEARCH_ONLY_HIGH_CARDINALITY" if high_cardinality else
                    "RARE_INTERSECTION_SIGNAL_CANDIDATE" if count <= rare_max_count else
                    "SUPPORTING_OBSERVED_INTERSECTION"
                ),
            })
        possible_frame = len(marginal_counts[left]) * len(marginal_counts[right])
        density_rows.append({
            "cellKind": "PAIR",
            "specId": spec_id,
            "dimensions": [left, right],
            "observedCellCount": len(counts),
            "observedMembershipEventCount": sum(counts.values()),
            "distinctValueFrameCellCount": possible_frame,
            "observedCellDensity": len(counts) / possible_frame if possible_frame else 0.0,
            "jointObservableObjectCount": joint_observable,
            "eligibleDenominator": denominator,
            "dimensionCoverageCounts": [coverage[left], coverage[right]],
        })
    return rows, density_rows


def _triple_rows(
    records: Sequence[Mapping[str, Any]],
    specs: Sequence[tuple[str, str, str]],
    labels: Mapping[str, Mapping[str, str]],
    marginal_counts: Mapping[str, Counter[str]],
    coverage: Mapping[str, int],
    rare_max_count: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    denominator = len(records)
    rows: list[dict[str, Any]] = []
    density_rows: list[dict[str, Any]] = []
    for first, second, third in specs:
        counts: Counter[tuple[str, str, str]] = Counter()
        joint_observable = 0
        for record in records:
            member_groups = [record["dimensions"][name] for name in (first, second, third)]
            if all(member_groups):
                joint_observable += 1
            counts.update(
                tuple(member["valueId"] for member in combination)
                for combination in product(*member_groups)
            )
        spec_id = _triple_id(first, second, third)
        for value_ids, count in sorted(counts.items()):
            rows.append({
                "tripleId": spec_id,
                "dimensionA": first,
                "valueAId": value_ids[0],
                "valueALabel": labels[first][value_ids[0]],
                "dimensionB": second,
                "valueBId": value_ids[1],
                "valueBLabel": labels[second][value_ids[1]],
                "dimensionC": third,
                "valueCId": value_ids[2],
                "valueCLabel": labels[third][value_ids[2]],
                "objectCount": count,
                "eligibleDenominator": denominator,
                "jointObservableDenominator": joint_observable,
                "supportRateEligible": count / denominator if denominator else 0.0,
                "supportRateJointObservable": count / joint_observable if joint_observable else 0.0,
                "marginalObjectCounts": [
                    marginal_counts[first][value_ids[0]],
                    marginal_counts[second][value_ids[1]],
                    marginal_counts[third][value_ids[2]],
                ],
                "diagnosticStatus": "ANALYSIS_DIAGNOSTIC",
                "rarityBand": rarity_band(count),
                "signalStatus": (
                    "RARE_INTERSECTION_SIGNAL_CANDIDATE" if count <= rare_max_count
                    else "RESEARCH_ONLY_BOUNDED_TRIPLE"
                ),
            })
        possible_frame = (
            len(marginal_counts[first])
            * len(marginal_counts[second])
            * len(marginal_counts[third])
        )
        density_rows.append({
            "cellKind": "BOUNDED_TRIPLE",
            "specId": spec_id,
            "dimensions": [first, second, third],
            "observedCellCount": len(counts),
            "observedMembershipEventCount": sum(counts.values()),
            "distinctValueFrameCellCount": possible_frame,
            "observedCellDensity": len(counts) / possible_frame if possible_frame else 0.0,
            "jointObservableObjectCount": joint_observable,
            "eligibleDenominator": denominator,
            "dimensionCoverageCounts": [coverage[first], coverage[second], coverage[third]],
        })
    return rows, density_rows


def _concentration_metrics(source_counts: Counter[str]) -> dict[str, Any]:
    total = sum(source_counts.values())
    ranked = sorted(source_counts.items(), key=lambda item: (-item[1], item[0]))
    shares = [count / total for _, count in ranked] if total else []
    entropy = -sum(share * math.log(share) for share in shares if share)
    distinct = len(ranked)
    return {
        "objectCount": total,
        "distinctSourceCount": distinct,
        "top1SourceId": ranked[0][0] if ranked else None,
        "top1ObjectCount": ranked[0][1] if ranked else 0,
        "top1Share": shares[0] if shares else 0.0,
        "top5ObjectCount": sum(count for _, count in ranked[:5]),
        "top5Share": sum(shares[:5]),
        "hhi": sum(share * share for share in shares),
        "entropyNats": entropy,
        "normalizedEntropy": entropy / math.log(distinct) if distinct > 1 else 0.0,
    }


def _source_concentration_rows(
    records: Sequence[Mapping[str, Any]],
    labels: Mapping[str, Mapping[str, str]],
    minimum_support: int,
) -> list[dict[str, Any]]:
    global_counts: Counter[str] = Counter()
    subset_sources: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for record in records:
        source_id = record["dimensions"]["source"][0]["valueId"]
        global_counts[source_id] += 1
        for dimension in SOURCE_SUBSET_DIMENSIONS:
            for member in record["dimensions"][dimension]:
                subset_sources[(dimension, member["valueId"])][source_id] += 1

    rows: list[dict[str, Any]] = []
    global_metrics = _concentration_metrics(global_counts)
    global_top_id = global_metrics.pop("top1SourceId")
    rows.append({
        "subsetDimension": "ALL_PUBLIC_OBJECTS",
        "subsetValueId": "ALL_PUBLIC_OBJECTS",
        "subsetValueLabel": "All public objects",
        **global_metrics,
        "top1SourceValueId": global_top_id,
        "top1SourceValueLabel": labels["source"].get(global_top_id) if global_top_id else None,
        "minimumSubsetSupport": minimum_support,
        "supportPolicyStatus": "GLOBAL_EXEMPT",
        "diagnosticStatus": "ANALYSIS_DIAGNOSTIC",
    })
    for (dimension, value_id), source_counts in sorted(subset_sources.items()):
        if sum(source_counts.values()) < minimum_support:
            continue
        metrics = _concentration_metrics(source_counts)
        top_id = metrics.pop("top1SourceId")
        rows.append({
            "subsetDimension": dimension,
            "subsetValueId": value_id,
            "subsetValueLabel": labels[dimension][value_id],
            **metrics,
            "top1SourceValueId": top_id,
            "top1SourceValueLabel": labels["source"].get(top_id) if top_id else None,
            "minimumSubsetSupport": minimum_support,
            "supportPolicyStatus": "MEETS_MINIMUM_SUPPORT",
            "diagnosticStatus": "ANALYSIS_DIAGNOSTIC",
        })
    return rows


def _dimension_concentration_rows(
    records: Sequence[Mapping[str, Any]],
    labels: Mapping[str, Mapping[str, str]],
    derivation_version: str,
) -> list[dict[str, Any]]:
    """Build four corpus diagnostics directly from unique object memberships.

    Coverage and missingness use the eligible-object denominator. Top-k shares,
    HHI, and entropy use the assignment denominator. This distinction matters
    for multi-valued decade, geography, and curated-container dimensions.
    """

    eligible = len(records)
    rows: list[dict[str, Any]] = []
    for spec in DIMENSION_CONCENTRATION_SPECS:
        dimension = str(spec["dimension"])
        counts: Counter[str] = Counter()
        observed_objects = 0
        for record in records:
            value_ids = {
                str(member["valueId"])
                for member in record["dimensions"][dimension]
            }
            if value_ids:
                observed_objects += 1
            counts.update(value_ids)

        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        assignment_count = sum(counts.values())
        shares = (
            [count / assignment_count for _, count in ranked]
            if assignment_count else []
        )
        entropy = -sum(share * math.log(share) for share in shares if share)
        distinct = len(ranked)
        top_id = ranked[0][0] if ranked else None
        row = {
            **spec,
            "derivationVersion": derivation_version,
            "eligibleDenominator": eligible,
            "observedObjectCount": observed_objects,
            "unassignedObjectCount": eligible - observed_objects,
            "assignmentCount": assignment_count,
            "assignmentDenominator": assignment_count,
            "distinctValueCount": distinct,
            "top1ValueId": top_id,
            "top1ValueLabel": labels[dimension].get(top_id) if top_id else None,
            "top1AssignmentCount": ranked[0][1] if ranked else 0,
            "top1Share": shares[0] if shares else 0.0,
            "top5AssignmentCount": sum(count for _, count in ranked[:5]),
            "top5Share": sum(shares[:5]),
            "hhi": sum(share * share for share in shares),
            "shannonEntropyNats": entropy,
            "normalizedEntropy": entropy / math.log(distinct) if distinct > 1 else 0.0,
            "membershipPolicy": "UNIQUE_PER_OBJECT_VALUE_MEMBERSHIP",
            "shareDenominatorSemantics": "UNIQUE_OBJECT_VALUE_ASSIGNMENTS",
            "eligibleDenominatorSemantics": "AUTHORITATIVE_PUBLIC_OBJECTS",
            "diagnosticStatus": "ANALYSIS_DIAGNOSTIC_NOT_A_RELATION",
            "deterministic": True,
            "historicalRelation": False,
            "semanticRelation": False,
        }
        if assignment_count < observed_objects:
            raise AnalysisInputError(
                f"{dimension} assignment count is below observed-object coverage"
            )
        if row["top1AssignmentCount"] > assignment_count:
            raise AnalysisInputError(f"{dimension} top-1 count exceeds assignments")
        row["receiptSha256"] = sha256_json(row)
        rows.append(row)
    return rows


def _rarity_summary(
    frequency_rows: Sequence[Mapping[str, Any]],
    pair_rows: Sequence[Mapping[str, Any]],
    triple_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    counters: dict[str, Counter[str]] = {
        "ONE_DIMENSIONAL": Counter(row["rarityBand"] for row in frequency_rows),
        "PAIR": Counter(row["rarityBand"] for row in pair_rows),
        "BOUNDED_TRIPLE": Counter(row["rarityBand"] for row in triple_rows),
    }
    return [
        {"cellKind": cell_kind, "rarityBand": band, "observedCellCount": count}
        for cell_kind, counter in counters.items()
        for band, count in sorted(counter.items())
    ]


def analyze(
    records: Iterable[Mapping[str, Any]],
    *,
    derivation_version: str = DEFAULT_DERIVATION_VERSION,
    expected_count: int | None = None,
    extension_pairs: Iterable[Sequence[str] | Mapping[str, str]] = (),
    minimum_subset_support: int = DEFAULT_MINIMUM_SUBSET_SUPPORT,
    rare_max_count: int = DEFAULT_RARE_MAX_COUNT,
) -> dict[str, Any]:
    """Return deterministic observed cells and concentration diagnostics."""

    started = time.perf_counter()
    derivation_version = _require_text(derivation_version, "derivation_version")
    if (
        isinstance(minimum_subset_support, bool)
        or not isinstance(minimum_subset_support, int)
        or minimum_subset_support < 1
    ):
        raise AnalysisInputError("minimum_subset_support must be a positive integer")
    if (
        isinstance(rare_max_count, bool)
        or not isinstance(rare_max_count, int)
        or not 1 <= rare_max_count <= 20
    ):
        raise AnalysisInputError("rare_max_count must be an integer from 1 through 20")
    normalized = sorted((_normalize_record(record) for record in records), key=lambda row: row["objectId"])
    if expected_count is not None and len(normalized) != expected_count:
        raise AnalysisInputError(f"expected {expected_count} public records, found {len(normalized)}")
    object_ids = [record["objectId"] for record in normalized]
    if len(object_ids) != len(set(object_ids)):
        raise AnalysisInputError("duplicate public objectId in analysis cohort")

    labels = _validate_label_registry(normalized)
    extensions = _normalize_extension_pairs(extension_pairs)
    pair_specs = tuple(BASE_PAIR_SPECS) + extensions
    frequency_dimensions = list(BASE_FREQUENCY_DIMENSIONS)
    for dimension in sorted({value for pair in extensions for value in pair}):
        if dimension not in frequency_dimensions:
            frequency_dimensions.append(dimension)

    frequency_rows, marginal_counts, coverage = _frequency_rows(
        normalized, frequency_dimensions, labels
    )
    pair_rows, pair_density = _pair_rows(
        normalized, pair_specs, labels, marginal_counts, coverage, rare_max_count
    )
    triple_rows, triple_density = _triple_rows(
        normalized, BASE_TRIPLE_SPECS, labels, marginal_counts, coverage, rare_max_count
    )
    concentration_rows = _source_concentration_rows(
        normalized, labels, minimum_subset_support
    )
    dimension_concentration_rows = _dimension_concentration_rows(
        normalized, labels, derivation_version
    )
    global_source_row = next(
        row
        for row in concentration_rows
        if row["subsetDimension"] == "ALL_PUBLIC_OBJECTS"
    )
    native_source_row = next(
        row for row in dimension_concentration_rows if row["dimension"] == "source"
    )
    source_reconciliation = {
        "objectCount": "assignmentCount",
        "distinctSourceCount": "distinctValueCount",
        "top1SourceValueId": "top1ValueId",
        "top1ObjectCount": "top1AssignmentCount",
        "top1Share": "top1Share",
        "top5ObjectCount": "top5AssignmentCount",
        "top5Share": "top5Share",
        "hhi": "hhi",
        "entropyNats": "shannonEntropyNats",
        "normalizedEntropy": "normalizedEntropy",
    }
    if any(
        global_source_row[source_key] != native_source_row[native_key]
        for source_key, native_key in source_reconciliation.items()
    ):
        raise AnalysisInputError(
            "native source concentration differs from the preserved source census"
        )
    density_rows = pair_density + triple_density
    rarity_rows = _rarity_summary(frequency_rows, pair_rows, triple_rows)

    deterministic_payload = {
        "schemaVersion": SCHEMA_VERSION,
        "derivationVersion": derivation_version,
        "population": {
            "publicObjectCount": len(normalized),
            "heldObjectCount": 0,
            "eligibleDenominator": len(normalized),
        },
        "policies": {
            "cellPolicy": "OBSERVED_CELLS_ONLY_NO_CARTESIAN_ZERO_ROWS",
            "membershipPolicy": "UNIQUE_OBJECT_MEMBERSHIP_PER_VALUE_OR_CELL",
            "minimumSubsetSupport": minimum_subset_support,
            "rareIntersectionMaximumCount": rare_max_count,
            "conditionalAndLiftStatus": "ANALYSIS_DIAGNOSTIC",
            "creatorMediumStatus": "RESEARCH_ONLY_HIGH_CARDINALITY",
            "tripleStatus": "RESEARCH_ONLY_BOUNDED_TRIPLE",
            "dimensionConcentrationMembershipPolicy": (
                "UNIQUE_PER_OBJECT_VALUE_MEMBERSHIP"
            ),
            "dimensionConcentrationShareDenominator": (
                "UNIQUE_OBJECT_VALUE_ASSIGNMENTS"
            ),
            "probabilityModelSelected": False,
            "similarityFunctionSelected": False,
            "featureWeightsSelected": False,
            "clusterModelSelected": False,
        },
        "dimensionRegistry": [
            {"dimension": dimension, **DIMENSION_SPECS[dimension]}
            for dimension in frequency_dimensions
        ],
        "pairRegistry": [
            {
                "pairId": _pair_id(*pair),
                "dimensions": list(pair),
                "registryStatus": "FROZEN_BASE" if pair in BASE_PAIR_SPECS else "CURATORIAL_EXTENSION",
            }
            for pair in pair_specs
        ],
        "tripleRegistry": [
            {
                "tripleId": _triple_id(*triple),
                "dimensions": list(triple),
                "registryStatus": "FROZEN_BOUNDED_TRIPLE",
            }
            for triple in BASE_TRIPLE_SPECS
        ],
        "frequencyRows": frequency_rows,
        "pairRows": pair_rows,
        "tripleRows": triple_rows,
        "densityRows": density_rows,
        "raritySummaryRows": rarity_rows,
        "sourceConcentrationRows": concentration_rows,
        "dimensionConcentrationRows": dimension_concentration_rows,
        "deferredFamilies": [
            {"family": "geographic_distance", "status": "DEFER", "reason": "No distance semantics selected."},
            {
                "family": "rights_or_image_state",
                "status": "DEFER_NOT_GOVERNED",
                "reason": "No governed public aggregate class is available.",
            },
            {
                "family": "raw_source_collection",
                "status": "NOT_GOVERNED",
                "reason": "Internal source diagnostic is not a public direct feature.",
            },
        ],
        "invariants": {
            "observedCellsOnly": True,
            "zeroCountRowsEmitted": 0,
            "heldObjectsIncluded": 0,
            "objectIdsEmittedInAggregateRows": 0,
            "rawFolderIdsEmitted": 0,
            "internalUuidExposureCount": 0,
            "titleExposureCount": 0,
            "urlExposureCount": 0,
            "dimensionConcentrationRowsComplete": True,
            "dimensionConcentrationSourceGlobalReconciled": True,
            "dimensionConcentrationUsesUniqueMemberships": True,
            "dimensionConcentrationSeparatesAssignmentAndEligibleDenominators": True,
            "dimensionConcentrationHistoricalRelation": False,
            "dimensionConcentrationSemanticRelation": False,
        },
    }
    deterministic_hash = sha256_json(deterministic_payload)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return {
        **deterministic_payload,
        "hashes": {
            "cohortObjectIdSetSha256": sha256_json(object_ids),
            "frequencyRowsSha256": sha256_json(frequency_rows),
            "pairRowsSha256": sha256_json(pair_rows),
            "tripleRowsSha256": sha256_json(triple_rows),
            "sourceConcentrationRowsSha256": sha256_json(concentration_rows),
            "dimensionConcentrationRowsSha256": sha256_json(
                dimension_concentration_rows
            ),
            "deterministicPayloadSha256": deterministic_hash,
        },
        "metrics": {
            "elapsedMs": round(elapsed_ms, 3),
            "normalizedRecordCount": len(normalized),
            "dimensionMembershipEventCount": sum(row["objectCount"] for row in frequency_rows),
            "frequencyRowCount": len(frequency_rows),
            "pairObservedCellCount": len(pair_rows),
            "pairMembershipEventCount": sum(row["objectCount"] for row in pair_rows),
            "tripleObservedCellCount": len(triple_rows),
            "tripleMembershipEventCount": sum(row["objectCount"] for row in triple_rows),
            "densityRowCount": len(density_rows),
            "sourceConcentrationRowCount": len(concentration_rows),
            "dimensionConcentrationRowCount": len(dimension_concentration_rows),
            "maximumDimensionMembersPerObject": max((
                sum(len(members) for members in record["dimensions"].values())
                for record in normalized
            ), default=0),
            "aggregateCanonicalBytes": len(canonical_json_bytes(deterministic_payload)),
        },
    }


def _synthetic_records() -> list[dict[str, Any]]:
    base = {
        "medium": [{"id": "CTX:MEDIUM:A", "label": "Medium A"}],
        "theme": [{"id": "CTX:THEME:X", "label": "Theme X"}],
        "movement_context": [],
        "decade": [{"id": "SPT:1900", "label": "1900s"}],
        "geography": [{"id": "SPTGEO:A", "label": "Place A"}],
        "source": "Source A",
        "object_type": "Poster",
        "creator": "Unknown",
        "temporalPrecision": "year",
        "startYear": 1901,
        "endYear": 1901,
        "geographyState": "mapped",
        "geographyClass": "country",
        "geographyQualified": False,
        "multiRegion": False,
        "curated_container": [
            {"id": "analysis:curated_container:sha256:container-a", "label": "Container A"}
        ],
        "curated_container_type": ["Exhibition"],
    }
    second = {
        **base,
        "objectId": "SURF-TEST-002",
        "medium": [
            {"id": "CTX:MEDIUM:A", "label": "Medium A"},
            {"id": "CTX:MEDIUM:A", "label": "Medium A"},
        ],
        "theme": [
            {"id": "CTX:THEME:X", "label": "Theme X"},
            {"id": "CTX:THEME:Y", "label": "Theme Y"},
        ],
        "source": "Source B",
        "curated_container": [
            {"id": "analysis:curated_container:sha256:container-a", "label": "Container A"},
            {"id": "analysis:curated_container:sha256:container-a", "label": "Container A"},
            {"id": "analysis:curated_container:sha256:container-b", "label": "Container B"},
        ],
        "curated_container_type": [],
    }
    third = {
        **base,
        "objectId": "SURF-TEST-003",
        "medium": [{"id": "CTX:MEDIUM:B", "label": "Medium B"}],
        "theme": [{"id": "CTX:THEME:Y", "label": "Theme Y"}],
        "movement_context": [{"id": "CTX:MOVEMENT:M", "label": "Movement M"}],
        "decade": [{"id": "SPT:1910", "label": "1910s"}],
        "geography": [{"id": "SPTGEO:B", "label": "Place B"}],
        "source": "Source A",
        "creator": "Known Creator",
        "startYear": 1911,
        "endYear": 1911,
        "curated_container": [
            {"id": "analysis:curated_container:sha256:container-b", "label": "Container B"}
        ],
        "curated_container_type": ["Publication"],
    }
    return [{**base, "objectId": "SURF-TEST-001"}, second, third]


def run_self_tests() -> dict[str, Any]:
    records = _synthetic_records()
    extension = [("curated_container_type", "decade")]
    first = analyze(
        records,
        expected_count=3,
        extension_pairs=extension,
        minimum_subset_support=2,
    )
    second = analyze(
        list(reversed(records)),
        expected_count=3,
        extension_pairs=list(reversed(extension)),
        minimum_subset_support=2,
    )
    assert first["hashes"] == second["hashes"]
    medium_a_id = "CTX:MEDIUM:A"
    theme_x_id = "CTX:THEME:X"
    theme_pair = [row for row in first["pairRows"] if row["pairId"] == "medium__theme"]
    assert next(
        row["objectCount"] for row in theme_pair
        if row["valueAId"] == medium_a_id and row["valueBId"] == theme_x_id
    ) == 2
    assert not any(
        row["valueAId"] == "CTX:MEDIUM:B" and row["valueBId"] == theme_x_id
        for row in theme_pair
    )
    assert all(row["objectCount"] > 0 for row in first["pairRows"] + first["tripleRows"])
    assert any(row["registryStatus"] == "CURATORIAL_EXTENSION" for row in first["pairRegistry"])
    assert first["invariants"]["objectIdsEmittedInAggregateRows"] == 0
    concentration = {
        row["dimension"]: row for row in first["dimensionConcentrationRows"]
    }
    assert set(concentration) == {"source", "decade", "geography", "curated_container"}
    assert first["metrics"]["dimensionConcentrationRowCount"] == 4
    assert concentration["source"]["assignmentCount"] == 3
    assert concentration["source"]["eligibleDenominator"] == 3
    assert concentration["source"]["top1AssignmentCount"] == 2
    assert concentration["curated_container"]["assignmentCount"] == 4
    assert concentration["curated_container"]["assignmentDenominator"] == 4
    assert concentration["curated_container"]["eligibleDenominator"] == 3
    assert concentration["curated_container"]["top1AssignmentCount"] == 2
    assert all(row["deterministic"] is True for row in concentration.values())
    assert all(row["historicalRelation"] is False for row in concentration.values())
    assert all(row["semanticRelation"] is False for row in concentration.values())

    failures = 0
    adversaries: list[tuple[list[dict[str, Any]], dict[str, Any]]] = [
        ([records[0], records[0]], {}),
        ([{**records[0], "objectId": "123e4567-e89b-12d3-a456-426614174000"}], {}),
        ([{**records[0], "held": True}], {}),
        ([{**records[0], "medium": "not-an-array"}], {}),
        ([records[0]], {"extension_pairs": [("source", "theme")]}),
        ([records[0]], {"extension_pairs": [("curated_container", "curated_container")]}),
        ([records[0]], {"minimum_subset_support": 0}),
        ([{**records[0], "source": "https://unsafe.example"}], {}),
    ]
    for adversary_records, kwargs in adversaries:
        try:
            analyze(adversary_records, **kwargs)
        except AnalysisInputError:
            failures += 1
    assert failures == len(adversaries)
    return {
        "status": "PASS",
        "checks": 28,
        "adversaries": len(adversaries),
        "deterministicPayloadSha256": first["hashes"]["deterministicPayloadSha256"],
    }


def _load_cli_records(path: Path) -> list[Mapping[str, Any]]:
    payload = json.loads(path.read_text("utf-8"))
    records = payload.get("records") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise AnalysisInputError("CLI input must be an array or an object with records[]")
    return records


def _parse_extension_pair(text: str) -> tuple[str, str]:
    parts = text.split(":")
    if len(parts) != 2 or not all(parts):
        raise argparse.ArgumentTypeError("extension pair must be DIMENSION_A:DIMENSION_B")
    return parts[0], parts[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-count", type=int)
    parser.add_argument("--minimum-subset-support", type=int, default=DEFAULT_MINIMUM_SUBSET_SUPPORT)
    parser.add_argument("--extension-pair", type=_parse_extension_pair, action="append", default=[])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(run_self_tests(), sort_keys=True))
        return
    if args.input is None or args.output is None:
        parser.error("--input and --output are required unless --self-test is used")
    result = analyze(
        _load_cli_records(args.input),
        expected_count=args.expected_count,
        extension_pairs=args.extension_pair,
        minimum_subset_support=args.minimum_subset_support,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json_bytes(result))
    print(json.dumps({
        "status": "PASS",
        "output": str(args.output),
        "records": result["population"]["publicObjectCount"],
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
