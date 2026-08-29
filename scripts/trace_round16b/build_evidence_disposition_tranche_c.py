#!/usr/bin/env python3
"""Build deterministic Round 16B evidence-disposition tranche C.

This additive builder binds published checkpoint 006 and reviews the ten
remaining arity-four-or-greater participant-set families in the immutable
checkpoint-004 local candidate census.  It conserves all 60 linked trigger
occurrences and proves cumulative parent-disposition coverage of all 35
families and all 359 occurrences.

The Sweden 1954 and Hutton 2013 structures receive deterministic, scoped
research identities only.  Both remain INQUIRY_ONLY, product-ineligible,
pending external human review, and forbidden from manufacturing pair or
subset projections.  No active association, product path, or closure claim is
created.
"""

from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from typing import Any

import build_evidence_disposition_tranche_b as base


REPO = base.REPO
RAW = base.RAW
AUTHORIZED_SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
AUTHORIZED_SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
PARENT_CHECKPOINT_SHA = "f97d20b37b58a509d04cdf3bc3385486fc8d173c"
TRANCHE_ID = "CHECKPOINT-007-EVIDENCE-TRANCHE-C"
BUILDER_VERSION = "trace-round16b-evidence-disposition-tranche-c-v1"

OCCURRENCE_PATH = base.OCCURRENCE_PATH
FAMILY_PATH = base.FAMILY_PATH
CROSSWALK_PATH = base.CROSSWALK_PATH
CENSUS_PATH = base.CENSUS_PATH
METHOD_PATH = base.METHOD_PATH
TAXONOMY_PATH = base.TAXONOMY_PATH
GRAPH_PATH = base.GRAPH_PATH
CALIBRATION_PATH = base.CALIBRATION_PATH
TRANCHE_A_OCCURRENCE_PATH = base.TRANCHE_A_OCCURRENCE_PATH
TRANCHE_A_FAMILY_PATH = base.TRANCHE_A_FAMILY_PATH
TRANCHE_A_RECEIPT_PATH = base.TRANCHE_A_RECEIPT_PATH
TRANCHE_B_OCCURRENCE_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-occurrence-disposition-tranche-b-v1.tsv"
TRANCHE_B_FAMILY_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/family-evidence-disposition-tranche-b-v1.tsv"
TRANCHE_B_RECEIPT_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-build-receipt-tranche-b-v1.json"
TRANCHE_B_GENERATOR_PATH = "scripts/trace_round16b/build_evidence_disposition_tranche_b.py"
SOURCE_REGISTRY_PATH = "docs/research/trace-v49-exploration-composition-review-round1/03_COMPOSITION_SCHOLARLY_SOURCE_REGISTRY.tsv"
GENERATOR_PATH = "scripts/trace_round16b/build_evidence_disposition_tranche_c.py"

PINNED_INPUT_SHA256 = dict(base.PINNED_INPUT_SHA256)
PINNED_INPUT_SHA256.update({
    TRANCHE_B_OCCURRENCE_PATH: "8f87bdad1a700202fecdf0f28dfd0016e96a55e49435ba76d5e4c04b958dceaa",
    TRANCHE_B_FAMILY_PATH: "1f6547e799963d14c45335569aaa9a5facf9eb1715afe6c462605acdae16a090",
    TRANCHE_B_RECEIPT_PATH: "143266126e7ec3e06158b56647e91c416ed896fb6ebb067656f88db74d7c952f",
    TRANCHE_B_GENERATOR_PATH: "2532c815bcca68f9c86fbef6b4dc22d7a69617a6f403deb1a303b377ff94438c",
    SOURCE_REGISTRY_PATH: "1f54c0956ca12dfaad472a6644c6102ee13b2e9a46f6c1794e21e1a2d7097dca",
})


FAMILY_SPECS = [
    {
        "ordinal": 26,
        "key": "08555e0036d8fa72ac6454261ba70bfa4ad09988a59f17c92c3401fd0d1d907d",
        "disposition": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
        "rationale": "R15-COMP-008 explicitly keeps the institutionalization/professionalization and photography/typography pairs as distinct, unranked components; two supported pairs do not establish one four-member historical configuration.",
        "scope_status": "CLOSE_DISCONNECTED_PAIR_COMPONENT_PARENT_RETAIN_TWO_SEPARATE_PAIR_PATHS",
        "nonclaims": ["distinct pair components are not one group", "the fixture is a software control, not historical evidence", "no bridge, rank, direction, or chronology is inferred"],
    },
    {
        "ordinal": 27,
        "key": "0c335e4ef6d612535b516a59ac96442d3cbf17affbbd517d57c6d74388f8fd2d",
        "disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "rationale": "The shared-locator bundle joins the contact-zone adaptation/negotiation/rejection review to a separately qualified cultural-transfer bridge; the current cultural-transfer participant is not supported in the same bounded case or sense as the three-node contact-zone configuration.",
        "scope_status": "CLOSE_FOUR_NODE_PARENT_RETAIN_CONTACT_ZONE_TRIAD_AND_TRANSFER_BRIDGE_SEPARATELY",
        "nonclaims": ["a shared locator bundle does not erase source and sense bounds", "cultural transfer is not passive adaptation", "contact-zone alternatives are not chronological stages"],
    },
    {
        "ordinal": 28,
        "key": "89817e7a449f1cc7b574fb1b89c9541f765e52825c5cb62bf0a2bb833e8f970a",
        "disposition": "INQUIRY_ONLY_OR_UNRESOLVED",
        "rationale": "COMP-EVID-026 and its shared-locator bundle identify one Sweden-in-Sydney 1954 exposition configuration containing trade, propaganda, and design diplomacy even though exhibition/trade is not an independently active pair; exact-source, rights, counterevidence, role, and external design-history review remain mandatory before activation.",
        "scope_status": "CREATE_SCOPED_SWEDEN_1954_INQUIRY_IDENTITY_RECONCILE_45_STRUCTURAL_DERIVATIVES",
        "nonclaims": ["no exhibition/trade pair is manufactured", "design diplomacy is not equated with propaganda", "diplomatic intent does not prove reception", "the scoped hyperedge is not projected into any subset"],
    },
    {
        "ordinal": 29,
        "key": "9ba898462d422755c40d8ef6228e8a7faa6e74dd9b4b0499f82694e8ae4515da",
        "disposition": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
        "rationale": "The two R15 fixtures require a split or reject an unsupported bridge, and R14-NARY-004 is explicitly synthetic-layout-only with expected result SPLIT; neither pair bindings nor renderability validate the four-node group.",
        "scope_status": "CLOSE_SPLIT_PARENT_RETAIN_SEPARATE_SUPPORTED_PAIRS_AND_HARD_NEGATIVES",
        "nonclaims": ["pair bindings are not group evidence", "a synthetic layout cannot activate history", "split means separate inquiry components, not proven historical separation"],
    },
    {
        "ordinal": 30,
        "key": "d936154cb902968e2e5e0404e3dffaa3b61b47480b69f600b766b96351b66148",
        "disposition": "INQUIRY_ONLY_OR_UNRESOLVED",
        "rationale": "COMP-EVID-021 supports an article-level material-chain inquiry spanning production and consumption sites, material displacement, and supply-chain language, while the active pair graph has only four of ten pairs and two components; the current production/consumption senses and the distinction between article-method and three separate material cases remain unresolved.",
        "scope_status": "CREATE_SCOPED_HUTTON_METHOD_INQUIRY_IDENTITY_PENDING_SENSE_AND_CASE_SPLIT_AUDIT",
        "nonclaims": ["the article-level method is not one single material case", "current mediation-oriented production and consumption senses are not silently replaced", "sparse hyperedge review creates no missing pair", "read access does not authorize redistribution"],
    },
    {
        "ordinal": 31,
        "key": "5f28402103d5315b59cf0f022e43f679658b1e4d1e960072ae945a66c87d5669",
        "disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "rationale": "R15-COMP-024 is an explicit failed temporal-near-neighbour control combining six distinct periods, geographies, media, and cases with no active internal pair or qualified shared historical configuration.",
        "scope_status": "CLOSE_TEMPORAL_CASE_AND_MEDIUM_CONFLICT_PARENT",
        "nonclaims": ["chronological contrast alone is not disassociation evidence", "design-history prominence is not group evidence", "no cross-period influence or genealogy is asserted"],
    },
    {
        "ordinal": 32,
        "key": "6bd3485742a465105a9adb73f09f1d700f9601abf114d49ba37d02cbbe0337f7",
        "disposition": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
        "rationale": "R15-COMP-020 explicitly renders three source-supported associations as unranked separate components; the six-node parent has three disjoint active pairs among fifteen possible pairs and no group-level evidence.",
        "scope_status": "CLOSE_THREE_DISCONNECTED_PAIR_COMPONENT_PARENT_RETAIN_SEPARATE_PAIRS",
        "nonclaims": ["three source-supported pairs are not one six-node group", "unranked visibility does not prove historical coherence", "no bridging pair or hyperedge is invented"],
    },
    {
        "ordinal": 33,
        "key": "b2f6aef3aded759512be2f639056c7dacb37707ae596bf8c078035ccd5cd96d5",
        "disposition": "HARD_NEGATIVE",
        "rationale": "R15-COMP-023 is a failed hard-negative control set containing R14-ASSOC-025, R14-ASSOC-027, and R14-ASSOC-028; the six-node structure has no active internal pair and cannot enter composition.",
        "scope_status": "CLOSE_HARD_NEGATIVE_CONTROL_PARENT_NO_PROJECTION",
        "nonclaims": ["hard-negative controls are not association evidence", "a future separately evidenced scoped hyperedge is not logically impossible", "no pair or subset projection is created"],
    },
    {
        "ordinal": 34,
        "key": "ed83d4054c6d0fa7f02d620e5253572e58205ac5d7839b870b10748486883188",
        "disposition": "HARD_NEGATIVE",
        "rationale": "R15-COMP-022 is a failed control set containing the hard-negative R14-ASSOC-023 and R14-ASSOC-024 assessments alongside one qualified-but-inactive bridge; no active internal pair or coherent six-node configuration survives.",
        "scope_status": "CLOSE_HARD_NEGATIVE_AND_INSUFFICIENT_CONTROL_PARENT_NO_PROJECTION",
        "nonclaims": ["qualified-but-inactive is not support", "unrelated source families are not one group", "no hard-negative pair is bypassed by a synthetic hyperedge"],
    },
    {
        "ordinal": 35,
        "key": "3d978cc2b2ed5a65ad9841e04307657d41e0a23034f54b821fa59ce974e43e00",
        "disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "rationale": "R15-COMP-025 exercises four hard-negative controls, and the exact eight-node family also contains the separately governed R14-ASSOC-024 hard-negative pair; those five negatives and three active pairs come from unrelated bounded contexts and do not form one shared case, scope, or mechanism.",
        "scope_status": "CLOSE_EIGHT_NODE_MIXED_SCOPE_PARENT_RETAIN_SEPARATE_PAIR_AND_NEGATIVE_CONTROLS",
        "nonclaims": ["three active pairs do not repair five internal hard-negative controls", "broad design-historiography membership is not association evidence", "no universal transformation, professionalization, or commodification sequence is asserted"],
    },
]


