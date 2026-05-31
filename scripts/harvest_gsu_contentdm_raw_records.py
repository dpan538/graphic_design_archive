from __future__ import annotations

import csv
import json
import re
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import run_midcentury_capture_1930_1970 as mc
import run_midcentury_expansion_capture_1931_1970 as mx
from run_gsu_contentdm_image_ready_1830_1970 import field_map


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_gsu_contentdm_image_ready_1830_1970_raw"
RECORDS_CSV = DATA / "capture_batch_gsu_contentdm_image_ready_1830_1970_records.csv"
SUMMARY_CSV = DATA / "capture_batch_gsu_contentdm_image_ready_1830_1970_source_summary.csv"

ACCESS_DATE = "2026-05-31"
SOURCE_ID = "SRC131"
SOURCE_NAME = "Georgia State University Library Digital Collections / CONTENTdm"
BASE = "https://digitalcollections.library.gsu.edu"
YEAR_START = 1931
YEAR_END = 1970

FIELDNAMES = mx.FIELDNAMES

COLLECTION_LIMITS = {
    "GSB": 5,
    "IAM": 8,
    "gae": 6,
    "signal": 4,
    "mhross": 4,
    "SKennedy": 4,
    "labor": 3,
    "arwg": 2,
    "AFLCIO": 2,
    "popmusic": 1,
    "ugwa": 1,
    "music": 1,
}

COLLECTION_PRIORITY = {
    "GSB": 1,
    "SKennedy": 2,
    "labor": 3,
    "IAM": 4,
    "AFLCIO": 5,
    "signal": 6,
    "gae": 7,
    "mhross": 8,
    "ugwa": 9,
    "arwg": 10,
    "popmusic": 11,
    "music": 12,
}

EXCLUDED_TYPE_TERMS = ("sound", "video/mp4", "audio", "oral history")


def clean(value: Any, *, max_chars: int = 700) -> str:
    if isinstance(value, list):
        value = "; ".join(clean(item, max_chars=max_chars) for item in value if item)
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    return value[:max_chars]


def extracted_years(text: str) -> list[int]:
    years = [int(year) for year in re.findall(r"(?<!\d)((?:18|19|20)\d{2})(?!\d)", text or "")]
    for decade in re.findall(r"(?<!\d)((?:18|19|20)\d0)s(?!\d)", text or ""):
        years.extend([int(decade), int(decade) + 9])
    return years


def date_fields(fields: dict[str, str], title: str) -> tuple[str, str, str]:
    text = fields.get("date") or fields.get("decade") or title
    years = extracted_years(text)
    if not years:
        return "", "", text
    return str(min(years)), str(max(years)), text


def collection_and_item(detail: dict[str, Any]) -> tuple[str, str]:
    image_uri = clean(detail.get("imageUri"), max_chars=1000)
    for pattern in (r"/iiif/2/([^:/]+):([^/]+)/", r"/image/([^/]+)/([^/]+)/"):
        match = re.search(pattern, image_uri)
        if match:
            return match.group(1), match.group(2)
    filename = clean(detail.get("filename"))
    match = re.search(r"^([^_]+)_(\d+)", filename)
    if match:
        return match.group(1), match.group(2)
    return "", ""


def source_record_url(collection: str, item_id: str) -> str:
    return f"{BASE}/digital/collection/{urllib.parse.quote(collection)}/id/{urllib.parse.quote(item_id)}"


def absolute_image_url(url: str) -> str:
    return urllib.parse.urljoin(BASE, url)


def is_candidate(fields: dict[str, str], date_end: str) -> bool:
    if not date_end or not (YEAR_START <= int(date_end) <= YEAR_END):
        return False
    type_blob = " ".join([fields.get("type", ""), fields.get("format", ""), fields.get("formaa", "")]).lower()
    if any(term in type_blob for term in EXCLUDED_TYPE_TERMS):
        return False
    return "image" in type_blob or "pdf" in type_blob or "text" in type_blob


def series_key(title: str) -> str:
    title = re.sub(r"\b(18|19|20)\d{2}[-./]\d{2}[-./]\d{2}\b", "", title)
    title = re.sub(r"\b(18|19|20)\d{2}[-./]\d{2}\b", "", title)
    title = re.sub(r"\bv\.?\s*\d+.*$", "", title, flags=re.I)
    title = re.sub(r"\bvolume\s+\d+.*$", "", title, flags=re.I)
    title = re.sub(r"[,;:]+$", "", title)
    return clean(title.lower(), max_chars=90)


