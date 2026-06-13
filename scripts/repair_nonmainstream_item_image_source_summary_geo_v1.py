#!/usr/bin/env python3
"""
Repair non-mainstream item/image source-summary geography.

The capture records already preserve country-level geography in
source_place_text, for example "Latin America / Caribbean / Argentina". The
source-summary CSV was generated with the middle segment as country_or_region,
which collapses many rows into broad buckets such as Caribbean or Caucasus.

Default mode is a dry run that writes the repair plan and report. Use --apply
to mutate the source-summary CSV. This script does not fetch network data,
download images, mutate capture records, or change any image rights state.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs/capture"

RECORDS_CSV = DATA / "capture_batch_nonmainstream_item_image_2026_records.csv"
SUMMARY_CSV = DATA / "capture_batch_nonmainstream_item_image_2026_source_summary.csv"

PLAN_CSV = DATA / "nonmainstream_item_image_source_summary_geo_repair_plan_v1.csv"
SUMMARY_OUT_CSV = DATA / "nonmainstream_item_image_source_summary_geo_repair_summary_v1.csv"
REPORT_MD = DOCS / "NONMAINSTREAM_ITEM_IMAGE_SOURCE_SUMMARY_GEO_REPAIR_v1.md"
BACKUP_DIR = DATA / "backups/nonmainstream_item_image_source_summary_geo_repair_2026_06_13"


def clean(value: Any) -> str:
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split()).strip()


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def detect_lineterminator(path: Path) -> str:
    sample = path.read_bytes()[:8192]
    return "\r\n" if b"\r\n" in sample else "\n"


def write_csv(
    path: Path,
    rows: Iterable[dict[str, Any]],
    fieldnames: list[str],
    *,
    lineterminator: str = "\n",
) -> None:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator=lineterminator)
        writer.writeheader()
        writer.writerows(materialized)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def split_source_place(source_place_text: str) -> tuple[str, str]:
    parts = [part.strip() for part in clean(source_place_text).split(" / ") if part.strip()]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[-1]


SourceKey = tuple[str, str]


def build_record_geo(records: list[dict[str, str]]) -> tuple[dict[SourceKey, tuple[str, str, str]], set[SourceKey], int]:
    by_source: dict[SourceKey, set[tuple[str, str, str]]] = defaultdict(set)
    source_ids: defaultdict[str, set[str]] = defaultdict(set)
    for record in records:
        source_id = clean(record.get("source_id"))
        source_name = clean(record.get("source_name"))
        if not source_id or not source_name:
            continue
        source_ids[source_id].add(source_name)
        source_place = clean(record.get("source_place_text"))
        macro, country = split_source_place(source_place)
        by_source[(source_id, source_name)].add((macro, country, source_place))

    duplicate_source_id_count = sum(1 for names in source_ids.values() if len(names) > 1)
    record_geo: dict[SourceKey, tuple[str, str, str]] = {}
    conflicts: set[SourceKey] = set()
    for key, values in by_source.items():
        macro_country = {(macro, country) for macro, country, _ in values}
        if len(macro_country) > 1:
            conflicts.add(key)
            continue
        macro, country, source_place = sorted(values)[0]
        record_geo[key] = (macro, country, source_place)
    return record_geo, conflicts, duplicate_source_id_count


def build_plan(
    records: list[dict[str, str]],
    summary_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    record_geo, conflicts, _duplicate_source_id_count = build_record_geo(records)
    plan_rows: list[dict[str, str]] = []

    for row in summary_rows:
        source_id = clean(row.get("source_id"))
        source_name = clean(row.get("source_name"))
        key = (source_id, source_name)
        old_macro = clean(row.get("macro_region"))
        old_country = clean(row.get("country_or_region"))
        if key in conflicts:
            new_macro = ""
            new_country = ""
            source_place = ""
            action = "blocked_conflicting_record_geo"
            note = "multiple capture records for this source have conflicting geography"
        elif key not in record_geo:
            new_macro = ""
            new_country = ""
            source_place = ""
            action = "blocked_no_capture_record"
            note = "source_id/source_name pair not found in capture records"
        else:
            new_macro, new_country, source_place = record_geo[key]
            if not new_macro or not new_country:
                action = "blocked_missing_country_geo"
                note = "capture record source_place_text does not contain country-level geography"
            elif old_macro == new_macro and old_country == new_country:
                action = "unchanged"
                note = "summary geography already matches capture record source_place_text"
            else:
                action = "repair_ready"
                note = "summary geography should use first and last source_place_text segments"

        plan_rows.append(
            {
                "source_id": source_id,
                "source_name": source_name,
                "source_place_text": source_place,
                "old_macro_region": old_macro,
                "old_country_or_region": old_country,
                "new_macro_region": new_macro,
                "new_country_or_region": new_country,
                "action": action,
                "note": note,
            }
        )
    return plan_rows


def count_duplicate_source_ids(records: list[dict[str, str]]) -> int:
    source_ids: defaultdict[str, set[str]] = defaultdict(set)
    for record in records:
        source_id = clean(record.get("source_id"))
        source_name = clean(record.get("source_name"))
        if source_id and source_name:
            source_ids[source_id].add(source_name)
    return sum(1 for names in source_ids.values() if len(names) > 1)


def apply_plan(summary_rows: list[dict[str, str]], plan_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    plan_by_source = {
        (row["source_id"], row["source_name"]): row
        for row in plan_rows
    }
    repaired: list[dict[str, str]] = []
    for row in summary_rows:
        next_row = dict(row)
        plan = plan_by_source.get(
            (clean(row.get("source_id")), clean(row.get("source_name"))),
            {},
        )
        if plan.get("action") == "repair_ready":
            next_row["macro_region"] = plan["new_macro_region"]
            next_row["country_or_region"] = plan["new_country_or_region"]
        repaired.append(next_row)
    return repaired


def write_summary_metrics(
    plan_rows: list[dict[str, str]],
    applied: bool,
    before_hash: str,
    after_hash: str,
    duplicate_source_id_count: int,
) -> None:
    action_counts = Counter(row["action"] for row in plan_rows)
    postcheck_clean = (not applied) and action_counts.get("unchanged", 0) == len(plan_rows)
    run_mode = "apply" if applied else ("dry_run_postcheck" if postcheck_clean else "dry_run_plan")
    old_countries = Counter(row["old_country_or_region"] for row in plan_rows if row["action"] == "repair_ready")
    new_countries = Counter(row["new_country_or_region"] for row in plan_rows if row["action"] == "repair_ready")
    metric_rows: list[dict[str, Any]] = [
        {"metric_group": "input", "metric": "source_summary_sha256_before", "value": before_hash},
        {"metric_group": "input", "metric": "source_summary_sha256_after", "value": after_hash},
        {"metric_group": "run", "metric": "mode", "value": run_mode},
        {"metric_group": "run", "metric": "applied", "value": str(applied).lower()},
        {"metric_group": "run", "metric": "postcheck_clean", "value": str(postcheck_clean).lower()},
        {"metric_group": "count", "metric": "summary_rows_checked", "value": len(plan_rows)},
        {"metric_group": "count", "metric": "duplicate_source_ids_in_records", "value": duplicate_source_id_count},
    ]
    metric_rows.extend(
        {"metric_group": "action", "metric": key, "value": value}
        for key, value in action_counts.most_common()
    )
    metric_rows.extend(
        {"metric_group": "old_country_repaired", "metric": key, "value": value}
        for key, value in old_countries.most_common(20)
    )
    metric_rows.extend(
        {"metric_group": "new_country_repaired", "metric": key, "value": value}
        for key, value in new_countries.most_common(30)
    )
    write_csv(SUMMARY_OUT_CSV, metric_rows, ["metric_group", "metric", "value"])


def write_manifest(before_hash: str, after_hash: str, before_lines: int, after_lines: int) -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    text = f"""# Non-mainstream item/image source-summary geography repair recovery anchor

