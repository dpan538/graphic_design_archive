#!/usr/bin/env python3
"""Capture a conservative edge-source WordPress batch for 1970-2026.

This pass expands the source pool using public WordPress REST endpoints from
the edge-source v2 probe. It is deliberately rights-aware: images stay
source-hosted (`IMG02`) and publication dates are treated as source-record
dates unless the source exposes stronger object-level dates.
"""

from __future__ import annotations

import csv
import html
import json
import re
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import run_midcentury_capture_1930_1970 as mc
import run_midcentury_expansion_capture_1931_1970 as mx
from contemporary_noise_filter import evaluate_record


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_edge_wordpress_1970_2026_raw"
RECORDS_CSV = DATA / "capture_batch_edge_wordpress_1970_2026_records.csv"
SUMMARY_CSV = DATA / "capture_batch_edge_wordpress_1970_2026_source_summary.csv"
REPORT = ROOT / "docs" / "capture" / "EDGE_WORDPRESS_CAPTURE_1970_2026.md"

ACCESS_DATE = "2026-06-01"
USER_AGENT = "ModernGDHistory/0.1 edge-wordpress-capture"
FIELDNAMES = mx.FIELDNAMES
YEAR_START = 1970
YEAR_END = 2026
ADMIN_TITLE_TERMS = (
    "call for tender",
    "open bid",
    "call for applications",
    "application deadline",
    "press release",
    "donation",
    "launch a major national project",
    "training",
    "training program",
    "training programme",
    "welcome back",
    "reopens",
    "consultation space",
    "job opening",
    "vacancy",
    "annual report",
)
SECRET_PATTERNS = (
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"(?i)(key=)[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key[\"'\s:=]+)[0-9A-Za-z_-]{20,}"),
    re.compile(r"\bgh[pousr]_[0-9A-Za-z_]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
)


@dataclass(frozen=True)
class SourceConfig:
    source_id: str
    source_name: str
    macro_region: str
    country_or_region: str
    base_url: str
    direction_id: str
    direction_name: str
    queries: tuple[str, ...]
    max_records: int
    default_place: str
    source_note: str


