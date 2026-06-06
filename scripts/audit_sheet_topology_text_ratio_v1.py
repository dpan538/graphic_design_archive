#!/usr/bin/env python3
"""Audit sheet topology, text-page depth, and grouping readiness.

This is an assessment-only audit. It does not merge, reclassify, or rewrite
surfaces. The goal is to separate source-capture growth from the later work of
turning many main sheets into research dossiers with sub sheets, cards,
appendices, and text pages.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
PAYLOAD = ROOT / "generated" / "public_surfaces_v1.json"
GROUP_CANDIDATES = DATA / "surface_group_candidates_v1.csv"

SUMMARY_CSV = DATA / "sheet_topology_text_ratio_v1.csv"
GROUP_CSV = DATA / "sheet_topology_group_opportunities_v1.csv"
REPORT = DOCS / "SHEET_TOPOLOGY_TEXT_RATIO_v1.md"


def clean(value: object) -> str:
    return str(value or "").strip()


def pct(numerator: float, denominator: float) -> str:
    if denominator <= 0:
        return "0.00"
    return f"{(numerator / denominator) * 100:.2f}"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    surfaces = payload.get("surfaces", [])
    dossiers = payload.get("researchDossiers", [])
    candidates = read_csv(GROUP_CANDIDATES)

    template_counts = Counter(clean(surface.get("templateId")) for surface in surfaces)
    role_counts = Counter(clean(surface.get("publicationRole")) for surface in surfaces)
    disposition_counts = Counter(clean(surface.get("surfaceDisposition")) for surface in surfaces)

    main_surfaces = [surface for surface in surfaces if clean(surface.get("publicationRole")) == "main_sheet"]
    independent_text_surfaces = [surface for surface in surfaces if clean(surface.get("templateId")) == "sheet.text.v0"]
    sub_surfaces = [surface for surface in surfaces if clean(surface.get("publicationRole")) != "main_sheet"]

    dossier_page_counts = [len(dossier.get("pageSequence", [])) for dossier in dossiers]
    dossier_text_page_counts = [
        sum(1 for page in dossier.get("pageSequence", []) if page.get("pageType") == "text_page")
        for dossier in dossiers
    ]
    dossier_sub_page_counts = [
        sum(1 for page in dossier.get("pageSequence", []) if page.get("pageType") in {"sub_sheet", "card", "appendix", "text_page"})
        for dossier in dossiers
    ]
    dossiers_with_multi_pages = sum(1 for count in dossier_page_counts if count > 2)
    dossiers_with_two_text_pages = sum(1 for count in dossier_text_page_counts if count >= 2)
    dossiers_with_any_text = sum(1 for count in dossier_text_page_counts if count > 0)
    single_anchor_dossiers = sum(1 for dossier in dossiers if clean(dossier.get("sourceScope")) == "single_anchor_record")
    compound_dossiers = len(dossiers) - single_anchor_dossiers

    candidate_type_counts = Counter(clean(row.get("group_type")) for row in candidates)
    candidate_confidence_counts = Counter(clean(row.get("confidence")) for row in candidates)
    candidate_action_counts = Counter(clean(row.get("recommended_action")) for row in candidates)
    group_member_total = sum(int(row.get("member_count") or 0) for row in candidates)
    strong_group_candidates = [
        row for row in candidates
        if clean(row.get("confidence")) in {"high", "medium"} and int(row.get("member_count") or 0) >= 3
    ]
    high_value_groups = sorted(
        candidates,
        key=lambda row: (int(row.get("member_count") or 0), clean(row.get("confidence")) == "high"),
        reverse=True,
    )[:40]

    summary_rows = [
        {"metric": "public_surfaces", "value": str(len(surfaces)), "notes": "All generated public surfaces."},
        {"metric": "main_sheets", "value": str(len(main_surfaces)), "notes": "publicationRole=main_sheet."},
        {"metric": "sub_or_support_surfaces", "value": str(len(sub_surfaces)), "notes": "All surfaces not marked as main_sheet."},
        {"metric": "independent_text_sheet_surfaces", "value": str(len(independent_text_surfaces)), "notes": "templateId=sheet.text.v0."},
        {"metric": "independent_text_sheet_surface_rate", "value": pct(len(independent_text_surfaces), len(surfaces)), "notes": "Independent text-sheet surfaces / all surfaces."},
        {"metric": "sub_or_support_surface_rate", "value": pct(len(sub_surfaces), len(surfaces)), "notes": "Non-main surfaces / all surfaces."},
        {"metric": "research_dossiers", "value": str(len(dossiers)), "notes": "Generated dossier packets."},
        {"metric": "single_anchor_dossiers", "value": str(single_anchor_dossiers), "notes": "Dossiers still built around one source anchor."},
        {"metric": "compound_or_group_dossiers", "value": str(compound_dossiers), "notes": "Dossiers with grouped children or non-single source scope."},
        {"metric": "dossiers_with_any_text_page", "value": str(dossiers_with_any_text), "notes": "Dossier pageSequence contains at least one text_page."},
        {"metric": "dossiers_with_two_or_more_text_pages", "value": str(dossiers_with_two_text_pages), "notes": "Closer to the desired main-sheet package shape."},
        {"metric": "dossiers_with_more_than_two_pages", "value": str(dossiers_with_multi_pages), "notes": "Dossiers with meaningful packet depth beyond main + one text page."},
        {"metric": "average_dossier_pages", "value": f"{(sum(dossier_page_counts) / len(dossier_page_counts)) if dossier_page_counts else 0:.2f}", "notes": "Mean pages per research dossier."},
        {"metric": "average_dossier_text_pages", "value": f"{(sum(dossier_text_page_counts) / len(dossier_text_page_counts)) if dossier_text_page_counts else 0:.2f}", "notes": "Mean text_page entries per research dossier."},
        {"metric": "group_candidates", "value": str(len(candidates)), "notes": "Potential grouping/parent opportunities from surface_group_candidates_v1.csv."},
        {"metric": "strong_group_candidates", "value": str(len(strong_group_candidates)), "notes": "Medium/high confidence groups with at least three members."},
        {"metric": "group_candidate_member_total", "value": str(group_member_total), "notes": "Total member_count across group candidates; diagnostic only and may overlap."},
    ]
    for template, count in sorted(template_counts.items()):
        summary_rows.append({"metric": f"template_count:{template or '(blank)'}", "value": str(count), "notes": "Template distribution."})
    for role, count in sorted(role_counts.items()):
        summary_rows.append({"metric": f"publication_role_count:{role or '(blank)'}", "value": str(count), "notes": "Publication role distribution."})
    for disposition, count in disposition_counts.most_common():
        summary_rows.append({"metric": f"surface_disposition_count:{disposition or '(blank)'}", "value": str(count), "notes": "Surface disposition distribution."})
    for group_type, count in candidate_type_counts.most_common():
        summary_rows.append({"metric": f"group_candidate_type:{group_type or '(blank)'}", "value": str(count), "notes": "Grouping opportunity type distribution."})
    for confidence, count in candidate_confidence_counts.most_common():
        summary_rows.append({"metric": f"group_candidate_confidence:{confidence or '(blank)'}", "value": str(count), "notes": "Grouping opportunity confidence distribution."})
    for action, count in candidate_action_counts.most_common():
        summary_rows.append({"metric": f"group_candidate_action:{action or '(blank)'}", "value": str(count), "notes": "Recommended grouping action distribution."})

    group_rows = [
        {
            "rank": str(index),
            "group_id": clean(row.get("group_id")),
            "group_type": clean(row.get("group_type")),
            "confidence": clean(row.get("confidence")),
            "member_count": clean(row.get("member_count")),
            "proposed_parent_surface_id": clean(row.get("proposed_parent_surface_id")),
            "proposed_parent_title": clean(row.get("proposed_parent_title")),
            "date_span": clean(row.get("date_span")),
            "source_names": clean(row.get("source_names")),
            "primary_folder": clean(row.get("primary_folder")),
            "recommended_action": clean(row.get("recommended_action")),
            "evidence_basis": clean(row.get("evidence_basis")),
        }
        for index, row in enumerate(high_value_groups, 1)
    ]

    write_csv(SUMMARY_CSV, summary_rows, ["metric", "value", "notes"])
    write_csv(
        GROUP_CSV,
        group_rows,
        [
            "rank",
            "group_id",
            "group_type",
            "confidence",
            "member_count",
            "proposed_parent_surface_id",
            "proposed_parent_title",
            "date_span",
            "source_names",
            "primary_folder",
            "recommended_action",
            "evidence_basis",
        ],
    )

    lines = [
        "# Sheet Topology and Text Ratio v1",
        "",
        "Scope: assessment-only audit of public-surface structure, research dossier page depth, text-page ratio, and grouping opportunities. This report does not merge or reclassify records.",
        "",
        "## Summary",
        "",
    ]
    for row in summary_rows[:17]:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Interpretation", ""])
    lines.extend(
        [
            "- Source capture is now ahead of sheet architecture: main sheets dominate the surface count.",
            "- Independent `sheet.text.v0` surfaces remain scarce, but research dossiers often include generated `text_page` entries inside `pageSequence`.",
            "- The strongest next structural work is not another raw capture pass; it is a grouping pass that promotes high-confidence source/series/decade groups into main packages with sub sheets, cards, appendices, and text pages.",
            "- Because group candidates can overlap, this audit treats candidate member totals as planning evidence rather than a direct merge count.",
        ]
    )
    lines.extend(["", "## Top Grouping Opportunities", ""])
    for row in group_rows[:20]:
        lines.append(
            f"- {row['group_id']} · {row['group_type']} · members={row['member_count']} · "
            f"confidence={row['confidence']} · parent={row['proposed_parent_title']}"
        )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"main_sheets={len(main_surfaces)}")
    print(f"independent_text_sheet_surfaces={len(independent_text_surfaces)}")
    print(f"sub_or_support_surfaces={len(sub_surfaces)}")
    print(f"research_dossiers={len(dossiers)}")
    print(f"dossiers_with_any_text_page={dossiers_with_any_text}")
    print(f"dossiers_with_two_or_more_text_pages={dossiers_with_two_text_pages}")
    print(f"average_dossier_pages={summary_rows[12]['value']}")
    print(f"group_candidates={len(candidates)}")
    print(f"strong_group_candidates={len(strong_group_candidates)}")
    print(f"wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"wrote {GROUP_CSV.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
