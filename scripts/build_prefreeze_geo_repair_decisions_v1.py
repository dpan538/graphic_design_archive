#!/usr/bin/env python3
"""Build auditable geography repair decisions for the pre-freeze candidate.

The script is intentionally non-destructive. It reads the unresolved-region
queue produced by the candidate promotion blocker audit and emits:

- a full decision table for review,
- a narrow override table used by candidate/public rebuild code,
- a compact summary CSV and Markdown report.

It does not edit capture records, download images, or upgrade rights/image
states. Geography repair is only a folder/source coverage normalization step.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

QUEUE = DATA / "prefreeze_candidate_geo_repair_queue_v1.csv"
GEOGRAPHIES = DATA / "geographies.csv"
REGIONS = DATA / "regions.csv"

OUT_DECISIONS = DATA / "prefreeze_geo_repair_decisions_v1.csv"
OUT_OVERRIDES = DATA / "prefreeze_geo_repair_overrides_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_geo_repair_summary_v1.csv"
OUT_REPORT = DOCS / "PREFREEZE_GEO_REPAIR_DECISIONS_v1.md"

DECISION_FIELDS = [
    "source_file",
    "capture_id",
    "surface_id",
    "year",
    "current_region",
    "place_text",
    "source_subjects",
    "source_name",
    "title",
    "source_url",
    "suggested_region_label",
    "suggested_region_ids",
    "suggested_geo_ids",
    "decision_type",
    "confidence",
    "evidence_field",
    "evidence_value",
    "guardrail",
]

OVERRIDE_FIELDS = [
    "source_file",
    "capture_id",
    "surface_id",
    "region_folder",
    "region_ids",
    "geo_ids",
    "source_place_text",
    "decision_type",
    "confidence",
    "repair_basis",
    "source_name",
    "title",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]

GLOBALISH = {
    "global",
    "global / release gate expansion",
    "global / controlled expansion",
    "global / period balance",
    "global web / transnational",
    "post-1990 international",
    "transnational",
}

MACRO_PATHS = {
    "africa": ("Africa", "REG014", "GEO061"),
    "middle east and north africa": ("Middle East and North Africa", "REG013", "GEO055"),
    "eastern europe": ("Eastern Europe, Balkans, and socialist contexts", "REG002", "GEO015"),
    "eastern europe / caucasus": ("Caucasus", "REG002", "GEO078"),
    "southeast asia": ("Southeast Asia", "REG011", "GEO043"),
    "south asia": ("South Asia", "REG012", "GEO050"),
    "east asia": ("East Asia", "REG007", "GEO035"),
    "oceania": ("Oceania and Pacific", "REG015", "GEO068"),
    "oceania / pacific": ("Pacific Islands contexts", "REG015", "GEO071"),
    "latin america": ("Latin America and the Caribbean", "REG004", "GEO028"),
    "latin america and the caribbean": ("Latin America and the Caribbean", "REG004", "GEO028"),
    "north america": ("North America", "REG003", "GEO024"),
    "western and central europe": ("Western and Central Europe", "REG001", "GEO002"),
}

ALIASES = {
    "china": "Mainland China",
    "czech republic": "Czech and Slovak contexts",
    "czechia": "Czech and Slovak contexts",
    "czechia slovakia": "Czech and Slovak contexts",
    "hong kong": "Hong Kong",
    "korea": "Korean Peninsula",
    "mena": "Middle East and North Africa",
    "new zealand": "Aotearoa New Zealand",
    "palestine": "Palestinian territories and diaspora",
    "russia": "Russia / USSR contexts",
    "union of soviet socialist republics": "Russia / USSR contexts",
    "ussr": "Russia / USSR contexts",
    "soviet union": "Russia / USSR contexts",
    "usa": "United States",
    "u s a": "United States",
    "united states of america": "United States",
}


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def load_geo_index() -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for row in read_csv(GEOGRAPHIES):
        name = clean(row.get("name"))
        if not name:
            continue
        index[key(name)] = row
    for alias, canonical in ALIASES.items():
        target = index.get(key(canonical))
        if target:
            index[key(alias)] = target
    return index


def controlled_decision(
    row: dict[str, str],
    geo: dict[str, str],
    evidence_field: str,
    evidence_value: str,
    confidence: str = "high",
) -> dict[str, str]:
    label = clean(geo.get("name"))
    return {
        **row,
        "suggested_region_label": label,
        "suggested_region_ids": clean(geo.get("region_id")),
        "suggested_geo_ids": clean(geo.get("geo_id")),
        "decision_type": "auto_apply_candidate",
        "confidence": confidence,
        "evidence_field": evidence_field,
        "evidence_value": evidence_value,
        "guardrail": "Exact controlled geography match; geography only, no rights or image-state upgrade.",
    }


def macro_or_specific_decision(
    row: dict[str, str],
    label: str,
    region_id: str,
    geo_id: str,
    evidence_field: str,
    evidence_value: str,
    confidence: str,
    decision_type: str,
    guardrail: str,
) -> dict[str, str]:
    return {
        **row,
        "suggested_region_label": label,
        "suggested_region_ids": region_id,
        "suggested_geo_ids": geo_id,
        "decision_type": decision_type,
        "confidence": confidence,
        "evidence_field": evidence_field,
        "evidence_value": evidence_value,
        "guardrail": guardrail,
    }


def geo_by_label(geo_index: dict[str, dict[str, str]], label: str) -> dict[str, str] | None:
    return geo_index.get(key(label))


def path_segments(place_text: str) -> list[str]:
    return [clean(part) for part in re.split(r"/|;", place_text) if clean(part)]


def decide_from_place(row: dict[str, str], geo_index: dict[str, dict[str, str]]) -> dict[str, str] | None:
    place = clean(row.get("place_text"))
    if not place:
        return None
    place_key = place.lower()
    if place_key in GLOBALISH:
        return None

    segments = path_segments(place)
    terminal = segments[-1] if segments else ""
    terminal_geo = geo_index.get(key(terminal))
    if terminal_geo:
        return controlled_decision(row, terminal_geo, "place_text", place, "high")

    for length in range(len(segments), 0, -1):
        prefix = " / ".join(segments[:length]).lower()
        if prefix in MACRO_PATHS:
            macro_label, region_id, geo_id = MACRO_PATHS[prefix]
            if key(terminal) != key(macro_label):
                return macro_or_specific_decision(
                    row,
                    terminal,
                    region_id,
                    geo_id if key(macro_label) in key(prefix) else "",
                    "place_text",
                    place,
                    "medium",
                    "auto_specific_uncontrolled_candidate",
                    "Explicit path has a specific terminal place not yet represented in geographies.csv; keep as folder label and retain macro refs.",
                )
            return macro_or_specific_decision(
                row,
                macro_label,
                region_id,
                geo_id,
                "place_text",
                place,
                "medium",
                "auto_macro_context_candidate",
                "Explicit macro-region path only; use macro context without pretending country-level precision.",
                )
    if len(segments) == 1:
        geo = geo_index.get(key(segments[0]))
        if geo:
            return controlled_decision(row, geo, "place_text", place, "high")
    return None


def decide_from_local_markers(row: dict[str, str], geo_index: dict[str, dict[str, str]]) -> dict[str, str] | None:
    place = clean(row.get("place_text"))
    blob = " ".join(
        clean(row.get(field))
        for field in ("place_text", "source_subjects", "title", "source_name", "source_url")
        if clean(row.get(field))
    )
    blob_l = blob.lower()
    place_l = place.lower()

    if place_l in {"europe and usa", "europe and usa; europe and usa"}:
        return macro_or_specific_decision(
            row,
            "Global / transnational",
            "",
            "GEO001",
            "place_text",
            place,
            "medium",
            "keep_global_context",
            "Explicit Europe/USA transnational place label; do not collapse to one country.",
        )

    place_alias = geo_index.get(key(place))
    if place_alias:
        return controlled_decision(row, place_alias, "place_text", place, "high")

    local_rules = [
        (r"\b(?:atlanta|eastman|chicago|washington|boston|montclair|ohio|illinois|massachusetts|rhode island|new york|southern states)\b|\([a-z]{2}\.\)|\busa\b|\bu\.s\.\b|work projects administration|\bwpa\b", "United States"),
        (r"\b(?:london|england)\b", "United Kingdom"),
        (r"\bberlin\b", "Germany"),
        (r"\bflanders\b|\bbruges\b", "Belgium"),
        (r"\bcanada\b|--\s*canada\b", "Canada"),
        (r"\bpuerto rico\b", "Puerto Rico"),
    ]
    for pattern, label in local_rules:
        if not re.search(pattern, blob_l, re.I):
            continue
        geo = geo_by_label(geo_index, label)
        if geo:
            return controlled_decision(row, geo, "local_marker", blob[:220], "medium")
        if label == "Puerto Rico":
            return macro_or_specific_decision(
                row,
                "Puerto Rico",
                "REG003",
                "",
                "local_marker",
                blob[:220],
                "medium",
                "auto_specific_uncontrolled_candidate",
                "Puerto Rico is explicit but not yet represented in geographies.csv; keep as folder label and retain North America ref.",
            )
    return None


def exact_subject_tokens(row: dict[str, str], geo_index: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    subjects = clean(row.get("source_subjects"))
    if not subjects:
        return []
    hits: list[dict[str, str]] = []
    for token in [clean(part) for part in re.split(r"[;|,/]", subjects) if clean(part)]:
        geo = geo_index.get(key(token))
        if geo and clean(geo.get("name")) not in {clean(hit.get("name")) for hit in hits}:
            hits.append(geo)
    return hits


def decide_from_subject(row: dict[str, str], geo_index: dict[str, dict[str, str]]) -> dict[str, str] | None:
    hits = exact_subject_tokens(row, geo_index)
    if len(hits) == 1:
        return controlled_decision(row, hits[0], "source_subjects", clean(row.get("source_subjects")), "medium")
    if len(hits) > 1:
        labels = "; ".join(clean(hit.get("name")) for hit in hits)
        return macro_or_specific_decision(
            row,
            "Manual geography review",
            "",
            "",
            "source_subjects",
            labels,
            "low",
            "manual_review",
            "Multiple controlled geography tokens appear; do not auto-assign a single region.",
        )
    return None


def decide_global(row: dict[str, str]) -> dict[str, str] | None:
    place = clean(row.get("place_text")).lower()
    if place not in GLOBALISH:
        return None
    return macro_or_specific_decision(
        row,
        "Global / transnational",
        "",
        "GEO001",
        "place_text",
        clean(row.get("place_text")),
        "medium",
        "keep_global_context",
        "Global/transnational capture label retained because no exact specific geography was found.",
    )


def decide_row(row: dict[str, str], geo_index: dict[str, dict[str, str]]) -> dict[str, str]:
    row = {key_name: clean(value) for key_name, value in row.items()}
    for decider in (decide_from_place, decide_from_local_markers, decide_from_subject):
        decision = decider(row, geo_index)
        if decision:
            return decision
    global_decision = decide_global(row)
    if global_decision:
        return global_decision
    return macro_or_specific_decision(
        row,
        "",
        "",
        "",
        "",
        "",
        "low",
        "insufficient_evidence",
        "No exact controlled geography or explicit macro path found; leave for manual review.",
    )


def override_rows(decisions: list[dict[str, str]]) -> list[dict[str, str]]:
    allowed = {
        "auto_apply_candidate",
        "auto_specific_uncontrolled_candidate",
        "auto_macro_context_candidate",
        "keep_global_context",
    }
    rows: list[dict[str, str]] = []
    for decision in decisions:
        if decision.get("decision_type") not in allowed:
            continue
        label = clean(decision.get("suggested_region_label"))
        if not label:
            continue
        place_text = clean(decision.get("place_text"))
        public_place = label if not place_text or place_text.lower() in GLOBALISH else place_text
        rows.append(
            {
                "source_file": decision.get("source_file", ""),
                "capture_id": decision.get("capture_id", ""),
                "surface_id": decision.get("surface_id", ""),
                "region_folder": label,
                "region_ids": decision.get("suggested_region_ids", ""),
                "geo_ids": decision.get("suggested_geo_ids", ""),
                "source_place_text": public_place,
                "decision_type": decision.get("decision_type", ""),
                "confidence": decision.get("confidence", ""),
                "repair_basis": f"{decision.get('evidence_field', '')}: {decision.get('evidence_value', '')}",
                "source_name": decision.get("source_name", ""),
                "title": decision.get("title", ""),
            }
        )
    return rows


def merge_override_rows(existing: list[dict[str, str]], new_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[tuple[str, str], dict[str, str]] = {}
    for row in existing:
        source_file = clean(row.get("source_file"))
        capture_id = clean(row.get("capture_id"))
        if source_file and capture_id:
            merged[(source_file, capture_id)] = row
    for row in new_rows:
        source_file = clean(row.get("source_file"))
        capture_id = clean(row.get("capture_id"))
        if source_file and capture_id:
            merged[(source_file, capture_id)] = row
    return [merged[key] for key in sorted(merged)]


def write_report(decisions: list[dict[str, str]], overrides: list[dict[str, str]]) -> None:
    decision_counts = Counter(row.get("decision_type", "") for row in decisions)
    label_counts = Counter(row.get("suggested_region_label", "") for row in decisions if row.get("suggested_region_label"))
    confidence_counts = Counter(row.get("confidence", "") for row in decisions)
    lines = [
        "# Prefreeze Geography Repair Decisions v1",
        "",
        "Scope: deterministic geography repair for candidate promotion review. This does not edit raw capture data and does not overwrite the official public payload.",
        "",
        "## Summary",
        "",
        f"- queue_rows: {len(decisions)}",
        f"- override_rows: {len(overrides)}",
    ]
    for decision_type, count in decision_counts.most_common():
        lines.append(f"- decision:{decision_type}: {count}")
    for confidence, count in confidence_counts.most_common():
        lines.append(f"- confidence:{confidence}: {count}")
    lines.extend(["", "## Largest Suggested Labels", ""])
    for label, count in label_counts.most_common(30):
        lines.append(f"- {label}: {count}")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Geography repair is source/folder normalization only.",
            "- No image files were downloaded.",
            "- IMG01/IMG03 rights states were not upgraded.",
            "- Specific labels missing from geographies.csv are marked as uncontrolled candidates and retain macro region references.",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    geo_index = load_geo_index()
    queue = read_csv(QUEUE)
    decisions = [decide_row(row, geo_index) for row in queue]
    new_overrides = override_rows(decisions)
    existing_overrides = read_csv(OUT_OVERRIDES)
    overrides = merge_override_rows(existing_overrides, new_overrides)

    summary_rows: list[dict[str, str]] = [
        {"metric": "queue_rows", "value": str(len(queue)), "notes": "Unresolved-region rows from candidate blocker audit."},
        {"metric": "decision_rows", "value": str(len(decisions)), "notes": "Rows with deterministic repair decisions."},
        {"metric": "new_override_rows", "value": str(len(new_overrides)), "notes": "Rows eligible for in-memory geography override from the current queue."},
        {"metric": "existing_override_rows_preserved", "value": str(len(existing_overrides)), "notes": "Previously audited overrides retained by source_file + capture_id."},
        {"metric": "cumulative_override_rows", "value": str(len(overrides)), "notes": "Total override rows written for candidate/public rebuild."},
    ]
    for decision_type, count in Counter(row.get("decision_type", "") for row in decisions).most_common():
        summary_rows.append({"metric": f"decision:{decision_type}", "value": str(count), "notes": "Decision type distribution."})
    for confidence, count in Counter(row.get("confidence", "") for row in decisions).most_common():
        summary_rows.append({"metric": f"confidence:{confidence}", "value": str(count), "notes": "Confidence distribution."})

    write_csv(OUT_DECISIONS, decisions, DECISION_FIELDS)
    write_csv(OUT_OVERRIDES, overrides, OVERRIDE_FIELDS)
    write_csv(OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_report(decisions, overrides)

    print(f"queue_rows={len(queue)}")
    print(f"override_rows={len(overrides)}")
    print(f"wrote {OUT_DECISIONS.relative_to(ROOT)}")
    print(f"wrote {OUT_OVERRIDES.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
