from __future__ import annotations

import csv
import html
import json
import re
import time
import argparse
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GENERATED = ROOT / "generated"
SURFACES_JSON = GENERATED / "public_surfaces_v1.json"
SOURCE_REGISTRY = DATA / "source_registry.csv"

ACCESS_DATE = "2026-05-30"
RAW_DIR = DATA / "capture_batch_midcentury_1930_1970_raw"
RECORDS_CSV = DATA / "capture_batch_midcentury_1930_1970_records.csv"
SUMMARY_CSV = DATA / "capture_batch_midcentury_1930_1970_source_summary.csv"
CAPTURE_BATCH_ID = "CB-MIDCENTURY-1930-1970"
USER_AGENT = "ModernGDHistory/0.1 midcentury-capture"
YEAR_START = 1931
YEAR_END = 1970
TARGET_COUNT = 100


FIELDNAMES = [
    "capture_id",
    "direction_id",
    "direction_name",
    "source_id",
    "source_name",
    "source_api_url",
    "capture_status",
    "source_identifier",
    "source_record_url",
    "source_title",
    "source_creator",
    "source_date_text",
    "date_start",
    "date_end",
    "source_place_text",
    "source_object_type",
    "source_medium",
    "source_collection",
    "source_description",
    "source_notes",
    "source_subjects",
    "source_rights_text",
    "rights_uri",
    "rights_basis",
    "image_presence_code",
    "image_presence_basis",
    "image_state_evaluation",
    "image_state_confidence",
    "rights_review_required",
    "image_state_review_note",
    "image_frame_behavior",
    "image_url_detected",
    "local_copy_permitted",
    "iiif_or_viewer_available",
    "fallback_required",
    "fallback_reason",
    "raw_json_path",
    "access_date",
]


FOLDER_TYPES = [
    {
        "type": "region",
        "label": "Region",
        "color": "#2F5BEA",
        "scopeNote": "Geographic and transregional folder views. Time remains the default sorting axis.",
    },
    {
        "type": "theme",
        "label": "Theme",
        "color": "#111111",
        "scopeNote": "Research themes such as commercial print ecology, advertising, circulation, technology, or public information.",
    },
    {
        "type": "medium",
        "label": "Medium",
        "color": "#D94A38",
        "scopeNote": "Material and technological formats such as poster, trade card, periodical, sheet music cover, catalogue, or lithographic print.",
    },
    {
        "type": "movement",
        "label": "Movement",
        "color": "#E2C044",
        "scopeNote": "Historical formations, movements, schools, and named design cultures.",
    },
]


CAPTURE_PLAN = [
    {
        "direction_id": "MC01",
        "direction_name": "midcentury_open_and_museum_poster_records",
        "source_name": "Art Institute of Chicago API",
        "adapter": "aic",
        "queries": [
            "poster",
            "world war poster",
            "travel poster",
            "typography poster",
            "exhibition poster",
            "graphic design",
        ],
        "limit": 25,
    },
    {
        "direction_id": "MC02",
        "direction_name": "midcentury_design_museum_records",
        "source_name": "V&A Collections API",
        "adapter": "vam",
        "queries": ["poster", "travel poster", "London Transport poster", "typography", "graphic design", "photomontage", "exhibition poster"],
        "limit": 25,
    },
    {
        "direction_id": "MC03",
        "direction_name": "midcentury_public_information_and_propaganda_records",
        "source_name": "Library of Congress loc.gov API",
        "adapter": "loc",
        "queries": ["WPA poster", "World War poster", "propaganda poster", "public health poster", "civil rights poster", "travel poster", "poster"],
        "limit": 30,
    },
    {
        "direction_id": "MC04",
        "direction_name": "midcentury_open_museum_print_records",
        "source_name": "Cleveland Museum Open Access API",
        "adapter": "cleveland",
        "queries": ["poster", "graphic design", "photomontage", "advertisement", "typography"],
        "limit": 15,
    },
    {
        "direction_id": "MC05",
        "direction_name": "midcentury_met_open_access_records",
        "source_name": "The Met Open Access",
        "adapter": "met",
        "queries": ["poster", "graphic design", "advertising", "typography", "propaganda"],
        "limit": 15,
    },
]


def read_source_registry() -> dict[str, dict[str, str]]:
    with SOURCE_REGISTRY.open(encoding="utf-8", newline="") as f:
        return {row["name"]: row for row in csv.DictReader(f)}


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(text(item) for item in value if text(item))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def clean_text(value: Any, *, max_chars: int = 520) -> str:
    raw = text(value)
    if not raw:
        return ""
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    if len(raw) <= max_chars:
        return raw
    return raw[: max_chars - 1].rsplit(" ", 1)[0] + "…"


def join_notes(value: Any, *, max_chars: int = 520) -> str:
    if not value:
        return ""
    notes: list[str] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                note = item.get("note") or item.get("label") or item.get("description") or item.get("text")
                if note:
                    notes.append(clean_text(note, max_chars=180))
            else:
                notes.append(clean_text(item, max_chars=180))
    elif isinstance(value, dict):
        for key, item in value.items():
            if item:
                notes.append(f"{key}: {clean_text(item, max_chars=160)}")
    else:
        notes.append(clean_text(value, max_chars=180))
    return clean_text("; ".join(note for note in notes if note), max_chars=max_chars)


def detail_json(url: str) -> dict[str, Any]:
    try:
        data = fetch_json(url)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def extract_image_url(value: Any) -> str:
    if isinstance(value, dict):
        return text(value.get("url"))
    return text(value)


def first_year(value: str) -> int | None:
    if not value:
        return None
    matches = re.findall(r"(?<!\d)(1[5-9]\d{2}|20\d{2})(?!\d)", value)
    if not matches:
        return None
    return int(matches[0])


