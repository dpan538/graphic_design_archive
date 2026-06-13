#!/usr/bin/env python3
"""Generate the next capture and normalization plan.

The plan is a queue for future work. It does not run probes, fetch remote
records, download images, or modify archive surfaces.
"""

from __future__ import annotations

from collections import Counter

from lib.archive_audit import DATA, DOCS, GENERATED, ROOT, clean, read_csv, read_payload, surface_region, write_csv


MANUAL_CLUSTERS = DATA / "region_geo_manual_review_clusters_v1.csv"
READY_ACTIONS = DATA / "region_geo_cleaning_action_plan_v1.csv"
RELEASE_SNAPSHOT = DATA / "release_snapshot_v1.csv"
RIGHTS_PRIORITIES = DATA / "image_rights_repair_source_priorities_v1.csv"
PERIOD_BREAKDOWN = DATA / "source_coverage_period_breakdown_v1.csv"
OUTPUT_PLAN = DATA / "next_capture_plan_v1.csv"
OUTPUT_REPORT = DOCS / "NEXT_CAPTURE_AND_CLEANING_PLAN_v1.md"

FIELDS = [
    "plan_id",
    "phase",
    "track",
    "priority",
    "region_focus",
    "country_or_cluster_focus",
    "target_success_count",
    "source_strategy",
    "rights_preference",
    "text_requirement",
    "cleaning_dependency",
    "validation_gate",
    "rationale",
]


def current_region_counts() -> Counter[str]:
    payload = read_payload()
    return Counter(surface_region(surface) for surface in payload.get("surfaces", []))


def cluster_counts() -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in read_csv(MANUAL_CLUSTERS):
        try:
            counts[row.get("suggested_label", "")] += int(row.get("row_count", "0"))
        except ValueError:
            continue
    return counts


def metric_value(metric: str, default: str = "") -> str:
    for row in read_csv(RELEASE_SNAPSHOT):
        if row.get("metric") == metric:
            return clean(row.get("value")) or default
    return default


def int_metric(metric: str, default: int = 0) -> int:
    try:
        return int(float(metric_value(metric, str(default))))
    except ValueError:
        return default


def current_action_count() -> int:
    return len(read_csv(READY_ACTIONS))


def period_gap_summary() -> str:
    parts = []
    for row in read_csv(PERIOD_BREAKDOWN):
        try:
            target = int(float(row.get("target_source_count", "0")))
            active = int(float(row.get("active_source_count", "0")))
        except ValueError:
            continue
        gap = max(0, target - active)
        parts.append(f"{row.get('period_band')}: {gap}")
    return "; ".join(parts)


def top_rights_sources(limit: int = 8) -> str:
    rows = read_csv(RIGHTS_PRIORITIES)[:limit]
    return "; ".join(
        f"{clean(row.get('source_name'))} ({clean(row.get('weighted_gap_points'))} pts)"
        for row in rows
    )


