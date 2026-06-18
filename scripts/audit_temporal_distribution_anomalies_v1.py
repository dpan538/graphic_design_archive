#!/usr/bin/env python3
"""Audit temporal distribution and recency anomalies in capture records.

This script is intentionally diagnostic. It does not rewrite capture records.
It separates source-profile / source-page span records from object-dated
records so access-year and coverage-target years do not masquerade as object
years in 5-year / 10-year coverage reviews.
"""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

YEAR_COUNTS = DATA / "temporal_distribution_year_counts_v1.csv"
BIN5_COUNTS = DATA / "temporal_distribution_5yr_bins_v1.csv"
BIN10_COUNTS = DATA / "temporal_distribution_10yr_bins_v1.csv"
RECENT_REVIEW = DATA / "temporal_recent_anomaly_review_v1.csv"
GAP_PRIORITY = DATA / "temporal_gap_priority_v1.csv"
REPORT = DOCS / "TEMPORAL_DISTRIBUTION_ANOMALY_AUDIT_v1.md"

YEAR_FIELDS = ["year", "all_records", "object_dated_records", "span_or_profile_records"]
BIN_FIELDS = [
    "bin_start",
    "bin_end",
    "all_records",
    "object_dated_records",
    "span_or_profile_records",
    "object_share_of_expected",
    "status",
]
RECENT_FIELDS = [
    "capture_file",
    "capture_id",
    "source_name",
    "source_title",
    "date_start",
    "date_end",
    "source_date_text",
    "source_object_type",
    "source_place_text",
    "image_presence_code",
    "recent_year",
    "review_reason",
    "source_record_url",
]
GAP_FIELDS = [
    "bin_start",
    "bin_end",
    "object_dated_records",
    "expected_equalized_count",
    "share_of_expected",
    "priority",
    "recommended_capture_focus",
]

RECENT_YEARS = {2025, 2026}
GAP_START_YEAR = 1930
GAP_END_YEAR = 2026


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def lower(value: object) -> str:
    return clean(value).lower()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def capture_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(DATA.glob("capture_batch_*_records.csv")):
        if "cell_assignments" in path.name:
            continue
        for row in read_csv(path):
            row = dict(row)
            row["_capture_file"] = path.name
            rows.append(row)
    return rows


def safe_year(value: object) -> int | None:
    text = clean(value)
    if not text:
        return None
    try:
        year = int(float(text))
    except ValueError:
        return None
    if 1830 <= year <= 2026:
        return year
    return None


def record_year(row: dict[str, str]) -> int | None:
    return safe_year(row.get("date_end")) or safe_year(row.get("date_start"))


def year_span(row: dict[str, str]) -> tuple[int | None, int | None]:
    return safe_year(row.get("date_start")), safe_year(row.get("date_end"))


def source_date_object_years(row: dict[str, str]) -> list[int]:
    """Years stated in source_date_text, excluding access/coverage-only text."""
    source_date = lower(row.get("source_date_text"))
    if not source_date:
        return []
    if "accessed" in source_date or "coverage target" in source_date:
        return []
    years: list[int] = []
    for match in re.findall(r"\b(1[7-9]\d{2}|20[0-2]\d)\b", source_date):
        year = safe_year(match)
        if year is not None:
            years.append(year)
    return years


def access_year_used_as_object_year(row: dict[str, str]) -> bool:
    start, end = year_span(row)
    source_date = lower(row.get("source_date_text"))
    citation = lower(row.get("citation_basis"))
    if "accessed 2026" in source_date:
        return True
    if end in RECENT_YEARS and "accessed 2026" in citation and not source_date_object_years(row):
        return True
    if start in RECENT_YEARS and end in RECENT_YEARS and "accessed 2026" in citation and not source_date_object_years(row):
        return True
    return False


def anomaly_reasons(row: dict[str, str]) -> list[str]:
    start, end = year_span(row)
    source_date = lower(row.get("source_date_text"))
    object_type = lower(row.get("source_object_type"))
    notes = lower(" ".join([row.get("source_notes", ""), row.get("classification_rationale", ""), row.get("uncertainty_note", "")]))
    title = lower(row.get("source_title"))
    reasons: list[str] = []

    if "coverage target" in source_date:
        reasons.append("coverage_target_span_not_object_year")
    if access_year_used_as_object_year(row):
        reasons.append("access_year_as_object_year")
    if "source profile" in object_type:
        reasons.append("source_profile_not_item_record")
    if "official source image-bearing record" in object_type:
        reasons.append("source_page_image_record_not_object_year")
    if start is not None and end is not None and end - start >= 25:
        reasons.append("long_span_record")
    if "poster session" in title or "poster session" in notes:
        reasons.append("event_or_session_photo_review")
    if "source page, logo, hero, or collection image" in notes:
        reasons.append("hero_or_page_image_not_item_final")
    if end in RECENT_YEARS and start is not None and start < 2020:
        reasons.append("recent_end_year_with_old_start")
    if end == 2026 and not reasons:
        reasons.append("recent_2026_object_review")
    if end == 2025 and not reasons:
        reasons.append("recent_2025_object_review")
    return reasons


