#!/usr/bin/env python3
"""Parse existing region conflicts into direct geography suggestions.

This is a proposal-only pass. It only reads
data/region_geography_normalization_candidates_v1.csv and controlled
geographies, then writes a review CSV. It never rewrites surfaces.
"""

from __future__ import annotations

import re
from collections import defaultdict

from lib.archive_audit import DATA, ROOT, clean, read_csv, write_csv


INPUT = DATA / "region_geography_normalization_candidates_v1.csv"
OUTPUT = DATA / "region_conflict_direct_parse_v1.csv"

FIELDS = [
    "surface_id",
    "source_record_id",
    "current_region_label",
    "suggested_label",
    "suggested_region_id",
    "suggested_geo_id",
    "parse_confidence",
    "match_basis",
    "match_evidence",
    "title",
]

ALIASES = {
    "usa": "United States",
    "u s a": "United States",
    "u.s.a": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "great britain": "United Kingdom",
    "new zealand": "Aotearoa New Zealand",
    "china": "Mainland China",
    "russia": "Russia / USSR contexts",
    "palestine": "Palestinian territories and diaspora",
}


def norm(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean(value).lower()).strip()


def controlled_geographies() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in read_csv(DATA / "geographies.csv"):
        name = clean(row.get("name"))
        if not name:
            continue
        out[norm(name)] = row
        for alias, target in ALIASES.items():
            if target == name:
                out[norm(alias)] = row
    return out


def evidence_segments(value: str) -> dict[str, str]:
    parts: dict[str, list[str]] = defaultdict(list)
    for segment in clean(value).split(" | "):
        if ":" not in segment:
            continue
        key, text = segment.split(":", 1)
        parts[key.strip()].append(text.strip())
    return {key: " ".join(items) for key, items in parts.items()}


def direct_matches(text: str, controlled: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    normalized = f" {norm(text)} "
    matches: list[dict[str, str]] = []
    seen: set[str] = set()
    for key, row in controlled.items():
        if not key or key in {"global transnational"}:
            continue
        if f" {key} " in normalized and row["geo_id"] not in seen:
            matches.append(row)
            seen.add(row["geo_id"])
    return matches


def main() -> None:
    controlled = controlled_geographies()
    rows = []
    for row in read_csv(INPUT):
        if row.get("candidate_status") != "geography_conflict_review":
            continue
        segments = evidence_segments(row.get("evidence_snippet", ""))
        high_signal = " ".join([segments.get("placeText", ""), segments.get("sourceSubjects", "")])
        matches = direct_matches(high_signal, controlled)

        target_ids = {item.strip() for item in clean(row.get("target_geo_ids")).split(";") if item.strip()}
        if target_ids:
            matches = [match for match in matches if match.get("geo_id") in target_ids] or matches

        unique_geo_ids = {match.get("geo_id") for match in matches}
        if len(unique_geo_ids) != 1:
            continue
        match = matches[0]
        suggested = clean(match.get("name"))
        if suggested == clean(row.get("current_region_label")):
            continue
        rows.append(
            {
                "surface_id": row.get("surface_id", ""),
                "source_record_id": row.get("source_record_id", ""),
                "current_region_label": row.get("current_region_label", ""),
                "suggested_label": suggested,
                "suggested_region_id": clean(match.get("region_id")),
                "suggested_geo_id": clean(match.get("geo_id")),
                "parse_confidence": "high",
                "match_basis": "placeText/sourceSubjects controlled-geography match",
                "match_evidence": high_signal[:300],
                "title": row.get("title", ""),
            }
        )
    write_csv(OUTPUT, rows, FIELDS)
    print(f"conflict_rows_parsed={len(rows)}")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