SOURCE_CLASS_BY_SURFACE = base.SOURCE_CLASS_BY_SURFACE
EXPECTED_SOURCE_CLASS_COUNTS = {
    "R13_EXACT_EVIDENCE_RECORD": 2,
    "R14_SHARED_LOCATOR_PROVENANCE": 2,
    "R14_SYNTHETIC_NARY_CONTROL": 1,
    "R15_RESEARCH_FIXTURE": 10,
    "R16A_CONNECTED_SUBGRAPH": 14,
    "R16A_PRESENTATION_TOPOLOGY": 6,
    "R16A_PRODUCT_COMPOSITION": 24,
    "R16_LEGACY_PRODUCT_COMPOSITION": 1,
}
EXPECTED_GENERIC_CLASS_COUNTS = {
    "EVIDENCE_BEARING_INPUT": 4,
    "GLOBAL_COHERENCE_NEGATIVE_CONTROL": 2,
    "HARD_NEGATIVE_CONTROL": 3,
    "PAIR_COMPONENT_CONTROL": 2,
    "PAIR_GRAPH_RENDER_CONTROL": 2,
    "STRUCTURAL_ECHO": 45,
    "SYNTHETIC_CONTROL": 1,
    "TEMPORAL_SCOPE_NEGATIVE_CONTROL": 1,
}
EXPECTED_FAMILY_SOURCE_COUNTS = {
    "08555e00": {"R15_RESEARCH_FIXTURE": 1},
    "0c335e4e": {"R14_SHARED_LOCATOR_PROVENANCE": 1},
    "89817e7a": {"R13_EXACT_EVIDENCE_RECORD": 1, "R14_SHARED_LOCATOR_PROVENANCE": 1, "R15_RESEARCH_FIXTURE": 2, "R16A_CONNECTED_SUBGRAPH": 14, "R16A_PRESENTATION_TOPOLOGY": 6, "R16A_PRODUCT_COMPOSITION": 24, "R16_LEGACY_PRODUCT_COMPOSITION": 1},
    "9ba89846": {"R14_SYNTHETIC_NARY_CONTROL": 1, "R15_RESEARCH_FIXTURE": 2},
    "d936154c": {"R13_EXACT_EVIDENCE_RECORD": 1},
    "5f284021": {"R15_RESEARCH_FIXTURE": 1},
    "6bd34857": {"R15_RESEARCH_FIXTURE": 1},
    "b2f6aef3": {"R15_RESEARCH_FIXTURE": 1},
    "ed83d405": {"R15_RESEARCH_FIXTURE": 1},
    "3d978cc2": {"R15_RESEARCH_FIXTURE": 1},
}

R15_CLASS_BY_FIXTURE = {
    "R15-COMP-002": "PAIR_GRAPH_RENDER_CONTROL",
    "R15-COMP-005": "GLOBAL_COHERENCE_NEGATIVE_CONTROL",
    "R15-COMP-008": "PAIR_COMPONENT_CONTROL",
    "R15-COMP-009": "GLOBAL_COHERENCE_NEGATIVE_CONTROL",
    "R15-COMP-011": "PAIR_GRAPH_RENDER_CONTROL",
    "R15-COMP-020": "PAIR_COMPONENT_CONTROL",
    "R15-COMP-022": "HARD_NEGATIVE_CONTROL",
    "R15-COMP-023": "HARD_NEGATIVE_CONTROL",
    "R15-COMP-024": "TEMPORAL_SCOPE_NEGATIVE_CONTROL",
    "R15-COMP-025": "HARD_NEGATIVE_CONTROL",
}

OCCURRENCE_FIELDS = base.OCCURRENCE_FIELDS
FAMILY_FIELDS = list(base.FAMILY_FIELDS)
_PAIR_INSERT = FAMILY_FIELDS.index("final_parent_disposition")
FAMILY_FIELDS[_PAIR_INSERT:_PAIR_INSERT] = [
    "internal_hard_negative_pair_count",
    "internal_hard_negative_assessment_ids_json",
    "active_pair_graph_component_count",
    "active_pair_graph_connected",
]
_QUEUE_INSERT = FAMILY_FIELDS.index("direct_group_support_status")
FAMILY_FIELDS[_QUEUE_INSERT:_QUEUE_INSERT] = ["scoped_inquiry_identity_count"]

QUEUE_FIELDS = [
    "parent_checkpoint_sha", "review_tranche", "queue_ref", "queue_id",
    "queue_record_kind", "parent_candidate_id", "parent_family_ordinal",
    "queue_action", "association_id", "association_revision_id",
    "association_identity_created", "association_activation_status",
    "participant_labels_json", "participant_sense_ids_json", "arity",
    "scope_key", "scope_summary", "source_ids_json",
    "evidence_occurrence_ids_json", "evidence_locator_summary",
    "support_hypothesis", "active_pair_graph_status", "required_gates",
    "rights_review_status", "source_text_review_status", "human_review_status",
    "counterevidence_review_status", "pair_projection_policy",
    "pair_projection_created", "subset_projection_created",
    "product_path_created", "product_eligibility", "queue_status",
    "explicit_nonclaims_json", "record_sha256",
]
INPUT_FIELDS = base.INPUT_FIELDS
GAP_FIELDS = [
    "gap_id", "last_reviewed_checkpoint", "gap", "severity", "status",
    "checkpoint007_tranche_c_evidence", "authority_dependency",
    "required_next_action", "record_sha256",
]

canonical_json = base.canonical_json
sha256_bytes = base.sha256_bytes
sha256_text = base.sha256_text
sha256_file = base.sha256_file
finalize_row = base.finalize_row
read_tsv = base.read_tsv
read_json = base.read_json
tsv_bytes = base.tsv_bytes
json_bytes = base.json_bytes
source_row_details = base.source_row_details
input_record_count = base.input_record_count


def source_class(occurrence: dict[str, str]) -> str:
    try:
        return SOURCE_CLASS_BY_SURFACE[occurrence["input_surface_id"]]
    except KeyError as exc:
        raise AssertionError(f"unclassified tranche-C input surface: {occurrence['input_surface_id']}") from exc


def generic_class(occurrence: dict[str, str], exact_source_class: str) -> str:
    if exact_source_class in {"R13_EXACT_EVIDENCE_RECORD", "R14_SHARED_LOCATOR_PROVENANCE"}:
        return "EVIDENCE_BEARING_INPUT"
    if exact_source_class == "R14_SYNTHETIC_NARY_CONTROL":
        return "SYNTHETIC_CONTROL"
    if exact_source_class == "R15_RESEARCH_FIXTURE":
        refs = json.loads(occurrence["input_record_refs_json"])
        if len(refs) != 1 or refs[0] not in R15_CLASS_BY_FIXTURE:
            raise AssertionError(f"unclassified tranche-C R15 fixture: {refs}")
        return R15_CLASS_BY_FIXTURE[refs[0]]
    return "STRUCTURAL_ECHO"


