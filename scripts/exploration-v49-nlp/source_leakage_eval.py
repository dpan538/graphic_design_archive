#!/usr/bin/env python3
"""Source-neighborhood leakage, masking, controls, and linear probes."""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import replace
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import lsqr

import lexical_common as common
import known_item_eval
import metadata_holdout_eval


IMPLEMENTATION_VERSION = "trace-nlp-source-leakage-2026-08-24"


def source_labels() -> dict[str, str]:
    records = common.load_structured_public_records()
    labels = {
        object_id: str(record["source"]["label"])
        for object_id, record in sorted(records.items())
    }
    if len(labels) != common.PUBLIC_OBJECT_COUNT or not all(labels.values()):
        raise common.LexicalContractError("source label diagnostic cohort changed")
    return labels


def evaluate_source_neighborhoods(
    model_results: Mapping[str, Mapping[str, Any]],
    *,
    source_by_id: Mapping[str, str] | None = None,
    cutoffs: tuple[int, ...] = (10, 20, 50),
) -> dict[str, Any]:
    sources = dict(source_by_id or source_labels())
    corpus_counts = Counter(sources.values())
    corpus_hhi = sum((count / len(sources)) ** 2 for count in corpus_counts.values())
    rows = []
    for model_id, result in sorted(model_results.items()):
        rankings = result.get("rankings")
        if not isinstance(rankings, Mapping):
            raise common.LexicalContractError("source leakage requires in-memory bounded rankings")
        row: dict[str, Any] = {
            "modelId": model_id,
            "queryCount": len(rankings),
            "corpusSourceCount": len(corpus_counts),
            "corpusSourceHhi": corpus_hhi,
        }
        for cutoff in cutoffs:
            same_rates = []
            per_query_hhi = []
            global_neighbors: Counter[str] = Counter()
            for query_id, ranking in rankings.items():
                if query_id not in sources:
                    raise common.LexicalContractError("source leakage query is outside source registry")
                selected = list(ranking[:cutoff])
                if len(selected) < cutoff:
                    raise common.LexicalContractError("source leakage ranking is shorter than cutoff")
                neighbor_sources = [sources[row_["candidatePublicId"]] for row_ in selected]
                counts = Counter(neighbor_sources)
                same_rates.append(counts[sources[query_id]] / cutoff)
                per_query_hhi.append(sum((count / cutoff) ** 2 for count in counts.values()))
                global_neighbors.update(neighbor_sources)
            denominator = sum(global_neighbors.values())
            row[f"sameSourceNeighborRateAt{cutoff}"] = sum(same_rates) / len(same_rates)
            row[f"crossSourceNeighborRateAt{cutoff}"] = 1.0 - row[f"sameSourceNeighborRateAt{cutoff}"]
            row[f"meanQuerySourceHhiAt{cutoff}"] = sum(per_query_hhi) / len(per_query_hhi)
            row[f"aggregateNeighborSourceHhiAt{cutoff}"] = sum(
                (count / denominator) ** 2 for count in global_neighbors.values()
            )
        row.update(
            {
                "historicalRelation": False,
                "semanticRelation": False,
                "probability": False,
            }
        )
        rows.append(row)
    return {
        "schemaVersion": "trace-nlp-source-neighborhood-leakage/v1",
        "implementationVersion": IMPLEMENTATION_VERSION,
        "sourceCount": len(corpus_counts),
        "corpusSourceDistribution": dict(sorted(corpus_counts.items())),
        "modelRows": rows,
        "rowsSha256": common.sha256_json(rows),
    }


