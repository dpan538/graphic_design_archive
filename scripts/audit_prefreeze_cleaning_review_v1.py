#!/usr/bin/env python3
"""Build focused review queues for remaining candidate-cleaning blockers.

This audit is non-mutating. It converts broad promotion blockers into two
actionable queues:

- source-visible gaps (IMG00/IMG04),
- event/photo/context-image rows that need card/support review.

It does not edit capture records, exclude rows, download images, or upgrade
rights/image states.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

import audit_prefreeze_candidate_promotion_blockers_v1 as blockers


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
PAYLOAD = ROOT / "generated" / "public_surfaces_prefreeze_candidate_v1.json"
BLOCKERS = DATA / "prefreeze_candidate_promotion_blockers_v1.csv"

OUT_SOURCE_GAP = DATA / "prefreeze_source_visible_gap_review_v1.csv"
OUT_CONTEXT_REVIEW = DATA / "prefreeze_context_image_review_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_cleaning_review_summary_v1.csv"
OUT_REPORT = DOCS / "PREFREEZE_CLEANING_REVIEW_v1.md"

REVIEW_FIELDS = [
    "review_type",
    "source_file",
    "capture_id",
    "surface_id",
    "year",
    "region",
    "image_state",
    "source_name",
    "title",
    "source_url",
    "review_class",
    "suggested_action",
    "evidence",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


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


def payload_surfaces() -> dict[str, dict]:
    if not PAYLOAD.exists():
        return {}
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    return {
        clean(surface.get("sourceRecordId")): surface
        for surface in payload.get("surfaces", [])
        if clean(surface.get("sourceRecordId"))
    }


def source_gap_class(row: dict[str, str]) -> tuple[str, str]:
    state = row.get("image_state", "")
    source_file = row.get("source_file", "")
    source_name = row.get("source_name", "")
    if state == "IMG00":
        return "image_missing_or_parser_gap", "Recapture/probe image metadata or keep as text/card until source image evidence is visible."
    if "edge_source_registry_context" in source_file:
        return "source_registry_context_page", "Keep as source registry/context material; do not count as image-bearing object until item records are captured."
    if "Registry" in source_name or "Archive" in source_name and state == "IMG04":
        return "registry_or_archive_landing_page", "Keep as context source or split into item-level captures before publication."
    return "text_only_item_or_collection", "Review whether this should stay IMG04 text sheet, become card/support, or receive an item-image recapture."


def context_class(blob: str, has_design_claim: bool) -> tuple[str, str, str]:
    stamp = blockers.STAMP_TERMS.search(blob)
    event = blockers.EVENT_TERMS.search(blob)
    weak = blockers.WEAK_CONTEXT_TERMS.search(blob)
    if stamp:
        return "philatelic_or_stamp_like", "card_support_review", stamp.group(0)
    if event:
        action = "manual_keep_or_card_review" if has_design_claim else "card_support_candidate"
        return "event_or_photo_language", action, event.group(0)
    if weak:
        return "weak_context_or_profile_image", "card_support_candidate", weak.group(0)
    return "context_detector_match", "manual_review", ""


def review_base(row: dict[str, str], review_type: str) -> dict[str, str]:
    return {
        "review_type": review_type,
        "source_file": row.get("source_file", ""),
        "capture_id": row.get("capture_id", ""),
        "surface_id": row.get("surface_id", ""),
        "year": row.get("year", ""),
        "region": row.get("region", ""),
        "image_state": row.get("image_state", ""),
        "source_name": row.get("source_name", ""),
        "title": row.get("title", ""),
        "source_url": row.get("source_url", ""),
    }


def main() -> None:
    blocker_rows = read_csv(BLOCKERS)
    captures = blockers.capture_lookup()
    surfaces = payload_surfaces()

    source_gap_rows: list[dict[str, str]] = []
    context_rows: list[dict[str, str]] = []

    for row in blocker_rows:
        blocker_type = row.get("blocker_type")
        capture_id = clean(row.get("capture_id"))
        if blocker_type == "source_visible_gap":
            review_class, action = source_gap_class(row)
            source_gap_rows.append(
                {
                    **review_base(row, "source_visible_gap"),
                    "review_class": review_class,
                    "suggested_action": action,
                    "evidence": f"{row.get('image_state', '')}; {row.get('source_name', '')}",
                }
            )
        elif blocker_type == "event_photo_or_context_image":
            surface = surfaces.get(capture_id, {})
            capture = captures.get(capture_id)
            blob = blockers.row_blob(surface, capture)
            has_design_claim = blockers.DESIGN_TERMS.search(blob) is not None
            review_class, action, evidence = context_class(blob, has_design_claim)
            context_rows.append(
                {
                    **review_base(row, "event_photo_or_context_image"),
                    "review_class": review_class,
                    "suggested_action": action,
                    "evidence": evidence,
                }
            )

    source_gap_class_counts = Counter(row["review_class"] for row in source_gap_rows)
    context_class_counts = Counter(row["review_class"] for row in context_rows)
    context_action_counts = Counter(row["suggested_action"] for row in context_rows)
    summary_rows: list[dict[str, str]] = [
        {"metric": "source_visible_gap_rows", "value": str(len(source_gap_rows)), "notes": "IMG00/IMG04 rows requiring source-visible review."},
        {"metric": "context_image_review_rows", "value": str(len(context_rows)), "notes": "Event/photo/context-image review rows."},
    ]
    for label, count in source_gap_class_counts.most_common():
        summary_rows.append({"metric": f"source_gap_class:{label}", "value": str(count), "notes": "Source-visible gap class."})
    for label, count in context_class_counts.most_common():
        summary_rows.append({"metric": f"context_class:{label}", "value": str(count), "notes": "Context/image review class."})
    for label, count in context_action_counts.most_common():
        summary_rows.append({"metric": f"context_action:{label}", "value": str(count), "notes": "Suggested event/context handling."})

    write_csv(OUT_SOURCE_GAP, source_gap_rows, REVIEW_FIELDS)
    write_csv(OUT_CONTEXT_REVIEW, context_rows, REVIEW_FIELDS)
    write_csv(OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)

    lines = [
        "# Prefreeze Cleaning Review v1",
        "",
        "Scope: remaining source-visible and event/photo/context-image review queues for the pre-freeze candidate. No raw capture rows, official payloads, rights states, or image files were changed.",
        "",
        "## Summary",
        "",
    ]
    for row in summary_rows:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "- Source-visible gap rows are mostly IMG04/IMG00 records; they should be recaptured, kept as text/context, or demoted to support rather than hidden to improve a metric.",
            "- Event/photo/context-image rows are P1 review candidates. `manual_keep_or_card_review` means design language exists and the row should not be bulk-excluded.",
            "- This audit does not perform image-state or rights upgrades.",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"source_visible_gap_rows={len(source_gap_rows)}")
    print(f"context_image_review_rows={len(context_rows)}")
    print(f"wrote {OUT_SOURCE_GAP.relative_to(ROOT)}")
    print(f"wrote {OUT_CONTEXT_REVIEW.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
