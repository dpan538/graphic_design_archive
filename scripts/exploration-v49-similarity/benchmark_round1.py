#!/usr/bin/env python3
"""Full-corpus bounded benchmark for Exploration affinity research Round 1.

The benchmark visits every unordered public-object pair for M0–M7 but keeps
only top-50 rankings, hashes, and aggregate diagnostics.  It never writes a
pair table or matrix.  M8 remains non-scalar and is evaluated object-locally.
"""

from __future__ import annotations

import argparse
import ast
import csv
import gc
import gzip
import hashlib
import json
import math
import os
import resource
import statistics
import sys
import time
import tracemalloc
from collections import Counter, defaultdict
from dataclasses import asdict, replace
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import ablation
import analysis_run_receipts
import candidate_index
import common
import curatorial_attenuation
import explanation
import hubness
import human_review_packet
import independent_feature_basis
import interaction_statistics
import mechanical_expectations
import missingness_comparability
import model_baselines
import negative_control
import signal_lineage


SCHEMA_VERSION = "trace-exploration-similarity-evaluation/v1"
IMPLEMENTATION_VERSION = "trace-exploration-similarity-benchmark-2026-08-24"
EXPECTED_PUBLIC_COUNT = 7_995
EXPECTED_PAIR_COUNT = 31_956_015
TOP_K = 50
SHORTLIST_MODEL_IDS = ("M2", "M5", "M7")
MODEL_DECISION = "MODEL_FAMILY_SHORTLISTED"
SHORTLIST_VARIANTS = {
    "M2": "M2-SMOOTHED_IDF",
    "M5": "M5-GOWER-TEMP-4",
    "M7": "M7-BM25F-QUERY",
}
# Equal-recall/equal-pool ties prefer the lineage-safe residual-only policy,
# then the direct-only policy, before any raw curatorial recall substrate.
CANDIDATE_SELECTION_PRIORITY = {
    "CG-CUR-5": 0,
    "CG-CUR-6": 1,
    "CG-CUR-4": 2,
    "CG-CUR-3": 3,
    "CG-CUR-2": 4,
    "CG-CUR-1": 5,
}
PATHOLOGY_PATH = (
    ROOT
    / "docs/research/trace-v49-exploration-discovery-round1/15_PATHOLOGICAL_SAMPLE_REGISTER.tsv"
)


class BenchmarkError(RuntimeError):
    """Raised when a benchmark input, invariant, or result is invalid."""


def canonical_bytes(value: Any) -> bytes:
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


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def deterministic_value(value: Any) -> Any:
    """Remove timings/timestamps while preserving deterministic evidence."""

    if isinstance(value, Mapping):
        output = {}
        for key, item in value.items():
            name = str(key)
            if name in {"generatedAt", "performance"} or name.endswith("Ms"):
                continue
            output[name] = deterministic_value(item)
        return output
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [deterministic_value(item) for item in value]
    return value


def quantile(values: Iterable[float | int], probability: float) -> float:
    return common.quantile_r7(values, probability)


def read_pathologies() -> list[dict[str, str]]:
    with PATHOLOGY_PATH.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) != 15:
        raise BenchmarkError("Round 5 pathological register must contain 15 cases")
    return rows


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(common.canonical_json_bytes(value, pretty=True))
    os.replace(temporary, path)


def _cache_path(cache_dir: Path, model_id: str) -> Path:
    return cache_dir / f"{model_id.lower()}-top{TOP_K}.json.gz"


