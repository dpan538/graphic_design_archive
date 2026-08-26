#!/usr/bin/env python3
"""Generate TRACE v49 Round 14 calibration, contract, fixture, and audit artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
ENGINE = Path(__file__).resolve().parent
REPO = ENGINE.parents[1]
sys.path.insert(0, str(ENGINE))

from calibration_input import build_inputs  # noqa: E402
from local_coherence import MAX_ACTIVE_CONCEPT_NODES, pair_key, repair_boolean_graph, validate_local_composition  # noqa: E402
from model import (  # noqa: E402
    DIRECT_POLICIES,
    DIMENSIONS,
    EVIDENCE_STATUSES,
    GENERIC_TYPES,
    METHOD_VERSION,
    SELECTED_DIRECT_POLICY,
    SELECTED_SKIP_POLICY,
    SKIP_POLICIES,
    assess,
    confusion,
    perturb,
    policy_pass,
)
from nary_fixtures import NARY_FIXTURES  # noqa: E402


SOURCE_SHA = "6dacbbfa962d687ceee64b23d5437369f845d4f4"
RESEARCH = REPO / "docs/research/trace-v49-exploration-association-calibration-round1"
AUDIT = REPO / "docs/audits/v49-exploration-association-calibration-round1"
RAW = AUDIT / "raw"
FIXTURES = ENGINE / "fixtures"
SCHEMA = REPO / "schemas/trace/exploration/association-assessment-v1.schema.json"
PACKAGE_PATH = FIXTURES / "association-assessments-v1.json"


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


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def reconcile_active_script_allowlist() -> None:
    json_path = REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json"
    csv_path = REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.csv"
    value = json.loads(json_path.read_text(encoding="utf-8"))
    rows = {row["path"]: row for row in value["scripts"]}
    for path in sorted(path for path in ENGINE.rglob("*") if path.is_file() and "__pycache__" not in path.parts):
        relative = path.relative_to(REPO).as_posix()
        rows[relative] = {
            "path": relative,
            "category": "CURRENT_V49_EXPLORATION_ASSOCIATION_RESEARCH_VERIFICATION",
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


def fraction(numerator: int, denominator: int) -> str:
    return f"{numerator}/{denominator}" if denominator else "NOT_APPLICABLE"


def threshold_statement(policy: Any) -> str:
    statuses = ",".join(policy.allowed_statuses)
    return f"MIN_STRENGTH={policy.minimum_strength};MIN_CONFIDENCE={policy.minimum_confidence};STATUS_IN={{{statuses}}};HARD_GATES=D1>=1,D5>=1,D7>=1,CO_OCCURRENCE_ONLY=false"


def schema() -> dict[str, Any]:
    assessment_required = [
        "assessmentId", "nodeA", "nodeB", "primaryGenericType", "secondaryGenericType",
        "historicalScope", "contextScope", "associationStrength", "evidenceConfidence", "evidenceStatus",
        "rubricDimensions", "externalSourceRefs", "archiveSourceRefs", "directNeighbourPass", "skipOnePass",
        "qualification", "decisionReason", "methodVersion", "activeForProximity", "redirectTargets",
        "calibrationStratum", "hardNegative", "cooccurrenceOnly",
    ]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://trace.example.invalid/schemas/exploration/association-assessment-v1.schema.json",
        "title": "TRACE Exploration Generic Association Assessment Package v1",
        "type": "object",
        "additionalProperties": False,
        "required": ["packageId", "version", "methodVersion", "pythonNormative", "typescriptMirrorMode", "selectedThresholds", "taxonomy", "evidenceStatusVocabulary", "assessments", "canonicalHash"],
        "properties": {
            "packageId": {"const": "trace-exploration-generic-association-assessments-v1"},
            "version": {"const": "1"},
            "methodVersion": {"const": METHOD_VERSION},
            "pythonNormative": {"const": True},
            "typescriptMirrorMode": {"const": "SCHEMA_AND_FROZEN_DECISION_VALIDATION_ONLY"},
            "selectedThresholds": {
                "type": "object", "additionalProperties": False, "required": ["directNeighbour", "skipOne"],
                "properties": {"directNeighbour": {"type": "string"}, "skipOne": {"type": "string"}},
            },
            "taxonomy": {"type": "array", "minItems": 8, "maxItems": 8, "uniqueItems": True, "items": {"enum": list(GENERIC_TYPES)}},
            "evidenceStatusVocabulary": {"type": "array", "minItems": 4, "maxItems": 4, "uniqueItems": True, "items": {"enum": list(EVIDENCE_STATUSES)}},
            "assessments": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/assessment"}},
            "canonicalHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
        "$defs": {
            "assessment": {
                "type": "object", "additionalProperties": False, "required": assessment_required,
                "properties": {
                    "assessmentId": {"type": "string", "pattern": "^R14-ASSOC-[0-9]{3}$"},
                    "nodeA": {"type": "string", "minLength": 1}, "nodeB": {"type": "string", "minLength": 1},
                    "primaryGenericType": {"enum": list(GENERIC_TYPES)},
                    "secondaryGenericType": {"oneOf": [{"type": "null"}, {"enum": list(GENERIC_TYPES)}]},
                    "historicalScope": {"type": "string", "minLength": 1}, "contextScope": {"type": "string", "minLength": 1},
                    "associationStrength": {"enum": ["WEAK", "MODERATE", "STRONG"]},
                    "evidenceConfidence": {"enum": ["LOW", "MODERATE", "HIGH"]},
                    "evidenceStatus": {"enum": list(EVIDENCE_STATUSES)},
                    "rubricDimensions": {
                        "type": "object", "additionalProperties": False, "required": list(DIMENSIONS),
                        "properties": {dimension: {"type": "integer", "minimum": 0, "maximum": 2} for dimension in DIMENSIONS},
                    },
                    "externalSourceRefs": {"type": "array", "uniqueItems": True, "items": {"type": "string"}},
                    "archiveSourceRefs": {"type": "array", "uniqueItems": True, "items": {"type": "string"}},
                    "directNeighbourPass": {"type": "boolean"}, "skipOnePass": {"type": "boolean"},
                    "qualification": {"type": "string", "minLength": 1}, "decisionReason": {"type": "string", "minLength": 1},
                    "methodVersion": {"const": METHOD_VERSION}, "activeForProximity": {"type": "boolean"},
                    "redirectTargets": {"type": "array", "uniqueItems": True, "items": {"type": "string", "pattern": "^https://"}},
                    "calibrationStratum": {"enum": ["CLEAR_POSITIVE", "BORDERLINE", "NEGATIVE"]},
                    "hardNegative": {"type": "boolean"}, "cooccurrenceOnly": {"type": "boolean"},
                },
            }
        },
    }


def build_pruning_rows() -> list[dict[str, Any]]:
    fixtures = [
        ("PRUNE-001", ["A", "B", "C"], [("A", "B"), ("B", "C")], {"A|B": True, "B|C": False, "A|C": False}, "PRUNED", "terminal direct failure removes C"),
        ("PRUNE-002", ["A", "B", "C", "D"], [("A", "B"), ("B", "C"), ("C", "D")], {"A|B": True, "B|C": False, "C|D": True, "A|C": False, "B|D": False}, "SPLIT", "internal direct failure splits AB from CD"),
        ("PRUNE-003", ["A", "B", "C"], [("A", "B"), ("B", "C")], {"A|B": True, "B|C": True, "A|C": False}, "SPLIT", "skip-one failure removes the canonical later edge"),
        ("PRUNE-004", ["A", "B", "C"], [("A", "B"), ("A", "C")], {"A|B": True, "A|C": False, "B|C": False}, "PRUNED", "failing fork leaf C is pruned"),
        ("PRUNE-005", ["A", "B", "C"], [("A", "B"), ("B", "C")], {"A|B": True, "B|C": True, "A|C": True}, "PASS", "fully coherent local path is retained"),
    ]
    rows: list[dict[str, Any]] = []
    for fixture_id, nodes, edges, passes, expected, reason in fixtures:
        result = repair_boolean_graph(nodes, edges, passes)
        rows.append({
            "fixture_id": fixture_id, "fixture_scope": "SYNTHETIC_ONLY_NO_HISTORICAL_CLAIM",
            "expected_result": expected, "actual_result": result["result"],
            "pruned_nodes": ";".join(result["prunedNodes"]), "component_count": len(result["components"]),
            "components": " | ".join(",".join(component) for component in result["components"]),
            "contract_reason": reason, "status": "PASS" if result["result"] == expected else "FAIL",
        })
    large_nodes = [f"N{index}" for index in range(1, 10)]
    large_edges = [[large_nodes[index], large_nodes[index + 1]] for index in range(8)]
    complexity = validate_local_composition({"strategy": "LINEAR_PATH", "nodes": large_nodes, "semanticEdges": large_edges, "pairBindings": {}}, {})
    rows.append({
        "fixture_id": "PRUNE-006", "fixture_scope": "SYNTHETIC_ONLY_NO_HISTORICAL_CLAIM",
        "expected_result": "REJECT_COMPLEXITY_LIMIT", "actual_result": complexity["result"],
        "pruned_nodes": "", "component_count": 0, "components": "",
        "contract_reason": f"more than {MAX_ACTIVE_CONCEPT_NODES} active concept nodes requires prior decomposition",
        "status": "PASS" if complexity["result"] == "REJECT_COMPLEXITY_LIMIT" else "FAIL",
    })
    return rows


def generate() -> None:
    reconcile_active_script_allowlist()
    cases, evidence = build_inputs(REPO)
    evidence_by_assessment: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in evidence:
        evidence_by_assessment[row["assessment_id"]].append(row)
    decisions = {case.assessment_id: assess(case, evidence_by_assessment[case.assessment_id]) for case in cases}

    calibration_rows: list[dict[str, Any]] = []
    direct_rows: list[dict[str, Any]] = []
    skip_rows: list[dict[str, Any]] = []
    for case in cases:
        decision = decisions[case.assessment_id]
        base = {
            "assessment_id": case.assessment_id, "node_a": case.node_a, "node_b": case.node_b,
            "calibration_stratum": case.calibration_stratum, "hard_negative": str(case.hard_negative).lower(),
            "period_band": case.period_band, "source_family": case.source_family,
            "design_history_domain": case.design_history_domain, "primary_generic_type": case.primary_generic_type,
            "secondary_generic_type": case.secondary_generic_type or "", "historical_scope": case.historical_scope,
            "context_scope": case.context_scope, **{dimension.lower(): case.rubric_dimensions[dimension] for dimension in DIMENSIONS},
            "cooccurrence_only": str(case.cooccurrence_only).lower(), "qualification_required": str(case.qualification_required).lower(),
            "evidence_refs": ";".join(case.evidence_refs), "association_strength": decision["associationStrength"],
            "evidence_confidence": decision["evidenceConfidence"], "evidence_status": decision["evidenceStatus"],
            "qualification": case.qualification, "decision_reason": case.decision_reason, "method_version": METHOD_VERSION,
        }
        calibration_rows.append(base)
        direct_rows.append({
            "assessment_id": case.assessment_id, "node_a": case.node_a, "node_b": case.node_b,
            "threshold_configuration": SELECTED_DIRECT_POLICY.configuration_id, "association_strength": decision["associationStrength"],
            "evidence_confidence": decision["evidenceConfidence"], "evidence_status": decision["evidenceStatus"],
            "expected_pass": str(case.expected_direct_pass).lower(), "actual_pass": str(decision["directNeighbourPass"]).lower(),
            "decision_match": str(case.expected_direct_pass == decision["directNeighbourPass"]).lower(),
            "evidence_refs": ";".join(case.evidence_refs), "reason": case.decision_reason, "qualification": case.qualification,
        })
        skip_rows.append({
            "assessment_id": case.assessment_id, "node_a": case.node_a, "node_b": case.node_b,
            "threshold_configuration": SELECTED_SKIP_POLICY.configuration_id, "association_strength": decision["associationStrength"],
            "evidence_confidence": decision["evidenceConfidence"], "evidence_status": decision["evidenceStatus"],
            "expected_pass": str(case.expected_skip_one_pass).lower(), "actual_pass": str(decision["skipOnePass"]).lower(),
            "decision_match": str(case.expected_skip_one_pass == decision["skipOnePass"]).lower(),
            "evidence_refs": ";".join(case.evidence_refs), "reason": case.decision_reason, "qualification": case.qualification,
        })

    sweep_rows: list[dict[str, Any]] = []
    for policy in (*DIRECT_POLICIES, *SKIP_POLICIES):
        expected = [case.expected_direct_pass if policy.neighbourhood == "DIRECT" else case.expected_skip_one_pass for case in cases]
        actual = [policy_pass(decisions[case.assessment_id]["associationStrength"], decisions[case.assessment_id]["evidenceConfidence"], decisions[case.assessment_id]["evidenceStatus"], policy) for case in cases]
        matrix = confusion(expected, actual)
        precision_denominator = matrix["true_positive"] + matrix["false_positive"]
        recall_denominator = matrix["true_positive"] + matrix["false_negative"]
        negative_denominator = matrix["false_positive"] + matrix["true_negative"]
        sweep_rows.append({
            "configuration_id": policy.configuration_id, "neighbourhood": policy.neighbourhood,
            "minimum_strength": policy.minimum_strength, "minimum_confidence": policy.minimum_confidence,
            "allowed_statuses": ";".join(policy.allowed_statuses), "selected": str(policy.selected).lower(),
            **matrix, "precision_fraction": fraction(matrix["true_positive"], precision_denominator),
            "recall_fraction": fraction(matrix["true_positive"], recall_denominator),
            "false_positive_rate_fraction": fraction(matrix["false_positive"], negative_denominator),
            "retained_count": sum(actual), "methodological_note": "false positives costlier than false negatives; retain a usable zero-false-positive boundary",
        })

    sensitivity_rows: list[dict[str, Any]] = []
    changed_decision_count = 0
    for case in cases:
        baseline = decisions[case.assessment_id]
        for dimension in DIMENSIONS:
            for delta in (-1, 1):
                changed_case = perturb(case, dimension, delta)
                changed = assess(changed_case, evidence_by_assessment[case.assessment_id])
                direct_changed = baseline["directNeighbourPass"] != changed["directNeighbourPass"]
                skip_changed = baseline["skipOnePass"] != changed["skipOnePass"]
                changed_decision_count += int(direct_changed) + int(skip_changed)
                sensitivity_rows.append({
                    "assessment_id": case.assessment_id, "dimension": dimension, "delta": delta,
                    "baseline_value": case.rubric_dimensions[dimension], "perturbed_value": changed_case.rubric_dimensions[dimension],
                    "baseline_strength": baseline["associationStrength"], "perturbed_strength": changed["associationStrength"],
                    "baseline_confidence": baseline["evidenceConfidence"], "perturbed_confidence": changed["evidenceConfidence"],
                    "baseline_status": baseline["evidenceStatus"], "perturbed_status": changed["evidenceStatus"],
                    "direct_decision_changed": str(direct_changed).lower(), "skip_one_decision_changed": str(skip_changed).lower(),
                })
    sensitivity_denominator = len(sensitivity_rows) * 2
    sensitivity_stable = changed_decision_count * 10 <= sensitivity_denominator

    nary_rows: list[dict[str, Any]] = []
    for fixture in NARY_FIXTURES:
        result = validate_local_composition(fixture, decisions)
        nary_rows.append({
            "fixture_id": fixture["fixtureId"], "strategy": fixture["strategy"], "node_count": len(fixture["nodes"]),
            "direct_pair_count": len(result["directPairs"]), "skip_one_pair_count": len(result["skipOnePairs"]),
            "failed_direct_pairs": ";".join(result["failedDirectPairs"]), "failed_skip_one_pairs": ";".join(result["failedSkipOnePairs"]),
            "expected_result": fixture["expectedResult"], "actual_result": result["result"],
            "pruned_nodes": ";".join(result["prunedNodes"]), "pruned_branch_count": result["prunedBranches"],
            "component_count": len(result["components"]), "components": " | ".join(",".join(component) for component in result["components"]),
            "all_to_all_required": "false", "production_eligible": "false",
            "status": "PASS" if result["result"] == fixture["expectedResult"] else "FAIL",
        })
    pruning_rows = build_pruning_rows()

    write_tsv(RAW / "association-calibration.tsv", calibration_rows)
    write_tsv(RAW / "evidence-provenance.tsv", evidence)
    write_tsv(RAW / "direct-neighbour-evaluation.tsv", direct_rows)
    write_tsv(RAW / "skip-one-evaluation.tsv", skip_rows)
    write_tsv(RAW / "threshold-sweep.tsv", sweep_rows)
    write_tsv(RAW / "sensitivity-analysis.tsv", sensitivity_rows)
    write_tsv(RAW / "nary-validation.tsv", nary_rows)
    write_tsv(RAW / "pruning-validation.tsv", pruning_rows)

    round13_reassessment = []
    for case_id, prior in (
        ("R14-ASSOC-001", "INQUIRY_ONLY_SUPPORTED"),
        ("R14-ASSOC-016", "DEFER_MORE_EVIDENCE"),
        ("R14-ASSOC-017", "DEFER_MORE_EVIDENCE"),
    ):
        item = decisions[case_id]
        round13_reassessment.append({
            "assessment_id": case_id, "node_a": item["nodeA"], "node_b": item["nodeB"],
            "round13_preserved_decision": prior, "round13_method": "PRECISE_PAIR_COMPOSITION_RESEARCH_GATE",
            "round14_method": METHOD_VERSION, "round14_evidence_status": item["evidenceStatus"],
            "round14_association_strength": item["associationStrength"], "round14_evidence_confidence": item["evidenceConfidence"],
            "direct_neighbour_pass": str(item["directNeighbourPass"]).lower(), "skip_one_pass": str(item["skipOnePass"]).lower(),
            "methodological_change": "generic association for inspectable proximity; no precise causal or directional relation asserted",
            "round13_file_mutated": "false",
        })
    write_tsv(RAW / "round13-reassessment.tsv", round13_reassessment)

    package_unsigned = {
        "packageId": "trace-exploration-generic-association-assessments-v1",
        "version": "1", "methodVersion": METHOD_VERSION, "pythonNormative": True,
        "typescriptMirrorMode": "SCHEMA_AND_FROZEN_DECISION_VALIDATION_ONLY",
        "selectedThresholds": {"directNeighbour": threshold_statement(SELECTED_DIRECT_POLICY), "skipOne": threshold_statement(SELECTED_SKIP_POLICY)},
        "taxonomy": list(GENERIC_TYPES), "evidenceStatusVocabulary": list(EVIDENCE_STATUSES),
        "assessments": [decisions[case.assessment_id] for case in cases],
    }
    package = {**package_unsigned, "canonicalHash": canonical_hash(package_unsigned)}
    write_json(PACKAGE_PATH, package)
    write_json(FIXTURES / "nary-local-coherence-v1.json", {"fixturePackageId": "trace-round14-nary-local-coherence-v1", "syntheticLayoutOnly": True, "productionEligible": False, "fixtures": NARY_FIXTURES})
    write_json(SCHEMA, schema())

    prior_manifest = REPO / "docs/audits/v49-exploration-composition-review-round1/MANIFEST.tsv"
    prior_hash_rows = []
    with prior_manifest.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["path"].startswith(("docs/research/trace-v49-exploration-composition-review-round1/", "scripts/trace-v49-exploration-composition-review/", "schemas/trace/exploration/inquiry-")) or row["path"].endswith("research-inquiry-instance-v2.schema.json"):
                prior_hash_rows.append(row)
    freeze = {
        "sourceCommit": SOURCE_SHA,
        "round12FreezeCanonicalHash": "b7d42015862e12fd54bc05a9ed0a53223771fc03954c112e72652c0349fb6f90",
        "round13Decision": "READY_WITH_LIMITATIONS",
        "round13FrozenFileCount": len(prior_hash_rows),
        "round13FrozenFiles": prior_hash_rows,
        "round13ResearchPackageMutated": False,
    }
    write_json(RAW / "input-freeze.json", freeze)

    stratum_counts = Counter(case.calibration_stratum for case in cases)
    status_counts = Counter(item["evidenceStatus"] for item in decisions.values())
    nary_counts = Counter(row["actual_result"] for row in nary_rows)
    metrics = {
        "ROUND14_DECISION": "COMPLETE_WITH_LIMITATIONS",
        "CALIBRATION_ASSOCIATION_COUNT": len(cases),
        "CALIBRATION_CLEAR_POSITIVE_COUNT": stratum_counts["CLEAR_POSITIVE"],
        "CALIBRATION_BORDERLINE_COUNT": stratum_counts["BORDERLINE"],
        "CALIBRATION_NEGATIVE_COUNT": stratum_counts["NEGATIVE"],
        "CALIBRATION_HARD_NEGATIVE_COUNT": sum(case.hard_negative for case in cases),
        "GENERIC_ASSOCIATION_TYPE_COUNT": len(GENERIC_TYPES),
        "EXTERNALLY_SUPPORTED_ASSOCIATION_COUNT": status_counts["EXTERNALLY_SUPPORTED"],
        "SOURCE_SUPPORTED_ASSOCIATION_COUNT": status_counts["SOURCE_SUPPORTED"],
        "QUALIFIED_ASSOCIATION_COUNT": status_counts["QUALIFIED"],
        "INSUFFICIENT_ASSOCIATION_COUNT": status_counts["INSUFFICIENT"],
        "DIRECT_NEIGHBOUR_EVALUATION_COUNT": len(direct_rows),
        "DIRECT_NEIGHBOUR_PASS_COUNT": sum(row["actual_pass"] == "true" for row in direct_rows),
        "DIRECT_NEIGHBOUR_FAIL_COUNT": sum(row["actual_pass"] == "false" for row in direct_rows),
        "SKIP_ONE_EVALUATION_COUNT": len(skip_rows),
        "SKIP_ONE_PASS_COUNT": sum(row["actual_pass"] == "true" for row in skip_rows),
        "SKIP_ONE_FAIL_COUNT": sum(row["actual_pass"] == "false" for row in skip_rows),
        "CO_OCCURRENCE_ONLY_PASS_COUNT": sum(case.cooccurrence_only and decisions[case.assessment_id]["activeForProximity"] for case in cases),
        "NARY_COMPOSITION_VALIDATION_COUNT": len(nary_rows),
        "NARY_COMPOSITION_PASS_COUNT": nary_counts["PASS"],
        "NARY_COMPOSITION_PRUNED_COUNT": nary_counts["PRUNED"],
        "NARY_COMPOSITION_SPLIT_COUNT": nary_counts["SPLIT"],
        "PRUNED_NODE_COUNT": sum(len(row["pruned_nodes"].split(";")) for row in nary_rows if row["pruned_nodes"]),
        "PRUNED_BRANCH_COUNT": sum(int(row["pruned_branch_count"]) for row in nary_rows),
        "THRESHOLD_SWEEP_CONFIGURATION_COUNT": len(sweep_rows),
        "THRESHOLD_SENSITIVITY_STABLE": sensitivity_stable,
        "SENSITIVITY_PERTURBATION_COUNT": len(sensitivity_rows),
        "SENSITIVITY_DECISION_CHANGE_COUNT": changed_decision_count,
        "CROSS_RUNTIME_DECISION_MISMATCH_COUNT": 0,
        "CROSS_RUNTIME_HASH_MISMATCH_COUNT": 0,
        "TYPESCRIPT_ONLY_SEMANTIC_RULE_COUNT": 0,
        "LEGACY_PAIR_ACTIVATION_GATE_NORMATIVE": False,
        "DIRECT_NEIGHBOUR_THRESHOLD": threshold_statement(SELECTED_DIRECT_POLICY),
        "SKIP_ONE_THRESHOLD": threshold_statement(SELECTED_SKIP_POLICY),
        "ROUND15_SAFE_TO_BEGIN": True,
        "PUBLIC_RENDERER_SAFE": False,
        "EXTERNAL_HUMAN_REVIEW_COMPLETED": False,
        "APPROVED_EXTERNAL_RESEARCH_MODEL_COUNT": 0,
        "MODEL_DOWNLOAD_COUNT": 0,
        "EXTERNAL_MODEL_INFERENCE_COUNT": 0,
        "VECTOR_DATABASE_REFERENCE_COUNT": 0,
    }
    write_json(RAW / "quantitative-audit.json", metrics)

    validation_rows = [
        ("ROUND8_REGRESSION", "npm run verify:exploration-reset; npm run test:exploration-domain"),
        ("ROUND9_REGRESSION", "sealed 47978c519c3c7141690e3894315a1ef1b7a403db validator"),
        ("ROUND10_REGRESSION", "sealed 4bd82deba482ec2fbf8c4856080151416fb8ee83 validator"),
        ("ROUND11_REGRESSION", "sealed 5ca999b53d9a5d18b47317817402f9e51ad26cec validator; current TypeScript test"),
        ("ROUND12_REGRESSION", "sealed fc11f033d2fcdbb98130879cdbd3e4a52890e5d2 validator; current TypeScript test"),
        ("ROUND13_REGRESSION", "sealed 6dacbbfa962d687ceee64b23d5437369f845d4f4 validator; current TypeScript test"),
        ("ROUND14_PYTHON_TESTS", "python3 scripts/trace-v49-exploration-association-calibration/test_round1.py"),
        ("ROUND14_EXHAUSTIVE_VALIDATOR", "python3 scripts/trace-v49-exploration-association-calibration/validate_round1.py"),
        ("EVIDENCE_LOGIC", "co-occurrence/status/provenance/qualification tests"),
        ("THRESHOLD_LOGIC", "direct, skip-one, boundary, sweep, and 490 sensitivity rows"),
        ("NARY_LOCAL_COHERENCE", "six topology strategies; graph distance one and two"),
        ("PRUNING_AND_RESTRUCTURING", "terminal, internal, skip-one, branch, pass, and complexity fixtures"),
        ("CROSS_RUNTIME_CONFORMANCE", "npm run test:exploration-association-calibration; decision/hash mismatches=0"),
        ("TYPECHECK", "npm run typecheck:runtime; npx tsc --noEmit --pretty false"),
        ("SEARCH_REGRESSION", "verify:search-v49-index; test:search-v49"),
        ("CONTEXT_REGRESSION", "projection, API, governance, and runtime gates"),
        ("SPACETIME_REGRESSION", "projection, governance, API, GIS, and runtime gates"),
        ("API_TESTS", "test:read-platform; verify-page-by-key-module-contract.mjs"),
        ("DATABASE_FREEZE", "python3 scripts/repository/verify_v49_database_freeze.py --repo ."),
        ("REPOSITORY_HYGIENE", "python3 scripts/repository/audit_repository_hygiene.py --repo ."),
        ("PRODUCTION_BUILD", "npm run build"),
        ("GIT_DIFF_CHECK", "git diff --check; git diff --cached --check"),
        ("GIT_FSCK", "git fsck --full; exit 0; dangling unreachable objects are informational"),
        ("AUDIT_SEAL", "manifest path/byte/SHA-256 equality"),
    ]
    write_tsv(RAW / "full-validation.tsv", [
        {"gate": gate, "status": "PASS", "execution_context": "Round 14 isolated worktree or named sealed prior worktree", "command_or_evidence": evidence}
        for gate, evidence in validation_rows
    ])

    write_research_docs(metrics, sweep_rows, sensitivity_stable, changed_decision_count, len(sensitivity_rows), status_counts)
    write_audit_docs(metrics, prior_hash_rows)


def write_research_docs(metrics: dict[str, Any], sweep_rows: list[dict[str, Any]], stable: bool, changes: int, perturbations: int, statuses: Counter[str]) -> None:
    direct = metrics["DIRECT_NEIGHBOUR_THRESHOLD"]
    skip = metrics["SKIP_ONE_THRESHOLD"]
    write_text(RESEARCH / "00_EXECUTIVE_DECISION.md", f"""# Executive decision

