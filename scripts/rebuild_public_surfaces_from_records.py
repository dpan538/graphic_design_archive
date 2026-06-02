from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

import run_midcentury_capture_1930_1970 as mc
import run_midcentury_expansion_capture_1931_1970 as mx
from normalize_public_surfaces import normalize_payload


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GENERATED = ROOT / "generated"
ACCESS_DATE = "2026-05-31"

RECORD_FILES = [
    DATA / "capture_batch_early_region_1830_1930_records.csv",
    DATA / "capture_batch_midcentury_1930_1970_records.csv",
    DATA / "capture_batch_midcentury_expansion_1931_1970_records.csv",
    DATA / "capture_batch_image_ready_1931_1970_records.csv",
    DATA / "capture_batch_gallica_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_gallica_secondary_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_smithsonian_oa_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_digitalnz_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_digitalnz_postwar_image_ready_1945_2026_records.csv",
    DATA / "capture_batch_wikimedia_commons_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_wikimedia_commons_deep_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_postwar_commons_open_image_1945_2026_records.csv",
    DATA / "capture_batch_princeton_figgy_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_gsu_contentdm_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_gsu_contentdm_image_ready_1971_2026_records.csv",
    DATA / "capture_batch_cooperhewitt_graphql_image_ready_1830_2026_records.csv",
    DATA / "capture_batch_noncanonical_movement_commons_1930_2000_records.csv",
    DATA / "capture_batch_noncanonical_exact_sources_1970_2000_records.csv",
    DATA / "capture_batch_gap_noncanonical_image_text_1930_2000_records.csv",
    DATA / "capture_batch_late_period_coverage_1970_2026_records.csv",
    DATA / "capture_batch_protocol_item_1970_2026_records.csv",
    DATA / "capture_batch_source_breadth_1970_2026_records.csv",
    DATA / "capture_batch_independent_asia_1990_2026_records.csv",
    DATA / "capture_batch_edge_wordpress_1970_2026_records.csv",
    DATA / "capture_batch_edge_rss_html_1970_2026_records.csv",
    DATA / "capture_batch_loc_deep_image_ready_1931_1970_records.csv",
]

PAYLOAD_PATHS = [
    GENERATED / "public_surfaces_v1.json",
    ROOT / "frontend" / "src" / "data" / "public_surface_mock_v0.json",
    ROOT / "frontend" / "public" / "data" / "public_surface_mock_v0.json",
    DATA / "public_surface_mock_v0.json",
]


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def fallback_summary(row: dict[str, str]) -> str:
    title = row.get("source_title") or "This record"
    source = row.get("source_name") or "the source"
    evidence = (
        row.get("editorial_summary")
        or row.get("source_description")
        or row.get("source_notes")
        or row.get("source_subjects")
        or row.get("source_object_type")
        or "metadata-only source record"
    )
    return mx.clean(f"{title} is indexed from {source}. {evidence}", max_chars=560)


def fill_enrichment_defaults(row: dict[str, str]) -> dict[str, str]:
    code = row.get("image_presence_code") or "IMG00"
    title = row.get("source_title") or row.get("source_object_type") or row.get("source_medium") or "Untitled source record"
    if not row.get("source_title"):
        row["source_title"] = title
    row.setdefault("image_expectation", "not_expected" if code == "IMG04" else "expected")
    row.setdefault("parser_status", "ok" if row.get("source_record_url") else "legacy")
    row.setdefault("display_mode", row.get("image_frame_behavior", ""))
    row.setdefault("ocr_or_excerpt", row.get("source_description", ""))
    row.setdefault("source_description_raw", row.get("source_description", ""))
    if not row.get("historical_context_note"):
        row["historical_context_note"] = (
            "Cumulative 1830-1970 archive-box record retained as evidence of "
            "graphic communication, print circulation, advertising, public "
            "information, or visual culture in the period under review."
        )
    if not row.get("classification_rationale"):
        row["classification_rationale"] = (
            "Folder placement is provisional and derived from title, date, "
            "medium, subject terms, source institution, geography, and provider "
            "context. The folder is a filter view rather than an ownership claim."
        )
    row.setdefault("uncertainty_note", "")
    row.setdefault(
        "citation_basis",
        f"{row.get('source_name', '')}. {row.get('source_title', '')}. "
        f"{row.get('source_record_url') or row.get('source_api_url')}. "
        f"Accessed {row.get('access_date') or mc.ACCESS_DATE}.",
    )
    row.setdefault("editorial_summary", fallback_summary(row))
    for field in mx.FIELDNAMES:
        row.setdefault(field, "")
    return row


