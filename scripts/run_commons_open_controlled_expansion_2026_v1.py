#!/usr/bin/env python3
"""Capture controlled Commons open records for late release expansion.

This batch is designed to raise active source count, source coverage
time-balance, object source-visible coverage, and verified-open image coverage
together. It stores metadata, source links, rights evidence, and source-hosted
image URLs only. It does not download image binaries, thumbnails, screenshots,
raw API payloads, cookies, or browser sessions.

Unlike the earlier release-gate expansion, this controlled pass uses the
expanded project geography seed list, checkpointed state, object-family caps,
and a broader non-stamp object plan. Any remaining weak, duplicate, or
over-broad records are expected to be removed by the cleaning audit before
public rebuild.
"""

from __future__ import annotations

import csv
import os
import re
import time
from collections import Counter
from pathlib import Path

import run_commons_open_global_south_image_capture_2026_v1 as base
import run_commons_open_region_balance_image_capture_2026_v3 as v3


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

CAPTURE_RUNS = DATA / "capture_runs"

RECORDS_CSV = DATA / "capture_batch_commons_open_controlled_expansion_2026_v1_records.csv"
SUMMARY_CSV = DATA / "capture_batch_commons_open_controlled_expansion_2026_v1_source_summary.csv"
QUALITY_CSV = DATA / "commons_open_controlled_expansion_2026_v1_quality.csv"
STATE_CSV = DATA / "commons_open_controlled_expansion_2026_v1_query_state.csv"
REPORT = DOCS / "COMMONS_OPEN_CONTROLLED_EXPANSION_2026_v1.md"
MANIFEST = CAPTURE_RUNS / "capture_run_manifest_v1.csv"

ACCESS_DATE = "2026-06-13"
base.ACCESS_DATE = ACCESS_DATE
FIELDNAMES = base.FIELDNAMES
BASE_TARGET_ROWS = 4700
TARGET_ROWS = int(os.environ.get("COMMONS_OPEN_CONTROLLED_TARGET_ROWS", str(BASE_TARGET_ROWS)))
SEARCH_LIMIT = 50
MAX_SEARCH_PAGES = 16
REQUEST_DELAY_SECONDS = 0.12
CHECKPOINT_EVERY_ROWS = 100
GLOBAL_SEARCH_START_OFFSET = 2000

WEAK_PERIOD_YEARS = list(range(1970, 2001)) + list(range(1930, 1970)) + list(range(1830, 1930, 2))
SECONDARY_YEARS = list(range(2001, 2027))
COUNTRY_PRIORITY_YEARS = [1930, 1935, 1940, 1945, 1950, 1955, 1960, 1965, 1970, 1975, 1980, 1985, 1990, 1995, 2000, 2010, 2020]
OBJECT_TERMS = [
    "advertisement",
    "label",
    "book cover",
    "magazine cover",
    "trade card",
    "brochure",
    "pamphlet",
    "leaflet",
    "advertising poster",
    "film poster",
    "matchbox label",
    "packaging",
    "type specimen",
    "letterhead",
    "poster",
    "stamp",
]
OBJECT_CAPS = {
    "stamp": 1800,
    "film poster": 900,
    "poster": 1350,
    "advertising poster": 650,
    "advertisement": 650,
    "book cover": 850,
    "magazine cover": 460,
    "trade card": 520,
    "label": 650,
    "matchbox label": 420,
    "leaflet": 520,
    "pamphlet": 520,
    "brochure": 520,
    "packaging": 520,
    "type specimen": 360,
    "letterhead": 320,
}
YEAR_CAPS = {2026: 80, 2025: 140, 2024: 180}
GLOBAL_FALLBACK_CAP = 1600
COUNTRY_CAP = 260
MACRO_CAP = 900

