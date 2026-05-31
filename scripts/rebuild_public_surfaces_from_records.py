from __future__ import annotations

import csv
import json
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
    DATA / "capture_batch_wikimedia_commons_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_princeton_figgy_image_ready_1830_1970_records.csv",
    DATA / "capture_batch_gsu_contentdm_image_ready_1830_1970_records.csv",
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
    row.setdefault("image_expectation", "not_expected" if code == "IMG04" else "expected")
    row.setdefault("parser_status", "ok" if row.get("source_record_url") else "legacy")
    row.setdefault("display_mode", row.get("image_frame_behavior", ""))
    row.setdefault("ocr_or_excerpt", row.get("source_description", ""))
    row.setdefault("source_description_raw", row.get("source_description", ""))
    row.setdefault(
        "historical_context_note",
        "Cumulative 1931-1970 archive-box record retained for frontend and information-system verification.",
    )
    row.setdefault(
        "classification_rationale",
        "Provisional folder placement is derived from title, date, medium, subject, source, and provider context.",
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


def dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, str]] = []
    for row in rows:
        key = (
            row.get("source_name", ""),
            row.get("source_identifier") or row.get("source_record_url") or row.get("source_title", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


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
        surface["historicalContextNote"] = row.get("historical_context_note")
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


def main() -> None:
    rows: list[dict[str, str]] = []
    for path in RECORD_FILES:
        rows.extend(read_rows(path))
    rows = dedupe_rows([fill_enrichment_defaults(row) for row in rows])
    rows.sort(key=lambda r: (int(r["date_start"]) if r.get("date_start") else 9999, r.get("source_title", "")))

    payload = mc.build_public_payload(rows)
    payload = enhance_payload(payload, rows)
    payload = normalize_payload(payload)

    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    for path in PAYLOAD_PATHS:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    image_counter = Counter(surface.get("image", {}).get("state", "IMG00") for surface in payload.get("surfaces", []))
    ready = sum(image_counter[state] for state in ("IMG01", "IMG02", "IMG03"))
    total = len(payload.get("surfaces", []))
    coverage = round(ready / total * 100) if total else 0
    print(f"rows={len(rows)}")
    print(f"surfaces={total}")
    print(f"folders={len(payload.get('folders', []))}")
    print(f"image_states={dict(sorted(image_counter.items()))}")
    print(f"image_ready={ready}/{total} ({coverage}%)")


if __name__ == "__main__":
    main()