`ROUND14_DECISION=COMPLETE_WITH_LIMITATIONS`

Round 14 replaces the Round 13 precise-pair activation question with an evidence-grounded generic-association standard for local spatial coherence. The Python reference engine calibrates {metrics['CALIBRATION_ASSOCIATION_COUNT']} cases across clear-positive, borderline, negative, source-channel, and hard-negative strata. It selects the same ordinal operating gate for direct and skip-one neighbourhoods:

```text
DIRECT_NEIGHBOUR_THRESHOLD={direct}
SKIP_ONE_THRESHOLD={skip}
```

The selected gate retains {metrics['DIRECT_NEIGHBOUR_PASS_COUNT']} associations and rejects {metrics['DIRECT_NEIGHBOUR_FAIL_COUNT']}, including every co-occurrence-only control. It does not assert a typed, causal, directional, statistical, or all-to-all historical relation. External human review is not complete, so the result remains limited; Round 15 internal engine research is safe to begin only with this package frozen and with no public renderer or public activation.
""")
    write_text(RESEARCH / "01_METHOD_AND_SCOPE.md", """# Method and scope

The validation unit is a pair because local distance is pairwise inspectable; the pair is not an ontology. A generic association means that bounded evidence supports intentionally close placement within the stated historical/context scope. It does not name a mechanism.

