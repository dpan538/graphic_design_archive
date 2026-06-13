from __future__ import annotations

import csv
import json
import re
import ssl
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
RAW_DIR = DATA / "capture_batch_gsu_contentdm_image_ready_1830_1970_raw"
RECORDS_CSV = DATA / "capture_batch_gsu_contentdm_image_ready_1830_1970_records.csv"
SUMMARY_CSV = DATA / "capture_batch_gsu_contentdm_image_ready_1830_1970_source_summary.csv"

ACCESS_DATE = "2026-05-31"
SOURCE_ID = "SRC131"
SOURCE_NAME = "Georgia State University Library Digital Collections / CONTENTdm"
BASE = "https://digitalcollections.library.gsu.edu"
USER_AGENT = "ModernGDHistory/0.1 contentdm-image-ready"
YEAR_START = 1830
YEAR_END = 1970
MAX_ROWS = 20
FIELDNAMES = mx.FIELDNAMES
SSL_CONTEXT = ssl._create_unverified_context()

QUERY_PLAN = [
    ("GSU01", "gsu_local_posters", "poster", 14),
    ("GSU02", "gsu_civil_rights_visual_material", "civil rights poster", 4),
    ("GSU03", "gsu_labor_union_print_culture", "union poster", 2),
]

GRAPHIC_TERMS = (
    "advertisement",
    "broadsheet",
    "flyer",
    "graphic",
    "newspaper",
    "poster",
    "posters",
    "printed",
    "program",
    "typography",
)


def clean(value: Any, *, max_chars: int = 700) -> str:
    if isinstance(value, list):
        value = "; ".join(clean(item, max_chars=max_chars) for item in value if item)
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    return value[:max_chars]


def fetch_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=12, context=SSL_CONTEXT) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def search_url(term: str, page: int = 1, max_records: int = 15) -> str:
    encoded = urllib.parse.quote(term)
    return f"{BASE}/digital/api/search/searchterm/{encoded}/field/all/maxRecords/{max_records}/start/{(page - 1) * max_records + 1}"


def detail_url(collection: str, item_id: str) -> str:
    return f"{BASE}/digital/api/singleitem/collection/{urllib.parse.quote(collection)}/id/{urllib.parse.quote(item_id)}"


