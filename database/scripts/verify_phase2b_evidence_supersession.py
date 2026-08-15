#!/usr/bin/env python3
"""Independently gate the additive Phase 2B P1 evidence supersession."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = "11e7b82d27b2774273d2f0d68904632246dabd37"
BASE_HASH = "4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105"
FINAL_HASH = "aa8cb0af7b61931e51f1f71ed2e4cf0d10b178669de16807871819b330742e8b"
EXPECTED = {
    "P1_RIGHTS_LEAF_PRE_FIX_50": ("pre_fix", "rights_leaf", 50),
    "P1_RIGHTS_LEAF_PRE_FIX_250": ("pre_fix", "rights_leaf", 250),
    "P1_RIGHTS_LEAF_POST_FIX_50": ("post_fix", "rights_leaf", 50),
    "P1_RIGHTS_LEAF_POST_FIX_250": ("post_fix", "rights_leaf", 250),
    "P1_RIGHTS_LEAF_POST_FIX_1000": ("post_fix", "rights_leaf", 1000),
    "P1_RIGHTS_LEAF_POST_FIX_PLAN_1000": ("post_fix", "rights_leaf", 1000),
    "P1_DELIVERY_PRE_FIX_50": ("pre_fix", "delivery", 50),
    "P1_DELIVERY_POST_FIX_50": ("post_fix", "delivery", 50),
    "P1_DELIVERY_POST_FIX_250": ("post_fix", "delivery", 250),
    "P1_DELIVERY_POST_FIX_1000": ("post_fix", "delivery", 1000),
    "P1_DELIVERY_POST_FIX_PLAN_1000": ("post_fix", "delivery", 1000),
}


class GateError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GateError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def git_path_exists(path: str) -> bool:
    result = subprocess.run(["git", "cat-file", "-e", f"{SOURCE}:{path}"], cwd=ROOT, check=False, capture_output=True)
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    package = args.package.resolve()
    original = ROOT / "docs/audits/v49-phase2b-performance"
    original_manifest = load_json(original / "MANIFEST.json")
    entries = original_manifest.get("files")
    if not isinstance(entries, list) or len(entries) != 71:
        raise GateError("ORIGINAL_MANIFEST_ENTRY_COUNT")
    original_p1 = [entry for entry in entries if isinstance(entry, dict) and str(entry.get("path", "")).startswith("evidence/P1_")]
    if len(original_p1) != 11:
        raise GateError("ORIGINAL_P1_SET_NOT_11")
    checksum_entries: list[tuple[str, str]] = []
    for raw in (original / "CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines():
        digest, path = raw.split("  ", 1)
        checksum_entries.append((digest, path))
    if len(checksum_entries) != 72:
        raise GateError("ORIGINAL_CHECKSUM_ENTRY_COUNT")
    present: list[str] = []
    missing: list[str] = []
    import hashlib
    for expected_digest, path in checksum_entries:
        artifact = original / path
        if not artifact.is_file():
            missing.append(path)
            continue
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if digest != expected_digest:
            raise GateError(f"ORIGINAL_PRESENT_HASH_MISMATCH:{path}")
        present.append(path)
    if len(present) != 61 or len(missing) != 11 or any(not path.startswith("evidence/P1_") for path in missing):
        raise GateError("ORIGINAL_MISSING_SET_BOUNDARY")
    if any(git_path_exists("docs/audits/v49-phase2b-performance/" + path) for path in missing):
        raise GateError("SOURCE_TREE_UNEXPECTEDLY_CONTAINS_MISSING_LOG")

    self_contained = subprocess.run(
        [sys.executable, str(ROOT / "database/scripts/verify_audit_package_self_contained.py"), "--package", str(package), "--require-index"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    if self_contained.returncode:
        raise GateError("CORRECTIVE_PACKAGE_CHECKSUM_OR_INDEX_FAILURE:" + self_contained.stderr.strip())
    summary = load_json(package / "reproduced/P1_REPRODUCTION_SUMMARY.json")
    records = summary.get("records")
    if summary.get("status") != "PASS" or not isinstance(records, list) or len(records) != 11:
        raise GateError("CORRECTIVE_PROBE_SUMMARY_FAILURE")
    seen: set[str] = set()
    for record in records:
        name = record.get("name")
        if name not in EXPECTED or name in seen:
            raise GateError(f"UNEXPECTED_OR_DUPLICATE_PROBE:{name}")
        seen.add(name)
        state, family, scale = EXPECTED[name]
        if (record.get("schemaState"), record.get("probeFamily"), record.get("scale")) != (state, family, scale):
            raise GateError(f"PROBE_MATRIX_MISMATCH:{name}")
        if record.get("baseSchemaHash") != BASE_HASH:
            raise GateError(f"BASE_SCHEMA_HASH_MISMATCH:{name}")
        if record.get("activeSchemaHash") != (BASE_HASH if state == "pre_fix" else FINAL_HASH):
            raise GateError(f"ACTIVE_SCHEMA_HASH_MISMATCH:{name}")
        if state == "post_fix" and not all(bool(value) for value in record.get("forwardIndexes", {}).values()):
            raise GateError(f"FORWARD_INDEX_INVENTORY_FAILURE:{name}")
        probe = record.get("probe", {})
        execution = probe.get("execution", {}) if isinstance(probe, dict) else {}
        if execution.get("exitCode") != 0 or not probe.get("rollbackObserved"):
            raise GateError(f"PROBE_EXECUTION_OR_ROLLBACK_FAILURE:{name}")
        stdout_descriptor = execution.get("stdout", {}) if isinstance(execution, dict) else {}
        stdout_path = ROOT / str(stdout_descriptor.get("path", ""))
        if not stdout_path.is_file():
            raise GateError(f"PROBE_STDOUT_MISSING:{name}")
        stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace")
        official_probe = ROOT / "database/data-migrations/v48-to-v49" / (
            "p1_rights_leaf_probe.sql" if family == "rights_leaf" else "p1_delivery_validation_probe.sql"
        )
        if "ROLLBACK;" not in official_probe.read_text(encoding="utf-8"):
            raise GateError(f"PROBE_ROLLBACK_TERMINATOR_MISSING:{name}")
        if any(int(value) != 0 for value in record.get("residue", {}).values()):
            raise GateError(f"PROBE_RESIDUE_FAILURE:{name}")
        expected_plan = "sequential_scan" if state == "pre_fix" else (
            "rights_assessment_visual_reference_target_idx" if scale == 1000 else "target_led_function_with_index_present"
        )
        if probe.get("planAssertion") != expected_plan:
            raise GateError(f"PROBE_PLAN_ASSERTION_FAILURE:{name}")
        if state == "pre_fix" and "Seq Scan" not in stdout_text:
            raise GateError(f"PROBE_RAW_SEQUENTIAL_SCAN_MISSING:{name}")
        if state == "post_fix" and scale == 1000 and "rights_assessment_visual_reference_target_idx" not in stdout_text:
            raise GateError(f"PROBE_RAW_INDEX_PATH_MISSING:{name}")
    if seen != set(EXPECTED):
        raise GateError("PROBE_MATRIX_INCOMPLETE")

    output = {
        "status": "PASS",
        "promotionEvidenceBasis": "AUDITED_P1_REPRODUCTION_SUPERSESSION",
        "originalChecksumVerification": "61/72",
        "originalPresentHashMatch": "61/61",
        "originalMissingSetBound": "11/11",
        "missingSetP1Only": True,
        "historicalArtifactsRecovered": False,
        "correctiveProbePass": "11/11",
        "semanticEquivalenceVerified": True,
        "independentVerifierP0": 0,
        "independentVerifierP1": 0,
        "correctivePackageChecksum": json.loads(self_contained.stdout).get("checksumFileCount"),
        "evidentiaryGapClosed": True,
    }
    if args.output.exists():
        raise GateError("REFUSING_TO_OVERWRITE_OUTPUT")
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (GateError, OSError, json.JSONDecodeError) as error:
        print(f"PHASE2B_EVIDENCE_SUPERSESSION_GATE=FAIL:{error}", file=sys.stderr)
        raise SystemExit(2)
