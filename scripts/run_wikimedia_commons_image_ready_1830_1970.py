from __future__ import annotations

import csv
import html
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import run_midcentury_capture_1930_1970 as mc
import run_midcentury_expansion_capture_1931_1970 as mx


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_wikimedia_commons_image_ready_1830_1970_raw"
RECORDS_CSV = DATA / "capture_batch_wikimedia_commons_image_ready_1830_1970_records.csv"
SUMMARY_CSV = DATA / "capture_batch_wikimedia_commons_image_ready_1830_1970_source_summary.csv"

ACCESS_DATE = "2026-05-31"
SOURCE_ID = "SRC012"
SOURCE_NAME = "Wikimedia Commons"
USER_AGENT = "ModernGDHistory/0.1 commons-image-ready"
YEAR_START = 1830
YEAR_END = 1970
MAX_ROWS = 180

FIELDNAMES = mx.FIELDNAMES

QUERY_PLAN = [
    ("COM01", "commons_1930s_posters", 'incategory:"1930s posters" poster', 40),
    ("COM02", "commons_1940s_posters", 'incategory:"1940s posters" poster', 35),
    ("COM03", "commons_1950s_posters", 'incategory:"1950s posters" poster', 35),
    ("COM04", "commons_1960s_posters", 'incategory:"1960s posters" poster', 25),
    ("COM05", "commons_advertising_posters", 'incategory:"Advertising posters" poster', 25),
    ("COM06", "commons_travel_posters", 'incategory:"Travel posters" poster', 25),
    ("COM07", "commons_bauhaus_modernism", "Bauhaus poster modernism", 15),
]

GRAPHIC_TERMS = {
    "advert",
    "affiche",
    "bauhaus",
    "design",
    "graphic",
    "lithograph",
    "poster",
    "print",
    "publicity",
    "reklame",
    "typography",
}

OPEN_LICENSE_TERMS = [
    "public domain",
    "cc0",
    "creative commons attribution",
    "creative commons attribution-share alike",
]


def clean(value: Any, *, max_chars: int = 700) -> str:
    if isinstance(value, list):
        value = "; ".join(str(v) for v in value if v)
    value = re.sub(r"<[^>]+>", " ", str(value or ""))
    value = html.unescape(value)
    return mx.clean(value, max_chars=max_chars)


def fetch_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def search_url(query: str, *, offset: int = 0, limit: int = 50) -> str:
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrnamespace": "6",
        "gsrsearch": query,
        "gsrlimit": str(limit),
        "gsroffset": str(offset),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|mime",
        "iiurlwidth": "900",
    }
    return "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)


def extmeta(imageinfo: dict[str, Any]) -> dict[str, str]:
    meta = imageinfo.get("extmetadata") or {}
    return {key: clean(value.get("value")) for key, value in meta.items() if isinstance(value, dict)}


def first_year(blob: str) -> int | None:
    match = re.search(r"(?<!\d)(18[3-9]\d|19[0-6]\d|1970)(?!\d)", blob or "")
    return int(match.group(1)) if match else None


def in_scope(year: int | None) -> bool:
    return year is not None and YEAR_START <= year <= YEAR_END


def is_open(meta: dict[str, str]) -> bool:
    license_blob = " ".join(
        [
            meta.get("LicenseShortName", ""),
            meta.get("UsageTerms", ""),
            meta.get("License", ""),
            meta.get("Copyrighted", ""),
        ]
    ).lower()
    return any(term in license_blob for term in OPEN_LICENSE_TERMS)


def is_relevant(title: str, meta: dict[str, str]) -> bool:
    blob = " ".join(
        [
            title,
            meta.get("ObjectName", ""),
            meta.get("ImageDescription", ""),
            meta.get("Categories", ""),
        ]
    ).lower()
    if "blank poster" in blob or "war memorial" in blob:
        return False
    poster_terms = ["poster", "posters", "affiche", "advertising poster", "travel poster"]
    typography_terms = ["typography", "type specimen", "typeface", "letterpress", "graphic design"]
    return any(term in blob for term in poster_terms) or any(term in blob for term in typography_terms)


