#!/usr/bin/env python3
"""Build a manual rebuild queue for LOC item-level IMG03 candidates.

This script is advisory only. It joins the LOC source-only item probe with the
existing LOC repair preflight and emits a small queue for human/rebuild review.
It does not mutate capture records, rebuild surfaces, download images, or
upgrade IMG01/IMG03.
"""

from __future__ import annotations

from collections import Counter

from lib.archive_audit import DATA, DOCS, ROOT, read_csv, write_csv


PREFLIGHT = DATA / "loc_rights_repair_preflight_v1.csv"
PROBE = DATA / "loc_rights_item_probe_v1.csv"
OUTPUT_QUEUE = DATA / "loc_manual_img03_rebuild_queue_v1.csv"
OUTPUT_SUMMARY = DATA / "loc_manual_img03_rebuild_summary_v1.csv"
OUTPUT_REPORT = DOCS / "LOC_MANUAL_IMG03_REBUILD_QUEUE_v1.md"

QUEUE_FIELDS = [
    "surface_id",
    "local_record_file",
    "local_capture_id",
    "source_record_id",
    "source_record_url",
    "title",
    "date_or_period_hint",
    "local_image_state",
    "weighted_gap_points",
    "rights_signal",
    "rights_text_excerpt",
    "source_image_url",
    "source_image_url_count",
    "suggested_review_action",
    "suggested_target_state",
    "automatic_upgrade_allowed",
    "rights_boundary",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]


def build_queue() -> list[dict[str, str]]:
    preflight_by_surface = {row.get("surface_id", ""): row for row in read_csv(PREFLIGHT)}
    rows: list[dict[str, str]] = []
    for probe in read_csv(PROBE):
        if probe.get("recommendation") != "manual_img03_candidate_item_rights_visible":
            continue
        preflight = preflight_by_surface.get(probe.get("surface_id", ""), {})
        rows.append(
            {
                "surface_id": probe.get("surface_id", ""),
                "local_record_file": preflight.get("local_record_file", ""),
                "local_capture_id": preflight.get("local_capture_id", ""),
                "source_record_id": probe.get("source_record_id", ""),
                "source_record_url": probe.get("source_record_url", ""),
                "title": probe.get("title", ""),
                "date_or_period_hint": "pre-1940/WPA/advertising continuity candidate",
                "local_image_state": probe.get("local_image_state", ""),
                "weighted_gap_points": probe.get("weighted_gap_points", ""),
                "rights_signal": probe.get("rights_signal", ""),
                "rights_text_excerpt": probe.get("rights_text_excerpt", ""),
                "source_image_url": probe.get("first_image_url_excerpt", ""),
                "source_image_url_count": probe.get("image_url_count", ""),
                "suggested_review_action": "manual_patch_capture_record_then_rebuild_surfaces",
                "suggested_target_state": "IMG03_after_item_level_rights_review",
                "automatic_upgrade_allowed": "false",
                "rights_boundary": "LOC item metadata exposes image URL plus no-known-restrictions text; human review/rebuild still required.",
            }
        )
    rows.sort(key=lambda row: (row["local_record_file"], row["local_capture_id"], row["title"]))
    return rows


def write_summary(queue: list[dict[str, str]]) -> list[dict[str, str]]:
    by_file = Counter(row["local_record_file"] for row in queue)
    by_state = Counter(row["local_image_state"] for row in queue)
    weighted = sum(float(row.get("weighted_gap_points") or 0) for row in queue)
    summary = [
        {"metric": "manual_rebuild_candidate_rows", "value": str(len(queue)), "notes": "Rows with LOC item-level rights text and source image URLs."},
        {"metric": "manual_rebuild_candidate_weighted_gap_points", "value": f"{weighted:.2f}", "notes": "Weighted points represented by the queue; not applied automatically."},
        {"metric": "automatic_upgrade_allowed_rows", "value": "0", "notes": "Every row requires human/rebuild review before any state change."},
    ]
    for key, value in by_file.most_common():
        summary.append({"metric": f"local_record_file_{key}", "value": str(value), "notes": "Where a future patch would need to be applied after review."})
    for key, value in by_state.most_common():
        summary.append({"metric": f"local_image_state_{key}", "value": str(value), "notes": "Current local image state before review."})
    write_csv(OUTPUT_SUMMARY, summary, SUMMARY_FIELDS)
    return summary


def write_report(queue: list[dict[str, str]], summary: list[dict[str, str]]) -> None:
    metrics = {row["metric"]: row["value"] for row in summary}
    lines = [
        "# LOC Manual IMG03 Rebuild Queue v1",
        "",
        "This queue isolates LOC repair candidates where the source-only item probe found both a source-hosted image URL and item-level open/publication rights text. It is advisory only and does not mutate records or upgrade IMG01/IMG03.",
        "",
        "## Summary",
        "",
        f"- candidate rows: {metrics.get('manual_rebuild_candidate_rows', '0')}",
        f"- weighted gap points represented: {metrics.get('manual_rebuild_candidate_weighted_gap_points', '0.00')}",
        f"- automatic upgrades allowed: {metrics.get('automatic_upgrade_allowed_rows', '0')}",
        "",
        "## Rebuild Boundary",
        "",
        "- Future application must patch the original capture record with the LOC item rights text, image URL, source URL, and review note.",
        "- Surfaces must be rebuilt after the capture-record patch before the source can count as successful archive integration.",
        "- The queue does not contain image binaries or raw JSON payloads.",
        "- Rate-limited LOC rows are not included; they remain in `retry_later_rate_limited` from the item probe.",
        "",
        "## Output Files",
        "",
        f"- `{OUTPUT_QUEUE.relative_to(ROOT)}`",
        f"- `{OUTPUT_SUMMARY.relative_to(ROOT)}`",
    ]
    OUTPUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    queue = build_queue()
    write_csv(OUTPUT_QUEUE, queue, QUEUE_FIELDS)
    summary = write_summary(queue)
    write_report(queue, summary)
    metrics = {row["metric"]: row["value"] for row in summary}
    print(f"manual_rebuild_candidate_rows={metrics.get('manual_rebuild_candidate_rows', '0')}")
    print(f"manual_rebuild_candidate_weighted_gap_points={metrics.get('manual_rebuild_candidate_weighted_gap_points', '0.00')}")
    print(f"automatic_upgrade_allowed_rows={metrics.get('automatic_upgrade_allowed_rows', '0')}")
    print(f"wrote {OUTPUT_QUEUE.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
