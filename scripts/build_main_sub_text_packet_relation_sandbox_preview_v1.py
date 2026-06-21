#!/usr/bin/env python3
"""Preview a narrow packet-relation sandbox without release mutation.

This script selects explicit packet clusters from the packet-relation method
queue, keeps the chosen anchor as main, and previews only member/sub rows as
support-packet rows. It does not write generated payload JSON, download images,
or change rights/image states.
"""

from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import audit_prefreeze_candidate_payload_v1 as audit
import build_prefreeze_candidate_payload_v1 as candidate_build


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
BASELINE_PAYLOAD = ROOT / "generated" / "public_surfaces_prefreeze_candidate_v1.json"

IN_ROLE_QUEUE = DATA / "prefreeze_main_sub_text_packet_relation_role_queue_v1.csv"
BASE_OVERRIDES = DATA / "prefreeze_surface_role_overrides_packet_applied_v1.csv"

OUT_CLUSTER_PLAN = DATA / "prefreeze_main_sub_text_packet_relation_sandbox_cluster_plan_v1.csv"
OUT_MEMBER_CANDIDATES = DATA / "prefreeze_main_sub_text_packet_relation_sandbox_member_candidates_v1.csv"
OUT_NEW_OVERRIDES = DATA / "prefreeze_main_sub_text_packet_relation_sandbox_preview_new_overrides_v1.csv"
OUT_MERGED_OVERRIDES = DATA / "prefreeze_main_sub_text_packet_relation_sandbox_preview_overrides_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_main_sub_text_packet_relation_sandbox_preview_summary_v1.csv"
OUT_SURFACE_DELTA = DATA / "prefreeze_main_sub_text_packet_relation_sandbox_preview_surface_delta_v1.csv"
OUT_METRICS = DATA / "prefreeze_main_sub_text_packet_relation_sandbox_preview_metrics_v1.csv"
OUT_REPORT = DOCS / "MAIN_SUB_TEXT_PACKET_RELATION_SANDBOX_PREVIEW_v1.md"

MAX_CLUSTERS = 18
MAX_MEMBERS_PER_CLUSTER = 5
MAX_CLUSTER_SIZE = 18

VISIBLE_STATES = {"IMG01", "IMG02", "IMG03"}
OPEN_STATES = {"IMG03"}

OVERRIDE_FIELDS = [
    "source_file",
    "capture_id",
    "surface_id",
    "surface_disposition_override",
    "review_class",
    "decision_type",
    "confidence",
    "override_basis",
    "source_name",
    "title",
    "override_source",
    "packet_id",
]
CLUSTER_PLAN_FIELDS = [
    "packet_id",
    "cluster_key",
    "cluster_size",
    "cluster_lane",
    "cluster_confidence",
    "region",
    "theme",
    "source_family",
    "five_year_bucket",
    "anchor_surface_id",
    "anchor_capture_id",
    "anchor_title",
    "anchor_score",
    "eligible_members",
    "selected_members",
    "selection_reason",
]
MEMBER_FIELDS = [
    "packet_id",
    "surface_id",
    "capture_id",
    "title",
    "year",
    "region",
    "theme",
    "source_family",
    "cluster_key",
    "proposed_relation_role",
    "preview_disposition",
    "parent_anchor_surface_id",
    "relation_review_priority",
    "minimum_text_pages",
    "relation_blockers",
    "selection_status",
    "selection_reason",
]
SUMMARY_FIELDS = ["metric", "value", "notes"]
DELTA_FIELDS = [
    "surface_id",
    "capture_id",
    "packet_id",
    "parent_anchor_surface_id",
    "proposed_relation_role",
    "before_publication_role",
    "after_publication_role",
    "before_surface_type",
    "after_surface_type",
    "before_template_id",
    "after_template_id",
    "before_image_state",
    "after_image_state",
    "delta_status",
    "title",
    "source_name",
]
METRIC_FIELDS = ["metric", "baseline", "preview", "delta", "notes"]


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
    if not path.exists():
        return []
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


