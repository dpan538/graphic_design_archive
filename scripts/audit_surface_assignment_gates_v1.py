#!/usr/bin/env python3
"""Audit revised surface assignment gates against capture records and groups."""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

import generate_source_record_linkage_candidates_v1 as linkage


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

GROUPS = DATA / "source_record_linkage_candidates_v1.csv"
MEMBERS = DATA / "source_record_linkage_memberships_v1.csv"
OUT = DATA / "surface_assignment_gate_audit_v1.csv"
REPORT = DOCS / "SURFACE_ASSIGNMENT_GATE_AUDIT_v1.md"

FIELDS = [
    "capture_uid",
    "capture_id",
    "capture_file",
    "source_name",
    "source_identifier",
    "source_title",
    "period_band",
    "image_state",
    "source_reading_text_length",
    "all_context_text_length",
    "completeness_proxy",
    "group_count",
    "primary_group_id",
    "primary_relation_label",
    "primary_group_action",
    "recommended_disposition",
    "disposition_reason",
    "requires_group_review",
]

GENERIC_TITLE_RE = re.compile(
    r"^(untitled|untitled illustration|poster|affiche|graphic design|commercial art|"
    r"chineseposters\.net|source record|image|unknown|handkerchief)$",
    re.I,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def group_maps() -> tuple[dict[str, dict[str, str]], dict[str, list[dict[str, str]]]]:
    group_by_id = {row["linkage_group_id"]: row for row in read_csv(GROUPS)}
    groups_by_uid: dict[str, list[dict[str, str]]] = defaultdict(list)
    for member in read_csv(MEMBERS):
        group = group_by_id.get(member.get("linkage_group_id", ""))
        if group:
            groups_by_uid[member["capture_uid"]].append(group)
    return group_by_id, groups_by_uid


def important_group(groups: list[dict[str, str]]) -> dict[str, str] | None:
    if not groups:
        return None
    order = {
        "deduplicate_or_merge_source_records": 5,
        "review_duplicate_image_before_public_rebuild": 4,
        "canonical_main_with_child_text_appendix": 3,
        "support_packet_or_compound_sheet_candidate": 2,
        "attach_to_parent_as_card_or_appendix": 1,
    }
    return max(
        groups,
        key=lambda row: (
            order.get(row.get("recommended_group_action", ""), 0),
            int(row.get("member_count") or 0),
            int(row.get("anchor_completeness_proxy") or 0),
        ),
    )


def source_reading_text_length(row: dict[str, str]) -> int:
    # Only count source-provided description/OCR fields here. Generated editorial
    # summaries are useful downstream, but they must not promote a row to a main
    # sheet by themselves.
    fields = (
        "source_description",
        "source_notes",
        "source_subjects",
        "ocr_or_excerpt",
        "source_description_raw",
    )
    return len(" ".join(linkage.clean(row.get(field)) for field in fields).strip())


def has_source_return(row: dict[str, str]) -> bool:
    return bool(linkage.clean(row.get("source_record_url")) or linkage.clean(row.get("source_api_url")))


def has_rights_basis(row: dict[str, str]) -> bool:
    return bool(
        linkage.clean(row.get("source_rights_text"))
        or linkage.clean(row.get("rights_uri"))
        or linkage.clean(row.get("rights_basis"))
        or linkage.clean(row.get("image_state_review_note"))
    )


def is_generic_title(row: dict[str, str]) -> bool:
    value = linkage.norm(row.get("source_title"))
    if not value:
        return True
    return bool(GENERIC_TITLE_RE.match(value))


def assign(row: dict[str, str], group: dict[str, str] | None) -> tuple[str, str, bool]:
    score = linkage.completeness_proxy(row)
    source_text_len = source_reading_text_length(row)
    img = linkage.image_state(row)
    action = group.get("recommended_group_action", "") if group else ""
    relation = group.get("relation_label", "") if group else ""
    is_anchor = bool(group and group.get("proposed_anchor_capture_id") == row.get("capture_id"))

    if action == "deduplicate_or_merge_source_records" and not is_anchor:
        return "dedupe_child_record", "same source record/identifier should attach to canonical source register", True
    if action == "review_duplicate_image_before_public_rebuild":
        return "duplicate_image_review_packet", "shared image URL needs review before any independent main sheet", True
    if action == "canonical_main_with_child_text_appendix" and not is_anchor and relation != "related_but_not_same":
        if score >= 55:
            return "subsheet_group_child", "series/campaign member should attach under a main/group sheet as a subsheet", True
        return "card_or_bookmark_group_child", "weak series member should attach below the group as card/slip/bookmark", True

    core_gates = has_source_return(row) and has_rights_basis(row) and not is_generic_title(row)
    if score >= 80 and core_gates and source_text_len >= 160:
        if img == "IMG04" and source_text_len >= 300:
            return "text_sheet_candidate", "strong source text without image frame by source state", False
        if img == "IMG00" and source_text_len >= 220:
            return "img00_rights_sheet_candidate", "strong text/source evidence but image withheld; needs AX01 evidence", False
        if img in {"IMG01", "IMG02", "IMG03"}:
            return "main_sheet_candidate", "strong record with image evidence and enough source-reading text", False
    if score >= 75 and core_gates and source_text_len >= 80 and is_anchor:
        return "subsheet_or_group_anchor_review", "possible group anchor, but source text is below main-sheet threshold", True
    if score >= 75 and img in {"IMG01", "IMG02", "IMG03"}:
        return "subsheet_visual", "strong metadata/image but too little source-reading text for main sheet", False
    if score >= 75 and source_text_len >= 80:
        return "subsheet_text_or_appendix_review", "source text exists but core main-sheet gates are incomplete or title is generic", False
    if score >= 55:
        return "appendix_or_text_sheet", "medium completeness; use appendix plus text sheet treatment", False
    if score >= 40:
        return "card_with_slip_or_parent_attachment", "compact record should attach to a stronger unit if possible", False
    if score >= 20:
        return "card", "stable but sparse record", False
    return "bookmark_candidate", "fragmentary pointer or internal lead", False


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    _, groups_by_uid = group_maps()
    rows = linkage.capture_rows()
    audit_rows: list[dict[str, str]] = []

    for row in rows:
        groups = groups_by_uid.get(row["_capture_uid"], [])
        group = important_group(groups)
        disposition, reason, needs_group_review = assign(row, group)
        audit_rows.append(
            {
                "capture_uid": row["_capture_uid"],
                "capture_id": row.get("capture_id", ""),
                "capture_file": row["_capture_file"],
                "source_name": row.get("source_name", ""),
                "source_identifier": row.get("source_identifier", ""),
                "source_title": linkage.title(row),
                "period_band": linkage.period_band(row),
                "image_state": linkage.image_state(row),
                "source_reading_text_length": str(source_reading_text_length(row)),
                "all_context_text_length": str(linkage.text_length(row)),
                "completeness_proxy": str(linkage.completeness_proxy(row)),
                "group_count": str(len(groups)),
                "primary_group_id": group.get("linkage_group_id", "") if group else "",
                "primary_relation_label": group.get("relation_label", "") if group else "",
                "primary_group_action": group.get("recommended_group_action", "") if group else "",
                "recommended_disposition": disposition,
                "disposition_reason": reason,
                "requires_group_review": "true" if needs_group_review else "false",
            }
        )

    write_csv(OUT, audit_rows)

    disposition_counts = Counter(row["recommended_disposition"] for row in audit_rows)
    period_counts: dict[str, Counter[str]] = defaultdict(Counter)
    image_counts: dict[str, Counter[str]] = defaultdict(Counter)
    review_count = sum(1 for row in audit_rows if row["requires_group_review"] == "true")
    for row in audit_rows:
        period_counts[row["period_band"]][row["recommended_disposition"]] += 1
        image_counts[row["image_state"]][row["recommended_disposition"]] += 1

    thin_examples = [
        row
        for row in audit_rows
        if row["recommended_disposition"] in {"subsheet_visual", "appendix_or_text_sheet", "card_with_slip_or_parent_attachment", "subsheet_text_or_appendix_review"}
    ][:20]
    group_examples = [row for row in audit_rows if row["requires_group_review"] == "true"][:20]

    lines = [
        "# Surface Assignment Gate Audit v1",
        "",
        "Date: 2026-06-01",
        "",
        "Scope: capture records, before any public payload rebuild. This audit applies the hierarchy main sheet -> subsheet -> appendix/text sheet -> card/slip -> bookmark and uses linkage groups to suppress standalone thin or duplicated sheets.",
        "",
        "## Summary",
        "",
        f"- Capture rows audited: {len(audit_rows)}",
        f"- Rows requiring group/linkage review before standalone publication: {review_count}",
        "",
        "## Recommended Dispositions",
        "",
    ]
    lines += [f"- `{key}`: {value}" for key, value in disposition_counts.most_common()]
    lines += ["", "## Period Breakdown", ""]
    for period, counter in sorted(period_counts.items()):
        joined = "; ".join(f"{key}: {value}" for key, value in counter.most_common())
        lines.append(f"- {period}: {joined}")
    lines += ["", "## Image-State Breakdown", ""]
    for state, counter in sorted(image_counts.items()):
        joined = "; ".join(f"{key}: {value}" for key, value in counter.most_common())
        lines.append(f"- {state}: {joined}")
    lines += ["", "## Thin / Support Examples", ""]
    for row in thin_examples:
        lines.append(
            f"- {row['capture_id']} | {row['recommended_disposition']} | score {row['completeness_proxy']} | "
            f"source text {row['source_reading_text_length']} | {row['source_title']}"
        )
    lines += ["", "## Group Review Examples", ""]
    for row in group_examples:
        lines.append(
            f"- {row['capture_id']} | {row['recommended_disposition']} | {row['primary_group_id']} | "
            f"{row['primary_relation_label']} | {row['source_title']}"
        )
    lines += [
        "",
        "## Implementation Notes",
        "",
        "- This is an audit layer, not a destructive migration.",
        "- `dedupe_child_record` and `subsheet_group_child` should not receive independent main-sheet SEQ numbers until reviewed.",
        "- `subsheet_visual` is the new home for many former thin main sheets.",
        "- `main_sheet_candidate` still needs final rights, source-return, folder-membership, and research-unit checks.",
        "- The next payload rebuild should consume this audit so cards, bookmarks, text pages, and AX appendices become real publication surfaces instead of visual labs.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(audit_rows)} rows)")
    print(f"Wrote {REPORT}")
    print(f"dispositions={dict(disposition_counts.most_common())}")
    print(f"group_review={review_count}")


if __name__ == "__main__":
    main()
