#!/usr/bin/env python3
"""Capture open image records from Wikimedia Commons for undercovered regions.

This is an item/image capture batch, not a source-lead registry. It stores
metadata, source links, rights evidence, and source-hosted image URLs only. No
image binaries, thumbnails, screenshots, cookies, sessions, or raw API payloads
are saved.
"""

from __future__ import annotations

import csv
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import run_midcentury_capture_1930_1970 as mc
import run_midcentury_expansion_capture_1931_1970 as mx


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

RECORDS_CSV = DATA / "capture_batch_commons_open_global_south_image_2026_records.csv"
SUMMARY_CSV = DATA / "capture_batch_commons_open_global_south_image_2026_source_summary.csv"
REPORT = DOCS / "COMMONS_OPEN_GLOBAL_SOUTH_IMAGE_CAPTURE_2026_v1.md"

ACCESS_DATE = "2026-06-06"
USER_AGENT = "ModernGDHistory/0.1 commons-open-global-south-image-capture"
TARGET_ROWS = 1400
MAX_QUERY_PAGES = 6
BROAD_MAX_QUERY_PAGES = 8
SEARCH_LIMIT = 50
REQUEST_TIMEOUT_SECONDS = 30
REQUEST_DELAY_SECONDS = 0.75
SEARCH_FALLBACK_ENABLED = True
INFER_FALLBACK_REGION: tuple[str, str] | None = None
FIELDNAMES = mx.FIELDNAMES

OPEN_LICENSE_TERMS = (
    "public domain",
    "cc0",
    "creative commons attribution",
    "creative commons attribution-share alike",
    "cc by",
    "cc-by",
)

GRAPHIC_TERMS = (
    "advertisement",
    "advertising",
    "affiche",
    "banner",
    "book cover",
    "brochure",
    "campaign",
    "cover",
    "emblem",
    "exhibition",
    "festival",
    "graphic",
    "label",
    "leaflet",
    "lithograph",
    "magazine cover",
    "newspaper",
    "packaging",
    "pamphlet",
    "pictogram",
    "placard",
    "plakat",
    "poster",
    "print",
    "propaganda",
    "publicity",
    "stamp",
    "sticker",
    "typography",
)

NOISE_TERMS = (
    "blank map",
    "coat of arms",
    "commons-logo",
    "favicon",
    "flag of",
    "icon",
    "locator map",
    "logo.svg",
    "map of",
    "nuvola",
    "symbol of",
    "wikipedia-logo",
)

