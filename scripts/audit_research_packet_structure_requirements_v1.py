#!/usr/bin/env python3
"""Audit research-packet structure requirements before any packet rebuild.

This non-mutating audit translates the final-phase packet methodology into a
data review queue. It estimates cover-main, normal-main, sub, appendix, card,
text, folder-directory, and reading-note requirements from existing
main/sub/text packet relation review data. It writes CSVs and a report only.
"""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

IN_ROLE_QUEUE = DATA / "prefreeze_main_sub_text_packet_relation_role_queue_v1.csv"
IN_CLUSTER_AUDIT = DATA / "prefreeze_main_sub_text_packet_relation_cluster_audit_v1.csv"

OUT_REQUIREMENTS = DATA / "research_packet_structure_requirements_v1.csv"
OUT_NODE_CONTRACT = DATA / "research_packet_node_contract_v1.csv"
OUT_READING_NOTES = DATA / "research_packet_reading_note_requirements_v1.csv"
OUT_FRONTEND = DATA / "research_packet_frontend_layout_contract_v1.csv"
OUT_SUMMARY = DATA / "research_packet_structure_requirements_summary_v1.csv"
OUT_REPORT = DOCS / "RESEARCH_PACKET_STRUCTURE_REQUIREMENTS_v1.md"

SUMMARY_FIELDS = ["metric", "value", "notes"]
REQUIREMENT_FIELDS = [
    "cluster_key",
    "source_family",
    "region",
    "theme",
    "five_year_bucket",
    "actual_year_span",
    "global_scope_policy",
    "cluster_size",
    "role_rows",
    "packet_scale",
    "packet_readiness",
    "cover_main_requirement",
    "normal_main_policy",
    "normal_main_target_min",
    "sub_target_min",
    "sub_target_max",
    "appendix_policy",
    "card_policy",
    "minimum_text_pages",
    "editorial_page_requirement",
    "reading_note_requirement",
    "folder_directory_mode",
    "content_tree_depth",
    "layout_family",
    "node_explanation_required",
    "reason",
]
NODE_FIELDS = [
    "node_type",
    "parent_allowed",
    "children_allowed",
    "text_allowed",
    "card_allowed",
    "node_summary_required",
    "relation_note_required",
    "source_basis_required",
    "frontend_display_role",
]
READING_FIELDS = [
    "cluster_key",
    "packet_scale",
    "reading_note_type",
    "editorial_page_required",
    "must_include",
    "avoid",
    "curation_reason",
]
FRONTEND_FIELDS = [
    "layout_area",
    "requirement",
    "applies_to",
    "notes",
]


