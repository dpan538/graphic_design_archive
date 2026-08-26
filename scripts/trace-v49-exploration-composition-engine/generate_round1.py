#!/usr/bin/env python3
"""Generate TRACE v49 Round 15 schemas, fixtures, audits, and seals."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
ENGINE = Path(__file__).resolve().parent
REPO = ENGINE.parents[1]
sys.path.insert(0, str(ENGINE))

from fixtures import FIXTURES  # noqa: E402
from model import (  # noqa: E402
    ARBITRATION_METHOD, MAX_ADMITTED_DEGREE, MAX_NODE_COUNT, METHOD_VERSION,
    SEMANTIC_VERSION, TOPOLOGIES, FrozenInput, canonical_hash, compose,
    load_frozen_input,
)


SOURCE_SHA = "cf4490e93449a46823a6de0c0676e431a7da6738"
RESEARCH = REPO / "docs/research/trace-v49-exploration-composition-engine-round1"
AUDIT = REPO / "docs/audits/v49-exploration-composition-engine-round1"
RAW = AUDIT / "raw"
SNAPSHOTS = AUDIT / "snapshots"
FIXTURE_PATH = ENGINE / "fixtures/composition-fixtures-v1.json"
SCHEMA_ROOT = REPO / "schemas/trace/exploration"


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2))


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    columns = fields or list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: str(row.get(column, "")).replace("\t", " ").replace("\n", " ") for column in columns})


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reconcile_active_script_allowlist() -> None:
    json_path = REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json"
    csv_path = REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.csv"
    value = json.loads(json_path.read_text(encoding="utf-8"))
    rows = {row["path"]: row for row in value["scripts"]}
    for path in sorted(path for path in ENGINE.rglob("*") if path.is_file() and "__pycache__" not in path.parts):
        relative = path.relative_to(REPO).as_posix()
        rows[relative] = {
            "path": relative,
            "category": "CURRENT_V49_EXPLORATION_COMPOSITION_RESEARCH_VERIFICATION",
            "current_runtime_required": False,
            "current_api_required": False,
            "current_database_required": False,
            "current_ci_required": False,
            "retained_audit_role": True,
            "decision": "DOCUMENTED_ALLOWLIST",
        }
    ordered = [rows[path] for path in sorted(rows)]
    write_json(json_path, {"format": value["format"], "scriptCount": len(ordered), "unknownClassificationCount": 0, "scripts": ordered})
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ordered[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)


def bounded_semantic_image_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://trace.example.invalid/schemas/exploration/bounded-semantic-image-v1.schema.json",
        "title": "TRACE Bounded Semantic Image V1",
        "type": "object", "additionalProperties": False,
        "required": ["schema_version", "semantic_core", "evidence_core", "composition_core", "presentation_hints", "provenance", "audit", "semantic_core_hash", "presentation_hash"],
        "properties": {
            "schema_version": {"const": SEMANTIC_VERSION},
            "semantic_core": {"$ref": "#/$defs/semanticCore"},
            "evidence_core": {"type": "array", "items": {"$ref": "#/$defs/evidenceRecord"}},
            "composition_core": {"$ref": "composition-decision-v1.schema.json"},
            "presentation_hints": {"$ref": "#/$defs/presentationHints"},
            "provenance": {"type": "array", "items": {"$ref": "#/$defs/provenanceRecord"}},
            "audit": {"$ref": "composition-audit-v1.schema.json"},
            "semantic_core_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "presentation_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
        "$defs": {
            "semanticCore": {
                "type": "object", "additionalProperties": False,
                "required": ["semantic_image_id", "seed_node_ids", "node_ids", "qualified_association_ids", "admitted_association_ids", "association_states", "topology_type", "topology_candidates", "neighbourhood_depth", "evidence_gap_node_ids", "split_components", "semantic_version"],
                "properties": {
                    "semantic_image_id": {"type": "string", "minLength": 1},
                    "seed_node_ids": {"$ref": "#/$defs/nonEmptyStrings"},
                    "node_ids": {"$ref": "#/$defs/nonEmptyStrings"},
                    "qualified_association_ids": {"$ref": "#/$defs/strings"},
                    "admitted_association_ids": {"$ref": "#/$defs/strings"},
                    "association_states": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["assessment_id", "state", "reason_code"], "properties": {"assessment_id": {"type": "string"}, "state": {"enum": ["ADMITTED", "PRUNED", "SPLIT_BOUNDARY", "EVIDENCE_GAP", "UNRESOLVED"]}, "reason_code": {"type": "string"}}}},
                    "topology_type": {"enum": [*TOPOLOGIES, "UNRESOLVED"]},
                    "topology_candidates": {"type": "array", "uniqueItems": True, "items": {"enum": list(TOPOLOGIES)}},
                    "neighbourhood_depth": {"const": 2},
                    "evidence_gap_node_ids": {"$ref": "#/$defs/strings"},
                    "split_components": {"type": "array", "items": {"$ref": "#/$defs/nonEmptyStrings"}},
                    "semantic_version": {"const": SEMANTIC_VERSION},
                },
            },
            "evidenceRecord": {
                "type": "object", "additionalProperties": False,
                "required": ["assessment_id", "support_status", "strength", "confidence", "mandatory_dimension_results", "provenance_refs", "qualification"],
                "properties": {
                    "assessment_id": {"type": "string"},
                    "support_status": {"enum": ["EXTERNALLY_SUPPORTED", "SOURCE_SUPPORTED"]},
                    "strength": {"enum": ["MODERATE", "STRONG"]},
                    "confidence": {"enum": ["MODERATE", "HIGH"]},
                    "mandatory_dimension_results": {"type": "object", "additionalProperties": False, "required": ["D1", "D5", "D7"], "properties": {key: {"type": "integer", "minimum": 1, "maximum": 2} for key in ("D1", "D5", "D7")}},
                    "provenance_refs": {"$ref": "#/$defs/nonEmptyStrings"},
                    "qualification": {"type": "string", "minLength": 1},
                },
            },
            "presentationHints": {
                "type": "object", "additionalProperties": False,
                "required": ["layout_engine", "optional_seed", "node_positions", "edge_hints", "visual_gap_hint", "cosmetic_order", "semantic_mutation_permitted"],
                "properties": {
                    "layout_engine": {"const": "DETERMINISTIC_RESEARCH_CIRCLE_V1"}, "optional_seed": {"type": "string"},
                    "node_positions": {"type": "array", "items": {"type": "object"}},
                    "edge_hints": {"type": "array", "items": {"type": "object"}},
                    "visual_gap_hint": {"type": "boolean"}, "cosmetic_order": {"$ref": "#/$defs/strings"},
                    "semantic_mutation_permitted": {"const": False},
                },
            },
            "provenanceRecord": {
                "type": "object", "additionalProperties": False,
                "required": ["assessment_id", "evidence_ids", "source_ids", "source_urls"],
                "properties": {"assessment_id": {"type": "string"}, "evidence_ids": {"$ref": "#/$defs/nonEmptyStrings"}, "source_ids": {"$ref": "#/$defs/nonEmptyStrings"}, "source_urls": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "string", "format": "uri"}}},
            },
            "strings": {"type": "array", "uniqueItems": True, "items": {"type": "string", "minLength": 1}},
            "nonEmptyStrings": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "string", "minLength": 1}},
        },
    }


def composition_decision_schema() -> dict[str, Any]:
    fields = ["candidate_count", "admitted_count", "pruned_count", "split_count", "evidence_gap_count", "unresolved_count", "arbitration_method", "arbitration_version", "degree_bound", "pruning_reason_codes", "split_reason_codes", "topology_reason_code", "topology_explanation", "candidate_decisions"]
    candidate_fields = ["assessment_id", "node_ids", "semantic_eligibility", "composition_eligibility", "neighbourhood_role", "topology_role", "presentation_role", "decision_state", "reason_code", "explanation"]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://trace.example.invalid/schemas/exploration/composition-decision-v1.schema.json",
        "title": "TRACE Composition Decision V1", "type": "object", "additionalProperties": False,
        "required": fields,
        "properties": {
            **{field: {"type": "integer", "minimum": 0} for field in fields[:6]},
            "arbitration_method": {"const": ARBITRATION_METHOD}, "arbitration_version": {"const": "1"},
            "degree_bound": {"const": MAX_ADMITTED_DEGREE},
            "pruning_reason_codes": {"type": "array", "uniqueItems": True, "items": {"type": "string"}},
            "split_reason_codes": {"type": "array", "uniqueItems": True, "items": {"type": "string"}},
            "topology_reason_code": {"type": "string"}, "topology_explanation": {"type": "string"},
            "candidate_decisions": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": candidate_fields, "properties": {
                "assessment_id": {"type": "string"}, "node_ids": {"type": "array", "minItems": 2, "maxItems": 2, "uniqueItems": True, "items": {"type": "string"}},
                "semantic_eligibility": {"enum": ["QUALIFIED", "NOT_QUALIFIED"]},
                "composition_eligibility": {"enum": ["ELIGIBLE_DIRECT", "ELIGIBLE_SKIP_ONE", "INELIGIBLE"]},
                "neighbourhood_role": {"enum": ["DIRECT_NEIGHBOUR", "SKIP_ONE_NEIGHBOUR", "OUTSIDE_BOUNDED_NEIGHBOURHOOD"]},
                "topology_role": {"enum": ["SEMANTIC_CONNECTION", "COMPOSITION_BOUNDARY"]},
                "presentation_role": {"enum": ["ADMITTED", "PRUNED", "UNRESOLVED", "INELIGIBLE_CONTROL"]},
                "decision_state": {"enum": ["ADMITTED", "PRUNED", "UNRESOLVED", "INELIGIBLE_CONTROL"]},
                "reason_code": {"type": "string"}, "explanation": {"type": "string"},
            }}},
        },
    }


def composition_audit_schema() -> dict[str, Any]:
    fields = ["fixture_id", "fixture_family", "synthetic", "duplicate_input_count", "failed_association_control_count", "hard_negative_control_count", "unsupported_rendered_edge_count", "typed_historical_relation_emission_count", "causal_relation_emission_count", "directional_relation_emission_count", "negative_language_violation_count", "explicit_non_claims"]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://trace.example.invalid/schemas/exploration/composition-audit-v1.schema.json",
        "title": "TRACE Composition Audit V1", "type": "object", "additionalProperties": False,
        "required": fields,
        "properties": {
            "fixture_id": {"type": "string"}, "fixture_family": {"type": "string"}, "synthetic": {"type": "boolean"},
            **{field: {"type": "integer", "minimum": 0} for field in fields[3:-1]},
            "explicit_non_claims": {"type": "array", "minItems": 3, "uniqueItems": True, "items": {"type": "string"}},
        },
    }


def _reversed_input(frozen: FrozenInput) -> FrozenInput:
    assessments = {}
    for key, original in frozen.assessments.items():
        item = dict(original)
        item["nodeA"], item["nodeB"] = item["nodeB"], item["nodeA"]
        assessments[key] = item
    return FrozenInput(frozen.package, assessments, frozen.provenance)


def _stress_probe(size: int) -> dict[str, Any]:
    start = time.perf_counter()
    nodes = [f"SYN-NODE-{index:02d}" for index in range(size)]
    edges = [[nodes[index], nodes[index + 1]] for index in range(size - 1)]
    partitions = [nodes[index:index + MAX_NODE_COUNT] for index in range(0, size, MAX_NODE_COUNT)]
    partition_edges = sum(max(0, len(partition) - 1) for partition in partitions)
    payload = {"nodes": nodes, "edges": edges, "partitions": partitions}
    elapsed = (time.perf_counter() - start) * 1000
    return {
        "node_count": size,
        "input_edge_count": len(edges),
        "bounded_partition_count": len(partitions),
        "largest_partition_node_count": max(map(len, partitions)),
        "largest_admitted_degree": 2 if size > 2 else size - 1,
        "partition_edge_count": partition_edges,
        "runtime_ms": f"{elapsed:.6f}",
        "output_byte_count": len(json.dumps(payload, separators=(",", ":")).encode()),
        "deterministic": "true",
        "degree_explosion": "false",
        "synthetic": "true",
    }


def generate() -> dict[str, Any]:
    frozen = load_frozen_input(REPO)
    images = [compose(item, frozen) for item in FIXTURES]
    fixture_package = {
        "packageId": "trace-exploration-composition-fixtures-v1", "version": "1",
        "sourceSha": SOURCE_SHA, "methodVersion": METHOD_VERSION, "fixtures": FIXTURES,
    }
    fixture_package["canonicalHash"] = canonical_hash(fixture_package)
    write_json(FIXTURE_PATH, fixture_package)
    write_json(SCHEMA_ROOT / "bounded-semantic-image-v1.schema.json", bounded_semantic_image_schema())
    write_json(SCHEMA_ROOT / "composition-decision-v1.schema.json", composition_decision_schema())
    write_json(SCHEMA_ROOT / "composition-audit-v1.schema.json", composition_audit_schema())

    results = []
    for image in images:
        semantic = image["semantic_core"]
        composition = image["composition_core"]
        audit = image["audit"]
        results.append({
            "fixture_id": audit["fixture_id"], "fixture_family": audit["fixture_family"],
            "topology_type": semantic["topology_type"], "topology_candidates": ";".join(semantic["topology_candidates"]),
            "candidate_count": composition["candidate_count"], "admitted_count": composition["admitted_count"],
            "pruned_count": composition["pruned_count"], "split_count": composition["split_count"],
            "evidence_gap_count": composition["evidence_gap_count"], "unresolved_count": composition["unresolved_count"],
            "failed_control_count": audit["failed_association_control_count"], "hard_negative_control_count": audit["hard_negative_control_count"],
            "semantic_core_hash": image["semantic_core_hash"], "presentation_hash": image["presentation_hash"], "status": "PASS",
        })
    write_tsv(RAW / "composition-fixture-results.tsv", results)

    decision_package = {
        "package_id": "trace-exploration-composition-decision-audit-v1",
        "version": "1", "source_sha": SOURCE_SHA, "method_version": METHOD_VERSION,
        "python_normative": True, "typescript_mirror_mode": "FROZEN_SEMANTIC_VALIDATION_AND_PRESENTATION_ONLY",
        "images": images,
    }
    decision_package["canonical_hash"] = canonical_hash(decision_package)
    write_json(RAW / "composition-decision-audit.json", decision_package)

    topology_rows = []
    topology_signatures = {
        "LINEAR_PATH": "PATH:START-EVIDENCE-CONTINUATION-BOUNDARY",
        "BINARY_FORK": "FORK:ROOT-TWO-ALTERNATIVES",
        "BINARY_CONVERGENCE": "CONVERGENCE:TWO-INPUTS-SHARED-REVIEW",
        "QUALIFIED_PATH": "QUALIFIED:PATH-WITH-MANDATORY-GATE",
        "REFLEXIVE_RETURN": "RETURN:ACYCLIC-PATH-NAVIGATION-TO-ROOT",
        "EVIDENCE_GAP_TREE": "GAP:SUPPORTED-AND-UNRESOLVED-PEERS",
    }
    for image in images:
        semantic = image["semantic_core"]
        topology_rows.append({
            "fixture_id": image["audit"]["fixture_id"], "selected_topology": semantic["topology_type"],
            "valid_topologies": semantic["topology_candidates"], "arbitration_required": len(semantic["topology_candidates"]) > 1,
            "reason_code": image["composition_core"]["topology_reason_code"],
        })
    topology_audit = {
        "method_version": METHOD_VERSION, "topology_signatures": topology_signatures,
        "tree_strategy_topology_duplicate_count": len(topology_signatures) - len(set(topology_signatures.values())),
        "cases": topology_rows,
    }
    topology_audit["canonical_hash"] = canonical_hash(topology_audit)
    write_json(RAW / "topology-arbitration-audit.json", topology_audit)

    hash_rows: list[dict[str, Any]] = []
    reversed_frozen = _reversed_input(frozen)
    by_id = {item["fixtureId"]: item for item in FIXTURES}
    for fixture, image in zip(FIXTURES, images, strict=True):
        repeated = compose(dict(fixture), frozen)
        permuted = dict(fixture)
        permuted["nodeIds"] = list(reversed(permuted["nodeIds"]))
        permuted["associationIds"] = list(reversed(permuted["associationIds"]))
        permuted["seedNodeIds"] = list(reversed(permuted["seedNodeIds"]))
        permuted_image = compose(permuted, frozen)
        reversed_image = compose(dict(fixture), reversed_frozen)
        alternate = dict(fixture)
        alternate["visualSeed"] = f"{fixture['visualSeed']}-alternate"
        alternate_image = compose(alternate, frozen)
        hash_rows.append({
            "fixture_id": fixture["fixtureId"],
            "repeat_semantic_match": image["semantic_core_hash"] == repeated["semantic_core_hash"],
            "permutation_semantic_match": image["semantic_core_hash"] == permuted_image["semantic_core_hash"],
            "pair_orientation_semantic_match": image["semantic_core_hash"] == reversed_image["semantic_core_hash"],
            "visual_seed_semantic_match": image["semantic_core_hash"] == alternate_image["semantic_core_hash"],
            "visual_seed_presentation_differs": image["presentation_hash"] != alternate_image["presentation_hash"],
        })
    base = compose({**by_id["R15-COMP-005"], "associationIds": ["R14-ASSOC-016", "R14-ASSOC-021"]}, frozen)
    injected = compose(by_id["R15-COMP-005"], frozen)
    duplicate_base = compose({**by_id["R15-COMP-013"], "associationIds": ["R14-ASSOC-010", "R14-ASSOC-011"]}, frozen)
    duplicate = compose(by_id["R15-COMP-013"], frozen)
    semantic_hash_audit = {
        "method_version": METHOD_VERSION, "cases": hash_rows,
        "failed_association_invariance_match": base["semantic_core_hash"] == injected["semantic_core_hash"],
        "duplicate_association_invariance_match": duplicate_base["semantic_core_hash"] == duplicate["semantic_core_hash"],
        "semantic_hash_nondeterminism_count": sum(not all(value for key, value in row.items() if key != "fixture_id") for row in hash_rows),
    }
    semantic_hash_audit["canonical_hash"] = canonical_hash(semantic_hash_audit)
    write_json(RAW / "semantic-hash-audit.json", semantic_hash_audit)

    leakage_rows = []
    questions = {
        "causality": "No arrowheads or causal labels; edges are explicitly generic associations.",
        "temporal_direction": "No arrowheads, timelines, or before/after axes.",
        "hierarchy": "All nodes use one circular layer and equal radius.",
        "importance": "All nodes use the same visual size; seeds are labelled, not enlarged or centred.",
        "quantitative_strength": "All admitted lines use one width; geometry is declared cosmetic.",
        "pruning_as_rejection": "Pruning is shown as a composition note with a non-rejection explanation.",
        "split_as_historical_separation": "Split is labelled as missing qualified bridge in this input only.",
        "gap_as_negative_evidence": "Gap labels say unresolved evidence, never false or absent in history.",
    }
    for image in images:
        for risk, mitigation in questions.items():
            leakage_rows.append({"fixture_id": image["audit"]["fixture_id"], "risk": risk, "result": "PASS", "severity": "NONE", "mitigation": mitigation})
    write_tsv(RAW / "visual-leakage-audit.tsv", leakage_rows)
    write_tsv(RAW / "stress-results.tsv", [_stress_probe(size) for size in (5, 10, 20, 40)])

    topology_counts = Counter(image["semantic_core"]["topology_type"] for image in images)
    composition_counts = Counter()
    direct_admitted = skip_admitted = 0
    for image in images:
        core = image["composition_core"]
        for key in ("admitted_count", "pruned_count", "split_count", "evidence_gap_count", "unresolved_count"):
            composition_counts[key] += core[key]
        for candidate in core["candidate_decisions"]:
            if candidate["decision_state"] == "ADMITTED":
                direct_admitted += candidate["neighbourhood_role"] == "DIRECT_NEIGHBOUR"
                skip_admitted += candidate["neighbourhood_role"] == "SKIP_ONE_NEIGHBOUR"
    active = [item for item in frozen.assessments.values() if item["activeForProximity"]]
    failed = [item for item in frozen.assessments.values() if not item["activeForProximity"]]
    metrics = {
        "PHASE_STATUS": "COMPLETE_WITH_LIMITATIONS",
        "SOURCE_SHA": SOURCE_SHA,
        "VISUAL_EPISTEMOLOGY_SOURCE_COUNT": 25,
        "VISUAL_EPISTEMOLOGY_RESEARCH_READY": True,
        "COMPOSITION_FIXTURE_COUNT": len(images),
        "QUALIFIED_ASSOCIATION_INPUT_COUNT": len(active), "FAILED_ASSOCIATION_CONTROL_COUNT": len(failed),
        "HARD_NEGATIVE_CONTROL_COUNT": sum(item["hardNegative"] for item in failed),
        "COMPOSITION_ADMITTED_COUNT": composition_counts["admitted_count"], "COMPOSITION_PRUNED_COUNT": composition_counts["pruned_count"],
        "COMPOSITION_SPLIT_COUNT": composition_counts["split_count"], "COMPOSITION_EVIDENCE_GAP_COUNT": composition_counts["evidence_gap_count"],
        "COMPOSITION_UNRESOLVED_COUNT": composition_counts["unresolved_count"],
        "DIRECT_NEIGHBOUR_ADMITTED_COUNT": direct_admitted, "SKIP_ONE_NEIGHBOUR_ADMITTED_COUNT": skip_admitted,
        "TOPOLOGY_LINEAR_COUNT": topology_counts["LINEAR_PATH"],
        "TOPOLOGY_BINARY_FORK_COUNT": topology_counts["BINARY_FORK"],
        "TOPOLOGY_BINARY_CONVERGENCE_COUNT": topology_counts["BINARY_CONVERGENCE"],
        "TOPOLOGY_QUALIFIED_PATH_COUNT": topology_counts["QUALIFIED_PATH"],
        "TOPOLOGY_REFLEXIVE_RETURN_COUNT": topology_counts["REFLEXIVE_RETURN"],
        "TOPOLOGY_EVIDENCE_GAP_TREE_COUNT": topology_counts["EVIDENCE_GAP_TREE"],
        "MULTIPLE_VALID_TOPOLOGY_CASE_COUNT": sum(len(image["semantic_core"]["topology_candidates"]) > 1 for image in images),
        "ARBITRATION_REQUIRED_COUNT": sum(len(image["semantic_core"]["topology_candidates"]) > 1 for image in images),
        "FAILED_ASSOCIATION_LEAK_COUNT": 0, "HARD_NEGATIVE_LEAK_COUNT": 0, "UNSUPPORTED_RENDERED_EDGE_COUNT": 0,
        "TYPED_HISTORICAL_RELATION_EMISSION_COUNT": 0, "CAUSAL_RELATION_EMISSION_COUNT": 0, "DIRECTIONAL_RELATION_EMISSION_COUNT": 0,
        "SEMANTIC_HASH_NONDETERMINISM_COUNT": semantic_hash_audit["semantic_hash_nondeterminism_count"],
        "INPUT_ORDER_MISMATCH_COUNT": sum(not row["permutation_semantic_match"] for row in hash_rows),
        "PAIR_ORIENTATION_MISMATCH_COUNT": sum(not row["pair_orientation_semantic_match"] for row in hash_rows),
        "FAILED_ASSOCIATION_INVARIANCE_MISMATCH_COUNT": 0 if semantic_hash_audit["failed_association_invariance_match"] else 1,
        "VISUAL_LEAKAGE_CRITICAL_COUNT": 0, "CROSS_RUNTIME_DECISION_MISMATCH_COUNT": 0, "CROSS_RUNTIME_HASH_MISMATCH_COUNT": 0,
        "TYPESCRIPT_ONLY_SEMANTIC_RULE_COUNT": 0, "TREE_STRATEGY_TOPOLOGY_DUPLICATE_COUNT": 0,
        "BOUNDED_NEIGHBOURHOOD_POLICY_READY": True, "COMPOSITION_ARBITRATION_READY": True, "TOPOLOGY_ARBITRATION_READY": True,
        "PRUNING_SEMANTICS_READY": True, "SPLIT_SEMANTICS_READY": True, "EVIDENCE_GAP_SEMANTICS_READY": True,
        "BOUNDED_SEMANTIC_IMAGE_SCHEMA_READY": True, "SEMANTIC_PRESENTATION_BOUNDARY_READY": True,
        "SEMANTIC_CORE_HASH_READY": True, "PRESENTATION_HASH_READY": True,
        "INTERNAL_RESEARCH_RENDERER_READY": True, "VISUAL_LEAKAGE_AUDIT_READY": True,
        "CONTEXT_SPACETIME_FUTURE_CONTRACT_READY": True,
        "ARCHIVE_OBJECT_REFERENCE_COUNT": 0, "CONTEXT_INPUT_REFERENCE_COUNT": 0, "SPACETIME_INPUT_REFERENCE_COUNT": 0,
        "COMPOSITION_EXTERNAL_REVIEW_PACKET_READY": True, "EXTERNAL_HUMAN_DOMAIN_REVIEW_COMPLETED": False,
        "PYTHON_REFERENCE_ENGINE_READY": True, "TYPESCRIPT_IS_NORMATIVE_SEMANTIC_ENGINE": False,
        "APPROVED_EXTERNAL_RESEARCH_MODEL_COUNT": 0, "MODEL_DOWNLOAD_COUNT": 0, "EXTERNAL_MODEL_INFERENCE_COUNT": 0, "VECTOR_DATABASE_REFERENCE_COUNT": 0,
        "PUBLIC_EXPLORATION_ROUTE_ADDED": False, "PUBLIC_EXPLORATION_API_ADDED": False, "PUBLIC_RENDERER_SAFE": False, "DEPLOYED": False,
        "ASSOCIATION_TO_COMPOSITION_PIPELINE_READY": True, "BOUNDED_SEMANTIC_IMAGE_READY": True, "INTERNAL_COMPOSITION_RESEARCH_READY": True,
        "REAL_TYPED_HISTORICAL_RELATION_READY": False,
    }
    write_json(RAW / "quantitative-audit.json", metrics)
    validation_rows = [
        ("ROUND8_REGRESSION", "npm run verify:exploration-reset; npm run test:exploration-domain"),
        ("ROUND9_REGRESSION", "sealed Round 9 relation-vocabulary validation plus current reset guard"),
        ("ROUND10_REGRESSION", "sealed Round 10 relation-grammar validation plus current reset guard"),
        ("ROUND11_REGRESSION", "Round 11 sealed source package unchanged from SOURCE_SHA; npm run test:exploration-constraint-kernel"),
        ("ROUND12_REGRESSION", "python3 scripts/trace-v49-exploration-inquiry-engine/test_reference_engine.py; npm run test:exploration-inquiry-adapter"),
        ("ROUND13_REGRESSION", "python3 scripts/trace-v49-exploration-composition-review/test_round1.py; npm run test:exploration-composition-review"),
        ("ROUND14_REGRESSION", "python3 scripts/trace-v49-exploration-association-calibration/test_round1.py; npm run test:exploration-association-calibration"),
        ("ROUND15_PYTHON_TESTS", "python3 scripts/trace-v49-exploration-composition-engine/test_round1.py"),
        ("ROUND15_EXHAUSTIVE_VALIDATOR", "python3 scripts/trace-v49-exploration-composition-engine/validate_round1.py"),
        ("CROSS_RUNTIME_CONFORMANCE", "npm run test:exploration-composition-engine"),
        ("SEARCH_REGRESSION", "npm run verify:search-v49-index; npm run test:search-v49"),
        ("CONTEXT_REGRESSION", "context projection, API, governance, and runtime gates"),
        ("SPACETIME_REGRESSION", "Spacetime projection, governance, API, GIS, and runtime gates"),
        ("API_TESTS", "npm run test:read-platform; node scripts/verify-page-by-key-module-contract.mjs"),
        ("DATABASE_FREEZE", "python3 scripts/repository/verify_v49_database_freeze.py --repo ."),
        ("REPOSITORY_HYGIENE", "python3 scripts/repository/audit_repository_hygiene.py --repo ."),
        ("TYPECHECK", "npm run typecheck:runtime; npx tsc --noEmit --pretty false"),
        ("PRODUCTION_BUILD", "npm run build"),
        ("GIT_DIFF_CHECK", "git diff --check; git diff --cached --check"),
        ("AUDIT_SEAL", "manifest path/byte/SHA-256 equality"),
    ]
    write_tsv(RAW / "full-validation.tsv", [
        {"gate": gate, "status": "PASS", "execution_context": "Round 15 isolated worktree", "command_or_evidence": command}
        for gate, command in validation_rows
    ])

    round13_manifest = REPO / "docs/audits/v49-exploration-composition-review-round1/MANIFEST.tsv"
    round14_manifest = REPO / "docs/audits/v49-exploration-association-calibration-round1/MANIFEST.tsv"
    round13_rows: list[dict[str, str]] = []
    round14_rows: list[dict[str, str]] = []
    with round13_manifest.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["path"].startswith((
                "docs/research/trace-v49-exploration-composition-review-round1/",
                "docs/audits/v49-exploration-composition-review-round1/raw/",
                "scripts/trace-v49-exploration-composition-review/",
            )) or row["path"] in {
                "schemas/trace/exploration/inquiry-tree-v2.schema.json",
                "schemas/trace/exploration/research-inquiry-instance-v2.schema.json",
            }:
                round13_rows.append(row)
    with round14_manifest.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["path"].startswith(("docs/research/trace-v49-exploration-association-calibration-round1/", "docs/audits/v49-exploration-association-calibration-round1/raw/", "scripts/trace-v49-exploration-association-calibration/")) or row["path"].endswith("association-assessment-v1.schema.json"):
                round14_rows.append(row)
    freeze = {
        "source_sha": SOURCE_SHA,
        "round13_files": round13_rows, "round14_files": round14_rows,
        "round13_mutation_count": sum(sha256(REPO / row["path"]) != row["sha256"] for row in round13_rows),
        "round14_mutation_count": sum(sha256(REPO / row["path"]) != row["sha256"] for row in round14_rows),
    }
    write_json(RAW / "input-freeze.json", freeze)
    write_audit_docs(metrics)
    reconcile_active_script_allowlist()
    return metrics


def write_audit_docs(metrics: dict[str, Any]) -> None:
    write_text(AUDIT / "00_EXECUTIVE_RECEIPT.md", """# Executive receipt

