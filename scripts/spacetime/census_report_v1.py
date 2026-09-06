"""The census report writer, v1 (Markdown)."""
from __future__ import annotations

import statistics
from collections import Counter
from pathlib import Path

from census_gates_v1 import REASONS


def fmt(value) -> str:
    if isinstance(value, float):
        return f"{value:,.1f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(" --- " for _ in headers) + "|"]
    for row in rows:
        out.append("| " + " | ".join(fmt(v) for v in row) + " |")
    return "\n".join(out)


def series_line(row: dict, periods: list[dict]) -> str:
    parts = []
    for i, count in enumerate(row["records_by_period"]):
        if count:
            parts.append(f"{periods[i]['label']} {count}")
    return " · ".join(parts)


def candidate_rows(rows: list[dict]) -> list[list]:
    out = []
    for r in rows:
        out.append([
            r["label"], r["total_public_records"], r["active_period_count"], r["substantive_period_count"],
            r["longest_substantive_run"], r["median_records_per_active_period"],
            f"{r['peak_period']} ({r['peak_period_concentration_pct']}%)",
            f"{r['source_count']} ({r['top_source_share_pct']}% {r['top_source']})",
            f"{r['precise_share_pct']}%", f"{r['reader_facing_records']:,} ({r['reader_facing_share_pct']}%)",
            f"{r['first_active_period']}–{r['last_active_period']}", r["decision"], ", ".join(r["reason_codes"]),
        ])
    return out


CANDIDATE_HEAD = ["Place", "Records", "Active decades", "Substantive decades (≥5)", "Longest substantive run",
                  "Median / active decade", "Peak decade (share)", "Institutions (top share)", "Year-or-finer",
                  "Reader-facing", "Range", "Decision", "Reason codes"]


