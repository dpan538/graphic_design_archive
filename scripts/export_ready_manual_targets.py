from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

TARGETS = DATA / "first_ingest_record_targets.csv"
VERIFICATIONS = DATA / "first_ingest_target_verifications.csv"
OUTPUT = DATA / "ready_manual_ingest_targets.csv"

READY_PREFIXES = (
    "ready_manual",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    targets = {row["first_target_id"]: row for row in read_csv(TARGETS)}
    verifications = read_csv(VERIFICATIONS)

    rows: list[dict[str, str]] = []
    for verification in verifications:
        decision = verification["verification_decision"]
        if not decision.startswith(READY_PREFIXES):
            continue
        target = targets[verification["first_target_id"]]
        rows.append(
            {
                "first_target_id": target["first_target_id"],
                "target_number": target["target_number"],
                "scope_cell_id": target["scope_cell_id"],
                "target_label": target["target_label"],
                "source_name": target["source_name"],
                "record_family": target["record_family"],
                "source_url_or_search_path": target["source_url_or_search_path"],
                "canonical_url": verification["canonical_url"],
                "verification_decision": decision,
                "confirmed_image_zone": verification["confirmed_image_zone"],
                "rights_risk": target["rights_risk"],
                "required_action": verification["required_action"],
            }
        )

    rows.sort(key=lambda row: int(row["target_number"]))
    fieldnames = list(rows[0].keys()) if rows else []
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{OUTPUT}: {len(rows)} ready targets")


if __name__ == "__main__":
    main()
