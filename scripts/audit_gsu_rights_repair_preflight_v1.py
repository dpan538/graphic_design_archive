#!/usr/bin/env python3
"""Audit GSU CONTENTdm IMG02 candidates against local records and raw rights.

This preflight reads already captured CSV/JSON metadata only. It does not call
CONTENTdm, download images, mutate records, or upgrade IMG01/IMG03.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from lib.archive_audit import DATA, DOCS, ROOT, capture_record_files, clean, normalize_url, read_csv, write_csv


SOURCE_NAME = "Georgia State University Library Digital Collections / CONTENTdm"
CANDIDATES = DATA / "image_rights_repair_candidates_v1.csv"
OUTPUT_ROWS = DATA / "gsu_rights_repair_preflight_v1.csv"
OUTPUT_SUMMARY = DATA / "gsu_rights_repair_summary_v1.csv"
OUTPUT_REPORT = DOCS / "GSU_RIGHTS_REPAIR_PREFLIGHT_v1.md"

ROW_FIELDS = [
    "surface_id",
    "source_record_id",
    "source_record_url",
    "title",
    "best_image_state",
    "weighted_gap_points",
    "local_record_found",
    "local_capture_id",
    "local_record_file",
    "local_image_state",
    "local_rights_review_required",
    "local_rights_text_excerpt",
    "raw_record_found",
    "raw_rights_uri",
    "raw_rights_text_excerpt",
    "raw_rights_signal",
    "rights_signal",
    "future_action",
    "upgrade_recommendation",
    "automatic_upgrade_allowed",
    "iiif_or_viewer_available",
    "image_url_detected_excerpt",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]

OPEN_URI_TERMS = [
    "creativecommons.org/publicdomain/zero",
    "rightsstatements.org/vocab/noc",
]

OPEN_TEXT_TERMS = [
    "cc0",
    "public domain",
    "no known copyright",
    "no copyright",
]

BLOCKING_URI_TERMS = [
    "rightsstatements.org/vocab/inc",
    "rightsstatements.org/vocab/inc-edu",
    "rightsstatements.org/vocab/inc-nc",
]

BLOCKING_TEXT_TERMS = [
    "protected by copyright",
    "copyright to this item is owned",
    "permission",
    "educational uses",
    "for research and educational purposes",
    "rights-holder",
    "rights holder",
]


def excerpt(value: str, limit: int = 240) -> str:
    value = re.sub(r"\s+", " ", clean(value))
    if len(value) <= limit:
        return value
    return value[: limit - 1].rsplit(" ", 1)[0] + "..."


def records_by_url() -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    for path in capture_record_files():
        for row in read_csv(path):
            if row.get("source_name") != SOURCE_NAME:
                continue
            url = normalize_url(row.get("source_record_url", ""))
            if not url:
                continue
            candidate = dict(row)
            candidate["_record_file"] = str(path.relative_to(ROOT))
            records.setdefault(url, candidate)
    return records


def raw_path_for(row: dict[str, str] | None) -> Path | None:
    if not row:
        return None
    raw_value = clean(row.get("raw_json_path"))
    if not raw_value:
        return None
    path = ROOT / raw_value
    return path if path.exists() else None


def raw_fields(row: dict[str, str] | None) -> tuple[bool, str, str]:
    path = raw_path_for(row)
    if path is None:
        return False, "", ""
    try:
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, "", ""
    rights_text = ""
    rights_uri = ""
    for field in payload.get("fields", []):
        if not isinstance(field, dict):
            continue
        key = clean(field.get("key")).lower()
        label = clean(field.get("label")).lower()
        value = clean(field.get("value"))
        if key == "rightl" or label == "local rights statement":
            rights_text = value
        if key == "rights" or label == "standardized rights statements":
            rights_uri = value
    return True, rights_text, rights_uri


def raw_rights_signal(rights_text: str, rights_uri: str, raw_found: bool) -> str:
    if not raw_found:
        return "raw_record_missing"
    blob = f"{rights_text} {rights_uri}".lower()
    open_flag = any(term in blob for term in OPEN_URI_TERMS) or any(term in blob for term in OPEN_TEXT_TERMS)
    block_flag = any(term in blob for term in BLOCKING_URI_TERMS) or any(term in blob for term in BLOCKING_TEXT_TERMS)
    if open_flag and block_flag:
        return "mixed_open_and_blocking_raw_rights"
    if open_flag:
        return "raw_open_rights_signal"
    if block_flag:
        return "raw_blocking_or_permission_rights_signal"
    if rights_text or rights_uri:
        return "raw_rights_present_unclassified"
    return "raw_rights_statement_missing"


def signal_from_record(row: dict[str, str] | None) -> tuple[str, str, str, bool, str, str, str]:
    if not row:
        return (
            "local_record_missing",
            "contentdm_item_probe_required",
            "no_upgrade",
            False,
            "",
            "",
            "raw_record_missing",
        )
    raw_found, rights_text, rights_uri = raw_fields(row)
    raw_signal = raw_rights_signal(rights_text, rights_uri, raw_found)
    if raw_signal == "raw_open_rights_signal":
        return (
            "raw_open_rights_signal_needs_record_rebuild_review",
            "rebuild_record_with_raw_rights_evidence_after_manual_check",
            "review_rebuild_alignment_no_automatic_upgrade",
            raw_found,
            rights_text,
            rights_uri,
            raw_signal,
        )
    if raw_signal in {"raw_blocking_or_permission_rights_signal", "mixed_open_and_blocking_raw_rights"}:
        return (
            "blocked_by_raw_copyright_or_permission_signal",
            "keep_img02_pending_explicit_open_rights",
            "no_upgrade",
            raw_found,
            rights_text,
            rights_uri,
            raw_signal,
        )
    if raw_signal == "raw_rights_present_unclassified":
        return (
            "raw_rights_present_but_unclassified",
            "manual_contentdm_rights_review_required",
            "no_upgrade",
            raw_found,
            rights_text,
            rights_uri,
            raw_signal,
        )
    return (
        "raw_rights_statement_missing",
        "contentdm_item_rights_probe_required",
        "no_upgrade",
        raw_found,
        rights_text,
        rights_uri,
        raw_signal,
    )


def build_rows() -> list[dict[str, str]]:
    records = records_by_url()
    rows = []
    for candidate in read_csv(CANDIDATES):
        if candidate.get("source_name") != SOURCE_NAME:
            continue
        record = records.get(normalize_url(candidate.get("source_url", "")))
        signal, action, recommendation, raw_found, raw_rights_text, raw_rights_uri, raw_signal = signal_from_record(record)
        rows.append(
            {
                "surface_id": candidate.get("surface_id", ""),
                "source_record_id": clean(record.get("source_identifier")) if record else "",
                "source_record_url": candidate.get("source_url", ""),
                "title": candidate.get("title", ""),
                "best_image_state": candidate.get("best_image_state", ""),
                "weighted_gap_points": candidate.get("weighted_gap_points", ""),
                "local_record_found": str(record is not None).lower(),
                "local_capture_id": clean(record.get("capture_id")) if record else "",
                "local_record_file": clean(record.get("_record_file")) if record else "",
                "local_image_state": clean(record.get("image_presence_code")) if record else "",
                "local_rights_review_required": clean(record.get("rights_review_required")) if record else "",
                "local_rights_text_excerpt": excerpt(record.get("source_rights_text", "")) if record else "",
                "raw_record_found": str(raw_found).lower(),
                "raw_rights_uri": raw_rights_uri,
                "raw_rights_text_excerpt": excerpt(raw_rights_text),
                "raw_rights_signal": raw_signal,
                "rights_signal": signal,
                "future_action": action,
                "upgrade_recommendation": recommendation,
                "automatic_upgrade_allowed": "false",
                "iiif_or_viewer_available": clean(record.get("iiif_or_viewer_available")) if record else "",
                "image_url_detected_excerpt": excerpt(record.get("image_url_detected", "")) if record else "",
            }
        )
    rows.sort(key=lambda row: (row["upgrade_recommendation"], row["raw_rights_signal"], row["title"], row["surface_id"]))
    return rows


def weighted_points(rows: list[dict[str, str]], recommendation: str | None = None) -> float:
    total = 0.0
    for row in rows:
        if recommendation is not None and row["upgrade_recommendation"] != recommendation:
            continue
        try:
            total += float(row.get("weighted_gap_points") or 0)
        except ValueError:
            continue
    return total


def write_report(rows: list[dict[str, str]]) -> None:
    states = Counter(row["local_image_state"] or "missing" for row in rows)
    found = Counter(row["local_record_found"] for row in rows)
    raw_found = Counter(row["raw_record_found"] for row in rows)
    raw_signals = Counter(row["raw_rights_signal"] for row in rows)
    rights_signals = Counter(row["rights_signal"] for row in rows)
    recommendations = Counter(row["upgrade_recommendation"] for row in rows)

    summary_rows = [
        {"metric": "gsu_candidate_rows", "value": str(len(rows)), "notes": "GSU rows from image_rights_repair_candidates_v1."},
        {"metric": "local_records_found", "value": str(found.get("true", 0)), "notes": "Rows matched to existing local capture records."},
        {"metric": "raw_records_found", "value": str(raw_found.get("true", 0)), "notes": "Rows with local raw CONTENTdm JSON available."},
        {"metric": "automatic_upgrade_allowed_rows", "value": "0", "notes": "No automatic IMG03 upgrades are permitted by this preflight."},
        {"metric": "candidate_weighted_gap_points", "value": f"{weighted_points(rows):.2f}", "notes": "Weighted-publication gap points represented by these candidates."},
    ]
    for key, value in states.most_common():
        summary_rows.append({"metric": f"local_image_state_{key}", "value": str(value), "notes": "Best matching local capture state."})
    for key, value in raw_signals.most_common():
        summary_rows.append({"metric": f"raw_rights_signal_{key}", "value": str(value), "notes": "Signal recovered from local raw CONTENTdm JSON."})
    for key, value in rights_signals.most_common():
        summary_rows.append({"metric": f"rights_signal_{key}", "value": str(value), "notes": "Conservative rights-repair signal."})
    for key, value in recommendations.most_common():
        summary_rows.append({"metric": f"upgrade_recommendation_{key}", "value": str(value), "notes": f"{weighted_points(rows, key):.2f} weighted points."})
    write_csv(OUTPUT_SUMMARY, summary_rows, SUMMARY_FIELDS)

    lines = [
        "# GSU CONTENTdm Rights Repair Preflight v1",
        "",
        "This local preflight checks GSU CONTENTdm IMG02 candidates against already captured CSV records and local raw CONTENTdm JSON. It does not call CONTENTdm, download images, mutate records, or upgrade IMG01/IMG03.",
        "",
        "## Result",
        "",
        f"- GSU candidate rows: {len(rows)}",
        f"- local records found: {found.get('true', 0)}",
        f"- raw records found: {raw_found.get('true', 0)}",
        "- automatic upgrades allowed: 0",
        f"- candidate weighted gap points: {weighted_points(rows):.2f}",
        "",
        "## Local Image States",
        "",
    ]
    for key, value in states.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Raw Rights Signals", ""])
    for key, value in raw_signals.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Rights Signals", ""])
    for key, value in rights_signals.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Upgrade Recommendations", ""])
    for key, value in recommendations.most_common():
        lines.append(f"- {key}: {value} ({weighted_points(rows, key):.2f} weighted points)")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- GSU is not a broad verified-open repair route under the current evidence. Most raw records carry copyright, permission, InC, or educational-use signals.",
            "- One local raw record carries a CC0 URI. It is still not automatically upgraded; it should be manually checked and then rebuilt so the public record preserves the item-level rights evidence.",
            "- The existing GSU capture path appears to overwrite the source rights statement with image-state basis text in the record CSV. A future capture-script patch should preserve both local rights text and image-display basis separately.",
            "- GSU remains useful for regional/local print-culture coverage, but rights repair should be selective rather than counted as a bulk IMG03 gain.",
            "",
            "## Output Files",
            "",
            f"- `{OUTPUT_ROWS.relative_to(ROOT)}`",
            f"- `{OUTPUT_SUMMARY.relative_to(ROOT)}`",
        ]
    )
    OUTPUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(OUTPUT_ROWS, rows, ROW_FIELDS)
    write_report(rows)
    print(f"gsu_candidate_rows={len(rows)}")
    print(f"wrote {OUTPUT_ROWS.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
