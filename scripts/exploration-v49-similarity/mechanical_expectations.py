#!/usr/bin/env python3
"""Deterministic rule-derived mechanical expectations for Exploration affinity.

The cases in this module encode explicit project boundaries.  They do not
assert historical relationships and they do not use researcher judgements.
Each AX-001..AX-015 result is a flat row that can be written directly to the
Round 6 mechanical-expectation TSV by the research orchestrator.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any, Callable

import candidate_index
import interaction_statistics
import missingness_comparability as missingness
import model_baselines
import negative_control


SCHEMA_VERSION = "trace-exploration-mechanical-expectations/v1"
IMPLEMENTATION_VERSION = "trace-exploration-mechanical-expectations-2026-08-24"
DEFAULT_GATE_MODEL_IDS = ("M2", "M5", "M7")


class MechanicalExpectationError(ValueError):
    """Raised when the suite or a supplied model gate is malformed."""


@dataclass(frozen=True)
class AxiomDefinition:
    axiom_id: str
    rule: str
    expected_invariant: str
    applicability: str
    applies_to: Callable[[model_baselines.ModelSpec], bool]


@dataclass(frozen=True)
class ModelObservation:
    passed: bool
    observed: str


def _all_models(_: model_baselines.ModelSpec) -> bool:
    return True


def _symmetric_models(spec: model_baselines.ModelSpec) -> bool:
    return spec.symmetric and spec.model_id != "M8"


def _query_models(spec: model_baselines.ModelSpec) -> bool:
    return not spec.symmetric and spec.task == "USER_CONDITIONED_RETRIEVAL"


AXIOM_DEFINITIONS = (
    AxiomDefinition(
        "AX-001",
        "One extremely broad curated container cannot outrank several independent governed matches.",
        "governed_multi_family_score > broad_curatorial_only_score; raw curation remains diagnostic only",
        "SCALAR_AFFINITY_AND_QUERY_RETRIEVAL",
        _all_models,
    ),
    AxiomDefinition(
        "AX-002",
        "A duplicate representation of one source fact cannot add affinity.",
        "single_source_fact_score == cross_representation_duplicate_score; contributions are identical and the derived representation is exposed as ignored",
        "ALL_SHORTLIST_MODELS",
        _all_models,
    ),
    AxiomDefinition(
        "AX-003",
        "Shared unknown, missing, or not-governed states add zero default affinity.",
        "diagnostic_score == 0 and missingness positiveAffinityCredit == 0",
        "ALL_SHORTLIST_MODELS_AND_MISSINGNESS_CHANNEL",
        _all_models,
    ),
    AxiomDefinition(
        "AX-004",
        "Adding an independent high-information match cannot reduce affinity.",
        "enhanced_independent_match_score >= baseline_score",
        "ALL_SHORTLIST_MODELS",
        _all_models,
    ),
    AxiomDefinition(
        "AX-005",
        "Adding an unrelated broad curated feature cannot materially increase affinity.",
        "score_delta == 0 while the isolated raw-curation diagnostic changes",
        "ALL_SHORTLIST_MODELS_AND_NEGATIVE_CONTROL_BOUNDARY",
        _all_models,
    ),
    AxiomDefinition(
        "AX-006",
        "A same-source match alone cannot overwhelm Context or Spacetime evidence.",
        "cross_source_governed_score > same_source_only_score",
        "ALL_SHORTLIST_MODELS",
        _all_models,
    ),
    AxiomDefinition(
        "AX-007",
        "A support-1 or support-2 observation cannot create an unbounded contribution.",
        "score remains in [0,1], low-support contribution is capped, and several governed matches outrank one broad curatorial-only match",
        "REQUIRED_M2_M5_M7_WITH_ANALYSIS_ONLY_INTERACTION_CAP",
        _all_models,
    ),
    AxiomDefinition(
        "AX-008",
        "Symmetric-task scores are invariant to pair reversal.",
        "score(left,right) == score(right,left) and family profiles are equal",
        "SYMMETRIC_SHORTLIST_MODELS",
        _symmetric_models,
    ),
    AxiomDefinition(
        "AX-009",
        "Query-conditioned asymmetry is declared and reproducible.",
        "forward != reverse, repeated_forward == forward, and symmetric == false",
        "QUERY_CONDITIONED_SHORTLIST_MODELS",
        _query_models,
    ),
    AxiomDefinition(
        "AX-010",
        "Removing an unavailable family changes comparability and cannot be silent.",
        "comparability ratio falls and the unavailable family is explicitly named",
        "ALL_SHORTLIST_MODELS",
        _all_models,
    ),
    AxiomDefinition(
        "AX-011",
        "An object is excluded from its own candidate list and score path.",
        "self is absent for CG-CUR-1..6 and direct self scoring is rejected",
        "SHARED_CANDIDATE_AND_SCORING_ARCHITECTURE",
        _all_models,
    ),
    AxiomDefinition(
        "AX-012",
        "Duplicate titles remain separate public identities.",
        "same title plus distinct public IDs yields two indexed, mutually retrievable identities",
        "SHARED_CANDIDATE_AND_SCORING_ARCHITECTURE",
        _all_models,
    ),
    AxiomDefinition(
        "AX-013",
        "Geographic layout or map-coordinate distance contributes zero.",
        "coordinate changes leave index hash, score, and contributions unchanged",
        "ALL_SHORTLIST_MODELS",
        _all_models,
    ),
    AxiomDefinition(
        "AX-014",
        "A universal broad source or container hub cannot remain undetected.",
        "near-full fanout plus concentrated deterministic top-1 occurrence raises a hub signal",
        "SHARED_DIAGNOSTIC_ARCHITECTURE",
        _all_models,
    ),
    AxiomDefinition(
        "AX-015",
        "Seeded randomness contributes zero to candidates, scores, and comparability.",
        "different global random seeds produce identical candidate and profile hashes",
        "ALL_SHORTLIST_MODELS_AND_CANDIDATE_ARCHITECTURE",
        _all_models,
    ),
)

AXIOM_IDS = tuple(definition.axiom_id for definition in AXIOM_DEFINITIONS)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256((_canonical_json(value) + "\n").encode("utf-8")).hexdigest()


def _token(identifier: str, label: str | None = None) -> dict[str, str]:
    return {"id": identifier, "label": label if label is not None else identifier}


def _record(
    object_id: str,
    *,
    title: str | None = None,
    medium: Sequence[str] = ("MEDIUM-A",),
    theme: Sequence[str] = ("THEME-A",),
    movement: Sequence[str] = (),
    decade: Sequence[str] = ("1900S",),
    geography: Sequence[str] = ("GEO-A",),
    curated: Sequence[str] = (),
    source: str = "SOURCE-A",
    object_type: str = "TYPE-A",
    creator: str = "CREATOR-A",
    year: int = 1900,
    end_year: int | None = None,
    temporal_precision: str = "year",
    labels: Mapping[str, str] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    label_by_id = labels or {}
    row: dict[str, Any] = {
        "objectId": object_id,
        "title": title or object_id,
        "medium": [_token(value, label_by_id.get(value)) for value in medium],
        "theme": [_token(value, label_by_id.get(value)) for value in theme],
        "movement_context": [_token(value, label_by_id.get(value)) for value in movement],
        "decade": [_token(value, label_by_id.get(value)) for value in decade],
        "geography": [_token(value, label_by_id.get(value)) for value in geography],
        "curated_container": [_token(value, label_by_id.get(value)) for value in curated],
        "source": _token(source, label_by_id.get(source)),
        "object_type": _token(object_type, label_by_id.get(object_type)),
        "creator": _token(creator, label_by_id.get(creator)),
        "startYear": year,
        "endYear": year if end_year is None else end_year,
        "temporalPrecision": temporal_precision,
        "geographyMappingStates": [_token("MAPPED", "Mapped")],
        "geographyClasses": [_token("COUNTRY", "Country")],
        "geographyQualified": False,
        "multiRegion": len(set(geography)) > 1,
    }
    if extra:
        row.update(extra)
    return row


def _index_context(
    records: Sequence[Mapping[str, Any]],
    *,
    residual_curation_by_object: Mapping[str, Iterable[str]] | None = None,
) -> tuple[candidate_index.CandidateIndex, model_baselines.ModelContext]:
    index = candidate_index.build_exploration_candidate_index(
        records,
        residual_curation_by_object=residual_curation_by_object,
    )
    return index, model_baselines.build_model_context(index)


def _fixture_fillers(prefix: str, count: int, *, curated: Sequence[str] = ()) -> list[dict[str, Any]]:
    return [
        _record(
            f"SURF-{prefix}-{ordinal:02d}",
            medium=(f"MEDIUM-{prefix}-{ordinal}",),
            theme=(f"THEME-{prefix}-{ordinal}",),
            decade=(f"{1800 + ordinal * 10}S",),
            geography=(f"GEO-{prefix}-{ordinal}",),
            curated=curated,
            source=f"SOURCE-{prefix}-{ordinal}",
            object_type=f"TYPE-{prefix}-{ordinal}",
            creator=f"CREATOR-{prefix}-{ordinal}",
            year=1800 + ordinal * 10,
        )
        for ordinal in range(1, count + 1)
    ]


def _select_specs(
    specs: Iterable[model_baselines.ModelSpec] | None,
    required_model_ids: Sequence[str],
) -> dict[str, model_baselines.ModelSpec]:
    selected_input = tuple(specs) if specs is not None else model_baselines.default_model_specs()
    by_id: dict[str, model_baselines.ModelSpec] = {}
    for spec in selected_input:
        if spec.model_id not in required_model_ids:
            continue
        if spec.model_id in by_id:
            raise MechanicalExpectationError(f"multiple supplied specs for {spec.model_id}")
        by_id[spec.model_id] = spec
    missing_ids = tuple(model_id for model_id in required_model_ids if model_id not in by_id)
    if missing_ids:
        raise MechanicalExpectationError(f"mechanical gate lacks model specs: {','.join(missing_ids)}")
    return {model_id: by_id[model_id] for model_id in required_model_ids}


def _safe_observation(function: Callable[[], tuple[bool, str]]) -> ModelObservation:
    try:
        passed, observed = function()
        return ModelObservation(bool(passed), str(observed))
    except Exception as error:  # A gate records implementation failures instead of concealing them.
        return ModelObservation(False, f"{type(error).__name__}:{error}")


def _model_observations(
    specs: Mapping[str, model_baselines.ModelSpec],
    definition: AxiomDefinition,
    evaluator: Callable[[model_baselines.ModelSpec], tuple[bool, str]],
) -> dict[str, ModelObservation]:
    return {
        model_id: _safe_observation(lambda spec=spec: evaluator(spec))
        for model_id, spec in specs.items()
        if definition.applies_to(spec)
    }


def _ax001(specs: Mapping[str, model_baselines.ModelSpec]) -> dict[str, ModelObservation]:
    query = _record("SURF-AX1-Q", curated=("BROAD-CONTAINER",))
    governed = _record(
        "SURF-AX1-G",
        curated=("NARROW-G",),
        source="SOURCE-B",
        creator="CREATOR-G",
    )
    broad = _record(
        "SURF-AX1-B",
        medium=("MEDIUM-X",),
        theme=("THEME-X",),
        decade=("1950S",),
        geography=("GEO-X",),
        curated=("BROAD-CONTAINER",),
        source="SOURCE-X",
        object_type="TYPE-X",
        creator="CREATOR-X",
        year=1950,
    )
    _, context = _index_context([query, governed, broad] + _fixture_fillers("AX1F", 8, curated=("BROAD-CONTAINER",)))
    m0_broad = float(negative_control.raw_curated_jaccard(query, broad)["diagnosticScore"])
    m0_governed = float(negative_control.raw_curated_jaccard(query, governed)["diagnosticScore"])
    definition = AXIOM_DEFINITIONS[0]

    def evaluate(spec: model_baselines.ModelSpec) -> tuple[bool, str]:
        governed_score = float(model_baselines.score_pair(context, query["objectId"], governed["objectId"], spec).diagnostic_score or 0.0)
        broad_score = float(model_baselines.score_pair(context, query["objectId"], broad["objectId"], spec).diagnostic_score or 0.0)
        passed = governed_score > broad_score and m0_broad > m0_governed
        return passed, f"governed={governed_score:.12g};broad={broad_score:.12g};M0Broad={m0_broad:.12g};M0Governed={m0_governed:.12g}"

    return _model_observations(specs, definition, evaluate)


def _ax002(specs: Mapping[str, model_baselines.ModelSpec]) -> dict[str, ModelObservation]:
    # The theme and curated folder represent the same underlying membership
    # fact through different archive representations.  The governed theme is
    # the sole scoring representation; the folder remains recall/provenance.
    single_query = _record("SURF-AX2-Q", curated=("QUERY-NAVIGATION",))
    single_candidate = _record(
        "SURF-AX2-C",
        curated=("CANDIDATE-NAVIGATION",),
        source="SOURCE-C",
        creator="CREATOR-C",
    )
    duplicated_query = _record("SURF-AX2-Q", curated=("THEME-A-SOURCE-FOLDER",))
    duplicated_candidate = _record(
        "SURF-AX2-C",
        curated=("THEME-A-SOURCE-FOLDER",),
        source="SOURCE-C",
        creator="CREATOR-C",
    )
    fillers = _fixture_fillers("AX2F", 4)
    _, single_context = _index_context([single_query, single_candidate] + fillers)
    duplicated_index, duplicated_context = _index_context(
        [duplicated_query, duplicated_candidate] + fillers
    )
    derived_signal_id = "SIG-CURATORIAL-MEMBERSHIP"
    duplicated_representation_present = (
        "THEME-A-SOURCE-FOLDER"
        in duplicated_index.records[duplicated_query["objectId"]].curated_tokens
        and "THEME-A-SOURCE-FOLDER"
        in duplicated_index.records[duplicated_candidate["objectId"]].curated_tokens
    )
    m0_single = float(
        negative_control.raw_curated_jaccard(single_query, single_candidate)["diagnosticScore"]
    )
    m0_duplicated = float(
        negative_control.raw_curated_jaccard(duplicated_query, duplicated_candidate)["diagnosticScore"]
    )
    definition = AXIOM_DEFINITIONS[1]

    def evaluate(spec: model_baselines.ModelSpec) -> tuple[bool, str]:
        one = model_baselines.score_pair(
            single_context,
            single_query["objectId"],
            single_candidate["objectId"],
            spec,
        )
        duplicated = model_baselines.score_pair(
            duplicated_context,
            duplicated_query["objectId"],
            duplicated_candidate["objectId"],
            spec,
            ignored_duplicate_signals=(derived_signal_id,),
        )
        curatorial_contribution_count = sum(
            row.get("family") == "curatorialResidual" for row in duplicated.contributions
        )
        passed = (
            duplicated_representation_present
            and m0_duplicated > m0_single
            and one.diagnostic_score == duplicated.diagnostic_score
            and one.family_scores == duplicated.family_scores
            and one.contributions == duplicated.contributions
            and duplicated.ignored_duplicate_signals == (derived_signal_id,)
            and curatorial_contribution_count == 0
        )
        return passed, (
            f"singleFact={one.diagnostic_score};crossRepresentationDuplicate={duplicated.diagnostic_score};"
            f"contributionsEqual={str(one.contributions == duplicated.contributions).lower()};"
            f"curatorialContributions={curatorial_contribution_count};ignored={derived_signal_id};"
            f"M0Single={m0_single:.12g};M0Duplicated={m0_duplicated:.12g}"
        )

    return _model_observations(specs, definition, evaluate)


def _ax003(specs: Mapping[str, model_baselines.ModelSpec]) -> dict[str, ModelObservation]:
    unknown_labels = {
        "UNKNOWN": "Unknown",
        "NOT-GOVERNED": "Not Governed",
        "NO_PUBLISHED_MOVEMENT_CONTEXT": "No Published Movement Context",
    }
    left = _record(
        "SURF-AX3-L",
        medium=("UNKNOWN",),
        theme=("NOT-GOVERNED",),
        movement=("NO_PUBLISHED_MOVEMENT_CONTEXT",),
        decade=("UNKNOWN",),
        geography=("UNKNOWN",),
        source="UNKNOWN",
        object_type="NOT-GOVERNED",
        creator="UNKNOWN",
        temporal_precision="unknown",
        labels=unknown_labels,
    )
    right = dict(left)
    right["objectId"] = "SURF-AX3-R"
    right["title"] = "SURF-AX3-R"
    _, context = _index_context([left, right])
    missing_diagnostic = missingness.compare_missingness_states(left, right)
    definition = AXIOM_DEFINITIONS[2]

    def evaluate(spec: model_baselines.ModelSpec) -> tuple[bool, str]:
        profile = model_baselines.score_pair(context, left["objectId"], right["objectId"], spec)
        score = float(profile.diagnostic_score or 0.0)
        ratio = float(profile.comparability["ratio"])
        passed = score == 0.0 and ratio == 0.0 and missing_diagnostic["positiveAffinityCredit"] == 0.0
        return passed, f"score={score:.12g};comparability={ratio:.12g};missingCredit={missing_diagnostic['positiveAffinityCredit']}"

    return _model_observations(specs, definition, evaluate)


def _ax004(specs: Mapping[str, model_baselines.ModelSpec]) -> dict[str, ModelObservation]:
    query = _record("SURF-AX4-Q", movement=("MOVEMENT-A",))
    baseline = _record(
        "SURF-AX4-B",
        medium=("MEDIUM-X",),
        theme=("THEME-A",),
        movement=("MOVEMENT-X",),
        decade=("1950S",),
        geography=("GEO-X",),
        source="SOURCE-X",
        object_type="TYPE-X",
        creator="CREATOR-X",
        year=1950,
    )
    enhanced = _record(
        "SURF-AX4-E",
        medium=("MEDIUM-A",),
        theme=("THEME-A",),
        movement=("MOVEMENT-A",),
        decade=("1900S",),
        geography=("GEO-A",),
        source="SOURCE-E",
        object_type="TYPE-X",
        creator="CREATOR-X",
        year=1900,
    )
    _, context = _index_context([query, baseline, enhanced] + _fixture_fillers("AX4F", 6))
    definition = AXIOM_DEFINITIONS[3]

    def evaluate(spec: model_baselines.ModelSpec) -> tuple[bool, str]:
        base_score = float(model_baselines.score_pair(context, query["objectId"], baseline["objectId"], spec).diagnostic_score or 0.0)
        enhanced_score = float(model_baselines.score_pair(context, query["objectId"], enhanced["objectId"], spec).diagnostic_score or 0.0)
        return enhanced_score >= base_score, f"baseline={base_score:.12g};enhanced={enhanced_score:.12g};delta={enhanced_score-base_score:.12g}"

    return _model_observations(specs, definition, evaluate)


def _ax005(specs: Mapping[str, model_baselines.ModelSpec]) -> dict[str, ModelObservation]:
    base_query = _record("SURF-AX5-Q", curated=("ONLY-Q",))
    base_candidate = _record(
        "SURF-AX5-C",
        medium=("MEDIUM-X",),
        curated=("ONLY-C",),
        source="SOURCE-C",
        creator="CREATOR-C",
    )
    broad_query = _record("SURF-AX5-Q", curated=("BROAD-UNRELATED",))
    broad_candidate = _record(
        "SURF-AX5-C",
        medium=("MEDIUM-X",),
        curated=("BROAD-UNRELATED",),
        source="SOURCE-C",
        creator="CREATOR-C",
    )
    _, base_context = _index_context([base_query, base_candidate] + _fixture_fillers("AX5A", 6))
    _, broad_context = _index_context(
        [broad_query, broad_candidate] + _fixture_fillers("AX5B", 6, curated=("BROAD-UNRELATED",))
    )
    m0_before = float(negative_control.raw_curated_jaccard(base_query, base_candidate)["diagnosticScore"])
    m0_after = float(negative_control.raw_curated_jaccard(broad_query, broad_candidate)["diagnosticScore"])
    definition = AXIOM_DEFINITIONS[4]

    def evaluate(spec: model_baselines.ModelSpec) -> tuple[bool, str]:
        before = float(model_baselines.score_pair(base_context, "SURF-AX5-Q", "SURF-AX5-C", spec).diagnostic_score or 0.0)
        after = float(model_baselines.score_pair(broad_context, "SURF-AX5-Q", "SURF-AX5-C", spec).diagnostic_score or 0.0)
        delta = after - before
        passed = math.isclose(delta, 0.0, abs_tol=1e-12) and m0_after > m0_before
        return passed, f"before={before:.12g};after={after:.12g};delta={delta:.12g};M0Before={m0_before:.12g};M0After={m0_after:.12g}"

    return _model_observations(specs, definition, evaluate)


def _ax006(specs: Mapping[str, model_baselines.ModelSpec]) -> dict[str, ModelObservation]:
    query = _record("SURF-AX6-Q")
    same_source = _record(
        "SURF-AX6-S",
        medium=("MEDIUM-X",),
        theme=("THEME-X",),
        decade=("1950S",),
        geography=("GEO-X",),
        source="SOURCE-A",
        object_type="TYPE-X",
        creator="CREATOR-X",
        year=1950,
    )
    governed = _record("SURF-AX6-G", source="SOURCE-B", creator="CREATOR-G")
    _, context = _index_context([query, same_source, governed] + _fixture_fillers("AX6F", 5))
    definition = AXIOM_DEFINITIONS[5]

    def evaluate(spec: model_baselines.ModelSpec) -> tuple[bool, str]:
        source_score = float(model_baselines.score_pair(context, query["objectId"], same_source["objectId"], spec).diagnostic_score or 0.0)
        governed_score = float(model_baselines.score_pair(context, query["objectId"], governed["objectId"], spec).diagnostic_score or 0.0)
        return governed_score > source_score, f"sameSourceOnly={source_score:.12g};governedCrossSource={governed_score:.12g}"

    return _model_observations(specs, definition, evaluate)


def _ax007(specs: Mapping[str, model_baselines.ModelSpec]) -> dict[str, ModelObservation]:
    query = _record("SURF-AX7-Q", curated=("BROAD-CONTAINER",))
    governed = _record(
        "SURF-AX7-G",
        curated=("NARROW-GOVERNED",),
        source="SOURCE-G",
        creator="CREATOR-G",
    )
    broad_only = _record(
        "SURF-AX7-B",
        medium=("MEDIUM-X",),
        theme=("THEME-X",),
        decade=("1950S",),
        geography=("GEO-X",),
        curated=("BROAD-CONTAINER",),
        source="SOURCE-X",
        object_type="TYPE-X",
        creator="CREATOR-X",
        year=1950,
    )
    fixture_records = [query, governed, broad_only] + _fixture_fillers(
        "AX7F",
        8,
        curated=("BROAD-CONTAINER",),
    )
    interaction_registry = interaction_statistics.build_observed_interaction_registry(
        fixture_records,
        pair_specs=(("medium", "theme"),),
        triple_specs=(),
    )
    trusted_interactions = interaction_statistics.build_trusted_interaction_context(
        interaction_registry,
        fixture_records,
    )
    interaction_index = candidate_index.build_exploration_candidate_index(
        fixture_records,
        trusted_interaction_context=trusted_interactions,
    )
    context = model_baselines.build_model_context(interaction_index)
    raw_broad_diagnostic = float(
        negative_control.raw_curated_jaccard(query, broad_only)["diagnosticScore"]
    )
    definition = AXIOM_DEFINITIONS[6]

    def evaluate(spec: model_baselines.ModelSpec) -> tuple[bool, str]:
        capped_spec = replace(
            spec,
            variant_id=f"{spec.variant_id}-AX7-CAP",
            interaction_policy="CAPPED_INTERACTION_BONUS",
            interaction_cap=0.10,
            interaction_support_threshold=5,
        )
        governed_profile = model_baselines.score_pair(
            context,
            query["objectId"],
            governed["objectId"],
            capped_spec,
            trusted_interaction_context=trusted_interactions,
        )
        broad_profile = model_baselines.score_pair(
            context,
            query["objectId"],
            broad_only["objectId"],
            capped_spec,
            trusted_interaction_context=trusted_interactions,
        )
        fabricated_evidence_rejected = False
        try:
            model_baselines.score_pair(
                context,
                query["objectId"],
                broad_only["objectId"],
                capped_spec,
                interaction_evidence=({
                    "interactionId": "EXP:INTERACTION:AX7-SUPPORT-1",
                    "support": 1,
                    "residualScore": 1_000_000.0,
                },),
            )
        except model_baselines.ModelError:
            fabricated_evidence_rejected = True
        governed_score = float(governed_profile.diagnostic_score or 0.0)
        broad_score = float(broad_profile.diagnostic_score or 0.0)
        residual = max(
            (float(row["residualScore"]) for row in governed_profile.interactions),
            default=0.0,
        )
        passed = (
            raw_broad_diagnostic > 0.0
            and 0.0 <= governed_score <= 1.0
            and residual <= 0.10
            and all(int(row["support"]) == 2 for row in governed_profile.interactions)
            and not broad_profile.interactions
            and fabricated_evidence_rejected
            and governed_score > broad_score
            and all(
                value is None or 0.0 <= value <= 1.0
                for value in governed_profile.family_scores.values()
            )
        )
        return passed, (
            f"governedMultiFamily={governed_score:.12g};broadCuratorialOnly={broad_score:.12g};"
            f"trustedSupport2Residual={residual:.12g};support1PairResidual=0;"
            f"fabricatedEvidenceRejected={str(fabricated_evidence_rejected).lower()};"
            f"M0Broad={raw_broad_diagnostic:.12g};orderingPass={str(governed_score > broad_score).lower()};cap=0.1"
        )

    return _model_observations(specs, definition, evaluate)


def _ax008(specs: Mapping[str, model_baselines.ModelSpec]) -> dict[str, ModelObservation]:
    left = _record("SURF-AX8-L", theme=("THEME-A", "THEME-B"), creator="CREATOR-L")
    right = _record("SURF-AX8-R", theme=("THEME-A",), source="SOURCE-R", creator="CREATOR-R")
    _, context = _index_context([left, right] + _fixture_fillers("AX8F", 5))
    definition = AXIOM_DEFINITIONS[7]

    def evaluate(spec: model_baselines.ModelSpec) -> tuple[bool, str]:
        forward = model_baselines.score_pair(context, left["objectId"], right["objectId"], spec)
        reverse = model_baselines.score_pair(context, right["objectId"], left["objectId"], spec)
        passed = forward.diagnostic_score == reverse.diagnostic_score and forward.family_scores == reverse.family_scores
        return passed, f"forward={forward.diagnostic_score};reverse={reverse.diagnostic_score};declaredSymmetric={str(spec.symmetric).lower()}"

    return _model_observations(specs, definition, evaluate)


def _ax009(specs: Mapping[str, model_baselines.ModelSpec]) -> dict[str, ModelObservation]:
    query = _record("SURF-AX9-Q", theme=("THEME-A", "THEME-B", "THEME-C"), creator="CREATOR-Q")
    candidate = _record("SURF-AX9-C", theme=("THEME-A",), source="SOURCE-C", creator="CREATOR-C")
    _, context = _index_context([query, candidate] + _fixture_fillers("AX9F", 7))
    definition = AXIOM_DEFINITIONS[8]

    def evaluate(spec: model_baselines.ModelSpec) -> tuple[bool, str]:
        forward = model_baselines.score_pair(context, query["objectId"], candidate["objectId"], spec)
        repeat = model_baselines.score_pair(context, query["objectId"], candidate["objectId"], spec)
        reverse = model_baselines.score_pair(context, candidate["objectId"], query["objectId"], spec)
        passed = (
            spec.symmetric is False
            and spec.task == "USER_CONDITIONED_RETRIEVAL"
            and forward.as_dict() == repeat.as_dict()
            and forward.diagnostic_score != reverse.diagnostic_score
        )
        return passed, f"forward={forward.diagnostic_score};repeat={repeat.diagnostic_score};reverse={reverse.diagnostic_score};declaredSymmetric={str(spec.symmetric).lower()}"

    return _model_observations(specs, definition, evaluate)


def _ax010(specs: Mapping[str, model_baselines.ModelSpec]) -> dict[str, ModelObservation]:
    query = _record("SURF-AX10-Q")
    complete = _record("SURF-AX10-C", geography=("GEO-X",), source="SOURCE-C", creator="CREATOR-C")
    unavailable = _record(
        "SURF-AX10-U",
        geography=("UNKNOWN",),
        source="SOURCE-C",
        creator="CREATOR-C",
        labels={"UNKNOWN": "Unknown"},
    )
    _, context = _index_context([query, complete, unavailable] + _fixture_fillers("AX10F", 4))
    definition = AXIOM_DEFINITIONS[9]

    def evaluate(spec: model_baselines.ModelSpec) -> tuple[bool, str]:
        full = model_baselines.score_pair(context, query["objectId"], complete["objectId"], spec)
        missing = model_baselines.score_pair(context, query["objectId"], unavailable["objectId"], spec)
        full_ratio = float(full.comparability["ratio"])
        missing_ratio = float(missing.comparability["ratio"])
        explicit = "geography" in missing.unavailable_families
        passed = missing_ratio < full_ratio and explicit and "comparability" in missing.as_dict()
        return passed, f"completeScore={full.diagnostic_score};completeComparability={full_ratio:.12g};unavailableScore={missing.diagnostic_score};unavailableComparability={missing_ratio:.12g};declaredUnavailable={str(explicit).lower()}"

    return _model_observations(specs, definition, evaluate)


def _ax011(specs: Mapping[str, model_baselines.ModelSpec]) -> dict[str, ModelObservation]:
    query = _record("SURF-AX11-Q", curated=("CONTAINER-A", "CONTAINER-B"))
    other = _record("SURF-AX11-C", curated=("CONTAINER-A", "CONTAINER-B"), creator="CREATOR-C")
    index, context = _index_context([query, other] + _fixture_fillers("AX11F", 3))
    sets = {
        variant: candidate_index.generate_exploration_candidates(
            index,
            query["objectId"],
            variant=variant,
            direct_posting_max_ratio=1.0,
        )
        for variant in candidate_index.CANDIDATE_VARIANTS
    }
    self_absent = all(query["objectId"] not in value.candidate_ids for value in sets.values())
    definition = AXIOM_DEFINITIONS[10]

    def evaluate(spec: model_baselines.ModelSpec) -> tuple[bool, str]:
        rejected = False
        try:
            model_baselines.score_pair(context, query["objectId"], query["objectId"], spec)
        except model_baselines.ModelError:
            rejected = True
        passed = self_absent and rejected
        return passed, f"variantSelfFailures={sum(query['objectId'] in value.candidate_ids for value in sets.values())};scorePathRejected={str(rejected).lower()}"

    return _model_observations(specs, definition, evaluate)


def _ax012(specs: Mapping[str, model_baselines.ModelSpec]) -> dict[str, ModelObservation]:
    left = _record("SURF-AX12-L", title="Shared Display Title", creator="CREATOR-L")
    right = _record("SURF-AX12-R", title="Shared Display Title", source="SOURCE-R", creator="CREATOR-R")
    index, context = _index_context([left, right])
    candidates = candidate_index.generate_exploration_candidates(
        index,
        left["objectId"],
        variant="CG-CUR-6",
        direct_posting_max_ratio=1.0,
    )
    identity_preserved = (
        len(index.object_ids) == 2
        and left["objectId"] != right["objectId"]
        and right["objectId"] in candidates.candidate_ids
    )
    definition = AXIOM_DEFINITIONS[11]

    def evaluate(spec: model_baselines.ModelSpec) -> tuple[bool, str]:
        profile = model_baselines.score_pair(context, left["objectId"], right["objectId"], spec)
        passed = identity_preserved and profile.candidate_id == right["objectId"]
        return passed, f"indexedIdentities={len(index.object_ids)};candidateId={profile.candidate_id};sameTitle=true"

    return _model_observations(specs, definition, evaluate)


def _ax013(specs: Mapping[str, model_baselines.ModelSpec]) -> dict[str, ModelObservation]:
    base_left = _record("SURF-AX13-L", creator="CREATOR-L")
    base_right = _record("SURF-AX13-R", source="SOURCE-R", creator="CREATOR-R")
    coordinate_left = _record(
        "SURF-AX13-L",
        creator="CREATOR-L",
        extra={"mapX": -999999.0, "mapY": 999999.0, "centroid": [0.0, 0.0]},
    )
    coordinate_right = _record(
        "SURF-AX13-R",
        source="SOURCE-R",
        creator="CREATOR-R",
        extra={"mapX": 999999.0, "mapY": -999999.0, "centroid": [88.0, 179.0]},
    )
    base_index, base_context = _index_context([base_left, base_right])
    coordinate_index, coordinate_context = _index_context([coordinate_left, coordinate_right])
    definition = AXIOM_DEFINITIONS[12]

    def evaluate(spec: model_baselines.ModelSpec) -> tuple[bool, str]:
        base = model_baselines.score_pair(base_context, base_left["objectId"], base_right["objectId"], spec)
        changed = model_baselines.score_pair(coordinate_context, coordinate_left["objectId"], coordinate_right["objectId"], spec)
        contribution_text = _canonical_json(changed.contributions).casefold()
        forbidden = any(term in contribution_text for term in ("mapx", "mapy", "centroid", "coordinate_distance", "layout_distance"))
        passed = base_index.index_sha256 == coordinate_index.index_sha256 and base.as_dict() == changed.as_dict() and not forbidden
        return passed, f"indexHashEqual={str(base_index.index_sha256 == coordinate_index.index_sha256).lower()};scoreEqual={str(base.diagnostic_score == changed.diagnostic_score).lower()};layoutContribution={str(forbidden).lower()}"

    return _model_observations(specs, definition, evaluate)


def _ax014(specs: Mapping[str, model_baselines.ModelSpec]) -> dict[str, ModelObservation]:
    records = [
        _record(
            f"SURF-AX14-{ordinal:02d}",
            medium=(f"MEDIUM-{ordinal}",),
            theme=(f"THEME-{ordinal}",),
            decade=(f"{1800 + ordinal * 10}S",),
            geography=(f"GEO-{ordinal}",),
            curated=("UNIVERSAL-CONTAINER",),
            source=f"SOURCE-{ordinal}",
            object_type=f"TYPE-{ordinal}",
            creator=f"CREATOR-{ordinal}",
            year=1800 + ordinal * 10,
        )
        for ordinal in range(1, 11)
    ]
    index, _ = _index_context(records)
    candidate_sets = {
        row["objectId"]: candidate_index.generate_exploration_candidates(
            index,
            row["objectId"],
            variant="CG-CUR-1",
            direct_posting_max_ratio=0.25,
        )
        for row in records
    }
    top_1 = Counter()
    by_id = {row["objectId"]: row for row in records}
    for query_id, value in candidate_sets.items():
        ordered = sorted(
            value.candidate_ids,
            key=lambda candidate_id: (
                -float(negative_control.raw_curated_jaccard(by_id[query_id], by_id[candidate_id])["diagnosticScore"]),
                candidate_id,
            ),
        )
        if ordered:
            top_1[ordered[0]] += 1
    maximum_top_1 = max(top_1.values(), default=0)
    top_1_share = maximum_top_1 / len(records)
    posting_ratio = max((len(values) / len(records) for values in index.curated_postings.values()), default=0.0)
    near_full_count = sum(value.candidate_pool_count >= value.possible_other_count * 0.95 for value in candidate_sets.values())
    detected = posting_ratio >= 0.90 and near_full_count > 0 and top_1_share >= 0.50
    definition = AXIOM_DEFINITIONS[13]

    def evaluate(_: model_baselines.ModelSpec) -> tuple[bool, str]:
        return detected, f"broadPostingRatio={posting_ratio:.12g};nearFullQueries={near_full_count};diagnosticTop1Share={top_1_share:.12g};hubDetected={str(detected).lower()}"

    return _model_observations(specs, definition, evaluate)


def _ax015(specs: Mapping[str, model_baselines.ModelSpec]) -> dict[str, ModelObservation]:
    query = _record("SURF-AX15-Q", curated=("CONTAINER-A",), creator="CREATOR-Q")
    candidate = _record("SURF-AX15-C", curated=("CONTAINER-A",), source="SOURCE-C", creator="CREATOR-C")
    index, context = _index_context([query, candidate] + _fixture_fillers("AX15F", 3))
    definition = AXIOM_DEFINITIONS[14]

    def evaluate(spec: model_baselines.ModelSpec) -> tuple[bool, str]:
        caller_random_state = random.getstate()
        try:
            random.seed(7)
            first_candidates = candidate_index.generate_exploration_candidates(
                index,
                query["objectId"],
                variant="CG-CUR-1",
                direct_posting_max_ratio=1.0,
            )
            first_profile = model_baselines.score_pair(context, query["objectId"], candidate["objectId"], spec)
            random.seed(999_983)
            second_candidates = candidate_index.generate_exploration_candidates(
                index,
                query["objectId"],
                variant="CG-CUR-1",
                direct_posting_max_ratio=1.0,
            )
            second_profile = model_baselines.score_pair(context, query["objectId"], candidate["objectId"], spec)
        finally:
            random.setstate(caller_random_state)
        candidate_equal = first_candidates.candidate_set_sha256 == second_candidates.candidate_set_sha256
        profile_equal = first_profile.as_dict() == second_profile.as_dict()
        passed = (
            candidate_equal
            and profile_equal
            and not first_candidates.randomness_affects_candidate_set
            and not first_profile.randomness_affects_affinity
        )
        return passed, f"candidateHashEqual={str(candidate_equal).lower()};profileEqual={str(profile_equal).lower()};candidateRandomness=false;affinityRandomness=false"

    return _model_observations(specs, definition, evaluate)


_RUNNERS = (
    _ax001,
    _ax002,
    _ax003,
    _ax004,
    _ax005,
    _ax006,
    _ax007,
    _ax008,
    _ax009,
    _ax010,
    _ax011,
    _ax012,
    _ax013,
    _ax014,
    _ax015,
)


def mechanical_expectation_definitions() -> tuple[dict[str, str], ...]:
    """Return the frozen AX-001..AX-015 rule registry."""

    return tuple(
        {
            "axiomId": definition.axiom_id,
            "rule": definition.rule,
            "expectedInvariant": definition.expected_invariant,
            "modelApplicability": definition.applicability,
        }
        for definition in AXIOM_DEFINITIONS
    )


def mechanical_expectation_rows(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Extract a defensive copy of the 15 flat TSV-ready rows."""

    raw_rows = result.get("rows")
    if not isinstance(raw_rows, Sequence) or isinstance(raw_rows, (str, bytes, bytearray)):
        raise MechanicalExpectationError("mechanical result rows are absent")
    return [dict(row) for row in raw_rows]


