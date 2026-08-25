"""Schema-aware canonicalization for Round 13 v2 interchange artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any


SORTED_STRING_ARRAY_KEYS = {
    "allowedOrigins",
    "allowedTreeStrategies",
    "clusterHandoffIds",
    "convergenceSourceItemIds",
    "contestationRefs",
    "evidenceRefs",
    "gapRefs",
    "grammarAttestationIds",
    "grammarAttestationRefs",
    "lexicalAttestationIds",
    "observedChainIds",
    "pairQuestionIds",
    "qualificationRefs",
    "requiredFields",
    "sourceIds",
    "unresolvedGapRefs",
    "vocabularyGapIds",
}
ORDERED_ARRAY_KEYS = {"candidateSenseIds", "orderedFlowIds", "orderedNodeConceptIds", "treeItems"}
SORTED_OBJECT_ARRAY_KEYS = {"candidates": "candidateId", "semanticNodeRefs": "senseId"}
SORTED_OBJECT_ARRAY_KEYS.update({
    "nodeActivationCandidates": "candidateId",
    "pairCompositionCandidates": "candidateId",
    "inquiryGrammarCandidates": "candidateId",
    "structuralAnnotationCandidates": "candidateId",
})


def canonicalize(value: Any, key: str | None = None) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        raise ValueError("FLOAT_PROHIBITED")
    if isinstance(value, list):
        items = [canonicalize(item) for item in value]
        if key in ORDERED_ARRAY_KEYS:
            return items
        if key in SORTED_STRING_ARRAY_KEYS:
            if not all(isinstance(item, str) for item in items):
                raise ValueError(f"{key}:STRING_ARRAY_REQUIRED")
            return sorted(items)
        if key in SORTED_OBJECT_ARRAY_KEYS:
            return sorted(items, key=lambda item: item[SORTED_OBJECT_ARRAY_KEYS[key]])
        raise ValueError(f"UNKNOWN_ARRAY_ORDER:{key}")
    if isinstance(value, dict):
        return {name: canonicalize(value[name], name) for name in sorted(value)}
    raise TypeError(f"UNSUPPORTED_CANONICAL_TYPE:{type(value).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(canonicalize(value), ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def semantic_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
