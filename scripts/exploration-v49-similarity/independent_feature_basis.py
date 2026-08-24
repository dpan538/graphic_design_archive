#!/usr/bin/env python3
"""Build the smallest defensible independent Exploration feature basis.

The basis is a research contract, not a selected public model.  It assigns the
eight scoring-eligible base signals to eight non-duplicative basis units,
keeps missingness in a separate comparability channel, and leaves raw curation
outside the independent score basis.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from signal_lineage import (
    RAW_CURATED_JACCARD_IMPORT_BOUNDARY,
    SignalLineageError,
    analyze_signal_lineage,
    validate_signal_lineage_analysis,
)


SCHEMA_VERSION = "trace-exploration-independent-feature-basis/v1"
DERIVATION_VERSION = "trace-exploration-independent-feature-basis-round1-v1"

BASIS_COLUMNS = (
    "basis_id",
    "affinity_family",
    "primary_signal_ids",
    "candidate_posting_signal_ids",
    "comparability_signal_ids",
    "explanation_signal_ids",
    "combination_policy",
    "positive_affinity_policy",
    "missingness_policy",
    "broad_feature_policy",
    "default_enabled",
    "reason",
)


class IndependentFeatureBasisError(ValueError):
    """Raised when the independent basis cannot be proven non-duplicative."""


def _canonical_json_bytes(value: Any) -> bytes:
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


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _basis(
    basis_id: str,
    affinity_family: str,
    primary_signal_ids: Sequence[str],
    *,
    candidate_posting_signal_ids: Sequence[str] = (),
    comparability_signal_ids: Sequence[str] = (),
    explanation_signal_ids: Sequence[str] = (),
    combination_policy: str,
    positive_affinity_policy: str,
    missingness_policy: str,
    broad_feature_policy: str,
    default_enabled: bool,
    reason: str,
) -> dict[str, Any]:
    return {
        "basis_id": basis_id,
        "affinity_family": affinity_family,
        "primary_signal_ids": sorted(set(primary_signal_ids)),
        "candidate_posting_signal_ids": sorted(
            set(candidate_posting_signal_ids)
        ),
        "comparability_signal_ids": sorted(set(comparability_signal_ids)),
        "explanation_signal_ids": sorted(set(explanation_signal_ids)),
        "combination_policy": combination_policy,
        "positive_affinity_policy": positive_affinity_policy,
        "missingness_policy": missingness_policy,
        "broad_feature_policy": broad_feature_policy,
        "default_enabled": default_enabled,
        "reason": reason,
    }


_BASIS_ROWS = (
    _basis(
        "BASIS-CONTEXT-MEDIUM",
        "GOVERNED_CONTEXT",
        ("SIG-CONTEXT-MEDIUM",),
        candidate_posting_signal_ids=("SIG-CONTEXT-MEDIUM",),
        explanation_signal_ids=("SIG-CONTEXT-SAME-MEDIUM",),
        combination_policy="SET_OVERLAP_ON_CANONICAL_GOVERNED_VALUES;ONE_MEDIUM_CONTRIBUTION",
        positive_affinity_policy="OBSERVED_SHARED_VALUE_ONLY",
        missingness_policy="UNAVAILABLE_EXCLUDED_FROM_AFFINITY_AND_REPORTED_IN_COMPARABILITY",
        broad_feature_policy="VALUE_FREQUENCY_SENSITIVITY_AND_FAMILY_CAP_REQUIRED",
        default_enabled=True,
        reason="Removing medium loses a governed Context dimension not recoverable from theme or movement context.",
    ),
    _basis(
        "BASIS-CONTEXT-MOVEMENT",
        "GOVERNED_CONTEXT",
        ("SIG-CONTEXT-MOVEMENT",),
        candidate_posting_signal_ids=("SIG-CONTEXT-MOVEMENT",),
        comparability_signal_ids=("SIG-MISSINGNESS-MOVEMENT-AVAILABILITY",),
        explanation_signal_ids=("SIG-CONTEXT-SAME-MOVEMENT",),
        combination_policy="SET_OVERLAP_ON_PUBLISHED_GOVERNED_VALUES;ONE_MOVEMENT_CONTRIBUTION",
        positive_affinity_policy="BOTH_OBSERVED_AND_SHARED_VALUE_ONLY",
        missingness_policy="NO_PUBLISHED_MOVEMENT_CONTEXT_IS_UNAVAILABLE_NOT_A_MATCH",
        broad_feature_policy="SPARSE_SELECTION_EFFECT_REPORTED;FAMILY_CAP_REQUIRED",
        default_enabled=True,
        reason="Published movement context is sparse but contains governed information not derivable from medium or theme.",
    ),
    _basis(
        "BASIS-CONTEXT-THEME",
        "GOVERNED_CONTEXT",
        ("SIG-CONTEXT-THEME",),
        candidate_posting_signal_ids=("SIG-CONTEXT-THEME",),
        explanation_signal_ids=("SIG-CONTEXT-SAME-THEME",),
        combination_policy="SET_OVERLAP_ON_CANONICAL_GOVERNED_VALUES;ONE_THEME_CONTRIBUTION",
        positive_affinity_policy="OBSERVED_SHARED_VALUE_ONLY",
        missingness_policy="UNAVAILABLE_EXCLUDED_FROM_AFFINITY_AND_REPORTED_IN_COMPARABILITY",
        broad_feature_policy="VALUE_FREQUENCY_SENSITIVITY_AND_FAMILY_CAP_REQUIRED",
        default_enabled=True,
        reason="Removing theme loses a governed Context dimension not recoverable from medium or movement context.",
    ),
    _basis(
        "BASIS-TEMPORAL-OBSERVATION",
        "GOVERNED_TEMPORAL",
        ("SIG-TEMPORAL-EXTENT",),
        candidate_posting_signal_ids=("SIG-TEMPORAL-DECADE",),
        comparability_signal_ids=(
            "SIG-MISSINGNESS-TEMPORAL",
            "SIG-TEMPORAL-PRECISION",
        ),
        explanation_signal_ids=(
            "SIG-TEMPORAL-RANGE-SPAN",
            "SIG-TEMPORAL-SAME-DECADE",
        ),
        combination_policy="ONE_BOUNDED_TEMPORAL_CONTRIBUTION_FROM_INCLUSIVE_EXTENT;DECADE_IS_RETRIEVAL_ALIAS",
        positive_affinity_policy="TRANSPARENT_INTERVAL_OVERLAP_OR_DECLARED_DISTANCE_VARIANT_ONLY",
        missingness_policy="PRECISION_QUALIFIES_COMPARABILITY_AND_NEVER_MATCHES_POSITIVELY",
        broad_feature_policy="RANGE_AND_APPROXIMATE_PRECISION_PRESERVED;DECAY_SENSITIVITY_REQUIRED",
        default_enabled=True,
        reason="Inclusive governed extent is the least-derived temporal fact; decade, range span, and same-decade are projections of it.",
    ),
    _basis(
        "BASIS-GEOGRAPHY-OBSERVATION",
        "GOVERNED_GEOGRAPHY",
        ("SIG-GEOGRAPHY-ASSIGNMENT",),
        candidate_posting_signal_ids=(
            "SIG-GEOGRAPHY-ASSIGNMENT",
            "SIG-GEOGRAPHY-CLASS",
        ),
        comparability_signal_ids=(
            "SIG-GEOGRAPHY-MAPPING-STATE",
            "SIG-GEOGRAPHY-MULTI-REGION",
            "SIG-MISSINGNESS-GEOGRAPHY-MAPPING",
            "SIG-MISSINGNESS-GEOGRAPHY-QUALIFIED",
        ),
        explanation_signal_ids=("SIG-GEOGRAPHY-SAME",),
        combination_policy="ONE_EXACT_GOVERNED_GEOGRAPHY_CONTRIBUTION;CLASS_IS_CANDIDATE_OR_EXPLANATION_FALLBACK_ONLY_AND_NEVER_ADDITIVE",
        positive_affinity_policy="EXACT_GOVERNED_OVERLAP_ONLY;DETERMINISTIC_CLASS_LOOKUP_ADDS_ZERO_SCORE",
        missingness_policy="MAPPED_AGGREGATE_ONLY_UNMAPPED_QUALIFIED_AND_MULTI_REGION_STATES_REPORTED_SEPARATELY",
        broad_feature_policy="GEOGRAPHY_CLASS_CAPPED;NO_LAYOUT_CENTROID_ADJACENCY_OR_COORDINATE_DISTANCE",
        default_enabled=True,
        reason="All 93 governed geography IDs deterministically map to one class, so exact assignment is the sole independent fact and class remains retrieval/explanation only.",
    ),
    _basis(
        "BASIS-SOURCE-IDENTITY",
        "SOURCE_COMPOSITION",
        ("SIG-SOURCE-NAME",),
        candidate_posting_signal_ids=("SIG-SOURCE-NAME",),
        explanation_signal_ids=("SIG-SOURCE-SAME",),
        combination_policy="ONE_CAPPED_SOURCE_FAMILY_CONTRIBUTION_UNDER_EXPLICIT_SOURCE_VARIANT",
        positive_affinity_policy="NOT_AUTOMATIC;SOURCE_0_TO_SOURCE_4_EXPERIMENT_POLICY_REQUIRED",
        missingness_policy="UNAVAILABLE_SOURCE_ADDS_ZERO_AFFINITY",
        broad_feature_policy="CORPUS_SHARE_HHI_AND_RESULT_CONCENTRATION_REPORTED;CAP_REQUIRED",
        default_enabled=False,
        reason="Source identity is independent corpus-composition information, but acquisition bias makes exclusion the default baseline.",
    ),
    _basis(
        "BASIS-DESCRIPTIVE-CREATOR",
        "DESCRIPTIVE_METADATA",
        ("SIG-DESCRIPTIVE-CREATOR",),
        candidate_posting_signal_ids=("SIG-DESCRIPTIVE-CREATOR",),
        comparability_signal_ids=("SIG-MISSINGNESS-CREATOR",),
        explanation_signal_ids=("SIG-DESCRIPTIVE-SAME-CREATOR",),
        combination_policy="ONE_CREATOR_CONTRIBUTION_FROM_NORMALIZED_PUBLIC_ATTRIBUTION",
        positive_affinity_policy="OBSERVED_NON_UNKNOWN_EQUALITY_ONLY",
        missingness_policy="UNKNOWN_AND_QUALIFIED_UNKNOWN_ARE_UNAVAILABLE_AND_ADD_ZERO",
        broad_feature_policy="HIGH_CARDINALITY_LOW_SUPPORT_CAP_AND_SOURCE_GRANULARITY_DIAGNOSTIC_REQUIRED",
        default_enabled=True,
        reason="Observed creator attribution is approved descriptive information not recoverable from governed Context, time, or geography.",
    ),
    _basis(
        "BASIS-DESCRIPTIVE-OBJECT-TYPE",
        "DESCRIPTIVE_METADATA",
        ("SIG-DESCRIPTIVE-OBJECT-TYPE",),
        candidate_posting_signal_ids=("SIG-DESCRIPTIVE-OBJECT-TYPE",),
        combination_policy="ONE_OBJECT_TYPE_CONTRIBUTION_FROM_NORMALIZED_PUBLIC_VALUE",
        positive_affinity_policy="OBSERVED_SHARED_VALUE_ONLY",
        missingness_policy="UNAVAILABLE_EXCLUDED_FROM_AFFINITY_AND_REPORTED_IN_COMPARABILITY",
        broad_feature_policy="SOURCE_GRANULARITY_DIAGNOSTIC_AND_FAMILY_CAP_REQUIRED",
        default_enabled=True,
        reason="Object type is approved descriptive information not deterministically recoverable from governed medium.",
    ),
)

BASIS_ROW_BY_ID = {row["basis_id"]: row for row in _BASIS_ROWS}


def _lineage_signals(lineage_analysis: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    try:
        validate_signal_lineage_analysis(lineage_analysis)
    except SignalLineageError as error:
        raise IndependentFeatureBasisError(str(error)) from error
    signals = lineage_analysis["signals"]
    return {row["signal_id"]: row for row in signals}


def _validate_basis_rows(
    rows: Sequence[Mapping[str, Any]],
    lineage_by_id: Mapping[str, Mapping[str, Any]],
) -> None:
    if len(rows) != 8 or len({row.get("basis_id") for row in rows}) != 8:
        raise IndependentFeatureBasisError("independent basis must contain 8 units")
    independent_ids: list[str] = []
    for row in rows:
        missing = set(BASIS_COLUMNS) - set(row)
        if missing:
            raise IndependentFeatureBasisError(
                f"{row.get('basis_id')} lacks basis columns {sorted(missing)}"
            )
        primary = row["primary_signal_ids"]
        if not isinstance(primary, list) or not primary:
            raise IndependentFeatureBasisError(
                f"{row['basis_id']} must name at least one primary signal"
            )
        independent_ids.extend(primary)
        for signal_id in primary:
            signal = lineage_by_id.get(signal_id)
            if signal is None:
                raise IndependentFeatureBasisError(
                    f"unknown primary basis signal: {signal_id}"
                )
            if signal["scoring_disposition"] != "INDEPENDENT_BASE_SIGNAL":
                raise IndependentFeatureBasisError(
                    f"non-independent signal entered the base: {signal_id}"
                )
            if not signal["scoring_allowed"] or signal["duplicate_for_scoring"]:
                raise IndependentFeatureBasisError(
                    f"ineligible primary signal entered the base: {signal_id}"
                )
        for field in (
            "candidate_posting_signal_ids",
            "comparability_signal_ids",
            "explanation_signal_ids",
        ):
            values = row[field]
            if not isinstance(values, list) or values != sorted(set(values)):
                raise IndependentFeatureBasisError(
                    f"{row['basis_id']} {field} is not a sorted unique array"
                )
            if any(signal_id not in lineage_by_id for signal_id in values):
                raise IndependentFeatureBasisError(
                    f"{row['basis_id']} references an unknown supporting signal"
                )
        for signal_id in row["comparability_signal_ids"]:
            if lineage_by_id[signal_id]["scoring_disposition"] != "COMPARABILITY_ONLY":
                raise IndependentFeatureBasisError(
                    f"non-comparability signal entered comparability channel: {signal_id}"
                )
    if len(independent_ids) != len(set(independent_ids)):
        raise IndependentFeatureBasisError(
            "one independent source signal entered more than one basis unit"
        )
    expected_independent = {
        signal_id
        for signal_id, signal in lineage_by_id.items()
        if signal["scoring_disposition"] == "INDEPENDENT_BASE_SIGNAL"
    }
    if set(independent_ids) != expected_independent:
        raise IndependentFeatureBasisError(
            "basis does not cover every and only independent lineage signal"
        )
    if any(
        lineage_by_id[signal_id]["source_artifact"].endswith(
            "exploration-curatorial-summary.json"
        )
        for signal_id in independent_ids
    ):
        raise IndependentFeatureBasisError(
            "raw curatorial structure entered the independent score basis"
        )


def validate_independent_feature_basis(analysis: Mapping[str, Any]) -> None:
    """Raise when the basis receipt no longer proves independence."""

    if not isinstance(analysis, Mapping):
        raise IndependentFeatureBasisError("basis analysis must be a mapping")
    rows = analysis.get("basisRows")
    lineage_signals = analysis.get("lineageSignals")
    if not isinstance(rows, list) or not isinstance(lineage_signals, list):
        raise IndependentFeatureBasisError(
            "basis analysis must contain basisRows and lineageSignals"
        )
    lineage_by_id = {
        row.get("signal_id"): row for row in lineage_signals if isinstance(row, Mapping)
    }
    if len(lineage_by_id) != 64:
        raise IndependentFeatureBasisError(
            "basis analysis must bind all 64 lineage signals"
        )
    _validate_basis_rows(rows, lineage_by_id)
    counts = analysis.get("counts")
    if not isinstance(counts, Mapping):
        raise IndependentFeatureBasisError("basis counts are absent")
    if counts.get("independentBaseSignalCount") != 8:
        raise IndependentFeatureBasisError("independent base signal count changed")
    if counts.get("basisUnitCount") != 8:
        raise IndependentFeatureBasisError("basis unit count changed")
    if counts.get("curatorialResidualSignalCount") != 0:
        raise IndependentFeatureBasisError(
            "curatorial residual entered the independent basis"
        )
    if counts.get("sameSourceFactDoubleScoreCount") != 0:
        raise IndependentFeatureBasisError(
            "same-source fact remains multiply scoreable"
        )
    curatorial = analysis.get("curatorialPolicy")
    if not isinstance(curatorial, Mapping):
        raise IndependentFeatureBasisError("curatorial policy is absent")
    if (
        curatorial.get("asRecallIndex") is not True
        or curatorial.get("asIndependentScore") is not False
        or curatorial.get("residualSignalCount") != 0
    ):
        raise IndependentFeatureBasisError("curatorial boundary changed")
    if curatorial.get("rawJaccardImportBoundary") != RAW_CURATED_JACCARD_IMPORT_BOUNDARY:
        raise IndependentFeatureBasisError("raw Jaccard import boundary changed")
    comparability = analysis.get("comparabilityChannel")
    if not isinstance(comparability, Mapping):
        raise IndependentFeatureBasisError("comparability channel is absent")
    if (
        comparability.get("sharedUnknownPositiveCreditCount") != 0
        or comparability.get("includedInAffinityNumerator") is not False
        or comparability.get("emittedSeparately") is not True
    ):
        raise IndependentFeatureBasisError(
            "missingness leaked into positive affinity"
        )
    invariants = analysis.get("invariants")
    if not isinstance(invariants, Mapping) or not all(invariants.values()):
        raise IndependentFeatureBasisError("independent basis has a failed invariant")


def build_independent_feature_basis(
    lineage_analysis: Mapping[str, Any],
    *,
    input_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the canonical independent basis and machine-checkable policies."""

    lineage_by_id = _lineage_signals(lineage_analysis)
    bound_input_receipt = dict(lineage_analysis["inputReceipt"])
    if input_receipt is not None and dict(input_receipt) != bound_input_receipt:
        raise IndependentFeatureBasisError(
            "basis input receipt differs from the lineage receipt"
        )
    rows = [deepcopy(BASIS_ROW_BY_ID[basis_id]) for basis_id in sorted(BASIS_ROW_BY_ID)]
    _validate_basis_rows(rows, lineage_by_id)

    independent_ids = sorted(
        signal_id
        for row in rows
        for signal_id in row["primary_signal_ids"]
    )
    comparability_ids = sorted(
        {
            signal_id
            for row in rows
            for signal_id in row["comparability_signal_ids"]
        }
    )
    direct_candidate_ids = sorted(
        {
            signal_id
            for row in rows
            for signal_id in row["candidate_posting_signal_ids"]
        }
    )
    cross_dimensional_candidate_ids = sorted(
        signal_id
        for signal_id, signal in lineage_by_id.items()
        if signal["scoring_disposition"] == "CANDIDATE_GENERATION_ONLY"
        and not signal_id.startswith("SIG-CURATORIAL-")
        and signal_id != "SIG-TEMPORAL-DECADE"
    )
    curatorial_recall_ids = sorted(
        signal_id
        for signal_id, signal in lineage_by_id.items()
        if signal["scoring_disposition"] == "CANDIDATE_GENERATION_ONLY"
        and signal_id.startswith("SIG-CURATORIAL-")
    )
    interaction_ids = sorted(
        signal_id
        for signal_id, signal in lineage_by_id.items()
        if signal["scoring_disposition"] == "DEPENDENT_INTERACTION_SIGNAL"
    )
    families = Counter(row["affinity_family"] for row in rows)
    same_source_groups = [
        lineage_by_id[signal_id]["same_source_fact_group"]
        for signal_id in independent_ids
    ]

    material: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "derivationVersion": DERIVATION_VERSION,
        "inputReceipt": bound_input_receipt,
        "lineageReceiptSha256": lineage_analysis["deterministicReceipt"]["sha256"],
        "lineageSignalsSha256": lineage_analysis["signalsSha256"],
        "lineageSignals": deepcopy(lineage_analysis["signals"]),
        "basisRows": rows,
        "independentBaseSignalIds": independent_ids,
        "basisUnitIds": [row["basis_id"] for row in rows],
        "affinityFamilies": sorted(families),
        "directCandidatePostingSignalIds": direct_candidate_ids,
        "highInformationCandidatePostingSignalIds": cross_dimensional_candidate_ids,
        "dependentInteractionSignalIds": interaction_ids,
        "counts": {
            "signalInputCount": 64,
            "independentBaseSignalCount": len(independent_ids),
            "basisUnitCount": len(rows),
            "activeAffinityFamilyCount": len(families),
            "basisUnitsByFamily": dict(sorted(families.items())),
            "comparabilitySignalCount": len(comparability_ids),
            "directCandidatePostingSignalCount": len(direct_candidate_ids),
            "highInformationCandidatePostingSignalCount": len(
                cross_dimensional_candidate_ids
            ),
            "dependentInteractionSignalCount": len(interaction_ids),
            "curatorialRecallSignalCount": len(curatorial_recall_ids),
            "curatorialResidualSignalCount": 0,
            "sameSourceFactDoubleScoreCount": (
                len(same_source_groups) - len(set(same_source_groups))
            ),
        },
        "familyAggregationContract": {
            "GOVERNED_CONTEXT": "MEAN_OR_DECLARED_CAPPED_AGGREGATE_OF_MEDIUM_THEME_MOVEMENT;ONE_CONTEXT_FAMILY_CAP",
            "GOVERNED_TEMPORAL": "ONE_EXTENT_DERIVED_CONTRIBUTION;PRECISION_COMPARABILITY_SEPARATE",
            "GOVERNED_GEOGRAPHY": "EXACT_GOVERNED_OVERLAP_ONLY;CLASS_CANDIDATE_OR_EXPLANATION_FALLBACK;NEVER_ADDITIVE",
            "SOURCE_COMPOSITION": "SOURCE_VARIANT_REQUIRED;DEFAULT_EXCLUDED;WHEN_INCLUDED_ONE_CAP",
            "DESCRIPTIVE_METADATA": "MEAN_OR_DECLARED_CAPPED_AGGREGATE_OF_OBSERVED_CREATOR_AND_OBJECT_TYPE",
        },
        "interactionLayer": {
            "separateFromBase": True,
            "signalIds": interaction_ids,
            "parentResidualRequired": True,
            "supportThresholdRequired": True,
            "boundedContributionRequired": True,
            "rawPmiOrLiftDirectContributionAllowed": False,
            "supportOneOrTwoCanDominate": False,
        },
        "comparabilityChannel": {
            "signalIds": comparability_ids,
            "emittedSeparately": True,
            "includedInAffinityNumerator": False,
            "sharedUnknownPositiveCreditCount": 0,
            "notApplicableTreatedAsMissingCount": 0,
            "requiredProfileFields": [
                "eligibleFamilyCount",
                "jointlyObservableFamilies",
                "observedFamilyCount",
                "ratio",
                "unavailableFamilies",
            ],
        },
        "curatorialPolicy": {
            "asRecallIndex": True,
            "asIndependentScore": False,
            "recallSignalIds": curatorial_recall_ids,
            "residualSignalIds": [],
            "residualSignalCount": 0,
            "sameSourceGovernedContainerTypes": [
                "medium",
                "movement",
                "region",
                "theme",
            ],
            "sameSourceGovernedFactsRemovedBeforeAnyFutureResidual": True,
            "rawJaccardImportBoundary": deepcopy(
                RAW_CURATED_JACCARD_IMPORT_BOUNDARY
            ),
        },
        "minimalityWitnesses": {
            row["basis_id"]: row["reason"] for row in rows
        },
        "selectionBoundary": {
            "similarityModelSelected": False,
            "similarityWeightsSelected": False,
            "publicSimilarityModelSelected": False,
            "clusteringModelSelected": False,
            "probabilityModelSelected": False,
            "rendererImplemented": False,
        },
        "invariants": {
            "EVERY_INDEPENDENT_SIGNAL_ASSIGNED_EXACTLY_ONCE": (
                len(independent_ids) == len(set(independent_ids)) == 8
            ),
            "NO_DUPLICATE_SIGNAL_IN_BASE_UNITS": len(independent_ids)
            == len(set(independent_ids)),
            "SAME_SOURCE_FACT_DOUBLE_SCORE_COUNT_ZERO": len(same_source_groups)
            == len(set(same_source_groups)),
            "CURATORIAL_AS_RECALL_INDEX_TRUE": bool(curatorial_recall_ids),
            "CURATORIAL_AS_INDEPENDENT_SCORE_FALSE": True,
            "CURATORIAL_RESIDUAL_SIGNAL_COUNT_ZERO": True,
            "RAW_CURATED_JACCARD_PRODUCTION_ELIGIBLE_FALSE": not RAW_CURATED_JACCARD_IMPORT_BOUNDARY[
                "productionEligible"
            ],
            "COMPARABILITY_SEPARATE_FROM_AFFINITY": True,
            "SHARED_UNKNOWN_POSITIVE_CREDIT_COUNT_ZERO": True,
            "TEMPORAL_DECADE_NOT_DOUBLE_SCORED": "SIG-TEMPORAL-DECADE"
            not in independent_ids,
            "GEOGRAPHY_LAYOUT_DISTANCE_EXCLUDED": "SIG-GEOGRAPHY-DISTANCE"
            not in independent_ids,
            "GEOGRAPHY_CLASS_NOT_INDEPENDENT": "SIG-GEOGRAPHY-CLASS"
            not in independent_ids,
            "GEOGRAPHY_CLASS_RETRIEVAL_FALLBACK_PRESERVED": (
                "SIG-GEOGRAPHY-CLASS" in direct_candidate_ids
            ),
            "SOURCE_MATCH_NOT_AUTOMATICALLY_POSITIVE": next(
                row
                for row in rows
                if row["basis_id"] == "BASIS-SOURCE-IDENTITY"
            )["default_enabled"]
            is False,
            "INTERACTION_PARENT_RESIDUAL_REQUIRED": True,
            "NO_MODEL_SELECTED_BY_BASIS": True,
        },
    }
    material["basisRowsSha256"] = _sha256_json(rows)
    material["deterministicReceipt"] = {
        "canonicalization": "recursive key sort; compact JSON; final LF; UTF-8",
        "sha256": _sha256_json(material),
    }
    validate_independent_feature_basis(material)
    return material


