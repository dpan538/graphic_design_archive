#!/usr/bin/env python3
"""Capture region-balanced Commons open image records with stricter relevance.

This is an item/image capture batch. It stores metadata, source links, rights
evidence, source-derived text, and source-hosted image URLs only. It does not
download image binaries, thumbnails, screenshots, raw API payloads, cookies, or
browser sessions.
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
CAPTURE_RUNS = DATA / "capture_runs"

RECORDS_CSV = DATA / "capture_batch_commons_open_region_balance_image_2026_v2_records.csv"
SUMMARY_CSV = DATA / "capture_batch_commons_open_region_balance_image_2026_v2_source_summary.csv"
QUALITY_CSV = DATA / "commons_open_region_balance_image_2026_v2_quality.csv"
REPORT = DOCS / "COMMONS_OPEN_REGION_BALANCE_IMAGE_CAPTURE_2026_v2.md"
MANIFEST = CAPTURE_RUNS / "capture_run_manifest_v1.csv"

ACCESS_DATE = "2026-06-12"
base.ACCESS_DATE = ACCESS_DATE
FIELDNAMES = base.FIELDNAMES
TARGET_ROWS = 800
PREFLIGHT_QUERIES = 36
PREFLIGHT_MIN_ROWS = 18
MAX_QUERIES = 1200
SEARCH_LIMIT = 50
CATEGORY_PAGES = 2
SEARCH_PAGES = 1
REQUEST_DELAY_SECONDS = 0.2
CHECKPOINT_EVERY_ROWS = 50
COUNTRY_CAP = 85
MACRO_CAPS = {
    "Africa": 190,
    "South Asia": 150,
    "Southeast Asia": 150,
    "Middle East and North Africa": 150,
    "Eastern Europe / Caucasus": 110,
    "Central Asia": 80,
    "Latin America / Caribbean": 130,
    "Oceania / Pacific": 60,
    "East Asia": 80,
}
MACRO_ORDER = [
    "Africa",
    "South Asia",
    "Southeast Asia",
    "Middle East and North Africa",
    "Eastern Europe / Caucasus",
    "Central Asia",
    "Latin America / Caribbean",
    "Oceania / Pacific",
    "East Asia",
]

OBJECT_TERMS = [
    "poster",
    "political poster",
    "propaganda poster",
    "advertising poster",
    "film poster",
    "travel poster",
    "book cover",
    "magazine cover",
    "postage stamp",
    "packaging",
    "label",
    "brochure",
    "pamphlet",
    "typography",
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
    ("South Asia", "Bangladesh", ["Bangladesh", "Bangladeshi"]),
    ("South Asia", "Pakistan", ["Pakistan", "Pakistani"]),
    ("South Asia", "Nepal", ["Nepal", "Nepali"]),
    ("South Asia", "Sri Lanka", ["Sri Lanka", "Sri Lankan"]),
    ("South Asia", "India", ["India", "Indian"]),
    ("Southeast Asia", "Indonesia", ["Indonesia", "Indonesian"]),
    ("Southeast Asia", "Philippines", ["Philippines", "Filipino", "Philippine"]),
    ("Southeast Asia", "Vietnam", ["Vietnam", "Vietnamese"]),
    ("Southeast Asia", "Thailand", ["Thailand", "Thai"]),
    ("Southeast Asia", "Malaysia", ["Malaysia", "Malaysian"]),
    ("Southeast Asia", "Singapore", ["Singapore"]),
    ("Middle East and North Africa", "Iran", ["Iran", "Iranian", "Persian"]),
    ("Middle East and North Africa", "Iraq", ["Iraq", "Iraqi"]),
    ("Middle East and North Africa", "Lebanon", ["Lebanon", "Lebanese"]),
    ("Middle East and North Africa", "Palestine", ["Palestine", "Palestinian"]),
    ("Middle East and North Africa", "Turkey", ["Turkey", "Turkish"]),
    ("Eastern Europe / Caucasus", "Ukraine", ["Ukraine", "Ukrainian"]),
    ("Eastern Europe / Caucasus", "Georgia", ["Georgia", "Georgian"]),
    ("Eastern Europe / Caucasus", "Armenia", ["Armenia", "Armenian"]),
    ("Eastern Europe / Caucasus", "Azerbaijan", ["Azerbaijan", "Azerbaijani"]),
    ("Central Asia", "Kazakhstan", ["Kazakhstan", "Kazakh"]),
    ("Central Asia", "Uzbekistan", ["Uzbekistan", "Uzbek"]),
    ("Central Asia", "Kyrgyzstan", ["Kyrgyzstan", "Kyrgyz"]),
    ("Latin America / Caribbean", "Colombia", ["Colombia", "Colombian"]),
    ("Latin America / Caribbean", "Peru", ["Peru", "Peruvian"]),
    ("Latin America / Caribbean", "Cuba", ["Cuba", "Cuban", "OSPAAAL"]),
    ("Latin America / Caribbean", "Uruguay", ["Uruguay", "Uruguayan"]),
    ("Latin America / Caribbean", "Venezuela", ["Venezuela", "Venezuelan"]),
    ("Oceania / Pacific", "Samoa", ["Samoa", "Samoan"]),
    ("Oceania / Pacific", "Fiji", ["Fiji", "Fijian"]),
    ("East Asia", "Taiwan", ["Taiwan", "Taiwanese"]),
    ("East Asia", "Korea", ["Korea", "Korean", "South Korea"]),
]

CATEGORY_PATTERNS = [
    ("poster", "Category:Posters of {country}"),
    ("poster", "Category:Political posters of {country}"),
    ("poster", "Category:Propaganda posters of {country}"),
    ("poster", "Category:Film posters of {country}"),
    ("poster", "Category:Travel posters of {country}"),
    ("advertising poster", "Category:Advertising posters of {country}"),
    ("postage stamp", "Category:Postage stamps of {country}"),
    ("book cover", "Category:Book covers of {country}"),
    ("magazine cover", "Category:Magazine covers of {country}"),
    ("packaging", "Category:Packaging of {country}"),
    ("label", "Category:Labels of {country}"),
]

EXACT_CATEGORIES = [
    ("Middle East and North Africa", "Palestine", "poster", "Category:Pro-Palestinian posters"),
    ("Latin America / Caribbean", "Cuba", "poster", "Category:OSPAAAL posters"),
    ("Africa", "South Africa", "poster", "Category:Anti-apartheid posters"),
    ("East Asia", "China", "poster", "Category:Chinese propaganda posters"),
    ("South Asia", "India", "poster", "Category:Posters of Bollywood films"),
    ("Southeast Asia", "Philippines", "poster", "Category:Posters of the Philippines"),
]

STRONG_GRAPHIC_TERMS = (
    "advertisement",
    "advertising",
    "affiche",
    "book cover",
    "brochure",
    "campaign poster",
    "cartel",
    "cover",
    "film poster",
    "graphic design",
    "label",
    "leaflet",
    "magazine cover",
    "packaging",
    "pamphlet",
    "plakat",
    "poster",
    "postage stamp",
    "propaganda poster",
    "stamp",
    "typography",
    "visual communication",
)

REJECT_TERMS = (
    "aerial photograph",
    "album cover of a sound recording",
    "architecture",
    "building",
    "bust",
    "cathedral",
    "church",
    "coin",
    "commemorative medal",
    "locator map",
    "map of",
    "painting",
    "photograph of",
    "portrait",
    "sculpture",
    "statue",
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


def query_plan() -> list[tuple[str, str, str, str, str]]:
    plan: list[tuple[str, str, str, str, str]] = []
    seen: set[str] = set()
    country_rows = ordered_countries()

    def add(macro: str, country: str, object_term: str, query: str) -> None:
        if query in seen:
            return
        seen.add(query)
        direction = re.sub(r"[^a-z0-9]+", "_", f"region_balance_{country}_{object_term}".lower()).strip("_")
        plan.append((macro, country, direction, object_term, query))

    for macro, country, object_term, query in EXACT_CATEGORIES:
        add(macro, country, object_term, query)

    for macro, country, aliases in country_rows:
        for alias in aliases[:3]:
            for object_term in OBJECT_TERMS:
                add(macro, country, object_term, f'"{alias}" "{object_term}"')
    for macro, country, aliases in country_rows:
        for object_term, pattern in CATEGORY_PATTERNS:
            add(macro, country, object_term, pattern.format(country=country))
    for macro, country, aliases in country_rows:
        for alias in aliases[:2]:
            for year in range(2026, 1999, -1):
                for object_term in ("poster", "graphic design", "typography", "advertising poster", "film poster", "book cover"):
                    add(macro, country, object_term, f'"{alias}" "{year}" "{object_term}"')
            for year in range(1999, 1969, -1):
                for object_term in ("poster", "advertising poster", "film poster", "postage stamp"):
                    add(macro, country, object_term, f'"{alias}" "{year}" "{object_term}"')
    return plan


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


def strong_relevance(row: dict[str, str], object_term: str) -> tuple[bool, str]:
    # Only source-derived fields can prove graphic/design relevance. Do not
    # count project-assigned object_type/source_subjects, or the query term
    # starts confirming itself.
    blob = " ".join([row.get("source_title", ""), row.get("source_description", ""), row.get("source_notes", "")]).lower()
    title = row.get("source_title", "").lower()
    notes = row.get("source_notes", "").lower()
    description = row.get("source_description", "").lower()
    title_direct = any(
        term in title
        for term in (
            "advertisement",
            "advertising",
            "affiche",
            "book cover",
            "brochure",
            "campaign poster",
            "cartel",
            "film poster",
            "front cover",
            "magazine cover",
            "pamphlet",
            "plakat",
            "poster",
            "postage stamp",
            "typography",
        )
    )
    category_direct = any(
        term in notes
        for term in (
            "category:advertisements",
            "category:advertising posters",
            "category:book covers",
            "category:brochures",
            "category:film posters",
            "category:labels",
            "category:magazine covers",
            "category:packaging",
            "category:pamphlets",
            "category:political posters",
            "category:postage stamps",
            "category:posters",
            "category:propaganda posters",
            "category:travel posters",
            "category:typography",
        )
    )
    phrase_direct = any(
        term in description
        for term in (
            "advertising poster",
            "book cover",
            "campaign poster",
            "election poster",
            "magazine cover",
            "packaging label",
            "poster for",
            "postage stamp",
            "type specimen",
            "typographic",
            "typography",
        )
    )
    label_direct = ("label" in title or "category:labels" in notes or "packaging label" in description) and "record label" not in blob
    stamp_direct = "stamp" in title or "category:postage stamps" in notes or "postage stamp" in description
    if any(term in blob for term in REJECT_TERMS):
        if not (title_direct or category_direct or phrase_direct or stamp_direct or label_direct):
            return False, "reject_non_graphic_object"
    if object_term in {"postage stamp", "stamp"} and stamp_direct:
        return True, "stamp_term"
    if title_direct:
        return True, "title_graphic_term"
    if category_direct:
        return True, "category_graphic_term"
    if phrase_direct:
        return True, "metadata_graphic_term"
    if label_direct:
        return True, "label_graphic_term"
    return False, "weak_graphic_evidence"


def write_outputs(
    rows: list[dict[str, str]],
    failures: list[dict[str, str]],
    rejects: Counter[str],
    started: float,
    preflight_rows: int,
    *,
    update_run_manifest: bool,
) -> None:
    rows.sort(key=lambda row: (row["source_place_text"], row["date_start"], row["source_title"]))
    for index, row in enumerate(rows, 1):
        row["capture_id"] = f"CRB2026V2R{index:04d}"

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
    macro_counts = Counter(row["source_place_text"].split(" / ")[0] for row in rows)
    country_counts = Counter(row["source_place_text"] for row in rows)
    text_lengths = [
        len(" ".join([row["source_description"], row["source_notes"], row["source_subjects"], row["ocr_or_excerpt"]]).strip())
        for row in rows
    ]
    quality_rows = [
        {"metric": "records_captured", "value": str(len(rows))},
        {"metric": "distinct_active_source_names", "value": str(len(by_source))},
        {"metric": "query_failures", "value": str(len(failures))},
        {"metric": "preflight_rows_at_query_limit", "value": str(preflight_rows)},
        {"metric": "minimum_source_derived_text_length", "value": str(min(text_lengths) if text_lengths else 0)},
        {"metric": "median_source_derived_text_length", "value": str(sorted(text_lengths)[len(text_lengths) // 2] if text_lengths else 0)},
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
        "# Commons Open Region Balance Image Capture 2026 v2",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        "Scope: region-balanced Commons open-license source pages with explicit object-year evidence and stricter graphic-object filtering. Metadata/source links/source-hosted image URLs only.",
        "",
        "## Metrics",
        "",
        f"- Records captured: {len(rows)}",
        f"- Distinct active source names: {len(by_source)}",
        f"- Image states: {', '.join(f'{key}:{value}' for key, value in sorted(image_counts.items())) or 'none'}",
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
    for macro, count in macro_counts.most_common():
        lines.append(f"- {macro}: {count}")
    lines.extend(["", "## Top Country/Region Buckets", ""])
    for country, count in country_counts.most_common(35):
        lines.append(f"- {country}: {count}")
    lines.extend(["", "## Filter Diagnostics", ""])
    for key, value in rejects.most_common(15):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Query Failures", ""])
    if failures:
        for failure in failures[:20]:
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
            "- Impact and source priority are internal triage only.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if update_run_manifest:
        update_manifest(len(rows), len(by_source), image_counts)


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


def within_distribution_caps(row: dict[str, str], macro_counts: Counter[str], country_counts: Counter[str]) -> bool:
    country_key = row["source_place_text"]
    macro_key = country_key.split(" / ")[0]
    if country_counts[country_key] >= COUNTRY_CAP:
        return False
    if macro_counts[macro_key] >= MACRO_CAPS.get(macro_key, TARGET_ROWS):
        return False
    return True


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
    run_id = "commons_open_region_balance_image_2026_v2"
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
            "notes": "Region-balanced Commons open image capture; strict graphic-object filter; no image binaries or raw payloads saved.",
        }
    )
    write_csv(MANIFEST, rows, fields)


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    seen_ids, seen_images = existing_keys()
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    rejects: Counter[str] = Counter()
    query_counts: Counter[str] = Counter()
    macro_caps: Counter[str] = Counter()
    country_caps: Counter[str] = Counter()
    started = time.time()
    plans = query_plan()
    preflight_rows = 0
    last_checkpoint_rows = 0

    for index, (macro, country, direction_name, object_term, query) in enumerate(plans, 1):
        if len(rows) >= TARGET_ROWS:
            break
        if index > MAX_QUERIES:
            failures.append({"query": "query_plan_limit", "error": "QueryPlanLimitReached", "detail": str(MAX_QUERIES)})
            break
        offset: int | str = ""
        pages_seen = 0
        before = len(rows)
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
            for page in sorted(pages, key=lambda item: item.get("index", 9999)):
                row = base.row_from_page(page, macro, country, direction_name, object_term, url)
                if not row:
                    rejects["base_filter"] += 1
                    continue
                ok, reason = strong_relevance(row, object_term)
                if not ok:
                    rejects[reason] += 1
                    continue
                source_key = row["source_identifier"] or row["source_record_url"]
                image_key = row["image_url_detected"].lower()
                if source_key in seen_ids or image_key in seen_images:
                    rejects["duplicate"] += 1
                    continue
                if not within_distribution_caps(row, macro_caps, country_caps):
                    rejects["distribution_cap"] += 1
                    continue
                row["direction_id"] = "CRB2026V2"
                row["source_id"] = "SRC-COMMONS-REGION-BALANCE-2026-V2"
                row["source_object_type"] = f"region-balanced open image record; {object_term}"
                row["classification_rationale"] = base.clean(
                    "Selected by region-balanced Commons query, open-license extmetadata, strict graphic-object filter, duplicate exclusion, and explicit object-year evidence.",
                    max_chars=700,
                )
                row["uncertainty_note"] = (
                    "Commons metadata can be user-maintained; verify object date, original creator, source credit, and visual-communication relevance before final scholarly use."
                )
                seen_ids.add(source_key)
                seen_images.add(image_key)
                rows.append(row)
                query_counts[f"{macro} / {country}"] += 1
                country_caps[row["source_place_text"]] += 1
                macro_caps[row["source_place_text"].split(" / ")[0]] += 1
                if len(rows) - last_checkpoint_rows >= CHECKPOINT_EVERY_ROWS:
                    write_outputs(rows, failures, rejects, started, preflight_rows, update_run_manifest=False)
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
        if index == PREFLIGHT_QUERIES and len(rows) < PREFLIGHT_MIN_ROWS:
            preflight_rows = len(rows)
            failures.append(
                {
                    "query": "preflight",
                    "error": "LowYieldPreflight",
                    "detail": f"{len(rows)} rows after {PREFLIGHT_QUERIES} queries; continuing with guarded full run.",
                }
            )
        elif index == PREFLIGHT_QUERIES:
            preflight_rows = len(rows)
        if index % 20 == 0 or len(rows) > before or len(rows) >= TARGET_ROWS:
            print(f"region_balance_progress={index}/{len(plans)} rows={len(rows)} added={len(rows)-before} failures={len(failures)}", flush=True)

    write_outputs(rows, failures, rejects, started, preflight_rows, update_run_manifest=True)

    period_counts = Counter(period_band(row) for row in rows)
    macro_counts = Counter(row["source_place_text"].split(" / ")[0] for row in rows)
    by_source = Counter(row["source_name"] for row in rows)

    print(f"records={len(rows)}")
    print(f"distinct_source_names={len(by_source)}")
    print("periods=" + ",".join(f"{key}:{value}" for key, value in period_counts.most_common()))
    print("macro_regions=" + ",".join(f"{key}:{value}" for key, value in macro_counts.most_common()))
    print("rejects=" + ",".join(f"{key}:{value}" for key, value in rejects.most_common()))
    print(f"wrote {RECORDS_CSV.relative_to(ROOT)}")
    print(f"wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"wrote {QUALITY_CSV.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")
    print(f"updated {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
