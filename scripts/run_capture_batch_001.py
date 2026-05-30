from __future__ import annotations

import csv
import json
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_001_raw"
RECORDS_CSV = DATA / "capture_batch_001_records.csv"
SUMMARY_CSV = DATA / "capture_batch_001_source_summary.csv"
SOURCE_REGISTRY = DATA / "source_registry.csv"

ACCESS_DATE = "2026-05-30"
USER_AGENT = "ModernGDHistory/0.1 rights-aware capture batch"


CAPTURE_PLAN = [
    {
        "direction_id": "D01",
        "direction_name": "open_and_restricted_museum_poster_objects",
        "source_name": "Art Institute of Chicago API",
        "limit": 15,
        "adapter": "aic",
        "url": "https://api.artic.edu/api/v1/artworks/search?"
        + urllib.parse.urlencode(
            {
                "q": "poster",
                "fields": ",".join(
                    [
                        "id",
                        "title",
                        "artist_display",
                        "date_display",
                        "place_of_origin",
                        "medium_display",
                        "classification_titles",
                        "api_link",
                        "image_id",
                        "thumbnail",
                        "is_public_domain",
                        "artist_id",
                        "date_start",
                        "date_end",
                    ]
                ),
                "page": "1",
                "limit": "15",
            }
        ),
    },
    {
        "direction_id": "D01",
        "direction_name": "open_and_restricted_museum_poster_objects",
        "source_name": "Cleveland Museum Open Access API",
        "limit": 10,
        "adapter": "cleveland",
        "url": "https://openaccess-api.clevelandart.org/api/artworks/?"
        + urllib.parse.urlencode(
            {
                "q": "poster",
                "has_image": "1",
                "limit": "10",
            }
        ),
    },
    {
        "direction_id": "D02",
        "direction_name": "design_museum_poster_catalogue_metadata",
        "source_name": "V&A Collections API",
        "limit": 15,
        "adapter": "vam",
        "url": "https://api.vam.ac.uk/v2/objects/search?"
        + urllib.parse.urlencode(
            {
                "q": "poster",
                "page_size": "15",
            }
        ),
    },
    {
        "direction_id": "D03",
        "direction_name": "public_poster_archive_search_records",
        "source_name": "Library of Congress loc.gov API",
        "limit": 10,
        "adapter": "loc",
        "url": "https://www.loc.gov/pictures/search/?"
        + urllib.parse.urlencode(
            {
                "q": "poster",
                "fo": "json",
                "c": "10",
            }
        ),
    },
]


FIELDNAMES = [
    "capture_id",
    "direction_id",
    "direction_name",
    "source_id",
    "source_name",
    "source_api_url",
    "capture_status",
    "source_identifier",
    "source_record_url",
    "source_title",
    "source_creator",
    "source_date_text",
    "date_start",
    "date_end",
    "source_place_text",
    "source_object_type",
    "source_medium",
    "source_collection",
    "source_rights_text",
    "rights_uri",
    "rights_basis",
    "image_presence_code",
    "image_presence_basis",
    "image_state_evaluation",
    "image_state_confidence",
    "rights_review_required",
    "image_state_review_note",
    "image_frame_behavior",
    "image_url_detected",
    "local_copy_permitted",
    "iiif_or_viewer_available",
    "fallback_required",
    "fallback_reason",
    "raw_json_path",
    "access_date",
]


def read_source_registry() -> dict[str, dict[str, str]]:
    with SOURCE_REGISTRY.open(encoding="utf-8", newline="") as f:
        return {row["name"]: row for row in csv.DictReader(f)}


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(text(item) for item in value if text(item))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def image_fields(
    code: str,
    basis: str,
    *,
    image_url: str = "",
    viewer: str = "",
    confidence: str = "medium",
    rights_review_required: bool = True,
    note: str = "",
) -> dict[str, str]:
    behavior = {
        "IMG00": "empty_rights_frame",
        "IMG01": "thumbnail_frame",
        "IMG02": "source_viewer_frame",
        "IMG03": "open_image_frame",
        "IMG04": "no_image_frame",
    }[code]
    return {
        "source_rights_text": basis,
        "rights_uri": "",
        "rights_basis": basis,
        "image_presence_code": code,
        "image_presence_basis": basis,
        "image_state_evaluation": f"{code}: {basis}",
        "image_state_confidence": confidence,
        "rights_review_required": "true" if rights_review_required else "false",
        "image_state_review_note": note,
        "image_frame_behavior": behavior,
        "image_url_detected": image_url,
        "local_copy_permitted": "false",
        "iiif_or_viewer_available": viewer,
        "fallback_required": "false",
        "fallback_reason": "",
    }


