#!/usr/bin/env python3
"""Run a chunked pre-freeze public-surface rebuild candidate.

This is a sandbox rebuild validator. It processes capture rows in chunks
(default 2,000 rows), applies the pre-freeze P0 exclusion table, runs the same
surface-building/enrichment/normalization path as the monolithic rebuild for
each chunk, and writes metrics/reports only. It intentionally does not overwrite
`generated/public_surfaces_v1.json` or frontend payloads.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

import rebuild_public_surfaces_from_records as rebuild
import run_midcentury_capture_1930_1970 as mc
from normalize_public_surfaces import normalize_payload


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

OUT_DIR = DATA / "prefreeze_chunked_rebuild_v1"
CHUNKS_CSV = OUT_DIR / "chunk_metrics.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
REPORT = DOCS / "PREFREEZE_CHUNKED_REBUILD_v1.md"

CHUNK_FIELDS = [
    "chunk_id",
    "scope",
    "row_start",
    "row_end",
    "input_rows",
    "surface_count",
    "distinct_source_names",
    "image_state_counts",
    "source_visible_surfaces",
    "verified_open_surfaces",
    "folder_count",
    "dossier_count",
    "first_surface_id",
    "last_surface_id",
    "status",
    "error",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def clean(value: object) -> str:
    return " ".join(str(value or "").split()).strip()


def image_state(surface: dict[str, Any]) -> str:
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    return clean(image.get("state")) or "IMG00"


def is_source_visible(surface: dict[str, Any]) -> bool:
    return image_state(surface) in {"IMG01", "IMG02", "IMG03"}


def is_verified_open(surface: dict[str, Any]) -> bool:
    review = surface.get("reviewGates") if isinstance(surface.get("reviewGates"), dict) else {}
    return image_state(surface) == "IMG03" and review.get("rightsReviewed") is True


def all_capture_record_files() -> list[Path]:
    return sorted(path for path in DATA.glob("capture_batch_*_records.csv") if "cell_assignments" not in path.name)


def selected_record_files(scope: str) -> list[Path]:
    if scope == "manifest":
        return rebuild.rebuild_record_files()
    if scope == "all-capture":
        return all_capture_record_files()
    if scope == "not-included":
        included = {path.resolve() for path in rebuild.rebuild_record_files()}
        return [path for path in all_capture_record_files() if path.resolve() not in included]
    raise ValueError(f"unknown scope: {scope}")


def collect_rows(scope: str) -> tuple[list[dict[str, str]], int, int, list[Path]]:
    exclusions = rebuild.prefreeze_exclusion_lookup()
    files = selected_record_files(scope)
    rows: list[dict[str, str]] = []
    raw_rows = 0
    excluded_rows = 0
    for path in files:
        input_rows = rebuild.read_rows(path)
        raw_rows += len(input_rows)
        excluded_ids = exclusions.get(path.name, set())
        if excluded_ids:
            before = len(input_rows)
            input_rows = [row for row in input_rows if row.get("capture_id", "") not in excluded_ids]
            excluded_rows += before - len(input_rows)
        rows.extend(input_rows)
    rows = rebuild.dedupe_rows(
        [
            rebuild.normalize_public_date_fields(rebuild.fill_enrichment_defaults(row))
            for row in rows
        ]
    )
    rows.sort(key=lambda row: (rebuild.row_sort_year(row), row.get("source_title", "")))
    return rows, raw_rows, excluded_rows, files


def build_chunk_payload(rows: list[dict[str, str]]) -> dict[str, Any]:
    payload = mc.build_public_payload(rows)
    payload = rebuild.enhance_payload(payload, rows)
    payload = normalize_payload(payload)
    payload = rebuild.normalize_public_surface_visible_text(payload)
    payload = rebuild.normalize_public_folder_metadata(payload)
    payload = rebuild.attach_structural_collections(payload)
    payload = rebuild.build_research_dossiers(payload)
    return payload


def chunked(values: list[dict[str, str]], chunk_size: int) -> list[list[dict[str, str]]]:
    return [values[index : index + chunk_size] for index in range(0, len(values), chunk_size)]


def counter_string(counter: Counter[str]) -> str:
    return ";".join(f"{key}:{counter[key]}" for key in sorted(counter))


def run_chunks(rows: list[dict[str, str]], *, chunk_size: int, scope: str) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for index, part in enumerate(chunked(rows, chunk_size), start=1):
        row_start = (index - 1) * chunk_size + 1
        row_end = row_start + len(part) - 1
        chunk_id = f"chunk_{index:04d}"
        try:
            payload = build_chunk_payload(part)
            surfaces = payload.get("surfaces", [])
            states = Counter(image_state(surface) for surface in surfaces)
            sources = {clean(surface.get("sourceName")) for surface in surfaces if clean(surface.get("sourceName"))}
            out.append(
                {
                    "chunk_id": chunk_id,
                    "scope": scope,
                    "row_start": row_start,
                    "row_end": row_end,
                    "input_rows": len(part),
                    "surface_count": len(surfaces),
                    "distinct_source_names": len(sources),
                    "image_state_counts": counter_string(states),
                    "source_visible_surfaces": sum(1 for surface in surfaces if is_source_visible(surface)),
                    "verified_open_surfaces": sum(1 for surface in surfaces if is_verified_open(surface)),
                    "folder_count": len(payload.get("folders", [])),
                    "dossier_count": len(payload.get("researchDossiers", [])),
                    "first_surface_id": clean(surfaces[0].get("surfaceId")) if surfaces else "",
                    "last_surface_id": clean(surfaces[-1].get("surfaceId")) if surfaces else "",
                    "status": "ok",
                    "error": "",
                }
            )
            print(f"{chunk_id}: rows={len(part)} surfaces={len(surfaces)} status=ok")
        except Exception as exc:  # pragma: no cover - operational audit path.
            out.append(
                {
                    "chunk_id": chunk_id,
                    "scope": scope,
                    "row_start": row_start,
                    "row_end": row_end,
                    "input_rows": len(part),
                    "surface_count": 0,
                    "distinct_source_names": 0,
                    "image_state_counts": "",
                    "source_visible_surfaces": 0,
                    "verified_open_surfaces": 0,
                    "folder_count": 0,
                    "dossier_count": 0,
                    "first_surface_id": "",
                    "last_surface_id": "",
                    "status": "error",
                    "error": clean(exc),
                }
            )
            print(f"{chunk_id}: rows={len(part)} status=error error={exc}")
    return out


def write_report(
    *,
    scope: str,
    chunk_size: int,
    raw_rows: int,
    deduped_rows: int,
    excluded_rows: int,
    record_files: list[Path],
    chunk_rows: list[dict[str, object]],
) -> None:
    ok_count = sum(1 for row in chunk_rows if row["status"] == "ok")
    error_count = sum(1 for row in chunk_rows if row["status"] != "ok")
    total_surfaces = sum(int(row["surface_count"]) for row in chunk_rows)
    total_sources = sum(int(row["distinct_source_names"]) for row in chunk_rows)
    total_visible = sum(int(row["source_visible_surfaces"]) for row in chunk_rows)
    total_open = sum(int(row["verified_open_surfaces"]) for row in chunk_rows)
    summary_rows = [
        {"metric": "scope", "value": scope, "notes": "Record-file selection mode."},
        {"metric": "chunk_size", "value": str(chunk_size), "notes": "Maximum rows per chunk."},
        {"metric": "record_files", "value": str(len(record_files)), "notes": "Capture CSV inputs scanned."},
        {"metric": "raw_input_rows", "value": str(raw_rows), "notes": "Rows before P0 exclusion and dedupe."},
        {"metric": "prefreeze_excluded_rows", "value": str(excluded_rows), "notes": "Rows skipped by pre-freeze exclusion table."},
        {"metric": "deduped_candidate_rows", "value": str(deduped_rows), "notes": "Rows after exclusion and dedupe."},
        {"metric": "chunks_total", "value": str(len(chunk_rows)), "notes": "Chunks executed."},
        {"metric": "chunks_ok", "value": str(ok_count), "notes": "Chunks built successfully."},
        {"metric": "chunks_error", "value": str(error_count), "notes": "Chunks with exceptions."},
        {"metric": "chunk_surface_sum", "value": str(total_surfaces), "notes": "Sum of surfaces built per chunk; not a finalized public payload count."},
        {"metric": "chunk_distinct_source_sum", "value": str(total_sources), "notes": "Per-chunk source counts summed; cross-chunk duplicates are not collapsed here."},
        {"metric": "chunk_source_visible_surface_sum", "value": str(total_visible), "notes": "Per-chunk source-visible surface sum."},
        {"metric": "chunk_verified_open_surface_sum", "value": str(total_open), "notes": "Per-chunk verified-open surface sum."},
    ]
    write_csv(SUMMARY_CSV, summary_rows, SUMMARY_FIELDS)
    lines = [
        "# Pre-freeze Chunked Rebuild v1",
        "",
        "Scope: sandbox chunked rebuild validator. It processes capture rows in chunks and writes metrics only; it does not overwrite generated public payloads or frontend files.",
        "",
        "## Summary",
        "",
    ]
    for row in summary_rows:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Chunk Results", ""])
    for row in chunk_rows:
        lines.append(
            f"- {row['chunk_id']}: rows={row['input_rows']}, surfaces={row['surface_count']}, "
            f"sources={row['distinct_source_names']}, states={row['image_state_counts']}, status={row['status']}"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This pass validates that candidate rows can be rebuilt in batches of 2,000 or fewer.",
            "- The summed chunk source count is diagnostic only; a final official payload must still perform global grouping, folder aggregation, and object-level release audits.",
            "- P0 rows remain available in capture CSVs but are skipped from this candidate rebuild through the exclusion table.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a chunked pre-freeze public-surface rebuild candidate.")
    parser.add_argument("--chunk-size", type=int, default=2000)
    parser.add_argument("--scope", choices=["manifest", "all-capture", "not-included"], default="all-capture")
    args = parser.parse_args()
    if args.chunk_size <= 0:
        raise SystemExit("--chunk-size must be positive")

    rows, raw_rows, excluded_rows, files = collect_rows(args.scope)
    chunk_rows = run_chunks(rows, chunk_size=args.chunk_size, scope=args.scope)
    write_csv(CHUNKS_CSV, chunk_rows, CHUNK_FIELDS)
    write_report(
        scope=args.scope,
        chunk_size=args.chunk_size,
        raw_rows=raw_rows,
        deduped_rows=len(rows),
        excluded_rows=excluded_rows,
        record_files=files,
        chunk_rows=chunk_rows,
    )
    print(f"scope={args.scope}")
    print(f"raw_input_rows={raw_rows}")
    print(f"prefreeze_excluded_rows={excluded_rows}")
    print(f"deduped_candidate_rows={len(rows)}")
    print(f"chunks={len(chunk_rows)}")
    print(f"errors={sum(1 for row in chunk_rows if row['status'] != 'ok')}")
    print(f"wrote {CHUNKS_CSV.relative_to(ROOT)}")
    print(f"wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
