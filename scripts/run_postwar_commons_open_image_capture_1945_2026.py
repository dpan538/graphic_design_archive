from __future__ import annotations

import csv
import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

import run_midcentury_capture_1930_1970 as mc
import run_wikimedia_commons_image_ready_1830_1970 as commons


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_postwar_commons_open_image_1945_2026_raw"
RECORDS_CSV = DATA / "capture_batch_postwar_commons_open_image_1945_2026_records.csv"
SUMMARY_CSV = DATA / "capture_batch_postwar_commons_open_image_1945_2026_source_summary.csv"

ACCESS_DATE = "2026-06-02"
SOURCE_ID = "SRC012"
SOURCE_NAME = "Wikimedia Commons"
FIELDNAMES = commons.FIELDNAMES
YEAR_START = 1945
YEAR_END = 2026
MAX_ROWS = 48

QUERY_PLAN = [
    ("PWC01", "commons_cuban_poster_open_images", '"Cuban poster" poster', 10),
    ("PWC02", "commons_chinese_propaganda_postwar_open_images", '"Chinese propaganda poster"', 10),
    ("PWC03", "commons_munich_1972_pictogram_open_images", '"Olympic games 1972" pictogram', 8),
    ("PWC04", "commons_hong_kong_poster_open_images", '"Hong Kong poster"', 6),
    ("PWC05", "commons_indonesian_poster_open_images", '"Indonesian poster" poster', 6),
    ("PWC06", "commons_korean_poster_open_images", '"Korean poster" poster', 5),
    ("PWC07", "commons_palestinian_poster_open_images", '"Palestinian poster" poster', 5),
    ("PWC08", "commons_apartheid_poster_open_images", '"apartheid poster"', 5),
]

RELEVANCE_TERMS = (
    "poster",
    "affiche",
    "plakat",
    "pictogram",
    "propaganda",
    "graphic",
    "typography",
    "visual communication",
    "olympic games 1972",
    "munich 1972",
)

NOISE_TERMS = (
    "blank map",
    "coat of arms",
    "logo.svg",
    "icon.png",
    "wikipedia-logo",
)