REGION_SEEDS: list[tuple[str, str, str, list[str]]] = [
    ("Latin America", "Mexico", "Mexico", ["Mexico", "Mexican", "México"]),
    ("Latin America", "Brazil", "Brazil", ["Brazil", "Brazilian", "Brasil"]),
    ("Latin America", "Argentina", "Argentina", ["Argentina", "Argentine"]),
    ("Latin America", "Chile", "Chile", ["Chile", "Chilean"]),
    ("Latin America", "Colombia", "Colombia", ["Colombia", "Colombian"]),
    ("Latin America", "Peru", "Peru", ["Peru", "Peruvian"]),
    ("Latin America", "Cuba", "Cuba", ["Cuba", "Cuban"]),
    ("Latin America", "Uruguay", "Uruguay", ["Uruguay", "Uruguayan"]),
    ("Latin America", "Venezuela", "Venezuela", ["Venezuela", "Venezuelan"]),
    ("Latin America", "Bolivia", "Bolivia", ["Bolivia", "Bolivian"]),
    ("Africa", "Nigeria", "Nigeria", ["Nigeria", "Nigerian"]),
    ("Africa", "Ghana", "Ghana", ["Ghana", "Ghanaian"]),
    ("Africa", "Kenya", "Kenya", ["Kenya", "Kenyan"]),
    ("Africa", "South Africa", "South Africa", ["South Africa", "South African", "apartheid"]),
    ("Africa", "Egypt", "Egypt", ["Egypt", "Egyptian"]),
    ("Africa", "Morocco", "Morocco", ["Morocco", "Moroccan"]),
    ("Africa", "Algeria", "Algeria", ["Algeria", "Algerian"]),
    ("Africa", "Ethiopia", "Ethiopia", ["Ethiopia", "Ethiopian"]),
    ("Africa", "Tanzania", "Tanzania", ["Tanzania", "Tanzanian"]),
    ("Africa", "Senegal", "Senegal", ["Senegal", "Senegalese"]),
    ("South Asia", "India", "India", ["India", "Indian"]),
    ("South Asia", "Pakistan", "Pakistan", ["Pakistan", "Pakistani"]),
    ("South Asia", "Bangladesh", "Bangladesh", ["Bangladesh", "Bangladeshi"]),
    ("South Asia", "Sri Lanka", "Sri Lanka", ["Sri Lanka", "Sri Lankan"]),
    ("South Asia", "Nepal", "Nepal", ["Nepal", "Nepali"]),
    ("Southeast Asia", "Indonesia", "Indonesia", ["Indonesia", "Indonesian"]),
    ("Southeast Asia", "Philippines", "Philippines", ["Philippines", "Filipino", "Philippine"]),
    ("Southeast Asia", "Vietnam", "Vietnam", ["Vietnam", "Vietnamese"]),
    ("Southeast Asia", "Thailand", "Thailand", ["Thailand", "Thai"]),
    ("Southeast Asia", "Malaysia", "Malaysia", ["Malaysia", "Malaysian"]),
    ("Southeast Asia", "Singapore", "Singapore", ["Singapore"]),
    ("Middle East and North Africa", "Iran", "Iran", ["Iran", "Iranian", "Persian"]),
    ("Middle East and North Africa", "Iraq", "Iraq", ["Iraq", "Iraqi"]),
    ("Middle East and North Africa", "Lebanon", "Lebanon", ["Lebanon", "Lebanese"]),
    ("Middle East and North Africa", "Palestine", "Palestine", ["Palestine", "Palestinian"]),
    ("Middle East and North Africa", "Turkey", "Turkey", ["Turkey", "Turkish"]),
    ("East Asia", "China", "China", ["China", "Chinese", "Shanghai"]),
    ("East Asia", "Taiwan", "Taiwan", ["Taiwan", "Taiwanese"]),
    ("East Asia", "Korea", "Korea", ["Korea", "Korean"]),
    ("Eastern Europe", "Ukraine", "Ukraine", ["Ukraine", "Ukrainian"]),
    ("Eastern Europe", "Serbia", "Serbia", ["Serbia", "Serbian"]),
    ("Eastern Europe", "Romania", "Romania", ["Romania", "Romanian"]),
    ("Eastern Europe", "Bulgaria", "Bulgaria", ["Bulgaria", "Bulgarian"]),
    ("Eastern Europe", "Georgia", "Georgia", ["Georgia", "Georgian"]),
    ("Oceania and Pacific", "Pacific", "Pacific", ["Pacific", "Samoa", "Fiji", "Papua New Guinea"]),
]

OBJECT_TERMS = [
    "poster",
    "advertising poster",
    "propaganda poster",
    "travel poster",
    "film poster",
    "stamp",
    "book cover",
    "magazine cover",
    "graphic design",
    "typography",
]

CATEGORY_PATTERNS: list[tuple[str, str]] = [
    ("poster", "Category:Posters of {country}"),
    ("poster", "Category:Political posters of {country}"),
    ("poster", "Category:Propaganda posters of {country}"),
    ("poster", "Category:Film posters of {country}"),
    ("poster", "Category:Travel posters of {country}"),
    ("advertising", "Category:Advertising posters of {country}"),
    ("stamp", "Category:Stamps of {country}"),
    ("stamp", "Category:Postage stamps of {country}"),
    ("book cover", "Category:Book covers of {country}"),
    ("magazine cover", "Category:Magazine covers of {country}"),
]

EXACT_CATEGORY_QUERIES: list[tuple[str, str, str, str]] = [
    ("Middle East and North Africa", "Palestine", "poster", "Category:Pro-Palestinian posters"),
    ("Latin America", "Cuba", "poster", "Category:OSPAAAL posters"),
    ("Africa", "South Africa", "poster", "Category:Anti-apartheid posters"),
    ("Africa", "South Africa", "poster", "Category:Posters of apartheid"),
    ("East Asia", "China", "poster", "Category:Chinese propaganda posters"),
    ("East Asia", "Taiwan", "poster", "Category:Taiwanese political posters"),
    ("South Asia", "India", "poster", "Category:Posters of Bollywood films"),
    ("Southeast Asia", "Philippines", "poster", "Category:Posters of the Philippines"),
]

