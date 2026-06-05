#!/usr/bin/env python3
"""Capture non-mainstream regional source records for 1990-2026 coverage.

This batch uses public WordPress REST-style endpoints from sources prioritized
by the contemporary v2 adapter queue. It captures source metadata, canonical
links, descriptions, tags, and rights notes only. It never downloads image
binaries; discovered image URLs remain source-hosted IMG02 references and still
require item-level rights review.
"""

from __future__ import annotations

import csv
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import run_midcentury_capture_1930_1970 as mc
import run_midcentury_expansion_capture_1931_1970 as mx


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

TARGETS_CSV = DATA / "nonmainstream_region_capture_targets_1990_2026_v1.csv"
RECORDS_CSV = DATA / "capture_batch_nonmainstream_region_1990_2026_records.csv"
SUMMARY_CSV = DATA / "capture_batch_nonmainstream_region_1990_2026_source_summary.csv"
IMPACT_CSV = DATA / "nonmainstream_region_impact_ratings_1990_2026_v1.csv"
REPORT = DOCS / "NONMAINSTREAM_REGION_CAPTURE_1990_2026_v1.md"

ACCESS_DATE = "2026-06-05"
USER_AGENT = "ModernGDHistory/0.1 nonmainstream-region-content-capture"
FIELDNAMES = mx.FIELDNAMES
YEAR_START = 1990
YEAR_END = 2026

TARGET_FIELDS = [
    "target_id",
    "source_name",
    "macro_region",
    "country_or_region",
    "endpoint_type",
    "base_url",
    "post_type",
    "queries",
    "max_records",
    "selection_reason",
    "rights_boundary",
]

SUMMARY_FIELDS = [
    "source_id",
    "source_name",
    "macro_region",
    "country_or_region",
    "endpoint_type",
    "targeted_queries",
    "captured_records",
    "failure_count",
    "image_states",
    "impact_ratings",
    "notes",
]

IMPACT_FIELDS = [
    "capture_id",
    "source_name",
    "macro_region",
    "country_or_region",
    "source_title",
    "impact_score",
    "impact_rating",
    "impact_basis",
    "source_record_url",
]

REGION_WEIGHT = {
    "Africa": 5,
    "MENA": 5,
    "South Asia": 5,
    "Southeast Asia": 5,
    "Latin America": 4,
    "Latin America / Caribbean": 4,
    "East Asia": 4,
    "Eastern Europe / Central Asia": 3,
}

HIGH_IMPACT_TERMS = (
    "poster",
    "typography",
    "type",
    "graphic design",
    "visual culture",
    "identity",
    "archive",
    "print",
    "publication",
    "campaign",
    "activism",
    "heritage",
    "ephemera",
    "design",
    "lettering",
    "广告",
    "ポスター",
)


@dataclass(frozen=True)
class CaptureTarget:
    target_id: str
    source_name: str
    macro_region: str
    country_or_region: str
    endpoint_type: str
    base_url: str
    post_type: str
    queries: tuple[str, ...]
    max_records: int
    selection_reason: str


