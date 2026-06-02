#!/usr/bin/env python3
"""Audit contemporary capture rows with the shared noise filter."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

from contemporary_noise_filter import evaluate_record


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_CSV = DATA / "contemporary_noise_filter_audit_v1.csv"
REPORT = ROOT / "docs" / "capture" / "CONTEMPORARY_NOISE_FILTER_AUDIT_v1.md"

INPUT_GLOBS = [
    "capture_batch_late_period_coverage_1970_2026_records.csv",
    "capture_batch_source_breadth_1970_2026_records.csv",
    "capture_batch_edge_wordpress_1970_2026_records.csv",
    "capture_batch_protocol_item_1970_2026_records.csv",
    "capture_batch_independent_asia_1990_2026_records.csv",
    "capture_batch_noncanonical_exact_sources_1970_2000_records.csv",
    "capture_batch_gap_noncanonical_image_text_1930_2000_records.csv",
]

FIELDNAMES = [
    "input_file",
    "capture_id",
    "source_id",
    "source_name",
    "source_identifier",
    "source_record_url",
    "source_title",
    "date_start",
    "date_end",
    "image_presence_code",
    "decision",
    "score",
    "design_score",
    "provenance_score",
    "risk_score",
    "source_family",
    "positive_signals",
    "negative_signals",
    "reason",
]


def read_rows() -> list[tuple[Path, dict[str, str]]]:
    rows: list[tuple[Path, dict[str, str]]] = []
    for name in INPUT_GLOBS:
        path = DATA / name
        if not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                rows.append((path, dict(row)))
    return rows


def write_report(rows: list[dict[str, str]]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    by_decision = Counter(row["decision"] for row in rows)
    by_source_family = Counter(row["source_family"] for row in rows)
    by_source = Counter(row["source_name"] for row in rows)
    by_input = Counter(row["input_file"] for row in rows)
    by_decision_source: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        by_decision_source[row["decision"]][row["source_name"]] += 1

    review_rows = [row for row in rows if row["decision"] in {"exclude_noise", "review_lead", "discovery_only"}]
    review_rows.sort(key=lambda row: (row["decision"], row["source_name"], row["source_title"]))
    sample = review_rows[:30]

    lines = [
        "# Contemporary Noise Filter Audit v1",
        "",
        "Date: 2026-06-01",
        "",
        "This audit applies a reusable contemporary-capture filter to existing 1970-2026 and adjacent late-period capture rows. It is not a deletion list. It marks which rows can proceed toward public surfaces, which should be downgraded to subsheet/card/text candidates, and which should remain discovery-only or review leads.",
        "",
        "## Summary",
        "",
        f"- Rows audited: {len(rows)}",
        f"- Include candidates: {by_decision.get('include_candidate', 0)}",
        f"- Downgrade candidates: {by_decision.get('downgrade_candidate', 0)}",
        f"- Review leads: {by_decision.get('review_lead', 0)}",
        f"- Discovery-only leads: {by_decision.get('discovery_only', 0)}",
        f"- Excluded noise candidates: {by_decision.get('exclude_noise', 0)}",
        "",
        "## Decisions",
        "",
        "| Decision | Rows |",
        "|---|---:|",
    ]
    for decision, count in by_decision.most_common():
        lines.append(f"| {decision} | {count} |")

    lines.extend(
        [
            "",
            "## Source Families",
            "",
            "| Source family | Rows |",
            "|---|---:|",
        ]
    )
    for family, count in by_source_family.most_common():
        lines.append(f"| {family} | {count} |")

    lines.extend(
        [
            "",
            "## Input Files",
            "",
            "| Input file | Rows |",
            "|---|---:|",
        ]
    )
    for input_file, count in by_input.most_common():
        lines.append(f"| `{input_file}` | {count} |")

    lines.extend(
        [
            "",
            "## Largest Source Contributors",
            "",
            "| Source | Rows |",
            "|---|---:|",
        ]
    )
    for source, count in by_source.most_common(20):
        lines.append(f"| {source or 'Unknown'} | {count} |")

    lines.extend(
        [
            "",
            "## Decision Notes",
            "",
            "- `include_candidate` means the row has enough object/provenance language to remain in publication generation, subject to surface-gate thresholds.",
            "- `downgrade_candidate` means the row should usually become a subsheet, text sheet, card, slip, or grouped child rather than a main sheet.",
            "- `review_lead` means the row should stay in capture/research space until corroborated by a stronger object record or local source.",
            "- `discovery_only` is for social/repost platforms and should not become standalone evidence.",
            "- `exclude_noise` identifies likely jobs/events/commerce/policy/admin pages.",
            "",
            "## Review Sample",
            "",
            "| Decision | Source | Title | Reason |",
            "|---|---|---|---|",
        ]
    )
    for row in sample:
        title = (row["source_title"] or "").replace("|", "/")[:100]
        source = (row["source_name"] or "").replace("|", "/")[:60]
        reason = row["reason"].replace("|", "/")
        lines.append(f"| {row['decision']} | {source} | {title} | {reason} |")

    lines.extend(
        [
            "",
            "## Constraint",
            "",
            "Future 1990-2026 captures should call the shared filter before writing publication-ready rows. Rejected rows may still be preserved as source leads, but they must not mint main sheets. This prevents contemporary independent-source expansion from turning into a general design-blog or event-listing scrape.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    output_rows: list[dict[str, str]] = []
    for path, row in read_rows():
        decision = evaluate_record(row)
        output_rows.append(
            {
                "input_file": path.name,
                "capture_id": row.get("capture_id", ""),
                "source_id": row.get("source_id", ""),
                "source_name": row.get("source_name", ""),
                "source_identifier": row.get("source_identifier", ""),
                "source_record_url": row.get("source_record_url", ""),
                "source_title": row.get("source_title", ""),
                "date_start": row.get("date_start", ""),
                "date_end": row.get("date_end", ""),
                "image_presence_code": row.get("image_presence_code", ""),
                "decision": decision.decision,
                "score": str(decision.score),
                "design_score": str(decision.design_score),
                "provenance_score": str(decision.provenance_score),
                "risk_score": str(decision.risk_score),
                "source_family": decision.source_family,
                "positive_signals": decision.positive_signals,
                "negative_signals": decision.negative_signals,
                "reason": decision.reason,
            }
        )

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(output_rows)

    write_report(output_rows)
    print(f"wrote {OUT_CSV.relative_to(ROOT)} ({len(output_rows)} rows)")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