def classification_policy(evidence_class: str) -> tuple[str, str, str, str, str]:
    if evidence_class == "EVIDENCE_BEARING_INPUT":
        return (
            "LOCATOR_BEARING_BOUNDED_INPUT_REQUIRES_TRANCHE_C_GROUP_REVIEW",
            "The local row is a reviewable bounded input, not an inherited higher-order support or activation decision.",
            "SCOPED_REVIEW_INPUT_NOT_AUTOMATIC_SUPPORT",
            "BOUNDED_LOCAL_RECORD_REVIEWED_EXTERNAL_EXACT_TEXT_REVIEW_OPEN",
            "OPEN_EXTERNAL_ACCESS_AND_RIGHTS_RECONCILIATION",
        )
    if evidence_class == "STRUCTURAL_ECHO":
        return (
            "ROUND16_OR_ROUND16A_STRUCTURAL_DESCENDANT_NOT_EVIDENCE",
            "A prior subgraph, topology, product composition, or legacy composition is a reconciliation target, not historical group evidence.",
            "NOT_EVIDENCE_RECONCILIATION_ONLY",
            "NOT_APPLICABLE_STRUCTURAL_RECORD",
            "NOT_APPLICABLE_STRUCTURAL_RECORD",
        )
    if evidence_class == "SYNTHETIC_CONTROL":
        return (
            "SYNTHETIC_NARY_LAYOUT_CONTROL_EXPECTS_SPLIT",
            "The n-ary fixture tests pair binding and split behavior only; synthetic layout output is not historical evidence.",
            "NOT_EVIDENCE_TEST_CONTROL_ONLY",
            "NOT_APPLICABLE_SYNTHETIC_CONTROL",
            "NOT_APPLICABLE_CONTROL_RECORD",
        )
    detail_by_class = {
        "PAIR_COMPONENT_CONTROL": "R15_SEPARATE_PAIR_COMPONENT_CONTROL",
        "PAIR_GRAPH_RENDER_CONTROL": "R15_PAIR_GRAPH_RENDER_OR_PRUNING_CONTROL",
        "GLOBAL_COHERENCE_NEGATIVE_CONTROL": "R15_UNSUPPORTED_BRIDGE_OR_SPLIT_CONTROL",
        "TEMPORAL_SCOPE_NEGATIVE_CONTROL": "R15_TEMPORAL_SCOPE_NEGATIVE_CONTROL",
        "HARD_NEGATIVE_CONTROL": "R15_HARD_NEGATIVE_CONTROL_SET",
    }
    return (
        detail_by_class[evidence_class],
        "The R15 fixture is a software and research-control record; its explicit component, split, scope, or negative semantics constrain the parent but cannot supply historical group evidence.",
        "CONTROL_INPUT_NOT_SUPPORT",
        "NOT_APPLICABLE_CONTROL_RECORD",
        "NOT_APPLICABLE_CONTROL_RECORD",
    )


def graph_component_count(labels: list[str], active_pairs: list[dict[str, Any]]) -> int:
    adjacency = {label: set() for label in labels}
    for edge in active_pairs:
        adjacency[edge["label_a"]].add(edge["label_b"])
        adjacency[edge["label_b"]].add(edge["label_a"])
    remaining = set(labels)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            for neighbour in adjacency[stack.pop()]:
                if neighbour in remaining:
                    remaining.remove(neighbour)
                    stack.append(neighbour)
    return count


def scoped_identity(family: dict[str, str], scope_key: str) -> tuple[str, str]:
    identity = {
        "association_class": "HIGHER_ORDER",
        "participant_sense_ids": json.loads(family["participant_sense_ids_json"]),
        "order_semantics": "UNORDERED",
        "role_semantics": "NONE_UNTIL_EXTERNAL_REVIEW",
        "scope_key": scope_key,
    }
    association_id = "R16B-ASSOC:" + sha256_text(canonical_json(identity))
    revision = {
        "association_id": association_id,
        "activation_status": "INQUIRY_ONLY",
        "final_disposition": "INQUIRY_ONLY_OR_UNRESOLVED",
        "pair_projection_policy": "NONE",
        "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
        "product_eligibility": "INELIGIBLE",
        "review_tranche": TRANCHE_ID,
    }
    return association_id, "R16B-ASSOC-REV:" + sha256_text(canonical_json(revision))


