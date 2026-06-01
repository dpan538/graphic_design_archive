#!/usr/bin/env python3
"""Generate the next item-level capture queue from source probes."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
PROBE = DATA / "source_candidate_probe_v1.csv"
REGISTRY = DATA / "source_candidate_registry_v1.csv"
OUTPUT = DATA / "item_capture_queue_v1.csv"
REPORT = DOCS / "ITEM_CAPTURE_QUEUE_v1.md"

FIELDNAMES = [
    "queue_id",
    "candidate_id",
    "source_name",
    "macro_region",
    "country_or_region",
    "institution_class",
    "adapter_hint",
    "queue_priority",
    "capture_phase",
    "target_record_count",
    "target_period",
    "first_query_terms",
    "image_policy",
    "text_policy",
    "rights_gate",
    "source_url",
    "next_action",
    "notes",
]

QUERY_TERMS_BY_REGION = {
    "Latin America": "poster; revista; diseño gráfico; tipografía; propaganda; publicidad",
    "Latin America and the Caribbean": "poster; magazine; propaganda; public campaign; print culture",
    "East Asia": "poster; graphic design; typography; advertisement; magazine; propaganda",
    "Southeast Asia": "poster; advertisement; public campaign; magazine; print culture",
    "South Asia": "poster; commercial art; typography; public communication; design education",
    "Middle East and North Africa": "poster; advertisement; typography; magazine; public campaign",
    "Africa": "poster; pamphlet; anti-apartheid; public campaign; magazine; print culture",
    "Eastern Europe": "poster; plakát; typography; magazine; propaganda; print culture",
    "Oceania and Pacific": "poster; ephemera; public campaign; Indigenous; magazine",
}

ADAPTER_PHASE = {
    "iiif_manifest_adapter": "protocol:iiif",
    "dspace_oai_or_rest_adapter": "protocol:dspace_oai",
    "kramerius_adapter": "protocol:kramerius",
    "omeka_api_adapter": "protocol:omeka",
    "html_jsonld_adapter": "protocol:html_jsonld",
    "pdf_text_or_link_adapter": "protocol:pdf_text",
    "html_text_source_adapter": "protocol:html_text",
    "html_source_probe_then_manual_rules": "protocol:html_manual",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


def load_registry() -> dict[str, dict[str, str]]:
    return {row["candidate_id"]: row for row in read_csv(REGISTRY)}


def queue_priority(row: dict[str, str]) -> str:
    if row["capture_priority_next"] == "P1_adapter_candidate":
        return "Q1"
    if row["capture_priority_next"] == "P2_html_source_candidate":
        return "Q2"
    return "Q3"


def record_target(row: dict[str, str]) -> str:
    if row["adapter_hint"] in {"iiif_manifest_adapter", "dspace_oai_or_rest_adapter", "kramerius_adapter"}:
        return "12"
    if row["adapter_hint"] in {"html_jsonld_adapter", "omeka_api_adapter"}:
        return "8"
    return "5"


def next_action(row: dict[str, str]) -> str:
    adapter = row["adapter_hint"]
    if adapter == "iiif_manifest_adapter":
        return "Find search/API endpoint; harvest manifest URLs; create source-hosted IMG02 records only after rights row exists."
    if adapter == "dspace_oai_or_rest_adapter":
        return "Try /oai/request Identify/ListRecords and /server/api discovery before HTML fallback."
    if adapter == "kramerius_adapter":
        return "Use Kramerius API search for title/keyword, then inspect item policy and IIIF/viewer support."
    if adapter == "omeka_api_adapter":
        return "Probe /api/items and media endpoints; keep images source-hosted unless license is explicit."
    if adapter == "html_jsonld_adapter":
        return "Extract JSON-LD/schema metadata and source text; only link images unless record-level rights are explicit."
    if adapter == "pdf_text_or_link_adapter":
        return "Capture PDF/text record as IMG04 or IMG02 source-viewer; use text page as reading appendix."
    return "Create HTML parser with conservative link-only image policy."


def select_queue_rows() -> list[dict[str, str]]:
    registry = load_registry()
    probes = [
        row
        for row in read_csv(PROBE)
        if row["capture_priority_next"] in {"P1_adapter_candidate", "P2_html_source_candidate"}
    ]

    # Keep all Q1. For Q2, cap by adapter/region so it does not crowd out the
    # protocol candidates.
    rows: list[dict[str, str]] = []
    q2_counts: Counter[tuple[str, str]] = Counter()
    for row in probes:
        if row["capture_priority_next"] == "P2_html_source_candidate":
            key = (row["macro_region"], row["adapter_hint"])
            if q2_counts[key] >= 2:
                continue
            q2_counts[key] += 1
        rows.append(row)

    def sort_key(row: dict[str, str]) -> tuple[int, str, str]:
        q_rank = 0 if row["capture_priority_next"] == "P1_adapter_candidate" else 1
        adapter_rank = {
            "iiif_manifest_adapter": "00",
            "dspace_oai_or_rest_adapter": "01",
            "kramerius_adapter": "02",
            "omeka_api_adapter": "03",
            "html_jsonld_adapter": "04",
            "pdf_text_or_link_adapter": "05",
            "html_text_source_adapter": "06",
        }.get(row["adapter_hint"], "99")
        return (q_rank, adapter_rank, row["candidate_id"])

    output: list[dict[str, str]] = []
    for idx, row in enumerate(sorted(rows, key=sort_key), start=1):
        reg = registry.get(row["candidate_id"], {})
        output.append(
            {
                "queue_id": f"ICQ{idx:03d}",
                "candidate_id": row["candidate_id"],
                "source_name": row["source_name"],
                "macro_region": row["macro_region"],
                "country_or_region": row["country_or_region"],
                "institution_class": row["institution_class"],
                "adapter_hint": row["adapter_hint"],
                "queue_priority": queue_priority(row),
                "capture_phase": ADAPTER_PHASE.get(row["adapter_hint"], "protocol:manual_html"),
                "target_record_count": record_target(row),
                "target_period": "1931-1970 first; keep later records if discovered",
                "first_query_terms": QUERY_TERMS_BY_REGION.get(row["macro_region"], "poster; graphic design; typography; print culture"),
                "image_policy": row["recommended_image_policy"],
                "text_policy": row["recommended_text_policy"],
                "rights_gate": "record_level_rights_required_before_IMG03; otherwise IMG00/IMG02 source-return only",
                "source_url": row["url"],
                "next_action": next_action(row),
                "notes": reg.get("notes", ""),
            }
        )
    return output


def write_report(rows: list[dict[str, str]]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    by_priority = Counter(row["queue_priority"] for row in rows)
    by_adapter = Counter(row["adapter_hint"] for row in rows)
    by_region = Counter(row["macro_region"] for row in rows)
    lines = [
        "# Item Capture Queue v1",
        "",
        "This queue converts source-level probe evidence into the next item-level capture plan. It should be treated as a work queue, not as public archive content.",
        "",
        f"- Queue rows: {len(rows)}",
        f"- Q1 protocol/adapter rows: {by_priority.get('Q1', 0)}",
        f"- Q2 HTML/text rows: {by_priority.get('Q2', 0)}",
        "",
        "## Adapter Mix",
        "",
    ]
    for key, count in by_adapter.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Region Mix", ""])
    for key, count in by_region.most_common():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## First 15 Queue Rows", ""])
    for row in rows[:15]:
        lines.append(
            f"- {row['queue_id']} | {row['queue_priority']} | {row['source_name']} | "
            f"{row['macro_region']} | {row['adapter_hint']} | target {row['target_record_count']}"
        )
    lines.extend(
        [
            "",
            "## Execution Rule",
            "",
            "Run one adapter family at a time. Each family must write raw source payloads, source-level evidence, image policy, text excerpts, and failure rows. The goal is not to maximize rows; the goal is to prove that each source can produce readable, rights-aware archive surfaces without collapsing back into large-institution sampling.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = select_queue_rows()
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    write_report(rows)
    print(f"Wrote {OUTPUT} ({len(rows)} rows)")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
