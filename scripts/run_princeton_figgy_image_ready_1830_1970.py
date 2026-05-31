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
RAW_DIR = DATA / "capture_batch_princeton_figgy_image_ready_1830_1970_raw"
RECORDS_CSV = DATA / "capture_batch_princeton_figgy_image_ready_1830_1970_records.csv"
SUMMARY_CSV = DATA / "capture_batch_princeton_figgy_image_ready_1830_1970_source_summary.csv"

ACCESS_DATE = "2026-05-31"
SOURCE_ID = "SRC130"
SOURCE_NAME = "Princeton University Library Digital Collections / Figgy"
USER_AGENT = "ModernGDHistory/0.1 figgy-image-ready"
YEAR_START = 1830
YEAR_END = 1970
MAX_ROWS = 90
FIELDNAMES = mx.FIELDNAMES

QUERY_PLAN = [
    ("PUL01", "princeton_posters", "poster", 30),
    ("PUL02", "princeton_war_posters", '"war poster"', 24),
    ("PUL03", "princeton_advertising_print", "advertising poster", 18),
    ("PUL04", "princeton_graphic_ephemera", "graphic design OR typography OR broadside", 18),
]

OPEN_LICENSE_MARKERS = ("pdm", "publicdomain", "cc0", "creativecommons.org/publicdomain")


def strip_markup(value: Any, *, max_chars: int = 700) -> str:
    if isinstance(value, list):
        value = "; ".join(strip_markup(item, max_chars=max_chars) for item in value if item)
    if isinstance(value, dict):
        value = value.get("@value") or value.get("value") or json.dumps(value, ensure_ascii=False)
    value = html.unescape(str(value or ""))
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:max_chars]


def fetch_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def search_url(query: str, page: int = 1) -> str:
    params = {"q": query, "search_field": "all_fields", "page": str(page)}
    return "https://figgy.princeton.edu/catalog.json?" + urllib.parse.urlencode(params)


def manifest_url(resource_id: str) -> str:
    return f"https://figgy.princeton.edu/concern/scanned_resources/{resource_id}/manifest"


def metadata_value(manifest: dict[str, Any], label: str) -> str:
    for item in manifest.get("metadata", []):
        if strip_markup(item.get("label")).lower() == label.lower():
            return strip_markup(item.get("value"), max_chars=1000)
    return ""


def first_year(value: str) -> int | None:
    match = re.search(r"(?<!\d)(18[3-9]\d|19[0-6]\d|1970)(?!\d)", value or "")
    return int(match.group(1)) if match else None


def date_fields(manifest: dict[str, Any], attributes: dict[str, Any]) -> tuple[str, str, str]:
    date_text = metadata_value(manifest, "Date")
    if not date_text:
        date_text = strip_markup(attributes.get("readonly_date_ssim", {}).get("attributes", {}).get("value"))
    years = [int(year) for year in re.findall(r"(?<!\d)(18[3-9]\d|19[0-6]\d|1970)(?!\d)", date_text)]
    if not years:
        return "", "", date_text
    return str(min(years)), str(max(years)), date_text


def in_scope(date_start: str, date_end: str, date_text: str) -> bool:
    year = int(date_end) if date_end else first_year(date_text)
    return year is not None and YEAR_START <= year <= YEAR_END


def first_image(manifest: dict[str, Any]) -> tuple[str, str]:
    sequences = manifest.get("sequences") or []
    canvases = sequences[0].get("canvases", []) if sequences else []
    for canvas in canvases:
        for image in canvas.get("images", []):
            resource = image.get("resource") or {}
            url = strip_markup(resource.get("@id"), max_chars=1000)
            service = resource.get("service") or {}
            service_id = strip_markup(service.get("@id"), max_chars=1000)
            if service_id:
                return f"{service_id}/full/900,/0/default.jpg", service_id
            if url:
                return url, ""
    thumb = manifest.get("thumbnail")
    if isinstance(thumb, dict):
        return strip_markup(thumb.get("@id"), max_chars=1000), ""
    return "", ""


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