def build_source_masked_corpus_view(
    corpus: common.CorpusBundle,
    *,
    aspect_ids: Sequence[str],
    source_by_id: Mapping[str, str] | None = None,
    aliases_by_source: Mapping[str, Iterable[str]] | None = None,
) -> tuple[common.CorpusBundle, dict[str, Any]]:
    if not aspect_ids or set(aspect_ids) - common.ALLOWED_ASPECTS:
        raise common.LexicalContractError("source mask aspects are absent or ungoverned")
    sources = dict(source_by_id or source_labels())
    aliases = {
        source: tuple(sorted({source, *map(str, values)}, key=lambda value: (-len(value), value.casefold())))
        for source, values in (aliases_by_source or {}).items()
    }
    for source in set(sources.values()):
        aliases.setdefault(source, (source,))
    documents = []
    affected = 0
    removed = 0
    for document in corpus.documents:
        if document.object_id not in sources:
            raise common.LexicalContractError("source mask is missing a public object")
        aspects = dict(document.aspects)
        object_removed = 0
        for aspect_id in aspect_ids:
            aspect = aspects.get(aspect_id)
            if aspect is None:
                continue
            phrases = aliases[sources[document.object_id]]
            semantic, semantic_count = metadata_holdout_eval.mask_registered_phrases(
                aspect.semantic_normalized, phrases
            )
            lexical, lexical_count = metadata_holdout_eval.mask_registered_phrases(
                aspect.lexical_casefolded, phrases
            )
            object_removed += max(semantic_count, lexical_count)
            aspects[aspect_id] = replace(
                aspect,
                semantic_normalized=semantic,
                lexical_casefolded=lexical,
                semantic_normalized_hash=common.sha256_bytes(semantic.encode("utf-8")),
                lexical_casefolded_hash=common.sha256_bytes(lexical.encode("utf-8")),
                character_count=len(semantic),
                source_identity_masked=True,
            )
        affected += bool(object_removed)
        removed += object_removed
        documents.append(replace(document, aspects=aspects))
    alias_hash = common.sha256_json(aliases)
    material = {
        "baseCorpusSha256": corpus.corpus_sha256,
        "transformation": "SOURCE_IDENTITY_MASKED",
        "aspectIds": list(aspect_ids),
        "sourceAliasRegistrySha256": alias_hash,
        "documentAspectHashes": [
            [
                document.object_id,
                [
                    [aspect_id, document.aspects[aspect_id].lexical_casefolded_hash]
                    for aspect_id in sorted(aspect_ids)
                    if aspect_id in document.aspects
                ],
            ]
            for document in documents
        ],
    }
    derived = replace(
        corpus,
        documents=tuple(documents),
        documents_by_id={document.object_id: document for document in documents},
        corpus_sha256=common.sha256_json(material),
    )
    return derived, {
        "inputVariant": "SOURCE_IDENTITY_MASKED",
        "sourceAliasRegistrySha256": alias_hash,
        "affectedObjectCount": affected,
        "removedOccurrenceCount": removed,
        "derivedCorpusSha256": derived.corpus_sha256,
        "hiddenBlacklistUsed": False,
    }


def _macro_f1(expected: Sequence[int], predicted: Sequence[int], class_count: int) -> float:
    scores = []
    for class_id in range(class_count):
        true_positive = sum(a == class_id and b == class_id for a, b in zip(expected, predicted))
        false_positive = sum(a != class_id and b == class_id for a, b in zip(expected, predicted))
        false_negative = sum(a == class_id and b != class_id for a, b in zip(expected, predicted))
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return sum(scores) / len(scores)


