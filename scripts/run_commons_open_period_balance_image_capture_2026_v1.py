#!/usr/bin/env python3
"""Capture period-balanced open Commons image records for source coverage.

This supplement targets 1930-2000 records so the active source pool is not
overconcentrated in default/contemporary dates. It stores metadata, source
links, rights evidence, and source-hosted image URLs only.
"""

from __future__ import annotations

import csv
import re
import time
from collections import Counter
from pathlib import Path

import run_commons_open_global_south_image_capture_2026_v1 as base


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

RECORDS_CSV = DATA / "capture_batch_commons_open_period_balance_image_2026_records.csv"
SUMMARY_CSV = DATA / "capture_batch_commons_open_period_balance_image_2026_source_summary.csv"
REPORT = DOCS / "COMMONS_OPEN_PERIOD_BALANCE_IMAGE_CAPTURE_2026_v1.md"

TARGET_ROWS = 90
MAX_QUERY_PAGES = 3
ACCESS_DATE = base.ACCESS_DATE
FIELDNAMES = base.FIELDNAMES

DECADES = ["1970s", "1980s", "1990s"]
OBJECT_TERMS = ["poster", "advertising", "stamp", "book cover", "magazine cover", "leaflet", "pamphlet"]
EXACT_YEARS = list(range(1970, 2001))
BROAD_PERIOD_CATEGORIES = [
    ("poster", "Category:1970s posters"),
    ("poster", "Category:1980s posters"),
    ("poster", "Category:1990s posters"),
    ("advertising", "Category:1970s advertisements"),
    ("advertising", "Category:1980s advertisements"),
    ("advertising", "Category:1990s advertisements"),
    ("stamp", "Category:1970s postage stamps"),
    ("stamp", "Category:1980s postage stamps"),
    ("stamp", "Category:1990s postage stamps"),
]


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


def existing_keys() -> tuple[set[str], set[str]]:
    ids: set[str] = set()
    image_urls: set[str] = set()
    for path in sorted(DATA.glob("capture_batch_*_records.csv")):
        if path == RECORDS_CSV:
            continue
        for row in read_csv(path):
            if base.clean(row.get("source_identifier")):
                ids.add(base.clean(row.get("source_identifier")))
            if base.clean(row.get("source_record_url")):
                ids.add(base.clean(row.get("source_record_url")))
            if base.clean(row.get("image_url_detected")):
                image_urls.add(base.clean(row.get("image_url_detected")).lower())
    return ids, image_urls


def query_plan() -> list[tuple[str, str, str, str, str]]:
    plan: list[tuple[str, str, str, str, str]] = []
    seen: set[str] = set()

    def add(macro: str, country: str, object_term: str, query: str) -> None:
        if query in seen:
            return
        seen.add(query)
        direction = re.sub(r"[^a-z0-9]+", "_", f"period_{country}_{object_term}".lower()).strip("_")
        plan.append((macro, country, direction, object_term, query))

    for object_term, query in BROAD_PERIOD_CATEGORIES:
        add("_infer", "_infer", object_term, query)

    for year in EXACT_YEARS:
        for object_term in ("poster", "stamp", "advertising poster", "film poster", "book cover"):
            add("_infer", "_infer", object_term, f'"{year}" "{object_term}"')

    for macro, country, _region_term, terms in base.REGION_SEEDS:
        if country == "Pacific":
            aliases = [term for term in terms if term != "Pacific"]
        else:
            aliases = [country, *terms[:1]]
        for alias in aliases:
            for decade in DECADES:
                for object_term in OBJECT_TERMS:
                    add(macro, country, object_term, f'"{alias}" "{decade}" "{object_term}"')
    return plan


def period_ok(row: dict[str, str]) -> bool:
    try:
        year = int(float(row.get("date_end") or row.get("date_start") or "0"))
    except ValueError:
        return False
    return 1930 <= year <= 2000


