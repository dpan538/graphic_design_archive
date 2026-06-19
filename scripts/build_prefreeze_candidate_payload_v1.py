#!/usr/bin/env python3
"""Build a candidate public-surface payload without touching release payloads.

This is a pre-freeze evaluation helper. It reads every capture records CSV,
applies the pre-freeze P0 exclusion gate, globally dedupes, and writes one
candidate JSON for audits. It does not write frontend mirrors, official payloads,
shards, raw files, or image binaries.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import rebuild_public_surfaces_from_records as rebuild
from normalize_public_surfaces import normalize_payload


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GENERATED = ROOT / "generated"
DOCS = ROOT / "docs" / "capture"

OUT_PAYLOAD = GENERATED / "public_surfaces_prefreeze_candidate_v1.json"
OUT_SUMMARY = DATA / "prefreeze_candidate_payload_build_v1.csv"
OUT_REPORT = DOCS / "PREFREEZE_CANDIDATE_PAYLOAD_BUILD_v1.md"

SUMMARY_FIELDS = ["metric", "value", "notes"]


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def capture_record_files() -> list[Path]:
    """Use the full local capture pool, including batches not in release rebuild."""
    return sorted(DATA.glob("capture_batch_*_records.csv"))


def candidate_rows() -> tuple[list[dict[str, str]], Counter[str], dict[str, int]]:
    rows: list[dict[str, str]] = []
    input_stats: Counter[str] = Counter()
    exclusions = rebuild.prefreeze_exclusion_lookup()
    skipped_by_exclusion = 0
    file_count = 0
    raw_rows = 0

    for path in capture_record_files():
        file_count += 1
        input_rows = rebuild.read_rows(path)
        raw_rows += len(input_rows)
        excluded_ids = exclusions.get(path.name, set())
        if excluded_ids:
            before = len(input_rows)
            input_rows = [row for row in input_rows if row.get("capture_id", "") not in excluded_ids]
            skipped_by_exclusion += before - len(input_rows)
        for row in input_rows:
            row["_source_file"] = path.name
        input_stats[path.name] = len(input_rows)
        rows.extend(input_rows)

    rows, geo_overrides_applied = rebuild.apply_prefreeze_geo_overrides(rows)
    rows, role_overrides_applied = rebuild.apply_prefreeze_role_overrides(rows)
    normalized = [
        rebuild.normalize_public_date_fields(rebuild.fill_enrichment_defaults(dict(row)))
        for row in rows
    ]
    deduped = rebuild.dedupe_rows(normalized)
    deduped.sort(key=lambda row: (rebuild.row_sort_year(row), row.get("source_title", "")))
    counters = {
        "input_files": file_count,
        "raw_input_rows": raw_rows,
        "skipped_by_p0_exclusion": skipped_by_exclusion,
        "rows_after_exclusion": len(rows),
        "geo_overrides_applied": geo_overrides_applied,
        "role_overrides_applied": role_overrides_applied,
        "deduped_candidate_rows": len(deduped),
        "dedupe_removed_rows": len(rows) - len(deduped),
    }
    return deduped, input_stats, counters


def build_payload(rows: list[dict[str, str]]) -> dict:
    payload = rebuild.mc.build_public_payload(rows)
    payload = rebuild.enhance_payload(payload, rows)
    payload = normalize_payload(payload)
    payload = rebuild.normalize_public_surface_visible_text(payload)
    payload = rebuild.normalize_public_folder_metadata(payload)
    payload = rebuild.attach_structural_collections(payload)
    payload = rebuild.build_research_dossiers(payload)
    payload.setdefault("meta", {})
    payload["meta"].update(
        {
            "status": "prefreeze_candidate",
            "candidatePayload": True,
            "officialReleasePayload": False,
            "source": "all capture_batch_*_records.csv with prefreeze P0 exclusions",
            "noImageDownload": True,
            "rightsUpgradePolicy": "No heuristic/LLM/TOS/platform image-state or rights upgrades.",
        }
    )
    return payload


def write_report(summary_rows: list[dict[str, str]], input_stats: Counter[str]) -> None:
    lines = [
        "# Prefreeze Candidate Payload Build v1",
        "",
        "Scope: sandbox candidate build for source and gate evaluation. It does not overwrite the official public payload or frontend data.",
        "",
        "## Summary",
        "",
    ]
    for row in summary_rows:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Largest Included Capture Inputs", ""])
    for name, count in input_stats.most_common(20):
        lines.append(f"- {name}: {count}")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- No image files were downloaded.",
            "- IMG01/IMG03 were not upgraded by heuristic, LLM, TOS, or platform signals.",
            "- Impact/source priority remains an internal triage signal only.",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows, input_stats, counters = candidate_rows()
    payload = build_payload(rows)
    OUT_PAYLOAD.parent.mkdir(parents=True, exist_ok=True)
    OUT_PAYLOAD.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

    surfaces = payload.get("surfaces", [])
    dossiers = payload.get("researchDossiers", [])
    states = Counter(surface.get("image", {}).get("state", "IMG00") for surface in surfaces)
    source_names = {str(surface.get("sourceName") or "").strip() for surface in surfaces if surface.get("sourceName")}
    summary_rows = [
        {"metric": "candidate_payload", "value": str(OUT_PAYLOAD.relative_to(ROOT)), "notes": "Local evaluation payload path."},
        {"metric": "input_files", "value": str(counters["input_files"]), "notes": "All capture record CSV inputs discovered."},
        {"metric": "raw_input_rows", "value": str(counters["raw_input_rows"]), "notes": "Rows before P0 exclusion and dedupe."},
        {"metric": "skipped_by_p0_exclusion", "value": str(counters["skipped_by_p0_exclusion"]), "notes": "Rows blocked by pre-freeze cleaning gate."},
        {"metric": "rows_after_exclusion", "value": str(counters["rows_after_exclusion"]), "notes": "Rows eligible for global dedupe."},
        {"metric": "geo_overrides_applied", "value": str(counters["geo_overrides_applied"]), "notes": "Audited pre-freeze geography repairs applied in memory."},
        {"metric": "role_overrides_applied", "value": str(counters["role_overrides_applied"]), "notes": "Audited pre-freeze card/subsheet demotions applied in memory."},
        {"metric": "deduped_candidate_rows", "value": str(counters["deduped_candidate_rows"]), "notes": "Rows passed to payload builder."},
        {"metric": "dedupe_removed_rows", "value": str(counters["dedupe_removed_rows"]), "notes": "Duplicate rows removed before surface build."},
        {"metric": "candidate_surfaces", "value": str(len(surfaces)), "notes": "Surfaces generated in candidate payload."},
        {"metric": "candidate_active_public_sources", "value": str(len(source_names)), "notes": "Distinct source names in candidate payload."},
        {"metric": "candidate_research_dossiers", "value": str(len(dossiers)), "notes": "Generated research dossier anchors."},
    ]
    for state, count in sorted(states.items()):
        summary_rows.append({"metric": f"candidate_image_state:{state}", "value": str(count), "notes": "Candidate surface image state distribution."})
    write_csv(OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_report(summary_rows, input_stats)
    print(f"candidate_surfaces={len(surfaces)}")
    print(f"candidate_active_public_sources={len(source_names)}")
    print(f"wrote {OUT_PAYLOAD.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
