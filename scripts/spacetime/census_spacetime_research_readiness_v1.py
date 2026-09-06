#!/usr/bin/env python3
"""Spacetime research-readiness census, v1.

Reads the frozen v49 public Spacetime resources — the governed geography
registry, the 23 period-region aggregates, the record index with its
temporal precision, the public source-viewer projection (source host per
record), the reader-eligibility census and the visual-availability census —
and evaluates every governed geography for research readiness.

Nothing is inferred: every metric is a count over the frozen files. The
gates' thresholds are derived from the observed distribution (see the
report) and are printed with the decisions. Output: a CSV of all 93
geographies with metrics, decision and reason codes; a versioned candidate
registry JSON; a Markdown report. The underlying 93-geography projection is
not touched — a geography that is not promoted is NOT_RESEARCH_READY for
this Spacetime release, nothing else.
"""
from __future__ import annotations

import csv
import hashlib
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "frontend" / "generated"
SPT = GEN / "trace-spacetime-v1"

OUT_CSV = ROOT / "data" / "spacetime_research_readiness_census_v1.csv"
OUT_JSON = ROOT / "data" / "spacetime_research_region_registry_candidate_v1.json"
OUT_MD = ROOT / "docs" / "frontend" / "SPACETIME_RESEARCH_READINESS_CENSUS_v1.md"

REGISTRY_VERSION = "spacetime-research-region-registry-candidate/v1"

# the sealed count tiers (features/trace-v49/spacetime/gis, TRACE_NATIVE_COUNT_TIERS):
# 1–4 · 5–24 · 25–99 · 100+ — "substantive" here means the second tier or above
SUBSTANTIVE_PERIOD_MIN = 5

PRECISE = ("year", "month", "day")
VISUAL_ROUTES = ("SOURCE_VIEWER_AVAILABLE", "REMOTE_VISUAL_CANDIDATE_VERIFIED")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def longest_run(flags: list[bool]) -> int:
    best = run = 0
    for flag in flags:
        run = run + 1 if flag else 0
        best = max(best, run)
    return best


def pct(numerator: float, denominator: float) -> float:
    return round(100.0 * numerator / denominator, 1) if denominator else 0.0