def public_context_note(value: str) -> str:
    """Remove capture-phase ranges from public reading notes.

    Phase labels such as 1970-2026 describe the capture plan, not the object,
    movement, or source record. They may remain in raw provenance paths and
    internal reports, but not as public historical labels.
    """
    note = value or ""
    note = re.sub(r"\b(?:19|20)\d{2}-20\d{2}\s+protocol capture", "Protocol-source capture", note)
    note = re.sub(r"\b(?:19|20)\d{2}-20\d{2}\s+coverage-first capture", "Coverage-first capture", note)
    note = re.sub(r"\b(?:19|20)\d{2}-20\d{2}\s+capture", "Capture", note)
    return note


def public_visible_text(value: object) -> object:
    """Sanitize public strings while leaving non-string values untouched."""
    if not isinstance(value, str):
        return value
    text = public_context_note(value)
    text = re.sub(
        r"\b(?:early|midcentury|late[- ]period)?\s*(?:1830[-–]1930|1930[-–]1970|1970[-–]2026)\s+capture rule\b",
        "Item-level source classification rule",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bCB-(?:EARLY|MIDCENTURY|LATE)[-_A-Z0-9]*(?:1830[-_]1930|1930[-_]1970|1970[-_]2026)\b",
        "CB-ITEM-LEVEL-CAPTURE",
        text,
    )
    return text


def normalize_public_surface_visible_text(payload: dict) -> dict:
    """Clean visible sheet fields and table rows generated by older captures."""
    visible_fields = (
        "descriptionSummary",
        "sourceDescription",
        "sourceNotes",
        "sourceSubjects",
        "historicalContextNote",
        "classificationRationale",
        "uncertaintyNote",
        "citationBasis",
    )
    for surface in payload.get("surfaces", []):
        for field in visible_fields:
            if field in surface:
                surface[field] = public_visible_text(surface[field])
        for table in surface.get("tables", []):
            rows = []
            for row in table.get("rows", []):
                if not isinstance(row, list):
                    rows.append(row)
                    continue
                rows.append([public_visible_text(cell) for cell in row])
            table["rows"] = rows
    return payload


def public_folder_scope_note(folder: dict) -> str:
    """Describe folder function without leaking capture-phase ranges.

    Folders are filter views. Their member dates may span decades, especially
    for regions or long-running source families, but that span is not a claim
    about a movement's historical duration.
    """
    title = folder.get("title") or "this folder"
    folder_type = folder.get("type") or "folder"
    if folder_type == "region":
        return f"Geographic and transregional filter view for {title}. Member records are sorted by item-level date when known."
    if folder_type == "theme":
        return f"Theme filter view for {title}. Membership records research relevance; it is not a single historical period."
    if folder_type == "medium":
        return f"Medium filter view for {title}. Member records are filed by material, format, or production context."
    if folder_type == "movement":
        return f"Movement or formation filter for {title}. Dates shown on leaves are item dates, not a movement-duration claim."
    return f"Filter view for {title}. Member records are sorted by item-level date when known."


def normalize_public_folder_metadata(payload: dict) -> dict:
    """Clean public folder metadata after the shared payload builder runs."""
    for folder in payload.get("folders", []):
        folder["scopeNote"] = public_folder_scope_note(folder)
        if folder.get("type") == "movement":
            start = folder.get("dateStart")
            end = folder.get("dateEnd")
            if isinstance(start, int) and isinstance(end, int) and end - start > 35:
                folder["memberDateStart"] = start
                folder["memberDateEnd"] = end
                folder["dateStart"] = None
                folder["dateEnd"] = None
                folder["chronologyStatus"] = "member_date_span_not_movement_duration"
    return payload


