from __future__ import annotations

import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import run_gallica_image_ready_1830_1970 as ga


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_DIR = DATA / "capture_batch_gallica_secondary_image_ready_1830_1970_raw"
RECORDS_CSV = DATA / "capture_batch_gallica_secondary_image_ready_1830_1970_records.csv"
SUMMARY_CSV = DATA / "capture_batch_gallica_secondary_image_ready_1830_1970_source_summary.csv"

MAX_ROWS = 140

QUERY_PLAN = [
    ("GAX01", "gallica_affiche_publicitaire", 'dc.title all "affiche publicitaire" and dc.date >= "1830" and dc.date <= "1970"', 35),
    ("GAX02", "gallica_reclame", 'dc.title all "réclame" and dc.date >= "1830" and dc.date <= "1970"', 30),
    ("GAX03", "gallica_typographie", 'dc.title all "typographie" and dc.date >= "1830" and dc.date <= "1970"', 25),
    ("GAX04", "gallica_imprimerie", 'dc.title all "imprimerie" and dc.date >= "1830" and dc.date <= "1970"', 25),
    ("GAX05", "gallica_catalogue_affiche", 'dc.title all "catalogue" and dc.description all "Affiche" and dc.date >= "1830" and dc.date <= "1970"', 25),
]


def write_raw(name: str, text: str) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    path.write_text(text, encoding="utf-8")
    return str(path.relative_to(ROOT))


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    seen = ga.existing_keys()

    for direction_id, direction_name, query, limit in QUERY_PLAN:
        start = 1
        while len([row for row in rows if row["direction_id"] == direction_id]) < limit and len(rows) < MAX_ROWS:
            url = ga.sru_url(query, start=start, maximum=50)
            try:
                xml_text = ga.fetch_text(url)
            except Exception as exc:  # noqa: BLE001
                failures.append({"direction_id": direction_id, "source_name": ga.SOURCE_NAME, "error": str(exc)})
                break
            raw_path = write_raw(f"{direction_name}_{start}.xml", xml_text)
            parsed = ga.parse_records(xml_text, direction_id, direction_name, url)
            if not parsed:
                break
            added = 0
            for row in parsed:
                key = (row.get("source_name", ""), row.get("source_identifier") or row.get("source_record_url", ""))
                if key in seen:
                    continue
                seen.add(key)
                row["raw_json_path"] = raw_path
                rows.append(row)
                added += 1
                if len([item for item in rows if item["direction_id"] == direction_id]) >= limit or len(rows) >= MAX_ROWS:
                    break
            if added == 0 and len(parsed) < 50:
                break
            start += 50
            time.sleep(0.35)

    rows.sort(key=lambda row: (int(row["date_start"]) if row.get("date_start") else 9999, row.get("source_title", "")))
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"GAX1970R{index:03d}"

    with RECORDS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ga.FIELDNAMES)
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
                    "source_id": ga.SOURCE_ID,
                    "source_name": ga.SOURCE_NAME,
                    "captured_count": str(len(items)),
                    "failure_count": str(sum(1 for failure in failures if failure["direction_id"] == direction_id)),
                    "img00_count": str(counter.get("IMG00", 0)),
                    "img01_count": str(counter.get("IMG01", 0)),
                    "img02_count": str(counter.get("IMG02", 0)),
                    "img03_count": str(counter.get("IMG03", 0)),
                    "img04_count": str(counter.get("IMG04", 0)),
                    "notes": "Secondary Gallica SRU/IIIF image-ready capture for advertising, typography, printing, and catalogue routes.",
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
