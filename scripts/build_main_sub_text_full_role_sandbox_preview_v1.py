#!/usr/bin/env python3
"""Preview calibrated full-role main/sub/text overrides without release mutation."""

from __future__ import annotations

import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import audit_prefreeze_candidate_payload_v1 as audit
import build_prefreeze_candidate_payload_v1 as candidate_build


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "capture"
BASELINE_PAYLOAD = ROOT / "generated" / "public_surfaces_prefreeze_candidate_v1.json"

IN_CANDIDATES = DATA / "prefreeze_main_sub_text_full_role_sandbox_candidates_v1.csv"
BASE_OVERRIDES = DATA / "prefreeze_surface_role_overrides_packet_applied_v1.csv"

SANDBOX_OVERRIDES = DATA / "prefreeze_main_sub_text_full_role_sandbox_preview_overrides_v1.csv"
OVERRIDE_SUMMARY = DATA / "prefreeze_main_sub_text_full_role_sandbox_preview_override_summary_v1.csv"
SURFACE_DELTA = DATA / "prefreeze_main_sub_text_full_role_sandbox_preview_surface_delta_v1.csv"
METRICS = DATA / "prefreeze_main_sub_text_full_role_sandbox_preview_metrics_v1.csv"
REPORT = DOCS / "MAIN_SUB_TEXT_FULL_ROLE_SANDBOX_PREVIEW_v1.md"

OVERRIDE_FIELDS = [
    "source_file",
    "capture_id",
    "surface_id",
    "surface_disposition_override",
    "review_class",
    "decision_type",
    "confidence",
    "override_basis",
    "source_name",
    "title",
    "override_source",
    "packet_id",
]

SUMMARY_FIELDS = ["metric", "value", "notes"]
DELTA_FIELDS = [
    "surface_id",
    "capture_id",
    "candidate_role",
    "title",
    "source_name",
    "before_publication_role",
    "after_publication_role",
    "before_surface_type",
    "after_surface_type",
    "before_template_id",
    "after_template_id",
    "before_image_state",
    "after_image_state",
    "delta_status",
]
METRIC_FIELDS = ["metric", "baseline", "preview", "delta", "notes"]

ROLE_TO_DISPOSITION = {
    "card_context": "card",
    "sub_under_packet": "support_packet_appendix_text",
    "text_or_appendix": "support_packet_appendix_text",
}
VISIBLE_STATES = {"IMG01", "IMG02", "IMG03"}
OPEN_STATES = {"IMG03"}


def clean(value: object) -> str:
    return str(value or "").strip()


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


def capture_record_index() -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for path in candidate_build.capture_record_files():
        for row in read_csv(path):
            capture_id = clean(row.get("capture_id"))
            if not capture_id or capture_id in index:
                continue
            enriched = dict(row)
            enriched["_source_file"] = path.name
            index[capture_id] = enriched
    return index