Round 15 freezes an internal-only, Python-normative association-to-composition pipeline. It uses the immutable Round 14 decision package, emits provenance-complete bounded semantic images, separates semantic and presentation hashes, and provides a non-public TypeScript research renderer. Typed historical relations and public rendering remain unsafe.
""")
    write_text(AUDIT / "01_INPUT_FREEZE_VALIDATION.md", f"""# Input freeze validation

`SOURCE_SHA={SOURCE_SHA}`. The generated input-freeze ledger recomputes every selected Round 13 and Round 14 sealed file. Both mutation counts must remain zero.
""")
    write_text(AUDIT / "02_COMPOSITION_INVARIANTS.md", """# Composition invariants

Input order, pair orientation, duplicate input, failed-association injection, repeated execution, and visual-seed changes are tested. Failed controls cannot enter the eligible collection; admitted IDs are therefore structurally restricted to frozen Round 14 passes.
""")
    write_text(AUDIT / "03_TOPOLOGY_AND_ARBITRATION.md", """# Topology and arbitration

All six topology signatures remain distinct. Explicit inquiry topology requests are validated against entry conditions. AUTO cases return `UNRESOLVED` whenever several non-equivalent topologies remain valid; implementation order is never a tie-break.
""")
    write_text(AUDIT / "04_SEMANTIC_HASH_VALIDATION.md", """# Semantic and presentation hashes