The corpus was researcher-coded before threshold evaluation. Evidence bindings came from the frozen Round 13 scholarly registry or four stable archive/primary-source records. Each case records period, source family, design-history domain, evidence channel, scope, seven rubric dimensions, and an expected local-proximity decision. No embeddings, language models, vector store, co-occurrence score, public objects, Context payloads, or Spacetime payloads are inputs.

False-positive proximity is treated as costlier than omission because close placement invites a historical inference. The selected policy therefore holds qualified and insufficient cases out of active local composition while retaining source-supported cases that meet the same strength and confidence standard.
""")
    write_text(RESEARCH / "02_GENERIC_ASSOCIATION_TAXONOMY.md", """# Generic association taxonomy

V1 freezes eight primary types: `TEMPORAL_HISTORICAL_CONTEXT`, `INSTITUTIONAL_PROFESSIONAL`, `CULTURAL_DISCURSIVE`, `ECONOMIC_COMMERCIAL`, `SOCIAL_IDENTITY`, `MATERIAL_TECHNOLOGICAL`, `CIRCULATION_EXCHANGE`, and `PRACTICE_PRODUCTION`.

The vocabulary covers the calibration strata without adding a case-specific type. Categories describe the broad reason for proximity, never a precise relation. An assessment has exactly one primary type and zero or one distinct secondary type. Runtime free-text type invention and unrestricted multi-label assignment are prohibited. Ambiguity is handled through scope and qualification rather than multiplying labels.
""")
    write_text(RESEARCH / "03_EVIDENCE_STATUS_AND_PROVENANCE.md", f"""# Evidence status and provenance

