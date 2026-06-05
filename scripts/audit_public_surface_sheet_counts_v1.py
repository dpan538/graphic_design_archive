#!/usr/bin/env python3
"""Audit public-surface main/sub/text sheet counts and inferred group depth."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
PAYLOAD = ROOT / "generated" / "public_surfaces_v1.json"
GROUP_MEMBERSHIPS = DATA / "surface_group_memberships_v1.csv"

SUMMARY_OUTPUT = DATA / "public_surface_sheet_counts_v1.csv"
BREAKDOWN_OUTPUT = DATA / "public_surface_sheet_parent_breakdown_v1.csv"
REPORT = DOCS / "PUBLIC_SURFACE_SHEET_COUNTS_v1.md"

SUMMARY_FIELDS = ["metric", "value", "notes"]
BREAKDOWN_FIELDS = [
    "parent_surface_id",
    "parent_title",
    "group_count",
    "sub_sheet_count",
    "text_sheet_count",
    "child_surface_ids",
]


def clean(value: object) -> str:
    return str(value or "").strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def is_main_sheet(surface: dict) -> bool:
    return surface.get("publicationRole") == "main_sheet"


def is_text_sheet(surface: dict) -> bool:
    return surface.get("templateId") == "sheet.text.v0"


def is_sub_sheet(surface: dict) -> bool:
    return surface.get("surfaceType") == "sheet" and not is_main_sheet(surface)


def build_parent_child_map(surfaces_by_id: dict[str, dict]) -> dict[str, set[str]]:
    rows = read_csv(GROUP_MEMBERSHIPS)
    by_group: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_group[clean(row.get("group_id"))].append(row)

    parent_children: dict[str, set[str]] = defaultdict(set)
    for group_rows in by_group.values():
        parents = [
            clean(row.get("surface_id"))
            for row in group_rows
            if row.get("membership_role") == "parent_candidate"
            and clean(row.get("surface_id")) in surfaces_by_id
        ]
        if not parents:
            continue
        parent_id = parents[0]
        for row in group_rows:
            child_id = clean(row.get("surface_id"))
            if not child_id or child_id == parent_id or child_id not in surfaces_by_id:
                continue
            parent_children[parent_id].add(child_id)
    return parent_children


def main() -> None:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    surfaces = payload.get("surfaces", [])
    surfaces_by_id = {clean(surface.get("surfaceId")): surface for surface in surfaces if clean(surface.get("surfaceId"))}

    main_sheets = [surface for surface in surfaces if is_main_sheet(surface)]
    sub_sheets = [surface for surface in surfaces if is_sub_sheet(surface)]
    text_sheets = [surface for surface in surfaces if is_text_sheet(surface)]
    template_counts = Counter(clean(surface.get("templateId")) for surface in surfaces)
    role_counts = Counter(clean(surface.get("publicationRole")) or "(blank)" for surface in surfaces)

    parent_children = build_parent_child_map(surfaces_by_id)
    breakdown_rows: list[dict[str, str]] = []
    main_with_more_than_two_sub = 0
    main_with_more_than_five_text = 0
    for parent_id, child_ids in sorted(parent_children.items()):
        parent = surfaces_by_id[parent_id]
        sub_count = sum(1 for child_id in child_ids if is_sub_sheet(surfaces_by_id[child_id]) or is_main_sheet(surfaces_by_id[child_id]))
        text_count = sum(1 for child_id in child_ids if is_text_sheet(surfaces_by_id[child_id]))
        if sub_count > 2:
            main_with_more_than_two_sub += 1
        if text_count > 5:
            main_with_more_than_five_text += 1
        breakdown_rows.append(
            {
                "parent_surface_id": parent_id,
                "parent_title": clean(parent.get("title")),
                "group_count": str(len(child_ids)),
                "sub_sheet_count": str(sub_count),
                "text_sheet_count": str(text_count),
                "child_surface_ids": ";".join(sorted(child_ids)),
            }
        )

    summary_rows = [
        {
            "metric": "public_surfaces",
            "value": str(len(surfaces)),
            "notes": "All public surface records in generated/public_surfaces_v1.json.",
        },
        {
            "metric": "main_sheets",
            "value": str(len(main_sheets)),
            "notes": "Surfaces with publicationRole=main_sheet.",
        },
        {
            "metric": "sub_sheets",
            "value": str(len(sub_sheets)),
            "notes": "Sheet surfaces whose publicationRole is not main_sheet.",
        },
        {
            "metric": "text_sheets",
            "value": str(len(text_sheets)),
            "notes": "Surfaces with templateId=sheet.text.v0.",
        },
        {
            "metric": "inferred_parent_main_sheets",
            "value": str(len(parent_children)),
            "notes": "Main-sheet parents inferred from surface_group_memberships_v1 parent_candidate rows.",
        },
        {
            "metric": "main_sheets_with_more_than_2_sub_sheets",
            "value": str(main_with_more_than_two_sub),
            "notes": "Inferred group parents with more than two grouped child sheets. This includes grouped plate/main variants as sub-sheet depth for reporting.",
        },
        {
            "metric": "main_sheets_with_more_than_5_text_sheets",
            "value": str(main_with_more_than_five_text),
            "notes": "Inferred group parents with more than five child templateId=sheet.text.v0 records.",
        },
    ]
    for template, count in sorted(template_counts.items()):
        summary_rows.append({"metric": "template_count", "value": f"{template}:{count}", "notes": "Public-surface template distribution."})
    for role, count in sorted(role_counts.items()):
        summary_rows.append({"metric": "publication_role_count", "value": f"{role}:{count}", "notes": "Public-surface publicationRole distribution."})

    write_csv(SUMMARY_OUTPUT, summary_rows, SUMMARY_FIELDS)
    write_csv(BREAKDOWN_OUTPUT, breakdown_rows, BREAKDOWN_FIELDS)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Public Surface Sheet Counts v1",
        "",
        "Scope: generated public-surface payload and existing surface-group membership hints.",
        "",
        "## Summary",
        "",
        f"- Public surfaces: {len(surfaces)}",
        f"- Main sheets: {len(main_sheets)}",
        f"- Sub sheets: {len(sub_sheets)}",
        f"- Text sheets: {len(text_sheets)}",
        f"- Inferred parent main sheets: {len(parent_children)}",
        f"- Main sheets with more than 2 sub sheets: {main_with_more_than_two_sub}",
        f"- Main sheets with more than 5 text sheets: {main_with_more_than_five_text}",
        "",
        "## Template Distribution",
        "",
    ]
    for template, count in sorted(template_counts.items()):
        lines.append(f"- {template}: {count}")
    lines.extend(["", "## Publication Role Distribution", ""])
    for role, count in sorted(role_counts.items()):
        lines.append(f"- {role}: {count}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `main_sheets` uses `publicationRole=main_sheet` because that is the project-facing role surfaced to the frontend.",
            "- `sub_sheets` counts non-main sheet surfaces, including appendix/support/merge/thin visual sheets.",
            "- Parent-child depth is inferred from `surface_group_memberships_v1`; it is a reporting aid, not a rights or authorship claim.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"main_sheets={len(main_sheets)}")
    print(f"sub_sheets={len(sub_sheets)}")
    print(f"text_sheets={len(text_sheets)}")
    print(f"main_sheets_with_more_than_2_sub_sheets={main_with_more_than_two_sub}")
    print(f"main_sheets_with_more_than_5_text_sheets={main_with_more_than_five_text}")
    print(f"wrote {SUMMARY_OUTPUT.relative_to(ROOT)}")
    print(f"wrote {BREAKDOWN_OUTPUT.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