SOURCES: tuple[SourceConfig, ...] = (
    SourceConfig(
        "ESV212",
        "Tokyo TDC",
        "East Asia",
        "Japan",
        "https://tokyotypedirectorsclub.org",
        "EW01",
        "tokyo_tdc_typography_context_1970_2026",
        ("typography", "poster", "exhibition", "award", "design"),
        8,
        "Japan",
        "Professional typography/design organization; source-hosted image evidence only.",
    ),
    SourceConfig(
        "ESV221",
        "DesignSingapore Council",
        "Southeast Asia",
        "Singapore",
        "https://designsingapore.org",
        "EW02",
        "designsingapore_policy_and_design_context_2003_2026",
        ("graphic design", "poster", "identity", "publication", "typography"),
        8,
        "Singapore",
        "Government design institution; useful for contemporary policy and design-context records.",
    ),
    SourceConfig(
        "ESV225",
        "Asian Film Archive",
        "Southeast Asia",
        "Singapore / regional",
        "https://asianfilmarchive.org",
        "EW03",
        "asian_film_archive_publicity_context_1970_2026",
        ("poster", "publicity", "title design", "programme", "archive"),
        8,
        "Singapore / Southeast Asia",
        "Regional film archive; film publicity and poster records are link-first and rights-sensitive.",
    ),
    SourceConfig(
        "ESV229",
        "Bophana Audiovisual Resource Center",
        "Southeast Asia",
        "Cambodia",
        "https://bophana.org",
        "EW04",
        "bophana_cambodia_visual_culture_context_1970_2026",
        ("poster", "archive", "exhibition", "film", "Cambodia"),
        8,
        "Cambodia",
        "Cambodian audiovisual/community archive; item images remain source-hosted.",
    ),
    SourceConfig(
        "ESV236",
        "Cultural Center of the Philippines",
        "Southeast Asia",
        "Philippines",
        "https://culturalcenter.gov.ph",
        "EW05",
        "ccp_philippines_cultural_graphics_context_1970_2026",
        ("poster", "graphic design", "exhibition", "publication", "festival"),
        8,
        "Philippines",
        "Philippine cultural institution; records serve event/publication graphic context.",
    ),
    SourceConfig(
        "ESV238",
        "Grafis Nusantara",
        "Southeast Asia",
        "Indonesia",
        "https://grafisnusantara.com",
        "EW06",
        "grafis_nusantara_indonesian_ephemera_1970_2026",
        ("label", "packaging", "poster", "sticker", "typography"),
        12,
        "Indonesia",
        "Community graphic archive focused on Indonesian labels, stickers, packaging, and ephemera.",
    ),
    SourceConfig(
        "ESV239",
        "Desain Grafis Indonesia",
        "Southeast Asia",
        "Indonesia",
        "https://dgi.or.id",
        "EW07",
        "desain_grafis_indonesia_text_context_1970_2026",
        ("poster", "typography", "graphic design", "identity", "archive"),
        10,
        "Indonesia",
        "Indonesian design-history publication; high text-enrichment value.",
    ),
    SourceConfig(
        "ESV240",
        "Indonesian Visual Art Archive",
        "Southeast Asia",
        "Indonesia",
        "https://archive.ivaa-online.org",
        "EW08",
        "ivaa_indonesian_visual_archive_context_1970_2026",
        ("poster", "publication", "graphic", "archive", "exhibition"),
        8,
        "Indonesia",
        "Community visual archive; may expose artwork/event context rather than clean design-object records.",
    ),
    SourceConfig(
        "ESV244",
        "Another Graphic",
        "Global",
        "post-1990 international",
        "https://anothergraphic.org",
        "EW09",
        "another_graphic_independent_design_context_1990_2026",
        ("Asia", "poster", "typography", "identity", "editorial"),
        8,
        "post-1990 international",
        "Independent curated design source; context/link layer, not ownership evidence.",
    ),
    SourceConfig(
        "ESV246",
        "People's Graphic Design Archive",
        "Global",
        "global/community",
        "https://peoplesgdarchive.org",
        "EW10",
        "pgda_community_graphic_design_records_1970_2026",
        ("poster", "typography", "community", "activism", "publication"),
        8,
        "global/community",
        "Community-uploaded design archive; high relevance but rights and authority require review.",
    ),
    SourceConfig(
        "ESV248",
        "Design Reviewed",
        "Europe",
        "United Kingdom / global",
        "https://www.designreviewed.com",
        "EW11",
        "design_reviewed_independent_archive_context_1970_2026",
        ("poster", "identity", "typography", "magazine", "archive"),
        8,
        "United Kingdom / global",
        "Independent design archive/source; rights-sensitive, source-hosted images only.",
    ),
    SourceConfig(
        "ESV255",
        "Arquivo Nacional Brasil",
        "Latin America",
        "Brazil",
        "https://www.gov.br/arquivonacional",
        "EW12",
        "arquivo_nacional_brazil_context_1970_2026",
        ("cartaz", "design gráfico", "publicação", "exposição", "arquivo"),
        8,
        "Brazil",
        "Brazilian national archive context; stable source registry before item promotion.",
    ),
    SourceConfig(
        "ESV260",
        "JAGDA",
        "East Asia",
        "Japan",
        "https://www.jagda.or.jp",
        "EW13",
        "jagda_postwar_contemporary_graphic_design_context_1970_2026",
        ("poster", "typography", "exhibition", "identity", "graphic design"),
        8,
        "Japan",
        "Japanese professional graphic design organization; source-hosted images and text only.",
    ),
    SourceConfig(
        "ESV261",
        "Fonts In Use",
        "Global",
        "global",
        "https://fontsinuse.com",
        "EW14",
        "fonts_in_use_typographic_evidence_1970_2026",
        ("poster", "identity", "magazine", "signage", "publication"),
        8,
        "global",
        "Typographic use archive; evidence is contextual and source-hosted, not ownership evidence for underlying works.",
    ),
    SourceConfig(
        "ESV262",
        "Letterform Archive",
        "North America",
        "United States / global",
        "https://letterformarchive.org",
        "EW15",
        "letterform_archive_typography_collection_context_1970_2026",
        ("poster", "typography", "identity", "publication", "archive"),
        8,
        "United States / global",
        "Typography and graphic design archive; source-hosted images only unless item-level rights state is explicit.",
    ),
    SourceConfig(
        "ESV263",
        "Thaipography Archive",
        "Southeast Asia",
        "Thailand",
        "https://thaipography-archive.com",
        "EW16",
        "thaipography_archive_thai_typography_context_1990_2026",
        ("typography", "poster", "lettering", "publication", "identity"),
        8,
        "Thailand",
        "Thai typography/design archive; useful for Southeast Asian contemporary graphic design context.",
    ),
    SourceConfig(
        "ESV264",
        "M+ Magazine",
        "East Asia",
        "Hong Kong",
        "https://www.mplus.org.hk",
        "EW17",
        "mplus_hong_kong_visual_culture_context_1970_2026",
        ("graphic design", "poster", "typography", "identity", "publication"),
        8,
        "Hong Kong",
        "Museum publication/source-context records for Hong Kong and East Asian visual culture; images remain source-hosted.",
    ),
)


