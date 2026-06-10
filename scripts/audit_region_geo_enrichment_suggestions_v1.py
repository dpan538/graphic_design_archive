#!/usr/bin/env python3
"""Summarize region/geography enrichment suggestion outputs."""

from __future__ import annotations

from collections import Counter

from lib.archive_audit import DATA, DOCS, ROOT, clean, read_csv, write_csv


DIRECT = DATA / "region_conflict_direct_parse_v1.csv"
HISTORICAL = DATA / "region_conflict_historical_split_suggestions_v1.csv"
PENDING = DATA / "region_pending_geo_text_suggestions_v1.csv"
CANDIDATES = DATA / "region_geography_normalization_candidates_v1.csv"

SUMMARY = DATA / "region_geo_enrichment_audit_summary_v1.csv"
REPORT = DOCS / "REGION_GEO_ENRICHMENT_AUDIT_v1.md"

FIELDS = ["metric", "value", "notes"]


def ids(rows: list[dict[str, str]]) -> set[str]:
    return {clean(row.get("surface_id")) for row in rows if clean(row.get("surface_id"))}


def main() -> None:
    direct = read_csv(DIRECT)
    historical = read_csv(HISTORICAL)
    pending = read_csv(PENDING)
    candidates = read_csv(CANDIDATES)

    resolved_like = ids(direct) | ids(historical) | ids(pending)
    conflict_total = sum(1 for row in candidates if row.get("candidate_status") == "geography_conflict_review")
    pending_total = sum(1 for row in candidates if row.get("candidate_action") == "keep_pending")
    low_signal_total = sum(1 for row in candidates if row.get("candidate_action") == "review_low_signal_geo_candidates")

    summary_rows = [
        {"metric": "direct_conflict_parse_suggestions", "value": str(len(direct)), "notes": "Controlled-geography matches from high-signal conflict evidence."},
        {"metric": "historical_split_suggestions", "value": str(len(historical)), "notes": "Date/term based historical split suggestions for conflict rows."},
        {"metric": "pending_text_suggestions", "value": str(len(pending)), "notes": "Rule-based suggestions from pending or low-signal rows."},
        {"metric": "unique_surfaces_with_enrichment_suggestions", "value": str(len(resolved_like)), "notes": "Unique surface IDs suggested by any local enrichment pass."},
        {"metric": "original_conflict_review_rows", "value": str(conflict_total), "notes": "Rows in candidate table with geography_conflict_review."},
        {"metric": "original_pending_rows", "value": str(pending_total), "notes": "Rows in candidate table with keep_pending."},
        {"metric": "original_low_signal_rows", "value": str(low_signal_total), "notes": "Rows in candidate table with review_low_signal_geo_candidates."},
    ]
    write_csv(SUMMARY, summary_rows, FIELDS)

    direct_labels = Counter(row.get("suggested_label", "") for row in direct)
    pending_labels = Counter(row.get("suggested_label", "") for row in pending)
    lines = [
        "# Region / Geography Enrichment Audit v1",
        "",
        "Scope: local, proposal-only enrichment over region/geography normalization candidates. No source records, public surfaces, controlled taxonomy CSVs, or frontend files are rewritten.",
        "",
        "## Summary",
        "",
    ]
    for row in summary_rows:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")

    lines.extend(["", "## Direct Conflict Parse Targets", ""])
    if direct_labels:
        for label, count in direct_labels.most_common(25):
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- none")

    lines.extend(["", "## Pending / Low-Signal Text Targets", ""])
    if pending_labels:
        for label, count in pending_labels.most_common(25):
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- none")

    lines.extend(["", "## Interpretation", ""])
    lines.append("- The 3,900 pending rows should not be accepted as final; local enrichment can surface additional review candidates without changing archive data.")
    lines.append("- Direct conflict parse suggestions are stronger than low-signal text suggestions because they rely on high-signal candidate evidence.")
    lines.append("- Historical split suggestions should remain review-only until controlled historical geography rows and display rules are confirmed.")
    lines.append("- Pending text suggestions are useful for prioritizing manual review and source-family repairs, not for automatic application.")
    lines.append("- A Wikidata or external lookup pass can be added later, but should use caching, rate limits, and a dry-run-only output contract.")

    lines.extend(["", "## Generated Files", ""])
    for path in [DIRECT, HISTORICAL, PENDING, SUMMARY]:
        lines.append(f"- `data/{path.name}`")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"direct_conflict_parse_suggestions={len(direct)}")
    print(f"historical_split_suggestions={len(historical)}")
    print(f"pending_text_suggestions={len(pending)}")
    print(f"unique_surfaces_with_enrichment_suggestions={len(resolved_like)}")
    print(f"wrote {SUMMARY.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
