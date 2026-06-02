#!/usr/bin/env python3
"""Source-breadth capture for underrepresented 1970-2026 records.

This pass is deliberately breadth-first: it adds a small number of item-level
records from sources that are not already dominant in the public payload. It
keeps failed or source-level-only probes in the summary instead of turning them
into thin public sheets.
"""

from __future__ import annotations

import csv
import html
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

import run_midcentury_capture_1930_1970 as mc
import run_midcentury_expansion_capture_1931_1970 as mx
from contemporary_noise_filter import evaluate_record


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_source_breadth_1970_2026_raw"
RECORDS_CSV = DATA / "capture_batch_source_breadth_1970_2026_records.csv"
SUMMARY_CSV = DATA / "capture_batch_source_breadth_1970_2026_source_summary.csv"
REPORT = ROOT / "docs" / "capture" / "SOURCE_BREADTH_CAPTURE_1970_2026.md"

ACCESS_DATE = "2026-06-01"
USER_AGENT = "ModernGDHistory/0.1 source-breadth-capture"
FIELDNAMES = mx.FIELDNAMES

GRAPHIC_TERMS = (
    "poster",
    "posters",
    "afiche",
    "plakat",
    "plakát",
    "advert",
    "advertisement",
    "advertising",
    "publicidad",
    "publicity",
    "revista",
    "magazine",
    "pamphlet",
    "flyer",
    "bookmark",
    "ephemera",
    "typography",
    "graphic design",
    "diseño",
    "visual communication",
    "print culture",
    "ポスター",
    "広告",
)


def clean(value: Any, *, max_chars: int = 900) -> str:
    text = html.unescape(re.sub(r"\s+", " ", str(value or "")).strip())
    return text[:max_chars]


def apply_noise_filter(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], Counter[str]]:
    decisions: Counter[str] = Counter()
    kept: list[dict[str, str]] = []
    for row in rows:
        decision = evaluate_record(row)
        decisions[decision.decision] += 1
        row["noise_filter_decision"] = decision.decision
        row["noise_filter_reason"] = decision.reason
        if decision.decision in {"include_candidate", "downgrade_candidate"}:
            kept.append(row)
    return kept, decisions


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
    years = []
    for match in re.findall(r"\b(18\d{2}|19\d{2}|20[0-2]\d)\b", value or ""):
        year = int(match)
        if 1800 <= year <= 2026:
            years.append(year)
    return years


def date_bounds(text: str) -> tuple[str, str]:
    years = years_from_text(text)
    if not years:
        return "", ""
    return str(min(years)), str(max(years))


def terminal_year(text: str) -> int | None:
    years = years_from_text(text)
    return max(years) if years else None


def in_scope(text: str) -> bool:
    year = terminal_year(text)
    return year is not None and 1970 <= year <= 2026


def relevant(*parts: str) -> bool:
    blob = " ".join(str(part or "") for part in parts).lower()
    return any(term in blob for term in GRAPHIC_TERMS)


