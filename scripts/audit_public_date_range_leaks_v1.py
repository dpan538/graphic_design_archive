#!/usr/bin/env python3
"""Audit broad capture/source ranges that could leak into public chronology."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PAYLOAD = ROOT / "generated" / "public_surfaces_v1.json"
OUT_CSV = DATA / "public_date_range_leak_audit_v1.csv"
REPORT = ROOT / "docs" / "capture" / "PUBLIC_DATE_RANGE_LEAK_AUDIT_v1.md"

PHASE_PATTERNS = (
    "1970-2026",
    "1970–2026",
    "1930-1970",
    "1930–1970",
    "1830-1930",
    "1830–1930",
)


def read_csv_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in DATA.glob("capture_batch_*_records.csv"):
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                row = dict(row)
                row["_file"] = path.name
                rows.append(row)
    return rows


def row_issue(row: dict[str, str]) -> tuple[str, str] | None:
    blob = " ".join(
        str(row.get(key, ""))
        for key in (
            "source_date_text",
            "date_start",
            "date_end",
            "source_title",
            "source_object_type",
            "source_medium",
            "historical_context_note",
            "classification_rationale",
        )
    )
    start = row.get("date_start")
    end = row.get("date_end")
    if start and end and start.isdigit() and end.isdigit() and int(end) - int(start) > 40 and int(end) >= 2026:
        return "broad_record_date_range", f"{start}-{end}"
    blob_l = blob.lower()
    for pattern in PHASE_PATTERNS:
        variants = {pattern.lower(), pattern.lower().replace("–", "-"), pattern.lower().replace("-", "–")}
        if any(re.search(rf"{re.escape(variant)}[^\n.;]{{0,40}}capture", blob_l) for variant in variants):
            return "phase_label_in_record_text", pattern
    return None


def payload_issues() -> list[dict[str, str]]:
    if not PAYLOAD.exists():
        return []
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    issues: list[dict[str, str]] = []
    for surface in payload.get("surfaces", []):
        visible_blob = json.dumps(
            {
                "title": surface.get("title"),
                "dateText": surface.get("dateText"),
                "dateStart": surface.get("dateStart"),
                "dateEnd": surface.get("dateEnd"),
                "descriptionSummary": surface.get("descriptionSummary"),
                "sourceDescription": surface.get("sourceDescription"),
                "sourceNotes": surface.get("sourceNotes"),
                "sourceSubjects": surface.get("sourceSubjects"),
                "historicalContextNote": surface.get("historicalContextNote"),
                "classificationRationale": surface.get("classificationRationale"),
                "uncertaintyNote": surface.get("uncertaintyNote"),
                "citationBasis": surface.get("citationBasis"),
                "tables": surface.get("tables"),
            },
            ensure_ascii=False,
        )
        for pattern in PHASE_PATTERNS:
            if pattern in visible_blob:
                issues.append(
                    {
                        "source": "public_payload",
                        "record_id": surface.get("sourceRecordId", ""),
                        "title": surface.get("title", ""),
                        "issue_type": "phase_label_in_public_payload",
                        "value": pattern,
                    }
                )
                break
        start = surface.get("dateStart")
        end = surface.get("dateEnd")
        if isinstance(start, int) and isinstance(end, int) and end - start > 40 and end >= 2026:
            issues.append(
                {
                    "source": "public_payload",
                    "record_id": surface.get("sourceRecordId", ""),
                    "title": surface.get("title", ""),
                    "issue_type": "broad_public_date_range",
                    "value": f"{start}-{end}",
                }
            )
    for folder in payload.get("folders", []):
        visible_blob = json.dumps(
            {
                "folderId": folder.get("folderId"),
                "type": folder.get("type"),
                "title": folder.get("title"),
                "dateStart": folder.get("dateStart"),
                "dateEnd": folder.get("dateEnd"),
                "scopeNote": folder.get("scopeNote"),
            },
            ensure_ascii=False,
        )
        for pattern in PHASE_PATTERNS:
            if pattern in visible_blob:
                issues.append(
                    {
                        "source": "public_payload_folder",
                        "record_id": folder.get("folderId", ""),
                        "title": folder.get("title", ""),
                        "issue_type": "phase_label_in_public_folder",
                        "value": pattern,
                    }
                )
                break
        start = folder.get("dateStart")
        end = folder.get("dateEnd")
        if (
            folder.get("type") == "movement"
            and isinstance(start, int)
            and isinstance(end, int)
            and end - start > 35
        ):
            issues.append(
                {
                    "source": "public_payload_folder",
                    "record_id": folder.get("folderId", ""),
                    "title": folder.get("title", ""),
                    "issue_type": "broad_movement_folder_date_range",
                    "value": f"{start}-{end}",
                }
            )
    return issues


def main() -> None:
    issues: list[dict[str, str]] = []
    for row in read_csv_rows():
        issue = row_issue(row)
        if not issue:
            continue
        issue_type, value = issue
        issues.append(
            {
                "source": row.get("_file", ""),
                "record_id": row.get("capture_id", ""),
                "title": row.get("source_title", ""),
                "issue_type": issue_type,
                "value": value,
            }
        )
    issues.extend(payload_issues())

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        fields = ["source", "record_id", "title", "issue_type", "value"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(issues)

    counts = Counter(issue["issue_type"] for issue in issues)
    lines = [
        "# Public Date Range Leak Audit v1",
        "",
        "Date: 2026-06-01",
        "",
        "This audit catches capture-phase or collection-scope date ranges that must not be displayed as object or movement chronology.",
        "",
        "## Summary",
        "",
        f"- Issues found: {len(issues)}",
    ]
    for key, count in counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Rule", ""])
    lines.append("Broad ranges such as `1970-2026` are valid for capture planning or source collection scope only. Public sheets must use item-level dates, precise group ranges, or an explicit `undated/source scope` state.")
    lines.extend(["", "## Sample", "", "| Source | Record | Issue | Value | Title |", "|---|---|---|---|---|"])
    for issue in issues[:40]:
        title = re.sub(r"\s+", " ", issue["title"]).replace("|", "/")[:90]
        lines.append(f"| {issue['source']} | {issue['record_id']} | {issue['issue_type']} | {issue['value']} | {title} |")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_CSV.relative_to(ROOT)} ({len(issues)} issues)")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
