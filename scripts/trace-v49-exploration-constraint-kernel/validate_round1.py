#!/usr/bin/env python3
"""Deterministic hard-gate validator for TRACE v49 Round 11."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "docs/research/trace-v49-exploration-constraint-kernel-round1"
AUDIT = ROOT / "docs/audits/v49-exploration-constraint-kernel-round1"
SOURCE_SHA = "4bd82deba482ec2fbf8c4856080151416fb8ee83"
REAL_LABELS = [
    "mediation", "canonization", "professionalization", "institutionalization",
    "transnational interactions", "cultural translation", "design exchanges",
    "commodification", "gendering", "displacement", "transculturation",
    "cultural mobility", "self-exoticization", "coloniality", "imitation", "piracy",
]
REQUIRED_FAILURE_CODES = {
    "NO_ACTIVE_VOCABULARY", "NO_ACTIVE_GRAMMAR", "UNRESOLVED_NODE",
    "RESEARCH_ONLY_NODE", "UNKNOWN_NODE", "UNAUTHORIZED_PAIR", "DEFERRED_PAIR",
    "REJECTED_PAIR", "DIRECTIONALITY_NOT_AUTHORIZED", "SELF_RELATION_NOT_AUTHORIZED",
    "UNBOUNDED_ARGUMENT_ROLE", "ROLE_MISMATCH", "UNIVERSAL_NODE_PROHIBITED",
    "REQUIRED_QUALIFICATION_MISSING", "UNAUTHORIZED_CLUSTER", "UNAUTHORIZED_CHAIN",
    "TRANSITIVE_INFERENCE_PROHIBITED", "ARCHIVE_OBJECT_CONTAMINATION",
    "CONTEXT_CONTAMINATION", "SPACETIME_CONTAMINATION", "EXTERNAL_MODEL_CONTAMINATION",
    "PACKAGE_HASH_MISMATCH", "PROVENANCE_MISSING", "NONDETERMINISTIC_BUILD",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def reconcile() -> dict[str, object]:
    """Run the sealed-input reconciler without importing it or creating pycache."""
    result = subprocess.run(
        ["python3", str(ROOT / "scripts/trace-v49-exploration-constraint-kernel/reconcile_round10.py")],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def verify_required_files() -> None:
    research_names = [
        "00_EXECUTIVE_DECISION.md", "01_SCOPE_AND_NON_GOALS.md", "02_ROUND10_NEGATIVE_CONSTRAINT_INPUT.md",
        "03_ACTIVATION_STATE_MACHINE.md", "04_CONSTRAINT_REGISTRY.tsv", "05_BUILD_CONTRACT.md",
        "06_IMAGE_COMPILER_SPECIFICATION.md", "07_BUILD_FAILURE_CODE_REGISTRY.tsv",
        "08_SYNTHETIC_FIXTURE_REGISTRY.tsv", "09_ROUND10_RECONCILIATION.tsv",
        "10_DETERMINISM_AND_HASHING.md", "11_IMAGE_INSTANCE_CONTAINER_LIFECYCLE.md",
        "12_GENERATIVE_COMPOSITION_BOUNDARY.md", "13_CLUSTER_AND_CHAIN_BOUNDARY.md",
        "14_REAL_IMAGE_BLOCKER_REGISTER.tsv", "15_ADVERSARIAL_TEST_MATRIX.tsv",
        "16_HUMAN_DOMAIN_REVIEW_HANDOFF.md", "17_ROUND_DECISION.md",
    ]
    audit_names = [
        "00_EXECUTIVE_RECEIPT.md", "01_MAIN_SYNC_VALIDATION.md", "02_ROUND10_INPUT_RECONCILIATION.md",
        "03_CONSTRAINT_KERNEL_VALIDATION.md", "04_REAL_BUILD_REJECTION_VALIDATION.md",
        "05_SYNTHETIC_BUILD_VALIDATION.md", "06_IMAGE_IMMUTABILITY_VALIDATION.md",
        "07_FAIL_CLOSED_MUTATION_VALIDATION.md", "08_ZERO_OBJECT_AND_MODEL_BOUNDARY.md",
        "09_PROTECTED_SYSTEMS.md", "10_CHANGED_FILES.md", "MANIFEST.tsv", "SHA256SUMS.txt",
    ]
    require(all((RESEARCH / name).is_file() for name in research_names), "required research file missing")
    require(all((AUDIT / name).is_file() for name in audit_names), "required audit file missing")
    require(len([path for path in RESEARCH.iterdir() if path.is_file()]) == len(research_names), "unexpected research root file")


def verify_research_registries() -> None:
    constraints = read_tsv(RESEARCH / "04_CONSTRAINT_REGISTRY.tsv")
    failures = read_tsv(RESEARCH / "07_BUILD_FAILURE_CODE_REGISTRY.tsv")
    fixtures = read_tsv(RESEARCH / "08_SYNTHETIC_FIXTURE_REGISTRY.tsv")
    round10 = read_tsv(RESEARCH / "09_ROUND10_RECONCILIATION.tsv")
    blockers = read_tsv(RESEARCH / "14_REAL_IMAGE_BLOCKER_REGISTER.tsv")
    adversarial = read_tsv(RESEARCH / "15_ADVERSARIAL_TEST_MATRIX.tsv")
    require(len(constraints) == 37 and all(row["status"] == "PASS" for row in constraints), "constraint registry incomplete")
    require(REQUIRED_FAILURE_CODES <= {row["failure_code"] for row in failures}, "failure-code registry incomplete")
    require(all(row["fail_closed"] == "true" and row["partial_image_allowed"] == "false" for row in failures), "failure code is not fail closed")
    require(len(fixtures) == 10, "synthetic fixture count mismatch")
    require(all(row["synthetic_test_only"] == "true" and row["production_exportable"] == "false" for row in fixtures), "synthetic fixture is exportable")
    require(len(round10) == 13 and all(row["status"] == "PASS" and row["runtime_activation"] == "false" for row in round10), "Round 10 reconciliation registry mismatch")
    require(len(blockers) == 9 and all(row["current_status"] == "OPEN" for row in blockers), "real Image blockers changed")
    require(len(adversarial) == 20 and all(row["status"] == "PASS" for row in adversarial), "adversarial matrix incomplete")


def verify_test_receipt() -> None:
    receipt = json.loads((AUDIT / "raw/constraint_kernel_test_receipt.json").read_text())
    require(receipt["status"] == "PASS", "constraint suite failed")
    require(receipt["requiredAdversarialCaseCount"] == 20 and receipt["requiredAdversarialPassCount"] == 20, "adversarial case count mismatch")
    require(receipt["failOpenMutationCount"] == 0 and receipt["mutationCaseCount"] == 10, "mutation gate failed")
    require((receipt["currentRealBuildAttemptCount"], receipt["currentRealBuildSuccessCount"], receipt["currentRealBuildRejectionCount"]) == (1, 0, 1), "current real build did not fail closed")
    require(receipt["syntheticTestImageBuildCount"] >= 1 and receipt["syntheticTestImageBuildPass"] is True, "synthetic compile did not pass")
    require(receipt["syntheticInstanceCreation"] == "PASS" and receipt["syntheticContainerLifecycle"] == "PASS", "synthetic lifecycle failed")
    require(receipt["syntheticFixtureProductionImportCount"] == 0, "synthetic fixture leaked into production")
    require(receipt["realSemanticImageBuildCount"] == receipt["realSemanticFlowBuildCount"] == receipt["realSemanticClusterBuildCount"] == receipt["realSemanticChainBuildCount"] == 0, "real semantic artifact was built")
    require(receipt["syntheticBuildHashEquality"] == "PASS" and receipt["imageImmutability"] == "PASS", "determinism or immutability failed")
    require(receipt["imageHashMutationAfterContainerEditCount"] == 0, "Container edit changed Image hash")


def verify_runtime_boundaries() -> None:
    production = [
        ROOT / "frontend/src/lib/trace/exploration-build-contract.ts",
        ROOT / "frontend/src/lib/trace/exploration-constraint-kernel.ts",
        ROOT / "frontend/src/lib/trace/exploration-image-compiler.ts",
    ]
    source = "\n".join(path.read_text().lower() for path in production)
    require(not [label for label in REAL_LABELS if label in source], "Round 9/10 label entered runtime compiler")
    require("docs/research/" not in source and "docs/audits/" not in source and ".tsv" not in source, "production runtime reads research/audit TSV")
    require("exploration-constraint-kernel-synthetic-fixtures" not in source, "production runtime imports synthetic fixture")
    require(not (ROOT / "frontend/src/app/trace/exploration").exists(), "public Exploration route added")
    require(not (ROOT / "frontend/src/app/api/trace/exploration").exists(), "public Exploration API added")
    require(not (ROOT / "frontend/src/app/api/v1/trace/exploration").exists(), "public v1 Exploration API added")
    require("unresolved_relation_vocabulary_version" in source and "unresolved_relation_grammar_version" in source, "unresolved active state absent")


def verify_changed_paths() -> None:
    changed = set(subprocess.run(["git", "diff", "--name-only", SOURCE_SHA], cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE).stdout.splitlines())
    changed.update(subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE).stdout.splitlines())
    allowed_exact = {
        "PROJECT_LOG.md", "docs/research/EXPLORATION_CURRENT.md", "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json",
        "frontend/package.json", "frontend/tsconfig.json",
        "frontend/src/lib/trace/exploration-build-contract.ts",
        "frontend/src/lib/trace/exploration-constraint-kernel.ts",
        "frontend/src/lib/trace/exploration-image-compiler.ts",
        "frontend/scripts/fixtures/exploration-constraint-kernel-synthetic-fixtures.ts",
        "frontend/scripts/test-exploration-constraint-kernel.mjs",
    }
    allowed_prefixes = (
        "docs/research/trace-v49-exploration-constraint-kernel-round1/",
        "docs/audits/v49-exploration-constraint-kernel-round1/",
        "scripts/trace-v49-exploration-constraint-kernel/",
    )
    disallowed = sorted(path for path in changed if path not in allowed_exact and not path.startswith(allowed_prefixes))
    require(not disallowed, f"out-of-scope changed paths: {disallowed}")
    protected = ("database/", "frontend/src/app/search/", "frontend/src/features/search-v49/", "frontend/src/features/trace-v49/context/", "frontend/src/features/trace-v49/spacetime/")
    require(not [path for path in changed if path.startswith(protected)], "protected system changed")


def verify_audit_seal() -> None:
    manifest = read_tsv(AUDIT / "MANIFEST.tsv")
    require(len(manifest) >= 40, "manifest unexpectedly small")
    for row in manifest:
        path = ROOT / row["path"]
        require(path.is_file(), f"manifest path missing: {row['path']}")
        require(path.stat().st_size == int(row["bytes"]), f"manifest bytes mismatch: {row['path']}")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"], f"manifest hash mismatch: {row['path']}")
    checksum_lines = (AUDIT / "SHA256SUMS.txt").read_text().splitlines()
    require(len(checksum_lines) == len(manifest) + 1, "checksum count mismatch")
    for line in checksum_lines:
        digest, relative = line.split("  ", 1)
        path = ROOT / relative
        require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, f"checksum mismatch: {relative}")


def verify_indexes_and_allowlist() -> None:
    project_log = (ROOT / "PROJECT_LOG.md").read_text()
    current = (ROOT / "docs/research/EXPLORATION_CURRENT.md").read_text()
    require("ROUND11_CONSTRAINT_KERNEL_PREPROGRAMMING=COMPLETE_WITH_LIMITATIONS" in project_log, "Project Log not updated")
    require("CONSTRAINT_KERNEL_PREPROGRAMMING_READY" in current and "REAL_SEMANTIC_IMAGE_READY=false" in current, "current authority not updated")
    allowlist = json.loads((ROOT / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json").read_text())
    require(allowlist["scriptCount"] == len(allowlist["scripts"]), "active-script allowlist count mismatch")
    required = {
        "scripts/trace-v49-relation-grammar/generate_round1.py",
        "scripts/trace-v49-relation-grammar/validate_round1.py",
        "scripts/trace-v49-exploration-constraint-kernel/reconcile_round10.py",
        "scripts/trace-v49-exploration-constraint-kernel/generate_round1.py",
        "scripts/trace-v49-exploration-constraint-kernel/validate_round1.py",
    }
    require(required <= {row["path"] for row in allowlist["scripts"]}, "active-script allowlist missing Round 10/11 scripts")


def main() -> None:
    reconciliation = reconcile()
    require(reconciliation["reconciliation"] == "PASS", "Round 10 reconciliation failed")
    verify_required_files()
    verify_research_registries()
    verify_test_receipt()
    verify_runtime_boundaries()
    verify_changed_paths()
    verify_audit_seal()
    verify_indexes_and_allowlist()
    require(not list(ROOT.rglob("__pycache__")) and not list(ROOT.rglob("*.pyc")), "Python cache artifact present")
    print("ROUND11_VALIDATION=PASS")
    print("ROUND10_RECONCILIATION=PASS")
    print("CONSTRAINT_KERNEL_TESTS=PASS")
    print("IMAGE_COMPILER_TESTS=PASS")
    print("CURRENT_REAL_BUILD_REJECTION=PASS")
    print("SYNTHETIC_TEST_IMAGE_BUILD=PASS")
    print("FAIL_OPEN_MUTATION_COUNT=0")
    print("PRODUCTION_RUNTIME_RESEARCH_TSV_READ_COUNT=0")
    print("REAL_SEMANTIC_IMAGE_BUILD_COUNT=0")
    print("AUDIT_SEAL=PASS")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, subprocess.CalledProcessError) as exc:
        print(f"ROUND11_VALIDATION=FAIL: {exc}")
        raise SystemExit(1)
