#!/usr/bin/env python3
"""Audit V&A repair candidates against local object-detail metadata.

This preflight reads already captured CSV and `vam_object_*.json` files only.
It does not call V&A APIs, download images, mutate records, or upgrade
IMG01/IMG03.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from lib.archive_audit import DATA, DOCS, ROOT, capture_record_files, clean, normalize_url, read_csv, write_csv


SOURCE_NAME = "V&A Collections API"
CANDIDATES = DATA / "image_rights_repair_candidates_v1.csv"
OUTPUT_ROWS = DATA / "vam_rights_repair_preflight_v1.csv"
OUTPUT_SUMMARY = DATA / "vam_rights_repair_summary_v1.csv"
OUTPUT_REPORT = DOCS / "VAM_RIGHTS_REPAIR_PREFLIGHT_v1.md"

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
    "object_raw_found",
    "object_image_resolution",
    "object_image_copyright_excerpt",
    "object_image_signal",
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


def object_id_from_url(url: str) -> str:
    return clean(url).rstrip("/").split("/")[-1]


def object_raw_paths() -> dict[str, Path]:
    return {path.stem.replace("vam_object_", ""): path for path in DATA.glob("capture_batch_*_raw/vam_object_*.json")}


def object_image_metadata(object_id: str, raw_paths: dict[str, Path]) -> tuple[bool, str, str]:
    path = raw_paths.get(object_id)
    if path is None:
        return False, "", ""
    try:
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, "", ""
    meta_images = payload.get("meta", {}).get("images") if isinstance(payload.get("meta"), dict) else {}
    if not isinstance(meta_images, dict):
        meta_images = {}
    record = payload.get("record") if isinstance(payload.get("record"), dict) else {}
    image_resolution = clean(meta_images.get("imageResolution") or record.get("imageResolution"))
    copyrights: list[str] = []
    for image_meta in meta_images.get("_images_meta", []) or []:
        if isinstance(image_meta, dict) and clean(image_meta.get("copyright")):
            copyrights.append(clean(image_meta.get("copyright")))
    return True, image_resolution, "; ".join(copyrights)


def object_image_signal(raw_found: bool, image_resolution: str, copyright_text: str) -> str:
    if not raw_found:
        return "object_raw_missing"
    if copyright_text:
        return "object_image_copyright_metadata_present"
    if image_resolution:
        return "object_image_metadata_without_open_rights"
    return "object_detail_no_image_metadata"


def signal_from_record(row: dict[str, str] | None, raw_paths: dict[str, Path]) -> tuple[str, str, str, bool, str, str, str]:
    if not row:
        return ("local_record_missing", "vam_item_probe_required", "no_upgrade", False, "", "", "object_raw_missing")
    object_id = object_id_from_url(row.get("source_record_url", ""))
    raw_found, image_resolution, copyright_text = object_image_metadata(object_id, raw_paths)
    image_signal = object_image_signal(raw_found, image_resolution, copyright_text)
    state = clean(row.get("image_presence_code"))
    if image_signal == "object_image_copyright_metadata_present":
        return (
            "blocked_by_object_image_copyright_metadata",
            "keep_img02_or_img04_pending_open_item_evidence",
            "no_upgrade",
            raw_found,
            image_resolution,
            copyright_text,
            image_signal,
        )
    if state == "IMG04":
        return (
            "no_source_visible_image_in_public_record",
            "vam_visual_member_or_item_probe_required",
            "source_visible_repair_needed",
            raw_found,
            image_resolution,
            copyright_text,
            image_signal,
        )
    if image_signal == "object_image_metadata_without_open_rights":
        return (
            "source_hosted_image_metadata_without_open_rights",
            "manual_vam_rights_review_required",
            "no_upgrade",
            raw_found,
            image_resolution,
            copyright_text,
            image_signal,
        )
    return (
        "no_item_level_open_rights_evidence",
        "vam_item_rights_probe_required",
        "no_upgrade",
        raw_found,
        image_resolution,
        copyright_text,
        image_signal,
    )


def build_rows() -> list[dict[str, str]]:
    records = records_by_url()
    raw_paths = object_raw_paths()
    rows = []
    for candidate in read_csv(CANDIDATES):
        if candidate.get("source_name") != SOURCE_NAME:
            continue
        record = records.get(normalize_url(candidate.get("source_url", "")))
        signal, action, recommendation, raw_found, image_resolution, copyright_text, image_signal = signal_from_record(record, raw_paths)
        rows.append(
            {
                "surface_id": candidate.get("surface_id", ""),
                "source_record_id": clean(record.get("source_identifier")) if record else object_id_from_url(candidate.get("source_url", "")),
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
                "object_raw_found": str(raw_found).lower(),
                "object_image_resolution": image_resolution,
                "object_image_copyright_excerpt": excerpt(copyright_text),
                "object_image_signal": image_signal,
                "rights_signal": signal,
                "future_action": action,
                "upgrade_recommendation": recommendation,
                "automatic_upgrade_allowed": "false",
                "image_url_detected_excerpt": excerpt(record.get("image_url_detected", "")) if record else "",
                "rights_basis_excerpt": excerpt(record.get("rights_basis", "")) if record else "",
                "review_note_excerpt": excerpt(record.get("image_state_review_note", "")) if record else "",
            }
        )
    rows.sort(key=lambda row: (row["upgrade_recommendation"], row["object_image_signal"], row["title"], row["surface_id"]))
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
    raw_found = Counter(row["object_raw_found"] for row in rows)
    resolutions = Counter(row["object_image_resolution"] or "missing" for row in rows)
    image_signals = Counter(row["object_image_signal"] for row in rows)
    rights_signals = Counter(row["rights_signal"] for row in rows)
    recommendations = Counter(row["upgrade_recommendation"] for row in rows)

    summary_rows = [
        {"metric": "vam_candidate_rows", "value": str(len(rows)), "notes": "V&A rows from image_rights_repair_candidates_v1."},
        {"metric": "object_raw_records_found", "value": str(raw_found.get("true", 0)), "notes": "Rows with local V&A object detail JSON."},
        {"metric": "automatic_upgrade_allowed_rows", "value": "0", "notes": "No automatic IMG03 upgrades are permitted by this preflight."},
        {"metric": "candidate_weighted_gap_points", "value": f"{weighted_points(rows):.2f}", "notes": "Weighted-publication gap points represented by these candidates."},
    ]
    for key, value in repair_families.most_common():
        summary_rows.append({"metric": f"repair_family_{key}", "value": str(value), "notes": "Original repair family."})
    for key, value in states.most_common():
        summary_rows.append({"metric": f"local_image_state_{key}", "value": str(value), "notes": "Best matching local capture state."})
    for key, value in resolutions.most_common():
        summary_rows.append({"metric": f"object_image_resolution_{key}", "value": str(value), "notes": "V&A object image resolution metadata."})
    for key, value in image_signals.most_common():
        summary_rows.append({"metric": f"object_image_signal_{key}", "value": str(value), "notes": "Signal recovered from V&A object detail JSON."})
    for key, value in rights_signals.most_common():
        summary_rows.append({"metric": f"rights_signal_{key}", "value": str(value), "notes": "Conservative rights-repair signal."})
    for key, value in recommendations.most_common():
        summary_rows.append({"metric": f"upgrade_recommendation_{key}", "value": str(value), "notes": f"{weighted_points(rows, key):.2f} weighted points."})
    write_csv(OUTPUT_SUMMARY, summary_rows, SUMMARY_FIELDS)

    lines = [
        "# V&A Rights Repair Preflight v1",
        "",
        "This local preflight checks V&A repair candidates against already captured CSV records and local V&A object-detail JSON. It does not call V&A APIs, download images, mutate records, or upgrade IMG01/IMG03.",
        "",
        "## Result",
        "",
        f"- V&A candidate rows: {len(rows)}",
        f"- object raw records found: {raw_found.get('true', 0)}",
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
    lines.extend(["", "## Object Image Resolution", ""])
    for key, value in resolutions.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Object Image Signals", ""])
    for key, value in image_signals.most_common():
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
            "- V&A object detail metadata improves source-visible triage, but it does not provide bulk verified-open image evidence in this candidate set.",
            "- Rows with copyright metadata stay IMG02/IMG04 unless a later item page exposes explicit open/public-domain evidence.",
            "- Rows with image metadata but no open-rights statement may be useful source-hosted records, but they are not IMG03 repair candidates.",
            "- The compound IMG04 rows need member-level visual search rather than a source-family rights upgrade.",
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
    print(f"vam_candidate_rows={len(rows)}")
    print(f"wrote {OUTPUT_ROWS.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