def parse_year(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        year = int(value)
    except (TypeError, ValueError):
        return ""
    if 1500 <= year <= 2100:
        return str(year)
    return ""


def rows_from_aic(payload: dict[str, Any], plan: dict[str, str], source: dict[str, str]) -> list[dict[str, str]]:
    rows = []
    for item in payload.get("data", [])[: int(plan["limit"])]:
        identifier = text(item.get("id"))
        public_domain = bool(item.get("is_public_domain"))
        image_id = text(item.get("image_id"))
        image_url = f"https://www.artic.edu/iiif/2/{image_id}/full/843,/0/default.jpg" if image_id else ""
        if public_domain:
            rights = image_fields(
                "IMG03",
                "AIC search API reports is_public_domain=true.",
                image_url=image_url,
                viewer=image_url,
                confidence="high",
                rights_review_required=True,
                note="Open image display candidate; final publication still needs item-page rights capture.",
            )
        elif image_id:
            rights = image_fields(
                "IMG00",
                "AIC image identifier exists, but search row does not report public-domain status.",
                image_url=image_url,
                viewer=image_url,
                confidence="high",
                rights_review_required=True,
                note="Image frame should render empty with source link until item-level rights evidence upgrades it.",
            )
        else:
            rights = image_fields(
                "IMG04",
                "AIC row does not expose an image identifier in this capture.",
                confidence="high",
                rights_review_required=False,
                note="No image frame should be rendered for this capture row.",
            )
        rows.append(
            {
                **base_row(plan, source),
                **rights,
                "capture_status": "captured",
                "source_identifier": identifier,
                "source_record_url": f"https://www.artic.edu/artworks/{identifier}",
                "source_title": text(item.get("title")),
                "source_creator": text(item.get("artist_display")),
                "source_date_text": text(item.get("date_display")),
                "date_start": parse_year(item.get("date_start")),
                "date_end": parse_year(item.get("date_end")),
                "source_place_text": text(item.get("place_of_origin")),
                "source_object_type": text(item.get("classification_titles")),
                "source_medium": text(item.get("medium_display")),
                "source_collection": "Art Institute of Chicago",
            }
        )
    return rows


def rows_from_cleveland(payload: dict[str, Any], plan: dict[str, str], source: dict[str, str]) -> list[dict[str, str]]:
    rows = []
    for item in payload.get("data", [])[: int(plan["limit"])]:
        identifier = text(item.get("accession_number") or item.get("id"))
        license_status = text(item.get("share_license_status"))
        images = item.get("images") if isinstance(item.get("images"), dict) else {}
        image_url = text(images.get("web") or images.get("print") or images.get("full")) if isinstance(images, dict) else ""
        is_open = license_status.upper() == "CC0"
        if is_open and image_url:
            rights = image_fields(
                "IMG03",
                f"Cleveland Museum API share_license_status={license_status}.",
                image_url=image_url,
                viewer=image_url,
                confidence="high",
                rights_review_required=True,
                note="Open image display candidate; local copy remains disabled until record-level review.",
            )
        elif image_url:
            rights = image_fields(
                "IMG00",
                f"Cleveland Museum API share_license_status={license_status or 'not captured'}.",
                image_url=image_url,
                viewer=image_url,
                confidence="medium",
                rights_review_required=True,
                note="Image exists but open reuse evidence was not captured.",
            )
        else:
            rights = image_fields(
                "IMG04",
                "Cleveland Museum API row did not expose an image URL in this capture.",
                confidence="high",
                rights_review_required=False,
                note="No image frame should be rendered for this capture row.",
            )
        rows.append(
            {
                **base_row(plan, source),
                **rights,
                "capture_status": "captured",
                "source_identifier": identifier,
                "source_record_url": text(item.get("url")) or f"https://www.clevelandart.org/art/{identifier}",
                "source_title": text(item.get("title")),
                "source_creator": text([creator.get("description") for creator in item.get("creators", [])] if isinstance(item.get("creators"), list) else ""),
                "source_date_text": text(item.get("creation_date")),
                "date_start": parse_year(item.get("creation_date_earliest")),
                "date_end": parse_year(item.get("creation_date_latest")),
                "source_place_text": text(item.get("culture")),
                "source_object_type": text(item.get("type")),
                "source_medium": text(item.get("technique")),
                "source_collection": text(item.get("collection") or item.get("department")),
            }
        )
    return rows


def rows_from_vam(payload: dict[str, Any], plan: dict[str, str], source: dict[str, str]) -> list[dict[str, str]]:
    rows = []
    for item in payload.get("records", [])[: int(plan["limit"])]:
        identifier = text(item.get("systemNumber"))
        images = item.get("_images") if isinstance(item.get("_images"), dict) else {}
        thumb = text(images.get("_primary_thumbnail")) if isinstance(images, dict) else ""
        iiif_base = text(images.get("_iiif_image_base_url")) if isinstance(images, dict) else ""
        viewer = iiif_base or thumb
        if iiif_base:
            rights = image_fields(
                "IMG02",
                "V&A API exposes source-hosted IIIF/image service metadata; no local copy is permitted in this pass.",
                image_url=thumb,
                viewer=viewer,
                confidence="medium",
                rights_review_required=True,
                note="Treat as source-hosted viewer candidate, not as reusable local image.",
            )
        elif thumb:
            rights = image_fields(
                "IMG01",
                "V&A API exposes a source thumbnail but no source-hosted viewer evidence was captured.",
                image_url=thumb,
                viewer=thumb,
                confidence="medium",
                rights_review_required=True,
                note="Thumbnail-only candidate; final source terms review required.",
            )
        else:
            rights = image_fields(
                "IMG04",
                "V&A row does not expose image metadata in this capture.",
                confidence="high",
                rights_review_required=False,
                note="No image frame should be rendered for this capture row.",
            )
        rows.append(
            {
                **base_row(plan, source),
                **rights,
                "capture_status": "captured",
                "source_identifier": identifier,
                "source_record_url": f"https://collections.vam.ac.uk/item/{identifier}/",
                "source_title": text(item.get("_primaryTitle")),
                "source_creator": text((item.get("_primaryMaker") or {}).get("name") if isinstance(item.get("_primaryMaker"), dict) else ""),
                "source_date_text": text(item.get("_primaryDate")),
                "date_start": "",
                "date_end": "",
                "source_place_text": text(item.get("_primaryPlace")),
                "source_object_type": text(item.get("objectType")),
                "source_medium": "",
                "source_collection": "V&A Collections",
            }
        )
    return rows


def rows_from_loc(payload: dict[str, Any], plan: dict[str, str], source: dict[str, str]) -> list[dict[str, str]]:
    rows = []
    for item in payload.get("results", [])[: int(plan["limit"])]:
        links = item.get("links") if isinstance(item.get("links"), dict) else {}
        image = item.get("image") if isinstance(item.get("image"), dict) else {}
        image_url = text(image.get("thumb") or image.get("full")) if isinstance(image, dict) else ""
        if "notdigitized" in image_url or "not_digitized" in image_url:
            rights = image_fields(
                "IMG04",
                "LOC search row uses a not-digitized placeholder rather than an item image.",
                image_url="",
                viewer=text(links.get("item")),
                confidence="high",
                rights_review_required=False,
                note="This should render as a text/source row without an image frame.",
            )
        elif image_url:
            rights = image_fields(
                "IMG01",
                "LOC pictures search row exposes a thumbnail; item-level rights advisory was not captured in this pass.",
                image_url=image_url,
                viewer=text(links.get("item")),
                confidence="medium",
                rights_review_required=True,
                note="Thumbnail candidate only; item page rights advisory must be captured before publication.",
            )
        else:
            rights = image_fields(
                "IMG04",
                "LOC search row does not expose an image in this capture.",
                viewer=text(links.get("item")),
                confidence="high",
                rights_review_required=False,
                note="No image frame should be rendered for this capture row.",
            )
        rows.append(
            {
                **base_row(plan, source),
                **rights,
                "capture_status": "captured",
                "source_identifier": text(item.get("pk")),
                "source_record_url": text(links.get("item")),
                "source_title": text(item.get("title")),
                "source_creator": text(item.get("creator")),
                "source_date_text": text(item.get("created_published_date")),
                "date_start": "",
                "date_end": "",
                "source_place_text": "",
                "source_object_type": text(item.get("medium_brief")),
                "source_medium": text(item.get("medium")),
                "source_collection": text(item.get("collection")),
            }
        )
    return rows


def base_row(plan: dict[str, str], source: dict[str, str]) -> dict[str, str]:
    return {
        "direction_id": plan["direction_id"],
        "direction_name": plan["direction_name"],
        "source_id": source["source_id"],
        "source_name": plan["source_name"],
        "source_api_url": plan["url"],
        "access_date": ACCESS_DATE,
    }


ADAPTERS = {
    "aic": rows_from_aic,
    "cleveland": rows_from_cleveland,
    "vam": rows_from_vam,
    "loc": rows_from_loc,
}


def write_raw(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_records(rows: list[dict[str, str]]) -> None:
    with RECORDS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(rows: list[dict[str, str]], failures: list[dict[str, str]]) -> None:
    summary_rows = []
    for key, grouped_rows in group_rows(rows, ["direction_id", "direction_name", "source_id", "source_name"]).items():
        direction_id, direction_name, source_id, source_name = key
        image_counter = Counter(row["image_presence_code"] for row in grouped_rows)
        summary_rows.append(
            {
                "direction_id": direction_id,
                "direction_name": direction_name,
                "source_id": source_id,
                "source_name": source_name,
                "captured_count": str(len(grouped_rows)),
                "failure_count": str(sum(1 for failure in failures if failure["source_name"] == source_name)),
                "img00_count": str(image_counter.get("IMG00", 0)),
                "img01_count": str(image_counter.get("IMG01", 0)),
                "img02_count": str(image_counter.get("IMG02", 0)),
                "img03_count": str(image_counter.get("IMG03", 0)),
                "img04_count": str(image_counter.get("IMG04", 0)),
                "notes": "Capture-batch production candidate; not final source record until review.",
            }
        )
    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "direction_id",
            "direction_name",
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
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)


def group_rows(rows: list[dict[str, str]], keys: list[str]) -> dict[tuple[str, ...], list[dict[str, str]]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row)
    return grouped


def main() -> None:
    sources = read_source_registry()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []

    for plan in CAPTURE_PLAN:
        source = sources.get(plan["source_name"])
        if not source:
            raise SystemExit(f"source not found in registry: {plan['source_name']}")
        try:
            payload = fetch_json(plan["url"])
            raw_path = RAW_DIR / f"{plan['source_id'] if 'source_id' in plan else source['source_id']}_{plan['adapter']}_search.json"
            write_raw(raw_path, payload)
            plan_rows = ADAPTERS[plan["adapter"]](payload, plan, source)
            for row in plan_rows:
                row["raw_json_path"] = str(raw_path.relative_to(ROOT))
            rows.extend(plan_rows)
        except Exception as exc:  # noqa: BLE001 - this is a capture log, not app runtime.
            failures.append(
                {
                    "source_name": plan["source_name"],
                    "source_api_url": plan["url"],
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        time.sleep(0.4)

    rows = rows[:50]
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"ECAP{index:03d}"
        for field in FIELDNAMES:
            row.setdefault(field, "")

    write_records(rows)
    write_summary(rows, failures)

    print(f"{RECORDS_CSV.relative_to(ROOT)}: {len(rows)} captured rows")
    print(f"{SUMMARY_CSV.relative_to(ROOT)}: summary written")
    if failures:
        print("Failures:")
        for failure in failures:
            print(f"- {failure['source_name']}: {failure['error']}")
    if len(rows) != 50:
        raise SystemExit(f"expected 50 captured rows, got {len(rows)}")


if __name__ == "__main__":
    main()
