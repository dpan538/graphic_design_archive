#!/usr/bin/env python3
"""Audit source coverage with distribution and research-quality penalties.

v1 intentionally measured whether the weighted source pool and period fill had
reached the final source-count target. v2 keeps that capacity signal, but makes
the stricter distribution and main-sheet research quality visible as first-class
release diagnostics.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import audit_source_coverage_rate_v1 as v1


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

PAYLOAD = ROOT / "generated" / "public_surfaces_v1.json"
RESEARCH_AUDIT = DATA / "main_sheet_research_value_audit_v1.csv"

SUMMARY_OUT = DATA / "source_coverage_rate_v2.csv"
PERIOD_OUT = DATA / "source_coverage_period_breakdown_v2.csv"
REGION_OUT = DATA / "source_coverage_region_breakdown_v2.csv"
REPORT = DOCS / "SOURCE_COVERAGE_RATE_v2.md"

SUMMARY_FIELDS = ["metric", "value", "notes"]
PERIOD_FIELDS = [
    "period_band",
    "surface_count",
    "main_sheet_count",
    "quality_main_count",
    "source_visible_count",
    "text_action_needed_count",
    "desired_surface_target",
    "surface_balance_rate",
    "quality_main_balance_rate",
]
REGION_FIELDS = [
    "region_group",
    "surface_count",
    "main_sheet_count",
    "quality_main_count",
    "source_visible_count",
    "desired_surface_target",
    "surface_balance_rate",
    "quality_main_balance_rate",
]

PERIOD_SURFACE_TARGETS = {
    "pre_1930": 1700,
    "1930_1970": 2000,
    "1970_2000": 2200,
    "2000_2026": 2600,
}

REGION_SURFACE_TARGETS = {
    "Africa": 750,
    "East Asia": 750,
    "Southeast Asia": 800,
    "South Asia": 750,
    "Middle East and North Africa": 750,
    "Latin America": 850,
    "Latin America and the Caribbean": 850,
    "Eastern Europe": 650,
    "Eastern Europe / Caucasus": 650,
    "Oceania and Pacific": 450,
    "Western/Central Europe": 550,
    "Europe": 550,
    "North America": 450,
    "Global": 400,
    "Global / web / transnational": 400,
    "Unresolved region": 250,
}


def clean(value: object) -> str:
    return str(value or "").strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def pct(value: float) -> str:
    return f"{value * 100:.2f}"


def period_band(surface: dict) -> str:
    try:
        year = int(surface.get("dateEnd") or surface.get("dateStart"))
    except (TypeError, ValueError):
        return "undated_or_unparsed"
    if year <= 1930:
        return "pre_1930"
    if year <= 1970:
        return "1930_1970"
    if year <= 2000:
        return "1970_2000"
    if year <= 2026:
        return "2000_2026"
    return "post_2026_or_error"


def macro_region(surface: dict) -> str:
    folders = surface.get("folders") if isinstance(surface.get("folders"), list) else []
    for folder in folders:
        if folder.get("type") == "region":
            return clean(folder.get("title")).split("/")[0].strip()
    return "Unresolved region"


def image_state(surface: dict) -> str:
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    return clean(image.get("state")) or "IMG00"


def v1_capacity_metrics() -> dict[str, str]:
    rows = read_csv(DATA / "source_coverage_rate_v1.csv")
    return {row["metric"]: row["value"] for row in rows}


def research_actions() -> dict[str, dict[str, str]]:
    return {row["surface_id"]: row for row in read_csv(RESEARCH_AUDIT)}


def is_quality_main(surface: dict, action_row: dict[str, str] | None) -> bool:
    if clean(surface.get("publicationRole")) != "main_sheet":
        return False
    if image_state(surface) not in {"IMG01", "IMG02", "IMG03"}:
        return False
    if not action_row:
        return False
    if action_row.get("recommended_action") not in {"keep_main", "keep_main_add_editorial_text"}:
        return False
    return int(action_row.get("research_value_score") or 0) >= 60


def balance(count: int, target: int) -> float:
    return min(count / target, 1.0) if target else 0.0


def average(rows: list[float]) -> float:
    return sum(rows) / len(rows) if rows else 0.0


def main() -> None:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    surfaces = payload.get("surfaces", [])
    actions = research_actions()
    capacity = v1_capacity_metrics()

    period_stats: dict[str, Counter[str]] = defaultdict(Counter)
    region_stats: dict[str, Counter[str]] = defaultdict(Counter)

    for surface in surfaces:
        sid = clean(surface.get("surfaceId"))
        action = actions.get(sid)
        period = period_band(surface)
        region = macro_region(surface)
        for stats in (period_stats[period], region_stats[region]):
            stats["surface_count"] += 1
            if clean(surface.get("publicationRole")) == "main_sheet":
                stats["main_sheet_count"] += 1
            if image_state(surface) in {"IMG01", "IMG02", "IMG03"}:
                stats["source_visible_count"] += 1
            if is_quality_main(surface, action):
                stats["quality_main_count"] += 1
            if action and action.get("recommended_action") == "keep_main_add_editorial_text":
                stats["text_action_needed_count"] += 1

    period_rows: list[dict[str, str]] = []
    for period in list(PERIOD_SURFACE_TARGETS) + sorted(set(period_stats) - set(PERIOD_SURFACE_TARGETS)):
        stats = period_stats.get(period, Counter())
        target = PERIOD_SURFACE_TARGETS.get(period, 250)
        period_rows.append(
            {
                "period_band": period,
                "surface_count": str(stats["surface_count"]),
                "main_sheet_count": str(stats["main_sheet_count"]),
                "quality_main_count": str(stats["quality_main_count"]),
                "source_visible_count": str(stats["source_visible_count"]),
                "text_action_needed_count": str(stats["text_action_needed_count"]),
                "desired_surface_target": str(target),
                "surface_balance_rate": pct(balance(stats["surface_count"], target)),
                "quality_main_balance_rate": pct(balance(stats["quality_main_count"], target)),
            }
        )

    region_rows: list[dict[str, str]] = []
    for region in sorted(set(REGION_SURFACE_TARGETS) | set(region_stats)):
        stats = region_stats.get(region, Counter())
        target = REGION_SURFACE_TARGETS.get(region, 250)
        region_rows.append(
            {
                "region_group": region,
                "surface_count": str(stats["surface_count"]),
                "main_sheet_count": str(stats["main_sheet_count"]),
                "quality_main_count": str(stats["quality_main_count"]),
                "source_visible_count": str(stats["source_visible_count"]),
                "desired_surface_target": str(target),
                "surface_balance_rate": pct(balance(stats["surface_count"], target)),
                "quality_main_balance_rate": pct(balance(stats["quality_main_count"], target)),
            }
        )

    period_surface_balance = average([float(row["surface_balance_rate"]) / 100 for row in period_rows if row["period_band"] in PERIOD_SURFACE_TARGETS])
    period_quality_balance = average([float(row["quality_main_balance_rate"]) / 100 for row in period_rows if row["period_band"] in PERIOD_SURFACE_TARGETS])
    region_surface_balance = average([float(row["surface_balance_rate"]) / 100 for row in region_rows if row["region_group"] in REGION_SURFACE_TARGETS])
    region_quality_balance = average([float(row["quality_main_balance_rate"]) / 100 for row in region_rows if row["region_group"] in REGION_SURFACE_TARGETS])
    source_visible_rate = sum(1 for surface in surfaces if image_state(surface) in {"IMG01", "IMG02", "IMG03"}) / len(surfaces) if surfaces else 0.0

    strict_v1 = float(capacity.get("strict_distribution_adjusted_source_coverage_rate", "0") or 0) / 100
    source_pool_period_fill = float(capacity.get("source_coverage_rate_v1", "0") or 0) / 100
    research_quality_adjusted = source_pool_period_fill * period_quality_balance * region_quality_balance * source_visible_rate

    summary_rows = [
        {
            "metric": "source_pool_period_fill_rate",
            "value": pct(source_pool_period_fill),
            "notes": "Former v1 source_coverage_rate; capacity/time fill only, capped at 100%.",
        },
        {
            "metric": "strict_distribution_adjusted_source_coverage_rate",
            "value": pct(strict_v1),
            "notes": "v1 strict diagnostic retained as a first-class warning signal.",
        },
        {
            "metric": "period_surface_balance_rate",
            "value": pct(period_surface_balance),
            "notes": "Surface count balance against v2 period targets; 2000-2026 target is intentionally higher.",
        },
        {
            "metric": "period_quality_main_balance_rate",
            "value": pct(period_quality_balance),
            "notes": "Quality main-sheet balance against v2 period targets.",
        },
        {
            "metric": "region_surface_balance_rate",
            "value": pct(region_surface_balance),
            "notes": "Surface count balance against v2 regional targets.",
        },
        {
            "metric": "region_quality_main_balance_rate",
            "value": pct(region_quality_balance),
            "notes": "Quality main-sheet balance against v2 regional targets.",
        },
        {
            "metric": "source_visible_surface_rate",
            "value": pct(source_visible_rate),
            "notes": "Surfaces with IMG01/IMG02/IMG03.",
        },
        {
            "metric": "research_quality_adjusted_source_coverage_rate_v2",
            "value": pct(research_quality_adjusted),
            "notes": "source_pool_period_fill * period_quality_main_balance * region_quality_main_balance * source_visible_rate.",
        },
    ]

    write_csv(SUMMARY_OUT, summary_rows, SUMMARY_FIELDS)
    write_csv(PERIOD_OUT, period_rows, PERIOD_FIELDS)
    write_csv(REGION_OUT, region_rows, REGION_FIELDS)

    weakest_periods = sorted(period_rows, key=lambda row: float(row["quality_main_balance_rate"]))[:4]
    weakest_regions = sorted(region_rows, key=lambda row: float(row["quality_main_balance_rate"]))[:10]
    lines = [
        "# Source Coverage Rate v2",
        "",
        "Scope: public surfaces plus main-sheet research-value diagnostics. v2 separates capacity fill from distribution and research quality.",
        "",
        "## Summary",
        "",
    ]
    for row in summary_rows:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Period Targets", ""])
    for row in period_rows:
        lines.append(
            f"- {row['period_band']}: surfaces={row['surface_count']}, main={row['main_sheet_count']}, "
            f"quality_main={row['quality_main_count']}, target={row['desired_surface_target']}, "
            f"surface_balance={row['surface_balance_rate']}%, quality_balance={row['quality_main_balance_rate']}%"
        )
    lines.extend(["", "## Weakest Periods By Quality Main Balance", ""])
    for row in weakest_periods:
        lines.append(f"- {row['period_band']}: quality_balance={row['quality_main_balance_rate']}%, target={row['desired_surface_target']}")
    lines.extend(["", "## Weakest Regions By Quality Main Balance", ""])
    for row in weakest_regions:
        lines.append(
            f"- {row['region_group']}: surfaces={row['surface_count']}, quality_main={row['quality_main_count']}, "
            f"target={row['desired_surface_target']}, quality_balance={row['quality_main_balance_rate']}%"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `source_pool_period_fill_rate` can reach 100% while the archive is still structurally weak.",
            "- `research_quality_adjusted_source_coverage_rate_v2` should be treated as the stricter release-facing source coverage diagnostic.",
            "- v2 gives the 2000-2026 period a larger target because contemporary graphic design, graphic art, and visual communication are broader and more diverse in the internet period.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print({row["metric"]: row["value"] for row in summary_rows})
    print(f"wrote {SUMMARY_OUT.relative_to(ROOT)}")
    print(f"wrote {PERIOD_OUT.relative_to(ROOT)}")
    print(f"wrote {REGION_OUT.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
