from __future__ import annotations

import csv
import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import run_midcentury_capture_1930_1970 as mc
import run_wikimedia_commons_image_ready_1830_1970 as commons


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_noncanonical_movement_commons_1930_2000_raw"
RECORDS_CSV = DATA / "capture_batch_noncanonical_movement_commons_1930_2000_records.csv"
SUMMARY_CSV = DATA / "capture_batch_noncanonical_movement_commons_1930_2000_source_summary.csv"

ACCESS_DATE = "2026-05-31"
SOURCE_ID = commons.SOURCE_ID
SOURCE_NAME = commons.SOURCE_NAME
FIELDNAMES = commons.FIELDNAMES
YEAR_START = 1930
YEAR_END = 2000
MAX_ROWS = 48

MOVEMENT_PLAN = [
    {
        "direction_id": "NCM01",
        "direction_name": "commons_taller_de_grafica_popular_records",
        "query": '"Taller de Gráfica Popular" OR "Taller de Grafica Popular" OR "TGP Mexico print"',
        "limit": 10,
        "region": "Mexico",
        "movement_id": "RM078",
        "movement_label": "Taller de Grafica Popular first-ingest scope",
        "required_terms": ["taller", "grafica", "gráfica", "tgp", "mendez", "méndez", "corrido"],
    },
    {
        "direction_id": "NCM02",
        "direction_name": "commons_medu_anti_apartheid_records",
        "query": '"Medu Art Ensemble" poster OR "anti-apartheid poster" OR "Thami Mnyele poster"',
        "limit": 8,
        "region": "South Africa / Botswana",
        "movement_id": "RM086",
        "movement_label": "Medu Art Ensemble and anti-apartheid poster movement",
        "required_terms": ["medu", "anti-apartheid", "apartheid", "mnyele", "aggression"],
    },
    {
        "direction_id": "NCM03",
        "direction_name": "commons_ospaaal_solidarity_records",
        "query": '"OSPAAAL" poster OR "Tricontinental" poster',
        "limit": 8,
        "region": "Cuba / transnational",
        "movement_id": "RM090",
        "movement_label": "OSPAAAL and Tricontinental solidarity graphics",
        "required_terms": ["ospaaal", "tricontinental", "solidarity", "che"],
    },
    {
        "direction_id": "NCM04",
        "direction_name": "commons_palestinian_poster_records",
        "query": '"Palestinian poster" OR "Palestinian Women on the Frontline" OR "Palestinian Communist Party"',
        "limit": 8,
        "region": "Palestine / transnational",
        "movement_id": "RM091",
        "movement_label": "Palestinian liberation and solidarity poster culture",
        "required_terms": ["palestinian", "palestine", "intifada"],
    },
    {
        "direction_id": "NCM05",
        "direction_name": "commons_naidoc_and_indigenous_poster_records",
        "query": '"NAIDOC poster" OR "Aboriginal land rights poster" OR "Indigenous poster Australia"',
        "limit": 8,
        "region": "Australia / Indigenous",
        "movement_id": "RM087",
        "movement_label": "Aboriginal land-rights and NAIDOC poster cultures",
        "required_terms": ["naidoc", "aboriginal", "indigenous", "land rights"],
    },
    {
        "direction_id": "NCM06",
        "direction_name": "commons_latin_american_political_graphics",
        "query": '"Brigadas Ramona Parra" OR "Ramona Parra poster"',
        "limit": 10,
        "region": "Latin America",
        "movement_id": "RM079",
        "movement_label": "Brigadas Ramona Parra first-ingest scope",
        "required_terms": ["ramona parra", "brigadas"],
    },
]


def write_raw(name: str, payload: dict[str, Any]) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path.relative_to(ROOT))


