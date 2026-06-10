#!/usr/bin/env python3
"""Create a stratified QA sample for region auto-normalization candidates."""

from __future__ import annotations

from collections import Counter, defaultdict

from lib.archive_audit import DATA, DOCS, ROOT, read_csv, write_csv


CANDIDATES = DATA / "region_geography_normalization_candidates_v1.csv"
SAMPLE = DATA / "region_geography_normalization_auto_review_sample_v1.csv"
REPORT = DOCS / "REGION_GEOGRAPHY_NORMALIZATION_AUTO_REVIEW_SAMPLE_v1.md"

FIELDS = [
    "sample_id",
    "sample_type",
    "target_display_labels",
    "target_region_ids",
    "target_geo_ids",
    "surface_id",
    "source_record_id",
    "title",
    "date_text",
    "period_band",
    "source_name",
    "current_region_label",
    "candidate_action",
    "confidence",
    "evidence_fields",
    "evidence_snippet",
    "review_question",
]


def sample_rows(rows: list[dict[str, str]], max_per_target: int = 8) -> list[dict[str, str]]:
    auto = [row for row in rows if row.get("candidate_action") == "auto_map_from_unresolved"]
    low_signal = [row for row in rows if row.get("candidate_action") == "review_low_signal_geo_candidates"]
    sensitive = [
        row
        for row in rows
        if row.get("current_region_label") == "Unresolved region"
        and row.get("candidate_action") not in {"auto_map_from_unresolved", "keep_pending", "review_low_signal_geo_candidates"}
    ]

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in auto:
        grouped[row.get("target_display_labels", "Unknown")].append(row)

    out: list[dict[str, str]] = []
    for target, target_rows in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        for row in target_rows[:max_per_target]:
            out.append(format_sample(len(out) + 1, "auto_map_stratified", row, "Does high-signal metadata support this target geography?"))

    for row in low_signal[:40]:
        out.append(format_sample(len(out) + 1, "low_signal_review", row, "Is the low-signal location an actual object/source geography or only incidental text?"))

    for row in sensitive[:40]:
        out.append(format_sample(len(out) + 1, "sensitive_or_multi_review", row, "Does this require split, historical, protocol, or multi-geography handling?"))

    return out


def format_sample(sample_id: int, sample_type: str, row: dict[str, str], question: str) -> dict[str, str]:
    return {
        "sample_id": f"RGN-QA-{sample_id:03d}",
        "sample_type": sample_type,
        "target_display_labels": row.get("target_display_labels", ""),
        "target_region_ids": row.get("target_region_ids", ""),
        "target_geo_ids": row.get("target_geo_ids", ""),
        "surface_id": row.get("surface_id", ""),
        "source_record_id": row.get("source_record_id", ""),
        "title": row.get("title", ""),
        "date_text": row.get("date_text", ""),
        "period_band": row.get("period_band", ""),
        "source_name": row.get("source_name", ""),
        "current_region_label": row.get("current_region_label", ""),
        "candidate_action": row.get("candidate_action", ""),
        "confidence": row.get("confidence", ""),
        "evidence_fields": row.get("evidence_fields", ""),
        "evidence_snippet": row.get("evidence_snippet", ""),
        "review_question": question,
    }


def write_report(rows: list[dict[str, str]], samples: list[dict[str, str]]) -> None:
    action_counts = Counter(row.get("candidate_action", "") for row in rows)
    auto_targets = Counter(
        row.get("target_display_labels", "")
        for row in rows
        if row.get("candidate_action") == "auto_map_from_unresolved"
    )
    sample_types = Counter(row.get("sample_type", "") for row in samples)
    lines = [
        "# Region / Geography Auto Candidate QA Sample v1",
        "",
        "Scope: stratified review sample for proposal-only region/geography normalization candidates. This report does not apply any candidate.",
        "",
        "## Summary",
        "",
        f"- candidate rows read: {len(rows)}",
        f"- QA sample rows: {len(samples)}",
        f"- auto-map candidates available: {action_counts.get('auto_map_from_unresolved', 0)}",
        f"- low-signal candidates available: {action_counts.get('review_low_signal_geo_candidates', 0)}",
        "",
        "## Sample Types",
        "",
    ]
    for sample_type, count in sample_types.most_common():
        lines.append(f"- {sample_type}: {count}")
    lines.extend(["", "## Largest Auto Targets", ""])
    for target, count in auto_targets.most_common(20):
        lines.append(f"- {target}: {count}")
    lines.extend(
        [
            "",
            "## Review Rule",
            "",
            "- If the stratified sample shows low false-positive risk, the next script may generate a dry-run normalized payload for `auto_map_from_unresolved` only.",
            "- If false positives cluster by source family, add source-family guards before any application script.",
            "- Low-signal and sensitive/multi-review samples must not be applied automatically.",
            "",
            "## Generated File",
            "",
            f"- `data/{SAMPLE.name}`",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = read_csv(CANDIDATES)
    samples = sample_rows(rows)
    write_csv(SAMPLE, samples, FIELDS)
    write_report(rows, samples)
    print(f"candidate_rows={len(rows)}")
    print(f"sample_rows={len(samples)}")
    print(f"wrote {SAMPLE.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
