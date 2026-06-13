#!/usr/bin/env python3
"""Audit Cooper Hewitt IMG02 repair candidates against local item metadata.

This preflight is deliberately conservative. It reads already captured metadata
and does not call GraphQL, fetch item pages, download images, mutate records, or
upgrade IMG01/IMG03.
"""

from __future__ import annotations

import csv
import re
from collections import Counter

from lib.archive_audit import DATA, DOCS, ROOT, clean, read_csv, write_csv


SOURCE_NAME = "Cooper Hewitt Collection GraphQL API"
CANDIDATES = DATA / "image_rights_repair_candidates_v1.csv"
RECORDS = DATA / "capture_batch_cooperhewitt_graphql_image_ready_1830_2026_records.csv"
OUTPUT_ROWS = DATA / "cooperhewitt_rights_repair_preflight_v1.csv"
OUTPUT_SUMMARY = DATA / "cooperhewitt_rights_repair_summary_v1.csv"
OUTPUT_REPORT = DOCS / "COOPERHEWITT_RIGHTS_REPAIR_PREFLIGHT_v1.md"

ROW_FIELDS = [
    "surface_id",
    "source_record_id",
    "source_record_url",
    "title",
    "best_image_state",
    "local_record_found",
    "local_image_state",
    "local_rights_review_required",
    "rights_signal",
    "future_action",
    "upgrade_recommendation",
    "automatic_upgrade_allowed",
    "legal_excerpt",
    "rights_basis_excerpt",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]

BLOCKING_TERMS = [
    "copyright",
    "no rights owned",
    "restrictions",
    "permission",
    "approval",
    "artist rights society",
    "ars, new york",
    "bild-kunst",
    "wolfgang",
]

OPEN_TERMS = [
    "cc0",
    "public domain",
    "open access",
    "creative commons zero",
    "no known copyright",
]


def norm_url(value: str) -> str:
    return clean(value).rstrip("/")


def excerpt(value: str, limit: int = 220) -> str:
    value = re.sub(r"\s+", " ", clean(value))
    if len(value) <= limit:
        return value
    return value[: limit - 1].rsplit(" ", 1)[0] + "..."


def records_by_url() -> dict[str, dict[str, str]]:
    rows = read_csv(RECORDS)
    return {norm_url(row.get("source_record_url", "")): row for row in rows if row.get("source_record_url")}


def signal_from_record(row: dict[str, str] | None) -> tuple[str, str, str]:
    if not row:
        return "local_record_missing", "network_verify_item_record_before_any_change", "no_upgrade"
    legal_blob = " ".join(
        [
            row.get("source_notes", ""),
            row.get("source_rights_text", ""),
            row.get("rights_basis", ""),
            row.get("image_state_review_note", ""),
        ]
    )
    legal_norm = legal_blob.lower()
    if any(term in legal_norm for term in BLOCKING_TERMS):
        return "blocked_by_local_copyright_or_restriction_signal", "keep_img02_or_manual_rights_review", "no_upgrade"
    if any(term in legal_norm for term in OPEN_TERMS):
        return "possible_open_text_requires_item_verification", "manual_item_page_verification_required", "review_only_no_automatic_upgrade"
    if clean(row.get("source_notes")):
        return "local_legal_credit_only_no_open_evidence", "keep_img02_pending_item_rights_evidence", "no_upgrade"
    return "no_item_level_open_rights_evidence", "keep_img02_pending_item_rights_evidence", "no_upgrade"


def build_rows() -> list[dict[str, str]]:
    records = records_by_url()
    rows = []
    for candidate in read_csv(CANDIDATES):
        if candidate.get("source_name") != SOURCE_NAME:
            continue
        record = records.get(norm_url(candidate.get("source_url", "")))
        signal, action, recommendation = signal_from_record(record)
        rows.append(
            {
                "surface_id": candidate.get("surface_id", ""),
                "source_record_id": clean(record.get("source_identifier")) if record else "",
                "source_record_url": candidate.get("source_url", ""),
                "title": candidate.get("title", ""),
                "best_image_state": candidate.get("best_image_state", ""),
                "local_record_found": str(record is not None).lower(),
                "local_image_state": clean(record.get("image_presence_code")) if record else "",
                "local_rights_review_required": clean(record.get("rights_review_required")) if record else "",
                "rights_signal": signal,
                "future_action": action,
                "upgrade_recommendation": recommendation,
                "automatic_upgrade_allowed": "false",
                "legal_excerpt": excerpt(record.get("source_notes", "")) if record else "",
                "rights_basis_excerpt": excerpt(record.get("source_rights_text", "") or record.get("rights_basis", "")) if record else "",
            }
        )
    rows.sort(key=lambda row: (row["rights_signal"], row["title"], row["surface_id"]))
    return rows


def write_report(rows: list[dict[str, str]]) -> None:
    signals = Counter(row["rights_signal"] for row in rows)
    found = Counter(row["local_record_found"] for row in rows)
    upgrades = Counter(row["upgrade_recommendation"] for row in rows)
    summary_rows = [
        {"metric": "cooperhewitt_candidate_rows", "value": str(len(rows)), "notes": "Cooper Hewitt rows from image_rights_repair_candidates_v1."},
        {"metric": "local_records_found", "value": str(found.get("true", 0)), "notes": "Rows matched to existing Cooper Hewitt capture records."},
        {"metric": "automatic_upgrade_allowed_rows", "value": "0", "notes": "No automatic IMG03 upgrades are permitted by this preflight."},
    ]
    for key, value in signals.most_common():
        summary_rows.append({"metric": f"rights_signal_{key}", "value": str(value), "notes": "Conservative local metadata signal."})
    for key, value in upgrades.most_common():
        summary_rows.append({"metric": f"upgrade_recommendation_{key}", "value": str(value), "notes": "Preflight recommendation."})
    write_csv(OUTPUT_SUMMARY, summary_rows, SUMMARY_FIELDS)

    lines = [
        "# Cooper Hewitt Rights Repair Preflight v1",
        "",
        "This local preflight checks Cooper Hewitt IMG02 repair candidates against already captured item metadata. It does not call GraphQL, fetch item pages, download images, mutate surfaces, or upgrade IMG01/IMG03.",
        "",
        "## Result",
        "",
        f"- Cooper Hewitt candidate rows: {len(rows)}",
        f"- local records found: {found.get('true', 0)}",
        "- automatic upgrades allowed: 0",
        "",
        "## Rights Signals",
        "",
    ]
    for key, value in signals.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Cooper Hewitt remains a high-value source-visible IMG02 family, but local metadata does not support automatic verified-open promotion.",
            "- Rows with copyright/restriction signals should stay IMG02 unless an item page later exposes explicit open evidence.",
            "- Rows with credit-only or no open-rights evidence also stay IMG02; source-hosted display is not the same as project-local open publication.",
            "",
            "## Output Files",
            "",
            f"- `{OUTPUT_ROWS.relative_to(ROOT)}`",
            f"- `{OUTPUT_SUMMARY.relative_to(ROOT)}`",
        ]
    )
    OUTPUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(OUTPUT_ROWS, rows, ROW_FIELDS)
    write_report(rows)
    print(f"cooperhewitt_candidate_rows={len(rows)}")
    print(f"wrote {OUTPUT_ROWS.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