BROAD_CATEGORY_QUERIES: list[tuple[str, str]] = [
    ("poster", "Category:Posters"),
    ("poster", "Category:Political posters"),
    ("poster", "Category:Propaganda posters"),
    ("poster", "Category:Film posters"),
    ("poster", "Category:Travel posters"),
    ("advertising", "Category:Advertising posters"),
    ("stamp", "Category:Postage stamps"),
    ("book cover", "Category:Book covers"),
    ("magazine cover", "Category:Magazine covers"),
    ("label", "Category:Labels"),
    ("packaging", "Category:Packaging"),
    ("brochure", "Category:Brochures"),
]


def clean(value: Any, *, max_chars: int = 900) -> str:
    if isinstance(value, list):
        value = "; ".join(str(part) for part in value if part)
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", str(value or ""))
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(re.sub(r"\s+", " ", text).strip())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rsplit(" ", 1)[0] + "..."


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


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                return json.loads(response.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("unreachable fetch retry state")


def search_url(query: str, *, offset: int | str = 0, limit: int = SEARCH_LIMIT) -> str:
    params = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo|categories",
        "iiprop": "url|extmetadata|mime|size",
        "iiurlwidth": "1000",
        "cllimit": "20",
    }
    if query.startswith("Category:"):
        params.update(
            {
                "generator": "categorymembers",
                "gcmtitle": query,
                "gcmnamespace": "6",
                "gcmlimit": str(limit),
            }
        )
        if offset:
            params["gcmcontinue"] = str(offset)
    else:
        params.update(
            {
                "generator": "search",
                "gsrnamespace": "6",
                "gsrsearch": query,
                "gsrlimit": str(limit),
                "gsroffset": str(offset or 0),
            }
        )
    return "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)


def extmeta(imageinfo: dict[str, Any]) -> dict[str, str]:
    meta = imageinfo.get("extmetadata") or {}
    return {key: clean(value.get("value")) for key, value in meta.items() if isinstance(value, dict)}


def is_open(meta: dict[str, str]) -> bool:
    blob = " ".join(
        [
            meta.get("LicenseShortName", ""),
            meta.get("UsageTerms", ""),
            meta.get("License", ""),
            meta.get("Copyrighted", ""),
            meta.get("LicenseUrl", ""),
        ]
    ).lower()
    return any(term in blob for term in OPEN_LICENSE_TERMS)


def first_year(blob: str) -> int | None:
    years = [int(year) for year in re.findall(r"(?<!\d)((?:18|19|20)\d{2})(?!\d)", blob or "")]
    years = [year for year in years if 1830 <= year <= 2026]
    return min(years) if years else None


def object_year(title: str, meta: dict[str, str], cats: str) -> int | None:
    blob = " ".join(
        [
            meta.get("DateTimeOriginal", ""),
            meta.get("ObjectName", ""),
            meta.get("ImageDescription", ""),
            title,
            cats,
        ]
    )
    return first_year(blob)


def category_blob(page: dict[str, Any]) -> str:
    return " ".join(clean(cat.get("title", "")) for cat in page.get("categories", []) if isinstance(cat, dict))


def infer_region_from_blob(blob: str) -> tuple[str, str] | None:
    haystack = blob.lower()
    for macro, country, _region_term, terms in REGION_SEEDS:
        aliases = [country, *terms]
        if country == "Pacific":
            aliases = [term for term in terms if term != "Pacific"]
        for alias in aliases:
            alias = alias.strip()
            if not alias:
                continue
            if re.search(rf"(?<![a-z]){re.escape(alias.lower())}(?![a-z])", haystack):
                return macro, country if country != "Pacific" else alias
    return None


def relevant(title: str, meta: dict[str, str], cats: str) -> bool:
    blob = " ".join([title, meta.get("ObjectName", ""), meta.get("ImageDescription", ""), cats]).lower()
    if any(term in blob for term in NOISE_TERMS):
        return False
    return any(term in blob for term in GRAPHIC_TERMS)


