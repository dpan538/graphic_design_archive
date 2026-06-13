#!/usr/bin/env python3
"""Dry-run a controlled LOC manual IMG03 capture-record patch.

The script plans field-level changes for the 20 LOC manual rebuild candidates
but does not write to source capture CSVs. It is a pre-apply audit used before a
future rebuild pass.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from lib.archive_audit import DATA, DOCS, ROOT, clean, read_csv, write_csv


QUEUE = DATA / "loc_manual_img03_rebuild_queue_v1.csv"
OUTPUT_PLAN = DATA / "loc_manual_img03_apply_dry_run_v1.csv"
OUTPUT_SUMMARY = DATA / "loc_manual_img03_apply_dry_run_summary_v1.csv"
OUTPUT_REPORT = DOCS / "LOC_MANUAL_IMG03_APPLY_DRY_RUN_v1.md"

PLAN_FIELDS = [
    "surface_id",
    "local_record_file",
    "local_capture_id",
    "source_record_id",
    "record_found",
    "current_image_presence_code",
    "planned_image_presence_code",
    "current_image_url_detected",
    "planned_image_url_detected",
    "current_source_rights_text",
    "planned_source_rights_text",
    "planned_rights_review_required",
    "planned_image_frame_behavior",
    "planned_image_state_confidence",
    "dry_run_status",
    "notes",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]


def read_records(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader], list(reader.fieldnames or [])


def planned_rights_text(queue_row: dict[str, str]) -> str:
    text = queue_row.get("rights_text_excerpt", "")
    return clean(f"Library of Congress item rights/advisory text: {text}")


def build_plan() -> list[dict[str, str]]:
    rows_by_file: dict[str, tuple[list[dict[str, str]], list[str]]] = {}
    plan: list[dict[str, str]] = []
    for queue_row in read_csv(QUEUE):
        rel_path = queue_row.get("local_record_file", "")
        record_path = ROOT / rel_path
        if rel_path not in rows_by_file:
            rows_by_file[rel_path] = read_records(record_path)
        records, _fields = rows_by_file[rel_path]
        capture_id = queue_row.get("local_capture_id", "")
        record = next((row for row in records if row.get("capture_id") == capture_id), None)
        image_url = queue_row.get("source_image_url", "")
        rights_text = planned_rights_text(queue_row)
        current_state = record.get("image_presence_code", "") if record else ""
        dry_status = "ready_for_manual_apply" if record and current_state == "IMG01" and image_url and rights_text else "blocked_review_required"
        plan.append(
            {
                "surface_id": queue_row.get("surface_id", ""),
                "local_record_file": rel_path,
                "local_capture_id": capture_id,
                "source_record_id": queue_row.get("source_record_id", ""),
                "record_found": str(record is not None).lower(),
                "current_image_presence_code": current_state,
                "planned_image_presence_code": "IMG03",
                "current_image_url_detected": record.get("image_url_detected", "") if record else "",
                "planned_image_url_detected": image_url,
                "current_source_rights_text": record.get("source_rights_text", "") if record else "",
                "planned_source_rights_text": rights_text,
                "planned_rights_review_required": "true",
                "planned_image_frame_behavior": "open_image_frame",
                "planned_image_state_confidence": "high",
                "dry_run_status": dry_status,
                "notes": "Dry-run only. Future apply must patch capture records and rebuild surfaces before metrics change.",
            }
        )
    return plan


def write_summary(plan: list[dict[str, str]]) -> list[dict[str, str]]:
    status_counts = Counter(row["dry_run_status"] for row in plan)
    by_file = Counter(row["local_record_file"] for row in plan)
    current_states = Counter(row["current_image_presence_code"] for row in plan)
    summary = [
        {"metric": "planned_rows", "value": str(len(plan)), "notes": "Rows in dry-run patch plan."},
        {"metric": "ready_for_manual_apply_rows", "value": str(status_counts.get("ready_for_manual_apply", 0)), "notes": "Rows with matching capture id, IMG01 current state, image URL, and rights text."},
        {"metric": "blocked_review_required_rows", "value": str(status_counts.get("blocked_review_required", 0)), "notes": "Rows not ready for controlled apply."},
        {"metric": "automatic_upgrade_allowed_rows", "value": "0", "notes": "Dry-run only; no writes performed."},
    ]
    for key, value in by_file.most_common():
        summary.append({"metric": f"target_file_{key}", "value": str(value), "notes": "Target capture CSV for future apply."})
    for key, value in current_states.most_common():
        summary.append({"metric": f"current_image_state_{key}", "value": str(value), "notes": "Current image state in target capture records."})
    write_csv(OUTPUT_SUMMARY, summary, SUMMARY_FIELDS)
    return summary


def write_report(plan: list[dict[str, str]], summary: list[dict[str, str]]) -> None:
    metrics = {row["metric"]: row["value"] for row in summary}
    lines = [
        "# LOC Manual IMG03 Apply Dry Run v1",
        "",
        "This dry-run plans a controlled capture-record patch for LOC manual IMG03 candidates. It does not write target CSVs, rebuild surfaces, download images, or change archive metrics.",
        "",
        "## Summary",
        "",
        f"- planned rows: {metrics.get('planned_rows', '0')}",
        f"- ready for manual apply: {metrics.get('ready_for_manual_apply_rows', '0')}",
        f"- blocked/review required: {metrics.get('blocked_review_required_rows', '0')}",
        f"- automatic upgrades allowed: {metrics.get('automatic_upgrade_allowed_rows', '0')}",
        "",
        "## Planned Field Changes",
        "",
        "- `image_presence_code`: IMG01 -> IMG03",
        "- `image_frame_behavior`: open_image_frame",
        "- `image_state_confidence`: high",
        "- `source_rights_text` / `rights_basis`: LOC item rights/advisory text",
        "- `image_url_detected`: LOC source-hosted image URL",
        "- `iiif_or_viewer_available`: source record URL should remain visible in a future apply pass",
        "",
        "## Boundary",
        "",
        "- No capture records were changed in this pass.",
        "- No public payload or frontend data was rebuilt.",
        "- This is not a substitute for the future apply/rebuild audit.",
        "",
        "## Output Files",
        "",
        f"- `{OUTPUT_PLAN.relative_to(ROOT)}`",
        f"- `{OUTPUT_SUMMARY.relative_to(ROOT)}`",
    ]
    OUTPUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    plan = build_plan()
    write_csv(OUTPUT_PLAN, plan, PLAN_FIELDS)
    summary = write_summary(plan)
    write_report(plan, summary)
    metrics = {row["metric"]: row["value"] for row in summary}
    print(f"planned_rows={metrics.get('planned_rows', '0')}")
    print(f"ready_for_manual_apply_rows={metrics.get('ready_for_manual_apply_rows', '0')}")
    print(f"blocked_review_required_rows={metrics.get('blocked_review_required_rows', '0')}")
    print(f"automatic_upgrade_allowed_rows={metrics.get('automatic_upgrade_allowed_rows', '0')}")
    print(f"wrote {OUTPUT_PLAN.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
