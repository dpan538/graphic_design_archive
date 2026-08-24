#!/usr/bin/env python3
"""Independent-channel comparison against frozen Round 6 M2/M5/M7 research."""

from __future__ import annotations

import importlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import lexical_common as common


IMPLEMENTATION_VERSION = "trace-nlp-structured-disagreement-2026-08-24"
ROUND6_DIR = common.ROOT / "scripts/exploration-v49-similarity"
EXPECTED_CANDIDATE_INDEX_SHA256 = "abba30fcdded21b8f1ba6f7ec87a47b6bbd83c0d1e40d90670143fb88b83873f"
STRUCTURED_VARIANTS = {
    "M2": "M2-SMOOTHED_IDF",
    "M5": "M5-GOWER-TEMP-4",
    "M7": "M7-BM25F-QUERY",
}
STRUCTURED_CANDIDATE_VARIANT = "CG-CUR-4"


def _round6_modules() -> dict[str, Any]:
    path = str(ROUND6_DIR)
    # The NLP source-governance package also has a module named ``common``.
    # Importing Round 6's module by that bare name would therefore depend on
    # import order and can silently return the wrong API after corpus loading.
    # Load the frozen Round 6 common module through the unique-name adapter and
    # import only the dependency modules whose names do not collide.
    if path in sys.path:
        sys.path.remove(path)
    sys.path.insert(0, path)
    names = (
        "candidate_index",
        "interaction_statistics",
        "model_baselines",
    )
    try:
        modules = {name: importlib.import_module(name) for name in names}
        modules["common"] = common._load_round6_common()
        return modules
    except ImportError as error:
        raise common.LexicalContractError("frozen Round 6 modules are unavailable") from error


def build_structured_anchor_rankings(
    anchor_ids: Sequence[str],
    *,
    ranking_depth: int = 50,
    enforce_review_packet_size: bool = True,
) -> dict[str, Any]:
    anchors = tuple(sorted(set(map(str, anchor_ids))))
    if len(anchors) != len(anchor_ids):
        raise common.LexicalContractError("structured/NLP anchors are duplicated")
    if enforce_review_packet_size and not 24 <= len(anchors) <= 36:
        raise common.LexicalContractError("structured/NLP review anchor count must be 24--36")
    if ranking_depth < 20:
        raise common.LexicalContractError("structured comparison needs rankings through at least 20")
    modules = _round6_modules()
    round6_common = modules["common"]
    candidate_index = modules["candidate_index"]
    interaction_statistics = modules["interaction_statistics"]
    model_baselines = modules["model_baselines"]

    started = time.perf_counter()
    loaded = round6_common.load_normalized_public_records()
    records = loaded["records"]
    if len(records) != common.PUBLIC_OBJECT_COUNT or loaded["heldObjectCount"] != common.HELD_OBJECT_COUNT:
        raise common.LexicalContractError("Round 6 public/held cohort changed")
    public_ids = {str(record["objectId"]) for record in records}
    if set(anchors) - public_ids:
        raise common.LexicalContractError("structured/NLP anchor is outside the public cohort")
    observed = interaction_statistics.build_observed_interaction_registry(records)
    trusted = interaction_statistics.build_trusted_interaction_context(observed, records)
    index = candidate_index.build_exploration_candidate_index(
        records,
        residual_curation_by_object={},
        trusted_interaction_context=trusted,
    )
    if index.index_sha256 != EXPECTED_CANDIDATE_INDEX_SHA256:
        raise common.LexicalContractError("CG-CUR-4 candidate-index pin changed")
    context = model_baselines.build_model_context(index)
    specs_by_variant = {
        spec.variant_id: spec for spec in model_baselines.benchmark_model_specs()
    }
    specs = {}
    for model_id, variant_id in STRUCTURED_VARIANTS.items():
        spec = specs_by_variant.get(variant_id)
        if spec is None or spec.model_id != model_id:
            raise common.LexicalContractError("Round 6 shortlist parameter variant is unavailable")
        specs[model_id] = spec

    rankings = {model_id: {} for model_id in STRUCTURED_VARIANTS}
    candidate_ids_by_anchor = {}
    candidate_set_hashes = {}
    for anchor_id in anchors:
        candidate_set = candidate_index.generate_exploration_candidates(
            index,
            anchor_id,
            variant=STRUCTURED_CANDIDATE_VARIANT,
            fallback_minimum_candidates=20,
            include_reasons=False,
        )
        candidate_ids_by_anchor[anchor_id] = frozenset(candidate_set.candidate_ids)
        candidate_set_hashes[anchor_id] = candidate_set.candidate_set_sha256
        for model_id, spec in specs.items():
            rankings[model_id][anchor_id] = model_baselines.rank_candidates(
                context,
                anchor_id,
                candidate_set.candidate_ids,
                spec,
                k=ranking_depth,
            )
    rank_material = {
        model_id: {
            anchor_id: [row["candidateId"] for row in rankings[model_id][anchor_id]]
            for anchor_id in anchors
        }
        for model_id in STRUCTURED_VARIANTS
    }
    return {
        "schemaVersion": "trace-nlp-frozen-structured-rankings/v1",
        "implementationVersion": IMPLEMENTATION_VERSION,
        "candidateVariant": STRUCTURED_CANDIDATE_VARIANT,
        "candidateIndexSha256": index.index_sha256,
        "structuredVariants": dict(STRUCTURED_VARIANTS),
        "anchorIds": list(anchors),
        "anchorCount": len(anchors),
        "rankingDepth": ranking_depth,
        "rankingIdsSha256": common.sha256_json(rank_material),
        "candidateSetHashesSha256": common.sha256_json(candidate_set_hashes),
        "buildAndQueryMs": (time.perf_counter() - started) * 1000.0,
        "cgCur4Changed": False,
        "m2SpecificationChanged": False,
        "m5SpecificationChanged": False,
        "m7SpecificationChanged": False,
        "fusionSelected": False,
        "rankings": rankings,
        # Runtime-only objects are needed to explain NLP-only candidates. They
        # are explicitly removed by strip_runtime before any evidence write.
        "_runtime": {
            "context": context,
            "specs": specs,
            "candidateIdsByAnchor": candidate_ids_by_anchor,
            "modelBaselines": model_baselines,
        },
    }


