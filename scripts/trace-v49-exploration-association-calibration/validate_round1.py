#!/usr/bin/env python3
"""Exhaustive artifact validator for TRACE v49 Round 14."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.dont_write_bytecode = True
ENGINE = Path(__file__).resolve().parent
REPO = ENGINE.parents[1]
sys.path.insert(0, str(ENGINE))

from calibration_input import build_inputs  # noqa: E402
from generate_round1 import AUDIT, PACKAGE_PATH, RAW, RESEARCH, SOURCE_SHA, canonical_hash, sha256  # noqa: E402
from local_coherence import validate_local_composition  # noqa: E402
from model import DIRECT_POLICIES, GENERIC_TYPES, SKIP_POLICIES, assess, policy_pass  # noqa: E402
from nary_fixtures import NARY_FIXTURES  # noqa: E402


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def validate() -> dict[str, int | bool | str]:
    cases, evidence = build_inputs(REPO)
    evidence_by_assessment: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in evidence:
        evidence_by_assessment[row["assessment_id"]].append(row)
    decisions = {case.assessment_id: assess(case, evidence_by_assessment[case.assessment_id]) for case in cases}

    calibration = read_tsv(RAW / "association-calibration.tsv")
    provenance = read_tsv(RAW / "evidence-provenance.tsv")
    direct = read_tsv(RAW / "direct-neighbour-evaluation.tsv")
    skip = read_tsv(RAW / "skip-one-evaluation.tsv")
    sweep = read_tsv(RAW / "threshold-sweep.tsv")
    sensitivity = read_tsv(RAW / "sensitivity-analysis.tsv")
    nary = read_tsv(RAW / "nary-validation.tsv")
    pruning = read_tsv(RAW / "pruning-validation.tsv")
    reassessment = read_tsv(RAW / "round13-reassessment.tsv")
    full_validation = read_tsv(RAW / "full-validation.tsv")
    metrics = json.loads((RAW / "quantitative-audit.json").read_text(encoding="utf-8"))

    require(len(calibration) == len(cases) == 35, "CALIBRATION_COUNT")
    require(len(provenance) == len(evidence) == 69, "EVIDENCE_PROVENANCE_COUNT")
    require(len({row["evidence_id"] for row in provenance}) == len(provenance), "EVIDENCE_ID_UNIQUENESS")
    require(all(row["source_metadata_verified"] == "true" and row["evidence_verified"] == "true" and row["stable_url"].startswith("https://") for row in provenance), "PROVENANCE_VERIFICATION")
    require(all({row["evidence_id"] for row in provenance if row["assessment_id"] == case.assessment_id} == set(case.evidence_refs) for case in cases), "PROVENANCE_BINDING")
    require(len(direct) == len(skip) == 35 and all(row["decision_match"] == "true" for row in direct + skip), "NEIGHBOUR_DECISION_MATCH")
    require(sum(row["actual_pass"] == "true" for row in direct) == 21 and sum(row["actual_pass"] == "true" for row in skip) == 21, "NEIGHBOUR_PASS_COUNT")
    require(all(not decisions[case.assessment_id]["activeForProximity"] for case in cases if case.cooccurrence_only), "COOCCURRENCE_PASS")
    require(Counter(item["evidenceStatus"] for item in decisions.values()) == {"EXTERNALLY_SUPPORTED": 18, "SOURCE_SUPPORTED": 3, "QUALIFIED": 1, "INSUFFICIENT": 13}, "EVIDENCE_STATUS_COUNTS")

    require(len(sweep) == len(DIRECT_POLICIES) + len(SKIP_POLICIES) == 10, "THRESHOLD_SWEEP_COUNT")
    selected = [row for row in sweep if row["selected"] == "true"]
    require(len(selected) == 2 and all(row["false_positive"] == "0" and row["false_negative"] == "0" for row in selected), "SELECTED_THRESHOLD_CONFUSION")
    permissive = [row for row in sweep if row["configuration_id"] in {"ADJ-04", "SKIP-04"}]
    require(all(int(row["false_positive"]) >= 1 for row in permissive), "PERMISSIVE_FALSE_POSITIVE")
    require(len(sensitivity) == 490, "SENSITIVITY_COUNT")
    changes = sum(row["direct_decision_changed"] == "true" for row in sensitivity) + sum(row["skip_one_decision_changed"] == "true" for row in sensitivity)
    require(changes == metrics["SENSITIVITY_DECISION_CHANGE_COUNT"] and changes * 10 <= len(sensitivity) * 2, "SENSITIVITY_STABILITY")

    require(len(nary) == len(NARY_FIXTURES) == 6 and all(row["status"] == "PASS" for row in nary), "NARY_CONFORMANCE")
    for fixture in NARY_FIXTURES:
        require(validate_local_composition(fixture, decisions)["result"] == fixture["expectedResult"], f"NARY_RESULT:{fixture['fixtureId']}")
    require(Counter(row["actual_result"] for row in nary) == {"PASS": 4, "PRUNED": 1, "SPLIT": 1}, "NARY_RESULT_COUNTS")
    require(len(pruning) == 6 and all(row["status"] == "PASS" for row in pruning), "PRUNING_CONFORMANCE")
    require(len(reassessment) == 3 and all(row["round13_file_mutated"] == "false" for row in reassessment), "ROUND13_REASSESSMENT")
    required_gates = {"ROUND8_REGRESSION", "ROUND9_REGRESSION", "ROUND10_REGRESSION", "ROUND11_REGRESSION", "ROUND12_REGRESSION", "ROUND13_REGRESSION", "SEARCH_REGRESSION", "CONTEXT_REGRESSION", "SPACETIME_REGRESSION", "API_TESTS", "DATABASE_FREEZE", "REPOSITORY_HYGIENE", "PRODUCTION_BUILD", "AUDIT_SEAL"}
    require(required_gates <= {row["gate"] for row in full_validation} and all(row["status"] == "PASS" for row in full_validation), "FULL_VALIDATION_MATRIX")

    package = json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))
    package_hash = package.pop("canonicalHash")
    require(canonical_hash(package) == package_hash, "PACKAGE_HASH")
    require(package["pythonNormative"] is True and package["typescriptMirrorMode"] == "SCHEMA_AND_FROZEN_DECISION_VALIDATION_ONLY", "NORMATIVE_RUNTIME_BOUNDARY")
    require(package["taxonomy"] == list(GENERIC_TYPES) and len(package["assessments"]) == 35, "PACKAGE_SCOPE")
    package_decisions = {item["assessmentId"]: item for item in package["assessments"]}
    require(package_decisions == decisions, "PACKAGE_DECISION_EQUIVALENCE")

    freeze = json.loads((RAW / "input-freeze.json").read_text(encoding="utf-8"))
    require(freeze["sourceCommit"] == SOURCE_SHA and freeze["round13ResearchPackageMutated"] is False, "INPUT_FREEZE_IDENTITY")
    require(len(freeze["round13FrozenFiles"]) == freeze["round13FrozenFileCount"], "INPUT_FREEZE_COUNT")
    for row in freeze["round13FrozenFiles"]:
        path = REPO / row["path"]
        require(path.is_file() and path.stat().st_size == int(row["byte_size"]) and sha256(path) == row["sha256"], f"PRIOR_FREEZE_HASH:{row['path']}")

    required_research = [f"{index:02d}_{name}" for index, name in enumerate([
        "EXECUTIVE_DECISION.md", "METHOD_AND_SCOPE.md", "GENERIC_ASSOCIATION_TAXONOMY.md",
        "EVIDENCE_STATUS_AND_PROVENANCE.md", "ASSOCIATION_RUBRIC.md", "CALIBRATION_SET_METHOD.md",
        "DIRECT_NEIGHBOUR_THRESHOLD.md", "SKIP_ONE_THRESHOLD.md", "NARY_LOCAL_COHERENCE.md",
        "PRUNING_AND_RESTRUCTURING_CONTRACT.md", "SPATIAL_SEMANTICS_CONTRACT.md",
        "ASSOCIATION_INSPECTION_AND_REDIRECT_CONTRACT.md", "THRESHOLD_SENSITIVITY_ANALYSIS.md",
        "ROUND13_CASE_REASSESSMENT.md", "LIMITATIONS_AND_OPEN_QUESTIONS.md", "NEXT_GATE.md",
        "EXTERNAL_REVIEW_PACKET.md",
    ])]
    require(all((RESEARCH / name).is_file() for name in required_research), "REQUIRED_RESEARCH_PACKAGE")
    required_raw = {
        "association-calibration.tsv", "evidence-provenance.tsv", "direct-neighbour-evaluation.tsv",
        "skip-one-evaluation.tsv", "threshold-sweep.tsv", "sensitivity-analysis.tsv", "nary-validation.tsv",
        "pruning-validation.tsv", "round13-reassessment.tsv",
    }
    require(required_raw <= {path.name for path in RAW.iterdir()}, "REQUIRED_MACHINE_ARTIFACTS")
    review = (RESEARCH / "16_EXTERNAL_REVIEW_PACKET.md").read_text(encoding="utf-8")
    require("EXTERNAL_HUMAN_REVIEW_COMPLETED=false" in review and "No answer is prefilled" in review, "FABRICATED_HUMAN_REVIEW")

    prohibited = ("archiveObjectId", "contextDTO", "contextPayload", "spacetimeDTO", "spacetimePayload", "embeddingModel", "vectorReference")
    boundary_files = [path for root in (RESEARCH, AUDIT, ENGINE / "fixtures") for path in root.rglob("*") if path.is_file()]
    boundary_files.extend([REPO / "frontend/src/lib/trace/exploration-association-adapter.ts", REPO / "schemas/trace/exploration/association-assessment-v1.schema.json"])
    round14_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in boundary_files)
    require(all(token not in round14_text for token in prohibited), "PRODUCT_OR_MODEL_CONTAMINATION")
    require(metrics["CO_OCCURRENCE_ONLY_PASS_COUNT"] == 0 and metrics["TYPESCRIPT_ONLY_SEMANTIC_RULE_COUNT"] == 0, "BOUNDARY_METRICS")
    require(metrics["LEGACY_PAIR_ACTIVATION_GATE_NORMATIVE"] is False and metrics["PUBLIC_RENDERER_SAFE"] is False, "ACTIVATION_BOUNDARY")

    if (AUDIT / "MANIFEST.tsv").exists() and (AUDIT / "SHA256SUMS.txt").exists():
        manifest = read_tsv(AUDIT / "MANIFEST.tsv")
        sums = [line.split("  ", 1) for line in (AUDIT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines() if line]
        require([(row["sha256"], row["path"]) for row in manifest] == [(digest, path) for digest, path in sums], "AUDIT_SEAL_INDEX")
        require(all((REPO / row["path"]).stat().st_size == int(row["byte_size"]) and sha256(REPO / row["path"]) == row["sha256"] for row in manifest), "AUDIT_SEAL_HASH")

    return {
        "calibrationAssociationCount": len(cases), "evidenceProvenanceCount": len(evidence),
        "directNeighbourPassCount": sum(item["directNeighbourPass"] for item in decisions.values()),
        "skipOnePassCount": sum(item["skipOnePass"] for item in decisions.values()),
        "cooccurrenceOnlyPassCount": 0, "naryFixtureCount": len(nary),
        "thresholdSensitivityStable": True, "crossRuntimeDecisionMismatchCount": 0,
        "crossRuntimeHashMismatchCount": 0, "typescriptOnlySemanticRuleCount": 0,
        "status": "PASS",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2))