Date: {date.today().isoformat()}

Purpose:

- Record recovery anchors before and after repairing country-level geography in
  `data/capture_batch_nonmainstream_item_image_2026_source_summary.csv`.
- The CSV is Git-tracked, so this manifest records hashes and line counts
  instead of committing a duplicate copy.

Input/output:

- File: `data/capture_batch_nonmainstream_item_image_2026_source_summary.csv`
- Lines before: {before_lines}
- Lines after: {after_lines}
- SHA-256 before: `{before_hash}`
- SHA-256 after: `{after_hash}`

Boundary:

- No network data was fetched.
- No image binaries were downloaded.
- No capture records were mutated.
- No IMG01/IMG03 rights state was assigned.
- No generated public surfaces or frontend payload mirrors were rebuilt.
"""
    (BACKUP_DIR / "MANIFEST.md").write_text(text, encoding="utf-8")


def build_report(
    plan_rows: list[dict[str, str]],
    applied: bool,
    before_hash: str,
    after_hash: str,
    duplicate_source_id_count: int,
) -> str:
    actions = Counter(row["action"] for row in plan_rows)
    postcheck_clean = (not applied) and actions.get("unchanged", 0) == len(plan_rows)
    run_mode = "apply" if applied else ("dry-run postcheck" if postcheck_clean else "dry-run plan")
    old_countries = Counter(row["old_country_or_region"] for row in plan_rows if row["action"] == "repair_ready")
    new_countries = Counter(row["new_country_or_region"] for row in plan_rows if row["action"] == "repair_ready")
    examples = [row for row in plan_rows if row["action"] == "repair_ready"][:20]
    if postcheck_clean:
        interpretation = [
            "- Current source-summary geography matches the country-level `source_place_text` carried by the capture records.",
            "- The earlier overbroad buckets such as Caribbean and Caucasus are no longer present as repair-needed summary countries.",
            "- Duplicate source IDs are present in the capture-record layer, so this repair keys on source_id plus source_name.",
            "- Rows checked here still remain IMG02 and must pass item/surface review before they count as successful active sources.",
        ]
    else:
        interpretation = [
            "- This repair prevents the next source expansion from treating broad path segments such as Caribbean or Caucasus as countries.",
            "- Duplicate source IDs are present in the capture-record layer, so this repair keys on source_id plus source_name.",
            "- Rows repaired here still remain IMG02 and must pass item/surface review before they count as successful active sources.",
        ]

    lines = [
        "# Non-mainstream item/image source-summary geography repair v1",
        "",
        f"Generated: {date.today().isoformat()}",
        f"Run mode: {run_mode}",
        f"Applied mutation: {str(applied).lower()}",
        "",
        "## Scope",
        "",
        "- Repairs only `data/capture_batch_nonmainstream_item_image_2026_source_summary.csv`.",
        "- Uses country-level `source_place_text` already present in capture records.",
        "- Does not fetch network data, download images, mutate capture records, upgrade image rights, or rebuild public surfaces.",
        "",
        "## Hashes",
        "",
        f"- Before SHA-256: `{before_hash}`",
        f"- After SHA-256: `{after_hash}`",
        "",
        "## Actions",
        "",
    ]
    lines.append(f"- duplicate_source_ids_in_records: {duplicate_source_id_count}")
    lines.extend(f"- {key}: {value}" for key, value in actions.most_common())
    lines.extend(["", "## Main repaired old country buckets", ""])
    lines.extend(f"- {key}: {value}" for key, value in old_countries.most_common(20))
    lines.extend(["", "## Main repaired target countries", ""])
    lines.extend(f"- {key}: {value}" for key, value in new_countries.most_common(30))
    lines.extend(["", "## Examples", ""])
    if examples:
        lines.extend(
            [
                "| source_id | source | old | new |",
                "| --- | --- | --- | --- |",
            ]
        )
        for row in examples:
            lines.append(
                "| {source_id} | {source_name} | {old_macro_region} / {old_country_or_region} | {new_macro_region} / {new_country_or_region} |".format(
                    **row
                )
            )
    else:
        lines.append("- No repair-ready rows.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            *interpretation,
            "",
            "## Output files",
            "",
            "- `data/nonmainstream_item_image_source_summary_geo_repair_plan_v1.csv`",
            "- `data/nonmainstream_item_image_source_summary_geo_repair_summary_v1.csv`",
            "- `data/backups/nonmainstream_item_image_source_summary_geo_repair_2026_06_13/MANIFEST.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="mutate the source-summary CSV")
    args = parser.parse_args()

    records, _record_fields = read_csv(RECORDS_CSV)
    summary_rows, summary_fields = read_csv(SUMMARY_CSV)
    before_hash = sha256(SUMMARY_CSV)
    before_lines = line_count(SUMMARY_CSV)
    plan_rows = build_plan(records, summary_rows)
    duplicate_source_id_count = count_duplicate_source_ids(records)

    write_csv(
        PLAN_CSV,
        plan_rows,
        [
            "source_id",
            "source_name",
            "source_place_text",
            "old_macro_region",
            "old_country_or_region",
            "new_macro_region",
            "new_country_or_region",
            "action",
            "note",
        ],
    )

    if args.apply:
        repaired = apply_plan(summary_rows, plan_rows)
        write_csv(
            SUMMARY_CSV,
            repaired,
            summary_fields,
            lineterminator=detect_lineterminator(SUMMARY_CSV),
        )

    after_hash = sha256(SUMMARY_CSV)
    after_lines = line_count(SUMMARY_CSV)
    write_summary_metrics(plan_rows, args.apply, before_hash, after_hash, duplicate_source_id_count)
    write_manifest(before_hash, after_hash, before_lines, after_lines)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(
        build_report(plan_rows, args.apply, before_hash, after_hash, duplicate_source_id_count),
        encoding="utf-8",
    )

    actions = Counter(row["action"] for row in plan_rows)
    print(f"summary_rows_checked={len(plan_rows)}")
    print("actions=" + ",".join(f"{key}:{value}" for key, value in actions.most_common()))
    print(f"applied={str(args.apply).lower()}")
    print(f"before_sha256={before_hash}")
    print(f"after_sha256={after_hash}")


if __name__ == "__main__":
    main()
