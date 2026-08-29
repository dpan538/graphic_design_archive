#!/usr/bin/env python3
"""Build the deterministic Round 16B checkpoint-005 evidence tranche A.

This builder is deliberately additive.  It treats the checkpoint-004 v2
candidate census as immutable input, classifies every linked occurrence for a
fixed eleven-family tranche, and gives each *unsplit parent review family* a
fail-closed disposition.  Potential scoped children and semantic reroutes are
kept in a separate queue.  The builder creates no association identity, pair
projection, product activation, or closure claim.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw"
RESEARCH = REPO / "docs/research/trace-v49-exploration-higher-order-association-closure-round16b"

AUTHORIZED_SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
AUTHORIZED_SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
PARENT_CHECKPOINT_SHA = "068c92151a935cfb9e4adc36b150c6800a6de9a2"
TRANCHE_ID = "CHECKPOINT-005-EVIDENCE-TRANCHE-A"
BUILDER_VERSION = "trace-round16b-evidence-disposition-tranche-a-v1"

OCCURRENCE_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/candidate-trigger-occurrence-ledger-v2.tsv"
FAMILY_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/local-candidate-family-ledger-v2.tsv"
CROSSWALK_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/concept-sense-crosswalk-v1.tsv"
CENSUS_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/local-candidate-census-v2.json"
METHOD_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/higher-order-association-method-v1.json"
GRAPH_PATH = "docs/audits/v49-exploration-full-space-closure-round1/raw/validated-association-graph-v2.json"
GENERATOR_PATH = "scripts/trace_round16b/build_evidence_disposition_tranche_a.py"

PINNED_INPUT_SHA256 = {
    OCCURRENCE_PATH: "1685e5bfdab735657ce78499b2597e6a20aecd7402d97f515b162a5d16009cd6",
    FAMILY_PATH: "cd4c3ca997c0f4cd5919d4e29d89ca45291fae4f70f78a49742aafb9c76baea7",
    CROSSWALK_PATH: "dfc1751482f3e74de78c2a94fd46f20eb3538d26e8c6bbf94482cac9534e770a",
    CENSUS_PATH: "b40e28810aa59a0e2ac926e403cf45ba9b032b465ee54a62fd7e32b2f6e4fe31",
    METHOD_PATH: "f37ff8aa97d3c9a0d417ee0a9e6ef96971b0c0985bf88bf7bb59af8da8d106e7",
    GRAPH_PATH: "1dee15d7cc0a9aa25f2a4a0fd7a352d2df5e7eacf88bd71badec5ebd476063bd",
    "docs/audits/v49-exploration-association-calibration-round1/raw/evidence-provenance.tsv": "3bfc526c160909838da90db700a72c987e1b9ea80fb605358a400951c64c2d8c",
    "docs/audits/v49-exploration-full-space-closure-round1/raw/canonical-composition-registry-v2.json": "51c3e29909a8aa5226a7d18ebaef896aa52c48be6725d722c869515874c6c24d",
    "docs/research/trace-v49-design-history-relation-grammar-round1/07_GRAMMAR_ATTESTATION_REGISTRY.tsv": "62b56052829d23cd2cf820a232479f74cbf663d64465cdc242900e71220df2a8",
    "docs/research/trace-v49-design-history-relation-grammar-round1/14_CLUSTER_EVIDENCE_HANDOFF.tsv": "0fca1a4995577ddb3e33e1a12bebb18ccd14e74684755c26749029722dfb2ccd",
    "docs/research/trace-v49-design-history-relation-vocabulary-round1/05_TERM_ATTESTATION_REGISTRY.tsv": "f2f8ff68c9263ee360aa84f73bc3adb55e5b18b41f86f03faa18522645193240",
    "docs/research/trace-v49-exploration-composition-review-round1/04_COMPOSITION_EVIDENCE_REGISTRY.tsv": "c3d24a2a6f90d1e0b6ce7f0f483d04a752761cb3699294039c97778ed84dd714",
    "frontend/generated/trace-exploration-v2/production-read-model.json": "53eaf59c95446eeb3781a7153183c54b3ff59fd52f21744cc917053959dfdcc9",
    "scripts/trace-v49-exploration-association-calibration/fixtures/nary-local-coherence-v1.json": "32c8fa359e6bd14d3d2e4d62c4a276a1bcfa6daee1c29e9b18bffb427f6e0e56",
    "scripts/trace-v49-exploration-composition-engine/fixtures/composition-fixtures-v1.json": "0322c715166f4ed8cb4603a5a1f10db69512ef3f41386cec6450c6d52813badb",
    "scripts/trace-v49-exploration-real-database/real-composition-registry-v1.json": "cad6669c93a52924a17d31d07a16b1e1e5b0ffa06917f3cd467a5f2db003393f",
}


FAMILY_SPECS = [
    {
        "ordinal": 1,
        "key": "b63bdc2ca9694ca8e682cf6d1b38b65c8154eed366c405ab76391683e0b3c35b",
        "disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "rationale": "Consumer culture is a qualification around the bounded gendering/commodification case, not a third coequal participant supported by the passage.",
        "scope_status": "PARENT_SCOPE_CONFLICT_NO_HIGHER_ORDER_CHILD",
        "nonclaims": ["consumer culture is not activated as a third participant", "the underlying gendering/commodification pair is not generalized beyond its governed scope"],
    },
    {
        "ordinal": 2,
        "key": "7e0a0ee4f78d2f565c4f7771653ecc5a27828dd9fb704139d1e068f2a5fdce64",
        "disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "rationale": "The unsplit parent combines distinct 2009 PCM, 2026 digital-PCM, and 2021 Polish design-historiography configurations; pair connectivity and repeated product renderings do not make one global case.",
        "scope_status": "PARENT_MUST_SPLIT_THREE_CONDITIONAL_SCOPED_CHILDREN",
        "nonclaims": ["the three active internal pairs do not establish group coherence", "structural descendants are not evidence", "no scoped child is active"],
    },
    {
        "ordinal": 3,
        "key": "b19df183e2e9eb0dd6b0a3bccc95944aebf625d45faf01908eaddae994c97e67",
        "disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "rationale": "Mediating devices denotes materially different designed-good and digital-object cases; the unsplit participant set does not preserve their time, actors, mechanism, or device sense.",
        "scope_status": "PARENT_MUST_SPLIT_TWO_CONDITIONAL_DIRECT_CHILDREN",
        "nonclaims": ["mediating devices is not a universal node", "the consumption/production pair does not supply the missing group claim"],
    },
    {
        "ordinal": 4,
        "key": "3cd10180090e141ef9c63f03a217b2bae056c52da1a52850736c3b580dd533b7",
        "disposition": "INQUIRY_ONLY_OR_UNRESOLVED",
        "rationale": "One locator-bearing PCM channel record triggers a plausible scoped child, but source-text, rights, bounded-role, human, and counterevidence gates remain open.",
        "scope_status": "ONE_CONDITIONAL_PCM_CHANNEL_CHILD_PENDING_REVIEW",
        "nonclaims": ["mediating channels is not any conduit", "directionality and role order are not activated"],
    },
    {
        "ordinal": 5,
        "key": "1d76bf657bbdec293265d051268a2a1153be0108b15a8d63ebbf2cb98cf6f06a",
        "disposition": "INQUIRY_ONLY_OR_UNRESOLVED",
        "rationale": "A same-locator material-chain bundle warrants a named-chain review, but the unsplit parent lacks a frozen case identity and its many product structures add no historical support.",
        "scope_status": "ONE_CONDITIONAL_NAMED_MATERIAL_CHAIN_CHILD_PENDING_REVIEW",
        "nonclaims": ["the active internal pair clique does not establish group coherence", "product structures and the synthetic control are not evidence"],
    },
    {
        "ordinal": 6,
        "key": "de6643ced4014989a08d0517a4c72ea1ccb91d6f95be3303c35997dd8c3df9c1",
        "disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "rationale": "Brazilian exposition is a rejected case label that belongs in the scope of the bounded gendering/commodification pair, not as a third vocabulary participant.",
        "scope_status": "REROUTE_CASE_LABEL_TO_EXISTING_PAIR_SCOPE",
        "nonclaims": ["Brazilian exposition is not reactivated", "one exposition case does not authorize a general three-term association"],
    },
    {
        "ordinal": 7,
        "key": "33a113b724e4e0088fd1c0fa77ea8757112a289ca51e8a441f9111b96697646a",
        "disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "rationale": "The shared source and locator contain a title-level design-exchanges container and a repeated context for appropriation/creative appropriation; they do not support three coequal concepts.",
        "scope_status": "REROUTE_TO_BINARY_MODIFIER_AND_ROLE_REVIEW",
        "nonclaims": ["creative appropriation is not independent from appropriation merely because both labels occur", "source identity and locator identity do not prove group support"],
    },
    {
        "ordinal": 8,
        "key": "c0a6431919578166078d9823cb9994e5819ab7d56a9bad39a0dcb45d056d892c",
        "disposition": "INSUFFICIENT_EVIDENCE",
        "rationale": "The family is emitted only by two prior structures and one synthetic validation fixture; none is historical evidence for the exact group.",
        "scope_status": "NO_HIGHER_ORDER_CHILD_RETAIN_UNDERLYING_PAIR_ONLY",
        "nonclaims": ["a synthetic fixture is not evidence", "renderability is not group validity", "the imitation/piracy pair does not activate cultural transformation"],
    },
    {
        "ordinal": 9,
        "key": "eaa73d3eac5e2a533cb50baf9955efb5a9c848bddbecdd05b6b59d30a1aa508b",
        "disposition": "INQUIRY_ONLY_OR_UNRESOLVED",
        "rationale": "The Tejo Remy passage is a locator-bearing direct review input, but cultural mobility and mobile-object roles require bounded-sense, scope, rights, human, and falsification review.",
        "scope_status": "ONE_CONDITIONAL_TEJO_REMY_CHILD_PENDING_REVIEW",
        "nonclaims": ["mobile object is not a universal relation", "object itinerary does not imply transitivity", "no pair projection is created"],
    },
    {
        "ordinal": 10,
        "key": "80a8ae28dc2c532a9ee8fb3293fbfa310d5e9b9042b7d8d3d1dc9612eb7fb941",
        "disposition": "TOPOLOGY_OR_ROLE_CONFLICT",
        "rationale": "The upstream record explicitly rejects flattening: imitation must not collapse into piracy and commodification is not a universal intermediate node.",
        "scope_status": "NO_HIGHER_ORDER_CHILD_RETAIN_SCOPED_PAIR_ONLY",
        "nonclaims": ["commodification is not an intermediary hub", "imitation and piracy are not synonyms or equivalent", "no three-node path is inferred"],
    },
    {
        "ordinal": 11,
        "key": "00244f87a89799f75a57307b7eecd35f40bd1f74c99f8e31f4c23fa56855c27a",
        "disposition": "COOCCURRENCE_ONLY",
        "rationale": "Four pair-evidence rows reuse one exhibition container.  The archive supports photography/typography in the exhibition description, but exhibition is contextual containment, not an independently supported third participant.",
        "scope_status": "NO_HIGHER_ORDER_CHILD_RETAIN_PHOTOGRAPHY_TYPOGRAPHY_PAIR",
        "nonclaims": ["an exhibition container is not a hyperedge", "one source reused by four pair rows is not four group sources", "group support is not inherited from the photography/typography pair"],
    },
]


EVIDENCE_BEARING_PREFIXES = {
    "044561834c2e", "61ad00846aeb", "9f22a09e6934", "66fbdbd1bccb",
    "b2cedc8d85b6", "155b9e43f260", "2d582e66de47", "57947a0bbabc",
    "fe71e5e89a9d", "987db5e0e8ec", "b00ad15cf61c", "d9e45fcc8872",
    "a1a38cdef01d",
}
SYNTHETIC_PREFIXES = {"dfbcb6f7543e", "d2cd204af8ff", "5136878da5cd"}
NEGATIVE_PREFIXES = {"1f09c20a0ea6"}
SOURCE_CONTAINER_PREFIXES = {"3a64a716813a", "7b9cb1b860b5", "7c8cb35ba685", "c8c9e3e959ca"}

CLASS_DETAIL = {
    "EVIDENCE_BEARING": "EVIDENCE_BEARING_INPUT_NOT_YET_GOVERNED_SUPPORT",
    "STRUCTURAL_ECHO": "STRUCTURAL_ECHO_NOT_EVIDENCE",
    "SYNTHETIC_CONTROL": "SYNTHETIC_CONTROL_NOT_EVIDENCE",
    "NEGATIVE_CONTEXT": "NEGATIVE_CONTEXT_OR_UNSUPPORTED_SYNTHESIS",
    "SOURCE_CONTAINER_COOCCURRENCE": "SOURCE_CONTAINER_COOCCURRENCE",
}

OCCURRENCE_FIELDS = [
    "parent_checkpoint_sha", "review_tranche", "family_ordinal", "candidate_id",
    "participant_set_key", "trigger_occurrence_id", "source_occurrence_sha256",
    "trigger_id", "trigger_class", "emission_kind", "source_path",
    "input_surface_id", "input_record_refs_json", "source_locator",
    "content_hashes_json", "upstream_record_ids_json", "upstream_source_ids_json",
    "upstream_locators_json", "occurrence_evidence_class", "classification_detail",
    "classification_reason", "evidence_use_disposition", "exact_group_support_status",
    "source_text_review_status", "rights_review_status", "human_review_status",
    "counterevidence_review_status", "scope_split_need", "product_eligibility",
    "pair_projection_created", "association_activation_created", "explicit_nonclaims_json",
    "record_sha256",
]

FAMILY_FIELDS = [
    "parent_checkpoint_sha", "review_tranche", "family_ordinal", "candidate_id",
    "candidate_object_kind", "participant_set_key", "participant_sense_ids_json",
    "canonical_labels_json", "arity", "linked_occurrence_count",
    "linked_occurrence_ids_sha256", "occurrence_class_counts_json",
    "evidence_bearing_input_count", "structural_echo_count", "synthetic_control_count",
    "negative_context_count", "source_container_cooccurrence_count",
    "review_input_record_ids_json", "review_locators_json", "internal_possible_pair_count",
    "internal_active_pair_count", "internal_active_pair_ids_json", "final_parent_disposition",
    "parent_disposition_status", "disposition_rationale", "scope_split_or_reroute_status",
    "conditional_queue_count", "direct_group_support_status", "composite_group_support_status",
    "global_coherence_status", "rights_review_status", "source_text_review_status",
    "human_review_status", "counterevidence_review_status", "association_identity_status",
    "association_activation_status", "product_eligibility", "pair_projection_count",
    "explicit_nonclaims_json", "record_sha256",
]

QUEUE_FIELDS = [
    "parent_checkpoint_sha", "review_tranche", "queue_id", "parent_candidate_id",
    "parent_family_ordinal", "queue_action", "scope_key", "scope_label",
    "proposed_participant_sense_ids_json", "proposed_relation_form",
    "candidate_support_mode_if_reviewed", "evidence_occurrence_ids_json",
    "active_pair_refs_json", "case_time_geography_institution_actor_mechanism_note",
    "required_scope_or_sense_resolution", "rights_review_status",
    "source_text_review_status", "human_review_status", "counterevidence_review_status",
    "queue_status", "association_identity_created", "association_active",
    "pair_projection_created", "product_eligibility", "explicit_nonclaims_json",
    "record_sha256",
]

INPUT_FIELDS = [
    "parent_checkpoint_sha", "input_ordinal", "path", "input_role", "bytes",
    "input_record_count", "sha256", "pinned_sha256", "pin_match", "record_sha256",
]

GAP_FIELDS = [
    "gap_id", "last_reviewed_checkpoint", "gap", "severity", "status",
    "checkpoint005_tranche_a_evidence", "authority_dependency", "required_next_action",
    "record_sha256",
]


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(relative: str) -> str:
    return sha256_bytes((REPO / relative).read_bytes())


def row_hash(row: dict[str, Any]) -> str:
    return sha256_text(canonical_json(row))


def finalize_row(row: dict[str, Any]) -> dict[str, Any]:
    # Hash the exact scalar representation written to TSV.  This avoids a
    # verifier having to guess which numeric-looking columns were integers in
    # memory before serialization.
    result = {key: "" if value is None else str(value) for key, value in row.items()}
    result["record_sha256"] = row_hash(result)
    return result


def read_tsv(relative: str) -> list[dict[str, str]]:
    with (REPO / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, dialect="excel-tab"))


def read_json(relative: str) -> Any:
    return json.loads((REPO / relative).read_text(encoding="utf-8"))


def tsv_bytes(fields: list[str], rows: Iterable[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, dialect="excel-tab", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return buffer.getvalue().encode("utf-8")


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def occurrence_digest(occurrence_id: str) -> str:
    return occurrence_id.split(":", 1)[1]


def prefix_match(occurrence_id: str, prefixes: set[str]) -> bool:
    digest = occurrence_digest(occurrence_id)
    return any(digest.startswith(prefix) for prefix in prefixes)


def occurrence_class(occurrence_id: str) -> str:
    if prefix_match(occurrence_id, EVIDENCE_BEARING_PREFIXES):
        return "EVIDENCE_BEARING"
    if prefix_match(occurrence_id, SYNTHETIC_PREFIXES):
        return "SYNTHETIC_CONTROL"
    if prefix_match(occurrence_id, NEGATIVE_PREFIXES):
        return "NEGATIVE_CONTEXT"
    if prefix_match(occurrence_id, SOURCE_CONTAINER_PREFIXES):
        return "SOURCE_CONTAINER_COOCCURRENCE"
    return "STRUCTURAL_ECHO"


def split_values(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(";") if item.strip()]


def source_row_details(occurrence: dict[str, str]) -> tuple[list[str], list[str], list[str]]:
    """Resolve exact upstream refs in tabular sources without interpreting prose."""
    refs = json.loads(occurrence["input_record_refs_json"])
    paths = [occurrence["source_path"]]
    for ref in refs:
        if "#" in ref and "/" in ref:
            path = ref.split("#", 1)[0]
            if path not in paths:
                paths.append(path)
    leaf_refs = {ref.rsplit("#", 1)[-1] for ref in refs}
    upstream_ids = set(leaf_refs)
    source_ids: set[str] = set()
    locators: set[str] = {occurrence["locator"]} if occurrence["locator"] else set()
    for relative in paths:
        path = REPO / relative
        if path.suffix != ".tsv":
            continue
        for row in read_tsv(relative):
            values = set(row.values())
            if not leaf_refs.intersection(values):
                continue
            for field, value in row.items():
                if not value:
                    continue
                if field == "source_id":
                    source_ids.add(value)
                elif field == "source_ids":
                    source_ids.update(split_values(value))
                elif field in {"locator", "page_section_locator", "page_or_section_locator", "discovery_locator"}:
                    locators.add(value)
                elif field.endswith("_id") and field in {
                    "evidence_id", "grammar_attestation_id", "attestation_id",
                    "fixture_id", "cluster_handoff_id", "composition_id",
                }:
                    upstream_ids.add(value)
    return sorted(upstream_ids), sorted(source_ids), sorted(locators)


def input_record_count(relative: str) -> int:
    path = REPO / relative
    if path.suffix == ".tsv":
        return len(read_tsv(relative))
    if path.suffix == ".jsonl":
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    if path.suffix in {".json", ".py"}:
        return 1
    return 1


def make_queue_specs(families_by_key: dict[str, dict[str, str]], active_pairs_by_family: dict[str, list[str]]) -> list[dict[str, Any]]:
    def family(key: str) -> dict[str, str]:
        return families_by_key[key]

    specs = [
        (2, "PCM_2009", "2009 Production–Consumption–Mediation paradigm", "SCOPED_CHILD_ASSOCIATION_REVIEW", "INCIDENCE_HYPEREDGE", "COHERENT_COMPOSITE_SUPPORT_CANDIDATE_NOT_DECIDED", ["66fbdbd1bccb"], "One 2009 PCM methodological case; designed channels/devices, meaning inscription, producer/institution and consumer/user roles.", "Freeze one PCM case identity and distinguish mediation process from channel/device roles."),
        (2, "DIGITAL_PCM_2026", "2026 digital Production–Consumption–Mediation configuration", "SCOPED_CHILD_ASSOCIATION_REVIEW", "INCIDENCE_HYPEREDGE", "MIXED_DIRECT_AND_COMPOSITE_SUPPORT_CANDIDATE_NOT_DECIDED", ["61ad00846aeb", "b2cedc8d85b6", "155b9e43f260"], "One 2026 digital design-history case; platforms, algorithms, digital objects, users, data and third parties.", "Freeze the digital case and separate mediation as practice from device/platform mechanisms."),
        (2, "POLISH_DESIGN_FIELD_2021", "2021 Polish design-historiography field configuration", "SCOPED_CHILD_ASSOCIATION_REVIEW", "INCIDENCE_HYPEREDGE", "DIRECT_HIGHER_ORDER_SUPPORT_CANDIDATE_NOT_DECIDED", ["9f22a09e6934"], "One 2021 Polish design-historiography abstract; institutions and mediators between production and consumption.", "Review the source text/translation and bind the Polish field, institutions and mediator roles."),
        (3, "PCM_DESIGNED_DEVICE_2009", "2009 PCM designed-good mediating-device case", "SCOPED_CHILD_ASSOCIATION_REVIEW", "INCIDENCE_HYPEREDGE", "DIRECT_HIGHER_ORDER_SUPPORT_CANDIDATE_NOT_DECIDED", ["2d582e66de47"], "One 2009 designed-good case between production and consumption.", "Freeze the designed-good/device sense and the specific producer/institution and user/consumer roles."),
        (3, "DIGITAL_DEVICE_2026", "2026 digital-object mediating-device case", "SCOPED_CHILD_ASSOCIATION_REVIEW", "INCIDENCE_HYPEREDGE", "DIRECT_HIGHER_ORDER_SUPPORT_CANDIDATE_NOT_DECIDED", ["57947a0bbabc"], "One 2026 digital-object case with platform rules, algorithms, data flows, users and third parties.", "Freeze the digital-device sense, actor set and data/platform mechanism."),
        (4, "PCM_MEDIATING_CHANNEL_2009", "2009 PCM mediating-channel case", "SCOPED_CHILD_ASSOCIATION_REVIEW", "INCIDENCE_HYPEREDGE", "DIRECT_HIGHER_ORDER_SUPPORT_CANDIDATE_NOT_DECIDED", ["fe71e5e89a9d"], "One 2009 PCM designed-channel case linking production and consumption with meaning inscription.", "Freeze the named channel and mediated variable; reject any-conduit generalization."),
        (5, "RECIPROCAL_LANDSCAPES_MATERIAL_CHAIN_2013", "2013 named landscape-material-chain case", "SCOPED_CHILD_ASSOCIATION_REVIEW", "INCIDENCE_HYPEREDGE", "COHERENT_COMPOSITE_SUPPORT_CANDIDATE_NOT_DECIDED", ["987db5e0e8ec"], "One 2013 source/locator concerning production and consumption sites, material displacement, supply chains, ecology and labor.", "Freeze the named material chain, exact sites, geography, materials and labor/ecology mechanism."),
        (6, "PARIS_1867_BRAZILIAN_EXPOSITION", "Paris 1867 Brazilian imperial exposition case", "REROUTE_REJECTED_CASE_LABEL_TO_PAIR_SCOPE", "PAIR_SCOPE_QUALIFICATION_NOT_HIGHER_ORDER_CHILD", "BOUNDED_PAIR_CASE_QUALIFICATION_CANDIDATE", ["b00ad15cf61c"], "One Paris 1867 exposition case; tropical nature/raw materials are common targets of gendering and commodification.", "Represent Brazilian exposition as case scope, not as a vocabulary participant or third node."),
        (7, "BUENOS_AIRES_MID_CENTURY", "Mid-twentieth-century Buenos Aires design-exchanges case", "REROUTE_MODIFIED_TERM_TO_BINARY_ROLE_SCOPE", "BINARY_ROLE_OR_LEXICAL_SENSE_REVIEW_NOT_HIGHER_ORDER_CHILD", "BOUNDED_BINARY_ROLE_REVIEW_CANDIDATE", ["d9e45fcc8872"], "One Buenos Aires source/locator with a title-level design-exchanges container and a repeated creative-appropriation phrase.", "Resolve whether creative appropriation is a modified bounded sense/role of appropriation; do not make the container a participant."),
        (9, "TEJO_REMY_CHEST_OF_DRAWERS_2016", "2016 Tejo Remy chest-of-drawers mobility case", "SCOPED_CHILD_ASSOCIATION_REVIEW", "INCIDENCE_HYPEREDGE", "DIRECT_HIGHER_ORDER_SUPPORT_CANDIDATE_NOT_DECIDED", ["a1a38cdef01d"], "One 2016 object-biography case; Tejo Remy's chest is constituted through mediation and changing cultural settings.", "Freeze the cultural-mobility sense, object role, itinerary and reception-change scope."),
    ]

    result: list[dict[str, Any]] = []
    occurrence_rows = read_tsv(OCCURRENCE_PATH)
    all_occurrence_ids = [row["trigger_occurrence_id"] for row in occurrence_rows]
    for ordinal, scope_key, scope_label, action, form, support_mode, prefixes, context, resolution in specs:
        family_spec = FAMILY_SPECS[ordinal - 1]
        parent = family(family_spec["key"])
        evidence_ids = sorted(
            occurrence_id for occurrence_id in all_occurrence_ids
            if any(occurrence_digest(occurrence_id).startswith(prefix) for prefix in prefixes)
        )
        if len(evidence_ids) != len(prefixes):
            raise AssertionError(f"conditional queue occurrence resolution failed: {scope_key}: {evidence_ids}")
        identity = {
            "parent_candidate_id": parent["candidate_id"],
            "queue_action": action,
            "scope_key": scope_key,
            "evidence_occurrence_ids": evidence_ids,
        }
        result.append(finalize_row({
            "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
            "review_tranche": TRANCHE_ID,
            "queue_id": f"R16B-CONDITIONAL-REVIEW:{row_hash(identity)}",
            "parent_candidate_id": parent["candidate_id"],
            "parent_family_ordinal": ordinal,
            "queue_action": action,
            "scope_key": scope_key,
            "scope_label": scope_label,
            "proposed_participant_sense_ids_json": parent["participant_sense_ids_json"],
            "proposed_relation_form": form,
            "candidate_support_mode_if_reviewed": support_mode,
            "evidence_occurrence_ids_json": canonical_json(evidence_ids),
            "active_pair_refs_json": canonical_json(active_pairs_by_family[parent["candidate_id"]]),
            "case_time_geography_institution_actor_mechanism_note": context,
            "required_scope_or_sense_resolution": resolution,
            "rights_review_status": "OPEN",
            "source_text_review_status": "OPEN_REVIEW_LOCATOR_BEARING_INPUT_AGAINST_LAWFULLY_ACCESSED_TEXT",
            "human_review_status": "OPEN_EXTERNAL_DESIGN_HISTORY_REVIEW",
            "counterevidence_review_status": "OPEN_FALSIFICATION_AND_CONFLICT_SEARCH",
            "queue_status": "CONDITIONAL_REVIEW_ONLY_NOT_ASSOCIATION",
            "association_identity_created": "false",
            "association_active": "false",
            "pair_projection_created": "false",
            "product_eligibility": "INELIGIBLE_PENDING_ALL_GOVERNED_GATES",
            "explicit_nonclaims_json": canonical_json([
                "queue membership is not a governed association disposition",
                "candidate support mode is a review hypothesis, not support",
                "no pair relation, direction, role, cause, chronology, hierarchy, influence, similarity, or transitivity is inferred",
            ]),
        }))
    return result


def build_artifacts() -> dict[str, bytes]:
    for relative, expected in PINNED_INPUT_SHA256.items():
        actual = sha256_file(relative)
        if actual != expected:
            raise AssertionError(f"pinned checkpoint-004 input changed: {relative}: {actual} != {expected}")

    parent_census = read_json(CENSUS_PATH)
    if parent_census["local_candidate_family_count"] != 35 or parent_census["trigger_occurrence_count"] != 359:
        raise AssertionError("checkpoint-004 census totals changed")
    if any(parent_census["closure"].values()):
        raise AssertionError("checkpoint-004 unexpectedly claims closure")

    occurrences = read_tsv(OCCURRENCE_PATH)
    families = read_tsv(FAMILY_PATH)
    occurrence_by_id = {row["trigger_occurrence_id"]: row for row in occurrences}
    family_by_key = {row["participant_set_key"]: row for row in families}
    if len(occurrence_by_id) != 359 or len(family_by_key) != 35:
        raise AssertionError("checkpoint-004 occurrence/family uniqueness changed")

    graph = read_json(GRAPH_PATH)
    active_pair_by_labels = {
        tuple(sorted((edge["label_a"], edge["label_b"]))): edge["association_id"]
        for edge in graph["edges"]
    }

    selected_occurrence_ids: list[str] = []
    active_pairs_by_family: dict[str, list[str]] = {}
    selected_families_by_key: dict[str, dict[str, str]] = {}
    for spec in FAMILY_SPECS:
        family = family_by_key.get(spec["key"])
        if family is None:
            raise AssertionError(f"missing tranche family {spec['key']}")
        selected_families_by_key[spec["key"]] = family
        family_occurrence_ids = json.loads(family["trigger_occurrence_ids_json"])
        if len(family_occurrence_ids) != int(family["occurrence_count"]):
            raise AssertionError(f"family occurrence count mismatch {family['candidate_id']}")
        selected_occurrence_ids.extend(family_occurrence_ids)
        labels = json.loads(family["canonical_labels_json"])
        active_pairs_by_family[family["candidate_id"]] = sorted(
            active_pair_by_labels[pair]
            for pair in (tuple(sorted(pair)) for pair in itertools.combinations(labels, 2))
            if pair in active_pair_by_labels
        )

    if len(selected_occurrence_ids) != 112 or len(set(selected_occurrence_ids)) != 112:
        raise AssertionError("tranche A must bind exactly 112 unique occurrences")

    occurrence_rows: list[dict[str, Any]] = []
    rows_by_family: dict[str, list[dict[str, Any]]] = {}
    for spec in FAMILY_SPECS:
        family = selected_families_by_key[spec["key"]]
        rows_by_family[family["candidate_id"]] = []
        for occurrence_id in json.loads(family["trigger_occurrence_ids_json"]):
            source = occurrence_by_id[occurrence_id]
            evidence_class = occurrence_class(occurrence_id)
            upstream_ids, source_ids, locators = source_row_details(source)
            if evidence_class == "EVIDENCE_BEARING":
                reason = "Locator-bearing or bounded upstream source record; retained only as an input to scoped governed review."
                use = "SCOPED_REVIEW_INPUT_NOT_SUPPORT"
                source_text = "BOUNDED_UPSTREAM_RECORD_PRESENT_FULL_SOURCE_TEXT_REVIEW_OPEN"
            elif evidence_class == "STRUCTURAL_ECHO":
                reason = "Prior composition, topology, subgraph, fixture-derived product record, or production read-model descendant; structure is not historical evidence."
                use = "NOT_EVIDENCE_RECONCILIATION_ONLY"
                source_text = "NOT_APPLICABLE_STRUCTURAL_RECORD"
            elif evidence_class == "SYNTHETIC_CONTROL":
                reason = "Explicit synthetic n-ary validation control; useful for verifier behavior only."
                use = "NOT_EVIDENCE_TEST_CONTROL_ONLY"
                source_text = "NOT_APPLICABLE_SYNTHETIC_CONTROL"
            elif evidence_class == "NEGATIVE_CONTEXT":
                reason = "Upstream handoff explicitly records flattening/intermediary-role risk and cannot support the proposed topology."
                use = "NEGATIVE_OR_CONFLICT_INPUT_NOT_SUPPORT"
                source_text = "BOUNDED_UPSTREAM_NEGATIVE_CONTEXT_REVIEWED"
            else:
                reason = "Multiple pair evidence rows reuse one institutional exhibition source container; container membership does not support the exact group."
                use = "NOT_EVIDENCE_SOURCE_CONTAINER_ONLY"
                source_text = "SOURCE_CONTAINER_RECORD_PRESENT_GROUP_TEXT_SUPPORT_ABSENT"
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
                "occurrence_evidence_class": evidence_class,
                "classification_detail": CLASS_DETAIL[evidence_class],
                "classification_reason": reason,
                "evidence_use_disposition": use,
                "exact_group_support_status": "NOT_GOVERNED_SUPPORT",
                "source_text_review_status": source_text,
                "rights_review_status": "OPEN_FOR_ANY_SUPPORT_USE" if evidence_class == "EVIDENCE_BEARING" else "NOT_APPLICABLE_TO_NON_SUPPORT_CLASSIFICATION",
                "human_review_status": "OPEN_FOR_ANY_ASSOCIATION_ACTIVATION",
                "counterevidence_review_status": "OPEN_FOR_ANY_ASSOCIATION_ACTIVATION",
                "scope_split_need": spec["scope_status"],
                "product_eligibility": "INELIGIBLE_NOT_GOVERNED_ASSOCIATION_SUPPORT",
                "pair_projection_created": "false",
                "association_activation_created": "false",
                "explicit_nonclaims_json": canonical_json(spec["nonclaims"]),
            })
            occurrence_rows.append(row)
            rows_by_family[family["candidate_id"]].append(row)

    occurrence_rows.sort(key=lambda row: (int(row["family_ordinal"]), row["trigger_occurrence_id"]))
    class_counts = Counter(row["occurrence_evidence_class"] for row in occurrence_rows)
    expected_class_counts = {
        "EVIDENCE_BEARING": 13,
        "STRUCTURAL_ECHO": 91,
        "SYNTHETIC_CONTROL": 3,
        "NEGATIVE_CONTEXT": 1,
        "SOURCE_CONTAINER_COOCCURRENCE": 4,
    }
    if dict(class_counts) != expected_class_counts:
        raise AssertionError(f"tranche class counts changed: {dict(class_counts)}")

    queue_rows = make_queue_specs(selected_families_by_key, active_pairs_by_family)
    queue_count_by_parent = Counter(row["parent_candidate_id"] for row in queue_rows)

    family_rows: list[dict[str, Any]] = []
    for spec in FAMILY_SPECS:
        family = selected_families_by_key[spec["key"]]
        linked = rows_by_family[family["candidate_id"]]
        counts = Counter(row["occurrence_evidence_class"] for row in linked)
        review_input_ids = sorted({
            value
            for row in linked
            if row["occurrence_evidence_class"] in {"EVIDENCE_BEARING", "NEGATIVE_CONTEXT", "SOURCE_CONTAINER_COOCCURRENCE"}
            for value in json.loads(row["upstream_record_ids_json"])
        })
        review_locators = sorted({
            value
            for row in linked
            if row["occurrence_evidence_class"] in {"EVIDENCE_BEARING", "NEGATIVE_CONTEXT", "SOURCE_CONTAINER_COOCCURRENCE"}
            for value in json.loads(row["upstream_locators_json"])
        })
        active_pairs = active_pairs_by_family[family["candidate_id"]]
        arity = int(family["arity"])
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
            "occurrence_class_counts_json": canonical_json(dict(sorted(counts.items()))),
            "evidence_bearing_input_count": counts["EVIDENCE_BEARING"],
            "structural_echo_count": counts["STRUCTURAL_ECHO"],
            "synthetic_control_count": counts["SYNTHETIC_CONTROL"],
            "negative_context_count": counts["NEGATIVE_CONTEXT"],
            "source_container_cooccurrence_count": counts["SOURCE_CONTAINER_COOCCURRENCE"],
            "review_input_record_ids_json": canonical_json(review_input_ids),
            "review_locators_json": canonical_json(review_locators),
            "internal_possible_pair_count": arity * (arity - 1) // 2,
            "internal_active_pair_count": len(active_pairs),
            "internal_active_pair_ids_json": canonical_json(active_pairs),
            "final_parent_disposition": spec["disposition"],
            "parent_disposition_status": "FINAL_FOR_UNSPLIT_PARENT_REVIEW_FAMILY_FAIL_CLOSED",
            "disposition_rationale": spec["rationale"],
            "scope_split_or_reroute_status": spec["scope_status"],
            "conditional_queue_count": queue_count_by_parent[family["candidate_id"]],
            "direct_group_support_status": "NO_ACTIVE_DIRECT_SUPPORT_FOR_UNSPLIT_PARENT",
            "composite_group_support_status": "NO_ACTIVE_COMPOSITE_SUPPORT_FOR_UNSPLIT_PARENT",
            "global_coherence_status": "FAIL_CLOSED_NOT_PASSED",
            "rights_review_status": "OPEN_FOR_CONDITIONAL_CHILD_OR_REROUTE_REVIEW" if queue_count_by_parent[family["candidate_id"]] else "NO_SUPPORT_USE",
            "source_text_review_status": "OPEN_FOR_CONDITIONAL_CHILD_OR_REROUTE_REVIEW" if queue_count_by_parent[family["candidate_id"]] else "NO_GROUP_SUPPORT_TEXT",
            "human_review_status": "OPEN_FOR_ANY_ASSOCIATION_ACTIVATION",
            "counterevidence_review_status": "OPEN_FOR_ANY_ASSOCIATION_ACTIVATION",
            "association_identity_status": "NOT_CREATED_PARENT_IS_REVIEW_FAMILY_NOT_ASSOCIATION",
            "association_activation_status": "INACTIVE",
            "product_eligibility": "INELIGIBLE_UNSPLIT_PARENT_NOT_GOVERNED_ASSOCIATION",
            "pair_projection_count": 0,
            "explicit_nonclaims_json": canonical_json(spec["nonclaims"]),
        }))

    if len(queue_rows) != 10 or len(family_rows) != 11:
        raise AssertionError("tranche A family/queue counts changed")
    if sum(int(row["linked_occurrence_count"]) for row in family_rows) != 112:
        raise AssertionError("family-to-occurrence conservation failed")
    if sum(int(row["conditional_queue_count"]) for row in family_rows) != 10:
        raise AssertionError("family-to-queue conservation failed")
    if any(row["association_activation_status"] != "INACTIVE" or int(row["pair_projection_count"]) for row in family_rows):
        raise AssertionError("activation or pair projection is forbidden")

    input_roles = {
        OCCURRENCE_PATH: "IMMUTABLE_CHECKPOINT004_OCCURRENCE_UNIVERSE",
        FAMILY_PATH: "IMMUTABLE_CHECKPOINT004_FAMILY_UNIVERSE",
        CROSSWALK_PATH: "IMMUTABLE_PARTICIPANT_SENSE_AUTHORITY",
        CENSUS_PATH: "IMMUTABLE_CHECKPOINT004_HEADLINE_AND_CLOSURE_BOUNDARY",
        METHOD_PATH: "GOVERNED_EVIDENCE_AND_ACTIVATION_METHOD",
        GRAPH_PATH: "IMMUTABLE_ROUND16A_ACTIVE_PAIR_BASELINE",
        GENERATOR_PATH: "DETERMINISTIC_GENERATOR_SOURCE",
    }
    source_paths = sorted({row["source_path"] for row in occurrence_rows})
    all_input_paths = [OCCURRENCE_PATH, FAMILY_PATH, CROSSWALK_PATH, CENSUS_PATH, METHOD_PATH, GRAPH_PATH] + source_paths + [GENERATOR_PATH]
    if len(all_input_paths) != len(set(all_input_paths)):
        raise AssertionError("duplicate input path")
    input_rows: list[dict[str, Any]] = []
    for ordinal, relative in enumerate(all_input_paths, 1):
        actual = sha256_file(relative)
        pinned = PINNED_INPUT_SHA256.get(relative, actual if relative == GENERATOR_PATH else "")
        if relative != GENERATOR_PATH and not pinned:
            raise AssertionError(f"unbound source input: {relative}")
        input_rows.append(finalize_row({
            "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
            "input_ordinal": ordinal,
            "path": relative,
            "input_role": input_roles.get(relative, "ROW_EXACT_UPSTREAM_SOURCE_FOR_SELECTED_OCCURRENCES"),
            "bytes": (REPO / relative).stat().st_size,
            "input_record_count": input_record_count(relative),
            "sha256": actual,
            "pinned_sha256": pinned,
            "pin_match": "true" if actual == pinned else "false",
        }))
    if any(row["pin_match"] != "true" for row in input_rows):
        raise AssertionError("input pin mismatch")

    gap_rows = [
        ("GAP-010", "Twenty-four checkpoint-004 families remain undisposed after tranche A", "CLOSURE_BLOCKING", "OPEN_24_FAMILIES", "Eleven of 35 families now have final unsplit-parent dispositions; the other 24 remain pending.", "GOVERNED_EVIDENCE_REVIEW", "Complete additive tranches and prove all 35 families have one final parent disposition."),
        ("GAP-011", "Evidence-bearing inputs are not governed higher-order support", "CLOSURE_BLOCKING", "OPEN_13_INPUTS", "Thirteen locator-bearing inputs were separated from 99 non-support occurrences; none is activated as support.", "RIGHTS_SOURCE_TEXT_AND_HUMAN_AUTHORITY", "Lawfully review text, locators, senses, rights, roles, scope, and synthesis for each conditional queue item."),
        ("GAP-012", "Scoped child and reroute resolution", "CLOSURE_BLOCKING", "OPEN_10_CONDITIONAL_RECORDS", "Ten conditional records preserve three split PCM cases, two device cases, one channel case, one material-chain case, two semantic reroutes, and one mobility case.", "SCOPE_CASE_AND_SENSE_AUTHORITY", "Review each conditional record without mutating its disposed unsplit parent or prematurely creating an association ID."),
        ("GAP-013", "Counterevidence and falsification review for tranche A", "CLOSURE_BLOCKING", "NOT_STARTED", "All 11 parent families fail closed and all conditional records explicitly retain an open counterevidence gate.", "SCHOLARLY_REVIEW", "Run case-specific falsification, conflicting-scope, and source-family review before any child support decision."),
        ("GAP-014", "Source-container and structural-echo promotion risk", "CLOSURE_BLOCKING", "CONTROLLED_IN_TRANCHE_A_CONTINUES_GLOBALLY", "Ninety-one structural echoes, three synthetic controls, and four source-container co-occurrences are explicitly non-evidence.", "METHOD_AND_VERIFIER", "Require independent verification that later tranches and product reconciliation never promote these classes."),
        ("GAP-015", "Pair clique and pair projection leakage", "CLOSURE_BLOCKING", "CONTROLLED_NO_PROJECTIONS", "Families 2 and 5 each have all three internal pairs active yet remain unsupported as unsplit groups; zero pair projections were created.", "INCIDENCE_SEMANTICS_AND_VERIFIER", "Retest clique-invalidity and hyperedge-without-projection cases in the independent verifier."),
        ("GAP-016", "Product realization remains unavailable for tranche A", "CLOSURE_BLOCKING", "OPEN", "All 11 parents and all 10 conditional records are product-ineligible; no runtime or read model changed.", "GLOBAL_COHERENCE_AND_PRODUCT_AUTHORITY", "Only map independently validated active associations after complete evidence and global-coherence review."),
    ]
    gap_rows_final = [finalize_row({
        "gap_id": gap_id,
        "last_reviewed_checkpoint": "CHECKPOINT-005-TRANCHE-A",
        "gap": gap,
        "severity": severity,
        "status": status,
        "checkpoint005_tranche_a_evidence": evidence,
        "authority_dependency": dependency,
        "required_next_action": action,
    }) for gap_id, gap, severity, status, evidence, dependency, action in gap_rows]

    census = {
        "format": "trace-round16b-evidence-disposition-tranche-a-census-v1",
        "builder_version": BUILDER_VERSION,
        "source_sha": AUTHORIZED_SOURCE_SHA,
        "source_tree": AUTHORIZED_SOURCE_TREE,
        "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
        "review_tranche": TRANCHE_ID,
        "checkpoint004_candidate_family_count": 35,
        "checkpoint004_trigger_occurrence_count": 359,
        "tranche_family_count": len(family_rows),
        "tranche_linked_occurrence_count": len(occurrence_rows),
        "occurrence_evidence_class_counts": dict(sorted(class_counts.items())),
        "final_parent_disposition_counts": dict(sorted(Counter(row["final_parent_disposition"] for row in family_rows).items())),
        "conditional_scoped_child_or_reroute_queue_count": len(queue_rows),
        "conditional_queue_action_counts": dict(sorted(Counter(row["queue_action"] for row in queue_rows).items())),
        "internal_active_pair_count_distribution": dict(sorted(Counter(str(row["internal_active_pair_count"]) for row in family_rows).items())),
        "association_identity_created_count": 0,
        "association_activation_count": 0,
        "pair_projection_created_count": 0,
        "product_eligible_count": 0,
        "active_pending_review_count": 0,
        "remaining_undisposed_checkpoint004_family_count": 24,
        "closure": {
            "pair_association_closure": False,
            "higher_order_association_closure": False,
            "global_composition_coherence_closure": False,
            "product_association_reachability_closure": False,
            "computational_space_closure": False,
            "function3_closure": False,
        },
        "semantic_boundary": "Final dispositions apply only to the eleven unsplit checkpoint-004 parent review families. Conditional scoped children and reroutes are inactive review queue records, not governed associations or support decisions.",
    }

    note = f"""# Checkpoint 005 — Evidence disposition tranche A

