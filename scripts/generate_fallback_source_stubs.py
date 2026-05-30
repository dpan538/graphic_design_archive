from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

TARGETS = DATA / "first_ingest_record_targets.csv"
VERIFICATIONS = DATA / "first_ingest_target_verifications.csv"
OUTPUT = DATA / "fallback_source_stubs.csv"

READY_PREFIX = "ready_manual"


STATUS_BY_DECISION = {
    "search_path_only": "search_path_only",
    "needs_browser_recheck": "browser_recheck_required",
    "needs_page_level_recheck": "page_level_recheck_required",
    "replace_target": "replacement_recommended",
    "needs_exact_record_url": "exact_link_unconfirmed",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def public_policy(decision: str) -> str:
    if decision == "replace_target":
        return "show_replacement_link_only_stub"
    if decision == "search_path_only":
        return "show_search_path_stub"
    return "show_link_only_stub"


def display_policy(image_zone: str) -> str:
    if image_zone == "IMG04":
        return "preserve_text_stub_without_image_frame"
    return "preserve_area_with_empty_frame"


def user_action_url(target: dict[str, str], verification: dict[str, str]) -> str:
    raw = (
        verification.get("replacement_url")
        or verification.get("canonical_url")
        or target.get("source_url_or_search_path")
        or ""
    )
    match = re.search(r"https?://[^\s>]+", raw)
    return match.group(0) if match else raw


def main() -> None:
    targets = {row["first_target_id"]: row for row in read_csv(TARGETS)}
    verifications = read_csv(VERIFICATIONS)

    rows: list[dict[str, str]] = []
    for verification in verifications:
        decision = verification["verification_decision"]
        if decision.startswith(READY_PREFIX):
            continue

        target = targets[verification["first_target_id"]]
        status = STATUS_BY_DECISION.get(decision, "not_ingested")
        image_zone = verification["confirmed_image_zone"] or target["expected_image_zone"] or "IMG00"
        reason = verification["blocking_reason"] or verification["required_action"] or "Source could not be safely ingested in this pass."
        action_url = user_action_url(target, verification)

        rows.append(
            {
                "fallback_stub_id": f"FSS{int(target['target_number']):03d}",
                "first_target_id": target["first_target_id"],
                "scope_cell_id": target["scope_cell_id"],
                "target_label": target["target_label"],
                "source_name": target["source_name"],
                "source_url_or_search_path": target["source_url_or_search_path"],
                "canonical_url": verification["canonical_url"],
                "replacement_url": verification["replacement_url"],
                "fallback_status": status,
                "public_stub_policy": public_policy(decision),
                "expected_image_zone": image_zone,
                "display_area_policy": display_policy(image_zone),
                "not_ingested_reason": reason,
                "user_action_label": "Search at source" if decision == "search_path_only" else "View at source",
                "user_action_url": action_url,
                "verification_decision": decision,
                "verified_at": verification["verified_at"],
                "verified_by": verification["verified_by"],
                "evidence_summary": verification["evidence_summary"],
                "required_action": verification["required_action"],
                "blocking_reason": verification["blocking_reason"],
            }
        )

    rows.sort(key=lambda row: int(row["fallback_stub_id"].replace("FSS", "")))
    fieldnames = list(rows[0].keys()) if rows else []
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{OUTPUT.relative_to(ROOT)}: {len(rows)} fallback stubs")


if __name__ == "__main__":
    main()
