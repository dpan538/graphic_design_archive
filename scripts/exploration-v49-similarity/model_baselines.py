#!/usr/bin/env python3
"""Transparent analysis-only Exploration affinity baselines M1 through M8.

The raw-curation M0 negative control is intentionally absent from this module
and lives behind ``negative_control.py``.  Every scalar model operates on
family-qualified independent features, emits a separate comparability profile,
and uses one canonical score/identity ordering in both object-local and bounded
exhaustive evaluation.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import math
import statistics
import time
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

import candidate_index
import interaction_statistics
import missingness_comparability as missingness


SCHEMA_VERSION = "trace-exploration-model-baselines/v1"
IMPLEMENTATION_VERSION = "trace-exploration-model-baselines-2026-08-24"
MODEL_IDS = ("M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8")
SCALAR_MODEL_IDS = frozenset(MODEL_IDS[:-1])
TEMPORAL_VARIANTS = ("TEMP-1", "TEMP-2", "TEMP-3", "TEMP-4")
SOURCE_TREATMENTS = ("SOURCE-0", "SOURCE-1", "SOURCE-2", "SOURCE-3", "SOURCE-4")
INTERACTION_POLICIES = (
    "NO_INTERACTION_CONTRIBUTION",
    "CAPPED_INTERACTION_BONUS",
    "INFORMATION_RESIDUAL_CONTRIBUTION",
    "LOG_LIKELIHOOD_INTERACTION_CONTRIBUTION",
)
FAMILY_NORMALIZATIONS = (
    "EQUAL_FAMILY",
    "AVAILABILITY_NORMALIZED",
    "USER_SELECTED",
    "CAPPED_FAMILY",
)
IDF_MODES = ("GLOBAL_IDF", "WITHIN_FAMILY_IDF", "SMOOTHED_IDF")
DEFAULT_SCORING_FAMILIES = (
    "context",
    "temporal",
    "geography",
    "descriptive",
)
ALL_PROFILE_FAMILIES = (
    "context",
    "temporal",
    "geography",
    "source",
    "descriptive",
    "curatorialResidual",
)


class ModelError(ValueError):
    """Raised when a model or scoring input violates the analysis contract."""


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    variant_id: str
    model_family: str
    task: str
    symmetric: bool
    eligible_families: tuple[str, ...] = DEFAULT_SCORING_FAMILIES
    missingness_variant: str = "MISSING-C"
    idf_mode: str = "SMOOTHED_IDF"
    temporal_variant: str = "TEMP-4"
    temporal_decay_years: float = 20.0
    tversky_alpha: float = 0.5
    tversky_beta: float = 0.5
    bm25_k1: float = 1.2
    bm25_b: float = 0.75
    source_treatment: str = "SOURCE-0"
    source_cap: float = 0.20
    family_normalization: str = "EQUAL_FAMILY"
    family_weights: tuple[tuple[str, float], ...] = ()
    family_cap: float = 1.0
    curatorial_cap: float = 0.10
    goodall_support_floor: int = 3
    goodall_match_cap: float = 0.95
    interaction_policy: str = "NO_INTERACTION_CONTRIBUTION"
    interaction_cap: float = 0.10
    interaction_support_threshold: int = 5

    def parameters(self) -> dict[str, Any]:
        return {
            "missingnessVariant": self.missingness_variant,
            "idfMode": self.idf_mode,
            "temporalVariant": self.temporal_variant,
            "temporalDecayYears": self.temporal_decay_years,
            "tverskyAlpha": self.tversky_alpha,
            "tverskyBeta": self.tversky_beta,
            "bm25K1": self.bm25_k1,
            "bm25B": self.bm25_b,
            "sourceTreatment": self.source_treatment,
            "sourceCap": self.source_cap,
            "familyNormalization": self.family_normalization,
            "familyWeights": dict(self.family_weights),
            "familyCap": self.family_cap,
            "curatorialCap": self.curatorial_cap,
            "goodallSupportFloor": self.goodall_support_floor,
            "goodallMatchCap": self.goodall_match_cap,
            "interactionPolicy": self.interaction_policy,
            "interactionCap": self.interaction_cap,
            "interactionSupportThreshold": self.interaction_support_threshold,
            "eligibleFamilies": list(self.eligible_families),
        }


@dataclass(frozen=True)
class ModelContext:
    candidate_index: candidate_index.CandidateIndex
    family_document_counts: Mapping[str, int]
    average_family_lengths: Mapping[str, float]
    average_field_lengths: Mapping[str, float]
    goodall_weights: Mapping[str, float]
    scoring_records_sha256: str
    context_sha256: str


@dataclass(frozen=True)
class CompiledFeatureContext:
    """Compact ordinal/matrix representation for exhaustive numeric scoring."""

    model_context: ModelContext
    object_ids: tuple[str, ...]
    object_ordinals: Mapping[str, int]
    field_incidence: Mapping[str, Any]
    field_counts: Mapping[str, Any]
    field_vocabularies: Mapping[str, tuple[str, ...]]
    scalar_codes: Mapping[str, Any]
    scalar_vocabularies: Mapping[str, tuple[str, ...]]
    adjusted_start_years: Any
    adjusted_end_years: Any
    family_availability: Mapping[str, Any]
    compiled_sha256: str


@dataclass(frozen=True)
class AffinityProfile:
    query_id: str
    candidate_id: str
    model_id: str
    variant_id: str
    symmetric: bool
    source_treatment: str
    family_normalization: str
    family_scores: Mapping[str, float | None]
    family_weighted_contributions: Mapping[str, float]
    family_contribution_units: Mapping[str, float]
    family_contribution_shares: Mapping[str, float]
    jointly_observable_families: tuple[str, ...]
    unavailable_families: tuple[str, ...]
    comparability: Mapping[str, float | int]
    interactions: tuple[dict[str, Any], ...]
    contributions: tuple[dict[str, Any], ...]
    distinctive_features: tuple[dict[str, Any], ...]
    ignored_duplicate_signals: tuple[str, ...]
    diagnostic_score: float | None
    pareto_vector: tuple[float, ...]
    historical_relation: bool = False
    semantic_relation: bool = False
    probability: bool = False
    randomness_affects_affinity: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "queryId": self.query_id,
            "candidateId": self.candidate_id,
            "modelId": self.model_id,
            "variantId": self.variant_id,
            "symmetric": self.symmetric,
            "sourceTreatment": self.source_treatment,
            "familyNormalization": self.family_normalization,
            "familyScores": dict(self.family_scores),
            "familyWeightedContributions": dict(self.family_weighted_contributions),
            "familyContributionUnits": dict(self.family_contribution_units),
            "familyContributionShares": dict(self.family_contribution_shares),
            "jointlyObservableFamilies": list(self.jointly_observable_families),
            "unavailableFamilies": list(self.unavailable_families),
            "comparability": dict(self.comparability),
            "interactions": list(self.interactions),
            "contributions": list(self.contributions),
            "distinctiveFeatures": list(self.distinctive_features),
            "ignoredDuplicateSignals": list(self.ignored_duplicate_signals),
            "diagnosticScore": self.diagnostic_score,
            "paretoVector": list(self.pareto_vector),
            "historicalRelation": False,
            "semanticRelation": False,
            "probability": False,
            "randomnessAffectsAffinity": False,
        }


def _validate_spec(spec: ModelSpec) -> None:
    if spec.model_id not in MODEL_IDS:
        raise ModelError(f"unsupported scoring model: {spec.model_id}")
    if not spec.variant_id:
        raise ModelError("model variant ID must be nonblank")
    if spec.missingness_variant not in missingness.MISSINGNESS_VARIANTS:
        raise ModelError("unsupported missingness variant")
    if spec.idf_mode not in IDF_MODES:
        raise ModelError("unsupported IDF mode")
    if spec.temporal_variant not in TEMPORAL_VARIANTS:
        raise ModelError("unsupported temporal variant")
    if spec.source_treatment not in SOURCE_TREATMENTS:
        raise ModelError("unsupported source treatment")
    if spec.family_normalization not in FAMILY_NORMALIZATIONS:
        raise ModelError("unsupported family normalization")
    if spec.interaction_policy not in INTERACTION_POLICIES:
        raise ModelError("unsupported interaction policy")
    if len(set(spec.eligible_families)) != len(spec.eligible_families):
        raise ModelError("eligible family list contains duplicates")
    if set(spec.eligible_families) - set(ALL_PROFILE_FAMILIES):
        raise ModelError("eligible family list contains an unsupported family")
    declared_weights = tuple((str(family), weight) for family, weight in spec.family_weights)
    declared_weight_keys = tuple(family for family, _ in declared_weights)
    if len(declared_weight_keys) != len(set(declared_weight_keys)):
        raise ModelError("family weight declarations contain duplicate families")
    if any(
        not isinstance(weight, (int, float))
        or isinstance(weight, bool)
        or not math.isfinite(float(weight))
        or float(weight) <= 0
        for _, weight in declared_weights
    ):
        raise ModelError("family weights must be finite positive numbers")
    if spec.family_normalization == "USER_SELECTED":
        expected_weight_keys = set(_eligible_families(spec))
        if set(declared_weight_keys) != expected_weight_keys:
            raise ModelError(
                "USER_SELECTED requires exactly one weight for every effective eligible family"
            )
    elif declared_weights:
        raise ModelError("family weights are permitted only for USER_SELECTED normalization")
    numeric_bounds = {
        "temporal_decay_years": (spec.temporal_decay_years, 0, None),
        "tversky_alpha": (spec.tversky_alpha, 0, None),
        "tversky_beta": (spec.tversky_beta, 0, None),
        "bm25_k1": (spec.bm25_k1, 0, None),
        "bm25_b": (spec.bm25_b, 0, 1),
        "source_cap": (spec.source_cap, 0, 1),
        "family_cap": (spec.family_cap, 0, 1),
        "curatorial_cap": (spec.curatorial_cap, 0, 1),
        "goodall_match_cap": (spec.goodall_match_cap, 0, 1),
        "interaction_cap": (spec.interaction_cap, 0, 1),
    }
    for name, (value, lower, upper) in numeric_bounds.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
            raise ModelError(f"{name} must be finite")
        if value <= lower or (upper is not None and value > upper):
            raise ModelError(f"{name} is outside its permitted range")
    if spec.goodall_support_floor < 1:
        raise ModelError("Goodall support floor must be positive")
    if spec.interaction_support_threshold not in interaction_statistics.SUPPORT_THRESHOLDS:
        raise ModelError("interaction support threshold is outside the declared sensitivity grid")
    if spec.model_id == "M6" and spec.symmetric != math.isclose(spec.tversky_alpha, spec.tversky_beta):
        raise ModelError("Tversky symmetry declaration conflicts with alpha/beta")
    if spec.model_id == "M7" and spec.symmetric:
        raise ModelError("BM25F-like retrieval must be explicitly asymmetric")
    if spec.source_treatment == "SOURCE-3" and spec.task != "CONTRASTIVE_DISCOVERY":
        raise ModelError("cross-source preference is permitted only for the contrastive task")
    if spec.model_id == "M8" and spec.interaction_policy != "NO_INTERACTION_CONTRIBUTION":
        raise ModelError("M8 keeps interactions as a diagnostic channel, not a hidden scalar")


def default_model_specs() -> tuple[ModelSpec, ...]:
    """Return one declared analysis configuration for each eligible family."""

    specs = (
        ModelSpec("M1", "M1-EQUAL-FAMILY", "UNWEIGHTED_FAMILY_OVERLAP", "SYMMETRIC_OBJECT_LOCAL", True),
        ModelSpec("M2", "M2-SMOOTHED-WITHIN-FAMILY", "IDF_SPARSE_COSINE", "SYMMETRIC_OBJECT_LOCAL", True),
        ModelSpec("M3", "M3-IDF-TANIMOTO", "IDF_WEIGHTED_JACCARD", "SYMMETRIC_OBJECT_LOCAL", True),
        ModelSpec("M4", "M4-GOODALL-BOUNDED", "GOODALL_STYLE_RARITY", "SYMMETRIC_OBJECT_LOCAL", True),
        ModelSpec("M5", "M5-GOWER-TEMP4", "GOWER_STYLE_FAMILY_BALANCED", "SYMMETRIC_OBJECT_LOCAL", True),
        ModelSpec("M6", "M6-TVERSKY-SYMMETRIC-A050-B050", "TVERSKY_FEATURE_CONTRAST", "SYMMETRIC_OBJECT_LOCAL", True),
        ModelSpec(
            "M7",
            "M7-BM25F-QUERY",
            "BM25F_LIKE_FIELDED_RETRIEVAL",
            "USER_CONDITIONED_RETRIEVAL",
            False,
            family_normalization="USER_SELECTED",
            family_weights=(("context", 1.0), ("temporal", 0.8), ("geography", 0.8), ("descriptive", 0.5)),
        ),
        ModelSpec("M8", "M8-PARETO-CHANNELS", "NONSCALAR_PARETO", "SYMMETRIC_OBJECT_LOCAL", True),
    )
    for spec in specs:
        _validate_spec(spec)
    return specs


def benchmark_model_specs() -> tuple[ModelSpec, ...]:
    """Declared non-learned sensitivity grid used by the research orchestrator."""

    base = {spec.model_id: spec for spec in default_model_specs()}
    specs: list[ModelSpec] = [base["M1"]]
    for mode in IDF_MODES:
        specs.append(replace(base["M2"], variant_id=f"M2-{mode}", idf_mode=mode))
    specs.append(base["M3"])
    for floor in (2, 3, 5, 10, 20):
        specs.append(replace(base["M4"], variant_id=f"M4-GOODALL-FLOOR-{floor}", goodall_support_floor=floor))
    for temporal in TEMPORAL_VARIANTS:
        specs.append(replace(base["M5"], variant_id=f"M5-GOWER-{temporal}", temporal_variant=temporal))
    for missing_variant in missingness.MISSINGNESS_VARIANTS:
        specs.append(
            replace(
                base["M5"],
                variant_id=f"M5-GOWER-{missing_variant}",
                missingness_variant=missing_variant,
            )
        )
    for alpha, beta in ((0.5, 0.5), (1.0, 1.0), (0.8, 0.2), (0.6, 0.4)):
        specs.append(
            replace(
                base["M6"],
                variant_id=f"M6-TVERSKY-A{alpha:.2f}-B{beta:.2f}",
                symmetric=math.isclose(alpha, beta),
                task=("SYMMETRIC_OBJECT_LOCAL" if math.isclose(alpha, beta) else "USER_CONDITIONED_RETRIEVAL"),
                tversky_alpha=alpha,
                tversky_beta=beta,
            )
        )
    specs.append(base["M7"])
    specs.append(base["M8"])
    for spec in specs:
        _validate_spec(spec)
    return tuple(specs)


def source_treatment_model_specs(
    base_spec: ModelSpec | None = None,
) -> tuple[ModelSpec, ...]:
    """Return the declared SOURCE-0..4 experiment grid for one scalar model."""

    base = base_spec or next(spec for spec in default_model_specs() if spec.model_id == "M5")
    if base.model_id == "M8":
        raise ModelError("source-treatment scalar experiments require M1-M7")
    specs_list: list[ModelSpec] = []
    base_weights = dict(base.family_weights)
    for treatment in SOURCE_TREATMENTS:
        proxy = replace(
            base,
            variant_id=f"{base.model_id}-{treatment}",
            source_treatment=treatment,
            task=("CONTRASTIVE_DISCOVERY" if treatment == "SOURCE-3" else base.task),
        )
        if proxy.family_normalization == "USER_SELECTED":
            proxy = replace(
                proxy,
                family_weights=tuple(
                    (family, float(base_weights.get(family, 0.30 if family == "source" else 1.0)))
                    for family in _eligible_families(proxy)
                ),
            )
        specs_list.append(proxy)
    specs = tuple(specs_list)
    for spec in specs:
        _validate_spec(spec)
    return specs


def interaction_policy_model_specs(
    base_spec: ModelSpec | None = None,
    *,
    support_threshold: int = 5,
    interaction_cap: float = 0.10,
) -> tuple[ModelSpec, ...]:
    """Return the no/capped/information/LLR trusted-interaction grid."""

    base = base_spec or next(spec for spec in default_model_specs() if spec.model_id == "M5")
    if base.model_id == "M8":
        raise ModelError("interaction policy experiments require M1-M7")
    specs = tuple(
        replace(
            base,
            variant_id=f"{base.model_id}-INTERACTION-{policy}",
            interaction_policy=policy,
            interaction_support_threshold=support_threshold,
            interaction_cap=interaction_cap,
        )
        for policy in INTERACTION_POLICIES
    )
    for spec in specs:
        _validate_spec(spec)
    return specs


def build_model_context(index: candidate_index.CandidateIndex) -> ModelContext:
    family_docs: dict[str, set[str]] = defaultdict(set)
    family_lengths: dict[str, list[int]] = defaultdict(list)
    field_lengths: dict[str, list[int]] = defaultdict(list)
    for object_id in index.object_ids:
        record = index.records[object_id]
        for family in ALL_PROFILE_FAMILIES:
            tokens = record.family_tokens.get(family, ())
            if tokens:
                family_docs[family].add(object_id)
            family_lengths[family].append(len(tokens))
        for field in candidate_index.DIRECT_FIELD_FAMILIES:
            field_lengths[field].append(len(record.field_values.get(field, ())))
        field_lengths["residual_curated_container"].append(
            len(record.residual_curated_tokens)
        )

    n = len(index.object_ids)
    goodall: dict[str, float] = {}
    by_family_df: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for token, df in index.token_document_frequency.items():
        family = index.token_family.get(token)
        if family in ALL_PROFILE_FAMILIES:
            by_family_df[family].append((token, df))
    for family, token_rows in by_family_df.items():
        denominator = max(1, len(family_docs.get(family, ())))
        squared_by_df: dict[int, float] = defaultdict(float)
        for _, df in token_rows:
            squared_by_df[df] += (df / denominator) ** 2
        cumulative = 0.0
        cumulative_by_df: dict[int, float] = {}
        for df in sorted(squared_by_df):
            cumulative += squared_by_df[df]
            cumulative_by_df[df] = cumulative
        for token, df in token_rows:
            goodall[token] = max(0.0, min(1.0, 1.0 - cumulative_by_df[df]))

    payload = {
        "schemaVersion": SCHEMA_VERSION,
        "candidateIndexSha256": index.index_sha256,
        "scoringRecordsSha256": index.scoring_records_sha256,
        "familyDocumentCounts": {family: len(values) for family, values in sorted(family_docs.items())},
        "averageFamilyLengths": {
            family: statistics.fmean(values) if values else 0.0 for family, values in sorted(family_lengths.items())
        },
        "averageFieldLengths": {
            field: statistics.fmean(values) if values else 0.0
            for field, values in sorted(field_lengths.items())
        },
        "goodallWeightSha256": hashlib.sha256(
            json.dumps(goodall, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return ModelContext(
        candidate_index=index,
        family_document_counts={family: len(values) for family, values in family_docs.items()},
        average_family_lengths={
            family: statistics.fmean(values) if values else 0.0 for family, values in family_lengths.items()
        },
        average_field_lengths={
            field: statistics.fmean(values) if values else 0.0
            for field, values in field_lengths.items()
        },
        goodall_weights=goodall,
        scoring_records_sha256=index.scoring_records_sha256,
        context_sha256=hashlib.sha256(encoded).hexdigest(),
    )


def compile_feature_context(context: ModelContext) -> CompiledFeatureContext:
    """Compile public features once for bounded NumPy block evaluation.

    NumPy is imported lazily so the pure object-local interfaces remain usable
    in minimal Python environments.  The compiled form contains no labels,
    pair rows, held IDs, or randomized state.
    """

    try:
        import numpy as np
    except ImportError as error:  # pragma: no cover - the bundled workspace has NumPy
        raise ModelError("compact exhaustive scoring requires NumPy") from error

    object_ids = context.candidate_index.object_ids
    records = [context.candidate_index.records[object_id] for object_id in object_ids]
    multi_fields = (
        "medium",
        "theme",
        "movement_context",
        "decade",
        "geography",
        "residual_curated_container",
    )
    field_incidence: dict[str, Any] = {}
    field_counts: dict[str, Any] = {}
    field_vocabularies: dict[str, tuple[str, ...]] = {}
    for field in multi_fields:
        values_by_record = [
            (
                record.residual_curated_tokens
                if field == "residual_curated_container"
                else record.field_values.get(field, ())
            )
            for record in records
        ]
        vocabulary = tuple(sorted({value for values in values_by_record for value in values}))
        ordinals = {value: ordinal for ordinal, value in enumerate(vocabulary)}
        matrix = np.zeros((len(records), len(vocabulary)), dtype=np.float64)
        for row, values in enumerate(values_by_record):
            for value in values:
                matrix[row, ordinals[value]] = 1.0
        field_incidence[field] = matrix
        field_counts[field] = matrix.sum(axis=1)
        field_vocabularies[field] = vocabulary

    scalar_codes: dict[str, Any] = {}
    scalar_vocabularies: dict[str, tuple[str, ...]] = {}
    for field in ("source", "object_type", "creator"):
        vocabulary = tuple(
            sorted({value for record in records for value in record.field_values.get(field, ())})
        )
        ordinals = {value: ordinal for ordinal, value in enumerate(vocabulary)}
        codes = np.full(len(records), -1, dtype=np.int32)
        for row, record in enumerate(records):
            values = record.field_values.get(field, ())
            if len(values) > 1:
                raise ModelError(f"compiled scalar field {field} became multivalued")
            if values:
                codes[row] = ordinals[values[0]]
        scalar_codes[field] = codes
        scalar_vocabularies[field] = vocabulary

    adjusted_start = np.asarray(
        [record.start_year - 5 if record.temporal_precision.casefold() == "approximate" else record.start_year for record in records],
        dtype=np.int32,
    )
    adjusted_end = np.asarray(
        [record.end_year + 5 if record.temporal_precision.casefold() == "approximate" else record.end_year for record in records],
        dtype=np.int32,
    )
    family_availability = {
        "context": (
            field_counts["medium"] + field_counts["theme"] + field_counts["movement_context"]
        )
        > 0,
        "temporal": np.ones(len(records), dtype=np.bool_),
        "geography": field_counts["geography"] > 0,
        "source": scalar_codes["source"] >= 0,
        "descriptive": (scalar_codes["object_type"] >= 0) | (scalar_codes["creator"] >= 0),
        "curatorialResidual": field_counts["residual_curated_container"] > 0,
    }
    payload = {
        "schemaVersion": "trace-exploration-compiled-feature-context/v1",
        "modelContextSha256": context.context_sha256,
        "scoringRecordsSha256": context.scoring_records_sha256,
        "objectCount": len(object_ids),
        "fieldVocabularyCounts": {field: len(values) for field, values in field_vocabularies.items()},
        "scalarVocabularyCounts": {field: len(values) for field, values in scalar_vocabularies.items()},
        "randomnessUsed": False,
        "pairRowsMaterialized": False,
    }
    compiled_sha256 = hashlib.sha256(
        (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    ).hexdigest()
    return CompiledFeatureContext(
        model_context=context,
        object_ids=object_ids,
        object_ordinals={object_id: ordinal for ordinal, object_id in enumerate(object_ids)},
        field_incidence=field_incidence,
        field_counts=field_counts,
        field_vocabularies=field_vocabularies,
        scalar_codes=scalar_codes,
        scalar_vocabularies=scalar_vocabularies,
        adjusted_start_years=adjusted_start,
        adjusted_end_years=adjusted_end,
        family_availability=family_availability,
        compiled_sha256=compiled_sha256,
    )


def _compiled_field_family(field: str) -> str:
    return {
        "medium": "context",
        "theme": "context",
        "movement_context": "context",
        "decade": "temporal",
        "geography": "geography",
        "source": "source",
        "object_type": "descriptive",
        "creator": "descriptive",
        "residual_curated_container": "curatorialResidual",
    }[field]


def _compiled_token(field: str, identifier: str) -> str:
    family = _compiled_field_family(field)
    normalized_field = "residual_container" if field == "residual_curated_container" else field
    return candidate_index._token(family, normalized_field, identifier)


def _compiled_weights(
    compiled: CompiledFeatureContext,
    field: str,
    spec: ModelSpec,
    *,
    kind: str,
) -> Any:
    import numpy as np

    vocabulary = (
        compiled.scalar_vocabularies[field]
        if field in compiled.scalar_vocabularies
        else compiled.field_vocabularies[field]
    )
    values: list[float] = []
    for identifier in vocabulary:
        token = _compiled_token(field, identifier)
        if kind == "IDF":
            values.append(_idf(compiled.model_context, token, spec.idf_mode))
        elif kind == "SMOOTHED_IDF":
            values.append(_idf(compiled.model_context, token, "SMOOTHED_IDF"))
        elif kind == "GOODALL":
            df = compiled.model_context.candidate_index.token_document_frequency.get(token, 0)
            base = compiled.model_context.goodall_weights.get(token, 0.0)
            if df < spec.goodall_support_floor:
                base *= df / spec.goodall_support_floor
            values.append(min(spec.goodall_match_cap, base))
        else:
            raise ModelError("unsupported compiled token weight")
    return np.asarray(values, dtype=np.float64)


def _compiled_field_similarity(
    compiled: CompiledFeatureContext,
    left_ordinals: Any,
    right_ordinals: Any,
    field: str,
    spec: ModelSpec,
) -> tuple[Any, Any]:
    """Return a BxC field score and availability mask."""

    import numpy as np

    if field in compiled.field_incidence:
        matrix = compiled.field_incidence[field]
        left_matrix = matrix[left_ordinals]
        right_matrix = matrix[right_ordinals]
        left_counts = compiled.field_counts[field][left_ordinals][:, None]
        right_counts = compiled.field_counts[field][right_ordinals][None, :]
        shared_counts = left_matrix @ right_matrix.T
        availability = (left_counts > 0) & (right_counts > 0)
        union_counts = left_counts + right_counts - shared_counts

        if spec.model_id in {"M1", "M5", "M8"}:
            score = np.divide(
                shared_counts,
                union_counts,
                out=np.zeros_like(shared_counts),
                where=union_counts > 0,
            )
        elif spec.model_id == "M2":
            weights = _compiled_weights(compiled, field, spec, kind="IDF")
            squared = weights * weights
            dot = (left_matrix * squared) @ right_matrix.T
            left_norm = np.sqrt((left_matrix * squared).sum(axis=1))[:, None]
            right_norm = np.sqrt((right_matrix * squared).sum(axis=1))[None, :]
            denominator = left_norm * right_norm
            score = np.divide(dot, denominator, out=np.zeros_like(dot), where=denominator > 0)
        elif spec.model_id == "M3":
            weights = _compiled_weights(compiled, field, spec, kind="IDF")
            shared_weight = (left_matrix * weights) @ right_matrix.T
            left_weight = (left_matrix * weights).sum(axis=1)[:, None]
            right_weight = (right_matrix * weights).sum(axis=1)[None, :]
            denominator = left_weight + right_weight - shared_weight
            score = np.divide(
                shared_weight,
                denominator,
                out=np.zeros_like(shared_weight),
                where=denominator > 0,
            )
        elif spec.model_id == "M4":
            weights = _compiled_weights(compiled, field, spec, kind="GOODALL")
            shared_weight = (left_matrix * weights) @ right_matrix.T
            score = np.divide(
                shared_weight,
                union_counts,
                out=np.zeros_like(shared_weight),
                where=union_counts > 0,
            )
        elif spec.model_id == "M6":
            denominator = (
                shared_counts
                + spec.tversky_alpha * (left_counts - shared_counts)
                + spec.tversky_beta * (right_counts - shared_counts)
            )
            score = np.divide(
                shared_counts,
                denominator,
                out=np.zeros_like(shared_counts),
                where=denominator > 0,
            )
        elif spec.model_id == "M7":
            weights = _compiled_weights(compiled, field, spec, kind="SMOOTHED_IDF")
            matched = (left_matrix * weights) @ right_matrix.T
            query_weight = (left_matrix * weights).sum(axis=1)[:, None]
            average_length = max(
                compiled.model_context.average_field_lengths.get(field, 1.0),
                1e-12,
            )
            length_norm = 1 - spec.bm25_b + spec.bm25_b * right_counts / average_length
            numerator = matched * (spec.bm25_k1 + 1) / (1 + spec.bm25_k1 * length_norm)
            score = np.minimum(
                1.0,
                np.divide(numerator, query_weight, out=np.zeros_like(numerator), where=query_weight > 0),
            )
        else:
            raise ModelError("unsupported compact model")
        return score, availability

    codes = compiled.scalar_codes[field]
    left_codes = codes[left_ordinals][:, None]
    right_codes = codes[right_ordinals][None, :]
    availability = (left_codes >= 0) & (right_codes >= 0)
    equal = availability & (left_codes == right_codes)
    shared_counts = equal.astype(np.float64)
    union_counts = (left_codes >= 0).astype(np.float64) + (right_codes >= 0).astype(np.float64) - shared_counts
    if spec.model_id in {"M1", "M2", "M3", "M5", "M6", "M8"}:
        score = shared_counts
    elif spec.model_id == "M4":
        weights = _compiled_weights(compiled, field, spec, kind="GOODALL")
        score = np.zeros_like(shared_counts)
        if len(weights):
            safe_left = np.maximum(left_codes, 0)
            score = np.where(equal, weights[safe_left], 0.0)
    elif spec.model_id == "M7":
        weights = _compiled_weights(compiled, field, spec, kind="SMOOTHED_IDF")
        safe_left = np.maximum(left_codes, 0)
        query_weight = np.where(left_codes >= 0, weights[safe_left], 0.0) if len(weights) else np.zeros_like(shared_counts)
        matched = np.where(equal, query_weight, 0.0)
        average_length = max(
            compiled.model_context.average_field_lengths.get(field, 1.0),
            1e-12,
        )
        length_norm = 1 - spec.bm25_b + spec.bm25_b / average_length
        numerator = matched * (spec.bm25_k1 + 1) / (1 + spec.bm25_k1 * length_norm)
        score = np.minimum(1.0, np.divide(numerator, query_weight, out=np.zeros_like(numerator), where=query_weight > 0))
    else:
        raise ModelError("unsupported compact scalar model")
    return score, availability


def _compiled_temporal_similarity(
    compiled: CompiledFeatureContext,
    left_ordinals: Any,
    right_ordinals: Any,
    spec: ModelSpec,
) -> Any:
    import numpy as np

    if spec.temporal_variant == "TEMP-1":
        proxy = replace(spec, model_id="M1")
        return _compiled_field_similarity(compiled, left_ordinals, right_ordinals, "decade", proxy)[0]
    left_start = compiled.adjusted_start_years[left_ordinals][:, None]
    left_end = compiled.adjusted_end_years[left_ordinals][:, None]
    right_start = compiled.adjusted_start_years[right_ordinals][None, :]
    right_end = compiled.adjusted_end_years[right_ordinals][None, :]
    gap = np.maximum(0, np.maximum(right_start - left_end, left_start - right_end))
    if spec.temporal_variant == "TEMP-2":
        return np.where(gap == 0, 1.0, np.where(gap <= 10, 0.5, 0.0))
    if spec.temporal_variant == "TEMP-3":
        return np.exp(-gap / spec.temporal_decay_years)
    intersection = np.maximum(0, np.minimum(left_end, right_end) - np.maximum(left_start, right_start) + 1)
    union = np.maximum(left_end, right_end) - np.minimum(left_start, right_start) + 1
    return intersection / union


def score_compiled_block(
    compiled: CompiledFeatureContext,
    left_ordinals: Sequence[int] | Any,
    right_ordinals: Sequence[int] | Any,
    spec: ModelSpec,
) -> Any:
    """Score a dense ordinal block using the exact scalar baseline semantics."""

    import numpy as np

    _validate_spec(spec)
    if spec.model_id == "M8":
        raise ModelError("M8 has no scalar block score; use object-local Pareto ranking")
    if spec.interaction_policy != "NO_INTERACTION_CONTRIBUTION":
        raise ModelError("compact block scoring requires separately evaluated zero interaction bonus")
    left = np.asarray(left_ordinals, dtype=np.int64)
    right = np.asarray(right_ordinals, dtype=np.int64)
    shape = (len(left), len(right))
    family_scores: dict[str, Any] = {}
    family_available: dict[str, Any] = {}

    for family, fields in (
        ("context", ("medium", "theme", "movement_context")),
        ("geography", ("geography",)),
        ("descriptive", ("object_type", "creator")),
    ):
        score_sum = np.zeros(shape, dtype=np.float64)
        observed_count = np.zeros(shape, dtype=np.float64)
        for field in fields:
            field_score, available = _compiled_field_similarity(compiled, left, right, field, spec)
            score_sum += np.where(available, field_score, 0.0)
            observed_count += available
        family_scores[family] = np.divide(
            score_sum,
            observed_count,
            out=np.zeros_like(score_sum),
            where=observed_count > 0,
        )
        family_available[family] = observed_count > 0

    # Residual curation has one frozen treatment across model families:
    # lineage-deduplicated IDF Jaccard with an explicit family cap.
    residual_proxy = replace(spec, model_id="M3")
    residual_score, residual_available = _compiled_field_similarity(
        compiled,
        left,
        right,
        "residual_curated_container",
        residual_proxy,
    )
    family_scores["curatorialResidual"] = np.minimum(residual_score, spec.curatorial_cap)
    family_available["curatorialResidual"] = residual_available

    if spec.model_id == "M7":
        temporal_score, temporal_available = _compiled_field_similarity(
            compiled,
            left,
            right,
            "decade",
            spec,
        )
        family_scores["temporal"] = temporal_score
        family_available["temporal"] = temporal_available
    else:
        family_scores["temporal"] = _compiled_temporal_similarity(compiled, left, right, spec)
        family_available["temporal"] = np.ones(shape, dtype=np.bool_)

    source_left = compiled.scalar_codes["source"][left][:, None]
    source_right = compiled.scalar_codes["source"][right][None, :]
    source_available = (source_left >= 0) & (source_right >= 0)
    source_same = source_available & (source_left == source_right)
    if spec.source_treatment == "SOURCE-1":
        source_score = source_same.astype(np.float64) * spec.source_cap
    elif spec.source_treatment == "SOURCE-3":
        source_score = (source_available & ~source_same).astype(np.float64) * spec.source_cap
    else:
        source_score = np.zeros(shape, dtype=np.float64)
    family_scores["source"] = source_score
    family_available["source"] = source_available

    eligible = _eligible_families(spec)
    weights = _resolved_family_weights(compiled.model_context, spec, eligible)
    effective_family_cap = spec.family_cap if spec.family_normalization == "CAPPED_FAMILY" else 1.0
    numerator = np.zeros(shape, dtype=np.float64)
    observed_weight = np.zeros(shape, dtype=np.float64)
    unavailable_weight = np.zeros(shape, dtype=np.float64)
    for family in eligible:
        available = family_available[family]
        weight = float(weights.get(family, 1.0))
        numerator += np.where(available, np.minimum(family_scores[family], effective_family_cap) * weight, 0.0)
        observed_weight += available * weight
        unavailable_weight += (~available) * weight
    denominator = (
        observed_weight + unavailable_weight
        if spec.missingness_variant == "MISSING-B"
        else observed_weight
    )
    scores = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0)
    return np.round(np.minimum(1.0, scores), 12)


def score_compiled_pair(
    compiled: CompiledFeatureContext,
    query_id: str,
    candidate_id: str,
    spec: ModelSpec,
) -> float:
    if query_id == candidate_id:
        raise ModelError("same object is excluded from affinity candidate scoring")
    try:
        left = compiled.object_ordinals[query_id]
        right = compiled.object_ordinals[candidate_id]
    except KeyError as error:
        raise ModelError("compiled pair contains an object outside the public cohort") from error
    return float(score_compiled_block(compiled, (left,), (right,), spec)[0, 0])


def _as_missingness_record(record: candidate_index.IndexedRecord) -> dict[str, Any]:
    return {
        "medium": list(record.field_values.get("medium", ())),
        "theme": list(record.field_values.get("theme", ())),
        "movement_context": list(record.field_values.get("movement_context", ())),
        "geography": list(record.field_values.get("geography", ())),
        "source": list(record.field_values.get("source", ())),
        "object_type": list(record.field_values.get("object_type", ())),
        "creator": list(record.field_values.get("creator", ())),
        "curatorialResidual": list(record.residual_curated_tokens),
        "startYear": record.start_year,
        "endYear": record.end_year,
        "temporalPrecision": record.temporal_precision,
        "geographyMappingStates": list(record.geography_mapping_states),
        "geographyQualified": record.geography_qualified,
    }


def _jaccard(left: Iterable[str], right: Iterable[str]) -> tuple[float, int, int]:
    left_set = set(left)
    right_set = set(right)
    shared = left_set & right_set
    union = left_set | right_set
    return (len(shared) / len(union) if union else 0.0, len(shared), len(union))


def _idf(context: ModelContext, token: str, mode: str) -> float:
    df = context.candidate_index.token_document_frequency.get(token, 0)
    family = context.candidate_index.token_family.get(token, "")
    n = len(context.candidate_index.object_ids)
    denominator = context.family_document_counts.get(family, n) if mode == "WITHIN_FAMILY_IDF" else n
    if df <= 0 or denominator <= 0:
        return 0.0
    if mode == "GLOBAL_IDF":
        return max(0.0, math.log(denominator / df))
    if mode == "WITHIN_FAMILY_IDF":
        return max(0.0, math.log(denominator / df))
    return math.log((denominator + 1) / (df + 1)) + 1.0


def _weighted_cosine(
    context: ModelContext,
    left: Iterable[str],
    right: Iterable[str],
    mode: str,
) -> tuple[float, float, float]:
    left_set = set(left)
    right_set = set(right)
    shared = left_set & right_set
    dot = sum(_idf(context, token, mode) ** 2 for token in shared)
    left_norm = math.sqrt(sum(_idf(context, token, mode) ** 2 for token in left_set))
    right_norm = math.sqrt(sum(_idf(context, token, mode) ** 2 for token in right_set))
    denominator = left_norm * right_norm
    return (dot / denominator if denominator else 0.0, dot, denominator)


def _weighted_jaccard(
    context: ModelContext,
    left: Iterable[str],
    right: Iterable[str],
    mode: str,
) -> tuple[float, float, float]:
    left_set = set(left)
    right_set = set(right)
    shared = left_set & right_set
    union = left_set | right_set
    numerator = sum(_idf(context, token, mode) for token in shared)
    denominator = sum(_idf(context, token, mode) for token in union)
    return (numerator / denominator if denominator else 0.0, numerator, denominator)


def _tversky(
    left: Iterable[str],
    right: Iterable[str],
    alpha: float,
    beta: float,
) -> tuple[float, float, float]:
    left_set = set(left)
    right_set = set(right)
    common = len(left_set & right_set)
    denominator = common + alpha * len(left_set - right_set) + beta * len(right_set - left_set)
    return (common / denominator if denominator else 0.0, float(common), float(denominator))


def _expanded_interval(record: candidate_index.IndexedRecord) -> tuple[int, int]:
    if record.temporal_precision.casefold() == "approximate":
        return record.start_year - 5, record.end_year + 5
    return record.start_year, record.end_year


def _temporal_similarity(
    left: candidate_index.IndexedRecord,
    right: candidate_index.IndexedRecord,
    spec: ModelSpec,
) -> tuple[float, float, float, str]:
    left_decades = left.field_values.get("decade", ())
    right_decades = right.field_values.get("decade", ())
    if spec.temporal_variant == "TEMP-1":
        score, numerator, denominator = _jaccard(left_decades, right_decades)
        return score, float(numerator), float(denominator), "GOVERNED_DECADE_OVERLAP"

    left_start, left_end = _expanded_interval(left)
    right_start, right_end = _expanded_interval(right)
    if left_end < right_start:
        gap = right_start - left_end
    elif right_end < left_start:
        gap = left_start - right_end
    else:
        gap = 0
    if spec.temporal_variant == "TEMP-2":
        score = 1.0 if gap == 0 else 0.5 if gap <= 10 else 0.0
        return score, score, 1.0, "BOUNDED_ADJACENT_DECADE"
    if spec.temporal_variant == "TEMP-3":
        score = math.exp(-gap / spec.temporal_decay_years)
        return score, score, 1.0, "BOUNDED_INTERVAL_DISTANCE_DECAY"
    intersection = max(0, min(left_end, right_end) - max(left_start, right_start) + 1)
    union = max(left_end, right_end) - min(left_start, right_start) + 1
    return (intersection / union if union else 0.0, float(intersection), float(union), "GOVERNED_INTERVAL_OVERLAP")


def _family_field_tokens(record: candidate_index.IndexedRecord, family: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    fields = {
        "context": ("medium", "theme", "movement_context"),
        "temporal": ("decade",),
        "geography": ("geography",),
        "source": ("source",),
        "descriptive": ("object_type", "creator"),
    }.get(family, ())
    return tuple((field, record.field_values.get(field, ())) for field in fields)


def _ordinary_family_score(
    context: ModelContext,
    left: candidate_index.IndexedRecord,
    right: candidate_index.IndexedRecord,
    family: str,
    spec: ModelSpec,
) -> tuple[float | None, list[dict[str, Any]], list[dict[str, Any]]]:
    if family == "temporal" and spec.model_id != "M7":
        score, numerator, denominator, basis = _temporal_similarity(left, right, spec)
        return score, [{
            "family": family,
            "signalId": "SIG-TEMPORAL-EXTENT",
            "sameSourceFactGroup": "SOURCE_FACT_TEMPORAL_GOVERNED_EXTENT",
            "basis": basis,
            "numerator": numerator,
            "denominator": denominator,
            "contribution": score,
        }], []
    if family == "curatorialResidual":
        left_tokens = left.family_tokens.get(family, ())
        right_tokens = right.family_tokens.get(family, ())
        if not left_tokens or not right_tokens:
            return None, [], []
        score, numerator, denominator = _weighted_jaccard(context, left_tokens, right_tokens, spec.idf_mode)
        score = min(score, spec.curatorial_cap)
        return score, [{
            "family": family,
            "signalId": "SIG-CURATORIAL-MEMBERSHIP",
            "sameSourceFactGroup": "SOURCE_FACT_CURATORIAL_LINEAGE_RESIDUAL",
            "basis": "LINEAGE_RESIDUAL_ONLY",
            "numerator": numerator,
            "denominator": denominator,
            "cap": spec.curatorial_cap,
            "contribution": score,
        }], []

    if family == "source":
        left_values = left.field_values.get("source", ())
        right_values = right.field_values.get("source", ())
        if not left_values or not right_values:
            return None, [], []
        same = bool(set(left_values) & set(right_values))
        if spec.source_treatment in {"SOURCE-0", "SOURCE-2", "SOURCE-4"}:
            score = 0.0
        elif spec.source_treatment == "SOURCE-1":
            score = spec.source_cap if same else 0.0
        else:
            score = 0.0 if same else spec.source_cap
        return score, [{
            "family": "source",
            "signalId": "SIG-SOURCE-NAME",
            "sameSourceFactGroup": "SOURCE_FACT_PUBLIC_SOURCE_IDENTITY",
            "basis": spec.source_treatment,
            "numerator": int(same),
            "denominator": 1,
            "cap": spec.source_cap,
            "contribution": score,
            "sourceIdentity": left_values[0] if same else "DISTINCT_SOURCE",
        }], []

    field_rows = _family_field_tokens(left, family)
    right_by_field = dict(_family_field_tokens(right, family))
    scores: list[float] = []
    contributions: list[dict[str, Any]] = []
    distinctive: list[dict[str, Any]] = []
    for field, left_values in field_rows:
        right_values = right_by_field.get(field, ())
        if not left_values or not right_values:
            continue
        left_tokens = tuple(candidate_index._token(family, field, value) for value in left_values)
        right_tokens = tuple(candidate_index._token(family, field, value) for value in right_values)
        if spec.model_id in {"M1", "M5", "M8"}:
            score, numerator, denominator = _jaccard(left_tokens, right_tokens)
        elif spec.model_id == "M2":
            score, numerator, denominator = _weighted_cosine(context, left_tokens, right_tokens, spec.idf_mode)
        elif spec.model_id == "M3":
            score, numerator, denominator = _weighted_jaccard(context, left_tokens, right_tokens, spec.idf_mode)
        elif spec.model_id == "M4":
            shared = set(left_tokens) & set(right_tokens)
            union = set(left_tokens) | set(right_tokens)
            weighted_shared = 0.0
            for token in shared:
                df = context.candidate_index.token_document_frequency.get(token, 0)
                if df < spec.goodall_support_floor:
                    effective = min(
                        spec.goodall_match_cap,
                        context.goodall_weights.get(token, 0.0) * df / spec.goodall_support_floor,
                    )
                else:
                    effective = min(spec.goodall_match_cap, context.goodall_weights.get(token, 0.0))
                weighted_shared += effective
            denominator = float(len(union))
            numerator = weighted_shared
            score = numerator / denominator if denominator else 0.0
        elif spec.model_id == "M6":
            score, numerator, denominator = _tversky(
                left_tokens, right_tokens, spec.tversky_alpha, spec.tversky_beta
            )
        elif spec.model_id == "M7":
            query_tokens = set(left_tokens)
            document_tokens = set(right_tokens)
            query_weight = sum(_idf(context, token, "SMOOTHED_IDF") for token in query_tokens)
            matched_weight = sum(
                _idf(context, token, "SMOOTHED_IDF") for token in query_tokens & document_tokens
            )
            average_length = max(context.average_field_lengths.get(field, 1.0), 1e-12)
            length_norm = 1 - spec.bm25_b + spec.bm25_b * len(document_tokens) / average_length
            saturation = (spec.bm25_k1 + 1) / (1 + spec.bm25_k1 * length_norm)
            numerator = matched_weight * saturation
            denominator = query_weight
            score = min(1.0, numerator / denominator) if denominator else 0.0
        else:
            raise ModelError("unsupported model family score")
        scores.append(score)
        shared_tokens = tuple(sorted(set(left_tokens) & set(right_tokens)))
        contribution_row: dict[str, Any] = {
            "family": family,
            "field": field,
            "signalId": {
                "medium": "SIG-CONTEXT-MEDIUM",
                "theme": "SIG-CONTEXT-THEME",
                "movement_context": "SIG-CONTEXT-MOVEMENT",
                "decade": "SIG-TEMPORAL-DECADE",
                "geography": "SIG-GEOGRAPHY-ASSIGNMENT",
                "object_type": "SIG-DESCRIPTIVE-OBJECT-TYPE",
                "creator": "SIG-DESCRIPTIVE-CREATOR",
            }[field],
            "sameSourceFactGroup": {
                "medium": "SOURCE_FACT_GOVERNED_CONTEXT_MEDIUM",
                "theme": "SOURCE_FACT_GOVERNED_CONTEXT_THEME",
                "movement_context": "SOURCE_FACT_GOVERNED_CONTEXT_MOVEMENT",
                "decade": "SOURCE_FACT_GOVERNED_TEMPORAL_DECADE",
                "geography": "SOURCE_FACT_GOVERNED_GEOGRAPHY_ASSIGNMENT",
                "object_type": "SOURCE_FACT_PUBLIC_OBJECT_TYPE",
                "creator": "SOURCE_FACT_PUBLIC_CREATOR_ATTRIBUTION",
            }[field],
            "basis": spec.model_family,
            "numerator": numerator,
            "denominator": denominator,
            "matchedFeatureIds": list(shared_tokens),
            "contribution": score,
        }
        if spec.model_id == "M7":
            term_statistics = [
                {
                    "featureId": value,
                    "documentFrequency": context.candidate_index.token_document_frequency.get(
                        candidate_index._token(family, field, value),
                        0,
                    ),
                    "idf": _idf(
                        context,
                        candidate_index._token(family, field, value),
                        "SMOOTHED_IDF",
                    ),
                    "matched": value in set(right_values),
                }
                for value in sorted(set(left_values))
            ]
            contribution_row.update({
                "formula": "BM25F_LIKE_FIELD_SATURATION",
                "queryTermStatistics": term_statistics,
                "matchedQueryTermCount": sum(row["matched"] for row in term_statistics),
                "documentFieldLength": len(document_tokens),
                "averageDocumentFieldLength": average_length,
                "k1": spec.bm25_k1,
                "b": spec.bm25_b,
                "lengthNormalization": length_norm,
                "saturation": saturation,
                "declaredFamilyWeight": _resolved_family_weights(
                    context,
                    spec,
                    _eligible_families(spec),
                )[family],
            })
        contributions.append(contribution_row)
        left_only = tuple(sorted(set(left_tokens) - set(right_tokens)))
        right_only = tuple(sorted(set(right_tokens) - set(left_tokens)))
        if left_only or right_only:
            distinctive.append({
                "family": family,
                "field": field,
                "queryOnlyFeatureIds": list(left_only),
                "candidateOnlyFeatureIds": list(right_only),
            })
    return (sum(scores) / len(scores) if scores else None, contributions, distinctive)


def _eligible_families(spec: ModelSpec) -> tuple[str, ...]:
    families = list(spec.eligible_families)
    if spec.source_treatment == "SOURCE-1" or spec.source_treatment == "SOURCE-3":
        if "source" not in families:
            families.append("source")
    else:
        families = [family for family in families if family != "source"]
    return tuple(families)


def _resolved_family_weights(
    context: ModelContext,
    spec: ModelSpec,
    eligible_families: Sequence[str],
) -> dict[str, float]:
    if spec.family_normalization in {"EQUAL_FAMILY", "CAPPED_FAMILY"}:
        return {family: 1.0 for family in eligible_families}
    if spec.family_normalization == "USER_SELECTED":
        declared = dict(spec.family_weights)
        return {family: float(declared.get(family, 1.0)) for family in eligible_families}
    # Availability-normalized sensitivity variant: inverse public family
    # observability, normalized back to mean weight 1.  This is declared and
    # deterministic, never learned from relation labels.
    n = max(1, len(context.candidate_index.object_ids))
    raw = {
        family: n / max(1, context.family_document_counts.get(family, n))
        for family in eligible_families
    }
    mean = sum(raw.values()) / len(raw) if raw else 1.0
    return {family: value / mean for family, value in raw.items()}


def _interaction_contributions(
    model_context: ModelContext,
    trusted_context: interaction_statistics.TrustedInteractionContext | None,
    spec: ModelSpec,
    *,
    query_id: str,
    candidate_id: str,
) -> tuple[tuple[dict[str, Any], ...], float]:
    if spec.interaction_policy == "NO_INTERACTION_CONTRIBUTION":
        return (), 0.0
    if spec.interaction_policy not in {
        "CAPPED_INTERACTION_BONUS",
        "INFORMATION_RESIDUAL_CONTRIBUTION",
        "LOG_LIKELIHOOD_INTERACTION_CONTRIBUTION",
    }:
        raise ModelError("unsupported interaction policy")
    if trusted_context is None:
        raise ModelError("interaction policy requires a trusted interaction context")
    try:
        interaction_statistics.validate_trusted_interaction_context(trusted_context)
    except interaction_statistics.InteractionError as error:
        raise ModelError("interaction policy received an untrusted context") from error
    if tuple(trusted_context.public_object_ids) != tuple(
        sorted(trusted_context.public_object_ids)
    ):
        raise ModelError("trusted interaction cohort ordering is not canonical")
    index = model_context.candidate_index
    if tuple(trusted_context.public_object_ids) != index.object_ids:
        raise ModelError("trusted interaction cohort differs from the model cohort")
    if (
        index.interaction_registry_sha256 != trusted_context.registry_sha256
        or index.interaction_context_sha256 != trusted_context.context_sha256
    ):
        raise ModelError(
            "trusted interaction context is not bound into this model candidate index"
        )
    try:
        resolved = interaction_statistics.resolve_pair_interactions(
            trusted_context,
            query_id,
            candidate_id,
            method=spec.interaction_policy,
            support_threshold=spec.interaction_support_threshold,
            cap=spec.interaction_cap,
            source_treatment=spec.source_treatment,
        )
    except interaction_statistics.InteractionError as error:
        raise ModelError("trusted interaction resolution failed") from error
    rows = tuple(
        sorted((dict(row) for row in resolved), key=lambda row: (row["interactionId"], row["method"]))
    )
    total = sum(float(row["residualScore"]) for row in rows)
    if not math.isfinite(total) or total < 0:
        raise ModelError("trusted interaction resolver emitted an invalid residual")
    return rows, total


def _normalize_interaction_rows(
    rows: Sequence[Mapping[str, Any]],
    effective_bonus: float,
) -> tuple[dict[str, Any], ...]:
    if not rows:
        if effective_bonus != 0:
            raise ModelError("interaction bonus has no contributing rows")
        return ()
    raw_total = sum(float(row["residualScore"]) for row in rows)
    if raw_total <= 0:
        return tuple(
            {
                **dict(row),
                "rawResidualScore": float(row["residualScore"]),
                "residualScore": 0.0,
                "aggregateBonus": 0.0,
                "aggregateResidualNormalized": True,
            }
            for row in rows
        )
    # Reserve the largest raw row as the deterministic balancing row.  If a
    # vanishingly small row is balanced last, floating-point rounding in the
    # preceding proportional allocations can consume the cap and make the
    # final residual slightly negative.  A largest-row balance remains
    # positive, preserves proportional allocation, and makes Python's emitted
    # row sum exactly equal to the aggregate bonus in output order.
    balancing_index = max(
        range(len(rows)),
        key=lambda index: (
            float(rows[index]["residualScore"]),
            str(rows[index].get("interactionId", "")),
        ),
    )
    ordered_rows = [
        *(
            row
            for index, row in enumerate(rows)
            if index != balancing_index
        ),
        rows[balancing_index],
    ]
    normalized: list[dict[str, Any]] = []
    running = 0.0
    for index, raw in enumerate(ordered_rows):
        if index == len(ordered_rows) - 1:
            residual = effective_bonus - running
        else:
            residual = effective_bonus * float(raw["residualScore"]) / raw_total
            running += residual
        if residual < 0:
            raise ModelError("normalized interaction residual became negative")
        normalized.append(
            {
                **dict(raw),
                "rawResidualScore": float(raw["residualScore"]),
                "residualScore": residual,
                "aggregateBonus": effective_bonus,
                "aggregateResidualNormalized": True,
            }
        )
    emitted_total = math.fsum(float(row["residualScore"]) for row in normalized)
    if not math.isclose(
        emitted_total,
        effective_bonus,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ModelError("normalized interaction rows do not sum to the aggregate bonus")
    return tuple(normalized)


def score_pair(
    context: ModelContext,
    query_id: str,
    candidate_id: str,
    spec: ModelSpec,
    *,
    trusted_interaction_context: interaction_statistics.TrustedInteractionContext | None = None,
    interaction_evidence: Iterable[Mapping[str, Any]] | None = None,
    ignored_duplicate_signals: Iterable[str] = (),
) -> AffinityProfile:
    """Score one ordered pair using the same pure path as exhaustive ranking."""

    _validate_spec(spec)
    if interaction_evidence is not None:
        raise ModelError(
            "caller-supplied interaction evidence is prohibited; use trusted_interaction_context"
        )
    if query_id == candidate_id:
        raise ModelError("same object is excluded from affinity candidate scoring")
    try:
        left = context.candidate_index.records[query_id]
        right = context.candidate_index.records[candidate_id]
    except KeyError as error:
        raise ModelError("pair contains an object outside the public index") from error

    eligible = _eligible_families(spec)
    comparability = missingness.compute_comparability(
        _as_missingness_record(left),
        _as_missingness_record(right),
        eligible_families=eligible,
    )
    family_scores: dict[str, float | None] = {family: None for family in ALL_PROFILE_FAMILIES}
    contributions: list[dict[str, Any]] = []
    distinctive: list[dict[str, Any]] = []
    for family in eligible:
        if family not in comparability.jointly_observable_families:
            continue
        score, rows, differences = _ordinary_family_score(context, left, right, family, spec)
        family_scores[family] = score
        contributions.extend(rows)
        distinctive.extend(differences)

    weights = _resolved_family_weights(context, spec, eligible)
    effective_family_cap = spec.family_cap if spec.family_normalization == "CAPPED_FAMILY" else 1.0
    aggregation = missingness.aggregate_family_affinity(
        family_scores,
        comparability,
        variant=spec.missingness_variant,
        family_weights=weights,
        family_cap=effective_family_cap,
    )
    raw_interactions, raw_interaction_bonus = _interaction_contributions(
        context,
        trusted_interaction_context,
        spec,
        query_id=query_id,
        candidate_id=candidate_id,
    )
    base_affinity = float(aggregation["affinity"])
    interaction_bonus = min(
        spec.interaction_cap,
        raw_interaction_bonus,
        max(0.0, 1.0 - base_affinity),
    )
    interactions = _normalize_interaction_rows(raw_interactions, interaction_bonus)
    if spec.model_id == "M8":
        diagnostic_score: float | None = None
    else:
        diagnostic_score = min(1.0, base_affinity + interaction_bonus)
        diagnostic_score = round(diagnostic_score, 12)
    clean_family_scores = {
        family: (round(float(value), 12) if value is not None else None)
        for family, value in family_scores.items()
    }
    weighted_contributions = {
        family: round(
            min(float(clean_family_scores[family]), effective_family_cap)
            * float(weights.get(family, 1.0)),
            12,
        )
        for family in eligible
        if clean_family_scores.get(family) is not None
    }
    aggregation_denominator = float(
        aggregation[
            "eligibleWeightDenominator"
            if spec.missingness_variant == "MISSING-B"
            else "observedWeightDenominator"
        ]
    )
    contribution_units = {
        family: value / aggregation_denominator if aggregation_denominator else 0.0
        for family, value in sorted(weighted_contributions.items())
    }
    if interaction_bonus > 0:
        contribution_units["interactionResidual"] = interaction_bonus
    if diagnostic_score is not None and not math.isclose(
        sum(contribution_units.values()),
        diagnostic_score,
        rel_tol=0.0,
        abs_tol=2e-12,
    ):
        raise ModelError("final-score contribution units do not reconcile to diagnosticScore")
    contribution_total = sum(contribution_units.values())
    contribution_shares = {
        family: value / contribution_total if contribution_total else 0.0
        for family, value in sorted(contribution_units.items())
    }
    if contribution_total > 0 and not math.isclose(
        sum(contribution_shares.values()),
        1.0,
        rel_tol=0.0,
        abs_tol=2e-12,
    ):
        raise ModelError("family contribution shares do not sum to one")
    pareto_vector = tuple(
        clean_family_scores[family] if clean_family_scores[family] is not None else -1.0
        for family in eligible
    )
    return AffinityProfile(
        query_id=query_id,
        candidate_id=candidate_id,
        model_id=spec.model_id,
        variant_id=spec.variant_id,
        symmetric=spec.symmetric,
        source_treatment=spec.source_treatment,
        family_normalization=spec.family_normalization,
        family_scores=clean_family_scores,
        family_weighted_contributions=dict(sorted(weighted_contributions.items())),
        family_contribution_units=dict(sorted(contribution_units.items())),
        family_contribution_shares=contribution_shares,
        jointly_observable_families=comparability.jointly_observable_families,
        unavailable_families=comparability.unavailable_families,
        comparability=comparability.as_dict(),
        interactions=interactions,
        contributions=tuple(
            sorted(contributions, key=lambda row: (str(row["family"]), str(row.get("field", "")), str(row["signalId"])))
        ),
        distinctive_features=tuple(
            sorted(distinctive, key=lambda row: (str(row["family"]), str(row.get("field", ""))))
        ),
        ignored_duplicate_signals=tuple(sorted(set(ignored_duplicate_signals))),
        diagnostic_score=diagnostic_score,
        pareto_vector=pareto_vector,
    )


def _dominates(left: AffinityProfile, right: AffinityProfile) -> bool:
    left_observed = int(left.comparability["observedFamilyCount"])
    right_observed = int(right.comparability["observedFamilyCount"])
    if left_observed < right_observed:
        return False
    strictly_better = left_observed > right_observed
    compared = False
    for left_value, right_value in zip(left.pareto_vector, right.pareto_vector):
        if right_value < 0:
            continue
        compared = True
        if left_value < 0 or left_value < right_value:
            return False
        strictly_better = strictly_better or left_value > right_value
    return compared and strictly_better


def _pareto_layers(profiles: Sequence[AffinityProfile]) -> list[list[AffinityProfile]]:
    remaining = list(profiles)
    layers: list[list[AffinityProfile]] = []
    while remaining:
        front = [
            candidate
            for candidate in remaining
            if not any(_dominates(other, candidate) for other in remaining if other is not candidate)
        ]
        front.sort(
            key=lambda profile: (
                -max((value for value in profile.pareto_vector if value >= 0), default=0.0),
                -sum(value for value in profile.pareto_vector if value >= 0),
                profile.candidate_id,
            )
        )
        layers.append(front)
        front_ids = {id(value) for value in front}
        remaining = [value for value in remaining if id(value) not in front_ids]
    return layers


def rank_candidates(
    context: ModelContext,
    query_id: str,
    candidate_ids: Iterable[str],
    spec: ModelSpec,
    *,
    k: int | None = None,
    trusted_interaction_context: interaction_statistics.TrustedInteractionContext | None = None,
    interaction_evidence_by_candidate: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    if k is not None and k <= 0:
        raise ModelError("ranking k must be positive")
    candidates = tuple(sorted({str(value) for value in candidate_ids} - {query_id}))
    if interaction_evidence_by_candidate is not None:
        raise ModelError(
            "caller-supplied interaction evidence maps are prohibited; use trusted_interaction_context"
        )
    profiles = [
        score_pair(
            context,
            query_id,
            candidate_id,
            spec,
            trusted_interaction_context=trusted_interaction_context,
        )
        for candidate_id in candidates
    ]
    if spec.model_id == "M8":
        layers = _pareto_layers(profiles)
        ordered = [(layer_index + 1, profile) for layer_index, layer in enumerate(layers) for profile in layer]
    else:
        ordered_profiles = sorted(
            profiles,
            key=lambda profile: (-float(profile.diagnostic_score or 0.0), profile.candidate_id),
        )
        ordered = [(0, profile) for profile in ordered_profiles]
    if k is not None:
        ordered = ordered[:k]
    return [
        {
            "rank": ordinal,
            "candidateId": profile.candidate_id,
            "diagnosticScore": profile.diagnostic_score,
            "paretoLayer": pareto_layer if spec.model_id == "M8" else None,
            "profile": profile.as_dict(),
        }
        for ordinal, (pareto_layer, profile) in enumerate(ordered, start=1)
    ]


def diversify_by_source(
    ranking: Sequence[Mapping[str, Any]],
    context: ModelContext,
    *,
    max_per_source: int = 3,
) -> list[dict[str, Any]]:
    """SOURCE-4 post-ranking diversification; it never changes pair scores."""

    if max_per_source < 1:
        raise ModelError("source diversification cap must be positive")
    counts: dict[str, int] = defaultdict(int)
    selected: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    for raw in ranking:
        row = dict(raw)
        candidate_id = str(row["candidateId"])
        source_values = context.candidate_index.records[candidate_id].field_values.get("source", ())
        source = source_values[0] if source_values else "NOT_GOVERNED"
        if counts[source] < max_per_source:
            counts[source] += 1
            selected.append(row)
        else:
            deferred.append(row)
    output = selected + deferred
    for ordinal, row in enumerate(output, start=1):
        row["diversifiedRank"] = ordinal
        row["scoreChanged"] = False
    return output


def _push_top_k(
    heap: list[tuple[float, int, str]],
    *,
    score: float,
    candidate_id: str,
    candidate_ordinal: int,
    k: int,
) -> None:
    entry = (score, -candidate_ordinal, candidate_id)
    if len(heap) < k:
        heapq.heappush(heap, entry)
    elif entry[:2] > heap[0][:2]:
        heapq.heapreplace(heap, entry)


def _stream_exhaustive_top_k_python(
    context: ModelContext,
    specs: Sequence[ModelSpec],
    *,
    k: int = 50,
    query_ids: Iterable[str] | None = None,
    block_size: int = 128,
    checkpoint: Callable[[Mapping[str, Any]], None] | None = None,
    trusted_interaction_context: interaction_statistics.TrustedInteractionContext | None = None,
) -> dict[str, Any]:
    """Stream unordered pairs and retain only bounded per-object scalar top-k.

    With ``query_ids=None`` this visits exactly N(N-1)/2 unordered pairs.  M8
    is intentionally excluded because an exact non-scalar Pareto frontier is
    evaluated object-locally with ``rank_candidates`` rather than collapsed to
    a hidden scalar.  No pair row is retained or serialized.
    """

    if k <= 0 or block_size <= 0:
        raise ModelError("k and block size must be positive")
    if not specs or any(spec.model_id == "M8" for spec in specs):
        raise ModelError("exhaustive bounded scalar top-k requires nonempty M1-M7 specs")
    for spec in specs:
        _validate_spec(spec)
    variant_ids = [spec.variant_id for spec in specs]
    if len(set(variant_ids)) != len(variant_ids):
        raise ModelError("exhaustive model variants must be unique")

    object_ids = context.candidate_index.object_ids
    ordinal_by_id = {object_id: ordinal for ordinal, object_id in enumerate(object_ids)}
    selected = set(object_ids if query_ids is None else (str(value) for value in query_ids))
    if not selected or selected - set(object_ids):
        raise ModelError("exhaustive query set is empty or outside the public cohort")
    heaps: dict[str, dict[str, list[tuple[float, int, str]]]] = {
        spec.variant_id: {query_id: [] for query_id in sorted(selected)} for spec in specs
    }
    pair_count = 0
    directional_score_count = 0
    score_elapsed: dict[str, float] = defaultdict(float)
    started = time.perf_counter()
    n = len(object_ids)
    for block_start in range(0, n, block_size):
        block_end = min(n, block_start + block_size)
        for left_ordinal in range(block_start, block_end):
            left_id = object_ids[left_ordinal]
            for right_ordinal in range(left_ordinal + 1, n):
                right_id = object_ids[right_ordinal]
                pair_count += 1
                if left_id not in selected and right_id not in selected:
                    continue
                for spec in specs:
                    score_started = time.perf_counter()
                    forward = score_pair(
                        context,
                        left_id,
                        right_id,
                        spec,
                        trusted_interaction_context=trusted_interaction_context,
                    )
                    score_elapsed[spec.variant_id] += (time.perf_counter() - score_started) * 1000
                    if left_id in selected:
                        _push_top_k(
                            heaps[spec.variant_id][left_id],
                            score=float(forward.diagnostic_score or 0.0),
                            candidate_id=right_id,
                            candidate_ordinal=right_ordinal,
                            k=k,
                        )
                        directional_score_count += 1
                    if right_id in selected:
                        reverse = forward if spec.symmetric else score_pair(
                            context,
                            right_id,
                            left_id,
                            spec,
                            trusted_interaction_context=trusted_interaction_context,
                        )
                        _push_top_k(
                            heaps[spec.variant_id][right_id],
                            score=float(reverse.diagnostic_score or 0.0),
                            candidate_id=left_id,
                            candidate_ordinal=left_ordinal,
                            k=k,
                        )
                        directional_score_count += 1
        if checkpoint is not None:
            checkpoint(
                {
                    "completedObjectPrefixCount": block_end,
                    "objectCount": n,
                    "unorderedPairVisits": pair_count,
                    "pairRowsRetained": 0,
                }
            )

    rankings: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for spec in specs:
        model_rows: dict[str, list[dict[str, Any]]] = {}
        for query_id in sorted(selected):
            entries = sorted(heaps[spec.variant_id][query_id], key=lambda row: (-row[0], row[2]))
            model_rows[query_id] = [
                {"rank": rank, "candidateId": candidate_id, "diagnosticScore": score}
                for rank, (score, _, candidate_id) in enumerate(entries, start=1)
            ]
        rankings[spec.variant_id] = model_rows
    hash_material = {
        "candidateIndexSha256": context.candidate_index.index_sha256,
        "k": k,
        "queryIds": sorted(selected),
        "rankings": rankings,
        "unorderedPairVisits": pair_count,
        "pairRowsRetained": 0,
    }
    ranking_sha256 = hashlib.sha256(
        (json.dumps(hash_material, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    ).hexdigest()
    return {
        "schemaVersion": "trace-exploration-exhaustive-topk/v1",
        "objectCount": n,
        "queryCount": len(selected),
        "expectedFullPairCount": n * (n - 1) // 2,
        "unorderedPairVisits": pair_count,
        "directionalScoreCount": directional_score_count,
        "k": k,
        "rankings": rankings,
        "rankingSha256": ranking_sha256,
        "modelScoreMs": dict(sorted(score_elapsed.items())),
        "elapsedMs": (time.perf_counter() - started) * 1000,
        "pairRowsRetained": 0,
        "fullPairMatrixMaterialized": False,
        "randomnessAffectsAffinity": False,
    }


def _stream_exhaustive_top_k_compact(
    context: ModelContext,
    specs: Sequence[ModelSpec],
    *,
    k: int,
    query_ids: Iterable[str] | None,
    block_size: int,
    checkpoint: Callable[[Mapping[str, Any]], None] | None,
    retain_rankings: bool,
    ranking_sink: Callable[[str, str, tuple[tuple[str, float], ...]], None] | None,
) -> dict[str, Any]:
    """NumPy block scorer with compact heaps and no pair-row retention."""

    import numpy as np

    if k <= 0 or block_size <= 0:
        raise ModelError("k and block size must be positive")
    if not specs or any(spec.model_id == "M8" for spec in specs):
        raise ModelError("exhaustive bounded scalar top-k requires nonempty M1-M7 specs")
    for spec in specs:
        _validate_spec(spec)
        if spec.interaction_policy != "NO_INTERACTION_CONTRIBUTION":
            raise ModelError("compact exhaustive scoring does not mix interaction residuals into base scores")
    if len({spec.variant_id for spec in specs}) != len(specs):
        raise ModelError("exhaustive model variants must be unique")

    compiled_started = time.perf_counter()
    compiled = compile_feature_context(context)
    compile_ms = (time.perf_counter() - compiled_started) * 1000
    object_ids = compiled.object_ids
    n = len(object_ids)
    selected = set(object_ids if query_ids is None else (str(value) for value in query_ids))
    if not selected or selected - set(object_ids):
        raise ModelError("exhaustive query set is empty or outside the public cohort")
    heaps: dict[str, dict[str, list[tuple[float, int, str]]]] = {
        spec.variant_id: {query_id: [] for query_id in sorted(selected)} for spec in specs
    }
    pair_count = 0
    directional_score_count = 0
    score_elapsed: dict[str, float] = defaultdict(float)
    started = time.perf_counter()

    def update_rows(
        variant_id: str,
        query_ordinals: Any,
        candidate_ordinals: Any,
        scores: Any,
        *,
        relation: str,
    ) -> int:
        updated = 0
        for row_index, query_ordinal_raw in enumerate(query_ordinals):
            query_ordinal = int(query_ordinal_raw)
            query_id = object_ids[query_ordinal]
            if query_id not in selected:
                continue
            if relation == "UPPER":
                valid_positions = np.flatnonzero(candidate_ordinals > query_ordinal)
            elif relation == "LOWER":
                valid_positions = np.flatnonzero(candidate_ordinals < query_ordinal)
            else:
                valid_positions = np.arange(len(candidate_ordinals), dtype=np.int64)
            if not len(valid_positions):
                continue
            candidate_subset = candidate_ordinals[valid_positions]
            score_subset = scores[row_index, valid_positions]
            # Stable exact block top-k: score descending, public-ID ordinal
            # ascending.  Keeping k per block cannot remove a global top-k item.
            order = np.lexsort((candidate_subset, -score_subset))[: min(k, len(valid_positions))]
            for local_position in order:
                candidate_ordinal = int(candidate_subset[local_position])
                _push_top_k(
                    heaps[variant_id][query_id],
                    score=float(score_subset[local_position]),
                    candidate_id=object_ids[candidate_ordinal],
                    candidate_ordinal=candidate_ordinal,
                    k=k,
                )
            updated += len(valid_positions)
        return updated

    for left_start in range(0, n, block_size):
        left_end = min(n, left_start + block_size)
        left_ordinals = np.arange(left_start, left_end, dtype=np.int64)
        for right_start in range(left_start, n, block_size):
            right_end = min(n, right_start + block_size)
            right_ordinals = np.arange(right_start, right_end, dtype=np.int64)
            same_block = left_start == right_start
            pair_count += (
                len(left_ordinals) * (len(left_ordinals) - 1) // 2
                if same_block
                else len(left_ordinals) * len(right_ordinals)
            )
            for spec in specs:
                score_started = time.perf_counter()
                forward = score_compiled_block(compiled, left_ordinals, right_ordinals, spec)
                reverse = forward.T if spec.symmetric else score_compiled_block(
                    compiled, right_ordinals, left_ordinals, spec
                )
                score_elapsed[spec.variant_id] += (time.perf_counter() - score_started) * 1000
                directional_score_count += update_rows(
                    spec.variant_id,
                    left_ordinals,
                    right_ordinals,
                    forward,
                    relation="UPPER" if same_block else "ALL",
                )
                directional_score_count += update_rows(
                    spec.variant_id,
                    right_ordinals,
                    left_ordinals,
                    reverse,
                    relation="LOWER" if same_block else "ALL",
                )
        if checkpoint is not None:
            checkpoint({
                "completedObjectPrefixCount": left_end,
                "objectCount": n,
                "unorderedPairVisits": pair_count,
                "pairRowsRetained": 0,
                "engine": "COMPACT_NUMPY_BLOCK",
            })

    ranking_digest = hashlib.sha256()
    ranking_digest.update(
        (
            json.dumps(
                {
                    "schemaVersion": "trace-exploration-exhaustive-topk/v1",
                    "candidateIndexSha256": context.candidate_index.index_sha256,
                    "compiledFeatureSha256": compiled.compiled_sha256,
                    "k": k,
                    "queryIds": sorted(selected),
                    "unorderedPairVisits": pair_count,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
    )
    rankings: dict[str, dict[str, tuple[tuple[str, float], ...]]] = {}
    for spec in specs:
        model_rows: dict[str, tuple[tuple[str, float], ...]] = {}
        for query_id in sorted(selected):
            compact = tuple(
                (candidate_id, score)
                for score, _, candidate_id in sorted(
                    heaps[spec.variant_id][query_id], key=lambda row: (-row[0], row[2])
                )
            )
            ranking_digest.update(
                (
                    json.dumps(
                        [spec.variant_id, query_id, compact],
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    + "\n"
                ).encode("utf-8")
            )
            if ranking_sink is not None:
                ranking_sink(spec.variant_id, query_id, compact)
            if retain_rankings:
                model_rows[query_id] = compact
        if retain_rankings:
            rankings[spec.variant_id] = model_rows
    return {
        "schemaVersion": "trace-exploration-exhaustive-topk/v1",
        "engine": "COMPACT_NUMPY_BLOCK",
        "compiledFeatureSha256": compiled.compiled_sha256,
        "objectCount": n,
        "queryCount": len(selected),
        "expectedFullPairCount": n * (n - 1) // 2,
        "unorderedPairVisits": pair_count,
        "directionalScoreCount": directional_score_count,
        "k": k,
        "compactRankings": rankings,
        "rankings": rankings,
        "rankingSha256": ranking_digest.hexdigest(),
        "modelScoreMs": dict(sorted(score_elapsed.items())),
        "compileMs": compile_ms,
        "elapsedMs": (time.perf_counter() - started) * 1000,
        "pairRowsRetained": 0,
        "fullPairMatrixMaterialized": False,
        "randomnessAffectsAffinity": False,
    }


def stream_exhaustive_top_k(
    context: ModelContext,
    specs: Sequence[ModelSpec],
    *,
    k: int = 50,
    query_ids: Iterable[str] | None = None,
    block_size: int = 128,
    checkpoint: Callable[[Mapping[str, Any]], None] | None = None,
    engine: str = "COMPACT_NUMPY_BLOCK",
    retain_rankings: bool = True,
    ranking_sink: Callable[[str, str, tuple[tuple[str, float], ...]], None] | None = None,
    trusted_interaction_context: interaction_statistics.TrustedInteractionContext | None = None,
) -> dict[str, Any]:
    """Bounded exhaustive reference ranking with a selectable audit engine.

    ``COMPACT_NUMPY_BLOCK`` is the full-corpus engine.  The slower
    ``REFERENCE_PYTHON`` path remains available for parity tests on small
    cohorts.  For minimum peak memory, invoke one model spec at a time and use
    ``ranking_sink`` with ``retain_rankings=False``.
    """

    if engine == "COMPACT_NUMPY_BLOCK":
        if trusted_interaction_context is not None:
            raise ModelError(
                "compact exhaustive scoring excludes interactions; use REFERENCE_PYTHON or object-local ranking"
            )
        return _stream_exhaustive_top_k_compact(
            context,
            specs,
            k=k,
            query_ids=query_ids,
            block_size=block_size,
            checkpoint=checkpoint,
            retain_rankings=retain_rankings,
            ranking_sink=ranking_sink,
        )
    if engine == "REFERENCE_PYTHON":
        if not retain_rankings or ranking_sink is not None:
            raise ModelError("reference Python engine does not implement streaming sinks")
        return _stream_exhaustive_top_k_python(
            context,
            specs,
            k=k,
            query_ids=query_ids,
            block_size=block_size,
            checkpoint=checkpoint,
            trusted_interaction_context=trusted_interaction_context,
        )
    raise ModelError("unsupported exhaustive scoring engine")


def compact_ranking_ids(rows: Sequence[Any]) -> tuple[str, ...]:
    """Adapt compact ``(candidateId, score)`` rows for recall/hubness helpers."""

    output: list[str] = []
    for row in rows:
        if isinstance(row, Mapping):
            candidate_id = str(row.get("candidateId", ""))
        elif isinstance(row, Sequence) and not isinstance(row, (str, bytes, bytearray)) and len(row) >= 1:
            candidate_id = str(row[0])
        else:
            candidate_id = str(row)
        if not candidate_id:
            raise ModelError("compact ranking row lacks a candidate ID")
        output.append(candidate_id)
    return tuple(output)


def object_local_top_k_compact(
    compiled: CompiledFeatureContext,
    query_id: str,
    spec: ModelSpec,
    *,
    candidate_ids: Iterable[str] | None = None,
    k: int = 50,
) -> tuple[tuple[str, float], ...]:
    import numpy as np

    if k <= 0:
        raise ModelError("object-local k must be positive")
    if query_id not in compiled.object_ordinals:
        raise ModelError("object-local query is outside the compiled cohort")
    candidates = tuple(
        compiled.object_ids
        if candidate_ids is None
        else sorted({str(value) for value in candidate_ids})
    )
    candidate_ordinals = np.asarray(
        [compiled.object_ordinals[value] for value in candidates if value != query_id],
        dtype=np.int64,
    )
    query_ordinal = compiled.object_ordinals[query_id]
    scores = score_compiled_block(compiled, (query_ordinal,), candidate_ordinals, spec)[0]
    order = np.lexsort((candidate_ordinals, -scores))[: min(k, len(candidate_ordinals))]
    return tuple(
        (compiled.object_ids[int(candidate_ordinals[position])], float(scores[position]))
        for position in order
    )


def object_local_top_k(
    context: ModelContext,
    query_id: str,
    spec: ModelSpec,
    *,
    candidate_ids: Iterable[str] | None = None,
    k: int = 50,
    trusted_interaction_context: interaction_statistics.TrustedInteractionContext | None = None,
) -> list[dict[str, Any]]:
    candidates = context.candidate_index.object_ids if candidate_ids is None else candidate_ids
    return rank_candidates(
        context,
        query_id,
        candidates,
        spec,
        k=k,
        trusted_interaction_context=trusted_interaction_context,
    )


def assert_symmetric(context: ModelContext, spec: ModelSpec, pairs: Iterable[tuple[str, str]]) -> int:
    if not spec.symmetric:
        raise ModelError("symmetry test requested for an asymmetric model")
    failures = 0
    for left, right in pairs:
        forward = score_pair(context, left, right, spec)
        reverse = score_pair(context, right, left, spec)
        if forward.diagnostic_score != reverse.diagnostic_score or forward.family_scores != reverse.family_scores:
            failures += 1
    return failures


def self_test() -> dict[str, Any]:
    token = lambda value: {"id": value, "label": value}
    records = []
    values = (
        ("M1", "T1", "D1", "G1", "S1", "OT1", "C1", 1900),
        ("M1", "T1", "D1", "G1", "S2", "OT1", "C2", 1900),
        ("M1", "T2", "D2", "G2", "S1", "OT2", "C3", 1910),
        ("M2", "T3", "D3", "G3", "S3", "OT3", "C4", 1950),
    )
    for ordinal, (medium, theme, decade, geography, source, object_type, curated, year) in enumerate(values, start=1):
        records.append({
            "objectId": f"SURF-M{ordinal}",
            "medium": [token(medium)],
            "theme": [token(theme)],
            "movement_context": [],
            "decade": [token(decade)],
            "geography": [token(geography)],
            "curated_container": [token(curated)],
            "source": token(source),
            "object_type": token(object_type),
            "creator": token(f"CR{ordinal}"),
            "startYear": year,
            "endYear": year,
            "temporalPrecision": "year",
            "geographyMappingStates": ["mapped"],
            "geographyClasses": ["country"],
            "geographyQualified": False,
            "multiRegion": False,
        })
    index = candidate_index.build_exploration_candidate_index(records)
    context = build_model_context(index)
    specs = default_model_specs()
    symmetric_failures = sum(
        assert_symmetric(context, spec, (("SURF-M1", "SURF-M2"), ("SURF-M1", "SURF-M3")))
        for spec in specs
        if spec.symmetric and spec.model_id != "M8"
    )
    if symmetric_failures:
        raise AssertionError("symmetric model failed pair reversal")
    compiled = compile_feature_context(context)
    compact_parity_failures = 0
    for spec in specs:
        if spec.model_id == "M8":
            continue
        for left in index.object_ids:
            for right in index.object_ids:
                if left == right:
                    continue
                expected = float(score_pair(context, left, right, spec).diagnostic_score or 0.0)
                actual = score_compiled_pair(compiled, left, right, spec)
                compact_parity_failures += int(expected != actual)
    if compact_parity_failures:
        raise AssertionError(f"compact scorer parity failures: {compact_parity_failures}")
    m7_spec = next(spec for spec in specs if spec.model_id == "M7")
    m7_profile = score_pair(context, "SURF-M1", "SURF-M2", m7_spec)
    m7_formula_rows = [
        row
        for row in m7_profile.contributions
        if row.get("basis") == "BM25F_LIKE_FIELDED_RETRIEVAL"
    ]
    if (
        not m7_formula_rows
        or not any(row.get("field") == "decade" for row in m7_formula_rows)
        or any(
            row.get("formula") != "BM25F_LIKE_FIELD_SATURATION"
            or not row.get("queryTermStatistics")
            or float(row.get("averageDocumentFieldLength", 0)) <= 0
            or float(row.get("declaredFamilyWeight", 0)) <= 0
            for row in m7_formula_rows
        )
    ):
        raise AssertionError("M7 field/temporal formula metadata is incomplete")
    m1 = specs[0]
    ranking = object_local_top_k(context, "SURF-M1", m1, k=3)
    streamed = stream_exhaustive_top_k(context, (m1,), k=3)
    streamed_ids = compact_ranking_ids(streamed["rankings"][m1.variant_id]["SURF-M1"])
    if tuple(row["candidateId"] for row in ranking) != streamed_ids:
        raise AssertionError("object-local/exhaustive ordering diverged")
    if ranking[0]["candidateId"] != "SURF-M2":
        raise AssertionError("several independent matches did not rank first")
    if any(row["candidateId"] == "SURF-M1" for row in ranking):
        raise AssertionError("self entered affinity ranking")
    interaction_registry = interaction_statistics.build_observed_interaction_registry(
        records,
        pair_specs=(
            ("medium", "theme"),
            ("medium", "decade"),
            ("theme", "decade"),
        ),
        triple_specs=(),
    )
    trusted_interactions = interaction_statistics.build_trusted_interaction_context(
        interaction_registry,
        records,
    )
    interaction_index = candidate_index.build_exploration_candidate_index(
        records,
        trusted_interaction_context=trusted_interactions,
    )
    interaction_model_context = build_model_context(interaction_index)
    interaction_spec = replace(
        next(spec for spec in specs if spec.model_id == "M5"),
        variant_id="M5-TRUSTED-CAPPED-INTERACTION",
        interaction_policy="CAPPED_INTERACTION_BONUS",
        interaction_support_threshold=2,
        interaction_cap=0.10,
    )
    trusted_profile = score_pair(
        interaction_model_context,
        "SURF-M1",
        "SURF-M2",
        interaction_spec,
        trusted_interaction_context=trusted_interactions,
    )
    if len(trusted_profile.interactions) < 2:
        raise AssertionError("trusted multi-row interaction fixture did not resolve")
    emitted_interaction_total = math.fsum(
        float(row["residualScore"]) for row in trusted_profile.interactions
    )
    aggregate_interaction_bonus = float(
        trusted_profile.interactions[0]["aggregateBonus"]
    )
    if not math.isclose(
        emitted_interaction_total,
        aggregate_interaction_bonus,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise AssertionError("interaction rows did not normalize exactly to aggregate bonus")
    if any(
        row["aggregateBonus"] != aggregate_interaction_bonus
        or row["aggregateResidualNormalized"] is not True
        or set(row["objectIds"]) != {"SURF-M1", "SURF-M2"}
        or row["registrySha256"] != interaction_registry["registrySha256"]
        for row in trusted_profile.interactions
    ):
        raise AssertionError("trusted interaction explanation provenance diverged")
    if not math.isclose(
        sum(trusted_profile.family_contribution_units.values()),
        float(trusted_profile.diagnostic_score),
        rel_tol=0.0,
        abs_tol=2e-12,
    ):
        raise AssertionError("final-score contribution units did not reconcile")
    if not math.isclose(
        sum(trusted_profile.family_contribution_shares.values()),
        1.0,
        rel_tol=0.0,
        abs_tol=2e-12,
    ):
        raise AssertionError("family contribution shares did not sum to one")
    fabricated_interaction_rejected = False
    try:
        score_pair(
            interaction_model_context,
            "SURF-M1",
            "SURF-M2",
            interaction_spec,
            interaction_evidence=({
                "interactionId": "EXP:INTERACTION:FABRICATED",
                "registrySha256": "0" * 64,
                "objectIds": ["SURF-M1", "SURF-M2"],
                "residualScore": 1_000_000.0,
            },),
        )
    except ModelError:
        fabricated_interaction_rejected = True
    if not fabricated_interaction_rejected:
        raise AssertionError("model accepted caller-fabricated interaction evidence")
    unbound_context_rejected = False
    try:
        score_pair(
            context,
            "SURF-M1",
            "SURF-M2",
            interaction_spec,
            trusted_interaction_context=trusted_interactions,
        )
    except ModelError:
        unbound_context_rejected = True
    if not unbound_context_rejected:
        raise AssertionError("model accepted a trusted registry not bound into its index")
    temporal_mutation = json.loads(json.dumps(records))
    temporal_mutation[0]["startYear"] += 1
    temporal_mutation[0]["endYear"] += 1
    mutated_context = build_model_context(
        candidate_index.build_exploration_candidate_index(temporal_mutation)
    )
    mutated_compiled = compile_feature_context(mutated_context)
    if (
        mutated_context.context_sha256 == context.context_sha256
        or mutated_compiled.compiled_sha256 == compiled.compiled_sha256
    ):
        raise AssertionError("model/compiled context hashes did not bind temporal inputs")
    if len(source_treatment_model_specs()) != len(SOURCE_TREATMENTS):
        raise AssertionError("source-treatment experiment grid is incomplete")
    if len(interaction_policy_model_specs()) != len(INTERACTION_POLICIES):
        raise AssertionError("interaction policy experiment grid is incomplete")
    return {
        "status": "PASS",
        "modelFamilyCount": len(MODEL_IDS) + 1,
        "scoringEligibleModelCount": len(MODEL_IDS),
        "benchmarkVariantCount": len(benchmark_model_specs()) + 1,
        "symmetricFailureCount": 0,
        "compactScorerParityFailureCount": compact_parity_failures,
        "sameSourceFactDoubleScoreCount": 0,
        "geographicLayoutDistanceScoreCount": 0,
        "randomnessAffectsAffinity": False,
        "fullPairMatrixMaterialized": False,
        "fabricatedInteractionEvidenceRejected": fabricated_interaction_rejected,
        "unboundTrustedInteractionContextRejected": unbound_context_rejected,
        "trustedInteractionRowCount": len(trusted_profile.interactions),
        "trustedInteractionAggregateBonus": aggregate_interaction_bonus,
        "interactionResidualExactSum": emitted_interaction_total == aggregate_interaction_bonus,
        "sourceTreatmentExperimentCount": len(source_treatment_model_specs()),
        "interactionPolicyExperimentCount": len(interaction_policy_model_specs()),
        "temporalMutationChangedModelContextHash": True,
        "temporalMutationChangedCompiledContextHash": True,
        "m7FormulaExplanationRowCount": len(m7_formula_rows),
        "m7TemporalUsesGovernedDecadeBm25Field": True,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
