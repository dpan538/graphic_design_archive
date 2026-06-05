#!/usr/bin/env python3
"""Create source-profile records from successful low-coverage source probes.

This is a metadata-only capture. It converts successful source discovery probes
into public source-profile sheets so the archive can represent undercovered
regions as a system. It does not download images, capture screenshots, or
promote IMG01/IMG03 states.
"""

from __future__ import annotations

import csv
import html
import re
from collections import Counter
from pathlib import Path
from typing import Any

import run_midcentury_expansion_capture_1931_1970 as mx


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

CANDIDATES = DATA / "nonmainstream_low_coverage_source_candidates_1990_2026_v3.csv"
PROBE = DATA / "nonmainstream_low_coverage_source_probe_1990_2026_v3.csv"
RECORDS_CSV = DATA / "capture_batch_nonmainstream_source_profiles_1990_2026_records.csv"
SUMMARY_CSV = DATA / "capture_batch_nonmainstream_source_profiles_1990_2026_source_summary.csv"
IMPACT_CSV = DATA / "nonmainstream_source_profile_impact_ratings_1990_2026_v1.csv"
REPORT = DOCS / "NONMAINSTREAM_SOURCE_PROFILE_CAPTURE_1990_2026_v1.md"

ACCESS_DATE = "2026-06-05"
FIELDNAMES = mx.FIELDNAMES

SUMMARY_FIELDS = [
    "source_id",
    "source_name",
    "macro_region",
    "country_or_region",
    "protocol_family",
    "captured_records",
    "image_states",
    "impact_ratings",
    "detected_protocols",
    "notes",
]

IMPACT_FIELDS = [
    "capture_id",
    "source_name",
    "macro_region",
    "country_or_region",
    "impact_score",
    "impact_rating",
    "impact_basis",
    "source_record_url",
]


def clean(value: Any, *, max_chars: int = 900) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(re.sub(r"\s+", " ", text).strip())
    if len(text) > max_chars:
        return text[: max_chars - 1].rstrip() + "..."
    return text


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def pct(num: int, den: int) -> str:
    if den <= 0:
        return "0.00"
    return f"{(num / den) * 100:.2f}"


def merge_rows() -> list[dict[str, str]]:
    candidates = {row["candidate_id"]: row for row in read_csv(CANDIDATES)}
    merged: list[dict[str, str]] = []
    seen_keys: set[tuple[str, str]] = set()
    for probe_row in read_csv(PROBE):
        if probe_row.get("probe_status") != "ok":
            continue
        candidate = candidates.get(probe_row.get("candidate_id", ""), {})
        row = dict(candidate)
        row.update({f"probe_{key}": value for key, value in probe_row.items()})
        row["candidate_id"] = probe_row.get("candidate_id") or candidate.get("candidate_id", "")
        row["source_name"] = probe_row.get("source_name") or candidate.get("source_name", "")
        row["macro_region"] = probe_row.get("macro_region") or candidate.get("macro_region", "")
        row["country_or_region"] = probe_row.get("country_or_region") or candidate.get("country_or_region", "")
        row["url"] = probe_row.get("final_url") or probe_row.get("url") or candidate.get("url", "")
        key = (clean(row["source_name"]).lower(), clean(row["url"]).lower())
        if key in seen_keys:
            continue
        seen_keys.add(key)
        merged.append(row)
    return merged


def source_title(row: dict[str, str]) -> str:
    return clean(row.get("probe_page_title"), max_chars=160) or clean(row.get("source_name"), max_chars=160)


def source_description(row: dict[str, str]) -> str:
    parts = [
        clean(row.get("probe_meta_description"), max_chars=500),
        clean(row.get("expected_record_types"), max_chars=220),
        clean(row.get("text_enrichment_path"), max_chars=220),
    ]
    return " ".join(part for part in parts if part) or "Successful source-level probe for an undercovered regional design/history source."


