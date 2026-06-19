#!/usr/bin/env python3
"""Build a pre-freeze public rebuild exclusion list from cleaning queues.

This script is non-destructive: it does not edit capture records or public
surfaces. It converts the P0 pre-freeze cleaning queue into a stable
source_file + capture_id exclusion table that the public-surface rebuild can
consume before generating new surfaces.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

QUEUE = DATA / "prefreeze_data_cleaning_priority_queue_v1.csv"
EXCLUSION_DELTA = DATA / "prefreeze_candidate_exclusion_delta_v1.csv"
EXCLUSION = DATA / "prefreeze_public_rebuild_exclusion_v1.csv"
SUMMARY = DATA / "prefreeze_public_rebuild_exclusion_summary_v1.csv"
REPORT = DOCS / "PREFREEZE_PUBLIC_REBUILD_EXCLUSION_v1.md"

EXCLUSION_FIELDS = [
    "source_file",
    "capture_id",
    "priority",
    "action_type",
    "risk_flags",
    "year",
    "region",
    "image_state",
    "title",
    "source_name",
    "recommendation",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]


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


def clean(value: object) -> str:
    return " ".join(str(value or "").split()).strip()


def build_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    queue = read_csv(QUEUE)
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    skipped_no_key = 0
    delta_rows_added = 0
    delta_rows_duplicate = 0

    for row in queue:
        if clean(row.get("priority")) != "P0":
            continue
        source_file = Path(clean(row.get("source_file"))).name
        capture_id = clean(row.get("item_id"))
        if not source_file or not capture_id:
            skipped_no_key += 1
            continue
        key = (source_file, capture_id)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "source_file": source_file,
                "capture_id": capture_id,
                "priority": "P0",
                "action_type": clean(row.get("action_type")),
                "risk_flags": clean(row.get("risk_flags")),
                "year": clean(row.get("year")),
                "region": clean(row.get("region")),
                "image_state": clean(row.get("image_state")),
                "title": clean(row.get("title"))[:260],
                "source_name": clean(row.get("source_name"))[:260],
                "recommendation": clean(row.get("recommendation")),
            }
        )

    for row in read_csv(EXCLUSION_DELTA):
        source_file = Path(clean(row.get("source_file"))).name
        capture_id = clean(row.get("capture_id"))
        if not source_file or not capture_id:
            skipped_no_key += 1
            continue
        key = (source_file, capture_id)
        if key in seen:
            delta_rows_duplicate += 1
            continue
        seen.add(key)
        delta_rows_added += 1
        rows.append(
            {
                "source_file": source_file,
                "capture_id": capture_id,
                "priority": clean(row.get("priority")) or "P0",
                "action_type": clean(row.get("action_type")) or "candidate_delta_review",
                "risk_flags": clean(row.get("risk_flags")),
                "year": clean(row.get("year")),
                "region": clean(row.get("region")),
                "image_state": clean(row.get("image_state")),
                "title": clean(row.get("title"))[:260],
                "source_name": clean(row.get("source_name"))[:260],
                "recommendation": clean(row.get("recommendation")),
            }
        )

    by_action = Counter(row["action_type"] for row in rows)
    by_source_file = Counter(row["source_file"] for row in rows)
    summary_rows: list[dict[str, str]] = [
        {
            "metric": "p0_exclusion_rows",
            "value": str(len(rows)),
            "notes": "Distinct source_file + capture_id rows excluded from future public-surface rebuilds.",
        },
        {
            "metric": "skipped_p0_rows_without_rebuild_key",
            "value": str(skipped_no_key),
            "notes": "P0 queue rows without source_file or capture_id; not actionable for rebuild exclusion.",
        },
        {
            "metric": "source_files_with_exclusions",
            "value": str(len(by_source_file)),
            "notes": "Capture record files affected by the exclusion list.",
        },
        {
            "metric": "candidate_delta_rows_added",
            "value": str(delta_rows_added),
            "notes": "Rows merged from prefreeze_candidate_exclusion_delta_v1.csv.",
        },
        {
            "metric": "candidate_delta_rows_already_present",
            "value": str(delta_rows_duplicate),
            "notes": "Candidate delta rows already covered by the P0 queue.",
        },
    ]
    for action, count in by_action.most_common():
        summary_rows.append({"metric": f"action:{action}", "value": str(count), "notes": "P0 exclusion action type."})
    for source_file, count in by_source_file.most_common(20):
        summary_rows.append({"metric": f"source_file:{source_file}", "value": str(count), "notes": "Top capture files by P0 exclusion rows."})

    rows.sort(key=lambda item: (item["source_file"], item["capture_id"]))
    return rows, summary_rows


def write_report(rows: list[dict[str, str]], summary_rows: list[dict[str, str]]) -> None:
    by_action = Counter(row["action_type"] for row in rows)
    by_file = Counter(row["source_file"] for row in rows)
    lines = [
        "# Pre-freeze Public Rebuild Exclusion v1",
        "",
        "Scope: non-destructive P0 exclusion table for future public-surface rebuilds. It does not delete capture records, mutate rights states, download images, or rebuild frontend payloads.",
        "",
        "## Summary",
        "",
    ]
    for row in summary_rows[:3]:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Action Counts", ""])
    for action, count in by_action.most_common():
        lines.append(f"- {action}: {count}")
    lines.extend(["", "## Top Source Files", ""])
    for source_file, count in by_file.most_common(15):
        lines.append(f"- {source_file}: {count}")
    lines.extend(
        [
            "",
            "## Rebuild Rule",
            "",
            "- `scripts/rebuild_public_surfaces_from_records.py` reads this exclusion table when present.",
            "- A matching `source_file + capture_id` row is skipped before dedupe and surface generation.",
            "- The raw capture row remains available for audit, card/support review, or later manual reinstatement.",
            "- Candidate duplicate-image deltas are merged only when `data/prefreeze_candidate_exclusion_delta_v1.csv` exists.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows, summary_rows = build_rows()
    write_csv(EXCLUSION, rows, EXCLUSION_FIELDS)
    write_csv(SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_report(rows, summary_rows)
    print(f"p0_exclusion_rows={len(rows)}")
    print(f"source_files={len({row['source_file'] for row in rows})}")
    print(f"wrote {EXCLUSION.relative_to(ROOT)}")
    print(f"wrote {SUMMARY.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
