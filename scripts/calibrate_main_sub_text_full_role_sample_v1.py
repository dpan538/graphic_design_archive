#!/usr/bin/env python3
"""Calibrate the full main/sub/text role assessment sample.

This script reviews the 500-row full-role calibration sample with conservative,
auditable rules. It does not mutate surfaces, apply overrides, rebuild payloads,
download images, or change rights/image states.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"

IN_SAMPLE = DATA / "prefreeze_main_sub_text_full_role_calibration_sample_v1.csv"
OUT_CALIBRATION = DATA / "prefreeze_main_sub_text_full_role_calibration_v1.csv"
OUT_SUMMARY = DATA / "prefreeze_main_sub_text_full_role_calibration_summary_v1.csv"
OUT_SANDBOX_CANDIDATES = DATA / "prefreeze_main_sub_text_full_role_sandbox_candidates_v1.csv"
REPORT = DOCS / "MAIN_SUB_TEXT_FULL_ROLE_CALIBRATION_v1.md"

CALIBRATION_FIELDS = [
    "surface_id",
    "capture_id",
    "year",
    "period_band",
    "region",
    "theme",
    "source_family",
    "source_name",
    "title",
    "image_state",
    "recommended_next_action",
    "calibrated_action",
    "calibration_status",
    "calibration_confidence",
    "calibration_reason",
    "role_family",
    "source_text_chars",
    "overall_research_anchor_score",
    "source_depth_score",
    "relation_density_score",
    "text_depth_score",
    "design_object_confidence_score",
    "risk_pressure_score",
    "editorial_need_score",
    "risk_flags",
    "positive_flags",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]

SANDBOX_FIELDS = [
    "surface_id",
    "capture_id",
    "candidate_role",
    "recommended_next_action",
    "calibration_confidence",
    "calibration_reason",
    "preview_status",
    "source_family",
    "source_name",
    "title",
    "period_band",
    "region",
    "risk_flags",
    "positive_flags",
]


def clean(value: object) -> str:
    return str(value or "").strip()


def as_int(row: dict[str, str], key: str) -> int:
    try:
        return int(float(clean(row.get(key))))
    except ValueError:
        return 0


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def has_flag(row: dict[str, str], prefix: str) -> bool:
    return any(flag.startswith(prefix) for flag in clean(row.get("risk_flags")).split("; ") if flag)


def has_positive(row: dict[str, str], value: str) -> bool:
    return value in {flag for flag in clean(row.get("positive_flags")).split("; ") if flag}


def role_family(action: str) -> str:
    return {
        "downgrade_to_card_candidate": "card_context",
        "downgrade_to_sub_candidate": "sub_under_packet",
        "convert_to_text_or_appendix": "text_or_appendix",
        "keep_main_anchor": "main_anchor",
        "keep_main_add_text": "main_anchor_needs_text",
        "packet_anchor_review": "packet_relation_review",
        "manual_review": "manual_hold",
    }.get(action, "manual_hold")


def calibrate_row(row: dict[str, str]) -> tuple[str, str, str, str]:
    """Return calibrated_action, status, confidence, reason."""
    action = clean(row.get("recommended_next_action"))
    source_family = clean(row.get("source_family"))
    source_depth = as_int(row, "source_depth_score")
    relation = as_int(row, "relation_density_score")
    text_depth = as_int(row, "text_depth_score")
    design_conf = as_int(row, "design_object_confidence_score")
    risk = as_int(row, "risk_pressure_score")
    anchor = as_int(row, "overall_research_anchor_score")
    source_chars = as_int(row, "source_text_chars")
    editorial_need = as_int(row, "editorial_need_score")
    image = clean(row.get("image_state"))
    commons = source_family == "Wikimedia Commons"
    stamp = has_flag(row, "stamp_or_philatelic:")
    weak_context = has_flag(row, "weak_context:")
    drift = has_flag(row, "non_design_drift:")
    source_register = has_flag(row, "source_register:")
    design_positive = bool(clean(row.get("positive_flags")))
    poster_positive = has_positive(row, "poster") or has_positive(row, "film poster")
    advertising_positive = has_positive(row, "advertising") or has_positive(row, "advertisement")

    if action == "downgrade_to_card_candidate":
        if stamp:
            return action, "accepted_for_preview", "high", "Stamp/philatelic records should be card evidence unless manually justified as primary design objects."
        if weak_context or drift:
            return action, "accepted_for_preview", "high", "Context/photo or non-design drift flags support card treatment."
        if commons and source_chars < 260 and relation < 25:
            return action, "accepted_for_preview", "medium", "Thin Commons file-source record with weak relation density."
        if design_positive and risk < 25:
            return "manual_review", "revise_rule", "medium", "Design-positive low-risk row should not be auto-carded without human review."
        return action, "hold_for_manual", "medium", "Card direction is plausible but needs reviewer confirmation."

    if action == "downgrade_to_sub_candidate":
        if stamp and relation >= 50 and source_depth >= 75:
            return action, "accepted_for_preview", "medium", "Strong related stamp/philatelic cluster may work as a sub sheet under a packet anchor."
        if relation >= 45 and source_depth >= 55 and risk < 45:
            return action, "accepted_for_preview", "medium", "Relation density and source depth support sub-sheet treatment."
        if relation < 25:
            return "downgrade_to_card_candidate", "revise_rule", "medium", "Sub candidate lacks relation density; card review is safer."
        return action, "hold_for_manual", "medium", "Sub direction needs packet-parent confirmation."

    if action == "keep_main_anchor":
        if stamp or weak_context or drift:
            return "packet_anchor_review", "revise_rule", "medium", "Risk flags block default keep-main treatment."
        if source_depth >= 65 and design_conf >= 75 and risk <= 20 and source_chars >= 450:
            confidence = "medium" if commons else "high"
            return action, "accepted_for_method", confidence, "Enough source depth and design-object evidence for provisional main-anchor treatment."
        if poster_positive or advertising_positive:
            return "keep_main_add_text", "revise_rule", "medium", "Promising poster/advertising row still needs editorial text before main confirmation."
        return "packet_anchor_review", "revise_rule", "medium", "Keep-main signal is not strong enough after calibration."

    if action == "keep_main_add_text":
        if stamp or weak_context or drift:
            return "packet_anchor_review", "revise_rule", "medium", "Risk flags block default add-text main treatment."
        if editorial_need >= 20 and design_conf >= 55 and source_depth >= 35 and risk < 35:
            return action, "accepted_for_method", "medium", "Main status may be plausible if reviewed editorial text adds real research value."
        return "manual_review", "revise_rule", "medium", "Editorial need is not enough by itself to retain main status."

    if action == "packet_anchor_review":
        if relation >= 45 and source_depth >= 45 and risk < 45:
            return action, "accepted_for_method", "medium", "Packet relation review is appropriate before assigning main/sub/card structure."
        if risk >= 55:
            return "downgrade_to_card_candidate", "revise_rule", "medium", "High risk pressure should enter card review before packet anchoring."
        return action, "hold_for_manual", "medium", "Packet direction is plausible but lacks enough relation/source strength."

    if action == "convert_to_text_or_appendix":
        if image in {"IMG00", "IMG04"} or source_register:
            return action, "accepted_for_preview", "medium", "Source/register or no-image evidence is better handled as text/appendix."
        return "manual_review", "revise_rule", "medium", "Text/appendix conversion needs stronger source-register evidence."

    if action == "manual_review":
        if stamp:
            return "downgrade_to_card_candidate", "revise_rule", "medium", "Manual stamp row can safely start in card review."
        if anchor >= 60 and source_depth >= 60 and design_conf >= 70 and risk < 25:
            return "keep_main_add_text", "revise_rule", "medium", "Strong manual row should be tested as keep-main plus editorial text."
        return action, "accepted_for_method", "low", "Manual hold is appropriate because signals remain mixed."

    return "manual_review", "hold_for_manual", "low", "Unknown action; keep manual."


def sandbox_candidate_role(calibrated_action: str) -> str:
    return {
        "downgrade_to_card_candidate": "card_context",
        "downgrade_to_sub_candidate": "sub_under_packet",
        "convert_to_text_or_appendix": "text_or_appendix",
    }.get(calibrated_action, "")


def build_rows(source_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    calibration_rows: list[dict[str, Any]] = []
    sandbox_rows: list[dict[str, Any]] = []
    for row in source_rows:
        calibrated_action, status, confidence, reason = calibrate_row(row)
        out = {
            **{field: row.get(field, "") for field in CALIBRATION_FIELDS if field in row},
            "calibrated_action": calibrated_action,
            "calibration_status": status,
            "calibration_confidence": confidence,
            "calibration_reason": reason,
            "role_family": role_family(calibrated_action),
        }
        calibration_rows.append(out)
        candidate_role = sandbox_candidate_role(calibrated_action)
        if candidate_role and status == "accepted_for_preview":
            sandbox_rows.append(
                {
                    "surface_id": clean(row.get("surface_id")),
                    "capture_id": clean(row.get("capture_id")),
                    "candidate_role": candidate_role,
                    "recommended_next_action": clean(row.get("recommended_next_action")),
                    "calibration_confidence": confidence,
                    "calibration_reason": reason,
                    "preview_status": "confirmed_preview_only_not_apply_ready",
                    "source_family": clean(row.get("source_family")),
                    "source_name": clean(row.get("source_name")),
                    "title": clean(row.get("title")),
                    "period_band": clean(row.get("period_band")),
                    "region": clean(row.get("region")),
                    "risk_flags": clean(row.get("risk_flags")),
                    "positive_flags": clean(row.get("positive_flags")),
                }
            )
    return calibration_rows, sandbox_rows


def summary_rows(calibration_rows: list[dict[str, Any]], sandbox_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {"metric": "scope", "value": "non_mutating_calibration", "notes": "No rebuild, no role override, no image download, no rights/image-state change."},
        {"metric": "calibration_rows", "value": len(calibration_rows), "notes": "Rows reviewed from full-role calibration sample."},
        {"metric": "sandbox_candidate_rows", "value": len(sandbox_rows), "notes": "Preview-only rows accepted for a later sandbox override test."},
    ]
    for field, note in [
        ("calibration_status", "Calibration status distribution."),
        ("calibration_confidence", "Calibration confidence distribution."),
        ("recommended_next_action", "Original recommended action distribution."),
        ("calibrated_action", "Calibrated action distribution."),
        ("role_family", "Calibrated role family distribution."),
        ("source_family", "Source-family distribution."),
        ("period_band", "Period distribution."),
        ("region", "Region distribution."),
    ]:
        for value, count in Counter(clean(row.get(field)) for row in calibration_rows).most_common(30):
            rows.append({"metric": f"{field}:{value}", "value": count, "notes": note})
    for value, count in Counter(clean(row.get("candidate_role")) for row in sandbox_rows).most_common():
        rows.append({"metric": f"sandbox_candidate_role:{value}", "value": count, "notes": "Preview-only sandbox candidate role distribution."})
    return rows


def write_report(calibration_rows: list[dict[str, Any]], sandbox_rows: list[dict[str, Any]], summary: list[dict[str, Any]]) -> None:
    statuses = Counter(clean(row.get("calibration_status")) for row in calibration_rows)
    actions = Counter(clean(row.get("calibrated_action")) for row in calibration_rows)
    candidates = Counter(clean(row.get("candidate_role")) for row in sandbox_rows)
    source_families = Counter(clean(row.get("source_family")) for row in calibration_rows)
    lines = [
        "# Main/Sub/Text Full Role Calibration v1",
        "",
        "Scope: non-mutating calibration of the 500-row full-role sample.",
        "",
        "This pass does not apply overrides, rebuild payloads, download images, or change rights/image states.",
        "",
        "## Summary",
        "",
        f"- Calibration rows: {len(calibration_rows)}.",
        f"- Preview-only sandbox candidates: {len(sandbox_rows)}.",
    ]
    for status, count in statuses.most_common():
        lines.append(f"- `{status}`: {count}.")
    lines.extend(["", "## Calibrated Actions", ""])
    for action, count in actions.most_common():
        lines.append(f"- `{action}`: {count}.")
    lines.extend(["", "## Preview Candidate Roles", ""])
    for role, count in candidates.most_common():
        lines.append(f"- `{role}`: {count}.")
    lines.extend(["", "## Source-Family Bias", ""])
    for family, count in source_families.most_common(15):
        lines.append(f"- {family}: {count}.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The calibration confirms the direction of card treatment for stamp/philatelic and context/photo evidence.",
            "- Keep-main and keep-main-add-text actions are accepted as method signals only, not as release approval.",
            "- Packet-anchor review remains a relation-design task and should not be converted into overrides before parent/child rules are defined.",
            "- The sample remains Commons-heavy because the underlying candidate archive is Commons-heavy; this must remain visible in later validation.",
            "",
            "## Next Permitted Action",
            "",
            "Use `data/prefreeze_main_sub_text_full_role_sandbox_candidates_v1.csv` only for a later sandbox preview. Do not apply it to the official payload.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    source_rows = read_csv(IN_SAMPLE)
    calibration_rows, sandbox_rows = build_rows(source_rows)
    summary = summary_rows(calibration_rows, sandbox_rows)
    write_csv(OUT_CALIBRATION, calibration_rows, CALIBRATION_FIELDS)
    write_csv(OUT_SUMMARY, summary, SUMMARY_FIELDS)
    write_csv(OUT_SANDBOX_CANDIDATES, sandbox_rows, SANDBOX_FIELDS)
    write_report(calibration_rows, sandbox_rows, summary)
    print(f"calibration_rows={len(calibration_rows)}")
    print(f"sandbox_candidate_rows={len(sandbox_rows)}")
    print(f"statuses={dict(Counter(row['calibration_status'] for row in calibration_rows).most_common())}")
    print(f"calibrated_actions={dict(Counter(row['calibrated_action'] for row in calibration_rows).most_common())}")
    print(f"wrote {OUT_CALIBRATION.relative_to(ROOT)}")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_SANDBOX_CANDIDATES.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