def main() -> None:
    base.INFER_FALLBACK_REGION = ("Global", "period balance")
    DATA.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    seen_ids, seen_images = existing_keys()
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    query_counts: Counter[str] = Counter()
    started = time.time()
    plans = query_plan()

    for index, (macro, country, direction_name, object_term, query) in enumerate(plans, 1):
        if len(rows) >= TARGET_ROWS:
            break
        offset: int | str = ""
        pages_seen = 0
        before = len(rows)
        max_pages = 8 if country == "_infer" else MAX_QUERY_PAGES
        while pages_seen < max_pages and len(rows) < TARGET_ROWS:
            url = base.search_url(query, offset=offset)
            try:
                payload = base.fetch_json(url)
            except Exception as exc:  # noqa: BLE001
                failures.append({"query": query, "error": type(exc).__name__, "detail": base.clean(str(exc), max_chars=180)})
                break
            time.sleep(base.REQUEST_DELAY_SECONDS)
            pages = list((payload.get("query", {}).get("pages") or {}).values())
            if not pages:
                break
            for page in sorted(pages, key=lambda item: item.get("index", 9999)):
                row = base.row_from_page(page, macro, country, direction_name, object_term, url)
                if not row or not period_ok(row):
                    continue
                source_key = row["source_identifier"] or row["source_record_url"]
                image_key = row["image_url_detected"].lower()
                if source_key in seen_ids or image_key in seen_images:
                    continue
                row["direction_id"] = "CPB2026"
                row["source_id"] = "SRC-COMMONS-PERIOD-BALANCE-2026"
                row["source_object_type"] = f"period-balanced open image record; {object_term}"
                seen_ids.add(source_key)
                seen_images.add(image_key)
                rows.append(row)
                query_counts[row["source_place_text"]] += 1
                if len(rows) >= TARGET_ROWS:
                    break
            if "continue" not in payload:
                break
            cont = payload.get("continue", {})
            offset = base.clean(cont.get("gcmcontinue")) if query.startswith("Category:") else int(cont.get("gsroffset", int(offset or 0) + base.SEARCH_LIMIT))
            if not offset:
                break
            pages_seen += 1
        if index % 10 == 0 or len(rows) > before or len(rows) >= TARGET_ROWS:
            print(f"period_query_progress={index}/{len(plans)} rows={len(rows)} added={len(rows)-before} failures={len(failures)}", flush=True)

    rows.sort(key=lambda row: (row["date_start"], row["source_place_text"], row["source_title"]))
    for index, row in enumerate(rows, 1):
        row["capture_id"] = f"CPB2026R{index:04d}"

    write_csv(RECORDS_CSV, rows, FIELDNAMES)
    by_source = Counter(row["source_name"] for row in rows)
    summary_rows = [
        {
            "source_name": source,
            "captured_records": str(count),
            "image_states": "IMG03:" + str(count),
            "notes": "Period-balanced Commons open-license metadata; no image binary downloaded",
        }
        for source, count in sorted(by_source.items())
    ]
    write_csv(SUMMARY_CSV, summary_rows, ["source_name", "captured_records", "image_states", "notes"])

    period_counts = Counter(
        "1930_1970" if int(row["date_end"]) <= 1970 else "1970_2000"
        for row in rows
    )
    macro_counts = Counter(row["source_place_text"].split(" / ")[0] for row in rows)
    lines = [
        "# Commons Open Period Balance Image Capture 2026 v1",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        "Scope: Commons open-license source pages with explicit 1930-2000 date evidence. Metadata/source links/source-hosted image URLs only.",
        "",
        "## Metrics",
        "",
        f"- Records captured: {len(rows)}",
        f"- Distinct active source names: {len(by_source)}",
        f"- Query failures: {len(failures)}",
        f"- Runtime seconds: {time.time() - started:.1f}",
        "",
        "## Period Distribution",
        "",
    ]
    for period, count in period_counts.most_common():
        lines.append(f"- {period}: {count}")
    lines.extend(["", "## Macro-region Distribution", ""])
    for macro, count in macro_counts.most_common():
        lines.append(f"- {macro}: {count}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No image binaries were downloaded.",
            "- No raw API payloads, cookies, browser sessions, screenshots, or local image files were saved.",
            "- `IMG03` is assigned only when Commons extmetadata exposes open-license evidence.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"records={len(rows)}")
    print(f"distinct_source_names={len(by_source)}")
    print("periods=" + ",".join(f"{key}:{value}" for key, value in period_counts.most_common()))
    print("macro_regions=" + ",".join(f"{key}:{value}" for key, value in macro_counts.most_common()))
    print(f"wrote {RECORDS_CSV.relative_to(ROOT)}")
    print(f"wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