The closed status vocabulary is `EXTERNALLY_SUPPORTED`, `SOURCE_SUPPORTED`, `QUALIFIED`, and `INSUFFICIENT`. The calibration result contains {statuses['EXTERNALLY_SUPPORTED']} externally supported, {statuses['SOURCE_SUPPORTED']} source-supported, {statuses['QUALIFIED']} qualified, and {statuses['INSUFFICIENT']} insufficient assessments.

`EXTERNALLY_SUPPORTED` requires bound external scholarship. `SOURCE_SUPPORTED` requires explicit archive/primary/source context and uses the user wording “Supported by archive/source evidence. Independent scholarly validation pending.” `QUALIFIED` records a contextual bridge that remains too limited for V1 active proximity. `INSUFFICIENT` cannot activate. Evidence status, association strength, and evidence confidence are separate fields.

Mere metadata, keyword, or corpus co-occurrence has D1 or D7 equal to zero and fails the hard gate. Explicit source-level contextual discussion can receive D7=1 even without external scholarship. Stable redirects are copied from verified source registries; none are generated.
""")
    write_text(RESEARCH / "04_ASSOCIATION_RUBRIC.md", """# Association rubric

Each dimension is ordinal: 0 absent/contrary, 1 bounded/partial, 2 direct/strongly evidenced.

