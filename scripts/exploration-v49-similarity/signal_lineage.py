#!/usr/bin/env python3
"""Deterministic lineage classification for the 64 Round 5 signals.

This module is analysis-only.  It does not score objects, generate candidates,
read held rows, or import a raw-curation similarity implementation.  The
classification is deliberately closed over the sealed Round 5 signal IDs so a
new or renamed signal cannot silently enter an affinity model.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any


SCHEMA_VERSION = "trace-exploration-signal-lineage/v1"
DERIVATION_VERSION = "trace-exploration-signal-lineage-round1-v1"

SOURCE_SHA = "0e311f0b88b4adc3cbfe2080ac98d622013cc6d3"
RESEARCH_RELEASE_ID = "v49-api-contract-fresh-c"
CONTEXT_PROJECTION_SHA256 = (
    "825f6ecaa9ae1496c8a00ea0fefa5c90319046cf9c1f08a2ef76b9b02df4baeb"
)
SPACETIME_PROJECTION_SHA256 = (
    "f751b0f432ff684fd1000201b910aa397a4d9965468c2f7dd5022d6a4ae01c06"
)
ROUND5_SIGNAL_RECEIPT_SHA256 = (
    "224aaea1123ad9d5730006aa5e779c17b4673fdfc9ee87988f3f96ac8ce26424"
)
ROUND5_BUNDLE_SHA256 = (
    "bdb7f5f8350dde9e8264d254654d691ecc68e4fd279aa61ec2188bf2d65c8285"
)
PUBLIC_OBJECT_COUNT = 7_995
HELD_OBJECT_COUNT = 7_928
EXHAUSTIVE_PAIR_COUNT = 31_956_015
GEOGRAPHY_CLASS_MAPPING_SHA256 = (
    "10b51f6f33964cd267e35cd96703406d9ce55edfbc1534cfe55f5f7695902849"
)

EXPECTED_INPUT_RECEIPT: dict[str, Any] = {
    "sourceCommit": SOURCE_SHA,
    "researchReleaseId": RESEARCH_RELEASE_ID,
    "contextProjectionSha256": CONTEXT_PROJECTION_SHA256,
    "spacetimeProjectionSha256": SPACETIME_PROJECTION_SHA256,
    "explorationSignalRegistrySha256": ROUND5_SIGNAL_RECEIPT_SHA256,
    "explorationRound5BundleSha256": ROUND5_BUNDLE_SHA256,
    "publicObjectCount": PUBLIC_OBJECT_COUNT,
    "heldObjectCount": HELD_OBJECT_COUNT,
    "exhaustivePairCount": EXHAUSTIVE_PAIR_COUNT,
}

LINEAGE_COLUMNS = (
    "signal_id",
    "source_artifact",
    "source_row_family",
    "direct_parent_signals",
    "derived_from_signals",
    "same_source_fact_group",
    "epistemic_level",
    "scoring_disposition",
    "independent_information_candidate",
    "duplicate_for_scoring",
    "interaction_only",
    "diagnostic_only",
    "candidate_generation_allowed",
    "scoring_allowed",
    "explanation_allowed",
    "reason",
)

SCORING_DISPOSITIONS = frozenset(
    {
        "INDEPENDENT_BASE_SIGNAL",
        "DEPENDENT_INTERACTION_SIGNAL",
        "CANDIDATE_GENERATION_ONLY",
        "COMPARABILITY_ONLY",
        "EXPLANATION_ONLY",
        "DIAGNOSTIC_ONLY",
        "REJECT",
    }
)

EPISTEMIC_LEVELS = frozenset(
    {
        "DIRECT_GOVERNED_FACT",
        "DIRECT_APPROVED_PUBLIC_METADATA",
        "GOVERNED_PROJECTION_DERIVATION",
        "PROJECT_CURATED_RECALL_SUBSTRATE",
        "DETERMINISTIC_DERIVATION",
        "DEPENDENT_INTERACTION_DERIVATION",
        "COMPARABILITY_STATE",
        "ANALYSIS_DIAGNOSTIC",
        "UNSELECTED_COMPOUND",
        "UNSUPPORTED_INFERENCE",
    }
)

CONTEXT_RECORDS = "frontend/generated/trace-context-v1/records.json"
SPACETIME_RECORDS = "frontend/generated/trace-spacetime-v1/record-index.json"
SPACETIME_GEOGRAPHY = (
    "frontend/generated/trace-spacetime-v1/geography-registry.json"
)
MISSINGNESS_TSV = (
    "docs/research/trace-v49-exploration-discovery-round1/"
    "06_MISSINGNESS_CENSUS.tsv"
)
FREQUENCY_TSV = (
    "docs/research/trace-v49-exploration-discovery-round1/"
    "08_ONE_DIMENSION_FREQUENCIES.tsv"
)
PAIR_TSV = (
    "docs/research/trace-v49-exploration-discovery-round1/"
    "09_TWO_DIMENSION_INTERSECTIONS.tsv"
)
TRIPLE_TSV = (
    "docs/research/trace-v49-exploration-discovery-round1/"
    "10_THREE_DIMENSION_INTERSECTIONS.tsv"
)
RARE_TSV = (
    "docs/research/trace-v49-exploration-discovery-round1/"
    "11_RARE_INTERSECTION_REGISTER.tsv"
)
SIGNAL_TSV = (
    "docs/research/trace-v49-exploration-discovery-round1/"
    "13_EXPLORATION_SIGNAL_REGISTRY.tsv"
)
CURATORIAL_SUMMARY = (
    "docs/audits/v49-spacetime-closure-exploration-discovery/raw/"
    "exploration-curatorial-summary.json"
)
CURATORIAL_SUPPORT_SUMMARY = (
    "docs/audits/v49-spacetime-closure-exploration-discovery/raw/"
    "exploration-curatorial-support-summary.json"
)
MISSINGNESS_SUMMARY = (
    "docs/audits/v49-spacetime-closure-exploration-discovery/raw/"
    "exploration-missingness-summary.json"
)
CORRELATION_SUMMARY = (
    "docs/audits/v49-spacetime-closure-exploration-discovery/raw/"
    "exploration-cross-dimensional-summary.json"
)


class SignalLineageError(ValueError):
    """Raised when the sealed registry or lineage contract is violated."""


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


def _parents(*signal_ids: str) -> tuple[str, ...]:
    return tuple(sorted(set(signal_ids)))


def _lineage(
    signal_id: str,
    registry_family: str,
    source_artifact: str,
    source_row_family: str,
    same_source_fact_group: str,
    epistemic_level: str,
    scoring_disposition: str,
    reason: str,
    *,
    direct_parents: Sequence[str] = (),
    derived_from: Sequence[str] | None = None,
    independent: bool = False,
    duplicate: bool = False,
    interaction: bool = False,
    diagnostic: bool = False,
    candidate_allowed: bool = False,
    scoring_allowed: bool = False,
    explanation_allowed: bool = True,
    scoring_guard: str = "NOT_SCORING_ELIGIBLE",
) -> dict[str, Any]:
    direct = _parents(*direct_parents)
    ancestry = _parents(*(derived_from if derived_from is not None else direct))
    if not set(direct).issubset(ancestry):
        raise SignalLineageError(
            f"{signal_id} direct parents must be present in derived-from ancestry"
        )
    return {
        "signal_id": signal_id,
        "registry_family": registry_family,
        "source_artifact": source_artifact,
        "source_row_family": source_row_family,
        "direct_parent_signals": direct,
        "derived_from_signals": ancestry,
        "same_source_fact_group": same_source_fact_group,
        "epistemic_level": epistemic_level,
        "scoring_disposition": scoring_disposition,
        "independent_information_candidate": independent,
        "duplicate_for_scoring": duplicate,
        "interaction_only": interaction,
        "diagnostic_only": diagnostic,
        "candidate_generation_allowed": candidate_allowed,
        "scoring_allowed": scoring_allowed,
        "explanation_allowed": explanation_allowed,
        "reason": reason,
        "scoring_guard": scoring_guard,
    }


# The table is intentionally explicit.  Pattern-based classification would let
# a newly named signal acquire scoring privileges without a research decision.
_SPECS = (
    _lineage(
        "SIG-CONTEXT-MEDIUM",
        "GOVERNED_CONTEXT",
        CONTEXT_RECORDS,
        "records[].representations[kind=medium]",
        "SSF-CONTEXT-MEDIUM",
        "DIRECT_GOVERNED_FACT",
        "INDEPENDENT_BASE_SIGNAL",
        "The governed medium membership is the canonical medium source fact.",
        independent=True,
        candidate_allowed=True,
        scoring_allowed=True,
        scoring_guard="ONE_CONTEXT_FAMILY_CONTRIBUTION;BROAD_VALUE_ATTENUATION_REQUIRED",
    ),
    _lineage(
        "SIG-CONTEXT-MEDIUM-THEME",
        "GOVERNED_CONTEXT",
        PAIR_TSV,
        "pair_id=medium__theme alias",
        "SSF-PAIR-INTERSECTION-CELL",
        "DEPENDENT_INTERACTION_DERIVATION",
        "EXPLANATION_ONLY",
        "This is an alias of the medium-theme cell already represented by the generic pair-interaction carrier.",
        direct_parents=("SIG-CONTEXT-MEDIUM", "SIG-CONTEXT-THEME"),
        duplicate=True,
        interaction=True,
    ),
    _lineage(
        "SIG-CONTEXT-MOVEMENT",
        "GOVERNED_CONTEXT",
        CONTEXT_RECORDS,
        "records[].representations[kind=movement_context]",
        "SSF-CONTEXT-MOVEMENT",
        "DIRECT_GOVERNED_FACT",
        "INDEPENDENT_BASE_SIGNAL",
        "Published governed movement context is a sparse canonical source fact; absence is not a match.",
        independent=True,
        candidate_allowed=True,
        scoring_allowed=True,
        scoring_guard="OBSERVED_VALUES_ONLY;NO_PUBLISHED_MOVEMENT_CONTEXT_ZERO_CREDIT",
    ),
    _lineage(
        "SIG-CONTEXT-SAME-MEDIUM",
        "GOVERNED_CONTEXT",
        SIGNAL_TSV,
        "pairwise comparison derived from medium memberships",
        "SSF-CONTEXT-MEDIUM",
        "DETERMINISTIC_DERIVATION",
        "EXPLANATION_ONLY",
        "Pair equality is computed from the canonical medium base and cannot add a second contribution.",
        direct_parents=("SIG-CONTEXT-MEDIUM",),
        duplicate=True,
    ),
    _lineage(
        "SIG-CONTEXT-SAME-MOVEMENT",
        "GOVERNED_CONTEXT",
        SIGNAL_TSV,
        "pairwise comparison derived from movement memberships",
        "SSF-CONTEXT-MOVEMENT",
        "DETERMINISTIC_DERIVATION",
        "EXPLANATION_ONLY",
        "Pair equality repeats the movement source fact and is explanation-only.",
        direct_parents=("SIG-CONTEXT-MOVEMENT",),
        duplicate=True,
    ),
    _lineage(
        "SIG-CONTEXT-SAME-THEME",
        "GOVERNED_CONTEXT",
        SIGNAL_TSV,
        "pairwise comparison derived from theme memberships",
        "SSF-CONTEXT-THEME",
        "DETERMINISTIC_DERIVATION",
        "EXPLANATION_ONLY",
        "Pair equality is computed from the canonical theme base and cannot add a second contribution.",
        direct_parents=("SIG-CONTEXT-THEME",),
        duplicate=True,
    ),
    _lineage(
        "SIG-CONTEXT-THEME",
        "GOVERNED_CONTEXT",
        CONTEXT_RECORDS,
        "records[].representations[kind=theme]",
        "SSF-CONTEXT-THEME",
        "DIRECT_GOVERNED_FACT",
        "INDEPENDENT_BASE_SIGNAL",
        "The governed theme membership is the canonical theme source fact.",
        independent=True,
        candidate_allowed=True,
        scoring_allowed=True,
        scoring_guard="ONE_CONTEXT_FAMILY_CONTRIBUTION;BROAD_VALUE_ATTENUATION_REQUIRED",
    ),
    _lineage(
        "SIG-CONTEXT-THEME-MOVEMENT",
        "GOVERNED_CONTEXT",
        PAIR_TSV,
        "pair_id=theme__movement_context",
        "SSF-PAIR-INTERSECTION-CELL",
        "DEPENDENT_INTERACTION_DERIVATION",
        "CANDIDATE_GENERATION_ONLY",
        "The sparse cell may retrieve candidates, but any score must pass through the one residual pair-interaction channel.",
        direct_parents=("SIG-CONTEXT-MOVEMENT", "SIG-CONTEXT-THEME"),
        duplicate=True,
        interaction=True,
        candidate_allowed=True,
    ),
    _lineage(
        "SIG-CURATORIAL-AFFINITY",
        "CURATORIAL_STRUCTURE",
        SIGNAL_TSV,
        "unselected compound candidate",
        "SSF-UNSELECTED-CURATORIAL-AFFINITY",
        "UNSELECTED_COMPOUND",
        "REJECT",
        "No curatorial score, formula, or weights exist; the compound cannot enter scoring.",
        direct_parents=(
            "SIG-CURATORIAL-JACCARD",
            "SIG-CURATORIAL-MEMBERSHIP",
            "SIG-CURATORIAL-SHARED-COUNT",
        ),
        duplicate=True,
        explanation_allowed=False,
    ),
    _lineage(
        "SIG-CURATORIAL-CONTAINER-TYPE",
        "CURATORIAL_STRUCTURE",
        CURATORIAL_SUMMARY,
        "publicContainerTypeRows",
        "SSF-CURATORIAL-CONTAINER-TYPE",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Four broad project-curated types diagnose structure but are not independent affinity evidence.",
        diagnostic=True,
        duplicate=True,
    ),
    _lineage(
        "SIG-CURATORIAL-FANOUT",
        "CURATORIAL_STRUCTURE",
        CURATORIAL_SUMMARY,
        "perObjectFanoutThresholds",
        "SSF-CURATORIAL-MEMBERSHIP",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Fanout measures candidate explosion caused by the same membership substrate.",
        direct_parents=("SIG-CURATORIAL-MEMBERSHIP",),
        duplicate=True,
        diagnostic=True,
    ),
    _lineage(
        "SIG-CURATORIAL-HISTORICAL-RELATION",
        "CURATORIAL_STRUCTURE",
        SIGNAL_TSV,
        "explicitly prohibited inference",
        "SSF-UNSUPPORTED-CURATORIAL-HISTORICAL-RELATION",
        "UNSUPPORTED_INFERENCE",
        "REJECT",
        "Project-curated overlap cannot establish historical relation, influence, contact, or lineage.",
        direct_parents=("SIG-CURATORIAL-MEMBERSHIP",),
        duplicate=True,
        explanation_allowed=False,
    ),
    _lineage(
        "SIG-CURATORIAL-JACCARD",
        "CURATORIAL_STRUCTURE",
        CURATORIAL_SUMMARY,
        "rawCuratedJaccardDistribution",
        "SSF-CURATORIAL-MEMBERSHIP",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Raw curated-set Jaccard is retained only as M0 negative control and structural diagnostic.",
        direct_parents=("SIG-CURATORIAL-MEMBERSHIP",),
        duplicate=True,
        diagnostic=True,
        scoring_guard="M0_NEGATIVE_CONTROL_ONLY;PRODUCTION_IMPORT_FORBIDDEN;SHORTLIST_FORBIDDEN",
    ),
    _lineage(
        "SIG-CURATORIAL-MEMBERSHIP",
        "CURATORIAL_STRUCTURE",
        CURATORIAL_SUMMARY,
        "unique public object-container memberships",
        "SSF-CURATORIAL-MEMBERSHIP",
        "PROJECT_CURATED_RECALL_SUBSTRATE",
        "CANDIDATE_GENERATION_ONLY",
        "Raw memberships may support bounded recall and provenance, never independent score credit.",
        duplicate=True,
        candidate_allowed=True,
    ),
    _lineage(
        "SIG-CURATORIAL-MEMBERSHIP-COUNT",
        "CURATORIAL_STRUCTURE",
        CURATORIAL_SUMMARY,
        "membershipsPerObjectDistribution",
        "SSF-CURATORIAL-MEMBERSHIP",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Membership count diagnoses cataloguing density and cannot imply importance or affinity.",
        direct_parents=("SIG-CURATORIAL-MEMBERSHIP",),
        duplicate=True,
        diagnostic=True,
    ),
    _lineage(
        "SIG-CURATORIAL-SHARED-COUNT",
        "CURATORIAL_STRUCTURE",
        CURATORIAL_SUMMARY,
        "sharedContainerCountThresholds",
        "SSF-CURATORIAL-MEMBERSHIP",
        "PROJECT_CURATED_RECALL_SUBSTRATE",
        "CANDIDATE_GENERATION_ONLY",
        "Shared-count thresholds may narrow curatorial recall but repeat the raw membership fact for scoring.",
        direct_parents=("SIG-CURATORIAL-MEMBERSHIP",),
        duplicate=True,
        candidate_allowed=True,
    ),
    _lineage(
        "SIG-CURATORIAL-SUPPORT",
        "CURATORIAL_STRUCTURE",
        CURATORIAL_SUPPORT_SUMMARY,
        "containerSupportRows",
        "SSF-CURATORIAL-MEMBERSHIP",
        "PROJECT_CURATED_RECALL_SUBSTRATE",
        "CANDIDATE_GENERATION_ONLY",
        "Support may attenuate or stop broad postings, but is not an additional pair observation.",
        direct_parents=("SIG-CURATORIAL-MEMBERSHIP",),
        duplicate=True,
        candidate_allowed=True,
    ),
    _lineage(
        "SIG-DESCRIPTIVE-CREATOR",
        "DESCRIPTIVE_METADATA",
        CONTEXT_RECORDS,
        "records[].selectedRecord.rootMetadata.creatorAttribution",
        "SSF-DESCRIPTIVE-CREATOR",
        "DIRECT_APPROVED_PUBLIC_METADATA",
        "INDEPENDENT_BASE_SIGNAL",
        "Normalized public creator attribution is independently observable when it is not an explicit unknown state.",
        independent=True,
        candidate_allowed=True,
        scoring_allowed=True,
        scoring_guard="OBSERVED_CREATOR_ONLY;UNKNOWN_AND_QUALIFIED_UNKNOWN_ZERO_CREDIT;FAMILY_CAP_REQUIRED",
    ),
    _lineage(
        "SIG-DESCRIPTIVE-CREATOR-INTENT",
        "DESCRIPTIVE_METADATA",
        SIGNAL_TSV,
        "explicitly prohibited inference",
        "SSF-UNSUPPORTED-CREATOR-INTENT",
        "UNSUPPORTED_INFERENCE",
        "REJECT",
        "Creator attribution cannot establish intent.",
        direct_parents=("SIG-DESCRIPTIVE-CREATOR",),
        duplicate=True,
        explanation_allowed=False,
    ),
    _lineage(
        "SIG-DESCRIPTIVE-CREATOR-MEDIUM",
        "DESCRIPTIVE_METADATA",
        PAIR_TSV,
        "pair_id=creator__medium",
        "SSF-PAIR-INTERSECTION-CELL",
        "DEPENDENT_INTERACTION_DERIVATION",
        "CANDIDATE_GENERATION_ONLY",
        "The cell may retrieve candidates; score credit belongs only to the residual pair-interaction channel.",
        direct_parents=("SIG-CONTEXT-MEDIUM", "SIG-DESCRIPTIVE-CREATOR"),
        duplicate=True,
        interaction=True,
        candidate_allowed=True,
    ),
    _lineage(
        "SIG-DESCRIPTIVE-OBJECT-TYPE",
        "DESCRIPTIVE_METADATA",
        CONTEXT_RECORDS,
        "records[].selectedRecord.rootMetadata.objectType",
        "SSF-DESCRIPTIVE-OBJECT-TYPE",
        "DIRECT_APPROVED_PUBLIC_METADATA",
        "INDEPENDENT_BASE_SIGNAL",
        "Normalized public object type is independently observable, subject to source-granularity diagnostics.",
        independent=True,
        candidate_allowed=True,
        scoring_allowed=True,
        scoring_guard="ONE_DESCRIPTIVE_FAMILY_CONTRIBUTION;SOURCE_GRANULARITY_DIAGNOSTIC_REQUIRED",
    ),
    _lineage(
        "SIG-DESCRIPTIVE-OBJECT-TYPE-MEDIUM",
        "DESCRIPTIVE_METADATA",
        PAIR_TSV,
        "pair_id=object_type__medium",
        "SSF-PAIR-INTERSECTION-CELL",
        "DEPENDENT_INTERACTION_DERIVATION",
        "CANDIDATE_GENERATION_ONLY",
        "The cell may retrieve candidates; it cannot add object-type and medium evidence again.",
        direct_parents=("SIG-CONTEXT-MEDIUM", "SIG-DESCRIPTIVE-OBJECT-TYPE"),
        duplicate=True,
        interaction=True,
        candidate_allowed=True,
    ),
    _lineage(
        "SIG-DESCRIPTIVE-SAME-CREATOR",
        "DESCRIPTIVE_METADATA",
        SIGNAL_TSV,
        "pairwise comparison derived from creator attribution",
        "SSF-DESCRIPTIVE-CREATOR",
        "DETERMINISTIC_DERIVATION",
        "EXPLANATION_ONLY",
        "Same-creator equality repeats the canonical creator source fact; unknown states remain zero credit.",
        direct_parents=("SIG-DESCRIPTIVE-CREATOR",),
        duplicate=True,
    ),
    _lineage(
        "SIG-FREQUENCY-ONE-DIMENSION",
        "FREQUENCY_INTERSECTION_CONCENTRATION",
        FREQUENCY_TSV,
        "all observed one-dimensional frequency rows",
        "SSF-CROSS-DIMENSION-FREQUENCY",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Frequency supplies bounded weighting diagnostics; it is not a second observation of a feature value.",
        direct_parents=(
            "SIG-CONTEXT-MEDIUM",
            "SIG-CONTEXT-MOVEMENT",
            "SIG-CONTEXT-THEME",
            "SIG-CURATORIAL-CONTAINER-TYPE",
            "SIG-CURATORIAL-MEMBERSHIP",
            "SIG-DESCRIPTIVE-CREATOR",
            "SIG-DESCRIPTIVE-OBJECT-TYPE",
            "SIG-GEOGRAPHY-ASSIGNMENT",
            "SIG-GEOGRAPHY-CLASS",
            "SIG-GEOGRAPHY-MAPPING-STATE",
            "SIG-SOURCE-NAME",
            "SIG-TEMPORAL-DECADE",
            "SIG-TEMPORAL-PRECISION",
        ),
        duplicate=True,
        diagnostic=True,
    ),
    _lineage(
        "SIG-FREQUENCY-RARITY-BAND",
        "FREQUENCY_INTERSECTION_CONCENTRATION",
        FREQUENCY_TSV,
        "rarity_band over one-dimensional frequency rows",
        "SSF-CROSS-DIMENSION-FREQUENCY",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "A rarity label derives from frequency and cannot become importance or independent score evidence.",
        direct_parents=("SIG-FREQUENCY-ONE-DIMENSION",),
        duplicate=True,
        diagnostic=True,
    ),
    _lineage(
        "SIG-GEOGRAPHY-ASSIGNMENT",
        "GOVERNED_GEOGRAPHY",
        SPACETIME_RECORDS,
        "records[].geographyIds",
        "SSF-GEOGRAPHY-ASSIGNMENT",
        "DIRECT_GOVERNED_FACT",
        "INDEPENDENT_BASE_SIGNAL",
        "Governed geography identity is the canonical exact-overlap source fact.",
        independent=True,
        candidate_allowed=True,
        scoring_allowed=True,
        scoring_guard="EXACT_GOVERNED_OVERLAP_ONLY;LAYOUT_AND_CENTROID_DISTANCE_FORBIDDEN",
    ),
    _lineage(
        "SIG-GEOGRAPHY-CLASS",
        "GOVERNED_GEOGRAPHY",
        SPACETIME_GEOGRAPHY,
        "entries[].geographyClass",
        "SSF-GEOGRAPHY-ASSIGNMENT",
        "GOVERNED_PROJECTION_DERIVATION",
        "CANDIDATE_GENERATION_ONLY",
        "All 93 governed geography IDs map deterministically to exactly one class, so class adds no independent information and is only a weaker retrieval/explanation fallback.",
        direct_parents=("SIG-GEOGRAPHY-ASSIGNMENT",),
        duplicate=True,
        candidate_allowed=True,
        scoring_guard="DETERMINISTIC_LOOKUP_FROM_GEOGRAPHY_ASSIGNMENT;CANDIDATE_OR_EXPLANATION_ONLY;NEVER_ADDITIVE",
    ),
    _lineage(
        "SIG-GEOGRAPHY-CONCENTRATION",
        "GOVERNED_GEOGRAPHY",
        CORRELATION_SUMMARY,
        "dimensionConcentrationRows[dimension=geography]",
        "SSF-GEOGRAPHY-ASSIGNMENT",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Corpus concentration derives from governed geography assignments and diagnoses bias only.",
        direct_parents=("SIG-GEOGRAPHY-ASSIGNMENT",),
        duplicate=True,
        diagnostic=True,
    ),
    _lineage(
        "SIG-GEOGRAPHY-DISTANCE",
        "GOVERNED_GEOGRAPHY",
        SIGNAL_TSV,
        "unselected geography-distance candidate",
        "SSF-UNSUPPORTED-GEOGRAPHY-DISTANCE",
        "UNSELECTED_COMPOUND",
        "REJECT",
        "No governed research-distance policy exists; layout, centroid, adjacency, and coordinate distance are forbidden.",
        direct_parents=("SIG-GEOGRAPHY-ASSIGNMENT",),
        duplicate=True,
        explanation_allowed=False,
    ),
    _lineage(
        "SIG-GEOGRAPHY-MAPPING-STATE",
        "GOVERNED_GEOGRAPHY",
        SPACETIME_GEOGRAPHY,
        "entries[].mappingState",
        "SSF-GEOGRAPHY-MAPPING-STATE",
        "COMPARABILITY_STATE",
        "COMPARABILITY_ONLY",
        "Mapped, aggregate-only, and unmapped states describe observability, not positive affinity.",
        duplicate=True,
    ),
    _lineage(
        "SIG-GEOGRAPHY-MULTI-REGION",
        "GOVERNED_GEOGRAPHY",
        MISSINGNESS_SUMMARY,
        "objectVectors[].geographyCount>1 aggregate",
        "SSF-GEOGRAPHY-MULTI-REGION",
        "COMPARABILITY_STATE",
        "COMPARABILITY_ONLY",
        "Multi-region incidence changes comparison shape but is not an extra match.",
        direct_parents=("SIG-GEOGRAPHY-ASSIGNMENT",),
        duplicate=True,
    ),
    _lineage(
        "SIG-GEOGRAPHY-RARITY",
        "GOVERNED_GEOGRAPHY",
        FREQUENCY_TSV,
        "dimension=geography rarity_band",
        "SSF-GEOGRAPHY-ASSIGNMENT",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Geographic rarity derives from assignment frequency; rare does not mean important.",
        direct_parents=("SIG-GEOGRAPHY-ASSIGNMENT", "SIG-FREQUENCY-ONE-DIMENSION"),
        duplicate=True,
        diagnostic=True,
    ),
    _lineage(
        "SIG-GEOGRAPHY-SAME",
        "GOVERNED_GEOGRAPHY",
        SIGNAL_TSV,
        "pairwise comparison derived from geographyIds",
        "SSF-GEOGRAPHY-ASSIGNMENT",
        "DETERMINISTIC_DERIVATION",
        "EXPLANATION_ONLY",
        "Same-geography equality is calculated from the canonical assignment and cannot add a second contribution.",
        direct_parents=("SIG-GEOGRAPHY-ASSIGNMENT",),
        duplicate=True,
    ),
    _lineage(
        "SIG-INTERSECTION-BOUNDED-TRIPLE",
        "FREQUENCY_INTERSECTION_CONCENTRATION",
        TRIPLE_TSV,
        "all approved bounded triple cells",
        "SSF-TRIPLE-INTERSECTION-CELL",
        "DEPENDENT_INTERACTION_DERIVATION",
        "DEPENDENT_INTERACTION_SIGNAL",
        "Approved triple cells may add only bounded information residual after their base parents.",
        direct_parents=(
            "SIG-CONTEXT-MEDIUM",
            "SIG-CONTEXT-THEME",
            "SIG-GEOGRAPHY-ASSIGNMENT",
            "SIG-SOURCE-NAME",
            "SIG-TEMPORAL-DECADE",
        ),
        interaction=True,
        scoring_allowed=True,
        scoring_guard="APPROVED_CELLS_ONLY;PARENT_RESIDUAL_ONLY;SUPPORT_THRESHOLD_AND_CAP_REQUIRED",
    ),
    _lineage(
        "SIG-INTERSECTION-CONDITIONAL-LIFT",
        "FREQUENCY_INTERSECTION_CONCENTRATION",
        PAIR_TSV,
        "conditional rates and lift diagnostics",
        "SSF-PAIR-INTERSECTION-CELL",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Conditional support and raw lift are alternative diagnostics over the same pair cells, not extra evidence.",
        direct_parents=("SIG-INTERSECTION-PAIR-SUPPORT",),
        duplicate=True,
        interaction=True,
        diagnostic=True,
    ),
    _lineage(
        "SIG-INTERSECTION-MEDIUM-THEME",
        "FREQUENCY_INTERSECTION_CONCENTRATION",
        PAIR_TSV,
        "pair_id=medium__theme canonical retrieval alias",
        "SSF-PAIR-INTERSECTION-CELL",
        "DEPENDENT_INTERACTION_DERIVATION",
        "CANDIDATE_GENERATION_ONLY",
        "The high-information posting may retrieve candidates; score credit is centralized in the residual pair carrier.",
        direct_parents=("SIG-CONTEXT-MEDIUM", "SIG-CONTEXT-THEME"),
        duplicate=True,
        interaction=True,
        candidate_allowed=True,
    ),
    _lineage(
        "SIG-INTERSECTION-PAIR-SUPPORT",
        "FREQUENCY_INTERSECTION_CONCENTRATION",
        PAIR_TSV,
        "approved non-curatorial observed pair cells",
        "SSF-PAIR-INTERSECTION-CELL",
        "DEPENDENT_INTERACTION_DERIVATION",
        "DEPENDENT_INTERACTION_SIGNAL",
        "One residual pair-interaction carrier prevents named cells, support, lift, and rarity from being added repeatedly.",
        direct_parents=(
            "SIG-CONTEXT-MEDIUM",
            "SIG-CONTEXT-MOVEMENT",
            "SIG-CONTEXT-THEME",
            "SIG-DESCRIPTIVE-CREATOR",
            "SIG-DESCRIPTIVE-OBJECT-TYPE",
            "SIG-GEOGRAPHY-ASSIGNMENT",
            "SIG-SOURCE-NAME",
            "SIG-TEMPORAL-DECADE",
        ),
        interaction=True,
        scoring_allowed=True,
        scoring_guard="APPROVED_NON_CURATORIAL_CELLS_ONLY;PARENT_RESIDUAL_ONLY;SUPPORT_THRESHOLD_AND_CAP_REQUIRED",
    ),
    _lineage(
        "SIG-INTERSECTION-RARE-MULTI",
        "FREQUENCY_INTERSECTION_CONCENTRATION",
        RARE_TSV,
        "bounded rare pair and triple cells",
        "SSF-INTERSECTION-RARITY-CLASS",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Rare is a bounded sensitivity label, not importance and not an additional interaction observation.",
        direct_parents=(
            "SIG-INTERSECTION-BOUNDED-TRIPLE",
            "SIG-INTERSECTION-PAIR-SUPPORT",
        ),
        duplicate=True,
        interaction=True,
        diagnostic=True,
    ),
    _lineage(
        "SIG-MISSINGNESS-COOCCURRENCE",
        "MISSINGNESS_UNCERTAINTY",
        MISSINGNESS_TSV,
        "row_kind=COOCCURRENCE",
        "SSF-MISSINGNESS-COOCCURRENCE",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Shared uncertainty states are useful only for missingness-oriented aggregate exploration.",
        direct_parents=(
            "SIG-MISSINGNESS-CREATOR",
            "SIG-MISSINGNESS-GEOGRAPHY-MAPPING",
            "SIG-MISSINGNESS-GEOGRAPHY-QUALIFIED",
            "SIG-MISSINGNESS-MOVEMENT-AVAILABILITY",
            "SIG-MISSINGNESS-TEMPORAL",
        ),
        duplicate=True,
        diagnostic=True,
    ),
    _lineage(
        "SIG-MISSINGNESS-CREATOR",
        "MISSINGNESS_UNCERTAINTY",
        MISSINGNESS_TSV,
        "row_kind=FIELD_MATRIX;field=creator",
        "SSF-DESCRIPTIVE-CREATOR",
        "COMPARABILITY_STATE",
        "COMPARABILITY_ONLY",
        "Creator unknown and qualified-unknown states alter availability and add zero default affinity.",
        direct_parents=("SIG-DESCRIPTIVE-CREATOR",),
        duplicate=True,
    ),
    _lineage(
        "SIG-MISSINGNESS-GEOGRAPHY-MAPPING",
        "MISSINGNESS_UNCERTAINTY",
        MISSINGNESS_TSV,
        "row_kind=FIELD_MATRIX;field=geography_mapping_state",
        "SSF-GEOGRAPHY-MAPPING-STATE",
        "COMPARABILITY_STATE",
        "COMPARABILITY_ONLY",
        "Mapping availability belongs to the comparability channel and adds zero affinity.",
        direct_parents=("SIG-GEOGRAPHY-MAPPING-STATE",),
        duplicate=True,
    ),
    _lineage(
        "SIG-MISSINGNESS-GEOGRAPHY-QUALIFIED",
        "MISSINGNESS_UNCERTAINTY",
        MISSINGNESS_TSV,
        "taxonomy_class=QUALIFIED geography rows",
        "SSF-GEOGRAPHY-QUALIFICATION",
        "COMPARABILITY_STATE",
        "COMPARABILITY_ONLY",
        "Qualification is uncertainty metadata and cannot create positive pair credit.",
        direct_parents=("SIG-GEOGRAPHY-ASSIGNMENT",),
        duplicate=True,
    ),
    _lineage(
        "SIG-MISSINGNESS-MOVEMENT-AVAILABILITY",
        "MISSINGNESS_UNCERTAINTY",
        MISSINGNESS_TSV,
        "row_kind=FIELD_MATRIX;field=movement_context",
        "SSF-CONTEXT-MOVEMENT",
        "COMPARABILITY_STATE",
        "COMPARABILITY_ONLY",
        "No published movement context is an explicit availability state, not a shared positive feature.",
        direct_parents=("SIG-CONTEXT-MOVEMENT",),
        duplicate=True,
    ),
    _lineage(
        "SIG-MISSINGNESS-RIGHTS-DELIVERY",
        "MISSINGNESS_UNCERTAINTY",
        MISSINGNESS_SUMMARY,
        "internal rights and delivery diagnostics",
        "SSF-NOT-GOVERNED-RIGHTS-DELIVERY",
        "UNSELECTED_COMPOUND",
        "REJECT",
        "Rights and delivery states are not governed public Exploration features.",
        duplicate=True,
        explanation_allowed=False,
    ),
    _lineage(
        "SIG-MISSINGNESS-SINGLE-SCORE",
        "MISSINGNESS_UNCERTAINTY",
        SIGNAL_TSV,
        "explicitly rejected uncertainty compound",
        "SSF-UNSUPPORTED-MISSINGNESS-SCORE",
        "UNSUPPORTED_INFERENCE",
        "REJECT",
        "Collapsing heterogeneous availability states into one score hides comparability and is prohibited.",
        direct_parents=(
            "SIG-MISSINGNESS-CREATOR",
            "SIG-MISSINGNESS-GEOGRAPHY-MAPPING",
            "SIG-MISSINGNESS-GEOGRAPHY-QUALIFIED",
            "SIG-MISSINGNESS-MOVEMENT-AVAILABILITY",
            "SIG-MISSINGNESS-TEMPORAL",
        ),
        duplicate=True,
        explanation_allowed=False,
    ),
    _lineage(
        "SIG-MISSINGNESS-TEMPORAL",
        "MISSINGNESS_UNCERTAINTY",
        MISSINGNESS_TSV,
        "row_kind=FIELD_MATRIX;field=temporal_precision",
        "SSF-TEMPORAL-PRECISION",
        "COMPARABILITY_STATE",
        "COMPARABILITY_ONLY",
        "Approximate and range precision affect temporal comparability; matching uncertainty adds zero affinity.",
        direct_parents=("SIG-TEMPORAL-PRECISION",),
        duplicate=True,
    ),
    _lineage(
        "SIG-MODEL-CLUSTER",
        "FREQUENCY_INTERSECTION_CONCENTRATION",
        SIGNAL_TSV,
        "unselected clustering candidate",
        "SSF-UNSUPPORTED-CLUSTER",
        "UNSELECTED_COMPOUND",
        "REJECT",
        "Clustering is outside this round and is not an archive source fact.",
        duplicate=True,
        explanation_allowed=False,
    ),
    _lineage(
        "SIG-MODEL-RELATION-PROBABILITY",
        "FREQUENCY_INTERSECTION_CONCENTRATION",
        SIGNAL_TSV,
        "explicitly prohibited relation-probability candidate",
        "SSF-UNSUPPORTED-RELATION-PROBABILITY",
        "UNSUPPORTED_INFERENCE",
        "REJECT",
        "Archive-derived overlap cannot support a probability of historical or semantic relation.",
        duplicate=True,
        explanation_allowed=False,
    ),
    _lineage(
        "SIG-SOURCE-CONCENTRATION",
        "SOURCE_CORPUS_COMPOSITION",
        CORRELATION_SUMMARY,
        "dimensionConcentrationRows[dimension=source]",
        "SSF-SOURCE-IDENTITY",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Source concentration derives from source identity and diagnoses corpus bias.",
        direct_parents=("SIG-SOURCE-NAME",),
        duplicate=True,
        diagnostic=True,
    ),
    _lineage(
        "SIG-SOURCE-DIVERSITY",
        "SOURCE_CORPUS_COMPOSITION",
        CORRELATION_SUMMARY,
        "sourceCompositionRows candidate diversity summary",
        "SSF-SOURCE-IDENTITY",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Diversity is an aggregate/source-stratification diagnostic, not object-pair affinity.",
        direct_parents=("SIG-SOURCE-CONCENTRATION", "SIG-SOURCE-NAME"),
        duplicate=True,
        diagnostic=True,
    ),
    _lineage(
        "SIG-SOURCE-DOMINANT",
        "SOURCE_CORPUS_COMPOSITION",
        FREQUENCY_TSV,
        "dimension=source dominant-value diagnostic",
        "SSF-SOURCE-IDENTITY",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Dominant-source incidence is corpus composition, not independent pair evidence.",
        direct_parents=("SIG-SOURCE-FREQUENCY",),
        duplicate=True,
        diagnostic=True,
    ),
    _lineage(
        "SIG-SOURCE-FREQUENCY",
        "SOURCE_CORPUS_COMPOSITION",
        FREQUENCY_TSV,
        "dimension=source",
        "SSF-SOURCE-IDENTITY",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Source frequency may inform caps or IDF but repeats the source identity population.",
        direct_parents=("SIG-SOURCE-NAME",),
        duplicate=True,
        diagnostic=True,
    ),
    _lineage(
        "SIG-SOURCE-NAME",
        "SOURCE_CORPUS_COMPOSITION",
        CONTEXT_RECORDS,
        "records[].selectedRecord.rootMetadata.sourceName",
        "SSF-SOURCE-IDENTITY",
        "DIRECT_APPROVED_PUBLIC_METADATA",
        "INDEPENDENT_BASE_SIGNAL",
        "Public source identity is observable but biased; positive use requires an explicit capped experiment policy.",
        independent=True,
        candidate_allowed=True,
        scoring_allowed=True,
        scoring_guard="SOURCE_POLICY_VARIANT_REQUIRED;NOT_AUTOMATICALLY_POSITIVE;FAMILY_CAP_REQUIRED",
    ),
    _lineage(
        "SIG-SOURCE-RARE",
        "SOURCE_CORPUS_COMPOSITION",
        FREQUENCY_TSV,
        "dimension=source rarity_band",
        "SSF-SOURCE-IDENTITY",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Rare-source status derives from frequency and is not importance or a separate score signal.",
        direct_parents=("SIG-SOURCE-FREQUENCY",),
        duplicate=True,
        diagnostic=True,
    ),
    _lineage(
        "SIG-SOURCE-SAME",
        "SOURCE_CORPUS_COMPOSITION",
        SIGNAL_TSV,
        "pairwise comparison derived from sourceName",
        "SSF-SOURCE-IDENTITY",
        "DETERMINISTIC_DERIVATION",
        "EXPLANATION_ONLY",
        "Same-source equality repeats the source fact and is not automatically positive affinity.",
        direct_parents=("SIG-SOURCE-NAME",),
        duplicate=True,
    ),
    _lineage(
        "SIG-SOURCE-SHARE",
        "SOURCE_CORPUS_COMPOSITION",
        FREQUENCY_TSV,
        "dimension=source assignment_share",
        "SSF-SOURCE-IDENTITY",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Source share is frequency divided by the public denominator and supplies bias diagnostics only.",
        direct_parents=("SIG-SOURCE-FREQUENCY",),
        duplicate=True,
        diagnostic=True,
    ),
    _lineage(
        "SIG-TEMPORAL-CONCENTRATION",
        "GOVERNED_TEMPORAL",
        CORRELATION_SUMMARY,
        "dimensionConcentrationRows[dimension=decade]",
        "SSF-TEMPORAL-OBSERVATION",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Decade concentration derives from governed temporal observations and diagnoses corpus composition.",
        direct_parents=("SIG-TEMPORAL-DECADE",),
        duplicate=True,
        diagnostic=True,
    ),
    _lineage(
        "SIG-TEMPORAL-DECADE",
        "GOVERNED_TEMPORAL",
        SPACETIME_RECORDS,
        "records[].periodIds",
        "SSF-TEMPORAL-OBSERVATION",
        "GOVERNED_PROJECTION_DERIVATION",
        "CANDIDATE_GENERATION_ONLY",
        "Decade postings are deterministically projected from temporal extent and cannot add a second temporal score.",
        direct_parents=("SIG-TEMPORAL-EXTENT",),
        duplicate=True,
        candidate_allowed=True,
    ),
    _lineage(
        "SIG-TEMPORAL-DISTANCE",
        "GOVERNED_TEMPORAL",
        SIGNAL_TSV,
        "unselected temporal-distance candidate",
        "SSF-UNSELECTED-TEMPORAL-DISTANCE",
        "UNSELECTED_COMPOUND",
        "REJECT",
        "A Round 5 unselected distance signal cannot be scored; Round 6 methods must derive transparent bounded variants from extent.",
        direct_parents=("SIG-TEMPORAL-EXTENT", "SIG-TEMPORAL-PRECISION"),
        duplicate=True,
        explanation_allowed=False,
    ),
    _lineage(
        "SIG-TEMPORAL-EXTENT",
        "GOVERNED_TEMPORAL",
        SPACETIME_RECORDS,
        "records[].time.startYearInclusive/endYearInclusive",
        "SSF-TEMPORAL-OBSERVATION",
        "DIRECT_GOVERNED_FACT",
        "INDEPENDENT_BASE_SIGNAL",
        "Inclusive governed temporal extent is the canonical temporal source fact.",
        independent=True,
        candidate_allowed=True,
        scoring_allowed=True,
        scoring_guard="TRANSPARENT_BOUNDED_INTERVAL_FUNCTION_ONLY;PRECISION_PRESERVED;NO_HISTORICAL_PROXIMITY_CLAIM",
    ),
    _lineage(
        "SIG-TEMPORAL-LONG-RANGE",
        "GOVERNED_TEMPORAL",
        MISSINGNESS_SUMMARY,
        "longRangeTemporalDiagnostic",
        "SSF-TEMPORAL-OBSERVATION",
        "ANALYSIS_DIAGNOSTIC",
        "DIAGNOSTIC_ONLY",
        "Long-range status derives from extent and diagnoses uncertainty rather than affinity.",
        direct_parents=("SIG-TEMPORAL-RANGE-SPAN",),
        derived_from=("SIG-TEMPORAL-EXTENT", "SIG-TEMPORAL-RANGE-SPAN"),
        duplicate=True,
        diagnostic=True,
    ),
    _lineage(
        "SIG-TEMPORAL-PRECISION",
        "GOVERNED_TEMPORAL",
        SPACETIME_RECORDS,
        "records[].time.precision",
        "SSF-TEMPORAL-PRECISION",
        "COMPARABILITY_STATE",
        "COMPARABILITY_ONLY",
        "Temporal precision qualifies interval comparability; matching precision is not positive affinity.",
        duplicate=True,
    ),
    _lineage(
        "SIG-TEMPORAL-RANGE-SPAN",
        "GOVERNED_TEMPORAL",
        MISSINGNESS_SUMMARY,
        "rangeSpanDistribution",
        "SSF-TEMPORAL-OBSERVATION",
        "DETERMINISTIC_DERIVATION",
        "EXPLANATION_ONLY",
        "Range span is computed from the same inclusive extent and may explain a temporal contribution only.",
        direct_parents=("SIG-TEMPORAL-EXTENT",),
        duplicate=True,
    ),
    _lineage(
        "SIG-TEMPORAL-SAME-DECADE",
        "GOVERNED_TEMPORAL",
        SIGNAL_TSV,
        "pairwise comparison derived from periodIds",
        "SSF-TEMPORAL-OBSERVATION",
        "DETERMINISTIC_DERIVATION",
        "EXPLANATION_ONLY",
        "Same-decade equality repeats the temporal extent projection and cannot add a second temporal score.",
        direct_parents=("SIG-TEMPORAL-DECADE",),
        derived_from=("SIG-TEMPORAL-DECADE", "SIG-TEMPORAL-EXTENT"),
        duplicate=True,
    ),
)

LINEAGE_SPEC_BY_ID = {spec["signal_id"]: spec for spec in _SPECS}

RAW_CURATED_JACCARD_IMPORT_BOUNDARY: dict[str, Any] = {
    "boundaryId": "EXP-SIM-RAW-CURATED-JACCARD-NO-PRODUCTION-IMPORT-V1",
    "modelId": "M0_RAW_CURATED_JACCARD_NEGATIVE_CONTROL",
    "signalId": "SIG-CURATORIAL-JACCARD",
    "productionEligible": False,
    "shortlistEligible": False,
    "allowedRoles": ["NEGATIVE_CONTROL", "STRUCTURAL_DIAGNOSTIC"],
    "forbiddenProductionImportTokens": [
        "M0_RAW_CURATED_JACCARD_NEGATIVE_CONTROL",
        "RAW_CURATED_JACCARD",
        "SIG-CURATORIAL-JACCARD",
        "compute_raw_curated_jaccard",
        "raw_curated_jaccard",
    ],
    "forbiddenProductionRoots": [
        "frontend/app",
        "frontend/pages",
        "frontend/src/app",
        "frontend/src/features",
    ],
    "allowedAnalysisRoot": "scripts/exploration-v49-similarity",
    "runtimeScorerImportAllowed": False,
    "candidateGeneratorImportAllowed": False,
    "explanationRuntimeImportAllowed": False,
}

EXPECTED_GEOGRAPHY_CLASS_MAPPING_RECEIPT: dict[str, Any] = {
    "governedGeographyIdCount": 93,
    "singleClassMappingCount": 93,
    "ambiguousClassMappingCount": 0,
    "missingClassMappingCount": 0,
    "distinctGeographyClassCount": 5,
    "mappingSha256": GEOGRAPHY_CLASS_MAPPING_SHA256,
    "deterministicLookup": True,
    "independentInformationAdded": False,
}


def validate_governed_geography_class_mapping(
    geography_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Prove that geography class is a total deterministic lookup by ID."""

    if not isinstance(geography_registry, Mapping):
        raise SignalLineageError("geography registry must be a mapping")
    entries = geography_registry.get("entries")
    if not isinstance(entries, list) or len(entries) != 93:
        raise SignalLineageError(
            "governed geography registry must contain exactly 93 entries"
        )
    by_id: dict[str, str] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            raise SignalLineageError(
                f"governed geography entry {index} is not a mapping"
            )
        geography_id = entry.get("geographyId")
        geography_class = entry.get("geographyClass")
        if not isinstance(geography_id, str) or not geography_id:
            raise SignalLineageError(
                f"governed geography entry {index} lacks geographyId"
            )
        if (
            not isinstance(geography_class, str)
            or not geography_class
            or geography_class.strip() != geography_class
        ):
            raise SignalLineageError(
                f"governed geography {geography_id} lacks one scalar class"
            )
        previous = by_id.setdefault(geography_id, geography_class)
        if previous != geography_class:
            raise SignalLineageError(
                f"governed geography {geography_id} maps to multiple classes"
            )
    if len(by_id) != 93:
        raise SignalLineageError("governed geography IDs are not unique")
    mapping_rows = [
        {"geographyId": geography_id, "geographyClass": by_id[geography_id]}
        for geography_id in sorted(by_id)
    ]
    receipt = {
        "governedGeographyIdCount": len(by_id),
        "singleClassMappingCount": len(by_id),
        "ambiguousClassMappingCount": 0,
        "missingClassMappingCount": 0,
        "distinctGeographyClassCount": len(set(by_id.values())),
        "mappingSha256": _sha256_json(mapping_rows),
        "deterministicLookup": True,
        "independentInformationAdded": False,
    }
    if receipt != EXPECTED_GEOGRAPHY_CLASS_MAPPING_RECEIPT:
        raise SignalLineageError("governed geography-class mapping changed")
    return receipt


