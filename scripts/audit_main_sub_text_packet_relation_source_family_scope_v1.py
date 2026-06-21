#!/usr/bin/env python3
"""Audit non-Commons source-family scope for packet-relation validation.

This audit checks whether the packet relation method can be generalized beyond
the Commons-heavy sandbox. It is intentionally non-mutating: it writes review
queues and reports only, and it does not rebuild payloads, apply overrides,
download images, or change rights/image states.
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

IN_ROLE_QUEUE = DATA / "prefreeze_main_sub_text_packet_relation_role_queue_v1.csv"
IN_CLUSTER_AUDIT = DATA / "prefreeze_main_sub_text_packet_relation_cluster_audit_v1.csv"

OUT_FAMILY_SCOPE = DATA / "prefreeze_main_sub_text_packet_relation_source_family_scope_v1.csv"
OUT_CLUSTER_REVIEW = DATA / "prefreeze_main_sub_text_packet_relation_source_family_cluster_review_v1.csv"
OUT_ROLE_REVIEW = DATA / "prefreeze_main_sub_text_packet_relation_source_family_role_review_v1.csv"
OUT_VALIDATION_SAMPLE = DATA / "prefreeze_main_sub_text_packet_relation_source_family_validation_sample_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_main_sub_text_packet_relation_source_family_scope_summary_v1.csv"
OUT_REPORT = DOCS / "MAIN_SUB_TEXT_PACKET_RELATION_SOURCE_FAMILY_SCOPE_v1.md"

SAMPLE_TARGET = 260

SUMMARY_FIELDS = ["metric", "value", "notes"]
FAMILY_FIELDS = [
    "source_family",
    "family_class",
    "role_rows",
    "cluster_rows",
    "eligible_rows",
    "support_only_rows",
    "method_review_only_rows",
    "candidate_packet_anchor_rows",
    "member_or_sub_rows",
    "eligible_cluster_rows",
    "strict_sandbox_ready_clusters",
    "dominant_cluster_lane",
    "dominant_role",
    "scope_status",
    "scope_reason",
]
CLUSTER_FIELDS = [
    "cluster_key",
    "source_family",
    "family_class",
    "region",
    "theme",
    "five_year_bucket",
    "cluster_size",
    "packet_relation_lane",
    "packet_confidence",
    "role_rows",
    "eligible_rows",
    "anchor_rows",
    "member_or_sub_rows",
    "support_only_rows",
    "method_review_only_rows",
    "strict_sandbox_ready",
    "scope_status",
    "scope_reason",
    "sample_titles",
]
ROLE_FIELDS = [
    "surface_id",
    "capture_id",
    "year",
    "period_band",
    "region",
    "theme",
    "source_family",
    "family_class",
    "title",
    "cluster_key",
    "cluster_lane",
    "cluster_confidence",
    "proposed_relation_role",
    "relation_apply_readiness",
    "relation_blockers",
    "relation_review_priority",
    "minimum_text_pages",
    "source_family_scope_status",
    "source_family_scope_reason",
    "review_question",
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


def family_class(source_family: str) -> str:
    text = clean(source_family).casefold()
    if "wikimedia commons" in text:
        return "commons"
    if any(
        term in text
        for term in (
            "another graphic",
            "asian film",
            "barjeel",
            "chinese posters",
            "cultural",
            "desain",
            "design",
            "gala",
            "grafis",
            "heritage",
            "indian memory project",
            "letterform",
            "memory project",
            "naidoc",
            "poster gallery",
        )
    ):
        return "design_or_cultural_institution"
    if any(term in text for term in ("museum", "smithsonian", "wellcome", "te papa", "metropolitan", "cleveland", "art institute")):
        return "museum_or_collection_api"
    if any(term in text for term in ("library", "gallica", "bnf", "loc", "princeton", "figgy", "archive", "contentdm", "digitalnz", "internet archive")):
        return "library_archive_or_aggregator"
    return "other_non_commons"


def non_commons(row: dict[str, str]) -> bool:
    return family_class(clean(row.get("source_family"))) != "commons"


def split_cluster_key(key: str) -> tuple[str, str, str, str]:
    parts = clean(key).split("|")
    while len(parts) < 4:
        parts.append("")
    return parts[0], parts[1], parts[2], parts[3]


def is_macro_region(region: str) -> bool:
    folded = clean(region).casefold()
    return "transnational" in folded or folded.startswith("global") or folded.startswith("unresolved")


def eligible(row: dict[str, str]) -> bool:
    return clean(row.get("relation_apply_readiness")) == "eligible_for_next_sandbox_review"


def anchor_role(row: dict[str, str]) -> bool:
    return clean(row.get("proposed_relation_role")) == "candidate_packet_anchor" and clean(row.get("relation_blockers")) == "none"


def member_role(row: dict[str, str]) -> bool:
    return clean(row.get("proposed_relation_role")) in {"packet_member_review", "sub_under_packet_candidate"} and clean(row.get("relation_blockers")) == "none"


def strict_ready(cluster: dict[str, str], rows: list[dict[str, str]]) -> tuple[bool, str]:
    region = clean(cluster.get("region"))
    if is_macro_region(region):
        return False, "macro_or_unresolved_region"
    if clean(cluster.get("packet_relation_lane")) != "strong_packet_candidate":
        return False, "cluster_lane_not_strong_packet_candidate"
    if clean(cluster.get("packet_confidence")) != "high":
        return False, "cluster_confidence_not_high"
    if as_int(cluster.get("cluster_size")) > 18:
        return False, "cluster_too_large_for_cautious_non_commons_preview"
    eligible_rows = [row for row in rows if eligible(row)]
    if not any(anchor_role(row) for row in eligible_rows):
        return False, "missing_blocker_free_anchor"
    if not any(member_role(row) for row in eligible_rows):
        return False, "missing_blocker_free_member_or_sub"
    return True, "strict_non_commons_sandbox_ready"


def cluster_review(role_rows: list[dict[str, str]], cluster_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    role_by_cluster: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in role_rows:
        role_by_cluster[clean(row.get("cluster_key"))].append(row)

    out: list[dict[str, Any]] = []
    for cluster in cluster_rows:
        if not non_commons(cluster):
            continue
        key = clean(cluster.get("cluster_key"))
        rows = role_by_cluster.get(key, [])
        ok, reason = strict_ready(cluster, rows)
        eligible_rows = [row for row in rows if eligible(row)]
        anchors = [row for row in eligible_rows if anchor_role(row)]
        members = [row for row in eligible_rows if member_role(row)]
        if ok:
            status = "strict_sandbox_ready"
        elif eligible_rows:
            status = "scope_candidate_but_blocked"
        else:
            status = "method_review_only"
        out.append(
            {
                "cluster_key": key,
                "source_family": clean(cluster.get("source_family")),
                "family_class": family_class(clean(cluster.get("source_family"))),
                "region": clean(cluster.get("region")),
                "theme": clean(cluster.get("theme")),
                "five_year_bucket": clean(cluster.get("five_year_bucket")),
                "cluster_size": clean(cluster.get("cluster_size")),
                "packet_relation_lane": clean(cluster.get("packet_relation_lane")),
                "packet_confidence": clean(cluster.get("packet_confidence")),
                "role_rows": len(rows),
                "eligible_rows": len(eligible_rows),
                "anchor_rows": len(anchors),
                "member_or_sub_rows": len(members),
                "support_only_rows": sum(1 for row in rows if clean(row.get("relation_apply_readiness")) == "support_only_review"),
                "method_review_only_rows": sum(1 for row in rows if clean(row.get("relation_apply_readiness")) == "method_review_only"),
                "strict_sandbox_ready": "true" if ok else "false",
                "scope_status": status,
                "scope_reason": reason,
                "sample_titles": clean(cluster.get("sample_titles")),
            }
        )
    out.sort(
        key=lambda row: (
            {"strict_sandbox_ready": 0, "scope_candidate_but_blocked": 1, "method_review_only": 2}.get(clean(row.get("scope_status")), 9),
            -as_int(row.get("eligible_rows")),
            clean(row.get("source_family")),
            clean(row.get("cluster_key")),
        )
    )
    return out


def role_review(role_rows: list[dict[str, str]], cluster_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cluster_lookup = {clean(row.get("cluster_key")): row for row in cluster_rows}
    out: list[dict[str, Any]] = []
    for row in role_rows:
        if not non_commons(row):
            continue
        cluster = cluster_lookup.get(clean(row.get("cluster_key")), {})
        status = clean(cluster.get("scope_status")) or "method_review_only"
        reason = clean(cluster.get("scope_reason")) or "no_non_commons_cluster_match"
        out.append(
            {
                "surface_id": clean(row.get("surface_id")),
                "capture_id": clean(row.get("capture_id")),
                "year": clean(row.get("year")),
                "period_band": clean(row.get("period_band")),
                "region": clean(row.get("region")),
                "theme": clean(row.get("theme")),
                "source_family": clean(row.get("source_family")),
                "family_class": family_class(clean(row.get("source_family"))),
                "title": clean(row.get("title")),
                "cluster_key": clean(row.get("cluster_key")),
                "cluster_lane": clean(row.get("cluster_lane")),
                "cluster_confidence": clean(row.get("cluster_confidence")),
                "proposed_relation_role": clean(row.get("proposed_relation_role")),
                "relation_apply_readiness": clean(row.get("relation_apply_readiness")),
                "relation_blockers": clean(row.get("relation_blockers")),
                "relation_review_priority": clean(row.get("relation_review_priority")),
                "minimum_text_pages": clean(row.get("minimum_text_pages")),
                "source_family_scope_status": status,
                "source_family_scope_reason": reason,
                "review_question": clean(row.get("review_question")),
            }
        )
    out.sort(
        key=lambda row: (
            {"strict_sandbox_ready": 0, "scope_candidate_but_blocked": 1, "method_review_only": 2}.get(clean(row.get("source_family_scope_status")), 9),
            -as_int(row.get("relation_review_priority")),
            clean(row.get("source_family")),
            clean(row.get("surface_id")),
        )
    )
    return out


def family_scope(role_rows: list[dict[str, str]], cluster_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    roles_by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    clusters_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in role_rows:
        if non_commons(row):
            roles_by_family[clean(row.get("source_family"))].append(row)
    for row in cluster_rows:
        clusters_by_family[clean(row.get("source_family"))].append(row)

    out: list[dict[str, Any]] = []
    for family, rows in roles_by_family.items():
        clusters = clusters_by_family.get(family, [])
        eligible_rows = [row for row in rows if eligible(row)]
        ready_clusters = [row for row in clusters if clean(row.get("strict_sandbox_ready")) == "true"]
        if ready_clusters:
            status = "ready_for_tiny_non_commons_sandbox"
            reason = "Has at least one strict non-Commons cluster with blocker-free anchor and member/sub rows."
        elif eligible_rows:
            status = "eligible_but_scope_blocked"
            reason = "Has eligible rows but lacks explicit non-macro parent/member cluster shape."
        else:
            status = "needs_more_relation_or_source_depth"
            reason = "Rows remain method-review only or support-only under current packet rules."
        out.append(
            {
                "source_family": family,
                "family_class": family_class(family),
                "role_rows": len(rows),
                "cluster_rows": len(clusters),
                "eligible_rows": len(eligible_rows),
                "support_only_rows": sum(1 for row in rows if clean(row.get("relation_apply_readiness")) == "support_only_review"),
                "method_review_only_rows": sum(1 for row in rows if clean(row.get("relation_apply_readiness")) == "method_review_only"),
                "candidate_packet_anchor_rows": sum(1 for row in rows if clean(row.get("proposed_relation_role")) == "candidate_packet_anchor"),
                "member_or_sub_rows": sum(1 for row in rows if clean(row.get("proposed_relation_role")) in {"packet_member_review", "sub_under_packet_candidate"}),
                "eligible_cluster_rows": sum(1 for row in clusters if as_int(row.get("eligible_rows")) > 0),
                "strict_sandbox_ready_clusters": len(ready_clusters),
                "dominant_cluster_lane": Counter(clean(row.get("packet_relation_lane")) for row in clusters).most_common(1)[0][0] if clusters else "",
                "dominant_role": Counter(clean(row.get("proposed_relation_role")) for row in rows).most_common(1)[0][0] if rows else "",
                "scope_status": status,
                "scope_reason": reason,
            }
        )
    out.sort(
        key=lambda row: (
            {"ready_for_tiny_non_commons_sandbox": 0, "eligible_but_scope_blocked": 1, "needs_more_relation_or_source_depth": 2}.get(clean(row.get("scope_status")), 9),
            -as_int(row.get("role_rows")),
            clean(row.get("source_family")),
        )
    )
    return out


def validation_sample(role_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in role_rows:
        grouped[
            (
                clean(row.get("source_family_scope_status")),
                clean(row.get("family_class")),
                clean(row.get("source_family")),
                clean(row.get("proposed_relation_role")),
            )
        ].append(row)
    for rows in grouped.values():
        rows.sort(key=lambda row: (-as_int(row.get("relation_review_priority")), stable_hash(row.get("surface_id"))))

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    keys = sorted(grouped, key=lambda key: (len(grouped[key]), key))
    while len(selected) < SAMPLE_TARGET and keys:
        advanced = False
        for key in keys:
            rows = grouped[key]
            while rows:
                candidate = rows.pop(0)
                sid = clean(candidate.get("surface_id"))
                if sid not in seen:
                    selected.append(candidate)
                    seen.add(sid)
                    advanced = True
                    break
            if len(selected) >= SAMPLE_TARGET:
                break
        keys = [key for key in keys if grouped[key]]
        if not advanced:
            break
    if len(selected) < SAMPLE_TARGET:
        remaining = [row for row in role_rows if clean(row.get("surface_id")) not in seen]
        remaining.sort(key=lambda row: (-as_int(row.get("relation_review_priority")), stable_hash(row.get("surface_id"))))
        selected.extend(remaining[: SAMPLE_TARGET - len(selected)])
    return selected


def summary_rows(role_rows: list[dict[str, str]], cluster_rows: list[dict[str, Any]], family_rows: list[dict[str, Any]], sample: list[dict[str, Any]]) -> list[dict[str, Any]]:
    non_commons_roles = [row for row in role_rows if non_commons(row)]
    out: list[dict[str, Any]] = [
        {"metric": "scope", "value": "non_mutating_non_commons_source_family_scope", "notes": "No rebuild, no role override, no image download, no rights/image-state change."},
        {"metric": "non_commons_role_rows", "value": len(non_commons_roles), "notes": "Non-Commons rows in packet relation role queue."},
        {"metric": "non_commons_cluster_rows", "value": len(cluster_rows), "notes": "Non-Commons packet relation clusters reviewed."},
        {"metric": "source_family_rows", "value": len(family_rows), "notes": "Non-Commons source families represented."},
        {"metric": "validation_sample_rows", "value": len(sample), "notes": "Stratified sample for source-family scope review."},
        {"metric": "strict_sandbox_ready_clusters", "value": sum(1 for row in cluster_rows if clean(row.get("strict_sandbox_ready")) == "true"), "notes": "Clusters satisfying cautious non-Commons sandbox shape."},
        {"metric": "eligible_non_commons_rows", "value": sum(1 for row in non_commons_roles if eligible(row)), "notes": "Non-Commons rows currently marked eligible for next sandbox review."},
    ]
    for status, count in Counter(clean(row.get("scope_status")) for row in family_rows).most_common():
        out.append({"metric": f"family_scope_status:{status}", "value": count, "notes": "Source-family scope status distribution."})
    for status, count in Counter(clean(row.get("scope_status")) for row in cluster_rows).most_common():
        out.append({"metric": f"cluster_scope_status:{status}", "value": count, "notes": "Non-Commons cluster scope status distribution."})
    for family, count in Counter(clean(row.get("source_family")) for row in non_commons_roles).most_common(30):
        out.append({"metric": f"role_source_family:{family}", "value": count, "notes": "Non-Commons role queue source-family distribution."})
    for klass, count in Counter(family_class(clean(row.get("source_family"))) for row in non_commons_roles).most_common():
        out.append({"metric": f"family_class:{klass}", "value": count, "notes": "Non-Commons role queue source-family class distribution."})
    return out


def write_report(summary: list[dict[str, Any]], family_rows: list[dict[str, Any]], cluster_rows: list[dict[str, Any]]) -> None:
    ready_clusters = [row for row in cluster_rows if clean(row.get("strict_sandbox_ready")) == "true"]
    blocked_clusters = [row for row in cluster_rows if clean(row.get("scope_status")) == "scope_candidate_but_blocked"]
    lines = [
        "# Main/Sub/Text Packet Relation Source-Family Scope v1",
        "",
        "Scope: non-mutating source-family validation for extending packet relation rules beyond Commons-heavy clusters.",
        "",
        "This pass does not rebuild payloads, apply overrides, download images, or change rights/image states.",
        "",
        "## Summary",
        "",
    ]
    for row in summary[:50]:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(
        [
            "",
            "## Core Finding",
            "",
            f"- Strict non-Commons sandbox-ready clusters: {len(ready_clusters)}.",
            f"- Non-Commons clusters with eligible rows but blocked scope: {len(blocked_clusters)}.",
            "- Under the current cautious rules, non-Commons coverage is not yet strong enough to run a representative museum/API/design-institution sandbox.",
            "",
            "## Why This Matters",
            "",
            "- The prior packet sandbox validated a Commons-heavy path only.",
            "- Non-Commons source families have much fewer eligible rows, and many remain `mixed_manual_relation_review`, global/transnational, or anchor-only without member/sub rows.",
            "- A release-bound method should not assume that Commons file-source clusters behave like museum APIs, national libraries, design archives, or cultural institutions.",
            "",
            "## Source Families Needing Attention",
            "",
        ]
    )
    for row in family_rows[:24]:
        lines.append(
            f"- {row['source_family']}: status={row['scope_status']}; role_rows={row['role_rows']}; "
            f"eligible={row['eligible_rows']}; strict_ready_clusters={row['strict_sandbox_ready_clusters']}; reason={row['scope_reason']}"
        )
    lines.extend(
        [
            "",
            "## Next Safe Action",
            "",
            "- Do not run a non-Commons sandbox from this pass unless strict-ready clusters appear after source-family-specific rule tuning.",
            "- First tune relation rules for recurring source families such as Gallica / BnF APIs, DigitalNZ, Te Papa, Wellcome Collection, Library of Congress, NAIDOC Poster Gallery, V&A Collections API, and design archives.",
            "- Add source-family-specific parentage heuristics only as audit signals, not automatic role upgrades.",
            "",
            "## Safety",
            "",
            "- No image files were downloaded.",
            "- No rights, source authority, authorship, or IMG01/IMG03 upgrades were made.",
            "- Source-family scope is an internal method-validation signal only.",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    role_rows = read_csv(IN_ROLE_QUEUE)
    cluster_rows_raw = read_csv(IN_CLUSTER_AUDIT)
    clusters = cluster_review(role_rows, cluster_rows_raw)
    roles = role_review(role_rows, clusters)
    families = family_scope(role_rows, clusters)
    sample = validation_sample(roles)
    summary = summary_rows(role_rows, clusters, families, sample)

    write_csv(OUT_CLUSTER_REVIEW, clusters, CLUSTER_FIELDS)
    write_csv(OUT_ROLE_REVIEW, roles, ROLE_FIELDS)
    write_csv(OUT_FAMILY_SCOPE, families, FAMILY_FIELDS)
    write_csv(OUT_VALIDATION_SAMPLE, sample, ROLE_FIELDS)
    write_csv(OUT_SUMMARY, summary, SUMMARY_FIELDS)
    write_report(summary, families, clusters)

    print(f"non_commons_role_rows={len(roles)}")
    print(f"non_commons_cluster_rows={len(clusters)}")
    print(f"source_family_rows={len(families)}")
    print(f"validation_sample_rows={len(sample)}")
    print(f"strict_sandbox_ready_clusters={sum(1 for row in clusters if clean(row.get('strict_sandbox_ready')) == 'true')}")
    print(f"eligible_non_commons_rows={sum(1 for row in role_rows if non_commons(row) and eligible(row))}")
    print(f"wrote {OUT_FAMILY_SCOPE.relative_to(ROOT)}")
    print(f"wrote {OUT_CLUSTER_REVIEW.relative_to(ROOT)}")
    print(f"wrote {OUT_ROLE_REVIEW.relative_to(ROOT)}")
    print(f"wrote {OUT_VALIDATION_SAMPLE.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