BROAD_CATEGORIES = [
    ("advertising poster", "Category:Art Nouveau posters"),
    ("poster", "Category:1970s posters"),
    ("poster", "Category:1980s posters"),
    ("poster", "Category:1990s posters"),
    ("poster", "Category:2000s posters"),
    ("poster", "Category:1930s posters"),
    ("poster", "Category:1940s posters"),
    ("poster", "Category:1950s posters"),
    ("poster", "Category:1960s posters"),
    ("poster", "Category:1920s posters"),
    ("poster", "Category:1910s posters"),
    ("film poster", "Category:Film posters"),
    ("book cover", "Category:Book covers"),
    ("magazine cover", "Category:Magazine covers"),
    ("advertising", "Category:1970s advertisements"),
    ("advertising", "Category:1980s advertisements"),
    ("advertising", "Category:1990s advertisements"),
    ("advertisement", "Category:19th-century advertisements"),
    ("trade card", "Category:Trade cards"),
    ("label", "Category:Labels"),
    ("matchbox label", "Category:Matchbox labels"),
    ("type specimen", "Category:Type specimens"),
    ("stamp", "Category:1970s postage stamps"),
    ("stamp", "Category:1980s postage stamps"),
    ("stamp", "Category:1990s postage stamps"),
]

YEAR_CATEGORY_OBJECTS = [
    ("stamp", "Category:{year} postage stamps"),
    ("book cover", "Category:{year} book covers"),
    ("poster", "Category:{year} posters"),
    ("film poster", "Category:{year} film posters"),
    ("advertisement", "Category:{year} advertisements"),
    ("magazine cover", "Category:{year} magazine covers"),
    ("label", "Category:{year} labels"),
]

