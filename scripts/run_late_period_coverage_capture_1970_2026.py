from __future__ import annotations

import csv
import html
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import run_midcentury_capture_1930_1970 as mc
import run_midcentury_expansion_capture_1931_1970 as mx
import run_wikimedia_commons_image_ready_1830_1970 as commons
from contemporary_noise_filter import evaluate_record


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_late_period_coverage_1970_2026_raw"
RECORDS_CSV = DATA / "capture_batch_late_period_coverage_1970_2026_records.csv"
SUMMARY_CSV = DATA / "capture_batch_late_period_coverage_1970_2026_source_summary.csv"

ACCESS_DATE = "2026-06-01"
USER_AGENT = "ModernGDHistory/0.1 late-period-coverage"
FIELDNAMES = mx.FIELDNAMES

YEAR_START = 1970
YEAR_END = 2026


COMMONS_PLAN = [
    {
        "direction_id": "LPC01",
        "direction_name": "commons_late_counterpublic_poster_records",
        "query": '"AIDS poster" OR "ACT UP poster" OR "silence death poster"',
        "limit": 10,
        "region": "United States / transnational",
        "theme": "AIDS activist graphics and public health countervisuals",
        "required_terms": ["aids", "act up", "silence", "poster"],
    },
    {
        "direction_id": "LPC02",
        "direction_name": "commons_late_anti_apartheid_and_solidarity_graphics",
        "query": '"anti-apartheid poster" OR "apartheid poster" OR "Free Mandela poster"',
        "limit": 10,
        "region": "South Africa / transnational",
        "theme": "anti-apartheid and liberation solidarity graphics",
        "required_terms": ["apartheid", "mandela", "solidarity", "poster"],
    },
    {
        "direction_id": "LPC03",
        "direction_name": "commons_late_palestinian_solidarity_graphics",
        "query": '"Palestinian poster" OR "Palestine solidarity poster" OR "Intifada poster"',
        "limit": 10,
        "region": "Palestine / transnational",
        "theme": "Palestinian liberation and solidarity poster culture",
        "required_terms": ["palestine", "palestinian", "intifada", "poster"],
    },
    {
        "direction_id": "LPC04",
        "direction_name": "commons_late_environmental_and_nuclear_public_graphics",
        "query": '"anti nuclear poster" OR "environmental poster" OR "climate poster"',
        "limit": 10,
        "region": "transnational",
        "theme": "environmental, anti-nuclear, and climate public graphics",
        "required_terms": ["nuclear", "environment", "climate", "poster"],
    },
    {
        "direction_id": "LPC05",
        "direction_name": "commons_late_punk_music_and_subcultural_print",
        "query": '"punk poster" OR "punk flyer" OR "music flyer"',
        "limit": 10,
        "region": "transnational",
        "theme": "punk, music flyer, and subcultural print circulation",
        "required_terms": ["punk", "flyer", "poster", "music"],
    },
    {
        "direction_id": "LPC06",
        "direction_name": "commons_late_digital_interface_and_web_visual_culture",
        "query": '"web design" screenshot OR "website screenshot" "graphic design"',
        "limit": 10,
        "region": "global web / transnational",
        "theme": "web, interface, and networked visual communication",
        "required_terms": ["web", "website", "screenshot", "interface", "graphic design"],
    },
]


IA_PLAN = [
    {
        "direction_id": "LPIA01",
        "direction_name": "internet_archive_late_design_periodicals_and_books",
        "query": '("graphic design" OR "typography" OR "desktop publishing") AND mediatype:texts AND date:[1970 TO 2026]',
        "limit": 18,
        "region": "global web / transnational",
        "theme": "late twentieth-century design periodicals, books, and desktop publishing texts",
    },
    {
        "direction_id": "LPIA02",
        "direction_name": "internet_archive_web_interface_design_context",
        "query": '("web design" OR "interface design" OR "information architecture") AND mediatype:texts AND date:[1990 TO 2026]',
        "limit": 14,
        "region": "global web / transnational",
        "theme": "web/interface design texts and networked visual communication",
    },
    {
        "direction_id": "LPIA03",
        "direction_name": "internet_archive_poster_and_zine_culture",
        "query": '("poster design" OR "zine" OR "flyer design") AND mediatype:texts AND date:[1970 TO 2026]',
        "limit": 14,
        "region": "transnational",
        "theme": "poster, zine, flyer, and self-published print culture",
    },
]

