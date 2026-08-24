#!/usr/bin/env python3
"""Deterministic metadata-holdout proxy views and metrics.

These proxies measure alignment with governed metadata after literal target
labels are removed.  They are not semantic or historical ground truth.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import replace
from typing import Any, Iterable, Mapping, Sequence

import lexical_common as common


IMPLEMENTATION_VERSION = "trace-nlp-metadata-holdout-2026-08-24"
TARGETS = ("medium", "theme", "object_type")
MASK_VARIANTS = (
    "ORIGINAL_APPROVED",
    "TARGET_LABEL_MASKED",
    "ALL_CONTEXT_LABELS_MASKED",
)


def derive_governed_label_contract() -> dict[str, Any]:
    records = common.load_structured_public_records()
    assignments: dict[str, dict[str, tuple[str, ...]]] = {
        target: {} for target in (*TARGETS, "movement_context")
    }
    aliases: dict[str, set[str]] = {}
    labels: dict[str, str] = {}
    for object_id, record in sorted(records.items()):
        for target in ("medium", "theme", "movement_context"):
            values = record.get(target, ())
            ids = []
            for value in values:
                label_id = str(value["id"])
                label = str(value["label"]).strip()
                ids.append(label_id)
                labels[label_id] = label
                aliases.setdefault(label_id, set()).add(label)
            assignments[target][object_id] = tuple(sorted(ids))
        value = record["object_type"]
        label_id = str(value["id"])
        label = str(value["label"]).strip()
        assignments["object_type"][object_id] = (label_id,)
        labels[label_id] = label
        aliases.setdefault(label_id, set()).add(label)
        # The frozen object-type string is a deterministic semicolon-delimited
        # source label. Its observed components are registered masking literals,
        # not inferred synonyms.
        aliases[label_id].update(part.strip() for part in label.split(";") if part.strip())
    if any(set(values) != set(records) for values in assignments.values()):
        raise common.LexicalContractError("metadata-holdout assignments omit public objects")
    frozen_aliases = {
        label_id: tuple(sorted(values, key=lambda value: (-len(value), value.casefold())))
        for label_id, values in sorted(aliases.items())
    }
    return {
        "schemaVersion": "trace-nlp-metadata-label-contract/v1",
        "assignments": assignments,
        "labels": dict(sorted(labels.items())),
        "aliases": frozen_aliases,
        "contractSha256": common.sha256_json(
            {"assignments": assignments, "labels": labels, "aliases": frozen_aliases}
        ),
    }


def _phrase_pattern(phrase: str) -> re.Pattern[str]:
    escaped = re.escape(" ".join(phrase.split()))
    escaped = escaped.replace(r"\ ", r"\s+")
    prefix = r"(?<!\w)" if phrase and phrase[0].isalnum() else ""
    suffix = r"(?!\w)" if phrase and phrase[-1].isalnum() else ""
    return re.compile(prefix + escaped + suffix, re.IGNORECASE)


def mask_registered_phrases(text: str, phrases: Iterable[str]) -> tuple[str, int]:
    output = text
    count = 0
    ordered = sorted(
        {" ".join(str(value).split()) for value in phrases if str(value).strip()},
        key=lambda value: (-len(value), value.casefold()),
    )
    for phrase in ordered:
        output, replacements = _phrase_pattern(phrase).subn(" ", output)
        count += replacements
    output = " ".join(output.split())
    for phrase in ordered:
        if _phrase_pattern(phrase).search(output):
            raise common.LexicalContractError("registered metadata literal survived masking")
    return output, count


def _mask_phrases_for_object(
    object_id: str,
    *,
    target: str,
    mask_variant: str,
    contract: Mapping[str, Any],
) -> tuple[str, ...]:
    if mask_variant == "ORIGINAL_APPROVED":
        return ()
    assignments = contract["assignments"]
    aliases = contract["aliases"]
    label_ids: set[str] = set()
    if mask_variant == "TARGET_LABEL_MASKED":
        label_ids.update(assignments[target][object_id])
    elif mask_variant == "ALL_CONTEXT_LABELS_MASKED":
        for context_target in ("medium", "theme", "movement_context"):
            label_ids.update(assignments[context_target][object_id])
        label_ids.update(assignments["object_type"][object_id])
    else:
        raise common.LexicalContractError("unsupported metadata masking variant")
    return tuple(
        phrase for label_id in sorted(label_ids) for phrase in aliases.get(label_id, ())
    )


def build_masked_corpus_view(
    corpus: common.CorpusBundle,
    *,
    target: str,
    mask_variant: str,
    aspect_ids: Sequence[str],
    label_contract: Mapping[str, Any] | None = None,
) -> tuple[common.CorpusBundle, dict[str, Any]]:
    if target not in TARGETS or mask_variant not in MASK_VARIANTS:
        raise common.LexicalContractError("metadata target or mask variant is unsupported")
    if not aspect_ids or set(aspect_ids) - common.ALLOWED_ASPECTS:
        raise common.LexicalContractError("metadata mask aspects are absent or ungoverned")
    contract = label_contract or derive_governed_label_contract()
    if mask_variant == "ORIGINAL_APPROVED":
        return corpus, {
            "maskVariant": mask_variant,
            "maskedOccurrenceCount": 0,
            "affectedObjectCount": 0,
            "labelContractSha256": contract["contractSha256"],
        }
    documents = []
    masked_count = 0
    affected = 0
    for document in corpus.documents:
        phrases = _mask_phrases_for_object(
            document.object_id,
            target=target,
            mask_variant=mask_variant,
            contract=contract,
        )
        aspects = dict(document.aspects)
        object_masked = 0
        for aspect_id in aspect_ids:
            aspect = aspects.get(aspect_id)
            if aspect is None:
                continue
            semantic, semantic_count = mask_registered_phrases(
                aspect.semantic_normalized, phrases
            )
            lexical, lexical_count = mask_registered_phrases(
                aspect.lexical_casefolded, phrases
            )
            object_masked += max(semantic_count, lexical_count)
            aspects[aspect_id] = replace(
                aspect,
                semantic_normalized=semantic,
                lexical_casefolded=lexical,
                semantic_normalized_hash=common.sha256_bytes(semantic.encode("utf-8")),
                lexical_casefolded_hash=common.sha256_bytes(lexical.encode("utf-8")),
                character_count=len(semantic),
                structured_labels_masked=True,
            )
        masked_count += object_masked
        affected += bool(object_masked)
        documents.append(replace(document, aspects=aspects))
    material = {
        "baseCorpusSha256": corpus.corpus_sha256,
        "target": target,
        "maskVariant": mask_variant,
        "aspectIds": list(aspect_ids),
        "labelContractSha256": contract["contractSha256"],
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
        documents_by_id={value.object_id: value for value in documents},
        corpus_sha256=common.sha256_json(material),
    )
    return derived, {
        "maskVariant": mask_variant,
        "maskedOccurrenceCount": masked_count,
        "affectedObjectCount": affected,
        "labelContractSha256": contract["contractSha256"],
        "derivedCorpusSha256": derived.corpus_sha256,
    }


def _dcg(relevances: Sequence[int]) -> float:
    return sum(value / math.log2(index + 2.0) for index, value in enumerate(relevances))


def evaluate_metadata_proxy(
    model_results: Mapping[str, Mapping[str, Any]],
    *,
    target: str,
    label_contract: Mapping[str, Any] | None = None,
    cutoffs: tuple[int, ...] = (1, 5, 10, 20),
) -> dict[str, Any]:
    if target not in TARGETS:
        raise common.LexicalContractError("unsupported metadata proxy target")
    contract = label_contract or derive_governed_label_contract()
    assignments = contract["assignments"][target]
    support = Counter(label_id for values in assignments.values() for label_id in values)
    evaluable_queries = {
        object_id
        for object_id, labels in assignments.items()
        if any(support[label_id] > 1 for label_id in labels)
    }
    if not evaluable_queries:
        raise common.LexicalContractError("metadata proxy has no evaluable target pairs")
    rows = []
    for model_id, result in sorted(model_results.items()):
        rankings = result.get("rankings")
        if not isinstance(rankings, Mapping):
            raise common.LexicalContractError("metadata proxy requires in-memory rankings")
        per_cutoff_precision = {cutoff: [] for cutoff in cutoffs}
        per_cutoff_ndcg = {cutoff: [] for cutoff in cutoffs}
        evaluated = 0
        for query_id in sorted(evaluable_queries & set(rankings)):
            query_labels = set(assignments[query_id])
            ranking = rankings[query_id]
            evaluated += 1
            for cutoff in cutoffs:
                relevances = [
                    int(bool(query_labels & set(assignments[row["candidatePublicId"]])))
                    for row in ranking[:cutoff]
                ]
                per_cutoff_precision[cutoff].append(sum(relevances) / cutoff)
                total_relevant = sum(
                    bool(query_labels & set(candidate_labels))
                    for candidate_id, candidate_labels in assignments.items()
                    if candidate_id != query_id
                )
                ideal = [1] * min(cutoff, total_relevant) + [0] * max(0, cutoff - total_relevant)
                denominator = _dcg(ideal)
                per_cutoff_ndcg[cutoff].append(_dcg(relevances) / denominator if denominator else 0.0)
        rows.append(
            {
                "modelId": model_id,
                "target": target,
                "evaluatedQueryCount": evaluated,
                **{
                    f"precisionAt{cutoff}": sum(per_cutoff_precision[cutoff])
                    / len(per_cutoff_precision[cutoff])
                    for cutoff in cutoffs
                },
                **{
                    f"ndcgAt{cutoff}": sum(per_cutoff_ndcg[cutoff])
                    / len(per_cutoff_ndcg[cutoff])
                    for cutoff in cutoffs
                },
                "historicalRelation": False,
                "semanticRelation": False,
                "probability": False,
            }
        )
    majority_support = max(support.values())
    return {
        "schemaVersion": "trace-nlp-metadata-holdout-results/v1",
        "implementationVersion": IMPLEMENTATION_VERSION,
        "target": target,
        "proxyOnly": True,
        "labelCount": len(support),
        "evaluableQueryCount": len(evaluable_queries),
        "majorityLabelObjectShare": majority_support / len(assignments),
        "targetDistribution": dict(sorted(support.items())),
        "labelContractSha256": contract["contractSha256"],
        "modelRows": rows,
        "rowsSha256": common.sha256_json(rows),
    }


def self_test() -> dict[str, Any]:
    masked, count = mask_registered_phrases(
        "Poster — a POSTER; posterity remains", ("poster",)
    )
    if masked != "— a ; posterity remains" or count != 2:
        raise common.LexicalContractError("metadata exact-boundary masking self-test failed")
    if _dcg([1, 0, 1]) <= _dcg([0, 1, 1]):
        raise common.LexicalContractError("metadata NDCG self-test failed")
    miniature_contract = {
        "assignments": {
            "medium": {"SURF-A": ("M",)},
            "theme": {"SURF-A": ("T",)},
            "movement_context": {"SURF-A": ("C",)},
            "object_type": {"SURF-A": ("O",)},
        },
        "aliases": {"M": ("medium",), "T": ("theme",), "C": ("context",), "O": ("type",)},
    }
    all_labels = _mask_phrases_for_object(
        "SURF-A",
        target="medium",
        mask_variant="ALL_CONTEXT_LABELS_MASKED",
        contract=miniature_contract,
    )
    if set(all_labels) != {"medium", "theme", "context", "type"}:
        raise common.LexicalContractError("all-context mask omitted a governed label family")
    return {
        "schemaVersion": "trace-nlp-metadata-holdout-self-test/v1",
        "maskVariants": list(MASK_VARIANTS),
        "targetCount": len(TARGETS),
        "sharedMaskTokenInserted": False,
        "proxyIsGroundTruth": False,
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