BROAD_SEARCHES = [
    ("advertisement", '"advertisement"'),
    ("advertisement", '"advertising"'),
    ("book cover", '"book cover"'),
    ("magazine cover", '"magazine cover"'),
    ("label", '"label"'),
    ("trade card", '"trade card"'),
    ("poster", '"poster"'),
    ("film poster", '"film poster"'),
    ("brochure", '"brochure"'),
    ("pamphlet", '"pamphlet"'),
    ("type specimen", '"type specimen"'),
    ("letterhead", '"letterhead"'),
    ("stamp", '"postage stamp"'),
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


def expanded_region_seeds() -> list[tuple[str, str, str, list[str]]]:
    rows: list[tuple[str, str, str, list[str]]] = []
    seen: set[tuple[str, str]] = set()
    for macro, country, aliases in v3.COUNTRIES:
        rows.append((macro, country, country, aliases))
        seen.add((macro, country))
    for macro, country, region_term, terms in base.REGION_SEEDS:
        if (macro, country) not in seen:
            rows.append((macro, country, region_term, terms))
            seen.add((macro, country))
    return rows


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
    rows = [current for current in read_csv(STATE_CSV) if current.get("query") != row.get("query")]
    rows.append(row)
    write_csv(STATE_CSV, rows, fields)


def row_year(row: dict[str, str]) -> int:
    try:
        return int(float(row.get("date_end") or row.get("date_start") or "0"))
    except ValueError:
        return 0


def controlled_object_family(row: dict[str, str], object_term: str) -> str:
    blob = " ".join([object_term, row.get("source_object_type", ""), row.get("source_title", ""), row.get("source_subjects", "")]).lower()
    if "postage stamp" in blob or re.search(r"\bstamps?\b", blob):
        return "stamp"
    if "film poster" in blob or "movie poster" in blob or "cinema poster" in blob:
        return "film poster"
    if "advertising poster" in blob:
        return "advertising poster"
    if "poster" in blob or "affiche" in blob or "plakat" in blob:
        return "poster"
    if "book cover" in blob or "dust jacket" in blob:
        return "book cover"
    if "magazine cover" in blob or "journal cover" in blob:
        return "magazine cover"
    if "trade card" in blob:
        return "trade card"
    if "matchbox" in blob:
        return "matchbox label"
    if "label" in blob or "packaging" in blob or "package" in blob:
        return "label"
    if "advertisement" in blob or "advertising" in blob:
        return "advertisement"
    if "brochure" in blob:
        return "brochure"
    if "pamphlet" in blob:
        return "pamphlet"
    if "leaflet" in blob or "flyer" in blob:
        return "leaflet"
    if "type specimen" in blob or "typography" in blob:
        return "type specimen"
    if "letterhead" in blob:
        return "letterhead"
    return object_term


def weak_controlled_record(row: dict[str, str]) -> bool:
    blob = " ".join(
        [
            row.get("source_title", ""),
            row.get("source_description", ""),
            row.get("source_notes", ""),
            row.get("source_subjects", ""),
        ]
    ).lower()
    return any(
        term in blob
        for term in (
            "poster session",
            "conference poster",
            "scientific poster",
            "poster presentation",
            "calendar page",
            "flag of ",
            "coat of arms",
            "locator map",
            "blank map",
        )
    )


def within_controlled_caps(
    row: dict[str, str],
    object_term: str,
    object_counts: Counter[str],
    year_counts: Counter[int],
    country_counts: Counter[str],
    macro_counts: Counter[str],
) -> tuple[bool, str]:
    family = controlled_object_family(row, object_term)
    if object_counts[family] >= OBJECT_CAPS.get(family, TARGET_ROWS):
        return False, "object_family_cap"
    year = row_year(row)
    if year in YEAR_CAPS and year_counts[year] >= YEAR_CAPS[year]:
        return False, "year_cap"
    place = row.get("source_place_text", "")
    macro = place.split(" / ")[0] if place else "Unmapped"
    if place.startswith("Global / controlled expansion") and country_counts[place] >= GLOBAL_FALLBACK_CAP:
        return False, "global_fallback_cap"
    if country_counts[place] >= COUNTRY_CAP:
        return False, "country_cap"
    if macro_counts[macro] >= MACRO_CAP and macro != "Global":
        return False, "macro_cap"
    return True, "ok"


def initial_offset(macro: str, query: str) -> int | str:
    if query.startswith("Category:"):
        return ""
    if macro == "_infer":
        return GLOBAL_SEARCH_START_OFFSET
    return ""


def query_plan() -> list[tuple[str, str, str, str, str]]:
    plan: list[tuple[str, str, str, str, str]] = []
    seen: set[str] = set()

    def add(macro: str, country: str, object_term: str, query: str) -> None:
        if query in seen:
            return
        seen.add(query)
        direction = re.sub(r"[^a-z0-9]+", "_", f"release_{country}_{object_term}".lower()).strip("_")
        plan.append((macro, country, direction, object_term, query))

    for object_term, query in BROAD_CATEGORIES:
        add("_infer", "_infer", object_term, query)

    for object_term, query in BROAD_SEARCHES:
        add("_infer", "_infer", object_term, query)

    for object_term, pattern in YEAR_CATEGORY_OBJECTS:
        for year in range(2026, 1829, -1):
            add("_infer", "_infer", object_term, pattern.format(year=year))

    # Global year scans provide the main volume lane. The Global fallback is
    # capped and later cleaning/normalization must resolve or quarantine weak
    # geography before public rebuild.
    for object_term in OBJECT_TERMS:
        for year in WEAK_PERIOD_YEARS:
            add("_infer", "_infer", object_term, f'"{year}" "{object_term}"')

    # Region-named passes improve non-West distribution after the main volume
    # lane has had a chance to fill source count.
    for macro, country, _region_term, terms in base.REGION_SEEDS:
        aliases = [term for term in terms if term != "Pacific"] if country == "Pacific" else [country, *terms[:1]]
        for alias in aliases:
            for year in COUNTRY_PRIORITY_YEARS:
                for object_term in ("advertisement", "label", "book cover", "trade card", "poster", "advertising poster", "film poster", "brochure", "stamp"):
                    add(macro, country, object_term, f'"{alias}" "{year}" "{object_term}"')

    # Secondary years are only a fallback for object source-visible coverage if
    # the weak-period pool is exhausted before TARGET_ROWS.
    for object_term in ("advertisement", "label", "book cover", "magazine cover", "trade card", "poster", "advertising poster", "film poster", "stamp"):
        for year in SECONDARY_YEARS:
            add("_infer", "_infer", object_term, f'"{year}" "{object_term}"')
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
    manifest_rows = [row for row in read_csv(MANIFEST) if row.get("run_id") != "commons_open_controlled_expansion_2026_v1"]
    image_counts = Counter(row.get("image_presence_code", "") for row in rows)
    manifest_rows.append(
        {
            "run_id": "commons_open_controlled_expansion_2026_v1",
            "records_csv": str(RECORDS_CSV.relative_to(ROOT)),
            "records_count": str(len(rows)),
            "active_source_count": str(len(by_source)),
            "image_state_counts": ";".join(f"{key}:{value}" for key, value in sorted(image_counts.items())),
            "summary_csv": str(SUMMARY_CSV.relative_to(ROOT)),
            "summary_exists": "true",
            "report_md": str(REPORT.relative_to(ROOT)),
            "report_exists": "true",
            "raw_dir": "",
            "raw_dir_exists": "false",
            "raw_commit_policy": "not_present",
            "included_in_public_rebuild": "false",
            "stage": "item_image_capture_pending_rebuild" if rows else "empty_or_pending",
            "notes": "Controlled Commons open expansion; metadata/source links/source-hosted image URLs only; no image binaries or raw payloads saved; public surface rebuild deferred until final release-gate check.",
        }
    )
    write_csv(MANIFEST, manifest_rows, fields)


def write_outputs(rows: list[dict[str, str]], failures: list[dict[str, str]], rejects: Counter[str], started: float, *, final: bool) -> None:
    rows.sort(key=lambda row: (row["date_start"], row["source_place_text"], row["source_title"]))
    for index, row in enumerate(rows, 1):
        row["capture_id"] = f"CCE2026R{index:05d}"
    write_csv(RECORDS_CSV, rows, FIELDNAMES)
    by_source = Counter(row["source_name"] for row in rows)
    summary_rows = [
        {
            "source_name": source,
            "captured_records": str(count),
            "image_states": "IMG03:" + str(count),
            "notes": "Controlled Commons open-license metadata; no image binary downloaded; explicit object-year evidence required",
        }
        for source, count in sorted(by_source.items())
    ]
    write_csv(SUMMARY_CSV, summary_rows, ["source_name", "captured_records", "image_states", "notes"])

    period_counts = Counter(period_band(row) for row in rows)
    macro_counts = Counter(row["source_place_text"].split(" / ")[0] for row in rows)
    country_counts = Counter(row["source_place_text"] for row in rows)
    object_counts = Counter(controlled_object_family(row, row.get("source_object_type", "")) for row in rows)
    year_counts = Counter(row_year(row) for row in rows)
    text_lengths = [
        len(" ".join([row["source_description"], row["source_notes"], row["source_subjects"], row["ocr_or_excerpt"]]).strip())
        for row in rows
    ]
    quality_rows = [
        {"metric": "records_captured", "value": str(len(rows))},
        {"metric": "distinct_active_source_names", "value": str(len(by_source))},
        {"metric": "target_rows", "value": str(TARGET_ROWS)},
        {"metric": "target_met", "value": str(len(rows) >= TARGET_ROWS).lower()},
        {"metric": "query_failures", "value": str(len(failures))},
        {"metric": "minimum_source_derived_text_length", "value": str(min(text_lengths) if text_lengths else 0)},
        {"metric": "median_source_derived_text_length", "value": str(sorted(text_lengths)[len(text_lengths)//2] if text_lengths else 0)},
        {"metric": "year_2026_count", "value": str(year_counts.get(2026, 0))},
        {"metric": "year_2026_rate", "value": f"{(year_counts.get(2026, 0) / len(rows) * 100):.2f}" if rows else "0.00"},
    ]
    for key, value in period_counts.most_common():
        quality_rows.append({"metric": f"period:{key}", "value": str(value)})
    for key, value in macro_counts.most_common():
        quality_rows.append({"metric": f"macro_region:{key}", "value": str(value)})
    for key, value in object_counts.most_common():
        quality_rows.append({"metric": f"object_family:{key}", "value": str(value)})
    for key, value in country_counts.most_common(50):
        quality_rows.append({"metric": f"country:{key}", "value": str(value)})
    for key, value in rejects.most_common():
        quality_rows.append({"metric": f"reject:{key}", "value": str(value)})
    write_csv(QUALITY_CSV, quality_rows, ["metric", "value"])

    lines = [
        "# Commons Open Controlled Expansion 2026 v1",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        "Scope: controlled Commons open-license source pages with explicit object-year evidence. Metadata/source links/source-hosted image URLs only.",
        "",
        "## Metrics",
        "",
        f"- Records captured: {len(rows)}",
        f"- Target rows: {TARGET_ROWS}",
        f"- Target met: {'yes' if len(rows) >= TARGET_ROWS else 'no'}",
        f"- Distinct active source names: {len(by_source)}",
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
    lines.extend(["", "## Object-family Distribution", ""])
    for family, count in object_counts.most_common():
        lines.append(f"- {family}: {count}")
    lines.extend(["", "## Top Country/Region Buckets", ""])
    for country, count in country_counts.most_common(50):
        lines.append(f"- {country}: {count}")
    lines.extend(["", "## Filter Diagnostics", ""])
    for key, value in rejects.most_common(20):
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No image binaries were downloaded.",
            "- No raw API payloads, cookies, browser sessions, screenshots, or local image files were saved.",
            "- `IMG03` is assigned only when Commons extmetadata exposes open-license evidence.",
            "- Records without explicit object-year evidence are excluded; Commons modified/upload timestamps are not used as object dates.",
            "- Impact, source priority, and object weighting are internal triage only.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if final:
        update_manifest(rows, by_source)


def main() -> None:
    base.REGION_SEEDS = expanded_region_seeds()
    base.INFER_FALLBACK_REGION = ("Global", "controlled expansion")
    DATA.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    CAPTURE_RUNS.mkdir(parents=True, exist_ok=True)
    rows = read_csv(RECORDS_CSV)
    seen_ids, seen_images = existing_keys()
    object_counts = Counter(controlled_object_family(row, row.get("source_object_type", "")) for row in rows)
    year_counts = Counter(row_year(row) for row in rows)
    country_counts = Counter(row.get("source_place_text", "") for row in rows)
    macro_counts = Counter((row.get("source_place_text", "").split(" / ")[0] or "Unmapped") for row in rows)
    failures: list[dict[str, str]] = []
    rejects: Counter[str] = Counter()
    completed = completed_queries(len(rows))
    started = time.time()
    plans = query_plan()

    print(f"resume_rows={len(rows)} target={TARGET_ROWS} completed_queries={len(completed)}", flush=True)
    for index, (macro, country, direction_name, object_term, query) in enumerate(plans, 1):
        if len(rows) >= TARGET_ROWS:
            break
        if query in completed:
            continue
        offset: int | str = initial_offset(macro, query)
        pages_seen = 0
        before = len(rows)
        rejects_before = sum(rejects.values())
        failures_before = len(failures)
        max_pages = 18 if query.startswith("Category:") else MAX_SEARCH_PAGES
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
                if weak_controlled_record(row):
                    rejects["weak_graphic_or_event_photo"] += 1
                    continue
                source_key = row["source_identifier"] or row["source_record_url"]
                image_key = row["image_url_detected"].lower()
                if source_key in seen_ids or image_key in seen_images:
                    rejects["duplicate"] += 1
                    continue
                cap_ok, cap_reason = within_controlled_caps(row, object_term, object_counts, year_counts, country_counts, macro_counts)
                if not cap_ok:
                    rejects[cap_reason] += 1
                    continue
                family = controlled_object_family(row, object_term)
                row["direction_id"] = "CCE2026"
                row["source_id"] = "SRC-COMMONS-CONTROLLED-EXPANSION-2026-V1"
                row["source_object_type"] = f"controlled Commons open image record; {object_term}; {family}"
                row["classification_rationale"] = base.clean(
                    "Selected by controlled Commons open expansion: expanded geography inference, explicit object-year evidence, open-license extmetadata, duplicate exclusion, and post-capture cleaning review.",
                    max_chars=700,
                )
                row["uncertainty_note"] = (
                    "Commons metadata can be user-maintained; verify object date, original creator, source credit, category membership, and visual-communication relevance before final scholarly use."
                )
                seen_ids.add(source_key)
                seen_images.add(image_key)
                rows.append(row)
                object_counts[family] += 1
                year_counts[row_year(row)] += 1
                country_counts[row.get("source_place_text", "")] += 1
                macro_counts[(row.get("source_place_text", "").split(" / ")[0] or "Unmapped")] += 1
                if len(rows) % CHECKPOINT_EVERY_ROWS == 0:
                    write_outputs(rows, failures, rejects, started, final=False)
                    print(f"checkpoint rows={len(rows)} query={index}/{len(plans)}", flush=True)
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
        if len(rows) > before:
            write_outputs(rows, failures, rejects, started, final=False)
        if index % 10 == 0 or len(rows) > before or len(rows) >= TARGET_ROWS:
            print(
                f"controlled_query_progress={index}/{len(plans)} rows={len(rows)} added={len(rows)-before} failures={len(failures)} rejects={sum(rejects.values())}",
                flush=True,
            )

    write_outputs(rows, failures, rejects, started, final=True)
    print(f"records={len(rows)}")
    print(f"target_met={len(rows) >= TARGET_ROWS}")
    print(f"failures={len(failures)}")
    print(f"rejects={dict(rejects.most_common())}")
    print(f"wrote {RECORDS_CSV.relative_to(ROOT)}")
    print(f"wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"wrote {QUALITY_CSV.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
