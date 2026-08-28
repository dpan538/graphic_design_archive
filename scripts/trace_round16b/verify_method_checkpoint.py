#!/usr/bin/env python3
"""Independently verify the Round 16B higher-order method checkpoint."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
RAW_REL = Path("docs/audits/v49-exploration-higher-order-association-closure-round16b/raw")
REQUIRED_TRIGGER_IDS = {f"TRG-{index:03d}" for index in range(1, 13)}
REQUIRED_DISPOSITIONS = {
    "DIRECT_HIGHER_ORDER_SUPPORT",
    "COHERENT_COMPOSITE_SUPPORT",
    "MIXED_DIRECT_AND_COMPOSITE_SUPPORT",
    "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
    "INQUIRY_ONLY_OR_UNRESOLVED",
    "INSUFFICIENT_EVIDENCE",
    "COOCCURRENCE_ONLY",
    "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
    "TOPOLOGY_OR_ROLE_CONFLICT",
    "HARD_NEGATIVE",
    "PENDING_GOVERNED_REVIEW",
}
REQUIRED_EXCLUSIONS = {
    "NO_GOVERNED_TRIGGER",
    "METADATA_DISCOVERY_ONLY",
    "COOCCURRENCE_OR_CONCEPT_ONLY",
    "VOCABULARY_SUPPORT_ONLY",
    "INCOMPATIBLE_CASE_OR_SCOPE",
    "PAIR_DERIVED_WITHOUT_GROUP_REVIEW",
    "TOPOLOGY_OR_ROLE_CONFLICT",
    "UNRESOLVED_SENSE",
    "STRUCTURAL_ANNOTATION_NOT_ASSOCIATION",
    "ALIAS_OR_MERGED_IDENTITY",
    "RIGHTS_OR_ACCESS_BLOCKED",
    "CATEGORY_OR_DATABASE_COINCIDENCE_ONLY",
}
REQUIRED_CANDIDATE_FIELDS = {
    "candidate_id", "identity_hash", "association_kind", "participants", "arity",
    "order_semantics", "roles_meaningful", "scope", "scope_ids", "trigger_ids",
    "trigger_record_refs", "lifecycle_state", "proposed_disposition", "authority", "version",
}
REQUIRED_REVIEW_FIELDS = {
    "candidate_id", "participants", "evidence_items", "source_bundle_synthesis",
    "global_coherence", "negative_or_conflicting_evidence", "qualification",
    "explicit_non_claims", "rights_review", "product_eligibility", "final_disposition",
    "review_state", "verification", "association_revision_id", "review_authority", "review_version",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, dialect="excel-tab"))


def record_count(path: Path, selector: str) -> int:
    if selector == "tsv_rows":
        return len(read_tsv(path))
    if selector == "jsonl_rows":
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    if selector == "file":
        return 1
    if selector.startswith("json:"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        key = selector.split(":", 1)[1]
        return 1 if key == "file" else len(payload[key])
    raise ValueError(selector)


def schema_required(schema: dict[str, Any]) -> set[str]:
    return set(schema.get("required", []))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    raw = repo / RAW_REL
    failures: list[str] = []
    checks: dict[str, Any] = {}

    def require(code: str, condition: bool, detail: Any = None) -> None:
        checks[code] = {"pass": bool(condition), "detail": detail}
        if not condition:
            failures.append(code)

    method = json.loads((raw / "higher-order-association-method-v1.json").read_text(encoding="utf-8"))
    rights = json.loads((raw / "scholarly-source-rights-policy.json").read_text(encoding="utf-8"))
    build_receipt = json.loads((raw / "method-build-receipt.json").read_text(encoding="utf-8"))
    triggers = read_tsv(raw / "candidate-trigger-registry.tsv")
    dispositions = read_tsv(raw / "association-disposition-taxonomy.tsv")
    exclusions = read_tsv(raw / "exclusion-class-registry.tsv")
    inventory = read_tsv(raw / "evidence-surface-inventory.tsv")
    field_contracts = read_tsv(raw / "evidence-surface-field-contract.tsv")
    gaps = read_tsv(raw / "recursive-gap-ledger.tsv")
    baseline = read_tsv(raw / "round16a-baseline-reconciliation-plan.tsv")
    crosswalk = read_tsv(raw / "concept-sense-crosswalk.tsv")
    rights_ledger = read_tsv(raw / "scholarly-source-rights-ledger.tsv")
    trigger_occurrences = read_tsv(raw / "candidate-trigger-occurrence-ledger.tsv")
    association_evidence = read_tsv(raw / "association-evidence-ledger.tsv")
    candidate_exclusions = read_tsv(raw / "candidate-exclusion-ledger.tsv")

    require("SOURCE_SHA_EXACT", method.get("source_sha") == SOURCE_SHA and build_receipt.get("source_sha") == SOURCE_SHA)
    require("SOURCE_TREE_EXACT", method.get("source_tree") == SOURCE_TREE and build_receipt.get("source_tree") == SOURCE_TREE)
    require("ASSOCIATION_OBJECT_CLASSES_DISTINCT", set(method.get("association_object_boundary", {})) == {
        "vocabulary_concept", "pairwise_association", "higher_order_association", "composition",
        "interaction_state", "workflow", "export",
    })
    arity_policy = method.get("research_arity_policy", {})
    require("HIGHER_ORDER_MINIMUM_THREE", arity_policy.get("higher_order_minimum_arity") == 3)
    require("NO_UNAUDITED_RESEARCH_MAXIMUM", arity_policy.get("research_schema_maximum_arity") is None)
    require("PRODUCT_BOUND_EXPLICITLY_UNRESOLVED", arity_policy.get("product_maximum_arity") == "UNRESOLVED_REQUIRES_BOUND_AUDIT")
    require("TRIGGER_UNIVERSE_NOT_ALL_SUBSETS", "trigger" in method.get("candidate_universe_definition", "").lower() and "Mathematical subsets" in method.get("candidate_universe_definition", ""))
    identity = method.get("canonical_identity", {})
    require("STABLE_ASSOCIATION_ID_EXCLUDES_AUTHORITY_AND_VERSION", {"authority", "version"}.issubset(set(identity.get("non_identity_fields", []))))
    require("APPEND_ONLY_REVISION_ID_DEFINED", "association_revision_id" in identity.get("revision_rule", ""))

    trigger_ids = {row["trigger_id"] for row in triggers}
    require("TRIGGER_IDS_COMPLETE", trigger_ids == REQUIRED_TRIGGER_IDS, sorted(trigger_ids))
    require("TRIGGER_NAMES_UNIQUE", len({row["trigger_name"] for row in triggers}) == len(triggers))
    require("EVERY_TRIGGER_HAS_COVERAGE_PROOF", all(row["coverage_proof"].strip() for row in triggers))
    require("ADAPTIVE_AND_FALSIFICATION_SEARCH_PRESENT", {"TRG-010", "TRG-011"}.issubset({row["trigger_id"] for row in triggers if row["external_search_required"] == "true"}))

    disposition_names = {row["disposition"] for row in dispositions}
    require("REQUIRED_DISPOSITIONS_PRESENT", REQUIRED_DISPOSITIONS.issubset(disposition_names), sorted(disposition_names))
    potentially_active = {row["disposition"] for row in dispositions if row["potentially_active"] == "true"}
    require("ONLY_THREE_SUPPORT_CLASSES_POTENTIALLY_ACTIVE", potentially_active == {
        "DIRECT_HIGHER_ORDER_SUPPORT", "COHERENT_COMPOSITE_SUPPORT", "MIXED_DIRECT_AND_COMPOSITE_SUPPORT"
    }, sorted(potentially_active))
    require("PENDING_IS_NONFINAL", any(row["disposition"] == "PENDING_GOVERNED_REVIEW" and row["status_class"] == "NONFINAL" for row in dispositions))

    exclusion_names = {row["exclusion_class"] for row in exclusions}
    require("REQUIRED_EXCLUSION_CLASSES_PRESENT", REQUIRED_EXCLUSIONS.issubset(exclusion_names), sorted(exclusion_names))
    require("EVERY_EXCLUSION_HAS_PROOF_AND_REOPENING", all(row["proof_required"].strip() and row["reopening_condition"].strip() for row in exclusions))

    surface_ids = [row["surface_id"] for row in inventory]
    require("SURFACE_IDS_UNIQUE", len(surface_ids) == len(set(surface_ids)))
    require("SURFACE_INVENTORY_BROAD", len(inventory) >= 40, len(inventory))
    surface_failures: list[str] = []
    for row in inventory:
        path = repo / row["path"]
        if not path.is_file():
            surface_failures.append(f"{row['surface_id']}:missing")
            continue
        if sha256_file(path) != row["sha256"]:
            surface_failures.append(f"{row['surface_id']}:hash")
        if path.stat().st_size != int(row["bytes"]):
            surface_failures.append(f"{row['surface_id']}:bytes")
        if record_count(path, row["record_selector"]) != int(row["record_count"]):
            surface_failures.append(f"{row['surface_id']}:count")
        row_triggers = {value for value in row["candidate_trigger_ids"].split(";") if value}
        if not row_triggers or not row_triggers.issubset(trigger_ids):
            surface_failures.append(f"{row['surface_id']}:trigger")
    require("SURFACE_HASH_COUNT_AND_TRIGGER_RECONCILIATION", not surface_failures, surface_failures)
    contract_by_surface = {row["surface_id"]: row for row in field_contracts}
    field_contract_failures: list[str] = []
    for row in inventory:
        contract = contract_by_surface.get(row["surface_id"])
        if not contract:
            field_contract_failures.append(f"{row['surface_id']}:missing")
            continue
        path = repo / row["path"]
        selector = row["record_selector"]
        top_fields: list[str] = []
        record_fields: list[str] = []
        if selector == "tsv_rows":
            with path.open(encoding="utf-8", newline="") as handle:
                record_fields = next(csv.reader(handle, dialect="excel-tab"))
        elif selector.startswith("json:"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            top_fields = sorted(payload) if isinstance(payload, dict) else []
            key = selector.split(":", 1)[1]
            if key != "file" and isinstance(payload.get(key), list):
                record_fields = sorted({field for item in payload[key] if isinstance(item, dict) for field in item})
        elif selector == "jsonl_rows":
            record_fields = sorted({
                field for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
                for field in json.loads(line)
            })
        expected_payload = {
            "surface_id": row["surface_id"],
            "record_selector": selector,
            "top_level_fields": top_fields,
            "record_fields": record_fields,
        }
        expected_hash = hashlib.sha256(
            json.dumps(expected_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        if json.loads(contract["top_level_fields_json"]) != top_fields:
            field_contract_failures.append(f"{row['surface_id']}:top")
        if json.loads(contract["record_fields_json"]) != record_fields:
            field_contract_failures.append(f"{row['surface_id']}:record")
        if contract["contract_sha256"] != expected_hash:
            field_contract_failures.append(f"{row['surface_id']}:hash")
    require("EVIDENCE_SURFACE_FIELD_CONTRACTS_EXACT", not field_contract_failures and len(field_contracts) == len(inventory), field_contract_failures)
    inventory_paths = {row["path"] for row in inventory}
    require("ROUND10_NARY_SURFACES_INCLUDED", {
        "docs/research/trace-v49-design-history-relation-grammar-round1/06_ARGUMENT_ROLE_REGISTRY.tsv",
        "docs/research/trace-v49-design-history-relation-grammar-round1/07_GRAMMAR_ATTESTATION_REGISTRY.tsv",
        "docs/research/trace-v49-design-history-relation-grammar-round1/14_CLUSTER_EVIDENCE_HANDOFF.tsv",
    }.issubset(inventory_paths))
    require("PRIOR_MULTI_NODE_SURFACES_INCLUDED", {
        "scripts/trace-v49-exploration-composition-engine/fixtures/composition-fixtures-v1.json",
        "scripts/trace-v49-exploration-real-database/real-composition-registry-v1.json",
        "docs/audits/v49-exploration-full-space-closure-round1/raw/canonical-composition-registry-v2.json",
    }.issubset(inventory_paths))

    required_rights_fields = {
        "source_id", "stable_url", "retrieved_at_utc", "access_status", "access_condition",
        "license_identifier", "redistribution_authorized", "retained_material_type",
        "retained_sha256", "review_status",
    }
    require("RIGHTS_LEDGER_FIELDS_COMPLETE", required_rights_fields.issubset(set(rights.get("required_ledger_fields", []))))
    require("METADATA_EXPLICITLY_NOT_EVIDENCE", rights.get("metadata_is_not_evidence") is True)
    require("NO_FULL_TEXT_WITHOUT_AUTHORITY", "copyrighted_full_text" in rights.get("prohibited_without_explicit_redistribution_authority", []))
    with (raw / "concept-sense-crosswalk.tsv").open(encoding="utf-8", newline="") as handle:
        crosswalk_header = set(next(csv.reader(handle, dialect="excel-tab")))
    require("CONCEPT_SENSE_CROSSWALK_TEMPLATE_COMPLETE", {
        "participant_sense_id", "vocabulary_id", "canonical_label", "source_system",
        "source_concept_id", "source_sense_id", "bounded_sense", "scope_note",
        "disposition", "authority_path", "authority_record_id", "source_sha",
        "crosswalk_status", "crosswalk_reason",
    } == crosswalk_header)
    require("METHOD_CHECKPOINT_CROSSWALK_NOT_PREMATURELY_POPULATED", len(crosswalk) == 0)
    with (raw / "scholarly-source-rights-ledger.tsv").open(encoding="utf-8", newline="") as handle:
        rights_header = set(next(csv.reader(handle, dialect="excel-tab")))
    require("RIGHTS_LEDGER_TEMPLATE_MATCHES_POLICY", set(rights.get("required_ledger_fields", [])) == rights_header)
    require("METHOD_CHECKPOINT_RIGHTS_LEDGER_NOT_PREMATURELY_POPULATED", len(rights_ledger) == 0)
    require("METHOD_CHECKPOINT_OCCURRENCE_LEDGER_NOT_PREMATURELY_POPULATED", len(trigger_occurrences) == 0)
    require("METHOD_CHECKPOINT_EVIDENCE_LEDGER_NOT_PREMATURELY_POPULATED", len(association_evidence) == 0)
    require("METHOD_CHECKPOINT_EXCLUSION_LEDGER_NOT_PREMATURELY_POPULATED", len(candidate_exclusions) == 0)

    open_blockers = [row for row in gaps if row["severity"] == "CLOSURE_BLOCKING" and row["status"] == "OPEN"]
    require("METHOD_CHECKPOINT_REPORTS_OPEN_BLOCKERS", len(open_blockers) > 0, len(open_blockers))
    baseline_map = {row["round16a_metric"]: row["baseline_value"] for row in baseline}
    require("ROUND16A_BASELINE_COUNTS_EXACT", baseline_map == {
        "VOCABULARY_CANDIDATES": "65", "ACTIVE_VOCABULARY": "31", "UNORDERED_PAIR_UNIVERSE": "465",
        "ACTIVE_PAIR_ASSOCIATIONS": "21", "CANONICAL_PAIR_EDGE_SUBGRAPHS": "58", "TOPOLOGY_COMPOSITIONS": "81",
        "PRODUCTION_COMPOSITIONS": "228", "STATES": "5760", "TRANSITIONS": "749944", "WORKFLOWS": "5760",
        "EXPORTS": "11520", "LEGACY_COMPOSITIONS": "11",
    }, baseline_map)

    candidate_schema_path = repo / "schemas/trace/exploration/higher-order-association-candidate-v1.schema.json"
    review_schema_path = repo / "schemas/trace/exploration/higher-order-association-review-v1.schema.json"
    governed_schema_path = repo / "schemas/trace/exploration/governed-association-v1.schema.json"
    candidate_schema = json.loads(candidate_schema_path.read_text(encoding="utf-8"))
    review_schema = json.loads(review_schema_path.read_text(encoding="utf-8"))
    governed_schema = json.loads(governed_schema_path.read_text(encoding="utf-8"))
    require("CANDIDATE_SCHEMA_REQUIRED_FIELDS", REQUIRED_CANDIDATE_FIELDS.issubset(schema_required(candidate_schema)), sorted(schema_required(candidate_schema)))
    require("REVIEW_SCHEMA_REQUIRED_FIELDS", REQUIRED_REVIEW_FIELDS.issubset(schema_required(review_schema)), sorted(schema_required(review_schema)))
    participant_schema = candidate_schema.get("properties", {}).get("participants", {})
    require("CANDIDATE_PARTICIPANTS_MIN_THREE", participant_schema.get("minItems") == 3)
    require("CANDIDATE_SCHEMA_HAS_NO_MAX_ARITY", "maxItems" not in participant_schema)
    require("REVIEW_SCHEMA_FORBIDS_PAIR_PROJECTION", review_schema.get("properties", {}).get("pair_projection_authorized", {}).get("const") is False)
    review_final_values = set(review_schema.get("properties", {}).get("final_disposition", {}).get("enum", []))
    require("PENDING_NOT_A_FINAL_REVIEW_DISPOSITION", "PENDING_GOVERNED_REVIEW" not in review_final_values)
    require("REVIEW_SUPPORT_CONDITIONALS_PRESENT", len(review_schema.get("allOf", [])) >= 2)
    governed_required = schema_required(governed_schema)
    require("GOVERNED_ASSOCIATION_HAS_STABLE_AND_REVISION_IDS", {"association_id", "association_revision_id", "revision_content_sha256"}.issubset(governed_required))
    require("GOVERNED_ASSOCIATION_SEPARATES_PAIR_PROJECTION", {"pair_projection_policy", "authorized_pair_association_revision_ids"}.issubset(governed_required))
    require("GOVERNED_ASSOCIATION_HAS_NO_GLOBAL_MAX_ARITY", "maxItems" not in governed_schema.get("properties", {}).get("participant_sense_ids", {}))

    generator = repo / "scripts/trace_round16b/build_method_checkpoint.py"
    verifier = Path(__file__).resolve()
    verifier_tree = ast.parse(verifier.read_text(encoding="utf-8"))
    imports = {
        alias.name for node in ast.walk(verifier_tree) if isinstance(node, ast.Import) for alias in node.names
    } | {
        node.module or "" for node in ast.walk(verifier_tree) if isinstance(node, ast.ImportFrom)
    }
    require("VERIFIER_DOES_NOT_IMPORT_GENERATOR", "scripts.trace_round16b.build_method_checkpoint" not in imports and "build_method_checkpoint" not in imports)
    require("GENERATOR_AND_VERIFIER_DISTINCT_FILES", generator.resolve() != verifier)

    output_hash_failures = []
    for name, expected in build_receipt.get("output_sha256", {}).items():
        actual = sha256_file(raw / name)
        if actual != expected:
            output_hash_failures.append(f"{name}:{actual}")
    require("BUILD_RECEIPT_OUTPUT_HASHES_MATCH", not output_hash_failures, output_hash_failures)
    schema_hash_failures = [
        path for path, expected in build_receipt.get("schema_sha256", {}).items()
        if sha256_file(repo / path) != expected
    ]
    require("BUILD_RECEIPT_SCHEMA_HASHES_MATCH", not schema_hash_failures and len(build_receipt.get("schema_sha256", {})) == 3, schema_hash_failures)
    require("BUILD_RECEIPT_COUNTS_MATCH", build_receipt.get("evidence_surface_count") == len(inventory) and build_receipt.get("candidate_trigger_count") == len(triggers))

    payload = {
        "format": "trace-round16b-method-independent-verification-v1",
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "status": "PASS" if not failures else "FAIL",
        "check_count": len(checks),
        "failure_count": len(failures),
        "failure_codes": failures,
        "evidence_surface_count": len(inventory),
        "trigger_count": len(triggers),
        "disposition_count": len(dispositions),
        "exclusion_class_count": len(exclusions),
        "open_closure_blocking_gap_count": len(open_blockers),
        "checks": checks,
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ["status", "check_count", "failure_count", "open_closure_blocking_gap_count"]}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
