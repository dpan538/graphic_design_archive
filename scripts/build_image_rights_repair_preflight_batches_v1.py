#!/usr/bin/env python3
"""Build source-family preflight batches for image-rights repair.

This is an execution planning layer. It does not fetch remote records, download
images, mutate surfaces, or upgrade IMG01/IMG03. Each batch states the item-level
evidence needed before a future repair pass can change image state.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from lib.archive_audit import DATA, DOCS, ROOT, clean, read_csv, write_csv


CANDIDATES = DATA / "image_rights_repair_candidates_v1.csv"
SOURCE_PRIORITIES = DATA / "image_rights_repair_source_priorities_v1.csv"
OUTPUT_BATCHES = DATA / "image_rights_repair_preflight_batches_v1.csv"
OUTPUT_REPORT = DOCS / "IMAGE_RIGHTS_REPAIR_PREFLIGHT_BATCHES_v1.md"

BATCH_FIELDS = [
    "batch_id",
    "priority",
    "source_name",
    "dominant_repair_family",
    "candidate_objects",
    "batch_candidate_limit",
    "estimated_weighted_gap_points",
    "source_visible_gap_objects",
    "verified_open_gap_objects",
    "image_state_mix",
    "source_family_route",
    "item_level_evidence_contract",
    "raw_payload_policy",
    "automatic_upgrade_allowed",
    "network_required_for_execution",
    "sample_surface_ids",
]

SOURCE_ROUTES = [
    ("Cooper Hewitt", "cooper_hewitt_graphql_object_review"),
    ("Wellcome", "wellcome_catalogue_license_review"),
    ("Library of Congress", "loc_item_json_rights_advisory_review"),
    ("Georgia State University", "contentdm_item_rights_review"),
    ("Art Institute of Chicago", "aic_public_domain_image_id_review"),
    ("Internet Archive", "internet_archive_metadata_rights_review"),
    ("V&A", "vam_collections_image_permission_review"),
    ("Te Papa", "te_papa_collections_rights_review"),
    ("DigitalNZ", "digitalnz_aggregated_source_rights_review"),
    ("NAIDOC", "naidoc_source_page_rights_review"),
    ("Princeton", "princeton_figgy_manifest_rights_review"),
    ("The Met", "met_collection_object_rights_review"),
]

EVIDENCE_CONTRACTS = {
    "img02_open_rights_review": "Confirm item-level open-license/public-domain evidence on the source record before any IMG03 promotion.",
    "img01_item_image_and_rights_review": "Capture item-level image and rights evidence; thumbnail/search-result evidence is insufficient.",
    "img00_source_visible_repair": "Find a source-visible item image plus rights basis, or keep the object as a source-visible blocker.",
    "img04_visual_record_search": "Search for a source-visible visual record; keep IMG04 only with explicit no-image rationale.",
    "img04_text_state_review": "Confirm the record is genuinely text/authority/context-only and should remain IMG04.",
    "img03_rights_review_flag_check": "Confirm existing IMG03 has item-level open/public-domain evidence before setting rightsReviewed.",
}


def source_route(source_name: str) -> str:
    for marker, route in SOURCE_ROUTES:
        if marker.lower() in source_name.lower():
            return route
    return "generic_item_source_rights_review"


def priority(row: dict[str, str]) -> str:
    gap = float(row.get("weighted_gap_points", "0") or 0)
    source_visible = int(row.get("source_visible_gap_objects", "0") or 0)
    if gap >= 30 or source_visible >= 20:
        return "P0"
    if gap >= 15 or int(row.get("candidate_objects", "0") or 0) >= 30:
        return "P1"
    return "P2"


def dominant_action(source_name: str, candidates_by_source: dict[str, list[dict[str, str]]]) -> str:
    counter = Counter(row.get("repair_family", "") for row in candidates_by_source.get(source_name, []))
    return counter.most_common(1)[0][0] if counter else ""


def state_mix(source_name: str, candidates_by_source: dict[str, list[dict[str, str]]]) -> str:
    counter = Counter(row.get("best_image_state", "") for row in candidates_by_source.get(source_name, []))
    return "; ".join(f"{state}:{count}" for state, count in counter.most_common() if state)


def batch_limit(row: dict[str, str]) -> int:
    total = int(row.get("candidate_objects", "0") or 0)
    if priority(row) == "P0":
        return min(total, 150)
    if priority(row) == "P1":
        return min(total, 75)
    return min(total, 30)


def build_rows() -> list[dict[str, str]]:
    candidates = read_csv(CANDIDATES)
    candidates_by_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidates:
        candidates_by_source[row.get("source_name", "")].append(row)

    rows = []
    for source in read_csv(SOURCE_PRIORITIES):
        source_name = source.get("source_name", "")
        action = dominant_action(source_name, candidates_by_source)
        rows.append(
            {
                "batch_id": "",
                "priority": priority(source),
                "source_name": source_name,
                "dominant_repair_family": action,
                "candidate_objects": source.get("candidate_objects", ""),
                "batch_candidate_limit": str(batch_limit(source)),
                "estimated_weighted_gap_points": source.get("weighted_gap_points", ""),
                "source_visible_gap_objects": source.get("source_visible_gap_objects", ""),
                "verified_open_gap_objects": source.get("verified_open_gap_objects", ""),
                "image_state_mix": state_mix(source_name, candidates_by_source),
                "source_family_route": source_route(source_name),
                "item_level_evidence_contract": EVIDENCE_CONTRACTS.get(action, "Review item-level source and rights evidence before changing image state."),
                "raw_payload_policy": "metadata/source text/rights evidence only; no image binary download; redact token-like URL params before commit",
                "automatic_upgrade_allowed": "false",
                "network_required_for_execution": "true",
                "sample_surface_ids": source.get("example_surface_ids", ""),
            }
        )

    rows.sort(
        key=lambda row: (
            {"P0": 0, "P1": 1, "P2": 2}.get(row["priority"], 9),
            -float(row["estimated_weighted_gap_points"] or 0),
            row["source_name"],
        )
    )
    for idx, row in enumerate(rows, start=1):
        row["batch_id"] = f"IMG-RIGHTS-BATCH-{idx:04d}"
    return rows


def write_report(rows: list[dict[str, str]]) -> None:
    priority_counts = Counter(row["priority"] for row in rows)
    action_counts = Counter(row["dominant_repair_family"] for row in rows)
    p0_rows = [row for row in rows if row["priority"] == "P0"]
    p1_rows = [row for row in rows if row["priority"] == "P1"]
    estimated_p0_points = sum(float(row["estimated_weighted_gap_points"] or 0) for row in p0_rows)
    estimated_p1_points = sum(float(row["estimated_weighted_gap_points"] or 0) for row in p1_rows)
    lines = [
        "# Image Rights Repair Preflight Batches v1",
        "",
        "This preflight splits the image-rights repair queue into source-family execution batches. It does not fetch records, download images, mutate surfaces, or upgrade IMG01/IMG03.",
        "",
        "## Safety Contract",
        "",
        "- `automatic_upgrade_allowed=false` for every batch.",
        "- Any future IMG03 repair requires item-level open-license or public-domain evidence from the source record.",
        "- Source discovery and probe output should store metadata, source text, rights evidence, and source links only.",
        "- Raw payloads, if produced in a later execution run, must be redacted and audited before commit.",
        "",
        "## Batch Summary",
        "",
        f"- total source-family batches: {len(rows)}",
        f"- P0 batches: {priority_counts.get('P0', 0)}",
        f"- P1 batches: {priority_counts.get('P1', 0)}",
        f"- P2 batches: {priority_counts.get('P2', 0)}",
        f"- estimated P0 weighted-gap points: {estimated_p0_points:.2f}",
        f"- estimated P0+P1 weighted-gap points: {estimated_p0_points + estimated_p1_points:.2f}",
        "",
        "## Repair Families",
        "",
    ]
    for key, value in action_counts.most_common():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## P0 Execution Order", ""])
    for row in p0_rows:
        lines.append(
            f"- `{row['batch_id']}` {row['source_name']}: {row['candidate_objects']} candidates; "
            f"{row['estimated_weighted_gap_points']} weighted points; {row['dominant_repair_family']}"
        )
    lines.extend(["", "## Output File", "", f"- `{OUTPUT_BATCHES.relative_to(ROOT)}`"])
    OUTPUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(OUTPUT_BATCHES, rows, BATCH_FIELDS)
    write_report(rows)
    print(f"rights_repair_batches={len(rows)}")
    print(f"wrote {OUTPUT_BATCHES.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
