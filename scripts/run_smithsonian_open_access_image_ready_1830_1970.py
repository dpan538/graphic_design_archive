from __future__ import annotations

import csv
import json
import os
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
RAW_DIR = DATA / "capture_batch_smithsonian_oa_image_ready_1830_1970_raw"
RECORDS_CSV = DATA / "capture_batch_smithsonian_oa_image_ready_1830_1970_records.csv"
SUMMARY_CSV = DATA / "capture_batch_smithsonian_oa_image_ready_1830_1970_source_summary.csv"

ACCESS_DATE = "2026-05-31"
SOURCE_ID = "SRC003"
SOURCE_NAME = "Smithsonian Open Access"
USER_AGENT = "ModernGDHistory/0.1 smithsonian-open-access"
YEAR_START = 1830
YEAR_END = 1970
MAX_ROWS = 100
API_KEY = os.environ.get("SMITHSONIAN_API_KEY", "DEMO_KEY")

FIELDNAMES = mx.FIELDNAMES

QUERY_PLAN = [
    ("SI01", "smithsonian_poster_images", "poster online_media_type:Images", 30),
    ("SI02", "smithsonian_advertising_images", "advertising online_media_type:Images", 25),
    ("SI03", "smithsonian_trade_card_images", '"trade card" online_media_type:Images', 20),
    ("SI04", "smithsonian_book_cover_images", '"book cover" online_media_type:Images', 15),
    ("SI05", "smithsonian_graphic_design_images", '"graphic design" online_media_type:Images', 10),
]

GRAPHIC_TERMS = {
    "advert",
    "advertising",
    "affiche",
    "book cover",
    "catalog",
    "cover",
    "graphic design",
    "label",
    "lithograph",
    "magazine",
    "poster",
    "print",
    "trade card",
    "typography",
}


def clean(value: Any, *, max_chars: int = 700) -> str:
    return mx.clean(value, max_chars=max_chars)


def fetch_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=40) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def search_url(query: str, *, start: int = 0, rows: int = 100) -> str:
    return "https://api.si.edu/openaccess/api/v1.0/search?" + urllib.parse.urlencode(
        {
            "api_key": API_KEY,
            "q": query,
            "rows": str(rows),
            "start": str(start),
        }
    )


def freetext_values(row: dict[str, Any], key: str) -> list[str]:
    items = row.get("content", {}).get("freetext", {}).get(key, [])
    if not isinstance(items, list):
        return []
    return [clean(item.get("content", "")) for item in items if isinstance(item, dict) and clean(item.get("content", ""))]


def structured_values(row: dict[str, Any], key: str) -> list[str]:
    items = row.get("content", {}).get("indexedStructured", {}).get(key, [])
    if not isinstance(items, list):
        return []
    return [clean(item) for item in items if clean(item)]