def existing_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in DATA.glob("capture_batch_*_records.csv"):
        if path == RECORDS_CSV:
            continue
        if not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                keys.add((row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", "")))
    return keys


def year_from_blob(blob: str) -> int | None:
    years = [int(year) for year in re.findall(r"(?<!\d)((?:19|20)\d{2})(?!\d)", blob or "")]
    years = [year for year in years if YEAR_START <= year <= YEAR_END]
    return min(years) if years else None


def title_has_later_year(title: str) -> bool:
    years = [int(year) for year in re.findall(r"(?<!\d)(20\d{2})(?!\d)", title or "")]
    return any(year > YEAR_END for year in years)


def movement_relevant(plan: dict[str, Any], blob: str) -> bool:
    blob_l = blob.lower()
    return any(term.lower() in blob_l for term in plan["required_terms"])


def row_from_page(page: dict[str, Any], plan: dict[str, Any], api_url: str, raw_path: str) -> dict[str, str] | None:
    imageinfos = page.get("imageinfo") or []
    if not imageinfos:
        return None
    info = imageinfos[0]
    if not str(info.get("mime", "")).startswith("image/"):
        return None
    title = commons.clean(page.get("title", "")).replace("File:", "", 1)
    if title.lower().endswith((".djvu", ".pdf", ".svg")):
        return None
    if title_has_later_year(title):
        return None
    meta = commons.extmeta(info)
    blob = " ".join(
        [
            title,
            meta.get("ObjectName", ""),
            meta.get("ImageDescription", ""),
            meta.get("Categories", ""),
            meta.get("Credit", ""),
            plan["movement_label"],
        ]
    )
    blob_l = blob.lower()
    if "photograph" in blob_l and not any(term in blob_l for term in ["poster", "placard", "print"]):
        return None
    if not movement_relevant(plan, blob):
        return None
    year = year_from_blob(blob)
    if year is None or not (YEAR_START <= year <= YEAR_END):
        return None
    if not commons.is_open(meta):
        return None

    image_url = commons.clean(info.get("thumburl") or info.get("url"))
    source_url = commons.clean(info.get("descriptionurl") or info.get("descriptionshorturl"))
    if not image_url or not source_url:
        return None
    license_label = commons.clean(meta.get("LicenseShortName") or meta.get("UsageTerms") or meta.get("License"))
    description = commons.clean(meta.get("ImageDescription") or meta.get("ObjectName") or title, max_chars=900)
    categories = commons.clean(meta.get("Categories"), max_chars=900)
    rights = mc.image_fields(
        "IMG03",
        f"Wikimedia Commons open-license metadata: {license_label}. Commons is used only as a rights-aware image/display layer.",
        image_url=image_url,
        viewer=source_url,
        confidence="high",
        rights_review_required=False,
        local_copy_permitted=False,
        note="Verify original holding context where Commons credits another archive or institution.",
    )
    row = {
        "capture_id": "",
        "direction_id": plan["direction_id"],
        "direction_name": plan["direction_name"],
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
        "source_place_text": plan["region"],
        "source_object_type": "movement-linked open image record",
        "source_medium": "poster / print / campaign graphic",
        "source_collection": commons.clean(meta.get("Credit") or "Wikimedia Commons"),
        "source_description": description,
        "source_notes": commons.clean("; ".join([meta.get("ObjectName", ""), meta.get("DateTimeOriginal", ""), categories]), max_chars=900),
        "source_subjects": commons.clean(f"{plan['movement_label']}; {categories}", max_chars=900),
        "source_rights_text": commons.clean("; ".join([license_label, meta.get("UsageTerms", ""), meta.get("LicenseUrl", "")])),
        "rights_uri": commons.clean(meta.get("LicenseUrl")),
        "raw_json_path": raw_path,
        "access_date": ACCESS_DATE,
        **rights,
    }
    row["image_expectation"] = "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["source_description_raw"] = description
    row["ocr_or_excerpt"] = description
    row["historical_context_note"] = (
        f"Noncanonical movement image supplement for {plan['movement_label']}. "
        "The record is used to make counterpublic, regional, and solidarity graphics visible while retaining Commons as a secondary display source."
    )
    row["classification_rationale"] = (
        f"Movement assignment is limited to explicit query/category evidence for {plan['movement_id']} and direct title/description/category terms; visual resemblance alone is not used."
    )
    row["uncertainty_note"] = (
        "Commons metadata may be user-supplied or may mirror another holding institution. Treat the record as image access evidence, not as final authority."
    )
    row["citation_basis"] = f"Wikimedia Commons. {title}. {source_url}. Accessed {ACCESS_DATE}."
    row["editorial_summary"] = commons.clean(
        f"{title} is an openly licensed movement-linked image record. {description}",
        max_chars=700,
    )
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def main() -> None:
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    seen = existing_keys()

    for plan in MOVEMENT_PLAN:
        added_for_plan = 0
        offset = 0
        while added_for_plan < plan["limit"] and len(rows) < MAX_ROWS:
            url = commons.search_url(plan["query"], offset=offset, limit=30)
            try:
                payload = commons.fetch_json(url)
            except Exception as exc:  # noqa: BLE001
                failures.append({"direction_id": plan["direction_id"], "source_name": SOURCE_NAME, "error": str(exc)})
                break
            raw_path = write_raw(f"{plan['direction_name']}_{offset}.json", payload)
            pages = list((payload.get("query", {}).get("pages") or {}).values())
            if not pages:
                break
            for page in sorted(pages, key=lambda item: item.get("index", 9999)):
                row = row_from_page(page, plan, url, raw_path)
                if not row:
                    continue
                key = (row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", ""))
                if key in seen:
                    continue
                seen.add(key)
                rows.append(row)
                added_for_plan += 1
                if added_for_plan >= plan["limit"] or len(rows) >= MAX_ROWS:
                    break
            if "continue" not in payload:
                break
            offset = int(payload.get("continue", {}).get("gsroffset", offset + 30))
            if offset > 180:
                break
            time.sleep(0.7)

    rows.sort(key=lambda r: (int(r["date_start"]) if r.get("date_start") else 9999, r.get("source_title", "")))
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"NCM2026R{index:03d}"
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
        for plan in MOVEMENT_PLAN:
            items = grouped.get(plan["direction_id"], [])
            counter = Counter(row["image_presence_code"] for row in items)
            writer.writerow(
                {
                    "direction_id": plan["direction_id"],
                    "source_id": SOURCE_ID,
                    "source_name": SOURCE_NAME,
                    "captured_count": len(items),
                    "failure_count": sum(1 for failure in failures if failure["direction_id"] == plan["direction_id"]),
                    "img00_count": counter.get("IMG00", 0),
                    "img01_count": counter.get("IMG01", 0),
                    "img02_count": counter.get("IMG02", 0),
                    "img03_count": counter.get("IMG03", 0),
                    "img04_count": counter.get("IMG04", 0),
                    "notes": f"Noncanonical movement image supplement for {plan['movement_label']}; Commons is secondary display evidence.",
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