def parse_year(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        year = int(value)
    except (TypeError, ValueError):
        year = first_year(text(value))
        if year is None:
            return ""
    if 1500 <= year <= 2100:
        return str(year)
    return ""


def in_scope(date_start: str, date_end: str, date_text: str) -> bool:
    start = int(date_start) if date_start else first_year(date_text)
    end = int(date_end) if date_end else start
    if end is None:
        return False
    # Period batches are assigned by end year. This prevents a broad
    # start-date bias and follows the project rule that long-stage captures
    # fall into the bucket where their end year lands.
    if not (YEAR_START <= end <= YEAR_END):
        return False
    # Exclude very broad century-level ranges from publishable preview rows.
    if start is not None and end - start > 60:
        return False
    return True


def graphic_relevant(row_blob: str) -> bool:
    blob = row_blob.lower()
    include_terms = [
        "trade card",
        "advertis",
        "poster",
        "lithograph",
        "chromolithograph",
        "engraving",
        "etching",
        "wood engraving",
        "sheet music",
        "catalogue",
        "catalog",
        "printer",
        "printseller",
        "bookbinding",
        "label",
        "packaging",
        "broadsheet",
        "public information",
        "propaganda",
        "wpa",
        "war",
        "identity",
        "typography",
        "photomontage",
        "transport",
        "travel",
        "exhibition",
        "health",
        "civil rights",
        "corporate",
        "graphic design",
    ]
    exclude_terms = [
        "oil on canvas",
        "albumen silver print",
        "photograph",
        "ambrotype",
        "furniture",
        "silver",
        "marble",
        "table",
        "ceramic",
        "textile",
    ]
    if not any(term in blob for term in include_terms):
        return False
    if any(term in blob for term in exclude_terms) and not any(
        strong in blob for strong in ["trade card", "advertis", "poster", "sheet music", "catalog"]
    ):
        return False
    return True


def image_fields(
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
    behavior = {
        "IMG00": "empty_rights_frame",
        "IMG01": "thumbnail_frame",
        "IMG02": "source_viewer_frame",
        "IMG03": "open_image_frame",
        "IMG04": "no_image_frame",
    }[code]
    return {
        "source_rights_text": basis,
        "rights_uri": "",
        "rights_basis": basis,
        "image_presence_code": code,
        "image_presence_basis": basis,
        "image_state_evaluation": f"{code}: {basis}",
        "image_state_confidence": confidence,
        "rights_review_required": "true" if rights_review_required else "false",
        "image_state_review_note": note,
        "image_frame_behavior": behavior,
        "image_url_detected": image_url,
        "local_copy_permitted": "true" if local_copy_permitted else "false",
        "iiif_or_viewer_available": viewer,
        "fallback_required": "false",
        "fallback_reason": "",
    }


def base_row(plan: dict[str, Any], source: dict[str, str], url: str) -> dict[str, str]:
    return {
        "direction_id": plan["direction_id"],
        "direction_name": plan["direction_name"],
        "source_id": source["source_id"],
        "source_name": plan["source_name"],
        "source_api_url": url,
        "access_date": ACCESS_DATE,
    }


def met_search_url(query: str) -> str:
    return "https://collectionapi.metmuseum.org/public/collection/v1/search?" + urllib.parse.urlencode(
        {"hasImages": "true", "dateBegin": str(YEAR_START), "dateEnd": str(YEAR_END), "q": query}
    )


def rows_from_met(plan: dict[str, Any], source: dict[str, str]) -> tuple[list[dict[str, str]], list[tuple[str, Any]]]:
    rows: list[dict[str, str]] = []
    raw_payloads: list[tuple[str, Any]] = []
    seen: set[str] = set()
    for query in plan["queries"]:
        search_url = met_search_url(query)
        search_payload = fetch_json(search_url)
        raw_payloads.append((f"met_search_{slug(query)}.json", search_payload))
        object_ids = search_payload.get("objectIDs") or []
        for object_id in object_ids[:120]:
            if len(rows) >= int(plan["limit"]):
                return rows, raw_payloads
            identifier = str(object_id)
            if identifier in seen:
                continue
            detail_url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{identifier}"
            try:
                item = fetch_json(detail_url)
            except Exception:
                continue
            seen.add(identifier)
            raw_payloads.append((f"met_object_{identifier}.json", item))
            date_start = parse_year(item.get("objectBeginDate"))
            date_end = parse_year(item.get("objectEndDate"))
            date_text = text(item.get("objectDate"))
            if not in_scope(date_start, date_end, date_text):
                continue
            blob = " ".join(
                [
                    text(item.get("title")),
                    text(item.get("objectName") or item.get("classification")),
                    text(item.get("medium")),
                ]
            )
            if not graphic_relevant(blob):
                continue
            image_url = text(item.get("primaryImageSmall") or item.get("primaryImage"))
            is_open = bool(item.get("isPublicDomain"))
            if is_open and image_url:
                rights = image_fields(
                    "IMG03",
                    "Met API reports isPublicDomain=true for this object.",
                    image_url=image_url,
                    viewer=text(item.get("objectURL")),
                    confidence="high",
                    rights_review_required=True,
                    note="Open image candidate; keep source credit and source return visible.",
                )
            elif image_url:
                rights = image_fields(
                    "IMG00",
                    "Met API exposes an image but public-domain/open-display evidence was not captured.",
                    image_url=image_url,
                    viewer=text(item.get("objectURL")),
                    confidence="medium",
                    rights_review_required=True,
                    note="Render empty image frame until record-level rights evidence upgrades it.",
                )
            else:
                rights = image_fields(
                    "IMG04",
                    "Met detail row does not expose an image URL in this capture.",
                    viewer=text(item.get("objectURL")),
                    confidence="high",
                    rights_review_required=False,
                    note="Render as text/source page without image frame.",
                )
            rows.append(
                {
                    **base_row(plan, source, search_url),
                    **rights,
                    "capture_status": "captured",
                    "source_identifier": identifier,
                    "source_record_url": text(item.get("objectURL")) or detail_url,
                    "source_title": text(item.get("title")),
                    "source_creator": text(item.get("artistDisplayName") or item.get("artistDisplayBio")),
                    "source_date_text": date_text,
                    "date_start": date_start,
                    "date_end": date_end,
                    "source_place_text": text(item.get("country") or item.get("culture") or item.get("region")),
                    "source_object_type": text(item.get("objectName") or item.get("classification")),
                    "source_medium": text(item.get("medium")),
                    "source_collection": text(item.get("department")),
                }
            )
        time.sleep(0.2)
    return rows, raw_payloads


def aic_url(query: str, page: int = 1) -> str:
    return "https://api.artic.edu/api/v1/artworks/search?" + urllib.parse.urlencode(
        {
            "q": query,
            "fields": ",".join(
                [
                    "id",
                    "title",
                    "artist_display",
                    "date_display",
                    "place_of_origin",
                    "medium_display",
                    "classification_titles",
                    "api_link",
                    "image_id",
                    "thumbnail",
                    "is_public_domain",
                    "artist_id",
                    "date_start",
                    "date_end",
                ]
            ),
            "page": str(page),
            "limit": "50",
        }
    )


def rows_from_aic(plan: dict[str, Any], source: dict[str, str]) -> tuple[list[dict[str, str]], list[tuple[str, Any]]]:
    rows: list[dict[str, str]] = []
    raw_payloads: list[tuple[str, Any]] = []
    seen: set[str] = set()
    for query in plan["queries"]:
        url = aic_url(query)
        payload = fetch_json(url)
        raw_payloads.append((f"aic_search_{slug(query)}.json", payload))
        for item in payload.get("data", [])[:50]:
            if len(rows) >= int(plan["limit"]):
                return rows, raw_payloads
            identifier = text(item.get("id"))
            if not identifier or identifier in seen:
                continue
            date_text = text(item.get("date_display"))
            date_start = parse_year(item.get("date_start") or date_text)
            date_end = parse_year(item.get("date_end") or date_text)
            if not in_scope(date_start, date_end, date_text):
                continue
            blob = " ".join(
                [
                    text(item.get("title")),
                    text(item.get("classification_titles")),
                    text(item.get("medium_display")),
                ]
            )
            if not graphic_relevant(blob):
                continue
            seen.add(identifier)
            detail_url = "https://api.artic.edu/api/v1/artworks/" + identifier + "?" + urllib.parse.urlencode(
                {
                    "fields": ",".join(
                        [
                            "id",
                            "description",
                            "short_description",
                            "publication_history",
                            "exhibition_history",
                            "provenance_text",
                            "term_titles",
                            "category_titles",
                            "classification_titles",
                            "credit_line",
                        ]
                    )
                }
            )
            detail = detail_json(detail_url).get("data", {})
            raw_payloads.append((f"aic_object_{identifier}.json", detail))
            image_id = text(item.get("image_id"))
            image = f"https://www.artic.edu/iiif/2/{image_id}/full/843,/0/default.jpg" if image_id else ""
            public_domain = bool(item.get("is_public_domain"))
            if public_domain and image:
                rights = image_fields(
                    "IMG03",
                    "AIC search API reports is_public_domain=true.",
                    image_url=image,
                    viewer=image,
                    confidence="high",
                    rights_review_required=True,
                    note="Open image display candidate; final publication still needs item-page rights capture.",
                )
            elif image:
                rights = image_fields(
                    "IMG00",
                    "AIC image identifier exists, but search row does not report public-domain status.",
                    image_url=image,
                    viewer=image,
                    confidence="high",
                    rights_review_required=True,
                    note="Render empty image frame until item-level rights evidence upgrades it.",
                )
            else:
                rights = image_fields(
                    "IMG04",
                    "AIC row does not expose an image identifier in this capture.",
                    confidence="high",
                    rights_review_required=False,
                    note="Render as text/source page without image frame.",
                )
            rows.append(
                {
                    **base_row(plan, source, url),
                    **rights,
                    "capture_status": "captured",
                    "source_identifier": identifier,
                    "source_record_url": f"https://www.artic.edu/artworks/{identifier}",
                    "source_title": text(item.get("title")),
                    "source_creator": text(item.get("artist_display")),
                    "source_date_text": date_text,
                    "date_start": date_start,
                    "date_end": date_end,
                    "source_place_text": text(item.get("place_of_origin")),
                    "source_object_type": text(item.get("classification_titles")),
                    "source_medium": text(item.get("medium_display")),
                    "source_collection": "Art Institute of Chicago",
                    "source_description": clean_text(detail.get("short_description") or detail.get("description")),
                    "source_notes": clean_text(detail.get("publication_history") or detail.get("exhibition_history") or detail.get("provenance_text")),
                    "source_subjects": text(detail.get("term_titles") or detail.get("category_titles") or detail.get("classification_titles")),
                }
            )
    return rows, raw_payloads


def vam_url(query: str, page: int = 1) -> str:
    return "https://api.vam.ac.uk/v2/objects/search?" + urllib.parse.urlencode(
        {"q": query, "page_size": "50", "page": str(page)}
    )


def rows_from_vam(plan: dict[str, Any], source: dict[str, str]) -> tuple[list[dict[str, str]], list[tuple[str, Any]]]:
    rows: list[dict[str, str]] = []
    raw_payloads: list[tuple[str, Any]] = []
    seen: set[str] = set()
    for query in plan["queries"]:
        url = vam_url(query)
        payload = fetch_json(url)
        raw_payloads.append((f"vam_search_{slug(query)}.json", payload))
        for item in payload.get("records", [])[:80]:
            if len(rows) >= int(plan["limit"]):
                return rows, raw_payloads
            identifier = text(item.get("systemNumber"))
            if not identifier or identifier in seen:
                continue
            date_text = text(item.get("_primaryDate"))
            date_start = parse_year(date_text)
            if not in_scope(date_start, "", date_text):
                continue
            blob = " ".join([text(item.get("_primaryTitle")), text(item.get("objectType")), date_text])
            if not graphic_relevant(blob):
                continue
            seen.add(identifier)
            detail = detail_json(f"https://api.vam.ac.uk/v2/object/{identifier}")
            raw_payloads.append((f"vam_object_{identifier}.json", detail))
            record = detail.get("record", {}) if isinstance(detail.get("record"), dict) else {}
            categories = record.get("categories") if isinstance(record.get("categories"), list) else []
            images = item.get("_images") if isinstance(item.get("_images"), dict) else {}
            thumb = text(images.get("_primary_thumbnail")) if isinstance(images, dict) else ""
            iiif_base = text(images.get("_iiif_image_base_url")) if isinstance(images, dict) else ""
            viewer = iiif_base or thumb
            if iiif_base:
                rights = image_fields(
                    "IMG02",
                    "V&A API exposes source-hosted IIIF/image service metadata; no local copy is permitted in this pass.",
                    image_url=thumb,
                    viewer=viewer,
                    confidence="medium",
                    rights_review_required=True,
                    note="Source-hosted viewer candidate; keep source return visible.",
                )
            elif thumb:
                rights = image_fields(
                    "IMG01",
                    "V&A API exposes a source thumbnail but record-level image terms still require review.",
                    image_url=thumb,
                    viewer=thumb,
                    confidence="medium",
                    rights_review_required=True,
                    note="Thumbnail-only candidate.",
                )
            else:
                rights = image_fields(
                    "IMG04",
                    "V&A row does not expose image metadata in this capture.",
                    confidence="high",
                    rights_review_required=False,
                    note="Render as text/source page without image frame.",
                )
            maker = item.get("_primaryMaker") if isinstance(item.get("_primaryMaker"), dict) else {}
            rows.append(
                {
                    **base_row(plan, source, url),
                    **rights,
                    "capture_status": "captured",
                    "source_identifier": identifier,
                    "source_record_url": f"https://collections.vam.ac.uk/item/{identifier}/",
                    "source_title": text(item.get("_primaryTitle")),
                    "source_creator": text(maker.get("name")),
                    "source_date_text": date_text,
                    "date_start": date_start,
                    "date_end": "",
                    "source_place_text": text(item.get("_primaryPlace")),
                    "source_object_type": text(item.get("objectType")),
                    "source_medium": "",
                    "source_collection": "V&A Collections",
                    "source_description": clean_text(record.get("physicalDescription") or record.get("summaryDescription") or record.get("briefDescription")),
                    "source_notes": join_notes(record.get("production") or record.get("materialsAndTechniques") or record.get("objectHistory")),
                    "source_subjects": text([category.get("text") for category in categories if isinstance(category, dict)]),
                }
            )
    return rows, raw_payloads


def loc_url(query: str) -> str:
    return "https://www.loc.gov/pictures/search/?" + urllib.parse.urlencode({"q": query, "fo": "json", "c": "50"})


def rows_from_loc(plan: dict[str, Any], source: dict[str, str]) -> tuple[list[dict[str, str]], list[tuple[str, Any]]]:
    rows: list[dict[str, str]] = []
    raw_payloads: list[tuple[str, Any]] = []
    seen: set[str] = set()
    for query in plan["queries"]:
        url = loc_url(query)
        payload = fetch_json(url)
        raw_payloads.append((f"loc_search_{slug(query)}.json", payload))
        for item in payload.get("results", [])[:50]:
            if len(rows) >= int(plan["limit"]):
                return rows, raw_payloads
            identifier = text(item.get("pk") or item.get("number"))
            if not identifier or identifier in seen:
                continue
            date_text = text(item.get("created_published_date") or item.get("date"))
            date_start = parse_year(date_text)
            if not in_scope(date_start, "", date_text):
                continue
            blob = " ".join([text(item.get("title")), text(item.get("medium_brief")), text(item.get("medium"))])
            if not graphic_relevant(blob):
                continue
            seen.add(identifier)
            links = item.get("links") if isinstance(item.get("links"), dict) else {}
            detail_url = text(links.get("item"))
            detail = detail_json(detail_url + "?fo=json") if detail_url else {}
            detail_item = detail.get("item", {}) if isinstance(detail.get("item"), dict) else {}
            image = item.get("image") if isinstance(item.get("image"), dict) else {}
            image_url = text(image.get("thumb") or image.get("full")) if isinstance(image, dict) else ""
            if image_url and "notdigitized" not in image_url and "not_digitized" not in image_url:
                rights = image_fields(
                    "IMG01",
                    "LOC search row exposes a thumbnail; item-level rights advisory was not captured in this pass.",
                    image_url=image_url,
                    viewer=text(links.get("item")),
                    confidence="medium",
                    rights_review_required=True,
                    note="Thumbnail candidate only; keep source return visible.",
                )
            else:
                rights = image_fields(
                    "IMG04",
                    "LOC search row does not expose a usable image in this capture.",
                    viewer=text(links.get("item")),
                    confidence="high",
                    rights_review_required=False,
                    note="Render as text/source page without image frame.",
                )
            rows.append(
                {
                    **base_row(plan, source, url),
                    **rights,
                    "capture_status": "captured",
                    "source_identifier": identifier,
                    "source_record_url": text(links.get("item")),
                    "source_title": text(item.get("title")),
                    "source_creator": text(item.get("creator")),
                    "source_date_text": date_text,
                    "date_start": date_start,
                    "date_end": "",
                    "source_place_text": "",
                    "source_object_type": text(item.get("medium_brief")),
                    "source_medium": text(item.get("medium")),
                    "source_collection": text(item.get("collection")),
                    "source_description": clean_text(detail_item.get("summary") or detail_item.get("description")),
                    "source_notes": join_notes(detail_item.get("notes")),
                    "source_subjects": text(detail_item.get("subjects") or item.get("subjects")),
                }
            )
    return rows, raw_payloads


def cleveland_url(query: str) -> str:
    return "https://openaccess-api.clevelandart.org/api/artworks/?" + urllib.parse.urlencode(
        {"q": query, "has_image": "1", "limit": "50"}
    )


def rows_from_cleveland(plan: dict[str, Any], source: dict[str, str]) -> tuple[list[dict[str, str]], list[tuple[str, Any]]]:
    rows: list[dict[str, str]] = []
    raw_payloads: list[tuple[str, Any]] = []
    seen: set[str] = set()
    for query in plan["queries"]:
        url = cleveland_url(query)
        payload = fetch_json(url)
        raw_payloads.append((f"cleveland_search_{slug(query)}.json", payload))
        for item in payload.get("data", [])[:50]:
            if len(rows) >= int(plan["limit"]):
                return rows, raw_payloads
            identifier = text(item.get("accession_number") or item.get("id"))
            if not identifier or identifier in seen:
                continue
            date_text = text(item.get("creation_date"))
            date_start = parse_year(item.get("creation_date_earliest") or date_text)
            date_end = parse_year(item.get("creation_date_latest") or date_text)
            if not in_scope(date_start, date_end, date_text):
                continue
            blob = " ".join([text(item.get("title")), text(item.get("type")), text(item.get("technique"))])
            if not graphic_relevant(blob):
                continue
            seen.add(identifier)
            license_status = text(item.get("share_license_status"))
            images = item.get("images") if isinstance(item.get("images"), dict) else {}
            image_url_value = (images.get("web") or images.get("print") or images.get("full")) if isinstance(images, dict) else ""
            image_url = extract_image_url(image_url_value)
            if license_status.upper() == "CC0" and image_url:
                rights = image_fields(
                    "IMG03",
                    f"Cleveland Museum API share_license_status={license_status}.",
                    image_url=image_url,
                    viewer=image_url,
                    confidence="high",
                    rights_review_required=True,
                    note="Open image display candidate; keep source credit and source return visible.",
                )
            elif image_url:
                rights = image_fields(
                    "IMG00",
                    f"Cleveland Museum API share_license_status={license_status or 'not captured'}.",
                    image_url=image_url,
                    viewer=image_url,
                    confidence="medium",
                    rights_review_required=True,
                    note="Image exists but open reuse evidence was not captured.",
                )
            else:
                rights = image_fields(
                    "IMG04",
                    "Cleveland Museum API row did not expose an image URL in this capture.",
                    confidence="high",
                    rights_review_required=False,
                    note="Render as text/source page without image frame.",
                )
            creators = item.get("creators", [])
            rows.append(
                {
                    **base_row(plan, source, url),
                    **rights,
                    "capture_status": "captured",
                    "source_identifier": identifier,
                    "source_record_url": text(item.get("url")) or f"https://www.clevelandart.org/art/{identifier}",
                    "source_title": text(item.get("title")),
                    "source_creator": text([creator.get("description") for creator in creators] if isinstance(creators, list) else ""),
                    "source_date_text": date_text,
                    "date_start": date_start,
                    "date_end": date_end,
                    "source_place_text": text(item.get("culture")),
                    "source_object_type": text(item.get("type")),
                    "source_medium": text(item.get("technique")),
                    "source_collection": text(item.get("collection") or item.get("department")),
                    "source_description": clean_text(item.get("description")),
                    "source_notes": join_notes(item.get("inscriptions") or item.get("provenance")),
                    "source_subjects": text(item.get("tags") or item.get("alternate_titles")),
                }
            )
    return rows, raw_payloads


ADAPTERS = {
    "met": rows_from_met,
    "aic": rows_from_aic,
    "vam": rows_from_vam,
    "loc": rows_from_loc,
    "cleveland": rows_from_cleveland,
}


def slug(value: str) -> str:
    out = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return out or "query"


def write_raw(payloads: list[tuple[str, Any]]) -> dict[str, str]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for name, payload in payloads:
        path = RAW_DIR / name
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        paths[name] = str(path.relative_to(ROOT))
    return paths


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
                "notes": "Midcentury 1930-1970 production candidate batch; not final source record until review.",
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


def folder_id(folder_type: str, label: str) -> str:
    return f"FOL-{folder_type.upper()}-{slug(label).upper()}"


def region_for(row: dict[str, str]) -> tuple[str, str, dict[str, list[str]]]:
    blob = " ".join(
        [
            row.get("source_title", ""),
            row.get("source_place_text", ""),
            row.get("source_creator", ""),
            row.get("source_collection", ""),
        ]
    )
    tests = [
        ("United States", ["united states", "american", "new york", "broome street", "u.s."], {"regionIds": ["REG003"], "geoIds": []}),
        ("France", ["france", "french", "paris", "delâtre", "lachaise", "jacquin", "rochoux", "meryon"], {"regionIds": ["REG001"], "geoIds": ["GEO005"]}),
        ("United Kingdom", ["britain", "british", "england", "london", "scotland", "glasgow"], {"regionIds": ["REG001"], "geoIds": ["GEO003"]}),
        ("Germany", ["germany", "german", "munich", "berlin"], {"regionIds": ["REG001"], "geoIds": ["GEO006"]}),
        ("Belgium", ["belgium", "belgian", "ghent"], {"regionIds": ["REG001"], "geoIds": []}),
        ("Italy", ["italy", "italian", "florence"], {"regionIds": ["REG001"], "geoIds": []}),
        ("Brazil", ["brazil", "brazilian"], {"regionIds": ["REG004"], "geoIds": []}),
        ("Russia", ["russia", "russian", "st. petersburg", "petersburg"], {"regionIds": ["REG002"], "geoIds": []}),
        ("Uruguay", ["uruguay"], {"regionIds": ["REG004"], "geoIds": []}),
        ("Netherlands", ["netherlands", "dutch"], {"regionIds": ["REG001"], "geoIds": ["GEO009"]}),
        ("Japan", ["japan", "japanese"], {"regionIds": ["REG005", "REG007"], "geoIds": ["GEO035"]}),
        ("Mexico", ["mexico", "mexican"], {"regionIds": ["REG004"], "geoIds": []}),
        ("Cuba / transnational", ["cuba", "cuban", "ospaaal", "tricontinental"], {"regionIds": ["REG004"], "geoIds": []}),
        ("Palestine / transnational", ["palestine", "palestinian", "intifada"], {"regionIds": ["REG013"], "geoIds": []}),
        ("South Africa / Botswana", ["south africa", "south african", "botswana", "medu", "anti-apartheid", "apartheid"], {"regionIds": ["REG014"], "geoIds": []}),
        ("Australia / Indigenous", ["australia", "australian", "aboriginal", "naidoc", "indigenous"], {"regionIds": ["REG015"], "geoIds": []}),
        ("Latin America", ["latin america", "latin american"], {"regionIds": ["REG004"], "geoIds": []}),
        ("Poland", ["poland", "polish", "warsaw"], {"regionIds": ["REG002"], "geoIds": []}),
        ("Switzerland", ["switzerland", "swiss", "zurich", "basel"], {"regionIds": ["REG001"], "geoIds": []}),
        ("India", ["india", "indian", "ahmedabad"], {"regionIds": ["REG012"], "geoIds": []}),
        ("China / Hong Kong", ["china", "chinese", "hong kong", "shanghai"], {"regionIds": ["REG008"], "geoIds": []}),
    ]
    blob_l = blob.lower()
    for label, terms, refs in tests:
        if any(term in blob_l for term in terms):
            return folder_id("region", label), label, refs
    return folder_id("region", "Unresolved region"), "Unresolved region", {"regionIds": [], "geoIds": []}


def medium_for(row: dict[str, str]) -> tuple[str, str]:
    blob = " ".join([row.get("source_title", ""), row.get("source_object_type", ""), row.get("source_medium", "")]).lower()
    if "trade card" in blob:
        return folder_id("medium", "Trade card"), "Trade card"
    if "sheet music" in blob:
        return folder_id("medium", "Sheet music cover"), "Sheet music cover"
    if "poster" in blob:
        return folder_id("medium", "Poster"), "Poster"
    if "catalog" in blob or "catalogue" in blob:
        return folder_id("medium", "Catalogue"), "Catalogue"
    if "chromolithograph" in blob or "lithograph" in blob:
        return folder_id("medium", "Lithographic print"), "Lithographic print"
    if "advert" in blob:
        return folder_id("medium", "Advertisement"), "Advertisement"
    if "photomontage" in blob:
        return folder_id("medium", "Photomontage"), "Photomontage"
    if "book" in blob or "cover" in blob or "publication" in blob:
        return folder_id("medium", "Publication design"), "Publication design"
    if "identity" in blob or "logo" in blob:
        return folder_id("medium", "Corporate identity record"), "Corporate identity record"
    return folder_id("medium", "Graphic design object record"), "Graphic design object record"


def theme_for(row: dict[str, str]) -> tuple[str, str]:
    blob = " ".join(
        [
            row.get("source_title", ""),
            row.get("source_object_type", ""),
            row.get("source_medium", ""),
            row.get("source_description", ""),
            row.get("source_subjects", ""),
        ]
    ).lower()
    tests = [
        ("World War and public-information graphics", ["war", "propaganda", "victory", "liberty loan", "army", "navy", "air force"]),
        ("New Deal and civic poster programs", ["wpa", "works progress", "federal art", "national parks"]),
        ("Travel and transport poster culture", ["travel", "transport", "railway", "airline", "london transport", "bus", "underground"]),
        ("Corporate identity and design systems", ["identity", "corporate", "logo", "trademark", "brand"]),
        ("Modern typography and layout", ["typography", "type", "letter", "layout", "graphic design"]),
        ("Postwar exhibition and cultural posters", ["exhibition", "museum", "gallery", "festival", "biennial"]),
        ("Public health and social communication", ["health", "safety", "public information", "civil rights"]),
    ]
    for label, terms in tests:
        if any(term in blob for term in terms):
            return folder_id("theme", label), label
    return folder_id("theme", "Midcentury modern graphic communication"), "Midcentury modern graphic communication"


MOVEMENT_RULES = [
    {
        "id": "RM075",
        "label": "Bauhaus / New Typography first-ingest network",
        "terms": ["bauhaus", "new typography", "neue typographie", "herbert bayer", "jan tschichold", "detmold wald"],
    },
    {
        "id": "RM076",
        "label": "Polish Poster School first-ingest scope",
        "terms": ["polish poster", "polska szkola plakatu", "polska szkoła plakatu", "warsaw poster", "plakat polski"],
    },
    {
        "id": "RM078",
        "label": "Taller de Grafica Popular first-ingest scope",
        "terms": ["taller de grafica popular", "taller de gráfica popular", "leopoldo méndez", "leopoldo mendez", "tgp mexico", "corrido de diego rivera"],
    },
    {
        "id": "RM079",
        "label": "Brigadas Ramona Parra first-ingest scope",
        "terms": ["brigada ramona parra", "brigadas ramona parra", "ramona parra", "chilean mural", "chile mural"],
    },
    {
        "id": "RM080",
        "label": "Japanese postwar design institution network",
        "terms": ["world design conference", "wodeco", "nippon design center", "japan advertising artists club", "japanese poster", "japanese graphic design"],
    },
    {
        "id": "RM081",
        "label": "Shanghai Manhua and yuefenpai commercial print",
        "terms": ["shanghai manhua", "shanghai sketch", "上海漫畫", "上海漫画", "月份牌", "yuefenpai", "calendar poster shanghai"],
    },
    {
        "id": "RM082",
        "label": "Minjung and democratization poster culture",
        "terms": ["minjung", "민중미술", "democratization poster", "gwangju", "광주", "korean democratization"],
    },
    {
        "id": "RM083",
        "label": "Singapore multilingual poster and logotype systems",
        "terms": ["singapore campaign", "singapore poster", "housing and development board", "national library board singapore", "newspapersg"],
    },
    {
        "id": "RM084",
        "label": "NID development-communication and modern design formation",
        "terms": ["national institute of design", "nid ahmedabad", "eames india", "development communication", "ahmedabad design"],
    },
    {
        "id": "RM085",
        "label": "Iranian modern poster and graphic-design formation",
        "terms": ["morteza momayyez", "iranian poster", "iranian graphic", "tehran poster", "persian poster"],
    },
    {
        "id": "RM086",
        "label": "Medu Art Ensemble and anti-apartheid poster movement",
        "terms": ["medu art ensemble", "culture and resistance", "anti-apartheid", "apartheid", "thami mnyele", "anc poster"],
    },
    {
        "id": "RM087",
        "label": "Aboriginal land-rights and NAIDOC poster cultures",
        "terms": ["naidoc", "aboriginal land rights", "indigenous poster", "australia indigenous"],
    },
    {
        "id": "RM088",
        "label": "Gran Fury and ACT UP activist graphics",
        "terms": ["gran fury", "act up", "aids activist", "silence = death", "queer counterpublic"],
    },
    {
        "id": "RM089",
        "label": "Early web, CSS, and homepage/interface formation",
        "terms": ["geocities", "css1", "info.cern.ch", "world wide web", "early web"],
    },
    {
        "id": "RM090",
        "label": "OSPAAAL and Tricontinental solidarity graphics",
        "terms": ["ospaaal", "tricontinental", "solidarity with", "chetricontinental"],
    },
    {
        "id": "RM091",
        "label": "Palestinian liberation and solidarity poster culture",
        "terms": ["palestinian poster", "palestinian women", "palestinian communist", "palestine poster", "intifada"],
    },
]


def movement_for(row: dict[str, str]) -> tuple[list[str], list[dict[str, str]]]:
    """Return high-confidence movement folders only.

    Movement membership is intentionally conservative: a row must contain a
    direct movement/formation name, a named institution/collective, or a
    distinctive source phrase. Broad visual resemblance is not enough.
    """
    blob = " ".join(
        [
            row.get("source_title", ""),
            row.get("source_creator", ""),
            row.get("source_place_text", ""),
            row.get("source_object_type", ""),
            row.get("source_medium", ""),
            row.get("source_collection", ""),
            row.get("source_description", ""),
            row.get("source_notes", ""),
            row.get("source_subjects", ""),
            row.get("historical_context_note", ""),
            row.get("classification_rationale", ""),
        ]
    ).lower()
    ids: list[str] = []
    refs: list[dict[str, str]] = []
    for rule in MOVEMENT_RULES:
        if not any(term in blob for term in rule["terms"]):
            continue
        if rule["id"] in ids:
            continue
        ids.append(rule["id"])
        refs.append({"folderId": folder_id("movement", rule["label"]), "type": "movement", "title": rule["label"]})
    return ids, refs


MAIN_SHEET_THRESHOLD = 75
SUPPORT_PACKET_THRESHOLD = 55
MERGE_CANDIDATE_THRESHOLD = 40
CARD_THRESHOLD = 20
MAIN_SHEET_MIN_SOURCE_TEXT = 80


def source_reading_text_len(row: dict[str, str]) -> int:
    return len(
        " ".join(
            [
                row.get("source_description", ""),
                row.get("source_notes", ""),
                row.get("ocr_or_excerpt", ""),
            ]
        ).strip()
    )


def context_text_len(row: dict[str, str]) -> int:
    return len(
        " ".join(
            [
                row.get("editorial_summary", ""),
                row.get("historical_context_note", ""),
            ]
        ).strip()
    )


def reading_text_len(row: dict[str, str]) -> int:
    return source_reading_text_len(row)


def surface_score(row: dict[str, str]) -> int:
    """Score publication readiness as a true 0-100 gate.

    Earlier versions started every record at 20 points, which made bookmark-
    level records impossible and promoted thin metadata rows into sheets. This
    score gives most weight to source/citation integrity, rights/image evidence,
    and grounded source text.
    """
    score = 0

    # Source identity and provenance: 20
    if row.get("source_title"):
        score += 5
    if row.get("source_identifier") or row.get("capture_id"):
        score += 4
    if row.get("source_record_url"):
        score += 5
    if row.get("source_name") or row.get("source_id"):
        score += 3
    if row.get("raw_json_path") and row.get("access_date"):
        score += 3

    # Historical filing evidence: 20
    if row.get("date_start") or row.get("date_end"):
        score += 4
    if row.get("source_date_text"):
        score += 3
    if row.get("source_place_text"):
        score += 4
    if row.get("source_object_type") or row.get("source_medium"):
        score += 4
    if row.get("source_subjects"):
        score += 5

    # Rights and image evidence: 20
    img = row.get("image_presence_code") or ""
    if img:
        score += 3
    if img in {"IMG01", "IMG02", "IMG03"}:
        score += 7
    if row.get("rights_basis") or row.get("source_rights_text"):
        score += 5
    if row.get("image_state_review_note") or row.get("image_state_evaluation"):
        score += 5

    # Grounded source reading material: 30
    text_len = source_reading_text_len(row)
    if text_len >= 500:
        score += 30
    elif text_len >= 250:
        score += 24
    elif text_len >= 180:
        score += 18
    elif text_len >= 80:
        score += 12
    elif text_len >= 40:
        score += 6
    elif text_len > 0:
        score += 3

    # Context and relation support: 10
    context_len = context_text_len(row)
    if context_len >= 180:
        score += 5
    elif context_len >= 80:
        score += 3
    if row.get("source_creator"):
        score += 2
    if row.get("source_collection"):
        score += 1
    if row.get("classification_rationale"):
        score += 2

    return min(score, 100)


def surface_disposition(row: dict[str, str], score: int) -> str:
    img = row.get("image_presence_code", "IMG00")
    source_text_len = source_reading_text_len(row)
    source_blob = " ".join(
        [
            row.get("source_object_type", ""),
            row.get("source_medium", ""),
            row.get("direction_name", ""),
            row.get("classification_rationale", ""),
        ]
    ).lower()
    if "source registry/context record" in source_blob or "source-registry" in source_blob:
        if score >= SUPPORT_PACKET_THRESHOLD:
            return "support_packet_appendix_text"
        if score >= MERGE_CANDIDATE_THRESHOLD:
            return "merge_candidate_support_packet"
        if score >= CARD_THRESHOLD:
            return "card"
        return "bookmark_candidate"
    if score >= MAIN_SHEET_THRESHOLD and source_text_len >= MAIN_SHEET_MIN_SOURCE_TEXT:
        return "main_sheet"
    if score >= MAIN_SHEET_THRESHOLD and img in {"IMG01", "IMG02", "IMG03"}:
        return "thin_visual_support_packet"
    if score >= SUPPORT_PACKET_THRESHOLD:
        return "support_packet_appendix_text"
    if score >= MERGE_CANDIDATE_THRESHOLD:
        return "merge_candidate_support_packet"
    if score >= CARD_THRESHOLD:
        return "card"
    return "bookmark_candidate"


def surface_type_and_template(row: dict[str, str], score: int) -> tuple[str, str, str | None]:
    img = row.get("image_presence_code", "IMG00")
    disposition = surface_disposition(row, score)

    if disposition == "bookmark_candidate":
        return "fallback_stub", "stub.fallback.v0", "bookmark_candidate"
    if disposition == "card":
        return "card", "card.sparse.v0", "card"
    if disposition == "merge_candidate_support_packet":
        return "card", "card.sparse.v0", "merge_candidate"
    if disposition in {"support_packet_appendix_text", "thin_visual_support_packet"}:
        if img == "IMG04":
            return "sheet", "sheet.text.v0", "support_packet"
        if img == "IMG00":
            return "sheet", "sheet.img00.v0", "support_packet"
        return "sheet", "sheet.main.v0", "support_packet"

    if img == "IMG04":
        return "sheet", "sheet.text.v0", "text"
    if img == "IMG00":
        return "sheet", "sheet.img00.v0", "main"
    return "sheet", "sheet.main.v0", "plate"


def table(kind: str, rows: list[tuple[str, str]]) -> dict[str, Any]:
    return {"kind": kind, "rows": [[label, value or "Unknown"] for label, value in rows]}


def build_surface(row: dict[str, str], index: int) -> dict[str, Any]:
    capture_id = row["capture_id"]
    score = surface_score(row)
    disposition = surface_disposition(row, score)
    surface_type, template_id, layout_hint = surface_type_and_template(row, score)
    image_state = row.get("image_presence_code") or "IMG00"
    has_frame = image_state != "IMG04"
    year_text = row.get("source_date_text") or "undated"
    era = row.get("date_end") or row.get("date_start") or first_year(year_text) or "undated"
    seq = f"STAGED-MC-{index:04d}"
    tier = "M" if surface_type == "sheet" else "S"
    region_id, region_label, region_refs = region_for(row)
    medium_id, medium_label = medium_for(row)
    theme_id, theme_label = theme_for(row)
    movement_ids, movement_folders = movement_for(row)
    folders = [
        {"folderId": region_id, "type": "region", "title": region_label},
        {"folderId": theme_id, "type": "theme", "title": theme_label},
        {"folderId": medium_id, "type": "medium", "title": medium_label},
    ]
    folders.extend(movement_folders)
    rights_reviewed = row.get("rights_review_required") == "false" or image_state == "IMG03"
    date_known = bool(row.get("date_start") or row.get("source_date_text"))
    classification_known = region_label != "Unresolved region" or bool(medium_label)
    image_url = row.get("image_url_detected") if image_state in {"IMG01", "IMG02", "IMG03"} else None
    surface = {
        "surfaceId": f"SURF-{capture_id}",
        "sourceRecordId": capture_id,
        "surfaceType": surface_type,
        "templateId": template_id,
        "provisionalDisplayNumber": f"GD / {era} / {seq} / {tier}-p01",
        "seqLabel": seq,
        "historicalNodeIds": ["HN009", "HN010", "HN011", "HN014"],
        "movementIds": movement_ids,
        "title": row.get("source_title") or f"Untitled midcentury graphic design record {index}",
        "creator": row.get("source_creator") or "Unknown",
        "dateText": year_text,
        "dateStart": int(row["date_start"]) if row.get("date_start") else None,
        "dateEnd": int(row["date_end"]) if row.get("date_end") else None,
        "placeText": row.get("source_place_text") or region_label,
        "objectType": row.get("source_object_type") or medium_label,
        "medium": row.get("source_medium") or medium_label,
        "sourceName": row.get("source_name") or "Unknown source",
        "sourceUrl": row.get("source_record_url") or row.get("source_api_url"),
        "accessDate": row.get("access_date") or ACCESS_DATE,
        "descriptionSummary": row.get("source_description") or row.get("source_notes") or "",
        "sourceDescription": row.get("source_description") or "",
        "sourceNotes": row.get("source_notes") or "",
        "sourceSubjects": row.get("source_subjects") or "",
        "readingTextLength": reading_text_len(row),
        "sourceReadingTextLength": source_reading_text_len(row),
        "contextTextLength": context_text_len(row),
        "completenessScore": score,
        "surfaceDisposition": disposition,
        "publicationRole": disposition,
        "publicationGate": {
            "mainSheetThreshold": MAIN_SHEET_THRESHOLD,
            "supportPacketThreshold": SUPPORT_PACKET_THRESHOLD,
            "mergeCandidateThreshold": MERGE_CANDIDATE_THRESHOLD,
            "cardThreshold": CARD_THRESHOLD,
            "mainSheetMinSourceText": MAIN_SHEET_MIN_SOURCE_TEXT,
        },
        "reviewGates": {
            "sourceUrl": bool(row.get("source_record_url")),
            "rightsReviewed": rights_reviewed,
            "dateKnown": date_known,
            "classificationKnown": classification_known,
        },
        "image": {
            "state": image_state,
            "hasImageFrame": has_frame,
            "url": image_url or None,
            "credit": row.get("source_name") if image_url else None,
            "licenseLabel": row.get("image_state_review_note") or row.get("rights_basis") or "",
        },
        "rights": {
            "state": "open_candidate" if image_state == "IMG03" else ("thumbnail_candidate" if image_state == "IMG01" else ("source_viewer_candidate" if image_state == "IMG02" else "rights_review_required")),
            "displayPolicy": row.get("image_frame_behavior") or "empty_rights_frame",
            "label": row.get("image_state_evaluation") or "Rights state not reviewed.",
        },
        "folders": folders,
        "layoutHint": layout_hint,
        "tables": [
            table(
                "SOURCE",
                [
                    ("Source ID", row.get("source_id", "")),
                    ("Source name", row.get("source_name", "")),
                    ("Source identifier", row.get("source_identifier", "")),
                    ("Source title", row.get("source_title", "")),
                    ("Source creator", row.get("source_creator", "")),
                    ("Source date", row.get("source_date_text", "")),
                    ("Source place", row.get("source_place_text", "")),
                    ("Source collection", row.get("source_collection", "")),
                    ("Source description", row.get("source_description", "")),
                    ("Source notes", row.get("source_notes", "")),
                    ("Source URL", row.get("source_record_url", "")),
                ],
            ),
            table(
                "NORMALIZED",
                [
                    ("Date text", year_text),
                    ("Date start", row.get("date_start", "")),
                    ("Date end", row.get("date_end", "")),
                    ("Object type", row.get("source_object_type", "") or medium_label),
                    ("Medium", row.get("source_medium", "") or medium_label),
                    ("Region", region_label),
                    ("Description summary", row.get("source_description", "") or row.get("source_notes", "")),
                ],
            ),
            table(
                "RIGHTS",
                [
                    ("Image state", image_state),
                    ("Display policy", row.get("image_frame_behavior", "")),
                    ("Rights basis", row.get("rights_basis", "")),
                    ("Local copy permitted", row.get("local_copy_permitted", "false")),
                    ("Rights review required", row.get("rights_review_required", "true")),
                ],
            ),
            table(
                "CLASSIFICATION",
                [
                    ("Region folder", region_label),
                    ("Theme folder", theme_label),
                    ("Medium folder", medium_label),
                    ("Movement refs", "; ".join(movement_ids) or "NONE"),
                    ("Historical node refs", "HN009; HN010; HN011; HN014"),
                    ("Reading text length", str(reading_text_len(row))),
                    ("Classification basis", "Midcentury 1930-1970 capture rule"),
                ],
            ),
            table(
                "RELATIONS",
                [
                    ("held_by", row.get("source_name", "")),
                    ("classified_as", medium_label),
                    ("associated_with", theme_label),
                    ("movement_or_formation", "; ".join(movement_ids) or "NONE"),
                ],
            ),
            table(
                "CITATIONS",
                [
                    ("Source URL", row.get("source_record_url", "")),
                    ("Access date", row.get("access_date", "")),
                    ("Raw payload", row.get("raw_json_path", "")),
                ],
            ),
        ],
    }
    # Current frontend types do not require authorityRefs, but folder generation uses them.
    surface["_authorityRefs"] = {
        "historicalNodeIds": ["HN009", "HN010", "HN011", "HN014"],
        "movementIds": movement_ids,
        "regionalMovementIds": movement_ids,
        "regionIds": region_refs.get("regionIds", []),
        "geoIds": region_refs.get("geoIds", []),
        "mediaIds": [],
        "themeKeys": [slug(theme_label)],
        "sourceIds": [row.get("source_id", "")],
    }
    return surface


def normalized_title(value: str) -> str:
    cleaned = clean_text(value, max_chars=180).lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def compound_group_key(surface: dict[str, Any]) -> tuple[str, str] | None:
    title = normalized_title(surface.get("title", ""))
    source = surface.get("sourceName", "")
    if title == "huntley & palmers trade card" and source == "V&A Collections API":
        return ("huntley-palmers-trade-cards", "Huntley & Palmers trade-card series")
    if source == "V&A Collections API" and (
        title.startswith("chromolithograph, copy after") or title.startswith("copy after ")
    ):
        return ("arundel-society-chromolithograph-copies", "Arundel Society chromolithograph copy series")
    return None


def compact_list(values: list[str], *, max_items: int = 5) -> str:
    seen: list[str] = []
    for value in values:
        value = value.strip()
        if value and value not in seen:
            seen.append(value)
    if len(seen) <= max_items:
        return "; ".join(seen)
    return "; ".join(seen[:max_items]) + f"; +{len(seen) - max_items} more"


def folder_sort_key(ref: dict[str, str]) -> tuple[int, str]:
    order = {"region": 0, "theme": 1, "medium": 2, "movement": 3}
    return (order.get(ref.get("type", ""), 99), ref.get("title", ""))


def union_folders(children: list[dict[str, Any]]) -> list[dict[str, str]]:
    refs: dict[str, dict[str, str]] = {}
    for child in children:
        for ref in child.get("folders", []):
            refs.setdefault(ref["folderId"], ref)
    return sorted(refs.values(), key=folder_sort_key)


def image_state_counts(children: list[dict[str, Any]]) -> str:
    counts = Counter(child.get("image", {}).get("state", "IMG00") for child in children)
    return "; ".join(f"{state}: {count}" for state, count in sorted(counts.items()))


def date_span(children: list[dict[str, Any]]) -> tuple[int | None, int | None, str]:
    starts = [child["dateStart"] for child in children if child.get("dateStart") is not None]
    ends = [
        child.get("dateEnd") if child.get("dateEnd") is not None else child.get("dateStart")
        for child in children
        if child.get("dateEnd") is not None or child.get("dateStart") is not None
    ]
    start = min(starts) if starts else None
    end = max(ends) if ends else None
    if start and end and start != end:
        return start, end, f"{start}-{end}"
    if start:
        return start, end, str(start)
    return None, None, "undated"


def child_note(surface: dict[str, Any]) -> str:
    note = surface.get("descriptionSummary") or surface.get("sourceNotes") or surface.get("medium") or surface.get("objectType")
    return clean_text(note, max_chars=170) or "Member source record; see source link."


def build_compound_surface(key: str, title: str, children: list[dict[str, Any]], index: int) -> dict[str, Any]:
    children = sorted(children, key=lambda s: (s.get("dateStart") or 9999, s.get("title", ""), s.get("surfaceId", "")))
    date_start, date_end, date_text = date_span(children)
    era = date_start or "undated"
    seq = f"STAGED-MC-C{index:03d}"
    source_names = compact_list([child.get("sourceName", "") for child in children])
    media = compact_list([child.get("medium", "") or child.get("objectType", "") for child in children])
    object_types = compact_list([child.get("objectType", "") for child in children])
    places = compact_list([child.get("placeText", "") for child in children])
    source_urls = [child.get("sourceUrl", "") for child in children if child.get("sourceUrl")]
    member_ids = [child.get("sourceRecordId", "") for child in children]
    folders = union_folders(children)
    folder_labels = ", ".join(ref["title"] for ref in folders)
    historical_node_ids = sorted({node for child in children for node in child.get("historicalNodeIds", [])})
    movement_ids = sorted({node for child in children for node in child.get("movementIds", [])})
    description = (
        f"Compound sheet generated from {len(children)} atomic source records that share a repeated title "
        "or documented production pattern. The member list preserves individual source links, dates, and image states."
    )
    child_rows = [
        {
            "title": child.get("title", "Untitled member"),
            "dateText": child.get("dateText", "undated"),
            "sourceName": child.get("sourceName", "Unknown source"),
            "sourceUrl": child.get("sourceUrl", ""),
            "imageState": child.get("image", {}).get("state", "IMG00"),
            "note": child_note(child),
        }
        for child in children
    ]
    return {
        "surfaceId": f"SURF-COMPOUND-{key.upper()}",
        "sourceRecordId": f"COMPOUND-{key.upper()}",
        "surfaceType": "sheet",
        "templateId": "sheet.compound.v0",
        "provisionalDisplayNumber": f"GD / {era} / {seq} / L-p01",
        "seqLabel": seq,
        "historicalNodeIds": historical_node_ids,
        "movementIds": movement_ids,
        "title": title,
        "creator": "Multiple source records",
        "dateText": date_text,
        "dateStart": date_start,
        "dateEnd": date_end,
        "placeText": places or "Multiple / unresolved",
        "objectType": object_types or "Compound source-record group",
        "medium": media or "Mixed / unresolved",
        "sourceName": source_names or "Multiple sources",
        "sourceUrl": source_urls[0] if source_urls else "",
        "accessDate": ACCESS_DATE,
        "descriptionSummary": description,
        "sourceDescription": description,
        "sourceNotes": f"Grouped member source records: {compact_list(member_ids, max_items=8)}",
        "sourceSubjects": "",
        "completenessScore": min(95, max(child.get("completenessScore", 0) for child in children)),
        "reviewGates": {
            "sourceUrl": bool(source_urls),
            "rightsReviewed": False,
            "dateKnown": date_start is not None,
            "classificationKnown": bool(folders),
        },
        "image": {
            "state": "IMG04",
            "hasImageFrame": False,
            "url": None,
            "credit": None,
            "licenseLabel": "Compound text sheet; member image states remain record-level.",
        },
        "rights": {
            "state": "compound_member_rights",
            "displayPolicy": "no_image_frame",
            "label": "Compound sheet uses no image frame. Each member keeps its own IMG00-IMG04 status and source link.",
        },
        "folders": folders,
        "layoutHint": "compound",
        "compoundChildren": child_rows,
        "tables": [
            table(
                "SOURCE",
                [
                    ("Source group", title),
                    ("Member count", str(len(children))),
                    ("Source names", source_names),
                    ("Representative URL", source_urls[0] if source_urls else ""),
                    ("Member source records", compact_list(member_ids, max_items=8)),
                ],
            ),
            table(
                "NORMALIZED",
                [
                    ("Date span", date_text),
                    ("Object types", object_types),
                    ("Media", media),
                    ("Places", places),
                    ("Grouping rule", key),
                ],
            ),
            table(
                "RIGHTS",
                [
                    ("Compound page image state", "IMG04"),
                    ("Member image states", image_state_counts(children)),
                    ("Display policy", "No image frame on compound sheet; member states shown in list."),
                    ("Local copy permitted", "false"),
                    ("Rights review required", "true"),
                ],
            ),
            table(
                "CLASSIFICATION",
                [
                    ("Folder memberships", folder_labels),
                    ("Historical node refs", "; ".join(historical_node_ids)),
                    ("Movement refs", "; ".join(movement_ids) or "NONE"),
                    ("Classification basis", "Compound grouping over atomic source records"),
                ],
            ),
            table(
                "RELATIONS",
                [
                    ("has_member", compact_list(member_ids, max_items=10)),
                    ("grouped_by", key),
                    ("preserves", "source link; date; image state; source record id"),
                ],
            ),
            table(
                "CITATIONS",
                [
                    ("Source URLs", compact_list(source_urls, max_items=5)),
                    ("Access date", ACCESS_DATE),
                    ("Capture batch", CAPTURE_BATCH_ID),
                ],
            ),
        ],
    }


def collapse_compound_surfaces(surfaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for surface in surfaces:
        key = compound_group_key(surface)
        if key:
            groups[key].append(surface)

    grouped_ids: set[str] = set()
    compounds: list[dict[str, Any]] = []
    compound_index = 1
    for (key, title), children in sorted(groups.items(), key=lambda item: item[0][0]):
        if len(children) < 4:
            continue
        grouped_ids.update(child["surfaceId"] for child in children)
        compounds.append(build_compound_surface(key, title, children, compound_index))
        compound_index += 1

    singles = [surface for surface in surfaces if surface["surfaceId"] not in grouped_ids]
    return sorted(singles + compounds, key=lambda s: (s.get("dateStart") or 9999, s.get("seqLabel", ""), s.get("title", "")))


def build_folders(surfaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for surface in surfaces:
        for ref in surface["folders"]:
            folder = grouped.setdefault(
                ref["folderId"],
                {
                    "folderId": ref["folderId"],
                    "type": ref["type"],
                    "slug": slug(ref["title"]),
                    "title": ref["title"],
                    "dateStart": None,
                    "dateEnd": None,
                    "scopeNote": scope_note(ref["type"], ref["title"]),
                    "surfaceIds": [],
                    "relatedFolderIds": [],
                    "authorityRefs": {},
                },
            )
            folder["surfaceIds"].append(surface["surfaceId"])
            if surface.get("dateStart") is not None:
                folder["dateStart"] = min(folder["dateStart"], surface["dateStart"]) if folder["dateStart"] is not None else surface["dateStart"]
            if surface.get("dateEnd") is not None:
                folder["dateEnd"] = max(folder["dateEnd"], surface["dateEnd"]) if folder["dateEnd"] is not None else surface["dateEnd"]
            elif surface.get("dateStart") is not None:
                folder["dateEnd"] = max(folder["dateEnd"], surface["dateStart"]) if folder["dateEnd"] is not None else surface["dateStart"]
    for folder in grouped.values():
        related = set()
        for sid in folder["surfaceIds"]:
            surface = next(s for s in surfaces if s["surfaceId"] == sid)
            for ref in surface["folders"]:
                if ref["folderId"] != folder["folderId"]:
                    related.add(ref["folderId"])
        folder["relatedFolderIds"] = sorted(related)
    return sorted(grouped.values(), key=lambda f: (["region", "theme", "medium", "movement"].index(f["type"]), f["title"]))


def scope_note(folder_type: str, title: str) -> str:
    if folder_type == "region":
        return f"Midcentury 1930-1970 records associated with {title}."
    if folder_type == "theme":
        return "Midcentury 1930-1970 graphic communication, propaganda, corporate identity, modern typography, transport, public-information, and exhibition records."
    if folder_type == "medium":
        return f"Midcentury 1930-1970 records filed by medium: {title}."
    return f"Movement or formation folder: {title}."


def build_public_payload(rows: list[dict[str, str]]) -> dict[str, Any]:
    atomic_surfaces = [build_surface(row, index) for index, row in enumerate(rows, start=1)]
    surfaces = collapse_compound_surfaces(atomic_surfaces)
    folders = build_folders(surfaces)
    # Remove private helper refs to stay compatible with current frontend shape.
    for surface in surfaces:
        surface.pop("_authorityRefs", None)
    return {
        "meta": {
            "generatedAt": ACCESS_DATE,
            "status": "generated",
            "note": "Generated midcentury 1930-1970 visual-verification payload. Static export; not final publication data.",
        },
        "folderTypes": FOLDER_TYPES,
        "folders": folders,
        "surfaces": surfaces,
    }


def sync_frontend_payload(payload_text: str) -> None:
    paths = [
        ROOT / "frontend" / "src" / "data" / "public_surface_mock_v0.json",
        ROOT / "frontend" / "public" / "data" / "public_surface_mock_v0.json",
    ]
    for path in paths:
        if path.exists():
            path.write_text(payload_text, encoding="utf-8")


def read_existing_rows() -> list[dict[str, str]]:
    with RECORDS_CSV.open(encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_payload(rows: list[dict[str, str]]) -> dict[str, Any]:
    payload = build_public_payload(rows)
    payload_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    SURFACES_JSON.write_text(payload_text, encoding="utf-8")
    sync_frontend_payload(payload_text)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture and generate midcentury 1930-1970 public surfaces.")
    parser.add_argument(
        "--from-csv",
        action="store_true",
        help="Regenerate public surface payload from the existing capture CSV without making network requests.",
    )
    args = parser.parse_args()
    if args.from_csv:
        GENERATED.mkdir(parents=True, exist_ok=True)
        rows = read_existing_rows()
        payload = write_payload(rows)
        print(f"{SURFACES_JSON.relative_to(ROOT)}: {len(payload['surfaces'])} surfaces, {len(payload['folders'])} folders")
        print("regenerated from existing capture CSV")
        return

    sources = read_source_registry()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    raw_refs: dict[str, str] = {}

    for plan in CAPTURE_PLAN:
        source = sources.get(plan["source_name"])
        if not source:
            raise SystemExit(f"source not found in registry: {plan['source_name']}")
        try:
            plan_rows, raw_payloads = ADAPTERS[plan["adapter"]](plan, source)
            written = write_raw(raw_payloads)
            raw_refs.update(written)
            raw_path = next(iter(written.values()), "")
            for row in plan_rows:
                row["raw_json_path"] = raw_path
            rows.extend(plan_rows)
        except Exception as exc:  # noqa: BLE001 - capture log should preserve source errors.
            failures.append(
                {
                    "source_name": plan["source_name"],
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        time.sleep(0.4)

    rows = dedupe_rows(rows)
    rows.sort(key=lambda r: (int(r["date_start"]) if r.get("date_start") else 9999, r.get("source_title", "")))
    rows = rows[:TARGET_COUNT]
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"MC1930R{index:03d}"
        for field in FIELDNAMES:
            row.setdefault(field, "")

    write_records(rows)
    write_summary(rows, failures)
    payload = write_payload(rows)

    image_counts = Counter(row["image_presence_code"] for row in rows)
    print(f"{RECORDS_CSV.relative_to(ROOT)}: {len(rows)} captured rows")
    print(f"{SUMMARY_CSV.relative_to(ROOT)}: summary written")
    print(f"{SURFACES_JSON.relative_to(ROOT)}: {len(payload['surfaces'])} surfaces, {len(payload['folders'])} folders")
    print("image distribution:", dict(sorted(image_counts.items())))
    if failures:
        print("Failures:")
        for failure in failures:
            print(f"- {failure['source_name']}: {failure['error']}")
    if not rows:
        raise SystemExit("no rows captured")


if __name__ == "__main__":
    main()
