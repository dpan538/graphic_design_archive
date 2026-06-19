#!/usr/bin/env python3
"""Build reviewable card/subsheet demotion overrides for the candidate payload.

The decisions are non-destructive and apply only through the pre-freeze
candidate/public rebuild override layer. They do not delete capture rows,
download images, or change rights/image states.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

CONTEXT_REVIEW = DATA / "prefreeze_context_image_review_v1.csv"
SOURCE_GAP_REVIEW = DATA / "prefreeze_source_visible_gap_review_v1.csv"

OUT_DECISIONS = DATA / "prefreeze_surface_role_override_decisions_v1.csv"
OUT_OVERRIDES = DATA / "prefreeze_surface_role_overrides_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_surface_role_override_summary_v1.csv"
OUT_REPORT = DOCS / "PREFREEZE_SURFACE_ROLE_OVERRIDES_v1.md"

DECISION_FIELDS = [
    "source_file",
    "capture_id",
    "surface_id",
    "year",
    "region",
    "image_state",
    "source_name",
    "title",
    "source_url",
    "input_review_type",
    "review_class",
    "suggested_action",
    "surface_disposition_override",
    "decision_type",
    "confidence",
    "override_basis",
    "guardrail",
]

OVERRIDE_FIELDS = [
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


def base(row: dict[str, str]) -> dict[str, str]:
    return {
        "source_file": clean(row.get("source_file")),
        "capture_id": clean(row.get("capture_id")),
        "surface_id": clean(row.get("surface_id")),
        "year": clean(row.get("year")),
        "region": clean(row.get("region")),
        "image_state": clean(row.get("image_state")),
        "source_name": clean(row.get("source_name")),
        "title": clean(row.get("title")),
        "source_url": clean(row.get("source_url")),
        "input_review_type": clean(row.get("review_type")),
        "review_class": clean(row.get("review_class")),
        "suggested_action": clean(row.get("suggested_action")),
    }


def decision(row: dict[str, str], role: str, decision_type: str, confidence: str, basis: str, guardrail: str) -> dict[str, str]:
    return {
        **base(row),
        "surface_disposition_override": role,
        "decision_type": decision_type,
        "confidence": confidence,
        "override_basis": basis,
        "guardrail": guardrail,
    }


def decide_context(row: dict[str, str]) -> dict[str, str]:
    review_class = clean(row.get("review_class"))
    evidence = clean(row.get("evidence"))
    if review_class == "weak_context_or_profile_image":
        return decision(
            row,
            "card",
            "apply_card_demotion",
            "high",
            f"{review_class}: {evidence}",
            "Weak profile/own-work/context image; keep source visible but remove main-sheet claim.",
        )
    if review_class == "philatelic_or_stamp_like":
        return decision(
            row,
            "support_packet_appendix_text",
            "apply_subsheet_demotion",
            "medium",
            f"{review_class}: {evidence}",
            "Stamp/philatelic-like rows need support-packet treatment unless later reviewed as strong design objects.",
        )
    return decision(
        row,
        "",
        "manual_review_only",
        "low",
        f"{review_class}: {evidence}",
        "Event/photo language overlaps with design evidence; no automatic demotion.",
    )


def decide_source_gap(row: dict[str, str]) -> dict[str, str]:
    review_class = clean(row.get("review_class"))
    if review_class in {"source_registry_context_page", "registry_or_archive_landing_page"}:
        return decision(
            row,
            "card",
            "apply_card_demotion",
            "high",
            review_class,
            "Registry/landing page is source context, not an item-level image object.",
        )
    if review_class == "text_only_item_or_collection":
        return decision(
            row,
            "support_packet_appendix_text",
            "apply_subsheet_demotion",
            "medium",
            review_class,
            "Text-only or collection-level item remains readable but should not default to main-sheet status.",
        )
    return decision(
        row,
        "",
        "manual_recapture_or_review",
        "low",
        review_class,
        "IMG00/parser gap may become source-visible after recapture; no automatic demotion.",
    )


def override_rows(decisions: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in decisions:
        role = clean(row.get("surface_disposition_override"))
        if not role:
            continue
        rows.append(
            {
                "source_file": row.get("source_file", ""),
                "capture_id": row.get("capture_id", ""),
                "surface_id": row.get("surface_id", ""),
                "surface_disposition_override": role,
                "review_class": row.get("review_class", ""),
                "decision_type": row.get("decision_type", ""),
                "confidence": row.get("confidence", ""),
                "override_basis": row.get("override_basis", ""),
                "source_name": row.get("source_name", ""),
                "title": row.get("title", ""),
            }
        )
    return rows


def write_report(decisions: list[dict[str, str]], overrides: list[dict[str, str]], summary_rows: list[dict[str, str]]) -> None:
    lines = [
        "# Prefreeze Surface Role Overrides v1",
        "",
        "Scope: reviewable card/subsheet demotion layer for candidate-only rebuilds. It preserves source visibility and rights evidence while reducing unsupported main-sheet claims.",
        "",
        "## Summary",
        "",
    ]
    for row in summary_rows:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- No capture rows were deleted or edited.",
            "- No image files were downloaded.",
            "- IMG01/IMG03 rights states were not upgraded.",
            "- Manual review classes are not emitted as overrides.",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    context_rows = read_csv(CONTEXT_REVIEW)
    source_gap_rows = read_csv(SOURCE_GAP_REVIEW)
    decisions = [decide_context(row) for row in context_rows]
    decisions.extend(decide_source_gap(row) for row in source_gap_rows)
    overrides = override_rows(decisions)

    summary_rows: list[dict[str, str]] = [
        {"metric": "context_review_rows", "value": str(len(context_rows)), "notes": "Input context/event/photo review rows."},
        {"metric": "source_gap_review_rows", "value": str(len(source_gap_rows)), "notes": "Input source-visible gap review rows."},
        {"metric": "decision_rows", "value": str(len(decisions)), "notes": "Total role decisions emitted."},
        {"metric": "override_rows", "value": str(len(overrides)), "notes": "Rows eligible for candidate rebuild role override."},
    ]
    for decision_type, count in Counter(row.get("decision_type", "") for row in decisions).most_common():
        summary_rows.append({"metric": f"decision:{decision_type}", "value": str(count), "notes": "Decision type distribution."})
    for role, count in Counter(row.get("surface_disposition_override", "") for row in overrides).most_common():
        summary_rows.append({"metric": f"role:{role}", "value": str(count), "notes": "Surface role override distribution."})
    for review_class, count in Counter(row.get("review_class", "") for row in decisions).most_common():
        summary_rows.append({"metric": f"review_class:{review_class}", "value": str(count), "notes": "Review class distribution."})

    write_csv(OUT_DECISIONS, decisions, DECISION_FIELDS)
    write_csv(OUT_OVERRIDES, overrides, OVERRIDE_FIELDS)
    write_csv(OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_report(decisions, overrides, summary_rows)

    print(f"decision_rows={len(decisions)}")
    print(f"override_rows={len(overrides)}")
    print(f"wrote {OUT_DECISIONS.relative_to(ROOT)}")
    print(f"wrote {OUT_OVERRIDES.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
