#!/usr/bin/env python3
"""Non-selective future NLP-channel architecture register."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


POSITIONS = (
    ("NLP-POSITION-A", "EXPLANATION_ONLY_SEMANTIC_CHANNEL"),
    ("NLP-POSITION-B", "ADDITIONAL_CANDIDATE_GENERATION_CHANNEL"),
    ("NLP-POSITION-C", "RERANKER_OVER_CG_CUR_4"),
    ("NLP-POSITION-D", "INDEPENDENT_PARALLEL_AFFINITY_CHANNEL"),
    ("NLP-POSITION-E", "LATE_FUSION_WITH_STRUCTURED_PROFILE"),
)


def evaluate_channel_positions(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Emit five transparent positions without selecting fusion or weights."""

    rows = []
    dense_full = int(evidence.get("denseFullCorpusCount", 0))
    review_ready = bool(evidence.get("reviewPacketReady", False))
    source_blockers = int(evidence.get("sourceLeakageBlockerCount", 0))
    for position_id, role in POSITIONS:
        if position_id == "NLP-POSITION-E":
            state = "DEFER"
            reason = "Fusion weights and a public model are explicitly out of scope."
        elif source_blockers:
            state = "NEEDS_MORE_DATA"
            reason = "Source leakage requires further review before this integration position."
        elif position_id == "NLP-POSITION-D" and dense_full >= 1 and review_ready:
            state = "RESEARCH_SHORTLISTED"
            reason = "Preserves NLP as a separate profile while human review remains pending."
        elif position_id == "NLP-POSITION-A" and review_ready:
            state = "RESEARCH_SHORTLISTED"
            reason = "Bounded explanations are available without affecting retrieval or score."
        else:
            state = "RESEARCH_ONLY"
            reason = "Architecture remains evaluable but is not selected this round."
        rows.append(
            {
                "positionId": position_id,
                "role": role,
                "state": state,
                "reason": reason,
                "changesCgCur4": False,
                "changesM2M5M7": False,
                "fusionSelected": False,
                "weightsSelected": False,
                "publicModelSelected": False,
            }
        )
    digest = hashlib.sha256((json.dumps(rows, sort_keys=True, separators=(",", ":")) + "\n").encode()).hexdigest()
    return {
        "schemaVersion": "trace-nlp-channel-architecture-v1",
        "rows": rows,
        "variantCount": len(rows),
        "shortlist": [row["positionId"] for row in rows if row["state"] == "RESEARCH_SHORTLISTED"],
        "rowsSha256": digest,
        "fusionSelected": False,
        "fusionWeightsSelected": False,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate_channel_positions({"denseFullCorpusCount": 2, "reviewPacketReady": True}), sort_keys=True))
