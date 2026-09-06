"""The two research-readiness gates, v1 — thresholds derived from the
observed v49 distribution (docs/frontend/SPACETIME_RESEARCH_READINESS_CENSUS_v1.md §4).

Absolute floors reuse the sealed Spacetime count tiers (1–4 · 5–24 · 25–99 ·
100+): a governed vocabulary, not a number chosen for this census. The
continuity floors are the cohort's 90th (STRICT) and 75th (RELAXED)
percentiles. Every failed criterion yields one reason code; a geography that
fails nothing is OPEN under that gate.
"""
from __future__ import annotations

GATES = {
    "STRICT": {
        "intent": "first-release research geographies (about 6–10)",
        "mapped": True,
        "min_total_public_records": 100,
        "min_substantive_periods": 6,
        "min_longest_substantive_run": 4,
        "max_peak_period_concentration_pct": 50.0,
        "min_off_peak_records": 100,
        "min_source_count": 2,
        "min_outside_top_source_records": 25,
        "min_precise_share_pct": 90.0,
        "min_reader_facing_records": 100,
    },
    "RELAXED": {
        "intent": "future expansion (about 12–20)",
        "mapped": True,
        "min_total_public_records": 25,
        "min_substantive_periods": 3,
        "min_longest_substantive_run": 2,
        "max_peak_period_concentration_pct": 75.0,
        "min_off_peak_records": 25,
        "min_source_count": 2,
        "min_outside_top_source_records": 5,
        "min_precise_share_pct": 80.0,
        "min_reader_facing_records": 25,
    },
}

REASONS = {
    "NOT_MAPPED": "no safe map position in the governed registry (aggregate-only or unmapped)",
    "LOW_TOTAL_VOLUME": "fewer public records than the gate's volume floor",
    "INSUFFICIENT_TEMPORAL_CONTINUITY": "too few substantive decades, or no long enough consecutive run of them",
    "SINGLE_PERIOD_CONCENTRATION": "one decade holds more than the gate's share and the remainder is below the volume floor",
    "SOURCE_CONCENTRATION": "a single institution, or too little material from any other institution",
    "DATE_QUALITY_INSUFFICIENT": "too small a share of records dated to a year or finer",
    "INSUFFICIENT_READER_FACING_RECORDS": "too few records with a human-readable title (reader-eligibility census)",
}


def decide(row: dict, gate: dict) -> list[str]:
    codes = []
    if gate["mapped"] and row["mappingState"] != "mapped":
        codes.append("NOT_MAPPED")
    if row["total_public_records"] < gate["min_total_public_records"]:
        codes.append("LOW_TOTAL_VOLUME")
    if row["substantive_period_count"] < gate["min_substantive_periods"] or row["longest_substantive_run"] < gate["min_longest_substantive_run"]:
        codes.append("INSUFFICIENT_TEMPORAL_CONTINUITY")
    if row["peak_period_concentration_pct"] > gate["max_peak_period_concentration_pct"] and row["off_peak_records"] < gate["min_off_peak_records"]:
        codes.append("SINGLE_PERIOD_CONCENTRATION")
    if row["source_count"] < gate["min_source_count"] or row["outside_top_source_records"] < gate["min_outside_top_source_records"]:
        codes.append("SOURCE_CONCENTRATION")
    if row["precise_share_pct"] < gate["min_precise_share_pct"]:
        codes.append("DATE_QUALITY_INSUFFICIENT")
    if row["reader_facing_records"] < gate["min_reader_facing_records"]:
        codes.append("INSUFFICIENT_READER_FACING_RECORDS")
    return codes
