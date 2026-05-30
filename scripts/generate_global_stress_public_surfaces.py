from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import argparse

sys.path.append(str(Path(__file__).resolve().parent))

from run_early_region_capture_1830_1930 import (  # noqa: E402
    ACCESS_DATE,
    FOLDER_TYPES,
    ROOT,
    build_public_payload,
    clean_text,
    folder_id,
    slug,
    table,
)


DATA = ROOT / "data"
GENERATED = ROOT / "generated"
EARLY_RECORDS = DATA / "capture_batch_early_region_1830_1930_records.csv"
MANUAL_INDEX = DATA / "manual_source_records_index.csv"
REMEDIATION_INDEX = DATA / "remediation_source_records_index.csv"
SURFACES_JSON = GENERATED / "public_surfaces_v1.json"
GLOBAL_BATCH_JSON = GENERATED / "global_stress_surfaces_v1.json"
COMBINED_STRESS_JSON = GENERATED / "combined_stress_public_surfaces_v1.json"
SUMMARY_CSV = DATA / "capture_batch_global_stress_surface_summary.csv"


THEME_LABELS = {
    "bauhaus": "Bauhaus / New Typography normalization",
    "polish_poster": "Polish poster school",
    "ibm_design": "Corporate identity and design systems",
    "tgp": "Taller de Grafica Popular and political print",
    "wodeco": "Japanese postwar design institutions",
    "shanghai_manhua": "Shanghai commercial print and pictorial culture",
    "sg_posters": "Singapore multilingual public graphics",
    "nid": "Development communication and design education",
    "iran_poster": "Iranian modern and contemporary poster design",
    "medu": "Anti-apartheid and exile poster culture",
    "naidoc_land_rights": "Indigenous poster and land-rights graphics",
    "gran_fury_actup": "AIDS activist graphics and queer counterpublics",
    "early_web_css_geocities": "Early web standards and interface culture",
    "C05": "Brigadas Ramona Parra and mural graphics",
    "C06": "Japanese postwar design institutions",
    "C08": "Korean Minjung and democratization graphics",
    "C09": "Singapore multilingual public graphics",
    "C10": "Development communication and design education",
    "C11": "Iranian modern and contemporary poster design",
    "C12": "Anti-apartheid and exile poster culture",
    "remediation": "Source remediation and fallback evidence",
}


MOVEMENT_LABELS = {
    "RM075": "Bauhaus / New Typography",
    "RM076": "Polish Poster School",
    "RM077": "IBM corporate design systems",
    "RM078": "Taller de Grafica Popular",
    "RM079": "Brigadas Ramona Parra",
    "RM080": "World Design Conference / NDC network",
    "RM081": "Shanghai Manhua / yuefenpai commercial print",
    "RM082": "Minjung democratization graphics",
    "RM083": "Singapore multilingual public graphics",
    "RM084": "NID development communication",
    "RM085": "Iranian modern poster design",
    "RM086": "Medu / Culture and Resistance",
    "RM087": "NAIDOC / land-rights poster cultures",
    "RM088": "Gran Fury / ACT UP",
    "RM089": "Early web / CSS standards",
}


