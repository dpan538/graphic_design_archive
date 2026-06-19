#!/usr/bin/env python3
"""Audit stricter main/sub/card packetization candidates for pre-freeze payload.

This script is advisory only. It does not mutate public surfaces, does not
download images, and does not alter rights or image states.
"""

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

OUT_PACKETS = DATA / "prefreeze_packetization_candidates_v1.csv"
OUT_MEMBERS = DATA / "prefreeze_packetization_surface_recommendations_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_packetization_summary_v1.csv"
OUT_SOURCE_FAMILIES = DATA / "prefreeze_packetization_source_family_summary_v1.csv"
OUT_REPORT = DOCS / "PREFREEZE_PACKETIZATION_AUDIT_v1.md"

SUMMARY_FIELDS = ["metric", "value", "notes"]

PACKET_FIELDS = [
    "packet_id",
    "packet_type",
    "packet_key",
    "confidence",
    "member_count",
    "current_main_count",
    "current_subsheet_count",
    "current_card_count",
    "proposed_main_anchor_id",
    "proposed_main_anchor_title",
    "anchor_score",
    "date_span",
    "period_span_years",
    "region",
    "theme",
    "medium",
    "movement",
    "source_families",
    "image_states",
    "relation_density",
    "source_depth",
    "rights_state",
    "region_scarcity",
    "editorial_need",
    "recommended_action",
    "packet_reason",
    "member_surface_ids",
]

MEMBER_FIELDS = [
    "surface_id",
    "capture_id",
    "packet_id",
    "current_publication_role",
    "current_surface_type",
    "recommended_role",
    "recommendation_confidence",
    "recommendation_reason",
    "anchor_score",
    "relation_density",
    "title",
    "year",
    "region",
    "theme",
    "medium",
    "movement",
    "source_name",
    "image_state",
    "source_reading_text_length",
    "reading_text_length",
    "completeness_score",
]

SOURCE_FIELDS = [
    "source_family",
    "surface_count",
    "current_main_count",
    "packet_member_count",
    "candidate_anchor_count",
    "card_or_support_count",
    "top_regions",
    "top_periods",
    "notes",
]

PERIODS = [
    ("pre_1850", None, 1849),
    ("1850_1899", 1850, 1899),
    ("1900_1913", 1900, 1913),
    ("1914_1945", 1914, 1945),
    ("1946_1969", 1946, 1969),
    ("1970_1989", 1970, 1989),
    ("1990_1999", 1990, 1999),
    ("2000_2009", 2000, 2009),
    ("2010_2019", 2010, 2019),
    ("2020_2026", 2020, 2026),
    ("undated", None, None),
]

VISIBLE_STATES = {"IMG01", "IMG02", "IMG03"}
SUPPORT_ROLES = {"support_packet_appendix_text", "thin_visual_support_packet", "merge_candidate_support_packet"}

STRONG_DESIGN_TERMS = (
    "advert",
    "poster",
    "typograph",
    "typeface",
    "letter",
    "logo",
    "identity",
    "brand",
    "campaign",
    "publication",
    "magazine",
    "book cover",
    "catalogue",
    "exhibition",
    "film",
    "propaganda",
    "public information",
    "wayfinding",
    "signage",
    "map",
    "diagram",
    "graphic",
    "visual communication",
    "studio",
    "school",
)

WEAK_OBJECT_TERMS = (
    "stamp",
    "stamps of",
    "stamp of",
    "colnect",
    "philatel",
    "commemorative",
    "coin",
    "portrait",
    "painting",
    "conference",
    "lecture",
    "talk",
    "session",
    "poster session",
    "own work",
    "self-photographed",
    "cemetery",
    "plaque",
    "building facade",
    "group photo",
    "random processes in the brain",
    "petroxestes",
    "bivalve",
    "limestone",
    "fossil",
    "marianne north",
    "models with",
    "cocoanut",
    "teak trees",
)


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def norm(value: object) -> str:
    text = clean(value).lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[\W_]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def slug(value: object, limit: int = 90) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", norm(value))
    return text.strip("-")[:limit] or "unknown"


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_payload() -> dict[str, Any]:
    return json.loads(PAYLOAD.read_text(encoding="utf-8"))