def make_preview_overrides() -> tuple[list[dict[str, str]], list[dict[str, str]], Counter[str]]:
    candidate_rows = read_csv(IN_CANDIDATES)
    base_rows = read_csv(BASE_OVERRIDES)
    record_index = capture_record_index()
    existing_keys = {(Path(row.get("source_file", "")).name, clean(row.get("capture_id"))) for row in base_rows}
    preview_rows: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    stats: Counter[str] = Counter()

    for row in candidate_rows:
        stats["candidate_input_rows"] += 1
        candidate_role = clean(row.get("candidate_role"))
        disposition = ROLE_TO_DISPOSITION.get(candidate_role)
        capture_id = clean(row.get("capture_id"))
        source_record = record_index.get(capture_id)
        if not disposition:
            stats["rejected_unknown_candidate_role"] += 1
            rejected.append({**row, "reject_reason": "unknown_candidate_role"})
            continue
        if not source_record:
            stats["rejected_missing_capture_record"] += 1
            rejected.append({**row, "reject_reason": "missing_capture_record"})
            continue
        source_file = Path(source_record.get("_source_file", "")).name
        key = (source_file, capture_id)
        if key in existing_keys:
            stats["rejected_existing_override_collision"] += 1
            rejected.append({**row, "reject_reason": "existing_override_collision", "source_file": source_file})
            continue
        override = {
            "source_file": source_file,
            "capture_id": capture_id,
            "surface_id": clean(row.get("surface_id")) or f"SURF-{capture_id}",
            "surface_disposition_override": disposition,
            "review_class": f"full_role_calibrated_{candidate_role}",
            "decision_type": "sandbox_full_role_preview",
            "confidence": clean(row.get("calibration_confidence")) or "medium",
            "override_basis": "full_role_calibration_v1: " + clean(row.get("calibration_reason")),
            "source_name": clean(source_record.get("source_name")),
            "title": clean(source_record.get("source_title")),
            "override_source": "main_sub_text_full_role_sandbox_preview_v1",
            "packet_id": clean(row.get("period_band")) + "|" + clean(row.get("region")),
        }
        preview_rows.append(override)
        existing_keys.add(key)
        stats[f"preview_role:{candidate_role}"] += 1
        stats[f"preview_disposition:{disposition}"] += 1

    merged_rows = base_rows + preview_rows
    write_csv(SANDBOX_OVERRIDES, merged_rows, OVERRIDE_FIELDS)
    stats["base_override_rows"] = len(base_rows)
    stats["merged_override_rows"] = len(merged_rows)
    stats["sandbox_preview_overrides"] = len(preview_rows)
    stats["rejected_rows"] = len(rejected)
    return preview_rows, rejected, stats


def load_baseline_payload() -> dict[str, Any]:
    return json.loads(BASELINE_PAYLOAD.read_text(encoding="utf-8"))


def build_preview_payload() -> dict[str, Any]:
    previous = os.environ.get("PREFREEZE_ROLE_OVERRIDES_PATH")
    os.environ["PREFREEZE_ROLE_OVERRIDES_PATH"] = str(SANDBOX_OVERRIDES)
    try:
        rows, _input_stats, _counters = candidate_build.candidate_rows()
        payload = candidate_build.build_payload(rows)
    finally:
        if previous is None:
            os.environ.pop("PREFREEZE_ROLE_OVERRIDES_PATH", None)
        else:
            os.environ["PREFREEZE_ROLE_OVERRIDES_PATH"] = previous
    return payload


def surface_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {clean(surface.get("surfaceId")): surface for surface in payload.get("surfaces", [])}


def image_state(surface: dict[str, Any] | None) -> str:
    if not surface:
        return ""
    image = surface.get("image") if isinstance(surface.get("image"), dict) else {}
    return clean(image.get("state")) or "IMG00"


def object_metrics(payload: dict[str, Any]) -> dict[str, float | int]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for surface in payload.get("surfaces", []):
        groups[audit.object_key(surface)].append(surface)
    object_total = len(groups)
    object_visible = sum(1 for group in groups.values() if any(image_state(surface) in VISIBLE_STATES for surface in group))
    object_open = sum(
        1
        for group in groups.values()
        if any(image_state(surface) in OPEN_STATES and audit.rights_reviewed(surface) for surface in group)
    )
    object_weight = sum(max(audit.PUBLICATION_WEIGHTS.get(image_state(surface), 0.0) for surface in group) for group in groups.values())
    object_best_states = Counter(
        max((image_state(surface) for surface in group), key=lambda state: audit.PUBLICATION_WEIGHTS.get(state, 0.0))
        for group in groups.values()
    )
    return {
        "object_count": object_total,
        "object_source_visible_rate": float(audit.pct(object_visible, object_total)),
        "object_verified_open_rate": float(audit.pct(object_open, object_total)),
        "object_weighted_publication_grade_rate": float(audit.pct(object_weight, object_total)),
        "object_img04_rate": float(audit.pct(object_best_states.get("IMG04", 0), object_total)),
    }


