from __future__ import annotations

import csv
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import run_midcentury_capture_1930_1970 as mc
import run_midcentury_expansion_capture_1931_1970 as mx


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_gallica_image_ready_1830_1970_raw"
RECORDS_CSV = DATA / "capture_batch_gallica_image_ready_1830_1970_records.csv"
SUMMARY_CSV = DATA / "capture_batch_gallica_image_ready_1830_1970_source_summary.csv"

ACCESS_DATE = "2026-05-31"
CAPTURE_BATCH_ID = "CB-GALLICA-IMAGE-READY-1830-1970"
SOURCE_ID = "SRC023"
SOURCE_NAME = "Gallica / BnF APIs"
USER_AGENT = "ModernGDHistory/0.1 gallica-image-ready"
YEAR_START = 1830
YEAR_END = 1970
MAX_ROWS = 120

FIELDNAMES = mx.FIELDNAMES

NS = {
    "srw": "http://www.loc.gov/zing/srw/",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
    "dc": "http://purl.org/dc/elements/1.1/",
}

QUERY_PLAN = [
    ("GA01", "gallica_affiche_1830_1930", 'dc.description all "Affiche" and dc.date >= "1830" and dc.date <= "1930"', 40),
    ("GA02", "gallica_affiche_1931_1970", 'dc.description all "Affiche" and dc.date >= "1931" and dc.date <= "1970"', 50),
    ("GA03", "gallica_publicite_1830_1970", 'dc.title all "publicité" and dc.date >= "1830" and dc.date <= "1970"', 15),
    ("GA04", "gallica_arts_graphiques_1830_1970", 'dc.title all "arts graphiques" and dc.date >= "1830" and dc.date <= "1970"', 15),
]


