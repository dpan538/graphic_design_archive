#!/usr/bin/env python3
"""Audit Library of Congress IMG repair candidates against local records.

This preflight only reads already captured metadata. It does not call loc.gov,
download images, mutate surfaces, or promote IMG01/IMG03.
"""

from __future__ import annotations

import re
from collections import Counter

from lib.archive_audit import DATA, DOCS, ROOT, capture_record_files, clean, normalize_url, read_csv, write_csv


SOURCE_NAME = "Library of Congress loc.gov API"
CANDIDATES = DATA / "image_rights_repair_candidates_v1.csv"
OUTPUT_ROWS = DATA / "loc_rights_repair_preflight_v1.csv"
OUTPUT_SUMMARY = DATA / "loc_rights_repair_summary_v1.csv"
OUTPUT_REPORT = DOCS / "LOC_RIGHTS_REPAIR_PREFLIGHT_v1.md"

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
    "local_rights_signal",
    "rights_signal",
    "future_action",
    "upgrade_recommendation",
    "automatic_upgrade_allowed",
    "iiif_or_viewer_available",
    "image_url_detected_excerpt",
    "rights_text_excerpt",
    "rights_basis_excerpt",
    "review_note_excerpt",
    "source_notes_excerpt",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]

IMAGE_STATE_SCORE = {
    "IMG03": 4,
    "IMG02": 3,
    "IMG01": 2,
    "IMG00": 1,
    "IMG04": 0,
}

OPEN_TERMS = [
    "no known restrictions",
    "public domain",
    "public-domain",
    "unrestricted",
]

BLOCKING_TERMS = [
    "rights status not evaluated",
    "may be restricted",
    "restricted",
    "permission",
    "copyright",
]


def excerpt(value: str, limit: int = 220) -> str:
    value = re.sub(r"\s+", " ", clean(value))
    if len(value) <= limit:
        return value
    return value[: limit - 1].rsplit(" ", 1)[0] + "..."


def legal_blob(row: dict[str, str]) -> str:
    return " ".join(
        [
            row.get("source_notes", ""),
            row.get("source_rights_text", ""),
            row.get("rights_uri", ""),
            row.get("rights_basis", ""),
            row.get("image_presence_basis", ""),
            row.get("image_state_evaluation", ""),
            row.get("image_state_review_note", ""),
        ]
    )


def rights_signal_from_text(row: dict[str, str] | None) -> str:
    if not row:
        return "missing"
    blob = legal_blob(row).lower()
    open_flag = any(term in blob for term in OPEN_TERMS)
    block_flag = any(term in blob for term in BLOCKING_TERMS)
    if open_flag and block_flag:
        return "mixed_open_and_blocking_terms"
    if open_flag:
        return "local_open_rights_advisory_text"
    if block_flag:
        return "blocking_or_unresolved_rights_terms"
    return "no_item_rights_advisory_text"


def has_no_image_signal(row: dict[str, str]) -> bool:
    blob = " ".join(
        [
            row.get("image_url_detected", ""),
            row.get("image_presence_basis", ""),
            row.get("image_state_evaluation", ""),
            row.get("image_state_review_note", ""),
        ]
    ).lower()
    return "notdigitized" in blob or "not_digitized" in blob or "does not expose a usable image" in blob or "no image frame" in blob


def record_score(row: dict[str, str]) -> tuple[int, int]:
    state = clean(row.get("image_presence_code"))
    return (
        IMAGE_STATE_SCORE.get(state, 0),
        1 if rights_signal_from_text(row) == "local_open_rights_advisory_text" else 0,
    )


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
            if existing is None or record_score(candidate) > record_score(existing):
                records[url] = candidate
    return records


def signal_from_record(row: dict[str, str] | None) -> tuple[str, str, str]:
    if not row:
        return "local_record_missing", "loc_item_json_probe_required", "item_rights_capture_required"

    state = clean(row.get("image_presence_code")) or "IMG00"
    text_signal = rights_signal_from_text(row)
    image_url = clean(row.get("image_url_detected"))
    viewer = clean(row.get("iiif_or_viewer_available"))

    if state == "IMG03" and text_signal == "local_open_rights_advisory_text":
        return "local_open_rights_needs_payload_alignment", "compare_public_payload_and_rebuild_alignment", "review_rebuild_alignment_no_automatic_upgrade"
    if state in {"IMG00", "IMG04"} or has_no_image_signal(row):
        return "no_usable_image_in_local_capture", "loc_deep_item_image_probe_required", "source_visible_repair_needed"
    if state == "IMG01" and image_url:
        return "thumbnail_only_item_rights_missing", "loc_item_rights_and_image_derivative_capture_required", "item_rights_capture_required"
    if state == "IMG02" and viewer:
        return "source_viewer_item_rights_missing", "loc_item_rights_capture_required", "item_rights_capture_required"
    if text_signal == "blocking_or_unresolved_rights_terms":
        return "local_rights_blocked_or_unresolved", "manual_loc_rights_review_required", "no_upgrade"
    return "no_item_rights_advisory_text", "loc_item_rights_capture_required", "item_rights_capture_required"


