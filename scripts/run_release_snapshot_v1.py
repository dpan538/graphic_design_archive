#!/usr/bin/env python3
"""Write a compact release-health snapshot for the archive pipeline.

This script is intentionally read-only over source/capture data: it does not
rebuild surfaces and does not fetch network resources. Run it after any rebuild
or sandbox payload update to get the current gate posture in one place.
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
    read_csv,
    read_payload,
    state_counter_from_surfaces,
    surface_image_state,
    surface_is_source_visible,
    surface_is_verified_open,
    surface_period_band,
    surface_region,
    surface_weight,
    surface_year,
    write_csv,
)


SUMMARY = DATA / "release_snapshot_v1.csv"
PERIOD = DATA / "release_snapshot_period_main_sheets_v1.csv"
REGION = DATA / "release_snapshot_region_v1.csv"
REPORT = DOCS / "RELEASE_SNAPSHOT_v1.md"

RELEASE_SOURCE_TARGET = 20000
MIN_RELEASE_SOURCE_COVERAGE = 80
MIN_OBJECT_SOURCE_VISIBLE = 99
MIN_OBJECT_VERIFIED_OPEN = 95
MIN_OBJECT_WEIGHTED_PUBLICATION = 95
MAX_OBJECT_IMG04 = 10
YEAR_2026_WARNING_RATE = 25
MIN_STRICT_DISTRIBUTION_SOURCE_COVERAGE = 80
MIN_RESEARCH_QUALITY_ADJUSTED_SOURCE_COVERAGE = 80

SUMMARY_FIELDS = ["metric", "value", "gate", "notes"]
PERIOD_FIELDS = ["period_band", "main_sheet_count", "surface_count", "source_visible_surface_count", "img04_surface_count"]
REGION_FIELDS = ["region_group", "surface_count", "main_sheet_count", "source_visible_surface_count", "verified_open_surface_count", "img04_surface_count"]


def metric_value(rows: list[dict[str, str]], metric: str) -> str:
    return next((row.get("value", "") for row in rows if row.get("metric") == metric), "")


def existing_source_coverage_metrics() -> dict[str, str]:
    rows = read_csv(DATA / "source_coverage_rate_v2.csv")
    if not rows:
        rows = read_csv(DATA / "source_coverage_rate_v1.csv")
    return {row.get("metric", ""): row.get("value", "") for row in rows}


def gate(ok: bool) -> str:
    return "pass" if ok else "fail"


def object_metrics(surfaces: list[dict[str, Any]]) -> dict[str, float]:
    groups = object_groups(surfaces)
    object_total = len(groups)
    visible = sum(1 for group in groups.values() if any(surface_is_source_visible(surface) for surface in group))
    verified_open = sum(1 for group in groups.values() if any(surface_is_verified_open(surface) for surface in group))
    weighted = sum(max((surface_weight(surface) for surface in group), default=0.0) for group in groups.values())
    object_state_counts = Counter(
        max(
            (surface_image_state(surface) for surface in group),
            key=lambda state: PUBLICATION_WEIGHTS.get(state, 0.0),
        )
        for group in groups.values()
    )
    return {
        "object_total": object_total,
        "object_source_visible_count": visible,
        "object_source_visible_rate": float(pct(visible, object_total)),
        "object_verified_open_count": verified_open,
        "object_verified_open_rate": float(pct(verified_open, object_total)),
        "object_weighted_publication_score": round(weighted, 2),
        "object_weighted_publication_rate": float(pct(weighted, object_total)),
        "object_img04_count": object_state_counts.get("IMG04", 0),
        "object_img04_rate": float(pct(object_state_counts.get("IMG04", 0), object_total)),
    }


def active_public_source_count(surfaces: list[dict[str, Any]]) -> int:
    return len({clean(surface.get("sourceName")) for surface in surfaces if clean(surface.get("sourceName"))})


def build_rows() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    payload = read_payload()
    surfaces = payload.get("surfaces", [])
    dossiers = payload.get("researchDossiers", [])
    source_coverage = existing_source_coverage_metrics()
    states = state_counter_from_surfaces(surfaces)
    objects = object_metrics(surfaces)
    total = len(surfaces)
    active_sources = active_public_source_count(surfaces)
    release_source_coverage = float(pct(active_sources, RELEASE_SOURCE_TARGET))
    source_visible_surfaces = sum(1 for surface in surfaces if surface_is_source_visible(surface))
    verified_open_surfaces = sum(1 for surface in surfaces if surface_is_verified_open(surface))
    main_sheets = [surface for surface in surfaces if clean(surface.get("publicationRole")) == "main_sheet"]
    support_surfaces = [surface for surface in surfaces if clean(surface.get("publicationRole")) != "main_sheet"]
    independent_text_surfaces = [surface for surface in surfaces if clean(surface.get("templateId")) == "sheet.text.v0"]
    dossier_text_pages = sum(
        1
        for dossier in dossiers
        for page in dossier.get("pageSequence", [])
        if isinstance(page, dict) and page.get("pageType") == "text_page"
    )
    dossier_sub_pages = sum(
        1
        for dossier in dossiers
        for page in dossier.get("pageSequence", [])
        if isinstance(page, dict) and page.get("pageType") in {"sub_sheet", "card", "appendix"}
    )
    year_counts = Counter(surface_year(surface) for surface in surfaces)
    year_2026_count = year_counts.get(2026, 0)
    year_2026_rate = float(pct(year_2026_count, total))
    future_count = sum(1 for surface in surfaces if (surface_year(surface) or 0) > 2026)
    undated_count = sum(1 for surface in surfaces if surface_year(surface) is None)

    summary_rows = [
        {"metric": "public_surfaces", "value": str(total), "gate": "", "notes": "Generated public surfaces."},
        {"metric": "archive_active_public_sources", "value": str(active_sources), "gate": gate(release_source_coverage >= MIN_RELEASE_SOURCE_COVERAGE), "notes": f"Distinct public-surface source names; release target={RELEASE_SOURCE_TARGET}."},
        {"metric": "release_source_coverage_rate", "value": f"{release_source_coverage:.2f}", "gate": gate(release_source_coverage >= MIN_RELEASE_SOURCE_COVERAGE), "notes": f"Minimum release source coverage={MIN_RELEASE_SOURCE_COVERAGE}%."},
        {"metric": "surface_source_visible_rate", "value": pct(source_visible_surfaces, total), "gate": "", "notes": "Surface-level IMG01/IMG02/IMG03."},
        {"metric": "surface_verified_open_rate", "value": pct(verified_open_surfaces, total), "gate": "", "notes": "Surface-level reviewed IMG03."},
        {"metric": "object_count", "value": str(int(objects["object_total"])), "gate": "", "notes": "Object-level grouping; repeated views/photos count once."},
        {"metric": "object_source_visible_rate", "value": f"{objects['object_source_visible_rate']:.2f}", "gate": gate(objects["object_source_visible_rate"] >= MIN_OBJECT_SOURCE_VISIBLE), "notes": f"Minimum object source-visible={MIN_OBJECT_SOURCE_VISIBLE}%."},
        {"metric": "object_verified_open_rate", "value": f"{objects['object_verified_open_rate']:.2f}", "gate": gate(objects["object_verified_open_rate"] >= MIN_OBJECT_VERIFIED_OPEN), "notes": f"Minimum object verified-open={MIN_OBJECT_VERIFIED_OPEN}%."},
        {"metric": "object_weighted_publication_grade_rate", "value": f"{objects['object_weighted_publication_rate']:.2f}", "gate": gate(objects["object_weighted_publication_rate"] >= MIN_OBJECT_WEIGHTED_PUBLICATION), "notes": "Object-level max image weight per object; repeated photos are not double-counted."},
        {"metric": "object_img04_rate", "value": f"{objects['object_img04_rate']:.2f}", "gate": gate(objects["object_img04_rate"] <= MAX_OBJECT_IMG04), "notes": f"Maximum object IMG04 target={MAX_OBJECT_IMG04}%."},
        {"metric": "main_sheet_count", "value": str(len(main_sheets)), "gate": "", "notes": "publicationRole=main_sheet."},
        {"metric": "sub_or_support_surface_count", "value": str(len(support_surfaces)), "gate": "", "notes": "All surfaces not marked as main_sheet."},
        {"metric": "independent_text_sheet_count", "value": str(len(independent_text_surfaces)), "gate": "", "notes": "templateId=sheet.text.v0."},
        {"metric": "dossier_text_page_count", "value": str(dossier_text_pages), "gate": "", "notes": "text_page entries inside researchDossiers pageSequence."},
        {"metric": "dossier_sub_card_appendix_count", "value": str(dossier_sub_pages), "gate": "", "notes": "sub_sheet/card/appendix entries inside researchDossiers pageSequence."},
        {"metric": "year_2026_surface_rate", "value": f"{year_2026_rate:.2f}", "gate": gate(year_2026_rate <= YEAR_2026_WARNING_RATE), "notes": f"Warning if more than {YEAR_2026_WARNING_RATE}% of public surfaces date to 2026."},
        {"metric": "post_2026_or_error_count", "value": str(future_count), "gate": gate(future_count == 0), "notes": "Future year date sanity check."},
        {"metric": "undated_or_unparsed_count", "value": str(undated_count), "gate": "", "notes": "Missing/unparsed public surface dates."},
    ]
    for metric in (
        "source_pool_period_fill_rate",
        "strict_distribution_adjusted_source_coverage_rate",
        "period_surface_balance_rate",
        "region_surface_balance_rate",
        "research_quality_adjusted_source_coverage_rate_v2",
    ):
        value = source_coverage.get(metric)
        if value:
            metric_gate = ""
            notes = "Imported from source coverage audit."
            if metric == "source_pool_period_fill_rate":
                metric_gate = gate(float(value) >= MIN_RELEASE_SOURCE_COVERAGE)
                notes = f"Imported from source coverage audit; minimum release capacity fill={MIN_RELEASE_SOURCE_COVERAGE}%."
            elif metric == "strict_distribution_adjusted_source_coverage_rate":
                metric_gate = gate(float(value) >= MIN_STRICT_DISTRIBUTION_SOURCE_COVERAGE)
                notes = f"Imported from source coverage audit; minimum strict distribution coverage={MIN_STRICT_DISTRIBUTION_SOURCE_COVERAGE}%."
            elif metric == "research_quality_adjusted_source_coverage_rate_v2":
                metric_gate = gate(float(value) >= MIN_RESEARCH_QUALITY_ADJUSTED_SOURCE_COVERAGE)
                notes = f"Imported from source coverage audit; minimum research-quality adjusted coverage={MIN_RESEARCH_QUALITY_ADJUSTED_SOURCE_COVERAGE}%."
            summary_rows.append({"metric": metric, "value": value, "gate": metric_gate, "notes": notes})
    for state, count in sorted(states.items()):
        summary_rows.append({"metric": f"surface_image_state:{state}", "value": str(count), "gate": "", "notes": "Surface image state distribution."})

    period_stats: dict[str, Counter[str]] = defaultdict(Counter)
    region_stats: dict[str, Counter[str]] = defaultdict(Counter)
    for surface in surfaces:
        period = surface_period_band(surface)
        region = surface_region(surface)
        for stats in (period_stats[period], region_stats[region]):
            stats["surface_count"] += 1
            if clean(surface.get("publicationRole")) == "main_sheet":
                stats["main_sheet_count"] += 1
            if surface_is_source_visible(surface):
                stats["source_visible_surface_count"] += 1
            if surface_is_verified_open(surface):
                stats["verified_open_surface_count"] += 1
            if surface_image_state(surface) == "IMG04":
                stats["img04_surface_count"] += 1

    period_rows = [
        {
            "period_band": period,
            "main_sheet_count": str(stats["main_sheet_count"]),
            "surface_count": str(stats["surface_count"]),
            "source_visible_surface_count": str(stats["source_visible_surface_count"]),
            "img04_surface_count": str(stats["img04_surface_count"]),
        }
        for period, stats in sorted(period_stats.items())
    ]
    region_rows = [
        {
            "region_group": region,
            "surface_count": str(stats["surface_count"]),
            "main_sheet_count": str(stats["main_sheet_count"]),
            "source_visible_surface_count": str(stats["source_visible_surface_count"]),
            "verified_open_surface_count": str(stats["verified_open_surface_count"]),
            "img04_surface_count": str(stats["img04_surface_count"]),
        }
        for region, stats in sorted(region_stats.items())
    ]
    return summary_rows, period_rows, region_rows


def write_report(summary_rows: list[dict[str, str]], period_rows: list[dict[str, str]], region_rows: list[dict[str, str]]) -> None:
    failures = [row for row in summary_rows if row["gate"] == "fail"]
    lines = [
        "# Release Snapshot v1",
        "",
        "Scope: consolidated read-only release-health snapshot. Object-level image metrics count repeated views/photos of one source object once.",
        "",
        "## Gate Summary",
        "",
    ]
    for row in summary_rows:
        if row["gate"]:
            lines.append(f"- {row['metric']}: {row['value']} · {row['gate']} ({row['notes']})")
    lines.extend(["", "## Core Metrics", ""])
    for row in summary_rows[:18]:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Main Sheets by Period", ""])
    for row in period_rows:
        lines.append(f"- {row['period_band']}: main={row['main_sheet_count']}, surfaces={row['surface_count']}, IMG04={row['img04_surface_count']}")
    lines.extend(["", "## Region Distribution", ""])
    for row in sorted(region_rows, key=lambda item: int(item["surface_count"]), reverse=True)[:25]:
        lines.append(
            f"- {row['region_group']}: surfaces={row['surface_count']}, main={row['main_sheet_count']}, "
            f"visible={row['source_visible_surface_count']}, open={row['verified_open_surface_count']}, IMG04={row['img04_surface_count']}"
        )
    lines.extend(["", "## Failed Gates", ""])
    if failures:
        for row in failures:
            lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    else:
        lines.append("- none")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    summary_rows, period_rows, region_rows = build_rows()
    write_csv(SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_csv(PERIOD, period_rows, PERIOD_FIELDS)
    write_csv(REGION, region_rows, REGION_FIELDS)
    write_report(summary_rows, period_rows, region_rows)
    print(f"public_surfaces={next(row['value'] for row in summary_rows if row['metric'] == 'public_surfaces')}")
    print(f"archive_active_public_sources={next(row['value'] for row in summary_rows if row['metric'] == 'archive_active_public_sources')}")
    print(f"object_source_visible_rate={next(row['value'] for row in summary_rows if row['metric'] == 'object_source_visible_rate')}%")
    print(f"object_verified_open_rate={next(row['value'] for row in summary_rows if row['metric'] == 'object_verified_open_rate')}%")
    print(f"object_img04_rate={next(row['value'] for row in summary_rows if row['metric'] == 'object_img04_rate')}%")
    print(f"wrote {SUMMARY.relative_to(ROOT)}")
    print(f"wrote {PERIOD.relative_to(ROOT)}")
    print(f"wrote {REGION.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
