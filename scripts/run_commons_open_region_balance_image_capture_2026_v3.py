#!/usr/bin/env python3
"""Capture a large region-balanced Commons open-image batch.

This is an item/image capture batch for the long release-gate push. It stores
metadata, source links, rights evidence, source-derived text, and source-hosted
image URLs only. It does not download image binaries, thumbnails, screenshots,
raw API payloads, cookies, browser sessions, or local image files.
"""

from __future__ import annotations

import csv
import re
import time
import urllib.parse
from collections import Counter
from pathlib import Path

import run_commons_open_global_south_image_capture_2026_v1 as base
import run_commons_open_region_balance_image_capture_2026_v2 as v2


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
CAPTURE_RUNS = DATA / "capture_runs"

RECORDS_CSV = DATA / "capture_batch_commons_open_region_balance_image_2026_v3_records.csv"
SUMMARY_CSV = DATA / "capture_batch_commons_open_region_balance_image_2026_v3_source_summary.csv"
QUALITY_CSV = DATA / "commons_open_region_balance_image_2026_v3_quality.csv"
REPORT = DOCS / "COMMONS_OPEN_REGION_BALANCE_IMAGE_CAPTURE_2026_v3.md"
MANIFEST = CAPTURE_RUNS / "capture_run_manifest_v1.csv"
STATE_CSV = DATA / "commons_open_region_balance_image_2026_v3_query_state.csv"

ACCESS_DATE = "2026-06-12"
base.ACCESS_DATE = ACCESS_DATE
FIELDNAMES = base.FIELDNAMES

TARGET_ROWS = 500
MAX_QUERIES = 8500
SEARCH_LIMIT = 50
CATEGORY_PAGES = 2
SEARCH_PAGES = 1
REQUEST_DELAY_SECONDS = 0.1
CHECKPOINT_EVERY_ROWS = 100
COUNTRY_CAP = 300
YEAR_CAPS = {
    2026: 140,
    2025: 260,
    2024: 260,
}
PERIOD_CAPS = {
    "pre_1930": 800,
    "1930_1970": 1200,
    "1970_2000": 1300,
    "2000_2026": 1700,
}
MACRO_CAPS = {
    "Africa": 850,
    "South Asia": 600,
    "Southeast Asia": 650,
    "Middle East and North Africa": 650,
    "Eastern Europe": 450,
    "Eastern Europe / Caucasus": 450,
    "Central Asia": 320,
    "Latin America": 800,
    "Latin America / Caribbean": 800,
    "Oceania and Pacific": 260,
    "Oceania / Pacific": 260,
    "East Asia": 420,
}
MACRO_ORDER = [
    "Africa",
    "Latin America / Caribbean",
    "South Asia",
    "Southeast Asia",
    "Middle East and North Africa",
    "Eastern Europe / Caucasus",
    "Central Asia",
    "Oceania / Pacific",
    "East Asia",
]

OBJECT_TERMS = [
    "poster",
    "political poster",
    "propaganda poster",
    "advertising poster",
    "campaign poster",
    "exhibition poster",
    "film poster",
    "travel poster",
    "book cover",
    "magazine cover",
    "postage stamp",
    "stamp",
    "packaging",
    "label",
    "brochure",
    "pamphlet",
    "leaflet",
    "typography",
    "type specimen",
]