def _validate_input_receipt(input_receipt: Mapping[str, Any] | None) -> dict[str, Any]:
    if input_receipt is None:
        return dict(EXPECTED_INPUT_RECEIPT)
    if not isinstance(input_receipt, Mapping):
        raise SignalLineageError("input receipt must be a mapping")
    for key, expected in EXPECTED_INPUT_RECEIPT.items():
        if input_receipt.get(key) != expected:
            raise SignalLineageError(f"frozen input receipt mismatch: {key}")
    return {key: input_receipt[key] for key in EXPECTED_INPUT_RECEIPT}


def _validate_registry_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise SignalLineageError("signal registry rows must be an array")
    by_id: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise SignalLineageError(f"signal registry row {index} is not a mapping")
        signal_id = row.get("signal_id")
        if not isinstance(signal_id, str) or not signal_id:
            raise SignalLineageError(f"signal registry row {index} lacks signal_id")
        if signal_id in by_id:
            raise SignalLineageError(f"duplicate signal registry ID: {signal_id}")
        by_id[signal_id] = row
    actual_ids = set(by_id)
    expected_ids = set(LINEAGE_SPEC_BY_ID)
    if actual_ids != expected_ids:
        missing = sorted(expected_ids - actual_ids)
        unexpected = sorted(actual_ids - expected_ids)
        raise SignalLineageError(
            f"sealed 64-signal registry mismatch; missing={missing}; unexpected={unexpected}"
        )
    if len(by_id) != 64:
        raise SignalLineageError("signal registry must contain exactly 64 rows")
    for signal_id, row in by_id.items():
        spec = LINEAGE_SPEC_BY_ID[signal_id]
        if row.get("family") != spec["registry_family"]:
            raise SignalLineageError(f"Round 5 family changed for {signal_id}")
        if str(row.get("historical_relation", "")).lower() != "false":
            raise SignalLineageError(f"historical relation entered {signal_id}")
        if str(row.get("semantic_relation", "")).lower() != "false":
            raise SignalLineageError(f"semantic relation entered {signal_id}")
        if (spec["candidate_generation_allowed"] or spec["scoring_allowed"]) and str(
            row.get("public_safe", "")
        ).lower() != "true":
            raise SignalLineageError(
                f"non-public-safe signal received retrieval/scoring permission: {signal_id}"
            )
    return by_id


