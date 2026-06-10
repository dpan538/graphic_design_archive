#!/usr/bin/env python3
"""Generate proposal-only region/geography normalization candidates.

This pass turns the normalization decision table into per-surface candidate
actions. It is intentionally read-only: it does not rewrite public surfaces,
controlled taxonomy CSVs, source records, or generated frontend data.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from lib.archive_audit import DATA, DOCS, ROOT, clean, read_csv, read_payload, surface_period_band, write_csv


DECISIONS = DATA / "region_geography_normalization_decisions_v1.csv"
CANDIDATES = DATA / "region_geography_normalization_candidates_v1.csv"
SUMMARY = DATA / "region_geography_normalization_candidate_summary_v1.csv"
REPORT = DOCS / "REGION_GEOGRAPHY_NORMALIZATION_CANDIDATES_v1.md"

CANDIDATE_FIELDS = [
    "surface_id",
    "source_record_id",
    "title",
    "date_text",
    "period_band",
    "source_name",
    "current_region_label",
    "decision_id",
    "candidate_action",
    "candidate_status",
    "target_region_ids",
    "target_geo_ids",
    "target_display_labels",
    "confidence",
    "review_queue",
    "evidence_fields",
    "evidence_snippet",
    "guardrail",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]

TEXT_FIELDS = [
    "placeText",
    "sourceSubjects",
    "title",
    "sourceDescription",
    "sourceNotes",
    "sourceName",
]
HIGH_SIGNAL_FIELDS = ["placeText", "sourceSubjects"]

COUNTRY_ALIAS_TARGETS = {
    "usa": ("United States", "REG003", "GEO025"),
    "u s a": ("United States", "REG003", "GEO025"),
    "u.s.a": ("United States", "REG003", "GEO025"),
    "united states": ("United States", "REG003", "GEO025"),
    "united states of america": ("United States", "REG003", "GEO025"),
    "france": ("France", "REG001", "GEO005"),
    "brazil": ("Brazil", "REG004", "GEO030"),
    "brasil": ("Brazil", "REG004", "GEO030"),
    "mexico": ("Mexico", "REG004", "GEO027"),
    "india": ("India", "REG012", "GEO051"),
    "japan": ("Japan", "REG005", "GEO036"),
    "italy": ("Italy", "REG001", "GEO011"),
    "united kingdom": ("United Kingdom", "REG001", "GEO003"),
    "great britain": ("United Kingdom", "REG001", "GEO003"),
    "uk": ("United Kingdom", "REG001", "GEO003"),
    "germany": ("Germany", "REG001", "GEO006"),
    "austria": ("Austria", "REG001", "GEO008"),
    "switzerland": ("Switzerland", "REG001", "GEO007"),
    "netherlands": ("Netherlands", "REG001", "GEO009"),
    "belgium": ("Belgium", "REG001", "GEO010"),
    "poland": ("Poland", "REG002", "GEO018"),
    "aotearoa new zealand": ("Aotearoa New Zealand", "REG015", "GEO070"),
    "new zealand": ("Aotearoa New Zealand", "REG015", "GEO070"),
    "australia": ("Australia", "REG015", "GEO069"),
    "south africa": ("South Africa", "REG014", "GEO062"),
    "china": ("Mainland China", "REG008", "GEO040"),
    "hong kong": ("Hong Kong", "REG009", "GEO041"),
    "taiwan": ("Taiwan", "REG010", "GEO042"),
    "cuba": ("Cuba", "REG004", "GEO029"),
    "palestine": ("Palestinian territories and diaspora", "REG013", "GEO085"),
    "mandatory palestine": ("Mandatory Palestine", "REG013", "GEO084"),
    "russia": ("Russia / USSR contexts", "REG002", "GEO016"),
    "uruguay": ("Uruguay", "REG004", ""),
    "chile": ("Chile", "REG004", "GEO032"),
    "argentina": ("Argentina", "REG004", "GEO031"),
    "canada": ("Canada", "REG003", "GEO026"),
    "nigeria": ("Nigeria", "REG014", "GEO063"),
    "ghana": ("Ghana", "REG014", "GEO064"),
    "egypt": ("Egypt", "REG013", "GEO056"),
    "iran": ("Iran", "REG013", "GEO057"),
    "turkey": ("Turkey", "REG013", "GEO058"),
}

SENSITIVE_TERMS = {
    "indigenous": "protocol_sensitive",
    "aboriginal": "protocol_sensitive",
    "torres strait": "protocol_sensitive",
    "palestine": "historical_or_political_review",
    "transnational": "context_split_review",
    "soviet": "historical_period_review",
    "ussr": "historical_period_review",
    "east germany": "historical_period_review",
    "west germany": "historical_period_review",
    "hong kong": "territory_context_review",
    "taiwan": "territory_context_review",
}


def norm(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean(value).lower()).strip()


def field_text(surface: dict[str, Any], field: str) -> str:
    return clean(surface.get(field))


def current_region(surface: dict[str, Any]) -> str:
    for folder in surface.get("folders") or []:
        if isinstance(folder, dict) and folder.get("type") == "region":
            return clean(folder.get("title"))
    return "Unresolved region"


def evidence_bundle(surface: dict[str, Any]) -> tuple[str, str, str]:
    hits: list[str] = []
    snippets: list[str] = []
    full_parts: list[str] = []
    for field in TEXT_FIELDS:
        value = field_text(surface, field)
        if not value:
            continue
        full_parts.append(value)
        trimmed = re.sub(r"\s+", " ", value)[:180]
        snippets.append(f"{field}: {trimmed}")
        hits.append(field)
    return "; ".join(hits), " | ".join(snippets[:4]), " ".join(full_parts)


def split_terms(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def decision_index() -> dict[str, dict[str, str]]:
    rows = read_csv(DECISIONS)
    by_label: dict[str, dict[str, str]] = {}
    for row in rows:
        label = clean(row.get("source_label"))
        if label:
            by_label[label] = row
    return by_label


def infer_from_text(text: str) -> list[tuple[str, str, str, str]]:
    normalized = f" {norm(text)} "
    matches: list[tuple[str, str, str, str]] = []
    for alias, target in COUNTRY_ALIAS_TARGETS.items():
        pattern = f" {norm(alias)} "
        if pattern in normalized:
            matches.append((target[0], target[1], target[2], alias))
    seen: set[tuple[str, str, str]] = set()
    unique: list[tuple[str, str, str, str]] = []
    for label, region_id, geo_id, alias in matches:
        key = (label, region_id, geo_id)
        if key in seen:
            continue
        seen.add(key)
        unique.append((label, region_id, geo_id, alias))
    return unique


def sensitive_review_flags(text: str) -> list[str]:
    normalized = norm(text)
    flags = []
    for term, flag in SENSITIVE_TERMS.items():
        if norm(term) in normalized:
            flags.append(flag)
    return sorted(set(flags))


def composite_place_review(surface: dict[str, Any]) -> tuple[str, str, str] | None:
    place = norm(field_text(surface, "placeText"))
    if "europe and usa" in place or "europe usa" in place:
        return ("REG001; REG003", "GEO002; GEO025", "Western and Central Europe; United States")
    return None


def choose_unresolved_candidate(surface: dict[str, Any], text: str) -> tuple[str, str, str, str, str, str]:
    high_signal_text = " ".join(field_text(surface, field) for field in HIGH_SIGNAL_FIELDS)
    high_signal_matches = infer_from_text(high_signal_text)
    all_matches = infer_from_text(text)
    flags = sensitive_review_flags(text)
    if not high_signal_matches and not all_matches:
        return ("keep_pending", "manual_review", "", "", "", "low")

    if not high_signal_matches:
        labels = "; ".join(match[0] for match in all_matches[:4])
        region_ids = "; ".join(sorted({match[1] for match in all_matches if match[1]}))
        geo_ids = "; ".join(sorted({match[2] for match in all_matches if match[2]}))
        queue = "; ".join(flags) or "low_signal_geo_review"
        return ("review_low_signal_geo_candidates", queue, region_ids, geo_ids, labels, "low")

    if flags:
        labels = "; ".join(match[0] for match in high_signal_matches[:4])
        region_ids = "; ".join(sorted({match[1] for match in high_signal_matches if match[1]}))
        geo_ids = "; ".join(sorted({match[2] for match in high_signal_matches if match[2]}))
        queue = "; ".join(flags)
        return ("review_inferred_sensitive_mapping", queue, region_ids, geo_ids, labels, "medium")

    composite = composite_place_review(surface)
    if composite:
        region_ids, geo_ids, labels = composite
        return ("review_multiple_geo_candidates", "multi_match_review", region_ids, geo_ids, labels, "medium")

    if len(high_signal_matches) == 1:
        label, region_id, geo_id, _alias = high_signal_matches[0]
        confidence = "high" if field_text(surface, "placeText") else "medium"
        return ("auto_map_from_unresolved", "auto_candidate", region_id, geo_id, label, confidence)

    labels = "; ".join(match[0] for match in high_signal_matches[:4])
    region_ids = "; ".join(sorted({match[1] for match in high_signal_matches if match[1]}))
    geo_ids = "; ".join(sorted({match[2] for match in high_signal_matches if match[2]}))
    return ("review_multiple_geo_candidates", "multi_match_review", region_ids, geo_ids, labels, "medium")


def candidate_for_surface(surface: dict[str, Any], decisions: dict[str, dict[str, str]]) -> dict[str, str] | None:
    label = current_region(surface)
    fields, snippet, text = evidence_bundle(surface)
    decision = decisions.get(label)

    if label == "Unresolved region":
        action, status, region_ids, geo_ids, labels, confidence = choose_unresolved_candidate(surface, text)
        return build_row(
            surface,
            label,
            decision,
            action,
            status,
            region_ids,
            geo_ids,
            labels,
            confidence,
            status,
            fields,
            snippet,
        )

    if not decision:
        return None

    decision_class = clean(decision.get("decision_class"))
    proposed = clean(decision.get("proposed_action"))
    high_signal_text = " ".join(field_text(surface, field) for field in HIGH_SIGNAL_FIELDS)
    high_signal_matches = infer_from_text(high_signal_text)
    target_geo_ids = {item.strip() for item in clean(decision.get("target_geo_ids")).split(";") if item.strip()}
    high_signal_geo_ids = {match[2] for match in high_signal_matches if match[2]}
    if (
        target_geo_ids
        and high_signal_geo_ids
        and target_geo_ids.isdisjoint(high_signal_geo_ids)
        and decision_class.startswith("auto_country_mapping")
    ):
        return build_row(
            surface,
            label,
            decision,
            "review_existing_region_conflict",
            "geography_conflict_review",
            "; ".join(sorted({match[1] for match in high_signal_matches if match[1]})),
            "; ".join(sorted(high_signal_geo_ids)),
            "; ".join(match[0] for match in high_signal_matches[:4]),
            "medium",
            "geography_conflict_review",
            fields,
            snippet,
        )

    if decision_class == "auto_country_mapping":
        status = "auto_existing_mapping_candidate"
    elif decision_class in {"mapping_gap_or_display_alias", "controlled_geo_missing"}:
        status = "taxonomy_mapping_candidate"
    elif "split" in decision_class or "split" in proposed:
        status = "split_review"
    elif "historical" in decision_class or "sensitive" in decision_class:
        status = "sensitive_or_historical_review"
    else:
        status = "review_candidate"

    flags = sensitive_review_flags(text)
    if flags and status == "taxonomy_mapping_candidate":
        status = "taxonomy_mapping_with_sensitive_terms"

    return build_row(
        surface,
        label,
        decision,
        proposed,
        status,
        clean(decision.get("target_region_ids")),
        clean(decision.get("target_geo_ids")),
        clean(decision.get("recommended_preferred_label")),
        clean(decision.get("confidence")) or "medium",
        "; ".join(flags) or status,
        fields,
        snippet,
    )


def build_row(
    surface: dict[str, Any],
    label: str,
    decision: dict[str, str] | None,
    action: str,
    status: str,
    region_ids: str,
    geo_ids: str,
    labels: str,
    confidence: str,
    queue: str,
    fields: str,
    snippet: str,
) -> dict[str, str]:
    return {
        "surface_id": clean(surface.get("surfaceId")),
        "source_record_id": clean(surface.get("sourceRecordId")),
        "title": clean(surface.get("title")),
        "date_text": clean(surface.get("dateText")),
        "period_band": surface_period_band(surface),
        "source_name": clean(surface.get("sourceName")),
        "current_region_label": label,
        "decision_id": clean(decision.get("decision_id")) if decision else "RGN-008",
        "candidate_action": action,
        "candidate_status": status,
        "target_region_ids": region_ids,
        "target_geo_ids": geo_ids,
        "target_display_labels": labels,
        "confidence": confidence,
        "review_queue": queue,
        "evidence_fields": fields,
        "evidence_snippet": snippet,
        "guardrail": clean(decision.get("implementation_guardrail")) if decision else "Do not auto-map without record-level evidence.",
    }


def build_report(rows: list[dict[str, str]], surfaces_total: int) -> str:
    by_action = Counter(row["candidate_action"] for row in rows)
    by_status = Counter(row["candidate_status"] for row in rows)
    by_label = Counter(row["current_region_label"] for row in rows)
    unresolved_rows = [row for row in rows if row["current_region_label"] == "Unresolved region"]
    unresolved_auto = [row for row in unresolved_rows if row["candidate_action"] == "auto_map_from_unresolved"]
    unresolved_pending = [row for row in unresolved_rows if row["candidate_action"] == "keep_pending"]
    unresolved_low_signal = [row for row in unresolved_rows if row["candidate_action"] == "review_low_signal_geo_candidates"]
    unresolved_review = [
        row
        for row in unresolved_rows
        if row["candidate_action"] not in {"auto_map_from_unresolved", "keep_pending", "review_low_signal_geo_candidates"}
    ]
    conflicts = [row for row in rows if row["candidate_action"] == "review_existing_region_conflict"]

    lines = [
        "# Region / Geography Normalization Candidates v1",
        "",
        "Scope: proposal-only per-surface candidate generation. This report does not rewrite surfaces, source records, or controlled taxonomy CSVs.",
        "",
        "## Summary",
        "",
        f"- public surfaces scanned: {surfaces_total}",
        f"- candidate rows generated: {len(rows)}",
        f"- unresolved rows with auto-map candidates: {len(unresolved_auto)}",
        f"- unresolved rows needing manual/sensitive review: {len(unresolved_review)}",
        f"- unresolved rows with low-signal geography hints: {len(unresolved_low_signal)}",
        f"- unresolved rows remaining pending: {len(unresolved_pending)}",
        f"- existing region-label conflicts: {len(conflicts)}",
        "",
        "## Candidate Actions",
        "",
    ]
    for action, count in by_action.most_common():
        lines.append(f"- {action}: {count}")

    lines.extend(["", "## Candidate Status", ""])
    for status, count in by_status.most_common():
        lines.append(f"- {status}: {count}")

    lines.extend(["", "## Current Labels in Candidate Set", ""])
    for label, count in by_label.most_common():
        lines.append(f"- {label}: {count}")

    lines.extend(["", "## High-Signal Unresolved Samples", ""])
    for row in unresolved_auto[:12]:
        lines.append(
            f"- {row['surface_id']} -> {row['target_display_labels']} "
            f"({row['confidence']}): {row['title'][:100]}"
        )

    lines.extend(["", "## Existing Region Conflicts", ""])
    if conflicts:
        for label, count in Counter(row["current_region_label"] for row in conflicts).most_common():
            lines.append(f"- {label}: {count}")
        lines.extend(["", "Sample conflicts:", ""])
        for row in conflicts[:12]:
            lines.append(
                f"- {row['surface_id']}: {row['current_region_label']} -> evidence suggests "
                f"{row['target_display_labels']} · {row['title'][:100]}"
            )
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A large part of `Unresolved region` can be triaged before any new capture because many records already carry country/place evidence in source metadata.",
            "- Candidate rows with `auto_map_from_unresolved` should still be sampled before application, but they are the safest first cleanup batch.",
            "- `review_existing_region_conflict` rows show current public folder labels that disagree with high-signal geography fields and should block automated application.",
            "- Slash labels remain review queues. They should be split from record evidence, not replaced by one preferred string.",
            "- `Uruguay` is the clearest controlled-geography addition: the public folder is explicit, but no controlled geography row exists yet.",
            "- True source-gap capture should follow this cleanup, especially for Southeast Asia, MENA beyond Palestine, Africa beyond Southern Africa, and Pacific/Aotearoa contexts.",
            "",
            "## Generated Files",
            "",
            f"- `data/{CANDIDATES.name}`",
            f"- `data/{SUMMARY.name}`",
            f"- `docs/capture/{REPORT.name}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = read_payload()
    surfaces = payload.get("surfaces", [])
    decisions = decision_index()
    rows = [
        row
        for surface in surfaces
        if (row := candidate_for_surface(surface, decisions)) is not None
    ]

    by_action = Counter(row["candidate_action"] for row in rows)
    by_status = Counter(row["candidate_status"] for row in rows)
    unresolved = [row for row in rows if row["current_region_label"] == "Unresolved region"]
    summary_rows = [
        {"metric": "public_surfaces_scanned", "value": str(len(surfaces)), "notes": "Read from generated/public_surfaces_v1.json."},
        {"metric": "candidate_rows", "value": str(len(rows)), "notes": "Proposal-only rows; no surface rewrite."},
        {"metric": "candidate_actions", "value": "; ".join(f"{k}:{v}" for k, v in by_action.most_common()), "notes": "Action distribution."},
        {"metric": "candidate_status", "value": "; ".join(f"{k}:{v}" for k, v in by_status.most_common()), "notes": "Review status distribution."},
        {
            "metric": "unresolved_auto_map_candidates",
            "value": str(sum(1 for row in unresolved if row["candidate_action"] == "auto_map_from_unresolved")),
            "notes": "Unresolved rows with a single non-sensitive geography candidate.",
        },
        {
            "metric": "unresolved_review_candidates",
            "value": str(sum(1 for row in unresolved if row["candidate_action"] not in {"auto_map_from_unresolved", "keep_pending", "review_low_signal_geo_candidates"})),
            "notes": "Unresolved rows with sensitive, multiple, or ambiguous high-signal geography evidence.",
        },
        {
            "metric": "unresolved_low_signal_geo_candidates",
            "value": str(sum(1 for row in unresolved if row["candidate_action"] == "review_low_signal_geo_candidates")),
            "notes": "Unresolved rows with geography hints only in lower-signal fields such as title/source description/source name.",
        },
        {
            "metric": "unresolved_keep_pending",
            "value": str(sum(1 for row in unresolved if row["candidate_action"] == "keep_pending")),
            "notes": "Unresolved rows without enough geography evidence in the inspected fields.",
        },
        {
            "metric": "existing_region_conflict_candidates",
            "value": str(sum(1 for row in rows if row["candidate_action"] == "review_existing_region_conflict")),
            "notes": "Existing public region labels that disagree with high-signal geography fields.",
        },
    ]

    write_csv(CANDIDATES, rows, CANDIDATE_FIELDS)
    write_csv(SUMMARY, summary_rows, SUMMARY_FIELDS)
    REPORT.write_text(build_report(rows, len(surfaces)), encoding="utf-8")

    print(f"public_surfaces_scanned={len(surfaces)}")
    print(f"candidate_rows={len(rows)}")
    print(f"unresolved_auto_map_candidates={summary_rows[4]['value']}")
    print(f"unresolved_review_candidates={summary_rows[5]['value']}")
    print(f"unresolved_low_signal_geo_candidates={summary_rows[6]['value']}")
    print(f"unresolved_keep_pending={summary_rows[7]['value']}")
    print(f"existing_region_conflict_candidates={summary_rows[8]['value']}")
    print(f"wrote {CANDIDATES.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