def row_from_result(result: dict[str, Any], manifest: dict[str, Any], direction_id: str, direction_name: str, api_url: str, raw_path: str) -> dict[str, str] | None:
    resource_id = result.get("id")
    if not resource_id:
        return None
    attributes = result.get("attributes") or {}
    date_start, date_end, date_text = date_fields(manifest, attributes)
    if not in_scope(date_start, date_end, date_text):
        return None
    image_url, service_id = first_image(manifest)
    if not image_url:
        return None

    license_uri = strip_markup(manifest.get("license"), max_chars=400)
    code = "IMG03" if any(marker in license_uri.lower().replace("/", "") for marker in OPEN_LICENSE_MARKERS) else "IMG02"
    basis = (
        "Princeton Figgy manifest exposes an IIIF image and an open/public-domain license signal."
        if code == "IMG03"
        else "Princeton Figgy manifest exposes a source-hosted IIIF image, but the rights statement is not an explicit reuse grant."
    )
    rights = mc.image_fields(
        code,
        basis,
        image_url=image_url,
        viewer=manifest.get("@id") or manifest_url(resource_id),
        confidence="high" if code == "IMG03" else "medium",
        rights_review_required=code != "IMG03",
        local_copy_permitted=False,
        note="Keep Princeton source/manifest link visible; do not treat IIIF availability as ownership by this project.",
    )
    title = strip_markup(manifest.get("label") or attributes.get("title"), max_chars=500)
    description = strip_markup(manifest.get("description") or metadata_value(manifest, "Abstract") or metadata_value(manifest, "Contents"), max_chars=900)
    medium = strip_markup("; ".join([metadata_value(manifest, "Type"), metadata_value(manifest, "Extent"), metadata_value(manifest, "Content Type")]))
    subjects = strip_markup("; ".join([metadata_value(manifest, "Subject"), metadata_value(manifest, "Language")]), max_chars=700)
    source_url = strip_markup((result.get("links") or {}).get("self")) or f"https://figgy.princeton.edu/catalog/{resource_id}"
    row = {
        "capture_id": "",
        "direction_id": direction_id,
        "direction_name": direction_name,
        "source_id": SOURCE_ID,
        "source_name": SOURCE_NAME,
        "source_api_url": api_url,
        "capture_status": "captured",
        "source_identifier": str(resource_id),
        "source_record_url": source_url,
        "source_title": title,
        "source_creator": metadata_value(manifest, "Creator"),
        "source_date_text": date_text,
        "date_start": date_start,
        "date_end": date_end,
        "source_place_text": metadata_value(manifest, "Place") or "United States / Princeton",
        "source_object_type": metadata_value(manifest, "Type") or result.get("type") or "Scanned resource",
        "source_medium": medium,
        "source_collection": "Princeton University Library Digital Collections / Figgy",
        "source_description": description,
        "source_notes": strip_markup("; ".join([metadata_value(manifest, "Alternative"), metadata_value(manifest, "Identifier"), service_id]), max_chars=700),
        "source_subjects": subjects,
        "source_rights_text": license_uri or "Manifest rights statement not found.",
        "rights_uri": license_uri,
        "raw_json_path": raw_path,
        "access_date": ACCESS_DATE,
        **rights,
    }
    row["image_expectation"] = "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["source_description_raw"] = description
    row["ocr_or_excerpt"] = description or subjects
    row["editorial_summary"] = mx.clean(f"{title} is indexed from Princeton Figgy. {description or medium}", max_chars=560)
    row["historical_context_note"] = (
        "Captured through Princeton Figgy/IIIF to add university-held posters, ephemera, scanned resources, and source-hosted images outside the large museum API cluster."
    )
    row["classification_rationale"] = "Provisional folders derive from Figgy manifest label, date, type, extent, abstract, subject and IIIF metadata."
    row["uncertainty_note"] = "IIIF availability is treated as source-hosted display evidence, not as a reuse claim, unless the manifest license is explicitly open."
    row["citation_basis"] = f"Princeton University Library Digital Collections / Figgy. {title}. {source_url}. Accessed {ACCESS_DATE}."
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    seen = existing_keys()
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []

    for direction_id, direction_name, query, limit in QUERY_PLAN:
        page = 1
        direction_count = 0
        while direction_count < limit and len(rows) < MAX_ROWS:
            url = search_url(query, page)
            try:
                payload = fetch_json(url)
            except Exception as exc:  # noqa: BLE001
                failures.append({"direction_id": direction_id, "source_name": SOURCE_NAME, "error": str(exc)})
                break
            write_raw(f"{direction_name}_search_{page}.json", payload)
            results = payload.get("data", [])
            if not results:
                break
            added = 0
            for result in results:
                resource_id = result.get("id")
                if not resource_id:
                    continue
                try:
                    manifest = fetch_json(manifest_url(resource_id))
                except Exception as exc:  # noqa: BLE001
                    failures.append({"direction_id": direction_id, "source_name": SOURCE_NAME, "error": f"manifest {resource_id}: {exc}"})
                    continue
                raw_path = write_raw(f"{direction_name}_manifest_{resource_id}.json", manifest)
                row = row_from_result(result, manifest, direction_id, direction_name, url, raw_path)
                if not row:
                    continue
                key = (row["source_name"], row["source_identifier"])
                if key in seen:
                    continue
                seen.add(key)
                rows.append(row)
                direction_count += 1
                added += 1
                if direction_count >= limit or len(rows) >= MAX_ROWS:
                    break
                time.sleep(0.12)
            if added == 0 and page >= 5:
                break
            page += 1
            time.sleep(0.35)

    rows.sort(key=lambda r: (int(r["date_start"]) if r.get("date_start") else 9999, r.get("source_title", "")))
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"PUL1970R{index:03d}"

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
                    "notes": "University Figgy/IIIF source-hosted image batch; rights remain item/manifest dependent.",
                }
            )

    print(f"captured={len(rows)}")
    print(f"image_states={dict(Counter(row['image_presence_code'] for row in rows))}")
    print(f"failures={len(failures)}")


if __name__ == "__main__":
    main()