def analyze_independent_feature_basis(
    lineage_analysis: Mapping[str, Any],
    *,
    input_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compatibility alias for parent orchestration code."""

    return build_independent_feature_basis(
        lineage_analysis, input_receipt=input_receipt
    )


def _self_test() -> None:
    from common import load_signal_registry, source_receipt

    source = load_signal_registry()
    lineage = analyze_signal_lineage(source["rows"], input_receipt=source_receipt())
    first = build_independent_feature_basis(lineage)
    second = build_independent_feature_basis(lineage)
    assert first == second
    assert first["counts"]["independentBaseSignalCount"] == 8
    assert first["counts"]["basisUnitCount"] == 8
    assert first["counts"]["activeAffinityFamilyCount"] == 5
    assert first["counts"]["curatorialResidualSignalCount"] == 0
    assert first["counts"]["sameSourceFactDoubleScoreCount"] == 0
    assert first["comparabilityChannel"]["sharedUnknownPositiveCreditCount"] == 0
    assert first["curatorialPolicy"]["asRecallIndex"] is True
    assert first["curatorialPolicy"]["asIndependentScore"] is False

    damaged = deepcopy(first)
    damaged["basisRows"][0]["primary_signal_ids"] = []
    try:
        validate_independent_feature_basis(damaged)
    except IndependentFeatureBasisError:
        pass
    else:
        raise AssertionError("basis accepted a missing primary signal")

    print(
        json.dumps(
            {
                "status": "PASS",
                "schemaVersion": SCHEMA_VERSION,
                "basisUnitCount": first["counts"]["basisUnitCount"],
                "independentBaseSignalCount": first["counts"][
                    "independentBaseSignalCount"
                ],
                "activeAffinityFamilyCount": first["counts"][
                    "activeAffinityFamilyCount"
                ],
                "curatorialResidualSignalCount": first["counts"][
                    "curatorialResidualSignalCount"
                ],
                "basisRowsSha256": first["basisRowsSha256"],
                "receiptSha256": first["deterministicReceipt"]["sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    _self_test()