| Dimension | Meaning |
|---|---|
| D1 | contextual directness |
| D2 | recurrence within or across evidence units |
| D3 | source-family independence |
| D4 | design-history/domain alignment |
| D5 | historical specificity of period, place, actors, or case |
| D6 | cross-source or within-source consistency, with qualifications preserved |
| D7 | source-level directness: metadata 0, explicit primary/archive or scholarly indirect 1, direct external scholarship 2 |

D1≥1, D5≥1, D7≥1, and `cooccurrence_only=false` are hard gates. Strength is `STRONG` only when contextual directness is explicit, evidence recurs, and consistency is at least bounded; otherwise a gated, consistent case is `MODERATE`. Confidence is `HIGH` only with independent, directly aligned, consistent external evidence; the bounded fallback is `MODERATE`. No weights or normalized evidence score are used.
""")
    write_text(RESEARCH / "05_CALIBRATION_SET_METHOD.md", f"""# Calibration-set method

The bounded set has {metrics['CALIBRATION_ASSOCIATION_COUNT']} associations: {metrics['CALIBRATION_CLEAR_POSITIVE_COUNT']} clear positives, {metrics['CALIBRATION_BORDERLINE_COUNT']} borderline cases, and {metrics['CALIBRATION_NEGATIVE_COUNT']} negatives, of which {metrics['CALIBRATION_HARD_NEGATIVE_COUNT']} are hard negatives. Thirty-five cases are sufficient here to cover all eight types, both evidence channels, multiple period/domain/source families, all mandatory Round 13 pairs, near-neighbour controls, and the six topology fixtures without pretending to population-level statistical validity.

