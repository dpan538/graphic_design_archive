#!/usr/bin/env python3
"""Protocol-level item capture for underrepresented 1970-2026 sources.

This pass consumes the item capture queue and only promotes records that have
item-level metadata. Failed protocol probes are written to the source summary,
not to the public records CSV, so the archive does not mint thin public sheets
from source-level hopes.
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
RAW_DIR = DATA / "capture_batch_protocol_item_1970_2026_raw"
QUEUE = DATA / "item_capture_queue_v1.csv"
RECORDS_CSV = DATA / "capture_batch_protocol_item_1970_2026_records.csv"
SUMMARY_CSV = DATA / "capture_batch_protocol_item_1970_2026_source_summary.csv"
REPORT = ROOT / "docs" / "capture" / "PROTOCOL_ITEM_CAPTURE_1970_2026.md"

ACCESS_DATE = "2026-06-01"
USER_AGENT = "ModernGDHistory/0.1 protocol-item-capture"
FIELDNAMES = mx.FIELDNAMES

YEAR_START = 1970
YEAR_END = 2026
MAX_ROWS_PER_SOURCE = 5

GRAPHIC_TERMS = (
    "poster",
    "posters",
    "affiche",
    "plakat",
    "plakát",
    "advert",
    "advertising",
    "publicity",
    "graphic",
    "typography",
    "type",
    "print culture",
    "pamphlet",
    "campaign",
    "flyer",
    "ephemera",
    "revista",
    "magazine",
    "design",
)

STRONG_GRAPHIC_TERMS = (
    "poster",
    "posters",
    "affiche",
    "plakat",
    "plakát",
    "pamphlet",
    "flyer",
    "zine",
    "newspaper",
    "magazine",
    "revista",
    "advertisement",
    "advertising",
    "publicity",
    "typography",
    "graphic design",
    "visual communication",
    "print culture",
    "ephemera",
)

TITLE_PROMOTION_TERMS = (
    "poster",
    "posters",
    "affiche",
    "plakat",
    "plakát",
    "pamphlet",
    "flyer",
    "zine",
    "newspaper",
    "magazine",
    "revista",
    "advertisement",
    "advertising",
    "publicity",
    "typography",
    "graphic design",
    "visual communication",
)

DEEP_TEXT_PROMOTION_TERMS = (
    "poster",
    "posters",
    "graphic design",
    "typography",
    "advertising",
    "advertisement",
    "visual communication",
    "print culture",
)


def clean(value: Any, *, max_chars: int = 900) -> str:
    text = html.unescape(re.sub(r"\s+", " ", str(value or "")).strip())
    return text[:max_chars]


def strip_tags(value: str, *, max_chars: int = 900) -> str:
    value = re.sub(r"(?is)<(script|style).*?</\1>", " ", value or "")
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    return clean(value, max_chars=max_chars)


def fetch_bytes(url: str, *, accept: str = "application/json,text/plain,*/*") -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
        },
    )
    with urllib.request.urlopen(req, timeout=35) as response:
        return response.read()


def fetch_json(url: str) -> Any:
    return json.loads(fetch_bytes(url).decode("utf-8", errors="replace"))


def write_raw(name: str, payload: Any) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def years_from_text(value: str) -> list[int]:
    years: list[int] = []
    for match in re.findall(r"\b(18\d{2}|19\d{2}|20[0-2]\d)\b", value or ""):
        year = int(match)
        if 1800 <= year <= 2026:
            years.append(year)
    return years


def terminal_year(value: str) -> int | None:
    years = years_from_text(value)
    return max(years) if years else None


def in_target_period(date_text: str) -> bool:
    year = terminal_year(date_text)
    return year is not None and YEAR_START <= year <= YEAR_END


def relevant_blob(*parts: str) -> bool:
    blob = " ".join(parts).lower()
    return any(term in blob for term in GRAPHIC_TERMS)


def strong_item_relevance(title: str, description: str, subjects: str, query_term: str) -> bool:
    """Conservative promotion gate for text/context sources.

    Generic words such as "design", "communication", and "campaign" are useful
    for source discovery but too broad for public-sheet promotion. A record must
    carry a concrete graphic/print/publication term in the title, description,
    or subject evidence.
    """
    title_l = title.lower()
    desc_l = description.lower()
    subj_l = subjects.lower()
    term_l = query_term.lower()
    if any(term in title_l for term in TITLE_PROMOTION_TERMS):
        return True
    if any(term in subj_l for term in TITLE_PROMOTION_TERMS):
        return True
    if any(term in desc_l for term in DEEP_TEXT_PROMOTION_TERMS):
        return True
    return False


def serial_group_key(row: dict[str, str]) -> str:
    title = row.get("source_title", "").lower()
    source = row.get("source_name", "")
    if "daily trust newspaper" in title:
        return f"{source}|daily trust newspaper"
    if "citizen magazine" in title:
        return f"{source}|citizen magazine"
    if re.search(r"\bwest africa no\.", title):
        return f"{source}|west africa periodical"
    return ""


def consolidate_serial_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    passthrough: list[dict[str, str]] = []
    for row in rows:
        key = serial_group_key(row)
        if not key:
            passthrough.append(row)
            continue
        grouped.setdefault(key, []).append(row)

    for key, members in grouped.items():
        if len(members) == 1:
            passthrough.append(members[0])
            continue
        members = sorted(members, key=lambda r: (r.get("date_start") or "", r.get("source_title") or ""))
        base = dict(members[0])
        if "daily trust" in key:
            title_head = "Daily Trust newspaper issue group"
        elif "citizen magazine" in key:
            title_head = "Citizen magazine issue group"
        else:
            title_head = "West Africa periodical issue group"
        dates = [m.get("source_date_text", "") for m in members if m.get("source_date_text")]
        links = [m.get("source_record_url", "") for m in members if m.get("source_record_url")]
        base["source_identifier"] = key
        base["source_title"] = f"{title_head}, {dates[0]}-{dates[-1]}"
        base["source_date_text"] = f"{dates[0]}-{dates[-1]}" if dates else base.get("source_date_text", "")
        start_years = [int(m["date_start"]) for m in members if m.get("date_start", "").isdigit()]
        end_years = [int(m["date_end"]) for m in members if m.get("date_end", "").isdigit()]
        base["date_start"] = str(min(start_years)) if start_years else base.get("date_start", "")
        base["date_end"] = str(max(end_years)) if end_years else base.get("date_end", "")
        base["source_description"] = clean(
            "Grouped newspaper/periodical source record. Captured issues: "
            + " | ".join(f"{m.get('source_date_text')}: {m.get('source_title')}" for m in members),
            max_chars=1400,
        )
        base["source_notes"] = clean(
            "Source URLs: " + " ; ".join(links),
            max_chars=1200,
        )
        base["editorial_summary"] = clean(
            f"{base['source_title']} groups {len(members)} related issue records from {base['source_name']} so repeated newspaper issues do not render as separate public sheets.",
            max_chars=700,
        )
        base["classification_rationale"] = (
            "Multiple issue-level repository records were grouped by serial title. "
            "The group is intended to support one main record with text/source appendix leaves rather than repeated thin sheets."
        )
        passthrough.append(base)
    return passthrough


def first_meta(metadata: dict[str, Any], *keys: str) -> str:
    for key in keys:
        values = metadata.get(key)
        if isinstance(values, list) and values:
            first = values[0]
            if isinstance(first, dict):
                value = first.get("value") or first.get("@value")
                if value:
                    return clean(value)
            if isinstance(first, str):
                return clean(first)
    return ""


def all_meta(metadata: dict[str, Any], *keys: str, max_chars: int = 900) -> str:
    vals: list[str] = []
    for key in keys:
        values = metadata.get(key)
        if not isinstance(values, list):
            continue
        for item in values:
            if isinstance(item, dict):
                value = item.get("value") or item.get("@value")
            else:
                value = item
            if value:
                vals.append(clean(value, max_chars=240))
    return clean("; ".join(vals), max_chars=max_chars)


def omeka_values(item: dict[str, Any], *keys: str, max_chars: int = 900) -> str:
    vals: list[str] = []
    for key in keys:
        values = item.get(key)
        if not isinstance(values, list):
            continue
        for value in values:
            if isinstance(value, dict):
                vals.append(clean(value.get("@value") or value.get("display_title") or value.get("o:label"), max_chars=260))
            elif value:
                vals.append(clean(value, max_chars=260))
    return clean("; ".join(v for v in vals if v), max_chars=max_chars)


def date_bounds(date_text: str) -> tuple[str, str]:
    years = years_from_text(date_text)
    if not years:
        return "", ""
    return str(min(years)), str(max(years))


def image_fields(code: str, basis: str, image_url: str = "", viewer: str = "", open_image: bool = False) -> dict[str, str]:
    return mc.image_fields(
        code,
        basis,
        image_url=image_url,
        viewer=viewer or image_url,
        confidence="high" if image_url else "medium",
        rights_review_required=not open_image,
        local_copy_permitted=False,
        note="Protocol capture keeps images source-hosted unless the item-level rights row explicitly permits open display.",
    )


def row_defaults(row: dict[str, str]) -> dict[str, str]:
    row["image_expectation"] = "not_expected" if row.get("image_presence_code") == "IMG04" else "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["source_description_raw"] = row.get("source_description", "")
    row["ocr_or_excerpt"] = row.get("source_description") or row.get("source_notes") or row.get("source_subjects", "")
    row.setdefault("editorial_summary", row.get("source_description", ""))
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def existing_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in DATA.glob("capture_batch_*_records.csv"):
        if path == RECORDS_CSV or not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                keys.add((row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", "")))
    return keys


def dspace_search_url(base: str, query: str, size: int) -> str:
    base = base.rstrip("/")
    params = urllib.parse.urlencode({"query": query, "size": str(size)})
    return f"{base}/server/api/discover/search/objects?{params}"


def dspace_records(queue: dict[str, str], seen: set[tuple[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    base = queue["source_url"].rstrip("/")
    terms = [term.strip() for term in queue["first_query_terms"].split(";") if term.strip()]
    for term in terms[:4]:
        api_url = dspace_search_url(base, term, 8)
        try:
            payload = fetch_json(api_url)
        except Exception as exc:
            failures.append({"source_name": queue["source_name"], "adapter": "dspace", "term": term, "status": f"failed:{type(exc).__name__}", "note": str(exc)[:180]})
            continue
        raw_path = write_raw(f"{queue['candidate_id']}_dspace_{re.sub(r'[^a-z0-9]+', '_', term.lower())}.json", payload)
        objects = (((payload.get("_embedded") or {}).get("searchResult") or {}).get("_embedded") or {}).get("objects") or []
        for obj in objects:
            item = ((obj.get("_embedded") or {}).get("indexableObject") or {})
            if not item:
                link = ((obj.get("_links") or {}).get("indexableObject") or {}).get("href")
                if link:
                    try:
                        item = fetch_json(link)
                    except Exception:
                        item = {}
            metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            title = clean(item.get("name") or first_meta(metadata, "dc.title", "dcterms.title"))
            description = all_meta(metadata, "dc.description.abstract", "dc.description", "dcterms.description", max_chars=1400)
            subjects = all_meta(metadata, "dc.subject", "dcterms.subject", max_chars=900)
            date_text = first_meta(metadata, "dc.date.issued", "dcterms.issued", "dc.date", "dcterms.date")
            if (
                not title
                or not in_target_period(date_text)
                or not relevant_blob(title, description, subjects, term)
                or not strong_item_relevance(title, description, subjects, term)
            ):
                continue
            identifier = clean(item.get("uuid") or item.get("id") or item.get("handle") or title)
            key = (queue["source_name"], identifier)
            if key in seen:
                continue
            seen.add(key)
            start, end = date_bounds(date_text)
            source_url = f"{base}/handle/{item.get('handle')}" if item.get("handle") else clean(((item.get("_links") or {}).get("self") or {}).get("href") or api_url)
            creator = all_meta(metadata, "dc.contributor.author", "dc.creator", "dcterms.creator", max_chars=300)
            rights_text = all_meta(metadata, "dc.rights", "dc.rights.uri", "dcterms.rights", max_chars=500)
            rights = image_fields(
                "IMG04",
                rights_text or "DSpace metadata/text record; no item-level image display evidence captured.",
                viewer=source_url,
            )
            hit_highlights = obj.get("hitHighlights") if isinstance(obj.get("hitHighlights"), dict) else {}
            row = row_defaults(
                {
                    "capture_id": "",
                    "direction_id": "PIC-DS",
                    "direction_name": "protocol_item_capture_dspace_oai_1970_2026",
                    "source_id": queue["candidate_id"],
                    "source_name": queue["source_name"],
                    "source_api_url": api_url,
                    "capture_status": "captured",
                    "source_identifier": identifier,
                    "source_record_url": source_url,
                    "source_title": title,
                    "source_creator": creator,
                    "source_date_text": date_text,
                    "date_start": start,
                    "date_end": end,
                    "source_place_text": queue["country_or_region"] or queue["macro_region"],
                    "source_object_type": "repository text record / graphic communication context",
                    "source_medium": all_meta(metadata, "dc.type", "dcterms.type", max_chars=260) or "text / repository item",
                    "source_collection": queue["source_name"],
                    "source_description": description,
                    "source_notes": strip_tags(" ".join(hit_highlights.get("dc.description.abstract", [])), max_chars=900),
                    "source_subjects": subjects,
                    "source_rights_text": rights_text,
                    "rights_uri": first_meta(metadata, "dc.rights.uri"),
                    "raw_json_path": raw_path,
                    "access_date": ACCESS_DATE,
                    **rights,
                    "editorial_summary": clean(f"{title} is a source-level text/context record from {queue['source_name']}. {description}", max_chars=700),
                    "historical_context_note": (
                        f"Protocol-source record for {queue['macro_region']}. This source adds non-museum evidence for graphic communication, print culture, public campaign, or design-study context."
                    ),
                    "classification_rationale": (
                        "Captured from a DSpace-style repository search. It is retained as text/context evidence unless an item-level image and rights statement are later verified."
                    ),
                    "uncertainty_note": "Image evidence was not promoted from repository bitstreams in this pass.",
                    "citation_basis": f"{queue['source_name']}. {title}. {source_url}. Accessed {ACCESS_DATE}.",
                }
            )
            rows.append(row)
            if len(rows) >= MAX_ROWS_PER_SOURCE:
                return rows, failures
    return rows, failures


def omeka_search_url(base: str, query: str, size: int) -> str:
    base = base.rstrip("/")
    params = urllib.parse.urlencode({"fulltext_search": query, "per_page": str(size)})
    return f"{base}/api/items?{params}"


def omeka_records(queue: dict[str, str], seen: set[tuple[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    base = queue["source_url"].rstrip("/")
    terms = [term.strip() for term in queue["first_query_terms"].split(";") if term.strip()]
    for term in terms[:5]:
        api_url = omeka_search_url(base, term, 8)
        try:
            payload = fetch_json(api_url)
        except Exception as exc:
            failures.append({"source_name": queue["source_name"], "adapter": "omeka", "term": term, "status": f"failed:{type(exc).__name__}", "note": str(exc)[:180]})
            continue
        raw_path = write_raw(f"{queue['candidate_id']}_omeka_{re.sub(r'[^a-z0-9]+', '_', term.lower())}.json", payload)
        if not isinstance(payload, list):
            failures.append({"source_name": queue["source_name"], "adapter": "omeka", "term": term, "status": "unexpected_payload", "note": "Omeka endpoint did not return a list"})
            continue
        for item in payload:
            title = clean(item.get("o:title") or omeka_values(item, "dcterms:title"))
            description = omeka_values(item, "dcterms:description", "schema:description", "bibo:abstract", max_chars=1400)
            subjects = omeka_values(item, "dcterms:subject", "schema:about", max_chars=900)
            date_text = omeka_values(item, "dcterms:created", "dcterms:date", "schema:dateCreated", max_chars=120)
            if (
                not title
                or not in_target_period(date_text)
                or not relevant_blob(title, description, subjects, term)
                or not strong_item_relevance(title, description, subjects, term)
            ):
                continue
            identifier = str(item.get("o:id") or item.get("@id") or title)
            key = (queue["source_name"], identifier)
            if key in seen:
                continue
            seen.add(key)
            start, end = date_bounds(date_text)
            thumb = ""
            thumbs = item.get("thumbnail_display_urls")
            if isinstance(thumbs, dict):
                thumb = clean(thumbs.get("large") or thumbs.get("medium") or thumbs.get("square"))
            source_url = clean(item.get("@id") or api_url)
            rights_text = omeka_values(item, "dcterms:rights", "xhtml:license", "cc:license", max_chars=500)
            image_code = "IMG02" if thumb else "IMG04"
            rights = image_fields(
                image_code,
                rights_text or "Omeka public item metadata; image remains source-hosted unless explicit license is verified.",
                image_url=thumb,
                viewer=source_url,
            )
            row = row_defaults(
                {
                    "capture_id": "",
                    "direction_id": "PIC-OM",
                    "direction_name": "protocol_item_capture_omeka_1970_2026",
                    "source_id": queue["candidate_id"],
                    "source_name": queue["source_name"],
                    "source_api_url": api_url,
                    "capture_status": "captured",
                    "source_identifier": identifier,
                    "source_record_url": source_url,
                    "source_title": title,
                    "source_creator": omeka_values(item, "dcterms:creator", "schema:creator", max_chars=300),
                    "source_date_text": date_text,
                    "date_start": start,
                    "date_end": end,
                    "source_place_text": omeka_values(item, "dcterms:spatial", "schema:spatial", "schema:recordedAt", max_chars=260) or queue["country_or_region"] or queue["macro_region"],
                    "source_object_type": omeka_values(item, "dcterms:type", max_chars=260) or "Omeka archive item",
                    "source_medium": omeka_values(item, "dcterms:format", "dcterms:medium", max_chars=260) or "digital collection item",
                    "source_collection": queue["source_name"],
                    "source_description": description,
                    "source_notes": omeka_values(item, "dcterms:bibliographicCitation", "dcterms:source", max_chars=900),
                    "source_subjects": subjects,
                    "source_rights_text": rights_text,
                    "rights_uri": omeka_values(item, "cc:license", max_chars=260),
                    "raw_json_path": raw_path,
                    "access_date": ACCESS_DATE,
                    **rights,
                    "editorial_summary": clean(f"{title} is indexed from {queue['source_name']}. {description or subjects}", max_chars=700),
                    "historical_context_note": (
                        f"Protocol-source record for {queue['macro_region']}. This item is retained for non-museum visual and cultural context."
                    ),
                    "classification_rationale": (
                        "Captured from an Omeka API item search and filtered by date plus graphic/design/public-culture terms."
                    ),
                    "uncertainty_note": "Image state is source-hosted; license and cultural display constraints remain reviewable.",
                    "citation_basis": f"{queue['source_name']}. {title}. {source_url}. Accessed {ACCESS_DATE}.",
                }
            )
            rows.append(row)
            if len(rows) >= MAX_ROWS_PER_SOURCE:
                return rows, failures
    return rows, failures


def select_queue() -> list[dict[str, str]]:
    rows = read_csv(QUEUE)
    allowed = {"dspace_oai_or_rest_adapter", "omeka_api_adapter"}
    return [row for row in rows if row["queue_priority"] == "Q1" and row["adapter_hint"] in allowed]


def assign_capture_ids(rows: list[dict[str, str]]) -> None:
    for idx, row in enumerate(rows, start=1):
        row["capture_id"] = f"PIC1970R{idx:04d}"


def write_records(rows: list[dict[str, str]]) -> None:
    with RECORDS_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_summary(summary_rows: list[dict[str, str]], rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "source_id",
        "source_name",
        "adapter_hint",
        "macro_region",
        "country_or_region",
        "status",
        "captured_records",
        "failure_count",
        "image_states",
        "notes",
    ]
    promoted_by_source = Counter(row["source_name"] for row in rows)
    image_by_source: dict[str, Counter[str]] = {}
    for row in rows:
        image_by_source.setdefault(row["source_name"], Counter())[row["image_presence_code"]] += 1
    for summary in summary_rows:
        promoted_count = promoted_by_source.get(summary["source_name"], 0)
        summary["captured_records"] = str(promoted_count)
        summary["status"] = "captured" if promoted_count else "no_records_promoted"
        images = image_by_source.get(summary["source_name"], Counter())
        summary["image_states"] = "; ".join(f"{k}:{v}" for k, v in sorted(images.items()))

    with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(summary_rows)

    image_counts = Counter(row["image_presence_code"] for row in rows)
    source_counts = Counter(row["source_name"] for row in rows)
    region_counts = Counter(row["source_place_text"] for row in rows)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Protocol Item Capture 1970-2026",
        "",
        "This pass converts selected Q1 protocol sources into item-level records. Failure evidence remains in the source summary and raw payloads; failed probes are not promoted into public surfaces.",
        "",
        f"- Captured records: {len(rows)}",
        f"- Sources attempted: {len(summary_rows)}",
        f"- Access date: {ACCESS_DATE}",
        "",
        "## Image States",
        "",
    ]
    for key, count in image_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Source Counts", ""])
    for key, count in source_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Region/Place Counts", ""])
    for key, count in region_counts.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Source Attempts", ""])
    for row in summary_rows:
        lines.append(
            f"- {row['source_id']} | {row['status']} | {row['source_name']} | "
            f"{row['captured_records']} records | failures {row['failure_count']}"
        )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    seen = existing_keys()
    rows: list[dict[str, str]] = []
    summary_rows: list[dict[str, str]] = []

    for queue in select_queue():
        if queue["adapter_hint"] == "dspace_oai_or_rest_adapter":
            captured, failures = dspace_records(queue, seen)
        elif queue["adapter_hint"] == "omeka_api_adapter":
            captured, failures = omeka_records(queue, seen)
        else:
            captured, failures = [], []

        rows.extend(captured)
        image_counts = Counter(row["image_presence_code"] for row in captured)
        summary_rows.append(
            {
                "source_id": queue["candidate_id"],
                "source_name": queue["source_name"],
                "adapter_hint": queue["adapter_hint"],
                "macro_region": queue["macro_region"],
                "country_or_region": queue["country_or_region"],
                "status": "captured" if captured else "no_records_promoted",
                "captured_records": str(len(captured)),
                "failure_count": str(len(failures)),
                "image_states": "; ".join(f"{k}:{v}" for k, v in sorted(image_counts.items())),
                "notes": " | ".join(f"{f['term']} {f['status']}" for f in failures[:4]),
            }
        )
        time.sleep(0.3)

    rows = consolidate_serial_rows(rows)
    assign_capture_ids(rows)
    write_records(rows)
    write_summary(summary_rows, rows)
    print(f"captured={len(rows)} sources_attempted={len(summary_rows)}")
    print(f"wrote {RECORDS_CSV}")
    print(f"wrote {SUMMARY_CSV}")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