TARGETS: tuple[CaptureTarget, ...] = (
    CaptureTarget(
        "NMR001",
        "DesignSingapore Council",
        "Southeast Asia",
        "Singapore",
        "wordpress_rest",
        "https://designsingapore.org",
        "posts",
        ("graphic design", "typography", "identity", "publication"),
        4,
        "reachable v2 P1 WordPress source for Southeast Asian design policy and contemporary source text",
    ),
    CaptureTarget(
        "NMR002",
        "Malaysian Design Archive",
        "Southeast Asia",
        "Malaysia",
        "wordpress_rest_custom_type",
        "https://search.malaysiadesignarchive.org",
        "item",
        ("poster", "typography", "print", "publication", "advertisement"),
        5,
        "priority independent Southeast Asian visual culture archive with item-style source records",
    ),
    CaptureTarget(
        "NMR003",
        "Grafis Nusantara",
        "Southeast Asia",
        "Indonesia",
        "wordpress_rest",
        "https://grafisnusantara.com",
        "posts",
        ("label", "packaging", "poster", "typography"),
        4,
        "priority Indonesian graphic archive; source-hosted visual evidence only",
    ),
    CaptureTarget(
        "NMR004",
        "29LT",
        "MENA",
        "MENA",
        "wordpress_rest",
        "https://www.29lt.com",
        "posts",
        ("Arabic typography", "type design", "poster", "publication"),
        4,
        "reachable MENA typography source from v2 P1 queue",
    ),
    CaptureTarget(
        "NMR005",
        "Barjeel Art Foundation",
        "MENA",
        "MENA",
        "wordpress_rest",
        "https://www.barjeelartfoundation.org",
        "posts",
        ("poster", "graphic", "publication", "archive"),
        4,
        "MENA visual culture source with article/source text enrichment value",
    ),
    CaptureTarget(
        "NMR006",
        "African Digital Heritage",
        "Africa",
        "Africa",
        "wordpress_rest",
        "https://africandigitalheritage.org",
        "posts",
        ("graphic", "archive", "heritage", "poster"),
        4,
        "African digital heritage source; source relationship and cultural sensitivity review remains explicit",
    ),
    CaptureTarget(
        "NMR007",
        "GALA Queer Archive",
        "Africa",
        "South Africa",
        "wordpress_rest",
        "https://gala.co.za",
        "posts",
        ("poster", "archive", "activism", "publication"),
        4,
        "South African community archive source; source-hosted records only",
    ),
    CaptureTarget(
        "NMR008",
        "Indian Memory Project",
        "South Asia",
        "India",
        "wordpress_rest",
        "https://indianmemoryproject.com",
        "posts",
        ("poster", "print", "visual culture", "design"),
        4,
        "South Asian community visual archive; provenance and rights require item-level review",
    ),
    CaptureTarget(
        "NMR009",
        "MAP Academy",
        "South Asia",
        "South Asia",
        "wordpress_rest",
        "https://mapacademy.io",
        "posts",
        ("graphic", "poster", "print", "typography"),
        4,
        "South Asian scholarly encyclopedia/context source from v2 P1 queue",
    ),
    CaptureTarget(
        "NMR010",
        "Diseño Nacional",
        "Latin America",
        "Chile",
        "wordpress_rest",
        "https://www.disenonacional.cl",
        "posts",
        ("cartel", "afiche", "diseño gráfico", "tipografía"),
        4,
        "Latin American graphic archive with source text and source-hosted display evidence",
    ),
)


def clean(value: Any, *, max_chars: int = 900) -> str:
    text = html.unescape(re.sub(r"\s+", " ", str(value or "")).strip())
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(re.sub(r"\s+", " ", text).strip())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rsplit(" ", 1)[0] + "..."


