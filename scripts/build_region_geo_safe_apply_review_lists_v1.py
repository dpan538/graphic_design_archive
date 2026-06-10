#!/usr/bin/env python3
"""Build safe application and review lists for region/geography enrichment.

The outputs are review artifacts only. They do not apply mappings or rewrite
taxonomy/source/surface files.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from lib.archive_audit import DATA, DOCS, ROOT, clean, read_csv, write_csv


CONFIDENCE = DATA / "region_geo_enrichment_with_confidence_v1.csv"
VALIDATION = DATA / "region_geo_wikidata_validation_v1.csv"

OUTPUT_AUTO = DATA / "region_geo_ready_for_auto_apply_v1.csv"
OUTPUT_MANUAL = DATA / "region_geo_priority_manual_review_v1.csv"
OUTPUT_HISTORICAL = DATA / "region_geo_requires_historical_split_review_v1.csv"
OUTPUT_REPORT = DOCS / "REGION_GEO_SAFE_APPLY_REVIEW_LIST_v1.md"

FIELDS = [
    "suggestion_id",
    "surface_id",
    "source_record_id",
    "suggestion_type",
    "current_label",
    "suggested_label",
    "suggested_region_id",
    "suggested_geo_id",
    "confidence_level",
    "evidence_type",
    "auto_apply_eligible",
    "requires_date_check",
    "external_validation_status",
    "wikidata_country_found",
    "suggested_action",
    "years_found",
    "risk_flags",
    "review_priority",
    "evidence",
    "title",
    "source_file",
]


def validation_index() -> dict[str, dict[str, str]]:
    out = {}
    for row in read_csv(VALIDATION):
        suggestion_id = clean(row.get("suggestion_id"))
        if suggestion_id:
            out[suggestion_id] = row
    return out


def enrich_validation(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    validation = validation_index()
    out = []
    for row in rows:
        next_row = dict(row)
        result = validation.get(clean(row.get("suggestion_id")), {})
        next_row["external_validation_status"] = clean(
            result.get("external_validation_status") or row.get("external_validation_status") or "unchecked"
        )
        next_row["wikidata_country_found"] = clean(result.get("wikidata_country_found"))
        out.append(next_row)
    return out


def priority(row: dict[str, str]) -> str:
    if row.get("external_validation_status") == "confirmed":
        return "P0_external_confirmed_medium"
    if row.get("confidence_level") == "medium" and row.get("requires_date_check") == "true":
        return "P1_date_sensitive_medium"
    if row.get("confidence_level") == "medium":
        return "P1_medium_review"
    if row.get("external_validation_status") == "contradicted":
        return "P2_external_contradiction"
    return "P2_low_signal_review"


def sort_key(row: dict[str, str]) -> tuple[int, str, str, str]:
    rank = {
        "P0_external_confirmed_medium": 0,
        "P1_date_sensitive_medium": 1,
        "P1_medium_review": 2,
        "P2_external_contradiction": 3,
        "P2_low_signal_review": 4,
    }.get(row.get("review_priority"), 9)
    return (rank, row.get("suggested_label", ""), row.get("suggestion_type", ""), row.get("surface_id", ""))


def write_report(rows: list[dict[str, str]], auto: list[dict[str, str]], manual: list[dict[str, str]], historical: list[dict[str, str]]) -> None:
    by_type = Counter(row.get("suggestion_type") for row in rows)
    by_confidence = Counter(row.get("confidence_level") for row in rows)
    by_action = Counter(row.get("suggested_action") for row in rows)
    manual_priority = Counter(row.get("review_priority") for row in manual)
    auto_by_label = Counter(row.get("suggested_label") for row in auto)
    historical_by_label = Counter(row.get("suggested_label") for row in historical)

    type_label_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        type_label_counts[row.get("suggestion_type")][row.get("suggested_label")] += 1

    lines = [
        "# Region/Geography Safe Apply Review List v1",
        "",
        "This audit is proposal-only. It does not modify source records, public surfaces, region labels, or geography labels.",
        "",
        "## Summary",
        "",
        f"- scored suggestions: {len(rows)}",
        f"- ready for auto apply: {len(auto)}",
        f"- priority manual review: {len(manual)}",
        f"- historical split review: {len(historical)}",
        "",
        "## Suggestion Types",
        "",
    ]
    for key, value in by_type.most_common():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Confidence Levels", ""])
    for key, value in by_confidence.most_common():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Suggested Actions", ""])
    for key, value in by_action.most_common():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Manual Review Priority", ""])
    for key, value in manual_priority.most_common():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Auto-Apply Labels", ""])
    if auto_by_label:
        for key, value in auto_by_label.most_common(20):
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- none")

    lines.extend(["", "## Historical Split Labels", ""])
    if historical_by_label:
        for key, value in historical_by_label.most_common(20):
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- none")

    lines.extend(["", "## Top Labels by Suggestion Type", ""])
    for suggestion_type in sorted(type_label_counts):
        lines.append(f"### {suggestion_type}")
        for key, value in type_label_counts[suggestion_type].most_common(12):
            lines.append(f"- {key}: {value}")
        lines.append("")

    lines.extend(
        [
            "## Output Files",
            "",
            f"- `{OUTPUT_AUTO.relative_to(ROOT)}`",
            f"- `{OUTPUT_MANUAL.relative_to(ROOT)}`",
            f"- `{OUTPUT_HISTORICAL.relative_to(ROOT)}`",
            "",
            "## Interpretation",
            "",
            "- `ready_for_auto_apply` is limited to high-confidence direct conflict parses with no historical dispute, no multi-country risk, and no sensitive label risk.",
            "- `priority_manual_review` keeps pending text resurfacing and date-sensitive medium suggestions out of automatic application.",
            "- `requires_historical_split_review` is separated because split labels need taxonomy support before they can be used in public statistics.",
        ]
    )

    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = enrich_validation(read_csv(CONFIDENCE))
    auto = [
        row
        for row in rows
        if row.get("auto_apply_eligible") == "true" and row.get("external_validation_status") != "contradicted"
    ]
    historical = [row for row in rows if row.get("suggestion_type") == "historical_split"]
    manual = [
        row
        for row in rows
        if row.get("auto_apply_eligible") != "true" and row.get("suggestion_type") != "historical_split"
    ]
    for row in manual:
        row["review_priority"] = priority(row)
    for row in auto:
        row["review_priority"] = "auto_apply_ready"
    for row in historical:
        row["review_priority"] = "historical_split_review"

    manual = sorted(manual, key=sort_key)
    auto = sorted(auto, key=lambda row: (row.get("suggested_label", ""), row.get("surface_id", "")))
    historical = sorted(historical, key=lambda row: (row.get("suggested_label", ""), row.get("surface_id", "")))

    write_csv(OUTPUT_AUTO, auto, FIELDS)
    write_csv(OUTPUT_MANUAL, manual, FIELDS)
    write_csv(OUTPUT_HISTORICAL, historical, FIELDS)
    write_report(rows, auto, manual, historical)

    print(f"ready_for_auto_apply={len(auto)}")
    print(f"priority_manual_review={len(manual)}")
    print(f"requires_historical_split_review={len(historical)}")
    print(f"wrote {OUTPUT_AUTO.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_MANUAL.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_HISTORICAL.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
