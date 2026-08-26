"""Normative ordinal association model for TRACE v49 Round 14.

The pair is a validation unit for local spatial coherence.  It is not emitted as
a typed, causal, directional, or statistical historical relation.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterable


METHOD_VERSION = "trace-generic-association-rubric-v1"
GENERIC_TYPES = (
    "TEMPORAL_HISTORICAL_CONTEXT",
    "INSTITUTIONAL_PROFESSIONAL",
    "CULTURAL_DISCURSIVE",
    "ECONOMIC_COMMERCIAL",
    "SOCIAL_IDENTITY",
    "MATERIAL_TECHNOLOGICAL",
    "CIRCULATION_EXCHANGE",
    "PRACTICE_PRODUCTION",
)
EVIDENCE_STATUSES = (
    "EXTERNALLY_SUPPORTED",
    "SOURCE_SUPPORTED",
    "QUALIFIED",
    "INSUFFICIENT",
)
STRENGTHS = ("WEAK", "MODERATE", "STRONG")
CONFIDENCES = ("LOW", "MODERATE", "HIGH")
DIMENSIONS = ("D1", "D2", "D3", "D4", "D5", "D6", "D7")

STRENGTH_RANK = {value: index for index, value in enumerate(STRENGTHS)}
CONFIDENCE_RANK = {value: index for index, value in enumerate(CONFIDENCES)}


@dataclass(frozen=True)
class CalibrationCase:
    assessment_id: str
    node_a: str
    node_b: str
    calibration_stratum: str
    hard_negative: bool
    period_band: str
    source_family: str
    design_history_domain: str
    primary_generic_type: str
    secondary_generic_type: str | None
    historical_scope: str
    context_scope: str
    rubric_dimensions: dict[str, int]
    cooccurrence_only: bool
    qualification_required: bool
    evidence_refs: tuple[str, ...]
    expected_direct_pass: bool
    expected_skip_one_pass: bool
    qualification: str
    decision_reason: str


@dataclass(frozen=True)
class ThresholdPolicy:
    configuration_id: str
    neighbourhood: str
    minimum_strength: str
    minimum_confidence: str
    allowed_statuses: tuple[str, ...]
    selected: bool = False


DIRECT_POLICIES = (
    ThresholdPolicy("ADJ-01", "DIRECT", "STRONG", "HIGH", ("EXTERNALLY_SUPPORTED",)),
    ThresholdPolicy("ADJ-02", "DIRECT", "STRONG", "MODERATE", ("EXTERNALLY_SUPPORTED", "SOURCE_SUPPORTED")),
    ThresholdPolicy("ADJ-03", "DIRECT", "MODERATE", "MODERATE", ("EXTERNALLY_SUPPORTED", "SOURCE_SUPPORTED"), True),
    ThresholdPolicy("ADJ-04", "DIRECT", "MODERATE", "LOW", ("EXTERNALLY_SUPPORTED", "SOURCE_SUPPORTED", "QUALIFIED")),
    ThresholdPolicy("ADJ-05", "DIRECT", "WEAK", "LOW", ("EXTERNALLY_SUPPORTED", "SOURCE_SUPPORTED", "QUALIFIED")),
)
SKIP_POLICIES = (
    ThresholdPolicy("SKIP-01", "SKIP_ONE", "STRONG", "HIGH", ("EXTERNALLY_SUPPORTED",)),
    ThresholdPolicy("SKIP-02", "SKIP_ONE", "STRONG", "MODERATE", ("EXTERNALLY_SUPPORTED", "SOURCE_SUPPORTED")),
    ThresholdPolicy("SKIP-03", "SKIP_ONE", "MODERATE", "MODERATE", ("EXTERNALLY_SUPPORTED", "SOURCE_SUPPORTED"), True),
    ThresholdPolicy("SKIP-04", "SKIP_ONE", "MODERATE", "LOW", ("EXTERNALLY_SUPPORTED", "SOURCE_SUPPORTED", "QUALIFIED")),
    ThresholdPolicy("SKIP-05", "SKIP_ONE", "WEAK", "LOW", ("EXTERNALLY_SUPPORTED", "SOURCE_SUPPORTED", "QUALIFIED")),
)
SELECTED_DIRECT_POLICY = next(policy for policy in DIRECT_POLICIES if policy.selected)
SELECTED_SKIP_POLICY = next(policy for policy in SKIP_POLICIES if policy.selected)


def validate_case(case: CalibrationCase) -> None:
    if case.primary_generic_type not in GENERIC_TYPES:
        raise ValueError("UNKNOWN_PRIMARY_GENERIC_TYPE")
    if case.secondary_generic_type is not None:
        if case.secondary_generic_type not in GENERIC_TYPES:
            raise ValueError("UNKNOWN_SECONDARY_GENERIC_TYPE")
        if case.secondary_generic_type == case.primary_generic_type:
            raise ValueError("DUPLICATE_GENERIC_TYPE")
    if set(case.rubric_dimensions) != set(DIMENSIONS):
        raise ValueError("RUBRIC_DIMENSION_SET")
    if any(value not in (0, 1, 2) for value in case.rubric_dimensions.values()):
        raise ValueError("RUBRIC_DIMENSION_RANGE")
    if case.calibration_stratum not in {"CLEAR_POSITIVE", "BORDERLINE", "NEGATIVE"}:
        raise ValueError("UNKNOWN_CALIBRATION_STRATUM")
    if not case.evidence_refs:
        raise ValueError("EVIDENCE_REFERENCE_REQUIRED")
    if case.qualification_required and not case.qualification.strip():
        raise ValueError("QUALIFICATION_REQUIRED")


def _channels(evidence_rows: Iterable[dict[str, Any]]) -> tuple[set[str], set[str]]:
    external: set[str] = set()
    archive: set[str] = set()
    for row in evidence_rows:
        channel = row["evidence_channel"]
        if channel == "EXTERNAL_SCHOLARSHIP":
            external.add(row["source_id"])
        elif channel == "ARCHIVE_SOURCE":
            archive.add(row["source_id"])
        elif channel != "NEGATIVE_CONTROL":
            raise ValueError("UNKNOWN_EVIDENCE_CHANNEL")
    return external, archive


def hard_gate_pass(case: CalibrationCase) -> bool:
    d = case.rubric_dimensions
    return not case.cooccurrence_only and d["D1"] >= 1 and d["D5"] >= 1 and d["D7"] >= 1


def association_strength(case: CalibrationCase) -> str:
    d = case.rubric_dimensions
    if not hard_gate_pass(case):
        return "WEAK"
    if d["D1"] == 2 and d["D2"] >= 1 and d["D6"] >= 1:
        return "STRONG"
    if d["D6"] >= 1:
        return "MODERATE"
    return "WEAK"


def evidence_confidence(case: CalibrationCase) -> str:
    d = case.rubric_dimensions
    if not hard_gate_pass(case):
        return "LOW"
    if d["D3"] >= 1 and d["D4"] == 2 and d["D6"] == 2 and d["D7"] == 2:
        return "HIGH"
    if d["D4"] >= 1 and d["D6"] >= 1 and d["D7"] >= 1 and (d["D2"] >= 1 or d["D3"] >= 1):
        return "MODERATE"
    return "LOW"


def evidence_status(case: CalibrationCase, evidence_rows: Iterable[dict[str, Any]]) -> str:
    external, archive = _channels(evidence_rows)
    if not hard_gate_pass(case) or not (external or archive):
        return "INSUFFICIENT"
    if case.qualification_required:
        return "QUALIFIED"
    if external:
        return "EXTERNALLY_SUPPORTED"
    if archive:
        return "SOURCE_SUPPORTED"
    return "INSUFFICIENT"


def policy_pass(strength: str, confidence: str, status: str, policy: ThresholdPolicy) -> bool:
    return (
        status in policy.allowed_statuses
        and STRENGTH_RANK[strength] >= STRENGTH_RANK[policy.minimum_strength]
        and CONFIDENCE_RANK[confidence] >= CONFIDENCE_RANK[policy.minimum_confidence]
    )


def assess(case: CalibrationCase, evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    validate_case(case)
    if {row["evidence_id"] for row in evidence_rows} != set(case.evidence_refs):
        raise ValueError("EVIDENCE_BINDING_MISMATCH")
    external, archive = _channels(evidence_rows)
    strength = association_strength(case)
    confidence = evidence_confidence(case)
    status = evidence_status(case, evidence_rows)
    direct = policy_pass(strength, confidence, status, SELECTED_DIRECT_POLICY)
    skip = policy_pass(strength, confidence, status, SELECTED_SKIP_POLICY)
    active = direct or skip
    redirect_targets = sorted({row["stable_url"] for row in evidence_rows if row["support_role"] == "ASSOCIATION_SUPPORT" and row["stable_url"]})
    if active and not redirect_targets:
        raise ValueError("ACTIVE_REDIRECT_REQUIRED")
    return {
        "assessmentId": case.assessment_id,
        "nodeA": case.node_a,
        "nodeB": case.node_b,
        "primaryGenericType": case.primary_generic_type,
        "secondaryGenericType": case.secondary_generic_type,
        "historicalScope": case.historical_scope,
        "contextScope": case.context_scope,
        "associationStrength": strength,
        "evidenceConfidence": confidence,
        "evidenceStatus": status,
        "rubricDimensions": dict(sorted(case.rubric_dimensions.items())),
        "externalSourceRefs": sorted(external),
        "archiveSourceRefs": sorted(archive),
        "directNeighbourPass": direct,
        "skipOnePass": skip,
        "qualification": case.qualification,
        "decisionReason": case.decision_reason,
        "methodVersion": METHOD_VERSION,
        "activeForProximity": active,
        "redirectTargets": redirect_targets,
        "calibrationStratum": case.calibration_stratum,
        "hardNegative": case.hard_negative,
        "cooccurrenceOnly": case.cooccurrence_only,
    }


def perturb(case: CalibrationCase, dimension: str, delta: int) -> CalibrationCase:
    if dimension not in DIMENSIONS or delta not in (-1, 1):
        raise ValueError("INVALID_SENSITIVITY_PERTURBATION")
    dimensions = dict(case.rubric_dimensions)
    dimensions[dimension] = min(2, max(0, dimensions[dimension] + delta))
    return replace(case, rubric_dimensions=dimensions)


def confusion(expected: list[bool], actual: list[bool]) -> dict[str, int]:
    if len(expected) != len(actual):
        raise ValueError("CONFUSION_LENGTH_MISMATCH")
    tp = sum(want and got for want, got in zip(expected, actual, strict=True))
    fp = sum(not want and got for want, got in zip(expected, actual, strict=True))
    tn = sum(not want and not got for want, got in zip(expected, actual, strict=True))
    fn = sum(want and not got for want, got in zip(expected, actual, strict=True))
    return {"true_positive": tp, "false_positive": fp, "true_negative": tn, "false_negative": fn}
