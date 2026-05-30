from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

CAPTURES = DATA / "capture_batch_001_records.csv"
SCOPE_CELLS = DATA / "experimental_ingest_shortlist.csv"
ASSIGNMENTS = DATA / "capture_batch_001_cell_assignments.csv"
SUMMARY = DATA / "capture_batch_001_cell_summary.csv"
NEXT_QUEUE = DATA / "capture_batch_001_next_generation_queue.csv"


ASSIGNMENT_FIELDS = [
    "capture_id",
    "source_id",
    "source_name",
    "source_title",
    "image_presence_code",
    "assigned_cell_id",
    "assigned_cell_name",
    "assignment_type",
    "assignment_confidence",
    "assignment_basis",
    "matched_terms",
    "recommended_next_step",
]

SUMMARY_FIELDS = [
    "cell_id",
    "cell_name",
    "cell_type",
    "assigned_count",
    "img00_count",
    "img01_count",
    "img02_count",
    "img03_count",
    "img04_count",
    "source_names",
    "sample_capture_ids",
    "cell_status",
    "next_generation_action",
]

QUEUE_FIELDS = [
    "queue_id",
    "cell_id",
    "cell_name",
    "cell_type",
    "priority",
    "reason",
    "recommended_query",
    "recommended_sources",
    "required_img_states",
    "minimum_next_capture_count",
]