def record_from_row(row: dict[str, str], index: int) -> dict[str, str]:
    capture_id = f"NMSP2026R{index:04d}"
    source_name = clean(row.get("source_name"))
    source_url = clean(row.get("url"))
    title = source_title(row)
    description = source_description(row)
    protocols = clean(row.get("probe_detected_protocols") or row.get("protocol_family"))
    protocol_evidence = clean(row.get("probe_protocol_evidence"), max_chars=400)
    macro_region = clean(row.get("macro_region"))
    country = clean(row.get("country_or_region"))
    subjects = "; ".join(
        part
        for part in [
            macro_region,
            country,
            clean(row.get("source_class")),
            clean(row.get("expected_record_types"), max_chars=140),
            protocols,
        ]
        if part
    )
    rights_note = (
        "Source-profile metadata only. No image binary, screenshot, thumbnail, "
        "or item-level rights upgrade was captured in this pass."
    )
    context = (
        f"{source_name} is indexed as a source-profile page for {macro_region}"
        f"{' / ' + country if country else ''}. "
        f"Probe status was ok; detected protocols: {protocols or 'HTML/source metadata'}."
    )
    classification = (
        "Selected from the non-mainstream low-coverage v3 probe because the source "
        "responded successfully and can support source-level coverage expansion."
    )

    base = {
        "capture_id": capture_id,
        "direction_id": "NMSP01",
        "direction_name": "nonmainstream_source_profile_capture_1990_2026",
        "source_id": clean(row.get("candidate_id")),
        "source_name": source_name,
        "source_api_url": clean(row.get("probe_url") or source_url),
        "capture_status": "captured",
        "source_identifier": clean(row.get("candidate_id")),
        "source_record_url": source_url,
        "source_title": title,
        "source_creator": source_name,
        "source_date_text": f"{clean(row.get('period_start'))}-{clean(row.get('period_end'))} coverage target",
        "date_start": clean(row.get("period_start")) or "1990",
        "date_end": clean(row.get("period_end")) or "2026",
        "source_place_text": " / ".join(part for part in [macro_region, country] if part),
        "source_object_type": "source profile / archive-source record",
        "source_medium": "source metadata; catalogue landing page; public source profile",
        "source_collection": source_name,
        "source_description": description,
        "source_notes": f"protocols={protocols}; evidence={protocol_evidence}; adapter_hint={clean(row.get('probe_adapter_hint'))}",
        "source_subjects": subjects,
        "source_rights_text": rights_note,
        "rights_uri": "",
        "rights_basis": rights_note,
        "image_presence_code": "IMG04",
        "image_presence_basis": "A source-profile text page was captured; no image display is expected for this record.",
        "image_state_evaluation": "IMG04: true source-profile text page, not a parser failure.",
        "image_state_confidence": "high",
        "rights_review_required": "true",
        "image_state_review_note": "No IMG01 or IMG03 promotion; impact/source priority remains internal triage only.",
        "image_frame_behavior": "no_image_frame",
        "image_url_detected": "",
        "local_copy_permitted": "false",
        "iiif_or_viewer_available": "false",
        "fallback_required": "false",
        "fallback_reason": "",
        "raw_json_path": "",
        "access_date": ACCESS_DATE,
        "image_expectation": "not_expected",
        "parser_status": "ok",
        "display_mode": "no_image_frame",
        "ocr_or_excerpt": description,
        "source_description_raw": description,
        "editorial_summary": context,
        "historical_context_note": context,
        "classification_rationale": classification,
        "uncertainty_note": "This is source-level discovery/profile coverage, not item-level rights clearance or publication-grade image evidence.",
        "citation_basis": f"{source_name}. {title}. {source_url}. Accessed {ACCESS_DATE}.",
    }
    return {field: clean(base.get(field, "")) for field in FIELDNAMES}


