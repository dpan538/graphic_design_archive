from __future__ import annotations

import csv
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
RAW_DIR = DATA / "capture_batch_digitalnz_image_ready_1830_1970_raw"
RECORDS_CSV = DATA / "capture_batch_digitalnz_image_ready_1830_1970_records.csv"
SUMMARY_CSV = DATA / "capture_batch_digitalnz_image_ready_1830_1970_source_summary.csv"

ACCESS_DATE = "2026-05-31"
SOURCE_ID = "SRC011"
SOURCE_NAME = "DigitalNZ"
USER_AGENT = "ModernGDHistory/0.1 digitalnz-image-ready"
YEAR_START = 1830
YEAR_END = 1970
MAX_ROWS = 160

FIELDNAMES = mx.FIELDNAMES

QUERY_PLAN = [
    ("DNZ01", "digitalnz_newspaper_advertisements", "advertisements", 45),
    ("DNZ02", "digitalnz_poster_records", "poster", 35),
    ("DNZ03", "digitalnz_trade_and_commercial_print", '"trade card" OR advertising', 30),
    ("DNZ04", "digitalnz_transport_and_tourism_print", '"railway poster" OR tourism poster OR travel poster', 25),
    ("DNZ05", "digitalnz_typography_and_layout", '"graphic design" OR typography OR layout', 25),
]

GRAPHIC_TERMS = {
    "advertisement",
    "advertisements",
    "advertising",
    "broadsheet",
    "catalogue",
    "illustration",
    "layout",
    "poster",
    "print",
    "printing",
    "publicity",
    "trade card",
    "typography",
}


def clean(value: Any, *, max_chars: int = 700) -> str:
    if isinstance(value, list):
        value = "; ".join(str(v) for v in value if v)
    return mx.clean(value, max_chars=max_chars)


def fetch_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def search_url(query: str, *, page: int = 1, per_page: int = 100) -> str:
    params = [
        ("search_text", query),
        ("per_page", str(per_page)),
        ("page", str(page)),
        ("and[category][]", "Images"),
    ]
    return "https://api.digitalnz.org/v3/records.json?" + urllib.parse.urlencode(params)


def first_year(value: str) -> int | None:
    match = re.search(r"(?<!\d)(18[3-9]\d|19[0-6]\d|1970)(?!\d)", value)
    return int(match.group(1)) if match else None


def date_fields(item: dict[str, Any]) -> tuple[str, str, str]:
    values: list[str] = []
    for key in ("display_date", "date", "published_date", "syndication_date"):
        value = item.get(key)
        if isinstance(value, list):
            values.extend(clean(v, max_chars=120) for v in value)
        elif value:
            values.append(clean(value, max_chars=120))
    date_text = "; ".join(v for v in values if v)
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


def is_open_enough(item: dict[str, Any]) -> bool:
    rights = clean(item.get("rights")).lower()
    usage = {clean(v).lower() for v in item.get("usage", []) if clean(v)}
    if "no known copyright restrictions" in rights:
        return True
    return {"share", "modify", "use commercially"}.issubset(usage)


def is_graphic_relevant(item: dict[str, Any]) -> bool:
    blob = " ".join(
        [
            clean(item.get("title")),
            clean(item.get("description")),
            clean(item.get("additional_description")),
            clean(item.get("subject")),
            clean(item.get("collection_title")),
            clean(item.get("display_collection")),
            clean(item.get("dc_type")),
            clean(item.get("format")),
        ]
    ).lower()
    return any(term in blob for term in GRAPHIC_TERMS)


def image_url(item: dict[str, Any]) -> str:
    return clean(item.get("large_thumbnail_url") or item.get("object_url") or item.get("thumbnail_url"))


def row_from_item(item: dict[str, Any], direction_id: str, direction_name: str, api_url: str) -> dict[str, str] | None:
    if not image_url(item) or not is_open_enough(item) or not is_graphic_relevant(item):
        return None
    date_start, date_end, date_text = date_fields(item)
    if not in_scope(date_start, date_end, date_text):
        return None
    identifier = clean(item.get("id"))
    source_url = clean(item.get("landing_url") or item.get("dc_identifier") or item.get("source_url"))
    title = clean(item.get("title") or f"DigitalNZ record {identifier}")
    collection = clean(item.get("display_collection") or item.get("collection_title") or item.get("content_partner"))
    description = clean(
        "; ".join(
            [
                clean(item.get("description")),
                clean(item.get("additional_description")),
                clean(item.get("subject")),
            ]
        ),
        max_chars=700,
    )
    medium = clean("; ".join([clean(item.get("format")), clean(item.get("dc_type")), clean(item.get("dnz_type"))]))
    rights = mc.image_fields(
        "IMG03",
        "DigitalNZ record exposes an image URL with no-known-copyright-restrictions or full share/modify/commercial usage signals.",
        image_url=image_url(item),
        viewer=source_url or clean(item.get("source_url")) or image_url(item),
        confidence="high",
        rights_review_required=True,
        local_copy_permitted=False,
        note="Open image candidate; retain DigitalNZ and partner source links.",
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
        "source_creator": clean(item.get("creator") or item.get("credit_creator")),
        "source_date_text": date_text,
        "date_start": date_start,
        "date_end": date_end,
        "source_place_text": "Aotearoa New Zealand",
        "source_object_type": clean(item.get("category") or item.get("dnz_type") or "DigitalNZ image record"),
        "source_medium": medium,
        "source_collection": collection,
        "source_description": description,
        "source_notes": clean("; ".join([clean(item.get("content_partner")), clean(item.get("publisher")), clean(item.get("citation"))]), max_chars=500),
        "source_subjects": clean(item.get("subject") or item.get("tag")),
        "source_rights_text": clean("; ".join([clean(item.get("rights")), clean(item.get("usage"))])),
        "rights_uri": clean(item.get("rights_url")),
        "raw_json_path": "",
        "access_date": ACCESS_DATE,
        **rights,
    }
    row["image_expectation"] = "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["source_description_raw"] = description
    row["ocr_or_excerpt"] = clean(item.get("fulltext") or item.get("text") or description, max_chars=700)
    row["historical_context_note"] = (
        "Captured through DigitalNZ to expand beyond museum-object APIs into periodical, newspaper, advertising, and public visual communication records from Aotearoa New Zealand."
    )
    row["classification_rationale"] = (
        "Provisional folders derive from DigitalNZ title, collection, category, date, and subject metadata."
    )
    row["uncertainty_note"] = ""
    row["citation_basis"] = f"DigitalNZ. {title}. {source_url}. Accessed {ACCESS_DATE}."
    row["editorial_summary"] = clean(
        f"{title} is indexed from DigitalNZ. {description or collection or row['source_subjects']}",
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
        page = 1
        while direction_count < limit and len(rows) < MAX_ROWS:
            url = search_url(query, page=page)
            try:
                payload = fetch_json(url)
            except Exception as exc:  # noqa: BLE001 - preserve source-state facts.
                failures.append({"direction_id": direction_id, "source_name": SOURCE_NAME, "error": str(exc)})
                break
            raw_path = write_raw(f"{direction_name}_{page}.json", payload)
            items = payload.get("search", {}).get("results", [])
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
            if len(items) < 100 or (added == 0 and page >= 4):
                break
            page += 1
            time.sleep(1.0)

    rows.sort(key=lambda r: (int(r["date_start"]) if r.get("date_start") else 9999, r.get("source_title", "")))
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"DNZ1970R{index:03d}"

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
                    "notes": "DigitalNZ no-key image-ready capture.",
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
