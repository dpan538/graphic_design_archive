from __future__ import annotations

import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import run_midcentury_capture_1930_1970 as mc
import run_midcentury_expansion_capture_1931_1970 as mx


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_image_ready_1931_1970_raw"
RECORDS_CSV = DATA / "capture_batch_image_ready_1931_1970_records.csv"
SUMMARY_CSV = DATA / "capture_batch_image_ready_1931_1970_source_summary.csv"

ACCESS_DATE = "2026-05-31"
CAPTURE_BATCH_ID = "CB-IMAGE-READY-1931-1970"
IMAGE_READY_STATES = {"IMG01", "IMG02", "IMG03"}


CAPTURE_PLAN = [
    {
        "direction_id": "IR01",
        "direction_name": "loc_poster_thumbnail_expansion",
        "source_name": "Library of Congress loc.gov API",
        "adapter": "loc",
        "queries": [
            "WPA poster",
            "war poster",
            "world war poster",
            "public health poster",
            "travel poster",
            "civil rights poster",
            "advertising poster",
            "music poster",
            "exhibition poster",
            "poster",
        ],
        "limit": 90,
    },
    {
        "direction_id": "IR02",
        "direction_name": "vam_iiif_poster_design_expansion",
        "source_name": "V&A Collections API",
        "adapter": "vam",
        "queries": [
            "poster",
            "London Transport poster",
            "travel poster",
            "graphic design",
            "typography",
            "exhibition poster",
            "advertising poster",
            "photomontage",
            "political poster",
        ],
        "limit": 90,
    },
    {
        "direction_id": "IR03",
        "direction_name": "wellcome_iiif_public_information_expansion",
        "source_name": "Wellcome Collection Catalogue API",
        "adapter": "wellcome",
        "queries": [
            "public health poster",
            "health education poster",
            "safety poster",
            "anti smoking poster",
            "tuberculosis poster",
            "family planning poster",
            "poster campaign",
            "advertising poster",
        ],
        "limit": 80,
    },
    {
        "direction_id": "IR04",
        "direction_name": "cleveland_cc0_visual_object_expansion",
        "source_name": "Cleveland Museum Open Access API",
        "adapter": "cleveland",
        "queries": ["poster", "advertisement", "graphic design", "typography", "photomontage", "lithograph"],
        "limit": 40,
    },
    {
        "direction_id": "IR05",
        "direction_name": "met_open_access_visual_object_expansion",
        "source_name": "The Met Open Access",
        "adapter": "met",
        "queries": ["poster", "advertising", "graphic design", "typography", "lithograph", "book cover"],
        "limit": 40,
    },
]


FIELDNAMES = mx.FIELDNAMES


def existing_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for path in [
        DATA / "capture_batch_midcentury_1930_1970_records.csv",
        DATA / "capture_batch_midcentury_expansion_1931_1970_records.csv",
        RECORDS_CSV,
    ]:
        if not path.exists():
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


def enrich_for_public_payload(row: dict[str, str]) -> dict[str, str]:
    row["access_date"] = ACCESS_DATE
    code = row.get("image_presence_code") or "IMG00"
    row["image_expectation"] = "expected"
    row["parser_status"] = "ok"
    row["display_mode"] = row.get("image_frame_behavior", "")
    row["source_description_raw"] = row.get("source_description", "")
    row["ocr_or_excerpt"] = row.get("source_description") or row.get("source_notes") or row.get("source_subjects", "")
    row["historical_context_note"] = (
        "Captured in the image-ready expansion pass for 1931-1970. This record is kept because the source exposes "
        "a thumbnail, source-hosted IIIF/viewer image, or open image candidate."
    )
    row["classification_rationale"] = (
        "Folder placement is provisional and generated from source title, date, object type, medium, subject, and provider context."
    )
    row.setdefault("uncertainty_note", "")
    row["citation_basis"] = (
        f"{row.get('source_name', '')}. {row.get('source_title', '')}. "
        f"{row.get('source_record_url') or row.get('source_api_url')}. Accessed {ACCESS_DATE}."
    )
    row["editorial_summary"] = mx.clean(
        f"{row.get('source_title') or 'This record'} is indexed from {row.get('source_name') or 'the source'}. "
        f"{row.get('source_description') or row.get('source_notes') or row.get('source_subjects') or row.get('source_object_type') or ''}",
        max_chars=560,
    )
    if code not in IMAGE_READY_STATES:
        row["uncertainty_note"] = "Excluded from image-ready public expansion unless manually reviewed."
    for field in FIELDNAMES:
        row.setdefault(field, "")
    return row


def source_summary(rows: list[dict[str, str]], failures: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["direction_id"], row["source_id"], row["source_name"])].append(row)
    summary_rows: list[dict[str, str]] = []
    for (direction_id, source_id, source_name), items in sorted(grouped.items()):
        counter = Counter(row["image_presence_code"] for row in items)
        summary_rows.append(
            {
                "direction_id": direction_id,
                "source_id": source_id,
                "source_name": source_name,
                "captured_count": str(len(items)),
                "failure_count": str(sum(1 for failure in failures if failure["source_name"] == source_name)),
                "img00_count": str(counter.get("IMG00", 0)),
                "img01_count": str(counter.get("IMG01", 0)),
                "img02_count": str(counter.get("IMG02", 0)),
                "img03_count": str(counter.get("IMG03", 0)),
                "img04_count": str(counter.get("IMG04", 0)),
                "notes": "Only IMG01/IMG02/IMG03 records are written to this image-ready expansion batch.",
            }
        )
    return summary_rows


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    sources = mc.read_source_registry()
    prior_keys = existing_keys()
    rows: list[dict[str, str]] = []
    raw: list[tuple[str, Any]] = []
    failures: list[dict[str, str]] = []
    seen = set(prior_keys)

    for plan in CAPTURE_PLAN:
        try:
            if plan["adapter"] == "wellcome":
                plan_rows, plan_raw, plan_failures = mx.rows_from_wellcome(plan)
                failures.extend(plan_failures)
            else:
                source = sources[plan["source_name"]]
                plan_rows, plan_raw = mc.ADAPTERS[plan["adapter"]](plan, source)
            raw.extend(plan_raw)
        except Exception as exc:  # noqa: BLE001 - capture log must keep source failures.
            failures.append({"source_name": plan["source_name"], "query": "*", "error": f"{type(exc).__name__}: {exc}"})
            continue

        for row in plan_rows:
            if row.get("image_presence_code") not in IMAGE_READY_STATES:
                continue
            if not row.get("image_url_detected") and row.get("image_presence_code") != "IMG02":
                continue
            key = (row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", ""))
            if key in seen:
                continue
            seen.add(key)
            rows.append(enrich_for_public_payload(row))
        time.sleep(0.4)

    rows.sort(key=lambda r: (int(r["date_start"]) if r.get("date_start") else 9999, r.get("source_title", "")))
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"IR1970R{index:03d}"
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
        writer.writerows(source_summary(rows, failures))

    counter = Counter(row["image_presence_code"] for row in rows)
    print(f"{RECORDS_CSV.relative_to(ROOT)}: {len(rows)} image-ready rows")
    print(f"{SUMMARY_CSV.relative_to(ROOT)}: summary written")
    print("image distribution:", dict(sorted(counter.items())))
    if failures:
        print("failures:", len(failures))
        for failure in failures[:8]:
            print(f"- {failure['source_name']}: {failure.get('error')}")


if __name__ == "__main__":
    main()
