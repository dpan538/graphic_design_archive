#!/usr/bin/env python3
"""Promote reachable edge-source probes into source-registry context records.

This capture does not treat a source homepage as an object record. It records
reachable local, community, institutional, university, and government sources as
evidence-bearing source entries so the archive can measure source breadth before
writing deeper item adapters.
"""

from __future__ import annotations

import csv
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import run_midcentury_capture_1930_1970 as mc
import run_midcentury_expansion_capture_1931_1970 as mx


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_edge_source_registry_context_1931_2026_raw"
RECORDS_CSV = DATA / "capture_batch_edge_source_registry_context_1931_2026_records.csv"
SUMMARY_CSV = DATA / "capture_batch_edge_source_registry_context_1931_2026_source_summary.csv"
REPORT = ROOT / "docs" / "capture" / "EDGE_SOURCE_REGISTRY_CONTEXT_CAPTURE_1931_2026.md"

ACCESS_DATE = "2026-06-02"
FIELDNAMES = mx.FIELDNAMES

PROBE_FILES = [
    DATA / "source_probe_independent_asia_v1.csv",
    DATA / "source_probe_edge_v2.csv",
    DATA / "source_probe_south_asia_v1.csv",
]

TARGET_REGIONS = {
    "Africa",
    "East Asia",
    "Southeast Asia",
    "South Asia",
    "Middle East",
    "Middle East and North Africa",
    "Latin America",
    "Eastern Europe",
}

SKIP_SOURCE_NAMES = {
    "Another Graphic",
    "Fonts In Use",
    "People's Graphic Design Archive",
    "Letterform Archive",
    "Design Reviewed",
    "Archivo de la Grafica Chilena",
}

SKIP_SOURCE_CLASSES = {
    "social platform",
    "social-platform",
}

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
    return text[: max_chars - 1].rsplit(" ", 1)[0] + "..."


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def redact(value: str) -> str:
    out = value
    for pattern in SECRET_PATTERNS:
        out = pattern.sub(lambda match: (match.group(1) if match.lastindex else "") + "[REDACTED_SECRET]", out)
    return out


def existing_sources() -> set[str]:
    names: set[str] = set()
    for path in DATA.glob("capture_batch_*_records.csv"):
        if path == RECORDS_CSV:
            continue
        for row in read_csv(path):
            name = clean(row.get("source_name"))
            if name:
                names.add(name.lower())
    return names