def build_rows() -> list[dict[str, str]]:
    records = records_by_url()
    rows = []
    for candidate in read_csv(CANDIDATES):
        if candidate.get("source_name") != SOURCE_NAME:
            continue
        record = records.get(normalize_url(candidate.get("source_url", "")))
        signal, action, recommendation = signal_from_record(record)
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
                "local_rights_signal": rights_signal_from_text(record),
                "rights_signal": signal,
                "future_action": action,
                "upgrade_recommendation": recommendation,
                "automatic_upgrade_allowed": "false",
                "iiif_or_viewer_available": clean(record.get("iiif_or_viewer_available")) if record else "",
                "image_url_detected_excerpt": excerpt(record.get("image_url_detected", "")) if record else "",
                "rights_text_excerpt": excerpt(record.get("source_rights_text", "")) if record else "",
                "rights_basis_excerpt": excerpt(record.get("rights_basis", "")) if record else "",
                "review_note_excerpt": excerpt(record.get("image_state_review_note", "")) if record else "",
                "source_notes_excerpt": excerpt(record.get("source_notes", "")) if record else "",
            }
        )
    rows.sort(key=lambda row: (row["upgrade_recommendation"], row["repair_family"], row["title"], row["surface_id"]))
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
    rights_signals = Counter(row["rights_signal"] for row in rows)
    local_rights_signals = Counter(row["local_rights_signal"] for row in rows)
    recommendations = Counter(row["upgrade_recommendation"] for row in rows)
    found = Counter(row["local_record_found"] for row in rows)

    summary_rows = [
        {"metric": "loc_candidate_rows", "value": str(len(rows)), "notes": "Library of Congress rows from image_rights_repair_candidates_v1."},
        {"metric": "local_records_found", "value": str(found.get("true", 0)), "notes": "Rows matched to existing local capture records."},
        {"metric": "automatic_upgrade_allowed_rows", "value": "0", "notes": "No automatic IMG03 upgrades are permitted by this preflight."},
        {"metric": "candidate_weighted_gap_points", "value": f"{weighted_points(rows):.2f}", "notes": "Weighted-publication gap points represented by these candidates."},
    ]
    for key, value in repair_families.most_common():
        summary_rows.append({"metric": f"repair_family_{key}", "value": str(value), "notes": "Original repair family."})
    for key, value in states.most_common():
        summary_rows.append({"metric": f"local_image_state_{key}", "value": str(value), "notes": "Best matching local capture state."})
    for key, value in local_rights_signals.most_common():
        summary_rows.append({"metric": f"local_rights_signal_{key}", "value": str(value), "notes": "Local rights-advisory signal."})
    for key, value in rights_signals.most_common():
        summary_rows.append({"metric": f"rights_signal_{key}", "value": str(value), "notes": "Conservative local metadata signal."})
    for key, value in recommendations.most_common():
        summary_rows.append({"metric": f"upgrade_recommendation_{key}", "value": str(value), "notes": f"{weighted_points(rows, key):.2f} weighted points."})
    write_csv(OUTPUT_SUMMARY, summary_rows, SUMMARY_FIELDS)

    lines = [
        "# Library of Congress Rights Repair Preflight v1",
        "",
        "This local preflight checks Library of Congress IMG repair candidates against already captured item metadata. It does not call loc.gov, download images, mutate surfaces, or upgrade IMG01/IMG03.",
        "",
        "## Result",
        "",
        f"- LOC candidate rows: {len(rows)}",
        f"- local records found: {found.get('true', 0)}",
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
    lines.extend(["", "## Local Rights Signals", ""])
    for key, value in local_rights_signals.most_common():
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
            "- LOC is a stronger repair route than Cooper Hewitt/Wellcome because most candidates are thumbnail or no-image records where item-level image and rights data may not yet have been captured.",
            "- The 37 IMG01 rows should not be upgraded automatically; they need loc.gov item JSON/page rights-advisory capture and image derivative evidence.",
            "- The 13 IMG04 rows should be deep-probed before being accepted as true text-only pages, because an earlier search row may have missed item-level images.",
            "- Any later LOC upgrade must store the item page, rights advisory, source URL, and image evidence; source-family reputation alone is not sufficient.",
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
    print(f"loc_candidate_rows={len(rows)}")
    print(f"wrote {OUTPUT_ROWS.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
