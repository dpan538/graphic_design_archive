#!/usr/bin/env python3
"""Build a sandbox role-override layer from packet apply-ready rows.

This script does not mutate capture records or the canonical prefreeze role
override CSV. It creates a separate merged override file that can be passed to a
candidate rebuild for main/sub/text structure testing.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

BASE_OVERRIDES = DATA / "prefreeze_surface_role_overrides_v1.csv"
PACKET_APPLY_READY = DATA / "prefreeze_packet_role_apply_ready_v1.csv"

OUT_OVERRIDES = DATA / "prefreeze_surface_role_overrides_packet_applied_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_packet_role_applied_override_summary_v1.csv"
OUT_REPORT = DOCS / "PREFREEZE_PACKET_ROLE_APPLIED_OVERRIDES_v1.md"

FIELDS = [
    "source_file",
    "capture_id",
    "surface_id",
    "surface_disposition_override",
    "review_class",
    "decision_type",
    "confidence",
    "override_basis",
    "source_name",
    "title",
    "override_source",
    "packet_id",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]


def clean(value: object) -> str:
    return str(value or "").strip()


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


def key(row: dict[str, str]) -> tuple[str, str]:
    return (Path(clean(row.get("source_file"))).name, clean(row.get("capture_id")))


def base_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "source_file": Path(clean(row.get("source_file"))).name,
        "capture_id": clean(row.get("capture_id")),
        "surface_id": clean(row.get("surface_id")),
        "surface_disposition_override": clean(row.get("surface_disposition_override")),
        "review_class": clean(row.get("review_class")),
        "decision_type": clean(row.get("decision_type")),
        "confidence": clean(row.get("confidence")),
        "override_basis": clean(row.get("override_basis")),
        "source_name": clean(row.get("source_name")),
        "title": clean(row.get("title")),
        "override_source": "surface_role_override_v1",
        "packet_id": "",
    }


def packet_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "source_file": Path(clean(row.get("source_file"))).name,
        "capture_id": clean(row.get("capture_id")),
        "surface_id": clean(row.get("surface_id")),
        "surface_disposition_override": clean(row.get("surface_disposition_override")),
        "review_class": "packet_apply_ready_subsheet",
        "decision_type": "apply_packet_subsheet_demotion",
        "confidence": clean(row.get("review_confidence")) or "high",
        "override_basis": (
            "packet_apply_ready: "
            + clean(row.get("packet_id"))
            + "; "
            + clean(row.get("readiness_reason"))
        ),
        "source_name": clean(row.get("source_name")),
        "title": clean(row.get("title")),
        "override_source": "packet_role_apply_ready_v1",
        "packet_id": clean(row.get("packet_id")),
    }


def merged_rows() -> tuple[list[dict[str, str]], list[dict[str, str]], Counter[str]]:
    rows: list[dict[str, str]] = []
    collisions: list[dict[str, str]] = []
    source_counts: Counter[str] = Counter()
    seen: dict[tuple[str, str], dict[str, str]] = {}

    for raw in read_csv(BASE_OVERRIDES):
        row = base_row(raw)
        if not row["source_file"] or not row["capture_id"] or not row["surface_disposition_override"]:
            continue
        seen[key(row)] = row
        rows.append(row)
        source_counts[row["override_source"]] += 1

    for raw in read_csv(PACKET_APPLY_READY):
        row = packet_row(raw)
        row_key = key(row)
        if not row["source_file"] or not row["capture_id"] or row["surface_disposition_override"] != "support_packet_appendix_text":
            collisions.append({**row, "override_basis": "packet row failed applied-override shape check"})
            continue
        existing = seen.get(row_key)
        if existing:
            if existing["surface_disposition_override"] != row["surface_disposition_override"]:
                collisions.append(
                    {
                        **row,
                        "override_basis": (
                            "collision_with_existing_override: "
                            + existing["surface_disposition_override"]
                            + " from "
                            + existing["override_source"]
                        ),
                    }
                )
            continue
        seen[row_key] = row
        rows.append(row)
        source_counts[row["override_source"]] += 1

    rows.sort(key=lambda row: (row["source_file"], row["capture_id"], row["surface_id"]))
    collisions.sort(key=lambda row: (row["source_file"], row["capture_id"], row["surface_id"]))
    return rows, collisions, source_counts


def write_report(summary_rows: list[dict[str, object]]) -> None:
    lines = [
        "# Prefreeze Packet Role Applied Overrides v1",
        "",
        "Scope: sandbox role-override file for testing main/sub/text structure after packet apply-ready review.",
        "",
        "This pass does not mutate capture records, does not overwrite the canonical prefreeze role override file, does not download images, and does not change rights or image states.",
        "",
        "## Summary",
        "",
    ]
    for row in summary_rows:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(
        [
            "",
            "## Use",
            "",
            "- Use this merged override file only for candidate rebuild / structure audit.",
            "- Keep the canonical `prefreeze_surface_role_overrides_v1.csv` unchanged until the 200 packet rows pass sample review.",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows, collisions, source_counts = merged_rows()
    role_counts = Counter(row["surface_disposition_override"] for row in rows)
    summary_rows: list[dict[str, object]] = [
        {"metric": "base_override_rows", "value": len(read_csv(BASE_OVERRIDES)), "notes": "Canonical prefreeze surface-role override input rows."},
        {"metric": "packet_apply_ready_rows", "value": len(read_csv(PACKET_APPLY_READY)), "notes": "Packet role apply-ready rows considered."},
        {"metric": "merged_override_rows", "value": len(rows), "notes": "Rows written to sandbox merged override file."},
        {"metric": "collision_or_rejected_rows", "value": len(collisions), "notes": "Packet rows skipped because of duplicate/conflict/shape checks."},
    ]
    for source, count in source_counts.most_common():
        summary_rows.append({"metric": f"override_source:{source}", "value": count, "notes": "Merged override source distribution."})
    for role, count in role_counts.most_common():
        summary_rows.append({"metric": f"role:{role}", "value": count, "notes": "Merged override role distribution."})

    write_csv(OUT_OVERRIDES, rows, FIELDS)
    write_csv(OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_report(summary_rows)

    print(f"merged_override_rows={len(rows)}")
    print(f"collision_or_rejected_rows={len(collisions)}")
    print(f"wrote {OUT_OVERRIDES.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
