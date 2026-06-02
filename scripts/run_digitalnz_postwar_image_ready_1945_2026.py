from __future__ import annotations

from pathlib import Path

import run_digitalnz_image_ready_1830_1970 as digitalnz


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

digitalnz.RAW_DIR = DATA / "capture_batch_digitalnz_postwar_image_ready_1945_2026_raw"
digitalnz.RECORDS_CSV = DATA / "capture_batch_digitalnz_postwar_image_ready_1945_2026_records.csv"
digitalnz.SUMMARY_CSV = DATA / "capture_batch_digitalnz_postwar_image_ready_1945_2026_source_summary.csv"
digitalnz.YEAR_START = 1945
digitalnz.YEAR_END = 2026
digitalnz.MAX_ROWS = 130
digitalnz.CAPTURE_PREFIX = "DNZPOSTR"
digitalnz.USER_AGENT = "ModernGDHistory/0.1 digitalnz-postwar-image-ready"

digitalnz.QUERY_PLAN = [
    ("DNZP01", "digitalnz_postwar_poster_records", "poster", 30),
    ("DNZP02", "digitalnz_postwar_protest_poster", "protest poster", 20),
    ("DNZP03", "digitalnz_postwar_exhibition_poster", "exhibition poster", 20),
    ("DNZP04", "digitalnz_postwar_tourism_poster", "tourism poster", 20),
    ("DNZP05", "digitalnz_maori_poster", "Māori poster", 15),
    ("DNZP06", "digitalnz_pacific_poster", "Pacific poster", 15),
    ("DNZP07", "digitalnz_postwar_typography_design", "graphic design typography", 20),
    ("DNZP08", "digitalnz_postwar_advertising_print", "advertising", 25),
]


if __name__ == "__main__":
    digitalnz.main()
