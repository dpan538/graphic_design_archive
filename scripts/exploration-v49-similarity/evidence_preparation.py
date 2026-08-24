#!/usr/bin/env python3
"""Prepare bounded Round 6 evidence from the central benchmark receipt.

This module is deliberately an evidence *preparation* boundary.  It writes an
exact set of 13 bounded raw JSON summaries and 11 JSON row specifications to an
explicit output directory.  It never writes the final research TSVs, prose
documents, audit ledgers, or pair-level artifacts.

The normal workflow is two-pass:

1. prepare native raw components and TSV row specifications;
2. after all 24 research files exist, rerun with ``--research-dir`` so the
   central raw summary binds their exact byte counts and SHA-256 digests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import common
import independent_feature_basis
import signal_lineage


SCHEMA_VERSION = "trace-exploration-evidence-preparation/v1"
ROW_SPEC_SCHEMA_VERSION = "trace-exploration-tsv-row-spec/v1"
SOURCE_SHA = "0e311f0b88b4adc3cbfe2080ac98d622013cc6d3"
PUBLIC_OBJECT_COUNT = 7_995
EXHAUSTIVE_PAIR_COUNT = 31_956_015
MODEL_IDS = tuple(f"M{index}" for index in range(9))
SCALAR_MODEL_IDS = tuple(f"M{index}" for index in range(8))
CANDIDATE_VARIANTS = tuple(f"CG-CUR-{index}" for index in range(1, 7))
CURATORIAL_POLICIES = tuple(f"CUR-W{index}" for index in range(1, 7))
K_VALUES = (10, 20, 50)
SUPPORT_THRESHOLDS = (2, 3, 5, 10, 20)
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
RESIDUAL_INTERACTION_METHODS = (
    "NO_INTERACTION_CONTRIBUTION",
    "CAPPED_INTERACTION_BONUS",
    "INFORMATION_RESIDUAL_CONTRIBUTION",
    "LOG_LIKELIHOOD_INTERACTION_CONTRIBUTION",
)
ABLATION_FAMILIES = (
    "LEAVE_CONTEXT_OUT",
    "LEAVE_TIME_OUT",
    "LEAVE_GEOGRAPHY_OUT",
    "LEAVE_SOURCE_OUT",
    "LEAVE_CURATION_OUT",
    "LEAVE_MISSINGNESS_DIAGNOSTICS_OUT",
    "LEAVE_INTERACTIONS_OUT",
    "REMOVE_LARGEST_CURATED_CONTAINER",
    "REMOVE_DOMINANT_SOURCE",
    "CHANGE_BROAD_CONTAINER_THRESHOLD",
    "CHANGE_RARE_SUPPORT_THRESHOLD",
    "CHANGE_TEMPORAL_DECAY",
    "CHANGE_FAMILY_NORMALIZATION",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UUID_RE = re.compile(
    r"(?<![0-9a-f])[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}(?![0-9a-f])",
    re.IGNORECASE,
)
PRIVATE_ID_RE = re.compile(
    r"(?:\bFOL-[A-Z0-9_-]+|\bTRN-OBJ-[A-Z0-9_-]+|\bTRTREE[A-Z0-9_-]*|"
    r"\bTRBRANCH[A-Z0-9_-]*)",
    re.IGNORECASE,
)

RAW_FILES = (
    "exploration-similarity-evaluation-summary.json",
    "signal-lineage-summary.json",
    "independent-basis-summary.json",
    "candidate-index-summary.json",
    "model-benchmark-summary.json",
    "missingness-summary.json",
    "interaction-summary.json",
    "hubness-summary.json",
    "ablation-summary.json",
    "human-review-summary.json",
    "performance-summary.json",
    "analysis-run-summary.json",
    "security-summary.json",
)

RESEARCH_FILES = (
    "00_EXECUTIVE_DECISION.md",
    "01_EXPLORATION_TASK_DEFINITIONS.md",
    "02_SIMILARITY_LITERATURE_AND_APPLICABILITY.md",
    "03_SIGNAL_LINEAGE_REGISTRY.tsv",
    "04_INDEPENDENT_SIGNAL_BASIS.md",
    "05_EVALUATION_PROTOCOL.md",
    "06_CANDIDATE_GENERATION_ARCHITECTURE.md",
    "07_CURATORIAL_ATTENUATION_EXPERIMENTS.tsv",
    "08_MISSINGNESS_AND_COMPARABILITY.md",
    "09_MODEL_SPECIFICATIONS.md",
    "10_MODEL_BENCHMARK_RESULTS.tsv",
    "11_CANDIDATE_RECALL_RESULTS.tsv",
    "12_SOURCE_BIAS_AND_FAMILY_DOMINANCE.tsv",
    "13_HUBNESS_ANALYSIS.tsv",
    "14_ABLATION_AND_STABILITY.tsv",
    "15_INTERACTION_STATISTICS_REVIEW.tsv",
    "16_MECHANICAL_EXPECTATION_CASES.tsv",
    "17_HUMAN_REVIEW_PACKET.tsv",
    "18_EXPLANATION_CONTRACT.md",
    "19_ANALYSIS_RUN_REGISTER.tsv",
    "20_PERFORMANCE_AND_ARCHITECTURE.md",
    "21_RED_TEAM.md",
    "22_MODEL_SHORTLIST_DECISION.md",
    "23_ROUND_DECISION.md",
)

TSV_FILES = tuple(name for name in RESEARCH_FILES if name.endswith(".tsv"))

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


class EvidencePreparationError(RuntimeError):
    """Raised when the benchmark cannot be converted without invention."""


def _canonical_bytes(value: Any, *, pretty: bool = False) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256(_canonical_bytes(value))


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise EvidencePreparationError(f"{label} must be a JSON object")
    return dict(value)


def _rows(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise EvidencePreparationError(f"{label} must be a JSON row array")
    if not all(isinstance(row, Mapping) for row in value):
        raise EvidencePreparationError(f"{label} contains a non-object row")
    return [dict(row) for row in value]


def _sha(value: Any, label: str) -> str:
    text = str(value)
    if not SHA256_RE.fullmatch(text):
        raise EvidencePreparationError(f"{label} is not a lowercase SHA-256 digest")
    return text


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise EvidencePreparationError(f"{label} is not an integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise EvidencePreparationError(f"{label} is not an integer") from error
    if isinstance(value, float) and value != number:
        raise EvidencePreparationError(f"{label} is not an integer")
    return number


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise EvidencePreparationError(f"{label} is not numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise EvidencePreparationError(f"{label} is not numeric") from error
    if not (-float("inf") < number < float("inf")):
        raise EvidencePreparationError(f"{label} is not finite")
    return number


def _false(value: Any, label: str) -> None:
    if not (
        value is False
        or (isinstance(value, int) and not isinstance(value, bool) and value == 0)
        or (isinstance(value, str) and value in {"false", "False", "0"})
    ):
        raise EvidencePreparationError(f"{label} must remain false")


def _compact_cell(value: Any) -> Any:
    if isinstance(value, (Mapping, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if value is None:
        return ""
    return value


def _select(source: Mapping[str, Any], headers: Sequence[str]) -> dict[str, Any]:
    return {header: _compact_cell(source.get(header, "")) for header in headers}


def _remap(
    source: Mapping[str, Any],
    mapping: Sequence[tuple[str, str]],
    *,
    defaults: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    defaults = defaults or {}
    return {
        target: _compact_cell(source.get(native, defaults.get(target, "")))
        for target, native in mapping
    }


def _atomic_json(path: Path, value: Any) -> int:
    payload = _canonical_bytes(value, pretty=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)
    return len(payload)


def _walk(value: Any):
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key), item
            yield from _walk(item)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            yield from _walk(item)


def _validate_bounded(value: Any, label: str) -> None:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if UUID_RE.search(serialized) or PRIVATE_ID_RE.search(serialized):
        raise EvidencePreparationError(f"{label} exposes a private identifier")
    for key, item in _walk(value):
        normalized = re.sub(r"[^a-z0-9]", "", key.casefold())
        if normalized in {
            "pairrows",
            "pairrowsmaterialized",
            "pairrowsretained",
            "pairrowsemitted",
            "pairrowsstored",
            "pairrowscommitted",
        }:
            if isinstance(item, list) and item:
                raise EvidencePreparationError(f"{label}.{key} materializes pair rows")
            if not isinstance(item, list) and _integer(item, f"{label}.{key}") != 0:
                raise EvidencePreparationError(f"{label}.{key} reports retained pair rows")
        if "pairmatrix" in normalized or normalized in {"allpairs", "allpairrows"}:
            permitted = (
                item is False
                or item is None
                or (isinstance(item, int) and not isinstance(item, bool) and item == 0)
                or (isinstance(item, str) and item in {"false", "False", "0", ""})
                or (isinstance(item, list) and not item)
            )
            if not permitted:
                raise EvidencePreparationError(f"{label}.{key} reports a pair matrix")


def _load_central(path: Path) -> tuple[dict[str, Any], str]:
    payload = path.read_bytes()
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidencePreparationError("central benchmark is not valid UTF-8 JSON") from error
    central = _mapping(value, "central benchmark")
    if central.get("sourceCommit") != SOURCE_SHA:
        raise EvidencePreparationError("central benchmark source commit changed")
    if _integer(central.get("publicObjectCount"), "public object count") != PUBLIC_OBJECT_COUNT:
        raise EvidencePreparationError("central benchmark public cohort changed")
    if _integer(central.get("heldExplorationObjectCount"), "held object count") != 0:
        raise EvidencePreparationError("held objects entered the central benchmark")
    if _integer(central.get("exhaustivePairCount"), "exhaustive pair count") != EXHAUSTIVE_PAIR_COUNT:
        raise EvidencePreparationError("central benchmark pair count changed")
    for field in (
        "randomnessAffectsAffinity",
        "randomnessAffectsCandidateSet",
        "publicSimilarityModelSelected",
        "publicSimilarityWeightsSelected",
        "probabilityModelSelected",
        "clusteringModelSelected",
    ):
        _false(central.get(field), field)
    _validate_bounded(central, "central benchmark")
    return central, _sha256(payload)


def _regenerate_lineage_and_basis(central: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    signal_input = common.load_signal_registry()
    geography_registry = common.load_json(ROOT / signal_lineage.SPACETIME_GEOGRAPHY)
    lineage = signal_lineage.analyze_signal_lineage(
        signal_input["rows"],
        input_receipt=common.source_receipt(),
        geography_registry=geography_registry,
    )
    signal_lineage.validate_signal_lineage_analysis(lineage)
    basis = independent_feature_basis.build_independent_feature_basis(lineage)
    independent_feature_basis.validate_independent_feature_basis(basis)
    central_lineage = _mapping(central.get("lineage"), "central lineage")
    central_basis = _mapping(central.get("basis"), "central basis")
    if central_lineage.get("signalsSha256") != lineage["signalsSha256"]:
        raise EvidencePreparationError("central lineage digest does not match frozen inputs")
    if central_lineage.get("receiptSha256") != lineage["deterministicReceipt"]["sha256"]:
        raise EvidencePreparationError("central lineage receipt does not match frozen inputs")
    if central_basis.get("basisRowsSha256") != basis["basisRowsSha256"]:
        raise EvidencePreparationError("central independent-basis digest does not match frozen inputs")
    if central_basis.get("receiptSha256") != basis["deterministicReceipt"]["sha256"]:
        raise EvidencePreparationError("central independent-basis receipt does not match frozen inputs")
    return lineage, basis


def _semantic_receipts(central: Mapping[str, Any]) -> dict[str, str]:
    candidates = _mapping(central.get("candidates"), "central candidates")
    return {
        "candidateIndexSha256": _sha(candidates.get("indexSha256"), "candidate index digest"),
        "scoringRecordsSha256": _sha(central.get("scoringRecordsSha256"), "scoring records digest"),
        "modelContextSha256": _sha(central.get("modelContextSha256"), "model context digest"),
        "compiledFeatureContextSha256": _sha(
            central.get("compiledFeatureContextSha256"), "compiled feature-context digest"
        ),
    }


def _research_receipts(research_dir: Path) -> dict[str, dict[str, Any]]:
    research_dir = research_dir.resolve()
    if not research_dir.is_dir():
        raise EvidencePreparationError(f"research directory is absent: {research_dir}")
    actual_files = {path.name for path in research_dir.iterdir() if path.is_file()}
    if actual_files != set(RESEARCH_FILES) or any(path.is_dir() for path in research_dir.iterdir()):
        missing = sorted(set(RESEARCH_FILES) - actual_files)
        extra = sorted(actual_files - set(RESEARCH_FILES))
        raise EvidencePreparationError(
            f"research receipt binding requires exact 24 files; missing={missing}, extra={extra}"
        )
    receipts: dict[str, dict[str, Any]] = {}
    for filename in RESEARCH_FILES:
        payload = (research_dir / filename).read_bytes()
        if not payload or not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
            raise EvidencePreparationError(f"research file lacks exactly one final LF: {filename}")
        receipts[filename] = {"bytes": len(payload), "sha256": _sha256(payload)}
    return receipts


def _shortlist_candidate_rows(
    candidates: Mapping[str, Any], shortlist: set[str]
) -> list[dict[str, Any]]:
    rows = _rows(candidates.get("rows"), "candidate rows")
    selected = [row for row in rows if str(row.get("referenceModelId", "")) in shortlist]
    if {str(row.get("referenceModelId", "")) for row in selected} != shortlist:
        raise EvidencePreparationError("candidate rows omit a shortlisted reference model")
    return selected


def _candidate_row_spec(candidates: Mapping[str, Any], shortlist: set[str]) -> dict[str, Any]:
    rows = _shortlist_candidate_rows(candidates, shortlist)
    grouped: defaultdict[tuple[str, str], dict[int, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        candidate_variant = str(row.get("candidateVariant", ""))
        reference_variant = str(row.get("referenceVariantId", ""))
        k = _integer(row.get("k"), "candidate k")
        key = (candidate_variant, reference_variant)
        if k in grouped[key]:
            raise EvidencePreparationError("candidate rows duplicate candidate/reference/k")
        grouped[key][k] = row
    if set(key[0] for key in grouped) != set(CANDIDATE_VARIANTS):
        raise EvidencePreparationError("candidate rows do not cover CG-CUR-1..6")
    headers = (
        "candidate_variant_id",
        "model_id",
        "reference_variant_id",
        "candidate_pool_p50",
        "candidate_pool_p90",
        "candidate_pool_p95",
        "candidate_pool_p99",
        "candidate_pool_max",
        "candidate_reduction_p50",
        "recall_at_10",
        "recall_at_20",
        "recall_at_50",
        "zero_candidate_object_count",
        "near_full_candidate_object_count",
        "candidate_generation_p50_ms",
        "candidate_generation_p95_ms",
        "candidate_sets_sha256",
        "pair_rows_materialized",
        "randomness_affects_candidate_set",
    )
    output = []
    for key in sorted(grouped):
        by_k = grouped[key]
        if set(by_k) != set(K_VALUES):
            raise EvidencePreparationError(f"candidate recall k grid is incomplete: {key}")
        representative = by_k[10]
        stable_fields = (
            "referenceModelId",
            "candidatePoolP50",
            "candidatePoolP90",
            "candidatePoolP95",
            "candidatePoolP99",
            "candidatePoolMax",
            "candidateReductionP50",
            "zeroCandidateObjectCount",
            "nearFullCorpusCandidateObjectCount",
            "candidateGenerationP50Ms",
            "candidateGenerationP95Ms",
            "candidateSetsSha256",
        )
        for field in stable_fields:
            if len({_sha256_json(row.get(field)) for row in by_k.values()}) != 1:
                raise EvidencePreparationError(f"candidate {field} conflicts across k: {key}")
        output.append(
            {
                "candidate_variant_id": key[0],
                "model_id": representative["referenceModelId"],
                "reference_variant_id": key[1],
                "candidate_pool_p50": representative["candidatePoolP50"],
                "candidate_pool_p90": representative["candidatePoolP90"],
                "candidate_pool_p95": representative["candidatePoolP95"],
                "candidate_pool_p99": representative["candidatePoolP99"],
                "candidate_pool_max": representative["candidatePoolMax"],
                "candidate_reduction_p50": representative["candidateReductionP50"],
                "recall_at_10": by_k[10]["recall"],
                "recall_at_20": by_k[20]["recall"],
                "recall_at_50": by_k[50]["recall"],
                "zero_candidate_object_count": representative["zeroCandidateObjectCount"],
                "near_full_candidate_object_count": representative[
                    "nearFullCorpusCandidateObjectCount"
                ],
                "candidate_generation_p50_ms": representative["candidateGenerationP50Ms"],
                "candidate_generation_p95_ms": representative["candidateGenerationP95Ms"],
                "candidate_sets_sha256": representative["candidateSetsSha256"],
                "pair_rows_materialized": 0,
                "randomness_affects_candidate_set": False,
            }
        )
    return {"headers": list(headers), "rows": output}


def _model_row_spec(models: Mapping[str, Any], shortlist: set[str]) -> dict[str, Any]:
    native_rows = _rows(models.get("rows"), "model benchmark rows")
    keys = [(str(row.get("modelId", "")), str(row.get("variantId", ""))) for row in native_rows]
    if len(keys) != len(set(keys)) or set(model for model, _ in keys) != set(MODEL_IDS):
        raise EvidencePreparationError("model benchmark keys are duplicated or omit M0..M8")
    flagged = {str(row["modelId"]) for row in native_rows if row.get("shortlistEligible") is True}
    if flagged != shortlist:
        raise EvidencePreparationError("native model shortlist flags disagree with central decision")
    headers = (
        "model_id",
        "variant_id",
        "model_family",
        "task",
        "symmetric",
        "symmetry_test",
        "asymmetry_declared",
        "deterministic",
        "comparability_exposed",
        "explanation_path",
        "shortlisted",
        "exhaustive_pair_count",
        "directional_score_count",
        "ranking_sha256",
        "compiled_feature_sha256",
        "compile_ms",
        "elapsed_ms",
        "model_score_ms",
        "explanation_profile_score_p95_ms",
        "pair_rows_retained",
        "full_pair_matrix_materialized",
        "production_eligible",
        "parameters_json",
        "historical_relation",
        "semantic_relation",
        "probability",
    )
    output = []
    for row in sorted(native_rows, key=lambda value: (str(value["modelId"]), str(value["variantId"]))):
        symmetric = bool(row.get("symmetric"))
        output.append(
            {
                "model_id": row["modelId"],
                "variant_id": row["variantId"],
                "model_family": row["modelFamily"],
                "task": row.get("task", ""),
                "symmetric": symmetric,
                "symmetry_test": "PASS" if symmetric else "NOT_APPLICABLE",
                "asymmetry_declared": not symmetric,
                "deterministic": True,
                "comparability_exposed": True,
                "explanation_path": True,
                "shortlisted": bool(row.get("shortlistEligible")),
                "exhaustive_pair_count": row.get("exhaustivePairCount", ""),
                "directional_score_count": row.get("directionalScoreCount", ""),
                "ranking_sha256": row.get("rankingSha256", ""),
                "compiled_feature_sha256": row.get("compiledFeatureSha256", ""),
                "compile_ms": row.get("compileMs", ""),
                "elapsed_ms": row.get("elapsedMs", ""),
                "model_score_ms": row.get("modelScoreMs", ""),
                "explanation_profile_score_p95_ms": row.get(
                    "explanationProfileScoreP95Ms", ""
                ),
                "pair_rows_retained": row.get("pairRowsRetained", 0),
                "full_pair_matrix_materialized": row.get(
                    "fullPairMatrixMaterialized", False
                ),
                "production_eligible": row.get("productionEligible", False),
                "parameters_json": _compact_cell(row.get("parameters", {})),
                "historical_relation": False,
                "semantic_relation": False,
                "probability": False,
            }
        )
    return {"headers": list(headers), "rows": output}


def _build_row_specs(
    central: Mapping[str, Any],
    lineage: Mapping[str, Any],
    benchmark_sha256: str,
) -> dict[str, dict[str, Any]]:
    candidates = _mapping(central.get("candidates"), "central candidates")
    models = _mapping(central.get("models"), "central models")
    curatorial = _mapping(central.get("curatorial"), "central curatorial")
    hubness = _mapping(central.get("hubness"), "central hubness")
    ablation = _mapping(central.get("ablation"), "central ablation")
    interactions = _mapping(central.get("interactions"), "central interactions")
    evaluation = _mapping(central.get("evaluation"), "central evaluation")
    mechanical = _mapping(evaluation.get("mechanical"), "central mechanical evaluation")
    human = _mapping(central.get("humanReview"), "central human review")
    runs = _mapping(central.get("runs"), "central analysis runs")
    shortlist = set(map(str, central.get("shortlistModelIds", ())))
    if not shortlist or len(shortlist) > 3 or not shortlist.issubset(set(MODEL_IDS) - {"M0"}):
        raise EvidencePreparationError("central shortlist is absent or invalid")

    lineage_rows = []
    for native in _rows(lineage.get("signals"), "lineage signals"):
        row = _select(native, LINEAGE_COLUMNS)
        row["direct_parent_signals"] = ";".join(map(str, native["direct_parent_signals"]))
        row["derived_from_signals"] = ";".join(map(str, native["derived_from_signals"]))
        lineage_rows.append(row)

    curatorial_headers = (
        "policy_id", "sensitivity_id", "policy_name", "role", "weight_rule",
        "posting_space", "alpha", "broad_stop_ratio", "rare_support_floor", "family_cap",
        "container_posting_count", "active_posting_count", "stopped_posting_count",
        "candidate_pool_p50", "candidate_pool_p90", "candidate_pool_p95",
        "candidate_pool_p99", "candidate_pool_max", "zero_candidate_object_count",
        "near_full_candidate_object_count", "weight_min", "weight_p50", "weight_max",
        "score_contribution", "score_contribution_basis", "residual_signal_count",
        "raw_membership_scoring_allowed", "same_source_parent_duplication_failures",
        "broad_dominance_failures", "randomness_affects_candidate_set",
        "historical_relation", "semantic_relation", "probability",
    )
    curatorial_rows = [
        _select(row, curatorial_headers)
        for row in _rows(curatorial.get("rows"), "curatorial rows")
    ]
    if len(curatorial_rows) != 9 or set(row["policy_id"] for row in curatorial_rows) != set(
        CURATORIAL_POLICIES
    ):
        raise EvidencePreparationError("curatorial row grid is not the exact nine-row policy grid")

    model_spec = _model_row_spec(models, shortlist)
    candidate_spec = _candidate_row_spec(candidates, shortlist)

    bias_mapping = (
        ("model_id", "modelId"), ("variant_id", "variantId"), ("k", "k"),
        ("query_count", "queryCount"),
        ("result_top1_source_share", "resultTop1SourceShare"),
        ("result_hhi", "resultHhi"), ("cross_source_rate", "crossSourceRate"),
        ("evaluated_result_count", "evaluatedResultCount"),
        ("median_maximum_family_share", "medianMaximumFamilyShare"),
        ("maximum_family_contribution_p95", "p95MaximumFamilyShare"),
        ("one_family_over_80_percent_rate", "oneFamilyOver80PercentRate"),
        ("source_dominated_query_rate", "sourceDominatedQueryRate"),
        ("curation_dominated_query_rate", "curationDominatedQueryRate"),
        ("same_source_is_historical_relation", "sameSourceIsHistoricalRelation"),
        ("diagnostic_only", "diagnosticOnly"),
    )
    # Sensitivity variants whose family profiles were intentionally not
    # measured carry null dominance metrics in the native raw evidence.  They
    # remain in hubness-summary.json, but cannot become numeric TSV rows.  The
    # table therefore contains every fully measured diagnostic row, including
    # the complete shortlist, without inventing replacements for nulls.
    native_bias_rows = _rows(hubness.get("biasRows"), "source-bias rows")
    bias_rows = [
        _remap(row, bias_mapping, defaults={"diagnostic_only": True})
        for row in native_bias_rows
        if all(
            row.get(field) is not None
            for field in (
                "resultTop1SourceShare",
                "resultHhi",
                "crossSourceRate",
                "sourceDominatedQueryRate",
                "curationDominatedQueryRate",
                "p95MaximumFamilyShare",
            )
        )
    ]
    if not shortlist.issubset({str(row["model_id"]) for row in bias_rows}):
        raise EvidencePreparationError("source-bias rows omit a shortlisted model")

    hub_mapping = (
        ("model_id", "modelId"), ("variant_id", "variantId"), ("k", "k"),
        ("object_count", "objectCount"), ("query_count", "queryCount"),
        ("mean", "mean"), ("variance", "variance"), ("skewness", "skewness"),
        ("gini", "gini"),
        ("top1_percent_occurrence_share", "top1PercentOccurrenceShare"),
        ("maximum_occurrence", "maximumOccurrence"),
        ("zero_occurrence_object_count", "zeroOccurrenceObjectCount"),
        ("total_occurrence_count", "totalOccurrenceCount"),
    )
    hub_rows = [
        _remap(row, hub_mapping) for row in _rows(hubness.get("rows"), "hubness rows")
    ]
    coverage: defaultdict[str, set[int]] = defaultdict(set)
    for row in hub_rows:
        coverage[str(row["model_id"])].add(_integer(row["k"], "hubness k"))
    if any(coverage[model] != set(K_VALUES) for model in SCALAR_MODEL_IDS):
        raise EvidencePreparationError("hubness rows omit a scalar model/k cell")

    ablation_mapping = (
        ("model_id", "modelId"), ("base_variant_id", "baseVariantId"),
        ("ablation_id", "ablationId"), ("ablation_family", "ablationFamily"),
        ("k", "k"), ("query_count", "queryCount"),
        ("mean_top_k_overlap", "meanTopKOverlap"),
        ("minimum_top_k_overlap", "minimumTopKOverlap"),
        ("mean_rank_correlation", "meanRankCorrelation"),
        ("minimum_rank_correlation", "minimumRankCorrelation"),
        ("scoring_effect", "scoringEffect"),
        ("learned_weights_used", "learnedWeightsUsed"),
        ("historical_labels_used", "historicalLabelsUsed"),
    )
    ablation_rows = [
        _remap(row, ablation_mapping, defaults={"historical_labels_used": False})
        for row in _rows(ablation.get("rows"), "ablation rows")
    ]
    ablation_coverage: defaultdict[str, set[str]] = defaultdict(set)
    ablation_k: defaultdict[tuple[str, str], set[int]] = defaultdict(set)
    for row in ablation_rows:
        ablation_coverage[str(row["model_id"])].add(str(row["ablation_family"]))
        ablation_k[(str(row["model_id"]), str(row["ablation_id"]))].add(
            _integer(row["k"], "ablation k")
        )
    if any(ablation_coverage[model] != set(ABLATION_FAMILIES) for model in MODEL_IDS[1:]):
        raise EvidencePreparationError("ablation rows omit a model/family cell")
    if any(values != set(K_VALUES) for values in ablation_k.values()):
        raise EvidencePreparationError("ablation rows omit a k cell")
    if (
        set(ablation_coverage) != set(MODEL_IDS[1:])
        or len(ablation_k) != 216
        or len(ablation_rows) != 648
        or any(
            sum(model_id == model for model_id, _ in ablation_k) != 27
            for model in MODEL_IDS[1:]
        )
    ):
        raise EvidencePreparationError("ablation rows are not the exact 8 x 27 x 3 grid")

    interaction_mapping = (
        ("method_id", "method"), ("support_threshold", "supportThreshold"),
        ("eligible_observed_cell_count", "eligibleObservedCellCount"),
        ("low_support_cells_excluded", "lowSupportCellsExcluded"),
        ("statistic_p50", "statisticP50"), ("statistic_p95", "statisticP95"),
        ("statistic_max", "statisticMax"),
        ("parent_contribution_repeated", "parentContributionRepeated"),
        ("importance_inference", "importanceInference"),
    )
    interaction_rows = []
    for row in _rows(interactions.get("rows"), "interaction rows"):
        mapped = _remap(row, interaction_mapping, defaults={"importance_inference": "PROHIBITED"})
        mapped["importance_inference"] = "PROHIBITED"
        interaction_rows.append(mapped)
    expected_interactions = {
        (method, threshold) for method in INTERACTION_METHODS for threshold in SUPPORT_THRESHOLDS
    }
    if {
        (str(row["method_id"]), _integer(row["support_threshold"], "interaction threshold"))
        for row in interaction_rows
    } != expected_interactions or len(interaction_rows) != len(expected_interactions):
        raise EvidencePreparationError("interaction method/support grid is incomplete")

    mechanical_headers = (
        "axiom_id", "rule", "expected_invariant", "model_applicability",
        "tested_model_ids", "model_result_summary", "observed_result", "status",
        "failure_count", "failed_model_ids", "case_sha256", "historical_relation",
        "semantic_relation", "probability",
    )
    mechanical_rows = [
        _select(row, mechanical_headers)
        for row in _rows(mechanical.get("rows"), "mechanical rows")
    ]
    if len(mechanical_rows) != 15 or any(
        row["status"] != "PASS" or _integer(row["failure_count"], "mechanical failure") != 0
        for row in mechanical_rows
    ):
        raise EvidencePreparationError("mechanical suite is incomplete or failing")

    human_mapping = (
        ("packet_row_id", "packetRowId"), ("anchor_public_id", "anchorPublicId"),
        ("anchor_title", "anchorTitle"),
        ("anchor_selection_strata", "anchorSelectionStrata"),
        ("blind_profile_slot", "blindProfileSlot"),
        ("candidate_ordinal", "candidateOrdinal"),
        ("candidate_public_id", "candidatePublicId"),
        ("candidate_title", "candidateTitle"),
        ("retrieval_reasons", "retrievalReasons"),
        ("shared_independent_signals", "sharedIndependentSignals"),
        ("distinctive_signals", "distinctiveSignals"),
        ("unavailable_families", "unavailableFamilies"),
        ("comparability_ratio", "comparabilityRatio"),
        ("anchor_source_name", "anchorSourceName"),
        ("candidate_source_name", "candidateSourceName"),
        ("source_composition", "sourceComposition"),
        ("source_bias_notes", "sourceBiasNotes"),
        ("interaction_evidence", "interactionEvidence"),
        ("useful_for_further_exploration", "usefulForFurtherExploration"),
        ("explanation_intelligible", "explanationIntelligible"),
        ("merely_broad_category", "merelyBroadCategory"),
        ("new_defensible_research_direction", "newDefensibleResearchDirection"),
        ("accidental_relation_suggestion", "accidentalRelationSuggestion"),
        ("reviewer_notes", "reviewerNotes"),
        ("human_review_completed", "humanReviewCompleted"),
        ("historical_relation", "historicalRelation"),
        ("semantic_relation", "semanticRelation"), ("probability", "probability"),
    )
    human_rows = [
        _remap(row, human_mapping) for row in _rows(human.get("rows"), "human-review rows")
    ]
    if len({str(row["anchor_public_id"]) for row in human_rows}) != 72:
        raise EvidencePreparationError("human-review rows do not cover exactly 72 anchors")
    groups: defaultdict[tuple[str, str], list[int]] = defaultdict(list)
    for row in human_rows:
        groups[(str(row["anchor_public_id"]), str(row["blind_profile_slot"]))].append(
            _integer(row["candidate_ordinal"], "human candidate ordinal")
        )
        if not str(row["retrieval_reasons"]).strip() or not str(
            row["shared_independent_signals"]
        ).strip():
            raise EvidencePreparationError("human-review row lacks an explanation path")
        _false(row["human_review_completed"], "human review completed")
    if any(sorted(values) != list(range(1, len(values) + 1)) or not 3 <= len(values) <= 5 for values in groups.values()):
        raise EvidencePreparationError("human-review candidate groups are not bounded 3..5")

    run_rows = _rows(runs.get("rows"), "analysis-run rows")
    if not set(MODEL_IDS).issubset({str(row.get("modelId", "")) for row in run_rows}):
        raise EvidencePreparationError("analysis-run register omits M0..M8")
    if _integer(runs.get("receiptFailureCount"), "analysis receipt failures") != 0:
        raise EvidencePreparationError("analysis-run register reports receipt failures")

    native_specs: dict[str, dict[str, Any]] = {
        "03_SIGNAL_LINEAGE_REGISTRY.tsv": {
            "headers": list(LINEAGE_COLUMNS), "rows": lineage_rows
        },
        "07_CURATORIAL_ATTENUATION_EXPERIMENTS.tsv": {
            "headers": list(curatorial_headers), "rows": curatorial_rows
        },
        "10_MODEL_BENCHMARK_RESULTS.tsv": model_spec,
        "11_CANDIDATE_RECALL_RESULTS.tsv": candidate_spec,
        "12_SOURCE_BIAS_AND_FAMILY_DOMINANCE.tsv": {
            "headers": [target for target, _ in bias_mapping], "rows": bias_rows
        },
        "13_HUBNESS_ANALYSIS.tsv": {
            "headers": [target for target, _ in hub_mapping], "rows": hub_rows
        },
        "14_ABLATION_AND_STABILITY.tsv": {
            "headers": [target for target, _ in ablation_mapping], "rows": ablation_rows
        },
        "15_INTERACTION_STATISTICS_REVIEW.tsv": {
            "headers": [target for target, _ in interaction_mapping], "rows": interaction_rows
        },
        "16_MECHANICAL_EXPECTATION_CASES.tsv": {
            "headers": list(mechanical_headers), "rows": mechanical_rows
        },
        "17_HUMAN_REVIEW_PACKET.tsv": {
            "headers": [target for target, _ in human_mapping], "rows": human_rows
        },
        "19_ANALYSIS_RUN_REGISTER.tsv": {
            "headers": ["receipt_json"],
            "rows": [{"receipt_json": _compact_cell(row)} for row in run_rows],
        },
    }
    if set(native_specs) != set(TSV_FILES):
        raise AssertionError("internal TSV row-spec registry changed")
    return {
        filename: {
            "schemaVersion": ROW_SPEC_SCHEMA_VERSION,
            "outputFilename": filename,
            "sourceBenchmarkSha256": benchmark_sha256,
            "headers": spec["headers"],
            "rows": spec["rows"],
            "rowCount": len(spec["rows"]),
        }
        for filename, spec in native_specs.items()
    }


def _central_summary(
    central: Mapping[str, Any],
    lineage: Mapping[str, Any],
    basis: Mapping[str, Any],
    row_specs: Mapping[str, Mapping[str, Any]],
    semantic: Mapping[str, str],
    benchmark_sha256: str,
    research_receipts: Mapping[str, Mapping[str, Any]] | None,
) -> dict[str, Any]:
    counts = _mapping(lineage.get("counts"), "lineage counts")
    candidates = _mapping(central.get("candidates"), "central candidates")
    candidate_pool = _mapping(candidates.get("pool"), "selected candidate pool")
    candidate_recall = _mapping(candidates.get("recall"), "selected candidate recall")
    models = _mapping(central.get("models"), "central models")
    curatorial = _mapping(central.get("curatorial"), "central curatorial")
    missingness = _mapping(central.get("missingness"), "central missingness")
    interactions = _mapping(central.get("interactions"), "central interactions")
    hubness = _mapping(central.get("hubness"), "central hubness")
    ablation = _mapping(central.get("ablation"), "central ablation")
    evaluation = _mapping(central.get("evaluation"), "central evaluation")
    mechanical = _mapping(evaluation.get("mechanical"), "central mechanical")
    explanations = _mapping(central.get("explanations"), "central explanations")
    human = _mapping(central.get("humanReview"), "central human review")
    runs = _mapping(central.get("runs"), "central runs")
    performance = _mapping(central.get("performance"), "central performance")
    integrity = _mapping(central.get("integrity"), "central integrity")
    boundaries = _mapping(central.get("boundaries"), "central boundaries")
    source_receipt = _mapping(central.get("sourceReceipt"), "central source receipt")
    shortlist = list(map(str, central.get("shortlistModelIds", ())))
    model_rows = row_specs["10_MODEL_BENCHMARK_RESULTS.tsv"]["rows"]
    ablation_rows = row_specs["14_ABLATION_AND_STABILITY.tsv"]["rows"]

    def recall(k: int) -> float:
        row = _mapping(candidate_recall.get(str(k)), f"candidate recall@{k}")
        value = _number(row.get("minimum"), f"minimum candidate recall@{k}")
        if not 0 <= value <= 1:
            raise EvidencePreparationError(f"candidate recall@{k} escapes [0,1]")
        return value

    output: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "sourceBenchmarkSchemaVersion": central.get("schemaVersion"),
        "sourceBenchmarkImplementationVersion": central.get("implementationVersion"),
        "sourceBenchmarkSha256": benchmark_sha256,
        "sourceBenchmarkDeterministicPayloadSha256": central.get("deterministicPayloadSha256"),
        "sourceCommit": central["sourceCommit"],
        "researchReleaseId": source_receipt.get("researchReleaseId"),
        "researchReleaseSha256": source_receipt.get("researchManifestSha256"),
        "researchManifestSha256": source_receipt.get("researchManifestSha256"),
        "contextProjectionId": source_receipt.get("contextProjectionId"),
        "contextProjectionSha256": source_receipt.get("contextProjectionSha256"),
        "spacetimeProjectionId": source_receipt.get("spacetimeProjectionId"),
        "spacetimeProjectionSha256": source_receipt.get("spacetimeProjectionSha256"),
        "explorationSignalRegistrySha256": source_receipt.get("explorationSignalRegistrySha256"),
        "publicObjectCount": PUBLIC_OBJECT_COUNT,
        "heldExplorationObjectCount": 0,
        "exhaustivePairCount": EXHAUSTIVE_PAIR_COUNT,
        "explorationSignalInputCount": counts["signalInputCount"],
        "signalLineageClassifiedCount": counts["signalLineageClassifiedCount"],
        "signalLineageUnclassifiedCount": counts["signalLineageUnclassifiedCount"],
        "independentBaseSignalCount": counts["independentBaseSignalCount"],
        "dependentInteractionSignalCount": counts["dependentInteractionSignalCount"],
        "candidateGenerationOnlySignalCount": counts["candidateGenerationOnlySignalCount"],
        "comparabilityOnlySignalCount": counts["comparabilityOnlySignalCount"],
        "explanationOnlySignalCount": counts["explanationOnlySignalCount"],
        "diagnosticOnlySignalCount": counts["diagnosticOnlySignalCount"],
        "rejectedScoringSignalCount": counts["rejectedScoringSignalCount"],
        "sameSourceFactGroupCount": counts["sameSourceFactGroupCount"],
        "sameSourceFactDoubleScoreCount": counts["sameSourceFactDoubleScoreCount"],
        "rawCuratedJaccardImportBoundary": boundaries.get("rawCuratedJaccardImportBoundary"),
        "rawCuratedJaccardProductionEligible": False,
        "candidateGeneratorVariantCount": candidates["variantCount"],
        "candidateArchitectureSelected": candidates["candidateArchitectureSelected"],
        "selectedCandidateVariant": candidates["selectedVariant"],
        "selectedCandidatePoolP50": candidate_pool["p50"],
        "selectedCandidatePoolP95": candidate_pool["p95"],
        "selectedCandidatePoolP99": candidate_pool["p99"],
        "selectedCandidatePoolMax": candidate_pool["max"],
        "selectedCandidateRecallAt10": recall(10),
        "selectedCandidateRecallAt20": recall(20),
        "selectedCandidateRecallAt50": recall(50),
        "zeroCandidateObjectCount": candidate_pool["zeroCount"],
        "nearFullCorpusCandidateObjectCount": candidate_pool["nearFullCount"],
        "modelIds": list(MODEL_IDS),
        "modelVariantCount": len({str(row["variant_id"]) for row in model_rows}),
        "modelDecision": central["modelDecision"],
        "shortlistModelIds": shortlist,
        "modelShortlistCount": len(shortlist),
        "curatorialAttenuationVariantCount": curatorial["variantCount"],
        "curatorialResidualSignalCount": curatorial["residualSignalCount"],
        "curatorialAsRecallIndex": curatorial["asRecallIndex"],
        "curatorialAsIndependentScore": curatorial["asIndependentScore"],
        "curatorialParentDuplicationFailureCount": curatorial["parentDuplicationFailures"],
        "missingnessVariantCount": missingness["missingnessVariantCount"],
        "missingnessVariantIds": ["MISSING-A", "MISSING-B", "MISSING-C", "MISSING-D"],
        "comparabilityP50": missingness["comparabilityDistribution"]["p50"],
        "comparabilityP95": missingness["comparabilityDistribution"]["p95"],
        "interactionMethodCount": interactions["interactionMethodCount"],
        "interactionSupportThresholdCount": interactions["supportThresholdCount"],
        "hubnessKValues": list(K_VALUES),
        "hubnessCorrectionTested": hubness["correctionTested"],
        "hubnessCorrectionSelected": hubness["correctionSelected"],
        "mechanicalAxiomCount": mechanical["axiomCount"],
        "mechanicalAxiomFailureCount": mechanical["axiomFailureCount"],
        "ablationVariantCount": len(
            {(str(row["model_id"]), str(row["ablation_id"])) for row in ablation_rows}
        ),
        "pathologicalAnchorCount": evaluation["pathologicalAnchorCount"],
        "humanReviewPacketAnchorCount": human["anchorCount"],
        "humanReviewPacketReady": human["humanReviewPacketReady"],
        "humanReviewCompleted": human["humanReviewCompleted"],
        "analysisRunCount": runs["analysisRunCount"],
        "analysisRunReceiptFailureCount": runs["receiptFailureCount"],
        **semantic,
        "candidateIndexBuildMs": performance["candidateIndexBuildMs"],
        "candidateIndexBytes": performance["candidateIndexBytes"],
        "candidateIndexHeapBytes": performance["candidateIndexHeapBytes"],
        "exhaustiveModelBenchmarkMs": performance["exhaustiveModelBenchmarkMs"],
        "objectLocalQueryP50Ms": performance["objectLocalQueryP50Ms"],
        "objectLocalQueryP95Ms": performance["objectLocalQueryP95Ms"],
        "peakHeapBytes": performance["peakHeapBytes"],
        "peakRssBytes": performance["peakRssBytes"],
        "sharedUnknownPositiveCreditCount": missingness["sharedUnknownPositiveCreditCount"],
        "notApplicableAsMissingCount": missingness["notApplicableAsMissingCount"],
        "lowSupportInflationFailureCount": interactions["lowSupportInflationFailureCount"],
        "interactionParentDoubleCountFailures": interactions[
            "interactionParentDoubleCountFailures"
        ],
        "unexplainedShortlistResultCount": explanations["unexplainedShortlistResultCount"],
        "explanationCount": explanations["explanationCount"],
        "explanationRowsSha256": explanations["explanationRowsSha256"],
        "scoreOnlyResultCount": explanations["scoreOnlyResultCount"],
        "historicalRelationCount": explanations["historicalRelationCount"],
        "semanticRelationCount": explanations["semanticRelationCount"],
        "probabilityCount": explanations["probabilityCount"],
        "internalUuidExposureCount": integrity["internalUuidExposureCount"],
        "databaseFilesChanged": integrity["databaseFilesChanged"],
        "searchFilesChanged": integrity["searchFilesChanged"],
        "publicSimilarityModelSelected": False,
        "publicSimilarityWeightsSelected": False,
        "probabilityModelSelected": False,
        "clusteringModelSelected": False,
        "randomnessAffectsAffinity": False,
        "randomnessAffectsCandidateSet": False,
        "fullPairMatrixCommitted": False,
        "fullPairMatrixInClient": False,
        "canonicalReleaseChanged": integrity["canonicalReleaseChanged"],
        "contextSemanticsChanged": integrity["contextSemanticsChanged"],
        "contextGovernanceChanged": integrity["contextGovernanceChanged"],
        "contextPublicProjectionChanged": False,
        "spacetimeGovernanceChanged": integrity["spacetimeGovernanceChanged"],
        "spacetimePublicProjectionChanged": False,
        "publicExplorationApiAdded": boundaries["publicExplorationApiAdded"],
        "publicExplorationRouteAdded": boundaries["publicExplorationRouteAdded"],
        "explorationRendererImplemented": boundaries["explorationRendererImplemented"],
        "explorationTemplateRegistryFrozen": boundaries["explorationTemplateRegistryFrozen"],
        "comparabilityChannelImplemented": missingness["comparabilityChannelImplemented"],
        "explanationContractReady": explanations["explanationContractReady"],
        "contributionSchemaValid": explanations["contributionSchemaValid"],
        "curatorialHistoricalRelationCount": 0,
        "geographicLayoutDistanceScoreCount": mechanical[
            "geographicLayoutDistanceScoreCount"
        ],
        "sameSourcePositiveAffinityDefault": False,
        "researchOutputReceiptsBound": research_receipts is not None,
    }
    if research_receipts is not None:
        output["researchOutputReceipts"] = deepcopy(dict(research_receipts))
    output["preparationSha256"] = _sha256_json(output)
    return output


def build_evidence(
    central: Mapping[str, Any],
    *,
    benchmark_sha256: str,
    research_receipts: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Build raw receipts and TSV row specs without writing final artifacts."""

    lineage, basis = _regenerate_lineage_and_basis(central)
    semantic = _semantic_receipts(central)
    row_specs = _build_row_specs(central, lineage, benchmark_sha256)
    models = _mapping(central.get("models"), "central models")
    candidates = _mapping(central.get("candidates"), "central candidates")
    shortlist = set(map(str, central.get("shortlistModelIds", ())))
    explanations = _mapping(central.get("explanations"), "central explanations")
    human = _mapping(central.get("humanReview"), "central human review")
    runs = _mapping(central.get("runs"), "central runs")
    explanation_rows = _rows(explanations.get("explanationRows"), "standalone explanations")
    if _integer(explanations.get("explanationCount"), "explanation count") != len(
        explanation_rows
    ) or explanations.get("explanationRowsSha256") != _sha256_json(explanation_rows):
        raise EvidencePreparationError("standalone explanation count/digest does not reconcile")
    posting_receipt = _mapping(
        candidates.get("interactionPostingReceipt"), "candidate interaction-posting receipt"
    )
    interactions = _mapping(central.get("interactions"), "central interactions")
    interaction_registry_sha256 = _sha(
        interactions.get("registrySha256"), "interaction registry digest"
    )
    trusted_interaction_context_sha256 = _sha(
        interactions.get("trustedInteractionContextSha256"),
        "trusted interaction-context digest",
    )
    if _sha(posting_receipt.get("registrySha256"), "posting registry digest") != interaction_registry_sha256:
        raise EvidencePreparationError("candidate postings and interaction registry digests differ")
    if _sha(posting_receipt.get("contextSha256"), "posting context digest") != trusted_interaction_context_sha256:
        raise EvidencePreparationError("candidate postings and trusted interaction context differ")
    for field in (
        "invalidDenominatorCount",
        "supportExceedsDenominatorCount",
        "nonPositiveExcessResidualCount",
        "gridReconciliationFailureCount",
        "scorerCapReconciliationFailureCount",
        "interactionParentDoubleCountFailures",
        "lowSupportInflationFailureCount",
    ):
        if _integer(interactions.get(field), f"interaction {field}") != 0:
            raise EvidencePreparationError(f"interaction semantic guard reports {field}")
    if interactions.get("jointObservableDenominatorPolicy") != "ALL_DIMENSIONS_OBSERVED":
        raise EvidencePreparationError("interaction denominator policy changed")
    if interactions.get("positiveExcessAssociationRequired") is not True:
        raise EvidencePreparationError("interaction positive-excess gate is absent")
    registry_cell_count = _integer(interactions.get("registryCellCount"), "registry cell count")
    if (
        registry_cell_count <= 0
        or _integer(interactions.get("observedPairCellCount"), "pair-cell count")
        + _integer(interactions.get("observedTripleCellCount"), "triple-cell count")
        != registry_cell_count
    ):
        raise EvidencePreparationError("interaction registry cell counts do not reconcile")
    residual_rows = _rows(interactions.get("residualRows"), "interaction residual rows")
    residual_keys = {
        (str(row.get("method", "")), _integer(row.get("supportThreshold"), "residual threshold"))
        for row in residual_rows
    }
    if residual_keys != {
        (method, threshold)
        for method in RESIDUAL_INTERACTION_METHODS
        for threshold in SUPPORT_THRESHOLDS
    } or len(residual_rows) != 20:
        raise EvidencePreparationError("interaction residual grid is incomplete")
    scorer_rows = _rows(interactions.get("scorerExperimentRows"), "interaction scorer rows")
    if {str(row.get("interactionPolicy", "")) for row in scorer_rows} != set(
        RESIDUAL_INTERACTION_METHODS
    ) or len(scorer_rows) != len(RESIDUAL_INTERACTION_METHODS):
        raise EvidencePreparationError("interaction scorer experiment omits a declared policy")
    scorer_pair_count = _integer(
        interactions.get("scorerExperimentPairCount"), "interaction scorer pair count"
    )
    if scorer_pair_count <= 0 or any(
        _integer(row.get("evaluatedPairCount"), "interaction scorer row pair count")
        != scorer_pair_count
        for row in scorer_rows
    ):
        raise EvidencePreparationError("interaction scorer pair populations do not reconcile")
    run_rows = _rows(runs.get("rows"), "analysis-run rows")
    for receipt in run_rows:
        if receipt.get("candidateIndexSha256") != semantic["candidateIndexSha256"]:
            raise EvidencePreparationError("an analysis run changed the candidate-index digest")
        parameters = _mapping(receipt.get("parameterSet"), "analysis-run parameterSet")
        for field in (
            "scoringRecordsSha256",
            "modelContextSha256",
            "compiledFeatureContextSha256",
        ):
            if parameters.get(field) != semantic[field]:
                raise EvidencePreparationError(f"an analysis run changed {field}")
    explanation_validation = {
        key: deepcopy(value)
        for key, value in explanations.items()
        if key not in {"explanationRows", "explanationValidationRows"}
        and not key.endswith("Ms")
    }
    raw: dict[str, dict[str, Any]] = {
        "exploration-similarity-evaluation-summary.json": _central_summary(
            central,
            lineage,
            basis,
            row_specs,
            semantic,
            benchmark_sha256,
            research_receipts,
        ),
        "signal-lineage-summary.json": deepcopy(lineage),
        "independent-basis-summary.json": deepcopy(basis),
        "candidate-index-summary.json": {
            "schemaVersion": "trace-exploration-candidate-index-summary/v1",
            "sourceBenchmarkSha256": benchmark_sha256,
            **semantic,
            "candidateGeneratorVariantCount": candidates["variantCount"],
            "selectedCandidateVariant": candidates["selectedVariant"],
            "candidateArchitectureSelected": candidates["candidateArchitectureSelected"],
            "pairRowsMaterialized": 0,
            "randomnessAffectsCandidateSet": False,
            "interactionRegistrySha256": interaction_registry_sha256,
            "trustedInteractionContextSha256": trusted_interaction_context_sha256,
            "interactionPostingReceipt": deepcopy(posting_receipt),
            "rows": deepcopy(_shortlist_candidate_rows(candidates, shortlist)),
        },
        "model-benchmark-summary.json": {
            "schemaVersion": "trace-exploration-model-benchmark-summary/v1",
            "sourceBenchmarkSha256": benchmark_sha256,
            **{field: semantic[field] for field in (
                "scoringRecordsSha256",
                "modelContextSha256",
                "compiledFeatureContextSha256",
            )},
            "modelIds": list(MODEL_IDS),
            "modelRows": deepcopy(_rows(models.get("rows"), "model rows")),
            "explanationRows": deepcopy(explanation_rows),
            "explanationValidation": explanation_validation,
        },
        "missingness-summary.json": deepcopy(
            _mapping(central.get("missingness"), "central missingness")
        ),
        "interaction-summary.json": deepcopy(interactions),
        "hubness-summary.json": deepcopy(
            _mapping(central.get("hubness"), "central hubness")
        ),
        "ablation-summary.json": {
            **deepcopy(_mapping(central.get("ablation"), "central ablation")),
            "historicalLabelsUsed": False,
        },
        "human-review-summary.json": {
            **deepcopy(human),
            "humanReviewPacketAnchorCount": human["anchorCount"],
            "explanationRows": deepcopy(explanation_rows),
            "explanationValidation": deepcopy(explanation_validation),
        },
        "performance-summary.json": deepcopy(
            _mapping(central.get("performance"), "central performance")
        ),
        "analysis-run-summary.json": {
            **deepcopy(runs),
            "schemaVersion": "trace-exploration-analysis-run-register/v1",
        },
        "security-summary.json": {
            **deepcopy(_mapping(central.get("boundaries"), "central boundaries")),
            **deepcopy(_mapping(central.get("integrity"), "central integrity")),
            "sourceCommit": central["sourceCommit"],
            "publicObjectCount": central["publicObjectCount"],
            "heldExplorationObjectCount": central["heldExplorationObjectCount"],
            "fullPairMatrixCommitted": False,
            "fullPairMatrixInClient": False,
        },
    }
    if set(raw) != set(RAW_FILES) or set(row_specs) != set(TSV_FILES):
        raise AssertionError("evidence output registry changed")
    total_raw_bytes = 0
    for filename, value in raw.items():
        _validate_bounded(value, filename)
        size = len(_canonical_bytes(value, pretty=True))
        if size > 16 * 1024 * 1024:
            raise EvidencePreparationError(f"{filename} exceeds the 16 MiB raw receipt bound")
        total_raw_bytes += size
    if total_raw_bytes > 64 * 1024 * 1024:
        raise EvidencePreparationError("raw evidence package exceeds the 64 MiB aggregate bound")
    for filename, value in row_specs.items():
        _validate_bounded(value, filename)
    return raw, row_specs


