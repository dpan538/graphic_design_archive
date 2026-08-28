#!/usr/bin/env python3
"""Independently verify the additive TRACE Exploration v3 runtime read model.

This verifier parses only committed governed inputs and generated runtime
artifacts.  It does not import, invoke, or reuse the primary runtime generator.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable


REPO = Path(__file__).resolve().parents[2]
RAW_REL = Path("docs/audits/v49-exploration-higher-order-association-closure-round16b/raw")
RAW = REPO / RAW_REL
GENERATED_REL = Path("frontend/generated/trace-exploration-v3")
GENERATED = REPO / GENERATED_REL

FIXTURE_REL = RAW_REL / "v3-semantic-contract-fixtures-v1.json"
CENSUS_REL = RAW_REL / "v3-semantic-contract-census-v1.json"
HASH_CONTRACT_REL = RAW_REL / "v3-semantic-hash-binding-contract-v1.json"
ROUND16A_REL = RAW_REL / "round16a-global-reconciliation-census-v1.json"
READ_MODEL_REL = GENERATED_REL / "read-model.json"
MANIFEST_REL = GENERATED_REL / "manifest.json"
CHECKSUMS_REL = GENERATED_REL / "CHECKSUMS.sha256"
RECEIPT_REL = RAW_REL / "v3-runtime-independent-verification-v1.json"
VERIFIER_REL = Path("scripts/trace_round16b/verify_v3_runtime_independent.py")

SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
SEMANTIC_PARENT_SHA = "e5ddbc443c4a0a28004034cba439340ecdeb9a75"
CONTRACT_VERSION = "trace-exploration-v3-semantic-contract-1.0.0"
READ_MODEL_VERSION = "trace-exploration-runtime-read-model-v3-1.0.0"
MANIFEST_VERSION = "trace-exploration-runtime-manifest-v3-1.0.0"
VERIFIER_VERSION = "trace-round16b-v3-runtime-independent-verifier-v4"
API_VERSION = "trace-exploration/v3"
SEMANTIC_NAMESPACE = "trace/exploration/v3"
CANONICAL_SERIALIZATION = "recursive-key-sort;array-order-preserved;json-minified;final-lf;utf8"
EXPECTED_READ_MODEL_SHA256 = "f1ae8a35895b27c15fb3d9b42828b8611633ee8ee7e2cbc825772b590304351b"
EXPECTED_MANIFEST_SHA256 = "2ee550028cb60749bee7efa456ed21ea4f0c6170bb5c68d8888017fc948fdd2c"
EXPECTED_CHECKSUMS_SHA256 = "002d13c9175354054ee550b4d55d275ea2fad1c10693991bd726897aa50e8173"

SURFACE_COLLECTIONS = {
    "scopes",
    "concepts",
    "concept_senses",
    "associations",
    "incidences",
    "association_realizations",
    "composition_coherence_reviews",
    "compositions",
    "navigation_states",
    "workflows",
    "exports",
    "transitions",
}

NAVIGATION_STATE_KEYS = {
    "bipartite_alternation_valid", "composition_revision_id", "fact_boundary",
    "focus_navigation_node_id", "nodes", "path", "presentation",
    "presentation_sha256", "realm", "semantic_sha256", "state_id",
}
NAVIGATION_NODE_KEYS = {
    "association_revision_id", "concept_id", "navigation_node_id", "node_kind",
}
NAVIGATION_PATH_STEP_KEYS = {
    "from_navigation_node_id", "incidence_id", "to_navigation_node_id",
}
WORKFLOW_KEYS = {
    "association_realization_ids", "association_revision_ids", "fact_boundary",
    "initial_state_id", "reachable", "realm", "semantic_sha256", "state_ids",
    "transition_ids", "transition_kind", "workflow_id",
}
FACT_BOUNDARY_KEYS = {"data_class", "production_fact", "synthetic_control"}
EXPORT_KEYS = {
    "association_realization_ids", "association_revision_ids",
    "composition_revision_id", "export_id", "fact_boundary",
    "pair_projection_policy_preserved", "presentation", "presentation_sha256",
    "projection_preservation_records", "realm", "semantic_sha256", "state_id",
    "workflow_id",
}
PROJECTION_PRESERVATION_KEYS = {
    "association_realization_id", "association_revision_id",
    "pair_projection_policy", "realization_kind",
}
TRANSITION_KEYS = {
    "association_realization_id", "association_revision_id", "fact_boundary",
    "from_state_id", "incidence_id", "realm", "semantic_sha256", "state_mutated",
    "to_state_id", "transition_id", "transition_kind",
}

COLLECTION_IDENTITIES = (
    ("association-realizations", "association_realization_id"),
    ("associations", "association_id"),
    ("composition-coherence-reviews", "composition_coherence_review_id"),
    ("compositions", "composition_id"),
    ("concept-senses", "sense_id"),
    ("concepts", "concept_id"),
    ("exports", "export_id"),
    ("incidences", "incidence_id"),
    ("navigation-states", "state_id"),
    ("scopes", "scope_id"),
    ("transitions", "transition_id"),
    ("workflows", "workflow_id"),
)
EXPECTED_READ_PATHS = [
    "/capabilities",
    *(
        path
        for collection, identity in COLLECTION_IDENTITIES
        for path in (f"/{collection}", f"/{collection}/{{{identity}}}")
    ),
    *(
        path
        for collection, identity in COLLECTION_IDENTITIES
        for path in (
            f"/controls/{collection}",
            f"/controls/{collection}/{{{identity}}}",
        )
    ),
    "/baseline/reconciliation",
]

EXPECTED_CLOSURE = {
    "pair_association_closure": False,
    "higher_order_association_closure": False,
    "global_composition_coherence_closure": False,
    "product_association_reachability_closure": False,
    "computational_space_closure": False,
    "function3_closure": False,
}

EXPECTED_ROUND16A_DISTRIBUTIONS = {
    "ROUND16A_ASSOCIATION_SUBGRAPH": {"CORRECTED": 11, "INQUIRY": 18, "REJECTED": 8, "RETAINED": 21},
    "ROUND16A_CATEGORY_ENTRY": {"CORRECTED": 27, "INQUIRY": 15, "REJECTED": 18, "RETAINED": 21},
    "ROUND16A_EXPORT": {"CORRECTED": 3888, "INQUIRY": 4368, "REJECTED": 2592, "RETAINED": 672},
    "ROUND16A_LEGACY_RECONCILIATION": {"INQUIRY": 2, "REJECTED": 2, "RETAINED": 7},
    "ROUND16A_PRODUCTION_COMPOSITION": {"CORRECTED": 81, "INQUIRY": 51, "REJECTED": 54, "RETAINED": 42},
    "ROUND16A_SEED_VARIANT": {"CORRECTED": 81, "INQUIRY": 51, "REJECTED": 54, "RETAINED": 42},
    "ROUND16A_STATE": {"CORRECTED": 1944, "INQUIRY": 2184, "REJECTED": 1296, "RETAINED": 336},
    "ROUND16A_TOPOLOGY_COMPOSITION": {"CORRECTED": 27, "INQUIRY": 15, "REJECTED": 18, "RETAINED": 21},
    "ROUND16A_WORKFLOW": {"CORRECTED": 1944, "INQUIRY": 2184, "REJECTED": 1296, "RETAINED": 336},
}
EXPECTED_ROUND16A_TOTAL = {"CORRECTED": 203639, "INQUIRY": 290372, "REJECTED": 270370, "RETAINED": 9290}
EXPECTED_TRANSITION_OUTCOMES = {"CORRECTED": 195636, "INQUIRY": 281484, "REJECTED": 265032, "RETAINED": 7792}
EXPECTED_FAMILY_TOTALS = {
    "ROUND16A_ASSOCIATION_SUBGRAPH": 58,
    "ROUND16A_CATEGORY_ENTRY": 81,
    "ROUND16A_EXPORT": 11520,
    "ROUND16A_LEGACY_RECONCILIATION": 11,
    "ROUND16A_PRODUCTION_COMPOSITION": 228,
    "ROUND16A_SEED_VARIANT": 228,
    "ROUND16A_STATE": 5760,
    "ROUND16A_TOPOLOGY_COMPOSITION": 81,
    "ROUND16A_WORKFLOW": 5760,
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

SCOPE_IDENTITY_KEYS = (
    "scope_id",
    "historical_case_ids",
    "time_bounds",
    "geographies",
    "institutions",
    "actors",
    "mechanisms",
)
SCOPE_SET_KEYS = (
    "historical_case_ids",
    "geographies",
    "institutions",
    "actors",
    "mechanisms",
)
ASSOCIATION_SEMANTIC_FIELDS = (
    "association_kind", "realm", "semantic_version", "arity", "order_semantics",
    "roles_meaningful", "identity_material_sha256", "scope", "participants", "evidence",
    "review", "activation", "uncertainty", "lifecycle_state", "pair_projection_policy",
    "internal_pair_association_ids", "internal_pair_links", "product_eligible", "product_path",
    "product_eligibility_disposition", "product_ineligibility_reason",
)
COMPOSITION_SEMANTIC_FIELDS = (
    "realm", "association_realizations", "composition_node_ids", "topology_family",
    "renderability", "global_coherence_review_id", "association_trace_complete",
    "product_eligible", "product_path", "product_eligibility_disposition",
    "product_ineligibility_reason",
)


class VerificationError(AssertionError):
    """A stable, machine-readable independent-verification failure."""


def enforce(condition: bool, code: str) -> None:
    if not condition:
        raise VerificationError(code)


def require_dict(value: Any, code: str) -> dict[str, Any]:
    enforce(isinstance(value, dict), code)
    return value


def require_list(value: Any, code: str) -> list[Any]:
    enforce(isinstance(value, list), code)
    return value


def require_text(value: Any, code: str) -> str:
    enforce(isinstance(value, str) and bool(value), code)
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def semantic_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return sha256_bytes(payload.encode("utf-8"))


def binding_material(
    contract: dict[str, Any],
    object_type: str,
    material_name: str,
    record: dict[str, Any],
) -> Any:
    """Reconstruct one normative material from the separately frozen contract."""

    binding = next(
        (
            row for row in require_list(contract.get("bindings"), "HASH_CONTRACT_BINDINGS")
            if row.get("object_type") == object_type
        ),
        None,
    )
    enforce(binding is not None, f"HASH_BINDING_OBJECT_TYPE:{object_type}")
    material = next(
        (
            row for row in require_list(binding.get("materials"), f"HASH_MATERIALS:{object_type}")
            if row.get("material_name") == material_name
        ),
        None,
    )
    enforce(material is not None, f"HASH_MATERIAL_NAME:{object_type}:{material_name}")
    source_fields = require_list(
        material.get("source_fields"), f"HASH_MATERIAL_FIELDS:{object_type}:{material_name}"
    )
    if material.get("recipe") == "DIRECT_FIELD_VALUE":
        enforce(len(source_fields) == 1, f"HASH_MATERIAL_VALUE_WIDTH:{object_type}:{material_name}")
        return copy.deepcopy(record[source_fields[0]])
    enforce(
        material.get("recipe") == "DIRECT_FIELD_OBJECT",
        f"HASH_MATERIAL_RECIPE:{object_type}:{material_name}",
    )
    output_keys = require_list(
        material.get("output_keys"), f"HASH_MATERIAL_OUTPUT_KEYS:{object_type}:{material_name}"
    )
    enforce(output_keys == source_fields, f"HASH_MATERIAL_DIRECT_KEY_PARITY:{object_type}:{material_name}")
    return {key: copy.deepcopy(record[key]) for key in output_keys}


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
    ).encode("utf-8")


def receipt_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as error:
        raise VerificationError(f"INPUT_UNREADABLE:{path}:{error}") from error
    return require_dict(value, f"INPUT_NOT_OBJECT:{path}"), raw


class Checks:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def equal(self, check_id: str, observed: Any, expected: Any) -> None:
        if observed != expected:
            raise VerificationError(f"{check_id}:EXPECTED={expected!r}:OBSERVED={observed!r}")
        self.rows.append({"check_id": check_id, "status": "PASS"})

    def true(self, check_id: str, condition: bool) -> None:
        self.equal(check_id, bool(condition), True)


def canonical_participant_identity(record: dict[str, Any]) -> list[dict[str, Any]]:
    projected = [
        {
            "concept_id": item["concept_id"],
            "sense_id": item["sense_id"],
            "ordinal": item["ordinal"],
            "role_id": item["role_id"],
        }
        for item in record["participants"]
    ]
    if record["order_semantics"] == "ORDERED":
        return projected
    if record["roles_meaningful"]:
        return sorted(projected, key=lambda row: (row["role_id"] or "", row["sense_id"], row["concept_id"]))
    return sorted(projected, key=lambda row: (row["sense_id"], row["concept_id"]))


def scope_identity(scope: dict[str, Any]) -> dict[str, Any]:
    result = {key: copy.deepcopy(scope[key]) for key in SCOPE_IDENTITY_KEYS}
    for key in SCOPE_SET_KEYS:
        result[key] = sorted(result[key])
    return result


def association_semantic(record: dict[str, Any]) -> dict[str, Any]:
    return {key: copy.deepcopy(record[key]) for key in ASSOCIATION_SEMANTIC_FIELDS}


def graph_component_count(record: dict[str, Any]) -> int:
    incidence_ids = [item["incidence_id"] for item in record["participants"]]
    parent = {item: item for item in incidence_ids}

    def find(value: str) -> str:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    for link in record["internal_pair_links"]:
        left, right = link["participant_incidence_ids"]
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root
    return len({find(value) for value in incidence_ids})


def product_tuple_valid(record: dict[str, Any]) -> bool:
    if record["product_eligible"] is True:
        return (
            record["realm"] == "PRODUCTION"
            and isinstance(record["product_path"], str)
            and bool(record["product_path"])
            and record["product_eligibility_disposition"] == "ELIGIBLE"
            and record["product_ineligibility_reason"] is None
        )
    return (
        record["product_path"] is None
        and record["product_eligibility_disposition"]
        in {"INELIGIBLE", "DEFERRED", "NOT_APPLICABLE_SYNTHETIC"}
        and isinstance(record["product_ineligibility_reason"], str)
        and bool(record["product_ineligibility_reason"])
    )


def active_association_valid(record: dict[str, Any]) -> bool:
    review = record["review"]
    evidence = record["evidence"]
    activation = record["activation"]
    uncertainty = record["uncertainty"]
    expected = {
        ("PAIR", "DIRECT_PAIR"): "DIRECT_PAIRWISE_SUPPORT",
        ("HIGHER_ORDER", "DIRECT_GROUP"): "DIRECT_HIGHER_ORDER_SUPPORT",
        ("HIGHER_ORDER", "COHERENT_COMPOSITE"): "COHERENT_COMPOSITE_SUPPORT",
        ("HIGHER_ORDER", "MIXED"): "MIXED_DIRECT_AND_COMPOSITE_SUPPORT",
    }.get((record["association_kind"], evidence["support_mode"]))
    synthesis_valid = (
        evidence["support_mode"] in {"DIRECT_PAIR", "DIRECT_GROUP"}
        and not evidence["synthesis_steps"]
    ) or (
        evidence["support_mode"] in {"COHERENT_COMPOSITE", "MIXED"}
        and bool(evidence["synthesis_steps"])
    )
    return (
        review["review_state"] == "FINAL"
        and review["authority_state"] == "FINAL"
        and review["disposition"] == expected
        and review["global_coherence"] == "PASS"
        and review["bounded_senses_compatible"] is True
        and review["case_scope_compatible"] is True
        and review["roles_and_topology_supported"] is True
        and review["unsupported_bridge_count"] == 0
        and evidence["same_configuration"] is True
        and evidence["evidence_complete"] is True
        and evidence["rights_cleared_for_governed_use"] is True
        and evidence["conflicts_resolved"] is True
        and not evidence["negative_or_conflicting_evidence"]
        and bool(evidence["evidence_item_ids"])
        and bool(evidence["locator_ids"])
        and synthesis_valid
        and activation["requested_state"] == "ACTIVE"
        and activation["decision"] == "ALLOW"
        and activation["all_gates_pass"] is True
        and all(
            activation[name] is True
            for name in (
                "evidence_gate", "final_review_gate", "authority_gate", "coherence_gate",
                "rights_gate", "conflict_gate", "bounded_scope_gate", "synthesis_gate",
                "product_policy_gate",
            )
        )
        and uncertainty["status"] == "RESOLVED_BOUNDED"
        and uncertainty["activation_policy"] == "ALLOWED_BOUNDED"
        and uncertainty["reviewed_in_review_id"] == review["review_id"]
    )


def reconstruct_count_taxonomy(fixture: dict[str, Any]) -> dict[str, Any]:
    associations = fixture["associations"]
    concepts = fixture["concepts"]
    senses = fixture["concept_senses"]
    compositions = fixture["compositions"]
    reviews = fixture["composition_coherence_reviews"]
    realizations = [
        realization
        for composition in compositions
        for realization in composition["association_realizations"]
    ]
    return {
        "vocabulary": {
            "synthetic_scope_count": sum(row.get("scope_id", "").startswith("scope:") for row in fixture["scopes"]),
            "synthetic_distinct_concept_count": len({
                participant["concept_id"]
                for row in associations if row["realm"] == "SYNTHETIC_CONTROL"
                for participant in row["participants"]
            }),
            "synthetic_concept_record_count": sum(row["realm"] == "SYNTHETIC_CONTROL" for row in concepts),
            "synthetic_active_concept_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" and row["lifecycle_state"] == "ACTIVE"
                for row in concepts
            ),
            "synthetic_concept_sense_record_count": sum(row["realm"] == "SYNTHETIC_CONTROL" for row in senses),
            "synthetic_active_concept_sense_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" and row["lifecycle_state"] == "ACTIVE"
                for row in senses
            ),
            "production_active_concept_count": sum(
                row["realm"] == "PRODUCTION" and row["lifecycle_state"] == "ACTIVE"
                for row in concepts
            ),
        },
        "associations": {
            "synthetic_pair_revision_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" and row["association_kind"] == "PAIR"
                for row in associations
            ),
            "synthetic_higher_order_revision_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" and row["association_kind"] == "HIGHER_ORDER"
                for row in associations
            ),
            "synthetic_active_pair_revision_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" and row["association_kind"] == "PAIR"
                and row["lifecycle_state"] == "ACTIVE" for row in associations
            ),
            "synthetic_active_higher_order_revision_count": sum(
                row["realm"] == "SYNTHETIC_CONTROL" and row["association_kind"] == "HIGHER_ORDER"
                and row["lifecycle_state"] == "ACTIVE" for row in associations
            ),
            "production_pair_revision_count": sum(
                row["realm"] == "PRODUCTION" and row["association_kind"] == "PAIR"
                for row in associations
            ),
            "production_higher_order_revision_count": sum(
                row["realm"] == "PRODUCTION" and row["association_kind"] == "HIGHER_ORDER"
                for row in associations
            ),
            "production_active_association_count": sum(
                row["realm"] == "PRODUCTION" and row["lifecycle_state"] == "ACTIVE"
                for row in associations
            ),
            "production_active_pending_review_count": sum(
                row["realm"] == "PRODUCTION" and row["lifecycle_state"] == "ACTIVE"
                and row["review"]["review_state"] != "FINAL" for row in associations
            ),
        },
        "incidence": {
            "synthetic_incidence_count": sum(
                len(row["participants"]) for row in associations if row["realm"] == "SYNTHETIC_CONTROL"
            ),
            "production_incidence_count": sum(
                len(row["participants"]) for row in associations if row["realm"] == "PRODUCTION"
            ),
            "implicit_projected_pair_count": sum(
                row["association_kind"] == "HIGHER_ORDER"
                and row["pair_projection_policy"] != "NONE" for row in associations
            ),
        },
        "realizations_and_compositions": {
            "synthetic_association_realization_count": sum(
                composition["realm"] == "SYNTHETIC_CONTROL"
                for composition in compositions for _ in composition["association_realizations"]
            ),
            "synthetic_composition_count": sum(row["realm"] == "SYNTHETIC_CONTROL" for row in compositions),
            "synthetic_composition_coherence_review_count": sum(row["realm"] == "SYNTHETIC_CONTROL" for row in reviews),
            "production_association_realization_count": sum(
                composition["realm"] == "PRODUCTION"
                for composition in compositions for _ in composition["association_realizations"]
            ),
            "production_composition_count": sum(row["realm"] == "PRODUCTION" for row in compositions),
            "production_composition_coherence_review_count": sum(row["realm"] == "PRODUCTION" for row in reviews),
            "production_product_eligible_composition_count": sum(
                row["realm"] == "PRODUCTION" and row["product_eligible"] for row in compositions
            ),
        },
        "interaction": {
            "synthetic_state_count": sum(row["realm"] == "SYNTHETIC_CONTROL" for row in fixture["navigation_states"]),
            "synthetic_workflow_count": sum(row["realm"] == "SYNTHETIC_CONTROL" for row in fixture["workflows"]),
            "synthetic_export_count": sum(row["realm"] == "SYNTHETIC_CONTROL" for row in fixture["exports"]),
            "synthetic_transition_count": sum(row["realm"] == "SYNTHETIC_CONTROL" for row in fixture["transitions"]),
            "production_state_count": sum(row["realm"] == "PRODUCTION" for row in fixture["navigation_states"]),
            "production_workflow_count": sum(row["realm"] == "PRODUCTION" for row in fixture["workflows"]),
            "production_export_count": sum(row["realm"] == "PRODUCTION" for row in fixture["exports"]),
            "production_transition_count": sum(row["realm"] == "PRODUCTION" for row in fixture["transitions"]),
        },
    }


def validate_fixture_core(
    fixture: dict[str, Any], hash_contract: dict[str, Any]
) -> dict[str, Any]:
    enforce(fixture.get("source_sha") == SOURCE_SHA, "FIXTURE_SOURCE_SHA")
    enforce(fixture.get("parent_checkpoint_sha") == SEMANTIC_PARENT_SHA, "FIXTURE_PARENT_SHA")
    enforce(fixture.get("contract_version") == CONTRACT_VERSION, "FIXTURE_CONTRACT_VERSION")
    enforce(fixture.get("api_namespace") == SEMANTIC_NAMESPACE, "FIXTURE_NAMESPACE")
    enforce(fixture.get("closure_flags") == EXPECTED_CLOSURE, "FIXTURE_CLOSURE")
    enforce(
        fixture.get("hash_binding_contract_canonical_sha256")
        == semantic_digest(fixture.get("hash_binding_contract")),
        "FIXTURE_HASH_CONTRACT_DIGEST",
    )
    enforce(fixture.get("hash_binding_contract") == hash_contract, "FIXTURE_HASH_CONTRACT_FILE_PARITY")

    scopes = require_list(fixture.get("scopes"), "FIXTURE_SCOPES")
    concepts = require_list(fixture.get("concepts"), "FIXTURE_CONCEPTS")
    senses = require_list(fixture.get("concept_senses"), "FIXTURE_SENSES")
    associations = require_list(fixture.get("associations"), "FIXTURE_ASSOCIATIONS")
    scope_by_id = {row["scope_id"]: row for row in scopes}
    concept_by_id = {row["concept_id"]: row for row in concepts}
    sense_by_id = {row["sense_id"]: row for row in senses}
    enforce(len(scope_by_id) == len(scopes), "DUPLICATE_SCOPE_ID")
    enforce(len(concept_by_id) == len(concepts), "DUPLICATE_CONCEPT_ID")
    enforce(len(sense_by_id) == len(senses), "DUPLICATE_SENSE_ID")
    for scope in scopes:
        for key in SCOPE_SET_KEYS:
            enforce(scope[key] == sorted(set(scope[key])), f"SCOPE_ARRAY_CANONICAL:{scope['scope_id']}:{key}")
    for concept in concepts:
        semantic = {
            key: concept[key]
            for key in (
                "realm", "canonical_label", "semantic_version", "lifecycle_state",
                "association_eligible", "authority", "product_eligible", "product_path",
                "product_eligibility_disposition", "product_ineligibility_reason",
            )
        }
        enforce(concept["semantic_sha256"] == semantic_digest(semantic), f"CONCEPT_HASH:{concept['concept_id']}")
        enforce(product_tuple_valid(concept), f"CONCEPT_PRODUCT_TUPLE:{concept['concept_id']}")
        if concept["lifecycle_state"] == "ACTIVE":
            enforce(
                concept["association_eligible"] is True
                and concept["authority"]["authority_state"] == "FINAL",
                f"ACTIVE_CONCEPT_GOVERNANCE:{concept['concept_id']}",
            )
    for sense in senses:
        semantic = {
            key: sense[key]
            for key in (
                "concept_id", "realm", "bounded_definition", "vocabulary_crosswalk_ids",
                "governed_scope_ids", "semantic_version", "lifecycle_state",
                "association_eligible", "authority", "product_eligible", "product_path",
                "product_eligibility_disposition", "product_ineligibility_reason",
            )
        }
        enforce(sense["semantic_sha256"] == semantic_digest(semantic), f"SENSE_HASH:{sense['sense_id']}")
        enforce(sense["concept_id"] in concept_by_id, f"SENSE_CONCEPT_REF:{sense['sense_id']}")
        enforce(set(sense["governed_scope_ids"]).issubset(scope_by_id), f"SENSE_SCOPE_REF:{sense['sense_id']}")
        enforce(product_tuple_valid(sense), f"SENSE_PRODUCT_TUPLE:{sense['sense_id']}")
        if sense["lifecycle_state"] == "ACTIVE":
            enforce(
                sense["association_eligible"] is True
                and sense["authority"]["authority_state"] == "FINAL",
                f"ACTIVE_SENSE_GOVERNANCE:{sense['sense_id']}",
            )

    by_revision: dict[str, dict[str, Any]] = {}
    by_association: dict[str, dict[str, Any]] = {}
    all_incidence_ids: set[str] = set()
    for record in associations:
        revision_id = require_text(record.get("association_revision_id"), "ASSOCIATION_REVISION_ID")
        association_id = require_text(record.get("association_id"), "ASSOCIATION_ID")
        enforce(revision_id not in by_revision, "DUPLICATE_ASSOCIATION_REVISION")
        enforce(association_id not in by_association, "DUPLICATE_ASSOCIATION_ID")
        participants = require_list(record.get("participants"), f"PARTICIPANTS:{revision_id}")
        enforce(record["arity"] == len(participants), f"ARITY:{revision_id}")
        if record["association_kind"] == "PAIR":
            enforce(record["arity"] == 2, f"PAIR_ARITY:{revision_id}")
            enforce(record["pair_projection_policy"] == "NOT_APPLICABLE", f"PAIR_POLICY:{revision_id}")
        else:
            enforce(record["association_kind"] == "HIGHER_ORDER" and record["arity"] >= 3, f"HIGHER_ARITY:{revision_id}")
            enforce(record["pair_projection_policy"] == "NONE", f"IMPLICIT_HYPEREDGE_PROJECTION:{revision_id}")

        ordinals = [item["ordinal"] for item in participants]
        roles = [item["role_id"] for item in participants]
        if record["order_semantics"] == "ORDERED":
            enforce(ordinals == list(range(len(participants))), f"ORDERED_ORDINALS:{revision_id}")
        else:
            enforce(record["order_semantics"] == "UNORDERED" and all(item is None for item in ordinals), f"UNORDERED_ORDINALS:{revision_id}")
            enforce(
                canonical_participant_identity(record)
                == [
                    {key: item[key] for key in ("concept_id", "sense_id", "ordinal", "role_id")}
                    for item in participants
                ],
                f"UNORDERED_STORAGE:{revision_id}",
            )
        if record["roles_meaningful"]:
            enforce(all(isinstance(item, str) and item for item in roles), f"ROLE_REQUIRED:{revision_id}")
        else:
            enforce(all(item is None for item in roles), f"ROLE_FORBIDDEN:{revision_id}")

        identity = {
            "association_kind": record["association_kind"],
            "participants": canonical_participant_identity(record),
            "scope_identity": scope_identity(record["scope"]),
            "order_semantics": record["order_semantics"],
            "roles_meaningful": record["roles_meaningful"],
        }
        identity_hash = semantic_digest(identity)
        enforce(record["identity_material_sha256"] == identity_hash, f"IDENTITY_HASH:{revision_id}")
        enforce(record["association_id"] == f"association:v3:{identity_hash[:24]}", f"ASSOCIATION_ID_HASH:{revision_id}")
        semantic = association_semantic(record)
        enforce(record["semantic_sha256"] == semantic_digest(semantic), f"ASSOCIATION_HASH:{revision_id}")
        enforce(
            record["association_revision_id"]
            == f"association-revision:v3:{semantic_digest({'association_id': association_id, **semantic})[:24]}",
            f"ASSOCIATION_REVISION_HASH:{revision_id}",
        )
        enforce(record["presentation_sha256"] == semantic_digest(record["presentation"]), f"ASSOCIATION_PRESENTATION_HASH:{revision_id}")
        enforce(record["scope"] == scope_by_id.get(record["scope"]["scope_id"]), f"ASSOCIATION_SCOPE_REF:{revision_id}")
        local_incidence_ids: set[str] = set()
        for index, participant in enumerate(participants, 1):
            incidence_id = participant["incidence_id"]
            enforce(incidence_id == f"incidence:{identity_hash[:16]}:{index:02d}", f"INCIDENCE_ID_HASH:{incidence_id}")
            enforce(incidence_id not in local_incidence_ids and incidence_id not in all_incidence_ids, f"INCIDENCE_UNIQUE:{incidence_id}")
            local_incidence_ids.add(incidence_id)
            all_incidence_ids.add(incidence_id)
            concept = concept_by_id.get(participant["concept_id"])
            sense = sense_by_id.get(participant["sense_id"])
            enforce(concept is not None and sense is not None and sense["concept_id"] == participant["concept_id"], f"PARTICIPANT_VOCABULARY:{incidence_id}")
            enforce(participant["participant_scope_id"] == record["scope"]["scope_id"], f"PARTICIPANT_SCOPE:{incidence_id}")
            enforce(record["scope"]["scope_id"] in sense["governed_scope_ids"], f"PARTICIPANT_SENSE_SCOPE:{incidence_id}")
            if record["lifecycle_state"] == "ACTIVE":
                enforce(concept["lifecycle_state"] == "ACTIVE" and concept["association_eligible"], f"ACTIVE_CONCEPT_REF:{incidence_id}")
                enforce(sense["lifecycle_state"] == "ACTIVE" and sense["association_eligible"], f"ACTIVE_SENSE_REF:{incidence_id}")
        enforce(product_tuple_valid(record), f"ASSOCIATION_PRODUCT_TUPLE:{revision_id}")
        if record["lifecycle_state"] == "ACTIVE":
            enforce(active_association_valid(record), f"ACTIVE_ASSOCIATION_FAIL_CLOSED:{revision_id}")
        by_revision[revision_id] = record
        by_association[association_id] = record

    for record in associations:
        revision_id = record["association_revision_id"]
        links = record["internal_pair_links"]
        enforce(
            record["internal_pair_association_ids"]
            == [link["pair_association_id"] for link in links],
            f"PAIR_LINK_ID_LIST:{revision_id}",
        )
        if record["association_kind"] == "PAIR":
            enforce(not links and not record["internal_pair_association_ids"], f"PAIR_NESTED_LINK:{revision_id}")
        parent_by_incidence = {item["incidence_id"]: item for item in record["participants"]}
        for link in links:
            pair = by_revision.get(link["pair_association_revision_id"])
            enforce(pair is not None and pair["association_kind"] == "PAIR", f"PAIR_LINK_REVISION:{revision_id}")
            enforce(pair["association_id"] == link["pair_association_id"], f"PAIR_LINK_ID:{revision_id}")
            enforce(pair["lifecycle_state"] == "ACTIVE", f"PAIR_LINK_ACTIVE:{revision_id}")
            enforce(len(link["participant_incidence_ids"]) == 2, f"PAIR_LINK_WIDTH:{revision_id}")
            enforce(set(link["participant_incidence_ids"]).issubset(parent_by_incidence), f"PAIR_LINK_PARENT_INCIDENCE:{revision_id}")
            enforce(
                link["pair_participant_incidence_ids"]
                == [item["incidence_id"] for item in pair["participants"]],
                f"PAIR_LINK_PAIR_INCIDENCE:{revision_id}",
            )
            enforce(
                link["endpoint_sense_ids"] == [item["sense_id"] for item in pair["participants"]]
                == [parent_by_incidence[item]["sense_id"] for item in link["participant_incidence_ids"]],
                f"PAIR_LINK_ENDPOINT_SENSE:{revision_id}",
            )

    reviews = require_list(fixture.get("composition_coherence_reviews"), "FIXTURE_REVIEWS")
    review_by_id = {row["composition_coherence_review_id"]: row for row in reviews}
    enforce(len(review_by_id) == len(reviews), "DUPLICATE_COMPOSITION_REVIEW")
    for review in reviews:
        semantic = {
            key: review[key]
            for key in (
                "composition_id", "realm", "review_state", "authority", "review_version",
                "global_coherence", "bounded_senses_compatible", "case_scope_compatible",
                "roles_and_topology_supported", "same_configuration", "unsupported_bridge_count",
                "association_revision_ids", "association_realization_ids", "incidence_ids",
                "decision", "reasons",
            )
        }
        enforce(review["semantic_sha256"] == semantic_digest(semantic), f"COMPOSITION_REVIEW_HASH:{review['composition_coherence_review_id']}")
        enforce(
            review["composition_coherence_review_id"]
            == f"composition-review:v3:{semantic_digest(semantic)[:24]}",
            f"COMPOSITION_REVIEW_ID_HASH:{review['composition_coherence_review_id']}",
        )
        if review["decision"] == "COHERENT":
            enforce(
                review["review_state"] == "FINAL"
                and review["authority"]["authority_state"] == "FINAL"
                and review["global_coherence"] == "PASS"
                and review["bounded_senses_compatible"] is True
                and review["case_scope_compatible"] is True
                and review["roles_and_topology_supported"] is True
                and review["same_configuration"] is True
                and review["unsupported_bridge_count"] == 0,
                f"COHERENT_REVIEW_FAIL_CLOSED:{review['composition_coherence_review_id']}",
            )

    compositions = require_list(fixture.get("compositions"), "FIXTURE_COMPOSITIONS")
    realization_by_id: dict[str, dict[str, Any]] = {}
    for composition in compositions:
        revision_id = composition["composition_revision_id"]
        realizations = composition["association_realizations"]
        identity = {
            "association_realization_ids": [row["association_realization_id"] for row in realizations],
            "node_ids": composition["composition_node_ids"],
            "topology_family": composition["topology_family"],
        }
        enforce(composition["composition_id"] == f"composition:v3:{semantic_digest(identity)[:24]}", f"COMPOSITION_ID_HASH:{revision_id}")
        semantic = {key: composition[key] for key in COMPOSITION_SEMANTIC_FIELDS}
        enforce(composition["semantic_sha256"] == semantic_digest(semantic), f"COMPOSITION_HASH:{revision_id}")
        enforce(
            revision_id == f"composition-revision:v3:{semantic_digest({'semantic': semantic, 'revision': 1})[:24]}",
            f"COMPOSITION_REVISION_HASH:{revision_id}",
        )
        enforce(composition["presentation_sha256"] == semantic_digest(composition["presentation"]), f"COMPOSITION_PRESENTATION_HASH:{revision_id}")
        review = review_by_id.get(composition["global_coherence_review_id"])
        enforce(review is not None and review["composition_id"] == composition["composition_id"], f"COMPOSITION_REVIEW_REF:{revision_id}")
        traced_revisions: set[str] = set()
        traced_realizations: set[str] = set()
        traced_incidence: set[str] = set()
        traced_nodes: set[str] = set()
        for realization in realizations:
            realization_id = realization["association_realization_id"]
            enforce(realization_id not in realization_by_id, f"DUPLICATE_REALIZATION:{realization_id}")
            association = by_revision.get(realization["association_revision_id"])
            enforce(association is not None, f"REALIZATION_ASSOCIATION_REF:{realization_id}")
            material = {
                "association_revision_id": realization["association_revision_id"],
                "incidence_ids": realization["realized_incidence_ids"],
                "realization_kind": realization["realization_kind"],
            }
            enforce(realization_id == f"realization:v3:{semantic_digest(material)[:24]}", f"REALIZATION_ID_HASH:{realization_id}")
            enforce(realization["semantic_sha256"] == semantic_digest(material), f"REALIZATION_HASH:{realization_id}")
            enforce(realization["presentation_sha256"] == semantic_digest(realization["presentation"]), f"REALIZATION_PRESENTATION_HASH:{realization_id}")
            expected_incidences = {item["incidence_id"] for item in association["participants"]}
            enforce(set(realization["realized_incidence_ids"]) == expected_incidences, f"REALIZATION_INCIDENCE_SET:{realization_id}")
            if association["association_kind"] == "PAIR":
                enforce(realization["realization_kind"] == "PAIR_EDGE", f"PAIR_REALIZATION_KIND:{realization_id}")
            else:
                enforce(realization["realization_kind"] != "PAIR_EDGE", f"HYPEREDGE_PAIR_REALIZATION:{realization_id}")
            traced_revisions.add(association["association_revision_id"])
            traced_realizations.add(realization_id)
            traced_incidence.update(expected_incidences)
            traced_nodes.update(item["concept_id"] for item in association["participants"])
            realization_by_id[realization_id] = realization
        enforce(set(composition["composition_node_ids"]) == traced_nodes, f"COMPOSITION_NODE_TRACE:{revision_id}")
        enforce(set(review["association_revision_ids"]) == traced_revisions, f"REVIEW_ASSOCIATION_TRACE:{revision_id}")
        enforce(set(review["association_realization_ids"]) == traced_realizations, f"REVIEW_REALIZATION_TRACE:{revision_id}")
        enforce(set(review["incidence_ids"]) == traced_incidence, f"REVIEW_INCIDENCE_TRACE:{revision_id}")
        enforce(product_tuple_valid(composition), f"COMPOSITION_PRODUCT_TUPLE:{revision_id}")

    state_by_id: dict[str, dict[str, Any]] = {}
    composition_by_revision = {row["composition_revision_id"]: row for row in compositions}
    for state in fixture["navigation_states"]:
        semantic = binding_material(
            hash_contract, "NAVIGATION_STATE", "navigation_state_semantic", state
        )
        enforce(state["semantic_sha256"] == semantic_digest(semantic), f"STATE_SEMANTIC_HASH:{state['state_id']}")
        enforce(state["state_id"] == f"state:v3:{semantic_digest(semantic)[:24]}", f"STATE_ID_HASH:{state['state_id']}")
        presentation = binding_material(
            hash_contract, "NAVIGATION_STATE", "navigation_state_presentation", state
        )
        enforce(state["presentation_sha256"] == semantic_digest(presentation), f"STATE_PRESENTATION_HASH:{state['state_id']}")
        enforce(state["composition_revision_id"] in composition_by_revision, f"STATE_COMPOSITION_REF:{state['state_id']}")
        state_by_id[state["state_id"]] = state
    transition_by_id: dict[str, dict[str, Any]] = {}
    for transition in require_list(fixture.get("transitions"), "FIXTURE_TRANSITIONS"):
        semantic = binding_material(
            hash_contract, "TRANSITION", "transition_semantic", transition
        )
        transition_id = transition["transition_id"]
        enforce(transition_id not in transition_by_id, f"DUPLICATE_TRANSITION_ID:{transition_id}")
        enforce(
            transition["semantic_sha256"] == semantic_digest(semantic),
            f"TRANSITION_SEMANTIC_HASH:{transition_id}",
        )
        enforce(
            transition_id == f"transition:v3:{semantic_digest(semantic)[:24]}",
            f"TRANSITION_ID_HASH:{transition_id}",
        )
        enforce(
            transition["from_state_id"] in state_by_id
            and transition["to_state_id"] in state_by_id,
            f"TRANSITION_STATE_REF:{transition_id}",
        )
        transition_by_id[transition_id] = transition
    workflow_by_id: dict[str, dict[str, Any]] = {}
    for workflow in fixture["workflows"]:
        semantic = binding_material(hash_contract, "WORKFLOW", "workflow_semantic", workflow)
        enforce(workflow["semantic_sha256"] == semantic_digest(semantic), f"WORKFLOW_SEMANTIC_HASH:{workflow['workflow_id']}")
        enforce(workflow["workflow_id"] == f"workflow:v3:{semantic_digest(semantic)[:24]}", f"WORKFLOW_ID_HASH:{workflow['workflow_id']}")
        enforce(set(workflow["state_ids"]).issubset(state_by_id), f"WORKFLOW_STATE_REF:{workflow['workflow_id']}")
        enforce(
            len(workflow["transition_ids"]) == len(set(workflow["transition_ids"]))
            and set(workflow["transition_ids"]).issubset(transition_by_id),
            f"WORKFLOW_TRANSITION_REF:{workflow['workflow_id']}",
        )
        enforce(set(workflow["association_revision_ids"]).issubset(by_revision), f"WORKFLOW_ASSOCIATION_REF:{workflow['workflow_id']}")
        enforce(set(workflow["association_realization_ids"]).issubset(realization_by_id), f"WORKFLOW_REALIZATION_REF:{workflow['workflow_id']}")
        workflow_by_id[workflow["workflow_id"]] = workflow
    for export in fixture["exports"]:
        semantic = binding_material(hash_contract, "EXPORT", "export_semantic", export)
        enforce(export["semantic_sha256"] == semantic_digest(semantic), f"EXPORT_SEMANTIC_HASH:{export['export_id']}")
        enforce(export["export_id"] == f"export:v3:{semantic_digest(semantic)[:24]}", f"EXPORT_ID_HASH:{export['export_id']}")
        presentation = binding_material(
            hash_contract, "EXPORT", "export_presentation", export
        )
        enforce(export["presentation_sha256"] == semantic_digest(presentation), f"EXPORT_PRESENTATION_HASH:{export['export_id']}")
        enforce(export["workflow_id"] in workflow_by_id and export["state_id"] in state_by_id, f"EXPORT_INTERACTION_REF:{export['export_id']}")
        enforce(export["composition_revision_id"] in composition_by_revision, f"EXPORT_COMPOSITION_REF:{export['export_id']}")
        enforce(export["pair_projection_policy_preserved"] is True, f"EXPORT_PROJECTION_PRESERVATION:{export['export_id']}")

    taxonomy = reconstruct_count_taxonomy(fixture)
    enforce(fixture.get("count_taxonomy") == taxonomy, "FIXTURE_COUNT_TAXONOMY")
    enforce(not any(row["realm"] == "PRODUCTION" and row["lifecycle_state"] == "ACTIVE" for row in associations), "PRODUCTION_ACTIVE_ASSOCIATION")
    enforce(not any(row["lifecycle_state"] == "ACTIVE" and row["review"]["review_state"] != "FINAL" for row in associations), "ACTIVE_PENDING_REVIEW")
    return {
        "scope_by_id": scope_by_id,
        "concept_by_id": concept_by_id,
        "sense_by_id": sense_by_id,
        "association_by_revision": by_revision,
        "association_by_id": by_association,
        "review_by_id": review_by_id,
        "composition_by_revision": composition_by_revision,
        "realization_by_id": realization_by_id,
        "state_by_id": state_by_id,
        "workflow_by_id": workflow_by_id,
        "transition_by_id": transition_by_id,
        "taxonomy": taxonomy,
        "incidence_count": len(all_incidence_ids),
    }


def control_map(fixture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    controls = {row["control_class"]: row for row in fixture["control_expectations"]}
    enforce(set(controls) == EXPECTED_CONTROL_CLASSES, "CONTROL_CLASS_SET")
    enforce(len(controls) == len(fixture["control_expectations"]), "CONTROL_CLASS_DUPLICATE")
    return controls


def validate_control_semantics(fixture: dict[str, Any]) -> dict[str, Any]:
    controls = control_map(fixture)
    by_revision = {row["association_revision_id"]: row for row in fixture["associations"]}
    by_concept = {row["concept_id"]: row for row in fixture["concepts"]}
    by_sense = {row["sense_id"]: row for row in fixture["concept_senses"]}
    by_composition = {row["composition_revision_id"]: row for row in fixture["compositions"]}
    by_review = {
        row["composition_coherence_review_id"]: row
        for row in fixture["composition_coherence_reviews"]
    }

    sparse_refs = controls["VALID_SPARSE_DISCONNECTED_HIGHER_ORDER_GROUP"]["object_refs"]
    sparse = by_revision[sparse_refs[0]]
    enforce(
        sparse["association_kind"] == "HIGHER_ORDER"
        and sparse["arity"] == 5
        and sparse["lifecycle_state"] == "ACTIVE"
        and sparse["review"]["global_coherence"] == "PASS"
        and sparse["pair_projection_policy"] == "NONE"
        and len(sparse["internal_pair_links"]) == 2
        and graph_component_count(sparse) == 3
        and all(by_revision[ref]["association_kind"] == "PAIR" and by_revision[ref]["lifecycle_state"] == "ACTIVE" for ref in sparse_refs[1:]),
        "CONTROL_SPARSE_VALID_HYPEREDGE",
    )

    clique_refs = controls["INVALID_FULL_PAIR_CLIQUE"]["object_refs"]
    clique = by_revision[clique_refs[0]]
    enforce(
        clique["association_kind"] == "HIGHER_ORDER"
        and clique["arity"] == 4
        and clique["lifecycle_state"] == "INACTIVE"
        and clique["review"]["global_coherence"] == "FAIL"
        and len(clique["internal_pair_links"]) == 6
        and graph_component_count(clique) == 1
        and len(clique_refs[1:]) == 6
        and all(by_revision[ref]["association_kind"] == "PAIR" and by_revision[ref]["lifecycle_state"] == "ACTIVE" for ref in clique_refs[1:]),
        "CONTROL_ALL_PAIRS_INVALID_GROUP",
    )

    bounded = by_revision[controls["BOUNDED_SENSE_CONFLICT"]["object_refs"][0]]
    enforce(
        bounded["review"]["bounded_senses_compatible"] is False
        and bounded["review"]["global_coherence"] == "FAIL"
        and bounded["lifecycle_state"] == "INACTIVE",
        "CONTROL_BOUNDED_SENSE_CONFLICT",
    )
    cross_case = by_revision[controls["CROSS_CASE_SOURCE_BUNDLE"]["object_refs"][0]]
    enforce(
        cross_case["review"]["case_scope_compatible"] is False
        and cross_case["review"]["unsupported_bridge_count"] == 2
        and len(cross_case["scope"]["historical_case_ids"]) == 2
        and cross_case["lifecycle_state"] == "INACTIVE",
        "CONTROL_CROSS_CASE_BUNDLE",
    )

    isolated_refs = controls["ISOLATED_ACTIVE_TERM_IN_VALID_HYPEREDGE"]["object_refs"]
    isolated_association = by_revision[isolated_refs[0]]
    isolated_concept = by_concept[isolated_refs[1]]
    isolated_sense = by_sense[isolated_refs[2]]
    linked_incidences = {
        incidence_id
        for link in isolated_association["internal_pair_links"]
        for incidence_id in link["participant_incidence_ids"]
    }
    isolated_participant = next(
        row for row in isolated_association["participants"] if row["sense_id"] == isolated_sense["sense_id"]
    )
    enforce(
        isolated_participant["incidence_id"] not in linked_incidences
        and isolated_concept["lifecycle_state"] == "ACTIVE"
        and isolated_concept["association_eligible"] is True
        and isolated_concept["authority"]["authority_state"] == "FINAL"
        and isolated_sense["lifecycle_state"] == "ACTIVE"
        and isolated_sense["association_eligible"] is True
        and isolated_sense["authority"]["authority_state"] == "FINAL"
        and isolated_association["lifecycle_state"] == "ACTIVE",
        "CONTROL_ISOLATED_ACTIVE_TERM",
    )

    render_refs = controls["RENDERABLE_COMPOSITION_WITHOUT_VALID_GROUP"]["object_refs"]
    renderable = by_composition[render_refs[0]]
    render_review = by_review[renderable["global_coherence_review_id"]]
    enforce(
        renderable["renderability"] == "PASS"
        and renderable["product_eligible"] is False
        and render_review["global_coherence"] == "FAIL"
        and by_revision[render_refs[1]]["review"]["global_coherence"] == "FAIL",
        "CONTROL_RENDERABLE_WITHOUT_VALID_ASSOCIATION",
    )

    projection_refs = controls["ILLEGAL_HYPEREDGE_PAIR_PROJECTION"]["object_refs"]
    enforce(
        by_revision[projection_refs[0]]["pair_projection_policy"] == "NONE"
        and not any(
            row["association_kind"] == "HIGHER_ORDER" and row["pair_projection_policy"] != "NONE"
            for row in fixture["associations"]
        )
        and any(
            row["attempt_id"] == projection_refs[1] and row["expected_decision"] == "REJECT"
            for row in fixture["invalid_attempts"]
        ),
        "CONTROL_IMPLICIT_PROJECTION",
    )

    pending_refs = controls["ACTIVE_WITH_PENDING_OR_NONFINAL_REVIEW"]["object_refs"]
    pending = by_revision[pending_refs[0]]
    enforce(
        pending["review"]["review_state"] == "PENDING"
        and pending["activation"]["decision"] == "REJECT"
        and pending["lifecycle_state"] == "INACTIVE"
        and any(
            row["attempt_id"] == pending_refs[1] and row["expected_decision"] == "REJECT"
            for row in fixture["invalid_attempts"]
        ),
        "CONTROL_ACTIVE_PENDING_REVIEW",
    )

    arity_five = by_revision[controls["ACTIVE_ARITY_FIVE_PROJECTION_NONE"]["object_refs"][0]]
    enforce(
        arity_five["arity"] == 5
        and arity_five["lifecycle_state"] == "ACTIVE"
        and arity_five["pair_projection_policy"] == "NONE"
        and arity_five["realm"] == "SYNTHETIC_CONTROL",
        "CONTROL_ACTIVE_ARITY_FIVE",
    )

    adapter_refs = controls["ONE_WAY_V2_PAIR_ADAPTER"]["object_refs"]
    adapters = {row["adapter_id"]: row for row in fixture["v2_pair_adapter_receipts"]}
    adapter = adapters[adapter_refs[0]]
    enforce(
        adapter["target_association_revision_id"] == adapter_refs[1]
        and adapter["direction"] == "V2_PAIR_TO_V3_PAIR_ONLY"
        and adapter["higher_order_input_allowed"] is False
        and adapter["reverse_conversion_allowed"] is False
        and adapter["semantic_claims_added"] is False
        and by_revision[adapter_refs[1]]["association_kind"] == "PAIR",
        "CONTROL_ONE_WAY_ADAPTER",
    )
    return {
        "sparse_revision_id": sparse["association_revision_id"],
        "clique_revision_id": clique["association_revision_id"],
        "bounded_revision_id": bounded["association_revision_id"],
        "cross_case_revision_id": cross_case["association_revision_id"],
        "isolated_concept_id": isolated_concept["concept_id"],
        "renderable_composition_revision_id": renderable["composition_revision_id"],
        "pending_revision_id": pending["association_revision_id"],
    }


def validate_round16a(round16a: dict[str, Any]) -> None:
    enforce(round16a.get("source_sha") == SOURCE_SHA, "ROUND16A_SOURCE_SHA")
    enforce(round16a.get("source_tree") == SOURCE_TREE, "ROUND16A_SOURCE_TREE")
    enforce(round16a.get("closure") == EXPECTED_CLOSURE, "ROUND16A_CLOSURE")
    enforce(round16a.get("main_object_distributions") == EXPECTED_ROUND16A_DISTRIBUTIONS, "ROUND16A_DISPOSITIONS")
    enforce(round16a.get("main_object_total_distribution") == EXPECTED_ROUND16A_TOTAL, "ROUND16A_TOTAL_DISPOSITION")
    enforce(round16a.get("transition_outcome_distribution") == EXPECTED_TRANSITION_OUTCOMES, "ROUND16A_TRANSITION_DISPOSITION")
    for family, expected in EXPECTED_FAMILY_TOTALS.items():
        enforce(sum(round16a["main_object_distributions"][family].values()) == expected, f"ROUND16A_FAMILY_TOTAL:{family}")
    enforce(sum(EXPECTED_TRANSITION_OUTCOMES.values()) == 749944 == round16a.get("transition_count"), "ROUND16A_TRANSITION_TOTAL")
    enforce(sum(EXPECTED_ROUND16A_TOTAL.values()) == 773671 == round16a.get("main_object_count"), "ROUND16A_MAIN_TOTAL")
    combined = {
        disposition: sum(
            distribution.get(disposition, 0)
            for distribution in EXPECTED_ROUND16A_DISTRIBUTIONS.values()
        ) + EXPECTED_TRANSITION_OUTCOMES[disposition]
        for disposition in EXPECTED_ROUND16A_TOTAL
    }
    enforce(combined == EXPECTED_ROUND16A_TOTAL, "ROUND16A_TOTAL_RECONCILIATION")
    enforce(round16a.get("reconciled_row_count_including_topology_audit_records") == 774296, "ROUND16A_RECONCILED_ROWS")
    enforce(round16a.get("active_fact_created_count") == 0, "ROUND16A_ACTIVE_FACT")
    enforce(round16a.get("product_activation_count") == 0, "ROUND16A_PRODUCT_ACTIVATION")
    enforce(round16a.get("pair_projection_created_count") == 0, "ROUND16A_PAIR_PROJECTION")
    enforce(round16a.get("checkpoint009_correction_round16a_subgraph_overlap_count") == 0, "ROUND16A_OVERLAP_CORRECTION")
    enforce(round16a.get("checkpoint009_quarantined_source_scope_correction_count") == 1, "ROUND16A_SCOPE_QUARANTINE")


def synthetic_fact_boundary() -> dict[str, Any]:
    return {
        "data_class": "SYNTHETIC_CONTROL",
        "production_fact": False,
        "synthetic_control": True,
    }


def validate_synthetic_fact_boundary(record: dict[str, Any], code: str) -> None:
    boundary = require_dict(record.get("fact_boundary"), f"{code}:FACT_BOUNDARY")
    enforce(set(boundary) == FACT_BOUNDARY_KEYS, f"{code}:FACT_BOUNDARY_KEYS")
    enforce(boundary == synthetic_fact_boundary(), f"{code}:FACT_BOUNDARY_VALUES")


def expected_association_dto(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "activation": source["activation"],
        "arity": source["arity"],
        "association_id": source["association_id"],
        "association_kind": source["association_kind"],
        "association_revision_id": source["association_revision_id"],
        "eligibility": {
            "lifecycle_state": source["lifecycle_state"],
            "product_eligibility_disposition": source["product_eligibility_disposition"],
            "product_eligible": source["product_eligible"],
            "product_ineligibility_reason": source["product_ineligibility_reason"],
            "product_path": source["product_path"],
        },
        "fact_boundary": synthetic_fact_boundary(),
        "identity_material_sha256": source["identity_material_sha256"],
        "internal_pair_association_ids": source["internal_pair_association_ids"],
        "internal_pair_links": source["internal_pair_links"],
        "order_semantics": source["order_semantics"],
        "pair_projection_policy": source["pair_projection_policy"],
        "participants": source["participants"],
        "presentation": source["presentation"],
        "presentation_sha256": source["presentation_sha256"],
        "provenance": source["evidence"],
        "realm": source["realm"],
        "review": source["review"],
        "roles_meaningful": source["roles_meaningful"],
        "scope": source["scope"],
        "semantic_sha256": source["semantic_sha256"],
        "semantic_version": source["semantic_version"],
        "uncertainty": source["uncertainty"],
    }


def expected_composition_dto(source: dict[str, Any], review: dict[str, Any], association_by_revision: dict[str, dict[str, Any]]) -> dict[str, Any]:
    realizations = []
    for item in source["association_realizations"]:
        association = association_by_revision[item["association_revision_id"]]
        realizations.append({**item, "association_id": association["association_id"], "association_kind": association["association_kind"]})
    return {
        "association_realizations": realizations,
        "association_trace_complete": source["association_trace_complete"],
        "coherence_review": {**review, "fact_boundary": synthetic_fact_boundary()},
        "composition_id": source["composition_id"],
        "composition_node_ids": source["composition_node_ids"],
        "composition_revision_id": source["composition_revision_id"],
        "eligibility": {
            "product_eligibility_disposition": source["product_eligibility_disposition"],
            "product_eligible": source["product_eligible"],
            "product_ineligibility_reason": source["product_ineligibility_reason"],
            "product_path": source["product_path"],
        },
        "fact_boundary": synthetic_fact_boundary(),
        "global_coherence_review_id": source["global_coherence_review_id"],
        "presentation": source["presentation"],
        "presentation_sha256": source["presentation_sha256"],
        "realm": source["realm"],
        "renderability": source["renderability"],
        "semantic_sha256": source["semantic_sha256"],
        "topology_family": source["topology_family"],
    }


def index_unique(records: list[dict[str, Any]], key: str, code: str) -> dict[str, dict[str, Any]]:
    result = {require_text(row.get(key), f"{code}:MISSING"): row for row in records}
    enforce(len(result) == len(records), f"{code}:DUPLICATE")
    return result


def validate_interaction_surface_independent(
    surface: dict[str, Any], hash_contract: dict[str, Any]
) -> None:
    """Reconstruct interaction integrity without using the primary TS validator."""

    expected_realm = "SYNTHETIC_CONTROL"
    compositions = index_unique(
        require_list(surface.get("compositions"), "INTERACTION_COMPOSITIONS"),
        "composition_revision_id",
        "INTERACTION_COMPOSITION",
    )
    realizations = index_unique(
        require_list(surface.get("association_realizations"), "INTERACTION_REALIZATIONS"),
        "association_realization_id",
        "INTERACTION_REALIZATION",
    )
    associations = index_unique(
        require_list(surface.get("associations"), "INTERACTION_ASSOCIATIONS"),
        "association_revision_id",
        "INTERACTION_ASSOCIATION",
    )
    incidences = index_unique(
        require_list(surface.get("incidences"), "INTERACTION_INCIDENCES"),
        "incidence_id",
        "INTERACTION_INCIDENCE",
    )

    state_rows = require_list(surface.get("navigation_states"), "INTERACTION_STATES")
    states = index_unique(state_rows, "state_id", "INTERACTION_STATE")
    for state in state_rows:
        state_id = state["state_id"]
        enforce(set(state) == NAVIGATION_STATE_KEYS, f"STATE_KEYS:{state_id}")
        validate_synthetic_fact_boundary(state, "STATE")
        composition = compositions.get(state["composition_revision_id"])
        enforce(composition is not None, f"STATE_COMPOSITION:{state_id}")
        enforce(
            state["realm"] == expected_realm == composition["realm"],
            f"STATE_COMPOSITION_REALM:{state_id}",
        )
        enforce(
            set(require_dict(state["presentation"], f"STATE_PRESENTATION:{state_id}"))
            == {"focus_style", "viewport"},
            f"STATE_PRESENTATION_KEYS:{state_id}",
        )
        enforce(state["bipartite_alternation_valid"] is True, f"STATE_BIPARTITE_FLAG:{state_id}")
        nodes = require_list(state["nodes"], f"STATE_NODES:{state_id}")
        enforce(len(nodes) >= 3, f"STATE_NODE_COUNT:{state_id}")
        node_by_id: dict[str, dict[str, Any]] = {}
        composition_concepts = set(composition["composition_node_ids"])
        composition_associations = {
            row["association_revision_id"] for row in composition["association_realizations"]
        }
        for node in nodes:
            enforce(set(node) == NAVIGATION_NODE_KEYS, f"NAVIGATION_NODE_KEYS:{state_id}")
            node_id = require_text(node.get("navigation_node_id"), f"NAVIGATION_NODE_ID:{state_id}")
            enforce(node_id not in node_by_id, f"NAVIGATION_NODE_DUPLICATE:{state_id}")
            node_by_id[node_id] = node
            if node["node_kind"] == "CONCEPT":
                enforce(
                    node["association_revision_id"] is None
                    and node["concept_id"] in composition_concepts,
                    f"STATE_NODE_OUTSIDE_COMPOSITION:{state_id}",
                )
            elif node["node_kind"] == "ASSOCIATION":
                enforce(
                    node["concept_id"] is None
                    and node["association_revision_id"] in composition_associations,
                    f"STATE_NODE_OUTSIDE_COMPOSITION:{state_id}",
                )
            else:
                raise VerificationError(f"STATE_NODE_KIND:{state_id}")
        focus_id = state["focus_navigation_node_id"]
        enforce(focus_id in node_by_id, f"STATE_FOCUS:{state_id}")
        steps = require_list(state["path"], f"STATE_PATH:{state_id}")
        enforce(bool(steps), f"STATE_PATH_EMPTY:{state_id}")
        previous_target: str | None = None
        for step in steps:
            enforce(set(step) == NAVIGATION_PATH_STEP_KEYS, f"NAVIGATION_PATH_STEP_KEYS:{state_id}")
            source = node_by_id.get(step["from_navigation_node_id"])
            target = node_by_id.get(step["to_navigation_node_id"])
            incidence = incidences.get(step["incidence_id"])
            enforce(
                source is not None and target is not None and incidence is not None
                and source["node_kind"] != target["node_kind"],
                f"STATE_PATH_REFERENCE:{state_id}",
            )
            if previous_target is not None:
                enforce(
                    previous_target == step["from_navigation_node_id"],
                    f"STATE_PATH_DISCONTINUOUS:{state_id}",
                )
            association_node = source if source["node_kind"] == "ASSOCIATION" else target
            concept_node = source if source["node_kind"] == "CONCEPT" else target
            realization_owns_incidence = any(
                row["association_revision_id"] == incidence["association_revision_id"]
                and incidence["incidence_id"] in row["realized_incidence_ids"]
                for row in composition["association_realizations"]
            )
            enforce(
                association_node["association_revision_id"] == incidence["association_revision_id"]
                and concept_node["concept_id"] == incidence["concept_id"]
                and realization_owns_incidence,
                f"STATE_PATH_INCIDENCE_TRACE:{state_id}",
            )
            previous_target = step["to_navigation_node_id"]
        enforce(previous_target == focus_id, f"STATE_TERMINAL_FOCUS:{state_id}")
        state_semantic = binding_material(
            hash_contract, "NAVIGATION_STATE", "navigation_state_semantic", state
        )
        state_semantic_sha256 = semantic_digest(state_semantic)
        enforce(
            state["semantic_sha256"] == state_semantic_sha256,
            f"STATE_SEMANTIC_HASH:{state_id}",
        )
        enforce(
            state_id == f"state:v3:{state_semantic_sha256[:24]}",
            f"STATE_ID_HASH:{state_id}",
        )
        state_presentation = binding_material(
            hash_contract, "NAVIGATION_STATE", "navigation_state_presentation", state
        )
        enforce(
            state["presentation_sha256"] == semantic_digest(state_presentation),
            f"STATE_PRESENTATION_HASH:{state_id}",
        )

    transition_rows = require_list(surface.get("transitions"), "INTERACTION_TRANSITIONS")
    transitions = index_unique(transition_rows, "transition_id", "INTERACTION_TRANSITION")
    for transition in transition_rows:
        transition_id = transition["transition_id"]
        enforce(set(transition) == TRANSITION_KEYS, f"TRANSITION_KEYS:{transition_id}")
        validate_synthetic_fact_boundary(transition, "TRANSITION")
        source = states.get(transition["from_state_id"])
        target = states.get(transition["to_state_id"])
        enforce(source is not None and target is not None, f"TRANSITION_ENDPOINT:{transition_id}")
        enforce(
            transition["realm"] == expected_realm
            == source["realm"] == target["realm"],
            f"TRANSITION_REALM:{transition_id}",
        )
        enforce(
            transition["transition_kind"] in {"FOLLOW_INCIDENCE", "MOVE_FOCUS", "EXPORT"},
            f"TRANSITION_KIND:{transition_id}",
        )
        enforce(
            isinstance(transition["state_mutated"], bool)
            and transition["state_mutated"]
            == (transition["from_state_id"] != transition["to_state_id"]),
            f"TRANSITION_STATE_MUTATED:{transition_id}",
        )
        trace_values = (
            transition["incidence_id"],
            transition["association_revision_id"],
            transition["association_realization_id"],
        )
        trace_null = all(value is None for value in trace_values)
        trace_complete = all(isinstance(value, str) and bool(value) for value in trace_values)
        enforce(
            (trace_null or trace_complete)
            and (transition["transition_kind"] != "FOLLOW_INCIDENCE" or trace_complete),
            f"TRANSITION_TRACE_PARTIAL:{transition_id}",
        )
        if trace_complete:
            incidence = incidences.get(transition["incidence_id"])
            realization = realizations.get(transition["association_realization_id"])
            enforce(
                incidence is not None and realization is not None
                and incidence["association_revision_id"] == transition["association_revision_id"]
                and realization["association_revision_id"] == transition["association_revision_id"]
                and transition["incidence_id"] in realization["realized_incidence_ids"]
                and source["composition_revision_id"] == target["composition_revision_id"]
                == realization["composition_revision_id"],
                f"TRANSITION_TRACE:{transition_id}",
            )
        transition_semantic = binding_material(
            hash_contract, "TRANSITION", "transition_semantic", transition
        )
        transition_semantic_sha256 = semantic_digest(transition_semantic)
        enforce(
            transition["semantic_sha256"] == transition_semantic_sha256,
            f"TRANSITION_SEMANTIC_HASH:{transition_id}",
        )
        enforce(
            transition_id == f"transition:v3:{transition_semantic_sha256[:24]}",
            f"TRANSITION_ID_HASH:{transition_id}",
        )

    workflow_rows = require_list(surface.get("workflows"), "INTERACTION_WORKFLOWS")
    workflows = index_unique(workflow_rows, "workflow_id", "INTERACTION_WORKFLOW")
    memberships = {transition_id: 0 for transition_id in transitions}
    for workflow in workflow_rows:
        workflow_id = workflow["workflow_id"]
        enforce(set(workflow) == WORKFLOW_KEYS, f"WORKFLOW_KEYS:{workflow_id}")
        validate_synthetic_fact_boundary(workflow, "WORKFLOW")
        enforce(
            workflow["transition_kind"] in {"FOLLOW_INCIDENCE", "MOVE_FOCUS", "EXPORT"},
            f"WORKFLOW_TRANSITION_KIND:{workflow_id}",
        )
        workflow_state_ids = require_list(
            workflow["state_ids"], f"WORKFLOW_STATE_IDS:{workflow_id}"
        )
        enforce(
            len(workflow_state_ids) == len(set(workflow_state_ids))
            and set(workflow_state_ids).issubset(states),
            f"WORKFLOW_STATE_SET:{workflow_id}",
        )
        enforce(
            workflow["initial_state_id"] in workflow_state_ids,
            f"WORKFLOW_INITIAL_STATE_MEMBERSHIP:{workflow_id}",
        )
        enforce(
            workflow["realm"] == expected_realm
            and all(states[state_id]["realm"] == workflow["realm"] for state_id in workflow_state_ids),
            f"WORKFLOW_STATE_REALM:{workflow_id}",
        )
        expected_realizations = {
            realization["association_realization_id"]
            for state_id in workflow_state_ids
            for realization in compositions[states[state_id]["composition_revision_id"]]["association_realizations"]
        }
        observed_realizations = workflow["association_realization_ids"]
        enforce(
            len(observed_realizations) == len(set(observed_realizations))
            and set(observed_realizations) == expected_realizations,
            f"WORKFLOW_REALIZATION_EXACT_SET:{workflow_id}",
        )
        expected_revisions = {
            realizations[realization_id]["association_revision_id"]
            for realization_id in expected_realizations
        }
        observed_revisions = workflow["association_revision_ids"]
        enforce(
            len(observed_revisions) == len(set(observed_revisions))
            and set(observed_revisions) == expected_revisions,
            f"WORKFLOW_ASSOCIATION_EXACT_SET:{workflow_id}",
        )
        workflow_transition_ids = require_list(
            workflow["transition_ids"], f"WORKFLOW_TRANSITION_IDS:{workflow_id}"
        )
        enforce(
            len(workflow_transition_ids) == len(set(workflow_transition_ids)),
            f"WORKFLOW_TRANSITION_IDS_DUPLICATE:{workflow_id}",
        )
        member_transitions: list[dict[str, Any]] = []
        workflow_state_set = set(workflow_state_ids)
        for transition_id in workflow_transition_ids:
            enforce(
                transition_id in transitions,
                f"WORKFLOW_TRANSITION_REFERENCE:{workflow_id}",
            )
            transition = transitions[transition_id]
            enforce(
                transition["realm"] == workflow["realm"]
                and transition["transition_kind"] == workflow["transition_kind"]
                and transition["from_state_id"] in workflow_state_set
                and transition["to_state_id"] in workflow_state_set,
                f"WORKFLOW_SELECTED_TRANSITION_SCOPE:{workflow_id}",
            )
            member_transitions.append(transition)
            memberships[transition_id] += 1
        reached = {workflow["initial_state_id"]}
        frontier = [workflow["initial_state_id"]]
        cursor = 0
        while cursor < len(frontier):
            current = frontier[cursor]
            cursor += 1
            for transition in member_transitions:
                destination = transition["to_state_id"]
                if transition["from_state_id"] == current and destination not in reached:
                    reached.add(destination)
                    frontier.append(destination)
        enforce(
            isinstance(workflow["reachable"], bool)
            and workflow["reachable"] == workflow_state_set.issubset(reached),
            f"WORKFLOW_REACHABILITY:{workflow_id}",
        )
        workflow_semantic = binding_material(
            hash_contract, "WORKFLOW", "workflow_semantic", workflow
        )
        workflow_semantic_sha256 = semantic_digest(workflow_semantic)
        enforce(
            workflow["semantic_sha256"] == workflow_semantic_sha256,
            f"WORKFLOW_SEMANTIC_HASH:{workflow_id}",
        )
        enforce(
            workflow_id == f"workflow:v3:{workflow_semantic_sha256[:24]}",
            f"WORKFLOW_ID_HASH:{workflow_id}",
        )
    enforce(
        all(count >= 1 for count in memberships.values()),
        "TRANSITION_UNLISTED_BY_WORKFLOW",
    )

    export_rows = require_list(surface.get("exports"), "INTERACTION_EXPORTS")
    for export in export_rows:
        export_id = export["export_id"]
        enforce(set(export) == EXPORT_KEYS, f"EXPORT_KEYS:{export_id}")
        validate_synthetic_fact_boundary(export, "EXPORT")
        enforce(
            set(require_dict(export["presentation"], f"EXPORT_PRESENTATION:{export_id}"))
            == {"format", "theme"},
            f"EXPORT_PRESENTATION_KEYS:{export_id}",
        )
        workflow = workflows.get(export["workflow_id"])
        state = states.get(export["state_id"])
        composition = compositions.get(export["composition_revision_id"])
        enforce(
            workflow is not None and state is not None and composition is not None
            and export["pair_projection_policy_preserved"] is True,
            f"EXPORT_TRACE:{export_id}",
        )
        enforce(
            export["realm"] == expected_realm
            == workflow["realm"] == state["realm"] == composition["realm"],
            f"EXPORT_REALM:{export_id}",
        )
        enforce(
            export["state_id"] in workflow["state_ids"]
            and state["composition_revision_id"] == export["composition_revision_id"],
            f"EXPORT_WORKFLOW_STATE_COMPOSITION:{export_id}",
        )
        expected_realizations = {
            row["association_realization_id"] for row in composition["association_realizations"]
        }
        export_realizations = export["association_realization_ids"]
        enforce(
            len(export_realizations) == len(set(export_realizations))
            and set(export_realizations) == expected_realizations
            == set(workflow["association_realization_ids"]),
            f"EXPORT_REALIZATION_EXACT_SET:{export_id}",
        )
        expected_revisions = {
            row["association_revision_id"] for row in composition["association_realizations"]
        }
        export_revisions = export["association_revision_ids"]
        enforce(
            len(export_revisions) == len(set(export_revisions))
            and set(export_revisions) == expected_revisions
            == set(workflow["association_revision_ids"]),
            f"EXPORT_ASSOCIATION_EXACT_SET:{export_id}",
        )
        preservation_records = export["projection_preservation_records"]
        for record in preservation_records:
            enforce(
                set(record) == PROJECTION_PRESERVATION_KEYS,
                f"EXPORT_PROJECTION_RECORD_KEYS:{export_id}",
            )
        preserve_ids = [row["association_realization_id"] for row in preservation_records]
        enforce(
            len(preserve_ids) == len(set(preserve_ids))
            and set(preserve_ids) == expected_realizations,
            f"EXPORT_PROJECTION_RECORD_SET:{export_id}",
        )
        for record in preservation_records:
            realization = realizations.get(record["association_realization_id"])
            association = associations.get(record["association_revision_id"])
            enforce(
                realization is not None and association is not None
                and realization["association_revision_id"] == record["association_revision_id"]
                and realization["realization_kind"] == record["realization_kind"]
                and association["pair_projection_policy"] == record["pair_projection_policy"],
                f"EXPORT_PROJECTION_RECORD_TRACE:{export_id}",
            )
        export_semantic = binding_material(
            hash_contract, "EXPORT", "export_semantic", export
        )
        export_semantic_sha256 = semantic_digest(export_semantic)
        enforce(
            export["semantic_sha256"] == export_semantic_sha256,
            f"EXPORT_SEMANTIC_HASH:{export_id}",
        )
        enforce(
            export_id == f"export:v3:{export_semantic_sha256[:24]}",
            f"EXPORT_ID_HASH:{export_id}",
        )
        export_presentation = binding_material(
            hash_contract, "EXPORT", "export_presentation", export
        )
        enforce(
            export["presentation_sha256"] == semantic_digest(export_presentation),
            f"EXPORT_PRESENTATION_HASH:{export_id}",
        )

    enforce(not transition_rows, "TRANSITION_SURFACE_DISALLOWED")


def validate_runtime_model(
    model: dict[str, Any],
    fixture: dict[str, Any],
    fixture_info: dict[str, Any],
    round16a: dict[str, Any],
    hash_contract: dict[str, Any],
) -> dict[str, Any]:
    enforce(
        set(model)
        == {
            "active_product", "api_version", "baseline_reconciliation", "capabilities",
            "closure_flags", "contract_version", "fact_boundary", "read_model_version",
            "research_controls", "source_authority",
        },
        "READ_MODEL_TOP_LEVEL_KEYS",
    )
    enforce(model["api_version"] == API_VERSION, "READ_MODEL_API_VERSION")
    enforce(model["contract_version"] == CONTRACT_VERSION, "READ_MODEL_CONTRACT_VERSION")
    enforce(model["read_model_version"] == READ_MODEL_VERSION, "READ_MODEL_VERSION")
    enforce(model["closure_flags"] == EXPECTED_CLOSURE, "READ_MODEL_CLOSURE")
    enforce(
        model["fact_boundary"]
        == {
            "active_product_policy": "FINAL_PRODUCTION_AUTHORITY_AND_ALL_GATES_REQUIRED",
            "current_status": "FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS",
            "inquiry_or_pending_records_are_active_facts": False,
            "synthetic_controls_are_active_facts": False,
        },
        "READ_MODEL_FACT_BOUNDARY",
    )
    enforce(
        model["source_authority"]
        == {
            "authorized_round16a_source_sha": SOURCE_SHA,
            "semantic_contract_namespace": SEMANTIC_NAMESPACE,
            "semantic_contract_parent_sha": SEMANTIC_PARENT_SHA,
            "semantic_contract_source_sha": SOURCE_SHA,
        },
        "READ_MODEL_SOURCE_AUTHORITY",
    )

    active = require_dict(model.get("active_product"), "ACTIVE_PRODUCT_SURFACE")
    controls = require_dict(model.get("research_controls"), "RESEARCH_CONTROL_SURFACE")
    enforce(set(active) == SURFACE_COLLECTIONS, "ACTIVE_PRODUCT_COLLECTION_KEYS")
    enforce(set(controls) == SURFACE_COLLECTIONS, "RESEARCH_CONTROL_COLLECTION_KEYS")
    for name in sorted(SURFACE_COLLECTIONS):
        enforce(require_list(active[name], f"ACTIVE_COLLECTION:{name}") == [], f"ACTIVE_PRODUCT_NOT_EMPTY:{name}")
        require_list(controls[name], f"CONTROL_COLLECTION:{name}")
    expected_lengths = {
        "scopes": 6,
        "concepts": 21,
        "concept_senses": 21,
        "associations": 14,
        "incidences": 37,
        "association_realizations": 10,
        "composition_coherence_reviews": 2,
        "compositions": 2,
        "navigation_states": 1,
        "workflows": 1,
        "exports": 1,
        "transitions": 0,
    }
    enforce({key: len(controls[key]) for key in SURFACE_COLLECTIONS} == expected_lengths, "CONTROL_COLLECTION_COUNTS")
    for name in SURFACE_COLLECTIONS:
        for row in controls[name]:
            validate_synthetic_fact_boundary(row, f"CONTROL_{name.upper()}")
    validate_interaction_surface_independent(controls, hash_contract)

    association_by_revision = fixture_info["association_by_revision"]
    model_associations = index_unique(controls["associations"], "association_revision_id", "MODEL_ASSOCIATION")
    enforce(set(model_associations) == set(association_by_revision), "MODEL_ASSOCIATION_ID_SET")
    for revision_id, source in association_by_revision.items():
        enforce(
            all(
                participant["participant_scope_id"] == model_associations[revision_id]["scope"]["scope_id"]
                for participant in model_associations[revision_id]["participants"]
            ),
            f"PARTICIPANT_SCOPE_DIVERGENCE:{revision_id}",
        )
        enforce(model_associations[revision_id] == expected_association_dto(source), f"MODEL_ASSOCIATION_PROJECTION:{revision_id}")

    expected_scopes = {
        source["scope_id"]: {**source, "realm": "SYNTHETIC_CONTROL", "fact_boundary": synthetic_fact_boundary()}
        for source in fixture["scopes"]
    }
    model_scopes = index_unique(controls["scopes"], "scope_id", "MODEL_SCOPE")
    enforce(model_scopes == expected_scopes, "MODEL_SCOPE_PROJECTION")
    expected_concepts = {
        source["concept_id"]: {**source, "fact_boundary": synthetic_fact_boundary()}
        for source in fixture["concepts"]
    }
    model_concepts = index_unique(controls["concepts"], "concept_id", "MODEL_CONCEPT")
    enforce(model_concepts == expected_concepts, "MODEL_CONCEPT_PROJECTION")
    expected_senses = {
        source["sense_id"]: {**source, "fact_boundary": synthetic_fact_boundary()}
        for source in fixture["concept_senses"]
    }
    model_senses = index_unique(controls["concept_senses"], "sense_id", "MODEL_SENSE")
    enforce(model_senses == expected_senses, "MODEL_SENSE_PROJECTION")

    expected_incidences: dict[str, dict[str, Any]] = {}
    for association in fixture["associations"]:
        for participant in association["participants"]:
            expected_incidences[participant["incidence_id"]] = {
                **participant,
                "association_id": association["association_id"],
                "association_kind": association["association_kind"],
                "association_revision_id": association["association_revision_id"],
                "fact_boundary": synthetic_fact_boundary(),
            }
    model_incidences = index_unique(controls["incidences"], "incidence_id", "MODEL_INCIDENCE")
    enforce(model_incidences == expected_incidences, "MODEL_INCIDENCE_PROJECTION")

    expected_realizations: dict[str, dict[str, Any]] = {}
    for composition in fixture["compositions"]:
        for realization in composition["association_realizations"]:
            association = association_by_revision[realization["association_revision_id"]]
            expected_realizations[realization["association_realization_id"]] = {
                **realization,
                "association_id": association["association_id"],
                "association_kind": association["association_kind"],
                "composition_id": composition["composition_id"],
                "composition_revision_id": composition["composition_revision_id"],
                "fact_boundary": synthetic_fact_boundary(),
            }
    model_realizations = index_unique(
        controls["association_realizations"], "association_realization_id", "MODEL_REALIZATION"
    )
    enforce(model_realizations == expected_realizations, "MODEL_REALIZATION_PROJECTION")
    for realization in model_realizations.values():
        if realization["association_kind"] == "PAIR":
            enforce(realization["realization_kind"] == "PAIR_EDGE", "MODEL_PAIR_REALIZATION_KIND")
        else:
            enforce(realization["realization_kind"] != "PAIR_EDGE", "MODEL_HYPEREDGE_PAIR_PROJECTION")
            source = association_by_revision[realization["association_revision_id"]]
            enforce(
                set(realization["realized_incidence_ids"])
                == {row["incidence_id"] for row in source["participants"]},
                "MODEL_HYPEREDGE_SUBSET_REALIZATION",
            )

    expected_reviews = {
        source["composition_coherence_review_id"]: {**source, "fact_boundary": synthetic_fact_boundary()}
        for source in fixture["composition_coherence_reviews"]
    }
    model_reviews = index_unique(
        controls["composition_coherence_reviews"], "composition_coherence_review_id", "MODEL_REVIEW"
    )
    enforce(model_reviews == expected_reviews, "MODEL_REVIEW_PROJECTION")

    review_by_id = fixture_info["review_by_id"]
    expected_compositions = {
        source["composition_revision_id"]: expected_composition_dto(
            source, review_by_id[source["global_coherence_review_id"]], association_by_revision
        )
        for source in fixture["compositions"]
    }
    model_compositions = index_unique(
        controls["compositions"], "composition_revision_id", "MODEL_COMPOSITION"
    )
    enforce(model_compositions == expected_compositions, "MODEL_COMPOSITION_PROJECTION")

    for collection, source_collection, identity_key in (
        ("navigation_states", "navigation_states", "state_id"),
        ("workflows", "workflows", "workflow_id"),
        ("exports", "exports", "export_id"),
    ):
        expected = {
            source[identity_key]: {**source, "fact_boundary": synthetic_fact_boundary()}
            for source in fixture[source_collection]
        }
        observed = index_unique(controls[collection], identity_key, f"MODEL_{collection.upper()}")
        enforce(observed == expected, f"MODEL_PROJECTION:{collection}")

    association_ids = {row["association_id"] for row in controls["associations"]}
    composition_ids = {row["composition_id"] for row in controls["compositions"]}
    enforce(association_ids.isdisjoint(composition_ids), "ASSOCIATION_COMPOSITION_ID_COLLISION")

    capabilities = require_dict(model.get("capabilities"), "READ_MODEL_CAPABILITIES")
    expected_count_capabilities = {
        "active_product_scope_count": 0,
        "active_product_concept_count": 0,
        "active_product_sense_count": 0,
        "active_product_association_count": 0,
        "active_product_incidence_count": 0,
        "active_product_realization_count": 0,
        "active_product_coherence_review_count": 0,
        "active_product_composition_count": 0,
        "active_product_navigation_state_count": 0,
        "active_product_workflow_count": 0,
        "active_product_export_count": 0,
        "active_product_transition_count": 0,
        "control_scope_count": 6,
        "control_concept_count": 21,
        "control_sense_count": 21,
        "control_association_count": 14,
        "control_pair_association_count": 9,
        "control_higher_order_association_count": 5,
        "control_incidence_count": 37,
        "control_realization_count": 10,
        "control_coherence_review_count": 2,
        "control_composition_count": 2,
        "control_navigation_state_count": 1,
        "control_workflow_count": 1,
        "control_export_count": 1,
        "control_transition_count": 0,
        "production_activation_count": 0,
    }
    for key, expected in expected_count_capabilities.items():
        enforce(capabilities.get(key) == expected, f"CAPABILITY_COUNT:{key}")
    enforce(capabilities.get("association_and_composition_identity_separate") is True, "CAPABILITY_IDENTITY_SEPARATION")
    enforce(capabilities.get("higher_order_associations_supported") is True, "CAPABILITY_HIGHER_ORDER")
    enforce(capabilities.get("implicit_pair_projection_allowed") is False, "CAPABILITY_IMPLICIT_PROJECTION")
    enforce(capabilities.get("product_activation_available") is False, "CAPABILITY_PRODUCT_ACTIVATION")
    enforce(capabilities.get("research_controls_only") is True, "CAPABILITY_RESEARCH_ONLY")
    enforce(capabilities.get("governed_product_arity_bound") is None, "CAPABILITY_ARITY_BOUND")
    enforce(
        capabilities.get("backend_association_arity_support")
        == "PAIR_2_OR_HIGHER_ORDER_3_PLUS_NO_FIXED_SCHEMA_MAXIMUM",
        "CAPABILITY_BACKEND_ARITY",
    )
    enforce(capabilities.get("transitions_available") is False, "CAPABILITY_TRANSITIONS_AVAILABLE")
    enforce(capabilities.get("transition_derivation_policy") == "NONE_NO_V2_INHERITANCE", "CAPABILITY_TRANSITION_DERIVATION")
    enforce(
        capabilities.get("transition_status") == "FAIL_CLOSED_NO_ACTIVE_PRODUCT_STATE_GRAPH",
        "CAPABILITY_TRANSITION_STATUS",
    )
    enforce(capabilities.get("supported_association_kinds") == ["PAIR", "HIGHER_ORDER"], "CAPABILITY_ASSOCIATION_KINDS")
    derived_active_pending_review_count = sum(
        row["eligibility"]["lifecycle_state"] == "ACTIVE"
        and (
            row["review"]["review_state"] != "FINAL"
            or row["review"]["authority_state"] != "FINAL"
        )
        for row in active["associations"]
    )
    all_associations = [*active["associations"], *controls["associations"]]
    all_realizations = [
        *active["association_realizations"], *controls["association_realizations"]
    ]
    derived_implicit_hyperedge_projection_count = sum(
        row["association_kind"] == "HIGHER_ORDER"
        and (
            row["pair_projection_policy"] != "NONE"
            or any(
                realization["association_revision_id"] == row["association_revision_id"]
                and realization["realization_kind"] == "PAIR_EDGE"
                for realization in all_realizations
            )
        )
        for row in all_associations
    )
    enforce(
        capabilities.get("active_pending_review_count")
        == derived_active_pending_review_count,
        "CAPABILITY_ACTIVE_PENDING_REVIEW_DERIVED",
    )
    enforce(
        capabilities.get("implicit_hyperedge_projection_count")
        == derived_implicit_hyperedge_projection_count,
        "CAPABILITY_IMPLICIT_PROJECTION_DERIVED",
    )
    enforce(capabilities.get("read_paths") == EXPECTED_READ_PATHS, "CAPABILITY_READ_PATH_PARITY")

    baseline_expected = {
        "active_fact_created_count": round16a["active_fact_created_count"],
        "authority_base_sha": round16a["authority_base_sha"],
        "closure": round16a["closure"],
        "main_object_distributions": round16a["main_object_distributions"],
        "main_object_total_distribution": round16a["main_object_total_distribution"],
        "pair_projection_created_count": round16a["pair_projection_created_count"],
        "product_activation_count": round16a["product_activation_count"],
        "reconciled_row_count_including_topology_audit_records": round16a[
            "reconciled_row_count_including_topology_audit_records"
        ],
        "status": round16a["status"],
        "transition_count": round16a["transition_count"],
        "transition_outcome_distribution": round16a["transition_outcome_distribution"],
    }
    enforce(model["baseline_reconciliation"] == baseline_expected, "READ_MODEL_BASELINE_RECONCILIATION")
    return {
        "capabilities": capabilities,
        "collection_counts": expected_lengths,
        "association_count": len(model_associations),
        "composition_count": len(model_compositions),
    }


def validate_census(census: dict[str, Any], fixture_info: dict[str, Any]) -> None:
    enforce(census.get("source_sha") == SOURCE_SHA, "CENSUS_SOURCE_SHA")
    enforce(census.get("parent_checkpoint_sha") == SEMANTIC_PARENT_SHA, "CENSUS_PARENT_SHA")
    enforce(census.get("contract_version") == CONTRACT_VERSION, "CENSUS_CONTRACT_VERSION")
    enforce(census.get("count_taxonomy") == fixture_info["taxonomy"], "CENSUS_COUNT_TAXONOMY")
    enforce(
        census.get("count_taxonomy_canonical_sha256") == semantic_digest(fixture_info["taxonomy"]),
        "CENSUS_COUNT_TAXONOMY_HASH",
    )
    enforce(census.get("count_taxonomy_reconstruction_status") == "PASS", "CENSUS_RECONSTRUCTION_STATUS")
    enforce(census.get("governed_scope_count") == 6, "CENSUS_SCOPE_COUNT")
    enforce(census.get("governed_concept_count") == 21, "CENSUS_CONCEPT_COUNT")
    enforce(census.get("governed_concept_sense_count") == 21, "CENSUS_SENSE_COUNT")
    enforce(census.get("composition_coherence_review_count") == 2, "CENSUS_REVIEW_COUNT")
    enforce(census.get("production_activation_count") == 0, "CENSUS_PRODUCTION_ACTIVATION")
    enforce(census.get("production_active_concept_count") == 0, "CENSUS_PRODUCTION_CONCEPT")
    enforce(census.get("production_active_concept_sense_count") == 0, "CENSUS_PRODUCTION_SENSE")
    enforce(census.get("production_active_pending_review_count") == 0, "CENSUS_ACTIVE_PENDING")
    enforce(census.get("production_product_eligible_count") == 0, "CENSUS_PRODUCT_ELIGIBLE")
    enforce(census.get("implicit_pair_projection_count") == 0, "CENSUS_IMPLICIT_PROJECTION")
    enforce(census.get("closure_true_count") == 0, "CENSUS_CLOSURE_TRUE")
    enforce(census.get("synthetic_fixture_validation_status") == "PASS", "CENSUS_FIXTURE_STATUS")


def expected_input_bindings(input_hashes: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"path": path.as_posix(), "sha256": input_hashes[path.as_posix()]}
        for path in (FIXTURE_REL, CENSUS_REL, HASH_CONTRACT_REL, ROUND16A_REL)
    ]


def validate_manifest_and_hashes(
    model: dict[str, Any],
    model_raw: bytes,
    manifest: dict[str, Any],
    manifest_raw: bytes,
    checksums_raw: bytes,
    input_hashes: dict[str, str],
    capabilities: dict[str, Any],
    *,
    canonical_required: bool = True,
) -> None:
    enforce(
        set(manifest)
        == {
            "api_version", "artifact_bytes", "artifact_sha256", "canonical_serialization",
            "closure_flags", "counts", "deterministic_build_contract", "fact_boundary",
            "generator_version", "input_bindings", "manifest_version", "read_model_version",
            "source_sha",
        },
        "MANIFEST_TOP_LEVEL_KEYS",
    )
    if canonical_required:
        enforce(model_raw == canonical_json_bytes(model), "READ_MODEL_CANONICAL_BYTES")
        enforce(manifest_raw == canonical_json_bytes(manifest), "MANIFEST_CANONICAL_BYTES")
    enforce(manifest.get("api_version") == API_VERSION, "MANIFEST_API_VERSION")
    enforce(manifest.get("manifest_version") == MANIFEST_VERSION, "MANIFEST_VERSION")
    enforce(manifest.get("read_model_version") == READ_MODEL_VERSION, "MANIFEST_READ_MODEL_VERSION")
    enforce(manifest.get("source_sha") == SOURCE_SHA, "MANIFEST_SOURCE_SHA")
    enforce(manifest.get("canonical_serialization") == CANONICAL_SERIALIZATION, "MANIFEST_CANONICAL_POLICY")
    enforce(manifest.get("closure_flags") == EXPECTED_CLOSURE == model["closure_flags"], "MANIFEST_CLOSURE")
    enforce(manifest.get("fact_boundary") == model["fact_boundary"], "MANIFEST_FACT_BOUNDARY")
    enforce(manifest.get("counts") == capabilities, "MANIFEST_CAPABILITY_COUNTS")
    enforce(manifest.get("input_bindings") == expected_input_bindings(input_hashes), "MANIFEST_INPUT_BINDINGS")
    enforce(manifest.get("artifact_bytes") == {"read-model.json": len(model_raw)}, "MANIFEST_READ_MODEL_BYTES")
    enforce(
        manifest.get("artifact_sha256") == {"read-model.json": sha256_bytes(model_raw)},
        "MANIFEST_READ_MODEL_SHA256",
    )
    expected_checksums = (
        f"{sha256_bytes(manifest_raw)}  manifest.json\n"
        f"{sha256_bytes(model_raw)}  read-model.json\n"
    ).encode("utf-8")
    enforce(checksums_raw == expected_checksums, "CHECKSUM_CONTENT")


def mutate_record(records: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    return next(row for row in records if row[key] == value)


def expect_rejection(
    probe_id: str,
    payload: Any,
    mutator: Callable[[Any], None],
    validator: Callable[[Any], None],
    expected_code: str,
) -> dict[str, Any]:
    mutant = copy.deepcopy(payload)
    mutator(mutant)
    try:
        validator(mutant)
    except VerificationError as error:
        observed = str(error)
        enforce(observed == expected_code or observed.startswith(f"{expected_code}:"), f"PROBE_WRONG_REJECTION:{probe_id}:{observed}")
        return {
            "probe_id": probe_id,
            "expected_error_code": expected_code,
            "observed_error_code": observed,
            "status": "PASS_REJECTED",
        }
    raise VerificationError(f"PROBE_UNEXPECTEDLY_ACCEPTED:{probe_id}")


def run_corruption_controls(
    fixture: dict[str, Any],
    control_ids: dict[str, Any],
    model: dict[str, Any],
    model_raw: bytes,
    manifest: dict[str, Any],
    manifest_raw: bytes,
    checksums_raw: bytes,
    input_hashes: dict[str, str],
    capabilities: dict[str, Any],
    census: dict[str, Any],
    round16a: dict[str, Any],
    hash_contract: dict[str, Any],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    def validate_controls(mutant: dict[str, Any]) -> None:
        validate_control_semantics(mutant)

    results.append(expect_rejection(
        "CORRUPT-ALL-PAIRS-INVALID-GROUP",
        fixture,
        lambda value: mutate_record(value["associations"], "association_revision_id", control_ids["clique_revision_id"])["review"].__setitem__("global_coherence", "PASS"),
        validate_controls,
        "CONTROL_ALL_PAIRS_INVALID_GROUP",
    ))
    results.append(expect_rejection(
        "CORRUPT-SPARSE-VALID-HYPEREDGE",
        fixture,
        lambda value: mutate_record(value["associations"], "association_revision_id", control_ids["sparse_revision_id"])["internal_pair_links"].append(
            copy.deepcopy(mutate_record(value["associations"], "association_revision_id", control_ids["sparse_revision_id"])["internal_pair_links"][0])
        ),
        validate_controls,
        "CONTROL_SPARSE_VALID_HYPEREDGE",
    ))
    results.append(expect_rejection(
        "CORRUPT-BOUNDED-SENSE-CONFLICT",
        fixture,
        lambda value: mutate_record(value["associations"], "association_revision_id", control_ids["bounded_revision_id"])["review"].__setitem__("bounded_senses_compatible", True),
        validate_controls,
        "CONTROL_BOUNDED_SENSE_CONFLICT",
    ))
    results.append(expect_rejection(
        "CORRUPT-CROSS-CASE-BUNDLE",
        fixture,
        lambda value: mutate_record(value["associations"], "association_revision_id", control_ids["cross_case_revision_id"])["review"].__setitem__("case_scope_compatible", True),
        validate_controls,
        "CONTROL_CROSS_CASE_BUNDLE",
    ))
    results.append(expect_rejection(
        "CORRUPT-ISOLATED-ACTIVE-TERM",
        fixture,
        lambda value: mutate_record(value["concepts"], "concept_id", control_ids["isolated_concept_id"]).__setitem__("lifecycle_state", "INQUIRY_ONLY"),
        validate_controls,
        "CONTROL_ISOLATED_ACTIVE_TERM",
    ))
    results.append(expect_rejection(
        "CORRUPT-RENDERABLE-NO-VALID-ASSOCIATION",
        fixture,
        lambda value: mutate_record(value["compositions"], "composition_revision_id", control_ids["renderable_composition_revision_id"]).__setitem__("product_eligible", True),
        validate_controls,
        "CONTROL_RENDERABLE_WITHOUT_VALID_ASSOCIATION",
    ))
    results.append(expect_rejection(
        "CORRUPT-IMPLICIT-HYPEREDGE-PROJECTION",
        fixture,
        lambda value: mutate_record(value["associations"], "association_revision_id", control_ids["sparse_revision_id"]).__setitem__("pair_projection_policy", "PROJECT_COMPLETE_GRAPH"),
        lambda value: validate_fixture_core(value, hash_contract),
        "IMPLICIT_HYPEREDGE_PROJECTION",
    ))
    results.append(expect_rejection(
        "CORRUPT-ACTIVE-PENDING-REVIEW",
        fixture,
        lambda value: mutate_record(value["associations"], "association_revision_id", control_ids["pending_revision_id"]).__setitem__("lifecycle_state", "ACTIVE"),
        validate_controls,
        "CONTROL_ACTIVE_PENDING_REVIEW",
    ))

    def clone_control_state(value: dict[str, Any]) -> dict[str, Any]:
        controls = value["research_controls"]
        cloned = copy.deepcopy(controls["navigation_states"][0])
        cloned["nodes"].reverse()
        cloned["path"] = [
            {
                "from_navigation_node_id": step["to_navigation_node_id"],
                "incidence_id": step["incidence_id"],
                "to_navigation_node_id": step["from_navigation_node_id"],
            }
            for step in reversed(cloned["path"])
        ]
        cloned["focus_navigation_node_id"] = cloned["path"][-1]["to_navigation_node_id"]
        semantic = binding_material(
            hash_contract, "NAVIGATION_STATE", "navigation_state_semantic", cloned
        )
        cloned["semantic_sha256"] = semantic_digest(semantic)
        cloned["state_id"] = f"state:v3:{cloned['semantic_sha256'][:24]}"
        cloned["presentation_sha256"] = semantic_digest(binding_material(
            hash_contract, "NAVIGATION_STATE", "navigation_state_presentation", cloned
        ))
        controls["navigation_states"].append(cloned)
        return cloned

    def add_control_transition(
        value: dict[str, Any], *, to_state_id: str | None = None
    ) -> dict[str, Any]:
        controls = value["research_controls"]
        source = controls["navigation_states"][0]
        target_id = to_state_id or source["state_id"]
        incidence = next(
            row for row in controls["incidences"]
            if row["incidence_id"] == source["path"][0]["incidence_id"]
        )
        realization = next(
            row for row in controls["association_realizations"]
            if row["composition_revision_id"] == source["composition_revision_id"]
            and row["association_revision_id"] == incidence["association_revision_id"]
            and incidence["incidence_id"] in row["realized_incidence_ids"]
        )
        transition = {
            "association_realization_id": realization["association_realization_id"],
            "association_revision_id": incidence["association_revision_id"],
            "fact_boundary": synthetic_fact_boundary(),
            "from_state_id": source["state_id"],
            "incidence_id": incidence["incidence_id"],
            "realm": "SYNTHETIC_CONTROL",
            "semantic_sha256": "",
            "state_mutated": source["state_id"] != target_id,
            "to_state_id": target_id,
            "transition_id": "",
            "transition_kind": "FOLLOW_INCIDENCE",
        }
        semantic = binding_material(
            hash_contract, "TRANSITION", "transition_semantic", transition
        )
        transition["semantic_sha256"] = semantic_digest(semantic)
        transition["transition_id"] = f"transition:v3:{transition['semantic_sha256'][:24]}"
        controls["transitions"].append(transition)
        return transition

    def refresh_transition(transition: dict[str, Any]) -> None:
        semantic = binding_material(
            hash_contract, "TRANSITION", "transition_semantic", transition
        )
        transition["semantic_sha256"] = semantic_digest(semantic)
        transition["transition_id"] = f"transition:v3:{transition['semantic_sha256'][:24]}"

    def refresh_export(export: dict[str, Any]) -> None:
        semantic = binding_material(hash_contract, "EXPORT", "export_semantic", export)
        export["semantic_sha256"] = semantic_digest(semantic)
        export["export_id"] = f"export:v3:{export['semantic_sha256'][:24]}"
        export["presentation_sha256"] = semantic_digest(binding_material(
            hash_contract, "EXPORT", "export_presentation", export
        ))

    def refresh_workflow_and_exports(value: dict[str, Any], workflow: dict[str, Any]) -> None:
        previous_id = workflow["workflow_id"]
        semantic = binding_material(hash_contract, "WORKFLOW", "workflow_semantic", workflow)
        workflow["semantic_sha256"] = semantic_digest(semantic)
        workflow["workflow_id"] = f"workflow:v3:{workflow['semantic_sha256'][:24]}"
        for export in value["research_controls"]["exports"]:
            if export["workflow_id"] == previous_id:
                export["workflow_id"] = workflow["workflow_id"]
                refresh_export(export)

    def mutate_interaction(value: dict[str, Any], case: str) -> None:
        controls = value["research_controls"]
        state = controls["navigation_states"][0]
        workflow = controls["workflows"][0]
        export = controls["exports"][0]
        if case == "STATE_KEYS":
            state["unexpected"] = True
        elif case == "NAVIGATION_NODE_KEYS":
            state["nodes"][0]["unexpected"] = True
        elif case == "NAVIGATION_PATH_STEP_KEYS":
            state["path"][0]["unexpected"] = True
        elif case == "STATE_PRESENTATION_KEYS":
            state["presentation"]["unexpected"] = True
        elif case == "WORKFLOW_KEYS":
            workflow["unexpected"] = True
        elif case == "EXPORT_KEYS":
            export["unexpected"] = True
        elif case == "EXPORT_PRESENTATION_KEYS":
            export["presentation"]["unexpected"] = True
        elif case == "EXPORT_PROJECTION_RECORD_KEYS":
            export["projection_preservation_records"][0]["unexpected"] = True
        elif case == "TRANSITION_KEYS":
            add_control_transition(value)["unexpected"] = True
        elif case == "STATE_NODE_COUNT":
            state["nodes"].pop()
        elif case == "STATE_PATH_EMPTY":
            state["path"] = []
        elif case == "STATE_PATH_DISCONTINUOUS":
            state["path"][1]["from_navigation_node_id"] = state["path"][1]["to_navigation_node_id"]
            state["path"][1]["to_navigation_node_id"] = state["path"][0]["to_navigation_node_id"]
        elif case == "STATE_TERMINAL_FOCUS":
            state["focus_navigation_node_id"] = state["path"][0]["from_navigation_node_id"]
        elif case == "STATE_CONCEPT_OUTSIDE_COMPOSITION":
            composition = next(
                row for row in controls["compositions"]
                if row["composition_revision_id"] == state["composition_revision_id"]
            )
            outside = next(
                row for row in controls["concepts"]
                if row["concept_id"] not in composition["composition_node_ids"]
            )
            next(row for row in state["nodes"] if row["node_kind"] == "CONCEPT")[
                "concept_id"
            ] = outside["concept_id"]
        elif case == "STATE_ASSOCIATION_OUTSIDE_COMPOSITION":
            composition = next(
                row for row in controls["compositions"]
                if row["composition_revision_id"] == state["composition_revision_id"]
            )
            inside = {
                row["association_revision_id"] for row in composition["association_realizations"]
            }
            outside = next(
                row for row in controls["associations"]
                if row["association_revision_id"] not in inside
            )
            next(row for row in state["nodes"] if row["node_kind"] == "ASSOCIATION")[
                "association_revision_id"
            ] = outside["association_revision_id"]
        elif case == "STATE_COMPOSITION_REALM":
            state["realm"] = "PRODUCTION"
        elif case == "STATE_MISSING_COMPOSITION":
            state["composition_revision_id"] = "composition-revision:v3:missing"
        elif case == "STATE_BIPARTITE_FLAG":
            state["bipartite_alternation_valid"] = False
        elif case == "STATE_FOCUS":
            state["focus_navigation_node_id"] = "navigation-node:v3:missing"
        elif case == "STATE_DUPLICATE_NODE":
            state["nodes"].append(copy.deepcopy(state["nodes"][0]))
        elif case == "STATE_DISCRIMINATOR_REFERENCE":
            concept_node = next(row for row in state["nodes"] if row["node_kind"] == "CONCEPT")
            concept_node["association_revision_id"] = controls["associations"][0]["association_revision_id"]
        elif case == "STATE_PATH_REFERENCE":
            state["path"][0]["to_navigation_node_id"] = "navigation-node:v3:missing"
        elif case == "STATE_WRONG_INCIDENCE":
            current = state["path"][0]["incidence_id"]
            state["path"][0]["incidence_id"] = next(
                row["incidence_id"] for row in controls["incidences"]
                if row["incidence_id"] != current
            )
        elif case == "STATE_SEMANTIC_HASH":
            state["semantic_sha256"] = "0" * 64
        elif case == "STATE_PRESENTATION_HASH":
            state["presentation_sha256"] = "0" * 64
        elif case == "STATE_ID_HASH":
            state["state_id"] = "state:v3:000000000000000000000000"
        elif case == "STATE_FACT_BOUNDARY":
            state["fact_boundary"]["unexpected"] = True
        elif case == "WORKFLOW_INITIAL_STATE_MEMBERSHIP":
            workflow["state_ids"] = []
        elif case == "WORKFLOW_STATE_REALM":
            workflow["realm"] = "PRODUCTION"
        elif case == "WORKFLOW_REALIZATION_EXACT_SET":
            workflow["association_realization_ids"].pop()
        elif case == "WORKFLOW_ASSOCIATION_EXACT_SET":
            workflow["association_revision_ids"].pop()
        elif case == "WORKFLOW_REACHABILITY":
            second = clone_control_state(value)
            workflow["state_ids"].append(second["state_id"])
        elif case == "WORKFLOW_MISSING_STATE":
            workflow["state_ids"].append("state:v3:missing")
        elif case == "WORKFLOW_DUPLICATE_STATE":
            workflow["state_ids"].append(workflow["state_ids"][0])
        elif case == "WORKFLOW_INVALID_KIND":
            workflow["transition_kind"] = "INVALID_KIND"
        elif case == "WORKFLOW_DUPLICATE_REALIZATION":
            workflow["association_realization_ids"].append(
                workflow["association_realization_ids"][0]
            )
        elif case == "WORKFLOW_DUPLICATE_REVISION":
            workflow["association_revision_ids"].append(
                workflow["association_revision_ids"][0]
            )
        elif case == "WORKFLOW_SEMANTIC_HASH":
            workflow["semantic_sha256"] = "0" * 64
        elif case == "WORKFLOW_ID_HASH":
            workflow["workflow_id"] = "workflow:v3:000000000000000000000000"
        elif case == "WORKFLOW_FACT_BOUNDARY":
            workflow["fact_boundary"]["unexpected"] = True
        elif case == "WORKFLOW_FOREIGN_TRANSITION":
            workflow["transition_ids"] = ["transition:v3:missing"]
        elif case == "WORKFLOW_DUPLICATE_TRANSITION":
            transition = add_control_transition(value)
            workflow["transition_ids"] = [transition["transition_id"], transition["transition_id"]]
        elif case == "WORKFLOW_SELECTED_TRANSITION_SCOPE":
            second = clone_control_state(value)
            transition = add_control_transition(value, to_state_id=second["state_id"])
            workflow["transition_ids"] = [transition["transition_id"]]
        elif case == "WORKFLOW_SELECTED_SUBSET_REACHABILITY":
            second = clone_control_state(value)
            selected = add_control_transition(value)
            add_control_transition(value, to_state_id=second["state_id"])
            workflow["state_ids"].append(second["state_id"])
            workflow["transition_ids"] = [selected["transition_id"]]
        elif case == "TRANSITION_REALM":
            add_control_transition(value)["realm"] = "PRODUCTION"
        elif case == "TRANSITION_ENDPOINT":
            transition = add_control_transition(value)
            transition["to_state_id"] = "state:v3:missing-endpoint"
            transition["state_mutated"] = True
        elif case == "TRANSITION_UNLISTED_BY_WORKFLOW":
            add_control_transition(value)
        elif case == "TRANSITION_TRACE":
            transition = add_control_transition(value)
            transition["association_revision_id"] = next(
                row["association_revision_id"] for row in controls["associations"]
                if row["association_revision_id"] != transition["association_revision_id"]
            )
        elif case == "TRANSITION_STATE_MUTATED":
            add_control_transition(value)["state_mutated"] = True
        elif case == "TRANSITION_TRACE_PARTIAL":
            add_control_transition(value)["association_realization_id"] = None
        elif case == "TRANSITION_DUPLICATE_ID":
            first = add_control_transition(value)
            second = add_control_transition(value)
            second["transition_id"] = first["transition_id"]
        elif case == "TRANSITION_INVALID_KIND":
            add_control_transition(value)["transition_kind"] = "INVALID_KIND"
        elif case == "TRANSITION_SEMANTIC_HASH":
            add_control_transition(value)["semantic_sha256"] = "0" * 64
        elif case == "TRANSITION_ID_HASH":
            add_control_transition(value)["transition_id"] = "transition:v3:000000000000000000000000"
        elif case == "TRANSITION_FACT_BOUNDARY":
            add_control_transition(value)["fact_boundary"]["unexpected"] = True
        elif case == "TRANSITION_SURFACE_DISALLOWED":
            transition = add_control_transition(value)
            workflow["transition_ids"] = [transition["transition_id"]]
            refresh_workflow_and_exports(value, workflow)
        elif case == "WORKFLOW_SHARED_STATE":
            follow = add_control_transition(value)
            move = add_control_transition(value)
            move["transition_kind"] = "MOVE_FOCUS"
            move["incidence_id"] = None
            move["association_revision_id"] = None
            move["association_realization_id"] = None
            refresh_transition(move)
            workflow["transition_ids"] = [follow["transition_id"]]
            refresh_workflow_and_exports(value, workflow)
            shared = copy.deepcopy(workflow)
            shared["transition_kind"] = "MOVE_FOCUS"
            shared["transition_ids"] = [move["transition_id"]]
            semantic = binding_material(hash_contract, "WORKFLOW", "workflow_semantic", shared)
            shared["semantic_sha256"] = semantic_digest(semantic)
            shared["workflow_id"] = f"workflow:v3:{shared['semantic_sha256'][:24]}"
            controls["workflows"].append(shared)
        elif case == "EXPORT_REALM":
            export["realm"] = "PRODUCTION"
        elif case == "EXPORT_REALIZATION_EXACT_SET":
            export["association_realization_ids"].pop()
        elif case == "EXPORT_ASSOCIATION_EXACT_SET":
            export["association_revision_ids"].pop()
        elif case == "EXPORT_MISSING_REFERENCES":
            export["workflow_id"] = "workflow:v3:missing"
        elif case == "EXPORT_COMPOSITION_MISMATCH":
            export["composition_revision_id"] = next(
                row["composition_revision_id"] for row in controls["compositions"]
                if row["composition_revision_id"] != export["composition_revision_id"]
            )
        elif case == "EXPORT_FALSE_FLAG":
            export["pair_projection_policy_preserved"] = False
        elif case == "EXPORT_INCOMPLETE_RECORDS":
            export["projection_preservation_records"].pop()
        elif case == "EXPORT_INCORRECT_RECORD":
            export["projection_preservation_records"][0]["realization_kind"] = "INVALID_KIND"
        elif case == "EXPORT_SEMANTIC_HASH":
            export["semantic_sha256"] = "0" * 64
        elif case == "EXPORT_PRESENTATION_HASH":
            export["presentation_sha256"] = "0" * 64
        elif case == "EXPORT_ID_HASH":
            export["export_id"] = "export:v3:000000000000000000000000"
        elif case == "EXPORT_FACT_BOUNDARY":
            export["fact_boundary"]["unexpected"] = True
        else:
            raise VerificationError(f"UNKNOWN_INTERACTION_MUTATION:{case}")

    interaction_probes = (
        ("CORRUPT-RUNTIME-STATE-DTO-KEYS", "STATE_KEYS", "STATE_KEYS"),
        ("CORRUPT-RUNTIME-NAVIGATION-NODE-DTO-KEYS", "NAVIGATION_NODE_KEYS", "NAVIGATION_NODE_KEYS"),
        ("CORRUPT-RUNTIME-PATH-STEP-DTO-KEYS", "NAVIGATION_PATH_STEP_KEYS", "NAVIGATION_PATH_STEP_KEYS"),
        ("CORRUPT-RUNTIME-STATE-PRESENTATION-DTO-KEYS", "STATE_PRESENTATION_KEYS", "STATE_PRESENTATION_KEYS"),
        ("CORRUPT-RUNTIME-WORKFLOW-DTO-KEYS", "WORKFLOW_KEYS", "WORKFLOW_KEYS"),
        ("CORRUPT-RUNTIME-EXPORT-DTO-KEYS", "EXPORT_KEYS", "EXPORT_KEYS"),
        ("CORRUPT-RUNTIME-EXPORT-PRESENTATION-DTO-KEYS", "EXPORT_PRESENTATION_KEYS", "EXPORT_PRESENTATION_KEYS"),
        ("CORRUPT-RUNTIME-PROJECTION-RECORD-DTO-KEYS", "EXPORT_PROJECTION_RECORD_KEYS", "EXPORT_PROJECTION_RECORD_KEYS"),
        ("CORRUPT-RUNTIME-TRANSITION-DTO-KEYS", "TRANSITION_KEYS", "TRANSITION_KEYS"),
        ("CORRUPT-RUNTIME-STATE-NODE-COUNT", "STATE_NODE_COUNT", "STATE_NODE_COUNT"),
        ("CORRUPT-RUNTIME-STATE-PATH-EMPTY", "STATE_PATH_EMPTY", "STATE_PATH_EMPTY"),
        ("CORRUPT-RUNTIME-STATE-PATH-DISCONTINUOUS", "STATE_PATH_DISCONTINUOUS", "STATE_PATH_DISCONTINUOUS"),
        ("CORRUPT-RUNTIME-STATE-TERMINAL-FOCUS", "STATE_TERMINAL_FOCUS", "STATE_TERMINAL_FOCUS"),
        ("CORRUPT-RUNTIME-STATE-CONCEPT-MEMBERSHIP", "STATE_CONCEPT_OUTSIDE_COMPOSITION", "STATE_NODE_OUTSIDE_COMPOSITION"),
        ("CORRUPT-RUNTIME-STATE-ASSOCIATION-MEMBERSHIP", "STATE_ASSOCIATION_OUTSIDE_COMPOSITION", "STATE_NODE_OUTSIDE_COMPOSITION"),
        ("CORRUPT-RUNTIME-STATE-COMPOSITION-REALM", "STATE_COMPOSITION_REALM", "STATE_COMPOSITION_REALM"),
        ("CORRUPT-RUNTIME-WORKFLOW-INITIAL-STATE", "WORKFLOW_INITIAL_STATE_MEMBERSHIP", "WORKFLOW_INITIAL_STATE_MEMBERSHIP"),
        ("CORRUPT-RUNTIME-WORKFLOW-STATE-REALM", "WORKFLOW_STATE_REALM", "WORKFLOW_STATE_REALM"),
        ("CORRUPT-RUNTIME-WORKFLOW-REALIZATION-SET", "WORKFLOW_REALIZATION_EXACT_SET", "WORKFLOW_REALIZATION_EXACT_SET"),
        ("CORRUPT-RUNTIME-WORKFLOW-ASSOCIATION-SET", "WORKFLOW_ASSOCIATION_EXACT_SET", "WORKFLOW_ASSOCIATION_EXACT_SET"),
        ("CORRUPT-RUNTIME-WORKFLOW-REACHABILITY", "WORKFLOW_REACHABILITY", "WORKFLOW_REACHABILITY"),
        ("CORRUPT-RUNTIME-TRANSITION-REALM", "TRANSITION_REALM", "TRANSITION_REALM"),
        ("CORRUPT-RUNTIME-TRANSITION-ENDPOINT", "TRANSITION_ENDPOINT", "TRANSITION_ENDPOINT"),
        ("WORKFLOW_UNLISTED_TRANSITION", "TRANSITION_UNLISTED_BY_WORKFLOW", "TRANSITION_UNLISTED_BY_WORKFLOW"),
        ("CORRUPT-RUNTIME-TRANSITION-TRACE", "TRANSITION_TRACE", "TRANSITION_TRACE"),
        ("CORRUPT-RUNTIME-TRANSITION-STATE-MUTATED", "TRANSITION_STATE_MUTATED", "TRANSITION_STATE_MUTATED"),
        ("CORRUPT-RUNTIME-TRANSITION-PARTIAL-TRACE", "TRANSITION_TRACE_PARTIAL", "TRANSITION_TRACE_PARTIAL"),
        ("CORRUPT-RUNTIME-TRANSITION-SURFACE", "TRANSITION_SURFACE_DISALLOWED", "TRANSITION_SURFACE_DISALLOWED"),
        ("CORRUPT-RUNTIME-EXPORT-REALM", "EXPORT_REALM", "EXPORT_REALM"),
        ("CORRUPT-RUNTIME-EXPORT-REALIZATION-SET", "EXPORT_REALIZATION_EXACT_SET", "EXPORT_REALIZATION_EXACT_SET"),
        ("CORRUPT-RUNTIME-EXPORT-ASSOCIATION-SET", "EXPORT_ASSOCIATION_EXACT_SET", "EXPORT_ASSOCIATION_EXACT_SET"),
        ("STATE_MISSING_COMPOSITION", "STATE_MISSING_COMPOSITION", "STATE_COMPOSITION"),
        ("STATE_FALSE_BIPARTITE", "STATE_BIPARTITE_FLAG", "STATE_BIPARTITE_FLAG"),
        ("STATE_MISSING_FOCUS", "STATE_FOCUS", "STATE_FOCUS"),
        ("STATE_DUPLICATE_NODES", "STATE_DUPLICATE_NODE", "NAVIGATION_NODE_DUPLICATE"),
        ("STATE_BAD_DISCRIMINATOR_REFERENCE", "STATE_DISCRIMINATOR_REFERENCE", "STATE_NODE_OUTSIDE_COMPOSITION"),
        ("STATE_BAD_PATH_REFERENCE", "STATE_PATH_REFERENCE", "STATE_PATH_REFERENCE"),
        ("STATE_WRONG_INCIDENCE", "STATE_WRONG_INCIDENCE", "STATE_PATH_INCIDENCE_TRACE"),
        ("STATE_SEMANTIC_HASH", "STATE_SEMANTIC_HASH", "STATE_SEMANTIC_HASH"),
        ("STATE_PRESENTATION_HASH", "STATE_PRESENTATION_HASH", "STATE_PRESENTATION_HASH"),
        ("STATE_ID_HASH", "STATE_ID_HASH", "STATE_ID_HASH"),
        ("STATE_FACT_BOUNDARY_EXTRA_KEY", "STATE_FACT_BOUNDARY", "STATE:FACT_BOUNDARY_KEYS"),
        ("WORKFLOW_MISSING_STATE", "WORKFLOW_MISSING_STATE", "WORKFLOW_STATE_SET"),
        ("WORKFLOW_DUPLICATE_STATE", "WORKFLOW_DUPLICATE_STATE", "WORKFLOW_STATE_SET"),
        ("WORKFLOW_INVALID_KIND", "WORKFLOW_INVALID_KIND", "WORKFLOW_TRANSITION_KIND"),
        ("WORKFLOW_DUPLICATE_REALIZATION", "WORKFLOW_DUPLICATE_REALIZATION", "WORKFLOW_REALIZATION_EXACT_SET"),
        ("WORKFLOW_DUPLICATE_REVISION", "WORKFLOW_DUPLICATE_REVISION", "WORKFLOW_ASSOCIATION_EXACT_SET"),
        ("WORKFLOW_SEMANTIC_HASH", "WORKFLOW_SEMANTIC_HASH", "WORKFLOW_SEMANTIC_HASH"),
        ("WORKFLOW_ID_HASH", "WORKFLOW_ID_HASH", "WORKFLOW_ID_HASH"),
        ("WORKFLOW_FACT_BOUNDARY_EXTRA_KEY", "WORKFLOW_FACT_BOUNDARY", "WORKFLOW:FACT_BOUNDARY_KEYS"),
        ("WORKFLOW_FOREIGN_TRANSITION_SELECTION", "WORKFLOW_FOREIGN_TRANSITION", "WORKFLOW_TRANSITION_REFERENCE"),
        ("WORKFLOW_DUPLICATE_TRANSITION_SELECTION", "WORKFLOW_DUPLICATE_TRANSITION", "WORKFLOW_TRANSITION_IDS_DUPLICATE"),
        ("WORKFLOW_SELECTED_TRANSITION_FOREIGN_STATE", "WORKFLOW_SELECTED_TRANSITION_SCOPE", "WORKFLOW_SELECTED_TRANSITION_SCOPE"),
        ("WORKFLOW_REACHABILITY_USES_EXACT_SELECTED_SUBSET", "WORKFLOW_SELECTED_SUBSET_REACHABILITY", "WORKFLOW_REACHABILITY"),
        ("WORKFLOW_SHARED_STATE_ALLOWED", "WORKFLOW_SHARED_STATE", "TRANSITION_SURFACE_DISALLOWED"),
        ("TRANSITION_DUPLICATE_ID", "TRANSITION_DUPLICATE_ID", "INTERACTION_TRANSITION:DUPLICATE"),
        ("TRANSITION_INVALID_KIND", "TRANSITION_INVALID_KIND", "TRANSITION_KIND"),
        ("TRANSITION_SEMANTIC_HASH_MISMATCH", "TRANSITION_SEMANTIC_HASH", "TRANSITION_SEMANTIC_HASH"),
        ("TRANSITION_ID_HASH_MISMATCH", "TRANSITION_ID_HASH", "TRANSITION_ID_HASH"),
        ("TRANSITION_FACT_BOUNDARY_EXTRA_KEY", "TRANSITION_FACT_BOUNDARY", "TRANSITION:FACT_BOUNDARY_KEYS"),
        ("EXPORT_MISSING_REFERENCES", "EXPORT_MISSING_REFERENCES", "EXPORT_TRACE"),
        ("EXPORT_COMPOSITION_MISMATCH", "EXPORT_COMPOSITION_MISMATCH", "EXPORT_WORKFLOW_STATE_COMPOSITION"),
        ("EXPORT_FALSE_PRESERVATION_FLAG", "EXPORT_FALSE_FLAG", "EXPORT_TRACE"),
        ("EXPORT_INCOMPLETE_RECORDS", "EXPORT_INCOMPLETE_RECORDS", "EXPORT_PROJECTION_RECORD_SET"),
        ("EXPORT_INCORRECT_RECORD", "EXPORT_INCORRECT_RECORD", "EXPORT_PROJECTION_RECORD_TRACE"),
        ("EXPORT_SEMANTIC_HASH", "EXPORT_SEMANTIC_HASH", "EXPORT_SEMANTIC_HASH"),
        ("EXPORT_PRESENTATION_HASH", "EXPORT_PRESENTATION_HASH", "EXPORT_PRESENTATION_HASH"),
        ("EXPORT_ID_HASH", "EXPORT_ID_HASH", "EXPORT_ID_HASH"),
        ("EXPORT_FACT_BOUNDARY_EXTRA_KEY", "EXPORT_FACT_BOUNDARY", "EXPORT:FACT_BOUNDARY_KEYS"),
    )
    for probe_id, mutation_case, expected_code in interaction_probes:
        results.append(expect_rejection(
            probe_id,
            model,
            lambda value, selected=mutation_case: mutate_interaction(value, selected),
            lambda value: validate_interaction_surface_independent(
                value["research_controls"], hash_contract
            ),
            expected_code,
        ))

    def manifest_validator(mutant: dict[str, Any]) -> None:
        validate_manifest_and_hashes(
            model, model_raw, mutant, manifest_raw, checksums_raw, input_hashes,
            capabilities, canonical_required=False,
        )

    results.append(expect_rejection(
        "CORRUPT-MANIFEST-READ-MODEL-HASH",
        manifest,
        lambda value: value["artifact_sha256"].__setitem__("read-model.json", "0" * 64),
        manifest_validator,
        "MANIFEST_READ_MODEL_SHA256",
    ))
    results.append(expect_rejection(
        "CORRUPT-CHECKSUMS",
        checksums_raw,
        lambda value: None,
        lambda _value: validate_manifest_and_hashes(
            model, model_raw, manifest, manifest_raw,
            checksums_raw.replace(b"manifest.json", b"manifest-tampered.json"),
            input_hashes, capabilities,
        ),
        "CHECKSUM_CONTENT",
    ))

    def runtime_validator(value: dict[str, Any]) -> None:
        validate_runtime_model(
            value,
            fixture,
            validate_fixture_core(fixture, hash_contract),
            round16a,
            hash_contract,
        )

    results.append(expect_rejection(
        "PARTICIPANT_SCOPE_DIVERGENCE",
        model,
        lambda value: value["research_controls"]["associations"][0]["participants"][0].__setitem__(
            "participant_scope_id",
            next(
                row["scope_id"] for row in value["research_controls"]["scopes"]
                if row["scope_id"]
                != value["research_controls"]["associations"][0]["scope"]["scope_id"]
            ),
        ),
        runtime_validator,
        "PARTICIPANT_SCOPE_DIVERGENCE",
    ))
    results.append(expect_rejection(
        "DERIVED_ACTIVE_PENDING_REVIEW_COUNT",
        model,
        lambda value: value["capabilities"].__setitem__("active_pending_review_count", 1),
        runtime_validator,
        "CAPABILITY_ACTIVE_PENDING_REVIEW_DERIVED",
    ))
    results.append(expect_rejection(
        "DERIVED_IMPLICIT_HYPEREDGE_PROJECTION_COUNT",
        model,
        lambda value: value["capabilities"].__setitem__("implicit_hyperedge_projection_count", 1),
        runtime_validator,
        "CAPABILITY_IMPLICIT_PROJECTION_DERIVED",
    ))
    results.append(expect_rejection(
        "EXACT_ADVERTISED_READ_PATH_PARITY",
        model,
        lambda value: value["capabilities"]["read_paths"].pop(),
        runtime_validator,
        "CAPABILITY_READ_PATH_PARITY",
    ))

    # A runtime-surface promotion must also fail, independently of source controls.
    results.append(expect_rejection(
        "CORRUPT-RUNTIME-ACTIVE-PRODUCT-PROMOTION",
        model,
        lambda value: value["active_product"]["associations"].append(
            copy.deepcopy(value["research_controls"]["associations"][0])
        ),
        runtime_validator,
        "ACTIVE_PRODUCT_NOT_EMPTY",
    ))
    return results


def build_receipt() -> dict[str, Any]:
    fixture, fixture_raw = load_json(REPO / FIXTURE_REL)
    census, census_raw = load_json(REPO / CENSUS_REL)
    hash_contract, hash_contract_raw = load_json(REPO / HASH_CONTRACT_REL)
    round16a, round16a_raw = load_json(REPO / ROUND16A_REL)
    model, model_raw = load_json(REPO / READ_MODEL_REL)
    manifest, manifest_raw = load_json(REPO / MANIFEST_REL)
    try:
        checksums_raw = (REPO / CHECKSUMS_REL).read_bytes()
    except OSError as error:
        raise VerificationError(f"INPUT_UNREADABLE:{CHECKSUMS_REL}:{error}") from error

    enforce(sha256_bytes(model_raw) == EXPECTED_READ_MODEL_SHA256, "FROZEN_READ_MODEL_TRUST_ANCHOR")
    enforce(sha256_bytes(manifest_raw) == EXPECTED_MANIFEST_SHA256, "FROZEN_MANIFEST_TRUST_ANCHOR")
    enforce(sha256_bytes(checksums_raw) == EXPECTED_CHECKSUMS_SHA256, "FROZEN_CHECKSUMS_TRUST_ANCHOR")

    actual_generated = sorted(path.name for path in GENERATED.iterdir())
    enforce(actual_generated == ["CHECKSUMS.sha256", "manifest.json", "read-model.json"], "GENERATED_FILE_SET")
    input_hashes = {
        FIXTURE_REL.as_posix(): sha256_bytes(fixture_raw),
        CENSUS_REL.as_posix(): sha256_bytes(census_raw),
        HASH_CONTRACT_REL.as_posix(): sha256_bytes(hash_contract_raw),
        ROUND16A_REL.as_posix(): sha256_bytes(round16a_raw),
    }

    fixture_info = validate_fixture_core(fixture, hash_contract)
    control_ids = validate_control_semantics(fixture)
    validate_census(census, fixture_info)
    validate_round16a(round16a)
    runtime_info = validate_runtime_model(
        model, fixture, fixture_info, round16a, hash_contract
    )
    validate_manifest_and_hashes(
        model, model_raw, manifest, manifest_raw, checksums_raw,
        input_hashes, runtime_info["capabilities"],
    )
    corruption_results = run_corruption_controls(
        fixture, control_ids, model, model_raw, manifest, manifest_raw,
        checksums_raw, input_hashes, runtime_info["capabilities"], census, round16a,
        hash_contract,
    )

    verifier_source = (REPO / VERIFIER_REL).read_text(encoding="utf-8")
    tree = ast.parse(verifier_source)
    imports = {
        alias.name
        for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    enforce(not any("build_exploration_v3_runtime_read_model" in name for name in imports), "PRIMARY_GENERATOR_IMPORTED")
    enforce("subprocess" not in imports, "PROCESS_EXECUTION_MODULE_IMPORTED")

    checks = Checks()
    checks.equal("semantic_fixture_source", fixture["source_sha"], SOURCE_SHA)
    checks.equal("semantic_census_taxonomy", census["count_taxonomy"], fixture_info["taxonomy"])
    checks.equal("round16a_dispositions", round16a["main_object_distributions"], EXPECTED_ROUND16A_DISTRIBUTIONS)
    checks.equal("round16a_transition_count", round16a["transition_count"], 749944)
    checks.equal("runtime_surface_keys", set(model["active_product"]), SURFACE_COLLECTIONS)
    checks.true("active_product_empty", all(not rows for rows in model["active_product"].values()))
    checks.equal("runtime_control_counts", runtime_info["collection_counts"], {
        "scopes": 6, "concepts": 21, "concept_senses": 21, "associations": 14,
        "incidences": 37, "association_realizations": 10,
        "composition_coherence_reviews": 2, "compositions": 2,
        "navigation_states": 1, "workflows": 1, "exports": 1, "transitions": 0,
    })
    checks.equal("runtime_closure", model["closure_flags"], EXPECTED_CLOSURE)
    checks.equal("runtime_source", model["source_authority"]["semantic_contract_source_sha"], SOURCE_SHA)
    checks.equal("manifest_read_model_sha", manifest["artifact_sha256"]["read-model.json"], sha256_bytes(model_raw))
    checks.equal("manifest_counts", manifest["counts"], model["capabilities"])
    checks.true("corruption_rejection_coverage", len(corruption_results) >= 80)
    checks.true("corruption_all_rejected", all(row["status"] == "PASS_REJECTED" for row in corruption_results))
    checks.true("primary_generator_not_imported", not any("build_exploration_v3_runtime_read_model" in name for name in imports))
    checks.true("primary_generator_not_invoked", "subprocess" not in imports)

    return {
        "receipt_version": VERIFIER_VERSION,
        "status": "PASS",
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "semantic_contract_parent_sha": SEMANTIC_PARENT_SHA,
        "contract_version": CONTRACT_VERSION,
        "read_model_version": READ_MODEL_VERSION,
        "manifest_version": MANIFEST_VERSION,
        "verifier_path": VERIFIER_REL.as_posix(),
        "verifier_sha256": sha256_file(REPO / VERIFIER_REL),
        "independence": {
            "primary_generator_imported": False,
            "primary_generator_invoked": False,
            "primary_projection_code_reuse_reviewed_absent": True,
            "implementation": "STDLIB_ONLY_INDEPENDENT_PARSER_HASHER_AND_INVARIANT_RECONSTRUCTION",
        },
        "artifact_pins": {
            "semantic_fixture_sha256": input_hashes[FIXTURE_REL.as_posix()],
            "semantic_census_sha256": input_hashes[CENSUS_REL.as_posix()],
            "semantic_hash_binding_contract_sha256": input_hashes[HASH_CONTRACT_REL.as_posix()],
            "round16a_reconciliation_census_sha256": input_hashes[ROUND16A_REL.as_posix()],
            "read_model_sha256": EXPECTED_READ_MODEL_SHA256,
            "manifest_sha256": EXPECTED_MANIFEST_SHA256,
            "checksums_sha256": EXPECTED_CHECKSUMS_SHA256,
        },
        "reconstructed_count_taxonomy": fixture_info["taxonomy"],
        "runtime_collection_counts": runtime_info["collection_counts"],
        "production_boundary": {
            "active_product_collection_count": len(model["active_product"]),
            "active_product_record_count": sum(len(rows) for rows in model["active_product"].values()),
            "production_activation_count": model["capabilities"]["production_activation_count"],
            "active_pending_review_count": model["capabilities"]["active_pending_review_count"],
            "implicit_hyperedge_projection_count": model["capabilities"]["implicit_hyperedge_projection_count"],
            "transitions_available": model["capabilities"]["transitions_available"],
            "transition_derivation_policy": model["capabilities"]["transition_derivation_policy"],
            "closure_true_count": sum(model["closure_flags"].values()),
        },
        "round16a_reconciliation": {
            "main_object_distributions": round16a["main_object_distributions"],
            "main_object_total_distribution": round16a["main_object_total_distribution"],
            "transition_count": round16a["transition_count"],
            "transition_outcome_distribution": round16a["transition_outcome_distribution"],
            "reconciled_row_count_including_topology_audit_records": round16a[
                "reconciled_row_count_including_topology_audit_records"
            ],
        },
        "control_verification": {
            "control_class_count": len(EXPECTED_CONTROL_CLASSES),
            "control_ids": control_ids,
        },
        "corruption_control_count": len(corruption_results),
        "corruption_controls": corruption_results,
        "check_count": len(checks.rows),
        "checks": checks.rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="require byte-identical committed receipt")
    args = parser.parse_args()
    receipt = build_receipt()
    expected = receipt_bytes(receipt)
    output = REPO / RECEIPT_REL
    if args.check:
        if not output.is_file():
            raise SystemExit(f"MISSING {RECEIPT_REL.as_posix()}")
        if output.read_bytes() != expected:
            raise SystemExit(f"DIFF {RECEIPT_REL.as_posix()}")
        print(
            f"PASS {VERIFIER_VERSION} checks={receipt['check_count']} "
            f"corruptions={receipt['corruption_control_count']} receipt={sha256_file(output)}"
        )
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(expected)
    print(
        f"PASS {VERIFIER_VERSION} checks={receipt['check_count']} "
        f"corruptions={receipt['corruption_control_count']} "
        f"wrote={RECEIPT_REL.as_posix()} sha256={sha256_bytes(expected)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
