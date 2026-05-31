from __future__ import annotations

import csv
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

import run_midcentury_capture_1930_1970 as mc
import run_midcentury_expansion_capture_1931_1970 as mx


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_loc_deep_image_ready_1931_1970_raw"
RECORDS_CSV = DATA / "capture_batch_loc_deep_image_ready_1931_1970_records.csv"
SUMMARY_CSV = DATA / "capture_batch_loc_deep_image_ready_1931_1970_source_summary.csv"

ACCESS_DATE = "2026-05-31"
SOURCE_NAME = "Library of Congress loc.gov API"
IMAGE_READY_STATES = {"IMG01", "IMG02", "IMG03"}
FIELDNAMES = mx.FIELDNAMES

CAPTURE_PLAN = [
    {
        "direction_id": "LOCDEEP01",
        "direction_name": "loc_wpa_and_public_information_posters",
        "source_name": SOURCE_NAME,
        "adapter": "loc",
        "queries": [
            "WPA art project poster",
            "Work Projects Administration poster",
            "Federal Art Project poster",
            "public information poster",
            "public health poster tuberculosis",
            "food conservation poster",
        ],
        "limit": 60,
    },
    {
        "direction_id": "LOCDEEP02",
        "direction_name": "loc_travel_transport_and_exhibition_posters",
        "source_name": SOURCE_NAME,
        "adapter": "loc",
        "queries": [
            "travel poster national parks",
            "railroad poster",
            "airline poster",
            "exhibition poster",
            "theater poster lithograph",
            "music poster lithograph",
        ],
        "limit": 60,
    },
    {
        "direction_id": "LOCDEEP03",
        "direction_name": "loc_social_movement_and_campaign_prints",
        "source_name": SOURCE_NAME,
        "adapter": "loc",
        "queries": [
            "civil rights poster",
            "labor union poster",
            "peace poster",
            "election poster",
            "campaign poster",
            "war information poster",
        ],
        "limit": 60,
    },
]


def existing_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in DATA.glob("capture_batch_*_records.csv"):
        if path == RECORDS_CSV:
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                keys.add((row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", "")))
    return keys


def save_raw(payloads: list[tuple[str, Any]]) -> dict[str, str]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for name, payload in payloads:
        path = RAW_DIR / name
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        paths[name] = str(path.relative_to(ROOT))
    return paths


def enrich(row: dict[str, str]) -> dict[str, str]:
    code = row.get("image_presence_code") or "IMG00"
    row["access_date"] = ACCESS_DATE
    row["image_expectation"] = "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["source_description_raw"] = row.get("source_description", "")
    row["ocr_or_excerpt"] = row.get("source_description") or row.get("source_notes") or row.get("source_subjects", "")
    row["historical_context_note"] = (
        "Deep LoC expansion pass for 1931-1970 posters and public graphic communication. "
        "This pass is used to improve image-bearing coverage while keeping Library of "
        "Congress item pages as the canonical source."
    )
    row["classification_rationale"] = (
        "Selected from LoC Pictures search by targeted poster/public-information queries, "
        "date scope, graphic relevance, and exclusion of source records already present in prior batches."
    )
    row["uncertainty_note"] = "LoC thumbnail/image rights remain item-level; source return must stay visible."
    row["citation_basis"] = (
        f"{row.get('source_name', '')}. {row.get('source_title', '')}. "
        f"{row.get('source_record_url') or row.get('source_api_url')}. Accessed {ACCESS_DATE}."
    )
    row["editorial_summary"] = mx.clean(
        f"{row.get('source_title') or 'This record'} is indexed from Library of Congress. "
        f"{row.get('source_description') or row.get('source_notes') or row.get('source_subjects') or row.get('source_object_type') or ''}",
        max_chars=680,
    )
    if code not in IMAGE_READY_STATES:
        row["uncertainty_note"] = "Excluded from image-ready output unless manually reviewed."
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    sources = mc.read_source_registry()
    source = sources[SOURCE_NAME]
    seen = existing_keys()
    rows: list[dict[str, str]] = []
    raw: list[tuple[str, Any]] = []
    failures: list[dict[str, str]] = []

    for plan in CAPTURE_PLAN:
        try:
            plan_rows, plan_raw = mc.ADAPTERS["loc"](plan, source)
            raw.extend(plan_raw)
        except Exception as exc:  # noqa: BLE001
            failures.append({"direction_id": plan["direction_id"], "source_name": SOURCE_NAME, "error": f"{type(exc).__name__}: {exc}"})
            continue
        for row in plan_rows:
            if row.get("image_presence_code") not in IMAGE_READY_STATES:
                continue
            key = (row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", ""))
            if key in seen:
                continue
            seen.add(key)
            rows.append(enrich(row))
        time.sleep(0.35)

    rows.sort(key=lambda r: (int(r["date_start"]) if r.get("date_start") else 9999, r.get("source_title", "")))
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"LOCDEEP1970R{index:03d}"
        for field in FIELDNAMES:
            row.setdefault(field, "")

    raw_paths = save_raw(raw)
    default_raw_path = next(iter(raw_paths.values()), "")
    for row in rows:
        row["raw_json_path"] = row.get("raw_json_path") or default_raw_path

    with RECORDS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    counter = Counter(row["image_presence_code"] for row in rows)
    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        fields = ["direction_id", "source_id", "source_name", "captured_count", "failure_count", "img00_count", "img01_count", "img02_count", "img03_count", "img04_count", "notes"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "direction_id": "LOCDEEP",
                "source_id": source.get("source_id", ""),
                "source_name": SOURCE_NAME,
                "captured_count": len(rows),
                "failure_count": len(failures),
                "img00_count": counter.get("IMG00", 0),
                "img01_count": counter.get("IMG01", 0),
                "img02_count": counter.get("IMG02", 0),
                "img03_count": counter.get("IMG03", 0),
                "img04_count": counter.get("IMG04", 0),
                "notes": "Deep image-ready LoC pass; duplicates against prior batches are skipped.",
            }
        )

    print(f"captured={len(rows)}")
    print(f"image_states={dict(counter)}")
    if failures:
        print(f"failures={len(failures)}")
        for failure in failures[:5]:
            print(f"- {failure['direction_id']}: {failure['error']}")


if __name__ == "__main__":
    main()
