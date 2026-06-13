from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
GENERATED = ROOT / "generated"
PAYLOAD = GENERATED / "public_surfaces_v1.json"

IMAGE_READY = {"IMG01", "IMG02", "IMG03"}
OPEN_IMAGE = {"IMG03"}
PUBLICATION_WEIGHTS = {
    # IMG03 is verified open-image evidence and is the publication-grade target.
    # Repeated views/photos are still collapsed at object level by object_key().
    "IMG03": 1.0,
    "IMG02": 0.55,
    "IMG01": 0.3,
    "IMG00": 0.0,
    "IMG04": 0.0,
}

REGION_ALIASES = {
    "Latin America and the Caribbean": "Latin America",
    "Latin America / Caribbean": "Latin America",
    "Caribbean": "Latin America",
    "Eastern Europe / Caucasus": "Eastern Europe",
    "Caucasus": "Eastern Europe",
    "Global / web / transnational": "Global",
    "Global / release gate expansion": "Global",
    "Global South / release gate expansion": "Global",
    "Middle East and North Africa": "MENA",
    "North Africa": "MENA",
    "Middle East": "MENA",
    "Western/Central Europe": "Europe",
    "Western Europe": "Europe",
    "Central Europe": "Europe",
    "Oceania and Pacific": "Oceania and Pacific",
}


def clean(value: object) -> str:
    return str(value or "").strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_payload(path: Path = PAYLOAD) -> dict[str, Any]:
    if not path.exists():
        return {"surfaces": [], "researchDossiers": []}
    return json.loads(path.read_text(encoding="utf-8"))


def pct(numerator: float, denominator: float) -> str:
    if denominator <= 0:
        return "0.00"
    return f"{(numerator / denominator) * 100:.2f}"


def normalize_url(value: str) -> str:
    value = clean(value)
    if not value:
        return ""
    parsed = urlsplit(value)
    path = parsed.path.rstrip("/") or parsed.path
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", ""))


def surface_image_state(surface: dict[str, Any]) -> str:
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    return clean(image.get("state")) or "IMG00"


def surface_is_source_visible(surface: dict[str, Any]) -> bool:
    return surface_image_state(surface) in IMAGE_READY


def surface_is_verified_open(surface: dict[str, Any]) -> bool:
    review = surface.get("reviewGates") if isinstance(surface.get("reviewGates"), dict) else {}
    return surface_image_state(surface) in OPEN_IMAGE and review.get("rightsReviewed") is True


def surface_weight(surface: dict[str, Any]) -> float:
    return PUBLICATION_WEIGHTS.get(surface_image_state(surface), 0.0)


def object_key(surface: dict[str, Any]) -> str:
    source_url = normalize_url(clean(surface.get("sourceUrl")))
    if source_url:
        return f"url:{source_url}"
    record_id = clean(surface.get("sourceRecordId"))
    if record_id:
        return f"record:{record_id}"
    parts = [
        clean(surface.get("sourceName")),
        clean(surface.get("title")).lower(),
        clean(surface.get("dateText")),
    ]
    return "fallback:" + "|".join(parts)


def object_groups(surfaces: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for surface in surfaces:
        groups.setdefault(object_key(surface), []).append(surface)
    return groups


def period_band_from_year(year: int | None) -> str:
    if year is None:
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


def surface_year(surface: dict[str, Any]) -> int | None:
    for field in ("dateStart", "dateEnd"):
        try:
            return int(surface.get(field))
        except (TypeError, ValueError):
            continue
    return None


def surface_period_band(surface: dict[str, Any]) -> str:
    return period_band_from_year(surface_year(surface))


def normalize_region(value: str) -> str:
    region = clean(value).split("/")[0].strip()
    if not region:
        return "Unresolved region"
    return REGION_ALIASES.get(region, region)


def surface_region(surface: dict[str, Any]) -> str:
    folders = surface.get("folders") if isinstance(surface.get("folders"), list) else []
    for folder in folders:
        if isinstance(folder, dict) and folder.get("type") == "region":
            return normalize_region(clean(folder.get("title")))
    return "Unresolved region"


def record_source_key(row: dict[str, str]) -> str:
    return clean(row.get("source_name")) or clean(row.get("source_id")) or clean(row.get("source_record_url"))


def record_image_state(row: dict[str, str]) -> str:
    return clean(row.get("image_presence_code")) or "IMG00"


def capture_record_files() -> list[Path]:
    return sorted(DATA.glob("capture_batch_*_records.csv"))


def state_counter_from_surfaces(surfaces: list[dict[str, Any]]) -> Counter[str]:
    return Counter(surface_image_state(surface) for surface in surfaces)
