#!/usr/bin/env python3
"""Audit Art Institute of Chicago repair candidates against local metadata.

This preflight reads already captured CSV/JSON only. It does not call AIC APIs,
download images, mutate records, or upgrade IMG01/IMG03.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from lib.archive_audit import DATA, DOCS, ROOT, capture_record_files, clean, normalize_url, read_csv, write_csv


SOURCE_NAME = "Art Institute of Chicago API"
CANDIDATES = DATA / "image_rights_repair_candidates_v1.csv"
OUTPUT_ROWS = DATA / "aic_rights_repair_preflight_v1.csv"
OUTPUT_SUMMARY = DATA / "aic_rights_repair_summary_v1.csv"
OUTPUT_REPORT = DOCS / "AIC_RIGHTS_REPAIR_PREFLIGHT_v1.md"

ROW_FIELDS = [
    "surface_id",
    "source_record_id",
    "source_record_url",
    "title",
    "best_image_state",
    "repair_family",
    "weighted_gap_points",
    "local_record_found",
    "local_capture_id",
    "local_record_file",
    "local_image_state",
    "local_rights_review_required",
    "raw_record_found",
    "raw_is_public_domain",
    "raw_image_id_present",
    "raw_rights_signal",
    "rights_signal",
    "future_action",
    "upgrade_recommendation",
    "automatic_upgrade_allowed",
    "image_url_detected_excerpt",
    "rights_basis_excerpt",
    "review_note_excerpt",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]

IMAGE_STATE_SCORE = {
    "IMG03": 4,
    "IMG02": 3,
    "IMG01": 2,
    "IMG00": 1,
    "IMG04": 0,
}


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
            existing = records.get(url)
            if existing is None or IMAGE_STATE_SCORE.get(candidate.get("image_presence_code", ""), 0) > IMAGE_STATE_SCORE.get(existing.get("image_presence_code", ""), 0):
                records[url] = candidate
    return records


def raw_path_for(row: dict[str, str] | None) -> Path | None:
    if not row:
        return None
    raw_value = clean(row.get("raw_json_path"))
    if not raw_value:
        return None
    path = ROOT / raw_value
    return path if path.exists() else None


def iter_raw_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        if isinstance(payload.get("data"), list):
            return [item for item in payload["data"] if isinstance(item, dict)]
        if isinstance(payload.get("data"), dict):
            return [payload["data"]]
        return [payload]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def raw_aic_signal(row: dict[str, str] | None) -> tuple[bool, str, str]:
    path = raw_path_for(row)
    if path is None or not row:
        return False, "", "false"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, "", "false"
    source_id = clean(row.get("source_identifier"))
    for item in iter_raw_items(payload):
        if clean(item.get("id")) != source_id:
            continue
        raw_pd = str(item.get("is_public_domain")).lower() if item.get("is_public_domain") is not None else ""
        image_id = clean(item.get("image_id"))
        return True, raw_pd, str(bool(image_id)).lower()
    return False, "", "false"


def raw_rights_signal(raw_found: bool, raw_pd: str, image_id_present: str) -> str:
    if not raw_found:
        return "raw_record_missing"
    if raw_pd == "true" and image_id_present == "true":
        return "raw_public_domain_image_signal"
    if raw_pd == "false" and image_id_present == "true":
        return "raw_image_id_non_public_domain"
    if raw_pd == "false":
        return "raw_non_public_domain_no_image_id"
    if image_id_present == "true":
        return "raw_image_id_without_public_domain_status"
    return "raw_no_image_identifier"


def signal_from_record(row: dict[str, str] | None) -> tuple[str, str, str, bool, str, str, str]:
    if not row:
        return ("local_record_missing", "aic_item_api_probe_required", "no_upgrade", False, "", "false", "raw_record_missing")
    raw_found, raw_pd, image_id_present = raw_aic_signal(row)
    raw_signal = raw_rights_signal(raw_found, raw_pd, image_id_present)
    if raw_signal == "raw_public_domain_image_signal":
        return (
            "raw_public_domain_image_needs_rebuild_review",
            "rebuild_record_with_aic_public_domain_image_evidence_after_manual_check",
            "review_rebuild_alignment_no_automatic_upgrade",
            raw_found,
            raw_pd,
            image_id_present,
            raw_signal,
        )
    if raw_signal == "raw_image_id_non_public_domain":
        return (
            "image_identifier_not_public_domain",
            "keep_empty_or_item_probe_for_rights_change",
            "no_upgrade",
            raw_found,
            raw_pd,
            image_id_present,
            raw_signal,
        )
    if raw_signal == "raw_image_id_without_public_domain_status":
        return (
            "image_identifier_public_domain_status_missing",
            "aic_item_api_rights_probe_required",
            "item_rights_capture_required",
            raw_found,
            raw_pd,
            image_id_present,
            raw_signal,
        )
    return (
        "no_public_domain_image_evidence",
        "aic_item_api_probe_required",
        "no_upgrade",
        raw_found,
        raw_pd,
        image_id_present,
        raw_signal,
    )


def build_rows() -> list[dict[str, str]]:
    records = records_by_url()
    rows = []
    for candidate in read_csv(CANDIDATES):
        if candidate.get("source_name") != SOURCE_NAME:
            continue
        record = records.get(normalize_url(candidate.get("source_url", "")))
        signal, action, recommendation, raw_found, raw_pd, image_id_present, raw_signal = signal_from_record(record)
        rows.append(
            {
                "surface_id": candidate.get("surface_id", ""),
                "source_record_id": clean(record.get("source_identifier")) if record else "",
                "source_record_url": candidate.get("source_url", ""),
                "title": candidate.get("title", ""),
                "best_image_state": candidate.get("best_image_state", ""),
                "repair_family": candidate.get("repair_family", ""),
                "weighted_gap_points": candidate.get("weighted_gap_points", ""),
                "local_record_found": str(record is not None).lower(),
                "local_capture_id": clean(record.get("capture_id")) if record else "",
                "local_record_file": clean(record.get("_record_file")) if record else "",
                "local_image_state": clean(record.get("image_presence_code")) if record else "",
                "local_rights_review_required": clean(record.get("rights_review_required")) if record else "",
                "raw_record_found": str(raw_found).lower(),
                "raw_is_public_domain": raw_pd,
                "raw_image_id_present": image_id_present,
                "raw_rights_signal": raw_signal,
                "rights_signal": signal,
                "future_action": action,
                "upgrade_recommendation": recommendation,
                "automatic_upgrade_allowed": "false",
                "image_url_detected_excerpt": excerpt(record.get("image_url_detected", "")) if record else "",
                "rights_basis_excerpt": excerpt(record.get("rights_basis", "")) if record else "",
                "review_note_excerpt": excerpt(record.get("image_state_review_note", "")) if record else "",
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
    repair_families = Counter(row["repair_family"] for row in rows)
    raw_signals = Counter(row["raw_rights_signal"] for row in rows)
    rights_signals = Counter(row["rights_signal"] for row in rows)
    recommendations = Counter(row["upgrade_recommendation"] for row in rows)
    found = Counter(row["local_record_found"] for row in rows)
    raw_found = Counter(row["raw_record_found"] for row in rows)

    summary_rows = [
        {"metric": "aic_candidate_rows", "value": str(len(rows)), "notes": "AIC rows from image_rights_repair_candidates_v1."},
        {"metric": "local_records_found", "value": str(found.get("true", 0)), "notes": "Rows matched to existing local capture records."},
        {"metric": "raw_records_found", "value": str(raw_found.get("true", 0)), "notes": "Rows with local raw AIC JSON found."},
        {"metric": "automatic_upgrade_allowed_rows", "value": "0", "notes": "No automatic IMG03 upgrades are permitted by this preflight."},
        {"metric": "candidate_weighted_gap_points", "value": f"{weighted_points(rows):.2f}", "notes": "Weighted-publication gap points represented by these candidates."},
    ]
    for key, value in repair_families.most_common():
        summary_rows.append({"metric": f"repair_family_{key}", "value": str(value), "notes": "Original repair family."})
    for key, value in states.most_common():
        summary_rows.append({"metric": f"local_image_state_{key}", "value": str(value), "notes": "Best matching local capture state."})
    for key, value in raw_signals.most_common():
        summary_rows.append({"metric": f"raw_rights_signal_{key}", "value": str(value), "notes": "Signal recovered from local raw AIC JSON."})
    for key, value in rights_signals.most_common():
        summary_rows.append({"metric": f"rights_signal_{key}", "value": str(value), "notes": "Conservative rights-repair signal."})
    for key, value in recommendations.most_common():
        summary_rows.append({"metric": f"upgrade_recommendation_{key}", "value": str(value), "notes": f"{weighted_points(rows, key):.2f} weighted points."})
    write_csv(OUTPUT_SUMMARY, summary_rows, SUMMARY_FIELDS)

    lines = [
        "# AIC Rights Repair Preflight v1",
        "",
        "This local preflight checks Art Institute of Chicago repair candidates against already captured CSV/JSON metadata. It does not call AIC APIs, download images, mutate records, or upgrade IMG01/IMG03.",
        "",
        "## Result",
        "",
        f"- AIC candidate rows: {len(rows)}",
        f"- local records found: {found.get('true', 0)}",
        f"- raw records found: {raw_found.get('true', 0)}",
        "- automatic upgrades allowed: 0",
        f"- candidate weighted gap points: {weighted_points(rows):.2f}",
        "",
        "## Repair Families",
        "",
    ]
    for key, value in repair_families.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Local Image States", ""])
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
            "- AIC is not an immediate verified-open repair family in this candidate set. The local raw search metadata marks most image-bearing candidates as `is_public_domain=false`.",
            "- These rows may still be valuable source records, but publication-grade open image display requires item-level public-domain evidence, not merely an AIC image identifier or IIIF URL.",
            "- Future AIC work should use item API probes to confirm whether any source records changed rights status, then rebuild only rows with explicit public-domain evidence.",
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
    print(f"aic_candidate_rows={len(rows)}")
    print(f"wrote {OUTPUT_ROWS.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
