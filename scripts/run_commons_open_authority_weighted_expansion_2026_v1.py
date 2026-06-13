#!/usr/bin/env python3
"""Capture authority-weighted Commons open-image metadata records.

This is a release-late capture pass. It targets additional open sources while
reducing the previous batch's over-reliance on postage stamps. It prioritizes
small/low-coverage countries, pre-1940 material, art-school/community/
university contexts, and object families that add design-research value:
posters, book covers, labels, packaging, trade cards, typography, brochures,
and related public graphic communication.

The script stores metadata, source links, rights evidence, source-derived text,
and source-hosted image URLs only. It does not download image binaries,
thumbnails, screenshots, raw API payloads, cookies, browser sessions, or local
image files.
"""

from __future__ import annotations

import csv
import re
import time
import urllib.parse
from collections import Counter
from pathlib import Path

import run_commons_open_global_south_image_capture_2026_v1 as base


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
CAPTURE_RUNS = DATA / "capture_runs"

RECORDS_CSV = DATA / "capture_batch_commons_open_authority_weighted_expansion_2026_v1_records.csv"
SUMMARY_CSV = DATA / "capture_batch_commons_open_authority_weighted_expansion_2026_v1_source_summary.csv"
QUALITY_CSV = DATA / "commons_open_authority_weighted_expansion_2026_v1_quality.csv"
STATE_CSV = DATA / "commons_open_authority_weighted_expansion_2026_v1_query_state.csv"
REPORT = DOCS / "COMMONS_OPEN_AUTHORITY_WEIGHTED_EXPANSION_2026_v1.md"
MANIFEST = CAPTURE_RUNS / "capture_run_manifest_v1.csv"

ACCESS_DATE = "2026-06-13"
base.ACCESS_DATE = ACCESS_DATE
base.REQUEST_DELAY_SECONDS = 0.08
base.SEARCH_LIMIT = 50
base.GRAPHIC_TERMS = tuple(
    dict.fromkeys(
        [
            *base.GRAPHIC_TERMS,
            "postage stamp",
            "matchbox label",
            "trade card",
            "type specimen",
            "letterhead",
        ]
    )
)
FIELDNAMES = base.FIELDNAMES

TARGET_ROWS = 5000
SEARCH_LIMIT = 50
SEARCH_PAGES = 2
CATEGORY_PAGES = 8
REQUEST_DELAY_SECONDS = 0.08
CHECKPOINT_EVERY_ROWS = 100
PRE_1940_SEARCH_YEARS = sorted(set(list(range(1830, 1940, 5)) + [1931, 1933, 1935, 1937, 1938, 1939]), reverse=True)
POST_1940_SEARCH_YEARS = sorted(set(list(range(1940, 2001, 5)) + [1949, 1956, 1968, 1979, 1989, 1991, 1995, 1999]), reverse=True)

COUNTRY_CAP = 220
PERIOD_CAPS = {
    "pre_1940": 1800,
    "1940_1970": 1200,
    "1970_2000": 1000,
    "2000_2026": 1500,
}
OBJECT_CAPS = {
    "postage_stamp": 1250,
    "political_poster": 650,
    "film_poster": 850,
    "travel_poster": 400,
    "poster": 1400,
    "book_cover": 850,
    "magazine_cover": 450,
    "advertising_trade": 750,
    "label_packaging": 700,
    "brochure_pamphlet": 650,
    "typography_identity": 500,
    "other": 350,
}
YEAR_CAPS = {
    2026: 60,
    2025: 120,
    2024: 140,
}

