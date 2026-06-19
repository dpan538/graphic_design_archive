#!/usr/bin/env python3
"""Audit main/sub/card/text structure in the pre-freeze candidate payload."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
PAYLOAD = ROOT / "generated" / "public_surfaces_prefreeze_candidate_v1.json"

OUT_SUMMARY = DATA / "prefreeze_main_sub_text_structure_summary_v1.csv"
OUT_PERIOD = DATA / "prefreeze_main_sub_text_structure_by_period_v1.csv"
OUT_REVIEW = DATA / "prefreeze_main_sheet_structure_review_v1.csv"
OUT_REPORT = DOCS / "PREFREEZE_MAIN_SUB_TEXT_STRUCTURE_v1.md"

SUMMARY_FIELDS = ["metric", "value", "notes"]
PERIOD_FIELDS = ["period", "main_sheets", "sub_sheets", "cards", "text_pages", "appendix_pages", "surfaces"]
REVIEW_FIELDS = [
    "surface_id",
    "capture_id",
    "year",
    "title",
    "source_name",
    "region",
    "image_state",
    "surface_type",
    "publication_role",
    "source_scope",
    "source_reading_text_length",
    "reading_text_length",
    "compound_children",
    "review_reason",
]


PERIODS = [
    ("pre_1850", None, 1849),
    ("1850_1899", 1850, 1899),
    ("1900_1913", 1900, 1913),
    ("1914_1945", 1914, 1945),
    ("1946_1969", 1946, 1969),
    ("1970_1989", 1970, 1989),
    ("1990_1999", 1990, 1999),
    ("2000_2009", 2000, 2009),
    ("2010_2019", 2010, 2019),
    ("2020_2026", 2020, 2026),
    ("undated", None, None),
]


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_payload() -> dict:
    return json.loads(PAYLOAD.read_text(encoding="utf-8"))


def year_of(surface: dict) -> int | None:
    for key in ("dateEnd", "dateStart"):
        value = surface.get(key)
        if isinstance(value, int):
            return value
        text = clean(value)
        if text.isdigit():
            return int(text)
    return None


def period_of(year: int | None) -> str:
    if year is None:
        return "undated"
    for label, start, end in PERIODS:
        if label == "undated":
            continue
        if (start is None or year >= start) and (end is None or year <= end):
            return label
    return "undated"


def region_of(surface: dict) -> str:
    for folder in surface.get("folders", []):
        if isinstance(folder, dict) and folder.get("type") == "region":
            return clean(folder.get("title"))
    return ""


def image_state(surface: dict) -> str:
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    return clean(image.get("state")) or "IMG00"


def source_text_length(surface: dict) -> int:
    return int(surface.get("sourceReadingTextLength") or 0)


def reading_length(surface: dict) -> int:
    return len(
        " ".join(
            clean(surface.get(key))
            for key in (
                "descriptionSummary",
                "sourceDescription",
                "historicalContextNote",
                "sourceNotes",
                "sourceSubjects",
            )
        ).strip()
    )


def by_surface_dossier(payload: dict) -> dict[str, dict]:
    return {
        clean(dossier.get("anchorSurfaceId")): dossier
        for dossier in payload.get("researchDossiers", [])
        if clean(dossier.get("anchorSurfaceId"))
    }


def page_type_counts(dossier: dict | None) -> Counter[str]:
    counts: Counter[str] = Counter()
    if not dossier:
        return counts
    for page in dossier.get("pageSequence", []):
        counts[clean(page.get("pageType"))] += 1
    return counts


def review_reason(surface: dict, dossier: dict | None) -> str:
    if surface.get("publicationRole") != "main_sheet":
        return ""
    reasons: list[str] = []
    source_len = source_text_length(surface)
    read_len = reading_length(surface)
    if source_len < 80:
        reasons.append("main_sheet_source_text_lt80")
    if read_len < 600:
        reasons.append("main_sheet_total_reading_lt600")
    if image_state(surface) == "IMG03" and source_len < 80:
        reasons.append("image_led_main_low_source_text")
    if not surface.get("compoundChildren") and page_type_counts(dossier).get("subsheet", 0) == 0:
        reasons.append("single_anchor_no_subsheet_relation")
    return "; ".join(reasons)


def main() -> None:
    payload = load_payload()
    surfaces = payload.get("surfaces", [])
    dossiers = payload.get("researchDossiers", [])
    dossier_by_surface = by_surface_dossier(payload)

    anchor_counts = Counter(clean(dossier.get("anchorType")) for dossier in dossiers)
    page_counts: Counter[str] = Counter()
    for dossier in dossiers:
        page_counts.update(page_type_counts(dossier))

    period_rows: dict[str, Counter[str]] = {label: Counter() for label, *_ in PERIODS}
    review_rows: list[dict[str, object]] = []
    main_with_children = 0
    main_children_gt2 = 0
    main_children_gt5 = 0
    main_dossier_sub_gt2 = 0
    main_dossier_text_gt5 = 0

    for surface in surfaces:
        sid = clean(surface.get("surfaceId"))
        dossier = dossier_by_surface.get(sid)
        period = period_of(year_of(surface))
        pcounts = page_type_counts(dossier)
        period_rows[period]["surfaces"] += 1
        if surface.get("publicationRole") == "main_sheet":
            period_rows[period]["main_sheets"] += 1
        elif surface.get("publicationRole") in {"support_packet_appendix_text", "thin_visual_support_packet"}:
            period_rows[period]["sub_sheets"] += 1
        elif surface.get("surfaceType") == "card":
            period_rows[period]["cards"] += 1
        period_rows[period]["text_pages"] += pcounts.get("text_page", 0)
        period_rows[period]["appendix_pages"] += pcounts.get("appendix", 0)

        children = surface.get("compoundChildren") or []
        if surface.get("publicationRole") == "main_sheet" and children:
            main_with_children += 1
            if len(children) > 2:
                main_children_gt2 += 1
            if len(children) > 5:
                main_children_gt5 += 1
        if surface.get("publicationRole") == "main_sheet" and pcounts.get("subsheet", 0) > 2:
            main_dossier_sub_gt2 += 1
        if surface.get("publicationRole") == "main_sheet" and pcounts.get("text_page", 0) > 5:
            main_dossier_text_gt5 += 1

        reason = review_reason(surface, dossier)
        if reason:
            review_rows.append(
                {
                    "surface_id": sid,
                    "capture_id": clean(surface.get("sourceRecordId")),
                    "year": year_of(surface) or "",
                    "title": clean(surface.get("title"))[:240],
                    "source_name": clean(surface.get("sourceName"))[:220],
                    "region": region_of(surface),
                    "image_state": image_state(surface),
                    "surface_type": clean(surface.get("surfaceType")),
                    "publication_role": clean(surface.get("publicationRole")),
                    "source_scope": clean(dossier.get("sourceScope")) if dossier else "",
                    "source_reading_text_length": source_text_length(surface),
                    "reading_text_length": reading_length(surface),
                    "compound_children": len(children),
                    "review_reason": reason,
                }
            )

    surface_type_counts = Counter(clean(surface.get("surfaceType")) for surface in surfaces)
    role_counts = Counter(clean(surface.get("publicationRole")) for surface in surfaces)
    summary_rows: list[dict[str, str]] = [
        {"metric": "surfaces", "value": str(len(surfaces)), "notes": "Candidate surfaces scanned."},
        {"metric": "research_dossiers", "value": str(len(dossiers)), "notes": "Research dossiers generated."},
        {"metric": "main_sheet_review_rows", "value": str(len(review_rows)), "notes": "Main sheets with thin text or no subsheet relation."},
        {"metric": "main_with_compound_children", "value": str(main_with_children), "notes": "Main sheets with compoundChildren."},
        {"metric": "main_with_compound_children_gt2", "value": str(main_children_gt2), "notes": "Main sheets with more than two child records."},
        {"metric": "main_with_compound_children_gt5", "value": str(main_children_gt5), "notes": "Main sheets with more than five child records."},
        {"metric": "main_dossiers_with_subsheet_pages_gt2", "value": str(main_dossier_sub_gt2), "notes": "Dossier page sequences with more than two subsheet pages."},
        {"metric": "main_dossiers_with_text_pages_gt5", "value": str(main_dossier_text_gt5), "notes": "Dossier page sequences with more than five text pages."},
    ]
    for key, count in surface_type_counts.most_common():
        summary_rows.append({"metric": f"surface_type:{key}", "value": str(count), "notes": "Surface type distribution."})
    for key, count in role_counts.most_common():
        summary_rows.append({"metric": f"publication_role:{key}", "value": str(count), "notes": "Publication role distribution."})
    for key, count in anchor_counts.most_common():
        summary_rows.append({"metric": f"dossier_anchor:{key}", "value": str(count), "notes": "Research dossier anchor distribution."})
    for key, count in page_counts.most_common():
        summary_rows.append({"metric": f"dossier_page:{key}", "value": str(count), "notes": "Research dossier page type distribution."})

    period_out = [
        {
            "period": label,
            "main_sheets": period_rows[label]["main_sheets"],
            "sub_sheets": period_rows[label]["sub_sheets"],
            "cards": period_rows[label]["cards"],
            "text_pages": period_rows[label]["text_pages"],
            "appendix_pages": period_rows[label]["appendix_pages"],
            "surfaces": period_rows[label]["surfaces"],
        }
        for label, *_ in PERIODS
    ]

    write_csv(OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_csv(OUT_PERIOD, period_out, PERIOD_FIELDS)
    write_csv(OUT_REVIEW, review_rows, REVIEW_FIELDS)

    lines = [
        "# Prefreeze Main/Sub/Text Structure Audit v1",
        "",
        "Scope: candidate payload structure audit after pre-freeze cleaning overrides. It evaluates distribution, not historical correctness.",
        "",
        "## Summary",
        "",
    ]
    for row in summary_rows:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Period Counts", ""])
    for row in period_out:
        lines.append(
            f"- {row['period']}: main {row['main_sheets']}, sub {row['sub_sheets']}, card {row['cards']}, text {row['text_pages']}, appendix {row['appendix_pages']}"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `main_sheet_review_rows` marks main sheets that are thin or have no visible subsheet relation; it is a review queue, not an automatic downgrade list.",
            "- `compoundChildren` is currently the only explicit intra-main relation available in the payload; most dossiers are still single-anchor records.",
            "- Text pages are generated one per sheet-level surface, so high text-page count does not yet mean editorial depth. The reading-length review queue is more meaningful.",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"surfaces={len(surfaces)}")
    print(f"research_dossiers={len(dossiers)}")
    print(f"main_sheet_review_rows={len(review_rows)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_PERIOD.relative_to(ROOT)}")
    print(f"wrote {OUT_REVIEW.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
