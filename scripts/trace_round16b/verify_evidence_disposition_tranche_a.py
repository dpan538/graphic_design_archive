#!/usr/bin/env python3
"""Independent verifier for Round 16B evidence-disposition tranche A.

This verifier deliberately reconstructs the selected family/occurrence universe,
upstream record locators, evidence classes, active internal pairs, queue safety,
and receipt hashes without importing or executing the tranche-A builder.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
PARENT_SHA = "068c92151a935cfb9e4adc36b150c6800a6de9a2"
TRANCHE = "CHECKPOINT-005-EVIDENCE-TRANCHE-A"
BUILDER_VERSION = "trace-round16b-evidence-disposition-tranche-a-v1"

RAW = Path("docs/audits/v49-exploration-higher-order-association-closure-round16b/raw")
RESEARCH = Path("docs/research/trace-v49-exploration-higher-order-association-closure-round16b")
V2_OCCURRENCES = RAW / "candidate-trigger-occurrence-ledger-v2.tsv"
V2_FAMILIES = RAW / "local-candidate-family-ledger-v2.tsv"
V2_CROSSWALK = RAW / "concept-sense-crosswalk-v1.tsv"
V2_CENSUS = RAW / "local-candidate-census-v2.json"
METHOD = RAW / "higher-order-association-method-v1.json"
ACTIVE_GRAPH = Path("docs/audits/v49-exploration-full-space-closure-round1/raw/validated-association-graph-v2.json")
R14_PROVENANCE = Path("docs/audits/v49-exploration-association-calibration-round1/raw/evidence-provenance.tsv")
R16A_REGISTRY = Path("docs/audits/v49-exploration-full-space-closure-round1/raw/canonical-composition-registry-v2.json")
R10_ATTESTATIONS = Path("docs/research/trace-v49-design-history-relation-grammar-round1/07_GRAMMAR_ATTESTATION_REGISTRY.tsv")
R10_CLUSTERS = Path("docs/research/trace-v49-design-history-relation-grammar-round1/14_CLUSTER_EVIDENCE_HANDOFF.tsv")
R9_ATTESTATIONS = Path("docs/research/trace-v49-design-history-relation-vocabulary-round1/05_TERM_ATTESTATION_REGISTRY.tsv")
R13_EVIDENCE = Path("docs/research/trace-v49-exploration-composition-review-round1/04_COMPOSITION_EVIDENCE_REGISTRY.tsv")
R16A_READ_MODEL = Path("frontend/generated/trace-exploration-v2/production-read-model.json")
R14_NARY = Path("scripts/trace-v49-exploration-association-calibration/fixtures/nary-local-coherence-v1.json")
R15_FIXTURES = Path("scripts/trace-v49-exploration-composition-engine/fixtures/composition-fixtures-v1.json")
R16_LEGACY = Path("scripts/trace-v49-exploration-real-database/real-composition-registry-v1.json")
BUILDER = Path("scripts/trace_round16b/build_evidence_disposition_tranche_a.py")

OCCURRENCE_OUTPUT = RAW / "evidence-occurrence-disposition-tranche-a-v1.tsv"
FAMILY_OUTPUT = RAW / "family-evidence-disposition-tranche-a-v1.tsv"
QUEUE_OUTPUT = RAW / "conditional-scoped-child-reroute-queue-tranche-a-v1.tsv"
INPUT_MANIFEST = RAW / "evidence-disposition-input-manifest-tranche-a-v1.tsv"
GAP_OUTPUT = RAW / "recursive-gap-ledger-checkpoint005-tranche-a-v1.tsv"
CENSUS_OUTPUT = RAW / "evidence-disposition-census-tranche-a-v1.json"
BUILD_RECEIPT = RAW / "evidence-disposition-build-receipt-tranche-a-v1.json"
RESEARCH_NOTE = RESEARCH / "08_EVIDENCE_DISPOSITION_TRANCHE_A.md"
DEFAULT_VERIFICATION = RAW / "evidence-disposition-independent-verification-tranche-a-v1.json"


FAMILY_SPECS = (
    ("b63bdc2ca9694ca8e682cf6d1b38b65c8154eed366c405ab76391683e0b3c35b", "BOUNDED_SENSE_OR_SCOPE_CONFLICT", "PARENT_SCOPE_CONFLICT_NO_HIGHER_ORDER_CHILD", 0),
    ("7e0a0ee4f78d2f565c4f7771653ecc5a27828dd9fb704139d1e068f2a5fdce64", "BOUNDED_SENSE_OR_SCOPE_CONFLICT", "PARENT_MUST_SPLIT_THREE_CONDITIONAL_SCOPED_CHILDREN", 3),
    ("b19df183e2e9eb0dd6b0a3bccc95944aebf625d45faf01908eaddae994c97e67", "BOUNDED_SENSE_OR_SCOPE_CONFLICT", "PARENT_MUST_SPLIT_TWO_CONDITIONAL_DIRECT_CHILDREN", 2),
    ("3cd10180090e141ef9c63f03a217b2bae056c52da1a52850736c3b580dd533b7", "INQUIRY_ONLY_OR_UNRESOLVED", "ONE_CONDITIONAL_PCM_CHANNEL_CHILD_PENDING_REVIEW", 1),
    ("1d76bf657bbdec293265d051268a2a1153be0108b15a8d63ebbf2cb98cf6f06a", "INQUIRY_ONLY_OR_UNRESOLVED", "ONE_CONDITIONAL_NAMED_MATERIAL_CHAIN_CHILD_PENDING_REVIEW", 1),
    ("de6643ced4014989a08d0517a4c72ea1ccb91d6f95be3303c35997dd8c3df9c1", "BOUNDED_SENSE_OR_SCOPE_CONFLICT", "REROUTE_CASE_LABEL_TO_EXISTING_PAIR_SCOPE", 1),
    ("33a113b724e4e0088fd1c0fa77ea8757112a289ca51e8a441f9111b96697646a", "BOUNDED_SENSE_OR_SCOPE_CONFLICT", "REROUTE_TO_BINARY_MODIFIER_AND_ROLE_REVIEW", 1),
    ("c0a6431919578166078d9823cb9994e5819ab7d56a9bad39a0dcb45d056d892c", "INSUFFICIENT_EVIDENCE", "NO_HIGHER_ORDER_CHILD_RETAIN_UNDERLYING_PAIR_ONLY", 0),
    ("eaa73d3eac5e2a533cb50baf9955efb5a9c848bddbecdd05b6b59d30a1aa508b", "INQUIRY_ONLY_OR_UNRESOLVED", "ONE_CONDITIONAL_TEJO_REMY_CHILD_PENDING_REVIEW", 1),
    ("80a8ae28dc2c532a9ee8fb3293fbfa310d5e9b9042b7d8d3d1dc9612eb7fb941", "TOPOLOGY_OR_ROLE_CONFLICT", "NO_HIGHER_ORDER_CHILD_RETAIN_SCOPED_PAIR_ONLY", 0),
    ("00244f87a89799f75a57307b7eecd35f40bd1f74c99f8e31f4c23fa56855c27a", "COOCCURRENCE_ONLY", "NO_HIGHER_ORDER_CHILD_RETAIN_PHOTOGRAPHY_TYPOGRAPHY_PAIR", 0),
)

EXPECTED_CLASS_COUNTS = {
    "EVIDENCE_BEARING": 13,
    "NEGATIVE_CONTEXT": 1,
    "SOURCE_CONTAINER_COOCCURRENCE": 4,
    "STRUCTURAL_ECHO": 91,
    "SYNTHETIC_CONTROL": 3,
}
EXPECTED_DISPOSITION_COUNTS = {
    "BOUNDED_SENSE_OR_SCOPE_CONFLICT": 5,
    "COOCCURRENCE_ONLY": 1,
    "INQUIRY_ONLY_OR_UNRESOLVED": 3,
    "INSUFFICIENT_EVIDENCE": 1,
    "TOPOLOGY_OR_ROLE_CONFLICT": 1,
}
EXPECTED_QUEUE_ACTION_COUNTS = {
    "REROUTE_MODIFIED_TERM_TO_BINARY_ROLE_SCOPE": 1,
    "REROUTE_REJECTED_CASE_LABEL_TO_PAIR_SCOPE": 1,
    "SCOPED_CHILD_ASSOCIATION_REVIEW": 8,
}
EXPECTED_SCOPE_KEYS = {
    "PCM_2009",
    "DIGITAL_PCM_2026",
    "POLISH_DESIGN_FIELD_2021",
    "PCM_DESIGNED_DEVICE_2009",
    "DIGITAL_DEVICE_2026",
    "PCM_MEDIATING_CHANNEL_2009",
    "RECIPROCAL_LANDSCAPES_MATERIAL_CHAIN_2013",
    "PARIS_1867_BRAZILIAN_EXPOSITION",
    "BUENOS_AIRES_MID_CENTURY",
    "TEJO_REMY_CHEST_OF_DRAWERS_2016",
}
EXPECTED_CLOSURE_KEYS = {
    "pair_association_closure",
    "higher_order_association_closure",
    "global_composition_coherence_closure",
    "product_association_reachability_closure",
    "computational_space_closure",
    "function3_closure",
}

STRUCTURAL_CLASSES = {
    "ROUND15_COMPOSITION_FIXTURE",
    "ROUND16A_CONNECTED_SUBGRAPH",
    "ROUND16A_PRODUCTION_COMPOSITION",
    "ROUND16A_TOPOLOGY_COMPOSITION",
    "ROUND16_LEGACY_COMPOSITION",
}

CLASS_CONTRACTS = {
    "EVIDENCE_BEARING": {
        "classification_detail": "EVIDENCE_BEARING_INPUT_NOT_YET_GOVERNED_SUPPORT",
        "classification_reason": "Locator-bearing or bounded upstream source record; retained only as an input to scoped governed review.",
        "evidence_use_disposition": "SCOPED_REVIEW_INPUT_NOT_SUPPORT",
        "source_text_review_status": "BOUNDED_UPSTREAM_RECORD_PRESENT_FULL_SOURCE_TEXT_REVIEW_OPEN",
        "rights_review_status": "OPEN_FOR_ANY_SUPPORT_USE",
    },
    "STRUCTURAL_ECHO": {
        "classification_detail": "STRUCTURAL_ECHO_NOT_EVIDENCE",
        "classification_reason": "Prior composition, topology, subgraph, fixture-derived product record, or production read-model descendant; structure is not historical evidence.",
        "evidence_use_disposition": "NOT_EVIDENCE_RECONCILIATION_ONLY",
        "source_text_review_status": "NOT_APPLICABLE_STRUCTURAL_RECORD",
        "rights_review_status": "NOT_APPLICABLE_TO_NON_SUPPORT_CLASSIFICATION",
    },
    "SYNTHETIC_CONTROL": {
        "classification_detail": "SYNTHETIC_CONTROL_NOT_EVIDENCE",
        "classification_reason": "Explicit synthetic n-ary validation control; useful for verifier behavior only.",
        "evidence_use_disposition": "NOT_EVIDENCE_TEST_CONTROL_ONLY",
        "source_text_review_status": "NOT_APPLICABLE_SYNTHETIC_CONTROL",
        "rights_review_status": "NOT_APPLICABLE_TO_NON_SUPPORT_CLASSIFICATION",
    },
    "NEGATIVE_CONTEXT": {
        "classification_detail": "NEGATIVE_CONTEXT_OR_UNSUPPORTED_SYNTHESIS",
        "classification_reason": "Upstream handoff explicitly records flattening/intermediary-role risk and cannot support the proposed topology.",
        "evidence_use_disposition": "NEGATIVE_OR_CONFLICT_INPUT_NOT_SUPPORT",
        "source_text_review_status": "BOUNDED_UPSTREAM_NEGATIVE_CONTEXT_REVIEWED",
        "rights_review_status": "NOT_APPLICABLE_TO_NON_SUPPORT_CLASSIFICATION",
    },
    "SOURCE_CONTAINER_COOCCURRENCE": {
        "classification_detail": "SOURCE_CONTAINER_COOCCURRENCE",
        "classification_reason": "Multiple pair evidence rows reuse one institutional exhibition source container; container membership does not support the exact group.",
        "evidence_use_disposition": "NOT_EVIDENCE_SOURCE_CONTAINER_ONLY",
        "source_text_review_status": "SOURCE_CONTAINER_RECORD_PRESENT_GROUP_TEXT_SUPPORT_ABSENT",
        "rights_review_status": "NOT_APPLICABLE_TO_NON_SUPPORT_CLASSIFICATION",
    },
}

PINNED_INPUT_SHA256 = {
    str(V2_OCCURRENCES): "1685e5bfdab735657ce78499b2597e6a20aecd7402d97f515b162a5d16009cd6",
    str(V2_FAMILIES): "cd4c3ca997c0f4cd5919d4e29d89ca45291fae4f70f78a49742aafb9c76baea7",
    str(V2_CROSSWALK): "dfc1751482f3e74de78c2a94fd46f20eb3538d26e8c6bbf94482cac9534e770a",
    str(V2_CENSUS): "b40e28810aa59a0e2ac926e403cf45ba9b032b465ee54a62fd7e32b2f6e4fe31",
    str(METHOD): "f37ff8aa97d3c9a0d417ee0a9e6ef96971b0c0985bf88bf7bb59af8da8d106e7",
    str(ACTIVE_GRAPH): "1dee15d7cc0a9aa25f2a4a0fd7a352d2df5e7eacf88bd71badec5ebd476063bd",
    str(R14_PROVENANCE): "3bfc526c160909838da90db700a72c987e1b9ea80fb605358a400951c64c2d8c",
    str(R16A_REGISTRY): "51c3e29909a8aa5226a7d18ebaef896aa52c48be6725d722c869515874c6c24d",
    str(R10_ATTESTATIONS): "62b56052829d23cd2cf820a232479f74cbf663d64465cdc242900e71220df2a8",
    str(R10_CLUSTERS): "0fca1a4995577ddb3e33e1a12bebb18ccd14e74684755c26749029722dfb2ccd",
    str(R9_ATTESTATIONS): "f2f8ff68c9263ee360aa84f73bc3adb55e5b18b41f86f03faa18522645193240",
    str(R13_EVIDENCE): "c3d24a2a6f90d1e0b6ce7f0f483d04a752761cb3699294039c97778ed84dd714",
    str(R16A_READ_MODEL): "53eaf59c95446eeb3781a7153183c54b3ff59fd52f21744cc917053959dfdcc9",
    str(R14_NARY): "32c8fa359e6bd14d3d2e4d62c4a276a1bcfa6daee1c29e9b18bffb427f6e0e56",
    str(R15_FIXTURES): "0322c715166f4ed8cb4603a5a1f10db69512ef3f41386cec6450c6d52813badb",
    str(R16_LEGACY): "cad6669c93a52924a17d31d07a16b1e1e5b0ffa06917f3cd467a5f2db003393f",
}

EXPECTED_INPUT_PATHS = tuple(PINNED_INPUT_SHA256) + (str(BUILDER),)
EXPECTED_OUTPUT_PATHS = {
    str(OCCURRENCE_OUTPUT),
    str(FAMILY_OUTPUT),
    str(QUEUE_OUTPUT),
    str(INPUT_MANIFEST),
    str(GAP_OUTPUT),
    str(CENSUS_OUTPUT),
    str(RESEARCH_NOTE),
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_hash(row: dict[str, Any]) -> str:
    return sha256_text(canonical_json(row))


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    csv.field_size_limit(sys.maxsize)
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, dialect="excel-tab")
        return list(reader.fieldnames or []), list(reader)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def classify_occurrence(row: dict[str, str]) -> str:
    trigger_class = row["trigger_class"]
    if trigger_class in STRUCTURAL_CLASSES:
        return "STRUCTURAL_ECHO"
    if trigger_class == "ROUND14_NARY_FIXTURE":
        return "SYNTHETIC_CONTROL"
    if trigger_class == "EXPLICIT_CLUSTER_NEAR_MISS":
        return "NEGATIVE_CONTEXT"
    if trigger_class == "ROUND14_ARCHIVE_EXACT_CONTEXT_DUPLICATE":
        return "SOURCE_CONTAINER_COOCCURRENCE"
    return "EVIDENCE_BEARING"


def strip_record_ref(value: str) -> tuple[str | None, str]:
    if "#" in value:
        path, record_id = value.rsplit("#", 1)
        return path, record_id
    return None, value


def verify_record_hashes(rows: list[dict[str, str]], hash_field: str = "record_sha256") -> list[str]:
    failures: list[str] = []
    for index, row in enumerate(rows, 1):
        material = dict(row)
        actual = material.pop(hash_field, "")
        if actual != row_hash(material):
            failures.append(str(index))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--output", default=str(DEFAULT_VERIFICATION))
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    output = repo / args.output
    checks: list[dict[str, Any]] = []
    failures: list[str] = []
    development_oracle_corrections = [
        {
            "failure": "The first development run compared a canonical-JSON occurrence-ID-set hash against a newline-delimited-set hash constant.",
            "classification": "VERIFIER_DEVELOPMENT_ORACLE_BUG_NOT_EVIDENCE_MISMATCH",
            "correction": "Pinned the independently reconstructed canonical-JSON set hash 87e345446cec2c78a5f8b7fc6d864e77ea5f70ba36bed8448e133478d701eaa0.",
            "status": "CORRECTED_BEFORE_FINAL_VERIFICATION",
        },
        {
            "failure": "The second development run looked up topology_composition_id, while the immutable registry identifies topology records with composition_id.",
            "classification": "VERIFIER_DEVELOPMENT_ORACLE_BUG_NOT_EVIDENCE_MISMATCH",
            "correction": "Reconstructed the topology index from canonical-composition-registry-v2.json:topology_compositions[].composition_id.",
            "status": "CORRECTED_BEFORE_FINAL_VERIFICATION",
        },
    ]

    def require(check_id: str, condition: bool, detail: Any = None) -> None:
        status = "PASS" if condition else "FAIL"
        record: dict[str, Any] = {"check_id": check_id, "status": status}
        if detail not in (None, [], {}, ""):
            record["detail"] = detail
        checks.append(record)
        if not condition:
            failures.append(check_id)

    required_paths = set(EXPECTED_INPUT_PATHS) | EXPECTED_OUTPUT_PATHS | {str(BUILD_RECEIPT)}
    missing = sorted(path for path in required_paths if not (repo / path).is_file())
    require("REQUIRED_ARTIFACTS_PRESENT", not missing, missing)
    if missing:
        payload = {"format": "trace-round16b-evidence-disposition-tranche-a-independent-verification-v1", "status": "FAIL", "failures": failures, "checks": checks}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 1

    # Pin checkpoint-004 and all upstream inputs independently of the builder.
    pin_failures = {
        path: {"expected": expected, "actual": sha256_file(repo / path)}
        for path, expected in PINNED_INPUT_SHA256.items()
        if sha256_file(repo / path) != expected
    }
    require("IMMUTABLE_INPUT_SHA256_PINS_EXACT", not pin_failures, pin_failures)

    family_headers, v2_family_rows = read_tsv(repo / V2_FAMILIES)
    occurrence_headers, v2_occurrence_rows = read_tsv(repo / V2_OCCURRENCES)
    require("CHECKPOINT004_FAMILY_UNIVERSE_EXACT", len(v2_family_rows) == 35 and len({row["participant_set_key"] for row in v2_family_rows}) == 35)
    require("CHECKPOINT004_OCCURRENCE_UNIVERSE_EXACT", len(v2_occurrence_rows) == 359 and len({row["trigger_occurrence_id"] for row in v2_occurrence_rows}) == 359)
    selected_keys = [spec[0] for spec in FAMILY_SPECS]
    family_by_key = {row["participant_set_key"]: row for row in v2_family_rows}
    selected_family_rows = [family_by_key[key] for key in selected_keys if key in family_by_key]
    require("GOVERNED_TRANCHE_SELECTOR_EXACT_11", len(selected_family_rows) == 11 and len(set(selected_keys)) == 11)

    selected_occurrences = [row for row in v2_occurrence_rows if row["participant_set_key"] in set(selected_keys)]
    selected_occurrences.sort(key=lambda row: (selected_keys.index(row["participant_set_key"]), row["trigger_occurrence_id"]))
    selected_occurrence_by_id = {row["trigger_occurrence_id"]: row for row in selected_occurrences}
    selected_id_hash = sha256_text(canonical_json(sorted(selected_occurrence_by_id)))
    require("SELECTED_OCCURRENCE_ID_SET_EXACT_112", len(selected_occurrences) == len(selected_occurrence_by_id) == 112 and selected_id_hash == "87e345446cec2c78a5f8b7fc6d864e77ea5f70ba36bed8448e133478d701eaa0", selected_id_hash)
    source_occurrence_hash_failures = []
    for row in selected_occurrences:
        material = dict(row)
        actual = material.pop("occurrence_sha256")
        if row_hash(material) != actual:
            source_occurrence_hash_failures.append(row["trigger_occurrence_id"])
    require("SELECTED_SOURCE_OCCURRENCE_ROW_HASHES_EXACT", not source_occurrence_hash_failures, source_occurrence_hash_failures[:10])

    expected_class_by_id = {row["trigger_occurrence_id"]: classify_occurrence(row) for row in selected_occurrences}
    independent_class_counts = dict(sorted(Counter(expected_class_by_id.values()).items()))
    require("INDEPENDENT_OCCURRENCE_CLASS_DISTRIBUTION_EXACT", independent_class_counts == EXPECTED_CLASS_COUNTS, independent_class_counts)

    # Independently index the upstream sources named by the immutable occurrence rows.
    _, r14_rows = read_tsv(repo / R14_PROVENANCE)
    _, r10_rows = read_tsv(repo / R10_ATTESTATIONS)
    _, cluster_rows = read_tsv(repo / R10_CLUSTERS)
    _, r9_rows = read_tsv(repo / R9_ATTESTATIONS)
    _, r13_rows = read_tsv(repo / R13_EVIDENCE)
    row_indexes: dict[str, tuple[str, dict[str, dict[str, str]], str | None, str | None, str]] = {
        str(R14_PROVENANCE): ("evidence_id", {row["evidence_id"]: row for row in r14_rows}, "source_id", "locator", "ROW_HASH"),
        str(R10_ATTESTATIONS): ("grammar_attestation_id", {row["grammar_attestation_id"]: row for row in r10_rows}, "source_id", "page_section_locator", "EVIDENCE_SHA"),
        str(R10_CLUSTERS): ("cluster_handoff_id", {row["cluster_handoff_id"]: row for row in cluster_rows}, "source_ids", None, "ROW_HASH"),
        str(R9_ATTESTATIONS): ("attestation_id", {row["attestation_id"]: row for row in r9_rows}, "source_id", "page_or_section_locator", "CONTEXT_SHA"),
        str(R13_EVIDENCE): ("evidence_id", {row["evidence_id"]: row for row in r13_rows}, "source_id", "locator", "ROW_HASH"),
    }
    registry = read_json(repo / R16A_REGISTRY)
    subgraphs = {row["association_subgraph_id"]: row for row in registry["association_subgraphs"]}
    topologies = {row["composition_id"]: row for row in registry["topology_compositions"]}
    read_model = read_json(repo / R16A_READ_MODEL)
    production = read_model["compositions"]
    r15_fixtures = {row["fixtureId"]: row for row in read_json(repo / R15_FIXTURES)["fixtures"]}
    nary_fixtures = {row["fixtureId"]: row for row in read_json(repo / R14_NARY)["fixtures"]}
    legacy_compositions = {row["compositionId"]: row for row in read_json(repo / R16_LEGACY)["compositions"]}

    def resolve_occurrence(row: dict[str, str]) -> tuple[list[str], list[str], list[str], list[str]]:
        record_ids: list[str] = []
        source_ids: list[str] = []
        locators: list[str] = []
        hashes: list[str] = []
        refs = json.loads(row["input_record_refs_json"])
        trigger_class = row["trigger_class"]
        for raw_ref in refs:
            override_path, record_id = strip_record_ref(raw_ref)
            source_path = override_path or row["source_path"]
            record_ids.append(record_id)
            if source_path in row_indexes:
                _, index, source_field, locator_field, hash_mode = row_indexes[source_path]
                upstream = index.get(record_id)
                if upstream is None:
                    raise KeyError(f"{source_path}#{record_id}")
                if source_field and upstream.get(source_field):
                    source_ids.extend(value.strip() for value in upstream[source_field].split(";") if value.strip())
                if locator_field and upstream.get(locator_field):
                    locators.append(upstream[locator_field])
                if hash_mode == "ROW_HASH":
                    hashes.append(row_hash(upstream))
                elif hash_mode == "EVIDENCE_SHA":
                    hashes.append(upstream["evidence_sha256"])
                elif hash_mode == "CONTEXT_SHA":
                    hashes.append(upstream["context_sha256"])
            elif trigger_class == "ROUND16A_CONNECTED_SUBGRAPH":
                hashes.append(subgraphs[record_id]["association_subgraph_hash"])
            elif trigger_class == "ROUND16A_TOPOLOGY_COMPOSITION":
                hashes.append(topologies[record_id]["topology_composition_hash"])
            elif trigger_class == "ROUND16A_PRODUCTION_COMPOSITION":
                hashes.append(production[record_id]["semantic_hash"])
            elif trigger_class == "ROUND15_COMPOSITION_FIXTURE":
                hashes.append(row_hash(r15_fixtures[record_id]))
            elif trigger_class == "ROUND14_NARY_FIXTURE":
                hashes.append(row_hash(nary_fixtures[record_id]))
            elif trigger_class == "ROUND16_LEGACY_COMPOSITION":
                hashes.append(row_hash(legacy_compositions[record_id]))
            else:
                raise KeyError(f"unresolved upstream reference {source_path}#{record_id}")
        return sorted(record_ids), sorted(set(source_ids)), sorted(set(locators)), sorted(hashes)

    upstream_expected: dict[str, tuple[list[str], list[str], list[str], list[str]]] = {}
    upstream_failures: list[str] = []
    for row in selected_occurrences:
        try:
            resolved = resolve_occurrence(row)
            upstream_expected[row["trigger_occurrence_id"]] = resolved
            if resolved[3] != sorted(json.loads(row["content_hashes_json"])):
                upstream_failures.append(row["trigger_occurrence_id"])
        except (KeyError, TypeError, ValueError) as exc:
            upstream_failures.append(f"{row['trigger_occurrence_id']}:{exc}")
    require("ALL_112_UPSTREAM_RECORDS_AND_CONTENT_HASHES_RECONSTRUCTED", not upstream_failures, upstream_failures[:10])

    output_occurrence_headers, output_occurrences = read_tsv(repo / OCCURRENCE_OUTPUT)
    output_occurrence_by_id = {row["trigger_occurrence_id"]: row for row in output_occurrences}
    require("OUTPUT_OCCURRENCE_COVERAGE_EXACT", len(output_occurrences) == len(output_occurrence_by_id) == 112 and set(output_occurrence_by_id) == set(selected_occurrence_by_id))
    require("OUTPUT_OCCURRENCE_RECORD_HASHES_EXACT", not verify_record_hashes(output_occurrences), verify_record_hashes(output_occurrences)[:10])

    copied_field_map = {
        "candidate_id": "candidate_id",
        "participant_set_key": "participant_set_key",
        "trigger_id": "trigger_id",
        "trigger_class": "trigger_class",
        "emission_kind": "emission_kind",
        "source_path": "source_path",
        "input_surface_id": "input_surface_id",
        "input_record_refs_json": "input_record_refs_json",
        "source_locator": "locator",
        "content_hashes_json": "content_hashes_json",
    }
    occurrence_failures: list[str] = []
    for occurrence_id, source in selected_occurrence_by_id.items():
        actual = output_occurrence_by_id.get(occurrence_id)
        if actual is None:
            continue
        family_ordinal = selected_keys.index(source["participant_set_key"]) + 1
        if actual["parent_checkpoint_sha"] != PARENT_SHA or actual["review_tranche"] != TRANCHE or int(actual["family_ordinal"]) != family_ordinal:
            occurrence_failures.append(occurrence_id)
            continue
        if actual["source_occurrence_sha256"] != source["occurrence_sha256"]:
            occurrence_failures.append(occurrence_id)
            continue
        if any(actual[out_field] != source[in_field] for out_field, in_field in copied_field_map.items()):
            occurrence_failures.append(occurrence_id)
            continue
        expected_class = expected_class_by_id[occurrence_id]
        expected_upstream = upstream_expected.get(occurrence_id)
        if actual["occurrence_evidence_class"] != expected_class or expected_upstream is None:
            occurrence_failures.append(occurrence_id)
            continue
        if (
            json.loads(actual["upstream_record_ids_json"]) != expected_upstream[0]
            or json.loads(actual["upstream_source_ids_json"]) != expected_upstream[1]
            or json.loads(actual["upstream_locators_json"]) != expected_upstream[2]
        ):
            occurrence_failures.append(occurrence_id)
            continue
        contract = CLASS_CONTRACTS[expected_class]
        if any(actual[field] != value for field, value in contract.items()):
            occurrence_failures.append(occurrence_id)
            continue
        expected_scope = FAMILY_SPECS[family_ordinal - 1][2]
        if (
            actual["exact_group_support_status"] != "NOT_GOVERNED_SUPPORT"
            or actual["human_review_status"] != "OPEN_FOR_ANY_ASSOCIATION_ACTIVATION"
            or actual["counterevidence_review_status"] != "OPEN_FOR_ANY_ASSOCIATION_ACTIVATION"
            or actual["scope_split_need"] != expected_scope
            or actual["product_eligibility"] != "INELIGIBLE_NOT_GOVERNED_ASSOCIATION_SUPPORT"
            or actual["pair_projection_created"] != "false"
            or actual["association_activation_created"] != "false"
        ):
            occurrence_failures.append(occurrence_id)
    require("OUTPUT_OCCURRENCE_ROWS_INDEPENDENTLY_RECONCILED", not occurrence_failures, occurrence_failures[:10])

    output_family_headers, output_families = read_tsv(repo / FAMILY_OUTPUT)
    output_family_by_key = {row["participant_set_key"]: row for row in output_families}
    require("OUTPUT_FAMILY_COVERAGE_EXACT_11", len(output_families) == len(output_family_by_key) == 11 and set(output_family_by_key) == set(selected_keys))
    require("OUTPUT_FAMILY_RECORD_HASHES_EXACT", not verify_record_hashes(output_families), verify_record_hashes(output_families)[:10])

    graph = read_json(repo / ACTIVE_GRAPH)
    active_edges = graph["edges"]
    family_failures: list[str] = []
    reconstructed_dispositions: Counter[str] = Counter()
    for ordinal, (key, disposition, scope_status, queue_count) in enumerate(FAMILY_SPECS, 1):
        source_family = family_by_key[key]
        actual = output_family_by_key.get(key)
        if actual is None:
            continue
        family_occurrences = [row for row in selected_occurrences if row["participant_set_key"] == key]
        ids = sorted(row["trigger_occurrence_id"] for row in family_occurrences)
        classes = Counter(expected_class_by_id[value] for value in ids)
        labels = set(json.loads(source_family["canonical_labels_json"]))
        active_pairs = sorted(
            edge["association_id"]
            for edge in active_edges
            if {edge["label_a"], edge["label_b"]}.issubset(labels)
        )
        review_ids = sorted({value for row in family_occurrences if expected_class_by_id[row["trigger_occurrence_id"]] not in {"STRUCTURAL_ECHO", "SYNTHETIC_CONTROL"} for value in upstream_expected[row["trigger_occurrence_id"]][0]})
        review_locators = sorted({value for row in family_occurrences if expected_class_by_id[row["trigger_occurrence_id"]] not in {"STRUCTURAL_ECHO", "SYNTHETIC_CONTROL"} for value in upstream_expected[row["trigger_occurrence_id"]][2]})
        common_ok = (
            actual["parent_checkpoint_sha"] == PARENT_SHA
            and actual["review_tranche"] == TRANCHE
            and int(actual["family_ordinal"]) == ordinal
            and actual["candidate_id"] == source_family["candidate_id"]
            and actual["candidate_object_kind"] == source_family["candidate_object_kind"]
            and actual["participant_sense_ids_json"] == source_family["participant_sense_ids_json"]
            and actual["canonical_labels_json"] == source_family["canonical_labels_json"]
            and actual["arity"] == source_family["arity"]
            and int(actual["linked_occurrence_count"]) == len(ids)
            and actual["linked_occurrence_ids_sha256"] == sha256_text(canonical_json(ids))
            and json.loads(actual["occurrence_class_counts_json"]) == dict(sorted(classes.items()))
            and int(actual["evidence_bearing_input_count"]) == classes["EVIDENCE_BEARING"]
            and int(actual["structural_echo_count"]) == classes["STRUCTURAL_ECHO"]
            and int(actual["synthetic_control_count"]) == classes["SYNTHETIC_CONTROL"]
            and int(actual["negative_context_count"]) == classes["NEGATIVE_CONTEXT"]
            and int(actual["source_container_cooccurrence_count"]) == classes["SOURCE_CONTAINER_COOCCURRENCE"]
            and json.loads(actual["review_input_record_ids_json"]) == review_ids
            and json.loads(actual["review_locators_json"]) == review_locators
            and int(actual["internal_possible_pair_count"]) == math.comb(int(source_family["arity"]), 2)
            and int(actual["internal_active_pair_count"]) == len(active_pairs)
            and json.loads(actual["internal_active_pair_ids_json"]) == active_pairs
            and actual["final_parent_disposition"] == disposition
            and actual["parent_disposition_status"] == "FINAL_FOR_UNSPLIT_PARENT_REVIEW_FAMILY_FAIL_CLOSED"
            and actual["scope_split_or_reroute_status"] == scope_status
            and int(actual["conditional_queue_count"]) == queue_count
            and actual["direct_group_support_status"] == "NO_ACTIVE_DIRECT_SUPPORT_FOR_UNSPLIT_PARENT"
            and actual["composite_group_support_status"] == "NO_ACTIVE_COMPOSITE_SUPPORT_FOR_UNSPLIT_PARENT"
            and actual["global_coherence_status"] == "FAIL_CLOSED_NOT_PASSED"
            and actual["human_review_status"] == "OPEN_FOR_ANY_ASSOCIATION_ACTIVATION"
            and actual["counterevidence_review_status"] == "OPEN_FOR_ANY_ASSOCIATION_ACTIVATION"
            and actual["association_identity_status"] == "NOT_CREATED_PARENT_IS_REVIEW_FAMILY_NOT_ASSOCIATION"
            and actual["association_activation_status"] == "INACTIVE"
            and actual["product_eligibility"] == "INELIGIBLE_UNSPLIT_PARENT_NOT_GOVERNED_ASSOCIATION"
            and int(actual["pair_projection_count"]) == 0
        )
        expected_rights = "OPEN_FOR_CONDITIONAL_CHILD_OR_REROUTE_REVIEW" if queue_count else "NO_SUPPORT_USE"
        expected_text = "OPEN_FOR_CONDITIONAL_CHILD_OR_REROUTE_REVIEW" if queue_count else "NO_GROUP_SUPPORT_TEXT"
        if actual["rights_review_status"] != expected_rights or actual["source_text_review_status"] != expected_text:
            common_ok = False
        nonclaims = json.loads(actual["explicit_nonclaims_json"])
        occurrence_nonclaims = {row["explicit_nonclaims_json"] for row in output_occurrences if row["participant_set_key"] == key}
        if not nonclaims or occurrence_nonclaims != {actual["explicit_nonclaims_json"]}:
            common_ok = False
        if not common_ok:
            family_failures.append(key)
        reconstructed_dispositions[disposition] += 1
    require("FAMILY_DISPOSITIONS_AND_ACTIVE_PAIRS_INDEPENDENTLY_RECONSTRUCTED", not family_failures, family_failures)
    require("FINAL_PARENT_DISPOSITION_DISTRIBUTION_EXACT", dict(sorted(reconstructed_dispositions.items())) == EXPECTED_DISPOSITION_COUNTS)
    clique_invalid_keys = {
        key for key, row in output_family_by_key.items()
        if int(row["internal_active_pair_count"]) == int(row["internal_possible_pair_count"])
    }
    require("PAIRWISE_CLIQUES_DO_NOT_BECOME_GROUP_SUPPORT", clique_invalid_keys == {FAMILY_SPECS[1][0], FAMILY_SPECS[4][0]} and all(output_family_by_key[key]["global_coherence_status"] == "FAIL_CLOSED_NOT_PASSED" for key in clique_invalid_keys), sorted(clique_invalid_keys))

    queue_headers, queue_rows = read_tsv(repo / QUEUE_OUTPUT)
    require("CONDITIONAL_QUEUE_RECORD_HASHES_EXACT", not verify_record_hashes(queue_rows), verify_record_hashes(queue_rows))
    queue_parent_counts = Counter(row["parent_candidate_id"] for row in queue_rows)
    expected_parent_counts = {
        family_by_key[key]["candidate_id"]: count for key, _, _, count in FAMILY_SPECS if count
    }
    queue_evidence_failures: list[str] = []
    for row in queue_rows:
        parent_key = row["parent_candidate_id"].removeprefix("R16B-LOCAL-FAMILY:")
        parent_evidence_ids = {
            source["trigger_occurrence_id"] for source in selected_occurrences
            if source["participant_set_key"] == parent_key and expected_class_by_id[source["trigger_occurrence_id"]] == "EVIDENCE_BEARING"
        }
        queue_occurrence_ids = set(json.loads(row["evidence_occurrence_ids_json"]))
        if not queue_occurrence_ids or not queue_occurrence_ids.issubset(parent_evidence_ids):
            queue_evidence_failures.append(row["queue_id"])
        if (
            row["parent_checkpoint_sha"] != PARENT_SHA
            or row["review_tranche"] != TRANCHE
            or row["queue_status"] != "CONDITIONAL_REVIEW_ONLY_NOT_ASSOCIATION"
            or row["rights_review_status"] != "OPEN"
            or row["source_text_review_status"] != "OPEN_REVIEW_LOCATOR_BEARING_INPUT_AGAINST_LAWFULLY_ACCESSED_TEXT"
            or row["human_review_status"] != "OPEN_EXTERNAL_DESIGN_HISTORY_REVIEW"
            or row["counterevidence_review_status"] != "OPEN_FALSIFICATION_AND_CONFLICT_SEARCH"
            or row["association_identity_created"] != "false"
            or row["association_active"] != "false"
            or row["pair_projection_created"] != "false"
            or row["product_eligibility"] != "INELIGIBLE_PENDING_ALL_GOVERNED_GATES"
            or not json.loads(row["explicit_nonclaims_json"])
        ):
            queue_evidence_failures.append(row["queue_id"])
    require("CONDITIONAL_QUEUE_COVERAGE_EXACT", len(queue_rows) == 10 and len({row["queue_id"] for row in queue_rows}) == 10 and set(row["scope_key"] for row in queue_rows) == EXPECTED_SCOPE_KEYS and dict(sorted(Counter(row["queue_action"] for row in queue_rows).items())) == EXPECTED_QUEUE_ACTION_COUNTS and dict(queue_parent_counts) == expected_parent_counts)
    require("CONDITIONAL_QUEUE_SEPARATE_INACTIVE_AND_BLOCKED", not queue_evidence_failures, sorted(set(queue_evidence_failures)))
    require("CONDITIONAL_QUEUE_DOES_NOT_MUTATE_FINAL_PARENT_DISPOSITIONS", all(row["parent_disposition_status"] == "FINAL_FOR_UNSPLIT_PARENT_REVIEW_FAMILY_FAIL_CLOSED" for row in output_families) and all(row["queue_status"] != "GOVERNED_ASSOCIATION" for row in queue_rows))

    manifest_headers, manifest_rows = read_tsv(repo / INPUT_MANIFEST)
    manifest_failures: list[str] = []
    for ordinal, row in enumerate(manifest_rows, 1):
        path = repo / row["path"]
        expected_records = 1
        if path.suffix == ".tsv":
            _, records = read_tsv(path)
            expected_records = len(records)
        material = dict(row)
        actual_record_hash = material.pop("record_sha256")
        if (
            row["parent_checkpoint_sha"] != PARENT_SHA
            or int(row["input_ordinal"]) != ordinal
            or not path.is_file()
            or int(row["bytes"]) != path.stat().st_size
            or int(row["input_record_count"]) != expected_records
            or row["sha256"] != sha256_file(path)
            or row["pinned_sha256"] != row["sha256"]
            or row["pin_match"] != "true"
            or actual_record_hash != row_hash(material)
        ):
            manifest_failures.append(row["path"])
    require("INPUT_MANIFEST_ALL_17_HASHES_EXACT", len(manifest_rows) == 17 and tuple(row["path"] for row in manifest_rows) == EXPECTED_INPUT_PATHS and not manifest_failures, manifest_failures)

    gap_headers, gap_rows = read_tsv(repo / GAP_OUTPUT)
    gap_statuses = {row["gap_id"]: row["status"] for row in gap_rows}
    require("RECURSIVE_GAPS_PRESERVED_AND_HASHED", len(gap_rows) == 7 and set(gap_statuses) == {f"GAP-{value:03d}" for value in range(10, 17)} and not verify_record_hashes(gap_rows), gap_statuses)
    require("RECURSIVE_GAPS_RETAIN_OPEN_AUTHORITY", gap_statuses.get("GAP-010") == "OPEN_24_FAMILIES" and gap_statuses.get("GAP-011") == "OPEN_13_INPUTS" and gap_statuses.get("GAP-012") == "OPEN_10_CONDITIONAL_RECORDS" and gap_statuses.get("GAP-013") == "NOT_STARTED" and gap_statuses.get("GAP-016") == "OPEN", gap_statuses)

    census = read_json(repo / CENSUS_OUTPUT)
    require(
        "CENSUS_COUNTS_AND_FAIL_CLOSED_BOUNDARY_EXACT",
        census.get("format") == "trace-round16b-evidence-disposition-tranche-a-census-v1"
        and census.get("source_sha") == SOURCE_SHA
        and census.get("source_tree") == SOURCE_TREE
        and census.get("parent_checkpoint_sha") == PARENT_SHA
        and census.get("review_tranche") == TRANCHE
        and census.get("tranche_family_count") == 11
        and census.get("tranche_linked_occurrence_count") == 112
        and census.get("conditional_scoped_child_or_reroute_queue_count") == 10
        and census.get("remaining_undisposed_checkpoint004_family_count") == 24
        and census.get("occurrence_evidence_class_counts") == EXPECTED_CLASS_COUNTS
        and census.get("final_parent_disposition_counts") == EXPECTED_DISPOSITION_COUNTS
        and census.get("conditional_queue_action_counts") == EXPECTED_QUEUE_ACTION_COUNTS
        and census.get("association_identity_created_count") == 0
        and census.get("association_activation_count") == 0
        and census.get("pair_projection_created_count") == 0
        and census.get("product_eligible_count") == 0
        and census.get("active_pending_review_count") == 0
        and "Conditional scoped children and reroutes are inactive review queue records" in census.get("semantic_boundary", ""),
        census,
    )
    require("ALL_SIX_CLOSURES_EXACTLY_FALSE", set(census.get("closure", {})) == EXPECTED_CLOSURE_KEYS and all(value is False for value in census["closure"].values()), census.get("closure"))

    receipt = read_json(repo / BUILD_RECEIPT)
    output_hash_failures: list[str] = []
    for path, metadata in receipt.get("output_hashes", {}).items():
        target = repo / path
        if not target.is_file() or target.stat().st_size != metadata.get("bytes") or sha256_file(target) != metadata.get("sha256"):
            output_hash_failures.append(path)
    expected_aggregate = sha256_text(canonical_json(receipt.get("output_hashes", {})))
    require("BUILD_RECEIPT_ALL_OUTPUT_HASHES_EXACT", set(receipt.get("output_hashes", {})) == EXPECTED_OUTPUT_PATHS and not output_hash_failures and receipt.get("aggregate_output_sha256") == expected_aggregate, output_hash_failures)
    require(
        "BUILD_RECEIPT_COUNTS_AND_STATUS_EXACT",
        receipt.get("format") == "trace-round16b-evidence-disposition-tranche-a-build-receipt-v1"
        and receipt.get("builder_version") == BUILDER_VERSION
        and receipt.get("source_sha") == SOURCE_SHA
        and receipt.get("source_tree") == SOURCE_TREE
        and receipt.get("parent_checkpoint_sha") == PARENT_SHA
        and receipt.get("review_tranche") == TRANCHE
        and receipt.get("input_count") == 17
        and receipt.get("input_manifest_sha256") == sha256_file(repo / INPUT_MANIFEST)
        and receipt.get("output_count_excluding_receipt") == 7
        and receipt.get("family_count") == 11
        and receipt.get("linked_occurrence_count") == 112
        and receipt.get("conditional_queue_count") == 10
        and receipt.get("occurrence_evidence_class_counts") == EXPECTED_CLASS_COUNTS
        and receipt.get("association_identity_created_count") == 0
        and receipt.get("association_activation_count") == 0
        and receipt.get("pair_projection_created_count") == 0
        and receipt.get("closure_flags_true_count") == 0
        and receipt.get("status") == "PASS_FAIL_CLOSED_TRANCHE_A",
        receipt,
    )

    # Structural independence: hash-only observation of the builder plus AST
    # inspection proving this module neither imports nor executes it.
    verifier_path = Path(__file__).resolve()
    builder_path = (repo / BUILDER).resolve()
    verifier_source = verifier_path.read_text(encoding="utf-8")
    parsed = ast.parse(verifier_source)
    imported_modules: list[str] = []
    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
    builder_imported = any("build_evidence_disposition_tranche_a" in name for name in imported_modules)
    builder_sha = sha256_file(builder_path)
    verifier_sha = sha256_file(verifier_path)
    require("GENERATOR_VERIFIER_IMPLEMENTATION_INDEPENDENCE", not builder_imported and builder_sha != verifier_sha, {"builder_sha256": builder_sha, "verifier_sha256": verifier_sha, "imported_modules": imported_modules})
    require(
        "PRE_FINAL_DEVELOPMENT_ORACLE_FAILURES_PRESERVED",
        len(development_oracle_corrections) == 2
        and all(row["classification"] == "VERIFIER_DEVELOPMENT_ORACLE_BUG_NOT_EVIDENCE_MISMATCH" for row in development_oracle_corrections)
        and all(row["status"] == "CORRECTED_BEFORE_FINAL_VERIFICATION" for row in development_oracle_corrections),
        development_oracle_corrections,
    )

    verification = {
        "format": "trace-round16b-evidence-disposition-tranche-a-independent-verification-v1",
        "status": "PASS" if not failures else "FAIL",
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "parent_checkpoint_sha": PARENT_SHA,
        "review_tranche": TRANCHE,
        "selected_family_count": len(selected_family_rows),
        "selected_occurrence_count": len(selected_occurrences),
        "selected_occurrence_id_set_sha256": selected_id_hash,
        "occurrence_evidence_class_counts": independent_class_counts,
        "final_parent_disposition_counts": dict(sorted(reconstructed_dispositions.items())),
        "conditional_queue_count": len(queue_rows),
        "association_identity_created_count": 0,
        "association_activation_count": 0,
        "pair_projection_created_count": 0,
        "product_eligible_count": 0,
        "closure": {key: False for key in sorted(EXPECTED_CLOSURE_KEYS)},
        "input_manifest_sha256": sha256_file(repo / INPUT_MANIFEST),
        "builder_sha256": builder_sha,
        "verifier_sha256": verifier_sha,
        "generator_module_imported": builder_imported,
        "development_oracle_corrections": development_oracle_corrections,
        "check_count": len(checks),
        "failure_count": len(failures),
        "failures": failures,
        "checks": checks,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(verification, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{verification['status']}: {len(checks) - len(failures)}/{len(checks)} checks; output={output}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
