#!/usr/bin/env python3
"""Audit packet-relation method signals from the full main/sub/text assessment.

This is a non-mutating second-pass audit. It reads the full-role assessment
CSV and writes review queues only. It does not rebuild payloads, apply role
overrides, download images, or change rights/image states.
"""

from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

IN_ASSESSMENT = DATA / "prefreeze_main_sub_text_full_role_assessment_v1.csv"

OUT_CLUSTER_AUDIT = DATA / "prefreeze_main_sub_text_packet_relation_cluster_audit_v1.csv"
OUT_ROLE_QUEUE = DATA / "prefreeze_main_sub_text_packet_relation_role_queue_v1.csv"
OUT_SAMPLE = DATA / "prefreeze_main_sub_text_packet_relation_validation_sample_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_main_sub_text_packet_relation_method_summary_v1.csv"
OUT_REPORT = DOCS / "MAIN_SUB_TEXT_PACKET_RELATION_METHOD_v1.md"

SAMPLE_TARGET = 800

SUMMARY_FIELDS = ["metric", "value", "notes"]
CLUSTER_FIELDS = [
    "cluster_key",
    "cluster_size",
    "region",
    "theme",
    "source_family",
    "five_year_bucket",
    "year_min",
    "year_max",
    "year_span",
    "main_count",
    "keep_main_anchor",
    "keep_main_add_text",
    "packet_anchor_review",
    "downgrade_to_sub_candidate",
    "downgrade_to_card_candidate",
    "manual_review",
    "convert_to_text_or_appendix",
    "median_anchor_score",
    "median_source_depth",
    "median_relation_density",
    "median_text_depth",
    "median_editorial_need",
    "median_risk_pressure",
    "high_score_anchor_count",
    "low_risk_anchor_count",
    "text_deficit_count",
    "sub_candidate_count",
    "card_context_count",
    "packet_relation_lane",
    "packet_confidence",
    "packet_reason",
    "sample_titles",
]
ROLE_FIELDS = [
    "surface_id",
    "capture_id",
    "year",
    "period_band",
    "five_year_bucket",
    "region",
    "theme",
    "source_family",
    "source_name",
    "title",
    "image_state",
    "cluster_key",
    "cluster_size",
    "cluster_lane",
    "cluster_confidence",
    "recommended_next_action",
    "proposed_relation_role",
    "parent_selection_hint",
    "minimum_text_pages",
    "text_page_reason",
    "relation_review_priority",
    "relation_apply_readiness",
    "relation_blockers",
    "anchor_strength_score",
    "source_depth_score",
    "relation_density_score",
    "text_depth_score",
    "design_object_confidence_score",
    "risk_pressure_score",
    "editorial_need_score",
    "risk_flags",
    "positive_flags",
    "review_question",
]


