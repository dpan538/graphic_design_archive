#!/usr/bin/env python3
"""Capture region-focused contemporary Commons open records for research depth.

This batch targets the 2000-2026 internet/design-diversification period while
keeping a small pre-1930 continuity lane. It stores metadata, source links,
rights evidence, source-derived text, and source-hosted image URLs only. It does
not download image binaries, thumbnails, screenshots, raw API payloads, cookies,
or browser sessions.
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

RECORDS_CSV = DATA / "capture_batch_commons_open_contemporary_region_research_2026_records.csv"
SUMMARY_CSV = DATA / "capture_batch_commons_open_contemporary_region_research_2026_source_summary.csv"
REPORT = DOCS / "COMMONS_OPEN_CONTEMPORARY_REGION_RESEARCH_CAPTURE_2026_v1.md"

ACCESS_DATE = base.ACCESS_DATE
FIELDNAMES = base.FIELDNAMES

TARGET_ROWS = 120
CONTEMPORARY_MIN_ROWS = 95
PRE1930_MAX_ROWS = 20
MAX_QUERIES = 180
SEARCH_LIMIT = 50
MAX_SEARCH_PAGES = 2
DEEP_SEARCH_PAGES = 4
CATEGORY_SEARCH_PAGES = 2
REQUEST_DELAY_SECONDS = 0.15

CONTEMPORARY_YEARS = list(range(2026, 2000, -1))
PRE1930_YEARS = list(range(1929, 1829, -1))

CONTEMPORARY_TERMS = [
    "poster",
    "graphic design",
    "typography",
    "festival poster",
    "exhibition poster",
    "advertising poster",
    "film poster",
    "book cover",
    "magazine cover",
    "visual communication",
    "campaign poster",
]

PRE1930_TERMS = [
    "poster",
    "advertisement",
    "advertising",
    "newspaper",
    "book cover",
    "magazine cover",
    "stamp",
    "label",
]

CONTEMPORARY_CATEGORY_QUERIES = [
    ("_infer", "_infer", "poster", "Category:2000s posters"),
    ("_infer", "_infer", "poster", "Category:2010s posters"),
    ("_infer", "_infer", "poster", "Category:2020s posters"),
    ("_infer", "_infer", "poster", "Category:2000s film posters"),
    ("_infer", "_infer", "poster", "Category:2010s film posters"),
    ("_infer", "_infer", "poster", "Category:2020s film posters"),
    ("_infer", "_infer", "advertising", "Category:2000s advertisements"),
    ("_infer", "_infer", "advertising", "Category:2010s advertisements"),
    ("_infer", "_infer", "advertising", "Category:2020s advertisements"),
    ("_infer", "_infer", "book cover", "Category:2000s book covers"),
    ("_infer", "_infer", "book cover", "Category:2010s book covers"),
    ("_infer", "_infer", "book cover", "Category:2020s book covers"),
    ("Latin America", "Mexico", "poster", "Category:Posters of Mexico"),
    ("Latin America", "Brazil", "poster", "Category:Posters of Brazil"),
    ("Latin America", "Argentina", "poster", "Category:Posters of Argentina"),
    ("Latin America", "Chile", "poster", "Category:Posters of Chile"),
    ("Africa", "South Africa", "poster", "Category:Posters of South Africa"),
    ("Africa", "Nigeria", "poster", "Category:Posters of Nigeria"),
    ("South Asia", "India", "poster", "Category:Posters of Bollywood films"),
    ("Southeast Asia", "Philippines", "poster", "Category:Posters of the Philippines"),
    ("Middle East and North Africa", "Palestine", "poster", "Category:Pro-Palestinian posters"),
    ("Middle East and North Africa", "Turkey", "poster", "Category:Posters of Turkey"),
    ("East Asia", "China", "poster", "Category:Chinese propaganda posters"),
    ("Eastern Europe", "Ukraine", "poster", "Category:Posters of Ukraine"),
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
            source_identifier = base.clean(row.get("source_identifier"))
            source_record_url = base.clean(row.get("source_record_url"))
            image_url = base.clean(row.get("image_url_detected"))
            if source_identifier:
                ids.add(source_identifier)
            if source_record_url:
                ids.add(source_record_url)
            if image_url:
                image_urls.add(image_url.lower())
    return ids, image_urls


def add_query(
    plan: list[tuple[str, str, str, str, str, str]],
    seen: set[str],
    phase: str,
    macro: str,
    country: str,
    object_term: str,
    query: str,
) -> None:
    if query in seen:
        return
    seen.add(query)
    direction = re.sub(r"[^a-z0-9]+", "_", f"commons_{phase}_{country}_{object_term}".lower()).strip("_")
    plan.append((phase, macro, country, direction, object_term, query))


def query_plan() -> list[tuple[str, str, str, str, str, str]]:
    plan: list[tuple[str, str, str, str, str, str]] = []
    seen: set[str] = set()

    for macro, country, object_term, query in CONTEMPORARY_CATEGORY_QUERIES:
        add_query(plan, seen, "contemporary_category", macro, country, object_term, query)

    for macro, country, region_term, terms in base.REGION_SEEDS:
        aliases = [country, region_term, *terms[:2]]
        aliases = [alias for alias in aliases if alias and alias != "Pacific"]
        if country == "Pacific":
            aliases = [alias for alias in terms if alias and alias != "Pacific"]
        for alias in aliases[:3]:
            for object_term in CONTEMPORARY_TERMS:
                add_query(
                    plan,
                    seen,
                    "contemporary_deep",
                    macro,
                    country if country != "Pacific" else alias,
                    object_term,
                    f'"{alias}" "{object_term}"',
                )
        for year in CONTEMPORARY_YEARS:
            for alias in aliases[:3]:
                for object_term in CONTEMPORARY_TERMS:
                    add_query(
                        plan,
                        seen,
                        "contemporary",
                        macro,
                        country if country != "Pacific" else alias,
                        object_term,
                        f'"{alias}" "{year}" "{object_term}"',
                    )

    for macro, country, region_term, terms in base.REGION_SEEDS:
        aliases = [country, region_term, *terms[:1]]
        aliases = [alias for alias in aliases if alias and alias != "Pacific"]
        if country == "Pacific":
            aliases = [alias for alias in terms if alias and alias != "Pacific"]
        for year in PRE1930_YEARS:
            for alias in aliases[:2]:
                for object_term in PRE1930_TERMS:
                    add_query(
                        plan,
                        seen,
                        "pre1930",
                        macro,
                        country if country != "Pacific" else alias,
                        object_term,
                        f'"{alias}" "{year}" "{object_term}"',
                    )
    return plan


def period_band(row: dict[str, str]) -> str:
    year = int(float(row.get("date_end") or row.get("date_start") or "0"))
    if year <= 1930:
        return "pre_1930"
    if year <= 1970:
        return "1930_1970"
    if year <= 2000:
        return "1970_2000"
    return "2000_2026"


def row_phase(row: dict[str, str]) -> str:
    return "pre1930" if period_band(row) == "pre_1930" else "contemporary"


def should_keep_row(row: dict[str, str], phase_counts: Counter[str]) -> bool:
    phase = row_phase(row)
    if phase == "pre1930":
        return phase_counts["pre1930"] < PRE1930_MAX_ROWS
    if phase == "contemporary":
        return True
    return False


def target_met(phase_counts: Counter[str], rows: list[dict[str, str]]) -> bool:
    return len(rows) >= TARGET_ROWS and phase_counts["contemporary"] >= CONTEMPORARY_MIN_ROWS


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    seen_ids, seen_images = existing_keys()
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    phase_counts: Counter[str] = Counter()
    query_counts: Counter[str] = Counter()
    started = time.time()

    plans = query_plan()
    for index, (phase, macro, country, direction_name, object_term, query) in enumerate(plans, 1):
        if index > MAX_QUERIES:
            failures.append(
                {
                    "query": "query_plan_limit",
                    "error": "QueryPlanLimitReached",
                    "detail": f"Stopped after {MAX_QUERIES} queries for bounded calibration capture.",
                }
            )
            break
        if target_met(phase_counts, rows):
            break
        if phase == "pre1930" and phase_counts["pre1930"] >= PRE1930_MAX_ROWS:
            continue
        offset: int | str = ""
        pages_seen = 0
        before = len(rows)
        max_pages = CATEGORY_SEARCH_PAGES if query.startswith("Category:") else DEEP_SEARCH_PAGES if phase == "contemporary_deep" else MAX_SEARCH_PAGES
        while pages_seen < max_pages and not target_met(phase_counts, rows):
            url = base.search_url(query, offset=offset, limit=SEARCH_LIMIT)
            try:
                payload = base.fetch_json(url)
            except Exception as exc:  # noqa: BLE001
                failures.append({"query": query, "error": type(exc).__name__, "detail": base.clean(str(exc), max_chars=180)})
                break
            time.sleep(REQUEST_DELAY_SECONDS)
            pages = list((payload.get("query", {}).get("pages") or {}).values())
            if not pages:
                break
            for page in sorted(pages, key=lambda item: item.get("index", 9999)):
                row = base.row_from_page(page, macro, country, direction_name, object_term, url)
                if not row or not should_keep_row(row, phase_counts):
                    continue
                source_key = row["source_identifier"] or row["source_record_url"]
                image_key = row["image_url_detected"].lower()
                if source_key in seen_ids or image_key in seen_images:
                    continue
                row["direction_id"] = "CCR2026"
                row["source_id"] = "SRC-COMMONS-CONTEMPORARY-REGION-RESEARCH-2026"
                row["source_object_type"] = f"region-focused open image record; {object_term}"
                row["historical_context_note"] = base.clean(
                    f"This record supports a region-focused research pass for {row['source_place_text']} and helps rebalance contemporary or early-continuity visual communication coverage.",
                    max_chars=700,
                )
                row["classification_rationale"] = base.clean(
                    "Selected by region/year/object query, open-license extmetadata, visual-communication relevance, duplicate exclusion, and source-derived text availability. Impact priority remains internal triage only.",
                    max_chars=700,
                )
                seen_ids.add(source_key)
                seen_images.add(image_key)
                rows.append(row)
                phase_counts[row_phase(row)] += 1
                query_counts[row["source_place_text"]] += 1
                if target_met(phase_counts, rows):
                    break
            if "continue" not in payload:
                break
            cont = payload.get("continue", {})
            offset = base.clean(cont.get("gcmcontinue")) if query.startswith("Category:") else int(cont.get("gsroffset", int(offset or 0) + SEARCH_LIMIT))
            if not offset:
                break
            pages_seen += 1
            if pages_seen and pages_seen % 3 == 0:
                print(
                    f"  page_progress query={index}/{len(plans)} pages={pages_seen}/{max_pages} "
                    f"rows={len(rows)} contemporary={phase_counts['contemporary']} pre1930={phase_counts['pre1930']}",
                    flush=True,
                )
        if index % 20 == 0 or len(rows) > before or target_met(phase_counts, rows):
            print(
                f"contemporary_region_query_progress={index}/{len(plans)} rows={len(rows)} "
                f"contemporary={phase_counts['contemporary']} pre1930={phase_counts['pre1930']} "
                f"added={len(rows)-before} failures={len(failures)}",
                flush=True,
            )

    rows.sort(key=lambda row: (period_band(row), row["source_place_text"], row["date_start"], row["source_title"]))
    for index, row in enumerate(rows, 1):
        row["capture_id"] = f"CCR2026R{index:04d}"

    write_csv(RECORDS_CSV, rows, FIELDNAMES)
    by_source = Counter(row["source_name"] for row in rows)
    summary_rows = [
        {
            "source_name": source,
            "captured_records": str(count),
            "image_states": "IMG03:" + str(count),
            "notes": "Region-focused contemporary/pre-1930 Commons metadata; no image binary downloaded",
        }
        for source, count in sorted(by_source.items())
    ]
    write_csv(SUMMARY_CSV, summary_rows, ["source_name", "captured_records", "image_states", "notes"])

    period_counts = Counter(period_band(row) for row in rows)
    macro_counts = Counter(row["source_place_text"].split(" / ")[0] for row in rows)
    country_counts = Counter(row["source_place_text"] for row in rows)
    text_lengths = [
        len(" ".join([row["source_description"], row["source_notes"], row["source_subjects"], row["ocr_or_excerpt"]]).strip())
        for row in rows
    ]
    current_year_count = sum(1 for row in rows if row.get("date_start") == "2026" or row.get("date_end") == "2026")
    lines = [
        "# Commons Open Contemporary Region Research Capture 2026 v1",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        "Scope: region-focused Commons open-license item records for contemporary visual communication, plus a capped pre-1930 continuity lane. Metadata/source links/source-hosted image URLs only.",
        "",
        "## Metrics",
        "",
        f"- Records captured: {len(rows)}",
        f"- Distinct active source names: {len(by_source)}",
        f"- Contemporary rows: {phase_counts['contemporary']}",
        f"- Pre-1930 rows: {phase_counts['pre1930']}",
        f"- Explicit 2026 rows: {current_year_count}",
        f"- Image states: IMG03 only",
        f"- Query failures: {len(failures)}",
        f"- Runtime seconds: {time.time() - started:.1f}",
        f"- Minimum source-derived text length: {min(text_lengths) if text_lengths else 0}",
        f"- Median source-derived text length: {sorted(text_lengths)[len(text_lengths)//2] if text_lengths else 0}",
        "",
        "## Period Distribution",
        "",
    ]
    for period, count in period_counts.most_common():
        lines.append(f"- {period}: {count}")
    lines.extend(["", "## Macro-region Distribution", ""])
    for macro_name, count in macro_counts.most_common():
        lines.append(f"- {macro_name}: {count}")
    lines.extend(["", "## Top Country/Region Buckets", ""])
    for bucket, count in country_counts.most_common(30):
        lines.append(f"- {bucket}: {count}")
    lines.extend(["", "## Query Failures", ""])
    for failure in failures[:25]:
        lines.append(f"- {failure.get('error')}: {failure.get('query')} ({failure.get('detail', '')})")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No image binaries were downloaded.",
            "- No raw API payloads, cookies, browser sessions, screenshots, or local image files were saved.",
            "- `IMG03` is assigned only when Commons extmetadata exposes open-license evidence.",
            "- Impact and source priority are internal triage signals only; they do not grant rights or public authority.",
            "- Commons metadata remains user-maintained and should be reviewed before final scholarly claims.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"records={len(rows)}")
    print(f"distinct_source_names={len(by_source)}")
    print(f"periods={dict(period_counts)}")
    print(f"macro_regions={dict(macro_counts)}")
    print(f"explicit_2026_rows={current_year_count}")
    print(f"failures={len(failures)}")
    print(f"wrote {RECORDS_CSV.relative_to(ROOT)}")
    print(f"wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