def prepare(
    *,
    benchmark_path: Path,
    output_dir: Path,
    research_dir: Path | None = None,
) -> dict[str, Any]:
    """Prepare the exact evidence file set in ``output_dir``."""

    benchmark_path = benchmark_path.resolve()
    output_dir = output_dir.resolve()
    if output_dir == ROOT or output_dir == Path("/"):
        raise EvidencePreparationError("output directory must be a dedicated explicit directory")
    central, benchmark_sha256 = _load_central(benchmark_path)
    receipts = _research_receipts(research_dir) if research_dir is not None else None
    raw, row_specs = build_evidence(
        central,
        benchmark_sha256=benchmark_sha256,
        research_receipts=receipts,
    )
    raw_dir = output_dir / "raw"
    spec_dir = output_dir / "tsv-row-specs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    spec_dir.mkdir(parents=True, exist_ok=True)
    expected_raw = set(RAW_FILES)
    expected_specs = {name.replace(".tsv", ".row-spec.json") for name in TSV_FILES}
    unexpected_raw = {path.name for path in raw_dir.iterdir() if path.is_file()} - expected_raw
    unexpected_specs = {path.name for path in spec_dir.iterdir() if path.is_file()} - expected_specs
    if unexpected_raw or unexpected_specs:
        raise EvidencePreparationError(
            f"output directories contain unexpected files; raw={sorted(unexpected_raw)}, "
            f"rowSpecs={sorted(unexpected_specs)}"
        )
    raw_bytes = {
        filename: _atomic_json(raw_dir / filename, raw[filename]) for filename in RAW_FILES
    }
    spec_bytes = {}
    for filename in TSV_FILES:
        spec_name = filename.replace(".tsv", ".row-spec.json")
        spec_bytes[spec_name] = _atomic_json(spec_dir / spec_name, row_specs[filename])
    actual_raw = {path.name for path in raw_dir.iterdir() if path.is_file()}
    actual_specs = {path.name for path in spec_dir.iterdir() if path.is_file()}
    if actual_raw != expected_raw or actual_specs != expected_specs:
        raise EvidencePreparationError("written evidence paths do not match the exact output contract")
    return {
        "status": "PASS",
        "schemaVersion": SCHEMA_VERSION,
        "benchmarkSha256": benchmark_sha256,
        "outputDirectory": str(output_dir),
        "rawJsonCount": len(raw_bytes),
        "rawJsonBytes": sum(raw_bytes.values()),
        "tsvRowSpecCount": len(spec_bytes),
        "tsvRowSpecBytes": sum(spec_bytes.values()),
        "researchOutputReceiptsBound": receipts is not None,
    }


