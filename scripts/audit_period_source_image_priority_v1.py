#!/usr/bin/env python3
"""Combine period-level source coverage and image coverage for capture planning."""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from pathlib import Path

import audit_source_coverage_rate_v1 as source_cov


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

IMAGE_METRICS = DATA / "layered_image_source_metrics_v1.csv"
OUTPUT = DATA / "period_source_image_capture_priority_v1.csv"
REPORT = DOCS / "PERIOD_SOURCE_IMAGE_CAPTURE_PRIORITY_v1.md"

LAUNCH_WEIGHTED_IMAGE_TARGET = 95.0

FIELDS = [
    "period_band",
    "period_weight",
    "record_count",
    "active_source_count",
    "weighted_source_points",
    "target_weighted_source_points",
    "period_source_coverage_rate",
    "weighted_image_coverage_rate",
    "source_visible_rate",
    "publication_grade_rate",
    "open_image_rate",
    "img00_count",
    "img01_count",
    "img02_count",
    "img03_count",
    "img04_count",
    "source_gap_to_target",
    "image_gap_to_launch_target",
    "capture_priority_index",
    "recommended_next_action",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pct(value: float) -> str:
    return f"{value * 100:.2f}"


def image_period_metrics() -> dict[str, dict[str, str]]:
    rows = read_csv(IMAGE_METRICS)
    return {
        row["group_value"]: row
        for row in rows
        if row.get("group_type") == "period_band"
    }


def action_for_period(period: str, source_rate: float, image_rate: float) -> str:
    if period == "pre_1930":
        if image_rate >= 70 and source_rate < 0.35:
            return "Hold broad capture; add targeted non-West/local source diversity and dedupe repeated early image evidence."
        return "Target missing regional source families only; do not let prewar work displace postwar coverage."
    if source_rate < 0.35 and image_rate < 60:
        return "Highest priority: add new active sources and prefer IMG03/strong IMG02 records before adding more thin sheets."
    if source_rate < 0.35:
        return "Add source breadth first: local/community/university/government adapters before more records from existing sources."
    if image_rate < 60:
        return "Improve image quality: upgrade IMG02/IMG00/IMG04 through source-specific image adapters and rights review."
    return "Maintain; fill known region/theme gaps and improve grouping/text enrichment."


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    rows = source_cov.capture_rows()
    registry = source_cov.registry_by_source_name()
    image_metrics = image_period_metrics()

    period_sources: dict[str, set[str]] = defaultdict(set)
    period_region_points: dict[str, float] = defaultdict(float)
    period_source_regions: dict[str, dict[str, str]] = defaultdict(dict)
    period_record_counts: dict[str, int] = defaultdict(int)

    for row in rows:
        period = source_cov.period_band(row)
        if period not in source_cov.PERIOD_WEIGHTS:
            continue
        period_record_counts[period] += 1
        source = source_cov.clean(row.get("source_name"))
        if not source or source in period_sources[period]:
            continue
        region = source_cov.canonical_region(source, registry)
        period_sources[period].add(source)
        period_source_regions[period][source] = region
        period_region_points[period] += source_cov.region_weight(region)

    out: list[dict[str, str]] = []
    for period, weight in source_cov.PERIOD_WEIGHTS.items():
        source_points = period_region_points.get(period, 0.0)
        target_points = source_cov.WEIGHTED_SOURCE_TARGET * weight
        source_rate = min(source_points / target_points, 1.0) if target_points else 0.0

        image = image_metrics.get(period, {})
        image_rate = float(image.get("weighted_publication_rate") or 0.0)
        source_visible_rate = float(image.get("source_visible_rate") or 0.0)
        publication_grade_rate = float(image.get("publication_grade_rate") or 0.0)
        open_image_rate = float(image.get("open_image_rate") or 0.0)
        source_gap = max(0.0, 1.0 - source_rate)
        image_gap = max(0.0, (LAUNCH_WEIGHTED_IMAGE_TARGET - image_rate) / LAUNCH_WEIGHTED_IMAGE_TARGET)
        priority = weight * ((0.55 * source_gap) + (0.45 * image_gap))
        out.append(
            {
                "period_band": period,
                "period_weight": f"{weight:.2f}",
                "record_count": str(period_record_counts.get(period, 0)),
                "active_source_count": str(len(period_sources.get(period, set()))),
                "weighted_source_points": f"{source_points:.2f}",
                "target_weighted_source_points": f"{target_points:.2f}",
                "period_source_coverage_rate": pct(source_rate),
                "weighted_image_coverage_rate": f"{image_rate:.2f}",
                "source_visible_rate": f"{source_visible_rate:.2f}",
                "publication_grade_rate": f"{publication_grade_rate:.2f}",
                "open_image_rate": f"{open_image_rate:.2f}",
                "img00_count": image.get("img00_count", "0"),
                "img01_count": image.get("img01_count", "0"),
                "img02_count": image.get("img02_count", "0"),
                "img03_count": image.get("img03_count", "0"),
                "img04_count": image.get("img04_count", "0"),
                "source_gap_to_target": pct(source_gap),
                "image_gap_to_launch_target": pct(image_gap),
                "capture_priority_index": f"{priority:.4f}",
                "recommended_next_action": action_for_period(period, source_rate, image_rate),
            }
        )

    out.sort(key=lambda row: float(row["capture_priority_index"]), reverse=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(out)

    lines = [
        "# Period Source + Image Capture Priority v1",
        "",
        f"Date: {date.today().isoformat()}",
        "",
        "Scope: active capture records grouped by project period bands. This report combines period-level source breadth and visual evidence health for next-capture planning.",
        "",
        "## Formula",
        "",
        "- `period_source_coverage_rate = weighted_source_points_in_period / target_weighted_source_points_for_period`",
        "- `image_gap_to_launch_target = (95 - weighted_image_coverage_rate) / 95`",
        "- `capture_priority_index = period_weight × (0.55 × source_gap + 0.45 × image_gap)`",
        "",
        "Source gap is weighted slightly higher because adding another record from the same source does not solve archive breadth.",
        "",
        "## Ranked Periods",
        "",
    ]
    for row in out:
        lines.append(
            f"- {row['period_band']}: priority={row['capture_priority_index']}, "
            f"source={row['period_source_coverage_rate']}%, image={row['weighted_image_coverage_rate']}%, "
            f"active_sources={row['active_source_count']}, records={row['record_count']}"
        )
        lines.append(f"  Action: {row['recommended_next_action']}")

    lines.extend(["", "## Current Table", ""])
    for row in out:
        lines.append(
            f"- {row['period_band']}: source_points={row['weighted_source_points']}/{row['target_weighted_source_points']}, "
            f"source_gap={row['source_gap_to_target']}%, image_gap={row['image_gap_to_launch_target']}%, "
            f"IMG03={row['img03_count']}, IMG02={row['img02_count']}, IMG00={row['img00_count']}, IMG04={row['img04_count']}"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- 1930-1970 remains the highest-priority period because it has the largest period weight, weak source breadth, and weak weighted image coverage.",
            "- 1970-2000 ranks second because its source breadth is still low, even though its visible-image rate is comparatively healthy after the latest DigitalNZ batch.",
            "- 2000-2026 ranks third in the combined index, but it has the weakest weighted image coverage and needs independent/local post-digital sources with stronger image evidence.",
            "- pre_1930 has comparatively strong image coverage and lower period weight; it should receive targeted non-West/local source work, not broad capture.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUTPUT}")
    print(f"Wrote {REPORT}")
    for row in out:
        print(row["period_band"], row["capture_priority_index"], row["period_source_coverage_rate"], row["weighted_image_coverage_rate"])


if __name__ == "__main__":
    main()