def base_plan_rows() -> list[dict[str, str]]:
    cluster = cluster_counts()
    action_count = current_action_count()
    active_sources = int_metric("archive_active_public_sources")
    source_gap = max(0, 20000 - active_sources)
    minimum_gap = max(0, 16000 - active_sources)
    rights_focus = top_rights_sources()
    return [
        {
            "phase": "cleaning_first",
            "track": "region_geo_safe_apply",
            "priority": "P0",
            "region_focus": "Cross-region",
            "country_or_cluster_focus": f"{action_count} hardened direct-conflict candidates",
            "target_success_count": f"{action_count} reviewed patch candidates",
            "source_strategy": "spot-check by label and source family before any mapping application",
            "rights_preference": "no rights change",
            "text_requirement": "preserve current source text; no synthetic editorial text",
            "cleaning_dependency": "data/region_geo_cleaning_action_plan_v1.csv",
            "validation_gate": "sample audit clean; no historical-dispute flag; high-signal metadata contains target geography",
            "rationale": "Turn the safest normalization rows into a controlled patch queue without rewriting public data yet.",
        },
        {
            "phase": "cleaning_first",
            "track": "historical_split_policy",
            "priority": "P0",
            "region_focus": "Latin America / North America",
            "country_or_cluster_focus": "Mexico; United States military occupation context",
            "target_success_count": "220 reviewed decisions",
            "source_strategy": "review Matamoros 1846 records as historical-context labels, not simple Mexico vs United States relabels",
            "rights_preference": "no rights change",
            "text_requirement": "record concise policy note for date-sensitive context",
            "cleaning_dependency": "data/region_geo_requires_historical_split_review_v1.csv",
            "validation_gate": "taxonomy supports split/context label or keeps existing label with historical note",
            "rationale": "This cluster dominates the historical split queue and can distort region statistics if flattened.",
        },
        {
            "phase": "cleaning_first",
            "track": "rights_repair_before_volume",
            "priority": "P0",
            "region_focus": "Cross-region",
            "country_or_cluster_focus": "Cooper Hewitt; Wellcome; Library of Congress; GSU CONTENTdm; AIC; Internet Archive; V&A; Te Papa",
            "target_success_count": "repair 800-1200 candidate objects or at least 223.40 weighted-publication points",
            "source_strategy": "item-level rights/source-evidence review over existing IMG02/IMG01/IMG00/IMG04 queues before adding more low-quality volume",
            "rights_preference": "only promote IMG03 when item-level open evidence is explicit; never from heuristic/platform/TOS/LLM signals",
            "text_requirement": "retain source notes and citation evidence for every repair decision",
            "cleaning_dependency": "data/image_rights_repair_candidates_v1.csv",
            "validation_gate": "object verified-open >= 95%; object weighted publication-grade >= 95%; no automatic upgrades",
            "rationale": f"Rights repair is the fastest route to the 95% image gates. Current top weighted gaps: {rights_focus}.",
        },
        {
            "phase": "capture_tranche_a",
            "track": "source_pool_5000_after_cleaning",
            "priority": "P0",
            "region_focus": "Global with non-mainstream weighting",
            "country_or_cluster_focus": "first 5,000 new active public-payload-ready sources",
            "target_success_count": "5,000 successful active sources after item/image capture, surface build, and metrics",
            "source_strategy": "combine authority APIs, art schools, community archives, design platforms, studios, national collections, and controlled Commons open-source pages",
            "rights_preference": "IMG03/IMG02 first; reject image mirrors and unsupported source pages",
            "text_requirement": "every main-sheet candidate should have source-derived text; avoid adding IMG04-only records as filler",
            "cleaning_dependency": "run region/geography hardening and rights repair queues before full incorporation",
            "validation_gate": f"minimum source gap now {minimum_gap}; full 20k gap now {source_gap}; count success only after rebuild and release snapshot",
            "rationale": "This tranche should push the project past the 80% public source floor while preserving rights and attribution quality.",
        },
        {
            "phase": "capture_tranche_a",
            "track": "authority_institution_sources",
            "priority": "P1",
            "region_focus": "Global / authority sources",
            "country_or_cluster_focus": "art schools, national libraries, design museums, university special collections, cultural institutes",
            "target_success_count": "1,400-1,700 successful active sources",
            "source_strategy": "prefer APIs/RSS/OAI/IIIF/search endpoints with item metadata, source URL, rights text, and description fields",
            "rights_preference": "verified open where explicit; IMG02 source-hosted evidence acceptable pending item-level review",
            "text_requirement": "catalogue description or institutional context required for research-packet value",
            "cleaning_dependency": "deduplicate against current source names and source URLs before capture",
            "validation_gate": "source-visible >= 99%; source authority flags reviewed; no duplicated institution mirrors",
            "rationale": "Authority sources are the best way to grow toward 20,000 without introducing fabricated or weak records.",
        },
        {
            "phase": "capture_tranche_a",
            "track": "contemporary_studio_platform_school_sources",
            "priority": "P1",
            "region_focus": "2000-2026 / contemporary global",
            "country_or_cluster_focus": "workshops, art/design schools, community design programs, studios, biennales, visual communication platforms",
            "target_success_count": "1,100-1,300 successful active sources",
            "source_strategy": "source discovery first, then metadata-only probes; favor project pages with creator/date/location/text and clear rights/source links",
            "rights_preference": "do not force open-image status; use IMG02 when source-hosted display is clear, keep rights state explicit",
            "text_requirement": "project/studio description required; shallow portfolio thumbnails without text should not become main sheets",
            "cleaning_dependency": "institution authority and duplication review",
            "validation_gate": "2000-2026 growth without future-date inflation; no excessive 2026 bug recurrence",
            "rationale": "The internet period should be richer, but it must not become a pile of weak image rows or future-dated records.",
        },
        {
            "phase": "capture_tranche_a",
            "track": "southeast_asia_modern_contemporary",
            "priority": "P1",
            "region_focus": "Southeast Asia",
            "country_or_cluster_focus": f"Indonesia ({cluster.get('Indonesia', 0)} review hints); Vietnam; Philippines; Thailand; Malaysia; Singapore",
            "target_success_count": "500-650 successful active sources",
            "source_strategy": "national libraries, design biennales, poster archives, university collections, contemporary studio/project pages, local design platforms",
            "rights_preference": "IMG03 open-license first; IMG02 source-hosted evidence second; avoid weak IMG04-only additions",
            "text_requirement": "at least one source-derived description or context note per main candidate",
            "cleaning_dependency": "separate topic geography from source geography in Indonesia/Singapore pending clusters",
            "validation_gate": "source-visible >= 90%; IMG04 <= 10%; country attribution from high-signal metadata",
            "rationale": "Large review hints suggest both opportunity and noise; capture should improve coverage while tightening attribution.",
        },
        {
            "phase": "capture_tranche_a",
            "track": "caucasus_central_asia_repair",
            "priority": "P1",
            "region_focus": "Eastern Europe / Caucasus / Central Asia",
            "country_or_cluster_focus": f"Caucasus ({cluster.get('Caucasus', 0)}); Azerbaijan ({cluster.get('Azerbaijan', 0)}); Georgia ({cluster.get('Georgia', 0)}); Armenia; Kazakhstan; Uzbekistan; Kyrgyzstan",
            "target_success_count": "350-450 successful active sources",
            "source_strategy": "national museum/library records, poster/stamp collections, theatre/film graphics, post-Soviet design platforms, bilingual source queries",
            "rights_preference": "IMG03/IMG02 only where source evidence is clear; keep Soviet-era republic context explicit",
            "text_requirement": "source-derived context required for republic vs USSR/Caucasus ambiguity",
            "cleaning_dependency": "do not collapse Caucasus into a country label without evidence",
            "validation_gate": "region/geography label must distinguish country, macro-region, and USSR-context records",
            "rationale": "The current pending clusters show under-defined regional logic and need both capture and normalization discipline.",
        },
        {
            "phase": "capture_tranche_a",
            "track": "south_asia_bangladesh_nepal_pakistan",
            "priority": "P1",
            "region_focus": "South Asia",
            "country_or_cluster_focus": f"Bangladesh ({cluster.get('Bangladesh', 0)}); Pakistan; Nepal; Sri Lanka; India non-canonical regional sources",
            "target_success_count": "450-550 successful active sources",
            "source_strategy": "national archives, museum/public library collections, design education archives, festival graphics, visual communication studios",
            "rights_preference": "prioritize source-visible IMG02/IMG03, reject unsupported image mirrors",
            "text_requirement": "source text or catalogue description required for main-sheet candidates",
            "cleaning_dependency": "use pending text hints only as search seeds",
            "validation_gate": "object verified-open improves without increasing IMG04 share",
            "rationale": "South Asia needs stronger country-level coverage and more text-supported research packets.",
        },
        {
            "phase": "capture_tranche_a",
            "track": "mena_africa_noncanonical",
            "priority": "P1",
            "region_focus": "MENA / Sub-Saharan Africa",
            "country_or_cluster_focus": "Egypt; Morocco; Tunisia; Algeria; Lebanon; Palestine; Nigeria; Ghana; Kenya; Ethiopia; Senegal; South Africa",
            "target_success_count": "650-800 successful active sources",
            "source_strategy": "national collections, poster/periodical archives, cultural institute records, design studios, open museum APIs, Wikimedia Commons only when source page and rights are clear",
            "rights_preference": "IMG03 where verified; IMG02 allowed with strong source-hosted evidence; no IMG01/IMG03 heuristic upgrade",
            "text_requirement": "avoid image-only rows; require description/context for research value",
            "cleaning_dependency": "review Palestine/sensitive labels manually before automated mapping",
            "validation_gate": "macro-region and country labels remain distinct; source-visible >= 90%",
            "rationale": "These regions remain structurally important for non-mainstream coverage and need text-rich capture rather than only object rows.",
        },
        {
            "phase": "capture_tranche_a",
            "track": "pre_1940_historical_continuity",
            "priority": "P1",
            "region_focus": "Pre-1940 global continuity",
            "country_or_cluster_focus": "pre-1930 gap plus 1930-1940 advertising, printing, visual education, colonial/postcolonial print cultures",
            "target_success_count": "450-650 successful active sources",
            "source_strategy": "library catalogues, periodical indexes, poster collections, trade catalogues, early advertising/typography records",
            "rights_preference": "public-domain/open evidence preferred; no heuristic IMG03 upgrade",
            "text_requirement": "source/citation text required so early records support research continuity",
            "cleaning_dependency": "historical place/state sensitivity review",
            "validation_gate": f"period gaps before capture: {period_gap_summary()}",
            "rationale": "Earlier periods cover long spans; adding stronger pre-1940 evidence makes the historical narrative less discontinuous.",
        },
        {
            "phase": "capture_tranche_a",
            "track": "latin_america_cleanup_and_growth",
            "priority": "P2",
            "region_focus": "Latin America and Caribbean",
            "country_or_cluster_focus": "Mexico; Brazil; Argentina; Chile; Colombia; Peru; Cuba; Caribbean design/print cultures",
            "target_success_count": "350-450 successful active sources after conflict cleanup",
            "source_strategy": "clean existing Mexico/Brazil/Argentina conflicts first, then add country-balanced poster, periodical, publishing, and studio sources",
            "rights_preference": "IMG03/IMG02 with clear evidence",
            "text_requirement": "source-derived context required for main/sub sheet grouping",
            "cleaning_dependency": "resolve high-confidence direct-conflict rows and Matamoros historical policy first",
            "validation_gate": "new capture must not recreate the same France/US/Germany misfiled Latin America conflicts",
            "rationale": "Latin America has strong candidate volume but needs normalization before expansion.",
        },
        {
            "phase": "capture_tranche_b",
            "track": "second_5000_after_audit",
            "priority": "P2",
            "region_focus": "Global with measured reweighting",
            "country_or_cluster_focus": "second 5,000 successful active sources only after tranche A release snapshot",
            "target_success_count": "5,000 additional successful active sources, then full rebuild and gate audit",
            "source_strategy": "rebalance based on tranche A failures, verified-open movement, text-page growth, and duplicate/source-authority audit",
            "rights_preference": "increase verified-open toward 95 while preserving rights evidence",
            "text_requirement": "raise text-supported main/sub packets; do not reward image-only volume",
            "cleaning_dependency": "run duplicate/authority review after tranche A before opening tranche B",
            "validation_gate": "projected public sources near or above 20,000; object source-visible 99; verified-open 95; weighted publication 95",
            "rationale": "The second 5,000 should be adaptive, not a blind repeat of the first capture mix.",
        },
        {
            "phase": "method_lock",
            "track": "classification_deep_research_inputs",
            "priority": "P2",
            "region_focus": "Global",
            "country_or_cluster_focus": "movement/theme/method terms that remain unstable",
            "target_success_count": "one evidence packet per disputed method family",
            "source_strategy": "use cleaned queues and capture failures to define research prompts; do not deep-research before source evidence has been exhausted",
            "rights_preference": "not applicable",
            "text_requirement": "extract classification language from source descriptions and catalogues",
            "cleaning_dependency": "taxonomy gap audit plus region/geography cleaning clusters",
            "validation_gate": "method terms must distinguish movement, medium, source family, theme, and research-packet role",
            "rationale": "Deep research should validate observed archive ambiguity rather than inventing taxonomy in advance.",
        },
    ]