def source_name_from_meta(pageid: str, title: str, meta: dict[str, str]) -> str:
    if title:
        return clean(f"Wikimedia Commons file source / {title} / page {pageid}", max_chars=220)
    credit = clean(meta.get("Credit") or meta.get("Source") or meta.get("Artist"), max_chars=100)
    credit = re.sub(r"https?://", "", credit)
    credit = re.sub(r"www\.", "", credit)
    credit = re.sub(r"[/?#].*", "", credit).strip()
    generic = {"", "own work", "wikimedia commons", "commons", "unknown", "unknown author", "author unknown"}
    if credit.lower() in generic or len(credit) < 3:
        credit = clean(meta.get("Artist"), max_chars=100)
    if credit.lower() in generic or len(credit) < 3:
        credit = f"Commons file {pageid}"
    return clean(f"Wikimedia Commons open source / {credit} / page {pageid}", max_chars=220)


def existing_keys() -> tuple[set[str], set[str]]:
    ids: set[str] = set()
    image_urls: set[str] = set()
    for path in sorted(DATA.glob("capture_batch_*_records.csv")):
        if path == RECORDS_CSV:
            continue
        for row in read_csv(path):
            if clean(row.get("source_identifier")):
                ids.add(clean(row.get("source_identifier")))
            if clean(row.get("source_record_url")):
                ids.add(clean(row.get("source_record_url")))
            if clean(row.get("image_url_detected")):
                image_urls.add(clean(row.get("image_url_detected")).lower())
    return ids, image_urls


def query_plan() -> list[tuple[str, str, str, str, str]]:
    plan: list[tuple[str, str, str, str, str]] = []
    seen_queries: set[str] = set()

    def append_plan(macro: str, country: str, object_term: str, query: str) -> None:
        if query in seen_queries:
            return
        seen_queries.add(query)
        direction_name = re.sub(r"[^a-z0-9]+", "_", f"commons_{country}_{object_term}".lower()).strip("_")
        plan.append((macro, country, direction_name, object_term, query))

    for macro, country, object_term, query in EXACT_CATEGORY_QUERIES:
        append_plan(macro, country, object_term, query)

    for object_term, query in BROAD_CATEGORY_QUERIES:
        append_plan("_infer", "_infer", object_term, query)

    for macro, country, region_term, terms in REGION_SEEDS:
        for object_term, pattern in CATEGORY_PATTERNS:
            append_plan(macro, country, object_term, pattern.format(country=country))
        if SEARCH_FALLBACK_ENABLED:
            for object_term in OBJECT_TERMS:
                query = f'"{region_term}" "{object_term}"'
                append_plan(macro, country, object_term, query)
            for term in terms[:2]:
                for object_term in ("poster", "advertising"):
                    query = f'"{term}" "{object_term}"'
                    append_plan(macro, country, object_term, query)
    return plan