PROPOSED_CELLS = {
    "PC01": {
        "name": "Art Nouveau and Belle Epoque poster culture",
        "query": "Mucha OR Toulouse-Lautrec OR La Plume OR Moulin Rouge poster",
        "sources": "AIC; Cleveland; V&A; Gallica; Europeana",
    },
    "PC02": {
        "name": "World War public-information and propaganda posters",
        "query": "war poster OR liberty loan OR civilian defense OR enemy poster",
        "sources": "LOC; AIC; NARA; Imperial War Museums; Europeana",
    },
    "PC03": {
        "name": "1970s London political solidarity posters",
        "query": "political poster London 1970 Zimbabwe imperialism farm workers prisoners Ireland",
        "sources": "V&A; Bishopsgate Institute; MayDay Rooms; IISG; Interference Archive",
    },
    "PC04": {
        "name": "South and Central Asian political poster collections",
        "query": "Pakistan Afghanistan Balochistan political posters Quetta Taliban poster",
        "sources": "LOC; British Library; SAADA; regional archives",
    },
    "PC05": {
        "name": "Contemporary campaign graphics and network circulation",
        "query": "Obama Hope poster campaign graphic Shepard Fairey",
        "sources": "AIC; Smithsonian; MoMA; Internet Archive",
    },
    "PC06": {
        "name": "Exhibition poster as design-history metadata",
        "query": "exhibition poster graphic design poster show poster",
        "sources": "AIC; V&A; Cleveland; MoMA; museum APIs",
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def contains(text: str, *patterns: str) -> list[str]:
    found = []
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(pattern)
    return found


def normalize_blob(row: dict[str, str]) -> str:
    return " ".join(
        [
            row.get("source_title", ""),
            row.get("source_creator", ""),
            row.get("source_date_text", ""),
            row.get("source_place_text", ""),
            row.get("source_object_type", ""),
            row.get("source_medium", ""),
            row.get("source_collection", ""),
        ]
    )


def load_existing_cells() -> dict[str, str]:
    cells: dict[str, str] = {}
    for row in read_csv(SCOPE_CELLS):
        cell_id = row.get("scope_cell_id", "")
        if cell_id:
            cells[cell_id] = row["candidate_name"].replace(" first-ingest cell", "")
    return cells


def assign(row: dict[str, str], existing_cells: dict[str, str]) -> dict[str, str]:
    blob = normalize_blob(row)
    title = row["source_title"]

    rules = [
        ("C02", "existing_scope_cell", "high", contains(blob, r"\bPolish\b", r"\bStasis\b", r"\bCzerniawski\b", r"\bJaniga\b"), "Polish poster-school candidate; verify object-level relation before promotion."),
        ("C12", "existing_scope_cell_contextual", "medium", contains(blob, r"\bZimbabwe\b", r"\bAfrica\b", r"\bimperialism\b", r"\bPeople'?s War\b"), "Southern African liberation/political print context; not automatically Medu."),
        ("C14", "existing_scope_cell_contextual", "low", contains(blob, r"\bAIDS\b", r"\bactivist\b"), "Thematic AIDS/activist graphic context; not automatically Gran Fury/ACT UP."),
        ("C04", "existing_scope_cell_contextual", "low", contains(blob, r"\bLatin America\b", r"\bBrazil\b", r"\bBelize\b", r"\bUruguay\b"), "Latin American political poster context; not automatically Taller de Grafica Popular."),
    ]
    for cell_id, assignment_type, confidence, matched, next_step in rules:
        if matched:
            return {
                "assigned_cell_id": cell_id,
                "assigned_cell_name": existing_cells.get(cell_id, cell_id),
                "assignment_type": assignment_type,
                "assignment_confidence": confidence,
                "assignment_basis": "keyword_rule",
                "matched_terms": "; ".join(matched),
                "recommended_next_step": next_step,
            }

    proposed_rules = [
        ("PC01", "high", contains(blob, r"\bMucha\b", r"\bToulouse-Lautrec\b", r"\bMoulin Rouge\b", r"\bLa Plume\b", r"\bSarah Bernhardt\b", r"\bMay Milton\b", r"\bMay Belfort\b", r"\bYvette Guilbert\b", r"\bLa Goulue\b"), "Create or confirm a poster-culture cell for Art Nouveau/Belle Epoque commercial lithography."),
        ("PC02", "high", contains(blob, r"\bLiberty Loan\b", r"\bCivilian Defense\b", r"\bdefense poster\b", r"\bWar Production\b", r"\bOffice of War Information\b", r"\bOffice of Emergency Management\b", r"\bAxis\b", r"\benemy\b", r"\bKaiser\b"), "Create or confirm a public-information/war-propaganda poster cell."),
        ("PC03", "high", contains(blob, r"\bIreland\b", r"\bFarm Workers\b", r"\bHull Prisoners\b", r"\bSocialist World\b", r"\bLondon\b.*\b197[0-9]\b"), "Create or confirm a 1970s London political-solidarity poster cell."),
        ("PC04", "high", contains(blob, r"\bPakistan\b", r"\bAfghanistan\b", r"\bBalochistan\b", r"\bQuetta\b", r"\bTaliban\b"), "Create or confirm a South/Central Asian political poster collection cell."),
        ("PC05", "high", contains(blob, r"\bObama\b", r"\bHope\b"), "Create or confirm a contemporary campaign/network graphic cell."),
        ("PC06", "medium", contains(blob, r"\bExhibition Poster\b", r"\bPoster Show\b", r"\bPicture Posters\b", r"\bModern Poster\b"), "Create or confirm an exhibition-poster metadata cell."),
    ]
    for cell_id, confidence, matched, next_step in proposed_rules:
        if matched:
            return {
                "assigned_cell_id": cell_id,
                "assigned_cell_name": PROPOSED_CELLS[cell_id]["name"],
                "assignment_type": "proposed_new_cell",
                "assignment_confidence": confidence,
                "assignment_basis": "keyword_rule",
                "matched_terms": "; ".join(matched),
                "recommended_next_step": next_step,
            }

    return {
        "assigned_cell_id": "UNASSIGNED",
        "assigned_cell_name": "Unassigned capture pool",
        "assignment_type": "unassigned_pool",
        "assignment_confidence": "unknown",
        "assignment_basis": "no_rule_match",
        "matched_terms": "",
        "recommended_next_step": "Review manually or add a new cell rule before next generation.",
    }


def build_assignment_rows(captures: list[dict[str, str]], existing_cells: dict[str, str]) -> list[dict[str, str]]:
    rows = []
    for row in captures:
        assignment = assign(row, existing_cells)
        rows.append(
            {
                "capture_id": row["capture_id"],
                "source_id": row["source_id"],
                "source_name": row["source_name"],
                "source_title": row["source_title"],
                "image_presence_code": row["image_presence_code"],
                **assignment,
            }
        )
    return rows


def build_summary_rows(assignments: list[dict[str, str]], existing_cells: dict[str, str]) -> list[dict[str, str]]:
    all_cells = {**existing_cells, **{key: value["name"] for key, value in PROPOSED_CELLS.items()}, "UNASSIGNED": "Unassigned capture pool"}
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in assignments:
        grouped[row["assigned_cell_id"]].append(row)

    rows = []
    for cell_id, cell_name in all_cells.items():
        items = grouped.get(cell_id, [])
        image_counts = Counter(item["image_presence_code"] for item in items)
        source_names = sorted({item["source_name"] for item in items})
        if cell_id.startswith("C"):
            cell_type = "existing_scope_cell"
        elif cell_id.startswith("PC"):
            cell_type = "proposed_new_cell"
        else:
            cell_type = "unassigned_pool"
        if items and cell_id.startswith("C"):
            status = "has_candidates"
            action = "Review candidates against cell definition before source-record generation."
        elif items and cell_id.startswith("PC"):
            status = "new_cell_candidate"
            action = "Decide whether to add this proposed cell to the historical framework."
        elif cell_id.startswith("C"):
            status = "empty_after_capture"
            action = "Needs targeted query/source plan in the next generation."
        else:
            status = "needs_review" if items else "empty"
            action = "Review unassigned rows and decide whether new cells are needed."

        rows.append(
            {
                "cell_id": cell_id,
                "cell_name": cell_name,
                "cell_type": cell_type,
                "assigned_count": str(len(items)),
                "img00_count": str(image_counts.get("IMG00", 0)),
                "img01_count": str(image_counts.get("IMG01", 0)),
                "img02_count": str(image_counts.get("IMG02", 0)),
                "img03_count": str(image_counts.get("IMG03", 0)),
                "img04_count": str(image_counts.get("IMG04", 0)),
                "source_names": "; ".join(source_names),
                "sample_capture_ids": "; ".join(item["capture_id"] for item in items[:5]),
                "cell_status": status,
                "next_generation_action": action,
            }
        )
    return rows


def build_queue_rows(summary_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    queue_rows = []
    queue_id = 1
    for row in summary_rows:
        include = row["cell_status"] in {"empty_after_capture", "new_cell_candidate", "needs_review"}
        if not include:
            continue
        cell_id = row["cell_id"]
        if cell_id in PROPOSED_CELLS:
            query = PROPOSED_CELLS[cell_id]["query"]
            sources = PROPOSED_CELLS[cell_id]["sources"]
            priority = "review"
            reason = "Captured rows suggest a new cell or expanded scope."
            minimum = "5"
        elif cell_id.startswith("C"):
            query = row["cell_name"]
            sources = "Use source registry and Deep Research source redundancy candidates."
            priority = "high" if row["assigned_count"] == "0" else "review"
            reason = "Existing scope cell received no candidates in this capture pass."
            minimum = "3"
        else:
            query = "manual review of unassigned capture rows"
            sources = "Current capture pool"
            priority = "review"
            reason = "Rows did not match existing or proposed rules."
            minimum = "0"
        queue_rows.append(
            {
                "queue_id": f"NGQ{queue_id:03d}",
                "cell_id": cell_id,
                "cell_name": row["cell_name"],
                "cell_type": row["cell_type"],
                "priority": priority,
                "reason": reason,
                "recommended_query": query,
                "recommended_sources": sources,
                "required_img_states": "IMG00; IMG01; IMG02; IMG03; IMG04",
                "minimum_next_capture_count": minimum,
            }
        )
        queue_id += 1
    return queue_rows


def main() -> None:
    captures = read_csv(CAPTURES)
    existing_cells = load_existing_cells()
    assignments = build_assignment_rows(captures, existing_cells)
    summary_rows = build_summary_rows(assignments, existing_cells)
    queue_rows = build_queue_rows(summary_rows)

    write_csv(ASSIGNMENTS, ASSIGNMENT_FIELDS, assignments)
    write_csv(SUMMARY, SUMMARY_FIELDS, summary_rows)
    write_csv(NEXT_QUEUE, QUEUE_FIELDS, queue_rows)

    print(f"{ASSIGNMENTS.relative_to(ROOT)}: {len(assignments)} assignment rows")
    print(f"{SUMMARY.relative_to(ROOT)}: {len(summary_rows)} cell summary rows")
    print(f"{NEXT_QUEUE.relative_to(ROOT)}: {len(queue_rows)} next-generation rows")


if __name__ == "__main__":
    main()
