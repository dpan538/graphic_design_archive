#!/usr/bin/env python3
"""Capture a final-gap open-source metadata batch for release-late cleanup.

This pass is deliberately narrower than earlier Commons expansion batches. It
targets underfilled release periods and contemporary studio/project evidence
while excluding post-2010 commemorative stamp drift, event photographs, memory
material, and access-year-only 2025/2026 inflation.

The script stores metadata, source links, rights evidence, source-derived text,
and source-hosted image URLs only. It does not download image binaries,
screenshots, thumbnails as files, cookies, browser sessions, or raw API
payloads.
"""

from __future__ import annotations

import csv
import os
import re
import time
from collections import Counter
from pathlib import Path

import run_commons_open_authority_weighted_expansion_2026_v1 as authority
import run_commons_open_global_south_image_capture_2026_v1 as base


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
CAPTURE_RUNS = DATA / "capture_runs"

RECORDS_CSV = DATA / "capture_batch_final_gap_open_source_1955_2024_v1_records.csv"
SUMMARY_CSV = DATA / "capture_batch_final_gap_open_source_1955_2024_v1_source_summary.csv"
QUALITY_CSV = DATA / "final_gap_open_source_capture_1955_2024_v1_quality.csv"
STATE_CSV = DATA / "final_gap_open_source_capture_1955_2024_v1_query_state.csv"
FAILURES_CSV = DATA / "final_gap_open_source_capture_1955_2024_v1_failures.csv"
REPORT = DOCS / "FINAL_GAP_OPEN_SOURCE_CAPTURE_1955_2024_v1.md"
MANIFEST = CAPTURE_RUNS / "capture_run_manifest_v1.csv"

ACCESS_DATE = "2026-06-18"
FIELDNAMES = base.FIELDNAMES

TARGET_ROWS = int(os.environ.get("FINAL_GAP_TARGET_ROWS", "4200"))
SEARCH_LIMIT = int(os.environ.get("FINAL_GAP_SEARCH_LIMIT", "50"))
SEARCH_PAGES = int(os.environ.get("FINAL_GAP_SEARCH_PAGES", "2"))
CATEGORY_PAGES = int(os.environ.get("FINAL_GAP_CATEGORY_PAGES", "5"))
REQUEST_DELAY_SECONDS = float(os.environ.get("FINAL_GAP_REQUEST_DELAY", "0.20"))
CHECKPOINT_EVERY_ROWS = int(os.environ.get("FINAL_GAP_CHECKPOINT_EVERY", "100"))
MAX_CONSECUTIVE_FAILURES = int(os.environ.get("FINAL_GAP_MAX_CONSECUTIVE_FAILURES", "80"))

base.ACCESS_DATE = ACCESS_DATE
base.SEARCH_LIMIT = SEARCH_LIMIT
base.REQUEST_DELAY_SECONDS = REQUEST_DELAY_SECONDS
base.GRAPHIC_TERMS = (
    "advertisement",
    "advertising",
    "affiche",
    "book cover",
    "brochure",
    "campaign",
    "cover",
    "exhibition poster",
    "festival poster",
    "film poster",
    "flyer",
    "graphic design",
    "label",
    "leaflet",
    "magazine cover",
    "matchbox label",
    "packaging",
    "pamphlet",
    "pictogram",
    "placard",
    "plakat",
    "poster",
    "record cover",
    "record sleeve",
    "typography",
)

TARGET_PERIODS: list[tuple[str, range]] = [
    ("1945_1949_moderate_gap", range(1945, 1950)),
    ("1955_1964_gap", range(1955, 1965)),
    ("1980_1989_gap", range(1980, 1990)),
    ("1990_1999_gap", range(1990, 2000)),
    ("2000_2004_gap", range(2000, 2005)),
    ("2015_2019_contemporary_studio_depth", range(2015, 2020)),
]
TARGET_YEARS = sorted({year for _label, years in TARGET_PERIODS for year in years})

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
    "record cover",
    "album cover",
    "record sleeve",
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

AUTHORITY_TERMS = [
    "art school poster",
    "design school poster",
    "school of art poster",
    "academy of fine arts poster",
    "university poster",
    "college poster",
    "student poster",
    "community poster",
    "museum poster",
    "gallery poster",
    "festival poster",
    "biennial poster",
    "identity design",
    "graphic design studio",
    "visual communication",
]

