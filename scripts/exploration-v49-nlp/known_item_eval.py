#!/usr/bin/env python3
"""Task A importer-representation consistency and duplicate-title stress tests.

The source-governance ``evaluation_registry`` module is the sole pair-registry
authority.  This module validates and consumes its rows/hash; it does not mint
a second positive/control registry.  The complete exact-title pair census is
kept as a separate aggregate stress test and never serialized as pair rows.
"""

from __future__ import annotations

import importlib
import itertools
import json
import sqlite3
from collections import Counter, defaultdict
from typing import Any, Iterator, Mapping, Sequence

import lexical_common as common


IMPLEMENTATION_VERSION = "trace-nlp-known-item-eval-2026-08-24"
SQLITE_PATH = common.ROOT / "data/prefreeze_candidate_v48.sqlite"
EXPECTED_EVALUATION_REGISTRY_SHA256 = (
    "73c0650cfc10a2db6d5fb61c72a783b086667d2da7e6229f1cdd00475700a785"
)
EXPECTED_SQLITE_SHA256 = "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e"
EXPECTED_LEDGER_SHA256 = "48f98f68ca2ec0cef96c82ecc9c01e4129eb9a3f91e08b07ad9a59644a9d4e01"
POSITIVE_CLASS = "KNOWN_REPRESENTATION_POSITIVE"
POSITIVE_QUALIFIER = "SAME_SOURCE_ITEM_DUPLICATE_IMPORT_IDENTITY"
POSITIVE_TASK = "NLP_TASK_A_KNOWN_REPRESENTATION_RETRIEVAL"
NEGATIVE_CLASS = "DIAGNOSTIC_NEGATIVE_CONTROL"
EXPECTED_POSITIVE_PAIRS = frozenset(
    {
        frozenset({"SURF-AICTRACEV47R0002", "SURF-HISTORICALAICTRACE2026V1R0021"}),
        frozenset({"SURF-CGS2026R0383", "SURF-LOCTRACE2026ICC0337ACE0D517"}),
        frozenset({"SURF-CGS2026R0740", "SURF-LOCTRACE2026R02046"}),
    }
)


def _authoritative_registry_module() -> Any:
    try:
        module = importlib.import_module("evaluation_registry")
    except ImportError as error:
        raise common.LexicalContractError(
            "authoritative evaluation_registry API is unavailable"
        ) from error
    for name in ("build_evaluation_registry", "evaluation_registry_sha256", "evaluation_summary"):
        if not callable(getattr(module, name, None)):
            raise common.LexicalContractError(f"evaluation_registry.{name} is unavailable")
    return module


def _source_public_ids() -> tuple[str, ...]:
    """Consume the source-governance boundary API without loading text."""

    _authoritative_registry_module()
    try:
        source_common = importlib.import_module("common")
    except ImportError as error:
        raise common.LexicalContractError("source-governance common API is unavailable") from error
    loader = getattr(source_common, "load_public_ids", None)
    if not callable(loader):
        raise common.LexicalContractError("source-governance public-ID API is unavailable")
    identifiers = tuple(loader())
    if (
        len(identifiers) != common.PUBLIC_OBJECT_COUNT
        or identifiers != tuple(sorted(identifiers))
        or len(set(identifiers)) != len(identifiers)
    ):
        raise common.LexicalContractError("source-governance public-ID cohort changed")
    return identifiers


