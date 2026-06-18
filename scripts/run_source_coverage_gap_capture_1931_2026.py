#!/usr/bin/env python3
"""Source-coverage gap capture for underrepresented 1931-2026 records.

This pass is deliberately source-breadth first. It promotes only item-level
repository or archive records from sources that help repair regional coverage
gaps. Records without image evidence are retained as text/context evidence
rather than upgraded into image sheets.
"""

from __future__ import annotations

import csv
import html
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

import run_midcentury_capture_1930_1970 as mc
import run_midcentury_expansion_capture_1931_1970 as mx


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_source_coverage_gap_1931_2026_raw"
RECORDS_CSV = DATA / "capture_batch_source_coverage_gap_1931_2026_records.csv"
SUMMARY_CSV = DATA / "capture_batch_source_coverage_gap_1931_2026_source_summary.csv"
REPORT = ROOT / "docs" / "capture" / "SOURCE_COVERAGE_GAP_CAPTURE_1931_2026.md"

ACCESS_DATE = "2026-06-02"
USER_AGENT = "ModernGDHistory/0.1 source-coverage-gap-capture"
YEAR_START = 1931
YEAR_END = 2026
FIELDNAMES = mx.FIELDNAMES

GRAPHIC_TERMS = (
    "poster",
    "posters",
    "propaganda",
    "advertisement",
    "advertising",
    "campaign",
    "publicity",
    "pamphlet",
    "print culture",
    "graphic",
    "typography",
    "visual communication",
    "cartoon",
    "media",
    "ポスター",
    "広告",
    "商業美術",
    "宣伝美術",
    "図案",
)

TITLE_TERMS = (
    "poster",
    "posters",
    "advertisement",
    "advertising",
    "propaganda",
    "campaign",
    "pamphlet",
    "graphic",
    "typography",
    "ポスター",
    "広告",
)

EXCLUDE_TERMS = (
    "cystitis",
    "prostate",
    "prostaat",
    "androgen",
    "androgeen",
    "ewekan",
    "oxygen therapy",
    "surgical",
    "student handbook",
    "speech on multilingual education",
    "necessary tool for educational transformation",
    "structure models exhibition",
    "daily trust newspaper",
    "theory of culture",
    "nigerbiblios",
)


DSpaceSource = dict[str, Any]

DSPACE_SOURCES: list[DSpaceSource] = [
    {
        "source_id": "SCG-UP",
        "source_name": "University of Pretoria Research Repository",
        "base": "https://repository.up.ac.za",
        "region": "Africa",
        "place": "South Africa",
        "terms": ["poster", "propaganda poster", "graphic design", "advertising"],
        "limit": 4,
    },
    {
        "source_id": "SCG-SUN",
        "source_name": "Stellenbosch University Scholar",
        "base": "https://scholar.sun.ac.za",
        "region": "Africa",
        "place": "South Africa",
        "terms": ["poster", "propaganda poster", "political poster", "cartoon"],
        "limit": 4,
    },
    {
        "source_id": "SCG-WITS",
        "source_name": "Wits University WiredSpace",
        "base": "https://wiredspace.wits.ac.za",
        "region": "Africa",
        "place": "South Africa",
        "terms": ["poster", "resistance posters", "anti-apartheid poster", "graphic design"],
        "limit": 4,
    },
    {
        "source_id": "SCG-AUB",
        "source_name": "American University of Beirut ScholarWorks",
        "base": "https://scholarworks.aub.edu.lb",
        "region": "Middle East and North Africa",
        "place": "Lebanon / Palestine / regional",
        "terms": ["poster", "Palestinian poster", "media solidarity", "graphic design"],
        "limit": 4,
    },
    {
        "source_id": "SCG-NIGERIA",
        "source_name": "National Repository of Nigeria",
        "base": "https://nigeriareposit.nln.gov.ng",
        "region": "Africa",
        "place": "Nigeria",
        "terms": ["poster", "advertising", "Nigeria Magazine", "public campaign"],
        "limit": 3,
    },
]


def clean(value: Any, *, max_chars: int = 900) -> str:
    text = html.unescape(re.sub(r"\s+", " ", str(value or "")).strip())
    return text[:max_chars]


