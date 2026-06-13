from __future__ import annotations

import csv
import html
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


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GENERATED = ROOT / "generated"
RAW_DIR = DATA / "capture_batch_midcentury_expansion_1931_1970_raw"
RECORDS_CSV = DATA / "capture_batch_midcentury_expansion_1931_1970_records.csv"
SUMMARY_CSV = DATA / "capture_batch_midcentury_expansion_1931_1970_source_summary.csv"
BASELINE_RECORDS_CSV = DATA / "capture_batch_midcentury_1930_1970_records.csv"
SURFACES_JSON = GENERATED / "public_surfaces_v1.json"
FRONTEND_DATA = ROOT / "frontend" / "src" / "data" / "public_surface_mock_v0.json"
FRONTEND_PUBLIC_DATA = ROOT / "frontend" / "public" / "data" / "public_surface_mock_v0.json"

ACCESS_DATE = "2026-05-30"
CAPTURE_BATCH_ID = "CB-MIDCENTURY-EXPANSION-1931-1970"
USER_AGENT = "ModernGDHistory/0.1 midcentury-expansion"
YEAR_START = 1931
YEAR_END = 1970


SOURCE_DEFS = {
    "Wellcome Collection Catalogue API": {
        "source_id": "GSE016",
        "source_name": "Wellcome Collection Catalogue API",
    },
    "Internet Archive / text and periodical collections": {
        "source_id": "GSE103",
        "source_name": "Internet Archive / text and periodical collections",
    },
    "NDL Search": {
        "source_id": "GSE063",
        "source_name": "NDL Search",
    },
    "Chinese Posters": {
        "source_id": "GSE106",
        "source_name": "Chinese Posters",
    },
    "Getty Research Portal": {
        "source_id": "GSE124",
        "source_name": "Getty Research Portal",
    },
    "Europeana": {
        "source_id": "GSE001",
        "source_name": "Europeana",
    },
}


CAPTURE_PLAN = [
    {
        "direction_id": "MX01",
        "direction_name": "wellcome_public_information_and_poster_records",
        "source_name": "Wellcome Collection Catalogue API",
        "adapter": "wellcome",
        "queries": ["poster health", "poster campaign", "public health poster", "advertising poster", "magazine design"],
        "limit": 24,
    },
    {
        "direction_id": "MX02",
        "direction_name": "internet_archive_text_periodical_records",
        "source_name": "Internet Archive / text and periodical collections",
        "adapter": "internet_archive",
        "queries": [
            'title:"graphic design"',
            'title:"commercial art"',
            'title:"industrial design"',
            'title:"advertising art"',
            'subject:"poster"',
            'subject:"typography"',
        ],
        "limit": 30,
    },
    {
        "direction_id": "MX03",
        "direction_name": "ndl_japanese_print_and_design_records",
        "source_name": "NDL Search",
        "adapter": "ndl",
        "queries": ["グラフィックデザイン", "広告", "ポスター", "商業美術", "宣伝美術", "図案"],
        "limit": 18,
    },
    {
        "direction_id": "MX04",
        "direction_name": "chinese_posters_campaign_records",
        "source_name": "Chinese Posters",
        "adapter": "chinese_posters",
        "queries": ["propaganda poster", "women", "industry", "health", "solidarity"],
        "limit": 18,
    },
    {
        "direction_id": "MX05",
        "direction_name": "getty_research_portal_text_records",
        "source_name": "Getty Research Portal",
        "adapter": "getty_portal_seed",
        "queries": ["graphic design history", "poster design", "typography", "corporate identity", "commercial art"],
        "limit": 10,
    },
    {
        "direction_id": "MX06",
        "direction_name": "europeana_rights_aware_gap_probe",
        "source_name": "Europeana",
        "adapter": "europeana_probe",
        "queries": ["poster", "graphic design", "typography", "propaganda poster"],
        "limit": 8,
    },
]


FIELDNAMES = mc.FIELDNAMES + [
    "image_expectation",
    "parser_status",
    "display_mode",
    "ocr_or_excerpt",
    "source_description_raw",
    "editorial_summary",
    "historical_context_note",
    "classification_rationale",
    "uncertainty_note",
    "citation_basis",
]


def fetch_text(url: str, *, accept: str = "*/*") -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
        },
    )
    with urllib.request.urlopen(req, timeout=35) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def fetch_json(url: str) -> Any:
    return json.loads(fetch_text(url, accept="application/json"))


