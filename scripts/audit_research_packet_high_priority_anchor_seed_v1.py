#!/usr/bin/env python3
"""Prepare high-priority anchor-selection seeds for manual packet review.

This non-mutating pass focuses on the 42 high-priority anchor-selection
clusters. It separates cover/editorial seed candidates from anchor-only and
card-heavy review cases. It writes review CSVs and a report only.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

IN_CLUSTER = DATA / "research_packet_anchor_selection_cluster_review_v1.csv"
IN_CANDIDATES = DATA / "research_packet_anchor_selection_candidate_review_v1.csv"

OUT_SEEDS = DATA / "research_packet_high_priority_anchor_seed_plan_v1.csv"
OUT_CANDIDATES = DATA / "research_packet_high_priority_anchor_seed_candidates_v1.csv"
OUT_SUMMARY = DATA / "research_packet_high_priority_anchor_seed_summary_v1.csv"
OUT_REPORT = DOCS / "RESEARCH_PACKET_HIGH_PRIORITY_ANCHOR_SEEDS_v1.md"

SEED_FIELDS = [
    "cluster_key",
    "seed_lane",
    "recommended_next_artifact",
    "manual_decision_needed",
    "sandbox_allowed_after_review",
    "packet_scale",
    "anchor_review_lane",
    "region",
    "theme",
    "source_family",
    "five_year_bucket",
    "actual_year_span",
    "sub_candidate_count",
    "card_candidate_count",
    "candidate_count_written",
    "top_candidate_surface_id",
    "top_candidate_title",
    "top_anchor_review_score",
    "top_candidate_role",
    "top_candidate_risk_flags",
    "candidate_surface_ids",
    "candidate_titles",
    "seed_reason",
]

CANDIDATE_FIELDS = [
    "cluster_key",
    "seed_lane",
    "candidate_rank",
    "surface_id",
    "year",
    "title",
    "image_state",
    "source_family",
    "source_name",
    "proposed_relation_role",
    "anchor_review_score",
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


def seed_lane(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    anchor_lane = clean(row.get("anchor_review_lane"))
    scale = clean(row.get("packet_scale"))
    sub_count = as_int(row.get("sub_candidate_count"))
    card_count = as_int(row.get("card_candidate_count"))
    top_score = as_float(row.get("top_anchor_review_score"))
    risk = clean(row.get("top_candidate_risk_flags")).casefold()
    title = clean(row.get("top_candidate_title")).casefold()
    card_heavy = card_count > max(8, sub_count * 2)
    weak_risk = any(term in risk for term in ("stamp", "philatelic", "event", "photo", "session", "profile", "interview"))
    object_drift_terms = (
        "marianne north",
        "flowers",
        "flower",
        "shrub",
        "humming bird",
        "hummingbird",
        "jacket",
        "model truck",
        "figure, advertising",
        "press photo",
        "insect",
        "beetle",
        "natural history",
    )
    graphic_terms = (
        "poster",
        "advertisement",
        "advertising",
        "brochure",
        "catalogue",
        "catalog",
        "print",
        "typography",
        "cover",
        "magazine",
        "booklet",
        "logo",
    )

    if weak_risk:
        return (
            "weak_object_hold",
            "weak-object evidence review memo",
            "verify that top candidate is a design object before any packet work",
            "false",
            "top candidate has weak-object risk flags",
        )
    if any(term in title for term in object_drift_terms) and not any(term in title for term in graphic_terms):
        return (
            "graphic_object_scope_review",
            "graphic-object scope review note",
            "verify this is graphic design evidence rather than adjacent visual/object evidence",
            "false",
            "top title suggests adjacent visual/object evidence rather than graphic design packet anchor",
        )
    if anchor_lane == "strong_packet_anchor_candidate_review" and not card_heavy and top_score >= 75:
        return (
            "cover_editorial_seed_ready",
            "cover scope draft + curated editorial reading note outline",
            "confirm top candidate as normal-main anchor and choose packet title",
            "true",
            "strong packet lane with low card pressure and high top-anchor score",
        )
    if anchor_lane == "sub_rich_anchor_candidate_review" and not card_heavy and sub_count >= 7 and top_score >= 65:
        return (
            "anchor_then_cover_seed",
            "normal-main anchor confirmation sheet, then cover/editorial outline",
            "confirm whether top candidate can carry normal-main status",
            "true",
            "sub-rich cluster has enough member structure for a reviewed packet seed",
        )
    if anchor_lane == "sub_rich_anchor_candidate_review" and card_heavy:
        return (
            "card_pressure_anchor_review",
            "anchor confirmation plus card/support pruning list",
            "separate candidate subs from support cards before cover/editorial work",
            "false",
            "card pressure is too high for immediate cover/editorial seeding",
        )
    if scale == "medium" and sub_count >= 3 and top_score >= 65:
        return (
            "anchor_confirmation_seed",
            "normal-main anchor confirmation sheet",
            "confirm anchor and decide whether this remains standalone or joins a larger packet",
            "false",
            "medium packet has plausible anchor signal but needs manual confirmation first",
        )
    return (
        "manual_hold",
        "manual anchor triage note",
        "review after cleaner high-priority seed lanes",
        "false",
        "does not satisfy high-confidence seed conditions",
    )


def make_outputs(
    clusters: list[dict[str, str]],
    candidates_by_cluster: dict[str, list[dict[str, str]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    high = [row for row in clusters if clean(row.get("manual_review_priority")) == "high"]
    seed_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []

    for row in high:
        key = clean(row.get("cluster_key"))
        lane, artifact, decision, sandbox, reason = seed_lane(row)
        candidates = sorted(
            candidates_by_cluster.get(key, []),
            key=lambda item: (as_int(item.get("candidate_rank")), -as_float(item.get("anchor_review_score"))),
        )[:5]
        seed_rows.append(
            {
                "cluster_key": key,
                "seed_lane": lane,
                "recommended_next_artifact": artifact,
                "manual_decision_needed": decision,
                "sandbox_allowed_after_review": sandbox,
                "packet_scale": clean(row.get("packet_scale")),
                "anchor_review_lane": clean(row.get("anchor_review_lane")),
                "region": clean(row.get("region")),
                "theme": clean(row.get("theme")),
                "source_family": clean(row.get("source_family")),
                "five_year_bucket": clean(row.get("five_year_bucket")),
                "actual_year_span": clean(row.get("actual_year_span")),
                "sub_candidate_count": clean(row.get("sub_candidate_count")),
                "card_candidate_count": clean(row.get("card_candidate_count")),
                "candidate_count_written": len(candidates),
                "top_candidate_surface_id": clean(row.get("top_candidate_surface_id")),
                "top_candidate_title": clean(row.get("top_candidate_title")),
                "top_anchor_review_score": clean(row.get("top_anchor_review_score")),
                "top_candidate_role": clean(row.get("top_candidate_role")),
                "top_candidate_risk_flags": clean(row.get("top_candidate_risk_flags")),
                "candidate_surface_ids": "; ".join(clean(item.get("surface_id")) for item in candidates),
                "candidate_titles": " | ".join(clean(item.get("title")) for item in candidates),
                "seed_reason": reason,
            }
        )
        for item in candidates:
            candidate_rows.append(
                {
                    "cluster_key": key,
                    "seed_lane": lane,
                    "candidate_rank": clean(item.get("candidate_rank")),
                    "surface_id": clean(item.get("surface_id")),
                    "year": clean(item.get("year")),
                    "title": clean(item.get("title")),
                    "image_state": clean(item.get("image_state")),
                    "source_family": clean(item.get("source_family")),
                    "source_name": clean(item.get("source_name")),
                    "proposed_relation_role": clean(item.get("proposed_relation_role")),
                    "anchor_review_score": clean(item.get("anchor_review_score")),
                    "risk_flags": clean(item.get("risk_flags")),
                    "positive_flags": clean(item.get("positive_flags")),
                    "candidate_use": clean(item.get("candidate_use")),
                    "manual_check": "seed candidate only; do not apply role automatically",
                }
            )

    order = {
        "cover_editorial_seed_ready": 0,
        "anchor_then_cover_seed": 1,
        "anchor_confirmation_seed": 2,
        "card_pressure_anchor_review": 3,
        "weak_object_hold": 4,
        "manual_hold": 5,
    }
    seed_rows.sort(key=lambda item: (order.get(clean(item.get("seed_lane")), 99), -as_float(item.get("top_anchor_review_score")), clean(item.get("cluster_key"))))
    candidate_rows.sort(key=lambda item: (order.get(clean(item.get("seed_lane")), 99), clean(item.get("cluster_key")), as_int(item.get("candidate_rank"))))
    return seed_rows, candidate_rows


def summary_rows(seeds: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "metric": "scope",
            "value": "non_mutating_high_priority_anchor_seed_plan",
            "notes": "No rebuild, role override, image download, rights/image-state change, or frontend mirror write.",
        },
        {"metric": "high_priority_seed_rows", "value": len(seeds), "notes": "High-priority anchor-selection clusters."},
        {"metric": "candidate_rows", "value": len(candidates), "notes": "Candidate rows copied into the seed review packet."},
        {
            "metric": "sandbox_allowed_after_review",
            "value": sum(1 for row in seeds if clean(row.get("sandbox_allowed_after_review")) == "true"),
            "notes": "Clusters that may enter sandbox only after manual anchor confirmation.",
        },
    ]
    lane_counts = Counter(clean(row.get("seed_lane")) for row in seeds)
    source_counts = Counter(clean(row.get("source_family")) for row in seeds)
    for key, value in sorted(lane_counts.items()):
        rows.append({"metric": f"seed_lane:{key}", "value": value, "notes": "High-priority seed lane distribution."})
    for key, value in sorted(source_counts.items()):
        rows.append({"metric": f"source_family:{key}", "value": value, "notes": "High-priority seed source-family distribution."})
    return rows


def report_text(summary: list[dict[str, Any]], seeds: list[dict[str, Any]]) -> str:
    lines = [
        "# Research Packet High-Priority Anchor Seeds v1",
        "",
        "Scope: non-mutating seed plan for high-priority anchor review.",
        "",
        "This pass separates high-priority anchor candidates into manual review",
        "lanes. It does not apply packet roles or rebuild any payload.",
        "",
        "## Summary",
        "",
    ]
    for row in summary:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## First Seed Rows", ""])
    for row in seeds[:20]:
        lines.append(
            f"- {row['cluster_key']}: lane={row['seed_lane']}; top={row['top_candidate_surface_id']}; "
            f"subs={row['sub_candidate_count']}; cards={row['card_candidate_count']}; sandbox_after_review={row['sandbox_allowed_after_review']}"
        )
    lines.extend(["", "## Method Commitments", ""])
    lines.extend(
        [
            "- `sandbox_allowed_after_review` still requires manual anchor confirmation.",
            "- Card pressure blocks immediate cover/editorial seeding.",
            "- Strong-packet and sub-rich candidates are separated because they need different review artifacts.",
            "- Candidate ordering is triage only, not role assignment.",
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
    clusters = read_csv(IN_CLUSTER)
    candidates = read_csv(IN_CANDIDATES)
    seeds, seed_candidates = make_outputs(clusters, by_cluster(candidates))
    summary = summary_rows(seeds, seed_candidates)

    write_csv(OUT_SEEDS, seeds, SEED_FIELDS)
    write_csv(OUT_CANDIDATES, seed_candidates, CANDIDATE_FIELDS)
    write_csv(OUT_SUMMARY, summary, SUMMARY_FIELDS)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(report_text(summary, seeds), encoding="utf-8")

    print(f"high_priority_seed_rows={len(seeds)}")
    print(f"candidate_rows={len(seed_candidates)}")
    print(f"sandbox_allowed_after_review={sum(1 for row in seeds if clean(row['sandbox_allowed_after_review']) == 'true')}")
    print(f"wrote {OUT_SEEDS.relative_to(ROOT)}")
    print(f"wrote {OUT_CANDIDATES.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
