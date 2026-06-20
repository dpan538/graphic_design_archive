#!/usr/bin/env python3
"""Initial role review for the main/sub/text validation packet.

This is a non-mutating method review. It does not apply overrides, rebuild
payloads, download images, or change rights/image states.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

IN_PACKET = DATA / "prefreeze_main_sub_text_method_validation_packet_v1.csv"

OUT_REVIEW = DATA / "prefreeze_main_sub_text_initial_role_review_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_main_sub_text_initial_role_review_summary_v1.csv"
OUT_SANDBOX_CANDIDATES = DATA / "prefreeze_main_sub_text_sandbox_candidate_pool_v1.csv"
OUT_CALIBRATION_QUEUE = DATA / "prefreeze_main_sub_text_manual_calibration_queue_v1.csv"
OUT_REPORT = DOCS / "MAIN_SUB_TEXT_INITIAL_ROLE_REVIEW_v1.md"
OUT_GATE = DOCS / "MAIN_SUB_TEXT_SANDBOX_GATE_v1.md"
OUT_CALIBRATION_REPORT = DOCS / "MAIN_SUB_TEXT_MANUAL_CALIBRATION_QUEUE_v1.md"

REVIEW_FIELDS = [
    "validation_sample_id",
    "surface_id",
    "capture_id",
    "sample_target_marker",
    "year",
    "period",
    "region",
    "theme",
    "medium",
    "image_state",
    "source_name",
    "source_family",
    "title",
    "descriptive_unit",
    "recommended_role",
    "parent_candidate",
    "relation_type",
    "text_need_level",
    "blocker_class",
    "review_result",
    "review_confidence",
    "generalizable_rule",
    "method_risk_flags",
    "role_rationale",
    "review_status",
    "reviewer_notes",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]

SANDBOX_FIELDS = [
    "validation_sample_id",
    "surface_id",
    "capture_id",
    "recommended_role",
    "parent_candidate",
    "relation_type",
    "review_confidence",
    "generalizable_rule",
    "role_rationale",
    "sandbox_status",
    "sandbox_blocker",
]

CALIBRATION_FIELDS = [
    *REVIEW_FIELDS,
    "calibration_priority",
    "calibration_group",
    "calibration_question",
]

MANUAL_BLOCKER_FLAGS = {
    "transnational_region",
    "unresolved_region_or_theme",
    "stamp_or_philatelic",
    "event_photo_context",
    "natural_history_geology",
}


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


def flag_set(row: dict[str, str]) -> set[str]:
    return {clean(flag) for flag in clean(row.get("method_risk_flags")).split(";") if clean(flag)}


def text_blob(row: dict[str, str]) -> str:
    return " ".join(
        clean(row.get(key))
        for key in ("title", "source_name", "source_family", "theme", "medium", "main_anchor_reason")
    ).casefold()


def has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def is_control_evidence_record(row: dict[str, str]) -> bool:
    text = " ".join(
        clean(row.get(key))
        for key in ("title", "medium", "theme", "main_anchor_reason")
    ).casefold()
    return has_any(
        text,
        (
            "rights evidence",
            "source statement",
            "typed index",
            "api verification",
            "source index",
            "metadata verification",
            "provenance note",
        ),
    )


def is_stampish(row: dict[str, str]) -> bool:
    text = text_blob(row)
    return bool(
        re.search(r"(?<![a-z0-9])(stamp|postage|philatelic|seebeck|sc\d+|mi\s?nr|minr\d+)(?![a-z0-9])", text)
    )


def descriptive_unit(row: dict[str, str], flags: set[str]) -> str:
    marker = clean(row.get("sample_target_marker"))
    text = text_blob(row)
    if "natural_history_geology" in flags:
        return "false_positive_candidate"
    if is_control_evidence_record(row):
        return "evidence_record"
    if "stamp_or_philatelic" in flags or is_stampish(row):
        return "commemorative_source_witness"
    if "event_photo_context" in flags:
        return "event_context_witness"
    if has_any(text, ("journal", "magazine", "periodical", "issue", "newspaper", "gazette")):
        return "periodical_or_issue"
    if as_int(row.get("cluster_size")) >= 5:
        return "source_cluster_member"
    if marker in {"strong_soft_anchor", "anchor_if_editorial_text_added"}:
        return "work_or_packet_anchor_candidate"
    if marker == "packet_anchor_or_member_review":
        return "packet_member_or_anchor_candidate"
    if "commons_file_source" in flags:
        return "image_file_source_witness"
    return "work_record_candidate"


def blocker_class(row: dict[str, str], flags: set[str]) -> str:
    blockers: list[str] = []
    if "natural_history_geology" in flags:
        blockers.append("natural_history_geology_false_positive")
    if "stamp_or_philatelic" in flags or is_stampish(row):
        blockers.append("stamp_or_commemorative_manual")
    if "event_photo_context" in flags:
        blockers.append("event_photo_memory_manual")
    if "unresolved_region_or_theme" in flags:
        blockers.append("unresolved_region_or_theme_manual")
    if "transnational_region" in flags:
        blockers.append("transnational_geography_manual")
    if "commons_file_source" in flags and as_int(row.get("source_reading_text_length")) < 250:
        blockers.append("weak_commons_only_manual")
    if as_int(row.get("cluster_size")) >= 10:
        blockers.append("large_cluster_parentage_review")
    if not blockers:
        blockers.append("none")
    return "; ".join(blockers)


def text_need_level(row: dict[str, str], flags: set[str], role: str) -> str:
    if role in {"appendix_evidence", "exclude_or_deprioritize"}:
        return "none"
    points = 0
    if as_int(row.get("cluster_size")) >= 3:
        points += 1
    if as_int(row.get("cluster_size")) >= 10:
        points += 1
    if "transnational_region" in flags or "unresolved_region_or_theme" in flags:
        points += 1
    if "commons_file_source" in flags:
        points += 1
    if clean(row.get("period")) in {"pre_1850", "1850_1899", "1914_1945", "2020_2026"}:
        points += 1
    if role == "main_needs_text":
        points += 1
    if role == "keep_main" and as_int(row.get("source_reading_text_length")) < 250:
        points += 1
    if points <= 0:
        return "none"
    if points <= 2:
        return "low"
    if points <= 4:
        return "medium"
    return "high"


def parent_candidate(row: dict[str, str], role: str) -> str:
    if role in {"sub_under_packet", "card_context", "appendix_evidence"}:
        return clean(row.get("cluster_key")) or "manual_parent_needed"
    if role == "main_needs_text":
        return clean(row.get("surface_id"))
    return ""


def relation_type(row: dict[str, str], role: str, unit: str) -> str:
    if role == "appendix_evidence":
        return "evidence_for_packet"
    if role == "card_context":
        if unit == "event_context_witness":
            return "context_for_packet"
        if unit == "commemorative_source_witness":
            return "commemorative_context_for_packet"
        return "context_or_source_witness_for_packet"
    if role == "sub_under_packet":
        if unit == "periodical_or_issue":
            return "issue_or_periodical_member_of_packet"
        if unit == "source_cluster_member":
            return "member_of_source_cluster_packet"
        return "member_of_packet"
    if role == "main_needs_text":
        return "packet_anchor_requires_text"
    if role == "keep_main":
        return "packet_anchor"
    return "manual_relation_review"


def role_review(row: dict[str, str]) -> dict[str, str]:
    flags = flag_set(row)
    marker = clean(row.get("sample_target_marker"))
    text = text_blob(row)
    unit = descriptive_unit(row, flags)
    blockers = blocker_class(row, flags)
    manual_blocked = any(flag in flags for flag in MANUAL_BLOCKER_FLAGS)

    role = "manual_hold"
    confidence = "low"
    result = "revise"
    rule = "manual_hold_for_ambiguous_packet_role"
    rationale = "Metadata is insufficient for safe structural assignment without parent or blocker review."

    if unit == "false_positive_candidate":
        role = "exclude_or_deprioritize"
        confidence = "high"
        result = "pass"
        rule = "natural_history_or_geology_false_positive_is_not_graphic_design_main"
        rationale = "Natural-history/geology drift should not carry main-sheet authority in a graphic design archive."
    elif unit == "evidence_record":
        role = "appendix_evidence"
        confidence = "high"
        result = "pass"
        rule = "source_or_rights_control_material_goes_to_appendix"
        rationale = "The record primarily verifies source, rights, API, index, or provenance evidence."
    elif "stamp_or_philatelic" in flags or is_stampish(row):
        role = "card_context"
        confidence = "medium"
        result = "revise"
        rule = "stamp_or_commemorative_record_is_manual_card_candidate"
        rationale = "Commemorative/philatelic material may be useful context but should not become main without design-specific justification."
    elif "event_photo_context" in flags:
        role = "card_context"
        confidence = "medium"
        result = "revise"
        rule = "event_or_memory_photo_is_card_context_by_default"
        rationale = "Event/memory documentation is useful context but normally lacks packet-anchor force."
    elif marker == "strong_soft_anchor":
        if manual_blocked:
            role = "manual_hold"
            confidence = "medium"
            result = "revise"
            rule = "strong_anchor_with_blocker_requires_manual_review"
            rationale = "The row has anchor signals but also a blocker that could cause rights, geography, or source-family overclaiming."
        elif as_int(row.get("source_reading_text_length")) >= 250:
            role = "keep_main"
            confidence = "medium"
            result = "pass"
            rule = "strong_soft_anchor_can_remain_main_after_review"
            rationale = "The row has strong anchor marker and enough source text for provisional main status."
        else:
            role = "main_needs_text"
            confidence = "medium"
            result = "revise"
            rule = "strong_anchor_with_thin_source_needs_text"
            rationale = "The row may remain main, but thin source text requires interpretive support."
    elif marker == "anchor_if_editorial_text_added":
        role = "main_needs_text" if not manual_blocked else "manual_hold"
        confidence = "medium" if not manual_blocked else "low"
        result = "pass" if not manual_blocked else "revise"
        rule = "editorial_text_needed_before_anchor_publication"
        rationale = "The row can only function as main if a non-filler text sheet explains packet scope and evidence."
    elif marker == "packet_anchor_or_member_review":
        if manual_blocked:
            role = "manual_hold"
            confidence = "low"
            result = "revise"
            rule = "packet_anchor_or_member_with_blocker_requires_manual_review"
            rationale = "Parent/member status is visible but blocked by geography, source, event, stamp, or false-positive risk."
        elif as_int(row.get("cluster_size")) >= 2:
            role = "sub_under_packet"
            confidence = "medium"
            result = "pass"
            rule = "packet_member_with_cluster_can_be_sub_candidate"
            rationale = "The row has a visible cluster relation and should be tested as packet member before main retention."
        else:
            role = "manual_hold"
            confidence = "low"
            result = "revise"
            rule = "packet_member_needs_parent_before_role_change"
            rationale = "The row may be packet member, but no reliable parent relation is available from metadata."
    elif marker == "support_or_card_review":
        if manual_blocked:
            role = "card_context" if "natural_history_geology" not in flags else "exclude_or_deprioritize"
            confidence = "medium"
            result = "revise"
            rule = "support_card_with_blocker_stays_manual_or_card"
            rationale = "The row should not carry main authority, but blocker type requires human confirmation before application."
        elif is_control_evidence_record(row):
            role = "appendix_evidence"
            confidence = "high"
            result = "pass"
            rule = "support_source_control_record_can_be_appendix_candidate"
            rationale = "Support material with source/control language is better treated as appendix evidence."
        else:
            role = "card_context"
            confidence = "high"
            result = "pass"
            rule = "support_or_card_review_without_blocker_can_be_card_candidate"
            rationale = "The row is already in support/card review and lacks blockers that would require manual hold."
    elif marker == "soft_anchor_review":
        if manual_blocked:
            role = "manual_hold"
            confidence = "low"
            result = "revise"
            rule = "soft_anchor_with_blocker_requires_manual_review"
            rationale = "The row may be anchor-worthy, but blocker risk prevents automatic role assignment."
        elif as_int(row.get("cluster_size")) >= 5:
            role = "sub_under_packet"
            confidence = "medium"
            result = "revise"
            rule = "soft_anchor_in_large_cluster_needs_parent_review"
            rationale = "Large cluster membership suggests packet relation, but parent selection remains unresolved."
        elif as_int(row.get("source_reading_text_length")) >= 600:
            role = "main_needs_text"
            confidence = "medium"
            result = "pass"
            rule = "soft_anchor_with_source_depth_can_be_main_needs_text"
            rationale = "Source depth supports anchor potential, but the main claim needs interpretive text."
        else:
            role = "manual_hold"
            confidence = "low"
            result = "revise"
            rule = "soft_anchor_without_depth_or_parent_stays_manual"
            rationale = "The row lacks enough source depth or parent relation for safe assignment."

    text_level = text_need_level(row, flags, role)
    return {
        "descriptive_unit": unit,
        "recommended_role": role,
        "parent_candidate": parent_candidate(row, role),
        "relation_type": relation_type(row, role, unit),
        "text_need_level": text_level,
        "blocker_class": blockers,
        "review_result": result,
        "review_confidence": confidence,
        "generalizable_rule": rule,
        "role_rationale": rationale,
    }


def reviewed_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    reviewed: list[dict[str, object]] = []
    for row in rows:
        review = role_review(row)
        reviewed.append({**row, **review})
    return reviewed


def sandbox_candidates(reviewed: list[dict[str, object]]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for row in reviewed:
        role = clean(row.get("recommended_role"))
        confidence = clean(row.get("review_confidence"))
        blockers = clean(row.get("blocker_class"))
        result = clean(row.get("review_result"))
        eligible_role = role in {"appendix_evidence", "card_context", "sub_under_packet"}
        high_enough = confidence == "high"
        no_blocker = blockers == "none"
        pass_result = result == "pass"
        parent_ok = role != "sub_under_packet" or clean(row.get("parent_candidate"))
        if eligible_role and high_enough and no_blocker and pass_result and parent_ok:
            status = "candidate_pool_only"
            blocker = "not_apply_ready_until_manual_calibration_passes"
        else:
            continue
        candidates.append(
            {
                "validation_sample_id": row.get("validation_sample_id"),
                "surface_id": row.get("surface_id"),
                "capture_id": row.get("capture_id"),
                "recommended_role": role,
                "parent_candidate": row.get("parent_candidate"),
                "relation_type": row.get("relation_type"),
                "review_confidence": confidence,
                "generalizable_rule": row.get("generalizable_rule"),
                "role_rationale": row.get("role_rationale"),
                "sandbox_status": status,
                "sandbox_blocker": blocker,
            }
        )
    return candidates


def calibration_group(row: dict[str, object]) -> str:
    blockers = [blocker for blocker in clean(row.get("blocker_class")).split("; ") if blocker and blocker != "none"]
    if blockers:
        return blockers[0]
    role = clean(row.get("recommended_role"))
    marker = clean(row.get("sample_target_marker"))
    if role in {"keep_main", "main_needs_text", "sub_under_packet", "manual_hold"}:
        return f"main_sensitive:{marker}:{role}"
    return f"support:{role}"


def calibration_priority(row: dict[str, object]) -> int:
    score = 0
    role = clean(row.get("recommended_role"))
    marker = clean(row.get("sample_target_marker"))
    blockers = clean(row.get("blocker_class"))
    if blockers != "none":
        score += 30
    if role in {"keep_main", "main_needs_text", "sub_under_packet"}:
        score += 25
    if role == "manual_hold":
        score += 20
    if marker in {"strong_soft_anchor", "anchor_if_editorial_text_added", "packet_anchor_or_member_review"}:
        score += 15
    if clean(row.get("review_confidence")) == "low":
        score += 8
    if clean(row.get("review_result")) == "revise":
        score += 5
    return score


def calibration_question(row: dict[str, object]) -> str:
    role = clean(row.get("recommended_role"))
    blockers = clean(row.get("blocker_class"))
    if blockers != "none":
        return "Does this blocker require manual-only handling, or can the role rule be safely narrowed?"
    if role == "keep_main":
        return "Does this row truly anchor a research packet, or is it only an object page?"
    if role == "main_needs_text":
        return "Would a non-filler text sheet make this a valid main anchor?"
    if role == "sub_under_packet":
        return "Is the parent packet and relation type explicit enough for sub status?"
    if role == "card_context":
        return "Would moving this to card hide any significant research path?"
    return "Is the recommended role reproducible from the available evidence?"


def calibration_queue(reviewed: list[dict[str, object]], target: int = 80) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in reviewed:
        enriched = {
            **row,
            "calibration_priority": calibration_priority(row),
            "calibration_group": calibration_group(row),
            "calibration_question": calibration_question(row),
        }
        grouped.setdefault(clean(enriched["calibration_group"]), []).append(enriched)

    for group_rows in grouped.values():
        group_rows.sort(
            key=lambda row: (
                -as_int(row.get("calibration_priority")),
                clean(row.get("sample_target_marker")),
                clean(row.get("validation_sample_id")),
            )
        )

    selected: list[dict[str, object]] = []
    seen: set[str] = set()
    groups = sorted(grouped, key=lambda key: (-max(as_int(row.get("calibration_priority")) for row in grouped[key]), key))
    while len(selected) < target and groups:
        progressed = False
        for group in groups:
            while grouped[group]:
                row = grouped[group].pop(0)
                surface_id = clean(row.get("surface_id"))
                if surface_id not in seen:
                    selected.append(row)
                    seen.add(surface_id)
                    progressed = True
                    break
            if len(selected) >= target:
                break
        groups = [group for group in groups if grouped[group]]
        if not progressed:
            break
    selected.sort(key=lambda row: (clean(row.get("calibration_group")), clean(row.get("validation_sample_id"))))
    return selected


def summary_rows(
    reviewed: list[dict[str, object]],
    candidates: list[dict[str, object]],
    calibration: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [
        {"metric": "review_scope", "value": "initial_codex_method_review", "notes": "Non-mutating first-pass review from validation packet metadata."},
        {"metric": "validation_rows_reviewed", "value": len(reviewed), "notes": "Rows reviewed from the 320-row packet."},
        {"metric": "sandbox_candidate_pool_rows", "value": len(candidates), "notes": "High-confidence candidate pool only; not apply-ready without manual calibration."},
        {"metric": "manual_calibration_queue_rows", "value": len(calibration), "notes": "Deterministic 25% queue for calibration before any sandbox override."},
        {"metric": "sandbox_gate_status", "value": "not_ready_for_override", "notes": "Manual calibration and reviewer agreement have not happened yet."},
    ]
    for key in ("recommended_role", "review_result", "review_confidence", "text_need_level", "sample_target_marker"):
        for value, count in Counter(clean(row.get(key)) for row in reviewed).most_common():
            rows.append({"metric": f"{key}:{value}", "value": count, "notes": f"Distribution by {key}."})
    blocker_counter: Counter[str] = Counter()
    for row in reviewed:
        for blocker in clean(row.get("blocker_class")).split("; "):
            if blocker:
                blocker_counter[blocker] += 1
    for blocker, count in blocker_counter.most_common():
        rows.append({"metric": f"blocker_class:{blocker}", "value": count, "notes": "Method blocker distribution."})
    for role, count in Counter(clean(row.get("recommended_role")) for row in candidates).most_common():
        rows.append({"metric": f"sandbox_candidate_role:{role}", "value": count, "notes": "Candidate pool role distribution."})
    for group, count in Counter(clean(row.get("calibration_group")) for row in calibration).most_common():
        rows.append({"metric": f"calibration_group:{group}", "value": count, "notes": "Manual calibration queue distribution."})
    return rows


def write_report(
    reviewed: list[dict[str, object]],
    candidates: list[dict[str, object]],
    calibration: list[dict[str, object]],
    summary: list[dict[str, object]],
) -> None:
    role_counts = Counter(clean(row.get("recommended_role")) for row in reviewed)
    result_counts = Counter(clean(row.get("review_result")) for row in reviewed)
    confidence_counts = Counter(clean(row.get("review_confidence")) for row in reviewed)
    blocker_counts: Counter[str] = Counter()
    for row in reviewed:
        for blocker in clean(row.get("blocker_class")).split("; "):
            if blocker and blocker != "none":
                blocker_counts[blocker] += 1
    lines = [
        "# Main/Sub/Text Initial Role Review v1",
        "",
        "Scope: first-pass method review of the 320-row validation packet.",
        "",
        "This pass does not rebuild surfaces, does not apply role overrides, does not download images, and does not change rights or image states.",
        "",
        "## Result",
        "",
        f"- Rows reviewed: {len(reviewed)}.",
        f"- Sandbox candidate-pool rows: {len(candidates)}.",
        f"- Manual calibration queue rows: {len(calibration)}.",
        "- Sandbox gate: not ready for override because manual calibration and reviewer agreement have not happened yet.",
        "",
        "## Recommended Role Distribution",
        "",
    ]
    for role, count in role_counts.most_common():
        lines.append(f"- `{role}`: {count}.")
    lines.extend(["", "## Review Result Distribution", ""])
    for result, count in result_counts.most_common():
        lines.append(f"- `{result}`: {count}.")
    lines.extend(["", "## Confidence Distribution", ""])
    for confidence, count in confidence_counts.most_common():
        lines.append(f"- `{confidence}`: {count}.")
    lines.extend(["", "## Main Blockers", ""])
    for blocker, count in blocker_counts.most_common():
        lines.append(f"- `{blocker}`: {count}.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The initial review can identify likely support/card and manual-hold lanes, but it is not a substitute for human method calibration.",
            "- High-confidence automation remains intentionally narrow and is limited to candidate-pool rows, not applied overrides.",
            "- Main retention remains conservative: keep-main and main-needs-text decisions should stay human-confirmed until the validation packet has calibrated review.",
            "- Records with geography, event/photo, stamp, weak Commons-only, large-cluster, or false-positive signals remain manual-first.",
            "",
            "## Next Step",
            "",
            "Manually calibrate the 80-row queue, including all blocker classes and all main-sensitive lanes. If agreement is near 80% and fail patterns stay below 10%, convert a small subset of the candidate pool into a sandbox override test.",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_gate(candidates: list[dict[str, object]], summary: list[dict[str, object]]) -> None:
    lines = [
        "# Main/Sub/Text Sandbox Gate v1",
        "",
        "Gate status: **not ready for override**.",
        "",
        "Reason: the initial Codex review is a methodology pass over metadata. It has not yet been manually calibrated, and no reviewer-agreement threshold has been measured.",
        "",
        "## Candidate Pool",
        "",
        f"- Candidate-pool rows: {len(candidates)}.",
        "- These rows are not apply-ready. They are the only rows eligible for later small sandbox conversion after calibration.",
        "",
        "## Required Before Sandbox Override",
        "",
        "- Review at least 25% of the 320-row packet.",
        "- Target about 80% role agreement.",
        "- Keep method fail at or below 10%.",
        "- Pause if failure patterns show rights/image inference, geography unfairness, source-family bias, event/photo confusion, stamp overclaiming, or duplicate/variant mistakes.",
        "",
        "## Permitted Future Sandbox Scope",
        "",
        "- High-confidence `appendix_evidence` rows.",
        "- High-confidence `card_context` rows.",
        "- High-confidence `sub_under_packet` rows only when parent and relation type are explicit.",
        "",
        "## Not Permitted Yet",
        "",
        "- Broad keep-main decisions.",
        "- Any rights or image-state upgrade.",
        "- Contested geography normalization.",
        "- Bulk main demotion.",
        "- Any official payload or frontend rebuild.",
    ]
    OUT_GATE.parent.mkdir(parents=True, exist_ok=True)
    OUT_GATE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_calibration_report(calibration: list[dict[str, object]]) -> None:
    group_counts = Counter(clean(row.get("calibration_group")) for row in calibration)
    role_counts = Counter(clean(row.get("recommended_role")) for row in calibration)
    lines = [
        "# Main/Sub/Text Manual Calibration Queue v1",
        "",
        "Scope: deterministic 80-row queue for calibrating the initial method review before any sandbox override.",
        "",
        "This queue does not apply overrides, rebuild surfaces, download images, or change rights/image states.",
        "",
        "## Queue Size",
        "",
        f"- Calibration rows: {len(calibration)}.",
        "- This is 25% of the 320-row validation packet.",
        "",
        "## Role Spread",
        "",
    ]
    for role, count in role_counts.most_common():
        lines.append(f"- `{role}`: {count}.")
    lines.extend(["", "## Calibration Groups", ""])
    for group, count in group_counts.most_common():
        lines.append(f"- `{group}`: {count}.")
    lines.extend(
        [
            "",
            "## How To Use",
            "",
            "- Review each row's recommended role, blocker class, relation type, and text need.",
            "- Mark whether the role is accepted, revised, or rejected.",
            "- Track recurring failure patterns rather than treating each row as isolated.",
            "- Do not create a sandbox override until the queue shows stable agreement.",
        ]
    )
    OUT_CALIBRATION_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_CALIBRATION_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    packet = read_csv(IN_PACKET)
    reviewed = reviewed_rows(packet)
    candidates = sandbox_candidates(reviewed)
    calibration = calibration_queue(reviewed)
    summary = summary_rows(reviewed, candidates, calibration)
    write_csv(OUT_REVIEW, reviewed, REVIEW_FIELDS)
    write_csv(OUT_SUMMARY, summary, SUMMARY_FIELDS)
    write_csv(OUT_SANDBOX_CANDIDATES, candidates, SANDBOX_FIELDS)
    write_csv(OUT_CALIBRATION_QUEUE, calibration, CALIBRATION_FIELDS)
    write_report(reviewed, candidates, calibration, summary)
    write_gate(candidates, summary)
    write_calibration_report(calibration)
    print(f"reviewed_rows={len(reviewed)}")
    print(f"sandbox_candidate_pool_rows={len(candidates)}")
    print(f"manual_calibration_queue_rows={len(calibration)}")
    print("sandbox_gate_status=not_ready_for_override")
    print(f"wrote {OUT_REVIEW.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_SANDBOX_CANDIDATES.relative_to(ROOT)}")
    print(f"wrote {OUT_CALIBRATION_QUEUE.relative_to(ROOT)}")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")
    print(f"wrote {OUT_GATE.relative_to(ROOT)}")
    print(f"wrote {OUT_CALIBRATION_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