def _self_test_central(lineage: Mapping[str, Any], basis: Mapping[str, Any]) -> dict[str, Any]:
    digest = lambda value: hashlib.sha256(value.encode()).hexdigest()
    semantic = {
        "index": digest("index"),
        "scoring": digest("scoring"),
        "context": digest("context"),
        "compiled": digest("compiled"),
        "interactionRegistry": digest("interaction-registry"),
        "interactionContext": digest("interaction-context"),
    }
    model_rows = [
        {
            "modelId": model,
            "variantId": f"{model}-SELF-TEST",
            "modelFamily": f"SELF_TEST_{model}",
            "task": "SELF_TEST",
            "symmetric": model != "M7",
            "shortlistEligible": model in {"M2", "M5", "M7"},
            "rankingSha256": digest(f"ranking-{model}"),
            "pairRowsRetained": 0,
            "fullPairMatrixMaterialized": False,
            "productionEligible": False,
        }
        for model in MODEL_IDS
    ]
    candidate_rows = []
    for variant in CANDIDATE_VARIANTS:
        # Include two non-shortlist internal references so the self-test proves
        # the evidence boundary filters them from committed candidate outputs.
        for model in ("M0", "M1", "M2", "M5", "M7"):
            for k in K_VALUES:
                candidate_rows.append(
                    {
                        "candidateVariant": variant,
                        "referenceModelId": model,
                        "referenceVariantId": f"{model}-SELF-TEST",
                        "k": k,
                        "recall": 1.0,
                        "candidatePoolP50": 100,
                        "candidatePoolP90": 150,
                        "candidatePoolP95": 200,
                        "candidatePoolP99": 250,
                        "candidatePoolMax": 300,
                        "candidateReductionP50": 0.98,
                        "zeroCandidateObjectCount": 0,
                        "nearFullCorpusCandidateObjectCount": 0,
                        "candidateGenerationP50Ms": 1,
                        "candidateGenerationP95Ms": 2,
                        "candidateSetsSha256": digest(f"candidates-{variant}-{model}"),
                    }
                )
    curatorial_rows = []
    for policy in CURATORIAL_POLICIES:
        ratios = (0.25, 0.50, 0.75, 0.90) if policy == "CUR-W3" else ("N/A",)
        for ratio in ratios:
            curatorial_rows.append(
                {
                    "policy_id": policy,
                    "sensitivity_id": f"{policy}-{ratio}",
                    "policy_name": policy,
                    "role": "RECALL_SUBSTRATE",
                    "weight_rule": "SELF_TEST",
                    "posting_space": "RAW_RECALL",
                    "alpha": 1,
                    "broad_stop_ratio": ratio,
                    "rare_support_floor": 5,
                    "family_cap": 0.1,
                    "container_posting_count": 1,
                    "active_posting_count": 1,
                    "stopped_posting_count": 0,
                    "candidate_pool_p50": 100,
                    "candidate_pool_p90": 150,
                    "candidate_pool_p95": 200,
                    "candidate_pool_p99": 250,
                    "candidate_pool_max": 300,
                    "zero_candidate_object_count": 0,
                    "near_full_candidate_object_count": 0,
                    "weight_min": 1,
                    "weight_p50": 1,
                    "weight_max": 1,
                    "score_contribution": 0,
                    "score_contribution_basis": "NONE",
                    "residual_signal_count": 0,
                    "raw_membership_scoring_allowed": False,
                    "same_source_parent_duplication_failures": 0,
                    "broad_dominance_failures": 0,
                    "randomness_affects_candidate_set": False,
                    "historical_relation": False,
                    "semantic_relation": False,
                    "probability": False,
                }
            )
    hub_rows = [
        {
            "modelId": model, "variantId": f"{model}-SELF-TEST", "k": k,
            "objectCount": PUBLIC_OBJECT_COUNT, "queryCount": PUBLIC_OBJECT_COUNT,
            "mean": k, "variance": 1, "skewness": 0, "gini": 0.1,
            "top1PercentOccurrenceShare": 0.02, "maximumOccurrence": k + 1,
            "zeroOccurrenceObjectCount": 0, "totalOccurrenceCount": PUBLIC_OBJECT_COUNT * k,
        }
        for model in SCALAR_MODEL_IDS for k in K_VALUES
    ]
    bias_rows = [
        {
            "modelId": model, "variantId": f"{model}-SELF-TEST", "k": 20,
            "queryCount": PUBLIC_OBJECT_COUNT, "resultTop1SourceShare": 0.2,
            "resultHhi": 0.1, "crossSourceRate": 0.8,
            "evaluatedResultCount": PUBLIC_OBJECT_COUNT * 20,
            "medianMaximumFamilyShare": 0.4, "p95MaximumFamilyShare": 0.5,
            "oneFamilyOver80PercentRate": 0, "sourceDominatedQueryRate": 0,
            "curationDominatedQueryRate": 0, "sameSourceIsHistoricalRelation": False,
            "diagnosticOnly": True,
        }
        for model in MODEL_IDS
    ]
    ablation_rows = [
        {
            "modelId": model, "baseVariantId": f"{model}-SELF-TEST",
            "ablationId": f"ABL-{variant_ordinal:02d}",
            "ablationFamily": ABLATION_FAMILIES[variant_ordinal % len(ABLATION_FAMILIES)],
            "k": k, "queryCount": 72, "meanTopKOverlap": 1,
            "minimumTopKOverlap": 1, "meanRankCorrelation": 1,
            "minimumRankCorrelation": 1, "scoringEffect": "SELF_TEST",
            "learnedWeightsUsed": False,
        }
        for model in MODEL_IDS[1:] for variant_ordinal in range(27) for k in K_VALUES
    ]
    interaction_rows = [
        {
            "method": method, "supportThreshold": threshold,
            "eligibleObservedCellCount": 12, "lowSupportCellsExcluded": 0,
            "statisticP50": 0.1, "statisticP95": 0.2, "statisticMax": 0.3,
            "parentContributionRepeated": False, "rareMeansImportant": False,
        }
        for method in INTERACTION_METHODS for threshold in SUPPORT_THRESHOLDS
    ]
    residual_rows = [
        {
            "method": method, "supportThreshold": threshold, "cellCount": 12,
            "residualP50": 0, "residualP95": 0, "residualMax": 0, "cap": 0.1,
            "positiveExcessAssociationRequired": True,
            "positiveExcessEligibleCellCount": 4, "positiveResidualCellCount": 0,
            "nonPositiveExcessResidualCount": 0,
        }
        for method in RESIDUAL_INTERACTION_METHODS for threshold in SUPPORT_THRESHOLDS
    ]
    scorer_rows = [
        {
            "interactionPolicy": method,
            "anchorCount": 72,
            "evaluatedPairCount": 500,
            "meanTop20Overlap": 1,
            "meanTop20RankCorrelation": 1,
            "scoreDeltaP50": 0,
            "scoreDeltaP95": 0,
            "directScorerSensitivity": True,
        }
        for method in RESIDUAL_INTERACTION_METHODS
    ]
    mechanical_rows = [
        {
            "axiom_id": f"AX-{index:03d}", "rule": "self-test",
            "expected_invariant": "self-test", "model_applicability": "ALL",
            "tested_model_ids": "M2,M5,M7", "model_result_summary": "PASS",
            "observed_result": "PASS", "status": "PASS", "failure_count": 0,
            "failed_model_ids": "NONE", "case_sha256": digest(f"axiom-{index}"),
            "historical_relation": "false", "semantic_relation": "false", "probability": "false",
        }
        for index in range(1, 16)
    ]
    public_ids = [f"SURF-SELF-{index:03d}" for index in range(100)]
    human_rows = []
    explanation_rows = []
    for anchor_index, anchor in enumerate(public_ids[:72]):
        for ordinal in range(1, 4):
            candidate = public_ids[(anchor_index + ordinal) % len(public_ids)]
            human_rows.append(
                {
                    "packetRowId": f"HR-{anchor_index:03d}-PROFILE-1-{ordinal}",
                    "anchorPublicId": anchor, "anchorTitle": anchor,
                    "anchorSelectionStrata": "SELF_TEST", "blindProfileSlot": "PROFILE-1",
                    "candidateOrdinal": ordinal, "candidatePublicId": candidate,
                    "candidateTitle": candidate, "retrievalReasons": "context:self-test",
                    "sharedIndependentSignals": "context:self-test", "distinctiveSignals": "",
                    "unavailableFamilies": "", "comparabilityRatio": 1,
                    "anchorSourceName": "Source A", "candidateSourceName": "Source B",
                    "sourceComposition": "CROSS_GOVERNED_SOURCE_NAME", "sourceBiasNotes": "",
                    "interactionEvidence": "", "usefulForFurtherExploration": "",
                    "explanationIntelligible": "", "merelyBroadCategory": "",
                    "newDefensibleResearchDirection": "", "accidentalRelationSuggestion": "",
                    "reviewerNotes": "", "humanReviewCompleted": False,
                    "historicalRelation": False, "semanticRelation": False, "probability": False,
                }
            )
            explanation_rows.append({"queryId": anchor, "candidateId": candidate})
    runs = [
        {
            "schemaVersion": "trace-exploration-analysis-run-receipt/v1",
            "modelId": model, "modelFamily": f"SELF_TEST_{model}",
            "implementationVersion": "self-test",
            "parameterSet": {
                "scoringRecordsSha256": semantic["scoring"],
                "modelContextSha256": semantic["context"],
                "compiledFeatureContextSha256": semantic["compiled"],
            },
            "sourceCommit": SOURCE_SHA, "analysisRunId": f"SELF-RUN-{model}",
            "candidateIndexSha256": semantic["index"],
        }
        for model in MODEL_IDS
    ]
    return {
        "schemaVersion": "self-test", "implementationVersion": "self-test",
        "sourceCommit": SOURCE_SHA, "sourceReceipt": common.source_receipt(),
        "publicObjectCount": PUBLIC_OBJECT_COUNT, "heldExplorationObjectCount": 0,
        "exhaustivePairCount": EXHAUSTIVE_PAIR_COUNT,
        "scoringRecordsSha256": semantic["scoring"],
        "modelContextSha256": semantic["context"],
        "compiledFeatureContextSha256": semantic["compiled"],
        "modelDecision": "MODEL_FAMILY_SHORTLISTED",
        "shortlistModelIds": ["M2", "M5", "M7"],
        "lineage": {
            "signalsSha256": lineage["signalsSha256"],
            "receiptSha256": lineage["deterministicReceipt"]["sha256"],
        },
        "basis": {
            "basisRowsSha256": basis["basisRowsSha256"],
            "receiptSha256": basis["deterministicReceipt"]["sha256"],
        },
        "candidates": {
            "variantCount": 6, "selectedVariant": "CG-CUR-4",
            "candidateArchitectureSelected": True,
            "pool": {"p50": 100, "p95": 200, "p99": 250, "max": 300,
                     "zeroCount": 0, "nearFullCount": 0},
            "recall": {str(k): {"minimum": 1, "mean": 1} for k in K_VALUES},
            "rows": candidate_rows, "indexSha256": semantic["index"],
            "interactionPostingReceipt": {
                "registrySha256": semantic["interactionRegistry"],
                "contextSha256": semantic["interactionContext"],
            },
        },
        "models": {"rows": model_rows},
        "curatorial": {
            "variantCount": 6, "residualSignalCount": 0, "asRecallIndex": True,
            "asIndependentScore": False, "parentDuplicationFailures": 0,
            "rows": curatorial_rows,
        },
        "missingness": {
            "missingnessVariantCount": 4, "comparabilityChannelImplemented": True,
            "comparabilityDistribution": {"p50": 1, "p95": 1},
            "sharedUnknownPositiveCreditCount": 0, "notApplicableAsMissingCount": 0,
        },
        "interactions": {
            "interactionMethodCount": 8, "supportThresholdCount": 5,
            "observedPairCellCount": 8, "observedTripleCellCount": 4,
            "registryCellCount": 12, "jointObservableDenominatorPolicy": "ALL_DIMENSIONS_OBSERVED",
            "invalidDenominatorCount": 0, "supportExceedsDenominatorCount": 0,
            "positiveExcessAssociationRequired": True, "nonPositiveExcessResidualCount": 0,
            "expectedMethodGridRowCount": 40, "observedMethodGridRowCount": 40,
            "expectedResidualGridRowCount": 20, "observedResidualGridRowCount": 20,
            "gridReconciliationFailureCount": 0, "rows": interaction_rows,
            "residualRows": residual_rows, "lowSupportInflationFailureCount": 0,
            "interactionParentDoubleCountFailures": 0,
            "scorerCapReconciliationFailureCount": 0,
            "registrySha256": semantic["interactionRegistry"],
            "trustedInteractionContextSha256": semantic["interactionContext"],
            "scorerExperimentRows": scorer_rows,
            "scorerExperimentPairCount": 500,
        },
        "hubness": {"rows": hub_rows, "biasRows": bias_rows,
                    "correctionTested": True, "correctionSelected": False},
        "ablation": {"rows": ablation_rows},
        "evaluation": {
            "pathologicalAnchorCount": 15,
            "mechanical": {"axiomCount": 15, "axiomFailureCount": 0,
                           "geographicLayoutDistanceScoreCount": 0, "rows": mechanical_rows},
        },
        "explanations": {
            "explanationContractReady": True, "standaloneSemanticValidationPassed": True,
            "contributionSchemaValid": True, "explanationCount": len(explanation_rows),
            "retrievalPathCount": len(explanation_rows),
            "affinityEvidencePathCount": len(explanation_rows),
            "comparabilityValidCount": len(explanation_rows),
            "provenancePinnedCount": len(explanation_rows), "invalidExplanationCount": 0,
            "unexplainedShortlistResultCount": 0,
            "explanationRowsSha256": _sha256_json(explanation_rows),
            "scoreOnlyResultCount": 0, "historicalRelationCount": 0,
            "semanticRelationCount": 0, "probabilityCount": 0,
            "explanationRows": explanation_rows, "explanationValidationRows": [],
        },
        "humanReview": {
            "anchorCount": 72, "rows": human_rows, "humanReviewPacketReady": True,
            "humanReviewCompleted": False,
        },
        "runs": {"analysisRunCount": 9, "receiptFailureCount": 0,
                 "registerSha256": digest("runs"), "rows": runs},
        "performance": {
            "candidateIndexBuildMs": 1, "candidateIndexBytes": 1,
            "candidateIndexHeapBytes": 1, "exhaustiveModelBenchmarkMs": 1,
            "objectLocalQueryP50Ms": 1, "objectLocalQueryP95Ms": 1,
            "peakHeapBytes": 1, "peakRssBytes": 1,
            "fullPairMatrixCommitted": False, "fullPairMatrixInClient": False,
        },
        "integrity": {
            "internalUuidExposureCount": 0, "databaseFilesChanged": 0,
            "searchFilesChanged": 0, "canonicalReleaseChanged": False,
            "contextSemanticsChanged": False, "contextGovernanceChanged": False,
            "spacetimeGovernanceChanged": False,
        },
        "boundaries": {
            "rawCuratedJaccardImportBoundary": "PASS",
            "publicExplorationApiAdded": False, "publicExplorationRouteAdded": False,
            "explorationRendererImplemented": False,
            "explorationTemplateRegistryFrozen": False,
        },
        "randomnessAffectsAffinity": False, "randomnessAffectsCandidateSet": False,
        "publicSimilarityModelSelected": False, "publicSimilarityWeightsSelected": False,
        "probabilityModelSelected": False, "clusteringModelSelected": False,
    }