def capture_record_index() -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for path in candidate_build.capture_record_files():
        for row in read_csv(path):
            capture_id = clean(row.get("capture_id"))
            if not capture_id or capture_id in index:
                continue
            enriched = dict(row)
            enriched["_source_file"] = path.name
            index[capture_id] = enriched
    return index


def row_rank(row: dict[str, str]) -> tuple[int, int, int, int, str]:
    return (
        as_int(row.get("relation_review_priority")),
        as_int(row.get("anchor_strength_score")),
        as_int(row.get("source_depth_score")),
        as_int(row.get("design_object_confidence_score")),
        clean(row.get("surface_id")),
    )


def is_cluster_eligible(rows: list[dict[str, str]]) -> bool:
    first = rows[0]
    region = clean(first.get("region"))
    if "transnational" in region.casefold() or region == "Global / transnational":
        return False
    if clean(first.get("cluster_lane")) != "strong_packet_candidate":
        return False
    if clean(first.get("cluster_confidence")) != "high":
        return False
    if as_int(first.get("cluster_size")) > MAX_CLUSTER_SIZE:
        return False
    anchors = [
        row
        for row in rows
        if clean(row.get("relation_apply_readiness")) == "eligible_for_next_sandbox_review"
        and clean(row.get("proposed_relation_role")) == "candidate_packet_anchor"
        and clean(row.get("relation_blockers")) == "none"
    ]
    members = selectable_member_rows(rows)
    return bool(anchors and members)


def selectable_member_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if clean(row.get("relation_apply_readiness")) == "eligible_for_next_sandbox_review"
        and clean(row.get("proposed_relation_role")) in {"sub_under_packet_candidate", "packet_member_review"}
        and clean(row.get("relation_blockers")) == "none"
    ]