COUNTRIES = [
    ("Africa", "Nigeria", ["Nigeria", "Nigerian"]),
    ("Africa", "Ghana", ["Ghana", "Ghanaian"]),
    ("Africa", "Kenya", ["Kenya", "Kenyan"]),
    ("Africa", "Ethiopia", ["Ethiopia", "Ethiopian"]),
    ("Africa", "Senegal", ["Senegal", "Senegalese"]),
    ("Africa", "Tanzania", ["Tanzania", "Tanzanian"]),
    ("Africa", "Morocco", ["Morocco", "Moroccan"]),
    ("Africa", "Algeria", ["Algeria", "Algerian"]),
    ("Africa", "South Africa", ["South Africa", "South African", "apartheid"]),
    ("Africa", "Egypt", ["Egypt", "Egyptian"]),
    ("Africa", "Tunisia", ["Tunisia", "Tunisian"]),
    ("Africa", "Angola", ["Angola", "Angolan"]),
    ("Africa", "Mozambique", ["Mozambique", "Mozambican"]),
    ("Africa", "Zimbabwe", ["Zimbabwe", "Zimbabwean"]),
    ("Africa", "Cameroon", ["Cameroon", "Cameroonian"]),
    ("South Asia", "Bangladesh", ["Bangladesh", "Bangladeshi"]),
    ("South Asia", "Pakistan", ["Pakistan", "Pakistani"]),
    ("South Asia", "Nepal", ["Nepal", "Nepali"]),
    ("South Asia", "Sri Lanka", ["Sri Lanka", "Sri Lankan"]),
    ("South Asia", "India", ["India", "Indian", "Bollywood"]),
    ("Southeast Asia", "Indonesia", ["Indonesia", "Indonesian"]),
    ("Southeast Asia", "Philippines", ["Philippines", "Filipino", "Philippine"]),
    ("Southeast Asia", "Vietnam", ["Vietnam", "Vietnamese"]),
    ("Southeast Asia", "Thailand", ["Thailand", "Thai"]),
    ("Southeast Asia", "Malaysia", ["Malaysia", "Malaysian"]),
    ("Southeast Asia", "Singapore", ["Singapore"]),
    ("Southeast Asia", "Cambodia", ["Cambodia", "Cambodian"]),
    ("Southeast Asia", "Laos", ["Laos", "Lao"]),
    ("Southeast Asia", "Myanmar", ["Myanmar", "Burmese"]),
    ("Middle East and North Africa", "Iran", ["Iran", "Iranian", "Persian"]),
    ("Middle East and North Africa", "Iraq", ["Iraq", "Iraqi"]),
    ("Middle East and North Africa", "Lebanon", ["Lebanon", "Lebanese"]),
    ("Middle East and North Africa", "Palestine", ["Palestine", "Palestinian"]),
    ("Middle East and North Africa", "Turkey", ["Turkey", "Turkish"]),
    ("Middle East and North Africa", "Syria", ["Syria", "Syrian"]),
    ("Middle East and North Africa", "Jordan", ["Jordan", "Jordanian"]),
    ("Eastern Europe / Caucasus", "Ukraine", ["Ukraine", "Ukrainian"]),
    ("Eastern Europe / Caucasus", "Georgia", ["Georgia", "Georgian"]),
    ("Eastern Europe / Caucasus", "Armenia", ["Armenia", "Armenian"]),
    ("Eastern Europe / Caucasus", "Azerbaijan", ["Azerbaijan", "Azerbaijani"]),
    ("Eastern Europe / Caucasus", "Romania", ["Romania", "Romanian"]),
    ("Eastern Europe / Caucasus", "Bulgaria", ["Bulgaria", "Bulgarian"]),
    ("Eastern Europe / Caucasus", "Serbia", ["Serbia", "Serbian"]),
    ("Eastern Europe / Caucasus", "Croatia", ["Croatia", "Croatian"]),
    ("Eastern Europe / Caucasus", "Poland", ["Poland", "Polish"]),
    ("Central Asia", "Kazakhstan", ["Kazakhstan", "Kazakh"]),
    ("Central Asia", "Uzbekistan", ["Uzbekistan", "Uzbek"]),
    ("Central Asia", "Kyrgyzstan", ["Kyrgyzstan", "Kyrgyz"]),
    ("Central Asia", "Tajikistan", ["Tajikistan", "Tajik"]),
    ("Central Asia", "Turkmenistan", ["Turkmenistan", "Turkmen"]),
    ("Latin America / Caribbean", "Mexico", ["Mexico", "Mexican", "México"]),
    ("Latin America / Caribbean", "Brazil", ["Brazil", "Brazilian", "Brasil"]),
    ("Latin America / Caribbean", "Argentina", ["Argentina", "Argentine"]),
    ("Latin America / Caribbean", "Chile", ["Chile", "Chilean"]),
    ("Latin America / Caribbean", "Colombia", ["Colombia", "Colombian"]),
    ("Latin America / Caribbean", "Peru", ["Peru", "Peruvian"]),
    ("Latin America / Caribbean", "Cuba", ["Cuba", "Cuban", "OSPAAAL"]),
    ("Latin America / Caribbean", "Uruguay", ["Uruguay", "Uruguayan"]),
    ("Latin America / Caribbean", "Venezuela", ["Venezuela", "Venezuelan"]),
    ("Latin America / Caribbean", "Bolivia", ["Bolivia", "Bolivian"]),
    ("Latin America / Caribbean", "Paraguay", ["Paraguay", "Paraguayan"]),
    ("Latin America / Caribbean", "Ecuador", ["Ecuador", "Ecuadorian"]),
    ("Latin America / Caribbean", "Dominican Republic", ["Dominican Republic", "Dominican"]),
    ("Latin America / Caribbean", "Puerto Rico", ["Puerto Rico", "Puerto Rican"]),
    ("Oceania / Pacific", "Samoa", ["Samoa", "Samoan"]),
    ("Oceania / Pacific", "Fiji", ["Fiji", "Fijian"]),
    ("Oceania / Pacific", "Papua New Guinea", ["Papua New Guinea", "Papuan"]),
    ("Oceania / Pacific", "Aotearoa New Zealand", ["New Zealand", "Aotearoa", "Māori", "Maori"]),
    ("Oceania / Pacific", "Australia / Indigenous", ["Australia", "Australian", "Aboriginal", "Torres Strait"]),
    ("East Asia", "Taiwan", ["Taiwan", "Taiwanese"]),
    ("East Asia", "Korea", ["Korea", "Korean", "South Korea"]),
    ("East Asia", "China", ["China", "Chinese", "Shanghai"]),
    ("East Asia", "Hong Kong", ["Hong Kong"]),
]

