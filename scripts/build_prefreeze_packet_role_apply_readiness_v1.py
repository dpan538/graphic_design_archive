#!/usr/bin/env python3
"""Prepare apply-readiness queues for reviewed packet-role draft overrides.

This script only classifies draft rows. It does not mutate capture CSVs, rebuild
payloads, download images, or change rights/image states.
"""

from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

DRAFT = DATA / "prefreeze_packet_role_override_draft_v1.csv"
REVIEW_QUEUE = DATA / "prefreeze_packet_role_review_queue_v1.csv"

OUT_APPLY_READY = DATA / "prefreeze_packet_role_apply_ready_v1.csv"
OUT_HOLD_REVIEW = DATA / "prefreeze_packet_role_hold_review_v1.csv"
OUT_SAMPLE = DATA / "prefreeze_packet_role_sample_review_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_packet_role_source_join_summary_v1.csv"
OUT_REPORT = DOCS / "PREFREEZE_PACKET_ROLE_APPLY_READINESS_v1.md"

SUMMARY_FIELDS = ["metric", "value", "notes"]

ROW_FIELDS = [
    "source_file",
    "capture_id",
    "surface_id",
    "packet_id",
    "surface_disposition_override",
    "readiness_status",
    "readiness_reason",
    "source_join_status",
    "review_decision",
    "review_confidence",
    "review_basis",
    "review_lane",
    "packet_action",
    "packet_confidence",
    "packet_type",
    "relation_density",
    "source_depth",
    "rights_state",
    "editorial_need",
    "current_publication_role",
    "recommended_role",
    "anchor_score",
    "year",
    "region",
    "theme",
    "medium",
    "movement",
    "source_name",
    "title",
]

SAMPLE_FIELDS = ROW_FIELDS + ["sample_lane", "sample_key"]

APPLY_DECISIONS = {"draft_subsheet_demote"}
CARD_REVIEW_DECISIONS = {"draft_card_demote", "keep_card_support"}
KEEP_REFERENCE_DECISIONS = {"keep_main_anchor_candidate"}
MIN_RELATION_DENSITY = 3

HISTORICAL_REVIEW_PERIODS = [
    (1846, 1848, ("mexico", "united states", "latin america")),
    (1939, 1945, ("france", "germany", "italy", "japan", "poland", "russia")),
    (1947, 1991, ("germany", "russia", "soviet", "ukraine", "caucasus")),
    (1949, 1990, ("germany", "china", "taiwan", "korea")),
]

SOURCE_FAMILY_HOLD_PREFIXES = (
    "wikimedia commons",
    "colnect",
)