def is_phase_or_collection_range(row: dict[str, str]) -> bool:
    start = row.get("date_start")
    end = row.get("date_end")
    if not (start and end and start.isdigit() and end.isdigit()):
        return False
    span = int(end) - int(start)
    date_text = row.get("source_date_text", "").strip()
    if date_text in {"1830-1930", "1930-1970", "1970-2026"}:
        return True
    if span <= 40:
        return False
    blob = " ".join(
        [
            row.get("source_title", ""),
            row.get("source_object_type", ""),
            row.get("source_medium", ""),
            row.get("source_collection", ""),
            row.get("source_notes", ""),
            row.get("source_subjects", ""),
        ]
    ).lower()
    collection_terms = (
        "collection-level",
        "poster gallery",
        "gallery",
        "collection",
        "inventory",
        "biographical information",
        "source record",
        "repository text record",
    )
    return int(end) >= 2026 or any(term in blob for term in collection_terms)


def normalize_public_date_fields(row: dict[str, str]) -> dict[str, str]:
    """Prevent broad source/capture scopes from becoming object dates."""
    if not is_phase_or_collection_range(row):
        return row
    original = row.get("source_date_text") or f"{row.get('date_start')}-{row.get('date_end')}"
    row = dict(row)
    row["source_date_text"] = "source collection scope; object date not itemized"
    row["date_start"] = ""
    row["date_end"] = ""
    note = row.get("uncertainty_note", "")
    row["uncertainty_note"] = mx.clean(
        f"{note} Broad source range was treated as collection/source scope, not as the object date.",
        max_chars=520,
    ).strip()
    if not row.get("classification_rationale"):
        row["classification_rationale"] = (
            "This record represents collection/source context. It should resolve to bookmark, source dossier, "
            "or grouped support material unless item-level dates are later captured."
        )
    return row


def row_sort_year(row: dict[str, str]) -> int:
    """Sort long-range records by their terminal year.

    The archive's capture phases treat a record that spans decades as belonging
    to the phase where its end year lands. Keeping the same rule in the static
    payload prevents ranges such as 1965-1990 from being visually filed with
    the 1960s merely because their start year is early.
    """
    year = row.get("date_end") or row.get("date_start")
    return int(year) if year and year.isdigit() else 9999


def dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    best: dict[tuple[str, str], dict[str, str]] = {}

    def score(row: dict[str, str]) -> tuple[int, int, int, int]:
        image_rank = {
            "IMG03": 5,
            "IMG02": 4,
            "IMG01": 3,
            "IMG04": 2,
            "IMG00": 1,
        }.get(row.get("image_presence_code") or "IMG00", 0)
        text_rank = max(
            len(row.get("editorial_summary") or ""),
            len(row.get("source_description") or ""),
            len(row.get("ocr_or_excerpt") or ""),
        )
        parsed_rank = 1 if row.get("parser_status") == "ok" else 0
        rights_rank = 1 if row.get("rights_review_required") == "true" else 0
        return image_rank, text_rank, parsed_rank, rights_rank

    for row in rows:
        key = (
            row.get("source_name", ""),
            row.get("source_identifier") or row.get("source_record_url") or row.get("source_title", ""),
        )
        current = best.get(key)
        if current is None or score(row) > score(current):
            best[key] = row
    return list(best.values())


def enhance_payload(payload: dict, rows: list[dict[str, str]]) -> dict:
    by_capture = {row.get("capture_id", ""): row for row in rows}
    payload["meta"] = {
        "generatedAt": ACCESS_DATE,
        "status": "generated",
        "note": "Generated cumulative 1830-1970 archive-box payload. Static export; not final publication data.",
    }
    for surface in payload.get("surfaces", []):
        row = by_capture.get(surface.get("sourceRecordId", ""))
        if not row:
            continue
        surface["descriptionSummary"] = (
            row.get("editorial_summary")
            or surface.get("descriptionSummary")
            or surface.get("sourceDescription")
            or ""
        )
        surface["sourceDescription"] = row.get("source_description") or surface.get("sourceDescription") or ""
        surface["historicalContextNote"] = public_context_note(row.get("historical_context_note", ""))
        surface["classificationRationale"] = row.get("classification_rationale")
        surface["uncertaintyNote"] = row.get("uncertainty_note")
        surface["citationBasis"] = row.get("citation_basis")
        image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
        if image:
            image["expectation"] = row.get("image_expectation")
            image["parserStatus"] = row.get("parser_status")
            image["displayMode"] = row.get("display_mode") or row.get("image_frame_behavior")
            if row.get("image_presence_code") == "IMG00":
                image["placeholderText"] = (
                    row.get("image_state_review_note")
                    or "Image evidence remains source-linked; this project does not display a local copy."
                )
    return payload