CATEGORY_PATTERNS = [
    ("poster", "Category:Posters of {country}"),
    ("poster", "Category:Political posters of {country}"),
    ("poster", "Category:Propaganda posters of {country}"),
    ("poster", "Category:Film posters of {country}"),
    ("poster", "Category:Travel posters of {country}"),
    ("advertising poster", "Category:Advertising posters of {country}"),
    ("postage stamp", "Category:Postage stamps of {country}"),
    ("stamp", "Category:Stamps of {country}"),
    ("book cover", "Category:Book covers of {country}"),
    ("magazine cover", "Category:Magazine covers of {country}"),
    ("packaging", "Category:Packaging of {country}"),
    ("label", "Category:Labels of {country}"),
    ("brochure", "Category:Brochures of {country}"),
    ("pamphlet", "Category:Pamphlets of {country}"),
]

EXACT_CATEGORIES = [
    ("Middle East and North Africa", "Palestine", "poster", "Category:Pro-Palestinian posters"),
    ("Latin America / Caribbean", "Cuba", "poster", "Category:OSPAAAL posters"),
    ("Africa", "South Africa", "poster", "Category:Anti-apartheid posters"),
    ("Africa", "South Africa", "poster", "Category:Posters of apartheid"),
    ("East Asia", "China", "poster", "Category:Chinese propaganda posters"),
    ("East Asia", "Taiwan", "poster", "Category:Taiwanese political posters"),
    ("South Asia", "India", "poster", "Category:Posters of Bollywood films"),
    ("Southeast Asia", "Philippines", "poster", "Category:Posters of the Philippines"),
    ("Latin America / Caribbean", "Mexico", "poster", "Category:Posters of Mexico"),
    ("Latin America / Caribbean", "Brazil", "poster", "Category:Posters of Brazil"),
]

BROAD_CATEGORIES = [
    ("_infer", "_infer", "poster", "Category:Political posters"),
    ("_infer", "_infer", "poster", "Category:Propaganda posters"),
    ("_infer", "_infer", "poster", "Category:Film posters"),
    ("_infer", "_infer", "poster", "Category:Travel posters"),
    ("_infer", "_infer", "advertising poster", "Category:Advertising posters"),
    ("_infer", "_infer", "postage stamp", "Category:Postage stamps"),
    ("_infer", "_infer", "book cover", "Category:Book covers"),
    ("_infer", "_infer", "magazine cover", "Category:Magazine covers"),
    ("_infer", "_infer", "packaging", "Category:Packaging"),
    ("_infer", "_infer", "label", "Category:Labels"),
    ("_infer", "_infer", "brochure", "Category:Brochures"),
]