COUNTRIES: list[tuple[str, str, list[str]]] = [
    ("Africa", "Angola", ["Angola", "Angolan"]),
    ("Africa", "Benin", ["Benin", "Beninese", "Dahomey"]),
    ("Africa", "Botswana", ["Botswana", "Bechuanaland"]),
    ("Africa", "Burkina Faso", ["Burkina Faso", "Upper Volta"]),
    ("Africa", "Cameroon", ["Cameroon", "Cameroonian"]),
    ("Africa", "Cape Verde", ["Cape Verde", "Cabo Verde"]),
    ("Africa", "Democratic Republic of the Congo", ["Democratic Republic of the Congo", "Congo", "Zaire"]),
    ("Africa", "Ethiopia", ["Ethiopia", "Ethiopian"]),
    ("Africa", "Ghana", ["Ghana", "Gold Coast"]),
    ("Africa", "Kenya", ["Kenya", "Kenyan"]),
    ("Africa", "Madagascar", ["Madagascar", "Malagasy"]),
    ("Africa", "Mali", ["Mali", "Malian"]),
    ("Africa", "Mauritius", ["Mauritius", "Mauritian"]),
    ("Africa", "Mozambique", ["Mozambique", "Mozambican"]),
    ("Africa", "Namibia", ["Namibia", "Namibian"]),
    ("Africa", "Nigeria", ["Nigeria", "Nigerian"]),
    ("Africa", "Rwanda", ["Rwanda", "Rwandan"]),
    ("Africa", "Senegal", ["Senegal", "Senegalese"]),
    ("Africa", "Seychelles", ["Seychelles"]),
    ("Africa", "Tanzania", ["Tanzania", "Tanganyika", "Zanzibar"]),
    ("Africa", "Togo", ["Togo", "Togolese"]),
    ("Africa", "Uganda", ["Uganda", "Ugandan"]),
    ("Africa", "Zambia", ["Zambia", "Northern Rhodesia"]),
    ("Africa", "Zimbabwe", ["Zimbabwe", "Rhodesia"]),
    ("Latin America / Caribbean", "Bahamas", ["Bahamas", "Bahamian"]),
    ("Latin America / Caribbean", "Barbados", ["Barbados", "Barbadian"]),
    ("Latin America / Caribbean", "Belize", ["Belize", "British Honduras"]),
    ("Latin America / Caribbean", "Bolivia", ["Bolivia", "Bolivian"]),
    ("Latin America / Caribbean", "Costa Rica", ["Costa Rica", "Costa Rican"]),
    ("Latin America / Caribbean", "Cuba", ["Cuba", "Cuban", "OSPAAAL"]),
    ("Latin America / Caribbean", "Dominican Republic", ["Dominican Republic", "Dominican"]),
    ("Latin America / Caribbean", "Ecuador", ["Ecuador", "Ecuadorian"]),
    ("Latin America / Caribbean", "El Salvador", ["El Salvador", "Salvadoran"]),
    ("Latin America / Caribbean", "Guatemala", ["Guatemala", "Guatemalan"]),
    ("Latin America / Caribbean", "Guyana", ["Guyana", "British Guiana"]),
    ("Latin America / Caribbean", "Haiti", ["Haiti", "Haitian"]),
    ("Latin America / Caribbean", "Honduras", ["Honduras", "Honduran"]),
    ("Latin America / Caribbean", "Jamaica", ["Jamaica", "Jamaican"]),
    ("Latin America / Caribbean", "Nicaragua", ["Nicaragua", "Nicaraguan"]),
    ("Latin America / Caribbean", "Panama", ["Panama", "Panamanian"]),
    ("Latin America / Caribbean", "Paraguay", ["Paraguay", "Paraguayan"]),
    ("Latin America / Caribbean", "Peru", ["Peru", "Peruvian"]),
    ("Latin America / Caribbean", "Puerto Rico", ["Puerto Rico", "Puerto Rican"]),
    ("Latin America / Caribbean", "Suriname", ["Suriname", "Surinamese"]),
    ("Latin America / Caribbean", "Trinidad and Tobago", ["Trinidad and Tobago", "Trinidad", "Tobago"]),
    ("Latin America / Caribbean", "Uruguay", ["Uruguay", "Uruguayan"]),
    ("Latin America / Caribbean", "Venezuela", ["Venezuela", "Venezuelan"]),
    ("Middle East and North Africa", "Algeria", ["Algeria", "Algerian"]),
    ("Middle East and North Africa", "Bahrain", ["Bahrain", "Bahraini"]),
    ("Middle East and North Africa", "Egypt", ["Egypt", "Egyptian"]),
    ("Middle East and North Africa", "Iran", ["Iran", "Iranian", "Persian"]),
    ("Middle East and North Africa", "Iraq", ["Iraq", "Iraqi"]),
    ("Middle East and North Africa", "Jordan", ["Jordan", "Jordanian"]),
    ("Middle East and North Africa", "Kuwait", ["Kuwait", "Kuwaiti"]),
    ("Middle East and North Africa", "Lebanon", ["Lebanon", "Lebanese"]),
    ("Middle East and North Africa", "Morocco", ["Morocco", "Moroccan"]),
    ("Middle East and North Africa", "Oman", ["Oman", "Omani"]),
    ("Middle East and North Africa", "Palestine", ["Palestine", "Palestinian"]),
    ("Middle East and North Africa", "Qatar", ["Qatar", "Qatari"]),
    ("Middle East and North Africa", "Syria", ["Syria", "Syrian"]),
    ("Middle East and North Africa", "Tunisia", ["Tunisia", "Tunisian"]),
    ("Middle East and North Africa", "United Arab Emirates", ["United Arab Emirates", "UAE", "Dubai", "Abu Dhabi"]),
    ("Middle East and North Africa", "Yemen", ["Yemen", "Yemeni"]),
    ("South Asia", "Bangladesh", ["Bangladesh", "Bangladeshi"]),
    ("South Asia", "India", ["India", "Indian", "Bollywood"]),
    ("South Asia", "Maldives", ["Maldives", "Maldivian"]),
    ("South Asia", "Nepal", ["Nepal", "Nepali"]),
    ("South Asia", "Pakistan", ["Pakistan", "Pakistani"]),
    ("South Asia", "Sri Lanka", ["Sri Lanka", "Ceylon", "Sri Lankan"]),
    ("Southeast Asia", "Brunei", ["Brunei", "Bruneian"]),
    ("Southeast Asia", "Cambodia", ["Cambodia", "Cambodian", "Khmer"]),
    ("Southeast Asia", "Indonesia", ["Indonesia", "Indonesian"]),
    ("Southeast Asia", "Laos", ["Laos", "Lao"]),
    ("Southeast Asia", "Malaysia", ["Malaysia", "Malaya", "Malaysian"]),
    ("Southeast Asia", "Myanmar", ["Myanmar", "Burma", "Burmese"]),
    ("Southeast Asia", "Philippines", ["Philippines", "Filipino", "Philippine"]),
    ("Southeast Asia", "Singapore", ["Singapore"]),
    ("Southeast Asia", "Thailand", ["Thailand", "Siam", "Thai"]),
    ("Southeast Asia", "Timor-Leste", ["Timor-Leste", "East Timor"]),
    ("Southeast Asia", "Vietnam", ["Vietnam", "Viet Nam", "Vietnamese"]),
    ("Central Asia", "Kazakhstan", ["Kazakhstan", "Kazakh"]),
    ("Central Asia", "Kyrgyzstan", ["Kyrgyzstan", "Kyrgyz"]),
    ("Central Asia", "Tajikistan", ["Tajikistan", "Tajik"]),
    ("Central Asia", "Turkmenistan", ["Turkmenistan", "Turkmen"]),
    ("Central Asia", "Uzbekistan", ["Uzbekistan", "Uzbek"]),
    ("Eastern Europe / Caucasus", "Albania", ["Albania", "Albanian"]),
    ("Eastern Europe / Caucasus", "Armenia", ["Armenia", "Armenian"]),
    ("Eastern Europe / Caucasus", "Azerbaijan", ["Azerbaijan", "Azerbaijani"]),
    ("Eastern Europe / Caucasus", "Bosnia and Herzegovina", ["Bosnia and Herzegovina", "Bosnia", "Herzegovina"]),
    ("Eastern Europe / Caucasus", "Bulgaria", ["Bulgaria", "Bulgarian"]),
    ("Eastern Europe / Caucasus", "Croatia", ["Croatia", "Croatian"]),
    ("Eastern Europe / Caucasus", "Estonia", ["Estonia", "Estonian"]),
    ("Eastern Europe / Caucasus", "Georgia", ["Georgia", "Georgian", "Tbilisi"]),
    ("Eastern Europe / Caucasus", "Latvia", ["Latvia", "Latvian"]),
    ("Eastern Europe / Caucasus", "Lithuania", ["Lithuania", "Lithuanian"]),
    ("Eastern Europe / Caucasus", "Moldova", ["Moldova", "Moldovan"]),
    ("Eastern Europe / Caucasus", "North Macedonia", ["North Macedonia", "Macedonia", "Macedonian"]),
    ("Eastern Europe / Caucasus", "Romania", ["Romania", "Romanian"]),
    ("Eastern Europe / Caucasus", "Serbia", ["Serbia", "Serbian"]),
    ("Eastern Europe / Caucasus", "Slovenia", ["Slovenia", "Slovenian"]),
    ("Eastern Europe / Caucasus", "Ukraine", ["Ukraine", "Ukrainian"]),
    ("Oceania / Pacific", "Fiji", ["Fiji", "Fijian"]),
    ("Oceania / Pacific", "Kiribati", ["Kiribati"]),
    ("Oceania / Pacific", "New Caledonia", ["New Caledonia"]),
    ("Oceania / Pacific", "Papua New Guinea", ["Papua New Guinea", "Papuan"]),
    ("Oceania / Pacific", "Samoa", ["Samoa", "Samoan"]),
    ("Oceania / Pacific", "Solomon Islands", ["Solomon Islands", "Solomon"]),
    ("Oceania / Pacific", "Tonga", ["Tonga", "Tongan"]),
    ("Oceania / Pacific", "Vanuatu", ["Vanuatu"]),
    ("Oceania / Pacific", "Aotearoa New Zealand", ["New Zealand", "Aotearoa", "Māori", "Maori"]),
    ("East Asia", "China", ["China", "Chinese", "Shanghai"]),
    ("East Asia", "Hong Kong", ["Hong Kong"]),
    ("East Asia", "Korea", ["Korea", "Korean", "South Korea"]),
    ("East Asia", "Mongolia", ["Mongolia", "Mongolian"]),
    ("East Asia", "Taiwan", ["Taiwan", "Taiwanese"]),
]

