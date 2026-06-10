#!/usr/bin/env python3
"""Generate region/geography normalization decisions from audit + research.

This is a read-only reconciliation pass. It compares the project-controlled
region/geography tables with the public taxonomy gap audit, then turns the
Region and Geography Normalization research packet into implementation
decisions. It does not rewrite records, surfaces, regions, or geographies.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from lib.archive_audit import DATA, DOCS, ROOT, clean, read_csv, write_csv


DECISIONS = DATA / "region_geography_normalization_decisions_v1.csv"
REPORT = DOCS / "REGION_GEOGRAPHY_NORMALIZATION_DECISIONS_v1.md"

FIELDS = [
    "decision_id",
    "source_label",
    "source_label_kind",
    "surface_count",
    "source_count",
    "periods",
    "current_gap_status",
    "recommended_preferred_label",
    "decision_class",
    "proposed_action",
    "target_region_ids",
    "target_geo_ids",
    "missing_geo_recommendation",
    "confidence",
    "evidence_needed",
    "public_display_rule",
    "implementation_guardrail",
    "source_basis",
]


RESEARCH_DECISIONS: dict[str, dict[str, str]] = {
    "Unresolved region": {
        "recommended_preferred_label": "Pending geographic normalization",
        "decision_class": "internal_qa_state",
        "proposed_action": "keep_pending_then_batch_resolve",
        "target_region_ids": "",
        "target_geo_ids": "",
        "missing_geo_recommendation": "",
        "confidence": "high",
        "evidence_needed": "record-level placeText, sourceSubjects, title, description, source notes, sourceUrl, and sourceName evidence",
        "public_display_rule": "hide from public browse; show as pending only on detail/internal QA surfaces",
        "implementation_guardrail": "Never treat Unresolved region as a geography or release coverage signal.",
    },
    "Latin America": {
        "recommended_preferred_label": "Latin America",
        "decision_class": "mapping_gap_or_display_alias",
        "proposed_action": "map_to_REG004_and_review_exact_child_need",
        "target_region_ids": "REG004",
        "target_geo_ids": "GEO028",
        "missing_geo_recommendation": "Add an exact Latin America display/alias geography only if records explicitly exclude the Caribbean.",
        "confidence": "medium",
        "evidence_needed": "verify whether each source scope means Latin America only or Latin America and the Caribbean",
        "public_display_rule": "display Latin America when source says Latin America; roll up to REG004 for browse",
        "implementation_guardrail": "Do not silently claim Caribbean coverage from Latin America-only evidence.",
    },
    "France": {
        "recommended_preferred_label": "France",
        "decision_class": "auto_country_mapping",
        "proposed_action": "auto_map",
        "target_region_ids": "REG001",
        "target_geo_ids": "GEO005",
        "missing_geo_recommendation": "",
        "confidence": "high",
        "evidence_needed": "exact controlled geography already exists",
        "public_display_rule": "display France; parent region optional in browse tree",
        "implementation_guardrail": "Do not inflate source coverage by counting parent macro-region as a separate source.",
    },
    "United States": {
        "recommended_preferred_label": "United States",
        "decision_class": "auto_country_mapping",
        "proposed_action": "auto_map",
        "target_region_ids": "REG003",
        "target_geo_ids": "GEO025",
        "missing_geo_recommendation": "",
        "confidence": "high",
        "evidence_needed": "exact controlled geography already exists",
        "public_display_rule": "display United States; city/state can appear as child detail when known",
        "implementation_guardrail": "Do not collapse Indigenous North America or transborder records into U.S. only.",
    },
    "Brazil": {
        "recommended_preferred_label": "Brazil",
        "decision_class": "auto_country_mapping",
        "proposed_action": "auto_map",
        "target_region_ids": "REG004",
        "target_geo_ids": "GEO030",
        "missing_geo_recommendation": "",
        "confidence": "high",
        "evidence_needed": "exact controlled geography already exists",
        "public_display_rule": "display Brazil",
        "implementation_guardrail": "Keep country mapping separate from broad Latin America source coverage.",
    },
    "Mexico": {
        "recommended_preferred_label": "Mexico",
        "decision_class": "auto_country_mapping",
        "proposed_action": "auto_map",
        "target_region_ids": "REG004",
        "target_geo_ids": "GEO027",
        "missing_geo_recommendation": "",
        "confidence": "high",
        "evidence_needed": "exact controlled geography already exists",
        "public_display_rule": "display Mexico; roll up to Latin America and the Caribbean in this archive",
        "implementation_guardrail": "Do not remap Mexico to REG003 merely because GEO027 is parented under North America.",
    },
    "India": {
        "recommended_preferred_label": "India",
        "decision_class": "auto_country_mapping",
        "proposed_action": "auto_map",
        "target_region_ids": "REG012",
        "target_geo_ids": "GEO051",
        "missing_geo_recommendation": "",
        "confidence": "high",
        "evidence_needed": "exact controlled geography already exists",
        "public_display_rule": "display India",
        "implementation_guardrail": "Keep multilingual/script evidence visible where source records provide it.",
    },
    "China / Hong Kong": {
        "recommended_preferred_label": "Mainland China; Hong Kong",
        "decision_class": "structural_split",
        "proposed_action": "split_by_record_evidence",
        "target_region_ids": "REG008; REG009",
        "target_geo_ids": "GEO040; GEO041",
        "missing_geo_recommendation": "",
        "confidence": "high",
        "evidence_needed": "determine whether each record is Mainland China, Hong Kong, or cross-border/bilingual circulation",
        "public_display_rule": "never show slash label; use separate chips or separate values",
        "implementation_guardrail": "Do not normalize Hong Kong records into Mainland China.",
    },
    "Australia / Indigenous": {
        "recommended_preferred_label": "Australia; Aboriginal Australia; Torres Strait Islander Australia",
        "decision_class": "sensitive_structural_split",
        "proposed_action": "split_with_protocol_review",
        "target_region_ids": "REG015",
        "target_geo_ids": "GEO069; GEO104; GEO105",
        "missing_geo_recommendation": "Add specific Nation/Country/community records only when the source evidence supports preferred naming.",
        "confidence": "high",
        "evidence_needed": "identify source-stated Indigenous community, Nation, Country, language group, or protocol note where possible",
        "public_display_rule": "display Australia plus Indigenous context or specific Nation/Country; never reduce Indigenous context to country only",
        "implementation_guardrail": "Use broad Indigenous Australia only as a temporary protocol-aware umbrella.",
    },
    "South Africa / Botswana": {
        "recommended_preferred_label": "South Africa; Botswana; Southern Africa",
        "decision_class": "structural_split_with_missing_geo",
        "proposed_action": "split_and_add_country_if_needed",
        "target_region_ids": "REG014",
        "target_geo_ids": "GEO062; GEO102",
        "missing_geo_recommendation": "Add Botswana as a country_context when record-level evidence is specifically Botswana.",
        "confidence": "high",
        "evidence_needed": "determine whether each record is South Africa, Botswana, bilateral, or regional southern African solidarity context",
        "public_display_rule": "display both countries for bilateral records; display Southern Africa only for region-wide records",
        "implementation_guardrail": "Do not leave bilateral records as a slash label.",
    },
    "Palestine / transnational": {
        "recommended_preferred_label": "Mandatory Palestine; Palestinian territories and diaspora; transnational context",
        "decision_class": "sensitive_historical_split",
        "proposed_action": "split_with_historical_review",
        "target_region_ids": "REG013",
        "target_geo_ids": "GEO084; GEO085; GEO001",
        "missing_geo_recommendation": "",
        "confidence": "medium",
        "evidence_needed": "distinguish historical Palestine, present-day Palestinian context, diaspora, and solidarity/transnational circulation",
        "public_display_rule": "use separate place and transnational/context badges",
        "implementation_guardrail": "Do not collapse all Palestine-related records into one modern-state label.",
    },
    "Cuba / transnational": {
        "recommended_preferred_label": "Cuba; transnational context",
        "decision_class": "structural_split",
        "proposed_action": "split_place_and_context",
        "target_region_ids": "REG004",
        "target_geo_ids": "GEO029; GEO001",
        "missing_geo_recommendation": "",
        "confidence": "medium",
        "evidence_needed": "distinguish island-based production from exile, diaspora, solidarity, or international circulation",
        "public_display_rule": "display Cuba and add transnational badge only when source evidence supports it",
        "implementation_guardrail": "Do not fuse place and circulation context into one geography.",
    },
    "Russia": {
        "recommended_preferred_label": "Russia or Russia / USSR contexts",
        "decision_class": "historical_period_review",
        "proposed_action": "route_by_date_and_territorial_scope",
        "target_region_ids": "REG002",
        "target_geo_ids": "GEO016",
        "missing_geo_recommendation": "Consider a modern Russia country_context split from GEO016 if enough post-1991 records accumulate.",
        "confidence": "medium",
        "evidence_needed": "review period, republic/territory scope, source institution, and Soviet vs Russian wording",
        "public_display_rule": "display Russia only when actually Russia; use USSR/Soviet context when multi-republic Soviet scope is explicit",
        "implementation_guardrail": "Do not nationalize Soviet material into Russia by default.",
    },
    "Uruguay": {
        "recommended_preferred_label": "Uruguay",
        "decision_class": "controlled_geo_missing",
        "proposed_action": "add_country_geography_then_map",
        "target_region_ids": "REG004",
        "target_geo_ids": "",
        "missing_geo_recommendation": "Add Uruguay as a country_context under GEO028 / REG004.",
        "confidence": "high",
        "evidence_needed": "country-level label is already explicit in public folder",
        "public_display_rule": "display Uruguay",
        "implementation_guardrail": "Add as controlled geography before treating the public folder as normalized.",
    },
    "Japan": {
        "recommended_preferred_label": "Japan",
        "decision_class": "auto_country_mapping",
        "proposed_action": "auto_map",
        "target_region_ids": "REG005",
        "target_geo_ids": "GEO036",
        "missing_geo_recommendation": "",
        "confidence": "high",
        "evidence_needed": "exact controlled geography already exists",
        "public_display_rule": "display Japan",
        "implementation_guardrail": "Keep REG005 as a browse exception until region/geography layer consistency is redesigned.",
    },
    "United Kingdom": {
        "recommended_preferred_label": "United Kingdom",
        "decision_class": "auto_country_mapping_with_specificity_review",
        "proposed_action": "map_then_review_constituent_country_when_named",
        "target_region_ids": "REG001",
        "target_geo_ids": "GEO003",
        "missing_geo_recommendation": "",
        "confidence": "medium",
        "evidence_needed": "split to England, Scotland, Wales, Northern Ireland, imperial, or colonial contexts only when source evidence is specific",
        "public_display_rule": "display United Kingdom; prefer constituent country when known later",
        "implementation_guardrail": "Do not erase constituent-country or colonial/imperial specificity.",
    },
    "Germany": {
        "recommended_preferred_label": "Germany; East Germany; West Germany when period-specific",
        "decision_class": "auto_country_mapping_with_historical_review",
        "proposed_action": "map_then_review_1949_1990_records",
        "target_region_ids": "REG001",
        "target_geo_ids": "GEO006",
        "missing_geo_recommendation": "Add East Germany and West Germany historical geographies if record volume requires precise browse/filtering.",
        "confidence": "medium",
        "evidence_needed": "period and institution/source wording for 1949-1990 records",
        "public_display_rule": "display Germany unless source evidence needs East/West specificity",
        "implementation_guardrail": "Do not force Cold War records into undifferentiated Germany when state/institution specificity matters.",
    },
    "Italy": {
        "recommended_preferred_label": "Italy",
        "decision_class": "auto_country_mapping",
        "proposed_action": "auto_map",
        "target_region_ids": "REG001",
        "target_geo_ids": "GEO011",
        "missing_geo_recommendation": "",
        "confidence": "high",
        "evidence_needed": "exact controlled geography already exists",
        "public_display_rule": "display Italy",
        "implementation_guardrail": "Keep country mapping distinct from broad European macro-region coverage.",
    },
}

CONTROLLED_REGION_DECISIONS: dict[str, dict[str, str]] = {
    "REG002": {
        "decision_class": "controlled_region_semantics_review",
        "proposed_action": "retain_id_but_stop_assigning_full_phrase_as_item_label",
        "confidence": "medium",
        "evidence_needed": "split country, Soviet/post-Soviet, Balkans, and socialist-context evidence",
        "public_display_rule": "use child geography labels; keep full phrase as internal/browse parent only",
        "implementation_guardrail": "Treat socialist context as a context facet, not a place.",
    },
    "REG003": {
        "decision_class": "controlled_region_rename_candidate",
        "proposed_action": "review_rename_to_Northern_America",
        "confidence": "medium",
        "evidence_needed": "confirm Mexico stays under REG004 and Indigenous/transborder routes remain explicit",
        "public_display_rule": "parent label only; cards should prefer country/community/city labels",
        "implementation_guardrail": "Do not let U.S. source depth dominate the macro-region semantics.",
    },
    "REG006": {
        "decision_class": "possible_hidden_mapping_gap",
        "proposed_action": "resolve_unresolved_region_before_source_gap_claim",
        "confidence": "medium",
        "evidence_needed": "search unresolved records and Korea/Korean/Hangul evidence",
        "public_display_rule": "use Korean Peninsula only for pan-Korean/historical contexts",
        "implementation_guardrail": "Do not claim Korea is truly absent until unresolved records are reviewed.",
    },
    "REG007": {
        "decision_class": "parent_browse_node_not_item_gap",
        "proposed_action": "keep_parent_region_only",
        "confidence": "high",
        "evidence_needed": "child geography coverage should carry item cards",
        "public_display_rule": "avoid East Asia as item-level label when country/territory is known",
        "implementation_guardrail": "Do not flatten China/Japan/Korea/Taiwan/Hong Kong into East Asia.",
    },
    "REG008": {
        "decision_class": "possible_hidden_mapping_gap",
        "proposed_action": "split_China_Hong_Kong_and_unresolved_records_first",
        "confidence": "medium",
        "evidence_needed": "Mainland China evidence in slash labels and unresolved records",
        "public_display_rule": "display Mainland China only when source evidence supports it",
        "implementation_guardrail": "Do not absorb Hong Kong or Taiwan into Mainland China.",
    },
    "REG009": {
        "decision_class": "possible_hidden_mapping_gap",
        "proposed_action": "split_China_Hong_Kong_and_unresolved_records_first",
        "confidence": "medium",
        "evidence_needed": "Hong Kong evidence in slash labels and unresolved records",
        "public_display_rule": "display Hong Kong separately",
        "implementation_guardrail": "Keep bilingual/colonial/activist contexts visible.",
    },
    "REG010": {
        "decision_class": "possible_hidden_mapping_gap_or_source_gap",
        "proposed_action": "audit_unresolved_then_target_source_routes",
        "confidence": "medium",
        "evidence_needed": "Taiwan/Taiwanese/Traditional Chinese/Japanese colonial source evidence",
        "public_display_rule": "display Taiwan separately",
        "implementation_guardrail": "Do not merge Taiwan into broader Chinese design history.",
    },
    "REG011": {
        "decision_class": "likely_true_source_gap",
        "proposed_action": "prioritize_source_discovery_after_mapping_cleanup",
        "confidence": "high",
        "evidence_needed": "country-level Southeast Asia source routes and image/text evidence",
        "public_display_rule": "use country labels where known; Southeast Asia as parent only",
        "implementation_guardrail": "Do not use one country as proxy for the region.",
    },
    "REG013": {
        "decision_class": "likely_true_source_gap_after_Palestine_split",
        "proposed_action": "prioritize_MENA_beyond_Palestine",
        "confidence": "high",
        "evidence_needed": "Arabic/Persian/Hebrew/Turkish/North African source routes with rights evidence",
        "public_display_rule": "use country/historical/place labels where known",
        "implementation_guardrail": "Do not treat political-poster-only material as full regional coverage.",
    },
    "REG014": {
        "decision_class": "likely_true_source_gap_after_Southern_Africa_split",
        "proposed_action": "prioritize_Africa_beyond_Southern_Africa",
        "confidence": "high",
        "evidence_needed": "West, East, Horn, North, Central, and country-level source routes",
        "public_display_rule": "continent label is parent only; cards should prefer country/subregion/community labels",
        "implementation_guardrail": "Avoid continent-as-single-category treatment.",
    },
    "REG015": {
        "decision_class": "likely_true_source_gap_after_Australia_split",
        "proposed_action": "prioritize_Pacific_and_Aotearoa_after_protocol_review",
        "confidence": "high",
        "evidence_needed": "Aotearoa New Zealand, Pacific Islands, Indigenous/community protocol evidence",
        "public_display_rule": "use country/community/subregion labels; Oceania and Pacific as parent only",
        "implementation_guardrail": "Do not let Australian institutional data stand in for Pacific coverage.",
    },
}


def norm(value: object) -> str:
    return " ".join(clean(value).lower().replace("/", " / ").split())


def index_rows(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {norm(row.get(key)): row for row in rows if clean(row.get(key))}


def controlled_lookup(regions: list[dict[str, str]], geographies: list[dict[str, str]]) -> tuple[dict[str, str], dict[str, str]]:
    region_by_label = {norm(row.get("region_name")): clean(row.get("region_id")) for row in regions}
    geo_by_label = {norm(row.get("name")): clean(row.get("geo_id")) for row in geographies}
    return region_by_label, geo_by_label


def public_stats(public_terms: list[dict[str, str]], label: str) -> dict[str, str]:
    row = index_rows([row for row in public_terms if row.get("folder_type") == "region"], "public_label").get(norm(label), {})
    return {
        "surface_count": clean(row.get("surface_count")),
        "source_count": clean(row.get("source_count")),
        "periods": clean(row.get("periods")),
    }


def make_decision(
    idx: int,
    label: str,
    label_kind: str,
    gap_status: str,
    stats: dict[str, str],
    decision: dict[str, str],
    source_basis: str,
) -> dict[str, str]:
    return {
        "decision_id": f"RGN-{idx:03d}",
        "source_label": label,
        "source_label_kind": label_kind,
        "surface_count": stats.get("surface_count", ""),
        "source_count": stats.get("source_count", ""),
        "periods": stats.get("periods", ""),
        "current_gap_status": gap_status,
        "source_basis": source_basis,
        **decision,
    }


def fallback_decision(
    label: str,
    region_by_label: dict[str, str],
    geo_by_label: dict[str, str],
) -> dict[str, str]:
    normalized = norm(label)
    if normalized in geo_by_label:
        return {
            "recommended_preferred_label": label,
            "decision_class": "existing_controlled_geography",
            "proposed_action": "keep_mapped",
            "target_region_ids": "",
            "target_geo_ids": geo_by_label[normalized],
            "missing_geo_recommendation": "",
            "confidence": "high",
            "evidence_needed": "exact controlled geography match",
            "public_display_rule": f"display {label}",
            "implementation_guardrail": "No action beyond confirming public folder-to-geo mapping.",
        }
    if normalized in region_by_label:
        return {
            "recommended_preferred_label": label,
            "decision_class": "existing_controlled_region",
            "proposed_action": "keep_as_parent_or_browse_node",
            "target_region_ids": region_by_label[normalized],
            "target_geo_ids": "",
            "missing_geo_recommendation": "",
            "confidence": "medium",
            "evidence_needed": "confirm item-level records also have child geography where possible",
            "public_display_rule": "use as browse parent; prefer child labels on item cards",
            "implementation_guardrail": "Avoid using macro-region where a specific place is known.",
        }
    return {
        "recommended_preferred_label": label,
        "decision_class": "unclassified_public_region_gap",
        "proposed_action": "manual_review",
        "target_region_ids": "",
        "target_geo_ids": "",
        "missing_geo_recommendation": "Review against authority vocabulary before adding a controlled row.",
        "confidence": "low",
        "evidence_needed": "record-level geography and context evidence",
        "public_display_rule": "keep pending until reviewed",
        "implementation_guardrail": "Do not auto-create controlled geography from folder text alone.",
    }


def build_rows() -> list[dict[str, str]]:
    regions = read_csv(DATA / "regions.csv")
    geographies = read_csv(DATA / "geographies.csv")
    region_gaps = read_csv(DATA / "taxonomy_gap_regions_v1.csv")
    public_terms = read_csv(DATA / "taxonomy_gap_public_terms_v1.csv")
    region_by_label, geo_by_label = controlled_lookup(regions, geographies)

    rows: list[dict[str, str]] = []
    used_labels: set[str] = set()
    idx = 1

    for gap in region_gaps:
        label = clean(gap.get("preferred_label"))
        if gap.get("taxonomy_kind") != "public_region_folder" or not label:
            continue
        decision = RESEARCH_DECISIONS.get(label) or fallback_decision(label, region_by_label, geo_by_label)
        rows.append(
            make_decision(
                idx,
                label,
                "public_region_folder",
                clean(gap.get("status")),
                public_stats(public_terms, label),
                decision,
                "taxonomy_gap_audit_v1 + region_geography_normalization_docx",
            )
        )
        idx += 1
        used_labels.add(label)

    for label, decision in RESEARCH_DECISIONS.items():
        if label in used_labels:
            continue
        rows.append(
            make_decision(
                idx,
                label,
                "research_packet_label",
                "not_present_as_public_gap",
                public_stats(public_terms, label),
                decision,
                "region_geography_normalization_docx",
            )
        )
        idx += 1

    for gap in region_gaps:
        if gap.get("taxonomy_kind") != "region":
            continue
        region_id = clean(gap.get("taxonomy_id"))
        decision = CONTROLLED_REGION_DECISIONS.get(region_id)
        if not decision:
            continue
        label = clean(gap.get("preferred_label"))
        stats = {
            "surface_count": clean(gap.get("exact_public_folder_count")),
            "source_count": clean(gap.get("public_source_count")),
            "periods": "",
        }
        rows.append(
            make_decision(
                idx,
                label,
                "controlled_region",
                clean(gap.get("status")),
                stats,
                {
                    "recommended_preferred_label": label,
                    "target_region_ids": region_id,
                    "target_geo_ids": "",
                    "missing_geo_recommendation": "",
                    **decision,
                },
                "taxonomy_gap_audit_v1 + region_geography_normalization_docx",
            )
        )
        idx += 1

    return rows


def report_lines(rows: list[dict[str, str]]) -> list[str]:
    class_counts = Counter(row["decision_class"] for row in rows)
    action_counts = Counter(row["proposed_action"] for row in rows)
    high_impact = [
        row
        for row in rows
        if row["source_label"] in {"Unresolved region", "Latin America", "Australia / Indigenous", "China / Hong Kong", "South Africa / Botswana", "Palestine / transnational"}
    ]
    true_gaps = [
        row for row in rows if row["decision_class"].startswith("likely_true_source_gap")
    ]
    auto_maps = [
        row for row in rows if row["decision_class"].startswith("auto_country_mapping")
    ]
    structural = [
        row for row in rows if "split" in row["decision_class"] or "split" in row["proposed_action"]
    ]

    lines = [
        "# Region / Geography Normalization Decisions v1",
        "",
        "Scope: read-only reconciliation of the Region and Geography Normalization research packet against live project taxonomy audit outputs. This report does not rewrite records, source files, public surfaces, regions, or geographies.",
        "",
        "## Summary",
        "",
        f"- decision rows: {len(rows)}",
        f"- auto country mapping rows: {len(auto_maps)}",
        f"- structural or sensitive split rows: {len(structural)}",
        f"- likely true source-gap rows after cleanup: {len(true_gaps)}",
        f"- internal QA rows: {class_counts.get('internal_qa_state', 0)}",
        "",
        "## Decision Classes",
        "",
    ]
    for label, count in sorted(class_counts.items()):
        lines.append(f"- {label}: {count}")
    lines.extend(["", "## Proposed Actions", ""])
    for label, count in sorted(action_counts.items()):
        lines.append(f"- {label}: {count}")

    lines.extend(["", "## Highest-Impact Rows", ""])
    for row in high_impact:
        lines.append(
            f"- {row['source_label']}: {row['decision_class']} -> {row['proposed_action']} "
            f"(surfaces={row['surface_count'] or 'n/a'}, sources={row['source_count'] or 'n/a'})"
        )

    lines.extend(["", "## Likely True Source Gaps After Mapping Cleanup", ""])
    for row in true_gaps:
        lines.append(f"- {row['source_label']}: {row['proposed_action']} · guardrail: {row['implementation_guardrail']}")

    lines.extend(
        [
            "",
            "## Implementation Notes",
            "",
            "- First pass should only auto-map high-confidence country labels already present in `geographies.csv`.",
            "- Slash labels should be split from record evidence, not normalized as preferred labels.",
            "- `Unresolved region` should be removed from public browse semantics and treated as an internal QA state.",
            "- Sensitive and historical labels need period/source review before any automated rewrite.",
            "- True source-gap capture should start only after the major mapping and split decisions are applied or sampled.",
            "",
            "## Generated Files",
            "",
            f"- `data/{DECISIONS.name}`",
            f"- `docs/capture/{REPORT.name}`",
        ]
    )
    return lines


def main() -> None:
    rows = build_rows()
    write_csv(DECISIONS, rows, FIELDS)
    REPORT.write_text("\n".join(report_lines(rows)) + "\n", encoding="utf-8")

    print(f"decision_rows={len(rows)}")
    print(f"wrote {DECISIONS.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
