#!/usr/bin/env python3
"""Generate release-quality action queues from non-mutating audits.

This script converts audit outputs into operational queues. It does not rewrite
capture records or surface data. The goal is to keep uncertain records moving
through explicit review states instead of blocking the next capture/clean pass.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

RECENT_QUALITY = DATA / "recent_design_object_quality_audit_2005_2025_v1.csv"
RECLASS_QUEUE = DATA / "recent_stamp_event_reclassification_queue_v1.csv"
TEMPORAL_RECENT = DATA / "temporal_recent_anomaly_review_v1.csv"
TEMPORAL_GAPS = DATA / "temporal_gap_priority_v1.csv"
CONCENTRATION = DATA / "recent_source_concentration_review_v1.csv"
YEAR_SUMMARY = DATA / "recent_design_object_quality_year_summary_2005_2025_v1.csv"

ACTION_PLAN = DATA / "release_quality_action_plan_v1.csv"
CAPTURE_TARGETS = DATA / "release_quality_capture_targets_v1.csv"
EXCLUSIONS = DATA / "release_quality_primary_exclusion_candidates_v1.csv"
REPORT = DOCS / "RELEASE_QUALITY_ACTION_PLAN_v1.md"

ACTION_FIELDS = [
    "action_id",
    "capture_id",
    "capture_file",
    "source_name",
    "source_title",
    "object_year",
    "source_place_text",
    "image_presence_code",
    "source_record_url",
    "action_family",
    "recommended_action",
    "priority",
    "reason",
    "quality_bucket",
    "review_flags",
]

TARGET_FIELDS = [
    "target_rank",
    "target_family",
    "period",
    "priority",
    "desired_records",
    "preferred_source_types",
    "avoid_patterns",
    "rationale",
]

EXCLUSION_FIELDS = [
    "capture_id",
    "capture_file",
    "source_title",
    "object_year",
    "exclusion_scope",
    "reason",
    "retain_as",
    "source_record_url",
]


def clean(value: object) -> str:
    return " ".join(str(value or "").split())


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def action_from_reclass(row: dict[str, str], index: int) -> dict[str, object]:
    bucket = clean(row.get("quality_bucket"))
    if bucket == "card_or_appendix_recent_commemorative_stamp_review":
        family = "post_2010_stamp_or_philatelic_demote"
        action = "exclude_from_primary_object_success; retain_as_card_or_appendix_only_if_research_relevant"
        priority = "P0"
        reason = "Post-2010 stamp/philatelic material can inflate contemporary design-object coverage."
    elif bucket == "card_only_event_or_memory_material":
        family = "event_photo_memory_card_only"
        action = "exclude_from_primary_object_success; retain_as_card_only"
        priority = "P0"
        reason = "Event/photo/memory documentation supports research context but is not a primary design object."
    else:
        family = "recent_object_review"
        action = "manual_review_before_release_count"
        priority = "P1"
        reason = "Recent object-quality row needs release-count review."
    return {
        "action_id": f"RQA{index:06d}",
        "capture_id": clean(row.get("capture_id")),
        "capture_file": clean(row.get("capture_file")),
        "source_name": clean(row.get("source_name")),
        "source_title": clean(row.get("source_title")),
        "object_year": clean(row.get("object_year")),
        "source_place_text": clean(row.get("source_place_text")),
        "image_presence_code": clean(row.get("image_presence_code")),
        "source_record_url": clean(row.get("source_record_url")),
        "action_family": family,
        "recommended_action": action,
        "priority": priority,
        "reason": reason,
        "quality_bucket": bucket,
        "review_flags": clean(row.get("review_flags")),
    }


def action_from_temporal(row: dict[str, str], index: int) -> dict[str, object] | None:
    reason = clean(row.get("review_reason"))
    capture_id = clean(row.get("capture_id"))
    if not capture_id:
        return None
    span_flags = {
        "access_year_as_object_year",
        "coverage_target_span_not_object_year",
        "source_profile_not_item_record",
        "source_page_image_record_not_object_year",
        "hero_or_page_image_not_item_final",
        "long_span_record",
        "recent_end_year_with_old_start",
    }
    reasons = set(part.strip() for part in reason.split(";") if part.strip())
    if reasons & span_flags:
        family = "temporal_span_profile_exclude"
        action = "exclude_from_object_year_metrics_until_item_level_date_is_resolved"
        priority = "P0"
        note = "Span/profile/source-page/access-year row should not count as object-year evidence."
    elif "event_or_session_photo_review" in reasons:
        family = "event_session_card_only"
        action = "exclude_from_primary_object_success; retain_as_card_only"
        priority = "P0"
        note = "Poster-session/event record should support context rather than primary object count."
    elif "recent_2026_object_review" in reasons or "recent_2025_object_review" in reasons:
        family = "recent_research_value_review"
        action = "manual_review_research_value_before_release_count"
        priority = "P1"
        note = "Recent object-dated row needs research-value review."
    else:
        return None
    return {
        "action_id": f"RQT{index:06d}",
        "capture_id": capture_id,
        "capture_file": clean(row.get("capture_file")),
        "source_name": clean(row.get("source_name")),
        "source_title": clean(row.get("source_title")),
        "object_year": clean(row.get("recent_year")),
        "source_place_text": clean(row.get("source_place_text")),
        "image_presence_code": clean(row.get("image_presence_code")),
        "source_record_url": clean(row.get("source_record_url")),
        "action_family": family,
        "recommended_action": action,
        "priority": priority,
        "reason": note,
        "quality_bucket": "",
        "review_flags": reason,
    }


def exclusion_from_action(row: dict[str, object]) -> dict[str, object] | None:
    family = clean(row.get("action_family"))
    if family not in {
        "post_2010_stamp_or_philatelic_demote",
        "event_photo_memory_card_only",
        "temporal_span_profile_exclude",
        "event_session_card_only",
    }:
        return None
    if family == "temporal_span_profile_exclude":
        scope = "object_year_metrics"
        retain = "source_review_or_appendix_after_item_date_resolution"
    elif family == "post_2010_stamp_or_philatelic_demote":
        scope = "primary_object_success"
        retain = "card_or_appendix_if_research_relevant"
    else:
        scope = "primary_object_success"
        retain = "card_only"
    return {
        "capture_id": clean(row.get("capture_id")),
        "capture_file": clean(row.get("capture_file")),
        "source_title": clean(row.get("source_title")),
        "object_year": clean(row.get("object_year")),
        "exclusion_scope": scope,
        "reason": clean(row.get("reason")),
        "retain_as": retain,
        "source_record_url": clean(row.get("source_record_url")),
    }


def dedupe_family(row: dict[str, object]) -> str:
    family = clean(row.get("action_family"))
    if family in {"event_photo_memory_card_only", "event_session_card_only"}:
        return "event_card_only"
    if family == "post_2010_stamp_or_philatelic_demote":
        return "stamp_or_philatelic_demote"
    if family == "temporal_span_profile_exclude":
        return "temporal_span_profile_exclude"
    return family


def capture_targets() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    gaps = read_csv(TEMPORAL_GAPS)
    rank = 1
    for gap in gaps:
        priority = clean(gap.get("priority"))
        if priority not in {"severe_gap", "moderate_gap", "recent_overfull_review"}:
            continue
        start = clean(gap.get("bin_start"))
        end = clean(gap.get("bin_end"))
        period = f"{start}-{end}"
        start_year = int(start) if start.isdigit() else 0
        if start_year >= 2025:
            family = "current_year_guard"
            desired = "do not expand by volume; review object dates, research value, and source type before release counting"
            preferred = "verified studio/project pages only when they are historically meaningful and object-dated"
            avoid = "current-year padding, access-year records, source-profile spans, event photos, post-2010 stamps"
            rationale = "Current/incomplete-year records are not a capture target even when equalized-bin math shows a gap."
        elif priority == "recent_overfull_review":
            family = "recent_quality_review"
            desired = "sample-and-clean existing recent records before more volume"
            preferred = "independent studio/project pages, design platforms, art schools, community archives"
            avoid = "more broad Commons stamps, event photos, poster-session documentation"
            rationale = "Recent totals are high enough; research quality and object status need review."
        else:
            family = "temporal_gap_capture"
            desired = clean(gap.get("recommended_capture_focus"))
            preferred = "museum/design archive catalogs, art-school repositories, local design platforms, periodical archives, studio/project pages"
            avoid = "source-profile spans, access-year-only pages, source-page hero images, post-2010 commemorative stamps"
            rationale = f"Object-dated records are under expected balance: share={clean(gap.get('share_of_expected'))}."
        rows.append(
            {
                "target_rank": rank,
                "target_family": family,
                "period": period,
                "priority": priority,
                "desired_records": desired,
                "preferred_source_types": preferred,
                "avoid_patterns": avoid,
                "rationale": rationale,
            }
        )
        rank += 1

    rows.append(
        {
            "target_rank": rank,
            "target_family": "contemporary_studio_depth",
            "period": "2015-2019",
            "priority": "high_value_supplement",
            "desired_records": "independent studio projects, design-platform projects, art-school/community visual communication records with explicit object years",
            "preferred_source_types": "studio case-study pages, design awards with source-visible project pages, school repositories, community archives",
            "avoid_patterns": "single-site repeated captures, event photos, purely commemorative material",
            "rationale": "2015-2019 primary share is usable, but high-confidence studio depth remains thin.",
        }
    )
    return rows


def write_report(actions: list[dict[str, object]], exclusions: list[dict[str, object]], targets: list[dict[str, object]]) -> None:
    action_counts = Counter(clean(row.get("action_family")) for row in actions)
    priority_counts = Counter(clean(row.get("priority")) for row in actions)
    years = read_csv(YEAR_SUMMARY)
    concentration = read_csv(CONCENTRATION)
    lines = [
        "# Release Quality Action Plan v1",
        "",
        "Scope: generated from temporal and recent object-quality audits. This plan is non-mutating and does not rewrite capture records.",
        "",
        "## Action Summary",
        "",
        f"- Action rows: {len(actions)}",
        f"- Primary/object-year exclusion candidates: {len(exclusions)}",
        f"- Capture target rows: {len(targets)}",
    ]
    for key, value in action_counts.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Priority Counts", ""])
    for key, value in priority_counts.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Quality-Adjusted Recent Years", ""])
    for row in years:
        lines.append(
            f"- {row['year']}: primary={row['primary_design_candidates']}/{row['total_records']}, "
            f"stamp/event share={row['stamp_event_share']}"
        )
    lines.extend(["", "## Concentration Caps", ""])
    for row in concentration:
        lines.append(f"- {row['concentration_type']} `{row['key']}`: {row['record_count']} records")
    lines.extend(
        [
            "",
            "## Next Execution Rule",
            "",
            "- Treat P0 demotion/exclusion rows as release-count guards, not as deletion instructions.",
            "- Keep stamp/event rows available as card or appendix material when they add editorial value.",
            "- Do not expand broad Commons harvests for 2010-2025 until the stamp/event queue is sampled or demoted.",
            "- For next capture, prioritize severe temporal gaps and contemporary studio/project authority sources.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    actions: list[dict[str, object]] = []
    for row in read_csv(RECLASS_QUEUE):
        actions.append(action_from_reclass(row, len(actions) + 1))
    for row in read_csv(TEMPORAL_RECENT):
        action = action_from_temporal(row, len(actions) + 1)
        if action is not None:
            actions.append(action)

    # Deduplicate on capture/action family so rows appearing in both audits do
    # not double-count the same demotion guard.
    deduped: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for row in actions:
        key = (clean(row.get("capture_id")), dedupe_family(row))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    exclusions_raw = [item for row in deduped if (item := exclusion_from_action(row)) is not None]
    exclusions: list[dict[str, object]] = []
    exclusion_seen: set[tuple[str, str]] = set()
    for row in exclusions_raw:
        key = (clean(row.get("capture_id")), clean(row.get("exclusion_scope")))
        if key in exclusion_seen:
            continue
        exclusion_seen.add(key)
        exclusions.append(row)
    targets = capture_targets()

    write_csv(ACTION_PLAN, deduped, ACTION_FIELDS)
    write_csv(EXCLUSIONS, exclusions, EXCLUSION_FIELDS)
    write_csv(CAPTURE_TARGETS, targets, TARGET_FIELDS)
    write_report(deduped, exclusions, targets)

    print(f"action_rows={len(deduped)}")
    print(f"exclusion_candidates={len(exclusions)}")
    print(f"capture_targets={len(targets)}")
    print(f"action_families={dict(Counter(clean(row.get('action_family')) for row in deduped))}")
    print(f"wrote {ACTION_PLAN.relative_to(ROOT)}")
    print(f"wrote {EXCLUSIONS.relative_to(ROOT)}")
    print(f"wrote {CAPTURE_TARGETS.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
