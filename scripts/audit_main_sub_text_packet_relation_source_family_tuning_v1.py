#!/usr/bin/env python3
"""Build a cautious source-family tuning audit for packet relation rules.

This pass explains why non-Commons packet relation clusters are not yet ready
for broader sandbox application. It emits review queues and rule-signal
recommendations only. It does not rebuild payloads, apply overrides, download
images, or change rights/image states.
"""

from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

IN_SCOPE = DATA / "prefreeze_main_sub_text_packet_relation_source_family_scope_v1.csv"
IN_CLUSTERS = DATA / "prefreeze_main_sub_text_packet_relation_source_family_cluster_review_v1.csv"
IN_ROLES = DATA / "prefreeze_main_sub_text_packet_relation_source_family_role_review_v1.csv"
IN_ROLE_QUEUE = DATA / "prefreeze_main_sub_text_packet_relation_role_queue_v1.csv"

OUT_MATRIX = DATA / "prefreeze_main_sub_text_packet_relation_source_family_tuning_matrix_v1.csv"
OUT_BLOCKERS = DATA / "prefreeze_main_sub_text_packet_relation_source_family_cluster_blockers_v1.csv"
OUT_RULES = DATA / "prefreeze_main_sub_text_packet_relation_source_family_rule_candidates_v1.csv"
OUT_SEEDS = DATA / "prefreeze_main_sub_text_packet_relation_source_family_tiny_sandbox_seed_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_main_sub_text_packet_relation_source_family_tuning_summary_v1.csv"
OUT_REPORT = DOCS / "MAIN_SUB_TEXT_PACKET_RELATION_SOURCE_FAMILY_TUNING_v1.md"

MAX_SEEDS = 60