def strip_tags(value: str, *, max_chars: int = 900) -> str:
    value = re.sub(r"(?is)<(script|style).*?</\1>", " ", value or "")
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    return clean(value, max_chars=max_chars)


def fetch_bytes(url: str, *, accept: str = "application/json,text/html,application/xml,*/*") -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(req, timeout=35) as response:
        return response.read()


def fetch_json(url: str) -> Any:
    return json.loads(fetch_bytes(url, accept="application/json").decode("utf-8", errors="replace"))


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8", errors="replace")


def write_raw(name: str, payload: Any) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path.relative_to(ROOT))


def years_from_text(value: str) -> list[int]:
    years: list[int] = []
    for match in re.findall(r"\b(18\d{2}|19\d{2}|20[0-2]\d)\b", value or ""):
        year = int(match)
        if 1800 <= year <= 2026:
            years.append(year)
    return years


def date_bounds(value: str) -> tuple[str, str]:
    years = years_from_text(value)
    if not years:
        return "", ""
    return str(min(years)), str(max(years))


def in_scope(date_text: str) -> bool:
    years = years_from_text(date_text)
    if not years:
        return False
    terminal = max(years)
    return YEAR_START <= terminal <= YEAR_END


def relevant(title: str, description: str, subjects: str = "", query: str = "") -> bool:
    title_l = title.lower()
    blob = " ".join([title, description, subjects]).lower()
    if any(term in blob for term in EXCLUDE_TERMS):
        return False
    if any(term in title_l for term in TITLE_TERMS):
        return True
    return any(term in blob for term in GRAPHIC_TERMS)


def metadata_value(metadata: dict[str, Any], *keys: str, max_chars: int = 1200) -> str:
    values: list[str] = []
    for key in keys:
        for entry in metadata.get(key, []) if isinstance(metadata.get(key), list) else []:
            if isinstance(entry, dict) and entry.get("value"):
                values.append(clean(entry.get("value"), max_chars=max_chars))
    return clean("; ".join(values), max_chars=max_chars)


