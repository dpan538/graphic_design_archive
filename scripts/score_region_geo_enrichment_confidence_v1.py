#!/usr/bin/env python3
"""Score region/geography enrichment suggestions for safe application.

This script is proposal-only. It adds confidence, risk, and auto-apply
eligibility fields to local enrichment suggestions without modifying archive
records or public surfaces.
"""

from __future__ import annotations

import re
from collections import Counter

from lib.archive_audit import DATA, ROOT, clean, read_csv, write_csv


DIRECT = DATA / "region_conflict_direct_parse_v1.csv"
HISTORICAL = DATA / "region_conflict_historical_split_suggestions_v1.csv"
PENDING = DATA / "region_pending_geo_text_suggestions_v1.csv"
CANDIDATES = DATA / "region_geography_normalization_candidates_v1.csv"

OUTPUT_CONFIDENCE = DATA / "region_geo_enrichment_with_confidence_v1.csv"
OUTPUT_AUTO = DATA / "region_geo_auto_apply_ready_v1.csv"

FIELDS = [
    "suggestion_id",
    "surface_id",
    "source_record_id",
    "suggestion_type",
    "current_label",
    "suggested_label",
    "suggested_region_id",
    "suggested_geo_id",
    "confidence_level",
    "evidence_type",
    "auto_apply_eligible",
    "requires_date_check",
    "external_validation_status",
    "suggested_action",
    "years_found",
    "risk_flags",
    "evidence",
    "title",
    "source_file",
]

DISPUTED_PERIODS = [
    (1846, 1848, {"Mexico", "United States"}),
    (1910, 1920, {"Mexico"}),
    (1939, 1945, {"France", "Germany", "Italy", "Japan"}),
    (1947, 1991, {"Germany", "Russia / USSR contexts", "Russia", "Soviet Union"}),
    (1949, 1990, {"Germany", "East Germany", "West Germany"}),
]

SENSITIVE_LABEL_PARTS = {
    "palestine",
    "ussr",
    "soviet",
    "indigenous",
    "aboriginal",
    "torres strait",
    "hong kong",
    "taiwan",
    "caucasus",
}

COUNTRY_CONTEXT_TYPES = {
    "country_context",
    "country/territory_context",
    "city/territory_context",
}


def norm(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean(value).lower()).strip()


def years_from_text(*values: str) -> list[int]:
    text = " ".join(clean(value) for value in values)
    return sorted({int(item) for item in re.findall(r"\b(1[7-9]\d{2}|20[0-2]\d)\b", text)})


def candidate_index() -> dict[str, dict[str, str]]:
    return {row["surface_id"]: row for row in read_csv(CANDIDATES) if row.get("surface_id")}


def controlled_label_index() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in read_csv(DATA / "geographies.csv"):
        name = clean(row.get("name"))
        if name:
            out[name] = row
    return out


def country_like_labels() -> set[str]:
    labels = set()
    for row in read_csv(DATA / "geographies.csv"):
        if clean(row.get("geo_type")) in COUNTRY_CONTEXT_TYPES:
            labels.add(clean(row.get("name")))
    labels.update({"United States", "Mexico", "Russia", "Soviet Union", "East Germany", "West Germany"})
    return {label for label in labels if label}


def label_occurrences(evidence: str, label: str) -> int:
    if not evidence or not label:
        return 0
    return len(re.findall(rf"\b{re.escape(label)}\b", evidence, flags=re.IGNORECASE))


def labels_in_evidence(evidence: str, labels: set[str]) -> set[str]:
    found = set()
    normalized = f" {norm(evidence)} "
    for label in labels:
        if f" {norm(label)} " in normalized:
            found.add(label)
    return found


def disputed(years: list[int], labels: set[str]) -> bool:
    for year in years:
        for start, end, affected in DISPUTED_PERIODS:
            if start <= year <= end and (labels & affected):
                return True
    return False


def sensitive_label(label: str, evidence: str) -> bool:
    text = norm(f"{label} {evidence}")
    return any(part in text for part in SENSITIVE_LABEL_PARTS)


