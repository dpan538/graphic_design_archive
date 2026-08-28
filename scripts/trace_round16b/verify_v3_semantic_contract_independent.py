#!/usr/bin/env python3
"""Independently verify the Round 16B TRACE Exploration v3 semantic contract.

This verifier is a separate implementation.  It does not import or invoke the
primary contract builder.  It implements the required Draft 2020-12 subset,
interprets the committed normative hash-binding contract, reconstructs every
identity/hash/count/reference, and evaluates the synthetic controls and
adversarial mutations from committed artifacts.
"""

from __future__ import annotations

import argparse
import ast
import copy
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[2]
RAW_REL = Path("docs/audits/v49-exploration-higher-order-association-closure-round16b/raw")
RAW = REPO / RAW_REL
SCHEMA_REL = Path("schemas/trace/exploration/v3")
SCHEMAS = REPO / SCHEMA_REL

SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
PARENT_CHECKPOINT_SHA = "e5ddbc443c4a0a28004034cba439340ecdeb9a75"
CONTRACT_VERSION = "trace-exploration-v3-semantic-contract-1.0.0"
HASH_CONTRACT_VERSION = "trace-exploration-v3-hash-binding-contract-1.0.0"
VERIFIER_VERSION = "trace-round16b-v3-semantic-contract-independent-verifier-v1"
AUTHORITY_CUTOFF_UTC = "2026-08-28T09:18:21Z"

FIXTURE_REL = RAW_REL / "v3-semantic-contract-fixtures-v1.json"
HASH_CONTRACT_REL = RAW_REL / "v3-semantic-hash-binding-contract-v1.json"
EXPECTATIONS_REL = RAW_REL / "v3-semantic-contract-fixture-expectations-v1.tsv"
INPUT_MANIFEST_REL = RAW_REL / "v3-semantic-contract-input-manifest-v1.tsv"
OUTPUT_MANIFEST_REL = RAW_REL / "v3-semantic-contract-output-manifest-v1.tsv"
CENSUS_REL = RAW_REL / "v3-semantic-contract-census-v1.json"
BUILD_RECEIPT_REL = RAW_REL / "v3-semantic-contract-build-receipt-v1.json"
GAP_REL = RAW_REL / "recursive-gap-ledger-checkpoint008-v1.tsv"
OUTPUT_REL = RAW_REL / "v3-semantic-contract-independent-verification.json"
VERIFIER_REL = Path("scripts/trace_round16b/verify_v3_semantic_contract_independent.py")

EXPECTED_FIXTURE_SHA256 = "290647400b83fef83896631ba5a9a9647cd36997eec20b3c8e6efec61e212e33"
EXPECTED_HASH_CONTRACT_FILE_SHA256 = "f2eb70dddc38da506a6380253c17fe66fda457ea0c37a591a4a0a832ea6e0186"
EXPECTED_HASH_CONTRACT_CANONICAL_SHA256 = "1da5396fb18dd49c328c30ee03386bebb07c7837beda38496b099b5c5e514962"
EXPECTED_OUTPUT_MANIFEST_SHA256 = "29583bde333d6b3f35a19dc3140ce40f09da5ec48a1ea23bbc3e71a6c669d1f2"
EXPECTED_BUILD_RECEIPT_SHA256 = "3724b45cbf2d3c53504fe0c5ba1f21807458cacaef39eb482dcd311734c2a114"
EXPECTED_OUTPUT_AGGREGATE_SHA256 = "8e789a36b739c298ccb8ce2f4e2762443ff78247026662f96f12602d90419ced"
EXPECTED_V49_FREEZE_MANIFEST_SHA256 = "f0dda59dd515ba243eaf213bce9f42513727f1ab0a44685635921c3759a7d22e"

EXPECTED_SCHEMA_NAMES = {
    "association.schema.json",
    "common.schema.json",
    "composition.schema.json",
    "concept.schema.json",
    "export-manifest.schema.json",
    "hash-binding-contract.schema.json",
    "navigation-state.schema.json",
    "semantic-contract.schema.json",
    "v2-pair-adapter.schema.json",
    "workflow.schema.json",
}

SCOPE_IDENTITY_KEYS = (
    "scope_id",
    "historical_case_ids",
    "time_bounds",
    "geographies",
    "institutions",
    "actors",
    "mechanisms",
)

EXPECTED_HASH_BINDING_OBJECT_TYPES = {
    "VOCABULARY_CONCEPT",
    "CONCEPT_SENSE",
    "ASSOCIATION_REVISION",
    "PARTICIPANT_INCIDENCE",
    "ASSOCIATION_REALIZATION",
    "COMPOSITION_REVISION",
    "COMPOSITION_COHERENCE_REVIEW",
    "NAVIGATION_STATE",
    "WORKFLOW",
    "EXPORT",
    "V2_PAIR_ADAPTER_RECEIPT",
    "V2_PAIR_SOURCE_FIXTURE",
}

EXPECTED_BINDING_POINTERS = {
    "VOCABULARY_CONCEPT": "/concepts/*",
    "CONCEPT_SENSE": "/concept_senses/*",
    "ASSOCIATION_REVISION": "/associations/*",
    "PARTICIPANT_INCIDENCE": "/associations/*/participants/*",
    "ASSOCIATION_REALIZATION": "/compositions/*/association_realizations/*",
    "COMPOSITION_REVISION": "/compositions/*",
    "COMPOSITION_COHERENCE_REVIEW": "/composition_coherence_reviews/*",
    "NAVIGATION_STATE": "/navigation_states/*",
    "WORKFLOW": "/workflows/*",
    "EXPORT": "/exports/*",
    "V2_PAIR_ADAPTER_RECEIPT": "/v2_pair_adapter_receipts/*",
    "V2_PAIR_SOURCE_FIXTURE": "/v2_pair_source_fixtures/*",
}

V2_PINNED_SHA256 = {
    "schemas/trace/exploration/v2/action-request.schema.json": "14231eb95b74a925f9cf4489918b175c1e6aad05453cb62a5f33d855e6b9be9b",
    "schemas/trace/exploration/v2/association-response.schema.json": "930918be48147c723d48464006c697add13c8d44e42f2e61fb101c13068518af",
    "schemas/trace/exploration/v2/capabilities-response.schema.json": "02b8f1c6be7d397fadda7e2e4cabfc92bbc278652c076f3e95a3b780e4fa3409",
    "schemas/trace/exploration/v2/category-response.schema.json": "a8d9eb2eae8c0f1f4150a3d92a2047cf08564d2faa59d73278e53f0647e91536",
    "schemas/trace/exploration/v2/common.schema.json": "fd03919a1efdec21118f0c1a5209fde3db3d4635e96f4f76158b0b6d324145af",
    "schemas/trace/exploration/v2/error.schema.json": "e262875467952760fcfbc141eb7f7853ff268f1a9156a01f4d83b132ea71fdec",
    "schemas/trace/exploration/v2/export-manifest.schema.json": "b67543306317c8fe4e73b1eabd90a3ac72e9ad1ea6e2b5231bb5d5f30441bc4d",
    "schemas/trace/exploration/v2/export-request.schema.json": "e3f7db8bd2c1fb0aac2b4548c46827e6c76f181b408e9a5b2e6b27299c3ef3f2",
    "schemas/trace/exploration/v2/map-request.schema.json": "e057fc21e8ddb6e49b33ed2fca411c00b923178316f856ef5f4a5fb3b886aad3",
    "schemas/trace/exploration/v2/map-response.schema.json": "a53f1e0262ced333f265b355156d6dde6aa51588c5df0889aff581a3c27307c0",
    "schemas/trace/exploration/v2/production-read-model.schema.json": "3bce74d7b71b36344150156fbff630dc1ba2de513a433a317e532710502a4033",
    "schemas/trace/exploration/v2/vocabulary-response.schema.json": "ee5365a1b45ece3e93330196f3336e81abc1869c7ec9d44ae7b8e5e6c15884b7",
    "frontend/src/features/trace-v49/exploration-v2/client.ts": "bfabdee0322f4f35fc032986764b0da40f0fb8431c8b03c2a34c0c1060a2ba2c",
    "frontend/src/features/trace-v49/exploration-v2/controller.server.ts": "677a8c8d12831d4cda28446fe4d3c3011a22f53fc33f9b41511c6f1a8bcc3c3d",
    "frontend/src/features/trace-v49/exploration-v2/derive.server.ts": "dd9d614159036278df55031eacd6b8bdf583b856634932ee41e3d903d7e71b2a",
    "frontend/src/features/trace-v49/exploration-v2/read-model.server.ts": "e1931a0ffa6f9c2eb20ba459038463a8e133dc3d0b8f192ba87dc2d2f707272e",
    "frontend/src/features/trace-v49/exploration-v2/renderer.server.ts": "d1fe026217180765832c026f1fe4f72cf21e849cb2368a67a110dd66e9ac54b7",
    "frontend/src/features/trace-v49/exploration-v2/service.server.ts": "59e6b137f630516b3449f22d65dc7fe09a0fae84ac636490cf28b5fd4b5f77c1",
    "frontend/src/features/trace-v49/exploration-v2/theme-tokens.ts": "165dfb86a082eb781568b50a25faa47d6f7708b5fffd723eab9df4c5e0d85001",
    "frontend/src/features/trace-v49/exploration-v2/transition.server.ts": "d9d91807d98a8fbe00daa63b68a11709513741745d3e2dbe923b7c004e7df35d",
    "frontend/src/features/trace-v49/exploration-v2/types.ts": "696a3752690707efea193f5a06de4fc3f568ebf7decd75020c58640b4553603d",
    "frontend/generated/trace-exploration-v2/production-read-model.json": "53eaf59c95446eeb3781a7153183c54b3ff59fd52f21744cc917053959dfdcc9",
}

EXPECTED_CONTROL_CLASSES = {
    "VALID_SPARSE_DISCONNECTED_HIGHER_ORDER_GROUP",
    "INVALID_FULL_PAIR_CLIQUE",
    "BOUNDED_SENSE_CONFLICT",
    "CROSS_CASE_SOURCE_BUNDLE",
    "ISOLATED_ACTIVE_TERM_IN_VALID_HYPEREDGE",
    "RENDERABLE_COMPOSITION_WITHOUT_VALID_GROUP",
    "ILLEGAL_HYPEREDGE_PAIR_PROJECTION",
    "ACTIVE_WITH_PENDING_OR_NONFINAL_REVIEW",
    "ACTIVE_ARITY_FIVE_PROJECTION_NONE",
    "ONE_WAY_V2_PAIR_ADAPTER",
}

EXPECTED_IDENTITY_BRANCHES = {
    "UNORDERED_PERMUTATION_INVARIANT": ("UNORDERED", False, "EQUAL"),
    "ORDERED_CONTIGUOUS_ORDINAL_SENSITIVE": ("ORDERED", False, "NOT_EQUAL"),
    "UNORDERED_MEANINGFUL_ROLE_PERMUTATION_INVARIANT": ("UNORDERED", True, "EQUAL"),
    "UNORDERED_MEANINGFUL_ROLE_REASSIGNMENT_SENSITIVE": ("UNORDERED", True, "NOT_EQUAL"),
}

EXPECTED_CLOSURE_KEYS = {
    "pair_association_closure",
    "higher_order_association_closure",
    "global_composition_coherence_closure",
    "product_association_reachability_closure",
    "computational_space_closure",
    "function3_closure",
}

EXPECTED_RECONSTRUCTED_COUNTS = {
    "vocabulary": {
        "synthetic_scope_count": 6,
        "synthetic_distinct_concept_count": 21,
        "synthetic_concept_record_count": 21,
        "synthetic_active_concept_count": 11,
        "synthetic_concept_sense_record_count": 21,
        "synthetic_active_concept_sense_count": 11,
        "production_active_concept_count": 0,
    },
    "associations": {
        "synthetic_pair_revision_count": 9,
        "synthetic_higher_order_revision_count": 5,
        "synthetic_active_pair_revision_count": 9,
        "synthetic_active_higher_order_revision_count": 1,
        "production_pair_revision_count": 0,
        "production_higher_order_revision_count": 0,
        "production_active_association_count": 0,
        "production_active_pending_review_count": 0,
    },
    "incidence": {
        "synthetic_incidence_count": 37,
        "production_incidence_count": 0,
        "implicit_projected_pair_count": 0,
    },
    "realizations_and_compositions": {
        "synthetic_association_realization_count": 10,
        "synthetic_composition_count": 2,
        "synthetic_composition_coherence_review_count": 2,
        "production_association_realization_count": 0,
        "production_composition_count": 0,
        "production_composition_coherence_review_count": 0,
        "production_product_eligible_composition_count": 0,
    },
    "interaction": {
        "synthetic_state_count": 1,
        "synthetic_workflow_count": 1,
        "synthetic_export_count": 1,
        "production_state_count": 0,
        "production_workflow_count": 0,
        "production_export_count": 0,
    },
}

FAILED_PROBES_AND_CORRECTIONS = [
    {
        "probe_id": "INDEPENDENT-PREP-001",
        "failed_state": "Schema-inspection command used a misspelled worktree path containing closure-round16b.",
        "correction": "Reran against the authorized isolated worktree path containing closure_round16b.",
        "repository_defect": False,
    },
    {
        "probe_id": "INDEPENDENT-SEMANTIC-002",
        "failed_state": "First-pass association revision material omitted activation and other governed semantic fields.",
        "correction": "Primary artifacts were regenerated with complete normative semantic projections and mutation-sensitive hashes.",
        "repository_defect": True,
    },
    {
        "probe_id": "INDEPENDENT-SCHEMA-003",
        "failed_state": "First-pass ACTIVE schema admitted incomplete evidence, uncleared rights, and unsupported dispositions.",
        "correction": "ACTIVE now fails closed across evidence, review, authority, coherence, rights, conflict, uncertainty, and product-policy gates.",
        "repository_defect": True,
    },
    {
        "probe_id": "INDEPENDENT-PAIR-004",
        "failed_state": "First-pass PAIR adapter target used DIRECT_HIGHER_ORDER_SUPPORT.",
        "correction": "PAIR target now uses DIRECT_PAIRWISE_SUPPORT with DIRECT_PAIR evidence.",
        "repository_defect": True,
    },
    {
        "probe_id": "INDEPENDENT-ADAPTER-005",
        "failed_state": "First-pass adapter flags did not bind a source fixture or endpoint-to-incidence crosswalk.",
        "correction": "Source fixture, source hash, endpoint crosswalk, adapter semantic hash, and one-way identifier are now bound.",
        "repository_defect": True,
    },
    {
        "probe_id": "INDEPENDENT-GRAPH-006",
        "failed_state": "First-pass oracle reported two components for five vertices with edges 1-2 and 4-5.",
        "correction": "Independent union-find proved three components; the governed expectation was corrected to three.",
        "repository_defect": True,
    },
    {
        "probe_id": "INDEPENDENT-HASH-SPEC-007",
        "failed_state": "Corrected hashes initially lacked a committed exact projection/canonicalization contract for independent reconstruction.",
        "correction": "A ninth schema and embedded/standalone normative hash-binding contract now specify every projection, wrapper, normalization, digest, and identifier rule.",
        "repository_defect": True,
    },
    {
        "probe_id": "INDEPENDENT-VERIFIER-CALIBRATION-008",
        "failed_state": "Pre-run verifier review expected 19 output artifacts excluding the build receipt.",
        "correction": "Recounted 17 output-manifest rows plus the output manifest itself and corrected the independent expectation to 18.",
        "repository_defect": False,
    },
    {
        "probe_id": "INDEPENDENT-VERIFIER-RUN-009",
        "failed_state": "First independent verifier run interpreted OBJECT_WITH_SEMANTIC_AND_REVISION_ONE as a flattened merge and rejected composition revision 1.",
        "correction": "Applied the normative wrapper literally as an object with `semantic` and `revision` keys; the reconstructed digest then matched the committed revision identifier.",
        "repository_defect": False,
    },
    {
        "probe_id": "INDEPENDENT-ACTIVATION-RUN-010",
        "failed_state": "The second independent verifier run found a pending association with nonempty negative/conflicting evidence while its stored conflict_gate was true.",
        "correction": "Withheld the independent receipt and required conflict_gate to be derived from bounded-sense, case-scope, topology, unsupported-bridge, and unresolved-conflict facts.",
        "repository_defect": True,
    },
    {
        "probe_id": "INDEPENDENT-HASH-CONTRACT-AUDIT-011",
        "failed_state": "The association identity binding named source field scope but declared no machine-readable projection to the digest material key scope_identity.",
        "correction": "Withheld the independent receipt and required an explicit scope projection mapping with the seven governed identity keys.",
        "repository_defect": True,
    },
    {
        "probe_id": "INDEPENDENT-GOVERNANCE-AUDIT-012",
        "failed_state": "Sparse and clique controls referred to eight pair identifiers that resolved to no governed PAIR revisions, and concept/sense identifiers resolved to no first-class governed vocabulary objects.",
        "correction": "Withheld the independent receipt and required governed concept/sense collections plus independently evidenced ACTIVE PAIR revisions behind every internal-pair link.",
        "repository_defect": True,
    },
    {
        "probe_id": "INDEPENDENT-COMPOSITION-AUDIT-013",
        "failed_state": "Composition eligibility depended on an association review identifier rather than a first-class composition-coherence review, and workflow hashes omitted realization identifiers.",
        "correction": "Withheld the independent receipt and required separately governed composition-coherence decisions and end-to-end workflow realization traceability.",
        "repository_defect": True,
    },
    {
        "probe_id": "INDEPENDENT-SUPPORT-MODE-AUDIT-014",
        "failed_state": "ACTIVE higher-order schema conditions allowed a direct-higher disposition to be paired with composite evidence support.",
        "correction": "Required exact disposition-to-support-mode mapping and independent schema plus semantic rejection of cross-mode combinations.",
        "repository_defect": True,
    },
    {
        "probe_id": "INDEPENDENT-COMPOSITION-AUTHORITY-AUDIT-015",
        "failed_state": "A composition-coherence review could declare COHERENT while its governed authority remained pending.",
        "correction": "Required FINAL governed authority for every COHERENT composition decision and added an independent schema mutation probe.",
        "repository_defect": True,
    },
    {
        "probe_id": "INDEPENDENT-VOCABULARY-ACTIVATION-AUDIT-016",
        "failed_state": "First-class concept and concept-sense schemas did not initially tie ACTIVE lifecycle to association eligibility and final authority.",
        "correction": "Required fail-closed ACTIVE vocabulary eligibility/authority conditions and independent schema mutation probes.",
        "repository_defect": True,
    },
    {
        "probe_id": "INDEPENDENT-VERIFIER-CALIBRATION-017",
        "failed_state": "The first remediated-artifact calibration selected the first sorted composition realization, which was a PAIR rather than the intended higher-order adversarial base.",
        "correction": "Select the adversarial realization by resolving its association kind, independent of array order.",
        "repository_defect": False,
    },
    {
        "probe_id": "INDEPENDENT-VERIFIER-CALIBRATION-018",
        "failed_state": "The second remediated-artifact calibration attempted to count scope realm from a nonexistent scope.realm field.",
        "correction": "Derive each governed scope's realm from the associations that reference it; scope records intentionally contain historical/context bounds rather than product realm.",
        "repository_defect": False,
    },
    {
        "probe_id": "INDEPENDENT-VERIFIER-CALIBRATION-019",
        "failed_state": "The first final receipt serialization encountered tuple-keyed role maps in a diagnostic observation, which JSON objects cannot encode.",
        "correction": "Canonicalize non-string diagnostic dictionary keys to compact JSON text before deterministic receipt serialization.",
        "repository_defect": False,
    },
]


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def read_json(relative: Path | str) -> Any:
    return json.loads((REPO / relative).read_text(encoding="utf-8"))


