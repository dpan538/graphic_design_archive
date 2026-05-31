from __future__ import annotations

import csv
import json
import re
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import run_midcentury_capture_1930_1970 as mc
import run_midcentury_expansion_capture_1931_1970 as mx


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_cooperhewitt_graphql_image_ready_1830_2026_raw"
RECORDS_CSV = DATA / "capture_batch_cooperhewitt_graphql_image_ready_1830_2026_records.csv"
SUMMARY_CSV = DATA / "capture_batch_cooperhewitt_graphql_image_ready_1830_2026_source_summary.csv"

ACCESS_DATE = "2026-05-31"
SOURCE_ID = "GSE038"
SOURCE_NAME = "Cooper Hewitt Collection GraphQL API"
GRAPHQL_URL = "https://api.cooperhewitt.org/"
USER_AGENT = "ModernGDHistory/0.1 cooperhewitt-image-ready"
YEAR_START = 1830
YEAR_END = 2026
MAX_ROWS = 180
PAGE_SIZE = 30
FIELDNAMES = mx.FIELDNAMES

QUERY_PLAN = [
    ("CH01", "cooperhewitt_poster_records", "poster", 70),
    ("CH02", "cooperhewitt_packaging_records", "packaging", 30),
    ("CH03", "cooperhewitt_label_records", "label", 25),
    ("CH04", "cooperhewitt_brochure_records", "brochure", 20),
    ("CH05", "cooperhewitt_advertising_records", "advertising", 25),
    ("CH06", "cooperhewitt_typographic_records", "typography", 15),
]

YEAR_RANGES = [
    (1830, 1930),
    (1931, 1970),
    (1971, 2000),
    (2001, 2026),
]

GRAPHIC_TERMS = (
    "advertis",
    "book cover",
    "brochure",
    "catalogue",
    "commercial",
    "graphic",
    "identity",
    "label",
    "package",
    "packaging",
    "poster",
    "typograph",
)


def clean(value: Any, *, max_chars: int = 700) -> str:
    if isinstance(value, list):
        value = "; ".join(clean(item, max_chars=max_chars) for item in value if item)
    if isinstance(value, dict):
        if "value" in value:
            value = value.get("value")
        elif "title" in value:
            value = value.get("title")
        else:
            value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rsplit(" ", 1)[0] + "…"


def gql_value(value: Any) -> str:
    if isinstance(value, dict):
        if "value" in value:
            return clean(value.get("value"))
        summary = value.get("summary")
        if isinstance(summary, dict) and summary.get("title"):
            return clean(summary.get("title"))
    return clean(value)


def gql_values(values: Any, *, max_chars: int = 900) -> str:
    if not isinstance(values, list):
        return gql_value(values)[:max_chars]
    return clean("; ".join(gql_value(value) for value in values if gql_value(value)), max_chars=max_chars)


def graphql_query(general: str, page: int, year_start: int, year_end: int) -> str:
    general_json = json.dumps(general)
    return f"""
    {{
      object(
        general: {general_json},
        hasImages: true,
        yearRange: {{from: {year_start}, to: {year_end}}},
        page: {page},
        size: {PAGE_SIZE}
      ) {{
        id
        collectionsOnlineId
        title
        date
        summary
        description
        medium
        material
        measurements
        department
        geography
        legal
        inscription
        note
        multimedia
        media {{
          caption
          preview
          large
          zoom
          original
        }}
        agent {{
          name
          role
          nationality
        }}
        subject {{
          name
          role
        }}
        tag {{
          name
        }}
      }}
    }}
    """


