#!/usr/bin/env python3
"""Bounded interaction statistics and residual contributions.

Observed cells are diagnostics derived from approved independent dimensions.
They never replace parent features, and any optional scoring contribution is a
separate, support-shrunk residual with an explicit cap.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from itertools import product
from types import MappingProxyType
from typing import Any


SCHEMA_VERSION = "trace-exploration-interaction-statistics/v1"
IMPLEMENTATION_VERSION = "trace-exploration-interaction-statistics-2026-08-24"
INTERACTION_METHODS = (
    "RAW_SUPPORT",
    "CONDITIONAL_SUPPORT",
    "LIFT",
    "PMI",
    "NORMALIZED_PMI",
    "LOG_LIKELIHOOD_RATIO",
    "SMOOTHED_LIFT",
    "SHRUNK_NORMALIZED_PMI",
)
SUPPORT_THRESHOLDS = (2, 3, 5, 10, 20)
CANDIDATE_INTERACTION_POLICY = MappingProxyType({
    "policyId": "HIGH_INFORMATION_OBSERVED_CELL_V1",
    "minimumSupportInclusive": 5,
    "maximumSupportInclusive": 20,
    "minimumShrunkNormalizedPmiInclusive": 0.10,
    "statistic": "shrunkNormalizedPmi",
    "candidateAllowedDimensionSpecs": (
        ("creator", "medium"),
        ("medium", "theme"),
        ("object_type", "medium"),
        ("theme", "movement_context"),
    ),
    "sourceRowsAllowed": False,
    "callerSelectedTokensAllowed": False,
})
PAIR_SPECS = (
    ("medium", "theme"),
    ("medium", "movement_context"),
    ("theme", "movement_context"),
    ("medium", "decade"),
    ("theme", "decade"),
    ("medium", "geography"),
    ("theme", "geography"),
    ("decade", "geography"),
    ("source", "medium"),
    ("source", "theme"),
    ("source", "decade"),
    ("source", "geography"),
    ("object_type", "medium"),
    ("creator", "medium"),
)
TRIPLE_SPECS = (
    ("medium", "theme", "decade"),
    ("medium", "theme", "geography"),
    ("theme", "decade", "geography"),
    ("medium", "decade", "geography"),
    ("source", "theme", "decade"),
    ("source", "medium", "geography"),
)
FIELD_SIGNAL_IDS = {
    "medium": "SIG-CONTEXT-MEDIUM",
    "theme": "SIG-CONTEXT-THEME",
    "movement_context": "SIG-CONTEXT-MOVEMENT",
    "decade": "SIG-TEMPORAL-DECADE",
    "geography": "SIG-GEOGRAPHY-ASSIGNMENT",
    "source": "SIG-SOURCE-NAME",
    "object_type": "SIG-DESCRIPTIVE-OBJECT-TYPE",
    "creator": "SIG-DESCRIPTIVE-CREATOR",
}
PUBLIC_ID_PATTERN = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_TRUST_SEAL = object()


class InteractionError(ValueError):
    """Raised when an observed-cell statistic is malformed."""


@dataclass(frozen=True)
class TrustedInteractionContext:
    registry_sha256: str
    public_object_ids: tuple[str, ...]
    interactions_by_id: Mapping[str, Mapping[str, Any]]
    object_interaction_ids: Mapping[str, frozenset[str]]
    context_sha256: str
    _seal: Any = field(repr=False, compare=False, default=None)
    _validation_fingerprint: tuple[Any, ...] = field(
        repr=False,
        compare=False,
        default=(),
    )


UNKNOWN_PATTERN = re.compile(
    r"^(?:unknown(?:;.*)?|not[ _-]?governed|no[ _-]?published[ _-]?movement[ _-]?context)$",
    re.IGNORECASE,
)


def _json_compatible(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return [_json_compatible(item) for item in sorted(value)]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_compatible(item) for item in value]
    return value


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(_deep_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_deep_freeze(item) for item in value)
    return value


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            _json_compatible(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _member_id(value: Any) -> str:
    if isinstance(value, Mapping):
        identifier = str(value.get("id", "")).strip()
    else:
        identifier = str(value if value is not None else "").strip()
    if not identifier:
        raise InteractionError("interaction dimension contains a blank value")
    return identifier


def _observed_member(value: Any) -> bool:
    label = (
        str(value.get("label", value.get("id", ""))).strip()
        if isinstance(value, Mapping)
        else str(value if value is not None else "").strip()
    )
    return bool(label) and not UNKNOWN_PATTERN.fullmatch(label)


def _values(record: Mapping[str, Any], field: str) -> tuple[str, ...]:
    raw = record.get(field)
    if field in {"source", "object_type", "creator"}:
        raw = [raw]
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise InteractionError(f"{field} must use its normalized Round 5 shape")
    return tuple(
        sorted(
            {
                _member_id(value)
                for value in raw
                if value is not None and _observed_member(value)
            }
        )
    )


def _xlogx(value: float, expected: float) -> float:
    return value * math.log(value / expected) if value > 0 and expected > 0 else 0.0


def pair_statistics(
    *,
    support: int,
    left_support: int,
    right_support: int,
    denominator: int,
    alpha: float = 0.5,
    shrinkage: float = 5.0,
) -> dict[str, float | int]:
    if denominator <= 0:
        raise InteractionError("interaction denominator must be positive")
    if not (0 <= support <= min(left_support, right_support) <= denominator):
        raise InteractionError("pair support/marginals do not form a valid table")
    if alpha <= 0 or shrinkage <= 0:
        raise InteractionError("smoothing and shrinkage parameters must be positive")
    n11 = support
    n10 = left_support - support
    n01 = right_support - support
    n00 = denominator - left_support - right_support + support
    if n00 < 0:
        raise InteractionError("pair contingency table has a negative cell")

    observed = ((n11, n10), (n01, n00))
    row_totals = (left_support, denominator - left_support)
    column_totals = (right_support, denominator - right_support)
    ll = 0.0
    for row in range(2):
        for column in range(2):
            expected = row_totals[row] * column_totals[column] / denominator
            ll += _xlogx(observed[row][column], expected)
    llr = 2 * ll

    joint_rate = support / denominator
    left_rate = left_support / denominator
    right_rate = right_support / denominator
    lift = joint_rate / (left_rate * right_rate) if left_rate and right_rate else 0.0
    pmi = math.log(lift) if lift > 0 else 0.0
    npmi_denominator = -math.log(joint_rate) if 0 < joint_rate < 1 else 0.0
    npmi = pmi / npmi_denominator if npmi_denominator else 0.0
    smoothed_joint = (support + alpha) / (denominator + 4 * alpha)
    smoothed_left = (left_support + 2 * alpha) / (denominator + 4 * alpha)
    smoothed_right = (right_support + 2 * alpha) / (denominator + 4 * alpha)
    smoothed_lift = smoothed_joint / (smoothed_left * smoothed_right)
    shrink_factor = support / (support + shrinkage)
    shrunk_npmi = max(-1.0, min(1.0, npmi * shrink_factor))
    return {
        "rawSupport": support,
        "leftSupport": left_support,
        "rightSupport": right_support,
        "denominator": denominator,
        "leftConditionalRate": support / left_support if left_support else 0.0,
        "rightConditionalRate": support / right_support if right_support else 0.0,
        "lift": lift,
        "pmiNats": pmi,
        "normalizedPmi": max(-1.0, min(1.0, npmi)),
        "logLikelihoodRatio": llr,
        "smoothedLift": smoothed_lift,
        "shrunkNormalizedPmi": shrunk_npmi,
        "shrinkFactor": shrink_factor,
    }


def higher_order_statistics(
    *,
    support: int,
    marginal_supports: Sequence[int],
    denominator: int,
    alpha: float = 0.5,
    shrinkage: float = 5.0,
) -> dict[str, float | int]:
    if len(marginal_supports) < 3:
        raise InteractionError("higher-order interaction requires at least three marginals")
    if denominator <= 0 or support < 0 or any(value < support or value > denominator for value in marginal_supports):
        raise InteractionError("higher-order support/marginals are invalid")
    expected_rate = math.prod(value / denominator for value in marginal_supports)
    observed_rate = support / denominator
    lift = observed_rate / expected_rate if expected_rate else 0.0
    pmi = math.log(lift) if lift > 0 else 0.0
    npmi_denominator = -math.log(observed_rate) if 0 < observed_rate < 1 else 0.0
    npmi = pmi / npmi_denominator if npmi_denominator else 0.0
    smoothed_observed = (support + alpha) / (denominator + 2 * alpha)
    smoothed_marginals = [
        (value + alpha) / (denominator + 2 * alpha) for value in marginal_supports
    ]
    smoothed_lift = smoothed_observed / math.prod(smoothed_marginals)
    expected_count = expected_rate * denominator
    complement_observed = denominator - support
    complement_expected = denominator - expected_count
    llr = 2 * (
        _xlogx(float(support), expected_count)
        + _xlogx(float(complement_observed), complement_expected)
    )
    shrink_factor = support / (support + shrinkage)
    return {
        "rawSupport": support,
        "marginalSupports": list(marginal_supports),
        "denominator": denominator,
        "lift": lift,
        "pmiNats": pmi,
        "normalizedPmi": max(-1.0, min(1.0, npmi)),
        "logLikelihoodRatio": llr,
        "smoothedLift": smoothed_lift,
        "shrunkNormalizedPmi": max(-1.0, min(1.0, npmi * shrink_factor)),
        "shrinkFactor": shrink_factor,
    }


def build_observed_interaction_registry(
    records: Sequence[Mapping[str, Any]],
    *,
    pair_specs: Sequence[Sequence[str]] = PAIR_SPECS,
    triple_specs: Sequence[Sequence[str]] = TRIPLE_SPECS,
    minimum_support: int = 1,
) -> dict[str, Any]:
    """Build only observed bounded cells; no Cartesian zero-cell matrix."""

    if minimum_support < 1:
        raise InteractionError("minimum support must be positive")
    normalized_pair_specs = tuple(tuple(str(value) for value in spec) for spec in pair_specs)
    normalized_triple_specs = tuple(tuple(str(value) for value in spec) for spec in triple_specs)
    if (
        len(normalized_pair_specs) != len(set(normalized_pair_specs))
        or set(normalized_pair_specs) - set(PAIR_SPECS)
    ):
        raise InteractionError("pair specs must be a unique declared subset")
    if (
        len(normalized_triple_specs) != len(set(normalized_triple_specs))
        or set(normalized_triple_specs) - set(TRIPLE_SPECS)
    ):
        raise InteractionError("triple specs must be a unique declared subset")
    object_ids = [str(record.get("objectId", "")) for record in records]
    if len(object_ids) != len(set(object_ids)):
        raise InteractionError("interaction input contains duplicate objects")
    normalized = [
        {field: _values(record, field) for field in FIELD_SIGNAL_IDS}
        for record in records
    ]
    def count_cells(specs: Sequence[Sequence[str]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for raw_spec in specs:
            fields = tuple(str(value) for value in raw_spec)
            if len(fields) not in {2, 3} or len(set(fields)) != len(fields):
                raise InteractionError("interaction specs must contain two or three distinct fields")
            if any(field not in FIELD_SIGNAL_IDS for field in fields):
                raise InteractionError("interaction spec references an unsupported field")
            eligible_records = [
                record for record in normalized if all(record[field] for field in fields)
            ]
            denominator = len(eligible_records)
            if denominator == 0:
                continue
            one_dimensional: Counter[tuple[str, str]] = Counter()
            for record in eligible_records:
                for field in fields:
                    one_dimensional.update((field, value) for value in record[field])
            counts: Counter[tuple[str, ...]] = Counter()
            for record in eligible_records:
                values = [record[field] for field in fields]
                counts.update(product(*values))
            for cell, support in sorted(counts.items()):
                if support < minimum_support:
                    continue
                marginals = [one_dimensional[(field, value)] for field, value in zip(fields, cell)]
                stats = (
                    pair_statistics(
                        support=support,
                        left_support=marginals[0],
                        right_support=marginals[1],
                        denominator=denominator,
                    )
                    if len(fields) == 2
                    else higher_order_statistics(
                        support=support,
                        marginal_supports=marginals,
                        denominator=denominator,
                    )
                )
                identity_material = "\x1f".join(
                    f"{field}={value}" for field, value in zip(fields, cell)
                )
                rows.append({
                    "interactionId": "EXP:INTERACTION:" + hashlib.sha256(identity_material.encode("utf-8")).hexdigest(),
                    "dimensions": list(fields),
                    "valueIds": list(cell),
                    "parentSignalIds": [FIELD_SIGNAL_IDS[field] for field in fields],
                    "support": support,
                    "eligiblePopulationCount": denominator,
                    "statistics": stats,
                    "interactionOnly": True,
                    "parentContributionRepeated": False,
                    "historicalRelation": False,
                    "semanticRelation": False,
                })
        rows.sort(key=lambda row: (tuple(row["dimensions"]), tuple(row["valueIds"])))
        return rows

    pair_rows = count_cells(normalized_pair_specs)
    triple_rows = count_cells(normalized_triple_specs)
    payload = {
        "schemaVersion": SCHEMA_VERSION,
        "implementationVersion": IMPLEMENTATION_VERSION,
        "pairSpecs": [list(value) for value in normalized_pair_specs],
        "tripleSpecs": [list(value) for value in normalized_triple_specs],
        "minimumSupport": minimum_support,
        "population": {"publicObjectCount": len(records), "heldObjectCount": 0},
        "pairRows": pair_rows,
        "tripleRows": triple_rows,
        "zeroCellsMaterialized": False,
        "fullPairMatrixMaterialized": False,
    }
    return {
        **payload,
        "registrySha256": hashlib.sha256(_canonical_json_bytes(payload)).hexdigest(),
    }


def _trusted_context_material(
    *,
    registry_sha256: str,
    public_object_ids: Sequence[str],
    interactions_by_id: Mapping[str, Mapping[str, Any]],
    object_interaction_ids: Mapping[str, Iterable[str]],
) -> dict[str, Any]:
    return {
        "schemaVersion": "trace-exploration-trusted-interaction-context/v1",
        "registrySha256": registry_sha256,
        "publicObjectIds": list(public_object_ids),
        "interactions": [dict(interactions_by_id[value]) for value in sorted(interactions_by_id)],
        "objectInteractionIds": {
            object_id: sorted(object_interaction_ids[object_id]) for object_id in public_object_ids
        },
        "heldObjectCount": 0,
        "randomnessUsed": False,
    }


def build_trusted_interaction_context(
    registry: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
) -> TrustedInteractionContext:
    """Validate a registry against public records and seal pair memberships.

    Statistics, interaction identities, parent lineage, support, and object
    membership are recomputed.  A caller-provided residual or pair declaration
    is never trusted.
    """

    registry_sha256 = str(registry.get("registrySha256", ""))
    if not SHA256_PATTERN.fullmatch(registry_sha256):
        raise InteractionError("interaction registry lacks a valid SHA-256 digest")
    registry_payload = {key: value for key, value in registry.items() if key != "registrySha256"}
    if hashlib.sha256(_canonical_json_bytes(registry_payload)).hexdigest() != registry_sha256:
        raise InteractionError("interaction registry digest does not bind its payload")
    if registry.get("fullPairMatrixMaterialized") is not False or registry.get("zeroCellsMaterialized") is not False:
        raise InteractionError("trusted interaction registry must remain observed-only and bounded")
    if (
        registry.get("schemaVersion") != SCHEMA_VERSION
        or registry.get("implementationVersion") != IMPLEMENTATION_VERSION
    ):
        raise InteractionError("interaction registry schema/implementation is not trusted")

    ordered_records = sorted(records, key=lambda row: str(row.get("objectId", "")))
    public_object_ids = tuple(str(record.get("objectId", "")) for record in ordered_records)
    if (
        len(public_object_ids) != len(set(public_object_ids))
        or any(not PUBLIC_ID_PATTERN.fullmatch(value) for value in public_object_ids)
    ):
        raise InteractionError("trusted interaction cohort has invalid or duplicate public IDs")
    if any(
        record.get("held") is True
        or record.get("isHeld") is True
        or str(record.get("researchDisposition", "")).casefold() == "held"
        for record in ordered_records
    ):
        raise InteractionError("held data cannot enter a trusted interaction context")
    population = registry.get("population")
    if not isinstance(population, Mapping) or int(population.get("publicObjectCount", -1)) != len(ordered_records):
        raise InteractionError("interaction registry population does not match its public records")
    if int(population.get("heldObjectCount", -1)) != 0:
        raise InteractionError("interaction registry contains held objects")

    raw_pair_specs = registry.get("pairSpecs")
    raw_triple_specs = registry.get("tripleSpecs")
    minimum_support = registry.get("minimumSupport")
    if (
        not isinstance(raw_pair_specs, Sequence)
        or isinstance(raw_pair_specs, (str, bytes, bytearray))
        or not isinstance(raw_triple_specs, Sequence)
        or isinstance(raw_triple_specs, (str, bytes, bytearray))
        or isinstance(minimum_support, bool)
        or not isinstance(minimum_support, int)
    ):
        raise InteractionError("interaction registry lacks its declared cell contract")
    pair_specs = tuple(tuple(str(value) for value in spec) for spec in raw_pair_specs)
    triple_specs = tuple(tuple(str(value) for value in spec) for spec in raw_triple_specs)
    expected_registry = build_observed_interaction_registry(
        ordered_records,
        pair_specs=pair_specs,
        triple_specs=triple_specs,
        minimum_support=minimum_support,
    )
    if _canonical_json_bytes(registry) != _canonical_json_bytes(expected_registry):
        raise InteractionError(
            "interaction registry is incomplete or does not recompute from the public cohort"
        )

    normalized = {
        object_id: {field: _values(record, field) for field in FIELD_SIGNAL_IDS}
        for object_id, record in zip(public_object_ids, ordered_records)
    }
    raw_rows = list(registry.get("pairRows", ())) + list(registry.get("tripleRows", ()))
    interactions: dict[str, dict[str, Any]] = {}
    cell_to_id: dict[tuple[tuple[str, ...], tuple[str, ...]], str] = {}
    allowed_specs = {tuple(value) for value in PAIR_SPECS} | {tuple(value) for value in TRIPLE_SPECS}
    for raw in raw_rows:
        if not isinstance(raw, Mapping):
            raise InteractionError("interaction registry row must be a mapping")
        row = json.loads(json.dumps(raw, ensure_ascii=False, sort_keys=True))
        interaction_id = str(row.get("interactionId", ""))
        dimensions = tuple(str(value) for value in row.get("dimensions", ()))
        value_ids = tuple(str(value) for value in row.get("valueIds", ()))
        if dimensions not in allowed_specs or len(value_ids) != len(dimensions):
            raise InteractionError("interaction registry row uses an undeclared dimension specification")
        identity_material = "\x1f".join(
            f"{dimension}={value}" for dimension, value in zip(dimensions, value_ids)
        )
        expected_id = "EXP:INTERACTION:" + hashlib.sha256(identity_material.encode("utf-8")).hexdigest()
        if interaction_id != expected_id or interaction_id in interactions:
            raise InteractionError("interaction identity is fabricated or duplicated")
        expected_parents = [FIELD_SIGNAL_IDS[dimension] for dimension in dimensions]
        if row.get("parentSignalIds") != expected_parents:
            raise InteractionError("interaction parent lineage does not match its dimensions")
        eligible_object_ids = tuple(
            object_id
            for object_id in public_object_ids
            if all(normalized[object_id][dimension] for dimension in dimensions)
        )
        denominator = len(eligible_object_ids)
        support = sum(
            all(value in normalized[object_id][dimension] for dimension, value in zip(dimensions, value_ids))
            for object_id in eligible_object_ids
        )
        if int(row.get("support", -1)) != support or support <= 0:
            raise InteractionError("interaction support does not reconcile to public records")
        if int(row.get("eligiblePopulationCount", -1)) != denominator or denominator <= 0:
            raise InteractionError("interaction eligible population does not reconcile")
        marginals = [
            sum(value in normalized[object_id][dimension] for object_id in eligible_object_ids)
            for dimension, value in zip(dimensions, value_ids)
        ]
        expected_stats = (
            pair_statistics(
                support=support,
                left_support=marginals[0],
                right_support=marginals[1],
                denominator=denominator,
            )
            if len(dimensions) == 2
            else higher_order_statistics(
                support=support,
                marginal_supports=marginals,
                denominator=denominator,
            )
        )
        if _canonical_json_bytes(row.get("statistics")) != _canonical_json_bytes(expected_stats):
            raise InteractionError("interaction statistics do not recompute from public records")
        if (
            row.get("interactionOnly") is not True
            or row.get("parentContributionRepeated") is not False
            or row.get("historicalRelation") is not False
            or row.get("semanticRelation") is not False
        ):
            raise InteractionError("interaction row crossed its interpretation/lineage boundary")
        interactions[interaction_id] = row
        cell_to_id[(dimensions, value_ids)] = interaction_id

    object_memberships: dict[str, set[str]] = {object_id: set() for object_id in public_object_ids}
    specs = sorted({dimensions for dimensions, _ in cell_to_id})
    for object_id in public_object_ids:
        record = normalized[object_id]
        for dimensions in specs:
            values = [record[dimension] for dimension in dimensions]
            if not all(values):
                continue
            for cell in product(*values):
                interaction_id = cell_to_id.get((dimensions, tuple(cell)))
                if interaction_id:
                    object_memberships[object_id].add(interaction_id)
    for interaction_id, row in interactions.items():
        membership_count = sum(
            interaction_id in object_memberships[object_id] for object_id in public_object_ids
        )
        if membership_count != int(row["support"]):
            raise InteractionError("trusted interaction membership does not equal registry support")

    frozen_interactions = {
        key: _deep_freeze(value) for key, value in sorted(interactions.items())
    }
    frozen_memberships = {
        key: frozenset(value) for key, value in sorted(object_memberships.items())
    }
    frozen_interaction_map = MappingProxyType(frozen_interactions)
    frozen_membership_map = MappingProxyType(frozen_memberships)
    material = _trusted_context_material(
        registry_sha256=registry_sha256,
        public_object_ids=public_object_ids,
        interactions_by_id=frozen_interaction_map,
        object_interaction_ids=frozen_membership_map,
    )
    context_sha256 = hashlib.sha256(_canonical_json_bytes(material)).hexdigest()
    validation_fingerprint = (
        registry_sha256,
        context_sha256,
        public_object_ids,
        id(frozen_interaction_map),
        id(frozen_membership_map),
        len(frozen_interaction_map),
        len(frozen_membership_map),
    )
    return TrustedInteractionContext(
        registry_sha256=registry_sha256,
        public_object_ids=public_object_ids,
        interactions_by_id=frozen_interaction_map,
        object_interaction_ids=frozen_membership_map,
        context_sha256=context_sha256,
        _seal=_TRUST_SEAL,
        _validation_fingerprint=validation_fingerprint,
    )


def validate_trusted_interaction_context(context: TrustedInteractionContext) -> None:
    if not isinstance(context, TrustedInteractionContext) or context._seal is not _TRUST_SEAL:
        raise InteractionError("interaction context was not created by the trusted builder")
    current_fingerprint = (
        context.registry_sha256,
        context.context_sha256,
        context.public_object_ids,
        id(context.interactions_by_id),
        id(context.object_interaction_ids),
        len(context.interactions_by_id),
        len(context.object_interaction_ids),
    )
    if context._validation_fingerprint != current_fingerprint:
        raise InteractionError("trusted interaction context identity or cohort was mutated")
    if (
        not SHA256_PATTERN.fullmatch(context.registry_sha256)
        or not SHA256_PATTERN.fullmatch(context.context_sha256)
        or not isinstance(context.interactions_by_id, MappingProxyType)
        or not isinstance(context.object_interaction_ids, MappingProxyType)
    ):
        raise InteractionError("trusted interaction context structure is invalid")


def trusted_candidate_postings(
    context: TrustedInteractionContext,
) -> dict[str, tuple[str, ...]]:
    """Return only the frozen high-information candidate-retrieval subset."""

    validate_trusted_interaction_context(context)
    allowed_dimension_specs = {
        tuple(str(value) for value in spec)
        for spec in CANDIDATE_INTERACTION_POLICY["candidateAllowedDimensionSpecs"]
    }
    selected_ids = {
        interaction_id
        for interaction_id, row in context.interactions_by_id.items()
        if int(CANDIDATE_INTERACTION_POLICY["minimumSupportInclusive"])
        <= int(row["support"])
        <= int(CANDIDATE_INTERACTION_POLICY["maximumSupportInclusive"])
        and float(row["statistics"][str(CANDIDATE_INTERACTION_POLICY["statistic"])])
        >= float(CANDIDATE_INTERACTION_POLICY["minimumShrunkNormalizedPmiInclusive"])
        and tuple(str(value) for value in row["dimensions"]) in allowed_dimension_specs
        and (
            bool(CANDIDATE_INTERACTION_POLICY["sourceRowsAllowed"])
            or "source" not in tuple(str(value) for value in row["dimensions"])
        )
    }
    postings: dict[str, list[str]] = {value: [] for value in sorted(selected_ids)}
    for object_id in context.public_object_ids:
        for interaction_id in context.object_interaction_ids[object_id]:
            if interaction_id in selected_ids:
                postings[interaction_id].append(object_id)
    frozen = {key: tuple(sorted(value)) for key, value in sorted(postings.items())}
    for interaction_id, object_ids in frozen.items():
        if len(object_ids) != int(context.interactions_by_id[interaction_id]["support"]):
            raise InteractionError("trusted candidate posting lost support reconciliation")
    return frozen


def trusted_candidate_posting_receipt(
    context: TrustedInteractionContext,
) -> dict[str, Any]:
    """Bind the frozen selection policy and selected postings to one digest."""

    postings = trusted_candidate_postings(context)
    material = {
        "schemaVersion": "trace-exploration-interaction-candidate-postings/v1",
        "registrySha256": context.registry_sha256,
        "interactionContextSha256": context.context_sha256,
        "policy": dict(CANDIDATE_INTERACTION_POLICY),
        "selectedPostings": postings,
        "selectedInteractionCount": len(postings),
        "selectedMembershipCount": sum(len(value) for value in postings.values()),
    }
    return {
        **material,
        "selectedPostingsSha256": hashlib.sha256(_canonical_json_bytes(material)).hexdigest(),
    }


def resolve_pair_interactions(
    context: TrustedInteractionContext,
    query_id: str,
    candidate_id: str,
    *,
    method: str,
    support_threshold: int,
    cap: float,
    source_treatment: str,
) -> list[dict[str, Any]]:
    validate_trusted_interaction_context(context)
    if query_id == candidate_id:
        raise InteractionError("self pair cannot resolve interaction evidence")
    if query_id not in context.object_interaction_ids or candidate_id not in context.object_interaction_ids:
        raise InteractionError("interaction pair is outside the trusted public cohort")
    shared = sorted(
        context.object_interaction_ids[query_id]
        & context.object_interaction_ids[candidate_id]
    )
    rows: list[dict[str, Any]] = []
    for interaction_id in shared:
        row = context.interactions_by_id[interaction_id]
        parents = tuple(str(value) for value in row["parentSignalIds"])
        if source_treatment in {"SOURCE-0", "SOURCE-2", "SOURCE-4"} and any(
            value.startswith("SIG-SOURCE-") for value in parents
        ):
            continue
        rows.append(
            residual_interaction_contribution(
                row,
                support_threshold=support_threshold,
                cap=cap,
                method=method,
                registry_sha256=context.registry_sha256,
                interaction_context_sha256=context.context_sha256,
                object_ids=(query_id, candidate_id),
            )
        )
    return rows


def residual_interaction_contribution(
    interaction: Mapping[str, Any],
    *,
    support_threshold: int = 5,
    cap: float = 0.10,
    method: str = "INFORMATION_RESIDUAL_CONTRIBUTION",
    registry_sha256: str | None = None,
    interaction_context_sha256: str | None = None,
    object_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Create a separate bounded bonus; never repeat parent base features."""

    if support_threshold not in SUPPORT_THRESHOLDS:
        raise InteractionError("support threshold is outside the declared sensitivity grid")
    if not 0 < cap <= 1:
        raise InteractionError("interaction cap must be in (0, 1]")
    support = int(interaction.get("support", 0))
    stats = interaction.get("statistics")
    if not isinstance(stats, Mapping):
        raise InteractionError("interaction lacks statistics")
    denominator = int(stats.get("denominator", 0))
    if denominator <= 0 or support > denominator:
        raise InteractionError("interaction residual lacks a valid support denominator")
    positive_excess_association = float(stats.get("lift", 0.0)) > 1.0
    if method == "NO_INTERACTION_CONTRIBUTION" or not positive_excess_association:
        residual = 0.0
    elif method == "CAPPED_INTERACTION_BONUS":
        residual = min(cap, cap * support / (support + support_threshold))
    elif method == "INFORMATION_RESIDUAL_CONTRIBUTION":
        information = max(0.0, float(stats.get("shrunkNormalizedPmi", 0.0)))
        residual = min(cap, cap * information * support / (support + support_threshold))
    elif method == "LOG_LIKELIHOOD_INTERACTION_CONTRIBUTION":
        llr = max(0.0, float(stats.get("logLikelihoodRatio", 0.0)))
        residual = min(cap, cap * (1 - math.exp(-llr / 10)) * support / (support + support_threshold))
    else:
        raise InteractionError("unsupported residualization method")
    if support < support_threshold:
        residual *= support / support_threshold
    return {
        "interactionId": str(interaction.get("interactionId", "")),
        "method": method,
        "support": support,
        "supportThreshold": support_threshold,
        "denominator": denominator,
        "parentSignalIds": list(interaction.get("parentSignalIds", ())),
        "residualScore": residual,
        "cap": cap,
        "registrySha256": registry_sha256 or str(interaction.get("registrySha256", "")),
        "interactionContextSha256": (
            interaction_context_sha256
            or str(interaction.get("interactionContextSha256", ""))
        ),
        "objectIds": list(object_ids or interaction.get("objectIds", ())),
        "parentContributionRepeated": False,
        "separateFromParentContributions": True,
        "rareMeansImportant": False,
        "positiveExcessAssociationRequired": True,
        "positiveExcessAssociationObserved": positive_excess_association,
    }