OBJECT_TERMS = [
    "poster",
    "political poster",
    "propaganda poster",
    "film poster",
    "travel poster",
    "advertising poster",
    "advertisement",
    "book cover",
    "magazine cover",
    "trade card",
    "label",
    "packaging",
    "matchbox label",
    "brochure",
    "pamphlet",
    "leaflet",
    "flyer",
    "type specimen",
    "letterhead",
]

AUTHORITY_CONTEXT_TERMS = [
    "art school poster",
    "school of art poster",
    "academy of fine arts poster",
    "university poster",
    "college poster",
    "student poster",
    "community poster",
    "library poster",
    "museum poster",
    "festival poster",
]

PRE_1940_CATEGORIES = [
    ("poster", "Category:1830s posters"),
    ("poster", "Category:1840s posters"),
    ("poster", "Category:1850s posters"),
    ("poster", "Category:1860s posters"),
    ("poster", "Category:1870s posters"),
    ("poster", "Category:1880s posters"),
    ("poster", "Category:1890s posters"),
    ("poster", "Category:1900s posters"),
    ("poster", "Category:1910s posters"),
    ("poster", "Category:1920s posters"),
    ("poster", "Category:1930s posters"),
    ("advertising poster", "Category:Art Nouveau posters"),
    ("advertisement", "Category:19th-century advertisements"),
    ("advertisement", "Category:Advertisements by year"),
    ("trade card", "Category:Trade cards"),
    ("label", "Category:Labels"),
    ("book cover", "Category:Book covers"),
    ("type specimen", "Category:Type specimens"),
]

