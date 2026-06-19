#!/usr/bin/env python3
"""Audit source success by pipeline stage.

Project rule: a source is archive-active only after item/source capture has
been rebuilt into public surfaces. Probe success and pre-surface registry
success remain useful planning signals, but they do not count as final archive
success on their own.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from lib.archive_audit import (
    DATA,
    DOCS,
    ROOT,
    capture_record_files,
    clean,
    object_groups,
    read_csv,
    read_payload,
    record_image_state,
    record_source_key,
    surface_image_state,
    surface_is_source_visible,
    surface_is_verified_open,
    write_csv,
)


SUMMARY = DATA / "active_source_success_summary_v1.csv"
SOURCE_ROWS = DATA / "active_source_success_sources_v1.csv"
REPORT = DOCS / "ACTIVE_SOURCE_SUCCESS_AUDIT_v1.md"

SUMMARY_FIELDS = ["metric", "value", "notes"]
SOURCE_FIELDS = [
    "source_name",
    "success_stage",
    "pre_surface_registry_count",
    "capture_record_count",
    "public_surface_count",
    "object_count",
    "source_visible_object_count",
    "verified_open_object_count",
    "surface_image_state_counts",
    "record_image_state_counts",
    "record_files",
    "notes",
]


def registry_sources() -> Counter[str]:
    sources: Counter[str] = Counter()
    for path in sorted(DATA.glob("nonmainstream_source_success_registry_2026_v*.csv")):
        for row in read_csv(path):
            if clean(row.get("source_success_status")) == "success":
                key = clean(row.get("source_name")) or clean(row.get("final_url") or row.get("url"))
                if key:
                    sources[key] += 1
    return sources


def capture_sources() -> tuple[dict[str, list[dict[str, str]]], dict[str, set[str]]]:
    rows_by_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    files_by_source: dict[str, set[str]] = defaultdict(set)
    for path in capture_record_files():
        if "cell_assignments" in path.name:
            continue
        for row in read_csv(path):
            source = record_source_key(row)
            if not source:
                continue
            rows_by_source[source].append(row)
            files_by_source[source].add(str(path.relative_to(ROOT)))
    return rows_by_source, files_by_source


def surface_sources(surfaces: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for surface in surfaces:
        source = clean(surface.get("sourceName")) or clean(surface.get("sourceUrl"))
        if source:
            out[source].append(surface)
    return out


def counter_string(counter: Counter[str]) -> str:
    return ";".join(f"{key}:{counter[key]}" for key in sorted(counter) if key)


def source_stage(pre_count: int, capture_count: int, surface_count: int) -> str:
    if surface_count:
        return "archive_active_public_surface"
    if capture_count:
        return "captured_not_public_surface"
    if pre_count:
        return "pre_surface_only"
    return "unknown"


def build_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    payload = read_payload()
    surfaces = payload.get("surfaces", [])
    pre_sources = registry_sources()
    capture_by_source, files_by_source = capture_sources()
    public_by_source = surface_sources(surfaces)
    all_sources = sorted(set(pre_sources) | set(capture_by_source) | set(public_by_source))

    source_rows: list[dict[str, str]] = []
    for source in all_sources:
        capture_rows = capture_by_source.get(source, [])
        public_rows = public_by_source.get(source, [])
        groups = object_groups(public_rows)
        source_visible_objects = sum(
            1 for group in groups.values() if any(surface_is_source_visible(surface) for surface in group)
        )
        verified_open_objects = sum(
            1 for group in groups.values() if any(surface_is_verified_open(surface) for surface in group)
        )
        surface_states = Counter(surface_image_state(surface) for surface in public_rows)
        record_states = Counter(record_image_state(row) for row in capture_rows)
        stage = source_stage(pre_sources.get(source, 0), len(capture_rows), len(public_rows))
        source_rows.append(
            {
                "source_name": source,
                "success_stage": stage,
                "pre_surface_registry_count": str(pre_sources.get(source, 0)),
                "capture_record_count": str(len(capture_rows)),
                "public_surface_count": str(len(public_rows)),
                "object_count": str(len(groups)),
                "source_visible_object_count": str(source_visible_objects),
                "verified_open_object_count": str(verified_open_objects),
                "surface_image_state_counts": counter_string(surface_states),
                "record_image_state_counts": counter_string(record_states),
                "record_files": ";".join(sorted(files_by_source.get(source, set()))[:8]),
                "notes": "Archive-active only when public_surface_count > 0.",
            }
        )

    stage_counts = Counter(row["success_stage"] for row in source_rows)
    public_sources = [row for row in source_rows if row["success_stage"] == "archive_active_public_surface"]
    captured_not_public = [row for row in source_rows if row["success_stage"] == "captured_not_public_surface"]
    pre_only = [row for row in source_rows if row["success_stage"] == "pre_surface_only"]
    total_public_surfaces = sum(int(row["public_surface_count"]) for row in source_rows)
    global_groups = object_groups(surfaces)
    total_objects = len(global_groups)
    total_visible_objects = sum(
        1 for group in global_groups.values() if any(surface_is_source_visible(surface) for surface in group)
    )
    total_verified_open_objects = sum(
        1 for group in global_groups.values() if any(surface_is_verified_open(surface) for surface in group)
    )
    summary_rows = [
        {"metric": "source_rows_total", "value": str(len(source_rows)), "notes": "Distinct source_name/source key across pre-surface, capture records, and public surfaces."},
        {"metric": "archive_active_public_sources", "value": str(len(public_sources)), "notes": "Sources represented in generated public surfaces."},
        {"metric": "captured_not_public_sources", "value": str(len(captured_not_public)), "notes": "Sources with capture records but no generated public surface yet."},
        {"metric": "pre_surface_only_sources", "value": str(len(pre_only)), "notes": "Reachable source leads only; not archive-success sources."},
        {"metric": "public_surface_count", "value": str(total_public_surfaces), "notes": "Generated public surfaces grouped by source."},
        {"metric": "public_object_count", "value": str(total_objects), "notes": "Object-level grouping dedupes repeated views/photos."},
        {"metric": "source_visible_object_count", "value": str(total_visible_objects), "notes": "Objects with IMG01/IMG02/IMG03."},
        {"metric": "verified_open_object_count", "value": str(total_verified_open_objects), "notes": "Objects with reviewed IMG03."},
    ]
    for stage, count in stage_counts.most_common():
        summary_rows.append({"metric": f"stage_count:{stage}", "value": str(count), "notes": "Pipeline stage distribution."})
    return summary_rows, source_rows


def write_report(summary_rows: list[dict[str, str]], source_rows: list[dict[str, str]]) -> None:
    stage_counts = Counter(row["success_stage"] for row in source_rows)
    captured_not_public = [
        row for row in source_rows
        if row["success_stage"] == "captured_not_public_surface"
    ][:40]
    pre_only = [row for row in source_rows if row["success_stage"] == "pre_surface_only"][:25]
    lines = [
        "# Active Source Success Audit v1",
        "",
        "Scope: pipeline-stage audit for source success. A source counts as archive-active only when it appears in the generated public-surface payload.",
        "",
        "## Summary",
        "",
    ]
    for row in summary_rows:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Stage Counts", ""])
    for stage, count in stage_counts.most_common():
        lines.append(f"- {stage}: {count}")
    lines.extend(["", "## Captured But Not Public", ""])
    for row in captured_not_public:
        lines.append(f"- {row['source_name']} · records={row['capture_record_count']} · states={row['record_image_state_counts']}")
    lines.extend(["", "## Pre-surface Only Examples", ""])
    for row in pre_only:
        lines.append(f"- {row['source_name']}")
    lines.extend(
        [
            "",
            "## Rule",
            "",
            "- Probe success does not equal archive success.",
            "- Pre-surface source registry success does not equal archive success.",
            "- Capture records become archive-active only after rebuild and public payload audit.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    summary_rows, source_rows = build_rows()
    write_csv(SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_csv(SOURCE_ROWS, source_rows, SOURCE_FIELDS)
    write_report(summary_rows, source_rows)
    print(f"archive_active_public_sources={next(row['value'] for row in summary_rows if row['metric'] == 'archive_active_public_sources')}")
    print(f"captured_not_public_sources={next(row['value'] for row in summary_rows if row['metric'] == 'captured_not_public_sources')}")
    print(f"pre_surface_only_sources={next(row['value'] for row in summary_rows if row['metric'] == 'pre_surface_only_sources')}")
    print(f"wrote {SUMMARY.relative_to(ROOT)}")
    print(f"wrote {SOURCE_ROWS.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
