from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
IA_SOURCE_NAME = "Internet Archive / text and periodical collections"


def archive_identifier(row: dict[str, str]) -> str:
    identifier = (row.get("source_identifier") or "").strip()
    if identifier:
        return identifier
    url = (row.get("source_record_url") or "").rstrip("/")
    if "/details/" in url:
        return url.rsplit("/details/", 1)[-1].split("/")[0]
    return ""


def remediate_row(row: dict[str, str]) -> bool:
    if row.get("source_name") != IA_SOURCE_NAME:
        return False
    if (row.get("image_presence_code") or "IMG00") != "IMG00":
        return False

    identifier = archive_identifier(row)
    if not identifier:
        return False

    image_url = f"https://archive.org/services/img/{identifier}"
    rights_note = (
        "Internet Archive services/img exposes a source-hosted thumbnail or cover. "
        "Use source-linked display only; do not store a local copy, and keep item-level rights visible."
    )
    row["image_presence_code"] = "IMG02"
    row["image_presence_basis"] = rights_note
    row["image_state_evaluation"] = f"IMG02: {rights_note}"
    row["image_state_confidence"] = "medium"
    row["rights_review_required"] = "true"
    row["image_state_review_note"] = (
        "Source-hosted Internet Archive image candidate; retain source return and rights review."
    )
    row["image_frame_behavior"] = "source_viewer_frame"
    row["image_url_detected"] = image_url
    row["local_copy_permitted"] = "false"
    row["iiif_or_viewer_available"] = row.get("source_record_url") or image_url
    row["fallback_required"] = "false"
    row["fallback_reason"] = ""
    row["image_expectation"] = "expected"
    row["parser_status"] = row.get("parser_status") or "ok"
    row["display_mode"] = "source_viewer_frame"
    if not row.get("source_rights_text"):
        row["source_rights_text"] = rights_note
    if not row.get("rights_basis"):
        row["rights_basis"] = rights_note
    return True


def process_file(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = [dict(row) for row in reader]
        fieldnames = reader.fieldnames or []

    changed = 0
    for row in rows:
        if remediate_row(row):
            changed += 1

    if not changed:
        return 0

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return changed


def main() -> None:
    total = 0
    for path in sorted(DATA.glob("capture_batch_*records.csv")):
        changed = process_file(path)
        if changed:
            total += changed
            print(f"{path.name}: {changed}")
    print(f"remediated={total}")


if __name__ == "__main__":
    main()
