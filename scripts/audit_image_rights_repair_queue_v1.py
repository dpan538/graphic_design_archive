#!/usr/bin/env python3
"""Build an object-level rights/image repair queue for release-gate work.

This audit is deliberately advisory. It does not upgrade IMG01/IMG03 states and
does not infer open rights from platform, TOS, source family, heuristics, or LLM
signals. Each row states what evidence would be needed before a later repair
pass can change image state.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from lib.archive_audit import (
    DATA,
    DOCS,
    ROOT,
    PUBLICATION_WEIGHTS,
    clean,
    object_groups,
    pct,
    read_payload,
    surface_image_state,
    surface_is_source_visible,
    surface_is_verified_open,
    surface_period_band,
    surface_region,
    write_csv,
)


SUMMARY = DATA / "image_rights_repair_summary_v1.csv"
SOURCE_PRIORITIES = DATA / "image_rights_repair_source_priorities_v1.csv"
CANDIDATES = DATA / "image_rights_repair_candidates_v1.csv"
REPORT = DOCS / "IMAGE_RIGHTS_REPAIR_QUEUE_v1.md"

SUMMARY_FIELDS = ["metric", "value", "notes"]
SOURCE_FIELDS = [
    "rank",
    "source_name",
    "candidate_objects",
    "weighted_gap_points",
    "source_visible_gap_objects",
    "verified_open_gap_objects",
    "img03_unreviewed_objects",
    "img02_objects",
    "img01_objects",
    "img00_objects",
    "img04_objects",
    "top_required_action",
    "example_surface_ids",
]
CANDIDATE_FIELDS = [
    "rank",
    "object_key",
    "surface_id",
    "source_name",
    "title",
    "region_group",
    "period_band",
    "best_image_state",
    "rights_reviewed",
    "source_visible_gap",
    "verified_open_gap",
    "weighted_gap_points",
    "repair_family",
    "required_evidence",
    "automatic_upgrade_allowed",
    "source_url",
    "rights_label",
    "image_license_label",
]


def best_surface(group: list[dict[str, Any]]) -> dict[str, Any]:
    return max(group, key=lambda surface: PUBLICATION_WEIGHTS.get(surface_image_state(surface), 0.0))


def rights_label(surface: dict[str, Any]) -> str:
    rights = surface.get("rights") if isinstance(surface.get("rights"), dict) else {}
    return clean(rights.get("label") or rights.get("state"))


def image_license_label(surface: dict[str, Any]) -> str:
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    return clean(image.get("licenseLabel"))


def reviewed(surface: dict[str, Any]) -> bool:
    gates = surface.get("reviewGates") if isinstance(surface.get("reviewGates"), dict) else {}
    return gates.get("rightsReviewed") is True


def repair_family(state: str, source_visible_gap: bool, verified_open_gap: bool, surface: dict[str, Any]) -> tuple[str, str]:
    if state == "IMG03" and verified_open_gap:
        return (
            "img03_rights_review_flag_check",
            "Confirm item-level open/public-domain evidence and set rightsReviewed only if the source record supports it.",
        )
    if state == "IMG02":
        return (
            "img02_open_rights_review",
            "Find item-level open-license or public-domain evidence from the source record before any IMG03 upgrade.",
        )
    if state == "IMG01":
        return (
            "img01_item_image_and_rights_review",
            "Capture item-level image and rights evidence; thumbnails alone cannot support IMG03.",
        )
    if state == "IMG00":
        return (
            "img00_source_visible_repair",
            "Find a source-visible item image or keep as a blocker; image identifier alone is not enough.",
        )
    if state == "IMG04":
        image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
        if image.get("expectation") == "not_expected":
            return (
                "img04_text_state_review",
                "Confirm this is genuinely text/authority/context-only; otherwise capture a visual source record.",
            )
        return (
            "img04_visual_record_search",
            "Search for a source-visible visual record or keep IMG04 only with explicit no-image rationale.",
        )
    if source_visible_gap:
        return (
            "source_visible_repair",
            "Find source-visible image evidence or retain the object as non-image evidence.",
        )
    return (
        "rights_review",
        "Review item-level rights evidence before changing image state.",
    )


def priority_score(row: dict[str, Any]) -> float:
    score = float(row["weighted_gap_points"]) * 100
    if row["source_visible_gap"]:
        score += 20
    if row["verified_open_gap"]:
        score += 12
    state_bonus = {"IMG00": 8, "IMG04": 6, "IMG01": 5, "IMG02": 3, "IMG03": 2}
    score += state_bonus.get(row["best_image_state"], 0)
    return score


def candidate_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for object_key, group in object_groups(payload.get("surfaces", [])).items():
        surface = best_surface(group)
        state = surface_image_state(surface)
        source_visible_gap = not any(surface_is_source_visible(item) for item in group)
        verified_open_gap = not any(surface_is_verified_open(item) for item in group)
        weighted_gap = round(1.0 - max(PUBLICATION_WEIGHTS.get(surface_image_state(item), 0.0) for item in group), 2)
        if not source_visible_gap and not verified_open_gap and weighted_gap <= 0:
            continue
        family, evidence = repair_family(state, source_visible_gap, verified_open_gap, surface)
        row = {
            "object_key": object_key,
            "surface_id": clean(surface.get("surfaceId")),
            "source_name": clean(surface.get("sourceName")) or "Unknown source",
            "title": clean(surface.get("title")),
            "region_group": surface_region(surface),
            "period_band": surface_period_band(surface),
            "best_image_state": state,
            "rights_reviewed": reviewed(surface),
            "source_visible_gap": source_visible_gap,
            "verified_open_gap": verified_open_gap,
            "weighted_gap_points": weighted_gap,
            "repair_family": family,
            "required_evidence": evidence,
            "automatic_upgrade_allowed": False,
            "source_url": clean(surface.get("sourceUrl")),
            "rights_label": rights_label(surface),
            "image_license_label": image_license_label(surface),
        }
        row["_priority"] = priority_score(row)
        rows.append(row)
    rows.sort(key=lambda row: (-float(row["_priority"]), row["source_name"], row["surface_id"]))
    for index, row in enumerate(rows, 1):
        row["rank"] = str(index)
        row["weighted_gap_points"] = f"{float(row['weighted_gap_points']):.2f}"
        row["rights_reviewed"] = str(row["rights_reviewed"]).lower()
        row["source_visible_gap"] = str(row["source_visible_gap"]).lower()
        row["verified_open_gap"] = str(row["verified_open_gap"]).lower()
        row["automatic_upgrade_allowed"] = "false"
        row.pop("_priority", None)
    return rows


def source_priority_rows(candidates: list[dict[str, Any]]) -> list[dict[str, str]]:
    stats: dict[str, Counter[str]] = defaultdict(Counter)
    examples: dict[str, list[str]] = defaultdict(list)
    actions: dict[str, Counter[str]] = defaultdict(Counter)
    for row in candidates:
        source = row["source_name"]
        stats[source]["candidate_objects"] += 1
        stats[source]["weighted_gap_points_x100"] += int(round(float(row["weighted_gap_points"]) * 100))
        if row["source_visible_gap"] == "true":
            stats[source]["source_visible_gap_objects"] += 1
        if row["verified_open_gap"] == "true":
            stats[source]["verified_open_gap_objects"] += 1
        state = row["best_image_state"].lower()
        stats[source][f"{state}_objects"] += 1
        actions[source][row["repair_family"]] += 1
        if len(examples[source]) < 6:
            examples[source].append(row["surface_id"])

    rows: list[dict[str, str]] = []
    for source, counter in stats.items():
        top_action = actions[source].most_common(1)[0][0] if actions[source] else ""
        rows.append(
            {
                "rank": "0",
                "source_name": source,
                "candidate_objects": str(counter["candidate_objects"]),
                "weighted_gap_points": f"{counter['weighted_gap_points_x100'] / 100:.2f}",
                "source_visible_gap_objects": str(counter["source_visible_gap_objects"]),
                "verified_open_gap_objects": str(counter["verified_open_gap_objects"]),
                "img03_unreviewed_objects": str(counter["img03_objects"]),
                "img02_objects": str(counter["img02_objects"]),
                "img01_objects": str(counter["img01_objects"]),
                "img00_objects": str(counter["img00_objects"]),
                "img04_objects": str(counter["img04_objects"]),
                "top_required_action": top_action,
                "example_surface_ids": ";".join(examples[source]),
            }
        )
    rows.sort(
        key=lambda row: (
            -float(row["weighted_gap_points"]),
            -int(row["candidate_objects"]),
            row["source_name"],
        )
    )
    for index, row in enumerate(rows, 1):
        row["rank"] = str(index)
    return rows


def summary_rows(payload: dict[str, Any], candidates: list[dict[str, Any]], sources: list[dict[str, str]]) -> list[dict[str, str]]:
    surfaces = payload.get("surfaces", [])
    groups = object_groups(surfaces)
    object_total = len(groups)
    verified_open = sum(1 for group in groups.values() if any(surface_is_verified_open(surface) for surface in group))
    source_visible = sum(1 for group in groups.values() if any(surface_is_source_visible(surface) for surface in group))
    weighted = sum(
        max((PUBLICATION_WEIGHTS.get(surface_image_state(surface), 0.0) for surface in group), default=0.0)
        for group in groups.values()
    )
    state_counts = Counter(row["best_image_state"] for row in candidates)
    return [
        {"metric": "object_total", "value": str(object_total), "notes": "Object-level groups; repeated views/photos count once."},
        {"metric": "object_source_visible_rate", "value": pct(source_visible, object_total), "notes": "Objects with IMG01/IMG02/IMG03 evidence."},
        {"metric": "object_verified_open_rate", "value": pct(verified_open, object_total), "notes": "Objects with reviewed IMG03 evidence."},
        {"metric": "object_weighted_publication_rate", "value": pct(weighted, object_total), "notes": "Object-level max image weight per object."},
        {"metric": "object_weighted_gap_to_95_points", "value": f"{max(0.0, 0.95 * object_total - weighted):.2f}", "notes": "Weighted points needed for the 95% publication-grade gate."},
        {"metric": "repair_candidate_objects", "value": str(len(candidates)), "notes": "Objects with source-visible, verified-open, or weighted-publication gaps."},
        {"metric": "source_priority_count", "value": str(len(sources)), "notes": "Source families represented in the repair queue."},
        {"metric": "candidate_img02_objects", "value": str(state_counts.get("IMG02", 0)), "notes": "Source-hosted visible objects needing open-rights review."},
        {"metric": "candidate_img01_objects", "value": str(state_counts.get("IMG01", 0)), "notes": "Thumbnail-only objects needing item-level image/rights review."},
        {"metric": "candidate_img00_objects", "value": str(state_counts.get("IMG00", 0)), "notes": "Expected-image blockers needing source-visible repair."},
        {"metric": "candidate_img04_objects", "value": str(state_counts.get("IMG04", 0)), "notes": "Text/no-image objects needing text-state confirmation or visual record search."},
    ]


def write_report(summary: list[dict[str, str]], sources: list[dict[str, str]], candidates: list[dict[str, Any]]) -> None:
    lines = [
        "# Image Rights Repair Queue v1",
        "",
        "Scope: object-level advisory queue for source-visible, verified-open, and weighted-publication repair. This report does not upgrade image states.",
        "",
        "## Safety Contract",
        "",
        "- IMG01 and IMG03 are not automatically upgraded by this audit.",
        "- Heuristics, LLM output, TOS/platform reputation, or source-family assumptions are not treated as rights evidence.",
        "- Each candidate requires item-level source evidence before any future state change.",
        "- Object-level grouping collapses repeated photos/views so one object contributes one repair unit.",
        "",
        "## Summary",
        "",
    ]
    for row in summary:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Top Source Priorities", ""])
    for row in sources[:20]:
        lines.append(
            f"- {row['source_name']}: gap={row['weighted_gap_points']}, candidates={row['candidate_objects']}, "
            f"IMG02={row['img02_objects']}, IMG01={row['img01_objects']}, IMG00={row['img00_objects']}, "
            f"IMG04={row['img04_objects']}, action={row['top_required_action']}"
        )
    lines.extend(["", "## Top Object Candidates", ""])
    for row in candidates[:25]:
        lines.append(
            f"- {row['surface_id']} · {row['best_image_state']} · gap={row['weighted_gap_points']} · "
            f"{row['source_name']} · {row['repair_family']} · {row['title'][:110]}"
        )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = read_payload()
    candidates = candidate_rows(payload)
    source_rows = source_priority_rows(candidates)
    summary = summary_rows(payload, candidates, source_rows)
    write_csv(SUMMARY, summary, SUMMARY_FIELDS)
    write_csv(SOURCE_PRIORITIES, source_rows, SOURCE_FIELDS)
    write_csv(CANDIDATES, candidates, CANDIDATE_FIELDS)
    write_report(summary, source_rows, candidates)
    print(f"repair_candidate_objects={len(candidates)}")
    print(f"source_priority_count={len(source_rows)}")
    print(f"top_source={source_rows[0]['source_name'] if source_rows else ''}")
    print(f"weighted_gap_top_source={source_rows[0]['weighted_gap_points'] if source_rows else '0.00'}")
    print(f"wrote {SUMMARY.relative_to(ROOT)}")
    print(f"wrote {SOURCE_PRIORITIES.relative_to(ROOT)}")
    print(f"wrote {CANDIDATES.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