def row_from_page(page: dict[str, Any], macro: str, country: str, direction_name: str, object_term: str, api_url: str) -> dict[str, str] | None:
    infos = page.get("imageinfo") or []
    if not infos:
        return None
    info = infos[0]
    title = clean(page.get("title", "")).replace("File:", "", 1)
    if title.lower().endswith((".djvu", ".pdf", ".svg")):
        return None
    if not str(info.get("mime", "")).startswith("image/"):
        return None
    meta = extmeta(info)
    cats = category_blob(page)
    blob = " ".join([title, meta.get("ObjectName", ""), meta.get("ImageDescription", ""), cats])
    if country == "_infer":
        inferred = infer_region_from_blob(blob)
        if not inferred:
            if INFER_FALLBACK_REGION is None:
                return None
            inferred = INFER_FALLBACK_REGION
        macro, country = inferred
    if not is_open(meta) or not relevant(title, meta, cats):
        return None
    image_url = clean(info.get("thumburl") or info.get("url"))
    source_url = clean(info.get("descriptionurl") or info.get("descriptionshorturl"))
    if not image_url or not source_url:
        return None
    pageid = str(page.get("pageid") or source_url)
    year = object_year(title, meta, cats)
    if year is None:
        return None
    license_label = clean(meta.get("LicenseShortName") or meta.get("UsageTerms") or meta.get("License"))
    rights = mc.image_fields(
        "IMG03",
        f"Wikimedia Commons open-license metadata: {license_label}.",
        image_url=image_url,
        viewer=source_url,
        confidence="high",
        rights_review_required=False,
        local_copy_permitted=False,
        note="Use source-hosted Commons image URL with attribution and source link; no local image copy.",
    )
    description = clean(meta.get("ImageDescription") or meta.get("ObjectName") or title, max_chars=1400)
    source_name = source_name_from_meta(pageid, title, meta)
    source_text = clean(
        "; ".join(
            part
            for part in [
                meta.get("ObjectName"),
                meta.get("DateTimeOriginal"),
                meta.get("DateTime"),
                meta.get("Credit"),
                meta.get("Source"),
                cats,
            ]
            if part
        ),
        max_chars=1500,
    )
    row = {
        "capture_id": "",
        "direction_id": "CGS2026",
        "direction_name": direction_name,
        "source_id": "SRC-COMMONS-GLOBAL-SOUTH-2026",
        "source_name": source_name,
        "source_api_url": api_url,
        "capture_status": "captured",
        "source_identifier": pageid,
        "source_record_url": source_url,
        "source_title": title,
        "source_creator": clean(meta.get("Artist"), max_chars=500),
        "source_date_text": str(year),
        "date_start": str(year),
        "date_end": str(year),
        "source_place_text": f"{macro} / {country}",
        "source_object_type": f"open image record; {object_term}",
        "source_medium": "source-hosted open image; graphic design / visual communication candidate",
        "source_collection": clean(meta.get("Credit") or "Wikimedia Commons", max_chars=500),
        "source_description": description,
        "source_notes": source_text,
        "source_subjects": clean("; ".join([macro, country, object_term, cats]), max_chars=1500),
        "source_rights_text": clean("; ".join([license_label, meta.get("UsageTerms", ""), meta.get("LicenseUrl", "")])),
        "rights_uri": clean(meta.get("LicenseUrl")),
        "rights_basis": clean(f"Commons extmetadata license fields identify this file as {license_label}; source file page retained for review."),
        "raw_json_path": "",
        "access_date": ACCESS_DATE,
        **rights,
    }
    row["image_expectation"] = "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["source_description_raw"] = description
    row["ocr_or_excerpt"] = description
    row["editorial_summary"] = clean(f"{title} is an open-license Commons image record linked to {macro} / {country}. {description}", max_chars=900)
    row["historical_context_note"] = clean(
        f"This open-image record strengthens undercovered {macro} / {country} visual evidence while preserving the Commons source page and any credited source/author.",
        max_chars=700,
    )
    row["classification_rationale"] = clean(
        "Selected by Commons search, open-license extmetadata, visual-communication term match, duplicate exclusion, and source-derived text availability.",
        max_chars=700,
    )
    row["uncertainty_note"] = "Commons metadata can be user-maintained; verify object date, original creator, and source credit before final scholarly use."
    row["citation_basis"] = f"Wikimedia Commons. {title}. {source_url}. Accessed {ACCESS_DATE}."
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return {field: clean(row.get(field, ""), max_chars=2500) for field in FIELDNAMES}


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    existing_ids, existing_images = existing_keys()
    seen_ids = set(existing_ids)
    seen_images = set(existing_images)
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    query_counts: Counter[str] = Counter()
    plans = query_plan()
    started = time.time()

    for index, (macro, country, direction_name, object_term, query) in enumerate(plans, 1):
        if len(rows) >= TARGET_ROWS:
            break
        offset: int | str = ""
        pages_seen = 0
        max_query_pages = BROAD_MAX_QUERY_PAGES if country == "_infer" else MAX_QUERY_PAGES
        rows_before_query = len(rows)
        while pages_seen < max_query_pages and len(rows) < TARGET_ROWS:
            url = search_url(query, offset=offset)
            try:
                payload = fetch_json(url)
            except Exception as exc:  # noqa: BLE001
                failures.append({"query": query, "error": type(exc).__name__, "detail": clean(str(exc), max_chars=180)})
                break
            time.sleep(REQUEST_DELAY_SECONDS)
            pages = list((payload.get("query", {}).get("pages") or {}).values())
            if not pages:
                break
            for page in sorted(pages, key=lambda item: item.get("index", 9999)):
                row = row_from_page(page, macro, country, direction_name, object_term, url)
                if not row:
                    continue
                source_key = row["source_identifier"] or row["source_record_url"]
                image_key = row["image_url_detected"].lower()
                if source_key in seen_ids or image_key in seen_images:
                    continue
                seen_ids.add(source_key)
                seen_images.add(image_key)
                rows.append(row)
                query_counts[f"{macro} / {country}"] += 1
                if len(rows) >= TARGET_ROWS:
                    break
            if "continue" not in payload:
                break
            continue_payload = payload.get("continue", {})
            if query.startswith("Category:"):
                offset = clean(continue_payload.get("gcmcontinue"))
            else:
                offset = int(continue_payload.get("gsroffset", int(offset or 0) + SEARCH_LIMIT))
            if not offset:
                break
            pages_seen += 1
        if index % 10 == 0 or len(rows) > rows_before_query or len(rows) >= TARGET_ROWS:
            added = len(rows) - rows_before_query
            print(f"query_progress={index}/{len(plans)} rows={len(rows)} added={added} failures={len(failures)}", flush=True)

    rows.sort(key=lambda row: (row["source_place_text"], row["date_start"], row["source_title"]))
    for index, row in enumerate(rows, 1):
        row["capture_id"] = f"CGS2026R{index:04d}"

    write_csv(RECORDS_CSV, rows, FIELDNAMES)
    by_source = Counter(row["source_name"] for row in rows)
    summary_rows = [
        {
            "source_name": source,
            "captured_records": str(count),
            "image_states": "IMG03:" + str(count),
            "notes": "Open-license Commons metadata; no image binary downloaded",
        }
        for source, count in sorted(by_source.items())
    ]
    write_csv(SUMMARY_CSV, summary_rows, ["source_name", "captured_records", "image_states", "notes"])

    macro_counts = Counter(row["source_place_text"].split(" / ")[0] for row in rows)
    country_counts = Counter(row["source_place_text"] for row in rows)
    text_lengths = [len(" ".join([row["source_description"], row["source_notes"], row["source_subjects"], row["ocr_or_excerpt"]]).strip()) for row in rows]
    lines = [
        "# Commons Open Global South Image Capture 2026 v1",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        "Scope: Wikimedia Commons open-license image records for undercovered regions. This batch stores metadata, rights evidence, source links, and source-hosted image URLs only.",
        "",
        "## Metrics",
        "",
        f"- Records captured: {len(rows)}",
        f"- Distinct active source names: {len(by_source)}",
        f"- Image states: IMG03 only",
        f"- Query failures: {len(failures)}",
        f"- Runtime seconds: {time.time() - started:.1f}",
        f"- Minimum source-derived text length: {min(text_lengths) if text_lengths else 0}",
        f"- Median source-derived text length: {sorted(text_lengths)[len(text_lengths)//2] if text_lengths else 0}",
        "",
        "## Macro-region Distribution",
        "",
    ]
    for macro, count in macro_counts.most_common():
        lines.append(f"- {macro}: {count}")
    lines.extend(["", "## Top Country/Region Buckets", ""])
    for country, count in country_counts.most_common(30):
        lines.append(f"- {country}: {count}")
    lines.extend(["", "## Query Failures", ""])
    for failure in failures[:20]:
        lines.append(f"- {failure.get('error')}: {failure.get('query')} ({failure.get('detail', '')})")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No image binaries were downloaded.",
            "- No raw API payloads, cookies, browser sessions, screenshots, or local image files were saved.",
            "- `IMG03` is assigned only when Commons extmetadata exposes open-license evidence.",
            "- Commons remains a source/rights-visible display layer; original creator/source credit still requires scholarly review.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"records={len(rows)}")
    print(f"distinct_source_names={len(by_source)}")
    print("macro_regions=" + ",".join(f"{key}:{value}" for key, value in macro_counts.most_common()))
    print(f"wrote {RECORDS_CSV.relative_to(ROOT)}")
    print(f"wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
