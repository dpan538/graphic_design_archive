#!/usr/bin/env python3
"""Fail-closed language-leakage diagnostics for the governed Round 7 corpus.

Language labels are optional analysis metadata, never affinity features or
semantic truth.  The frozen corpus currently has no selected local LID model
and no mechanically verified cross-language positive set, so the production
path returns an explicit NOT_RUN receipt instead of inferring labels from
script or model neighbourhoods.  Script-only neighbourhood diagnostics remain
available as a separate, clearly named channel.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Any, Mapping, Sequence

import common as governance_common


IMPLEMENTATION_VERSION = "trace-nlp-language-leakage-2026-08-24"
UNRELIABLE_LABELS = frozenset({"", "UNDETERMINED", "MIXED", "NOT_SELECTED"})
PUBLIC_ID_PATTERN = re.compile(r"^SURF-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
MAX_TOP_K = 50


class LanguageLeakageError(RuntimeError):
    """Raised when a language diagnostic crosses the governed boundary."""


def _sha(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _candidate_id(row: Mapping[str, Any]) -> str:
    value = str(row.get("candidatePublicId", ""))
    if not value:
        raise LanguageLeakageError("ranking row lacks a public candidate ID")
    return value


def _macro_f1(expected: Sequence[str], predicted: Sequence[str]) -> float:
    labels = tuple(sorted(set(expected) | set(predicted)))
    if not expected or not labels or len(expected) != len(predicted):
        raise LanguageLeakageError("language probe labels/predictions are invalid")
    scores: list[float] = []
    for label in labels:
        true_positive = sum(a == label and b == label for a, b in zip(expected, predicted))
        false_positive = sum(a != label and b == label for a, b in zip(expected, predicted))
        false_negative = sum(a == label and b != label for a, b in zip(expected, predicted))
        precision = (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive
            else 0.0
        )
        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else 0.0
        )
        scores.append(
            2.0 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
    return sum(scores) / len(scores)


def _validated_rankings(
    model_results: Mapping[str, Mapping[str, Any]],
    *,
    maximum_cutoff: int,
) -> tuple[dict[str, dict[str, tuple[Mapping[str, Any], ...]]], set[str]]:
    validated: dict[str, dict[str, tuple[Mapping[str, Any], ...]]] = {}
    observed_ids: set[str] = set()
    if not model_results:
        raise LanguageLeakageError("language leakage requires at least one model")
    authoritative_ids = set(governance_common.load_public_ids())
    for model_id, result in sorted(model_results.items()):
        rankings = result.get("rankings")
        if not isinstance(rankings, Mapping) or not rankings:
            raise LanguageLeakageError("language leakage requires bounded rankings")
        by_query: dict[str, tuple[Mapping[str, Any], ...]] = {}
        for raw_query_id, raw_ranking in sorted(rankings.items()):
            query_id = str(raw_query_id)
            if (
                not PUBLIC_ID_PATTERN.fullmatch(query_id)
                or query_id not in authoritative_ids
            ):
                raise LanguageLeakageError("ranking query is not a public object ID")
            if not isinstance(raw_ranking, Sequence) or isinstance(
                raw_ranking, (str, bytes, bytearray)
            ):
                raise LanguageLeakageError("language ranking is not a sequence")
            ranking = tuple(raw_ranking)
            if len(ranking) < maximum_cutoff or len(ranking) > MAX_TOP_K:
                raise LanguageLeakageError(
                    "ranking length is outside the bounded declared cutoff"
                )
            candidate_ids: list[str] = []
            normalized_rows: list[Mapping[str, Any]] = []
            for raw_row in ranking:
                if not isinstance(raw_row, Mapping):
                    raise LanguageLeakageError("language ranking row is not a mapping")
                candidate_id = _candidate_id(raw_row)
                if (
                    not PUBLIC_ID_PATTERN.fullmatch(candidate_id)
                    or candidate_id not in authoritative_ids
                ):
                    raise LanguageLeakageError("ranking candidate is not a public object ID")
                candidate_ids.append(candidate_id)
                normalized_rows.append(raw_row)
            if query_id in candidate_ids or len(candidate_ids) != len(set(candidate_ids)):
                raise LanguageLeakageError("language ranking contains self or duplicates")
            observed_ids.add(query_id)
            observed_ids.update(candidate_ids)
            by_query[query_id] = tuple(normalized_rows)
        validated[str(model_id)] = by_query
    return validated, observed_ids


def evaluate_language_leakage(
    model_results: Mapping[str, Mapping[str, Any]],
    *,
    language_by_object: Mapping[str, str] | None,
    script_by_object: Mapping[str, str],
    cutoffs: Sequence[int] = (10, 20, 50),
    language_id_model: str = "NOT_SELECTED",
) -> dict[str, Any]:
    """Evaluate language only when reliable labels are explicitly supplied.

    Script rates are always reported separately and are not substituted for a
    language label.  With the frozen Round 7 inputs, ``language_by_object`` is
    absent and the language-probe result is an honest N/A receipt.
    """

    normalized_lid_model = str(language_id_model).strip()
    lid_selected = bool(normalized_lid_model and normalized_lid_model != "NOT_SELECTED")
    if not lid_selected and language_by_object:
        raise LanguageLeakageError("language labels supplied without a selected LID model")
    if tuple(sorted(set(map(int, cutoffs)))) != tuple(cutoffs) or any(
        int(value) <= 0 or int(value) > 50 for value in cutoffs
    ):
        raise LanguageLeakageError("language-leakage cutoffs are invalid")

    normalized_cutoffs = tuple(map(int, cutoffs))
    validated, observed_ids = _validated_rankings(
        model_results, maximum_cutoff=max(normalized_cutoffs)
    )
    missing_scripts = sorted(observed_ids - set(script_by_object))
    if missing_scripts or any(not str(script_by_object[value]).strip() for value in observed_ids):
        raise LanguageLeakageError("script registry is incomplete for the ranking cohort")

    script_rows: list[dict[str, Any]] = []
    for model_id, rankings in validated.items():
        row: dict[str, Any] = {"modelId": model_id, "queryCount": len(rankings)}
        for cutoff in normalized_cutoffs:
            values: list[float] = []
            for query_id, ranking in rankings.items():
                script = str(script_by_object[query_id])
                selected = tuple(ranking[: int(cutoff)])
                values.append(
                    sum(
                        str(script_by_object[_candidate_id(candidate)]) == script
                        for candidate in selected
                    )
                    / int(cutoff)
                )
            row[f"sameScriptNeighborRateAt{cutoff}"] = sum(values) / len(values)
        row.update(
            {
                "languageIdentityUsedAsSemanticTruth": False,
                "historicalRelation": False,
                "semanticRelation": False,
                "probability": False,
            }
        )
        script_rows.append(row)

    supplied_labels = {
        str(object_id): str(label).strip()
        for object_id, label in (language_by_object or {}).items()
    }
    authoritative_ids = set(governance_common.load_public_ids())
    if any(
        not PUBLIC_ID_PATTERN.fullmatch(object_id) or object_id not in authoritative_ids
        for object_id in supplied_labels
    ):
        raise LanguageLeakageError("language-label registry contains a non-public object ID")
    reliable_labels = {
        object_id: label
        for object_id, label in supplied_labels.items()
        if label.upper() not in UNRELIABLE_LABELS
    }
    missing_language_ids = sorted(observed_ids - set(reliable_labels))
    language_rows: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []
    language_hubness_rows: list[dict[str, Any]] = []
    if not reliable_labels:
        status = "NOT_RUN"
        reason = "NO_SELECTED_LID_MODEL_OR_RELIABLE_LANGUAGE_LABEL_COHORT"
        blocker_count = int(lid_selected)
    elif missing_language_ids:
        status = "NOT_RUN"
        reason = "INCOMPLETE_RELIABLE_LANGUAGE_LABEL_COHORT"
        blocker_count = 1
    else:
        status = "PASS"
        reason = None
        blocker_count = 0
        all_labels = tuple(sorted(set(reliable_labels[value] for value in observed_ids)))
        if len(all_labels) < 2:
            status = "NOT_RUN"
            reason = "RELIABLE_LANGUAGE_LABEL_COHORT_HAS_FEWER_THAN_TWO_CLASSES"
            blocker_count = 1
        else:
            for model_id, rankings in validated.items():
                row: dict[str, Any] = {
                    "modelId": model_id,
                    "queryCount": len(rankings),
                }
                for cutoff in normalized_cutoffs:
                    same_rates: list[float] = []
                    neighbor_counts: Counter[str] = Counter()
                    per_query_hhi: list[float] = []
                    for query_id, ranking in rankings.items():
                        selected_labels = [
                            reliable_labels[_candidate_id(candidate)]
                            for candidate in ranking[:cutoff]
                        ]
                        counts = Counter(selected_labels)
                        same_rates.append(counts[reliable_labels[query_id]] / cutoff)
                        per_query_hhi.append(
                            sum((count / cutoff) ** 2 for count in counts.values())
                        )
                        neighbor_counts.update(selected_labels)
                    total_neighbors = sum(neighbor_counts.values())
                    same_rate = sum(same_rates) / len(same_rates)
                    row[f"sameLanguageNeighborRateAt{cutoff}"] = same_rate
                    row[f"crossLanguageNeighborRateAt{cutoff}"] = 1.0 - same_rate
                    row[f"meanQueryLanguageHhiAt{cutoff}"] = sum(per_query_hhi) / len(
                        per_query_hhi
                    )
                    row[f"aggregateNeighborLanguageHhiAt{cutoff}"] = sum(
                        (count / total_neighbors) ** 2
                        for count in neighbor_counts.values()
                    )
                    language_hubness_rows.append(
                        {
                            "modelId": model_id,
                            "k": cutoff,
                            "queryCount": len(rankings),
                            "totalNeighborCount": total_neighbors,
                            "distinctNeighborLanguageCount": len(neighbor_counts),
                            "aggregateNeighborLanguageHhi": row[
                                f"aggregateNeighborLanguageHhiAt{cutoff}"
                            ],
                            "maximumNeighborLanguageShare": max(neighbor_counts.values())
                            / total_neighbors,
                            "languageDistributionSha256": _sha(
                                dict(sorted(neighbor_counts.items()))
                            ),
                        }
                    )
                row.update(
                    {
                        "languageIdentityUsedAsSemanticTruth": False,
                        "historicalRelation": False,
                        "semanticRelation": False,
                        "probability": False,
                    }
                )
                language_rows.append(row)

                probe_k = min(20, min(len(ranking) for ranking in rankings.values()))
                expected: list[str] = []
                predicted: list[str] = []
                prediction_rows: list[list[str]] = []
                for query_id, ranking in sorted(rankings.items()):
                    counts = Counter(
                        reliable_labels[_candidate_id(candidate)]
                        for candidate in ranking[:probe_k]
                    )
                    prediction = sorted(
                        counts, key=lambda label: (-counts[label], label)
                    )[0]
                    expected.append(reliable_labels[query_id])
                    predicted.append(prediction)
                    prediction_rows.append([query_id, prediction])
                expected_counts = Counter(expected)
                majority = sorted(
                    expected_counts,
                    key=lambda label: (-expected_counts[label], label),
                )[0]
                majority_predictions = [majority] * len(expected)
                probe_rows.append(
                    {
                        "modelId": model_id,
                        "probeMethod": "DETERMINISTIC_TOP_K_NEIGHBOR_LANGUAGE_VOTE",
                        "analysisOnly": True,
                        "probeK": probe_k,
                        "queryCount": len(expected),
                        "classCount": len(set(expected)),
                        "accuracy": sum(a == b for a, b in zip(expected, predicted))
                        / len(expected),
                        "macroF1": _macro_f1(expected, predicted),
                        "majorityBaselineAccuracy": sum(
                            a == b for a, b in zip(expected, majority_predictions)
                        )
                        / len(expected),
                        "majorityBaselineMacroF1": _macro_f1(
                            expected, majority_predictions
                        ),
                        "predictionsSha256": _sha(prediction_rows),
                        "languageIdentityUsedAsSemanticTruth": False,
                    }
                )
    material = {
        "schemaVersion": "trace-nlp-language-leakage/v1",
        "implementationVersion": IMPLEMENTATION_VERSION,
        "status": status,
        "reason": reason,
        "languageIdModel": normalized_lid_model or "NOT_SELECTED",
        "languageIdModelCommitted": False,
        "reliableLanguageLabelObjectCount": len(reliable_labels),
        "distinctReliableLanguageLabelCount": len(set(reliable_labels.values())),
        "rankingCohortObjectCount": len(observed_ids),
        "missingReliableLanguageLabelObjectCount": len(missing_language_ids),
        "missingReliableLanguageLabelIdsSha256": _sha(missing_language_ids),
        "scriptDiagnosticRows": script_rows,
        "languageDiagnosticRows": language_rows,
        "languageProbeRows": probe_rows,
        "languageHubnessRows": language_hubness_rows,
        "languageLeakageBlockerCount": blocker_count,
        "scriptIsLanguage": False,
        "languageIdentityUsedAsPositiveAffinity": False,
        "generatedTranslationCount": 0,
    }
    return {**material, "receiptSha256": _sha(material)}


def self_test() -> dict[str, Any]:
    object_a, object_b, object_c = governance_common.load_public_ids()[:3]
    rankings = {
        "FIXTURE": {
            "rankings": {
                object_a: [
                    {"candidatePublicId": object_b},
                    {"candidatePublicId": object_c},
                ],
                object_b: [
                    {"candidatePublicId": object_a},
                    {"candidatePublicId": object_c},
                ],
            },
        }
    }
    result = evaluate_language_leakage(
        rankings,
        language_by_object=None,
        script_by_object={object_a: "LATIN", object_b: "LATIN", object_c: "HAN"},
        cutoffs=(2,),
    )
    if result["status"] != "NOT_RUN" or result["distinctReliableLanguageLabelCount"] != 0:
        raise LanguageLeakageError("missing-language fail-closed fixture changed")
    try:
        evaluate_language_leakage(
            rankings,
            language_by_object={object_a: "en"},
            script_by_object={object_a: "LATIN", object_b: "LATIN", object_c: "HAN"},
            cutoffs=(2,),
        )
    except LanguageLeakageError:
        rejected = True
    else:
        rejected = False
    if not rejected:
        raise LanguageLeakageError("unselected LID labels were accepted")
    invalid_id_rankings = {
        "FIXTURE": {
            "rankings": {
                "SURF-NOTINLEDGER": [
                    {"candidatePublicId": object_b},
                    {"candidatePublicId": object_c},
                ]
            }
        }
    }
    try:
        evaluate_language_leakage(
            invalid_id_rankings,
            language_by_object=None,
            script_by_object={object_b: "LATIN", object_c: "HAN"},
            cutoffs=(2,),
        )
    except LanguageLeakageError:
        invalid_id_rejected = True
    else:
        invalid_id_rejected = False
    if not invalid_id_rejected:
        raise LanguageLeakageError("non-public ranking identity was accepted")
    selected = evaluate_language_leakage(
        rankings,
        language_by_object={object_a: "en", object_b: "fr", object_c: "en"},
        script_by_object={object_a: "LATIN", object_b: "LATIN", object_c: "HAN"},
        cutoffs=(2,),
        language_id_model="PINNED-LOCAL-LID-FIXTURE",
    )
    if (
        selected["status"] != "PASS"
        or not selected["languageDiagnosticRows"]
        or not selected["languageProbeRows"]
        or not selected["languageHubnessRows"]
        or selected["languageDiagnosticRows"][0]["sameLanguageNeighborRateAt2"]
        != 0.25
        or selected["languageHubnessRows"][0]["totalNeighborCount"] != 4
        or any(
            not 0.0 <= selected["languageDiagnosticRows"][0][key] <= 1.0
            for key in (
                "sameLanguageNeighborRateAt2",
                "crossLanguageNeighborRateAt2",
                "meanQueryLanguageHhiAt2",
                "aggregateNeighborLanguageHhiAt2",
            )
        )
    ):
        raise LanguageLeakageError("selected reliable language diagnostics were omitted")
    incomplete = evaluate_language_leakage(
        rankings,
        language_by_object={object_a: "en", object_b: "fr"},
        script_by_object={object_a: "LATIN", object_b: "LATIN", object_c: "HAN"},
        cutoffs=(2,),
        language_id_model="PINNED-LOCAL-LID-FIXTURE",
    )
    if (
        incomplete["status"] != "NOT_RUN"
        or incomplete["reason"] != "INCOMPLETE_RELIABLE_LANGUAGE_LABEL_COHORT"
        or incomplete["languageProbeRows"]
        or incomplete["languageLeakageBlockerCount"] != 1
    ):
        raise LanguageLeakageError("incomplete language cohort produced a false PASS")
    return {
        "schemaVersion": "trace-nlp-language-leakage-self-test/v1",
        "status": "PASS",
        "checks": 5,
        "unselectedLidLabelsRejected": True,
        "nonPublicRankingIdentityRejected": True,
        "selectedReliableLabelsComputed": True,
        "incompleteReliableLabelsNotRun": True,
        "scriptIsLanguage": False,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
