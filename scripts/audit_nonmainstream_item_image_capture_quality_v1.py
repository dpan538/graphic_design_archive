#!/usr/bin/env python3
"""
Audit the non-mainstream item/image capture batch before surface rebuild.

This is an offline quality gate. It does not mutate source capture files,
download images, or upgrade image rights states. The output is a triage layer
for deciding which IMG02 source-hosted records can move into the next
item/surface review pass.
"""

from __future__ import annotations

import csv
import hashlib
import re
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]

INPUT_RECORDS = ROOT / "data/capture_batch_nonmainstream_item_image_2026_records.csv"
INPUT_SUMMARY = ROOT / "data/capture_batch_nonmainstream_item_image_2026_source_summary.csv"

OUTPUT_DETAIL = ROOT / "data/nonmainstream_item_image_capture_quality_v1.csv"
OUTPUT_SUMMARY = ROOT / "data/nonmainstream_item_image_capture_quality_summary_v1.csv"
OUTPUT_READY = ROOT / "data/nonmainstream_item_image_capture_ready_queue_v1.csv"
OUTPUT_MANUAL = ROOT / "data/nonmainstream_item_image_capture_manual_review_v1.csv"
OUTPUT_QUARANTINE = ROOT / "data/nonmainstream_item_image_capture_quarantine_v1.csv"
OUTPUT_REPORT = ROOT / "docs/capture/NONMAINSTREAM_ITEM_IMAGE_CAPTURE_QUALITY_v1.md"


DESIGN_TERMS = {
    "graphic design": 4,
    "visual communication": 4,
    "poster": 4,
    "cartel": 4,
    "carteles": 4,
    "affiche": 4,
    "plakat": 4,
    "advertising": 4,
    "advertisement": 4,
    "typography": 4,
    "tipografia": 4,
    "typographie": 4,
    "type design": 4,
    "publication design": 4,
    "book design": 4,
    "diseno grafico": 4,
    "grafico": 3,
    "grafica": 3,
    "graphic humor": 3,
    "humor grafico": 3,
    "historieta": 3,
    "comic": 3,
    "comics": 3,
    "logo": 3,
    "branding": 3,
    "identity": 3,
    "print design": 3,
    "printed matter": 3,
    "design studio": 3,
    "art school": 3,
    "design school": 3,
    "biennial": 2,
    "exhibition": 2,
    "catalogue": 2,
    "catalog": 2,
    "zine": 2,
    "poster art": 2,
    "illustration": 2,
    "printmaking": 2,
    "screen print": 2,
    "silkscreen": 2,
    "graphic art": 2,
    "visual art": 1,
    "festival": 1,
    "workshop": 1,
}

AUTHORITY_TERMS = {
    "national library": ("national_library", 4),
    "national archive": ("national_archive", 4),
    "national museum": ("national_museum", 4),
    "university": ("university", 3),
    "academy": ("academy", 3),
    "institute": ("institute", 3),
    "museum": ("museum", 3),
    "archive": ("archive", 3),
    "library": ("library", 2),
    "cultural center": ("cultural_center", 2),
    "cultural centre": ("cultural_center", 2),
    "foundation": ("foundation", 2),
    "biennial": ("biennial", 2),
    "gallery": ("gallery", 1),
    "studio": ("studio", 1),
    "craft": ("craft_market", 1),
    "school": ("school", 1),
}

SPAM_TERMS = {
    "sbobet",
    "judi",
    "casino",
    "slot",
    "betting",
    "taruhan",
    "login",
    "crypto",
    "porn",
    "escort",
    "viagra",
}

GENERIC_WEAK_SOURCE_TERMS = {
    "tourism",
    "restaurant",
    "hotel",
    "shop",
    "market",
    "marketing",
    "business",
    "conference room",
}

OVERBROAD_COUNTRY_LABELS = {
    "Caribbean",
    "Caucasus",
    "MENA",
    "Southeast Asia",
    "East Asia",
    "Central Asia",
    "South Asia",
    "Oceania",
    "Latin America",
    "Eastern Europe",
    "Africa",
}


