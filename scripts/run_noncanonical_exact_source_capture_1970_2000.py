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
RAW_DIR = DATA / "capture_batch_noncanonical_exact_sources_1970_2000_raw"
RECORDS_CSV = DATA / "capture_batch_noncanonical_exact_sources_1970_2000_records.csv"
SUMMARY_CSV = DATA / "capture_batch_noncanonical_exact_sources_1970_2000_source_summary.csv"

ACCESS_DATE = "2026-05-31"
USER_AGENT = "ModernGDHistory/0.1 exact-source-capture"
FIELDNAMES = mx.FIELDNAMES


TARGETS = [
    {
        "direction_id": "NXS01",
        "direction_name": "saha_medu_exact_records",
        "source_id": "SRC132",
        "source_name": "South African History Archive",
        "url": "https://www.saha.org.za/imagesofdefinace/december_16_heroes_day_2.htm",
        "title": "December 16: Heroes-Day",
        "date_start": "1983",
        "date_end": "1983",
        "place": "South Africa / Botswana",
        "object_type": "poster-object",
        "medium": "political poster / screenprint",
        "collection": "Images of Defiance / Medu-linked poster records",
        "subjects": "Medu Art Ensemble; anti-apartheid poster culture; Heroes Day",
        "context": "Exact SAHA poster page used to document Medu and anti-apartheid visual communication through a community/political archive.",
        "prefer_img": True,
    },
    {
        "direction_id": "NXS01",
        "direction_name": "saha_medu_exact_records",
        "source_id": "SRC132",
        "source_name": "South African History Archive",
        "url": "https://www.saha.org.za/imagesofdefinace/now_you_have_touched_the_women_you_have_struck_a_rock_you_have_dislodged_a_boulder_you_will_be_crushed_2.htm",
        "title": "Now You Have Touched the Women...",
        "date_start": "1982",
        "date_end": "1982",
        "place": "South Africa / Botswana",
        "object_type": "poster-object",
        "medium": "political poster / screenprint",
        "collection": "Images of Defiance / Medu-linked poster records",
        "subjects": "Medu Art Ensemble; anti-apartheid poster culture; women's resistance",
        "context": "Exact SAHA poster page used to document Medu, anti-apartheid visual communication, and women's resistance graphics.",
        "prefer_img": True,
    },
    {
        "direction_id": "NXS01",
        "direction_name": "saha_medu_exact_records",
        "source_id": "SRC132",
        "source_name": "South African History Archive",
        "url": "https://www.saha.org.za/imagesofdefinace/women_arise_organise_unite_for_peoples_power.htm",
        "title": "Women Arise: Organise, Unite for People's Power!",
        "date_start": "1986",
        "date_end": "1986",
        "place": "South Africa / Botswana",
        "object_type": "poster-object",
        "medium": "political poster / screenprint",
        "collection": "Images of Defiance / Medu-linked poster records",
        "subjects": "Medu Art Ensemble; anti-apartheid poster culture; women's resistance",
        "context": "Exact SAHA poster page used to document Medu-linked anti-apartheid poster production outside canonical museum collection routes.",
        "prefer_img": True,
    },
    {
        "direction_id": "NXS02",
        "direction_name": "wits_medu_context_records",
        "source_id": "SRC133",
        "source_name": "Wits Historical Papers",
        "url": "https://historicalpapers-atom.wits.ac.za/medu-4",
        "title": "MEDU cultural work portal",
        "date_start": "1978",
        "date_end": "1985",
        "place": "South Africa / Botswana",
        "object_type": "archive collection / finding aid",
        "medium": "archive finding aid / movement context",
        "collection": "Historical Papers Research Archive",
        "subjects": "Medu Art Ensemble; anti-apartheid cultural work; exile graphic production",
        "context": "Collection-level Wits record anchors Medu as an archive formation rather than only as isolated posters.",
        "prefer_img": False,
    },
    {
        "direction_id": "NXS03",
        "direction_name": "chile_brigadas_ramona_parra_records",
        "source_id": "SRC134",
        "source_name": "Biblioteca Nacional Digital de Chile / Memoria Chilena",
        "url": "https://www.bibliotecanacionaldigital.gob.cl/bnd/637/w3-article-156874.html",
        "title": "Murales Brigada Ramona Parra",
        "date_start": "1970",
        "date_end": "1970",
        "place": "Chile / Latin America",
        "object_type": "photographic record / mural documentation",
        "medium": "mural documentation / political wall graphics",
        "collection": "Biblioteca Nacional Digital de Chile",
        "subjects": "Brigadas Ramona Parra; Unidad Popular; mural graphics",
        "context": "BND Chile record documents Brigadas Ramona Parra as political wall-graphic practice rather than museum poster style.",
        "prefer_img": True,
    },
    {
        "direction_id": "NXS03",
        "direction_name": "chile_brigadas_ramona_parra_records",
        "source_id": "SRC134",
        "source_name": "Biblioteca Nacional Digital de Chile / Memoria Chilena",
        "url": "https://www.bibliotecanacionaldigital.gob.cl/bnd/649/w3-article-605531.html",
        "title": "Contra la dictadura ... pintaremos hasta el cielo!!",
        "date_start": "1980",
        "date_end": "1989",
        "place": "Chile / Latin America",
        "object_type": "poster-object",
        "medium": "political poster / print",
        "collection": "Biblioteca Nacional Digital de Chile",
        "subjects": "Brigadas Ramona Parra; anti-dictatorship graphics; Chilean political poster",
        "context": "BND Chile exact poster record extends the archive beyond canonical European poster narratives into Latin American political graphics.",
        "prefer_img": True,
    },
    {
        "direction_id": "NXS03",
        "direction_name": "chile_brigadas_ramona_parra_records",
        "source_id": "SRC134",
        "source_name": "Biblioteca Nacional Digital de Chile / Memoria Chilena",
        "url": "https://www.memoriachilena.gob.cl/602/w3-article-126078.html",
        "title": "Mural de la Brigada Ramona Parra",
        "date_start": "1983",
        "date_end": "1983",
        "place": "Chile / Latin America",
        "object_type": "bibliography/image page",
        "medium": "mural documentation / political wall graphics",
        "collection": "Memoria Chilena",
        "subjects": "Brigadas Ramona Parra; mural graphics; Chilean political visual culture",
        "context": "Memoria Chilena image/bibliography record gives a local reference point for Brigadas Ramona Parra visual practice.",
        "prefer_img": True,
    },
    {
        "direction_id": "NXS04",
        "direction_name": "kdf_minjung_records",
        "source_id": "SRC135",
        "source_name": "Korea Democracy Foundation Open Archives",
        "url": "https://archives.kdemo.or.kr/isad/view/01015877",
        "title": "한국민중판화모음전 포스터",
        "date_start": "1980",
        "date_end": "1999",
        "place": "Korea",
        "object_type": "poster-object",
        "medium": "poster / Minjung print culture",
        "collection": "KDF Open Archives",
        "subjects": "Minjung art; Korean democracy movement; poster culture",
        "context": "KDF exact record is used to connect Korean Minjung print and poster practice to the archive graph.",
        "prefer_img": True,
    },
    {
        "direction_id": "NXS04",
        "direction_name": "kdf_minjung_records",
        "source_id": "SRC135",
        "source_name": "Korea Democracy Foundation Open Archives",
        "url": "https://archives.kdemo.or.kr/isad/view/00856377",
        "title": "광주의거자료집2-오월 그날이 다시오면",
        "date_start": "1987",
        "date_end": "1987",
        "place": "Korea",
        "object_type": "document / movement print",
        "medium": "movement publication / democratic struggle print culture",
        "collection": "KDF Open Archives",
        "subjects": "Minjung; Gwangju; Korean democracy movement; movement publication",
        "context": "KDF record supplies movement-publication context for Korean democratic visual culture.",
        "prefer_img": True,
    },
    {
        "direction_id": "NXS05",
        "direction_name": "naidoc_indigenous_poster_records",
        "source_id": "SRC136",
        "source_name": "NAIDOC / AIATSIS",
        "url": "https://www.naidoc.org.au/posters/poster-gallery",
        "title": "Official NAIDOC Poster Gallery",
        "date_start": "1972",
        "date_end": "2026",
        "place": "Australia / Indigenous",
        "object_type": "poster gallery / collection-level record",
        "medium": "poster gallery / Indigenous public graphics",
        "collection": "NAIDOC Poster Gallery",
        "subjects": "NAIDOC; Aboriginal and Torres Strait Islander poster culture; Indigenous public graphics",
        "context": "NAIDOC gallery is captured as a collection-level visual source for Indigenous poster history; individual posters need later item-level review.",
        "prefer_img": True,
    },
    {
        "direction_id": "NXS05",
        "direction_name": "naidoc_indigenous_poster_records",
        "source_id": "SRC136",
        "source_name": "NAIDOC / AIATSIS",
        "url": "https://aiatsis.gov.au/collection/featured-collections/naidoc-week-posters",
        "title": "AIATSIS NAIDOC Week posters collection",
        "date_start": "1972",
        "date_end": "2026",
        "place": "Australia / Indigenous",
        "object_type": "collection-level record",
        "medium": "poster collection / Indigenous public graphics",
        "collection": "AIATSIS Featured Collections",
        "subjects": "NAIDOC; AIATSIS; Indigenous poster history",
        "context": "AIATSIS collection page is used as an authority/context record for NAIDOC poster history.",
        "prefer_img": True,
    },
    {
        "direction_id": "NXS06",
        "direction_name": "roots_singapore_multilingual_graphics",
        "source_id": "SRC137",
        "source_name": "Roots.sg / National Heritage Board Singapore",
        "url": "https://www.roots.gov.sg/Collection-Landing/listing/1239614",
        "title": "Street sign of Jalan Pisang",
        "date_start": "1930",
        "date_end": "1970",
        "place": "Singapore",
        "object_type": "street sign object",
        "medium": "multilingual sign / urban graphic object",
        "collection": "National Museum of Singapore",
        "subjects": "Singapore multilingual public graphics; street signage; urban visual communication",
        "context": "Roots.sg object record adds multilingual public signage and urban graphic systems to the archive graph.",
        "prefer_img": True,
    },
    {
        "direction_id": "NXS06",
        "direction_name": "roots_singapore_multilingual_graphics",
        "source_id": "SRC137",
        "source_name": "Roots.sg / National Heritage Board Singapore",
        "url": "https://www.roots.gov.sg/collection-landing/listing/1238399",
        "title": "Street sign of River Valley Road in Mandarin",
        "date_start": "1930",
        "date_end": "1970",
        "place": "Singapore",
        "object_type": "street sign object",
        "medium": "multilingual sign / urban graphic object",
        "collection": "National Museum of Singapore",
        "subjects": "Singapore multilingual public graphics; Chinese-language signage; urban visual communication",
        "context": "Roots.sg object record supports regional graphic design history through everyday signage and multilingual public typography.",
        "prefer_img": True,
    },
]


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}
        self.images: list[str] = []
        self.in_title = False
        self.in_h1 = False
        self.title_parts: list[str] = []
        self.h1_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "title":
            self.in_title = True
        if tag.lower() == "h1":
            self.in_h1 = True
        if tag.lower() == "meta":
            key = (attrs_dict.get("property") or attrs_dict.get("name") or "").lower()
            content = attrs_dict.get("content") or ""
            if key and content:
                self.meta[key] = html.unescape(content)
        if tag.lower() == "img":
            src = attrs_dict.get("src") or attrs_dict.get("data-src") or attrs_dict.get("data-original") or ""
            if src:
                self.images.append(html.unescape(src))

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False
        if tag.lower() == "h1":
            self.in_h1 = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.in_h1:
            self.h1_parts.append(data)


