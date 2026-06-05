#!/usr/bin/env python3
"""Audit non-mainstream low-coverage source probe v3 outputs."""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

CANDIDATES = DATA / "nonmainstream_low_coverage_source_candidates_1990_2026_v3.csv"
PROBE = DATA / "nonmainstream_low_coverage_source_probe_1990_2026_v3.csv"
SUMMARY = DATA / "nonmainstream_low_coverage_source_probe_health_1990_2026_v3.csv"
REGION_BREAKDOWN = DATA / "nonmainstream_low_coverage_source_probe_region_breakdown_1990_2026_v3.csv"
REPORT = DOCS / "NONMAINSTREAM_LOW_COVERAGE_SOURCE_PROBE_HEALTH_1990_2026_v3.md"

BASELINE_GLOBAL_EDGE_SOURCES = 81
MIN_NEW_SOURCES = 220
MIN_OK_SOURCES = 120
SOURCE_VISIBLE_PROTOCOLS = {"IIIF", "CONTENTdm", "Kramerius", "DSpace"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


def pct(numerator: int, denominator: int) -> str:
    return f"{(numerator / denominator * 100):.2f}" if denominator else "0.00"


def failure_family(row: dict[str, str]) -> str:
    reason = (row.get("failure_reason", "") or row.get("http_status", "")).lower()
    status = row.get("http_status", "")
    if status in {"401", "403", "404", "429", "500", "502", "503"}:
        return f"http_{status}"
    if "certificate" in reason or "ssl" in reason or "wrong_version_number" in reason:
        return "ssl_or_certificate"
    if "timed out" in reason or "timeout" in reason:
        return "timeout"
    if "nodename nor servname" in reason or "name or service not known" in reason:
        return "dns_or_domain"
    if "network is unreachable" in reason:
        return "network_unreachable"
    if "not found" in reason:
        return "http_404"
    if row.get("probe_status") == "ok":
        return "ok"
    return "other_failure"


def split_protocols(value: str) -> set[str]:
    return {part.strip() for part in value.split(";") if part.strip()}


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def metric_rows(candidates: list[dict[str, str]], probe: list[dict[str, str]]) -> list[dict[str, str]]:
    by_id = {row["candidate_id"]: row for row in candidates}
    total = len(probe)
    ok_rows = [row for row in probe if row["probe_status"] == "ok"]
    p1_rows = [row for row in probe if row["capture_priority_next"].startswith("P1")]
    visible_rows = [
        row
        for row in probe
        if SOURCE_VISIBLE_PROTOCOLS.intersection(split_protocols(row.get("detected_protocols", "")))
    ]

    rows = [
        {"metric": "target", "value": "baseline_global_edge_sources", "count": str(BASELINE_GLOBAL_EDGE_SOURCES), "rate": ""},
        {"metric": "target", "value": "new_candidate_sources", "count": str(len(candidates)), "rate": pct(len(candidates), MIN_NEW_SOURCES)},
        {
            "metric": "target",
            "value": "baseline_plus_new_candidate_sources",
            "count": str(BASELINE_GLOBAL_EDGE_SOURCES + len(candidates)),
            "rate": "",
        },
        {"metric": "target", "value": "new_source_target_met", "count": str(len(candidates) >= MIN_NEW_SOURCES), "rate": ""},
        {"metric": "probe", "value": "probe_rows", "count": str(total), "rate": ""},
        {"metric": "probe", "value": "ok", "count": str(len(ok_rows)), "rate": pct(len(ok_rows), total)},
        {"metric": "probe", "value": "success_target_met", "count": str(len(ok_rows) >= MIN_OK_SOURCES), "rate": pct(len(ok_rows), MIN_OK_SOURCES)},
        {"metric": "probe", "value": "failed", "count": str(sum(1 for row in probe if row["probe_status"] == "failed")), "rate": pct(sum(1 for row in probe if row["probe_status"] == "failed"), total)},
        {"metric": "probe", "value": "http_error", "count": str(sum(1 for row in probe if row["probe_status"] == "http_error")), "rate": pct(sum(1 for row in probe if row["probe_status"] == "http_error"), total)},
        {"metric": "probe", "value": "p1_actionable_rows", "count": str(len(p1_rows)), "rate": pct(len(p1_rows), total)},
        {
            "metric": "img_source_visible",
            "value": "source_visible_protocol_candidates",
            "count": str(len(visible_rows)),
            "rate": pct(len(visible_rows), total),
        },
        {"metric": "rights", "value": "img01_img03_auto_upgrades", "count": "0", "rate": "0.00"},
    ]

    def add_counter(metric: str, counter: Counter[str], denominator: int = total) -> None:
        for value, count in counter.most_common():
            rows.append({"metric": metric, "value": value or "(blank)", "count": str(count), "rate": pct(count, denominator)})

    add_counter("probe_status", Counter(row["probe_status"] for row in probe))
    add_counter("capture_priority_next", Counter(row["capture_priority_next"] for row in probe))
    add_counter("adapter_hint", Counter(row["adapter_hint"] for row in probe))
    protocol_counter: Counter[str] = Counter()
    for row in probe:
        protocol_counter.update(split_protocols(row.get("detected_protocols", "")))
    add_counter("detected_protocol", protocol_counter)
    add_counter("failure_family", Counter(failure_family(row) for row in probe if row["probe_status"] != "ok"), total)
    add_counter("candidate_priority_all", Counter(row["priority"] for row in candidates), len(candidates))
    add_counter("impact_rating_all", Counter(row["impact_rating"] for row in candidates), len(candidates))
    add_counter(
        "candidate_priority_ok",
        Counter(by_id[row["candidate_id"]]["priority"] for row in ok_rows if row["candidate_id"] in by_id),
        len(ok_rows),
    )
    add_counter(
        "impact_rating_ok",
        Counter(by_id[row["candidate_id"]]["impact_rating"] for row in ok_rows if row["candidate_id"] in by_id),
        len(ok_rows),
    )
    return rows


def region_rows(candidates: list[dict[str, str]], probe: list[dict[str, str]]) -> list[dict[str, str]]:
    by_id = {row["candidate_id"]: row for row in candidates}
    regions: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for candidate in candidates:
        region = candidate["macro_region"]
        regions[region]["candidates"] += 1
        regions[region][f"priority_{candidate['priority']}"] += 1
        regions[region][f"impact_{candidate['impact_rating']}"] += 1
    for row in probe:
        region = row["macro_region"]
        regions[region]["probe_rows"] += 1
        regions[region][row["probe_status"]] += 1
        if row["capture_priority_next"].startswith("P1"):
            regions[region]["p1_actionable"] += 1
        if SOURCE_VISIBLE_PROTOCOLS.intersection(split_protocols(row.get("detected_protocols", ""))):
            regions[region]["source_visible_protocol_candidates"] += 1
        if row["candidate_id"] in by_id:
            regions[region][f"ok_impact_{by_id[row['candidate_id']]['impact_rating']}"] += int(row["probe_status"] == "ok")

    rows: list[dict[str, str]] = []
    for region, values in sorted(regions.items(), key=lambda item: (-item[1]["candidates"], item[0])):
        candidates_n = values["candidates"]
        ok_n = values["ok"]
        rows.append(
            {
                "macro_region": region,
                "candidate_sources": str(candidates_n),
                "ok": str(ok_n),
                "failed": str(values["failed"]),
                "http_error": str(values["http_error"]),
                "ok_rate": pct(ok_n, candidates_n),
                "p1_actionable": str(values["p1_actionable"]),
                "source_visible_protocol_candidates": str(values["source_visible_protocol_candidates"]),
                "priority_P0": str(values["priority_P0"]),
                "priority_P1": str(values["priority_P1"]),
                "priority_P2": str(values["priority_P2"]),
                "impact_A": str(values["impact_A"]),
                "impact_B": str(values["impact_B"]),
                "impact_C": str(values["impact_C"]),
            }
        )
    return rows


def write_report(summary: list[dict[str, str]], regions: list[dict[str, str]], candidates: list[dict[str, str]], probe: list[dict[str, str]]) -> None:
    lookup = {(row["metric"], row["value"]): row for row in summary}

    def value(metric: str, name: str) -> str:
        return lookup.get((metric, name), {}).get("count", "0")

    def rate(metric: str, name: str) -> str:
        return lookup.get((metric, name), {}).get("rate", "")

    failure_counts = Counter(failure_family(row) for row in probe if row["probe_status"] != "ok")
    ok_rows = [row for row in probe if row["probe_status"] == "ok"]
    by_id = {row["candidate_id"]: row for row in candidates}
    top_ok = [
        row
        for row in ok_rows
        if row["candidate_id"] in by_id and by_id[row["candidate_id"]].get("priority") in {"P0", "P1"}
    ][:40]

    lines = [
        "# Non-mainstream Low-coverage Source Probe Health 1990-2026 v3",
        "",
        "This audit measures the v3 source-discovery/probe pass. It does not audit ingested item records, does not download images, and does not grant image rights.",
        "",
        "## Goal Check",
        "",
        f"- Baseline global edge candidate sources: {BASELINE_GLOBAL_EDGE_SOURCES}",
        f"- New candidate sources: {len(candidates)} / target {MIN_NEW_SOURCES} ({rate('target', 'new_candidate_sources')}%)",
        f"- Baseline + new candidate pool: {BASELINE_GLOBAL_EDGE_SOURCES + len(candidates)}",
        f"- Probe successes: {value('probe', 'ok')} / target {MIN_OK_SOURCES} ({rate('probe', 'success_target_met')}% of target)",
        f"- Probe health / ok rate: {rate('probe', 'ok')}%",
        f"- P1 actionable rows: {value('probe', 'p1_actionable_rows')} ({rate('probe', 'p1_actionable_rows')}%)",
        f"- Source-visible protocol candidates: {value('img_source_visible', 'source_visible_protocol_candidates')} ({rate('img_source_visible', 'source_visible_protocol_candidates')}%)",
        f"- IMG01/IMG03 automatic upgrades: 0",
        "",
        "## Probe Status",
        "",
        f"- ok: {value('probe_status', 'ok')}",
        f"- failed: {value('probe_status', 'failed')}",
        f"- http_error: {value('probe_status', 'http_error')}",
        "",
        "## Candidate Priority And Impact",
        "",
    ]
    for row in summary:
        if row["metric"] in {"candidate_priority_all", "impact_rating_all", "candidate_priority_ok", "impact_rating_ok"}:
            lines.append(f"- {row['metric']} / {row['value']}: {row['count']} ({row['rate']}%)")

    lines.extend(["", "## Macro-region Breakdown", ""])
    for row in regions:
        lines.append(
            f"- {row['macro_region']}: candidates {row['candidate_sources']}, ok {row['ok']} "
            f"({row['ok_rate']}%), failed {row['failed']}, http_error {row['http_error']}, "
            f"P1 actionable {row['p1_actionable']}, source-visible protocol {row['source_visible_protocol_candidates']}"
        )

    lines.extend(["", "## Failure Families", ""])
    for family, count in failure_counts.most_common():
        lines.append(f"- {family}: {count}")

    lines.extend(["", "## High-value Reachable Next Queue", ""])
    for row in top_ok:
        candidate = by_id[row["candidate_id"]]
        lines.append(
            f"- {row['candidate_id']} | {row['source_name']} | {row['macro_region']} / {row['subregion']} | "
            f"{candidate['priority']} / impact {candidate['impact_rating']} | {row['adapter_hint']} | "
            f"{row['detected_protocols'] or row['protocol_family']}"
        )

    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This pass is source discovery only.",
            "- Raw probe text is third-party page text and should not be committed unless separately reviewed and redacted.",
            "- `IMG01` and `IMG03` cannot be promoted from heuristic, LLM, platform, TOS, or protocol signals.",
            "- Source-visible protocol candidates only indicate possible source-hosted viewing routes such as IIIF/CONTENTdm/DSpace/Kramerius.",
            "- Impact/source priority remains internal triage only.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    candidates = read_csv(CANDIDATES)
    probe = read_csv(PROBE)
    summary = metric_rows(candidates, probe)
    regions = region_rows(candidates, probe)
    write_csv(SUMMARY, ["metric", "value", "count", "rate"], summary)
    write_csv(
        REGION_BREAKDOWN,
        [
            "macro_region",
            "candidate_sources",
            "ok",
            "failed",
            "http_error",
            "ok_rate",
            "p1_actionable",
            "source_visible_protocol_candidates",
            "priority_P0",
            "priority_P1",
            "priority_P2",
            "impact_A",
            "impact_B",
            "impact_C",
        ],
        regions,
    )
    write_report(summary, regions, candidates, probe)
    ok = sum(1 for row in probe if row["probe_status"] == "ok")
    print(f"new_candidates={len(candidates)}")
    print(f"baseline_plus_new={BASELINE_GLOBAL_EDGE_SOURCES + len(candidates)}")
    print(f"ok={ok}")
    print(f"success_target_met={ok >= MIN_OK_SOURCES}")
    print(f"probe_health={pct(ok, len(probe))}")
    print(f"wrote {SUMMARY.relative_to(ROOT)}")
    print(f"wrote {REGION_BREAKDOWN.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