BROAD_YEAR_OBJECT_TERMS = [
    "poster",
    "political poster",
    "propaganda poster",
    "film poster",
    "book cover",
    "postage stamp",
    "travel poster",
]

LOW_QUALITY_SOURCE_TERMS = (
    "copyright status of such a calendar page",
    "copyright status of such calendar page",
    "copyright status is unknown",
    "rights status is unknown",
    "unknown copyright status",
)


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


def existing_keys(current_rows: list[dict[str, str]]) -> tuple[set[str], set[str]]:
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
    for row in current_rows:
        if row.get("source_identifier"):
            ids.add(row["source_identifier"])
        if row.get("source_record_url"):
            ids.add(row["source_record_url"])
        if row.get("image_url_detected"):
            image_urls.add(row["image_url_detected"].lower())
    return ids, image_urls


def ordered_countries() -> list[tuple[str, str, list[str]]]:
    by_macro: dict[str, list[tuple[str, str, list[str]]]] = {macro: [] for macro in MACRO_ORDER}
    for row in COUNTRIES:
        by_macro.setdefault(row[0], []).append(row)
    ordered: list[tuple[str, str, list[str]]] = []
    while any(by_macro.values()):
        for macro in MACRO_ORDER:
            if by_macro.get(macro):
                ordered.append(by_macro[macro].pop(0))
    return ordered


def add_plan(
    plan: list[tuple[str, str, str, str, str]],
    seen: set[str],
    macro: str,
    country: str,
    object_term: str,
    query: str,
) -> None:
    if query in seen:
        return
    seen.add(query)
    direction = re.sub(r"[^a-z0-9]+", "_", f"region_balance_v3_{country}_{object_term}".lower()).strip("_")
    plan.append((macro, country, direction, object_term, query))


def query_plan() -> list[tuple[str, str, str, str, str]]:
    plan: list[tuple[str, str, str, str, str]] = []
    seen: set[str] = set()
    country_rows = ordered_countries()

    for year in range(2026, 1829, -1):
        for object_term in BROAD_YEAR_OBJECT_TERMS:
            add_plan(plan, seen, "_infer", "_infer", object_term, f'"{year}" "{object_term}"')
    for macro, country, aliases in country_rows:
        for alias in aliases[:3]:
            for object_term in OBJECT_TERMS:
                add_plan(plan, seen, macro, country, object_term, f'"{alias}" "{object_term}"')
    for macro, country, aliases in country_rows:
        for alias in aliases[:2]:
            for year in range(2026, 1999, -1):
                for object_term in (
                    "poster",
                    "advertising poster",
                    "film poster",
                    "book cover",
                    "magazine cover",
                    "typography",
                ):
                    add_plan(plan, seen, macro, country, object_term, f'"{alias}" "{year}" "{object_term}"')
            for year in range(1999, 1969, -1):
                for object_term in ("poster", "advertising poster", "film poster", "postage stamp", "book cover"):
                    add_plan(plan, seen, macro, country, object_term, f'"{alias}" "{year}" "{object_term}"')
            for year in range(1969, 1929, -1):
                for object_term in ("poster", "advertising poster", "film poster", "postage stamp"):
                    add_plan(plan, seen, macro, country, object_term, f'"{alias}" "{year}" "{object_term}"')
            for year in range(1929, 1829, -1):
                for object_term in ("poster", "advertising poster", "postage stamp", "book cover"):
                    add_plan(plan, seen, macro, country, object_term, f'"{alias}" "{year}" "{object_term}"')
    for macro, country, object_term, query in EXACT_CATEGORIES:
        add_plan(plan, seen, macro, country, object_term, query)
    for macro, country, aliases in country_rows:
        for object_term, pattern in CATEGORY_PATTERNS:
            add_plan(plan, seen, macro, country, object_term, pattern.format(country=country))
    for macro, country, object_term, query in BROAD_CATEGORIES:
        add_plan(plan, seen, macro, country, object_term, query)
    return plan