PRIORITY_COUNTRIES: list[tuple[str, str, list[str]]] = [
    ("Latin America / Caribbean", "Cuba", ["Cuba", "Cuban", "OSPAAAL"]),
    ("Latin America / Caribbean", "Mexico", ["Mexico", "Mexican", "México"]),
    ("Latin America / Caribbean", "Brazil", ["Brazil", "Brazilian", "Brasil"]),
    ("Latin America / Caribbean", "Argentina", ["Argentina", "Argentine"]),
    ("Latin America / Caribbean", "Chile", ["Chile", "Chilean"]),
    ("Latin America / Caribbean", "Colombia", ["Colombia", "Colombian"]),
    ("Africa", "South Africa", ["South Africa", "South African", "anti-apartheid", "apartheid"]),
    ("Africa", "Ghana", ["Ghana", "Ghanaian"]),
    ("Africa", "Nigeria", ["Nigeria", "Nigerian"]),
    ("Africa", "Kenya", ["Kenya", "Kenyan"]),
    ("Middle East and North Africa", "Palestine", ["Palestine", "Palestinian"]),
    ("Middle East and North Africa", "Iran", ["Iran", "Iranian", "Persian"]),
    ("Middle East and North Africa", "Turkey", ["Turkey", "Turkish"]),
    ("South Asia", "India", ["India", "Indian", "Bollywood"]),
    ("South Asia", "Pakistan", ["Pakistan", "Pakistani"]),
    ("South Asia", "Bangladesh", ["Bangladesh", "Bangladeshi"]),
    ("Southeast Asia", "Indonesia", ["Indonesia", "Indonesian"]),
    ("Southeast Asia", "Philippines", ["Philippines", "Filipino", "Philippine"]),
    ("Southeast Asia", "Vietnam", ["Vietnam", "Viet Nam", "Vietnamese"]),
    ("Eastern Europe / Caucasus", "Poland", ["Poland", "Polish", "Warsaw"]),
    ("Eastern Europe / Caucasus", "Czech Republic", ["Czech", "Czechoslovak", "Prague"]),
    ("Eastern Europe / Caucasus", "Hungary", ["Hungary", "Hungarian", "Budapest"]),
    ("Eastern Europe / Caucasus", "Yugoslavia", ["Yugoslavia", "Yugoslav"]),
    ("Eastern Europe / Caucasus", "Serbia", ["Serbia", "Serbian"]),
    ("Eastern Europe / Caucasus", "Croatia", ["Croatia", "Croatian"]),
    ("Eastern Europe / Caucasus", "Ukraine", ["Ukraine", "Ukrainian"]),
    ("Eastern Europe / Caucasus", "Russia", ["Russia", "Russian", "Soviet"]),
    ("Oceania / Pacific", "Aotearoa New Zealand", ["New Zealand", "Aotearoa", "Maori", "Māori"]),
]

PRIORITY_SEARCH_PHRASES = [
    ("Latin America / Caribbean", "Cuba", "poster", "OSPAAAL poster"),
    ("Latin America / Caribbean", "Cuba", "poster", "Cuban poster"),
    ("Africa", "South Africa", "poster", "anti-apartheid poster"),
    ("Africa", "South Africa", "poster", "South African poster"),
    ("Eastern Europe / Caucasus", "Poland", "poster", "Polish poster"),
    ("Eastern Europe / Caucasus", "Czech Republic", "poster", "Czech poster"),
    ("Eastern Europe / Caucasus", "Czech Republic", "poster", "Czechoslovak poster"),
    ("Eastern Europe / Caucasus", "Hungary", "poster", "Hungarian poster"),
    ("Eastern Europe / Caucasus", "Russia", "poster", "Soviet poster"),
    ("Eastern Europe / Caucasus", "Yugoslavia", "poster", "Yugoslav poster"),
    ("South Asia", "India", "film poster", "Bollywood poster"),
    ("Middle East and North Africa", "Palestine", "poster", "Palestinian poster"),
    ("Southeast Asia", "Indonesia", "poster", "Indonesian poster"),
    ("Southeast Asia", "Vietnam", "poster", "Vietnamese poster"),
]

PERIOD_CATEGORIES = [
    ("poster", "Category:1940s posters"),
    ("poster", "Category:1950s posters"),
    ("poster", "Category:1960s posters"),
    ("poster", "Category:1980s posters"),
    ("poster", "Category:1990s posters"),
    ("poster", "Category:2000s posters"),
    ("poster", "Category:2010s posters"),
    ("advertisement", "Category:1950s advertisements"),
    ("advertisement", "Category:1960s advertisements"),
    ("advertisement", "Category:1980s advertisements"),
    ("advertisement", "Category:1990s advertisements"),
    ("book cover", "Category:Book covers"),
    ("magazine cover", "Category:Magazine covers"),
    ("label", "Category:Labels"),
    ("packaging", "Category:Packaging"),
    ("brochure", "Category:Brochures"),
]