## Boundary

This additive tranche binds checkpoint 004 `{PARENT_CHECKPOINT_SHA}` and reviews eleven unchanged participant-set families. It does not mutate the v1/v2 census, create an association identity, project a hyperedge into pairs, change the product model, or claim closure.

The 112 linked trigger occurrences are conserved row-exactly and separated by evidentiary role:

- 13 `EVIDENCE_BEARING` inputs, retained only for bounded scoped review;
- 91 `STRUCTURAL_ECHO` records, which reconcile prior product/topology descendants but are not evidence;
- 3 `SYNTHETIC_CONTROL` records, which test software behavior but are not evidence;
- 1 `NEGATIVE_CONTEXT` record, which explicitly blocks an unsupported topology/role synthesis;
- 4 `SOURCE_CONTAINER_COOCCURRENCE` rows, which reuse one exhibition container and do not support an exact three-member association.

## Fail-closed parent decisions

All eleven unsplit parents now have substantive final dispositions: five bounded-sense/scope conflicts, three inquiry-only/unresolved decisions, one insufficient-evidence decision, one topology/role conflict, and one co-occurrence-only decision. These are final for the unchanged unsplit parent families; they do not pre-decide ten separately recorded conditional scoped-child/reroute reviews.

The pair baseline is reconstructed from the frozen Round 16A graph. In particular, `consumption / mediation / production` and `production site / material displacement / supply chain` each contain all three active internal pairs and still fail group activation. This is the required clique-does-not-imply-hyperedge control.