def clean(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def as_int(value: object) -> int:
    try:
        return int(float(clean(value) or "0"))
    except ValueError:
        return 0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def year_span(rows: list[dict[str, str]], cluster: dict[str, str]) -> str:
    years = sorted({as_int(row.get("year")) for row in rows if as_int(row.get("year")) > 0})
    if years:
        return f"{years[0]}-{years[-1]}"
    start = as_int(cluster.get("year_min"))
    end = as_int(cluster.get("year_max"))
    if start and end:
        return f"{start}-{end}"
    return ""


def source_family_from_key(key: str) -> str:
    parts = clean(key).split("|")
    return parts[2] if len(parts) > 2 else ""


def region_from_key(key: str) -> str:
    parts = clean(key).split("|")
    return parts[0] if parts else ""


def global_scope_policy(source_family: str, region: str) -> str:
    folded_family = clean(source_family).casefold()
    folded_region = clean(region).casefold()
    is_global = "transnational" in folded_region or folded_region.startswith("global") or folded_region.startswith("unresolved")
    if not is_global:
        return "region_specific_or_not_global"
    if any(term in folded_family for term in ("another graphic", "letterform", "design reviewed", "naidoc", "desain", "gala")):
        return "global_site_acceptable_with_relation_review"
    if any(term in folded_family for term in ("internet archive", "wikimedia commons", "contentdm", "library", "gallica", "bnf")):
        return "global_host_requires_scope_review"
    return "global_scope_manual_review"


def packet_scale(cluster_size: int, role_rows: int, sub_candidates: int) -> str:
    effective = max(cluster_size, role_rows, sub_candidates)
    if effective >= 13 or sub_candidates >= 10:
        return "large"
    if effective >= 6 or sub_candidates >= 3:
        return "medium"
    if effective >= 2:
        return "small"
    return "single_or_micro"


def text_target(scale: str, generated_text_rows: int, policy: str) -> tuple[int, str]:
    if scale == "large":
        return 15, "mandatory_editorial_page"
    if scale == "medium":
        return 5, "mandatory_editorial_page"
    if scale == "small":
        if generated_text_rows == 0 or policy != "region_specific_or_not_global":
            return 2, "recommended_editorial_page"
        return 2, "optional_editorial_page"
    return 1, "optional_editorial_page"


def role_counts(rows: list[dict[str, str]]) -> Counter[str]:
    return Counter(clean(row.get("proposed_relation_role")) for row in rows)


def readiness(rows: list[dict[str, str]], cluster: dict[str, str], policy: str) -> str:
    lane = clean(cluster.get("packet_relation_lane"))
    confidence = clean(cluster.get("packet_confidence"))
    if policy == "global_host_requires_scope_review":
        return "scope_review_before_packet"
    if lane == "strong_packet_candidate" and confidence == "high":
        return "structure_candidate_requires_manual_packet_review"
    if lane == "packet_parentage_review":
        return "parentage_signal_needed"
    if lane == "card_context_cluster":
        return "card_or_appendix_pool"
    if lane == "macro_cluster_needs_split":
        return "scope_review_before_packet"
    if any(clean(row.get("relation_apply_readiness")) == "eligible_for_next_sandbox_review" for row in rows):
        return "eligible_rows_but_packet_shape_unresolved"
    return "method_review_only"


def requirement_rows(role_rows: list[dict[str, str]], clusters: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows_by_cluster: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in role_rows:
        rows_by_cluster[clean(row.get("cluster_key"))].append(row)

    out: list[dict[str, Any]] = []
    for cluster in clusters:
        key = clean(cluster.get("cluster_key"))
        rows = rows_by_cluster.get(key, [])
        if not rows:
            continue
        region = clean(cluster.get("region")) or region_from_key(key)
        family = clean(cluster.get("source_family")) or source_family_from_key(key)
        counts = role_counts(rows)
        anchor_rows = counts.get("candidate_packet_anchor", 0) + counts.get("provisional_main_anchor_needs_text", 0) + counts.get("anchor_or_sibling_review", 0)
        sub_rows = counts.get("packet_member_review", 0) + counts.get("sub_under_packet_candidate", 0)
        card_rows = counts.get("card_context_candidate", 0)
        appendix_rows = counts.get("text_or_appendix_candidate", 0) + sum(1 for row in rows if "appendix" in clean(row.get("proposed_relation_role")))
        scale = packet_scale(as_int(cluster.get("cluster_size")), len(rows), sub_rows)
        policy = global_scope_policy(family, region)
        min_text, editorial = text_target(scale, appendix_rows + counts.get("provisional_main_anchor_needs_text", 0), policy)
        if scale == "large":
            sub_min, sub_max = 10, max(10, sub_rows or 10)
        elif scale == "medium":
            sub_min, sub_max = 3, 5
        elif scale == "small":
            sub_min, sub_max = 1, 2
        else:
            sub_min, sub_max = 0, 1
        if scale in {"medium", "large"} or policy != "region_specific_or_not_global":
            cover_req = "cover_main_required"
        elif scale == "small":
            cover_req = "cover_main_recommended"
        else:
            cover_req = "cover_main_optional"
        if anchor_rows > 1:
            normal_policy = "multiple_normal_mains_allowed_under_cover"
            normal_target = min(anchor_rows, max(1, sub_min))
        elif anchor_rows == 1:
            normal_policy = "single_normal_main_expected"
            normal_target = 1
        else:
            normal_policy = "normal_main_anchor_selection_needed"
            normal_target = 1 if sub_rows else 0
        reason_bits = [
            f"scale={scale}",
            f"sub_candidates={sub_rows}",
            f"card_candidates={card_rows}",
            f"scope={policy}",
            f"lane={clean(cluster.get('packet_relation_lane'))}",
        ]
        out.append(
            {
                "cluster_key": key,
                "source_family": family,
                "region": region,
                "theme": clean(cluster.get("theme")),
                "five_year_bucket": clean(cluster.get("five_year_bucket")),
                "actual_year_span": year_span(rows, cluster),
                "global_scope_policy": policy,
                "cluster_size": clean(cluster.get("cluster_size")),
                "role_rows": len(rows),
                "packet_scale": scale,
                "packet_readiness": readiness(rows, cluster, policy),
                "cover_main_requirement": cover_req,
                "normal_main_policy": normal_policy,
                "normal_main_target_min": normal_target,
                "sub_target_min": sub_min,
                "sub_target_max": sub_max,
                "appendix_policy": "appendix_can_have_text_and_card; use_for_weaker_than_sub_evidence",
                "card_policy": "card_is_leaf_visual_or_excerpt_unit",
                "minimum_text_pages": min_text,
                "editorial_page_requirement": editorial,
                "reading_note_requirement": "curated_packet_reading_note_required" if editorial.startswith("mandatory") or cover_req == "cover_main_required" else "curated_packet_reading_note_recommended",
                "folder_directory_mode": "packet_tree_directory",
                "content_tree_depth": "cover>normal_main>(text|sub>text|appendix>text|card)",
                "layout_family": "large_packet_tree" if scale == "large" else "medium_packet_tree" if scale == "medium" else "small_packet_tree",
                "node_explanation_required": "node_summary; relation_to_parent; source_basis; confidence_status",
                "reason": "; ".join(reason_bits),
            }
        )
    out.sort(
        key=lambda row: (
            {"large": 0, "medium": 1, "small": 2, "single_or_micro": 3}.get(clean(row.get("packet_scale")), 9),
            -as_int(row.get("role_rows")),
            clean(row.get("cluster_key")),
        )
    )
    return out


def node_contract_rows() -> list[dict[str, str]]:
    return [
        {
            "node_type": "cover_main",
            "parent_allowed": "packet_root",
            "children_allowed": "normal_main; appendix; text",
            "text_allowed": "yes",
            "card_allowed": "no_direct_card_except_index_thumbnail",
            "node_summary_required": "yes",
            "relation_note_required": "scope_rationale",
            "source_basis_required": "yes",
            "frontend_display_role": "packet_first_page_and_tree_root",
        },
        {
            "node_type": "normal_main",
            "parent_allowed": "cover_main; packet_root_for_standalone",
            "children_allowed": "text; sub_sheet; appendix; card",
            "text_allowed": "yes",
            "card_allowed": "yes",
            "node_summary_required": "yes",
            "relation_note_required": "yes",
            "source_basis_required": "yes",
            "frontend_display_role": "research_bearing_main_node",
        },
        {
            "node_type": "sub_sheet",
            "parent_allowed": "normal_main",
            "children_allowed": "text; appendix; card",
            "text_allowed": "yes",
            "card_allowed": "yes",
            "node_summary_required": "yes",
            "relation_note_required": "yes",
            "source_basis_required": "yes",
            "frontend_display_role": "strong_relation_child_node",
        },
        {
            "node_type": "appendix",
            "parent_allowed": "normal_main; sub_sheet",
            "children_allowed": "text; card",
            "text_allowed": "yes",
            "card_allowed": "yes",
            "node_summary_required": "yes",
            "relation_note_required": "evidence_role",
            "source_basis_required": "yes",
            "frontend_display_role": "supporting_evidence_node",
        },
        {
            "node_type": "card",
            "parent_allowed": "normal_main; sub_sheet; appendix",
            "children_allowed": "none",
            "text_allowed": "short_caption_only",
            "card_allowed": "not_applicable",
            "node_summary_required": "short",
            "relation_note_required": "optional",
            "source_basis_required": "yes",
            "frontend_display_role": "leaf_visual_or_excerpt_unit",
        },
        {
            "node_type": "text",
            "parent_allowed": "cover_main; normal_main; sub_sheet; appendix",
            "children_allowed": "none",
            "text_allowed": "not_applicable",
            "card_allowed": "no",
            "node_summary_required": "title_and_purpose",
            "relation_note_required": "text_purpose",
            "source_basis_required": "if source-specific",
            "frontend_display_role": "pure_editorial_or_explanatory_page",
        },
    ]


def reading_rows(requirements: list[dict[str, Any]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in requirements:
        scale = clean(row.get("packet_scale"))
        global_policy = clean(row.get("global_scope_policy"))
        must = [
            "packet_scope",
            "recommended_reading_path",
            "core_nodes",
            "appendix_card_evidence_policy",
            "rights_image_state_summary",
        ]
        if global_policy != "region_specific_or_not_global":
            must.append("global_transnational_scope_rationale")
        if clean(row.get("editorial_page_requirement")).startswith("mandatory"):
            must.append("editorial_page")
        out.append(
            {
                "cluster_key": clean(row.get("cluster_key")),
                "packet_scale": scale,
                "reading_note_type": "large_packet_editorial_note" if scale == "large" else "medium_packet_editorial_note" if scale == "medium" else "small_packet_reading_note",
                "editorial_page_required": "true" if clean(row.get("editorial_page_requirement")).startswith("mandatory") else "recommended",
                "must_include": "; ".join(must),
                "avoid": "engineering_register_language; raw_status_dump; forced_country_assignment; rights_upgrade_claims",
                "curation_reason": clean(row.get("reason")),
            }
        )
    return out


def frontend_contract_rows() -> list[dict[str, str]]:
    return [
        {
            "layout_area": "left_content_panel",
            "requirement": "render_packet_tree",
            "applies_to": "folder and surface routes",
            "notes": "Show cover main, normal mains, sub sheets, appendices, cards, and text counts; support hover/click navigation.",
        },
        {
            "layout_area": "folder_directory",
            "requirement": "show_reader_facing_packet_directory",
            "applies_to": "folder routes",
            "notes": "Replace engineering folder register language with packet tree summary, counts, scope, source family, rights/image state, and unresolved flags.",
        },
        {
            "layout_area": "reading_note",
            "requirement": "curated_editorial_reading_note",
            "applies_to": "cover main, folder, medium/large packets",
            "notes": "Explain what to study, reading path, core vs appendix/card evidence, global scope rationale, and uncertainty.",
        },
        {
            "layout_area": "text_page",
            "requirement": "pure_explanatory_text_page",
            "applies_to": "cover/main/sub/appendix children",
            "notes": "Text is expanded prose; node-level summaries still exist outside text pages.",
        },
        {
            "layout_area": "appendix",
            "requirement": "appendix_can_contain_text_and_cards",
            "applies_to": "main and sub nodes",
            "notes": "Appendix is weaker evidence than sub, but can have its own text/card children.",
        },
        {
            "layout_area": "assistant_or_search",
            "requirement": "functional_search_navigation_helper",
            "applies_to": "packet routes",
            "notes": "Does not require WebLLM; can use packet metadata, reading notes, and search to guide navigation.",
        },
    ]


def summary_rows(requirements: list[dict[str, Any]], reading: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {"metric": "scope", "value": "non_mutating_research_packet_structure_requirements", "notes": "No rebuild, role override, image download, or rights/image-state change."},
        {"metric": "packet_requirement_rows", "value": len(requirements), "notes": "Cluster-level packet structure requirements."},
        {"metric": "reading_note_requirement_rows", "value": len(reading), "notes": "Curated reading-note requirement rows."},
    ]
    for key, count in Counter(clean(row.get("packet_scale")) for row in requirements).most_common():
        rows.append({"metric": f"packet_scale:{key}", "value": count, "notes": "Packet scale distribution."})
    for key, count in Counter(clean(row.get("cover_main_requirement")) for row in requirements).most_common():
        rows.append({"metric": f"cover_main:{key}", "value": count, "notes": "Cover main requirement distribution."})
    for key, count in Counter(clean(row.get("editorial_page_requirement")) for row in requirements).most_common():
        rows.append({"metric": f"editorial:{key}", "value": count, "notes": "Editorial page requirement distribution."})
    for key, count in Counter(clean(row.get("global_scope_policy")) for row in requirements).most_common():
        rows.append({"metric": f"global_scope_policy:{key}", "value": count, "notes": "Global scope policy distribution."})
    total_text = sum(as_int(row.get("minimum_text_pages")) for row in requirements)
    rows.append({"metric": "minimum_text_pages_total", "value": total_text, "notes": "Estimated minimum text pages across requirement rows."})
    return rows


def write_report(summary: list[dict[str, Any]], requirements: list[dict[str, Any]]) -> None:
    lines = [
        "# Research Packet Structure Requirements v1",
        "",
        "Scope: non-mutating audit for cover/normal main/sub/text/appendix/card packet requirements.",
        "",
        "This pass does not rebuild payloads, apply overrides, download images, or change rights/image states.",
        "",
        "## Summary",
        "",
    ]
    for row in summary[:80]:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(
        [
            "",
            "## Method Commitments",
            "",
            "- Normal main is not automatically demoted when a cover main organizes it.",
            "- Cover main is the packet first page and curated entry point.",
            "- Text pages are pure explanatory pages, but node-level summaries and relation notes remain required.",
            "- Sub sheets can contain appendices; appendices can contain text and cards.",
            "- Medium and large packets require an editorial reading page.",
            "- Global/transnational scope is valid when justified; it must not be forced into a country folder without evidence.",
            "",
            "## Largest Requirement Rows",
            "",
        ]
    )
    for row in requirements[:20]:
        lines.append(
            f"- {row['cluster_key']}: scale={row['packet_scale']}; cover={row['cover_main_requirement']}; "
            f"sub_target={row['sub_target_min']}-{row['sub_target_max']}; min_text={row['minimum_text_pages']}; "
            f"editorial={row['editorial_page_requirement']}; scope={row['global_scope_policy']}"
        )
    lines.extend(
        [
            "",
            "## Frontend Implication",
            "",
            "- Left Content should render packet tree, not a flat register.",
            "- Folder Directory should show packet structure and counts, not engineering-only status.",
            "- Reading Note should become curated editorial guidance.",
            "- Assistant/search can be functional navigation over packet metadata and reading notes; WebLLM is optional.",
            "",
            "## Safety",
            "",
            "- No rights/source authority/image-state upgrades were made.",
            "- No source-family signal may override macro/global scope review.",
            "- No packet role is applied by this audit.",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    role_rows = read_csv(IN_ROLE_QUEUE)
    cluster_rows = read_csv(IN_CLUSTER_AUDIT)
    requirements = requirement_rows(role_rows, cluster_rows)
    nodes = node_contract_rows()
    reading = reading_rows(requirements)
    frontend = frontend_contract_rows()
    summary = summary_rows(requirements, reading)

    write_csv(OUT_REQUIREMENTS, requirements, REQUIREMENT_FIELDS)
    write_csv(OUT_NODE_CONTRACT, nodes, NODE_FIELDS)
    write_csv(OUT_READING_NOTES, reading, READING_FIELDS)
    write_csv(OUT_FRONTEND, frontend, FRONTEND_FIELDS)
    write_csv(OUT_SUMMARY, summary, SUMMARY_FIELDS)
    write_report(summary, requirements)

    print(f"packet_requirement_rows={len(requirements)}")
    print(f"reading_note_requirement_rows={len(reading)}")
    print(f"node_contract_rows={len(nodes)}")
    print(f"frontend_contract_rows={len(frontend)}")
    print(f"wrote {OUT_REQUIREMENTS.relative_to(ROOT)}")
    print(f"wrote {OUT_NODE_CONTRACT.relative_to(ROOT)}")
    print(f"wrote {OUT_READING_NOTES.relative_to(ROOT)}")
    print(f"wrote {OUT_FRONTEND.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
