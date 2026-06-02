#!/usr/bin/env python3
"""Capture a small post-1990 independent/Asian source batch.

This batch is intentionally conservative. It uses public WordPress REST
endpoints where source records are structured, keeps every image source-hosted
(`IMG02`) unless no image is present (`IMG04`), and records the source page as
the citation target. It is not a license claim and does not use Pinterest or
social platforms as evidence sources.
"""

from __future__ import annotations

import csv
import html
import json
import re
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

import run_midcentury_capture_1930_1970 as mc
import run_midcentury_expansion_capture_1931_1970 as mx
from contemporary_noise_filter import evaluate_record


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_independent_asia_1990_2026_raw"
RECORDS_CSV = DATA / "capture_batch_independent_asia_1990_2026_records.csv"
SUMMARY_CSV = DATA / "capture_batch_independent_asia_1990_2026_source_summary.csv"
REPORT = ROOT / "docs" / "capture" / "INDEPENDENT_ASIA_CAPTURE_1990_2026.md"

ACCESS_DATE = "2026-06-01"
USER_AGENT = "ModernGDHistory/0.1 independent-asia-capture"
FIELDNAMES = mx.FIELDNAMES
SECRET_PATTERNS = (
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"(?i)(key=)[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key[\"'\s:=]+)[0-9A-Za-z_-]{20,}"),
    re.compile(r"\bgh[pousr]_[0-9A-Za-z_]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
)


def clean(value: Any, *, max_chars: int = 900) -> str:
    text = html.unescape(re.sub(r"\s+", " ", str(value or "")).strip())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rsplit(" ", 1)[0] + "…"