def load_authoritative_evaluation_registry() -> dict[str, Any]:
    """Return a validated view of the central registry without altering rows."""

    module = _authoritative_registry_module()
    rows = tuple(dict(row) for row in module.build_evaluation_registry())
    summary = dict(module.evaluation_summary())
    registry_sha256 = str(module.evaluation_registry_sha256())
    if (
        registry_sha256 != EXPECTED_EVALUATION_REGISTRY_SHA256
        or summary.get("registrySha256") != registry_sha256
    ):
        raise common.LexicalContractError("authoritative evaluation-registry pin changed")
    if (
        len(rows) != 312
        or summary.get("pairCount") != 312
        or summary.get("knownRepresentationPositivePairCount") != 3
        or summary.get("negativeControlPairCount") != 309
        or summary.get("taskBPositivePairCount") != 0
        or summary.get("verifiedCrossLanguagePositivePairCount") != 0
    ):
        raise common.LexicalContractError("authoritative evaluation-registry census changed")
    required = {
        "pair_id",
        "public_object_id_a",
        "public_object_id_b",
        "task",
        "pair_class",
        "control_type",
        "verification_artifact_path",
        "verification_artifact_sha256",
        "eligibility_artifact_path",
        "eligibility_artifact_sha256",
        "verification_locator_sha256",
        "field_aspects_available",
        "representation_qualifier",
        "archive_native_variant_evidence",
        "prohibited_interpretation",
    }
    if any(not required <= set(row) for row in rows):
        raise common.LexicalContractError("authoritative evaluation row schema changed")
    positives = [row for row in rows if row["pair_class"] == POSITIVE_CLASS]
    observed_pairs = frozenset(
        frozenset((row["public_object_id_a"], row["public_object_id_b"]))
        for row in positives
    )
    if observed_pairs != EXPECTED_POSITIVE_PAIRS:
        raise common.LexicalContractError("Task A positive endpoints changed")
    for row in positives:
        if (
            row["task"] != POSITIVE_TASK
            or row["control_type"] != POSITIVE_QUALIFIER
            or row["representation_qualifier"] != POSITIVE_QUALIFIER
            or row["archive_native_variant_evidence"] is not False
            or row["verification_artifact_path"] != "data/prefreeze_candidate_v48.sqlite"
            or row["verification_artifact_sha256"] != EXPECTED_SQLITE_SHA256
            or row["eligibility_artifact_sha256"] != EXPECTED_LEDGER_SHA256
        ):
            raise common.LexicalContractError("Task A duplicate-import identity semantics changed")
    if any(
        row["pair_class"] not in {POSITIVE_CLASS, NEGATIVE_CLASS}
        for row in rows
    ):
        raise common.LexicalContractError("unknown central evaluation pair class")
    return {
        "schemaVersion": "trace-nlp-authoritative-evaluation-registry-view/v1",
        "implementationVersion": IMPLEMENTATION_VERSION,
        "registryVersion": summary["registryVersion"],
        "registrySha256": registry_sha256,
        "pairCount": len(rows),
        "knownRepresentationPositivePairCount": len(positives),
        "verifiedCrossLanguagePositivePairCount": 0,
        "negativeControlPairCount": len(rows) - len(positives),
        "taskBEvaluationState": "N_A_NO_VERIFIED_ARCHIVE_TITLE_LANGUAGE_VARIANT_PAIRS",
        "rows": rows,
    }


def _load_public_title_rows() -> dict[str, dict[str, str | None]]:
    public_ids = set(_source_public_ids())
    connection = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro&immutable=1", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    try:
        rows = {
            str(row["surface_id"]): {
                "title": str(row["title"]).strip(),
                "sourceName": str(row["source_name"]).strip(),
                "sourceTitle": (
                    str(row["source_title"]).strip() if row["source_title"] is not None else None
                ),
            }
            for row in connection.execute(
                "SELECT o.surface_id,o.title,o.source_name,"
                "(SELECT m.value FROM object_metadata_rows m "
                " WHERE m.surface_id=o.surface_id AND m.table_kind='SOURCE' "
                " AND m.label='Source title' ORDER BY m.row_order LIMIT 1) AS source_title "
                "FROM objects o ORDER BY o.surface_id"
            )
            if row["surface_id"] in public_ids
        }
    finally:
        connection.close()
    if len(rows) != common.PUBLIC_OBJECT_COUNT or set(rows) != public_ids:
        raise common.LexicalContractError("known-item title rows differ from the public cohort")
    return rows


def _iter_exact_title_stress_pairs(
    rows: Mapping[str, Mapping[str, str | None]],
) -> Iterator[tuple[str, str]]:
    identity_pairs = EXPECTED_POSITIVE_PAIRS
    groups: dict[str, list[str]] = defaultdict(list)
    for object_id, row in rows.items():
        groups[str(row["title"])].append(object_id)
    for title in sorted(groups):
        members = sorted(groups[title])
        if len(members) < 2:
            continue
        for pair in itertools.combinations(members, 2):
            if frozenset(pair) not in identity_pairs:
                yield pair


def build_full_same_title_stress_census() -> dict[str, Any]:
    """Census all duplicate titles, but expose hashes/counts rather than rows."""

    rows = _load_public_title_rows()
    groups: dict[str, list[str]] = defaultdict(list)
    for object_id, row in rows.items():
        groups[str(row["title"])].append(object_id)
    duplicate_groups = [sorted(values) for values in groups.values() if len(values) > 1]
    all_pairs = [
        pair
        for members in duplicate_groups
        for pair in itertools.combinations(members, 2)
    ]
    stress_pairs = list(_iter_exact_title_stress_pairs(rows))
    excluded_identity_pairs = [pair for pair in all_pairs if frozenset(pair) in EXPECTED_POSITIVE_PAIRS]
    if (
        len(duplicate_groups) != 155
        or sum(map(len, duplicate_groups)) != 520
        or len(all_pairs) != 4_346
        or len(excluded_identity_pairs) != 2
        or len(stress_pairs) != 4_344
    ):
        raise common.LexicalContractError("full exact-title stress census changed")
    return {
        "schemaVersion": "trace-nlp-full-same-title-stress-census/v1",
        "duplicateTitleGroupCount": 155,
        "duplicateTitleObjectCount": 520,
        "allUnorderedPairCount": 4_346,
        "excludedKnownIdentityPairCount": 2,
        "stressPairCount": 4_344,
        "pairEndpointsSha256": common.sha256_json(stress_pairs),
        "pairRowsSerialized": False,
        "historicalNonrelation": False,
    }