def folder(surface: dict[str, Any], folder_type: str) -> str:
    for item in surface.get("folders", []):
        if isinstance(item, dict) and item.get("type") == folder_type:
            return clean(item.get("title"))
    return ""


def year_of(surface: dict[str, Any]) -> int | None:
    for key in ("dateEnd", "dateStart"):
        value = surface.get(key)
        if isinstance(value, int):
            return value
        text = clean(value)
        if text.isdigit():
            return int(text)
    return None


def period_of(year: int | None) -> str:
    if year is None:
        return "undated"
    for label, start, end in PERIODS:
        if label == "undated":
            continue
        if (start is None or year >= start) and (end is None or year <= end):
            return label
    return "undated"


def decade_of(surface: dict[str, Any]) -> str:
    year = year_of(surface)
    if year is None:
        return "undated"
    return f"{year // 10 * 10}s"


def image_state(surface: dict[str, Any]) -> str:
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    return clean(image.get("state")) or "IMG00"


def rights_reviewed(surface: dict[str, Any]) -> bool:
    rights = surface.get("rights")
    if isinstance(rights, dict):
        return bool(rights.get("rightsReviewed"))
    return False


def table_value(surface: dict[str, Any], kind: str, label_terms: tuple[str, ...]) -> str:
    terms = tuple(term.lower() for term in label_terms)
    for table in surface.get("tables", []):
        if not isinstance(table, dict) or table.get("kind") != kind:
            continue
        for row in table.get("rows", []):
            if not isinstance(row, (list, tuple)) or len(row) < 2:
                continue
            label, value = row[0], row[1]
            if any(term in clean(label).lower() for term in terms):
                text = clean(value)
                if norm(text) not in {"unknown", "none", "n a", "na"}:
                    return text
    return ""


def source_identifier(surface: dict[str, Any]) -> str:
    return table_value(surface, "SOURCE", ("source identifier", "identifier", "record id", "accession"))


def source_collection(surface: dict[str, Any]) -> str:
    return table_value(surface, "SOURCE", ("collection", "department", "fonds", "series"))


def source_text_len(surface: dict[str, Any]) -> int:
    value = surface.get("sourceReadingTextLength")
    if isinstance(value, int):
        return value
    return len(clean(" ".join(str(surface.get(key) or "") for key in ("sourceDescription", "sourceNotes", "sourceSubjects"))))


def reading_len(surface: dict[str, Any]) -> int:
    value = surface.get("readingTextLength")
    if isinstance(value, int):
        return value
    return len(
        clean(
            " ".join(
                str(surface.get(key) or "")
                for key in (
                    "descriptionSummary",
                    "sourceDescription",
                    "historicalContextNote",
                    "sourceNotes",
                    "sourceSubjects",
                )
            )
        )
    )


def completeness(surface: dict[str, Any]) -> int:
    value = surface.get("completenessScore")
    return int(value) if isinstance(value, int) else 0


def text_blob(surface: dict[str, Any]) -> str:
    return norm(
        " ".join(
            clean(surface.get(key))
            for key in (
                "title",
                "creator",
                "objectType",
                "medium",
                "sourceName",
                "descriptionSummary",
                "sourceDescription",
                "historicalContextNote",
                "sourceSubjects",
            )
        )
    )


def has_design_terms(surface: dict[str, Any]) -> bool:
    blob = text_blob(surface)
    return any(term in blob for term in STRONG_DESIGN_TERMS)


def has_weak_terms(surface: dict[str, Any]) -> bool:
    blob = text_blob(surface)
    return any(term in blob for term in WEAK_OBJECT_TERMS)


def series_stem(surface: dict[str, Any]) -> str:
    title = clean(surface.get("title"))
    title = re.sub(r"\b(18|19|20)\d{2}[-/.]\d{1,2}([-/.]\d{1,2})?\b", " ", title)
    title = re.sub(r"\b(18|19|20)\d{2}\b", " ", title)
    title = re.sub(r"\b(volume|vol\.?|number|no\.?|issue|nº|nr\.?)\s*[\w.-]+\b", " ", title, flags=re.I)
    title = re.sub(r"\b\d{1,5}\b", " ", title)
    title = re.sub(r"\b(file|page|jpg|jpeg|png|tif|tiff|webp)\b", " ", title, flags=re.I)
    return norm(title)