def clean(value: Any, *, max_chars: int = 700) -> str:
    raw = mc.text(value)
    raw = re.sub(r"<script.*?</script>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style.*?</style>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    if len(raw) <= max_chars:
        return raw
    return raw[: max_chars - 1].rsplit(" ", 1)[0] + "…"


def first_year(value: str) -> int | None:
    return mc.first_year(value)


def parse_year(value: Any) -> str:
    return mc.parse_year(value)


def in_scope(date_start: str, date_end: str, date_text: str) -> bool:
    start = int(date_start) if date_start else first_year(date_text)
    end = int(date_end) if date_end else start
    if end is None:
        return False
    if not (YEAR_START <= end <= YEAR_END):
        return False
    if start is not None and end - start > 80:
        return False
    return True


def slug(value: str) -> str:
    return mc.slug(value)


def source_def(name: str) -> dict[str, str]:
    return SOURCE_DEFS[name]


def base_row(plan: dict[str, Any], url: str) -> dict[str, str]:
    source = source_def(plan["source_name"])
    return {
        "direction_id": plan["direction_id"],
        "direction_name": plan["direction_name"],
        "source_id": source["source_id"],
        "source_name": source["source_name"],
        "source_api_url": url,
        "access_date": ACCESS_DATE,
    }


def enrich_row(row: dict[str, str], *, expectation: str, parser_status: str, display_mode: str) -> dict[str, str]:
    text_parts = [
        row.get("source_description", ""),
        row.get("source_notes", ""),
        row.get("source_subjects", ""),
        row.get("ocr_or_excerpt", ""),
    ]
    grounded = clean(" ".join(part for part in text_parts if part), max_chars=900)
    title = row.get("source_title") or "This record"
    source = row.get("source_name") or "the source"
    if grounded:
        summary = clean(f"{title} is indexed from {source}. {grounded}", max_chars=560)
    else:
        summary = clean(f"{title} is indexed from {source}; public descriptive text remains thin and requires follow-up.", max_chars=560)
    context = row.get("historical_context_note") or "Captured for the 1931-1970 expansion pass to increase source diversity and reading evidence beyond museum object metadata."
    rationale = row.get("classification_rationale") or "Provisional Region/Theme/Medium/Movement placement is derived from source title, date, medium, subject, and provider context."
    citation = row.get("citation_basis") or f"{source}. {title}. {row.get('source_record_url') or row.get('source_api_url')}. Accessed {ACCESS_DATE}."
    row.update(
        {
            "image_expectation": expectation,
            "parser_status": parser_status,
            "display_mode": display_mode,
            "source_description_raw": row.get("source_description", ""),
            "editorial_summary": summary,
            "historical_context_note": context,
            "classification_rationale": rationale,
            "uncertainty_note": row.get("uncertainty_note", ""),
            "citation_basis": citation,
        }
    )
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def img_fields(
    code: str,
    basis: str,
    *,
    image_url: str = "",
    viewer: str = "",
    confidence: str = "medium",
    rights_review_required: bool = True,
    local_copy_permitted: bool = False,
    note: str = "",
) -> dict[str, str]:
    fields = mc.image_fields(
        code,
        basis,
        image_url=image_url,
        viewer=viewer,
        confidence=confidence,
        rights_review_required=rights_review_required,
        local_copy_permitted=local_copy_permitted,
        note=note,
    )
    fields["display_mode"] = fields.get("image_frame_behavior", "")
    return fields


def publication_grade_open_license(value: str) -> bool:
    """Return True only for explicit item-level open/public-domain licenses."""
    low = mc.text(value).lower()
    if not low:
        return False
    restrictive = (
        "by-nc",
        "by-nd",
        "noncommercial",
        "non-commercial",
        "no derivatives",
        "no-derivatives",
        "sampling",
    )
    if any(marker in low for marker in restrictive):
        return False
    public_domain_markers = (
        "cc0",
        "creativecommons.org/publicdomain",
        "public domain mark",
        "public-domain",
        "public domain",
        "rightsstatements.org/vocab/noc-oklr",
    )
    if any(marker in low for marker in public_domain_markers):
        return True
    if re.search(r"\bpdm\b", low):
        return True
    if "creativecommons.org/licenses/by/" in low or "creativecommons.org/licenses/by-sa/" in low:
        return True
    if re.search(r"\bcc[-\s]?by(?:[-\s]?sa)?\b", low):
        return True
    return False


def save_raw(payloads: list[tuple[str, Any]]) -> dict[str, str]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for name, payload in payloads:
        path = RAW_DIR / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        paths[name] = str(path.relative_to(ROOT))
    return paths


def wellcome_url(query: str, page: int = 1) -> str:
    params = {
        "query": query,
        "pageSize": "50",
        "page": str(page),
        "include": "items,identifiers,subjects,genres,contributors,production,images",
        "items.locations.locationType": "iiif-presentation",
        "production.dates.from": f"{YEAR_START}-01-01",
        "production.dates.to": f"{YEAR_END}-12-31",
    }
    return "https://api.wellcomecollection.org/catalogue/v2/works?" + urllib.parse.urlencode(params)


def iiif_manifest_thumbnail(manifest_url: str) -> str:
    if not manifest_url:
        return ""
    try:
        manifest = fetch_json(manifest_url)
    except Exception:
        return ""
    for candidate in [
        manifest.get("thumbnail") if isinstance(manifest, dict) else None,
        ((manifest.get("sequences") or [{}])[0].get("canvases") or [{}])[0].get("thumbnail") if isinstance(manifest, dict) else None,
    ]:
        if isinstance(candidate, dict):
            service = candidate.get("service") if isinstance(candidate.get("service"), dict) else {}
            service_id = mc.text(service.get("@id") or service.get("id"))
            if service_id:
                return service_id.rstrip("/") + "/full/400,/0/default.jpg"
            url = mc.text(candidate.get("@id") or candidate.get("id"))
            if url:
                return url
        elif candidate:
            return mc.text(candidate)
    canvases = ((manifest.get("sequences") or [{}])[0].get("canvases") or []) if isinstance(manifest, dict) else []
    if canvases:
        images = canvases[0].get("images") if isinstance(canvases[0], dict) else []
        if images:
            resource = images[0].get("resource") if isinstance(images[0], dict) else {}
            if isinstance(resource, dict):
                service = resource.get("service") if isinstance(resource.get("service"), dict) else {}
                service_id = mc.text(service.get("@id") or service.get("id"))
                if service_id:
                    return service_id.rstrip("/") + "/full/400,/0/default.jpg"
                return mc.text(resource.get("@id") or resource.get("id"))
    return ""


def date_from_wellcome(item: dict[str, Any]) -> tuple[str, str, str]:
    productions = item.get("production") if isinstance(item.get("production"), list) else []
    parts: list[str] = []
    years: list[int] = []
    for prod in productions:
        dates = prod.get("dates") if isinstance(prod, dict) else []
        if isinstance(dates, list):
            for d in dates:
                label = mc.text(d.get("label") if isinstance(d, dict) else d)
                if label:
                    parts.append(label)
                    years.extend(int(y) for y in re.findall(r"(?<!\d)(19[3-6]\d|1970)(?!\d)", label))
    date_text = "; ".join(parts) or mc.text(item.get("createdDate"))
    if not years:
        y = first_year(date_text)
        years = [y] if y else []
    if years:
        return str(min(years)), str(max(years)), date_text or str(min(years))
    return "", "", date_text


def rows_from_wellcome(plan: dict[str, Any]) -> tuple[list[dict[str, str]], list[tuple[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    raw: list[tuple[str, Any]] = []
    failures: list[dict[str, str]] = []
    seen: set[str] = set()
    for query in plan["queries"]:
        url = wellcome_url(query)
        try:
            payload = fetch_json(url)
        except Exception as exc:
            failures.append({"source_name": plan["source_name"], "query": query, "error": str(exc)})
            continue
        raw.append((f"wellcome_search_{slug(query)}.json", payload))
        for item in payload.get("results", [])[:50]:
            if len(rows) >= int(plan["limit"]):
                return rows, raw, failures
            identifier = mc.text(item.get("id"))
            if not identifier or identifier in seen:
                continue
            date_start, date_end, date_text = date_from_wellcome(item)
            if not in_scope(date_start, date_end, date_text):
                continue
            seen.add(identifier)
            record_url = f"https://wellcomecollection.org/works/{identifier}"
            items = item.get("items") if isinstance(item.get("items"), list) else []
            locations: list[dict[str, Any]] = []
            for holding in items:
                if isinstance(holding, dict) and isinstance(holding.get("locations"), list):
                    locations.extend(loc for loc in holding["locations"] if isinstance(loc, dict))
            manifest = ""
            license_text = ""
            for loc in locations:
                url_value = mc.text(loc.get("url"))
                loc_type = mc.text((loc.get("locationType") or {}).get("id") if isinstance(loc.get("locationType"), dict) else loc.get("locationType"))
                license_value = loc.get("license")
                if isinstance(license_value, dict):
                    license_text = mc.text(license_value.get("id") or license_value.get("label") or license_value)
                elif license_value:
                    license_text = mc.text(license_value)
                if "iiif" in loc_type.lower() or "iiif" in url_value:
                    manifest = url_value
                    break
            thumbnail = iiif_manifest_thumbnail(manifest)
            if manifest and publication_grade_open_license(license_text):
                rights = img_fields(
                    "IMG03",
                    f"Wellcome location exposes open licence signal: {license_text}.",
                    image_url=thumbnail,
                    viewer=manifest,
                    confidence="high",
                    rights_review_required=True,
                    note="Open image candidate; retain source item and licence snapshot.",
                )
                expectation, parser_status = "expected", "ok"
            elif manifest:
                rights = img_fields(
                    "IMG02",
                    "Wellcome exposes a source-hosted IIIF/viewer location; local copy is not assumed.",
                    image_url=thumbnail,
                    viewer=manifest,
                    confidence="medium",
                    rights_review_required=True,
                    note="Source-hosted viewer candidate.",
                )
                expectation, parser_status = "expected", "ok"
            elif thumbnail:
                rights = img_fields(
                    "IMG01",
                    "Wellcome exposes a thumbnail but no open local-display basis was captured.",
                    image_url=thumbnail,
                    viewer=record_url,
                    confidence="medium",
                    rights_review_required=True,
                    note="Thumbnail-only candidate.",
                )
                expectation, parser_status = "expected", "ok"
            else:
                rights = img_fields(
                    "IMG00",
                    "Wellcome record may describe a visual source, but no displayable image candidate was captured.",
                    viewer=record_url,
                    confidence="medium",
                    rights_review_required=True,
                    note="Render empty frame and source link; parser status preserved.",
                )
                expectation, parser_status = "expected", "no_candidate"
            contributors = item.get("contributors") if isinstance(item.get("contributors"), list) else []
            contributor_names = [mc.text(c.get("agent", {}).get("label") if isinstance(c.get("agent"), dict) else c.get("label")) for c in contributors if isinstance(c, dict)]
            subjects = item.get("subjects") if isinstance(item.get("subjects"), list) else []
            subject_labels = [mc.text(s.get("label")) for s in subjects if isinstance(s, dict)]
            genres = item.get("genres") if isinstance(item.get("genres"), list) else []
            genre_labels = [mc.text(s.get("label")) for s in genres if isinstance(s, dict)]
            row = {
                **base_row(plan, url),
                **rights,
                "capture_status": "captured",
                "source_identifier": identifier,
                "source_record_url": record_url,
                "source_title": mc.text(item.get("title")),
                "source_creator": "; ".join(c for c in contributor_names if c),
                "source_date_text": date_text,
                "date_start": date_start,
                "date_end": date_end,
                "source_place_text": "",
                "source_object_type": "; ".join(g for g in genre_labels if g) or "Wellcome work",
                "source_medium": "; ".join(g for g in genre_labels if g),
                "source_collection": "Wellcome Collection",
                "source_description": clean(item.get("description") or item.get("title"), max_chars=700),
                "source_notes": clean(item.get("lettering") or item.get("physicalDescription"), max_chars=500),
                "source_subjects": "; ".join(s for s in subject_labels if s),
                "ocr_or_excerpt": "",
                "raw_json_path": "",
            }
            rows.append(enrich_row(row, expectation=expectation, parser_status=parser_status, display_mode=rights["image_frame_behavior"]))
        time.sleep(0.2)
    return rows, raw, failures


def ia_url(query: str) -> str:
    full_query = f"({query}) AND mediatype:texts AND year:[{YEAR_START} TO {YEAR_END}]"
    params = {
        "q": full_query,
        "fl[]": ["identifier", "title", "creator", "date", "year", "description", "subject", "collection", "licenseurl"],
        "rows": "50",
        "page": "1",
        "output": "json",
        "sort[]": "year asc",
    }
    return "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(params, doseq=True)


def rows_from_internet_archive(plan: dict[str, Any]) -> tuple[list[dict[str, str]], list[tuple[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    raw: list[tuple[str, Any]] = []
    failures: list[dict[str, str]] = []
    seen: set[str] = set()
    for query in plan["queries"]:
        url = ia_url(query)
        try:
            payload = fetch_json(url)
        except Exception as exc:
            failures.append({"source_name": plan["source_name"], "query": query, "error": str(exc)})
            continue
        raw.append((f"ia_search_{slug(query)}.json", payload))
        docs = payload.get("response", {}).get("docs", [])
        for item in docs[:50]:
            if len(rows) >= int(plan["limit"]):
                return rows, raw, failures
            identifier = mc.text(item.get("identifier"))
            if not identifier or identifier in seen:
                continue
            seen.add(identifier)
            date_text = mc.text(item.get("date") or item.get("year"))
            date_start = parse_year(item.get("year") or date_text)
            if not in_scope(date_start, "", date_text):
                continue
            record_url = f"https://archive.org/details/{identifier}"
            license_url = mc.text(item.get("licenseurl"))
            if publication_grade_open_license(license_url):
                img_code = "IMG03"
                basis = f"Internet Archive search result exposes explicit licence URL: {license_url}."
                local_copy = False
                review = True
            else:
                img_code = "IMG00"
                basis = "Internet Archive item is valuable for discovery/text, but item-level image reuse is mixed or unclear."
                local_copy = False
                review = True
            thumb = f"https://archive.org/services/img/{identifier}"
            rights = img_fields(
                img_code,
                basis,
                image_url=thumb if img_code == "IMG03" else "",
                viewer=record_url,
                confidence="medium",
                rights_review_required=review,
                local_copy_permitted=local_copy,
                note="Use IA as source/citation first; do not assume scans are reusable without item licence review.",
            )
            subjects = mc.text(item.get("subject"))
            desc = clean(item.get("description"), max_chars=800)
            row = {
                **base_row(plan, url),
                **rights,
                "capture_status": "captured",
                "source_identifier": identifier,
                "source_record_url": record_url,
                "source_title": mc.text(item.get("title")),
                "source_creator": mc.text(item.get("creator")),
                "source_date_text": date_text,
                "date_start": date_start,
                "date_end": "",
                "source_place_text": "",
                "source_object_type": "book / periodical / text scan",
                "source_medium": "digitized text / periodical",
                "source_collection": mc.text(item.get("collection")),
                "source_description": desc or subjects,
                "source_notes": clean(f"Internet Archive metadata record. License URL: {license_url}" if license_url else "Internet Archive metadata record.", max_chars=500),
                "source_subjects": subjects,
                "ocr_or_excerpt": desc,
                "raw_json_path": "",
            }
            rows.append(enrich_row(row, expectation="expected", parser_status="ok", display_mode=rights["image_frame_behavior"]))
        time.sleep(0.2)
    return rows, raw, failures


def ndl_url(query: str) -> str:
    # NDL Search SRU endpoint. Query is intentionally broad; publication
    # filtering happens after XML parsing because source date fields vary.
    cql = f'title="{query}" OR any="{query}"'
    params = {
        "operation": "searchRetrieve",
        "recordSchema": "dcndl",
        "maximumRecords": "50",
        "query": cql,
    }
    return "https://iss.ndl.go.jp/api/sru?" + urllib.parse.urlencode(params)


def ns_text(elem: ET.Element, local_name: str) -> str:
    values = []
    for child in elem.iter():
        if child.tag.split("}")[-1] == local_name and child.text:
            values.append(child.text.strip())
    return "; ".join(dict.fromkeys(v for v in values if v))


def rows_from_ndl(plan: dict[str, Any]) -> tuple[list[dict[str, str]], list[tuple[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    raw: list[tuple[str, Any]] = []
    failures: list[dict[str, str]] = []
    seen: set[str] = set()
    for query in plan["queries"]:
        url = ndl_url(query)
        try:
            xml = fetch_text(url, accept="application/xml,text/xml")
        except Exception as exc:
            failures.append({"source_name": plan["source_name"], "query": query, "error": str(exc)})
            continue
        raw.append((f"ndl_sru_{slug(query)}.xml", xml))
        try:
            root = ET.fromstring(xml)
        except ET.ParseError as exc:
            failures.append({"source_name": plan["source_name"], "query": query, "error": f"XML parse failed: {exc}"})
            continue
        records = [elem for elem in root.iter() if elem.tag.split("}")[-1] == "recordData"]
        for record in records:
            if len(rows) >= int(plan["limit"]):
                return rows, raw, failures
            identifier = ns_text(record, "identifier") or ns_text(record, "recordIdentifier")
            title = ns_text(record, "title")
            if not identifier:
                identifier = title
            if not identifier or identifier in seen:
                continue
            date_text = ns_text(record, "date") or ns_text(record, "issued")
            year = parse_year(date_text)
            if not in_scope(year, "", date_text):
                continue
            seen.add(identifier)
            relation = ns_text(record, "relation")
            record_url = ""
            for candidate in [identifier, relation]:
                match = re.search(r"https?://[^\s;]+", candidate)
                if match:
                    record_url = match.group(0)
                    break
            if not record_url:
                record_url = "https://iss.ndl.go.jp/books/" + urllib.parse.quote(identifier, safe="")
            rights = img_fields(
                "IMG02",
                "NDL Search record is source-linked; image/viewer availability must be checked at item level before local display.",
                viewer=record_url,
                confidence="medium",
                rights_review_required=True,
                note="Source-hosted/viewer-first Japanese record.",
            )
            subjects = ns_text(record, "subject")
            desc = ns_text(record, "description")
            row = {
                **base_row(plan, url),
                **rights,
                "capture_status": "captured",
                "source_identifier": identifier,
                "source_record_url": record_url,
                "source_title": title,
                "source_creator": ns_text(record, "creator"),
                "source_date_text": date_text,
                "date_start": year,
                "date_end": "",
                "source_place_text": "Japan",
                "source_object_type": ns_text(record, "type") or "NDL bibliographic record",
                "source_medium": ns_text(record, "format") or "book / periodical / print record",
                "source_collection": "NDL Search",
                "source_description": clean(desc or subjects or title, max_chars=700),
                "source_notes": clean(ns_text(record, "publisher"), max_chars=400),
                "source_subjects": subjects,
                "ocr_or_excerpt": desc,
                "raw_json_path": "",
            }
            rows.append(enrich_row(row, expectation="expected", parser_status="ok", display_mode=rights["image_frame_behavior"]))
        time.sleep(0.2)
    return rows, raw, failures


def chinese_posters_search_url(query: str) -> str:
    return "https://chineseposters.net/search?keys=" + urllib.parse.quote(query)


CHINESE_POSTERS_SEED_URLS = [
    "https://chineseposters.net/posters/pc-1950-s-002",
    "https://chineseposters.net/posters/pc-1950-002",
    "https://chineseposters.net/posters/pc-1950-001",
    "https://chineseposters.net/posters/pc-1950-s-001",
    "https://chineseposters.net/posters/e13-807",
    "https://chineseposters.net/posters/pc-1950-003",
    "https://chineseposters.net/posters/pc-c-033",
    "https://chineseposters.net/posters/pc-195a-002",
    "https://chineseposters.net/posters/pc-c-038",
    "https://chineseposters.net/themes/early-industrialization",
    "https://chineseposters.net/themes/land-reform",
]


def html_links(html_text: str, base: str) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    for href, label in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html_text, flags=re.I | re.S):
        label_text = clean(label, max_chars=180)
        if not label_text:
            continue
        full = urllib.parse.urljoin(base, html.unescape(href))
        links.append((full, label_text))
    return links


def rows_from_chinese_posters(plan: dict[str, Any]) -> tuple[list[dict[str, str]], list[tuple[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    raw: list[tuple[str, Any]] = []
    failures: list[dict[str, str]] = []
    seen: set[str] = set()
    search_candidates: list[tuple[str, str, str]] = []
    for query in plan["queries"]:
        url = chinese_posters_search_url(query)
        try:
            html_text = fetch_text(url, accept="text/html")
        except Exception as exc:
            failures.append({"source_name": plan["source_name"], "query": query, "error": str(exc)})
            continue
        raw.append((f"chinese_posters_search_{slug(query)}.html", html_text))
        search_candidates.extend(
            (href, label, query)
            for href, label in html_links(html_text, url)
            if "chineseposters.net" in href and not any(skip in href for skip in ["/search/", "/node?", "/user/"])
        )
        time.sleep(0.5)
    if not search_candidates:
        search_candidates = [(href, href.rsplit("/", 1)[-1], "seed") for href in CHINESE_POSTERS_SEED_URLS]
    for href, label, query in search_candidates:
        if len(rows) >= int(plan["limit"]):
            return rows, raw, failures
        if href in seen:
            continue
        seen.add(href)
        try:
            detail_html = fetch_text(href, accept="text/html")
        except Exception as exc:
            failures.append({"source_name": plan["source_name"], "query": href, "error": str(exc)})
            continue
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", detail_html, flags=re.I | re.S)
        title = clean(h1.group(1), max_chars=220) if h1 else label
        raw.append((f"chinese_posters_item_{slug(title)[:48]}.html", detail_html))
        page_text = clean(detail_html, max_chars=1600)
        date_year = first_year(page_text)
        if date_year is None or not (YEAR_START <= date_year <= YEAR_END):
            continue
        image_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', detail_html, flags=re.I)
        image_url = urllib.parse.urljoin(href, html.unescape(image_match.group(1))) if image_match else ""
        rights = img_fields(
            "IMG00",
            "Chinese Posters item pages are high-value visual evidence, but local image reuse is not cleared in this pass.",
            image_url="",
            viewer=href,
            confidence="high",
            rights_review_required=True,
            note="Render empty frame with source link; do not mirror poster image.",
        )
        row = {
            **base_row(plan, href),
            **rights,
            "capture_status": "captured",
            "source_identifier": href,
            "source_record_url": href,
            "source_title": title,
            "source_creator": "",
            "source_date_text": str(date_year),
            "date_start": str(date_year),
            "date_end": "",
            "source_place_text": "Mainland China",
            "source_object_type": "poster / campaign record",
            "source_medium": "poster",
            "source_collection": "Chinese Posters",
            "source_description": page_text,
            "source_notes": "Chinese Posters page harvested as metadata/link-only source; image not mirrored.",
            "source_subjects": query,
            "ocr_or_excerpt": "",
            "raw_json_path": "",
            "image_url_detected": image_url,
        }
        rows.append(enrich_row(row, expectation="expected", parser_status="ok", display_mode=rights["image_frame_behavior"]))
    return rows, raw, failures


def rows_from_getty_seed(plan: dict[str, Any]) -> tuple[list[dict[str, str]], list[tuple[str, Any]], list[dict[str, str]]]:
    # Getty Research Portal is primarily a text/bibliographic enrichment layer.
    # A conservative seed keeps it public as context while later scripts can
    # replace these with item-level portal results.
    rows: list[dict[str, str]] = []
    raw = [("getty_research_portal_seed.json", {"queries": plan["queries"], "note": "Text enrichment seed rows"})]
    failures: list[dict[str, str]] = []
    seed_records = [
        ("Graphic design history bibliography seed", "1931-1970", "graphic design history; poster; typography", "Text enrichment source for design histories, exhibition catalogues, movement anthologies, and regional monographs."),
        ("Poster design bibliography seed", "1931-1970", "poster design; affiche; plakat; cartel", "Bibliographic support for poster-specific archive sheets and folder introductions."),
        ("Typography and commercial art bibliography seed", "1931-1970", "typography; commercial art; advertising art", "Text support for medium and movement notes where object records are thin."),
    ]
    for idx, (title, date_text, subjects, desc) in enumerate(seed_records, start=1):
        rights = img_fields(
            "IMG04",
            "Getty Research Portal seed is a text/bibliographic enrichment record; no image frame is expected.",
            viewer="https://portal.getty.edu/",
            confidence="high",
            rights_review_required=False,
            note="Use as text/context source, not image source.",
        )
        row = {
            **base_row(plan, "https://portal.getty.edu/"),
            **rights,
            "capture_status": "captured",
            "source_identifier": f"GETTY-PORTAL-SEED-{idx:02d}",
            "source_record_url": "https://portal.getty.edu/",
            "source_title": title,
            "source_creator": "Getty Research Portal",
            "source_date_text": date_text,
            "date_start": "1931",
            "date_end": "1970",
            "source_place_text": "Global / transnational",
            "source_object_type": "bibliographic / text source",
            "source_medium": "bibliographic record",
            "source_collection": "Getty Research Portal",
            "source_description": desc,
            "source_notes": "Seed row for text enrichment and citation discovery; not an object record.",
            "source_subjects": subjects,
            "ocr_or_excerpt": desc,
            "raw_json_path": "",
        }
        rows.append(enrich_row(row, expectation="not_expected", parser_status="ok", display_mode=rights["image_frame_behavior"]))
    return rows, raw, failures


def rows_from_europeana_probe(plan: dict[str, Any]) -> tuple[list[dict[str, str]], list[tuple[str, Any]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    raw = [("europeana_probe_note.json", {"queries": plan["queries"], "note": "Europeana requires an API key for production API crawling; retained as gap-repair source."})]
    failures = [
        {
            "source_name": plan["source_name"],
            "query": "; ".join(plan["queries"]),
            "error": "Europeana API key not configured; source retained in matrix for targeted gap repair.",
        }
    ]
    return rows, raw, failures


ADAPTERS = {
    "wellcome": rows_from_wellcome,
    "internet_archive": rows_from_internet_archive,
    "ndl": rows_from_ndl,
    "chinese_posters": rows_from_chinese_posters,
    "getty_portal_seed": rows_from_getty_seed,
    "europeana_probe": rows_from_europeana_probe,
}


def dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, str]] = []
    for row in rows:
        key = (row.get("source_name", ""), row.get("source_identifier", "") or row.get("source_record_url", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def write_records(rows: list[dict[str, str]]) -> None:
    with RECORDS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(rows: list[dict[str, str]], failures: list[dict[str, str]]) -> None:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["direction_id"], row["source_id"], row["source_name"])].append(row)
    summary_rows = []
    for (direction_id, source_id, source_name), items in sorted(grouped.items()):
        counter = Counter(row["image_presence_code"] for row in items)
        summary_rows.append(
            {
                "direction_id": direction_id,
                "source_id": source_id,
                "source_name": source_name,
                "captured_count": str(len(items)),
                "failure_count": str(sum(1 for failure in failures if failure["source_name"] == source_name)),
                "img00_count": str(counter.get("IMG00", 0)),
                "img01_count": str(counter.get("IMG01", 0)),
                "img02_count": str(counter.get("IMG02", 0)),
                "img03_count": str(counter.get("IMG03", 0)),
                "img04_count": str(counter.get("IMG04", 0)),
                "notes": "Second 1931-1970 mixed-source expansion batch; not final source record until review.",
            }
        )
    captured_sources = {row["source_name"] for row in rows}
    for failure in failures:
        if failure["source_name"] in captured_sources:
            continue
        summary_rows.append(
            {
                "direction_id": "",
                "source_id": "",
                "source_name": failure["source_name"],
                "captured_count": "0",
                "failure_count": "1",
                "img00_count": "0",
                "img01_count": "0",
                "img02_count": "0",
                "img03_count": "0",
                "img04_count": "0",
                "notes": failure["error"],
            }
        )
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
        writer.writerows(summary_rows)


def enhance_payload_text(payload: dict[str, Any], rows: list[dict[str, str]]) -> dict[str, Any]:
    by_capture = {row["capture_id"]: row for row in rows}
    payload["meta"] = {
        "generatedAt": ACCESS_DATE,
        "status": "generated",
        "note": "Generated 1931-1970 mixed-source expansion payload. Static export; not final publication data.",
    }
    for surface in payload.get("surfaces", []):
        source_record_id = surface.get("sourceRecordId", "")
        row = by_capture.get(source_record_id)
        if not row:
            continue
        surface["descriptionSummary"] = row.get("editorial_summary") or surface.get("descriptionSummary") or surface.get("sourceDescription")
        surface["sourceDescription"] = row.get("source_description") or surface.get("sourceDescription")
        surface["historicalContextNote"] = row.get("historical_context_note")
        surface["classificationRationale"] = row.get("classification_rationale")
        surface["uncertaintyNote"] = row.get("uncertainty_note")
        surface["citationBasis"] = row.get("citation_basis")
        image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
        if image:
            image["expectation"] = row.get("image_expectation")
            image["parserStatus"] = row.get("parser_status")
            image["displayMode"] = row.get("display_mode") or row.get("image_frame_behavior")
            if row.get("image_presence_code") == "IMG00":
                image["placeholderText"] = row.get("image_state_review_note") or "Image evidence remains source-linked; this project does not display a local copy."
    return payload


def write_payload(rows: list[dict[str, str]]) -> dict[str, Any]:
    # Reuse the existing publication-surface generator, then inject the new
    # text-enrichment fields that older payloads did not have.
    payload = mc.build_public_payload(rows)
    payload = enhance_payload_text(payload, rows)
    GENERATED.mkdir(parents=True, exist_ok=True)
    SURFACES_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    FRONTEND_DATA.parent.mkdir(parents=True, exist_ok=True)
    FRONTEND_PUBLIC_DATA.parent.mkdir(parents=True, exist_ok=True)
    FRONTEND_DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    FRONTEND_PUBLIC_DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def load_baseline_rows() -> list[dict[str, str]]:
    if not BASELINE_RECORDS_CSV.exists():
        return []
    rows: list[dict[str, str]] = []
    with BASELINE_RECORDS_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            code = row.get("image_presence_code", "")
            expectation = "not_expected" if code == "IMG04" else "expected"
            row.setdefault("image_expectation", expectation)
            row.setdefault("parser_status", "legacy")
            row.setdefault("display_mode", row.get("image_frame_behavior", ""))
            row.setdefault("ocr_or_excerpt", row.get("source_description", ""))
            row.setdefault("source_description_raw", row.get("source_description", ""))
            row.setdefault("historical_context_note", "Baseline 1931-1970 capture retained for cumulative frontend verification.")
            row.setdefault("classification_rationale", "Legacy provisional classification derived from source title, date, medium, subject, and provider context.")
            row.setdefault("uncertainty_note", "")
            row.setdefault(
                "citation_basis",
                f"{row.get('source_name', '')}. {row.get('source_title', '')}. {row.get('source_record_url') or row.get('source_api_url')}. Accessed {row.get('access_date') or ACCESS_DATE}.",
            )
            if not row.get("editorial_summary"):
                row["editorial_summary"] = clean(
                    f"{row.get('source_title', 'This record')} is indexed from {row.get('source_name', 'the source')}. "
                    f"{row.get('source_description') or row.get('source_notes') or row.get('source_subjects')}",
                    max_chars=560,
                )
            for field in FIELDNAMES:
                row.setdefault(field, "")
            rows.append(row)
    return rows


def main() -> None:
    all_rows: list[dict[str, str]] = []
    all_raw: list[tuple[str, Any]] = []
    failures: list[dict[str, str]] = []
    for plan in CAPTURE_PLAN:
        adapter = ADAPTERS[plan["adapter"]]
        try:
            rows, raw, source_failures = adapter(plan)
        except Exception as exc:
            rows, raw, source_failures = [], [], [{"source_name": plan["source_name"], "query": "*", "error": str(exc)}]
        all_rows.extend(rows)
        all_raw.extend(raw)
        failures.extend(source_failures)
    raw_paths = save_raw(all_raw)
    rows = dedupe_rows(all_rows)
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"MX1970R{index:03d}"
        for raw_name, raw_path in raw_paths.items():
            if raw_name.startswith(slug(row.get("source_identifier", ""))):
                row["raw_json_path"] = raw_path
                break
        for field in FIELDNAMES:
            row.setdefault(field, "")
    write_records(rows)
    write_summary(rows, failures)
    baseline_rows = load_baseline_rows()
    payload_rows = dedupe_rows(rows + baseline_rows)
    payload = write_payload(payload_rows)
    counter = Counter(row["image_presence_code"] for row in rows)
    payload_counter = Counter(row["image_presence_code"] for row in payload_rows)
    print(f"Captured rows: {len(rows)}")
    print(f"Cumulative payload rows: {len(payload_rows)}")
    print(f"Failures: {len(failures)}")
    print("Image states:", dict(sorted(counter.items())))
    print("Payload image states:", dict(sorted(payload_counter.items())))
    print(f"Surfaces: {len(payload.get('surfaces', []))}")
    print(f"Folders: {len(payload.get('folders', []))}")
    print(f"Wrote {RECORDS_CSV.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"Synced frontend payload to {FRONTEND_DATA.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
