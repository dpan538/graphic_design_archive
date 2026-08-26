#!/usr/bin/env python3
"""Exhaustive artifact validator for TRACE v49 Round 15."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
ENGINE = Path(__file__).resolve().parent
REPO = ENGINE.parents[1]
AUDIT = REPO / "docs/audits/v49-exploration-composition-engine-round1"
RAW = AUDIT / "raw"
RESEARCH = REPO / "docs/research/trace-v49-exploration-composition-engine-round1"
sys.path.insert(0, str(ENGINE))

from fixtures import FIXTURES  # noqa: E402
from model import METHOD_VERSION, TOPOLOGIES, canonical_hash, compose, load_frozen_input, validate_image  # noqa: E402


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> dict[str, Any]:
    frozen = load_frozen_input(REPO)
    images = [compose(fixture, frozen) for fixture in FIXTURES]
    for image in images:
        validate_image(image, frozen)
    results = read_tsv(RAW / "composition-fixture-results.tsv")
    require(len(results) == len(FIXTURES) and all(row["status"] == "PASS" for row in results), "COMPOSITION_FIXTURE_RESULTS")
    package = json.loads((RAW / "composition-decision-audit.json").read_text(encoding="utf-8"))
    package_hash = package.pop("canonical_hash")
    require(canonical_hash(package) == package_hash, "DECISION_AUDIT_HASH")
    require(package["python_normative"] is True and package["typescript_mirror_mode"] == "FROZEN_SEMANTIC_VALIDATION_AND_PRESENTATION_ONLY", "NORMATIVE_BOUNDARY")
    require(package["images"] == images, "GENERATED_IMAGE_EQUIVALENCE")

    topology = json.loads((RAW / "topology-arbitration-audit.json").read_text(encoding="utf-8"))
    topology_hash = topology.pop("canonical_hash")
    require(canonical_hash(topology) == topology_hash, "TOPOLOGY_AUDIT_HASH")
    require(topology["tree_strategy_topology_duplicate_count"] == 0 and set(topology["topology_signatures"]) == set(TOPOLOGIES), "TOPOLOGY_NON_DUPLICATION")
    semantic_hash = json.loads((RAW / "semantic-hash-audit.json").read_text(encoding="utf-8"))
    semantic_audit_hash = semantic_hash.pop("canonical_hash")
    require(canonical_hash(semantic_hash) == semantic_audit_hash, "SEMANTIC_HASH_AUDIT_HASH")
    require(semantic_hash["semantic_hash_nondeterminism_count"] == 0, "SEMANTIC_NONDETERMINISM")
    require(semantic_hash["failed_association_invariance_match"] and semantic_hash["duplicate_association_invariance_match"], "METAMORPHIC_INVARIANCE")
    require(all(all(value for key, value in row.items() if key != "fixture_id") for row in semantic_hash["cases"]), "HASH_SEPARATION")

    leakage = read_tsv(RAW / "visual-leakage-audit.tsv")
    require(len(leakage) == len(FIXTURES) * 8 and all(row["result"] == "PASS" and row["severity"] == "NONE" for row in leakage), "VISUAL_LEAKAGE")
    stress = read_tsv(RAW / "stress-results.tsv")
    require([int(row["node_count"]) for row in stress] == [5, 10, 20, 40], "STRESS_SIZES")
    require(all(row["deterministic"] == "true" and row["degree_explosion"] == "false" and int(row["largest_partition_node_count"]) <= 8 for row in stress), "STRESS_BOUND")

    metrics = json.loads((RAW / "quantitative-audit.json").read_text(encoding="utf-8"))
    zero_keys = {
        "FAILED_ASSOCIATION_LEAK_COUNT", "HARD_NEGATIVE_LEAK_COUNT", "UNSUPPORTED_RENDERED_EDGE_COUNT",
        "TYPED_HISTORICAL_RELATION_EMISSION_COUNT", "CAUSAL_RELATION_EMISSION_COUNT", "DIRECTIONAL_RELATION_EMISSION_COUNT",
        "SEMANTIC_HASH_NONDETERMINISM_COUNT", "INPUT_ORDER_MISMATCH_COUNT", "PAIR_ORIENTATION_MISMATCH_COUNT",
        "FAILED_ASSOCIATION_INVARIANCE_MISMATCH_COUNT", "VISUAL_LEAKAGE_CRITICAL_COUNT",
        "CROSS_RUNTIME_DECISION_MISMATCH_COUNT", "CROSS_RUNTIME_HASH_MISMATCH_COUNT", "TYPESCRIPT_ONLY_SEMANTIC_RULE_COUNT",
    }
    require(all(metrics[key] == 0 for key in zero_keys), "QUANTITATIVE_ZERO_GATE")
    require(metrics["QUALIFIED_ASSOCIATION_INPUT_COUNT"] == 21 and metrics["FAILED_ASSOCIATION_CONTROL_COUNT"] == 14 and metrics["HARD_NEGATIVE_CONTROL_COUNT"] == 10, "FROZEN_INPUT_COUNTS")
    topology_metric_keys = {
        "LINEAR_PATH": "TOPOLOGY_LINEAR_COUNT", "BINARY_FORK": "TOPOLOGY_BINARY_FORK_COUNT",
        "BINARY_CONVERGENCE": "TOPOLOGY_BINARY_CONVERGENCE_COUNT", "QUALIFIED_PATH": "TOPOLOGY_QUALIFIED_PATH_COUNT",
        "REFLEXIVE_RETURN": "TOPOLOGY_REFLEXIVE_RETURN_COUNT", "EVIDENCE_GAP_TREE": "TOPOLOGY_EVIDENCE_GAP_TREE_COUNT",
    }
    require(all(metrics[topology_metric_keys[topology]] >= 1 for topology in TOPOLOGIES), "TOPOLOGY_COVERAGE")
    require(metrics["PUBLIC_EXPLORATION_ROUTE_ADDED"] is False and metrics["PUBLIC_EXPLORATION_API_ADDED"] is False and metrics["PUBLIC_RENDERER_SAFE"] is False and metrics["DEPLOYED"] is False, "PRODUCT_BOUNDARY")
    require(metrics["ARCHIVE_OBJECT_REFERENCE_COUNT"] == metrics["CONTEXT_INPUT_REFERENCE_COUNT"] == metrics["SPACETIME_INPUT_REFERENCE_COUNT"] == 0, "FUTURE_INPUT_BOUNDARY")
    require(metrics["MODEL_DOWNLOAD_COUNT"] == metrics["EXTERNAL_MODEL_INFERENCE_COUNT"] == metrics["VECTOR_DATABASE_REFERENCE_COUNT"] == 0, "MODEL_BOUNDARY")

    freeze = json.loads((RAW / "input-freeze.json").read_text(encoding="utf-8"))
    require(freeze["source_sha"] == "cf4490e93449a46823a6de0c0676e431a7da6738", "SOURCE_SHA")
    require(freeze["round13_mutation_count"] == freeze["round14_mutation_count"] == 0, "FROZEN_INPUT_MUTATION")
    require(all(sha(REPO / row["path"]) == row["sha256"] for row in freeze["round13_files"] + freeze["round14_files"]), "FROZEN_INPUT_HASH")

    required_research = {
        "00_EXECUTIVE_DECISION.md", "01_RESEARCH_QUESTIONS.md", "02_VISUAL_EPISTEMOLOGY_REVIEW.md",
        "02_VISUAL_EPISTEMOLOGY_RESEARCH_MATRIX.tsv", "03_COMPOSITION_POLICY.md", "04_NEIGHBOURHOOD_GOVERNANCE.md",
        "05_TOPOLOGY_ARBITRATION.md", "06_PRUNING_AND_SPLIT_SEMANTICS.md", "07_EVIDENCE_GAP_POLICY.md",
        "08_SEMANTIC_PRESENTATION_BOUNDARY.md", "09_CONTEXT_SPACETIME_FUTURE_CONTRACT.md",
        "10_LIMITATIONS_AND_OPEN_QUESTIONS.md", "15_COMPOSITION_EXTERNAL_REVIEW_PACKET.md",
    }
    require(required_research <= {path.name for path in RESEARCH.iterdir() if path.is_file()}, "REQUIRED_RESEARCH_PACKAGE")
    required_raw = {
        "composition-fixture-results.tsv", "composition-decision-audit.json", "topology-arbitration-audit.json",
        "semantic-hash-audit.json", "visual-leakage-audit.tsv", "cross-runtime-composition-audit.json",
        "quantitative-audit.json", "stress-results.tsv", "input-freeze.json", "full-validation.tsv",
    }
    require(required_raw <= {path.name for path in RAW.iterdir()}, "REQUIRED_AUDIT_ARTIFACTS")
    matrix = read_tsv(RESEARCH / "02_VISUAL_EPISTEMOLOGY_RESEARCH_MATRIX.tsv")
    require(20 <= len(matrix) <= 35 and len({row["source_id"] for row in matrix}) == len(matrix), "VISUAL_RESEARCH_SOURCE_COUNT")
    review = (RESEARCH / "15_COMPOSITION_EXTERNAL_REVIEW_PACKET.md").read_text(encoding="utf-8")
    require("EXTERNAL_HUMAN_DOMAIN_REVIEW_COMPLETED=false" in review and all(value in review for value in ("APPROVE", "APPROVE_WITH_QUALIFICATION", "REVISE", "REJECT", "UNCERTAIN")), "HUMAN_REVIEW_BOUNDARY")

    schemas = [
        REPO / "schemas/trace/exploration/bounded-semantic-image-v1.schema.json",
        REPO / "schemas/trace/exploration/composition-decision-v1.schema.json",
        REPO / "schemas/trace/exploration/composition-audit-v1.schema.json",
    ]
    for path in schemas:
        schema = json.loads(path.read_text(encoding="utf-8"))
        require(schema["$schema"] == "https://json-schema.org/draft/2020-12/schema" and schema["additionalProperties"] is False, f"SCHEMA_STRICTNESS:{path.name}")

    cross_runtime = json.loads((RAW / "cross-runtime-composition-audit.json").read_text(encoding="utf-8"))
    require(cross_runtime["status"] == "PASS" and cross_runtime["crossRuntimeDecisionMismatchCount"] == 0 and cross_runtime["crossRuntimeHashMismatchCount"] == 0 and cross_runtime["typescriptOnlySemanticRuleCount"] == 0, "CROSS_RUNTIME_GATE")
    full_validation = read_tsv(RAW / "full-validation.tsv")
    required_gates = {f"ROUND{index}_REGRESSION" for index in range(8, 15)} | {"SEARCH_REGRESSION", "CONTEXT_REGRESSION", "SPACETIME_REGRESSION", "API_TESTS", "DATABASE_FREEZE", "REPOSITORY_HYGIENE", "TYPECHECK", "PRODUCTION_BUILD", "AUDIT_SEAL"}
    require(required_gates <= {row["gate"] for row in full_validation} and all(row["status"] == "PASS" for row in full_validation), "FULL_VALIDATION_MATRIX")

    manifest = read_tsv(AUDIT / "MANIFEST.tsv")
    sums = [line.split("  ", 1) for line in (AUDIT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines() if line]
    require([(row["sha256"], row["path"]) for row in manifest] == [(digest, path) for digest, path in sums], "AUDIT_SEAL_INDEX")
    require(all((REPO / row["path"]).stat().st_size == int(row["byte_size"]) and sha(REPO / row["path"]) == row["sha256"] for row in manifest), "AUDIT_SEAL_HASH")

    return {
        "status": "PASS", "compositionFixtureCount": len(images), "methodVersion": METHOD_VERSION,
        "qualifiedAssociationInputCount": 21, "failedAssociationControlCount": 14,
        "semanticMismatchCount": 0, "visualLeakageCriticalCount": 0,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2))
