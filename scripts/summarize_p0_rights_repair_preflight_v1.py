#!/usr/bin/env python3
"""Summarize P0 image-rights repair preflight outcomes.

The rollup combines the seven P0 source-family preflights and keeps the result
advisory only. It does not mutate records or upgrade image states.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from lib.archive_audit import DATA, DOCS, ROOT, clean, read_csv, write_csv


CANDIDATES = DATA / "image_rights_repair_candidates_v1.csv"
OUTPUT_ROLLUP = DATA / "p0_rights_repair_preflight_rollup_v1.csv"
OUTPUT_RECOMMENDATIONS = DATA / "p0_rights_repair_preflight_recommendations_v1.csv"
OUTPUT_REPORT = DOCS / "P0_RIGHTS_REPAIR_PREFLIGHT_ROLLUP_v1.md"

P0_PREFLIGHTS = [
    ("Cooper Hewitt Collection GraphQL API", DATA / "cooperhewitt_rights_repair_preflight_v1.csv"),
    ("Wellcome Collection Catalogue API", DATA / "wellcome_rights_repair_preflight_v1.csv"),
    ("Library of Congress loc.gov API", DATA / "loc_rights_repair_preflight_v1.csv"),
    ("Georgia State University Library Digital Collections / CONTENTdm", DATA / "gsu_rights_repair_preflight_v1.csv"),
    ("Art Institute of Chicago API", DATA / "aic_rights_repair_preflight_v1.csv"),
    ("Internet Archive / text and periodical collections", DATA / "internet_archive_rights_repair_preflight_v1.csv"),
    ("V&A Collections API", DATA / "vam_rights_repair_preflight_v1.csv"),
]

ROLLUP_FIELDS = [
    "source_name",
    "candidate_rows",
    "weighted_gap_points",
    "automatic_upgrade_allowed_rows",
    "no_upgrade_rows",
    "no_upgrade_points",
    "source_visible_repair_needed_rows",
    "source_visible_repair_needed_points",
    "item_rights_capture_required_rows",
    "item_rights_capture_required_points",
    "review_rebuild_alignment_no_automatic_upgrade_rows",
    "review_rebuild_alignment_no_automatic_upgrade_points",
    "review_only_no_automatic_upgrade_rows",
    "review_only_no_automatic_upgrade_points",
    "other_review_rows",
    "other_review_points",
    "primary_interpretation",
]

RECOMMENDATION_FIELDS = [
    "source_name",
    "upgrade_recommendation",
    "rows",
    "weighted_gap_points",
    "automatic_upgrade_allowed_rows",
]

INTERPRETATIONS = {
    "Cooper Hewitt Collection GraphQL API": "Not a quick verified-open repair family; mostly copyright/restriction or credit-only local metadata.",
    "Wellcome Collection Catalogue API": "Not a quick verified-open repair family; includes legacy CC-BY-NC/ND placeholder risks.",
    "Library of Congress loc.gov API": "Best P0 deep-probe target; missing item image/rights capture is the main blocker.",
    "Georgia State University Library Digital Collections / CONTENTdm": "Mostly blocked by raw copyright/permission rights; one CC0 row needs manual rebuild review.",
    "Art Institute of Chicago API": "No current repair gain; raw search data mostly says is_public_domain=false.",
    "Internet Archive / text and periodical collections": "Reading/source support source; current repair queue lacks explicit open item licenses.",
    "V&A Collections API": "Useful for source-visible triage; object metadata does not provide bulk verified-open evidence.",
}


def candidate_weights() -> dict[tuple[str, str], float]:
    weights: dict[tuple[str, str], float] = {}
    for row in read_csv(CANDIDATES):
        source = row.get("source_name", "")
        surface_id = row.get("surface_id", "")
        try:
            weight = float(row.get("weighted_gap_points") or 0)
        except ValueError:
            weight = 0.0
        if source and surface_id:
            weights[(source, surface_id)] = weight
    return weights


def row_weight(row: dict[str, str], source_name: str, weights: dict[tuple[str, str], float]) -> float:
    try:
        return float(row.get("weighted_gap_points") or "")
    except ValueError:
        return weights.get((source_name, row.get("surface_id", "")), 0.0)


def format_points(value: float) -> str:
    return f"{value:.2f}"


def build() -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, str]]:
    weights = candidate_weights()
    rollup_rows: list[dict[str, str]] = []
    recommendation_rows: list[dict[str, str]] = []
    totals = Counter()

    for source_name, path in P0_PREFLIGHTS:
        rows = read_csv(path)
        recommendation_counts: Counter[str] = Counter()
        recommendation_points: defaultdict[str, float] = defaultdict(float)
        recommendation_auto: Counter[str] = Counter()
        total_points = 0.0
        auto_rows = 0
        for row in rows:
            recommendation = clean(row.get("upgrade_recommendation")) or "unspecified"
            weight = row_weight(row, source_name, weights)
            total_points += weight
            recommendation_counts[recommendation] += 1
            recommendation_points[recommendation] += weight
            if clean(row.get("automatic_upgrade_allowed")).lower() == "true":
                auto_rows += 1
                recommendation_auto[recommendation] += 1

        for recommendation, count in recommendation_counts.most_common():
            recommendation_rows.append(
                {
                    "source_name": source_name,
                    "upgrade_recommendation": recommendation,
                    "rows": str(count),
                    "weighted_gap_points": format_points(recommendation_points[recommendation]),
                    "automatic_upgrade_allowed_rows": str(recommendation_auto.get(recommendation, 0)),
                }
            )

        known = {
            "no_upgrade",
            "source_visible_repair_needed",
            "item_rights_capture_required",
            "review_rebuild_alignment_no_automatic_upgrade",
            "review_only_no_automatic_upgrade",
        }
        other_rows = sum(count for rec, count in recommendation_counts.items() if rec not in known)
        other_points = sum(points for rec, points in recommendation_points.items() if rec not in known)
        rollup_rows.append(
            {
                "source_name": source_name,
                "candidate_rows": str(len(rows)),
                "weighted_gap_points": format_points(total_points),
                "automatic_upgrade_allowed_rows": str(auto_rows),
                "no_upgrade_rows": str(recommendation_counts.get("no_upgrade", 0)),
                "no_upgrade_points": format_points(recommendation_points.get("no_upgrade", 0.0)),
                "source_visible_repair_needed_rows": str(recommendation_counts.get("source_visible_repair_needed", 0)),
                "source_visible_repair_needed_points": format_points(recommendation_points.get("source_visible_repair_needed", 0.0)),
                "item_rights_capture_required_rows": str(recommendation_counts.get("item_rights_capture_required", 0)),
                "item_rights_capture_required_points": format_points(recommendation_points.get("item_rights_capture_required", 0.0)),
                "review_rebuild_alignment_no_automatic_upgrade_rows": str(recommendation_counts.get("review_rebuild_alignment_no_automatic_upgrade", 0)),
                "review_rebuild_alignment_no_automatic_upgrade_points": format_points(recommendation_points.get("review_rebuild_alignment_no_automatic_upgrade", 0.0)),
                "review_only_no_automatic_upgrade_rows": str(recommendation_counts.get("review_only_no_automatic_upgrade", 0)),
                "review_only_no_automatic_upgrade_points": format_points(recommendation_points.get("review_only_no_automatic_upgrade", 0.0)),
                "other_review_rows": str(other_rows),
                "other_review_points": format_points(other_points),
                "primary_interpretation": INTERPRETATIONS[source_name],
            }
        )
        totals["candidate_rows"] += len(rows)
        totals["automatic_upgrade_allowed_rows"] += auto_rows
        totals["weighted_gap_points_x100"] += round(total_points * 100)

    summary = {
        "candidate_rows": str(totals["candidate_rows"]),
        "weighted_gap_points": format_points(totals["weighted_gap_points_x100"] / 100),
        "automatic_upgrade_allowed_rows": str(totals["automatic_upgrade_allowed_rows"]),
    }
    return rollup_rows, recommendation_rows, summary


def write_report(rollup_rows: list[dict[str, str]], recommendation_rows: list[dict[str, str]], summary: dict[str, str]) -> None:
    recommendation_totals: defaultdict[str, float] = defaultdict(float)
    recommendation_counts: Counter[str] = Counter()
    for row in recommendation_rows:
        recommendation = row["upgrade_recommendation"]
        recommendation_counts[recommendation] += int(row["rows"])
        recommendation_totals[recommendation] += float(row["weighted_gap_points"])

    lines = [
        "# P0 Rights Repair Preflight Rollup v1",
        "",
        "This rollup combines the seven P0 image-rights repair preflights. It is advisory only and does not mutate records or upgrade IMG01/IMG03.",
        "",
        "## P0 Totals",
        "",
        f"- source families: {len(P0_PREFLIGHTS)}",
        f"- candidate rows: {summary['candidate_rows']}",
        f"- weighted gap points represented: {summary['weighted_gap_points']}",
        f"- automatic upgrades allowed: {summary['automatic_upgrade_allowed_rows']}",
        "",
        "## Recommendation Totals",
        "",
    ]
    for recommendation, count in recommendation_counts.most_common():
        lines.append(f"- {recommendation}: {count} rows / {recommendation_totals[recommendation]:.2f} weighted points")
    lines.extend(["", "## Source Summary", ""])
    for row in rollup_rows:
        lines.append(
            "- "
            f"{row['source_name']}: {row['candidate_rows']} rows / {row['weighted_gap_points']} pts; "
            f"auto={row['automatic_upgrade_allowed_rows']}; "
            f"{row['primary_interpretation']}"
        )
    lines.extend(
        [
            "",
            "## Next Actions",
            "",
            "- Treat the P0 preflight as a negative rights-upgrade result: source-family reputation and source-hosted images are not enough to move IMG01/IMG03.",
            "- Run a targeted LOC deep item/image-rights probe first because it has the clearest missing-evidence repair path.",
            "- Patch GSU capture logic so local rights statements and image-display basis are preserved separately before any future GSU rebuild.",
            "- Keep Wellcome, AIC, Internet Archive, V&A, and Cooper Hewitt as source-visible/context sources unless explicit item-level open evidence is captured.",
            "- Shift the next 5,000-source capture tranche toward sources with explicit public-domain/open-license item fields and lower region coverage, instead of trying to mine verified-open gains from these P0 families.",
            "",
            "## Output Files",
            "",
            f"- `{OUTPUT_ROLLUP.relative_to(ROOT)}`",
            f"- `{OUTPUT_RECOMMENDATIONS.relative_to(ROOT)}`",
        ]
    )
    OUTPUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rollup_rows, recommendation_rows, summary = build()
    write_csv(OUTPUT_ROLLUP, rollup_rows, ROLLUP_FIELDS)
    write_csv(OUTPUT_RECOMMENDATIONS, recommendation_rows, RECOMMENDATION_FIELDS)
    write_report(rollup_rows, recommendation_rows, summary)
    print(f"p0_candidate_rows={summary['candidate_rows']}")
    print(f"p0_weighted_gap_points={summary['weighted_gap_points']}")
    print(f"p0_automatic_upgrade_allowed_rows={summary['automatic_upgrade_allowed_rows']}")
    print(f"wrote {OUTPUT_ROLLUP.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_RECOMMENDATIONS.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