def row_from_raw(path: Path, detail: dict[str, Any]) -> dict[str, str] | None:
    fields = field_map(detail)
    title = fields.get("title") or clean(detail.get("title")) or path.stem
    collection, item_id = collection_and_item(detail)
    if not collection or not item_id:
        return None
    date_start, date_end, date_text = date_fields(fields, title)
    if not is_candidate(fields, date_end):
        return None
    image_url = absolute_image_url(clean(detail.get("imageUri") or detail.get("thumbnailUri"), max_chars=1000))
    if not image_url:
        return None

    viewer = source_record_url(collection, item_id)
    description = clean(
        fields.get("descri")
        or fields.get("description")
        or fields.get("public")
        or fields.get("publication_information"),
        max_chars=1200,
    )
    subjects = clean(
        "; ".join(
            [
                fields.get("subjec", ""),
                fields.get("subject", ""),
                fields.get("subject_(names)", ""),
                fields.get("covera", ""),
            ]
        ),
        max_chars=900,
    )
    medium = clean("; ".join([fields.get("format", ""), fields.get("formaa", ""), fields.get("type", "")]))
    collection_name = fields.get("cdmcoll") or fields.get("collection") or fields.get("digital_collection")
    rights_text = fields.get("rightl") or fields.get("local_rights_statement") or "Local rights statement not found in CONTENTdm item fields."
    basis = "GSU CONTENTdm item exposes a source-hosted IIIF image/thumbnail; use source-linked display and keep item-level rights visible."
    rights = mc.image_fields(
        "IMG02",
        basis,
        image_url=image_url,
        viewer=viewer,
        confidence="medium",
        rights_review_required=True,
        local_copy_permitted=False,
        note="Source-hosted CONTENTdm image candidate; no local copy.",
    )
    row = {
        "capture_id": "",
        "direction_id": "GSU04",
        "direction_name": "gsu_raw_harvest_local_university_print_culture",
        "source_id": SOURCE_ID,
        "source_name": SOURCE_NAME,
        "source_api_url": viewer,
        "capture_status": "captured_from_raw",
        "source_identifier": f"{collection}:{item_id}",
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
        "source_description": description,
        "source_notes": clean("; ".join([fields.get("identi", ""), fields.get("curato", ""), fields.get("digita", "")]), max_chars=900),
        "source_subjects": subjects,
        "source_rights_text": rights_text,
        "rights_uri": "",
        "raw_json_path": str(path.relative_to(ROOT)),
        "access_date": ACCESS_DATE,
        **rights,
    }
    row["image_expectation"] = "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["source_description_raw"] = description
    row["ocr_or_excerpt"] = description or subjects or fields.get("public") or fields.get("publication_information")
    row["editorial_summary"] = mx.clean(
        f"{title} is indexed from GSU Library Digital Collections. {description or subjects or medium}",
        max_chars=680,
    )
    row["historical_context_note"] = (
        "GSU CONTENTdm adds local and university-held evidence for periodicals, "
        "labor print culture, civil-rights adjacent publications, and regional "
        "public graphic communication in the 1931-1970 interval."
    )
    row["classification_rationale"] = (
        "Selected from already captured CONTENTdm raw records by date, image/PDF "
        "presence, source collection, subject terms, and per-collection caps to "
        "avoid flooding the archive with serial issue duplicates."
    )
    row["uncertainty_note"] = "Item-level rights statements remain authoritative; display is source-hosted and reversible."
    row["citation_basis"] = f"Georgia State University Library Digital Collections. {title}. {viewer}. Accessed {ACCESS_DATE}."
    row["_collection"] = collection
    row["_series"] = series_key(title)
    row["_date_sort"] = date_start or date_end or "9999"
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def harvest_rows() -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_raw_titles: set[tuple[str, str]] = set()
    for path in sorted(RAW_DIR.glob("*.json")):
        if "_search_" in path.name:
            continue
        detail = json.loads(path.read_text(encoding="utf-8"))
        row = row_from_raw(path, detail)
        if not row:
            continue
        identifier = row["source_identifier"]
        title_key = (row["_collection"], row["_series"])
        if identifier in seen_ids or title_key in seen_raw_titles and row["_collection"] not in {"IAM", "GSB", "gae"}:
            continue
        seen_ids.add(identifier)
        seen_raw_titles.add(title_key)
        candidates.append(row)

    candidates.sort(
        key=lambda row: (
            COLLECTION_PRIORITY.get(row["_collection"], 99),
            int(row.get("date_start") or row.get("date_end") or 9999),
            row.get("source_title", ""),
        )
    )

    selected: list[dict[str, str]] = []
    by_collection: Counter[str] = Counter()
    for row in candidates:
        collection = row["_collection"]
        limit = COLLECTION_LIMITS.get(collection, 1)
        if by_collection[collection] >= limit:
            continue
        by_collection[collection] += 1
        selected.append(row)

    selected.sort(key=lambda row: (int(row.get("date_start") or row.get("date_end") or 9999), row.get("source_title", "")))
    for index, row in enumerate(selected, start=1):
        row["capture_id"] = f"GSU1970R{index:03d}"
        for internal in ("_collection", "_series", "_date_sort"):
            row.pop(internal, None)
    return selected


def write_records(rows: list[dict[str, str]]) -> None:
    with RECORDS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["direction_id"], row["source_id"], row["source_name"])].append(row)
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
        for (direction_id, source_id, source_name), items in sorted(grouped.items()):
            counter = Counter(row["image_presence_code"] for row in items)
            writer.writerow(
                {
                    "direction_id": direction_id,
                    "source_id": source_id,
                    "source_name": source_name,
                    "captured_count": len(items),
                    "failure_count": 0,
                    "img00_count": counter.get("IMG00", 0),
                    "img01_count": counter.get("IMG01", 0),
                    "img02_count": counter.get("IMG02", 0),
                    "img03_count": counter.get("IMG03", 0),
                    "img04_count": counter.get("IMG04", 0),
                    "notes": "Offline raw harvest from GSU CONTENTdm; per-collection caps reduce serial duplicate flooding.",
                }
            )


def main() -> None:
    rows = harvest_rows()
    write_records(rows)
    print(f"captured={len(rows)}")
    print(f"image_states={dict(Counter(row['image_presence_code'] for row in rows))}")


if __name__ == "__main__":
    main()
