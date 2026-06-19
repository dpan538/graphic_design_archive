#!/usr/bin/env python3
"""Generate a manifest for capture batches and their archive inclusion state.

The manifest is a run ledger, not a release approval. It records which capture
CSV files exist, whether they are currently included by the public-surface
rebuild script, and whether nearby summary/report/raw outputs exist. Raw dirs
are listed for traceability but are never marked as commit-safe by this script.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from lib.archive_audit import DATA, DOCS, ROOT, read_csv, record_image_state, record_source_key, write_csv


OUT_DIR = DATA / "capture_runs"
MANIFEST = OUT_DIR / "capture_run_manifest_v1.csv"
REPORT = DOCS / "CAPTURE_RUN_MANIFEST_v1.md"
REBUILD_SCRIPT = ROOT / "scripts" / "rebuild_public_surfaces_from_records.py"

FIELDS = [
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


def clean_run_id(path: Path) -> str:
    stem = path.stem
    stem = re.sub(r"^capture_batch_", "", stem)
    stem = re.sub(r"_records$", "", stem)
    return stem


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def rebuild_references() -> set[str]:
    if not REBUILD_SCRIPT.exists():
        return set()
    text = REBUILD_SCRIPT.read_text(encoding="utf-8")
    return set(re.findall(r"capture_batch_[A-Za-z0-9_]+_records\.csv", text))


def report_candidates(run_id: str) -> list[Path]:
    report_key = re.sub(r"[^A-Za-z0-9]+", "_", run_id).strip("_").upper()
    words = [word for word in report_key.split("_") if word]
    if not words:
        return []
    candidates: list[Path] = []
    for path in DOCS.glob("*.md"):
        name = path.stem.upper()
        if all(word in name for word in words[: min(4, len(words))]):
            candidates.append(path)
    return sorted(candidates)


def infer_stage(records_path: Path, included: bool, records_count: int) -> str:
    name = records_path.name.lower()
    if records_count == 0:
        return "empty_or_pending"
    if "source_profiles" in name or "edge_source_registry_context" in name:
        return "source_profile_or_context"
    if "item_image" in name or "image_ready" in name or "open_image" in name:
        return "item_image_capture"
    if included:
        return "public_surface_rebuild_input"
    return "capture_records_unclassified"


def build_rows() -> list[dict[str, str]]:
    referenced = rebuild_references()
    rows: list[dict[str, str]] = []
    for records_path in sorted(DATA.glob("capture_batch_*_records.csv")):
        run_id = clean_run_id(records_path)
        records = read_csv(records_path)
        sources = {record_source_key(row) for row in records if record_source_key(row)}
        state_counts = Counter(record_image_state(row) for row in records)
        summary_path = records_path.with_name(records_path.name.replace("_records.csv", "_source_summary.csv"))
        raw_dir = records_path.with_name(records_path.name.replace("_records.csv", "_raw"))
        reports = report_candidates(run_id)
        included = records_path.name in referenced
        rows.append(
            {
                "run_id": run_id,
                "records_csv": relative(records_path),
                "records_count": str(len(records)),
                "active_source_count": str(len(sources)),
                "image_state_counts": ";".join(f"{key}:{state_counts[key]}" for key in sorted(state_counts)),
                "summary_csv": relative(summary_path) if summary_path.exists() else "",
                "summary_exists": str(summary_path.exists()).lower(),
                "report_md": relative(reports[0]) if reports else "",
                "report_exists": str(bool(reports)).lower(),
                "raw_dir": relative(raw_dir) if raw_dir.exists() else "",
                "raw_dir_exists": str(raw_dir.exists()).lower(),
                "raw_commit_policy": "do_not_commit_without_redaction_review" if raw_dir.exists() else "not_present",
                "included_in_public_rebuild": str(included).lower(),
                "stage": infer_stage(records_path, included, len(records)),
                "notes": "Manifest row only; archive success still requires public payload inclusion and release audit.",
            }
        )
    return rows


def write_report(rows: list[dict[str, str]]) -> None:
    included = [row for row in rows if row["included_in_public_rebuild"] == "true"]
    not_included = [row for row in rows if row["included_in_public_rebuild"] != "true"]
    stage_counts = Counter(row["stage"] for row in rows)
    raw_count = sum(1 for row in rows if row["raw_dir_exists"] == "true")
    lines = [
        "# Capture Run Manifest v1",
        "",
        "Scope: capture-batch ledger for source records and public-surface rebuild inclusion. This report does not approve rights or publication status.",
        "",
        "## Summary",
        "",
        f"- Capture record files: {len(rows)}",
        f"- Included in public rebuild script: {len(included)}",
        f"- Not yet included in public rebuild script: {len(not_included)}",
        f"- Raw directories present: {raw_count}",
        "",
        "## Stage Counts",
        "",
    ]
    for stage, count in stage_counts.most_common():
        lines.append(f"- {stage}: {count}")
    lines.extend(["", "## Not Yet Included", ""])
    for row in not_included[:40]:
        lines.append(f"- {row['run_id']} · records={row['records_count']} · sources={row['active_source_count']}")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Raw dirs are treated as non-commit-safe unless separately redacted and reviewed.",
            "- This manifest distinguishes capture records from archive-success sources.",
            "- Public-surface success must be audited after rebuild, not inferred from probe or capture output alone.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(MANIFEST, rows, FIELDS)
    write_report(rows)
    print(f"capture_record_files={len(rows)}")
    print(f"included_in_public_rebuild={sum(1 for row in rows if row['included_in_public_rebuild'] == 'true')}")
    print(f"not_included={sum(1 for row in rows if row['included_in_public_rebuild'] != 'true')}")
    print(f"wrote {MANIFEST.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
