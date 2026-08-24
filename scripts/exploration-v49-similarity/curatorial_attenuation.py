#!/usr/bin/env python3
"""Deterministic curatorial recall/attenuation diagnostics for Round 6.

Curatorial postings remain a recall substrate unless lineage proves residual
information.  This module evaluates CUR-W1..CUR-W6 against a complete public
candidate index, but it never imports or calls an affinity scorer.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import candidate_index


SCHEMA_VERSION = "trace-exploration-curatorial-attenuation/v1"
IMPLEMENTATION_VERSION = "trace-exploration-curatorial-attenuation-2026-08-24"
CURATORIAL_POLICY_IDS = ("CUR-W1", "CUR-W2", "CUR-W3", "CUR-W4", "CUR-W5", "CUR-W6")
W3_BROAD_STOP_RATIOS = (0.25, 0.50, 0.75, 0.90)


class CuratorialAttenuationError(ValueError):
    """Raised when a curatorial policy evaluation is malformed."""


@dataclass(frozen=True)
class CuratorialPolicy:
    policy_id: str
    name: str
    role: str
    weight_rule: str
    raw_membership_scoring_allowed: bool
    residual_only_scoring: bool
    explanation: str


POLICIES = (
    CuratorialPolicy(
        "CUR-W1",
        "GLOBAL_IDF_LIKE",
        "RECALL_AND_DIAGNOSTIC",
        "log((N + alpha) / (df + alpha))",
        False,
        True,
        "Global breadth is measurable, but raw membership supplies no affinity credit.",
    ),
    CuratorialPolicy(
        "CUR-W2",
        "WITHIN_CONTAINER_TYPE_IDF",
        "RECALL_AND_DIAGNOSTIC",
        "log((N_type + alpha) / (df + alpha))",
        False,
        True,
        "Breadth is normalized within a caller-supplied container type.",
    ),
    CuratorialPolicy(
        "CUR-W3",
        "HARD_BROAD_CONTAINER_STOP",
        "BOUNDED_RECALL",
        "retain when df / N <= threshold",
        False,
        True,
        "Threshold sensitivity is emitted at 25%, 50%, 75%, and 90%.",
    ),
    CuratorialPolicy(
        "CUR-W4",
        "CAPPED_CURATORIAL_FAMILY",
        "RESIDUAL_SCORING_SENSITIVITY",
        "min(residual_family_value, family_cap)",
        False,
        True,
        "Only lineage-approved residual information may approach the cap.",
    ),
    CuratorialPolicy(
        "CUR-W5",
        "RARE_AND_BROAD_BOUNDED",
        "RECALL_AND_RESIDUAL_SENSITIVITY",
        "min(weight_cap, idf * min(1, df / rare_support_floor))",
        False,
        True,
        "Both extremely low support and broad support receive bounded weights.",
    ),
    CuratorialPolicy(
        "CUR-W6",
        "LINEAGE_RESIDUAL_ONLY",
        "RESIDUAL_ONLY",
        "use only residual_curated_postings approved by lineage",
        False,
        True,
        "No governed Context or Spacetime source fact receives a second contribution.",
    ),
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256((_canonical_json(value) + "\n").encode("utf-8")).hexdigest()


def _posting_identifier(token: str) -> str:
    identifier = str(token).rsplit("\x1f", 1)[-1].strip()
    if not identifier:
        raise CuratorialAttenuationError("curatorial posting token lacks an identifier")
    return identifier


def _quantile(values: Sequence[int], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _weight_summary(weights: Mapping[str, float]) -> dict[str, float]:
    values = sorted(float(value) for value in weights.values())
    return {
        "weightMin": min(values) if values else 0.0,
        "weightP50": _quantile([int(round(value * 1_000_000)) for value in values], 0.50) / 1_000_000,
        "weightMax": max(values) if values else 0.0,
    }


def _fanout_distribution(
    object_ids: Sequence[str],
    postings: Mapping[str, Sequence[str]],
    active_tokens: Iterable[str],
) -> dict[str, float | int]:
    """Compute exact per-object candidate fanout with compact integer bitsets."""

    ordinals = {object_id: ordinal for ordinal, object_id in enumerate(object_ids)}
    masks: dict[str, int] = {}
    tokens_by_object: dict[str, list[str]] = defaultdict(list)
    active = tuple(sorted(set(active_tokens)))
    for token in active:
        members = postings.get(token)
        if members is None:
            raise CuratorialAttenuationError("active posting token is absent")
        mask = 0
        for object_id in members:
            if object_id not in ordinals:
                raise CuratorialAttenuationError("posting contains an object outside the public index")
            mask |= 1 << ordinals[object_id]
            tokens_by_object[object_id].append(token)
        masks[token] = mask

    counts: list[int] = []
    possible_other_count = max(0, len(object_ids) - 1)
    for object_id in object_ids:
        candidate_mask = 0
        for token in tokens_by_object.get(object_id, ()):
            candidate_mask |= masks[token]
        candidate_mask &= ~(1 << ordinals[object_id])
        counts.append(candidate_mask.bit_count())
    return {
        "candidatePoolP50": _quantile(counts, 0.50),
        "candidatePoolP90": _quantile(counts, 0.90),
        "candidatePoolP95": _quantile(counts, 0.95),
        "candidatePoolP99": _quantile(counts, 0.99),
        "candidatePoolMax": max(counts, default=0),
        "zeroCandidateObjectCount": sum(value == 0 for value in counts),
        "nearFullCandidateObjectCount": sum(
            value >= possible_other_count * 0.95 for value in counts
        ),
        "possibleOtherObjectCount": possible_other_count,
    }


def curatorial_attenuation_policies() -> tuple[dict[str, Any], ...]:
    """Return the frozen six-policy registry used by the evaluator."""

    return tuple(
        {
            "policyId": policy.policy_id,
            "name": policy.name,
            "role": policy.role,
            "weightRule": policy.weight_rule,
            "rawMembershipScoringAllowed": policy.raw_membership_scoring_allowed,
            "residualOnlyScoring": policy.residual_only_scoring,
            "explanation": policy.explanation,
        }
        for policy in POLICIES
    )


def evaluate_curatorial_attenuation(
    index: candidate_index.CandidateIndex,
    *,
    residual_signal_count: int = 0,
    represented_source_fact_container_ids: Iterable[str] = (),
    container_type_by_id: Mapping[str, str] | None = None,
    alpha: float = 1.0,
    family_cap: float = 0.10,
    rare_support_floor: int = 3,
    bounded_weight_cap: float = 4.0,
) -> dict[str, Any]:
    """Evaluate CUR-W1..CUR-W6 over every public object in ``index``.

    The returned rows are flat and deterministic.  ``score_contribution`` is a
    maximum eligible residual-family contribution, never a pair score.  It is
    exactly zero when ``residual_signal_count`` is zero.
    """

    if residual_signal_count < 0:
        raise CuratorialAttenuationError("residual signal count cannot be negative")
    if not isinstance(alpha, (int, float)) or isinstance(alpha, bool) or not math.isfinite(float(alpha)) or alpha <= 0:
        raise CuratorialAttenuationError("alpha must be a finite positive number")
    if not isinstance(family_cap, (int, float)) or isinstance(family_cap, bool) or not 0 < family_cap <= 1:
        raise CuratorialAttenuationError("family cap must be in (0, 1]")
    if rare_support_floor < 1:
        raise CuratorialAttenuationError("rare-support floor must be positive")
    if not isinstance(bounded_weight_cap, (int, float)) or bounded_weight_cap <= 0:
        raise CuratorialAttenuationError("bounded weight cap must be positive")
    n = len(index.object_ids)
    if n == 0:
        raise CuratorialAttenuationError("curatorial evaluation requires a nonempty public index")

    raw_postings = dict(index.curated_postings)
    residual_postings = dict(index.residual_curated_postings)
    raw_ids = {_posting_identifier(token): token for token in raw_postings}
    residual_ids = {_posting_identifier(token): token for token in residual_postings}
    if len(raw_ids) != len(raw_postings) or len(residual_ids) != len(residual_postings):
        raise CuratorialAttenuationError("curatorial posting identifiers are not unique")

    represented = {str(value).strip() for value in represented_source_fact_container_ids if str(value).strip()}
    residual_identifier_set = set(residual_ids)
    duplicate_parent_ids = tuple(sorted(represented & residual_identifier_set))
    same_source_parent_duplication_failures = len(duplicate_parent_ids)
    has_residual_scoring_basis = residual_signal_count > 0 and bool(residual_postings)
    score_contribution = float(family_cap) if has_residual_scoring_basis else 0.0

    global_weights = {
        token: math.log((n + alpha) / (len(members) + alpha))
        for token, members in raw_postings.items()
    }
    type_by_id = {
        identifier: str((container_type_by_id or {}).get(identifier, "UNSPECIFIED")).strip() or "UNSPECIFIED"
        for identifier in raw_ids
    }
    type_members: dict[str, set[str]] = defaultdict(set)
    for identifier, token in raw_ids.items():
        type_members[type_by_id[identifier]].update(raw_postings[token])
    within_type_weights = {
        token: math.log(
            (len(type_members[type_by_id[_posting_identifier(token)]]) + alpha)
            / (len(members) + alpha)
        )
        for token, members in raw_postings.items()
    }
    bounded_weights = {
        token: min(
            float(bounded_weight_cap),
            global_weights[token] * min(1.0, len(members) / rare_support_floor),
        )
        for token, members in raw_postings.items()
    }
    residual_weights = {
        token: math.log((n + alpha) / (len(members) + alpha))
        for token, members in residual_postings.items()
    }

    configurations: list[dict[str, Any]] = [
        {
            "policy": POLICIES[0],
            "sensitivityId": "CUR-W1-GLOBAL",
            "postings": raw_postings,
            "activeTokens": tuple(raw_postings),
            "weights": global_weights,
            "broadStopRatio": None,
        },
        {
            "policy": POLICIES[1],
            "sensitivityId": "CUR-W2-WITHIN-TYPE",
            "postings": raw_postings,
            "activeTokens": tuple(raw_postings),
            "weights": within_type_weights,
            "broadStopRatio": None,
        },
    ]
    for ratio in W3_BROAD_STOP_RATIOS:
        active = tuple(
            token for token, members in raw_postings.items() if len(members) / n <= ratio
        )
        configurations.append(
            {
                "policy": POLICIES[2],
                "sensitivityId": f"CUR-W3-STOP-{int(ratio * 100):02d}",
                "postings": raw_postings,
                "activeTokens": active,
                "weights": {token: 1.0 for token in active},
                "broadStopRatio": ratio,
            }
        )
    configurations.extend(
        (
            {
                "policy": POLICIES[3],
                "sensitivityId": "CUR-W4-CAP",
                "postings": raw_postings,
                "activeTokens": tuple(raw_postings),
                "weights": {token: min(value, family_cap) for token, value in global_weights.items()},
                "broadStopRatio": None,
            },
            {
                "policy": POLICIES[4],
                "sensitivityId": "CUR-W5-RARE-BROAD-BOUNDED",
                "postings": raw_postings,
                "activeTokens": tuple(raw_postings),
                "weights": bounded_weights,
                "broadStopRatio": None,
            },
            {
                "policy": POLICIES[5],
                "sensitivityId": "CUR-W6-RESIDUAL-ONLY",
                "postings": residual_postings,
                "activeTokens": tuple(residual_postings),
                "weights": residual_weights,
                "broadStopRatio": None,
            },
        )
    )

    fanout_cache: dict[tuple[str, tuple[str, ...]], dict[str, float | int]] = {}
    rows: list[dict[str, Any]] = []
    for configuration in configurations:
        policy: CuratorialPolicy = configuration["policy"]
        postings: Mapping[str, Sequence[str]] = configuration["postings"]
        active_tokens = tuple(sorted(configuration["activeTokens"]))
        posting_space = "RESIDUAL" if policy.policy_id == "CUR-W6" else "RAW_RECALL"
        cache_key = (posting_space, active_tokens)
        if cache_key not in fanout_cache:
            fanout_cache[cache_key] = _fanout_distribution(index.object_ids, postings, active_tokens)
        fanout = fanout_cache[cache_key]
        weights = _weight_summary(configuration["weights"])
        stopped_count = len(postings) - len(active_tokens)
        raw_score_allowed = policy.raw_membership_scoring_allowed
        row_score_contribution = score_contribution if policy.policy_id in {"CUR-W4", "CUR-W5", "CUR-W6"} else 0.0
        broad_dominance_failures = int(
            raw_score_allowed
            or row_score_contribution > family_cap
            or (residual_signal_count == 0 and row_score_contribution != 0.0)
        )
        rows.append(
            {
                "policy_id": policy.policy_id,
                "sensitivity_id": configuration["sensitivityId"],
                "policy_name": policy.name,
                "role": policy.role,
                "weight_rule": policy.weight_rule,
                "posting_space": posting_space,
                "alpha": float(alpha),
                "broad_stop_ratio": configuration["broadStopRatio"] if configuration["broadStopRatio"] is not None else "N/A",
                "rare_support_floor": rare_support_floor,
                "family_cap": float(family_cap),
                "container_posting_count": len(postings),
                "active_posting_count": len(active_tokens),
                "stopped_posting_count": stopped_count,
                "candidate_pool_p50": fanout["candidatePoolP50"],
                "candidate_pool_p90": fanout["candidatePoolP90"],
                "candidate_pool_p95": fanout["candidatePoolP95"],
                "candidate_pool_p99": fanout["candidatePoolP99"],
                "candidate_pool_max": fanout["candidatePoolMax"],
                "zero_candidate_object_count": fanout["zeroCandidateObjectCount"],
                "near_full_candidate_object_count": fanout["nearFullCandidateObjectCount"],
                "weight_min": weights["weightMin"],
                "weight_p50": weights["weightP50"],
                "weight_max": weights["weightMax"],
                "score_contribution": row_score_contribution,
                "score_contribution_basis": "LINEAGE_RESIDUAL_CAP" if row_score_contribution else "NONE",
                "residual_signal_count": residual_signal_count,
                "raw_membership_scoring_allowed": False,
                "same_source_parent_duplication_failures": same_source_parent_duplication_failures,
                "broad_dominance_failures": broad_dominance_failures,
                "randomness_affects_candidate_set": False,
                "historical_relation": False,
                "semantic_relation": False,
                "probability": False,
            }
        )

    broad_failure_count = sum(int(row["broad_dominance_failures"]) for row in rows)
    deterministic_material = {
        "schemaVersion": SCHEMA_VERSION,
        "implementationVersion": IMPLEMENTATION_VERSION,
        "candidateIndexSha256": index.index_sha256,
        "rows": rows,
        "duplicateParentContainerIds": duplicate_parent_ids,
    }
    result = {
        **deterministic_material,
        "policyCount": len(POLICIES),
        "sensitivityRowCount": len(rows),
        "w3SensitivityCount": len(W3_BROAD_STOP_RATIOS),
        "publicObjectCount": n,
        "fullIndexEvaluated": True,
        "rawCuratorialPostingCount": len(raw_postings),
        "residualCuratorialPostingCount": len(residual_postings),
        "residualSignalCount": residual_signal_count,
        "scoreContribution": score_contribution,
        "curatorialAsRecallIndex": bool(raw_postings),
        "curatorialAsIndependentScore": has_residual_scoring_basis,
        "sameSourceParentDuplicationFailures": same_source_parent_duplication_failures,
        "broadDominanceFailures": broad_failure_count,
        "randomnessAffectsCandidateSet": False,
        "evaluationSha256": _sha256(deterministic_material),
    }
    validate_curatorial_attenuation_result(result)
    return result


def curatorial_attenuation_rows(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_rows = result.get("rows")
    if not isinstance(raw_rows, Sequence) or isinstance(raw_rows, (str, bytes, bytearray)):
        raise CuratorialAttenuationError("curatorial result rows are absent")
    return [dict(row) for row in raw_rows]


def validate_curatorial_attenuation_result(result: Mapping[str, Any]) -> None:
    rows = curatorial_attenuation_rows(result)
    if result.get("policyCount") != 6 or tuple(dict.fromkeys(row["policy_id"] for row in rows)) != CURATORIAL_POLICY_IDS:
        raise CuratorialAttenuationError("CUR-W1..CUR-W6 policy coverage is incomplete")
    w3_rows = [row for row in rows if row["policy_id"] == "CUR-W3"]
    if tuple(row["broad_stop_ratio"] for row in w3_rows) != W3_BROAD_STOP_RATIOS:
        raise CuratorialAttenuationError("CUR-W3 sensitivity grid changed")
    if result.get("sensitivityRowCount") != 9 or len(rows) != 9:
        raise CuratorialAttenuationError("curatorial sensitivity output must contain nine rows")
    if result.get("residualSignalCount") == 0:
        if result.get("scoreContribution") != 0.0 or any(row["score_contribution"] != 0.0 for row in rows):
            raise CuratorialAttenuationError("zero residual signals received curatorial score credit")
        if result.get("curatorialAsIndependentScore"):
            raise CuratorialAttenuationError("zero residual signals were declared an independent score")
    if result.get("sameSourceParentDuplicationFailures") != len(result.get("duplicateParentContainerIds", ())):
        raise CuratorialAttenuationError("same-source parent duplication summary disagrees")
    if result.get("broadDominanceFailures") != sum(int(row["broad_dominance_failures"]) for row in rows):
        raise CuratorialAttenuationError("broad-dominance summary disagrees")
    if result.get("randomnessAffectsCandidateSet"):
        raise CuratorialAttenuationError("curatorial candidate diagnostic depends on randomness")


def _sample_record(object_id: str, ordinal: int, curated: Sequence[str]) -> dict[str, Any]:
    token = lambda value: {"id": value, "label": value}
    return {
        "objectId": object_id,
        "medium": [token(f"M-{ordinal}")],
        "theme": [token(f"T-{ordinal}")],
        "movement_context": [],
        "decade": [token(f"D-{ordinal}")],
        "geography": [token(f"G-{ordinal}")],
        "curated_container": [token(value) for value in curated],
        "source": token(f"S-{ordinal}"),
        "object_type": token(f"OT-{ordinal}"),
        "creator": token(f"CR-{ordinal}"),
        "startYear": 1900 + ordinal,
        "endYear": 1900 + ordinal,
        "temporalPrecision": "year",
        "geographyMappingStates": [token("MAPPED")],
        "geographyClasses": [token("COUNTRY")],
        "geographyQualified": False,
        "multiRegion": False,
    }


def self_test() -> dict[str, Any]:
    records = [
        _sample_record(
            f"SURF-CUR-{ordinal}",
            ordinal,
            ("BROAD", "NARROW") if ordinal <= 2 else ("BROAD",),
        )
        for ordinal in range(1, 6)
    ]
    index = candidate_index.build_exploration_candidate_index(records)
    result = evaluate_curatorial_attenuation(index, residual_signal_count=0)
    if result["broadDominanceFailures"] or result["sameSourceParentDuplicationFailures"]:
        raise AssertionError("bounded curatorial diagnostic reported a scoring failure")
    if result["scoreContribution"] != 0.0 or result["curatorialAsIndependentScore"]:
        raise AssertionError("zero-residual curatorial substrate received scoring credit")
    w6 = next(row for row in result["rows"] if row["policy_id"] == "CUR-W6")
    if w6["candidate_pool_max"] != 0 or w6["zero_candidate_object_count"] != len(records):
        raise AssertionError("empty residual curation produced candidate fanout")
    return {
        "status": "PASS",
        "policyCount": result["policyCount"],
        "sensitivityRowCount": result["sensitivityRowCount"],
        "w3SensitivityCount": result["w3SensitivityCount"],
        "scoreContribution": result["scoreContribution"],
        "evaluationSha256": result["evaluationSha256"],
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