def _rank_lookup(rows: Sequence[Mapping[str, Any]], id_field: str) -> dict[str, int]:
    return {str(row[id_field]): int(row["rank"]) for row in rows}


def _classify(
    *,
    structured_rank: int | None,
    nlp_rank: int | None,
    structured_candidate_eligible: bool,
    high_cutoff: int,
    low_cutoff: int,
) -> str:
    if structured_rank is not None and structured_rank <= high_cutoff:
        if nlp_rank is not None and nlp_rank <= high_cutoff:
            return "BOTH_HIGH"
        if nlp_rank is None or nlp_rank > low_cutoff:
            return "HIGH_STRUCTURED_LOW_NLP"
        return "HIGH_STRUCTURED_MID_NLP"
    if nlp_rank is not None and nlp_rank <= high_cutoff:
        if not structured_candidate_eligible:
            return "HIGH_NLP_OUTSIDE_STRUCTURED_RETRIEVAL"
        if structured_rank is None or structured_rank > low_cutoff:
            return "LOW_STRUCTURED_HIGH_NLP"
        return "MID_STRUCTURED_HIGH_NLP"
    return "NOT_IN_HIGH_UNION"


def compare_independent_channels(
    structured: Mapping[str, Any],
    nlp_result: Mapping[str, Any],
    corpus: common.CorpusBundle,
    *,
    high_cutoff: int = 20,
    low_cutoff: int = 50,
) -> dict[str, Any]:
    if high_cutoff <= 0 or low_cutoff < high_cutoff:
        raise common.LexicalContractError("structured/NLP rank thresholds are invalid")
    nlp_rankings = nlp_result.get("rankings")
    if not isinstance(nlp_rankings, Mapping):
        raise common.LexicalContractError("structured/NLP comparison needs in-memory NLP rankings")
    runtime = structured.get("_runtime")
    if not isinstance(runtime, Mapping):
        raise common.LexicalContractError("structured runtime context was stripped before comparison")
    model_baselines = runtime["modelBaselines"]
    context = runtime["context"]
    specs = runtime["specs"]
    candidate_sets = runtime["candidateIdsByAnchor"]
    source_by_id = {
        object_id: str(record.field_values.get("source", ("NOT_GOVERNED",))[0])
        if record.field_values.get("source")
        else "NOT_GOVERNED"
        for object_id, record in context.candidate_index.records.items()
    }
    comparison_rows = []
    summary_rows = []
    for model_id in STRUCTURED_VARIANTS:
        overlaps = []
        category_counts: dict[str, int] = {}
        for anchor_id in structured["anchorIds"]:
            if anchor_id not in nlp_rankings:
                raise common.LexicalContractError("NLP rankings omit a structured comparison anchor")
            structured_rows = structured["rankings"][model_id][anchor_id]
            nlp_rows = nlp_rankings[anchor_id]
            structured_lookup = _rank_lookup(structured_rows, "candidateId")
            nlp_lookup = _rank_lookup(nlp_rows, "candidatePublicId")
            structured_top = set(
                candidate_id for candidate_id, rank in structured_lookup.items() if rank <= high_cutoff
            )
            nlp_top = set(candidate_id for candidate_id, rank in nlp_lookup.items() if rank <= high_cutoff)
            overlap = len(structured_top & nlp_top)
            overlaps.append(overlap / len(structured_top | nlp_top) if structured_top | nlp_top else 0.0)
            for candidate_id in sorted(structured_top | nlp_top):
                eligible = candidate_id in candidate_sets[anchor_id]
                structured_rank = structured_lookup.get(candidate_id)
                nlp_rank = nlp_lookup.get(candidate_id)
                category = _classify(
                    structured_rank=structured_rank,
                    nlp_rank=nlp_rank,
                    structured_candidate_eligible=eligible,
                    high_cutoff=high_cutoff,
                    low_cutoff=low_cutoff,
                )
                category_counts[category] = category_counts.get(category, 0) + 1
                structured_row = next(
                    (row for row in structured_rows if row["candidateId"] == candidate_id),
                    None,
                )
                if structured_row is None:
                    profile = model_baselines.score_pair(
                        context,
                        anchor_id,
                        candidate_id,
                        specs[model_id],
                    ).as_dict()
                else:
                    profile = structured_row["profile"]
                candidate_aspect = corpus.documents_by_id[candidate_id].aspects.get(
                    nlp_result["aspectIds"][0]
                )
                anchor_aspect = corpus.documents_by_id[anchor_id].aspects.get(
                    nlp_result["aspectIds"][0]
                )
                comparison_rows.append(
                    {
                        "anchorPublicId": anchor_id,
                        "candidatePublicId": candidate_id,
                        "structuredModelId": model_id,
                        "structuredVariantId": STRUCTURED_VARIANTS[model_id],
                        "nlpMethodId": nlp_result["methodId"],
                        "classification": category,
                        "structuredCandidateEligible": eligible,
                        "structuredRank": structured_rank,
                        "nlpRank": nlp_rank,
                        "contextMatch": profile["familyScores"].get("context"),
                        "temporalMatch": profile["familyScores"].get("temporal"),
                        "geographyMatch": profile["familyScores"].get("geography"),
                        "descriptiveMatch": profile["familyScores"].get("descriptive"),
                        "textAspect": nlp_result["aspectIds"][0],
                        "anchorLanguageScriptState": (
                            anchor_aspect.language_script_state if anchor_aspect is not None else "UNAVAILABLE"
                        ),
                        "candidateLanguageScriptState": (
                            candidate_aspect.language_script_state if candidate_aspect is not None else "UNAVAILABLE"
                        ),
                        "sameSourceDiagnostic": source_by_id[anchor_id] == source_by_id[candidate_id],
                        "historicalRelation": False,
                        "semanticRelation": False,
                        "probability": False,
                    }
                )
        summary_rows.append(
            {
                "structuredModelId": model_id,
                "structuredVariantId": STRUCTURED_VARIANTS[model_id],
                "nlpMethodId": nlp_result["methodId"],
                "anchorCount": len(structured["anchorIds"]),
                "meanTop20Jaccard": sum(overlaps) / len(overlaps),
                **{f"{key}CaseCount": value for key, value in sorted(category_counts.items())},
            }
        )
    comparison_rows.sort(
        key=lambda row: (
            row["structuredModelId"],
            row["anchorPublicId"],
            row["classification"],
            row["candidatePublicId"],
        )
    )
    return {
        "schemaVersion": "trace-nlp-structured-disagreement/v1",
        "implementationVersion": IMPLEMENTATION_VERSION,
        "anchorCount": len(structured["anchorIds"]),
        "highRankCutoff": high_cutoff,
        "lowRankCutoff": low_cutoff,
        "candidateVariant": STRUCTURED_CANDIDATE_VARIANT,
        "candidateIndexSha256": structured["candidateIndexSha256"],
        "structuredNlpFusionSelected": False,
        "structuredNlpFusionWeightsSelected": False,
        "summaryRows": summary_rows,
        "comparisonRows": comparison_rows,
        "comparisonRowsSha256": common.sha256_json(comparison_rows),
    }