def fetch_json(url: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def endpoint_url(target: CaptureTarget, query: str) -> str:
    params = {
        "search": query,
        "per_page": str(min(max(target.max_records * 2, 6), 12)),
        "_embed": "1",
    }
    return f"{target.base_url.rstrip('/')}/wp-json/wp/v2/{target.post_type}?" + urllib.parse.urlencode(params)


def existing_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in DATA.glob("capture_batch_*_records.csv"):
        if path == RECORDS_CSV:
            continue
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                keys.add((row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", "")))
                if row.get("source_record_url"):
                    keys.add(("", row["source_record_url"]))
    return keys


def year_from_text(value: str) -> str:
    years = [int(year) for year in re.findall(r"\b(19[9]\d|20[0-2]\d|2026)\b", value or "")]
    years = [year for year in years if YEAR_START <= year <= YEAR_END]
    return str(max(years)) if years else ""


def post_image_url(post: dict[str, Any]) -> str:
    embedded = post.get("_embedded") if isinstance(post.get("_embedded"), dict) else {}
    media = embedded.get("wp:featuredmedia") if isinstance(embedded.get("wp:featuredmedia"), list) else []
    for item in media:
        if not isinstance(item, dict):
            continue
        details = item.get("media_details") if isinstance(item.get("media_details"), dict) else {}
        sizes = details.get("sizes") if isinstance(details.get("sizes"), dict) else {}
        for key in ("large", "medium_large", "full", "medium", "thumbnail"):
            size = sizes.get(key)
            if isinstance(size, dict) and size.get("source_url"):
                return clean(size["source_url"], max_chars=900)
        if item.get("source_url"):
            return clean(item["source_url"], max_chars=900)
    return ""


def embedded_terms(post: dict[str, Any]) -> str:
    embedded = post.get("_embedded") if isinstance(post.get("_embedded"), dict) else {}
    terms: list[str] = []
    for group in embedded.get("wp:term", []) if isinstance(embedded.get("wp:term"), list) else []:
        if not isinstance(group, list):
            continue
        for term in group:
            if isinstance(term, dict) and term.get("name"):
                terms.append(clean(term["name"], max_chars=80))
    return clean("; ".join(dict.fromkeys(terms)), max_chars=500)


def relevant(title: str, description: str, subjects: str, query: str) -> bool:
    blob = " ".join([title, description, subjects, query]).lower()
    if any(term in blob for term in HIGH_IMPACT_TERMS):
        return True
    return len(description) > 180 and any(word in blob for word in ("archive", "design", "visual", "print"))


def image_fields(image_url: str, viewer: str, source_name: str) -> dict[str, str]:
    if image_url:
        return mc.image_fields(
            "IMG02",
            f"{source_name} exposes a source-hosted image URL; no local copy or reuse right is inferred.",
            image_url=image_url,
            viewer=viewer,
            confidence="medium",
            rights_review_required=True,
            local_copy_permitted=False,
            note="Non-mainstream regional capture records source-hosted image routes only; item-level rights review remains required.",
        )
    return mc.image_fields(
        "IMG04",
        f"{source_name} text/source metadata record; no item-level image route was promoted.",
        viewer=viewer,
        confidence="medium",
        rights_review_required=True,
        local_copy_permitted=False,
        note="No image binary was downloaded; this is a text/source record until a rights-visible image route is reviewed.",
    )


def row_defaults(row: dict[str, str]) -> dict[str, str]:
    code = row.get("image_presence_code") or "IMG04"
    row["image_expectation"] = "not_expected" if code == "IMG04" else "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["ocr_or_excerpt"] = row.get("source_description", "")
    row["source_description_raw"] = row.get("source_description", "")
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def impact_for(row: dict[str, str], target: CaptureTarget) -> tuple[int, str, str]:
    score = REGION_WEIGHT.get(target.macro_region, 2) * 10
    blob = " ".join(
        [
            row.get("source_title", ""),
            row.get("source_description", ""),
            row.get("source_subjects", ""),
            target.selection_reason,
        ]
    ).lower()
    term_hits = sum(1 for term in HIGH_IMPACT_TERMS if term in blob)
    score += min(term_hits * 4, 24)
    if row.get("image_presence_code") == "IMG02":
        score += 8
    if row.get("source_record_url"):
        score += 5
    if len(row.get("source_description", "")) > 220:
        score += 5
    if "community" in target.selection_reason.lower() or "independent" in target.selection_reason.lower():
        score += 4
    if score >= 75:
        rating = "A"
    elif score >= 60:
        rating = "B"
    elif score >= 45:
        rating = "C"
    else:
        rating = "D"
    basis = (
        f"region_weight={REGION_WEIGHT.get(target.macro_region, 2)}; "
        f"term_hits={term_hits}; image_state={row.get('image_presence_code')}; "
        "internal triage only, not public authority"
    )
    return score, rating, basis


def capture_target(target: CaptureTarget, seen: set[tuple[str, str]]) -> tuple[list[dict[str, str]], dict[str, str], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    impact_rows: list[dict[str, str]] = []
    failures = 0
    for query in target.queries:
        if len(rows) >= target.max_records:
            break
        url = endpoint_url(target, query)
        try:
            payload = fetch_json(url)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
            failures += 1
            continue
        if not isinstance(payload, list):
            failures += 1
            continue
        for post in payload:
            if len(rows) >= target.max_records:
                break
            if not isinstance(post, dict):
                continue
            identifier = str(post.get("id") or "")
            link = clean(post.get("link") or post.get("guid", {}).get("rendered", ""), max_chars=900)
            title = clean((post.get("title") or {}).get("rendered") or post.get("title"), max_chars=320)
            excerpt = clean((post.get("excerpt") or {}).get("rendered"), max_chars=900)
            content = clean((post.get("content") or {}).get("rendered"), max_chars=1400)
            description = clean(" ".join(part for part in [excerpt, content] if part), max_chars=1600)
            subjects = embedded_terms(post)
            if not identifier or not link or not title or not relevant(title, description, subjects, query):
                continue
            key = (target.source_name, identifier)
            if key in seen or ("", link) in seen:
                continue
            seen.add(key)
            seen.add(("", link))
            date_text = clean(str(post.get("date") or post.get("modified") or "")[:10], max_chars=40)
            year = year_from_text(date_text) or year_from_text(description) or year_from_text(title)
            image_url = post_image_url(post)
            image = image_fields(image_url, link, target.source_name)
            row = row_defaults(
                {
                    "capture_id": "",
                    "direction_id": "NMR01",
                    "direction_name": "nonmainstream_region_content_capture_1990_2026",
                    "source_id": target.target_id,
                    "source_name": target.source_name,
                    "source_api_url": url,
                    "capture_status": "captured",
                    "source_identifier": identifier,
                    "source_record_url": link,
                    "source_title": title,
                    "source_creator": "",
                    "source_date_text": date_text,
                    "date_start": year,
                    "date_end": year,
                    "source_place_text": target.country_or_region,
                    "source_object_type": "source-linked regional design/context record",
                    "source_medium": "public source metadata; article/item text; source-hosted visual route where exposed",
                    "source_collection": target.source_name,
                    "source_description": description,
                    "source_notes": clean(f"query={query}; endpoint={target.endpoint_type}; {target.selection_reason}", max_chars=900),
                    "source_subjects": clean(subjects or query, max_chars=900),
                    "source_rights_text": f"{target.source_name} public source metadata; image and media rights require item-level source review.",
                    "rights_uri": "",
                    "raw_json_path": "",
                    "access_date": ACCESS_DATE,
                    **image,
                    "editorial_summary": clean(f"{title} is indexed from {target.source_name}. {description}", max_chars=760),
                    "historical_context_note": clean(
                        f"This record expands {target.macro_region} / {target.country_or_region} coverage through a source-linked non-mainstream regional record.",
                        max_chars=520,
                    ),
                    "classification_rationale": clean(
                        "Selected from public REST metadata because title, tags, excerpt, or body text match graphic design, print, typography, poster, archive, or visual culture terms.",
                        max_chars=620,
                    ),
                    "uncertainty_note": "Source date is the source/post date unless a stronger object date is later verified. Images stay source-hosted and rights-sensitive.",
                    "citation_basis": f"{target.source_name}. {title}. {link}. Accessed {ACCESS_DATE}.",
                }
            )
            rows.append(row)
        time.sleep(0.15)

    image_counts = Counter(row["image_presence_code"] for row in rows)
    ratings = Counter()
    for row in rows:
        score, rating, basis = impact_for(row, target)
        ratings[rating] += 1
        impact_rows.append(
            {
                "capture_id": row["capture_id"],
                "source_name": row["source_name"],
                "macro_region": target.macro_region,
                "country_or_region": target.country_or_region,
                "source_title": row["source_title"],
                "impact_score": str(score),
                "impact_rating": rating,
                "impact_basis": basis,
                "source_record_url": row["source_record_url"],
            }
        )
    return rows, {
        "source_id": target.target_id,
        "source_name": target.source_name,
        "macro_region": target.macro_region,
        "country_or_region": target.country_or_region,
        "endpoint_type": target.endpoint_type,
        "targeted_queries": "; ".join(target.queries),
        "captured_records": str(len(rows)),
        "failure_count": str(failures),
        "image_states": "; ".join(f"{k}:{v}" for k, v in sorted(image_counts.items())),
        "impact_ratings": "; ".join(f"{k}:{v}" for k, v in sorted(ratings.items())),
        "notes": target.selection_reason,
    }, impact_rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fieldnames} for row in rows)


def write_targets() -> None:
    rows = [
        {
            "target_id": target.target_id,
            "source_name": target.source_name,
            "macro_region": target.macro_region,
            "country_or_region": target.country_or_region,
            "endpoint_type": target.endpoint_type,
            "base_url": target.base_url,
            "post_type": target.post_type,
            "queries": "; ".join(target.queries),
            "max_records": str(target.max_records),
            "selection_reason": target.selection_reason,
            "rights_boundary": "source metadata only; no image download; IMG03 only by authoritative item-level rights",
        }
        for target in TARGETS
    ]
    write_csv(TARGETS_CSV, TARGET_FIELDS, rows)


def write_report(rows: list[dict[str, str]], summaries: list[dict[str, str]], impacts: list[dict[str, str]]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    by_region = Counter(row["source_place_text"] for row in rows)
    by_macro = Counter(summary["macro_region"] for summary in summaries if int(summary.get("captured_records") or 0) > 0)
    by_image = Counter(row["image_presence_code"] for row in rows)
    by_rating = Counter(row["impact_rating"] for row in impacts)
    lines = [
        "# Non-mainstream Region Content Capture 1990-2026 v1",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        "This batch expands coverage through public source metadata from non-mainstream and underrepresented regional sources. It does not download images, does not write raw third-party payloads, and does not upgrade image state from heuristics.",
        "",
        "## Target List",
        "",
        f"- Target sources listed: {len(TARGETS)}",
        f"- Captured sources: {len([s for s in summaries if int(s.get('captured_records') or 0) > 0])}",
        f"- Captured records: {len(rows)}",
        "",
        "## Macro-region Counts",
        "",
    ]
    for key, count in by_macro.most_common():
        lines.append(f"- {key}: {count} captured sources")
    lines.extend(["", "## Place Counts", ""])
    for key, count in by_region.most_common():
        lines.append(f"- {key}: {count} records")
    lines.extend(["", "## Image States", ""])
    for key, count in sorted(by_image.items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Impact Ratings", ""])
    for key, count in sorted(by_rating.items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Source Summary", ""])
    for summary in summaries:
        lines.append(
            f"- {summary['source_name']} ({summary['macro_region']} / {summary['country_or_region']}): "
            f"{summary['captured_records']} records; failures {summary['failure_count']}; "
            f"images {summary['image_states'] or 'none'}; impact {summary['impact_ratings'] or 'none'}"
        )
    lines.extend(
        [
            "",
            "## Rights Boundary",
            "",
            "- All images remain source-hosted if present (`IMG02`) or absent/text-only (`IMG04`).",
            "- No image binary, screenshot, thumbnail file, or raw third-party payload is stored by this batch.",
            "- Impact ratings are internal triage only and cannot decide public authority, inclusion, authorship, or rights.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    write_targets()
    seen = existing_keys()
    rows: list[dict[str, str]] = []
    summaries: list[dict[str, str]] = []
    impacts: list[dict[str, str]] = []
    for target in TARGETS:
        source_rows, summary, source_impacts = capture_target(target, seen)
        rows.extend(source_rows)
        summaries.append(summary)
        impacts.extend(source_impacts)
        time.sleep(0.25)

    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"NMR1990R{index:04d}"
    impact_by_url = {row["source_record_url"]: row for row in impacts}
    for row in rows:
        impact = impact_by_url.get(row["source_record_url"])
        if impact:
            impact["capture_id"] = row["capture_id"]

    write_csv(RECORDS_CSV, FIELDNAMES, rows)
    write_csv(SUMMARY_CSV, SUMMARY_FIELDS, summaries)
    write_csv(IMPACT_CSV, IMPACT_FIELDS, impacts)
    write_report(rows, summaries, impacts)

    print(f"targets={len(TARGETS)}")
    print(f"captured={len(rows)}")
    print("image_states=" + json.dumps(dict(Counter(row["image_presence_code"] for row in rows)), sort_keys=True))
    print("impact_ratings=" + json.dumps(dict(Counter(row["impact_rating"] for row in impacts)), sort_keys=True))
    print(f"wrote {TARGETS_CSV.relative_to(ROOT)}")
    print(f"wrote {RECORDS_CSV.relative_to(ROOT)}")
    print(f"wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"wrote {IMPACT_CSV.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
