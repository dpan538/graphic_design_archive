#!/usr/bin/env python3
"""Capture image-bearing records from pre-surface non-mainstream source leads.

This converts reachable source leads into archive records only when a
source-hosted image route is visible from page metadata. It does not download
images. All promoted records are conservative IMG02, not IMG01/IMG03.
"""

from __future__ import annotations

import csv
import html
import json
import re
import socket
import time
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import run_midcentury_expansion_capture_1931_1970 as mx


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

RECORDS_CSV = DATA / "capture_batch_nonmainstream_item_image_2026_records.csv"
SUMMARY_CSV = DATA / "capture_batch_nonmainstream_item_image_2026_source_summary.csv"
REPORT = DOCS / "NONMAINSTREAM_ITEM_IMAGE_CAPTURE_2026_v1.md"

ACCESS_DATE = "2026-06-05"
USER_AGENT = "ModernGDHistory/0.1 nonmainstream-item-image-capture"
MAX_WORKERS = 18
TIMEOUT = 8
READ_BYTES = 180_000
FIELDNAMES = mx.FIELDNAMES

SUMMARY_FIELDS = [
    "source_id",
    "source_name",
    "macro_region",
    "country_or_region",
    "captured_records",
    "image_states",
    "next_item_capture_priority",
    "notes",
]


class ImageHeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.links: list[tuple[str, str]] = []
        self.json_ld: list[str] = []
        self.in_json_ld = False
        self._json_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = {key.lower(): value or "" for key, value in attrs}
        tag_l = tag.lower()
        if tag_l == "title":
            self.in_title = True
        elif tag_l == "meta":
            key = (attrs_d.get("property") or attrs_d.get("name") or "").lower()
            value = attrs_d.get("content", "")
            if key and value:
                self.meta[key] = html.unescape(value)
        elif tag_l == "link":
            rel = attrs_d.get("rel", "")
            href = attrs_d.get("href", "")
            if href:
                self.links.append((rel, href))
        elif tag_l == "script" and attrs_d.get("type", "").lower() == "application/ld+json":
            self.in_json_ld = True
            self._json_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag_l = tag.lower()
        if tag_l == "title":
            self.in_title = False
        elif tag_l == "script" and self.in_json_ld:
            self.in_json_ld = False
            text = "".join(self._json_parts).strip()
            if text:
                self.json_ld.append(text)

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        elif self.in_json_ld:
            self._json_parts.append(data)

    @property
    def title(self) -> str:
        return clean(" ".join(self.title_parts), max_chars=180)


def clean(value: Any, *, max_chars: int = 900) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(re.sub(r"\s+", " ", text).strip())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rsplit(" ", 1)[0] + "..."


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def existing_project_image_urls() -> set[str]:
    urls: set[str] = set()
    for path in sorted(DATA.glob("capture_batch_*_records.csv")):
        if path == RECORDS_CSV:
            continue
        for row in read_csv(path):
            image_url = clean(row.get("image_url_detected")).lower()
            if image_url:
                urls.add(image_url)
    return urls


def abs_url(base: str, value: str) -> str:
    value = clean(value, max_chars=500)
    if not value:
        return ""
    return urllib.parse.urljoin(base, value)


