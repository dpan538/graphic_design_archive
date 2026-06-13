#!/usr/bin/env python3
"""Plan or apply the reviewed LOC manual IMG03 capture-record repair.

Default mode is dry-run. Use --apply only after confirming the LOC item rights
evidence and preparing an isolated rebuild pass.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from lib.archive_audit import DATA, DOCS, ROOT, clean, read_csv, write_csv


QUEUE = DATA / "loc_manual_img03_rebuild_queue_v1.csv"
OUTPUT_PLAN = DATA / "loc_manual_img03_capture_apply_plan_v1.csv"
OUTPUT_SUMMARY = DATA / "loc_manual_img03_capture_apply_summary_v1.csv"
OUTPUT_REPORT = DOCS / "LOC_MANUAL_IMG03_CAPTURE_APPLY_PLAN_v1.md"

REQUIRED_COLUMNS = {
    "capture_id",
    "source_record_url",
    "source_rights_text",
    "rights_basis",
    "image_presence_code",
    "image_presence_basis",
    "image_state_evaluation",
    "image_state_confidence",
    "rights_review_required",
    "image_state_review_note",
    "image_frame_behavior",
    "image_url_detected",
    "local_copy_permitted",
    "iiif_or_viewer_available",
    "fallback_required",
    "fallback_reason",
}

PLAN_FIELDS = [
    "surface_id",
    "local_record_file",
    "local_capture_id",
    "source_record_id",
    "source_record_url",
    "current_image_presence_code",
    "planned_image_presence_code",
    "current_image_url_detected",
    "planned_image_url_detected",
    "current_rights_basis",
    "planned_rights_basis",
    "required_column_check",
    "record_status",
    "apply_status",
    "notes",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]


def read_records(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader], list(reader.fieldnames or [])


def write_records(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rights_text(queue_row: dict[str, str]) -> str:
    return clean(f"Library of Congress item rights/advisory text: {queue_row.get('rights_text_excerpt', '')}")


def rights_basis(queue_row: dict[str, str]) -> str:
    return clean(
        "Library of Congress item metadata exposes an item-level no-known-restrictions advisory "
        f"and a source-hosted image URL; source record retained for traceability: {queue_row.get('source_record_url', '')}"
    )


def planned_values(queue_row: dict[str, str]) -> dict[str, str]:
    basis = rights_basis(queue_row)
    return {
        "source_rights_text": rights_text(queue_row),
        "rights_basis": basis,
        "image_presence_code": "IMG03",
        "image_presence_basis": basis,
        "image_state_evaluation": "IMG03: LOC item metadata exposes item-level no-known-restrictions rights text and source-hosted image URL.",
        "image_state_confidence": "high",
        "rights_review_required": "true",
        "image_state_review_note": "Manual LOC rights repair candidate; no image binary downloaded; source-hosted image URL only.",
        "image_frame_behavior": "open_image_frame",
        "image_url_detected": clean(queue_row.get("source_image_url")),
        "local_copy_permitted": "false",
        "iiif_or_viewer_available": clean(queue_row.get("source_record_url")),
        "fallback_required": "false",
        "fallback_reason": "",
    }


def is_already_applied(record: dict[str, str], values: dict[str, str]) -> bool:
    return (
        clean(record.get("image_presence_code")) == "IMG03"
        and clean(record.get("image_url_detected")) == values["image_url_detected"]
        and clean(record.get("rights_basis")) == values["rights_basis"]
    )


def build_plan(rows_by_file: dict[str, tuple[list[dict[str, str]], list[str]]]) -> tuple[list[dict[str, str]], dict[tuple[str, str], dict[str, str]]]:
    patch_by_key: dict[tuple[str, str], dict[str, str]] = {}
    plan: list[dict[str, str]] = []
    for queue_row in read_csv(QUEUE):
        rel_path = clean(queue_row.get("local_record_file"))
        capture_id = clean(queue_row.get("local_capture_id"))
        record_path = ROOT / rel_path
        if rel_path not in rows_by_file:
            rows_by_file[rel_path] = read_records(record_path)
        records, fields = rows_by_file[rel_path]
        record = next((row for row in records if row.get("capture_id") == capture_id), None)
        missing_columns = sorted(REQUIRED_COLUMNS - set(fields))
        values = planned_values(queue_row)
        current_state = clean(record.get("image_presence_code")) if record else ""
        if missing_columns:
            record_status = "blocked_missing_columns"
        elif record is None:
            record_status = "blocked_record_not_found"
        elif current_state == "IMG01" and values["image_url_detected"] and values["source_rights_text"]:
            record_status = "ready_for_apply"
            patch_by_key[(rel_path, capture_id)] = values
        elif record and is_already_applied(record, values):
            record_status = "already_applied"
        else:
            record_status = "blocked_unexpected_current_state"
        plan.append(
            {
                "surface_id": clean(queue_row.get("surface_id")),
                "local_record_file": rel_path,
                "local_capture_id": capture_id,
                "source_record_id": clean(queue_row.get("source_record_id")),
                "source_record_url": clean(queue_row.get("source_record_url")),
                "current_image_presence_code": current_state,
                "planned_image_presence_code": values["image_presence_code"],
                "current_image_url_detected": clean(record.get("image_url_detected")) if record else "",
                "planned_image_url_detected": values["image_url_detected"],
                "current_rights_basis": clean(record.get("rights_basis")) if record else "",
                "planned_rights_basis": values["rights_basis"],
                "required_column_check": "ok" if not missing_columns else "; ".join(missing_columns),
                "record_status": record_status,
                "apply_status": "not_run",
                "notes": "Default dry-run. --apply writes capture CSVs but still requires a rebuild before public metrics change.",
            }
        )
    return plan, patch_by_key


def apply_patches(
    rows_by_file: dict[str, tuple[list[dict[str, str]], list[str]]],
    patch_by_key: dict[tuple[str, str], dict[str, str]],
) -> Counter[str]:
    applied = Counter()
    patches_by_file: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for (rel_path, capture_id), values in patch_by_key.items():
        patches_by_file[rel_path][capture_id] = values
    for rel_path, patches in patches_by_file.items():
        rows, fields = rows_by_file[rel_path]
        for row in rows:
            capture_id = row.get("capture_id", "")
            if capture_id not in patches:
                continue
            row.update(patches[capture_id])
            applied[rel_path] += 1
        write_records(ROOT / rel_path, rows, fields)
    return applied


def write_summary(plan: list[dict[str, str]], applied: Counter[str], did_apply: bool) -> list[dict[str, str]]:
    status_counts = Counter(row["record_status"] for row in plan)
    by_file = Counter(row["local_record_file"] for row in plan)
    summary = [
        {"metric": "mode", "value": "apply" if did_apply else "dry_run", "notes": "Script execution mode."},
        {"metric": "planned_rows", "value": str(len(plan)), "notes": "Rows from the LOC manual IMG03 rebuild queue."},
        {"metric": "ready_for_apply_rows", "value": str(status_counts.get("ready_for_apply", 0)), "notes": "Rows eligible for --apply."},
        {"metric": "already_applied_rows", "value": str(status_counts.get("already_applied", 0)), "notes": "Rows already matching planned IMG03 fields."},
        {"metric": "blocked_rows", "value": str(sum(v for k, v in status_counts.items() if k.startswith("blocked_"))), "notes": "Rows that must not be applied automatically."},
        {"metric": "capture_rows_written", "value": str(sum(applied.values())), "notes": "Rows actually written in --apply mode."},
        {"metric": "images_downloaded", "value": "0", "notes": "This repair writes metadata only and never downloads image binaries."},
        {"metric": "public_surfaces_rebuilt", "value": "false", "notes": "A separate rebuild must follow any future apply pass."},
    ]
    for key, value in by_file.most_common():
        summary.append({"metric": f"planned_target_file_{key}", "value": str(value), "notes": "Rows planned in this capture CSV."})
    for key, value in applied.most_common():
        summary.append({"metric": f"applied_target_file_{key}", "value": str(value), "notes": "Rows written in this capture CSV."})
    write_csv(OUTPUT_SUMMARY, summary, SUMMARY_FIELDS)
    return summary


def write_report(summary: list[dict[str, str]], did_apply: bool) -> None:
    metrics = {row["metric"]: row["value"] for row in summary}
    lines = [
        "# LOC Manual IMG03 Capture Apply Plan v1",
        "",
        "This script layer converts the reviewed LOC manual IMG03 queue into a controlled capture-record patch plan. Default execution is dry-run; target capture CSVs are written only with `--apply`.",
        "",
        "## Summary",
        "",
        f"- mode: {metrics.get('mode', 'dry_run')}",
        f"- planned rows: {metrics.get('planned_rows', '0')}",
        f"- ready for apply: {metrics.get('ready_for_apply_rows', '0')}",
        f"- blocked rows: {metrics.get('blocked_rows', '0')}",
        f"- capture rows written: {metrics.get('capture_rows_written', '0')}",
        f"- public surfaces rebuilt: {metrics.get('public_surfaces_rebuilt', 'false')}",
        "",
        "## Planned Capture Fields",
        "",
        "- `image_presence_code`: `IMG03`",
        "- `source_rights_text` and `rights_basis`: LOC item-level no-known-restrictions advisory",
        "- `image_url_detected`: LOC source-hosted image URL",
        "- `image_frame_behavior`: `open_image_frame`",
        "- `local_copy_permitted`: `false`",
        "- `iiif_or_viewer_available`: LOC item/source record URL",
        "",
        "## Boundary",
        "",
        "- No image files are downloaded.",
        "- No raw LOC payloads are saved.",
        "- No heuristic, LLM, TOS, or platform-family signal upgrades are allowed.",
        "- Public metrics change only after a later isolated rebuild/audit pass.",
        "",
        "## Execution Note",
        "",
        "This run wrote target capture CSVs." if did_apply else "This run did not write target capture CSVs.",
        "",
        "## Output Files",
        "",
        f"- `{OUTPUT_PLAN.relative_to(ROOT)}`",
        f"- `{OUTPUT_SUMMARY.relative_to(ROOT)}`",
    ]
    OUTPUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan or apply reviewed LOC manual IMG03 capture-record repairs.")
    parser.add_argument("--apply", action="store_true", help="Write eligible patches into target capture CSVs.")
    parser.add_argument(
        "--confirm-item-rights-reviewed",
        action="store_true",
        help="Required with --apply to acknowledge item-level LOC rights evidence was reviewed.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.apply and not args.confirm_item_rights_reviewed:
        raise SystemExit("--apply requires --confirm-item-rights-reviewed")
    rows_by_file: dict[str, tuple[list[dict[str, str]], list[str]]] = {}
    plan, patch_by_key = build_plan(rows_by_file)
    blocked = [row for row in plan if row["record_status"].startswith("blocked_")]
    did_apply = False
    applied: Counter[str] = Counter()
    if args.apply:
        if blocked:
            raise SystemExit(f"Refusing apply: {len(blocked)} blocked row(s) in plan.")
        applied = apply_patches(rows_by_file, patch_by_key)
        did_apply = True
        for row in plan:
            if row["record_status"] == "ready_for_apply":
                row["apply_status"] = "applied"
    write_csv(OUTPUT_PLAN, plan, PLAN_FIELDS)
    summary = write_summary(plan, applied, did_apply)
    write_report(summary, did_apply)
    metrics = {row["metric"]: row["value"] for row in summary}
    print(f"mode={metrics.get('mode', 'dry_run')}")
    print(f"planned_rows={metrics.get('planned_rows', '0')}")
    print(f"ready_for_apply_rows={metrics.get('ready_for_apply_rows', '0')}")
    print(f"blocked_rows={metrics.get('blocked_rows', '0')}")
    print(f"capture_rows_written={metrics.get('capture_rows_written', '0')}")
    print(f"wrote {OUTPUT_PLAN.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