REGION_TESTS = [
    ("Global web / transnational", ["web / transnational", "web", "w3c", "css"]),
    ("China / Hong Kong", ["china", "hong kong", "上海", "日曆", "漫画", "漫畫"]),
    ("Japan", ["japan", "japanese", "jagda", "日本", "デザイン"]),
    ("Korea", ["korea", "seoul", "gwangju", "minjung"]),
    ("Singapore", ["singapore", "tamil road signs"]),
    ("India", ["india", "nid", "ahmedabad"]),
    ("Iran", ["iran", "persian", "momayez", "persianissimo"]),
    ("South Africa / Botswana", ["south africa", "botswana", "medu", "saha"]),
    ("Australia / Indigenous", ["australia", "aiatsis", "naidoc", "indigenous"]),
    ("Chile", ["chile", "brigada ramona parra", "bnd"]),
    ("Mexico", ["mexico", "grafica popular", "taller de grafica"]),
    ("Poland", ["poland", "polish", "cieslewicz", "lenica"]),
    ("Germany", ["germany", "bauhaus", "gropius"]),
    ("United States", ["united states", "nypl", "ibm", "moma", "harvard", "gran fury", "act up"]),
    ("Latin America", ["latin america"]),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_frontend_payload(payload_text: str) -> None:
    for path in [
        ROOT / "frontend" / "src" / "data" / "public_surface_mock_v0.json",
        ROOT / "frontend" / "public" / "data" / "public_surface_mock_v0.json",
    ]:
        if path.exists():
            path.write_text(payload_text, encoding="utf-8")


def load_valid_records() -> list[tuple[str, Path, dict[str, Any]]]:
    out: list[tuple[str, Path, dict[str, Any]]] = []
    seen_records: set[tuple[str, str]] = set()
    for index_path, id_field, path_field in [
        (MANUAL_INDEX, "first_target_id", "source_record_draft_path"),
        (REMEDIATION_INDEX, "remediation_verification_id", "source_record_draft_path"),
    ]:
        for row in read_csv(index_path):
            if row.get("validation_status") != "valid":
                continue
            path = ROOT / row[path_field]
            record = json.loads(path.read_text(encoding="utf-8"))
            url = record.get("source", {}).get("sourceRecordUrl", "")
            title = record.get("sourceMetadata", {}).get("sourceTitle", "")
            dedupe_key = (url, title)
            if url and dedupe_key in seen_records:
                continue
            seen_records.add(dedupe_key)
            out.append((row[id_field], path, record))
    return out


def classification_values(record: dict[str, Any], kind: str) -> list[str]:
    values = []
    for item in record.get("classifications", []):
        if item.get("classificationType") == kind and item.get("classificationValue"):
            values.append(item["classificationValue"])
    return values


def display_image_code(record: dict[str, Any]) -> str:
    code = record.get("publicationDisplay", {}).get("imagePresenceCode")
    if code in {"IMG00", "IMG01", "IMG02", "IMG03", "IMG04"}:
        return code
    return "IMG00"


def image_url_for(record: dict[str, Any], image_state: str) -> str | None:
    if image_state not in {"IMG01", "IMG03"}:
        return None
    image = record.get("image", {})
    url = image.get("thumbnailUrl") or image.get("sourceImageUrl")
    if not url:
        return None
    # Some manual records keep the source page URL in sourceImageUrl as evidence.
    # Do not render those as bitmaps.
    if not re.search(r"\.(apng|avif|gif|jpe?g|png|webp)(\?|$)", url, re.I):
        return None
    return url


def region_labels_for(record: dict[str, Any]) -> list[str]:
    source = record.get("source", {})
    source_meta = record.get("sourceMetadata", {})
    normalized = record.get("normalizedMetadata", {})
    blob = " ".join(
        [
            source.get("sourceName", ""),
            source_meta.get("sourceTitle", ""),
            source_meta.get("sourcePlaceText", ""),
            source_meta.get("sourceHoldingInstitution", ""),
            source_meta.get("sourceDescription", ""),
            normalized.get("normalizedPlace", ""),
        ]
    ).lower()
    labels = [label for label, terms in REGION_TESTS if any(term.lower() in blob for term in terms)]
    if not labels:
        return ["Unresolved region"]
    if len(labels) > 2:
        labels = labels[:2]
    return labels


def medium_label_for(record: dict[str, Any]) -> str:
    source_meta = record.get("sourceMetadata", {})
    blob = " ".join(
        [
            source_meta.get("sourceTitle", ""),
            source_meta.get("sourceObjectType", ""),
            source_meta.get("sourceMediumText", ""),
        ]
    ).lower()
    tests = [
        ("Poster", ["poster", "estampa"]),
        ("Institutional / event page", ["institutional", "event", "history page", "conference", "news archive"]),
        ("Authority record", ["authority"]),
        ("Web standard / webpage", ["web", "css", "recommendation"]),
        ("Periodical issue", ["periodical", "issue", "magazine", "上海漫畫"]),
        ("Bibliographic record", ["bibliographic", "book", "pdf", "report"]),
        ("Photograph record", ["photograph"]),
        ("Corporate identity record", ["logo", "identity", "corporate"]),
    ]
    for label, terms in tests:
        if any(term in blob for term in terms):
            return label
    if "museum object" in blob or "collection object" in blob:
        return "Museum object record"
    return source_meta.get("sourceObjectType") or "Source record"


def folder_refs_for(record: dict[str, Any]) -> list[dict[str, str]]:
    normalized = record.get("normalizedMetadata", {})
    refs: dict[str, dict[str, str]] = {}
    for label in region_labels_for(record):
        refs[folder_id("region", label)] = {"folderId": folder_id("region", label), "type": "region", "title": label}
    for term in normalized.get("themeTerms", []):
        label = THEME_LABELS.get(term, term.replace("_", " ").title())
        refs[folder_id("theme", label)] = {"folderId": folder_id("theme", label), "type": "theme", "title": label}
    medium_label = medium_label_for(record)
    refs[folder_id("medium", medium_label)] = {"folderId": folder_id("medium", medium_label), "type": "medium", "title": medium_label}
    for movement_id in classification_values(record, "movement_or_regional_formation"):
        label = MOVEMENT_LABELS.get(movement_id, movement_id)
        refs[folder_id("movement", label)] = {"folderId": folder_id("movement", label), "type": "movement", "title": label}
    return sorted(refs.values(), key=lambda ref: (["region", "theme", "medium", "movement"].index(ref["type"]), ref["title"]))


def score_record(record: dict[str, Any]) -> int:
    source = record.get("source", {})
    meta = record.get("sourceMetadata", {})
    normalized = record.get("normalizedMetadata", {})
    rights = record.get("rights", {})
    score = 22
    for value, points in [
        (source.get("sourceRecordUrl"), 10),
        (meta.get("sourceTitle"), 10),
        (meta.get("sourceDateText"), 8),
        (normalized.get("normalizedDateStart"), 8),
        (meta.get("sourceDescription"), 8),
        (meta.get("sourceObjectType"), 7),
        (meta.get("sourceHoldingInstitution"), 6),
        (rights.get("rightsBasis"), 6),
        (normalized.get("themeTerms"), 5),
        (classification_values(record, "movement_or_regional_formation"), 5),
    ]:
        if value:
            score += points
    return min(score, 95)


def surface_type_template(image_state: str, score: int) -> tuple[str, str, str | None]:
    if score < 45:
        return "fallback_stub", "stub.fallback.v0", None
    if score < 60:
        return "card", "card.sparse.v0", None
    if image_state == "IMG04":
        return "sheet", "sheet.text.v0", "text"
    if image_state == "IMG00":
        return "sheet", "sheet.img00.v0", "main"
    return "sheet", "sheet.main.v0", "plate"


def text_join(values: list[str]) -> str:
    seen = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return "; ".join(seen)


def build_surface(record_id: str, path: Path, record: dict[str, Any], index: int) -> dict[str, Any]:
    source = record.get("source", {})
    meta = record.get("sourceMetadata", {})
    normalized = record.get("normalizedMetadata", {})
    rights = record.get("rights", {})
    citation = record.get("citation", {})
    display = record.get("publicationDisplay", {})
    image_state = display_image_code(record)
    score = score_record(record)
    surface_type, template_id, layout_hint = surface_type_template(image_state, score)
    date_start = normalized.get("normalizedDateStart")
    date_end = normalized.get("normalizedDateEnd")
    era = date_start or "undated"
    tier = "M" if surface_type == "sheet" else "S"
    seq = f"STAGED-GS-{index:04d}"
    image_url = image_url_for(record, image_state)
    folders = folder_refs_for(record)
    title = normalized.get("normalizedTitle") or meta.get("sourceTitle") or f"Global stress record {record_id}"
    source_url = source.get("sourceRecordUrl") or citation.get("citationUrl") or ""
    description = meta.get("sourceDescription") or rights.get("rightsBasis") or display.get("imagePresenceBasis") or ""
    hn_ids = normalized.get("historicalNodeIds") or classification_values(record, "historical_node")
    movement_ids = classification_values(record, "movement_or_regional_formation")
    return {
        "surfaceId": f"SURF-{record_id}",
        "sourceRecordId": record_id,
        "surfaceType": surface_type,
        "templateId": template_id,
        "provisionalDisplayNumber": f"GD / {era} / {seq} / {tier}-p01",
        "seqLabel": seq,
        "historicalNodeIds": hn_ids,
        "movementIds": movement_ids,
        "title": title,
        "creator": meta.get("sourceCreator") or "Unknown / institutional",
        "dateText": meta.get("sourceDateText") or (str(date_start) if date_start else "undated"),
        "dateStart": date_start,
        "dateEnd": date_end,
        "placeText": normalized.get("normalizedPlace") or meta.get("sourcePlaceText") or text_join(region_labels_for(record)),
        "objectType": meta.get("sourceObjectType") or medium_label_for(record),
        "medium": meta.get("sourceMediumText") or medium_label_for(record),
        "sourceName": source.get("sourceName") or "Unknown source",
        "sourceUrl": source_url,
        "accessDate": source.get("accessDate") or citation.get("accessDate") or ACCESS_DATE,
        "descriptionSummary": clean_text(description, max_chars=520),
        "sourceDescription": clean_text(meta.get("sourceDescription", ""), max_chars=520),
        "sourceNotes": clean_text(display.get("imagePresenceBasis") or rights.get("rightsNotes") or "", max_chars=520),
        "sourceSubjects": text_join(normalized.get("themeTerms", [])),
        "completenessScore": score,
        "reviewGates": {
            "sourceUrl": bool(source_url),
            "rightsReviewed": not rights.get("rightsReviewRequired", True),
            "dateKnown": bool(date_start or meta.get("sourceDateText")),
            "classificationKnown": bool(folders),
        },
        "image": {
            "state": image_state,
            "hasImageFrame": image_state != "IMG04",
            "url": image_url,
            "credit": meta.get("sourceCreditLine") or source.get("sourceName") if image_url else None,
            "licenseLabel": rights.get("rightsNotes") or rights.get("rightsBasis") or display.get("imagePresenceBasis") or "",
        },
        "rights": {
            "state": rights.get("rightsState") or "rights_review_required",
            "displayPolicy": display.get("imageFrameBehavior") or rights.get("imageUsePolicy") or "do_not_display",
            "label": rights.get("rightsBasis") or display.get("imagePresenceBasis") or "Rights state not reviewed.",
        },
        "folders": folders,
        "layoutHint": layout_hint,
        "tables": [
            table(
                "SOURCE",
                [
                    ("Source ID", source.get("sourceId", "")),
                    ("Source name", source.get("sourceName", "")),
                    ("Source identifier", source.get("sourceIdentifier", "")),
                    ("Source title", meta.get("sourceTitle", "")),
                    ("Source creator", meta.get("sourceCreator", "")),
                    ("Source date", meta.get("sourceDateText", "")),
                    ("Holding institution", meta.get("sourceHoldingInstitution", "")),
                    ("Source description", meta.get("sourceDescription", "")),
                    ("Source URL", source_url),
                ],
            ),
            table(
                "NORMALIZED",
                [
                    ("Normalized title", title),
                    ("Date start", str(date_start or "")),
                    ("Date end", str(date_end or "")),
                    ("Normalized place", normalized.get("normalizedPlace", "")),
                    ("Object type", meta.get("sourceObjectType", "")),
                    ("Medium", meta.get("sourceMediumText", "") or medium_label_for(record)),
                    ("Language", normalized.get("language", "")),
                ],
            ),
            table(
                "RIGHTS",
                [
                    ("Image state", image_state),
                    ("Display policy", display.get("imageFrameBehavior", "")),
                    ("Rights state", rights.get("rightsState", "")),
                    ("Rights basis", rights.get("rightsBasis", "")),
                    ("Local copy permitted", str(rights.get("localCopyPermitted", False)).lower()),
                    ("Rights review required", str(rights.get("rightsReviewRequired", True)).lower()),
                ],
            ),
            table(
                "CLASSIFICATION",
                [
                    ("Historical node refs", text_join(hn_ids)),
                    ("Movement / formation refs", text_join(movement_ids) or "NONE"),
                    ("Theme terms", text_join(normalized.get("themeTerms", []))),
                    ("Folder memberships", text_join([ref["title"] for ref in folders])),
                    ("Classification basis", "Manual source record converted to public surface"),
                ],
            ),
            table(
                "RELATIONS",
                [
                    ("held_by", meta.get("sourceHoldingInstitution") or source.get("sourceName", "")),
                    ("classified_as", medium_label_for(record)),
                    ("source_record_file", str(path.relative_to(ROOT))),
                ],
            ),
            table(
                "CITATIONS",
                [
                    ("Citation", citation.get("citationText", "")),
                    ("Source URL", source_url),
                    ("Access date", source.get("accessDate") or ACCESS_DATE),
                ],
            ),
        ],
    }


def child_note(surface: dict[str, Any]) -> str:
    return clean_text(surface.get("descriptionSummary") or surface.get("sourceNotes") or surface.get("objectType"), max_chars=160)


def build_naidoc_compound(children: list[dict[str, Any]]) -> dict[str, Any]:
    children = sorted(children, key=lambda s: (s.get("dateStart") or 9999, s.get("title", "")))
    start = min(child["dateStart"] for child in children if child.get("dateStart"))
    end = max(child["dateStart"] for child in children if child.get("dateStart"))
    folders = {ref["folderId"]: ref for child in children for ref in child.get("folders", [])}
    member_ids = [child["sourceRecordId"] for child in children]
    return {
        "surfaceId": "SURF-COMPOUND-NAIDOC-POSTER-CULTURES",
        "sourceRecordId": "COMPOUND-NAIDOC-POSTER-CULTURES",
        "surfaceType": "sheet",
        "templateId": "sheet.compound.v0",
        "provisionalDisplayNumber": f"GD / {start} / STAGED-GS-C001 / L-p01",
        "seqLabel": "STAGED-GS-C001",
        "historicalNodeIds": sorted({node for child in children for node in child.get("historicalNodeIds", [])}),
        "movementIds": sorted({node for child in children for node in child.get("movementIds", [])}),
        "title": "NAIDOC poster cultures, 2020-2022",
        "creator": "Multiple artists / AIATSIS and NAIDOC source records",
        "dateText": f"{start}-{end}",
        "dateStart": start,
        "dateEnd": end,
        "placeText": "Australia / Indigenous",
        "objectType": "compound poster archive group",
        "medium": "Poster",
        "sourceName": "AIATSIS",
        "sourceUrl": children[0].get("sourceUrl", ""),
        "accessDate": ACCESS_DATE,
        "descriptionSummary": "Compound sheet for three protocol-aware NAIDOC poster records. The child list preserves each poster title, date, source link, and IMG state.",
        "sourceDescription": "Grouped public surface generated from validated manual source records.",
        "sourceNotes": "Protocol-sensitive image display remains subject to record-level and cultural review.",
        "sourceSubjects": "naidoc_land_rights",
        "completenessScore": max(child.get("completenessScore", 0) for child in children),
        "reviewGates": {
            "sourceUrl": True,
            "rightsReviewed": False,
            "dateKnown": True,
            "classificationKnown": True,
        },
        "image": {
            "state": "IMG04",
            "hasImageFrame": False,
            "url": None,
            "credit": None,
            "licenseLabel": "Compound page has no image frame; child records retain IMG03/protocol notes.",
        },
        "rights": {
            "state": "protocol_sensitive_compound",
            "displayPolicy": "no_image_frame",
            "label": "Compound page suppresses image display. Member records retain individual rights and protocol notes.",
        },
        "folders": sorted(folders.values(), key=lambda ref: (["region", "theme", "medium", "movement"].index(ref["type"]), ref["title"])),
        "layoutHint": "compound",
        "compoundChildren": [
            {
                "title": child.get("title", ""),
                "dateText": child.get("dateText", ""),
                "sourceName": child.get("sourceName", ""),
                "sourceUrl": child.get("sourceUrl", ""),
                "imageState": child.get("image", {}).get("state", "IMG00"),
                "note": child_note(child),
            }
            for child in children
        ],
        "tables": [
            table("SOURCE", [("Source group", "AIATSIS / NAIDOC"), ("Member count", str(len(children))), ("Member records", text_join(member_ids)), ("Representative URL", children[0].get("sourceUrl", ""))]),
            table("NORMALIZED", [("Date span", f"{start}-{end}"), ("Region", "Australia / Indigenous"), ("Medium", "Poster"), ("Grouping rule", "protocol-aware annual poster sequence")]),
            table("RIGHTS", [("Compound image state", "IMG04"), ("Member image states", "IMG03; protocol review retained"), ("Display policy", "No image frame on compound sheet"), ("Rights review required", "true")]),
            table("CLASSIFICATION", [("Historical node refs", "HN012; HN013; HN015"), ("Movement refs", "RM087"), ("Theme", "Indigenous poster and land-rights graphics")]),
            table("RELATIONS", [("has_member", text_join(member_ids)), ("grouped_by", "annual poster sequence"), ("preserves", "source link; date; image state; protocol note")]),
            table("CITATIONS", [("Source URL", children[0].get("sourceUrl", "")), ("Access date", ACCESS_DATE)]),
        ],
    }


def collapse_global_compounds(surfaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    naidoc = [s for s in surfaces if "naidoc_land_rights" in (s.get("sourceSubjects") or "")]
    if len(naidoc) < 3:
        return surfaces
    naidoc_ids = {s["surfaceId"] for s in naidoc}
    return [s for s in surfaces if s["surfaceId"] not in naidoc_ids] + [build_naidoc_compound(naidoc)]


def generic_scope_note(folder_type: str, title: str) -> str:
    if folder_type == "region":
        return f"Public surfaces associated with {title}. Time remains the sorting axis."
    if folder_type == "theme":
        return f"Research theme folder: {title}."
    if folder_type == "medium":
        return f"Medium and source-format folder: {title}."
    return f"Movement, formation, school, or named design-culture folder: {title}."


def build_folders(surfaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    surface_by_id = {surface["surfaceId"]: surface for surface in surfaces}
    for surface in surfaces:
        for ref in surface["folders"]:
            folder = grouped.setdefault(
                ref["folderId"],
                {
                    "folderId": ref["folderId"],
                    "type": ref["type"],
                    "slug": slug(ref["title"]),
                    "title": ref["title"],
                    "dateStart": None,
                    "dateEnd": None,
                    "scopeNote": generic_scope_note(ref["type"], ref["title"]),
                    "surfaceIds": [],
                    "relatedFolderIds": [],
                    "authorityRefs": {},
                },
            )
            folder["surfaceIds"].append(surface["surfaceId"])
            if surface.get("dateStart") is not None:
                folder["dateStart"] = min(folder["dateStart"], surface["dateStart"]) if folder["dateStart"] is not None else surface["dateStart"]
            if surface.get("dateEnd") is not None:
                folder["dateEnd"] = max(folder["dateEnd"], surface["dateEnd"]) if folder["dateEnd"] is not None else surface["dateEnd"]
            elif surface.get("dateStart") is not None:
                folder["dateEnd"] = max(folder["dateEnd"], surface["dateStart"]) if folder["dateEnd"] is not None else surface["dateStart"]

    for folder in grouped.values():
        folder["surfaceIds"].sort(key=lambda sid: (surface_by_id[sid].get("dateStart") or 9999, surface_by_id[sid].get("seqLabel", "")))
        related = set()
        for sid in folder["surfaceIds"]:
            for ref in surface_by_id[sid]["folders"]:
                if ref["folderId"] != folder["folderId"]:
                    related.add(ref["folderId"])
        folder["relatedFolderIds"] = sorted(related)
    order = {"region": 0, "theme": 1, "medium": 2, "movement": 3}
    return sorted(grouped.values(), key=lambda f: (order[f["type"]], f["title"]))


def write_summary(global_surfaces: list[dict[str, Any]], combined_payload: dict[str, Any]) -> None:
    fields = ["surface_id", "source_record_id", "title", "date_start", "image_state", "template_id", "folder_count", "source_url"]
    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for surface in sorted(global_surfaces, key=lambda s: (s.get("dateStart") or 9999, s["surfaceId"])):
            writer.writerow(
                {
                    "surface_id": surface["surfaceId"],
                    "source_record_id": surface["sourceRecordId"],
                    "title": surface["title"],
                    "date_start": surface.get("dateStart") or "",
                    "image_state": surface["image"]["state"],
                    "template_id": surface["templateId"],
                    "folder_count": len(surface["folders"]),
                    "source_url": surface["sourceUrl"],
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate global stress surfaces for internal coverage testing."
    )
    parser.add_argument(
        "--sync-frontend",
        action="store_true",
        help="Also write the combined stress payload into the frontend preview files. Off by default so period previews are not polluted.",
    )
    args = parser.parse_args()

    early_payload = build_public_payload(read_csv(EARLY_RECORDS))
    records = load_valid_records()
    global_surfaces = [build_surface(record_id, path, record, index) for index, (record_id, path, record) in enumerate(records, start=1)]
    global_surfaces = collapse_global_compounds(global_surfaces)
    global_surfaces.sort(key=lambda s: (s.get("dateStart") or 9999, s.get("seqLabel", ""), s.get("title", "")))
    combined_surfaces = sorted(
        early_payload["surfaces"] + global_surfaces,
        key=lambda s: (s.get("dateStart") or 9999, s.get("seqLabel", ""), s.get("title", "")),
    )
    payload = {
        "meta": {
            "generatedAt": ACCESS_DATE,
            "status": "generated",
            "note": "Generated public archive-box payload: early-region capture plus global stress batch from validated source records.",
        },
        "folderTypes": FOLDER_TYPES,
        "folders": build_folders(combined_surfaces),
        "surfaces": combined_surfaces,
    }
    write_json(GLOBAL_BATCH_JSON, {"meta": payload["meta"], "folderTypes": FOLDER_TYPES, "folders": build_folders(global_surfaces), "surfaces": global_surfaces})
    payload_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    COMBINED_STRESS_JSON.write_text(payload_text, encoding="utf-8")
    if args.sync_frontend:
        SURFACES_JSON.write_text(payload_text, encoding="utf-8")
        sync_frontend_payload(payload_text)
    write_summary(global_surfaces, payload)

    image_counts = Counter(surface["image"]["state"] for surface in global_surfaces)
    template_counts = Counter(surface["templateId"] for surface in global_surfaces)
    print(f"{GLOBAL_BATCH_JSON.relative_to(ROOT)}: {len(global_surfaces)} global stress surfaces")
    print(f"{COMBINED_STRESS_JSON.relative_to(ROOT)}: {len(payload['surfaces'])} combined surfaces, {len(payload['folders'])} folders")
    if not args.sync_frontend:
        print("frontend preview not updated; pass --sync-frontend for an intentional combined stress preview")
    print("global image distribution:", dict(sorted(image_counts.items())))
    print("global template distribution:", dict(sorted(template_counts.items())))


if __name__ == "__main__":
    main()
