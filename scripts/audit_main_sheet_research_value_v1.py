#!/usr/bin/env python3
"""Audit whether main sheets have enough research value to stay main sheets.

This is a diagnostic layer only. It does not demote, promote, or mutate public
surfaces. Impact scores are internal triage signals and do not upgrade rights,
authorship, source authority, or image state.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

PAYLOAD = ROOT / "generated" / "public_surfaces_v1.json"
GROUP_CANDIDATES = DATA / "surface_group_candidates_v1.csv"
REGION_IMPACT = DATA / "nonmainstream_region_impact_ratings_1990_2026_v1.csv"
SOURCE_PROFILE_IMPACT = DATA / "nonmainstream_source_profile_impact_ratings_1990_2026_v1.csv"

OUT = DATA / "main_sheet_research_value_audit_v1.csv"
PERIOD_OUT = DATA / "main_sheet_research_value_period_breakdown_v1.csv"
REPORT = DOCS / "MAIN_SHEET_RESEARCH_VALUE_AUDIT_v1.md"

FIELDS = [
    "surface_id",
    "title",
    "period_band",
    "macro_region",
    "source_name",
    "template_id",
    "publication_role",
    "image_state",
    "source_text_chars",
    "generated_text_chars",
    "total_reading_chars",
    "impact_score",
    "impact_rating",
    "impact_basis",
    "group_candidate_count",
    "max_group_member_count",
    "strong_group_candidate",
    "research_value_score",
    "recommended_action",
    "action_reason",
]

PERIOD_FIELDS = [
    "period_band",
    "main_sheet_count",
    "keep_main",
    "keep_main_add_editorial_text",
    "demote_to_sub",
    "demote_to_card",
    "source_dossier_or_register",
    "promote_text_or_appendix",
    "median_source_text_chars",
    "median_research_value_score",
]

UNDERCOVERED_REGIONS = {
    "Africa",
    "East Asia",
    "Southeast Asia",
    "South Asia",
    "Middle East and North Africa",
    "Latin America",
    "Latin America and the Caribbean",
    "Eastern Europe",
    "Eastern Europe / Caucasus",
    "Oceania and Pacific",
    "Mainland China",
}

HIGH_VALUE_TERMS = (
    "advertising",
    "activist",
    "anti-apartheid",
    "book cover",
    "campaign",
    "exhibition",
    "festival",
    "film poster",
    "graphic design",
    "identity",
    "magazine cover",
    "poster",
    "print",
    "publication",
    "stamp",
    "typography",
    "visual communication",
    "zine",
)


def clean(value: object) -> str:
    return str(value or "").strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def period_band(surface: dict) -> str:
    try:
        year = int(surface.get("dateEnd") or surface.get("dateStart"))
    except (TypeError, ValueError):
        return "undated_or_unparsed"
    if year <= 1930:
        return "pre_1930"
    if year <= 1970:
        return "1930_1970"
    if year <= 2000:
        return "1970_2000"
    if year <= 2026:
        return "2000_2026"
    return "post_2026_or_error"


def macro_region(surface: dict) -> str:
    folders = surface.get("folders") if isinstance(surface.get("folders"), list) else []
    for folder in folders:
        if folder.get("type") == "region":
            return clean(folder.get("title")).split("/")[0].strip()
    place = clean(surface.get("sourcePlaceText") or surface.get("placeText"))
    if place:
        return place.split("/")[0].strip()
    return "Unresolved region"


def image_state(surface: dict) -> str:
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    return clean(image.get("state")) or "IMG00"


def source_text(surface: dict) -> str:
    return " ".join(
        clean(surface.get(key))
        for key in (
            "sourceDescription",
            "sourceNotes",
            "sourceSubjects",
            "ocrOrExcerpt",
            "sourceDescriptionRaw",
        )
        if clean(surface.get(key))
    )


def generated_text(surface: dict) -> str:
    return " ".join(
        clean(surface.get(key))
        for key in (
            "descriptionSummary",
            "historicalContextNote",
            "classificationRationale",
            "uncertaintyNote",
            "citationBasis",
        )
        if clean(surface.get(key))
    )


def impact_lookup() -> dict[str, tuple[int, str, str]]:
    lookup: dict[str, tuple[int, str, str]] = {}
    for path in (REGION_IMPACT, SOURCE_PROFILE_IMPACT):
        for row in read_csv(path):
            score = int(float(row.get("impact_score") or 0))
            rating = clean(row.get("impact_rating")) or "C"
            basis = clean(row.get("impact_basis"))
            keys = {
                clean(row.get("capture_id")).lower(),
                clean(row.get("source_name")).lower(),
                clean(row.get("source_title")).lower(),
                clean(row.get("source_record_url")).lower(),
            }
            for key in keys:
                if key and (key not in lookup or score > lookup[key][0]):
                    lookup[key] = (score, rating, basis)
    return lookup


def group_lookup() -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(GROUP_CANDIDATES):
        ids = [part.strip() for part in clean(row.get("member_surface_ids")).split(";") if part.strip()]
        for surface_id in ids:
            groups[surface_id].append(row)
    return groups


def heuristic_impact(surface: dict, region: str) -> tuple[int, str, str]:
    text = " ".join(
        clean(surface.get(key))
        for key in ("title", "descriptionSummary", "sourceDescription", "sourceNotes", "classificationRationale")
    ).lower()
    score = 35
    basis = ["heuristic baseline"]
    if region in UNDERCOVERED_REGIONS:
        score += 15
        basis.append("undercovered region")
    if period_band(surface) == "2000_2026":
        score += 8
        basis.append("internet/contemporary period")
    term_hits = sum(1 for term in HIGH_VALUE_TERMS if term in text)
    if term_hits:
        score += min(20, term_hits * 4)
        basis.append(f"design-term hits={term_hits}")
    if image_state(surface) == "IMG03":
        score += 5
        basis.append("verified open image")
    score = min(score, 95)
    rating = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"
    return score, rating, "; ".join(basis)


def surface_impact(surface: dict, lookup: dict[str, tuple[int, str, str]], region: str) -> tuple[int, str, str]:
    keys = [
        clean(surface.get("sourceRecordId")).lower(),
        clean(surface.get("sourceName")).lower(),
        clean(surface.get("title")).lower(),
        clean(surface.get("sourceUrl")).lower(),
    ]
    found = [lookup[key] for key in keys if key in lookup]
    if found:
        return max(found, key=lambda item: item[0])
    return heuristic_impact(surface, region)


def research_score(surface: dict, source_chars: int, generated_chars: int, impact_score: int, groups: list[dict[str, str]]) -> int:
    state = image_state(surface)
    score = 0
    if state == "IMG03":
        score += 25
    elif state == "IMG02":
        score += 18
    elif state == "IMG01":
        score += 10
    elif state == "IMG04":
        score += 4
    score += min(30, source_chars // 40)
    score += min(15, generated_chars // 180)
    score += min(20, impact_score // 5)
    if groups:
        score += 8
    if any(clean(group.get("confidence")) in {"medium", "high"} for group in groups):
        score += 7
    return min(score, 100)


def recommended_action(
    surface: dict,
    source_chars: int,
    generated_chars: int,
    impact_score: int,
    value_score: int,
    groups: list[dict[str, str]],
) -> tuple[str, str]:
    state = image_state(surface)
    role = clean(surface.get("publicationRole"))
    template = clean(surface.get("templateId"))
    strong_group = any(clean(group.get("confidence")) in {"medium", "high"} and int(group.get("member_count") or 0) >= 3 for group in groups)
    collectionish = re.search(r"\b(collection|registry|source profile|archive profile|catalogue|bibliography)\b", " ".join([clean(surface.get("title")), clean(surface.get("sourceDescription"))]).lower())

    if template == "sheet.text.v0" or (state == "IMG04" and source_chars >= 320 and impact_score >= 60):
        return "promote_text_or_appendix", "Text-forward or image-withheld evidence should become an explicit research text/appendix page."
    if collectionish and state in {"IMG00", "IMG04"}:
        return "source_dossier_or_register", "Collection/source-context record should be a source dossier/register, not an object main."
    if role != "main_sheet":
        return "keep_non_main", "Already not a main sheet; tracked for topology context."
    if source_chars < 160 and impact_score < 60 and not strong_group:
        return "demote_to_card", "Very thin source-derived text and no strong impact/grouping basis."
    if source_chars < 300 and impact_score < 70:
        return "demote_to_sub", "Thin source-derived text and insufficient impact basis for standalone main."
    if strong_group and source_chars < 500 and impact_score < 80:
        return "demote_to_sub", "Likely belongs under a stronger grouped parent rather than standalone main."
    if impact_score >= 75 and source_chars < 500:
        return "keep_main_add_editorial_text", "High-impact or undercovered-region record needs an editorial research text page before release."
    if value_score >= 72 and source_chars >= 300 and state in {"IMG01", "IMG02", "IMG03"}:
        return "keep_main", "Sufficient image/source/text/impact balance for main-sheet treatment."
    if generated_chars >= 900 and source_chars >= 220 and impact_score >= 65:
        return "keep_main_add_editorial_text", "Moderate source text and useful generated context; keep but add reviewed editorial text."
    return "demote_to_sub", "Research value is not yet strong enough for standalone main treatment."


def median(values: list[int]) -> int:
    if not values:
        return 0
    values = sorted(values)
    return values[len(values) // 2]


def main() -> None:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    lookup = impact_lookup()
    groups_by_surface = group_lookup()
    rows: list[dict[str, str]] = []

    for surface in payload.get("surfaces", []):
        region = macro_region(surface)
        src_text = source_text(surface)
        gen_text = generated_text(surface)
        groups = groups_by_surface.get(clean(surface.get("surfaceId")), [])
        impact_score, impact_rating, impact_basis = surface_impact(surface, lookup, region)
        value_score = research_score(surface, len(src_text), len(gen_text), impact_score, groups)
        action, reason = recommended_action(surface, len(src_text), len(gen_text), impact_score, value_score, groups)
        rows.append(
            {
                "surface_id": clean(surface.get("surfaceId")),
                "title": clean(surface.get("title")),
                "period_band": period_band(surface),
                "macro_region": region,
                "source_name": clean(surface.get("sourceName")),
                "template_id": clean(surface.get("templateId")),
                "publication_role": clean(surface.get("publicationRole")),
                "image_state": image_state(surface),
                "source_text_chars": str(len(src_text)),
                "generated_text_chars": str(len(gen_text)),
                "total_reading_chars": str(len(src_text) + len(gen_text)),
                "impact_score": str(impact_score),
                "impact_rating": impact_rating,
                "impact_basis": impact_basis,
                "group_candidate_count": str(len(groups)),
                "max_group_member_count": str(max([int(group.get("member_count") or 0) for group in groups] or [0])),
                "strong_group_candidate": str(any(clean(group.get("confidence")) in {"medium", "high"} for group in groups)).lower(),
                "research_value_score": str(value_score),
                "recommended_action": action,
                "action_reason": reason,
            }
        )

    write_csv(OUT, rows, FIELDS)

    period_rows: list[dict[str, str]] = []
    by_period: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["publication_role"] == "main_sheet":
            by_period[row["period_band"]].append(row)
    for period, period_main_rows in sorted(by_period.items()):
        action_counts = Counter(row["recommended_action"] for row in period_main_rows)
        period_rows.append(
            {
                "period_band": period,
                "main_sheet_count": str(len(period_main_rows)),
                "keep_main": str(action_counts.get("keep_main", 0)),
                "keep_main_add_editorial_text": str(action_counts.get("keep_main_add_editorial_text", 0)),
                "demote_to_sub": str(action_counts.get("demote_to_sub", 0)),
                "demote_to_card": str(action_counts.get("demote_to_card", 0)),
                "source_dossier_or_register": str(action_counts.get("source_dossier_or_register", 0)),
                "promote_text_or_appendix": str(action_counts.get("promote_text_or_appendix", 0)),
                "median_source_text_chars": str(median([int(row["source_text_chars"]) for row in period_main_rows])),
                "median_research_value_score": str(median([int(row["research_value_score"]) for row in period_main_rows])),
            }
        )
    write_csv(PERIOD_OUT, period_rows, PERIOD_FIELDS)

    main_rows = [row for row in rows if row["publication_role"] == "main_sheet"]
    action_counts = Counter(row["recommended_action"] for row in main_rows)
    region_actions: dict[str, Counter[str]] = defaultdict(Counter)
    for row in main_rows:
        region_actions[row["macro_region"]][row["recommended_action"]] += 1

    lines = [
        "# Main Sheet Research Value Audit v1",
        "",
        "Scope: generated public surfaces. This is a diagnostic layer only; it does not demote or promote public records.",
        "",
        "## Summary",
        "",
        f"- Surfaces audited: {len(rows)}",
        f"- Main sheets audited: {len(main_rows)}",
    ]
    for action, count in action_counts.most_common():
        lines.append(f"- `{action}`: {count}")
    lines.extend(["", "## Period Breakdown", ""])
    for row in period_rows:
        lines.append(
            f"- {row['period_band']}: main={row['main_sheet_count']}; keep={row['keep_main']}; "
            f"add_text={row['keep_main_add_editorial_text']}; demote_sub={row['demote_to_sub']}; "
            f"demote_card={row['demote_to_card']}; text_or_appendix={row['promote_text_or_appendix']}; "
            f"median_source_text={row['median_source_text_chars']}; median_score={row['median_research_value_score']}"
        )
    lines.extend(["", "## Region Pressure", ""])
    for region, counter in sorted(region_actions.items(), key=lambda item: (-sum(item[1].values()), item[0]))[:20]:
        joined = "; ".join(f"{action}: {count}" for action, count in counter.most_common())
        lines.append(f"- {region}: {joined}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `keep_main_add_editorial_text` means the object may stay a main-sheet anchor, but it needs a reviewed editorial text page before release.",
            "- `demote_to_sub` and `demote_to_card` are review recommendations, not destructive changes.",
            "- Impact is an internal triage signal only. It does not upgrade `IMG01`/`IMG03`, rights, source authority, or authorship.",
            "- Source-derived text and editorial/generated text are separated so thin record pages are not mistaken for research-rich sheets.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"surfaces={len(rows)}")
    print(f"main_sheets={len(main_rows)}")
    print(f"actions={dict(action_counts.most_common())}")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"wrote {PERIOD_OUT.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