def clean(value: Any, *, max_chars: int = 900) -> str:
    text = html.unescape(re.sub(r"\s+", " ", str(value or "")).strip())
    return text[:max_chars]


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    with urllib.request.urlopen(req, timeout=18) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


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


def text_excerpt(markup: str, *, max_chars: int = 800) -> str:
    no_scripts = re.sub(r"(?is)<(script|style).*?</\1>", " ", markup)
    text = re.sub(r"(?s)<[^>]+>", " ", no_scripts)
    return clean(text, max_chars=max_chars)


def absolute_url(url: str, base: str) -> str:
    return urllib.parse.urljoin(base, url)


def usable_image(url: str) -> bool:
    lowered = url.lower()
    if not lowered.startswith(("http://", "https://")):
        return False
    blocked = (
        "blank",
        "circle-close",
        "close-menu",
        "contribute",
        "facebook",
        "favicon",
        "hamburger",
        "header",
        "icon",
        "instagram",
        "loading",
        "logo",
        "menu",
        "next.",
        "placeholder",
        "previous.",
        "search",
        "sprite",
        "transparent",
        "twitter",
    )
    if any(term in lowered for term in blocked):
        return False
    if "/themes/custom/" in lowered:
        return False
    return lowered.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))


def choose_image(parser: PageParser, base_url: str) -> str:
    candidates = [
        parser.meta.get("og:image", ""),
        parser.meta.get("twitter:image", ""),
        parser.meta.get("twitter:image:src", ""),
    ]
    candidates.extend(parser.images[:16])
    preferred: list[str] = []
    fallback: list[str] = []
    for candidate in candidates:
        if not candidate:
            continue
        image_url = absolute_url(candidate, base_url)
        if not usable_image(image_url):
            continue
        lowered = image_url.lower()
        if any(term in lowered for term in ("preview", "full", "thumbnail", "thumb", "articles-")):
            preferred.append(image_url)
        else:
            fallback.append(image_url)
    return (preferred or fallback or [""])[0]