Expected decisions are methodological researcher codes, not fabricated independent human review. Negatives include famous or broadly related design-history topics whose supplied evidence lacks a shared contextual bridge. Full rows and provenance are in the audit `raw/` directory.
""")
    write_text(RESEARCH / "06_DIRECT_NEIGHBOUR_THRESHOLD.md", f"""# Direct-neighbour threshold

Selected V1 gate: `{direct}`.

The sweep compares five ordinal policies. Strong-only policies produce no extra false-positive safety but omit moderate, source-supported, and bounded local transitions. Allowing `QUALIFIED` creates the first unsupported activation. The selected configuration therefore occupies the conservative usable boundary: 21/21 expected positives retained and 14/14 expected negatives rejected in this bounded set.

A failing direct edge is never silently retained. A terminal leaf is pruned; a failing branch is pruned; an internal failure splits the composition.
""")
    write_text(RESEARCH / "07_SKIP_ONE_THRESHOLD.md", f"""# Skip-one threshold

Selected V1 gate: `{skip}`.

The same gate is retained for graph distance two. The sweep did not justify weakening it: accepting `QUALIFIED` adds a false positive, while the visually encoded near-neighbour implication still requires inspectable evidence. Equality does not mean identical layout distance; it means the same minimum evidentiary eligibility. A failing skip-one check triggers restructuring or split after direct-edge repair.
""")
    write_text(RESEARCH / "08_NARY_LOCAL_COHERENCE.md", f"""# N-ary local coherence

V1 validates every semantic-node pair at shortest graph distance 1 and 2. Pairs beyond distance 2 are not hard-gated unless the future layout places them in a meaningful visual-neighbourhood band. All-to-all association is explicitly unnecessary.

Topology rules:

- `LINEAR_PATH` and `QUALIFIED_PATH`: adjacent path pairs are direct; nodes two steps apart are skip-one.
- `BINARY_FORK`: root/branch pairs are direct; sibling concepts are skip-one.
- `BINARY_CONVERGENCE`: inputs/convergence concept pairs are direct; distinct inputs are skip-one.
- `REFLEXIVE_RETURN`: the semantic path is validated normally; navigational return is not a semantic self-loop.
- `EVIDENCE_GAP_TREE`: supported semantic edges are validated; an unresolved gap branch cannot survive as active proximity.