def existing_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in DATA.glob("capture_batch_*_records.csv"):
        if path == RECORDS_CSV:
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                keys.add((row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", "")))
    return keys


def image_fields(
    code: str,
    basis: str,
    *,
    image_url: str = "",
    viewer: str = "",
    confidence: str = "medium",
    local_copy_permitted: bool = False,
) -> dict[str, str]:
    return mc.image_fields(
        code,
        basis,
        image_url=image_url,
        viewer=viewer or image_url,
        confidence=confidence,
        rights_review_required=True,
        local_copy_permitted=local_copy_permitted,
        note="Source-coverage gap capture keeps images source-hosted unless a record-level open statement is explicit.",
    )


def row_defaults(row: dict[str, str]) -> dict[str, str]:
    code = row.get("image_presence_code", "")
    row["image_expectation"] = "not_expected" if code == "IMG04" else "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["ocr_or_excerpt"] = row.get("source_description") or row.get("source_notes") or row.get("source_subjects", "")
    row["source_description_raw"] = row.get("source_description", "")
    row.setdefault("editorial_summary", row.get("source_description", ""))
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def dspace_search_url(base: str, term: str, size: int = 8) -> str:
    params = {"query": term, "size": str(size)}
    return f"{base.rstrip('/')}/server/api/discover/search/objects?" + urllib.parse.urlencode(params)


def dspace_record_url(base: str, handle: str, uuid: str) -> str:
    if handle:
        return f"{base.rstrip('/')}/handle/{handle}"
    return f"{base.rstrip('/')}/items/{uuid}"


def capture_dspace_source(config: DSpaceSource, seen: set[tuple[str, str]]) -> tuple[list[dict[str, str]], dict[str, str]]:
    rows: list[dict[str, str]] = []
    failures = 0
    for term in config["terms"]:
        url = dspace_search_url(config["base"], term)
        try:
            payload = fetch_json(url)
        except Exception as exc:
            failures += 1
            continue
        raw_path = write_raw(f"{config['source_id'].lower()}_dspace_{re.sub(r'[^a-z0-9]+', '_', term.lower())}.json", payload)
        objects = (
            payload.get("_embedded", {})
            .get("searchResult", {})
            .get("_embedded", {})
            .get("objects", [])
        )
        for obj in objects:
            item = obj.get("_embedded", {}).get("indexableObject", {}) if isinstance(obj, dict) else {}
            if item.get("type") != "item":
                continue
            metadata = item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {}
            title = clean(item.get("name") or metadata_value(metadata, "dc.title", max_chars=400), max_chars=400)
            creator = metadata_value(metadata, "dc.contributor.author", "dc.creator", max_chars=400)
            date_text = metadata_value(metadata, "dc.date.issued", "dc.date.created", "dcterms.date", max_chars=120)
            description = metadata_value(metadata, "dc.description.abstract", "dc.description", max_chars=1600)
            subjects = metadata_value(metadata, "dc.subject", "dcterms.subject", max_chars=900)
            if not title or not in_scope(date_text) or not relevant(title, description, subjects, term):
                continue
            identifier = clean(item.get("uuid") or item.get("handle") or title)
            key = (config["source_name"], identifier)
            if key in seen:
                continue
            seen.add(key)
            start, end = date_bounds(date_text)
            record_url = dspace_record_url(config["base"], clean(item.get("handle")), clean(item.get("uuid")))
            image = image_fields(
                "IMG04",
                "DSpace repository metadata/text record; no item-level image display evidence was captured.",
                viewer=record_url,
            )
            row = {
                "capture_id": "",
                "direction_id": "SCG-DS",
                "direction_name": "source_coverage_gap_dspace_repository_1931_2026",
                "source_id": config["source_id"],
                "source_name": config["source_name"],
                "source_api_url": url,
                "capture_status": "captured",
                "source_identifier": identifier,
                "source_record_url": record_url,
                "source_title": title,
                "source_creator": creator,
                "source_date_text": date_text,
                "date_start": start,
                "date_end": end,
                "source_place_text": config["place"],
                "source_object_type": metadata_value(metadata, "dc.type", "dcterms.type", max_chars=200) or "repository text record / graphic communication context",
                "source_medium": metadata_value(metadata, "dc.type", "dcterms.type", max_chars=200) or "text/context record",
                "source_collection": config["source_name"],
                "source_description": description,
                "source_notes": metadata_value(metadata, "dc.identifier.citation", "dc.publisher", "dc.relation.ispartof", max_chars=900),
                "source_subjects": subjects or term,
                "source_rights_text": "DSpace repository record; image or file rights require item-level review.",
                "rights_uri": "",
                "raw_json_path": raw_path,
                "access_date": ACCESS_DATE,
                **image,
                "editorial_summary": clean(f"{title} is indexed from {config['source_name']}. {description}", max_chars=700),
                "historical_context_note": f"{config['source_name']} adds {config['region']} source evidence for graphic communication, posters, advertising, propaganda, public media, or visual culture research outside dominant museum APIs.",
                "classification_rationale": "Captured from a DSpace REST item search and promoted only when title/metadata/date carry graphic communication evidence.",
                "uncertainty_note": "This is text/context evidence unless a linked visual object and rights-visible image path are verified.",
                "citation_basis": f"{config['source_name']}. {title}. {record_url}. Accessed {ACCESS_DATE}.",
            }
            rows.append(row_defaults(row))
            if len(rows) >= int(config["limit"]):
                return rows, {
                    "source_id": config["source_id"],
                    "source_name": config["source_name"],
                    "region": config["region"],
                    "status": "captured",
                    "captured_records": str(len(rows)),
                    "failure_count": str(failures),
                    "notes": "DSpace REST item search; promoted as text/context evidence.",
                }
        time.sleep(0.2)
    return rows, {
        "source_id": config["source_id"],
        "source_name": config["source_name"],
        "region": config["region"],
        "status": "captured" if rows else "no_records_promoted",
        "captured_records": str(len(rows)),
        "failure_count": str(failures),
        "notes": "DSpace REST item search; no eligible records promoted." if not rows else "DSpace REST item search.",
    }


def omeka_value(item: dict[str, Any], *keys: str, max_chars: int = 1200) -> str:
    values: list[str] = []
    for key in keys:
        raw = item.get(key)
        if isinstance(raw, list):
            for entry in raw:
                if isinstance(entry, dict):
                    value = entry.get("@value") or entry.get("o:label") or entry.get("display_title")
                    if value:
                        values.append(clean(value, max_chars=max_chars))
        elif raw:
            values.append(clean(raw, max_chars=max_chars))
    return clean("; ".join(values), max_chars=max_chars)


def capture_uct_omeka(seen: set[tuple[str, str]]) -> tuple[list[dict[str, str]], dict[str, str]]:
    source_name = "University of Cape Town Digital Collections"
    rows: list[dict[str, str]] = []
    failures = 0
    for term in ["poster", "anti-apartheid poster", "pamphlet", "public campaign"]:
        url = "https://digitalcollections.lib.uct.ac.za/api/items?search=" + urllib.parse.quote(term)
        try:
            payload = fetch_json(url)
        except Exception:
            failures += 1
            continue
        raw_path = write_raw(f"scg_uct_omeka_{re.sub(r'[^a-z0-9]+', '_', term.lower())}.json", payload)
        if not isinstance(payload, list):
            continue
        for item in payload[:10]:
            title = clean(item.get("o:title") or omeka_value(item, "dcterms:title", max_chars=400), max_chars=400)
            date_text = omeka_value(item, "dcterms:date", "dcterms:created", max_chars=120)
            description = omeka_value(item, "dcterms:description", "bibo:abstract", max_chars=1600)
            subjects = omeka_value(item, "dcterms:subject", "dcterms:type", max_chars=900)
            if not title or not in_scope(date_text) or not relevant(title, description, subjects, term):
                continue
            identifier = str(item.get("o:id") or item.get("@id") or title)
            key = (source_name, identifier)
            if key in seen:
                continue
            seen.add(key)
            start, end = date_bounds(date_text)
            record_url = clean(item.get("o:site_url") or item.get("@id") or url)
            thumbnails = item.get("thumbnail_display_urls") if isinstance(item.get("thumbnail_display_urls"), dict) else {}
            image_url = clean(thumbnails.get("large") or thumbnails.get("medium") or "")
            image = image_fields(
                "IMG02" if image_url else "IMG00",
                "Omeka item exposes a source-hosted thumbnail; local copy is not assumed.",
                image_url=image_url,
                viewer=record_url,
            )
            row = {
                "capture_id": "",
                "direction_id": "SCG-OMEKA",
                "direction_name": "source_coverage_gap_omeka_image_context_1931_2026",
                "source_id": "SCG-UCT",
                "source_name": source_name,
                "source_api_url": url,
                "capture_status": "captured",
                "source_identifier": identifier,
                "source_record_url": record_url,
                "source_title": title,
                "source_creator": omeka_value(item, "dcterms:creator", "dcterms:contributor", max_chars=400),
                "source_date_text": date_text,
                "date_start": start,
                "date_end": end,
                "source_place_text": "South Africa",
                "source_object_type": omeka_value(item, "dcterms:type", max_chars=200) or "Omeka item",
                "source_medium": omeka_value(item, "dcterms:format", "dcterms:medium", max_chars=200) or "source-hosted visual/context item",
                "source_collection": source_name,
                "source_description": description,
                "source_notes": omeka_value(item, "dcterms:publisher", "dcterms:relation", max_chars=900),
                "source_subjects": subjects or term,
                "source_rights_text": omeka_value(item, "dcterms:rights", "dcterms:license", max_chars=700) or "Omeka item; rights require record-level review.",
                "rights_uri": "",
                "raw_json_path": raw_path,
                "access_date": ACCESS_DATE,
                **image,
                "editorial_summary": clean(f"{title} is indexed from University of Cape Town Digital Collections. {description}", max_chars=700),
                "historical_context_note": "UCT Digital Collections adds southern African community/university archive evidence with source-hosted visual material where item thumbnails exist.",
                "classification_rationale": "Captured from an Omeka item endpoint and filtered by date plus poster/pamphlet/campaign evidence.",
                "uncertainty_note": "Images remain source-hosted unless an explicit open licence is verified at item level.",
                "citation_basis": f"University of Cape Town Digital Collections. {title}. {record_url}. Accessed {ACCESS_DATE}.",
            }
            rows.append(row_defaults(row))
            if len(rows) >= 6:
                return rows, {
                    "source_id": "SCG-UCT",
                    "source_name": source_name,
                    "region": "Africa",
                    "status": "captured",
                    "captured_records": str(len(rows)),
                    "failure_count": str(failures),
                    "notes": "Omeka item capture with source-hosted thumbnails.",
                }
        time.sleep(0.2)
    return rows, {
        "source_id": "SCG-UCT",
        "source_name": source_name,
        "region": "Africa",
        "status": "captured" if rows else "no_records_promoted",
        "captured_records": str(len(rows)),
        "failure_count": str(failures),
        "notes": "Omeka item capture.",
    }


def dc_text(record: Any, local_name: str) -> str:
    vals = []
    for elem in record.iter():
        if elem.tag.endswith("}" + local_name) and elem.text:
            vals.append(clean(elem.text, max_chars=260))
    return clean("; ".join(vals), max_chars=900)


def capture_ndl_sru(seen: set[tuple[str, str]]) -> tuple[list[dict[str, str]], dict[str, str]]:
    import xml.etree.ElementTree as ET

    source_name = "NDL Search"
    rows: list[dict[str, str]] = []
    failures = 0
    queries = [
        'title any "ポスター"',
        'title any "広告"',
        'title any "商業美術"',
        'title any "宣伝美術"',
        'title any "図案"',
    ]
    for query in queries:
        url = "https://iss.ndl.go.jp/api/sru?operation=searchRetrieve&recordPacking=xml&maximumRecords=12&query=" + urllib.parse.quote(query)
        try:
            text = fetch_text(url)
        except Exception:
            failures += 1
            continue
        raw_path = write_raw(f"scg_ndl_sru_{re.sub(r'[^a-z0-9]+', '_', query.lower())}.xml", text)
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            failures += 1
            continue
        for record in root.iter():
            if not record.tag.endswith("}recordData"):
                continue
            title = dc_text(record, "title")
            creator = dc_text(record, "creator")
            description = dc_text(record, "description")
            date_text = dc_text(record, "date") or dc_text(record, "issued")
            subjects = dc_text(record, "subject")
            if not title or not in_scope(date_text) or not relevant(title, description, subjects, query):
                continue
            identifier = dc_text(record, "identifier") or f"NDL:{title}:{date_text}"
            key = (source_name, identifier)
            if key in seen:
                continue
            seen.add(key)
            start, end = date_bounds(date_text)
            record_url = identifier if identifier.startswith("http") else "https://iss.ndl.go.jp/books?ar=4e1f&search_mode=advanced&title=" + urllib.parse.quote(title)
            image = image_fields("IMG04", "NDL SRU bibliographic metadata; no item-level image path was promoted.", viewer=record_url)
            row = {
                "capture_id": "",
                "direction_id": "SCG-NDL",
                "direction_name": "source_coverage_gap_ndl_sru_1931_2026",
                "source_id": "SCG-NDL",
                "source_name": source_name,
                "source_api_url": url,
                "capture_status": "captured",
                "source_identifier": identifier,
                "source_record_url": record_url,
                "source_title": title,
                "source_creator": creator,
                "source_date_text": date_text,
                "date_start": start,
                "date_end": end,
                "source_place_text": "Japan",
                "source_object_type": "bibliographic design/print record",
                "source_medium": dc_text(record, "type") or "bibliographic metadata",
                "source_collection": "NDL Search",
                "source_description": description,
                "source_notes": dc_text(record, "publisher"),
                "source_subjects": subjects or query,
                "source_rights_text": "Bibliographic metadata only; image not promoted.",
                "rights_uri": "",
                "raw_json_path": raw_path,
                "access_date": ACCESS_DATE,
                **image,
                "editorial_summary": clean(f"{title} is indexed from NDL Search as Japanese bibliographic evidence for poster, advertising, commercial art, and print design records. {description}", max_chars=700),
                "historical_context_note": "NDL Search adds Japanese bibliographic coverage so East Asian graphic design history is not represented only through Western museum objects.",
                "classification_rationale": "Captured from NDL SRU Dublin Core metadata and filtered by date plus poster/advertising/commercial-art title queries.",
                "uncertainty_note": "No image is displayed until a linked digital object or rights-visible viewer is verified.",
                "citation_basis": f"NDL Search. {title}. {record_url}. Accessed {ACCESS_DATE}.",
            }
            rows.append(row_defaults(row))
            if len(rows) >= 8:
                return rows, {
                    "source_id": "SCG-NDL",
                    "source_name": source_name,
                    "region": "East Asia",
                    "status": "captured",
                    "captured_records": str(len(rows)),
                    "failure_count": str(failures),
                    "notes": "NDL SRU bibliographic metadata; image not promoted.",
                }
    return rows, {
        "source_id": "SCG-NDL",
        "source_name": source_name,
        "region": "East Asia",
        "status": "captured" if rows else "no_records_promoted",
        "captured_records": str(len(rows)),
        "failure_count": str(failures),
        "notes": "NDL SRU bibliographic metadata.",
    }


def assign_ids(rows: list[dict[str, str]]) -> None:
    for idx, row in enumerate(rows, start=1):
        row["capture_id"] = f"SCG1931R{idx:04d}"


def write_outputs(rows: list[dict[str, str]], summaries: list[dict[str, str]]) -> None:
    for row in rows:
        for field in FIELDNAMES:
            row.setdefault(field, "")
    with RECORDS_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDNAMES} for row in rows)

    image_by_source: dict[str, Counter[str]] = {}
    for row in rows:
        image_by_source.setdefault(row["source_name"], Counter())[row["image_presence_code"]] += 1
    summary_fields = ["source_id", "source_name", "region", "status", "captured_records", "failure_count", "image_states", "notes"]
    for summary in summaries:
        images = image_by_source.get(summary["source_name"], Counter())
        summary["image_states"] = "; ".join(f"{k}:{v}" for k, v in sorted(images.items()))
        for field in summary_fields:
            summary.setdefault(field, "")
    with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in summary_fields} for row in summaries)

    image_counts = Counter(row["image_presence_code"] for row in rows)
    source_counts = Counter(row["source_name"] for row in rows)
    region_counts = Counter(row["source_place_text"] for row in rows)
    period_counts = Counter("pre_1930" if int(row["date_end"] or row["date_start"] or 0) <= 1930 else "1931_1970" if int(row["date_end"] or row["date_start"] or 0) <= 1970 else "1971_2000" if int(row["date_end"] or row["date_start"] or 0) <= 2000 else "2001_2026" for row in rows)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Source Coverage Gap Capture 1931-2026",
        "",
        "This pass repairs source breadth for underrepresented regions with item-level DSpace, Omeka, and SRU records. It keeps text/context records as text evidence and does not convert source-hosted thumbnails into local image claims.",
        "",
        f"- Captured records: {len(rows)}",
        f"- Distinct sources captured: {len(source_counts)}",
        f"- Access date: {ACCESS_DATE}",
        "",
        "## Image States",
        "",
    ]
    for key, count in sorted(image_counts.items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Periods", ""])
    for key, count in sorted(period_counts.items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Sources", ""])
    for key, count in source_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Places", ""])
    for key, count in region_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Method Note", ""])
    lines.append("DSpace records are mostly text/context evidence and should normally render as text sheets, appendix evidence, or grouped supporting leaves. UCT Omeka records may include IMG02 thumbnails, but the images remain source-hosted. NDL SRU records are bibliographic until a rights-visible digital-object pathway is verified.")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    seen = existing_keys()
    rows: list[dict[str, str]] = []
    summaries: list[dict[str, str]] = []
    for config in DSPACE_SOURCES:
        source_rows, summary = capture_dspace_source(config, seen)
        rows.extend(source_rows)
        summaries.append(summary)
        time.sleep(0.4)
    source_rows, summary = capture_uct_omeka(seen)
    rows.extend(source_rows)
    summaries.append(summary)
    source_rows, summary = capture_ndl_sru(seen)
    rows.extend(source_rows)
    summaries.append(summary)
    assign_ids(rows)
    write_outputs(rows, summaries)
    print(f"captured={len(rows)} sources={len(set(row['source_name'] for row in rows))}")
    print("image_states=" + json.dumps(dict(Counter(row["image_presence_code"] for row in rows)), sort_keys=True))
    print("sources=" + json.dumps(dict(Counter(row["source_name"] for row in rows)), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