def infer_geography(row: dict[str, str], summary: dict[str, str]) -> dict[str, Any]:
    source_place = (row.get("source_place_text") or "").strip()
    summary_macro = (summary.get("macro_region") or "").strip()
    summary_country = (summary.get("country_or_region") or "").strip()
    parts = [part.strip() for part in source_place.split("/") if part.strip()]
    place_macro = parts[0] if parts else ""
    place_country = parts[-1] if parts else ""

    if place_country and place_country not in OVERBROAD_COUNTRY_LABELS:
        inferred_macro = place_macro or summary_macro
        inferred_country = place_country
        precision = "country_from_source_place"
    elif summary_country and summary_country not in OVERBROAD_COUNTRY_LABELS:
        inferred_macro = summary_macro or place_macro
        inferred_country = summary_country
        precision = "country_from_summary"
    elif summary_country or place_country:
        inferred_macro = summary_macro or place_macro
        inferred_country = summary_country or place_country
        precision = "overbroad"
    else:
        inferred_macro = summary_macro or place_macro
        inferred_country = ""
        precision = "missing"

    repair_needed = (
        bool(inferred_country)
        and bool(summary_country)
        and inferred_country != summary_country
    )
    if inferred_macro and summary_macro and inferred_macro != summary_macro:
        repair_needed = True

    return {
        "source_place_text": source_place,
        "summary_macro_region": summary_macro,
        "summary_country_or_region": summary_country,
        "macro_region": inferred_macro,
        "country_or_region": inferred_country,
        "geo_precision": precision,
        "geo_repair_needed": repair_needed,
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(materialized)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_text.strip().lower())


def contains_any(text: str, terms: Iterable[str]) -> list[str]:
    found = []
    for term in sorted(terms, key=len, reverse=True):
        if term in text:
            found.append(term)
    return found


def score_design(text: str) -> tuple[int, list[str]]:
    hits = []
    score = 0
    for term, weight in DESIGN_TERMS.items():
        if term in text:
            hits.append(term)
            score += weight
    return min(score, 12), sorted(hits)


def score_authority(text: str) -> tuple[int, str, list[str]]:
    hits = []
    best_tier = "unclear"
    best_score = 0
    for term, (tier, weight) in AUTHORITY_TERMS.items():
        if term in text:
            hits.append(term)
            if weight > best_score:
                best_score = weight
                best_tier = tier
    return min(best_score, 5), best_tier, sorted(hits)


def text_bundle(row: dict[str, str]) -> str:
    keys = [
        "source_name",
        "source_title",
        "source_creator",
        "source_object_type",
        "source_medium",
        "source_collection",
        "source_description",
        "source_notes",
        "source_subjects",
        "editorial_summary",
        "historical_context_note",
        "classification_rationale",
        "citation_basis",
    ]
    return normalize(" ".join(row.get(key, "") for key in keys))


def text_depth(row: dict[str, str]) -> int:
    keys = [
        "source_description",
        "editorial_summary",
        "historical_context_note",
        "classification_rationale",
        "citation_basis",
        "source_subjects",
    ]
    return sum(len((row.get(key) or "").strip()) for key in keys)