def region_hint(blob: str) -> str:
    tests = [
        ("United States", ["united states", "american", "new york", "wpa"]),
        ("France", ["france", "french", "paris", "affiche"]),
        ("United Kingdom", ["britain", "british", "london", "england"]),
        ("Germany", ["germany", "german", "berlin", "bauhaus"]),
        ("Belgium", ["belgium", "belgian", "gent", "ghent"]),
        ("Poland", ["poland", "polish", "warsaw"]),
        ("Russia", ["russia", "russian", "soviet"]),
        ("Netherlands", ["netherlands", "dutch"]),
        ("Switzerland", ["switzerland", "swiss", "zurich"]),
        ("Japan", ["japan", "japanese"]),
        ("China / Hong Kong", ["china", "chinese", "shanghai"]),
        ("Mexico", ["mexico", "mexican"]),
    ]
    blob_l = blob.lower()
    for label, terms in tests:
        if any(term in blob_l for term in terms):
            return label
    return ""


def row_from_page(page: dict[str, Any], direction_id: str, direction_name: str, api_url: str) -> dict[str, str] | None:
    imageinfos = page.get("imageinfo") or []
    if not imageinfos:
        return None
    info = imageinfos[0]
    title = clean(page.get("title", "")).replace("File:", "", 1)
    if title.lower().endswith((".djvu", ".pdf")):
        return None
    if not str(info.get("mime", "")).startswith("image/"):
        return None
    meta = extmeta(info)
    blob = " ".join([title, meta.get("ObjectName", ""), meta.get("ImageDescription", ""), meta.get("Categories", "")])
    year = first_year(blob)
    if not in_scope(year) or not is_open(meta) or not is_relevant(title, meta):
        return None

    image_url = clean(info.get("thumburl") or info.get("url"))
    source_url = clean(info.get("descriptionurl") or info.get("descriptionshorturl"))
    license_label = clean(meta.get("LicenseShortName") or meta.get("UsageTerms") or meta.get("License"))
    rights = mc.image_fields(
        "IMG03",
        f"Wikimedia Commons image with open license metadata: {license_label}.",
        image_url=image_url,
        viewer=source_url,
        confidence="high",
        rights_review_required=False,
        local_copy_permitted=False,
        note="Use source-hosted Commons thumbnail with attribution and source link.",
    )
    description = clean(meta.get("ImageDescription") or meta.get("ObjectName") or title)
    categories = clean(meta.get("Categories"))
    place = region_hint(blob)
    row = {
        "capture_id": "",
        "direction_id": direction_id,
        "direction_name": direction_name,
        "source_id": SOURCE_ID,
        "source_name": SOURCE_NAME,
        "source_api_url": api_url,
        "capture_status": "captured",
        "source_identifier": str(page.get("pageid") or ""),
        "source_record_url": source_url,
        "source_title": title,
        "source_creator": clean(meta.get("Artist")),
        "source_date_text": str(year),
        "date_start": str(year),
        "date_end": str(year),
        "source_place_text": place,
        "source_object_type": "Open image record; poster/print candidate",
        "source_medium": "poster / print / graphic record",
        "source_collection": clean(meta.get("Credit") or "Wikimedia Commons"),
        "source_description": description,
        "source_notes": clean("; ".join([meta.get("ObjectName", ""), meta.get("DateTimeOriginal", ""), categories]), max_chars=700),
        "source_subjects": categories,
        "source_rights_text": clean("; ".join([license_label, meta.get("UsageTerms", ""), meta.get("LicenseUrl", "")])),
        "rights_uri": clean(meta.get("LicenseUrl")),
        "raw_json_path": "",
        "access_date": ACCESS_DATE,
        **rights,
    }
    row["image_expectation"] = "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["source_description_raw"] = description
    row["ocr_or_excerpt"] = description
    row["historical_context_note"] = (
        "Captured through Wikimedia Commons as an openly licensed image supplement. Commons is treated as a rights-aware discovery/display layer, not as the original holding archive."
    )
    row["classification_rationale"] = (
        "Provisional classification derives from Commons title, description, categories, date, and license metadata."
    )
    row["uncertainty_note"] = "Commons metadata may aggregate user-supplied descriptions; verify against linked institutional credit when available."
    row["citation_basis"] = f"Wikimedia Commons. {title}. {source_url}. Accessed {ACCESS_DATE}."
    row["editorial_summary"] = clean(f"{title} is an openly licensed Commons image record. {description}", max_chars=560)
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def existing_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in DATA.glob("capture_batch_*_records.csv"):
        if not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                keys.add((row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", "")))
    return keys


def write_raw(name: str, payload: dict[str, Any]) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path.relative_to(ROOT))


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    seen = existing_keys()

    for direction_id, direction_name, query, limit in QUERY_PLAN:
        direction_count = 0
        offset = 0
        while direction_count < limit and len(rows) < MAX_ROWS:
            url = search_url(query, offset=offset)
            try:
                payload = fetch_json(url)
            except Exception as exc:  # noqa: BLE001
                failures.append({"direction_id": direction_id, "source_name": SOURCE_NAME, "error": str(exc)})
                break
            raw_path = write_raw(f"{direction_name}_{offset}.json", payload)
            pages = list((payload.get("query", {}).get("pages") or {}).values())
            if not pages:
                break
            added = 0
            for page in sorted(pages, key=lambda item: item.get("index", 9999)):
                row = row_from_page(page, direction_id, direction_name, url)
                if not row:
                    continue
                key = (row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", ""))
                if key in seen:
                    continue
                seen.add(key)
                row["raw_json_path"] = raw_path
                rows.append(row)
                direction_count += 1
                added += 1
                if direction_count >= limit or len(rows) >= MAX_ROWS:
                    break
            if "continue" not in payload or (added == 0 and offset >= 150):
                break
            offset = int(payload.get("continue", {}).get("gsroffset", offset + 50))
            time.sleep(0.7)

    rows.sort(key=lambda r: (int(r["date_start"]) if r.get("date_start") else 9999, r.get("source_title", "")))
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"COM1970R{index:03d}"

    with RECORDS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["direction_id"]].append(row)
    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "direction_id",
            "source_id",
            "source_name",
            "captured_count",
            "failure_count",
            "img00_count",
            "img01_count",
            "img02_count",
            "img03_count",
            "img04_count",
            "notes",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for direction_id, items in sorted(grouped.items()):
            counter = Counter(row["image_presence_code"] for row in items)
            writer.writerow(
                {
                    "direction_id": direction_id,
                    "source_id": SOURCE_ID,
                    "source_name": SOURCE_NAME,
                    "captured_count": str(len(items)),
                    "failure_count": str(sum(1 for failure in failures if failure["direction_id"] == direction_id)),
                    "img00_count": str(counter.get("IMG00", 0)),
                    "img01_count": str(counter.get("IMG01", 0)),
                    "img02_count": str(counter.get("IMG02", 0)),
                    "img03_count": str(counter.get("IMG03", 0)),
                    "img04_count": str(counter.get("IMG04", 0)),
                    "notes": "Wikimedia Commons open-license image supplementation; verify original holding institution where possible.",
                }
            )

    counter = Counter(row["image_presence_code"] for row in rows)
    print(f"{RECORDS_CSV.relative_to(ROOT)}: {len(rows)} rows")
    print(f"{SUMMARY_CSV.relative_to(ROOT)}: summary written")
    print("image distribution:", dict(sorted(counter.items())))
    if failures:
        print("failures:", json.dumps(failures[:8], ensure_ascii=False))


if __name__ == "__main__":
    main()