def write_report(path: Path, decided: list[dict], periods: list[dict], gates: dict, manifest: dict,
                 substantive_min: int, csv_path: Path, json_path: Path, coverage: list[dict]) -> None:
    root = path.parents[2]
    counts = Counter(r["decision"] for r in decided)
    open_rows = [r for r in decided if r["decision"] == "OPEN"]
    review_rows = [r for r in decided if r["decision"] == "REVIEW"]
    not_ready = [r for r in decided if r["decision"] == "NOT_READY"]
    reason_counts = Counter(code for r in not_ready for code in r["reason_codes"])

    metric_keys = [
        ("total_public_records", "Public records"),
        ("active_period_count", "Active decades (non-zero)"),
        ("substantive_period_count", f"Substantive decades (≥{substantive_min})"),
        ("longest_substantive_run", "Longest consecutive substantive run"),
        ("median_records_per_active_period", "Median records per active decade"),
        ("peak_period_concentration_pct", "Peak-decade concentration %"),
        ("off_peak_records", "Records outside the peak decade"),
        ("max_share_of_period_pct", "Largest share of a period denominator %"),
        ("source_count", "Institutions"),
        ("top_source_share_pct", "Top-institution share %"),
        ("outside_top_source_records", "Records outside the top institution"),
        ("precise_share_pct", "Year-or-finer share %"),
        ("reader_facing_share_pct", "Reader-facing share %"),
        ("visual_route_share_pct", "Visual-route share %"),
    ]
    dist_rows = []
    for key, name in metric_keys:
        values = sorted(float(r[key]) for r in decided)
        q = statistics.quantiles(values, n=20)
        dist_rows.append([name, values[0], q[4], q[9], q[14], q[17], values[-1]])

    gate_rows = []
    for key in [k for k in gates["STRICT"] if k != "intent"]:
        gate_rows.append([key, gates["STRICT"][key], gates["RELAXED"][key]])

    lines = []
    lines.append("# Spacetime research-readiness census · v1\n")
    lines.append("**Status: CANDIDATE — pending the owner's approval. Nothing here is wired into the UI.**\n")
    lines.append(f"Release `{manifest['sourceRelease']['researchReleaseId']}` · projection `{manifest['projectionId']}` "
                 f"(`{manifest['projectionSha256'][:16]}…`) · generator `scripts/spacetime/census_spacetime_research_readiness_v1.py` · "
                 f"outputs `{csv_path.relative_to(root)}`, `{json_path.relative_to(root)}`.\n")
    lines.append("## 1 · Why\n")
    lines.append("The sealed v49 Spacetime projection governs 93 geographies over 23 decades (373 non-zero period × geography "
                 "cells). Governance means every one of them is *safe to show*; it does not mean every one of them can carry "
                 "research. Exposing all 93 as equal options on a world map overstates the archive's geographic and temporal "
                 "coverage: most decades are carried by a handful of places, and most places are a handful of records. This census "
                 "evaluates every governed geography for research readiness and proposes a separate, versioned **Spacetime Research "
                 "Region Registry** that decides which geographies are promoted into the normal public Spacetime UI. The projection "
                 "underneath is untouched; a geography that is not promoted is not deleted and not held — it is `NOT_RESEARCH_READY` "
                 "for this Spacetime release.\n")
    lines.append("A first-release Research Region maps directly to one existing governed geography identity. No macro-region "
                 "(Western Europe, East Asia, Latin America, Global North) is composed in this round; that would be a separate "
                 "governance decision.\n")
    lines.append("## 2 · Inputs (all frozen, all one release)\n")
    lines.append("- `frontend/generated/trace-spacetime-v1/` — geography registry (93), period-region aggregates (23 periods, "
                 "per-cell record counts, denominators, precision breakdowns), record index (7,995 public records with "
                 "geography ids, period ids, governed year extent and precision), time buckets; payload sha256 checked against the manifest.")
    lines.append("- `frontend/generated/source-viewer-v49/source-viewer.json` — the public source record URL of every record; the "
                 "URL host is the record's source institution (13 hosts). Cross-checked read-only against the frozen candidate "
                 "payload's `objects.source_name`: each host maps to exactly one institution (the V&A's two API names share one "
                 "host, as do the Library of Congress's two).")
    lines.append("- `frontend/generated/reader-eligibility-v49/eligibility.json` — `INDEX_ELIGIBLE` (a human-readable title) vs "
                 "`RECORD_ONLY` per record: the reader-facing usability of a matching-records list.")
    lines.append("- `frontend/generated/visual-availability-v49/census.json` — whether a record has a visual route "
                 "(`SOURCE_VIEWER_AVAILABLE` or `REMOTE_VISUAL_CANDIDATE_VERIFIED`); reported, not gated.")
    lines.append("- Nothing is inferred. Where a value is not in the frozen public resources it is not computed.\n")
    lines.append("## 3 · Metrics per geography\n")
    lines.append("| Metric | Definition |\n| --- | --- |")
    lines.append("| Public records | distinct public records whose governed geography ids include the geography |")
    lines.append("| Records by decade | the sealed period-region cell counts (INTERVAL_OVERLAP: a ranged record counts in every decade it overlaps, so the decade sum can exceed the record count); verified equal to a recount from the record index |")
    lines.append("| Active decades | decades with at least one record |")
    lines.append(f"| Substantive decades | decades with at least {substantive_min} records — the second sealed count tier (1–4 · 5–24 · 25–99 · 100+) |")
    lines.append("| Longest substantive run | the longest sequence of consecutive substantive decades |")
    lines.append("| Median records per active decade | the typical active decade |")
    lines.append("| Peak-decade concentration | the largest decade's share of the geography's decade assignments; and the records outside that decade |")
    lines.append("| Share of period | the geography's records over the period's public denominator, per decade; rank within the decade |")
    lines.append("| Year-or-finer share | records whose governed precision is `year`, `month` or `day` (vs `approximate`, `range`) |")
    lines.append("| Institutions | distinct source hosts; the top institution's share; the records outside it |")
    lines.append("| Reader-facing | `INDEX_ELIGIBLE` records (a human-readable title) |")
    lines.append("| Visual route | records with a source-viewer frame or a verified remote image |")
    lines.append("| Mapping state | the registry's `mapped` / `aggregate_only` / `unmapped` |\n")
    lines.append("## 4 · Observed distribution (93 geographies)\n")
    lines.append(table(["Metric", "min", "p25", "p50", "p75", "p90", "max"], dist_rows) + "\n")
    n = len(decided)
    small = sum(r["total_public_records"] <= 8 for r in decided)
    brief = sum(r["active_period_count"] <= 2 for r in decided)
    tiny = sum(r["total_public_records"] <= 2 for r in decided)
    top_tier = sum(r["total_public_records"] >= 100 for r in decided)
    long_run = sum(r["longest_substantive_run"] >= 4 for r in decided)
    single = sum(r["source_count"] == 1 for r in decided)
    lines.append(f"The archive is steep: {small} of the {n} governed geographies have 8 records or fewer, {brief} are active in two "
                 f"decades or fewer, {tiny} have at most 2 records. Only {top_tier} geographies reach the top sealed count tier (100+) "
                 f"and only {long_run} have a run of four or more substantive decades; {single} are single-institution.\n")
    lines.append("### Per-decade coverage\n")
    lines.append(table(["Decade", "Public records", "Geographies", "Mapped", f"Substantive (≥{substantive_min})", "Top geography", "Top records", "Top share %"],
                       [[c["label"], c["denominator"], c["geographies"], c["mapped_geographies"], c["substantive_geographies"], c["top"], c["top_records"], c["top_share_pct"]] for c in coverage]) + "\n")
    early = [c for c in coverage if c["label"] < "1890s"]
    early_max = max(c["substantive_geographies"] for c in early)
    early_dominant = sum(1 for c in early if c["top_share_pct"] > 50.0)
    lines.append(f"Before the 1890s no decade has more than {early_max} geographies with five or more records, and in {early_dominant} "
                 f"of those {len(early)} decades one geography holds more than half of the decade. Only the 1960s and 1970s have more "
                 f"than 20 substantive geographies. A world map of the other decades draws a global coverage the archive does not have.\n")
    lines.append("## 5 · The gates (thresholds derived from §4)\n")
    lines.append(table(["Criterion", "STRICT", "RELAXED"], gate_rows) + "\n")
    lines.append("Derivation:\n")
    lines.append("- **Absolute floors reuse the sealed count tiers** (`TRACE_NATIVE_COUNT_TIERS`: 1–4 · 5–24 · 25–99 · 100+). STRICT "
                 "requires the top tier (100+) for the geography's records, its reader-facing records and its material outside the peak "
                 "decade, and the third tier (25+) for material outside the top institution; RELAXED steps each down one tier. "
                 "A *substantive* decade is the second tier (5+).")
    lines.append("- **Continuity** is the cohort's own distribution: STRICT = the 90th percentile (6 substantive decades, a run of 4 — "
                 "p90 is 6.0 and 3.6); RELAXED = above the 75th percentile (3 and 2 — p75 is 2 and 2).")
    lines.append("- **Single-period concentration** fails only when the peak decade holds more than the gate's share *and* the "
                 "remainder is below the volume floor: a geography whose remainder is itself a top-tier body of material is not "
                 "'one decade', however large that decade is (the United Kingdom's 1980s is the case).")
    lines.append("- **Source concentration** requires a second institution with tier-level material (25+ STRICT, 5+ RELAXED) rather "
                 "than a share ceiling, because a share ceiling would fail the two largest continuous series (the United Kingdom at "
                 "92.8% V&A, Norway at 92.9% National Library) while passing two-record geographies split one-and-one. The share is "
                 "disclosed as a flag (`SOURCE_DOMINANT_75`) for the Data quality fold instead.")
    lines.append("- **Date quality**: 90% year-or-finer (STRICT) / 80% (RELAXED); the cohort's 10th percentile is 100%, so the gate only "
                 "catches the tail (Switzerland 87.5, Poland 89.9, Spain 80.0, Egypt 66.7).")
    lines.append("- **Mapped** is required by both gates: a Research Region needs a map locator.\n")
    lines.append("Reason codes: " + "; ".join(f"`{k}` — {v}" for k, v in REASONS.items()) + ". Disclosure flags (never a decision): "
                 "`SOURCE_DOMINANT_75` (one institution ≥ 75%), `PEAK_DECADE_HALF` (one decade ≥ 50%), `READER_FACING_MINORITY` "
                 "(reader-facing < 50%), `COMPOSITE_GOVERNED_IDENTITY` (a governed transnational or broad-region identity).\n")
    lines.append(f"## 6 · Decisions: {counts['OPEN']} OPEN · {counts['REVIEW']} REVIEW · {counts['NOT_READY']} NOT_READY\n")
    lines.append("### 6.1 · STRICT candidates (OPEN) — proposed first release\n")
    lines.append(table(CANDIDATE_HEAD, candidate_rows(open_rows)) + "\n")
    for r in open_rows:
        lines.append(f"- **{r['label']}** — {series_line(r, periods)}." + (f" Flags: {', '.join(r['flags'])}." if r["flags"] else ""))
    lines.append("")
    lines.append("### 6.2 · Near misses (REVIEW) — pass RELAXED, fail STRICT\n")
    lines.append(table(CANDIDATE_HEAD, candidate_rows(review_rows)) + "\n")
    for r in review_rows:
        lines.append(f"- **{r['label']}** — {series_line(r, periods)}." + (f" Flags: {', '.join(r['flags'])}." if r["flags"] else ""))
    lines.append("")
    lines.append("### 6.3 · NOT_READY — by reason code (a geography can carry several)\n")
    lines.append(table(["Reason code", "Geographies"], [[k, v] for k, v in reason_counts.most_common()]) + "\n")
    lines.append("### 6.4 · All 93 geographies\n")
    lines.append(table(["Place", "State", "Records", "Active", f"Subst. (≥{substantive_min})", "Run", "Median", "Peak %", "Inst.", "Top inst. %", "Year+ %", "Reader-facing", "Range", "Decision", "Reason codes"],
                       [[r["label"], r["mappingState"], r["total_public_records"], r["active_period_count"], r["substantive_period_count"],
                         r["longest_substantive_run"], r["median_records_per_active_period"], r["peak_period_concentration_pct"], r["source_count"],
                         r["top_source_share_pct"], r["precise_share_pct"], r["reader_facing_records"],
                         f"{r['first_active_period']}–{r['last_active_period']}", r["decision"], ", ".join(r["reason_codes"])] for r in decided]) + "\n")
    lines.append("## 7 · Findings the product must state\n")
    uk = next(r for r in decided if r["label"] == "United Kingdom")
    lines.append(f"- The United Kingdom's 1980s (1,630 of the decade's 1,898 public records) is 1,629 V&A records and one Nasjonalmuseet record; "
                 f"{uk['top_source_share_pct']}% of the United Kingdom's {uk['total_public_records']:,} records are V&A, and only "
                 f"{uk['reader_facing_records']:,} ({uk['reader_facing_share_pct']}%) carry a human-readable title (the V&A titles are "
                 f"mostly source identifiers). It still passes STRICT — 21 substantive decades, 230 records from five other institutions — "
                 f"but the Data quality fold must say so.")
    lines.append("- Norway is a single-institution series in effect (92.9% National Library of Norway) with 40 records from four others; "
                 "China / Hong Kong is 93.3% Library of Congress with 75.5% of its material in one decade; Indonesia (96.2%), Austria (98.7%), "
                 "Finland, Portugal and the Pacific territories (100%) are single-institution captures in effect.")
    lines.append("- Under STRICT the open set is exactly the geographies that are continuous, multi-institution and large: six in Europe, "
                 "the United States and Japan. Nothing in the Pacific, Africa, the Middle East, South Asia, Southeast Asia or Latin America "
                 "clears it; under RELAXED only China / Hong Kong, Chile, Malaysia and South Africa do outside Europe and North America. "
                 "That is the archive's present coverage, not a curatorial choice, and the public statement should say it.")
    lines.append("- Aggregate-only identities with research-scale material — Global / transnational (97), Cuba / transnational (76) — are "
                 "excluded only by `NOT_MAPPED`; a later governance round could give transnational identities a non-map research surface.\n")
    lines.append("## 8 · What this round does not do\n")
    lines.append("- It does not change `gis/*`, the governed readers, the read APIs, the projection, the period membership or the count tiers.")
    lines.append("- It does not hard-code the shortlist into the UI: the registry is `CANDIDATE_PENDING_OWNER_APPROVAL`.")
    lines.append("- It does not compose macro-regions and does not rename or hold any geography.\n")
    lines.append("## 9 · Proposed public Spacetime scope (for review, not built)\n")
    lines.append("Entry: **RESEARCH REGIONS** — the approved set as cards (name · substantive decades · public records · research range "
                 "first–last substantive decade · a one-line source statement), plus the boundary sentence: *We do not expose a geography "
                 "merely because a record can be plotted. Spacetime opens a place for research only when the current archive contains "
                 "sufficient temporal and evidentiary coverage.* Selecting a region opens five blocks: 01 Research region (name, Change), "
                 "02 Time (the decade rail limited to the region's substantive range, previous → current → next with counts), 03 Map (one "
                 "primary visualization: the region's locator with the three-bar temporal glyph; Density / Texture under View options; the "
                 "world atlas as an optional Overview mode, not the entry), 04 Place profile (records · share of period · rank; the "
                 "three-decade ledger; Data quality fold holding mapping state, precision mix, institution mix, reader-facing share, "
                 "flags), 05 Records (matching records). System suggests reads the region's own change only.\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
