#!/usr/bin/env python3
"""Resolve tiny non-Commons packet sandbox seeds into manual next actions.

This audit narrows the six source-family tuning seeds into explicit manual
resolution paths. It is non-mutating: it does not apply overrides, rebuild
payloads, download images, or change rights/image states.
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

IN_SEEDS = DATA / "prefreeze_main_sub_text_packet_relation_source_family_tiny_sandbox_seed_v1.csv"
IN_ROLE_REVIEW = DATA / "prefreeze_main_sub_text_packet_relation_source_family_role_review_v1.csv"
IN_ROLE_QUEUE = DATA / "prefreeze_main_sub_text_packet_relation_role_queue_v1.csv"

OUT_RESOLUTION = DATA / "prefreeze_main_sub_text_packet_relation_tiny_seed_resolution_v1.csv"
OUT_DETAIL = DATA / "prefreeze_main_sub_text_packet_relation_tiny_seed_role_detail_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_main_sub_text_packet_relation_tiny_seed_resolution_summary_v1.csv"
OUT_REPORT = DOCS / "MAIN_SUB_TEXT_PACKET_RELATION_TINY_SEED_RESOLUTION_v1.md"

SUMMARY_FIELDS = ["metric", "value", "notes"]
RESOLUTION_FIELDS = [
    "cluster_key",
    "source_family",
    "family_class",
    "region",
    "theme",
    "five_year_bucket",
    "cluster_size",
    "packet_relation_lane",
    "packet_confidence",
    "eligible_rows",
    "anchor_rows",
    "member_or_sub_rows",
    "blocking_dimensions",
    "manual_resolution_path",
    "seed_priority",
    "role_rows",
    "candidate_anchor_rows",
    "eligible_anchor_rows",
    "eligible_member_rows",
    "weak_member_rows",
    "profile_or_interview_rows",
    "book_or_software_rows",
    "event_or_exhibition_rows",
    "issue_or_serial_rows",
    "resolution_status",
    "resolution_reason",
    "manual_requirements",
    "next_action",
    "candidate_anchor_surface_ids",
    "candidate_member_surface_ids",
    "sample_titles",
]
DETAIL_FIELDS = [
    "cluster_key",
    "surface_id",
    "capture_id",
    "year",
    "region",
    "theme",
    "source_family",
    "title",
    "proposed_relation_role",
    "relation_apply_readiness",
    "relation_blockers",
    "risk_flags",
    "positive_flags",
    "anchor_strength_score",
    "source_depth_score",
    "relation_density_score",
    "design_object_confidence_score",
    "record_kind_hint",
    "manual_note",
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


def split_semicolon(value: str) -> list[str]:
    text = clean(value)
    if not text or text == "none":
        return []
    return [part.strip() for part in text.split(";") if part.strip()]


def record_kind(title: str) -> str:
    text = clean(title).casefold()
    if any(term in text for term in ("interview", "profile", "about ", "biography")) or text.endswith(" - another graphic"):
        return "profile_or_interview"
    if any(term in text for term in ("issue", "magazine", "zine", "maximum rocknroll", "future sex", "shadis")):
        return "issue_or_serial"
    if any(term in text for term in ("html", "css", "python", "gui", "web design", "handbook", "cookbook", "usability")):
        return "book_or_software"
    if any(term in text for term in ("exhibition", "gallery", "museum", "federal art project")):
        return "event_or_exhibition"
    if "poster" in text:
        return "poster_or_campaign_item"
    return "object_or_unclear"


def manual_note(kind: str, row: dict[str, str]) -> str:
    blockers = split_semicolon(clean(row.get("relation_blockers")))
    if kind == "profile_or_interview":
        return "Keep as profile/card support unless a specific work/project relation is explicit."
    if kind == "book_or_software":
        return "Likely reference/publication support; do not packet as graphic-design object without stronger object evidence."
    if "weak_design_object_signal" in blockers:
        return "Needs visual/design-object evidence before any sub/member downgrade."
    if kind == "issue_or_serial":
        return "May be a publication series, but needs one anchor and explicit issue/member logic."
    if kind == "event_or_exhibition":
        return "May support packet context; anchor must be explicit exhibition/project record."
    return "Manual review required before role change."


def resolution_for(seed: dict[str, str], rows: list[dict[str, str]]) -> tuple[str, str, str, str]:
    family = clean(seed.get("source_family"))
    blockers = set(split_semicolon(clean(seed.get("blocking_dimensions"))))
    kinds = Counter(record_kind(row.get("title", "")) for row in rows)
    eligible_anchors = [row for row in rows if clean(row.get("proposed_relation_role")) == "candidate_packet_anchor" and clean(row.get("relation_apply_readiness")) == "eligible_for_next_sandbox_review"]
    eligible_members = [
        row
        for row in rows
        if clean(row.get("proposed_relation_role")) in {"packet_member_review", "sub_under_packet_candidate"}
        and clean(row.get("relation_apply_readiness")) == "eligible_for_next_sandbox_review"
    ]
    weak_members = [
        row
        for row in rows
        if clean(row.get("proposed_relation_role")) in {"packet_member_review", "sub_under_packet_candidate"}
        and "weak_design_object_signal" in split_semicolon(clean(row.get("relation_blockers")))
    ]

    if family == "Another Graphic" and kinds.get("profile_or_interview", 0) >= max(1, len(rows) // 2):
        return (
            "hold_profile_directory_not_packet",
            "Rows look like designer/studio profile pages, not a proven work/project packet.",
            "Need explicit project/work relation, creator-work grouping, and non-macro region before any role change.",
            "Keep out of sandbox; use as card/profile support or wait for project-level records.",
        )
    if kinds.get("book_or_software", 0) >= 2:
        return (
            "hold_reference_publication_drift",
            "Seed mixes reference/software/web-design books with archive issues, creating design-object drift risk.",
            "Need object-level graphic-design evidence and source-family split before packeting.",
            "Remove from tiny sandbox candidate list until cluster is split by object type.",
        )
    if "macro_or_unresolved_region" in blockers and not eligible_members:
        return (
            "hold_macro_anchor_only_series",
            "Cluster has macro/global region and eligible anchors but no eligible member/sub rows.",
            "Need region split plus one accepted anchor/member relation before tiny sandbox.",
            "Do not sandbox; resolve region and relation shape first.",
        )
    if "macro_or_unresolved_region" in blockers:
        return (
            "needs_region_split_before_tiny_sandbox",
            "Cluster has potentially useful anchor/member shape but region scope is macro/global.",
            "Need country/region split or explicit transnational packet rationale before sandbox.",
            "Run a region-scope review before any role override.",
        )
    if "missing_anchor" in blockers:
        return (
            "needs_anchor_selection_review",
            "Cluster has eligible member/sub rows but no blocker-free anchor.",
            "Need one explicit packet anchor chosen from source text and design-object evidence.",
            "Create an anchor-selection review; do not auto-promote an anchor.",
        )
    if "missing_member_or_sub" in blockers and weak_members:
        return (
            "needs_member_evidence_review",
            "Cluster has an anchor but members are blocked by weak design-object evidence.",
            "Need source-side visual/object evidence for at least one member/sub row.",
            "Review member evidence before any tiny sandbox.",
        )
    if eligible_anchors and eligible_members:
        return (
            "candidate_after_manual_review",
            "Cluster has eligible anchor and member/sub rows after existing blockers are resolved.",
            "Need manual confirmation that source family relation evidence is explicit.",
            "Can enter a tiny sandbox only after manual sign-off.",
        )
    return (
        "manual_hold",
        "Cluster does not yet have a safe packet shape.",
        "Need source-family relation evidence and manual review.",
        "Hold from sandbox.",
    )


def main() -> None:
    seeds = read_csv(IN_SEEDS)
    role_review = read_csv(IN_ROLE_REVIEW)
    queue_rows = read_csv(IN_ROLE_QUEUE)
    queue_by_surface = {clean(row.get("surface_id")): row for row in queue_rows}
    roles_by_cluster: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in role_review:
        roles_by_cluster[clean(row.get("cluster_key"))].append(row)

    resolution_rows: list[dict[str, Any]] = []
    detail_rows: list[dict[str, Any]] = []

    for seed in seeds:
        key = clean(seed.get("cluster_key"))
        rows = roles_by_cluster.get(key, [])
        for row in rows:
            source = queue_by_surface.get(clean(row.get("surface_id")), {})
            kind = record_kind(clean(row.get("title")))
            detail_rows.append(
                {
                    "cluster_key": key,
                    "surface_id": clean(row.get("surface_id")),
                    "capture_id": clean(row.get("capture_id")),
                    "year": clean(row.get("year")),
                    "region": clean(row.get("region")),
                    "theme": clean(row.get("theme")),
                    "source_family": clean(row.get("source_family")),
                    "title": clean(row.get("title")),
                    "proposed_relation_role": clean(row.get("proposed_relation_role")),
                    "relation_apply_readiness": clean(row.get("relation_apply_readiness")),
                    "relation_blockers": clean(row.get("relation_blockers")),
                    "risk_flags": clean(source.get("risk_flags")),
                    "positive_flags": clean(source.get("positive_flags")),
                    "anchor_strength_score": clean(source.get("anchor_strength_score")),
                    "source_depth_score": clean(source.get("source_depth_score")),
                    "relation_density_score": clean(source.get("relation_density_score")),
                    "design_object_confidence_score": clean(source.get("design_object_confidence_score")),
                    "record_kind_hint": kind,
                    "manual_note": manual_note(kind, row),
                }
            )
        status, reason, requirements, next_action = resolution_for(seed, rows)
        eligible_anchor_ids = [
            clean(row.get("surface_id"))
            for row in rows
            if clean(row.get("proposed_relation_role")) == "candidate_packet_anchor"
            and clean(row.get("relation_apply_readiness")) == "eligible_for_next_sandbox_review"
        ]
        eligible_member_ids = [
            clean(row.get("surface_id"))
            for row in rows
            if clean(row.get("proposed_relation_role")) in {"packet_member_review", "sub_under_packet_candidate"}
            and clean(row.get("relation_apply_readiness")) == "eligible_for_next_sandbox_review"
        ]
        kinds = Counter(record_kind(row.get("title", "")) for row in rows)
        resolution_rows.append(
            {
                **{field: clean(seed.get(field)) for field in RESOLUTION_FIELDS if field in seed},
                "role_rows": len(rows),
                "candidate_anchor_rows": sum(1 for row in rows if clean(row.get("proposed_relation_role")) == "candidate_packet_anchor"),
                "eligible_anchor_rows": len(eligible_anchor_ids),
                "eligible_member_rows": len(eligible_member_ids),
                "weak_member_rows": sum(
                    1
                    for row in rows
                    if clean(row.get("proposed_relation_role")) in {"packet_member_review", "sub_under_packet_candidate"}
                    and "weak_design_object_signal" in split_semicolon(clean(row.get("relation_blockers")))
                ),
                "profile_or_interview_rows": kinds.get("profile_or_interview", 0),
                "book_or_software_rows": kinds.get("book_or_software", 0),
                "event_or_exhibition_rows": kinds.get("event_or_exhibition", 0),
                "issue_or_serial_rows": kinds.get("issue_or_serial", 0),
                "resolution_status": status,
                "resolution_reason": reason,
                "manual_requirements": requirements,
                "next_action": next_action,
                "candidate_anchor_surface_ids": "; ".join(eligible_anchor_ids),
                "candidate_member_surface_ids": "; ".join(eligible_member_ids),
            }
        )

    resolution_rows.sort(key=lambda row: (-as_int(row.get("seed_priority")), clean(row.get("cluster_key"))))
    detail_rows.sort(key=lambda row: (clean(row.get("cluster_key")), -as_int(row.get("anchor_strength_score")), clean(row.get("surface_id"))))

    summary_rows = [
        {"metric": "scope", "value": "non_mutating_tiny_seed_resolution", "notes": "No rebuild, role override, payload write, image download, or rights/image-state change."},
        {"metric": "tiny_seed_rows", "value": len(seeds), "notes": "Seed clusters reviewed."},
        {"metric": "seed_role_detail_rows", "value": len(detail_rows), "notes": "Role rows inside seed clusters."},
        {"metric": "sandbox_ready_rows", "value": sum(1 for row in resolution_rows if clean(row.get("resolution_status")) == "candidate_after_manual_review"), "notes": "Rows that could enter tiny sandbox after manual sign-off."},
    ]
    for status, count in Counter(clean(row.get("resolution_status")) for row in resolution_rows).most_common():
        summary_rows.append({"metric": f"resolution_status:{status}", "value": count, "notes": "Seed resolution status distribution."})
    for kind, count in Counter(clean(row.get("record_kind_hint")) for row in detail_rows).most_common():
        summary_rows.append({"metric": f"record_kind:{kind}", "value": count, "notes": "Record-kind hints inside seed clusters."})

    write_csv(OUT_RESOLUTION, resolution_rows, RESOLUTION_FIELDS)
    write_csv(OUT_DETAIL, detail_rows, DETAIL_FIELDS)
    write_csv(OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_report(summary_rows, resolution_rows)

    print(f"tiny_seed_rows={len(seeds)}")
    print(f"seed_role_detail_rows={len(detail_rows)}")
    print(f"sandbox_ready_rows={sum(1 for row in resolution_rows if clean(row.get('resolution_status')) == 'candidate_after_manual_review')}")
    print(f"wrote {OUT_RESOLUTION.relative_to(ROOT)}")
    print(f"wrote {OUT_DETAIL.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


def write_report(summary: list[dict[str, Any]], resolutions: list[dict[str, Any]]) -> None:
    lines = [
        "# Main/Sub/Text Packet Relation Tiny Seed Resolution v1",
        "",
        "Scope: non-mutating manual-resolution audit for the six non-Commons tiny sandbox seeds.",
        "",
        "This pass does not rebuild payloads, apply overrides, download images, or change rights/image states.",
        "",
        "## Summary",
        "",
    ]
    for row in summary:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(
        [
            "",
            "## Seed Decisions",
            "",
        ]
    )
    for row in resolutions:
        lines.append(
            f"- {row['cluster_key']}: status={row['resolution_status']}; reason={row['resolution_reason']}; "
            f"next={row['next_action']}"
        )
    lines.extend(
        [
            "",
            "## Method Note",
            "",
            "- A seed is not sandbox-ready just because it has eligible rows.",
            "- Macro/global clusters need region-scope resolution before packet role changes.",
            "- Profile, interview, software/book, and support/reference records should not become packet members without explicit design-object evidence.",
            "- Anchor/member repair remains a manual review action, not an automatic upgrade.",
            "",
            "## Safety",
            "",
            "- No rights, source authority, authorship, or IMG01/IMG03 state changes were made.",
            "- No source-family or seed signal may override macro/unresolved region review.",
            "- No image files were downloaded.",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