def strip_runtime(structured: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in structured.items()
        if key not in {"_runtime", "rankings"}
    }


def self_test() -> dict[str, Any]:
    cases = {
        _classify(
            structured_rank=1,
            nlp_rank=2,
            structured_candidate_eligible=True,
            high_cutoff=20,
            low_cutoff=50,
        ): "BOTH_HIGH",
        _classify(
            structured_rank=3,
            nlp_rank=None,
            structured_candidate_eligible=True,
            high_cutoff=20,
            low_cutoff=50,
        ): "HIGH_STRUCTURED_LOW_NLP",
        _classify(
            structured_rank=None,
            nlp_rank=4,
            structured_candidate_eligible=False,
            high_cutoff=20,
            low_cutoff=50,
        ): "HIGH_NLP_OUTSIDE_STRUCTURED_RETRIEVAL",
    }
    if any(key != value for key, value in cases.items()):
        raise common.LexicalContractError("structured/NLP classification self-test failed")
    return {
        "schemaVersion": "trace-nlp-structured-disagreement-self-test/v1",
        "candidateVariant": STRUCTURED_CANDIDATE_VARIANT,
        "structuredVariants": dict(STRUCTURED_VARIANTS),
        "fusionSelected": False,
        "outsideCandidatePoolDistinguished": True,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