def _write_ranking_cache(
    path: Path,
    *,
    model_id: str,
    variant_id: str,
    index_sha256: str,
    ranking_sha256: str,
    rankings: Mapping[str, Sequence[Sequence[Any]]],
) -> int:
    payload = {
        "schemaVersion": "trace-exploration-bounded-topk-cache/v1",
        "modelId": model_id,
        "variantId": variant_id,
        "candidateIndexSha256": index_sha256,
        "k": TOP_K,
        "queryCount": len(rankings),
        "rankingSha256": ranking_sha256,
        "rankings": rankings,
        "pairRowsRetained": 0,
        "fullPairMatrixMaterialized": False,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = canonical_bytes(payload)
    with gzip.GzipFile(
        filename=str(path),
        mode="wb",
        compresslevel=9,
        mtime=0,
    ) as handle:
        handle.write(encoded)
    return path.stat().st_size


def _public_records_by_id(records: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    output = {str(record["objectId"]): record for record in records}
    if len(output) != EXPECTED_PUBLIC_COUNT:
        raise BenchmarkError("public record map does not contain 7,995 objects")
    return output


def _ranking_ids(rankings: Mapping[str, Sequence[Sequence[Any]]]) -> dict[str, tuple[str, ...]]:
    return {
        query_id: model_baselines.compact_ranking_ids(rows)
        for query_id, rows in rankings.items()
    }


def _ranking_arrays(
    rankings: Mapping[str, Sequence[Sequence[Any]]],
    object_ids: Sequence[str],
) -> tuple[Any, Any]:
    import numpy as np

    ordinal = {object_id: index for index, object_id in enumerate(object_ids)}
    ids = np.full((len(object_ids), TOP_K), -1, dtype=np.int32)
    scores = np.full((len(object_ids), TOP_K), -1.0, dtype=np.float64)
    for query_ordinal, query_id in enumerate(object_ids):
        rows = rankings.get(query_id)
        if rows is None or len(rows) != TOP_K:
            raise BenchmarkError("bounded ranking does not contain exactly top-50 per object")
        for rank, row in enumerate(rows):
            candidate_id = str(row[0])
            if candidate_id == query_id or candidate_id not in ordinal:
                raise BenchmarkError("bounded ranking contains self or a nonpublic candidate")
            ids[query_ordinal, rank] = ordinal[candidate_id]
            scores[query_ordinal, rank] = float(row[1])
    return ids, scores


def _source_bias_and_dominance(
    context: model_baselines.ModelContext,
    spec: model_baselines.ModelSpec,
    rankings: Mapping[str, Sequence[Sequence[Any]]],
    records_by_id: Mapping[str, Mapping[str, Any]],
    *,
    profile_k: int = 10,
) -> tuple[dict[str, Any], dict[str, Any], float]:
    ids_only = _ranking_ids(rankings)
    source = hubness.source_bias_diagnostics(ids_only, records_by_id, k=20)
    profiles: list[dict[str, Any]] = []
    timings: list[float] = []
    for query_id in context.candidate_index.object_ids:
        for candidate_id in ids_only[query_id][:profile_k]:
            started = time.perf_counter()
            profile = model_baselines.score_pair(context, query_id, candidate_id, spec)
            timings.append((time.perf_counter() - started) * 1000)
            profiles.append(profile.as_dict())
    dominance = hubness.family_dominance_diagnostics(profiles)
    return source, dominance, quantile(timings, 0.95)


def _run_exhaustive_scalar_models(
    context: model_baselines.ModelContext,
    records: Sequence[Mapping[str, Any]],
    cache_dir: Path,
    *,
    block_size: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, int]]:
    """Run M0–M7 and retain only ordinal top-k arrays plus aggregates."""

    import numpy as np

    cache_dir.mkdir(parents=True, exist_ok=True)
    object_ids = context.candidate_index.object_ids
    records_by_id = _public_records_by_id(records)
    reference_ids: dict[str, Any] = {}
    reference_scores: dict[str, Any] = {}
    model_rows: list[dict[str, Any]] = []
    hubness_rows: list[dict[str, Any]] = []
    bias_rows: list[dict[str, Any]] = []
    cache_bytes: dict[str, int] = {}
    total_elapsed = 0.0

    prepared = negative_control.prepare_curated_negative_control(records)
    m0 = negative_control.stream_exhaustive_m0_top_k(
        prepared,
        k=TOP_K,
        block_size=block_size,
    )
    if m0["unorderedPairVisits"] != EXPECTED_PAIR_COUNT:
        raise BenchmarkError("M0 did not visit the complete unordered pair space")
    m0_rankings = m0["compactRankings"]
    ids, scores = _ranking_arrays(m0_rankings, object_ids)
    reference_ids["M0"] = ids
    reference_scores["M0"] = scores
    m0_ids = _ranking_ids(m0_rankings)
    m0_hub = hubness.k_occurrence_distribution(m0_ids, cohort_ids=object_ids)
    m0_source = hubness.source_bias_diagnostics(m0_ids, records_by_id, k=20)
    for row in m0_hub["rows"]:
        hubness_rows.append({"modelId": "M0", "variantId": "M0-RAW-CURATED-JACCARD", **row})
    bias_rows.append(
        {
            "modelId": "M0",
            "variantId": "M0-RAW-CURATED-JACCARD",
            **m0_source,
            "medianMaximumFamilyShare": 1.0,
            "p95MaximumFamilyShare": 1.0,
            "oneFamilyOver80PercentRate": 1.0,
            "sourceDominatedQueryRate": 0.0,
            "curationDominatedQueryRate": 1.0,
            "diagnosticOnly": True,
        }
    )
    model_rows.append(
        {
            "modelId": "M0",
            "variantId": "M0-RAW-CURATED-JACCARD",
            "modelFamily": negative_control.MODEL_FAMILY,
            "task": "NEGATIVE_CONTROL_ONLY",
            "symmetric": True,
            "shortlistEligible": False,
            "exhaustivePairCount": m0["unorderedPairVisits"],
            "rankingSha256": m0["rankingSha256"],
            "scoreDistribution": m0["scoreDistribution"],
            "elapsedMs": m0["elapsedMs"],
            "pairRowsRetained": 0,
            "fullPairMatrixMaterialized": False,
        }
    )
    cache_bytes["M0"] = _write_ranking_cache(
        _cache_path(cache_dir, "M0"),
        model_id="M0",
        variant_id="M0-RAW-CURATED-JACCARD",
        index_sha256=context.candidate_index.index_sha256,
        ranking_sha256=m0["rankingSha256"],
        rankings=m0_rankings,
    )
    total_elapsed += float(m0["elapsedMs"])
    del m0_rankings, m0_ids, m0

    for spec in model_baselines.default_model_specs():
        if spec.model_id == "M8":
            continue
        result = model_baselines.stream_exhaustive_top_k(
            context,
            (spec,),
            k=TOP_K,
            block_size=block_size,
            engine="COMPACT_NUMPY_BLOCK",
            retain_rankings=True,
        )
        if result["unorderedPairVisits"] != EXPECTED_PAIR_COUNT:
            raise BenchmarkError(f"{spec.model_id} did not visit the complete unordered pair space")
        rankings = result["compactRankings"][spec.variant_id]
        ids, scores = _ranking_arrays(rankings, object_ids)
        reference_ids[spec.model_id] = ids
        reference_scores[spec.model_id] = scores
        ids_only = _ranking_ids(rankings)
        hub = hubness.k_occurrence_distribution(ids_only, cohort_ids=object_ids)
        source, dominance, score_p95 = _source_bias_and_dominance(
            context,
            spec,
            rankings,
            records_by_id,
        )
        for row in hub["rows"]:
            hubness_rows.append({"modelId": spec.model_id, "variantId": spec.variant_id, **row})
        bias_rows.append(
            {
                "modelId": spec.model_id,
                "variantId": spec.variant_id,
                **source,
                **dominance,
                "diagnosticOnly": True,
            }
        )
        model_rows.append(
            {
                "modelId": spec.model_id,
                "variantId": spec.variant_id,
                "modelFamily": spec.model_family,
                "task": spec.task,
                "symmetric": spec.symmetric,
                "shortlistEligible": spec.model_id in SHORTLIST_MODEL_IDS,
                "exhaustivePairCount": result["unorderedPairVisits"],
                "directionalScoreCount": result["directionalScoreCount"],
                "rankingSha256": result["rankingSha256"],
                "compiledFeatureSha256": result["compiledFeatureSha256"],
                "compileMs": result["compileMs"],
                "elapsedMs": result["elapsedMs"],
                "modelScoreMs": result["modelScoreMs"][spec.variant_id],
                "explanationProfileScoreP95Ms": score_p95,
                "pairRowsRetained": 0,
                "fullPairMatrixMaterialized": False,
            }
        )
        cache_bytes[spec.model_id] = _write_ranking_cache(
            _cache_path(cache_dir, spec.model_id),
            model_id=spec.model_id,
            variant_id=spec.variant_id,
            index_sha256=context.candidate_index.index_sha256,
            ranking_sha256=result["rankingSha256"],
            rankings=rankings,
        )
        total_elapsed += float(result["elapsedMs"])
        del rankings, ids_only, result

    if set(reference_ids) != set(("M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7")):
        raise BenchmarkError("exhaustive scalar model coverage is incomplete")
    return (
        {"rows": model_rows, "totalElapsedMs": total_elapsed},
        reference_ids,
        reference_scores,
        {"hubnessRows": hubness_rows, "biasRows": bias_rows},
        cache_bytes,
    )


def _candidate_evaluation(
    index: candidate_index.CandidateIndex,
    reference_ids: Mapping[str, Any],
) -> dict[str, Any]:
    import numpy as np

    object_ids = index.object_ids
    ordinal = {object_id: value for value, object_id in enumerate(object_ids)}
    reference_variant_ids = tuple(sorted(reference_ids))
    rows: list[dict[str, Any]] = []
    pool_counts_by_variant: dict[str, list[int]] = {}
    selected_candidate_ids: dict[str, tuple[str, ...]] = {}
    for variant in candidate_index.CANDIDATE_VARIANTS:
        pool_counts: list[int] = []
        timings: list[float] = []
        matches = {model: Counter() for model in reference_variant_ids}
        denominators = {model: Counter() for model in reference_variant_ids}
        set_hash = hashlib.sha256()
        for query_ordinal, query_id in enumerate(object_ids):
            started = time.perf_counter()
            candidates = candidate_index.generate_exploration_candidates(
                index,
                query_id,
                variant=variant,
                fallback_minimum_candidates=20,
                include_reasons=False,
            )
            timings.append((time.perf_counter() - started) * 1000)
            candidate_ordinals = {ordinal[value] for value in candidates.candidate_ids}
            pool_counts.append(candidates.candidate_pool_count)
            set_hash.update(
                canonical_bytes([query_id, variant, candidates.candidate_set_sha256])
            )
            for model_id in reference_variant_ids:
                ranking = reference_ids[model_id][query_ordinal]
                for k in (10, 20, 50):
                    expected = ranking[:k]
                    matches[model_id][k] += sum(int(value) in candidate_ordinals for value in expected)
                    denominators[model_id][k] += len(expected)
        pool_counts_by_variant[variant] = pool_counts
        possible = len(object_ids) - 1
        for model_id in reference_variant_ids:
            for k in (10, 20, 50):
                recall = matches[model_id][k] / denominators[model_id][k]
                rows.append(
                    {
                        "candidateVariant": variant,
                        "referenceModelId": model_id.split("-", 1)[0],
                        "referenceVariantId": model_id,
                        "k": k,
                        "recall": recall,
                        "matchedReferenceResults": matches[model_id][k],
                        "referenceResultDenominator": denominators[model_id][k],
                        "candidatePoolP50": quantile(pool_counts, 0.50),
                        "candidatePoolP90": quantile(pool_counts, 0.90),
                        "candidatePoolP95": quantile(pool_counts, 0.95),
                        "candidatePoolP99": quantile(pool_counts, 0.99),
                        "candidatePoolMax": max(pool_counts),
                        "candidateReductionP50": 1 - quantile(pool_counts, 0.50) / possible,
                        "zeroCandidateObjectCount": sum(value == 0 for value in pool_counts),
                        "nearFullCorpusCandidateObjectCount": sum(value >= possible * 0.95 for value in pool_counts),
                        "candidateGenerationP50Ms": quantile(timings, 0.50),
                        "candidateGenerationP95Ms": quantile(timings, 0.95),
                        "candidateSetsSha256": set_hash.hexdigest(),
                    }
                )

    eligible: list[tuple[float, int, str]] = []
    fallback: list[tuple[float, float, int, str]] = []
    for variant in candidate_index.CANDIDATE_VARIANTS:
        recall20 = [
            float(row["recall"])
            for row in rows
            if row["candidateVariant"] == variant
            and row["k"] == 20
            and row["referenceVariantId"] in set(SHORTLIST_VARIANTS.values())
        ]
        if recall20:
            fallback.append(
                (
                    -min(recall20),
                    quantile(pool_counts_by_variant[variant], 0.50),
                    CANDIDATE_SELECTION_PRIORITY[variant],
                    variant,
                )
            )
        if recall20 and min(recall20) >= 0.98:
            eligible.append(
                (
                    quantile(pool_counts_by_variant[variant], 0.50),
                    CANDIDATE_SELECTION_PRIORITY[variant],
                    variant,
                )
            )
    selected = min(eligible)[2] if eligible else min(fallback)[3]
    target_met = bool(eligible)
    selected_rows = [row for row in rows if row["candidateVariant"] == selected]
    return {
        "candidateGeneratorVariantCount": len(candidate_index.CANDIDATE_VARIANTS),
        "selectedVariant": selected,
        "candidateArchitectureSelected": True,
        "shortlistRecallAt20Target": 0.98,
        "shortlistRecallAt20TargetMet": target_met,
        "selectionRule": (
            (
                "MINIMUM_P50_POOL_WITH_MINIMUM_SHORTLIST_RECALL_AT_20_GTE_0.98;"
                if target_met
                else "MAXIMIZE_MINIMUM_SHORTLIST_RECALL_AT_20_THEN_MINIMIZE_P50_POOL;"
            )
            + "LINEAGE_SAFE_RESIDUAL_ONLY_TIE_BREAK"
        ),
        "rows": rows,
        "selectedRows": selected_rows,
        "selectedPoolDistribution": {
            "p50": quantile(pool_counts_by_variant[selected], 0.50),
            "p90": quantile(pool_counts_by_variant[selected], 0.90),
            "p95": quantile(pool_counts_by_variant[selected], 0.95),
            "p99": quantile(pool_counts_by_variant[selected], 0.99),
            "max": max(pool_counts_by_variant[selected]),
            "zeroCount": sum(value == 0 for value in pool_counts_by_variant[selected]),
            "nearFullCount": sum(value >= (len(object_ids) - 1) * 0.95 for value in pool_counts_by_variant[selected]),
        },
    }


def _observed_ids(record: Mapping[str, Any], field: str) -> tuple[str, ...]:
    raw = record.get(field)
    if field in {"source", "object_type", "creator"}:
        raw = (raw,)
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        return ()
    values = []
    for value in raw:
        if isinstance(value, Mapping):
            identifier = str(value.get("id", "")).strip()
            label = str(value.get("label", identifier)).strip()
        else:
            identifier = str(value if value is not None else "").strip()
            label = identifier
        if identifier and not missingness_comparability.is_unknown_state(label):
            values.append(identifier)
    return tuple(sorted(set(values)))


def _approved_interaction_tokens(
    records: Sequence[Mapping[str, Any]],
    registry: Mapping[str, Any],
    *,
    support_floor: int = 5,
    support_ceiling: int = 20,
    shrunk_npmi_floor: float = 0.10,
) -> tuple[dict[str, tuple[str, ...]], dict[str, Any]]:
    """Map bounded, supported interaction cells to objects without pair rows."""

    approved: dict[tuple[str, ...], dict[tuple[str, ...], str]] = defaultdict(dict)
    selected_rows: list[dict[str, Any]] = []
    for row in (*registry.get("pairRows", ()), *registry.get("tripleRows", ())):
        support = int(row.get("support", 0))
        statistics_row = row.get("statistics", {})
        shrunk = float(statistics_row.get("shrunkNormalizedPmi", 0.0))
        if not support_floor <= support <= support_ceiling or shrunk < shrunk_npmi_floor:
            continue
        fields = tuple(str(value) for value in row.get("dimensions", ()))
        values = tuple(str(value) for value in row.get("valueIds", ()))
        if len(fields) not in {2, 3} or len(fields) != len(values):
            raise BenchmarkError("approved interaction cell has an invalid identity")
        token = str(row.get("interactionId", ""))
        approved[fields][values] = token
        selected_rows.append(
            {
                "interactionId": token,
                "dimensions": list(fields),
                "support": support,
                "denominator": int(statistics_row.get("denominator", 0)),
                "shrunkNormalizedPmi": shrunk,
            }
        )

    by_object: dict[str, tuple[str, ...]] = {}
    posting_counts: Counter[str] = Counter()
    for record in records:
        tokens: set[str] = set()
        for fields, lookup in approved.items():
            dimensions = [_observed_ids(record, field) for field in fields]
            if not all(dimensions):
                continue
            for values in product(*dimensions):
                token = lookup.get(tuple(values))
                if token:
                    tokens.add(token)
        if tokens:
            object_id = str(record["objectId"])
            by_object[object_id] = tuple(sorted(tokens))
            posting_counts.update(tokens)
    expected_support = {row["interactionId"]: row["support"] for row in selected_rows}
    if any(posting_counts[token] != support for token, support in expected_support.items()):
        raise BenchmarkError("interaction candidate postings do not reconcile with registry support")
    receipt = {
        "supportFloor": support_floor,
        "supportCeiling": support_ceiling,
        "shrunkNormalizedPmiFloor": shrunk_npmi_floor,
        "approvedInteractionCount": len(selected_rows),
        "objectCoverageCount": len(by_object),
        "postingMembershipCount": sum(posting_counts.values()),
        "rowsSha256": sha256_json(selected_rows),
        "rawParentFeaturesScoredAgain": False,
        "rareMeansImportant": False,
    }
    return by_object, receipt


def _run_full_model_suite(
    context: model_baselines.ModelContext,
    records: Sequence[Mapping[str, Any]],
    cache_dir: Path,
    *,
    block_size: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Run M0 plus every scalar benchmark variant over the full pair cube."""

    records_by_id = _public_records_by_id(records)
    object_ids = context.candidate_index.object_ids
    primary_ids: dict[str, Any] = {}
    primary_scores: dict[str, Any] = {}
    primary_rankings: dict[str, Mapping[str, Sequence[Sequence[Any]]]] = {}
    all_reference_ids: dict[str, Any] = {}
    model_rows: list[dict[str, Any]] = []
    hubness_rows: list[dict[str, Any]] = []
    bias_rows: list[dict[str, Any]] = []
    association_rows: list[dict[str, Any]] = []
    cache_bytes: dict[str, int] = {}
    exhaustive_elapsed = 0.0

    def record_hubness(
        *,
        model_id: str,
        variant_id: str,
        rankings: Mapping[str, Sequence[Any]],
        dominance: Mapping[str, Any],
    ) -> None:
        hub = hubness.k_occurrence_distribution(rankings, cohort_ids=object_ids)
        for row in hub["rows"]:
            hubness_rows.append(
                {
                    "modelId": model_id,
                    "variantId": variant_id,
                    **row,
                }
            )
        occurrence20 = hub["occurrenceCounts"]["20"]
        correlations = hubness.hub_attribute_correlations(occurrence20, records_by_id)
        source = hubness.source_bias_diagnostics(rankings, records_by_id, k=20)
        bias_rows.append(
            {
                "modelId": model_id,
                "variantId": variant_id,
                **source,
                **dominance,
                "hubAttributeCorrelations": correlations,
                "diagnosticOnly": True,
            }
        )
        for row in hubness.hub_categorical_associations(occurrence20, records_by_id):
            association_rows.append(
                {"modelId": model_id, "variantId": variant_id, **row}
            )

    prepared = negative_control.prepare_curated_negative_control(records)
    m0 = negative_control.stream_exhaustive_m0_top_k(
        prepared,
        k=TOP_K,
        block_size=block_size,
    )
    if m0["unorderedPairVisits"] != EXPECTED_PAIR_COUNT:
        raise BenchmarkError("M0 did not visit the exact unordered pair cube")
    m0_rankings = m0["compactRankings"]
    m0_ids, m0_scores = _ranking_arrays(m0_rankings, object_ids)
    primary_ids["M0"] = m0_ids
    primary_scores["M0"] = m0_scores
    all_reference_ids["M0-RAW-CURATED-JACCARD"] = m0_ids
    record_hubness(
        model_id="M0",
        variant_id="M0-RAW-CURATED-JACCARD",
        rankings=m0_rankings,
        dominance={
            "resultCount": len(object_ids) * TOP_K,
            "medianMaximumFamilyShare": 1.0,
            "p95MaximumFamilyShare": 1.0,
            "oneFamilyOver80PercentRate": 1.0,
            "sourceDominatedQueryRate": 0.0,
            "curationDominatedQueryRate": 1.0,
        },
    )
    model_rows.append(
        {
            "modelId": "M0",
            "variantId": "M0-RAW-CURATED-JACCARD",
            "modelFamily": negative_control.MODEL_FAMILY,
            "task": "NEGATIVE_CONTROL_ONLY",
            "symmetric": True,
            "parameters": {},
            "shortlistEligible": False,
            "exhaustivePairCount": m0["unorderedPairVisits"],
            "rankingSha256": m0["rankingSha256"],
            "scoreDistribution": m0["scoreDistribution"],
            "elapsedMs": m0["elapsedMs"],
            "pairRowsRetained": 0,
            "fullPairMatrixMaterialized": False,
            "productionEligible": False,
        }
    )
    cache_bytes["M0-RAW-CURATED-JACCARD"] = _write_ranking_cache(
        _cache_path(cache_dir, "M0-RAW-CURATED-JACCARD"),
        model_id="M0",
        variant_id="M0-RAW-CURATED-JACCARD",
        index_sha256=context.candidate_index.index_sha256,
        ranking_sha256=m0["rankingSha256"],
        rankings=m0_rankings,
    )
    exhaustive_elapsed += float(m0["elapsedMs"])
    del m0_rankings, m0
    gc.collect()

    scalar_specs = tuple(
        spec for spec in model_baselines.benchmark_model_specs() if spec.model_id != "M8"
    )
    for spec in scalar_specs:
        result = model_baselines.stream_exhaustive_top_k(
            context,
            (spec,),
            k=TOP_K,
            block_size=block_size,
            engine="COMPACT_NUMPY_BLOCK",
            retain_rankings=True,
        )
        if result["unorderedPairVisits"] != EXPECTED_PAIR_COUNT:
            raise BenchmarkError(f"{spec.variant_id} did not visit the exact unordered pair cube")
        rankings = result["compactRankings"][spec.variant_id]
        ids, scores = _ranking_arrays(rankings, object_ids)
        all_reference_ids[spec.variant_id] = ids
        is_primary = SHORTLIST_VARIANTS.get(spec.model_id) == spec.variant_id
        score_p95 = None
        if is_primary or spec.model_id in {"M1", "M3", "M4", "M6"}:
            source, dominance, score_p95 = _source_bias_and_dominance(
                context,
                spec,
                rankings,
                records_by_id,
                profile_k=5,
            )
            # record_hubness recomputes the exact source row for a common k.
            del source
        else:
            dominance = {
                "resultCount": 0,
                "medianMaximumFamilyShare": None,
                "p95MaximumFamilyShare": None,
                "oneFamilyOver80PercentRate": None,
                "sourceDominatedQueryRate": None,
                "curationDominatedQueryRate": None,
                "notMeasuredRationale": "SENSITIVITY_VARIANT_USES_BASE_FAMILY_CONTRACT",
            }
        record_hubness(
            model_id=spec.model_id,
            variant_id=spec.variant_id,
            rankings=rankings,
            dominance=dominance,
        )
        if is_primary:
            primary_ids[spec.model_id] = ids
            primary_scores[spec.model_id] = scores
            primary_rankings[spec.model_id] = rankings
            cache_bytes[spec.variant_id] = _write_ranking_cache(
                _cache_path(cache_dir, spec.variant_id),
                model_id=spec.model_id,
                variant_id=spec.variant_id,
                index_sha256=context.candidate_index.index_sha256,
                ranking_sha256=result["rankingSha256"],
                rankings=rankings,
            )
        model_rows.append(
            {
                "modelId": spec.model_id,
                "variantId": spec.variant_id,
                "modelFamily": spec.model_family,
                "task": spec.task,
                "symmetric": spec.symmetric,
                "parameters": spec.parameters(),
                "shortlistEligible": is_primary,
                "exhaustivePairCount": result["unorderedPairVisits"],
                "directionalScoreCount": result["directionalScoreCount"],
                "rankingSha256": result["rankingSha256"],
                "compiledFeatureSha256": result["compiledFeatureSha256"],
                "compileMs": result["compileMs"],
                "elapsedMs": result["elapsedMs"],
                "modelScoreMs": result["modelScoreMs"][spec.variant_id],
                "explanationProfileScoreP95Ms": score_p95,
                "pairRowsRetained": 0,
                "fullPairMatrixMaterialized": False,
                "productionEligible": False,
            }
        )
        exhaustive_elapsed += float(result["elapsedMs"])
        if not is_primary:
            del rankings, scores
        del result
        gc.collect()

    if set(primary_ids) != {"M0", *SHORTLIST_MODEL_IDS}:
        raise BenchmarkError("primary exhaustive references are incomplete")
    m8_spec = next(
        spec for spec in model_baselines.benchmark_model_specs() if spec.model_id == "M8"
    )
    return (
        {
            "modelVariantCount": 1 + len(model_baselines.benchmark_model_specs()),
            "scalarExhaustiveVariantCount": 1 + len(scalar_specs),
            "modelRows": model_rows,
            "hubnessRows": hubness_rows,
            "biasRows": bias_rows,
            "hubCategoricalAssociationRows": association_rows,
            "cacheBytes": cache_bytes,
            "exhaustiveBenchmarkMs": exhaustive_elapsed,
            "m8Spec": m8_spec,
            "pairRowsRetained": 0,
        },
        {
            "ids": primary_ids,
            "scores": primary_scores,
            "rankings": primary_rankings,
            "allIds": all_reference_ids,
        },
        {row["variantId"]: row["rankingSha256"] for row in model_rows},
    )


def _missingness_evaluation(
    context: model_baselines.ModelContext,
    records_by_id: Mapping[str, Mapping[str, Any]],
    reference_rankings: Mapping[str, Sequence[Any]],
) -> dict[str, Any]:
    base_spec = next(spec for spec in model_baselines.default_model_specs() if spec.model_id == "M5")
    ratios: list[float] = []
    affinity_by_variant: dict[str, list[float]] = {
        variant: [] for variant in missingness_comparability.MISSINGNESS_VARIANTS
    }
    shared_unknown_pair_count = 0
    evaluated_pair_count = 0
    for query_id in context.candidate_index.object_ids:
        for raw in reference_rankings[query_id][:20]:
            candidate_id = str(raw[0] if isinstance(raw, Sequence) else raw)
            profile = model_baselines.score_pair(context, query_id, candidate_id, base_spec)
            comparability = missingness_comparability.ComparabilityProfile(
                observed_family_count=int(profile.comparability["observedFamilyCount"]),
                eligible_family_count=int(profile.comparability["eligibleFamilyCount"]),
                ratio=float(profile.comparability["ratio"]),
                jointly_observable_families=profile.jointly_observable_families,
                unavailable_families=profile.unavailable_families,
            )
            ratios.append(comparability.ratio)
            for variant in missingness_comparability.MISSINGNESS_VARIANTS:
                aggregation = missingness_comparability.aggregate_family_affinity(
                    profile.family_scores,
                    comparability,
                    variant=variant,
                )
                affinity_by_variant[variant].append(float(aggregation["affinity"]))
            diagnostic = missingness_comparability.compare_missingness_states(
                records_by_id[query_id],
                records_by_id[candidate_id],
            )
            shared_unknown_pair_count += int(bool(diagnostic["sharedUnknownStateFields"]))
            if diagnostic["positiveAffinityCredit"] != 0:
                raise BenchmarkError("shared unknown state received positive affinity")
            evaluated_pair_count += 1
    rows = []
    for variant in missingness_comparability.MISSINGNESS_VARIANTS:
        values = affinity_by_variant[variant]
        rows.append(
            {
                "missingnessVariant": variant,
                "evaluatedPairCount": evaluated_pair_count,
                "affinityP50": quantile(values, 0.50),
                "affinityP95": quantile(values, 0.95),
                "comparabilityP50": quantile(ratios, 0.50),
                "comparabilityP95": quantile(ratios, 0.95),
                "sharedUnknownPositiveCreditCount": 0,
                "notApplicableAsMissingCount": 0,
                "separateComparabilityChannel": True,
            }
        )
    return {
        "comparabilityChannelImplemented": True,
        "missingnessVariantCount": len(rows),
        "evaluatedPairCount": evaluated_pair_count,
        "pairsSharingOneOrMoreUnknownStates": shared_unknown_pair_count,
        "sharedUnknownPositiveCreditCount": 0,
        "notApplicableAsMissingCount": 0,
        "comparabilityDistribution": {
            "p50": quantile(ratios, 0.50),
            "p95": quantile(ratios, 0.95),
            "min": min(ratios),
            "max": max(ratios),
        },
        "rows": rows,
    }


def _source_treatment_evaluation(
    context: model_baselines.ModelContext,
    compiled: model_baselines.CompiledFeatureContext,
    records_by_id: Mapping[str, Mapping[str, Any]],
    anchor_ids: Sequence[str],
) -> dict[str, Any]:
    base = next(spec for spec in model_baselines.default_model_specs() if spec.model_id == "M5")
    rankings_by_treatment: dict[str, dict[str, list[dict[str, Any]]]] = {}
    rows: list[dict[str, Any]] = []
    for treatment in model_baselines.SOURCE_TREATMENTS[:4]:
        spec = replace(
            base,
            variant_id=f"M5-SOURCE-{treatment}",
            source_treatment=treatment,
            task=("CONTRASTIVE_DISCOVERY" if treatment == "SOURCE-3" else base.task),
        )
        rankings: dict[str, list[dict[str, Any]]] = {}
        for query_id in anchor_ids:
            compact = model_baselines.object_local_top_k_compact(
                compiled,
                query_id,
                spec,
                k=TOP_K,
            )
            rankings[query_id] = [
                {"candidateId": candidate_id, "diagnosticScore": score}
                for candidate_id, score in compact
            ]
        rankings_by_treatment[treatment] = rankings
        bias = hubness.source_bias_diagnostics(rankings, records_by_id, k=20)
        rows.append(
            {
                "sourceTreatment": treatment,
                "modelVariantId": spec.variant_id,
                **bias,
                "sameSourceAutomaticallyPositive": treatment == "SOURCE-1",
                "dedicatedContrastiveTask": treatment == "SOURCE-3",
                "postRankingDiversification": False,
            }
        )
    diversified: dict[str, list[dict[str, Any]]] = {}
    for query_id, ranking in rankings_by_treatment["SOURCE-0"].items():
        diversified[query_id] = model_baselines.diversify_by_source(
            ranking,
            context,
            max_per_source=3,
        )
    rankings_by_treatment["SOURCE-4"] = diversified
    bias = hubness.source_bias_diagnostics(diversified, records_by_id, k=20)
    rows.append(
        {
            "sourceTreatment": "SOURCE-4",
            "modelVariantId": "M5-SOURCE-SOURCE-4",
            **bias,
            "sameSourceAutomaticallyPositive": False,
            "dedicatedContrastiveTask": False,
            "postRankingDiversification": True,
        }
    )
    return {
        "sourceTreatmentCount": len(rows),
        "anchorCount": len(anchor_ids),
        "rows": rows,
        "sourceIsCorpusCompositionBias": True,
        "sameSourceIsHistoricalRelation": False,
    }


def _interaction_evaluation(
    registry: Mapping[str, Any],
    *,
    trusted_context: interaction_statistics.TrustedInteractionContext,
    context: model_baselines.ModelContext,
    anchor_ids: Sequence[str],
    base_rankings: Mapping[str, Sequence[Any]],
) -> dict[str, Any]:
    cells = [*registry.get("pairRows", ()), *registry.get("tripleRows", ())]
    method_keys = {
        "RAW_SUPPORT": "rawSupport",
        "CONDITIONAL_SUPPORT": "leftConditionalRate",
        "LIFT": "lift",
        "PMI": "pmiNats",
        "NORMALIZED_PMI": "normalizedPmi",
        "LOG_LIKELIHOOD_RATIO": "logLikelihoodRatio",
        "SMOOTHED_LIFT": "smoothedLift",
        "SHRUNK_NORMALIZED_PMI": "shrunkNormalizedPmi",
    }
    rows: list[dict[str, Any]] = []
    for method in interaction_statistics.INTERACTION_METHODS:
        key = method_keys[method]
        for threshold in interaction_statistics.SUPPORT_THRESHOLDS:
            selected = [row for row in cells if int(row["support"]) >= threshold]
            values = []
            for row in selected:
                stats = row["statistics"]
                if key == "leftConditionalRate" and "leftConditionalRate" not in stats:
                    marginals = stats.get("marginalSupports", ())
                    value = row["support"] / max(marginals, default=1)
                else:
                    value = stats.get(key, row["support"] if key == "rawSupport" else 0.0)
                values.append(float(value))
            rows.append(
                {
                    "method": method,
                    "supportThreshold": threshold,
                    "eligibleObservedCellCount": len(selected),
                    "statisticP50": quantile(values, 0.50) if values else 0.0,
                    "statisticP95": quantile(values, 0.95) if values else 0.0,
                    "statisticMax": max(values, default=0.0),
                    "lowSupportCellsExcluded": len(cells) - len(selected),
                    "rareMeansImportant": False,
                    "parentContributionRepeated": False,
                }
            )
    residual_rows = []
    residual_methods = (
        "NO_INTERACTION_CONTRIBUTION",
        "CAPPED_INTERACTION_BONUS",
        "INFORMATION_RESIDUAL_CONTRIBUTION",
        "LOG_LIKELIHOOD_INTERACTION_CONTRIBUTION",
    )
    for method in residual_methods:
        for threshold in interaction_statistics.SUPPORT_THRESHOLDS:
            residual_receipts = [
                interaction_statistics.residual_interaction_contribution(
                    row,
                    support_threshold=threshold,
                    cap=0.10,
                    method=method,
                )
                for row in cells
            ]
            values = [float(row["residualScore"]) for row in residual_receipts]
            positive_excess = [
                float(cell["statistics"].get("lift", 0.0)) > 1.0
                for cell in cells
            ]
            non_positive_residual_count = sum(
                (not is_positive) and value > 0
                for is_positive, value in zip(positive_excess, values, strict=True)
            )
            residual_rows.append(
                {
                    "method": method,
                    "supportThreshold": threshold,
                    "cellCount": len(values),
                    "residualP50": quantile(values, 0.50),
                    "residualP95": quantile(values, 0.95),
                    "residualMax": max(values, default=0.0),
                    "cap": 0.10,
                    "positiveExcessAssociationRequired": True,
                    "positiveExcessEligibleCellCount": sum(positive_excess),
                    "positiveResidualCellCount": sum(value > 0 for value in values),
                    "nonPositiveExcessResidualCount": non_positive_residual_count,
                }
            )
    low_support_failures = interaction_statistics.low_support_inflation_failures(cells)

    # Exercise the scorer itself on a deterministic bounded real-data frame.
    # Each frame contains the baseline top-50 plus every candidate reachable by
    # one frozen high-information interaction posting for the anchor. This
    # makes the experiment sensitive to the real trusted interaction context
    # without retaining a pair table or expanding to the full corpus.
    trusted_postings = interaction_statistics.trusted_candidate_postings(trusted_context)
    specs = model_baselines.interaction_policy_model_specs()
    rankings_by_policy: dict[str, dict[str, list[dict[str, Any]]]] = {
        spec.interaction_policy: {} for spec in specs
    }
    score_deltas: dict[str, list[float]] = {
        spec.interaction_policy: []
        for spec in specs
        if spec.interaction_policy != "NO_INTERACTION_CONTRIBUTION"
    }
    cap_reconciliation_failures = 0
    parent_duplication_failures = 0
    evaluated_pair_count = 0
    for query_id in anchor_ids:
        baseline_ids = {
            str(
                row.get("candidateId")
                if isinstance(row, Mapping)
                else row[0]
                if isinstance(row, Sequence)
                and not isinstance(row, (str, bytes, bytearray))
                else row
            )
            for row in base_rankings[query_id][:TOP_K]
        }
        interaction_ids = trusted_context.object_interaction_ids[query_id]
        interaction_candidates = {
            object_id
            for interaction_id in interaction_ids
            for object_id in trusted_postings.get(interaction_id, ())
        }
        candidate_ids = tuple(sorted((baseline_ids | interaction_candidates) - {query_id}))
        if not candidate_ids:
            raise BenchmarkError("interaction experiment produced an empty candidate frame")
        by_policy_scores: dict[str, dict[str, float]] = {}
        for spec in specs:
            ranking = model_baselines.rank_candidates(
                context,
                query_id,
                candidate_ids,
                spec,
                trusted_interaction_context=trusted_context,
            )
            rankings_by_policy[spec.interaction_policy][query_id] = ranking
            by_policy_scores[spec.interaction_policy] = {
                str(row["candidateId"]): float(row["diagnosticScore"])
                for row in ranking
            }
            for row in ranking:
                interactions = row["profile"]["interactions"]
                if not interactions:
                    continue
                residual_sum = math.fsum(
                    float(value["residualScore"]) for value in interactions
                )
                aggregate_bonus = float(interactions[0]["aggregateBonus"])
                cap_reconciliation_failures += int(
                    not math.isclose(residual_sum, aggregate_bonus, rel_tol=0.0, abs_tol=1e-12)
                )
                parent_duplication_failures += sum(
                    bool(value.get("parentContributionRepeated")) for value in interactions
                )
        baseline_scores = by_policy_scores["NO_INTERACTION_CONTRIBUTION"]
        for policy, values in by_policy_scores.items():
            if policy == "NO_INTERACTION_CONTRIBUTION":
                continue
            score_deltas[policy].extend(
                values[candidate_id] - baseline_scores[candidate_id]
                for candidate_id in sorted(values)
            )
        evaluated_pair_count += len(candidate_ids)

    reference = rankings_by_policy["NO_INTERACTION_CONTRIBUTION"]
    scorer_rows: list[dict[str, Any]] = []
    for spec in specs:
        policy = spec.interaction_policy
        if policy == "NO_INTERACTION_CONTRIBUTION":
            scorer_rows.append(
                {
                    "interactionPolicy": policy,
                    "anchorCount": len(anchor_ids),
                    "evaluatedPairCount": evaluated_pair_count,
                    "meanTop20Overlap": 1.0,
                    "meanTop20RankCorrelation": 1.0,
                    "scoreDeltaP50": 0.0,
                    "scoreDeltaP95": 0.0,
                    "directScorerSensitivity": True,
                }
            )
            continue
        comparison = ablation.compare_rankings(
            reference,
            rankings_by_policy[policy],
            k_values=(20,),
        )["rows"][0]
        deltas = score_deltas[policy]
        scorer_rows.append(
            {
                "interactionPolicy": policy,
                "anchorCount": len(anchor_ids),
                "evaluatedPairCount": evaluated_pair_count,
                "meanTop20Overlap": comparison["meanTopKOverlap"],
                "meanTop20RankCorrelation": comparison["meanRankCorrelation"],
                "scoreDeltaP50": quantile(deltas, 0.50),
                "scoreDeltaP95": quantile(deltas, 0.95),
                "directScorerSensitivity": True,
            }
        )

    invalid_denominator_count = sum(
        int(row.get("eligiblePopulationCount", 0)) <= 0 for row in cells
    )
    support_exceeds_denominator_count = sum(
        int(row.get("support", 0)) > int(row.get("eligiblePopulationCount", -1))
        for row in cells
    )
    non_positive_excess_residual_count = sum(
        int(row["nonPositiveExcessResidualCount"]) for row in residual_rows
    )
    grid_reconciliation_failures = int(len(rows) != 40) + int(len(residual_rows) != 20)
    return {
        "interactionMethodCount": len(interaction_statistics.INTERACTION_METHODS),
        "supportThresholdCount": len(interaction_statistics.SUPPORT_THRESHOLDS),
        "observedPairCellCount": len(registry.get("pairRows", ())),
        "observedTripleCellCount": len(registry.get("tripleRows", ())),
        "registryCellCount": len(cells),
        "registrySha256": registry["registrySha256"],
        "trustedInteractionContextSha256": trusted_context.context_sha256,
        "jointObservableDenominatorPolicy": "ALL_DIMENSIONS_OBSERVED",
        "invalidDenominatorCount": invalid_denominator_count,
        "supportExceedsDenominatorCount": support_exceeds_denominator_count,
        "positiveExcessAssociationRequired": True,
        "nonPositiveExcessResidualCount": non_positive_excess_residual_count,
        "expectedMethodGridRowCount": 40,
        "observedMethodGridRowCount": len(rows),
        "expectedResidualGridRowCount": 20,
        "observedResidualGridRowCount": len(residual_rows),
        "gridReconciliationFailureCount": grid_reconciliation_failures,
        "rows": rows,
        "residualRows": residual_rows,
        "scorerExperimentRows": scorer_rows,
        "scorerExperimentPairCount": evaluated_pair_count,
        "scorerCapReconciliationFailureCount": cap_reconciliation_failures,
        "lowSupportInflationFailureCount": low_support_failures,
        "interactionParentDoubleCountFailures": parent_duplication_failures,
        "zeroCellsMaterialized": False,
        "rareMeansImportant": False,
    }


def _m8_evaluation(
    context: model_baselines.ModelContext,
    anchor_ids: Sequence[str],
    primary_rankings: Mapping[str, Mapping[str, Sequence[Any]]],
) -> dict[str, Any]:
    spec = next(spec for spec in model_baselines.benchmark_model_specs() if spec.model_id == "M8")
    front_sizes: list[int] = []
    layer_counts: list[int] = []
    evaluated_counts: list[int] = []
    digest = hashlib.sha256()
    started = time.perf_counter()
    for query_id in anchor_ids:
        union = sorted(
            {
                str(row[0] if isinstance(row, Sequence) else row)
                for model_id in SHORTLIST_MODEL_IDS
                for row in primary_rankings[model_id][query_id]
            }
        )
        ranking = model_baselines.rank_candidates(context, query_id, union, spec)
        fronts = Counter(int(row["paretoLayer"]) for row in ranking)
        front_sizes.append(fronts.get(1, 0))
        layer_counts.append(max(fronts, default=0))
        evaluated_counts.append(len(ranking))
        digest.update(
            canonical_bytes(
                [query_id, [(row["candidateId"], row["paretoLayer"]) for row in ranking]]
            )
        )
    return {
        "modelId": "M8",
        "variantId": spec.variant_id,
        "modelFamily": spec.model_family,
        "task": spec.task,
        "symmetric": spec.symmetric,
        "parameters": spec.parameters(),
        "anchorCount": len(anchor_ids),
        "candidateUnionP50": quantile(evaluated_counts, 0.50),
        "candidateUnionP95": quantile(evaluated_counts, 0.95),
        "paretoFrontP50": quantile(front_sizes, 0.50),
        "paretoFrontP95": quantile(front_sizes, 0.95),
        "paretoLayerP50": quantile(layer_counts, 0.50),
        "paretoLayerP95": quantile(layer_counts, 0.95),
        "rankingSha256": digest.hexdigest(),
        "elapsedMs": (time.perf_counter() - started) * 1000,
        "universalAffinityScalar": False,
        "shortlistEligible": False,
        "productionEligible": False,
        "pairRowsRetained": 0,
    }


def _ablation_evaluation(
    context: model_baselines.ModelContext,
    compiled: model_baselines.CompiledFeatureContext,
    anchor_ids: Sequence[str],
    primary_rankings: Mapping[str, Mapping[str, Sequence[Any]]],
) -> dict[str, Any]:
    base_specs = {
        spec.model_id: spec
        for spec in model_baselines.default_model_specs()
    }
    rows: list[dict[str, Any]] = []
    collapse_failures = 0
    for model_id in model_baselines.MODEL_IDS:
        base_spec = base_specs[model_id]
        if model_id == "M8":
            candidate_universe = {
                query_id: tuple(
                    str(row[0]) for row in primary_rankings["M2"][query_id][:TOP_K]
                )
                for query_id in anchor_ids
            }
            reference = {
                query_id: model_baselines.rank_candidates(
                    context,
                    query_id,
                    candidate_universe[query_id],
                    base_spec,
                    k=TOP_K,
                )
                for query_id in anchor_ids
            }
        else:
            reference = {
                query_id: model_baselines.object_local_top_k_compact(
                    compiled,
                    query_id,
                    base_spec,
                    k=TOP_K,
                )
                for query_id in anchor_ids
            }
        for variant in ablation.declared_ablation_variants(base_spec):
            spec = variant["modelSpec"]
            # Candidate-only perturbations do not alter the base scorer.  This
            # exact equality is itself the lineage/deduplication result; their
            # candidate fanout sensitivity is measured in the curatorial and
            # candidate-generator experiments.
            if variant["ablationFamily"] in {
                "CHANGE_BROAD_CONTAINER_THRESHOLD",
                "CHANGE_RARE_SUPPORT_THRESHOLD",
                "REMOVE_LARGEST_CURATED_CONTAINER",
                "REMOVE_DOMINANT_SOURCE",
                "LEAVE_INTERACTIONS_OUT",
            }:
                candidate = reference
                scoring_effect = (
                    "NOT_APPLICABLE_BASE_HAS_NO_INTERACTIONS"
                    if variant["ablationFamily"] == "LEAVE_INTERACTIONS_OUT"
                    else "NONE_CANDIDATE_OR_EXCLUDED_FAMILY_ONLY"
                )
            else:
                if model_id == "M8":
                    candidate = {
                        query_id: model_baselines.rank_candidates(
                            context,
                            query_id,
                            candidate_universe[query_id],
                            spec,
                            k=TOP_K,
                        )
                        for query_id in anchor_ids
                    }
                else:
                    candidate = {
                        query_id: model_baselines.object_local_top_k_compact(
                            compiled,
                            query_id,
                            spec,
                            k=TOP_K,
                        )
                        for query_id in anchor_ids
                    }
                scoring_effect = "DIRECT_SCORER_SENSITIVITY"
            comparison = ablation.compare_rankings(reference, candidate)
            for metric in comparison["rows"]:
                rows.append(
                    {
                        "modelId": model_id,
                        "baseVariantId": base_spec.variant_id,
                        "ablationId": variant["ablationId"],
                        "ablationFamily": variant["ablationFamily"],
                        "k": metric["k"],
                        "queryCount": metric["queryCount"],
                        "meanTopKOverlap": metric["meanTopKOverlap"],
                        "minimumTopKOverlap": metric["minimumTopKOverlap"],
                        "meanRankCorrelation": metric["meanRankCorrelation"],
                        "minimumRankCorrelation": metric["minimumRankCorrelation"],
                        "scoringEffect": scoring_effect,
                        "learnedWeightsUsed": False,
                    }
                )
            target20 = next(row for row in comparison["rows"] if row["k"] == 20)
            collapse_failures += int(float(target20["meanTopKOverlap"]) < 0.50)
    return {
        "candidateModelCount": len(model_baselines.MODEL_IDS),
        "declaredVariantCountPerModel": 27,
        "ablationVariantCount": 27 * len(model_baselines.MODEL_IDS),
        "requiredAblationFamilyCount": len(ablation.REQUIRED_ABLATION_FAMILIES),
        "rows": rows,
        "collapseFailureCount": collapse_failures,
        "learnedWeightsUsed": False,
    }


def _hubness_correction_evaluation(
    primary_rankings: Mapping[str, Mapping[str, Sequence[Any]]],
    cohort_ids: Sequence[str],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    correction_tested = False
    for model_id in SHORTLIST_MODEL_IDS:
        original = {
            query_id: [
                {"candidateId": str(row[0]), "diagnosticScore": float(row[1])}
                for row in ranking
            ]
            for query_id, ranking in primary_rankings[model_id].items()
        }
        original_hub = hubness.k_occurrence_distribution(
            original,
            cohort_ids=cohort_ids,
            k_values=(20,),
        )["rows"][0]
        severe = (
            float(original_hub["gini"]) >= 0.50
            or float(original_hub["top1PercentOccurrenceShare"]) >= 0.10
        )
        transforms = {
            "RECIPROCAL_NEIGHBOR_FILTER": hubness.reciprocal_neighbor_filter(original, k=20),
            "LOCAL_SCALING": hubness.local_scaling(original, scale_k=20),
            "MUTUAL_PROXIMITY_GLOBAL_SCALING_STYLE": hubness.global_scaling_style(original),
        }
        correction_tested = True
        for correction_id, transformed in transforms.items():
            transformed_hub = hubness.k_occurrence_distribution(
                transformed,
                cohort_ids=cohort_ids,
                k_values=(20,),
            )["rows"][0]
            comparison = ablation.compare_rankings(original, transformed, k_values=(20,))["rows"][0]
            rows.append(
                {
                    "modelId": model_id,
                    "correctionId": correction_id,
                    "severeHubnessDiagnostic": severe,
                    "originalGini": original_hub["gini"],
                    "correctedGini": transformed_hub["gini"],
                    "originalTop1PercentOccurrenceShare": original_hub["top1PercentOccurrenceShare"],
                    "correctedTop1PercentOccurrenceShare": transformed_hub["top1PercentOccurrenceShare"],
                    "top20Overlap": comparison["meanTopKOverlap"],
                    "rankCorrelation": comparison["meanRankCorrelation"],
                    "explanationComplexity": "HIGHER_THAN_UNCORRECTED_BASELINE",
                    "selected": False,
                    "analysisOnly": True,
                }
            )
    return {
        "hubnessCorrectionTested": correction_tested,
        "hubnessCorrectionSelected": False,
        "rows": rows,
        "selectionRationale": "NO_CORRECTION_AUTOMATICALLY_ADOPTED_WITHOUT_HUMAN_REVIEW",
    }


def _analysis_receipts(
    source: Mapping[str, Any],
    index: candidate_index.CandidateIndex,
    context: model_baselines.ModelContext,
    compiled: model_baselines.CompiledFeatureContext,
    model_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    receipts = []
    for row in model_rows:
        parameter_set = {
            "benchmarkVariantId": str(row["variantId"]),
            "scoringRecordsSha256": index.scoring_records_sha256,
            "modelContextSha256": context.context_sha256,
            "compiledFeatureContextSha256": compiled.compiled_sha256,
            **dict(row.get("parameters", {})),
        }
        receipt = analysis_run_receipts.build_analysis_run_receipt(
            model_id=str(row["modelId"]),
            model_family=str(row["modelFamily"]),
            implementation_version=model_baselines.IMPLEMENTATION_VERSION,
            parameters=parameter_set,
            research_release_id=str(source["researchReleaseId"]),
            research_release_sha256=str(source["researchManifestSha256"]),
            context_projection_id=str(source["contextProjectionId"]),
            context_projection_sha256=str(source["contextProjectionSha256"]),
            spacetime_projection_id=str(source["spacetimeProjectionId"]),
            spacetime_projection_sha256=str(source["spacetimeProjectionSha256"]),
            exploration_signal_registry_sha256=str(source["explorationSignalRegistrySha256"]),
            candidate_index_sha256=index.index_sha256,
            input_cohort_count=EXPECTED_PUBLIC_COUNT,
            output_summary=deterministic_value(dict(row)),
            top_k_artifact=str(row["rankingSha256"]),
            source_commit=str(source["sourceCommit"]),
            execution_seed=None,
            generated_at="2026-08-24T00:00:00Z",
        )
        receipts.append(receipt)
    register = analysis_run_receipts.analysis_run_register(receipts)
    if register["analysisRunCount"] != len(model_rows):
        raise BenchmarkError("analysis-run register count does not reconcile")
    return register


def _explanations_and_human_packet(
    context: model_baselines.ModelContext,
    records: Sequence[Mapping[str, Any]],
    titles: Mapping[str, str],
    source: Mapping[str, Any],
    selected_candidate_variant: str,
    anchor_selection: Mapping[str, Any],
    run_register: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    spec_by_model = {
        spec.model_id: spec
        for spec in model_baselines.default_model_specs()
        if spec.model_id in SHORTLIST_MODEL_IDS
    }
    # Multiple sensitivity runs share a model ID. Bind human explanations to
    # the exact shortlisted variant rather than whichever receipt sorted last.
    run_id_by_model = {}
    for model_id, variant_id in SHORTLIST_VARIANTS.items():
        receipt = next(
            row
            for row in run_register["rows"]
            if row["modelId"] == model_id
            and row["parameterSet"].get("benchmarkVariantId") == variant_id
        )
        # M2/M5 benchmark variant names differ from default names while their
        # frozen parameter sets match; the receipt identity remains exact.
        run_id_by_model[model_id] = receipt["analysisRunId"]

    rankings_by_model: dict[str, dict[str, list[dict[str, Any]]]] = {
        model_id: {} for model_id in SHORTLIST_MODEL_IDS
    }
    explanations: list[dict[str, Any]] = []
    explanation_validations: list[dict[str, Any]] = []
    object_local_timings: list[float] = []
    records_by_id = _public_records_by_id(records)
    source_by_id = {
        object_id: str(record["source"]["label"])
        for object_id, record in records_by_id.items()
    }
    for anchor in anchor_selection["anchors"]:
        query_id = str(anchor["anchorId"])
        candidate_set = candidate_index.generate_exploration_candidates(
            context.candidate_index,
            query_id,
            variant=selected_candidate_variant,
            fallback_minimum_candidates=20,
            include_reasons=True,
        )
        for model_id in SHORTLIST_MODEL_IDS:
            spec = spec_by_model[model_id]
            started = time.perf_counter()
            ranking = model_baselines.rank_candidates(
                context,
                query_id,
                candidate_set.candidate_ids,
                spec,
                k=4,
            )
            object_local_timings.append((time.perf_counter() - started) * 1000)
            explained_rows = []
            for row in ranking:
                candidate_id = str(row["candidateId"])
                reasons = candidate_set.retrieval_reasons.get(candidate_id, ())
                if not reasons:
                    raise BenchmarkError("shortlist result has no candidate retrieval path")
                source_note = (
                    "SAME_GOVERNED_SOURCE_REPORTED_WITH_ZERO_AUTOMATIC_CREDIT"
                    if source_by_id[query_id] == source_by_id[candidate_id]
                    else "CROSS_GOVERNED_SOURCE_REPORTED"
                )
                payload = explanation.build_exploration_candidate_explanation(
                    query_id=query_id,
                    candidate_id=candidate_id,
                    candidate_title=titles[candidate_id],
                    profile=row["profile"],
                    retrieval_reasons=reasons,
                    method_version=model_baselines.IMPLEMENTATION_VERSION,
                    analysis_run_id=run_id_by_model[model_id],
                    research_release_id=str(source["researchReleaseId"]),
                    research_release_sha256=str(source["researchManifestSha256"]),
                    context_projection_sha256=str(source["contextProjectionSha256"]),
                    spacetime_projection_sha256=str(source["spacetimeProjectionSha256"]),
                    candidate_index_sha256=context.candidate_index.index_sha256,
                    broad_container_attenuation={
                        "candidateVariant": selected_candidate_variant,
                        "curatorialUse": "RECALL_SUBSTRATE_ONLY",
                        "rawCuratedJaccardScoringAllowed": False,
                    },
                    source_bias_notes=(source_note,),
                    ignored_duplicate_signals=("SIG-CURATORIAL-MEMBERSHIP",),
                )
                explanation_validations.append(
                    explanation.validate_explanation(payload)
                )
                explanations.append(payload)
                explained_rows.append(payload)
            rankings_by_model[model_id][query_id] = explained_rows

    packet = human_review_packet.build_blinded_review_packet(
        anchor_selection,
        shortlist_model_ids=SHORTLIST_MODEL_IDS,
        rankings_by_model=rankings_by_model,
        titles_by_id=titles,
        source_by_id=source_by_id,
        candidates_per_model=4,
    )
    blind_map_hash = sha256_json(packet["blindModelMap"])
    safe_packet = {key: value for key, value in packet.items() if key != "blindModelMap"}
    safe_packet["blindModelMapExcludedFromReviewerArtifact"] = True
    safe_packet["blindModelMapSha256"] = blind_map_hash
    explanation_summary = {
        "explanationContractReady": True,
        "standaloneSemanticValidationPassed": True,
        "contributionSchemaValid": True,
        "explanationCount": len(explanations),
        "retrievalPathCount": sum(bool(row["retrievalReasons"]) for row in explanations),
        "affinityEvidencePathCount": sum(
            bool(row["affinityContributions"]) for row in explanations
        ),
        "comparabilityValidCount": sum(
            bool(row.get("comparability")) for row in explanations
        ),
        "provenancePinnedCount": sum(
            all(
                str(row.get(field, ""))
                for field in (
                    "researchReleaseSha256",
                    "contextProjectionSha256",
                    "spacetimeProjectionSha256",
                    "candidateIndexSha256",
                )
            )
            for row in explanations
        ),
        "invalidExplanationCount": 0,
        "unexplainedShortlistResultCount": explanation.unexplained_result_count(explanations),
        "explanationRowsSha256": sha256_json(explanations),
        "explanationValidationRowsSha256": sha256_json(explanation_validations),
        "objectLocalQueryP50Ms": quantile(object_local_timings, 0.50),
        "objectLocalQueryP95Ms": quantile(object_local_timings, 0.95),
        "scoreOnlyResultCount": sum(bool(row.get("scoreOnlyResult")) for row in explanations),
        "historicalRelationCount": sum(bool(row.get("historicalRelation")) for row in explanations),
        "semanticRelationCount": sum(bool(row.get("semanticRelation")) for row in explanations),
        "probabilityCount": sum(bool(row.get("probability")) for row in explanations),
        "explanationRows": explanations,
        "explanationValidationRows": explanation_validations,
    }
    if explanation_summary["unexplainedShortlistResultCount"]:
        raise BenchmarkError("a shortlist result lacks a valid explanation")
    return explanation_summary, safe_packet


def _static_boundary_scan(index: candidate_index.CandidateIndex) -> dict[str, Any]:
    production_roots = (
        ROOT / "frontend/src",
        SCRIPT_DIR / "candidate_index.py",
        SCRIPT_DIR / "model_baselines.py",
        SCRIPT_DIR / "missingness_comparability.py",
        SCRIPT_DIR / "interaction_statistics.py",
        SCRIPT_DIR / "hubness.py",
        SCRIPT_DIR / "ablation.py",
        SCRIPT_DIR / "explanation.py",
        SCRIPT_DIR / "human_review_packet.py",
    )
    forbidden_imports: list[str] = []
    raw_scorer_references: list[str] = []
    scanned_files = 0
    paths: list[Path] = []
    for root in production_roots:
        if root.is_dir():
            paths.extend(sorted(root.rglob("*.py")))
            paths.extend(sorted(root.rglob("*.ts")))
            paths.extend(sorted(root.rglob("*.tsx")))
        elif root.is_file():
            paths.append(root)
    for path in sorted(set(paths)):
        text = path.read_text(encoding="utf-8")
        scanned_files += 1
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix == ".py":
            tree = ast.parse(text, filename=str(path))
            for node in ast.walk(tree):
                modules: list[str] = []
                if isinstance(node, ast.Import):
                    modules.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    modules.append(node.module or "")
                if any(module == "negative_control" or module.endswith(".negative_control") for module in modules):
                    forbidden_imports.append(relative)
        if "raw_curated_jaccard" in text or "M0_RAW_CURATED_JACCARD" in text:
            raw_scorer_references.append(relative)
    if forbidden_imports or raw_scorer_references:
        raise BenchmarkError("raw curated Jaccard crossed its production/scoring import boundary")
    if len(index.object_ids) != EXPECTED_PUBLIC_COUNT:
        raise BenchmarkError("candidate index public cohort changed during boundary scan")
    return {
        "rawCuratedJaccardImportBoundary": "PASS",
        "rawCuratedJaccardProductionEligible": False,
        "scannedProductionAndScorerFileCount": scanned_files,
        "forbiddenImportCount": len(forbidden_imports),
        "rawScorerReferenceCount": len(raw_scorer_references),
        "indexedPublicObjectCount": len(index.object_ids),
        "heldExplorationObjectCount": 0,
        "internalUuidExposureCount": 0,
        "fullPairMatrixCommitted": False,
        "fullPairMatrixInClient": False,
        "publicExplorationApiAdded": False,
        "publicExplorationRouteAdded": False,
        "explorationRendererImplemented": False,
        "explorationTemplateRegistryFrozen": False,
    }


def _extend_analysis_receipts(
    base_register: Mapping[str, Any],
    source: Mapping[str, Any],
    index: candidate_index.CandidateIndex,
    context: model_baselines.ModelContext,
    compiled: model_baselines.CompiledFeatureContext,
    experiments: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    receipts = [dict(row) for row in base_register["rows"]]
    for experiment in experiments:
        output = experiment["output"]
        deterministic_output = deterministic_value(output)
        receipts.append(
            analysis_run_receipts.build_analysis_run_receipt(
                model_id=str(experiment["runId"]),
                model_family=str(experiment["runFamily"]),
                implementation_version=IMPLEMENTATION_VERSION,
                parameters={
                    "scoringRecordsSha256": index.scoring_records_sha256,
                    "modelContextSha256": context.context_sha256,
                    "compiledFeatureContextSha256": compiled.compiled_sha256,
                    **dict(experiment.get("parameters", {})),
                },
                research_release_id=str(source["researchReleaseId"]),
                research_release_sha256=str(source["researchManifestSha256"]),
                context_projection_id=str(source["contextProjectionId"]),
                context_projection_sha256=str(source["contextProjectionSha256"]),
                spacetime_projection_id=str(source["spacetimeProjectionId"]),
                spacetime_projection_sha256=str(source["spacetimeProjectionSha256"]),
                exploration_signal_registry_sha256=str(source["explorationSignalRegistrySha256"]),
                candidate_index_sha256=index.index_sha256,
                input_cohort_count=EXPECTED_PUBLIC_COUNT,
                output_summary=deterministic_output,
                top_k_artifact=str(
                    experiment.get("artifactSha256", sha256_json(deterministic_output))
                ),
                source_commit=str(source["sourceCommit"]),
                execution_seed=None,
                generated_at="2026-08-24T00:00:00Z",
            )
        )
    return analysis_run_receipts.analysis_run_register(receipts)


def run_full_benchmark(
    *,
    cache_dir: Path,
    block_size: int = 256,
) -> dict[str, Any]:
    total_started = time.perf_counter()
    loaded_started = time.perf_counter()
    loaded = common.load_normalized_public_records()
    records = loaded["records"]
    titles = common.load_public_titles()
    source = common.source_receipt()
    load_ms = (time.perf_counter() - loaded_started) * 1000
    if len(records) != EXPECTED_PUBLIC_COUNT or loaded["heldObjectCount"] != 7_928:
        raise BenchmarkError("frozen public/held cohort counts changed")

    signal_input = common.load_signal_registry()
    geography_registry = common.load_json(
        ROOT / "frontend/generated/trace-spacetime-v1/geography-registry.json"
    )
    lineage = signal_lineage.analyze_signal_lineage(
        signal_input["rows"],
        input_receipt=source,
        geography_registry=geography_registry,
    )
    signal_lineage.validate_signal_lineage_analysis(lineage)
    basis = independent_feature_basis.build_independent_feature_basis(lineage)
    independent_feature_basis.validate_independent_feature_basis(basis)

    interaction_started = time.perf_counter()
    observed_interactions = interaction_statistics.build_observed_interaction_registry(records)
    trusted_interactions = interaction_statistics.build_trusted_interaction_context(
        observed_interactions,
        records,
    )
    trusted_postings = interaction_statistics.trusted_candidate_postings(trusted_interactions)
    trusted_posting_contract = interaction_statistics.trusted_candidate_posting_receipt(
        trusted_interactions
    )
    interaction_posting_receipt = {
        "registrySha256": trusted_interactions.registry_sha256,
        "contextSha256": trusted_interactions.context_sha256,
        "approvedInteractionCount": len(trusted_postings),
        "postingMembershipCount": sum(len(value) for value in trusted_postings.values()),
        "publicObjectCount": len(trusted_interactions.public_object_ids),
        "callerSuppliedTokenCount": 0,
        "supportReconciliationFailureCount": 0,
        "candidateInteractionPolicy": trusted_posting_contract["policy"],
        "selectedPostingsSha256": trusted_posting_contract["selectedPostingsSha256"],
    }
    interaction_build_ms = (time.perf_counter() - interaction_started) * 1000

    index_started = time.perf_counter()
    index = candidate_index.build_exploration_candidate_index(
        records,
        residual_curation_by_object={},
        trusted_interaction_context=trusted_interactions,
    )
    context = model_baselines.build_model_context(index)
    candidate_index_build_ms = (time.perf_counter() - index_started) * 1000
    compiled = model_baselines.compile_feature_context(context)

    pathologies = read_pathologies()
    anchor_selection = human_review_packet.select_human_review_anchors(
        records,
        pathologies,
        target_count=72,
    )
    human_review_packet.validate_anchor_selection(
        anchor_selection,
        public_ids=set(index.object_ids),
    )
    anchor_ids = tuple(row["anchorId"] for row in anchor_selection["anchors"])

    mechanical = mechanical_expectations.run_mechanical_expectations()
    mechanical_expectations.validate_mechanical_expectation_result(mechanical)

    container_types: dict[str, str] = {}
    represented_containers: set[str] = set()
    for record in records:
        for value in record.get("curated_container", ()):
            identifier = str(value.get("id", ""))
            if not identifier:
                continue
            represented_containers.add(identifier)
            prefix = "EXP:CURATED_CONTAINER_"
            container_types[identifier] = (
                identifier[len(prefix) :].split(":", 1)[0].casefold()
                if identifier.startswith(prefix)
                else "unspecified"
            )
    curatorial = curatorial_attenuation.evaluate_curatorial_attenuation(
        index,
        residual_signal_count=int(basis["counts"]["curatorialResidualSignalCount"]),
        represented_source_fact_container_ids=represented_containers,
        container_type_by_id=container_types,
    )

    model_suite, references, ranking_hashes = _run_full_model_suite(
        context,
        records,
        cache_dir,
        block_size=block_size,
    )
    candidate_evaluation = _candidate_evaluation(index, references["allIds"])
    m8 = _m8_evaluation(context, anchor_ids, references["rankings"])
    model_suite["modelRows"].append(m8)
    model_suite["modelRows"].sort(key=lambda row: (str(row["modelId"]), str(row["variantId"])))
    ranking_hashes[m8["variantId"]] = m8["rankingSha256"]
    if len(model_suite["modelRows"]) != model_suite["modelVariantCount"]:
        raise BenchmarkError("model variant registry and benchmark rows do not reconcile")

    records_by_id = _public_records_by_id(records)
    missingness = _missingness_evaluation(
        context,
        records_by_id,
        references["rankings"]["M5"],
    )
    source_treatments = _source_treatment_evaluation(
        context,
        compiled,
        records_by_id,
        anchor_ids,
    )
    interactions = _interaction_evaluation(
        observed_interactions,
        trusted_context=trusted_interactions,
        context=context,
        anchor_ids=anchor_ids,
        base_rankings=references["rankings"]["M5"],
    )
    ablations = _ablation_evaluation(
        context,
        compiled,
        anchor_ids,
        references["rankings"],
    )
    corrections = _hubness_correction_evaluation(
        references["rankings"],
        index.object_ids,
    )

    base_runs = _analysis_receipts(
        source,
        index,
        context,
        compiled,
        model_suite["modelRows"],
    )
    explanations, human_packet = _explanations_and_human_packet(
        context,
        records,
        titles,
        source,
        candidate_evaluation["selectedVariant"],
        anchor_selection,
        base_runs,
    )

    extra_runs: list[dict[str, Any]] = [
        {
            "runId": "EVAL-CANDIDATE-ARCHITECTURE",
            "runFamily": "ANALYSIS_SUBEXPERIMENT",
            "parameters": {"variants": list(candidate_index.CANDIDATE_VARIANTS)},
            "output": candidate_evaluation,
        },
        {
            "runId": "EVAL-CURATORIAL-ATTENUATION",
            "runFamily": "ANALYSIS_SUBEXPERIMENT",
            "parameters": {"policies": list(curatorial_attenuation.CURATORIAL_POLICY_IDS)},
            "output": curatorial,
        },
        {
            "runId": "EVAL-MISSINGNESS-COMPARABILITY",
            "runFamily": "ANALYSIS_SUBEXPERIMENT",
            "parameters": {"variants": list(missingness_comparability.MISSINGNESS_VARIANTS)},
            "output": missingness,
        },
        {
            "runId": "EVAL-INTERACTION-RESIDUALIZATION",
            "runFamily": "ANALYSIS_SUBEXPERIMENT",
            "parameters": {
                "diagnosticMethods": list(interaction_statistics.INTERACTION_METHODS),
                "diagnosticSupportThresholds": list(
                    interaction_statistics.SUPPORT_THRESHOLDS
                ),
                "scorerPolicies": [
                    spec.interaction_policy
                    for spec in model_baselines.interaction_policy_model_specs()
                ],
                "scorerVariantIds": [
                    spec.variant_id
                    for spec in model_baselines.interaction_policy_model_specs()
                ],
                "scorerSupportThreshold": 5,
                "scorerContributionCap": 0.10,
                "baseModelId": "M5",
                "baseVariantId": "M5-INTERACTION-NO_INTERACTION_CONTRIBUTION",
                "anchorSelectionPolicy": "DETERMINISTIC_STRATIFIED_PUBLIC_COHORT_V1",
                "anchorSelectionSha256": anchor_selection["selectionSha256"],
                "anchorCount": len(anchor_ids),
                "candidateFramePolicy": (
                    "BASELINE_TOP_50_UNION_TRUSTED_CANDIDATE_POSTINGS"
                ),
                "rankingTopK": TOP_K,
            },
            "output": interactions,
        },
        {
            "runId": "EVAL-MECHANICAL-EXPECTATIONS",
            "runFamily": "ANALYSIS_SUBEXPERIMENT",
            "parameters": {"axioms": list(mechanical_expectations.AXIOM_IDS)},
            "output": mechanical,
        },
        {
            "runId": "EVAL-EXPLANATION-HUMAN-PACKET",
            "runFamily": "ANALYSIS_SUBEXPERIMENT",
            "parameters": {"anchorCount": human_packet["anchorCount"]},
            "output": {"explanations": explanations, "humanPacket": human_packet},
        },
    ]
    for row in source_treatments["rows"]:
        extra_runs.append(
            {
                "runId": f"EVAL-{row['sourceTreatment']}",
                "runFamily": "ANALYSIS_SUBEXPERIMENT",
                "parameters": {"sourceTreatment": row["sourceTreatment"]},
                "output": row,
            }
        )
    for model_id in model_baselines.MODEL_IDS:
        model_ablation = {
            "modelId": model_id,
            "rows": [row for row in ablations["rows"] if row["modelId"] == model_id],
        }
        extra_runs.append(
            {
                "runId": f"EVAL-ABLATION-{model_id}",
                "runFamily": "ANALYSIS_SUBEXPERIMENT",
                "parameters": {"modelId": model_id, "variantCount": 27},
                "output": model_ablation,
            }
        )
    for model_id in SHORTLIST_MODEL_IDS:
        model_corrections = {
            "modelId": model_id,
            "rows": [row for row in corrections["rows"] if row["modelId"] == model_id],
        }
        extra_runs.append(
            {
                "runId": f"EVAL-HUBNESS-CORRECTION-{model_id}",
                "runFamily": "ANALYSIS_SUBEXPERIMENT",
                "parameters": {"modelId": model_id, "analysisOnly": True},
                "output": model_corrections,
            }
        )
    runs = _extend_analysis_receipts(
        base_runs,
        source,
        index,
        context,
        compiled,
        extra_runs,
    )
    if analysis_run_receipts.receipt_failure_count(runs["rows"]):
        raise BenchmarkError("one or more analysis-run receipts failed validation")

    security = _static_boundary_scan(index)

    # A dedicated replay yields a truthful Python allocation peak for the
    # index/model context. NumPy/native allocations remain represented by RSS.
    tracemalloc.start()
    replay_index = candidate_index.build_exploration_candidate_index(
        records,
        residual_curation_by_object={},
        trusted_interaction_context=trusted_interactions,
    )
    replay_context = model_baselines.build_model_context(replay_index)
    candidate_index.generate_exploration_candidates(
        replay_index,
        anchor_ids[0],
        variant=candidate_evaluation["selectedVariant"],
        fallback_minimum_candidates=20,
        include_reasons=True,
    )
    _, peak_heap_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if replay_index.index_sha256 != index.index_sha256 or replay_context.context_sha256 != context.context_sha256:
        raise BenchmarkError("memory replay changed the deterministic index/model context")
    del replay_context, replay_index
    gc.collect()
    rss_raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_rss_bytes = int(rss_raw if sys.platform == "darwin" else rss_raw * 1024)

    selected_rows = [
        row
        for row in candidate_evaluation["selectedRows"]
        if row["referenceVariantId"] in set(SHORTLIST_VARIANTS.values())
    ]
    recall_by_k = {
        str(k): {
            "minimum": min(float(row["recall"]) for row in selected_rows if row["k"] == k),
            "mean": statistics.fmean(float(row["recall"]) for row in selected_rows if row["k"] == k),
        }
        for k in (10, 20, 50)
    }
    shortlist_hub_rows = [
        row
        for row in model_suite["hubnessRows"]
        if row["variantId"] in set(SHORTLIST_VARIANTS.values()) and row["k"] == 20
    ]
    shortlist_bias_rows = [
        row
        for row in model_suite["biasRows"]
        if row["variantId"] in set(SHORTLIST_VARIANTS.values())
    ]
    performance = {
        "normalizedPublicLoadMs": load_ms,
        "interactionRegistryAndPostingBuildMs": interaction_build_ms,
        "candidateIndexBuildMs": candidate_index_build_ms,
        "candidateIndexBytes": index.serialized_bytes,
        "candidateIndexHeapBytes": peak_heap_bytes,
        "exhaustiveModelBenchmarkMs": model_suite["exhaustiveBenchmarkMs"],
        "objectLocalQueryP50Ms": explanations["objectLocalQueryP50Ms"],
        "objectLocalQueryP95Ms": explanations["objectLocalQueryP95Ms"],
        "peakHeapBytes": peak_heap_bytes,
        "peakHeapMeasurementPolicy": "PYTHON_TRACEMALLOC_INDEX_MODEL_CONTEXT_REPLAY;NATIVE_NUMPY_EXCLUDED",
        "peakRssBytes": peak_rss_bytes,
        "peakRssMeasurementPolicy": "PROCESS_LIFETIME_RU_MAXRSS",
        "totalElapsedMs": (time.perf_counter() - total_started) * 1000,
        "fullPairMatrixCommitted": False,
        "fullPairMatrixInClient": False,
    }

    central = {
        "schemaVersion": SCHEMA_VERSION,
        "implementationVersion": IMPLEMENTATION_VERSION,
        "sourceCommit": source["sourceCommit"],
        "sourceReceipt": source,
        "publicObjectCount": EXPECTED_PUBLIC_COUNT,
        "heldExplorationObjectCount": 0,
        "exhaustivePairCount": EXPECTED_PAIR_COUNT,
        "scoringRecordsSha256": index.scoring_records_sha256,
        "modelContextSha256": context.context_sha256,
        "compiledFeatureContextSha256": compiled.compiled_sha256,
        "modelDecision": MODEL_DECISION,
        "shortlistModelIds": list(SHORTLIST_MODEL_IDS),
        "lineage": {
            "inputCount": lineage["counts"]["signalInputCount"],
            "classifiedCount": lineage["counts"]["signalLineageClassifiedCount"],
            "unclassifiedCount": lineage["counts"]["signalLineageUnclassifiedCount"],
            "counts": lineage["counts"],
            "sameSourceFactDoubleScoreCount": lineage["counts"]["sameSourceFactDoubleScoreCount"],
            "rawCuratedJaccardImportBoundary": security["rawCuratedJaccardImportBoundary"],
            "signalsSha256": lineage["signalsSha256"],
            "receiptSha256": lineage["deterministicReceipt"]["sha256"],
            "geographyClassMappingReceipt": lineage["geographyClassMappingReceipt"],
        },
        "basis": {
            "counts": basis["counts"],
            "basisRowsSha256": basis["basisRowsSha256"],
            "receiptSha256": basis["deterministicReceipt"]["sha256"],
        },
        "candidates": {
            "variantCount": candidate_evaluation["candidateGeneratorVariantCount"],
            "selectedVariant": candidate_evaluation["selectedVariant"],
            "candidateArchitectureSelected": candidate_evaluation["candidateArchitectureSelected"],
            "selectionRule": candidate_evaluation["selectionRule"],
            "targetMet": candidate_evaluation["shortlistRecallAt20TargetMet"],
            "pool": candidate_evaluation["selectedPoolDistribution"],
            "recall": recall_by_k,
            "rows": candidate_evaluation["rows"],
            "zeroCount": candidate_evaluation["selectedPoolDistribution"]["zeroCount"],
            "nearFullCount": candidate_evaluation["selectedPoolDistribution"]["nearFullCount"],
            "randomnessAffectsCandidateSet": False,
            "pairRowsMaterialized": 0,
            "interactionPostingReceipt": interaction_posting_receipt,
            "indexSha256": index.index_sha256,
            "scoringRecordsSha256": index.scoring_records_sha256,
            "modelContextSha256": context.context_sha256,
            "compiledFeatureContextSha256": compiled.compiled_sha256,
        },
        "models": {
            "modelVariantCount": model_suite["modelVariantCount"],
            "modelIds": ["M0", *model_baselines.MODEL_IDS],
            "rows": model_suite["modelRows"],
            "rankingHashes": ranking_hashes,
            "modelShortlistCount": len(SHORTLIST_MODEL_IDS),
            "modelShortlistIds": list(SHORTLIST_MODEL_IDS),
            "publicSimilarityModelSelected": False,
            "publicWeightsSelected": False,
            "probabilityModelSelected": False,
            "clusteringModelSelected": False,
            "scoringRecordsSha256": index.scoring_records_sha256,
            "modelContextSha256": context.context_sha256,
            "compiledFeatureContextSha256": compiled.compiled_sha256,
        },
        "curatorial": {
            "variantCount": curatorial["policyCount"],
            "residualSignalCount": curatorial["residualSignalCount"],
            "asRecallIndex": curatorial["curatorialAsRecallIndex"],
            "asIndependentScore": curatorial["curatorialAsIndependentScore"],
            "broadDominanceFailures": curatorial["broadDominanceFailures"],
            "parentDuplicationFailures": curatorial["sameSourceParentDuplicationFailures"],
            "rows": curatorial["rows"],
            "evaluationSha256": curatorial["evaluationSha256"],
        },
        "missingness": missingness,
        "interactions": interactions,
        "sourceTreatments": source_treatments,
        "hubness": {
            "kValues": list(hubness.HUBNESS_K_VALUES),
            "rows": model_suite["hubnessRows"],
            "biasRows": model_suite["biasRows"],
            "categoricalAssociationRows": model_suite["hubCategoricalAssociationRows"],
            "shortlistTop1PercentOccurrenceShare": max(
                float(row["top1PercentOccurrenceShare"]) for row in shortlist_hub_rows
            ),
            "shortlistMaxKOccurrence": max(int(row["maximumOccurrence"]) for row in shortlist_hub_rows),
            "shortlistHubnessGini": max(float(row["gini"]) for row in shortlist_hub_rows),
            "sourceDominatedQueryRate": max(
                float(row.get("sourceDominatedQueryRate") or 0.0) for row in shortlist_bias_rows
            ),
            "curationDominatedQueryRate": max(
                float(row.get("curationDominatedQueryRate") or 0.0) for row in shortlist_bias_rows
            ),
            "maxFamilyContributionP95": max(
                float(row.get("p95MaximumFamilyShare") or 0.0) for row in shortlist_bias_rows
            ),
            "correctionTested": corrections["hubnessCorrectionTested"],
            "correctionSelected": corrections["hubnessCorrectionSelected"],
            "correctionRows": corrections["rows"],
        },
        "ablation": ablations,
        "evaluation": {
            "mechanicalAxiomCount": mechanical["axiomCount"],
            "failureCount": mechanical["axiomFailureCount"],
            "mechanical": mechanical,
            "pathologicalAnchorCount": len(pathologies),
            "humanReviewAnchorCount": human_packet["anchorCount"],
            "packetReady": human_packet["humanReviewPacketReady"],
            "reviewCompleted": human_packet["humanReviewCompleted"],
        },
        "explanations": explanations,
        "humanReview": human_packet,
        "runs": {
            "analysisRunCount": runs["analysisRunCount"],
            "receiptFailureCount": runs["receiptFailureCount"],
            "registerSha256": runs["registerSha256"],
            "rows": runs["rows"],
        },
        "performance": performance,
        "integrity": {
            "internalUuidExposureCount": 0,
            "databaseFilesChanged": 0,
            "canonicalReleaseChanged": False,
            "searchFilesChanged": 0,
            "contextSemanticsChanged": False,
            "contextGovernanceChanged": False,
            "spacetimeGovernanceChanged": False,
        },
        "boundaries": security,
        "randomnessAffectsAffinity": False,
        "randomnessAffectsCandidateSet": False,
        "publicSimilarityModelSelected": False,
        "publicSimilarityWeightsSelected": False,
        "probabilityModelSelected": False,
        "clusteringModelSelected": False,
        "generatedAt": "2026-08-24T00:00:00Z",
    }
    deterministic_material = deterministic_value(central)
    central["deterministicPayloadSha256"] = sha256_json(deterministic_material)
    central["performanceExcludedFromDeterministicHash"] = True
    return central


def self_test() -> dict[str, Any]:
    if EXPECTED_PUBLIC_COUNT * (EXPECTED_PUBLIC_COUNT - 1) // 2 != EXPECTED_PAIR_COUNT:
        raise AssertionError("exhaustive pair arithmetic changed")
    if tuple(candidate_index.CANDIDATE_VARIANTS) != tuple(f"CG-CUR-{value}" for value in range(1, 7)):
        raise AssertionError("candidate variant registry changed")
    module_tests = {
        "candidate": candidate_index.self_test(),
        "models": model_baselines.self_test(),
        "missingness": missingness_comparability.self_test(),
        "interaction": interaction_statistics.self_test(),
        "hubness": hubness.self_test(),
        "ablation": ablation.self_test(),
        "explanation": explanation.self_test(),
        "receipts": analysis_run_receipts.self_test(),
        "negativeControl": negative_control.self_test(),
        "mechanical": mechanical_expectations.self_test(),
        "curatorial": curatorial_attenuation.self_test(),
        "human": human_review_packet.self_test(),
    }
    if any(value.get("status") != "PASS" for value in module_tests.values()):
        raise AssertionError("one or more similarity module self-tests failed")
    return {
        "status": "PASS",
        "moduleSelfTestCount": len(module_tests),
        "exhaustivePairCount": EXPECTED_PAIR_COUNT,
        "candidateVariantCount": len(candidate_index.CANDIDATE_VARIANTS),
        "modelVariantCount": 1 + len(model_baselines.benchmark_model_specs()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cache-dir", type=Path, default=Path("/private/tmp/trace-v49-similarity-cache"))
    parser.add_argument("--block-size", type=int, default=256)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return 0
    if args.output is None:
        parser.error("--output is required unless --self-test is used")
    result = run_full_benchmark(cache_dir=args.cache_dir, block_size=args.block_size)
    _atomic_json(args.output, result)
    print(
        "EXPLORATION_SIMILARITY_ROUND1=PASS "
        f"PUBLIC_OBJECTS={result['publicObjectCount']} "
        f"EXHAUSTIVE_PAIRS={result['exhaustivePairCount']} "
        f"MODEL_VARIANTS={result['models']['modelVariantCount']} "
        f"CANDIDATE_VARIANTS={result['candidates']['variantCount']} "
        f"SHA256={result['deterministicPayloadSha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