def table_rows(surface: dict, kind: str) -> int:
    for table in surface.get("tables", []):
        if table.get("kind") == kind:
            return len(table.get("rows", []))
    return 0


def table_map(surface: dict) -> dict[str, dict]:
    return {
        table.get("kind", ""): table
        for table in surface.get("tables", [])
        if isinstance(table, dict)
    }


def table_row_value(surface: dict, kind: str, label_terms: tuple[str, ...]) -> str:
    terms = tuple(term.lower() for term in label_terms)
    for label, value in table_map(surface).get(kind, {}).get("rows", []):
        if any(term in str(label).lower() for term in terms):
            return str(value)
    return ""


def reading_length(surface: dict) -> int:
    return len(
        " ".join(
            str(surface.get(key) or "")
            for key in (
                "descriptionSummary",
                "sourceDescription",
                "historicalContextNote",
                "sourceNotes",
                "sourceSubjects",
            )
        ).strip()
    )


def stable_hash(value: str) -> int:
    h = 2166136261
    for char in value:
        h ^= ord(char)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def appendix_rule(surface: dict) -> tuple[str | None, list[str]]:
    """Return the production AX layout and reasons for one appendix packet.

    The rule mirrors `frontend/src/lib/paginate.ts`: a surface gets at most one
    appendix packet, selected by evidence priority rather than generic table
    overflow. Text leaves stay reading/image-only; evidence ledgers move here.
    """
    if surface.get("surfaceType") != "sheet":
        return None, []

    tables = table_map(surface)
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    image_state = image.get("state")
    folders = surface.get("folders") if isinstance(surface.get("folders"), list) else []
    child_count = len(surface.get("compoundChildren") or [])
    total_rows = sum(len(table.get("rows", [])) for table in tables.values())
    source_links = table_row_value(surface, "CITATIONS", ("source links", "source urls", "source url"))
    multi_source_list = source_links.count("http://") + source_links.count("https://") >= 2
    protocol_text = " ".join(
        str(surface.get(key) or "")
        for key in (
            "historicalContextNote",
            "classificationRationale",
            "citationBasis",
        )
    )
    rights = surface.get("rights") if isinstance(surface.get("rights"), dict) else {}
    protocol_text = f"{protocol_text} {rights.get('label', '')}"
    surface_hash = stable_hash(surface.get("surfaceId", ""))
    protocol_low = protocol_text.lower()
    explicit_protocol_note = any(
        term in protocol_low
        for term in ("manual review", "protocol-sensitive", "source-only", "source only", "suppress", "sensitive")
    )
    source_policy_context = image_state == "IMG02" and reading_length(surface) >= 1500 and surface_hash % 4 == 0
    display_policy = rights.get("displayPolicy") or rights.get("display_policy") or ""
    review_gates = surface.get("reviewGates") if isinstance(surface.get("reviewGates"), dict) else {}
    rights_reviewed = bool(review_gates.get("rightsReviewed"))
    non_blank_rights_evidence = (
        image_state in {"IMG01", "IMG02", "IMG03"}
        and (display_policy != "open_image_frame" or not rights_reviewed)
        and reading_length(surface) >= 900
        and surface_hash % 6 == 0
    )

    if image_state == "IMG00":
        return "AX01.rights", ["rights/image evidence continuation"]
    if multi_source_list or child_count >= 3:
        return "AX02.citation", ["source/citation register"]
    if table_rows(surface, "RELATIONS") > 4 or len(folders) >= 4 or child_count > 0:
        return "AX03.relations", ["relations/classification appendix"]
    if non_blank_rights_evidence:
        return "AX01.rights", ["rights/image display evidence continuation"]
    if explicit_protocol_note or source_policy_context:
        return "AX04.context", ["protocol/context packet"]
    if total_rows >= 30 and reading_length(surface) >= 900 and surface_hash % 5 == 0:
        layout = "AX06.typed-index" if surface_hash % 3 == 0 else "AX05.statement"
        return layout, ["source verification dossier"]
    return None, []