SOURCE_TEXT_HOLD_TERMS = (
    "stamp",
    "postage",
    "commemorative",
    "coin",
    "banknote",
    "medal",
    "trophy",
    "event photo",
    "session",
    "conference",
    "inauguration",
    "anniversary",
    "ceremony",
    "street view",
    "tourist",
    "wildlife",
    "natural history",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def clean(value: object) -> str:
    return str(value or "").strip()


def as_int(value: object) -> int:
    try:
        return int(float(str(value or "0")))
    except ValueError:
        return 0


def has_any(text: str, needles: tuple[str, ...]) -> bool:
    lowered = clean(text).casefold()
    return any(needle in lowered for needle in needles)


def historical_review_reason(row: dict[str, str]) -> str:
    year = as_int(row.get("year"))
    if not year:
        return ""
    region = clean(row.get("region")).casefold()
    title = clean(row.get("title")).casefold()
    source = clean(row.get("source_name")).casefold()
    combined = f"{region} {title} {source}"
    for start, end, terms in HISTORICAL_REVIEW_PERIODS:
        if start <= year <= end and any(term in combined for term in terms):
            return f"historical/geography review period: {year}"
    return ""


def research_combination_risk(row: dict[str, str]) -> str:
    region = clean(row.get("region"))
    source_name = clean(row.get("source_name"))
    title = clean(row.get("title"))
    medium = clean(row.get("medium"))
    movement = clean(row.get("movement"))
    source_lower = source_name.casefold()

    if not region or region.casefold().startswith("unresolved") or "transnational" in region.casefold():
        return "region not stable enough for automatic packet role application"
    if source_lower.startswith(SOURCE_FAMILY_HOLD_PREFIXES):
        return "source family requires sample review before packet role application"
    if "file source /" in source_lower and "page " in source_lower:
        return "file-page source requires sample review before packet role application"
    if has_any(" ".join([source_name, title, medium, movement]), SOURCE_TEXT_HOLD_TERMS):
        return "stamp/event/photo/context term requires review before packet role application"
    historical = historical_review_reason(row)
    if historical:
        return historical
    return ""


def capture_record_files() -> list[Path]:
    return sorted(DATA.glob("capture_batch_*_records.csv"))


def capture_lookup() -> dict[str, list[dict[str, str]]]:
    lookup: dict[str, list[dict[str, str]]] = defaultdict(list)
    for path in capture_record_files():
        for row in read_csv(path):
            capture_id = clean(row.get("capture_id"))
            if not capture_id:
                continue
            entry = dict(row)
            entry["_source_file"] = path.name
            lookup[capture_id].append(entry)
    return lookup


def same_text(left: str, right: str) -> bool:
    return clean(left).casefold() == clean(right).casefold()


def resolve_source_file(row: dict[str, str], lookup: dict[str, list[dict[str, str]]]) -> tuple[str, str]:
    existing = clean(row.get("source_file"))
    if existing:
        return existing, "already_present"
    capture_id = clean(row.get("capture_id"))
    matches = lookup.get(capture_id, [])
    if not matches:
        return "", "missing_capture_id"
    if len(matches) == 1:
        return matches[0]["_source_file"], "unique_capture_id"

    title = clean(row.get("title"))
    source_name = clean(row.get("source_name"))
    scored: list[tuple[int, dict[str, str]]] = []
    for match in matches:
        score = 0
        if same_text(title, match.get("source_title", "")):
            score += 2
        if same_text(source_name, match.get("source_name", "")):
            score += 2
        if title and title.casefold() in clean(match.get("source_title")).casefold():
            score += 1
        scored.append((score, match))
    best_score = max(score for score, _ in scored)
    best = [match for score, match in scored if score == best_score and score > 0]
    if len(best) == 1:
        return best[0]["_source_file"], "resolved_duplicate_capture_id"
    return "", "ambiguous_capture_id"


def review_lookup(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        key = (clean(row.get("packet_id")), clean(row.get("surface_id")))
        if key[0] and key[1]:
            lookup[key] = row
    return lookup


def readiness(row: dict[str, str]) -> tuple[str, str]:
    join_status = clean(row.get("source_join_status"))
    decision = clean(row.get("review_decision"))
    confidence = clean(row.get("review_confidence"))
    role = clean(row.get("surface_disposition_override"))
    lane = clean(row.get("review_lane"))
    packet_confidence = clean(row.get("packet_confidence"))
    source_depth = clean(row.get("source_depth"))
    rights_state = clean(row.get("rights_state"))
    relation_density = as_int(row.get("relation_density"))

    if join_status not in {"unique_capture_id", "resolved_duplicate_capture_id", "already_present"}:
        return "hold_review", f"source join not unique: {join_status}"
    if lane != "conservative_draft_override":
        return "hold_review", f"not conservative lane: {lane}"
    if decision in KEEP_REFERENCE_DECISIONS:
        return "reference_only", "main-anchor keep reference; no demotion override needed"
    if decision in CARD_REVIEW_DECISIONS:
        return "hold_review", "card-related decisions require visual/editorial sample review"
    if decision not in APPLY_DECISIONS:
        return "hold_review", f"decision not apply-ready: {decision}"
    if confidence != "high" or packet_confidence != "high":
        return "hold_review", "confidence below high"
    if role != "support_packet_appendix_text":
        return "hold_review", f"role not support appendage: {role}"
    if source_depth not in {"medium", "high"}:
        return "hold_review", f"source depth too low: {source_depth}"
    if rights_state not in {"source_visible", "verified_open"}:
        return "hold_review", f"rights/source visibility not sufficient: {rights_state}"
    if relation_density < MIN_RELATION_DENSITY:
        return "hold_review", f"relation density below {MIN_RELATION_DENSITY}"
    risk_reason = research_combination_risk(row)
    if risk_reason:
        return "hold_review", risk_reason
    return "apply_ready", "unique source join and high-confidence packet-member subsheet demotion"


def merged_rows() -> tuple[list[dict[str, object]], Counter[str]]:
    draft_rows = read_csv(DRAFT)
    queue_rows = read_csv(REVIEW_QUEUE)
    queue = review_lookup(queue_rows)
    captures = capture_lookup()
    join_counts: Counter[str] = Counter()
    rows: list[dict[str, object]] = []

    for draft in draft_rows:
        packet_id = clean(draft.get("packet_id"))
        surface_id = clean(draft.get("surface_id"))
        queue_row = queue.get((packet_id, surface_id), {})
        source_file, join_status = resolve_source_file(draft, captures)
        join_counts[join_status] += 1
        merged = {
            **draft,
            "source_file": source_file,
            "source_join_status": join_status,
            "review_lane": queue_row.get("review_lane", ""),
            "packet_action": queue_row.get("packet_action", ""),
            "packet_confidence": queue_row.get("packet_confidence", ""),
            "packet_type": queue_row.get("packet_type", ""),
            "relation_density": queue_row.get("relation_density", ""),
            "source_depth": queue_row.get("source_depth", ""),
            "rights_state": queue_row.get("rights_state", ""),
            "editorial_need": queue_row.get("editorial_need", ""),
            "current_publication_role": queue_row.get("current_publication_role", ""),
            "recommended_role": queue_row.get("recommended_role", ""),
            "anchor_score": queue_row.get("anchor_score", ""),
            "year": queue_row.get("year", ""),
            "region": queue_row.get("region", ""),
            "theme": queue_row.get("theme", ""),
            "medium": queue_row.get("medium", ""),
            "movement": queue_row.get("movement", ""),
        }
        status, reason = readiness(merged)
        merged["readiness_status"] = status
        merged["readiness_reason"] = reason
        rows.append(merged)
    return rows, join_counts


def sample_key(row: dict[str, object]) -> str:
    return "|".join(
        clean(row.get(key))
        for key in ("readiness_status", "surface_disposition_override", "source_name", "region", "year")
    )


def stable_score(row: dict[str, object]) -> str:
    seed = "|".join(clean(row.get(key)) for key in ("packet_id", "surface_id", "capture_id", "title"))
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()


def sample_rows(rows: list[dict[str, object]], per_bucket: int = 5) -> list[dict[str, object]]:
    buckets: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        if row["readiness_status"] == "reference_only":
            continue
        key = sample_key(row)
        buckets[key].append(row)
    sampled: list[dict[str, object]] = []
    for key, values in sorted(buckets.items()):
        values.sort(key=stable_score)
        for row in values[:per_bucket]:
            sampled.append({**row, "sample_lane": clean(row.get("readiness_status")), "sample_key": key})
    return sampled


def write_report(summary_rows: list[dict[str, object]], apply_rows: list[dict[str, object]], hold_rows: list[dict[str, object]], sample: list[dict[str, object]]) -> None:
    lines = [
        "# Prefreeze Packet Role Apply Readiness v1",
        "",
        "Scope: source-file join, confidence filtering, and sample queue for packet-role draft overrides.",
        "",
        "This pass does not mutate capture records, does not rebuild the public payload, does not download images, and does not change rights or image states.",
        "",
        "## Summary",
        "",
    ]
    for row in summary_rows:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Interpretation", ""])
    lines.append("- `apply_ready` rows are source-file-backed, high-confidence, and pass the stricter risk gate; they are still a small rebuild-test queue, not a final applied layer.")
    lines.append("- `hold_review` rows remain useful for editorial planning but should not be applied automatically.")
    lines.append("- Main-anchor keep rows are reference-only; they document packet anchors but do not need an override.")
    lines.append("- Commons/Colnect file-page clusters, unstable regions, historical review periods, and stamp/event/photo/context terms are held for sample review.")
    lines.extend(["", "## Next Use", ""])
    lines.append("- Review the sample queue by source family, region, and period.")
    lines.append("- If sample review passes, create a separate applied override file from `apply_ready` rows only.")
    lines.append("- Rebuild the candidate payload in chunks after applying a small tested override layer.")
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows, join_counts = merged_rows()
    apply_rows = [row for row in rows if row["readiness_status"] == "apply_ready"]
    hold_rows = [row for row in rows if row["readiness_status"] == "hold_review"]
    reference_rows = [row for row in rows if row["readiness_status"] == "reference_only"]
    sample = sample_rows(rows)

    status_counts = Counter(row["readiness_status"] for row in rows)
    reason_counts = Counter(row["readiness_reason"] for row in rows)
    role_counts = Counter(row["surface_disposition_override"] for row in apply_rows)
    source_counts = Counter(row["source_name"] for row in apply_rows)
    summary_rows: list[dict[str, object]] = [
        {"metric": "draft_rows_scanned", "value": len(rows), "notes": "Packet role draft rows scanned."},
        {"metric": "apply_ready_rows", "value": len(apply_rows), "notes": "Rows technically ready for a later applied override file."},
        {"metric": "hold_review_rows", "value": len(hold_rows), "notes": "Rows held for sample/manual review."},
        {"metric": "reference_only_rows", "value": len(reference_rows), "notes": "Main-anchor keep references; no override needed."},
        {"metric": "sample_review_rows", "value": len(sample), "notes": "Deterministic sample queue for review."},
    ]
    for status, count in status_counts.most_common():
        summary_rows.append({"metric": f"status:{status}", "value": count, "notes": "Readiness status distribution."})
    for status, count in join_counts.most_common():
        summary_rows.append({"metric": f"source_join:{status}", "value": count, "notes": "Source-file join status distribution."})
    for role, count in role_counts.most_common():
        summary_rows.append({"metric": f"apply_ready_role:{role}", "value": count, "notes": "Apply-ready role distribution."})
    for reason, count in reason_counts.most_common(12):
        summary_rows.append({"metric": f"reason:{reason}", "value": count, "notes": "Top readiness reasons."})
    for source, count in source_counts.most_common(12):
        summary_rows.append({"metric": f"apply_ready_source:{source}", "value": count, "notes": "Top apply-ready source families/names."})

    write_csv(OUT_APPLY_READY, apply_rows, ROW_FIELDS)
    write_csv(OUT_HOLD_REVIEW, hold_rows + reference_rows, ROW_FIELDS)
    write_csv(OUT_SAMPLE, sample, SAMPLE_FIELDS)
    write_csv(OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_report(summary_rows, apply_rows, hold_rows, sample)

    print(f"draft_rows_scanned={len(rows)}")
    print(f"apply_ready_rows={len(apply_rows)}")
    print(f"hold_review_rows={len(hold_rows)}")
    print(f"reference_only_rows={len(reference_rows)}")
    print(f"sample_review_rows={len(sample)}")
    print(f"wrote {OUT_APPLY_READY.relative_to(ROOT)}")
    print(f"wrote {OUT_HOLD_REVIEW.relative_to(ROOT)}")
    print(f"wrote {OUT_SAMPLE.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