def low_support_inflation_failures(
    interactions: Iterable[Mapping[str, Any]],
    *,
    support_threshold: int = 5,
    cap: float = 0.10,
) -> int:
    failures = 0
    for interaction in interactions:
        contribution = residual_interaction_contribution(
            interaction,
            support_threshold=support_threshold,
            cap=cap,
        )
        support = int(contribution["support"])
        residual = float(contribution["residualScore"])
        if residual > cap + 1e-12 or (support <= 2 and residual >= cap):
            failures += 1
    return failures


def self_test() -> dict[str, Any]:
    stats = pair_statistics(support=2, left_support=10, right_support=5, denominator=100)
    row = {
        "interactionId": "EXP:INTERACTION:TEST",
        "support": 2,
        "parentSignalIds": ["SIG-A", "SIG-B"],
        "statistics": stats,
    }
    contribution = residual_interaction_contribution(row, support_threshold=5, cap=0.1)
    if contribution["residualScore"] >= 0.1 or contribution["parentContributionRepeated"]:
        raise AssertionError("low-support residual was unbounded or repeated parents")
    negative_stats = pair_statistics(
        support=25,
        left_support=70,
        right_support=50,
        denominator=100,
    )
    negative_row = {
        "interactionId": "EXP:INTERACTION:NEGATIVE-ASSOCIATION",
        "support": 25,
        "parentSignalIds": ["SIG-A", "SIG-B"],
        "statistics": negative_stats,
    }
    negative_policy_failures = sum(
        residual_interaction_contribution(
            negative_row,
            support_threshold=5,
            cap=0.1,
            method=method,
        )["residualScore"]
        != 0
        for method in (
            "CAPPED_INTERACTION_BONUS",
            "INFORMATION_RESIDUAL_CONTRIBUTION",
            "LOG_LIKELIHOOD_INTERACTION_CONTRIBUTION",
        )
    )
    if negative_policy_failures:
        raise AssertionError("negative association received a positive interaction bonus")
    records = [
        {
            "objectId": f"SURF-I{ordinal}",
            "medium": [{"id": medium}],
            "theme": [{"id": theme}],
            "movement_context": [],
            "decade": [{"id": decade}],
            "geography": [{"id": geography}],
            "source": {"id": source},
            "object_type": {"id": "OT"},
            "creator": {"id": f"CR{ordinal}"},
        }
        for ordinal, (medium, theme, decade, geography, source) in enumerate(
            (("M1", "T1", "D1", "G1", "S1"), ("M1", "T1", "D1", "G2", "S2"), ("M2", "T2", "D2", "G1", "S1")),
            start=1,
        )
    ]
    registry = build_observed_interaction_registry(
        records,
        pair_specs=(("medium", "theme"),),
        triple_specs=(("medium", "theme", "decade"),),
    )
    trusted = build_trusted_interaction_context(registry, records)
    validate_trusted_interaction_context(trusted)
    incomplete = json.loads(json.dumps(registry))
    incomplete["pairRows"] = incomplete["pairRows"][:-1]
    incomplete_payload = {
        key: value for key, value in incomplete.items() if key != "registrySha256"
    }
    incomplete["registrySha256"] = hashlib.sha256(
        _canonical_json_bytes(incomplete_payload)
    ).hexdigest()
    incomplete_registry_rejected = False
    try:
        build_trusted_interaction_context(incomplete, records)
    except InteractionError:
        incomplete_registry_rejected = True
    if not incomplete_registry_rejected:
        raise AssertionError("trusted context accepted an incomplete rehashed registry")
    missing_dimension_records = json.loads(json.dumps(records))
    missing_dimension_records[1]["theme"] = []
    missing_registry = build_observed_interaction_registry(
        missing_dimension_records,
        pair_specs=(("medium", "theme"),),
        triple_specs=(),
    )
    if not missing_registry["pairRows"] or any(
        int(row["eligiblePopulationCount"]) != 2
        or int(row["statistics"]["denominator"]) != 2
        for row in missing_registry["pairRows"]
    ):
        raise AssertionError("interaction denominator included unavailable observations")
    candidate_records = []
    for ordinal in range(1, 7):
        common = ordinal <= 5
        candidate_records.append({
            "objectId": f"SURF-CI{ordinal}",
            "medium": [{"id": "M-COMMON" if common else "M-OTHER"}],
            "theme": [{"id": "T-COMMON" if common else "T-OTHER"}],
            "movement_context": [{"id": "MV-COMMON" if common else "MV-OTHER"}],
            "decade": [{"id": "D-COMMON" if common else "D-OTHER"}],
            "geography": [{"id": "G-COMMON" if common else "G-OTHER"}],
            "source": {"id": f"S{ordinal}"},
            "object_type": {"id": "OT-COMMON" if common else "OT-OTHER"},
            "creator": {"id": "CR-COMMON" if common else "CR-OTHER"},
        })
    candidate_registry = build_observed_interaction_registry(
        candidate_records,
        pair_specs=(
            ("medium", "theme"),
            ("medium", "geography"),
            ("creator", "medium"),
            ("object_type", "medium"),
            ("theme", "movement_context"),
        ),
        triple_specs=(("medium", "theme", "decade"),),
    )
    candidate_context = build_trusted_interaction_context(
        candidate_registry,
        candidate_records,
    )
    candidate_postings = trusted_candidate_postings(candidate_context)
    candidate_dimensions = {
        tuple(candidate_context.interactions_by_id[interaction_id]["dimensions"])
        for interaction_id in candidate_postings
    }
    expected_candidate_dimensions = {
        ("creator", "medium"),
        ("medium", "theme"),
        ("object_type", "medium"),
        ("theme", "movement_context"),
    }
    if candidate_dimensions != expected_candidate_dimensions:
        raise AssertionError(
            "candidate interaction postings escaped or omitted the lineage-authorized pair set"
        )
    if ("medium", "geography") in candidate_dimensions or any(
        len(dimensions) != 2 for dimensions in candidate_dimensions
    ):
        raise AssertionError("unapproved pair/triple became a candidate interaction posting")
    return {
        "status": "PASS",
        "interactionMethodCount": len(INTERACTION_METHODS),
        "supportThresholdCount": len(SUPPORT_THRESHOLDS),
        "observedPairCellCount": len(registry["pairRows"]),
        "observedTripleCellCount": len(registry["tripleRows"]),
        "lowSupportInflationFailureCount": low_support_inflation_failures([row]),
        "interactionParentDoubleCountFailures": 0,
        "trustedContextSha256": trusted.context_sha256,
        "incompleteRehashedRegistryRejected": incomplete_registry_rejected,
        "negativeAssociationPositiveBonusFailures": negative_policy_failures,
        "jointObservableDenominator": 2,
        "unavailableObservationDenominatorLeakCount": 0,
        "candidateAllowedDimensionSpecCount": len(expected_candidate_dimensions),
        "unapprovedCandidateInteractionPostingCount": 0,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
