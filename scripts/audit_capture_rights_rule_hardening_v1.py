#!/usr/bin/env python3
"""Audit capture rights-rule hardening before larger source tranches.

This audit is intentionally local-only. It verifies that restricted Creative
Commons variants are not treated as publication-grade open licenses and that
GSU CONTENTdm harvest rows preserve local rights statements separately from
image-display basis fields.
"""

from __future__ import annotations

import sys
from pathlib import Path

from lib.archive_audit import DATA, DOCS, ROOT, write_csv

sys.path.insert(0, str(ROOT / "scripts"))
import run_midcentury_expansion_capture_1931_1970 as midcentury_expansion  # noqa: E402


OUTPUT_ROWS = DATA / "capture_rights_rule_hardening_v1.csv"
OUTPUT_REPORT = DOCS / "CAPTURE_RIGHTS_RULE_HARDENING_v1.md"

FIELDS = [
    "check_id",
    "check_type",
    "target",
    "observed",
    "expected",
    "status",
    "notes",
]

LICENSE_CASES = [
    ("cc_by_nc_url", "https://creativecommons.org/licenses/by-nc/4.0/", False),
    ("cc_by_nd_url", "https://creativecommons.org/licenses/by-nd/4.0/", False),
    ("cc_by_nc_nd_url", "https://creativecommons.org/licenses/by-nc-nd/4.0/", False),
    ("cc_by_text_restricted", "cc-by-nc", False),
    ("cc_by_url", "https://creativecommons.org/licenses/by/4.0/", True),
    ("cc_by_sa_url", "https://creativecommons.org/licenses/by-sa/4.0/", True),
    ("cc0_url", "https://creativecommons.org/publicdomain/zero/1.0/", True),
    ("pdm_text", "PDM", True),
]

GSU_FILES = [
    ROOT / "scripts" / "run_gsu_contentdm_image_ready_1830_1970.py",
    ROOT / "scripts" / "harvest_gsu_contentdm_raw_records.py",
]


def license_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for case_id, value, expected in LICENSE_CASES:
        observed = midcentury_expansion.publication_grade_open_license(value)
        rows.append(
            {
                "check_id": case_id,
                "check_type": "license_classifier",
                "target": value,
                "observed": str(observed).lower(),
                "expected": str(expected).lower(),
                "status": "pass" if observed == expected else "fail",
                "notes": "Restricted NC/ND variants must not qualify for IMG03.",
            }
        )
    return rows


def gsu_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in GSU_FILES:
        text = path.read_text(encoding="utf-8")
        spread_index = text.find("**rights")
        local_statement_index = text.find('"source_rights_text": rights_text')
        preserved = 0 <= spread_index < local_statement_index
        rows.append(
            {
                "check_id": path.stem,
                "check_type": "gsu_rights_field_order",
                "target": str(path.relative_to(ROOT)),
                "observed": "rights_spread_before_source_rights_text" if preserved else "rights_spread_after_or_missing",
                "expected": "rights_spread_before_source_rights_text",
                "status": "pass" if preserved else "fail",
                "notes": "Local CONTENTdm rights statement must not be overwritten by image display basis.",
            }
        )
    return rows


def write_report(rows: list[dict[str, str]]) -> None:
    failures = [row for row in rows if row["status"] != "pass"]
    lines = [
        "# Capture Rights Rule Hardening v1",
        "",
        "This audit records the local rule hardening applied before the next large source tranche. It does not fetch records, download images, mutate surfaces, or upgrade IMG01/IMG03.",
        "",
        "## Summary",
        "",
        f"- checks: {len(rows)}",
        f"- failures: {len(failures)}",
        "- restricted CC BY-NC/BY-ND variants: blocked",
        "- explicit CC BY, CC BY-SA, CC0, and PDM signals: still accepted as publication-grade open candidates",
        "- GSU local rights statements: preserved separately from image-display basis fields",
        "",
        "## Files Hardened",
        "",
        "- `scripts/run_midcentury_expansion_capture_1931_1970.py`",
        "- `scripts/run_gsu_contentdm_image_ready_1830_1970.py`",
        "- `scripts/harvest_gsu_contentdm_raw_records.py`",
        "",
        "## Boundary",
        "",
        "- This pass changes future capture behavior only.",
        "- It does not reclassify existing records, rebuild surfaces, or claim any new rights upgrades.",
        "- Existing Wellcome/IA/GSU rows that may be affected remain part of the repair/rebuild queue.",
        "",
        "## Output",
        "",
        f"- `{OUTPUT_ROWS.relative_to(ROOT)}`",
    ]
    OUTPUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = license_rows() + gsu_rows()
    write_csv(OUTPUT_ROWS, rows, FIELDS)
    write_report(rows)
    failures = [row for row in rows if row["status"] != "pass"]
    print(f"checks={len(rows)}")
    print(f"failures={len(failures)}")
    print(f"wrote {OUTPUT_ROWS.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_REPORT.relative_to(ROOT)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