COUNTRY_CATEGORY_PATTERNS = [
    ("poster", "Category:Posters of {country}"),
    ("political poster", "Category:Political posters of {country}"),
    ("propaganda poster", "Category:Propaganda posters of {country}"),
    ("film poster", "Category:Film posters of {country}"),
    ("travel poster", "Category:Travel posters of {country}"),
    ("advertising poster", "Category:Advertising posters of {country}"),
    ("book cover", "Category:Book covers of {country}"),
    ("magazine cover", "Category:Magazine covers of {country}"),
    ("label", "Category:Labels of {country}"),
    ("packaging", "Category:Packaging of {country}"),
    ("brochure", "Category:Brochures of {country}"),
    ("pamphlet", "Category:Pamphlets of {country}"),
]

POSTAGE_TERMS = (
    "postage stamp",
    "postage stamps",
    "stamp sheet",
    "stamp series",
    "stamp issue",
    "stamp of",
    "stamps of",
    "philatelic",
    "philately",
    "first day cover",
    "souvenir sheet",
    "sheetlet",
    "postmark",
    "postal stationery",
    "commemorative stamp",
    "wns stamp",
    "scott catalogue",
)

EVENT_PHOTO_TERMS = (
    "demonstratie",
    "demonstration",
    "protest march",
    "rally",
    "manifestation",
    "conference poster",
    "conference attendees",
    "conference can be viewed",
    "satellite conference",
    "poster session",
    "scientific poster",
    "poster presentation",
    "poster launch",
    "group photo",
    "group photograph",
    "photograph",
    "photo of",
    "press conference",
    "opening ceremony",
    "award ceremony",
    "launch event",
    "workshop participants",
    "at the workshop",
    "at the conference",
    "talk at",
    "lecture at",
    "wikimania",
    "meetup",
    "memory of",
    "commemorative photo",
)

WEAK_SOURCE_TERMS = (
    "copyright status unknown",
    "unknown copyright",
    "rights status is unknown",
    "own work",
    "self-photographed",
    "flickr",
    "instagram",
    "facebook",
    "geograph.org.uk",
    "flickr",
)

NON_OBJECT_TEXT_TERMS = (
    "poster designer",
    "designer.jpg",
    "cableway",
    "constitution page",
    "bilingual.png",
    "page 1 bilingual",
    "page 2 bilingual",
    "along milwaukee",
    "launch.jpg",
)

COUNTRY_CAP = int(os.environ.get("FINAL_GAP_COUNTRY_CAP", "160"))
COLLECTION_CAP = int(os.environ.get("FINAL_GAP_COLLECTION_CAP", "120"))
CREATOR_CAP = int(os.environ.get("FINAL_GAP_CREATOR_CAP", "85"))
YEAR_CAP = int(os.environ.get("FINAL_GAP_YEAR_CAP", "240"))
FAMILY_CAPS = {
    "poster": 1500,
    "political_poster": 700,
    "film_poster": 900,
    "travel_poster": 380,
    "book_cover": 620,
    "magazine_cover": 380,
    "advertising_trade": 620,
    "label_packaging": 620,
    "brochure_pamphlet": 520,
    "typography_identity": 360,
    "other": 0,
    "postage_stamp": 0,
}
PERIOD_CAPS = {
    "1945_1949_moderate_gap": 220,
    "1955_1964_gap": 260,
    "1980_1989_gap": 430,
    "1990_1999_gap": 320,
    "2000_2004_gap": 320,
    "2015_2019_contemporary_studio_depth": 260,
}


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


def target_period(year: int) -> str:
    for label, years in TARGET_PERIODS:
        if year in years:
            return label
    return "out_of_scope"


def row_year(row: dict[str, str]) -> int:
    try:
        return int(float(row.get("date_end") or row.get("date_start") or "0"))
    except ValueError:
        return 0


def object_family(row: dict[str, str], object_term: str) -> str:
    return authority.object_family(row, object_term)