def classify_row(row: dict[str, str], summary: dict[str, str]) -> dict[str, Any]:
    text = text_bundle(row)
    design_score, design_hits = score_design(text)
    authority_score, authority_tier, authority_hits = score_authority(text)
    spam_hits = contains_any(text, SPAM_TERMS)
    weak_hits = contains_any(text, GENERIC_WEAK_SOURCE_TERMS)
    geo = infer_geography(row, summary)
    country_label = geo["country_or_region"]
    overbroad_geo = geo["geo_precision"] == "overbroad"
    q_source_name = bool(re.fullmatch(r"Q\d+", row.get("source_name", "").strip()))
    img_state = row.get("image_presence_code", "")
    image_url = row.get("image_url_detected", "")
    text_chars = text_depth(row)
    has_image_route = bool(image_url.strip())
    rights_text = normalize(
        " ".join(
            [
                row.get("source_rights_text", ""),
                row.get("rights_basis", ""),
                row.get("image_presence_basis", ""),
            ]
        )
    )
    rights_has_source_link = "source" in rights_text or "source-hosted" in rights_text

    risk_flags = []
    if spam_hits:
        risk_flags.append("spam_or_seo_pollution")
    if q_source_name:
        risk_flags.append("qid_as_source_name")
    if overbroad_geo:
        risk_flags.append("overbroad_country_or_region")
    if not country_label:
        risk_flags.append("missing_country_or_region")
    if geo["geo_repair_needed"]:
        risk_flags.append("summary_geo_repair_needed")
    if weak_hits and design_score == 0:
        risk_flags.append("generic_non_design_source")
    if design_score == 0:
        risk_flags.append("missing_design_signal")
    if img_state != "IMG02":
        risk_flags.append("unexpected_image_state")
    if not has_image_route:
        risk_flags.append("missing_source_hosted_image_route")
    if text_chars < 180:
        risk_flags.append("thin_text_evidence")
    if not rights_has_source_link:
        risk_flags.append("thin_rights_basis")

    quality_score = (
        design_score
        + authority_score
        + (2 if has_image_route else 0)
        + (2 if text_chars >= 480 else 1 if text_chars >= 240 else 0)
        - (5 if spam_hits else 0)
        - (2 if q_source_name else 0)
        - (2 if overbroad_geo else 0)
        - (2 if weak_hits and design_score == 0 else 0)
    )

    if spam_hits or not has_image_route:
        readiness = "quarantine_not_counted"
        recommended_action = "exclude until source is replaced or manually repaired"
    elif design_score >= 4 and authority_score >= 2 and text_chars >= 240 and not overbroad_geo:
        readiness = "ready_for_item_review"
        recommended_action = "eligible for next item/surface review; keep IMG02 until rights-reviewed"
    elif design_score >= 2 and authority_score >= 1 and text_chars >= 180:
        readiness = "manual_review_before_surface"
        recommended_action = "review design relevance and geography before any rebuild"
    elif authority_score >= 3 and text_chars >= 300 and not weak_hits:
        readiness = "manual_review_before_surface"
        recommended_action = "institutional source; needs object-level design relevance check"
    else:
        if "low_surface_signal" not in risk_flags:
            risk_flags.append("low_surface_signal")
        readiness = "quarantine_not_counted"
        recommended_action = "do not count as successful source without stronger design evidence"

    if overbroad_geo and readiness == "ready_for_item_review":
        readiness = "manual_review_before_surface"
        recommended_action = "resolve overbroad geography before surface assignment"

    return {
        "capture_id": row.get("capture_id", ""),
        "source_id": row.get("source_id", ""),
        "source_name": row.get("source_name", ""),
        "source_identifier": row.get("source_identifier", ""),
        "source_record_url": row.get("source_record_url", ""),
        "source_title": row.get("source_title", ""),
        "source_place_text": geo["source_place_text"],
        "summary_macro_region": geo["summary_macro_region"],
        "summary_country_or_region": geo["summary_country_or_region"],
        "macro_region": geo["macro_region"],
        "country_or_region": country_label,
        "geo_precision": geo["geo_precision"],
        "geo_repair_needed": geo["geo_repair_needed"],
        "image_presence_code": img_state,
        "image_url_detected": image_url,
        "quality_score": quality_score,
        "design_signal_score": design_score,
        "design_signal_terms": "; ".join(design_hits),
        "authority_score": authority_score,
        "authority_tier": authority_tier,
        "authority_terms": "; ".join(authority_hits),
        "text_evidence_chars": text_chars,
        "risk_flags": "; ".join(risk_flags),
        "surface_readiness": readiness,
        "recommended_action": recommended_action,
        "rights_boundary": "IMG02 only; no image download; no IMG01/IMG03 upgrade",
    }


def counter_rows(label: str, counter: Counter[str]) -> list[dict[str, Any]]:
    return [
        {"metric_group": label, "metric": key or "(blank)", "value": value}
        for key, value in counter.most_common()
    ]


