#!/usr/bin/env python3
"""Second-pass calibration for the main/sub/text method review.

This script reads the 80-row manual calibration queue and enriches it with the
prefreeze candidate payload. It does not apply overrides, rebuild surfaces,
download images, or change rights/image states.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
PAYLOAD = ROOT / "generated" / "public_surfaces_prefreeze_candidate_v1.json"

IN_QUEUE = DATA / "prefreeze_main_sub_text_manual_calibration_queue_v1.csv"
IN_CANDIDATES = DATA / "prefreeze_main_sub_text_sandbox_candidate_pool_v1.csv"

OUT_CALIBRATION = DATA / "prefreeze_main_sub_text_calibration_second_pass_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_main_sub_text_calibration_second_pass_summary_v1.csv"
OUT_CONFIRMED_CANDIDATES = DATA / "prefreeze_main_sub_text_sandbox_candidate_confirmed_preview_v1.csv"
OUT_REPORT = DOCS / "MAIN_SUB_TEXT_CALIBRATION_SECOND_PASS_v1.md"
OUT_GATE = DOCS / "MAIN_SUB_TEXT_SANDBOX_GATE_SECOND_PASS_v1.md"

FIELDS = [
    "validation_sample_id",
    "surface_id",
    "capture_id",
    "sample_target_marker",
    "title",
    "period",
    "region",
    "theme",
    "source_family",
    "image_state",
    "initial_recommended_role",
    "second_pass_role",
    "second_pass_decision",
    "second_pass_confidence",
    "second_pass_fail_pattern",
    "second_pass_reason",
    "parent_candidate",
    "second_pass_parent_status",
    "relation_type",
    "text_need_level",
    "second_pass_text_status",
    "blocker_class",
    "payload_surface_disposition",
    "payload_publication_role",
    "payload_object_type",
    "payload_medium",
    "payload_place_text",
    "payload_source_reading_text_length",
    "payload_reading_text_length",
    "payload_source_url",
    "source_context_excerpt",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]

CONFIRMED_FIELDS = [
    "validation_sample_id",
    "surface_id",
    "capture_id",
    "confirmed_role",
    "parent_candidate",
    "relation_type",
    "second_pass_confidence",
    "second_pass_reason",
    "preview_status",
]


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def as_int(value: object) -> int:
    try:
        return int(float(str(value or "0")))
    except ValueError:
        return 0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_payload_index(surface_ids: set[str]) -> dict[str, dict]:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    index: dict[str, dict] = {}
    for surface in payload.get("surfaces", []):
        surface_id = clean(surface.get("surfaceId"))
        if surface_id in surface_ids:
            index[surface_id] = surface
    return index


def payload_text(surface: dict) -> str:
    return " ".join(
        clean(surface.get(key))
        for key in (
            "title",
            "sourceName",
            "sourceDescription",
            "descriptionSummary",
            "historicalContextNote",
            "classificationRationale",
            "objectType",
            "medium",
            "placeText",
            "sourceSubjects",
        )
    )


def has_stamp_signal(text: str) -> bool:
    folded = text.casefold()
    return bool(
        re.search(r"(?<![a-z0-9])(stamp|postage|philatelic|seebeck|sc\d+|mi\s?nr|minr\d+|colnect)(?![a-z0-9])", folded)
    )


def has_event_signal(text: str) -> bool:
    folded = text.casefold()
    return bool(
        re.search(r"(?<![a-z0-9])(event photo|conference|session|ceremony|anniversary|inauguration|reception)(?![a-z0-9])", folded)
    )


def has_false_positive_signal(text: str) -> bool:
    folded = text.casefold()
    return bool(
        re.search(r"(?<![a-z0-9])(natural history|geology|geological|fossil|mineral)(?![a-z0-9])", folded)
    )


def has_design_object_signal(text: str) -> bool:
    folded = text.casefold()
    return bool(
        re.search(
            r"(?<![a-z0-9])(poster|trade card|advertisement|advertising|typography|type|print|lithograph|wood engraving|periodical|journal|magazine|cover|brochure|catalogue|label)(?![a-z0-9])",
            folded,
        )
    )


def has_control_evidence_signal(text: str) -> bool:
    folded = text.casefold()
    return any(
        term in folded
        for term in (
            "rights evidence",
            "source statement",
            "typed index",
            "source index",
            "api verification",
            "metadata verification",
            "provenance note",
        )
    )


def blocker_set(row: dict[str, str]) -> set[str]:
    return {clean(value) for value in clean(row.get("blocker_class")).split("; ") if clean(value) and clean(value) != "none"}


def parent_status(row: dict[str, str]) -> str:
    parent = clean(row.get("parent_candidate"))
    role = clean(row.get("recommended_role"))
    if role != "sub_under_packet":
        return "not_required"
    if not parent:
        return "missing_parent"
    if "|" in parent:
        return "cluster_key_parent_needs_named_anchor"
    return "explicit_parent_candidate"


def second_pass(row: dict[str, str], surface: dict) -> dict[str, object]:
    initial_role = clean(row.get("recommended_role"))
    blockers = blocker_set(row)
    text = payload_text(surface)
    source_len = as_int(surface.get("sourceReadingTextLength") or row.get("source_reading_text_length"))
    reading_len = as_int(surface.get("readingTextLength") or row.get("reading_text_length"))
    cluster_size = as_int(row.get("cluster_size"))
    marker = clean(row.get("sample_target_marker"))
    parent_state = parent_status(row)

    role = initial_role
    decision = "accept_initial"
    confidence = "medium"
    fail_pattern = "none"
    reason = "The enriched payload supports the initial role recommendation."

    if has_false_positive_signal(text):
        if has_design_object_signal(text):
            role = "card_context"
            confidence = "medium"
            fail_pattern = "natural_history_topic_design_object_context"
            reason = "Payload contains natural-history/geology topic language, but also poster/advertising/design-object evidence; keep as card context rather than main or exclusion."
        else:
            role = "exclude_or_deprioritize"
            confidence = "high"
            fail_pattern = "false_positive_or_non_design_context"
            reason = "Payload context contains natural-history, geology, fossil, or mineral signals without enough design-object evidence."
        decision = "accept_initial" if initial_role == role else "revise_initial"
    elif has_stamp_signal(text):
        role = "card_context"
        confidence = "high"
        fail_pattern = "stamp_or_commemorative_context"
        reason = "Payload/title contains stamp or philatelic signals; treat as contextual design evidence unless manually justified as a primary design object."
        decision = "accept_initial" if initial_role == role else "revise_initial"
    elif has_control_evidence_signal(text):
        role = "appendix_evidence"
        confidence = "high"
        fail_pattern = "evidence_control_material"
        reason = "Payload contains explicit source/rights/index/API/provenance control language."
        decision = "accept_initial" if initial_role == role else "revise_initial"
    elif initial_role == "keep_main":
        if blockers:
            role = "manual_hold"
            confidence = "medium"
            fail_pattern = "main_with_blocker"
            reason = "A keep-main decision has blocker risk and needs manual confirmation."
            decision = "revise_initial"
        elif source_len >= 250 and reading_len >= 1500 and has_design_object_signal(text):
            confidence = "medium"
            reason = "Source and archive text support a provisional main anchor, but keep-main remains human-confirmed."
        else:
            role = "main_needs_text"
            confidence = "medium"
            fail_pattern = "main_anchor_needs_context"
            reason = "The row may remain anchor-worthy, but source/design evidence is not strong enough for keep-main without interpretive text."
            decision = "revise_initial"
    elif initial_role == "main_needs_text":
        if blockers:
            role = "manual_hold"
            confidence = "medium"
            fail_pattern = "main_needs_text_with_blocker"
            reason = "Text could help, but blocker risk must be resolved before anchor status."
            decision = "revise_initial"
        elif source_len >= 150 or reading_len >= 1500 or has_design_object_signal(text):
            confidence = "medium"
            reason = "Payload supports anchor potential, but text is required to avoid metadata-only main status."
        else:
            role = "manual_hold"
            confidence = "low"
            fail_pattern = "thin_source_no_anchor_support"
            reason = "Payload does not provide enough design/source context to justify main-needs-text yet."
            decision = "revise_initial"
    elif initial_role == "sub_under_packet":
        if parent_state == "missing_parent":
            role = "manual_hold"
            confidence = "low"
            fail_pattern = "missing_parent"
            reason = "Sub status requires a parent packet; no parent candidate is available."
            decision = "revise_initial"
        elif parent_state == "cluster_key_parent_needs_named_anchor":
            confidence = "medium"
            fail_pattern = "parent_needs_named_anchor"
            reason = "Cluster membership supports sub direction, but the parent must be converted from a cluster key into a named anchor before application."
            decision = "accept_initial"
        elif cluster_size >= 2 or has_design_object_signal(text):
            confidence = "medium"
            reason = "Payload and cluster evidence support member status, with parent relation still requiring confirmation."
        else:
            role = "manual_hold"
            confidence = "low"
            fail_pattern = "weak_sub_relation"
            reason = "Sub assignment is not reproducible from payload evidence."
            decision = "revise_initial"
    elif initial_role == "card_context":
        if has_design_object_signal(text) and not blockers and source_len >= 500 and marker != "support_or_card_review":
            role = "manual_hold"
            confidence = "medium"
            fail_pattern = "possible_underclassified_design_object"
            reason = "Payload has enough design-object signal that card status should be checked manually."
            decision = "revise_initial"
        else:
            confidence = "high" if not blockers else "medium"
            reason = "Payload supports context/support treatment without packet-anchor authority."
    elif initial_role == "manual_hold":
        if blockers:
            confidence = "high" if "unresolved_region_or_theme_manual" in blockers or "transnational_geography_manual" in blockers else "medium"
            reason = "Manual hold is confirmed by unresolved blocker risk."
        elif source_len >= 600 and has_design_object_signal(text):
            role = "main_needs_text"
            confidence = "medium"
            fail_pattern = "manual_hold_can_be_narrowed"
            reason = "Payload has enough design/source depth to test as main-needs-text rather than manual hold."
            decision = "revise_initial"
        else:
            confidence = "medium"
            reason = "Manual hold remains appropriate because the role is not reproducible enough for application."

    text_status = "not_required"
    if role == "main_needs_text":
        text_status = "required_before_main_publication"
    elif role == "keep_main":
        text_status = "recommended_for_anchor_explanation"
    elif role == "sub_under_packet":
        text_status = "inherited_from_parent_unless_local_caution"
    elif role == "card_context":
        text_status = "short_context_only"

    return {
        "second_pass_role": role,
        "second_pass_decision": decision,
        "second_pass_confidence": confidence,
        "second_pass_fail_pattern": fail_pattern,
        "second_pass_reason": reason,
        "second_pass_parent_status": parent_state,
        "second_pass_text_status": text_status,
    }


def enriched_rows(queue: list[dict[str, str]], payload_index: dict[str, dict]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in queue:
        surface = payload_index.get(clean(row.get("surface_id")), {})
        review = second_pass(row, surface)
        context_excerpt = clean(payload_text(surface))[:700].rstrip()
        rows.append(
            {
                "validation_sample_id": row.get("validation_sample_id"),
                "surface_id": row.get("surface_id"),
                "capture_id": row.get("capture_id"),
                "sample_target_marker": row.get("sample_target_marker"),
                "title": row.get("title"),
                "period": row.get("period"),
                "region": row.get("region"),
                "theme": row.get("theme"),
                "source_family": row.get("source_family"),
                "image_state": row.get("image_state"),
                "initial_recommended_role": row.get("recommended_role"),
                **review,
                "parent_candidate": row.get("parent_candidate"),
                "relation_type": row.get("relation_type"),
                "text_need_level": row.get("text_need_level"),
                "blocker_class": row.get("blocker_class"),
                "payload_surface_disposition": surface.get("surfaceDisposition", ""),
                "payload_publication_role": surface.get("publicationRole", ""),
                "payload_object_type": surface.get("objectType", ""),
                "payload_medium": surface.get("medium", ""),
                "payload_place_text": surface.get("placeText", ""),
                "payload_source_reading_text_length": surface.get("sourceReadingTextLength", ""),
                "payload_reading_text_length": surface.get("readingTextLength", ""),
                "payload_source_url": surface.get("sourceUrl", ""),
                "source_context_excerpt": context_excerpt,
            }
        )
    return rows


def confirmed_candidates(rows: list[dict[str, object]], candidate_ids: set[str]) -> list[dict[str, object]]:
    confirmed: list[dict[str, object]] = []
    for row in rows:
        if clean(row.get("surface_id")) not in candidate_ids:
            continue
        if clean(row.get("second_pass_decision")) != "accept_initial":
            continue
        if clean(row.get("second_pass_role")) not in {"card_context", "appendix_evidence", "sub_under_packet"}:
            continue
        confirmed.append(
            {
                "validation_sample_id": row.get("validation_sample_id"),
                "surface_id": row.get("surface_id"),
                "capture_id": row.get("capture_id"),
                "confirmed_role": row.get("second_pass_role"),
                "parent_candidate": row.get("parent_candidate"),
                "relation_type": row.get("relation_type"),
                "second_pass_confidence": row.get("second_pass_confidence"),
                "second_pass_reason": row.get("second_pass_reason"),
                "preview_status": "confirmed_preview_only_not_apply_ready",
            }
        )
    return confirmed


def summary_rows(rows: list[dict[str, object]], confirmed: list[dict[str, object]]) -> list[dict[str, object]]:
    agreement = sum(1 for row in rows if clean(row.get("second_pass_decision")) == "accept_initial")
    fail = sum(1 for row in rows if clean(row.get("second_pass_decision")) == "reject_initial")
    agreement_rate = agreement / len(rows) * 100 if rows else 0
    fail_rate = fail / len(rows) * 100 if rows else 0
    gate = "not_ready_for_override"
    if agreement_rate >= 80 and fail_rate <= 10 and confirmed:
        gate = "codex_calibrated_preview_only"
    summary: list[dict[str, object]] = [
        {"metric": "calibration_scope", "value": "codex_second_pass", "notes": "Second-pass review enriched with candidate payload; still non-mutating."},
        {"metric": "calibration_rows", "value": len(rows), "notes": "Rows in the manual calibration queue."},
        {"metric": "agreement_rows", "value": agreement, "notes": "Rows where second pass accepts the initial role."},
        {"metric": "agreement_rate", "value": f"{agreement_rate:.2f}%", "notes": "Accept-initial rows divided by calibration rows."},
        {"metric": "fail_rows", "value": fail, "notes": "Rows where second pass rejects the initial role outright."},
        {"metric": "fail_rate", "value": f"{fail_rate:.2f}%", "notes": "Reject-initial rows divided by calibration rows."},
        {"metric": "confirmed_candidate_preview_rows", "value": len(confirmed), "notes": "Candidate-pool rows confirmed by second pass; not apply-ready."},
        {"metric": "sandbox_gate_status", "value": gate, "notes": "No override is applied by this script."},
    ]
    for key in ("initial_recommended_role", "second_pass_role", "second_pass_decision", "second_pass_confidence", "second_pass_fail_pattern", "second_pass_parent_status"):
        for value, count in Counter(clean(row.get(key)) for row in rows).most_common():
            summary.append({"metric": f"{key}:{value}", "value": count, "notes": f"Second-pass distribution by {key}."})
    for role, count in Counter(clean(row.get("confirmed_role")) for row in confirmed).most_common():
        summary.append({"metric": f"confirmed_candidate_role:{role}", "value": count, "notes": "Confirmed preview role distribution."})
    return summary


def write_report(rows: list[dict[str, object]], confirmed: list[dict[str, object]], summary: list[dict[str, object]]) -> None:
    def metric(name: str) -> str:
        for row in summary:
            if row["metric"] == name:
                return str(row["value"])
        return ""

    role_counts = Counter(clean(row.get("second_pass_role")) for row in rows)
    decision_counts = Counter(clean(row.get("second_pass_decision")) for row in rows)
    fail_counts = Counter(clean(row.get("second_pass_fail_pattern")) for row in rows)
    lines = [
        "# Main/Sub/Text Calibration Second Pass v1",
        "",
        "Scope: Codex second-pass calibration over the 80-row queue, enriched with candidate payload context.",
        "",
        "This pass does not apply overrides, rebuild surfaces, download images, or change rights/image states.",
        "",
        "## Gate",
        "",
        f"- Agreement rate: {metric('agreement_rate')}.",
        f"- Fail rate: {metric('fail_rate')}.",
        f"- Confirmed candidate preview rows: {metric('confirmed_candidate_preview_rows')}.",
        f"- Sandbox gate status: `{metric('sandbox_gate_status')}`.",
        "",
        "The gate remains preview-only. A future override still needs an explicit sandbox apply step.",
        "",
        "## Second-Pass Role Distribution",
        "",
    ]
    for role, count in role_counts.most_common():
        lines.append(f"- `{role}`: {count}.")
    lines.extend(["", "## Decision Distribution", ""])
    for decision, count in decision_counts.most_common():
        lines.append(f"- `{decision}`: {count}.")
    lines.extend(["", "## Fail / Revision Patterns", ""])
    for pattern, count in fail_counts.most_common():
        lines.append(f"- `{pattern}`: {count}.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The second pass uses richer payload context to catch overbroad card/appendix/sub/main decisions.",
            "- Stamp, commemorative, geography, false-positive, and parent-selection issues remain manual-first.",
            "- Confirmed candidate rows are preview-only and should not be applied until the project explicitly creates a sandbox override layer.",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_gate(summary: list[dict[str, object]], confirmed: list[dict[str, object]]) -> None:
    value = {row["metric"]: row["value"] for row in summary}
    lines = [
        "# Main/Sub/Text Sandbox Gate Second Pass v1",
        "",
        f"Gate status: **{value.get('sandbox_gate_status')}**.",
        "",
        "This status means the method has a Codex-calibrated preview, not an applied or official role-change layer.",
        "",
        "## Second-Pass Metrics",
        "",
        f"- Calibration rows: {value.get('calibration_rows')}.",
        f"- Agreement rows: {value.get('agreement_rows')}.",
        f"- Agreement rate: {value.get('agreement_rate')}.",
        f"- Fail rows: {value.get('fail_rows')}.",
        f"- Fail rate: {value.get('fail_rate')}.",
        f"- Confirmed preview candidates: {len(confirmed)}.",
        "",
        "## Allowed Next Action",
        "",
        "- Create a small sandbox override preview only if the project accepts Codex second-pass calibration as sufficient.",
        "- Keep the override limited to confirmed candidate rows.",
        "- Run only a candidate rebuild, never official payload overwrite.",
        "",
        "## Still Forbidden",
        "",
        "- Bulk main demotion.",
        "- Rights or image-state upgrades.",
        "- Contested geography normalization.",
        "- Official payload or frontend rebuild.",
    ]
    OUT_GATE.parent.mkdir(parents=True, exist_ok=True)
    OUT_GATE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    queue = read_csv(IN_QUEUE)
    candidate_ids = {clean(row.get("surface_id")) for row in read_csv(IN_CANDIDATES)}
    payload_index = load_payload_index({clean(row.get("surface_id")) for row in queue})
    rows = enriched_rows(queue, payload_index)
    confirmed = confirmed_candidates(rows, candidate_ids)
    summary = summary_rows(rows, confirmed)

    write_csv(OUT_CALIBRATION, rows, FIELDS)
    write_csv(OUT_CONFIRMED_CANDIDATES, confirmed, CONFIRMED_FIELDS)
    write_csv(OUT_SUMMARY, summary, SUMMARY_FIELDS)
    write_report(rows, confirmed, summary)
    write_gate(summary, confirmed)

    print(f"calibration_rows={len(rows)}")
    print(f"confirmed_candidate_preview_rows={len(confirmed)}")
    for row in summary:
        if row["metric"] in {"agreement_rate", "fail_rate", "sandbox_gate_status"}:
            print(f"{row['metric']}={row['value']}")
    print(f"wrote {OUT_CALIBRATION.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_CONFIRMED_CANDIDATES.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")
    print(f"wrote {OUT_GATE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