def payload_metrics(payload: dict[str, Any]) -> dict[str, float | int]:
    surfaces = payload.get("surfaces", [])
    source_names = {clean(surface.get("sourceName")) for surface in surfaces if clean(surface.get("sourceName"))}
    roles = Counter(clean(surface.get("publicationRole")) or "unknown" for surface in surfaces)
    types = Counter(clean(surface.get("surfaceType")) or "unknown" for surface in surfaces)
    states = Counter(image_state(surface) for surface in surfaces)
    metrics: dict[str, float | int] = {
        "surfaces": len(surfaces),
        "active_public_sources": len(source_names),
        "research_dossiers": len(payload.get("researchDossiers", [])),
        "main_sheet_count": roles.get("main_sheet", 0),
        "card_count": sum(1 for surface in surfaces if clean(surface.get("publicationRole")) == "card" or clean(surface.get("surfaceType")) == "card"),
        "support_packet_count": roles.get("support_packet_appendix_text", 0) + roles.get("thin_visual_support_packet", 0),
        "text_template_count": sum(1 for surface in surfaces if clean(surface.get("templateId")) == "sheet.text.v0"),
        "sheet_surface_count": types.get("sheet", 0),
        "surface_source_visible_rate": float(audit.pct(sum(1 for surface in surfaces if image_state(surface) in VISIBLE_STATES), len(surfaces))),
        "surface_verified_open_rate": float(
            audit.pct(sum(1 for surface in surfaces if image_state(surface) in OPEN_STATES and audit.rights_reviewed(surface)), len(surfaces))
        ),
    }
    for state, count in states.items():
        metrics[f"surface_image_state_{state}"] = count
    metrics.update(object_metrics(payload))
    return metrics


def metric_rows(baseline_payload: dict[str, Any], preview_payload: dict[str, Any]) -> list[dict[str, str]]:
    baseline = payload_metrics(baseline_payload)
    preview = payload_metrics(preview_payload)
    rows: list[dict[str, str]] = []
    for metric in sorted(set(baseline) | set(preview)):
        before = baseline.get(metric, 0)
        after = preview.get(metric, 0)
        if isinstance(before, float) or isinstance(after, float):
            before_num = float(before)
            after_num = float(after)
            rows.append({"metric": metric, "baseline": f"{before_num:.2f}", "preview": f"{after_num:.2f}", "delta": f"{after_num - before_num:.2f}", "notes": "Candidate-only sandbox preview metric."})
        else:
            before_num = int(before)
            after_num = int(after)
            rows.append({"metric": metric, "baseline": str(before_num), "preview": str(after_num), "delta": str(after_num - before_num), "notes": "Candidate-only sandbox preview metric."})
    return rows


def build_surface_delta(
    baseline_payload: dict[str, Any],
    preview_payload: dict[str, Any],
    preview_overrides: list[dict[str, str]],
) -> list[dict[str, str]]:
    baseline = surface_map(baseline_payload)
    preview = surface_map(preview_payload)
    candidate_lookup = {clean(row.get("surface_id")): row for row in read_csv(IN_CANDIDATES)}
    rows: list[dict[str, str]] = []
    for override in preview_overrides:
        surface_id = clean(override.get("surface_id"))
        before = baseline.get(surface_id)
        after = preview.get(surface_id)
        candidate = candidate_lookup.get(surface_id, {})
        if not before:
            status = "missing_before"
        elif not after:
            status = "missing_after"
        elif clean(after.get("publicationRole")) == clean(override.get("surface_disposition_override")):
            status = "preview_disposition_applied"
        elif clean(after.get("surfaceType")) == "card" and clean(override.get("surface_disposition_override")) == "card":
            status = "preview_disposition_applied"
        else:
            status = "preview_not_applied"
        rows.append(
            {
                "surface_id": surface_id,
                "capture_id": clean(override.get("capture_id")),
                "candidate_role": clean(candidate.get("candidate_role")),
                "title": clean((after or before or {}).get("title")),
                "source_name": clean((after or before or {}).get("sourceName")),
                "before_publication_role": clean((before or {}).get("publicationRole")),
                "after_publication_role": clean((after or {}).get("publicationRole")),
                "before_surface_type": clean((before or {}).get("surfaceType")),
                "after_surface_type": clean((after or {}).get("surfaceType")),
                "before_template_id": clean((before or {}).get("templateId")),
                "after_template_id": clean((after or {}).get("templateId")),
                "before_image_state": image_state(before),
                "after_image_state": image_state(after),
                "delta_status": status,
            }
        )
    return rows


