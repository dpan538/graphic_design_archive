#!/usr/bin/env python3
"""Capture edge design sources through RSS/Atom plus page metadata.

This adapter is for post-1970 independent, professional, or community design
sources that expose feeds but not clean object APIs. Rows are source/context
records: images stay source-hosted (`IMG02`) and dates are source-record dates
unless the page metadata gives clearer item-level evidence.
"""

from __future__ import annotations

import csv
import email.utils
import html
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import run_midcentury_capture_1930_1970 as mc
import run_midcentury_expansion_capture_1931_1970 as mx
from contemporary_noise_filter import evaluate_record


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_edge_rss_html_1970_2026_raw"
RECORDS_CSV = DATA / "capture_batch_edge_rss_html_1970_2026_records.csv"
SUMMARY_CSV = DATA / "capture_batch_edge_rss_html_1970_2026_source_summary.csv"

ACCESS_DATE = "2026-06-02"
USER_AGENT = "ModernGDHistory/0.1 edge-rss-html-capture"
FIELDNAMES = mx.FIELDNAMES
YEAR_START = 1970
YEAR_END = 2026

SECRET_PATTERNS = (
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"(?i)(key=)[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key[\"'\s:=]+)[0-9A-Za-z_-]{20,}"),
    re.compile(r"\bgh[pousr]_[0-9A-Za-z_]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
)

DESIGN_TERMS = (
    "poster",
    "typography",
    "type",
    "lettering",
    "graphic",
    "identity",
    "logo",
    "publication",
    "editorial",
    "design",
    "visual",
    "archive",
    "exhibition",
    "print",
    "signage",
    "branding",
    "font",
    "typeface",
    "book",
    "magazine",
    "ephemera",
    "広告",
    "ポスター",
    "タイポグラフィ",
    "デザイン",
)


@dataclass(frozen=True)
class FeedSource:
    source_id: str
    source_name: str
    feed_url: str
    default_place: str
    macro_region: str
    direction_id: str
    max_records: int = 10


SOURCES: tuple[FeedSource, ...] = (
    FeedSource("ERS001", "JAGDA", "https://www.jagda.or.jp/feed/", "Japan", "East Asia", "ERS01", 10),
    FeedSource("ERS002", "Tokyo TDC", "https://tokyotypedirectorsclub.org/feed/", "Japan", "East Asia", "ERS02", 10),
    FeedSource("ERS003", "Fonts In Use", "https://fontsinuse.com/feed", "global", "Global", "ERS03", 12),
    FeedSource("ERS004", "People's Graphic Design Archive", "https://peoplesgdarchive.org/feed/", "global/community", "Global", "ERS04", 10),
    FeedSource("ERS005", "M+ Magazine", "https://www.mplus.org.hk/en/magazine/rss.xml", "Hong Kong", "East Asia", "ERS05", 10),
    FeedSource("ERS006", "BiblioAsia", "https://biblioasia.nlb.gov.sg/feed/", "Singapore", "Southeast Asia", "ERS06", 8),
    FeedSource("ERS007", "Design Reviewed", "https://www.designreviewed.com/feed/", "United Kingdom / global", "Europe", "ERS07", 8),
    FeedSource("ERS008", "Another Graphic", "https://anothergraphic.org/feed/", "post-1990 international", "Global", "ERS08", 8),
)


class PageMetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}
        self.title_parts: list[str] = []
        self.in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k.lower(): v or "" for k, v in attrs}
        if tag.lower() == "title":
            self.in_title = True
        if tag.lower() == "meta":
            key = (attrs_dict.get("property") or attrs_dict.get("name") or "").lower()
            content = attrs_dict.get("content") or ""
            if key and content:
                self.meta[key] = html.unescape(content)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)


def clean(value: Any, *, max_chars: int = 900) -> str:
    text = html.unescape(re.sub(r"\s+", " ", str(value or "")).strip())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rsplit(" ", 1)[0] + "..."


def strip_markup(value: str, *, max_chars: int = 900) -> str:
    value = re.sub(r"(?is)<(script|style).*?</\1>", " ", value or "")
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    return clean(value, max_chars=max_chars)


def redact(value: str) -> str:
    out = value
    for pattern in SECRET_PATTERNS:
        out = pattern.sub(lambda match: (match.group(1) if match.lastindex else "") + "[REDACTED_SECRET]", out)
    return out


def fetch_text(url: str, *, accept: str = "text/html,application/xhtml+xml,application/xml,*/*") -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(req, timeout=35) as response:
        return response.read().decode("utf-8", errors="replace")


def write_raw(name: str, text: str) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    path.write_text(redact(text), encoding="utf-8")
    return str(path.relative_to(ROOT))


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "record"


def first_year(value: str) -> str:
    years = [int(y) for y in re.findall(r"\b(19[7-9]\d|20[0-2]\d|2026)\b", value or "")]
    years = [year for year in years if YEAR_START <= year <= YEAR_END]
    return str(max(years)) if years else ""


