#!/usr/bin/env python3
"""Suggest historical split labels for geography conflict rows."""

from __future__ import annotations

import re

from lib.archive_audit import DATA, ROOT, clean, read_csv, write_csv


INPUT = DATA / "region_geography_normalization_candidates_v1.csv"
OUTPUT = DATA / "region_conflict_historical_split_suggestions_v1.csv"

FIELDS = [
    "surface_id",
    "source_record_id",
    "current_region_label",
    "suggested_split_label",
    "period_basis",
    "match_evidence",
    "title",
]

HISTORICAL_RULES = [
    {
        "start": 1846,
        "end": 1848,
        "terms": ["matamoros", "tamaulipas", "mexican american war"],
        "label": "Mexico; United States military occupation context",
    },
    {
        "start": 1949,
        "end": 1990,
        "terms": ["germany", "berlin", "gdr", "ddr", "west germany", "east germany"],
        "label": "Germany; East/West Germany review",
    },
    {
        "start": 1939,
        "end": 1945,
        "terms": ["france", "vichy", "free france", "occupation"],
        "label": "France; wartime occupation/state-context review",
    },
    {
        "start": 1917,
        "end": 1991,
        "terms": ["soviet", "ussr", "russia", "minsk", "ukraine", "belarus"],
        "label": "Russia / USSR contexts; republic-specific review",
    },
    {
        "start": 1910,
        "end": 1920,
        "terms": ["mexico", "revolution", "tamaulipas", "matamoros"],
        "label": "Mexico; Revolutionary-period review",
    },
]


def years(text: str) -> list[int]:
    return [int(item) for item in re.findall(r"\b(1[7-9]\d{2}|20[0-2]\d)\b", text)]


def main() -> None:
    out = []
    for row in read_csv(INPUT):
        if row.get("candidate_status") != "geography_conflict_review":
            continue
        evidence = " ".join(
            [
                clean(row.get("title")),
                clean(row.get("date_text")),
                clean(row.get("evidence_snippet")),
                clean(row.get("target_display_labels")),
            ]
        )
        low = evidence.lower()
        row_years = years(evidence)
        for rule in HISTORICAL_RULES:
            if not any(term in low for term in rule["terms"]):
                continue
            matched_years = [year for year in row_years if rule["start"] <= year <= rule["end"]]
            if not matched_years:
                continue
            out.append(
                {
                    "surface_id": row.get("surface_id", ""),
                    "source_record_id": row.get("source_record_id", ""),
                    "current_region_label": row.get("current_region_label", ""),
                    "suggested_split_label": rule["label"],
                    "period_basis": f"{min(matched_years)} in {rule['start']}-{rule['end']}",
                    "match_evidence": evidence[:300],
                    "title": row.get("title", ""),
                }
            )
            break
    write_csv(OUTPUT, out, FIELDS)
    print(f"historical_split_suggestions={len(out)}")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