def is_error_page(markup: str, parser: PageParser) -> bool:
    title = clean(" ".join(parser.title_parts)).lower()
    blob = markup[:3000].lower()
    return "error page" in title or "404 error" in blob or "페이지가 존재하지 않습니다" in blob


def source_title(parser: PageParser, target: dict[str, str]) -> str:
    h1 = clean(" ".join(parser.h1_parts), max_chars=220)
    title = clean(parser.meta.get("og:title") or " ".join(parser.title_parts), max_chars=220)
    for candidate in [h1, title, target["title"]]:
        if candidate and len(candidate) > 4:
            return candidate
    return target["title"]


def source_description(parser: PageParser, target: dict[str, str], markup: str) -> str:
    desc = clean(parser.meta.get("og:description") or parser.meta.get("description"), max_chars=900)
    if desc and desc.lower() not in {"home", "homepage"}:
        return desc
    excerpt = text_excerpt(markup, max_chars=850)
    if len(excerpt) > 80:
        return excerpt
    return target["context"]


def row_from_target(target: dict[str, str], markup: str, raw_path: str) -> dict[str, str]:
    parser = PageParser()
    parser.feed(markup)
    if is_error_page(markup, parser):
        raise ValueError("source returned an error page rather than the target record")
    title = source_title(parser, target)
    description = source_description(parser, target, markup)
    image_url = choose_image(parser, target["url"]) if target.get("prefer_img") else ""

    if image_url:
        basis = (
            "Source page exposes a source-hosted preview image. This is treated as IMG02 "
            "for framed source viewing only; no local copy or reuse claim is made."
        )
        rights = mc.image_fields(
            "IMG02",
            basis,
            image_url=image_url,
            viewer=target["url"],
            confidence="medium",
            rights_review_required=True,
            local_copy_permitted=False,
            note="Use source-hosted preview only with visible source return and rights/context note.",
        )
        image_expectation = "expected"
    else:
        basis = (
            "No reliable source-hosted image was extracted by the exact-page parser; "
            "retain as a text/context record with source return."
        )
        rights = mc.image_fields(
            "IMG04",
            basis,
            viewer=target["url"],
            confidence="medium",
            rights_review_required=False,
            local_copy_permitted=False,
            note="Text/context record; no image frame requested for this page.",
        )
        image_expectation = "not_expected"

    row = {
        "capture_id": "",
        "direction_id": target["direction_id"],
        "direction_name": target["direction_name"],
        "source_id": target["source_id"],
        "source_name": target["source_name"],
        "source_api_url": target["url"],
        "capture_status": "captured",
        "source_identifier": target["url"],
        "source_record_url": target["url"],
        "source_title": title,
        "source_creator": "",
        "source_date_text": f"{target['date_start']}-{target['date_end']}" if target["date_start"] != target["date_end"] else target["date_start"],
        "date_start": target["date_start"],
        "date_end": target["date_end"],
        "source_place_text": target["place"],
        "source_object_type": target["object_type"],
        "source_medium": target["medium"],
        "source_collection": target["collection"],
        "source_description": description,
        "source_notes": target["context"],
        "source_subjects": target["subjects"],
        "source_rights_text": rights["source_rights_text"],
        "rights_uri": "",
        "raw_json_path": raw_path,
        "access_date": ACCESS_DATE,
        **rights,
    }
    row["image_expectation"] = image_expectation
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["source_description_raw"] = description
    row["ocr_or_excerpt"] = description
    row["historical_context_note"] = target["context"]
    row["classification_rationale"] = (
        "Exact-source capture from a preselected noncanonical movement/community source. "
        "Folder placement derives from the target source, title, date, place, subjects, and source context."
    )
    row["uncertainty_note"] = (
        "Exact page metadata may be incomplete or institution-specific; keep the source link visible and treat "
        "image display as source-hosted evidence rather than project-owned reproduction."
    )
    row["citation_basis"] = f"{target['source_name']}. {title}. {target['url']}. Accessed {ACCESS_DATE}."
    row["editorial_summary"] = clean(f"{title} is indexed from {target['source_name']}. {description}", max_chars=700)
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def main() -> None:
    seen = existing_urls()
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    for target in TARGETS:
        if target["url"].rstrip("/") in seen:
            continue
        try:
            markup = fetch_html(target["url"])
        except Exception as exc:  # noqa: BLE001
            failures.append({"direction_id": target["direction_id"], "source_name": target["source_name"], "error": str(exc), "url": target["url"]})
            continue
        safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", target["direction_name"] + "_" + target["title"].lower()).strip("_")
        raw_path = write_raw(
            f"{safe_name}.json",
            {
                "url": target["url"],
                "target": target,
                "html_excerpt": markup[:12000],
            },
        )
        try:
            rows.append(row_from_target(target, markup, raw_path))
        except Exception as exc:  # noqa: BLE001
            failures.append({"direction_id": target["direction_id"], "source_name": target["source_name"], "error": str(exc), "url": target["url"]})
        time.sleep(0.5)

    rows.sort(key=lambda row: (int(row.get("date_end") or row.get("date_start") or 9999), row.get("source_title", "")))
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"NXS2026R{index:03d}"
        for field in FIELDNAMES:
            row.setdefault(field, "")

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
        plan_keys = sorted({(target["direction_id"], target["source_id"], target["source_name"]) for target in TARGETS})
        for direction_id, source_id, source_name in plan_keys:
            items = grouped.get((direction_id, source_id, source_name), [])
            counter = Counter(row["image_presence_code"] for row in items)
            writer.writerow(
                {
                    "direction_id": direction_id,
                    "source_id": source_id,
                    "source_name": source_name,
                    "captured_count": len(items),
                    "failure_count": sum(1 for failure in failures if failure["direction_id"] == direction_id and failure["source_name"] == source_name),
                    "img00_count": counter.get("IMG00", 0),
                    "img01_count": counter.get("IMG01", 0),
                    "img02_count": counter.get("IMG02", 0),
                    "img03_count": counter.get("IMG03", 0),
                    "img04_count": counter.get("IMG04", 0),
                    "notes": "Exact source-page capture for noncanonical movement/community archive coverage.",
                }
            )

    print(f"captured={len(rows)}")
    print(f"image_states={dict(Counter(row['image_presence_code'] for row in rows))}")
    if failures:
        print(f"failures={len(failures)}")
        for failure in failures:
            print(f"- {failure['source_name']} {failure['url']}: {failure['error']}")


if __name__ == "__main__":
    main()
