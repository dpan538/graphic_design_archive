#!/usr/bin/env python3
"""Build non-mutating cover/editorial packet sandbox drafts.

This pass consumes only the high-priority anchor seed plan and copied seed
candidate rows. It drafts cover/editorial review artifacts for the
cover_editorial_seed_ready lane and writes sandbox CSVs plus a capture report.

It does not apply packet roles, rebuild official payloads, write frontend
mirrors, download images, or change rights/image states.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

IN_PLAN = DATA / "research_packet_high_priority_anchor_seed_plan_v1.csv"
IN_CANDIDATES = DATA / "research_packet_high_priority_anchor_seed_candidates_v1.csv"

OUT_SANDBOX = DATA / "research_packet_cover_editorial_sandbox_v1.csv"
OUT_TREE = DATA / "research_packet_cover_editorial_tree_sandbox_v1.csv"
OUT_TEXT = DATA / "research_packet_cover_editorial_text_sandbox_v1.csv"
OUT_SUMMARY = DATA / "research_packet_cover_editorial_sandbox_summary_v1.csv"
OUT_REPORT = DOCS / "RESEARCH_PACKET_COVER_EDITORIAL_SANDBOX_v1.md"

READY_LANE = "cover_editorial_seed_ready"

SANDBOX_FIELDS = [
    "packet_id",
    "cluster_key",
    "sandbox_lane",
    "review_status",
    "packet_cover_title_draft",
    "cover_main_scope_summary",
    "normal_main_candidate_surface_id",
    "normal_main_candidate_title",
    "normal_main_candidate_year",
    "normal_main_candidate_source_family",
    "normal_main_candidate_image_state",
    "normal_main_candidate_basis",
    "sub_card_candidate_count_from_seed_rows",
    "sub_candidate_surface_ids_from_seed_rows",
    "sub_candidate_titles_from_seed_rows",
    "card_candidate_count_from_plan",
    "card_candidate_note",
    "rights_image_state_summary",
    "curated_reading_note_outline",
    "editorial_page_outline",
    "relation_uncertainty_notes",
    "what_must_not_be_claimed",
    "manual_review_next_step",
    "official_rebuild_status",
]

TREE_FIELDS = [
    "packet_id",
    "cluster_key",
    "node_id",
    "parent_node_id",
    "node_type",
    "candidate_surface_id",
    "candidate_rank",
    "node_title",
    "year",
    "source_family",
    "image_state",
    "proposed_relation_role",
    "candidate_use",
    "node_summary",
    "relation_to_parent",
    "source_basis",
    "scope_policy",
    "confidence_status",
    "manual_check",
]

TEXT_FIELDS = [
    "packet_id",
    "cluster_key",
    "text_id",
    "attach_to_node_id",
    "text_type",
    "title",
    "outline",
    "source_basis",
    "required_manual_review",
    "do_not_claim",
    "official_status",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]


def clean(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def as_int(value: object) -> int:
    try:
        return int(float(clean(value) or "0"))
    except ValueError:
        return 0


def as_float(value: object) -> float:
    try:
        return float(clean(value) or "0")
    except ValueError:
        return 0.0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def by_cluster(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        out[clean(row.get("cluster_key"))].append(row)
    return out


def packet_title(row: dict[str, str]) -> str:
    region = clean(row.get("region"))
    theme = clean(row.get("theme"))
    span = clean(row.get("actual_year_span")) or clean(row.get("five_year_bucket"))
    return f"{region}: {theme}, {span}"


def image_state_summary(candidates: list[dict[str, str]]) -> str:
    counts = Counter(clean(row.get("image_state")) or "UNKNOWN" for row in candidates)
    parts = [f"{key}={value}" for key, value in sorted(counts.items())]
    return (
        "Seed candidate image states: "
        + ", ".join(parts)
        + ". Rights and image-state values are copied from seed inputs only; no upgrade or download was made."
    )


def candidate_label(row: dict[str, str]) -> str:
    rank = clean(row.get("candidate_rank"))
    surface_id = clean(row.get("surface_id"))
    title = clean(row.get("title"))
    role = clean(row.get("proposed_relation_role"))
    image_state = clean(row.get("image_state"))
    score = clean(row.get("anchor_review_score"))
    return f"rank {rank} {surface_id}: {title} ({role}; {image_state}; score {score})"


def review_scope_policy(row: dict[str, str]) -> str:
    region = clean(row.get("region"))
    if region.casefold().startswith("global"):
        return "global_site_acceptable_with_relation_review"
    return "region_specific_or_not_global"


def reading_note_outline(row: dict[str, str], normal: dict[str, str], candidate_count: int) -> str:
    title = packet_title(row)
    top_title = clean(normal.get("title")) or clean(row.get("top_candidate_title"))
    return (
        f"Frame {title} as a reader-facing packet draft; start with {top_title} as an anchor candidate; "
        f"compare {candidate_count} copied seed candidates as possible member, sub, card, or appendix evidence; "
        "separate source-family grouping from proven campaign, series, project, or institutional relation; "
        "close with rights/image-state limits and unresolved relation questions."
    )


def editorial_outline(row: dict[str, str]) -> str:
    return (
        "1. Packet scope and why this cluster is being reviewed. "
        "2. Source-family evidence and actual year span. "
        "3. Normal-main anchor decision to confirm. "
        "4. Candidate relation map for sub/card/appendix review. "
        "5. Rights and image-state reading limits. "
        "6. Claims to exclude until manual review and official rebuild."
    )


def uncertainty_notes(row: dict[str, str], candidates: list[dict[str, str]]) -> str:
    risks = sorted({clean(item.get("risk_flags")) for item in candidates if clean(item.get("risk_flags"))})
    card_count = as_int(row.get("card_candidate_count"))
    notes = [
        "Top candidate is a normal-main candidate only and still needs manual anchor confirmation.",
        "Same source family, region, period, or platform is not enough to prove sub-sheet relation.",
        "Ranks below the top candidate need explicit campaign, series, project, institution, or source-side grouping evidence.",
    ]
    if card_count:
        notes.append(
            f"Plan reports {card_count} card candidates in the wider cluster; copied seed rows do not exhaust card/support review."
        )
    if risks:
        notes.append("Candidate risk flags to inspect: " + "; ".join(risks) + ".")
    return " ".join(notes)


def must_not_claim(row: dict[str, str]) -> str:
    return (
        "Do not claim that cover_main, normal_main, sub_sheet, card, appendix, or text roles have been applied. "
        "Do not claim final packet completeness, final rights clearance, source-authority upgrade, image-state upgrade, "
        "image download, or official payload/frontend rebuild. Do not claim a shared campaign, series, project, or "
        "institutional relation unless manual review confirms it."
    )


def node_type_for_candidate(row: dict[str, str]) -> str:
    role = clean(row.get("proposed_relation_role"))
    if role == "sub_under_packet_candidate":
        return "sub_sheet_candidate"
    if role == "card_context_candidate":
        return "card_candidate"
    return "packet_member_or_card_candidate"


def make_sandbox_rows(
    plan_rows: list[dict[str, str]],
    candidates_by_key: dict[str, list[dict[str, str]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    ready_rows = [row for row in plan_rows if clean(row.get("seed_lane")) == READY_LANE]
    ready_rows.sort(key=lambda row: (-as_float(row.get("top_anchor_review_score")), clean(row.get("cluster_key"))))

    sandbox_rows: list[dict[str, Any]] = []
    tree_rows: list[dict[str, Any]] = []
    text_rows: list[dict[str, Any]] = []

    for index, plan in enumerate(ready_rows, start=1):
        key = clean(plan.get("cluster_key"))
        packet_id = f"cover_editorial_sandbox_{index:03d}"
        candidates = sorted(
            candidates_by_key.get(key, []),
            key=lambda row: (as_int(row.get("candidate_rank")), -as_float(row.get("anchor_review_score"))),
        )
        if not candidates:
            candidates = [
                {
                    "candidate_rank": "1",
                    "surface_id": clean(plan.get("top_candidate_surface_id")),
                    "year": "",
                    "title": clean(plan.get("top_candidate_title")),
                    "image_state": "",
                    "source_family": clean(plan.get("source_family")),
                    "source_name": "",
                    "proposed_relation_role": clean(plan.get("top_candidate_role")),
                    "anchor_review_score": clean(plan.get("top_anchor_review_score")),
                    "risk_flags": clean(plan.get("top_candidate_risk_flags")),
                    "candidate_use": "top_anchor_review_candidate",
                }
            ]
        normal = candidates[0]
        secondary = candidates[1:]
        title = packet_title(plan)
        cover_node_id = f"{packet_id}::cover_main_sandbox"
        normal_node_id = f"{packet_id}::normal_main_candidate::{clean(normal.get('surface_id'))}"
        sub_ids = "; ".join(clean(item.get("surface_id")) for item in secondary)
        sub_titles = " | ".join(clean(item.get("title")) for item in secondary)
        card_count = as_int(plan.get("card_candidate_count"))
        card_note = (
            f"{card_count} card candidates reported by the high-priority seed plan; inspect wider candidate queue before card assignment."
            if card_count
            else "No card pressure reported by the high-priority seed plan; keep all copied non-top rows provisional."
        )
        scope_summary = (
            f"Medium sandbox packet draft for {clean(plan.get('region'))} / {clean(plan.get('theme'))} "
            f"using {clean(plan.get('source_family'))} seed records from "
            f"{clean(plan.get('actual_year_span')) or clean(plan.get('five_year_bucket'))}. "
            "The cover draft frames a review scope only; packet roles remain unapplied."
        )
        reading_outline = reading_note_outline(plan, normal, len(candidates))
        editorial = editorial_outline(plan)
        uncertainty = uncertainty_notes(plan, candidates)
        exclusions = must_not_claim(plan)

        sandbox_rows.append(
            {
                "packet_id": packet_id,
                "cluster_key": key,
                "sandbox_lane": READY_LANE,
                "review_status": "human_cover_editorial_review_ready",
                "packet_cover_title_draft": title,
                "cover_main_scope_summary": scope_summary,
                "normal_main_candidate_surface_id": clean(normal.get("surface_id")),
                "normal_main_candidate_title": clean(normal.get("title")),
                "normal_main_candidate_year": clean(normal.get("year")),
                "normal_main_candidate_source_family": clean(normal.get("source_family")) or clean(plan.get("source_family")),
                "normal_main_candidate_image_state": clean(normal.get("image_state")),
                "normal_main_candidate_basis": "Top copied seed candidate; candidate only, not applied as normal_main.",
                "sub_card_candidate_count_from_seed_rows": len(secondary),
                "sub_candidate_surface_ids_from_seed_rows": sub_ids,
                "sub_candidate_titles_from_seed_rows": sub_titles,
                "card_candidate_count_from_plan": card_count,
                "card_candidate_note": card_note,
                "rights_image_state_summary": image_state_summary(candidates),
                "curated_reading_note_outline": reading_outline,
                "editorial_page_outline": editorial,
                "relation_uncertainty_notes": uncertainty,
                "what_must_not_be_claimed": exclusions,
                "manual_review_next_step": "Confirm packet title, confirm or reject normal-main anchor candidate, then separate sub/card/appendix evidence.",
                "official_rebuild_status": "blocked_until_manual_review_and_future_payload_rebuild",
            }
        )

        tree_rows.append(
            {
                "packet_id": packet_id,
                "cluster_key": key,
                "node_id": cover_node_id,
                "parent_node_id": "",
                "node_type": "cover_main_sandbox_draft",
                "candidate_surface_id": "",
                "candidate_rank": "",
                "node_title": title,
                "year": clean(plan.get("actual_year_span")) or clean(plan.get("five_year_bucket")),
                "source_family": clean(plan.get("source_family")),
                "image_state": image_state_summary(candidates),
                "proposed_relation_role": "cover_scope_candidate",
                "candidate_use": "sandbox_cover_editorial_review",
                "node_summary": scope_summary,
                "relation_to_parent": "root sandbox cover draft; no official role applied",
                "source_basis": "High-priority anchor seed plan row.",
                "scope_policy": review_scope_policy(plan),
                "confidence_status": "sandbox_only_needs_manual_review",
                "manual_check": "Do not apply cover_main automatically.",
            }
        )
        tree_rows.append(
            {
                "packet_id": packet_id,
                "cluster_key": key,
                "node_id": normal_node_id,
                "parent_node_id": cover_node_id,
                "node_type": "normal_main_candidate",
                "candidate_surface_id": clean(normal.get("surface_id")),
                "candidate_rank": clean(normal.get("candidate_rank")),
                "node_title": clean(normal.get("title")),
                "year": clean(normal.get("year")),
                "source_family": clean(normal.get("source_family")) or clean(plan.get("source_family")),
                "image_state": clean(normal.get("image_state")),
                "proposed_relation_role": clean(normal.get("proposed_relation_role")),
                "candidate_use": clean(normal.get("candidate_use")),
                "node_summary": "Top anchor review candidate copied into the sandbox tree for manual normal-main review.",
                "relation_to_parent": "candidate anchor below cover scope; relation not applied",
                "source_basis": "High-priority seed candidate row.",
                "scope_policy": review_scope_policy(plan),
                "confidence_status": "candidate_only",
                "manual_check": "Confirm before any normal_main role assignment.",
            }
        )
        for item in secondary:
            surface_id = clean(item.get("surface_id"))
            tree_rows.append(
                {
                    "packet_id": packet_id,
                    "cluster_key": key,
                    "node_id": f"{packet_id}::{node_type_for_candidate(item)}::{surface_id}",
                    "parent_node_id": normal_node_id,
                    "node_type": node_type_for_candidate(item),
                    "candidate_surface_id": surface_id,
                    "candidate_rank": clean(item.get("candidate_rank")),
                    "node_title": clean(item.get("title")),
                    "year": clean(item.get("year")),
                    "source_family": clean(item.get("source_family")) or clean(plan.get("source_family")),
                    "image_state": clean(item.get("image_state")),
                    "proposed_relation_role": clean(item.get("proposed_relation_role")),
                    "candidate_use": clean(item.get("candidate_use")),
                    "node_summary": "Copied seed candidate for sub/card/appendix relation review.",
                    "relation_to_parent": "candidate relation under normal-main candidate; relation not applied",
                    "source_basis": "High-priority seed candidate row.",
                    "scope_policy": review_scope_policy(plan),
                    "confidence_status": "candidate_only",
                    "manual_check": "Require explicit relation evidence before sub/card/appendix assignment.",
                }
            )

        text_specs = [
            (
                "reading_note_outline",
                "Curated Reading Note Outline",
                reading_outline,
                "Identify reader path and packet rationale before any payload rebuild.",
            ),
            (
                "editorial_page_outline",
                "Editorial Page Outline",
                editorial,
                "Confirm editorial scope, anchor status, relation map, and rights limits.",
            ),
            (
                "relation_uncertainty_note",
                "Relation Uncertainty Notes",
                uncertainty,
                "Resolve relation evidence before assigning sub sheets, cards, appendices, or text pages.",
            ),
            (
                "claims_exclusion_note",
                "What Must Not Be Claimed",
                exclusions,
                "Keep sandbox language separate from official role and rebuild language.",
            ),
        ]
        for text_index, (text_type, text_title, outline, required_review) in enumerate(text_specs, start=1):
            text_rows.append(
                {
                    "packet_id": packet_id,
                    "cluster_key": key,
                    "text_id": f"{packet_id}::text_{text_index:02d}_{text_type}",
                    "attach_to_node_id": cover_node_id,
                    "text_type": text_type,
                    "title": text_title,
                    "outline": outline,
                    "source_basis": "Sandbox outline generated from seed plan and copied seed candidates.",
                    "required_manual_review": required_review,
                    "do_not_claim": exclusions,
                    "official_status": "sandbox_only_not_payload_text",
                }
            )

    return sandbox_rows, tree_rows, text_rows


def summary_rows(
    sandbox_rows: list[dict[str, Any]],
    tree_rows: list[dict[str, Any]],
    text_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    node_counts = Counter(clean(row.get("node_type")) for row in tree_rows)
    source_counts = Counter(clean(row.get("normal_main_candidate_source_family")) for row in sandbox_rows)
    image_counts: Counter[str] = Counter()
    card_count_total = 0
    for row in sandbox_rows:
        card_count_total += as_int(row.get("card_candidate_count_from_plan"))
        for part in clean(row.get("rights_image_state_summary")).split(":")[-1].split(".")[0].split(","):
            if "=" in part:
                key, value = part.strip().split("=", 1)
                image_counts[key] += as_int(value)

    rows: list[dict[str, Any]] = [
        {
            "metric": "scope",
            "value": "non_mutating_cover_editorial_packet_sandbox",
            "notes": "No official payload rebuild, frontend mirror write, image download, rights/source-authority change, or role application.",
        },
        {
            "metric": "cover_editorial_seed_ready_packets",
            "value": len(sandbox_rows),
            "notes": "Only cover_editorial_seed_ready clusters from the high-priority seed plan.",
        },
        {"metric": "sandbox_packet_rows", "value": len(sandbox_rows), "notes": "Cover/editorial sandbox rows."},
        {"metric": "tree_rows", "value": len(tree_rows), "notes": "Sandbox cover, normal-main candidate, and sub/card candidate nodes."},
        {"metric": "text_outline_rows", "value": len(text_rows), "notes": "Reading note, editorial, uncertainty, and exclusion outline rows."},
        {
            "metric": "card_candidate_count_from_plan",
            "value": card_count_total,
            "notes": "Card pressure reported by seed plan; copied seed rows do not apply card roles.",
        },
        {
            "metric": "manual_review_ready_packets",
            "value": len(sandbox_rows),
            "notes": "Can enter human cover/editorial sandbox review.",
        },
        {
            "metric": "official_rebuild_ready_packets",
            "value": 0,
            "notes": "Official rebuild remains blocked until manual review and future payload pass.",
        },
    ]
    for key, value in sorted(node_counts.items()):
        rows.append({"metric": f"node_type:{key}", "value": value, "notes": "Sandbox tree node distribution."})
    for key, value in sorted(source_counts.items()):
        rows.append({"metric": f"source_family:{key}", "value": value, "notes": "Sandbox packet source-family distribution."})
    for key, value in sorted(image_counts.items()):
        rows.append({"metric": f"image_state:{key}", "value": value, "notes": "Copied seed candidate image-state distribution."})
    return rows


def report_text(summary: list[dict[str, Any]], sandbox_rows: list[dict[str, Any]], tree_rows: list[dict[str, Any]]) -> str:
    tree_by_packet: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in tree_rows:
        tree_by_packet[clean(row.get("packet_id"))].append(row)

    lines = [
        "# Research Packet Cover/Editorial Sandbox v1",
        "",
        "Scope: non-mutating cover/editorial sandbox for the four cover_editorial_seed_ready rows.",
        "",
        "This report drafts packet covers, normal-main candidates, candidate tree rows,",
        "reading-note outlines, editorial outlines, rights/image-state summaries, and",
        "relation uncertainty notes. It does not apply packet roles or rebuild any",
        "official archive payload.",
        "",
        "## Summary",
        "",
    ]
    for row in summary:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")

    lines.extend(["", "## Packet Seeds", ""])
    for row in sandbox_rows:
        lines.append(
            f"- {row['packet_id']}: {row['packet_cover_title_draft']} | "
            f"normal-main candidate={row['normal_main_candidate_surface_id']} | "
            f"seed candidates={row['sub_card_candidate_count_from_seed_rows']} secondary rows | "
            f"official rebuild={row['official_rebuild_status']}"
        )

    for row in sandbox_rows:
        packet_id = clean(row.get("packet_id"))
        lines.extend(["", f"## {row['packet_cover_title_draft']}", ""])
        lines.extend(
            [
                f"- packet_id: {packet_id}",
                f"- cluster_key: {row['cluster_key']}",
                f"- cover_main_scope_summary: {row['cover_main_scope_summary']}",
                (
                    "- normal_main_candidate: "
                    f"{row['normal_main_candidate_surface_id']} | {row['normal_main_candidate_title']} | "
                    f"{row['normal_main_candidate_image_state']}"
                ),
                f"- rights_image_state_summary: {row['rights_image_state_summary']}",
                f"- curated_reading_note_outline: {row['curated_reading_note_outline']}",
                f"- editorial_page_outline: {row['editorial_page_outline']}",
                f"- relation_uncertainty_notes: {row['relation_uncertainty_notes']}",
                f"- what_must_not_be_claimed: {row['what_must_not_be_claimed']}",
                f"- manual_review_next_step: {row['manual_review_next_step']}",
            ]
        )
        lines.extend(["", "Candidate Tree Rows:", ""])
        for tree in tree_by_packet[packet_id]:
            lines.append(
                f"- {tree['node_type']}: {tree['candidate_surface_id'] or tree['node_id']} | "
                f"{tree['node_title']} | relation={tree['proposed_relation_role']} | "
                f"status={tree['confidence_status']}"
            )

    lines.extend(["", "## Method Commitments", ""])
    lines.extend(
        [
            "- The top candidate remains a normal-main candidate only.",
            "- Secondary candidates remain sub/card/appendix review candidates only.",
            "- Same source platform, year span, or broad region is not enough to prove sub-sheet relation.",
            "- Card pressure reported by the plan must be reviewed before any card assignment.",
            "- Text rows are editorial outlines, not official packet text pages.",
        ]
    )
    lines.extend(["", "## Safety", ""])
    lines.extend(
        [
            "- No image files were downloaded.",
            "- No rights/source authority/IMG01/IMG03 upgrades were made.",
            "- No packet role, text page, sub sheet, card, or appendix was applied.",
            "- No official payload, frontend mirror, shard, or release build output was modified.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    plan_rows = read_csv(IN_PLAN)
    candidate_rows = read_csv(IN_CANDIDATES)
    sandbox, tree, text = make_sandbox_rows(plan_rows, by_cluster(candidate_rows))
    summary = summary_rows(sandbox, tree, text)

    write_csv(OUT_SANDBOX, sandbox, SANDBOX_FIELDS)
    write_csv(OUT_TREE, tree, TREE_FIELDS)
    write_csv(OUT_TEXT, text, TEXT_FIELDS)
    write_csv(OUT_SUMMARY, summary, SUMMARY_FIELDS)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(report_text(summary, sandbox, tree), encoding="utf-8")

    print(f"cover_editorial_seed_ready_packets={len(sandbox)}")
    print(f"tree_rows={len(tree)}")
    print(f"text_outline_rows={len(text)}")
    print(f"wrote {OUT_SANDBOX.relative_to(ROOT)}")
    print(f"wrote {OUT_TREE.relative_to(ROOT)}")
    print(f"wrote {OUT_TEXT.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
