#!/usr/bin/env python3
"""Generate deterministic aggregate artifacts for Exploration discovery Round 1.

The generator runs the complete analysis twice and requires byte-identical
deterministic payloads before it writes anything. Committed outputs contain no
normalized object rows, object-level missingness vectors, held identifiers,
UUIDs, URLs, raw folder tokens, object titles, or object-pair matrices.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import inspect
import json
import math
import os
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
DEFAULT_RESEARCH_DIR = ROOT / "docs/research/trace-v49-exploration-discovery-round1"
DEFAULT_AUDIT_RAW_DIR = ROOT / "docs/audits/v49-spacetime-closure-exploration-discovery/raw"

SCHEMA_VERSION = "trace-exploration-round1-generation/v1"
DERIVATION_VERSION = "trace-exploration-round1-aggregate-v1"
PUBLIC_OBJECT_COUNT = 7_995
MINIMUM_SUBSET_SUPPORT = 30
RARE_MAX_COUNT = 20
CURATORIAL_EXTENSION_PAIRS = (
    ("curated_container", "decade"),
    ("curated_container", "geography"),
    ("curated_container_type", "decade"),
    ("curated_container_type", "geography"),
)

RESEARCH_SCHEMAS: dict[str, tuple[str, ...]] = {
    "06_MISSINGNESS_CENSUS.tsv": (
        "row_kind", "row_id", "field", "taxonomy_class", "meaning",
        "applicability", "is_generic_missing", "governance_state",
        "state_counts_json", "uncertainty_counts_json", "qualifier_counts_json",
        "diagnostic_presence_count", "diagnostic_absence_count", "missing_count",
        "state_a", "state_b", "object_count", "eligible_denominator",
        "support_rate", "interpretation", "input_source", "derivation_version",
        "signal_status",
    ),
    "08_ONE_DIMENSION_FREQUENCIES.tsv": (
        "dimension", "value_id", "value_label", "object_count",
        "eligible_denominator", "object_support_rate", "observed_object_denominator",
        "dimension_assignment_denominator", "assignment_share", "rarity_band",
        "derivation_level", "signal_status", "input_source", "derivation_version",
    ),
    "09_TWO_DIMENSION_INTERSECTIONS.tsv": (
        "pair_id", "dimension_a", "value_a_id", "value_a_label", "dimension_b",
        "value_b_id", "value_b_label", "object_count", "eligible_denominator",
        "support_rate_eligible", "joint_observable_denominator",
        "support_rate_joint_observable", "dimension_a_value_object_count",
        "dimension_b_value_object_count", "conditional_observed_rate_a_given_b",
        "conditional_observed_rate_b_given_a", "lift_diagnostic",
        "lift_reference_denominator", "rarity_band", "rare_candidate",
        "diagnostic_status", "signal_status", "input_source", "derivation_version",
    ),
    "10_THREE_DIMENSION_INTERSECTIONS.tsv": (
        "triple_id", "dimension_a", "value_a_id", "value_a_label", "dimension_b",
        "value_b_id", "value_b_label", "dimension_c", "value_c_id",
        "value_c_label", "object_count", "eligible_denominator",
        "support_rate_eligible", "joint_observable_denominator",
        "support_rate_joint_observable", "dimension_a_value_object_count",
        "dimension_b_value_object_count", "dimension_c_value_object_count",
        "rarity_band", "rare_candidate", "diagnostic_status", "signal_status",
        "input_source", "derivation_version",
    ),
    "11_RARE_INTERSECTION_REGISTER.tsv": (
        "cell_kind", "spec_id", "dimension_a", "value_a_id", "value_a_label",
        "dimension_b", "value_b_id", "value_b_label", "dimension_c", "value_c_id",
        "value_c_label", "object_count", "eligible_denominator",
        "support_rate_eligible", "joint_observable_denominator",
        "support_rate_joint_observable", "rarity_band", "rare_max_count",
        "signal_status", "diagnostic_status", "importance_inference",
        "input_source", "derivation_version",
    ),
    "13_EXPLORATION_SIGNAL_REGISTRY.tsv": (
        "signal_id", "family", "signal_name", "description", "input_source",
        "input_governance_state", "direct_or_derived", "derivation_level", "coverage",
        "cardinality", "missing_rate", "numerator_definition",
        "denominator_definition", "derivation_method", "derivation_version",
        "deterministic", "explainable", "public_safe", "held_risk",
        "pairwise_or_object_level", "expected_fanout", "computational_cost",
        "materialization_risk", "historical_relation", "semantic_relation",
        "known_failure_modes", "status",
    ),
    "15_PATHOLOGICAL_SAMPLE_REGISTER.tsv": (
        "sample_id", "case_type", "public_object_ids", "selection_basis",
        "permitted_diagnostic", "candidate_count",
        "eligible_denominator", "support_rate", "input_source", "derivation_version",
        "deterministic", "public_safe", "held_object_count", "historical_relation",
        "semantic_relation", "regression_role", "status",
    ),
}

RAW_FILENAMES = (
    "exploration-source-inventory-summary.json",
    "exploration-curatorial-summary.json",
    "exploration-source-curatorial-structure-registry.json",
    "exploration-missingness-summary.json",
    "exploration-cross-dimensional-summary.json",
    "exploration-signal-registry-summary.json",
    "exploration-pathological-samples-summary.json",
    "exploration-curatorial-support-summary.json",
    "exploration-generation-summary.json",
)

UUID_RE = re.compile(
    r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[1-5][0-9A-Fa-f]{3}"
    r"-[89ABab][0-9A-Fa-f]{3}-[0-9A-Fa-f]{12}(?![0-9A-Fa-f])"
)
URL_RE = re.compile(r"(?:https?://|file://)", re.IGNORECASE)
PUBLIC_ID_RE = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
PUBLIC_ID_SEARCH_RE = re.compile(r"\bSURF-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")
RAW_PRIVATE_ID_RE = re.compile(
    r"\b(?:FOL-|TRN-OBJ-|TRTREE-|TRBRANCH-|DOS-SURF-)[A-Z0-9#_-]+\b",
    re.IGNORECASE,
)


class GenerationError(RuntimeError):
    """Raised when deterministic or safety gates prevent artifact generation."""


def canonical_json_bytes(value: Any, *, pretty: bool = False) -> bytes:
    kwargs = {
        "ensure_ascii": False,
        "sort_keys": True,
        "allow_nan": False,
    }
    if pretty:
        return (json.dumps(value, indent=2, **kwargs) + "\n").encode("utf-8")
    return (json.dumps(value, separators=(",", ":"), **kwargs) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_cell(value: Any) -> str:
    if value in (None, {}, []):
        return ""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if not math.isfinite(value):
            raise GenerationError("non-finite TSV value")
        return format(value, ".12g")
    if isinstance(value, (Mapping, list, tuple)):
        return _json_cell(value)
    text = str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")
    return text


def tsv_bytes(headers: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> bytes:
    materialized = list(rows)
    header_set = set(headers)
    lines = ["\t".join(headers)]
    for index, row in enumerate(materialized, start=1):
        unknown = set(row) - header_set
        if unknown:
            raise GenerationError(f"TSV row {index} has unknown columns: {sorted(unknown)}")
        lines.append("\t".join(_cell(row.get(header)) for header in headers))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _import_modules() -> dict[str, Any]:
    names = (
        "common",
        "source_inventory",
        "curatorial_analysis",
        "missingness_analysis",
        "cross_dimensional_analysis",
        "signal_registry",
        "pathological_samples",
    )
    modules: dict[str, Any] = {}
    for name in names:
        try:
            modules[name] = importlib.import_module(name)
        except ModuleNotFoundError as error:
            if error.name == name:
                raise GenerationError(f"required analysis module has not landed: {name}.py") from error
            raise
    return modules


def _call_pathological(
    module: Any,
    records: Sequence[Mapping[str, Any]],
    public_ids: set[str],
    held_ids: set[str],
) -> Mapping[str, Any]:
    signature = inspect.signature(module.analyze)
    parameters = signature.parameters
    kwargs: dict[str, Any] = {}
    if "authoritative_public_ids" in parameters:
        kwargs["authoritative_public_ids"] = public_ids
    elif "public_ids" in parameters:
        kwargs["public_ids"] = public_ids
    if "held_ids" in parameters:
        kwargs["held_ids"] = held_ids
    if "expected_count" in parameters:
        kwargs["expected_count"] = len(records)
    if "records" in parameters:
        kwargs["records"] = records
        result = module.analyze(**kwargs)
    else:
        result = module.analyze(records, **kwargs)
    if not isinstance(result, Mapping):
        raise GenerationError("pathological sample analysis did not return an object")
    return result


def _ratio_receipt(numerator: int, denominator: int) -> dict[str, Any]:
    if numerator < 0 or denominator <= 0 or numerator > denominator:
        raise GenerationError("aggregate ratio escapes its denominator")
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": numerator / denominator,
    }


def _r7(values: Sequence[int], probability: float) -> int | float:
    if not values:
        return 0
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    result = ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
    return int(result) if float(result).is_integer() else round(result, 6)


def _distribution(values: Iterable[int]) -> dict[str, Any]:
    materialized = list(values)
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in materialized):
        raise GenerationError("distribution values must be nonnegative integers")
    if not materialized:
        return {
            "n": 0, "min": 0, "p50": 0, "p90": 0, "p95": 0,
            "p99": 0, "max": 0, "mean": 0, "zeroCount": 0,
        }
    mean = sum(materialized) / len(materialized)
    return {
        "n": len(materialized),
        "min": min(materialized),
        "p50": _r7(materialized, 0.50),
        "p90": _r7(materialized, 0.90),
        "p95": _r7(materialized, 0.95),
        "p99": _r7(materialized, 0.99),
        "max": max(materialized),
        "mean": int(mean) if float(mean).is_integer() else round(mean, 6),
        "zeroCount": sum(value == 0 for value in materialized),
    }


def _histogram(values: Iterable[int], denominator: int) -> list[dict[str, Any]]:
    counts = Counter(values)
    if sum(counts.values()) != denominator:
        raise GenerationError("histogram count differs from its denominator")
    return [
        {
            "value": value,
            "objectCount": count,
            "eligibleDenominator": denominator,
            "rate": count / denominator,
        }
        for value, count in sorted(counts.items())
    ]


def native_concentration_receipt(cross: Mapping[str, Any]) -> dict[str, Any]:
    """Consume and validate the native cross-analysis concentration receipt."""

    rows = _extract_rows(
        cross, ("dimensionConcentrationRows",), "dimension concentration diagnostics"
    )
    expected = {
        "SOURCE": "source",
        "TEMPORAL": "decade",
        "GEOGRAPHIC": "geography",
        "CURATORIAL": "curated_container",
    }
    if len(rows) != 4 or {
        str(row.get("family")): str(row.get("dimension")) for row in rows
    } != expected:
        raise GenerationError("native dimension concentration registry differs")
    for row in rows:
        eligible = int(row["eligibleDenominator"])
        observed = int(row["observedObjectCount"])
        assignments = int(row["assignmentCount"])
        if (
            eligible != PUBLIC_OBJECT_COUNT
            or not 0 <= observed <= eligible
            or assignments < observed
            or int(row["assignmentDenominator"]) != assignments
            or row.get("diagnosticStatus") != "ANALYSIS_DIAGNOSTIC_NOT_A_RELATION"
            or row.get("historicalRelation") is not False
            or row.get("semanticRelation") is not False
        ):
            raise GenerationError("native dimension concentration receipt is invalid")
        if sha256_bytes(canonical_json_bytes({
            key: value for key, value in row.items() if key != "receiptSha256"
        })) != row.get("receiptSha256"):
            raise GenerationError("native dimension concentration row hash differs")
    rows_sha = sha256_bytes(canonical_json_bytes(rows))
    if rows_sha != cross.get("hashes", {}).get("dimensionConcentrationRowsSha256"):
        raise GenerationError("native dimension concentration aggregate hash differs")
    return {
        "schemaVersion": "trace-exploration-native-concentration-receipt/v1",
        "rowCount": len(rows),
        "rows": rows,
        "rowsSha256": rows_sha,
        "policies": {
            "topK": [1, 5],
            "hhiBasis": "assignment-event shares",
            "entropy": "natural-log Shannon entropy plus distinct-normalized entropy",
            "zeroCartesianRows": False,
            "historicalRelation": False,
            "semanticRelation": False,
            "source": "cross_dimensional_analysis.dimensionConcentrationRows",
        },
    }


def curatorial_support_summary(
    normalized_records: Sequence[Mapping[str, Any]],
    cross: Mapping[str, Any],
) -> dict[str, Any]:
    """Aggregate object-level curated support features without emitting vectors."""

    frequency = _extract_rows(cross, ("frequencyRows",), "cross frequency")
    support = {
        str(row["valueId"]): int(row["objectCount"])
        for row in frequency
        if row.get("dimension") == "curated_container"
    }
    if not support:
        raise GenerationError("curated-container support counts are absent")
    vectors: list[tuple[str, int | None, int | None, int]] = []
    rarest_values: list[int] = []
    most_common_values: list[int] = []
    rare_membership_counts: list[int] = []
    for record in sorted(normalized_records, key=lambda row: str(row["objectId"])):
        members = record.get("dimensions", {}).get("curated_container", ())
        value_ids = sorted({str(member["valueId"]) for member in members})
        counts = [support[value_id] for value_id in value_ids]
        rarest = min(counts) if counts else None
        most_common = max(counts) if counts else None
        rare_count = sum(count <= RARE_MAX_COUNT for count in counts)
        object_id = str(record["objectId"])
        vectors.append((object_id, rarest, most_common, rare_count))
        if rarest is not None and most_common is not None:
            rarest_values.append(rarest)
            most_common_values.append(most_common)
        rare_membership_counts.append(rare_count)
    if len(vectors) != PUBLIC_OBJECT_COUNT:
        raise GenerationError("curatorial support vector changed public cohort size")
    observed = len(rarest_values)
    result = {
        "schemaVersion": "trace-exploration-curatorial-support/v1",
        "derivationVersion": DERIVATION_VERSION,
        "population": {
            "publicObjectCount": PUBLIC_OBJECT_COUNT,
            "heldObjectCount": 0,
            "objectsWithCuratedMembership": observed,
            "objectsWithoutCuratedMembership": PUBLIC_OBJECT_COUNT - observed,
        },
        "rareMembershipPolicy": {
            "maximumInclusivePublicMemberCount": RARE_MAX_COUNT,
            "status": "ANALYSIS_DIAGNOSTIC",
            "importanceInference": "PROHIBITED",
        },
        "features": {
            "rarestCuratedContainerSupport": {
                "definition": "Minimum public support among an object's curated containers.",
                "eligibleDenominator": observed,
                "distribution": _distribution(rarest_values),
                "histogram": _histogram(rarest_values, observed),
            },
            "mostCommonCuratedMembershipSupport": {
                "definition": "Maximum public support among an object's curated containers.",
                "eligibleDenominator": observed,
                "distribution": _distribution(most_common_values),
                "histogram": _histogram(most_common_values, observed),
            },
            "rareCuratedMembershipCount": {
                "definition": "Number of memberships whose public support is at most 20.",
                "eligibleDenominator": PUBLIC_OBJECT_COUNT,
                "distribution": _distribution(rare_membership_counts),
                "histogram": _histogram(rare_membership_counts, PUBLIC_OBJECT_COUNT),
            },
        },
        "safety": {
            "objectVectorRowsEmitted": 0,
            "publicObjectIdsEmitted": 0,
            "heldObjectsIncluded": 0,
            "titlesEmitted": 0,
            "rawContainerIdsEmitted": 0,
        },
    }
    result["hashes"] = {
        "objectVectorSha256": sha256_bytes(canonical_json_bytes(vectors)),
        "aggregatePayloadSha256": sha256_bytes(canonical_json_bytes(result)),
    }
    return result


def govern_registry_result(
    registry: Mapping[str, Any],
    concentration: Mapping[str, Any],
    curatorial_support: Mapping[str, Any],
) -> dict[str, Any]:
    """Assert the native registry boundary without rewriting analysis semantics."""

    governed = json.loads(json.dumps(registry, ensure_ascii=False, allow_nan=False))
    rows = governed.get("rows")
    if not isinstance(rows, list) or len(rows) != 64:
        raise GenerationError("native signal registry requires exactly 64 rows")
    metadata_signals = {
        "SIG-SOURCE-NAME",
        "SIG-DESCRIPTIVE-CREATOR",
        "SIG-DESCRIPTIVE-OBJECT-TYPE",
    }
    by_id = {str(row.get("signal_id")): row for row in rows}
    if len(by_id) != 64:
        raise GenerationError("native signal registry contains duplicate IDs")
    for row in rows:
        signal_id = str(row.get("signal_id"))
        if signal_id in metadata_signals:
            if (
                row.get("direct_or_derived") != "DERIVED"
                or row.get("derivation_level")
                != "LEVEL_B_DETERMINISTIC_DERIVED_STATISTIC"
            ):
                raise GenerationError(
                    f"native signal registry misclassifies public metadata: {signal_id}"
                )
    concentration_by_family = {
        str(row["family"]): row for row in concentration["rows"]
    }
    concentration_signals = {
        "SIG-TEMPORAL-CONCENTRATION": "TEMPORAL",
        "SIG-GEOGRAPHY-CONCENTRATION": "GEOGRAPHIC",
        "SIG-SOURCE-DOMINANT": "SOURCE",
        "SIG-SOURCE-CONCENTRATION": "SOURCE",
        "SIG-SOURCE-DIVERSITY": "SOURCE",
        "SIG-CURATORIAL-SUPPORT": "CURATORIAL",
    }
    for signal_id, family in concentration_signals.items():
        receipt_sha = concentration_by_family[family]["receiptSha256"]
        signal = by_id[signal_id]
        for field in ("coverage", "cardinality", "missing_rate"):
            metric = signal.get(field)
            if (
                not isinstance(metric, Mapping)
                or metric.get("dimensionConcentrationReceiptSha256") != receipt_sha
            ):
                raise GenerationError(
                    f"native signal registry concentration receipt is unbound: {signal_id}"
                )
    level_counts = Counter(str(row["derivation_level"]) for row in rows)
    expected_levels = {
        "LEVEL_A_GOVERNED_DIRECT_FEATURE": 9,
        "LEVEL_B_DETERMINISTIC_DERIVED_STATISTIC": 43,
        "LEVEL_C_COMPOUND_EXPLORATORY_SIGNAL": 12,
    }
    if dict(level_counts) != expected_levels:
        raise GenerationError(f"signal derivation levels changed: {dict(level_counts)}")
    if not re.fullmatch(
        r"[0-9a-f]{64}", str(curatorial_support["hashes"]["objectVectorSha256"])
    ):
        raise GenerationError("curatorial support vector receipt is invalid")
    if concentration.get("rowCount") != 4:
        raise GenerationError("native concentration receipt must contain four rows")
    return governed


def _applicable_distribution(
    values: Iterable[int],
    population: str,
    *,
    include_multiple_count: bool = False,
) -> dict[str, Any]:
    materialized = [int(value) for value in values]
    distribution = _distribution(materialized)
    if include_multiple_count:
        distribution["multipleCount"] = sum(value > 1 for value in materialized)
    return {
        "status": "APPLICABLE",
        "population": population,
        "quantileMethod": "R7_LINEAR",
        "distribution": distribution,
    }


def _mapped_distribution(
    value: Mapping[str, Any],
    population: str,
    *,
    multiple_count: int | None = None,
) -> dict[str, Any]:
    required = ("n", "min", "p50", "p90", "p95", "p99", "max", "mean")
    if any(key not in value for key in required):
        raise GenerationError("source distribution receipt is incomplete")
    distribution = {key: value[key] for key in required}
    distribution["zeroCount"] = value.get("zero_count", value.get("zeroCount", 0))
    if multiple_count is not None:
        if multiple_count < 0 or multiple_count > int(distribution["n"]):
            raise GenerationError("source distribution multiple-count receipt is invalid")
        distribution["multipleCount"] = int(multiple_count)
    return {
        "status": "APPLICABLE",
        "population": population,
        "quantileMethod": "R7_LINEAR",
        "distribution": distribution,
    }


def _not_applicable(reason: str) -> dict[str, Any]:
    if not reason.strip():
        raise GenerationError("not-applicable distribution requires a rationale")
    return {"status": "NOT_APPLICABLE", "rationale": reason}


def _candidate_structure_distributions(
    source_module: Any,
    candidate_path: Path,
    public_ids: set[str],
    held_ids: set[str],
) -> dict[str, dict[str, Any]]:
    """Stream bounded candidate aggregates; never retain or emit source rows."""

    folder_members: dict[str, set[str]] = {}
    folder_related_degrees: list[int] = []
    reading_note_folders: list[str] = []
    appendix_counts: Counter[str] = Counter()
    compound_counts: Counter[str] = Counter()
    dossier_page_counts: Counter[str] = Counter()
    card_member_sets: list[set[str]] = []
    branch_member_counts: Counter[str] = Counter()
    object_branch_counts: Counter[str] = Counter()
    stream = source_module._TopLevelJsonStream(candidate_path)
    try:
        for key, is_array, value in stream.entries():
            if key == "meta":
                continue
            if not is_array:
                raise GenerationError(f"candidate structure is not an array: {key}")
            for raw_item in value:
                if not isinstance(raw_item, Mapping):
                    raise GenerationError(f"candidate {key} item is not an object")
                if key == "folders":
                    folder_id = str(raw_item.get("folderId", ""))
                    members = raw_item.get("surfaceIds")
                    related = raw_item.get("relatedFolderIds")
                    if (
                        not folder_id
                        or not isinstance(members, list)
                        or not isinstance(related, list)
                    ):
                        raise GenerationError("candidate folder structure is malformed")
                    folder_members[folder_id] = {str(member) for member in members}
                    folder_related_degrees.append(len({str(member) for member in related}))
                elif key == "readingNotes":
                    reading_note_folders.append(str(raw_item.get("folderId", "")))
                elif key == "appendices":
                    appendix_counts[str(raw_item.get("surfaceId", ""))] += 1
                elif key == "registrationCards":
                    pages = raw_item.get("memberPages")
                    if not isinstance(pages, list):
                        raise GenerationError("candidate registration-card pages are malformed")
                    card_member_sets.append({
                        str(page.get("surfaceId", ""))
                        for page in pages
                        if isinstance(page, Mapping)
                    })
                elif key == "researchDossiers":
                    pages = raw_item.get("pageSequence")
                    if not isinstance(pages, list):
                        raise GenerationError("candidate dossier pages are malformed")
                    dossier_page_counts[str(raw_item.get("anchorSurfaceId", ""))] += len(pages)
                elif key == "surfaces":
                    object_id = str(raw_item.get("surfaceId", ""))
                    children = raw_item.get("compoundChildren", [])
                    if children is not None:
                        if not isinstance(children, list):
                            raise GenerationError("candidate compound children are malformed")
                        if children:
                            compound_counts[object_id] += len(children)
                    trace = raw_item.get("trace")
                    if not isinstance(trace, Mapping):
                        raise GenerationError("candidate trace structure is malformed")
                    branch_ids = trace.get("branchIds")
                    if not isinstance(branch_ids, list):
                        raise GenerationError("candidate trace branches are malformed")
                    unique_branches = {str(branch_id) for branch_id in branch_ids}
                    object_branch_counts[object_id] = len(unique_branches)
                    for branch_id in unique_branches:
                        branch_member_counts[branch_id] += 1
    finally:
        stream.close()

    universe = public_ids | held_ids
    if len(universe) != 15_923 or public_ids & held_ids:
        raise GenerationError("candidate distribution cohort does not reconcile")

    def values(counter: Mapping[str, int], cohort: set[str]) -> list[int]:
        return [int(counter.get(object_id, 0)) for object_id in sorted(cohort)]

    def candidate_receipt(
        *,
        container_sizes: Sequence[int],
        membership_counter: Mapping[str, int],
        derivation_source: str,
    ) -> dict[str, Any]:
        public_values = values(membership_counter, public_ids)
        held_values = values(membership_counter, held_ids)
        return {
            "containerCount": len(container_sizes),
            "membershipCount": sum(container_sizes),
            "publicObjectCoverage": sum(value > 0 for value in public_values),
            "heldObjectCoverage": sum(value > 0 for value in held_values),
            "containerSize": _applicable_distribution(container_sizes, "all containers"),
            "publicMembershipsPerObject": _applicable_distribution(
                public_values,
                "authoritative public objects",
                include_multiple_count=True,
            ),
            "heldMembershipsPerObject": _applicable_distribution(
                held_values,
                "authoritative held objects; aggregate receipt only",
                include_multiple_count=True,
            ),
            "derivationSource": derivation_source,
        }

    folder_membership_counter: Counter[str] = Counter()
    for members in folder_members.values():
        folder_membership_counter.update(members)
    card_membership_counter: Counter[str] = Counter()
    for members in card_member_sets:
        card_membership_counter.update(members)
    reading_membership_counter: Counter[str] = Counter()
    reading_container_sizes: list[int] = []
    for folder_id in reading_note_folders:
        if not folder_id:
            reading_container_sizes.append(0)
            continue
        if folder_id not in folder_members:
            raise GenerationError("reading note references an unknown folder")
        members = folder_members[folder_id]
        reading_container_sizes.append(len(members))
        reading_membership_counter.update(members)

    receipts = {
        "folder_membership": candidate_receipt(
            container_sizes=[len(members) for members in folder_members.values()],
            membership_counter=folder_membership_counter,
            derivation_source="streamed candidate folder membership",
        ),
        "research_dossiers": candidate_receipt(
            container_sizes=list(dossier_page_counts.values()),
            membership_counter=dossier_page_counts,
            derivation_source="streamed candidate dossier page sequence",
        ),
        "registration_cards": candidate_receipt(
            container_sizes=[len(members) for members in card_member_sets],
            membership_counter=card_membership_counter,
            derivation_source="streamed candidate registration-card membership",
        ),
        "appendices": candidate_receipt(
            container_sizes=[1] * sum(appendix_counts.values()),
            membership_counter=appendix_counts,
            derivation_source="streamed candidate appendix surface reference",
        ),
        "reading_notes": candidate_receipt(
            container_sizes=reading_container_sizes,
            membership_counter=reading_membership_counter,
            derivation_source="streamed candidate reading-note folder membership",
        ),
        "compound_child_references": candidate_receipt(
            container_sizes=list(compound_counts.values()),
            membership_counter=compound_counts,
            derivation_source="streamed candidate compound-parent child count",
        ),
        "legacy_trace_branches": candidate_receipt(
            container_sizes=list(branch_member_counts.values()),
            membership_counter=object_branch_counts,
            derivation_source="streamed candidate trace-branch membership",
        ),
    }
    receipts["folder_related_graph"] = {
        "containerCount": len(folder_related_degrees),
        "membershipCount": 0,
        "directedReferenceCount": sum(folder_related_degrees),
        "undirectedEdgeCount": sum(folder_related_degrees) // 2,
        "publicObjectCoverage": 0,
        "heldObjectCoverage": 0,
        "containerSize": _applicable_distribution(
            folder_related_degrees, "candidate folders as graph vertices"
        ),
        "publicMembershipsPerObject": _not_applicable(
            "Folder-related edges connect curated containers, not objects."
        ),
        "heldMembershipsPerObject": _not_applicable(
            "Folder-related edges connect curated containers, not objects."
        ),
        "derivationSource": "streamed candidate folder-related adjacency",
    }
    return receipts


def structure_distribution_receipt(
    *,
    source_module: Any,
    candidate_path: Path,
    source: Mapping[str, Any],
    curatorial: Mapping[str, Any],
    normalized_records: Sequence[Mapping[str, Any]],
    cross: Mapping[str, Any],
    public_ids: set[str],
    held_ids: set[str],
) -> dict[str, Any]:
    candidate = _candidate_structure_distributions(
        source_module, candidate_path, public_ids, held_ids
    )

    def census_receipt(value: Mapping[str, Any], source_name: str) -> dict[str, Any]:
        all_rows = value["all"]
        public_rows = value["eligible"]
        held_rows = value["held"]

        def exact_multiple_count(rows: Mapping[str, Any]) -> int:
            if "objects_with_multiple_memberships" in rows:
                return int(rows["objects_with_multiple_memberships"])
            distribution = rows["memberships_per_object"]
            if float(distribution["max"]) <= 1:
                return 0
            if float(distribution["min"]) > 1:
                return int(distribution["n"])
            raise GenerationError(
                "source census cannot prove an exact multiple-membership count"
            )

        return {
            "containerCount": int(all_rows["container_count"]),
            "membershipCount": int(all_rows["membership_count"]),
            "publicObjectCoverage": int(public_rows["object_coverage"]),
            "heldObjectCoverage": int(held_rows["object_coverage"]),
            "containerSize": _mapped_distribution(
                all_rows["container_size"], "all observed containers"
            ),
            "publicMembershipsPerObject": _mapped_distribution(
                public_rows["memberships_per_object"],
                "authoritative public objects",
                multiple_count=exact_multiple_count(public_rows),
            ),
            "heldMembershipsPerObject": _mapped_distribution(
                held_rows["memberships_per_object"],
                "authoritative held objects; aggregate receipt only",
                multiple_count=exact_multiple_count(held_rows),
            ),
            "derivationSource": source_name,
        }

    folder_census = curatorial["folder_census"]["by_cohort"]
    legacy = curatorial["legacy_structure_census"]
    source_census = curatorial["source_structure_census"]
    folder_all = folder_census["all"]
    folder_public = folder_census["eligible"]
    folder_held = folder_census["held"]
    candidate["folder_membership"] = {
        "containerCount": int(folder_all["nonempty_container_count"]),
        "membershipCount": int(folder_all["membership_count"]),
        "publicObjectCoverage": int(folder_public["object_count"])
        - int(folder_public["objects_without_membership"]),
        "heldObjectCoverage": int(folder_held["object_count"])
        - int(folder_held["objects_without_membership"]),
        "containerSize": _mapped_distribution(
            folder_all["container_size"], "all observed curated containers"
        ),
        "publicMembershipsPerObject": _mapped_distribution(
            folder_public["memberships_per_object"],
            "authoritative public objects",
            multiple_count=int(folder_public["objects_with_multiple_memberships"]),
        ),
        "heldMembershipsPerObject": _mapped_distribution(
            folder_held["memberships_per_object"],
            "authoritative held objects; aggregate receipt only",
            multiple_count=int(folder_held["objects_with_multiple_memberships"]),
        ),
        "derivationSource": "immutable SQLite folder census reconciled to candidate",
    }
    candidate["legacy_trace_trees"] = census_receipt(
        legacy["trace_tree_membership"], "immutable SQLite trace-tree census"
    )
    candidate["object_trace_edge_membership"] = census_receipt(
        legacy["object_trace_edge_membership"],
        "immutable SQLite object-to-trace-edge census",
    )
    candidate["source_document_assignment"] = census_receipt(
        source_census["source_document"], "immutable SQLite source-document census"
    )
    candidate["source_collection_membership"] = census_receipt(
        source_census["source_collection"], "immutable SQLite source-collection census"
    )

    frequency = _extract_rows(cross, ("frequencyRows",), "cross frequency")
    for structure_id, dimensions in (
        ("governed_context_representations", {"medium", "theme", "movement_context"}),
        ("governed_spacetime_geography", {"geography"}),
    ):
        selected = [row for row in frequency if row.get("dimension") in dimensions]
        member_counts = [int(row["objectCount"]) for row in selected]
        per_object = [
            sum(len(record["dimensions"].get(dimension, ())) for dimension in dimensions)
            for record in normalized_records
        ]
        candidate[structure_id] = {
            "containerCount": len(selected),
            "membershipCount": sum(member_counts),
            "publicObjectCoverage": sum(value > 0 for value in per_object),
            "heldObjectCoverage": 0,
            "containerSize": _applicable_distribution(
                member_counts, "governed public dimension values"
            ),
            "publicMembershipsPerObject": _applicable_distribution(
                per_object,
                "authoritative public objects",
                include_multiple_count=True,
            ),
            "heldMembershipsPerObject": _not_applicable(
                "Governed Context and Spacetime releases are public-only projections."
            ),
            "derivationSource": "governed public projection frequency receipt",
        }

    for structure_id, row_count, reason in (
        (
            "sqlite_trace_nodes",
            int(legacy["sqlite_table_counts"]["trace_nodes"]),
            "Trace nodes are legacy structural rows, not object-membership containers.",
        ),
        (
            "sqlite_trace_edges",
            int(legacy["sqlite_table_counts"]["trace_edges"]),
            "Trace edges are legacy structural rows, not object-membership containers.",
        ),
    ):
        candidate[structure_id] = {
            "structureRowCount": row_count,
            "containerCount": 0,
            "membershipCount": 0,
            "publicObjectCoverage": 0,
            "heldObjectCoverage": 0,
            "containerSize": _not_applicable(reason),
            "publicMembershipsPerObject": _not_applicable(reason),
            "heldMembershipsPerObject": _not_applicable(reason),
            "derivationSource": "immutable SQLite scalar table census",
        }

    rows = [
        {"structureId": structure_id, **receipt}
        for structure_id, receipt in sorted(candidate.items())
    ]
    return {
        "schemaVersion": "trace-exploration-structure-distributions/v1",
        "candidatePayloadSha256": source["candidatePayloadSha256"],
        "rowCount": len(rows),
        "rows": rows,
        "rowsSha256": sha256_bytes(canonical_json_bytes(rows)),
        "safety": {
            "rawRowsEmitted": 0,
            "rawIdentifiersEmitted": 0,
            "heldIdentifiersEmitted": 0,
            "aggregateHeldCountsOnly": True,
        },
    }


def enrich_analysis(
    *,
    modules: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
    source: Mapping[str, Any],
    curatorial: Mapping[str, Any],
    missingness: Mapping[str, Any],
    cross: Mapping[str, Any],
    public_ids: set[str],
    held_ids: set[str],
) -> dict[str, Any]:
    normalized = sorted(
        (modules["cross_dimensional_analysis"]._normalize_record(record) for record in records),
        key=lambda row: str(row["objectId"]),
    )
    concentration = native_concentration_receipt(cross)
    support = curatorial_support_summary(normalized, cross)
    enriched_cross = dict(cross)
    enriched_cross["concentrationDiagnostics"] = concentration
    enriched_cross["enrichmentHashes"] = {
        "concentrationRowsSha256": concentration["rowsSha256"],
        "curatorialSupportAggregateSha256": support["hashes"]["aggregatePayloadSha256"],
    }
    enriched_cross["metrics"] = {
        **cross["metrics"],
        "concentrationDiagnosticRowCount": concentration["rowCount"],
    }
    registry_base = modules["signal_registry"].analyze(
        cross_dimensional_result=enriched_cross,
        missingness_result=missingness,
        curatorial_result=curatorial,
        derivation_version=DERIVATION_VERSION,
    )
    registry = govern_registry_result(registry_base, concentration, support)
    structures = structure_distribution_receipt(
        source_module=modules["source_inventory"],
        candidate_path=modules["common"].CANDIDATE_PATH,
        source=source,
        curatorial=curatorial,
        normalized_records=normalized,
        cross=enriched_cross,
        public_ids=public_ids,
        held_ids=held_ids,
    )
    return {
        "cross": enriched_cross,
        "registry": registry,
        "curatorialSupport": support,
        "structureDistributions": structures,
    }


def derive_once() -> dict[str, Any]:
    """Run every source module once without emitting committed artifacts."""

    modules = _import_modules()
    common = modules["common"]
    source = modules["source_inventory"].analyze(
        candidate_path=common.CANDIDATE_PATH,
        ledger_path=common.LEDGER_PATH,
    )
    curatorial = modules["curatorial_analysis"].analyze(
        sqlite_path=common.SQLITE_PATH,
        ledger_path=common.LEDGER_PATH,
        candidate_summary=source,
    )
    loaded = common.load_normalized_public_records()
    records = loaded["records"]
    public_ids = set(loaded["publicObjectIds"])
    held_ids = set(loaded["heldObjectIds"])
    if len(records) != PUBLIC_OBJECT_COUNT or len(public_ids) != PUBLIC_OBJECT_COUNT:
        raise GenerationError("public cohort does not contain exactly 7,995 objects")
    if any(record["objectId"] in held_ids for record in records):
        raise GenerationError("held object entered normalized public records")

    missingness = modules["missingness_analysis"].analyze(
        records,
        expected_count=PUBLIC_OBJECT_COUNT,
        include_object_vectors=False,
    )
    cross = modules["cross_dimensional_analysis"].analyze(
        records,
        expected_count=PUBLIC_OBJECT_COUNT,
        extension_pairs=CURATORIAL_EXTENSION_PAIRS,
        minimum_subset_support=MINIMUM_SUBSET_SUPPORT,
        rare_max_count=RARE_MAX_COUNT,
    )
    enrichment = enrich_analysis(
        modules=modules,
        records=records,
        source=source,
        curatorial=curatorial,
        missingness=missingness,
        cross=cross,
        public_ids=public_ids,
        held_ids=held_ids,
    )
    cross = enrichment["cross"]
    registry = enrichment["registry"]
    if not isinstance(registry, Mapping):
        raise GenerationError("signal registry analysis did not return an object")
    pathological = _call_pathological(
        modules["pathological_samples"], records, public_ids, held_ids
    )
    return {
        "source": source,
        "curatorial": curatorial,
        "missingness": missingness,
        "cross": cross,
        "registry": registry,
        "pathological": pathological,
        "curatorialSupport": enrichment["curatorialSupport"],
        "structureDistributions": enrichment["structureDistributions"],
        "receipts": loaded["receipts"],
        "publicObjectIds": public_ids,
        "heldObjectIds": held_ids,
    }


def _without_keys(value: Any, forbidden: frozenset[str]) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _without_keys(item, forbidden)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
            if str(key) not in forbidden
        }
    if isinstance(value, (list, tuple)):
        return [_without_keys(item, forbidden) for item in value]
    if isinstance(value, set):
        return sorted(_without_keys(item, forbidden) for item in value)
    return value


def deterministic_bundle(result: Mapping[str, Any]) -> dict[str, Any]:
    """Remove timings and temp-only vectors while retaining analysis semantics."""

    missingness = _without_keys(
        result["missingness"],
        frozenset({"elapsedMs", "objectVectors", "pathologicalSelections"}),
    )
    cross = _without_keys(result["cross"], frozenset({"elapsedMs"}))
    curatorial = _without_keys(result["curatorial"], frozenset({"performance"}))
    registry = _without_keys(
        result["registry"],
        frozenset({"elapsedMs", "performance", "timings"}),
    )
    pathological = _without_keys(
        result["pathological"],
        frozenset({"elapsedMs", "performance", "timings"}),
    )
    curatorial_support = _without_keys(
        result["curatorialSupport"], frozenset({"elapsedMs", "performance", "timings"})
    )
    structure_distributions = _without_keys(
        result["structureDistributions"],
        frozenset({"elapsedMs", "performance", "timings"}),
    )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "derivationVersion": DERIVATION_VERSION,
        "receipts": result["receipts"],
        "source": result["source"],
        "curatorial": curatorial,
        "missingness": missingness,
        "cross": cross,
        "registry": registry,
        "pathological": pathological,
        "curatorialSupport": curatorial_support,
        "structureDistributions": structure_distributions,
        "population": {"publicObjectCount": PUBLIC_OBJECT_COUNT, "heldObjectsInStatistics": 0},
    }


def _dimension_source(dimension: str) -> str:
    if dimension in {"medium", "theme", "movement_context"}:
        return "governed Context public projection"
    if dimension in {
        "decade", "geography", "temporal_precision",
        "geography_mapping_state", "geography_class",
    }:
        return "governed Spacetime public projection"
    if dimension in {"source", "object_type", "creator"}:
        return "public Context selected-record metadata"
    if dimension in {"curated_container", "curated_container_type"}:
        return "immutable SQLite curation reconciled to governed public labels"
    raise GenerationError(f"dimension has no named source: {dimension}")


def _field_source(field: str) -> str:
    if field in {"medium", "theme", "movement_context"}:
        return "governed Context public projection"
    if field in {"temporal_precision", "geography_mapping_state"}:
        return "governed Spacetime public projection"
    if field in {"creator", "source", "object_type"}:
        return "public Context selected-record metadata"
    if field == "source_collection":
        return "immutable SQLite internal diagnostic"
    raise GenerationError(f"field has no named source: {field}")


def _field_signal_status(field: str) -> str:
    if field in {"medium", "theme"}:
        return "HIGH_POTENTIAL"
    if field == "source_collection":
        return "RESEARCH_ONLY"
    return "SUPPORTING_SIGNAL"


def missingness_rows(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    derivation = str(result["derivationVersion"])
    for item in sorted(result["taxonomy"], key=lambda row: str(row["class"])):
        taxonomy_class = str(item["class"])
        rows.append({
            "row_kind": "TAXONOMY",
            "row_id": f"TAXONOMY:{taxonomy_class}",
            "taxonomy_class": taxonomy_class,
            "meaning": item["meaning"],
            "applicability": item["applicability"],
            "is_generic_missing": item["isGenericMissing"],
            "interpretation": "SUPPORTED_CLASSIFICATION_NOT_A_SINGLE_SCORE",
            "input_source": "Round 1 explicit missingness taxonomy",
            "derivation_version": derivation,
            "signal_status": "SUPPORTING_SIGNAL",
        })
    for item in sorted(result["fieldMatrix"], key=lambda row: str(row["field"])):
        field = str(item["field"])
        denominator = int(item["eligibleDenominator"])
        object_count = int(item.get("diagnosticProvidedCount", denominator))
        rows.append({
            "row_kind": "FIELD_MATRIX",
            "row_id": f"FIELD:{field}",
            "field": field,
            "governance_state": item["governanceState"],
            "state_counts_json": _json_cell(item.get("stateCounts")),
            "uncertainty_counts_json": _json_cell(item.get("uncertaintyCounts")),
            "qualifier_counts_json": _json_cell(item.get("qualifierCounts")),
            "diagnostic_presence_count": item.get("diagnosticPresenceCount"),
            "diagnostic_absence_count": item.get("diagnosticAbsenceCount"),
            "missing_count": item.get("missingCount", item.get("nullMissingCount")),
            "object_count": object_count,
            "eligible_denominator": denominator,
            "support_rate": object_count / denominator,
            "interpretation": item.get("interpretation", "FIELD_STATE_CENSUS"),
            "input_source": _field_source(field),
            "derivation_version": derivation,
            "signal_status": _field_signal_status(field),
        })
    for item in sorted(
        result["cooccurrences"], key=lambda row: (str(row["stateA"]), str(row["stateB"]))
    ):
        rows.append({
            "row_kind": "COOCCURRENCE",
            "row_id": f"COOCCURRENCE:{item['stateA']}__{item['stateB']}",
            "state_a": item["stateA"],
            "state_b": item["stateB"],
            "object_count": item["count"],
            "eligible_denominator": item["eligibleDenominator"],
            "support_rate": item["supportRate"],
            "interpretation": item["interpretation"],
            "input_source": "derived public missingness vectors",
            "derivation_version": derivation,
            "signal_status": "RESEARCH_ONLY",
        })
    if Counter(row["row_kind"] for row in rows) != {
        "TAXONOMY": 10, "FIELD_MATRIX": 9, "COOCCURRENCE": 19,
    }:
        raise GenerationError("missingness census row groups do not reconcile to 38 rows")
    return rows


def frequency_rows(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    derivation = str(result["derivationVersion"])
    rows = [{
        "dimension": item["dimension"],
        "value_id": item["valueId"],
        "value_label": item["valueLabel"],
        "object_count": item["objectCount"],
        "eligible_denominator": item["eligibleDenominator"],
        "object_support_rate": item["objectSupportRate"],
        "observed_object_denominator": item["observedObjectDenominator"],
        "dimension_assignment_denominator": item["dimensionAssignmentDenominator"],
        "assignment_share": item["assignmentShare"],
        "rarity_band": item["rarityBand"],
        "derivation_level": item["derivationLevel"],
        "signal_status": item["signalStatus"],
        "input_source": _dimension_source(str(item["dimension"])),
        "derivation_version": derivation,
    } for item in result["frequencyRows"]]
    return sorted(rows, key=lambda row: (str(row["dimension"]), str(row["value_id"])))


def pair_rows(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    derivation = str(result["derivationVersion"])
    rows: list[dict[str, Any]] = []
    for item in result["pairRows"]:
        pair_id = str(item["pairId"])
        is_rare = int(item["objectCount"]) <= RARE_MAX_COUNT and pair_id != "creator__medium"
        rows.append({
            "pair_id": pair_id,
            "dimension_a": item["dimensionA"],
            "value_a_id": item["valueAId"],
            "value_a_label": item["valueALabel"],
            "dimension_b": item["dimensionB"],
            "value_b_id": item["valueBId"],
            "value_b_label": item["valueBLabel"],
            "object_count": item["objectCount"],
            "eligible_denominator": item["eligibleDenominator"],
            "support_rate_eligible": item["supportRateEligible"],
            "joint_observable_denominator": item["jointObservableDenominator"],
            "support_rate_joint_observable": item["supportRateJointObservable"],
            "dimension_a_value_object_count": item["dimensionAValueObjectCount"],
            "dimension_b_value_object_count": item["dimensionBValueObjectCount"],
            "conditional_observed_rate_a_given_b": item["conditionalObservedRateAGivenB"],
            "conditional_observed_rate_b_given_a": item["conditionalObservedRateBGivenA"],
            "lift_diagnostic": item["liftDiagnostic"],
            "lift_reference_denominator": item["liftReferenceDenominator"],
            "rarity_band": item["rarityBand"],
            "rare_candidate": is_rare,
            "diagnostic_status": item["diagnosticStatus"],
            "signal_status": item["signalStatus"],
            "input_source": (
                f"{_dimension_source(str(item['dimensionA']))}; "
                f"{_dimension_source(str(item['dimensionB']))}"
            ),
            "derivation_version": derivation,
        })
    return sorted(rows, key=lambda row: (
        str(row["pair_id"]), str(row["value_a_id"]), str(row["value_b_id"])
    ))


def triple_rows(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    derivation = str(result["derivationVersion"])
    rows: list[dict[str, Any]] = []
    for item in result["tripleRows"]:
        marginals = list(item["marginalObjectCounts"])
        if len(marginals) != 3:
            raise GenerationError("triple marginal count vector is not length three")
        rows.append({
            "triple_id": item["tripleId"],
            "dimension_a": item["dimensionA"],
            "value_a_id": item["valueAId"],
            "value_a_label": item["valueALabel"],
            "dimension_b": item["dimensionB"],
            "value_b_id": item["valueBId"],
            "value_b_label": item["valueBLabel"],
            "dimension_c": item["dimensionC"],
            "value_c_id": item["valueCId"],
            "value_c_label": item["valueCLabel"],
            "object_count": item["objectCount"],
            "eligible_denominator": item["eligibleDenominator"],
            "support_rate_eligible": item["supportRateEligible"],
            "joint_observable_denominator": item["jointObservableDenominator"],
            "support_rate_joint_observable": item["supportRateJointObservable"],
            "dimension_a_value_object_count": marginals[0],
            "dimension_b_value_object_count": marginals[1],
            "dimension_c_value_object_count": marginals[2],
            "rarity_band": item["rarityBand"],
            "rare_candidate": int(item["objectCount"]) <= RARE_MAX_COUNT,
            "diagnostic_status": item["diagnosticStatus"],
            "signal_status": item["signalStatus"],
            "input_source": "; ".join(
                _dimension_source(str(item[key]))
                for key in ("dimensionA", "dimensionB", "dimensionC")
            ),
            "derivation_version": derivation,
        })
    return sorted(rows, key=lambda row: (
        str(row["triple_id"]), str(row["value_a_id"]),
        str(row["value_b_id"]), str(row["value_c_id"]),
    ))


def rare_rows(
    pairs: Sequence[Mapping[str, Any]],
    triples: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in pairs:
        if not item["rare_candidate"]:
            continue
        rows.append({
            "cell_kind": "PAIR",
            "spec_id": item["pair_id"],
            "dimension_a": item["dimension_a"],
            "value_a_id": item["value_a_id"],
            "value_a_label": item["value_a_label"],
            "dimension_b": item["dimension_b"],
            "value_b_id": item["value_b_id"],
            "value_b_label": item["value_b_label"],
            "object_count": item["object_count"],
            "eligible_denominator": item["eligible_denominator"],
            "support_rate_eligible": item["support_rate_eligible"],
            "joint_observable_denominator": item["joint_observable_denominator"],
            "support_rate_joint_observable": item["support_rate_joint_observable"],
            "rarity_band": item["rarity_band"],
            "rare_max_count": RARE_MAX_COUNT,
            "signal_status": "RARE_INTERSECTION_SIGNAL_CANDIDATE",
            "diagnostic_status": "ANALYSIS_DIAGNOSTIC",
            "importance_inference": "PROHIBITED",
            "input_source": item["input_source"],
            "derivation_version": item["derivation_version"],
        })
    for item in triples:
        if not item["rare_candidate"]:
            continue
        rows.append({
            "cell_kind": "BOUNDED_TRIPLE",
            "spec_id": item["triple_id"],
            "dimension_a": item["dimension_a"],
            "value_a_id": item["value_a_id"],
            "value_a_label": item["value_a_label"],
            "dimension_b": item["dimension_b"],
            "value_b_id": item["value_b_id"],
            "value_b_label": item["value_b_label"],
            "dimension_c": item["dimension_c"],
            "value_c_id": item["value_c_id"],
            "value_c_label": item["value_c_label"],
            "object_count": item["object_count"],
            "eligible_denominator": item["eligible_denominator"],
            "support_rate_eligible": item["support_rate_eligible"],
            "joint_observable_denominator": item["joint_observable_denominator"],
            "support_rate_joint_observable": item["support_rate_joint_observable"],
            "rarity_band": item["rarity_band"],
            "rare_max_count": RARE_MAX_COUNT,
            "signal_status": "RARE_INTERSECTION_SIGNAL_CANDIDATE",
            "diagnostic_status": "ANALYSIS_DIAGNOSTIC",
            "importance_inference": "PROHIBITED",
            "input_source": item["input_source"],
            "derivation_version": item["derivation_version"],
        })
    rank = {"PAIR": 0, "BOUNDED_TRIPLE": 1}
    rows.sort(key=lambda row: (
        rank[str(row["cell_kind"])], str(row["spec_id"]), str(row["value_a_id"]),
        str(row["value_b_id"]), str(row.get("value_c_id", "")),
    ))
    if len(rows) != 4_251:
        raise GenerationError(f"rare intersection register expected 4,251 rows, found {len(rows)}")
    return rows


def _extract_rows(
    result: Mapping[str, Any],
    candidates: Sequence[str],
    label: str,
) -> list[Mapping[str, Any]]:
    for key in candidates:
        value = result.get(key)
        if isinstance(value, list) and all(isinstance(item, Mapping) for item in value):
            return list(value)
    raise GenerationError(f"{label} result has no supported row collection: {candidates}")


def signal_registry_rows(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    source_rows = _extract_rows(
        result, ("rows", "signalRows", "signalRegistry", "signals"), "signal registry"
    )
    headers = RESEARCH_SCHEMAS["13_EXPLORATION_SIGNAL_REGISTRY.tsv"]
    aliases = {
        "coverage": ("coverage", "coverage_count", "coverageCount"),
        "cardinality": ("cardinality", "cardinality_count", "cardinalityCount"),
        "missing_rate": ("missing_rate", "missingRate"),
    }
    rows: list[dict[str, Any]] = []
    for source in source_rows:
        row: dict[str, Any] = {}
        for header in headers:
            if header in source:
                row[header] = source[header]
                continue
            camel = header.split("_")[0] + "".join(part.title() for part in header.split("_")[1:])
            if camel in source:
                row[header] = source[camel]
                continue
            for alias in aliases.get(header, ()):
                if alias in source:
                    row[header] = source[alias]
                    break
        missing = [header for header in headers if header not in row]
        if missing:
            raise GenerationError(f"signal registry row is missing required columns: {missing}")
        rows.append(row)
    rows.sort(key=lambda row: str(row["signal_id"]))
    if len({str(row["signal_id"]) for row in rows}) != len(rows):
        raise GenerationError("signal registry contains duplicate signal_id values")
    return rows


def pathological_rows(
    result: Mapping[str, Any],
    public_ids: set[str],
    held_ids: set[str],
) -> list[dict[str, Any]]:
    source_rows = _extract_rows(
        result, ("rows", "samples", "sampleRows", "pathologicalSamples"),
        "pathological samples",
    )
    headers = RESEARCH_SCHEMAS["15_PATHOLOGICAL_SAMPLE_REGISTER.tsv"]
    rows: list[dict[str, Any]] = []
    for source in source_rows:
        normalized = {
            str(key): value for key, value in source.items()
        }

        def get(*names: str, default: Any = None) -> Any:
            for name in names:
                if name in normalized:
                    return normalized[name]
            return default

        object_ids_value = normalized.get(
            "public_object_ids",
            normalized.get(
                "publicObjectIds",
                normalized.get(
                    "public_id",
                    normalized.get("publicId", normalized.get("objectIds")),
                ),
            ),
        )
        if isinstance(object_ids_value, str):
            object_ids = sorted(
                value.strip() for value in object_ids_value.split(";") if value.strip()
            )
        elif isinstance(object_ids_value, (list, tuple)):
            object_ids = sorted(str(value).strip() for value in object_ids_value)
        else:
            raise GenerationError("pathological sample lacks public object IDs")
        if not 1 <= len(object_ids) <= 2 or len(set(object_ids)) != len(object_ids):
            raise GenerationError("pathological sample must contain one or two public IDs")
        if any(not PUBLIC_ID_RE.fullmatch(value) for value in object_ids):
            raise GenerationError("pathological sample contains a non-public identifier")
        if any(value not in public_ids or value in held_ids for value in object_ids):
            raise GenerationError("pathological sample contains a non-authoritative public ID")

        sample_id = get("sample_id", "sampleId", "case_id", "caseId")
        case_type = get("case_type", "caseType", "case_id", "caseId")
        if sample_id == "CROSS_SOURCE_CONTEXT_MATCH":
            if len(object_ids) != 2:
                raise GenerationError("cross-source/context sample requires a public-ID pair")
        elif len(object_ids) != 1:
            raise GenerationError("only cross-source/context may contain a public-ID pair")

        coverage = get("case_coverage", "caseCoverage")
        if not isinstance(coverage, Mapping):
            raise GenerationError("pathological sample lacks denominator-bearing case coverage")
        numerator = coverage.get("numerator")
        denominator = coverage.get("denominator")
        rate = coverage.get("rate")
        if (
            isinstance(numerator, bool)
            or not isinstance(numerator, int)
            or numerator < 1
            or isinstance(denominator, bool)
            or not isinstance(denominator, int)
            or denominator != PUBLIC_OBJECT_COUNT
            or numerator > denominator
            or isinstance(rate, bool)
            or not isinstance(rate, (int, float))
            or not math.isfinite(float(rate))
            or not math.isclose(
                float(rate), numerator / denominator, rel_tol=1e-12, abs_tol=1e-15
            )
        ):
            raise GenerationError("pathological case coverage is invalid")

        permitted_diagnostic = get(
            "permitted_diagnostic", "permittedDiagnostic", default="PUBLIC_COHORT_DIAGNOSTIC_ONLY"
        )

        row = {
            "sample_id": sample_id,
            "case_type": case_type,
            "public_object_ids": ";".join(object_ids),
            "selection_basis": get(
                "selection_basis", "selectionBasis", "selection_rule", "selectionRule"
            ),
            "permitted_diagnostic": permitted_diagnostic,
            "candidate_count": numerator,
            "eligible_denominator": denominator,
            "support_rate": rate,
            "input_source": get("input_source", "inputSource", default="governed public analysis cohort"),
            "derivation_version": get("derivation_version", "derivationVersion", default=DERIVATION_VERSION),
            "deterministic": get("deterministic", default=True),
            "public_safe": get("public_safe", "publicSafe", default=True),
            "held_object_count": get("held_object_count", "heldObjectCount", default=0),
            "historical_relation": get("historical_relation", "historicalRelation", default=False),
            "semantic_relation": get("semantic_relation", "semanticRelation", default=False),
            "regression_role": get("regression_role", "regressionRole", default="FUTURE_REGRESSION_CORPUS"),
            "status": get("status", default="SELECTED_PATHOLOGICAL_CASE"),
        }
        missing = [header for header in headers if row.get(header) is None]
        if missing:
            raise GenerationError(f"pathological sample row is missing columns: {missing}")
        rows.append(row)
    rows.sort(key=lambda row: str(row["sample_id"]))
    if len(rows) != 15 or len({str(row["sample_id"]) for row in rows}) != 15:
        raise GenerationError("pathological register must contain 15 unique samples")
    return rows


def _structure_row(
    structure_id: str,
    structure_name: str,
    population_state: str,
    classifications: Sequence[str],
    container_count: int,
    membership_count: int,
    public_coverage: int,
    held_coverage: int,
    count_source: str,
    *,
    duplicate_count: int = 0,
    duplicate_additive: bool = False,
    note: str = "",
    structure_row_count: int | None = None,
    directed_reference_count: int | None = None,
    undirected_edge_count: int | None = None,
) -> dict[str, Any]:
    row = {
        "structureId": structure_id,
        "structureName": structure_name,
        "populationState": population_state,
        "classifications": list(classifications),
        "containerCount": container_count,
        "membershipCount": membership_count,
        "publicObjectCoverage": public_coverage,
        "heldObjectCoverage": held_coverage,
        "countSource": count_source,
        "duplicateRepresentationCount": duplicate_count,
        "duplicateRepresentationsAdditive": duplicate_additive,
        "historicalRelation": False,
        "semanticRelation": False,
        "note": note,
    }
    if structure_row_count is not None:
        row["structureRowCount"] = structure_row_count
    if directed_reference_count is not None:
        row["directedReferenceCount"] = directed_reference_count
    if undirected_edge_count is not None:
        row["undirectedEdgeCount"] = undirected_edge_count
    return row


def source_curatorial_structure_registry(
    source: Mapping[str, Any],
    curatorial: Mapping[str, Any],
    cross: Mapping[str, Any],
    structure_distributions: Mapping[str, Any],
) -> dict[str, Any]:
    top = source["topLevelStructures"]
    folders = source["folderStructures"]
    legacy = source["legacyTraceStructures"]
    compound = int(source["compoundChildReferenceCount"])
    folder_census = curatorial["folder_census"]
    cohort = folder_census["by_cohort"]
    legacy_tables = curatorial["legacy_structure_census"]["sqlite_table_counts"]
    source_census = curatorial["source_structure_census"]
    frequency = cross["frequencyRows"]

    def dimension_stats(names: set[str]) -> tuple[int, int, int]:
        selected = [row for row in frequency if row["dimension"] in names]
        cardinality = len(selected)
        memberships = sum(
            int(next(row["dimensionAssignmentDenominator"] for row in selected if row["dimension"] == name))
            for name in sorted(names)
        )
        coverage = max(
            int(row["observedObjectDenominator"]) for row in selected
        ) if selected else 0
        return cardinality, memberships, coverage

    context_cardinality, context_memberships, context_coverage = dimension_stats(
        {"medium", "theme", "movement_context"}
    )
    geography_cardinality, geography_memberships, geography_coverage = dimension_stats(
        {"geography"}
    )
    source_document = source_census["source_document"]
    source_collection = source_census["source_collection"]
    populated_internal = ("POPULATED", "LEGACY_ONLY", "INTERNAL_ONLY", "UNSAFE")
    rows = [
        _structure_row(
            "folder_membership", "Folder membership", "POPULATED",
            ("POPULATED", "LEGACY_ONLY", "CANDIDATE", "INTERNAL_ONLY", "UNSAFE"),
            int(folder_census["folder_count"]), int(folder_census["membership_pair_count"]),
            int(cohort["eligible"]["object_count"] - cohort["eligible"]["objects_without_membership"]),
            int(cohort["held"]["object_count"] - cohort["held"]["objects_without_membership"]),
            "immutable SQLite plus candidate duplicate-view receipt",
            duplicate_count=len(folders["duplicateRepresentationIntegrity"]),
            duplicate_additive=False,
            note="Duplicate candidate representations reconcile to one non-additive membership set.",
        ),
        _structure_row(
            "folder_related_graph", "Folder-related graph", "POPULATED",
            ("POPULATED", "LEGACY_ONLY", "CANDIDATE", "INTERNAL_ONLY", "UNSAFE"),
            int(top["folders"]), 0, 0, 0,
            "canonical candidate aggregate receipt",
            directed_reference_count=int(folders["relatedFolderDirectedReferences"]),
            undirected_edge_count=int(folders["relatedFolderUndirectedEdges"]),
        ),
        _structure_row(
            "governed_context_representations", "Governed Context representations", "POPULATED",
            ("POPULATED", "PUBLIC_GOVERNED"), context_cardinality, context_memberships,
            context_coverage, 0, "governed Context public projection",
        ),
        _structure_row(
            "governed_spacetime_geography", "Governed Spacetime geography assignments", "POPULATED",
            ("POPULATED", "PUBLIC_GOVERNED"), geography_cardinality,
            geography_memberships, geography_coverage, 0,
            "governed Spacetime public projection",
        ),
        _structure_row(
            "research_dossiers", "Research dossiers", "POPULATED", populated_internal,
            int(top["researchDossiers"]), int(source["dossierStructures"]["pageCount"]),
            PUBLIC_OBJECT_COUNT, int(source["population"]["heldObjects"]),
            "canonical candidate aggregate receipt",
        ),
        _structure_row(
            "registration_cards", "Registration cards", "POPULATED", populated_internal,
            int(top["registrationCards"]), int(folders["membershipCount"]),
            PUBLIC_OBJECT_COUNT, int(source["population"]["heldObjects"]),
            "canonical candidate aggregate receipt", duplicate_count=1,
            duplicate_additive=False, note="Member pages duplicate the folder membership view.",
        ),
        _structure_row(
            "appendices", "Appendices", "POPULATED", populated_internal,
            int(top["appendices"]), int(top["appendices"]), 0, 0,
            "canonical candidate aggregate receipt",
        ),
        _structure_row(
            "reading_notes", "Reading notes", "POPULATED", populated_internal,
            int(top["readingNotes"]), int(top["readingNotes"]), 0, 0,
            "canonical candidate aggregate receipt",
        ),
        _structure_row(
            "bookmarks", "Bookmarks", "EMPTY", ("EMPTY", "LEGACY_ONLY", "INTERNAL_ONLY"),
            0, int(top["bookmarks"]), 0, 0, "canonical candidate aggregate receipt",
        ),
        _structure_row(
            "compound_child_references", "Compound-child references", "POPULATED",
            populated_internal, 0, compound, 0, 0, "canonical candidate aggregate receipt",
        ),
        _structure_row(
            "legacy_trace_trees", "Legacy trace trees", "POPULATED", populated_internal,
            int(legacy["treeCount"]), int(legacy["treeMembershipCount"]),
            int(legacy["publicTreeMembershipCount"]), int(legacy["heldTreeMembershipCount"]),
            "canonical candidate aggregate receipt",
        ),
        _structure_row(
            "legacy_trace_branches", "Legacy trace branches", "POPULATED", populated_internal,
            int(legacy["branchCount"]), int(legacy["branchMembershipCount"]),
            int(legacy["publicBranchMembershipCount"]), int(legacy["heldBranchMembershipCount"]),
            "canonical candidate aggregate receipt",
        ),
        _structure_row(
            "sqlite_trace_nodes", "SQLite trace nodes", "POPULATED", populated_internal,
            0, 0, 0, 0, "immutable SQLite aggregate census",
            structure_row_count=int(legacy_tables["trace_nodes"]),
        ),
        _structure_row(
            "sqlite_trace_edges", "SQLite trace edges", "POPULATED", populated_internal,
            0, 0, 0, 0, "immutable SQLite aggregate census",
            structure_row_count=int(legacy_tables["trace_edges"]),
        ),
        _structure_row(
            "object_trace_edge_membership", "Object-to-trace-edge membership", "POPULATED",
            populated_internal, 0, int(legacy_tables["object_trace_edges"]), 0, 0,
            "immutable SQLite aggregate census",
        ),
        _structure_row(
            "source_document_assignment", "Source-document assignment", "POPULATED",
            populated_internal, int(source_document["all"]["container_count"]),
            int(source_document["all"]["membership_count"]),
            int(source_document["eligible"]["object_coverage"]),
            int(source_document["held"]["object_coverage"]),
            "immutable SQLite aggregate census",
        ),
        _structure_row(
            "source_collection_membership", "Source-collection membership", "POPULATED",
            ("POPULATED", "LEGACY_ONLY", "CANDIDATE", "INTERNAL_ONLY", "UNSAFE"),
            int(source_collection["all"]["container_count"]),
            int(source_collection["all"]["membership_count"]),
            int(source_collection["eligible"]["object_coverage"]),
            int(source_collection["held"]["object_coverage"]),
            "immutable SQLite aggregate census",
        ),
        _structure_row(
            "governed_trace_projection", "Governed TRACE projection", "EMPTY",
            ("EMPTY", "PUBLIC_GOVERNED"), 0, 0, 0, 0,
            "known fail-closed public projection receipt",
        ),
        _structure_row(
            "accepted_semantic_relations", "Accepted semantic relations", "EMPTY",
            ("EMPTY", "PUBLIC_GOVERNED"), 0, 0, 0, 0,
            "Round 1 semantic boundary receipt",
        ),
        _structure_row(
            "sealed_public_folder_membership_release",
            "Current sealed public folder-membership release", "EMPTY",
            ("EMPTY", "CANDIDATE"), 0, 0, 0, 0,
            "current sealed release inventory",
        ),
    ]
    distribution_rows = {
        str(row["structureId"]): row
        for row in _extract_rows(
            structure_distributions, ("rows",), "structure distributions"
        )
    }
    populated_ids = {
        str(row["structureId"])
        for row in rows
        if row["populationState"] == "POPULATED"
    }
    if set(distribution_rows) != populated_ids:
        raise GenerationError("structure distribution receipt must cover all 16 populated rows")
    for row in rows:
        structure_id = str(row["structureId"])
        distribution = distribution_rows.get(structure_id)
        if distribution is None:
            reason = "Structure is empty in the current release."
            row["containerSize"] = _not_applicable(reason)
            row["publicMembershipsPerObject"] = _not_applicable(reason)
            row["heldMembershipsPerObject"] = _not_applicable(reason)
            row["distributionSource"] = "current empty-release receipt"
            continue
        for scalar in (
            "containerCount", "membershipCount", "publicObjectCoverage",
            "heldObjectCoverage", "structureRowCount", "directedReferenceCount",
            "undirectedEdgeCount",
        ):
            if scalar in distribution:
                row[scalar] = int(distribution[scalar])
        row["containerSize"] = distribution["containerSize"]
        row["publicMembershipsPerObject"] = distribution["publicMembershipsPerObject"]
        row["heldMembershipsPerObject"] = distribution["heldMembershipsPerObject"]
        row["distributionSource"] = distribution["derivationSource"]
    rows.sort(key=lambda row: str(row["structureId"]))
    population_counts = Counter(str(row["populationState"]) for row in rows)
    if len(rows) != 20 or population_counts != {"POPULATED": 16, "EMPTY": 4}:
        raise GenerationError("source/curatorial structure registry does not reconcile 16/4")
    classification_counts = Counter(
        str(classification)
        for row in rows
        for classification in row["classifications"]
    )
    expected_classification_counts = {
        "CANDIDATE": 4,
        "EMPTY": 4,
        "INTERNAL_ONLY": 15,
        "LEGACY_ONLY": 15,
        "POPULATED": 16,
        "PUBLIC_GOVERNED": 4,
        "UNSAFE": 14,
    }
    if dict(classification_counts) != expected_classification_counts:
        raise GenerationError(
            f"structure classification counts changed: {dict(classification_counts)}"
        )
    payload = {
        "schemaVersion": "trace-exploration-source-curatorial-structure-registry/v1",
        "derivationVersion": DERIVATION_VERSION,
        "rowCount": len(rows),
        "populationStateCounts": dict(sorted(population_counts.items())),
        "classificationCounts": dict(sorted(classification_counts.items())),
        "duplicateRepresentationPolicy": "DUPLICATE_VIEWS_ARE_NON_ADDITIVE",
        "rows": rows,
        "invariants": {
            "historicalRelationsCreated": 0,
            "semanticRelationsCreated": 0,
            "rawIdentifiersEmitted": 0,
            "duplicateRepresentationsAddedToCounts": 0,
        },
    }
    payload["rowsSha256"] = sha256_bytes(canonical_json_bytes(rows))
    return payload


def _safe_module_summary(bundle: Mapping[str, Any]) -> dict[str, Any]:
    registry = bundle["registry"]
    registry_rows = signal_registry_rows(registry)
    status_counts = Counter(str(row["status"]) for row in registry_rows)
    pathological_source = _extract_rows(
        bundle["pathological"],
        ("rows", "samples", "sampleRows", "pathologicalSamples"),
        "pathological samples",
    )
    missing = bundle["missingness"]
    cross = bundle["cross"]
    return {
        "source": bundle["source"],
        "curatorial": bundle["curatorial"],
        "missingness": {
            key: missing[key] for key in (
                "schemaVersion", "derivationVersion", "population", "taxonomy",
                "orthogonalFlags", "fieldMatrix", "stateCounts", "cooccurrences",
                "deferredFields", "invariants", "hashes", "metrics",
            ) if key in missing
        },
        "cross": {
            key: cross[key] for key in (
                "schemaVersion", "derivationVersion", "population", "policies",
                "dimensionRegistry", "pairRegistry", "tripleRegistry", "densityRows",
                "raritySummaryRows", "sourceConcentrationRows", "dimensionConcentrationRows",
                "deferredFamilies",
                "concentrationDiagnostics", "enrichmentHashes", "invariants", "hashes",
                "metrics",
            ) if key in cross
        },
        "registry": {
            "schemaVersion": registry.get(
                "schemaVersion", registry.get("schema_version", registry.get("format"))
            ),
            "derivationVersion": registry.get("derivationVersion", registry.get("derivation_version")),
            "signalCount": len(registry_rows),
            "statusCounts": dict(sorted(status_counts.items())),
            "rowsSha256": sha256_bytes(canonical_json_bytes(registry_rows)),
            "invariants": registry.get("invariants", {}),
            "deterministicReceipt": registry.get("deterministic_receipt", {}),
        },
        "pathological": {
            "schemaVersion": bundle["pathological"].get(
                "schemaVersion",
                bundle["pathological"].get(
                    "schema_version", bundle["pathological"].get("format")
                ),
            ),
            "sampleCount": len(pathological_source),
            "samplesSha256": sha256_bytes(canonical_json_bytes(pathological_source)),
            "invariants": bundle["pathological"].get("invariants", {}),
        },
    }


def build_output_files(
    derived: Mapping[str, Any],
) -> tuple[dict[str, bytes], dict[str, bytes], dict[str, Any]]:
    bundle = deterministic_bundle(derived)
    missing_rows = missingness_rows(bundle["missingness"])
    frequencies = frequency_rows(bundle["cross"])
    pairs = pair_rows(bundle["cross"])
    triples = triple_rows(bundle["cross"])
    rare = rare_rows(pairs, triples)
    signals = signal_registry_rows(bundle["registry"])
    samples = pathological_rows(
        bundle["pathological"], derived["publicObjectIds"], derived["heldObjectIds"]
    )
    row_sets = {
        "06_MISSINGNESS_CENSUS.tsv": missing_rows,
        "08_ONE_DIMENSION_FREQUENCIES.tsv": frequencies,
        "09_TWO_DIMENSION_INTERSECTIONS.tsv": pairs,
        "10_THREE_DIMENSION_INTERSECTIONS.tsv": triples,
        "11_RARE_INTERSECTION_REGISTER.tsv": rare,
        "13_EXPLORATION_SIGNAL_REGISTRY.tsv": signals,
        "15_PATHOLOGICAL_SAMPLE_REGISTER.tsv": samples,
    }
    expected_counts = {
        "06_MISSINGNESS_CENSUS.tsv": 38,
        "08_ONE_DIMENSION_FREQUENCIES.tsv": 3_364,
        "09_TWO_DIMENSION_INTERSECTIONS.tsv": 6_146,
        "10_THREE_DIMENSION_INTERSECTIONS.tsv": 2_399,
        "11_RARE_INTERSECTION_REGISTER.tsv": 4_251,
        "13_EXPLORATION_SIGNAL_REGISTRY.tsv": 64,
        "15_PATHOLOGICAL_SAMPLE_REGISTER.tsv": 15,
    }
    for filename, expected in expected_counts.items():
        if len(row_sets[filename]) != expected:
            raise GenerationError(
                f"{filename} expected {expected} rows, found {len(row_sets[filename])}"
            )
    research = {
        filename: tsv_bytes(RESEARCH_SCHEMAS[filename], row_sets[filename])
        for filename in RESEARCH_SCHEMAS
    }
    summaries = _safe_module_summary(bundle)
    structure_registry = source_curatorial_structure_registry(
        bundle["source"], bundle["curatorial"], bundle["cross"],
        bundle["structureDistributions"],
    )
    raw = {
        "exploration-source-inventory-summary.json": canonical_json_bytes(summaries["source"], pretty=True),
        "exploration-curatorial-summary.json": canonical_json_bytes(summaries["curatorial"], pretty=True),
        "exploration-source-curatorial-structure-registry.json": canonical_json_bytes(structure_registry, pretty=True),
        "exploration-missingness-summary.json": canonical_json_bytes(summaries["missingness"], pretty=True),
        "exploration-cross-dimensional-summary.json": canonical_json_bytes(summaries["cross"], pretty=True),
        "exploration-signal-registry-summary.json": canonical_json_bytes(summaries["registry"], pretty=True),
        "exploration-pathological-samples-summary.json": canonical_json_bytes(summaries["pathological"], pretty=True),
        "exploration-curatorial-support-summary.json": canonical_json_bytes(
            bundle["curatorialSupport"], pretty=True
        ),
    }
    bundle_hash = sha256_bytes(canonical_json_bytes(bundle))
    receipts = {
        f"research/{filename}": {
            "rowCount": len(row_sets[filename]),
            "columnCount": len(RESEARCH_SCHEMAS[filename]),
            "bytes": len(payload),
            "sha256": sha256_bytes(payload),
        }
        for filename, payload in research.items()
    }
    receipts.update({
        f"raw/{filename}": {
            "bytes": len(payload),
            "sha256": sha256_bytes(payload),
        }
        for filename, payload in raw.items()
    })
    generation = {
        "schemaVersion": SCHEMA_VERSION,
        "derivationVersion": DERIVATION_VERSION,
        "status": "PASS",
        "runCount": 2,
        "deterministicBundleSha256": bundle_hash,
        "population": {"publicObjectCount": PUBLIC_OBJECT_COUNT, "heldObjectsInStatistics": 0},
        "outputReceipts": dict(sorted(receipts.items())),
        "rowCounts": {filename: len(rows) for filename, rows in row_sets.items()},
        "structureRegistry": {
            "rowCount": structure_registry["rowCount"],
            "populationStateCounts": structure_registry["populationStateCounts"],
            "rowsSha256": structure_registry["rowsSha256"],
        },
        "safety": {
            "normalizedRowsEmitted": 0,
            "objectVectorsEmitted": 0,
            "heldIdentifiersEmitted": 0,
            "internalUuidsEmitted": 0,
            "urlsEmitted": 0,
            "rawFolderTokensEmitted": 0,
            "objectTitlesEmitted": 0,
            "objectPairRowsEmitted": 0,
            "pairMatrixEmitted": False,
        },
        "modelBoundary": {
            "similarityModelSelected": False,
            "rankingSelected": False,
            "probabilityModelSelected": False,
            "templateRegistryCreated": False,
            "rendererImplemented": False,
        },
    }
    raw["exploration-generation-summary.json"] = canonical_json_bytes(generation, pretty=True)
    return research, raw, generation


def validate_output_safety(
    research: Mapping[str, bytes],
    raw: Mapping[str, bytes],
) -> None:
    for filename, payload in {**research, **raw}.items():
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise GenerationError(f"{filename} is not UTF-8") from error
        if UUID_RE.search(text):
            raise GenerationError(f"{filename} exposes an internal UUID")
        if URL_RE.search(text):
            raise GenerationError(f"{filename} exposes a URL")
        if RAW_PRIVATE_ID_RE.search(text):
            raise GenerationError(f"{filename} exposes a raw private identifier")
        public_ids = PUBLIC_ID_SEARCH_RE.findall(text)
        if public_ids and filename != "15_PATHOLOGICAL_SAMPLE_REGISTER.tsv":
            raise GenerationError(f"{filename} exposes public object IDs outside sample register")
        if filename.endswith(".json"):
            value = json.loads(text)
            if not isinstance(value, Mapping):
                raise GenerationError(f"{filename} JSON root is not an object")
        if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
            raise GenerationError(f"{filename} does not have exactly one final LF")


def run_self_tests() -> dict[str, Any]:
    safe_prose = {"probe.tsv": b"value\nFolder membership is aggregate-only.\n"}
    validate_output_safety(safe_prose, {})
    rejected = 0
    for value in (
        b"value\nFOL-ABC123\n",
        b"value\nTRN-OBJ-ABC123\n",
        b"value\nhttps://unsafe.example\n",
        b"value\n123e4567-e89b-12d3-a456-426614174000\n",
    ):
        try:
            validate_output_safety({"probe.tsv": value}, {})
        except GenerationError:
            rejected += 1
    if rejected != 4:
        raise GenerationError("output safety self-test did not reject every adversary")
    return {"status": "PASS", "checks": 5, "adversariesRejected": rejected}


def run_twice() -> tuple[dict[str, bytes], dict[str, bytes], dict[str, Any]]:
    first = derive_once()
    second = derive_once()
    first_bundle = canonical_json_bytes(deterministic_bundle(first))
    second_bundle = canonical_json_bytes(deterministic_bundle(second))
    if first_bundle != second_bundle:
        raise GenerationError("two complete analysis runs produced different canonical payloads")
    first_research, first_raw, first_receipt = build_output_files(first)
    second_research, second_raw, second_receipt = build_output_files(second)
    if first_research != second_research or first_raw != second_raw:
        raise GenerationError("two complete analysis runs produced different output bytes")
    if first_receipt != second_receipt:
        raise GenerationError("two complete analysis runs produced different generation receipts")
    validate_output_safety(first_research, first_raw)
    return first_research, first_raw, first_receipt


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_bytes(payload)
    temporary.replace(path)


def write_outputs(
    research_dir: Path,
    audit_raw_dir: Path,
    research: Mapping[str, bytes],
    raw: Mapping[str, bytes],
) -> None:
    if set(research) != set(RESEARCH_SCHEMAS):
        raise GenerationError("research output set differs from the seven-file contract")
    if set(raw) != set(RAW_FILENAMES):
        raise GenerationError("audit raw output set differs from the sanitized contract")
    for filename, payload in research.items():
        _atomic_write(research_dir / filename, payload)
    for filename, payload in raw.items():
        _atomic_write(audit_raw_dir / filename, payload)


def schema_receipt() -> dict[str, Any]:
    return {
        filename: {"columns": list(columns), "columnCount": len(columns)}
        for filename, columns in RESEARCH_SCHEMAS.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-dir", type=Path, default=DEFAULT_RESEARCH_DIR)
    parser.add_argument("--audit-raw-dir", type=Path, default=DEFAULT_AUDIT_RAW_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--print-schema", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(run_self_tests(), sort_keys=True))
        return
    if args.print_schema:
        print(json.dumps(schema_receipt(), ensure_ascii=False, sort_keys=True, indent=2))
        return
    research, raw, receipt = run_twice()
    if not args.dry_run:
        write_outputs(
            args.research_dir.resolve(), args.audit_raw_dir.resolve(), research, raw
        )
    print(json.dumps({
        "status": "PASS",
        "dryRun": args.dry_run,
        "deterministicBundleSha256": receipt["deterministicBundleSha256"],
        "researchFileCount": len(research),
        "auditRawFileCount": len(raw),
        "rowCounts": receipt["rowCounts"],
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