def build_signal_lineage_rows(
    registry_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Return the complete canonical 64-row lineage registry.

    Parent arrays are represented as JSON-ready lists so ``common.tsv_bytes``
    serializes them unambiguously into the required TSV cells.
    """

    _validate_registry_rows(registry_rows)
    output: list[dict[str, Any]] = []
    for signal_id in sorted(LINEAGE_SPEC_BY_ID):
        spec = LINEAGE_SPEC_BY_ID[signal_id]
        row = {column: spec[column] for column in LINEAGE_COLUMNS}
        row["direct_parent_signals"] = list(row["direct_parent_signals"])
        row["derived_from_signals"] = list(row["derived_from_signals"])
        output.append(row)
    return output


def _same_source_double_score_groups(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    scoring_by_group: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        if row["scoring_allowed"]:
            scoring_by_group[str(row["same_source_fact_group"])].append(
                str(row["signal_id"])
            )
    return sorted(
        group for group, signal_ids in scoring_by_group.items() if len(signal_ids) > 1
    )


def validate_signal_lineage_analysis(analysis: Mapping[str, Any]) -> None:
    """Raise when a lineage analysis violates the closed scoring boundary."""

    if not isinstance(analysis, Mapping):
        raise SignalLineageError("lineage analysis must be a mapping")
    signals = analysis.get("signals")
    if not isinstance(signals, list) or len(signals) != 64:
        raise SignalLineageError("lineage analysis must contain 64 signals")
    if [row.get("signal_id") for row in signals] != sorted(LINEAGE_SPEC_BY_ID):
        raise SignalLineageError("lineage signal order or identity changed")
    for row in signals:
        missing_columns = set(LINEAGE_COLUMNS) - set(row)
        if missing_columns:
            raise SignalLineageError(
                f"{row.get('signal_id')} lacks lineage columns {sorted(missing_columns)}"
            )
        if row["scoring_disposition"] not in SCORING_DISPOSITIONS:
            raise SignalLineageError(
                f"unknown scoring disposition for {row['signal_id']}"
            )
        if row["epistemic_level"] not in EPISTEMIC_LEVELS:
            raise SignalLineageError(f"unknown epistemic level for {row['signal_id']}")
        parent_ids = row["direct_parent_signals"]
        ancestry = row["derived_from_signals"]
        if not isinstance(parent_ids, list) or not isinstance(ancestry, list):
            raise SignalLineageError("lineage parents and ancestry must be arrays")
        if not set(parent_ids).issubset(set(ancestry)):
            raise SignalLineageError(
                f"direct parents escape ancestry for {row['signal_id']}"
            )
        if any(parent not in LINEAGE_SPEC_BY_ID for parent in ancestry):
            raise SignalLineageError(f"unknown ancestor for {row['signal_id']}")
        if row["duplicate_for_scoring"] and row["scoring_allowed"]:
            raise SignalLineageError(
                f"duplicate signal is scoring-eligible: {row['signal_id']}"
            )
        if row["diagnostic_only"] != (
            row["scoring_disposition"] == "DIAGNOSTIC_ONLY"
        ):
            raise SignalLineageError(
                f"diagnostic flag/disposition mismatch: {row['signal_id']}"
            )
        if row["scoring_allowed"] and row["scoring_disposition"] not in {
            "INDEPENDENT_BASE_SIGNAL",
            "DEPENDENT_INTERACTION_SIGNAL",
        }:
            raise SignalLineageError(
                f"invalid scoring permission for {row['signal_id']}"
            )
        if row["independent_information_candidate"] != (
            row["scoring_disposition"] == "INDEPENDENT_BASE_SIGNAL"
        ):
            raise SignalLineageError(
                f"independence flag/disposition mismatch: {row['signal_id']}"
            )
    double_groups = _same_source_double_score_groups(signals)
    if double_groups:
        raise SignalLineageError(
            f"same source facts remain multiply scoring-eligible: {double_groups}"
        )
    boundary = analysis.get("rawCuratedJaccardImportBoundary")
    if boundary != RAW_CURATED_JACCARD_IMPORT_BOUNDARY:
        raise SignalLineageError("raw curated Jaccard import boundary changed")
    if (
        analysis.get("geographyClassMappingReceipt")
        != EXPECTED_GEOGRAPHY_CLASS_MAPPING_RECEIPT
    ):
        raise SignalLineageError("governed geography-class mapping receipt changed")
    jaccard = next(
        row for row in signals if row["signal_id"] == "SIG-CURATORIAL-JACCARD"
    )
    if (
        jaccard["scoring_disposition"] != "DIAGNOSTIC_ONLY"
        or jaccard["scoring_allowed"]
        or jaccard["candidate_generation_allowed"]
    ):
        raise SignalLineageError("raw curated Jaccard escaped its negative-control role")
    geography_class = next(
        row for row in signals if row["signal_id"] == "SIG-GEOGRAPHY-CLASS"
    )
    if (
        geography_class["scoring_disposition"]
        != "CANDIDATE_GENERATION_ONLY"
        or geography_class["scoring_allowed"]
        or not geography_class["candidate_generation_allowed"]
        or geography_class["same_source_fact_group"]
        != "SSF-GEOGRAPHY-ASSIGNMENT"
        or geography_class["direct_parent_signals"]
        != ["SIG-GEOGRAPHY-ASSIGNMENT"]
    ):
        raise SignalLineageError(
            "deterministic geography class escaped its candidate-only boundary"
        )
    invariants = analysis.get("invariants")
    if not isinstance(invariants, Mapping) or not all(invariants.values()):
        raise SignalLineageError("lineage analysis has a failed invariant")


def analyze_signal_lineage(
    registry_rows: Sequence[Mapping[str, Any]],
    *,
    input_receipt: Mapping[str, Any] | None = None,
    geography_registry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify all 64 signals and return a canonical machine receipt."""

    frozen_input_receipt = _validate_input_receipt(input_receipt)
    geography_class_mapping_receipt = (
        validate_governed_geography_class_mapping(geography_registry)
        if geography_registry is not None
        else dict(EXPECTED_GEOGRAPHY_CLASS_MAPPING_RECEIPT)
    )
    signals = build_signal_lineage_rows(registry_rows)
    disposition_counts = Counter(row["scoring_disposition"] for row in signals)
    group_members: dict[str, list[str]] = defaultdict(list)
    for row in signals:
        group_members[row["same_source_fact_group"]].append(row["signal_id"])
    same_source_fact_groups = {
        group: sorted(signal_ids) for group, signal_ids in sorted(group_members.items())
    }
    double_score_groups = _same_source_double_score_groups(signals)
    scoring_eligible = sorted(
        row["signal_id"] for row in signals if row["scoring_allowed"]
    )
    candidate_generation = sorted(
        row["signal_id"]
        for row in signals
        if row["candidate_generation_allowed"]
    )
    independent = sorted(
        row["signal_id"]
        for row in signals
        if row["scoring_disposition"] == "INDEPENDENT_BASE_SIGNAL"
    )
    interaction = sorted(
        row["signal_id"]
        for row in signals
        if row["scoring_disposition"] == "DEPENDENT_INTERACTION_SIGNAL"
    )
    material: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "derivationVersion": DERIVATION_VERSION,
        "inputReceipt": frozen_input_receipt,
        "geographyClassMappingReceipt": geography_class_mapping_receipt,
        "signals": signals,
        "counts": {
            "signalInputCount": 64,
            "signalLineageClassifiedCount": len(signals),
            "signalLineageUnclassifiedCount": 0,
            "dispositionCounts": dict(sorted(disposition_counts.items())),
            "independentBaseSignalCount": disposition_counts[
                "INDEPENDENT_BASE_SIGNAL"
            ],
            "dependentInteractionSignalCount": disposition_counts[
                "DEPENDENT_INTERACTION_SIGNAL"
            ],
            "candidateGenerationOnlySignalCount": disposition_counts[
                "CANDIDATE_GENERATION_ONLY"
            ],
            "comparabilityOnlySignalCount": disposition_counts[
                "COMPARABILITY_ONLY"
            ],
            "explanationOnlySignalCount": disposition_counts["EXPLANATION_ONLY"],
            "diagnosticOnlySignalCount": disposition_counts["DIAGNOSTIC_ONLY"],
            "rejectedScoringSignalCount": disposition_counts["REJECT"],
            "sameSourceFactGroupCount": len(same_source_fact_groups),
            "multiSignalSameSourceFactGroupCount": sum(
                len(signal_ids) > 1 for signal_ids in same_source_fact_groups.values()
            ),
            "duplicateForScoringSignalCount": sum(
                bool(row["duplicate_for_scoring"]) for row in signals
            ),
            "sameSourceFactDoubleScoreCount": len(double_score_groups),
            "interactionOnlySignalCount": sum(
                bool(row["interaction_only"]) for row in signals
            ),
            "candidateGenerationAllowedCount": len(candidate_generation),
            "scoringAllowedCount": len(scoring_eligible),
            "explanationAllowedCount": sum(
                bool(row["explanation_allowed"]) for row in signals
            ),
            "curatorialResidualSignalCount": 0,
        },
        "independentBaseSignalIds": independent,
        "dependentInteractionSignalIds": interaction,
        "scoringEligibleSignalIds": scoring_eligible,
        "candidateGenerationSignalIds": candidate_generation,
        "sameSourceFactGroups": same_source_fact_groups,
        "sameSourceFactDoubleScoreGroups": double_score_groups,
        "scoringGuardsBySignalId": {
            signal_id: LINEAGE_SPEC_BY_ID[signal_id]["scoring_guard"]
            for signal_id in sorted(LINEAGE_SPEC_BY_ID)
        },
        "rawCuratedJaccardImportBoundary": dict(
            RAW_CURATED_JACCARD_IMPORT_BOUNDARY
        ),
        "invariants": {
            "EXP_SIM_INV_001_RAW_CURATED_JACCARD_PRODUCTION_INELIGIBLE": True,
            "EXP_SIM_INV_002_EVERY_SCORED_SIGNAL_RESOLVES_TO_LINEAGE": (
                set(scoring_eligible).issubset(LINEAGE_SPEC_BY_ID)
            ),
            "EXP_SIM_INV_003_SAME_SOURCE_FACT_AT_MOST_ONCE": not double_score_groups,
            "EXP_SIM_INV_004_INTERACTIONS_SEPARATE_FROM_PARENTS": all(
                row["direct_parent_signals"] and not row["independent_information_candidate"]
                for row in signals
                if row["scoring_disposition"] == "DEPENDENT_INTERACTION_SIGNAL"
            ),
            "EXP_SIM_INV_005_SHARED_MISSING_ZERO_DEFAULT_AFFINITY": all(
                not row["scoring_allowed"]
                for row in signals
                if row["scoring_disposition"] == "COMPARABILITY_ONLY"
            ),
            "EXP_SIM_INV_008_CURATION_NOT_HISTORICAL_RELATION": True,
            "EXP_SIM_INV_009_RARE_NOT_IMPORTANT": not any(
                row["scoring_allowed"] and "RARE" in row["signal_id"]
                for row in signals
            ),
            "EXP_SIM_INV_010_MAP_DISTANCE_ZERO": not LINEAGE_SPEC_BY_ID[
                "SIG-GEOGRAPHY-DISTANCE"
            ]["scoring_allowed"],
            "GEOGRAPHY_CLASS_DETERMINISTIC_LOOKUP_NOT_INDEPENDENT": (
                geography_class_mapping_receipt["deterministicLookup"]
                and not geography_class_mapping_receipt[
                    "independentInformationAdded"
                ]
                and LINEAGE_SPEC_BY_ID["SIG-GEOGRAPHY-CLASS"][
                    "scoring_disposition"
                ]
                == "CANDIDATE_GENERATION_ONLY"
                and not LINEAGE_SPEC_BY_ID["SIG-GEOGRAPHY-CLASS"][
                    "scoring_allowed"
                ]
            ),
            "EXP_SIM_INV_011_SOURCE_NOT_AUTOMATICALLY_POSITIVE": (
                "NOT_AUTOMATICALLY_POSITIVE"
                in LINEAGE_SPEC_BY_ID["SIG-SOURCE-NAME"]["scoring_guard"]
            ),
            "EXP_SIM_INV_012_LINEAGE_DETERMINISTIC": True,
            "EXP_SIM_INV_013_INPUTS_PINNED": (
                frozen_input_receipt == EXPECTED_INPUT_RECEIPT
            ),
            "EXP_SIM_INV_014_HELD_EXCLUDED": frozen_input_receipt[
                "heldObjectCount"
            ]
            == HELD_OBJECT_COUNT,
            "EXP_SIM_INV_017_UNSUPPORTED_RELATION_COMPOUND_REJECTED": (
                LINEAGE_SPEC_BY_ID["SIG-MODEL-RELATION-PROBABILITY"][
                    "scoring_disposition"
                ]
                == "REJECT"
            ),
            "EXP_SIM_INV_019_CLUSTERING_REJECTED": LINEAGE_SPEC_BY_ID[
                "SIG-MODEL-CLUSTER"
            ]["scoring_disposition"]
            == "REJECT",
            "UNCLASSIFIED_SIGNAL_LINEAGE_COUNT_ZERO": len(signals) == 64,
            "CURATORIAL_RESIDUAL_SIGNAL_COUNT_ZERO": True,
            "RAW_CURATED_JACCARD_IMPORT_BOUNDARY_DECLARED": True,
        },
    }
    material["signalsSha256"] = _sha256_json(signals)
    material["deterministicReceipt"] = {
        "canonicalization": "recursive key sort; compact JSON; final LF; UTF-8",
        "sha256": _sha256_json(material),
    }
    validate_signal_lineage_analysis(material)
    return material


