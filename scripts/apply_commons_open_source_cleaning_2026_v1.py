#!/usr/bin/env python3
"""Apply the Commons open-source cleaning quarantine.

This script removes non-release-ready rows identified by
`audit_commons_open_source_cleaning_2026_v1.py` from the recent Commons capture
CSV inputs, writes a quarantine CSV for auditability, and refreshes source
summary/manifest counts. It does not download images or alter rights states.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
AUDIT_CSV = DATA / "commons_open_source_cleaning_audit_2026_v1.csv"
QUARANTINE_CSV = DATA / "commons_open_source_cleaning_quarantine_2026_v1.csv"
MANIFEST = DATA / "capture_runs" / "capture_run_manifest_v1.csv"

BATCH_TO_SUMMARY = {
    "capture_batch_commons_open_category_tree_image_2026_v1_records.csv": (
        DATA / "capture_batch_commons_open_category_tree_image_2026_v1_records.csv",
        DATA / "capture_batch_commons_open_category_tree_image_2026_v1_source_summary.csv",
        "commons_open_category_tree_image_2026_v1",
        "Commons country category-tree open image capture; post-cleaned by commons_open_source_cleaning_2026_v1; no image binaries or raw payloads saved.",
    ),
    "capture_batch_commons_open_region_balance_image_2026_v3_records.csv": (
        DATA / "capture_batch_commons_open_region_balance_image_2026_v3_records.csv",
        DATA / "capture_batch_commons_open_region_balance_image_2026_v3_source_summary.csv",
        "commons_open_region_balance_image_2026_v3",
        "Large region-balanced Commons open image capture; post-cleaned by commons_open_source_cleaning_2026_v1; no image binaries or raw payloads saved.",
    ),
    "capture_batch_commons_open_authority_weighted_expansion_2026_v1_records.csv": (
        DATA / "capture_batch_commons_open_authority_weighted_expansion_2026_v1_records.csv",
        DATA / "capture_batch_commons_open_authority_weighted_expansion_2026_v1_source_summary.csv",
        "commons_open_authority_weighted_expansion_2026_v1",
        "Authority-weighted Commons open image capture; post-cleaned by commons_open_source_cleaning_2026_v1; no image binaries or raw payloads saved.",
    ),
    "capture_batch_commons_open_controlled_expansion_2026_v1_records.csv": (
        DATA / "capture_batch_commons_open_controlled_expansion_2026_v1_records.csv",
        DATA / "capture_batch_commons_open_controlled_expansion_2026_v1_source_summary.csv",
        "commons_open_controlled_expansion_2026_v1",
        "Controlled Commons open image capture; post-cleaned by commons_open_source_cleaning_2026_v1; no image binaries or raw payloads saved.",
    ),
    "capture_batch_commons_open_publication_category_tree_2026_v1_records.csv": (
        DATA / "capture_batch_commons_open_publication_category_tree_2026_v1_records.csv",
        DATA / "capture_batch_commons_open_publication_category_tree_2026_v1_source_summary.csv",
        "commons_open_publication_category_tree_2026_v1",
        "Commons publication category-tree open image capture; post-cleaned by commons_open_source_cleaning_2026_v1; no image binaries or raw payloads saved.",
    ),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def summary_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_source: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_source.setdefault(row.get("source_name", ""), []).append(row)
    out: list[dict[str, str]] = []
    for source, items in sorted(by_source.items()):
        states = Counter(row.get("image_presence_code", "UNKNOWN") or "UNKNOWN" for row in items)
        out.append(
            {
                "source_name": source,
                "captured_records": str(len(items)),
                "image_states": ";".join(f"{state}:{count}" for state, count in sorted(states.items())),
                "notes": "Commons open-license metadata; post-cleaned release-ready row set; no image binary downloaded",
            }
        )
    return out


def update_manifest_for_batch(batch_file: str, rows: list[dict[str, str]]) -> None:
    if batch_file not in BATCH_TO_SUMMARY:
        return
    records_path, summary_path, run_id, notes = BATCH_TO_SUMMARY[batch_file]
    manifest_rows = read_csv(MANIFEST)
    fields = list(manifest_rows[0].keys()) if manifest_rows else [
        "run_id",
        "records_csv",
        "records_count",
        "active_source_count",
        "image_state_counts",
        "summary_csv",
        "summary_exists",
        "report_md",
        "report_exists",
        "raw_dir",
        "raw_dir_exists",
        "raw_commit_policy",
        "included_in_public_rebuild",
        "stage",
        "notes",
    ]
    states = Counter(row.get("image_presence_code", "UNKNOWN") or "UNKNOWN" for row in rows)
    active_sources = len({row.get("source_name", "") for row in rows if row.get("source_name", "")})
    image_state_counts = ";".join(f"{state}:{count}" for state, count in sorted(states.items()))
    for row in manifest_rows:
        if row.get("run_id") == run_id:
            row["records_count"] = str(len(rows))
            row["active_source_count"] = str(active_sources)
            row["image_state_counts"] = image_state_counts
            row["summary_csv"] = str(summary_path.relative_to(ROOT))
            row["summary_exists"] = "true"
            row["included_in_public_rebuild"] = "true" if rows else "false"
            row["stage"] = "item_image_capture" if rows else "empty_or_pending"
            row["notes"] = notes
            break
    else:
        manifest_rows.append(
            {
                "run_id": run_id,
                "records_csv": str(records_path.relative_to(ROOT)),
                "records_count": str(len(rows)),
                "active_source_count": str(active_sources),
                "image_state_counts": image_state_counts,
                "summary_csv": str(summary_path.relative_to(ROOT)),
                "summary_exists": "true",
                "report_md": "",
                "report_exists": "false",
                "raw_dir": "",
                "raw_dir_exists": "false",
                "raw_commit_policy": "not_present",
                "included_in_public_rebuild": "true" if rows else "false",
                "stage": "item_image_capture" if rows else "empty_or_pending",
                "notes": notes,
            }
        )
    write_csv(MANIFEST, manifest_rows, fields)


def main() -> None:
    audit_rows = read_csv(AUDIT_CSV)
    quarantine = [row for row in audit_rows if row.get("release_cleaning_status") != "release_ready"]
    write_csv(QUARANTINE_CSV, quarantine, list(audit_rows[0].keys()) if audit_rows else [])

    by_batch: dict[str, set[str]] = {}
    for row in quarantine:
        by_batch.setdefault(row.get("batch_file", ""), set()).add(row.get("capture_id", ""))

    total_removed = 0
    for batch_file, capture_ids in by_batch.items():
        if batch_file not in BATCH_TO_SUMMARY:
            continue
        records_path, summary_path, _run_id, _notes = BATCH_TO_SUMMARY[batch_file]
        rows = read_csv(records_path)
        fields = list(rows[0].keys()) if rows else []
        kept = [row for row in rows if row.get("capture_id") not in capture_ids]
        removed = len(rows) - len(kept)
        total_removed += removed
        write_csv(records_path, kept, fields)
        write_csv(summary_path, summary_rows(kept), ["source_name", "captured_records", "image_states", "notes"])
        update_manifest_for_batch(batch_file, kept)
        print(f"{batch_file}: removed={removed} kept={len(kept)}")

    for batch_file, (records_path, summary_path, _run_id, _notes) in BATCH_TO_SUMMARY.items():
        if batch_file in by_batch:
            continue
        rows = read_csv(records_path)
        if not rows:
            continue
        write_csv(summary_path, summary_rows(rows), ["source_name", "captured_records", "image_states", "notes"])
        update_manifest_for_batch(batch_file, rows)

    print(f"quarantined_records={len(quarantine)}")
    print(f"removed_records={total_removed}")
    print(f"quarantine_csv={QUARANTINE_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
