#!/usr/bin/env python3
"""Build the first deterministic TRACE v49 Exploration signal registry.

The registry consumes aggregate results from the cross-dimensional,
missingness, and curatorial analyses. It does not read source rows or choose a
similarity formula, weights, clustering, probabilities, templates, or a
renderer. Every registry metric carries its own denominator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "trace-exploration-signal-registry/v1"
DEFAULT_DERIVATION_VERSION = "trace-exploration-signal-registry-v1"
DIRECT_DERIVATION_VERSION = "trace-v49-normalized-public-direct-v1"

FAMILIES = (
    "GOVERNED_CONTEXT",
    "GOVERNED_TEMPORAL",
    "GOVERNED_GEOGRAPHY",
    "SOURCE_CORPUS_COMPOSITION",
    "DESCRIPTIVE_METADATA",
    "CURATORIAL_STRUCTURE",
    "MISSINGNESS_UNCERTAINTY",
    "FREQUENCY_INTERSECTION_CONCENTRATION",
)
DERIVATION_LEVELS = frozenset(
    {
        "LEVEL_A_GOVERNED_DIRECT_FEATURE",
        "LEVEL_B_DETERMINISTIC_DERIVED_STATISTIC",
        "LEVEL_C_COMPOUND_EXPLORATORY_SIGNAL",
    }
)
ALLOWED_STATUSES = frozenset(
    {
        "HIGH_POTENTIAL",
        "SUPPORTING_SIGNAL",
        "RESEARCH_ONLY",
        "NEEDS_MORE_DATA",
        "DEFER",
        "REJECT",
    }
)
REQUIRED_COLUMNS = (
    "signal_id",
    "family",
    "signal_name",
    "description",
    "input_source",
    "input_governance_state",
    "direct_or_derived",
    "derivation_level",
    "coverage",
    "cardinality",
    "missing_rate",
    "numerator_definition",
    "denominator_definition",
    "derivation_method",
    "derivation_version",
    "deterministic",
    "explainable",
    "public_safe",
    "held_risk",
    "pairwise_or_object_level",
    "expected_fanout",
    "computational_cost",
    "materialization_risk",
    "historical_relation",
    "semantic_relation",
    "known_failure_modes",
    "status",
)

UUID_PATTERN = re.compile(
    r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[1-5][0-9A-Fa-f]{3}"
    r"-[89ABab][0-9A-Fa-f]{3}-[0-9A-Fa-f]{12}(?![0-9A-Fa-f])"
)
URL_PATTERN = re.compile(r"(?:https?://|file://)", re.IGNORECASE)
RAW_ID_PATTERN = re.compile(
    r"\b(?:SURF|FOL|TRN-OBJ|TRTREE|TRBRANCH|DOS-SURF)-[A-Z0-9#_-]+\b"
)


class RegistryInputError(ValueError):
    """Raised when aggregate analysis inputs or registry rows are invalid."""


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RegistryInputError(f"{label} must be a mapping")
    return value


def _require_sequence(value: Any, label: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise RegistryInputError(f"{label} must be an array")
    return value


def _require_nonnegative_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RegistryInputError(f"{label} must be a nonnegative integer")
    return value


def _ratio(numerator: int, denominator: int, *, state: str = "OBSERVED") -> dict[str, Any]:
    numerator = _require_nonnegative_int(numerator, "ratio numerator")
    denominator = _require_nonnegative_int(denominator, "ratio denominator")
    if numerator > denominator:
        raise RegistryInputError("ratio numerator exceeds denominator")
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": numerator / denominator if denominator else 0.0,
        "state": state,
    }


def _not_applicable(denominator: int, state: str) -> dict[str, Any]:
    return {"state": state, "denominator": denominator}


def _cardinality(count: int, denominator: int, unit: str) -> dict[str, Any]:
    return {
        "count": _require_nonnegative_int(count, "cardinality count"),
        "denominator": _require_nonnegative_int(
            denominator, "cardinality denominator"
        ),
        "unit": unit,
    }


def _metric(
    *,
    coverage_numerator: int,
    denominator: int,
    cardinality_count: int | None,
    cardinality_unit: str,
    missing_numerator: int | None,
    numerator_definition: str,
    denominator_definition: str,
    coverage_state: str = "OBSERVED",
    missing_state: str = "OBSERVED",
    cardinality_state: str = "NOT_REPORTED_BY_AGGREGATE",
) -> dict[str, Any]:
    cardinality = (
        _cardinality(cardinality_count, denominator, cardinality_unit)
        if cardinality_count is not None
        else _not_applicable(denominator, cardinality_state)
    )
    missing_rate = (
        _ratio(missing_numerator, denominator, state=missing_state)
        if missing_numerator is not None
        else _not_applicable(denominator, missing_state)
    )
    return {
        "coverage": _ratio(
            coverage_numerator, denominator, state=coverage_state
        ),
        "cardinality": cardinality,
        "missing_rate": missing_rate,
        "numerator_definition": numerator_definition,
        "denominator_definition": denominator_definition,
    }


def _unselected_metric(public_count: int, state: str) -> dict[str, Any]:
    return {
        "coverage": _not_applicable(public_count, state),
        "cardinality": _not_applicable(public_count, state),
        "missing_rate": _not_applicable(public_count, state),
        "numerator_definition": "Not computed because the candidate is unselected.",
        "denominator_definition": "Authoritative public-object cohort, retained for provenance.",
    }


def _spec(
    signal_id: str,
    family: str,
    signal_name: str,
    description: str,
    metric_key: str,
    status: str,
    *,
    input_source: str,
    input_governance_state: str,
    direct_or_derived: str = "DERIVED",
    derivation_level: str = "LEVEL_B_DETERMINISTIC_DERIVED_STATISTIC",
    derivation_method: str,
    pairwise_or_object_level: str = "OBJECT_LEVEL",
    expected_fanout: str = "ONE_VALUE_PER_OBJECT",
    computational_cost: str = "LOW",
    materialization_risk: str = "LOW",
    known_failure_modes: str,
    public_safe: bool = True,
    held_risk: str = "NONE_PUBLIC_COHORT_ONLY",
    deterministic: bool = True,
    explainable: bool = True,
) -> dict[str, Any]:
    return {
        "signal_id": signal_id,
        "family": family,
        "signal_name": signal_name,
        "description": description,
        "metric_key": metric_key,
        "input_source": input_source,
        "input_governance_state": input_governance_state,
        "direct_or_derived": direct_or_derived,
        "derivation_level": derivation_level,
        "derivation_method": derivation_method,
        "deterministic": deterministic,
        "explainable": explainable,
        "public_safe": public_safe,
        "held_risk": held_risk,
        "pairwise_or_object_level": pairwise_or_object_level,
        "expected_fanout": expected_fanout,
        "computational_cost": computational_cost,
        "materialization_risk": materialization_risk,
        "historical_relation": False,
        "semantic_relation": False,
        "known_failure_modes": known_failure_modes,
        "status": status,
    }


CONTEXT_SOURCE = "Governed Context public projection"
SPACETIME_SOURCE = "Governed Spacetime public projection"
NORMALIZED_SOURCE = "Normalized public descriptive metadata"
CROSS_SOURCE = "Cross-dimensional aggregate analysis"
CURATORIAL_SOURCE = "Curatorial aggregate analysis"
MISSINGNESS_SOURCE = "Missingness and uncertainty aggregate analysis"


SPECS = (
    # Governed Context: 8
    _spec(
        "SIG-CONTEXT-MEDIUM", "GOVERNED_CONTEXT", "Medium",
        "Governed medium assignments for public objects.", "dimension:medium",
        "HIGH_POTENTIAL", input_source=CONTEXT_SOURCE,
        input_governance_state="PUBLIC_GOVERNED", direct_or_derived="DIRECT",
        derivation_level="LEVEL_A_GOVERNED_DIRECT_FEATURE",
        derivation_method="Read governed medium representations without inference.",
        expected_fanout="BOUNDED_MULTI_VALUE", known_failure_modes="Broad media can dominate counts.",
    ),
    _spec(
        "SIG-CONTEXT-THEME", "GOVERNED_CONTEXT", "Theme",
        "Governed thematic assignments for public objects.", "dimension:theme",
        "HIGH_POTENTIAL", input_source=CONTEXT_SOURCE,
        input_governance_state="PUBLIC_GOVERNED", direct_or_derived="DIRECT",
        derivation_level="LEVEL_A_GOVERNED_DIRECT_FEATURE",
        derivation_method="Read governed theme representations without inference.",
        expected_fanout="BOUNDED_MULTI_VALUE", known_failure_modes="Themes are curatorial descriptors, not historical causes.",
    ),
    _spec(
        "SIG-CONTEXT-MOVEMENT", "GOVERNED_CONTEXT", "Movement context",
        "Published movement-context availability and assignments.",
        "dimension-no-missing:movement_context", "SUPPORTING_SIGNAL",
        input_source=CONTEXT_SOURCE, input_governance_state="PUBLIC_GOVERNED",
        direct_or_derived="DIRECT", derivation_level="LEVEL_A_GOVERNED_DIRECT_FEATURE",
        derivation_method="Read governed movement-context representations.",
        expected_fanout="SPARSE_BOUNDED_MULTI_VALUE",
        known_failure_modes="No published movement context is not generic missingness.",
    ),
    _spec(
        "SIG-CONTEXT-SAME-MEDIUM", "GOVERNED_CONTEXT", "Same-medium overlap",
        "Pairwise structural overlap on at least one governed medium.",
        "dimension:medium", "HIGH_POTENTIAL", input_source=CROSS_SOURCE,
        input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="Intersect per-object governed medium sets.",
        pairwise_or_object_level="PAIRWISE", expected_fanout="POTENTIALLY_HIGH_PAIRWISE",
        computational_cost="MEDIUM", materialization_risk="HIGH",
        known_failure_modes="Shared medium does not establish relation, influence, or quality.",
    ),
    _spec(
        "SIG-CONTEXT-SAME-THEME", "GOVERNED_CONTEXT", "Same-theme overlap",
        "Pairwise structural overlap on at least one governed theme.",
        "dimension:theme", "HIGH_POTENTIAL", input_source=CROSS_SOURCE,
        input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="Intersect per-object governed theme sets.",
        pairwise_or_object_level="PAIRWISE", expected_fanout="POTENTIALLY_HIGH_PAIRWISE",
        computational_cost="MEDIUM", materialization_risk="HIGH",
        known_failure_modes="Shared theme can reflect broad cataloguing practice.",
    ),
    _spec(
        "SIG-CONTEXT-SAME-MOVEMENT", "GOVERNED_CONTEXT", "Same movement-context overlap",
        "Pairwise overlap among objects with published movement context.",
        "dimension-no-missing:movement_context", "RESEARCH_ONLY",
        input_source=CROSS_SOURCE, input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="Intersect nonempty governed movement-context sets.",
        pairwise_or_object_level="PAIRWISE", expected_fanout="SPARSE_PAIRWISE",
        computational_cost="LOW", materialization_risk="MEDIUM",
        known_failure_modes="Sparse publication coverage creates severe selection effects.",
    ),
    _spec(
        "SIG-CONTEXT-MEDIUM-THEME", "GOVERNED_CONTEXT", "Medium-theme intersection",
        "Observed public-object cells across governed medium and theme.",
        "pair:medium__theme", "HIGH_POTENTIAL", input_source=CROSS_SOURCE,
        input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="Count observed medium-theme memberships only.",
        pairwise_or_object_level="AGGREGATE_CELL", expected_fanout="OBSERVED_CELLS_ONLY",
        computational_cost="LOW", known_failure_modes="Common cells need not be representative or important.",
    ),
    _spec(
        "SIG-CONTEXT-THEME-MOVEMENT", "GOVERNED_CONTEXT", "Theme-movement intersection",
        "Observed intersections where movement context is published.",
        "pair-no-missing:theme__movement_context", "NEEDS_MORE_DATA",
        input_source=CROSS_SOURCE, input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="Count observed theme-movement cells without zero-cell expansion.",
        pairwise_or_object_level="AGGREGATE_CELL", expected_fanout="SPARSE_OBSERVED_CELLS",
        computational_cost="LOW", known_failure_modes="The small movement-covered cohort is not corpus-wide evidence.",
    ),

    # Governed Temporal: 8
    _spec(
        "SIG-TEMPORAL-DECADE", "GOVERNED_TEMPORAL", "Decade",
        "Governed period-bucket assignments.", "dimension:decade", "HIGH_POTENTIAL",
        input_source=SPACETIME_SOURCE, input_governance_state="PUBLIC_GOVERNED",
        direct_or_derived="DIRECT", derivation_level="LEVEL_A_GOVERNED_DIRECT_FEATURE",
        derivation_method="Read governed Spacetime period identifiers.",
        expected_fanout="BOUNDED_MULTI_VALUE", known_failure_modes="Ranges may span more than one decade.",
    ),
    _spec(
        "SIG-TEMPORAL-EXTENT", "GOVERNED_TEMPORAL", "Recorded temporal extent",
        "Inclusive governed start and end years.", "temporal-extent", "SUPPORTING_SIGNAL",
        input_source=SPACETIME_SOURCE, input_governance_state="PUBLIC_GOVERNED",
        direct_or_derived="DIRECT", derivation_level="LEVEL_A_GOVERNED_DIRECT_FEATURE",
        derivation_method="Read governed inclusive temporal endpoints.",
        expected_fanout="TWO_ENDPOINTS_PER_OBJECT", known_failure_modes="Recorded extent is not necessarily production duration.",
    ),
    _spec(
        "SIG-TEMPORAL-PRECISION", "GOVERNED_TEMPORAL", "Temporal precision",
        "Governed precision class for each temporal record.",
        "dimension:temporal_precision", "SUPPORTING_SIGNAL",
        input_source=SPACETIME_SOURCE, input_governance_state="PUBLIC_GOVERNED",
        direct_or_derived="DIRECT", derivation_level="LEVEL_A_GOVERNED_DIRECT_FEATURE",
        derivation_method="Read governed temporal precision.",
        known_failure_modes="Precision class is uncertainty metadata, not object importance.",
    ),
    _spec(
        "SIG-TEMPORAL-RANGE-SPAN", "GOVERNED_TEMPORAL", "Range span",
        "Inclusive year span for records governed as ranges.",
        "range-span", "SUPPORTING_SIGNAL", input_source=MISSINGNESS_SOURCE,
        input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="For range records, compute end minus start plus one.",
        expected_fanout="ONE_VALUE_WHEN_APPLICABLE",
        known_failure_modes="Non-range records are not missing this statistic; it is not applicable.",
    ),
    _spec(
        "SIG-TEMPORAL-SAME-DECADE", "GOVERNED_TEMPORAL", "Same-decade overlap",
        "Pairwise overlap on at least one governed period bucket.",
        "dimension:decade", "HIGH_POTENTIAL", input_source=CROSS_SOURCE,
        input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="Intersect governed period-bucket sets.",
        pairwise_or_object_level="PAIRWISE", expected_fanout="POTENTIALLY_HIGH_PAIRWISE",
        computational_cost="MEDIUM", materialization_risk="HIGH",
        known_failure_modes="Temporal co-occurrence is not evidence of contact or influence.",
    ),
    _spec(
        "SIG-TEMPORAL-LONG-RANGE", "GOVERNED_TEMPORAL", "Long-range diagnostic",
        "Descriptive tail diagnostic for governed temporal ranges.",
        "range-span", "RESEARCH_ONLY", input_source=MISSINGNESS_SOURCE,
        input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="Compare inclusive range spans without selecting a product threshold.",
        expected_fanout="ONE_FLAG_WHEN_APPLICABLE",
        known_failure_modes="A long catalogued range may reflect uncertainty, not longevity.",
    ),
    _spec(
        "SIG-TEMPORAL-CONCENTRATION", "GOVERNED_TEMPORAL", "Temporal concentration",
        "Distributional concentration across governed period buckets.",
        "dimension-concentration:decade", "RESEARCH_ONLY", input_source=CROSS_SOURCE,
        input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="Compute deterministic concentration diagnostics from decade counts.",
        pairwise_or_object_level="AGGREGATE", expected_fanout="ONE_CORPUS_SUMMARY",
        known_failure_modes="Archive concentration can reflect acquisition or source bias.",
    ),
    _spec(
        "SIG-TEMPORAL-DISTANCE", "GOVERNED_TEMPORAL", "Temporal distance",
        "Candidate distance between governed temporal observations.",
        "unselected", "DEFER", input_source=SPACETIME_SOURCE,
        input_governance_state="UNSELECTED_MODEL",
        derivation_level="LEVEL_C_COMPOUND_EXPLORATORY_SIGNAL",
        derivation_method="No distance or adjacency policy selected.",
        pairwise_or_object_level="PAIRWISE", expected_fanout="UNSELECTED",
        computational_cost="NOT_EVALUATED", materialization_risk="HIGH",
        known_failure_modes="Distance can be mistaken for historical proximity.", public_safe=False,
    ),

    # Governed Geography: 8
    _spec(
        "SIG-GEOGRAPHY-ASSIGNMENT", "GOVERNED_GEOGRAPHY", "Governed geography",
        "Governed geographic assignments for public objects.",
        "dimension:geography", "HIGH_POTENTIAL", input_source=SPACETIME_SOURCE,
        input_governance_state="PUBLIC_GOVERNED", direct_or_derived="DIRECT",
        derivation_level="LEVEL_A_GOVERNED_DIRECT_FEATURE",
        derivation_method="Read governed Spacetime geography identifiers.",
        expected_fanout="BOUNDED_MULTI_VALUE", known_failure_modes="Geography can describe several scopes, not a single point.",
    ),
    _spec(
        "SIG-GEOGRAPHY-CLASS", "GOVERNED_GEOGRAPHY", "Geography class",
        "Governed class of geographic assignment.", "dimension:geography_class",
        "SUPPORTING_SIGNAL", input_source=SPACETIME_SOURCE,
        input_governance_state="PUBLIC_GOVERNED", direct_or_derived="DIRECT",
        derivation_level="LEVEL_A_GOVERNED_DIRECT_FEATURE",
        derivation_method="Read governed geography class.",
        known_failure_modes="Class overlap is coarser than geographic identity.",
    ),
    _spec(
        "SIG-GEOGRAPHY-MAPPING-STATE", "GOVERNED_GEOGRAPHY", "Geography mapping state",
        "Mapped, aggregate-only, or unmapped governed state.",
        "dimension:geography_mapping_state", "SUPPORTING_SIGNAL",
        input_source=SPACETIME_SOURCE, input_governance_state="PUBLIC_GOVERNED",
        direct_or_derived="DIRECT", derivation_level="LEVEL_A_GOVERNED_DIRECT_FEATURE",
        derivation_method="Read governed mapping state.",
        known_failure_modes="Unmapped does not mean geographically absent.",
    ),
    _spec(
        "SIG-GEOGRAPHY-MULTI-REGION", "GOVERNED_GEOGRAPHY", "Multi-region incidence",
        "Deterministic flag for more than one governed geography assignment.",
        "state-flag:GEOGRAPHY:MULTI_REGION", "SUPPORTING_SIGNAL",
        input_source=MISSINGNESS_SOURCE, input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="Test governed geography assignment count greater than one.",
        known_failure_modes="Multiple assignments do not imply travel, exchange, or influence.",
    ),
    _spec(
        "SIG-GEOGRAPHY-SAME", "GOVERNED_GEOGRAPHY", "Same-geography overlap",
        "Pairwise overlap on a governed geography identifier.",
        "dimension:geography", "HIGH_POTENTIAL", input_source=CROSS_SOURCE,
        input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="Intersect governed geography sets.",
        pairwise_or_object_level="PAIRWISE", expected_fanout="POTENTIALLY_HIGH_PAIRWISE",
        computational_cost="MEDIUM", materialization_risk="HIGH",
        known_failure_modes="Shared geography is not historical contact.",
    ),
    _spec(
        "SIG-GEOGRAPHY-RARITY", "GOVERNED_GEOGRAPHY", "Region rarity",
        "Observed frequency band of governed geography values.",
        "dimension:geography", "RESEARCH_ONLY", input_source=CROSS_SOURCE,
        input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="Band observed geography counts without an importance score.",
        known_failure_modes="Rare geography can reflect cataloguing or collection bias.",
    ),
    _spec(
        "SIG-GEOGRAPHY-CONCENTRATION", "GOVERNED_GEOGRAPHY", "Geographic concentration",
        "Distributional concentration across governed geography values.",
        "dimension-concentration:geography", "RESEARCH_ONLY", input_source=CROSS_SOURCE,
        input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="Compute aggregate concentration diagnostics from observed counts.",
        pairwise_or_object_level="AGGREGATE", expected_fanout="ONE_CORPUS_SUMMARY",
        known_failure_modes="Archive density is not historical representativeness.",
    ),
    _spec(
        "SIG-GEOGRAPHY-DISTANCE", "GOVERNED_GEOGRAPHY", "Geographic distance",
        "Candidate distance or hierarchy proximity between governed geographies.",
        "unselected", "DEFER", input_source=SPACETIME_SOURCE,
        input_governance_state="UNSELECTED_MODEL",
        derivation_level="LEVEL_C_COMPOUND_EXPLORATORY_SIGNAL",
        derivation_method="No governed adjacency, hierarchy-distance, or distance policy selected.",
        pairwise_or_object_level="PAIRWISE", expected_fanout="UNSELECTED",
        computational_cost="NOT_EVALUATED", materialization_risk="HIGH",
        known_failure_modes="Map coordinates or centroid distance can be misread as historical proximity.",
        public_safe=False,
    ),

    # Source / corpus composition: 8
    _spec(
        "SIG-SOURCE-NAME", "SOURCE_CORPUS_COMPOSITION", "Source name",
        "Public-safe source attribution used for corpus composition analysis.",
        "dimension:source", "SUPPORTING_SIGNAL", input_source=NORMALIZED_SOURCE,
        input_governance_state="PUBLIC_METADATA_ANALYSIS_ONLY", direct_or_derived="DERIVED",
        derivation_level="LEVEL_B_DETERMINISTIC_DERIVED_STATISTIC",
        derivation_method="Normalize and hash public source attribution for analysis-only identity.",
        known_failure_modes="Source is not governed Context and can encode acquisition bias.",
    ),
    _spec(
        "SIG-SOURCE-FREQUENCY", "SOURCE_CORPUS_COMPOSITION", "Source frequency",
        "Public-object count per normalized source.", "dimension:source",
        "HIGH_POTENTIAL", input_source=CROSS_SOURCE,
        input_governance_state="PUBLIC_METADATA_DERIVED",
        derivation_method="Count unique public objects per source.",
        pairwise_or_object_level="AGGREGATE", expected_fanout="ONE_ROW_PER_SOURCE",
        known_failure_modes="Frequency reflects corpus composition, not source authority.",
    ),
    _spec(
        "SIG-SOURCE-SHARE", "SOURCE_CORPUS_COMPOSITION", "Source share",
        "Source frequency divided by the authoritative public denominator.",
        "dimension:source", "HIGH_POTENTIAL", input_source=CROSS_SOURCE,
        input_governance_state="PUBLIC_METADATA_DERIVED",
        derivation_method="Divide each source count by all public objects.",
        pairwise_or_object_level="AGGREGATE", expected_fanout="ONE_ROW_PER_SOURCE",
        known_failure_modes="Share does not establish source independence or representativeness.",
    ),
    _spec(
        "SIG-SOURCE-RARE", "SOURCE_CORPUS_COMPOSITION", "Rare source",
        "Descriptive lower-tail source-frequency class.", "dimension:source",
        "RESEARCH_ONLY", input_source=CROSS_SOURCE,
        input_governance_state="PUBLIC_METADATA_DERIVED",
        derivation_method="Apply frozen observed-count rarity bands.",
        known_failure_modes="Rare does not mean important, obscure, or historically absent.",
    ),
    _spec(
        "SIG-SOURCE-DOMINANT", "SOURCE_CORPUS_COMPOSITION", "Dominant source incidence",
        "Largest observed source count and assignment share.", "dimension-concentration:source",
        "SUPPORTING_SIGNAL", input_source=CROSS_SOURCE,
        input_governance_state="PUBLIC_METADATA_DERIVED",
        derivation_method="Select the maximum source count with deterministic tie handling.",
        pairwise_or_object_level="AGGREGATE", expected_fanout="ONE_CORPUS_SUMMARY",
        known_failure_modes="Dominance can be a data-source artifact.",
    ),
    _spec(
        "SIG-SOURCE-SAME", "SOURCE_CORPUS_COMPOSITION", "Same-source overlap",
        "Pairwise equality of normalized source attribution.", "dimension:source",
        "RESEARCH_ONLY", input_source=CROSS_SOURCE,
        input_governance_state="PUBLIC_METADATA_DERIVED",
        derivation_method="Compare normalized source identifiers for equality.",
        pairwise_or_object_level="PAIRWISE", expected_fanout="POTENTIALLY_HIGH_PAIRWISE",
        computational_cost="MEDIUM", materialization_risk="HIGH",
        known_failure_modes="Same source is not evidence that objects are historically related.",
    ),
    _spec(
        "SIG-SOURCE-CONCENTRATION", "SOURCE_CORPUS_COMPOSITION", "Source concentration",
        "Top shares, HHI, and entropy over public source counts.",
        "dimension-concentration:source", "HIGH_POTENTIAL", input_source=CROSS_SOURCE,
        input_governance_state="PUBLIC_METADATA_DERIVED",
        derivation_method="Compute deterministic top-k, HHI, and entropy diagnostics.",
        pairwise_or_object_level="AGGREGATE", expected_fanout="ONE_GLOBAL_AND_BOUNDED_SUBSET_ROWS",
        known_failure_modes="Concentration describes this corpus, not the historical field.",
    ),
    _spec(
        "SIG-SOURCE-DIVERSITY", "SOURCE_CORPUS_COMPOSITION", "Source diversity candidate",
        "Candidate compound interpretation of distinct-source and entropy diagnostics.",
        "dimension-concentration:source", "NEEDS_MORE_DATA", input_source=CROSS_SOURCE,
        input_governance_state="PUBLIC_METADATA_DERIVED",
        derivation_level="LEVEL_C_COMPOUND_EXPLORATORY_SIGNAL",
        derivation_method="Inventory component diagnostics; do not combine into a score.",
        pairwise_or_object_level="AGGREGATE", expected_fanout="ONE_CORPUS_SUMMARY",
        known_failure_modes="A single diversity score can hide source-size imbalance.",
    ),

    # Descriptive metadata: 6
    _spec(
        "SIG-DESCRIPTIVE-CREATOR", "DESCRIPTIVE_METADATA", "Creator attribution",
        "Normalized public creator attribution for analysis only.",
        "dimension:creator", "RESEARCH_ONLY", input_source=NORMALIZED_SOURCE,
        input_governance_state="PUBLIC_METADATA_ANALYSIS_ONLY", direct_or_derived="DERIVED",
        derivation_level="LEVEL_B_DETERMINISTIC_DERIVED_STATISTIC",
        derivation_method="Normalize and hash public creator attribution for analysis-only identity.",
        known_failure_modes="High cardinality and explicit unknown states complicate comparison.",
    ),
    _spec(
        "SIG-DESCRIPTIVE-OBJECT-TYPE", "DESCRIPTIVE_METADATA", "Object type",
        "Normalized public object type for descriptive analysis.",
        "dimension:object_type", "SUPPORTING_SIGNAL", input_source=NORMALIZED_SOURCE,
        input_governance_state="PUBLIC_METADATA_ANALYSIS_ONLY", direct_or_derived="DERIVED",
        derivation_level="LEVEL_B_DETERMINISTIC_DERIVED_STATISTIC",
        derivation_method="Normalize and hash public object type for analysis-only identity.",
        known_failure_modes="Object-type granularity can vary by source.",
    ),
    _spec(
        "SIG-DESCRIPTIVE-SAME-CREATOR", "DESCRIPTIVE_METADATA", "Same-creator overlap",
        "Pairwise equality of normalized creator attribution.", "dimension:creator",
        "RESEARCH_ONLY", input_source=CROSS_SOURCE,
        input_governance_state="PUBLIC_METADATA_DERIVED",
        derivation_method="Compare normalized creator identifiers for equality.",
        pairwise_or_object_level="PAIRWISE", expected_fanout="HIGH_CARDINALITY_PAIRWISE",
        computational_cost="MEDIUM", materialization_risk="HIGH",
        known_failure_modes="Unknown and role-qualified attribution must not collapse together.",
    ),
    _spec(
        "SIG-DESCRIPTIVE-OBJECT-TYPE-MEDIUM", "DESCRIPTIVE_METADATA", "Object-type-medium intersection",
        "Observed public cells across object type and medium.",
        "pair:object_type__medium", "SUPPORTING_SIGNAL", input_source=CROSS_SOURCE,
        input_governance_state="MIXED_PUBLIC_METADATA_GOVERNED_DERIVED",
        derivation_method="Count observed object-type-medium cells.",
        pairwise_or_object_level="AGGREGATE_CELL", expected_fanout="OBSERVED_CELLS_ONLY",
        known_failure_modes="Taxonomic conventions can create artificial intersections.",
    ),
    _spec(
        "SIG-DESCRIPTIVE-CREATOR-MEDIUM", "DESCRIPTIVE_METADATA", "Creator-medium intersection",
        "Observed public cells across creator attribution and governed medium.",
        "pair:creator__medium", "RESEARCH_ONLY", input_source=CROSS_SOURCE,
        input_governance_state="MIXED_PUBLIC_METADATA_GOVERNED_DERIVED",
        derivation_method="Count observed creator-medium cells with no zero-cell expansion.",
        pairwise_or_object_level="AGGREGATE_CELL", expected_fanout="HIGH_CARDINALITY_OBSERVED_CELLS",
        computational_cost="MEDIUM", materialization_risk="MEDIUM",
        known_failure_modes="High cardinality and unknown attribution can dominate the tail.",
    ),
    _spec(
        "SIG-DESCRIPTIVE-CREATOR-INTENT", "DESCRIPTIVE_METADATA", "Creator-intent inference",
        "Attempt to infer creator intent from descriptive co-occurrence.",
        "unselected", "REJECT", input_source=NORMALIZED_SOURCE,
        input_governance_state="UNSUPPORTED_INFERENCE",
        derivation_level="LEVEL_C_COMPOUND_EXPLORATORY_SIGNAL",
        derivation_method="No derivation permitted from current evidence.",
        expected_fanout="UNSELECTED", computational_cost="NOT_EVALUATED",
        materialization_risk="PROHIBITED",
        known_failure_modes="Descriptive metadata cannot establish intent.", public_safe=False,
        deterministic=False,
    ),

    # Curatorial structure: 9
    _spec(
        "SIG-CURATORIAL-MEMBERSHIP", "CURATORIAL_STRUCTURE", "Curated-container membership",
        "Analysis-only project-curated membership substrate.",
        "curatorial-membership", "RESEARCH_ONLY", input_source=CURATORIAL_SOURCE,
        input_governance_state="INTERNAL_AGGREGATE_ANALYSIS_ONLY",
        derivation_method="Reconcile public membership aggregates against the authoritative ledger.",
        expected_fanout="BOUNDED_MULTI_VALUE", held_risk="AGGREGATE_ONLY_SEPARATION_REQUIRED",
        known_failure_modes="Raw container identities are unsafe and curation is not history.",
    ),
    _spec(
        "SIG-CURATORIAL-CONTAINER-TYPE", "CURATORIAL_STRUCTURE", "Curated-container type",
        "Observed type of project-curated container.",
        "curatorial-type", "SUPPORTING_SIGNAL", input_source=CURATORIAL_SOURCE,
        input_governance_state="INTERNAL_AGGREGATE_ANALYSIS_ONLY",
        derivation_method="Count sanitized observed container types.",
        expected_fanout="BOUNDED_MULTI_VALUE", held_risk="AGGREGATE_ONLY_SEPARATION_REQUIRED",
        known_failure_modes="Underlying raw memberships remain separate from governed Context terms.",
    ),
    _spec(
        "SIG-CURATORIAL-MEMBERSHIP-COUNT", "CURATORIAL_STRUCTURE", "Membership count per object",
        "Number of curated containers assigned to a public object.",
        "curatorial-degree", "HIGH_POTENTIAL", input_source=CURATORIAL_SOURCE,
        input_governance_state="INTERNAL_AGGREGATE_DERIVED",
        derivation_method="Count unique public container memberships per object.",
        known_failure_modes="More memberships can reflect cataloguing density, not importance.",
    ),
    _spec(
        "SIG-CURATORIAL-SHARED-COUNT", "CURATORIAL_STRUCTURE", "Shared-container count",
        "Exact number of curated containers shared by a public-object pair.",
        "curatorial-shared", "HIGH_POTENTIAL", input_source=CURATORIAL_SOURCE,
        input_governance_state="INTERNAL_AGGREGATE_DERIVED",
        derivation_method="Use inverted membership bitsets and exact shared-count thresholds.",
        pairwise_or_object_level="PAIRWISE", expected_fanout="VERY_HIGH_PAIRWISE",
        computational_cost="MEDIUM", materialization_risk="HIGH",
        held_risk="AGGREGATE_ONLY_SEPARATION_REQUIRED",
        known_failure_modes="Shared curation is structural overlap, not historical relation.",
    ),
    _spec(
        "SIG-CURATORIAL-FANOUT", "CURATORIAL_STRUCTURE", "Co-membership fanout thresholds",
        "Per-object count of public neighbors sharing at least one, two, or three containers.",
        "curatorial-fanout", "HIGH_POTENTIAL", input_source=CURATORIAL_SOURCE,
        input_governance_state="INTERNAL_AGGREGATE_DERIVED",
        derivation_method="Derive exact threshold fanout with container bitsets.",
        expected_fanout="VERY_HIGH_PAIRWISE", computational_cost="MEDIUM",
        materialization_risk="HIGH", held_risk="AGGREGATE_ONLY_SEPARATION_REQUIRED",
        known_failure_modes="Large broad containers create pair explosion.",
    ),
    _spec(
        "SIG-CURATORIAL-JACCARD", "CURATORIAL_STRUCTURE", "Curated-set Jaccard diagnostic",
        "Descriptive Jaccard of curated-container sets.",
        "curatorial-jaccard", "RESEARCH_ONLY", input_source=CURATORIAL_SOURCE,
        input_governance_state="INTERNAL_AGGREGATE_DERIVED",
        derivation_method="Divide shared-container count by set-union size.",
        pairwise_or_object_level="PAIRWISE", expected_fanout="VERY_HIGH_PAIRWISE",
        computational_cost="MEDIUM", materialization_risk="HIGH",
        held_risk="AGGREGATE_ONLY_SEPARATION_REQUIRED",
        known_failure_modes="Jaccard is a benchmark diagnostic, not the selected similarity metric.",
    ),
    _spec(
        "SIG-CURATORIAL-SUPPORT", "CURATORIAL_STRUCTURE", "Curated-container support concentration",
        "Distributional concentration of unique public-object container memberships.",
        "dimension-concentration:curated_container", "HIGH_POTENTIAL", input_source=CROSS_SOURCE,
        input_governance_state="ANALYSIS_ONLY_CURATORIAL_DERIVED",
        derivation_method="Compute deterministic top-k, HHI, and entropy over unique per-object memberships.",
        pairwise_or_object_level="AGGREGATE", expected_fanout="ONE_CORPUS_SUMMARY",
        held_risk="AGGREGATE_ONLY_SEPARATION_REQUIRED",
        known_failure_modes="Concentration can reflect broad project curation, not historical importance.",
    ),
    _spec(
        "SIG-CURATORIAL-AFFINITY", "CURATORIAL_STRUCTURE", "Curatorial affinity score",
        "Candidate compound score over curatorial diagnostics.",
        "unselected", "DEFER", input_source=CURATORIAL_SOURCE,
        input_governance_state="UNSELECTED_MODEL",
        derivation_level="LEVEL_C_COMPOUND_EXPLORATORY_SIGNAL",
        derivation_method="No formula, weights, ranking, or top-k policy selected.",
        pairwise_or_object_level="PAIRWISE", expected_fanout="UNSELECTED",
        computational_cost="NOT_EVALUATED", materialization_risk="HIGH",
        held_risk="AGGREGATE_ONLY_SEPARATION_REQUIRED",
        known_failure_modes="A score could hide broad-container dominance and imply relation.",
        public_safe=False,
    ),
    _spec(
        "SIG-CURATORIAL-HISTORICAL-RELATION", "CURATORIAL_STRUCTURE", "Historical relation from curation",
        "Attempt to reinterpret project-curated overlap as historical relation.",
        "unselected", "REJECT", input_source=CURATORIAL_SOURCE,
        input_governance_state="UNSUPPORTED_INFERENCE",
        derivation_level="LEVEL_C_COMPOUND_EXPLORATORY_SIGNAL",
        derivation_method="Explicitly prohibited by the Exploration boundary.",
        pairwise_or_object_level="PAIRWISE", expected_fanout="UNSELECTED",
        computational_cost="NOT_EVALUATED", materialization_risk="PROHIBITED",
        held_risk="HIGH", known_failure_modes="Curation cannot establish historical relation.",
        public_safe=False, deterministic=False,
    ),

    # Missingness / uncertainty: 8
    _spec(
        "SIG-MISSINGNESS-MOVEMENT-AVAILABILITY", "MISSINGNESS_UNCERTAINTY", "Movement-context availability",
        "Observed versus no-published-movement-context classification.",
        "field:movement_context", "SUPPORTING_SIGNAL", input_source=MISSINGNESS_SOURCE,
        input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="Classify governed movement-context availability without generic missingness.",
        known_failure_modes="No published context must not be labelled missing movement.",
    ),
    _spec(
        "SIG-MISSINGNESS-TEMPORAL", "MISSINGNESS_UNCERTAINTY", "Temporal uncertainty class",
        "Observed precision, approximate, range, or supported unknown state.",
        "field:temporal_precision", "SUPPORTING_SIGNAL", input_source=MISSINGNESS_SOURCE,
        input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="Preserve governed temporal precision classes.",
        known_failure_modes="Approximate and range are not generic null missingness.",
    ),
    _spec(
        "SIG-MISSINGNESS-GEOGRAPHY-MAPPING", "MISSINGNESS_UNCERTAINTY", "Geography mapping uncertainty",
        "Mapped, aggregate-only, and unmapped classification.",
        "field:geography_mapping_state", "SUPPORTING_SIGNAL",
        input_source=MISSINGNESS_SOURCE, input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="Preserve governed geography mapping states.",
        known_failure_modes="Aggregate-only and unmapped do not mean geographic absence.",
    ),
    _spec(
        "SIG-MISSINGNESS-GEOGRAPHY-QUALIFIED", "MISSINGNESS_UNCERTAINTY", "Geography qualification flag",
        "Whether a governed geography carries explicit qualification.",
        "state-flag:GEOGRAPHY:QUALIFIED", "SUPPORTING_SIGNAL",
        input_source=MISSINGNESS_SOURCE, input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="Read the explicit governed qualification flag.",
        known_failure_modes="Qualification is context, not a scalar confidence penalty.",
    ),
    _spec(
        "SIG-MISSINGNESS-CREATOR", "MISSINGNESS_UNCERTAINTY", "Creator attribution state",
        "Observed, unknown, or role-qualified unknown creator attribution.",
        "field:creator", "RESEARCH_ONLY", input_source=MISSINGNESS_SOURCE,
        input_governance_state="PUBLIC_METADATA_DERIVED",
        derivation_method="Classify explicit public attribution text with bounded rules.",
        known_failure_modes="Unknown attribution is not creator absence from history.",
    ),
    _spec(
        "SIG-MISSINGNESS-COOCCURRENCE", "MISSINGNESS_UNCERTAINTY", "Uncertainty-state co-occurrence",
        "Observed intersections among supported uncertainty states.",
        "missingness-cooccurrence", "RESEARCH_ONLY", input_source=MISSINGNESS_SOURCE,
        input_governance_state="MIXED_PUBLIC_DERIVED",
        derivation_method="Count observed state intersections without causal inference.",
        pairwise_or_object_level="AGGREGATE_CELL", expected_fanout="OBSERVED_STATE_PAIRS_ONLY",
        known_failure_modes="Co-occurrence does not identify a cause or common mechanism.",
    ),
    _spec(
        "SIG-MISSINGNESS-SINGLE-SCORE", "MISSINGNESS_UNCERTAINTY", "Single uncertainty score",
        "Attempt to compress orthogonal uncertainty states into one score.",
        "unselected", "REJECT", input_source=MISSINGNESS_SOURCE,
        input_governance_state="UNSUPPORTED_INFERENCE",
        derivation_level="LEVEL_C_COMPOUND_EXPLORATORY_SIGNAL",
        derivation_method="Explicitly prohibited; retain the state vector.",
        expected_fanout="UNSELECTED", computational_cost="NOT_EVALUATED",
        materialization_risk="PROHIBITED",
        known_failure_modes="A scalar erases not-applicable and qualified distinctions.",
        public_safe=False, deterministic=False,
    ),
    _spec(
        "SIG-MISSINGNESS-RIGHTS-DELIVERY", "MISSINGNESS_UNCERTAINTY", "Rights and delivery state",
        "Candidate public-safe rights or image-delivery diagnostic.",
        "unselected", "DEFER", input_source="Internal source diagnostics",
        input_governance_state="NOT_GOVERNED",
        derivation_level="LEVEL_C_COMPOUND_EXPLORATORY_SIGNAL",
        derivation_method="No governed public projection is available.",
        expected_fanout="UNSELECTED", computational_cost="NOT_EVALUATED",
        materialization_risk="HIGH", held_risk="HIGH",
        known_failure_modes="Internal delivery states can expose restricted workflow information.",
        public_safe=False,
    ),

    # Frequency / intersection / concentration: 9
    _spec(
        "SIG-FREQUENCY-ONE-DIMENSION", "FREQUENCY_INTERSECTION_CONCENTRATION", "One-dimensional frequency",
        "Observed value counts and support rates for usable dimensions.",
        "cross-frequency", "HIGH_POTENTIAL", input_source=CROSS_SOURCE,
        input_governance_state="MIXED_GOVERNED_CLASSIFIED_DERIVED",
        derivation_method="Count unique public-object membership per observed value.",
        pairwise_or_object_level="AGGREGATE_CELL", expected_fanout="ONE_ROW_PER_OBSERVED_VALUE",
        known_failure_modes="Frequency does not measure importance or quality.",
    ),
    _spec(
        "SIG-FREQUENCY-RARITY-BAND", "FREQUENCY_INTERSECTION_CONCENTRATION", "Observed rarity band",
        "Frozen descriptive count bands over observed cells.",
        "cross-rarity", "SUPPORTING_SIGNAL", input_source=CROSS_SOURCE,
        input_governance_state="MIXED_GOVERNED_CLASSIFIED_DERIVED",
        derivation_method="Assign deterministic bands from observed positive counts.",
        pairwise_or_object_level="AGGREGATE_CELL", expected_fanout="ONE_BAND_PER_OBSERVED_CELL",
        known_failure_modes="Rare does not imply important or historically exceptional.",
    ),
    _spec(
        "SIG-INTERSECTION-MEDIUM-THEME", "FREQUENCY_INTERSECTION_CONCENTRATION", "Medium-theme observed support",
        "Count and support rate for observed medium-theme cells.",
        "pair:medium__theme", "HIGH_POTENTIAL", input_source=CROSS_SOURCE,
        input_governance_state="PUBLIC_GOVERNED_DERIVED",
        derivation_method="Emit observed cells only with public and joint-observable denominators.",
        pairwise_or_object_level="AGGREGATE_CELL", expected_fanout="OBSERVED_CELLS_ONLY",
        known_failure_modes="Cell support is descriptive and not a recommendation score.",
    ),
    _spec(
        "SIG-INTERSECTION-PAIR-SUPPORT", "FREQUENCY_INTERSECTION_CONCENTRATION", "Observed pair support",
        "Observed support across the bounded pair registry.",
        "cross-pairs", "HIGH_POTENTIAL", input_source=CROSS_SOURCE,
        input_governance_state="MIXED_GOVERNED_CLASSIFIED_DERIVED",
        derivation_method="Count observed pair cells without Cartesian zero rows.",
        pairwise_or_object_level="AGGREGATE_CELL", expected_fanout="BOUNDED_PAIR_REGISTRY",
        computational_cost="MEDIUM", materialization_risk="MEDIUM",
        known_failure_modes="Different pair specifications have different observable cohorts.",
    ),
    _spec(
        "SIG-INTERSECTION-CONDITIONAL-LIFT", "FREQUENCY_INTERSECTION_CONCENTRATION", "Conditional and lift diagnostics",
        "P(A|B), P(B|A), and lift retained only as analysis diagnostics.",
        "cross-pairs", "RESEARCH_ONLY", input_source=CROSS_SOURCE,
        input_governance_state="MIXED_GOVERNED_CLASSIFIED_DERIVED",
        derivation_method="Derive conditional observed rates and lift with explicit marginals.",
        pairwise_or_object_level="AGGREGATE_CELL", expected_fanout="BOUNDED_PAIR_REGISTRY",
        computational_cost="MEDIUM", materialization_risk="MEDIUM",
        known_failure_modes="Lift is not calibrated probability, causality, or historical relation.",
    ),
    _spec(
        "SIG-INTERSECTION-BOUNDED-TRIPLE", "FREQUENCY_INTERSECTION_CONCENTRATION", "Bounded three-way support",
        "Observed cells for the frozen high-value triple registry.",
        "cross-triples", "RESEARCH_ONLY", input_source=CROSS_SOURCE,
        input_governance_state="MIXED_GOVERNED_CLASSIFIED_DERIVED",
        derivation_level="LEVEL_C_COMPOUND_EXPLORATORY_SIGNAL",
        derivation_method="Count only the frozen bounded triple specifications.",
        pairwise_or_object_level="AGGREGATE_CELL", expected_fanout="BOUNDED_TRIPLE_REGISTRY",
        computational_cost="MEDIUM", materialization_risk="MEDIUM",
        known_failure_modes="Sparse triples are vulnerable to tiny-cell overinterpretation.",
    ),
    _spec(
        "SIG-INTERSECTION-RARE-MULTI", "FREQUENCY_INTERSECTION_CONCENTRATION", "Rare multi-dimensional intersection",
        "Observed low-count pair or bounded-triple cell candidate.",
        "cross-rare", "HIGH_POTENTIAL", input_source=CROSS_SOURCE,
        input_governance_state="MIXED_GOVERNED_CLASSIFIED_DERIVED",
        derivation_level="LEVEL_C_COMPOUND_EXPLORATORY_SIGNAL",
        derivation_method="Select eligible observed pair and bounded-triple cells within the frozen rarity-count ceiling.",
        pairwise_or_object_level="AGGREGATE_CELL", expected_fanout="OBSERVED_RARE_CELLS_ONLY",
        computational_cost="MEDIUM", materialization_risk="MEDIUM",
        known_failure_modes="Rare is descriptive only and does not imply significance.",
    ),
    _spec(
        "SIG-MODEL-CLUSTER", "FREQUENCY_INTERSECTION_CONCENTRATION", "Cluster candidate",
        "Candidate clustering over multiple Exploration signals.",
        "unselected", "DEFER", input_source="Exploration signal registry",
        input_governance_state="UNSELECTED_MODEL",
        derivation_level="LEVEL_C_COMPOUND_EXPLORATORY_SIGNAL",
        derivation_method="No clustering method, features, scale, or validation selected.",
        expected_fanout="UNSELECTED", computational_cost="NOT_EVALUATED",
        materialization_risk="HIGH",
        known_failure_modes="Clusters can falsely imply canonical groups or historical communities.",
        public_safe=False,
    ),
    _spec(
        "SIG-MODEL-RELATION-PROBABILITY", "FREQUENCY_INTERSECTION_CONCENTRATION", "Relation probability",
        "Attempt to assign calibrated relation probability without a model.",
        "unselected", "REJECT", input_source="Exploration signal registry",
        input_governance_state="UNSUPPORTED_INFERENCE",
        derivation_level="LEVEL_C_COMPOUND_EXPLORATORY_SIGNAL",
        derivation_method="No calibrated probabilistic model exists.",
        expected_fanout="UNSELECTED", computational_cost="NOT_EVALUATED",
        materialization_risk="PROHIBITED",
        known_failure_modes="Uncalibrated percentages would misstate evidence and relation.",
        public_safe=False, deterministic=False,
    ),
)


EXPECTED_STATUS_COUNTS = {
    "HIGH_POTENTIAL": 20,
    "SUPPORTING_SIGNAL": 17,
    "RESEARCH_ONLY": 16,
    "NEEDS_MORE_DATA": 2,
    "DEFER": 5,
    "REJECT": 4,
}

DIMENSION_CONCENTRATION_CONTRACT = {
    "source": {
        "family": "SOURCE",
        "governanceState": "PUBLIC_METADATA_DERIVED",
    },
    "decade": {
        "family": "TEMPORAL",
        "governanceState": "PUBLIC_GOVERNED_DERIVED",
    },
    "geography": {
        "family": "GEOGRAPHIC",
        "governanceState": "PUBLIC_GOVERNED_DERIVED",
    },
    "curated_container": {
        "family": "CURATORIAL",
        "governanceState": "ANALYSIS_ONLY_CURATORIAL_DERIVED",
    },
}


def _indexes(
    cross: Mapping[str, Any], missingness: Mapping[str, Any]
) -> dict[str, Any]:
    frequency_rows = _require_sequence(cross.get("frequencyRows"), "frequencyRows")
    frequency: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for raw_row in frequency_rows:
        row = _require_mapping(raw_row, "frequency row")
        frequency[str(row.get("dimension"))].append(row)

    density: dict[str, Mapping[str, Any]] = {}
    for raw_row in _require_sequence(cross.get("densityRows"), "densityRows"):
        row = _require_mapping(raw_row, "density row")
        density[str(row.get("specId"))] = row

    fields: dict[str, Mapping[str, Any]] = {}
    for raw_row in _require_sequence(missingness.get("fieldMatrix"), "fieldMatrix"):
        row = _require_mapping(raw_row, "field matrix row")
        fields[str(row.get("field"))] = row

    dimension_concentration: dict[str, Mapping[str, Any]] = {}
    for raw_row in _require_sequence(
        cross.get("dimensionConcentrationRows"), "dimensionConcentrationRows"
    ):
        row = _require_mapping(raw_row, "dimension concentration row")
        dimension = str(row.get("dimension"))
        if dimension in dimension_concentration:
            raise RegistryInputError(
                f"duplicate dimension concentration row: {dimension}"
            )
        dimension_concentration[dimension] = row
    if set(dimension_concentration) != set(DIMENSION_CONCENTRATION_CONTRACT):
        raise RegistryInputError(
            "dimension concentration rows must contain exactly source, decade, "
            "geography, and curated_container"
        )
    return {
        "frequency": frequency,
        "density": density,
        "fields": fields,
        "dimension_concentration": dimension_concentration,
    }


def _require_finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RegistryInputError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise RegistryInputError(f"{label} must be finite")
    return result


def _dimension_concentration_metric(
    dimension: str,
    indexes: Mapping[str, Any],
    public_count: int,
) -> dict[str, Any]:
    contract = DIMENSION_CONCENTRATION_CONTRACT.get(dimension)
    if contract is None:
        raise RegistryInputError(f"unknown concentration dimension: {dimension}")
    row = _require_mapping(
        indexes["dimension_concentration"].get(dimension),
        f"{dimension} concentration row",
    )
    if row.get("family") != contract["family"]:
        raise RegistryInputError(f"{dimension} concentration family conflicts")
    if row.get("governanceState") != contract["governanceState"]:
        raise RegistryInputError(f"{dimension} concentration governance conflicts")
    if row.get("membershipPolicy") != "UNIQUE_PER_OBJECT_VALUE_MEMBERSHIP":
        raise RegistryInputError(f"{dimension} concentration membership policy conflicts")
    if row.get("shareDenominatorSemantics") != "UNIQUE_OBJECT_VALUE_ASSIGNMENTS":
        raise RegistryInputError(f"{dimension} concentration share denominator conflicts")
    if row.get("eligibleDenominatorSemantics") != "AUTHORITATIVE_PUBLIC_OBJECTS":
        raise RegistryInputError(f"{dimension} concentration eligible denominator conflicts")
    if row.get("diagnosticStatus") != "ANALYSIS_DIAGNOSTIC_NOT_A_RELATION":
        raise RegistryInputError(f"{dimension} concentration is not diagnostic-only")
    if (
        row.get("deterministic") is not True
        or row.get("historicalRelation") is not False
        or row.get("semanticRelation") is not False
    ):
        raise RegistryInputError(f"{dimension} concentration semantic boundary conflicts")

    eligible = _require_nonnegative_int(
        row.get("eligibleDenominator"), f"{dimension}.eligibleDenominator"
    )
    observed = _require_nonnegative_int(
        row.get("observedObjectCount"), f"{dimension}.observedObjectCount"
    )
    unassigned = _require_nonnegative_int(
        row.get("unassignedObjectCount"), f"{dimension}.unassignedObjectCount"
    )
    assignments = _require_nonnegative_int(
        row.get("assignmentCount"), f"{dimension}.assignmentCount"
    )
    assignment_denominator = _require_nonnegative_int(
        row.get("assignmentDenominator"), f"{dimension}.assignmentDenominator"
    )
    distinct = _require_nonnegative_int(
        row.get("distinctValueCount"), f"{dimension}.distinctValueCount"
    )
    top1_count = _require_nonnegative_int(
        row.get("top1AssignmentCount"), f"{dimension}.top1AssignmentCount"
    )
    top5_count = _require_nonnegative_int(
        row.get("top5AssignmentCount"), f"{dimension}.top5AssignmentCount"
    )
    if eligible != public_count or observed + unassigned != eligible:
        raise RegistryInputError(f"{dimension} concentration eligible coverage conflicts")
    if assignment_denominator != assignments or assignments < observed:
        raise RegistryInputError(f"{dimension} concentration assignment denominator conflicts")
    if not 0 <= top1_count <= top5_count <= assignments:
        raise RegistryInputError(f"{dimension} concentration top-k counts conflict")
    if (distinct == 0) != (assignments == 0) or distinct > assignments:
        raise RegistryInputError(f"{dimension} concentration cardinality conflicts")

    top1_share = _require_finite_number(row.get("top1Share"), f"{dimension}.top1Share")
    top5_share = _require_finite_number(row.get("top5Share"), f"{dimension}.top5Share")
    hhi = _require_finite_number(row.get("hhi"), f"{dimension}.hhi")
    entropy = _require_finite_number(
        row.get("shannonEntropyNats"), f"{dimension}.shannonEntropyNats"
    )
    normalized_entropy = _require_finite_number(
        row.get("normalizedEntropy"), f"{dimension}.normalizedEntropy"
    )
    expected_top1 = top1_count / assignments if assignments else 0.0
    expected_top5 = top5_count / assignments if assignments else 0.0
    if abs(top1_share - expected_top1) > 1e-12:
        raise RegistryInputError(f"{dimension} top-1 share conflicts with assignments")
    if abs(top5_share - expected_top5) > 1e-12:
        raise RegistryInputError(f"{dimension} top-5 share conflicts with assignments")
    tolerance = 1e-12
    if not (
        -tolerance <= hhi <= 1.0 + tolerance
        and entropy >= -tolerance
        and -tolerance <= normalized_entropy <= 1.0 + tolerance
    ):
        raise RegistryInputError(f"{dimension} concentration metric range conflicts")

    receipt_sha = row.get("receiptSha256")
    if not isinstance(receipt_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", receipt_sha):
        raise RegistryInputError(f"{dimension} concentration receipt SHA is invalid")
    receipt_payload = {key: value for key, value in row.items() if key != "receiptSha256"}
    if sha256_json(receipt_payload) != receipt_sha:
        raise RegistryInputError(f"{dimension} concentration receipt SHA conflicts")

    metric = _metric(
        coverage_numerator=observed,
        denominator=eligible,
        cardinality_count=distinct,
        cardinality_unit="observed_distinct_values_per_unique_assignment_denominator",
        missing_numerator=unassigned,
        numerator_definition=(
            f"Public objects with at least one unique {dimension} assignment."
        ),
        denominator_definition=(
            "Coverage and missingness use all authoritative public objects; "
            f"concentration shares use {assignments} unique object-value assignments."
        ),
    )
    metric["coverage"].update({
        "assignmentCount": assignments,
        "assignmentDenominator": assignment_denominator,
        "membershipPolicy": row["membershipPolicy"],
        "dimensionConcentrationReceiptSha256": receipt_sha,
    })
    metric["cardinality"].update({
        "denominator": assignment_denominator,
        "top1AssignmentCount": top1_count,
        "top1Share": top1_share,
        "top5AssignmentCount": top5_count,
        "top5Share": top5_share,
        "hhi": hhi,
        "shannonEntropyNats": entropy,
        "normalizedEntropy": normalized_entropy,
        "shareDenominator": assignment_denominator,
        "governanceState": row["governanceState"],
        "diagnosticStatus": row["diagnosticStatus"],
        "dimensionConcentrationReceiptSha256": receipt_sha,
    })
    metric["missing_rate"]["dimensionConcentrationReceiptSha256"] = receipt_sha
    return metric


def _dimension_metric(
    dimension: str,
    indexes: Mapping[str, Any],
    public_count: int,
    *,
    missing_is_not_applicable: bool = False,
) -> dict[str, Any]:
    rows = indexes["frequency"].get(dimension, [])
    if not rows:
        raise RegistryInputError(f"frequency rows are missing dimension {dimension!r}")
    observed_values = {int(row["observedObjectDenominator"]) for row in rows}
    eligible_values = {int(row["eligibleDenominator"]) for row in rows}
    if len(observed_values) != 1 or eligible_values != {public_count}:
        raise RegistryInputError(f"dimension {dimension!r} denominators conflict")
    observed = next(iter(observed_values))
    missing = None if missing_is_not_applicable else public_count - observed
    missing_state = (
        "NO_GENERIC_MISSINGNESS; UNPUBLISHED IS NOT MISSING"
        if missing_is_not_applicable
        else "OBSERVED"
    )
    return _metric(
        coverage_numerator=observed,
        denominator=public_count,
        cardinality_count=len(rows),
        cardinality_unit="observed_distinct_values",
        missing_numerator=missing,
        missing_state=missing_state,
        numerator_definition=f"Public objects with at least one observed {dimension} value.",
        denominator_definition="All authoritative public objects.",
    )


def _pair_metric(
    spec_id: str,
    indexes: Mapping[str, Any],
    public_count: int,
    *,
    missing_is_not_applicable: bool = False,
) -> dict[str, Any]:
    row = indexes["density"].get(spec_id)
    if row is None:
        raise RegistryInputError(f"density row is missing pair {spec_id!r}")
    observed = int(row["jointObservableObjectCount"])
    if int(row["eligibleDenominator"]) != public_count:
        raise RegistryInputError(f"pair {spec_id!r} denominator conflicts")
    return _metric(
        coverage_numerator=observed,
        denominator=public_count,
        cardinality_count=int(row["observedCellCount"]),
        cardinality_unit="observed_positive_cells",
        missing_numerator=None if missing_is_not_applicable else public_count - observed,
        missing_state=(
            "NOT_APPLICABLE_FOR_UNPUBLISHED_MOVEMENT_CONTEXT"
            if missing_is_not_applicable
            else "OBSERVED"
        ),
        numerator_definition="Public objects jointly observable for the selected dimensions.",
        denominator_definition="All authoritative public objects.",
    )


def _field_metric(field: str, indexes: Mapping[str, Any], public_count: int) -> dict[str, Any]:
    row = indexes["fields"].get(field)
    if row is None:
        raise RegistryInputError(f"missingness field {field!r} is absent")
    if int(row["eligibleDenominator"]) != public_count:
        raise RegistryInputError(f"missingness field {field!r} denominator conflicts")
    state_counts = _require_mapping(row.get("stateCounts"), f"{field}.stateCounts")
    if sum(int(value) for value in state_counts.values()) != public_count:
        raise RegistryInputError(f"missingness field {field!r} is not exhaustive")
    return _metric(
        coverage_numerator=public_count,
        denominator=public_count,
        cardinality_count=len(state_counts),
        cardinality_unit="supported_classification_states",
        missing_numerator=0,
        missing_state="EXPLICIT_CLASSIFICATION_NOT_GENERIC_NULL_MISSINGNESS",
        numerator_definition=f"Public objects explicitly classified for {field}.",
        denominator_definition="All authoritative public objects.",
    )


def _state_flag_metric(state: str, missingness: Mapping[str, Any], public_count: int) -> dict[str, Any]:
    counts = _require_mapping(missingness.get("stateCounts"), "stateCounts")
    incidence = _require_nonnegative_int(int(counts.get(state, 0)), f"{state} count")
    return _metric(
        coverage_numerator=public_count,
        denominator=public_count,
        cardinality_count=2,
        cardinality_unit="boolean_states",
        missing_numerator=0,
        missing_state="EXPLICIT_FLAG_NOT_GENERIC_MISSINGNESS",
        numerator_definition=(
            f"All public objects evaluated for {state}; observed incidence is "
            f"{incidence} of {public_count}."
        ),
        denominator_definition="All authoritative public objects.",
    )


def _resolve_metric(
    key: str,
    *,
    cross: Mapping[str, Any],
    missingness: Mapping[str, Any],
    curatorial: Mapping[str, Any],
    indexes: Mapping[str, Any],
    public_count: int,
) -> dict[str, Any]:
    if key == "unselected":
        return _unselected_metric(public_count, "UNSELECTED")
    if key.startswith("dimension-concentration:"):
        return _dimension_concentration_metric(
            key.split(":", 1)[1], indexes, public_count
        )
    if key.startswith("dimension-no-missing:"):
        return _dimension_metric(
            key.split(":", 1)[1], indexes, public_count,
            missing_is_not_applicable=True,
        )
    if key.startswith("dimension:"):
        return _dimension_metric(key.split(":", 1)[1], indexes, public_count)
    if key.startswith("pair-no-missing:"):
        return _pair_metric(
            key.split(":", 1)[1], indexes, public_count,
            missing_is_not_applicable=True,
        )
    if key.startswith("pair:"):
        return _pair_metric(key.split(":", 1)[1], indexes, public_count)
    if key.startswith("field:"):
        return _field_metric(key.split(":", 1)[1], indexes, public_count)
    if key.startswith("state-flag:"):
        return _state_flag_metric(
            key.split(":", 1)[1], missingness, public_count
        )

    if key == "temporal-extent":
        base = _field_metric("temporal_precision", indexes, public_count)
        base["cardinality"] = _cardinality(2, public_count, "inclusive_endpoint_fields")
        base["numerator_definition"] = "Public objects with governed start and end years."
        return base
    if key == "range-span":
        count = int(
            _require_mapping(missingness.get("stateCounts"), "stateCounts").get(
                "TEMPORAL:RANGE", 0
            )
        )
        spans = {
            row.get("temporalRangeSpanYears")
            for row in _require_sequence(
                missingness.get("objectVectors", []), "objectVectors"
            )
            if isinstance(row, Mapping)
            and isinstance(row.get("temporalRangeSpanYears"), int)
        }
        return _metric(
            coverage_numerator=count,
            denominator=public_count,
            cardinality_count=len(spans) if spans else None,
            cardinality_unit="observed_distinct_inclusive_spans",
            cardinality_state="OBJECT_VECTORS_OMITTED; CARDINALITY_NOT_REPORTED",
            missing_numerator=None,
            missing_state="NOT_APPLICABLE_TO_NON_RANGE_RECORDS",
            numerator_definition="Public objects governed as temporal ranges.",
            denominator_definition="All authoritative public objects; non-range records are not missing a range span.",
        )
    if key == "missingness-cooccurrence":
        cooccurrences = _require_sequence(
            missingness.get("cooccurrences"), "cooccurrences"
        )
        return _metric(
            coverage_numerator=public_count,
            denominator=public_count,
            cardinality_count=len(cooccurrences),
            cardinality_unit="observed_uncertainty_state_pair_cells",
            missing_numerator=None,
            missing_state="OBJECTS_WITH_NO_ACTIVE_UNCERTAINTY_ARE_OBSERVED",
            numerator_definition="Public cohort evaluated for supported uncertainty-state pairs.",
            denominator_definition="All authoritative public objects.",
        )

    folder_census = _require_mapping(curatorial.get("folder_census"), "folder_census")
    cohort = _require_mapping(folder_census.get("by_cohort"), "folder by_cohort")
    public_folders = _require_mapping(cohort.get("eligible"), "eligible folder census")
    co_membership = _require_mapping(curatorial.get("co_membership"), "co_membership")
    pair_explosion = _require_mapping(curatorial.get("pair_explosion"), "pair_explosion")
    public_members = int(public_folders["object_count"])
    if public_members != public_count:
        raise RegistryInputError("curatorial public population conflicts")
    covered = public_count - int(public_folders["objects_without_membership"])
    nonempty = int(public_folders["nonempty_container_count"])

    if key == "curatorial-membership":
        return _metric(
            coverage_numerator=covered,
            denominator=public_count,
            cardinality_count=nonempty,
            cardinality_unit="nonempty_public_curated_containers",
            missing_numerator=public_count - covered,
            numerator_definition="Public objects with at least one curated-container membership.",
            denominator_definition="All authoritative public objects.",
        )
    if key == "curatorial-type":
        type_count = int(folder_census["observed_folder_type_count"])
        return _metric(
            coverage_numerator=covered,
            denominator=public_count,
            cardinality_count=type_count,
            cardinality_unit="observed_curated_container_types",
            missing_numerator=public_count - covered,
            numerator_definition="Public objects with a typed curated-container membership.",
            denominator_definition="All authoritative public objects.",
        )
    if key == "curatorial-degree":
        distribution = _require_mapping(
            public_folders.get("memberships_per_object"), "memberships_per_object"
        )
        bounded_values = int(distribution["max"]) - int(distribution["min"]) + 1
        return _metric(
            coverage_numerator=covered,
            denominator=public_count,
            cardinality_count=bounded_values,
            cardinality_unit="bounded_integer_membership_counts",
            missing_numerator=public_count - covered,
            numerator_definition="Public objects with a computed curated-membership count.",
            denominator_definition="All authoritative public objects.",
        )
    possible_pairs = int(pair_explosion["possible_public_pair_count"])
    unique_pairs = int(co_membership["unique_pair_count_ge1"])
    if key in {"curatorial-shared", "curatorial-jaccard"}:
        if key == "curatorial-shared":
            cardinality_count = len(_require_mapping(
                co_membership.get("shared_container_count_histogram"),
                "shared container histogram",
            ))
        else:
            cardinality_count = len(
                _require_sequence(
                    _require_mapping(
                        co_membership.get("jaccard_structural_diagnostic"),
                        "jaccard diagnostic",
                    ).get("histogram"),
                    "jaccard histogram",
                )
            )
        return _metric(
            coverage_numerator=unique_pairs,
            denominator=possible_pairs,
            cardinality_count=cardinality_count,
            cardinality_unit=(
                "observed_shared_count_values"
                if key == "curatorial-shared"
                else "observed_jaccard_values"
            ),
            missing_numerator=None,
            missing_state="NO_SHARED_CONTAINER_NOT_GENERIC_MISSINGNESS",
            numerator_definition="Possible public-object pairs sharing at least one curated container.",
            denominator_definition="All unordered pairs in the authoritative public cohort.",
        )
    if key == "curatorial-fanout":
        fanout = _require_mapping(co_membership.get("fanout_ge1"), "fanout_ge1")
        fanout_n = int(fanout["n"])
        nonzero = fanout_n - int(fanout["zero_count"])
        return _metric(
            coverage_numerator=nonzero,
            denominator=public_count,
            cardinality_count=int(fanout["max"]) - int(fanout["min"]) + 1,
            cardinality_unit="bounded_integer_fanout_values",
            missing_numerator=None,
            missing_state="ZERO_FANOUT_IS_OBSERVED_NOT_MISSING",
            numerator_definition="Public objects with at least one co-membership neighbor.",
            denominator_definition="All authoritative public objects.",
        )

    metrics = _require_mapping(cross.get("metrics"), "cross metrics")
    if key in {"cross-frequency", "cross-rarity"}:
        if key == "cross-frequency":
            count = int(metrics["frequencyRowCount"])
            unit = "observed_one_dimensional_value_rows"
        else:
            count = len({str(row["rarityBand"]) for rows in indexes["frequency"].values() for row in rows})
            unit = "observed_rarity_bands"
        return _metric(
            coverage_numerator=public_count,
            denominator=public_count,
            cardinality_count=count,
            cardinality_unit=unit,
            missing_numerator=None,
            missing_state="DIMENSION_SPECIFIC_MISSINGNESS_RETAINED_SEPARATELY",
            numerator_definition="Public cohort evaluated by the frequency registry.",
            denominator_definition="All authoritative public objects.",
        )
    if key == "cross-pairs":
        count = int(metrics["pairObservedCellCount"])
        unit = "observed_positive_pair_cells"
    elif key == "cross-triples":
        count = int(metrics["tripleObservedCellCount"])
        unit = "observed_positive_bounded_triple_cells"
    elif key == "cross-rare":
        rare_rows = [
            row
            for field in ("pairRows", "tripleRows")
            for row in _require_sequence(cross.get(field), field)
            if _require_mapping(row, field).get("signalStatus")
            == "RARE_INTERSECTION_SIGNAL_CANDIDATE"
        ]
        count = len(rare_rows)
        unit = "eligible_observed_rare_pair_or_triple_cells"
    else:
        raise RegistryInputError(f"unknown signal metric key: {key}")
    return _metric(
        coverage_numerator=public_count,
        denominator=public_count,
        cardinality_count=count,
        cardinality_unit=unit,
        missing_numerator=None,
        missing_state="SPECIFICATION_SPECIFIC_OBSERVABILITY",
        numerator_definition="Public cohort evaluated by the bounded observed-cell registry.",
        denominator_definition="All authoritative public objects.",
    )


def _validate_metric_receipt(value: Any, label: str) -> None:
    receipt = _require_mapping(value, label)
    denominator = _require_nonnegative_int(receipt.get("denominator"), f"{label}.denominator")
    if "numerator" in receipt:
        numerator = _require_nonnegative_int(receipt.get("numerator"), f"{label}.numerator")
        if numerator > denominator:
            raise RegistryInputError(f"{label} numerator exceeds denominator")
        rate = receipt.get("rate")
        if not isinstance(rate, (int, float)) or isinstance(rate, bool):
            raise RegistryInputError(f"{label}.rate must be numeric")
        expected = numerator / denominator if denominator else 0.0
        if abs(float(rate) - expected) > 1e-12:
            raise RegistryInputError(f"{label}.rate does not match its denominator")
    elif "count" in receipt:
        _require_nonnegative_int(receipt.get("count"), f"{label}.count")
    elif "state" not in receipt:
        raise RegistryInputError(f"{label} lacks numerator, count, or state")


def _validate_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    if len(rows) != 64:
        raise RegistryInputError(f"registry must contain 64 rows, found {len(rows)}")
    ids: set[str] = set()
    for index, row in enumerate(rows):
        if set(row) != set(REQUIRED_COLUMNS):
            missing = sorted(set(REQUIRED_COLUMNS) - set(row))
            extra = sorted(set(row) - set(REQUIRED_COLUMNS))
            raise RegistryInputError(
                f"row {index} column mismatch; missing={missing}, extra={extra}"
            )
        signal_id = str(row["signal_id"])
        if signal_id in ids:
            raise RegistryInputError(f"duplicate signal_id: {signal_id}")
        ids.add(signal_id)
        if row["family"] not in FAMILIES:
            raise RegistryInputError(f"unknown family: {row['family']}")
        if row["status"] not in ALLOWED_STATUSES:
            raise RegistryInputError(f"forbidden status: {row['status']}")
        if row["derivation_level"] not in DERIVATION_LEVELS:
            raise RegistryInputError(f"forbidden derivation level: {row['derivation_level']}")
        if row["direct_or_derived"] not in {"DIRECT", "DERIVED"}:
            raise RegistryInputError("direct_or_derived must be DIRECT or DERIVED")
        if row["historical_relation"] is not False or row["semantic_relation"] is not False:
            raise RegistryInputError("registry signals cannot be relations")
        if row["direct_or_derived"] == "DERIVED" and not str(row["derivation_version"]).strip():
            raise RegistryInputError("every derived row requires a derivation version")
        _validate_metric_receipt(row["coverage"], f"{signal_id}.coverage")
        _validate_metric_receipt(row["cardinality"], f"{signal_id}.cardinality")
        _validate_metric_receipt(row["missing_rate"], f"{signal_id}.missing_rate")
        rendered = json.dumps(row, ensure_ascii=False, sort_keys=True)
        if UUID_PATTERN.search(rendered):
            raise RegistryInputError("internal UUID entered signal registry")
        if URL_PATTERN.search(rendered):
            raise RegistryInputError("URL entered signal registry")
        if RAW_ID_PATTERN.search(rendered):
            raise RegistryInputError("raw object or curatorial ID entered signal registry")

    family_counts = Counter(str(row["family"]) for row in rows)
    status_counts = Counter(str(row["status"]) for row in rows)
    if set(family_counts) != set(FAMILIES) or any(family_counts[family] == 0 for family in FAMILIES):
        raise RegistryInputError("all eight signal families must be populated")
    if dict(status_counts) != EXPECTED_STATUS_COUNTS:
        raise RegistryInputError(
            f"status distribution changed: {dict(sorted(status_counts.items()))}"
        )


def _summary_distribution(counter: Counter[str], total: int) -> list[dict[str, Any]]:
    return [
        {"value": value, **_ratio(count, total)}
        for value, count in sorted(counter.items())
    ]


def analyze(
    *,
    cross_dimensional_result: Mapping[str, Any],
    missingness_result: Mapping[str, Any],
    curatorial_result: Mapping[str, Any],
    derivation_version: str = DEFAULT_DERIVATION_VERSION,
) -> dict[str, Any]:
    """Return a validated, deterministic 64-row candidate signal registry."""

    cross = _require_mapping(cross_dimensional_result, "cross_dimensional_result")
    missingness = _require_mapping(missingness_result, "missingness_result")
    curatorial = _require_mapping(curatorial_result, "curatorial_result")
    if not isinstance(derivation_version, str) or not derivation_version.strip():
        raise RegistryInputError("derivation_version must be nonblank text")

    cross_population = _require_mapping(cross.get("population"), "cross population")
    missing_population = _require_mapping(
        missingness.get("population"), "missingness population"
    )
    public_count = _require_nonnegative_int(
        cross_population.get("publicObjectCount"), "cross publicObjectCount"
    )
    if public_count == 0:
        raise RegistryInputError("signal registry requires a nonempty public cohort")
    if int(cross_population.get("heldObjectCount", -1)) != 0:
        raise RegistryInputError("held objects entered cross-dimensional results")
    if int(missing_population.get("publicObjectCount", -1)) != public_count:
        raise RegistryInputError("analysis public populations do not reconcile")
    if int(missing_population.get("heldObjectCount", -1)) != 0:
        raise RegistryInputError("held objects entered missingness results")
    cross_hashes = _require_mapping(cross.get("hashes"), "cross hashes")
    dimension_concentration_sha = cross_hashes.get(
        "dimensionConcentrationRowsSha256"
    )
    if not isinstance(dimension_concentration_sha, str) or not re.fullmatch(
        r"[0-9a-f]{64}", dimension_concentration_sha
    ):
        raise RegistryInputError(
            "cross analysis lacks a deterministic dimension concentration receipt"
        )

    indexes = _indexes(cross, missingness)
    rows: list[dict[str, Any]] = []
    for spec in SPECS:
        metrics = _resolve_metric(
            str(spec["metric_key"]),
            cross=cross,
            missingness=missingness,
            curatorial=curatorial,
            indexes=indexes,
            public_count=public_count,
        )
        row = {key: value for key, value in spec.items() if key != "metric_key"}
        row.update(metrics)
        row["derivation_version"] = (
            DIRECT_DERIVATION_VERSION
            if row["direct_or_derived"] == "DIRECT"
            else derivation_version
        )
        rows.append({column: row[column] for column in REQUIRED_COLUMNS})
    rows.sort(key=lambda row: str(row["signal_id"]))
    _validate_rows(rows)

    status_counts = Counter(str(row["status"]) for row in rows)
    family_counts = Counter(str(row["family"]) for row in rows)
    level_counts = Counter(str(row["derivation_level"]) for row in rows)
    total = len(rows)
    summary = {
        "SIGNAL_COUNT": _cardinality(total, total, "registry_rows"),
        "DEFERRED_SIGNAL_COUNT": _cardinality(
            status_counts["DEFER"], total, "registry_rows"
        ),
        "NEEDS_MORE_DATA_SIGNAL_COUNT": _cardinality(
            status_counts["NEEDS_MORE_DATA"], total, "registry_rows"
        ),
        "status_distribution": _summary_distribution(status_counts, total),
        "family_distribution": _summary_distribution(family_counts, total),
        "derivation_level_distribution": _summary_distribution(level_counts, total),
    }
    deterministic_payload = {
        "schema_version": SCHEMA_VERSION,
        "derivation_version": derivation_version,
        "required_columns": list(REQUIRED_COLUMNS),
        "rows": rows,
        "summary": summary,
        "input_receipts": {
            "cross_dimensional_sha256": _require_mapping(
                cross.get("hashes"), "cross hashes"
            ).get("deterministicPayloadSha256"),
            "dimension_concentration_rows_sha256": _require_mapping(
                cross.get("hashes"), "cross hashes"
            ).get("dimensionConcentrationRowsSha256"),
            "missingness_sha256": _require_mapping(
                missingness.get("hashes"), "missingness hashes"
            ).get("deterministicPayloadSha256"),
            "curatorial_sha256": _require_mapping(
                curatorial.get("deterministic_receipt"), "curatorial receipt"
            ).get("sha256"),
        },
        "invariants": {
            "ALL_EIGHT_FAMILIES_PRESENT": True,
            "ALL_REQUIRED_COLUMNS_PRESENT": True,
            "ALLOWED_STATUS_VOCABULARY_ONLY": True,
            "EVERY_METRIC_EXPOSES_DENOMINATOR": True,
            "EVERY_DERIVED_SIGNAL_VERSIONED": True,
            "NATIVE_DIMENSION_CONCENTRATION_RECEIPTS_BOUND": True,
            "BOUND_DIMENSION_CONCENTRATION_SIGNAL_COUNT": 6,
            "HISTORICAL_RELATION": False,
            "SEMANTIC_RELATION": False,
            "SIMILARITY_MODEL_SELECTED": False,
            "FEATURE_WEIGHTS_SELECTED": False,
            "CLUSTER_MODEL_SELECTED": False,
            "PROBABILITY_MODEL_SELECTED": False,
            "TEMPLATE_SELECTED": False,
            "RENDERER_SELECTED": False,
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


def _synthetic_results() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    dimensions = {
        "medium": (2, 4), "theme": (2, 4), "movement_context": (1, 2),
        "decade": (2, 4), "geography": (2, 4), "source": (2, 4),
        "object_type": (2, 4), "creator": (3, 4), "temporal_precision": (2, 4),
        "geography_mapping_state": (3, 4), "geography_class": (2, 4),
    }
    frequency_rows: list[dict[str, Any]] = []
    for dimension, (cardinality, coverage) in dimensions.items():
        for index in range(cardinality):
            frequency_rows.append({
                "dimension": dimension,
                "observedObjectDenominator": coverage,
                "eligibleDenominator": 4,
                "rarityBand": "SINGLETON" if index == 0 else "COUNT_2_TO_5",
            })
    density_rows = [
        {
            "specId": spec_id,
            "cellKind": "PAIR",
            "observedCellCount": 2,
            "jointObservableObjectCount": 2 if "movement_context" in spec_id else 4,
            "eligibleDenominator": 4,
        }
        for spec_id in (
            "medium__theme", "theme__movement_context", "object_type__medium",
            "creator__medium",
        )
    ]
    concentration_inputs = (
        ("CONCENTRATION_SOURCE", "SOURCE", "source", "PUBLIC_METADATA_DERIVED", 4, 4, 2, 3, 3 / 4, 4, 1.0),
        ("CONCENTRATION_TEMPORAL", "TEMPORAL", "decade", "PUBLIC_GOVERNED_DERIVED", 4, 4, 2, 3, 3 / 4, 4, 1.0),
        ("CONCENTRATION_GEOGRAPHIC", "GEOGRAPHIC", "geography", "PUBLIC_GOVERNED_DERIVED", 4, 4, 2, 3, 3 / 4, 4, 1.0),
        ("CONCENTRATION_CURATORIAL", "CURATORIAL", "curated_container", "ANALYSIS_ONLY_CURATORIAL_DERIVED", 4, 8, 3, 4, 1 / 2, 8, 1.0),
    )
    dimension_concentration_rows: list[dict[str, Any]] = []
    for (
        diagnostic_id, family, dimension, governance_state, observed,
        assignments, distinct, top1_count, top1_share,
        top5_assignment_count, top5_share,
    ) in concentration_inputs:
        if dimension == "curated_container":
            shares = (4 / 8, 3 / 8, 1 / 8)
        else:
            shares = (3 / 4, 1 / 4)
        entropy = -sum(share * math.log(share) for share in shares)
        row = {
            "diagnosticId": diagnostic_id,
            "family": family,
            "dimension": dimension,
            "governanceState": governance_state,
            "interpretationBoundary": "SYNTHETIC_DIAGNOSTIC_NOT_A_RELATION",
            "derivationVersion": DEFAULT_DERIVATION_VERSION,
            "eligibleDenominator": 4,
            "observedObjectCount": observed,
            "unassignedObjectCount": 4 - observed,
            "assignmentCount": assignments,
            "assignmentDenominator": assignments,
            "distinctValueCount": distinct,
            "top1ValueId": f"analysis:{dimension}:top1",
            "top1ValueLabel": "Synthetic top value",
            "top1AssignmentCount": top1_count,
            "top1Share": top1_share,
            "top5AssignmentCount": top5_assignment_count,
            "top5Share": top5_share,
            "hhi": sum(share * share for share in shares),
            "shannonEntropyNats": entropy,
            "normalizedEntropy": entropy / math.log(distinct),
            "membershipPolicy": "UNIQUE_PER_OBJECT_VALUE_MEMBERSHIP",
            "shareDenominatorSemantics": "UNIQUE_OBJECT_VALUE_ASSIGNMENTS",
            "eligibleDenominatorSemantics": "AUTHORITATIVE_PUBLIC_OBJECTS",
            "diagnosticStatus": "ANALYSIS_DIAGNOSTIC_NOT_A_RELATION",
            "deterministic": True,
            "historicalRelation": False,
            "semanticRelation": False,
        }
        row["receiptSha256"] = sha256_json(row)
        dimension_concentration_rows.append(row)
    cross = {
        "population": {"publicObjectCount": 4, "heldObjectCount": 0},
        "frequencyRows": frequency_rows,
        "densityRows": density_rows,
        "pairRows": [
            {
                "objectCount": 1,
                "signalStatus": "RARE_INTERSECTION_SIGNAL_CANDIDATE",
            },
            {
                "objectCount": 30,
                "signalStatus": "SUPPORTING_OBSERVED_INTERSECTION",
            },
        ],
        "tripleRows": [{
            "objectCount": 2,
            "signalStatus": "RARE_INTERSECTION_SIGNAL_CANDIDATE",
        }],
        "sourceConcentrationRows": [{
            "subsetDimension": "ALL_PUBLIC_OBJECTS",
            "objectCount": 4,
            "distinctSourceCount": 2,
        }],
        "dimensionConcentrationRows": dimension_concentration_rows,
        "metrics": {
            "frequencyRowCount": len(frequency_rows),
            "pairObservedCellCount": 2,
            "tripleObservedCellCount": 1,
        },
        "hashes": {
            "deterministicPayloadSha256": "a" * 64,
            "dimensionConcentrationRowsSha256": sha256_json(
                dimension_concentration_rows
            ),
        },
    }
    field_matrix = [
        {"field": "movement_context", "eligibleDenominator": 4,
         "stateCounts": {"OBSERVED": 2, "NO_PUBLISHED_MOVEMENT_CONTEXT": 2}},
        {"field": "temporal_precision", "eligibleDenominator": 4,
         "stateCounts": {"year": 3, "range": 1}},
        {"field": "geography_mapping_state", "eligibleDenominator": 4,
         "stateCounts": {"mapped": 2, "aggregate_only": 1, "unmapped": 1}},
        {"field": "creator", "eligibleDenominator": 4,
         "stateCounts": {"OBSERVED": 2, "UNKNOWN_SOURCE_VALUE": 2}},
    ]
    missingness = {
        "population": {"publicObjectCount": 4, "heldObjectCount": 0},
        "fieldMatrix": field_matrix,
        "stateCounts": {
            "TEMPORAL:RANGE": 1,
            "GEOGRAPHY:MULTI_REGION": 1,
            "GEOGRAPHY:QUALIFIED": 1,
        },
        "cooccurrences": [{"stateA": "A", "stateB": "B"}],
        "objectVectors": [{"temporalRangeSpanYears": 10}],
        "hashes": {"deterministicPayloadSha256": "b" * 64},
    }
    curatorial = {
        "cohort": {"public_object_count": 4},
        "folder_census": {
            "observed_folder_type_count": 4,
            "by_cohort": {"eligible": {
                "object_count": 4,
                "objects_without_membership": 0,
                "nonempty_container_count": 4,
                "memberships_per_object": {"min": 3, "max": 4},
            }},
        },
        "co_membership": {
            "unique_pair_count_ge1": 4,
            "shared_container_count_histogram": {"1": 3, "2": 1},
            "fanout_ge1": {"n": 4, "min": 1, "max": 3, "zero_count": 0},
            "jaccard_structural_diagnostic": {"histogram": [{"value": 0.5}]},
        },
        "pair_explosion": {"possible_public_pair_count": 6},
        "deterministic_receipt": {"sha256": "c" * 64},
    }
    return cross, missingness, curatorial


def run_self_tests() -> dict[str, Any]:
    cross, missingness, curatorial = _synthetic_results()
    first = analyze(
        cross_dimensional_result=cross,
        missingness_result=missingness,
        curatorial_result=curatorial,
    )
    reversed_cross = dict(cross)
    for key in (
        "frequencyRows", "densityRows", "pairRows", "tripleRows",
        "dimensionConcentrationRows",
    ):
        reversed_cross[key] = list(reversed(cross[key]))
    second = analyze(
        cross_dimensional_result=reversed_cross,
        missingness_result={**missingness, "fieldMatrix": list(reversed(missingness["fieldMatrix"]))},
        curatorial_result=curatorial,
    )
    assert first["deterministic_receipt"] == second["deterministic_receipt"]
    assert len(first["rows"]) == 64
    assert first["summary"]["DEFERRED_SIGNAL_COUNT"]["count"] == 5
    assert first["summary"]["NEEDS_MORE_DATA_SIGNAL_COUNT"]["count"] == 2
    assert all(row["historical_relation"] is False for row in first["rows"])
    assert all(row["semantic_relation"] is False for row in first["rows"])
    bound = {
        row["signal_id"]: row
        for row in first["rows"]
        if row["signal_id"] in {
            "SIG-TEMPORAL-CONCENTRATION",
            "SIG-GEOGRAPHY-CONCENTRATION",
            "SIG-SOURCE-DOMINANT",
            "SIG-SOURCE-CONCENTRATION",
            "SIG-SOURCE-DIVERSITY",
            "SIG-CURATORIAL-SUPPORT",
        }
    }
    assert len(bound) == 6
    assert all(
        "dimensionConcentrationReceiptSha256" in row["coverage"]
        for row in bound.values()
    )
    assert all(
        "dimensionConcentrationReceiptSha256" in row["cardinality"]
        for row in bound.values()
    )
    assert bound["SIG-CURATORIAL-SUPPORT"]["coverage"]["assignmentCount"] == 8
    assert bound["SIG-CURATORIAL-SUPPORT"]["coverage"]["denominator"] == 4
    assert bound["SIG-CURATORIAL-SUPPORT"]["cardinality"]["denominator"] == 8
    assert bound["SIG-TEMPORAL-CONCENTRATION"]["cardinality"]["top1Share"] == 0.75

    adversaries: list[dict[str, Any]] = []
    base = dict(first["rows"][0])
    missing_column = dict(base)
    missing_column.pop("coverage")
    adversaries.append(missing_column)
    forbidden_status = dict(base, status="PROMOTED")
    adversaries.append(forbidden_status)
    adversaries.append(dict(base, description="unsafe 123e4567-e89b-12d3-a456-426614174000"))
    adversaries.append(dict(base, description="unsafe FOL-RAW-001"))
    adversaries.append(dict(base, historical_relation=True))
    adversaries.append(dict(base, semantic_relation=True))
    derived_unversioned = dict(base, direct_or_derived="DERIVED", derivation_version="")
    adversaries.append(derived_unversioned)
    failures = 0
    for adversary in adversaries:
        candidate_rows = list(first["rows"])
        candidate_rows[0] = adversary
        try:
            _validate_rows(candidate_rows)
        except RegistryInputError:
            failures += 1
    assert failures == len(adversaries)

    corrupt_receipt_cross = dict(cross)
    corrupt_receipt_rows = [dict(row) for row in cross["dimensionConcentrationRows"]]
    corrupt_receipt_rows[0]["top1Share"] = 0.5
    corrupt_receipt_cross["dimensionConcentrationRows"] = corrupt_receipt_rows
    try:
        analyze(
            cross_dimensional_result=corrupt_receipt_cross,
            missingness_result=missingness,
            curatorial_result=curatorial,
        )
    except RegistryInputError:
        failures += 1
    else:
        raise AssertionError("corrupt concentration receipt was accepted")

    concentration_adversaries = (
        {"assignmentDenominator": 3},
        {"membershipPolicy": "DUPLICATE_ASSIGNMENTS_ALLOWED"},
        {"semanticRelation": True},
        {"governanceState": "UNGOVERNED"},
    )
    for mutation in concentration_adversaries:
        adversary_cross = dict(cross)
        adversary_rows = [dict(row) for row in cross["dimensionConcentrationRows"]]
        adversary_rows[0].update(mutation)
        adversary_rows[0]["receiptSha256"] = sha256_json({
            key: value
            for key, value in adversary_rows[0].items()
            if key != "receiptSha256"
        })
        adversary_cross["dimensionConcentrationRows"] = adversary_rows
        try:
            analyze(
                cross_dimensional_result=adversary_cross,
                missingness_result=missingness,
                curatorial_result=curatorial,
            )
        except RegistryInputError:
            failures += 1
        else:
            raise AssertionError(
                f"invalid concentration semantics were accepted: {mutation}"
            )
    expected_adversaries = len(adversaries) + 1 + len(concentration_adversaries)
    assert failures == expected_adversaries
    return {
        "status": "PASS",
        "checks": 28,
        "adversaries": expected_adversaries,
        "signal_count": {"count": 64, "denominator": 64},
        "deterministic_sha256": first["deterministic_receipt"]["sha256"],
    }


def _load_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text("utf-8"))
    if not isinstance(value, Mapping):
        raise RegistryInputError(f"{path} must contain a JSON object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cross", type=Path)
    parser.add_argument("--missingness", type=Path)
    parser.add_argument("--curatorial", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(run_self_tests(), sort_keys=True))
        return
    if not all((args.cross, args.missingness, args.curatorial, args.output)):
        parser.error("--cross, --missingness, --curatorial, and --output are required")
    result = analyze(
        cross_dimensional_result=_load_json(args.cross),
        missingness_result=_load_json(args.missingness),
        curatorial_result=_load_json(args.curatorial),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json_bytes(result))
    print(json.dumps({
        "status": "PASS",
        "output": str(args.output),
        "signals": len(result["rows"]),
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