def existing_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in DATA.glob("capture_batch_*_records.csv"):
        if path == RECORDS_CSV:
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                keys.add((row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", "")))
    return keys


def write_raw(name: str, payload: dict) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path.relative_to(ROOT))


def evidence_blob(title: str, meta: dict[str, str]) -> str:
    # Do not use DateTime/DateTimeOriginal here; those often describe a scan or
    # photo date rather than the graphic object date.
    return " ".join(
        [
            title,
            meta.get("ObjectName", ""),
            meta.get("ImageDescription", ""),
            meta.get("Categories", ""),
        ]
    )


def postwar_year(blob: str) -> int | None:
    years = [int(year) for year in re.findall(r"(?<!\d)((?:19|20)\d{2})(?!\d)", blob or "")]
    years = [year for year in years if YEAR_START <= year <= YEAR_END]
    return min(years) if years else None


def relevant(title: str, meta: dict[str, str], direction_name: str) -> bool:
    blob = evidence_blob(title, meta).lower()
    if any(term in blob for term in NOISE_TERMS):
        return False
    if "pictogram" in direction_name:
        return "1972" in blob and ("pictogram" in blob or "olympic" in blob)
    return any(term in blob for term in RELEVANCE_TERMS)


def row_from_page(page: dict, direction_id: str, direction_name: str, api_url: str) -> dict[str, str] | None:
    imageinfos = page.get("imageinfo") or []
    if not imageinfos:
        return None
    info = imageinfos[0]
    title = commons.clean(page.get("title", "")).replace("File:", "", 1)
    if title.lower().endswith((".djvu", ".pdf", ".svg")):
        return None
    if not str(info.get("mime", "")).startswith("image/"):
        return None
    meta = commons.extmeta(info)
    blob = evidence_blob(title, meta)
    year = postwar_year(blob)
    if year is None or not commons.is_open(meta) or not relevant(title, meta, direction_name):
        return None

    image_url = commons.clean(info.get("thumburl") or info.get("url"))
    source_url = commons.clean(info.get("descriptionurl") or info.get("descriptionshorturl"))
    license_label = commons.clean(meta.get("LicenseShortName") or meta.get("UsageTerms") or meta.get("License"))
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
    description = commons.clean(meta.get("ImageDescription") or meta.get("ObjectName") or title, max_chars=900)
    categories = commons.clean(meta.get("Categories"), max_chars=900)
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
        "source_creator": commons.clean(meta.get("Artist")),
        "source_date_text": str(year),
        "date_start": str(year),
        "date_end": str(year),
        "source_place_text": commons.region_hint(blob),
        "source_object_type": "Open image record; postwar poster/pictogram candidate",
        "source_medium": "poster / pictogram / graphic record",
        "source_collection": commons.clean(meta.get("Credit") or "Wikimedia Commons"),
        "source_description": description,
        "source_notes": commons.clean("; ".join([meta.get("ObjectName", ""), categories]), max_chars=900),
        "source_subjects": categories,
        "source_rights_text": commons.clean("; ".join([license_label, meta.get("UsageTerms", ""), meta.get("LicenseUrl", "")])),
        "rights_uri": commons.clean(meta.get("LicenseUrl")),
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
        "Postwar Commons open-image supplement for visual anchors. Commons is used as a rights-visible display layer and must not replace the original holding or creator source."
    )
    row["classification_rationale"] = (
        "Selected by targeted postwar Commons query, open-license metadata, duplicate exclusion, and year evidence from title/description/category fields rather than scan/upload date."
    )
    row["uncertainty_note"] = "Commons metadata is user-maintained; verify object date and original institutional source before treating this as authority evidence."
    row["citation_basis"] = f"Wikimedia Commons. {title}. {source_url}. Accessed {ACCESS_DATE}."
    row["editorial_summary"] = commons.clean(f"{title} is an openly licensed postwar Commons image record. {description}", max_chars=760)
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def main() -> None:
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    seen = existing_keys()

    for direction_id, direction_name, query, limit in QUERY_PLAN:
        direction_count = 0
        offset = 0
        while direction_count < limit and len(rows) < MAX_ROWS:
            url = commons.search_url(query, offset=offset, limit=50)
            try:
                payload = commons.fetch_json(url)
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
            if "continue" not in payload or (added == 0 and offset >= 100):
                break
            offset = int(payload.get("continue", {}).get("gsroffset", offset + 50))
            time.sleep(0.7)

    rows.sort(key=lambda row: (int(row["date_start"]) if row.get("date_start") else 9999, row.get("source_title", "")))
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"PWC2026R{index:03d}"
        for field in FIELDNAMES:
            row.setdefault(field, "")

    with RECORDS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["direction_id"]].append(row)
    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        fields = ["direction_id", "source_id", "source_name", "captured_count", "failure_count", "img00_count", "img01_count", "img02_count", "img03_count", "img04_count", "notes"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for direction_id, items in sorted(grouped.items()):
            counter = Counter(row["image_presence_code"] for row in items)
            writer.writerow(
                {
                    "direction_id": direction_id,
                    "source_id": SOURCE_ID,
                    "source_name": SOURCE_NAME,
                    "captured_count": len(items),
                    "failure_count": sum(1 for failure in failures if failure["direction_id"] == direction_id),
                    "img00_count": counter.get("IMG00", 0),
                    "img01_count": counter.get("IMG01", 0),
                    "img02_count": counter.get("IMG02", 0),
                    "img03_count": counter.get("IMG03", 0),
                    "img04_count": counter.get("IMG04", 0),
                    "notes": "Postwar Commons open-image supplement; object dates require verification against original sources.",
                }
            )

    counter = Counter(row["image_presence_code"] for row in rows)
    print(f"captured={len(rows)}")
    print(f"image_states={dict(counter)}")
    if failures:
        print(f"failures={len(failures)}")
        for failure in failures[:8]:
            print(f"- {failure['direction_id']}: {failure['error']}")


if __name__ == "__main__":
    main()