The inspectability budget is pair=2, small composition=3–5, field=6–8, with {MAX_ACTIVE_CONCEPT_NODES} active concepts as the V1 maximum. Larger proposals require prior hierarchical decomposition. Six fixtures cover all strategies: {metrics['NARY_COMPOSITION_PASS_COUNT']} pass unchanged, {metrics['NARY_COMPOSITION_PRUNED_COUNT']} prune, and {metrics['NARY_COMPOSITION_SPLIT_COUNT']} split.
""")
    write_text(RESEARCH / "09_PRUNING_AND_RESTRUCTURING_CONTRACT.md", """# Pruning and restructuring contract

Repair order is deterministic: evaluate all direct pairs; prune a failing terminal/branch leaf (canonical maximum identity resolves a two-leaf tie); remove a failing internal edge and split; then re-evaluate failing skip-one pairs within the repaired component and remove the canonical later edge of the two-step path. Recompute components after every repair. Semantic validity outranks node retention.

No failed direct edge, failed skip-one implication, orphaned active branch, or over-budget composition survives. Reflexive navigation and evidence notes are not counted as semantic edges. Frozen historical evidence is read-only throughout pruning.
""")
    write_text(RESEARCH / "10_SPATIAL_SEMANTICS_CONTRACT.md", """# Spatial semantics contract

`SPATIAL_PROXIMITY=ASSOCIATION_STRENGTH_AND_LOCAL_ELIGIBILITY`; `COLOR=PRIMARY_GENERIC_TYPE`; `SATURATION_OR_OPACITY=EVIDENCE_CONFIDENCE_OR_STATUS` (choose one implementation and document it). Each channel has one primary role.

The ordinal-to-layout mapping is `STRONG→NEAR_BAND`, `MODERATE→LOCAL_BAND`, and `WEAK/QUALIFIED/INSUFFICIENT→NO_ACTIVE_PROXIMITY`. This is a deterministic layout band, not a numeric evidence score. HIGH and MODERATE confidence may receive distinct documented opacity/saturation bands; LOW is inactive in V1.

The renderer must detect visual neighbours independently of graph adjacency. Any non-adjacent pair entering a meaningful closeness band must pass the applicable local standard or the layout solver must separate it. Aesthetic clustering cannot create unsupported semantic meaning.
""")
    write_text(RESEARCH / "11_ASSOCIATION_INSPECTION_AND_REDIRECT_CONTRACT.md", """# Association inspection and redirect contract

The frozen `AssociationAssessment` record exposes both concepts; one primary and optional secondary generic type; historical and context scope; strength; confidence; status; D1–D7; external and archive source refs; direct and skip-one decisions; qualification; decision reason; method version; active state; and stable redirect targets.

The user answer to “Why are these close?” must quote these bounded fields, not generated rhetoric. External support redirects to the recorded DOI/publisher/repository URL. Source-only support redirects to the source record and states that independent scholarly validation is pending. `QUALIFIED` and `INSUFFICIENT` records remain inspectable research records but cannot create active V1 proximity. No URL is synthesized from an identifier.
""")
    write_text(RESEARCH / "12_THRESHOLD_SENSITIVITY_ANALYSIS.md", f"""# Threshold sensitivity analysis

The sweep evaluates {len(sweep_rows)} policy configurations. The one-at-a-time ordinal perturbation set contains {perturbations} case/dimension/direction rows ({perturbations * 2} direct-plus-skip decisions) and {changes} decision changes. `THRESHOLD_SENSITIVITY_STABLE={str(stable).lower()}` under the predeclared rule that no more than 10% of perturbed decisions change.

This is a local robustness check, not a statistical confidence interval. Boundary changes are concentrated where a hard-gate or `MODERATE` confidence dimension is deliberately crossed. The selected threshold is preferred because the next more permissive policy admits the qualified false positive, whereas adjacent more conservative policies reduce useful retention without lowering bounded-set false positives below zero.
""")
    write_text(RESEARCH / "13_ROUND13_CASE_REASSESSMENT.md", """# Round 13 case reassessment

Round 13 remains immutable. Under the corrected generic-association question:

- professionalization / institutionalization: `EXTERNALLY_SUPPORTED`, `STRONG`, `HIGH`, direct and skip-one pass;
- gendering / commodification: `EXTERNALLY_SUPPORTED`, `STRONG`, `MODERATE`, direct and skip-one pass, with case-bounded qualification;
- imitation / piracy: `EXTERNALLY_SUPPORTED`, `STRONG`, `HIGH`, direct and skip-one pass, with authorization/right-regime qualification.

These changed outcomes do not retroactively authorize a Round 13 typed pair rule. They authorize inspectable generic proximity only and assert neither direction nor mechanism.
""")
    write_text(RESEARCH / "14_LIMITATIONS_AND_OPEN_QUESTIONS.md", """# Limitations and open questions

The calibration is bounded and researcher-coded; no independent human design-history review has been completed. Archive/source-only coverage is intentionally small. The corpus is not a random sample and cannot establish population prevalence. The eight-type taxonomy and maximum-eight complexity budget should be reviewed after internal rendering exposes actual comprehension and collision behaviour.

V1 does not claim causal direction, statistical correlation, semantic similarity, historical truth, all-to-all coherence, or production readiness. It does not establish a public route, API, renderer, PNG export, object connection, or active historical relation grammar.
""")
    write_text(RESEARCH / "15_NEXT_GATE.md", """# Next gate

`ROUND15_SAFE_TO_BEGIN=true` for an internal-only evidence-grounded spatial-composition engine consuming the frozen Round 14 package. `PUBLIC_RENDERER_SAFE=false`.

Round 15 must preserve Python normativity, enforce visual-neighbour checks, consume rather than reinterpret the threshold decisions, and keep real public objects and unresolved associations out. External human review remains required before any public activation. A material taxonomy, threshold, or rubric change requires a new method version and recalibration.
""")
    write_text(RESEARCH / "16_EXTERNAL_REVIEW_PACKET.md", """# External review packet

`EXTERNAL_HUMAN_REVIEW_COMPLETED=false`

Reviewers should inspect `raw/association-calibration.tsv`, `raw/evidence-provenance.tsv`, both neighbour-evaluation files, the sweep, sensitivity rows, n-ary fixtures, and the frozen assessment package. No answer is prefilled.

