#!/usr/bin/env python3
"""Audit non-mainstream regional capture coverage, health, IMG rate, and impact."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

TARGETS = DATA / "nonmainstream_region_capture_targets_1990_2026_v1.csv"
RECORDS = DATA / "capture_batch_nonmainstream_region_1990_2026_records.csv"
SUMMARY = DATA / "capture_batch_nonmainstream_region_1990_2026_source_summary.csv"
IMPACT = DATA / "nonmainstream_region_impact_ratings_1990_2026_v1.csv"
OUTPUT = DATA / "nonmainstream_region_capture_health_v1.csv"
REPORT = DOCS / "NONMAINSTREAM_REGION_CAPTURE_HEALTH_v1.md"

FIELDS = ["metric", "value", "count", "rate", "notes"]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def pct(num: int, den: int) -> str:
    if den <= 0:
        return "0.00"
    return f"{(num / den) * 100:.2f}"


def has_required_record_fields(row: dict[str, str]) -> bool:
    required = [
        "capture_id",
        "source_name",
        "source_identifier",
        "source_record_url",
        "source_title",
        "source_description",
        "source_rights_text",
        "image_presence_code",
        "rights_review_required",
        "citation_basis",
    ]
    return all((row.get(field) or "").strip() for field in required)


def source_visible(row: dict[str, str]) -> bool:
    return row.get("image_presence_code") in {"IMG01", "IMG02", "IMG03"} or bool(row.get("image_url_detected"))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def add_counter(out: list[dict[str, str]], metric: str, counter: Counter[str], total: int, notes: str = "") -> None:
    for value, count in counter.most_common():
        out.append(
            {
                "metric": metric,
                "value": value or "(blank)",
                "count": str(count),
                "rate": pct(count, total),
                "notes": notes,
            }
        )


def main() -> None:
    targets = read_csv(TARGETS)
    records = read_csv(RECORDS)
    summaries = read_csv(SUMMARY)
    impacts = read_csv(IMPACT)

    target_count = len(targets)
    captured_source_count = sum(1 for row in summaries if int(row.get("captured_records") or 0) > 0)
    total = len(records)
    complete_count = sum(1 for row in records if has_required_record_fields(row))
    source_visible_count = sum(1 for row in records if source_visible(row))
    rights_review_count = sum(1 for row in records if (row.get("rights_review_required") or "").lower() == "true")

    rows: list[dict[str, str]] = [
        {
            "metric": "target_source_coverage",
            "value": "captured_sources_over_targets",
            "count": f"{captured_source_count}/{target_count}",
            "rate": pct(captured_source_count, target_count),
            "notes": "How many planned non-mainstream regional source targets produced at least one record.",
        },
        {
            "metric": "record_health",
            "value": "required_fields_complete",
            "count": f"{complete_count}/{total}",
            "rate": pct(complete_count, total),
            "notes": "Required source, citation, rights, title, description, and image-state fields present.",
        },
        {
            "metric": "img_rate",
            "value": "source_visible_or_source_hosted",
            "count": f"{source_visible_count}/{total}",
            "rate": pct(source_visible_count, total),
            "notes": "IMG01/IMG02/IMG03 or source-hosted image URL; not an open-image claim.",
        },
        {
            "metric": "rights_review_rate",
            "value": "rights_review_required_true",
            "count": f"{rights_review_count}/{total}",
            "rate": pct(rights_review_count, total),
            "notes": "All new rows should require item-level rights review.",
        },
    ]

    add_counter(rows, "macro_region_coverage", Counter(row.get("macro_region") for row in summaries if int(row.get("captured_records") or 0) > 0), captured_source_count)
    add_counter(rows, "record_place_coverage", Counter(row.get("source_place_text") for row in records), total)
    add_counter(rows, "image_state_distribution", Counter(row.get("image_presence_code") for row in records), total)
    add_counter(rows, "impact_factor_rating", Counter(row.get("impact_rating") for row in impacts), len(impacts), "Internal triage only, not public authority.")

    write_csv(OUTPUT, rows)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Non-mainstream Region Capture Health v1",
        "",
        "Audit scope: non-mainstream regional content capture 1990-2026 v1.",
        "",
        "## Top Metrics",
        "",
        f"- Target source coverage: {captured_source_count}/{target_count} ({pct(captured_source_count, target_count)}%)",
        f"- Record health: {complete_count}/{total} ({pct(complete_count, total)}%)",
        f"- IMG/source-visible rate: {source_visible_count}/{total} ({pct(source_visible_count, total)}%)",
        f"- Rights-review required rate: {rights_review_count}/{total} ({pct(rights_review_count, total)}%)",
        "",
        "## Image States",
        "",
    ]
    for state, count in Counter(row.get("image_presence_code") for row in records).most_common():
        lines.append(f"- {state}: {count}")
    lines.extend(["", "## Impact Factor Ratings", ""])
    for rating, count in Counter(row.get("impact_rating") for row in impacts).most_common():
        lines.append(f"- {rating}: {count}")
    lines.extend(["", "## Macro-region Coverage", ""])
    for region, count in Counter(row.get("macro_region") for row in summaries if int(row.get("captured_records") or 0) > 0).most_common():
        lines.append(f"- {region}: {count} captured sources")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The IMG/source-visible rate counts source-hosted visual routes only. It does not mean the project may locally copy, republish, or treat these images as open. Impact factor ratings are internal next-work triage.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"target_source_coverage={pct(captured_source_count, target_count)}")
    print(f"record_health={pct(complete_count, total)}")
    print(f"img_rate={pct(source_visible_count, total)}")
    print("impact_ratings=" + ",".join(f"{k}:{v}" for k, v in Counter(row.get("impact_rating") for row in impacts).most_common()))
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