def build_source_title_difference_census() -> dict[str, Any]:
    """Audit the 23 frozen object-title/source-title normalization differences."""

    rows = _load_public_title_rows()
    observations = []
    for object_id, row in sorted(rows.items()):
        source_title = row["sourceTitle"]
        if source_title is None or source_title == row["title"]:
            continue
        source_name = str(row["sourceName"])
        if source_name == "V&A Collections API":
            category = "V_AND_A_MARKUP_OR_ADJACENT_PUNCTUATION_NORMALIZATION"
        else:
            category = "LOC_FILE_SUFFIX_OR_FILENAME_TITLE_REWRITE"
        observations.append(
            [
                object_id,
                category,
                common.sha256_bytes(str(row["title"]).encode("utf-8")),
                common.sha256_bytes(source_title.encode("utf-8")),
            ]
        )
    counts = Counter(row[1] for row in observations)
    if (
        len(observations) != 23
        or counts["V_AND_A_MARKUP_OR_ADJACENT_PUNCTUATION_NORMALIZATION"] != 16
        or counts["LOC_FILE_SUFFIX_OR_FILENAME_TITLE_REWRITE"] != 7
    ):
        raise common.LexicalContractError("source-title normalization-difference census changed")
    return {
        "schemaVersion": "trace-nlp-source-title-difference-census/v1",
        "sourceTitleObservedObjectCount": sum(row["sourceTitle"] is not None for row in rows.values()),
        "sourceTitleUnavailableObjectCount": sum(row["sourceTitle"] is None for row in rows.values()),
        "differenceCount": len(observations),
        "differenceTypeCounts": dict(sorted(counts.items())),
        "observationHashesSha256": common.sha256_json(observations),
        "archiveNativeLanguageVariantCount": 0,
        "taskBPositivePairCount": 0,
        "rawTitlesSerialized": False,
    }


def build_evaluation_pair_registry() -> dict[str, Any]:
    """Compatibility adapter returning only the authoritative central rows/hash."""

    registry = load_authoritative_evaluation_registry()
    output = dict(registry)
    output["fullSameTitleStressCensus"] = build_full_same_title_stress_census()
    output["sourceTitleDifferenceCensus"] = build_source_title_difference_census()
    return output