def select_clusters(role_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in role_rows:
        grouped[clean(row.get("cluster_key"))].append(row)

    eligible: list[tuple[str, list[dict[str, str]], dict[str, str], list[dict[str, str]]]] = []
    for cluster_key, rows in grouped.items():
        if not is_cluster_eligible(rows):
            continue
        anchors = [
            row
            for row in rows
            if clean(row.get("relation_apply_readiness")) == "eligible_for_next_sandbox_review"
            and clean(row.get("proposed_relation_role")) == "candidate_packet_anchor"
            and clean(row.get("relation_blockers")) == "none"
        ]
        anchor = sorted(anchors, key=row_rank, reverse=True)[0]
        members = sorted(selectable_member_rows(rows), key=row_rank, reverse=True)
        eligible.append((cluster_key, rows, anchor, members))

    # Round-robin by region so one geography does not dominate the small sandbox.
    by_region: dict[str, list[tuple[str, list[dict[str, str]], dict[str, str], list[dict[str, str]]]]] = defaultdict(list)
    for item in eligible:
        by_region[clean(item[2].get("region"))].append(item)
    for values in by_region.values():
        values.sort(key=lambda item: (len(item[3]), row_rank(item[2])), reverse=True)

    selected_items: list[tuple[str, list[dict[str, str]], dict[str, str], list[dict[str, str]]]] = []
    regions = sorted(by_region, key=lambda region: (-len(by_region[region]), region))
    while len(selected_items) < MAX_CLUSTERS and regions:
        advanced = False
        for region in list(regions):
            values = by_region[region]
            if not values:
                continue
            selected_items.append(values.pop(0))
            advanced = True
            if len(selected_items) >= MAX_CLUSTERS:
                break
        regions = [region for region in regions if by_region[region]]
        if not advanced:
            break

    cluster_plan: list[dict[str, Any]] = []
    member_rows: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    for index, (cluster_key, rows, anchor, members) in enumerate(selected_items, start=1):
        region, theme, family, bucket = split_cluster_key(cluster_key)
        packet_id = f"PRSP{index:03d}"
        selected_members = members[:MAX_MEMBERS_PER_CLUSTER]
        cluster_plan.append(
            {
                "packet_id": packet_id,
                "cluster_key": cluster_key,
                "cluster_size": clean(anchor.get("cluster_size")),
                "cluster_lane": clean(anchor.get("cluster_lane")),
                "cluster_confidence": clean(anchor.get("cluster_confidence")),
                "region": region,
                "theme": theme,
                "source_family": family,
                "five_year_bucket": bucket,
                "anchor_surface_id": clean(anchor.get("surface_id")),
                "anchor_capture_id": clean(anchor.get("capture_id")),
                "anchor_title": clean(anchor.get("title")),
                "anchor_score": clean(anchor.get("anchor_strength_score")),
                "eligible_members": len(members),
                "selected_members": len(selected_members),
                "selection_reason": "single top-ranked packet anchor with blocker-free member/sub candidates; non-macro cluster",
            }
        )
        stats["selected_clusters"] += 1
        stats[f"selected_region:{region}"] += 1
        for member in selected_members:
            role = clean(member.get("proposed_relation_role"))
            member_rows.append(
                {
                    "packet_id": packet_id,
                    "surface_id": clean(member.get("surface_id")),
                    "capture_id": clean(member.get("capture_id")),
                    "title": clean(member.get("title")),
                    "year": clean(member.get("year")),
                    "region": clean(member.get("region")),
                    "theme": clean(member.get("theme")),
                    "source_family": clean(member.get("source_family")),
                    "cluster_key": cluster_key,
                    "proposed_relation_role": role,
                    "preview_disposition": "support_packet_appendix_text",
                    "parent_anchor_surface_id": clean(anchor.get("surface_id")),
                    "relation_review_priority": clean(member.get("relation_review_priority")),
                    "minimum_text_pages": clean(member.get("minimum_text_pages")),
                    "relation_blockers": clean(member.get("relation_blockers")),
                    "selection_status": "selected_for_sandbox_preview",
                    "selection_reason": "blocker-free eligible packet member/sub candidate under selected anchor",
                }
            )
            stats[f"selected_role:{role}"] += 1
    stats["eligible_explicit_clusters"] = len(eligible)
    stats["selected_member_rows"] = len(member_rows)
    return cluster_plan, member_rows, stats


def make_overrides(member_rows: list[dict[str, Any]]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], Counter[str]]:
    base_rows = read_csv(BASE_OVERRIDES)
    record_index = capture_record_index()
    existing_keys = {(Path(row.get("source_file", "")).name, clean(row.get("capture_id"))) for row in base_rows}
    new_rows: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    stats: Counter[str] = Counter()

    for row in member_rows:
        stats["member_rows_considered"] += 1
        capture_id = clean(row.get("capture_id"))
        source_record = record_index.get(capture_id)
        if not source_record:
            stats["rejected_missing_capture_record"] += 1
            rejected.append({**{k: clean(v) for k, v in row.items()}, "reject_reason": "missing_capture_record"})
            continue
        source_file = Path(source_record.get("_source_file", "")).name
        key = (source_file, capture_id)
        if key in existing_keys:
            stats["rejected_existing_override_collision"] += 1
            rejected.append({**{k: clean(v) for k, v in row.items()}, "reject_reason": "existing_override_collision", "source_file": source_file})
            continue
        override = {
            "source_file": source_file,
            "capture_id": capture_id,
            "surface_id": clean(row.get("surface_id")) or f"SURF-{capture_id}",
            "surface_disposition_override": "support_packet_appendix_text",
            "review_class": "packet_relation_sandbox_member",
            "decision_type": "sandbox_packet_relation_member_preview",
            "confidence": "medium",
            "override_basis": (
                "packet_relation_sandbox_preview_v1: "
                + clean(row.get("proposed_relation_role"))
                + " under "
                + clean(row.get("parent_anchor_surface_id"))
            ),
            "source_name": clean(source_record.get("source_name")),
            "title": clean(source_record.get("source_title")),
            "override_source": "main_sub_text_packet_relation_sandbox_preview_v1",
            "packet_id": clean(row.get("packet_id")),
        }
        new_rows.append(override)
        existing_keys.add(key)
        stats["new_preview_overrides"] += 1
    merged_rows = base_rows + new_rows
    stats["base_override_rows"] = len(base_rows)
    stats["merged_override_rows"] = len(merged_rows)
    stats["rejected_rows"] = len(rejected)
    return new_rows, merged_rows, rejected, stats