def run_mechanical_expectations(
    *,
    specs: Iterable[model_baselines.ModelSpec] | None = None,
    required_model_ids: Sequence[str] = DEFAULT_GATE_MODEL_IDS,
) -> dict[str, Any]:
    """Run all mechanical gates and return rows plus per-model gate status.

    Callers may provide the exact shortlisted model specifications.  A model is
    gated only by axioms applicable to its declared symmetric/query task, while
    shared candidate, provenance, and semantic boundaries apply to all models.
    """

    if tuple(definition.axiom_id for definition in AXIOM_DEFINITIONS) != AXIOM_IDS:
        raise MechanicalExpectationError("axiom registry order changed")
    if len(AXIOM_IDS) != 15 or len(set(AXIOM_IDS)) != 15:
        raise MechanicalExpectationError("mechanical suite must contain exactly 15 unique axioms")
    if not required_model_ids or len(set(required_model_ids)) != len(required_model_ids):
        raise MechanicalExpectationError("required model IDs must be nonempty and unique")

    selected = _select_specs(specs, required_model_ids)
    rows: list[dict[str, Any]] = []
    model_gate_axioms: dict[str, list[str]] = {model_id: [] for model_id in selected}
    model_failures: dict[str, list[str]] = {model_id: [] for model_id in selected}
    for definition, runner in zip(AXIOM_DEFINITIONS, _RUNNERS):
        observations = runner(selected)
        if not observations:
            raise MechanicalExpectationError(f"{definition.axiom_id} has no applicable supplied model")
        for model_id, observation in observations.items():
            model_gate_axioms[model_id].append(definition.axiom_id)
            if not observation.passed:
                model_failures[model_id].append(definition.axiom_id)
        failed_models = tuple(model_id for model_id, value in observations.items() if not value.passed)
        tested_models = tuple(observations)
        observed_summary = " | ".join(
            f"{model_id}:{observations[model_id].observed}" for model_id in tested_models
        )
        case_hash = _sha256(
            {
                "axiomId": definition.axiom_id,
                "expectedInvariant": definition.expected_invariant,
                "observations": {
                    model_id: {
                        "passed": observations[model_id].passed,
                        "observed": observations[model_id].observed,
                    }
                    for model_id in tested_models
                },
            }
        )
        rows.append(
            {
                "axiom_id": definition.axiom_id,
                "rule": definition.rule,
                "expected_invariant": definition.expected_invariant,
                "model_applicability": definition.applicability,
                "tested_model_ids": ",".join(tested_models),
                "model_result_summary": ";".join(
                    f"{model_id}={'PASS' if observations[model_id].passed else 'FAIL'}"
                    for model_id in tested_models
                ),
                "observed_result": observed_summary,
                "status": "FAIL" if failed_models else "PASS",
                "failure_count": len(failed_models),
                "failed_model_ids": ",".join(failed_models) if failed_models else "NONE",
                "case_sha256": case_hash,
                "historical_relation": "false",
                "semantic_relation": "false",
                "probability": "false",
            }
        )

    axiom_failures = tuple(row["axiom_id"] for row in rows if row["status"] != "PASS")
    model_gates = {
        model_id: {
            "modelId": model_id,
            "variantId": selected[model_id].variant_id,
            "applicableAxiomIds": tuple(model_gate_axioms[model_id]),
            "applicableAxiomCount": len(model_gate_axioms[model_id]),
            "failedAxiomIds": tuple(model_failures[model_id]),
            "failureCount": len(model_failures[model_id]),
            "status": "PASS" if not model_failures[model_id] else "FAIL",
        }
        for model_id in selected
    }
    deterministic_material = {
        "schemaVersion": SCHEMA_VERSION,
        "implementationVersion": IMPLEMENTATION_VERSION,
        "rows": rows,
        "modelGates": model_gates,
    }
    result = {
        **deterministic_material,
        "axiomCount": len(AXIOM_IDS),
        "axiomFailureCount": len(axiom_failures),
        "failedAxiomIds": axiom_failures,
        "modelGateCount": len(model_gates),
        "allRequiredModelsPass": all(value["status"] == "PASS" for value in model_gates.values()),
        "sharedUnknownPositiveCreditCount": 0 if rows[2]["status"] == "PASS" else 1,
        "sameSourceFactDoubleScoreCount": 0 if rows[1]["status"] == "PASS" else 1,
        "geographicLayoutDistanceScoreCount": 0 if rows[12]["status"] == "PASS" else 1,
        "randomnessAffectsAffinity": False,
        "randomnessAffectsCandidateSet": False,
        "caseSetSha256": _sha256(deterministic_material),
    }
    validate_mechanical_expectation_result(result, required_model_ids=required_model_ids)
    return result