TE_PAPA_TERMS = [
    "poster protest",
    "poster Maori",
    "poster Pacific",
    "poster music",
    "poster environment",
    "poster gay rights",
]


class MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}
        self.images: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.in_title = False
        self.in_h1 = False
        self.in_a = False
        self.current_href = ""
        self.title_parts: list[str] = []
        self.h1_parts: list[str] = []
        self.link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        tag_l = tag.lower()
        if tag_l == "title":
            self.in_title = True
        if tag_l == "h1":
            self.in_h1 = True
        if tag_l == "a":
            self.in_a = True
            self.current_href = attrs_dict.get("href", "")
            self.link_text = []
        if tag_l == "meta":
            key = (attrs_dict.get("property") or attrs_dict.get("name") or "").lower()
            content = attrs_dict.get("content") or ""
            if key and content:
                self.meta[key] = html.unescape(content)
        if tag_l in {"img", "source"}:
            for attr in ("src", "data-src", "srcset"):
                value = attrs_dict.get(attr)
                if value:
                    self.images.append(html.unescape(value.split()[0]))

    def handle_endtag(self, tag: str) -> None:
        tag_l = tag.lower()
        if tag_l == "title":
            self.in_title = False
        if tag_l == "h1":
            self.in_h1 = False
        if tag_l == "a" and self.in_a:
            self.links.append((self.current_href, " ".join(self.link_text)))
            self.in_a = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.in_h1:
            self.h1_parts.append(data)
        if self.in_a:
            self.link_text.append(data)


def clean(value: Any, *, max_chars: int = 900) -> str:
    text = html.unescape(re.sub(r"\s+", " ", str(value or "")).strip())
    return text[:max_chars]


def strip_markup(value: str, *, max_chars: int = 900) -> str:
    value = re.sub(r"(?is)<(script|style).*?</\1>", " ", value or "")
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    return clean(value, max_chars=max_chars)


def fetch_bytes(url: str, *, accept: str = "text/html,application/xhtml+xml,application/json") -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(req, timeout=35) as response:
        return response.read()


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8", errors="replace")


def fetch_json(url: str) -> dict[str, Any]:
    return json.loads(fetch_bytes(url, accept="application/json").decode("utf-8", errors="replace"))


def write_raw(name: str, payload: dict[str, Any]) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path.relative_to(ROOT))