def load_baseline_payload() -> dict[str, Any]:
    return json.loads(BASELINE_PAYLOAD.read_text(encoding="utf-8"))


def build_preview_payload() -> dict[str, Any]:
    previous = os.environ.get("PREFREEZE_ROLE_OVERRIDES_PATH")
    os.environ["PREFREEZE_ROLE_OVERRIDES_PATH"] = str(OUT_MERGED_OVERRIDES)
    try:
        rows, _input_stats, _counters = candidate_build.candidate_rows()
        payload = candidate_build.build_payload(rows)
    finally:
        if previous is None:
            os.environ.pop("PREFREEZE_ROLE_OVERRIDES_PATH", None)
        else:
            os.environ["PREFREEZE_ROLE_OVERRIDES_PATH"] = previous
    return payload


def surface_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {clean(surface.get("surfaceId")): surface for surface in payload.get("surfaces", [])}


def image_state(surface: dict[str, Any] | None) -> str:
    if not surface:
        return ""
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    return clean(image.get("state")) or "IMG00"


def object_metrics(payload: dict[str, Any]) -> dict[str, float | int]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for surface in payload.get("surfaces", []):
        groups[audit.object_key(surface)].append(surface)
    object_total = len(groups)
    object_visible = sum(1 for group in groups.values() if any(image_state(surface) in VISIBLE_STATES for surface in group))
    object_open = sum(1 for group in groups.values() if any(image_state(surface) in OPEN_STATES and audit.rights_reviewed(surface) for surface in group))
    object_weight = sum(max(audit.PUBLICATION_WEIGHTS.get(image_state(surface), 0.0) for surface in group) for group in groups.values())
    object_best_states = Counter(
        max((image_state(surface) for surface in group), key=lambda state: audit.PUBLICATION_WEIGHTS.get(state, 0.0))
        for group in groups.values()
    )
    return {
        "object_count": object_total,
        "object_source_visible_rate": float(audit.pct(object_visible, object_total)),
        "object_verified_open_rate": float(audit.pct(object_open, object_total)),
        "object_weighted_publication_grade_rate": float(audit.pct(object_weight, object_total)),
        "object_img04_rate": float(audit.pct(object_best_states.get("IMG04", 0), object_total)),
    }


def payload_metrics(payload: dict[str, Any]) -> dict[str, float | int]:
    surfaces = payload.get("surfaces", [])
    source_names = {clean(surface.get("sourceName")) for surface in surfaces if clean(surface.get("sourceName"))}
    roles = Counter(clean(surface.get("publicationRole")) or "unknown" for surface in surfaces)
    types = Counter(clean(surface.get("surfaceType")) or "unknown" for surface in surfaces)
    states = Counter(image_state(surface) for surface in surfaces)
    metrics: dict[str, float | int] = {
        "surfaces": len(surfaces),
        "active_public_sources": len(source_names),
        "research_dossiers": len(payload.get("researchDossiers", [])),
        "main_sheet_count": roles.get("main_sheet", 0),
        "support_packet_count": roles.get("support_packet_appendix_text", 0) + roles.get("thin_visual_support_packet", 0),
        "card_count": sum(1 for surface in surfaces if clean(surface.get("publicationRole")) == "card" or clean(surface.get("surfaceType")) == "card"),
        "text_template_count": sum(1 for surface in surfaces if clean(surface.get("templateId")) == "sheet.text.v0"),
        "sheet_surface_count": types.get("sheet", 0),
        "surface_source_visible_rate": float(audit.pct(sum(1 for surface in surfaces if image_state(surface) in VISIBLE_STATES), len(surfaces))),
        "surface_verified_open_rate": float(audit.pct(sum(1 for surface in surfaces if image_state(surface) in OPEN_STATES and audit.rights_reviewed(surface)), len(surfaces))),
    }
    for state, count in states.items():
        metrics[f"surface_image_state_{state}"] = count
    metrics.update(object_metrics(payload))
    return metrics


