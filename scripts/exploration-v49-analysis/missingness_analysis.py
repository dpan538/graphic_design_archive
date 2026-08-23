#!/usr/bin/env python3
"""Deterministic public-cohort missingness and uncertainty analysis.

The module consumes centrally normalized public records. It does not open the
candidate database, infer eligibility, or serialize source rows. Object vectors
are analysis-only and may be written only to a requested temporary JSON path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "trace-exploration-missingness-analysis/v1"
DEFAULT_DERIVATION_VERSION = "trace-exploration-missingness-v1"

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

TAXONOMY = (
    {
        "class": "OBSERVED",
        "meaning": "A governed or explicitly classified value is present.",
        "isGenericMissing": False,
        "applicability": "object field",
    },
    {
        "class": "UNKNOWN_SOURCE_VALUE",
        "meaning": "The public source value explicitly states unknown.",
        "isGenericMissing": False,
        "applicability": "creator attribution",
    },
    {
        "class": "QUALIFIED_UNKNOWN_SOURCE_VALUE",
        "meaning": "The public source states unknown with a bounded role qualifier.",
        "isGenericMissing": False,
        "applicability": "creator attribution",
    },
    {
        "class": "NO_PUBLISHED_MOVEMENT_CONTEXT",
        "meaning": "No governed movement-context representation is published for the object.",
        "isGenericMissing": False,
        "applicability": "movement_context",
    },
    {
        "class": "APPROXIMATE",
        "meaning": "The governed temporal observation retains approximate precision.",
        "isGenericMissing": False,
        "applicability": "temporal precision",
    },
    {
        "class": "RANGE",
        "meaning": "The governed temporal observation is an inclusive range.",
        "isGenericMissing": False,
        "applicability": "temporal precision",
    },
    {
        "class": "AGGREGATE_ONLY",
        "meaning": "The governed geography remains countable without a map point.",
        "isGenericMissing": False,
        "applicability": "geography mapping state",
    },
    {
        "class": "UNMAPPED",
        "meaning": "The governed geography has no selected geometry mapping.",
        "isGenericMissing": False,
        "applicability": "geography mapping state",
    },
    {
        "class": "QUALIFIED",
        "meaning": "A governed value carries an explicit qualification.",
        "isGenericMissing": False,
        "applicability": "geography governance",
    },
    {
        "class": "NOT_GOVERNED",
        "meaning": "A source diagnostic exists but is not a governed public direct feature.",
        "isGenericMissing": False,
        "applicability": "field-level diagnostics only",
    },
)

TEMPORAL_PRECISIONS = frozenset({"year", "approximate", "day", "month", "range", "unknown"})
GEOGRAPHY_STATES = frozenset({"mapped", "aggregate_only", "unmapped"})
UUID_PATTERN = re.compile(
    r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[1-5][0-9A-Fa-f]{3}"
    r"-[89ABab][0-9A-Fa-f]{3}-[0-9A-Fa-f]{12}(?![0-9A-Fa-f])"
)
URL_PATTERN = re.compile(r"(?:https?://|file://)", re.IGNORECASE)
PUBLIC_ID_PATTERN = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
ROLE_QUALIFIED_UNKNOWN_PATTERN = re.compile(
    r"^(?:unknown;\s*(?:artist|artists|designer|designers|maker|makers|"
    r"photographer|photographers|printer|printers)(?:\s+\(people\))?|"
    r"(?:artist|designer|creator):\s*unknown)$",
    re.IGNORECASE,
)

STATE_ORDER = (
    "MOVEMENT_CONTEXT:NO_PUBLISHED_MOVEMENT_CONTEXT",
    "TEMPORAL:APPROXIMATE",
    "TEMPORAL:RANGE",
    "TEMPORAL:UNKNOWN_SOURCE_VALUE",
    "GEOGRAPHY:AGGREGATE_ONLY",
    "GEOGRAPHY:UNMAPPED",
    "GEOGRAPHY:QUALIFIED",
    "GEOGRAPHY:MULTI_REGION",
    "CREATOR:UNKNOWN_SOURCE_VALUE",
    "CREATOR:QUALIFIED_UNKNOWN_SOURCE_VALUE",
)
STATE_RANK = {state: index for index, state in enumerate(STATE_ORDER)}


class AnalysisInputError(ValueError):
    """Raised when a normalized analysis input violates the public contract."""


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
    if URL_PATTERN.search(value):
        raise AnalysisInputError(f"{field} contains a URL")
    if UUID_PATTERN.search(value):
        raise AnalysisInputError(f"{field} contains an internal UUID")
    return value.strip()


def derived_value_id(namespace: str, label: str) -> str:
    """Derive a stable analysis-only ID without exposing a source identifier."""

    safe_namespace = re.sub(r"[^a-z0-9_]+", "_", namespace.casefold()).strip("_")
    if not safe_namespace:
        raise AnalysisInputError("dimension namespace must contain a safe character")
    digest = hashlib.sha256(f"{safe_namespace}\0{label}".encode("utf-8")).hexdigest()
    return f"analysis:{safe_namespace}:sha256:{digest[:24]}"


def normalize_dimension_member(value: Any, namespace: str) -> dict[str, str]:
    """Normalize either a safe label or a governed ``{id,label}`` member."""

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


def _unique_dimension_array(value: Any, field: str) -> tuple[dict[str, str], ...]:
    if not isinstance(value, (list, tuple)):
        raise AnalysisInputError(f"{field} must be an array")
    by_id: dict[str, str] = {}
    for item in value:
        member = normalize_dimension_member(item, field)
        previous = by_id.setdefault(member["valueId"], member["valueLabel"])
        if previous != member["valueLabel"]:
            raise AnalysisInputError(f"{field} reuses a value ID with conflicting labels")
    return tuple(
        {"valueId": value_id, "valueLabel": label}
        for value_id, label in sorted(by_id.items())
    )


def _require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise AnalysisInputError(f"{field} must be boolean")
    return value


def _require_year(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AnalysisInputError(f"{field} must be an integer year")
    if value < 0 or value > 9999:
        raise AnalysisInputError(f"{field} is outside the supported year range")
    return value


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


def creator_state(value: str) -> str:
    normalized = value.strip().casefold()
    if normalized == "unknown":
        return "UNKNOWN_SOURCE_VALUE"
    if ROLE_QUALIFIED_UNKNOWN_PATTERN.fullmatch(normalized):
        return "QUALIFIED_UNKNOWN_SOURCE_VALUE"
    return "OBSERVED"


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
    medium = _unique_dimension_array(record["medium"], "medium")
    theme = _unique_dimension_array(record["theme"], "theme")
    movement = _unique_dimension_array(record["movement_context"], "movement_context")
    decade = _unique_dimension_array(record["decade"], "decade")
    geography = _unique_dimension_array(record["geography"], "geography")
    if not medium or not theme or not decade or not geography:
        raise AnalysisInputError("governed medium/theme/decade/geography must be present")

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
        geography_class = normalize_dimension_member(
            record["geographyClass"], "geography_class"
        )["valueLabel"]
    else:
        geography_class_members = _unique_dimension_array(
            record["geography_class"], "geography_class"
        )
        if not geography_class_members:
            raise AnalysisInputError("governed geography class must be present")
        geography_class = "|".join(
            member["valueLabel"] for member in geography_class_members
        )
    geography_qualified = _require_bool(record["geographyQualified"], "geographyQualified")
    multi_region = _require_bool(record["multiRegion"], "multiRegion")
    if multi_region != (len(geography) > 1):
        raise AnalysisInputError("multiRegion does not match governed geography cardinality")

    source_collection_present = record.get("sourceCollectionPresent")
    if source_collection_present is not None and not isinstance(source_collection_present, bool):
        raise AnalysisInputError("sourceCollectionPresent must be boolean or absent")

    return {
        "objectId": object_id,
        "medium": medium,
        "theme": theme,
        "movement_context": movement,
        "decade": decade,
        "geography": geography,
        "source": normalize_dimension_member(record["source"], "source")["valueLabel"],
        "object_type": normalize_dimension_member(
            record["object_type"], "object_type"
        )["valueLabel"],
        "creator": normalize_dimension_member(record["creator"], "creator")["valueLabel"],
        "temporalPrecision": temporal_precision,
        "startYear": start_year,
        "endYear": end_year,
        "geographyState": geography_state,
        "geographyClass": geography_class,
        "geographyQualified": geography_qualified,
        "multiRegion": multi_region,
        "sourceCollectionPresent": source_collection_present,
    }


def _active_states(record: Mapping[str, Any], creator_status: str) -> tuple[str, ...]:
    states: list[str] = []
    if not record["movement_context"]:
        states.append("MOVEMENT_CONTEXT:NO_PUBLISHED_MOVEMENT_CONTEXT")
    if record["temporalPrecision"] == "approximate":
        states.append("TEMPORAL:APPROXIMATE")
    elif record["temporalPrecision"] == "range":
        states.append("TEMPORAL:RANGE")
    elif record["temporalPrecision"] == "unknown":
        states.append("TEMPORAL:UNKNOWN_SOURCE_VALUE")
    if record["geographyState"] == "aggregate_only":
        states.append("GEOGRAPHY:AGGREGATE_ONLY")
    elif record["geographyState"] == "unmapped":
        states.append("GEOGRAPHY:UNMAPPED")
    if record["geographyQualified"]:
        states.append("GEOGRAPHY:QUALIFIED")
    if record["multiRegion"]:
        states.append("GEOGRAPHY:MULTI_REGION")
    if creator_status == "UNKNOWN_SOURCE_VALUE":
        states.append("CREATOR:UNKNOWN_SOURCE_VALUE")
    elif creator_status == "QUALIFIED_UNKNOWN_SOURCE_VALUE":
        states.append("CREATOR:QUALIFIED_UNKNOWN_SOURCE_VALUE")
    return tuple(sorted(states, key=lambda state: (STATE_RANK.get(state, len(STATE_RANK)), state)))


def _field_matrix(
    vectors: list[dict[str, Any]],
    precision_counts: Counter[str],
    geography_counts: Counter[str],
    creator_counts: Counter[str],
) -> list[dict[str, Any]]:
    denominator = len(vectors)
    movement_present = sum(vector["movementContextCount"] > 0 for vector in vectors)
    collection_provided = sum(vector["sourceCollectionPresent"] is not None for vector in vectors)
    collection_present = sum(vector["sourceCollectionPresent"] is True for vector in vectors)
    return [
        {
            "field": "medium",
            "governanceState": "LEVEL_A_GOVERNED_DIRECT_FEATURE",
            "eligibleDenominator": denominator,
            "stateCounts": {"OBSERVED": denominator},
        },
        {
            "field": "theme",
            "governanceState": "LEVEL_A_GOVERNED_DIRECT_FEATURE",
            "eligibleDenominator": denominator,
            "stateCounts": {"OBSERVED": denominator},
        },
        {
            "field": "movement_context",
            "governanceState": "LEVEL_A_GOVERNED_DIRECT_FEATURE",
            "eligibleDenominator": denominator,
            "stateCounts": {
                "OBSERVED": movement_present,
                "NO_PUBLISHED_MOVEMENT_CONTEXT": denominator - movement_present,
            },
        },
        {
            "field": "temporal_precision",
            "governanceState": "LEVEL_A_GOVERNED_DIRECT_FEATURE",
            "eligibleDenominator": denominator,
            "stateCounts": dict(sorted(precision_counts.items())),
            "uncertaintyCounts": {
                "APPROXIMATE": precision_counts["approximate"],
                "RANGE": precision_counts["range"],
                "UNKNOWN_SOURCE_VALUE": precision_counts["unknown"],
            },
        },
        {
            "field": "geography_mapping_state",
            "governanceState": "LEVEL_A_GOVERNED_DIRECT_FEATURE",
            "eligibleDenominator": denominator,
            "stateCounts": dict(sorted(geography_counts.items())),
            "qualifierCounts": {
                "QUALIFIED": sum(vector["geographyQualified"] for vector in vectors),
                "MULTI_REGION": sum(vector["multiRegion"] for vector in vectors),
            },
        },
        {
            "field": "creator",
            "governanceState": "PUBLIC_ROOT_METADATA_ANALYSIS_ONLY",
            "eligibleDenominator": denominator,
            "stateCounts": dict(sorted(creator_counts.items())),
            "nullMissingCount": 0,
        },
        {
            "field": "source",
            "governanceState": "PUBLIC_ROOT_METADATA_ANALYSIS_ONLY",
            "eligibleDenominator": denominator,
            "stateCounts": {"OBSERVED": denominator},
            "nullMissingCount": 0,
        },
        {
            "field": "object_type",
            "governanceState": "PUBLIC_ROOT_METADATA_ANALYSIS_ONLY",
            "eligibleDenominator": denominator,
            "stateCounts": {"OBSERVED": denominator},
            "nullMissingCount": 0,
        },
        {
            "field": "source_collection",
            "governanceState": "NOT_GOVERNED",
            "eligibleDenominator": denominator,
            "diagnosticProvidedCount": collection_provided,
            "diagnosticPresenceCount": collection_present,
            "diagnosticAbsenceCount": collection_provided - collection_present,
            "missingCount": 0,
            "interpretation": "Internal source diagnostic only; absence is not public missingness.",
        },
    ]


def analyze(
    records: Iterable[Mapping[str, Any]],
    *,
    derivation_version: str = DEFAULT_DERIVATION_VERSION,
    expected_count: int | None = None,
    include_object_vectors: bool = True,
) -> dict[str, Any]:
    """Analyze a centrally normalized, public-only record iterable."""

    started = time.perf_counter()
    derivation_version = _require_text(derivation_version, "derivation_version")
    normalized = sorted((_normalize_record(record) for record in records), key=lambda row: row["objectId"])
    if expected_count is not None and len(normalized) != expected_count:
        raise AnalysisInputError(f"expected {expected_count} public records, found {len(normalized)}")
    object_ids = [record["objectId"] for record in normalized]
    if len(object_ids) != len(set(object_ids)):
        raise AnalysisInputError("duplicate public objectId in analysis cohort")

    vectors: list[dict[str, Any]] = []
    precision_counts: Counter[str] = Counter()
    geography_counts: Counter[str] = Counter()
    creator_counts: Counter[str] = Counter()
    state_counts: Counter[str] = Counter()
    cooccurrence_counts: Counter[tuple[str, str]] = Counter()
    pathological: dict[str, str] = {}

    for record in normalized:
        precision_counts[record["temporalPrecision"]] += 1
        geography_counts[record["geographyState"]] += 1
        creator_status = creator_state(record["creator"])
        creator_counts[creator_status] += 1
        active_states = _active_states(record, creator_status)
        for state in active_states:
            state_counts[state] += 1
            pathological.setdefault(state, record["objectId"])
        for index, left in enumerate(active_states):
            for right in active_states[index + 1:]:
                cooccurrence_counts[(left, right)] += 1
        vectors.append({
            "objectId": record["objectId"],
            "movementContextState": (
                "OBSERVED" if record["movement_context"] else "NO_PUBLISHED_MOVEMENT_CONTEXT"
            ),
            "movementContextCount": len(record["movement_context"]),
            "temporalPrecision": record["temporalPrecision"],
            "temporalUncertaintyState": (
                "APPROXIMATE" if record["temporalPrecision"] == "approximate" else
                "RANGE" if record["temporalPrecision"] == "range" else
                "UNKNOWN_SOURCE_VALUE" if record["temporalPrecision"] == "unknown" else
                "OBSERVED"
            ),
            "temporalRangeSpanYears": (
                record["endYear"] - record["startYear"] + 1
                if record["temporalPrecision"] == "range" else None
            ),
            "geographyMappingState": record["geographyState"],
            "geographyClass": record["geographyClass"],
            "geographyQualified": record["geographyQualified"],
            "multiRegion": record["multiRegion"],
            "creatorState": creator_status,
            "sourceState": "OBSERVED",
            "objectTypeState": "OBSERVED",
            "sourceCollectionPresent": record["sourceCollectionPresent"],
            "activeStates": list(active_states),
        })

    denominator = len(vectors)
    field_matrix = _field_matrix(vectors, precision_counts, geography_counts, creator_counts)
    cooccurrences = [
        {
            "stateA": left,
            "stateB": right,
            "count": count,
            "eligibleDenominator": denominator,
            "supportRate": count / denominator if denominator else 0.0,
            "interpretation": "OBSERVED_INTERSECTION_ONLY_NO_CAUSAL_INFERENCE",
        }
        for (left, right), count in sorted(cooccurrence_counts.items())
    ]
    if vectors:
        densest = min(vectors, key=lambda row: (-len(row["activeStates"]), row["objectId"]))
        pathological["MAX_ACTIVE_STATE_COUNT"] = densest["objectId"]

    deterministic_payload = {
        "schemaVersion": SCHEMA_VERSION,
        "derivationVersion": derivation_version,
        "population": {
            "publicObjectCount": denominator,
            "heldObjectCount": 0,
            "objectVectorCount": len(vectors),
        },
        "taxonomy": list(TAXONOMY),
        "orthogonalFlags": [{
            "flag": "MULTI_REGION",
            "meaning": "More than one governed geography assignment; not a missingness class.",
        }],
        "fieldMatrix": field_matrix,
        "stateCounts": dict(sorted(state_counts.items())),
        "cooccurrences": cooccurrences,
        "deferredFields": [
            {
                "field": "rights_delivery_state",
                "status": "DEFER",
                "governanceState": "NOT_GOVERNED",
                "reason": "No governed public Exploration projection exists for per-object rights/delivery state.",
            },
            {
                "field": "image_state",
                "status": "DEFER",
                "governanceState": "NOT_GOVERNED",
                "reason": "No governed public Exploration projection exists for per-object image state.",
            },
        ],
        "pathologicalSelections": dict(sorted(pathological.items())),
        "invariants": {
            "movementAbsenceClass": "NO_PUBLISHED_MOVEMENT_CONTEXT",
            "genericMovementMissingCount": 0,
            "creatorNullMissingCount": 0,
            "heldObjectsIncluded": 0,
            "internalUuidExposureCount": 0,
            "historicalRelation": False,
            "semanticRelation": False,
            "singleUncertaintyScore": False,
        },
    }
    vector_hash = sha256_json(vectors)
    field_matrix_hash = sha256_json(field_matrix)
    cooccurrence_hash = sha256_json(cooccurrences)
    deterministic_hash = sha256_json(deterministic_payload)
    elapsed_ms = (time.perf_counter() - started) * 1000

    return {
        **deterministic_payload,
        "objectVectors": vectors if include_object_vectors else [],
        "hashes": {
            "objectVectorsSha256": vector_hash,
            "fieldMatrixSha256": field_matrix_hash,
            "cooccurrencesSha256": cooccurrence_hash,
            "deterministicPayloadSha256": deterministic_hash,
        },
        "metrics": {
            "elapsedMs": round(elapsed_ms, 3),
            "normalizedRecordCount": len(normalized),
            "objectVectorCount": len(vectors),
            "activeStateEventCount": sum(state_counts.values()),
            "cooccurrenceCellCount": len(cooccurrences),
            "maxActiveStatesPerObject": max((len(row["activeStates"]) for row in vectors), default=0),
            "objectVectorCanonicalBytes": len(canonical_json_bytes(vectors)),
        },
    }


def _synthetic_records() -> list[dict[str, Any]]:
    base = {
        "medium": ["CTX:MEDIUM:A"],
        "theme": ["CTX:THEME:A"],
        "movement_context": [],
        "decade": ["SPT:1900"],
        "geography": ["SPTGEO:A"],
        "source": "Source A",
        "object_type": "Poster",
        "creator": "Known Creator",
        "temporalPrecision": "year",
        "startYear": 1901,
        "endYear": 1901,
        "geographyState": "mapped",
        "geographyClass": "country",
        "geographyQualified": False,
        "multiRegion": False,
        "sourceCollectionPresent": True,
    }
    first = {**base, "objectId": "SURF-TEST-001", "creator": "Unknown"}
    second = {
        **base,
        "objectId": "SURF-TEST-002",
        "creator": "unknown; printers",
        "temporalPrecision": "approximate",
        "geographyState": "aggregate_only",
        "geographyQualified": True,
        "sourceCollectionPresent": False,
    }
    third = {
        **base,
        "objectId": "SURF-TEST-003",
        "movement_context": ["CTX:MOVEMENT:A"],
        "temporalPrecision": "range",
        "startYear": 1900,
        "endYear": 1910,
        "geography": ["SPTGEO:A", "SPTGEO:B"],
        "multiRegion": True,
        "geographyState": "mapped",
    }
    return [first, second, third]


def run_self_tests() -> dict[str, Any]:
    records = _synthetic_records()
    first = analyze(records, expected_count=3)
    second = analyze(list(reversed(records)), expected_count=3)
    assert first["hashes"] == second["hashes"]
    assert first["stateCounts"]["CREATOR:UNKNOWN_SOURCE_VALUE"] == 1
    assert first["stateCounts"]["CREATOR:QUALIFIED_UNKNOWN_SOURCE_VALUE"] == 1
    assert first["stateCounts"]["MOVEMENT_CONTEXT:NO_PUBLISHED_MOVEMENT_CONTEXT"] == 2
    assert first["invariants"]["genericMovementMissingCount"] == 0
    assert first["population"]["heldObjectCount"] == 0
    assert creator_state("Unknown artist printed by a known printer") == "OBSERVED"

    failures = 0
    adversaries = [
        [records[0], records[0]],
        [{**records[0], "objectId": "123e4567-e89b-12d3-a456-426614174000"}],
        [{**records[0], "held": True}],
        [{**records[0], "temporalPrecision": "invented"}],
        [{**records[0], "multiRegion": True}],
    ]
    for adversary in adversaries:
        try:
            analyze(adversary)
        except AnalysisInputError:
            failures += 1
    assert failures == len(adversaries)
    return {
        "status": "PASS",
        "checks": 12,
        "adversaries": len(adversaries),
        "deterministicPayloadSha256": first["hashes"]["deterministicPayloadSha256"],
    }


def _load_cli_records(path: Path) -> list[Mapping[str, Any]]:
    payload = json.loads(path.read_text("utf-8"))
    records = payload.get("records") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise AnalysisInputError("CLI input must be an array or an object with records[]")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-count", type=int)
    parser.add_argument("--omit-object-vectors", action="store_true")
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
        include_object_vectors=not args.omit_object_vectors,
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
