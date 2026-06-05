#!/usr/bin/env python3
"""Audit source coverage as a region/time weighted breadth metric.

This metric is deliberately separate from image coverage. It asks whether the
source pool is broad enough across regions and periods, before asking whether
individual records have good images.
"""

from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

REGISTRY = DATA / "source_prospect_registry_v2.csv"
PRE_SURFACE_SOURCE_REGISTRY = DATA / "nonmainstream_source_success_registry_2026_v1.csv"
OUTPUT = DATA / "source_coverage_rate_v1.csv"
REGION_OUTPUT = DATA / "source_coverage_region_breakdown_v1.csv"
PERIOD_OUTPUT = DATA / "source_coverage_period_breakdown_v1.csv"
REPORT = DOCS / "SOURCE_COVERAGE_RATE_v1.md"

WEIGHTED_SOURCE_TARGET = 2000.0
MIN_RELEASE_SOURCE_COVERAGE_RATE = 80.0

REGION_WEIGHTS = {
    "Africa": 1.35,
    "East Asia": 1.25,
    "Southeast Asia": 1.35,
    "South Asia": 1.35,
    "Middle East and North Africa": 1.35,
    "Latin America": 1.30,
    "Latin America and the Caribbean": 1.30,
    "Eastern Europe": 1.20,
    "Eastern Europe / Caucasus": 1.20,
    "Oceania and Pacific": 1.10,
    "Western/Central Europe": 0.85,
    "Europe": 0.85,
    "North America": 0.75,
    "Global": 0.70,
    "Global / web / transnational": 0.70,
    "North America / Global digital": 0.70,
    "Latin America / Transregional": 1.30,
    "Mainland China": 1.25,
}

PERIOD_WEIGHTS = {
    "pre_1930": 0.15,
    "1930_1970": 0.35,
    "1970_2000": 0.25,
    "2000_2026": 0.25,
}

SOURCE_REGION_OVERRIDES = {
    "Art Institute of Chicago API": "North America",
    "Auckland Libraries Heritage Collections / CONTENTdm": "Oceania and Pacific",
    "Biblioteca Nacional Digital de Chile / Memoria Chilena": "Latin America",
    "Chinese Posters": "Mainland China",
    "Cooper Hewitt Collection GraphQL API": "North America",
    "Gallica / BnF APIs": "Western/Central Europe",
    "Internet Archive / text and periodical collections": "Global / web / transnational",
    "Library of Congress loc.gov API": "North America",
    "NAIDOC Poster Gallery": "Oceania and Pacific",
    "NDL Search": "East Asia",
    "NDL Search / National Diet Library": "East Asia",
    "Roots.sg / National Heritage Board Singapore": "Southeast Asia",
    "American University of Beirut ScholarWorks": "Middle East and North Africa",
    "National Repository of Nigeria": "Africa",
    "Stellenbosch University Scholar": "Africa",
    "University of Cape Town Digital Collections": "Africa",
    "University of Pretoria Research Repository": "Africa",
    "Wits University WiredSpace": "Africa",
    "V&A Collections API": "Western/Central Europe",
    "Wellcome Collection Catalogue API": "Western/Central Europe",
}

UNMAPPED_REGION_LABELS = {
    "",
    "active payload / needs registry mapping",
    "captured source / needs mapping",
    "unmapped",
    "unmapped_region",
}

SUMMARY_FIELDS = [
    "metric",
    "value",
    "notes",
]

REGION_FIELDS = [
    "region_group",
    "active_source_count",
    "candidate_source_count",
    "region_weight",
    "weighted_active_source_points",
    "weighted_target_points",
    "region_target_source_count",
    "region_balance_rate",
]

PERIOD_FIELDS = [
    "period_band",
    "active_source_count",
    "record_count",
    "period_weight",
    "target_source_count",
    "period_balance_rate",
]


def clean(value: str | None) -> str:
    return (value or "").strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe_int(value: str | None) -> int | None:
    value = clean(value)
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def period_band(row: dict[str, str]) -> str:
    year = safe_int(row.get("date_end")) or safe_int(row.get("date_start"))
    if year is None:
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


def capture_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(DATA.glob("capture_batch_*_records.csv")):
        if "cell_assignments" in path.name:
            continue
        for row in read_csv(path):
            row = dict(row)
            row["_capture_file"] = path.name
            rows.append(row)
    return rows


def pre_surface_source_registry_count() -> int:
    return sum(
        1
        for row in read_csv(PRE_SURFACE_SOURCE_REGISTRY)
        if clean(row.get("source_success_status")) == "success"
    )


def registry_rows() -> list[dict[str, str]]:
    return read_csv(REGISTRY)


def registry_by_source_name() -> dict[str, dict[str, str]]:
    return {clean(row.get("source_name")).lower(): row for row in registry_rows() if clean(row.get("source_name"))}


