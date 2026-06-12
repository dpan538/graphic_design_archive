#!/usr/bin/env python3
"""Capture Commons open-image records through country category trees.

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
from collections import Counter, deque
from pathlib import Path
from typing import Any

import run_commons_open_global_south_image_capture_2026_v1 as base
import run_commons_open_region_balance_image_capture_2026_v2 as v2
import run_commons_open_region_balance_image_capture_2026_v3 as v3


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
CAPTURE_RUNS = DATA / "capture_runs"

RECORDS_CSV = DATA / "capture_batch_commons_open_category_tree_image_2026_v1_records.csv"
SUMMARY_CSV = DATA / "capture_batch_commons_open_category_tree_image_2026_v1_source_summary.csv"
QUALITY_CSV = DATA / "commons_open_category_tree_image_2026_v1_quality.csv"
REPORT = DOCS / "COMMONS_OPEN_CATEGORY_TREE_IMAGE_CAPTURE_2026_v1.md"
MANIFEST = CAPTURE_RUNS / "capture_run_manifest_v1.csv"
STATE_CSV = DATA / "commons_open_category_tree_image_2026_v1_category_state.csv"

ACCESS_DATE = "2026-06-12"
base.ACCESS_DATE = ACCESS_DATE
FIELDNAMES = base.FIELDNAMES

TARGET_ROWS = 5000
CATEGORY_MEMBER_LIMIT = 500
FILE_PAGE_LIMIT = 50
FILES_PER_CATEGORY_PAGES = 30
MAX_CATEGORY_VISITS = 9000
MAX_SUBCAT_DEPTH = 4
REQUEST_DELAY_SECONDS = 0.08
CHECKPOINT_EVERY_ROWS = 100

SEED_CATEGORIES = [
    ("poster", "Category:Posters by country"),
    ("political poster", "Category:Political posters by country"),
    ("propaganda poster", "Category:Propaganda posters by country"),
    ("film poster", "Category:Film posters by country"),
    ("travel poster", "Category:Travel posters by country"),
    ("postage stamp", "Category:Postage stamps by country"),
    ("book cover", "Category:Book covers by country"),
    ("magazine cover", "Category:Magazine covers by country"),
    ("packaging", "Category:Packaging by country"),
    ("label", "Category:Labels by country"),
    ("brochure", "Category:Brochures by country"),
    ("pamphlet", "Category:Pamphlets by country"),
    ("typography", "Category:Typography by country"),
]

REVISIT_CATEGORIES = [
    ("postage stamp", "Category:Meter stamps of Mexico"),
    ("postage stamp", "Category:Meter stamps of Morocco"),
    ("postage stamp", "Category:Meter stamps of South Korea"),
    ("postage stamp", "Category:Meter stamps of South Africa"),
    ("postage stamp", "Category:Meter stamps of Malaysia"),
    ("postage stamp", "Category:Airmail stamps of Brazil"),
    ("postage stamp", "Category:Airmail stamps of Peru"),
    ("postage stamp", "Category:Definitive stamps of India"),
    ("postage stamp", "Category:Meter stamps of India"),
    ("postage stamp", "Category:1960 postage stamps of Iraq"),
    ("postage stamp", "Category:1962 postage stamps of Iraq"),
    ("postage stamp", "Category:1936 stamps of Algeria"),
    ("postage stamp", "Category:1942 stamps of Algeria"),
    ("postage stamp", "Category:1995 stamps of Kazakhstan"),
    ("postage stamp", "Category:1997 stamps of Kazakhstan"),
    ("film poster", "Category:1970s film posters of Iran"),
    ("film poster", "Category:1980s film posters of Iran"),
    ("poster", "Category:Rail transport posters of New Zealand"),
]

SKIP_CATEGORY_TERMS = (
    "bottle",
    "bottles",
    "canteen",
    "flask",
    "jar",
    "jars",
    "canisters",
    "cans by country",
    "ink bottles",
    "container",
    "containers",
    "cooking pots",
    "bags of rice",
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


def categorymembers_url(category: str, cmtype: str, offset: str = "") -> str:
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": category,
        "cmtype": cmtype,
        "cmlimit": str(CATEGORY_MEMBER_LIMIT),
    }
    if offset:
        params["cmcontinue"] = offset
    return "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)


def category_subcats(category: str) -> tuple[list[str], list[dict[str, str]]]:
    subcats: list[str] = []
    failures: list[dict[str, str]] = []
    offset = ""
    while True:
        url = categorymembers_url(category, "subcat", offset)
        try:
            payload = base.fetch_json(url)
        except Exception as exc:  # noqa: BLE001
            failures.append({"category": category, "error": type(exc).__name__, "detail": base.clean(str(exc), max_chars=180)})
            break
        time.sleep(REQUEST_DELAY_SECONDS)
        members = payload.get("query", {}).get("categorymembers", [])
        for member in members:
            title = base.clean(member.get("title"))
            if title.startswith("Category:"):
                subcats.append(title)
        cont = payload.get("continue", {}).get("cmcontinue")
        if not cont:
            break
        offset = base.clean(cont)
    return subcats, failures


def country_patterns() -> list[tuple[str, str, list[str]]]:
    rows = []
    for macro, country, aliases in v3.COUNTRIES:
        unique_aliases = list(dict.fromkeys([country, *aliases]))
        unique_aliases.sort(key=len, reverse=True)
        rows.append((macro, country, unique_aliases))
    return rows


COUNTRY_PATTERNS = country_patterns()


def match_country(category_title: str) -> tuple[str, str] | None:
    label = category_title.replace("_", " ")
    for macro, country, aliases in COUNTRY_PATTERNS:
        for alias in aliases:
            pattern = r"(?<![A-Za-z])" + re.escape(alias) + r"(?![A-Za-z])"
            if re.search(pattern, label, flags=re.IGNORECASE):
                return macro, country
    return None


def object_from_category(default_object: str, category_title: str) -> str:
    label = category_title.lower()
    if "postage stamp" in label or "stamps" in label:
        return "postage stamp"
    if "political poster" in label:
        return "political poster"
    if "propaganda poster" in label:
        return "propaganda poster"
    if "film poster" in label or "movie poster" in label:
        return "film poster"
    if "travel poster" in label:
        return "travel poster"
    if "book cover" in label:
        return "book cover"
    if "magazine cover" in label:
        return "magazine cover"
    if "packaging" in label:
        return "packaging"
    if "label" in label:
        return "label"
    if "brochure" in label:
        return "brochure"
    if "pamphlet" in label:
        return "pamphlet"
    if "typograph" in label or "type specimen" in label:
        return "typography"
    if "poster" in label:
        return "poster"
    return default_object


def should_walk_subcat(title: str, matched_country: tuple[str, str] | None, depth: int) -> bool:
    label = title.lower()
    if any(term in label for term in SKIP_CATEGORY_TERMS):
        return False
    if matched_country:
        return True
    if depth <= 2 and "by country" in label:
        return True
    return False


def completed_categories(max_rows_after: int) -> set[str]:
    completed: set[str] = set()
    for row in read_csv(STATE_CSV):
        try:
            rows_after = int(row.get("rows_after") or "0")
        except ValueError:
            rows_after = 0
        if rows_after > max_rows_after:
            continue
        if row.get("status") == "completed" and row.get("category"):
            completed.add(row["category"])
    return completed


def append_category_state(row: dict[str, str]) -> None:
    fields = [
        "category",
        "macro",
        "country",
        "object_term",
        "depth",
        "status",
        "added",
        "failures_delta",
        "rejects_delta",
        "rows_after",
        "elapsed_seconds",
    ]
    rows = read_csv(STATE_CSV)
    rows = [current for current in rows if current.get("category") != row.get("category")]
    rows.append(row)
    write_csv(STATE_CSV, rows, fields)


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
    run_id = "commons_open_category_tree_image_2026_v1"
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
            "notes": "Commons country category-tree open image capture; source-derived metadata only; no image binaries or raw payloads saved.",
        }
    )
    write_csv(MANIFEST, rows, fields)


def write_outputs(
    rows: list[dict[str, str]],
    failures: list[dict[str, str]],
    rejects: Counter[str],
    visited_count: int,
    queue_count: int,
    started: float,
    *,
    final: bool,
) -> None:
    rows.sort(key=lambda row: (row["source_place_text"], row["date_start"], row["source_title"]))
    for index, row in enumerate(rows, 1):
        row["capture_id"] = f"CCT2026R{index:05d}"
    write_csv(RECORDS_CSV, rows, FIELDNAMES)

    by_source = Counter(row["source_name"] for row in rows)
    image_counts = Counter(row["image_presence_code"] for row in rows)
    summary_rows = [
        {
            "source_name": source,
            "captured_records": str(count),
            "image_states": "IMG03:" + str(count),
            "notes": "Commons country category-tree open-license metadata; no image binary downloaded",
        }
        for source, count in sorted(by_source.items())
    ]
    write_csv(SUMMARY_CSV, summary_rows, ["source_name", "captured_records", "image_states", "notes"])

    period_counts = Counter(v3.period_band(row) for row in rows)
    macro_counts = Counter(v3.macro_key(row) for row in rows)
    country_counts = Counter(row["source_place_text"] for row in rows)
    year_counts = Counter(v3.row_year(row) for row in rows)
    text_lengths = [
        len(" ".join([row["source_description"], row["source_notes"], row["source_subjects"], row["ocr_or_excerpt"]]).strip())
        for row in rows
    ]
    quality_rows = [
        {"metric": "records_captured", "value": str(len(rows))},
        {"metric": "distinct_active_source_names", "value": str(len(by_source))},
        {"metric": "category_failures", "value": str(len(failures))},
        {"metric": "visited_categories", "value": str(visited_count)},
        {"metric": "queued_categories", "value": str(queue_count)},
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
    for key, value in country_counts.most_common(45):
        quality_rows.append({"metric": f"country:{key}", "value": str(value)})
    for key, value in rejects.most_common():
        quality_rows.append({"metric": f"reject:{key}", "value": str(value)})
    write_csv(QUALITY_CSV, quality_rows, ["metric", "value"])

    lines = [
        "# Commons Open Category Tree Image Capture 2026 v1",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        "Scope: Commons country category-tree discovery for open-license source pages. Metadata/source links/source-hosted image URLs only.",
        "",
        "## Metrics",
        "",
        f"- Records captured: {len(rows)}",
        f"- Target rows: {TARGET_ROWS}",
        f"- Target met: {'yes' if len(rows) >= TARGET_ROWS else 'no'}",
        f"- Distinct active source names: {len(by_source)}",
        f"- Image states: {', '.join(f'{key}:{value}' for key, value in sorted(image_counts.items())) or 'none'}",
        f"- Category failures: {len(failures)}",
        f"- Visited categories: {visited_count}",
        f"- Queued categories: {queue_count}",
        f"- Runtime seconds: {time.time() - started:.1f}",
        f"- Minimum source-derived text length: {min(text_lengths) if text_lengths else 0}",
        f"- Median source-derived text length: {sorted(text_lengths)[len(text_lengths)//2] if text_lengths else 0}",
        f"- 2026 count/rate: {year_counts.get(2026, 0)} / {quality_rows[10]['value']}%",
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
    lines.extend(["", "## Category Failures", ""])
    if failures:
        for failure in failures[:30]:
            lines.append(f"- {failure.get('error')}: {failure.get('category')} ({failure.get('detail', '')})")
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
            "- Category-tree membership is source discovery evidence, not an authorship or final interpretive claim.",
            "- Impact and source priority are internal triage only.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if final:
        update_manifest(len(rows), len(by_source), image_counts)


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    rows = read_csv(RECORDS_CSV)
    failures: list[dict[str, str]] = []
    rejects: Counter[str] = Counter()
    seen_ids, seen_images = existing_keys(rows)
    macro_counts, country_counts, period_counts, year_counts = v3.reseed_counters(rows)
    completed = completed_categories(len(rows))
    completed.difference_update(category for _object_term, category in REVISIT_CATEGORIES)
    queue: deque[tuple[str, str, int]] = deque((category, object_term, 0) for object_term, category in [*REVISIT_CATEGORIES, *SEED_CATEGORIES])
    queued: set[str] = {category for _object_term, category in [*REVISIT_CATEGORIES, *SEED_CATEGORIES]}
    visited: set[str] = set()
    started = time.time()
    last_checkpoint_rows = len(rows)

    print(f"resume_rows={len(rows)} target={TARGET_ROWS} completed_categories={len(completed)}", flush=True)
    while queue and len(rows) < TARGET_ROWS and len(visited) < MAX_CATEGORY_VISITS:
        category, default_object, depth = queue.popleft()
        if category in visited:
            continue
        visited.add(category)
        match = match_country(category)
        object_term = object_from_category(default_object, category)
        before = len(rows)
        failures_before = len(failures)
        rejects_before = sum(rejects.values())

        subcats, subcat_failures = category_subcats(category) if depth < MAX_SUBCAT_DEPTH else ([], [])
        failures.extend(subcat_failures)
        for subcat in subcats:
            subcat_match = match_country(subcat)
            if should_walk_subcat(subcat, subcat_match, depth + 1) and subcat not in queued and subcat not in visited:
                queue.append((subcat, object_from_category(object_term, subcat), depth + 1))
                queued.add(subcat)

        if match and category not in completed:
            macro, country = match
            offset: int | str = ""
            pages_seen = 0
            while pages_seen < FILES_PER_CATEGORY_PAGES and len(rows) < TARGET_ROWS:
                url = base.search_url(category, offset=offset, limit=FILE_PAGE_LIMIT)
                try:
                    payload = base.fetch_json(url)
                except Exception as exc:  # noqa: BLE001
                    failures.append({"category": category, "error": type(exc).__name__, "detail": base.clean(str(exc), max_chars=180)})
                    break
                time.sleep(REQUEST_DELAY_SECONDS)
                pages = list((payload.get("query", {}).get("pages") or {}).values())
                if not pages:
                    break
                for page in sorted(pages, key=lambda item: item.get("index", 9999)):
                    row = base.row_from_page(
                        page,
                        macro,
                        country,
                        re.sub(r"[^a-z0-9]+", "_", f"category_tree_{country}_{object_term}".lower()).strip("_"),
                        object_term,
                        url,
                    )
                    if not row:
                        rejects["base_filter"] += 1
                        continue
                    ok, reason = v2.strong_relevance(row, object_term)
                    if not ok:
                        rejects[reason] += 1
                        continue
                    ok, reason = v3.v3_quality_gate(row, object_term)
                    if not ok:
                        rejects[reason] += 1
                        continue
                    source_key = row["source_identifier"] or row["source_record_url"]
                    image_key = row["image_url_detected"].lower()
                    if source_key in seen_ids or image_key in seen_images:
                        rejects["duplicate"] += 1
                        continue
                    cap_ok, cap_reason = v3.within_distribution_caps(row, macro_counts, country_counts, period_counts, year_counts)
                    if not cap_ok:
                        rejects[cap_reason] += 1
                        continue
                    row["direction_id"] = "CCT2026"
                    row["source_id"] = "SRC-COMMONS-CATEGORY-TREE-2026-V1"
                    row["source_object_type"] = f"Commons country category-tree open image record; {object_term}"
                    row["classification_rationale"] = base.clean(
                        f"Selected by Commons country category-tree category {category}, open-license extmetadata, strict source-derived graphic-object filter, duplicate exclusion, and object-year evidence.",
                        max_chars=700,
                    )
                    row["uncertainty_note"] = (
                        "Commons metadata and category membership can be user-maintained; verify object date, original creator, source credit, category membership, and visual-communication relevance before final scholarly use."
                    )
                    seen_ids.add(source_key)
                    seen_images.add(image_key)
                    rows.append(row)
                    country_counts[row["source_place_text"]] += 1
                    macro_counts[v3.macro_key(row)] += 1
                    period_counts[v3.period_band(row)] += 1
                    year_counts[v3.row_year(row)] += 1
                    if len(rows) - last_checkpoint_rows >= CHECKPOINT_EVERY_ROWS:
                        write_outputs(rows, failures, rejects, len(visited), len(queued), started, final=False)
                        last_checkpoint_rows = len(rows)
                    if len(rows) >= TARGET_ROWS:
                        break
                if "continue" not in payload:
                    break
                cont = payload.get("continue", {})
                offset = base.clean(cont.get("gcmcontinue"))
                if not offset:
                    break
                pages_seen += 1

        if category not in completed:
            append_category_state(
                {
                    "category": category,
                    "macro": match[0] if match else "",
                    "country": match[1] if match else "",
                    "object_term": object_term,
                    "depth": str(depth),
                    "status": "completed",
                    "added": str(len(rows) - before),
                    "failures_delta": str(len(failures) - failures_before),
                    "rejects_delta": str(sum(rejects.values()) - rejects_before),
                    "rows_after": str(len(rows)),
                    "elapsed_seconds": f"{time.time() - started:.1f}",
                }
            )
        if len(rows) > before:
            write_outputs(rows, failures, rejects, len(visited), len(queued), started, final=False)
            last_checkpoint_rows = len(rows)
        if len(visited) % 25 == 0 or len(rows) > before or len(rows) >= TARGET_ROWS:
            print(
                f"category_tree_progress visited={len(visited)} queued={len(queued)} rows={len(rows)} added={len(rows)-before} failures={len(failures)} rejects={sum(rejects.values())} category={category}",
                flush=True,
            )

    if len(visited) >= MAX_CATEGORY_VISITS and len(rows) < TARGET_ROWS:
        failures.append({"category": "category_visit_limit", "error": "CategoryVisitLimitReached", "detail": str(MAX_CATEGORY_VISITS)})
    write_outputs(rows, failures, rejects, len(visited), len(queued), started, final=True)
    print(f"wrote {RECORDS_CSV} rows={len(rows)} failures={len(failures)} rejects={sum(rejects.values())}")
    print(f"wrote {SUMMARY_CSV}")
    print(f"wrote {QUALITY_CSV}")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