def strip_tags(value: Any, *, max_chars: int = 1200) -> str:
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", str(value or ""))
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return clean(text, max_chars=max_chars)


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json,*/*"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def redact_secrets(value: str) -> str:
    redacted = value
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: (match.group(1) if match.lastindex else "") + "[REDACTED_SECRET]", redacted)
    return redacted


def write_raw(name: str, payload: Any) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(redact_secrets(text), encoding="utf-8")
    return str(path.relative_to(ROOT))


def year_from_date(value: str) -> str:
    match = re.search(r"\b(19\d{2}|20[0-2]\d)\b", value or "")
    return match.group(1) if match else ""


def wp_featured_image(post: dict[str, Any]) -> str:
    embedded = post.get("_embedded") if isinstance(post.get("_embedded"), dict) else {}
    media = embedded.get("wp:featuredmedia") if isinstance(embedded.get("wp:featuredmedia"), list) else []
    for item in media:
        if not isinstance(item, dict):
            continue
        details = item.get("media_details") if isinstance(item.get("media_details"), dict) else {}
        sizes = details.get("sizes") if isinstance(details.get("sizes"), dict) else {}
        for key in ("large", "medium_large", "full", "medium"):
            size = sizes.get(key)
            if isinstance(size, dict) and size.get("source_url"):
                return clean(size.get("source_url"))
        if item.get("source_url"):
            return clean(item.get("source_url"))
    return ""


def wp_media_image(base: str, post_id: str, *, raw_prefix: str) -> tuple[str, str]:
    if not post_id:
        return "", ""
    url = f"{base.rstrip('/')}/wp-json/wp/v2/media?parent={urllib.parse.quote(post_id)}"
    try:
        payload = fetch_json(url)
    except Exception:
        return "", ""
    raw_path = write_raw(f"{raw_prefix}_media_{post_id}.json", payload)
    if not isinstance(payload, list):
        return "", raw_path
    for item in payload:
        if not isinstance(item, dict) or item.get("media_type") != "image":
            continue
        details = item.get("media_details") if isinstance(item.get("media_details"), dict) else {}
        sizes = details.get("sizes") if isinstance(details.get("sizes"), dict) else {}
        for key in ("large", "medium_large", "full", "medium"):
            size = sizes.get(key)
            if isinstance(size, dict) and size.get("source_url"):
                return clean(size.get("source_url")), raw_path
        if item.get("source_url"):
            return clean(item.get("source_url")), raw_path
        guid = item.get("guid") if isinstance(item.get("guid"), dict) else {}
        if guid.get("rendered"):
            return clean(guid.get("rendered")), raw_path
    return "", raw_path


def embedded_alt(post: dict[str, Any]) -> str:
    embedded = post.get("_embedded") if isinstance(post.get("_embedded"), dict) else {}
    media = embedded.get("wp:featuredmedia") if isinstance(embedded.get("wp:featuredmedia"), list) else []
    for item in media:
        if isinstance(item, dict):
            alt = clean(item.get("alt_text"))
            if alt:
                return alt
    return ""


def terms_map(base: str, taxonomy: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for page in range(1, 5):
        url = f"{base.rstrip('/')}/wp-json/wp/v2/{taxonomy}?per_page=100&page={page}"
        try:
            payload = fetch_json(url)
        except Exception:
            break
        if not isinstance(payload, list) or not payload:
            break
        for item in payload:
            if isinstance(item, dict) and item.get("id"):
                out[int(item["id"])] = strip_tags(item.get("name"), max_chars=120)
        if len(payload) < 100:
            break
    return out


def image_fields(code: str, basis: str, image_url: str, viewer: str) -> dict[str, str]:
    return mc.image_fields(
        code,
        basis,
        image_url=image_url,
        viewer=viewer or image_url,
        confidence="high" if image_url else "medium",
        rights_review_required=True,
        local_copy_permitted=False,
        note="Independent/local source capture keeps images source-hosted; item-level rights remain with the source and original creator.",
    )


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


def seen_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in DATA.glob("capture_batch_*_records.csv"):
        if path == RECORDS_CSV or not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                keys.add((row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", "")))
    return keys


def capture_malaysia_design_archive(seen: set[tuple[str, str]]) -> tuple[list[dict[str, str]], dict[str, str]]:
    base = "https://search.malaysiadesignarchive.org"
    source_name = "Malaysia Design Archive"
    source_id = "IAS004"
    queries = ["poster", "typography", "print", "pamphlet", "publication", "logo", "advertisement", "signage"]
    tags = terms_map(base, "tags")
    item_types = terms_map(base, "item_type")
    rows: list[dict[str, str]] = []
    failures = 0
    for query in queries:
        url = f"{base}/wp-json/wp/v2/item?search={urllib.parse.quote(query)}&per_page=8&_embed=1"
        try:
            payload = fetch_json(url)
        except Exception:
            failures += 1
            continue
        raw_path = write_raw(f"malaysia_design_archive_item_{re.sub(r'[^a-z0-9]+', '_', query)}.json", payload)
        if not isinstance(payload, list):
            continue
        for post in payload:
            if not isinstance(post, dict):
                continue
            identifier = str(post.get("id") or "")
            title = strip_tags((post.get("title") or {}).get("rendered"), max_chars=260)
            body = strip_tags((post.get("content") or {}).get("rendered"), max_chars=1400)
            if not identifier or not title or len(body) < 25:
                continue
            key = (source_name, identifier)
            if key in seen:
                continue
            seen.add(key)
            link = clean(post.get("link"))
            date_text = clean(str(post.get("date", ""))[:10])
            year = year_from_date(date_text)
            tag_names = [tags.get(int(t), "") for t in post.get("tags", []) if str(t).isdigit()]
            type_names = [item_types.get(int(t), "") for t in post.get("item_type", []) if str(t).isdigit()]
            image_url = wp_featured_image(post)
            media_raw_path = ""
            if not image_url:
                image_url, media_raw_path = wp_media_image(base, identifier, raw_prefix="malaysia_design_archive")
            alt = embedded_alt(post)
            basis = "Malaysia Design Archive public item metadata; image remains source-hosted and requires item-level rights review."
            image = image_fields("IMG02" if image_url else "IMG04", basis, image_url, link)
            description = clean(" ".join(part for part in [body, alt] if part), max_chars=1500)
            rows.append(
                row_defaults(
                    {
                        "capture_id": "",
                        "direction_id": "IAC-MDA",
                        "direction_name": "independent_asia_malaysia_design_archive_1990_2026",
                        "source_id": source_id,
                        "source_name": source_name,
                        "source_api_url": url,
                        "capture_status": "captured",
                        "source_identifier": identifier,
                        "source_record_url": link,
                        "source_title": title,
                        "source_creator": "",
                        "source_date_text": date_text,
                        "date_start": year,
                        "date_end": year,
                        "source_place_text": "Malaysia",
                        "source_object_type": clean("; ".join(t for t in type_names if t) or "Malaysia Design Archive item"),
                        "source_medium": clean("; ".join(t for t in type_names if t) or "poster / print / design archive item"),
                        "source_collection": source_name,
                        "source_description": description,
                        "source_notes": "Captured as a regional/community archive item. Publication date is the source record date unless item metadata provides a more specific work date.",
                        "source_subjects": clean("; ".join(t for t in tag_names if t) or query),
                        "source_rights_text": basis,
                        "rights_uri": "",
                        "raw_json_path": media_raw_path or raw_path,
                        "access_date": ACCESS_DATE,
                        **image,
                        "editorial_summary": clean(f"{title} is indexed from Malaysia Design Archive. {description}", max_chars=800),
                        "historical_context_note": "Malaysia Design Archive adds a community/local Southeast Asian source for posters, publications, signs, and social/political graphic material outside the museum API canon.",
                        "classification_rationale": "Captured from the public WordPress REST item endpoint and filtered by graphic-design terms.",
                        "uncertainty_note": "Dates may reflect source publication rather than original production; original source page remains the evidence target.",
                        "citation_basis": f"{source_name}. {title}. {link}. Accessed {ACCESS_DATE}.",
                    }
                )
            )
            if len(rows) >= 14:
                return rows, {"source_name": source_name, "status": "captured", "captured_records": str(len(rows)), "failure_count": str(failures)}
    return rows, {"source_name": source_name, "status": "captured" if rows else "no_records_promoted", "captured_records": str(len(rows)), "failure_count": str(failures)}


def capture_another_graphic(seen: set[tuple[str, str]]) -> tuple[list[dict[str, str]], dict[str, str]]:
    base = "https://anothergraphic.org"
    source_name = "Another Graphic"
    source_id = "IAS001"
    categories = terms_map(base, "categories")
    tags = terms_map(base, "tags")
    endpoints = [
        ("posts", f"{base}/wp-json/wp/v2/posts?per_page=30&_embed=1"),
        ("product", f"{base}/wp-json/wp/v2/product?per_page=10&_embed=1"),
    ]
    rows: list[dict[str, str]] = []
    failures = 0
    preferred_regions = {
        "China",
        "Hong Kong",
        "Taiwan",
        "Japan",
        "South Korea",
        "Korea",
        "Singapore",
        "Thailand",
        "Indonesia",
        "Malaysia",
        "Vietnam",
        "Philippines",
        "India",
    }
    for subtype, url in endpoints:
        try:
            payload = fetch_json(url)
        except Exception:
            failures += 1
            continue
        raw_path = write_raw(f"another_graphic_{subtype}.json", payload)
        if not isinstance(payload, list):
            continue
        for post in payload:
            if not isinstance(post, dict):
                continue
            identifier = str(post.get("id") or "")
            title = strip_tags((post.get("title") or {}).get("rendered"), max_chars=260)
            body = strip_tags((post.get("content") or {}).get("rendered") or (post.get("excerpt") or {}).get("rendered"), max_chars=1500)
            if not identifier or not title:
                continue
            tag_names = [tags.get(int(t), "") for t in post.get("tags", []) if str(t).isdigit()]
            category_names = [categories.get(int(t), "") for t in post.get("categories", []) if str(t).isdigit()]
            region_hit = next((name for name in tag_names if name in preferred_regions), "")
            if subtype == "posts" and not region_hit:
                continue
            key = (source_name, identifier)
            if key in seen:
                continue
            seen.add(key)
            link = clean(post.get("link"))
            date_text = clean(str(post.get("date", ""))[:10])
            year = year_from_date(date_text)
            image_url = wp_featured_image(post)
            alt = embedded_alt(post)
            basis = "Another Graphic public WordPress metadata; images are curated examples and remain source-hosted with original rights holders."
            image = image_fields("IMG02" if image_url else "IMG04", basis, image_url, link)
            description = clean(" ".join(part for part in [body, alt] if part), max_chars=1500)
            if len(description) < 25 and not image_url:
                continue
            rows.append(
                row_defaults(
                    {
                        "capture_id": "",
                        "direction_id": "IAC-AG",
                        "direction_name": "independent_asia_another_graphic_1990_2026",
                        "source_id": source_id,
                        "source_name": source_name,
                        "source_api_url": url,
                        "capture_status": "captured",
                        "source_identifier": identifier,
                        "source_record_url": link,
                        "source_title": title,
                        "source_creator": "",
                        "source_date_text": date_text,
                        "date_start": year,
                        "date_end": year,
                        "source_place_text": region_hit or "post-1990 international",
                        "source_object_type": clean("; ".join(category_names) or f"Another Graphic {subtype}"),
                        "source_medium": clean("; ".join(category_names) or "contemporary graphic design source record"),
                        "source_collection": "Another Graphic curated archive",
                        "source_description": description,
                        "source_notes": "Captured as a contemporary independent-archive context/link record; not treated as original ownership evidence.",
                        "source_subjects": clean("; ".join(tag_names + category_names)),
                        "source_rights_text": basis,
                        "rights_uri": "",
                        "raw_json_path": raw_path,
                        "access_date": ACCESS_DATE,
                        **image,
                        "editorial_summary": clean(f"{title} is indexed from Another Graphic. {description}", max_chars=800),
                        "historical_context_note": "Another Graphic adds a post-1990 independent curation layer for contemporary graphic design circulation and typographic treatment. It should route users toward original designers and source pages.",
                        "classification_rationale": "Captured from public WordPress REST records and restricted to post-1990 contemporary entries, prioritizing non-Western country tags where exposed.",
                        "uncertainty_note": "This is a context/link layer. Record date is the publication date on Another Graphic, not necessarily the work creation date.",
                        "citation_basis": f"{source_name}. {title}. {link}. Accessed {ACCESS_DATE}.",
                    }
                )
            )
            if len(rows) >= 10:
                return rows, {"source_name": source_name, "status": "captured", "captured_records": str(len(rows)), "failure_count": str(failures)}
    return rows, {"source_name": source_name, "status": "captured" if rows else "no_records_promoted", "captured_records": str(len(rows)), "failure_count": str(failures)}


def assign_ids(rows: list[dict[str, str]]) -> None:
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"IAC1990R{index:03d}"


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
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    source_counts = Counter(row["source_name"] for row in rows)
    image_counts = Counter(row["image_presence_code"] for row in rows)
    lines = [
        "# Independent + Asia Capture 1990-2026",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        "This capture introduces a small number of post-1990 independent and Southeast Asian source records. It is designed to expand source diversity without converting independent-site images into open-license assets.",
        "",
        "## Capture Rules",
        "",
        "- Only public source endpoints are used.",
        "- All images from independent/community sites are `IMG02` source-hosted unless no image is exposed (`IMG04`).",
        "- Source publication dates are marked with uncertainty when original work dates are not exposed.",
        "- Pinterest/Instagram-like platforms are discovery channels only and are not recorded as evidence sources.",
        "",
        "## Summary",
        "",
        f"- Captured records: {len(rows)}",
        f"- Sources: {len(source_counts)}",
        f"- Image states: {dict(image_counts)}",
        "",
        "## Source Counts",
        "",
    ]
    for name, count in sorted(source_counts.items()):
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Source Probe Results", ""])
    for summary in summaries:
        lines.append(f"- {summary['source_name']}: {summary['status']} ({summary['captured_records']} records; failures {summary['failure_count']})")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    seen = seen_keys()
    rows: list[dict[str, str]] = []
    summaries: list[dict[str, str]] = []
    for capture in (capture_malaysia_design_archive, capture_another_graphic):
        captured, summary = capture(seen)
        rows.extend(captured)
        summaries.append(summary)
    rows, noise_decisions = apply_noise_filter(rows)
    assign_ids(rows)
    write_csv(RECORDS_CSV, rows, FIELDNAMES)
    write_csv(SUMMARY_CSV, summaries, ["source_name", "status", "captured_records", "failure_count"])
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