def clean(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def as_int(value: object) -> int:
    try:
        if clean(value) == "":
            return 0
        return int(float(clean(value)))
    except ValueError:
        return 0


def pct(numerator: int, denominator: int) -> float:
    return round(numerator * 100 / denominator, 2) if denominator else 0.0


def stable_hash(*parts: object) -> str:
    text = "||".join(clean(part) for part in parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def split_cluster_key(key: str) -> tuple[str, str, str, str]:
    parts = clean(key).split("|")
    while len(parts) < 4:
        parts.append("")
    return parts[0], parts[1], parts[2], parts[3]


def numbers(rows: list[dict[str, str]], field: str) -> list[int]:
    return [as_int(row.get(field)) for row in rows]


def med(rows: list[dict[str, str]], field: str) -> int:
    values = numbers(rows, field)
    return int(median(values)) if values else 0


def action_count(rows: list[dict[str, str]], action: str) -> int:
    return sum(1 for row in rows if clean(row.get("recommended_next_action")) == action)


def has_risk(row: dict[str, str], *needles: str) -> bool:
    text = clean(row.get("risk_flags")).casefold()
    return any(needle.casefold() in text for needle in needles)


def cluster_lane(rows: list[dict[str, str]]) -> tuple[str, str, str]:
    size = len(rows)
    region = clean(rows[0].get("region")) if rows else ""
    theme = clean(rows[0].get("theme")) if rows else ""
    family = clean(rows[0].get("source_family")) if rows else ""
    keep = action_count(rows, "keep_main_anchor")
    add_text = action_count(rows, "keep_main_add_text")
    packet = action_count(rows, "packet_anchor_review")
    sub = action_count(rows, "downgrade_to_sub_candidate")
    card = action_count(rows, "downgrade_to_card_candidate")
    manual = action_count(rows, "manual_review")
    text_deficit = sum(1 for row in rows if as_int(row.get("editorial_need_score")) >= 55)
    high_anchor = sum(1 for row in rows if as_int(row.get("overall_research_anchor_score")) >= 60)
    low_risk = sum(1 for row in rows if as_int(row.get("risk_pressure_score")) < 35)
    median_risk = med(rows, "risk_pressure_score")
    median_relation = med(rows, "relation_density_score")
    relation_load = keep + add_text + packet + sub
    card_ratio = card / size if size else 0
    is_macro_region = region in {"Global / transnational", "Unresolved region"} or "transnational" in region.casefold()
    is_broad_theme = theme in {"Modern typography and layout", "Unresolved theme"}
    is_commons = family == "Wikimedia Commons"

    if size >= 100 or (is_macro_region and size >= 25) or (is_broad_theme and is_commons and size >= 50):
        return (
            "macro_cluster_needs_split",
            "low",
            "Cluster key is too broad for packet parentage; split by object type, project, creator, source subseries, or narrower theme before sandbox use.",
        )

    if size >= 5 and high_anchor >= 1 and relation_load >= 3 and card_ratio < 0.45 and median_risk < 45:
        return (
            "strong_packet_candidate",
            "high",
            "Cluster has at least one plausible anchor, multiple relation-bearing members, and manageable risk.",
        )
    if size >= 3 and (packet + sub + add_text) >= 2 and median_relation >= 30:
        return (
            "packet_parentage_review",
            "medium",
            "Cluster has several packet/member candidates but needs parent selection before mutation.",
        )
    if add_text >= 2 or (text_deficit >= 3 and high_anchor >= 1):
        return (
            "text_scaffold_needed",
            "medium",
            "Cluster may support a packet, but editorial text is needed to make the main/sub relation useful.",
        )
    if card >= 3 and (card_ratio >= 0.55 or median_risk >= 55):
        return (
            "card_context_cluster",
            "medium",
            "Cluster is dominated by weak context, stamp, event, or file-source evidence.",
        )
    if size <= 2 and (keep + add_text) >= 1 and manual <= 1:
        return (
            "small_anchor_or_manual",
            "low",
            "Cluster is too small to infer packet structure; retain manual judgment.",
        )
    return (
        "mixed_manual_relation_review",
        "low",
        "Signals are mixed or sparse; this should not become an automatic override source.",
    )


def cluster_audit(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[clean(row.get("cluster_key"))].append(row)

    out: list[dict[str, Any]] = []
    for key, values in grouped.items():
        region, theme, family, bucket = split_cluster_key(key)
        years = [as_int(row.get("year")) for row in values if as_int(row.get("year"))]
        year_min = min(years) if years else ""
        year_max = max(years) if years else ""
        year_span = year_max - year_min if years else ""
        lane, confidence, reason = cluster_lane(values)
        values_sorted = sorted(values, key=lambda row: (-as_int(row.get("overall_research_anchor_score")), clean(row.get("title"))))
        out.append(
            {
                "cluster_key": key,
                "cluster_size": len(values),
                "region": region,
                "theme": theme,
                "source_family": family,
                "five_year_bucket": bucket,
                "year_min": year_min,
                "year_max": year_max,
                "year_span": year_span,
                "main_count": len(values),
                "keep_main_anchor": action_count(values, "keep_main_anchor"),
                "keep_main_add_text": action_count(values, "keep_main_add_text"),
                "packet_anchor_review": action_count(values, "packet_anchor_review"),
                "downgrade_to_sub_candidate": action_count(values, "downgrade_to_sub_candidate"),
                "downgrade_to_card_candidate": action_count(values, "downgrade_to_card_candidate"),
                "manual_review": action_count(values, "manual_review"),
                "convert_to_text_or_appendix": action_count(values, "convert_to_text_or_appendix"),
                "median_anchor_score": med(values, "overall_research_anchor_score"),
                "median_source_depth": med(values, "source_depth_score"),
                "median_relation_density": med(values, "relation_density_score"),
                "median_text_depth": med(values, "text_depth_score"),
                "median_editorial_need": med(values, "editorial_need_score"),
                "median_risk_pressure": med(values, "risk_pressure_score"),
                "high_score_anchor_count": sum(1 for row in values if as_int(row.get("overall_research_anchor_score")) >= 60),
                "low_risk_anchor_count": sum(1 for row in values if as_int(row.get("risk_pressure_score")) < 35),
                "text_deficit_count": sum(1 for row in values if as_int(row.get("editorial_need_score")) >= 55),
                "sub_candidate_count": action_count(values, "downgrade_to_sub_candidate"),
                "card_context_count": action_count(values, "downgrade_to_card_candidate"),
                "packet_relation_lane": lane,
                "packet_confidence": confidence,
                "packet_reason": reason,
                "sample_titles": " | ".join(clean(row.get("title")) for row in values_sorted[:5])[:900],
            }
        )
    out.sort(
        key=lambda row: (
            {"strong_packet_candidate": 0, "packet_parentage_review": 1, "text_scaffold_needed": 2}.get(
                clean(row.get("packet_relation_lane")), 9
            ),
            -as_int(row.get("cluster_size")),
            -as_int(row.get("median_anchor_score")),
            clean(row.get("cluster_key")),
        )
    )
    return out


def role_for(row: dict[str, str], cluster: dict[str, Any]) -> tuple[str, str, str]:
    action = clean(row.get("recommended_next_action"))
    cluster_lane_value = clean(cluster.get("packet_relation_lane"))
    if action == "keep_main_add_text":
        return (
            "provisional_main_anchor_needs_text",
            "select self as anchor only if text plan is accepted",
            "Can remain main only after editorial scaffold is drafted and reviewed.",
        )
    if action == "packet_anchor_review":
        if as_int(row.get("overall_research_anchor_score")) >= as_int(cluster.get("median_anchor_score")) + 8:
            return (
                "anchor_or_sibling_review",
                "compare against top cluster anchor candidates",
                "Could anchor the packet, but sibling/parent relation must be checked.",
            )
        return (
            "packet_member_review",
            "attach to strongest nearby anchor candidate in cluster",
            "Likely useful as a member, but parent anchor is unresolved.",
        )
    if action == "downgrade_to_sub_candidate":
        return (
            "sub_under_packet_candidate",
            "attach to strongest low-risk anchor candidate in cluster",
            "Relation value is stronger than standalone main authority.",
        )
    if action == "downgrade_to_card_candidate":
        return (
            "card_context_candidate",
            "attach only as context/evidence if packet anchor exists",
            "Evidence should be preserved without carrying main-sheet authority.",
        )
    if action == "convert_to_text_or_appendix":
        return (
            "text_or_appendix_candidate",
            "attach as source-register or appendix evidence",
            "This is better treated as text/appendix evidence than object main.",
        )
    if action == "keep_main_anchor" and cluster_lane_value in {"strong_packet_candidate", "text_scaffold_needed"}:
        return (
            "candidate_packet_anchor",
            "possible parent for sub/card/text members in cluster",
            "High enough to test as packet anchor after relation review.",
        )
    return (
        "manual_relation_review",
        "manual parent needed",
        "No automatic relation role should be inferred.",
    )


def minimum_text_pages(row: dict[str, str], cluster: dict[str, Any], proposed_role: str) -> tuple[int, str]:
    if proposed_role in {"card_context_candidate", "text_or_appendix_candidate"}:
        return 0, "Support evidence should not receive filler text."
    if proposed_role == "sub_under_packet_candidate":
        return 1, "Sub sheet needs a short relation note only if attached to a packet."
    base = 1 if proposed_role in {"candidate_packet_anchor", "provisional_main_anchor_needs_text", "anchor_or_sibling_review"} else 0
    size = as_int(cluster.get("cluster_size"))
    editorial = as_int(row.get("editorial_need_score"))
    risk = as_int(row.get("risk_pressure_score"))
    add = 0
    if size >= 5:
        add += 1
    if size >= 10:
        add += 1
    if editorial >= 70:
        add += 1
    if risk >= 45 and proposed_role != "manual_relation_review":
        add += 1
    pages = min(4, base + add)
    if pages <= 0:
        return 0, "No text requirement can be assigned before parentage review."
    return pages, "Minimum text estimate based on cluster size, editorial need, and risk pressure."


def blockers(row: dict[str, str], cluster: dict[str, Any], proposed_role: str) -> str:
    found: list[str] = []
    if has_risk(row, "stamp_or_philatelic"):
        found.append("stamp_or_philatelic_manual")
    if has_risk(row, "weak_context"):
        found.append("weak_context_manual")
    if has_risk(row, "non_design_drift"):
        found.append("non_design_drift_manual")
    if has_risk(row, "source_register"):
        found.append("source_register_manual")
    if as_int(row.get("source_depth_score")) < 25 and proposed_role not in {"card_context_candidate", "text_or_appendix_candidate"}:
        found.append("thin_source_depth")
    if as_int(row.get("design_object_confidence_score")) < 55 and proposed_role not in {"card_context_candidate", "text_or_appendix_candidate"}:
        found.append("weak_design_object_signal")
    if clean(cluster.get("packet_confidence")) == "low" and proposed_role != "manual_relation_review":
        found.append("low_cluster_confidence")
    return "; ".join(found) or "none"


def review_question(proposed_role: str) -> str:
    questions = {
        "candidate_packet_anchor": "Can this surface act as the parent packet anchor without overclaiming?",
        "provisional_main_anchor_needs_text": "What text pages are required before this remains main?",
        "anchor_or_sibling_review": "Is this an anchor, or a sibling under a stronger nearby anchor?",
        "packet_member_review": "Which main anchor should own this as a member?",
        "sub_under_packet_candidate": "Which packet anchor should own this as a sub sheet?",
        "card_context_candidate": "Would card treatment preserve evidence without hiding research value?",
        "text_or_appendix_candidate": "Should this become source-register text or appendix evidence?",
    }
    return questions.get(proposed_role, "What relation role is justified by source depth, cluster context, and risk?")


def relation_priority(row: dict[str, str], cluster: dict[str, Any], proposed_role: str, blockers_text: str) -> int:
    score = as_int(row.get("relation_density_score")) + as_int(row.get("editorial_need_score"))
    if proposed_role in {"candidate_packet_anchor", "provisional_main_anchor_needs_text", "anchor_or_sibling_review"}:
        score += 35
    if proposed_role == "sub_under_packet_candidate":
        score += 25
    if clean(cluster.get("packet_relation_lane")) == "strong_packet_candidate":
        score += 20
    if clean(cluster.get("packet_relation_lane")) == "packet_parentage_review":
        score += 12
    if blockers_text != "none":
        score -= 15
    return max(0, score)


def role_queue(rows: list[dict[str, str]], clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cluster_lookup = {clean(row.get("cluster_key")): row for row in clusters}
    out: list[dict[str, Any]] = []
    target_actions = {
        "keep_main_anchor",
        "keep_main_add_text",
        "packet_anchor_review",
        "downgrade_to_sub_candidate",
        "downgrade_to_card_candidate",
        "convert_to_text_or_appendix",
    }
    for row in rows:
        if clean(row.get("recommended_next_action")) not in target_actions:
            continue
        cluster = cluster_lookup.get(clean(row.get("cluster_key")), {})
        proposed_role, parent_hint, role_reason = role_for(row, cluster)
        min_pages, text_reason = minimum_text_pages(row, cluster, proposed_role)
        blocker_text = blockers(row, cluster, proposed_role)
        readiness = "method_review_only"
        if blocker_text == "none" and clean(cluster.get("packet_confidence")) in {"high", "medium"}:
            readiness = "eligible_for_next_sandbox_review"
        if proposed_role in {"card_context_candidate", "text_or_appendix_candidate"}:
            readiness = "support_only_review"
        priority = relation_priority(row, cluster, proposed_role, blocker_text)
        out.append(
            {
                "surface_id": clean(row.get("surface_id")),
                "capture_id": clean(row.get("capture_id")),
                "year": clean(row.get("year")),
                "period_band": clean(row.get("period_band")),
                "five_year_bucket": clean(row.get("five_year_bucket")),
                "region": clean(row.get("region")),
                "theme": clean(row.get("theme")),
                "source_family": clean(row.get("source_family")),
                "source_name": clean(row.get("source_name")),
                "title": clean(row.get("title")),
                "image_state": clean(row.get("image_state")),
                "cluster_key": clean(row.get("cluster_key")),
                "cluster_size": clean(row.get("cluster_size")),
                "cluster_lane": clean(cluster.get("packet_relation_lane")),
                "cluster_confidence": clean(cluster.get("packet_confidence")),
                "recommended_next_action": clean(row.get("recommended_next_action")),
                "proposed_relation_role": proposed_role,
                "parent_selection_hint": parent_hint,
                "minimum_text_pages": min_pages,
                "text_page_reason": text_reason,
                "relation_review_priority": priority,
                "relation_apply_readiness": readiness,
                "relation_blockers": blocker_text,
                "anchor_strength_score": clean(row.get("anchor_strength_score")),
                "source_depth_score": clean(row.get("source_depth_score")),
                "relation_density_score": clean(row.get("relation_density_score")),
                "text_depth_score": clean(row.get("text_depth_score")),
                "design_object_confidence_score": clean(row.get("design_object_confidence_score")),
                "risk_pressure_score": clean(row.get("risk_pressure_score")),
                "editorial_need_score": clean(row.get("editorial_need_score")),
                "risk_flags": clean(row.get("risk_flags")),
                "positive_flags": clean(row.get("positive_flags")),
                "review_question": f"{review_question(proposed_role)} {role_reason}",
            }
        )
    out.sort(
        key=lambda row: (
            {"eligible_for_next_sandbox_review": 0, "method_review_only": 1, "support_only_review": 2}.get(
                clean(row.get("relation_apply_readiness")), 9
            ),
            -as_int(row.get("relation_review_priority")),
            clean(row.get("proposed_relation_role")),
            clean(row.get("surface_id")),
        )
    )
    return out


def stratified_sample(rows: list[dict[str, Any]], target: int) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            clean(row.get("proposed_relation_role")),
            clean(row.get("relation_apply_readiness")),
            clean(row.get("period_band")),
            clean(row.get("region")),
            clean(row.get("source_family")),
        )
        grouped[key].append(row)
    for values in grouped.values():
        values.sort(key=lambda row: (-as_int(row.get("relation_review_priority")), stable_hash(row.get("surface_id"))))

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    keys = sorted(grouped, key=lambda key: (len(grouped[key]), key))
    while len(selected) < target and keys:
        advanced = False
        for key in keys:
            values = grouped[key]
            while values:
                candidate = values.pop(0)
                sid = clean(candidate.get("surface_id"))
                if sid not in seen:
                    selected.append(candidate)
                    seen.add(sid)
                    advanced = True
                    break
            if len(selected) >= target:
                break
        keys = [key for key in keys if grouped[key]]
        if not advanced:
            break

    if len(selected) < target:
        remaining = [row for row in rows if clean(row.get("surface_id")) not in seen]
        remaining.sort(key=lambda row: (-as_int(row.get("relation_review_priority")), stable_hash(row.get("surface_id"))))
        selected.extend(remaining[: target - len(selected)])
    return selected


def summary_rows(rows: list[dict[str, str]], clusters: list[dict[str, Any]], queue: list[dict[str, Any]], sample: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = [
        {"metric": "scope", "value": "non_mutating_packet_relation_method_audit", "notes": "No rebuild, no role override, no image download, no rights/image-state change."},
        {"metric": "assessment_rows_read", "value": len(rows), "notes": "Rows read from full-role main-sheet assessment."},
        {"metric": "cluster_rows", "value": len(clusters), "notes": "Unique relation clusters audited."},
        {"metric": "role_queue_rows", "value": len(queue), "notes": "Rows with relation-role proposals for review."},
        {"metric": "validation_sample_rows", "value": len(sample), "notes": "Stratified sample for next packet relation review."},
    ]
    for lane, count in Counter(clean(row.get("packet_relation_lane")) for row in clusters).most_common():
        out.append({"metric": f"cluster_lane:{lane}", "value": count, "notes": "Packet relation cluster lane distribution."})
    for role, count in Counter(clean(row.get("proposed_relation_role")) for row in queue).most_common():
        out.append({"metric": f"queue_role:{role}", "value": count, "notes": "Proposed relation role distribution."})
    for readiness, count in Counter(clean(row.get("relation_apply_readiness")) for row in queue).most_common():
        out.append({"metric": f"queue_readiness:{readiness}", "value": count, "notes": "Relation review readiness distribution."})
    for pages, count in Counter(clean(row.get("minimum_text_pages")) for row in queue).most_common():
        out.append({"metric": f"minimum_text_pages:{pages}", "value": count, "notes": "Estimated minimum text page requirement."})
    for action, count in Counter(clean(row.get("recommended_next_action")) for row in queue).most_common():
        out.append({"metric": f"queue_source_action:{action}", "value": count, "notes": "Original full-role action represented in relation queue."})
    return out


def write_report(rows: list[dict[str, str]], clusters: list[dict[str, Any]], queue: list[dict[str, Any]], sample: list[dict[str, Any]], summary: list[dict[str, Any]]) -> None:
    lane_counts = Counter(clean(row.get("packet_relation_lane")) for row in clusters)
    role_counts = Counter(clean(row.get("proposed_relation_role")) for row in queue)
    readiness_counts = Counter(clean(row.get("relation_apply_readiness")) for row in queue)
    eligible = readiness_counts.get("eligible_for_next_sandbox_review", 0)
    support = readiness_counts.get("support_only_review", 0)
    method_only = readiness_counts.get("method_review_only", 0)
    lines = [
        "# Main/Sub/Text Packet Relation Method v1",
        "",
        "Scope: non-mutating second-pass audit for packet relation, text need, and main/sub/card boundary planning.",
        "",
        "This pass reads the full-role assessment only. It does not apply overrides, rebuild payloads, download images, or change rights/image states.",
        "",
        "## Inputs and Outputs",
        "",
        f"- Assessment rows read: {len(rows)}.",
        f"- Relation clusters audited: {len(clusters)}.",
        f"- Relation role queue rows: {len(queue)}.",
        f"- Validation sample rows: {len(sample)}.",
        "",
        "## Cluster Lanes",
        "",
    ]
    for lane, count in lane_counts.most_common():
        lines.append(f"- `{lane}`: {count}.")
    lines.extend(["", "## Proposed Relation Roles", ""])
    for role, count in role_counts.most_common():
        lines.append(f"- `{role}`: {count}.")
    lines.extend(
        [
            "",
            "## Readiness",
            "",
            f"- `eligible_for_next_sandbox_review`: {eligible}.",
            f"- `method_review_only`: {method_only}.",
            f"- `support_only_review`: {support}.",
            "",
            "## Method Reading",
            "",
            "- `strong_packet_candidate` clusters may be used to test parent/child relation rules, but they are not automatic release mutations.",
            "- `packet_parentage_review` is the central backlog: these clusters likely contain usable sub/main relations, but parent selection must be explicit.",
            "- `text_scaffold_needed` means main status depends on real editorial text; generated filler should not count.",
            "- `macro_cluster_needs_split` is a warning lane for over-broad buckets such as global Commons typography groups; these need narrower source series, creator, project, object-type, or theme splitting before sandbox use.",
            "- `card_context_cluster` preserves weak context, stamp, event/photo, or source-file evidence without treating it as a main research anchor.",
            "",
            "## Advantages",
            "",
            "- Separates packet relation design from rights/image/source-count work.",
            "- Keeps main-sheet demotion reversible during methodology testing.",
            "- Provides a concrete text-page estimate without forcing text generation now.",
            "- Makes parent selection auditable at the cluster level before any rebuild.",
            "",
            "## Disadvantages",
            "",
            "- Cluster keys are still provisional and depend on current region/theme/source/five-year grouping.",
            "- Commons-heavy source distribution can overrepresent card-context decisions.",
            "- The method cannot prove final reading quality until a later small rebuild displays the packet structure.",
            "- Text-page estimates are planning signals, not release requirements yet.",
            "",
            "## Next Permitted Action",
            "",
            "Review `data/prefreeze_main_sub_text_packet_relation_validation_sample_v1.csv` and use the `eligible_for_next_sandbox_review` rows for a later, limited sandbox preview only after parent-selection rules are accepted.",
            "",
            "## Safety",
            "",
            "- No image files were downloaded.",
            "- No rights, source authority, authorship, or IMG01/IMG03 upgrades were made.",
            "- Region scarcity, source family, and period signals remain internal triage signals only.",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = read_csv(IN_ASSESSMENT)
    clusters = cluster_audit(rows)
    queue = role_queue(rows, clusters)
    sample = stratified_sample(queue, SAMPLE_TARGET)
    summary = summary_rows(rows, clusters, queue, sample)

    write_csv(OUT_CLUSTER_AUDIT, clusters, CLUSTER_FIELDS)
    write_csv(OUT_ROLE_QUEUE, queue, ROLE_FIELDS)
    write_csv(OUT_SAMPLE, sample, ROLE_FIELDS)
    write_csv(OUT_SUMMARY, summary, SUMMARY_FIELDS)
    write_report(rows, clusters, queue, sample, summary)

    print(f"assessment_rows_read={len(rows)}")
    print(f"cluster_rows={len(clusters)}")
    print(f"role_queue_rows={len(queue)}")
    print(f"validation_sample_rows={len(sample)}")
    for row in summary[:20]:
        print(f"{row['metric']}={row['value']}")
    print(f"wrote {OUT_CLUSTER_AUDIT.relative_to(ROOT)}")
    print(f"wrote {OUT_ROLE_QUEUE.relative_to(ROOT)}")
    print(f"wrote {OUT_SAMPLE.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