def main() -> int:
    manifest = load(SPT / "manifest.json")
    registry = load(SPT / "geography-registry.json")
    aggregates = load(SPT / "period-region-aggregates.json")
    buckets = load(SPT / "time-buckets.json")
    record_index = load(SPT / "record-index.json")
    source_viewer = load(GEN / "source-viewer-v49" / "source-viewer.json")
    eligibility = load(GEN / "reader-eligibility-v49" / "eligibility.json")
    visual = load(GEN / "visual-availability-v49" / "census.json")

    # --- bindings: everything must be the one frozen release --------------
    release = manifest["sourceRelease"]["researchReleaseId"]
    for name, doc in (("source-viewer", source_viewer), ("eligibility", eligibility), ("visual", visual)):
        assert doc["release_id"] == release, f"{name} is not {release}"
    for name in ("geography-registry.json", "period-region-aggregates.json", "record-index.json", "time-buckets.json"):
        assert sha256(SPT / name) == manifest["payloadSha256"][name], f"{name} sha mismatch"
    assert len(record_index["records"]) == manifest["counts"]["publicObjects"] == 7995

    periods = buckets["periods"]  # chronological
    period_order = {p["periodId"]: i for i, p in enumerate(periods)}
    period_label = {p["periodId"]: p["label"] for p in periods}
    denominators = {p["periodId"]: p["recordCount"] for p in periods}

    # --- per-record side tables -------------------------------------------
    host_of = {e[0]: urlparse(e[1]).netloc for e in source_viewer["entries"]}
    eligible = {e[0]: e[1] for e in eligibility["entries"]}
    visual_of = {r[0]: r[2] for r in visual["rows"]}  # schema: stableId, reading, visual, ...
    assert len(host_of) == len(eligible) == len(visual_of) == 7995

    # --- per-geography accumulation from the record index ------------------
    geo = {}
    for entry in registry["entries"]:
        geo[entry["geographyId"]] = {
            "entry": entry,
            "records": set(),
            "precision": Counter(),
            "hosts": Counter(),
            "eligible": 0,
            "visual": 0,
            "year_min": None,
            "year_max": None,
            "periods": Counter(),
        }
    for record in record_index["records"]:
        oid = record["objectId"]
        time = record["time"]
        for gid in record["geographyIds"]:
            g = geo[gid]
            g["records"].add(oid)
            g["precision"][time["precision"]] += 1
            g["hosts"][host_of[oid]] += 1
            g["eligible"] += eligible[oid] == "INDEX_ELIGIBLE"
            g["visual"] += visual_of[oid] in VISUAL_ROUTES
            g["year_min"] = time["startYearInclusive"] if g["year_min"] is None else min(g["year_min"], time["startYearInclusive"])
            g["year_max"] = time["endYearInclusive"] if g["year_max"] is None else max(g["year_max"], time["endYearInclusive"])
            for pid in record["periodIds"]:
                g["periods"][pid] += 1

    # --- the sealed aggregates must agree with the record index ------------
    cell_counts = {}
    rank_in_period = {}
    for period in aggregates["periods"]:
        pid = period["periodId"]
        assert period["denominator"] == denominators[pid]
        cells = sorted(period["cells"], key=lambda c: (-c["recordCount"], c["geographyId"]))
        for rank, cell in enumerate(cells, start=1):
            cell_counts[(pid, cell["geographyId"])] = cell["recordCount"]
            rank_in_period[(pid, cell["geographyId"])] = rank
    for gid, g in geo.items():
        for pid, count in g["periods"].items():
            assert cell_counts.get((pid, gid), 0) == count, (gid, pid)
        assert sum(1 for (pid, x) in cell_counts if x == gid and cell_counts[(pid, x)] > 0) == len(g["periods"])
    assert len([k for k, v in cell_counts.items() if v > 0]) == manifest["counts"]["periodRegionCells"] == 373

    # --- metrics -------------------------------------------------------------
    rows = []
    for gid, g in geo.items():
        entry = g["entry"]
        total = len(g["records"])
        series = [g["periods"].get(p["periodId"], 0) for p in periods]
        active = [c > 0 for c in series]
        substantive = [c >= SUBSTANTIVE_PERIOD_MIN for c in series]
        assignments = sum(series)
        active_counts = [c for c in series if c > 0]
        peak_index = max(range(len(series)), key=lambda i: series[i])
        shares = [pct(series[i], denominators[periods[i]["periodId"]]) for i in range(len(series))]
        ranks = [rank_in_period.get((periods[i]["periodId"], gid)) for i in range(len(series))]
        active_indexes = [i for i, c in enumerate(series) if c > 0]
        precise = sum(g["precision"][p] for p in PRECISE)
        top_host, top_host_count = g["hosts"].most_common(1)[0]
        flags = []
        if pct(top_host_count, total) >= 75.0:
            flags.append("SOURCE_DOMINANT_75")
        if pct(series[peak_index], assignments) >= 50.0:
            flags.append("PEAK_DECADE_HALF")
        if pct(g["eligible"], total) < 50.0:
            flags.append("READER_FACING_MINORITY")
        if entry["transnational"] or entry["broadRegion"]:
            flags.append("COMPOSITE_GOVERNED_IDENTITY")
        rows.append({
            "geographyId": gid,
            "label": entry["displayLabel"],
            "class": entry["geographyClass"],
            "mappingState": entry["mappingState"],
            "transnational": entry["transnational"],
            "broadRegion": entry["broadRegion"],
            "historical": entry["historicalStatus"],
            "total_public_records": total,
            "period_assignments": assignments,
            "active_period_count": sum(active),
            "longest_consecutive_run": longest_run(active),
            "substantive_period_count": sum(substantive),
            "longest_substantive_run": longest_run(substantive),
            "first_active_period": period_label[periods[active_indexes[0]]["periodId"]],
            "last_active_period": period_label[periods[active_indexes[-1]]["periodId"]],
            "year_min": g["year_min"],
            "year_max": g["year_max"],
            "median_records_per_active_period": statistics.median(active_counts),
            "peak_period": period_label[periods[peak_index]["periodId"]],
            "peak_period_records": series[peak_index],
            "peak_period_concentration_pct": pct(series[peak_index], assignments),
            "off_peak_records": assignments - series[peak_index],
            "max_share_of_period_pct": max(shares),
            "periods_at_rank_1": sum(1 for r in ranks if r == 1),
            "periods_in_top_3": sum(1 for r in ranks if r is not None and r <= 3),
            "precise_records": precise,
            "precise_share_pct": pct(precise, total),
            "approximate_records": g["precision"]["approximate"],
            "range_records": g["precision"]["range"],
            "source_count": len(g["hosts"]),
            "top_source": top_host,
            "top_source_share_pct": pct(top_host_count, total),
            "outside_top_source_records": total - top_host_count,
            "reader_facing_records": g["eligible"],
            "reader_facing_share_pct": pct(g["eligible"], total),
            "visual_route_records": g["visual"],
            "visual_route_share_pct": pct(g["visual"], total),
            "flags": flags,
            "records_by_period": series,
            "share_by_period_pct": shares,
            "rank_by_period": ranks,
        })
    rows.sort(key=lambda r: (-r["total_public_records"], r["label"]))

    if "--distribution" in sys.argv:
        keys = ["total_public_records", "active_period_count", "longest_consecutive_run", "substantive_period_count",
                "longest_substantive_run", "median_records_per_active_period", "peak_period_concentration_pct",
                "max_share_of_period_pct", "precise_share_pct", "source_count", "top_source_share_pct",
                "reader_facing_share_pct", "visual_route_share_pct"]
        print("metric\tmin\tp25\tp50\tp75\tp90\tmax")
        for key in keys:
            values = sorted(float(r[key]) for r in rows)
            q = statistics.quantiles(values, n=20)
            print(f"{key}\t{values[0]}\t{q[4]}\t{q[9]}\t{q[14]}\t{q[17]}\t{values[-1]}")
        print()
        head = ["label", "mappingState", "total_public_records", "active_period_count", "longest_consecutive_run",
                "substantive_period_count", "longest_substantive_run", "median_records_per_active_period",
                "peak_period_concentration_pct", "precise_share_pct", "source_count", "top_source_share_pct",
                "reader_facing_share_pct", "visual_route_share_pct", "first_active_period", "last_active_period"]
        print("\t".join(head))
        for r in rows:
            print("\t".join(str(r[k]) for k in head))
        return 0

    from census_gates_v1 import GATES, decide  # noqa: E402  (same directory)

    decided = []
    for r in rows:
        strict_codes = decide(r, GATES["STRICT"])
        relaxed_codes = decide(r, GATES["RELAXED"])
        if not strict_codes:
            decision = "OPEN"
            codes = ["OPEN"]
        elif not relaxed_codes:
            decision = "REVIEW"
            codes = strict_codes
        else:
            decision = "NOT_READY"
            codes = relaxed_codes
        decided.append({**r, "decision": decision, "reason_codes": codes, "strict_codes": strict_codes, "relaxed_codes": relaxed_codes})

    # --- CSV -------------------------------------------------------------------
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = [k for k in decided[0].keys() if k not in ("records_by_period", "share_by_period_pct", "rank_by_period", "strict_codes", "relaxed_codes")]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields + ["records_by_period", "share_by_period_pct", "rank_by_period"])
        for r in decided:
            writer.writerow([("|".join(r[k]) if k in ("reason_codes", "flags") else r[k]) for k in fields]
                            + ["|".join(str(x) for x in r["records_by_period"]),
                               "|".join(str(x) for x in r["share_by_period_pct"]),
                               "|".join("" if x is None else str(x) for x in r["rank_by_period"])])

    # --- the candidate registry -----------------------------------------------
    registry_out = {
        "format": REGISTRY_VERSION,
        "status": "CANDIDATE_PENDING_OWNER_APPROVAL",
        "projectionId": manifest["projectionId"],
        "projectionSha256": manifest["projectionSha256"],
        "sourceRelease": manifest["sourceRelease"],
        "inputs": {
            "trace-spacetime-v1": manifest["payloadSha256"],
            "source-viewer-v49": sha256(GEN / "source-viewer-v49" / "source-viewer.json"),
            "reader-eligibility-v49": sha256(GEN / "reader-eligibility-v49" / "eligibility.json"),
            "visual-availability-v49": sha256(GEN / "visual-availability-v49" / "census.json"),
        },
        "substantivePeriodMinRecords": SUBSTANTIVE_PERIOD_MIN,
        "gates": GATES,
        "periods": [p["label"] for p in periods],
        "counts": Counter(r["decision"] for r in decided),
        "geographies": [
            {
                "geographyId": r["geographyId"],
                "label": r["label"],
                "mappingState": r["mappingState"],
                "decision": r["decision"],
                "reasonCodes": r["reason_codes"],
                "flags": r["flags"],
                "metrics": {k: r[k] for k in fields if k not in ("geographyId", "label", "mappingState", "decision", "reason_codes", "flags")},
                "recordsByPeriod": r["records_by_period"],
                "shareByPeriodPct": r["share_by_period_pct"],
                "rankByPeriod": r["rank_by_period"],
            }
            for r in decided
        ],
    }
    OUT_JSON.write_text(json.dumps(registry_out, indent=1, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8")

    label_of = {gid: g["entry"]["displayLabel"] for gid, g in geo.items()}
    coverage = []
    for period in aggregates["periods"]:
        cells = sorted((c for c in period["cells"] if c["recordCount"] > 0), key=lambda c: (-c["recordCount"], c["geographyId"]))
        top = cells[0]
        coverage.append({
            "label": period_label[period["periodId"]],
            "denominator": period["denominator"],
            "geographies": len(cells),
            "mapped_geographies": sum(1 for c in cells if c["mappingState"] == "mapped"),
            "top": label_of[top["geographyId"]],
            "top_records": top["recordCount"],
            "top_share_pct": pct(top["recordCount"], period["denominator"]),
            "substantive_geographies": sum(1 for c in cells if c["recordCount"] >= SUBSTANTIVE_PERIOD_MIN),
        })
    from census_report_v1 import write_report  # noqa: E402
    write_report(OUT_MD, decided, periods, GATES, manifest, SUBSTANTIVE_PERIOD_MIN, OUT_CSV, OUT_JSON, coverage)
    print(json.dumps({"decisions": registry_out["counts"], "csv": str(OUT_CSV), "json": str(OUT_JSON), "md": str(OUT_MD)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
