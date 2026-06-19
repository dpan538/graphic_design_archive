#!/usr/bin/env python3
"""Audit the pre-freeze candidate payload without mutating release outputs."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
PAYLOAD = ROOT / "generated" / "public_surfaces_prefreeze_candidate_v1.json"

SUMMARY = DATA / "prefreeze_candidate_release_snapshot_v1.csv"
PERIOD = DATA / "prefreeze_candidate_period_breakdown_v1.csv"
REGION = DATA / "prefreeze_candidate_region_breakdown_v1.csv"
SHEETS = DATA / "prefreeze_candidate_sheet_counts_v1.csv"
YEAR_BUCKETS = DATA / "prefreeze_candidate_year_bucket_breakdown_v1.csv"
WARNINGS = DATA / "prefreeze_candidate_review_warnings_v1.csv"
REPORT = DOCS / "PREFREEZE_CANDIDATE_EVALUATION_v1.md"

RELEASE_SOURCE_TARGET = 20000
MIN_RELEASE_SOURCE_COVERAGE = 80
MIN_OBJECT_SOURCE_VISIBLE = 99
MIN_OBJECT_VERIFIED_OPEN = 95
MIN_OBJECT_WEIGHTED_PUBLICATION = 95
MAX_OBJECT_IMG04 = 10
MAX_2025_2026_RATE = 12

PERIOD_SURFACE_TARGETS = {
    "pre_1930": 1700,
    "1930_1970": 2000,
    "1970_2000": 2200,
    "2000_2026": 2600,
}

REGION_SURFACE_TARGETS = {
    "Western and Central Europe": 550,
    "Eastern Europe, Balkans, and Central/Eastern socialist contexts": 650,
    "North America": 450,
    "Latin America and the Caribbean": 850,
    "East Asia": 750,
    "Southeast Asia": 800,
    "South Asia": 750,
    "Middle East and North Africa": 750,
    "Africa": 750,
    "Oceania and Pacific": 450,
    "Global / transnational": 400,
    "Unresolved region": 250,
}

PUBLICATION_WEIGHTS = {"IMG03": 1.0, "IMG02": 0.55, "IMG01": 0.3, "IMG00": 0.0, "IMG04": 0.0}
VISIBLE_STATES = {"IMG01", "IMG02", "IMG03"}
OPEN_STATES = {"IMG03"}

REGION_ALIASES = {
    "Western/Central Europe": "Western and Central Europe",
    "Western Europe": "Western and Central Europe",
    "Central Europe": "Western and Central Europe",
    "Europe": "Western and Central Europe",
    "Eastern Europe": "Eastern Europe, Balkans, and Central/Eastern socialist contexts",
    "Eastern Europe / Caucasus": "Eastern Europe, Balkans, and Central/Eastern socialist contexts",
    "Caucasus": "Eastern Europe, Balkans, and Central/Eastern socialist contexts",
    "Latin America": "Latin America and the Caribbean",
    "Latin America / Caribbean": "Latin America and the Caribbean",
    "Caribbean": "Latin America and the Caribbean",
    "MENA": "Middle East and North Africa",
    "Middle East": "Middle East and North Africa",
    "North Africa": "Middle East and North Africa",
    "Global": "Global / transnational",
    "Global / web / transnational": "Global / transnational",
    "Global / release gate expansion": "Global / transnational",
    "Global South / release gate expansion": "Global / transnational",
}

COUNTRY_MACRO_FALLBACK = {
    "United Kingdom": "Western and Central Europe",
    "France": "Western and Central Europe",
    "Germany": "Western and Central Europe",
    "Italy": "Western and Central Europe",
    "Belgium": "Western and Central Europe",
    "Netherlands": "Western and Central Europe",
    "Switzerland": "Western and Central Europe",
    "Russia": "Eastern Europe, Balkans, and Central/Eastern socialist contexts",
    "Ukraine": "Eastern Europe, Balkans, and Central/Eastern socialist contexts",
    "Poland": "Eastern Europe, Balkans, and Central/Eastern socialist contexts",
    "Romania": "Eastern Europe, Balkans, and Central/Eastern socialist contexts",
    "Bulgaria": "Eastern Europe, Balkans, and Central/Eastern socialist contexts",
    "Armenia": "Eastern Europe, Balkans, and Central/Eastern socialist contexts",
    "Georgia": "Eastern Europe, Balkans, and Central/Eastern socialist contexts",
    "Azerbaijan": "Eastern Europe, Balkans, and Central/Eastern socialist contexts",
    "Kazakhstan": "Eastern Europe, Balkans, and Central/Eastern socialist contexts",
    "Kyrgyzstan": "Eastern Europe, Balkans, and Central/Eastern socialist contexts",
    "Tajikistan": "Eastern Europe, Balkans, and Central/Eastern socialist contexts",
    "Turkmenistan": "Eastern Europe, Balkans, and Central/Eastern socialist contexts",
    "Uzbekistan": "Eastern Europe, Balkans, and Central/Eastern socialist contexts",
    "United States": "North America",
    "Canada": "North America",
    "Mexico": "Latin America and the Caribbean",
    "Cuba": "Latin America and the Caribbean",
    "Brazil": "Latin America and the Caribbean",
    "Argentina": "Latin America and the Caribbean",
    "Chile": "Latin America and the Caribbean",
    "Colombia": "Latin America and the Caribbean",
    "Bolivia": "Latin America and the Caribbean",
    "Peru": "Latin America and the Caribbean",
    "Uruguay": "Latin America and the Caribbean",
    "Venezuela": "Latin America and the Caribbean",
    "China": "East Asia",
    "Japan": "East Asia",
    "Korean Peninsula": "East Asia",
    "South Korea": "East Asia",
    "Taiwan": "East Asia",
    "Indonesia": "Southeast Asia",
    "Malaysia": "Southeast Asia",
    "Philippines": "Southeast Asia",
    "Singapore": "Southeast Asia",
    "Thailand": "Southeast Asia",
    "Vietnam": "Southeast Asia",
    "Bangladesh": "South Asia",
    "India": "South Asia",
    "Nepal": "South Asia",
    "Pakistan": "South Asia",
    "Sri Lanka": "South Asia",
    "Algeria": "Middle East and North Africa",
    "Egypt": "Middle East and North Africa",
    "Iran": "Middle East and North Africa",
    "Iraq": "Middle East and North Africa",
    "Lebanon": "Middle East and North Africa",
    "Morocco": "Middle East and North Africa",
    "Palestine": "Middle East and North Africa",
    "Turkey": "Middle East and North Africa",
    "Ethiopia": "Africa",
    "Ghana": "Africa",
    "Kenya": "Africa",
    "Nigeria": "Africa",
    "Senegal": "Africa",
    "South Africa": "Africa",
    "Tanzania": "Africa",
    "Australia": "Oceania and Pacific",
    "Aotearoa New Zealand": "Oceania and Pacific",
}

SUMMARY_FIELDS = ["metric", "value", "gate", "notes"]
PERIOD_FIELDS = [
    "period_band",
    "surface_count",
    "main_sheet_count",
    "source_visible_count",
    "verified_open_count",
    "img04_count",
    "desired_surface_target",
    "surface_balance_rate",
]
REGION_FIELDS = [
    "region_group",
    "surface_count",
    "main_sheet_count",
    "source_visible_count",
    "verified_open_count",
    "img04_count",
    "desired_surface_target",
    "surface_balance_rate",
]
SHEET_FIELDS = ["metric", "value", "notes"]
YEAR_FIELDS = [
    "year_bucket",
    "surface_count",
    "main_sheet_count",
    "source_visible_count",
    "verified_open_count",
    "img04_count",
    "dominant_source_name",
    "dominant_source_count",
]
WARNING_FIELDS = ["warning_type", "count", "rate", "sample_surface_ids", "notes"]


def clean(value: object) -> str:
    return str(value or "").strip()


def pct(value: float, total: float) -> str:
    if total <= 0:
        return "0.00"
    return f"{(value / total) * 100:.2f}"


def gate(ok: bool) -> str:
    return "pass" if ok else "fail"


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def macro_region_lookup() -> dict[str, str]:
    """Map country/context labels to launch macro-region labels."""
    region_rows = read_csv(DATA / "regions.csv")
    geo_rows = read_csv(DATA / "geographies.csv")
    by_id = {row.get("region_id", ""): row for row in region_rows}

    def macro_for_region(region_id: str) -> str:
        row = by_id.get(region_id, {})
        if not row:
            return ""
        if row.get("region_type") == "macro_region":
            return clean(row.get("region_name"))
        parent = row.get("parent_region_id", "")
        parent_row = by_id.get(parent, {})
        return clean(parent_row.get("region_name")) or clean(row.get("region_name"))

    lookup: dict[str, str] = {}
    for row in region_rows:
        name = clean(row.get("region_name"))
        macro = macro_for_region(row.get("region_id", ""))
        if name and macro:
            lookup[name] = macro
    for row in geo_rows:
        name = clean(row.get("name"))
        macro = macro_for_region(row.get("region_id", ""))
        if name and macro:
            lookup[name] = macro
    for alias, target in REGION_ALIASES.items():
        lookup[alias] = target
    for label, target in COUNTRY_MACRO_FALLBACK.items():
        lookup.setdefault(label, target)
    return lookup


def image_state(surface: dict[str, Any]) -> str:
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    return clean(image.get("state")) or "IMG00"


def rights_reviewed(surface: dict[str, Any]) -> bool:
    review = surface.get("reviewGates") if isinstance(surface.get("reviewGates"), dict) else {}
    return review.get("rightsReviewed") is True


def year(surface: dict[str, Any]) -> int | None:
    for field in ("dateEnd", "dateStart"):
        try:
            return int(surface.get(field))
        except (TypeError, ValueError):
            continue
    return None


def period_band(surface: dict[str, Any]) -> str:
    y = year(surface)
    if y is None:
        return "undated_or_unparsed"
    if y <= 1930:
        return "pre_1930"
    if y <= 1970:
        return "1930_1970"
    if y <= 2000:
        return "1970_2000"
    if y <= 2026:
        return "2000_2026"
    return "post_2026_or_error"


def five_year_bucket(surface: dict[str, Any]) -> str:
    y = year(surface)
    if y is None:
        return "undated_or_unparsed"
    if y > 2026:
        return "post_2026_or_error"
    start = (y // 5) * 5
    return f"{start}-{start + 4}"


def region(surface: dict[str, Any], lookup: dict[str, str]) -> str:
    folders = surface.get("folders") if isinstance(surface.get("folders"), list) else []
    for folder in folders:
        if isinstance(folder, dict) and folder.get("type") == "region":
            label = clean(folder.get("title")).split("/")[0].strip()
            if not label:
                return "Unresolved region"
            return lookup.get(label) or REGION_ALIASES.get(label, label)
    return "Unresolved region"


def normalized_url(value: str) -> str:
    text = clean(value).rstrip("/")
    return re.sub(r"[?#].*$", "", text.lower())


def object_key(surface: dict[str, Any]) -> str:
    source_url = normalized_url(clean(surface.get("sourceUrl")))
    if source_url:
        return f"url:{source_url}"
    record_id = clean(surface.get("sourceRecordId"))
    if record_id:
        return f"record:{record_id}"
    return "fallback:" + "|".join(
        [
            clean(surface.get("sourceName")),
            clean(surface.get("title")).lower(),
            clean(surface.get("dateText")),
        ]
    )


def reading_chars(surface: dict[str, Any]) -> int:
    return len(
        " ".join(
            clean(surface.get(key))
            for key in (
                "descriptionSummary",
                "sourceDescription",
                "historicalContextNote",
                "classificationRationale",
                "uncertaintyNote",
                "citationBasis",
            )
            if clean(surface.get(key))
        )
    )


def source_text_chars(surface: dict[str, Any]) -> int:
    return len(
        " ".join(
            clean(surface.get(key))
            for key in ("sourceDescription", "sourceNotes", "sourceSubjects", "ocrOrExcerpt", "sourceDescriptionRaw")
            if clean(surface.get(key))
        )
    )


def balance(count: int, target: int) -> float:
    return min(count / target, 1.0) if target else 0.0


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def warning_sample(surfaces: list[dict[str, Any]]) -> str:
    return ";".join(clean(surface.get("surfaceId")) for surface in surfaces[:12])


def issue_warnings(surfaces: list[dict[str, Any]]) -> list[dict[str, str]]:
    total = len(surfaces)
    year_2025_2026 = [surface for surface in surfaces if year(surface) in {2025, 2026}]
    future = [surface for surface in surfaces if (year(surface) or 0) > 2026]
    stamps_after_2010 = [
        surface
        for surface in surfaces
        if (year(surface) or 0) >= 2010
        and re.search(r"\bstamp|commemorative|postage\b", " ".join(map(clean, [surface.get("title"), surface.get("sourceDescription"), surface.get("sourceSubjects")])).lower())
    ]
    event_photo = [
        surface
        for surface in surfaces
        if re.search(r"\bevent photo|photograph of|opening reception|conference|workshop|talk\b", " ".join(map(clean, [surface.get("title"), surface.get("sourceDescription"), surface.get("sourceSubjects")])).lower())
    ]
    rows = [
        {
            "warning_type": "year_2025_2026_high_share",
            "count": str(len(year_2025_2026)),
            "rate": pct(len(year_2025_2026), total),
            "sample_surface_ids": warning_sample(year_2025_2026),
            "notes": "2025-2026 should be inspected for capture-date leakage and weak contemporary research value.",
        },
        {
            "warning_type": "post_2026_or_error",
            "count": str(len(future)),
            "rate": pct(len(future), total),
            "sample_surface_ids": warning_sample(future),
            "notes": "Future dates are release blockers.",
        },
        {
            "warning_type": "post_2010_stamp_like",
            "count": str(len(stamps_after_2010)),
            "rate": pct(len(stamps_after_2010), total),
            "sample_surface_ids": warning_sample(stamps_after_2010),
            "notes": "Recent commemorative stamp-like rows should be reduced unless design relevance is strong.",
        },
        {
            "warning_type": "event_photo_like",
            "count": str(len(event_photo)),
            "rate": pct(len(event_photo), total),
            "sample_surface_ids": warning_sample(event_photo),
            "notes": "Event/photo memory material should usually become card/support material, not design-object main sheets.",
        },
    ]
    return rows


def main() -> None:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    surfaces = payload.get("surfaces", [])
    dossiers = payload.get("researchDossiers", [])
    region_lookup = macro_region_lookup()
    total = len(surfaces)
    states = Counter(image_state(surface) for surface in surfaces)
    source_names = {clean(surface.get("sourceName")) for surface in surfaces if clean(surface.get("sourceName"))}

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for surface in surfaces:
        groups[object_key(surface)].append(surface)
    object_total = len(groups)
    object_visible = sum(1 for group in groups.values() if any(image_state(surface) in VISIBLE_STATES for surface in group))
    object_open = sum(1 for group in groups.values() if any(image_state(surface) in OPEN_STATES and rights_reviewed(surface) for surface in group))
    object_weight = sum(max(PUBLICATION_WEIGHTS.get(image_state(surface), 0.0) for surface in group) for group in groups.values())
    object_best_states = Counter(
        max((image_state(surface) for surface in group), key=lambda state: PUBLICATION_WEIGHTS.get(state, 0.0))
        for group in groups.values()
    )
    object_img04 = object_best_states.get("IMG04", 0)

    source_visible = sum(1 for surface in surfaces if image_state(surface) in VISIBLE_STATES)
    verified_open = sum(1 for surface in surfaces if image_state(surface) in OPEN_STATES and rights_reviewed(surface))
    main_sheets = [surface for surface in surfaces if clean(surface.get("publicationRole")) == "main_sheet"]
    sub_or_support = [surface for surface in surfaces if clean(surface.get("publicationRole")) != "main_sheet"]
    text_sheets = [surface for surface in surfaces if clean(surface.get("templateId")) == "sheet.text.v0"]
    rich_text_surfaces = [surface for surface in surfaces if reading_chars(surface) >= 1200]
    weak_text_main = [surface for surface in main_sheets if reading_chars(surface) < 700 and source_text_chars(surface) < 350]

    dossier_text_pages = sum(
        1
        for dossier in dossiers
        for page in dossier.get("pageSequence", [])
        if isinstance(page, dict) and page.get("pageType") == "text_page"
    )
    dossier_support_pages = sum(
        1
        for dossier in dossiers
        for page in dossier.get("pageSequence", [])
        if isinstance(page, dict) and page.get("pageType") in {"sub_sheet", "card", "appendix", "child_source_record"}
    )
    dossiers_gt2_support = sum(
        1
        for dossier in dossiers
        if sum(1 for page in dossier.get("pageSequence", []) if isinstance(page, dict) and page.get("pageType") in {"sub_sheet", "card", "appendix", "child_source_record"}) > 2
    )
    dossiers_gt5_text = sum(
        1
        for dossier in dossiers
        if sum(1 for page in dossier.get("pageSequence", []) if isinstance(page, dict) and page.get("pageType") == "text_page") > 5
    )

    release_source_coverage = float(pct(len(source_names), RELEASE_SOURCE_TARGET))
    object_visible_rate = float(pct(object_visible, object_total))
    object_open_rate = float(pct(object_open, object_total))
    object_publication_rate = float(pct(object_weight, object_total))
    object_img04_rate = float(pct(object_img04, object_total))
    year_2025_2026_rate = float(pct(sum(1 for surface in surfaces if year(surface) in {2025, 2026}), total))

    period_stats: dict[str, Counter[str]] = defaultdict(Counter)
    region_stats: dict[str, Counter[str]] = defaultdict(Counter)
    year_stats: dict[str, Counter[str]] = defaultdict(Counter)
    year_sources: dict[str, Counter[str]] = defaultdict(Counter)
    for surface in surfaces:
        for stats in (period_stats[period_band(surface)], region_stats[region(surface, region_lookup)], year_stats[five_year_bucket(surface)]):
            stats["surface_count"] += 1
            if clean(surface.get("publicationRole")) == "main_sheet":
                stats["main_sheet_count"] += 1
            if image_state(surface) in VISIBLE_STATES:
                stats["source_visible_count"] += 1
            if image_state(surface) in OPEN_STATES and rights_reviewed(surface):
                stats["verified_open_count"] += 1
            if image_state(surface) == "IMG04":
                stats["img04_count"] += 1
        year_sources[five_year_bucket(surface)][clean(surface.get("sourceName"))] += 1

    period_rows = []
    for band in list(PERIOD_SURFACE_TARGETS) + sorted(set(period_stats) - set(PERIOD_SURFACE_TARGETS)):
        stats = period_stats.get(band, Counter())
        target = PERIOD_SURFACE_TARGETS.get(band, 250)
        period_rows.append(
            {
                "period_band": band,
                "surface_count": stats["surface_count"],
                "main_sheet_count": stats["main_sheet_count"],
                "source_visible_count": stats["source_visible_count"],
                "verified_open_count": stats["verified_open_count"],
                "img04_count": stats["img04_count"],
                "desired_surface_target": target,
                "surface_balance_rate": pct(stats["surface_count"], target),
            }
        )
    region_rows = []
    for band in sorted(set(REGION_SURFACE_TARGETS) | set(region_stats)):
        stats = region_stats.get(band, Counter())
        target = REGION_SURFACE_TARGETS.get(band, 250)
        region_rows.append(
            {
                "region_group": band,
                "surface_count": stats["surface_count"],
                "main_sheet_count": stats["main_sheet_count"],
                "source_visible_count": stats["source_visible_count"],
                "verified_open_count": stats["verified_open_count"],
                "img04_count": stats["img04_count"],
                "desired_surface_target": target,
                "surface_balance_rate": pct(stats["surface_count"], target),
            }
        )
    year_rows = []
    for bucket, stats in sorted(year_stats.items()):
        dominant = year_sources[bucket].most_common(1)
        year_rows.append(
            {
                "year_bucket": bucket,
                "surface_count": stats["surface_count"],
                "main_sheet_count": stats["main_sheet_count"],
                "source_visible_count": stats["source_visible_count"],
                "verified_open_count": stats["verified_open_count"],
                "img04_count": stats["img04_count"],
                "dominant_source_name": dominant[0][0] if dominant else "",
                "dominant_source_count": dominant[0][1] if dominant else 0,
            }
        )

    period_balance = average([balance(int(row["surface_count"]), int(row["desired_surface_target"])) for row in period_rows if row["period_band"] in PERIOD_SURFACE_TARGETS])
    region_balance = average([balance(int(row["surface_count"]), int(row["desired_surface_target"])) for row in region_rows if row["region_group"] in REGION_SURFACE_TARGETS])
    strict_distribution_adjusted = min(release_source_coverage / 100, period_balance, region_balance) * 100

    independent_2005_2025 = [
        surface
        for surface in surfaces
        if 2005 <= (year(surface) or 0) <= 2025
        and re.search(r"\bstudio|collective|school|academy|university|institute|independent|design platform|biennial|festival\b", " ".join(map(clean, [surface.get("sourceName"), surface.get("title"), surface.get("sourceDescription")])).lower())
    ]

    summary_rows = [
        {"metric": "candidate_public_surfaces", "value": str(total), "gate": "", "notes": "Candidate payload only; official payload unchanged."},
        {"metric": "candidate_active_public_sources", "value": str(len(source_names)), "gate": gate(release_source_coverage >= MIN_RELEASE_SOURCE_COVERAGE), "notes": f"Distinct sourceName values; target={RELEASE_SOURCE_TARGET}."},
        {"metric": "candidate_release_source_coverage_rate", "value": f"{release_source_coverage:.2f}", "gate": gate(release_source_coverage >= MIN_RELEASE_SOURCE_COVERAGE), "notes": "Candidate source-name coverage against 20,000 final target."},
        {"metric": "candidate_surface_source_visible_rate", "value": pct(source_visible, total), "gate": "", "notes": "Surface-level IMG01/IMG02/IMG03."},
        {"metric": "candidate_surface_verified_open_rate", "value": pct(verified_open, total), "gate": "", "notes": "Surface-level IMG03 with rightsReviewed=true."},
        {"metric": "candidate_object_count", "value": str(object_total), "gate": "", "notes": "Object-level grouping; repeated photos/views count once."},
        {"metric": "candidate_object_source_visible_rate", "value": f"{object_visible_rate:.2f}", "gate": gate(object_visible_rate >= MIN_OBJECT_SOURCE_VISIBLE), "notes": f"Gate target={MIN_OBJECT_SOURCE_VISIBLE}%."},
        {"metric": "candidate_object_verified_open_rate", "value": f"{object_open_rate:.2f}", "gate": gate(object_open_rate >= MIN_OBJECT_VERIFIED_OPEN), "notes": f"Gate target={MIN_OBJECT_VERIFIED_OPEN}%."},
        {"metric": "candidate_object_weighted_publication_grade_rate", "value": f"{object_publication_rate:.2f}", "gate": gate(object_publication_rate >= MIN_OBJECT_WEIGHTED_PUBLICATION), "notes": "Object-level max image weight; repeated photos count once."},
        {"metric": "candidate_object_img04_rate", "value": f"{object_img04_rate:.2f}", "gate": gate(object_img04_rate <= MAX_OBJECT_IMG04), "notes": f"Gate max={MAX_OBJECT_IMG04}%."},
        {"metric": "candidate_period_surface_balance_rate", "value": f"{period_balance * 100:.2f}", "gate": "", "notes": "Average surface fill against period targets."},
        {"metric": "candidate_region_surface_balance_rate", "value": f"{region_balance * 100:.2f}", "gate": "", "notes": "Average surface fill against regional targets."},
        {"metric": "candidate_strict_distribution_adjusted_source_coverage_rate", "value": f"{strict_distribution_adjusted:.2f}", "gate": "", "notes": "min(source coverage, period balance, region balance)."},
        {"metric": "candidate_2025_2026_surface_rate", "value": f"{year_2025_2026_rate:.2f}", "gate": gate(year_2025_2026_rate <= MAX_2025_2026_RATE), "notes": "High 2025/2026 share is suspicious and should be audited for date leakage."},
        {"metric": "candidate_independent_studio_school_platform_2005_2025_count", "value": str(len(independent_2005_2025)), "gate": "", "notes": "Heuristic count for contemporary studios, schools, platforms, festivals, and collectives."},
    ]
    for state, count in sorted(states.items()):
        summary_rows.append({"metric": f"candidate_surface_image_state:{state}", "value": str(count), "gate": "", "notes": "Surface image state distribution."})

    sheet_rows = [
        {"metric": "main_sheet_count", "value": str(len(main_sheets)), "notes": "publicationRole=main_sheet."},
        {"metric": "sub_or_support_surface_count", "value": str(len(sub_or_support)), "notes": "All non-main public surfaces."},
        {"metric": "independent_text_sheet_count", "value": str(len(text_sheets)), "notes": "templateId=sheet.text.v0."},
        {"metric": "rich_text_surface_count_ge1200_chars", "value": str(len(rich_text_surfaces)), "notes": "Reading/support text >= 1200 chars."},
        {"metric": "weak_text_main_sheet_count", "value": str(len(weak_text_main)), "notes": "Main sheets with weak source/generated text."},
        {"metric": "research_dossier_count", "value": str(len(dossiers)), "notes": "Dossier anchors in candidate payload."},
        {"metric": "dossier_text_page_count", "value": str(dossier_text_pages), "notes": "text_page entries in researchDossiers."},
        {"metric": "dossier_sub_card_appendix_count", "value": str(dossier_support_pages), "notes": "sub_sheet/card/appendix/child_source_record entries."},
        {"metric": "dossiers_with_more_than_two_support_pages", "value": str(dossiers_gt2_support), "notes": "Research packets with >2 sub/card/appendix/child pages."},
        {"metric": "dossiers_with_more_than_five_text_pages", "value": str(dossiers_gt5_text), "notes": "Research packets with >5 text pages."},
    ]

    warning_rows = issue_warnings(surfaces)
    write_csv(SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_csv(PERIOD, period_rows, PERIOD_FIELDS)
    write_csv(REGION, region_rows, REGION_FIELDS)
    write_csv(SHEETS, sheet_rows, SHEET_FIELDS)
    write_csv(YEAR_BUCKETS, year_rows, YEAR_FIELDS)
    write_csv(WARNINGS, warning_rows, WARNING_FIELDS)

    failed = [row for row in summary_rows if row["gate"] == "fail"]
    weakest_years = sorted(year_rows, key=lambda row: int(row["surface_count"]))[:12]
    top_years = sorted(year_rows, key=lambda row: int(row["surface_count"]), reverse=True)[:12]
    weakest_regions = sorted(region_rows, key=lambda row: int(row["surface_count"]))[:12]
    lines = [
        "# Prefreeze Candidate Evaluation v1",
        "",
        "Scope: candidate public-surface payload generated from all local capture records after P0 pre-freeze exclusions. Official payload and frontend mirrors are unchanged.",
        "",
        "## Gate Summary",
        "",
    ]
    for row in summary_rows:
        if row["gate"]:
            lines.append(f"- {row['metric']}: {row['value']} · {row['gate']} ({row['notes']})")
    lines.extend(["", "## Core Metrics", ""])
    for row in summary_rows[:15]:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Sheet Structure", ""])
    for row in sheet_rows:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Weakest 5-Year Buckets", ""])
    for row in weakest_years:
        lines.append(f"- {row['year_bucket']}: surfaces={row['surface_count']}, main={row['main_sheet_count']}, open={row['verified_open_count']}")
    lines.extend(["", "## Heaviest 5-Year Buckets", ""])
    for row in top_years:
        lines.append(
            f"- {row['year_bucket']}: surfaces={row['surface_count']}, dominant_source={row['dominant_source_name']} ({row['dominant_source_count']})"
        )
    lines.extend(["", "## Weakest Regions By Surface Count", ""])
    for row in weakest_regions:
        lines.append(f"- {row['region_group']}: surfaces={row['surface_count']}, visible={row['source_visible_count']}, open={row['verified_open_count']}")
    lines.extend(["", "## Review Warnings", ""])
    for row in warning_rows:
        lines.append(f"- {row['warning_type']}: count={row['count']}, rate={row['rate']}% ({row['notes']})")
    lines.extend(["", "## Failed Gates", ""])
    if failed:
        for row in failed:
            lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- No image files were downloaded.",
            "- IMG01/IMG03 were not upgraded by heuristic, LLM, TOS, or platform signals.",
            "- Candidate metrics are for deciding the next cleaning/rebuild focus; they are not a release promotion.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"candidate_public_surfaces={total}")
    print(f"candidate_active_public_sources={len(source_names)}")
    print(f"candidate_object_source_visible_rate={object_visible_rate:.2f}%")
    print(f"candidate_object_verified_open_rate={object_open_rate:.2f}%")
    print(f"candidate_object_img04_rate={object_img04_rate:.2f}%")
    print(f"candidate_strict_distribution_adjusted_source_coverage_rate={strict_distribution_adjusted:.2f}%")
    print(f"wrote {SUMMARY.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
