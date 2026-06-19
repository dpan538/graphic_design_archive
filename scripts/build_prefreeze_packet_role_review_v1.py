#!/usr/bin/env python3
"""Build review queues and conservative draft role overrides from packet audit.

This pass is advisory. It does not mutate the candidate or official payload and
does not change image rights states.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

PACKETS = DATA / "prefreeze_packetization_candidates_v1.csv"
SURFACE_RECS = DATA / "prefreeze_packetization_surface_recommendations_v1.csv"

OUT_REVIEW = DATA / "prefreeze_packet_role_review_queue_v1.csv"
OUT_OVERRIDES = DATA / "prefreeze_packet_role_override_draft_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_packet_role_review_summary_v1.csv"
OUT_REPORT = DOCS / "PREFREEZE_PACKET_ROLE_REVIEW_v1.md"

SUMMARY_FIELDS = ["metric", "value", "notes"]

REVIEW_FIELDS = [
    "packet_id",
    "surface_id",
    "capture_id",
    "review_lane",
    "packet_action",
    "packet_confidence",
    "packet_type",
    "member_count",
    "relation_density",
    "source_depth",
    "rights_state",
    "editorial_need",
    "current_publication_role",
    "current_surface_type",
    "recommended_role",
    "draft_surface_disposition_override",
    "review_decision",
    "review_confidence",
    "review_reason",
    "anchor_score",
    "title",
    "year",
    "region",
    "theme",
    "medium",
    "movement",
    "source_name",
    "image_state",
]

OVERRIDE_FIELDS = [
    "source_file",
    "capture_id",
    "surface_id",
    "packet_id",
    "surface_disposition_override",
    "review_decision",
    "review_confidence",
    "review_basis",
    "source_name",
    "title",
]


AUTO_PACKET_ACTIONS = {
    "promote_one_main_anchor_demote_members_to_subsheets",
    "demote_parallel_mains_to_subsheet_cluster",
}

VISIBLE_RIGHTS = {"source_visible", "verified_open"}
REVIEWABLE_ROLES = {"main_sheet_anchor_candidate", "subsheet_candidate", "card_or_appendix_candidate"}


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


def packet_eligible(packet: dict[str, str]) -> bool:
    return (
        packet.get("recommended_action") in AUTO_PACKET_ACTIONS
        and packet.get("confidence") == "high"
        and packet.get("rights_state") in VISIBLE_RIGHTS
        and packet.get("source_depth") in {"medium", "high"}
        and as_int(packet.get("relation_density")) >= 3
    )


def packet_review_lane(packet: dict[str, str]) -> str:
    action = packet.get("recommended_action", "")
    if packet_eligible(packet):
        return "conservative_draft_override"
    if action in AUTO_PACKET_ACTIONS:
        return "sample_before_override"
    if action == "manual_packet_or_card_review":
        return "manual_packet_or_card_review"
    return "packet_reference_only"


def role_decision(member: dict[str, str], packet: dict[str, str]) -> tuple[str, str, str, str]:
    """Return override, decision, confidence, reason."""
    lane = packet_review_lane(packet)
    current_role = clean(member.get("current_publication_role"))
    rec_role = clean(member.get("recommended_role"))
    sid = clean(member.get("surface_id"))
    anchor_id = clean(packet.get("proposed_main_anchor_id"))

    if lane != "conservative_draft_override":
        return "", "review_only", "medium", f"{lane}; no draft override emitted."
    if sid == anchor_id:
        if rec_role == "main_sheet_anchor_candidate" and as_int(member.get("anchor_score")) >= 60:
            return "main_sheet", "keep_main_anchor_candidate", "high", "Best packet anchor; retain as candidate main sheet."
        return "", "anchor_manual_review", "medium", "Packet anchor lacks enough score for automatic keep-main draft."
    if current_role == "card" or member.get("current_surface_type") == "card":
        return "card", "keep_card_support", "high", "Already a card/context surface."
    if rec_role == "card_or_appendix_candidate":
        return "card", "draft_card_demote", "medium", "Packet member has weak/context signal; draft card support role."
    if rec_role == "subsheet_candidate":
        return "support_packet_appendix_text", "draft_subsheet_demote", "high", "Related packet member; draft subsheet/support role."
    if rec_role in {"appendix_or_subsheet", "card"}:
        return current_role or "support_packet_appendix_text", "keep_existing_support", "high", "Already support-oriented."
    return "", "member_manual_review", "medium", "Member relation found, but role is not safe for draft override."


def choose_packet_for_member(member: dict[str, str], packet_by_id: dict[str, dict[str, str]]) -> dict[str, str] | None:
    packet_id = clean(member.get("packet_id"))
    if packet_id:
        return packet_by_id.get(packet_id)
    return None


def output_row(member: dict[str, str], packet: dict[str, str]) -> dict[str, object]:
    override, decision, confidence, reason = role_decision(member, packet)
    return {
        "packet_id": packet.get("packet_id", ""),
        "surface_id": member.get("surface_id", ""),
        "capture_id": member.get("capture_id", ""),
        "review_lane": packet_review_lane(packet),
        "packet_action": packet.get("recommended_action", ""),
        "packet_confidence": packet.get("confidence", ""),
        "packet_type": packet.get("packet_type", ""),
        "member_count": packet.get("member_count", ""),
        "relation_density": packet.get("relation_density", ""),
        "source_depth": packet.get("source_depth", ""),
        "rights_state": packet.get("rights_state", ""),
        "editorial_need": packet.get("editorial_need", ""),
        "current_publication_role": member.get("current_publication_role", ""),
        "current_surface_type": member.get("current_surface_type", ""),
        "recommended_role": member.get("recommended_role", ""),
        "draft_surface_disposition_override": override,
        "review_decision": decision,
        "review_confidence": confidence,
        "review_reason": reason,
        "anchor_score": member.get("anchor_score", ""),
        "title": member.get("title", ""),
        "year": member.get("year", ""),
        "region": member.get("region", ""),
        "theme": member.get("theme", ""),
        "medium": member.get("medium", ""),
        "movement": member.get("movement", ""),
        "source_name": member.get("source_name", ""),
        "image_state": member.get("image_state", ""),
    }


def source_file_from_capture(capture_id: str) -> str:
    # This draft deliberately does not infer source_file. Applying it requires a
    # later join against the candidate payload or capture registry.
    return ""


def override_row(row: dict[str, object]) -> dict[str, object]:
    capture_id = clean(row.get("capture_id"))
    return {
        "source_file": source_file_from_capture(capture_id),
        "capture_id": capture_id,
        "surface_id": row.get("surface_id", ""),
        "packet_id": row.get("packet_id", ""),
        "surface_disposition_override": row.get("draft_surface_disposition_override", ""),
        "review_decision": row.get("review_decision", ""),
        "review_confidence": row.get("review_confidence", ""),
        "review_basis": row.get("review_reason", ""),
        "source_name": row.get("source_name", ""),
        "title": row.get("title", ""),
    }


def write_report(summary_rows: list[dict[str, object]], review_rows: list[dict[str, object]], override_rows_: list[dict[str, object]]) -> None:
    lane_counts = Counter(row["review_lane"] for row in review_rows)
    decision_counts = Counter(row["review_decision"] for row in review_rows)
    lines = [
        "# Prefreeze Packet Role Review v1",
        "",
        "Scope: review queues and conservative draft overrides derived from the packetization audit.",
        "",
        "This pass is advisory. It does not mutate the official payload, does not download images, and does not change rights or image states.",
        "",
        "## Summary",
        "",
    ]
    for row in summary_rows:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Review Lanes", ""])
    for lane, count in lane_counts.most_common():
        lines.append(f"- {lane}: {count}")
    lines.extend(["", "## Decisions", ""])
    for decision, count in decision_counts.most_common():
        lines.append(f"- {decision}: {count}")
    lines.extend(["", "## Guardrails", ""])
    lines.append("- Draft overrides are not wired into rebuild scripts.")
    lines.append("- `source_file` is intentionally blank in the draft override file; application requires a later audited join.")
    lines.append("- Manual packet/card review rows are excluded from conservative override application.")
    lines.append("- Weak or broad packets remain review evidence only.")
    lines.extend(["", "## Next Use", ""])
    lines.append("- Sample the conservative draft override rows by source family and period before any applied override layer.")
    lines.append("- Add source-file joins only after sample review confirms the packet logic.")
    lines.append("- Use manual lanes for editorial packet planning, not automatic rebuild changes.")
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    packets = read_csv(PACKETS)
    members = read_csv(SURFACE_RECS)
    packet_by_id = {clean(row.get("packet_id")): row for row in packets}

    review_packets = {
        row["packet_id"]
        for row in packets
        if row.get("recommended_action") in AUTO_PACKET_ACTIONS
        or row.get("recommended_action") == "manual_packet_or_card_review"
    }

    review_rows: list[dict[str, object]] = []
    for member in members:
        packet = choose_packet_for_member(member, packet_by_id)
        if not packet or packet.get("packet_id") not in review_packets:
            continue
        if member.get("recommended_role") not in REVIEWABLE_ROLES and member.get("current_surface_type") != "card":
            continue
        review_rows.append(output_row(member, packet))

    overrides = [
        override_row(row)
        for row in review_rows
        if clean(row.get("draft_surface_disposition_override"))
        and row.get("review_lane") == "conservative_draft_override"
    ]

    packet_lane_counts = Counter(packet_review_lane(row) for row in packets)
    review_lane_counts = Counter(row["review_lane"] for row in review_rows)
    decision_counts = Counter(row["review_decision"] for row in review_rows)
    override_role_counts = Counter(row["surface_disposition_override"] for row in overrides)

    summary_rows: list[dict[str, object]] = [
        {"metric": "packets_scanned", "value": len(packets), "notes": "Packet candidates scanned."},
        {"metric": "surface_recommendations_scanned", "value": len(members), "notes": "Surface recommendations scanned."},
        {"metric": "review_queue_rows", "value": len(review_rows), "notes": "Rows in packet role review queue."},
        {"metric": "draft_override_rows", "value": len(overrides), "notes": "Conservative draft override rows; not applied."},
    ]
    for lane, count in packet_lane_counts.most_common():
        summary_rows.append({"metric": f"packet_lane:{lane}", "value": count, "notes": "Packet-level lane distribution."})
    for lane, count in review_lane_counts.most_common():
        summary_rows.append({"metric": f"review_lane:{lane}", "value": count, "notes": "Surface-level review lane distribution."})
    for decision, count in decision_counts.most_common():
        summary_rows.append({"metric": f"decision:{decision}", "value": count, "notes": "Surface-level review decision distribution."})
    for role, count in override_role_counts.most_common():
        summary_rows.append({"metric": f"draft_override_role:{role}", "value": count, "notes": "Draft override role distribution."})

    write_csv(OUT_REVIEW, review_rows, REVIEW_FIELDS)
    write_csv(OUT_OVERRIDES, overrides, OVERRIDE_FIELDS)
    write_csv(OUT_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_report(summary_rows, review_rows, overrides)

    print(f"packets_scanned={len(packets)}")
    print(f"review_queue_rows={len(review_rows)}")
    print(f"draft_override_rows={len(overrides)}")
    print(f"wrote {OUT_REVIEW.relative_to(ROOT)}")
    print(f"wrote {OUT_OVERRIDES.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