def deterministic_linear_probe(
    features: sparse.spmatrix,
    object_ids: Sequence[str],
    labels_by_id: Mapping[str, str],
    *,
    requested_folds: int = 5,
    ridge: float = 1.0,
    iteration_limit: int = 100,
) -> dict[str, Any]:
    """Analysis-only stratified one-vs-rest ridge least-squares linear probe."""

    if tuple(object_ids) != tuple(sorted(object_ids)) or features.shape[0] != len(object_ids):
        raise common.LexicalContractError("linear probe feature/public-ID alignment is invalid")
    if set(labels_by_id) != set(object_ids):
        raise common.LexicalContractError("linear probe labels differ from feature cohort")
    labels = tuple(sorted(set(labels_by_id.values())))
    label_to_id = {value: index for index, value in enumerate(labels)}
    y = np.asarray([label_to_id[labels_by_id[value]] for value in object_ids], dtype=np.int32)
    support = Counter(y.tolist())
    fold_count = min(requested_folds, min(support.values()))
    if fold_count < 2:
        raise common.LexicalContractError("linear probe needs at least two examples per source")
    fold_by_ordinal = np.empty(len(object_ids), dtype=np.int32)
    for class_id in range(len(labels)):
        ordinals = np.flatnonzero(y == class_id)
        for position, ordinal in enumerate(ordinals):
            fold_by_ordinal[ordinal] = position % fold_count
    matrix = sparse.csr_matrix(features, dtype=np.float64)
    predictions = np.empty(len(object_ids), dtype=np.int32)
    for fold in range(fold_count):
        test = fold_by_ordinal == fold
        train = ~test
        train_matrix = sparse.hstack(
            [matrix[train], np.ones((int(train.sum()), 1), dtype=np.float64)],
            format="csr",
        )
        test_matrix = sparse.hstack(
            [matrix[test], np.ones((int(test.sum()), 1), dtype=np.float64)],
            format="csr",
        )
        scores = np.empty((int(test.sum()), len(labels)), dtype=np.float64)
        for class_id in range(len(labels)):
            target = np.where(y[train] == class_id, 1.0, -1.0)
            coefficients = lsqr(
                train_matrix,
                target,
                damp=math.sqrt(ridge),
                atol=1e-6,
                btol=1e-6,
                iter_lim=iteration_limit,
                show=False,
            )[0]
            scores[:, class_id] = test_matrix @ coefficients
        predictions[test] = np.argmax(scores, axis=1)
    majority_class = max(support, key=lambda class_id: (support[class_id], -class_id))
    majority_predictions = np.full(len(y), majority_class, dtype=np.int32)
    return {
        "schemaVersion": "trace-nlp-linear-source-probe/v1",
        "probeMethod": "ONE_VS_REST_RIDGE_LEAST_SQUARES",
        "foldCount": fold_count,
        "stratified": True,
        "seed": None,
        "classCount": len(labels),
        "macroF1": _macro_f1(y.tolist(), predictions.tolist(), len(labels)),
        "accuracy": float(np.mean(predictions == y)),
        "majorityBaselineMacroF1": _macro_f1(
            y.tolist(), majority_predictions.tolist(), len(labels)
        ),
        "majorityBaselineAccuracy": float(np.mean(majority_predictions == y)),
        "ridge": ridge,
        "iterationLimit": iteration_limit,
        "predictionsSha256": common.sha256_json(
            [[object_id, labels[int(prediction)]] for object_id, prediction in zip(object_ids, predictions)]
        ),
        "highPerformanceMeansLeakageDiagnostic": True,
    }


def sparse_field_probe_matrix(index: common.SparseFieldIndex) -> sparse.csr_matrix:
    weights = dict(index.spec.field_weights)
    blocks = [
        index.matrices[aspect_id] * math.sqrt(weights[aspect_id])
        for aspect_id in index.spec.aspect_ids
    ]
    return sparse.hstack(blocks, format="csr")


def build_bounded_negative_controls(
    corpus: common.CorpusBundle,
    *,
    maximum_per_type: int = 64,
) -> dict[str, Any]:
    """Return the central model-independent diagnostic controls unchanged."""

    if maximum_per_type != 64:
        raise common.LexicalContractError(
            "negative-control cap is frozen centrally at 64 for generated control families"
        )
    if corpus.public_object_count != common.PUBLIC_OBJECT_COUNT:
        raise common.LexicalContractError("negative-control corpus boundary changed")
    registry = known_item_eval.load_authoritative_evaluation_registry()
    rows = [
        dict(row)
        for row in registry["rows"]
        if row["pair_class"] == known_item_eval.NEGATIVE_CLASS
    ]
    if len(rows) != 309:
        raise common.LexicalContractError("central negative-control count changed")
    return {
        "schemaVersion": "trace-nlp-authoritative-leakage-control-view/v1",
        "evaluationRegistrySha256": registry["registrySha256"],
        "maximumPerGeneratedControlType": maximum_per_type,
        "controlTypeCounts": dict(Counter(row["control_type"] for row in rows)),
        "negativeControlPairCount": len(rows),
        "rowsSha256": common.sha256_json(rows),
        "rows": rows,
    }


def self_test() -> dict[str, Any]:
    expected = [0, 0, 1, 1]
    predicted = [0, 1, 1, 1]
    score = _macro_f1(expected, predicted, 2)
    if not math.isclose(score, (2 / 3 + 0.8) / 2):
        raise common.LexicalContractError("macro-F1 self-test failed")
    return {
        "schemaVersion": "trace-nlp-source-leakage-self-test/v1",
        "neighborhoodCutoffs": [10, 20, 50],
        "sourceProbe": "ONE_VS_REST_RIDGE_LEAST_SQUARES",
        "stratifiedProbe": True,
        "maskUsesHiddenBlacklist": False,
        "negativeControlsAreHistoricalNonrelations": False,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