def completed_query_keys(max_rows_after: int) -> set[str]:
    completed: set[str] = set()
    for row in read_csv(STATE_CSV):
        try:
            rows_after = int(row.get("rows_after") or "0")
        except ValueError:
            rows_after = 0
        if rows_after > max_rows_after:
            continue
        if row.get("status") in {"completed", "empty"} and row.get("query"):
            completed.add(row["query"])
    return completed


def row_query_keys(rows: list[dict[str, str]]) -> set[str]:
    keys: set[str] = set()
    for row in rows:
        parsed = urllib.parse.urlparse(row.get("source_api_url", ""))
        params = urllib.parse.parse_qs(parsed.query)
        query = params.get("gsrsearch", [""])[0] or params.get("gcmtitle", [""])[0]
        if query:
            keys.add(query)
    return keys


def append_query_state(row: dict[str, str]) -> None:
    fields = [
        "query_index",
        "macro",
        "country",
        "object_term",
        "query",
        "status",
        "added",
        "failures_delta",
        "rejects_delta",
        "rows_after",
        "elapsed_seconds",
    ]
    rows = read_csv(STATE_CSV)
    rows = [current for current in rows if current.get("query") != row.get("query")]
    rows.append(row)
    write_csv(STATE_CSV, rows, fields)


def v3_quality_gate(row: dict[str, str], object_term: str | None = None) -> tuple[bool, str]:
    title = row.get("source_title", "").lower()
    description = row.get("source_description", "").lower()
    notes = row.get("source_notes", "").lower()
    blob = " ".join([title, description, notes])
    if any(term in blob for term in LOW_QUALITY_SOURCE_TERMS):
        return False, "rights_unclear_source_text"
    if object_term == "advertising poster" and "calendar page" in blob and "stapling to an advertising poster" in blob:
        return False, "weak_advertising_poster_relation"
    if "file:" in title and title.endswith((".svg", ".pdf", ".djvu")):
        return False, "non_raster_source"
    return True, "ok"


def period_band(row: dict[str, str]) -> str:
    try:
        year = int(float(row.get("date_end") or row.get("date_start") or "0"))
    except ValueError:
        return "undated"
    if year <= 1930:
        return "pre_1930"
    if year <= 1970:
        return "1930_1970"
    if year <= 2000:
        return "1970_2000"
    return "2000_2026"


def row_year(row: dict[str, str]) -> int:
    try:
        return int(float(row.get("date_end") or row.get("date_start") or "0"))
    except ValueError:
        return 0


def macro_key(row: dict[str, str]) -> str:
    return row["source_place_text"].split(" / ")[0]


def within_distribution_caps(
    row: dict[str, str],
    macro_counts: Counter[str],
    country_counts: Counter[str],
    period_counts: Counter[str],
    year_counts: Counter[int],
) -> tuple[bool, str]:
    country = row["source_place_text"]
    macro = macro_key(row)
    period = period_band(row)
    year = row_year(row)
    if country_counts[country] >= COUNTRY_CAP:
        return False, "country_cap"
    if macro_counts[macro] >= MACRO_CAPS.get(macro, TARGET_ROWS):
        return False, "macro_cap"
    if period_counts[period] >= PERIOD_CAPS.get(period, TARGET_ROWS):
        return False, "period_cap"
    if year in YEAR_CAPS and year_counts[year] >= YEAR_CAPS[year]:
        return False, "year_cap"
    return True, "ok"


def reseed_counters(rows: list[dict[str, str]]) -> tuple[Counter[str], Counter[str], Counter[str], Counter[int]]:
    macro_counts: Counter[str] = Counter()
    country_counts: Counter[str] = Counter()
    period_counts: Counter[str] = Counter()
    year_counts: Counter[int] = Counter()
    for row in rows:
        country_counts[row["source_place_text"]] += 1
        macro_counts[macro_key(row)] += 1
        period_counts[period_band(row)] += 1
        year_counts[row_year(row)] += 1
    return macro_counts, country_counts, period_counts, year_counts


