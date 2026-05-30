from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

FALLBACK_STUBS = DATA / "fallback_source_stubs.csv"
REMEDIATION = DATA / "fallback_remediation_recommendations.csv"
OUTPUT = DATA / "fallback_remediation_projection.csv"


STATUS_MAP = {
    "promote_to_candidate": "projected_candidate_after_verification",
    "replace_target": "projected_replacement_after_verification",
    "browser_recheck_only": "projected_browser_recheck",
    "keep_fallback_stub": "remain_fallback_stub",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    stubs = read_csv(FALLBACK_STUBS)
    remediation_by_cell = {
        row["failed_target_or_cell"]: row for row in read_csv(REMEDIATION)
    }

    rows: list[dict[str, str]] = []
    for stub in stubs:
        remediation = remediation_by_cell.get(stub["scope_cell_id"])
        if remediation:
            recommended_status = remediation["recommended_status"]
            projected_status = STATUS_MAP.get(recommended_status, "needs_manual_decision")
            if recommended_status == "promote_to_candidate":
                projected_url = remediation["confirmed_exact_url"] or remediation["replacement_url"] or stub["user_action_url"]
            elif recommended_status == "replace_target":
                projected_url = remediation["replacement_url"] or remediation["confirmed_exact_url"] or stub["user_action_url"]
            else:
                projected_url = remediation["confirmed_exact_url"] or remediation["replacement_url"] or stub["user_action_url"]
            rationale = remediation["reason"]
        else:
            recommended_status = ""
            projected_status = "remain_fallback_stub"
            projected_url = stub["user_action_url"]
            rationale = "No remediation recommendation was supplied for this scope cell in the current report."

        rows.append(
            {
                "projection_id": f"FRP{len(rows) + 1:03d}",
                "fallback_stub_id": stub["fallback_stub_id"],
                "first_target_id": stub["first_target_id"],
                "scope_cell_id": stub["scope_cell_id"],
                "target_label": stub["target_label"],
                "current_fallback_status": stub["fallback_status"],
                "current_user_action_url": stub["user_action_url"],
                "remediation_recommended_status": recommended_status,
                "projected_status": projected_status,
                "projected_url": projected_url,
                "projected_image_zone": remediation["recommended_image_zone"] if remediation else stub["expected_image_zone"],
                "source_title": remediation["source_title"] if remediation else "",
                "rights_note": remediation["rights_note"] if remediation else "",
                "rationale": rationale,
            }
        )

    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "projection_id",
            "fallback_stub_id",
            "first_target_id",
            "scope_cell_id",
            "target_label",
            "current_fallback_status",
            "current_user_action_url",
            "remediation_recommended_status",
            "projected_status",
            "projected_url",
            "projected_image_zone",
            "source_title",
            "rights_note",
            "rationale",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{OUTPUT.relative_to(ROOT)}: {len(rows)} rows")


if __name__ == "__main__":
    main()