def existing_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in DATA.glob("capture_batch_*_records.csv"):
        if path == RECORDS_CSV or not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                keys.add((row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", "")))
    return keys


def image_fields(code: str, basis: str, image_url: str = "", viewer: str = "", *, open_ok: bool = False) -> dict[str, str]:
    return mc.image_fields(
        code,
        basis,
        image_url=image_url,
        viewer=viewer or image_url,
        confidence="high" if image_url else "medium",
        rights_review_required=not open_ok,
        local_copy_permitted=False,
        note="Source-breadth capture keeps images source-hosted unless a record-level open statement is explicit.",
    )


def row_defaults(row: dict[str, str]) -> dict[str, str]:
    row["image_expectation"] = "not_expected" if row.get("image_presence_code") == "IMG04" else "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["ocr_or_excerpt"] = row.get("source_description") or row.get("source_notes") or row.get("source_subjects", "")
    row["source_description_raw"] = row.get("source_description", "")
    row.setdefault("editorial_summary", row.get("source_description", ""))
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def field_map(item: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for field in item.get("fields", []):
        label = clean(field.get("label") or field.get("key")).lower()
        key = clean(field.get("key")).lower()
        value = clean(field.get("value"), max_chars=2200)
        if label:
            out[label] = value
        if key:
            out[key] = value
    return out


def contentdm_record_url(collection: str, item_id: str) -> str:
    return f"https://kura.aucklandlibraries.govt.nz/digital/collection/{collection}/id/{item_id}"


def generic_contentdm_record_url(base: str, collection: str, item_id: str) -> str:
    return f"{base.rstrip('/')}/collection/{collection}/id/{item_id}"


def capture_contentdm_source(
    *,
    source_id: str,
    source_name: str,
    base: str,
    region: str,
    terms: list[tuple[str, str, int]],
    seen: set[tuple[str, str]],
    max_rows: int = 8,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    rows: list[dict[str, str]] = []
    failures = 0
    for collection, query, max_keep in terms:
        if collection:
            url = f"{base.rstrip('/')}/api/search/collection/{collection}/searchterm/{urllib.parse.quote(query)}/field/all/maxRecords/10"
        else:
            url = f"{base.rstrip('/')}/api/search/searchterm/{urllib.parse.quote(query)}/field/all/maxRecords/10"
        try:
            payload = fetch_json(url)
        except Exception:
            failures += 1
            continue
        write_raw(f"{source_id.lower()}_contentdm_{collection or 'all'}_{re.sub(r'[^a-z0-9]+', '_', query.lower())}.json", payload)
        kept_for_query = 0
        for hit in payload.get("items", [])[:10]:
            collection_alias = clean(hit.get("collectionAlias"))
            item_id = clean(hit.get("itemId"))
            if not collection_alias or not item_id:
                continue
            item_url = f"{base.rstrip('/')}/api/singleitem/collection/{collection_alias}/id/{item_id}"
            try:
                item = fetch_json(item_url)
            except Exception:
                failures += 1
                continue
            raw_path = write_raw(f"{source_id.lower()}_{collection_alias}_{item_id}.json", item)
            fm = field_map(item)
            title = fm.get("title") or clean(hit.get("title"))
            desc = fm.get("description") or item.get("text", "")
            subjects = fm.get("subjects") or fm.get("subject") or fm.get("keywords")
            date_text = fm.get("date") or fm.get("date created") or fm.get("date of image") or fm.get("decade") or fm.get("covera")
            if not title or not in_scope(date_text) or not relevant(title, desc, subjects):
                continue
            identifier = fm.get("identifier") or fm.get("record id") or fm.get("identi") or f"{collection_alias}:{item_id}"
            key = (source_name, identifier)
            if key in seen:
                continue
            seen.add(key)
            start, end = date_bounds(date_text)
            rights_text = fm.get("rights") or fm.get("usage rights") or fm.get("rights status")
            rights_low = rights_text.lower()
            image_url = clean(item.get("imageUri") or "")
            record_url = generic_contentdm_record_url(base, collection_alias, item_id)
            item_type = fm.get("format") or fm.get("type") or clean(item.get("contentType"))
            open_ok = "no known copyright restrictions" in rights_low or "creative commons" in rights_low or "cc by" in rights_low or "public domain" in rights_low
            if image_url and open_ok:
                image = image_fields("IMG03", rights_text or "CONTENTdm item reports open display terms.", image_url, record_url, open_ok=True)
            elif image_url:
                image = image_fields("IMG02", rights_text or "CONTENTdm item image is source-hosted; rights require record-level review.", image_url, record_url)
            else:
                image = image_fields("IMG04", rights_text or "CONTENTdm metadata record; no public image promoted.", viewer=record_url)
            rows.append(
                row_defaults(
                    {
                        "capture_id": "",
                        "direction_id": "SBC-CDM",
                        "direction_name": "source_breadth_contentdm_local_university_1970_2026",
                        "source_id": source_id,
                        "source_name": source_name,
                        "source_api_url": item_url,
                        "capture_status": "captured",
                        "source_identifier": identifier,
                        "source_record_url": record_url,
                        "source_title": title,
                        "source_creator": fm.get("creator") or fm.get("photographer") or fm.get("contributor"),
                        "source_date_text": date_text,
                        "date_start": start,
                        "date_end": end,
                        "source_place_text": region,
                        "source_object_type": item_type or "CONTENTdm item",
                        "source_medium": item_type or "poster / visual record",
                        "source_collection": fm.get("collection") or fm.get("collection name") or fm.get("source") or collection_alias,
                        "source_description": desc,
                        "source_notes": fm.get("publisher") or fm.get("relation") or fm.get("is part of"),
                        "source_subjects": subjects,
                        "source_rights_text": rights_text,
                        "rights_uri": "",
                        "raw_json_path": raw_path,
                        "access_date": ACCESS_DATE,
                        **image,
                        "editorial_summary": clean(f"{title} is indexed from {source_name}. {desc}", max_chars=700),
                        "historical_context_note": f"{source_name} broadens local and university-held visual communication evidence beyond national museum APIs.",
                        "classification_rationale": "Captured from a CONTENTdm item endpoint and filtered by date plus poster/advertising/graphic terms.",
                        "uncertainty_note": "Images remain source-hosted. Rights language is displayed as evidence, not as a transfer of ownership.",
                        "citation_basis": f"{source_name}. {title}. {record_url}. Accessed {ACCESS_DATE}.",
                    }
                )
            )
            kept_for_query += 1
            if len(rows) >= max_rows or kept_for_query >= max_keep:
                break
        if len(rows) >= max_rows:
            break
    return rows, {"source_name": source_name, "status": "captured" if rows else "no_records_promoted", "captured_records": str(len(rows)), "failure_count": str(failures)}


def capture_auckland(seen: set[tuple[str, str]]) -> tuple[list[dict[str, str]], dict[str, str]]:
    rows: list[dict[str, str]] = []
    failures = 0
    terms = [
        ("photos", "poster", 6),
        ("photos", "Maori poster", 4),
        ("photos", "Pacific poster", 4),
        ("photos", "graphic design", 4),
        ("ephemera", "Maori poster", 3),
        ("ephemera", "poster", 3),
    ]
    text_only_count = 0
    for term in terms:
        collection, query, max_keep = term
        url = (
            f"https://kura.aucklandlibraries.govt.nz/digital/api/search/collection/{collection}/searchterm/"
            + urllib.parse.quote(query)
            + "/field/all/maxRecords/10"
        )
        try:
            payload = fetch_json(url)
        except Exception:
            failures += 1
            continue
        write_raw(f"auckland_search_{collection}_{re.sub(r'[^a-z0-9]+', '_', query.lower())}.json", payload)
        kept_for_query = 0
        for hit in payload.get("items", [])[:8]:
            collection = clean(hit.get("collectionAlias"))
            item_id = clean(hit.get("itemId"))
            if not collection or not item_id:
                continue
            item_url = f"https://kura.aucklandlibraries.govt.nz/digital/api/singleitem/collection/{collection}/id/{item_id}"
            try:
                item = fetch_json(item_url)
            except Exception:
                failures += 1
                continue
            raw_path = write_raw(f"auckland_{collection}_{item_id}.json", item)
            fm = field_map(item)
            title = fm.get("title") or clean(hit.get("title"))
            desc = fm.get("description") or item.get("text", "")
            subjects = fm.get("subjects") or fm.get("keywords")
            date_text = fm.get("date of image") or fm.get("date") or fm.get("decade") or fm.get("covera")
            if not title or not in_scope(date_text) or not relevant(title, desc, subjects):
                continue
            identifier = fm.get("record id") or fm.get("identi") or f"{collection}:{item_id}"
            key = ("Auckland Libraries Heritage Collections / CONTENTdm", identifier)
            if key in seen:
                continue
            seen.add(key)
            start, end = date_bounds(date_text)
            rights_text = fm.get("usage rights") or fm.get("rights")
            image_url = clean(item.get("imageUri") or "")
            record_url = contentdm_record_url(collection, item_id)
            item_type = fm.get("type") or clean(item.get("contentType"))
            rights_low = rights_text.lower()
            open_ok = "no known copyright restrictions" in rights_low or "creative commons" in rights_low or "cc by" in rights_low
            if image_url and open_ok:
                image = image_fields("IMG03", rights_text, image_url, record_url, open_ok=True)
            elif image_url and item_type.lower() != "text only":
                image = image_fields("IMG02", rights_text or "CONTENTdm item image is source-hosted; rights require record-level review.", image_url, record_url)
            else:
                if text_only_count >= 3:
                    continue
                text_only_count += 1
                image = image_fields("IMG04", rights_text or "CONTENTdm text/folder record; no public image promoted.", viewer=record_url)
            rows.append(
                row_defaults(
                    {
                        "capture_id": "",
                        "direction_id": "SBC-AKL",
                        "direction_name": "source_breadth_auckland_contentdm_1970_2026",
                        "source_id": "ESC095",
                        "source_name": "Auckland Libraries Heritage Collections / CONTENTdm",
                        "source_api_url": item_url,
                        "capture_status": "captured",
                        "source_identifier": identifier,
                        "source_record_url": record_url,
                        "source_title": title,
                        "source_creator": fm.get("creator") or fm.get("photographer"),
                        "source_date_text": date_text,
                        "date_start": start,
                        "date_end": end,
                        "source_place_text": "Aotearoa New Zealand",
                        "source_object_type": item_type or "CONTENTdm item",
                        "source_medium": fm.get("physical description") or item_type or "ephemera / image record",
                        "source_collection": fm.get("collection name") or fm.get("source") or collection,
                        "source_description": desc,
                        "source_notes": fm.get("access") or fm.get("published in") or fm.get("page link"),
                        "source_subjects": subjects,
                        "source_rights_text": rights_text,
                        "rights_uri": "",
                        "raw_json_path": raw_path,
                        "access_date": ACCESS_DATE,
                        **image,
                        "editorial_summary": clean(f"{title} is indexed from Auckland Libraries Heritage Collections. {desc}", max_chars=700),
                        "historical_context_note": "Auckland CONTENTdm adds municipal and Pacific-region evidence for ephemera, posters, pamphlets, Māori public culture, and local graphic circulation.",
                        "classification_rationale": "Captured from CONTENTdm item metadata and filtered by date plus poster/pamphlet/ephemera terms. Folder placement is a filter, not ownership.",
                        "uncertainty_note": "Text-only folder records may describe multiple pieces; they should render as grouped reading/context leaves rather than repeated thin sheets.",
                        "citation_basis": f"Auckland Libraries Heritage Collections. {title}. {record_url}. Accessed {ACCESS_DATE}.",
                    }
                )
            )
            kept_for_query += 1
            if len(rows) >= 10 or kept_for_query >= max_keep:
                break
        if len(rows) >= 10:
                return rows, {"source_name": "Auckland Libraries Heritage Collections / CONTENTdm", "status": "captured", "captured_records": str(len(rows)), "failure_count": str(failures)}
    return rows, {"source_name": "Auckland Libraries Heritage Collections / CONTENTdm", "status": "captured" if rows else "no_records_promoted", "captured_records": str(len(rows)), "failure_count": str(failures)}


def wp_featured_image(post: dict[str, Any]) -> str:
    embedded = post.get("_embedded") if isinstance(post.get("_embedded"), dict) else {}
    media = embedded.get("wp:featuredmedia") if isinstance(embedded.get("wp:featuredmedia"), list) else []
    for item in media:
        if isinstance(item, dict):
            sizes = item.get("media_details", {}).get("sizes", {}) if isinstance(item.get("media_details"), dict) else {}
            for key in ("large", "medium_large", "full"):
                src = (sizes.get(key) or {}).get("source_url") if isinstance(sizes.get(key), dict) else ""
                if src:
                    return clean(src)
            if item.get("source_url"):
                return clean(item.get("source_url"))
    return ""


def capture_wordpress_source(source_id: str, source_name: str, base: str, terms: list[str], region: str, seen: set[tuple[str, str]]) -> tuple[list[dict[str, str]], dict[str, str]]:
    rows: list[dict[str, str]] = []
    failures = 0
    for term in terms:
        url = f"{base.rstrip('/')}/wp-json/wp/v2/posts?search={urllib.parse.quote(term)}&per_page=5&_embed=1"
        try:
            payload = fetch_json(url)
        except Exception:
            failures += 1
            continue
        raw_path = write_raw(f"{source_id.lower()}_wp_{re.sub(r'[^a-z0-9]+', '_', term.lower())}.json", payload)
        if not isinstance(payload, list):
            continue
        for post in payload:
            title = strip_tags((post.get("title") or {}).get("rendered", ""))
            content = strip_tags((post.get("excerpt") or {}).get("rendered") or (post.get("content") or {}).get("rendered", ""), max_chars=1600)
            date_text = clean(post.get("date", "")[:10])
            if not title or not in_scope(date_text) or not relevant(title, content) or len(content) < 80:
                continue
            identifier = str(post.get("id") or post.get("link") or title)
            key = (source_name, identifier)
            if key in seen:
                continue
            seen.add(key)
            image_url = wp_featured_image(post)
            rights_basis = "WordPress public post metadata; image remains source-hosted and requires record-level review."
            image = image_fields("IMG02" if image_url else "IMG04", rights_basis, image_url, clean(post.get("link")))
            start, end = date_bounds(date_text)
            rows.append(
                row_defaults(
                    {
                        "capture_id": "",
                        "direction_id": "SBC-WP",
                        "direction_name": "source_breadth_wordpress_context_1970_2026",
                        "source_id": source_id,
                        "source_name": source_name,
                        "source_api_url": url,
                        "capture_status": "captured",
                        "source_identifier": identifier,
                        "source_record_url": clean(post.get("link")),
                        "source_title": title,
                        "source_creator": "",
                        "source_date_text": date_text,
                        "date_start": start,
                        "date_end": end,
                        "source_place_text": region,
                        "source_object_type": "source context / archive publication note",
                        "source_medium": "HTML article / collection context",
                        "source_collection": source_name,
                        "source_description": content,
                        "source_notes": "Promoted sparingly as a source-context reading record, not as a substitute for item-level collection data.",
                        "source_subjects": term,
                        "source_rights_text": rights_basis,
                        "rights_uri": "",
                        "raw_json_path": raw_path,
                        "access_date": ACCESS_DATE,
                        **image,
                        "editorial_summary": clean(f"{title} is a source-context record from {source_name}. {content}", max_chars=700),
                        "historical_context_note": f"{source_name} is retained as a non-museum archive voice for Latin American print, magazine, political, or design-history context.",
                        "classification_rationale": "Captured from WordPress REST metadata and promoted only when the public post itself discusses magazines, posters, design, advertising, or political print culture.",
                        "uncertainty_note": "This is not treated as an object record; it should support reading/context surfaces and source-return links.",
                        "citation_basis": f"{source_name}. {title}. {post.get('link')}. Accessed {ACCESS_DATE}.",
                    }
                )
            )
            if len(rows) >= 3:
                return rows, {"source_name": source_name, "status": "captured", "captured_records": str(len(rows)), "failure_count": str(failures)}
    return rows, {"source_name": source_name, "status": "captured" if rows else "no_records_promoted", "captured_records": str(len(rows)), "failure_count": str(failures)}


def dc_text(node: ET.Element, local_name: str) -> str:
    vals = []
    for elem in node.iter():
        if elem.tag.endswith("}" + local_name) and elem.text:
            vals.append(clean(elem.text, max_chars=260))
    return clean("; ".join(vals), max_chars=900)


def capture_ndl(seen: set[tuple[str, str]]) -> tuple[list[dict[str, str]], dict[str, str]]:
    rows: list[dict[str, str]] = []
    failures = 0
    queries = [
        'dpid=iss-ndl-opac and title=poster',
        'dpid=iss-ndl-opac and title any "ポスター"',
        'dpid=iss-ndl-opac and title any "広告"',
    ]
    for query in queries:
        url = "https://iss.ndl.go.jp/api/sru?operation=searchRetrieve&recordPacking=xml&maximumRecords=8&query=" + urllib.parse.quote(query)
        try:
            text = fetch_text(url)
        except Exception:
            failures += 1
            continue
        raw_path = write_raw(f"ndl_sru_{re.sub(r'[^a-z0-9]+', '_', query.lower())}.xml", text)
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
            date_text = dc_text(record, "date") or dc_text(record, "issued") or clean(" ".join(re.findall(r"\b(19\d{2}|20[0-2]\d)\b", text)[:1]))
            if not title or not in_scope(date_text) or not relevant(title, description):
                continue
            identifier = dc_text(record, "identifier") or f"NDL:{title}:{date_text}"
            key = ("NDL Search / National Diet Library", identifier)
            if key in seen:
                continue
            seen.add(key)
            start, end = date_bounds(date_text)
            record_url = ""
            if identifier.startswith("http"):
                record_url = identifier
            else:
                record_url = "https://iss.ndl.go.jp/books?ar=4e1f&search_mode=advanced&title=" + urllib.parse.quote(title)
            image = image_fields("IMG04", "NDL SRU bibliographic metadata; no item-level image was promoted.", viewer=record_url)
            rows.append(
                row_defaults(
                    {
                        "capture_id": "",
                        "direction_id": "SBC-NDL",
                        "direction_name": "source_breadth_ndl_sru_bibliographic_1970_2026",
                        "source_id": "SEM063",
                        "source_name": "NDL Search / National Diet Library",
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
                        "source_subjects": query,
                        "source_rights_text": "Bibliographic metadata only; image not promoted.",
                        "rights_uri": "",
                        "raw_json_path": raw_path,
                        "access_date": ACCESS_DATE,
                        **image,
                        "editorial_summary": clean(f"{title} is indexed from NDL Search as Japanese bibliographic evidence for poster, advertising, and design publication records. {description}", max_chars=700),
                        "historical_context_note": "NDL Search adds Japanese bibliographic coverage so East Asian graphic design history is not represented only through Western museum objects.",
                        "classification_rationale": "Captured from NDL SRU Dublin Core metadata and filtered by date plus poster/advertising title queries.",
                        "uncertainty_note": "No image is displayed until a linked digital object or rights-visible viewer is verified.",
                        "citation_basis": f"NDL Search / National Diet Library. {title}. {record_url}. Accessed {ACCESS_DATE}.",
                    }
                )
            )
            if len(rows) >= 6:
                return rows, {"source_name": "NDL Search / National Diet Library", "status": "captured", "captured_records": str(len(rows)), "failure_count": str(failures)}
    return rows, {"source_name": "NDL Search / National Diet Library", "status": "captured" if rows else "no_records_promoted", "captured_records": str(len(rows)), "failure_count": str(failures)}


def assign_ids(rows: list[dict[str, str]]) -> None:
    for idx, row in enumerate(rows, start=1):
        row["capture_id"] = f"SBC1970R{idx:04d}"


def write_outputs(rows: list[dict[str, str]], summaries: list[dict[str, str]]) -> None:
    output_rows: list[dict[str, str]] = []
    for row in rows:
        clean_row = dict(row)
        noise_decision = clean_row.pop("noise_filter_decision", "")
        noise_reason = clean_row.pop("noise_filter_reason", "")
        if noise_decision or noise_reason:
            note = clean_row.get("uncertainty_note", "")
            clean_row["uncertainty_note"] = clean(
                " | ".join(part for part in [note, f"Noise filter: {noise_decision} {noise_reason}".strip()] if part),
                max_chars=900,
            )
        output_rows.append({field: clean_row.get(field, "") for field in FIELDNAMES})

    with RECORDS_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    summary_fields = ["source_name", "status", "captured_records", "failure_count", "image_states", "notes"]
    image_by_source: dict[str, Counter[str]] = {}
    for row in output_rows:
        image_by_source.setdefault(row["source_name"], Counter())[row["image_presence_code"]] += 1
    for summary in summaries:
        images = image_by_source.get(summary["source_name"], Counter())
        summary["image_states"] = "; ".join(f"{k}:{v}" for k, v in sorted(images.items()))
        summary.setdefault("notes", "source-breadth capture")
    with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(summaries)

    image_counts = Counter(row["image_presence_code"] for row in output_rows)
    source_counts = Counter(row["source_name"] for row in output_rows)
    region_counts = Counter(row["source_place_text"] for row in output_rows)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Source Breadth Capture 1970-2026",
        "",
        "This pass increases distinct source coverage with small, item-level or source-context batches from municipal, national-library, community, and university sources. It is intentionally conservative: failed probes and generic landing-page evidence remain in the summary instead of becoming public sheets.",
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
    lines.extend(["", "## Sources", ""])
    for key, count in source_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Regions", ""])
    for key, count in region_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Method Note", ""])
    lines.append("Auckland CONTENTdm records can carry images and rights fields. NDL SRU records are bibliographic and therefore IMG04 until a rights-visible digital object is verified. WordPress archive posts are promoted only as limited source-context records, not as object substitutes.")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    seen = existing_keys()
    all_rows: list[dict[str, str]] = []
    summaries: list[dict[str, str]] = []
    extra_contentdm_sources = [
        {
            "source_id": "ESC-CDM-UH",
            "source_name": "University of Houston Digital Library / CONTENTdm",
            "base": "https://digital.lib.uh.edu/digital",
            "region": "United States / Gulf Coast / Latinx",
            "terms": [("", "poster", 3), ("", "advertising", 2), ("", "brochure", 2)],
            "max_rows": 5,
        },
        {
            "source_id": "ESC-CDM-SMU",
            "source_name": "SMU Libraries Digital Collections / CONTENTdm",
            "base": "https://digitalcollections.smu.edu/digital",
            "region": "United States / Texas / Latin America",
            "terms": [("", "poster", 3), ("", "Mexico poster", 2), ("", "advertising", 2)],
            "max_rows": 5,
        },
        {
            "source_id": "ESC-CDM-IOWA",
            "source_name": "Iowa Digital Library / CONTENTdm",
            "base": "https://digital.lib.uiowa.edu/digital",
            "region": "United States / Midwest",
            "terms": [("", "poster", 3), ("", "advertising", 2), ("", "flyer", 2)],
            "max_rows": 5,
        },
        {
            "source_id": "ESC-CDM-UCSB",
            "source_name": "UCSB Library Digital Collections / CONTENTdm",
            "base": "https://digital.library.ucsb.edu/digital",
            "region": "United States / California / transnational",
            "terms": [("", "poster", 3), ("", "advertising", 2), ("", "pamphlet", 2)],
            "max_rows": 5,
        },
        {
            "source_id": "ESC-CDM-MIAMI",
            "source_name": "University of Miami Libraries Digital Collections / CONTENTdm",
            "base": "https://digitalcollections.library.miami.edu/digital",
            "region": "United States / Caribbean / Latin America",
            "terms": [("", "poster", 3), ("", "Cuba poster", 2), ("", "advertising", 2)],
            "max_rows": 5,
        },
        {
            "source_id": "ESC-CDM-VCU",
            "source_name": "VCU Libraries Digital Collections / CONTENTdm",
            "base": "https://digital.library.vcu.edu/digital",
            "region": "United States / Mid-Atlantic",
            "terms": [("", "poster", 3), ("", "graphic design", 2), ("", "advertising", 2)],
            "max_rows": 5,
        },
        {
            "source_id": "ESC-CDM-DPL",
            "source_name": "Denver Public Library Digital Collections / CONTENTdm",
            "base": "https://digital.denverlibrary.org/digital",
            "region": "United States / Mountain West / Indigenous",
            "terms": [("", "poster", 3), ("", "advertising", 2), ("", "brochure", 2)],
            "max_rows": 5,
        },
        {
            "source_id": "ESC-CDM-TEMPLE",
            "source_name": "Temple University Libraries Digital Collections / CONTENTdm",
            "base": "https://digital.library.temple.edu/digital",
            "region": "United States / Philadelphia",
            "terms": [("", "poster", 3), ("", "flyer", 2), ("", "advertising", 2)],
            "max_rows": 5,
        },
        {
            "source_id": "ESC-CDM-MARQUETTE",
            "source_name": "Marquette University Digital Collections / CONTENTdm",
            "base": "https://cdm16280.contentdm.oclc.org/digital",
            "region": "United States / Midwest / Indigenous",
            "terms": [("", "poster", 3), ("", "pamphlet", 2), ("", "advertising", 2)],
            "max_rows": 5,
        },
        {
            "source_id": "ESC-CDM-UKY",
            "source_name": "University of Kentucky ExploreUK / CONTENTdm",
            "base": "https://exploreuk.uky.edu/digital",
            "region": "United States / Appalachia",
            "terms": [("", "poster", 3), ("", "advertising", 2), ("", "broadside", 2)],
            "max_rows": 5,
        },
    ]
    for fn in (
        lambda s: capture_auckland(s),
        lambda s: capture_wordpress_source("ESC001", "AHIRA Archivo Historico de Revistas Argentinas", "https://ahira.com.ar", ["revista", "publicidad", "diseño"], "Argentina", s),
        lambda s: capture_wordpress_source("ESC005", "CeDInCI Archivo", "https://cedinci.org", ["afiche", "revista", "publicidad", "diseño"], "Argentina", s),
        lambda s: capture_ndl(s),
        lambda s: capture_contentdm_source(
            source_id="ESC-LAPL",
            source_name="Los Angeles Public Library Tessa / CONTENTdm",
            base="https://tessa2.lapl.org/digital",
            region="United States / Mexico / transnational",
            terms=[("archives", "poster", 5), ("photos", "poster", 3), ("archives", "advertising", 3)],
            seen=s,
            max_rows=8,
        ),
        lambda s: capture_contentdm_source(
            source_id="ESC-UW",
            source_name="University of Washington Digital Collections / CONTENTdm",
            base="https://digitalcollections.lib.washington.edu/digital",
            region="United States / transnational",
            terms=[("social", "poster", 4), ("posters", "poster", 4), ("", "graphic design", 2)],
            seen=s,
            max_rows=6,
        ),
    ):
        rows, summary = fn(seen)
        all_rows.extend(rows)
        summaries.append(summary)
        time.sleep(0.5)
    for config in extra_contentdm_sources:
        rows, summary = capture_contentdm_source(seen=seen, **config)
        all_rows.extend(rows)
        summaries.append(summary)
        time.sleep(0.5)
    all_rows, noise_decisions = apply_noise_filter(all_rows)
    assign_ids(all_rows)
    write_outputs(all_rows, summaries)
    print(f"captured={len(all_rows)} sources={len(set(row['source_name'] for row in all_rows))}")
    print("image_states=" + json.dumps(dict(Counter(row["image_presence_code"] for row in all_rows)), sort_keys=True))
    print("noise_filter=" + json.dumps(dict(noise_decisions), sort_keys=True))


if __name__ == "__main__":
    main()
