#!/usr/bin/env python3
"""Deterministic, bounded, public-safe NLP review packet preparation."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from typing import Any, Mapping, Sequence

from common import (
    PRIVATE_TOKEN_PATTERN,
    PUBLIC_ID_PATTERN,
    URL_PATTERN,
    UUID_PATTERN,
    load_public_ids,
)


class ReviewPacketError(RuntimeError):
    """Raised when review evidence would cross a public or semantic boundary."""


def _sha(value: Any) -> str:
    return hashlib.sha256(
        (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    ).hexdigest()


def _safe_title(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewPacketError("review title is empty")
    title = " ".join(value.split())
    if UUID_PATTERN.search(title) or PRIVATE_TOKEN_PATTERN.search(title) or URL_PATTERN.search(title):
        raise ReviewPacketError("review title contains a private identifier or URL")
    return title


def select_review_anchors(
    profiles: Mapping[str, Mapping[str, Any]], *, target_count: int = 24
) -> tuple[str, ...]:
    """Select a stable round-robin sample across declared diagnostic strata."""

    if target_count < 24 or target_count > 36:
        raise ReviewPacketError("review packet must contain 24 to 36 anchors")
    buckets: dict[str, list[str]] = defaultdict(list)
    public_ids = set(load_public_ids())
    for object_id, profile in profiles.items():
        if not PUBLIC_ID_PATTERN.fullmatch(object_id) or object_id not in public_ids:
            raise ReviewPacketError("review profile is outside the authoritative public cohort")
        aspect_availability = str(profile.get("aspectAvailability", "")).strip()
        if not aspect_availability:
            raise ReviewPacketError("review profile lacks text-aspect availability stratum")
        strata = (
            str(profile.get("scriptState", "UNDETERMINED")),
            aspect_availability,
            str(profile.get("sourceId", "UNDETERMINED")),
            str(profile.get("timeBand", "UNDETERMINED")),
            str(profile.get("geographyBand", "UNDETERMINED")),
            str(profile.get("contextRarityBand", "UNDETERMINED")),
            str(profile.get("sourceLeakageRisk", "UNDETERMINED")),
            str(profile.get("hubnessBand", "UNDETERMINED")),
            str(profile.get("structuredNlpDisagreement", "UNDETERMINED")),
        )
        bucket_id = "\x1f".join(strata)
        buckets[bucket_id].append(object_id)
    for bucket_id, identifiers in buckets.items():
        identifiers.sort(key=lambda value: (hashlib.sha256((bucket_id + "\0" + value).encode()).hexdigest(), value))
    selected: list[str] = []
    offsets = {bucket_id: 0 for bucket_id in buckets}
    while len(selected) < target_count:
        progressed = False
        for bucket_id in sorted(buckets):
            offset = offsets[bucket_id]
            if offset < len(buckets[bucket_id]):
                candidate = buckets[bucket_id][offset]
                offsets[bucket_id] += 1
                if candidate not in selected:
                    selected.append(candidate)
                    progressed = True
                    if len(selected) == target_count:
                        break
        if not progressed:
            break
    if len(selected) != target_count:
        raise ReviewPacketError("not enough public profiles for the requested packet")
    return tuple(selected)


def build_review_packet(
    profiles: Mapping[str, Mapping[str, Any]],
    rankings: Mapping[str, Mapping[str, Sequence[Mapping[str, Any]]]],
    *,
    method_roles: Mapping[str, str],
    target_count: int = 24,
    candidates_per_method: int = 5,
) -> dict[str, Any]:
    """Build a blinded packet; no expert answer is synthesized in this round."""

    if candidates_per_method < 1 or candidates_per_method > 10:
        raise ReviewPacketError("bounded candidates_per_method is 1..10")
    anchors = select_review_anchors(profiles, target_count=target_count)
    method_ids = tuple(sorted(rankings))
    if set(method_ids) != set(method_roles):
        raise ReviewPacketError("method-role registry does not match ranking inputs")
    role_counts = Counter(str(value) for value in method_roles.values())
    allowed_roles = {
        "LEXICAL",
        "DENSE",
        "HYBRID_DIAGNOSTIC",
        "STRUCTURED_M2_INDEPENDENT",
        "STRUCTURED_M5_INDEPENDENT",
        "STRUCTURED_M7_INDEPENDENT",
    }
    if (
        set(role_counts) - allowed_roles
        or role_counts["LEXICAL"] != 1
        or not 1 <= role_counts["DENSE"] <= 3
        or role_counts["HYBRID_DIAGNOSTIC"] != 1
        or role_counts["STRUCTURED_M2_INDEPENDENT"] != 1
        or role_counts["STRUCTURED_M5_INDEPENDENT"] != 1
        or role_counts["STRUCTURED_M7_INDEPENDENT"] != 1
    ):
        raise ReviewPacketError("review packet lacks a required lexical/dense/hybrid/structured profile")
    public_ids = set(load_public_ids())
    blind_codes = {method_id: f"MODEL-{chr(65 + index)}" for index, method_id in enumerate(method_ids)}
    rows: list[dict[str, Any]] = []
    for anchor_id in anchors:
        anchor = profiles[anchor_id]
        anchor_title = _safe_title(anchor.get("title"))
        for method_id in method_ids:
            candidates = rankings[method_id].get(anchor_id)
            if not candidates:
                raise ReviewPacketError("review anchor lacks a required method ranking")
            for expected_rank, candidate in enumerate(candidates[:candidates_per_method], start=1):
                candidate_id = candidate.get("candidateId")
                if (
                    not isinstance(candidate_id, str)
                    or not PUBLIC_ID_PATTERN.fullmatch(candidate_id)
                    or candidate_id not in public_ids
                    or candidate_id == anchor_id
                ):
                    raise ReviewPacketError("review candidate identity is invalid")
                candidate_profile = profiles.get(candidate_id)
                if candidate_profile is None:
                    raise ReviewPacketError("review candidate is outside the public profile set")
                rank = int(candidate.get("rank", expected_rank))
                if rank != expected_rank:
                    raise ReviewPacketError("review ranking is not contiguous")
                score = candidate.get("score")
                if score is not None and not isinstance(score, (int, float)):
                    raise ReviewPacketError("review score is not numeric")
                rows.append(
                    {
                        "packetId": "NLP-REVIEW-ROUND1",
                        "anchorPublicObjectId": anchor_id,
                        "anchorTitle": anchor_title,
                        "candidatePublicObjectId": candidate_id,
                        "candidateTitle": _safe_title(candidate_profile.get("title")),
                        "blindModelCode": blind_codes[method_id],
                        "methodRole": method_roles[method_id],
                        "rank": rank,
                        "scoreObservation": score,
                        "textAspect": candidate.get("aspectId"),
                        "retrievalReason": candidate.get("retrievalReason", "BOUNDED_TOP_K"),
                        "sameSource": anchor.get("sourceId") == candidate_profile.get("sourceId"),
                        "sameScriptState": anchor.get("scriptState") == candidate_profile.get("scriptState"),
                        "contextMatch": candidate.get("contextMatch"),
                        "temporalMatch": candidate.get("temporalMatch"),
                        "geographyMatch": candidate.get("geographyMatch"),
                        "descriptiveMatch": candidate.get("descriptiveMatch"),
                        "expertJudgment": "PENDING_LATER_REVIEW",
                        "historicalRelation": False,
                        "semanticRelation": False,
                        "probability": False,
                    }
                )
    return {
        "schemaVersion": "trace-nlp-review-packet-v1",
        "anchorIds": list(anchors),
        "anchorCount": len(anchors),
        "methodCount": len(method_ids),
        "methodRoleCounts": dict(sorted(role_counts.items())),
        "requiredMethodFamiliesPresent": True,
        "rows": rows,
        "rowCount": len(rows),
        "rowsSha256": _sha(rows),
        "packetReady": True,
        "domainExpertReviewCompleted": False,
    }


def self_test() -> dict[str, Any]:
    ids = load_public_ids()[:30]
    profiles = {
        object_id: {
            "title": f"Public title {i}",
            "sourceId": f"S{i % 3}",
            "scriptState": "LATIN",
            "aspectAvailability": "T",
        }
        for i, object_id in enumerate(ids, start=1)
    }
    methods = {
        "L": "LEXICAL",
        "D": "DENSE",
        "H": "HYBRID_DIAGNOSTIC",
        "M2": "STRUCTURED_M2_INDEPENDENT",
        "M5": "STRUCTURED_M5_INDEPENDENT",
        "M7": "STRUCTURED_M7_INDEPENDENT",
    }
    rankings = {
        method_id: {
            object_id: [
                {"candidateId": candidate_id, "rank": rank, "score": 1.0 / rank, "aspectId": "NLP_TITLE"}
                for rank, candidate_id in enumerate((value for value in profiles if value != object_id), start=1)
            ]
            for object_id in profiles
        }
        for method_id in methods
    }
    result = build_review_packet(profiles, rankings, method_roles=methods, target_count=24, candidates_per_method=2)
    if result["anchorCount"] != 24 or result["rowCount"] != 288:
        raise ReviewPacketError("review packet fixture failed")
    try:
        build_review_packet(
            profiles,
            {key: value for key, value in rankings.items() if key != "M7"},
            method_roles={key: value for key, value in methods.items() if key != "M7"},
            target_count=24,
            candidates_per_method=2,
        )
    except ReviewPacketError:
        pass
    else:
        raise ReviewPacketError("review packet without M7 was marked ready")
    return {"status": "PASS", "checks": 2, "receiptSha256": _sha(result)}


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True))