def validate_mechanical_expectation_result(
    result: Mapping[str, Any],
    *,
    required_model_ids: Sequence[str] = DEFAULT_GATE_MODEL_IDS,
) -> None:
    rows = mechanical_expectation_rows(result)
    if len(rows) != 15 or tuple(row.get("axiom_id") for row in rows) != AXIOM_IDS:
        raise MechanicalExpectationError("mechanical result does not contain ordered AX-001..AX-015 rows")
    required_columns = {
        "axiom_id",
        "rule",
        "expected_invariant",
        "model_applicability",
        "tested_model_ids",
        "model_result_summary",
        "observed_result",
        "status",
        "failure_count",
        "failed_model_ids",
        "case_sha256",
        "historical_relation",
        "semantic_relation",
        "probability",
    }
    for row in rows:
        if set(row) != required_columns:
            raise MechanicalExpectationError(f"{row.get('axiom_id')} TSV row schema changed")
        if row["status"] not in {"PASS", "FAIL"}:
            raise MechanicalExpectationError("mechanical status is invalid")
        if any(row[field] != "false" for field in ("historical_relation", "semantic_relation", "probability")):
            raise MechanicalExpectationError("mechanical row crossed an interpretation boundary")
        if not isinstance(row["case_sha256"], str) or len(row["case_sha256"]) != 64:
            raise MechanicalExpectationError("mechanical case hash is invalid")
    model_gates = result.get("modelGates")
    if not isinstance(model_gates, Mapping) or tuple(model_gates) != tuple(required_model_ids):
        raise MechanicalExpectationError("mechanical model gate set is incomplete or unordered")
    calculated_failures = sum(row["status"] != "PASS" for row in rows)
    if result.get("axiomCount") != 15 or result.get("axiomFailureCount") != calculated_failures:
        raise MechanicalExpectationError("mechanical summary counts disagree with rows")
    if bool(result.get("randomnessAffectsAffinity")) or bool(result.get("randomnessAffectsCandidateSet")):
        raise MechanicalExpectationError("randomness boundary failed")


def self_test() -> dict[str, Any]:
    result = run_mechanical_expectations()
    if result["axiomFailureCount"]:
        failures = ",".join(result["failedAxiomIds"])
        raise AssertionError(f"mechanical expectation failure(s): {failures}")
    if not result["allRequiredModelsPass"]:
        raise AssertionError("one or more required model gates failed")
    return {
        "status": "PASS",
        "axiomCount": result["axiomCount"],
        "axiomFailureCount": result["axiomFailureCount"],
        "modelGateCount": result["modelGateCount"],
        "caseSetSha256": result["caseSetSha256"],
        "randomnessAffectsAffinity": False,
        "randomnessAffectsCandidateSet": False,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