SUMMARY_FIELDS = ["metric", "value", "notes"]
MATRIX_FIELDS = [
    "source_family",
    "family_class",
    "role_rows",
    "cluster_rows",
    "eligible_rows",
    "eligible_cluster_rows",
    "scope_candidate_but_blocked_clusters",
    "packet_parentage_review_clusters",
    "strong_high_clusters",
    "primary_blocker",
    "dominant_scope_reason",
    "dominant_relation_blocker",
    "dominant_role",
    "dominant_readiness",
    "tuning_status",
    "tuning_signal",
    "required_evidence",
    "risk_controls",
    "next_action",
]
BLOCKER_FIELDS = [
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
    "scope_status",
    "scope_reason",
    "blocking_dimensions",
    "manual_resolution_path",
    "seed_priority",
    "sample_titles",
]
RULE_FIELDS = [
    "source_family",
    "family_class",
    "signal_name",
    "signal_scope",
    "required_evidence",
    "blocked_actions",
    "risk_level",
    "audit_priority",
    "why_this_family",
]
SEED_FIELDS = [
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
    "sample_titles",
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


def stable_hash(*parts: object) -> str:
    text = "||".join(clean(part) for part in parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def is_macro_region(region: str) -> bool:
    folded = clean(region).casefold()
    return "transnational" in folded or folded.startswith("global") or folded.startswith("unresolved")


def split_blockers(text: str) -> list[str]:
    value = clean(text)
    if not value or value == "none":
        return []
    return [part.strip() for part in value.split(";") if part.strip()]


def first_counter(counter: Counter[str]) -> str:
    return counter.most_common(1)[0][0] if counter else ""


def source_signal(family: str, family_class: str) -> tuple[str, str, str, str]:
    folded = clean(family).casefold()
    if "gallica" in folded or "bnf" in folded:
        return (
            "bibliographic_sequence_signal",
            "title stem, BnF/Gallica record type, view/page count, date evidence, and shared bibliographic collection context",
            "Do not treat Gallica volume/page adjacency as design-object parentage without source text and non-macro region evidence.",
            "high",
        )
    if "contentdm" in folded:
        return (
            "collection_record_series_signal",
            "CONTENTdm collection name, object type, place/date metadata, and repeated source collection identifiers",
            "Do not collapse same-platform records into packets unless collection/series membership is explicit.",
            "high",
        )
    if "internet archive" in folded:
        return (
            "scan_or_publication_host_signal",
            "publication title, archive item id, page/volume relation, source-side metadata, and object-level design relevance",
            "Do not let hosting source alone define a packet; avoid global/transnational packeting without region resolution.",
            "high",
        )
    if any(term in folded for term in ("digitalnz", "te papa", "wellcome", "smithsonian", "cleveland", "art institute", "v&a")):
        return (
            "collection_api_object_signal",
            "institution object id, collection/department, object type, date/place, maker, and source description",
            "Do not convert museum/API siblings into sub sheets unless an anchor work or project relation is explicit.",
            "medium",
        )
    if any(term in folded for term in ("naidoc", "letterform", "another graphic", "design", "poster gallery", "desain", "gala", "memory project", "asian film")):
        return (
            "editorial_project_or_event_signal",
            "project/studio/exhibition/event context, curatorial text, creator relation, date span, and repeated title/project markers",
            "Do not make event photos, interviews, profiles, or thin posts into packet members without design-object evidence.",
            "high",
        )
    if family_class == "library_archive_or_aggregator":
        return (
            "library_archive_series_signal",
            "collection/series id, bibliographic hierarchy, source-side relation text, date/place, and object type",
            "Do not infer packet parentage from library platform alone.",
            "medium",
        )
    if family_class == "museum_or_collection_api":
        return (
            "museum_collection_relation_signal",
            "object id, department/collection, source description, date/place, creator, and object type",
            "Do not infer main/sub relation from same museum collection alone.",
            "medium",
        )
    return (
        "manual_source_family_signal",
        "source-specific record structure, explicit relation text, date/place, and object type",
        "No automatic role upgrade until this family has a reviewed relation rule.",
        "high",
    )


def cluster_blocking_dimensions(cluster: dict[str, str]) -> list[str]:
    dims: list[str] = []
    if is_macro_region(cluster.get("region", "")):
        dims.append("macro_or_unresolved_region")
    if clean(cluster.get("packet_relation_lane")) != "strong_packet_candidate":
        dims.append("lane_not_strong")
    if clean(cluster.get("packet_confidence")) != "high":
        dims.append("confidence_not_high")
    if as_int(cluster.get("cluster_size")) > 18:
        dims.append("cluster_too_large")
    if as_int(cluster.get("eligible_rows")) == 0:
        dims.append("no_eligible_rows")
    if as_int(cluster.get("anchor_rows")) == 0:
        dims.append("missing_anchor")
    if as_int(cluster.get("member_or_sub_rows")) == 0:
        dims.append("missing_member_or_sub")
    if clean(cluster.get("scope_status")) == "method_review_only":
        dims.append("method_review_only")
    return dims


def resolution_path(dims: list[str]) -> str:
    if "macro_or_unresolved_region" in dims:
        return "resolve_region_scope_before_packeting"
    if "no_eligible_rows" in dims:
        return "improve_relation_evidence_before_sandbox"
    if "lane_not_strong" in dims or "confidence_not_high" in dims:
        return "tune_family_relation_signal_then_reaudit"
    if "missing_anchor" in dims:
        return "identify_blocker_free_anchor_candidate"
    if "missing_member_or_sub" in dims:
        return "identify_blocker_free_member_or_sub_candidate"
    if "cluster_too_large" in dims:
        return "split_cluster_or_sample_manually"
    return "manual_relation_review"


def seed_priority(cluster: dict[str, str], dims: list[str]) -> int:
    score = 0
    score += as_int(cluster.get("eligible_rows")) * 4
    score += as_int(cluster.get("anchor_rows")) * 3
    score += as_int(cluster.get("member_or_sub_rows")) * 3
    if clean(cluster.get("packet_relation_lane")) == "strong_packet_candidate":
        score += 12
    if clean(cluster.get("packet_confidence")) == "high":
        score += 8
    if "macro_or_unresolved_region" in dims:
        score -= 8
    if "no_eligible_rows" in dims:
        score -= 10
    if "cluster_too_large" in dims:
        score -= 4
    return score


def blocker_rows(clusters: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cluster in clusters:
        dims = cluster_blocking_dimensions(cluster)
        rows.append(
            {
                "cluster_key": clean(cluster.get("cluster_key")),
                "source_family": clean(cluster.get("source_family")),
                "family_class": clean(cluster.get("family_class")),
                "region": clean(cluster.get("region")),
                "theme": clean(cluster.get("theme")),
                "five_year_bucket": clean(cluster.get("five_year_bucket")),
                "cluster_size": clean(cluster.get("cluster_size")),
                "packet_relation_lane": clean(cluster.get("packet_relation_lane")),
                "packet_confidence": clean(cluster.get("packet_confidence")),
                "eligible_rows": clean(cluster.get("eligible_rows")),
                "anchor_rows": clean(cluster.get("anchor_rows")),
                "member_or_sub_rows": clean(cluster.get("member_or_sub_rows")),
                "scope_status": clean(cluster.get("scope_status")),
                "scope_reason": clean(cluster.get("scope_reason")),
                "blocking_dimensions": "; ".join(dims) if dims else "none",
                "manual_resolution_path": resolution_path(dims),
                "seed_priority": seed_priority(cluster, dims),
                "sample_titles": clean(cluster.get("sample_titles")),
            }
        )
    rows.sort(key=lambda row: (-as_int(row.get("seed_priority")), clean(row.get("source_family")), clean(row.get("cluster_key"))))
    return rows


def matrix_rows(scope_rows: list[dict[str, str]], clusters: list[dict[str, str]], roles: list[dict[str, str]]) -> list[dict[str, Any]]:
    clusters_by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    roles_by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    for cluster in clusters:
        clusters_by_family[clean(cluster.get("source_family"))].append(cluster)
    for role in roles:
        roles_by_family[clean(role.get("source_family"))].append(role)

    rows: list[dict[str, Any]] = []
    for scope in scope_rows:
        family = clean(scope.get("source_family"))
        family_class = clean(scope.get("family_class"))
        family_clusters = clusters_by_family.get(family, [])
        family_roles = roles_by_family.get(family, [])
        dims_counter: Counter[str] = Counter()
        reason_counter: Counter[str] = Counter()
        for cluster in family_clusters:
            dims_counter.update(cluster_blocking_dimensions(cluster))
            reason_counter.update([clean(cluster.get("scope_reason"))])
        blocker_counter = Counter()
        for role in family_roles:
            blocker_counter.update(split_blockers(clean(role.get("relation_blockers"))))
        readiness_counter = Counter(clean(role.get("relation_apply_readiness")) for role in family_roles)
        role_counter = Counter(clean(role.get("proposed_relation_role")) for role in family_roles)
        lane_counter = Counter(clean(cluster.get("packet_relation_lane")) for cluster in family_clusters)
        signal, required, blocked, risk = source_signal(family, family_class)
        primary = first_counter(dims_counter)
        if as_int(scope.get("eligible_rows")) > 0 and as_int(scope.get("eligible_cluster_rows")) > 0:
            tuning_status = "tiny_seed_after_manual_resolution"
            next_action = "review blocked eligible clusters, then rerun strict-ready audit on this family only"
        elif lane_counter.get("packet_parentage_review", 0) > 0:
            tuning_status = "define_parentage_signal"
            next_action = "write a source-family parentage signal and test as audit-only scoring"
        elif blocker_counter.get("weak_design_object_signal", 0) or blocker_counter.get("low_cluster_confidence", 0):
            tuning_status = "improve_design_object_and_cluster_confidence"
            next_action = "separate design-object evidence from host/source-register evidence before packeting"
        else:
            tuning_status = "manual_source_family_review"
            next_action = "inspect sample rows before defining any family rule"
        rows.append(
            {
                "source_family": family,
                "family_class": family_class,
                "role_rows": clean(scope.get("role_rows")),
                "cluster_rows": clean(scope.get("cluster_rows")),
                "eligible_rows": clean(scope.get("eligible_rows")),
                "eligible_cluster_rows": clean(scope.get("eligible_cluster_rows")),
                "scope_candidate_but_blocked_clusters": sum(1 for cluster in family_clusters if clean(cluster.get("scope_status")) == "scope_candidate_but_blocked"),
                "packet_parentage_review_clusters": lane_counter.get("packet_parentage_review", 0),
                "strong_high_clusters": sum(1 for cluster in family_clusters if clean(cluster.get("packet_relation_lane")) == "strong_packet_candidate" and clean(cluster.get("packet_confidence")) == "high"),
                "primary_blocker": primary,
                "dominant_scope_reason": first_counter(reason_counter),
                "dominant_relation_blocker": first_counter(blocker_counter) or "none",
                "dominant_role": first_counter(role_counter),
                "dominant_readiness": first_counter(readiness_counter),
                "tuning_status": tuning_status,
                "tuning_signal": signal,
                "required_evidence": required,
                "risk_controls": blocked,
                "next_action": next_action,
            }
        )
    rows.sort(
        key=lambda row: (
            {"tiny_seed_after_manual_resolution": 0, "define_parentage_signal": 1, "improve_design_object_and_cluster_confidence": 2, "manual_source_family_review": 3}.get(clean(row.get("tuning_status")), 9),
            -as_int(row.get("role_rows")),
            clean(row.get("source_family")),
        )
    )
    return rows


def rule_rows(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in matrix:
        priority = "P0" if clean(row.get("tuning_status")) == "tiny_seed_after_manual_resolution" else "P1"
        if as_int(row.get("role_rows")) < 5:
            priority = "P2"
        risk = "high" if "Do not" in clean(row.get("risk_controls")) else "medium"
        rows.append(
            {
                "source_family": clean(row.get("source_family")),
                "family_class": clean(row.get("family_class")),
                "signal_name": clean(row.get("tuning_signal")),
                "signal_scope": "audit_signal_only",
                "required_evidence": clean(row.get("required_evidence")),
                "blocked_actions": clean(row.get("risk_controls")) + " No rights/image-state/source-authority upgrade is permitted.",
                "risk_level": risk,
                "audit_priority": priority,
                "why_this_family": f"{row.get('role_rows')} role rows; primary blocker={row.get('primary_blocker')}; status={row.get('tuning_status')}",
            }
        )
    return rows


def seed_rows(blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [
        row
        for row in blockers
        if clean(row.get("scope_status")) == "scope_candidate_but_blocked"
        or as_int(row.get("eligible_rows")) > 0
    ]
    candidates.sort(key=lambda row: (-as_int(row.get("seed_priority")), stable_hash(row.get("cluster_key"))))
    return candidates[:MAX_SEEDS]


def summary_rows(matrix: list[dict[str, Any]], blockers: list[dict[str, Any]], rules: list[dict[str, Any]], seeds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {"metric": "scope", "value": "non_mutating_source_family_tuning_audit", "notes": "No rebuild, role override, payload write, image download, or rights/image-state change."},
        {"metric": "source_family_rows", "value": len(matrix), "notes": "Source-family tuning matrix rows."},
        {"metric": "cluster_blocker_rows", "value": len(blockers), "notes": "Non-Commons clusters with blocking dimensions."},
        {"metric": "rule_candidate_rows", "value": len(rules), "notes": "Audit-only source-family rule signal candidates."},
        {"metric": "tiny_sandbox_seed_rows", "value": len(seeds), "notes": "Manual seed rows for a future tiny sandbox after tuning."},
        {"metric": "strict_ready_clusters", "value": 0, "notes": "Carried forward from scope v1; this pass does not create ready clusters."},
    ]
    for status, count in Counter(clean(row.get("tuning_status")) for row in matrix).most_common():
        rows.append({"metric": f"tuning_status:{status}", "value": count, "notes": "Source-family tuning status distribution."})
    for blocker, count in Counter(clean(row.get("primary_blocker")) for row in matrix).most_common():
        rows.append({"metric": f"primary_blocker:{blocker}", "value": count, "notes": "Dominant source-family blocking dimension."})
    for path, count in Counter(clean(row.get("manual_resolution_path")) for row in blockers).most_common():
        rows.append({"metric": f"resolution_path:{path}", "value": count, "notes": "Cluster-level manual resolution path distribution."})
    for family_class, count in Counter(clean(row.get("family_class")) for row in matrix).most_common():
        rows.append({"metric": f"family_class:{family_class}", "value": count, "notes": "Source-family class distribution."})
    return rows


def write_report(summary: list[dict[str, Any]], matrix: list[dict[str, Any]], seeds: list[dict[str, Any]]) -> None:
    lines = [
        "# Main/Sub/Text Packet Relation Source-Family Tuning v1",
        "",
        "Scope: non-mutating tuning audit for non-Commons packet relation evidence.",
        "",
        "This pass does not rebuild payloads, apply overrides, download images, or change rights/image states.",
        "",
        "## Summary",
        "",
    ]
    for row in summary[:60]:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(
        [
            "",
            "## Core Finding",
            "",
            "- This pass intentionally creates no strict-ready clusters.",
            "- Non-Commons packeting needs family-specific relation evidence before any broader sandbox.",
            "- The most useful next step is a small manual tuning cycle on blocked eligible clusters, not a full rebuild.",
            "",
            "## Priority Families",
            "",
        ]
    )
    for row in matrix[:14]:
        lines.append(
            f"- {row['source_family']}: status={row['tuning_status']}; rows={row['role_rows']}; "
            f"eligible={row['eligible_rows']}; primary_blocker={row['primary_blocker']}; signal={row['tuning_signal']}; next={row['next_action']}"
        )
    lines.extend(
        [
            "",
            "## Tiny Sandbox Seeds",
            "",
        ]
    )
    for row in seeds[:12]:
        lines.append(
            f"- {row['cluster_key']}: priority={row['seed_priority']}; path={row['manual_resolution_path']}; "
            f"blockers={row['blocking_dimensions']}"
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Rule candidates are audit signals only.",
            "- No candidate may upgrade source authority, authorship, rights state, or IMG01/IMG03 state.",
            "- No source-family signal may override macro/unresolved region review.",
            "- Event/photo/interview/profile/stamp/support records remain card/support candidates unless design-object evidence is explicit.",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    scope = read_csv(IN_SCOPE)
    clusters = read_csv(IN_CLUSTERS)
    roles = read_csv(IN_ROLES)
    # Read the original role queue as a schema guard. The tuning pass currently
    # relies on the reviewed source-family role queue, but this confirms the
    # underlying role source still exists before emitting follow-up queues.
    read_csv(IN_ROLE_QUEUE)

    blockers = blocker_rows(clusters)
    matrix = matrix_rows(scope, clusters, roles)
    rules = rule_rows(matrix)
    seeds = seed_rows(blockers)
    summary = summary_rows(matrix, blockers, rules, seeds)

    write_csv(OUT_BLOCKERS, blockers, BLOCKER_FIELDS)
    write_csv(OUT_MATRIX, matrix, MATRIX_FIELDS)
    write_csv(OUT_RULES, rules, RULE_FIELDS)
    write_csv(OUT_SEEDS, seeds, SEED_FIELDS)
    write_csv(OUT_SUMMARY, summary, SUMMARY_FIELDS)
    write_report(summary, matrix, seeds)

    print(f"source_family_rows={len(matrix)}")
    print(f"cluster_blocker_rows={len(blockers)}")
    print(f"rule_candidate_rows={len(rules)}")
    print(f"tiny_sandbox_seed_rows={len(seeds)}")
    print("strict_ready_clusters=0")
    print(f"wrote {OUT_MATRIX.relative_to(ROOT)}")
    print(f"wrote {OUT_BLOCKERS.relative_to(ROOT)}")
    print(f"wrote {OUT_RULES.relative_to(ROOT)}")
    print(f"wrote {OUT_SEEDS.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