def build_report(detail_rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]]) -> str:
    total = len(detail_rows)
    readiness = Counter(row["surface_readiness"] for row in detail_rows)
    regions = Counter(row["macro_region"] for row in detail_rows)
    ready_regions = Counter(
        row["macro_region"]
        for row in detail_rows
        if row["surface_readiness"] == "ready_for_item_review"
    )
    risk_flags = Counter()
    for row in detail_rows:
        for flag in str(row["risk_flags"]).split("; "):
            if flag:
                risk_flags[flag] += 1
    authority = Counter(row["authority_tier"] for row in detail_rows)
    geo_precision = Counter(row["geo_precision"] for row in detail_rows)
    geo_repairs = Counter(str(row["geo_repair_needed"]).lower() for row in detail_rows)
    design_terms = Counter()
    for row in detail_rows:
        for term in str(row["design_signal_terms"]).split("; "):
            if term:
                design_terms[term] += 1

    def bullet_counts(counter: Counter[str], limit: int | None = None) -> list[str]:
        items = counter.most_common(limit)
        return [f"- {key or '(blank)'}: {value}" for key, value in items]

    ready_examples = [
        row
        for row in detail_rows
        if row["surface_readiness"] == "ready_for_item_review"
    ][:10]
    quarantine_examples = [
        row
        for row in detail_rows
        if row["surface_readiness"] == "quarantine_not_counted"
    ][:10]

    lines = [
        "# Non-mainstream item/image capture quality audit v1",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "## Scope",
        "",
        "- Input records: `data/capture_batch_nonmainstream_item_image_2026_records.csv`.",
        "- Input source summary: `data/capture_batch_nonmainstream_item_image_2026_source_summary.csv`.",
        "- Offline audit only: no network access, no image download, no source-record mutation, no frontend rebuild.",
        "- All records remain IMG02; this audit does not grant IMG01/IMG03 rights state.",
        "",
        "## Results",
        "",
        f"- Records audited: {total}",
        *bullet_counts(readiness),
        "",
        "## Macro-region distribution",
        "",
        *bullet_counts(regions),
        "",
        "## Ready queue by macro-region",
        "",
        *bullet_counts(ready_regions),
        "",
        "## Authority tiers",
        "",
        *bullet_counts(authority),
        "",
        "## Geography precision",
        "",
        *bullet_counts(geo_precision),
        "",
        "## Geography repair needed",
        "",
        *bullet_counts(geo_repairs),
        "",
        "## Main risk flags",
        "",
        *bullet_counts(risk_flags, 20),
        "",
        "## Design signal terms",
        "",
        *bullet_counts(design_terms, 20),
        "",
        "## Ready queue examples",
        "",
    ]

    if ready_examples:
        lines.extend(
            [
                "| capture_id | source | region | score | design terms |",
                "| --- | --- | --- | ---: | --- |",
            ]
        )
        for row in ready_examples:
            lines.append(
                "| {capture_id} | {source_name} | {macro_region} / {country_or_region} | {quality_score} | {design_signal_terms} |".format(
                    **row
                )
            )
    else:
        lines.append("- None.")

    lines.extend(["", "## Quarantine examples", ""])
    if quarantine_examples:
        lines.extend(
            [
                "| capture_id | source | reason |",
                "| --- | --- | --- |",
            ]
        )
        for row in quarantine_examples:
            lines.append(
                "| {capture_id} | {source_name} | {risk_flags} |".format(
                    **row
                )
            )
    else:
        lines.append("- None.")

    if geo_repairs.get("true", 0):
        geography_interpretation = [
            "- `source_place_text` carries country-level geography for this batch; the source-summary layer still has overbroad country buckets that should be repaired upstream before rebuild.",
        ]
    else:
        geography_interpretation = [
            "- Source-summary geography now matches the country-level `source_place_text` for this batch; the remaining blockers are design relevance, source authority, and object-level review.",
        ]

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- The batch has useful under-covered-region leads, but it is not safe to count all {len(detail_rows)} records as successful active sources.",
            "- `ready_for_item_review` records should enter a small item/surface review pass first; `manual_review_before_surface` records need geography and design-relevance confirmation.",
            "- `quarantine_not_counted` records should not be included in success totals or rebuild inputs without source replacement or manual repair.",
            *geography_interpretation,
            "",
            "## Output files",
            "",
            "- `data/nonmainstream_item_image_capture_quality_v1.csv`",
            "- `data/nonmainstream_item_image_capture_quality_summary_v1.csv`",
            "- `data/nonmainstream_item_image_capture_ready_queue_v1.csv`",
            "- `data/nonmainstream_item_image_capture_manual_review_v1.csv`",
            "- `data/nonmainstream_item_image_capture_quarantine_v1.csv`",
        ]
    )
    return "\n".join(lines) + "\n"


