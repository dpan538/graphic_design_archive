#!/usr/bin/env python3
"""Generate follow-up queues from the contemporary source scan v2 outputs.

This is a source-planning derivation only. It reads the v2 candidate/probe CSVs
and writes queue files for adapter planning, regional prioritization, and retry
work. It does not fetch source pages, read raw probe bodies, download images, or
change image/rights states.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

CANDIDATES = DATA / "contemporary_source_scan_candidates_1990_2026_v2.csv"
PROBE = DATA / "contemporary_source_scan_probe_1990_2026_v2.csv"

P1_QUEUE = DATA / "contemporary_source_p1_protocol_queue_1990_2026_v2.csv"
REGION_PRIORITIES = DATA / "contemporary_source_region_priorities_1990_2026_v2.csv"
RETRY_REGISTRY = DATA / "contemporary_source_retry_registry_1990_2026_v2.csv"
ADAPTER_QUEUE = DATA / "contemporary_source_adapter_queue_1990_2026_v2.csv"
REPORT = DOCS / "CONTEMPORARY_SOURCE_SCAN_FOLLOWUP_1990_2026_v2.md"

IMAGE_BOUNDARY = (
    "do_not_capture_images; metadata_source_links_descriptions_rights_evidence_only; "
    "IMG03_requires_authoritative_item_level_open_rights"
)

REGION_WEIGHTS = {
    "Africa": 5,
    "MENA": 5,
    "South Asia": 5,
    "Southeast Asia": 5,
    "Latin America": 4,
    "Latin America / Caribbean": 4,
    "East Asia": 4,
    "Oceania / Indigenous": 4,
    "Eastern Europe": 3,
    "Eastern Europe / Central Asia": 3,
    "Oceania": 3,
    "Global": 2,
    "Europe": 1,
    "North America": 1,
}

P1_FIELDNAMES = [
    "queue_id",
    "candidate_id",
    "source_name",
    "macro_region",
    "subregion",
    "country_or_region",
    "source_class",
    "protocol_lane",
    "adapter_type",
    "detected_protocols",
    "adapter_hint",
    "capture_priority_next",
    "candidate_priority",
    "recommended_text_policy_next",
    "recommended_image_policy_next",
    "rights_risk",
    "next_action",
    "image_capture_boundary",
    "source_url",
    "final_url",
    "notes",
]

REGION_FIELDNAMES = [
    "rank",
    "macro_region",
    "total_candidates",
    "ok",
    "failed",
    "http_error",
    "p1_adapter_build",
    "p1_text_source_enrichment",
    "p2_retry_manual_verification",
    "p2_discovery_lead_queue",
    "p2_manual_source_review",
    "detected_protocol_count",
    "candidate_p0",
    "candidate_p1",
    "candidate_p2",
    "candidate_p3",
    "priority_score",
    "next_action",
    "image_capture_boundary",
]

RETRY_FIELDNAMES = [
    "retry_id",
    "candidate_id",
    "source_name",
    "macro_region",
    "subregion",
    "country_or_region",
    "source_class",
    "source_url",
    "final_url",
    "http_status",
    "probe_status",
    "failure_family",
    "failure_reason",
    "candidate_priority",
    "capture_priority_next",
    "alternate_endpoint_hint",
    "recommended_retry_route",
    "rights_boundary",
    "notes",
]

ADAPTER_FIELDNAMES = [
    "queue_id",
    "candidate_id",
    "source_name",
    "macro_region",
    "subregion",
    "country_or_region",
    "source_url",
    "protocol_lane",
    "adapter_type",
    "queue_priority",
    "queue_status",
    "candidate_priority",
    "probe_status",
    "capture_priority_next",
    "rights_risk",
    "next_action",
    "do_not_capture_images",
    "rights_review_gate",
    "notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def clean(value: str, max_chars: int = 260) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rsplit(" ", 1)[0] + "..."


def origin(url: str) -> str:
    parts = urlsplit(url)
    if not parts.scheme or not parts.netloc:
        return url
    return urlunsplit((parts.scheme, parts.netloc, "/", "", ""))


def load_joined() -> list[dict[str, str]]:
    candidates = {row["candidate_id"]: row for row in read_csv(CANDIDATES)}
    rows: list[dict[str, str]] = []
    for probe in read_csv(PROBE):
        candidate = candidates.get(probe["candidate_id"], {})
        item = {**candidate, **probe}
        item["candidate_priority"] = candidate.get("priority", "")
        item["candidate_notes"] = candidate.get("notes", "")
        rows.append(item)
    return rows


def protocol_lane(row: dict[str, str]) -> str:
    haystack = " ".join(
        [
            row.get("detected_protocols", ""),
            row.get("protocol_family", ""),
            row.get("adapter_hint", ""),
            row.get("recommended_adapter", ""),
        ]
    ).lower()
    if "contentdm" in haystack:
        return "CONTENTdm source metadata"
    if "kramerius" in haystack:
        return "Kramerius / IIIF source metadata"
    if "iiif" in haystack:
        return "IIIF/source-viewer metadata"
    if "wordpress" in haystack:
        return "WordPress REST / HTML"
    if "rss" in haystack or "atom" in haystack:
        return "RSS/Atom source feed"
    if "json-ld" in haystack or "jsonld" in haystack:
        return "JSON-LD page metadata"
    if "dspace" in haystack:
        return "DSpace repository metadata"
    if "omeka" in haystack:
        return "Omeka source metadata"
    if "oai" in haystack:
        return "OAI-PMH metadata"
    if "pdf" in haystack:
        return "PDF text/link extraction"
    if "graphql" in haystack:
        return "GraphQL schema probe"
    if "static" in haystack or "headless" in haystack:
        return "Static JS/headless metadata"
    if "search" in haystack:
        return "Search interface/manual source registry"
    return "HTML/manual source registry"


def adapter_type(row: dict[str, str]) -> str:
    lane = protocol_lane(row)
    if lane == "WordPress REST / HTML":
        return "wordpress_rest_or_html_source_adapter"
    if lane == "RSS/Atom source feed":
        return "rss_atom_source_adapter"
    if lane == "JSON-LD page metadata":
        return "html_jsonld_source_adapter"
    if lane == "IIIF/source-viewer metadata":
        return "iiif_manifest_metadata_adapter"
    if lane == "CONTENTdm source metadata":
        return "contentdm_metadata_adapter"
    if lane == "Kramerius / IIIF source metadata":
        return "kramerius_metadata_adapter"
    if lane == "DSpace repository metadata":
        return "dspace_oai_or_rest_metadata_adapter"
    if lane == "Omeka source metadata":
        return "omeka_metadata_adapter"
    if lane == "OAI-PMH metadata":
        return "oai_pmh_metadata_adapter"
    if lane == "PDF text/link extraction":
        return "pdf_text_link_adapter"
    if lane == "GraphQL schema probe":
        return "graphql_schema_probe_then_metadata_adapter"
    if lane == "Static JS/headless metadata":
        return "headless_metadata_probe_only"
    if lane == "Search interface/manual source registry":
        return "manual_search_source_registry"
    return "html_source_probe_then_manual_rules"


def lane_rank(lane: str) -> int:
    order = [
        "WordPress REST / HTML",
        "RSS/Atom source feed",
        "JSON-LD page metadata",
        "IIIF/source-viewer metadata",
        "CONTENTdm source metadata",
        "Kramerius / IIIF source metadata",
        "OAI-PMH metadata",
        "DSpace repository metadata",
        "Omeka source metadata",
        "Static JS/headless metadata",
        "GraphQL schema probe",
        "PDF text/link extraction",
        "Search interface/manual source registry",
        "HTML/manual source registry",
    ]
    return order.index(lane) if lane in order else len(order)


def p1_protocol_queue(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    p1 = [row for row in rows if row.get("capture_priority_next", "").startswith("P1")]
    p1.sort(
        key=lambda row: (
            lane_rank(protocol_lane(row)),
            -REGION_WEIGHTS.get(row.get("macro_region", ""), 2),
            row.get("source_name", ""),
        )
    )
    out: list[dict[str, str]] = []
    for index, row in enumerate(p1, start=1):
        lane = protocol_lane(row)
        out.append(
            {
                "queue_id": f"P1V2-{index:03d}",
                "candidate_id": row.get("candidate_id", ""),
                "source_name": row.get("source_name", ""),
                "macro_region": row.get("macro_region", ""),
                "subregion": row.get("subregion", ""),
                "country_or_region": row.get("country_or_region", ""),
                "source_class": row.get("source_class", ""),
                "protocol_lane": lane,
                "adapter_type": adapter_type(row),
                "detected_protocols": row.get("detected_protocols", ""),
                "adapter_hint": row.get("adapter_hint", ""),
                "capture_priority_next": row.get("capture_priority_next", ""),
                "candidate_priority": row.get("candidate_priority", ""),
                "recommended_text_policy_next": row.get("recommended_text_policy_next", ""),
                "recommended_image_policy_next": row.get("recommended_image_policy_next", ""),
                "rights_risk": row.get("rights_risk", ""),
                "next_action": next_action_for_lane(row, lane),
                "image_capture_boundary": IMAGE_BOUNDARY,
                "source_url": row.get("url", ""),
                "final_url": row.get("final_url", ""),
                "notes": clean(row.get("notes", "")),
            }
        )
    return out


def next_action_for_lane(row: dict[str, str], lane: str) -> str:
    if "discovery" in row.get("adapter_hint", "").lower():
        return "keep as discovery lead; resolve original source before item records"
    if lane == "WordPress REST / HTML":
        return "probe public REST/feed endpoints; extract titles, dates, source links, tags, citations, rights text only"
    if lane == "RSS/Atom source feed":
        return "read feed metadata and canonical links; enrich source registry without media ingestion"
    if lane == "JSON-LD page metadata":
        return "extract JSON-LD title/description/date/source fields; ignore image objects as rights evidence"
    if "IIIF" in lane or "CONTENTdm" in lane or "Kramerius" in lane:
        return "map manifests/viewers as source-hosted display routes; no reuse claim without item-level rights"
    if lane == "PDF text/link extraction":
        return "extract bibliographic text and source links only; no page-image possession"
    if lane == "Static JS/headless metadata":
        return "run headless metadata probe for rendered title, description, canonical URL, and rights text"
    if lane == "GraphQL schema probe":
        return "inspect public schema/network metadata before any item-level adapter"
    if "Search interface" in lane:
        return "write manual source-registry record and identify stable search/API endpoint"
    return "extract source-level metadata and rights evidence only"


def region_priorities(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get("macro_region", "")].append(row)

    out: list[dict[str, str]] = []
    for region, items in groups.items():
        status = Counter(row.get("probe_status", "") for row in items)
        priority = Counter(row.get("capture_priority_next", "") for row in items)
        candidate_priority = Counter(row.get("candidate_priority", "") for row in items)
        protocols = Counter()
        for row in items:
            for protocol in row.get("detected_protocols", "").split(";"):
                if protocol:
                    protocols[protocol] += 1
        score = (
            REGION_WEIGHTS.get(region, 2) * 10
            + priority["P1 adapter build"] * 3
            + priority["P1 text/source enrichment"] * 2
            + status["failed"]
            + status["http_error"]
            + candidate_priority["P0"]
        )
        out.append(
            {
                "rank": "",
                "macro_region": region,
                "total_candidates": str(len(items)),
                "ok": str(status["ok"]),
                "failed": str(status["failed"]),
                "http_error": str(status["http_error"]),
                "p1_adapter_build": str(priority["P1 adapter build"]),
                "p1_text_source_enrichment": str(priority["P1 text/source enrichment"]),
                "p2_retry_manual_verification": str(priority["P2 retry/manual verification"]),
                "p2_discovery_lead_queue": str(priority["P2 discovery lead queue"]),
                "p2_manual_source_review": str(priority["P2 manual source review"]),
                "detected_protocol_count": str(sum(protocols.values())),
                "candidate_p0": str(candidate_priority["P0"]),
                "candidate_p1": str(candidate_priority["P1"]),
                "candidate_p2": str(candidate_priority["P2"]),
                "candidate_p3": str(candidate_priority["P3"]),
                "priority_score": str(score),
                "next_action": region_next_action(region, priority, status),
                "image_capture_boundary": IMAGE_BOUNDARY,
            }
        )
    out.sort(key=lambda row: (-int(row["priority_score"]), row["macro_region"]))
    for index, row in enumerate(out, start=1):
        row["rank"] = str(index)
    return out


def region_next_action(region: str, priority: Counter[str], status: Counter[str]) -> str:
    if priority["P1 adapter build"] >= priority["P1 text/source enrichment"]:
        action = "start with protocol-family adapter rows"
    else:
        action = "start with text/source enrichment rows"
    if status["failed"] + status["http_error"] >= 4:
        action += "; run alternate endpoint review for failed sources"
    if region in {"Africa", "MENA", "South Asia", "Southeast Asia", "Oceania / Indigenous"}:
        action += "; keep cultural sensitivity and source relationship review explicit"
    return action


def failure_family(row: dict[str, str]) -> str:
    reason = " ".join([row.get("failure_reason", ""), row.get("http_status", "")]).lower()
    if "certificate" in reason or "ssl" in reason:
        return "ssl_certificate"
    if "nodename" in reason or "dns" in reason or "servname" in reason:
        return "dns_or_domain"
    if "429" in reason:
        return "rate_limited_429"
    if "403" in reason:
        return "forbidden_403"
    if "404" in reason:
        return "not_found_404"
    if "401" in reason:
        return "auth_required_401"
    if "timeout" in reason or "timed out" in reason:
        return "timeout"
    if "reset" in reason:
        return "connection_reset"
    return "manual_retry_other"


def alternate_endpoint_hint(row: dict[str, str]) -> str:
    url = row.get("url", "")
    base = origin(url)
    family = failure_family(row)
    claimed = row.get("protocol_family", "").lower()
    hints: list[str] = []
    if family == "not_found_404":
        hints.append(f"try source root {base}")
    if "wordpress" in claimed:
        hints.extend([f"{base}wp-json/", f"{base}feed/"])
    if "rss" in claimed or "atom" in claimed:
        hints.append(f"{base}feed/")
    if "iiif" in claimed:
        hints.append("look for collection search, IIIF manifest endpoint, or provider API from source root")
    if "oai" in claimed:
        hints.append("look for OAI-PMH Identify/ListRecords endpoint from source documentation")
    if family in {"forbidden_403", "rate_limited_429", "auth_required_401"}:
        hints.append("manual browser/source documentation review; respect access controls and terms")
    if family == "ssl_certificate":
        hints.append("manual browser check and canonical-domain verification before retry")
    if family == "dns_or_domain":
        hints.append("verify current domain, moved project page, or institutional successor page")
    if not hints:
        hints.append("manual source-registry review and alternate endpoint search")
    return " | ".join(dict.fromkeys(hints))


def recommended_retry_route(row: dict[str, str]) -> str:
    family = failure_family(row)
    if family in {"forbidden_403", "auth_required_401", "rate_limited_429"}:
        return "manual_source_registry_record; do not bypass access controls"
    if family == "not_found_404":
        return "canonical_url_recheck_then_source_root_probe"
    if family == "ssl_certificate":
        return "canonical_domain_and_certificate_review_then_retry"
    if family == "dns_or_domain":
        return "domain_successor_or_archival_source_note"
    if family == "timeout":
        return "slow_retry_with_lower_rate_or_manual_browser_check"
    if family == "connection_reset":
        return "retry_later_or_manual_browser_source_check"
    return "manual_source_registry_review"


def retry_registry(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    retry = [
        row
        for row in rows
        if row.get("probe_status") != "ok"
        or row.get("capture_priority_next") == "P2 retry/manual verification"
    ]
    retry.sort(
        key=lambda row: (
            -REGION_WEIGHTS.get(row.get("macro_region", ""), 2),
            row.get("probe_status", ""),
            failure_family(row),
            row.get("source_name", ""),
        )
    )
    out: list[dict[str, str]] = []
    for index, row in enumerate(retry, start=1):
        out.append(
            {
                "retry_id": f"RTV2-{index:03d}",
                "candidate_id": row.get("candidate_id", ""),
                "source_name": row.get("source_name", ""),
                "macro_region": row.get("macro_region", ""),
                "subregion": row.get("subregion", ""),
                "country_or_region": row.get("country_or_region", ""),
                "source_class": row.get("source_class", ""),
                "source_url": row.get("url", ""),
                "final_url": row.get("final_url", ""),
                "http_status": row.get("http_status", ""),
                "probe_status": row.get("probe_status", ""),
                "failure_family": failure_family(row),
                "failure_reason": clean(row.get("failure_reason", "")),
                "candidate_priority": row.get("candidate_priority", ""),
                "capture_priority_next": row.get("capture_priority_next", ""),
                "alternate_endpoint_hint": alternate_endpoint_hint(row),
                "recommended_retry_route": recommended_retry_route(row),
                "rights_boundary": IMAGE_BOUNDARY,
                "notes": clean(row.get("notes", "")),
            }
        )
    return out


def queue_priority(row: dict[str, str]) -> str:
    if row.get("capture_priority_next") == "P1 adapter build":
        return "P1A_protocol_adapter"
    if row.get("capture_priority_next") == "P1 text/source enrichment":
        return "P1B_text_source_enrichment"
    if row.get("capture_priority_next") == "P2 discovery lead queue":
        return "P2_discovery_source_resolution"
    if row.get("capture_priority_next") == "P2 retry/manual verification":
        return "P2_retry_or_alternate_endpoint"
    return "P2_manual_source_review"


def adapter_queue(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    included = [
        row
        for row in rows
        if row.get("capture_priority_next", "").startswith("P1")
        or row.get("capture_priority_next", "").startswith("P2")
    ]
    included.sort(
        key=lambda row: (
            queue_priority(row),
            lane_rank(protocol_lane(row)),
            -REGION_WEIGHTS.get(row.get("macro_region", ""), 2),
            row.get("source_name", ""),
        )
    )
    out: list[dict[str, str]] = []
    for index, row in enumerate(included, start=1):
        q_priority = queue_priority(row)
        out.append(
            {
                "queue_id": f"AQV2-{index:03d}",
                "candidate_id": row.get("candidate_id", ""),
                "source_name": row.get("source_name", ""),
                "macro_region": row.get("macro_region", ""),
                "subregion": row.get("subregion", ""),
                "country_or_region": row.get("country_or_region", ""),
                "source_url": row.get("url", ""),
                "protocol_lane": protocol_lane(row),
                "adapter_type": adapter_type(row),
                "queue_priority": q_priority,
                "queue_status": "ready" if q_priority.startswith("P1") else "review_first",
                "candidate_priority": row.get("candidate_priority", ""),
                "probe_status": row.get("probe_status", ""),
                "capture_priority_next": row.get("capture_priority_next", ""),
                "rights_risk": row.get("rights_risk", ""),
                "next_action": next_action_for_lane(row, protocol_lane(row))
                if q_priority.startswith("P1")
                else recommended_retry_route(row),
                "do_not_capture_images": "true",
                "rights_review_gate": "item_level_rights_required_before_IMG01_or_IMG03",
                "notes": clean(row.get("notes", "")),
            }
        )
    return out


def write_report(
    p1_rows: list[dict[str, str]],
    region_rows: list[dict[str, str]],
    retry_rows: list[dict[str, str]],
    adapter_rows: list[dict[str, str]],
) -> None:
    lane_counts = Counter(row["protocol_lane"] for row in p1_rows)
    region_top = region_rows[:8]
    retry_counts = Counter(row["failure_family"] for row in retry_rows)
    queue_counts = Counter(row["queue_priority"] for row in adapter_rows)
    lines = [
        "# Contemporary Source Scan Follow-up 1990-2026 v2",
        "",
        "Derived follow-up queues from the v2 source scan. This document is source planning only: no pages were fetched, no raw probe bodies were read, no image files were downloaded, and no image state was upgraded.",
        "",
        "## Safety Rules",
        "",
        "- Source discovery only until item-level source and rights review exists.",
        "- Do not capture image binaries from these queues.",
        "- IMG01 and IMG03 require authoritative item-level source evidence; heuristic, platform, ToS, LLM, IIIF, OpenGraph, or JSON-LD image signals are not enough.",
        "- IMG04 remains a real text/no-image-frame state, not a parser-failure fallback.",
        "- Priority is internal triage only.",
        "",
        "## P1 Protocol Queue",
        "",
        f"- Rows: {len(p1_rows)}",
    ]
    for lane, count in lane_counts.most_common():
        lines.append(f"- {lane}: {count}")
    lines.extend(["", "## Regional Priorities", ""])
    for row in region_top:
        lines.append(
            f"- {row['rank']}. {row['macro_region']}: score {row['priority_score']}; "
            f"total {row['total_candidates']}; ok {row['ok']}; P1 adapter "
            f"{row['p1_adapter_build']}; P1 text {row['p1_text_source_enrichment']}"
        )
    lines.extend(["", "## Retry Registry", "", f"- Rows: {len(retry_rows)}"])
    for family, count in retry_counts.most_common():
        lines.append(f"- {family}: {count}")
    lines.extend(["", "## Adapter Queue", "", f"- Rows: {len(adapter_rows)}"])
    for priority, count in queue_counts.most_common():
        lines.append(f"- {priority}: {count}")
    lines.extend(
        [
            "",
            "## Next Implementation Order",
            "",
            "1. Build WordPress/RSS/JSON-LD source adapters for text, canonical source links, tags, dates, and rights text.",
            "2. Build IIIF/CONTENTdm/Kramerius/DSpace metadata adapters as source-hosted display-route probes only.",
            "3. Run headless/static metadata probes for high-priority regional sources after source terms review.",
            "4. Resolve retry rows through canonical endpoint checks or manual source-registry notes without bypassing access controls.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--step",
        choices=["p1", "regions", "retry", "adapter", "all"],
        default="all",
        help="Which follow-up output to write.",
    )
    args = parser.parse_args()

    rows = load_joined()
    p1_rows = p1_protocol_queue(rows)
    region_rows = region_priorities(rows)
    retry_rows = retry_registry(rows)
    adapter_rows = adapter_queue(rows)

    if args.step in {"p1", "all"}:
        write_csv(P1_QUEUE, P1_FIELDNAMES, p1_rows)
        print(f"Wrote {len(p1_rows)} rows to {P1_QUEUE.relative_to(ROOT)}")
    if args.step in {"regions", "all"}:
        write_csv(REGION_PRIORITIES, REGION_FIELDNAMES, region_rows)
        print(f"Wrote {len(region_rows)} rows to {REGION_PRIORITIES.relative_to(ROOT)}")
    if args.step in {"retry", "all"}:
        write_csv(RETRY_REGISTRY, RETRY_FIELDNAMES, retry_rows)
        print(f"Wrote {len(retry_rows)} rows to {RETRY_REGISTRY.relative_to(ROOT)}")
    if args.step in {"adapter", "all"}:
        write_csv(ADAPTER_QUEUE, ADAPTER_FIELDNAMES, adapter_rows)
        write_report(p1_rows, region_rows, retry_rows, adapter_rows)
        print(f"Wrote {len(adapter_rows)} rows to {ADAPTER_QUEUE.relative_to(ROOT)}")
        print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
