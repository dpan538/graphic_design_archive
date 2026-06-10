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


def base_plan_rows() -> list[dict[str, str]]:
    cluster = cluster_counts()
    return [
        {
            "phase": "cleaning_first",
            "track": "region_geo_safe_apply",
            "priority": "P0",
            "region_focus": "Cross-region",
            "country_or_cluster_focus": "88 high-confidence direct-conflict candidates",
            "target_success_count": "88 reviewed patch candidates",
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
            "phase": "capture_after_cleaning",
            "track": "southeast_asia_modern_contemporary",
            "priority": "P1",
            "region_focus": "Southeast Asia",
            "country_or_cluster_focus": f"Indonesia ({cluster.get('Indonesia', 0)} review hints); Vietnam; Philippines; Thailand; Malaysia; Singapore",
            "target_success_count": "220 active sources / 140 surface-ready objects",
            "source_strategy": "national libraries, design biennales, poster archives, university collections, contemporary studio/project pages, local design platforms",
            "rights_preference": "IMG03 open-license first; IMG02 source-hosted evidence second; avoid weak IMG04-only additions",
            "text_requirement": "at least one source-derived description or context note per main candidate",
            "cleaning_dependency": "separate topic geography from source geography in Indonesia/Singapore pending clusters",
            "validation_gate": "source-visible >= 90%; IMG04 <= 10%; country attribution from high-signal metadata",
            "rationale": "Large review hints suggest both opportunity and noise; capture should improve coverage while tightening attribution.",
        },
        {
            "phase": "capture_after_cleaning",
            "track": "caucasus_central_asia_repair",
            "priority": "P1",
            "region_focus": "Eastern Europe / Caucasus / Central Asia",
            "country_or_cluster_focus": f"Caucasus ({cluster.get('Caucasus', 0)}); Azerbaijan ({cluster.get('Azerbaijan', 0)}); Georgia ({cluster.get('Georgia', 0)}); Armenia; Kazakhstan; Uzbekistan; Kyrgyzstan",
            "target_success_count": "180 active sources / 110 surface-ready objects",
            "source_strategy": "national museum/library records, poster/stamp collections, theatre/film graphics, post-Soviet design platforms, bilingual source queries",
            "rights_preference": "IMG03/IMG02 only where source evidence is clear; keep Soviet-era republic context explicit",
            "text_requirement": "source-derived context required for republic vs USSR/Caucasus ambiguity",
            "cleaning_dependency": "do not collapse Caucasus into a country label without evidence",
            "validation_gate": "region/geography label must distinguish country, macro-region, and USSR-context records",
            "rationale": "The current pending clusters show under-defined regional logic and need both capture and normalization discipline.",
        },
        {
            "phase": "capture_after_cleaning",
            "track": "south_asia_bangladesh_nepal_pakistan",
            "priority": "P1",
            "region_focus": "South Asia",
            "country_or_cluster_focus": f"Bangladesh ({cluster.get('Bangladesh', 0)}); Pakistan; Nepal; Sri Lanka; India non-canonical regional sources",
            "target_success_count": "180 active sources / 110 surface-ready objects",
            "source_strategy": "national archives, museum/public library collections, design education archives, festival graphics, visual communication studios",
            "rights_preference": "prioritize source-visible IMG02/IMG03, reject unsupported image mirrors",
            "text_requirement": "source text or catalogue description required for main-sheet candidates",
            "cleaning_dependency": "use pending text hints only as search seeds",
            "validation_gate": "object verified-open improves without increasing IMG04 share",
            "rationale": "South Asia needs stronger country-level coverage and more text-supported research packets.",
        },
        {
            "phase": "capture_after_cleaning",
            "track": "mena_africa_noncanonical",
            "priority": "P1",
            "region_focus": "MENA / Sub-Saharan Africa",
            "country_or_cluster_focus": "Egypt; Morocco; Tunisia; Algeria; Lebanon; Palestine; Nigeria; Ghana; Kenya; Ethiopia; Senegal; South Africa",
            "target_success_count": "260 active sources / 160 surface-ready objects",
            "source_strategy": "national collections, poster/periodical archives, cultural institute records, design studios, open museum APIs, Wikimedia Commons only when source page and rights are clear",
            "rights_preference": "IMG03 where verified; IMG02 allowed with strong source-hosted evidence; no IMG01/IMG03 heuristic upgrade",
            "text_requirement": "avoid image-only rows; require description/context for research value",
            "cleaning_dependency": "review Palestine/sensitive labels manually before automated mapping",
            "validation_gate": "macro-region and country labels remain distinct; source-visible >= 90%",
            "rationale": "These regions remain structurally important for non-mainstream coverage and need text-rich capture rather than only object rows.",
        },
        {
            "phase": "capture_after_cleaning",
            "track": "latin_america_cleanup_and_growth",
            "priority": "P2",
            "region_focus": "Latin America and Caribbean",
            "country_or_cluster_focus": "Mexico; Brazil; Argentina; Chile; Colombia; Peru; Cuba; Caribbean design/print cultures",
            "target_success_count": "180 active sources / 110 surface-ready objects",
            "source_strategy": "clean existing Mexico/Brazil/Argentina conflicts first, then add country-balanced poster, periodical, publishing, and studio sources",
            "rights_preference": "IMG03/IMG02 with clear evidence",
            "text_requirement": "source-derived context required for main/sub sheet grouping",
            "cleaning_dependency": "resolve high-confidence direct-conflict rows and Matamoros historical policy first",
            "validation_gate": "new capture must not recreate the same France/US/Germany misfiled Latin America conflicts",
            "rationale": "Latin America has strong candidate volume but needs normalization before expansion.",
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
    lines = [
        "# Next Capture And Cleaning Plan v1",
        "",
        "This plan schedules the next work cycle after the region/geography confidence gate. It does not run capture or mutate archive data.",
        "",
        "## Current Read",
        "",
        "- The project now has a usable normalization frame, but region/geography certainty is uneven.",
        "- The immediate bottleneck is not raw source discovery alone; it is controlled attribution, historical-context policy, and text-supported surface value.",
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