def add_ids(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for idx, row in enumerate(rows, start=1):
        next_row = {"plan_id": f"NEXT-CAP-{idx:03d}"}
        next_row.update(row)
        out.append(next_row)
    return out


def write_report(rows: list[dict[str, str]]) -> None:
    counts = current_region_counts()
    phase_counts = Counter(row["phase"] for row in rows)
    priority_counts = Counter(row["priority"] for row in rows)
    active_sources = int_metric("archive_active_public_sources")
    source_gap = max(0, 20000 - active_sources)
    minimum_gap = max(0, 16000 - active_sources)
    lines = [
        "# Next Capture And Cleaning Plan v1",
        "",
        "This plan schedules the next work cycle after the region/geography confidence gate. It does not run capture or mutate archive data.",
        "",
        "## Current Read",
        "",
        f"- Active public sources: {active_sources}; full 20,000-source gap: {source_gap}; 80% release floor gap: {minimum_gap}.",
        f"- Source-visible: {metric_value('object_source_visible_rate', '?')}%; verified-open: {metric_value('object_verified_open_rate', '?')}%; weighted publication-grade: {metric_value('object_weighted_publication_grade_rate', '?')}%; IMG04: {metric_value('object_img04_rate', '?')}%.",
        f"- Period source gaps: {period_gap_summary()}.",
        f"- Top rights-repair sources: {top_rights_sources()}.",
        "- The immediate bottleneck is not raw source discovery alone; it is controlled attribution, source authority, rights evidence, and text-supported surface value.",
        "- The next capture cycle should start after the first cleaning pass so new sources inherit stricter labels.",
        "",
        "## Region Surface Snapshot",
        "",
    ]
    for key, value in counts.most_common(15):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Plan Phases", ""])
    for key, value in phase_counts.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Priorities", ""])
    for key, value in priority_counts.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Recommended Sequence", ""])
    for row in rows:
        lines.append(
            f"- {row['priority']} `{row['track']}`: {row['country_or_cluster_focus']} "
            f"({row['target_success_count']})"
        )
    lines.extend(
        [
            "",
            "## Operating Rules",
            "",
            "- Do not download images during source discovery.",
            "- Do not upgrade IMG01/IMG03 from heuristic, platform, TOS, or LLM signals.",
            "- Count new successful sources only after item/image capture, surface build, archive incorporation, and release-gate metrics.",
            "- Keep IMG04 low, but do not remove text capture pressure; text is required for research-packet value.",
            "- Use sandbox/sample runs before full rebuilds whenever the task does not require rebuilding all surfaces.",
            "",
            "## Output File",
            "",
            f"- `{OUTPUT_PLAN.relative_to(ROOT)}`",
        ]
    )
    OUTPUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not GENERATED.joinpath("public_surfaces_v1.json").exists():
        print("warning: generated/public_surfaces_v1.json not found; region snapshot will be empty")
    rows = add_ids(base_plan_rows())
    write_csv(OUTPUT_PLAN, rows, FIELDS)
    write_report(rows)
    print(f"next_capture_plan_rows={len(rows)}")
    print(f"wrote {OUTPUT_PLAN.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