def build_summary_lookup(summary_rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row.get("source_id", ""), row.get("source_name", "")): row
        for row in summary_rows
    }


def main() -> None:
    records = read_csv(INPUT_RECORDS)
    summaries = build_summary_lookup(read_csv(INPUT_SUMMARY))

    detail_rows = [
        classify_row(
            row,
            summaries.get((row.get("source_id", ""), row.get("source_name", "")), {}),
        )
        for row in records
    ]

    fieldnames = [
        "capture_id",
        "source_id",
        "source_name",
        "source_identifier",
        "source_record_url",
        "source_title",
        "source_place_text",
        "summary_macro_region",
        "summary_country_or_region",
        "macro_region",
        "country_or_region",
        "geo_precision",
        "geo_repair_needed",
        "image_presence_code",
        "image_url_detected",
        "quality_score",
        "design_signal_score",
        "design_signal_terms",
        "authority_score",
        "authority_tier",
        "authority_terms",
        "text_evidence_chars",
        "risk_flags",
        "surface_readiness",
        "recommended_action",
        "rights_boundary",
    ]

    ready_rows = [
        row for row in detail_rows if row["surface_readiness"] == "ready_for_item_review"
    ]
    manual_rows = [
        row
        for row in detail_rows
        if row["surface_readiness"] == "manual_review_before_surface"
    ]
    quarantine_rows = [
        row
        for row in detail_rows
        if row["surface_readiness"] == "quarantine_not_counted"
    ]

    write_csv(OUTPUT_DETAIL, detail_rows, fieldnames)
    write_csv(OUTPUT_READY, ready_rows, fieldnames)
    write_csv(OUTPUT_MANUAL, manual_rows, fieldnames)
    write_csv(OUTPUT_QUARANTINE, quarantine_rows, fieldnames)

    summary: list[dict[str, Any]] = [
        {"metric_group": "input", "metric": "records_sha256", "value": sha256(INPUT_RECORDS)},
        {"metric_group": "input", "metric": "source_summary_sha256", "value": sha256(INPUT_SUMMARY)},
        {"metric_group": "count", "metric": "records_audited", "value": len(detail_rows)},
        {"metric_group": "count", "metric": "ready_for_item_review", "value": len(ready_rows)},
        {"metric_group": "count", "metric": "manual_review_before_surface", "value": len(manual_rows)},
        {"metric_group": "count", "metric": "quarantine_not_counted", "value": len(quarantine_rows)},
    ]
    summary.extend(counter_rows("surface_readiness", Counter(row["surface_readiness"] for row in detail_rows)))
    summary.extend(counter_rows("macro_region", Counter(row["macro_region"] for row in detail_rows)))
    summary.extend(
        counter_rows(
            "summary_macro_region",
            Counter(row["summary_macro_region"] for row in detail_rows),
        )
    )
    summary.extend(counter_rows("geo_precision", Counter(row["geo_precision"] for row in detail_rows)))
    summary.extend(
        counter_rows(
            "geo_repair_needed",
            Counter(str(row["geo_repair_needed"]).lower() for row in detail_rows),
        )
    )
    summary.extend(
        counter_rows(
            "ready_macro_region",
            Counter(row["macro_region"] for row in ready_rows),
        )
    )
    summary.extend(counter_rows("authority_tier", Counter(row["authority_tier"] for row in detail_rows)))
    flags = Counter()
    for row in detail_rows:
        for flag in str(row["risk_flags"]).split("; "):
            if flag:
                flags[flag] += 1
    summary.extend(counter_rows("risk_flag", flags))

    write_csv(OUTPUT_SUMMARY, summary, ["metric_group", "metric", "value"])
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(build_report(detail_rows, summary), encoding="utf-8")

    print(f"Audited records: {len(detail_rows)}")
    print(f"Ready for item review: {len(ready_rows)}")
    print(f"Manual review before surface: {len(manual_rows)}")
    print(f"Quarantine / not counted: {len(quarantine_rows)}")
    print(f"Wrote {OUTPUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