def _rank_lookup(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {str(row["candidatePublicId"]): int(row["rank"]) for row in rows}


def _direction_has_aspect(row: Mapping[str, Any], side: int, aspect_ids: Sequence[str]) -> bool:
    parts = str(row["field_aspects_available"]).split("|")
    if len(parts) != 2:
        raise common.LexicalContractError("central field-aspect availability encoding changed")
    available = set(filter(None, parts[side].split(",")))
    return any(aspect_id in available for aspect_id in aspect_ids)


def _bounded_pair_metrics(
    rankings: Mapping[str, Sequence[Mapping[str, Any]]],
    pairs: Sequence[tuple[str, str]],
    *,
    cutoffs: Sequence[int],
) -> dict[str, Any]:
    ranks: list[int | None] = []
    for left_id, right_id in pairs:
        for query_id, target_id in ((left_id, right_id), (right_id, left_id)):
            if query_id not in rankings:
                continue
            ranks.append(_rank_lookup(rankings[query_id]).get(target_id))
    return {
        "evaluatedDirectionCount": len(ranks),
        **{
            f"hitRateAt{cutoff}": (
                sum(rank is not None and rank <= cutoff for rank in ranks) / len(ranks)
                if ranks
                else None
            )
            for cutoff in cutoffs
        },
    }


def evaluate_known_items(
    model_results: Mapping[str, Mapping[str, Any]],
    pair_registry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    registry = dict(pair_registry or load_authoritative_evaluation_registry())
    if registry.get("registrySha256") != EXPECTED_EVALUATION_REGISTRY_SHA256:
        raise common.LexicalContractError("known-item evaluation received a non-authoritative registry")
    rows = tuple(registry.get("rows", ()))
    positives = [row for row in rows if row["pair_class"] == POSITIVE_CLASS]
    controls = [row for row in rows if row["pair_class"] == NEGATIVE_CLASS]
    if len(positives) != 3 or len(controls) != 309:
        raise common.LexicalContractError("known-item central pair census changed")
    title_rows = _load_public_title_rows()
    full_stress_pairs = tuple(_iter_exact_title_stress_pairs(title_rows))
    model_rows = []
    for model_id, result in sorted(model_results.items()):
        rankings = result.get("rankings")
        if not isinstance(rankings, Mapping):
            raise common.LexicalContractError("known-item evaluation requires in-memory bounded rankings")
        aspect_ids = tuple(map(str, result.get("aspectIds", ())))
        top_k = result.get("topK")
        if not aspect_ids or not isinstance(top_k, int) or top_k < 20:
            raise common.LexicalContractError("known-item result lacks aspect/top-k semantics")
        cutoffs = (1, 5, 10, 20)
        positive_ranks: list[int | None] = []
        skipped_directions = 0
        for pair in positives:
            endpoints = (pair["public_object_id_a"], pair["public_object_id_b"])
            for side, (query_id, target_id) in enumerate((endpoints, endpoints[::-1])):
                if not (
                    _direction_has_aspect(pair, side, aspect_ids)
                    and _direction_has_aspect(pair, 1 - side, aspect_ids)
                ):
                    skipped_directions += 1
                    continue
                if query_id not in rankings:
                    raise common.LexicalContractError(
                        "available Task A query is absent from the model result"
                    )
                positive_ranks.append(_rank_lookup(rankings[query_id]).get(target_id))
        control_metrics: dict[str, dict[str, Any]] = {}
        controls_by_type: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for pair in controls:
            controls_by_type[str(pair["control_type"])].append(
                (str(pair["public_object_id_a"]), str(pair["public_object_id_b"]))
            )
        for control_type, pairs in sorted(controls_by_type.items()):
            control_metrics[control_type] = _bounded_pair_metrics(
                rankings, pairs, cutoffs=cutoffs
            )
        stress = _bounded_pair_metrics(rankings, full_stress_pairs, cutoffs=cutoffs)
        model_rows.append(
            {
                "modelId": model_id,
                "aspectIds": list(aspect_ids),
                "topK": top_k,
                "taskAMetricMeaning": "IMPORTER_REPRESENTATION_CONSISTENCY_ONLY",
                "directedKnownRepresentationQueryCount": len(positive_ranks),
                "skippedUnavailableAspectDirectionCount": skipped_directions,
                **{
                    f"knownRepresentationRecallAt{cutoff}": (
                        sum(rank is not None and rank <= cutoff for rank in positive_ranks)
                        / len(positive_ranks)
                        if positive_ranks
                        else None
                    )
                    for cutoff in cutoffs
                },
                f"knownRepresentationBoundedMrrAt{top_k}": (
                    sum(0.0 if rank is None else 1.0 / rank for rank in positive_ranks)
                    / len(positive_ranks)
                    if positive_ranks
                    else None
                ),
                "authoritativeControlMetricsByType": control_metrics,
                "fullSameTitleStressMetrics": stress,
                "historicalRelation": False,
                "semanticRelation": False,
                "probability": False,
            }
        )
    census = build_full_same_title_stress_census()
    return {
        "schemaVersion": "trace-nlp-known-item-results/v1",
        "implementationVersion": IMPLEMENTATION_VERSION,
        "evaluationRegistrySha256": EXPECTED_EVALUATION_REGISTRY_SHA256,
        "knownRepresentationPairCount": 3,
        "knownRepresentationQualifier": POSITIVE_QUALIFIER,
        "taskAMetricMeaning": "IMPORTER_REPRESENTATION_CONSISTENCY_ONLY",
        "verifiedCrossLanguagePairCount": 0,
        "taskBEvaluationState": "N_A_NO_VERIFIED_ARCHIVE_TITLE_LANGUAGE_VARIANT_PAIRS",
        "authoritativeNegativeControlPairCount": 309,
        "fullSameTitleStressCensus": census,
        "modelRows": model_rows,
        "rowsSha256": common.sha256_json(model_rows),
    }


def self_test() -> dict[str, Any]:
    registry = load_authoritative_evaluation_registry()
    title_census = build_full_same_title_stress_census()
    source_title_census = build_source_title_difference_census()
    return {
        "schemaVersion": "trace-nlp-known-item-self-test/v1",
        "evaluationRegistrySha256": registry["registrySha256"],
        "knownRepresentationPositiveCount": registry["knownRepresentationPositivePairCount"],
        "knownRepresentationQualifier": POSITIVE_QUALIFIER,
        "negativeControlCount": registry["negativeControlPairCount"],
        "duplicateTitleGroupCount": title_census["duplicateTitleGroupCount"],
        "fullSameTitleStressPairCount": title_census["stressPairCount"],
        "sourceTitleDifferenceCount": source_title_census["differenceCount"],
        "verifiedCrossLanguagePositiveCount": 0,
        "taskBEvaluationState": "N_A_NO_VERIFIED_ARCHIVE_TITLE_LANGUAGE_VARIANT_PAIRS",
        "verificationUsesModelOutput": False,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
