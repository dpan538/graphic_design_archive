#!/usr/bin/env python3
"""Audit Wellcome IMG repair candidates against local capture metadata.

This preflight is intentionally conservative. It reads already captured CSV
records and does not query Wellcome, fetch pages, download images, mutate
surfaces, or upgrade IMG01/IMG03.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from lib.archive_audit import DATA, DOCS, ROOT, capture_record_files, clean, normalize_url, read_csv, write_csv


SOURCE_NAME = "Wellcome Collection Catalogue API"
CANDIDATES = DATA / "image_rights_repair_candidates_v1.csv"
OUTPUT_ROWS = DATA / "wellcome_rights_repair_preflight_v1.csv"
OUTPUT_SUMMARY = DATA / "wellcome_rights_repair_summary_v1.csv"
OUTPUT_REPORT = DOCS / "WELLCOME_RIGHTS_REPAIR_PREFLIGHT_v1.md"

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
    "local_license_signal",
    "rights_signal",
    "future_action",
    "upgrade_recommendation",
    "automatic_upgrade_allowed",
    "iiif_or_viewer_available",
    "image_url_detected_excerpt",
    "rights_text_excerpt",
    "rights_basis_excerpt",
    "review_note_excerpt",
    "citation_basis_excerpt",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]

OPEN_TERMS = [
    "pdm",
    "cc0",
    "public domain",
    "public-domain",
]

BLOCKING_TERMS = [
    "cc-by-nc",
    "by-nc",
    "non-commercial",
    "noncommercial",
    "in copyright",
    "copyrighted",
    "restricted",
    "permission required",
]

IMAGE_STATE_SCORE = {
    "IMG03": 4,
    "IMG02": 3,
    "IMG01": 2,
    "IMG00": 1,
    "IMG04": 0,
}


def norm_url(value: str) -> str:
    return normalize_url(value)


def excerpt(value: str, limit: int = 220) -> str:
    value = re.sub(r"\s+", " ", clean(value))
    if len(value) <= limit:
        return value
    return value[: limit - 1].rsplit(" ", 1)[0] + "..."


def legal_blob(row: dict[str, str]) -> str:
    return " ".join(
        [
            row.get("source_rights_text", ""),
            row.get("rights_uri", ""),
            row.get("rights_basis", ""),
            row.get("image_presence_basis", ""),
            row.get("image_state_evaluation", ""),
            row.get("image_state_review_note", ""),
            row.get("source_notes", ""),
            row.get("citation_basis", ""),
        ]
    )


def has_open_signal(row: dict[str, str]) -> bool:
    blob = legal_blob(row).lower()
    if any(term in blob for term in OPEN_TERMS):
        return True
    # Treat CC BY and CC BY-SA as open text, but never allow the prefix to
    # match CC BY-NC or CC BY-NC-ND. Non-commercial/ND rows remain blocked.
    return re.search(r"\bcc[- ]by(?![- ](?:nc|nd))(?:[- ]sa)?\b", blob) is not None


def has_blocking_signal(row: dict[str, str]) -> bool:
    blob = legal_blob(row).lower()
    return any(term in blob for term in BLOCKING_TERMS)


def has_placeholder_signal(row: dict[str, str]) -> bool:
    blob = " ".join(
        [
            row.get("image_url_detected", ""),
            row.get("image_presence_basis", ""),
            row.get("image_state_evaluation", ""),
            row.get("image_state_review_note", ""),
        ]
    ).lower()
    return "placeholder" in blob or "no displayable image" in blob


def record_score(row: dict[str, str]) -> tuple[int, int, int]:
    state = clean(row.get("image_presence_code"))
    return (
        IMAGE_STATE_SCORE.get(state, 0),
        1 if has_open_signal(row) else 0,
        1 if clean(row.get("parser_status")) == "ok" else 0,
    )


def records_by_url() -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    for path in capture_record_files():
        for row in read_csv(path):
            if row.get("source_name") != SOURCE_NAME:
                continue
            url = norm_url(row.get("source_record_url", ""))
            if not url:
                continue
            candidate = dict(row)
            candidate["_record_file"] = str(path.relative_to(ROOT))
            existing = records.get(url)
            if existing is None or record_score(candidate) > record_score(existing):
                records[url] = candidate
    return records


def license_signal(row: dict[str, str] | None) -> str:
    if not row:
        return "missing"
    open_flag = has_open_signal(row)
    block_flag = has_blocking_signal(row)
    if open_flag and block_flag:
        return "mixed_open_and_blocking_terms"
    if block_flag:
        return "blocking_or_noncommercial_terms"
    if open_flag:
        return "local_open_license_text"
    return "no_open_license_text"


def signal_from_record(row: dict[str, str] | None) -> tuple[str, str, str]:
    if not row:
        return "local_record_missing", "network_verify_item_record_before_any_change", "no_upgrade"

    state = clean(row.get("image_presence_code")) or "IMG00"
    open_flag = has_open_signal(row)
    block_flag = has_blocking_signal(row)
    placeholder_flag = has_placeholder_signal(row)
    viewer = clean(row.get("iiif_or_viewer_available"))
    image_url = clean(row.get("image_url_detected"))

    if state == "IMG00" or placeholder_flag:
        return "placeholder_or_no_displayable_image_blocker", "repair_source_visible_before_rights_upgrade", "source_visible_repair_needed"
    if open_flag and block_flag:
        return "mixed_rights_signal_manual_review", "manual_item_license_check_required", "review_only_no_automatic_upgrade"
    if state == "IMG03" or open_flag:
        return "local_open_license_signal_needs_alignment_review", "compare_public_payload_and_rebuild_alignment", "review_rebuild_alignment_no_automatic_upgrade"
    if block_flag:
        return "blocked_by_noncommercial_or_restriction_signal", "keep_img02_or_manual_rights_review", "no_upgrade"
    if state == "IMG02" and viewer:
        return "source_hosted_viewer_no_open_license_signal", "keep_img02_pending_item_license_evidence", "no_upgrade"
    if state == "IMG01" and image_url:
        return "thumbnail_only_no_open_license_signal", "keep_img01_pending_item_license_evidence", "no_upgrade"
    return "no_item_level_open_rights_evidence", "keep_pending_item_rights_evidence", "no_upgrade"


def build_rows() -> list[dict[str, str]]:
    records = records_by_url()
    rows = []
    for candidate in read_csv(CANDIDATES):
        if candidate.get("source_name") != SOURCE_NAME:
            continue
        record = records.get(norm_url(candidate.get("source_url", "")))
        signal, action, recommendation = signal_from_record(record)
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
                "local_license_signal": license_signal(record),
                "rights_signal": signal,
                "future_action": action,
                "upgrade_recommendation": recommendation,
                "automatic_upgrade_allowed": "false",
                "iiif_or_viewer_available": clean(record.get("iiif_or_viewer_available")) if record else "",
                "image_url_detected_excerpt": excerpt(record.get("image_url_detected", "")) if record else "",
                "rights_text_excerpt": excerpt(record.get("source_rights_text", "")) if record else "",
                "rights_basis_excerpt": excerpt(record.get("rights_basis", "")) if record else "",
                "review_note_excerpt": excerpt(record.get("image_state_review_note", "")) if record else "",
                "citation_basis_excerpt": excerpt(record.get("citation_basis", "")) if record else "",
            }
        )
    rows.sort(key=lambda row: (row["upgrade_recommendation"], row["rights_signal"], row["title"], row["surface_id"]))
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
    signals = Counter(row["rights_signal"] for row in rows)
    recommendations = Counter(row["upgrade_recommendation"] for row in rows)
    states = Counter(row["local_image_state"] or "missing" for row in rows)
    license_signals = Counter(row["local_license_signal"] for row in rows)
    found = Counter(row["local_record_found"] for row in rows)
    summary_rows = [
        {"metric": "wellcome_candidate_rows", "value": str(len(rows)), "notes": "Wellcome rows from image_rights_repair_candidates_v1."},
        {"metric": "local_records_found", "value": str(found.get("true", 0)), "notes": "Rows matched to existing local capture records."},
        {"metric": "automatic_upgrade_allowed_rows", "value": "0", "notes": "No automatic IMG03 upgrades are permitted by this preflight."},
        {"metric": "candidate_weighted_gap_points", "value": f"{weighted_points(rows):.2f}", "notes": "Weighted-publication gap points represented by these candidates."},
    ]
    for key, value in states.most_common():
        summary_rows.append({"metric": f"local_image_state_{key}", "value": str(value), "notes": "Best matching local capture state."})
    for key, value in license_signals.most_common():
        summary_rows.append({"metric": f"local_license_signal_{key}", "value": str(value), "notes": "Conservative local license text signal."})
    for key, value in signals.most_common():
        summary_rows.append({"metric": f"rights_signal_{key}", "value": str(value), "notes": "Conservative local metadata signal."})
    for key, value in recommendations.most_common():
        summary_rows.append(
            {
                "metric": f"upgrade_recommendation_{key}",
                "value": str(value),
                "notes": f"{weighted_points(rows, key):.2f} weighted points.",
            }
        )
    write_csv(OUTPUT_SUMMARY, summary_rows, SUMMARY_FIELDS)

    lines = [
        "# Wellcome Rights Repair Preflight v1",
        "",
        "This local preflight checks Wellcome IMG repair candidates against already captured item metadata. It does not call Wellcome APIs, fetch item pages, download images, mutate surfaces, or upgrade IMG01/IMG03.",
        "",
        "## Result",
        "",
        f"- Wellcome candidate rows: {len(rows)}",
        f"- local records found: {found.get('true', 0)}",
        "- automatic upgrades allowed: 0",
        f"- candidate weighted gap points: {weighted_points(rows):.2f}",
        "",
        "## Local Image States",
        "",
    ]
    for key, value in states.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## License Signals", ""])
    for key, value in license_signals.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Rights Signals", ""])
    for key, value in signals.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Upgrade Recommendations", ""])
    for key, value in recommendations.most_common():
        lines.append(f"- {key}: {value} ({weighted_points(rows, key):.2f} weighted points)")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Wellcome does not provide quick verified-open gain under this local-only preflight. Most rows are source-hosted IIIF/viewer records without open-license text.",
            "- Two legacy local IMG03 rows carry non-commercial license text and placeholder image URLs; they should be treated as repair/downgrade risks, not as verified-open evidence.",
            "- IMG02 rows with IIIF/viewer availability remain source-visible but not verified-open until item-level license evidence is captured.",
            "- IMG00/placeholder rows should be repaired as source-visible records before any rights upgrade is considered.",
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
    print(f"wellcome_candidate_rows={len(rows)}")
    print(f"wrote {OUTPUT_ROWS.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
