#!/usr/bin/env python3
"""Audit layered image/source metrics across capture records.

This is intentionally not a launch gate. It measures the current capture corpus
before public-surface assignment, splitting image health by period, source
family, and region. It also flags repeated image URLs so repeated thumbnail or
placeholder problems are visible before a rebuild.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

REGISTRY = DATA / "source_prospect_registry_v2.csv"
METRICS = DATA / "layered_image_source_metrics_v1.csv"
DUPLICATES = DATA / "duplicate_image_url_warnings_v1.csv"
REPORT = DOCS / "LAYERED_IMAGE_SOURCE_METRICS_v1.md"

IMAGE_VISIBLE = {"IMG01", "IMG02", "IMG03"}
PUBLICATION_GRADE = {"IMG02", "IMG03"}
OPEN_IMAGE = {"IMG03"}
PUBLICATION_WEIGHTS = {
    "IMG03": 0.9,
    "IMG02": 0.55,
    "IMG01": 0.3,
    "IMG00": 0.0,
    "IMG04": 0.0,
}

METRIC_FIELDS = [
    "group_type",
    "group_value",
    "records_total",
    "source_visible_count",
    "source_visible_rate",
    "publication_grade_count",
    "publication_grade_rate",
    "weighted_publication_score",
    "weighted_publication_rate",
    "open_image_count",
    "open_image_rate",
    "rights_labeled_count",
    "rights_labeled_rate",
    "unclear_image_state_count",
    "unclear_image_state_rate",
    "anchor_image_available_count",
    "anchor_image_available_rate",
    "duplicate_image_url_records",
    "duplicate_image_url_rate",
    "img00_count",
    "img01_count",
    "img02_count",
    "img03_count",
    "img04_count",
]

DUP_FIELDS = [
    "image_url_detected",
    "record_count",
    "source_names",
    "period_bands",
    "capture_ids",
    "titles",
]


def clean(value: str | None) -> str:
    return (value or "").strip()


def lower(value: str | None) -> str:
    return clean(value).lower()


def yes(value: str | None) -> bool:
    return lower(value) in {"true", "yes", "1", "y"}


def safe_int(value: str | None) -> int | None:
    value = clean(value)
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def period_band(row: dict[str, str]) -> str:
    # Per project rule: long-span records use ending year for period assignment.
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


def canonical_image_state(row: dict[str, str]) -> str:
    state = clean(row.get("image_presence_code"))
    if state in {"IMG00", "IMG01", "IMG02", "IMG03", "IMG04"}:
        return state
    state = clean(row.get("image_state_evaluation"))
    for code in ["IMG00", "IMG01", "IMG02", "IMG03", "IMG04"]:
        if code in state:
            return code
    return "UNKNOWN"


def has_source_return(row: dict[str, str]) -> bool:
    return bool(clean(row.get("source_record_url")) or clean(row.get("source_api_url")))


def has_image_url(row: dict[str, str]) -> bool:
    return bool(clean(row.get("image_url_detected")) or yes(row.get("iiif_or_viewer_available")))


def rights_labeled(row: dict[str, str]) -> bool:
    return bool(
        clean(row.get("source_rights_text"))
        or clean(row.get("rights_uri"))
        or clean(row.get("rights_basis"))
        or clean(row.get("image_state_review_note"))
    )


def source_visible(row: dict[str, str]) -> bool:
    state = canonical_image_state(row)
    return state in IMAGE_VISIBLE or has_image_url(row)


def publication_grade(row: dict[str, str]) -> bool:
    state = canonical_image_state(row)
    return state in PUBLICATION_GRADE and has_source_return(row) and rights_labeled(row)


def open_image(row: dict[str, str]) -> bool:
    state = canonical_image_state(row)
    return state in OPEN_IMAGE and (yes(row.get("local_copy_permitted")) or "open" in lower(row.get("rights_basis")))


def weighted_publication_score(row: dict[str, str]) -> float:
    return PUBLICATION_WEIGHTS.get(canonical_image_state(row), 0.0)


def unclear_image_state(row: dict[str, str]) -> bool:
    state = canonical_image_state(row)
    text = f"{row.get('image_state_evaluation','')} {row.get('image_state_confidence','')} {row.get('image_state_review_note','')}".lower()
    if state == "UNKNOWN":
        return True
    return "unclear" in text or "unknown" in text or "review" in text and not rights_labeled(row)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def registry_map() -> dict[str, dict[str, str]]:
    rows = read_csv(REGISTRY)
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        name = lower(row.get("source_name"))
        if name:
            out[name] = row
    return out


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


def pct(num: int, den: int) -> str:
    if not den:
        return "0.00"
    return f"{(num / den) * 100:.2f}"


def aggregate(rows: list[dict[str, str]], group_type: str, key_fn, duplicate_urls: set[str]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[key_fn(row) or "unmapped"].append(row)

    out: list[dict[str, str]] = []
    for group_value, items in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        total = len(items)
        state_counts = Counter(canonical_image_state(row) for row in items)
        duplicate_records = sum(1 for row in items if clean(row.get("image_url_detected")) in duplicate_urls)
        source_visible_count = sum(1 for row in items if source_visible(row))
        publication_grade_count = sum(1 for row in items if publication_grade(row))
        weighted_score = sum(weighted_publication_score(row) for row in items)
        open_image_count = sum(1 for row in items if open_image(row))
        rights_labeled_count = sum(1 for row in items if rights_labeled(row))
        unclear_count = sum(1 for row in items if unclear_image_state(row))
        anchor_count = sum(1 for row in items if canonical_image_state(row) in PUBLICATION_GRADE and has_image_url(row))
        out.append(
            {
                "group_type": group_type,
                "group_value": group_value,
                "records_total": str(total),
                "source_visible_count": str(source_visible_count),
                "source_visible_rate": pct(source_visible_count, total),
                "publication_grade_count": str(publication_grade_count),
                "publication_grade_rate": pct(publication_grade_count, total),
                "weighted_publication_score": f"{weighted_score:.2f}",
                "weighted_publication_rate": f"{(weighted_score / total) * 100:.2f}" if total else "0.00",
                "open_image_count": str(open_image_count),
                "open_image_rate": pct(open_image_count, total),
                "rights_labeled_count": str(rights_labeled_count),
                "rights_labeled_rate": pct(rights_labeled_count, total),
                "unclear_image_state_count": str(unclear_count),
                "unclear_image_state_rate": pct(unclear_count, total),
                "anchor_image_available_count": str(anchor_count),
                "anchor_image_available_rate": pct(anchor_count, total),
                "duplicate_image_url_records": str(duplicate_records),
                "duplicate_image_url_rate": pct(duplicate_records, total),
                "img00_count": str(state_counts.get("IMG00", 0)),
                "img01_count": str(state_counts.get("IMG01", 0)),
                "img02_count": str(state_counts.get("IMG02", 0)),
                "img03_count": str(state_counts.get("IMG03", 0)),
                "img04_count": str(state_counts.get("IMG04", 0)),
            }
        )
    return out


def truncate(values: list[str], limit: int = 5) -> str:
    seen = []
    for value in values:
        value = clean(value)
        if value and value not in seen:
            seen.append(value)
        if len(seen) >= limit:
            break
    return " | ".join(seen)


def host_of_url(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except ValueError:
        return ""


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    rows = capture_rows()
    sources = registry_map()

    for row in rows:
        source = sources.get(lower(row.get("source_name")), {})
        row["_period_band"] = period_band(row)
        row["_source_family"] = clean(source.get("source_family")) or "unmapped_source_family"
        row["_region_group"] = clean(source.get("region_group")) or "unmapped_region"
        row["_image_host"] = host_of_url(clean(row.get("image_url_detected")))

    url_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        url = clean(row.get("image_url_detected"))
        if url:
            url_groups[url].append(row)
    duplicate_urls = {url for url, items in url_groups.items() if len(items) > 1}

    metrics: list[dict[str, str]] = []
    metrics += aggregate(rows, "all_capture_records", lambda row: "all", duplicate_urls)
    metrics += aggregate(rows, "period_band", lambda row: row["_period_band"], duplicate_urls)
    metrics += aggregate(rows, "source_family", lambda row: row["_source_family"], duplicate_urls)
    metrics += aggregate(rows, "region_group", lambda row: row["_region_group"], duplicate_urls)
    metrics += aggregate(rows, "source_name", lambda row: clean(row.get("source_name")), duplicate_urls)

    with METRICS.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=METRIC_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(metrics)

    duplicate_rows: list[dict[str, str]] = []
    for url, items in sorted(url_groups.items(), key=lambda item: -len(item[1])):
        if len(items) <= 1:
            continue
        duplicate_rows.append(
            {
                "image_url_detected": url,
                "record_count": str(len(items)),
                "source_names": truncate([row.get("source_name", "") for row in items]),
                "period_bands": truncate([row["_period_band"] for row in items]),
                "capture_ids": truncate([row.get("capture_id", "") for row in items], limit=8),
                "titles": truncate([row.get("source_title", "") for row in items], limit=3),
            }
        )
    with DUPLICATES.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DUP_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(duplicate_rows)

    all_row = next(row for row in metrics if row["group_type"] == "all_capture_records")
    period_rows = [row for row in metrics if row["group_type"] == "period_band"]
    family_rows = [row for row in metrics if row["group_type"] == "source_family"]
    weak_periods = sorted(period_rows, key=lambda row: float(row["weighted_publication_rate"]))[:4]
    duplicate_top = duplicate_rows[:10]

    lines = [
        "# Layered Image and Source Metrics v1",
        "",
        f"Date: {date.today().isoformat()}",
        "",
        "Scope: capture records, not final public surfaces. These metrics measure the raw/candidate corpus before grouping and surface assignment.",
        "",
        "## Overall",
        "",
        f"- Capture records: {all_row['records_total']}",
        f"- Source-visible coverage: {all_row['source_visible_rate']}%",
        f"- Publication-grade candidate coverage: {all_row['publication_grade_rate']}%",
        f"- Weighted publication image rate: {all_row['weighted_publication_rate']}% ({all_row['weighted_publication_score']} weighted points)",
        f"- Open-image candidate coverage: {all_row['open_image_rate']}%",
        f"- Rights-labeled coverage: {all_row['rights_labeled_rate']}%",
        f"- Unclear image-state rate: {all_row['unclear_image_state_rate']}%",
        f"- Duplicate image URL record rate: {all_row['duplicate_image_url_rate']}%",
        "",
        "## Period Bands",
        "",
    ]
    for row in period_rows:
        lines.append(
            f"- {row['group_value']}: records={row['records_total']}, "
            f"source-visible={row['source_visible_rate']}%, "
            f"publication-grade={row['publication_grade_rate']}%, "
            f"weighted={row['weighted_publication_rate']}%, "
            f"open={row['open_image_rate']}%, duplicate-url={row['duplicate_image_url_rate']}%"
        )
    lines.extend(["", "## Lowest Weighted Publication Periods", ""])
    for row in weak_periods:
        lines.append(
            f"- {row['group_value']}: weighted={row['weighted_publication_rate']}% "
            f"({row['weighted_publication_score']} weighted points / {row['records_total']} records)"
        )
    lines.extend(["", "## Source Families", ""])
    for row in family_rows[:20]:
        lines.append(
            f"- {row['group_value']}: records={row['records_total']}, "
            f"source-visible={row['source_visible_rate']}%, "
            f"publication-grade={row['publication_grade_rate']}%, "
            f"weighted={row['weighted_publication_rate']}%, "
            f"open={row['open_image_rate']}%"
        )
    lines.extend(["", "## Duplicate Image URL Warnings", ""])
    if duplicate_top:
        for row in duplicate_top:
            lines.append(
                f"- {row['record_count']} records share `{row['image_url_detected']}`; "
                f"sources={row['source_names']}; periods={row['period_bands']}; ids={row['capture_ids']}"
            )
    else:
        lines.append("- No duplicate image URLs detected.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Source-visible coverage means an image or source viewer appears to exist.",
            "- Publication-grade candidate coverage requires IMG02/IMG03 plus source return and rights labeling.",
            f"- Weighted publication rate uses conservative visual-evidence weights: {PUBLICATION_WEIGHTS}.",
            "- Open-image coverage is deliberately stricter and should not be confused with IMG02 source-hosted visibility.",
            "- Duplicate image URL warnings identify repeated visual evidence that may be legitimate series reuse, source thumbnails, or a data bug; these rows require review before public rebuild.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {METRICS} ({len(metrics)} metric rows)")
    print(f"Wrote {DUPLICATES} ({len(duplicate_rows)} duplicate image URL groups)")
    print(f"Wrote {REPORT}")
    print("overall", all_row)


if __name__ == "__main__":
    main()
