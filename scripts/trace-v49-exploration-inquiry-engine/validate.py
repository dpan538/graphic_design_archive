#!/usr/bin/env python3
"""Fail-closed validator for the complete Round 12 generated package."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ENGINE = Path(__file__).resolve().parent
REPO = ENGINE.parents[1]
sys.path.insert(0, str(ENGINE))

from coverage import compute_evidence_coverage  # noqa: E402
from freeze import build_candidate_freeze, load_candidate_freeze  # noqa: E402
from instance_compiler import verify_research_inquiry_instance  # noqa: E402
from seed_registry import build_seed_registry  # noqa: E402
from strict_parse import validate_candidate_freeze  # noqa: E402

RESEARCH = REPO / "docs/research/trace-v49-exploration-inquiry-flow-round1"
AUDIT = REPO / "docs/audits/v49-exploration-inquiry-flow-round1"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle: return list(csv.DictReader(handle, delimiter="\t"))


def fail(condition: bool, message: str) -> None:
    if not condition: raise SystemExit(f"ROUND12_VALIDATION_FAIL: {message}")


def sha256(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    required_research = [
        "00_EXECUTIVE_DECISION.md", "01_SCOPE_AND_METHOD.md", "02_RESEARCH_CANDIDATE_FREEZE.json",
        "03_EVIDENCE_COVERAGE_SUMMARY.tsv", "04_NODE_EVIDENCE_COVERAGE.tsv", "05_PAIR_QUESTION_EVIDENCE_COVERAGE.tsv",
        "06_NODE_TO_INSTANCE_COVERAGE.tsv", "07_INSTANCE_EVIDENCE_COVERAGE.tsv", "08_INQUIRY_SEED_REGISTRY.tsv",
        "09_TREE_STRATEGY_REGISTRY.tsv", "10_INQUIRY_OPERATION_REGISTRY.tsv", "11_RESEARCH_INSTANCE_REGISTRY.tsv",
        "13_CROSS_RUNTIME_CONFORMANCE.tsv", "14_RUNTIME_SCHEMA_HARDENING.md", "15_RESEARCH_PREVIEW_REVIEW_PACKET.tsv",
        "16_LIMITATIONS_AND_ACTIVATION_BOUNDARY.md", "17_ROUND_DECISION.md", "coverage-summary.json",
    ]
    required_audit = [f"{index:02d}_{name}.md" for index, name in enumerate([
        "EXECUTIVE_RECEIPT", "SOURCE_AND_FREEZE_VALIDATION", "EVIDENCE_COVERAGE_VALIDATION",
        "LANGUAGE_NEUTRAL_SCHEMA_VALIDATION", "PYTHON_REFERENCE_ENGINE_VALIDATION", "TYPESCRIPT_ADAPTER_CONFORMANCE",
        "FLOW_AND_TREE_VALIDATION", "INSTANCE_VALIDATION", "RUNTIME_SCHEMA_HARDENING", "ZERO_OBJECT_AND_MODEL_BOUNDARY",
        "PROTECTED_SYSTEMS", "CHANGED_FILES",
    ])] + ["MANIFEST.tsv", "SHA256SUMS.txt"]
    fail(all((RESEARCH / name).is_file() for name in required_research), "research package incomplete")
    fail(all((AUDIT / name).is_file() for name in required_audit), "audit package incomplete")
    instance_paths = sorted((RESEARCH / "12_RESEARCH_INSTANCES").glob("INQUIRY-INSTANCE-*.json"))
    fail(len(instance_paths) == 5, "instance count is not five")

    freeze = load_candidate_freeze(RESEARCH / "02_RESEARCH_CANDIDATE_FREEZE.json")
    fail(freeze == build_candidate_freeze(REPO), "freeze replay changed")
    validate_candidate_freeze(freeze)
    coverage = compute_evidence_coverage(REPO, freeze)
    expected = {"totalResearchSourceCount": 78, "totalResearchAttestationCount": 85, "frozenCandidateDirectSourceCount": 57, "frozenCandidateDirectAttestationCount": 62, "boundedCandidateDirectSourceCount": 31, "boundedCandidateDirectAttestationCount": 35, "deferredCandidateDirectSourceCount": 27, "deferredCandidateDirectAttestationCount": 27, "pairQuestionCount": 3, "clusterHandoffCount": 2, "observedChainCount": 2, "gapCount": 6, "blockerCount": 9}
    for key, value in expected.items(): fail(coverage["summary"][key] == value, f"coverage mismatch {key}")
    fail(json.loads((RESEARCH / "coverage-summary.json").read_text()) == coverage["summary"], "coverage dashboard differs from replay")
    fail(len(rows(RESEARCH / "04_NODE_EVIDENCE_COVERAGE.tsv")) == 16, "node coverage row count")
    fail(len(rows(RESEARCH / "05_PAIR_QUESTION_EVIDENCE_COVERAGE.tsv")) == 3, "pair coverage row count")
    fail(len(rows(RESEARCH / "06_NODE_TO_INSTANCE_COVERAGE.tsv")) == 16, "node-instance coverage row count")
    fail(len(rows(RESEARCH / "07_INSTANCE_EVIDENCE_COVERAGE.tsv")) == 5, "instance evidence row count")
    fail(len(rows(RESEARCH / "08_INQUIRY_SEED_REGISTRY.tsv")) == 5, "seed row count")
    fail(len(rows(RESEARCH / "09_TREE_STRATEGY_REGISTRY.tsv")) == 6, "strategy count")
    fail(len(rows(RESEARCH / "10_INQUIRY_OPERATION_REGISTRY.tsv")) == 6, "link kind count")
    fail(len(rows(RESEARCH / "15_RESEARCH_PREVIEW_REVIEW_PACKET.tsv")) == 5, "review row count")

    seeds = build_seed_registry(freeze, coverage["pairRows"])
    instances = [json.loads(path.read_text(encoding="utf-8")) for path in instance_paths]
    for instance, seed in zip(instances, seeds): fail(verify_research_inquiry_instance(instance, freeze, seed), f"instance invalid {instance['instanceId']}")
    fail(len({node["senseId"] for instance in instances for node in instance["semanticNodeRefs"]}) == 8, "bounded Node coverage is not 8/8")
    fail(sum(len(instance["semanticNodeRefs"]) == 2 for instance in instances) == 3, "pair instance count")
    fail(sum(len(instance["semanticNodeRefs"]) == 1 for instance in instances) == 2, "single instance count")
    fail(max(len(instance["semanticNodeRefs"]) for instance in instances) == 2, "max semantic Node count")
    fail(max(item["depth"] for instance in instances for item in instance["treeItems"]) == 3, "max tree depth")
    fail(max(len(instance["treeItems"]) for instance in instances) == 6, "max tree item count")

    for schema_path in sorted((REPO / "schemas/trace/exploration").glob("*.schema.json")):
        schema = json.loads(schema_path.read_text(encoding="utf-8")); fail(schema.get("additionalProperties") is False, f"schema not strict: {schema_path.name}")
    fail(len(list((REPO / "schemas/trace/exploration").glob("*.schema.json"))) == 4, "schema count")
    fixture_payload = json.loads((ENGINE / "fixtures/cross-runtime-fixtures.json").read_text(encoding="utf-8"))
    fail(len(fixture_payload["fixtures"]) >= 10, "cross-runtime fixture count")
    fail(all(row["decision_match"] == "true" for row in rows(RESEARCH / "13_CROSS_RUNTIME_CONFORMANCE.tsv")), "Python conformance mismatch")

    manifest = rows(AUDIT / "MANIFEST.tsv")
    fail(len(manifest) == len({row["relative_path"] for row in manifest}), "duplicate manifest path")
    for row in manifest:
        path = REPO / row["relative_path"]
        fail(path.is_file(), f"manifest path missing {row['relative_path']}")
        fail(sha256(path) == row["sha256"], f"manifest checksum mismatch {row['relative_path']}")
        fail(path.stat().st_size == int(row["byte_count"]), f"manifest size mismatch {row['relative_path']}")
    checksum_lines = (AUDIT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    fail(len(checksum_lines) == len(manifest), "checksum row count mismatch")

    # The generator's sealed manifest is the pre-commit changed-path authority.
    # Post-commit validation separately compares the two Git trees, avoiding
    # worktree clean filters for the repository's large LFS payloads.
    changed = [row["relative_path"] for row in manifest] + [
        "docs/audits/v49-exploration-inquiry-flow-round1/MANIFEST.tsv",
        "docs/audits/v49-exploration-inquiry-flow-round1/SHA256SUMS.txt",
    ]
    protected_prefixes = ("data/", "database/", "frontend/src/app/api/", "frontend/src/lib/search", "frontend/src/lib/context", "frontend/src/lib/spacetime")
    fail(not any(path.startswith(protected_prefixes) for path in changed), f"protected path changed: {[path for path in changed if path.startswith(protected_prefixes)]}")
    fail(not any("__pycache__" in str(path) or str(path).endswith(".pyc") for path in REPO.rglob("__pycache__")), "Python cache artifact present")
    receipt = {"status": "PASS", "freezeValidation": "PASS", "evidenceCoverageValidation": "PASS", "languageNeutralSchemaReady": True, "pythonReferenceEngineReady": True, "typescriptIsNormativeSemanticEngine": False, "seedCount": 5, "instanceCount": 5, "boundedNodeCoverage": "8/8", "manifestRowCount": len(manifest), "protectedSystemChangeCount": 0}
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__": main()