def normalized_key(value: str, *, default: str) -> str:
    text = base.clean(value, max_chars=220).lower()
    text = re.sub(r"https?://", "", text)
    text = re.sub(r"www\.", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return text or default


def quality_blob(row: dict[str, str], object_term: str) -> str:
    return " ".join(
        [
            object_term,
            row.get("source_title", ""),
            row.get("source_description", ""),
            row.get("source_notes", ""),
            row.get("source_subjects", ""),
            row.get("source_collection", ""),
            row.get("source_creator", ""),
            row.get("source_rights_text", ""),
        ]
    ).lower()


def object_evidence_blob(row: dict[str, str]) -> str:
    return " ".join(
        [
            row.get("source_title", ""),
            row.get("source_description", ""),
            row.get("source_notes", ""),
            row.get("source_collection", ""),
            row.get("source_creator", ""),
        ]
    ).lower()


def country_aliases(country: str) -> list[str]:
    aliases: list[str] = []
    for _macro, candidate, terms in [*PRIORITY_COUNTRIES, *authority.COUNTRIES]:
        if candidate == country:
            aliases.extend(terms)
            aliases.append(candidate)
    if country == "Czech Republic":
        aliases.extend(["Czech", "Czechoslovak", "Prague"])
    if country == "Russia":
        aliases.extend(["Russia", "Russian", "Soviet"])
    return [alias.lower() for alias in dict.fromkeys(aliases) if alias]


def has_region_evidence(row: dict[str, str]) -> bool:
    place = row.get("source_place_text", "")
    country = place.split(" / ")[-1].strip()
    if not country or country in {"_infer", "final gap review"}:
        return True
    aliases = country_aliases(country)
    if not aliases:
        return True
    blob = object_evidence_blob(row)
    return any(re.search(rf"(?<![a-z]){re.escape(alias)}(?![a-z])", blob) for alias in aliases)


def has_object_evidence(row: dict[str, str], object_term: str) -> bool:
    blob = object_evidence_blob(row)
    family = object_family(row, object_term)
    if family in {"poster", "political_poster", "film_poster", "travel_poster"}:
        return bool(re.search(r"\b(poster|posters|plakat|affiche|cartel|cartaz)\b", blob))
    if family == "book_cover":
        return bool(re.search(r"\b(book cover|cover design|dust jacket)\b", blob))
    if family == "magazine_cover":
        return bool(re.search(r"\b(magazine cover|journal cover|periodical cover)\b", blob))
    if family == "advertising_trade":
        return bool(re.search(r"\b(advertisement|advertising|trade card|publicity)\b", blob))
    if family == "label_packaging":
        return bool(re.search(r"\b(label|packaging|package|wrapper|matchbox)\b", blob))
    if family == "brochure_pamphlet":
        return bool(re.search(r"\b(brochure|pamphlet|leaflet|flyer|fly-sheet)\b", blob))
    if family == "typography_identity":
        return bool(re.search(r"\b(type specimen|letterhead|typography|identity|pictogram)\b", blob))
    return False


def quality_gate(row: dict[str, str], object_term: str) -> tuple[bool, str]:
    year = row_year(row)
    blob = quality_blob(row, object_term)
    evidence_blob = object_evidence_blob(row)
    family = object_family(row, object_term)
    if year not in TARGET_YEARS:
        return False, "outside_target_periods"
    if year >= 2025:
        return False, "current_year_guard"
    if row.get("image_presence_code") != "IMG03":
        return False, "not_verified_open_img03"
    if any(term in blob for term in POSTAGE_TERMS):
        return False, "postage_or_philatelic_excluded"
    if any(term in blob for term in EVENT_PHOTO_TERMS):
        return False, "event_photo_or_memory_material"
    if any(term in evidence_blob for term in NON_OBJECT_TEXT_TERMS):
        return False, "non_object_text_or_context_image"
    if any(term in blob for term in WEAK_SOURCE_TERMS):
        return False, "weak_source_or_platform_noise"
    if family in {"other", "postage_stamp"}:
        return False, f"unsupported_object_family:{family}"
    if not has_region_evidence(row):
        return False, "region_not_source_evidenced"
    if not has_object_evidence(row, object_term):
        return False, "object_term_not_source_evidenced"
    return True, "ok"


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


def work_key(row: dict[str, str]) -> str:
    title = base.clean(row.get("source_title", ""), max_chars=300).lower()
    title = re.sub(r"\.(jpg|jpeg|png|tif|tiff|webp)$", "", title)
    title = re.sub(r"\([^)]*(cropped|crop|bestanddeelnr|file|version|v[0-9]+)[^)]*\)", " ", title)
    title = re.sub(r"\b(cropped|crop|bestanddeelnr|file|version)\b", " ", title)
    title = re.sub(r"\b(v|version)\s*[0-9]+\b", " ", title)
    title = re.sub(r"\b[a-z][0-9]{2,}\b", " ", title)
    title = re.sub(r"\b[0-9]{4,}\b", " ", title)
    title = re.sub(r"[^a-z0-9]+", " ", title).strip()
    place = row.get("source_place_text", "").lower().strip()
    year = row_year(row)
    return f"{place}|{year}|{title}"


def existing_work_keys(current_rows: list[dict[str, str]]) -> set[str]:
    keys: set[str] = set()
    for row in current_rows:
        key = work_key(row)
        if key:
            keys.add(key)
    return keys


def completed_queries(max_rows_after: int) -> set[str]:
    completed: set[str] = set()
    for row in read_csv(STATE_CSV):
        try:
            rows_after = int(row.get("rows_after") or "0")
        except ValueError:
            rows_after = 0
        if rows_after > max_rows_after:
            continue
        if row.get("status") in {"completed", "empty", "failed"} and row.get("query"):
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


def query_plan() -> list[tuple[str, str, str, str, str]]:
    plan: list[tuple[str, str, str, str, str]] = []
    seen: set[str] = set()
    countries = []
    seen_country: set[tuple[str, str]] = set()
    for macro, country, aliases in [*PRIORITY_COUNTRIES, *authority.COUNTRIES]:
        if (macro, country) in seen_country:
            continue
        seen_country.add((macro, country))
        countries.append((macro, country, aliases))
    priority_countries = PRIORITY_COUNTRIES
    priority_years = [*range(1980, 1990), *range(2000, 2005), *range(1955, 1965), *range(1990, 2000), *range(2015, 2020), *range(1945, 1950)]

    for macro, country, object_term, phrase in PRIORITY_SEARCH_PHRASES:
        add_plan(plan, seen, macro, country, object_term, phrase, "priority_phrase")

    for year in priority_years:
        for macro, country, object_term, phrase in PRIORITY_SEARCH_PHRASES:
            add_plan(plan, seen, macro, country, object_term, f"{phrase} {year}", "priority_phrase_year")

    for year in priority_years:
        for macro, country, aliases in priority_countries:
            for alias in aliases[:3]:
                for object_term in ("poster", "advertising poster", "film poster", "book cover", "magazine cover", "record cover", "label", "brochure"):
                    add_plan(plan, seen, macro, country, object_term, f"{alias} {year} {object_term}", "priority_country_year_object")

    for year in priority_years:
        for macro, country, aliases in countries:
            for alias in aliases[:2]:
                for object_term in ("poster", "advertising poster", "film poster", "book cover", "label", "brochure"):
                    add_plan(plan, seen, macro, country, object_term, f"{alias} {year} {object_term}", "country_year_object")

    for year in range(2015, 2020):
        for authority_term in AUTHORITY_TERMS:
            add_plan(plan, seen, "_infer", "_infer", "poster", f'"{year}" "{authority_term}"', "authority_year")
        for macro, country, aliases in countries:
            for alias in aliases[:2]:
                for authority_term in AUTHORITY_TERMS[:8]:
                    add_plan(plan, seen, macro, country, "poster", f"{alias} {year} {authority_term}", "country_authority_year")

    for object_term in ("poster", "advertising poster", "book cover", "label", "packaging", "brochure"):
        for macro, country, aliases in countries:
            for alias in aliases[:2]:
                add_plan(plan, seen, macro, country, object_term, f"{alias} {object_term}", "scarcity_object")

    for macro, country, aliases in countries:
        for object_term, pattern in COUNTRY_CATEGORY_PATTERNS:
            add_plan(plan, seen, macro, country, object_term, pattern.format(country=country), "country_category")

    for object_term, category in PERIOD_CATEGORIES:
        add_plan(plan, seen, "_infer", "_infer", object_term, category, "period_category")

    for year in priority_years:
        for object_term in ("poster", "advertising poster", "film poster", "book cover", "magazine cover", "label", "packaging", "brochure", "record cover"):
            add_plan(plan, seen, "_infer", "_infer", object_term, f'"{year}" "{object_term}"', "year_object")

    return plan


def distribution_gate(
    row: dict[str, str],
    object_term: str,
    country_counts: Counter[str],
    collection_counts: Counter[str],
    creator_counts: Counter[str],
    year_counts: Counter[int],
    family_counts: Counter[str],
    period_counts: Counter[str],
) -> tuple[bool, str]:
    country = row.get("source_place_text", "")
    year = row_year(row)
    period = target_period(year)
    family = object_family(row, object_term)
    collection_key = normalized_key(row.get("source_collection", ""), default="unknown_collection")
    creator_key = normalized_key(row.get("source_creator", ""), default="unknown_creator")
    nearly_done = sum(family_counts.values()) >= int(TARGET_ROWS * 0.9)
    if country_counts[country] >= COUNTRY_CAP and not nearly_done:
        return False, "country_cap"
    if collection_counts[collection_key] >= COLLECTION_CAP and not nearly_done:
        return False, "collection_cap"
    if creator_key != "unknown_creator" and creator_counts[creator_key] >= CREATOR_CAP and not nearly_done:
        return False, "creator_cap"
    if year_counts[year] >= YEAR_CAP:
        return False, "year_cap"
    if period_counts[period] >= PERIOD_CAPS.get(period, TARGET_ROWS) and not nearly_done:
        return False, "period_cap"
    if family_counts[family] >= FAMILY_CAPS.get(family, TARGET_ROWS) and not nearly_done:
        return False, "object_family_cap"
    return True, "ok"


def reseed_counters(rows: list[dict[str, str]]) -> tuple[Counter[str], Counter[str], Counter[str], Counter[int], Counter[str], Counter[str]]:
    country_counts: Counter[str] = Counter()
    collection_counts: Counter[str] = Counter()
    creator_counts: Counter[str] = Counter()
    year_counts: Counter[int] = Counter()
    family_counts: Counter[str] = Counter()
    period_counts: Counter[str] = Counter()
    for row in rows:
        country_counts[row.get("source_place_text", "")] += 1
        collection_counts[normalized_key(row.get("source_collection", ""), default="unknown_collection")] += 1
        creator_counts[normalized_key(row.get("source_creator", ""), default="unknown_creator")] += 1
        year_counts[row_year(row)] += 1
        family_counts[object_family(row, row.get("source_object_type", ""))] += 1
        period_counts[target_period(row_year(row))] += 1
    return country_counts, collection_counts, creator_counts, year_counts, family_counts, period_counts


def write_outputs(rows: list[dict[str, str]], failures: list[dict[str, str]], rejects: Counter[str]) -> None:
    rows.sort(key=lambda row: (row.get("date_start", ""), row.get("source_place_text", ""), row.get("source_title", "")))
    for index, row in enumerate(rows, 1):
        row["capture_id"] = f"FGC2026R{index:05d}"
    write_csv(RECORDS_CSV, rows, FIELDNAMES)

    source_summary = Counter(normalized_key(row.get("source_collection", ""), default="unknown_collection") for row in rows)
    source_names = {
        normalized_key(row.get("source_collection", ""), default="unknown_collection"): row.get("source_collection", "unknown")
        for row in rows
    }
    summary_rows = [
        {
            "source_name": source_names.get(source, source),
            "captured_records": str(count),
            "image_states": f"IMG03:{count}",
            "notes": "Final-gap open metadata capture; source-hosted URLs only; post-2010 stamp/event-photo exclusions applied",
        }
        for source, count in sorted(source_summary.items(), key=lambda item: (-item[1], item[0]))
    ]
    write_csv(SUMMARY_CSV, summary_rows, ["source_name", "captured_records", "image_states", "notes"])

    year_counts = Counter(row_year(row) for row in rows)
    period_counts = Counter(target_period(row_year(row)) for row in rows)
    macro_counts = Counter((row.get("source_place_text", "").split(" / ")[0] or "unmapped") for row in rows)
    country_counts = Counter(row.get("source_place_text", "unmapped") for row in rows)
    family_counts = Counter(object_family(row, row.get("source_object_type", "")) for row in rows)
    creator_counts = Counter(normalized_key(row.get("source_creator", ""), default="unknown_creator") for row in rows)

    quality_rows: list[dict[str, str]] = [
        {"metric": "records_captured", "value": str(len(rows)), "notes": "New final-gap capture records."},
        {"metric": "distinct_source_collections", "value": str(len(source_summary)), "notes": "Normalized source_collection count."},
        {"metric": "distinct_creators", "value": str(len(creator_counts)), "notes": "Normalized creator/artist count."},
        {"metric": "query_failures", "value": str(len(failures)), "notes": "Network/API failures; rows continue after failure."},
    ]
    for key, count in period_counts.most_common():
        quality_rows.append({"metric": f"period:{key}", "value": str(count), "notes": "Target-period distribution."})
    for key, count in macro_counts.most_common():
        quality_rows.append({"metric": f"macro_region:{key}", "value": str(count), "notes": "Macro-region distribution."})
    for key, count in family_counts.most_common():
        quality_rows.append({"metric": f"object_family:{key}", "value": str(count), "notes": "Object family after quality gate."})
    for key, count in year_counts.most_common(30):
        quality_rows.append({"metric": f"year:{key}", "value": str(count), "notes": "Top captured years."})
    for key, count in rejects.most_common(30):
        quality_rows.append({"metric": f"reject:{key}", "value": str(count), "notes": "Rejected before output."})
    write_csv(QUALITY_CSV, quality_rows, ["metric", "value", "notes"])
    write_csv(FAILURES_CSV, failures, ["query", "error", "detail"])

    lines = [
        "# Final Gap Open Source Capture 1955-2024 v1",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        "Scope: release-late metadata capture for underfilled temporal bands and contemporary studio/project evidence. The batch stores source metadata, source links, rights evidence, and source-hosted image URLs only.",
        "",
        "## Safety Rules",
        "",
        "- No image binaries, screenshots, cookies, sessions, or raw API payloads were saved.",
        "- IMG03 is assigned only from explicit Commons open-license extmetadata inherited from the base parser.",
        "- Post-2010 stamp/philatelic records are excluded rather than used to pad source counts.",
        "- Event photographs, memory material, conference poster sessions, and 2025-2026 access-year inflation are excluded.",
        "- Collection, creator, country, year, and object-family caps reduce repeated-source concentration.",
        "",
        "## Metrics",
        "",
        f"- Records captured: {len(rows)}",
        f"- Distinct source collections: {len(source_summary)}",
        f"- Distinct creators: {len(creator_counts)}",
        f"- Query failures: {len(failures)}",
        f"- Failure detail CSV: `{FAILURES_CSV.relative_to(ROOT)}`",
        "",
        "## Target Period Distribution",
        "",
    ]
    for key, count in period_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Macro-region Distribution", ""])
    for key, count in macro_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Object Family Distribution", ""])
    for key, count in family_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Top Countries", ""])
    for key, count in country_counts.most_common(20):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Top Years", ""])
    for key, count in year_counts.most_common(25):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Top Rejections", ""])
    for key, count in rejects.most_common(20):
        lines.append(f"- {key}: {count}")
    lines.extend(
        [
            "",
            "## Next Review",
            "",
            "- Run source coverage and temporal audits after this batch is merged into the capture pool.",
            "- Keep 2025-2026 in bug/review guard rather than release volume targets.",
            "- Review high-count source collections before surface rebuild to avoid repeated studio/platform padding.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest_rows = read_csv(MANIFEST)
    manifest_rows = [row for row in manifest_rows if row.get("run_id") != "final_gap_open_source_1955_2024_v1"]
    manifest_rows.append(
        {
            "run_id": "final_gap_open_source_1955_2024_v1",
            "run_type": "item_image_capture",
            "records_csv": str(RECORDS_CSV.relative_to(ROOT)),
            "summary_csv": str(SUMMARY_CSV.relative_to(ROOT)),
            "report": str(REPORT.relative_to(ROOT)),
            "status": "completed",
            "notes": "Final-gap target-period open metadata capture with stamp/event-photo/current-year guards.",
        }
    )
    write_csv(
        MANIFEST,
        manifest_rows,
        ["run_id", "run_type", "records_csv", "summary_csv", "report", "status", "notes"],
    )


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    CAPTURE_RUNS.mkdir(parents=True, exist_ok=True)

    rows = read_csv(RECORDS_CSV)
    failures: list[dict[str, str]] = []
    rejects: Counter[str] = Counter()
    seen_ids, seen_images = existing_keys(rows)
    seen_work_keys = existing_work_keys(rows)
    country_counts, collection_counts, creator_counts, year_counts, family_counts, period_counts = reseed_counters(rows)
    completed = completed_queries(len(rows))
    plans = query_plan()
    started = time.time()
    consecutive_failures = 0

    print(
        f"final_gap_start rows_existing={len(rows)} target={TARGET_ROWS} plans={len(plans)} completed={len(completed)}",
        flush=True,
    )
    for index, (macro, country, direction_name, object_term, query) in enumerate(plans, 1):
        if len(rows) >= TARGET_ROWS:
            break
        if query in completed:
            continue
        offset: int | str = ""
        pages_seen = 0
        before = len(rows)
        rejects_before = sum(rejects.values())
        failures_before = len(failures)
        max_pages = CATEGORY_PAGES if query.startswith("Category:") else SEARCH_PAGES
        status = "empty"
        while pages_seen < max_pages and len(rows) < TARGET_ROWS:
            url = base.search_url(query, offset=offset)
            try:
                payload = base.fetch_json(url)
            except Exception as exc:  # noqa: BLE001
                failures.append({"query": query, "error": type(exc).__name__, "detail": base.clean(str(exc), max_chars=220)})
                status = "failed"
                consecutive_failures += 1
                break
            consecutive_failures = 0
            time.sleep(REQUEST_DELAY_SECONDS)
            pages = list((payload.get("query", {}).get("pages") or {}).values())
            if not pages:
                break
            status = "completed"
            for page in sorted(pages, key=lambda item: item.get("index", 9999)):
                row = base.row_from_page(page, macro, country, direction_name, object_term, url)
                if not row:
                    rejects["base_parser_rejected"] += 1
                    continue
                ok, reason = quality_gate(row, object_term)
                if not ok:
                    rejects[reason] += 1
                    continue
                source_key = row.get("source_identifier") or row.get("source_record_url")
                image_key = row.get("image_url_detected", "").lower()
                if source_key in seen_ids or row.get("source_record_url", "").lower() in seen_ids or image_key in seen_images:
                    rejects["duplicate_existing_source_or_image"] += 1
                    continue
                object_key = work_key(row)
                if object_key in seen_work_keys:
                    rejects["duplicate_work_variant"] += 1
                    continue
                ok, reason = distribution_gate(row, object_term, country_counts, collection_counts, creator_counts, year_counts, family_counts, period_counts)
                if not ok:
                    rejects[reason] += 1
                    continue
                row["direction_id"] = "FGC2026"
                row["source_id"] = "SRC-FINAL-GAP-OPEN-1955-2024-V1"
                row["source_object_type"] = f"final-gap open image record; {object_term}; {target_period(row_year(row))}"
                row["classification_rationale"] = base.clean(
                    "Selected by final-gap target period, explicit open-license extmetadata, non-stamp object family, duplicate exclusion, and source-concentration caps.",
                    max_chars=700,
                )
                row["uncertainty_note"] = base.clean(
                    "Commons metadata can be user-maintained; verify original object date, creator, collection credit, and regional assignment before final scholarly use.",
                    max_chars=700,
                )
                rows.append(row)
                seen_ids.add(source_key)
                seen_ids.add(row.get("source_record_url", "").lower())
                seen_images.add(image_key)
                seen_work_keys.add(object_key)
                country_counts[row.get("source_place_text", "")] += 1
                collection_counts[normalized_key(row.get("source_collection", ""), default="unknown_collection")] += 1
                creator_counts[normalized_key(row.get("source_creator", ""), default="unknown_creator")] += 1
                year_counts[row_year(row)] += 1
                family_counts[object_family(row, object_term)] += 1
                period_counts[target_period(row_year(row))] += 1
                if len(rows) % CHECKPOINT_EVERY_ROWS == 0:
                    write_outputs(rows, failures, rejects)
                    print(
                        f"checkpoint rows={len(rows)} query_index={index}/{len(plans)} failures={len(failures)} rejects={sum(rejects.values())}",
                        flush=True,
                    )
                if len(rows) >= TARGET_ROWS:
                    break
            if "continue" not in payload:
                break
            cont = payload.get("continue", {})
            offset = base.clean(cont.get("gcmcontinue")) if query.startswith("Category:") else int(cont.get("gsroffset", int(offset or 0) + SEARCH_LIMIT))
            if not offset:
                break
            pages_seen += 1
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
                f"query_progress={index}/{len(plans)} rows={len(rows)} added={len(rows)-before} failures={len(failures)} rejects={sum(rejects.values())}",
                flush=True,
            )
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            print(
                f"abort_consecutive_failures={consecutive_failures} rows={len(rows)} last_query={query}",
                flush=True,
            )
            break

    write_outputs(rows, failures, rejects)
    print(f"records={len(rows)}")
    print(f"failures={len(failures)}")
    print("periods=" + ",".join(f"{key}:{value}" for key, value in Counter(target_period(row_year(row)) for row in rows).most_common()))
    print("families=" + ",".join(f"{key}:{value}" for key, value in Counter(object_family(row, row.get("source_object_type", "")) for row in rows).most_common()))
    print("rejects=" + ",".join(f"{key}:{value}" for key, value in rejects.most_common(10)))


if __name__ == "__main__":
    main()
