#!/usr/bin/env python3
"""Deterministic, blinded human-review packet construction for Round 6.

The packet is deliberately downstream of candidate generation and model
evaluation.  It contains public identifiers and governed public titles only,
never held identifiers, model scores, inferred relations, or fabricated human
judgments.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any


SCHEMA_VERSION = "trace-exploration-human-review-packet/v1"
IMPLEMENTATION_VERSION = "trace-exploration-human-review-packet-2026-08-24"
PUBLIC_ID_PATTERN = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
TARGET_ANCHOR_COUNT = 72
DEFAULT_CANDIDATES_PER_MODEL = 4


class HumanReviewPacketError(ValueError):
    """Raised when a packet input violates its public/review boundary."""


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _identifier(value: Any) -> str:
    if isinstance(value, Mapping):
        return str(value.get("id", "")).strip()
    return str(value if value is not None else "").strip()


def _ids(record: Mapping[str, Any], field: str) -> tuple[str, ...]:
    value = record.get(field, ())
    if isinstance(value, Mapping) or isinstance(value, str):
        values: Sequence[Any] = (value,)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        values = value
    else:
        raise HumanReviewPacketError(f"{field} must be an array or public token")
    result = tuple(sorted({_identifier(item) for item in values if _identifier(item)}))
    return result


def _safe_title(value: Any) -> str:
    title = unicodedata.normalize("NFC", str(value if value is not None else "").strip())
    if not title:
        raise HumanReviewPacketError("every review object needs a governed public title")
    # Two governed titles contain C1 source controls.  Preserve the public text
    # semantics while making the tabular review artifact safe and renderable.
    return "".join("\ufffd" if unicodedata.category(char) == "Cc" else char for char in title)


def _record_id(record: Mapping[str, Any]) -> str:
    object_id = str(record.get("objectId", "")).strip()
    if not PUBLIC_ID_PATTERN.fullmatch(object_id):
        raise HumanReviewPacketError("review cohort contains a non-public object ID")
    return object_id


def _support_maps(records: Sequence[Mapping[str, Any]]) -> dict[str, Counter[str]]:
    maps = {field: Counter() for field in ("medium", "theme", "geography", "decade", "source", "curated_container")}
    for record in records:
        for field, counter in maps.items():
            counter.update(_ids(record, field))
    return maps


def _pathological_selections(rows: Sequence[Mapping[str, Any]]) -> list[tuple[str, str]]:
    selections: list[tuple[str, str]] = []
    for row in rows:
        case_id = str(row.get("case_type", row.get("sample_id", ""))).strip()
        public_ids = str(row.get("public_object_ids", "")).strip().split(";")
        if not case_id or not public_ids:
            raise HumanReviewPacketError("pathological rows require a case and public IDs")
        for object_id in public_ids:
            if not PUBLIC_ID_PATTERN.fullmatch(object_id):
                raise HumanReviewPacketError("pathological review anchor is not public")
            selections.append((object_id, f"PATHOLOGICAL:{case_id}"))
    return selections


def select_human_review_anchors(
    records: Sequence[Mapping[str, Any]],
    pathological_rows: Sequence[Mapping[str, Any]],
    *,
    target_count: int = TARGET_ANCHOR_COUNT,
) -> dict[str, Any]:
    """Select stable public anchors without randomness or titles as criteria."""

    if target_count < 60 or target_count > 80:
        raise HumanReviewPacketError("human-review target must stay within 60–80 anchors")
    ordered = sorted(records, key=_record_id)
    if len({_record_id(record) for record in ordered}) != len(ordered):
        raise HumanReviewPacketError("review cohort contains duplicate object IDs")
    by_id = {_record_id(record): record for record in ordered}
    support = _support_maps(ordered)

    reasons: dict[str, set[str]] = defaultdict(set)
    selected: list[str] = []

    def add(object_id: str, reason: str) -> None:
        if object_id not in by_id:
            raise HumanReviewPacketError("pathological anchor is outside the public cohort")
        reasons[object_id].add(reason)
        if object_id not in selected and len(selected) < target_count:
            selected.append(object_id)

    for object_id, reason in _pathological_selections(pathological_rows):
        add(object_id, reason)

    def field_extreme(field: str, rare: bool) -> list[tuple[str, str]]:
        rows: list[tuple[int, str, str]] = []
        for record in ordered:
            object_id = _record_id(record)
            values = _ids(record, field)
            if not values:
                continue
            frequency = min(support[field][value] for value in values) if rare else max(
                support[field][value] for value in values
            )
            rows.append((frequency, object_id, values[0]))
        rows.sort(key=lambda row: (row[0], row[1]) if rare else (-row[0], row[1]))
        label = "RARE" if rare else "COMMON"
        return [(object_id, f"{label}_{field.upper()}:{value}") for _, object_id, value in rows]

    strata: list[list[tuple[str, str]]] = []
    for field in ("medium", "theme", "geography", "decade", "source", "curated_container"):
        strata.append(field_extreme(field, True))
        strata.append(field_extreme(field, False))

    def matches(predicate: Any, reason: str) -> list[tuple[str, str]]:
        return [(_record_id(record), reason) for record in ordered if predicate(record)]

    strata.extend(
        [
            matches(lambda row: bool(_ids(row, "movement_context")), "MOVEMENT_CONTEXT"),
            matches(lambda row: len(_ids(row, "geography")) > 1, "MULTI_REGION"),
            matches(
                lambda row: "AGGREGATE_WITHOUT_POINT" in _ids(row, "geography_mapping_state")
                or "AGGREGATE_WITHOUT_POINT" in tuple(map(str, row.get("geographyMappingStates", ()))),
                "AGGREGATE_ONLY_GEOGRAPHY",
            ),
            matches(
                lambda row: "DISPLAY_UNMAPPED" in _ids(row, "geography_mapping_state")
                or "DISPLAY_UNMAPPED" in tuple(map(str, row.get("geographyMappingStates", ()))),
                "UNMAPPED_GEOGRAPHY",
            ),
            matches(lambda row: str(row.get("temporalPrecision", "")).casefold() == "approximate", "APPROXIMATE_TIME"),
            matches(lambda row: str(row.get("temporalPrecision", "")).casefold() == "range", "RANGE_TIME"),
            matches(
                lambda row: str(row.get("creatorLabel", "")).casefold() == "unknown",
                "UNKNOWN_CREATOR_SOURCE_VALUE",
            ),
            matches(
                lambda row: str(row.get("creatorLabel", "")).casefold().startswith("unknown;"),
                "QUALIFIED_UNKNOWN_CREATOR",
            ),
        ]
    )

    # Round-robin across strata prevents a large category from consuming the
    # packet.  Each stratum cursor advances deterministically past duplicates.
    cursors = [0] * len(strata)
    while len(selected) < target_count:
        progressed = False
        for index, rows in enumerate(strata):
            while cursors[index] < len(rows):
                object_id, reason = rows[cursors[index]]
                cursors[index] += 1
                reasons[object_id].add(reason)
                if object_id not in selected:
                    selected.append(object_id)
                    progressed = True
                    break
            if len(selected) >= target_count:
                break
        if not progressed:
            for record in ordered:
                object_id = _record_id(record)
                if object_id not in selected:
                    selected.append(object_id)
                    reasons[object_id].add("LEXICAL_PUBLIC_COHORT_FILL")
                    progressed = True
                    break
        if not progressed:
            raise HumanReviewPacketError("public cohort cannot satisfy the review anchor target")

    anchors = [
        {
            "anchorId": object_id,
            "selectionStrata": sorted(reasons[object_id]),
            "deterministic": True,
            "publicSafe": True,
        }
        for object_id in selected
    ]
    result = {
        "schemaVersion": SCHEMA_VERSION,
        "implementationVersion": IMPLEMENTATION_VERSION,
        "anchorCount": len(anchors),
        "pathologicalCaseCount": len(pathological_rows),
        "anchors": anchors,
        "selectionSha256": _hash(anchors),
        "randomnessAffectsSelection": False,
    }
    validate_anchor_selection(result, public_ids=set(by_id))
    return result


def validate_anchor_selection(result: Mapping[str, Any], *, public_ids: set[str]) -> None:
    anchors = result.get("anchors")
    if not isinstance(anchors, list) or not 60 <= len(anchors) <= 80:
        raise HumanReviewPacketError("review selection must contain 60–80 anchors")
    identifiers = [row.get("anchorId") for row in anchors]
    if len(identifiers) != len(set(identifiers)) or any(value not in public_ids for value in identifiers):
        raise HumanReviewPacketError("review anchors must be unique public objects")
    if result.get("randomnessAffectsSelection") is not False:
        raise HumanReviewPacketError("randomness cannot affect human-review selection")


def _serialize_contributions(values: Any) -> str:
    if values is None:
        return ""
    if isinstance(values, str):
        return values
    if not isinstance(values, Sequence):
        raise HumanReviewPacketError("explanation contributions must be an array")
    normalized: list[str] = []
    for value in values:
        if isinstance(value, Mapping):
            family = str(value.get("family", value.get("kind", "signal"))).strip()
            label = str(value.get("label", value.get("value", value.get("signalId", "")))).strip()
            normalized.append(f"{family}:{label}" if label else family)
        else:
            normalized.append(str(value).strip())
    return "; ".join(sorted({value for value in normalized if value}))


def build_blinded_review_packet(
    anchor_selection: Mapping[str, Any],
    *,
    shortlist_model_ids: Sequence[str],
    rankings_by_model: Mapping[str, Mapping[str, Sequence[Mapping[str, Any]]]],
    titles_by_id: Mapping[str, str],
    source_by_id: Mapping[str, str],
    candidates_per_model: int = DEFAULT_CANDIDATES_PER_MODEL,
) -> dict[str, Any]:
    """Build review rows with blank response fields and hidden model identity."""

    if not 1 <= len(shortlist_model_ids) <= 3:
        raise HumanReviewPacketError("the review packet requires one to three shortlisted models")
    if candidates_per_model < 3 or candidates_per_model > 5:
        raise HumanReviewPacketError("review packets allow three to five candidates per model")
    model_ids = tuple(shortlist_model_ids)
    if len(set(model_ids)) != len(model_ids) or any(model not in rankings_by_model for model in model_ids):
        raise HumanReviewPacketError("shortlist model IDs must be unique and have rankings")
    blind_slots = {model_id: f"PROFILE-{index + 1}" for index, model_id in enumerate(sorted(model_ids))}
    if set(source_by_id) != set(titles_by_id):
        raise HumanReviewPacketError("source composition must cover exactly the public title cohort")
    safe_sources = {
        object_id: _safe_title(source_name)
        for object_id, source_name in source_by_id.items()
    }
    rows: list[dict[str, Any]] = []
    for anchor_number, anchor in enumerate(anchor_selection["anchors"], start=1):
        anchor_id = anchor["anchorId"]
        if anchor_id not in titles_by_id:
            raise HumanReviewPacketError("an anchor title is absent")
        for model_id in sorted(model_ids):
            rankings = rankings_by_model[model_id].get(anchor_id)
            if not isinstance(rankings, Sequence) or len(rankings) < candidates_per_model:
                raise HumanReviewPacketError("every anchor/model needs the bounded candidate count")
            for candidate_number, result in enumerate(rankings[:candidates_per_model], start=1):
                candidate_id = str(result.get("candidateId", "")).strip()
                if candidate_id == anchor_id or not PUBLIC_ID_PATTERN.fullmatch(candidate_id):
                    raise HumanReviewPacketError("review candidate is invalid or self-selected")
                if candidate_id not in titles_by_id:
                    raise HumanReviewPacketError("a candidate title is absent")
                comparability = result.get("comparability", {})
                ratio = comparability.get("ratio") if isinstance(comparability, Mapping) else None
                if not isinstance(ratio, (int, float)) or isinstance(ratio, bool) or not 0 <= float(ratio) <= 1:
                    raise HumanReviewPacketError("every review candidate needs bounded comparability")
                retrieval_reasons = _serialize_contributions(result.get("retrievalReasons"))
                affinity_contributions = _serialize_contributions(
                    result.get("affinityContributions", result.get("contributions"))
                )
                if not retrieval_reasons or not affinity_contributions:
                    raise HumanReviewPacketError(
                        "every review candidate needs retrieval and independent-affinity explanation paths"
                    )
                anchor_source = safe_sources[anchor_id]
                candidate_source = safe_sources[candidate_id]
                rows.append(
                    {
                        "packetRowId": f"HR-{anchor_number:03d}-{blind_slots[model_id]}-{candidate_number}",
                        "anchorPublicId": anchor_id,
                        "anchorTitle": _safe_title(titles_by_id[anchor_id]),
                        "anchorSelectionStrata": ";".join(anchor["selectionStrata"]),
                        "blindProfileSlot": blind_slots[model_id],
                        "candidateOrdinal": candidate_number,
                        "candidatePublicId": candidate_id,
                        "candidateTitle": _safe_title(titles_by_id[candidate_id]),
                        "retrievalReasons": retrieval_reasons,
                        "sharedIndependentSignals": affinity_contributions,
                        "distinctiveSignals": _serialize_contributions(result.get("distinctiveFeatures")),
                        "unavailableFamilies": ";".join(sorted(map(str, result.get("unavailableFamilies", ())))),
                        "comparabilityRatio": float(ratio),
                        "anchorSourceName": anchor_source,
                        "candidateSourceName": candidate_source,
                        "sourceComposition": (
                            "SAME_GOVERNED_SOURCE_NAME"
                            if anchor_source == candidate_source
                            else "CROSS_GOVERNED_SOURCE_NAME"
                        ),
                        "sourceBiasNotes": _serialize_contributions(result.get("sourceBiasNotes")),
                        "interactionEvidence": _serialize_contributions(
                            result.get("interactionEvidence", result.get("interactions"))
                        ),
                        "usefulForFurtherExploration": "",
                        "explanationIntelligible": "",
                        "merelyBroadCategory": "",
                        "newDefensibleResearchDirection": "",
                        "accidentalRelationSuggestion": "",
                        "reviewerNotes": "",
                        "humanReviewCompleted": False,
                        "historicalRelation": False,
                        "semanticRelation": False,
                        "probability": False,
                    }
                )

    if any(row["humanReviewCompleted"] for row in rows):
        raise HumanReviewPacketError("human judgments must remain blank in the generated packet")
    public_ids = set(titles_by_id)
    for row in rows:
        if row["anchorPublicId"] not in public_ids or row["candidatePublicId"] not in public_ids:
            raise HumanReviewPacketError("packet contains a non-public identifier")
        if not row["retrievalReasons"] or not row["sharedIndependentSignals"]:
            raise HumanReviewPacketError("packet contains an unexplained candidate")
        if row["sourceComposition"] not in {
            "SAME_GOVERNED_SOURCE_NAME",
            "CROSS_GOVERNED_SOURCE_NAME",
        }:
            raise HumanReviewPacketError("packet source composition is invalid")
    result = {
        "schemaVersion": SCHEMA_VERSION,
        "implementationVersion": IMPLEMENTATION_VERSION,
        "anchorCount": len(anchor_selection["anchors"]),
        "shortlistModelCount": len(model_ids),
        "candidateRowsPerAnchorModel": candidates_per_model,
        "packetRowCount": len(rows),
        "rows": rows,
        "blindModelMap": blind_slots,
        "humanReviewPacketReady": True,
        "humanReviewCompleted": False,
        "scoresIncluded": False,
        "judgmentsFabricated": False,
        "packetSha256": _hash(rows),
    }
    return result


def self_test() -> dict[str, Any]:
    token = lambda value: {"id": value, "label": value}
    records = []
    for index in range(80):
        records.append(
            {
                "objectId": f"SURF-TEST-{index:03d}",
                "medium": [token(f"M{index % 3}")],
                "theme": [token(f"T{index % 4}")],
                "movement_context": [token("MOV")] if index % 7 == 0 else [],
                "decade": [token(f"D{index % 5}")],
                "geography": [token(f"G{index % 6}")],
                "geography_mapping_state": [token("MAPPED")],
                "source": token(f"S{index % 4}"),
                "object_type": token("POSTER"),
                "creator": token("CREATOR"),
                "creatorLabel": "Creator",
                "curated_container": [token(f"C{index % 8}")],
                "temporalPrecision": "year",
            }
        )
    pathologies = [
        {
            "sample_id": "CASE-1",
            "case_type": "CASE-1",
            "public_object_ids": "SURF-TEST-000",
        }
    ]
    first = select_human_review_anchors(records, pathologies, target_count=72)
    second = select_human_review_anchors(list(reversed(records)), pathologies, target_count=72)
    if first != second:
        raise AssertionError("anchor selection is not order invariant")
    titles = {record["objectId"]: f"Public title {index}" for index, record in enumerate(records)}
    sources = {record["objectId"]: f"Source {index % 4}" for index, record in enumerate(records)}
    object_ids = sorted(titles)
    rankings = {"M2": {}}
    for anchor in first["anchors"]:
        anchor_id = anchor["anchorId"]
        candidates = [value for value in object_ids if value != anchor_id][:3]
        rankings["M2"][anchor_id] = [
            {
                "candidateId": candidate_id,
                "retrievalReasons": ["context:approved posting"],
                "affinityContributions": ["context:governed match"],
                "distinctiveFeatures": [],
                "unavailableFamilies": [],
                "comparability": {
                    "observedFamilyCount": 4,
                    "eligibleFamilyCount": 4,
                    "ratio": 1.0,
                },
                "sourceBiasNotes": ["source:reported only"],
                "interactionEvidence": [],
            }
            for candidate_id in candidates
        ]
    packet = build_blinded_review_packet(
        first,
        shortlist_model_ids=("M2",),
        rankings_by_model=rankings,
        titles_by_id=titles,
        source_by_id=sources,
        candidates_per_model=3,
    )
    if not packet["humanReviewPacketReady"] or packet["humanReviewCompleted"]:
        raise AssertionError("human-review readiness/completion boundary changed")
    return {
        "status": "PASS",
        "anchorCount": first["anchorCount"],
        "selectionSha256": first["selectionSha256"],
        "packetRowCount": packet["packetRowCount"],
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), ensure_ascii=False, sort_keys=True))
