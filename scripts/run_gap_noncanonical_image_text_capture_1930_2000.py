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


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_gap_noncanonical_image_text_1930_2000_raw"
RECORDS_CSV = DATA / "capture_batch_gap_noncanonical_image_text_1930_2000_records.csv"
SUMMARY_CSV = DATA / "capture_batch_gap_noncanonical_image_text_1930_2000_source_summary.csv"

ACCESS_DATE = "2026-05-31"
USER_AGENT = "ModernGDHistory/0.1 gap-noncanonical-image-text-capture"
FIELDNAMES = mx.FIELDNAMES

TE_PAPA_TERMS = [
    "Second World War poster",
    "anti nuclear poster",
    "protest poster",
    "Māori poster",
    "Pacific poster",
    "gay rights poster",
    "women poster",
    "Aotearoa poster",
]
TE_PAPA_MAX_ROWS = 32

NAIDOC_YEARS = [
    1974,
    1976,
    1977,
    1978,
    1979,
    1980,
    1981,
    1982,
    1983,
    1984,
    1985,
    1986,
    1987,
    1988,
    1989,
    1990,
    1991,
    1992,
    1993,
    1994,
    1995,
    1996,
    1997,
    1998,
    1999,
    2000,
]


class MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}
        self.images: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.in_title = False
        self.in_a = False
        self.current_href = ""
        self.title_parts: list[str] = []
        self.link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "title":
            self.in_title = True
        if tag.lower() == "a":
            self.in_a = True
            self.current_href = attrs_dict.get("href", "")
            self.link_text = []
        if tag.lower() == "meta":
            key = (attrs_dict.get("property") or attrs_dict.get("name") or "").lower()
            content = attrs_dict.get("content") or ""
            if key and content:
                self.meta[key] = html.unescape(content)
        if tag.lower() in {"img", "source"}:
            for attr in ("src", "data-src", "srcset"):
                value = attrs_dict.get(attr)
                if value:
                    self.images.append(html.unescape(value.split()[0]))

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False
        if tag.lower() == "a" and self.in_a:
            self.links.append((self.current_href, " ".join(self.link_text)))
            self.in_a = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.in_a:
            self.link_text.append(data)


def clean(value: Any, *, max_chars: int = 900) -> str:
    text = html.unescape(re.sub(r"\s+", " ", str(value or "")).strip())
    return text[:max_chars]


def strip_markup(value: str, *, max_chars: int = 900) -> str:
    decoded = html.unescape(value or "")
    decoded = re.sub(r"(?is)<(script|style).*?</\1>", " ", decoded)
    decoded = re.sub(r"(?s)<[^>]+>", " ", decoded)
    return clean(decoded, max_chars=max_chars)


def decode_json_string(fragment: str) -> str:
    if not fragment:
        return ""
    try:
        return json.loads(f'"{fragment}"')
    except json.JSONDecodeError:
        return html.unescape(fragment)


def fetch(url: str, *, accept: str = "text/html,application/xhtml+xml,application/json") -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(req, timeout=24) as response:
        return response.read()


def fetch_text(url: str) -> str:
    return fetch(url).decode("utf-8", errors="replace")


def write_raw(name: str, payload: dict[str, Any]) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path.relative_to(ROOT))


def existing_urls() -> set[str]:
    urls: set[str] = set()
    for path in DATA.glob("capture_batch_*_records.csv"):
        if path == RECORDS_CSV:
            continue
        if not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                url = row.get("source_record_url") or ""
                if url:
                    urls.add(url.rstrip("/"))
    return urls


def year_from_text(value: str) -> int | None:
    years = [int(year) for year in re.findall(r"(?<!\d)((?:19|20)\d{2})(?!\d)", value or "")]
    years = [year for year in years if 1930 <= year <= 2000]
    return min(years) if years else None


def image_rights(code: str, image_url: str, viewer: str, basis: str) -> dict[str, str]:
    return mc.image_fields(
        code,
        basis,
        image_url=image_url,
        viewer=viewer,
        confidence="high" if image_url else "medium",
        rights_review_required=True,
        local_copy_permitted=False,
        note="Source-hosted display only; no local image copy or ownership claim.",
    )


def row_defaults(row: dict[str, str]) -> dict[str, str]:
    row["image_expectation"] = "expected" if row.get("image_presence_code") != "IMG04" else "not_expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["source_description_raw"] = row.get("source_description", "")
    row["ocr_or_excerpt"] = row.get("source_description", "")
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def te_papa_search(term: str) -> list[dict[str, Any]]:
    url = "https://collections.tepapa.govt.nz/api/search?" + urllib.parse.urlencode({"search": term, "size": "24"})
    data = json.loads(fetch(url, accept="application/json").decode("utf-8"))
    results = data.get("results") if isinstance(data, dict) else []
    return [item for item in results if item.get("type") == "Object"]