def attach_structural_collections(payload: dict) -> dict:
    """Expose non-sheet archive structures in the static payload.

    The frontend can still paginate these virtually, but the data layer should
    explicitly acknowledge bookmarks, appendix candidates, and filing/register
    records so the archive does not collapse into a flat list of sheets.
    """
    folders = payload.get("folders", [])
    surfaces = payload.get("surfaces", [])
    by_surface = {surface.get("surfaceId"): surface for surface in surfaces}

    payload["bookmarks"] = [
        {
            "bookmarkId": f"BMK-{folder.get('folderId')}",
            "folderId": folder.get("folderId"),
            "type": folder.get("type"),
            "title": folder.get("title"),
            "dateStart": folder.get("dateStart"),
            "dateEnd": folder.get("dateEnd"),
            "surfaceCount": len(folder.get("surfaceIds", [])),
            "scopeNote": folder.get("scopeNote"),
            "displayRule": "one bookmark reading-note leaf after folder register",
        }
        for folder in folders
    ]

    appendix_candidates = []
    for surface in surfaces:
        layout_id, reasons = appendix_rule(surface)
        if reasons:
            total_rows = sum(len(table.get("rows", [])) for table in surface.get("tables", []))
            appendix_candidates.append(
                {
                    "appendixId": f"APP-{surface.get('surfaceId')}",
                    "surfaceId": surface.get("surfaceId"),
                    "title": surface.get("title"),
                    "displayNumber": surface.get("provisionalDisplayNumber"),
                    "layoutId": layout_id,
                    "reasons": reasons,
                    "tableRows": total_rows,
                }
            )
    payload["appendices"] = appendix_candidates

    payload["registrationCards"] = [
        {
            "registrationId": f"REGCARD-{folder.get('folderId')}",
            "folderId": folder.get("folderId"),
            "type": folder.get("type"),
            "title": folder.get("title"),
            "memberPages": [
                {
                    "surfaceId": sid,
                    "displayNumber": (by_surface.get(sid) or {}).get("provisionalDisplayNumber"),
                    "title": (by_surface.get(sid) or {}).get("title"),
                }
                for sid in folder.get("surfaceIds", [])
                if sid in by_surface
            ],
            "displayRule": "folder membership ledger; folder is a filter, not a container",
        }
        for folder in folders
    ]
    return payload


def main() -> None:
    rows: list[dict[str, str]] = []
    for path in RECORD_FILES:
        rows.extend(read_rows(path))
    rows = dedupe_rows([normalize_public_date_fields(fill_enrichment_defaults(row)) for row in rows])
    rows.sort(key=lambda r: (row_sort_year(r), r.get("source_title", "")))

    payload = mc.build_public_payload(rows)
    payload = enhance_payload(payload, rows)
    payload = normalize_payload(payload)
    payload = normalize_public_surface_visible_text(payload)
    payload = normalize_public_folder_metadata(payload)
    payload = attach_structural_collections(payload)

    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    for path in PAYLOAD_PATHS:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    image_counter = Counter(surface.get("image", {}).get("state", "IMG00") for surface in payload.get("surfaces", []))
    source_visible = sum(image_counter[state] for state in ("IMG01", "IMG02", "IMG03"))
    publication_weights = {
        "IMG03": 0.9,
        "IMG02": 0.55,
        "IMG01": 0.3,
        "IMG00": 0.0,
        "IMG04": 0.0,
    }
    weighted_ready = sum(
        publication_weights.get(surface.get("image", {}).get("state", "IMG00"), 0.0)
        for surface in payload.get("surfaces", [])
    )
    total = len(payload.get("surfaces", []))
    source_visible_coverage = round(source_visible / total * 100, 2) if total else 0
    weighted_coverage = round(weighted_ready / total * 100, 2) if total else 0
    print(f"rows={len(rows)}")
    print(f"surfaces={total}")
    print(f"folders={len(payload.get('folders', []))}")
    print(f"image_states={dict(sorted(image_counter.items()))}")
    print(f"source_visible_image_ready={source_visible}/{total} ({source_visible_coverage}%)")
    print(f"weighted_publication_image_score={round(weighted_ready, 2)}/{total} ({weighted_coverage}%)")


if __name__ == "__main__":
    main()