def write_report(summary_rows: list[dict[str, Any]], delta_rows: list[dict[str, str]], metrics: list[dict[str, str]]) -> None:
    key_metrics = {
        row["metric"]: row
        for row in metrics
        if row["metric"]
        in {
            "surfaces",
            "active_public_sources",
            "main_sheet_count",
            "card_count",
            "support_packet_count",
            "text_template_count",
            "object_source_visible_rate",
            "object_verified_open_rate",
            "object_weighted_publication_grade_rate",
            "object_img04_rate",
        }
    }
    status_counts = Counter(row["delta_status"] for row in delta_rows)
    lines = [
        "# Main/Sub/Text Full Role Sandbox Preview v1",
        "",
        "Scope: candidate-only sandbox preview of calibrated full-role card/sub/text candidates.",
        "",
        "This pass does not write a generated payload JSON, mutate the official payload, download images, or change rights/image states.",
        "",
        "## Override Summary",
        "",
    ]
    for row in summary_rows:
        lines.append(f"- {row['metric']}: {row['value']} ({row['notes']})")
    lines.extend(["", "## Delta Status", ""])
    for status, count in status_counts.most_common():
        lines.append(f"- `{status}`: {count}")
    lines.extend(["", "## Key Metric Deltas", ""])
    for metric, label in [
        ("surfaces", "surfaces"),
        ("active_public_sources", "active public sources"),
        ("main_sheet_count", "main sheets"),
        ("card_count", "cards"),
        ("support_packet_count", "support packets"),
        ("text_template_count", "text templates"),
        ("object_source_visible_rate", "object source-visible rate"),
        ("object_verified_open_rate", "object verified-open rate"),
        ("object_weighted_publication_grade_rate", "object weighted publication-grade rate"),
        ("object_img04_rate", "object IMG04 rate"),
    ]:
        row = key_metrics.get(metric)
        if row:
            lines.append(f"- {label}: {row['baseline']} -> {row['preview']} (delta {row['delta']})")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This preview tests structure only; it is not an archive-wide demotion.",
            "- Source, object, rights, and image-state rates should remain stable because the same objects are retained with different roles.",
            "- Card-heavy movement is expected because the calibrated candidates are mostly stamp/philatelic Commons records.",
            "",
            "## Safety Notes",
            "",
            "- No image files were downloaded.",
            "- IMG01/IMG03 were not upgraded by heuristic, LLM, TOS, platform, or source-priority signals.",
            "- The official payload and frontend mirrors were not edited.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    preview_overrides, rejected, stats = make_preview_overrides()
    baseline_payload = load_baseline_payload()
    preview_payload = build_preview_payload()
    delta_rows = build_surface_delta(baseline_payload, preview_payload, preview_overrides)
    metric_delta_rows = metric_rows(baseline_payload, preview_payload)
    stats["preview_applied"] = sum(1 for row in delta_rows if row["delta_status"] == "preview_disposition_applied")
    stats["rejected_examples"] = len(rejected)
    summary_rows = [{"metric": key, "value": value, "notes": "Full-role sandbox preview statistic."} for key, value in sorted(stats.items())]
    write_csv(OVERRIDE_SUMMARY, summary_rows, SUMMARY_FIELDS)
    write_csv(SURFACE_DELTA, delta_rows, DELTA_FIELDS)
    write_csv(METRICS, metric_delta_rows, METRIC_FIELDS)
    write_report(summary_rows, delta_rows, metric_delta_rows)
    print(f"sandbox_preview_overrides={stats['sandbox_preview_overrides']}")
    print(f"preview_applied={stats['preview_applied']}")
    print(f"rejected_rows={stats['rejected_rows']}")
    print(f"wrote {SANDBOX_OVERRIDES.relative_to(ROOT)}")
    print(f"wrote {OVERRIDE_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {SURFACE_DELTA.relative_to(ROOT)}")
    print(f"wrote {METRICS.relative_to(ROOT)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