def build_queue_rows(
    families_by_key: dict[str, dict[str, str]],
    occurrences_by_family: dict[str, list[dict[str, str]]],
    pair_status_by_family: dict[str, str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(
        queue_ref: str,
        family_prefix: str,
        kind: str,
        action: str,
        scope_key: str,
        scope_summary: str,
        source_ids: list[str],
        evidence_ids: list[str],
        locator_summary: str,
        support_hypothesis: str,
        required_gates: str,
        nonclaims: list[str],
        create_identity: bool = False,
    ) -> None:
        matches = [value for key, value in families_by_key.items() if key.startswith(family_prefix)]
        if len(matches) != 1:
            raise AssertionError(f"queue family prefix must resolve once: {family_prefix}")
        family = matches[0]
        association_id = ""
        revision_id = ""
        if create_identity:
            association_id, revision_id = scoped_identity(family, scope_key)
        identity = {
            "queue_ref": queue_ref,
            "parent_candidate_id": family["candidate_id"],
            "queue_action": action,
            "scope_key": scope_key,
            "association_id": association_id,
        }
        rows.append(finalize_row({
            "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
            "review_tranche": TRANCHE_ID,
            "queue_ref": queue_ref,
            "queue_id": "R16B-TRANCHE-C-QUEUE:" + sha256_text(canonical_json(identity)),
            "queue_record_kind": kind,
            "parent_candidate_id": family["candidate_id"],
            "parent_family_ordinal": next(spec["ordinal"] for spec in FAMILY_SPECS if spec["key"] == family["participant_set_key"]),
            "queue_action": action,
            "association_id": association_id,
            "association_revision_id": revision_id,
            "association_identity_created": "true" if create_identity else "false",
            "association_activation_status": "INQUIRY_ONLY" if create_identity else "INACTIVE",
            "participant_labels_json": family["canonical_labels_json"],
            "participant_sense_ids_json": family["participant_sense_ids_json"],
            "arity": family["arity"],
            "scope_key": scope_key,
            "scope_summary": scope_summary,
            "source_ids_json": canonical_json(source_ids),
            "evidence_occurrence_ids_json": canonical_json(sorted(evidence_ids)),
            "evidence_locator_summary": locator_summary,
            "support_hypothesis": support_hypothesis,
            "active_pair_graph_status": pair_status_by_family[family["candidate_id"]],
            "required_gates": required_gates,
            "rights_review_status": "OPEN_EXTERNAL_RIGHTS_AND_REDISTRIBUTION_REVIEW" if create_identity else "NOT_APPLICABLE_FINAL_PARENT_CONTROL",
            "source_text_review_status": "OPEN_EXTERNAL_EXACT_TEXT_AND_LOCATOR_REVIEW" if create_identity else "NOT_APPLICABLE_FINAL_PARENT_CONTROL",
            "human_review_status": "OPEN_EXTERNAL_DESIGN_HISTORY_REVIEW" if create_identity else "NOT_PENDING_FOR_FINAL_NON_SUPPORTING_PARENT",
            "counterevidence_review_status": "OPEN_ADAPTIVE_FALSIFICATION_REVIEW" if create_identity else "NOT_PENDING_FOR_FINAL_NON_SUPPORTING_PARENT",
            "pair_projection_policy": "NONE",
            "pair_projection_created": "false",
            "subset_projection_created": "false",
            "product_path_created": "false",
            "product_eligibility": "INELIGIBLE",
            "queue_status": "OPEN_INQUIRY_ONLY_NOT_ACTIVE" if create_identity else ("OPEN_RECONCILIATION_CONTROL" if kind != "PARENT_CLOSE_CONTROL" else "CLOSED_PARENT_CONTROL"),
            "explicit_nonclaims_json": canonical_json(nonclaims),
        }))

    def family_occ(prefix: str) -> list[dict[str, str]]:
        keys = [key for key in families_by_key if key.startswith(prefix)]
        if len(keys) != 1:
            raise AssertionError(f"family occurrence prefix must resolve once: {prefix}")
        return occurrences_by_family[families_by_key[keys[0]]["candidate_id"]]

    add("TCQ-001", "08555e00", "PARENT_CLOSE_CONTROL", "CLOSE_DISCONNECTED_PAIR_COMPONENT_PARENT", "DISTINCT_PAIR_COMPONENTS", "Institutional/professional and photography/typography pair components remain separate.", [], [row["trigger_occurrence_id"] for row in family_occ("08555e00")], "R15-COMP-008", "PAIRWISE_COMPONENTS_NOT_GROUP", "FINAL_PARENT_DISPOSITION", ["no unsupported bridge", "fixture output is not evidence"])
    add("TCQ-002", "0c335e4e", "PARENT_CLOSE_CONTROL", "CLOSE_SCOPE_CONFLICT_PARENT", "CONTACT_ZONE_VERSUS_TRANSFER_BRIDGE", "Contact-zone triad and qualified cultural-transfer bridge remain separately bounded.", ["COMP-SRC-013", "COMP-SRC-014"], [row["trigger_occurrence_id"] for row in family_occ("0c335e4e")], "p.354; Contact Zone section", "SCOPE_CONFLICT_NOT_GROUP", "FINAL_PARENT_DISPOSITION", ["no cross-source flattening", "no passive-transfer equivalence"])

    sweden_rows = family_occ("89817e7a")
    sweden_evidence = [row["trigger_occurrence_id"] for row in sweden_rows if source_class(row) in {"R13_EXACT_EVIDENCE_RECORD", "R14_SHARED_LOCATOR_PROVENANCE"}]
    sweden_structural = [row["trigger_occurrence_id"] for row in sweden_rows if source_class(row) in {"R16A_CONNECTED_SUBGRAPH", "R16A_PRESENTATION_TOPOLOGY", "R16A_PRODUCT_COMPOSITION", "R16_LEGACY_PRODUCT_COMPOSITION"}]
    if len(sweden_evidence) != 2 or len(sweden_structural) != 45:
        raise AssertionError("Sweden evidence/derivative partition changed")
    add("TCQ-003", "89817e7a", "SCOPED_INQUIRY_IDENTITY", "CREATE_INQUIRY_ONLY_HIGHER_ORDER_IDENTITY", "SWEDEN_IN_SYDNEY_1954", "Sweden at David Jones' exposition, Sydney, 1954; exact four-concept source-bound inquiry.", ["COMP-SRC-025"], sweden_evidence, "COMP-EVID-026; R14 provenance; p.282; DOI 10.1080/10331867.2023.2282294", "DIRECT_GROUP_HYPOTHESIS_NOT_FINAL_SUPPORT", "EXACT_TEXT; RIGHTS; SENSE; ROLE; SAME_CASE; COUNTEREVIDENCE; EXTERNAL_HUMAN_REVIEW", ["no exhibition/trade pair", "no audience-acceptance claim", "no diplomacy/propaganda equivalence", "no subset projection"], True)
    add("TCQ-004", "89817e7a", "DERIVATIVE_RECONCILIATION", "RECONCILE_PRIOR_STRUCTURAL_DESCENDANTS", "SWEDEN_1954_PRIOR_DERIVATIVE_SET", "Fourteen subgraphs, six topologies, twenty-four Round 16A product compositions, and one legacy composition.", ["COMP-SRC-025"], sweden_structural, "45 structural descendants", "RETAIN_ONLY_IF_TRACED_TO_LATER_GOVERNED_ACTIVE_ASSOCIATION", "EXTERNAL_DECISION; PRODUCT_RECONCILIATION", ["renderability is not group support", "compatibility does not preserve a composition automatically"])

    add("TCQ-005", "9ba89846", "PARENT_CLOSE_CONTROL", "CLOSE_UNSUPPORTED_BRIDGE_AND_SPLIT_PARENT", "R15_SPLIT_CONTROL", "Two disconnected pair components plus three internal hard-negative pair assessments.", [], [row["trigger_occurrence_id"] for row in family_occ("9ba89846")], "R15-COMP-005; R15-COMP-009; R14-NARY-004", "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE", "FINAL_PARENT_DISPOSITION", ["synthetic layout is not evidence", "split is not historical separation"])

    hutton_rows = family_occ("d936154c")
    hutton_evidence = [row["trigger_occurrence_id"] for row in hutton_rows]
    add("TCQ-006", "d936154c", "SCOPED_INQUIRY_IDENTITY", "CREATE_INQUIRY_ONLY_HIGHER_ORDER_IDENTITY", "HUTTON_RECIPROCAL_LANDSCAPES_ARTICLE_METHOD_2013", "Article-method level material-chain inquiry across production/consumption sites and material movements; not one merged case.", ["COMP-SRC-020"], hutton_evidence, "COMP-EVID-021; abstract; p.40; DOI 10.1080/18626033.2013.798922", "SPARSE_DISCONNECTED_DIRECT_HYPEREDGE_HYPOTHESIS_NOT_FINAL_SUPPORT", "EXACT_TEXT; RIGHTS; NEW_OR_CORRECTED_SENSES; ARTICLE_METHOD_VERSUS_CASE_SPLIT; COUNTEREVIDENCE; EXTERNAL_HUMAN_REVIEW", ["no invented missing pairs", "no single-case claim", "no silent production-sense substitution", "no full-text redistribution"], True)
    add("TCQ-007", "d936154c", "SENSE_AND_CASE_SPLIT_REVIEW", "AUDIT_METHOD_LEVEL_AND_THREE_CASE_SPECIFIC_IDENTITIES", "HUTTON_SENSE_AND_CASE_SPLIT", "Resolve production and consumption sense compatibility and distinguish article-method coherence from each material case.", ["COMP-SRC-020"], hutton_evidence, "COMP-EVID-021; abstract; p.40", "IDENTITY_SPLIT_OR_REFORMULATION_REQUIRED_BEFORE_ACTIVATION", "EXACT_SENSES; CASE_MEMBERSHIP; ROLE; RIGHTS; EXTERNAL_HUMAN_REVIEW", ["method-level coherence does not imply one case", "case-specific children are not automatic subsets"])

    add("TCQ-008", "5f284021", "PARENT_CLOSE_CONTROL", "CLOSE_TEMPORAL_SCOPE_CONFLICT_PARENT", "FAILED_TEMPORAL_NEAR_NEIGHBOUR_CONTROL", "Six unrelated periods, geographies, media, and cases.", [], [row["trigger_occurrence_id"] for row in family_occ("5f284021")], "R15-COMP-024", "BOUNDED_SENSE_OR_SCOPE_CONFLICT", "FINAL_PARENT_DISPOSITION", ["chronology alone is not association evidence", "no reception genealogy"])
    add("TCQ-009", "6bd34857", "PARENT_CLOSE_CONTROL", "CLOSE_THREE_DISCONNECTED_PAIR_COMPONENT_PARENT", "THREE_SEPARATE_PAIR_COMPONENTS", "Consumer-culture/advertising, education/craft, and photography/typography remain separate.", [], [row["trigger_occurrence_id"] for row in family_occ("6bd34857")], "R15-COMP-020", "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE", "FINAL_PARENT_DISPOSITION", ["separate pair support is not six-node support", "no bridge is invented"])
    add("TCQ-010", "b2f6aef3", "PARENT_CLOSE_CONTROL", "CLOSE_HARD_NEGATIVE_PARENT", "FAILED_HARD_NEGATIVE_CONTROL_SET_B", "Three hard-negative pair assessments defeat the exact six-node fixture parent.", [], [row["trigger_occurrence_id"] for row in family_occ("b2f6aef3")], "R15-COMP-023; R14-ASSOC-025/027/028", "HARD_NEGATIVE", "FINAL_PARENT_DISPOSITION", ["no pair or subset projection", "future separately evidenced scope not precluded"])
    add("TCQ-011", "ed83d405", "PARENT_CLOSE_CONTROL", "CLOSE_HARD_NEGATIVE_PARENT", "FAILED_HARD_NEGATIVE_CONTROL_SET_A", "Two hard-negative pair assessments and one qualified-but-inactive bridge defeat the exact six-node fixture parent.", [], [row["trigger_occurrence_id"] for row in family_occ("ed83d405")], "R15-COMP-022; R14-ASSOC-022/023/024", "HARD_NEGATIVE", "FINAL_PARENT_DISPOSITION", ["qualified-but-inactive is not support", "no negative pair bypass"])
    add("TCQ-012", "3d978cc2", "PARENT_CLOSE_CONTROL", "CLOSE_MIXED_SCOPE_PARENT", "FAILED_HARD_NEGATIVE_CONTROL_SET_D", "Five internal hard-negative pairs and three unrelated active pairs remain bounded to separate contexts.", [], [row["trigger_occurrence_id"] for row in family_occ("3d978cc2")], "R15-COMP-025; R14-ASSOC-024/032/033/034/035", "BOUNDED_SENSE_OR_SCOPE_CONFLICT", "FINAL_PARENT_DISPOSITION", ["broad historiography membership is not group support", "no universal sequence"])

    rows.sort(key=lambda row: row["queue_ref"])
    if [row["queue_ref"] for row in rows] != [f"TCQ-{value:03d}" for value in range(1, 13)]:
        raise AssertionError("tranche-C queue references changed")
    expected_kinds = {"DERIVATIVE_RECONCILIATION": 1, "PARENT_CLOSE_CONTROL": 8, "SCOPED_INQUIRY_IDENTITY": 2, "SENSE_AND_CASE_SPLIT_REVIEW": 1}
    if dict(Counter(row["queue_record_kind"] for row in rows)) != expected_kinds:
        raise AssertionError("tranche-C queue kind distribution changed")
    identity_rows = [row for row in rows if row["association_identity_created"] == "true"]
    if len(identity_rows) != 2 or any(row["association_activation_status"] != "INQUIRY_ONLY" or row["product_eligibility"] != "INELIGIBLE" for row in identity_rows):
        raise AssertionError("exactly two inquiry-only, ineligible identities are required")
    if any(row["pair_projection_created"] != "false" or row["subset_projection_created"] != "false" or row["product_path_created"] != "false" or row["pair_projection_policy"] != "NONE" for row in rows):
        raise AssertionError("queue projection or product creation is forbidden")
    return rows


def build_artifacts() -> dict[str, bytes]:
    for relative, expected in PINNED_INPUT_SHA256.items():
        if not (REPO / relative).exists():
            raise AssertionError(f"pinned input is missing: {relative}")
        actual = sha256_file(relative)
        if actual != expected:
            raise AssertionError(f"pinned input changed: {relative}: {actual} != {expected}")

    parent_census = read_json(CENSUS_PATH)
    if parent_census["local_candidate_family_count"] != 35 or parent_census["trigger_occurrence_count"] != 359 or any(parent_census["closure"].values()):
        raise AssertionError("checkpoint-004 candidate boundary changed")
    tranche_b_receipt = read_json(TRANCHE_B_RECEIPT_PATH)
    if tranche_b_receipt["status"] != "PASS_FAIL_CLOSED_TRANCHE_B" or tranche_b_receipt["cumulative_disposed_family_count"] != 25 or tranche_b_receipt["remaining_undisposed_family_count"] != 10:
        raise AssertionError("published tranche-B receipt boundary changed")

    taxonomy = {row["disposition"]: row for row in read_tsv(TAXONOMY_PATH)}
    for spec in FAMILY_SPECS:
        governed = taxonomy.get(spec["disposition"])
        if governed is None or governed["status_class"] != "FINAL_NON_SUPPORTING" or governed["potentially_active"] != "false":
            raise AssertionError(f"tranche-C disposition must be final non-supporting: {spec['disposition']}")

    occurrences = read_tsv(OCCURRENCE_PATH)
    families = read_tsv(FAMILY_PATH)
    occurrence_by_id = {row["trigger_occurrence_id"]: row for row in occurrences}
    family_by_key = {row["participant_set_key"]: row for row in families}
    if len(occurrence_by_id) != 359 or len(family_by_key) != 35:
        raise AssertionError("checkpoint-004 occurrence/family uniqueness changed")

    prior_occurrence_ids = set()
    prior_family_keys = set()
    prior_family_rows = []
    for occurrence_path, family_path, expected_occurrences, expected_families in [
        (TRANCHE_A_OCCURRENCE_PATH, TRANCHE_A_FAMILY_PATH, 112, 11),
        (TRANCHE_B_OCCURRENCE_PATH, TRANCHE_B_FAMILY_PATH, 187, 14),
    ]:
        occurrence_rows = read_tsv(occurrence_path)
        family_rows = read_tsv(family_path)
        if len(occurrence_rows) != expected_occurrences or len(family_rows) != expected_families:
            raise AssertionError(f"published prior tranche boundary changed: {family_path}")
        ids = {row["trigger_occurrence_id"] for row in occurrence_rows}
        keys = {row["participant_set_key"] for row in family_rows}
        if prior_occurrence_ids.intersection(ids) or prior_family_keys.intersection(keys):
            raise AssertionError("prior evidence tranches overlap")
        prior_occurrence_ids.update(ids)
        prior_family_keys.update(keys)
        prior_family_rows.extend(family_rows)
    if len(prior_occurrence_ids) != 299 or len(prior_family_keys) != 25:
        raise AssertionError("cumulative tranche-A/B boundary changed")

    graph = read_json(GRAPH_PATH)
    active_edge_by_labels = {tuple(sorted((edge["label_a"], edge["label_b"]))): edge for edge in graph["edges"]}
    calibration_rows = read_tsv(CALIBRATION_PATH)
    calibration_by_labels = {tuple(sorted((row["node_a"], row["node_b"]))): row for row in calibration_rows}

    selected_occurrence_ids = []
    selected_families: dict[str, dict[str, str]] = {}
    active_pairs_by_family: dict[str, list[dict[str, Any]]] = {}
    hard_negatives_by_family: dict[str, list[dict[str, str]]] = {}
    component_count_by_family: dict[str, int] = {}
    pair_status_by_family: dict[str, str] = {}
    for spec in FAMILY_SPECS:
        family = family_by_key.get(spec["key"])
        if family is None or int(family["arity"]) < 4:
            raise AssertionError(f"missing or low-arity tranche-C family: {spec['key']}")
        selected_families[spec["key"]] = family
        family_occurrence_ids = json.loads(family["trigger_occurrence_ids_json"])
        if len(family_occurrence_ids) != int(family["occurrence_count"]):
            raise AssertionError(f"family occurrence count mismatch: {family['candidate_id']}")
        selected_occurrence_ids.extend(family_occurrence_ids)
        labels = json.loads(family["canonical_labels_json"])
        pairs = [active_edge_by_labels[key] for key in (tuple(sorted(value)) for value in itertools.combinations(labels, 2)) if key in active_edge_by_labels]
        negatives = [calibration_by_labels[key] for key in (tuple(sorted(value)) for value in itertools.combinations(labels, 2)) if key in calibration_by_labels and calibration_by_labels[key]["hard_negative"] == "true"]
        components = graph_component_count(labels, pairs)
        active_pairs_by_family[family["candidate_id"]] = pairs
        hard_negatives_by_family[family["candidate_id"]] = negatives
        component_count_by_family[family["candidate_id"]] = components
        pair_status_by_family[family["candidate_id"]] = f"ACTIVE_PAIRS_{len(pairs)}_OF_{len(labels) * (len(labels) - 1) // 2};COMPONENTS_{components}"

    if len(selected_occurrence_ids) != 60 or len(set(selected_occurrence_ids)) != 60 or prior_occurrence_ids.intersection(selected_occurrence_ids):
        raise AssertionError("tranche C must bind exactly 60 new occurrences")
    if prior_family_keys.intersection(selected_families):
        raise AssertionError("tranche C parent families overlap prior tranches")
    if prior_occurrence_ids | set(selected_occurrence_ids) != set(occurrence_by_id) or prior_family_keys | set(selected_families) != set(family_by_key):
        raise AssertionError("all 35 families and 359 occurrences must be partitioned exactly")

    d936 = selected_families[FAMILY_SPECS[4]["key"]]
    if len(active_pairs_by_family[d936["candidate_id"]]) != 4 or component_count_by_family[d936["candidate_id"]] != 2:
        raise AssertionError("Hutton sparse/disconnected hyperedge control changed")
    sweden = selected_families[FAMILY_SPECS[2]["key"]]
    sweden_labels = json.loads(sweden["canonical_labels_json"])
    if len(active_pairs_by_family[sweden["candidate_id"]]) != 5 or tuple(sorted(("exhibition", "trade"))) in active_edge_by_labels or set(sweden_labels) != {"exhibition", "trade", "propaganda", "design diplomacy"}:
        raise AssertionError("Sweden sparse exact-group control changed")

    occurrence_rows: list[dict[str, Any]] = []
    rows_by_family: dict[str, list[dict[str, Any]]] = {}
    for spec in FAMILY_SPECS:
        family = selected_families[spec["key"]]
        rows_by_family[family["candidate_id"]] = []
        for occurrence_id in json.loads(family["trigger_occurrence_ids_json"]):
            source = occurrence_by_id[occurrence_id]
            exact_class = source_class(source)
            evidence_class = generic_class(source, exact_class)
            detail, reason, use, source_text, rights = classification_policy(evidence_class)
            upstream_ids, source_ids, locators = source_row_details(source)
            if spec["key"].startswith("89817e7a") and evidence_class == "EVIDENCE_BEARING_INPUT":
                group_status = "SCOPED_SWEDEN_DIRECT_HYPEREDGE_HYPOTHESIS_NOT_ACTIVATED"
            elif spec["key"].startswith("d936154c") and evidence_class == "EVIDENCE_BEARING_INPUT":
                group_status = "SCOPED_HUTTON_SPARSE_HYPEREDGE_HYPOTHESIS_NOT_ACTIVATED"
            else:
                group_status = "NOT_GOVERNED_SUPPORT"
            row = finalize_row({
                "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
                "review_tranche": TRANCHE_ID,
                "family_ordinal": spec["ordinal"],
                "candidate_id": family["candidate_id"],
                "participant_set_key": family["participant_set_key"],
                "trigger_occurrence_id": occurrence_id,
                "source_occurrence_sha256": source["occurrence_sha256"],
                "trigger_id": source["trigger_id"],
                "trigger_class": source["trigger_class"],
                "emission_kind": source["emission_kind"],
                "source_path": source["source_path"],
                "input_surface_id": source["input_surface_id"],
                "input_record_refs_json": source["input_record_refs_json"],
                "source_locator": source["locator"],
                "content_hashes_json": source["content_hashes_json"],
                "upstream_record_ids_json": canonical_json(upstream_ids),
                "upstream_source_ids_json": canonical_json(source_ids),
                "upstream_locators_json": canonical_json(locators),
                "occurrence_source_class": exact_class,
                "occurrence_evidence_class": evidence_class,
                "classification_detail": detail,
                "classification_reason": reason,
                "evidence_use_disposition": use,
                "exact_group_support_status": group_status,
                "source_text_review_status": source_text,
                "rights_review_status": rights,
                "human_review_status": "OPEN_FOR_ANY_ASSOCIATION_ACTIVATION",
                "counterevidence_review_status": "OPEN_FOR_ANY_ASSOCIATION_ACTIVATION",
                "scope_split_need": spec["scope_status"],
                "product_eligibility": "INELIGIBLE_NO_ACTIVE_GOVERNED_ASSOCIATION",
                "pair_projection_created": "false",
                "association_activation_created": "false",
                "explicit_nonclaims_json": canonical_json(spec["nonclaims"]),
            })
            occurrence_rows.append(row)
            rows_by_family[family["candidate_id"]].append(row)
    occurrence_rows.sort(key=lambda row: (int(row["family_ordinal"]), row["trigger_occurrence_id"]))

    source_counts = Counter(row["occurrence_source_class"] for row in occurrence_rows)
    evidence_counts = Counter(row["occurrence_evidence_class"] for row in occurrence_rows)
    if dict(source_counts) != EXPECTED_SOURCE_CLASS_COUNTS or dict(evidence_counts) != EXPECTED_GENERIC_CLASS_COUNTS:
        raise AssertionError(f"tranche-C occurrence classifications changed: {dict(source_counts)} {dict(evidence_counts)}")
    for spec in FAMILY_SPECS:
        family = selected_families[spec["key"]]
        actual = dict(Counter(row["occurrence_source_class"] for row in rows_by_family[family["candidate_id"]]))
        if actual != EXPECTED_FAMILY_SOURCE_COUNTS[spec["key"][:8]]:
            raise AssertionError(f"family source counts changed: {spec['key']}: {actual}")

    queue_rows = build_queue_rows(selected_families, rows_by_family, pair_status_by_family)
    queue_by_parent = Counter(row["parent_candidate_id"] for row in queue_rows)
    identity_by_parent = Counter(row["parent_candidate_id"] for row in queue_rows if row["association_identity_created"] == "true")

    family_rows: list[dict[str, Any]] = []
    for spec in FAMILY_SPECS:
        family = selected_families[spec["key"]]
        linked = rows_by_family[family["candidate_id"]]
        exact_counts = Counter(row["occurrence_source_class"] for row in linked)
        generic_counts = Counter(row["occurrence_evidence_class"] for row in linked)
        review_rows = [row for row in linked if row["occurrence_evidence_class"] != "STRUCTURAL_ECHO"]
        review_ids = sorted({value for row in review_rows for value in json.loads(row["upstream_record_ids_json"])})
        review_locators = sorted({value for row in review_rows for value in json.loads(row["upstream_locators_json"])})
        active_pairs = active_pairs_by_family[family["candidate_id"]]
        negatives = hard_negatives_by_family[family["candidate_id"]]
        arity = int(family["arity"])
        is_inquiry = spec["disposition"] == "INQUIRY_ONLY_OR_UNRESOLVED"
        if spec["key"].startswith("89817e7a"):
            direct_status = "SCOPED_DIRECT_HYPEREDGE_HYPOTHESIS_PENDING_EXTERNAL_HUMAN_REVIEW"
            coherence_status = "INQUIRY_ONLY_SAME_CASE_HYPOTHESIS_NOT_FINAL"
        elif spec["key"].startswith("d936154c"):
            direct_status = "ARTICLE_METHOD_LEVEL_SPARSE_HYPEREDGE_HYPOTHESIS_PENDING_SENSE_CASE_AND_HUMAN_REVIEW"
            coherence_status = "INQUIRY_ONLY_SENSE_AND_CASE_SPLIT_AUDIT_OPEN"
        else:
            direct_status = "NO_ACTIVE_DIRECT_SUPPORT_FOR_UNSPLIT_PARENT"
            coherence_status = "FAIL_CLOSED_NOT_PASSED"
        family_rows.append(finalize_row({
            "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
            "review_tranche": TRANCHE_ID,
            "family_ordinal": spec["ordinal"],
            "candidate_id": family["candidate_id"],
            "candidate_object_kind": family["candidate_object_kind"],
            "participant_set_key": family["participant_set_key"],
            "participant_sense_ids_json": family["participant_sense_ids_json"],
            "canonical_labels_json": family["canonical_labels_json"],
            "arity": arity,
            "linked_occurrence_count": len(linked),
            "linked_occurrence_ids_sha256": sha256_text(canonical_json(sorted(row["trigger_occurrence_id"] for row in linked))),
            "occurrence_source_class_counts_json": canonical_json(dict(sorted(exact_counts.items()))),
            "occurrence_evidence_class_counts_json": canonical_json(dict(sorted(generic_counts.items()))),
            "evidence_bearing_input_count": generic_counts["EVIDENCE_BEARING_INPUT"],
            "metadata_discovery_count": 0,
            "structural_echo_count": generic_counts["STRUCTURAL_ECHO"],
            "synthetic_control_count": generic_counts["SYNTHETIC_CONTROL"],
            "hard_negative_control_count": generic_counts["HARD_NEGATIVE_CONTROL"],
            "explicit_near_miss_count": generic_counts["GLOBAL_COHERENCE_NEGATIVE_CONTROL"] + generic_counts["TEMPORAL_SCOPE_NEGATIVE_CONTROL"],
            "vocabulary_only_cooccurrence_count": 0,
            "review_input_record_ids_json": canonical_json(review_ids),
            "review_locators_json": canonical_json(review_locators),
            "internal_possible_pair_count": arity * (arity - 1) // 2,
            "internal_active_pair_count": len(active_pairs),
            "internal_active_pair_ids_json": canonical_json(sorted(edge["association_id"] for edge in active_pairs)),
            "internal_active_round14_assessment_ids_json": canonical_json(sorted(edge["round14_assessment_id"] for edge in active_pairs)),
            "internal_hard_negative_pair_count": len(negatives),
            "internal_hard_negative_assessment_ids_json": canonical_json(sorted(row["assessment_id"] for row in negatives)),
            "active_pair_graph_component_count": component_count_by_family[family["candidate_id"]],
            "active_pair_graph_connected": "true" if component_count_by_family[family["candidate_id"]] == 1 else "false",
            "final_parent_disposition": spec["disposition"],
            "parent_disposition_status": "FINAL_INQUIRY_ONLY_PARENT_NOT_ACTIVE" if is_inquiry else "FINAL_FOR_UNSPLIT_PARENT_REVIEW_FAMILY_FAIL_CLOSED",
            "disposition_rationale": spec["rationale"],
            "scope_split_or_reroute_status": spec["scope_status"],
            "queue_record_count": queue_by_parent[family["candidate_id"]],
            "conditional_scoped_child_review_count": identity_by_parent[family["candidate_id"]],
            "scoped_inquiry_identity_count": identity_by_parent[family["candidate_id"]],
            "direct_group_support_status": direct_status,
            "composite_group_support_status": "NO_ACTIVE_COMPOSITE_SUPPORT_FOR_UNSPLIT_PARENT",
            "global_coherence_status": coherence_status,
            "rights_review_status": "OPEN_EXTERNAL_RIGHTS_AND_REDISTRIBUTION_REVIEW" if is_inquiry else "NOT_REQUIRED_FOR_FINAL_NON_SUPPORTING_PARENT",
            "source_text_review_status": "OPEN_EXTERNAL_EXACT_TEXT_AND_LOCATOR_REVIEW" if is_inquiry else "NOT_REQUIRED_FOR_FINAL_NON_SUPPORTING_PARENT",
            "human_review_status": "OPEN_EXTERNAL_DESIGN_HISTORY_REVIEW" if is_inquiry else "NOT_PENDING_FOR_FINAL_NON_SUPPORTING_PARENT",
            "counterevidence_review_status": "OPEN_ADAPTIVE_FALSIFICATION_REVIEW" if is_inquiry else "NOT_PENDING_FOR_FINAL_NON_SUPPORTING_PARENT",
            "association_identity_status": "SCOPED_INQUIRY_IDENTITY_CREATED_NOT_ACTIVE_FACT" if is_inquiry else "NOT_CREATED_PARENT_IS_REVIEW_FAMILY_NOT_ASSOCIATION",
            "association_activation_status": "INQUIRY_ONLY" if is_inquiry else "INACTIVE",
            "product_eligibility": "INELIGIBLE",
            "pair_projection_count": 0,
            "explicit_nonclaims_json": canonical_json(spec["nonclaims"]),
        }))

    final_distribution = dict(Counter(row["final_parent_disposition"] for row in family_rows))
    expected_distribution = {"BOUNDED_SENSE_OR_SCOPE_CONFLICT": 3, "HARD_NEGATIVE": 2, "INQUIRY_ONLY_OR_UNRESOLVED": 2, "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE": 3}
    if final_distribution != expected_distribution or len(family_rows) != 10 or len(occurrence_rows) != 60 or len(queue_rows) != 12:
        raise AssertionError(f"tranche-C headline counts changed: {final_distribution}")
    if sum(int(row["linked_occurrence_count"]) for row in family_rows) != 60 or any(int(row["pair_projection_count"]) != 0 or row["product_eligibility"] != "INELIGIBLE" or row["association_activation_status"] == "ACTIVE" for row in family_rows):
        raise AssertionError("tranche-C conservation or fail-closed boundary changed")

    prior_distribution = Counter(row["final_parent_disposition"] for row in prior_family_rows)
    cumulative_distribution = dict(sorted((prior_distribution + Counter(final_distribution)).items()))
    expected_cumulative = {"BOUNDED_SENSE_OR_SCOPE_CONFLICT": 14, "COOCCURRENCE_ONLY": 2, "HARD_NEGATIVE": 3, "INQUIRY_ONLY_OR_UNRESOLVED": 5, "INSUFFICIENT_EVIDENCE": 2, "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE": 8, "TOPOLOGY_OR_ROLE_CONFLICT": 1}
    if cumulative_distribution != expected_cumulative or sum(cumulative_distribution.values()) != 35:
        raise AssertionError(f"cumulative parent distribution changed: {cumulative_distribution}")

    clique_controls = [row for row in prior_family_rows if int(row["internal_possible_pair_count"]) == int(row["internal_active_pair_count"]) and row["final_parent_disposition"] not in {"DIRECT_HIGHER_ORDER_SUPPORT", "COHERENT_COMPOSITE_SUPPORT", "MIXED_DIRECT_AND_COMPOSITE_SUPPORT"}]
    if len(clique_controls) != 5 or any(row["association_activation_status"] == "ACTIVE" for row in clique_controls):
        raise AssertionError("inherited pairwise-clique-invalid control changed")
    if len(hard_negatives_by_family[selected_families[FAMILY_SPECS[7]["key"]]["candidate_id"]]) != 3 or len(hard_negatives_by_family[selected_families[FAMILY_SPECS[8]["key"]]["candidate_id"]]) != 2:
        raise AssertionError("tranche-C hard-negative family controls changed")

    input_roles = {
        OCCURRENCE_PATH: "IMMUTABLE_CHECKPOINT004_OCCURRENCE_UNIVERSE",
        FAMILY_PATH: "IMMUTABLE_CHECKPOINT004_FAMILY_UNIVERSE",
        CROSSWALK_PATH: "IMMUTABLE_PARTICIPANT_SENSE_AUTHORITY",
        CENSUS_PATH: "IMMUTABLE_CHECKPOINT004_HEADLINE_AND_CLOSURE_BOUNDARY",
        METHOD_PATH: "GOVERNED_EVIDENCE_AND_ACTIVATION_METHOD",
        TAXONOMY_PATH: "EXACT_GOVERNED_DISPOSITION_TAXONOMY",
        GRAPH_PATH: "IMMUTABLE_ROUND16A_ACTIVE_PAIR_BASELINE",
        CALIBRATION_PATH: "ACTIVE_PAIR_AND_HARD_NEGATIVE_AUTHORITY",
        TRANCHE_A_OCCURRENCE_PATH: "PUBLISHED_TRANCHE_A_OCCURRENCE_AUTHORITY",
        TRANCHE_A_FAMILY_PATH: "PUBLISHED_TRANCHE_A_PARENT_DISPOSITION_AUTHORITY",
        TRANCHE_A_RECEIPT_PATH: "PUBLISHED_TRANCHE_A_BUILD_RECEIPT",
        TRANCHE_B_OCCURRENCE_PATH: "PUBLISHED_TRANCHE_B_OCCURRENCE_AUTHORITY",
        TRANCHE_B_FAMILY_PATH: "PUBLISHED_TRANCHE_B_PARENT_DISPOSITION_AUTHORITY",
        TRANCHE_B_RECEIPT_PATH: "PUBLISHED_TRANCHE_B_BUILD_RECEIPT",
        TRANCHE_B_GENERATOR_PATH: "PUBLISHED_TRANCHE_B_GENERATOR_SOURCE",
        SOURCE_REGISTRY_PATH: "COMP_SRC_020_AND_025_BIBLIOGRAPHIC_IDENTITY_AUTHORITY",
        GENERATOR_PATH: "DETERMINISTIC_TRANCHE_C_GENERATOR_SOURCE",
    }
    source_paths = sorted({row["source_path"] for row in occurrence_rows})
    all_input_paths = list(dict.fromkeys([
        OCCURRENCE_PATH, FAMILY_PATH, CROSSWALK_PATH, CENSUS_PATH, METHOD_PATH,
        TAXONOMY_PATH, GRAPH_PATH, CALIBRATION_PATH,
        TRANCHE_A_OCCURRENCE_PATH, TRANCHE_A_FAMILY_PATH, TRANCHE_A_RECEIPT_PATH,
        TRANCHE_B_OCCURRENCE_PATH, TRANCHE_B_FAMILY_PATH, TRANCHE_B_RECEIPT_PATH,
        TRANCHE_B_GENERATOR_PATH, SOURCE_REGISTRY_PATH, *source_paths, GENERATOR_PATH,
    ]))
    input_rows = []
    for ordinal, relative in enumerate(all_input_paths, 1):
        actual = sha256_file(relative)
        pinned = PINNED_INPUT_SHA256.get(relative, actual if relative == GENERATOR_PATH else "")
        if not pinned or actual != pinned:
            raise AssertionError(f"unbound or changed tranche-C input: {relative}")
        input_rows.append(finalize_row({
            "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
            "input_ordinal": ordinal,
            "path": relative,
            "input_role": input_roles.get(relative, "ROW_EXACT_UPSTREAM_SOURCE_FOR_SELECTED_OCCURRENCES"),
            "bytes": (REPO / relative).stat().st_size,
            "input_record_count": input_record_count(relative),
            "sha256": actual,
            "pinned_sha256": pinned,
            "pin_match": "true",
        }))

    gap_specs = [
        ("GAP-025", "All checkpoint-004 local parent families now have final dispositions, but local parent coverage is not candidate-universe closure", "CLOSURE_BLOCKING", "RESOLVED_LOCAL_PARENT_COVERAGE_CLOSURE_OPEN", "Tranches A-C conserve all 35 families and 359 occurrences; every parent has one final disposition and none is active from pending review.", "RECURSIVE_DISCOVERY_AND_EXCLUSION_AUTHORITY", "Continue candidate-trigger gap audit, external evidence shards, exclusion proof, and newly discovered class incorporation."),
        ("GAP-026", "Sweden 1954 may require a direct four-member hyperedge without an exhibition/trade pair", "CLOSURE_BLOCKING", "OPEN_INQUIRY_ONLY_IDENTITY", "Five of six pairs are active, exhibition/trade is absent, and two locator-bearing inputs support a scoped direct-hyperedge hypothesis without projection.", "EXTERNAL_EXACT_TEXT_RIGHTS_AND_DESIGN_HISTORY_REVIEW", "Complete lawful source, locator, rights, role, counterevidence, and independent human review before any support or activation decision."),
        ("GAP-027", "Hutton 2013 may require a sparse disconnected article-method hyperedge or smaller case-specific identities", "CLOSURE_BLOCKING", "OPEN_INQUIRY_ONLY_IDENTITY_AND_SPLIT_AUDIT", "Four of ten pairs form two components; the local record supports material-chain inquiry but current production/consumption senses and article-method versus case scope remain unresolved.", "SENSE_CASE_RIGHTS_AND_EXTERNAL_HUMAN_AUTHORITY", "Review exact text and three cases, govern any new senses, and decide method-level identity versus case-specific children."),
        ("GAP-028", "A complete active pair clique can still fail global group coherence", "CLOSURE_BLOCKING", "CONTROLLED_FIVE_INHERITED_NONACTIVE_CLIQUES", "Five tranche-A/B parents have every internal pair active yet a final non-supporting disposition; none is active.", "INDEPENDENT_GLOBAL_COHERENCE_VERIFIER", "Retain an implementation-independent clique-invalid test and prevent generator/verifier assumption sharing."),
        ("GAP-029", "Sparse or disconnected pair graphs must not suppress legitimate hyperedge inquiry", "CLOSURE_BLOCKING", "CONTROLLED_TWO_SCOPED_INQUIRY_IDENTITIES_NO_PROJECTION", "Sweden lacks one pair and Hutton has two active-pair components; both remain inquiry-only identities without invented pairs or subsets.", "HYPEREDGE_INCIDENCE_MODEL_AND_EXTERNAL_AUTHORITY", "Implement first-class incidence semantics and verify navigation/rendering without pair expansion."),
        ("GAP-030", "Hard-negative pairs must block projections without automatically precluding separately evidenced hyperedges", "CLOSURE_BLOCKING", "CONTROLLED_TWO_HARD_NEGATIVE_PARENTS", "The b2f6 and ed83 parents close hard-negative; the eight-node 3d97 parent also retains five internal hard-negative assessments under a primary scope-conflict disposition.", "NEGATIVE_EVIDENCE_AND_NO_PROJECTION_VERIFIER", "Test hard-negative, subset projection, and independently evidenced hyperedge cases separately."),
        ("GAP-031", "Prior product and topology descendants remain unreconciled", "CLOSURE_BLOCKING", "OPEN_45_SWEDEN_DERIVATIVES_PLUS_GLOBAL_ROUND16A_RECONCILIATION", "Forty-five Sweden-linked structural descendants are queued explicitly; no prior result is silently retained or removed.", "GLOBAL_COHERENCE_AND_PRODUCT_AUTHORITY", "Reconcile every Round 16A subgraph, topology, product composition, state, workflow, and export after association decisions freeze."),
        ("GAP-032", "Zero remaining checkpoint-004 parent rows can be mistaken for Function 3 closure", "CLOSURE_BLOCKING", "CONTROLLED_ALL_CLOSURE_FLAGS_FALSE", "Local parent-disposition coverage is a measurement only; two inquiry identities, external review, recursive discovery, product representation, and independent verification remain open.", "FINAL_CLOSURE_AUTHORITY", "Do not set any closure flag until all evidence, model, product, reproduction, and independent-review conditions pass."),
    ]
    gap_rows = [finalize_row({
        "gap_id": gap_id,
        "last_reviewed_checkpoint": "CHECKPOINT-007-TRANCHE-C",
        "gap": gap,
        "severity": severity,
        "status": status,
        "checkpoint007_tranche_c_evidence": evidence,
        "authority_dependency": dependency,
        "required_next_action": action,
    }) for gap_id, gap, severity, status, evidence, dependency, action in gap_specs]

    queue_kind_counts = dict(sorted(Counter(row["queue_record_kind"] for row in queue_rows).items()))
    census = {
        "format": "trace-round16b-evidence-disposition-tranche-c-census-v1",
        "builder_version": BUILDER_VERSION,
        "source_sha": AUTHORIZED_SOURCE_SHA,
        "source_tree": AUTHORIZED_SOURCE_TREE,
        "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
        "review_tranche": TRANCHE_ID,
        "checkpoint004_candidate_family_count": 35,
        "checkpoint004_trigger_occurrence_count": 359,
        "tranche_family_count": len(family_rows),
        "tranche_linked_occurrence_count": len(occurrence_rows),
        "tranche_family_arity_counts": dict(sorted(Counter(row["arity"] for row in family_rows).items())),
        "occurrence_source_class_counts": dict(sorted(source_counts.items())),
        "occurrence_evidence_class_counts": dict(sorted(evidence_counts.items())),
        "final_parent_disposition_counts": dict(sorted(final_distribution.items())),
        "active_pair_count_distribution": dict(sorted(Counter(row["internal_active_pair_count"] for row in family_rows).items())),
        "active_pair_graph_component_count_distribution": dict(sorted(Counter(row["active_pair_graph_component_count"] for row in family_rows).items())),
        "internal_hard_negative_pair_count": sum(int(row["internal_hard_negative_pair_count"]) for row in family_rows),
        "scoped_review_queue_record_count": len(queue_rows),
        "scoped_review_queue_kind_counts": queue_kind_counts,
        "scoped_inquiry_identity_count": 2,
        "association_identity_created_count": 2,
        "association_activation_count": 0,
        "active_association_count": 0,
        "pair_projection_created_count": 0,
        "subset_projection_created_count": 0,
        "product_path_created_count": 0,
        "product_eligible_count": 0,
        "active_pending_review_count": 0,
        "unresolved_inquiry_association_count": 2,
        "controls": {
            "inherited_pairwise_clique_invalid_parent_count": len(clique_controls),
            "sweden_active_pairs": 5,
            "sweden_possible_pairs": 6,
            "sweden_missing_pair": ["exhibition", "trade"],
            "hutton_active_pairs": 4,
            "hutton_possible_pairs": 10,
            "hutton_active_pair_graph_components": 2,
            "tranche_hard_negative_parent_count": 2,
            "no_pair_projection": True,
            "no_subset_projection": True,
        },
        "cumulative_tranche_a_b_c": {
            "disposed_family_count": 35,
            "disposed_occurrence_count": 359,
            "final_parent_disposition_counts": cumulative_distribution,
            "remaining_undisposed_local_family_count": 0,
            "remaining_undisposed_local_occurrence_count": 0,
            "local_parent_disposition_coverage": True,
            "candidate_universe_closure": False,
        },
        "closure": {
            "pair_association_closure": False,
            "higher_order_association_closure": False,
            "global_composition_coherence_closure": False,
            "product_association_reachability_closure": False,
            "computational_space_closure": False,
            "function3_closure": False,
        },
        "semantic_boundary": "All ten remaining checkpoint-004 parent review families have final non-supporting dispositions. Sweden 1954 and Hutton 2013 exist only as scoped INQUIRY_ONLY research identities pending external human review; neither is an active fact, product path, pair projection, subset projection, or closure result.",
    }

    note = f"""# Checkpoint 007 — Evidence disposition tranche C

## Boundary

This additive tranche binds published checkpoint 006 `{PARENT_CHECKPOINT_SHA}` and reviews the ten remaining checkpoint-004 participant-set families, all with arity four or greater. It conserves all 60 linked occurrences. Together, tranches A, B, and C now give one final disposition to every one of the 35 local families and account for all 359 trigger occurrences.

That is local parent-disposition coverage, not candidate-universe or Function 3 closure. Recursive discovery, exclusions, external evidence review, product reconciliation, model work, independent verification, and clean reproduction remain open. All six closure flags remain false.

## Exact tranche decisions

The ten-parent distribution is:

- 3 `PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE`;
- 3 `BOUNDED_SENSE_OR_SCOPE_CONFLICT`;
- 2 `HARD_NEGATIVE`;
- 2 `INQUIRY_ONLY_OR_UNRESOLVED`.

The occurrence census contains 45 prior structural descendants, ten R15 controls, four locator-bearing evidence inputs, and one synthetic n-ary control. No subgraph, topology, product composition, fixture, or pair binding is promoted to historical group evidence.

## Higher-order controls and scoped identities

The Sweden-in-Sydney 1954 family `{FAMILY_SPECS[2]['key']}` has five of six active internal pairs. The absent exhibition/trade pair is not manufactured. Its two locator-bearing local inputs support a direct four-member hyperedge hypothesis, but exact-source, rights, role, counterevidence, and external design-history review remain open. Its deterministic identity is `INQUIRY_ONLY`, product-ineligible, and projection-free. Forty-five inherited structural descendants remain queued for explicit reconciliation.

The Hutton 2013 family `{FAMILY_SPECS[4]['key']}` has four of ten active pairs in two disconnected components. That sparse graph does not suppress a source-centred article-method hyperedge inquiry, but the current production and consumption senses and the distinction between an article-level method and three material cases remain unresolved. Its deterministic identity is likewise `INQUIRY_ONLY`, product-ineligible, and projection-free. No copyrighted full text is retained.

Five already published tranche-A/B families serve as controls in which every internal pair is active yet the parent has a final non-supporting disposition. Tranche C also closes two explicit hard-negative parents and preserves hard-negative pair controls inside other parents. A hard-negative pair blocks projection but does not logically preclude a future separately evidenced, newly scoped hyperedge.

## Closure state

No association is active, no active fact depends on pending human review, no pair or subset projection is created, no product path is created, and no closure claim is made. The two scoped identities remain unresolved research inquiries until the external evidence and human-review gates are completed.
""".encode("utf-8")

    occurrence_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-occurrence-disposition-tranche-c-v1.tsv"
    family_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/family-evidence-disposition-tranche-c-v1.tsv"
    queue_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/scoped-higher-order-review-queue-tranche-c-v1.tsv"
    input_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-input-manifest-tranche-c-v1.tsv"
    gap_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/recursive-gap-ledger-checkpoint007-tranche-c-v1.tsv"
    census_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-census-tranche-c-v1.json"
    note_output = "docs/research/trace-v49-exploration-higher-order-association-closure-round16b/12_EVIDENCE_DISPOSITION_TRANCHE_C.md"
    artifacts: dict[str, bytes] = {
        occurrence_output: tsv_bytes(OCCURRENCE_FIELDS, occurrence_rows),
        family_output: tsv_bytes(FAMILY_FIELDS, family_rows),
        queue_output: tsv_bytes(QUEUE_FIELDS, queue_rows),
        input_output: tsv_bytes(INPUT_FIELDS, input_rows),
        gap_output: tsv_bytes(GAP_FIELDS, gap_rows),
        census_output: json_bytes(census),
        note_output: note,
    }
    output_hashes = {path: {"bytes": len(payload), "sha256": sha256_bytes(payload)} for path, payload in sorted(artifacts.items())}
    receipt = {
        "format": "trace-round16b-evidence-disposition-tranche-c-build-receipt-v1",
        "builder_version": BUILDER_VERSION,
        "source_sha": AUTHORIZED_SOURCE_SHA,
        "source_tree": AUTHORIZED_SOURCE_TREE,
        "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
        "review_tranche": TRANCHE_ID,
        "input_count": len(input_rows),
        "input_manifest_sha256": sha256_bytes(artifacts[input_output]),
        "family_count": len(family_rows),
        "linked_occurrence_count": len(occurrence_rows),
        "family_arity_counts": dict(sorted(Counter(row["arity"] for row in family_rows).items())),
        "occurrence_source_class_counts": dict(sorted(source_counts.items())),
        "occurrence_evidence_class_counts": dict(sorted(evidence_counts.items())),
        "final_parent_disposition_counts": dict(sorted(final_distribution.items())),
        "scoped_review_queue_record_count": len(queue_rows),
        "scoped_review_queue_kind_counts": queue_kind_counts,
        "scoped_inquiry_identity_count": 2,
        "cumulative_disposed_family_count": 35,
        "cumulative_disposed_occurrence_count": 359,
        "remaining_undisposed_local_family_count": 0,
        "remaining_undisposed_local_occurrence_count": 0,
        "local_parent_disposition_coverage": True,
        "candidate_universe_closure": False,
        "inherited_pairwise_clique_invalid_parent_count": len(clique_controls),
        "association_identity_created_count": 2,
        "association_activation_count": 0,
        "active_association_count": 0,
        "pair_projection_created_count": 0,
        "subset_projection_created_count": 0,
        "product_path_created_count": 0,
        "product_eligible_count": 0,
        "active_pending_review_count": 0,
        "unresolved_inquiry_association_count": 2,
        "closure_flags_true_count": 0,
        "output_count_excluding_receipt": len(artifacts),
        "output_hashes": output_hashes,
        "aggregate_output_sha256": sha256_text(canonical_json(output_hashes)),
        "status": "PASS_FAIL_CLOSED_TRANCHE_C_LOCAL_PARENT_COVERAGE_ONLY",
    }
    artifacts["docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-build-receipt-tranche-c-v1.json"] = json_bytes(receipt)
    return artifacts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="compare generated bytes with materialized artifacts")
    args = parser.parse_args()
    artifacts = build_artifacts()
    if args.check:
        mismatches = [relative for relative, expected in artifacts.items() if not (REPO / relative).exists() or (REPO / relative).read_bytes() != expected]
        if mismatches:
            raise SystemExit("deterministic artifact mismatch: " + ";".join(mismatches))
        print(canonical_json({"status": "PASS", "mode": "CHECK", "artifact_count": len(artifacts)}))
        return
    for relative, payload in artifacts.items():
        path = REPO / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print((RAW / "evidence-disposition-build-receipt-tranche-c-v1.json").read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
