#!/usr/bin/env python3
"""Build the additive TRACE Exploration v3 runtime read model.

The committed v3 semantic contract is the only semantic input.  This builder
projects its synthetic controls into an explicitly labelled control catalog and
derives a separate, fail-closed active-product catalog.  It never promotes an
inquiry, pending review, synthetic control, or product-ineligible record.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = (
    REPO_ROOT
    / "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw"
)
OUTPUT_ROOT = REPO_ROOT / "frontend/generated/trace-exploration-v3"

SEMANTIC_FIXTURES = RAW_ROOT / "v3-semantic-contract-fixtures-v1.json"
SEMANTIC_CENSUS = RAW_ROOT / "v3-semantic-contract-census-v1.json"
SEMANTIC_HASH_BINDINGS = RAW_ROOT / "v3-semantic-hash-binding-contract-v1.json"
ROUND16A_CENSUS = RAW_ROOT / "round16a-global-reconciliation-census-v1.json"

SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
API_VERSION = "trace-exploration/v3"
SEMANTIC_NAMESPACE = "trace/exploration/v3"
READ_MODEL_VERSION = "trace-exploration-runtime-read-model-v3-1.0.0"
MANIFEST_VERSION = "trace-exploration-runtime-manifest-v3-1.0.0"
GENERATOR_VERSION = "trace-round16b-exploration-v3-runtime-builder-v1"
CANONICAL_SERIALIZATION = (
    "recursive-key-sort;array-order-preserved;json-minified;final-lf;utf8"
)
OUTPUT_FILENAMES = ("CHECKSUMS.sha256", "manifest.json", "read-model.json")

FINAL_SUPPORTING_DISPOSITIONS = {
    "DIRECT_PAIRWISE_SUPPORT",
    "DIRECT_HIGHER_ORDER_SUPPORT",
    "COHERENT_COMPOSITE_SUPPORT",
    "MIXED_DIRECT_AND_COMPOSITE_SUPPORT",
}


def fail(code: str) -> None:
    raise ValueError(code)


def require(condition: bool, code: str) -> None:
    if not condition:
        fail(code)


def require_dict(value: Any, code: str) -> dict[str, Any]:
    require(isinstance(value, dict), code)
    return value


def require_list(value: Any, code: str) -> list[Any]:
    require(isinstance(value, list), code)
    return value


def require_text(value: Any, code: str) -> str:
    require(isinstance(value, str) and bool(value), code)
    return value


def read_json(path: Path) -> dict[str, Any]:
    try:
        return require_dict(json.loads(path.read_text(encoding="utf-8")), f"INVALID_JSON:{path}")
    except OSError as error:
        raise ValueError(f"INPUT_UNAVAILABLE:{path}:{error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"INVALID_JSON:{path}:{error}") from error


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sorted_records(records: list[dict[str, Any]], identity_key: str) -> list[dict[str, Any]]:
    return sorted(records, key=lambda item: require_text(item.get(identity_key), f"MISSING:{identity_key}"))


def exact_supporting_association(record: dict[str, Any]) -> bool:
    review = require_dict(record.get("review"), "ASSOCIATION_REVIEW_MISSING")
    activation = require_dict(record.get("activation"), "ASSOCIATION_ACTIVATION_MISSING")
    evidence = require_dict(record.get("evidence"), "ASSOCIATION_EVIDENCE_MISSING")
    return (
        record.get("realm") == "PRODUCTION"
        and record.get("lifecycle_state") == "ACTIVE"
        and record.get("product_eligible") is True
        and isinstance(record.get("product_path"), str)
        and bool(record.get("product_path"))
        and review.get("review_state") == "FINAL"
        and review.get("authority_state") == "FINAL"
        and review.get("disposition") in FINAL_SUPPORTING_DISPOSITIONS
        and review.get("global_coherence") == "PASS"
        and review.get("bounded_senses_compatible") is True
        and review.get("case_scope_compatible") is True
        and review.get("roles_and_topology_supported") is True
        and review.get("unsupported_bridge_count") == 0
        and evidence.get("evidence_complete") is True
        and evidence.get("rights_cleared_for_governed_use") is True
        and evidence.get("conflicts_resolved") is True
        and bool(evidence.get("evidence_item_ids"))
        and bool(evidence.get("locator_ids"))
        and activation.get("all_gates_pass") is True
        and activation.get("decision") == "ALLOW"
    )


def association_dto(record: dict[str, Any], *, production_fact: bool) -> dict[str, Any]:
    participants = copy.deepcopy(require_list(record.get("participants"), "ASSOCIATION_PARTICIPANTS_MISSING"))
    review = copy.deepcopy(require_dict(record.get("review"), "ASSOCIATION_REVIEW_MISSING"))
    evidence = copy.deepcopy(require_dict(record.get("evidence"), "ASSOCIATION_EVIDENCE_MISSING"))
    activation = copy.deepcopy(require_dict(record.get("activation"), "ASSOCIATION_ACTIVATION_MISSING"))
    return {
        "activation": activation,
        "arity": record["arity"],
        "association_id": record["association_id"],
        "association_kind": record["association_kind"],
        "association_revision_id": record["association_revision_id"],
        "eligibility": {
            "lifecycle_state": record["lifecycle_state"],
            "product_eligibility_disposition": record["product_eligibility_disposition"],
            "product_eligible": record["product_eligible"],
            "product_ineligibility_reason": record["product_ineligibility_reason"],
            "product_path": record["product_path"],
        },
        "fact_boundary": {
            "data_class": "ACTIVE_PRODUCT_FACT" if production_fact else "SYNTHETIC_CONTROL",
            "production_fact": production_fact,
            "synthetic_control": record["realm"] == "SYNTHETIC_CONTROL",
        },
        "identity_material_sha256": record["identity_material_sha256"],
        "internal_pair_association_ids": copy.deepcopy(record["internal_pair_association_ids"]),
        "internal_pair_links": copy.deepcopy(record["internal_pair_links"]),
        "order_semantics": record["order_semantics"],
        "pair_projection_policy": record["pair_projection_policy"],
        "participants": participants,
        "presentation": copy.deepcopy(record["presentation"]),
        "presentation_sha256": record["presentation_sha256"],
        "provenance": evidence,
        "realm": record["realm"],
        "review": review,
        "roles_meaningful": record["roles_meaningful"],
        "scope": copy.deepcopy(record["scope"]),
        "semantic_sha256": record["semantic_sha256"],
        "semantic_version": record["semantic_version"],
        "uncertainty": copy.deepcopy(record["uncertainty"]),
    }


def validate_associations(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_revision: dict[str, dict[str, Any]] = {}
    by_association: dict[str, dict[str, Any]] = {}
    all_incidence_ids: set[str] = set()
    for record in sorted_records(records, "association_revision_id"):
        association_id = require_text(record.get("association_id"), "ASSOCIATION_ID_MISSING")
        revision_id = require_text(record.get("association_revision_id"), "ASSOCIATION_REVISION_ID_MISSING")
        require(association_id not in by_association, "DUPLICATE_ASSOCIATION_ID")
        require(revision_id not in by_revision, "DUPLICATE_ASSOCIATION_REVISION_ID")
        participants = require_list(record.get("participants"), "ASSOCIATION_PARTICIPANTS_MISSING")
        arity = record.get("arity")
        require(isinstance(arity, int) and arity == len(participants), "ASSOCIATION_ARITY_MISMATCH")
        kind = record.get("association_kind")
        require(kind in {"PAIR", "HIGHER_ORDER"}, "ASSOCIATION_KIND_INVALID")
        if kind == "PAIR":
            require(arity == 2, "PAIR_ARITY_INVALID")
            require(record.get("pair_projection_policy") == "NOT_APPLICABLE", "PAIR_PROJECTION_POLICY_INVALID")
        else:
            require(arity >= 3, "HIGHER_ORDER_ARITY_INVALID")
            require(record.get("pair_projection_policy") == "NONE", "HIGHER_ORDER_PAIR_PROJECTION_FORBIDDEN")

        local_incidence_ids: set[str] = set()
        participant_senses: set[str] = set()
        for participant in participants:
            participant = require_dict(participant, "PARTICIPANT_INVALID")
            incidence_id = require_text(participant.get("incidence_id"), "INCIDENCE_ID_MISSING")
            sense_id = require_text(participant.get("sense_id"), "SENSE_ID_MISSING")
            require(incidence_id not in local_incidence_ids, "DUPLICATE_ASSOCIATION_INCIDENCE")
            require(incidence_id not in all_incidence_ids, "DUPLICATE_GLOBAL_INCIDENCE")
            require(sense_id not in participant_senses, "DUPLICATE_PARTICIPANT_SENSE")
            local_incidence_ids.add(incidence_id)
            all_incidence_ids.add(incidence_id)
            participant_senses.add(sense_id)

        internal_pair_ids = require_list(record.get("internal_pair_association_ids"), "INTERNAL_PAIR_IDS_MISSING")
        internal_pair_links = require_list(record.get("internal_pair_links"), "INTERNAL_PAIR_LINKS_MISSING")
        require(len(internal_pair_ids) == len(internal_pair_links), "INTERNAL_PAIR_LINK_COUNT_MISMATCH")
        require(
            sorted(internal_pair_ids)
            == sorted(require_text(link.get("pair_association_id"), "PAIR_LINK_ID_MISSING") for link in internal_pair_links),
            "INTERNAL_PAIR_LINK_IDS_MISMATCH",
        )
        if kind == "PAIR":
            require(not internal_pair_ids and not internal_pair_links, "PAIR_CANNOT_NEST_PAIR_LINKS")

        by_revision[revision_id] = record
        by_association[association_id] = record

    for record in records:
        parent_incidence_ids = {
            participant["incidence_id"] for participant in record["participants"]
        }
        for link in record["internal_pair_links"]:
            pair_record = by_revision.get(link["pair_association_revision_id"])
            require(pair_record is not None, "INTERNAL_PAIR_REVISION_UNRESOLVED")
            require(pair_record["association_kind"] == "PAIR", "INTERNAL_PAIR_KIND_INVALID")
            require(pair_record["association_id"] == link["pair_association_id"], "INTERNAL_PAIR_ID_MISMATCH")
            require(
                set(link["participant_incidence_ids"]).issubset(parent_incidence_ids),
                "INTERNAL_PAIR_PARENT_INCIDENCE_MISMATCH",
            )
            require(
                set(link["pair_participant_incidence_ids"])
                == {participant["incidence_id"] for participant in pair_record["participants"]},
                "INTERNAL_PAIR_OWN_INCIDENCE_MISMATCH",
            )
    return by_revision


def exact_product_composition(
    record: dict[str, Any],
    review: dict[str, Any],
    association_by_revision: dict[str, dict[str, Any]],
) -> bool:
    traced = [
        association_by_revision.get(realization.get("association_revision_id"))
        for realization in require_list(record.get("association_realizations"), "REALIZATIONS_MISSING")
    ]
    return (
        record.get("realm") == "PRODUCTION"
        and record.get("product_eligible") is True
        and isinstance(record.get("product_path"), str)
        and bool(record.get("product_path"))
        and record.get("association_trace_complete") is True
        and record.get("renderability") == "PASS"
        and review.get("review_state") == "FINAL"
        and review.get("global_coherence") == "PASS"
        and review.get("decision") == "COHERENT"
        and review.get("bounded_senses_compatible") is True
        and review.get("case_scope_compatible") is True
        and review.get("roles_and_topology_supported") is True
        and review.get("same_configuration") is True
        and review.get("unsupported_bridge_count") == 0
        and bool(traced)
        and all(item is not None and exact_supporting_association(item) for item in traced)
    )


def composition_dto(
    record: dict[str, Any],
    review: dict[str, Any],
    association_by_revision: dict[str, dict[str, Any]],
    *,
    production_fact: bool,
) -> dict[str, Any]:
    realizations: list[dict[str, Any]] = []
    for source in record["association_realizations"]:
        association = association_by_revision[source["association_revision_id"]]
        realization = copy.deepcopy(source)
        realization["association_id"] = association["association_id"]
        realization["association_kind"] = association["association_kind"]
        realizations.append(realization)
    return {
        "association_realizations": realizations,
        "association_trace_complete": record["association_trace_complete"],
        "coherence_review": tagged_record(review, production_fact=production_fact),
        "composition_id": record["composition_id"],
        "composition_node_ids": copy.deepcopy(record["composition_node_ids"]),
        "composition_revision_id": record["composition_revision_id"],
        "eligibility": {
            "product_eligibility_disposition": record["product_eligibility_disposition"],
            "product_eligible": record["product_eligible"],
            "product_ineligibility_reason": record["product_ineligibility_reason"],
            "product_path": record["product_path"],
        },
        "fact_boundary": {
            "data_class": "ACTIVE_PRODUCT_FACT" if production_fact else "SYNTHETIC_CONTROL",
            "production_fact": production_fact,
            "synthetic_control": record["realm"] == "SYNTHETIC_CONTROL",
        },
        "global_coherence_review_id": record["global_coherence_review_id"],
        "presentation": copy.deepcopy(record["presentation"]),
        "presentation_sha256": record["presentation_sha256"],
        "realm": record["realm"],
        "renderability": record["renderability"],
        "semantic_sha256": record["semantic_sha256"],
        "topology_family": record["topology_family"],
    }


def fact_boundary(production_fact: bool) -> dict[str, Any]:
    return {
        "data_class": "ACTIVE_PRODUCT_FACT" if production_fact else "SYNTHETIC_CONTROL",
        "production_fact": production_fact,
        "synthetic_control": not production_fact,
    }


def tagged_record(record: dict[str, Any], *, production_fact: bool) -> dict[str, Any]:
    projected = copy.deepcopy(record)
    projected["fact_boundary"] = fact_boundary(production_fact)
    return projected


def incidence_dtos(
    associations: list[dict[str, Any]],
    *,
    production_fact: bool,
) -> list[dict[str, Any]]:
    incidences: list[dict[str, Any]] = []
    for association in associations:
        for participant in association["participants"]:
            incidences.append(
                {
                    "association_id": association["association_id"],
                    "association_kind": association["association_kind"],
                    "association_revision_id": association["association_revision_id"],
                    "concept_id": participant["concept_id"],
                    "fact_boundary": fact_boundary(production_fact),
                    "incidence_id": participant["incidence_id"],
                    "ordinal": participant["ordinal"],
                    "participant_scope_id": participant["participant_scope_id"],
                    "qualifications": copy.deepcopy(participant["qualifications"]),
                    "role_id": participant["role_id"],
                    "sense_id": participant["sense_id"],
                }
            )
    return sorted(incidences, key=lambda item: item["incidence_id"])


def realization_dtos(compositions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for composition in compositions:
        for realization in composition["association_realizations"]:
            realization_id = realization["association_realization_id"]
            require(realization_id not in by_id, "DUPLICATE_EXPLICIT_REALIZATION")
            projected = copy.deepcopy(realization)
            projected["composition_id"] = composition["composition_id"]
            projected["composition_revision_id"] = composition["composition_revision_id"]
            projected["fact_boundary"] = copy.deepcopy(composition["fact_boundary"])
            by_id[realization_id] = projected
    return [by_id[key] for key in sorted(by_id)]


def validate_and_project_compositions(
    records: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    association_by_revision: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    review_by_id = {
        require_text(review.get("composition_coherence_review_id"), "COHERENCE_REVIEW_ID_MISSING"): review
        for review in reviews
    }
    require(len(review_by_id) == len(reviews), "DUPLICATE_COHERENCE_REVIEW_ID")
    active_product: list[dict[str, Any]] = []
    controls: list[dict[str, Any]] = []
    used_review_ids: set[str] = set()
    for record in sorted_records(records, "composition_revision_id"):
        review_id = require_text(record.get("global_coherence_review_id"), "COMPOSITION_REVIEW_REF_MISSING")
        review = review_by_id.get(review_id)
        require(review is not None, "COMPOSITION_REVIEW_UNRESOLVED")
        require(review.get("composition_id") == record.get("composition_id"), "COMPOSITION_REVIEW_IDENTITY_MISMATCH")
        used_review_ids.add(review_id)
        realization_ids: set[str] = set()
        for realization in require_list(record.get("association_realizations"), "REALIZATIONS_MISSING"):
            realization = require_dict(realization, "REALIZATION_INVALID")
            realization_id = require_text(realization.get("association_realization_id"), "REALIZATION_ID_MISSING")
            require(realization_id not in realization_ids, "DUPLICATE_REALIZATION_ID")
            realization_ids.add(realization_id)
            revision_id = require_text(realization.get("association_revision_id"), "REALIZATION_ASSOCIATION_REF_MISSING")
            association = association_by_revision.get(revision_id)
            require(association is not None, "REALIZATION_ASSOCIATION_UNRESOLVED")
            if association["association_kind"] == "HIGHER_ORDER":
                require(realization.get("realization_kind") != "PAIR_EDGE", "HYPEREDGE_PROJECTED_AS_PAIR_EDGE")
                require(
                    set(realization.get("realized_incidence_ids", []))
                    == {participant["incidence_id"] for participant in association["participants"]},
                    "HYPEREDGE_PARTIAL_REALIZATION_FORBIDDEN",
                )
        production_fact = exact_product_composition(record, review, association_by_revision)
        dto = composition_dto(
            record,
            review,
            association_by_revision,
            production_fact=production_fact,
        )
        if production_fact:
            active_product.append(dto)
        elif record.get("realm") == "SYNTHETIC_CONTROL":
            controls.append(dto)
    require(used_review_ids == set(review_by_id), "ORPHAN_COHERENCE_REVIEW")
    return (
        active_product,
        controls,
        [tagged_record(review_by_id[key], production_fact=False) for key in sorted(review_by_id)],
    )


def concept_dto(record: dict[str, Any], *, production_fact: bool) -> dict[str, Any]:
    return {
        "association_eligible": record["association_eligible"],
        "authority": copy.deepcopy(record["authority"]),
        "canonical_label": record["canonical_label"],
        "concept_id": record["concept_id"],
        "fact_boundary": {
            "data_class": "ACTIVE_PRODUCT_FACT" if production_fact else "SYNTHETIC_CONTROL",
            "production_fact": production_fact,
            "synthetic_control": record["realm"] == "SYNTHETIC_CONTROL",
        },
        "lifecycle_state": record["lifecycle_state"],
        "product_eligibility_disposition": record["product_eligibility_disposition"],
        "product_eligible": record["product_eligible"],
        "product_ineligibility_reason": record["product_ineligibility_reason"],
        "product_path": record["product_path"],
        "realm": record["realm"],
        "semantic_sha256": record["semantic_sha256"],
        "semantic_version": record["semantic_version"],
    }


def sense_dto(record: dict[str, Any], *, production_fact: bool) -> dict[str, Any]:
    return {
        "association_eligible": record["association_eligible"],
        "authority": copy.deepcopy(record["authority"]),
        "bounded_definition": record["bounded_definition"],
        "concept_id": record["concept_id"],
        "fact_boundary": {
            "data_class": "ACTIVE_PRODUCT_FACT" if production_fact else "SYNTHETIC_CONTROL",
            "production_fact": production_fact,
            "synthetic_control": record["realm"] == "SYNTHETIC_CONTROL",
        },
        "governed_scope_ids": copy.deepcopy(record["governed_scope_ids"]),
        "lifecycle_state": record["lifecycle_state"],
        "product_eligibility_disposition": record["product_eligibility_disposition"],
        "product_eligible": record["product_eligible"],
        "product_ineligibility_reason": record["product_ineligibility_reason"],
        "product_path": record["product_path"],
        "realm": record["realm"],
        "semantic_sha256": record["semantic_sha256"],
        "semantic_version": record["semantic_version"],
        "sense_id": record["sense_id"],
        "vocabulary_crosswalk_ids": copy.deepcopy(record["vocabulary_crosswalk_ids"]),
    }


def build_read_model() -> dict[str, Any]:
    fixtures = read_json(SEMANTIC_FIXTURES)
    census = read_json(SEMANTIC_CENSUS)
    round16a = read_json(ROUND16A_CENSUS)
    require(fixtures.get("source_sha") == SOURCE_SHA, "SEMANTIC_SOURCE_SHA_MISMATCH")
    require(round16a.get("source_sha") == SOURCE_SHA, "ROUND16A_SOURCE_SHA_MISMATCH")
    require(fixtures.get("api_namespace") == SEMANTIC_NAMESPACE, "API_NAMESPACE_MISMATCH")
    closure_flags = require_dict(fixtures.get("closure_flags"), "CLOSURE_FLAGS_MISSING")
    require(closure_flags and all(value is False for value in closure_flags.values()), "CLOSURE_FLAG_NOT_FALSE")
    require(round16a.get("closure") == closure_flags, "CLOSURE_INPUTS_DISAGREE")
    require(round16a.get("active_fact_created_count") == 0, "ROUND16A_ACTIVE_FACT_CREATED")
    require(round16a.get("product_activation_count") == 0, "ROUND16A_PRODUCT_ACTIVATION_CREATED")
    require(round16a.get("pair_projection_created_count") == 0, "ROUND16A_PAIR_PROJECTION_CREATED")

    associations = [require_dict(value, "ASSOCIATION_INVALID") for value in require_list(fixtures.get("associations"), "ASSOCIATIONS_MISSING")]
    association_by_revision = validate_associations(associations)
    active_product_associations = [
        association_dto(record, production_fact=True)
        for record in sorted_records(associations, "association_revision_id")
        if exact_supporting_association(record)
    ]
    control_associations = [
        association_dto(record, production_fact=False)
        for record in sorted_records(associations, "association_revision_id")
        if record.get("realm") == "SYNTHETIC_CONTROL"
    ]

    compositions = [require_dict(value, "COMPOSITION_INVALID") for value in require_list(fixtures.get("compositions"), "COMPOSITIONS_MISSING")]
    reviews = [require_dict(value, "COHERENCE_REVIEW_INVALID") for value in require_list(fixtures.get("composition_coherence_reviews"), "COHERENCE_REVIEWS_MISSING")]
    active_product_compositions, control_compositions, control_reviews = validate_and_project_compositions(
        compositions,
        reviews,
        association_by_revision,
    )

    concepts = [require_dict(value, "CONCEPT_INVALID") for value in require_list(fixtures.get("concepts"), "CONCEPTS_MISSING")]
    senses = [require_dict(value, "SENSE_INVALID") for value in require_list(fixtures.get("concept_senses"), "SENSES_MISSING")]
    active_product_concepts = [
        concept_dto(record, production_fact=True)
        for record in sorted_records(concepts, "concept_id")
        if record.get("realm") == "PRODUCTION"
        and record.get("lifecycle_state") == "ACTIVE"
        and record.get("association_eligible") is True
        and record.get("product_eligible") is True
        and isinstance(record.get("product_path"), str)
        and bool(record.get("product_path"))
    ]
    active_product_senses = [
        sense_dto(record, production_fact=True)
        for record in sorted_records(senses, "sense_id")
        if record.get("realm") == "PRODUCTION"
        and record.get("lifecycle_state") == "ACTIVE"
        and record.get("association_eligible") is True
        and record.get("product_eligible") is True
        and isinstance(record.get("product_path"), str)
        and bool(record.get("product_path"))
    ]
    control_concepts = [
        concept_dto(record, production_fact=False)
        for record in sorted_records(concepts, "concept_id")
        if record.get("realm") == "SYNTHETIC_CONTROL"
    ]
    control_senses = [
        sense_dto(record, production_fact=False)
        for record in sorted_records(senses, "sense_id")
        if record.get("realm") == "SYNTHETIC_CONTROL"
    ]

    scopes = [require_dict(value, "SCOPE_INVALID") for value in require_list(fixtures.get("scopes"), "SCOPES_MISSING")]
    control_scopes = []
    for record in sorted_records(scopes, "scope_id"):
        projected_scope = tagged_record(record, production_fact=False)
        projected_scope["realm"] = "SYNTHETIC_CONTROL"
        control_scopes.append(projected_scope)
    control_incidences = incidence_dtos(control_associations, production_fact=False)
    control_realizations = realization_dtos(control_compositions)
    navigation_states = [
        require_dict(value, "NAVIGATION_STATE_INVALID")
        for value in require_list(fixtures.get("navigation_states"), "NAVIGATION_STATES_MISSING")
    ]
    transitions = [
        require_dict(value, "TRANSITION_INVALID")
        for value in require_list(fixtures.get("transitions"), "TRANSITIONS_MISSING")
    ]
    workflows = [
        require_dict(value, "WORKFLOW_INVALID")
        for value in require_list(fixtures.get("workflows"), "WORKFLOWS_MISSING")
    ]
    exports = [
        require_dict(value, "EXPORT_INVALID")
        for value in require_list(fixtures.get("exports"), "EXPORTS_MISSING")
    ]
    control_navigation_states = [
        tagged_record(record, production_fact=False)
        for record in sorted_records(navigation_states, "state_id")
        if record.get("realm") == "SYNTHETIC_CONTROL"
    ]
    control_workflows = [
        tagged_record(record, production_fact=False)
        for record in sorted_records(workflows, "workflow_id")
        if record.get("realm") == "SYNTHETIC_CONTROL"
    ]
    control_exports = [
        tagged_record(record, production_fact=False)
        for record in sorted_records(exports, "export_id")
        if record.get("realm") == "SYNTHETIC_CONTROL"
    ]
    # The semantic fixture governs no transition records.  A workflow or state
    # is not permission to synthesize transitions, and v2 derivation is not
    # imported into this additive contract.
    require(not transitions, "SEMANTIC_TRANSITION_SURFACE_MUST_REMAIN_EMPTY")
    control_transitions: list[dict[str, Any]] = []

    # This checkpoint has no governed production records.  Pinning zero here is
    # deliberate: later production population requires a new additive tranche.
    require(not active_product_associations, "UNAUTHORIZED_PRODUCT_ASSOCIATION")
    require(not active_product_compositions, "UNAUTHORIZED_PRODUCT_COMPOSITION")
    require(not active_product_concepts, "UNAUTHORIZED_PRODUCT_CONCEPT")
    require(not active_product_senses, "UNAUTHORIZED_PRODUCT_SENSE")

    empty_active_product = {
        "association_realizations": [],
        "associations": active_product_associations,
        "composition_coherence_reviews": [],
        "compositions": active_product_compositions,
        "concept_senses": active_product_senses,
        "concepts": active_product_concepts,
        "exports": [],
        "incidences": incidence_dtos(active_product_associations, production_fact=True),
        "navigation_states": [],
        "scopes": [],
        "transitions": [],
        "workflows": [],
    }
    require(
        all(not values for values in empty_active_product.values()),
        "UNAUTHORIZED_ACTIVE_PRODUCT_CLASS",
    )

    higher_order_controls = [
        item for item in control_associations if item["association_kind"] == "HIGHER_ORDER"
    ]
    pair_controls = [item for item in control_associations if item["association_kind"] == "PAIR"]
    association_census = census["count_taxonomy"]["associations"]
    require(
        len(control_associations)
        == association_census["synthetic_pair_revision_count"]
        + association_census["synthetic_higher_order_revision_count"],
        "CONTROL_ASSOCIATION_CENSUS_MISMATCH",
    )
    require(
        len(higher_order_controls) == association_census["synthetic_higher_order_revision_count"],
        "CONTROL_HIGHER_ORDER_CENSUS_MISMATCH",
    )
    require(
        len(pair_controls) == association_census["synthetic_pair_revision_count"],
        "CONTROL_PAIR_CENSUS_MISMATCH",
    )
    taxonomy = census["count_taxonomy"]
    require(len(control_scopes) == taxonomy["vocabulary"]["synthetic_scope_count"], "CONTROL_SCOPE_CENSUS_MISMATCH")
    require(len(control_concepts) == taxonomy["vocabulary"]["synthetic_concept_record_count"], "CONTROL_CONCEPT_CENSUS_MISMATCH")
    require(len(control_senses) == taxonomy["vocabulary"]["synthetic_concept_sense_record_count"], "CONTROL_SENSE_CENSUS_MISMATCH")
    require(len(control_incidences) == taxonomy["incidence"]["synthetic_incidence_count"], "CONTROL_INCIDENCE_CENSUS_MISMATCH")
    require(
        len(control_realizations)
        == taxonomy["realizations_and_compositions"]["synthetic_association_realization_count"],
        "CONTROL_REALIZATION_CENSUS_MISMATCH",
    )
    require(
        len(control_reviews)
        == taxonomy["realizations_and_compositions"]["synthetic_composition_coherence_review_count"],
        "CONTROL_COHERENCE_REVIEW_CENSUS_MISMATCH",
    )
    require(
        len(control_compositions)
        == taxonomy["realizations_and_compositions"]["synthetic_composition_count"],
        "CONTROL_COMPOSITION_CENSUS_MISMATCH",
    )
    require(len(control_navigation_states) == taxonomy["interaction"]["synthetic_state_count"], "CONTROL_STATE_CENSUS_MISMATCH")
    require(len(control_workflows) == taxonomy["interaction"]["synthetic_workflow_count"], "CONTROL_WORKFLOW_CENSUS_MISMATCH")
    require(len(control_exports) == taxonomy["interaction"]["synthetic_export_count"], "CONTROL_EXPORT_CENSUS_MISMATCH")

    baseline = {
        "active_fact_created_count": round16a["active_fact_created_count"],
        "authority_base_sha": round16a["authority_base_sha"],
        "closure": copy.deepcopy(round16a["closure"]),
        "main_object_distributions": copy.deepcopy(round16a["main_object_distributions"]),
        "main_object_total_distribution": copy.deepcopy(round16a["main_object_total_distribution"]),
        "pair_projection_created_count": round16a["pair_projection_created_count"],
        "product_activation_count": round16a["product_activation_count"],
        "reconciled_row_count_including_topology_audit_records": round16a[
            "reconciled_row_count_including_topology_audit_records"
        ],
        "status": round16a["status"],
        "transition_count": round16a["transition_count"],
        "transition_outcome_distribution": copy.deepcopy(round16a["transition_outcome_distribution"]),
    }
    active_pending_review_count = sum(
        association["eligibility"]["lifecycle_state"] == "ACTIVE"
        and (
            association["review"]["review_state"] != "FINAL"
            or association["review"]["authority_state"] != "FINAL"
        )
        for association in active_product_associations
    )
    implicit_hyperedge_projection_count = sum(
        association["association_kind"] == "HIGHER_ORDER"
        and (
            association["pair_projection_policy"] != "NONE"
            or any(
                realization["realization_kind"] == "PAIR_EDGE"
                for composition in [*active_product_compositions, *control_compositions]
                for realization in composition["association_realizations"]
                if realization["association_revision_id"]
                == association["association_revision_id"]
            )
        )
        for association in [*active_product_associations, *control_associations]
    )
    capabilities = {
        "active_pending_review_count": active_pending_review_count,
        "active_product_association_count": len(active_product_associations),
        "active_product_coherence_review_count": 0,
        "active_product_composition_count": len(active_product_compositions),
        "active_product_concept_count": len(active_product_concepts),
        "active_product_export_count": 0,
        "active_product_incidence_count": 0,
        "active_product_navigation_state_count": 0,
        "active_product_realization_count": 0,
        "active_product_scope_count": 0,
        "active_product_sense_count": len(active_product_senses),
        "active_product_transition_count": 0,
        "active_product_workflow_count": 0,
        "association_and_composition_identity_separate": True,
        "backend_association_arity_support": "PAIR_2_OR_HIGHER_ORDER_3_PLUS_NO_FIXED_SCHEMA_MAXIMUM",
        "control_association_count": len(control_associations),
        "control_coherence_review_count": len(control_reviews),
        "control_composition_count": len(control_compositions),
        "control_concept_count": len(control_concepts),
        "control_export_count": len(control_exports),
        "control_higher_order_association_count": len(higher_order_controls),
        "control_incidence_count": len(control_incidences),
        "control_navigation_state_count": len(control_navigation_states),
        "control_pair_association_count": len(pair_controls),
        "control_realization_count": len(control_realizations),
        "control_scope_count": len(control_scopes),
        "control_sense_count": len(control_senses),
        "control_transition_count": len(control_transitions),
        "control_workflow_count": len(control_workflows),
        "higher_order_associations_supported": True,
        "implicit_pair_projection_allowed": False,
        "implicit_hyperedge_projection_count": implicit_hyperedge_projection_count,
        "governed_product_arity_bound": None,
        "production_activation_count": len(active_product_associations),
        "product_activation_available": False,
        "read_paths": [
            "/capabilities",
            *[
                path
                for collection, identity in (
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
                for path in (
                    f"/{collection}",
                    f"/{collection}/{{{identity}}}",
                )
            ],
            *[
                path
                for collection, identity in (
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
                for path in (
                    f"/controls/{collection}",
                    f"/controls/{collection}/{{{identity}}}",
                )
            ],
            "/baseline/reconciliation",
        ],
        "supported_association_kinds": ["PAIR", "HIGHER_ORDER"],
        "research_controls_only": True,
        "transition_derivation_policy": "NONE_NO_V2_INHERITANCE",
        "transition_status": "FAIL_CLOSED_NO_ACTIVE_PRODUCT_STATE_GRAPH",
        "transitions_available": False,
    }

    research_controls = {
        "association_realizations": control_realizations,
        "associations": control_associations,
        "composition_coherence_reviews": control_reviews,
        "compositions": control_compositions,
        "concept_senses": control_senses,
        "concepts": control_concepts,
        "exports": control_exports,
        "incidences": control_incidences,
        "navigation_states": control_navigation_states,
        "scopes": control_scopes,
        "transitions": control_transitions,
        "workflows": control_workflows,
    }

    return {
        "active_product": empty_active_product,
        "api_version": API_VERSION,
        "baseline_reconciliation": baseline,
        "capabilities": capabilities,
        "closure_flags": copy.deepcopy(closure_flags),
        "contract_version": fixtures["contract_version"],
        "fact_boundary": {
            "active_product_policy": "FINAL_PRODUCTION_AUTHORITY_AND_ALL_GATES_REQUIRED",
            "current_status": "FAIL_CLOSED_NO_PRODUCTION_ACTIVATIONS",
            "inquiry_or_pending_records_are_active_facts": False,
            "synthetic_controls_are_active_facts": False,
        },
        "read_model_version": READ_MODEL_VERSION,
        "research_controls": research_controls,
        "source_authority": {
            "authorized_round16a_source_sha": SOURCE_SHA,
            "semantic_contract_namespace": SEMANTIC_NAMESPACE,
            "semantic_contract_parent_sha": fixtures["parent_checkpoint_sha"],
            "semantic_contract_source_sha": fixtures["source_sha"],
        },
    }


def build_artifacts() -> dict[str, bytes]:
    model = build_read_model()
    model_bytes = canonical_bytes(model)
    input_bindings = [
        {
            "path": str(path.relative_to(REPO_ROOT)),
            "sha256": sha256_file(path),
        }
        for path in (
            SEMANTIC_FIXTURES,
            SEMANTIC_CENSUS,
            SEMANTIC_HASH_BINDINGS,
            ROUND16A_CENSUS,
        )
    ]
    manifest = {
        "api_version": API_VERSION,
        "artifact_bytes": {"read-model.json": len(model_bytes)},
        "artifact_sha256": {"read-model.json": sha256_bytes(model_bytes)},
        "canonical_serialization": CANONICAL_SERIALIZATION,
        "closure_flags": copy.deepcopy(model["closure_flags"]),
        "counts": copy.deepcopy(model["capabilities"]),
        "deterministic_build_contract": (
            "--check rebuilds twice in memory, compares every byte, then compares "
            "the exact committed artifact set without writing."
        ),
        "fact_boundary": copy.deepcopy(model["fact_boundary"]),
        "generator_version": GENERATOR_VERSION,
        "input_bindings": input_bindings,
        "manifest_version": MANIFEST_VERSION,
        "read_model_version": READ_MODEL_VERSION,
        "source_sha": SOURCE_SHA,
    }
    manifest_bytes = canonical_bytes(manifest)
    files = {
        "manifest.json": manifest_bytes,
        "read-model.json": model_bytes,
    }
    checksum_lines = [
        f"{sha256_bytes(files[name])}  {name}\n" for name in sorted(files)
    ]
    files["CHECKSUMS.sha256"] = "".join(checksum_lines).encode("utf-8")
    return files


def check_artifacts() -> dict[str, bytes]:
    first = build_artifacts()
    second = build_artifacts()
    require(first == second, "IN_MEMORY_DETERMINISM_MISMATCH")
    actual_names = sorted(path.name for path in OUTPUT_ROOT.iterdir()) if OUTPUT_ROOT.exists() else []
    require(actual_names == list(OUTPUT_FILENAMES), "GENERATED_FILE_SET_MISMATCH")
    for name, expected in first.items():
        actual = (OUTPUT_ROOT / name).read_bytes()
        require(actual == expected, f"GENERATED_ARTIFACT_MISMATCH:{name}")
    return first


def write_artifacts() -> dict[str, bytes]:
    files = build_artifacts()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for name in sorted(files):
        (OUTPUT_ROOT / name).write_bytes(files[name])
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify deterministic committed output")
    args = parser.parse_args()
    try:
        files = check_artifacts() if args.check else write_artifacts()
        model = json.loads(files["read-model.json"])
        receipt = {
            "active_product_association_count": model["capabilities"]["active_product_association_count"],
            "active_product_composition_count": model["capabilities"]["active_product_composition_count"],
            "control_association_count": model["capabilities"]["control_association_count"],
            "control_composition_count": model["capabilities"]["control_composition_count"],
            "higher_order_pair_projection_count": sum(
                len(item["internal_pair_links"])
                for item in model["research_controls"]["associations"]
                if item["association_kind"] == "HIGHER_ORDER"
                and item["pair_projection_policy"] != "NONE"
            ),
            "active_pending_review_count": model["capabilities"]["active_pending_review_count"],
            "implicit_hyperedge_projection_count": model["capabilities"]["implicit_hyperedge_projection_count"],
            "mode": "CHECK" if args.check else "WRITE",
            "read_model_sha256": sha256_bytes(files["read-model.json"]),
            "status": "PASS",
        }
        print(json.dumps(receipt, sort_keys=True))
        return 0
    except (OSError, KeyError, TypeError, ValueError) as error:
        print(
            json.dumps(
                {
                    "error": str(error),
                    "mode": "CHECK" if args.check else "WRITE",
                    "status": "FAIL",
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
