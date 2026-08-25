"""Schema-aware canonical serialization shared conceptually with the TS adapter."""

from __future__ import annotations

import hashlib
import json
from typing import Any


SORTED_STRING_ARRAY_KEYS = {
    "allowedOrigins", "allowedTreeStrategies", "clusterHandoffIds", "contestationRefs",
    "evidenceRefs", "gapRefs", "grammarAttestationIds", "grammarAttestationRefs",
    "lexicalAttestationIds", "observedChainIds", "pairQuestionIds", "qualificationRefs",
    "sourceIds", "unresolvedGapRefs", "vocabularyGapIds",
}
SORTED_OBJECT_ARRAY_KEYS = {
    "candidates": "candidateId",
    "semanticNodeRefs": "senseId",
}
ORDERED_ARRAY_KEYS = {
    "candidateSenseIds", "orderedFlowIds", "orderedNodeConceptIds", "treeItems",
}


def canonicalize(value: Any, key: str | None = None) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        raise ValueError("floating-point values are not semantic canonical inputs")
    if isinstance(value, list):
        items = [canonicalize(item) for item in value]
        if key in ORDERED_ARRAY_KEYS:
            return items
        if key in SORTED_STRING_ARRAY_KEYS:
            if not all(isinstance(item, str) for item in items):
                raise ValueError(f"{key} must contain strings")
            return sorted(items)
        if key in SORTED_OBJECT_ARRAY_KEYS:
            sort_key = SORTED_OBJECT_ARRAY_KEYS[key]
            return sorted(items, key=lambda item: item[sort_key])
        raise ValueError(f"unknown array-ordering rule for {key!r}")
    if isinstance(value, dict):
        return {name: canonicalize(value[name], name) for name in sorted(value)}
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(canonicalize(value), ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def semantic_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def without_hash(value: dict[str, Any], field: str = "canonicalHash") -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != field}
