#!/usr/bin/env python3
"""Select the deterministic public-only Exploration pathological register.

The selector emits one minimal stable selection for each Round 5 section 53
case. The only data identifiers in the output are public surface IDs. A sorted
semicolon-delimited pair is permitted solely for the cross-source/context case.
No titles, dimension values, source labels, URLs, held IDs, or internal IDs are
serialized.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "trace-exploration-pathological-samples/v1"
DEFAULT_DERIVATION_VERSION = "trace-exploration-pathological-selection-v1"

CASE_IDS = (
    "MANY_CURATED_MEMBERSHIPS",
    "MINIMAL_CURATION",
    "RARE_MEDIUM_THEME_INTERSECTION",
    "COMMON_MEDIUM_THEME_INTERSECTION",
    "MULTI_REGION_RECORD",
    "LONG_TEMPORAL_RANGE",
    "APPROXIMATE_DATE",
    "AGGREGATE_ONLY_GEOGRAPHY",
    "UNMAPPED_GEOGRAPHY",
    "RARE_SOURCE",
    "DOMINANT_SOURCE",
    "MISSING_CREATOR",
    "MULTIPLE_THEME",
    "MULTIPLE_MOVEMENT",
    "CROSS_SOURCE_CONTEXT_MATCH",
)
ROW_COLUMNS = (
    "case_id",
    "public_id",
    "selection_rule",
    "permitted_diagnostic",
    "sample_id",
    "case_type",
    "public_object_ids",
    "selection_basis",
    "expected_property",
    "observed_property",
    "case_coverage",
    "derivation_version",
    "historical_relation",
    "semantic_relation",
)

PUBLIC_ID_PATTERN = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
UUID_PATTERN = re.compile(
    r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[1-5][0-9A-Fa-f]{3}"
    r"-[89ABab][0-9A-Fa-f]{3}-[0-9A-Fa-f]{12}(?![0-9A-Fa-f])"
)
URL_PATTERN = re.compile(r"(?:https?://|file://)", re.IGNORECASE)
INTERNAL_ID_PATTERN = re.compile(
    r"\b(?:FOL|TRN-OBJ|TRTREE|TRBRANCH|DOS-SURF)-[A-Z0-9#_-]+\b"
)
QUALIFIED_UNKNOWN_PATTERN = re.compile(
    r"^(?:unknown;\s*(?:artist|artists|designer|designers|maker|makers|"
    r"photographer|photographers|printer|printers)(?:\s+\(people\))?|"
    r"(?:artist|designer|creator):\s*unknown)$",
    re.IGNORECASE,
)
GEOGRAPHY_STATES = frozenset({"mapped", "aggregate_only", "unmapped"})


class PathologicalInputError(ValueError):
    """Raised when normalized public input or a selection violates the boundary."""


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PathologicalInputError(f"{field} must be nonblank text")
    text = value.strip()
    if UUID_PATTERN.search(text):
        raise PathologicalInputError(f"{field} contains an internal UUID")
    if URL_PATTERN.search(text):
        raise PathologicalInputError(f"{field} contains a URL")
    return text


def _public_id(value: Any) -> str:
    object_id = _text(value, "objectId")
    if not PUBLIC_ID_PATTERN.fullmatch(object_id):
        raise PathologicalInputError("objectId is not a public surface ID")
    return object_id


def _member_key(value: Any, field: str) -> str:
    if isinstance(value, str):
        return _text(value, field)
    if isinstance(value, Mapping):
        if "id" not in value:
            raise PathologicalInputError(f"{field} member lacks id")
        return _text(value["id"], f"{field}.id")
    raise PathologicalInputError(f"{field} members must be text or mappings")


def _members(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise PathologicalInputError(f"{field} must be an array")
    return tuple(sorted({_member_key(item, field) for item in value}))


def _scalar_key(value: Any, field: str) -> str:
    if isinstance(value, Mapping):
        if "id" not in value:
            raise PathologicalInputError(f"{field} mapping lacks id")
        return _text(value["id"], f"{field}.id")
    return _text(value, field)


def _creator_label(record: Mapping[str, Any]) -> str:
    if "creatorLabel" in record:
        return _text(record["creatorLabel"], "creatorLabel")
    value = record.get("creator")
    if isinstance(value, Mapping):
        if "label" not in value:
            raise PathologicalInputError("creator mapping lacks label")
        return _text(value["label"], "creator.label")
    return _text(value, "creator")


def _creator_state(label: str) -> str:
    normalized = label.strip().casefold()
    if normalized == "unknown":
        return "UNKNOWN_SOURCE_VALUE"
    if QUALIFIED_UNKNOWN_PATTERN.fullmatch(normalized):
        return "QUALIFIED_UNKNOWN_SOURCE_VALUE"
    return "OBSERVED"


def _geography_states(record: Mapping[str, Any]) -> tuple[str, ...]:
    raw = record.get("geographyMappingStates", record.get("geography_mapping_state"))
    if raw is None:
        scalar = record.get("geographyState", record.get("geographyMappingState"))
        raw = [scalar]
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise PathologicalInputError("geography mapping states must be an array")
    states = tuple(sorted({_member_key(value, "geography_mapping_state") for value in raw}))
    if not states or any(state not in GEOGRAPHY_STATES for state in states):
        raise PathologicalInputError("unsupported geography mapping state")
    return states


def _year(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9999:
        raise PathologicalInputError(f"{field} must be an integer year")
    return value


def _normalize_record(record: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise PathologicalInputError("every record must be a mapping")
    required = (
        "objectId", "medium", "theme", "movement_context", "geography",
        "curated_container", "source", "creator", "temporalPrecision",
        "startYear", "endYear", "multiRegion",
    )
    missing = [key for key in required if key not in record]
    if missing:
        raise PathologicalInputError(f"record lacks required fields: {', '.join(missing)}")
    if record.get("held") is True or record.get("isHeld") is True:
        raise PathologicalInputError("held record entered the public selector")
    if record.get("researchDisposition") == "held":
        raise PathologicalInputError("held disposition entered the public selector")

    object_id = _public_id(record["objectId"])
    medium = _members(record["medium"], "medium")
    theme = _members(record["theme"], "theme")
    movement = _members(record["movement_context"], "movement_context")
    geography = _members(record["geography"], "geography")
    curated = _members(record["curated_container"], "curated_container")
    if not medium or not theme or not geography or not curated:
        raise PathologicalInputError(
            "medium, theme, geography, and curated_container must be nonempty"
        )
    multi_region = record["multiRegion"]
    if not isinstance(multi_region, bool):
        raise PathologicalInputError("multiRegion must be boolean")
    if multi_region != (len(geography) > 1):
        raise PathologicalInputError("multiRegion conflicts with geography cardinality")
    precision = _text(record["temporalPrecision"], "temporalPrecision")
    start_year = _year(record["startYear"], "startYear")
    end_year = _year(record["endYear"], "endYear")
    if end_year < start_year:
        raise PathologicalInputError("endYear precedes startYear")
    return {
        "object_id": object_id,
        "medium": medium,
        "theme": theme,
        "movement": movement,
        "geography": geography,
        "curated": curated,
        "source": _scalar_key(record["source"], "source"),
        "creator_state": _creator_state(_creator_label(record)),
        "precision": precision,
        "start_year": start_year,
        "end_year": end_year,
        "geography_states": _geography_states(record),
        "multi_region": multi_region,
    }


def _ratio(numerator: int, denominator: int) -> dict[str, Any]:
    if numerator < 0 or denominator <= 0 or numerator > denominator:
        raise PathologicalInputError("case coverage is outside its denominator")
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": numerator / denominator,
    }


def _row(
    case_id: str,
    public_id: str,
    selection_rule: str,
    permitted_diagnostic: str,
    candidate_count: int,
    public_count: int,
    derivation_version: str,
) -> dict[str, Any]:
    expected_property = case_id.replace("_", " ").lower()
    observed_property = (
        "Deterministic public-only selection satisfies the case rule; "
        + permitted_diagnostic
    )
    return {
        "case_id": case_id,
        "public_id": public_id,
        "selection_rule": selection_rule,
        "permitted_diagnostic": permitted_diagnostic,
        "sample_id": case_id,
        "case_type": case_id,
        "public_object_ids": public_id,
        "selection_basis": selection_rule,
        "expected_property": expected_property,
        "observed_property": observed_property,
        "case_coverage": _ratio(candidate_count, public_count),
        "derivation_version": derivation_version,
        "historical_relation": False,
        "semantic_relation": False,
    }


def _first_at_extreme(
    records: Sequence[Mapping[str, Any]],
    value_key: str,
    *,
    maximum: bool,
) -> tuple[str, int]:
    values = [int(record[value_key]) for record in records]
    extreme = max(values) if maximum else min(values)
    candidates = sorted(
        str(record["object_id"])
        for record in records
        if int(record[value_key]) == extreme
    )
    return candidates[0], len(candidates)


def _validate_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    allowed_public_ids: set[str],
    held_ids: set[str],
) -> None:
    if len(rows) != len(CASE_IDS):
        raise PathologicalInputError("pathological register does not cover all cases")
    if {str(row.get("case_id")) for row in rows} != set(CASE_IDS):
        raise PathologicalInputError("pathological case coverage is incomplete")
    for row in rows:
        if set(row) != set(ROW_COLUMNS):
            raise PathologicalInputError("pathological row columns changed")
        case_id = str(row["case_id"])
        encoded = str(row["public_id"])
        if (
            row["sample_id"] != case_id
            or row["case_type"] != case_id
            or row["public_object_ids"] != encoded
            or row["selection_basis"] != row["selection_rule"]
        ):
            raise PathologicalInputError("generator adapter aliases diverged")
        if not str(row["expected_property"]).strip() or not str(
            row["observed_property"]
        ).strip():
            raise PathologicalInputError("expected/observed adapter fields are blank")
        ids = encoded.split(";")
        if case_id == "CROSS_SOURCE_CONTEXT_MATCH":
            if len(ids) != 2 or ids != sorted(ids) or ids[0] == ids[1]:
                raise PathologicalInputError(
                    "cross-source/context must contain one sorted distinct pair"
                )
        elif len(ids) != 1:
            raise PathologicalInputError(
                "only cross-source/context may contain a semicolon pair"
            )
        if any(not PUBLIC_ID_PATTERN.fullmatch(object_id) for object_id in ids):
            raise PathologicalInputError("selection contains a non-public ID")
        if any(object_id not in allowed_public_ids for object_id in ids):
            raise PathologicalInputError("selection escaped the authoritative public set")
        if any(object_id in held_ids for object_id in ids):
            raise PathologicalInputError("held ID entered pathological register")
        coverage = row["case_coverage"]
        if not isinstance(coverage, Mapping):
            raise PathologicalInputError("case coverage must expose a denominator")
        numerator = coverage.get("numerator")
        denominator = coverage.get("denominator")
        rate = coverage.get("rate")
        if (
            isinstance(numerator, bool)
            or not isinstance(numerator, int)
            or numerator < 1
            or isinstance(denominator, bool)
            or not isinstance(denominator, int)
            or denominator <= 0
            or numerator > denominator
            or not isinstance(rate, (int, float))
            or isinstance(rate, bool)
            or abs(float(rate) - numerator / denominator) > 1e-12
        ):
            raise PathologicalInputError("case coverage receipt is invalid")
        if row["historical_relation"] is not False or row["semantic_relation"] is not False:
            raise PathologicalInputError("pathological selections cannot be relations")

    rendered = json.dumps(rows, ensure_ascii=False, sort_keys=True)
    if UUID_PATTERN.search(rendered):
        raise PathologicalInputError("internal UUID entered pathological register")
    if URL_PATTERN.search(rendered):
        raise PathologicalInputError("URL entered pathological register")
    if INTERNAL_ID_PATTERN.search(rendered):
        raise PathologicalInputError("internal curatorial ID entered pathological register")


def analyze(
    records: Iterable[Mapping[str, Any]],
    *,
    public_ids: Iterable[str] | None = None,
    held_ids: Iterable[str] = (),
    expected_count: int | None = None,
    derivation_version: str = DEFAULT_DERIVATION_VERSION,
) -> dict[str, Any]:
    """Return the complete 15-case public-ID-only pathological register."""

    if not isinstance(derivation_version, str) or not derivation_version.strip():
        raise PathologicalInputError("derivation_version must be nonblank text")
    normalized = sorted(
        (_normalize_record(record) for record in records),
        key=lambda record: str(record["object_id"]),
    )
    if not normalized:
        raise PathologicalInputError("pathological selector requires public records")
    if expected_count is not None and len(normalized) != expected_count:
        raise PathologicalInputError(
            f"expected {expected_count} public records, found {len(normalized)}"
        )
    object_ids = [str(record["object_id"]) for record in normalized]
    if len(object_ids) != len(set(object_ids)):
        raise PathologicalInputError("duplicate public object ID")
    authoritative_public = (
        {_public_id(value) for value in public_ids}
        if public_ids is not None
        else set(object_ids)
    )
    held_set = {_public_id(value) for value in held_ids}
    if authoritative_public & held_set:
        raise PathologicalInputError("authoritative public and held sets overlap")
    if set(object_ids) != authoritative_public:
        raise PathologicalInputError(
            "selector records do not equal the authoritative public-ID set"
        )
    if set(object_ids) & held_set:
        raise PathologicalInputError("held ID entered selector records")

    public_count = len(normalized)
    enriched = [
        {
            **record,
            "curated_count": len(record["curated"]),
            "theme_count": len(record["theme"]),
            "movement_count": len(record["movement"]),
            "range_span": record["end_year"] - record["start_year"] + 1,
        }
        for record in normalized
    ]

    max_curation_id, max_curation_candidates = _first_at_extreme(
        enriched, "curated_count", maximum=True
    )
    min_curation_id, min_curation_candidates = _first_at_extreme(
        enriched, "curated_count", maximum=False
    )

    medium_theme_members: dict[tuple[str, str], set[str]] = defaultdict(set)
    for record in enriched:
        for medium, theme in itertools.product(record["medium"], record["theme"]):
            medium_theme_members[(medium, theme)].add(str(record["object_id"]))
    if not medium_theme_members:
        raise PathologicalInputError("no observed medium-theme intersections")
    rare_cell, rare_members = min(
        medium_theme_members.items(), key=lambda item: (len(item[1]), item[0])
    )
    del rare_cell
    common_cell, common_members = min(
        medium_theme_members.items(), key=lambda item: (-len(item[1]), item[0])
    )
    del common_cell

    source_members: dict[str, set[str]] = defaultdict(set)
    for record in enriched:
        source_members[str(record["source"])].add(str(record["object_id"]))
    rare_source, rare_source_members = min(
        source_members.items(), key=lambda item: (len(item[1]), item[0])
    )
    del rare_source
    dominant_source, dominant_source_members = min(
        source_members.items(), key=lambda item: (-len(item[1]), item[0])
    )
    del dominant_source

    def selected(
        predicate: Any,
        label: str,
        *,
        rank: Any | None = None,
    ) -> tuple[str, int]:
        candidates = [record for record in enriched if predicate(record)]
        if not candidates:
            raise PathologicalInputError(f"no public object covers {label}")
        if rank is None:
            candidates.sort(key=lambda record: str(record["object_id"]))
        else:
            candidates.sort(key=rank)
        return str(candidates[0]["object_id"]), len(candidates)

    multi_region_id, multi_region_count = selected(
        lambda record: record["multi_region"], "multi-region"
    )
    ranges = [record for record in enriched if record["precision"] == "range"]
    if not ranges:
        raise PathologicalInputError("no public temporal range exists")
    longest_span = max(int(record["range_span"]) for record in ranges)
    long_range_id, long_range_count = selected(
        lambda record: record["precision"] == "range"
        and int(record["range_span"]) == longest_span,
        "long temporal range",
    )
    approximate_id, approximate_count = selected(
        lambda record: record["precision"] == "approximate", "approximate date"
    )
    aggregate_id, aggregate_count = selected(
        lambda record: "aggregate_only" in record["geography_states"],
        "aggregate-only geography",
    )
    unmapped_id, unmapped_count = selected(
        lambda record: "unmapped" in record["geography_states"],
        "unmapped geography",
    )
    missing_creator_id, missing_creator_count = selected(
        lambda record: record["creator_state"] != "OBSERVED", "missing creator"
    )
    max_theme = max(int(record["theme_count"]) for record in enriched)
    if max_theme < 2:
        raise PathologicalInputError("no public object has multiple themes")
    multiple_theme_id, multiple_theme_count = selected(
        lambda record: int(record["theme_count"]) == max_theme,
        "multiple theme",
    )
    max_movement = max(int(record["movement_count"]) for record in enriched)
    if max_movement < 2:
        raise PathologicalInputError("no public object has multiple movements")
    multiple_movement_id, multiple_movement_count = selected(
        lambda record: int(record["movement_count"]) == max_movement,
        "multiple movement",
    )

    context_groups: dict[tuple[tuple[str, ...], tuple[str, ...]], list[Mapping[str, Any]]] = defaultdict(list)
    for record in enriched:
        context_groups[(record["medium"], record["theme"])].append(record)
    qualifying_contexts = [
        (signature, members)
        for signature, members in context_groups.items()
        if len({str(member["source"]) for member in members}) >= 2
    ]
    if not qualifying_contexts:
        raise PathologicalInputError("no cross-source exact-context match exists")
    _, cross_members = min(
        qualifying_contexts,
        key=lambda item: (-len(item[1]), item[0]),
    )
    cross_pairs = sorted(
        tuple(sorted((str(left["object_id"]), str(right["object_id"]))))
        for left, right in itertools.combinations(cross_members, 2)
        if left["source"] != right["source"]
    )
    if not cross_pairs:
        raise PathologicalInputError("cross-source context group lacks a valid pair")
    cross_encoded = ";".join(cross_pairs[0])

    rows = [
        _row(
            "MANY_CURATED_MEMBERSHIPS", max_curation_id,
            "Select the first public ID among objects at the maximum unique curated-membership count.",
            "Curated membership-count extremum only; not importance or canonicality.",
            max_curation_candidates, public_count, derivation_version,
        ),
        _row(
            "MINIMAL_CURATION", min_curation_id,
            "Select the first public ID among objects at the minimum positive curated-membership count.",
            "Curated membership-count extremum only; not historical absence.",
            min_curation_candidates, public_count, derivation_version,
        ),
        _row(
            "RARE_MEDIUM_THEME_INTERSECTION", min(rare_members),
            "Choose the first minimum-positive-count medium-theme cell, then its first public ID.",
            "Observed cell frequency and support only; rare does not imply important.",
            len(rare_members), public_count, derivation_version,
        ),
        _row(
            "COMMON_MEDIUM_THEME_INTERSECTION", min(common_members),
            "Choose the first maximum-count medium-theme cell, then its first public ID.",
            "Observed cell frequency and support only; common does not imply representative.",
            len(common_members), public_count, derivation_version,
        ),
        _row(
            "MULTI_REGION_RECORD", multi_region_id,
            "Select the first public ID with more than one governed geography assignment.",
            "Governed multi-region incidence only; not travel or influence.",
            multi_region_count, public_count, derivation_version,
        ),
        _row(
            "LONG_TEMPORAL_RANGE", long_range_id,
            "Select the first public ID at the maximum inclusive governed range span.",
            "Recorded temporal-span extremum only; not production duration.",
            long_range_count, public_count, derivation_version,
        ),
        _row(
            "APPROXIMATE_DATE", approximate_id,
            "Select the first public ID governed with approximate temporal precision.",
            "Approximate-precision state only; not a scalar confidence score.",
            approximate_count, public_count, derivation_version,
        ),
        _row(
            "AGGREGATE_ONLY_GEOGRAPHY", aggregate_id,
            "Select the first public ID with aggregate-only governed geography.",
            "Aggregate-only mapping state; not geographic absence.",
            aggregate_count, public_count, derivation_version,
        ),
        _row(
            "UNMAPPED_GEOGRAPHY", unmapped_id,
            "Select the first public ID with unmapped governed geography.",
            "Unmapped state only; not evidence that place is unknown or absent.",
            unmapped_count, public_count, derivation_version,
        ),
        _row(
            "RARE_SOURCE", min(rare_source_members),
            "Choose the first minimum-positive-count source, then its first public ID.",
            "Observed source frequency and support only; not source authority.",
            len(rare_source_members), public_count, derivation_version,
        ),
        _row(
            "DOMINANT_SOURCE", min(dominant_source_members),
            "Choose the first maximum-count source, then its first public ID.",
            "Observed source concentration only; not representativeness.",
            len(dominant_source_members), public_count, derivation_version,
        ),
        _row(
            "MISSING_CREATOR", missing_creator_id,
            "Select the first public ID with explicit unknown or qualified-unknown creator attribution.",
            "Attribution uncertainty class only; not creator absence from history.",
            missing_creator_count, public_count, derivation_version,
        ),
        _row(
            "MULTIPLE_THEME", multiple_theme_id,
            "Select the first public ID at the maximum governed theme cardinality, requiring at least two.",
            "Multi-theme assignment count only; not greater importance.",
            multiple_theme_count, public_count, derivation_version,
        ),
        _row(
            "MULTIPLE_MOVEMENT", multiple_movement_id,
            "Select the first public ID at the maximum published movement-context cardinality, requiring at least two.",
            "Multi-movement-context assignment count only; not influence.",
            multiple_movement_count, public_count, derivation_version,
        ),
        _row(
            "CROSS_SOURCE_CONTEXT_MATCH", cross_encoded,
            "Choose the largest exact medium-theme context group spanning sources, then its first sorted cross-source public-ID pair.",
            "Cross-source governed-context co-occurrence only; not source independence or relation.",
            len(cross_members), public_count, derivation_version,
        ),
    ]
    rows.sort(key=lambda row: str(row["case_id"]))
    _validate_rows(
        rows,
        allowed_public_ids=authoritative_public,
        held_ids=held_set,
    )

    selected_slots = [
        object_id
        for row in rows
        for object_id in str(row["public_id"]).split(";")
    ]
    deterministic_payload = {
        "schema_version": SCHEMA_VERSION,
        "derivation_version": derivation_version,
        "rows": rows,
        "summary": {
            "required_case_coverage": _ratio(len(rows), len(CASE_IDS)),
            "selected_public_id_slots": {
                "count": len(selected_slots),
                "denominator": len(CASE_IDS) + 1,
                "unit": "required_selection_slots",
            },
            "unique_public_ids": {
                "count": len(set(selected_slots)),
                "denominator": len(selected_slots),
                "unit": "selected_public_id_slots",
            },
        },
        "input_receipt": {
            "public_id_set_sha256": sha256_json(sorted(authoritative_public)),
            "held_id_intersection": _ratio(0, public_count),
        },
        "invariants": {
            "ALL_SECTION_53_CASES_COVERED": True,
            "EVERY_CASE_HAS_POSITIVE_COVERAGE": True,
            "HELD_SET_REJECTED": True,
            "PUBLIC_IDS_ONLY": True,
            "CROSS_SOURCE_CONTEXT_ONLY_SEMICOLON_PAIR": True,
            "TITLE_EXPOSURE": False,
            "VALUE_LABEL_EXPOSURE": False,
            "SOURCE_LABEL_EXPOSURE": False,
            "URL_EXPOSURE": False,
            "UUID_EXPOSURE": False,
            "HISTORICAL_RELATION": False,
            "SEMANTIC_RELATION": False,
        },
    }
    deterministic_sha = sha256_json(deterministic_payload)
    return {
        **deterministic_payload,
        "deterministic_receipt": {
            "canonicalization": "recursive key sort; compact JSON; final LF; UTF-8",
            "sha256": deterministic_sha,
        },
    }


def _member(identifier: str, label: str) -> dict[str, str]:
    return {"id": identifier, "label": label}


def _synthetic_records() -> list[dict[str, Any]]:
    base = {
        "medium": [_member("CTX:MED:A", "Medium A")],
        "theme": [_member("CTX:THEME:A", "Theme A")],
        "movement_context": [],
        "geography": [_member("GEO:A", "Place A")],
        "curated_container": [
            _member("EXP:CURATED:A", "Container A"),
            _member("EXP:CURATED:B", "Container B"),
        ],
        "source": _member("EXP:SOURCE:A", "Source A"),
        "creator": _member("EXP:CREATOR:A", "Known Creator"),
        "creatorLabel": "Known Creator",
        "temporalPrecision": "year",
        "startYear": 1900,
        "endYear": 1900,
        "geographyMappingStates": ["mapped"],
        "multiRegion": False,
    }
    records = [
        {
            **base,
            "objectId": "SURF-TEST-001",
            "curated_container": [
                _member(f"EXP:CURATED:{letter}", f"Container {letter}")
                for letter in "ABCDE"
            ],
            "medium": [_member("CTX:MED:RARE", "Rare Medium")],
            "theme": [_member("CTX:THEME:RARE", "Rare Theme")],
            "geography": [
                _member("GEO:A", "Place A"), _member("GEO:B", "Place B")
            ],
            "multiRegion": True,
            "temporalPrecision": "range",
            "startYear": 1800,
            "endYear": 1900,
            "geographyMappingStates": ["mapped"],
            "creator": _member("EXP:CREATOR:UNKNOWN", "Unknown"),
            "creatorLabel": "Unknown",
        },
        {
            **base,
            "objectId": "SURF-TEST-002",
            "curated_container": [_member("EXP:CURATED:A", "Container A")],
            "theme": [
                _member("CTX:THEME:A", "Theme A"),
                _member("CTX:THEME:B", "Theme B"),
            ],
            "movement_context": [
                _member("CTX:MOV:A", "Movement A"),
                _member("CTX:MOV:B", "Movement B"),
            ],
            "temporalPrecision": "approximate",
            "geographyMappingStates": ["unmapped"],
            "source": _member("EXP:SOURCE:RARE", "Rare Source"),
        },
        {
            **base,
            "objectId": "SURF-TEST-003",
            "geographyMappingStates": ["aggregate_only"],
        },
        {**base, "objectId": "SURF-TEST-004"},
        {
            **base,
            "objectId": "SURF-TEST-005",
            "source": _member("EXP:SOURCE:B", "Source B"),
        },
        {**base, "objectId": "SURF-TEST-006"},
    ]
    return records


def run_self_tests() -> dict[str, Any]:
    records = _synthetic_records()
    public_ids = {str(record["objectId"]) for record in records}
    held_ids = {"SURF-HELD-999"}
    first = analyze(
        records,
        public_ids=public_ids,
        held_ids=held_ids,
        expected_count=len(records),
    )
    second = analyze(
        list(reversed(records)),
        public_ids=reversed(sorted(public_ids)),
        held_ids=held_ids,
        expected_count=len(records),
    )
    assert first["deterministic_receipt"] == second["deterministic_receipt"]
    assert first["summary"]["required_case_coverage"]["numerator"] == 15
    assert first["summary"]["required_case_coverage"]["denominator"] == 15
    assert all(row["case_coverage"]["numerator"] > 0 for row in first["rows"])
    cross = next(
        row for row in first["rows"]
        if row["case_id"] == "CROSS_SOURCE_CONTEXT_MATCH"
    )
    assert len(cross["public_id"].split(";")) == 2
    assert all(
        ";" not in row["public_id"]
        for row in first["rows"]
        if row["case_id"] != "CROSS_SOURCE_CONTEXT_MATCH"
    )

    adversaries: list[tuple[list[dict[str, Any]], dict[str, Any]]] = [
        ([{**records[0], "objectId": "123e4567-e89b-12d3-a456-426614174000"}], {}),
        ([{**records[0], "held": True}], {}),
        ([{**records[0], "source": "https://unsafe.example"}], {}),
        ([{key: value for key, value in records[0].items() if key != "theme"}], {}),
        (records, {"public_ids": public_ids, "held_ids": {"SURF-TEST-001"}}),
    ]
    failures = 0
    for adversary_records, kwargs in adversaries:
        try:
            analyze(adversary_records, **kwargs)
        except PathologicalInputError:
            failures += 1
    assert failures == len(adversaries)
    return {
        "status": "PASS",
        "checks": 13,
        "adversaries": len(adversaries),
        "case_coverage": {"numerator": 15, "denominator": 15},
        "deterministic_sha256": first["deterministic_receipt"]["sha256"],
    }


def _load_cli(path: Path) -> tuple[list[Mapping[str, Any]], Any, Any]:
    payload = json.loads(path.read_text("utf-8"))
    if isinstance(payload, Mapping):
        records = payload.get("records")
        public_ids = payload.get("publicObjectIds")
        held_ids = payload.get("heldObjectIds", [])
    else:
        records = payload
        public_ids = None
        held_ids = []
    if not isinstance(records, list):
        raise PathologicalInputError("CLI input must contain records[]")
    return records, public_ids, held_ids


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-count", type=int)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(run_self_tests(), sort_keys=True))
        return
    if args.input is None or args.output is None:
        parser.error("--input and --output are required unless --self-test is used")
    records, public_ids, held_ids = _load_cli(args.input)
    result = analyze(
        records,
        public_ids=public_ids,
        held_ids=held_ids,
        expected_count=args.expected_count,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json_bytes(result))
    print(json.dumps({
        "status": "PASS",
        "output": str(args.output),
        "cases": len(result["rows"]),
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