def direct_score(
    row: dict[str, str],
    candidates: dict[str, dict[str, str]],
    controlled: dict[str, dict[str, str]],
    country_labels: set[str],
) -> dict[str, str]:
    surface_id = clean(row.get("surface_id"))
    candidate = candidates.get(surface_id, {})
    suggested = clean(row.get("suggested_label"))
    evidence = clean(row.get("match_evidence"))
    title = clean(row.get("title"))
    years = years_from_text(evidence, title, candidate.get("date_text", ""), candidate.get("evidence_snippet", ""))
    found_labels = labels_in_evidence(evidence, country_labels)
    if suggested:
        found_labels.add(suggested)

    risk_flags: list[str] = []
    if len(found_labels) > 1:
        risk_flags.append("multiple_country_evidence")
    if disputed(years, {suggested, clean(row.get("current_region_label"))} | found_labels):
        risk_flags.append("historical_dispute_period")
    if sensitive_label(suggested, evidence):
        risk_flags.append("sensitive_or_historical_label")

    geo = controlled.get(suggested, {})
    is_country_context = clean(geo.get("geo_type")) in COUNTRY_CONTEXT_TYPES
    occurrence = label_occurrences(evidence, suggested)
    explicit = occurrence >= 1 and suggested in controlled
    confidence = "medium"
    auto = False
    action = "manual_review"
    evidence_type = "explicit_country_in_metadata" if explicit else "controlled_label_suggestion"

    if explicit and is_country_context and not risk_flags:
        confidence = "high"
        auto = True
        action = "apply_directly"
    elif explicit and "historical_dispute_period" in risk_flags:
        confidence = "medium"
        action = "split_by_date"
    elif explicit:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "surface_id": surface_id,
        "source_record_id": row.get("source_record_id", ""),
        "suggestion_type": "direct_conflict_parse",
        "current_label": row.get("current_region_label", ""),
        "suggested_label": suggested,
        "suggested_region_id": row.get("suggested_region_id", ""),
        "suggested_geo_id": row.get("suggested_geo_id", ""),
        "confidence_level": confidence,
        "evidence_type": evidence_type,
        "auto_apply_eligible": str(auto).lower(),
        "requires_date_check": str("historical_dispute_period" in risk_flags).lower(),
        "external_validation_status": "unchecked",
        "suggested_action": action,
        "years_found": "; ".join(str(year) for year in years),
        "risk_flags": "; ".join(risk_flags),
        "evidence": evidence,
        "title": title,
        "source_file": DIRECT.name,
    }


def historical_score(row: dict[str, str]) -> dict[str, str]:
    evidence = clean(row.get("match_evidence"))
    title = clean(row.get("title"))
    years = years_from_text(evidence, title, row.get("period_basis", ""))
    return {
        "surface_id": row.get("surface_id", ""),
        "source_record_id": row.get("source_record_id", ""),
        "suggestion_type": "historical_split",
        "current_label": row.get("current_region_label", ""),
        "suggested_label": row.get("suggested_split_label", ""),
        "suggested_region_id": "",
        "suggested_geo_id": "",
        "confidence_level": "medium",
        "evidence_type": "historical_period_rule",
        "auto_apply_eligible": "false",
        "requires_date_check": "true",
        "external_validation_status": "unchecked",
        "suggested_action": "split_by_date",
        "years_found": "; ".join(str(year) for year in years),
        "risk_flags": "historical_split_requires_taxonomy_support",
        "evidence": evidence,
        "title": title,
        "source_file": HISTORICAL.name,
    }


def pending_score(row: dict[str, str], country_labels: set[str]) -> dict[str, str]:
    evidence = clean(row.get("match_evidence"))
    suggested = clean(row.get("suggested_label"))
    years = years_from_text(evidence, row.get("title", ""))
    occurrence = label_occurrences(evidence, suggested)
    risk_flags = ["pending_or_low_signal_source"]
    if len(labels_in_evidence(evidence, country_labels)) > 1:
        risk_flags.append("multiple_country_evidence")
    if clean(row.get("match_field")) not in {"placeText", "sourceSubjects"}:
        risk_flags.append("low_signal_field")

    confidence = "low"
    if suggested in country_labels and occurrence == 1 and clean(row.get("match_field")) in {"placeText", "sourceSubjects"}:
        confidence = "medium"
    elif clean(row.get("confidence")) == "medium_high":
        confidence = "medium"

    return {
        "surface_id": row.get("surface_id", ""),
        "source_record_id": row.get("source_record_id", ""),
        "suggestion_type": "pending_text_resurface",
        "current_label": row.get("current_region_label", ""),
        "suggested_label": suggested,
        "suggested_region_id": row.get("suggested_region_id", ""),
        "suggested_geo_id": row.get("suggested_geo_id", ""),
        "confidence_level": confidence,
        "evidence_type": "low_signal_text_geography" if "low_signal_field" in risk_flags else "metadata_geography_resurface",
        "auto_apply_eligible": "false",
        "requires_date_check": "false",
        "external_validation_status": "unchecked",
        "suggested_action": "manual_only",
        "years_found": "; ".join(str(year) for year in years),
        "risk_flags": "; ".join(risk_flags),
        "evidence": evidence,
        "title": row.get("title", ""),
        "source_file": PENDING.name,
    }


def with_ids(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for idx, row in enumerate(rows, start=1):
        next_row = {"suggestion_id": f"RGE-SCORE-{idx:05d}"}
        next_row.update(row)
        out.append(next_row)
    return out


def main() -> None:
    candidates = candidate_index()
    controlled = controlled_label_index()
    country_labels = country_like_labels()
    scored = []
    scored.extend(direct_score(row, candidates, controlled, country_labels) for row in read_csv(DIRECT))
    scored.extend(historical_score(row) for row in read_csv(HISTORICAL))
    scored.extend(pending_score(row, country_labels) for row in read_csv(PENDING))
    scored = with_ids(scored)
    auto = [row for row in scored if row["auto_apply_eligible"] == "true"]
    write_csv(OUTPUT_CONFIDENCE, scored, FIELDS)
    write_csv(OUTPUT_AUTO, auto, FIELDS)

    counts = Counter(row["suggestion_type"] for row in scored)
    print(f"scored_suggestions={len(scored)}")
    for key, value in counts.most_common():
        print(f"{key}={value}")
    print(f"auto_apply_ready={len(auto)}")
    print(f"wrote {OUTPUT_CONFIDENCE.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_AUTO.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