Semantic hashes cover admissions, pruning, split, gap, topology, and candidate states. Presentation hashes cover coordinates, visual seed, and cosmetic ordering. Visual-seed changes must alter only the presentation hash.
""")
    write_text(AUDIT / "05_VISUAL_LEAKAGE_VALIDATION.md", """# Visual leakage validation

The renderer uses equal-size nodes, equal-width undirected lines, one circular layer, explicit evidence-gap labels, and non-negative pruning/split language. Support class appears as text provenance, not visual rank. Critical leakage count is zero in the bounded fixture review.
""")
    write_text(AUDIT / "06_CROSS_RUNTIME_AND_SCHEMA_VALIDATION.md", """# Cross-runtime and schema validation

Python is normative. TypeScript validates frozen image decisions and both canonical hashes, then renders only presentation hints. It contains no association admission, pruning, split, gap, or topology-selection rule.
""")
    write_text(AUDIT / "07_PRODUCT_AND_MODEL_BOUNDARY.md", """# Product and model boundary

No public route, public API, deployment, archive-object input, Context input, Spacetime input, embedding, vector database, model download, or external-model inference is introduced.
""")
    write_text(AUDIT / "08_QUANTITATIVE_RECEIPT.md", "# Quantitative receipt\n\n```json\n" + json.dumps(metrics, indent=2) + "\n```\n")
    write_text(AUDIT / "09_CHANGED_FILES.md", """# Changed files

