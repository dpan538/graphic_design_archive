#!/usr/bin/env python3
"""Generate candidate archive groups from the current public surface payload.

This pass does not mutate public surfaces. It proposes grouping units that can
later become canonical sheets, compound sheets, support packets, source
registers, child cards, or bookmark fragments.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "generated" / "public_surfaces_v1.json"
GROUPS_CSV = ROOT / "data" / "surface_group_candidates_v1.csv"
MEMBERS_CSV = ROOT / "data" / "surface_group_memberships_v1.csv"
REPORT = ROOT / "docs" / "capture" / "SURFACE_GROUPING_AUDIT_v1.md"
ACCESS_DATE = "2026-06-01"

GROUP_FIELDS = [
    "group_id",
    "group_type",
    "group_key",
    "confidence",
    "member_count",
    "proposed_parent_surface_id",
    "proposed_parent_title",
    "parent_score",
    "date_span",
    "source_names",
    "primary_folder",
    "member_dispositions",
    "image_states",
    "recommended_action",
    "coverage_gap_flags",
    "evidence_basis",
    "member_surface_ids",
]

MEMBER_FIELDS = [
    "group_id",
    "surface_id",
    "membership_role",
    "display_role",
    "membership_confidence",
    "title",
    "date_text",
    "source_name",
    "surface_disposition",
    "completeness_score",
    "image_state",
    "source_url",
]


def norm(value: str) -> str:
    value = value or ""
    value = value.lower()
    value = re.sub(r"https?://\S+", " ", value)
    value = re.sub(r"[\W_]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", norm(value))
    return cleaned.strip("-")[:80] or "unknown"


def read_payload() -> dict[str, Any]:
    return json.loads(PAYLOAD.read_text(encoding="utf-8"))


def table_value(surface: dict[str, Any], kind: str, label_terms: tuple[str, ...]) -> str:
    terms = tuple(term.lower() for term in label_terms)
    for table in surface.get("tables", []):
        if table.get("kind") != kind:
            continue
        for label, value in table.get("rows", []):
            if any(term in str(label).lower() for term in terms):
                return str(value or "")
    return ""


def source_identifier(surface: dict[str, Any]) -> str:
    value = table_value(surface, "SOURCE", ("source identifier", "identifier"))
    return "" if norm(value) in {"unknown", "none", "n a", "na"} else value


def source_collection(surface: dict[str, Any]) -> str:
    value = table_value(surface, "SOURCE", ("collection",))
    return "" if norm(value) in {"unknown", "none", "n a", "na"} else value


def source_text_len(surface: dict[str, Any]) -> int:
    value = surface.get("sourceReadingTextLength")
    if isinstance(value, int):
        return value
    return len(
        " ".join(
            str(surface.get(key) or "")
            for key in ("sourceDescription", "sourceNotes", "sourceSubjects")
        ).strip()
    )


def score(surface: dict[str, Any]) -> int:
    value = surface.get("completenessScore")
    return int(value) if isinstance(value, int) else 0


def image_state(surface: dict[str, Any]) -> str:
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    return image.get("state") or "IMG00"


def folder_key(surface: dict[str, Any], folder_type: str) -> str:
    for folder in surface.get("folders", []):
        if folder.get("type") == folder_type:
            return folder.get("title", "")
    return ""


def decade(surface: dict[str, Any]) -> str:
    year = surface.get("dateEnd") or surface.get("dateStart")
    if isinstance(year, int):
        return f"{year // 10 * 10}s"
    return "undated"


def series_stem(title: str) -> str:
    text = title or ""
    text = re.sub(r"\b(18|19|20)\d{2}[-/.]\d{1,2}([-/.]\d{1,2})?\b", " ", text)
    text = re.sub(r"\b(18|19|20)\d{2}\b", " ", text)
    text = re.sub(r"\b(volume|vol\.?|number|no\.?|issue|nº|nr\.?)\s*[\w.-]+\b", " ", text, flags=re.I)
    text = re.sub(r"\b\d{1,4}\b", " ", text)
    text = re.sub(r"\s*[,;:]\s*$", "", text)
    return norm(text)


def add_group(
    groups: dict[tuple[str, str], list[dict[str, Any]]],
    group_type: str,
    key: str,
    surface: dict[str, Any],
) -> None:
    if key:
        groups[(group_type, key)].append(surface)


def candidate_groups(surfaces: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for surface in surfaces:
        title = norm(surface.get("title", ""))
        source_name = norm(surface.get("sourceName", ""))
        source_id = norm(source_identifier(surface))
        collection = norm(source_collection(surface))
        region = norm(folder_key(surface, "region"))
        theme = norm(folder_key(surface, "theme"))
        medium = norm(folder_key(surface, "medium"))
        movement = norm(folder_key(surface, "movement"))
        stem = series_stem(surface.get("title", ""))

        add_group(groups, "same_title_within_source", f"{source_name}|{title}", surface)
        if source_id:
            add_group(groups, "same_source_identifier", f"{source_name}|{source_id}", surface)
        add_group(groups, "same_series_stem", f"{source_name}|{stem}", surface)
        if collection:
            add_group(groups, "same_source_collection", f"{source_name}|{collection}|{decade(surface)}", surface)
        add_group(groups, "folder_cell_decade", f"{region}|{theme}|{medium}|{movement}|{decade(surface)}", surface)
    return groups


def image_rank(state: str) -> int:
    return {"IMG03": 5, "IMG02": 4, "IMG01": 3, "IMG00": 2, "IMG04": 1}.get(state, 0)


def parent_key(surface: dict[str, Any]) -> tuple[int, int, int, str]:
    return (
        score(surface),
        source_text_len(surface),
        image_rank(image_state(surface)),
        surface.get("title", ""),
    )


def date_span(items: list[dict[str, Any]]) -> str:
    years: list[int] = []
    for item in items:
        for key in ("dateStart", "dateEnd"):
            value = item.get(key)
            if isinstance(value, int):
                years.append(value)
    if not years:
        return "undated"
    start, end = min(years), max(years)
    return str(start) if start == end else f"{start}-{end}"


def concise(values: list[str], max_items: int = 6) -> str:
    seen: list[str] = []
    for value in values:
        value = str(value or "").strip()
        if value and value not in seen:
            seen.append(value)
    if len(seen) <= max_items:
        return "; ".join(seen)
    return "; ".join(seen[:max_items]) + f"; +{len(seen) - max_items} more"


def group_confidence(group_type: str, items: list[dict[str, Any]]) -> str:
    if group_type in {"same_source_identifier", "same_title_within_source"}:
        return "high"
    if group_type in {"same_series_stem", "same_source_collection"}:
        return "medium"
    if len(items) >= 5:
        return "medium"
    return "low"


def recommended_action(items: list[dict[str, Any]]) -> str:
    parent = max(items, key=parent_key)
    parent_score = score(parent)
    support_count = sum(
        1
        for item in items
        if item.get("surfaceDisposition") in {"support_packet_appendix_text", "merge_candidate_support_packet"}
    )
    main_count = sum(1 for item in items if item.get("surfaceDisposition") == "main_sheet")
    if parent_score >= 75 and main_count >= 1 and support_count >= 1:
        return "canonical_main_with_support_children"
    if parent_score >= 75 and len(items) >= 3:
        return "canonical_main_with_source_register"
    if len(items) >= 4:
        return "compound_main_candidate"
    if support_count:
        return "support_packet_cluster"
    return "review_only"


def gap_flags(items: list[dict[str, Any]]) -> str:
    flags: list[str] = []
    if not any(image_state(item) in {"IMG01", "IMG02", "IMG03"} for item in items):
        flags.append("needs_image")
    if max(source_text_len(item) for item in items) < 180:
        flags.append("needs_text")
    if any(image_state(item) == "IMG00" for item in items):
        flags.append("needs_rights")
    if len({folder_key(item, "region") for item in items if folder_key(item, "region")}) > 1:
        flags.append("multi_region_review")
    if not flags:
        flags.append("coverage_ready")
    return ";".join(flags)


def evidence_basis(group_type: str) -> str:
    return {
        "same_title_within_source": "Same normalized title inside the same source.",
        "same_source_identifier": "Same source identifier inside the same source.",
        "same_series_stem": "Shared title stem after removing dates, issue numbers, and serial markers.",
        "same_source_collection": "Same source collection and decade bucket.",
        "folder_cell_decade": "Same region/theme/medium/movement cell and decade; weak grouping for coverage planning.",
    }.get(group_type, "Candidate grouping rule.")


def member_role(item: dict[str, Any], parent_id: str) -> tuple[str, str]:
    if item.get("surfaceId") == parent_id:
        return "parent_candidate", "canonical_sheet"
    disposition = item.get("surfaceDisposition")
    if disposition == "merge_candidate_support_packet":
        return "support_fragment", "child_card_or_slip"
    if disposition == "support_packet_appendix_text":
        return "support_record", "appendix_or_text_leaf"
    if image_state(item) in {"IMG01", "IMG02", "IMG03"}:
        return "plate_variant", "child_plate"
    return "source_supplement", "source_register_row"


def build_rows(payload: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    surfaces = [s for s in payload.get("surfaces", []) if s.get("surfaceType") in {"sheet", "card", "fallback_stub"}]
    raw_groups = candidate_groups(surfaces)
    group_rows: list[dict[str, str]] = []
    member_rows: list[dict[str, str]] = []
    index = 1

    for (group_type, key), items in sorted(raw_groups.items()):
        # Folder-cell grouping is intentionally weaker; require more evidence.
        min_count = 4 if group_type == "folder_cell_decade" else 2
        if len(items) < min_count:
            continue
        if group_type == "same_series_stem" and len(key.split("|")[-1]) < 8:
            continue

        parent = max(items, key=parent_key)
        group_id = f"GRP{index:04d}"
        index += 1
        parent_id = parent.get("surfaceId", "")
        source_names = concise([item.get("sourceName", "") for item in items])
        primary_folder = concise(
            [
                folder_key(parent, "region"),
                folder_key(parent, "theme"),
                folder_key(parent, "medium"),
                folder_key(parent, "movement"),
            ],
            max_items=4,
        )
        group_rows.append(
            {
                "group_id": group_id,
                "group_type": group_type,
                "group_key": key,
                "confidence": group_confidence(group_type, items),
                "member_count": str(len(items)),
                "proposed_parent_surface_id": parent_id,
                "proposed_parent_title": parent.get("title", ""),
                "parent_score": str(score(parent)),
                "date_span": date_span(items),
                "source_names": source_names,
                "primary_folder": primary_folder,
                "member_dispositions": "; ".join(f"{k}: {v}" for k, v in sorted(Counter(item.get("surfaceDisposition", "missing") for item in items).items())),
                "image_states": "; ".join(f"{k}: {v}" for k, v in sorted(Counter(image_state(item) for item in items).items())),
                "recommended_action": recommended_action(items),
                "coverage_gap_flags": gap_flags(items),
                "evidence_basis": evidence_basis(group_type),
                "member_surface_ids": ";".join(item.get("surfaceId", "") for item in items),
            }
        )
        for item in sorted(items, key=lambda s: (s.get("dateStart") or 9999, s.get("title", ""), s.get("surfaceId", ""))):
            role, display_role = member_role(item, parent_id)
            member_rows.append(
                {
                    "group_id": group_id,
                    "surface_id": item.get("surfaceId", ""),
                    "membership_role": role,
                    "display_role": display_role,
                    "membership_confidence": group_confidence(group_type, items),
                    "title": item.get("title", ""),
                    "date_text": item.get("dateText", ""),
                    "source_name": item.get("sourceName", ""),
                    "surface_disposition": item.get("surfaceDisposition", ""),
                    "completeness_score": str(score(item)),
                    "image_state": image_state(item),
                    "source_url": item.get("sourceUrl", ""),
                }
            )
    return group_rows, member_rows


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            {
                field: str(row.get(field, "") or "").strip()
                for field in fields
            }
            for row in rows
        )


def write_report(groups: list[dict[str, str]], members: list[dict[str, str]]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    type_counts = Counter(row["group_type"] for row in groups)
    action_counts = Counter(row["recommended_action"] for row in groups)
    gap_counts = Counter(flag for row in groups for flag in row["coverage_gap_flags"].split(";") if flag)
    confidence_counts = Counter(row["confidence"] for row in groups)
    lines = [
        "# Surface Grouping Audit v1",
        "",
        f"Date: {ACCESS_DATE}",
        "",
        "This audit proposes group candidates before the next broad coverage pass. It does not mutate public surfaces. Groups are archive organization units: they decide where loose leaves, support packets, child cards, appendices, and bookmarks should attach.",
        "",
        "## Summary",
        "",
        f"- Candidate groups: {len(groups)}",
        f"- Candidate memberships: {len(members)}",
        "",
        "## Group Types",
        "",
    ]
    for key, count in type_counts.most_common():
        lines.append(f"- `{key}`: {count}")
    lines.extend(["", "## Recommended Actions", ""])
    for key, count in action_counts.most_common():
        lines.append(f"- `{key}`: {count}")
    lines.extend(["", "## Coverage Gap Flags", ""])
    for key, count in gap_counts.most_common():
        lines.append(f"- `{key}`: {count}")
    lines.extend(["", "## Confidence", ""])
    for key, count in confidence_counts.most_common():
        lines.append(f"- `{key}`: {count}")
    lines.extend(["", "## High-Value Next Groups", ""])
    priority = sorted(
        groups,
        key=lambda row: (
            "needs_text" not in row["coverage_gap_flags"],
            "needs_image" not in row["coverage_gap_flags"],
            -int(row["member_count"]),
            row["group_type"],
        ),
    )
    for row in priority[:25]:
        lines.append(
            f"- {row['group_id']} | {row['group_type']} | {row['member_count']} members | "
            f"{row['recommended_action']} | {row['coverage_gap_flags']} | {row['proposed_parent_title']}"
        )
    lines.extend(
        [
            "",
            "## Use In Next Coverage Pass",
            "",
            "The 1970-2026 pass should use these groups as targets. New records should first try to attach to a group by source identifier, title stem, source collection, series/campaign/event, or folder-cell decade. Only records that cannot responsibly attach should create new groups.",
            "",
            "Group-level gaps should drive capture queries:",
            "",
            "- `needs_image`: search IIIF, source viewer, Commons/open image, or local collection image endpoints.",
            "- `needs_text`: search catalogue essays, collection notes, OCR pages, exhibition text, or institutional context.",
            "- `needs_rights`: search item-level rights, source policy, IIIF manifest rights, or access statements.",
            "- `multi_region_review`: do not collapse into a single national narrative without evidence.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = read_payload()
    groups, members = build_rows(payload)
    write_csv(GROUPS_CSV, GROUP_FIELDS, groups)
    write_csv(MEMBERS_CSV, MEMBER_FIELDS, members)
    write_report(groups, members)
    print(f"groups={len(groups)}")
    print(f"memberships={len(members)}")
    print(f"wrote {GROUPS_CSV.relative_to(ROOT)}")
    print(f"wrote {MEMBERS_CSV.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