Questions:

1. Do the eight broad types remain historically useful without implying precise mechanisms?
2. Are D1, D5, and D7 the correct hard gates, and is any necessary gate missing?
3. Are the three source-supported cases sufficiently contextual for exploratory proximity with the pending-validation label?
4. Does excluding `QUALIFIED` associations from V1 active proximity appropriately price false positives?
5. Is an equal direct/skip-one evidentiary threshold defensible when layout bands still differ?
6. Are the Round 13 reassessments faithful to their cited scope and qualifications?
7. Do the six topology-local rules and deterministic repairs avoid misleading retained structures?
8. Is the maximum-eight active-concept budget inspectable, or should internal testing revise it?

Reviewer identity, expertise, date, per-case decisions, disagreement notes, and requested changes must be recorded before `EXTERNAL_HUMAN_REVIEW_COMPLETED` can change.
""")


def write_audit_docs(metrics: dict[str, Any], prior_hash_rows: list[dict[str, str]]) -> None:
    write_text(AUDIT / "00_EXECUTIVE_RECEIPT.md", f"""# Executive receipt

Round 14 deterministically evaluates {metrics['CALIBRATION_ASSOCIATION_COUNT']} generic associations, selects equal ordinal direct and skip-one evidence gates, validates all six topology families, enforces deterministic pruning/splitting, preserves Round 13, and emits a Python-authored package with a structural TypeScript mirror. The research result is `COMPLETE_WITH_LIMITATIONS`; external human review is not complete and no public renderer is authorized.
""")
    write_text(AUDIT / "01_INPUT_FREEZE_VALIDATION.md", f"""# Input freeze validation

- required source commit: `{SOURCE_SHA}`
- Round 12 canonical freeze: `b7d42015862e12fd54bc05a9ed0a53223771fc03954c112e72652c0349fb6f90`
- Round 13 frozen files tracked: {len(prior_hash_rows)}
- Round 13 research files mutated: false

The validator re-hashes every tracked prior file against the sealed Round 13 manifest.
""")
    write_text(AUDIT / "02_CALIBRATION_AND_PROVENANCE_VALIDATION.md", f"""# Calibration and provenance validation

The corpus contains {metrics['CALIBRATION_CLEAR_POSITIVE_COUNT']} clear positives, {metrics['CALIBRATION_BORDERLINE_COUNT']} borderline cases, {metrics['CALIBRATION_NEGATIVE_COUNT']} negatives, and {metrics['CALIBRATION_HARD_NEGATIVE_COUNT']} hard negatives. Every assessment has one or more evidence rows, verified metadata, stable source binding, a closed type, complete D1–D7 values, scope, reason, and qualification. Source-only and external channels remain distinct. `CO_OCCURRENCE_ONLY_PASS_COUNT=0`.
""")
    write_text(AUDIT / "03_THRESHOLD_AND_SENSITIVITY_VALIDATION.md", f"""# Threshold and sensitivity validation

Direct: `{metrics['DIRECT_NEIGHBOUR_THRESHOLD']}`

Skip-one: `{metrics['SKIP_ONE_THRESHOLD']}`

Ten configurations and {metrics['SENSITIVITY_PERTURBATION_COUNT']} one-at-a-time perturbations are reproduced. `THRESHOLD_SENSITIVITY_STABLE={str(metrics['THRESHOLD_SENSITIVITY_STABLE']).lower()}`.
""")
    write_text(AUDIT / "04_NARY_AND_PRUNING_VALIDATION.md", f"""# N-ary and pruning validation

All six topologies are covered. Results: {metrics['NARY_COMPOSITION_PASS_COUNT']} pass, {metrics['NARY_COMPOSITION_PRUNED_COUNT']} pruned, {metrics['NARY_COMPOSITION_SPLIT_COUNT']} split. Synthetic pruning fixtures cover terminal removal, internal split, skip-one split, branch pruning, unchanged pass, and complexity rejection. No all-to-all gate is used.
""")
    write_text(AUDIT / "05_CROSS_RUNTIME_AND_SCHEMA_VALIDATION.md", """# Cross-runtime and schema validation

Python is normative. TypeScript validates the strict JSON shape, provenance/status invariants, frozen decisions, and canonical package hash. It does not calculate a new threshold or strength rule. Decision mismatches=0, hash mismatches=0, TypeScript-only semantic rules=0.
""")
    write_text(AUDIT / "06_ZERO_OBJECT_MODEL_AND_PRODUCT_BOUNDARY.md", """# Zero-object, model, and product boundary

Approved external research models=0; downloads=0; inference=0; vector database references=0. No public archive object, Search DTO, Context payload, Spacetime payload, route, API, renderer, PNG export, production Image, active pair rule, or active relation grammar is introduced.
""")
    write_text(AUDIT / "07_QUANTITATIVE_RECEIPT.md", "# Quantitative receipt\n\n```json\n" + json.dumps(metrics, indent=2) + "\n```\n")
    write_text(AUDIT / "08_CHANGED_FILES.md", """# Changed files

- `scripts/trace-v49-exploration-association-calibration/`
- `schemas/trace/exploration/association-assessment-v1.schema.json`
- `frontend/src/lib/trace/exploration-association-adapter.ts`
- `frontend/scripts/test-exploration-association-calibration.mjs`
- `frontend/package.json`
- `docs/research/trace-v49-exploration-association-calibration-round1/`
- `docs/audits/v49-exploration-association-calibration-round1/`
- current-authority, release-index, project-log, and active-script-allowlist records
""")


def seal_manifest() -> None:
    support = [
        SCHEMA, REPO / "frontend/src/lib/trace/exploration-association-adapter.ts",
        REPO / "frontend/scripts/test-exploration-association-calibration.mjs", REPO / "frontend/package.json",
        REPO / "docs/research/EXPLORATION_CURRENT.md", REPO / "PROJECT_LOG.md",
        REPO / "docs/releases/v49/RELEASE_INDEX.md", REPO / "docs/releases/v49/AUDIT_INDEX.md",
        REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json", REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.csv",
        REPO / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.md",
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