def extract_te_papa_field(markup: str, field: str) -> str:
    pattern = rf'\\"{re.escape(field)}\\":\\"(.*?)(?<!\\)\\"'
    match = re.search(pattern, markup, re.S)
    return decode_json_string(match.group(1)) if match else ""


def extract_te_papa_object(item_id: int, raw_search: dict[str, Any]) -> dict[str, str] | None:
    url = f"https://collections.tepapa.govt.nz/object/{item_id}"
    markup = fetch_text(url)
    parser = MetaParser()
    parser.feed(markup)
    title = clean(parser.meta.get("og:title") or raw_search.get("title") or f"Te Papa object {item_id}", max_chars=220)
    title_l = title.lower()
    if "poster" not in title_l and "print" not in title_l:
        return None
    year_text = (
        extract_te_papa_field(markup, "createdDate")
        or extract_te_papa_field(markup, "verbatim")
        or clean(raw_search.get("publicationDate") or "")
    )
    year = year_from_text(year_text + " " + title)
    if year is None or not (1930 <= year <= 2000):
        return None
    image_url = parser.meta.get("og:image") or extract_te_papa_field(markup, "previewUrl")
    if "media.tepapa.govt.nz/collection/" not in image_url:
        image_url = ""
    description = strip_markup(extract_te_papa_field(markup, "description"), max_chars=1200)
    if not description:
        description = clean(parser.meta.get("og:description") or f"{title} is indexed from Te Papa Collections Online.", max_chars=800)
    if len(description) < 80 or not image_url:
        return None
    creator = clean(extract_te_papa_field(markup, "contributor").split('"title":"')[-1].split('"')[0] if '"title":"' in extract_te_papa_field(markup, "contributor") else "")
    production_title = extract_te_papa_field(markup, "title")
    rights_match = re.search(r'\\"rights\\":\{\\"type\\":\\"Right\\",\\"title\\":\\"(.*?)(?<!\\)\\"', markup, re.S)
    rights_title = decode_json_string(rights_match.group(1)) if rights_match else ""
    raw_path = write_raw(
        f"te_papa_object_{item_id}.json",
        {"source": "Te Papa Collections Online", "search_result": raw_search, "url": url, "html_excerpt": markup[:14000]},
    )
    rights = image_rights(
        "IMG02" if image_url else "IMG00",
        image_url,
        url,
        "Te Papa exposes a source-hosted preview image; the page is treated as restricted/source-viewer evidence, not reusable image stock.",
    )
    row = {
        "capture_id": "",
        "direction_id": "GAP01",
        "direction_name": "te_papa_aotearoa_poster_and_public_graphics",
        "source_id": "SRC138",
        "source_name": "Te Papa Collections Online",
        "source_api_url": url,
        "capture_status": "captured",
        "source_identifier": str(item_id),
        "source_record_url": url,
        "source_title": title,
        "source_creator": creator,
        "source_date_text": str(year),
        "date_start": str(year),
        "date_end": str(year),
        "source_place_text": "Aotearoa / New Zealand",
        "source_object_type": "poster-object / public graphic object",
        "source_medium": "poster / printed public communication",
        "source_collection": "Museum of New Zealand Te Papa Tongarewa",
        "source_description": description,
        "source_notes": clean(production_title or "Te Papa object record.", max_chars=900),
        "source_subjects": "Aotearoa poster culture; protest graphics; public communication; museum object record",
        "source_rights_text": clean(rights_title or "Record/image rights stated at source; review required before reuse."),
        "rights_uri": "https://www.tepapa.govt.nz/about/collections/all-te-papa-websites/copyright-and-terms-use",
        "raw_json_path": raw_path,
        "access_date": ACCESS_DATE,
        **rights,
        "historical_context_note": (
            "Te Papa object records extend the index beyond European/North American museum canons by adding Aotearoa/New Zealand "
            "public posters, protest graphics, music-publicity print, and community visual communication."
        ),
        "classification_rationale": (
            "Captured from Te Papa object search using poster/protest/public communication terms; folder placement should privilege "
            "region, medium, and movement/theme evidence from title, date, place, and source description."
        ),
        "uncertainty_note": "Rights are source-specific and frequently restricted; display must remain source-hosted with source return.",
        "citation_basis": f"Te Papa Collections Online. {title}. {url}. Accessed {ACCESS_DATE}.",
        "editorial_summary": clean(f"{title} is indexed from Te Papa Collections Online. {description}", max_chars=700),
    }
    return row_defaults(row)