def main() -> None:
    rows = merge_rows()
    records = [record_from_row(row, index + 1) for index, row in enumerate(rows)]
    write_csv(RECORDS_CSV, records, FIELDNAMES)

    by_source = {row["source_name"]: row for row in rows}
    summary_rows: list[dict[str, str]] = []
    impact_rows: list[dict[str, str]] = []
    for record in records:
        source_row = by_source.get(record["source_name"], {})
        summary_rows.append(
            {
                "source_id": record["source_id"],
                "source_name": record["source_name"],
                "macro_region": clean(source_row.get("macro_region")),
                "country_or_region": clean(source_row.get("country_or_region")),
                "protocol_family": clean(source_row.get("protocol_family") or source_row.get("probe_detected_protocols")),
                "captured_records": "1",
                "image_states": "IMG04:1",
                "impact_ratings": f"{clean(source_row.get('impact_rating'))}:1",
                "detected_protocols": clean(source_row.get("probe_detected_protocols")),
                "notes": "source-profile metadata capture; no image download or rights upgrade",
            }
        )
        impact_rows.append(
            {
                "capture_id": record["capture_id"],
                "source_name": record["source_name"],
                "macro_region": clean(source_row.get("macro_region")),
                "country_or_region": clean(source_row.get("country_or_region")),
                "impact_score": clean(source_row.get("impact_score")),
                "impact_rating": clean(source_row.get("impact_rating")),
                "impact_basis": clean(source_row.get("impact_basis"), max_chars=600),
                "source_record_url": record["source_record_url"],
            }
        )
    write_csv(SUMMARY_CSV, summary_rows, SUMMARY_FIELDS)
    write_csv(IMPACT_CSV, impact_rows, IMPACT_FIELDS)

    region_counts = Counter(row["macro_region"] for row in summary_rows)
    protocol_counts = Counter(row["protocol_family"] for row in summary_rows)
    impact_counts = Counter(row["impact_rating"] for row in impact_rows)
    priority_counts = Counter(row.get("probe_capture_priority_next") for row in rows)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Non-mainstream Source Profile Capture 1990-2026 v1",
        "",
        f"Access date: {ACCESS_DATE}",
        "",
        "This pass turns successful v3 source probes into source-profile sheets. It is source-level metadata capture only.",
        "",
        "## Metrics",
        "",
        f"- Candidate/probe ok rows converted: {len(records)}",
        f"- Record health: {len(records)}/{len(records)} ({pct(len(records), len(records))}%)",
        f"- IMG rate: 0/{len(records)} open/source-visible item images (0.00%)",
        f"- IMG04 source-profile text pages: {len(records)}",
        "",
        "## Macro-region Distribution",
        "",
    ]
    for region, count in region_counts.most_common():
        lines.append(f"- {region}: {count}")
    lines.extend(["", "## Protocol Family Distribution", ""])
    for protocol, count in protocol_counts.most_common():
        lines.append(f"- {protocol or '(blank)'}: {count}")
    lines.extend(["", "## Impact Rating Distribution", ""])
    for rating, count in impact_counts.most_common():
        lines.append(f"- {rating or '(blank)'}: {count}")
    lines.extend(["", "## Next Capture Priority Distribution", ""])
    for priority, count in priority_counts.most_common():
        lines.append(f"- {priority or '(blank)'}: {count}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No image binaries, thumbnails, screenshots, or source raw payloads were downloaded.",
            "- All rows are `IMG04` because they are source-profile text pages, not parser failures.",
            "- `IMG01` and `IMG03` were not automatically upgraded from heuristics, LLM inference, terms-of-service text, platform signals, protocol evidence, source priority, or impact score.",
            "- Impact/source priority is internal triage only.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"converted_ok_sources={len(records)}")
    print("macro_regions=" + ",".join(f"{k}:{v}" for k, v in region_counts.most_common()))
    print("protocol_families=" + ",".join(f"{k or '(blank)'}:{v}" for k, v in protocol_counts.most_common()))
    print("impact_ratings=" + ",".join(f"{k or '(blank)'}:{v}" for k, v in impact_counts.most_common()))
    print(f"wrote {RECORDS_CSV.relative_to(ROOT)}")
    print(f"wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"wrote {IMPACT_CSV.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