def is_span_or_profile_record(row: dict[str, str]) -> bool:
    reasons = set(anomaly_reasons(row))
    span_reasons = {
        "coverage_target_span_not_object_year",
        "access_year_as_object_year",
        "source_profile_not_item_record",
        "source_page_image_record_not_object_year",
        "hero_or_page_image_not_item_final",
    }
    return bool(reasons & span_reasons)


def object_temporal_eligible(row: dict[str, str]) -> bool:
    year = record_year(row)
    if year is None:
        return False
    if is_span_or_profile_record(row):
        return False
    return True


def bin_start(year: int, size: int) -> int:
    return (year // size) * size


def bin_rows(rows: list[dict[str, str]], size: int) -> list[dict[str, object]]:
    all_counts: Counter[int] = Counter()
    object_counts: Counter[int] = Counter()
    span_counts: Counter[int] = Counter()
    for row in rows:
        year = record_year(row)
        if year is None:
            continue
        start = bin_start(year, size)
        all_counts[start] += 1
        if object_temporal_eligible(row):
            object_counts[start] += 1
        else:
            span_counts[start] += 1

    starts = range(1830, 2027, size)
    eligible_gap_bins = [start for start in range(GAP_START_YEAR, GAP_END_YEAR + 1, 5)]
    expected = sum(object_counts[start] for start in eligible_gap_bins) / len(eligible_gap_bins)
    out: list[dict[str, object]] = []
    for start in starts:
        end = min(start + size - 1, 2026)
        share = (object_counts[start] / expected) if expected else 0.0
        if size == 5 and start >= GAP_START_YEAR:
            if start >= 2020 and share >= 1.4:
                status = "recent_overfull_review"
            elif share < 0.55:
                status = "severe_gap"
            elif share < 0.75:
                status = "moderate_gap"
            else:
                status = "ok"
        else:
            status = "diagnostic"
        out.append(
            {
                "bin_start": start,
                "bin_end": end,
                "all_records": all_counts[start],
                "object_dated_records": object_counts[start],
                "span_or_profile_records": span_counts[start],
                "object_share_of_expected": f"{share:.3f}",
                "status": status,
            }
        )
    return out


def capture_focus(start: int, end: int) -> str:
    if 1955 <= start <= 1960:
        return "late-1950s/early-1960s institutional posters, book covers, labels, advertising, design-school records"
    if 1980 <= start <= 1985:
        return "1980s posters, record sleeves, magazine covers, identity systems, political/cultural graphics"
    if 1990 <= start <= 1995:
        return "1990s early web/platform graphics, studio projects, posters, magazines, cultural identity systems"
    if start == 2000:
        return "2000-2004 studio/platform projects, early web visual communication, art-school/community posters"
    return "targeted object-dated records with explicit source year and source-visible image evidence"


def main() -> None:
    rows = capture_rows()
    year_all: Counter[int] = Counter()
    year_object: Counter[int] = Counter()
    year_span: Counter[int] = Counter()
    recent_rows: list[dict[str, object]] = []

    for row in rows:
        year = record_year(row)
        if year is None:
            continue
        year_all[year] += 1
        if object_temporal_eligible(row):
            year_object[year] += 1
        else:
            year_span[year] += 1
        if year in RECENT_YEARS or (year >= 2020 and anomaly_reasons(row)):
            reasons = anomaly_reasons(row)
            if reasons:
                recent_rows.append(
                    {
                        "capture_file": row.get("_capture_file", ""),
                        "capture_id": row.get("capture_id", ""),
                        "source_name": row.get("source_name", ""),
                        "source_title": row.get("source_title", ""),
                        "date_start": row.get("date_start", ""),
                        "date_end": row.get("date_end", ""),
                        "source_date_text": row.get("source_date_text", ""),
                        "source_object_type": row.get("source_object_type", ""),
                        "source_place_text": row.get("source_place_text", ""),
                        "image_presence_code": row.get("image_presence_code", ""),
                        "recent_year": year,
                        "review_reason": ";".join(reasons),
                        "source_record_url": row.get("source_record_url", ""),
                    }
                )

    year_rows = [
        {
            "year": year,
            "all_records": year_all[year],
            "object_dated_records": year_object[year],
            "span_or_profile_records": year_span[year],
        }
        for year in range(1830, 2027)
    ]
    bin5 = bin_rows(rows, 5)
    bin10 = bin_rows(rows, 10)

    expected = sum(int(row["object_dated_records"]) for row in bin5 if GAP_START_YEAR <= int(row["bin_start"]) <= GAP_END_YEAR) / len(
        [row for row in bin5 if GAP_START_YEAR <= int(row["bin_start"]) <= GAP_END_YEAR]
    )
    gap_rows: list[dict[str, object]] = []
    for row in bin5:
        start = int(row["bin_start"])
        if start < GAP_START_YEAR or start > GAP_END_YEAR:
            continue
        count = int(row["object_dated_records"])
        share = count / expected if expected else 0.0
        status = str(row["status"])
        if status in {"severe_gap", "moderate_gap", "recent_overfull_review"}:
            gap_rows.append(
                {
                    "bin_start": start,
                    "bin_end": row["bin_end"],
                    "object_dated_records": count,
                    "expected_equalized_count": f"{expected:.1f}",
                    "share_of_expected": f"{share:.3f}",
                    "priority": status,
                    "recommended_capture_focus": capture_focus(start, int(row["bin_end"])),
                }
            )

    recent_reason_counts = Counter()
    recent_file_counts = Counter()
    for row in recent_rows:
        recent_file_counts[str(row["capture_file"])] += 1
        for reason in str(row["review_reason"]).split(";"):
            recent_reason_counts[reason] += 1

    write_csv(YEAR_COUNTS, year_rows, YEAR_FIELDS)
    write_csv(BIN5_COUNTS, bin5, BIN_FIELDS)
    write_csv(BIN10_COUNTS, bin10, BIN_FIELDS)
    write_csv(RECENT_REVIEW, recent_rows, RECENT_FIELDS)
    write_csv(GAP_PRIORITY, sorted(gap_rows, key=lambda row: (row["priority"] != "severe_gap", float(row["share_of_expected"]))), GAP_FIELDS)

    lines = [
        "# Temporal Distribution Anomaly Audit v1",
        "",
        "Scope: capture records only. This audit separates object-dated records from source-profile or source-page span records.",
        "",
        "## Summary",
        "",
        f"- Capture records scanned: {len(rows)}",
        f"- Recent anomaly review rows: {len(recent_rows)}",
        f"- 2025 all/object/span: {year_all[2025]} / {year_object[2025]} / {year_span[2025]}",
        f"- 2026 all/object/span: {year_all[2026]} / {year_object[2026]} / {year_span[2026]}",
        "",
        "## Recent Anomaly Reasons",
        "",
    ]
    for reason, count in recent_reason_counts.most_common():
        lines.append(f"- {reason}: {count}")
    lines.extend(["", "## Recent Anomaly Files", ""])
    for file_name, count in recent_file_counts.most_common(20):
        lines.append(f"- {file_name}: {count}")
    lines.extend(["", "## 5-Year Gap / Overfull Priorities", ""])
    for row in gap_rows[:30]:
        lines.append(
            f"- {row['bin_start']}-{row['bin_end']}: object={row['object_dated_records']}, "
            f"share={row['share_of_expected']}, priority={row['priority']}"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A high 2026 count is not automatically contemporary design coverage. In current data, much of it is access-year or coverage-span metadata from source-profile/image-page records.",
            "- Object-year coverage should use `object_dated_records`, not `all_records`, until span/profile records are normalized or excluded from object temporal metrics.",
            "- 1980s, 1990s, 2000-2004, and late-1950s/early-1960s bins remain priority capture targets.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"records_scanned={len(rows)}")
    print(f"recent_review_rows={len(recent_rows)}")
    print(f"2025 all/object/span={year_all[2025]}/{year_object[2025]}/{year_span[2025]}")
    print(f"2026 all/object/span={year_all[2026]}/{year_object[2026]}/{year_span[2026]}")
    print(f"recent_reasons={dict(recent_reason_counts.most_common())}")
    print(f"wrote {YEAR_COUNTS.relative_to(ROOT)}")
    print(f"wrote {BIN5_COUNTS.relative_to(ROOT)}")
    print(f"wrote {BIN10_COUNTS.relative_to(ROOT)}")
    print(f"wrote {RECENT_REVIEW.relative_to(ROOT)}")
    print(f"wrote {GAP_PRIORITY.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