def update_manifest(records_count: int, active_sources: int, image_counts: Counter[str]) -> None:
    CAPTURE_RUNS.mkdir(parents=True, exist_ok=True)
    fields = [
        "run_id",
        "records_csv",
        "records_count",
        "active_source_count",
        "image_state_counts",
        "summary_csv",
        "summary_exists",
        "report_md",
        "report_exists",
        "raw_dir",
        "raw_dir_exists",
        "raw_commit_policy",
        "included_in_public_rebuild",
        "stage",
        "notes",
    ]
    rows = read_csv(MANIFEST)
    run_id = "commons_open_region_balance_image_2026_v3"
    rows = [row for row in rows if row.get("run_id") != run_id]
    rows.append(
        {
            "run_id": run_id,
            "records_csv": str(RECORDS_CSV.relative_to(ROOT)),
            "records_count": str(records_count),
            "active_source_count": str(active_sources),
            "image_state_counts": ";".join(f"{key}:{value}" for key, value in sorted(image_counts.items())),
            "summary_csv": str(SUMMARY_CSV.relative_to(ROOT)),
            "summary_exists": "true",
            "report_md": str(REPORT.relative_to(ROOT)),
            "report_exists": "true",
            "raw_dir": "",
            "raw_dir_exists": "false",
            "raw_commit_policy": "not_present",
            "included_in_public_rebuild": "true" if records_count > 0 else "false",
            "stage": "item_image_capture" if records_count > 0 else "empty_or_pending",
            "notes": "Large region-balanced Commons open image capture; strict source-derived graphic filter; no image binaries or raw payloads saved.",
        }
    )
    write_csv(MANIFEST, rows, fields)