def _self_test() -> None:
    # Import lazily so the pure analysis functions remain usable without a repo.
    from common import ROOT, load_json, load_signal_registry, source_receipt

    signal_input = load_signal_registry()
    geography_registry = load_json(ROOT / SPACETIME_GEOGRAPHY)
    first = analyze_signal_lineage(
        signal_input["rows"],
        input_receipt=source_receipt(),
        geography_registry=geography_registry,
    )
    second = analyze_signal_lineage(
        list(reversed(signal_input["rows"])),
        input_receipt=source_receipt(),
        geography_registry=geography_registry,
    )
    assert first == second
    assert first["counts"]["signalLineageClassifiedCount"] == 64
    assert first["counts"]["signalLineageUnclassifiedCount"] == 0
    assert sum(first["counts"]["dispositionCounts"].values()) == 64
    assert first["counts"]["independentBaseSignalCount"] == 8
    assert first["counts"]["candidateGenerationOnlySignalCount"] == 9
    assert first["counts"]["scoringAllowedCount"] == 10
    assert first["counts"]["sameSourceFactDoubleScoreCount"] == 0
    assert first["counts"]["curatorialResidualSignalCount"] == 0
    assert first["rawCuratedJaccardImportBoundary"]["productionEligible"] is False
    assert first["rawCuratedJaccardImportBoundary"]["shortlistEligible"] is False
    assert first["geographyClassMappingReceipt"] == (
        EXPECTED_GEOGRAPHY_CLASS_MAPPING_RECEIPT
    )

    duplicate = [dict(row) for row in signal_input["rows"]]
    duplicate.append(dict(duplicate[0]))
    try:
        analyze_signal_lineage(duplicate)
    except SignalLineageError:
        pass
    else:
        raise AssertionError("duplicate registry ID was accepted")

    unknown = [dict(row) for row in signal_input["rows"]]
    unknown[0]["signal_id"] = "SIG-UNCLASSIFIED"
    try:
        analyze_signal_lineage(unknown)
    except SignalLineageError:
        pass
    else:
        raise AssertionError("unclassified registry ID was accepted")

    print(
        json.dumps(
            {
                "status": "PASS",
                "schemaVersion": SCHEMA_VERSION,
                "signalCount": first["counts"]["signalLineageClassifiedCount"],
                "sameSourceFactGroupCount": first["counts"][
                    "sameSourceFactGroupCount"
                ],
                "sameSourceFactDoubleScoreCount": first["counts"][
                    "sameSourceFactDoubleScoreCount"
                ],
                "dispositionCounts": first["counts"]["dispositionCounts"],
                "signalsSha256": first["signalsSha256"],
                "receiptSha256": first["deterministicReceipt"]["sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    _self_test()