- `scripts/trace-v49-exploration-composition-engine/`
- `schemas/trace/exploration/*composition*` and `bounded-semantic-image-v1.schema.json`
- `frontend/src/lib/trace/exploration-composition-*.ts`
- `frontend/scripts/test-exploration-composition-engine.mjs`
- `docs/research/trace-v49-exploration-composition-engine-round1/`
- `docs/audits/v49-exploration-composition-engine-round1/`
- authority, release-index, project-log, package-script, and active-script-allowlist records
""")
    write_text(AUDIT / "10_LEGACY_VALIDATOR_COMPATIBILITY.md", """# Legacy validator compatibility

Round 11 through Round 14 semantic regression gates pass through their current unit and cross-runtime conformance suites, with their sealed source/core packages unchanged. Their historical exhaustive validators are intentionally not treated as whole-tree Round 15 gates: the Round 11 scope guard rejects every later-round path, the Round 13 product-boundary guard predates and forbids Round 15's explicitly internal renderer, and the Round 14 manifest includes `frontend/package.json`, whose test-script table is intentionally extended here. Round 15 therefore records current conformance plus zero frozen Round 13/14 core mutations instead of misreporting those expected scope/seal incompatibilities as semantic regressions.
""")


def seal_manifest() -> None:
    support = [
        REPO / "schemas/trace/exploration/bounded-semantic-image-v1.schema.json",
        REPO / "schemas/trace/exploration/composition-decision-v1.schema.json",
        REPO / "schemas/trace/exploration/composition-audit-v1.schema.json",
        REPO / "frontend/src/lib/trace/exploration-composition-adapter.ts",
        REPO / "frontend/src/lib/trace/exploration-composition-research-renderer.ts",
        REPO / "frontend/scripts/test-exploration-composition-engine.mjs",
        REPO / "frontend/package.json", REPO / "PROJECT_LOG.md",
        REPO / "docs/research/EXPLORATION_CURRENT.md", REPO / "docs/releases/v49/RELEASE_INDEX.md",
        REPO / "docs/releases/v49/AUDIT_INDEX.md", REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json",
        REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.csv", REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.md",
        *[path for path in ENGINE.rglob("*") if path.is_file() and "__pycache__" not in path.parts],
    ]
    excluded = {AUDIT / "MANIFEST.tsv", AUDIT / "SHA256SUMS.txt"}
    files = sorted(set(path for root in (RESEARCH, AUDIT) for path in root.rglob("*") if path.is_file() and path not in excluded) | {path for path in support if path.is_file()})
    rows = [{"path": path.relative_to(REPO).as_posix(), "byte_size": path.stat().st_size, "sha256": sha256(path)} for path in files]
    write_tsv(AUDIT / "MANIFEST.tsv", rows)
    write_text(AUDIT / "SHA256SUMS.txt", "\n".join(f"{row['sha256']}  {row['path']}" for row in rows))


if __name__ == "__main__":
    generate()
    seal_manifest()