def naidoc_links() -> list[str]:
    gallery_url = "https://www.naidoc.org.au/posters/poster-gallery"
    markup = fetch_text(gallery_url)
    parser = MetaParser()
    parser.feed(markup)
    found: dict[int, str] = {}
    for href, text in parser.links:
        full = urllib.parse.urljoin(gallery_url, href)
        blob = f"{href} {text}"
        year = year_from_text(blob)
        if year in NAIDOC_YEARS and "/posters/poster-gallery/" in full:
            found[year] = full
    for year in NAIDOC_YEARS:
        found.setdefault(year, f"https://www.naidoc.org.au/posters/poster-gallery/naidoc-{year}-poster")
    return [found[year] for year in NAIDOC_YEARS]


def choose_naidoc_image(parser: MetaParser, url: str) -> str:
    candidates: list[str] = []
    candidates.extend(parser.images)
    for candidate in candidates:
        full = urllib.parse.urljoin(url, candidate)
        lowered = full.lower()
        if "/sites/default/files/" not in lowered:
            continue
        if any(term in lowered for term in ("css_", "js_", "logo", "icon", "application-pdf", "image-x-generic")):
            continue
        if lowered.endswith((".jpg", ".jpeg", ".png", ".webp")):
            return full
    return ""


def extract_naidoc_description(markup: str, parser: MetaParser, title: str) -> str:
    desc = clean(parser.meta.get("description") or parser.meta.get("og:description"), max_chars=1000)
    if desc:
        return desc
    fields = extract_naidoc_fields(markup)
    parts = []
    for label in ("Poster title", "Artist"):
        if fields.get(label):
            parts.append(f"{label}: {fields[label]}")
    alt = extract_naidoc_image_alt(markup)
    if alt:
        parts.append(f"Image description: {alt}")
    if parts:
        return clean("; ".join(parts), max_chars=1000)
    return clean(f"{title} is an official NAIDOC poster-gallery item page.", max_chars=500)


def extract_naidoc_fields(markup: str) -> dict[str, str]:
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


def extract_naidoc_image_alt(markup: str) -> str:
    match = re.search(r'<img[^>]+/sites/default/files/images/photo-gallery-items/[^>]+alt="([^"]*)"', markup, re.I)
    return clean(match.group(1), max_chars=700) if match else ""


def extract_naidoc_year(url: str, title: str) -> int | None:
    return year_from_text(url + " " + title)


def extract_naidoc_object(url: str) -> dict[str, str] | None:
    markup = fetch_text(url)
    parser = MetaParser()
    parser.feed(markup)
    title = clean(parser.meta.get("og:title") or " ".join(parser.title_parts), max_chars=220)
    if not title or "naidoc" not in title.lower():
        return None
    year = extract_naidoc_year(url, title)
    if year is None or not (1974 <= year <= 2000):
        return None
    image_url = choose_naidoc_image(parser, url)
    fields = extract_naidoc_fields(markup)
    description = extract_naidoc_description(markup, parser, title)
    raw_path = write_raw(
        f"naidoc_poster_{year}.json",
        {"source": "NAIDOC Poster Gallery", "url": url, "html_excerpt": markup[:14000]},
    )
    rights = image_rights(
        "IMG02" if image_url else "IMG00",
        image_url,
        url,
        "NAIDOC exposes source-hosted poster images/download links; the index treats them as source-viewer evidence with Indigenous/community context and no local copy.",
    )
    row = {
        "capture_id": "",
        "direction_id": "GAP02",
        "direction_name": "naidoc_indigenous_poster_item_records",
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
        "source_notes": clean(fields.get("Poster title") or "Official NAIDOC poster-gallery item page; display source-hosted image only.", max_chars=900),
        "source_subjects": "NAIDOC; Aboriginal and Torres Strait Islander poster culture; Indigenous public graphics; annual public communication",
        "source_rights_text": "Rights and reuse are governed by NAIDOC/source terms; no local image copy.",
        "rights_uri": "https://www.naidoc.org.au/contact-us",
        "raw_json_path": raw_path,
        "access_date": ACCESS_DATE,
        **rights,
        "historical_context_note": (
            "NAIDOC annual posters document Indigenous public communication, identity, commemoration, and political-cultural visibility. "
            "They are treated as source-linked records with cultural and rights caution."
        ),
        "classification_rationale": (
            "Captured from the official NAIDOC poster gallery as item-level poster records; classify under Australia/Indigenous, poster medium, "
            "and Aboriginal land-rights/NAIDOC poster culture where applicable."
        ),
        "uncertainty_note": "Some older item pages provide sparse text; keep source return and avoid treating the image as project-owned.",
        "citation_basis": f"NAIDOC Poster Gallery. {title}. {url}. Accessed {ACCESS_DATE}.",
        "editorial_summary": clean(f"{title} is indexed from the official NAIDOC Poster Gallery. {description}", max_chars=700),
    }
    return row_defaults(row)


