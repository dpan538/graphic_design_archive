#!/usr/bin/env python3
"""Audit the applied LOC manual IMG03 capture-record repair."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from lib.archive_audit import DATA, DOCS, ROOT, clean, read_csv, write_csv


QUEUE = DATA / "loc_manual_img03_rebuild_queue_v1.csv"
OUTPUT = DATA / "loc_manual_img03_apply_postcheck_v1.csv"
SUMMARY = DATA / "loc_manual_img03_apply_postcheck_summary_v1.csv"
REPORT = DOCS / "LOC_MANUAL_IMG03_APPLY_POSTCHECK_v1.md"

FIELDS = [
    "surface_id",
    "local_record_file",
    "local_capture_id",
    "source_record_id",
    "record_found",
    "image_presence_code",
    "image_url_match",
    "rights_text_present",
    "rights_basis_present",
    "source_record_visible",
    "local_copy_permitted",
    "image_frame_behavior",
    "postcheck_status",
    "notes",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]


def read_records(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def yes(value: bool) -> str:
    return str(value).lower()


def check_row(queue_row: dict[str, str], record: dict[str, str] | None) -> dict[str, str]:
    expected_url = clean(queue_row.get("source_image_url"))
    source_url = clean(queue_row.get("source_record_url"))
    if record is None:
        return {
            "surface_id": clean(queue_row.get("surface_id")),
            "local_record_file": clean(queue_row.get("local_record_file")),
            "local_capture_id": clean(queue_row.get("local_capture_id")),
            "source_record_id": clean(queue_row.get("source_record_id")),
            "record_found": "false",
            "postcheck_status": "fail_record_not_found",
            "notes": "Capture row missing after apply.",
        }
    checks = {
        "state": clean(record.get("image_presence_code")) == "IMG03",
        "url": clean(record.get("image_url_detected")) == expected_url,
        "rights_text": "No known restrictions on publication" in clean(record.get("source_rights_text")),
        "rights_basis": "Library of Congress item metadata" in clean(record.get("rights_basis")),
        "source_visible": clean(record.get("iiif_or_viewer_available")) == source_url,
        "local_copy": clean(record.get("local_copy_permitted")).lower() == "false",
        "frame": clean(record.get("image_frame_behavior")) == "open_image_frame",
    }
    status = "pass" if all(checks.values()) else "fail_field_contract"
    failed = ", ".join(key for key, value in checks.items() if not value)
    return {
        "surface_id": clean(queue_row.get("surface_id")),
        "local_record_file": clean(queue_row.get("local_record_file")),
        "local_capture_id": clean(queue_row.get("local_capture_id")),
        "source_record_id": clean(queue_row.get("source_record_id")),
        "record_found": "true",
        "image_presence_code": clean(record.get("image_presence_code")),
        "image_url_match": yes(checks["url"]),
        "rights_text_present": yes(checks["rights_text"]),
        "rights_basis_present": yes(checks["rights_basis"]),
        "source_record_visible": yes(checks["source_visible"]),
        "local_copy_permitted": clean(record.get("local_copy_permitted")),
        "image_frame_behavior": clean(record.get("image_frame_behavior")),
        "postcheck_status": status,
        "notes": "All LOC IMG03 apply fields match." if status == "pass" else f"Failed checks: {failed}",
    }


def build_audit() -> list[dict[str, str]]:
    rows_by_file: dict[str, list[dict[str, str]]] = {}
    audit_rows: list[dict[str, str]] = []
    for queue_row in read_csv(QUEUE):
        rel_path = clean(queue_row.get("local_record_file"))
        capture_id = clean(queue_row.get("local_capture_id"))
        if rel_path not in rows_by_file:
            rows_by_file[rel_path] = read_records(ROOT / rel_path)
        record = next((row for row in rows_by_file[rel_path] if row.get("capture_id") == capture_id), None)
        audit_rows.append(check_row(queue_row, record))
    return audit_rows


def write_summary(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    statuses = Counter(row.get("postcheck_status", "") for row in rows)
    by_file = Counter(row.get("local_record_file", "") for row in rows)
    image_states = Counter(row.get("image_presence_code", "") for row in rows)
    summary = [
        {"metric": "checked_rows", "value": str(len(rows)), "notes": "Rows checked from LOC manual IMG03 rebuild queue."},
        {"metric": "pass_rows", "value": str(statuses.get("pass", 0)), "notes": "Rows matching the post-apply field contract."},
        {"metric": "fail_rows", "value": str(sum(value for key, value in statuses.items() if key.startswith("fail"))), "notes": "Rows that need review before rebuild."},
        {"metric": "images_downloaded", "value": "0", "notes": "Postcheck only; no image binaries are downloaded."},
        {"metric": "public_surfaces_rebuilt", "value": "false", "notes": "Postcheck does not rebuild generated public payloads or frontend mirrors."},
    ]
    for key, value in by_file.most_common():
        summary.append({"metric": f"checked_file_{key}", "value": str(value), "notes": "Rows checked in this target capture CSV."})
    for key, value in image_states.most_common():
        summary.append({"metric": f"post_apply_image_state_{key or 'missing'}", "value": str(value), "notes": "Image state after controlled apply."})
    write_csv(SUMMARY, summary, SUMMARY_FIELDS)
    return summary


def write_report(summary: list[dict[str, str]]) -> None:
    metrics = {row["metric"]: row["value"] for row in summary}
    lines = [
        "# LOC Manual IMG03 Apply Postcheck v1",
        "",
        "This audit verifies the capture-record state after the controlled LOC manual IMG03 apply pass. It does not rebuild public surfaces or frontend payloads.",
        "",
        "## Summary",
        "",
        f"- checked rows: {metrics.get('checked_rows', '0')}",
        f"- pass rows: {metrics.get('pass_rows', '0')}",
        f"- fail rows: {metrics.get('fail_rows', '0')}",
        f"- images downloaded: {metrics.get('images_downloaded', '0')}",
        f"- public surfaces rebuilt: {metrics.get('public_surfaces_rebuilt', 'false')}",
        "",
        "## Contract Checked",
        "",
        "- target capture row exists",
        "- `image_presence_code == IMG03`",
        "- `image_url_detected` matches the LOC source-hosted image URL",
        "- `source_rights_text` carries the LOC item rights/advisory text",
        "- `rights_basis` identifies item-level LOC metadata",
        "- `iiif_or_viewer_available` points back to the LOC item/source record",
        "- `local_copy_permitted == false`",
        "- `image_frame_behavior == open_image_frame`",
        "",
        "## Boundary",
        "",
        "- No image binaries were downloaded.",
        "- No raw LOC payloads were saved.",
        "- No public surfaces or frontend data were rebuilt.",
        "- Public release metrics remain unchanged until a later rebuild/audit pass.",
        "",
        "## Output Files",
        "",
        f"- `{OUTPUT.relative_to(ROOT)}`",
        f"- `{SUMMARY.relative_to(ROOT)}`",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_audit()
    write_csv(OUTPUT, rows, FIELDS)
    summary = write_summary(rows)
    write_report(summary)
    metrics = {row["metric"]: row["value"] for row in summary}
    print(f"checked_rows={metrics.get('checked_rows', '0')}")
    print(f"pass_rows={metrics.get('pass_rows', '0')}")
    print(f"fail_rows={metrics.get('fail_rows', '0')}")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    print(f"wrote {SUMMARY.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
