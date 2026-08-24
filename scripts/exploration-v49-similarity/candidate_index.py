#!/usr/bin/env python3
"""Deterministic public-only candidate retrieval for Exploration research.

Candidate generation is deliberately separate from affinity scoring.  Curated
containers are available only as a recall substrate in this module; the index
does not expose a curatorial score.  All postings contain public surface IDs,
and the index is an in-memory research artifact rather than a runtime API.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
import time
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any


SCHEMA_VERSION = "trace-exploration-candidate-index/v1"
IMPLEMENTATION_VERSION = "trace-exploration-candidate-index-2026-08-24"
PUBLIC_ID_PATTERN = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")

CANDIDATE_VARIANTS = (
    "CG-CUR-1",
    "CG-CUR-2",
    "CG-CUR-3",
    "CG-CUR-4",
    "CG-CUR-5",
    "CG-CUR-6",
)

# Direct governed/approved features are candidate evidence.  Diagnostic state
# fields and raw curation never enter a model token namespace here.
DIRECT_FIELD_FAMILIES: dict[str, str] = {
    "medium": "context",
    "theme": "context",
    "movement_context": "context",
    "decade": "temporal",
    "geography": "geography",
    "source": "source",
    "object_type": "descriptive",
    "creator": "descriptive",
}
GOVERNED_RETRIEVAL_FIELDS = frozenset(
    {"medium", "theme", "movement_context", "decade", "geography"}
)
APPROVED_DESCRIPTIVE_FIELDS = frozenset({"source", "object_type", "creator"})
UNKNOWN_LABELS = frozenset(
    {
        "",
        "unknown",
        "not governed",
        "not_governed",
        "no published movement context",
        "no_published_movement_context",
    }
)


class CandidateIndexError(ValueError):
    """Raised when an index input or candidate request violates the contract."""


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


def _member(value: Any, field: str) -> tuple[str, str]:
    if isinstance(value, str):
        identifier = value.strip()
        label = identifier
    elif isinstance(value, Mapping):
        identifier = str(value.get("id", "")).strip()
        label = str(value.get("label", identifier)).strip()
    else:
        raise CandidateIndexError(f"{field} contains a non-text/non-mapping value")
    if not identifier:
        raise CandidateIndexError(f"{field} contains a blank identifier")
    return identifier, label


def _members(record: Mapping[str, Any], field: str) -> tuple[tuple[str, str], ...]:
    raw = record.get(field)
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise CandidateIndexError(f"{field} must be an array")
    values = {_member(value, field) for value in raw}
    return tuple(sorted(values))


def _scalar(record: Mapping[str, Any], field: str) -> tuple[str, str]:
    if field not in record:
        raise CandidateIndexError(f"{field} is required")
    return _member(record[field], field)


def _is_observed(identifier: str, label: str) -> bool:
    normalized = label.strip().casefold().replace("-", "_")
    return normalized not in UNKNOWN_LABELS and not normalized.startswith("unknown;")


def _token(family: str, field: str, identifier: str) -> str:
    # The separator cannot occur in normalized JSON identifiers and makes
    # family/field qualification unambiguous without exposing labels.
    return f"{family}\x1f{field}\x1f{identifier}"


@dataclass(frozen=True)
class IndexedRecord:
    """Minimal immutable feature view shared by retrieval and model code."""

    object_id: str
    field_values: Mapping[str, tuple[str, ...]]
    family_tokens: Mapping[str, tuple[str, ...]]
    candidate_only_tokens: tuple[str, ...]
    curated_tokens: tuple[str, ...]
    residual_curated_tokens: tuple[str, ...]
    labels: Mapping[str, str]
    start_year: int
    end_year: int
    temporal_precision: str
    geography_mapping_states: tuple[str, ...]
    geography_classes: tuple[str, ...]
    geography_qualified: bool
    multi_region: bool


@dataclass(frozen=True)
class CandidateIndex:
    schema_version: str
    implementation_version: str
    object_ids: tuple[str, ...]
    records: Mapping[str, IndexedRecord]
    direct_postings: Mapping[str, tuple[str, ...]]
    candidate_only_postings: Mapping[str, tuple[str, ...]]
    curated_postings: Mapping[str, tuple[str, ...]]
    residual_curated_postings: Mapping[str, tuple[str, ...]]
    interaction_postings: Mapping[str, tuple[str, ...]]
    interaction_registry_sha256: str | None
    interaction_context_sha256: str | None
    interaction_candidate_policy: Mapping[str, Any] | None
    interaction_selected_postings_sha256: str | None
    token_document_frequency: Mapping[str, int]
    token_family: Mapping[str, str]
    scoring_records_sha256: str
    index_sha256: str
    serialized_bytes: int


@dataclass(frozen=True)
class CandidateSet:
    query_id: str
    variant: str
    candidate_ids: tuple[str, ...]
    retrieval_reasons: Mapping[str, tuple[dict[str, Any], ...]]
    direct_candidate_count: int
    curatorial_candidate_count: int
    candidate_pool_count: int
    possible_other_count: int
    reduction_ratio: float
    candidate_set_sha256: str
    candidate_index_sha256: str
    policy_parameters: Mapping[str, Any]
    policy_metadata: Mapping[str, Any]
    randomness_affects_candidate_set: bool = False


def normalize_index_record(
    record: Mapping[str, Any],
    *,
    residual_curated_tokens: Iterable[str] = (),
) -> IndexedRecord:
    """Normalize one sealed Round 5 record without deriving pairwise facts."""

    if not isinstance(record, Mapping):
        raise CandidateIndexError("every record must be a mapping")
    object_id = str(record.get("objectId", "")).strip()
    if not PUBLIC_ID_PATTERN.fullmatch(object_id):
        raise CandidateIndexError("objectId is not a public surface ID")
    if (
        record.get("held") is True
        or record.get("isHeld") is True
        or str(record.get("researchDisposition", "")).casefold() == "held"
    ):
        raise CandidateIndexError("held data cannot enter the candidate index")

    field_values: dict[str, tuple[str, ...]] = {}
    labels: dict[str, str] = {}
    for field in ("medium", "theme", "movement_context", "decade", "geography"):
        values = tuple(
            (identifier, label)
            for identifier, label in _members(record, field)
            if _is_observed(identifier, label)
        )
        field_values[field] = tuple(identifier for identifier, _ in values)
        labels.update({identifier: label for identifier, label in values})
    for field in ("source", "object_type", "creator"):
        identifier, label = _scalar(record, field)
        labels[identifier] = label
        field_values[field] = (identifier,) if _is_observed(identifier, label) else ()

    curated = _members(record, "curated_container")
    curated_ids = tuple(identifier for identifier, _ in curated)
    labels.update({identifier: label for identifier, label in curated})
    residual = tuple(sorted({str(value).strip() for value in residual_curated_tokens if str(value).strip()}))
    if not set(residual).issubset(curated_ids):
        raise CandidateIndexError("residual curation must be a subset of curated memberships")

    family_tokens: dict[str, list[str]] = defaultdict(list)
    for field, family in DIRECT_FIELD_FAMILIES.items():
        for identifier in field_values[field]:
            family_tokens[family].append(_token(family, field, identifier))
    if residual:
        family_tokens["curatorialResidual"].extend(
            _token("curatorialResidual", "residual_container", value) for value in residual
        )

    start_year = record.get("startYear")
    end_year = record.get("endYear")
    if isinstance(start_year, bool) or not isinstance(start_year, int):
        raise CandidateIndexError("startYear must be an integer")
    if isinstance(end_year, bool) or not isinstance(end_year, int) or end_year < start_year:
        raise CandidateIndexError("endYear must be an integer not before startYear")
    precision = str(record.get("temporalPrecision", "")).strip()
    if not precision:
        raise CandidateIndexError("temporalPrecision is required")

    raw_states = record.get("geographyMappingStates", record.get("geography_mapping_state", ()))
    if not isinstance(raw_states, Sequence) or isinstance(raw_states, (str, bytes, bytearray)):
        raise CandidateIndexError("geographyMappingStates must be an array")
    states = tuple(sorted({_member(value, "geographyMappingStates")[0] for value in raw_states}))
    raw_classes = record.get("geographyClasses", record.get("geography_class", ()))
    if not isinstance(raw_classes, Sequence) or isinstance(raw_classes, (str, bytes, bytearray)):
        raise CandidateIndexError("geographyClasses must be an array")
    classes = tuple(sorted({_member(value, "geographyClasses")[0] for value in raw_classes}))

    multi_region = record.get("multiRegion")
    if not isinstance(multi_region, bool):
        raise CandidateIndexError("multiRegion must be boolean")
    if multi_region != (len(field_values["geography"]) > 1):
        raise CandidateIndexError("multiRegion conflicts with governed geography cardinality")

    return IndexedRecord(
        object_id=object_id,
        field_values={key: tuple(value) for key, value in sorted(field_values.items())},
        family_tokens={key: tuple(sorted(set(value))) for key, value in sorted(family_tokens.items())},
        candidate_only_tokens=tuple(
            _token("candidateOnly", "geography_class", value) for value in classes
        ),
        curated_tokens=curated_ids,
        residual_curated_tokens=residual,
        labels=dict(sorted(labels.items())),
        start_year=start_year,
        end_year=end_year,
        temporal_precision=precision,
        geography_mapping_states=states,
        geography_classes=classes,
        geography_qualified=bool(record.get("geographyQualified", False)),
        multi_region=multi_region,
    )


def build_exploration_candidate_index(
    records: Sequence[Mapping[str, Any]],
    *,
    residual_curation_by_object: Mapping[str, Iterable[str]] | None = None,
    interaction_tokens_by_object: Mapping[str, Iterable[str]] | None = None,
    trusted_interaction_context: Any | None = None,
) -> CandidateIndex:
    """Build a deterministic inverted index without materializing object pairs.

    ``residual_curation_by_object`` must already have passed lineage review.  It
    is empty for the Round 5 corpus because all folder memberships are source
    facts underlying governed Context/Spacetime dimensions.  Interaction
    postings are accepted only through a sealed context whose registry,
    support, membership, and public cohort have been recomputed together.
    """

    residual_by_object = residual_curation_by_object or {}
    if interaction_tokens_by_object is not None:
        raise CandidateIndexError(
            "interaction_tokens_by_object is prohibited; provide a trusted interaction context"
        )
    interaction_by_object: Mapping[str, Iterable[str]] = {}
    interaction_registry_sha256: str | None = None
    interaction_context_sha256: str | None = None
    interaction_candidate_policy: Mapping[str, Any] | None = None
    interaction_selected_postings_sha256: str | None = None
    normalized = [
        normalize_index_record(
            record,
            residual_curated_tokens=residual_by_object.get(str(record.get("objectId", "")), ()),
        )
        for record in records
    ]
    normalized.sort(key=lambda value: value.object_id)
    object_ids = tuple(value.object_id for value in normalized)
    if len(object_ids) != len(set(object_ids)):
        raise CandidateIndexError("candidate index input contains duplicate public IDs")
    if set(residual_by_object) - set(object_ids):
        raise CandidateIndexError("residual curation references an object outside the public cohort")
    if trusted_interaction_context is not None:
        try:
            import interaction_statistics

            interaction_statistics.validate_trusted_interaction_context(
                trusted_interaction_context
            )
            trusted_postings = interaction_statistics.trusted_candidate_postings(
                trusted_interaction_context
            )
            posting_receipt = interaction_statistics.trusted_candidate_posting_receipt(
                trusted_interaction_context
            )
        except (ImportError, ValueError) as error:
            raise CandidateIndexError("trusted interaction context validation failed") from error
        if tuple(trusted_interaction_context.public_object_ids) != object_ids:
            raise CandidateIndexError("trusted interaction cohort differs from candidate-index cohort")
        value_postings: dict[tuple[str, str], set[str]] = defaultdict(set)
        for record in normalized:
            for dimension in interaction_statistics.FIELD_SIGNAL_IDS:
                for value_id in record.field_values.get(dimension, ()):
                    value_postings[(dimension, value_id)].add(record.object_id)
        all_trusted_postings: dict[str, set[str]] = {
            interaction_id: set()
            for interaction_id in trusted_interaction_context.interactions_by_id
        }
        for object_id in object_ids:
            for interaction_id in trusted_interaction_context.object_interaction_ids[object_id]:
                all_trusted_postings[interaction_id].add(object_id)
        for interaction_id, row in trusted_interaction_context.interactions_by_id.items():
            dimensions = tuple(str(value) for value in row["dimensions"])
            value_ids = tuple(str(value) for value in row["valueIds"])
            dimension_postings = [
                value_postings.get((dimension, value_id), set())
                for dimension, value_id in zip(dimensions, value_ids)
            ]
            expected_posting = (
                set.intersection(*dimension_postings) if dimension_postings else set()
            )
            if expected_posting != all_trusted_postings[interaction_id]:
                raise CandidateIndexError(
                    "trusted interaction membership does not reconcile to indexed scoring records"
                )
        by_object: dict[str, list[str]] = {object_id: [] for object_id in object_ids}
        for interaction_id, posting in trusted_postings.items():
            expected_support = int(
                trusted_interaction_context.interactions_by_id[interaction_id]["support"]
            )
            if len(posting) != expected_support:
                raise CandidateIndexError("trusted interaction posting support changed")
            for object_id in posting:
                by_object[object_id].append(interaction_id)
        interaction_by_object = by_object
        interaction_registry_sha256 = trusted_interaction_context.registry_sha256
        interaction_context_sha256 = trusted_interaction_context.context_sha256
        interaction_candidate_policy = dict(posting_receipt["policy"])
        interaction_selected_postings_sha256 = str(
            posting_receipt["selectedPostingsSha256"]
        )

    direct: dict[str, list[str]] = defaultdict(list)
    candidate_only: dict[str, list[str]] = defaultdict(list)
    curated: dict[str, list[str]] = defaultdict(list)
    residual: dict[str, list[str]] = defaultdict(list)
    interactions: dict[str, list[str]] = defaultdict(list)
    token_family: dict[str, str] = {}
    for value in normalized:
        for family, tokens in value.family_tokens.items():
            for token in tokens:
                if family == "curatorialResidual":
                    residual[token].append(value.object_id)
                else:
                    direct[token].append(value.object_id)
                token_family[token] = family
        for token in value.candidate_only_tokens:
            candidate_only[token].append(value.object_id)
            token_family[token] = "geographyClassCandidateOnly"
        for identifier in value.curated_tokens:
            token = _token("curatorialRecall", "container", identifier)
            curated[token].append(value.object_id)
            token_family[token] = "curatorialRecall"
        for raw in sorted({str(item).strip() for item in interaction_by_object.get(value.object_id, ()) if str(item).strip()}):
            token = _token("interaction", "approved_cell", raw)
            interactions[token].append(value.object_id)
            token_family[token] = "interaction"

    def freeze(postings: Mapping[str, Sequence[str]]) -> dict[str, tuple[str, ...]]:
        return {token: tuple(sorted(set(values))) for token, values in sorted(postings.items())}

    frozen_direct = freeze(direct)
    frozen_candidate_only = freeze(candidate_only)
    frozen_curated = freeze(curated)
    frozen_residual = freeze(residual)
    frozen_interactions = freeze(interactions)
    all_postings = {
        **frozen_direct,
        **frozen_candidate_only,
        **frozen_curated,
        **frozen_residual,
        **frozen_interactions,
    }
    dfs = {token: len(values) for token, values in sorted(all_postings.items())}
    scoring_record_material = [
        {
            "objectId": value.object_id,
            "fieldValues": value.field_values,
            "familyTokens": value.family_tokens,
            "candidateOnlyTokens": value.candidate_only_tokens,
            "curatedTokens": value.curated_tokens,
            "residualCuratedTokens": value.residual_curated_tokens,
            "labels": value.labels,
            "startYear": value.start_year,
            "endYear": value.end_year,
            "temporalPrecision": value.temporal_precision,
            "geographyMappingStates": value.geography_mapping_states,
            "geographyClasses": value.geography_classes,
            "geographyQualified": value.geography_qualified,
            "multiRegion": value.multi_region,
        }
        for value in normalized
    ]
    scoring_records_sha256 = hashlib.sha256(
        _canonical_json_bytes(scoring_record_material)
    ).hexdigest()
    payload = {
        "schemaVersion": SCHEMA_VERSION,
        "implementationVersion": IMPLEMENTATION_VERSION,
        "objectIds": object_ids,
        "directPostings": frozen_direct,
        "candidateOnlyPostings": frozen_candidate_only,
        "curatedRecallPostings": frozen_curated,
        "residualCuratedPostings": frozen_residual,
        "interactionPostings": frozen_interactions,
        "interactionRegistrySha256": interaction_registry_sha256,
        "interactionContextSha256": interaction_context_sha256,
        "interactionCandidatePolicy": interaction_candidate_policy,
        "interactionSelectedPostingsSha256": interaction_selected_postings_sha256,
        "scoringRecordsSha256": scoring_records_sha256,
        "randomnessAffectsCandidateSet": False,
        "pairRowsMaterialized": False,
    }
    encoded = _canonical_json_bytes(payload)
    return CandidateIndex(
        schema_version=SCHEMA_VERSION,
        implementation_version=IMPLEMENTATION_VERSION,
        object_ids=object_ids,
        records={value.object_id: value for value in normalized},
        direct_postings=frozen_direct,
        candidate_only_postings=frozen_candidate_only,
        curated_postings=frozen_curated,
        residual_curated_postings=frozen_residual,
        interaction_postings=frozen_interactions,
        interaction_registry_sha256=interaction_registry_sha256,
        interaction_context_sha256=interaction_context_sha256,
        interaction_candidate_policy=interaction_candidate_policy,
        interaction_selected_postings_sha256=interaction_selected_postings_sha256,
        token_document_frequency=dfs,
        token_family=dict(sorted(token_family.items())),
        scoring_records_sha256=scoring_records_sha256,
        index_sha256=hashlib.sha256(encoded).hexdigest(),
        serialized_bytes=len(encoded),
    )


def _record_tokens(index: CandidateIndex, object_id: str, family: str | None = None) -> tuple[str, ...]:
    record = index.records.get(object_id)
    if record is None:
        raise CandidateIndexError("query is not in the public candidate index")
    if family is None:
        return tuple(token for values in record.family_tokens.values() for token in values)
    return record.family_tokens.get(family, ())


def _base_candidates(
    index: CandidateIndex,
    query_id: str,
    *,
    direct_posting_max_ratio: float,
    include_source: bool,
    include_descriptive: bool,
    include_interactions: bool,
    collect_reasons: bool,
) -> tuple[set[str], dict[str, list[dict[str, Any]]]]:
    if not 0 < direct_posting_max_ratio <= 1:
        raise CandidateIndexError("direct posting maximum ratio must be in (0, 1]")
    n = len(index.object_ids)
    candidates: set[str] = set()
    reasons: dict[str, list[dict[str, Any]]] = defaultdict(list)
    record = index.records[query_id]
    permitted_families = {"context", "temporal", "geography"}
    if include_source:
        permitted_families.add("source")
    if include_descriptive:
        permitted_families.add("descriptive")
    for family in sorted(permitted_families):
        for token in record.family_tokens.get(family, ()):
            posting = index.direct_postings.get(token, ())
            df = len(posting)
            if df <= 1 or df / n > direct_posting_max_ratio:
                continue
            for candidate_id in posting:
                if candidate_id == query_id:
                    continue
                candidates.add(candidate_id)
                if collect_reasons:
                    reasons[candidate_id].append(
                        {
                            "reasonType": "DIRECT_APPROVED_POSTING",
                            "family": family,
                            "token": token,
                            "support": df,
                            "denominator": n,
                        }
                    )
    for token in record.candidate_only_tokens:
        posting = index.candidate_only_postings.get(token, ())
        df = len(posting)
        if df <= 1 or df / n > direct_posting_max_ratio:
            continue
        for candidate_id in posting:
            if candidate_id == query_id:
                continue
            candidates.add(candidate_id)
            if collect_reasons:
                reasons[candidate_id].append(
                    {
                        "reasonType": "CANDIDATE_ONLY_GEOGRAPHY_CLASS_FALLBACK",
                        "family": "geography",
                        "token": token,
                        "support": df,
                        "denominator": n,
                        "scoringAllowed": False,
                    }
                )
    if include_interactions:
        query_tokens = {
            _token("interaction", "approved_cell", str(raw).strip())
            for raw in ()
        }
        # Interaction tokens are optional input.  Discover query membership
        # from the inverted postings without maintaining a duplicate object map.
        query_tokens.update(
            token for token, posting in index.interaction_postings.items() if query_id in posting
        )
        for token in sorted(query_tokens):
            posting = index.interaction_postings[token]
            for candidate_id in posting:
                if candidate_id == query_id:
                    continue
                candidates.add(candidate_id)
                if collect_reasons:
                    reasons[candidate_id].append(
                        {
                            "reasonType": "APPROVED_HIGH_INFORMATION_POSTING",
                            "family": "interaction",
                            "token": token,
                            "support": len(posting),
                            "denominator": n,
                        }
                    )
    return candidates, reasons


def _curatorial_candidates(
    index: CandidateIndex,
    query_id: str,
    variant: str,
    *,
    rare_support_threshold: int,
    information_weight_threshold: float,
    broad_container_stop_ratio: float,
    collect_reasons: bool,
) -> tuple[set[str], dict[str, list[dict[str, Any]]]]:
    n = len(index.object_ids)
    record = index.records[query_id]
    candidates: set[str] = set()
    reasons: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if variant == "CG-CUR-6":
        return candidates, reasons
    if variant == "CG-CUR-5":
        postings = index.residual_curated_postings
        query_tokens = record.family_tokens.get("curatorialResidual", ())
    else:
        postings = index.curated_postings
        query_tokens = tuple(
            _token("curatorialRecall", "container", identifier)
            for identifier in record.curated_tokens
        )

    shared_count: Counter[str] = Counter()
    shared_weight: Counter[str] = Counter()
    shared_reasons: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rare_hit: set[str] = set()
    for token in query_tokens:
        posting = postings.get(token, ())
        support = len(posting)
        if support <= 1:
            continue
        support_ratio = support / n
        if support_ratio > broad_container_stop_ratio:
            continue
        weight = math.log((n + 1) / (support + 1))
        for candidate_id in posting:
            if candidate_id == query_id:
                continue
            shared_count[candidate_id] += 1
            shared_weight[candidate_id] += weight
            if support <= rare_support_threshold:
                rare_hit.add(candidate_id)
            if collect_reasons:
                shared_reasons[candidate_id].append(
                    {
                        "reasonType": (
                            "RESIDUAL_CURATORIAL_RECALL"
                            if variant == "CG-CUR-5"
                            else "CURATORIAL_RECALL_ONLY"
                        ),
                        "family": "curatorialRecall",
                        "token": token,
                        "support": support,
                        "denominator": n,
                        "idfWeight": weight,
                        "scoringAllowed": False,
                    }
                )

    for candidate_id in sorted(shared_count):
        include = False
        if variant in {"CG-CUR-1", "CG-CUR-5"}:
            include = shared_count[candidate_id] >= 1
        elif variant == "CG-CUR-2":
            include = shared_count[candidate_id] >= 2
        elif variant == "CG-CUR-3":
            include = candidate_id in rare_hit
        elif variant == "CG-CUR-4":
            include = shared_weight[candidate_id] >= information_weight_threshold
        if include:
            candidates.add(candidate_id)
            if collect_reasons:
                reasons[candidate_id].extend(shared_reasons[candidate_id])
    return candidates, reasons


def generate_exploration_candidates(
    index: CandidateIndex,
    query_id: str,
    *,
    variant: str = "CG-CUR-6",
    direct_posting_max_ratio: float = 0.25,
    include_source: bool = False,
    include_descriptive: bool = True,
    include_interactions: bool = True,
    rare_support_threshold: int = 20,
    information_weight_threshold: float = 1.0,
    broad_container_stop_ratio: float = 1.0,
    fallback_minimum_candidates: int = 0,
    include_reasons: bool = True,
) -> CandidateSet:
    """Generate one deterministic object-local candidate set.

    Candidate IDs are lexically ordered, not score ordered.  Any later ranking
    must be performed by a model module using the same IDs and stable tie-break.
    """

    if variant not in CANDIDATE_VARIANTS:
        raise CandidateIndexError(f"unsupported candidate variant: {variant}")
    if query_id not in index.records:
        raise CandidateIndexError("query is not in the public candidate index")
    if rare_support_threshold < 1:
        raise CandidateIndexError("rare support threshold must be positive")
    if information_weight_threshold < 0:
        raise CandidateIndexError("information threshold cannot be negative")
    if not 0 < broad_container_stop_ratio <= 1:
        raise CandidateIndexError("broad container stop ratio must be in (0, 1]")
    if fallback_minimum_candidates < 0 or fallback_minimum_candidates >= len(index.object_ids):
        raise CandidateIndexError("fallback minimum must be between zero and N-1")

    direct, direct_reasons = _base_candidates(
        index,
        query_id,
        direct_posting_max_ratio=direct_posting_max_ratio,
        include_source=include_source,
        include_descriptive=include_descriptive,
        include_interactions=include_interactions,
        collect_reasons=include_reasons,
    )
    curatorial, curatorial_reasons = _curatorial_candidates(
        index,
        query_id,
        variant,
        rare_support_threshold=rare_support_threshold,
        information_weight_threshold=information_weight_threshold,
        broad_container_stop_ratio=broad_container_stop_ratio,
        collect_reasons=include_reasons,
    )
    combined_set = (direct | curatorial) - {query_id}
    if len(combined_set) < fallback_minimum_candidates:
        record = index.records[query_id]
        permitted_families = {"context", "temporal", "geography"}
        if include_source:
            permitted_families.add("source")
        if include_descriptive:
            permitted_families.add("descriptive")
        fallback_tokens = sorted(
            (
                (len(index.direct_postings.get(token, ())), family, token)
                for family in permitted_families
                for token in record.family_tokens.get(family, ())
                if len(index.direct_postings.get(token, ())) > 1
            ),
            key=lambda row: (row[0], row[1], row[2]),
        )
        fallback_tokens.extend(
            sorted(
                (
                    (len(index.candidate_only_postings.get(token, ())), "geography", token)
                    for token in record.candidate_only_tokens
                    if len(index.candidate_only_postings.get(token, ())) > 1
                ),
                key=lambda row: (row[0], row[1], row[2]),
            )
        )
        fallback_tokens.sort(key=lambda row: (row[0], row[1], row[2]))
        for support, family, token in fallback_tokens:
            posting = index.direct_postings.get(
                token,
                index.candidate_only_postings.get(token, ()),
            )
            for candidate_id in posting:
                if candidate_id == query_id or candidate_id in combined_set:
                    continue
                combined_set.add(candidate_id)
                direct.add(candidate_id)
                if include_reasons:
                    direct_reasons[candidate_id].append({
                        "reasonType": (
                            "CANDIDATE_ONLY_GEOGRAPHY_CLASS_FALLBACK"
                            if token in index.candidate_only_postings
                            else "DETERMINISTIC_HIGH_INFORMATION_FALLBACK"
                        ),
                        "family": family,
                        "token": token,
                        "support": support,
                        "denominator": len(index.object_ids),
                        "scoringAllowed": False,
                    })
                if len(combined_set) >= fallback_minimum_candidates:
                    break
            if len(combined_set) >= fallback_minimum_candidates:
                break
    combined = tuple(sorted(combined_set))
    reasons: dict[str, tuple[dict[str, Any], ...]] = {}
    if include_reasons:
        for candidate_id in combined:
            rows = direct_reasons.get(candidate_id, []) + curatorial_reasons.get(candidate_id, [])
            reasons[candidate_id] = tuple(
                sorted(rows, key=lambda row: (str(row["reasonType"]), str(row["family"]), str(row["token"])))
            )
    policy_parameters = {
        "directPostingMaxRatio": direct_posting_max_ratio,
        "includeSource": include_source,
        "includeDescriptive": include_descriptive,
        "includeInteractions": include_interactions,
        "rareSupportThreshold": rare_support_threshold,
        "informationWeightThreshold": information_weight_threshold,
        "broadContainerStopRatio": broad_container_stop_ratio,
        "fallbackMinimumCandidates": fallback_minimum_candidates,
    }
    policy_metadata = {
        "candidateGenerationSeparatedFromScoring": True,
        "geographyClassCandidateOnly": True,
        "geographyClassScoringAllowed": False,
        "curationUse": "RECALL_SUBSTRATE_ONLY",
        "rawCuratedJaccardScoringAllowed": False,
        "fallbackPolicy": (
            "MOST_INFORMATIVE_APPROVED_QUERY_POSTINGS_THEN_PUBLIC_ID"
            if fallback_minimum_candidates
            else "DISABLED"
        ),
        "randomnessUsed": False,
        "interactionRegistrySha256": index.interaction_registry_sha256,
        "interactionContextSha256": index.interaction_context_sha256,
        "interactionCandidatePolicy": index.interaction_candidate_policy,
        "interactionSelectedPostingsSha256": index.interaction_selected_postings_sha256,
    }
    payload = {
        "queryId": query_id,
        "variant": variant,
        "candidateIds": combined,
        "parameters": policy_parameters,
        "metadata": policy_metadata,
        "candidateIndexSha256": index.index_sha256,
        "randomnessAffectsCandidateSet": False,
    }
    return CandidateSet(
        query_id=query_id,
        variant=variant,
        candidate_ids=combined,
        retrieval_reasons=reasons,
        direct_candidate_count=len(direct),
        curatorial_candidate_count=len(curatorial),
        candidate_pool_count=len(combined),
        possible_other_count=max(0, len(index.object_ids) - 1),
        reduction_ratio=(1 - len(combined) / (len(index.object_ids) - 1)) if len(index.object_ids) > 1 else 0.0,
        candidate_set_sha256=hashlib.sha256(_canonical_json_bytes(payload)).hexdigest(),
        candidate_index_sha256=index.index_sha256,
        policy_parameters=policy_parameters,
        policy_metadata=policy_metadata,
    )


def candidate_pool_distribution(candidate_sets: Iterable[CandidateSet]) -> dict[str, float | int]:
    materialized = tuple(candidate_sets)
    values = sorted(candidate.candidate_pool_count for candidate in materialized)
    if not values:
        return {"count": 0, "p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "max": 0, "zeroCount": 0, "nearFullCount": 0}

    def quantile(probability: float) -> float:
        position = (len(values) - 1) * probability
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return float(values[lower])
        return values[lower] + (values[upper] - values[lower]) * (position - lower)

    possible = max(candidate.possible_other_count for candidate in materialized)
    return {
        "count": len(values),
        "p50": quantile(0.50),
        "p90": quantile(0.90),
        "p95": quantile(0.95),
        "p99": quantile(0.99),
        "max": max(values),
        "zeroCount": sum(value == 0 for value in values),
        "nearFullCount": sum(value >= possible * 0.95 for value in values),
    }


def candidate_recall(
    reference_rankings: Mapping[str, Sequence[str]],
    candidate_sets: Mapping[str, CandidateSet | Sequence[str]],
    *,
    k_values: Sequence[int] = (10, 20, 50),
) -> dict[str, Any]:
    """Compute macro and micro recall against deterministic exhaustive top-k."""

    if any(k <= 0 for k in k_values):
        raise CandidateIndexError("recall k values must be positive")
    per_k: dict[int, list[float]] = {k: [] for k in k_values}
    matched: Counter[int] = Counter()
    denominators: Counter[int] = Counter()
    for query_id in sorted(reference_rankings):
        if query_id not in candidate_sets:
            raise CandidateIndexError("candidate recall input lacks a reference query")
        raw_candidates = candidate_sets[query_id]
        candidate_ids = (
            set(raw_candidates.candidate_ids)
            if isinstance(raw_candidates, CandidateSet)
            else {str(value) for value in raw_candidates}
        )
        if query_id in candidate_ids:
            raise CandidateIndexError("self entered a candidate set")
        ranking: list[str] = []
        for raw in reference_rankings[query_id]:
            if isinstance(raw, Mapping):
                value = str(raw.get("candidateId", ""))
            elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
                value = str(raw[0]) if raw else ""
            else:
                value = str(raw)
            if not value:
                raise CandidateIndexError("reference ranking row lacks a candidate ID")
            if value != query_id:
                ranking.append(value)
        for k in k_values:
            expected = ranking[:k]
            denominator = len(expected)
            count = sum(value in candidate_ids for value in expected)
            matched[k] += count
            denominators[k] += denominator
            per_k[k].append(count / denominator if denominator else 1.0)
    return {
        "queryCount": len(reference_rankings),
        "kValues": list(k_values),
        "macroRecall": {
            str(k): sum(per_k[k]) / len(per_k[k]) if per_k[k] else 0.0 for k in k_values
        },
        "microRecall": {
            str(k): matched[k] / denominators[k] if denominators[k] else 0.0 for k in k_values
        },
        "randomnessAffectsCandidateSet": False,
    }


def evaluate_candidate_variant(
    index: CandidateIndex,
    *,
    variant: str,
    reference_rankings: Mapping[str, Sequence[Any]] | None = None,
    k_values: Sequence[int] = (10, 20, 50),
    **policy_parameters: Any,
) -> dict[str, Any]:
    """Stream one full-cohort policy evaluation without retaining candidate sets."""

    counts: list[int] = []
    zero_count = 0
    near_full_count = 0
    recall_matches: Counter[int] = Counter()
    recall_denominators: Counter[int] = Counter()
    macro_values: dict[int, list[float]] = {k: [] for k in k_values}
    digest = hashlib.sha256()
    started = time.perf_counter()
    for query_id in index.object_ids:
        candidate_set = generate_exploration_candidates(
            index,
            query_id,
            variant=variant,
            include_reasons=False,
            **policy_parameters,
        )
        pool = candidate_set.candidate_pool_count
        counts.append(pool)
        zero_count += int(pool == 0)
        near_full_count += int(pool >= candidate_set.possible_other_count * 0.95)
        digest.update(f"{query_id}\t{candidate_set.candidate_set_sha256}\n".encode("utf-8"))
        if reference_rankings is None:
            continue
        if query_id not in reference_rankings:
            raise CandidateIndexError("candidate evaluation reference lacks a public query")
        candidate_ids = set(candidate_set.candidate_ids)
        reference_ids: list[str] = []
        for raw in reference_rankings[query_id]:
            if isinstance(raw, Mapping):
                value = str(raw.get("candidateId", ""))
            elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
                value = str(raw[0]) if raw else ""
            else:
                value = str(raw)
            if value and value != query_id:
                reference_ids.append(value)
        for k in k_values:
            expected = reference_ids[:k]
            matched = sum(value in candidate_ids for value in expected)
            denominator = len(expected)
            recall_matches[k] += matched
            recall_denominators[k] += denominator
            macro_values[k].append(matched / denominator if denominator else 1.0)

    ordered = sorted(counts)

    def quantile(probability: float) -> float:
        position = (len(ordered) - 1) * probability
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return float(ordered[lower])
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)

    return {
        "variant": variant,
        "queryCount": len(counts),
        "candidatePool": {
            "p50": quantile(0.50),
            "p90": quantile(0.90),
            "p95": quantile(0.95),
            "p99": quantile(0.99),
            "max": max(ordered, default=0),
            "zeroCount": zero_count,
            "nearFullCount": near_full_count,
        },
        "macroRecall": {
            str(k): statistics.fmean(macro_values[k]) if macro_values[k] else None
            for k in k_values
        },
        "microRecall": {
            str(k): (
                recall_matches[k] / recall_denominators[k]
                if recall_denominators[k]
                else None
            )
            for k in k_values
        },
        "candidateSetAggregateSha256": digest.hexdigest(),
        "elapsedMs": (time.perf_counter() - started) * 1000,
        "candidateSetsRetained": 0,
        "pairRowsMaterialized": 0,
        "randomnessAffectsCandidateSet": False,
    }


def self_test() -> dict[str, Any]:
    def token(identifier: str, label: str | None = None) -> dict[str, str]:
        return {"id": identifier, "label": label or identifier}

    records = []
    for ordinal, values in enumerate(
        (
            ("M1", "T1", "D1", "G1", "S1", ("C1", "C2")),
            ("M1", "T2", "D1", "G2", "S2", ("C1", "C2")),
            ("M2", "T1", "D2", "G1", "S1", ("C1",)),
            ("M3", "T3", "D3", "G3", "S3", ("C3",)),
        ),
        start=1,
    ):
        medium, theme, decade, geography, source, curated = values
        records.append(
            {
                "objectId": f"SURF-T{ordinal}",
                "medium": [token(medium)],
                "theme": [token(theme)],
                "movement_context": [],
                "decade": [token(decade)],
                "geography": [token(geography)],
                "curated_container": [token(value) for value in curated],
                "source": token(source),
                "object_type": token("OT1"),
                "creator": token(f"CR{ordinal}"),
                "startYear": 1900 + ordinal,
                "endYear": 1900 + ordinal,
                "temporalPrecision": "year",
                "geographyMappingStates": ["mapped"],
                "geographyClasses": ["country"],
                "geographyQualified": False,
                "multiRegion": False,
            }
        )
    index = build_exploration_candidate_index(records)
    one = generate_exploration_candidates(index, "SURF-T1", variant="CG-CUR-1", direct_posting_max_ratio=1.0)
    two = generate_exploration_candidates(index, "SURF-T1", variant="CG-CUR-2", direct_posting_max_ratio=1.0)
    six = generate_exploration_candidates(index, "SURF-T1", variant="CG-CUR-6", direct_posting_max_ratio=1.0)
    if "SURF-T1" in one.candidate_ids or one.randomness_affects_candidate_set:
        raise AssertionError("candidate self/randomness invariant failed")
    if not set(two.candidate_ids).issubset(one.candidate_ids):
        raise AssertionError("two-container candidates are not a subset of any-container candidates")
    if not set(six.candidate_ids).issubset(one.candidate_ids):
        raise AssertionError("direct candidates were lost when curation was enabled")
    geography_class_reasons = [
        reason
        for candidate_id in one.candidate_ids
        for reason in one.retrieval_reasons.get(candidate_id, ())
        if reason.get("reasonType") == "CANDIDATE_ONLY_GEOGRAPHY_CLASS_FALLBACK"
    ]
    if (
        not index.candidate_only_postings
        or not geography_class_reasons
        or any(reason.get("scoringAllowed") is not False for reason in geography_class_reasons)
        or any(
            "geography_class" in token
            for record in index.records.values()
            for tokens in record.family_tokens.values()
            for token in tokens
        )
    ):
        raise AssertionError(
            "geography-class candidate fallback is absent or leaked into scoring tokens"
        )
    if index.index_sha256 != build_exploration_candidate_index(list(reversed(records))).index_sha256:
        raise AssertionError("candidate index is input-order dependent")
    fabricated_posting_rejected = False
    try:
        build_exploration_candidate_index(
            records,
            interaction_tokens_by_object={"SURF-T1": ("EXP:INTERACTION:FABRICATED",)},
        )
    except CandidateIndexError:
        fabricated_posting_rejected = True
    if not fabricated_posting_rejected:
        raise AssertionError("candidate index accepted an untrusted interaction posting")
    import interaction_statistics

    interaction_records: list[dict[str, Any]] = []
    for ordinal in range(1, 7):
        template = records[0] if ordinal <= 5 else records[3]
        value = json.loads(json.dumps(template))
        value["objectId"] = f"SURF-IP{ordinal}"
        value["creator"] = token(f"IP-CREATOR-{ordinal}")
        interaction_records.append(value)
    registry = interaction_statistics.build_observed_interaction_registry(
        interaction_records,
        pair_specs=(("medium", "theme"),),
        triple_specs=(),
    )
    trusted = interaction_statistics.build_trusted_interaction_context(
        registry,
        interaction_records,
    )
    trusted_index = build_exploration_candidate_index(
        interaction_records,
        trusted_interaction_context=trusted,
    )
    if (
        trusted_index.interaction_registry_sha256 != registry["registrySha256"]
        or trusted_index.interaction_context_sha256 != trusted.context_sha256
        or not trusted_index.interaction_postings
    ):
        raise AssertionError("trusted interaction posting contract was not preserved")
    for token_value, posting in trusted_index.interaction_postings.items():
        interaction_id = token_value.rsplit("\x1f", 1)[-1]
        if len(posting) != int(trusted.interactions_by_id[interaction_id]["support"]):
            raise AssertionError("trusted candidate posting support did not reconcile")
    fabricated_context_rejected = False
    try:
        build_exploration_candidate_index(
            interaction_records,
            trusted_interaction_context=interaction_statistics.TrustedInteractionContext(
                registry_sha256="0" * 64,
                public_object_ids=tuple(
                    sorted(record["objectId"] for record in interaction_records)
                ),
                interactions_by_id={},
                object_interaction_ids={
                    record["objectId"]: frozenset() for record in interaction_records
                },
                context_sha256="0" * 64,
            ),
        )
    except CandidateIndexError:
        fabricated_context_rejected = True
    if not fabricated_context_rejected:
        raise AssertionError("candidate index accepted a fabricated trusted context")
    alternate_interaction_records = json.loads(json.dumps(interaction_records))
    alternate_interaction_records[0]["medium"] = [token("M-ALTERED")]
    alternate_registry = interaction_statistics.build_observed_interaction_registry(
        alternate_interaction_records,
        pair_specs=(("medium", "theme"),),
        triple_specs=(),
    )
    alternate_context = interaction_statistics.build_trusted_interaction_context(
        alternate_registry,
        alternate_interaction_records,
    )
    cross_record_context_rejected = False
    try:
        build_exploration_candidate_index(
            interaction_records,
            trusted_interaction_context=alternate_context,
        )
    except CandidateIndexError:
        cross_record_context_rejected = True
    if not cross_record_context_rejected:
        raise AssertionError("candidate index accepted an interaction context from altered records")
    temporal_mutation = json.loads(json.dumps(records))
    temporal_mutation[0]["startYear"] += 1
    temporal_mutation[0]["endYear"] += 1
    mutated_index = build_exploration_candidate_index(temporal_mutation)
    if (
        mutated_index.scoring_records_sha256 == index.scoring_records_sha256
        or mutated_index.index_sha256 == index.index_sha256
    ):
        raise AssertionError("candidate index hash did not bind a temporal scorer input")
    return {
        "status": "PASS",
        "candidateVariantCount": len(CANDIDATE_VARIANTS),
        "indexSha256": index.index_sha256,
        "selfCandidateCount": 0,
        "randomnessAffectsCandidateSet": False,
        "fabricatedInteractionPostingRejected": fabricated_posting_rejected,
        "fabricatedInteractionContextRejected": fabricated_context_rejected,
        "crossRecordInteractionContextRejected": cross_record_context_rejected,
        "geographyClassCandidateOnlyPostingCount": len(index.candidate_only_postings),
        "geographyClassScoringAllowed": False,
        "trustedInteractionPostingCount": len(trusted_index.interaction_postings),
        "trustedInteractionRegistrySha256": trusted_index.interaction_registry_sha256,
        "temporalMutationChangedScoringRecordHash": True,
        "temporalMutationChangedIndexHash": True,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