def fetch_graphql(query: str) -> dict[str, Any]:
    request = urllib.request.Request(
        GRAPHQL_URL,
        data=json.dumps({"query": query}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"], ensure_ascii=False)[:1200])
    return payload


def write_raw(name: str, payload: dict[str, Any]) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path.relative_to(ROOT))


def existing_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in DATA.glob("capture_batch_*_records.csv"):
        if not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                keys.add((row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", "")))
    return keys


def date_fields(item: dict[str, Any]) -> tuple[str, str, str]:
    date_values = item.get("date") if isinstance(item.get("date"), list) else []
    date_text = gql_values(date_values, max_chars=240)
    starts: list[int] = []
    ends: list[int] = []
    for value in date_values:
        if not isinstance(value, dict):
            continue
        start = clean(value.get("from"))
        end = clean(value.get("to"))
        if start.isdigit():
            starts.append(int(start))
        if end.isdigit():
            ends.append(int(end))
        years = [int(year) for year in re.findall(r"(?<!\d)((?:18|19|20)\d{2})(?!\d)", clean(value.get("value")))]
        starts.extend(years)
        ends.extend(years)
    if starts or ends:
        return str(min(starts or ends)), str(max(ends or starts)), date_text
    years = [int(year) for year in re.findall(r"(?<!\d)((?:18|19|20)\d{2})(?!\d)", date_text)]
    if years:
        return str(min(years)), str(max(years)), date_text
    return "", "", date_text


def terminal_year_in_scope(date_start: str, date_end: str) -> bool:
    year = int(date_end) if date_end and date_end.isdigit() else int(date_start) if date_start and date_start.isdigit() else None
    return year is not None and YEAR_START <= year <= YEAR_END


def first_media(item: dict[str, Any]) -> tuple[str, str, str, bool]:
    raw_media = item.get("media") if isinstance(item.get("media"), list) else []
    raw_multimedia = item.get("multimedia") if isinstance(item.get("multimedia"), list) else []
    media_items = raw_media + raw_multimedia
    for media in media_items:
        if not isinstance(media, dict):
            continue
        url = ""
        for key in ("large", "preview", "zoom", "original"):
            value = media.get(key)
            if isinstance(value, dict) and value.get("url"):
                url = clean(value.get("url"), max_chars=1000)
                break
        if not url:
            continue
        caption = clean(media.get("caption") or media.get("summary"), max_chars=240)
        media_id = clean(media.get("id"), max_chars=80)
        cc0 = bool(media.get("cc0"))
        return url, caption, media_id, cc0
    return "", "", "", False


def agent_names(item: dict[str, Any]) -> str:
    agents = item.get("agent") if isinstance(item.get("agent"), list) else []
    names: list[str] = []
    for agent in agents:
        if not isinstance(agent, dict):
            continue
        name = gql_values(agent.get("name"), max_chars=180)
        roles = gql_values(agent.get("role"), max_chars=120)
        if name and roles:
            names.append(f"{name} ({roles})")
        elif name:
            names.append(name)
    return clean("; ".join(names), max_chars=500)


def subject_terms(item: dict[str, Any]) -> str:
    parts = [
        gql_values(item.get("subject"), max_chars=400),
        gql_values(item.get("tag"), max_chars=400),
        gql_values(item.get("classification"), max_chars=240),
    ]
    return clean("; ".join(part for part in parts if part), max_chars=700)


def is_graphic_relevant(item: dict[str, Any]) -> bool:
    title = gql_values(item.get("title"), max_chars=260)
    summary = gql_value(item.get("summary"))
    if title.lower().startswith("illustration for"):
        return False
    blob = " ".join(
        [
            title,
            summary,
            gql_values(item.get("description"), max_chars=500),
            gql_values(item.get("medium"), max_chars=400),
            gql_values(item.get("material"), max_chars=300),
            subject_terms(item),
        ]
    ).lower()
    return any(term in blob for term in GRAPHIC_TERMS)


def geography_value(value: Any) -> str:
    if not isinstance(value, dict):
        return clean(value, max_chars=260)
    names = []
    if isinstance(value.get("name"), str):
        names.append(value["name"])
    for key in ("country", "city", "state", "continent"):
        part = value.get(key)
        if isinstance(part, dict) and part.get("value"):
            names.append(clean(part.get("value")))
    return clean(" / ".join(dict.fromkeys(name for name in names if name)), max_chars=260)


def source_record_url(item: dict[str, Any]) -> str:
    online_id = clean(item.get("collectionsOnlineId"))
    if online_id:
        return f"https://collection.cooperhewitt.org/objects/{online_id}/"
    object_id = clean(item.get("id"))
    return f"https://collection.cooperhewitt.org/objects/{object_id}/"


def row_from_item(
    item: dict[str, Any],
    direction_id: str,
    direction_name: str,
    api_label: str,
    raw_path: str,
) -> dict[str, str] | None:
    date_start, date_end, date_text = date_fields(item)
    if not terminal_year_in_scope(date_start, date_end) or not is_graphic_relevant(item):
        return None
    image_url, media_caption, media_id, cc0 = first_media(item)
    if not image_url:
        return None

    title = gql_values(item.get("title"), max_chars=420) or gql_value(item.get("summary")) or "Untitled Cooper Hewitt object"
    description = clean(
        "; ".join(
            part
            for part in [
                gql_values(item.get("description"), max_chars=700),
                gql_values(item.get("inscription"), max_chars=360),
                media_caption,
            ]
            if part
        ),
        max_chars=1000,
    )
    medium = clean(
        "; ".join(
            part
            for part in [
                gql_values(item.get("medium"), max_chars=360),
                gql_values(item.get("material"), max_chars=260),
                gql_values(item.get("measurements"), max_chars=260),
            ]
            if part
        ),
        max_chars=700,
    )
    legal = clean(item.get("legal"), max_chars=700)
    geography = geography_value(item.get("geography"))
    department = gql_values(item.get("department"), max_chars=260)
    subjects = subject_terms(item)
    viewer = source_record_url(item)
    code = "IMG03" if cc0 else "IMG02"
    basis = (
        "Cooper Hewitt media field marks this image as CC0 and exposes a stable source-hosted image URL."
        if cc0
        else "Cooper Hewitt GraphQL exposes a source-hosted collection image; image display stays source-linked and item rights remain authoritative."
    )
    rights = mc.image_fields(
        code,
        basis,
        image_url=image_url,
        viewer=viewer,
        confidence="high" if cc0 else "medium",
        rights_review_required=not cc0,
        local_copy_permitted=False,
        note="Design-specific museum source; no local copy. Keep Cooper Hewitt object page visible.",
    )
    row = {
        "capture_id": "",
        "direction_id": direction_id,
        "direction_name": direction_name,
        "source_id": SOURCE_ID,
        "source_name": SOURCE_NAME,
        "source_api_url": api_label,
        "capture_status": "captured",
        "source_identifier": clean(item.get("id")) or clean(item.get("collectionsOnlineId")),
        "source_record_url": viewer,
        "source_title": title,
        "source_creator": agent_names(item),
        "source_date_text": date_text,
        "date_start": date_start,
        "date_end": date_end,
        "source_place_text": geography,
        "source_object_type": gql_value(item.get("summary")) or "Cooper Hewitt collection object",
        "source_medium": medium,
        "source_collection": department or "Cooper Hewitt, Smithsonian Design Museum",
        "source_description": description,
        "source_notes": clean("; ".join(part for part in [legal, media_id, gql_values(item.get("note"), max_chars=360)] if part), max_chars=700),
        "source_subjects": subjects,
        "source_rights_text": legal or ("Media cc0=true" if cc0 else "Item-level legal statement not found in GraphQL payload."),
        "rights_uri": "",
        "raw_json_path": raw_path,
        "access_date": ACCESS_DATE,
        **rights,
    }
    row["image_expectation"] = "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["source_description_raw"] = description
    row["ocr_or_excerpt"] = description or subjects or medium
    row["editorial_summary"] = mx.clean(
        f"{title} is indexed from Cooper Hewitt. {description or medium or subjects}",
        max_chars=680,
    )
    row["historical_context_note"] = (
        "Captured through Cooper Hewitt's public GraphQL API to add a design-specific museum source with object images, "
        "maker fields, medium statements, and collection links across early, midcentury, and later graphic design records."
    )
    row["classification_rationale"] = (
        "Provisional folders derive from Cooper Hewitt title, date range, department, medium/material, geography, makers, and subject/tag fields."
    )
    row["uncertainty_note"] = "Broad century date ranges are filed by terminal year; source-hosted image access is not treated as project ownership."
    row["citation_basis"] = f"Cooper Hewitt, Smithsonian Design Museum. {title}. {viewer}. Accessed {ACCESS_DATE}."
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    seen = existing_keys()
    seen_images: set[str] = set()
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []

    for direction_id, direction_name, term, limit in QUERY_PLAN:
        direction_count = 0
        for year_start, year_end in YEAR_RANGES:
            if direction_count >= limit or len(rows) >= MAX_ROWS:
                break
            page = 1
            empty_pages = 0
            while direction_count < limit and len(rows) < MAX_ROWS and empty_pages < 3:
                query = graphql_query(term, page, year_start, year_end)
                try:
                    payload = fetch_graphql(query)
                except Exception as exc:  # noqa: BLE001
                    failures.append({"direction_id": direction_id, "source_name": SOURCE_NAME, "error": str(exc)})
                    break
                raw_path = write_raw(f"{direction_name}_{year_start}_{year_end}_page_{page}.json", payload)
                items = payload.get("data", {}).get("object") or []
                if not items:
                    break
                added = 0
                for item in items:
                    row = row_from_item(
                        item,
                        direction_id,
                        direction_name,
                        f"{GRAPHQL_URL} :: {term} :: {year_start}-{year_end} :: page {page}",
                        raw_path,
                    )
                    if not row:
                        continue
                    key = (row["source_name"], row["source_identifier"])
                    image_key = row.get("image_url_detected", "")
                    if key in seen or image_key in seen_images:
                        continue
                    seen.add(key)
                    seen_images.add(image_key)
                    rows.append(row)
                    direction_count += 1
                    added += 1
                    if direction_count >= limit or len(rows) >= MAX_ROWS:
                        break
                empty_pages = empty_pages + 1 if added == 0 else 0
                page += 1
                time.sleep(0.45)

    rows.sort(key=lambda row: (int(row.get("date_end") or row.get("date_start") or 9999), row.get("source_title", "")))
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"CHW2026R{index:03d}"

    with RECORDS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["direction_id"]].append(row)
    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "direction_id",
            "source_id",
            "source_name",
            "captured_count",
            "failure_count",
            "img00_count",
            "img01_count",
            "img02_count",
            "img03_count",
            "img04_count",
            "notes",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for direction_id, items in sorted(grouped.items()):
            counter = Counter(row["image_presence_code"] for row in items)
            writer.writerow(
                {
                    "direction_id": direction_id,
                    "source_id": SOURCE_ID,
                    "source_name": SOURCE_NAME,
                    "captured_count": str(len(items)),
                    "failure_count": str(sum(1 for failure in failures if failure["direction_id"] == direction_id)),
                    "img00_count": str(counter.get("IMG00", 0)),
                    "img01_count": str(counter.get("IMG01", 0)),
                    "img02_count": str(counter.get("IMG02", 0)),
                    "img03_count": str(counter.get("IMG03", 0)),
                    "img04_count": str(counter.get("IMG04", 0)),
                    "notes": "Design-specific Cooper Hewitt GraphQL image-ready capture; source-hosted image URLs only, no local copies.",
                }
            )

    counter = Counter(row["image_presence_code"] for row in rows)
    print(f"{RECORDS_CSV.relative_to(ROOT)}: {len(rows)} rows")
    print(f"{SUMMARY_CSV.relative_to(ROOT)}: summary written")
    print("image distribution:", dict(sorted(counter.items())))
    if failures:
        print("failures:", json.dumps(failures[:8], ensure_ascii=False))


if __name__ == "__main__":
    main()