def metric_rows(baseline_payload: dict[str, Any], preview_payload: dict[str, Any]) -> list[dict[str, str]]:
    baseline = payload_metrics(baseline_payload)
    preview = payload_metrics(preview_payload)
    rows: list[dict[str, str]] = []
    for metric in sorted(set(baseline) | set(preview)):
        before = baseline.get(metric, 0)
        after = preview.get(metric, 0)
        if isinstance(before, float) or isinstance(after, float):
            before_num = float(before)
            after_num = float(after)
            rows.append({"metric": metric, "baseline": f"{before_num:.2f}", "preview": f"{after_num:.2f}", "delta": f"{after_num - before_num:.2f}", "notes": "Packet-relation sandbox preview metric."})
        else:
            before_num = int(before)
            after_num = int(after)
            rows.append({"metric": metric, "baseline": str(before_num), "preview": str(after_num), "delta": str(after_num - before_num), "notes": "Packet-relation sandbox preview metric."})
    return rows


def build_surface_delta(
    baseline_payload: dict[str, Any],
    preview_payload: dict[str, Any],
    new_overrides: list[dict[str, str]],
    member_rows: list[dict[str, Any]],
) -> list[dict[str, str]]:
    baseline = surface_map(baseline_payload)
    preview = surface_map(preview_payload)
    member_lookup = {clean(row.get("surface_id")): row for row in member_rows}
    rows: list[dict[str, str]] = []
    for override in new_overrides:
        surface_id = clean(override.get("surface_id"))
        before = baseline.get(surface_id)
        after = preview.get(surface_id)
        member = member_lookup.get(surface_id, {})
        if not before:
            status = "missing_before"
        elif not after:
            status = "missing_after"
        elif clean(after.get("publicationRole")) == clean(override.get("surface_disposition_override")):
            status = "preview_disposition_applied"
        else:
            status = "preview_not_applied"
        rows.append(
            {
                "surface_id": surface_id,
                "capture_id": clean(override.get("capture_id")),
                "packet_id": clean(override.get("packet_id")),
                "parent_anchor_surface_id": clean(member.get("parent_anchor_surface_id")),
                "proposed_relation_role": clean(member.get("proposed_relation_role")),
                "before_publication_role": clean((before or {}).get("publicationRole")),
                "after_publication_role": clean((after or {}).get("publicationRole")),
                "before_surface_type": clean((before or {}).get("surfaceType")),
                "after_surface_type": clean((after or {}).get("surfaceType")),
                "before_template_id": clean((before or {}).get("templateId")),
                "after_template_id": clean((after or {}).get("templateId")),
                "before_image_state": image_state(before),
                "after_image_state": image_state(after),
                "delta_status": status,
                "title": clean((after or before or {}).get("title")),
                "source_name": clean((after or before or {}).get("sourceName")),
            }
        )
    return rows