def existing_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in DATA.glob("capture_batch_*_records.csv"):
        if path == RECORDS_CSV or not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                keys.add((row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", "")))
    return keys


def years_from_text(value: str) -> list[int]:
    years = [int(year) for year in re.findall(r"(?<!\d)((?:19|20)\d{2})(?!\d)", value or "")]
    return [year for year in years if YEAR_START <= year <= YEAR_END]


def terminal_year(value: str) -> int | None:
    years = years_from_text(value)
    return max(years) if years else None


def image_rights(code: str, image_url: str, viewer: str, basis: str, *, open_image: bool = False) -> dict[str, str]:
    return mc.image_fields(
        code,
        basis,
        image_url=image_url,
        viewer=viewer,
        confidence="high" if image_url else "medium",
        rights_review_required=not open_image,
        local_copy_permitted=False,
        note="Source-hosted display only; no local image copy or ownership claim.",
    )


def row_defaults(row: dict[str, str]) -> dict[str, str]:
    row["image_expectation"] = "not_expected" if row.get("image_presence_code") == "IMG04" else "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["source_description_raw"] = row.get("source_description", "")
    row["ocr_or_excerpt"] = row.get("source_description") or row.get("source_notes") or row.get("source_subjects", "")
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def commons_year(blob: str) -> int | None:
    years = years_from_text(blob)
    return min(years) if years else None


def commons_relevant(plan: dict[str, Any], blob: str) -> bool:
    blob_l = blob.lower()
    return any(term.lower() in blob_l for term in plan["required_terms"])


def commons_row(page: dict[str, Any], plan: dict[str, Any], api_url: str, raw_path: str) -> dict[str, str] | None:
    imageinfos = page.get("imageinfo") or []
    if not imageinfos:
        return None
    info = imageinfos[0]
    if not str(info.get("mime", "")).startswith("image/"):
        return None
    title = commons.clean(page.get("title", "")).replace("File:", "", 1)
    if title.lower().endswith((".djvu", ".pdf", ".svg", ".ogg", ".webm")):
        return None
    meta = commons.extmeta(info)
    blob = " ".join(
        [
            title,
            meta.get("ObjectName", ""),
            meta.get("ImageDescription", ""),
            meta.get("Categories", ""),
            meta.get("Credit", ""),
            plan["theme"],
        ]
    )
    year = commons_year(blob)
    if year is None or not commons_relevant(plan, blob) or not commons.is_open(meta):
        return None
    image_url = commons.clean(info.get("thumburl") or info.get("url"))
    source_url = commons.clean(info.get("descriptionurl") or info.get("descriptionshorturl"))
    if not image_url or not source_url:
        return None
    license_label = commons.clean(meta.get("LicenseShortName") or meta.get("UsageTerms") or meta.get("License"))
    description = commons.clean(meta.get("ImageDescription") or meta.get("ObjectName") or title, max_chars=900)
    categories = commons.clean(meta.get("Categories"), max_chars=900)
    rights = image_rights(
        "IMG03",
        image_url,
        source_url,
        f"Wikimedia Commons open-license metadata: {license_label}. Commons is a secondary display layer; original holding context remains reviewable.",
        open_image=True,
    )
    row = {
        "capture_id": "",
        "direction_id": plan["direction_id"],
        "direction_name": plan["direction_name"],
        "source_id": commons.SOURCE_ID,
        "source_name": commons.SOURCE_NAME,
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
        "source_object_type": "open image record / late-period graphic communication",
        "source_medium": "poster / flyer / print / interface image",
        "source_collection": commons.clean(meta.get("Credit") or "Wikimedia Commons"),
        "source_description": description,
        "source_notes": commons.clean("; ".join([meta.get("ObjectName", ""), meta.get("DateTimeOriginal", ""), categories]), max_chars=900),
        "source_subjects": commons.clean(f"{plan['theme']}; {categories}", max_chars=900),
        "source_rights_text": commons.clean("; ".join([license_label, meta.get("UsageTerms", ""), meta.get("LicenseUrl", "")])),
        "rights_uri": commons.clean(meta.get("LicenseUrl")),
        "raw_json_path": raw_path,
        "access_date": ACCESS_DATE,
        **rights,
        "historical_context_note": (
            f"Late-period coverage record for {plan['theme']}. Commons is used as an image-access layer while the archive keeps source return and rights evidence visible."
        ),
        "classification_rationale": (
            "Captured by targeted late-period movement/theme query. Classification is based on explicit title, description, category, date, and query evidence; visual resemblance is not used."
        ),
        "uncertainty_note": "Commons metadata may be user-contributed or derived from another institution; verify original source if this becomes a canonical main sheet.",
        "citation_basis": f"Wikimedia Commons. {title}. {source_url}. Accessed {ACCESS_DATE}.",
        "editorial_summary": commons.clean(f"{title} is indexed as a late-period open image record for {plan['theme']}. {description}", max_chars=700),
    }
    return row_defaults(row)


def capture_commons(seen: set[tuple[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    for plan in COMMONS_PLAN:
        added = 0
        offset = 0
        while added < plan["limit"]:
            url = commons.search_url(plan["query"], offset=offset, limit=35)
            try:
                payload = commons.fetch_json(url)
            except Exception as exc:  # noqa: BLE001
                failures.append({"direction_id": plan["direction_id"], "source_name": commons.SOURCE_NAME, "error": str(exc)})
                break
            raw_path = write_raw(f"{plan['direction_name']}_{offset}.json", payload)
            pages = list((payload.get("query", {}).get("pages") or {}).values())
            if not pages:
                break
            for page in sorted(pages, key=lambda item: item.get("index", 9999)):
                row = commons_row(page, plan, url, raw_path)
                if not row:
                    continue
                key = (row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", ""))
                if key in seen:
                    continue
                seen.add(key)
                rows.append(row)
                added += 1
                if added >= plan["limit"]:
                    break
            if "continue" not in payload:
                break
            offset = int(payload.get("continue", {}).get("gsroffset", offset + 35))
            if offset > 245:
                break
            time.sleep(0.55)
    return rows, failures


def ia_search_url(query: str, *, rows: int) -> str:
    params = [
        ("q", query),
        ("fl[]", "identifier"),
        ("fl[]", "title"),
        ("fl[]", "creator"),
        ("fl[]", "date"),
        ("fl[]", "description"),
        ("fl[]", "subject"),
        ("fl[]", "collection"),
        ("fl[]", "publicdate"),
        ("sort[]", "downloads desc"),
        ("rows", str(rows)),
        ("page", "1"),
        ("output", "json"),
    ]
    return "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(params)


def ia_value(value: Any) -> str:
    if isinstance(value, list):
        return clean("; ".join(str(item) for item in value if item), max_chars=900)
    return clean(value, max_chars=900)


def ia_row(doc: dict[str, Any], plan: dict[str, Any], api_url: str, raw_path: str) -> dict[str, str] | None:
    identifier = ia_value(doc.get("identifier"))
    title = ia_value(doc.get("title"),) or identifier
    if not identifier or not title:
        return None
    year = terminal_year(" ".join([ia_value(doc.get("date")), title, ia_value(doc.get("publicdate"))]))
    if year is None:
        return None
    source_url = f"https://archive.org/details/{identifier}"
    image_url = f"https://archive.org/services/img/{urllib.parse.quote(identifier)}"
    description = strip_markup(ia_value(doc.get("description")), max_chars=1100)
    subjects = ia_value(doc.get("subject"),)
    rights = image_rights(
        "IMG02",
        image_url,
        source_url,
        "Internet Archive exposes a source-hosted item thumbnail. This is treated as source-viewer evidence, not a local reusable image.",
    )
    row = {
        "capture_id": "",
        "direction_id": plan["direction_id"],
        "direction_name": plan["direction_name"],
        "source_id": "SRC043",
        "source_name": "Internet Archive / text and periodical collections",
        "source_api_url": api_url,
        "capture_status": "captured",
        "source_identifier": identifier,
        "source_record_url": source_url,
        "source_title": title,
        "source_creator": ia_value(doc.get("creator")),
        "source_date_text": ia_value(doc.get("date")) or str(year),
        "date_start": str(year),
        "date_end": str(year),
        "source_place_text": plan["region"],
        "source_object_type": "text/periodical record / late-period design context",
        "source_medium": "digitized text / periodical / design discourse",
        "source_collection": ia_value(doc.get("collection")) or "Internet Archive",
        "source_description": description or f"{title} is indexed from Internet Archive for late-period design and visual communication context.",
        "source_notes": "Internet Archive text record; use as source-return context and reading support, not as a definitive object-rights authority.",
        "source_subjects": clean(f"{plan['theme']}; {subjects}", max_chars=900),
        "source_rights_text": "Rights vary by item; review source page before reuse.",
        "rights_uri": "",
        "raw_json_path": raw_path,
        "access_date": ACCESS_DATE,
        **rights,
        "historical_context_note": (
            f"Late-period reading/source record for {plan['theme']}. It helps prevent the archive from becoming only an image table by preserving text and discourse context."
        ),
        "classification_rationale": "Captured from Internet Archive advanced search by late-period design/publication query, terminal year, and source title/subject evidence.",
        "uncertainty_note": "Internet Archive metadata and thumbnails are heterogeneous; treat this as a reading/source support record until item rights are reviewed.",
        "citation_basis": f"Internet Archive. {title}. {source_url}. Accessed {ACCESS_DATE}.",
        "editorial_summary": clean(f"{title} is indexed from Internet Archive as a late-period design-context text. {description or subjects}", max_chars=700),
    }
    return row_defaults(row)


def capture_internet_archive(seen: set[tuple[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    for plan in IA_PLAN:
        url = ia_search_url(plan["query"], rows=plan["limit"] * 3)
        try:
            payload = fetch_json(url)
        except Exception as exc:  # noqa: BLE001
            failures.append({"direction_id": plan["direction_id"], "source_name": "Internet Archive", "error": str(exc)})
            continue
        raw_path = write_raw(f"{plan['direction_name']}.json", payload)
        docs = payload.get("response", {}).get("docs", []) if isinstance(payload.get("response"), dict) else []
        added = 0
        for doc in docs:
            row = ia_row(doc, plan, url, raw_path)
            if not row:
                continue
            key = (row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", ""))
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
            added += 1
            if added >= plan["limit"]:
                break
        time.sleep(0.5)
    return rows, failures


def naidoc_item_urls() -> list[str]:
    gallery_url = "https://www.naidoc.org.au/posters/poster-gallery"
    markup = fetch_text(gallery_url)
    parser = MetaParser()
    parser.feed(markup)
    found: dict[int, str] = {}
    for href, text in parser.links:
        full = urllib.parse.urljoin(gallery_url, href)
        year = terminal_year(f"{href} {text}") or terminal_year(full)
        if year and 2001 <= year <= 2026 and "/posters/poster-gallery/" in full:
            found[year] = full
    for year in range(2001, 2027):
        found.setdefault(year, f"https://www.naidoc.org.au/posters/poster-gallery/naidoc-{year}-poster")
    return [found[year] for year in range(2001, 2027)]


def naidoc_image(parser: MetaParser, url: str) -> str:
    for candidate in parser.images:
        full = urllib.parse.urljoin(url, candidate)
        lowered = full.lower()
        if "/sites/default/files/" not in lowered:
            continue
        if any(term in lowered for term in ("css_", "js_", "logo", "icon", "application-pdf", "image-x-generic")):
            continue
        if lowered.endswith((".jpg", ".jpeg", ".png", ".webp")):
            return full
    return ""


def naidoc_fields(markup: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    pattern = re.compile(
        r'<div class="field field--name-[^"]+ field--type-[^"]+ field--label-above">\s*'
        r'<h2 class="field__label">([^<]+)</h2>\s*'
        r'<div class="field__item">(.*?)</div>',
        re.S,
    )
    for label, value in pattern.findall(markup):
        fields[clean(label)] = strip_markup(value, max_chars=700)
    return fields


def naidoc_row(url: str, raw_path: str) -> dict[str, str] | None:
    markup = fetch_text(url)
    parser = MetaParser()
    parser.feed(markup)
    title = clean(parser.meta.get("og:title") or " ".join(parser.title_parts), max_chars=220)
    year = terminal_year(url + " " + title)
    if year is None or not (2001 <= year <= 2026) or "naidoc" not in title.lower():
        return None
    fields = naidoc_fields(markup)
    image_url = naidoc_image(parser, url)
    description = clean(
        parser.meta.get("description")
        or fields.get("Poster title")
        or fields.get("Artist")
        or f"{title} is an official NAIDOC poster-gallery item page.",
        max_chars=900,
    )
    rights = image_rights(
        "IMG02" if image_url else "IMG00",
        image_url,
        url,
        "NAIDOC exposes source-hosted poster images/download links; use source-viewer evidence only with Indigenous/community context and no local copy.",
    )
    row = {
        "capture_id": "",
        "direction_id": "LPNAIDOC01",
        "direction_name": "naidoc_contemporary_indigenous_poster_item_records",
        "source_id": "SRC136",
        "source_name": "NAIDOC Poster Gallery",
        "source_api_url": url,
        "capture_status": "captured",
        "source_identifier": f"naidoc-{year}",
        "source_record_url": url,
        "source_title": title.replace(" | NAIDOC", ""),
        "source_creator": fields.get("Artist", ""),
        "source_date_text": str(year),
        "date_start": str(year),
        "date_end": str(year),
        "source_place_text": "Australia / Indigenous",
        "source_object_type": "poster-object / official poster-gallery item",
        "source_medium": "poster / Indigenous public communication",
        "source_collection": "NAIDOC Poster Gallery",
        "source_description": description,
        "source_notes": fields.get("Poster title") or "Official NAIDOC poster-gallery item page.",
        "source_subjects": "NAIDOC; Aboriginal and Torres Strait Islander poster culture; Indigenous public graphics; contemporary public communication",
        "source_rights_text": "Rights and reuse are governed by NAIDOC/source terms; no local image copy.",
        "rights_uri": "https://www.naidoc.org.au/contact-us",
        "raw_json_path": raw_path,
        "access_date": ACCESS_DATE,
        **rights,
        "historical_context_note": "Contemporary NAIDOC annual posters document Indigenous public communication, commemoration, identity, and political-cultural visibility.",
        "classification_rationale": "Captured from the official NAIDOC poster gallery as item-level poster records; classify under Australia/Indigenous, poster medium, and NAIDOC/Indigenous public graphics.",
        "uncertainty_note": "Keep source return and avoid treating the image as project-owned.",
        "citation_basis": f"NAIDOC Poster Gallery. {title}. {url}. Accessed {ACCESS_DATE}.",
        "editorial_summary": clean(f"{title} is indexed from the official NAIDOC Poster Gallery. {description}", max_chars=700),
    }
    return row_defaults(row)


def capture_naidoc(seen: set[tuple[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    try:
        urls = naidoc_item_urls()
    except Exception as exc:  # noqa: BLE001
        return [], [{"direction_id": "LPNAIDOC01", "source_name": "NAIDOC Poster Gallery", "error": str(exc)}]
    for url in urls:
        try:
            raw_path = write_raw(f"naidoc_contemporary_{terminal_year(url) or len(rows)}.json", {"source": "NAIDOC Poster Gallery", "url": url})
            row = naidoc_row(url, raw_path)
            if row:
                key = (row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", ""))
                if key not in seen:
                    seen.add(key)
                    rows.append(row)
        except Exception as exc:  # noqa: BLE001
            failures.append({"direction_id": "LPNAIDOC01", "source_name": "NAIDOC Poster Gallery", "error": str(exc), "url": url})
        time.sleep(0.35)
    return rows, failures


def te_papa_search(term: str) -> list[dict[str, Any]]:
    url = "https://collections.tepapa.govt.nz/api/search?" + urllib.parse.urlencode({"search": term, "size": "24"})
    data = fetch_json(url)
    results = data.get("results") if isinstance(data, dict) else []
    return [item for item in results if item.get("type") == "Object"]


def te_papa_field(markup: str, field: str) -> str:
    pattern = rf'\\"{re.escape(field)}\\":\\"(.*?)(?<!\\)\\"'
    match = re.search(pattern, markup, re.S)
    if not match:
        return ""
    try:
        return json.loads(f'"{match.group(1)}"')
    except json.JSONDecodeError:
        return html.unescape(match.group(1))


def te_papa_row(item_id: int, raw_search: dict[str, Any]) -> dict[str, str] | None:
    url = f"https://collections.tepapa.govt.nz/object/{item_id}"
    markup = fetch_text(url)
    parser = MetaParser()
    parser.feed(markup)
    title = clean(parser.meta.get("og:title") or raw_search.get("title") or f"Te Papa object {item_id}", max_chars=220)
    title_l = title.lower()
    if not any(term in title_l for term in ("poster", "print", "flyer", "programme", "program")):
        return None
    year_text = te_papa_field(markup, "createdDate") or te_papa_field(markup, "verbatim") or clean(raw_search.get("publicationDate") or "")
    year = terminal_year(year_text + " " + title)
    if year is None or not (1970 <= year <= 2026):
        return None
    image_url = parser.meta.get("og:image") or te_papa_field(markup, "previewUrl")
    if "media.tepapa.govt.nz/collection/" not in image_url:
        image_url = ""
    description = strip_markup(te_papa_field(markup, "description"), max_chars=1200)
    if not description:
        description = clean(parser.meta.get("og:description") or f"{title} is indexed from Te Papa Collections Online.", max_chars=800)
    raw_path = write_raw(
        f"te_papa_late_object_{item_id}.json",
        {"source": "Te Papa Collections Online", "search_result": raw_search, "url": url, "html_excerpt": markup[:14000]},
    )
    rights = image_rights(
        "IMG02" if image_url else "IMG00",
        image_url,
        url,
        "Te Papa exposes source-hosted preview imagery when present; the page is treated as source-viewer evidence, not reusable image stock.",
    )
    row = {
        "capture_id": "",
        "direction_id": "LPTEPAPA01",
        "direction_name": "te_papa_late_aotearoa_poster_and_public_graphics",
        "source_id": "SRC138",
        "source_name": "Te Papa Collections Online",
        "source_api_url": url,
        "capture_status": "captured",
        "source_identifier": str(item_id),
        "source_record_url": url,
        "source_title": title,
        "source_creator": clean(te_papa_field(markup, "contributor"), max_chars=220),
        "source_date_text": str(year),
        "date_start": str(year),
        "date_end": str(year),
        "source_place_text": "Aotearoa / New Zealand",
        "source_object_type": "poster-object / public graphic object",
        "source_medium": "poster / printed public communication",
        "source_collection": "Museum of New Zealand Te Papa Tongarewa",
        "source_description": description,
        "source_notes": clean(te_papa_field(markup, "title") or "Te Papa object record.", max_chars=900),
        "source_subjects": "Aotearoa poster culture; protest graphics; public communication; museum object record",
        "source_rights_text": "Record/image rights stated at source; review required before reuse.",
        "rights_uri": "https://www.tepapa.govt.nz/about/collections/all-te-papa-websites/copyright-and-terms-use",
        "raw_json_path": raw_path,
        "access_date": ACCESS_DATE,
        **rights,
        "historical_context_note": "Te Papa object records add Aotearoa/New Zealand public posters, protest graphics, and community visual communication to the late-period archive map.",
        "classification_rationale": "Captured from Te Papa object search using poster/protest/public communication terms; folder placement should privilege region, medium, and theme evidence.",
        "uncertainty_note": "Rights are source-specific and frequently restricted; display must remain source-hosted with source return.",
        "citation_basis": f"Te Papa Collections Online. {title}. {url}. Accessed {ACCESS_DATE}.",
        "editorial_summary": clean(f"{title} is indexed from Te Papa Collections Online. {description}", max_chars=700),
    }
    return row_defaults(row)


def capture_te_papa(seen: set[tuple[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    ids: dict[int, dict[str, Any]] = {}
    for term in TE_PAPA_TERMS:
        try:
            for item in te_papa_search(term):
                item_id = item.get("id")
                if isinstance(item_id, int):
                    ids.setdefault(item_id, item)
        except Exception as exc:  # noqa: BLE001
            failures.append({"direction_id": "LPTEPAPA01", "source_name": "Te Papa Collections Online", "error": str(exc), "url": term})
        time.sleep(0.35)
    for item_id, item in ids.items():
        if len(rows) >= 24:
            break
        try:
            row = te_papa_row(item_id, item)
            if row:
                key = (row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", ""))
                if key not in seen:
                    seen.add(key)
                    rows.append(row)
        except Exception as exc:  # noqa: BLE001
            failures.append({"direction_id": "LPTEPAPA01", "source_name": "Te Papa Collections Online", "error": str(exc), "url": str(item_id)})
        time.sleep(0.35)
    return rows, failures


def write_outputs(rows: list[dict[str, str]], failures: list[dict[str, str]]) -> None:
    rows.sort(key=lambda row: (int(row.get("date_end") or row.get("date_start") or 9999), row.get("source_name", ""), row.get("source_title", "")))
    output_rows: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=1):
        clean_row = dict(row)
        noise_decision = clean_row.pop("noise_filter_decision", "")
        noise_reason = clean_row.pop("noise_filter_reason", "")
        if noise_decision or noise_reason:
            note = clean_row.get("uncertainty_note", "")
            clean_row["uncertainty_note"] = clean(
                " | ".join(part for part in [note, f"Noise filter: {noise_decision} {noise_reason}".strip()] if part),
                max_chars=900,
            )
        clean_row["capture_id"] = f"LPC2026R{index:03d}"
        for field in FIELDNAMES:
            clean_row.setdefault(field, "")
        output_rows.append({field: clean_row.get(field, "") for field in FIELDNAMES})

    with RECORDS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(output_rows)

    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in output_rows:
        grouped[(row["direction_id"], row["source_name"])].append(row)

    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        fields = ["direction_id", "source_id", "source_name", "captured_count", "failure_count", "img00_count", "img01_count", "img02_count", "img03_count", "img04_count", "notes"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for direction_id, source_name in sorted(grouped):
            items = grouped[(direction_id, source_name)]
            counter = Counter(row["image_presence_code"] for row in items)
            writer.writerow(
                {
                    "direction_id": direction_id,
                    "source_id": items[0].get("source_id", ""),
                    "source_name": source_name,
                    "captured_count": len(items),
                    "failure_count": sum(1 for failure in failures if failure.get("direction_id") == direction_id and failure.get("source_name") == source_name),
                    "img00_count": counter.get("IMG00", 0),
                    "img01_count": counter.get("IMG01", 0),
                    "img02_count": counter.get("IMG02", 0),
                    "img03_count": counter.get("IMG03", 0),
                    "img04_count": counter.get("IMG04", 0),
                    "notes": "Late-period 1970-2026 coverage-first capture; records are retained as grouping/coverage evidence before final enrichment.",
                }
            )


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


def main() -> None:
    if RAW_DIR.exists():
        for stale_file in RAW_DIR.glob("*.json"):
            stale_file.unlink()
    DATA.mkdir(parents=True, exist_ok=True)
    seen = existing_keys()
    all_rows: list[dict[str, str]] = []
    all_failures: list[dict[str, str]] = []

    for capture in (capture_commons, capture_internet_archive, capture_naidoc, capture_te_papa):
        rows, failures = capture(seen)
        all_rows.extend(rows)
        all_failures.extend(failures)

    all_rows, noise_decisions = apply_noise_filter(all_rows)
    write_outputs(all_rows, all_failures)
    print(f"captured={len(all_rows)}")
    print(f"image_states={dict(Counter(row['image_presence_code'] for row in all_rows))}")
    print(f"noise_filter={dict(noise_decisions)}")
    print(f"sources={dict(Counter(row['source_name'] for row in all_rows))}")
    if all_failures:
        print(f"failures={len(all_failures)}")
        for failure in all_failures[:20]:
            print(f"- {failure.get('direction_id')}: {failure.get('source_name')} {failure.get('url', '')}: {failure.get('error')}")


if __name__ == "__main__":
    main()
