#!/usr/bin/env python3
"""Predeclared ranking robustness/ablation diagnostics for TRACE NLP.

This module compares already-computed bounded rankings.  It does not mutate
governed text, optimize prompts or weights, select a production channel, or
collapse aspect-specific results into one affinity score.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

import common as governance_common


SCHEMA_VERSION = "trace-nlp-robustness-ablation/v1"
IMPLEMENTATION_VERSION = "trace-nlp-robustness-ablation-2026-08-24"
DEFAULT_K_VALUES = (10, 20, 50)
MAX_K = 50
MAX_WORST_QUERY_ROWS = 50
SUITE_STATUSES = ("COMPLETED", "NOT_RUN", "STOPPED_RECOVERABLE_CHECKPOINT")


class RobustnessAblationError(ValueError):
    """Raised when ranking variants cannot support a valid comparison."""


@dataclass(frozen=True)
class AblationSpec:
    ablation_id: str
    family: str
    comparison: str
    requires_reencoding: bool
    governed_text_mutation_allowed: bool
    selection_role: str = "SENSITIVITY_ONLY"


DECLARED_ABLATIONS = (
    AblationSpec(
        "MAX_LENGTH_128",
        "TRUNCATION",
        "fixed tokenizer cap 128 versus declared baseline",
        True,
        False,
    ),
    AblationSpec(
        "MAX_LENGTH_256",
        "TRUNCATION",
        "fixed tokenizer cap 256 versus declared baseline",
        True,
        False,
    ),
    AblationSpec(
        "MAX_LENGTH_512",
        "TRUNCATION",
        "fixed tokenizer cap 512 versus declared baseline",
        True,
        False,
    ),
    AblationSpec(
        "OFFICIAL_ASYMMETRIC_VS_PLAIN_DIAGNOSTIC",
        "INPUT_MODE",
        "official query/plain-document retrieval versus separately labeled plain/plain diagnostic",
        True,
        False,
    ),
    AblationSpec(
        "TITLE_ONLY",
        "ASPECT",
        "NLP_TITLE isolated",
        True,
        False,
    ),
    AblationSpec(
        "SUBJECT_ONLY",
        "ASPECT",
        "NLP_SUBJECT isolated",
        True,
        False,
    ),
    AblationSpec(
        "SOURCE_NARRATIVE_ONLY",
        "ASPECT",
        "NLP_SOURCE_NARRATIVE isolated; never silently merged",
        True,
        False,
    ),
    AblationSpec(
        "SOURCE_IDENTITY_MASKED",
        "LEAKAGE",
        "governance-provided source-identity-masked variant only",
        True,
        False,
    ),
    AblationSpec(
        "REGISTERED_BOILERPLATE_REMOVED",
        "LEAKAGE",
        "governance-provided registered-boilerplate removal only",
        True,
        False,
    ),
    AblationSpec("MARKUP_CLEANED", "ROBUSTNESS", "parser-cleaned markup versus original approved text", True, False),
    AblationSpec("CASE_NORMALIZED", "ROBUSTNESS", "case-normalized versus case-preserving semantic input", True, False),
    AblationSpec("PUNCTUATION_VARIANT", "ROBUSTNESS", "controlled punctuation-preserving/removal sensitivity", True, False),
    AblationSpec("HYPHEN_VARIANT", "ROBUSTNESS", "controlled hyphen-codepoint sensitivity", True, False),
    AblationSpec("APOSTROPHE_VARIANT", "ROBUSTNESS", "controlled apostrophe-codepoint sensitivity", True, False),
    AblationSpec("UNICODE_CANONICAL_VARIANT", "ROBUSTNESS", "canonically equivalent NFC/NFD sensitivity", True, False),
    AblationSpec("DIACRITIC_FOLDED_LEXICAL_VIEW", "ROBUSTNESS", "diacritic-preserving versus separately versioned folded lexical view", True, False),
    AblationSpec("WIDTH_COMPATIBILITY_LEXICAL_VIEW", "ROBUSTNESS", "full-width/half-width compatibility sensitivity", True, False),
)
DECLARED_ABLATION_IDS = tuple(spec.ablation_id for spec in DECLARED_ABLATIONS)


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _candidate_id(row: Any) -> str:
    if isinstance(row, Mapping):
        value = row.get("candidatePublicId", row.get("candidateId"))
    elif isinstance(row, str):
        value = row
    else:
        raise RobustnessAblationError("ranking row lacks candidate public ID")
    value = str(value or "")
    if not value:
        raise RobustnessAblationError("ranking row lacks candidate public ID")
    return value


def _ranking_ids(ranking: Sequence[Any], k: int) -> tuple[str, ...]:
    values = tuple(_candidate_id(row) for row in ranking[:k])
    if len(values) != k:
        raise RobustnessAblationError("ranking is shorter than the declared top-k")
    if len(values) != len(set(values)):
        raise RobustnessAblationError("ranking contains a duplicate candidate")
    return values


def top_k_overlap(reference: Sequence[Any], variant: Sequence[Any], *, k: int) -> float:
    if k <= 0 or k > MAX_K:
        raise RobustnessAblationError("top-k overlap bound is invalid")
    left = set(_ranking_ids(reference, k))
    right = set(_ranking_ids(variant, k))
    return len(left & right) / k


def _flatten_numeric(value: Mapping[str, Any], *, prefix: str = "") -> dict[str, float]:
    result: dict[str, float] = {}
    for key, child in sorted(value.items()):
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(child, Mapping):
            result.update(_flatten_numeric(child, prefix=path))
        elif isinstance(child, (int, float)) and not isinstance(child, bool) and math.isfinite(float(child)):
            result[path] = float(child)
    return result


def _diagnostic_delta(
    reference_result: Mapping[str, Any],
    variant_result: Mapping[str, Any],
    key: str,
) -> dict[str, Any]:
    reference = reference_result.get(key)
    variant = variant_result.get(key)
    if not isinstance(reference, Mapping) or not isinstance(variant, Mapping):
        raise RobustnessAblationError(f"robustness comparison lacks {key}")
    left = _flatten_numeric(reference)
    right = _flatten_numeric(variant)
    shared = tuple(sorted(set(left) & set(right)))
    if not shared:
        raise RobustnessAblationError(f"robustness comparison has no shared numeric {key}")
    rows = [
        {
            "metric": metric,
            "reference": left[metric],
            "variant": right[metric],
            "delta": right[metric] - left[metric],
        }
        for metric in shared
    ]
    return {"metricCount": len(rows), "rows": rows, "rowsSha256": _sha256_json(rows)}


def rank_correlation(reference: Sequence[Any], variant: Sequence[Any], *, k: int) -> float:
    """Spearman correlation with absent members assigned deterministic k+1."""

    if k <= 1 or k > MAX_K:
        raise RobustnessAblationError("rank correlation k is invalid")
    left_ids = _ranking_ids(reference, k)
    right_ids = _ranking_ids(variant, k)
    universe = sorted(set(left_ids) | set(right_ids))
    if len(universe) < 2:
        return 1.0
    absent = k + 1
    left_rank = {value: ordinal for ordinal, value in enumerate(left_ids, start=1)}
    right_rank = {value: ordinal for ordinal, value in enumerate(right_ids, start=1)}
    left = [float(left_rank.get(value, absent)) for value in universe]
    right = [float(right_rank.get(value, absent)) for value in universe]
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right))
    denominator = math.sqrt(
        sum((a - left_mean) ** 2 for a in left)
        * sum((b - right_mean) ** 2 for b in right)
    )
    return numerator / denominator if denominator else 0.0


def _quantile_r7(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _rankings(result: Mapping[str, Any]) -> Mapping[str, Sequence[Any]]:
    rankings = result.get("rankings")
    if not isinstance(rankings, Mapping) or not rankings:
        raise RobustnessAblationError("ablation input lacks in-memory rankings")
    return rankings


def compare_ranking_results(
    reference_result: Mapping[str, Any],
    variant_result: Mapping[str, Any],
    *,
    ablation_id: str,
    k_values: Sequence[int] = DEFAULT_K_VALUES,
    max_worst_query_rows: int = MAX_WORST_QUERY_ROWS,
) -> dict[str, Any]:
    specs = {spec.ablation_id: spec for spec in DECLARED_ABLATIONS}
    if ablation_id not in specs:
        raise RobustnessAblationError("ablation was not predeclared")
    if tuple(sorted(set(k_values))) != tuple(k_values) or any(
        k <= 1 or k > MAX_K for k in k_values
    ):
        raise RobustnessAblationError("ablation k values are invalid")
    if not 0 <= max_worst_query_rows <= MAX_WORST_QUERY_ROWS:
        raise RobustnessAblationError("worst-query row bound exceeds 50")
    reference = _rankings(reference_result)
    variant = _rankings(variant_result)
    if set(reference) != set(variant):
        raise RobustnessAblationError("reference/variant query cohorts differ")
    query_ids = tuple(sorted(reference))
    public_ids = set(governance_common.load_public_ids())
    if any(query_id not in public_ids for query_id in query_ids):
        raise RobustnessAblationError("robustness query is outside the public cohort")
    for by_query in (reference, variant):
        for ranking in by_query.values():
            if any(_candidate_id(row) not in public_ids for row in ranking):
                raise RobustnessAblationError("robustness candidate is outside the public cohort")
    rows: list[dict[str, Any]] = []
    for query_id in query_ids:
        for k in k_values:
            overlap = top_k_overlap(reference[query_id], variant[query_id], k=k)
            correlation = rank_correlation(reference[query_id], variant[query_id], k=k)
            rows.append(
                {
                    "queryPublicObjectId": query_id,
                    "k": k,
                    "topKOverlap": overlap,
                    "rankCorrelation": correlation,
                }
            )
    aggregates: list[dict[str, Any]] = []
    for k in k_values:
        selected = [row for row in rows if row["k"] == k]
        overlaps = [row["topKOverlap"] for row in selected]
        correlations = [row["rankCorrelation"] for row in selected]
        aggregates.append(
            {
                "k": k,
                "queryCount": len(selected),
                "meanTopKOverlap": statistics.fmean(overlaps),
                "medianTopKOverlap": _quantile_r7(overlaps, 0.50),
                "p05TopKOverlap": _quantile_r7(overlaps, 0.05),
                "meanRankCorrelation": statistics.fmean(correlations),
                "medianRankCorrelation": _quantile_r7(correlations, 0.50),
                "p05RankCorrelation": _quantile_r7(correlations, 0.05),
            }
        )
    maximum_k = max(k_values)
    worst = sorted(
        (row for row in rows if row["k"] == maximum_k),
        key=lambda row: (row["topKOverlap"], row["rankCorrelation"], row["queryPublicObjectId"]),
    )[:max_worst_query_rows]
    spec = specs[ablation_id]
    source_leakage_delta = _diagnostic_delta(
        reference_result, variant_result, "sourceLeakageDiagnostics"
    )
    hubness_delta = _diagnostic_delta(reference_result, variant_result, "hubnessDiagnostics")
    return {
        "schemaVersion": SCHEMA_VERSION,
        "implementationVersion": IMPLEMENTATION_VERSION,
        "ablation": asdict(spec),
        "referenceMethodId": reference_result.get("methodId"),
        "variantMethodId": variant_result.get("methodId"),
        "referenceCorpusSha256": reference_result.get("corpusSha256"),
        "variantCorpusSha256": variant_result.get("corpusSha256"),
        "referenceRankingIdsSha256": reference_result.get("rankingIdsSha256"),
        "variantRankingIdsSha256": variant_result.get("rankingIdsSha256"),
        "queryCount": len(query_ids),
        "kValues": list(k_values),
        "aggregateRows": aggregates,
        "comparisonObservationSha256": _sha256_json(rows),
        "worstQueryRows": worst,
        "worstQueryRowsSha256": _sha256_json(worst),
        "worstQueryRowsTruncated": len(worst) < len(query_ids),
        "sourceLeakageChange": source_leakage_delta,
        "hubnessChange": hubness_delta,
        "fullPerQueryRowsRetained": False,
        "weightsSelected": False,
        "promptOptimized": False,
        "aspectsFused": False,
        "historicalRelationProduced": False,
        "probabilityProduced": False,
    }


def evaluate_ablation_suite(
    reference_result: Mapping[str, Any],
    variant_results: Mapping[str, Mapping[str, Any]],
    *,
    k_values: Sequence[int] = DEFAULT_K_VALUES,
    evaluation_status: str,
) -> dict[str, Any]:
    if evaluation_status not in SUITE_STATUSES:
        raise RobustnessAblationError("robustness suite status is invalid")
    unknown = sorted(set(variant_results) - set(DECLARED_ABLATION_IDS))
    if unknown:
        raise RobustnessAblationError(f"undeclared ablations supplied: {unknown}")
    missing = sorted(set(DECLARED_ABLATION_IDS) - set(variant_results))
    if evaluation_status == "COMPLETED" and missing:
        raise RobustnessAblationError("completed robustness suite omits declared ablations")
    if evaluation_status == "NOT_RUN" and variant_results:
        raise RobustnessAblationError("NOT_RUN robustness suite cannot contain executed variants")
    raw_aspect_ids = reference_result.get("aspectIds")
    aspect_id = reference_result.get("aspectId")
    if aspect_id is None and isinstance(raw_aspect_ids, Sequence) and not isinstance(
        raw_aspect_ids, (str, bytes, bytearray)
    ) and len(raw_aspect_ids) == 1:
        aspect_id = raw_aspect_ids[0]
    identity = {
        "methodId": str(reference_result.get("methodId", "")).strip(),
        "corpusSha256": str(reference_result.get("corpusSha256", "")),
        "inputVariant": str(reference_result.get("inputVariant", "")).strip(),
        "aspectId": str(aspect_id or "").strip(),
        "indexSha256": str(reference_result.get("indexSha256", "")),
        "rankingIdsSha256": str(reference_result.get("rankingIdsSha256", "")),
    }
    if (
        not identity["methodId"]
        or not identity["inputVariant"]
        or not identity["aspectId"]
        or any(
            not re.fullmatch(r"[0-9a-f]{64}", identity[key])
            for key in ("corpusSha256", "indexSha256", "rankingIdsSha256")
        )
    ):
        raise RobustnessAblationError("robustness reference identity is incomplete")
    rows = [
        compare_ranking_results(
            reference_result,
            variant_results[ablation_id],
            ablation_id=ablation_id,
            k_values=k_values,
        )
        for ablation_id in sorted(variant_results)
    ]
    material = {
        "schemaVersion": "trace-nlp-robustness-ablation-suite/v1",
        "implementationVersion": IMPLEMENTATION_VERSION,
        "status": evaluation_status,
        **identity,
        "declaredAblationIds": list(DECLARED_ABLATION_IDS),
        "executedAblationIds": sorted(variant_results),
        "notRunAblationIds": missing,
        "comparisons": rows,
        "selectionPerformed": False,
        "fusionSelected": False,
        "sourceLeakageAndRobustnessCannotBeOmittedFromShortlistDecision": True,
    }
    return {**material, "suiteSha256": _sha256_json(material)}


def _test_result(rankings: Mapping[str, Sequence[str]], method: str) -> dict[str, Any]:
    return {
        "methodId": method,
        "corpusSha256": "a" * 64,
        "inputVariant": "PLAIN_DOCUMENT_SYMMETRIC_DIAGNOSTIC",
        "aspectId": "NLP_TITLE",
        "indexSha256": "b" * 64,
        "rankingIdsSha256": _sha256_json(rankings),
        "sourceLeakageDiagnostics": {"sameSourceNeighborRateAt20": 0.25},
        "hubnessDiagnostics": {"giniAt20": 0.1},
        "rankings": {
            query: [
                {"candidatePublicId": candidate, "score": 1.0 / ordinal}
                for ordinal, candidate in enumerate(values, start=1)
            ]
            for query, values in rankings.items()
        },
    }


def run_self_tests() -> dict[str, Any]:
    ids = governance_common.load_public_ids()[:4]
    reference = _test_result(
        {ids[0]: (ids[1], ids[2], ids[3]), ids[1]: (ids[0], ids[2], ids[3])},
        "REF",
    )
    variant = _test_result(
        {ids[0]: (ids[2], ids[1], ids[3]), ids[1]: (ids[0], ids[3], ids[2])},
        "VAR",
    )
    result = compare_ranking_results(
        reference,
        variant,
        ablation_id="MAX_LENGTH_256",
        k_values=(2, 3),
        max_worst_query_rows=1,
    )
    if result["aggregateRows"][1]["meanTopKOverlap"] != 1.0:
        raise AssertionError("ranking overlap changed")
    if result["fullPerQueryRowsRetained"] or result["weightsSelected"]:
        raise AssertionError("ablation boundary weakened")
    if any(spec.governed_text_mutation_allowed for spec in DECLARED_ABLATIONS):
        raise AssertionError("ablation grid permits ungoverned text mutation")
    try:
        evaluate_ablation_suite(
            reference,
            {"MAX_LENGTH_256": variant},
            k_values=(2, 3),
            evaluation_status="COMPLETED",
        )
    except RobustnessAblationError:
        pass
    else:
        raise AssertionError("partial robustness suite masqueraded as completed")
    stopped = evaluate_ablation_suite(
        reference,
        {"MAX_LENGTH_256": variant},
        k_values=(2, 3),
        evaluation_status="STOPPED_RECOVERABLE_CHECKPOINT",
    )
    if stopped["status"] != "STOPPED_RECOVERABLE_CHECKPOINT":
        raise AssertionError("partial robustness suite lost its stopped status")
    return {
        "schemaVersion": "trace-nlp-robustness-ablation-self-test/v1",
        "status": "PASS",
        "declaredAblationCount": len(DECLARED_ABLATIONS),
        "queryCount": result["queryCount"],
        "fullPerQueryRowsRetained": False,
        "weightsSelected": False,
        "networkCalls": 0,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.self_test:
        print(json.dumps(run_self_tests(), sort_keys=True))
        return 0
    raise SystemExit("robustness evaluation requires bounded in-memory rankings")


if __name__ == "__main__":
    raise SystemExit(main())