def year_from_pubdate(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = email.utils.parsedate_to_datetime(value)
    except Exception:
        return first_year(value)
    if YEAR_START <= parsed.year <= YEAR_END:
        return str(parsed.year)
    return ""


def page_meta(url: str, source: FeedSource, index: int) -> tuple[dict[str, str], str]:
    try:
        text = fetch_text(url)
    except Exception:
        return {}, ""
    raw_path = write_raw(f"{slug(source.source_name)}_page_{index:03d}.html.txt", text)
    parser = PageMetaParser()
    parser.feed(text)
    meta = dict(parser.meta)
    if parser.title_parts:
        meta.setdefault("title", clean(" ".join(parser.title_parts), max_chars=280))
    return meta, raw_path


def parse_feed(text: str) -> list[dict[str, str]]:
    root = ET.fromstring(text.encode("utf-8"))
    items: list[dict[str, str]] = []
    namespaces = {
        "atom": "http://www.w3.org/2005/Atom",
        "content": "http://purl.org/rss/1.0/modules/content/",
        "media": "http://search.yahoo.com/mrss/",
    }

    rss_items = root.findall(".//item")
    for item in rss_items:
        data = {
            "title": clean(item.findtext("title"), max_chars=280),
            "link": clean(item.findtext("link"), max_chars=900),
            "date": clean(item.findtext("pubDate") or item.findtext("{http://purl.org/dc/elements/1.1/}date"), max_chars=120),
            "description": strip_markup(item.findtext("description") or "", max_chars=1200),
            "content": strip_markup(item.findtext("content:encoded", namespaces=namespaces) or "", max_chars=1400),
            "image": "",
        }
        media = item.find("media:content", namespaces=namespaces) or item.find("media:thumbnail", namespaces=namespaces)
        if media is not None:
            data["image"] = clean(media.attrib.get("url"), max_chars=900)
        items.append(data)

    atom_entries = root.findall(".//atom:entry", namespaces)
    for entry in atom_entries:
        link = ""
        for link_el in entry.findall("atom:link", namespaces):
            if link_el.attrib.get("rel", "alternate") == "alternate":
                link = clean(link_el.attrib.get("href"), max_chars=900)
                break
        items.append(
            {
                "title": clean(entry.findtext("atom:title", namespaces=namespaces), max_chars=280),
                "link": link,
                "date": clean(entry.findtext("atom:updated", namespaces=namespaces) or entry.findtext("atom:published", namespaces=namespaces), max_chars=120),
                "description": strip_markup(entry.findtext("atom:summary", namespaces=namespaces) or "", max_chars=1200),
                "content": strip_markup(entry.findtext("atom:content", namespaces=namespaces) or "", max_chars=1400),
                "image": "",
            }
        )
    return items


def existing_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in DATA.glob("capture_batch_*_records.csv"):
        if path == RECORDS_CSV or not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                keys.add((row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", "")))
    return keys


def is_relevant(title: str, description: str, source: FeedSource) -> bool:
    blob = f"{title} {description} {source.source_name}".lower()
    return any(term.lower() in blob for term in DESIGN_TERMS)


def image_fields(image_url: str, viewer: str, basis: str) -> dict[str, str]:
    return mc.image_fields(
        "IMG02" if image_url else "IMG04",
        basis,
        image_url=image_url,
        viewer=viewer or image_url,
        confidence="high" if image_url else "medium",
        rights_review_required=True,
        local_copy_permitted=False,
        note="RSS/HTML edge-source capture keeps images source-hosted and requires item-level rights review.",
    )


def row_defaults(row: dict[str, str]) -> dict[str, str]:
    row["image_expectation"] = "not_expected" if row.get("image_presence_code") == "IMG04" else "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["ocr_or_excerpt"] = row.get("source_description", "")
    row["source_description_raw"] = row.get("source_description", "")
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def capture_source(source: FeedSource, seen: set[tuple[str, str]]) -> tuple[list[dict[str, str]], dict[str, str]]:
    rows: list[dict[str, str]] = []
    failures = 0
    try:
        feed_text = fetch_text(source.feed_url, accept="application/rss+xml,application/atom+xml,application/xml,text/xml,*/*")
    except Exception as exc:
        return [], {"source_id": source.source_id, "source_name": source.source_name, "captured_count": "0", "failure_count": "1", "notes": str(exc)[:220]}
    feed_raw = write_raw(f"{slug(source.source_name)}_feed.xml", feed_text)
    try:
        items = parse_feed(feed_text)
    except Exception as exc:
        return [], {"source_id": source.source_id, "source_name": source.source_name, "captured_count": "0", "failure_count": "1", "notes": f"feed parse error: {exc}"[:220]}

    for index, item in enumerate(items[:40], start=1):
        if len(rows) >= source.max_records:
            break
        link = item.get("link", "")
        if not link:
            continue
        key = (source.source_name, link)
        if key in seen:
            continue
        meta, raw_path = page_meta(link, source, index)
        time.sleep(0.3)
        title = clean(meta.get("og:title") or meta.get("twitter:title") or item.get("title"), max_chars=280)
        description = clean(
            meta.get("og:description") or meta.get("description") or item.get("description") or item.get("content"),
            max_chars=1500,
        )
        image_url = clean(meta.get("og:image") or meta.get("twitter:image") or item.get("image"), max_chars=900)
        date_text = item.get("date", "")
        year = first_year(f"{title} {description}") or year_from_pubdate(date_text)
        if not year or not is_relevant(title, description, source):
            continue
        image = image_fields(
            image_url,
            link,
            f"{source.source_name} RSS/HTML metadata. Image is source-hosted and rights review is required.",
        )
        row = row_defaults(
            {
                "capture_id": "",
                "direction_id": source.direction_id,
                "direction_name": f"{slug(source.source_name)}_rss_html_context_1970_2026",
                "source_id": source.source_id,
                "source_name": source.source_name,
                "source_api_url": source.feed_url,
                "capture_status": "captured",
                "source_identifier": link,
                "source_record_url": link,
                "source_title": title,
                "source_creator": "",
                "source_date_text": date_text or year,
                "date_start": year,
                "date_end": year,
                "source_place_text": source.default_place,
                "source_object_type": f"{source.source_name} source-context record",
                "source_medium": "source-context page; article; archive entry",
                "source_collection": source.source_name,
                "source_description": description,
                "source_notes": f"Captured via RSS/Atom feed and page metadata from {source.source_name}; raw feed: {feed_raw}.",
                "source_subjects": "graphic design; typography; poster; archive; visual culture",
                "source_rights_text": f"{source.source_name} source-hosted web page; no local image copy permitted by default.",
                "rights_uri": "",
                "raw_json_path": raw_path or feed_raw,
                "access_date": ACCESS_DATE,
                **image,
                "editorial_summary": clean(f"{title} is indexed from {source.source_name}. {description}", max_chars=850),
                "historical_context_note": clean(
                    f"{source.source_name} expands the archive toward {source.default_place} / {source.macro_region} independent or institutional design-source context.",
                    max_chars=620,
                ),
                "classification_rationale": "Captured from RSS/Atom plus page metadata and filtered by design, typography, poster, print, archive, or visual-culture terms.",
                "uncertainty_note": "This is a source-context record. The public date is usually the source page publication date unless stronger item-level dates appear in title/description.",
                "citation_basis": f"{source.source_name}. {title}. {link}. Accessed {ACCESS_DATE}.",
            }
        )
        decision = evaluate_record(row)
        if decision.decision not in {"include_candidate", "downgrade_candidate"}:
            continue
        row["uncertainty_note"] = clean(f"{row['uncertainty_note']} Noise filter: {decision.decision} — {decision.reason}", max_chars=520)
        rows.append(row)
        seen.add(key)

    summary = {
        "source_id": source.source_id,
        "source_name": source.source_name,
        "captured_count": str(len(rows)),
        "failure_count": str(failures),
        "notes": "RSS/HTML edge-source capture; source-context records only.",
    }
    return rows, summary


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    seen = existing_keys()
    rows: list[dict[str, str]] = []
    summaries: list[dict[str, str]] = []

    for source in SOURCES:
        source_rows, summary = capture_source(source, seen)
        summaries.append(summary)
        rows.extend(source_rows)

    rows.sort(key=lambda r: (int(r["date_start"]) if r.get("date_start", "").isdigit() else 9999, r.get("source_name", ""), r.get("source_title", "")))
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"ERS1970R{index:03d}"

    with RECORDS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        fields = ["source_id", "source_name", "captured_count", "failure_count", "img00_count", "img01_count", "img02_count", "img03_count", "img04_count", "notes"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        by_source = {summary["source_name"]: summary for summary in summaries}
        counters: dict[str, dict[str, int]] = {}
        for row in rows:
            counters.setdefault(row["source_name"], {"IMG00": 0, "IMG01": 0, "IMG02": 0, "IMG03": 0, "IMG04": 0})
            counters[row["source_name"]][row["image_presence_code"]] += 1
        for source in SOURCES:
            summary = by_source[source.source_name]
            counter = counters.get(source.source_name, {})
            writer.writerow(
                {
                    **summary,
                    "img00_count": str(counter.get("IMG00", 0)),
                    "img01_count": str(counter.get("IMG01", 0)),
                    "img02_count": str(counter.get("IMG02", 0)),
                    "img03_count": str(counter.get("IMG03", 0)),
                    "img04_count": str(counter.get("IMG04", 0)),
                }
            )

    print(f"{RECORDS_CSV.relative_to(ROOT)}: {len(rows)} rows")
    print("image distribution:", dict(sorted(Counter(row["image_presence_code"] for row in rows).items())))
    print(f"{SUMMARY_CSV.relative_to(ROOT)}: summary written")


if __name__ == "__main__":
    main()