def self_test() -> dict[str, Any]:
    signal_input = common.load_signal_registry()
    geography_registry = common.load_json(ROOT / signal_lineage.SPACETIME_GEOGRAPHY)
    lineage = signal_lineage.analyze_signal_lineage(
        signal_input["rows"],
        input_receipt=common.source_receipt(),
        geography_registry=geography_registry,
    )
    basis = independent_feature_basis.build_independent_feature_basis(lineage)
    central = _self_test_central(lineage, basis)
    with tempfile.TemporaryDirectory(prefix="trace-v49-evidence-prep-") as directory:
        root = Path(directory)
        benchmark = root / "benchmark.json"
        benchmark.write_bytes(_canonical_bytes(central, pretty=True))
        research = root / "research"
        research.mkdir()
        for filename in RESEARCH_FILES:
            (research / filename).write_text(f"{filename}\n", encoding="utf-8", newline="\n")
        first = prepare(
            benchmark_path=benchmark,
            output_dir=root / "first",
            research_dir=research,
        )
        second = prepare(
            benchmark_path=benchmark,
            output_dir=root / "second",
            research_dir=research,
        )
        first_files = {
            path.relative_to(root / "first"): path.read_bytes()
            for path in (root / "first").rglob("*.json")
        }
        second_files = {
            path.relative_to(root / "second"): path.read_bytes()
            for path in (root / "second").rglob("*.json")
        }
        if first_files != second_files:
            raise AssertionError("evidence preparation is not byte deterministic")
        if first["rawJsonCount"] != 13 or first["tsvRowSpecCount"] != 11:
            raise AssertionError("evidence preparation file counts changed")
        prepared_candidate = json.loads(
            (root / "first/raw/candidate-index-summary.json").read_text(encoding="utf-8")
        )
        if {
            str(row["referenceModelId"]) for row in prepared_candidate["rows"]
        } != {"M2", "M5", "M7"}:
            raise AssertionError("non-shortlist candidate references crossed the evidence boundary")
        corrupt = deepcopy(central)
        corrupt["publicObjectCount"] = PUBLIC_OBJECT_COUNT - 1
        corrupt_path = root / "corrupt.json"
        corrupt_path.write_bytes(_canonical_bytes(corrupt, pretty=True))
        try:
            prepare(benchmark_path=corrupt_path, output_dir=root / "corrupt-output")
        except EvidencePreparationError:
            pass
        else:
            raise AssertionError("corrupt public cohort was accepted")
    return {
        "status": "PASS",
        "rawJsonCount": len(RAW_FILES),
        "tsvRowSpecCount": len(TSV_FILES),
        "researchReceiptCount": len(RESEARCH_FILES),
        "deterministicReplay": True,
        "corruptionRejected": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, help="central benchmark JSON")
    parser.add_argument("--output-dir", type=Path, help="explicit evidence-preparation directory")
    parser.add_argument(
        "--research-dir",
        type=Path,
        help="optional exact 24-file research directory for final receipt binding",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), ensure_ascii=False, sort_keys=True))
        return 0
    if args.benchmark is None or args.output_dir is None:
        parser.error("--benchmark and --output-dir are required unless --self-test is used")
    result = prepare(
        benchmark_path=args.benchmark,
        output_dir=args.output_dir,
        research_dir=args.research_dir,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
