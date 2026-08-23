#!/usr/bin/env python3
"""Rederive and verify Exploration discovery Round 1 aggregate artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import generate_round1 as generator


SCHEMA_VERSION = "trace-exploration-round1-verification/v1"
ALLOWED_SIGNAL_STATUSES = frozenset({
    "HIGH_POTENTIAL",
    "SUPPORTING_SIGNAL",
    "RESEARCH_ONLY",
    "NEEDS_MORE_DATA",
    "DEFER",
    "REJECT",
})
DOCUMENTED_NON_GENERATOR_RAW_RECEIPTS = frozenset({
    "exploration-benchmark-summary.json",
    "exploration-performance-summary.json",
    "exploration-verification-summary.json",
})

INVARIANT_TEXT = {
    "EXP-INV-001": "Every Exploration signal has a named source.",
    "EXP-INV-002": "Every derived signal has a derivation version.",
    "EXP-INV-003": "Every count/rate exposes its denominator.",
    "EXP-INV-004": "No signal is a semantic relation.",
    "EXP-INV-005": "No curatorial co-membership becomes historical relation.",
    "EXP-INV-006": "Missingness is not reduced to null detection.",
    "EXP-INV-007": "Not-applicable and missing remain distinct.",
    "EXP-INV-008": "Movement-context absence is not automatically missingness.",
    "EXP-INV-009": "Held records do not enter public-cohort statistics.",
    "EXP-INV-010": "No internal UUID appears in committed Exploration artifacts.",
    "EXP-INV-011": "Rare does not imply important.",
    "EXP-INV-012": "High overlap does not imply influence.",
    "EXP-INV-013": "Geographic layout distance is not historical distance.",
    "EXP-INV-014": "Source concentration is not truth/quality.",
    "EXP-INV-015": "Same inputs produce deterministic statistics.",
    "EXP-INV-016": "No final similarity score exists in Round 1.",
    "EXP-INV-017": "No final ranking exists in Round 1.",
    "EXP-INV-018": "No final Exploration template registry exists in Round 1.",
}


class VerificationError(RuntimeError):
    """Raised when an Exploration Round 1 verification gate fails."""


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _float(value: str, field: str) -> float:
    try:
        result = float(value)
    except ValueError as error:
        raise VerificationError(f"{field} is not numeric: {value!r}") from error
    if not math.isfinite(result):
        raise VerificationError(f"{field} is not finite")
    return result


def _int(value: str, field: str) -> int:
    number = _float(value, field)
    if not number.is_integer():
        raise VerificationError(f"{field} is not an integer")
    return int(number)


def _close(actual: float, expected: float, field: str) -> None:
    if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-12):
        raise VerificationError(f"{field} differs: {actual} != {expected}")


def parse_tsv(payload: bytes, expected_headers: Sequence[str], filename: str) -> list[dict[str, str]]:
    if b"\r" in payload or b"\x00" in payload:
        raise VerificationError(f"{filename} contains CR or NUL bytes")
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        raise VerificationError(f"{filename} must have exactly one final LF")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise VerificationError(f"{filename} is not UTF-8") from error
    reader = csv.reader(io.StringIO(text), delimiter="\t", strict=True)
    table = list(reader)
    if not table or tuple(table[0]) != tuple(expected_headers):
        raise VerificationError(f"{filename} header differs from its frozen schema")
    width = len(expected_headers)
    if any(len(row) != width for row in table):
        raise VerificationError(f"{filename} is not rectangular")
    return [dict(zip(expected_headers, row, strict=True)) for row in table[1:]]


def _verify_rate(
    row: Mapping[str, str],
    count_field: str,
    denominator_field: str,
    rate_field: str,
    label: str,
) -> None:
    count = _int(row[count_field], f"{label}.{count_field}")
    denominator = _int(row[denominator_field], f"{label}.{denominator_field}")
    rate = _float(row[rate_field], f"{label}.{rate_field}")
    if denominator <= 0 or count < 0:
        raise VerificationError(f"{label} has invalid count/denominator")
    _close(rate, count / denominator, f"{label}.{rate_field}")


def _verify_missingness(rows: Sequence[Mapping[str, str]]) -> None:
    counts = Counter(row["row_kind"] for row in rows)
    if counts != {"TAXONOMY": 10, "FIELD_MATRIX": 9, "COOCCURRENCE": 19}:
        raise VerificationError("06 missingness row groups do not reconcile")
    for index, row in enumerate(rows, start=1):
        kind = row["row_kind"]
        if not row["input_source"] or not row["derivation_version"]:
            raise VerificationError("06 row lacks source or derivation version")
        if kind == "TAXONOMY":
            if not row["taxonomy_class"] or not row["meaning"]:
                raise VerificationError("06 taxonomy row is incomplete")
            continue
        _verify_rate(row, "object_count", "eligible_denominator", "support_rate", f"06[{index}]")
        denominator = _int(row["eligible_denominator"], "06.eligible_denominator")
        for field in ("state_counts_json", "uncertainty_counts_json", "qualifier_counts_json"):
            if not row[field]:
                continue
            values = json.loads(row[field])
            if not isinstance(values, dict):
                raise VerificationError(f"06 {field} is not a JSON object")
            for value in values.values():
                count = int(value)
                if not 0 <= count <= denominator:
                    raise VerificationError(f"06 {field} count escapes denominator")
        if kind == "COOCCURRENCE" and (not row["state_a"] or not row["state_b"]):
            raise VerificationError("06 cooccurrence lacks states")


def _verify_frequency(rows: Sequence[Mapping[str, str]]) -> None:
    if len(rows) != 3_364:
        raise VerificationError("08 frequency row count differs from 3,364")
    for index, row in enumerate(rows, start=1):
        _verify_rate(row, "object_count", "eligible_denominator", "object_support_rate", f"08[{index}]")
        _verify_rate(row, "object_count", "dimension_assignment_denominator", "assignment_share", f"08[{index}]")
        observed = _int(row["observed_object_denominator"], "08.observed_object_denominator")
        if observed <= 0 or not row["input_source"] or not row["derivation_version"]:
            raise VerificationError("08 row lacks denominator, source, or version")


def _verify_pairs(rows: Sequence[Mapping[str, str]]) -> None:
    if len(rows) != 6_146 or len({row["pair_id"] for row in rows}) != 18:
        raise VerificationError("09 pair rows/specs do not reconcile")
    for index, row in enumerate(rows, start=1):
        label = f"09[{index}]"
        _verify_rate(row, "object_count", "eligible_denominator", "support_rate_eligible", label)
        _verify_rate(
            row, "object_count", "joint_observable_denominator",
            "support_rate_joint_observable", label,
        )
        count = _int(row["object_count"], f"{label}.object_count")
        left = _int(row["dimension_a_value_object_count"], f"{label}.left_count")
        right = _int(row["dimension_b_value_object_count"], f"{label}.right_count")
        eligible = _int(row["eligible_denominator"], f"{label}.eligible")
        lift_denominator = _int(row["lift_reference_denominator"], f"{label}.lift_denominator")
        if count <= 0 or left <= 0 or right <= 0 or lift_denominator != eligible:
            raise VerificationError("09 contains a zero cell or invalid lift denominator")
        _close(
            _float(row["conditional_observed_rate_a_given_b"], f"{label}.conditional_a"),
            count / right,
            f"{label}.conditional_a",
        )
        _close(
            _float(row["conditional_observed_rate_b_given_a"], f"{label}.conditional_b"),
            count / left,
            f"{label}.conditional_b",
        )
        _close(
            _float(row["lift_diagnostic"], f"{label}.lift"),
            count * eligible / (left * right),
            f"{label}.lift",
        )
        if row["diagnostic_status"] != "ANALYSIS_DIAGNOSTIC":
            raise VerificationError("09 conditional/lift metrics are not diagnostic")
        if not row["input_source"] or not row["derivation_version"]:
            raise VerificationError("09 row lacks source/version")


def _verify_triples(rows: Sequence[Mapping[str, str]]) -> None:
    if len(rows) != 2_399 or len({row["triple_id"] for row in rows}) != 6:
        raise VerificationError("10 triple rows/specs do not reconcile")
    for index, row in enumerate(rows, start=1):
        label = f"10[{index}]"
        _verify_rate(row, "object_count", "eligible_denominator", "support_rate_eligible", label)
        _verify_rate(
            row, "object_count", "joint_observable_denominator",
            "support_rate_joint_observable", label,
        )
        if _int(row["object_count"], f"{label}.object_count") <= 0:
            raise VerificationError("10 contains a zero Cartesian cell")
        for field in (
            "dimension_a_value_object_count",
            "dimension_b_value_object_count",
            "dimension_c_value_object_count",
        ):
            if _int(row[field], f"{label}.{field}") <= 0:
                raise VerificationError("10 contains an empty marginal")
        if row["diagnostic_status"] != "ANALYSIS_DIAGNOSTIC":
            raise VerificationError("10 metrics are not diagnostic")
        if not row["input_source"] or not row["derivation_version"]:
            raise VerificationError("10 row lacks source/version")


def _verify_rare(rows: Sequence[Mapping[str, str]]) -> None:
    if len(rows) != 4_251:
        raise VerificationError("11 rare register row count differs from 4,251")
    kinds = Counter(row["cell_kind"] for row in rows)
    if kinds != {"PAIR": 2_238, "BOUNDED_TRIPLE": 2_013}:
        raise VerificationError("11 pair/triple rare counts do not reconcile")
    for index, row in enumerate(rows, start=1):
        label = f"11[{index}]"
        _verify_rate(row, "object_count", "eligible_denominator", "support_rate_eligible", label)
        _verify_rate(
            row, "object_count", "joint_observable_denominator",
            "support_rate_joint_observable", label,
        )
        if not 1 <= _int(row["object_count"], f"{label}.count") <= generator.RARE_MAX_COUNT:
            raise VerificationError("11 count escapes frozen rare threshold")
        if row["importance_inference"] != "PROHIBITED":
            raise VerificationError("11 implies importance from rarity")
        if row["spec_id"] == "creator__medium":
            raise VerificationError("11 includes high-cardinality creator cells")


def _verify_registry(rows: Sequence[Mapping[str, str]]) -> None:
    if len(rows) != 64 or len({row["signal_id"] for row in rows}) != 64:
        raise VerificationError("13 signal registry must contain 64 unique IDs")

    def metric_receipt(cell: str, label: str) -> Mapping[str, Any]:
        try:
            value = json.loads(cell)
        except json.JSONDecodeError as error:
            raise VerificationError(f"13 {label} is not canonical JSON") from error
        if not isinstance(value, Mapping):
            raise VerificationError(f"13 {label} is not a metric receipt")
        denominator = value.get("denominator")
        if (
            isinstance(denominator, bool)
            or not isinstance(denominator, int)
            or denominator < 0
        ):
            raise VerificationError(f"13 {label} lacks a nonnegative denominator")
        if "numerator" in value:
            numerator = value.get("numerator")
            rate = value.get("rate")
            if (
                isinstance(numerator, bool)
                or not isinstance(numerator, int)
                or numerator < 0
                or numerator > denominator
                or isinstance(rate, bool)
                or not isinstance(rate, (int, float))
            ):
                raise VerificationError(f"13 {label} has an invalid ratio")
            expected = numerator / denominator if denominator else 0.0
            _close(float(rate), expected, f"13.{label}.rate")
        elif "count" in value:
            count = value.get("count")
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                raise VerificationError(f"13 {label} has an invalid count")
        elif not isinstance(value.get("state"), str) or not value["state"].strip():
            raise VerificationError(f"13 {label} lacks numerator, count, or state")
        return value

    for row in rows:
        if not row["input_source"] or not row["derivation_version"]:
            raise VerificationError("13 signal lacks source or derivation version")
        if not row["numerator_definition"] or not row["denominator_definition"]:
            raise VerificationError("13 signal lacks count/rate definitions")
        if row["historical_relation"] != "false" or row["semantic_relation"] != "false":
            raise VerificationError("13 signal claims a relation")
        if row["status"] not in ALLOWED_SIGNAL_STATUSES:
            raise VerificationError("13 signal has a disallowed status")
        for field in ("deterministic", "explainable", "public_safe"):
            if row[field] not in {"true", "false"}:
                raise VerificationError(f"13 {field} is not boolean")
        for field in ("coverage", "cardinality", "missing_rate"):
            metric_receipt(row[field], f"{row['signal_id']}.{field}")
    level_counts = Counter(row["derivation_level"] for row in rows)
    if level_counts != {
        "LEVEL_A_GOVERNED_DIRECT_FEATURE": 9,
        "LEVEL_B_DETERMINISTIC_DERIVED_STATISTIC": 43,
        "LEVEL_C_COMPOUND_EXPLORATORY_SIGNAL": 12,
    }:
        raise VerificationError(f"13 derivation levels differ: {dict(level_counts)}")
    by_id = {row["signal_id"]: row for row in rows}
    for signal_id in (
        "SIG-SOURCE-NAME",
        "SIG-DESCRIPTIVE-CREATOR",
        "SIG-DESCRIPTIVE-OBJECT-TYPE",
    ):
        row = by_id[signal_id]
        if (
            row["direct_or_derived"] != "DERIVED"
            or row["derivation_level"] != "LEVEL_B_DETERMINISTIC_DERIVED_STATISTIC"
        ):
            raise VerificationError(f"13 public metadata signal is misclassified: {signal_id}")


def _verify_samples(
    rows: Sequence[Mapping[str, str]],
    public_ids: set[str],
    held_ids: set[str],
) -> None:
    if len(rows) != 15 or len({row["sample_id"] for row in rows}) != 15:
        raise VerificationError("15 pathological register must contain 15 unique rows")
    for index, row in enumerate(rows, start=1):
        object_ids = row["public_object_ids"].split(";")
        if object_ids != sorted(object_ids) or not 1 <= len(object_ids) <= 2:
            raise VerificationError("15 public IDs are not a sorted one/two-ID selection")
        if any(
            not generator.PUBLIC_ID_RE.fullmatch(value)
            or value not in public_ids
            or value in held_ids
            for value in object_ids
        ):
            raise VerificationError("15 contains a held or non-authoritative public ID")
        _verify_rate(row, "candidate_count", "eligible_denominator", "support_rate", f"15[{index}]")
        if _int(row["eligible_denominator"], "15.eligible_denominator") != generator.PUBLIC_OBJECT_COUNT:
            raise VerificationError("15 prevalence denominator differs from the public cohort")
        if _int(row["candidate_count"], "15.candidate_count") < 1:
            raise VerificationError("15 case prevalence must be positive")
        if not row["permitted_diagnostic"]:
            raise VerificationError("15 lacks its permitted diagnostic")
        if row["sample_id"] == "CROSS_SOURCE_CONTEXT_MATCH":
            if len(object_ids) != 2:
                raise VerificationError("15 cross-source/context case lacks its public-ID pair")
        elif len(object_ids) != 1:
            raise VerificationError("15 only cross-source/context may use a public-ID pair")
        if row["held_object_count"] != "0":
            raise VerificationError("15 reports a held object")
        if row["historical_relation"] != "false" or row["semantic_relation"] != "false":
            raise VerificationError("15 sample claims a relation")


def _walk_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(_walk_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_keys(item))
    return keys


def _verify_distribution_field(
    value: Any,
    label: str,
    *,
    require_multiple_count: bool = False,
) -> None:
    if not isinstance(value, Mapping):
        raise VerificationError(f"{label} is not a distribution applicability receipt")
    status = value.get("status")
    if status == "NOT_APPLICABLE":
        if not isinstance(value.get("rationale"), str) or not value["rationale"].strip():
            raise VerificationError(f"{label} lacks a not-applicable rationale")
        return
    if status != "APPLICABLE" or not isinstance(value.get("distribution"), Mapping):
        raise VerificationError(f"{label} has an invalid applicability state")
    distribution = value["distribution"]
    for key in ("n", "min", "p50", "p90", "p95", "p99", "max", "mean", "zeroCount"):
        if key not in distribution or not isinstance(distribution[key], (int, float)):
            raise VerificationError(f"{label} lacks numeric {key}")
    if int(distribution["n"]) < 0 or int(distribution["zeroCount"]) < 0:
        raise VerificationError(f"{label} has a negative population")
    if require_multiple_count:
        multiple_count = distribution.get("multipleCount")
        if not isinstance(multiple_count, int):
            raise VerificationError(f"{label} lacks exact integer multipleCount")
        if multiple_count < 0 or multiple_count > int(distribution["n"]):
            raise VerificationError(f"{label} has an invalid multipleCount")
        if float(distribution["max"]) <= 1 and multiple_count != 0:
            raise VerificationError(f"{label} multipleCount contradicts max")
        if float(distribution["min"]) > 1 and multiple_count != int(distribution["n"]):
            raise VerificationError(f"{label} multipleCount contradicts min")


def _verify_structure_registry(value: Mapping[str, Any]) -> None:
    if value.get("rowCount") != 20 or value.get("populationStateCounts") != {
        "EMPTY": 4, "POPULATED": 16,
    }:
        raise VerificationError("20-row structure registry does not reconcile")
    expected_classification_counts = {
        "CANDIDATE": 4,
        "EMPTY": 4,
        "INTERNAL_ONLY": 15,
        "LEGACY_ONLY": 15,
        "POPULATED": 16,
        "PUBLIC_GOVERNED": 4,
        "UNSAFE": 14,
    }
    if value.get("classificationCounts") != expected_classification_counts:
        raise VerificationError("structure classification counts do not reconcile")
    rows = value.get("rows")
    if not isinstance(rows, list) or len(rows) != 20:
        raise VerificationError("structure registry rows are absent")
    by_id = {str(row.get("structureId")): row for row in rows if isinstance(row, Mapping)}
    if len(by_id) != 20:
        raise VerificationError("structure registry IDs are incomplete or duplicated")
    if by_id["governed_trace_projection"].get("classifications") != [
        "EMPTY", "PUBLIC_GOVERNED"
    ]:
        raise VerificationError("governed TRACE projection is not known fail-closed empty")
    if any(
        "UNKNOWN" in row.get("classifications", [])
        for row in rows
        if isinstance(row, Mapping)
    ):
        raise VerificationError("structure registry contains an UNKNOWN classification")
    for structure_id, row_count in (
        ("sqlite_trace_nodes", 97_889),
        ("sqlite_trace_edges", 255_695),
    ):
        row = by_id[structure_id]
        if (
            row.get("structureRowCount") != row_count
            or row.get("containerCount") != 0
            or row.get("membershipCount") != 0
        ):
            raise VerificationError(
                f"SQLite graph row count is misclassified: {structure_id}"
            )
    folder_graph = by_id["folder_related_graph"]
    if (
        folder_graph.get("membershipCount") != 0
        or folder_graph.get("directedReferenceCount") != 2_016
        or folder_graph.get("undirectedEdgeCount") != 1_008
    ):
        raise VerificationError("folder graph references are misclassified as memberships")
    exact_coverage = {
        "appendices": (7_995, 7_458),
        "reading_notes": (7_995, 7_928),
        "compound_child_references": (15, 0),
        "object_trace_edge_membership": (7_995, 7_928),
    }
    for structure_id, (public_count, held_count) in exact_coverage.items():
        row = by_id[structure_id]
        if (
            int(row.get("publicObjectCoverage", -1)) != public_count
            or int(row.get("heldObjectCoverage", -1)) != held_count
        ):
            raise VerificationError(f"structure coverage differs: {structure_id}")
    for structure_id, row in by_id.items():
        _verify_distribution_field(
            row.get("containerSize"), f"structure.{structure_id}.containerSize"
        )
        for field in ("publicMembershipsPerObject", "heldMembershipsPerObject"):
            _verify_distribution_field(
                row.get(field),
                f"structure.{structure_id}.{field}",
                require_multiple_count=True,
            )
        if row.get("duplicateRepresentationsAdditive") is not False:
            raise VerificationError(f"structure duplicate views became additive: {structure_id}")

    exact_multiple_counts = {
        "appendices": (0, 0),
        "compound_child_references": (15, 0),
        "folder_membership": (7_995, 7_928),
        "governed_context_representations": (7_995, None),
        "governed_spacetime_geography": (1, None),
        "legacy_trace_trees": (0, 0),
        "object_trace_edge_membership": (7_995, 7_928),
        "reading_notes": (7_995, 7_928),
        "registration_cards": (7_995, 7_928),
        "source_collection_membership": (0, 0),
        "source_document_assignment": (0, 0),
    }
    for structure_id, (public_count, held_count) in exact_multiple_counts.items():
        row = by_id[structure_id]
        public_distribution = row["publicMembershipsPerObject"]
        if public_distribution["distribution"].get("multipleCount") != public_count:
            raise VerificationError(
                f"structure public multipleCount differs: {structure_id}"
            )
        held_distribution = row["heldMembershipsPerObject"]
        if held_count is None:
            if held_distribution.get("status") != "NOT_APPLICABLE":
                raise VerificationError(
                    f"structure held multipleCount should be not applicable: {structure_id}"
                )
        elif held_distribution["distribution"].get("multipleCount") != held_count:
            raise VerificationError(
                f"structure held multipleCount differs: {structure_id}"
            )


def _verify_curatorial_support(value: Mapping[str, Any]) -> None:
    population = value.get("population")
    if not isinstance(population, Mapping) or population.get("publicObjectCount") != 7_995:
        raise VerificationError("curatorial support population differs")
    if population.get("heldObjectCount") != 0:
        raise VerificationError("held objects entered curatorial support")
    policy = value.get("rareMembershipPolicy")
    if (
        not isinstance(policy, Mapping)
        or policy.get("maximumInclusivePublicMemberCount") != 20
        or policy.get("importanceInference") != "PROHIBITED"
    ):
        raise VerificationError("curatorial rare-membership policy differs")
    features = value.get("features")
    required = {
        "rarestCuratedContainerSupport",
        "mostCommonCuratedMembershipSupport",
        "rareCuratedMembershipCount",
    }
    if not isinstance(features, Mapping) or set(features) != required:
        raise VerificationError("curatorial support feature set differs")
    for name, feature in features.items():
        if not isinstance(feature, Mapping):
            raise VerificationError(f"curatorial support feature is malformed: {name}")
        denominator = feature.get("eligibleDenominator")
        histogram = feature.get("histogram")
        if not isinstance(denominator, int) or denominator <= 0 or not isinstance(histogram, list):
            raise VerificationError(f"curatorial support histogram is malformed: {name}")
        if sum(int(row["objectCount"]) for row in histogram) != denominator:
            raise VerificationError(f"curatorial support histogram does not reconcile: {name}")
        for row in histogram:
            _close(
                float(row["rate"]), int(row["objectCount"]) / denominator,
                f"curatorial-support.{name}.rate",
            )
    hashes = value.get("hashes")
    if not isinstance(hashes, Mapping) or any(
        not isinstance(hashes.get(key), str)
        or not re.fullmatch(r"[0-9a-f]{64}", hashes[key])
        for key in ("objectVectorSha256", "aggregatePayloadSha256")
    ):
        raise VerificationError("curatorial support hashes are invalid")
    safety = value.get("safety")
    if not isinstance(safety, Mapping) or any(
        safety.get(key) != 0
        for key in (
            "objectVectorRowsEmitted", "publicObjectIdsEmitted", "heldObjectsIncluded",
            "titlesEmitted", "rawContainerIdsEmitted",
        )
    ):
        raise VerificationError("curatorial support safety boundary differs")


def _verify_native_concentration(value: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = value.get("dimensionConcentrationRows")
    if not isinstance(rows, list) or len(rows) != 4:
        raise VerificationError("native dimension concentration must contain four rows")
    expected = {
        "SOURCE": "source",
        "TEMPORAL": "decade",
        "GEOGRAPHIC": "geography",
        "CURATORIAL": "curated_container",
    }
    by_family = {
        str(row.get("family")): row for row in rows if isinstance(row, Mapping)
    }
    if {family: row.get("dimension") for family, row in by_family.items()} != expected:
        raise VerificationError("native concentration family/dimension registry differs")
    for family, row in by_family.items():
        eligible = int(row["eligibleDenominator"])
        observed = int(row["observedObjectCount"])
        unassigned = int(row["unassignedObjectCount"])
        assignments = int(row["assignmentCount"])
        distinct = int(row["distinctValueCount"])
        top1 = int(row["top1AssignmentCount"])
        top5 = int(row["top5AssignmentCount"])
        if (
            eligible != generator.PUBLIC_OBJECT_COUNT
            or observed + unassigned != eligible
            or assignments < observed
            or int(row["assignmentDenominator"]) != assignments
            or not 0 < distinct <= assignments
            or not 0 < top1 <= top5 <= assignments
        ):
            raise VerificationError(f"native concentration counts conflict: {family}")
        _close(float(row["top1Share"]), top1 / assignments, f"concentration.{family}.top1")
        _close(float(row["top5Share"]), top5 / assignments, f"concentration.{family}.top5")
        if not 0 < float(row["hhi"]) <= 1:
            raise VerificationError(f"native concentration HHI is invalid: {family}")
        if float(row["shannonEntropyNats"]) < 0 or not 0 <= float(row["normalizedEntropy"]) <= 1:
            raise VerificationError(f"native concentration entropy is invalid: {family}")
        if (
            row.get("diagnosticStatus") != "ANALYSIS_DIAGNOSTIC_NOT_A_RELATION"
            or row.get("historicalRelation") is not False
            or row.get("semanticRelation") is not False
        ):
            raise VerificationError(f"native concentration crosses semantic boundary: {family}")
        expected_hash = _sha256(generator.canonical_json_bytes({
            key: item for key, item in row.items() if key != "receiptSha256"
        }))
        if row.get("receiptSha256") != expected_hash:
            raise VerificationError(f"native concentration row hash differs: {family}")
    aggregate_hash = _sha256(generator.canonical_json_bytes(rows))
    hashes = value.get("hashes")
    if (
        not isinstance(hashes, Mapping)
        or hashes.get("dimensionConcentrationRowsSha256") != aggregate_hash
    ):
        raise VerificationError("native concentration aggregate hash differs")
    return by_family


def _verify_registry_concentration_bindings(
    rows: Sequence[Mapping[str, str]],
    concentration: Mapping[str, Mapping[str, Any]],
) -> None:
    expected = {
        "SIG-TEMPORAL-CONCENTRATION": "TEMPORAL",
        "SIG-GEOGRAPHY-CONCENTRATION": "GEOGRAPHIC",
        "SIG-SOURCE-DOMINANT": "SOURCE",
        "SIG-SOURCE-CONCENTRATION": "SOURCE",
        "SIG-SOURCE-DIVERSITY": "SOURCE",
        "SIG-CURATORIAL-SUPPORT": "CURATORIAL",
    }
    by_id = {row["signal_id"]: row for row in rows}
    for signal_id, family in expected.items():
        signal = by_id.get(signal_id)
        if signal is None:
            raise VerificationError(f"registry concentration signal is absent: {signal_id}")
        receipt_sha = concentration[family]["receiptSha256"]
        metrics = [json.loads(signal[field]) for field in ("coverage", "cardinality", "missing_rate")]
        if any(
            metric.get("dimensionConcentrationReceiptSha256") != receipt_sha
            for metric in metrics
        ):
            raise VerificationError(f"registry concentration receipt is unbound: {signal_id}")
        cardinality = metrics[1]
        if (
            int(cardinality.get("denominator", -1))
            != int(concentration[family]["assignmentDenominator"])
            or int(cardinality.get("shareDenominator", -1))
            != int(concentration[family]["assignmentDenominator"])
        ):
            raise VerificationError(f"registry concentration denominator differs: {signal_id}")


def _scan_scoped_outputs(
    research_dir: Path,
    audit_raw_dir: Path,
) -> tuple[dict[str, bytes], dict[str, bytes]]:
    research_paths = sorted(research_dir.glob("*.tsv"))
    if {path.name for path in research_paths} != set(generator.RESEARCH_SCHEMAS):
        raise VerificationError("unexpected or missing research TSV in scoped directory")
    raw_paths = sorted(audit_raw_dir.glob("*.json"))
    allowed_raw = set(generator.RAW_FILENAMES) | set(DOCUMENTED_NON_GENERATOR_RAW_RECEIPTS)
    unexpected = {path.name for path in raw_paths} - allowed_raw
    if unexpected:
        raise VerificationError(f"unexpected audit raw JSON receipts: {sorted(unexpected)}")
    scoped_research = {path.name: path.read_bytes() for path in research_paths}
    scoped_raw = {path.name: path.read_bytes() for path in raw_paths}
    generator.validate_output_safety(scoped_research, scoped_raw)
    _verify_no_title_keys(scoped_raw)
    return scoped_research, scoped_raw


def _verify_no_title_keys(raw: Mapping[str, bytes]) -> None:
    forbidden = {"title", "objecttitle", "recordtitle", "rawtitle"}
    for filename, payload in raw.items():
        value = json.loads(payload)
        normalized = {re.sub(r"[^a-z0-9]", "", key.casefold()) for key in _walk_keys(value)}
        if normalized & forbidden:
            raise VerificationError(f"{filename} exposes a title key")


def _check_committed_bytes(
    directory: Path,
    expected: Mapping[str, bytes],
    label: str,
) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    for filename, expected_bytes in expected.items():
        path = directory / filename
        if not path.is_file():
            raise VerificationError(f"missing committed {label} output: {filename}")
        actual = path.read_bytes()
        if actual != expected_bytes:
            raise VerificationError(f"committed {label} bytes differ: {filename}")
        receipts[filename] = {"bytes": len(actual), "sha256": _sha256(actual)}
    return receipts


def verify(
    *,
    research_dir: Path,
    audit_raw_dir: Path,
) -> dict[str, Any]:
    research, raw, generation = generator.run_twice()
    generator.validate_output_safety(research, raw)
    parsed = {
        filename: parse_tsv(payload, generator.RESEARCH_SCHEMAS[filename], filename)
        for filename, payload in research.items()
    }
    _verify_missingness(parsed["06_MISSINGNESS_CENSUS.tsv"])
    _verify_frequency(parsed["08_ONE_DIMENSION_FREQUENCIES.tsv"])
    _verify_pairs(parsed["09_TWO_DIMENSION_INTERSECTIONS.tsv"])
    _verify_triples(parsed["10_THREE_DIMENSION_INTERSECTIONS.tsv"])
    _verify_rare(parsed["11_RARE_INTERSECTION_REGISTER.tsv"])
    _verify_registry(parsed["13_EXPLORATION_SIGNAL_REGISTRY.tsv"])

    common = __import__("common")
    public_ids, held_ids = common.load_eligibility()
    _verify_samples(parsed["15_PATHOLOGICAL_SAMPLE_REGISTER.tsv"], public_ids, held_ids)
    _verify_no_title_keys(raw)
    research_receipts = _check_committed_bytes(research_dir, research, "research")
    raw_receipts = _check_committed_bytes(audit_raw_dir, raw, "audit raw")
    scoped_research, scoped_raw = _scan_scoped_outputs(research_dir, audit_raw_dir)
    scoped_raw_receipts = {
        filename: {"bytes": len(payload), "sha256": _sha256(payload)}
        for filename, payload in sorted(scoped_raw.items())
        if filename != "exploration-verification-summary.json"
    }
    scoped_raw_receipts["exploration-verification-summary.json"] = {
        "safetyScan": (
            "PASS" if "exploration-verification-summary.json" in scoped_raw else "NOT_PRESENT"
        ),
        "hashOmitted": "SELF_REFERENCE",
    }

    generation_boundary = generation["modelBoundary"]
    cross_summary = json.loads(raw["exploration-cross-dimensional-summary.json"])
    curatorial_summary = json.loads(raw["exploration-curatorial-summary.json"])
    structure_summary = json.loads(
        raw["exploration-source-curatorial-structure-registry.json"]
    )
    support_summary = json.loads(raw["exploration-curatorial-support-summary.json"])
    _verify_structure_registry(structure_summary)
    _verify_curatorial_support(support_summary)
    concentration_by_family = _verify_native_concentration(cross_summary)
    _verify_registry_concentration_bindings(
        parsed["13_EXPLORATION_SIGNAL_REGISTRY.tsv"], concentration_by_family
    )
    missing_rows = parsed["06_MISSINGNESS_CENSUS.tsv"]
    rare = parsed["11_RARE_INTERSECTION_REGISTER.tsv"]
    concentration = cross_summary.get("dimensionConcentrationRows", [])
    registry_rows = parsed["13_EXPLORATION_SIGNAL_REGISTRY.tsv"]
    taxonomy = {
        row["taxonomy_class"]: row for row in missing_rows if row["row_kind"] == "TAXONOMY"
    }
    movement = next(
        row for row in missing_rows
        if row["row_kind"] == "FIELD_MATRIX" and row["field"] == "movement_context"
    )
    deferred = {row["family"]: row["status"] for row in cross_summary["deferredFamilies"]}

    checks: dict[str, tuple[bool, str]] = {
        "EXP-INV-001": (
            all(row["input_source"] for row in registry_rows),
            f"named sources present on {len(registry_rows)} registry rows",
        ),
        "EXP-INV-002": (
            all(row["derivation_version"] for rows in parsed.values() for row in rows),
            "every derived TSV row carries a derivation version",
        ),
        "EXP-INV-003": (True, "all emitted counts/rates passed numeric denominator checks"),
        "EXP-INV-004": (
            all(row["semantic_relation"] == "false" for row in registry_rows),
            "registry semantic_relation=false",
        ),
        "EXP-INV-005": (
            curatorial_summary["semantic_boundary"]["historical_relation"] is False,
            "curatorial co-membership is structural diagnostic only",
        ),
        "EXP-INV-006": (
            len(taxonomy) == 10 and "UNKNOWN_SOURCE_VALUE" in taxonomy,
            "10-class explicit taxonomy exceeds null detection",
        ),
        "EXP-INV-007": (
            taxonomy["NOT_GOVERNED"]["is_generic_missing"] == "false",
            "NOT_GOVERNED remains distinct from missing",
        ),
        "EXP-INV-008": (
            "NO_PUBLISHED_MOVEMENT_CONTEXT" in movement["state_counts_json"],
            "movement absence retains NO_PUBLISHED_MOVEMENT_CONTEXT",
        ),
        "EXP-INV-009": (
            generation["population"] == {
                "publicObjectCount": generator.PUBLIC_OBJECT_COUNT,
                "heldObjectsInStatistics": 0,
            },
            "7,995 public and zero held objects in statistics",
        ),
        "EXP-INV-010": (
            not any(generator.UUID_RE.search(payload.decode("utf-8")) for payload in [*research.values(), *raw.values()]),
            "no UUID found in committed bytes",
        ),
        "EXP-INV-011": (
            all(row["importance_inference"] == "PROHIBITED" for row in rare),
            f"importance inference prohibited on {len(rare)} rare rows",
        ),
        "EXP-INV-012": (
            curatorial_summary["co_membership"]["jaccard_structural_diagnostic"]["historical_relation"] is False,
            "high overlap remains a non-historical structural diagnostic",
        ),
        "EXP-INV-013": (
            deferred.get("geographic_distance") == "DEFER",
            "geographic distance remains DEFER",
        ),
        "EXP-INV-014": (
            len(concentration) == 4
            and all(
                row["diagnosticStatus"] == "ANALYSIS_DIAGNOSTIC_NOT_A_RELATION"
                for row in concentration
            ),
            "temporal/geographic/source/curatorial concentration rows are analysis diagnostics",
        ),
        "EXP-INV-015": (
            generation["runCount"] == 2,
            f"two-run canonical SHA {generation['deterministicBundleSha256']}",
        ),
        "EXP-INV-016": (
            generation_boundary["similarityModelSelected"] is False,
            "similarity model not selected",
        ),
        "EXP-INV-017": (
            generation_boundary["rankingSelected"] is False,
            "ranking not selected",
        ),
        "EXP-INV-018": (
            generation_boundary["templateRegistryCreated"] is False,
            "template registry not created",
        ),
    }
    failures = [identifier for identifier, (passed, _) in checks.items() if not passed]
    if failures:
        raise VerificationError(f"required invariants failed: {failures}")
    invariants = [
        {
            "invariantId": identifier,
            "requirement": INVARIANT_TEXT[identifier],
            "status": "PASS",
            "evidence": checks[identifier][1],
        }
        for identifier in sorted(INVARIANT_TEXT)
    ]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": "PASS",
        "publicObjectCount": generator.PUBLIC_OBJECT_COUNT,
        "heldObjectsInStatistics": 0,
        "deterministicBundleSha256": generation["deterministicBundleSha256"],
        "invariantCount": len(invariants),
        "invariants": invariants,
        "researchOutputReceipts": research_receipts,
        "auditRawOutputReceipts": raw_receipts,
        "scopedAuditRawReceipts": scoped_raw_receipts,
        "scopedResearchTsvCount": len(scoped_research),
        "rowCounts": {filename: len(rows) for filename, rows in parsed.items()},
        "security": {
            "internalUuidCount": 0,
            "urlCount": 0,
            "rawPrivateIdentifierCount": 0,
            "heldIdentifierCount": 0,
            "titleKeyCount": 0,
        },
        "modelBoundary": generation_boundary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-dir", type=Path, default=generator.DEFAULT_RESEARCH_DIR)
    parser.add_argument("--audit-raw-dir", type=Path, default=generator.DEFAULT_AUDIT_RAW_DIR)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(
        research_dir=args.research_dir.resolve(),
        audit_raw_dir=args.audit_raw_dir.resolve(),
    )
    payload = generator.canonical_json_bytes(result, pretty=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(payload)
    print(json.dumps({
        "status": result["status"],
        "invariants": result["invariantCount"],
        "deterministicBundleSha256": result["deterministicBundleSha256"],
        "rowCounts": result["rowCounts"],
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
