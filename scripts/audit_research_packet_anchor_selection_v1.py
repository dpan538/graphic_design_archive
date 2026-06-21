#!/usr/bin/env python3
"""Audit normal-main anchor selection blockers before packet rebuild.

This non-mutating pass focuses on the phase_1_anchor_selection queue. It
creates cluster-level anchor review lanes and surface-level anchor candidates
for manual review. It does not apply roles, rebuild payloads, write frontend
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

IN_READINESS = DATA / "research_packet_readiness_layer_queue_v1.csv"
IN_ROLE_QUEUE = DATA / "prefreeze_main_sub_text_packet_relation_role_queue_v1.csv"
IN_CLUSTER_AUDIT = DATA / "prefreeze_main_sub_text_packet_relation_cluster_audit_v1.csv"

OUT_CLUSTER = DATA / "research_packet_anchor_selection_cluster_review_v1.csv"
OUT_CANDIDATES = DATA / "research_packet_anchor_selection_candidate_review_v1.csv"
OUT_SUMMARY = DATA / "research_packet_anchor_selection_summary_v1.csv"
OUT_REPORT = DOCS / "RESEARCH_PACKET_ANCHOR_SELECTION_v1.md"

CLUSTER_FIELDS = [
    "cluster_key",
    "anchor_review_lane",
    "recommended_next_step",
    "manual_review_priority",
    "can_seed_anchor_review",
    "candidate_count_written",
    "packet_scale",
    "packet_relation_lane",
    "packet_confidence",
    "region",
    "theme",
    "source_family",
    "five_year_bucket",
    "actual_year_span",
    "cluster_size",
    "role_rows",
    "anchor_candidate_count",
    "sub_candidate_count",
    "card_candidate_count",
    "appendix_candidate_count",
    "top_candidate_surface_id",
    "top_candidate_title",
    "top_anchor_review_score",
    "top_candidate_role",
    "top_candidate_risk_flags",
    "blocking_reason",
]

CANDIDATE_FIELDS = [
    "cluster_key",
    "candidate_rank",
    "surface_id",
    "capture_id",
    "year",
    "title",
    "region",
    "theme",
    "source_family",
    "source_name",
    "image_state",
    "proposed_relation_role",
    "recommended_next_action",
    "anchor_review_score",
    "anchor_strength_score",
    "source_depth_score",
    "relation_density_score",
    "text_depth_score",
    "design_object_confidence_score",
    "risk_pressure_score",
    "editorial_need_score",
    "risk_flags",
    "positive_flags",
    "candidate_use",
    "manual_check",
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


def by_cluster(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[clean(row.get("cluster_key"))].append(row)
    return grouped


def cluster_map(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {clean(row.get("cluster_key")): row for row in rows}


def role_counts(rows: list[dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        role = clean(row.get("proposed_relation_role"))
        counts[role] += 1
        if "appendix" in role:
            counts["appendix_any"] += 1
    return counts


def score_candidate(row: dict[str, str]) -> float:
    role = clean(row.get("proposed_relation_role"))
    action = clean(row.get("recommended_next_action"))
    risk_flags = clean(row.get("risk_flags")).casefold()
    positive_flags = clean(row.get("positive_flags")).casefold()

    score = (
        as_int(row.get("anchor_strength_score")) * 0.30
        + as_int(row.get("source_depth_score")) * 0.20
        + as_int(row.get("design_object_confidence_score")) * 0.20
        + as_int(row.get("text_depth_score")) * 0.15
        + as_int(row.get("relation_density_score")) * 0.15
        + as_int(row.get("editorial_need_score")) * 0.05
        - as_int(row.get("risk_pressure_score")) * 0.30
    )
    if role == "candidate_packet_anchor":
        score += 24
    elif role == "provisional_main_anchor_needs_text":
        score += 18
    elif role == "anchor_or_sibling_review":
        score += 10
    elif role in {"packet_member_review", "sub_under_packet_candidate"}:
        score += 3
    elif role == "card_context_candidate":
        score -= 14

    if action == "keep_main_anchor":
        score += 20
    elif action == "keep_main_add_text":
        score += 14
    elif action == "packet_anchor_review":
        score += 6
    elif action == "downgrade_to_card_candidate":
        score -= 16

    high_risk_terms = (
        "event",
        "photo",
        "session",
        "stamp",
        "philatelic",
        "profile",
        "interview",
        "memory",
        "commemorative",
    )
    if any(term in risk_flags for term in high_risk_terms):
        score -= 22
    if any(term in positive_flags for term in ("design", "graphic", "poster", "typography", "visual communication")):
        score += 8
    return round(score, 2)


def candidate_rows_for_cluster(rows: list[dict[str, str]], limit: int = 5) -> list[dict[str, str]]:
    ranked = sorted(
        rows,
        key=lambda row: (
            score_candidate(row),
            as_int(row.get("anchor_strength_score")),
            as_int(row.get("source_depth_score")),
            as_int(row.get("design_object_confidence_score")),
            -as_int(row.get("risk_pressure_score")),
            clean(row.get("title")),
        ),
        reverse=True,
    )
    return ranked[:limit]


def lane_for(
    readiness: dict[str, str],
    cluster: dict[str, str],
    rows: list[dict[str, str]],
    counts: Counter[str],
    top_score: float,
) -> tuple[str, str, str, bool, str]:
    scale = clean(readiness.get("packet_scale"))
    lane = clean(readiness.get("packet_relation_lane"))
    confidence = clean(readiness.get("packet_confidence"))
    role_rows = as_int(readiness.get("role_rows"))
    sub_count = counts.get("packet_member_review", 0) + counts.get("sub_under_packet_candidate", 0)
    card_count = counts.get("card_context_candidate", 0)
    anchor_count = (
        counts.get("candidate_packet_anchor", 0)
        + counts.get("provisional_main_anchor_needs_text", 0)
        + counts.get("anchor_or_sibling_review", 0)
    )
    top_risk = clean(rows[0].get("risk_flags")).casefold() if rows else ""

    if anchor_count > 0:
        return (
            "existing_anchor_candidate_confirm",
            "confirm_existing_anchor_candidate_and_required_text",
            "high",
            True,
            "existing anchor-like role present but still needs manual confirmation",
        )
    if card_count >= max(8, sub_count * 4) and sub_count <= 2:
        return (
            "card_heavy_support_pool",
            "keep_as_card_or_appendix_support_until_stronger_anchor_exists",
            "medium" if scale in {"large", "medium"} else "low",
            False,
            "card-heavy cluster has no stable normal-main anchor",
        )
    if lane == "packet_parentage_review":
        if sub_count >= 3 and top_score >= 55:
            return (
                "sub_rich_anchor_candidate_review",
                "manually_test_top_candidate_as_normal_main_anchor",
                "high",
                True,
                "sub-rich parentage cluster has a plausible top anchor candidate",
            )
        return (
            "parentage_before_anchor",
            "strengthen_parent_member_evidence_before_anchor_selection",
            "medium",
            False,
            "parentage lane lacks enough anchor confidence",
        )
    if lane == "strong_packet_candidate" and top_score >= 60:
        return (
            "strong_packet_anchor_candidate_review",
            "manually_confirm_top_candidate_then_prepare_cover_or_editorial",
            "high",
            True,
            "strong packet lane with plausible top anchor candidate",
        )
    if scale in {"single_or_micro", "small"} and role_rows <= 3:
        return (
            "small_packet_standalone_or_sub_review",
            "decide_if_standalone_normal_main_or_sub_under_nearby_packet",
            "low",
            top_score >= 65,
            "small packet may not need cover-main treatment",
        )
    if any(term in top_risk for term in ("event", "photo", "session", "stamp", "philatelic", "profile", "interview")):
        return (
            "weak_graphic_anchor_risk",
            "do_not_promote_until_design_object_evidence_is_reviewed",
            "medium",
            False,
            "top candidate carries weak graphic/object risk flags",
        )
    if sub_count >= 3 and top_score >= 50:
        return (
            "manual_anchor_candidate_review",
            "review_top_candidates_for_normal_main_anchor",
            "medium",
            True,
            "sub candidates exist but anchor role is unset",
        )
    return (
        "defer_anchor_method_review",
        "defer_until_higher_confidence_packet_work_is_complete",
        "low",
        False,
        "no reliable anchor signal yet",
    )


def make_outputs(
    readiness_rows: list[dict[str, str]],
    role_rows_by_cluster: dict[str, list[dict[str, str]]],
    clusters_by_key: dict[str, dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    target_rows = [row for row in readiness_rows if clean(row.get("packet_layer")) == "phase_1_anchor_selection"]
    cluster_out: list[dict[str, Any]] = []
    candidate_out: list[dict[str, Any]] = []

    for readiness in target_rows:
        key = clean(readiness.get("cluster_key"))
        rows = role_rows_by_cluster.get(key, [])
        cluster = clusters_by_key.get(key, {})
        counts = role_counts(rows)
        candidates = candidate_rows_for_cluster(rows, limit=5)
        top = candidates[0] if candidates else {}
        top_score = score_candidate(top) if top else 0.0
        review_lane, next_step, priority, can_seed, reason = lane_for(readiness, cluster, candidates, counts, top_score)

        for index, candidate in enumerate(candidates, start=1):
            role = clean(candidate.get("proposed_relation_role"))
            action = clean(candidate.get("recommended_next_action"))
            if index == 1 and can_seed:
                candidate_use = "top_anchor_review_candidate"
            elif role == "card_context_candidate" or action == "downgrade_to_card_candidate":
                candidate_use = "context_or_card_support_candidate"
            else:
                candidate_use = "secondary_anchor_review_candidate"
            candidate_out.append(
                {
                    "cluster_key": key,
                    "candidate_rank": index,
                    "surface_id": clean(candidate.get("surface_id")),
                    "capture_id": clean(candidate.get("capture_id")),
                    "year": clean(candidate.get("year")),
                    "title": clean(candidate.get("title")),
                    "region": clean(candidate.get("region")),
                    "theme": clean(candidate.get("theme")),
                    "source_family": clean(candidate.get("source_family")),
                    "source_name": clean(candidate.get("source_name")),
                    "image_state": clean(candidate.get("image_state")),
                    "proposed_relation_role": role,
                    "recommended_next_action": action,
                    "anchor_review_score": score_candidate(candidate),
                    "anchor_strength_score": clean(candidate.get("anchor_strength_score")),
                    "source_depth_score": clean(candidate.get("source_depth_score")),
                    "relation_density_score": clean(candidate.get("relation_density_score")),
                    "text_depth_score": clean(candidate.get("text_depth_score")),
                    "design_object_confidence_score": clean(candidate.get("design_object_confidence_score")),
                    "risk_pressure_score": clean(candidate.get("risk_pressure_score")),
                    "editorial_need_score": clean(candidate.get("editorial_need_score")),
                    "risk_flags": clean(candidate.get("risk_flags")),
                    "positive_flags": clean(candidate.get("positive_flags")),
                    "candidate_use": candidate_use,
                    "manual_check": "candidate only; do not apply role automatically",
                }
            )

        cluster_out.append(
            {
                "cluster_key": key,
                "anchor_review_lane": review_lane,
                "recommended_next_step": next_step,
                "manual_review_priority": priority,
                "can_seed_anchor_review": str(can_seed).lower(),
                "candidate_count_written": len(candidates),
                "packet_scale": clean(readiness.get("packet_scale")),
                "packet_relation_lane": clean(readiness.get("packet_relation_lane")),
                "packet_confidence": clean(readiness.get("packet_confidence")),
                "region": clean(readiness.get("region")),
                "theme": clean(readiness.get("theme")),
                "source_family": clean(readiness.get("source_family")),
                "five_year_bucket": clean(readiness.get("five_year_bucket")),
                "actual_year_span": clean(readiness.get("actual_year_span")),
                "cluster_size": clean(readiness.get("cluster_size")),
                "role_rows": clean(readiness.get("role_rows")),
                "anchor_candidate_count": (
                    counts.get("candidate_packet_anchor", 0)
                    + counts.get("provisional_main_anchor_needs_text", 0)
                    + counts.get("anchor_or_sibling_review", 0)
                ),
                "sub_candidate_count": counts.get("packet_member_review", 0) + counts.get("sub_under_packet_candidate", 0),
                "card_candidate_count": counts.get("card_context_candidate", 0),
                "appendix_candidate_count": counts.get("text_or_appendix_candidate", 0) + counts.get("appendix_any", 0),
                "top_candidate_surface_id": clean(top.get("surface_id")),
                "top_candidate_title": clean(top.get("title")),
                "top_anchor_review_score": top_score,
                "top_candidate_role": clean(top.get("proposed_relation_role")),
                "top_candidate_risk_flags": clean(top.get("risk_flags")),
                "blocking_reason": reason,
            }
        )
    return (
        sorted(cluster_out, key=lambda row: (row["manual_review_priority"] != "high", row["manual_review_priority"] != "medium", clean(row["anchor_review_lane"]), -as_int(row["role_rows"]))),
        sorted(candidate_out, key=lambda row: (clean(row["cluster_key"]), as_int(row["candidate_rank"]))),
    )


def summary_rows(cluster_rows: list[dict[str, Any]], candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "metric": "scope",
            "value": "non_mutating_research_packet_anchor_selection",
            "notes": "No rebuild, role override, image download, rights/image-state change, or frontend mirror write.",
        },
        {"metric": "cluster_review_rows", "value": len(cluster_rows), "notes": "Phase 1 anchor-selection clusters."},
        {"metric": "candidate_review_rows", "value": len(candidate_rows), "notes": "Top surface candidates written for manual anchor review."},
        {
            "metric": "can_seed_anchor_review",
            "value": sum(1 for row in cluster_rows if clean(row.get("can_seed_anchor_review")) == "true"),
            "notes": "Clusters with a plausible candidate for manual anchor review, not automatic role application.",
        },
    ]
    lane_counts = Counter(clean(row.get("anchor_review_lane")) for row in cluster_rows)
    priority_counts = Counter(clean(row.get("manual_review_priority")) for row in cluster_rows)
    scale_counts = Counter(clean(row.get("packet_scale")) for row in cluster_rows)
    for key, value in sorted(lane_counts.items()):
        rows.append({"metric": f"anchor_review_lane:{key}", "value": value, "notes": "Anchor review lane distribution."})
    for key, value in sorted(priority_counts.items()):
        rows.append({"metric": f"manual_review_priority:{key}", "value": value, "notes": "Manual review priority distribution."})
    for key, value in sorted(scale_counts.items()):
        rows.append({"metric": f"packet_scale:{key}", "value": value, "notes": "Phase 1 packet scale distribution."})
    return rows


def report_text(summary: list[dict[str, Any]], clusters: list[dict[str, Any]]) -> str:
    lines = [
        "# Research Packet Anchor Selection v1",
        "",
        "Scope: non-mutating audit for normal-main anchor selection blockers.",
        "",
        "This pass writes review queues only. It does not apply normal-main, sub,",
        "appendix, card, or text roles.",
        "",
        "## Summary",
        "",
    ]
    for row in summary:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## High-Priority Seed Candidates", ""])
    high_rows = [row for row in clusters if clean(row.get("manual_review_priority")) == "high" and clean(row.get("can_seed_anchor_review")) == "true"][:20]
    if not high_rows:
        lines.append("- None.")
    for row in high_rows:
        lines.append(
            f"- {row['cluster_key']}: lane={row['anchor_review_lane']}; top={row['top_candidate_surface_id']}; "
            f"score={row['top_anchor_review_score']}; subs={row['sub_candidate_count']}; cards={row['card_candidate_count']}"
        )
    lines.extend(["", "## Method Commitments", ""])
    lines.extend(
        [
            "- Candidate ranking is triage only; it does not apply packet roles.",
            "- Card-heavy clusters without sub structure remain support pools.",
            "- A cover main can organize normal mains, but cannot invent a normal-main anchor.",
            "- Same source family, region, or period is not sufficient parentage.",
            "- Weak graphic-object risk flags block automatic anchor promotion.",
        ]
    )
    lines.extend(["", "## Safety", ""])
    lines.extend(
        [
            "- No image files were downloaded.",
            "- No rights/source authority/image-state upgrades were made.",
            "- No packet role was applied by this audit.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    readiness = read_csv(IN_READINESS)
    role_rows = read_csv(IN_ROLE_QUEUE)
    clusters = read_csv(IN_CLUSTER_AUDIT)
    cluster_rows, candidate_rows = make_outputs(readiness, by_cluster(role_rows), cluster_map(clusters))
    summary = summary_rows(cluster_rows, candidate_rows)

    write_csv(OUT_CLUSTER, cluster_rows, CLUSTER_FIELDS)
    write_csv(OUT_CANDIDATES, candidate_rows, CANDIDATE_FIELDS)
    write_csv(OUT_SUMMARY, summary, SUMMARY_FIELDS)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(report_text(summary, cluster_rows), encoding="utf-8")

    print(f"cluster_review_rows={len(cluster_rows)}")
    print(f"candidate_review_rows={len(candidate_rows)}")
    print(f"can_seed_anchor_review={sum(1 for row in cluster_rows if clean(row['can_seed_anchor_review']) == 'true')}")
    print(f"wrote {OUT_CLUSTER.relative_to(ROOT)}")
    print(f"wrote {OUT_CANDIDATES.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