COUNTRY_CATEGORY_PATTERNS = [
    ("poster", "Category:Posters of {country}"),
    ("political poster", "Category:Political posters of {country}"),
    ("propaganda poster", "Category:Propaganda posters of {country}"),
    ("film poster", "Category:Film posters of {country}"),
    ("travel poster", "Category:Travel posters of {country}"),
    ("advertising poster", "Category:Advertising posters of {country}"),
    ("postage stamp", "Category:Postage stamps of {country}"),
    ("book cover", "Category:Book covers of {country}"),
    ("magazine cover", "Category:Magazine covers of {country}"),
    ("label", "Category:Labels of {country}"),
    ("packaging", "Category:Packaging of {country}"),
    ("brochure", "Category:Brochures of {country}"),
    ("pamphlet", "Category:Pamphlets of {country}"),
]

WEAK_TERMS = (
    "poster session",
    "conference poster",
    "scientific poster",
    "poster presentation",
    "at poster session",
    "with poster",
    "standing next to poster",
    "calendar page",
    "copyright status unknown",
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


def expanded_region_seeds() -> list[tuple[str, str, str, list[str]]]:
    seeds: list[tuple[str, str, str, list[str]]] = []
    seen: set[tuple[str, str]] = set()
    for macro, country, aliases in COUNTRIES:
        if (macro, country) in seen:
            continue
        seen.add((macro, country))
        seeds.append((macro, country, country, aliases))
    for macro, country, region_term, aliases in base.REGION_SEEDS:
        if (macro, country) not in seen:
            seeds.append((macro, country, region_term, aliases))
            seen.add((macro, country))
    return seeds


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
                ids.add(source_record_url.lower())
            if image_url:
                image_urls.add(image_url.lower())
    for row in current_rows:
        if row.get("source_identifier"):
            ids.add(row["source_identifier"])
        if row.get("source_record_url"):
            ids.add(row["source_record_url"].lower())
        if row.get("image_url_detected"):
            image_urls.add(row["image_url_detected"].lower())
    return ids, image_urls


def add_plan(
    plan: list[tuple[str, str, str, str, str]],
    seen: set[str],
    macro: str,
    country: str,
    object_term: str,
    query: str,
    prefix: str,
) -> None:
    if query in seen:
        return
    seen.add(query)
    direction = re.sub(r"[^a-z0-9]+", "_", f"{prefix}_{country}_{object_term}".lower()).strip("_")
    plan.append((macro, country, direction, object_term, query))


def query_plan() -> list[tuple[str, str, str, str, str]]:
    plan: list[tuple[str, str, str, str, str]] = []
    seen: set[str] = set()
    balanced_object_terms = (
        "poster",
        "advertisement",
        "label",
        "postage stamp",
    )
    fast_global_object_terms = (
        "label",
        "book cover",
        "pamphlet",
        "advertisement",
        "trade card",
        "type specimen",
    )

    # Start with balanced country/object searches. The earlier global-year lane
    # was safe but too sparse after the first 500 rows; rotating by object first
    # keeps one productive country from monopolizing the run.
    for object_term in balanced_object_terms:
        for macro, country, aliases in COUNTRIES:
            for alias in aliases[:2]:
                add_plan(plan, seen, macro, country, object_term, f'"{alias}" "{object_term}"', "scarcity_object")

    for object_term, category in PRE_1940_CATEGORIES:
        add_plan(plan, seen, "_infer", "_infer", object_term, category, "pre1940_category")

    # Late-run topoff lanes. Once the country/object seed pass and high-yield
    # pre-1940 categories have run, these sources add clearer object evidence
    # than the very sparse pre-1940 country/year fallback queue.
    for year in range(2026, 1829, -1):
        for object_term in fast_global_object_terms:
            add_plan(plan, seen, "_infer", "_infer", object_term, f'"{year}" "{object_term}"', "high_yield_year_object")

    for authority_term in AUTHORITY_CONTEXT_TERMS:
        for macro, country, aliases in COUNTRIES:
            for alias in aliases[:2]:
                add_plan(plan, seen, macro, country, "poster", f'"{alias}" "{authority_term}"', "authority_context")

    for year in range(2000, 2027):
        for object_term in ("art school poster", "community poster", "design school poster", "university poster"):
            add_plan(plan, seen, "_infer", "_infer", "poster", f'"{year}" "{object_term}"', "contemporary_authority")

    for macro, country, aliases in COUNTRIES:
        for alias in aliases[:2]:
            for year in POST_1940_SEARCH_YEARS:
                for object_term in ("poster", "film poster", "advertising poster", "book cover"):
                    add_plan(plan, seen, macro, country, object_term, f'"{alias}" "{year}" "{object_term}"', "mid_late_country")

    for year in PRE_1940_SEARCH_YEARS:
        for object_term in ("poster", "advertisement", "trade card", "label", "book cover", "type specimen"):
            add_plan(plan, seen, "_infer", "_infer", object_term, f'"{year}" "{object_term}"', "pre1940_global")

    for macro, country, aliases in COUNTRIES:
        for alias in aliases[:2]:
            for year in PRE_1940_SEARCH_YEARS:
                for object_term in ("poster", "advertisement", "trade card", "label", "book cover"):
                    add_plan(plan, seen, macro, country, object_term, f'"{alias}" "{year}" "{object_term}"', "pre1940_country")

    for macro, country, aliases in COUNTRIES:
        for object_term, pattern in COUNTRY_CATEGORY_PATTERNS:
            add_plan(plan, seen, macro, country, object_term, pattern.format(country=country), "country_category")

    for year in range(2026, 1829, -1):
        for object_term in (
            "poster",
            "political poster",
            "propaganda poster",
            "film poster",
            "travel poster",
            "advertising poster",
            "advertisement",
            "book cover",
            "magazine cover",
            "trade card",
            "label",
            "packaging",
            "brochure",
            "pamphlet",
            "type specimen",
        ):
            add_plan(plan, seen, "_infer", "_infer", object_term, f'"{year}" "{object_term}"', "global_year_object")
    return plan


def completed_queries(max_rows_after: int) -> set[str]:
    completed: set[str] = set()
    for row in read_csv(STATE_CSV):
        try:
            rows_after = int(row.get("rows_after") or "0")
        except ValueError:
            rows_after = 0
        # A previous interrupted run can leave query_state ahead of the
        # checkpointed records CSV. Treat those rows as not completed so the
        # query can be replayed and de-duplicated against the saved records.
        if rows_after > max_rows_after:
            continue
        if row.get("status") in {"completed", "empty"} and row.get("query"):
            completed.add(row["query"])
    return completed


def append_state(row: dict[str, str]) -> None:
    fields = [
        "query_index",
        "macro",
        "country",
        "object_term",
        "query",
        "status",
        "added",
        "rows_after",
        "rejects_delta",
        "failures_delta",
        "elapsed_seconds",
    ]
    rows = [existing for existing in read_csv(STATE_CSV) if existing.get("query") != row.get("query")]
    rows.append(row)
    write_csv(STATE_CSV, rows, fields)


def row_year(row: dict[str, str]) -> int:
    try:
        return int(float(row.get("date_end") or row.get("date_start") or "0"))
    except ValueError:
        return 0


def period_band(row: dict[str, str]) -> str:
    year = row_year(row)
    if 1830 <= year < 1940:
        return "pre_1940"
    if year <= 1970:
        return "1940_1970"
    if year <= 2000:
        return "1970_2000"
    return "2000_2026"


def object_family(row: dict[str, str], object_term: str) -> str:
    blob = " ".join([object_term, row.get("source_object_type", ""), row.get("source_title", ""), row.get("source_subjects", "")]).lower()
    if "postage stamp" in blob or re.search(r"\bstamp\b", blob):
        return "postage_stamp"
    if "political poster" in blob or "propaganda poster" in blob or "campaign poster" in blob:
        return "political_poster"
    if "film poster" in blob or "movie poster" in blob:
        return "film_poster"
    if "travel poster" in blob:
        return "travel_poster"
    if "poster" in blob or "affiche" in blob or "plakat" in blob:
        return "poster"
    if "book cover" in blob:
        return "book_cover"
    if "magazine cover" in blob:
        return "magazine_cover"
    if "trade card" in blob or "advertisement" in blob or "advertising" in blob:
        return "advertising_trade"
    if "label" in blob or "packaging" in blob or "matchbox" in blob:
        return "label_packaging"
    if "brochure" in blob or "pamphlet" in blob or "leaflet" in blob or "flyer" in blob:
        return "brochure_pamphlet"
    if "type specimen" in blob or "letterhead" in blob or "typography" in blob:
        return "typography_identity"
    return "other"


def quality_gate(row: dict[str, str], object_term: str) -> tuple[bool, str]:
    title = row.get("source_title", "").lower()
    description = row.get("source_description", "").lower()
    notes = row.get("source_notes", "").lower()
    subjects = row.get("source_subjects", "").lower()
    blob = " ".join([title, description, notes, subjects])
    if any(term in blob for term in WEAK_TERMS):
        return False, "weak_graphic_or_event_photo"
    if object_family(row, object_term) == "other":
        return False, "unclear_object_family"
    if row_year(row) in YEAR_CAPS and row_year(row) > 2026:
        return False, "future_year"
    if "file:" in title and title.endswith((".svg", ".pdf", ".djvu")):
        return False, "non_raster_source"
    return True, "ok"


def macro_key(row: dict[str, str]) -> str:
    return row.get("source_place_text", "").split(" / ")[0] or "unmapped"


def distribution_gate(
    row: dict[str, str],
    object_term: str,
    macro_counts: Counter[str],
    country_counts: Counter[str],
    period_counts: Counter[str],
    object_counts: Counter[str],
    year_counts: Counter[int],
) -> tuple[bool, str]:
    country = row.get("source_place_text", "")
    period = period_band(row)
    family = object_family(row, object_term)
    year = row_year(row)
    # Near the end, loosen caps except for severe duplicate-prone classes.
    nearly_done = sum(object_counts.values()) >= int(TARGET_ROWS * 0.88)
    if country_counts[country] >= COUNTRY_CAP and not nearly_done:
        return False, "country_cap"
    if period_counts[period] >= PERIOD_CAPS.get(period, TARGET_ROWS) and not nearly_done:
        return False, "period_cap"
    if object_counts[family] >= OBJECT_CAPS.get(family, TARGET_ROWS) and not nearly_done:
        return False, "object_family_cap"
    if family == "postage_stamp" and object_counts[family] >= OBJECT_CAPS["postage_stamp"] + 250:
        return False, "postage_stamp_hard_cap"
    if year in YEAR_CAPS and year_counts[year] >= YEAR_CAPS[year]:
        return False, "year_cap"
    if macro_counts[macro_key(row)] >= 950 and not nearly_done:
        return False, "macro_soft_cap"
    return True, "ok"


def reseed_counters(rows: list[dict[str, str]]) -> tuple[Counter[str], Counter[str], Counter[str], Counter[str], Counter[int]]:
    macro_counts: Counter[str] = Counter()
    country_counts: Counter[str] = Counter()
    period_counts: Counter[str] = Counter()
    object_counts: Counter[str] = Counter()
    year_counts: Counter[int] = Counter()
    for row in rows:
        country_counts[row.get("source_place_text", "")] += 1
        macro_counts[macro_key(row)] += 1
        period_counts[period_band(row)] += 1
        object_counts[object_family(row, row.get("source_object_type", ""))] += 1
        year_counts[row_year(row)] += 1
    return macro_counts, country_counts, period_counts, object_counts, year_counts


def write_outputs(rows: list[dict[str, str]], failures: list[dict[str, str]], rejects: Counter[str]) -> None:
    rows.sort(key=lambda row: (row.get("date_start", ""), row.get("source_place_text", ""), row.get("source_title", "")))
    for index, row in enumerate(rows, 1):
        row["capture_id"] = f"CAW2026R{index:05d}"
    write_csv(RECORDS_CSV, rows, FIELDNAMES)

    by_source = Counter(row["source_name"] for row in rows)
    summary_rows = [
        {
            "source_name": source,
            "captured_records": str(count),
            "image_states": f"IMG03:{count}",
            "notes": "Authority-weighted Commons open-license metadata; no image binary downloaded",
        }
        for source, count in sorted(by_source.items())
    ]
    write_csv(SUMMARY_CSV, summary_rows, ["source_name", "captured_records", "image_states", "notes"])

    period_counts = Counter(period_band(row) for row in rows)
    macro_counts = Counter(macro_key(row) for row in rows)
    object_counts = Counter(object_family(row, row.get("source_object_type", "")) for row in rows)
    country_counts = Counter(row.get("source_place_text", "") for row in rows)
    year_2026 = sum(1 for row in rows if row_year(row) == 2026)
    quality_rows = [
        {"metric": "records_captured", "value": str(len(rows))},
        {"metric": "distinct_active_source_names", "value": str(len(by_source))},
        {"metric": "target_rows", "value": str(TARGET_ROWS)},
        {"metric": "target_met", "value": str(len(rows) >= TARGET_ROWS).lower()},
        {"metric": "query_failures", "value": str(len(failures))},
        {"metric": "year_2026_count", "value": str(year_2026)},
        {"metric": "year_2026_rate", "value": f"{(year_2026 / len(rows) * 100):.2f}" if rows else "0.00"},
    ]
    for key, count in period_counts.most_common():
        quality_rows.append({"metric": f"period:{key}", "value": str(count)})
    for key, count in macro_counts.most_common():
        quality_rows.append({"metric": f"macro:{key}", "value": str(count)})
    for key, count in object_counts.most_common():
        quality_rows.append({"metric": f"object_family:{key}", "value": str(count)})
    for key, count in country_counts.most_common(40):
        quality_rows.append({"metric": f"country:{key}", "value": str(count)})
    for key, count in rejects.most_common():
        quality_rows.append({"metric": f"reject:{key}", "value": str(count)})
    write_csv(QUALITY_CSV, quality_rows, ["metric", "value"])

    update_manifest(rows, by_source)
    write_report(rows, by_source, failures, rejects, period_counts, macro_counts, object_counts, country_counts)


def update_manifest(rows: list[dict[str, str]], by_source: Counter[str]) -> None:
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
    run_id = "commons_open_authority_weighted_expansion_2026_v1"
    manifest_rows = [row for row in read_csv(MANIFEST) if row.get("run_id") != run_id]
    manifest_rows.append(
        {
            "run_id": run_id,
            "records_csv": str(RECORDS_CSV.relative_to(ROOT)),
            "records_count": str(len(rows)),
            "active_source_count": str(len(by_source)),
            "image_state_counts": f"IMG03:{len(rows)}" if rows else "",
            "summary_csv": str(SUMMARY_CSV.relative_to(ROOT)),
            "summary_exists": "true",
            "report_md": str(REPORT.relative_to(ROOT)),
            "report_exists": "true",
            "raw_dir": "",
            "raw_dir_exists": "false",
            "raw_commit_policy": "not_present",
            "included_in_public_rebuild": "false",
            "stage": "item_image_capture_pending_rebuild" if rows else "empty_or_pending",
            "notes": "Authority-weighted Commons open image capture; low-coverage countries, pre-1940, art/community/education contexts; no image binaries or raw payloads saved. Pending final surface rebuild before release-gate counting.",
        }
    )
    write_csv(MANIFEST, manifest_rows, fields)


def write_report(
    rows: list[dict[str, str]],
    by_source: Counter[str],
    failures: list[dict[str, str]],
    rejects: Counter[str],
    period_counts: Counter[str],
    macro_counts: Counter[str],
    object_counts: Counter[str],
    country_counts: Counter[str],
) -> None:
    lines = [
        "# Commons Open Authority Weighted Expansion 2026 v1",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        "Scope: Commons open-license source pages prioritized for low-coverage regions, pre-1940 material, art-school/community/education contexts, and design-research object families.",
        "",
        "## Metrics",
        "",
        f"- Records captured: {len(rows)}",
        f"- Distinct active source names: {len(by_source)}",
        f"- Query failures: {len(failures)}",
        f"- Target rows: {TARGET_ROWS}",
        f"- Target met: {str(len(rows) >= TARGET_ROWS).lower()}",
        "",
        "## Period Distribution",
        "",
    ]
    for key, count in period_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Macro-region Distribution", ""])
    for key, count in macro_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Object Family Distribution", ""])
    for key, count in object_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Top Country Distribution", ""])
    for key, count in country_counts.most_common(40):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Reject Reasons", ""])
    for key, count in rejects.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No image binaries were downloaded.",
            "- No raw API payloads, cookies, browser sessions, screenshots, thumbnails, or local image files were saved.",
            "- IMG03 is assigned only from Commons open-license extmetadata.",
            "- Poster-session, conference-poster, calendar-page, and unclear event-photo records are filtered out.",
            "- Commons remains a source page, not an ownership claim; source credit and original creator require review where Commons metadata is thin.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    base.REGION_SEEDS = expanded_region_seeds()
    base.INFER_FALLBACK_REGION = None
    DATA.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    rows = read_csv(RECORDS_CSV)
    seen_ids, seen_images = existing_keys(rows)
    macro_counts, country_counts, period_counts, object_counts, year_counts = reseed_counters(rows)
    failures: list[dict[str, str]] = []
    rejects: Counter[str] = Counter()
    completed = completed_queries(len(rows))
    started = time.time()
    plan = query_plan()

    for index, (macro, country, direction_name, object_term, query) in enumerate(plan, 1):
        if len(rows) >= TARGET_ROWS:
            break
        if query in completed:
            continue
        before = len(rows)
        rejects_before = sum(rejects.values())
        failures_before = len(failures)
        offset: int | str = ""
        pages_seen = 0
        max_pages = CATEGORY_PAGES if query.startswith("Category:") else SEARCH_PAGES
        status = "empty"
        while pages_seen < max_pages and len(rows) < TARGET_ROWS:
            url = base.search_url(query, offset=offset, limit=SEARCH_LIMIT)
            try:
                payload = base.fetch_json(url)
            except Exception as exc:  # noqa: BLE001
                failures.append({"query": query, "error": type(exc).__name__, "detail": base.clean(str(exc), max_chars=180)})
                status = "failed"
                break
            time.sleep(REQUEST_DELAY_SECONDS)
            pages = list((payload.get("query", {}).get("pages") or {}).values())
            if not pages:
                break
            status = "completed"
            for page in sorted(pages, key=lambda item: item.get("index", 9999)):
                row = base.row_from_page(page, macro, country, direction_name, object_term, url)
                if not row:
                    rejects["base_filter"] += 1
                    continue
                ok, reason = quality_gate(row, object_term)
                if not ok:
                    rejects[reason] += 1
                    continue
                source_key = row["source_identifier"] or row["source_record_url"]
                record_url_key = row["source_record_url"].lower()
                image_key = row["image_url_detected"].lower()
                if source_key in seen_ids or record_url_key in seen_ids or image_key in seen_images:
                    rejects["duplicate"] += 1
                    continue
                ok, reason = distribution_gate(row, object_term, macro_counts, country_counts, period_counts, object_counts, year_counts)
                if not ok:
                    rejects[reason] += 1
                    continue
                family = object_family(row, object_term)
                row["direction_id"] = "CAW2026"
                row["source_id"] = "SRC-COMMONS-AUTHORITY-WEIGHTED-EXPANSION-2026-V1"
                row["source_object_type"] = f"authority-weighted Commons open image record; {object_term}; {family}"
                row["classification_rationale"] = base.clean(
                    "Selected by authority-weighted Commons query/category capture: low-coverage region, pre-1940 or design-research object signal, open-license extmetadata, duplicate exclusion, and weak event-photo filtering.",
                    max_chars=900,
                )
                row["uncertainty_note"] = base.clean(
                    "Commons metadata and category membership are user-maintained; verify object date, source credit, original creator, and institutional relation before high-stakes scholarly use.",
                    max_chars=900,
                )
                seen_ids.add(source_key)
                seen_ids.add(record_url_key)
                seen_images.add(image_key)
                rows.append(row)
                macro_counts[macro_key(row)] += 1
                country_counts[row["source_place_text"]] += 1
                period_counts[period_band(row)] += 1
                object_counts[family] += 1
                year_counts[row_year(row)] += 1
                if len(rows) % CHECKPOINT_EVERY_ROWS == 0:
                    write_outputs(rows, failures, rejects)
                    print(f"checkpoint rows={len(rows)} query={index}/{len(plan)}", flush=True)
                if len(rows) >= TARGET_ROWS:
                    break
            if "continue" not in payload:
                break
            cont = payload.get("continue", {})
            offset = base.clean(cont.get("gcmcontinue")) if query.startswith("Category:") else int(cont.get("gsroffset", int(offset or 0) + SEARCH_LIMIT))
            if not offset:
                break
            pages_seen += 1
        if len(rows) > before:
            write_outputs(rows, failures, rejects)
        append_state(
            {
                "query_index": str(index),
                "macro": macro,
                "country": country,
                "object_term": object_term,
                "query": query,
                "status": status,
                "added": str(len(rows) - before),
                "rows_after": str(len(rows)),
                "rejects_delta": str(sum(rejects.values()) - rejects_before),
                "failures_delta": str(len(failures) - failures_before),
                "elapsed_seconds": f"{time.time() - started:.1f}",
            }
        )
        if index % 25 == 0 or len(rows) > before:
            print(
                f"authority_query_progress={index}/{len(plan)} rows={len(rows)} added={len(rows)-before} failures={len(failures)} rejects={sum(rejects.values())}",
                flush=True,
            )

    write_outputs(rows, failures, rejects)
    print(f"records_captured={len(rows)}")
    print(f"target_met={len(rows) >= TARGET_ROWS}")
    print(f"failures={len(failures)}")
    print(f"rejects={dict(rejects.most_common())}")


if __name__ == "__main__":
    main()