def field_map(detail: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for field in detail.get("fields", []):
        out[field.get("key", "")] = clean(field.get("value"), max_chars=1200)
        label = clean(field.get("label")).lower().replace(" ", "_")
        if label:
            out[label] = clean(field.get("value"), max_chars=1200)
    return out


def first_year(value: str) -> int | None:
    match = re.search(r"(?<!\d)(18[3-9]\d|19[0-6]\d|1970)(?!\d)", value or "")
    return int(match.group(1)) if match else None


def date_fields(fields: dict[str, str], title: str) -> tuple[str, str, str]:
    text = fields.get("date") or fields.get("decade") or title
    years = [int(year) for year in re.findall(r"(?<!\d)(18[3-9]\d|19[0-6]\d|1970)(?!\d)", text)]
    if not years:
        return "", "", text
    return str(min(years)), str(max(years)), text


def in_scope(date_start: str, date_end: str, date_text: str) -> bool:
    year = int(date_end) if date_end else first_year(date_text)
    return year is not None and YEAR_START <= year <= YEAR_END


def is_relevant(fields: dict[str, str], title: str) -> bool:
    if "inventory of unscanned" in title.lower():
        return False
    blob = " ".join(
        [
            title,
            fields.get("format", ""),
            fields.get("formaa", ""),
            fields.get("type", ""),
            fields.get("descri", ""),
            fields.get("description", ""),
            fields.get("subjec", ""),
            fields.get("subject", ""),
            fields.get("digital_collection", ""),
        ]
    ).lower()
    return any(term in blob for term in GRAPHIC_TERMS)


def existing_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in DATA.glob("capture_batch_*_records.csv"):
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                keys.add((row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", "")))
    return keys


def write_raw(name: str, payload: dict[str, Any]) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path.relative_to(ROOT))


def source_record_url(collection: str, item_id: str, item_link: str = "") -> str:
    if item_link:
        return urllib.parse.urljoin(BASE, item_link)
    return f"{BASE}/digital/collection/{collection}/id/{item_id}"


def row_from_item(item: dict[str, Any], detail: dict[str, Any], direction_id: str, direction_name: str, api_url: str, raw_path: str) -> dict[str, str] | None:
    collection = clean(item.get("collectionAlias"))
    item_id = clean(item.get("itemId"))
    if not collection or not item_id:
        return None
    fields = field_map(detail)
    title = fields.get("title") or clean(item.get("title"))
    date_start, date_end, date_text = date_fields(fields, title)
    if not in_scope(date_start, date_end, date_text) or not is_relevant(fields, title):
        return None
    image_url = clean(detail.get("imageUri") or urllib.parse.urljoin(BASE, detail.get("thumbnailUri") or item.get("thumbnailUri") or ""), max_chars=1000)
    if not image_url:
        return None
    viewer = source_record_url(collection, item_id, clean(item.get("itemLink")))
    rights_text = fields.get("rightl") or fields.get("local_rights_statement") or "Local rights statement not found in CONTENTdm item fields."
    basis = "GSU CONTENTdm item exposes a source-hosted IIIF image/thumbnail; local rights statement requires source-linked, non-local display treatment."
    rights = mc.image_fields(
        "IMG02",
        basis,
        image_url=image_url,
        viewer=viewer,
        confidence="medium",
        rights_review_required=True,
        local_copy_permitted=False,
        note="Source-hosted image candidate; keep GSU item and rights statement visible.",
    )
    description = clean(fields.get("descri") or fields.get("description") or fields.get("public") or fields.get("publication_information"), max_chars=900)
    collection_name = fields.get("cdmcoll") or fields.get("digital_collection") or clean(item.get("metadataFields"))
    medium = clean("; ".join([fields.get("format", ""), fields.get("formaa", ""), fields.get("type", "")]))
    subjects = clean("; ".join([fields.get("subjec", ""), fields.get("subject", ""), fields.get("subject_(names)", ""), fields.get("covera", "")]), max_chars=700)
    identifier = f"{collection}:{item_id}"
    row = {
        "capture_id": "",
        "direction_id": direction_id,
        "direction_name": direction_name,
        "source_id": SOURCE_ID,
        "source_name": SOURCE_NAME,
        "source_api_url": api_url,
        "capture_status": "captured",
        "source_identifier": identifier,
        "source_record_url": viewer,
        "source_title": title,
        "source_creator": fields.get("creato") or fields.get("creator"),
        "source_date_text": date_text,
        "date_start": date_start,
        "date_end": date_end,
        "source_place_text": fields.get("covera") or "United States / Georgia",
        "source_object_type": fields.get("type") or "CONTENTdm digital object",
        "source_medium": medium,
        "source_collection": collection_name,
        **rights,
        "source_description": description,
        "source_notes": clean("; ".join([fields.get("identi", ""), fields.get("curato", ""), fields.get("digita", "")]), max_chars=700),
        "source_subjects": subjects,
        "source_rights_text": rights_text,
        "rights_uri": "",
        "raw_json_path": raw_path,
        "access_date": ACCESS_DATE,
    }
    row["image_expectation"] = "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["source_description_raw"] = description
    row["ocr_or_excerpt"] = description or subjects or fields.get("public")
    row["editorial_summary"] = mx.clean(f"{title} is indexed from GSU Library Digital Collections. {description or medium or subjects}", max_chars=560)
    row["historical_context_note"] = (
        "Captured through Georgia State University Library's CONTENTdm API to add local/university-held labor, civil-rights, theatre, newspaper, and urban print-culture records."
    )
    row["classification_rationale"] = "Provisional folders derive from CONTENTdm title, date, collection, source format, subject, location and rights fields."
    row["uncertainty_note"] = "CONTENTdm/IIIF image presence is treated as source-hosted display evidence; rights remain governed by the local item statement."
    row["citation_basis"] = f"Georgia State University Library Digital Collections. {title}. {viewer}. Accessed {ACCESS_DATE}."
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    seen = existing_keys()
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []

    for direction_id, direction_name, term, limit in QUERY_PLAN:
        page = 1
        direction_count = 0
        while direction_count < limit and len(rows) < MAX_ROWS:
            url = search_url(term, page)
            try:
                payload = fetch_json(url)
            except Exception as exc:  # noqa: BLE001
                failures.append({"direction_id": direction_id, "source_name": SOURCE_NAME, "error": str(exc)})
                break
            write_raw(f"{direction_name}_search_{page}.json", payload)
            items = payload.get("items", [])
            if not items:
                break
            added = 0
            for item in items:
                collection = clean(item.get("collectionAlias"))
                item_id = clean(item.get("itemId"))
                if not collection or not item_id:
                    continue
                try:
                    detail = fetch_json(detail_url(collection, item_id))
                except Exception as exc:  # noqa: BLE001
                    failures.append({"direction_id": direction_id, "source_name": SOURCE_NAME, "error": f"{collection}:{item_id}: {exc}"})
                    continue
                raw_path = write_raw(f"{direction_name}_{collection}_{item_id}.json", detail)
                row = row_from_item(item, detail, direction_id, direction_name, url, raw_path)
                if not row:
                    continue
                key = (row["source_name"], row["source_identifier"])
                if key in seen:
                    continue
                seen.add(key)
                rows.append(row)
                direction_count += 1
                added += 1
                print(f"captured {row['capture_id'] or len(rows)} {row['source_identifier']}", flush=True)
                if direction_count >= limit or len(rows) >= MAX_ROWS:
                    break
                time.sleep(0.08)
            if added == 0 and page >= 2:
                break
            page += 1
            time.sleep(0.25)

    rows.sort(key=lambda r: (int(r["date_start"]) if r.get("date_start") else 9999, r.get("source_title", "")))
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"GSU1970R{index:03d}"

    with RECORDS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["direction_id"], row["source_id"], row["source_name"])].append(row)
    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        fields = ["direction_id", "source_id", "source_name", "captured_count", "failure_count", "img00_count", "img01_count", "img02_count", "img03_count", "img04_count", "notes"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for (direction_id, source_id, source_name), items in sorted(grouped.items()):
            counter = Counter(row["image_presence_code"] for row in items)
            writer.writerow(
                {
                    "direction_id": direction_id,
                    "source_id": source_id,
                    "source_name": source_name,
                    "captured_count": len(items),
                    "failure_count": sum(1 for failure in failures if failure["direction_id"] == direction_id),
                    "img00_count": counter.get("IMG00", 0),
                    "img01_count": counter.get("IMG01", 0),
                    "img02_count": counter.get("IMG02", 0),
                    "img03_count": counter.get("IMG03", 0),
                    "img04_count": counter.get("IMG04", 0),
                    "notes": "Local/university CONTENTdm image-ready source-hosted batch; rights remain item-level.",
                }
            )

    print(f"captured={len(rows)}")
    print(f"image_states={dict(Counter(row['image_presence_code'] for row in rows))}")
    print(f"failures={len(failures)}")


if __name__ == "__main__":
    main()