def main() -> None:
    if RAW_DIR.exists():
        for stale_file in RAW_DIR.glob("*.json"):
            stale_file.unlink()
    seen = existing_urls()
    seen_titles: set[str] = set()
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    te_papa_ids: dict[int, dict[str, Any]] = {}

    for term in TE_PAPA_TERMS:
        try:
            for item in te_papa_search(term):
                item_id = item.get("id")
                if isinstance(item_id, int):
                    te_papa_ids.setdefault(item_id, item)
        except Exception as exc:  # noqa: BLE001
            failures.append({"direction_id": "GAP01", "source_name": "Te Papa Collections Online", "url": term, "error": str(exc)})
        time.sleep(0.35)

    for item_id, item in list(te_papa_ids.items()):
        if len([row for row in rows if row.get("direction_id") == "GAP01"]) >= TE_PAPA_MAX_ROWS:
            break
        url = f"https://collections.tepapa.govt.nz/object/{item_id}"
        if url.rstrip("/") in seen:
            continue
        try:
            row = extract_te_papa_object(item_id, item)
            if row:
                title_key = re.sub(r"\W+", " ", row["source_title"].lower()).strip()
                if title_key in seen_titles:
                    continue
                seen_titles.add(title_key)
                rows.append(row)
        except Exception as exc:  # noqa: BLE001
            failures.append({"direction_id": "GAP01", "source_name": "Te Papa Collections Online", "url": url, "error": str(exc)})
        time.sleep(0.35)

    for url in naidoc_links():
        if url.rstrip("/") in seen:
            continue
        try:
            row = extract_naidoc_object(url)
            if row:
                rows.append(row)
        except Exception as exc:  # noqa: BLE001
            failures.append({"direction_id": "GAP02", "source_name": "NAIDOC Poster Gallery", "url": url, "error": str(exc)})
        time.sleep(0.35)

    rows.sort(key=lambda row: (int(row.get("date_end") or row.get("date_start") or 9999), row.get("source_name", ""), row.get("source_title", "")))
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"GAPIT2026R{index:03d}"
        for field in FIELDNAMES:
            row.setdefault(field, "")

    retained_raw = {ROOT / row["raw_json_path"] for row in rows if row.get("raw_json_path")}
    for raw_file in RAW_DIR.glob("*.json"):
        if raw_file not in retained_raw:
            raw_file.unlink()

    with RECORDS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["direction_id"], row["source_name"])].append(row)

    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        fields = ["direction_id", "source_name", "captured_count", "failure_count", "img00_count", "img01_count", "img02_count", "img03_count", "img04_count", "notes"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for direction_id, source_name in sorted(grouped):
            items = grouped[(direction_id, source_name)]
            counter = Counter(row["image_presence_code"] for row in items)
            writer.writerow(
                {
                    "direction_id": direction_id,
                    "source_name": source_name,
                    "captured_count": len(items),
                    "failure_count": sum(1 for failure in failures if failure["direction_id"] == direction_id and failure["source_name"] == source_name),
                    "img00_count": counter.get("IMG00", 0),
                    "img01_count": counter.get("IMG01", 0),
                    "img02_count": counter.get("IMG02", 0),
                    "img03_count": counter.get("IMG03", 0),
                    "img04_count": counter.get("IMG04", 0),
                    "notes": "Gap capture for noncanonical source-linked image/text records; no local image copies.",
                }
            )

    print(f"captured={len(rows)}")
    print(f"image_states={dict(Counter(row['image_presence_code'] for row in rows))}")
    print(f"sources={dict(Counter(row['source_name'] for row in rows))}")
    if failures:
        print(f"failures={len(failures)}")
        for failure in failures[:20]:
            print(f"- {failure['source_name']} {failure['url']}: {failure['error']}")


if __name__ == "__main__":
    main()