def usable_image_url(url: str) -> bool:
    url_l = url.lower()
    if not url_l.startswith(("http://", "https://")):
        return False
    reject_tokens = (
        "sprite",
        "tracking",
        "pixel",
        "analytics",
        "blank.gif",
        "favicon",
        "fav%20icon",
        "apple-touch-icon",
        "/apple-touch",
        "/logo",
        "logo-",
        "-logo",
        "logo.",
        "logo_",
        "_logo",
        "cropped-logo",
        "cropped-cropped",
        "32x32",
    )
    if any(token in url_l for token in reject_tokens):
        return False
    return any(ext in url_l for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg")) or "image" in url_l


def jsonld_images(parser: ImageHeadParser, base_url: str) -> list[str]:
    out: list[str] = []
    for payload in parser.json_ld:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            item = stack.pop()
            if isinstance(item, list):
                stack.extend(item)
                continue
            if not isinstance(item, dict):
                continue
            for key in ("image", "thumbnailUrl"):
                value = item.get(key)
                if isinstance(value, str):
                    out.append(abs_url(base_url, value))
                elif isinstance(value, dict):
                    content = value.get("url") or value.get("@id")
                    if content:
                        out.append(abs_url(base_url, str(content)))
                elif isinstance(value, list):
                    stack.extend(value)
            graph = item.get("@graph")
            if isinstance(graph, list):
                stack.extend(graph)
    return out


def image_candidates(parser: ImageHeadParser, base_url: str) -> list[tuple[str, str]]:
    candidates = [
        ("og:image", parser.meta.get("og:image", "")),
        ("og:image:secure_url", parser.meta.get("og:image:secure_url", "")),
        ("twitter:image", parser.meta.get("twitter:image", "")),
        ("twitter:image:src", parser.meta.get("twitter:image:src", "")),
    ]
    for rel, href in parser.links:
        rel_l = rel.lower()
        if "image_src" in rel_l:
            candidates.append((f"link:{rel}", href))
    for image in jsonld_images(parser, base_url):
        candidates.append(("jsonld:image", image))
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for basis, value in candidates:
        image_url = abs_url(base_url, value)
        if not usable_image_url(image_url) or image_url in seen:
            continue
        seen.add(image_url)
        out.append((basis, image_url))
    return out


def fetch_page(row: dict[str, str]) -> dict[str, str] | None:
    url = clean(row.get("final_url") or row.get("url"))
    if not url:
        return None
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.5",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            final_url = response.geturl()
            content_type = response.headers.get("content-type", "")
            blob = response.read(READ_BYTES)
    except Exception:
        return None
    parser = ImageHeadParser()
    parser.feed(blob.decode("utf-8", errors="ignore"))
    images = image_candidates(parser, final_url)
    if not images:
        return None
    basis, image_url = images[0]
    title = parser.title or clean(row.get("page_title")) or clean(row.get("source_name"))
    description = clean(
        parser.meta.get("description")
        or parser.meta.get("og:description")
        or parser.meta.get("twitter:description")
        or row.get("meta_description")
        or "",
        max_chars=700,
    )
    return {
        **row,
        "_capture_final_url": final_url,
        "_capture_content_type": clean(content_type, max_chars=140),
        "_capture_title": title,
        "_capture_description": description,
        "_image_url": image_url,
        "_image_basis": basis,
    }


def registry_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for path in sorted(DATA.glob("nonmainstream_source_success_registry_2026_v*.csv")):
        version = path.stem.rsplit("_", 1)[-1]
        for row in read_csv(path):
            if clean(row.get("source_success_status")) != "success":
                continue
            key = (clean(row.get("source_name")).lower(), clean(row.get("final_url") or row.get("url")).lower())
            if key in seen:
                continue
            seen.add(key)
            row = dict(row)
            row["_registry_version"] = version
            rows.append(row)
    priority_rank = {"P0 item/image adapter": 0, "P1 item/source adapter": 1, "P1 manual item capture": 2, "P2 source enrichment": 3}
    return sorted(
        rows,
        key=lambda row: (
            priority_rank.get(clean(row.get("next_item_capture_priority")), 9),
            clean(row.get("macro_region")),
            clean(row.get("country_or_region")),
            clean(row.get("source_name")),
        ),
    )


def capture_record(row: dict[str, str], index: int) -> dict[str, str]:
    capture_id = f"NMIIC2026R{index:04d}"
    source_name = clean(row.get("source_name"))
    title = clean(row.get("_capture_title")) or source_name
    source_url = clean(row.get("_capture_final_url") or row.get("final_url") or row.get("url"))
    image_url = clean(row.get("_image_url"))
    description = clean(row.get("_capture_description") or row.get("meta_description") or title)
    macro = clean(row.get("macro_region"))
    country = clean(row.get("country_or_region"))
    image_basis = clean(row.get("_image_basis"))
    rights_note = (
        "Source-hosted image route discovered in official page metadata. "
        "No image binary was downloaded; item-level rights review is still required."
    )
    base = {
        "capture_id": capture_id,
        "direction_id": "NMIIC01",
        "direction_name": "nonmainstream_item_image_capture_2026",
        "source_id": clean(row.get("source_success_id")),
        "source_name": source_name,
        "source_api_url": clean(row.get("url")),
        "capture_status": "captured",
        "source_identifier": clean(row.get("wikidata_qid")) or clean(row.get("source_success_id")),
        "source_record_url": source_url,
        "source_title": title,
        "source_creator": source_name,
        "source_date_text": "official source page, accessed 2026",
        "date_start": clean(row.get("period_start")) or "1900",
        "date_end": clean(row.get("period_end")) or "2026",
        "source_place_text": " / ".join(part for part in [macro, country] if part),
        "source_object_type": "official source image-bearing record",
        "source_medium": "source-hosted web image route; official source metadata",
        "source_collection": source_name,
        "source_description": description,
        "source_notes": f"registry={clean(row.get('_registry_version'))}; image_basis={image_basis}; priority={clean(row.get('next_item_capture_priority'))}",
        "source_subjects": "; ".join(part for part in [macro, country, clean(row.get("source_class")), clean(row.get("detected_protocols"))] if part),
        "source_rights_text": rights_note,
        "rights_uri": "",
        "rights_basis": rights_note,
        "image_presence_code": "IMG02",
        "image_presence_basis": f"Source-hosted image URL discovered via {image_basis}.",
        "image_state_evaluation": "IMG02: source-hosted image route only; not open rights.",
        "image_state_confidence": "medium",
        "rights_review_required": "true",
        "image_state_review_note": "No IMG01/IMG03 upgrade. Source-hosted route is retained for rights-aware display review.",
        "image_frame_behavior": "source_hosted_image_frame",
        "image_url_detected": image_url,
        "local_copy_permitted": "false",
        "iiif_or_viewer_available": "true" if "IIIF" in clean(row.get("detected_protocols")) else "false",
        "fallback_required": "false",
        "fallback_reason": "",
        "raw_json_path": "",
        "access_date": ACCESS_DATE,
        "image_expectation": "expected",
        "parser_status": "ok",
        "display_mode": "source_hosted_image_frame",
        "ocr_or_excerpt": description,
        "source_description_raw": description,
        "editorial_summary": f"{title} is captured from {source_name} as an image-bearing official source record.",
        "historical_context_note": f"This record expands {macro} / {country} source coverage with a source-hosted visual route for later item-level review.",
        "classification_rationale": "Selected from the combined 1000 pre-surface source leads because official page metadata exposed a source-hosted image route.",
        "uncertainty_note": "The detected image may be a source page, logo, hero, or collection image; it is not treated as open or item-final until reviewed.",
        "citation_basis": f"{source_name}. {title}. {source_url}. Accessed {ACCESS_DATE}.",
    }
    return {field: clean(base.get(field, "")) for field in FIELDNAMES}


def main() -> None:
    socket.setdefaulttimeout(TIMEOUT)
    rows = registry_rows()
    print(f"pre_surface_leads={len(rows)}", flush=True)
    captured: list[dict[str, str]] = []
    probed = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {executor.submit(fetch_page, row): row for row in rows}
        for future in as_completed(future_map):
            probed += 1
            result = future.result()
            if result:
                captured.append(result)
            if probed % 100 == 0:
                print(f"probe_progress={probed}/{len(rows)} image_bearing={len(captured)}", flush=True)
    unique_captured: list[dict[str, str]] = []
    seen_images: set[str] = existing_project_image_urls()
    for row in captured:
        image_url = clean(row.get("_image_url")).lower()
        if image_url in seen_images:
            continue
        seen_images.add(image_url)
        unique_captured.append(row)
    records = [capture_record(row, index + 1) for index, row in enumerate(unique_captured)]
    write_csv(RECORDS_CSV, records, FIELDNAMES)

    by_source = Counter(record["source_name"] for record in records)
    summary_rows = [
        {
            "source_id": next((record["source_id"] for record in records if record["source_name"] == source), ""),
            "source_name": source,
            "macro_region": next((record["source_place_text"].split(" / ")[0] for record in records if record["source_name"] == source), ""),
            "country_or_region": next((record["source_place_text"].split(" / ")[1] if " / " in record["source_place_text"] else "" for record in records if record["source_name"] == source), ""),
            "captured_records": str(count),
            "image_states": "IMG02:" + str(count),
            "next_item_capture_priority": next((record["source_notes"] for record in records if record["source_name"] == source), ""),
            "notes": "source-hosted image route captured; no image binary downloaded",
        }
        for source, count in sorted(by_source.items())
    ]
    write_csv(SUMMARY_CSV, summary_rows, SUMMARY_FIELDS)

    region_counts = Counter(record["source_place_text"].split(" / ")[0] for record in records)
    basis_counts = Counter(record["source_notes"].split("image_basis=", 1)[-1].split(";", 1)[0] for record in records)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    versions = ", ".join(path.stem.rsplit("_", 1)[-1] for path in sorted(DATA.glob("nonmainstream_source_success_registry_2026_v*.csv")))
    lines = [
        "# Non-mainstream Item/Image Capture 2026 v1",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        f"Scope: combined {versions} pre-surface source leads. Records are written only when a source-hosted image route is discovered.",
        "",
        "## Metrics",
        "",
        f"- Pre-surface leads checked: {len(rows)}",
        f"- Image-bearing records captured: {len(records)}",
        f"- Duplicate image routes skipped: {len(captured) - len(unique_captured)}",
        "- Image states: IMG02 only",
        "",
        "## Macro-region Distribution",
        "",
    ]
    for region, count in region_counts.most_common():
        lines.append(f"- {region}: {count}")
    lines.extend(["", "## Image Route Basis", ""])
    for basis, count in basis_counts.most_common():
        lines.append(f"- {basis}: {count}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No image binaries were downloaded.",
            "- No `IMG01` or `IMG03` upgrades were made.",
            "- Favicon, logo, apple-touch-icon, tracker, and repeated image routes are filtered out.",
            "- `IMG02` means source-hosted route only; item-level rights review is still required.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"image_bearing_records={len(records)}")
    print("macro_regions=" + ",".join(f"{key}:{value}" for key, value in region_counts.most_common()))
    print(f"wrote {RECORDS_CSV.relative_to(ROOT)}")
    print(f"wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