def write_outputs(
    rows: list[dict[str, str]],
    failures: list[dict[str, str]],
    rejects: Counter[str],
    started: float,
    *,
    final: bool,
) -> None:
    rows.sort(key=lambda row: (row["source_place_text"], row["date_start"], row["source_title"]))
    for index, row in enumerate(rows, 1):
        row["capture_id"] = f"CRB2026V3R{index:05d}"
    write_csv(RECORDS_CSV, rows, FIELDNAMES)

    by_source = Counter(row["source_name"] for row in rows)
    image_counts = Counter(row["image_presence_code"] for row in rows)
    summary_rows = [
        {
            "source_name": source,
            "captured_records": str(count),
            "image_states": "IMG03:" + str(count),
            "notes": "Region-balanced Commons open-license metadata; no image binary downloaded",
        }
        for source, count in sorted(by_source.items())
    ]
    write_csv(SUMMARY_CSV, summary_rows, ["source_name", "captured_records", "image_states", "notes"])

    period_counts = Counter(period_band(row) for row in rows)
    macro_counts = Counter(macro_key(row) for row in rows)
    country_counts = Counter(row["source_place_text"] for row in rows)
    year_counts = Counter(row_year(row) for row in rows)
    text_lengths = [
        len(" ".join([row["source_description"], row["source_notes"], row["source_subjects"], row["ocr_or_excerpt"]]).strip())
        for row in rows
    ]
    quality_rows = [
        {"metric": "records_captured", "value": str(len(rows))},
        {"metric": "distinct_active_source_names", "value": str(len(by_source))},
        {"metric": "query_failures", "value": str(len(failures))},
        {"metric": "target_rows", "value": str(TARGET_ROWS)},
        {"metric": "target_met", "value": "true" if len(rows) >= TARGET_ROWS else "false"},
        {"metric": "minimum_source_derived_text_length", "value": str(min(text_lengths) if text_lengths else 0)},
        {"metric": "median_source_derived_text_length", "value": str(sorted(text_lengths)[len(text_lengths) // 2] if text_lengths else 0)},
        {"metric": "year_2026_count", "value": str(year_counts.get(2026, 0))},
        {"metric": "year_2026_rate", "value": f"{(year_counts.get(2026, 0) / len(rows) * 100):.2f}" if rows else "0.00"},
    ]
    for key, value in sorted(image_counts.items()):
        quality_rows.append({"metric": f"image_state:{key}", "value": str(value)})
    for key, value in period_counts.most_common():
        quality_rows.append({"metric": f"period:{key}", "value": str(value)})
    for key, value in macro_counts.most_common():
        quality_rows.append({"metric": f"macro_region:{key}", "value": str(value)})
    for key, value in rejects.most_common():
        quality_rows.append({"metric": f"reject:{key}", "value": str(value)})
    write_csv(QUALITY_CSV, quality_rows, ["metric", "value"])

    lines = [
        "# Commons Open Region Balance Image Capture 2026 v3",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        "Scope: large region-balanced Commons open-license source pages with explicit object-year evidence and strict source-derived graphic-object filtering. Metadata/source links/source-hosted image URLs only.",
        "",
        "## Metrics",
        "",
        f"- Records captured: {len(rows)}",
        f"- Target rows: {TARGET_ROWS}",
        f"- Target met: {'yes' if len(rows) >= TARGET_ROWS else 'no'}",
        f"- Distinct active source names: {len(by_source)}",
        f"- Image states: {', '.join(f'{key}:{value}' for key, value in sorted(image_counts.items())) or 'none'}",
        f"- Query failures: {len(failures)}",
        f"- Runtime seconds: {time.time() - started:.1f}",
        f"- Minimum source-derived text length: {min(text_lengths) if text_lengths else 0}",
        f"- Median source-derived text length: {sorted(text_lengths)[len(text_lengths)//2] if text_lengths else 0}",
        f"- 2026 count/rate: {year_counts.get(2026, 0)} / {quality_rows[8]['value']}%",
        "",
        "## Period Distribution",
        "",
    ]
    for period, count in period_counts.most_common():
        lines.append(f"- {period}: {count}")
    lines.extend(["", "## Macro-region Distribution", ""])
    for macro, count in macro_counts.most_common():
        lines.append(f"- {macro}: {count}")
    lines.extend(["", "## Top Country/Region Buckets", ""])
    for country, count in country_counts.most_common(45):
        lines.append(f"- {country}: {count}")
    lines.extend(["", "## Top Years", ""])
    for year, count in year_counts.most_common(25):
        lines.append(f"- {year}: {count}")
    lines.extend(["", "## Filter Diagnostics", ""])
    for key, value in rejects.most_common(20):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Query Failures", ""])
    if failures:
        for failure in failures[:30]:
            lines.append(f"- {failure.get('error')}: {failure.get('query')} ({failure.get('detail', '')})")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No image binaries were downloaded.",
            "- No raw API payloads, cookies, browser sessions, screenshots, thumbnails, or local image files were saved.",
            "- `IMG03` is assigned only when Commons extmetadata exposes open-license evidence.",
            "- The strict relevance filter uses source-derived title, Commons description, source notes, and source categories only.",
            "- Impact and source priority are internal triage only.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if final:
        update_manifest(len(rows), len(by_source), image_counts)


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = read_csv(RECORDS_CSV)
    pruned_rows = 0
    if rows:
        kept_rows: list[dict[str, str]] = []
        for row in rows:
            ok, _reason = v3_quality_gate(row)
            if ok:
                kept_rows.append(row)
            else:
                pruned_rows += 1
        rows = kept_rows
    failures: list[dict[str, str]] = []
    rejects: Counter[str] = Counter()
    if pruned_rows:
        rejects["resume_pruned_low_quality"] = pruned_rows
    seen_ids, seen_images = existing_keys(rows)
    macro_counts, country_counts, period_counts, year_counts = reseed_counters(rows)
    started = time.time()
    plans = query_plan()
    completed = completed_query_keys(len(rows))
    completed.update(row_query_keys(rows))
    last_checkpoint_rows = len(rows)
    base.INFER_FALLBACK_REGION = None

    print(
        f"resume_rows={len(rows)} pruned={pruned_rows} target={TARGET_ROWS} query_plan={len(plans)} completed_queries={len(completed)}",
        flush=True,
    )
    for index, (macro, country, direction_name, object_term, query) in enumerate(plans, 1):
        if len(rows) >= TARGET_ROWS:
            break
        if query in completed:
            continue
        if index > MAX_QUERIES:
            failures.append({"query": "query_plan_limit", "error": "QueryPlanLimitReached", "detail": str(MAX_QUERIES)})
            break
        offset: int | str = ""
        pages_seen = 0
        before = len(rows)
        failures_before = len(failures)
        rejects_before = sum(rejects.values())
        had_pages = False
        max_pages = CATEGORY_PAGES if query.startswith("Category:") else SEARCH_PAGES
        while pages_seen < max_pages and len(rows) < TARGET_ROWS:
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
            had_pages = True
            for page in sorted(pages, key=lambda item: item.get("index", 9999)):
                row = base.row_from_page(page, macro, country, direction_name, object_term, url)
                if not row:
                    rejects["base_filter"] += 1
                    continue
                ok, reason = v2.strong_relevance(row, object_term)
                if not ok:
                    rejects[reason] += 1
                    continue
                ok, reason = v3_quality_gate(row, object_term)
                if not ok:
                    rejects[reason] += 1
                    continue
                source_key = row["source_identifier"] or row["source_record_url"]
                image_key = row["image_url_detected"].lower()
                if source_key in seen_ids or image_key in seen_images:
                    rejects["duplicate"] += 1
                    continue
                cap_ok, cap_reason = within_distribution_caps(row, macro_counts, country_counts, period_counts, year_counts)
                if not cap_ok:
                    rejects[cap_reason] += 1
                    continue
                row["direction_id"] = "CRB2026V3"
                row["source_id"] = "SRC-COMMONS-REGION-BALANCE-2026-V3"
                row["source_object_type"] = f"large region-balanced open image record; {object_term}"
                row["classification_rationale"] = base.clean(
                    "Selected by large region-balanced Commons query, open-license extmetadata, strict source-derived graphic-object filter, duplicate exclusion, and explicit object-year evidence.",
                    max_chars=700,
                )
                row["uncertainty_note"] = (
                    "Commons metadata can be user-maintained; verify object date, original creator, source credit, and visual-communication relevance before final scholarly use."
                )
                seen_ids.add(source_key)
                seen_images.add(image_key)
                rows.append(row)
                country_counts[row["source_place_text"]] += 1
                macro_counts[macro_key(row)] += 1
                period_counts[period_band(row)] += 1
                year_counts[row_year(row)] += 1
                if len(rows) - last_checkpoint_rows >= CHECKPOINT_EVERY_ROWS:
                    write_outputs(rows, failures, rejects, started, final=False)
                    last_checkpoint_rows = len(rows)
                if len(rows) >= TARGET_ROWS:
                    break
            if "continue" not in payload:
                break
            cont = payload.get("continue", {})
            offset = base.clean(cont.get("gcmcontinue")) if query.startswith("Category:") else int(cont.get("gsroffset", int(offset or 0) + SEARCH_LIMIT))
            if not offset:
                break
            pages_seen += 1
        status = "failed" if len(failures) > failures_before else "completed"
        if status == "completed" and not had_pages:
            status = "empty"
        append_query_state(
            {
                "query_index": str(index),
                "macro": macro,
                "country": country,
                "object_term": object_term,
                "query": query,
                "status": status,
                "added": str(len(rows) - before),
                "failures_delta": str(len(failures) - failures_before),
                "rejects_delta": str(sum(rejects.values()) - rejects_before),
                "rows_after": str(len(rows)),
                "elapsed_seconds": f"{time.time() - started:.1f}",
            }
        )
        if len(rows) > before:
            write_outputs(rows, failures, rejects, started, final=False)
            last_checkpoint_rows = len(rows)
        if index % 25 == 0 or len(rows) > before or len(rows) >= TARGET_ROWS:
            print(f"v3_query_progress={index}/{len(plans)} rows={len(rows)} added={len(rows)-before} failures={len(failures)} rejects={sum(rejects.values())}", flush=True)

    write_outputs(rows, failures, rejects, started, final=True)
    print(f"wrote {RECORDS_CSV} rows={len(rows)} failures={len(failures)} rejects={sum(rejects.values())}")
    print(f"wrote {SUMMARY_CSV}")
    print(f"wrote {QUALITY_CSV}")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
