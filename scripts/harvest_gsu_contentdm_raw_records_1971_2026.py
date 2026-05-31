from __future__ import annotations

from collections import Counter
from pathlib import Path

import harvest_gsu_contentdm_raw_records as base


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

base.YEAR_START = 1971
base.YEAR_END = 2026
base.RECORDS_CSV = DATA / "capture_batch_gsu_contentdm_image_ready_1971_2026_records.csv"
base.SUMMARY_CSV = DATA / "capture_batch_gsu_contentdm_image_ready_1971_2026_source_summary.csv"

base.COLLECTION_LIMITS = {
    "signal": 8,
    "arwg": 6,
    "AFLCIO": 5,
    "IAM": 5,
    "gpc": 4,
    "PATCO": 4,
    "lane": 2,
    "gae": 3,
    "mhross": 3,
    "GSB": 3,
    "eastern": 2,
    "lgbtq": 2,
    "ajc": 2,
    "marta": 2,
    "labor": 2,
    "popmusic": 1,
    "gawl": 1,
    "yearbooks": 1,
    "SKennedy": 1,
    "popcul": 1,
    "CLATL": 1,
    "printed": 1,
}

base.COLLECTION_PRIORITY = {
    "AFLCIO": 1,
    "PATCO": 2,
    "GSB": 3,
    "signal": 4,
    "arwg": 5,
    "gpc": 6,
    "IAM": 7,
    "gae": 8,
    "mhross": 9,
    "marta": 10,
    "ajc": 11,
    "labor": 12,
    "lgbtq": 13,
    "eastern": 14,
    "gawl": 15,
    "popmusic": 16,
    "yearbooks": 17,
    "SKennedy": 18,
    "popcul": 19,
    "CLATL": 20,
    "printed": 21,
    "lane": 22,
}


def main() -> None:
    rows = base.harvest_rows()
    for index, row in enumerate(rows, start=1):
        row["capture_id"] = f"GSU2026R{index:03d}"
        row["direction_id"] = "GSU05"
        row["direction_name"] = "gsu_raw_harvest_late_twentieth_and_contemporary_print_culture"
        row["historical_context_note"] = (
            "GSU CONTENTdm adds later-stage local and university-held evidence for "
            "student newspapers, labor print culture, public communication, activism, "
            "institutional records, and regional visual culture from 1971-2026. "
            "Records are retained even when they fall outside the current design sprint, "
            "because the archive is intended to cover every later period."
        )
        row["classification_rationale"] = (
            "Selected from already captured CONTENTdm raw records by full date range, "
            "source-hosted image/PDF presence, source collection, subject terms, and "
            "per-collection caps to avoid serial issue flooding."
        )
    base.write_records(rows)
    print(f"captured={len(rows)}")
    print(f"image_states={dict(Counter(row['image_presence_code'] for row in rows))}")


if __name__ == "__main__":
    main()