## Conditional queue

Ten fail-closed records preserve possible scoped work: three PCM cases, two mediating-device cases, one mediating-channel case, one named material-chain case, the Brazilian-exposition case reroute, the Buenos-Aires modifier/role reroute, and one Tejo Remy mobility case. Candidate support-mode labels in that queue are review hypotheses only. Rights, lawful source-text review, bounded-sense/case review, external design-history review, and counterevidence review remain open.

## Closure

No association was activated, no pair projection was created, and no product path changed. Twenty-four checkpoint-004 families remain undisposed after tranche A. Pair, higher-order, global-coherence, reachability, computational-space, and Function 3 closure all remain false.
""".encode("utf-8")

    artifacts: dict[str, bytes] = {
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-occurrence-disposition-tranche-a-v1.tsv": tsv_bytes(OCCURRENCE_FIELDS, occurrence_rows),
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/family-evidence-disposition-tranche-a-v1.tsv": tsv_bytes(FAMILY_FIELDS, family_rows),
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/conditional-scoped-child-reroute-queue-tranche-a-v1.tsv": tsv_bytes(QUEUE_FIELDS, queue_rows),
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-input-manifest-tranche-a-v1.tsv": tsv_bytes(INPUT_FIELDS, input_rows),
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/recursive-gap-ledger-checkpoint005-tranche-a-v1.tsv": tsv_bytes(GAP_FIELDS, gap_rows_final),
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-census-tranche-a-v1.json": json_bytes(census),
        "docs/research/trace-v49-exploration-higher-order-association-closure-round16b/08_EVIDENCE_DISPOSITION_TRANCHE_A.md": note,
    }
    output_hashes = {
        path: {"bytes": len(payload), "sha256": sha256_bytes(payload)}
        for path, payload in sorted(artifacts.items())
    }
    receipt = {
        "format": "trace-round16b-evidence-disposition-tranche-a-build-receipt-v1",
        "builder_version": BUILDER_VERSION,
        "source_sha": AUTHORIZED_SOURCE_SHA,
        "source_tree": AUTHORIZED_SOURCE_TREE,
        "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
        "review_tranche": TRANCHE_ID,
        "input_count": len(input_rows),
        "input_manifest_sha256": sha256_bytes(artifacts["docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-input-manifest-tranche-a-v1.tsv"]),
        "family_count": 11,
        "linked_occurrence_count": 112,
        "occurrence_evidence_class_counts": dict(sorted(class_counts.items())),
        "conditional_queue_count": 10,
        "association_identity_created_count": 0,
        "association_activation_count": 0,
        "pair_projection_created_count": 0,
        "closure_flags_true_count": 0,
        "output_count_excluding_receipt": len(artifacts),
        "output_hashes": output_hashes,
        "aggregate_output_sha256": sha256_text(canonical_json(output_hashes)),
        "status": "PASS_FAIL_CLOSED_TRANCHE_A",
    }
    artifacts["docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-build-receipt-tranche-a-v1.json"] = json_bytes(receipt)
    return artifacts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="compare generated bytes with committed artifacts")
    args = parser.parse_args()
    artifacts = build_artifacts()
    if args.check:
        mismatches = []
        for relative, expected in artifacts.items():
            path = REPO / relative
            if not path.exists() or path.read_bytes() != expected:
                mismatches.append(relative)
        if mismatches:
            raise SystemExit("deterministic artifact mismatch: " + ";".join(mismatches))
        print(canonical_json({"status": "PASS", "mode": "CHECK", "artifact_count": len(artifacts)}))
        return
    for relative, payload in artifacts.items():
        path = REPO / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    receipt_path = RAW / "evidence-disposition-build-receipt-tranche-a-v1.json"
    print(receipt_path.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