def write_report(summary: list[dict[str, Any]], metrics: list[dict[str, str]], delta_rows: list[dict[str, str]]) -> None:
    metric_lookup = {row["metric"]: row for row in metrics}
    status_counts = Counter(row["delta_status"] for row in delta_rows)
    lines = [
        "# Main/Sub/Text Packet Relation Sandbox Preview v1",
        "",
        "Scope: narrow, non-mutating sandbox preview for explicit packet parent/member relations.",
        "",
        "This pass keeps selected anchors as main sheets and previews only blocker-free member/sub candidates as support-packet rows. It does not write generated payload JSON, mutate the official payload, download images, or change rights/image states.",
        "",
        "## Summary",
        "",
    ]
    for row in summary:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Delta Status", ""])
    for status, count in status_counts.most_common():
        lines.append(f"- `{status}`: {count}")
    lines.extend(["", "## Key Metric Deltas", ""])
    for metric, label in [
        ("surfaces", "surfaces"),
        ("active_public_sources", "active public sources"),
        ("main_sheet_count", "main sheets"),
        ("support_packet_count", "support packets"),
        ("card_count", "cards"),
        ("text_template_count", "text templates"),
        ("object_source_visible_rate", "object source-visible rate"),
        ("object_verified_open_rate", "object verified-open rate"),
        ("object_weighted_publication_grade_rate", "object weighted publication-grade rate"),
        ("object_img04_rate", "object IMG04 rate"),
    ]:
        row = metric_lookup.get(metric)
        if row:
            lines.append(f"- {label}: {row['baseline']} -> {row['preview']} (delta {row['delta']})")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This preview tests whether explicit parent/member clusters can move member rows out of main-sheet status without changing source inclusion or rights state.",
            "- Parent anchors are listed in the cluster plan but are not role-overridden by this pass.",
            "- A successful preview means the relation method is technically stable; it does not mean the selected parent choices are final.",
            "- The selected explicit clusters are currently all Wikimedia Commons; this validates a Commons-heavy structure path and must be repeated on museum/API/design-institution sources before generalization.",
            "- Text-page estimates remain planning signals and are not generated here.",
            "",
            "## Safety",
            "",
            "- No image files were downloaded.",
            "- No rights, source authority, authorship, or IMG01/IMG03 upgrades were made.",
            "- The official payload, frontend mirrors, shards, and release build outputs were not modified.",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    role_rows = read_csv(IN_ROLE_QUEUE)
    cluster_plan, member_rows, selection_stats = select_clusters(role_rows)
    new_overrides, merged_overrides, rejected, override_stats = make_overrides(member_rows)

    write_csv(OUT_CLUSTER_PLAN, cluster_plan, CLUSTER_PLAN_FIELDS)
    write_csv(OUT_MEMBER_CANDIDATES, member_rows, MEMBER_FIELDS)
    write_csv(OUT_NEW_OVERRIDES, new_overrides, OVERRIDE_FIELDS)
    write_csv(OUT_MERGED_OVERRIDES, merged_overrides, OVERRIDE_FIELDS)

    baseline_payload = load_baseline_payload()
    preview_payload = build_preview_payload()
    delta_rows = build_surface_delta(baseline_payload, preview_payload, new_overrides, member_rows)
    metric_delta_rows = metric_rows(baseline_payload, preview_payload)

    combined_stats = Counter()
    combined_stats.update(selection_stats)
    combined_stats.update(override_stats)
    combined_stats["preview_applied"] = sum(1 for row in delta_rows if row["delta_status"] == "preview_disposition_applied")
    combined_stats["rejected_examples"] = len(rejected)
    summary_rows = [{"metric": key, "value": value, "notes": "Packet-relation sandbox preview statistic."} for key, value in sorted(combined_stats.items())]
    write_csv(OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_csv(OUT_SURFACE_DELTA, delta_rows, DELTA_FIELDS)
    write_csv(OUT_METRICS, metric_delta_rows, METRIC_FIELDS)
    write_report(summary_rows, metric_delta_rows, delta_rows)

    print(f"selected_clusters={combined_stats['selected_clusters']}")
    print(f"selected_member_rows={combined_stats['selected_member_rows']}")
    print(f"new_preview_overrides={combined_stats['new_preview_overrides']}")
    print(f"preview_applied={combined_stats['preview_applied']}")
    print(f"rejected_rows={combined_stats['rejected_rows']}")
    print(f"wrote {OUT_CLUSTER_PLAN.relative_to(ROOT)}")
    print(f"wrote {OUT_MEMBER_CANDIDATES.relative_to(ROOT)}")
    print(f"wrote {OUT_NEW_OVERRIDES.relative_to(ROOT)}")
    print(f"wrote {OUT_MERGED_OVERRIDES.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_SURFACE_DELTA.relative_to(ROOT)}")
    print(f"wrote {OUT_METRICS.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
