#!/usr/bin/env python3
"""Audit Internet Archive IMG02 candidates against local license metadata.

This preflight reads already captured CSV metadata only. It does not call
archive.org, download files/images, mutate records, or upgrade IMG01/IMG03.
"""

from __future__ import annotations

import re
from collections import Counter

from lib.archive_audit import DATA, DOCS, ROOT, capture_record_files, clean, normalize_url, read_csv, write_csv


SOURCE_NAME = "Internet Archive / text and periodical collections"
CANDIDATES = DATA / "image_rights_repair_candidates_v1.csv"
OUTPUT_ROWS = DATA / "internet_archive_rights_repair_preflight_v1.csv"
OUTPUT_SUMMARY = DATA / "internet_archive_rights_repair_summary_v1.csv"
OUTPUT_REPORT = DOCS / "INTERNET_ARCHIVE_RIGHTS_REPAIR_PREFLIGHT_v1.md"

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
    "license_url_detected",
    "license_signal",
    "rights_signal",
    "future_action",
    "upgrade_recommendation",
    "automatic_upgrade_allowed",
    "image_url_detected_excerpt",
    "rights_basis_excerpt",
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


def license_url_from_record(row: dict[str, str] | None) -> str:
    if not row:
        return ""
    blob = " ".join([row.get("source_notes", ""), row.get("source_rights_text", ""), row.get("rights_basis", "")])
    match = re.search(r"https?://[^\s,;]+", blob)
    return match.group(0).rstrip(".") if match else ""


def license_signal(license_url: str) -> str:
    url = license_url.lower()
    if not url:
        return "no_explicit_license_url"
    if "publicdomain" in url or "publicdomain/zero" in url or "cc0" in url:
        return "explicit_public_domain_or_cc0_url"
    if "creativecommons.org/licenses/by-nc" in url or "creativecommons.org/licenses/by-nd" in url:
        return "blocking_noncommercial_or_noderivatives_url"
    if re.search(r"creativecommons\.org/licenses/by(?:/|/4\.0|/3\.0)", url):
        return "explicit_cc_by_url"
    return "unclassified_license_url"


def signal_from_record(row: dict[str, str] | None) -> tuple[str, str, str, str, str]:
    if not row:
        return "local_record_missing", "archive_item_metadata_probe_required", "no_upgrade", "", "missing"
    url = license_url_from_record(row)
    signal = license_signal(url)
    if signal in {"explicit_public_domain_or_cc0_url", "explicit_cc_by_url"}:
        return (
            "explicit_open_license_url_needs_item_review",
            "rebuild_record_with_explicit_license_after_manual_check",
            "review_rebuild_alignment_no_automatic_upgrade",
            url,
            signal,
        )
    if signal == "blocking_noncommercial_or_noderivatives_url":
        return (
            "blocked_by_noncommercial_or_noderivatives_license",
            "keep_img02_pending_different_open_source",
            "no_upgrade",
            url,
            signal,
        )
    if signal == "unclassified_license_url":
        return (
            "license_url_present_but_unclassified",
            "manual_archive_license_review_required",
            "no_upgrade",
            url,
            signal,
        )
    return (
        "no_explicit_item_license_url",
        "archive_item_license_probe_required",
        "no_upgrade",
        url,
        signal,
    )


def build_rows() -> list[dict[str, str]]:
    records = records_by_url()
    rows = []
    for candidate in read_csv(CANDIDATES):
        if candidate.get("source_name") != SOURCE_NAME:
            continue
        record = records.get(normalize_url(candidate.get("source_url", "")))
        signal, action, recommendation, license_url, lic_signal = signal_from_record(record)
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
                "license_url_detected": license_url,
                "license_signal": lic_signal,
                "rights_signal": signal,
                "future_action": action,
                "upgrade_recommendation": recommendation,
                "automatic_upgrade_allowed": "false",
                "image_url_detected_excerpt": excerpt(record.get("image_url_detected", "")) if record else "",
                "rights_basis_excerpt": excerpt(record.get("rights_basis", "")) if record else "",
                "source_notes_excerpt": excerpt(record.get("source_notes", "")) if record else "",
            }
        )
    rows.sort(key=lambda row: (row["upgrade_recommendation"], row["license_signal"], row["title"], row["surface_id"]))
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
    license_signals = Counter(row["license_signal"] for row in rows)
    rights_signals = Counter(row["rights_signal"] for row in rows)
    recommendations = Counter(row["upgrade_recommendation"] for row in rows)
    found = Counter(row["local_record_found"] for row in rows)

    summary_rows = [
        {"metric": "internet_archive_candidate_rows", "value": str(len(rows)), "notes": "Internet Archive rows from image_rights_repair_candidates_v1."},
        {"metric": "local_records_found", "value": str(found.get("true", 0)), "notes": "Rows matched to existing local capture records."},
        {"metric": "automatic_upgrade_allowed_rows", "value": "0", "notes": "No automatic IMG03 upgrades are permitted by this preflight."},
        {"metric": "candidate_weighted_gap_points", "value": f"{weighted_points(rows):.2f}", "notes": "Weighted-publication gap points represented by these candidates."},
    ]
    for key, value in states.most_common():
        summary_rows.append({"metric": f"local_image_state_{key}", "value": str(value), "notes": "Best matching local capture state."})
    for key, value in license_signals.most_common():
        summary_rows.append({"metric": f"license_signal_{key}", "value": str(value), "notes": "Local license URL signal."})
    for key, value in rights_signals.most_common():
        summary_rows.append({"metric": f"rights_signal_{key}", "value": str(value), "notes": "Conservative rights-repair signal."})
    for key, value in recommendations.most_common():
        summary_rows.append({"metric": f"upgrade_recommendation_{key}", "value": str(value), "notes": f"{weighted_points(rows, key):.2f} weighted points."})
    write_csv(OUTPUT_SUMMARY, summary_rows, SUMMARY_FIELDS)

    lines = [
        "# Internet Archive Rights Repair Preflight v1",
        "",
        "This local preflight checks Internet Archive IMG02 candidates against already captured CSV metadata. It does not call archive.org, download files/images, mutate records, or upgrade IMG01/IMG03.",
        "",
        "## Result",
        "",
        f"- Internet Archive candidate rows: {len(rows)}",
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
            "- Internet Archive remains useful for reading/source support, but most candidates lack explicit item-level open-license URLs in local metadata.",
            "- One candidate has a non-commercial/no-derivatives Creative Commons URL and is explicitly not an open publication-grade repair.",
            "- Any IA upgrade must preserve explicit item license evidence; IA thumbnails or scans alone are source-visible context, not reusable image evidence.",
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
    print(f"internet_archive_candidate_rows={len(rows)}")
    print(f"wrote {OUTPUT_ROWS.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