def source_family(surface: dict[str, Any]) -> str:
    name = clean(surface.get("sourceName"))
    if "Wikimedia Commons" in name:
        return "Wikimedia Commons"
    if "/" in name:
        return clean(name.split("/", 1)[0])
    return name or "Unknown source"


def date_span(items: list[dict[str, Any]]) -> tuple[str, int]:
    years = [year_of(item) for item in items if year_of(item) is not None]
    if not years:
        return "undated", 0
    start, end = min(years), max(years)
    return (str(start) if start == end else f"{start}-{end}"), end - start


def concise(values: list[str], limit: int = 6) -> str:
    seen: list[str] = []
    for value in values:
        value = clean(value)
        if value and value not in seen:
            seen.append(value)
    if len(seen) <= limit:
        return "; ".join(seen)
    return "; ".join(seen[:limit]) + f"; +{len(seen) - limit} more"


def add_group(groups: dict[tuple[str, str], list[dict[str, Any]]], group_type: str, key: str, surface: dict[str, Any]) -> None:
    if key and "unknown" not in key:
        groups[(group_type, key)].append(surface)


def candidate_groups(surfaces: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for surface in surfaces:
        source = norm(source_family(surface))
        title = norm(surface.get("title"))
        stem = series_stem(surface)
        identifier = norm(source_identifier(surface))
        collection = norm(source_collection(surface))
        creator = norm(surface.get("creator"))
        region = norm(folder(surface, "region"))
        theme = norm(folder(surface, "theme"))
        medium = norm(folder(surface, "medium"))
        movement = norm(folder(surface, "movement"))
        decade = decade_of(surface)

        if identifier:
            add_group(groups, "same_source_identifier", f"{source}|{identifier}", surface)
        if title:
            add_group(groups, "same_title_source", f"{source}|{title}", surface)
        if stem and len(stem) >= 12:
            add_group(groups, "same_series_stem", f"{source}|{stem}", surface)
        if creator and region and medium:
            add_group(groups, "creator_region_medium_decade", f"{creator}|{region}|{medium}|{decade}", surface)
        if collection and region:
            add_group(groups, "collection_region_decade", f"{source}|{collection}|{region}|{decade}", surface)
        if region and theme and medium and (movement or decade != "undated"):
            add_group(groups, "folder_cell_decade", f"{region}|{theme}|{medium}|{movement}|{decade}", surface)
    return groups


def valid_group(group_type: str, items: list[dict[str, Any]]) -> bool:
    if len(items) < 2:
        return False
    if group_type in {"same_source_identifier", "same_title_source"}:
        return 2 <= len(items) <= 80
    if group_type in {"same_series_stem", "creator_region_medium_decade", "collection_region_decade"}:
        return 3 <= len(items) <= 80
    if group_type == "folder_cell_decade":
        return 4 <= len(items) <= 45
    return False


def group_rank(group_type: str, items: list[dict[str, Any]]) -> tuple[int, int]:
    base = {
        "same_source_identifier": 90,
        "same_title_source": 85,
        "same_series_stem": 76,
        "creator_region_medium_decade": 72,
        "collection_region_decade": 66,
        "folder_cell_decade": 45,
    }.get(group_type, 0)
    return base, min(len(items), 50)


def image_rank(state: str) -> int:
    return {"IMG03": 6, "IMG02": 5, "IMG01": 4, "IMG00": 2, "IMG04": 1}.get(state, 0)


def region_scarcity_score(region: str, region_counts: Counter[str]) -> int:
    count = region_counts.get(region, 0)
    if not region:
        return 0
    if count <= 20:
        return 18
    if count <= 60:
        return 12
    if count <= 150:
        return 7
    return 0


def anchor_score(surface: dict[str, Any], relation_density: int, region_counts: Counter[str]) -> int:
    score = 0
    score += min(completeness(surface), 100) // 5
    score += min(source_text_len(surface), 600) // 40
    score += min(reading_len(surface), 1800) // 180
    score += image_rank(image_state(surface)) * 2
    score += min(relation_density, 12) * 2
    score += region_scarcity_score(folder(surface, "region"), region_counts)
    if rights_reviewed(surface) and image_state(surface) == "IMG03":
        score += 6
    if has_design_terms(surface):
        score += 8
    if has_weak_terms(surface):
        score -= 24
    if surface.get("publicationRole") in SUPPORT_ROLES:
        score -= 8
    if surface.get("surfaceType") == "card":
        score -= 20
    return max(score, 0)


def source_depth_label(items: list[dict[str, Any]]) -> str:
    best = max(source_text_len(item) for item in items)
    avg = sum(source_text_len(item) for item in items) / max(len(items), 1)
    if best >= 500 or avg >= 260:
        return "high"
    if best >= 180 or avg >= 90:
        return "medium"
    return "low"


def rights_state_label(items: list[dict[str, Any]]) -> str:
    states = {image_state(item) for item in items}
    if states <= {"IMG03"} and all(rights_reviewed(item) for item in items):
        return "verified_open"
    if states & VISIBLE_STATES:
        return "source_visible"
    if "IMG04" in states:
        return "text_only_or_missing_image"
    return "unknown"


def editorial_need_label(items: list[dict[str, Any]], relation_density: int) -> str:
    best_reading = max(reading_len(item) for item in items)
    span = date_span(items)[1]
    if relation_density >= 8 or span >= 20 or best_reading < 700:
        return "needs_packet_text"
    if any(source_text_len(item) < 80 for item in items):
        return "needs_source_note"
    return "sufficient_for_review"


def packet_confidence(group_type: str, items: list[dict[str, Any]], relation_density: int) -> str:
    if group_type in {"same_source_identifier", "same_title_source"}:
        return "high"
    if relation_density >= 5 and group_type != "folder_cell_decade":
        return "high"
    if relation_density >= 4:
        return "medium"
    return "low"


def packet_action(group_type: str, items: list[dict[str, Any]], source_depth: str, relation_density: int) -> str:
    current_main = sum(1 for item in items if item.get("publicationRole") == "main_sheet")
    weak_count = sum(1 for item in items if has_weak_terms(item))
    visible_count = sum(1 for item in items if image_state(item) in VISIBLE_STATES)
    if weak_count >= max(2, len(items) // 3):
        return "manual_packet_or_card_review"
    if relation_density >= 6 and source_depth in {"medium", "high"} and visible_count:
        return "promote_one_main_anchor_demote_members_to_subsheets"
    if relation_density >= 3 and current_main >= 2:
        return "demote_parallel_mains_to_subsheet_cluster"
    if source_depth == "low":
        return "hold_as_support_or_editorial_review"
    return "packet_review_only"


def packet_reason(group_type: str) -> str:
    return {
        "same_source_identifier": "Shared source identifier; strong object/series relation.",
        "same_title_source": "Same normalized title inside one source family.",
        "same_series_stem": "Shared title stem after removing dates, issue numbers, and file markers.",
        "creator_region_medium_decade": "Shared creator, region, medium, and decade.",
        "collection_region_decade": "Shared source collection, region, and decade.",
        "folder_cell_decade": "Same region/theme/medium/movement decade cell; weak planning relation only.",
    }.get(group_type, "Candidate packet relation.")


def choose_anchor(items: list[dict[str, Any]], relation_density: int, region_counts: Counter[str]) -> dict[str, Any]:
    return max(
        items,
        key=lambda item: (
            anchor_score(item, relation_density, region_counts),
            source_text_len(item),
            reading_len(item),
            completeness(item),
            image_rank(image_state(item)),
            clean(item.get("title")),
        ),
    )


def top_group_for_surfaces(groups: list[tuple[str, str, list[dict[str, Any]]]]) -> dict[str, tuple[str, str, int]]:
    best: dict[str, tuple[str, str, int]] = {}
    for group_type, key, items in groups:
        rank = group_rank(group_type, items)[0] + min(len(items), 20)
        for item in items:
            sid = clean(item.get("surfaceId"))
            if not sid:
                continue
            if sid not in best or rank > best[sid][2]:
                best[sid] = (group_type, key, rank)
    return best


def surface_recommendation(
    surface: dict[str, Any],
    packet_id: str,
    anchor_id: str,
    relation_density: int,
    score: int,
) -> tuple[str, str, str]:
    current_role = clean(surface.get("publicationRole"))
    if current_role == "card" or surface.get("surfaceType") == "card":
        return "card", "high", "Already card/support context."
    if current_role in SUPPORT_ROLES:
        return "appendix_or_subsheet", "high", "Already support-packet role."
    if not packet_id:
        if score >= 78 and source_text_len(surface) >= 180 and has_design_terms(surface) and not has_weak_terms(surface):
            return "main_sheet_review", "medium", "Singleton has enough source depth and design signal for manual main review."
        return "subsheet_or_card_review", "medium", "Singleton lacks explicit packet relation; main status should not be default."
    if clean(surface.get("surfaceId")) == anchor_id:
        if score >= 72 and relation_density >= 2:
            return "main_sheet_anchor_candidate", "high", "Best-ranked packet anchor with relation density."
        return "main_sheet_manual_review", "medium", "Packet anchor candidate but needs editorial/source-depth review."
    if has_weak_terms(surface):
        return "card_or_appendix_candidate", "medium", "Packet member has weak/context/stamp/event signal."
    return "subsheet_candidate", "high", "Related packet member should support the packet anchor rather than remain a parallel main."


def main() -> None:
    payload = load_payload()
    surfaces = payload.get("surfaces", [])
    region_counts = Counter(folder(surface, "region") for surface in surfaces)

    raw_groups = candidate_groups(surfaces)
    selected_groups = [
        (group_type, key, items)
        for (group_type, key), items in raw_groups.items()
        if valid_group(group_type, items)
    ]
    selected_groups.sort(key=lambda row: (group_rank(row[0], row[2]), row[0], row[1]), reverse=True)

    best_group = top_group_for_surfaces(selected_groups)
    packet_rows: list[dict[str, object]] = []
    member_rows: list[dict[str, object]] = []
    packet_anchor_by_group: dict[tuple[str, str], tuple[str, int, int]] = {}
    surfaced_in_packet: set[str] = set()

    for index, (group_type, key, items) in enumerate(selected_groups, start=1):
        relation_density = min(len(items), 99)
        anchor = choose_anchor(items, relation_density, region_counts)
        anchor_id = clean(anchor.get("surfaceId"))
        anchor_score_value = anchor_score(anchor, relation_density, region_counts)
        span_text, span_years = date_span(items)
        source_depth = source_depth_label(items)
        confidence = packet_confidence(group_type, items, relation_density)
        packet_id = f"PKT{index:05d}"
        packet_anchor_by_group[(group_type, key)] = (packet_id, anchor_id, relation_density)
        surfaced_in_packet.update(clean(item.get("surfaceId")) for item in items)

        regions = [folder(item, "region") for item in items]
        themes = [folder(item, "theme") for item in items]
        mediums = [folder(item, "medium") for item in items]
        movements = [folder(item, "movement") for item in items]
        role_counts = Counter(clean(item.get("publicationRole")) for item in items)
        surface_type_counts = Counter(clean(item.get("surfaceType")) for item in items)
        state_counts = Counter(image_state(item) for item in items)
        scarcity = "scarce" if region_scarcity_score(folder(anchor, "region"), region_counts) >= 12 else "normal"
        action = packet_action(group_type, items, source_depth, relation_density)

        packet_rows.append(
            {
                "packet_id": packet_id,
                "packet_type": group_type,
                "packet_key": key,
                "confidence": confidence,
                "member_count": len(items),
                "current_main_count": role_counts.get("main_sheet", 0),
                "current_subsheet_count": sum(role_counts.get(role, 0) for role in SUPPORT_ROLES),
                "current_card_count": surface_type_counts.get("card", 0),
                "proposed_main_anchor_id": anchor_id,
                "proposed_main_anchor_title": clean(anchor.get("title"))[:220],
                "anchor_score": anchor_score_value,
                "date_span": span_text,
                "period_span_years": span_years,
                "region": concise(regions, 4),
                "theme": concise(themes, 4),
                "medium": concise(mediums, 4),
                "movement": concise(movements, 4),
                "source_families": concise([source_family(item) for item in items], 6),
                "image_states": "; ".join(f"{key}:{value}" for key, value in state_counts.most_common()),
                "relation_density": relation_density,
                "source_depth": source_depth,
                "rights_state": rights_state_label(items),
                "region_scarcity": scarcity,
                "editorial_need": editorial_need_label(items, relation_density),
                "recommended_action": action,
                "packet_reason": packet_reason(group_type),
                "member_surface_ids": ";".join(clean(item.get("surfaceId")) for item in items),
            }
        )

    for surface in surfaces:
        sid = clean(surface.get("surfaceId"))
        group_tuple = best_group.get(sid)
        packet_id = ""
        anchor_id = ""
        relation_density = 0
        if group_tuple:
            packet_id, anchor_id, relation_density = packet_anchor_by_group.get((group_tuple[0], group_tuple[1]), ("", "", 0))
        score = anchor_score(surface, relation_density, region_counts)
        rec_role, rec_conf, rec_reason = surface_recommendation(surface, packet_id, anchor_id, relation_density, score)
        member_rows.append(
            {
                "surface_id": sid,
                "capture_id": clean(surface.get("sourceRecordId")),
                "packet_id": packet_id,
                "current_publication_role": clean(surface.get("publicationRole")),
                "current_surface_type": clean(surface.get("surfaceType")),
                "recommended_role": rec_role,
                "recommendation_confidence": rec_conf,
                "recommendation_reason": rec_reason,
                "anchor_score": score,
                "relation_density": relation_density,
                "title": clean(surface.get("title"))[:240],
                "year": year_of(surface) or "",
                "region": folder(surface, "region"),
                "theme": folder(surface, "theme"),
                "medium": folder(surface, "medium"),
                "movement": folder(surface, "movement"),
                "source_name": clean(surface.get("sourceName"))[:220],
                "image_state": image_state(surface),
                "source_reading_text_length": source_text_len(surface),
                "reading_text_length": reading_len(surface),
                "completeness_score": completeness(surface),
            }
        )

    source_rows: list[dict[str, object]] = []
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rec_by_surface = {row["surface_id"]: row for row in member_rows}
    for surface in surfaces:
        by_source[source_family(surface)].append(surface)
    for family, items in sorted(by_source.items(), key=lambda row: (-len(row[1]), row[0])):
        source_rows.append(
            {
                "source_family": family,
                "surface_count": len(items),
                "current_main_count": sum(1 for item in items if item.get("publicationRole") == "main_sheet"),
                "packet_member_count": sum(1 for item in items if clean(item.get("surfaceId")) in surfaced_in_packet),
                "candidate_anchor_count": sum(
                    1
                    for item in items
                    if rec_by_surface.get(clean(item.get("surfaceId")), {}).get("recommended_role") == "main_sheet_anchor_candidate"
                ),
                "card_or_support_count": sum(
                    1
                    for item in items
                    if rec_by_surface.get(clean(item.get("surfaceId")), {}).get("recommended_role")
                    in {"card", "appendix_or_subsheet", "card_or_appendix_candidate"}
                ),
                "top_regions": concise([folder(item, "region") for item in items], 5),
                "top_periods": concise([period_of(year_of(item)) for item in items], 5),
                "notes": "High source-family concentration should be reviewed for repeated-source overclaiming." if len(items) >= 100 else "",
            }
        )

    role_counts = Counter(row["recommended_role"] for row in member_rows)
    packet_action_counts = Counter(row["recommended_action"] for row in packet_rows)
    packet_conf_counts = Counter(row["confidence"] for row in packet_rows)
    summary_rows: list[dict[str, object]] = [
        {"metric": "surfaces_scanned", "value": len(surfaces), "notes": "Candidate payload surfaces scanned."},
        {"metric": "packet_candidates", "value": len(packet_rows), "notes": "Candidate packets generated by strict relation rules."},
        {"metric": "surfaces_in_candidate_packets", "value": len(surfaced_in_packet), "notes": "Surfaces with at least one packet relation."},
        {"metric": "surfaces_without_packet_relation", "value": len(surfaces) - len(surfaced_in_packet), "notes": "Singletons or records lacking strict relation signal."},
    ]
    for role, count in role_counts.most_common():
        summary_rows.append({"metric": f"recommended_role:{role}", "value": count, "notes": "Surface-level packetization recommendation."})
    for action, count in packet_action_counts.most_common():
        summary_rows.append({"metric": f"packet_action:{action}", "value": count, "notes": "Packet-level recommended action."})
    for confidence, count in packet_conf_counts.most_common():
        summary_rows.append({"metric": f"packet_confidence:{confidence}", "value": count, "notes": "Packet confidence distribution."})

    write_csv(OUT_PACKETS, packet_rows, PACKET_FIELDS)
    write_csv(OUT_MEMBERS, member_rows, MEMBER_FIELDS)
    write_csv(OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_csv(OUT_SOURCE_FAMILIES, source_rows, SOURCE_FIELDS)
    write_report(summary_rows, packet_rows, member_rows, source_rows)

    print(f"surfaces_scanned={len(surfaces)}")
    print(f"packet_candidates={len(packet_rows)}")
    print(f"surfaces_in_candidate_packets={len(surfaced_in_packet)}")
    print(f"wrote {OUT_PACKETS.relative_to(ROOT)}")
    print(f"wrote {OUT_MEMBERS.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_SOURCE_FAMILIES.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


def write_report(
    summary_rows: list[dict[str, object]],
    packet_rows: list[dict[str, object]],
    member_rows: list[dict[str, object]],
    source_rows: list[dict[str, object]],
) -> None:
    top_packets = sorted(packet_rows, key=lambda row: (int(row["member_count"]), int(row["anchor_score"])), reverse=True)[:20]
    role_counts = Counter(row["recommended_role"] for row in member_rows)
    lines = [
        "# Prefreeze Packetization Audit v1",
        "",
        "Scope: advisory audit for stricter main/sub/card/text assignment in the pre-freeze candidate payload.",
        "",
        "This pass does not mutate public surfaces, does not download images, and does not change rights or image states.",
        "",
        "## Summary",
        "",
    ]
    for row in summary_rows:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Interpretation", ""])
    lines.append(
        "- Main sheet should become a research packet anchor, not the default role for every captured object."
    )
    lines.append(
        "- Parallel main sheets inside a strong packet should usually become subsheets, cards, appendices, or editorial text leaves around one representative anchor."
    )
    lines.append(
        "- Singleton records are not automatically demoted here; they are queued for manual main/sub/card review unless source depth, design signal, and scarcity support main status."
    )
    lines.extend(["", "## Recommended Role Distribution", ""])
    for role, count in role_counts.most_common():
        lines.append(f"- {role}: {count}")
    lines.extend(["", "## Largest Candidate Packets", ""])
    for row in top_packets:
        lines.append(
            f"- {row['packet_id']} / {row['packet_type']} / members {row['member_count']} / action {row['recommended_action']} / anchor {row['proposed_main_anchor_id']} / {row['proposed_main_anchor_title']}"
        )
    lines.extend(["", "## Source-Family Concentration Notes", ""])
    for row in source_rows[:20]:
        note = row.get("notes") or ""
        lines.append(
            f"- {row['source_family']}: {row['surface_count']} surfaces, {row['current_main_count']} current mains, {row['candidate_anchor_count']} candidate anchors. {note}".rstrip()
        )
    lines.extend(["", "## Next Use", ""])
    lines.append("- Sample high-confidence packet anchors before applying any role override.")
    lines.append("- Use medium/low packet rows as planning evidence, not automatic grouping.")
    lines.append("- Build the next override layer only from reviewed packet recommendations.")
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