def clean(value: Any, *, max_chars: int = 900) -> str:
    text = html.unescape(re.sub(r"\s+", " ", str(value or "")).strip())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rsplit(" ", 1)[0] + "..."


def strip_tags(value: Any, *, max_chars: int = 1400) -> str:
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", str(value or ""))
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return clean(text, max_chars=max_chars)


def redact_secrets(value: str) -> str:
    redacted = value
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: (match.group(1) if match.lastindex else "") + "[REDACTED_SECRET]", redacted)
    return redacted


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json,*/*"},
    )
    with urllib.request.urlopen(req, timeout=35) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def write_raw(name: str, payload: Any) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(redact_secrets(text), encoding="utf-8")
    return str(path.relative_to(ROOT))


def clear_raw_dir() -> None:
    if not RAW_DIR.exists():
        return
    for path in sorted(RAW_DIR.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "record"


def year_from_text(value: str) -> str:
    years = [int(match.group(1)) for match in re.finditer(r"\b(19[7-9]\d|20[0-2]\d)\b", value or "")]
    if not years:
        return ""
    year = max(y for y in years if YEAR_START <= y <= YEAR_END)
    return str(year) if year else ""


def endpoint_url(source: SourceConfig, rest_base: str, query: str, page: int = 1) -> str:
    params = {
        "per_page": "20",
        "page": str(page),
        "_embed": "1",
        "search": query,
    }
    return f"{source.base_url.rstrip('/')}/wp-json/wp/v2/{rest_base}?{urllib.parse.urlencode(params)}"


def get_terms(source: SourceConfig, taxonomy: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for page in range(1, 4):
        url = f"{source.base_url.rstrip('/')}/wp-json/wp/v2/{taxonomy}?per_page=100&page={page}"
        try:
            payload = fetch_json(url)
        except Exception:
            break
        if not isinstance(payload, list) or not payload:
            break
        write_raw(f"{slug(source.source_name)}_{taxonomy}_{page}.json", payload)
        for item in payload:
            if isinstance(item, dict) and item.get("id"):
                out[int(item["id"])] = strip_tags(item.get("name"), max_chars=140)
        if len(payload) < 100:
            break
    return out


def get_rest_bases(source: SourceConfig) -> list[str]:
    try:
        payload = fetch_json(f"{source.base_url.rstrip('/')}/wp-json/wp/v2/types")
    except Exception:
        return ["posts"]
    write_raw(f"{slug(source.source_name)}_types.json", payload)
    bases: list[str] = []
    if isinstance(payload, dict):
        for key, item in payload.items():
            if not isinstance(item, dict):
                continue
            rest_base = str(item.get("rest_base") or key)
            if rest_base in {"media", "attachment", "wp_block", "nav_menu_item"}:
                continue
            if item.get("viewable") is False:
                continue
            if rest_base not in bases:
                bases.append(rest_base)
    preferred = [base for base in ("posts", "item", "product", "projects", "work", "archive") if base in bases]
    return preferred or ["posts"]


def image_from_embedded(post: dict[str, Any]) -> tuple[str, str]:
    embedded = post.get("_embedded") if isinstance(post.get("_embedded"), dict) else {}
    media = embedded.get("wp:featuredmedia") if isinstance(embedded.get("wp:featuredmedia"), list) else []
    for item in media:
        if not isinstance(item, dict):
            continue
        alt = clean(item.get("alt_text"), max_chars=220)
        details = item.get("media_details") if isinstance(item.get("media_details"), dict) else {}
        sizes = details.get("sizes") if isinstance(details.get("sizes"), dict) else {}
        for key in ("large", "medium_large", "full", "medium"):
            size = sizes.get(key)
            if isinstance(size, dict) and size.get("source_url"):
                return clean(size.get("source_url"), max_chars=900), alt
        if item.get("source_url"):
            return clean(item.get("source_url"), max_chars=900), alt
    return "", ""


def image_from_parent_media(source: SourceConfig, post_id: str) -> tuple[str, str, str]:
    if not post_id:
        return "", "", ""
    url = f"{source.base_url.rstrip('/')}/wp-json/wp/v2/media?parent={urllib.parse.quote(post_id)}&per_page=20"
    try:
        payload = fetch_json(url)
    except Exception:
        return "", "", ""
    raw_path = write_raw(f"{slug(source.source_name)}_media_{post_id}.json", payload)
    if not isinstance(payload, list):
        return "", "", raw_path
    for item in payload:
        if not isinstance(item, dict) or item.get("media_type") != "image":
            continue
        alt = clean(item.get("alt_text"), max_chars=220)
        details = item.get("media_details") if isinstance(item.get("media_details"), dict) else {}
        sizes = details.get("sizes") if isinstance(details.get("sizes"), dict) else {}
        for key in ("large", "medium_large", "full", "medium"):
            size = sizes.get(key)
            if isinstance(size, dict) and size.get("source_url"):
                return clean(size.get("source_url"), max_chars=900), alt, raw_path
        if item.get("source_url"):
            return clean(item.get("source_url"), max_chars=900), alt, raw_path
    return "", "", raw_path


def image_fields(code: str, image_url: str, viewer: str, basis: str) -> dict[str, str]:
    return mc.image_fields(
        code,
        basis,
        image_url=image_url,
        viewer=viewer or image_url,
        confidence="high" if image_url else "medium",
        rights_review_required=True,
        local_copy_permitted=False,
        note="Edge-source capture keeps images source-hosted; item-level rights remain with the source and original creator.",
    )


def seen_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in DATA.glob("capture_batch_*_records.csv"):
        if path == RECORDS_CSV or not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                keys.add((row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", "")))
    return keys


def row_defaults(row: dict[str, str]) -> dict[str, str]:
    code = row.get("image_presence_code") or "IMG04"
    row["image_expectation"] = "not_expected" if code == "IMG04" else "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["ocr_or_excerpt"] = row.get("source_description", "")
    row["source_description_raw"] = row.get("source_description", "")
    row.setdefault("editorial_summary", row.get("source_description", ""))
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def capture_source(source: SourceConfig, seen: set[tuple[str, str]]) -> tuple[list[dict[str, str]], dict[str, str]]:
    rows: list[dict[str, str]] = []
    failures = 0
    duplicates = 0
    categories = get_terms(source, "categories")
    tags = get_terms(source, "tags")
    rest_bases = get_rest_bases(source)
    for rest_base in rest_bases:
        for query in source.queries:
            if len(rows) >= source.max_records:
                break
            url = endpoint_url(source, rest_base, query)
            try:
                payload = fetch_json(url)
            except Exception:
                failures += 1
                continue
            raw_path = write_raw(f"{slug(source.source_name)}_{slug(rest_base)}_{slug(query)}.json", payload)
            if not isinstance(payload, list):
                continue
            for post in payload:
                if len(rows) >= source.max_records:
                    break
                if not isinstance(post, dict):
                    continue
                identifier = f"{rest_base}:{post.get('id') or ''}"
                title = strip_tags((post.get("title") or {}).get("rendered"), max_chars=280)
                excerpt = strip_tags((post.get("excerpt") or {}).get("rendered"), max_chars=900)
                body = strip_tags((post.get("content") or {}).get("rendered"), max_chars=1600)
                link = clean(post.get("link"), max_chars=900)
                title_l = title.lower()
                if not identifier or not title or not link:
                    continue
                if title_l in {"terms of use", "privacy policy", "cookie policy"}:
                    continue
                if any(term in title_l for term in ("advisory board", "contact us", "terms and conditions")):
                    continue
                if any(term in title_l for term in ADMIN_TITLE_TERMS):
                    continue
                key = (source.source_name, identifier)
                if key in seen:
                    duplicates += 1
                    continue
                date_text = clean(str(post.get("date", ""))[:10], max_chars=40)
                candidate_year = year_from_text(" ".join([date_text, title, excerpt, body]))
                if not candidate_year:
                    continue
                category_names = [categories.get(int(value), "") for value in post.get("categories", []) if str(value).isdigit()]
                tag_names = [tags.get(int(value), "") for value in post.get("tags", []) if str(value).isdigit()]
                description = clean(" ".join(part for part in (excerpt, body) if part), max_chars=1500)
                image_url, alt = image_from_embedded(post)
                media_raw_path = ""
                if not image_url:
                    image_url, alt, media_raw_path = image_from_parent_media(source, str(post.get("id") or ""))
                rights_basis = (
                    f"{source.source_name} public WordPress metadata. Images are not copied locally; "
                    "display is limited to source-hosted/reference behavior pending item-level review."
                )
                image = image_fields("IMG02" if image_url else "IMG04", image_url, link, rights_basis)
                object_type = clean("; ".join(name for name in category_names if name) or f"{source.source_name} source record", max_chars=240)
                subjects = clean("; ".join(name for name in tag_names + category_names if name) or query, max_chars=520)
                source_description = clean(" ".join(part for part in (description, alt) if part), max_chars=1500)
                if len(description) < 40 and not image_url:
                    continue
                relevant_text = " ".join([title, description, subjects, object_type]).lower()
                relevance_terms = (
                    "poster",
                    "graphic",
                    "design",
                    "typograph",
                    "publication",
                    "print",
                    "visual",
                    "archive",
                    "exhibition",
                    "identity",
                    "label",
                    "packag",
                    "sticker",
                    "cinema",
                    "publicity",
                    "advertising",
                    "letter",
                )
                if not any(term in relevant_text for term in relevance_terms):
                    continue
                seen.add(key)
                rows.append(
                    row_defaults(
                        {
                            "capture_id": "",
                            "direction_id": source.direction_id,
                            "direction_name": source.direction_name,
                            "source_id": source.source_id,
                            "source_name": source.source_name,
                            "source_api_url": url,
                            "capture_status": "captured",
                            "source_identifier": identifier,
                            "source_record_url": link,
                            "source_title": title,
                            "source_creator": "",
                            "source_date_text": date_text,
                            "date_start": candidate_year,
                            "date_end": candidate_year,
                            "source_place_text": source.default_place,
                            "source_object_type": object_type,
                            "source_medium": object_type,
                            "source_collection": source.source_name,
                            "source_description": source_description,
                            "source_notes": source.source_note,
                            "source_subjects": subjects,
                            "source_rights_text": rights_basis,
                            "rights_uri": "",
                            "raw_json_path": media_raw_path or raw_path,
                            "access_date": ACCESS_DATE,
                            **image,
                            "editorial_summary": clean(f"{title} is indexed from {source.source_name}. {source_description}", max_chars=850),
                            "historical_context_note": clean(
                                f"{source.source_name} expands the archive toward {source.country_or_region} / {source.macro_region} and provides context for graphic design, visual culture, publication, poster, typography, or institutional design circulation outside the large museum API canon.",
                                max_chars=620,
                            ),
                            "classification_rationale": "Captured from a public WordPress REST endpoint and filtered by design/print/visual-culture terms. Folder placement remains provisional and generated from source metadata.",
                            "uncertainty_note": "Date is generally the source record publication date unless the title/body exposes a clearer work date. This row should be treated as a source/context record until item-level metadata is verified.",
                            "citation_basis": f"{source.source_name}. {title}. {link}. Accessed {ACCESS_DATE}.",
                        }
                    )
                )
    status = "captured" if rows else "no_records_promoted"
    return rows, {
        "source_id": source.source_id,
        "source_name": source.source_name,
        "macro_region": source.macro_region,
        "country_or_region": source.country_or_region,
        "status": status,
        "captured_records": str(len(rows)),
        "failure_count": str(failures),
        "duplicate_count": str(duplicates),
        "rest_bases": ";".join(rest_bases),
    }


def assign_ids(rows: list[dict[str, str]]) -> None:
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"EW1970R{index:03d}"


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


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_report(rows: list[dict[str, str]], summaries: list[dict[str, str]]) -> None:
    source_counts = Counter(row["source_name"] for row in rows)
    image_counts = Counter(row["image_presence_code"] for row in rows)
    region_counts = Counter(row["source_place_text"] for row in rows)
    text_rows = sum(1 for row in rows if len(row.get("source_description", "")) >= 160)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Edge WordPress Source Capture 1970-2026",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        "This batch promotes a conservative set of records from P1/P2 edge-source candidates identified in `EDGE_SOURCE_PROBE_v2.md`. It focuses on public WordPress REST endpoints because they provide repeatable metadata, source URLs, text excerpts, and source-hosted image references without requiring local image copying.",
        "",
        "## Capture Rules",
        "",
        "- Sources are local, community, professional, government, or independent design/context sources.",
        "- Images are `IMG02` when source-hosted media is exposed, otherwise `IMG04`.",
        "- No image is promoted to `IMG03`; no local copy is made.",
        "- Dates are source-record dates unless the source text exposes a stronger object date.",
        "- The batch is suitable for source registry and text/image coverage testing, not final authority claims.",
        "",
        "## Summary",
        "",
        f"- Captured records: {len(rows)}",
        f"- Sources attempted: {len(summaries)}",
        f"- Sources with records: {len(source_counts)}",
        f"- Image states: {dict(image_counts)}",
        f"- Records with >=160 characters of source text: {text_rows}",
        f"- Regions/places represented: {dict(region_counts)}",
        "",
        "## Source Counts",
        "",
    ]
    for name, count in sorted(source_counts.items()):
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Attempt Summary", ""])
    for summary in summaries:
        lines.append(
            f"- {summary['source_name']} ({summary['country_or_region']}): "
            f"{summary['status']}; records {summary['captured_records']}; "
            f"duplicates {summary['duplicate_count']}; failures {summary['failure_count']}; "
            f"rest bases `{summary['rest_bases']}`"
        )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    clear_raw_dir()
    seen = seen_keys()
    rows: list[dict[str, str]] = []
    summaries: list[dict[str, str]] = []
    for source in SOURCES:
        captured, summary = capture_source(source, seen)
        rows.extend(captured)
        summaries.append(summary)
    rows, noise_decisions = apply_noise_filter(rows)
    assign_ids(rows)
    write_csv(RECORDS_CSV, rows, FIELDNAMES)
    write_csv(
        SUMMARY_CSV,
        summaries,
        ["source_id", "source_name", "macro_region", "country_or_region", "status", "captured_records", "failure_count", "duplicate_count", "rest_bases"],
    )
    write_report(rows, summaries)
    print(
        f"captured={len(rows)} sources={len({row['source_name'] for row in rows})} "
        f"image_states={dict(Counter(row['image_presence_code'] for row in rows))} "
        f"noise_filter={dict(noise_decisions)}"
    )
    print(f"wrote {RECORDS_CSV.relative_to(ROOT)}")
    print(f"wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