def canonical_region(source_name: str, registry: dict[str, dict[str, str]]) -> str:
    if source_name in SOURCE_REGION_OVERRIDES:
        return SOURCE_REGION_OVERRIDES[source_name]
    row = registry.get(source_name.lower(), {})
    region = clean(row.get("region_group"))
    if region in UNMAPPED_REGION_LABELS:
        country = clean(row.get("country_or_territory"))
        if country in {"China", "Hong Kong", "Japan", "Korea", "Taiwan"}:
            return "East Asia"
        if country in {"Singapore", "Indonesia", "Thailand", "Vietnam", "Cambodia", "Philippines", "Malaysia", "Laos"}:
            return "Southeast Asia"
        return "unmapped_region"
    return region or "unmapped_region"


def region_weight(region: str) -> float:
    return REGION_WEIGHTS.get(region, 1.0 if region != "unmapped_region" else 0.20)


def pct(value: float) -> str:
    return f"{value * 100:.2f}"


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    pre_surface_count = pre_surface_source_registry_count()
    rows = capture_rows()
    registry = registry_by_source_name()
    active_sources = sorted({clean(row.get("source_name")) for row in rows if clean(row.get("source_name"))})
    active_region = {source: canonical_region(source, registry) for source in active_sources}

    candidate_by_region: Counter[str] = Counter()
    for row in registry_rows():
        source = clean(row.get("source_name"))
        if not source:
            continue
        candidate_by_region[canonical_region(source, registry)] += 1

    active_by_region: dict[str, set[str]] = defaultdict(set)
    for source, region in active_region.items():
        active_by_region[region].add(source)

    weighted_active_points = sum(region_weight(region) for region in active_region.values())
    source_pool_rate = min(weighted_active_points / WEIGHTED_SOURCE_TARGET, 1.0)

    considered_regions = sorted(set(REGION_WEIGHTS) | set(active_by_region) | set(candidate_by_region))
    total_region_weight = sum(region_weight(region) for region in considered_regions if region != "unmapped_region")
    region_rows: list[dict[str, str]] = []
    region_balance_acc = 0.0
    for region in considered_regions:
        weight = region_weight(region)
        if region == "unmapped_region":
            target_points = max(1.0, WEIGHTED_SOURCE_TARGET * 0.02)
        else:
            target_points = WEIGHTED_SOURCE_TARGET * (weight / total_region_weight)
        active_count = len(active_by_region.get(region, set()))
        weighted_points = active_count * weight
        balance = min(weighted_points / target_points, 1.0) if target_points else 0.0
        if region != "unmapped_region":
            region_balance_acc += balance * weight
        region_rows.append(
            {
                "region_group": region,
                "active_source_count": str(active_count),
                "candidate_source_count": str(candidate_by_region.get(region, 0)),
                "region_weight": f"{weight:.2f}",
                "weighted_active_source_points": f"{weighted_points:.2f}",
                "weighted_target_points": f"{target_points:.2f}",
                "region_target_source_count": str(math.ceil(target_points / weight)) if weight else "0",
                "region_balance_rate": pct(balance),
            }
        )
    region_balance_rate = region_balance_acc / total_region_weight if total_region_weight else 0.0

    period_sources: dict[str, set[str]] = defaultdict(set)
    period_record_counts: Counter[str] = Counter()
    for row in rows:
        band = period_band(row)
        period_record_counts[band] += 1
        source = clean(row.get("source_name"))
        if source:
            period_sources[band].add(source)

    period_rows: list[dict[str, str]] = []
    time_balance_acc = 0.0
    for band, weight in PERIOD_WEIGHTS.items():
        target = WEIGHTED_SOURCE_TARGET * weight
        active_count = len(period_sources.get(band, set()))
        balance = min(active_count / target, 1.0) if target else 0.0
        time_balance_acc += balance * weight
        period_rows.append(
            {
                "period_band": band,
                "active_source_count": str(active_count),
                "record_count": str(period_record_counts.get(band, 0)),
                "period_weight": f"{weight:.2f}",
                "target_source_count": str(math.ceil(target)),
                "period_balance_rate": pct(balance),
            }
        )
    time_balance_rate = time_balance_acc / sum(PERIOD_WEIGHTS.values())

    source_coverage_rate = source_pool_rate * time_balance_rate
    strict_distribution_adjusted_rate = source_pool_rate * region_balance_rate * time_balance_rate

    summary_rows = [
        {
            "metric": "active_source_count",
            "value": str(len(active_sources)),
            "notes": "Distinct source_name values with at least one captured record.",
        },
        {
            "metric": "candidate_source_count",
            "value": str(len(registry_rows())),
            "notes": "Candidate/prospect sources in source_prospect_registry_v2; not counted as active coverage.",
        },
        {
            "metric": "pre_surface_source_registry_count",
            "value": str(pre_surface_count),
            "notes": "Official source sites verified as reachable, but not counted as active source coverage until item-level image-bearing surfaces are built.",
        },
        {
            "metric": "weighted_active_source_points",
            "value": f"{weighted_active_points:.2f}",
            "notes": "Sum of active source region weights. Non-West/local regions carry higher weights.",
        },
        {
            "metric": "weighted_source_target",
            "value": f"{WEIGHTED_SOURCE_TARGET:.2f}",
            "notes": "Final release source target requested as at least 2000 sources, expressed as weighted source points.",
        },
        {
            "metric": "minimum_release_source_coverage_rate",
            "value": f"{MIN_RELEASE_SOURCE_COVERAGE_RATE:.2f}",
            "notes": "Release gate threshold for source coverage before publication readiness.",
        },
        {
            "metric": "release_source_coverage_gate_passed",
            "value": str((source_pool_rate * 100) >= MIN_RELEASE_SOURCE_COVERAGE_RATE).lower(),
            "notes": "True only when source_pool_rate reaches the configured final release coverage threshold.",
        },
        {
            "metric": "source_pool_rate",
            "value": pct(source_pool_rate),
            "notes": "weighted_active_source_points / weighted_source_target.",
        },
        {
            "metric": "region_weighted_balance_rate",
            "value": pct(region_balance_rate),
            "notes": "Weighted average of per-region active-source coverage against regional source targets.",
        },
        {
            "metric": "time_weighted_balance_rate",
            "value": pct(time_balance_rate),
            "notes": "Weighted average of active-source coverage across period bands.",
        },
        {
            "metric": "source_coverage_rate_v1",
            "value": pct(source_coverage_rate),
            "notes": "source_pool_rate * time_weighted_balance_rate. The source pool itself is already region-weighted.",
        },
        {
            "metric": "strict_distribution_adjusted_source_coverage_rate",
            "value": pct(strict_distribution_adjusted_rate),
            "notes": "source_pool_rate * region_weighted_balance_rate * time_weighted_balance_rate; diagnostic only.",
        },
    ]

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(summary_rows)
    with REGION_OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REGION_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(region_rows, key=lambda row: (-float(row["region_weight"]), row["region_group"])))
    with PERIOD_OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PERIOD_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(period_rows)

    weakest_regions = sorted(region_rows, key=lambda row: float(row["region_balance_rate"]))[:8]
    weakest_periods = sorted(period_rows, key=lambda row: float(row["period_balance_rate"]))[:4]
    lines = [
        "# Source Coverage Rate v1",
        "",
        f"Date: {date.today().isoformat()}",
        "",
        "Scope: active captured sources, not candidate/prospect sources. This metric measures source breadth and distribution; it is separate from image coverage.",
        "",
        "## Formula",
        "",
        "- `source_pool_rate = weighted_active_source_points / weighted_source_target`",
        "- `region_weighted_balance_rate = weighted average of per-region active-source coverage`",
        "- `time_weighted_balance_rate = weighted average of active-source coverage by period band`",
        "- `source_coverage_rate_v1 = source_pool_rate × time_weighted_balance_rate`",
        "- `strict_distribution_adjusted_source_coverage_rate = source_pool_rate × region_weighted_balance_rate × time_weighted_balance_rate`",
        "",
        "The main rate uses region-weighted source points first, then applies time coverage. The stricter diagnostic additionally penalizes uneven regional distribution. The current release source target is at least 2000 sources, with an 80% minimum source-coverage gate before final release.",
        "",
        "## Current Result",
        "",
    ]
    for row in summary_rows:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Weakest Regions", ""])
    for row in weakest_regions:
        lines.append(
            f"- {row['region_group']}: active={row['active_source_count']}, "
            f"candidate={row['candidate_source_count']}, target≈{row['region_target_source_count']}, "
            f"balance={row['region_balance_rate']}%"
        )
    lines.extend(["", "## Period Balance", ""])
    for row in period_rows:
        lines.append(
            f"- {row['period_band']}: active_sources={row['active_source_count']}, "
            f"target≈{row['target_source_count']}, records={row['record_count']}, "
            f"balance={row['period_balance_rate']}%"
        )
    lines.extend(["", "## Weakest Periods", ""])
    for row in weakest_periods:
        lines.append(f"- {row['period_band']}: {row['period_balance_rate']}%")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Candidate sources are useful for planning but do not count as coverage until they produce captured records.",
            "- Region weights intentionally favor underrepresented/local regions so the score is not satisfied by Western museum API concentration.",
            "- Period weights currently prioritize postwar coverage: 1930-1970, 1970-2000, and 2000-2026 together carry 85% of the time-balance weight.",
            "- `unmapped_region` is included in diagnostics but carries a low weight; sources should be mapped rather than left as a hidden coverage bucket.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUTPUT}")
    print(f"Wrote {REGION_OUTPUT}")
    print(f"Wrote {PERIOD_OUTPUT}")
    print(f"Wrote {REPORT}")
    print({row["metric"]: row["value"] for row in summary_rows})


if __name__ == "__main__":
    main()
