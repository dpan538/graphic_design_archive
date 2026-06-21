#!/usr/bin/env python3
"""Create execution layers for research-packet review before rebuild.

This non-mutating audit turns packet structure requirements into an ordered
work queue. It does not apply packet roles, rebuild surfaces, write frontend
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

IN_REQUIREMENTS = DATA / "research_packet_structure_requirements_v1.csv"
IN_ROLE_QUEUE = DATA / "prefreeze_main_sub_text_packet_relation_role_queue_v1.csv"
IN_CLUSTER_AUDIT = DATA / "prefreeze_main_sub_text_packet_relation_cluster_audit_v1.csv"

OUT_QUEUE = DATA / "research_packet_readiness_layer_queue_v1.csv"
OUT_ACTIONS = DATA / "research_packet_readiness_layer_actions_v1.csv"
OUT_SUMMARY = DATA / "research_packet_readiness_layer_summary_v1.csv"
OUT_REPORT = DOCS / "RESEARCH_PACKET_READINESS_LAYER_v1.md"

QUEUE_FIELDS = [
    "cluster_key",
    "priority_rank",
    "packet_layer",
    "recommended_first_action",
    "blocking_issue",
    "safe_for_sandbox_packet_trial",
    "packet_scale",
    "packet_readiness",
    "packet_confidence",
    "packet_relation_lane",
    "region",
    "theme",
    "source_family",
    "five_year_bucket",
    "actual_year_span",
    "global_scope_policy",
    "cluster_size",
    "role_rows",
    "anchor_candidate_count",
    "sub_candidate_count",
    "card_candidate_count",
    "appendix_candidate_count",
    "text_deficit_count",
    "minimum_text_pages",
    "editorial_page_requirement",
    "cover_main_requirement",
    "normal_main_policy",
    "folder_directory_mode",
    "reason",
]

ACTION_FIELDS = [
    "packet_layer",
    "cluster_count",
    "safe_for_sandbox_count",
    "recommended_action",
    "expected_next_output",
    "do_not_do",
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def role_counts(rows: list[dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        role = clean(row.get("proposed_relation_role"))
        counts[role] += 1
        if "appendix" in role:
            counts["appendix_any"] += 1
    return counts


def by_cluster(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        out[clean(row.get("cluster_key"))].append(row)
    return out


def cluster_map(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {clean(row.get("cluster_key")): row for row in rows}


def is_sandbox_safe(
    req: dict[str, str],
    cluster: dict[str, str],
    counts: Counter[str],
    sub_count: int,
    anchor_count: int,
) -> bool:
    if clean(req.get("global_scope_policy")) != "region_specific_or_not_global":
        return False
    if clean(cluster.get("packet_relation_lane")) != "strong_packet_candidate":
        return False
    if clean(cluster.get("packet_confidence")) != "high":
        return False
    if anchor_count < 1 or sub_count < 1:
        return False
    if as_int(req.get("role_rows")) > 80:
        return False
    if clean(req.get("normal_main_policy")) == "normal_main_anchor_selection_needed" and anchor_count == 0:
        return False
    if counts.get("card_context_candidate", 0) > max(12, sub_count * 3):
        return False
    return True


def layer_for(req: dict[str, str], cluster: dict[str, str], counts: Counter[str]) -> tuple[int, str, str, str]:
    policy = clean(req.get("global_scope_policy"))
    readiness = clean(req.get("packet_readiness"))
    scale = clean(req.get("packet_scale"))
    lane = clean(cluster.get("packet_relation_lane"))
    confidence = clean(cluster.get("packet_confidence"))
    normal_policy = clean(req.get("normal_main_policy"))
    editorial = clean(req.get("editorial_page_requirement"))
    role_rows = as_int(req.get("role_rows"))
    sub_count = counts.get("packet_member_review", 0) + counts.get("sub_under_packet_candidate", 0)
    anchor_count = (
        counts.get("candidate_packet_anchor", 0)
        + counts.get("provisional_main_anchor_needs_text", 0)
        + counts.get("anchor_or_sibling_review", 0)
    )
    card_count = counts.get("card_context_candidate", 0)
    appendix_count = counts.get("text_or_appendix_candidate", 0) + counts.get("appendix_any", 0)
    safe = is_sandbox_safe(req, cluster, counts, sub_count, anchor_count)

    if policy in {"global_host_requires_scope_review", "global_scope_manual_review"} or readiness == "scope_review_before_packet":
        return (
            10,
            "phase_0_scope_review",
            "resolve_global_or_macro_scope_before_packet_shape",
            "global_or_macro_scope_unresolved",
        )
    if lane == "macro_cluster_needs_split" or role_rows > 120:
        return (
            20,
            "phase_0_macro_split",
            "split_macro_cluster_before_cover_or_sub_assignment",
            "cluster_too_large_or_macro_for_direct_packet",
        )
    if normal_policy == "normal_main_anchor_selection_needed" or anchor_count == 0:
        return (
            30,
            "phase_1_anchor_selection",
            "select_or_confirm_normal_main_anchor_before_sub_assignment",
            "missing_or_unsettled_normal_main_anchor",
        )
    if lane == "packet_parentage_review" or confidence not in {"high", "medium"}:
        return (
            40,
            "phase_1_relation_evidence_review",
            "strengthen_parent_member_relation_evidence",
            "parentage_or_relation_confidence_not_ready",
        )
    if safe and scale in {"medium", "large"} and editorial == "mandatory_editorial_page":
        return (
            50,
            "phase_2_editorial_cover_first",
            "draft_cover_scope_and_editorial_reading_note_before_sandbox",
            "editorial_and_cover_required_before_packet_trial",
        )
    if safe:
        return (
            60,
            "phase_3_sandbox_packet_trial",
            "run_small_packet_shape_trial_on_this_cluster",
            "none",
        )
    if lane == "card_context_cluster" or (card_count > 0 and sub_count == 0):
        return (
            70,
            "phase_4_card_appendix_support",
            "keep_as_card_or_appendix_support_until_anchor_relation_improves",
            "card_heavy_without_sub_structure",
        )
    if appendix_count > 0 and sub_count == 0:
        return (
            80,
            "phase_4_appendix_text_support",
            "treat_as_appendix_or_text_support_before_packet_promotion",
            "appendix_or_text_evidence_without_sub_structure",
        )
    return (
        90,
        "phase_5_method_review_hold",
        "hold_for_method_review_after_higher_confidence_packets",
        "insufficient_packet_shape_confidence",
    )


def queue_rows(
    requirements: list[dict[str, str]],
    role_rows_by_cluster: dict[str, list[dict[str, str]]],
    clusters_by_key: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for req in requirements:
        key = clean(req.get("cluster_key"))
        rows = role_rows_by_cluster.get(key, [])
        cluster = clusters_by_key.get(key, {})
        counts = role_counts(rows)
        anchor_count = (
            counts.get("candidate_packet_anchor", 0)
            + counts.get("provisional_main_anchor_needs_text", 0)
            + counts.get("anchor_or_sibling_review", 0)
        )
        sub_count = counts.get("packet_member_review", 0) + counts.get("sub_under_packet_candidate", 0)
        card_count = counts.get("card_context_candidate", 0)
        appendix_count = counts.get("text_or_appendix_candidate", 0) + counts.get("appendix_any", 0)
        priority, layer, action, blocker = layer_for(req, cluster, counts)
        safe = is_sandbox_safe(req, cluster, counts, sub_count, anchor_count)
        out.append(
            {
                "cluster_key": key,
                "priority_rank": priority,
                "packet_layer": layer,
                "recommended_first_action": action,
                "blocking_issue": blocker,
                "safe_for_sandbox_packet_trial": str(safe).lower(),
                "packet_scale": clean(req.get("packet_scale")),
                "packet_readiness": clean(req.get("packet_readiness")),
                "packet_confidence": clean(cluster.get("packet_confidence")),
                "packet_relation_lane": clean(cluster.get("packet_relation_lane")),
                "region": clean(req.get("region")),
                "theme": clean(req.get("theme")),
                "source_family": clean(req.get("source_family")),
                "five_year_bucket": clean(req.get("five_year_bucket")),
                "actual_year_span": clean(req.get("actual_year_span")),
                "global_scope_policy": clean(req.get("global_scope_policy")),
                "cluster_size": clean(req.get("cluster_size")),
                "role_rows": clean(req.get("role_rows")),
                "anchor_candidate_count": anchor_count,
                "sub_candidate_count": sub_count,
                "card_candidate_count": card_count,
                "appendix_candidate_count": appendix_count,
                "text_deficit_count": clean(cluster.get("text_deficit_count")),
                "minimum_text_pages": clean(req.get("minimum_text_pages")),
                "editorial_page_requirement": clean(req.get("editorial_page_requirement")),
                "cover_main_requirement": clean(req.get("cover_main_requirement")),
                "normal_main_policy": clean(req.get("normal_main_policy")),
                "folder_directory_mode": clean(req.get("folder_directory_mode")),
                "reason": clean(req.get("reason")),
            }
        )
    return sorted(out, key=lambda row: (as_int(row["priority_rank"]), -as_int(row["role_rows"]), clean(row["cluster_key"])))


def action_rows(queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    layer_counts = Counter(clean(row["packet_layer"]) for row in queue)
    safe_counts = Counter(clean(row["packet_layer"]) for row in queue if clean(row["safe_for_sandbox_packet_trial"]) == "true")
    actions = {
        "phase_0_scope_review": (
            "Resolve global/transnational or macro-region scope before packet construction.",
            "scope decision queue and allowed global packet list",
            "Do not force country assignment or create cover main from unresolved host scope.",
        ),
        "phase_0_macro_split": (
            "Split oversized macro clusters by source-side series, project, institution, or narrower period.",
            "macro split candidate list",
            "Do not generate one huge cover packet from a macro bucket.",
        ),
        "phase_1_anchor_selection": (
            "Choose or confirm normal main anchor candidates before sub/card attachment.",
            "anchor selection review table",
            "Do not demote all mains just because the packet needs a cover main.",
        ),
        "phase_1_relation_evidence_review": (
            "Strengthen parent/member evidence before any role application.",
            "relation evidence review notes",
            "Do not use same source family, year, or region as sufficient parentage.",
        ),
        "phase_2_editorial_cover_first": (
            "Draft cover scope and editorial reading note before sandbox packet shaping.",
            "cover/editorial draft queue",
            "Do not run full rebuild; use sandbox packet trials only.",
        ),
        "phase_3_sandbox_packet_trial": (
            "Run a small sandbox packet-shape trial.",
            "sandbox packet output for manual review",
            "Do not write official payload until manual review passes.",
        ),
        "phase_4_card_appendix_support": (
            "Keep as card or appendix support until stronger anchor/sub relation exists.",
            "support-evidence queue",
            "Do not promote card-heavy pools into normal mains.",
        ),
        "phase_4_appendix_text_support": (
            "Treat as appendix/text support before packet promotion.",
            "appendix/text support queue",
            "Do not hide weak evidence in the main reading path.",
        ),
        "phase_5_method_review_hold": (
            "Hold for later method review after high-confidence packets are resolved.",
            "deferred review list",
            "Do not spend rebuild budget here yet.",
        ),
    }
    for layer, count in sorted(layer_counts.items()):
        action, expected, avoid = actions.get(layer, ("Manual review.", "review list", "Do not apply automatically."))
        rows.append(
            {
                "packet_layer": layer,
                "cluster_count": count,
                "safe_for_sandbox_count": safe_counts.get(layer, 0),
                "recommended_action": action,
                "expected_next_output": expected,
                "do_not_do": avoid,
            }
        )
    return rows


def summary_rows(queue: list[dict[str, Any]], actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "metric": "scope",
            "value": "non_mutating_research_packet_readiness_layers",
            "notes": "No rebuild, role override, image download, rights/image-state change, or frontend mirror write.",
        },
        {"metric": "queue_rows", "value": len(queue), "notes": "Cluster-level readiness queue rows."},
        {"metric": "action_rows", "value": len(actions), "notes": "Layer action contract rows."},
        {
            "metric": "safe_for_sandbox_packet_trial",
            "value": sum(1 for row in queue if clean(row["safe_for_sandbox_packet_trial"]) == "true"),
            "notes": "Rows that may be used for sandbox packet-shape trials only.",
        },
    ]
    layer_counts = Counter(clean(row["packet_layer"]) for row in queue)
    scale_counts = Counter(clean(row["packet_scale"]) for row in queue)
    blocker_counts = Counter(clean(row["blocking_issue"]) for row in queue)
    editorial_counts = Counter(clean(row["editorial_page_requirement"]) for row in queue)
    for key, value in sorted(layer_counts.items()):
        rows.append({"metric": f"packet_layer:{key}", "value": value, "notes": "Readiness layer distribution."})
    for key, value in sorted(scale_counts.items()):
        rows.append({"metric": f"packet_scale:{key}", "value": value, "notes": "Packet scale distribution."})
    for key, value in sorted(blocker_counts.items()):
        rows.append({"metric": f"blocking_issue:{key}", "value": value, "notes": "Primary blocking issue distribution."})
    for key, value in sorted(editorial_counts.items()):
        rows.append({"metric": f"editorial:{key}", "value": value, "notes": "Editorial page requirement distribution."})
    return rows


def report_text(summary: list[dict[str, Any]], actions: list[dict[str, Any]], queue: list[dict[str, Any]]) -> str:
    lines = [
        "# Research Packet Readiness Layer v1",
        "",
        "Scope: non-mutating execution-layer audit for packet review before rebuild.",
        "",
        "This pass does not rebuild payloads, apply overrides, download images,",
        "write frontend mirrors, or change rights/image states.",
        "",
        "## Summary",
        "",
    ]
    for row in summary:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Layer Actions", ""])
    for row in actions:
        lines.append(
            f"- {row['packet_layer']}: {row['cluster_count']} clusters; action={row['recommended_action']} "
            f"output={row['expected_next_output']}"
        )
    lines.extend(["", "## Top Sandbox-Eligible Rows", ""])
    safe_rows = [row for row in queue if clean(row["safe_for_sandbox_packet_trial"]) == "true"][:20]
    if not safe_rows:
        lines.append("- None.")
    for row in safe_rows:
        lines.append(
            f"- {row['cluster_key']}: scale={row['packet_scale']}; anchors={row['anchor_candidate_count']}; "
            f"subs={row['sub_candidate_count']}; min_text={row['minimum_text_pages']}; action={row['recommended_first_action']}"
        )
    lines.extend(["", "## Method Commitments", ""])
    lines.extend(
        [
            "- Sandbox-ready means sandbox-only; it does not permit official payload writes.",
            "- Cover main can organize normal mains without automatically demoting them.",
            "- Medium and large packets need editorial reading-note work before full packet rebuild.",
            "- Card-heavy and appendix-heavy clusters remain support pools until anchor/sub evidence improves.",
            "- Global/transnational scope is valid, but unresolved host scope must be reviewed before packet construction.",
        ]
    )
    lines.extend(["", "## Safety", ""])
    lines.extend(
        [
            "- No rights/source authority/image-state upgrades were made.",
            "- No source-family signal overrides macro/global scope review.",
            "- No packet role is applied by this audit.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    requirements = read_csv(IN_REQUIREMENTS)
    role_rows = read_csv(IN_ROLE_QUEUE)
    clusters = read_csv(IN_CLUSTER_AUDIT)
    queue = queue_rows(requirements, by_cluster(role_rows), cluster_map(clusters))
    actions = action_rows(queue)
    summary = summary_rows(queue, actions)

    write_csv(OUT_QUEUE, queue, QUEUE_FIELDS)
    write_csv(OUT_ACTIONS, actions, ACTION_FIELDS)
    write_csv(OUT_SUMMARY, summary, SUMMARY_FIELDS)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(report_text(summary, actions, queue), encoding="utf-8")

    print(f"queue_rows={len(queue)}")
    print(f"action_rows={len(actions)}")
    print(f"safe_for_sandbox={sum(1 for row in queue if clean(row['safe_for_sandbox_packet_trial']) == 'true')}")
    print(f"wrote {OUT_QUEUE.relative_to(ROOT)}")
    print(f"wrote {OUT_ACTIONS.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