def raw_text(row: dict[str, str]) -> str:
    path = ROOT / clean(row.get("raw_probe_path"))
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def meta_content(body: str, *names: str) -> str:
    for name in names:
        pattern = re.compile(
            r"<meta[^>]+(?:property|name)=[\"']"
            + re.escape(name)
            + r"[\"'][^>]+content=[\"'](.*?)[\"']",
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(body)
        if match:
            return clean(match.group(1), max_chars=1200)
    return ""


def image_from_probe(row: dict[str, str], body: str) -> tuple[str, str]:
    image_url = meta_content(body, "og:image", "twitter:image")
    if not image_url:
        return "IMG04", ""
    policy = row.get("recommended_image_policy", "")
    if "IMG00" in policy and "IMG02" not in policy:
        return "IMG00", image_url
    return "IMG02", image_url


def year_range_from_intent(value: str) -> tuple[str, str]:
    years = [int(year) for year in re.findall(r"\b(19\d{2}|20[0-2]\d)\b", value or "")]
    years = [year for year in years if 1931 <= year <= 2026]
    if not years:
        return "", ""
    if max(years) - min(years) > 40:
        return "", ""
    return str(min(years)), str(max(years))


def include_probe(row: dict[str, str], active_sources: set[str]) -> bool:
    source_name = clean(row.get("source_name"))
    if not source_name or source_name in SKIP_SOURCE_NAMES:
        return False
    if source_name.lower() in active_sources:
        return False
    if clean(row.get("probe_status")) != "ok":
        return False
    region = clean(row.get("macro_region"))
    if region not in TARGET_REGIONS:
        return False
    source_class = clean(row.get("source_class")).lower()
    if any(skip in source_class for skip in SKIP_SOURCE_CLASSES):
        return False
    priority = clean(row.get("capture_priority"))
    if not (priority.startswith("P1") or priority.startswith("P2")):
        return False
    return True


def image_fields(code: str, basis: str, image_url: str, viewer: str) -> dict[str, str]:
    return mc.image_fields(
        code,
        basis,
        image_url=image_url,
        viewer=viewer or image_url,
        confidence="medium",
        rights_review_required=True,
        local_copy_permitted=False,
        note="Source-registry context capture keeps source images source-hosted and does not claim item-level image reuse.",
    )


def row_defaults(row: dict[str, str]) -> dict[str, str]:
    code = row.get("image_presence_code", "IMG04")
    row["image_expectation"] = "not_expected" if code == "IMG04" else "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["ocr_or_excerpt"] = row.get("source_description", "")
    row["source_description_raw"] = row.get("source_description", "")
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def build_rows() -> list[dict[str, str]]:
    active = existing_sources()
    selected: dict[str, dict[str, str]] = {}
    for probe_file in PROBE_FILES:
        for row in read_csv(probe_file):
            if not include_probe(row, active):
                continue
            selected.setdefault(clean(row.get("source_name")), row)

    rows: list[dict[str, str]] = []
    for index, probe in enumerate(sorted(selected.values(), key=lambda r: (r.get("macro_region", ""), r.get("source_name", ""))), start=1):
        source_name = clean(probe.get("source_name"))
        body = raw_text(probe)
        title = clean(probe.get("page_title") or source_name, max_chars=320)
        description = clean(
            probe.get("meta_description")
            or meta_content(body, "description", "og:description", "twitter:description")
            or probe.get("capture_intent")
            or probe.get("notes"),
            max_chars=1500,
        )
        image_code, image_url = image_from_probe(probe, body)
        start, end = year_range_from_intent(probe.get("period_intent", ""))
        record_url = clean(probe.get("final_url") or probe.get("url"))
        basis = clean(
            f"{source_name} source-registry context record. Recommended image policy: "
            f"{probe.get('recommended_image_policy') or 'source-hosted or link-only pending review'}.",
            max_chars=900,
        )
        row = {
            "capture_id": f"ESR1931R{index:03d}",
            "direction_id": "ESR01",
            "direction_name": "edge_source_registry_context_1931_2026",
            "source_id": clean(probe.get("candidate_id")),
            "source_name": source_name,
            "source_api_url": clean(probe.get("url")),
            "capture_status": "captured",
            "source_identifier": clean(probe.get("candidate_id")),
            "source_record_url": record_url,
            "source_title": title,
            "source_creator": "",
            "source_date_text": clean(f"source scope: {probe.get('period_intent') or 'modern-present'}", max_chars=160),
            "date_start": start,
            "date_end": end,
            "source_place_text": clean(probe.get("country_or_region") or probe.get("macro_region")),
            "source_object_type": clean(f"source registry/context record; {probe.get('source_class')}", max_chars=260),
            "source_medium": "source registry context; archive/source family evidence",
            "source_collection": source_name,
            "source_description": description,
            "source_notes": clean(
                f"Probe status: {probe.get('probe_status')}; protocols: {probe.get('detected_protocols')}; "
                f"intent: {probe.get('capture_intent')}; limitations: {probe.get('notes')}",
                max_chars=1200,
            ),
            "source_subjects": clean(
                f"{probe.get('capture_intent')}; {probe.get('source_class')}; {probe.get('macro_region')}; {probe.get('country_or_region')}",
                max_chars=900,
            ),
            "source_rights_text": basis,
            "rights_uri": "",
            "raw_json_path": clean(probe.get("raw_probe_path")),
            "access_date": clean(probe.get("access_date") or ACCESS_DATE),
            **image_fields(image_code, basis, image_url, record_url),
            "editorial_summary": clean(f"{source_name} is registered as an edge source for modern graphic design history. {description}", max_chars=850),
            "historical_context_note": clean(
                f"This source expands the archive toward {probe.get('country_or_region')} / {probe.get('macro_region')} "
                "and should guide later item-level capture without replacing the original archive.",
                max_chars=700,
            ),
            "classification_rationale": "Promoted from a successful source probe as source-registry evidence only; not an object-level sheet.",
            "uncertainty_note": "Dates describe source scope or institutional period intent, not a single work date. Use as source dossier, reading note, or support material until item records are captured.",
            "citation_basis": f"{source_name}. {record_url}. Accessed {probe.get('access_date') or ACCESS_DATE}.",
        }
        rows.append(row_defaults(row))
    return rows


def write_report(rows: list[dict[str, str]]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    by_region = Counter(row["source_place_text"] for row in rows)
    by_image = Counter(row["image_presence_code"] for row in rows)
    by_macro = Counter()
    for row in rows:
        subjects = row.get("source_subjects", "")
        for region in TARGET_REGIONS:
            if region in subjects:
                by_macro[region] += 1
                break
    lines = [
        "# Edge Source Registry Context Capture 1931-2026",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        "This capture promotes reachable source probes into source-registry context records. It is a source-breadth repair pass, not an object-level ingest.",
        "",
        "## Summary",
        "",
        f"- Captured source-context records: {len(rows)}",
        f"- Distinct sources: {len({row['source_name'] for row in rows})}",
        f"- Image states: {dict(sorted(by_image.items()))}",
        "",
        "## Macro-region / Place Counts",
        "",
    ]
    for name, count in sorted(by_macro.items()):
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Place Labels", ""])
    for name, count in sorted(by_region.items()):
        lines.append(f"- {name}: {count}")
    lines.extend(
        [
            "",
            "## Method Note",
            "",
            "Rows created here should normally render as source dossiers, reading notes, support packets, cards, or bookmarks. They should not become canonical main sheets until item-level records with stronger dates, object metadata, and rights evidence are captured.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    write_csv(RECORDS_CSV, rows, FIELDNAMES)
    summary_rows = []
    for row in rows:
        summary_rows.append(
            {
                "source_id": row["source_id"],
                "source_name": row["source_name"],
                "place": row["source_place_text"],
                "image_presence_code": row["image_presence_code"],
                "record_url": row["source_record_url"],
            }
        )
    write_csv(SUMMARY_CSV, summary_rows, ["source_id", "source_name", "place", "image_presence_code", "record_url"])
    write_report(rows)
    print(f"{RECORDS_CSV.relative_to(ROOT)}: {len(rows)} rows")
    print("image distribution:", dict(sorted(Counter(row["image_presence_code"] for row in rows).items())))
    print(f"{SUMMARY_CSV.relative_to(ROOT)}: summary written")
    print(f"{REPORT.relative_to(ROOT)}: report written")


if __name__ == "__main__":
    main()