def fetch_text(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/xml,text/xml,*/*"},
    )
    with urllib.request.urlopen(req, timeout=35) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def sru_url(query: str, *, start: int = 1, maximum: int = 50) -> str:
    return "https://gallica.bnf.fr/SRU?" + urllib.parse.urlencode(
        {
            "operation": "searchRetrieve",
            "version": "1.2",
            "maximumRecords": str(maximum),
            "startRecord": str(start),
            "query": query,
        }
    )


def values(dc: ET.Element, tag: str) -> list[str]:
    return [
        mx.clean(el.text or "", max_chars=900)
        for el in dc.findall(f"dc:{tag}", NS)
        if mx.clean(el.text or "", max_chars=900)
    ]


def first(values_: list[str]) -> str:
    return values_[0] if values_ else ""


def extract_ark(identifiers: list[str]) -> str:
    for identifier in identifiers:
        match = re.search(r"ark:/12148/([A-Za-z0-9]+)", identifier)
        if match:
            return match.group(1)
    return ""


def year_pair(date_values: list[str]) -> tuple[str, str, str]:
    date_text = "; ".join(date_values)
    years: list[int] = []
    for value in date_values:
        years.extend(int(y) for y in re.findall(r"(?<!\d)(18[3-9]\d|19[0-6]\d|1970)(?!\d)", value))
    if not years:
        year = mc.first_year(date_text)
        years = [year] if year else []
    if not years:
        return "", "", date_text
    return str(min(years)), str(max(years)), date_text or str(min(years))


def in_scope(date_start: str, date_end: str, date_text: str) -> bool:
    start = int(date_start) if date_start else mc.first_year(date_text)
    end = int(date_end) if date_end else start
    if end is None:
        return False
    return YEAR_START <= end <= YEAR_END


def image_fields(rights_values: list[str], ark: str) -> dict[str, str]:
    rights_blob = " ".join(rights_values).lower()
    manifest = f"https://gallica.bnf.fr/iiif/ark:/12148/{ark}/manifest.json"
    image_url = f"https://gallica.bnf.fr/iiif/ark:/12148/{ark}/f1/full/700,/0/native.jpg"
    if "public domain" in rights_blob or "domaine public" in rights_blob:
        return mc.image_fields(
            "IMG03",
            "Gallica SRU metadata reports public-domain rights; IIIF image is source-hosted by BnF.",
            image_url=image_url,
            viewer=manifest,
            confidence="high",
            rights_review_required=True,
            local_copy_permitted=False,
            note="Open/public-domain candidate; cite Gallica conditions and keep source return visible.",
        )
    return mc.image_fields(
        "IMG02",
        "Gallica exposes an IIIF source-hosted image, but the SRU rights value is not an explicit public-domain signal.",
        image_url=image_url,
        viewer=manifest,
        confidence="medium",
        rights_review_required=True,
        local_copy_permitted=False,
        note="Source-hosted viewer candidate.",
    )


def row_from_dc(dc: ET.Element, direction_id: str, direction_name: str, api_url: str) -> dict[str, str] | None:
    identifiers = values(dc, "identifier")
    ark = extract_ark(identifiers)
    if not ark:
        return None
    date_start, date_end, date_text = year_pair(values(dc, "date"))
    if not in_scope(date_start, date_end, date_text):
        return None
    title = first(values(dc, "title")) or first(values(dc, "description")) or f"Gallica record {ark}"
    creators = values(dc, "creator")
    descriptions = values(dc, "description")
    formats = values(dc, "format")
    subjects = values(dc, "subject")
    publishers = values(dc, "publisher")
    relations = values(dc, "relation")
    rights_values = values(dc, "rights")
    record_url = f"https://gallica.bnf.fr/ark:/12148/{ark}"
    rights = image_fields(rights_values, ark)
    source_description = mx.clean("; ".join(descriptions + formats), max_chars=700)
    source_notes = mx.clean("; ".join(relations + publishers), max_chars=500)
    row = {
        "capture_id": "",
        "direction_id": direction_id,
        "direction_name": direction_name,
        "source_id": SOURCE_ID,
        "source_name": SOURCE_NAME,
        "source_api_url": api_url,
        "capture_status": "captured",
        "source_identifier": ark,
        "source_record_url": record_url,
        "source_title": title,
        "source_creator": "; ".join(creators),
        "source_date_text": date_text,
        "date_start": date_start,
        "date_end": date_end,
        "source_place_text": "France",
        "source_object_type": "Gallica visual/document record",
        "source_medium": "; ".join(formats) or "Poster / print / document",
        "source_collection": "Bibliothèque nationale de France / Gallica",
        "source_description": source_description,
        "source_notes": source_notes,
        "source_subjects": "; ".join(subjects),
        "source_rights_text": "; ".join(rights_values),
        "rights_uri": first([v for v in rights_values if v.startswith("http")]),
        "raw_json_path": "",
        "access_date": ACCESS_DATE,
        **rights,
    }
    row["image_expectation"] = "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["source_description_raw"] = source_description
    row["ocr_or_excerpt"] = source_description or source_notes
    row["historical_context_note"] = (
        "Captured through Gallica SRU and IIIF as a protocol-family source expansion. "
        "This strengthens European print, poster, advertising, and visual-document coverage outside the existing museum API cluster."
    )
    row["classification_rationale"] = (
        "Provisional folders derive from Gallica description/title/format/date fields; source remains authoritative for item identity and rights."
    )
    row["uncertainty_note"] = ""
    row["citation_basis"] = f"Gallica / BnF. {title}. {record_url}. Accessed {ACCESS_DATE}."
    row["editorial_summary"] = mx.clean(
        f"{title} is indexed from Gallica / BnF. {source_description or source_notes or row['source_rights_text']}",
        max_chars=560,
    )
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def parse_records(xml_text: str, direction_id: str, direction_name: str, api_url: str) -> list[dict[str, str]]:
    root = ET.fromstring(xml_text)
    rows: list[dict[str, str]] = []
    for record in root.findall(".//srw:recordData/oai_dc:dc", NS):
        row = row_from_dc(record, direction_id, direction_name, api_url)
        if row:
            rows.append(row)
    return rows


def existing_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in DATA.glob("capture_batch_*_records.csv"):
        if not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                keys.add((row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", "")))
    return keys


def write_raw(name: str, text: str) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    path.write_text(text, encoding="utf-8")
    return str(path.relative_to(ROOT))


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    seen = existing_keys()

    for direction_id, direction_name, query, limit in QUERY_PLAN:
        start = 1
        while len([r for r in rows if r["direction_id"] == direction_id]) < limit and len(rows) < MAX_ROWS:
            url = sru_url(query, start=start, maximum=50)
            try:
                xml_text = fetch_text(url)
            except Exception as exc:  # noqa: BLE001 - capture logs preserve source failure.
                failures.append({"direction_id": direction_id, "source_name": SOURCE_NAME, "error": str(exc)})
                break
            raw_path = write_raw(f"{direction_name}_{start}.xml", xml_text)
            parsed = parse_records(xml_text, direction_id, direction_name, url)
            if not parsed:
                break
            added = 0
            for row in parsed:
                key = (row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", ""))
                if key in seen:
                    continue
                seen.add(key)
                row["raw_json_path"] = raw_path
                rows.append(row)
                added += 1
                if len([r for r in rows if r["direction_id"] == direction_id]) >= limit or len(rows) >= MAX_ROWS:
                    break
            if added == 0 and len(parsed) < 50:
                break
            start += 50
            time.sleep(0.35)

    rows.sort(key=lambda r: (int(r["date_start"]) if r.get("date_start") else 9999, r.get("source_title", "")))
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"GA1970R{index:03d}"

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
                    "failure_count": str(sum(1 for f in failures if f["direction_id"] == direction_id)),
                    "img00_count": str(counter.get("IMG00", 0)),
                    "img01_count": str(counter.get("IMG01", 0)),
                    "img02_count": str(counter.get("IMG02", 0)),
                    "img03_count": str(counter.get("IMG03", 0)),
                    "img04_count": str(counter.get("IMG04", 0)),
                    "notes": "Gallica SRU/IIIF protocol-family image-ready capture.",
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