def descriptive(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("content", {}).get("descriptiveNonRepeating", {}) if isinstance(row.get("content"), dict) else {}


def first_year(value: str) -> int | None:
    match = re.search(r"(?<!\d)(18[3-9]\d|19[0-6]\d|1970)(?!\d)", value)
    return int(match.group(1)) if match else None


def date_fields(row: dict[str, Any]) -> tuple[str, str, str]:
    values = freetext_values(row, "date") + structured_values(row, "date")
    date_text = "; ".join(values)
    years = [first_year(v) for v in values]
    years = [year for year in years if year is not None]
    if not years:
        return "", "", date_text
    return str(min(years)), str(max(years)), date_text or str(min(years))


def in_scope(date_start: str, date_end: str, date_text: str) -> bool:
    start = int(date_start) if date_start else first_year(date_text)
    end = int(date_end) if date_end else start
    if end is None:
        return False
    return YEAR_START <= end <= YEAR_END


def media_items(row: dict[str, Any]) -> list[dict[str, Any]]:
    media = descriptive(row).get("online_media", {}).get("media", [])
    return media if isinstance(media, list) else []


def image_url(media: dict[str, Any]) -> str:
    resources = media.get("resources") if isinstance(media.get("resources"), list) else []
    for label in ("Screen Image", "Thumbnail Image", "High-resolution JPEG"):
        for resource in resources:
            if isinstance(resource, dict) and resource.get("label") == label and resource.get("url"):
                return clean(resource.get("url"))
    return clean(media.get("thumbnail") or media.get("content"))


def record_url(row: dict[str, Any]) -> str:
    desc = descriptive(row)
    if desc.get("record_link"):
        return clean(desc.get("record_link"))
    url = clean(row.get("url"))
    return f"https://www.si.edu/object/{url}" if url else ""


def is_graphic_relevant(row: dict[str, Any]) -> bool:
    blob = " ".join(
        [
            clean(row.get("title")),
            " ".join(freetext_values(row, "objectType")),
            " ".join(freetext_values(row, "topic")),
            " ".join(freetext_values(row, "physicalDescription")),
            " ".join(structured_values(row, "object_type")),
        ]
    ).lower()
    return any(term in blob for term in GRAPHIC_TERMS)


def row_from_item(item: dict[str, Any], direction_id: str, direction_name: str, api_url: str) -> dict[str, str] | None:
    media = [m for m in media_items(item) if isinstance(m, dict) and image_url(m)]
    if not media:
        return None
    primary_media = media[0]
    usage = primary_media.get("usage") if isinstance(primary_media.get("usage"), dict) else {}
    if clean(usage.get("access")).upper() != "CC0":
        return None
    if not is_graphic_relevant(item):
        return None
    date_start, date_end, date_text = date_fields(item)
    if not in_scope(date_start, date_end, date_text):
        return None

    desc = descriptive(item)
    identifier = clean(desc.get("record_ID") or item.get("id") or item.get("url"))
    title = clean(item.get("title") or desc.get("title", {}).get("content") if isinstance(desc.get("title"), dict) else "")
    source_url = record_url(item)
    image = image_url(primary_media)
    source_description = clean(
        "; ".join(
            freetext_values(item, "physicalDescription")
            + freetext_values(item, "notes")
            + [clean(primary_media.get("altTextAccessibility")), clean(primary_media.get("extDescrAccessibility"))]
        ),
        max_chars=700,
    )
    topics = freetext_values(item, "topic") + structured_values(item, "object_type")
    object_types = freetext_values(item, "objectType") + structured_values(item, "object_type")
    creators = freetext_values(item, "name")
    place = "; ".join(freetext_values(item, "place") + structured_values(item, "place"))
    collection = clean(desc.get("data_source") or item.get("unitCode"))

    rights = mc.image_fields(
        "IMG03",
        "Smithsonian Open Access media usage reports CC0.",
        image_url=image,
        viewer=source_url or image,
        confidence="high",
        rights_review_required=True,
        local_copy_permitted=False,
        note="Open image candidate; keep Smithsonian source link and media usage evidence.",
    )
    row = {
        "capture_id": "",
        "direction_id": direction_id,
        "direction_name": direction_name,
        "source_id": SOURCE_ID,
        "source_name": SOURCE_NAME,
        "source_api_url": api_url,
        "capture_status": "captured",
        "source_identifier": identifier,
        "source_record_url": source_url,
        "source_title": title,
        "source_creator": "; ".join(creators),
        "source_date_text": date_text,
        "date_start": date_start,
        "date_end": date_end,
        "source_place_text": place,
        "source_object_type": "; ".join(object_types),
        "source_medium": "; ".join(freetext_values(item, "physicalDescription")) or "; ".join(object_types),
        "source_collection": collection,
        "source_description": source_description,
        "source_notes": clean("; ".join(freetext_values(item, "dataSource")), max_chars=500),
        "source_subjects": "; ".join(topics),
        "source_rights_text": "Smithsonian Open Access media usage: CC0",
        "rights_uri": "https://creativecommons.org/publicdomain/zero/1.0/",
        "raw_json_path": "",
        "access_date": ACCESS_DATE,
        **rights,
    }
    row["image_expectation"] = "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["source_description_raw"] = source_description
    row["ocr_or_excerpt"] = source_description
    row["historical_context_note"] = (
        "Captured through Smithsonian Open Access as a low-risk CC0 image expansion path, with emphasis on design objects, posters, trade cards, covers, and advertising records."
    )
    row["classification_rationale"] = (
        "Provisional folder placement derives from Smithsonian title, object type, topic, date, and physical description fields."
    )
    row["uncertainty_note"] = ""
    row["citation_basis"] = f"Smithsonian Open Access. {title}. {source_url}. Accessed {ACCESS_DATE}."
    row["editorial_summary"] = clean(
        f"{title} is indexed from Smithsonian Open Access. {source_description or row['source_subjects'] or row['source_object_type']}",
        max_chars=560,
    )
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
        start = 0
        while direction_count < limit and len(rows) < MAX_ROWS:
            url = search_url(query, start=start, rows=100)
            try:
                payload = fetch_json(url)
            except Exception as exc:  # noqa: BLE001 - source-state logging.
                failures.append({"direction_id": direction_id, "source_name": SOURCE_NAME, "error": str(exc)})
                break
            raw_path = write_raw(f"{direction_name}_{start}.json", payload)
            items = payload.get("response", {}).get("rows", [])
            if not items:
                break
            added = 0
            for item in items:
                row = row_from_item(item, direction_id, direction_name, url)
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
            if len(items) < 100 or added == 0 and start >= 300:
                break
            start += 100
            time.sleep(3.0)

    rows.sort(key=lambda r: (int(r["date_start"]) if r.get("date_start") else 9999, r.get("source_title", "")))
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"SI1970R{index:03d}"

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
                    "notes": "Smithsonian Open Access CC0 image-ready capture.",
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