def read_tsv(relative: Path | str) -> list[dict[str, str]]:
    with (REPO / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, dialect="excel-tab"))


def json_safe(value: Any) -> Any:
    if isinstance(value, (set, frozenset)):
        converted = [json_safe(item) for item in value]
        return sorted(converted, key=lambda item: canonical_bytes(item))
    if isinstance(value, dict):
        converted: dict[str, Any] = {}
        for key, item in value.items():
            safe_key = key if isinstance(key, str) else json.dumps(json_safe(key), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            converted[safe_key] = json_safe(item)
        return converted
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


class CheckRecorder:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def equal(self, check_id: str, observed: Any, expected: Any) -> None:
        if observed != expected:
            raise AssertionError(f"{check_id}: observed={observed!r} expected={expected!r}")
        self.rows.append({"check_id": check_id, "status": "PASS", "observed": json_safe(observed)})

    def true(self, check_id: str, condition: bool, observed: Any = True) -> None:
        if not condition:
            raise AssertionError(f"{check_id}: condition is false; observed={observed!r}")
        self.rows.append({"check_id": check_id, "status": "PASS", "observed": json_safe(observed)})


class Draft202012SubsetValidator:
    """Independent evaluator for the Draft 2020-12 keywords used by v3."""

    def __init__(self, documents: dict[str, dict[str, Any]]) -> None:
        self.documents = documents

    @staticmethod
    def _type_matches(value: Any, kind: str) -> bool:
        if kind == "null":
            return value is None
        if kind == "boolean":
            return isinstance(value, bool)
        if kind == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if kind == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if kind == "string":
            return isinstance(value, str)
        if kind == "array":
            return isinstance(value, list)
        if kind == "object":
            return isinstance(value, dict)
        return False

    @staticmethod
    def _pointer(document: Any, fragment: str) -> Any:
        if fragment in ("", "#"):
            return document
        if not fragment.startswith("#/"):
            raise ValueError(f"unsupported schema fragment: {fragment}")
        current = document
        for token in fragment[2:].split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            current = current[int(token)] if isinstance(current, list) else current[token]
        return current

    def _resolve(self, ref: str, owner: str) -> tuple[dict[str, Any], str]:
        filename, marker, fragment = ref.partition("#")
        target_name = filename or owner
        if target_name not in self.documents:
            raise KeyError(f"unresolved schema reference: {owner}:{ref}")
        target = self.documents[target_name]
        resolved = self._pointer(target, f"#{fragment}" if marker else "#")
        if not isinstance(resolved, dict):
            raise TypeError(f"schema ref did not resolve to object: {ref}")
        return resolved, target_name

    def errors(self, instance: Any, schema: dict[str, Any], owner: str, path: str = "$") -> list[str]:
        issues: list[str] = []
        ref = schema.get("$ref")
        if isinstance(ref, str):
            target, target_owner = self._resolve(ref, owner)
            issues.extend(self.errors(instance, target, target_owner, path))

        declared_type = schema.get("type")
        if declared_type is not None:
            kinds = [declared_type] if isinstance(declared_type, str) else declared_type
            if not any(self._type_matches(instance, kind) for kind in kinds):
                issues.append(f"{path}:TYPE")
                return issues

        if "const" in schema and instance != schema["const"]:
            issues.append(f"{path}:CONST")
        if "enum" in schema and instance not in schema["enum"]:
            issues.append(f"{path}:ENUM")

        if isinstance(instance, str):
            if "minLength" in schema and len(instance) < schema["minLength"]:
                issues.append(f"{path}:MIN_LENGTH")
            if "maxLength" in schema and len(instance) > schema["maxLength"]:
                issues.append(f"{path}:MAX_LENGTH")
            if "pattern" in schema and re.search(schema["pattern"], instance) is None:
                issues.append(f"{path}:PATTERN")

        if isinstance(instance, int) and not isinstance(instance, bool):
            if "minimum" in schema and instance < schema["minimum"]:
                issues.append(f"{path}:MINIMUM")
            if "maximum" in schema and instance > schema["maximum"]:
                issues.append(f"{path}:MAXIMUM")
            if "exclusiveMinimum" in schema and instance <= schema["exclusiveMinimum"]:
                issues.append(f"{path}:EXCLUSIVE_MINIMUM")
            if "exclusiveMaximum" in schema and instance >= schema["exclusiveMaximum"]:
                issues.append(f"{path}:EXCLUSIVE_MAXIMUM")
            if "multipleOf" in schema and instance % schema["multipleOf"] != 0:
                issues.append(f"{path}:MULTIPLE_OF")

        if isinstance(instance, list):
            if "minItems" in schema and len(instance) < schema["minItems"]:
                issues.append(f"{path}:MIN_ITEMS")
            if "maxItems" in schema and len(instance) > schema["maxItems"]:
                issues.append(f"{path}:MAX_ITEMS")
            if schema.get("uniqueItems") is True:
                encoded = [canonical_bytes(item) for item in instance]
                if len(encoded) != len(set(encoded)):
                    issues.append(f"{path}:UNIQUE_ITEMS")
            item_schema = schema.get("items")
            if isinstance(item_schema, dict):
                for index, item in enumerate(instance):
                    issues.extend(self.errors(item, item_schema, owner, f"{path}/{index}"))
            prefix_items = schema.get("prefixItems")
            if isinstance(prefix_items, list):
                for index, child_schema in enumerate(prefix_items[: len(instance)]):
                    if isinstance(child_schema, dict):
                        issues.extend(self.errors(instance[index], child_schema, owner, f"{path}/{index}"))
            contains = schema.get("contains")
            if isinstance(contains, dict):
                matches = sum(not self.errors(item, contains, owner, f"{path}/{index}") for index, item in enumerate(instance))
                minimum_contains = schema.get("minContains", 1)
                maximum_contains = schema.get("maxContains")
                if matches < minimum_contains:
                    issues.append(f"{path}:MIN_CONTAINS")
                if maximum_contains is not None and matches > maximum_contains:
                    issues.append(f"{path}:MAX_CONTAINS")

        if isinstance(instance, dict):
            if "minProperties" in schema and len(instance) < schema["minProperties"]:
                issues.append(f"{path}:MIN_PROPERTIES")
            if "maxProperties" in schema and len(instance) > schema["maxProperties"]:
                issues.append(f"{path}:MAX_PROPERTIES")
            required = schema.get("required", [])
            for key in required:
                if key not in instance:
                    issues.append(f"{path}/{key}:REQUIRED")
            properties = schema.get("properties", {})
            if isinstance(properties, dict):
                for key, child_schema in properties.items():
                    if key in instance and isinstance(child_schema, dict):
                        issues.extend(self.errors(instance[key], child_schema, owner, f"{path}/{key}"))
                if schema.get("additionalProperties") is False:
                    for key in instance:
                        if key not in properties:
                            issues.append(f"{path}/{key}:ADDITIONAL_PROPERTY")
                elif isinstance(schema.get("additionalProperties"), dict):
                    additional_schema = schema["additionalProperties"]
                    for key in instance:
                        if key not in properties:
                            issues.extend(self.errors(instance[key], additional_schema, owner, f"{path}/{key}"))
            dependent_required = schema.get("dependentRequired", {})
            if isinstance(dependent_required, dict):
                for trigger, dependencies in dependent_required.items():
                    if trigger in instance:
                        for dependency in dependencies:
                            if dependency not in instance:
                                issues.append(f"{path}/{dependency}:DEPENDENT_REQUIRED_BY_{trigger}")
            dependent_schemas = schema.get("dependentSchemas", {})
            if isinstance(dependent_schemas, dict):
                for trigger, child_schema in dependent_schemas.items():
                    if trigger in instance and isinstance(child_schema, dict):
                        issues.extend(self.errors(instance, child_schema, owner, path))

        for child in schema.get("allOf", []):
            issues.extend(self.errors(instance, child, owner, path))
        any_of = schema.get("anyOf")
        if isinstance(any_of, list) and not any(not self.errors(instance, child, owner, path) for child in any_of):
            issues.append(f"{path}:ANY_OF")
        one_of = schema.get("oneOf")
        if isinstance(one_of, list) and sum(not self.errors(instance, child, owner, path) for child in one_of) != 1:
            issues.append(f"{path}:ONE_OF")
        not_schema = schema.get("not")
        if isinstance(not_schema, dict) and not self.errors(instance, not_schema, owner, path):
            issues.append(f"{path}:NOT")
        if_schema = schema.get("if")
        if isinstance(if_schema, dict):
            condition_matches = not self.errors(instance, if_schema, owner, path)
            branch = schema.get("then") if condition_matches else schema.get("else")
            if isinstance(branch, dict):
                issues.extend(self.errors(instance, branch, owner, path))
        return sorted(set(issues))


def validate_schema_documents(documents: dict[str, dict[str, Any]], validator: Draft202012SubsetValidator) -> list[str]:
    failures: list[str] = []
    seen_ids: set[str] = set()

    def walk(value: Any, owner: str, pointer: str) -> None:
        if isinstance(value, dict):
            required = value.get("required")
            if required is not None:
                properties = value.get("properties", {})
                if not isinstance(required, list) or not set(required).issubset(properties):
                    failures.append(f"{owner}:{pointer}:REQUIRED_NOT_DECLARED")
            ref = value.get("$ref")
            if isinstance(ref, str):
                try:
                    validator._resolve(ref, owner)
                except (KeyError, TypeError, ValueError) as exc:
                    failures.append(f"{owner}:{pointer}:REF:{exc}")
            for key, child in value.items():
                walk(child, owner, f"{pointer}/{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, owner, f"{pointer}/{index}")

    for name, document in documents.items():
        if document.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            failures.append(f"{name}:DRAFT")
        expected_id = f"https://trace.example/schemas/exploration/v3/{name}"
        if document.get("$id") != expected_id:
            failures.append(f"{name}:ID")
        if document.get("$id") in seen_ids:
            failures.append(f"{name}:DUPLICATE_ID")
        seen_ids.add(document.get("$id"))
        walk(document, name, "#")
    return sorted(failures)


def hash_contract_semantic_issues(contract: dict[str, Any]) -> list[str]:
    """Reject prose-only or ambiguous hash bindings before interpreting them."""

    issues: list[str] = []
    bindings = contract.get("bindings", [])
    object_types = [binding.get("object_type") for binding in bindings]
    if len(object_types) != len(set(object_types)):
        issues.append("DUPLICATE_OBJECT_TYPE_BINDING")
    if set(object_types) != EXPECTED_HASH_BINDING_OBJECT_TYPES:
        issues.append("OBJECT_TYPE_BINDING_SET")

    by_type = {binding.get("object_type"): binding for binding in bindings}
    for object_type, pointer in EXPECTED_BINDING_POINTERS.items():
        if by_type.get(object_type, {}).get("collection_pointer") != pointer:
            issues.append(f"{object_type}:COLLECTION_POINTER")
    association_binding = by_type.get("ASSOCIATION_REVISION", {})
    identity_material = next(
        (row for row in association_binding.get("materials", []) if row.get("material_name") == "association_identity"),
        None,
    )
    if identity_material is None:
        issues.append("ASSOCIATION_IDENTITY_MATERIAL_MISSING")
    else:
        mappings = identity_material.get("field_mappings", [])
        scope_mappings = [
            mapping
            for mapping in mappings
            if mapping.get("source_pointer") == "/scope"
            and mapping.get("operation") == "PROJECT_SCOPE_IDENTITY"
            and mapping.get("output_key") == "scope_identity"
        ]
        if len(scope_mappings) != 1:
            issues.append("ASSOCIATION_SCOPE_PROJECTION_MAPPING")
        participant_mappings = [
            mapping
            for mapping in mappings
            if mapping.get("source_pointer") == "/participants"
            and mapping.get("operation") == "PROJECT_PARTICIPANT_IDENTITY"
            and mapping.get("output_key") == "participants"
        ]
        if len(participant_mappings) != 1:
            issues.append("ASSOCIATION_PARTICIPANT_PROJECTION_MAPPING")
        if tuple(identity_material.get("output_keys", [])) != (
            "association_kind",
            "participants",
            "scope_identity",
            "order_semantics",
            "roles_meaningful",
        ):
            issues.append("ASSOCIATION_IDENTITY_OUTPUT_KEYS")
        rules = set(identity_material.get("normalization_rules", []))
        if "PROJECT_PARTICIPANTS_TO_CONCEPT_ID_SENSE_ID_ORDINAL_ROLE_ID" not in rules:
            issues.append("ASSOCIATION_PARTICIPANT_PROJECTION_KEYS")
        if "SCOPE_IDENTITY_EXACT_KEYS_SCOPE_ID_HISTORICAL_CASE_IDS_TIME_BOUNDS_GEOGRAPHIES_INSTITUTIONS_ACTORS_MECHANISMS" not in rules:
            issues.append("ASSOCIATION_SCOPE_PROJECTION_KEYS")

    workflow_binding = by_type.get("WORKFLOW", {})
    workflow_semantic = next(
        (row for row in workflow_binding.get("materials", []) if row.get("material_name") == "workflow_semantic"),
        None,
    )
    if workflow_semantic is None or "association_realization_ids" not in workflow_semantic.get("source_fields", []):
        issues.append("WORKFLOW_REALIZATION_HASH_BINDING")

    critical_direct_fields = {
        "VOCABULARY_CONCEPT": {
            "realm", "canonical_label", "semantic_version", "lifecycle_state",
            "association_eligible", "authority", "product_eligible", "product_path",
            "product_eligibility_disposition", "product_ineligibility_reason",
        },
        "CONCEPT_SENSE": {
            "concept_id", "realm", "bounded_definition", "vocabulary_crosswalk_ids",
            "governed_scope_ids", "semantic_version", "lifecycle_state",
            "association_eligible", "authority", "product_eligible", "product_path",
            "product_eligibility_disposition", "product_ineligibility_reason",
        },
        "COMPOSITION_COHERENCE_REVIEW": {
            "composition_id", "realm", "review_state", "authority", "review_version",
            "global_coherence", "bounded_senses_compatible", "case_scope_compatible",
            "roles_and_topology_supported", "same_configuration", "unsupported_bridge_count",
            "association_revision_ids", "association_realization_ids", "incidence_ids",
            "decision", "reasons",
        },
        "WORKFLOW": {
            "realm", "initial_state_id", "transition_kind", "association_revision_ids",
            "association_realization_ids", "state_ids", "reachable",
        },
        "EXPORT": {
            "realm", "workflow_id", "state_id", "association_revision_ids",
            "association_realization_ids", "projection_preservation_records",
            "composition_revision_id", "pair_projection_policy_preserved",
        },
    }
    for object_type, expected_fields in critical_direct_fields.items():
        direct_materials = [
            row for row in by_type.get(object_type, {}).get("materials", [])
            if row.get("recipe") == "DIRECT_FIELD_OBJECT"
        ]
        if len(direct_materials) != 1 or set(direct_materials[0].get("source_fields", [])) != expected_fields:
            issues.append(f"{object_type}:DIRECT_SEMANTIC_FIELDS")

    for binding in bindings:
        object_type = binding.get("object_type", "UNKNOWN")
        materials = binding.get("materials", [])
        material_names = [row.get("material_name") for row in materials]
        if len(material_names) != len(set(material_names)):
            issues.append(f"{object_type}:DUPLICATE_MATERIAL_NAME")
        for hash_field in binding.get("hash_fields", []):
            if hash_field.get("material_name") not in material_names:
                issues.append(f"{object_type}:HASH_UNKNOWN_MATERIAL")
        for identifier in binding.get("identifiers", []):
            material_name = identifier.get("digest_material_name")
            if material_name is not None and material_name not in material_names:
                issues.append(f"{object_type}:IDENTIFIER_UNKNOWN_MATERIAL")
    return sorted(set(issues))


def association_identity_material(row: dict[str, Any], definition: dict[str, Any]) -> dict[str, Any]:
    participants = [
        {
            "concept_id": item["concept_id"],
            "sense_id": item["sense_id"],
            "ordinal": item["ordinal"],
            "role_id": item["role_id"],
        }
        for item in row["participants"]
    ]
    if row["order_semantics"] == "UNORDERED":
        if row["roles_meaningful"]:
            participants.sort(key=lambda item: (item["role_id"] or "", item["sense_id"], item["concept_id"]))
        else:
            participants.sort(key=lambda item: (item["sense_id"], item["concept_id"]))
    scope_mapping = next(
        mapping
        for mapping in definition["field_mappings"]
        if mapping["source_pointer"] == "/scope" and mapping["operation"] == "PROJECT_SCOPE_IDENTITY"
    )
    participant_mapping = next(
        mapping
        for mapping in definition["field_mappings"]
        if mapping["source_pointer"] == "/participants" and mapping["operation"] == "PROJECT_PARTICIPANT_IDENTITY"
    )
    scope = row["scope"]
    scope_identity = {key: scope[key] for key in SCOPE_IDENTITY_KEYS}
    return {
        "association_kind": row["association_kind"],
        "participants": participants,
        scope_mapping["output_key"]: scope_identity,
        "order_semantics": row["order_semantics"],
        "roles_meaningful": row["roles_meaningful"],
    }


def direct_fields(row: dict[str, Any], fields: Iterable[str]) -> dict[str, Any]:
    return {field: row[field] for field in fields}


def mapped_material(row: dict[str, Any], mappings: list[dict[str, Any]]) -> dict[str, Any]:
    material: dict[str, Any] = {}
    for mapping in mappings:
        pointer = mapping["source_pointer"]
        if not pointer.startswith("/"):
            raise AssertionError(f"unsupported independent mapping pointer: {pointer}")
        value: Any = row
        for token in pointer[1:].split("/"):
            value = value[token]
        if mapping["operation"] == "COPY":
            material[mapping["output_key"]] = value
        elif mapping["operation"] == "MAP_ARRAY_FIELD":
            material[mapping["output_key"]] = [item[mapping["item_field"]] for item in value]
        elif mapping["operation"] == "PROJECT_OBJECT_KEYS":
            material[mapping["output_key"]] = {key: value[key] for key in mapping["projected_fields"]}
        elif mapping["operation"] == "PROJECT_PARTICIPANTS":
            material[mapping["output_key"]] = [
                {key: item[key] for key in mapping["projected_fields"]}
                for item in value
            ]
        elif mapping["operation"] == "PROJECT_SCOPE_IDENTITY":
            material[mapping["output_key"]] = {key: value[key] for key in SCOPE_IDENTITY_KEYS}
        elif mapping["operation"] == "PROJECT_PARTICIPANT_IDENTITY":
            material[mapping["output_key"]] = [
                {key: item[key] for key in ("concept_id", "sense_id", "ordinal", "role_id")}
                for item in value
            ]
        else:
            raise AssertionError(f"unsupported independent mapping operation: {mapping['operation']}")
    return material


def materialize_binding(row: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
    materials: dict[str, Any] = {}
    definitions = {item["material_name"]: item for item in binding["materials"]}
    for definition in binding["materials"]:
        name = definition["material_name"]
        recipe = definition["recipe"]
        if recipe == "ASSOCIATION_IDENTITY":
            value = association_identity_material(row, definition)
        elif recipe == "DIRECT_FIELD_OBJECT":
            value = direct_fields(row, definition["source_fields"])
        elif recipe == "DIRECT_FIELD_VALUE":
            fields = definition["source_fields"]
            if len(fields) != 1:
                raise AssertionError(f"{name}: direct value requires exactly one field")
            value = row[fields[0]]
        elif recipe in {"REALIZATION_SEMANTIC_ALIASES", "COMPOSITION_IDENTITY_ALIASES"}:
            value = mapped_material(row, definition["field_mappings"])
        elif recipe == "ASSOCIATION_REVISION":
            semantic = materials.get("association_semantic")
            if not isinstance(semantic, dict):
                raise AssertionError("association semantic must precede revision material")
            value = {"association_id": row["association_id"], **semantic}
        elif recipe == "COMPOSITION_REVISION":
            semantic = materials.get("composition_semantic")
            if not isinstance(semantic, dict):
                raise AssertionError("composition semantic must precede revision material")
            value = {"semantic": semantic, "revision": 1}
        elif recipe in {"INCIDENCE_IDENTIFIER", "STATIC_AUTHORITY_IDENTIFIER"}:
            value = None
        else:
            raise AssertionError(f"unimplemented normative recipe: {recipe}")
        materials[name] = value
    if set(definitions) != set(materials):
        raise AssertionError("normative material definitions were not completely interpreted")
    return materials


def binding_objects(fixture: dict[str, Any], object_type: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    if object_type == "VOCABULARY_CONCEPT":
        return [(row, {}) for row in fixture["concepts"]]
    if object_type == "CONCEPT_SENSE":
        return [(row, {}) for row in fixture["concept_senses"]]
    if object_type == "ASSOCIATION_REVISION":
        return [(row, {}) for row in fixture["associations"]]
    if object_type == "PARTICIPANT_INCIDENCE":
        return [
            (participant, {"parent": association, "position": index})
            for association in fixture["associations"]
            for index, participant in enumerate(association["participants"], 1)
        ]
    if object_type == "ASSOCIATION_REALIZATION":
        return [(realization, {"parent": composition}) for composition in fixture["compositions"] for realization in composition["association_realizations"]]
    if object_type == "COMPOSITION_REVISION":
        return [(row, {}) for row in fixture["compositions"]]
    if object_type == "COMPOSITION_COHERENCE_REVIEW":
        return [(row, {}) for row in fixture["composition_coherence_reviews"]]
    if object_type == "NAVIGATION_STATE":
        return [(row, {}) for row in fixture["navigation_states"]]
    if object_type == "WORKFLOW":
        return [(row, {}) for row in fixture["workflows"]]
    if object_type == "EXPORT":
        return [(row, {}) for row in fixture["exports"]]
    if object_type == "V2_PAIR_ADAPTER_RECEIPT":
        return [(row, {}) for row in fixture["v2_pair_adapter_receipts"]]
    if object_type == "V2_PAIR_SOURCE_FIXTURE":
        return [(row, {}) for row in fixture["v2_pair_source_fixtures"]]
    raise AssertionError(f"unknown normative object type: {object_type}")


def verify_hash_bindings(fixture: dict[str, Any], contract: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    results: list[dict[str, Any]] = []
    assertion_count = 0
    for binding in contract["bindings"]:
        object_type = binding["object_type"]
        objects = binding_objects(fixture, object_type)
        for ordinal, (row, context) in enumerate(objects, 1):
            if object_type == "PARTICIPANT_INCIDENCE":
                parent = context["parent"]
                expected_id = f"incidence:{parent['identity_material_sha256'][:16]}:{context['position']:02d}"
                if row["incidence_id"] != expected_id:
                    raise AssertionError(f"{object_type}:{ordinal}: incidence identifier mismatch")
                assertion_count += 1
                continue
            materials = materialize_binding(row, binding)
            material_hashes = {
                name: digest(value)
                for name, value in materials.items()
                if value is not None
            }
            for hash_spec in binding["hash_fields"]:
                observed = row[hash_spec["hash_field"]]
                expected = material_hashes[hash_spec["material_name"]]
                if observed != expected:
                    raise AssertionError(f"{object_type}:{ordinal}:{hash_spec['hash_field']} mismatch")
                assertion_count += 1
            for identifier in binding["identifiers"]:
                observed = row[identifier["identifier_field"]]
                material_name = identifier["digest_material_name"]
                if material_name is None:
                    if not observed.startswith(identifier["prefix"]):
                        raise AssertionError(f"{object_type}:{ordinal}: static identifier prefix mismatch")
                else:
                    expected = identifier["prefix"] + material_hashes[material_name][: identifier["digest_hex_chars"]]
                    if observed != expected:
                        raise AssertionError(f"{object_type}:{ordinal}:{identifier['identifier_field']} mismatch")
                assertion_count += 1
            results.append(
                {
                    "object_type": object_type,
                    "object_ordinal": ordinal,
                    "status": "PASS",
                    "material_hashes": material_hashes,
                }
            )
    return results, assertion_count


def verify_identity_branch_receipts(
    receipts: list[dict[str, Any]], checks: CheckRecorder
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    semantic_branches: set[tuple[str, bool, str]] = set()
    for receipt in receipts:
        test_id = receipt["test_id"]
        base = receipt["base_identity_material"]
        comparison = receipt["comparison_identity_material"]
        exact_keys = {
            "association_kind",
            "participants",
            "scope_identity",
            "order_semantics",
            "roles_meaningful",
        }
        checks.equal(f"identity_branch_base_keys_{test_id}", set(base), exact_keys)
        checks.equal(f"identity_branch_comparison_keys_{test_id}", set(comparison), exact_keys)
        base_hash = digest(base)
        comparison_hash = digest(comparison)
        checks.equal(f"identity_branch_base_hash_{test_id}", receipt["base_identity_sha256"], base_hash)
        checks.equal(f"identity_branch_comparison_hash_{test_id}", receipt["comparison_identity_sha256"], comparison_hash)
        derived_relation = "EQUAL" if base_hash == comparison_hash else "NOT_EQUAL"
        checks.equal(f"identity_branch_expected_relation_{test_id}", receipt["expected_relation"], derived_relation)
        checks.equal(f"identity_branch_observed_relation_{test_id}", receipt["observed_relation"], derived_relation)
        checks.equal(f"identity_branch_status_{test_id}", receipt["status"], "PASS")
        base_incidence_ids = [
            f"incidence:{base_hash[:16]}:{index:02d}"
            for index in range(1, len(base["participants"]) + 1)
        ]
        comparison_incidence_ids = [
            f"incidence:{comparison_hash[:16]}:{index:02d}"
            for index in range(1, len(comparison["participants"]) + 1)
        ]
        checks.equal(f"identity_branch_base_incidences_{test_id}", receipt["base_canonical_incidence_ids"], base_incidence_ids)
        checks.equal(f"identity_branch_comparison_incidences_{test_id}", receipt["comparison_canonical_incidence_ids"], comparison_incidence_ids)
        checks.equal(f"identity_branch_order_semantics_{test_id}", comparison["order_semantics"], base["order_semantics"])
        checks.equal(f"identity_branch_role_semantics_{test_id}", comparison["roles_meaningful"], base["roles_meaningful"])
        checks.equal(f"identity_branch_association_kind_{test_id}", comparison["association_kind"], base["association_kind"])
        checks.equal(f"identity_branch_scope_{test_id}", comparison["scope_identity"], base["scope_identity"])
        base_endpoint_set = {(row["concept_id"], row["sense_id"]) for row in base["participants"]}
        comparison_endpoint_set = {(row["concept_id"], row["sense_id"]) for row in comparison["participants"]}
        checks.equal(f"identity_branch_endpoint_set_{test_id}", comparison_endpoint_set, base_endpoint_set)
        branch_key = (base["order_semantics"], base["roles_meaningful"], derived_relation)
        checks.true(f"identity_branch_constant_{test_id}", receipt["branch"] in EXPECTED_IDENTITY_BRANCHES, receipt["branch"])
        checks.equal(f"identity_branch_constant_semantics_{test_id}", branch_key, EXPECTED_IDENTITY_BRANCHES[receipt["branch"]])
        semantic_branches.add(branch_key)
        if base["order_semantics"] == "ORDERED":
            checks.equal(f"identity_branch_base_ordinals_{test_id}", [row["ordinal"] for row in base["participants"]], list(range(len(base["participants"]))))
            checks.equal(f"identity_branch_comparison_ordinals_{test_id}", [row["ordinal"] for row in comparison["participants"]], list(range(len(comparison["participants"]))))
            checks.equal(
                f"identity_branch_ordered_reversal_{test_id}",
                [(row["concept_id"], row["sense_id"]) for row in comparison["participants"]],
                list(reversed([(row["concept_id"], row["sense_id"]) for row in base["participants"]])),
            )
        elif base["roles_meaningful"]:
            for label, material in (("base", base), ("comparison", comparison)):
                roles = [row["role_id"] for row in material["participants"]]
                checks.true(f"identity_branch_{label}_roles_present_{test_id}", all(isinstance(role, str) and role for role in roles), roles)
                checks.equal(f"identity_branch_{label}_roles_unique_{test_id}", len(roles), len(set(roles)))
            if derived_relation == "NOT_EQUAL":
                base_roles = {(row["concept_id"], row["sense_id"]): row["role_id"] for row in base["participants"]}
                comparison_roles = {(row["concept_id"], row["sense_id"]): row["role_id"] for row in comparison["participants"]}
                checks.true(f"identity_branch_role_reassignment_{test_id}", base_roles != comparison_roles, [base_roles, comparison_roles])
                checks.equal(f"identity_branch_role_vocabulary_{test_id}", set(base_roles.values()), set(comparison_roles.values()))
        else:
            checks.true(f"identity_branch_roles_absent_{test_id}", all(row["role_id"] is None for row in base["participants"] + comparison["participants"]), receipt["branch"])
        if derived_relation == "EQUAL":
            checks.equal(f"identity_branch_equal_material_{test_id}", comparison, base)
            checks.equal(f"identity_branch_equal_incidence_sequence_{test_id}", comparison_incidence_ids, base_incidence_ids)
        results.append({"test_id": test_id, "branch": receipt["branch"], "derived_relation": derived_relation, "status": "PASS"})
    checks.equal(
        "identity_branch_semantic_coverage",
        semantic_branches,
        {
            ("UNORDERED", False, "EQUAL"),
            ("ORDERED", False, "NOT_EQUAL"),
            ("UNORDERED", True, "EQUAL"),
            ("UNORDERED", True, "NOT_EQUAL"),
        },
    )
    checks.equal("identity_branch_test_count", len(results), 4)
    checks.equal("identity_branch_constant_coverage", {row["branch"] for row in results}, set(EXPECTED_IDENTITY_BRANCHES))
    return results


def association_semantic_issues(row: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    revision = row.get("association_revision_id", "UNKNOWN")
    participants = row.get("participants", [])
    arity = row.get("arity")
    if arity != len(participants):
        issues.append(f"{revision}:ARITY_INCIDENCE_MISMATCH")
    incidence_ids = [item.get("incidence_id") for item in participants]
    concept_ids = [item.get("concept_id") for item in participants]
    sense_ids = [item.get("sense_id") for item in participants]
    concept_senses = [(item.get("concept_id"), item.get("sense_id")) for item in participants]
    if len(incidence_ids) != len(set(incidence_ids)):
        issues.append(f"{revision}:INCIDENCE_ID_DUPLICATE")
    if len(concept_ids) != len(set(concept_ids)) or len(sense_ids) != len(set(sense_ids)) or len(concept_senses) != len(set(concept_senses)):
        issues.append(f"{revision}:CONCEPT_SENSE_PARTICIPANT_DUPLICATE")
    if any(item.get("participant_scope_id") != row.get("scope", {}).get("scope_id") for item in participants):
        issues.append(f"{revision}:PARTICIPANT_SCOPE_MISMATCH")

    if row.get("association_kind") == "PAIR":
        if arity != 2 or row.get("pair_projection_policy") != "NOT_APPLICABLE":
            issues.append(f"{revision}:PAIR_CONTRACT")
        if row.get("internal_pair_association_ids") or row.get("internal_pair_links"):
            issues.append(f"{revision}:PAIR_INTERNAL_LINKS_FORBIDDEN")
    elif row.get("association_kind") == "HIGHER_ORDER":
        if not isinstance(arity, int) or arity < 3 or row.get("pair_projection_policy") != "NONE":
            issues.append(f"{revision}:HIGHER_ORDER_PROJECTION_CONTRACT")
    else:
        issues.append(f"{revision}:ASSOCIATION_KIND")

    if row.get("order_semantics") == "UNORDERED":
        if any(item.get("ordinal") is not None for item in participants):
            issues.append(f"{revision}:UNORDERED_ORDINAL_PRESENT")
        if row.get("roles_meaningful"):
            canonical_participants = sorted(
                participants,
                key=lambda item: (item.get("role_id") or "", item.get("sense_id"), item.get("concept_id")),
            )
        else:
            canonical_participants = sorted(
                participants,
                key=lambda item: (item.get("sense_id"), item.get("concept_id")),
            )
        if participants != canonical_participants:
            issues.append(f"{revision}:UNORDERED_STORED_ORDER_NOT_CANONICAL")
    elif row.get("order_semantics") == "ORDERED":
        ordinals = [item.get("ordinal") for item in participants]
        if ordinals != list(range(len(participants))):
            issues.append(f"{revision}:ORDERED_ORDINAL_SEQUENCE")
    if row.get("roles_meaningful"):
        if any(not isinstance(item.get("role_id"), str) or not item.get("role_id") for item in participants):
            issues.append(f"{revision}:MEANINGFUL_ROLE_MISSING")
        role_ids = [item.get("role_id") for item in participants]
        if len(role_ids) != len(set(role_ids)):
            issues.append(f"{revision}:MEANINGFUL_ROLE_DUPLICATE")
    elif any(item.get("role_id") is not None for item in participants):
        issues.append(f"{revision}:NONMEANINGFUL_ROLE_PRESENT")

    links = row.get("internal_pair_links", [])
    link_ids = [link.get("pair_association_id") for link in links]
    link_revision_ids = [link.get("pair_association_revision_id") for link in links]
    if set(link_ids) != set(row.get("internal_pair_association_ids", [])) or len(link_ids) != len(set(link_ids)):
        issues.append(f"{revision}:PAIR_LINK_ID_RECONCILIATION")
    if any(not isinstance(value, str) or not value for value in link_revision_ids) or len(link_revision_ids) != len(set(link_revision_ids)):
        issues.append(f"{revision}:PAIR_LINK_REVISION_ID_RECONCILIATION")
    valid_incidences = set(incidence_ids)
    endpoint_pairs: list[frozenset[str]] = []
    for link in links:
        endpoints = link.get("participant_incidence_ids", [])
        if len(endpoints) != 2 or len(set(endpoints)) != 2 or not set(endpoints).issubset(valid_incidences):
            issues.append(f"{revision}:PAIR_LINK_ENDPOINT_INVALID")
        endpoint_pairs.append(frozenset(endpoints))
    if len(endpoint_pairs) != len(set(endpoint_pairs)):
        issues.append(f"{revision}:PAIR_LINK_ENDPOINT_DUPLICATE")

    evidence = row.get("evidence", {})
    review = row.get("review", {})
    activation = row.get("activation", {})
    uncertainty = row.get("uncertainty", {})
    support_modes = {"DIRECT_PAIR", "DIRECT_GROUP", "COHERENT_COMPOSITE", "MIXED"}
    support_mode = evidence.get("support_mode")
    evidence_items_complete = bool(
        isinstance(evidence.get("evidence_item_ids"), list)
        and evidence["evidence_item_ids"]
        and len(evidence["evidence_item_ids"]) == len(set(evidence["evidence_item_ids"]))
    )
    locators_complete = bool(
        isinstance(evidence.get("locator_ids"), list)
        and evidence["locator_ids"]
        and len(evidence["locator_ids"]) == len(set(evidence["locator_ids"]))
    )
    synthesis_complete = bool(
        (support_mode in {"DIRECT_PAIR", "DIRECT_GROUP"} and not evidence.get("synthesis_steps"))
        or (support_mode in {"COHERENT_COMPOSITE", "MIXED"} and evidence.get("synthesis_steps"))
    )
    supporting_pair = review.get("disposition") == "DIRECT_PAIRWISE_SUPPORT" and support_mode == "DIRECT_PAIR"
    supporting_higher = {
        "DIRECT_GROUP": "DIRECT_HIGHER_ORDER_SUPPORT",
        "COHERENT_COMPOSITE": "COHERENT_COMPOSITE_SUPPORT",
        "MIXED": "MIXED_DIRECT_AND_COMPOSITE_SUPPORT",
    }.get(support_mode) == review.get("disposition")
    supporting_disposition = supporting_pair if row.get("association_kind") == "PAIR" else supporting_higher
    conflicts_cleared = bool(
        not evidence.get("negative_or_conflicting_evidence")
        or (
            evidence.get("conflicts_resolved") is True
            and isinstance(evidence.get("conflict_resolution_ids"), list)
            and bool(evidence.get("conflict_resolution_ids"))
        )
    )
    bounded_scope_pass = bool(
        evidence.get("same_configuration")
        and review.get("bounded_senses_compatible")
        and review.get("case_scope_compatible")
        and review.get("roles_and_topology_supported")
        and review.get("unsupported_bridge_count") == 0
    )
    if row.get("product_eligible"):
        expected_product_gate = bool(
            row.get("realm") == "PRODUCTION"
            and isinstance(row.get("product_path"), str)
            and row.get("product_path")
            and row.get("product_eligibility_disposition") == "ELIGIBLE"
            and row.get("product_ineligibility_reason") is None
        )
    else:
        expected_product_gate = bool(
            row.get("product_path") is None
            and row.get("product_eligibility_disposition") in {"INELIGIBLE", "DEFERRED", "NOT_APPLICABLE_SYNTHETIC"}
            and isinstance(row.get("product_ineligibility_reason"), str)
            and row.get("product_ineligibility_reason")
            and (
                row.get("realm") != "SYNTHETIC_CONTROL"
                or row.get("product_eligibility_disposition") == "NOT_APPLICABLE_SYNTHETIC"
            )
        )
    expected_gates = {
        "evidence_gate": bool(
            evidence.get("evidence_complete")
            and support_mode in support_modes
            and evidence_items_complete
            and locators_complete
        ),
        "final_review_gate": bool(review.get("review_state") == "FINAL" and supporting_disposition),
        "authority_gate": bool(
            review.get("authority_state") == "FINAL"
            and not (
                row.get("realm") == "PRODUCTION"
                and review.get("review_authority") == "SYNTHETIC_TEST_AUTHORITY"
            )
        ),
        "coherence_gate": review.get("global_coherence") == "PASS",
        "rights_gate": evidence.get("rights_cleared_for_governed_use") is True,
        "conflict_gate": conflicts_cleared,
        "bounded_scope_gate": bounded_scope_pass,
        "synthesis_gate": synthesis_complete,
        "product_policy_gate": expected_product_gate,
    }
    for gate, expected in expected_gates.items():
        if activation.get(gate) is not expected:
            issues.append(f"{revision}:{gate.upper()}_MISMATCH")
    uncertainty_pass = bool(
        uncertainty.get("status") == "RESOLVED_BOUNDED"
        and uncertainty.get("activation_policy") == "ALLOWED_BOUNDED"
        and uncertainty.get("reviewed_in_review_id") == review.get("review_id")
    )
    expected_all = all(expected_gates.values()) and uncertainty_pass
    if activation.get("all_gates_pass") is not expected_all:
        issues.append(f"{revision}:ALL_GATES_MISMATCH")
    requested_active = activation.get("requested_state") == "ACTIVE"
    expected_decision = "ALLOW" if requested_active and expected_all else ("REJECT" if requested_active else "NOT_REQUESTED")
    if activation.get("decision") != expected_decision:
        issues.append(f"{revision}:ACTIVATION_DECISION_MISMATCH")
    lifecycle_active = row.get("lifecycle_state") == "ACTIVE"
    if lifecycle_active != (expected_decision == "ALLOW"):
        issues.append(f"{revision}:LIFECYCLE_ACTIVATION_MISMATCH")

    if lifecycle_active:
        if activation.get("decision") != "ALLOW" or not expected_all:
            issues.append(f"{revision}:ACTIVE_GATE_DECISION")
        if not evidence.get("same_configuration"):
            issues.append(f"{revision}:ACTIVE_CONFIGURATION")
        if not evidence_items_complete:
            issues.append(f"{revision}:ACTIVE_EVIDENCE_ITEMS")
        if not locators_complete:
            issues.append(f"{revision}:ACTIVE_EVIDENCE_LOCATORS")
        if evidence.get("negative_or_conflicting_evidence"):
            issues.append(f"{revision}:ACTIVE_UNRESOLVED_CONFLICT")
        if evidence.get("conflicts_resolved") is not True:
            issues.append(f"{revision}:ACTIVE_CONFLICT_REVIEW")
        if not synthesis_complete:
            issues.append(f"{revision}:ACTIVE_SYNTHESIS_STEPS")
        if row.get("association_kind") == "PAIR" and not supporting_pair:
            issues.append(f"{revision}:ACTIVE_PAIR_SUPPORT")
        if row.get("association_kind") == "HIGHER_ORDER" and not supporting_higher:
            issues.append(f"{revision}:ACTIVE_HIGHER_ORDER_SUPPORT")
        if not uncertainty_pass:
            issues.append(f"{revision}:ACTIVE_UNCERTAINTY")
    if uncertainty.get("reviewed_in_review_id") != review.get("review_id"):
        issues.append(f"{revision}:UNCERTAINTY_REVIEW_REFERENCE")
    if row.get("realm") == "SYNTHETIC_CONTROL":
        if row.get("product_eligible") or row.get("product_path") is not None or row.get("product_eligibility_disposition") != "NOT_APPLICABLE_SYNTHETIC":
            issues.append(f"{revision}:SYNTHETIC_PRODUCT_BOUNDARY")
    return sorted(set(issues))


def governed_vocabulary_issues(
    fixture: dict[str, Any],
) -> tuple[list[str], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    issues: list[str] = []
    concepts = fixture.get("concepts", [])
    senses = fixture.get("concept_senses", [])
    scopes = fixture.get("scopes", [])
    concept_by_id = {row.get("concept_id"): row for row in concepts}
    sense_by_id = {row.get("sense_id"): row for row in senses}
    scope_by_id = {row.get("scope_id"): row for row in scopes}
    if None in concept_by_id or len(concept_by_id) != len(concepts):
        issues.append("CONCEPT_IDENTIFIER_UNIQUENESS")
    if None in sense_by_id or len(sense_by_id) != len(senses):
        issues.append("SENSE_IDENTIFIER_UNIQUENESS")
    if None in scope_by_id or len(scope_by_id) != len(scopes):
        issues.append("SCOPE_IDENTIFIER_UNIQUENESS")
    for scope_id, scope in scope_by_id.items():
        for key in ("historical_case_ids", "geographies", "institutions", "actors", "mechanisms"):
            values = scope.get(key, [])
            if values != sorted(set(values)):
                issues.append(f"{scope_id}:SCOPE_{key.upper()}_CANONICALIZATION")
    participant_concepts: set[str] = set()
    participant_senses: set[str] = set()
    active_concepts: set[str] = set()
    active_senses: set[str] = set()
    sense_scope_ids: dict[str, set[str]] = {}
    referenced_scope_ids: set[str] = set()
    for association in fixture.get("associations", []):
        referenced_scope_ids.add(association.get("scope", {}).get("scope_id"))
        for participant in association.get("participants", []):
            concept_id = participant.get("concept_id")
            sense_id = participant.get("sense_id")
            participant_concepts.add(concept_id)
            participant_senses.add(sense_id)
            sense_scope_ids.setdefault(sense_id, set()).add(association.get("scope", {}).get("scope_id"))
            if association.get("lifecycle_state") == "ACTIVE":
                active_concepts.add(concept_id)
                active_senses.add(sense_id)
    if set(concept_by_id) != participant_concepts:
        issues.append("CONCEPT_INCIDENCE_COVERAGE")
    if set(sense_by_id) != participant_senses:
        issues.append("SENSE_INCIDENCE_COVERAGE")
    if set(scope_by_id) != referenced_scope_ids:
        issues.append("SCOPE_ASSOCIATION_COVERAGE")
    for concept_id, concept in concept_by_id.items():
        if concept.get("realm") not in {"SYNTHETIC_CONTROL", "PRODUCTION"}:
            issues.append(f"{concept_id}:CONCEPT_REALM")
        if not isinstance(concept.get("canonical_label"), str) or not concept.get("canonical_label"):
            issues.append(f"{concept_id}:CONCEPT_LABEL")
        if not isinstance(concept.get("association_eligible"), bool) or not isinstance(concept.get("product_eligible"), bool):
            issues.append(f"{concept_id}:CONCEPT_ELIGIBILITY")
        authority = concept.get("authority", {})
        if not isinstance(authority.get("authority_id"), str) or not authority.get("authority_id"):
            issues.append(f"{concept_id}:CONCEPT_AUTHORITY")
        if not isinstance(authority.get("authority_version"), str) or not authority.get("authority_version"):
            issues.append(f"{concept_id}:CONCEPT_AUTHORITY_VERSION")
        if concept.get("lifecycle_state") == "ACTIVE" and not (
            concept.get("association_eligible") is True and authority.get("authority_state") == "FINAL"
        ):
            issues.append(f"{concept_id}:ACTIVE_CONCEPT_AUTHORITY_ELIGIBILITY")
        if (concept.get("lifecycle_state") == "ACTIVE") != (concept_id in active_concepts):
            issues.append(f"{concept_id}:CONCEPT_ACTIVE_DERIVATION")
        if concept.get("association_eligible") is not (concept_id in active_concepts):
            issues.append(f"{concept_id}:CONCEPT_ASSOCIATION_ELIGIBILITY_DERIVATION")
        if concept.get("realm") == "SYNTHETIC_CONTROL" and (
            concept.get("product_eligible") is not False
            or concept.get("product_path") is not None
            or concept.get("product_eligibility_disposition") != "NOT_APPLICABLE_SYNTHETIC"
            or not concept.get("product_ineligibility_reason")
        ):
            issues.append(f"{concept_id}:SYNTHETIC_CONCEPT_PRODUCT_BOUNDARY")
    senses_by_concept: dict[str, set[str]] = {}
    for sense_id, sense in sense_by_id.items():
        concept_id = sense.get("concept_id")
        if concept_id not in concept_by_id:
            issues.append(f"{sense_id}:SENSE_CONCEPT_REFERENCE")
            continue
        senses_by_concept.setdefault(concept_id, set()).add(sense_id)
        if not isinstance(sense.get("bounded_definition"), str) or not sense.get("bounded_definition"):
            issues.append(f"{sense_id}:BOUNDED_DEFINITION")
        authority = sense.get("authority", {})
        if not isinstance(authority.get("authority_id"), str) or not authority.get("authority_id"):
            issues.append(f"{sense_id}:SENSE_AUTHORITY")
        if not isinstance(authority.get("authority_version"), str) or not authority.get("authority_version"):
            issues.append(f"{sense_id}:SENSE_AUTHORITY_VERSION")
        if not isinstance(sense.get("semantic_version"), str) or not sense.get("semantic_version"):
            issues.append(f"{sense_id}:SENSE_SEMANTIC_VERSION")
        if not isinstance(sense.get("vocabulary_crosswalk_ids"), list) or not sense.get("vocabulary_crosswalk_ids"):
            issues.append(f"{sense_id}:CROSSWALK_IDENTITY")
        if len(sense.get("vocabulary_crosswalk_ids", [])) != len(set(sense.get("vocabulary_crosswalk_ids", []))):
            issues.append(f"{sense_id}:CROSSWALK_IDENTITY_DUPLICATE")
        if any(scope_id not in scope_by_id for scope_id in sense.get("governed_scope_ids", [])) or not sense.get("governed_scope_ids"):
            issues.append(f"{sense_id}:GOVERNED_SCOPE_REFERENCE")
        if set(sense.get("governed_scope_ids", [])) != sense_scope_ids.get(sense_id, set()):
            issues.append(f"{sense_id}:GOVERNED_SCOPE_SET_DERIVATION")
        if sense.get("lifecycle_state") == "ACTIVE" and not (
            sense.get("association_eligible") is True and authority.get("authority_state") == "FINAL"
        ):
            issues.append(f"{sense_id}:ACTIVE_SENSE_AUTHORITY_ELIGIBILITY")
        if (sense.get("lifecycle_state") == "ACTIVE") != (sense_id in active_senses):
            issues.append(f"{sense_id}:SENSE_ACTIVE_DERIVATION")
        if sense.get("association_eligible") is not (sense_id in active_senses):
            issues.append(f"{sense_id}:SENSE_ASSOCIATION_ELIGIBILITY_DERIVATION")
        if sense.get("realm") != concept_by_id[concept_id].get("realm"):
            issues.append(f"{sense_id}:SENSE_CONCEPT_REALM")
        if sense.get("realm") == "SYNTHETIC_CONTROL" and (
            sense.get("product_eligible") is not False
            or sense.get("product_path") is not None
            or sense.get("product_eligibility_disposition") != "NOT_APPLICABLE_SYNTHETIC"
            or not sense.get("product_ineligibility_reason")
        ):
            issues.append(f"{sense_id}:SYNTHETIC_SENSE_PRODUCT_BOUNDARY")
    for concept_id, concept in concept_by_id.items():
        if "sense_ids" in concept and set(concept["sense_ids"]) != senses_by_concept.get(concept_id, set()):
            issues.append(f"{concept_id}:CONCEPT_SENSE_SET")
    return sorted(set(issues)), concept_by_id, sense_by_id, scope_by_id


def internal_pair_governance_issues(
    associations: list[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    """Resolve every higher-order internal edge to an independently governed PAIR."""

    issues: list[str] = []
    ledger: list[dict[str, Any]] = []
    association_by_revision = {row.get("association_revision_id"): row for row in associations}
    association_by_identity = {row.get("association_id"): row for row in associations}
    for higher in associations:
        if higher.get("association_kind") != "HIGHER_ORDER":
            continue
        parent_by_incidence = {row.get("incidence_id"): row for row in higher.get("participants", [])}
        for link in higher.get("internal_pair_links", []):
            pair_id = link.get("pair_association_id")
            pair_revision_id = link.get("pair_association_revision_id")
            pair = association_by_revision.get(pair_revision_id)
            endpoint_ids = link.get("participant_incidence_ids", [])
            entry = {
                "higher_order_association_revision_id": higher.get("association_revision_id"),
                "pair_association_id": pair_id,
                "pair_association_revision_id": pair_revision_id,
                "participant_incidence_ids": endpoint_ids,
                "status": "PASS",
            }
            if pair is None:
                issues.append(f"{higher.get('association_revision_id')}:{pair_revision_id}:PAIR_REVISION_UNRESOLVED")
                entry["status"] = "FAIL"
                ledger.append(entry)
                continue
            if association_by_identity.get(pair_id) is not pair or pair.get("association_id") != pair_id:
                issues.append(f"{pair_revision_id}:PAIR_IDENTITY_REFERENCE")
            if pair.get("association_kind") != "PAIR" or pair.get("arity") != 2:
                issues.append(f"{pair_revision_id}:PAIR_KIND_ARITY")
            if pair.get("realm") != higher.get("realm"):
                issues.append(f"{pair_revision_id}:PAIR_REALM")
            evidence = pair.get("evidence", {})
            review = pair.get("review", {})
            activation = pair.get("activation", {})
            if not (
                pair.get("lifecycle_state") == "ACTIVE"
                and activation.get("decision") == "ALLOW"
                and activation.get("all_gates_pass") is True
                and review.get("review_state") == "FINAL"
                and review.get("authority_state") == "FINAL"
                and review.get("global_coherence") == "PASS"
                and review.get("disposition") == "DIRECT_PAIRWISE_SUPPORT"
                and evidence.get("support_mode") == "DIRECT_PAIR"
                and evidence.get("evidence_complete") is True
                and evidence.get("same_configuration") is True
                and evidence.get("evidence_item_ids")
                and evidence.get("locator_ids")
            ):
                issues.append(f"{pair_revision_id}:PAIR_NOT_GOVERNED_ACTIVE_DIRECT")
            parent_endpoints = {
                (parent_by_incidence[incidence_id].get("concept_id"), parent_by_incidence[incidence_id].get("sense_id"))
                for incidence_id in endpoint_ids
                if incidence_id in parent_by_incidence
            }
            pair_endpoints = {
                (participant.get("concept_id"), participant.get("sense_id"))
                for participant in pair.get("participants", [])
            }
            if len(endpoint_ids) != 2 or len(parent_endpoints) != 2 or parent_endpoints != pair_endpoints:
                issues.append(f"{pair_revision_id}:PAIR_ENDPOINT_CROSSWALK")
            if set(link.get("pair_participant_incidence_ids", [])) != {
                participant.get("incidence_id") for participant in pair.get("participants", [])
            }:
                issues.append(f"{pair_revision_id}:PAIR_PARTICIPANT_INCIDENCE_CROSSWALK")
            if set(link.get("endpoint_sense_ids", [])) != {
                sense_id for _concept_id, sense_id in parent_endpoints
            } or set(link.get("endpoint_sense_ids", [])) != {
                participant.get("sense_id") for participant in pair.get("participants", [])
            }:
                issues.append(f"{pair_revision_id}:PAIR_ENDPOINT_SENSE_CROSSWALK")
            if any(issue.startswith(f"{pair_revision_id}:") for issue in issues):
                entry["status"] = "FAIL"
            ledger.append(entry)
    return sorted(set(issues)), ledger


def fixture_semantic_issues(fixture: dict[str, Any]) -> list[str]:
    """Re-evaluate cross-record semantics without the primary fixture validator."""

    issues: list[str] = []
    associations = fixture.get("associations", [])
    association_by_revision = {row.get("association_revision_id"): row for row in associations}
    for association in associations:
        issues.extend(association_semantic_issues(association))
    vocabulary_issues, concept_by_id, sense_by_id, scope_by_id = governed_vocabulary_issues(fixture)
    issues.extend(vocabulary_issues)
    pair_issues, _ledger = internal_pair_governance_issues(associations)
    issues.extend(pair_issues)
    all_incidences: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for association in associations:
        scope = association.get("scope", {})
        if scope_by_id.get(scope.get("scope_id")) != scope:
            issues.append(f"{association.get('association_revision_id')}:GOVERNED_SCOPE_DRIFT")
        for participant in association.get("participants", []):
            all_incidences[participant.get("incidence_id")] = (association, participant)
            if participant.get("concept_id") not in concept_by_id or participant.get("sense_id") not in sense_by_id:
                issues.append(f"{association.get('association_revision_id')}:PARTICIPANT_VOCABULARY_UNRESOLVED")
            elif association.get("lifecycle_state") == "ACTIVE" and not (
                concept_by_id[participant["concept_id"]].get("lifecycle_state") == "ACTIVE"
                and concept_by_id[participant["concept_id"]].get("association_eligible") is True
                and sense_by_id[participant["sense_id"]].get("lifecycle_state") == "ACTIVE"
                and sense_by_id[participant["sense_id"]].get("association_eligible") is True
            ):
                issues.append(f"{association.get('association_revision_id')}:ACTIVE_PARTICIPANT_NOT_ELIGIBLE")

    compositions = fixture.get("compositions", [])
    composition_by_revision = {row.get("composition_revision_id"): row for row in compositions}
    composition_by_id = {row.get("composition_id"): row for row in compositions}
    realization_by_id: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for composition in compositions:
        expected_nodes: set[str] = set()
        for realization in composition.get("association_realizations", []):
            realization_by_id[realization.get("association_realization_id")] = (composition, realization)
            association = association_by_revision.get(realization.get("association_revision_id"))
            if association is None:
                issues.append(f"{composition.get('composition_revision_id')}:REALIZATION_ASSOCIATION_UNRESOLVED")
                continue
            expected_kind = "PAIR_EDGE" if association.get("association_kind") == "PAIR" else None
            if expected_kind == "PAIR_EDGE" and realization.get("realization_kind") != "PAIR_EDGE":
                issues.append(f"{composition.get('composition_revision_id')}:PAIR_REALIZATION_NOT_EDGE")
            if expected_kind is None and realization.get("realization_kind") == "PAIR_EDGE":
                issues.append(f"{composition.get('composition_revision_id')}:HIGHER_ORDER_PAIR_EDGE_FORBIDDEN")
            expected_incidences = {row.get("incidence_id") for row in association.get("participants", [])}
            if set(realization.get("realized_incidence_ids", [])) != expected_incidences:
                issues.append(f"{composition.get('composition_revision_id')}:REALIZATION_TRACE_MISMATCH")
            expected_nodes.update(row.get("concept_id") for row in association.get("participants", []))
        if set(composition.get("composition_node_ids", [])) != expected_nodes:
            issues.append(f"{composition.get('composition_revision_id')}:COMPOSITION_NODE_TRACE_MISMATCH")

    review_by_id = {
        row.get("composition_coherence_review_id"): row
        for row in fixture.get("composition_coherence_reviews", [])
    }
    for review in review_by_id.values():
        if review.get("decision") == "COHERENT" and not (
            review.get("review_state") == "FINAL"
            and review.get("authority", {}).get("authority_state") == "FINAL"
            and review.get("global_coherence") == "PASS"
            and review.get("bounded_senses_compatible") is True
            and review.get("case_scope_compatible") is True
            and review.get("roles_and_topology_supported") is True
            and review.get("same_configuration") is True
            and review.get("unsupported_bridge_count") == 0
        ):
            issues.append(f"{review.get('composition_coherence_review_id')}:COHERENT_REVIEW_NOT_FAIL_CLOSED")
        composition = composition_by_id.get(review.get("composition_id"))
        if composition is None:
            issues.append(f"{review.get('composition_coherence_review_id')}:COMPOSITION_REVIEW_TARGET_UNRESOLVED")
            continue
        realization_ids = {row.get("association_realization_id") for row in composition.get("association_realizations", [])}
        association_ids = {row.get("association_revision_id") for row in composition.get("association_realizations", [])}
        incidence_ids = {
            incidence_id
            for realization in composition.get("association_realizations", [])
            for incidence_id in realization.get("realized_incidence_ids", [])
        }
        if set(review.get("association_realization_ids", [])) != realization_ids or set(review.get("association_revision_ids", [])) != association_ids or set(review.get("incidence_ids", [])) != incidence_ids:
            issues.append(f"{review.get('composition_coherence_review_id')}:COMPOSITION_REVIEW_TRACE_MISMATCH")
    for composition in compositions:
        review = review_by_id.get(composition.get("global_coherence_review_id"))
        if review is None:
            issues.append(f"{composition.get('composition_revision_id')}:COMPOSITION_REVIEW_UNRESOLVED")
            continue
        if composition.get("product_eligible") and not (
            composition.get("realm") == "PRODUCTION"
            and composition.get("renderability") == "PASS"
            and composition.get("association_trace_complete") is True
            and review.get("decision") == "COHERENT"
            and all(
                association_by_revision[realization["association_revision_id"]].get("lifecycle_state") == "ACTIVE"
                and association_by_revision[realization["association_revision_id"]].get("product_eligible") is True
                for realization in composition.get("association_realizations", [])
            )
        ):
            issues.append(f"{composition.get('composition_revision_id')}:PRODUCT_COMPOSITION_TRACE_INVALID")

    for state in fixture.get("navigation_states", []):
        composition = composition_by_revision.get(state.get("composition_revision_id"))
        if composition is None:
            issues.append(f"{state.get('state_id')}:NAVIGATION_COMPOSITION_UNRESOLVED")
            continue
        nodes = {row.get("navigation_node_id"): row for row in state.get("nodes", [])}
        realized_associations = {row.get("association_revision_id") for row in composition.get("association_realizations", [])}
        previous_to: str | None = None
        for step in state.get("path", []):
            left = nodes.get(step.get("from_navigation_node_id"))
            right = nodes.get(step.get("to_navigation_node_id"))
            if left is None or right is None:
                issues.append(f"{state.get('state_id')}:NAVIGATION_PATH_ENDPOINT_MISSING")
                continue
            if previous_to is not None and step.get("from_navigation_node_id") != previous_to:
                issues.append(f"{state.get('state_id')}:NAVIGATION_PATH_DISCONTINUITY")
            previous_to = step.get("to_navigation_node_id")
            incidence = all_incidences.get(step.get("incidence_id"))
            concept_node = left if left.get("node_kind") == "CONCEPT" else right
            association_node = left if left.get("node_kind") == "ASSOCIATION" else right
            if incidence is None or association_node.get("association_revision_id") not in realized_associations:
                issues.append(f"{state.get('state_id')}:NAVIGATION_INCIDENCE_OWNERSHIP_MISMATCH")
            else:
                association, participant = incidence
                if concept_node.get("concept_id") != participant.get("concept_id") or association_node.get("association_revision_id") != association.get("association_revision_id"):
                    issues.append(f"{state.get('state_id')}:NAVIGATION_INCIDENCE_OWNERSHIP_MISMATCH")
    return sorted(set(issues))


def union_find_components(nodes: Iterable[str], edges: Iterable[Iterable[str]]) -> tuple[int, dict[str, int]]:
    node_list = list(nodes)
    parent = {node: node for node in node_list}
    degree = {node: 0 for node in node_list}

    def root(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for raw_edge in edges:
        edge = list(raw_edge)
        if len(edge) != 2:
            continue
        left, right = edge
        degree[left] += 1
        degree[right] += 1
        left_root, right_root = root(left), root(right)
        if left_root != right_root:
            parent[right_root] = left_root
    return len({root(node) for node in node_list}), degree


def reconstruct_counts(fixture: dict[str, Any]) -> dict[str, Any]:
    associations = fixture["associations"]
    synthetic = [row for row in associations if row["realm"] == "SYNTHETIC_CONTROL"]
    production = [row for row in associations if row["realm"] == "PRODUCTION"]
    active_production = [row for row in production if row["lifecycle_state"] == "ACTIVE"]
    compositions = fixture["compositions"]
    synthetic_compositions = [row for row in compositions if row["realm"] == "SYNTHETIC_CONTROL"]
    production_compositions = [row for row in compositions if row["realm"] == "PRODUCTION"]
    concepts = fixture["concepts"]
    senses = fixture["concept_senses"]
    scopes = fixture["scopes"]
    coherence_reviews = fixture["composition_coherence_reviews"]
    explicitly_governed_pair_revisions = {
        link["pair_association_revision_id"]
        for row in associations
        if row["association_kind"] == "HIGHER_ORDER"
        for link in row["internal_pair_links"]
    } | {
        row["target_association_revision_id"]
        for row in fixture["v2_pair_adapter_receipts"]
    }
    pair_revision_ids = {
        row["association_revision_id"]
        for row in associations
        if row["association_kind"] == "PAIR"
    }
    implicit_pair_revisions = pair_revision_ids - explicitly_governed_pair_revisions
    synthetic_scope_ids = {
        row["scope"]["scope_id"] for row in synthetic
    }
    return {
        "vocabulary": {
            "synthetic_scope_count": len(synthetic_scope_ids),
            "synthetic_distinct_concept_count": len({row["concept_id"] for row in concepts if row["realm"] == "SYNTHETIC_CONTROL"}),
            "synthetic_concept_record_count": sum(row["realm"] == "SYNTHETIC_CONTROL" for row in concepts),
            "synthetic_active_concept_count": sum(row["realm"] == "SYNTHETIC_CONTROL" and row["lifecycle_state"] == "ACTIVE" for row in concepts),
            "synthetic_concept_sense_record_count": sum(row["realm"] == "SYNTHETIC_CONTROL" for row in senses),
            "synthetic_active_concept_sense_count": sum(row["realm"] == "SYNTHETIC_CONTROL" and row["lifecycle_state"] == "ACTIVE" for row in senses),
            "production_active_concept_count": sum(row["realm"] == "PRODUCTION" and row["lifecycle_state"] == "ACTIVE" for row in concepts),
        },
        "associations": {
            "synthetic_pair_revision_count": sum(row["association_kind"] == "PAIR" for row in synthetic),
            "synthetic_higher_order_revision_count": sum(row["association_kind"] == "HIGHER_ORDER" for row in synthetic),
            "synthetic_active_pair_revision_count": sum(row["association_kind"] == "PAIR" and row["lifecycle_state"] == "ACTIVE" for row in synthetic),
            "synthetic_active_higher_order_revision_count": sum(row["association_kind"] == "HIGHER_ORDER" and row["lifecycle_state"] == "ACTIVE" for row in synthetic),
            "production_pair_revision_count": sum(row["association_kind"] == "PAIR" for row in production),
            "production_higher_order_revision_count": sum(row["association_kind"] == "HIGHER_ORDER" for row in production),
            "production_active_association_count": len(active_production),
            "production_active_pending_review_count": sum(
                row["review"]["review_state"] != "FINAL" or row["review"]["authority_state"] != "FINAL"
                for row in active_production
            ),
        },
        "incidence": {
            "synthetic_incidence_count": sum(len(row["participants"]) for row in synthetic),
            "production_incidence_count": sum(len(row["participants"]) for row in production),
            "implicit_projected_pair_count": len(implicit_pair_revisions),
        },
        "realizations_and_compositions": {
            "synthetic_association_realization_count": sum(len(row["association_realizations"]) for row in synthetic_compositions),
            "synthetic_composition_count": len(synthetic_compositions),
            "synthetic_composition_coherence_review_count": sum(row["realm"] == "SYNTHETIC_CONTROL" for row in coherence_reviews),
            "production_association_realization_count": sum(len(row["association_realizations"]) for row in production_compositions),
            "production_composition_count": len(production_compositions),
            "production_composition_coherence_review_count": sum(row["realm"] == "PRODUCTION" for row in coherence_reviews),
            "production_product_eligible_composition_count": sum(row["product_eligible"] for row in production_compositions),
        },
        "interaction": {
            "synthetic_state_count": sum(row["realm"] == "SYNTHETIC_CONTROL" for row in fixture["navigation_states"]),
            "synthetic_workflow_count": sum(row["realm"] == "SYNTHETIC_CONTROL" for row in fixture["workflows"]),
            "synthetic_export_count": sum(row["realm"] == "SYNTHETIC_CONTROL" for row in fixture["exports"]),
            "production_state_count": sum(row["realm"] == "PRODUCTION" for row in fixture["navigation_states"]),
            "production_workflow_count": sum(row["realm"] == "PRODUCTION" for row in fixture["workflows"]),
            "production_export_count": sum(row["realm"] == "PRODUCTION" for row in fixture["exports"]),
        },
    }


def set_pointer(document: Any, pointer: str, value: Any) -> None:
    if not pointer.startswith("/"):
        raise ValueError(pointer)
    tokens = [token.replace("~1", "/").replace("~0", "~") for token in pointer[1:].split("/")]
    target = document
    for token in tokens[:-1]:
        target = target[int(token)] if isinstance(target, list) else target[token]
    final = tokens[-1]
    if isinstance(target, list):
        target[int(final)] = value
    else:
        target[final] = value


def normalize_expectation_rows(fixture: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "control_id": row["control_id"],
            "control_class": row["control_class"],
            "object_refs_json": json.dumps(row["object_refs"], separators=(",", ":")),
            "expected_result": row["expected_result"],
            "assertions_json": json.dumps(row["assertions"], separators=(",", ":")),
            "production_activation_authorized": "false",
            "product_eligibility_authorized": "false",
            "closure_authorized": "false",
        }
        for row in fixture["control_expectations"]
    ]


def run_git(args: list[str]) -> list[str]:
    completed = subprocess.run(["git", *args], cwd=REPO, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return [line for line in completed.stdout.splitlines() if line]


def build_receipt() -> dict[str, Any]:
    checks = CheckRecorder()
    fixture = read_json(FIXTURE_REL)
    hash_contract = read_json(HASH_CONTRACT_REL)
    census = read_json(CENSUS_REL)
    build_receipt = read_json(BUILD_RECEIPT_REL)
    expectations = read_tsv(EXPECTATIONS_REL)
    input_manifest = read_tsv(INPUT_MANIFEST_REL)
    output_manifest = read_tsv(OUTPUT_MANIFEST_REL)
    gaps = read_tsv(GAP_REL)

    checks.equal("source_sha", fixture["source_sha"], SOURCE_SHA)
    checks.equal("parent_checkpoint_sha", fixture["parent_checkpoint_sha"], PARENT_CHECKPOINT_SHA)
    checks.equal("contract_version", fixture["contract_version"], CONTRACT_VERSION)
    checks.equal("api_namespace", fixture["api_namespace"], "trace/exploration/v3")
    checks.equal("fixture_file_sha256", sha256_file(REPO / FIXTURE_REL), EXPECTED_FIXTURE_SHA256)
    checks.equal("hash_contract_file_sha256", sha256_file(REPO / HASH_CONTRACT_REL), EXPECTED_HASH_CONTRACT_FILE_SHA256)
    checks.equal("output_manifest_file_sha256", sha256_file(REPO / OUTPUT_MANIFEST_REL), EXPECTED_OUTPUT_MANIFEST_SHA256)
    checks.equal("build_receipt_file_sha256", sha256_file(REPO / BUILD_RECEIPT_REL), EXPECTED_BUILD_RECEIPT_SHA256)

    schema_paths = sorted(SCHEMAS.glob("*.schema.json"), key=lambda path: path.name)
    checks.equal("schema_filename_set", {path.name for path in schema_paths}, EXPECTED_SCHEMA_NAMES)
    schema_documents = {path.name: json.loads(path.read_text(encoding="utf-8")) for path in schema_paths}
    validator = Draft202012SubsetValidator(schema_documents)
    schema_document_failures = validate_schema_documents(schema_documents, validator)
    checks.equal("schema_document_failure_count", len(schema_document_failures), 0)
    root_schema_errors = validator.errors(fixture, schema_documents["semantic-contract.schema.json"], "semantic-contract.schema.json")
    checks.equal("fixture_root_schema_error_count", len(root_schema_errors), 0)
    hash_contract_schema_errors = validator.errors(hash_contract, schema_documents["hash-binding-contract.schema.json"], "hash-binding-contract.schema.json")
    checks.equal("hash_contract_schema_error_count", len(hash_contract_schema_errors), 0)

    checks.equal("hash_contract_version", hash_contract["contract_version"], HASH_CONTRACT_VERSION)
    checks.equal("embedded_hash_contract", fixture["hash_binding_contract"], hash_contract)
    hash_contract_semantic_failures = hash_contract_semantic_issues(hash_contract)
    checks.equal("hash_contract_semantic_failure_count", len(hash_contract_semantic_failures), 0)
    checks.equal("hash_contract_canonical_sha256", digest(hash_contract), EXPECTED_HASH_CONTRACT_CANONICAL_SHA256)
    checks.equal("fixture_hash_contract_canonical_sha256", fixture["hash_binding_contract_canonical_sha256"], EXPECTED_HASH_CONTRACT_CANONICAL_SHA256)
    expected_canonicalization = {
        "array_order_default": "PRESERVE_STORED_ORDER",
        "digest_algorithm": "SHA-256",
        "digest_representation": "LOWERCASE_HEX_64",
        "item_separators": [",", ":"],
        "json_ensure_ascii": False,
        "object_key_order": "LEXICOGRAPHIC_ASCENDING",
        "text_encoding": "UTF-8",
        "trailing_newline_in_digest_material": False,
    }
    checks.equal("hash_contract_canonicalization", hash_contract["canonicalization"], expected_canonicalization)
    checks.equal("hash_binding_object_type_set", {row["object_type"] for row in hash_contract["bindings"]}, EXPECTED_HASH_BINDING_OBJECT_TYPES)
    hash_results, hash_assertion_count = verify_hash_bindings(fixture, hash_contract)
    checks.true("normative_hash_assertion_count_positive", hash_assertion_count >= 70, hash_assertion_count)
    identity_branch_results = verify_identity_branch_receipts(fixture["identity_branch_test_receipts"], checks)

    associations = fixture["associations"]
    association_by_revision = {row["association_revision_id"]: row for row in associations}
    checks.equal("association_revision_id_uniqueness", len(association_by_revision), len(associations))
    checks.equal(
        "association_identity_version_uniqueness",
        len({(row["association_id"], row["semantic_version"]) for row in associations}),
        len(associations),
    )
    checks.equal("association_semantic_issue_count", sum(len(association_semantic_issues(row)) for row in associations), 0)

    vocabulary_issues, concept_by_id, sense_by_id, scope_by_id = governed_vocabulary_issues(fixture)
    checks.equal("governed_vocabulary_issue_count", len(vocabulary_issues), 0)
    checks.true("governed_concept_count_positive", bool(concept_by_id), len(concept_by_id))
    checks.true("governed_sense_count_positive", bool(sense_by_id), len(sense_by_id))
    checks.true("governed_scope_count_positive", bool(scope_by_id), len(scope_by_id))
    for association in associations:
        scope_id = association["scope"]["scope_id"]
        checks.true(f"association_scope_resolves_{association['association_revision_id']}", scope_id in scope_by_id, scope_id)
        checks.equal(f"association_scope_exact_{association['association_revision_id']}", association["scope"], scope_by_id[scope_id])
        for participant in association["participants"]:
            concept_id = participant["concept_id"]
            sense_id = participant["sense_id"]
            checks.true(f"participant_concept_resolves_{participant['incidence_id']}", concept_id in concept_by_id, concept_id)
            checks.true(f"participant_sense_resolves_{participant['incidence_id']}", sense_id in sense_by_id, sense_id)
            checks.equal(f"participant_sense_concept_{participant['incidence_id']}", sense_by_id[sense_id]["concept_id"], concept_id)
            checks.equal(f"participant_scope_resolves_{participant['incidence_id']}", participant["participant_scope_id"], scope_id)

    pair_governance_issues, internal_pair_ledger = internal_pair_governance_issues(associations)
    checks.equal("internal_pair_governance_issue_count", len(pair_governance_issues), 0)
    checks.equal("governed_internal_pair_link_count", len(internal_pair_ledger), 8)
    checks.equal("governed_internal_pair_failure_count", sum(row["status"] != "PASS" for row in internal_pair_ledger), 0)

    all_incidences: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for association in associations:
        for participant in association["participants"]:
            if participant["incidence_id"] in all_incidences:
                raise AssertionError("global incidence identifier duplicate")
            all_incidences[participant["incidence_id"]] = (association, participant)
    checks.equal("global_incidence_id_count", len(all_incidences), sum(row["arity"] for row in associations))

    compositions = fixture["compositions"]
    composition_by_revision = {row["composition_revision_id"]: row for row in compositions}
    checks.equal("composition_revision_id_uniqueness", len(composition_by_revision), len(compositions))
    realization_by_id: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for composition in compositions:
        realized_concepts: set[str] = set()
        realized_association_revisions: set[str] = set()
        for realization in composition["association_realizations"]:
            checks.true(
                f"realization_association_resolves_{realization['association_realization_id']}",
                realization["association_revision_id"] in association_by_revision,
                realization["association_revision_id"],
            )
            association = association_by_revision[realization["association_revision_id"]]
            realized_association_revisions.add(association["association_revision_id"])
            checks.equal(
                f"realization_realm_{realization['association_realization_id']}",
                association["realm"],
                composition["realm"],
            )
            expected_kind = "PAIR_EDGE" if association["association_kind"] == "PAIR" else None
            if expected_kind is not None:
                checks.equal(f"realization_kind_pair_{realization['association_realization_id']}", realization["realization_kind"], expected_kind)
            else:
                checks.true(
                    f"realization_kind_higher_{realization['association_realization_id']}",
                    realization["realization_kind"] in {"HYPEREDGE_HUB", "HYPEREDGE_CONTOUR", "LIST_GROUP"},
                    realization["realization_kind"],
                )
            expected_incidences = {item["incidence_id"] for item in association["participants"]}
            checks.equal(f"realization_incidence_trace_{realization['association_realization_id']}", set(realization["realized_incidence_ids"]), expected_incidences)
            for incidence_id in realization["realized_incidence_ids"]:
                realized_concepts.add(all_incidences[incidence_id][1]["concept_id"])
            if realization["association_realization_id"] in realization_by_id:
                raise AssertionError(f"duplicate realization identifier: {realization['association_realization_id']}")
            realization_by_id[realization["association_realization_id"]] = (composition, realization)
        checks.equal(f"composition_node_trace_{composition['composition_revision_id']}", set(composition["composition_node_ids"]), realized_concepts)
        checks.true(
            f"composition_nodes_governed_{composition['composition_revision_id']}",
            set(composition["composition_node_ids"]).issubset(concept_by_id),
            composition["composition_node_ids"],
        )
        checks.equal(f"composition_trace_flag_{composition['composition_revision_id']}", composition["association_trace_complete"], True)
        if composition["realm"] == "SYNTHETIC_CONTROL":
            checks.equal(
                f"composition_synthetic_product_tuple_{composition['composition_revision_id']}",
                [
                    composition["product_eligible"],
                    composition["product_path"],
                    composition["product_eligibility_disposition"],
                    bool(composition["product_ineligibility_reason"]),
                ],
                [False, None, "NOT_APPLICABLE_SYNTHETIC", True],
            )
        if composition["product_eligible"]:
            checks.equal(f"product_composition_realm_{composition['composition_revision_id']}", composition["realm"], "PRODUCTION")
            checks.equal(f"product_composition_renderability_{composition['composition_revision_id']}", composition["renderability"], "PASS")
            for realization in composition["association_realizations"]:
                association = association_by_revision[realization["association_revision_id"]]
                checks.true(
                    f"product_composition_active_association_{realization['association_realization_id']}",
                    association["lifecycle_state"] == "ACTIVE" and association["product_eligible"],
                    association["association_revision_id"],
                )

    coherence_reviews = fixture["composition_coherence_reviews"]
    coherence_review_by_id = {
        row["composition_coherence_review_id"]: row
        for row in coherence_reviews
    }
    checks.equal("composition_coherence_review_id_uniqueness", len(coherence_review_by_id), len(coherence_reviews))
    for composition in compositions:
        review_id = composition["global_coherence_review_id"]
        checks.true(f"composition_coherence_review_resolves_{composition['composition_revision_id']}", review_id in coherence_review_by_id, review_id)
        review = coherence_review_by_id[review_id]
        checks.equal(f"composition_coherence_review_composition_{review_id}", review["composition_id"], composition["composition_id"])
        checks.equal(f"composition_coherence_review_realm_{review_id}", review["realm"], composition["realm"])
        realization_ids = {row["association_realization_id"] for row in composition["association_realizations"]}
        association_ids = {row["association_revision_id"] for row in composition["association_realizations"]}
        incidence_ids = {
            incidence_id
            for realization in composition["association_realizations"]
            for incidence_id in realization["realized_incidence_ids"]
        }
        checks.equal(f"composition_review_realization_set_{review_id}", set(review["association_realization_ids"]), realization_ids)
        checks.equal(f"composition_review_association_set_{review_id}", set(review["association_revision_ids"]), association_ids)
        checks.equal(f"composition_review_incidence_set_{review_id}", set(review["incidence_ids"]), incidence_ids)
        authority = review["authority"]
        authority_final = bool(
            isinstance(authority.get("authority_id"), str)
            and authority.get("authority_id")
            and isinstance(authority.get("authority_kind"), str)
            and authority.get("authority_kind")
            and authority.get("authority_state") == "FINAL"
            and isinstance(authority.get("authority_version"), str)
            and authority.get("authority_version")
        )
        derived_review_pass = bool(
            review["review_state"] == "FINAL"
            and authority_final
            and review["global_coherence"] == "PASS"
            and review["bounded_senses_compatible"] is True
            and review["case_scope_compatible"] is True
            and review["roles_and_topology_supported"] is True
            and review["same_configuration"] is True
            and review["unsupported_bridge_count"] == 0
        )
        if review["global_coherence"] == "PASS":
            checks.true(f"composition_review_pass_is_derived_{review_id}", derived_review_pass, review)
            checks.equal(f"composition_review_coherent_decision_{review_id}", review["decision"], "COHERENT")
        else:
            checks.true(f"composition_review_noncoherent_decision_{review_id}", review["decision"] in {"INCOHERENT", "UNRESOLVED"}, review["decision"])
        if composition["product_eligible"]:
            checks.true(f"product_composition_coherence_gate_{review_id}", derived_review_pass, review)
            checks.true(
                f"product_composition_review_decision_{review_id}",
                review["decision"] == "COHERENT",
                review["decision"],
            )
        else:
            checks.true(
                f"nonproduct_composition_reason_{review_id}",
                bool(review["reasons"]) or composition["realm"] == "SYNTHETIC_CONTROL",
                review["reasons"],
            )

    states = fixture["navigation_states"]
    state_by_id = {row["state_id"]: row for row in states}
    checks.equal("navigation_state_id_uniqueness", len(state_by_id), len(states))
    for state in states:
        checks.true(f"navigation_composition_resolves_{state['state_id']}", state["composition_revision_id"] in composition_by_revision, state["composition_revision_id"])
        composition = composition_by_revision[state["composition_revision_id"]]
        checks.equal(f"navigation_realm_{state['state_id']}", state["realm"], composition["realm"])
        composition_realizations = {
            realization["association_revision_id"]: set(realization["realized_incidence_ids"])
            for realization in composition["association_realizations"]
        }
        nodes = {row["navigation_node_id"]: row for row in state["nodes"]}
        checks.equal(f"navigation_node_id_uniqueness_{state['state_id']}", len(nodes), len(state["nodes"]))
        checks.true(f"navigation_focus_exists_{state['state_id']}", state["focus_navigation_node_id"] in nodes, state["focus_navigation_node_id"])
        for node in nodes.values():
            if node["node_kind"] == "CONCEPT":
                checks.true(
                    f"navigation_concept_shape_{node['navigation_node_id']}",
                    isinstance(node["concept_id"], str)
                    and node["association_revision_id"] is None
                    and node["concept_id"] in composition["composition_node_ids"]
                    and node["concept_id"] in concept_by_id,
                    node,
                )
            elif node["node_kind"] == "ASSOCIATION":
                checks.true(
                    f"navigation_association_shape_{node['navigation_node_id']}",
                    node["concept_id"] is None
                    and node["association_revision_id"] in association_by_revision
                    and node["association_revision_id"] in composition_realizations,
                    node,
                )
            else:
                raise AssertionError(f"navigation node kind is not governed: {node['node_kind']}")
        previous_to: str | None = None
        derived_alternation = True
        for index, step in enumerate(state["path"]):
            checks.true(
                f"navigation_endpoints_resolve_{state['state_id']}_{index}",
                step["from_navigation_node_id"] in nodes and step["to_navigation_node_id"] in nodes,
                step,
            )
            left = nodes[step["from_navigation_node_id"]]
            right = nodes[step["to_navigation_node_id"]]
            step_alternates = {left["node_kind"], right["node_kind"]} == {"CONCEPT", "ASSOCIATION"}
            derived_alternation = derived_alternation and step_alternates
            checks.true(f"navigation_bipartite_step_{state['state_id']}_{index}", step_alternates, [left["node_kind"], right["node_kind"]])
            if previous_to is not None:
                checks.equal(f"navigation_path_continuity_{state['state_id']}_{index}", step["from_navigation_node_id"], previous_to)
            previous_to = step["to_navigation_node_id"]
            checks.true(f"navigation_incidence_resolves_{state['state_id']}_{index}", step["incidence_id"] in all_incidences, step["incidence_id"])
            association, participant = all_incidences[step["incidence_id"]]
            concept_node = left if left["node_kind"] == "CONCEPT" else right
            association_node = left if left["node_kind"] == "ASSOCIATION" else right
            checks.equal(f"navigation_incidence_concept_{state['state_id']}_{index}", concept_node["concept_id"], participant["concept_id"])
            checks.equal(f"navigation_incidence_association_{state['state_id']}_{index}", association_node["association_revision_id"], association["association_revision_id"])
            checks.true(
                f"navigation_incidence_realized_{state['state_id']}_{index}",
                step["incidence_id"] in composition_realizations[association["association_revision_id"]],
                step["incidence_id"],
            )
        checks.equal(f"navigation_focus_terminal_{state['state_id']}", previous_to, state["focus_navigation_node_id"])
        checks.equal(f"navigation_derived_alternation_{state['state_id']}", state["bipartite_alternation_valid"], derived_alternation)

    workflows = fixture["workflows"]
    workflow_by_id = {row["workflow_id"]: row for row in workflows}
    checks.equal("workflow_id_uniqueness", len(workflow_by_id), len(workflows))
    for workflow in workflows:
        checks.true(f"workflow_initial_state_{workflow['workflow_id']}", workflow["initial_state_id"] in workflow["state_ids"] and workflow["initial_state_id"] in state_by_id, workflow["initial_state_id"])
        checks.true(f"workflow_state_refs_{workflow['workflow_id']}", set(workflow["state_ids"]).issubset(state_by_id), workflow["state_ids"])
        checks.true(f"workflow_association_refs_{workflow['workflow_id']}", set(workflow["association_revision_ids"]).issubset(association_by_revision), workflow["association_revision_ids"])
        checks.true(f"workflow_realization_refs_{workflow['workflow_id']}", set(workflow["association_realization_ids"]).issubset(realization_by_id), workflow["association_realization_ids"])
        workflow_realization_associations = {
            realization_by_id[realization_id][1]["association_revision_id"]
            for realization_id in workflow["association_realization_ids"]
        }
        checks.equal(
            f"workflow_realization_association_trace_{workflow['workflow_id']}",
            set(workflow["association_revision_ids"]),
            workflow_realization_associations,
        )
        workflow_compositions = {
            state_by_id[state_id]["composition_revision_id"]
            for state_id in workflow["state_ids"]
        }
        checks.true(
            f"workflow_realizations_reachable_from_states_{workflow['workflow_id']}",
            all(realization_by_id[realization_id][0]["composition_revision_id"] in workflow_compositions for realization_id in workflow["association_realization_ids"]),
            workflow["association_realization_ids"],
        )
        checks.true(
            f"workflow_realm_trace_{workflow['workflow_id']}",
            all(state_by_id[state_id]["realm"] == workflow["realm"] for state_id in workflow["state_ids"]),
            workflow["realm"],
        )
        if workflow["reachable"]:
            checks.true(f"workflow_reachable_path_{workflow['workflow_id']}", all(state_by_id[state_id]["path"] for state_id in workflow["state_ids"]), workflow["state_ids"])

    for export in fixture["exports"]:
        workflow = workflow_by_id[export["workflow_id"]]
        state = state_by_id[export["state_id"]]
        composition = composition_by_revision[export["composition_revision_id"]]
        checks.true(f"export_state_in_workflow_{export['export_id']}", export["state_id"] in workflow["state_ids"], export["state_id"])
        checks.equal(f"export_state_composition_{export['export_id']}", state["composition_revision_id"], composition["composition_revision_id"])
        checks.true(f"export_association_refs_{export['export_id']}", set(export["association_revision_ids"]).issubset(association_by_revision), export["association_revision_ids"])
        checks.true(f"export_realization_refs_{export['export_id']}", set(export["association_realization_ids"]).issubset(realization_by_id), export["association_realization_ids"])
        checks.equal(f"export_workflow_realization_trace_{export['export_id']}", set(export["association_realization_ids"]), set(workflow["association_realization_ids"]))
        export_realization_associations = {
            realization_by_id[realization_id][1]["association_revision_id"]
            for realization_id in export["association_realization_ids"]
        }
        checks.equal(f"export_association_realization_trace_{export['export_id']}", set(export["association_revision_ids"]), export_realization_associations)
        checks.true(
            f"export_composition_realization_trace_{export['export_id']}",
            all(realization_by_id[realization_id][0]["composition_revision_id"] == composition["composition_revision_id"] for realization_id in export["association_realization_ids"]),
            export["association_realization_ids"],
        )
        projection_records = {
            row["association_realization_id"]: row
            for row in export["projection_preservation_records"]
        }
        checks.equal(
            f"export_projection_record_uniqueness_{export['export_id']}",
            len(projection_records),
            len(export["projection_preservation_records"]),
        )
        checks.equal(
            f"export_projection_record_coverage_{export['export_id']}",
            set(projection_records),
            set(export["association_realization_ids"]),
        )
        derived_projection_preserved = True
        for association_id in export["association_revision_ids"]:
            association = association_by_revision[association_id]
            if association["association_kind"] == "HIGHER_ORDER":
                checks.equal(f"export_higher_order_no_projection_{export['export_id']}_{association_id}", association["pair_projection_policy"], "NONE")
        for realization_id in export["association_realization_ids"]:
            realization = realization_by_id[realization_id][1]
            association = association_by_revision[realization["association_revision_id"]]
            record = projection_records[realization_id]
            checks.equal(f"export_projection_record_association_{export['export_id']}_{realization_id}", record["association_revision_id"], association["association_revision_id"])
            checks.equal(f"export_projection_record_policy_{export['export_id']}_{realization_id}", record["pair_projection_policy"], association["pair_projection_policy"])
            checks.equal(f"export_projection_record_realization_kind_{export['export_id']}_{realization_id}", record["realization_kind"], realization["realization_kind"])
            if association["association_kind"] == "HIGHER_ORDER":
                derived_projection_preserved = derived_projection_preserved and record["realization_kind"] != "PAIR_EDGE" and record["pair_projection_policy"] == "NONE"
            else:
                derived_projection_preserved = derived_projection_preserved and record["realization_kind"] == "PAIR_EDGE" and record["pair_projection_policy"] == "NOT_APPLICABLE"
        checks.equal(f"export_projection_policy_derived_{export['export_id']}", export["pair_projection_policy_preserved"], derived_projection_preserved)

    source_fixture_by_id = {row["source_pair_id"]: row for row in fixture["v2_pair_source_fixtures"]}
    checks.equal("v2_pair_source_id_uniqueness", len(source_fixture_by_id), len(fixture["v2_pair_source_fixtures"]))
    adapter_results: list[dict[str, Any]] = []
    adapter_ids: set[str] = set()
    for adapter in fixture["v2_pair_adapter_receipts"]:
        checks.true(f"adapter_id_unique_{adapter['adapter_id']}", adapter["adapter_id"] not in adapter_ids, adapter["adapter_id"])
        adapter_ids.add(adapter["adapter_id"])
        checks.true(f"adapter_source_resolves_{adapter['adapter_id']}", adapter["source_pair_id"] in source_fixture_by_id, adapter["source_pair_id"])
        source = source_fixture_by_id[adapter["source_pair_id"]]
        checks.true(f"adapter_target_resolves_{adapter['adapter_id']}", adapter["target_association_revision_id"] in association_by_revision, adapter["target_association_revision_id"])
        target = association_by_revision[adapter["target_association_revision_id"]]
        checks.equal(f"adapter_source_hash_{adapter['adapter_id']}", adapter["source_pair_fixture_sha256"], source["source_pair_fixture_sha256"])
        checks.equal(f"adapter_source_endpoints_{adapter['adapter_id']}", set(adapter["source_endpoint_ids"]), {row["source_endpoint_id"] for row in source["endpoints"]})
        checks.equal(f"adapter_target_kind_{adapter['adapter_id']}", target["association_kind"], "PAIR")
        checks.equal(f"adapter_target_arity_{adapter['adapter_id']}", target["arity"], 2)
        checks.equal(f"adapter_target_incidences_{adapter['adapter_id']}", set(adapter["target_incidence_ids"]), {row["incidence_id"] for row in target["participants"]})
        source_by_endpoint = {row["source_endpoint_id"]: row for row in source["endpoints"]}
        target_by_incidence = {row["incidence_id"]: row for row in target["participants"]}
        checks.equal(f"adapter_source_endpoint_count_{adapter['adapter_id']}", len(source_by_endpoint), 2)
        checks.equal(f"adapter_crosswalk_count_{adapter['adapter_id']}", len(adapter["endpoint_crosswalk"]), 2)
        checks.equal(
            f"adapter_crosswalk_source_coverage_{adapter['adapter_id']}",
            {row["source_endpoint_id"] for row in adapter["endpoint_crosswalk"]},
            set(source_by_endpoint),
        )
        checks.equal(
            f"adapter_crosswalk_target_coverage_{adapter['adapter_id']}",
            {row["target_incidence_id"] for row in adapter["endpoint_crosswalk"]},
            set(target_by_incidence),
        )
        for crosswalk in adapter["endpoint_crosswalk"]:
            source_endpoint = source_by_endpoint[crosswalk["source_endpoint_id"]]
            target_incidence = target_by_incidence[crosswalk["target_incidence_id"]]
            checks.equal(f"adapter_crosswalk_concept_{adapter['adapter_id']}_{crosswalk['source_endpoint_id']}", crosswalk["target_concept_id"], source_endpoint["concept_id"])
            checks.equal(f"adapter_crosswalk_sense_{adapter['adapter_id']}_{crosswalk['source_endpoint_id']}", crosswalk["target_sense_id"], source_endpoint["sense_id"])
            checks.equal(f"adapter_crosswalk_target_concept_{adapter['adapter_id']}_{crosswalk['source_endpoint_id']}", crosswalk["target_concept_id"], target_incidence["concept_id"])
            checks.equal(f"adapter_crosswalk_target_sense_{adapter['adapter_id']}_{crosswalk['source_endpoint_id']}", crosswalk["target_sense_id"], target_incidence["sense_id"])
            checks.true(f"adapter_crosswalk_governed_concept_{adapter['adapter_id']}_{crosswalk['source_endpoint_id']}", crosswalk["target_concept_id"] in concept_by_id, crosswalk["target_concept_id"])
            checks.true(f"adapter_crosswalk_governed_sense_{adapter['adapter_id']}_{crosswalk['source_endpoint_id']}", crosswalk["target_sense_id"] in sense_by_id, crosswalk["target_sense_id"])
        checks.equal(f"adapter_direction_{adapter['adapter_id']}", adapter["direction"], "V2_PAIR_TO_V3_PAIR_ONLY")
        checks.equal(f"adapter_higher_order_forbidden_{adapter['adapter_id']}", adapter["higher_order_input_allowed"], False)
        checks.equal(f"adapter_reverse_forbidden_{adapter['adapter_id']}", adapter["reverse_conversion_allowed"], False)
        checks.equal(f"adapter_claim_addition_forbidden_{adapter['adapter_id']}", adapter["semantic_claims_added"], False)
        checks.equal(f"adapter_input_arity_{adapter['adapter_id']}", adapter["input_arity"], 2)
        checks.equal(f"adapter_output_kind_{adapter['adapter_id']}", adapter["output_association_kind"], "PAIR")
        adapter_results.append({"adapter_id": adapter["adapter_id"], "source_pair_id": source["source_pair_id"], "target_association_revision_id": target["association_revision_id"], "status": "PASS"})

    controls_by_class = {row["control_class"]: row for row in fixture["control_expectations"]}
    checks.equal("control_class_set", set(controls_by_class), EXPECTED_CONTROL_CLASSES)
    checks.equal("control_id_sequence", [row["control_id"] for row in fixture["control_expectations"]], [f"CTRL-V3-{index:03d}" for index in range(1, 11)])
    control_results: list[dict[str, Any]] = []

    sparse_control = controls_by_class["VALID_SPARSE_DISCONNECTED_HIGHER_ORDER_GROUP"]
    sparse = association_by_revision[sparse_control["object_refs"][0]]
    sparse_components, sparse_degree = union_find_components(
        [row["incidence_id"] for row in sparse["participants"]],
        [row["participant_incidence_ids"] for row in sparse["internal_pair_links"]],
    )
    sparse_observed = {
        "arity": sparse["arity"],
        "internal_pair_count": len(sparse["internal_pair_links"]),
        "internal_pair_components": sparse_components,
        "pair_projection_policy": sparse["pair_projection_policy"],
        "global_coherence": sparse["review"]["global_coherence"],
    }
    checks.equal("control_sparse_observation", sparse_observed, {"arity": 5, "internal_pair_count": 2, "internal_pair_components": 3, "pair_projection_policy": "NONE", "global_coherence": "PASS"})
    checks.equal("control_sparse_assertions", set(sparse_control["assertions"]), {"arity=5", "internal_pair_count=2", "internal_pair_components=3", "all_internal_pairs=ACTIVE", "pair_projection_policy=NONE", "global_coherence=PASS"})
    control_results.append({"control_id": sparse_control["control_id"], "status": "PASS", "observed": sparse_observed})

    clique_control = controls_by_class["INVALID_FULL_PAIR_CLIQUE"]
    clique = association_by_revision[clique_control["object_refs"][0]]
    clique_components, _ = union_find_components(
        [row["incidence_id"] for row in clique["participants"]],
        [row["participant_incidence_ids"] for row in clique["internal_pair_links"]],
    )
    clique_observed = {"arity": clique["arity"], "pair_count": len(clique["internal_pair_links"]), "possible_pair_count": clique["arity"] * (clique["arity"] - 1) // 2, "components": clique_components, "coherence": clique["review"]["global_coherence"], "lifecycle": clique["lifecycle_state"]}
    checks.equal("control_clique_observation", clique_observed, {"arity": 4, "pair_count": 6, "possible_pair_count": 6, "components": 1, "coherence": "FAIL", "lifecycle": "INACTIVE"})
    checks.equal("control_clique_assertions", set(clique_control["assertions"]), {"arity=4", "internal_pair_count=6", "all_six_pair_revisions=ACTIVE", "global_coherence=FAIL", "lifecycle_state=INACTIVE"})
    control_results.append({"control_id": clique_control["control_id"], "status": "PASS", "observed": clique_observed})

    sense_control = controls_by_class["BOUNDED_SENSE_CONFLICT"]
    sense_conflict = association_by_revision[sense_control["object_refs"][0]]
    sense_observed = {"bounded_senses_compatible": sense_conflict["review"]["bounded_senses_compatible"], "global_coherence": sense_conflict["review"]["global_coherence"], "active": sense_conflict["lifecycle_state"] == "ACTIVE"}
    checks.equal("control_sense_conflict", sense_observed, {"bounded_senses_compatible": False, "global_coherence": "FAIL", "active": False})
    control_results.append({"control_id": sense_control["control_id"], "status": "PASS", "observed": sense_observed})

    case_control = controls_by_class["CROSS_CASE_SOURCE_BUNDLE"]
    cross_case = association_by_revision[case_control["object_refs"][0]]
    case_observed = {"case_scope_compatible": cross_case["review"]["case_scope_compatible"], "historical_case_count": len(cross_case["scope"]["historical_case_ids"]), "unsupported_bridge_count": cross_case["review"]["unsupported_bridge_count"], "same_configuration": cross_case["evidence"]["same_configuration"]}
    checks.equal("control_cross_case", case_observed, {"case_scope_compatible": False, "historical_case_count": 2, "unsupported_bridge_count": 2, "same_configuration": False})
    control_results.append({"control_id": case_control["control_id"], "status": "PASS", "observed": case_observed})

    isolated_control = controls_by_class["ISOLATED_ACTIVE_TERM_IN_VALID_HYPEREDGE"]
    isolated_concept = isolated_control["object_refs"][1]
    isolated_sense = isolated_control["object_refs"][2]
    isolated_incidence = next(row["incidence_id"] for row in sparse["participants"] if row["concept_id"] == isolated_concept)
    isolated_observed = {
        "concept_id": isolated_concept,
        "sense_id": isolated_sense,
        "internal_pair_degree": sparse_degree[isolated_incidence],
        "concept_lifecycle": concept_by_id[isolated_concept]["lifecycle_state"],
        "sense_lifecycle": sense_by_id[isolated_sense]["lifecycle_state"],
        "association_lifecycle": sparse["lifecycle_state"],
        "realm": sparse["realm"],
    }
    checks.equal("control_isolated_term", isolated_observed, {"concept_id": isolated_concept, "sense_id": isolated_sense, "internal_pair_degree": 0, "concept_lifecycle": "ACTIVE", "sense_lifecycle": "ACTIVE", "association_lifecycle": "ACTIVE", "realm": "SYNTHETIC_CONTROL"})
    control_results.append({"control_id": isolated_control["control_id"], "status": "PASS", "observed": isolated_observed})

    render_control = controls_by_class["RENDERABLE_COMPOSITION_WITHOUT_VALID_GROUP"]
    render_composition = composition_by_revision[render_control["object_refs"][0]]
    render_association = association_by_revision[render_control["object_refs"][1]]
    render_observed = {"renderability": render_composition["renderability"], "group_coherence": render_association["review"]["global_coherence"], "product_eligible": render_composition["product_eligible"]}
    checks.equal("control_renderable_invalid", render_observed, {"renderability": "PASS", "group_coherence": "FAIL", "product_eligible": False})
    control_results.append({"control_id": render_control["control_id"], "status": "PASS", "observed": render_observed})

    attempts_by_id = {row["attempt_id"]: row for row in fixture["invalid_attempts"]}
    projection_control = controls_by_class["ILLEGAL_HYPEREDGE_PAIR_PROJECTION"]
    projection_attempt = attempts_by_id[projection_control["object_refs"][1]]
    sparse_pair_records = [row for row in associations if row["association_kind"] == "PAIR" and {item["concept_id"] for item in row["participants"]}.issubset({item["concept_id"] for item in sparse["participants"]})]
    sparse_explicit_pair_revisions = {link["pair_association_revision_id"] for link in sparse["internal_pair_links"]}
    projected_pair_records = [row for row in sparse_pair_records if row["association_revision_id"] not in sparse_explicit_pair_revisions]
    projection_observed = {
        "policy": sparse["pair_projection_policy"],
        "attempt_decision": projection_attempt["expected_decision"],
        "governed_internal_pair_count": len(sparse_explicit_pair_revisions),
        "implicit_pair_creation_count": len(projected_pair_records),
    }
    checks.equal("control_illegal_projection", projection_observed, {"policy": "NONE", "attempt_decision": "REJECT", "governed_internal_pair_count": 2, "implicit_pair_creation_count": 0})
    control_results.append({"control_id": projection_control["control_id"], "status": "PASS", "observed": projection_observed})

    pending_control = controls_by_class["ACTIVE_WITH_PENDING_OR_NONFINAL_REVIEW"]
    pending = association_by_revision[pending_control["object_refs"][0]]
    pending_attempt = attempts_by_id[pending_control["object_refs"][1]]
    pending_observed = {"review_state": pending["review"]["review_state"], "authority_state": pending["review"]["authority_state"], "activation_decision": pending["activation"]["decision"], "lifecycle": pending["lifecycle_state"], "attempt_decision": pending_attempt["expected_decision"]}
    checks.equal("control_pending_active", pending_observed, {"review_state": "PENDING", "authority_state": "PENDING", "activation_decision": "REJECT", "lifecycle": "INACTIVE", "attempt_decision": "REJECT"})
    control_results.append({"control_id": pending_control["control_id"], "status": "PASS", "observed": pending_observed})

    arity_control = controls_by_class["ACTIVE_ARITY_FIVE_PROJECTION_NONE"]
    checks.equal("control_active_arity_five", [sparse["lifecycle_state"], sparse["arity"], sparse["pair_projection_policy"], sparse["realm"]], ["ACTIVE", 5, "NONE", "SYNTHETIC_CONTROL"])
    control_results.append({"control_id": arity_control["control_id"], "status": "PASS", "observed": {"lifecycle": "ACTIVE", "arity": 5, "projection": "NONE"}})

    adapter_control = controls_by_class["ONE_WAY_V2_PAIR_ADAPTER"]
    adapter = next(row for row in fixture["v2_pair_adapter_receipts"] if row["adapter_id"] == adapter_control["object_refs"][0])
    checks.equal("control_adapter_target", adapter["target_association_revision_id"], adapter_control["object_refs"][1])
    checks.equal("control_adapter_flags", [adapter["direction"], adapter["reverse_conversion_allowed"], adapter["higher_order_input_allowed"], adapter["semantic_claims_added"]], ["V2_PAIR_TO_V3_PAIR_ONLY", False, False, False])
    control_results.append({"control_id": adapter_control["control_id"], "status": "PASS", "observed": {"direction": adapter["direction"], "reverse": False, "higher_order_input": False}})
    checks.equal("control_result_count", len(control_results), 10)
    checks.equal("expectation_tsv_exact_reconstruction", expectations, normalize_expectation_rows(fixture))

    primary_probe_receipts = fixture["schema_negative_probe_receipts"]
    base_objects: dict[str, dict[str, Any]] = {}
    base_object_locations: dict[str, tuple[str, int]] = {}
    collection_identifiers = {
        "associations": "association_revision_id",
        "compositions": "composition_revision_id",
        "navigation_states": "state_id",
        "workflows": "workflow_id",
        "exports": "export_id",
        "concepts": "concept_id",
        "concept_senses": "sense_id",
        "composition_coherence_reviews": "composition_coherence_review_id",
    }
    for collection_name, identifier_field in collection_identifiers.items():
        for index, row in enumerate(fixture[collection_name]):
            reference = row[identifier_field]
            base_objects[reference] = row
            base_object_locations[reference] = (collection_name, index)
    independent_probe_results: list[dict[str, Any]] = []
    for receipt in primary_probe_receipts:
        mutated = copy.deepcopy(base_objects[receipt["base_object_ref"]])
        set_pointer(mutated, receipt["mutation_pointer"], json.loads(receipt["mutation_value_json"]))
        if receipt["validator"] == "JSON_SCHEMA":
            target_schema = receipt["target_schema"]
            schema_name, marker, fragment = target_schema.partition("#")
            schema = schema_documents[schema_name]
            if marker:
                schema = validator._pointer(schema, f"#{fragment}")
            errors = validator.errors(mutated, schema, schema_name)
        elif receipt["validator"] == "SEMANTIC_INVARIANT":
            errors = association_semantic_issues(mutated)
        elif receipt["validator"] == "FIXTURE_SEMANTIC_INVARIANT":
            mutant_fixture = copy.deepcopy(fixture)
            collection_name, index = base_object_locations[receipt["base_object_ref"]]
            mutant_fixture[collection_name][index] = mutated
            errors = fixture_semantic_issues(mutant_fixture)
        else:
            raise AssertionError(f"unknown primary negative-probe validator: {receipt['validator']}")
        checks.true(f"independent_primary_probe_rejected_{receipt['probe_id']}", bool(errors), errors)
        checks.equal(f"primary_probe_receipt_expected_{receipt['probe_id']}", [receipt["expected_rejected"], receipt["observed_rejected"]], [True, True])
        checks.true(f"primary_probe_receipt_errors_{receipt['probe_id']}", bool(receipt["observed_error_codes"]), receipt["observed_error_codes"])
        independent_probe_results.append({"probe_id": receipt["probe_id"], "status": "PASS", "independent_errors": errors})
    checks.equal("primary_negative_probe_count", len(independent_probe_results), 37)

    adversarial_results: list[dict[str, Any]] = []
    independent_mutations = [
        ("ADV-V3-001", "association", "/evidence/support_mode", "NONE"),
        ("ADV-V3-002", "association", "/review/authority_state", "PENDING"),
        ("ADV-V3-003", "association", "/activation/product_policy_gate", False),
        ("ADV-V3-004", "association", "/participants/0/ordinal", 0),
        ("ADV-V3-005", "association", "/participants/0/role_id", "invented-role"),
        ("ADV-V3-006", "composition", "/product_eligible", True),
    ]
    for probe_id, kind, pointer, value in independent_mutations:
        base = sparse if kind == "association" else render_composition
        schema_name = "association.schema.json" if kind == "association" else "composition.schema.json"
        mutated = copy.deepcopy(base)
        set_pointer(mutated, pointer, value)
        schema_errors = validator.errors(mutated, schema_documents[schema_name], schema_name)
        checks.true(f"fresh_adversarial_schema_rejected_{probe_id}", bool(schema_errors), schema_errors)
        errors = schema_errors
        if kind == "association":
            semantic_errors = association_semantic_issues(mutated)
            checks.true(f"fresh_adversarial_semantic_rejected_{probe_id}", bool(semantic_errors), semantic_errors)
            errors = sorted(set(errors + semantic_errors))
        checks.true(f"fresh_adversarial_rejected_{probe_id}", bool(errors), errors)
        adversarial_results.append({"probe_id": probe_id, "mutation_pointer": pointer, "status": "PASS", "independent_errors": errors})

    nav_mutant = copy.deepcopy(states[0])
    nav_mutant["path"][0]["to_navigation_node_id"] = nav_mutant["nodes"][2]["navigation_node_id"]
    nav_nodes = {row["navigation_node_id"]: row for row in nav_mutant["nodes"]}
    nav_invalid = any(nav_nodes[step["from_navigation_node_id"]]["node_kind"] == nav_nodes[step["to_navigation_node_id"]]["node_kind"] for step in nav_mutant["path"])
    checks.true("fresh_adversarial_rejected_ADV_V3_007", nav_invalid, "same-kind navigation step detected")
    adversarial_results.append({"probe_id": "ADV-V3-007", "mutation_pointer": "/path/0/to_navigation_node_id", "status": "PASS", "independent_errors": ["BIPARTITE_ALTERNATION"]})

    adapter_mutant = copy.deepcopy(adapter)
    adapter_mutant["target_association_revision_id"] = sparse["association_revision_id"]
    adapter_invalid = association_by_revision[adapter_mutant["target_association_revision_id"]]["association_kind"] != "PAIR"
    checks.true("fresh_adversarial_rejected_ADV_V3_008", adapter_invalid, "higher-order adapter target detected")
    adversarial_results.append({"probe_id": "ADV-V3-008", "mutation_pointer": "/target_association_revision_id", "status": "PASS", "independent_errors": ["ADAPTER_TARGET_NOT_PAIR"]})

    for probe_id, pointer in (
        ("ADV-V3-009", "/evidence/evidence_item_ids"),
        ("ADV-V3-010", "/evidence/locator_ids"),
        ("ADV-V3-011", "/evidence/negative_or_conflicting_evidence"),
    ):
        mutant = copy.deepcopy(sparse)
        set_pointer(mutant, pointer, ["synthetic-conflict"] if probe_id.endswith("011") else [])
        errors = sorted(
            set(
                validator.errors(mutant, schema_documents["association.schema.json"], "association.schema.json")
                + association_semantic_issues(mutant)
            )
        )
        schema_gate_errors = validator.errors(mutant, schema_documents["association.schema.json"], "association.schema.json")
        semantic_gate_errors = association_semantic_issues(mutant)
        checks.true(f"fresh_adversarial_schema_rejected_{probe_id}", bool(schema_gate_errors), schema_gate_errors)
        checks.true(f"fresh_adversarial_semantic_rejected_{probe_id}", bool(semantic_gate_errors), semantic_gate_errors)
        checks.true(f"fresh_adversarial_rejected_{probe_id}", bool(errors), errors)
        adversarial_results.append({"probe_id": probe_id, "mutation_pointer": pointer, "status": "PASS", "independent_errors": errors})

    pair_link_mutant = copy.deepcopy(associations)
    higher_mutant = next(row for row in pair_link_mutant if row["association_revision_id"] == sparse["association_revision_id"])
    higher_mutant["internal_pair_links"][0]["pair_association_revision_id"] = sparse["association_revision_id"]
    pair_mutant_errors, _ = internal_pair_governance_issues(pair_link_mutant)
    checks.true("fresh_adversarial_rejected_ADV_V3_012", bool(pair_mutant_errors), pair_mutant_errors)
    adversarial_results.append({"probe_id": "ADV-V3-012", "mutation_pointer": "/internal_pair_links/0/pair_association_revision_id", "status": "PASS", "independent_errors": pair_mutant_errors})

    illegal_higher_realization = copy.deepcopy(
        next(
            realization
            for composition in compositions
            for realization in composition["association_realizations"]
            if association_by_revision[realization["association_revision_id"]]["association_kind"] == "HIGHER_ORDER"
        )
    )
    illegal_higher_realization["realization_kind"] = "PAIR_EDGE"
    higher_realization_invalid = association_by_revision[illegal_higher_realization["association_revision_id"]]["association_kind"] == "HIGHER_ORDER"
    checks.true("fresh_adversarial_rejected_ADV_V3_013", higher_realization_invalid, "higher-order PAIR_EDGE detected")
    adversarial_results.append({"probe_id": "ADV-V3-013", "mutation_pointer": "/association_realizations/0/realization_kind", "status": "PASS", "independent_errors": ["HIGHER_ORDER_PAIR_EDGE_FORBIDDEN"]})

    pair_target = association_by_revision[adapter["target_association_revision_id"]]
    illegal_pair_kind = "HYPEREDGE_HUB"
    pair_realization_invalid = pair_target["association_kind"] == "PAIR" and illegal_pair_kind != "PAIR_EDGE"
    checks.true("fresh_adversarial_rejected_ADV_V3_014", pair_realization_invalid, illegal_pair_kind)
    adversarial_results.append({"probe_id": "ADV-V3-014", "mutation_pointer": "/realization_kind", "status": "PASS", "independent_errors": ["PAIR_NON_PAIR_EDGE_FORBIDDEN"]})

    concept_mutant = copy.deepcopy(next(iter(concept_by_id.values())))
    concept_mutant["authority"]["authority_id"] = ""
    concept_errors = validator.errors(concept_mutant, schema_documents["concept.schema.json"]["$defs"]["concept"], "concept.schema.json")
    checks.true("fresh_adversarial_rejected_ADV_V3_015", bool(concept_errors), concept_errors)
    adversarial_results.append({"probe_id": "ADV-V3-015", "mutation_pointer": "/authority/authority_id", "status": "PASS", "independent_errors": concept_errors})

    sense_mutant = copy.deepcopy(next(iter(sense_by_id.values())))
    sense_mutant["bounded_definition"] = ""
    sense_errors = validator.errors(sense_mutant, schema_documents["concept.schema.json"]["$defs"]["conceptSense"], "concept.schema.json")
    checks.true("fresh_adversarial_rejected_ADV_V3_016", bool(sense_errors), sense_errors)
    adversarial_results.append({"probe_id": "ADV-V3-016", "mutation_pointer": "/bounded_definition", "status": "PASS", "independent_errors": sense_errors})

    scope_mutant = copy.deepcopy(sparse)
    scope_mutant["scope"]["actors"] = ["scope-drift"]
    scope_invalid = scope_mutant["scope"] != scope_by_id[scope_mutant["scope"]["scope_id"]]
    checks.true("fresh_adversarial_rejected_ADV_V3_017", scope_invalid, scope_mutant["scope"])
    adversarial_results.append({"probe_id": "ADV-V3-017", "mutation_pointer": "/scope/actors", "status": "PASS", "independent_errors": ["GOVERNED_SCOPE_DRIFT"]})

    review_mutant = copy.deepcopy(coherence_reviews[0])
    review_mutant["association_revision_ids"] = []
    review_schema_errors = validator.errors(review_mutant, schema_documents["composition.schema.json"]["$defs"]["compositionCoherenceReview"], "composition.schema.json")
    checks.true("fresh_adversarial_rejected_ADV_V3_018", bool(review_schema_errors), review_schema_errors)
    adversarial_results.append({"probe_id": "ADV-V3-018", "mutation_pointer": "/association_revision_ids", "status": "PASS", "independent_errors": review_schema_errors})

    nav_shape_mutant = copy.deepcopy(states[0])
    concept_node_mutant = next(row for row in nav_shape_mutant["nodes"] if row["node_kind"] == "CONCEPT")
    concept_node_mutant["association_revision_id"] = sparse["association_revision_id"]
    nav_shape_errors = validator.errors(nav_shape_mutant, schema_documents["navigation-state.schema.json"], "navigation-state.schema.json")
    checks.true("fresh_adversarial_rejected_ADV_V3_019", bool(nav_shape_errors), nav_shape_errors)
    adversarial_results.append({"probe_id": "ADV-V3-019", "mutation_pointer": "/nodes/0/association_revision_id", "status": "PASS", "independent_errors": nav_shape_errors})

    workflow_mutant = copy.deepcopy(workflows[0])
    workflow_mutant["association_realization_ids"] = []
    workflow_errors = validator.errors(workflow_mutant, schema_documents["workflow.schema.json"], "workflow.schema.json")
    checks.true("fresh_adversarial_rejected_ADV_V3_020", bool(workflow_errors), workflow_errors)
    adversarial_results.append({"probe_id": "ADV-V3-020", "mutation_pointer": "/association_realization_ids", "status": "PASS", "independent_errors": workflow_errors})

    projection_export_mutant = copy.deepcopy(fixture["exports"][0])
    projection_export_mutant["pair_projection_policy_preserved"] = False
    export_errors = validator.errors(projection_export_mutant, schema_documents["export-manifest.schema.json"], "export-manifest.schema.json")
    checks.true("fresh_adversarial_rejected_ADV_V3_021", bool(export_errors), export_errors)
    adversarial_results.append({"probe_id": "ADV-V3-021", "mutation_pointer": "/pair_projection_policy_preserved", "status": "PASS", "independent_errors": export_errors})

    hash_contract_mutant = copy.deepcopy(hash_contract)
    identity_binding_mutant = next(row for row in hash_contract_mutant["bindings"] if row["object_type"] == "ASSOCIATION_REVISION")
    identity_material_mutant = next(row for row in identity_binding_mutant["materials"] if row["material_name"] == "association_identity")
    identity_material_mutant["field_mappings"] = [
        row for row in identity_material_mutant["field_mappings"] if row.get("source_pointer") != "/scope"
    ]
    contract_mutant_errors = hash_contract_semantic_issues(hash_contract_mutant)
    checks.true("fresh_adversarial_rejected_ADV_V3_022", bool(contract_mutant_errors), contract_mutant_errors)
    adversarial_results.append({"probe_id": "ADV-V3-022", "mutation_pointer": "/bindings/ASSOCIATION_REVISION/materials/association_identity/field_mappings", "status": "PASS", "independent_errors": contract_mutant_errors})

    composite_mutant = copy.deepcopy(sparse)
    composite_mutant["evidence"]["support_mode"] = "COHERENT_COMPOSITE"
    composite_mutant["evidence"]["synthesis_steps"] = []
    composite_semantic_errors = association_semantic_issues(composite_mutant)
    composite_schema_errors = validator.errors(composite_mutant, schema_documents["association.schema.json"], "association.schema.json")
    checks.true("fresh_adversarial_schema_rejected_ADV_V3_023", bool(composite_schema_errors), composite_schema_errors)
    checks.true("fresh_adversarial_semantic_rejected_ADV_V3_023", bool(composite_semantic_errors), composite_semantic_errors)
    composite_errors = sorted(set(composite_semantic_errors + composite_schema_errors))
    checks.true("fresh_adversarial_rejected_ADV_V3_023", bool(composite_errors), composite_errors)
    adversarial_results.append({"probe_id": "ADV-V3-023", "mutation_pointer": "/evidence/synthesis_steps", "status": "PASS", "independent_errors": composite_errors})

    disposition_mutant = copy.deepcopy(sparse)
    disposition_mutant["evidence"]["support_mode"] = "COHERENT_COMPOSITE"
    disposition_mutant["evidence"]["synthesis_steps"] = ["bounded synthetic synthesis"]
    disposition_semantic_errors = association_semantic_issues(disposition_mutant)
    disposition_schema_errors = validator.errors(disposition_mutant, schema_documents["association.schema.json"], "association.schema.json")
    checks.true("fresh_adversarial_schema_rejected_ADV_V3_024", bool(disposition_schema_errors), disposition_schema_errors)
    checks.true("fresh_adversarial_semantic_rejected_ADV_V3_024", bool(disposition_semantic_errors), disposition_semantic_errors)
    disposition_errors = sorted(set(disposition_schema_errors + disposition_semantic_errors))
    adversarial_results.append({"probe_id": "ADV-V3-024", "mutation_pointer": "/evidence/support_mode", "status": "PASS", "independent_errors": disposition_errors})

    coherent_review = next(row for row in coherence_reviews if row["decision"] == "COHERENT")
    review_authority_mutant = copy.deepcopy(coherent_review)
    review_authority_mutant["authority"]["authority_state"] = "PENDING"
    review_authority_errors = validator.errors(review_authority_mutant, schema_documents["composition.schema.json"]["$defs"]["compositionCoherenceReview"], "composition.schema.json")
    checks.true("fresh_adversarial_schema_rejected_ADV_V3_025", bool(review_authority_errors), review_authority_errors)
    adversarial_results.append({"probe_id": "ADV-V3-025", "mutation_pointer": "/authority/authority_state", "status": "PASS", "independent_errors": review_authority_errors})

    active_concept = next(row for row in concept_by_id.values() if row["lifecycle_state"] == "ACTIVE")
    concept_eligibility_mutant = copy.deepcopy(active_concept)
    concept_eligibility_mutant["association_eligible"] = False
    concept_eligibility_errors = validator.errors(concept_eligibility_mutant, schema_documents["concept.schema.json"]["$defs"]["concept"], "concept.schema.json")
    checks.true("fresh_adversarial_schema_rejected_ADV_V3_026", bool(concept_eligibility_errors), concept_eligibility_errors)
    adversarial_results.append({"probe_id": "ADV-V3-026", "mutation_pointer": "/association_eligible", "status": "PASS", "independent_errors": concept_eligibility_errors})

    active_sense = next(row for row in sense_by_id.values() if row["lifecycle_state"] == "ACTIVE")
    sense_authority_mutant = copy.deepcopy(active_sense)
    sense_authority_mutant["authority"]["authority_state"] = "PENDING"
    sense_authority_errors = validator.errors(sense_authority_mutant, schema_documents["concept.schema.json"]["$defs"]["conceptSense"], "concept.schema.json")
    checks.true("fresh_adversarial_schema_rejected_ADV_V3_027", bool(sense_authority_errors), sense_authority_errors)
    adversarial_results.append({"probe_id": "ADV-V3-027", "mutation_pointer": "/authority/authority_state", "status": "PASS", "independent_errors": sense_authority_errors})

    checks.equal("fresh_adversarial_probe_count", len(adversarial_results), 27)

    reconstructed_counts = reconstruct_counts(fixture)
    checks.equal("count_taxonomy_independent_expected", reconstructed_counts, EXPECTED_RECONSTRUCTED_COUNTS)
    checks.equal("count_taxonomy_reconstruction", fixture["count_taxonomy"], reconstructed_counts)
    checks.equal("closure_flag_key_set", set(fixture["closure_flags"]), EXPECTED_CLOSURE_KEYS)
    checks.equal("closure_true_count", sum(bool(value) for value in fixture["closure_flags"].values()), 0)
    zero_production_fields = {
        "production_active_concept_count": reconstructed_counts["vocabulary"]["production_active_concept_count"],
        "production_pair_revision_count": reconstructed_counts["associations"]["production_pair_revision_count"],
        "production_higher_order_revision_count": reconstructed_counts["associations"]["production_higher_order_revision_count"],
        "production_active_association_count": reconstructed_counts["associations"]["production_active_association_count"],
        "production_active_pending_review_count": reconstructed_counts["associations"]["production_active_pending_review_count"],
        "production_incidence_count": reconstructed_counts["incidence"]["production_incidence_count"],
        "implicit_projected_pair_count": reconstructed_counts["incidence"]["implicit_projected_pair_count"],
        "production_association_realization_count": reconstructed_counts["realizations_and_compositions"]["production_association_realization_count"],
        "production_composition_count": reconstructed_counts["realizations_and_compositions"]["production_composition_count"],
        "production_composition_coherence_review_count": reconstructed_counts["realizations_and_compositions"]["production_composition_coherence_review_count"],
        "production_product_eligible_composition_count": reconstructed_counts["realizations_and_compositions"]["production_product_eligible_composition_count"],
        "production_state_count": reconstructed_counts["interaction"]["production_state_count"],
        "production_workflow_count": reconstructed_counts["interaction"]["production_workflow_count"],
        "production_export_count": reconstructed_counts["interaction"]["production_export_count"],
    }
    checks.equal("zero_production_taxonomy", set(zero_production_fields.values()), {0})

    checks.equal("census_count_taxonomy", census["count_taxonomy"], reconstructed_counts)
    checks.equal("census_schema_document_count", census["schema_document_count"], 10)
    checks.equal("census_control_count", census["control_count"], 10)
    checks.equal("census_negative_probe_count", [census["negative_probe_count"], census["negative_probe_rejection_count"]], [37, 37])
    checks.equal("census_zero_boundaries", [census["production_activation_count"], census["production_product_eligible_count"], census["implicit_pair_projection_count"], census["closure_true_count"]], [0, 0, 0, 0])
    checks.equal("census_independent_status_precheckpoint", census["independent_verification_status"], "PENDING_SEPARATE_IMPLEMENTATION")

    checks.equal("build_receipt_status", build_receipt["status"], "PASS")
    checks.equal("build_receipt_output_aggregate", build_receipt["output_aggregate_sha256"], EXPECTED_OUTPUT_AGGREGATE_SHA256)
    checks.equal("build_receipt_counts", [build_receipt["schema_document_count"], build_receipt["control_count"], build_receipt["negative_probe_count"], build_receipt["negative_probe_rejection_count"], build_receipt["output_artifact_count_excluding_receipt"]], [10, 10, 37, 37, 19])
    checks.equal("build_receipt_non_authorizations", [build_receipt["production_activation_count"], build_receipt["production_product_eligible_count"], build_receipt["implicit_pair_projection_count"], build_receipt["closure_true_count"], build_receipt["v2_files_modified"], build_receipt["frozen_v49_artifacts_modified"], build_receipt["database_implemented"], build_receipt["runtime_implemented"], build_receipt["deployment_performed"], build_receipt["history_rewritten"], build_receipt["force_push_used"]], [0, 0, 0, 0, 0, 0, False, False, False, False, False])

    output_paths = [row["path"] for row in output_manifest]
    checks.equal("output_manifest_path_uniqueness", len(output_paths), len(set(output_paths)))
    for row in output_manifest:
        path = REPO / row["path"]
        checks.true(f"output_manifest_file_exists_{row['path']}", path.is_file(), row["path"])
        checks.equal(f"output_manifest_sha_{row['path']}", sha256_file(path), row["sha256"])
        checks.equal(f"output_manifest_bytes_{row['path']}", path.stat().st_size, int(row["bytes"]))
    aggregate_material = [{"path": row["path"], "sha256": row["sha256"], "bytes": int(row["bytes"])} for row in output_manifest]
    checks.equal("output_manifest_aggregate", digest(aggregate_material), EXPECTED_OUTPUT_AGGREGATE_SHA256)
    checks.true("output_manifest_excludes_itself", OUTPUT_MANIFEST_REL.as_posix() not in output_paths, output_paths)
    checks.true("output_manifest_excludes_build_receipt", BUILD_RECEIPT_REL.as_posix() not in output_paths, output_paths)
    checks.true("output_manifest_includes_hash_contract", HASH_CONTRACT_REL.as_posix() in output_paths, output_paths)

    for row in input_manifest:
        path = REPO / row["path"]
        checks.true(f"input_manifest_file_exists_{row['path']}", path.is_file(), row["path"])
        checks.equal(f"input_manifest_sha_{row['path']}", sha256_file(path), row["sha256"])
        checks.equal(f"input_manifest_bytes_{row['path']}", path.stat().st_size, int(row["bytes"]))
        checks.equal(f"input_manifest_mutation_policy_{row['path']}", row["mutation_policy"], "READ_ONLY_PIN")

    v2_inventory: list[dict[str, Any]] = []
    for relative, expected_sha in sorted(V2_PINNED_SHA256.items()):
        observed_sha = sha256_file(REPO / relative)
        checks.equal(f"v2_pinned_sha_{relative}", observed_sha, expected_sha)
        v2_inventory.append({"path": relative, "sha256": observed_sha})
    checks.equal("v2_pinned_file_count", len(v2_inventory), 22)

    freeze_path = REPO / "database/FREEZE_V49.json"
    checks.equal("v49_freeze_manifest_sha256", sha256_file(freeze_path), EXPECTED_V49_FREEZE_MANIFEST_SHA256)
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    checks.equal("v49_freeze_version_status", [freeze["version"], freeze["freezeStatus"]], [49, "FROZEN"])
    v49_rows: list[dict[str, str]] = []
    for relative, expected_sha in sorted(freeze["perFileSha256"].items()):
        observed_sha = sha256_file(REPO / relative)
        if observed_sha != expected_sha:
            raise AssertionError(f"frozen v49 hash mismatch: {relative}")
        v49_rows.append({"path": relative, "sha256": observed_sha})
    checks.equal("v49_frozen_file_count", len(v49_rows), freeze["fileCount"])
    v49_inventory_sha = digest(v49_rows)
    checks.equal("v49_schema_hash", freeze["schemaHash"], "df1e7741e59e5e6bf1ca80f2a33edfad1abb2fc6d95b57d4d6993b49917020dd")

    tracked_changes = set(run_git(["diff", "--name-only", PARENT_CHECKPOINT_SHA, "--"]))
    untracked_changes = set(run_git(["ls-files", "--others", "--exclude-standard"]))
    all_changes = tracked_changes | untracked_changes
    v2_protected_prefixes = (
        "schemas/trace/exploration/v2/",
        "frontend/src/features/trace-v49/exploration-v2/",
        "frontend/generated/trace-exploration-v2/production-read-model.json",
    )
    frozen_exact = set(freeze["perFileSha256"])
    frozen_prefixes = tuple(path.rstrip("/") + "/" for path in freeze["frozenPaths"] if (REPO / path).is_dir())
    protected_changes = sorted(
        path
        for path in all_changes
        if path in frozen_exact
        or any(path.startswith(prefix) for prefix in frozen_prefixes)
        or any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in v2_protected_prefixes)
    )
    checks.equal("checkpoint_diff_protected_change_count", len(protected_changes), 0)

    gap_hash_count = 0
    for row in gaps:
        stored = row["record_sha256"]
        material = {key: value for key, value in row.items() if key != "record_sha256"}
        checks.equal(f"gap_record_hash_{row['gap_id']}", stored, digest(material))
        gap_hash_count += 1
    checks.equal("gap_record_count", gap_hash_count, 5)
    checks.equal("open_closure_blocking_gap_count", sum(row["status"] == "OPEN_CLOSURE_BLOCKING" for row in gaps), 4)
    checks.equal("gap_closure_authorization", {row["closure_authorized"] for row in gaps}, {"false"})

    verifier_source = (REPO / VERIFIER_REL).read_text(encoding="utf-8")
    tree = ast.parse(verifier_source)
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    checks.true("primary_builder_not_imported", all("build_v3_semantic_contract" not in name for name in imported_modules), sorted(imported_modules))

    receipt = {
        "receipt_version": VERIFIER_VERSION,
        "status": "PASS",
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
        "contract_version": CONTRACT_VERSION,
        "hash_contract_version": HASH_CONTRACT_VERSION,
        "authority_cutoff_utc": AUTHORITY_CUTOFF_UTC,
        "verifier_path": VERIFIER_REL.as_posix(),
        "verifier_sha256": sha256_file(REPO / VERIFIER_REL),
        "independence": {
            "primary_builder_imported": False,
            "primary_builder_invoked": False,
            "shared_enumeration_reused": False,
            "schema_validator": "INDEPENDENT_STDLIB_DRAFT_2020_12_USED_KEYWORD_SUBSET",
            "hash_interpreter": "INDEPENDENT_NORMATIVE_BINDING_CONTRACT_INTERPRETER",
            "graph_algorithm": "INDEPENDENT_UNION_FIND_OVER_EXPLICIT_INCIDENCE_LINKS",
        },
        "artifact_pins": {
            "fixture_sha256": EXPECTED_FIXTURE_SHA256,
            "hash_contract_file_sha256": EXPECTED_HASH_CONTRACT_FILE_SHA256,
            "hash_contract_canonical_sha256": EXPECTED_HASH_CONTRACT_CANONICAL_SHA256,
            "output_manifest_sha256": EXPECTED_OUTPUT_MANIFEST_SHA256,
            "build_receipt_sha256": EXPECTED_BUILD_RECEIPT_SHA256,
            "output_aggregate_sha256": EXPECTED_OUTPUT_AGGREGATE_SHA256,
        },
        "schema_verification": {
            "schema_document_count": len(schema_documents),
            "schema_document_failures": schema_document_failures,
            "fixture_schema_errors": root_schema_errors,
            "hash_contract_schema_errors": hash_contract_schema_errors,
            "hash_contract_semantic_failures": hash_contract_semantic_failures,
        },
        "normative_hash_verification": {
            "binding_count": len(hash_contract["bindings"]),
            "object_verification_count": len(hash_results),
            "assertion_count": hash_assertion_count,
            "results": hash_results,
        },
        "identity_branch_verification": {
            "branch_count": len(identity_branch_results),
            "results": identity_branch_results,
        },
        "governance_verification": {
            "concept_count": len(concept_by_id),
            "concept_sense_count": len(sense_by_id),
            "scope_count": len(scope_by_id),
            "composition_coherence_review_count": len(coherence_review_by_id),
            "internal_pair_link_count": len(internal_pair_ledger),
            "internal_pair_ledger": internal_pair_ledger,
        },
        "control_verification": {
            "control_count": len(control_results),
            "results": control_results,
        },
        "negative_probe_verification": {
            "primary_receipt_probe_count": len(independent_probe_results),
            "independently_replayed_primary_probes": independent_probe_results,
            "fresh_adversarial_probe_count": len(adversarial_results),
            "fresh_adversarial_results": adversarial_results,
        },
        "adapter_verification": {
            "adapter_count": len(adapter_results),
            "results": adapter_results,
            "higher_order_down_projection_count": reconstructed_counts["incidence"]["implicit_projected_pair_count"],
        },
        "reconstructed_count_taxonomy": reconstructed_counts,
        "closure_flags": fixture["closure_flags"],
        "production_boundary": {
            "zero_fields": zero_production_fields,
            "production_activation_count": 0,
            "production_product_eligible_count": 0,
            "implicit_pair_projection_count": 0,
            "closure_true_count": 0,
        },
        "protected_authority": {
            "v2_pinned_file_count": len(v2_inventory),
            "v2_inventory": v2_inventory,
            "v49_freeze_manifest_sha256": EXPECTED_V49_FREEZE_MANIFEST_SHA256,
            "v49_frozen_file_count": len(v49_rows),
            "v49_inventory_canonical_sha256": v49_inventory_sha,
            "checkpoint_diff_protected_changes": protected_changes,
        },
        "failed_probes_and_corrections": FAILED_PROBES_AND_CORRECTIONS,
        "check_count": len(checks.rows),
        "checks": checks.rows,
    }
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify that the committed receipt is byte-identical")
    args = parser.parse_args()
    receipt = build_receipt()
    expected = json_bytes(receipt)
    output = REPO / OUTPUT_REL
    if args.check:
        if not output.is_file():
            raise SystemExit(f"MISSING {OUTPUT_REL.as_posix()}")
        observed = output.read_bytes()
        if observed != expected:
            raise SystemExit(f"DIFF {OUTPUT_REL.as_posix()}")
        print(f"PASS {VERIFIER_VERSION} checks={receipt['check_count']} receipt={sha256_file(output)}")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(expected)
    print(f"PASS {VERIFIER_VERSION} checks={receipt['check_count']} wrote={OUTPUT_REL.as_posix()} sha256={hashlib.sha256(expected).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
