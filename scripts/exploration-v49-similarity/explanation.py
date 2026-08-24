#!/usr/bin/env python3
"""Deterministic explanation contract for every Exploration candidate result."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


SCHEMA_VERSION = "trace-exploration-candidate-explanation/v1"
IMPLEMENTATION_VERSION = "trace-exploration-explanation-2026-08-24"
PUBLIC_ID_PATTERN = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
INTERACTION_ID_PATTERN = re.compile(r"^EXP:INTERACTION:[0-9a-f]{64}$")
SOURCE_TREATMENTS = frozenset({"SOURCE-0", "SOURCE-1", "SOURCE-2", "SOURCE-3", "SOURCE-4"})
INTERACTION_METHODS = frozenset({
    "CAPPED_INTERACTION_BONUS",
    "INFORMATION_RESIDUAL_CONTRIBUTION",
    "LOG_LIKELIHOOD_INTERACTION_CONTRIBUTION",
})
UUID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
PRIVATE_PATTERN = re.compile(r"(?:\bFOL-|\bTRN-OBJ-|\bTRTREE|\bTRBRANCH|https?://|file://)", re.IGNORECASE)


class ExplanationError(ValueError):
    """Raised when a candidate result lacks a safe explanation path."""


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _safe_text(value: Any, field: str, *, allow_blank: bool = False) -> str:
    text = str(value if value is not None else "").strip()
    if not text and not allow_blank:
        raise ExplanationError(f"{field} must be nonblank")
    if UUID_PATTERN.search(text) or PRIVATE_PATTERN.search(text):
        raise ExplanationError(f"{field} contains a private identifier or URL")
    return text


def _public_id(value: Any, field: str) -> str:
    identifier = _safe_text(value, field)
    if not PUBLIC_ID_PATTERN.fullmatch(identifier):
        raise ExplanationError(f"{field} is not a public surface ID")
    return identifier


def _profile_mapping(profile: Any) -> Mapping[str, Any]:
    if isinstance(profile, Mapping):
        return profile
    as_dict = getattr(profile, "as_dict", None)
    if callable(as_dict):
        value = as_dict()
        if isinstance(value, Mapping):
            return value
    raise ExplanationError("affinity profile must be a mapping or expose as_dict()")


def _bounded_number(value: Any, field: str, *, minimum: float = 0.0, maximum: float | None = None) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        raise ExplanationError(f"{field} must be a finite number")
    number = float(value)
    if number < minimum or (maximum is not None and number > maximum):
        raise ExplanationError(f"{field} is outside its permitted range")
    return number


def _normalize_contribution(raw: Mapping[str, Any], *, kind: str) -> dict[str, Any]:
    row = {str(key): value for key, value in raw.items()}
    family = _safe_text(row.get("family", "diagnostic"), f"{kind}.family")
    if "numerator" not in row and "support" in row:
        row["numerator"] = row["support"]
    has_ratio = "numerator" in row and "denominator" in row
    has_source = bool(str(row.get("sourceIdentity", "")).strip())
    if not has_ratio and not has_source:
        raise ExplanationError(f"{kind} contribution lacks numerator/denominator or source identity")
    if has_ratio:
        numerator = _bounded_number(row["numerator"], f"{kind}.numerator")
        denominator = _bounded_number(row["denominator"], f"{kind}.denominator")
        if denominator <= 0:
            # BM25-style saturation can make a weighted numerator larger than
            # its raw query-weight denominator; the emitted contribution is
            # still explicitly bounded by the model profile.
            raise ExplanationError(f"{kind} contribution has an invalid ratio")
        row["numerator"] = numerator
        row["denominator"] = denominator
    if has_source:
        row["sourceIdentity"] = _safe_text(row["sourceIdentity"], f"{kind}.sourceIdentity")
    row["family"] = family
    if kind == "affinity":
        row["sameSourceFactGroup"] = _safe_text(
            row.get("sameSourceFactGroup"), f"{kind}.sameSourceFactGroup"
        )
    row["historicalRelation"] = False
    row["semanticRelation"] = False
    return row


def build_exploration_candidate_explanation(
    *,
    query_id: str,
    candidate_id: str,
    candidate_title: str,
    profile: Any,
    retrieval_reasons: Iterable[Mapping[str, Any]],
    method_version: str,
    analysis_run_id: str,
    research_release_id: str,
    research_release_sha256: str,
    context_projection_sha256: str,
    spacetime_projection_sha256: str,
    candidate_index_sha256: str,
    broad_container_attenuation: Mapping[str, Any] | None = None,
    source_bias_notes: Iterable[str] = (),
    ignored_duplicate_signals: Iterable[str] = (),
) -> dict[str, Any]:
    """Build an auditable no-score-only explanation payload."""

    query = _public_id(query_id, "queryId")
    candidate = _public_id(candidate_id, "candidateId")
    if query == candidate:
        raise ExplanationError("candidate explanation cannot target the query object")
    title = _safe_text(candidate_title, "candidateTitle")
    profile_row = _profile_mapping(profile)
    if str(profile_row.get("candidateId", candidate)) != candidate:
        raise ExplanationError("profile candidate identity conflicts with explanation")

    comparability = profile_row.get("comparability")
    if not isinstance(comparability, Mapping):
        raise ExplanationError("profile lacks a comparability channel")
    ratio = _bounded_number(comparability.get("ratio"), "comparability.ratio", maximum=1.0)
    observed = int(comparability.get("observedFamilyCount", -1))
    eligible = int(comparability.get("eligibleFamilyCount", -1))
    if observed < 0 or eligible <= 0 or observed > eligible or not math.isclose(ratio, observed / eligible):
        raise ExplanationError("comparability numerator/denominator/ratio do not reconcile")

    retrieval = tuple(
        sorted(
            (_normalize_contribution(row, kind="retrieval") for row in retrieval_reasons),
            key=lambda row: (str(row.get("reasonType", "")), str(row["family"]), str(row.get("token", ""))),
        )
    )
    affinity = tuple(
        sorted(
            (
                _normalize_contribution(row, kind="affinity")
                for row in profile_row.get("contributions", ())
            ),
            key=lambda row: (str(row["family"]), str(row.get("field", "")), str(row.get("signalId", ""))),
        )
    )
    if not retrieval:
        raise ExplanationError("candidate explanation lacks a retrieval reason")
    if not affinity:
        raise ExplanationError("candidate explanation lacks an affinity evidence path")
    source_fact_groups = [str(row["sameSourceFactGroup"]) for row in affinity]
    if len(source_fact_groups) != len(set(source_fact_groups)):
        raise ExplanationError("one source fact group contributes more than once")
    distinctive = tuple(
        sorted(
            (dict(row) for row in profile_row.get("distinctiveFeatures", ())),
            key=lambda row: (str(row.get("family", "")), str(row.get("field", ""))),
        )
    )
    unavailable = tuple(sorted({_safe_text(value, "unavailableFamily") for value in profile_row.get("unavailableFamilies", ())}))
    duplicates = tuple(
        sorted(
            {
                _safe_text(value, "ignoredDuplicateSignal")
                for value in (*profile_row.get("ignoredDuplicateSignals", ()), *ignored_duplicate_signals)
            }
        )
    )
    interactions = tuple(
        sorted(
            (dict(row) for row in profile_row.get("interactions", ())),
            key=lambda row: (str(row.get("interactionId", "")), str(row.get("method", ""))),
        )
    )
    for interaction in interactions:
        if interaction.get("separateFromParentContributions") is not True:
            raise ExplanationError("interaction explanation repeats or obscures parent contributions")
        if int(interaction.get("support", 0)) <= 0 or int(interaction.get("supportThreshold", 0)) <= 0:
            raise ExplanationError("interaction explanation lacks support and threshold")
        denominator = int(interaction.get("denominator", 0))
        if denominator <= 0 or int(interaction["support"]) > denominator:
            raise ExplanationError("interaction explanation lacks a valid denominator")
        if set(str(value) for value in interaction.get("objectIds", ())) != {query, candidate}:
            raise ExplanationError("interaction explanation is not bound to this public pair")
        registry_sha = str(interaction.get("registrySha256", ""))
        if not SHA256_PATTERN.fullmatch(registry_sha):
            raise ExplanationError("interaction explanation lacks a registry hash")
        context_sha = str(interaction.get("interactionContextSha256", ""))
        if not SHA256_PATTERN.fullmatch(context_sha):
            raise ExplanationError("interaction explanation lacks a trusted-context hash")

    interaction_registry_sha256 = (
        str(interactions[0]["registrySha256"]) if interactions else None
    )
    interaction_context_sha256 = (
        str(interactions[0]["interactionContextSha256"]) if interactions else None
    )
    if any(
        row["registrySha256"] != interaction_registry_sha256
        or row["interactionContextSha256"] != interaction_context_sha256
        for row in interactions
    ):
        raise ExplanationError("interaction evidence mixes registries or trusted contexts")

    hashes = {
        "researchReleaseSha256": research_release_sha256,
        "contextProjectionSha256": context_projection_sha256,
        "spacetimeProjectionSha256": spacetime_projection_sha256,
        "candidateIndexSha256": candidate_index_sha256,
    }
    for field, digest in hashes.items():
        if not SHA256_PATTERN.fullmatch(str(digest)):
            raise ExplanationError(f"{field} must be a lowercase SHA-256 digest")
    attenuation = dict(broad_container_attenuation or {})
    attenuation.setdefault("curatorialUse", "RECALL_SUBSTRATE_ONLY")
    attenuation.setdefault("rawCuratedJaccardScoringAllowed", False)
    if attenuation.get("rawCuratedJaccardScoringAllowed") is not False:
        raise ExplanationError("raw curated Jaccard cannot be scoring evidence")
    source_treatment = _safe_text(profile_row.get("sourceTreatment", "SOURCE-0"), "sourceTreatment")
    if source_treatment in {"SOURCE-0", "SOURCE-2", "SOURCE-4"} and any(
        row["family"] == "source" and float(row.get("contribution", 0.0)) > 0
        for row in affinity
    ):
        raise ExplanationError("source-excluded treatment contains positive source affinity")

    raw_units = profile_row.get("familyContributionUnits")
    raw_shares = profile_row.get("familyContributionShares")
    if not isinstance(raw_units, Mapping) or not isinstance(raw_shares, Mapping):
        raise ExplanationError("profile lacks family contribution units/shares")
    contribution_units = {
        _safe_text(family, "familyContributionUnits.family"): _bounded_number(
            value,
            f"familyContributionUnits.{family}",
            maximum=1.0,
        )
        for family, value in raw_units.items()
    }
    contribution_shares = {
        _safe_text(family, "familyContributionShares.family"): _bounded_number(
            value,
            f"familyContributionShares.{family}",
            maximum=1.0,
        )
        for family, value in raw_shares.items()
    }
    if set(contribution_units) != set(contribution_shares):
        raise ExplanationError("family contribution units/shares use different families")
    unit_total = sum(contribution_units.values())
    share_total = sum(contribution_shares.values())
    diagnostic_score = profile_row.get("diagnosticScore")
    if diagnostic_score is not None and not math.isclose(
        unit_total,
        float(diagnostic_score),
        rel_tol=0.0,
        abs_tol=2e-12,
    ):
        raise ExplanationError("family contribution units do not reconcile to diagnostic score")
    if unit_total > 0:
        if not math.isclose(share_total, 1.0, rel_tol=0.0, abs_tol=2e-12):
            raise ExplanationError("family contribution shares do not sum to one")
        if any(
            not math.isclose(
                contribution_shares[family],
                value / unit_total,
                rel_tol=0.0,
                abs_tol=2e-12,
            )
            for family, value in contribution_units.items()
        ):
            raise ExplanationError("family contribution shares do not reconcile to units")
    elif share_total != 0:
        raise ExplanationError("zero contribution units have nonzero shares")

    payload = {
        "schemaVersion": SCHEMA_VERSION,
        "queryId": query,
        "candidateId": candidate,
        "candidateTitle": title,
        "retrievalReasons": list(retrieval),
        "affinityContributions": list(affinity),
        "distinctiveFeatures": list(distinctive),
        "ignoredDuplicateSignals": list(duplicates),
        "unavailableFamilies": list(unavailable),
        "comparability": {
            "observedFamilyCount": observed,
            "eligibleFamilyCount": eligible,
            "ratio": ratio,
        },
        "familyContributionUnits": dict(sorted(contribution_units.items())),
        "familyContributionShares": dict(sorted(contribution_shares.items())),
        "broadContainerAttenuation": attenuation,
        "sourceBiasNotes": sorted({_safe_text(value, "sourceBiasNote") for value in source_bias_notes}),
        "interactionEvidence": list(interactions),
        "interactionRegistrySha256": interaction_registry_sha256,
        "interactionContextSha256": interaction_context_sha256,
        "methodId": _safe_text(profile_row.get("modelId"), "modelId"),
        "sourceTreatment": source_treatment,
        "methodVersion": _safe_text(method_version, "methodVersion"),
        "analysisRunId": _safe_text(analysis_run_id, "analysisRunId"),
        "researchReleaseId": _safe_text(research_release_id, "researchReleaseId"),
        **hashes,
        "diagnosticScore": diagnostic_score,
        "scoreOnlyResult": False,
        "probability": False,
        "historicalRelation": False,
        "semanticRelation": False,
    }
    payload["explanationSha256"] = hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()
    validate_explanation(payload)
    return payload


def _mapping_rows(value: Any, field: str, *, nonempty: bool = False) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ExplanationError(f"{field} must be an array")
    rows = tuple(value)
    if nonempty and not rows:
        raise ExplanationError(f"{field} must be nonempty")
    if any(not isinstance(row, Mapping) for row in rows):
        raise ExplanationError(f"{field} rows must be mappings")
    return rows


def _validate_standalone_evidence_row(
    row: Mapping[str, Any],
    *,
    field: str,
    affinity: bool,
) -> None:
    _safe_text(row.get("family"), f"{field}.family")
    if row.get("historicalRelation") is not False or row.get("semanticRelation") is not False:
        raise ExplanationError(f"{field} crossed an interpretation boundary")
    has_ratio = "numerator" in row and "denominator" in row
    has_source = bool(str(row.get("sourceIdentity", "")).strip())
    if not has_ratio and not has_source:
        raise ExplanationError(f"{field} lacks numerator/denominator or source identity")
    if has_ratio:
        _bounded_number(row["numerator"], f"{field}.numerator")
        denominator = _bounded_number(row["denominator"], f"{field}.denominator")
        if denominator <= 0:
            raise ExplanationError(f"{field} denominator must be positive")
    if has_source:
        _safe_text(row["sourceIdentity"], f"{field}.sourceIdentity")
    if affinity:
        _safe_text(row.get("sameSourceFactGroup"), f"{field}.sameSourceFactGroup")
        _safe_text(row.get("signalId"), f"{field}.signalId")


def _validate_m7_formula(row: Mapping[str, Any], field: str) -> None:
    if row.get("basis") != "BM25F_LIKE_FIELDED_RETRIEVAL":
        return
    if row.get("formula") != "BM25F_LIKE_FIELD_SATURATION":
        raise ExplanationError(f"{field} lacks its declared BM25F-like formula")
    terms = _mapping_rows(row.get("queryTermStatistics"), f"{field}.queryTermStatistics", nonempty=True)
    matched_count = 0
    for ordinal, term in enumerate(terms):
        _safe_text(term.get("featureId"), f"{field}.queryTermStatistics[{ordinal}].featureId")
        df = term.get("documentFrequency")
        if isinstance(df, bool) or not isinstance(df, int) or df <= 0:
            raise ExplanationError(f"{field} contains an invalid document frequency")
        _bounded_number(term.get("idf"), f"{field}.queryTermStatistics[{ordinal}].idf")
        if not isinstance(term.get("matched"), bool):
            raise ExplanationError(f"{field} query-term match flag must be boolean")
        matched_count += int(term["matched"])
    if int(row.get("matchedQueryTermCount", -1)) != matched_count:
        raise ExplanationError(f"{field} matched query-term count does not reconcile")
    document_length = row.get("documentFieldLength")
    if isinstance(document_length, bool) or not isinstance(document_length, int) or document_length <= 0:
        raise ExplanationError(f"{field} has an invalid document field length")
    average_length = _bounded_number(
        row.get("averageDocumentFieldLength"),
        f"{field}.averageDocumentFieldLength",
    )
    if average_length <= 0:
        raise ExplanationError(f"{field} average document field length must be positive")
    k1 = _bounded_number(row.get("k1"), f"{field}.k1")
    b = _bounded_number(row.get("b"), f"{field}.b", maximum=1.0)
    length_normalization = _bounded_number(
        row.get("lengthNormalization"),
        f"{field}.lengthNormalization",
    )
    saturation = _bounded_number(row.get("saturation"), f"{field}.saturation")
    if k1 <= 0 or saturation <= 0:
        raise ExplanationError(f"{field} saturation must be positive")
    if _bounded_number(row.get("declaredFamilyWeight"), f"{field}.declaredFamilyWeight") <= 0:
        raise ExplanationError(f"{field} family weight must be positive")
    expected_length_normalization = 1.0 - b + b * document_length / average_length
    expected_saturation = (k1 + 1.0) / (1.0 + k1 * expected_length_normalization)
    query_weight = sum(float(term["idf"]) for term in terms)
    matched_weight = sum(float(term["idf"]) for term in terms if term["matched"])
    expected_numerator = matched_weight * expected_saturation
    expected_denominator = query_weight
    expected_contribution = min(
        1.0,
        expected_numerator / expected_denominator if expected_denominator else 0.0,
    )
    checks = (
        (length_normalization, expected_length_normalization, "lengthNormalization"),
        (saturation, expected_saturation, "saturation"),
        (float(row["numerator"]), expected_numerator, "numerator"),
        (float(row["denominator"]), expected_denominator, "denominator"),
        (float(row.get("contribution", -1.0)), expected_contribution, "contribution"),
    )
    for observed, expected, label in checks:
        if not math.isclose(observed, expected, rel_tol=0.0, abs_tol=2e-12):
            raise ExplanationError(f"{field} {label} does not reconcile to BM25F metadata")


def validate_explanation(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Revalidate a serialized explanation without relying on its builder."""

    if not isinstance(payload, Mapping):
        raise ExplanationError("explanation must be a mapping")
    required = {
        "queryId",
        "candidateId",
        "candidateTitle",
        "retrievalReasons",
        "affinityContributions",
        "distinctiveFeatures",
        "ignoredDuplicateSignals",
        "unavailableFamilies",
        "comparability",
        "familyContributionUnits",
        "familyContributionShares",
        "broadContainerAttenuation",
        "sourceBiasNotes",
        "interactionEvidence",
        "interactionRegistrySha256",
        "interactionContextSha256",
        "methodId",
        "sourceTreatment",
        "methodVersion",
        "analysisRunId",
        "researchReleaseId",
        "researchReleaseSha256",
        "contextProjectionSha256",
        "spacetimeProjectionSha256",
        "candidateIndexSha256",
        "scoreOnlyResult",
        "probability",
        "historicalRelation",
        "semanticRelation",
        "explanationSha256",
    }
    if required - set(payload):
        raise ExplanationError(f"explanation lacks required fields: {sorted(required - set(payload))}")
    if payload.get("schemaVersion") != SCHEMA_VERSION:
        raise ExplanationError("explanation schema version is not supported")
    if any(payload.get(field) is not False for field in ("scoreOnlyResult", "probability", "historicalRelation", "semanticRelation")):
        raise ExplanationError("explanation crossed an interpretation boundary")
    query_id = _public_id(payload.get("queryId"), "queryId")
    candidate_id = _public_id(payload.get("candidateId"), "candidateId")
    if query_id == candidate_id:
        raise ExplanationError("candidate explanation cannot target the query object")
    for field in (
        "candidateTitle",
        "methodId",
        "sourceTreatment",
        "methodVersion",
        "analysisRunId",
        "researchReleaseId",
    ):
        _safe_text(payload.get(field), field)
    source_treatment = str(payload["sourceTreatment"])
    if source_treatment not in SOURCE_TREATMENTS:
        raise ExplanationError("sourceTreatment is outside the declared policy grid")
    for field in (
        "researchReleaseSha256",
        "contextProjectionSha256",
        "spacetimeProjectionSha256",
        "candidateIndexSha256",
    ):
        if not SHA256_PATTERN.fullmatch(str(payload.get(field, ""))):
            raise ExplanationError(f"{field} must be a lowercase SHA-256 digest")

    retrieval = _mapping_rows(payload.get("retrievalReasons"), "retrievalReasons", nonempty=True)
    affinity = _mapping_rows(payload.get("affinityContributions"), "affinityContributions", nonempty=True)
    for ordinal, row in enumerate(retrieval):
        _validate_standalone_evidence_row(
            row,
            field=f"retrievalReasons[{ordinal}]",
            affinity=False,
        )
    source_fact_groups: list[str] = []
    for ordinal, row in enumerate(affinity):
        field = f"affinityContributions[{ordinal}]"
        _validate_standalone_evidence_row(row, field=field, affinity=True)
        source_fact_groups.append(str(row["sameSourceFactGroup"]))
        if str(payload["methodId"]) == "M7":
            _validate_m7_formula(row, field)
    if len(source_fact_groups) != len(set(source_fact_groups)):
        raise ExplanationError("one source fact group contributes more than once")

    comparability = payload.get("comparability")
    if not isinstance(comparability, Mapping):
        raise ExplanationError("comparability must be a mapping")
    observed = comparability.get("observedFamilyCount")
    eligible = comparability.get("eligibleFamilyCount")
    if (
        isinstance(observed, bool)
        or not isinstance(observed, int)
        or isinstance(eligible, bool)
        or not isinstance(eligible, int)
        or observed < 0
        or eligible <= 0
        or observed > eligible
    ):
        raise ExplanationError("comparability counts are invalid")
    ratio = _bounded_number(comparability.get("ratio"), "comparability.ratio", maximum=1.0)
    if not math.isclose(ratio, observed / eligible, rel_tol=0.0, abs_tol=1e-12):
        raise ExplanationError("comparability numerator/denominator/ratio do not reconcile")
    unavailable_raw = payload.get("unavailableFamilies")
    if not isinstance(unavailable_raw, Sequence) or isinstance(unavailable_raw, (str, bytes, bytearray)):
        raise ExplanationError("unavailableFamilies must be an array")
    unavailable = tuple(_safe_text(value, "unavailableFamily") for value in unavailable_raw)
    if len(unavailable) != len(set(unavailable)) or len(unavailable) != eligible - observed:
        raise ExplanationError("unavailable families do not reconcile to comparability counts")

    raw_units = payload.get("familyContributionUnits")
    raw_shares = payload.get("familyContributionShares")
    if not isinstance(raw_units, Mapping) or not isinstance(raw_shares, Mapping):
        raise ExplanationError("family contribution units/shares must be mappings")
    units = {
        _safe_text(family, "familyContributionUnits.family"): _bounded_number(
            value,
            f"familyContributionUnits.{family}",
            maximum=1.0,
        )
        for family, value in raw_units.items()
    }
    shares = {
        _safe_text(family, "familyContributionShares.family"): _bounded_number(
            value,
            f"familyContributionShares.{family}",
            maximum=1.0,
        )
        for family, value in raw_shares.items()
    }
    if set(units) != set(shares):
        raise ExplanationError("family contribution units/shares use different families")
    unit_total = sum(units.values())
    diagnostic_score = payload.get("diagnosticScore")
    if diagnostic_score is not None:
        score = _bounded_number(diagnostic_score, "diagnosticScore", maximum=1.0)
        if not math.isclose(unit_total, score, rel_tol=0.0, abs_tol=2e-12):
            raise ExplanationError("family contribution units do not reconcile to diagnostic score")
    share_total = sum(shares.values())
    if unit_total > 0:
        if not math.isclose(share_total, 1.0, rel_tol=0.0, abs_tol=2e-12):
            raise ExplanationError("family contribution shares do not sum to one")
        if any(
            not math.isclose(shares[family], value / unit_total, rel_tol=0.0, abs_tol=2e-12)
            for family, value in units.items()
        ):
            raise ExplanationError("family contribution shares do not reconcile to units")
    elif share_total != 0:
        raise ExplanationError("zero contribution units have nonzero shares")

    attenuation = payload.get("broadContainerAttenuation")
    if not isinstance(attenuation, Mapping):
        raise ExplanationError("broadContainerAttenuation must be a mapping")
    if (
        attenuation.get("curatorialUse") != "RECALL_SUBSTRATE_ONLY"
        or attenuation.get("rawCuratedJaccardScoringAllowed") is not False
    ):
        raise ExplanationError("raw curated evidence crossed the scoring boundary")
    if source_treatment in {"SOURCE-0", "SOURCE-2", "SOURCE-4"} and any(
        str(row.get("family")) == "source"
        and _bounded_number(row.get("contribution", 0.0), "source.contribution") > 0
        for row in affinity
    ):
        raise ExplanationError("source-excluded treatment contains positive source affinity")

    interactions = _mapping_rows(payload.get("interactionEvidence"), "interactionEvidence")
    top_registry = payload.get("interactionRegistrySha256")
    top_context = payload.get("interactionContextSha256")
    if interactions:
        if not SHA256_PATTERN.fullmatch(str(top_registry or "")):
            raise ExplanationError("interactionRegistrySha256 is invalid")
        if not SHA256_PATTERN.fullmatch(str(top_context or "")):
            raise ExplanationError("interactionContextSha256 is invalid")
    elif top_registry is not None or top_context is not None:
        raise ExplanationError("interaction provenance hashes exist without interaction evidence")
    interaction_ids: list[str] = []
    aggregate_bonus: float | None = None
    emitted_residual = 0.0
    for ordinal, row in enumerate(interactions):
        field = f"interactionEvidence[{ordinal}]"
        interaction_id = str(row.get("interactionId", ""))
        if not INTERACTION_ID_PATTERN.fullmatch(interaction_id):
            raise ExplanationError(f"{field} interaction ID is not registry-derived")
        interaction_ids.append(interaction_id)
        if row.get("method") not in INTERACTION_METHODS:
            raise ExplanationError(f"{field} method is unsupported")
        support = row.get("support")
        threshold = row.get("supportThreshold")
        denominator = row.get("denominator")
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (support, threshold, denominator)):
            raise ExplanationError(f"{field} support contract must use integers")
        if support <= 0 or threshold <= 0 or denominator <= 0 or support > denominator:
            raise ExplanationError(f"{field} support/threshold/denominator are invalid")
        if threshold not in {2, 3, 5, 10, 20}:
            raise ExplanationError(f"{field} support threshold is outside the declared grid")
        if tuple(str(value) for value in row.get("objectIds", ())) != (query_id, candidate_id):
            raise ExplanationError(f"{field} is not bound to this ordered public pair")
        if row.get("registrySha256") != top_registry or row.get("interactionContextSha256") != top_context:
            raise ExplanationError(f"{field} provenance hash conflicts with the explanation")
        parents = tuple(str(value) for value in row.get("parentSignalIds", ()))
        if not parents or len(parents) != len(set(parents)) or any(not value.startswith("SIG-") for value in parents):
            raise ExplanationError(f"{field} has invalid parent-signal lineage")
        if source_treatment in {"SOURCE-0", "SOURCE-2", "SOURCE-4"} and any(
            value.startswith("SIG-SOURCE-") for value in parents
        ):
            raise ExplanationError(f"{field} violates the source-treatment boundary")
        if (
            row.get("separateFromParentContributions") is not True
            or row.get("parentContributionRepeated") is not False
            or row.get("aggregateResidualNormalized") is not True
            or row.get("positiveExcessAssociationRequired") is not True
            or row.get("rareMeansImportant") is not False
        ):
            raise ExplanationError(f"{field} crossed its residual/lineage boundary")
        cap = _bounded_number(row.get("cap"), f"{field}.cap", maximum=1.0)
        residual = _bounded_number(row.get("residualScore"), f"{field}.residualScore", maximum=cap)
        raw_residual = _bounded_number(row.get("rawResidualScore"), f"{field}.rawResidualScore", maximum=cap)
        if residual > 0 and row.get("positiveExcessAssociationObserved") is not True:
            raise ExplanationError(f"{field} adds a bonus without positive excess association")
        if not isinstance(row.get("positiveExcessAssociationObserved"), bool):
            raise ExplanationError(f"{field} positive-association flag is not boolean")
        row_aggregate = _bounded_number(row.get("aggregateBonus"), f"{field}.aggregateBonus", maximum=1.0)
        if aggregate_bonus is None:
            aggregate_bonus = row_aggregate
        elif row_aggregate != aggregate_bonus:
            raise ExplanationError("interaction rows disagree on aggregate bonus")
        emitted_residual += residual
    if len(interaction_ids) != len(set(interaction_ids)):
        raise ExplanationError("interaction evidence contains duplicate registry rows")
    if interactions and not math.isclose(
        emitted_residual,
        aggregate_bonus,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ExplanationError("interaction residual rows do not sum exactly to aggregate bonus")

    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    if UUID_PATTERN.search(text) or PRIVATE_PATTERN.search(text):
        raise ExplanationError("explanation contains a private identifier or URL")
    without_hash = dict(payload)
    digest = str(without_hash.pop("explanationSha256"))
    if digest != hashlib.sha256(_canonical_json_bytes(without_hash)).hexdigest():
        raise ExplanationError("explanation hash does not bind its deterministic payload")
    return {
        "schemaVersion": "trace-exploration-explanation-validation/v1",
        "explanationSha256": digest,
        "retrievalReasonCount": len(retrieval),
        "affinityContributionCount": len(affinity),
        "sameSourceFactGroupCount": len(source_fact_groups),
        "familyContributionShareCount": len(shares),
        "familyContributionSharesReconciled": True,
        "interactionEvidenceCount": len(interactions),
        "comparabilityReconciled": True,
        "sourceTreatmentBoundaryPass": True,
        "rawCuratedScoringBoundaryPass": True,
        "interactionPairBindingPass": True,
        "semanticValidationPass": True,
    }


def unexplained_result_count(results: Iterable[Mapping[str, Any]]) -> int:
    failures = 0
    for result in results:
        try:
            validate_explanation(result)
        except (ExplanationError, TypeError, ValueError):
            failures += 1
    return failures


def self_test() -> dict[str, Any]:
    digest = "a" * 64
    profile = {
        "candidateId": "SURF-E2",
        "modelId": "M5",
        "sourceTreatment": "SOURCE-0",
        "comparability": {"observedFamilyCount": 4, "eligibleFamilyCount": 5, "ratio": 0.8},
        "familyContributionUnits": {"context": 0.5},
        "familyContributionShares": {"context": 1.0},
        "contributions": [{"family": "context", "signalId": "SIG-CONTEXT-MEDIUM", "sameSourceFactGroup": "SOURCE_FACT_GOVERNED_CONTEXT_MEDIUM", "numerator": 1, "denominator": 2}],
        "distinctiveFeatures": [],
        "ignoredDuplicateSignals": ["SIG-CONTEXT-SAME-MEDIUM"],
        "unavailableFamilies": ["source"],
        "interactions": [],
        "diagnosticScore": 0.5,
    }
    result = build_exploration_candidate_explanation(
        query_id="SURF-E1",
        candidate_id="SURF-E2",
        candidate_title="Test candidate",
        profile=profile,
        retrieval_reasons=[{"reasonType": "DIRECT_APPROVED_POSTING", "family": "context", "support": 2, "denominator": 10}],
        method_version=IMPLEMENTATION_VERSION,
        analysis_run_id="EXP-RUN-TEST",
        research_release_id="v49-test",
        research_release_sha256=digest,
        context_projection_sha256=digest,
        spacetime_projection_sha256=digest,
        candidate_index_sha256=digest,
    )
    validation_receipt = validate_explanation(result)

    def rehash(value: dict[str, Any]) -> dict[str, Any]:
        value.pop("explanationSha256", None)
        value["explanationSha256"] = hashlib.sha256(
            _canonical_json_bytes(value)
        ).hexdigest()
        return value

    m7_contribution = {
        "family": "context",
        "field": "medium",
        "signalId": "SIG-CONTEXT-MEDIUM",
        "sameSourceFactGroup": "SOURCE_FACT_GOVERNED_CONTEXT_MEDIUM",
        "basis": "BM25F_LIKE_FIELDED_RETRIEVAL",
        "formula": "BM25F_LIKE_FIELD_SATURATION",
        "numerator": 1.0,
        "denominator": 1.5,
        "contribution": 2.0 / 3.0,
        "matchedFeatureIds": ["context\\x1fmedium\\x1fMEDIUM-A"],
        "queryTermStatistics": [
            {"featureId": "MEDIUM-A", "documentFrequency": 2, "idf": 1.0, "matched": True},
            {"featureId": "MEDIUM-B", "documentFrequency": 3, "idf": 0.5, "matched": False},
        ],
        "matchedQueryTermCount": 1,
        "documentFieldLength": 2,
        "averageDocumentFieldLength": 2.0,
        "k1": 1.2,
        "b": 0.75,
        "lengthNormalization": 1.0,
        "saturation": 1.0,
        "declaredFamilyWeight": 1.0,
    }
    m7_profile = {
        "candidateId": "SURF-E4",
        "modelId": "M7",
        "sourceTreatment": "SOURCE-0",
        "comparability": {"observedFamilyCount": 1, "eligibleFamilyCount": 1, "ratio": 1.0},
        "familyContributionUnits": {"context": 2.0 / 3.0},
        "familyContributionShares": {"context": 1.0},
        "contributions": [m7_contribution],
        "distinctiveFeatures": [],
        "ignoredDuplicateSignals": [],
        "unavailableFamilies": [],
        "interactions": [],
        "diagnosticScore": 2.0 / 3.0,
    }
    m7_result = build_exploration_candidate_explanation(
        query_id="SURF-E1",
        candidate_id="SURF-E4",
        candidate_title="M7 test candidate",
        profile=m7_profile,
        retrieval_reasons=[{
            "reasonType": "DIRECT_APPROVED_POSTING",
            "family": "context",
            "support": 2,
            "denominator": 10,
        }],
        method_version=IMPLEMENTATION_VERSION,
        analysis_run_id="EXP-RUN-M7-TEST",
        research_release_id="v49-test",
        research_release_sha256=digest,
        context_projection_sha256=digest,
        spacetime_projection_sha256=digest,
        candidate_index_sha256=digest,
    )
    validate_explanation(m7_result)

    adversaries: list[dict[str, Any]] = []
    empty_retrieval = json.loads(json.dumps(result))
    empty_retrieval["retrievalReasons"] = []
    adversaries.append(rehash(empty_retrieval))
    empty_affinity = json.loads(json.dumps(result))
    empty_affinity["affinityContributions"] = []
    adversaries.append(rehash(empty_affinity))
    broken_comparability = json.loads(json.dumps(result))
    broken_comparability["comparability"]["ratio"] = 0.6
    adversaries.append(rehash(broken_comparability))
    duplicate_source_fact = json.loads(json.dumps(result))
    duplicate_source_fact["affinityContributions"].append(
        dict(duplicate_source_fact["affinityContributions"][0])
    )
    adversaries.append(rehash(duplicate_source_fact))
    raw_curated = json.loads(json.dumps(result))
    raw_curated["broadContainerAttenuation"]["rawCuratedJaccardScoringAllowed"] = True
    adversaries.append(rehash(raw_curated))
    source_leak = json.loads(json.dumps(result))
    source_leak["affinityContributions"].append({
        "family": "source",
        "signalId": "SIG-SOURCE-NAME",
        "sameSourceFactGroup": "SOURCE_FACT_PUBLIC_SOURCE_IDENTITY",
        "numerator": 1.0,
        "denominator": 1.0,
        "contribution": 0.5,
        "historicalRelation": False,
        "semanticRelation": False,
    })
    adversaries.append(rehash(source_leak))
    forged_interaction = json.loads(json.dumps(result))
    forged_interaction["interactionRegistrySha256"] = "b" * 64
    forged_interaction["interactionContextSha256"] = "c" * 64
    forged_interaction["interactionEvidence"] = [{
        "interactionId": "EXP:INTERACTION:" + "d" * 64,
        "method": "CAPPED_INTERACTION_BONUS",
        "support": 2,
        "supportThreshold": 2,
        "denominator": 4,
        "parentSignalIds": ["SIG-CONTEXT-MEDIUM", "SIG-CONTEXT-THEME"],
        "residualScore": 0.05,
        "rawResidualScore": 0.05,
        "aggregateBonus": 0.05,
        "aggregateResidualNormalized": True,
        "cap": 0.10,
        "registrySha256": "b" * 64,
        "interactionContextSha256": "c" * 64,
        "objectIds": ["SURF-E1", "SURF-E3"],
        "parentContributionRepeated": False,
        "separateFromParentContributions": True,
        "rareMeansImportant": False,
        "positiveExcessAssociationRequired": True,
        "positiveExcessAssociationObserved": True,
    }]
    adversaries.append(rehash(forged_interaction))
    m7_formula_mutations = (
        ("lengthNormalization", 0.2),
        ("saturation", 0.2),
        ("numerator", 0.1),
        ("denominator", 0.9),
        ("contribution", 0.9),
    )
    for field, value in m7_formula_mutations:
        forged_m7 = json.loads(json.dumps(m7_result))
        forged_m7["affinityContributions"][0][field] = value
        adversaries.append(rehash(forged_m7))
    forged_artifact_rejected_count = unexplained_result_count(adversaries)
    if forged_artifact_rejected_count != len(adversaries):
        raise AssertionError("standalone validator accepted a self-hashed forged artifact")
    return {
        "status": "PASS",
        "explanationContractReady": True,
        "unexplainedResultCount": unexplained_result_count([result]),
        "explanationSha256": result["explanationSha256"],
        "semanticValidationReceipt": validation_receipt,
        "selfHashedForgedArtifactCount": len(adversaries),
        "selfHashedForgedArtifactRejectedCount": forged_artifact_rejected_count,
        "m7FormulaForgeryCount": len(m7_formula_mutations),
        "m7FormulaForgeryRejectedCount": len(m7_formula_mutations),
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
