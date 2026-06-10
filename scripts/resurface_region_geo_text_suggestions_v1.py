#!/usr/bin/env python3
"""Resurface geography hints from pending and low-signal candidate rows.

This script is intentionally conservative. It generates suggestions from
controlled geography terms and field strength, but does not apply them.
"""

from __future__ import annotations

import re
from collections import Counter

from lib.archive_audit import DATA, ROOT, clean, read_csv, write_csv


INPUT = DATA / "region_geography_normalization_candidates_v1.csv"
OUTPUT = DATA / "region_pending_geo_text_suggestions_v1.csv"

FIELDS = [
    "surface_id",
    "source_record_id",
    "current_region_label",
    "candidate_status",
    "suggested_label",
    "suggested_region_id",
    "suggested_geo_id",
    "confidence",
    "match_field",
    "match_count",
    "match_evidence",
    "title",
]

TARGET_ACTIONS = {"keep_pending", "review_low_signal_geo_candidates"}
HIGH_SIGNAL_FIELDS = {"placeText", "sourceSubjects"}
LOW_SIGNAL_FIELDS = {"title", "sourceDescription", "sourceNotes", "sourceName"}

ALIASES = {
    "usa": "United States",
    "u s a": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "great britain": "United Kingdom",
    "new zealand": "Aotearoa New Zealand",
    "china": "Mainland China",
    "russia": "Russia / USSR contexts",
    "palestine": "Palestinian territories and diaspora",
}

IGNORE_LABELS = {
    "Global / transnational",
    "Western and Central Europe",
    "Latin America and the Caribbean",
    "East Asia",
    "Africa",
    "Oceania and Pacific",
    "Middle East and North Africa",
    "South Asia",
    "Southeast Asia",
}


def norm(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean(value).lower()).strip()


def controlled_terms() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in read_csv(DATA / "geographies.csv"):
        name = clean(row.get("name"))
        if not name or name in IGNORE_LABELS:
            continue
        out[norm(name)] = row
        for alias, target in ALIASES.items():
            if target == name:
                out[norm(alias)] = row
    return out


def evidence_segments(value: str) -> dict[str, str]:
    segments: dict[str, str] = {}
    for segment in clean(value).split(" | "):
        if ":" not in segment:
            continue
        key, text = segment.split(":", 1)
        segments[key.strip()] = text.strip()
    return segments


def field_matches(text: str, controlled: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    normalized = f" {norm(text)} "
    matches = []
    seen: set[str] = set()
    for key, row in controlled.items():
        if f" {key} " in normalized and row["geo_id"] not in seen:
            matches.append(row)
            seen.add(row["geo_id"])
    return matches


def main() -> None:
    controlled = controlled_terms()
    out = []
    for row in read_csv(INPUT):
        if row.get("candidate_action") not in TARGET_ACTIONS:
            continue
        segments = evidence_segments(row.get("evidence_snippet", ""))
        weighted: Counter[str] = Counter()
        evidence_by_geo: dict[str, tuple[str, str, dict[str, str]]] = {}
        for field, text in segments.items():
            matches = field_matches(text, controlled)
            for match in matches:
                geo_id = match["geo_id"]
                weight = 3 if field in HIGH_SIGNAL_FIELDS else 1
                weighted[geo_id] += weight
                existing = evidence_by_geo.get(geo_id)
                if not existing or weight > (3 if existing[0] in HIGH_SIGNAL_FIELDS else 1):
                    evidence_by_geo[geo_id] = (field, text[:300], match)

        if not weighted:
            continue
        [(geo_id, score)] = weighted.most_common(1)
        top_ties = [item for item, item_score in weighted.items() if item_score == score]
        if len(top_ties) > 1:
            continue
        field, evidence, match = evidence_by_geo[geo_id]
        if field in HIGH_SIGNAL_FIELDS and score >= 3:
            confidence = "medium_high"
        elif score >= 2:
            confidence = "medium"
        else:
            confidence = "low"
        out.append(
            {
                "surface_id": row.get("surface_id", ""),
                "source_record_id": row.get("source_record_id", ""),
                "current_region_label": row.get("current_region_label", ""),
                "candidate_status": row.get("candidate_status", ""),
                "suggested_label": clean(match.get("name")),
                "suggested_region_id": clean(match.get("region_id")),
                "suggested_geo_id": clean(match.get("geo_id")),
                "confidence": confidence,
                "match_field": field,
                "match_count": str(score),
                "match_evidence": evidence,
                "title": row.get("title", ""),
            }
        )
    write_csv(OUTPUT, out, FIELDS)
    print(f"pending_text_suggestions={len(out)}")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
