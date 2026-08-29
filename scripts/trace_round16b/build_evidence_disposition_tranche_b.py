#!/usr/bin/env python3
"""Build the deterministic Round 16B evidence-disposition tranche B.

This additive builder binds the published checkpoint-005 tranche-A tip and
reviews the fourteen remaining arity-three participant-set families from the
immutable checkpoint-004 v2 census.  It conserves all 187 linked trigger
occurrences, assigns each unsplit parent a final fail-closed disposition, and
records 37 scoped-child, pair/scope-reroute, derivative-reconciliation, or
parent-close queue controls.  Queue rows are not association candidates.

No association identity, activation, pair projection, product eligibility, or
closure claim is created here.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any

import build_evidence_disposition_tranche_a as base


REPO = base.REPO
RAW = base.RAW
RESEARCH = base.RESEARCH

AUTHORIZED_SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
AUTHORIZED_SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
PARENT_CHECKPOINT_SHA = "adf3cc7a214aa1b8fdaef75b7a9e8888c39c906e"
TRANCHE_ID = "CHECKPOINT-006-EVIDENCE-TRANCHE-B"
BUILDER_VERSION = "trace-round16b-evidence-disposition-tranche-b-v1"

OCCURRENCE_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/candidate-trigger-occurrence-ledger-v2.tsv"
FAMILY_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/local-candidate-family-ledger-v2.tsv"
CROSSWALK_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/concept-sense-crosswalk-v1.tsv"
CENSUS_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/local-candidate-census-v2.json"
METHOD_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/higher-order-association-method-v1.json"
TAXONOMY_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/association-disposition-taxonomy.tsv"
DATABASE_LEDGER_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/database-discovery-occurrence-ledger-v2.tsv"
GRAPH_PATH = "docs/audits/v49-exploration-full-space-closure-round1/raw/validated-association-graph-v2.json"
CALIBRATION_PATH = "docs/audits/v49-exploration-association-calibration-round1/raw/association-calibration.tsv"
TRANCHE_A_OCCURRENCE_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-occurrence-disposition-tranche-a-v1.tsv"
TRANCHE_A_FAMILY_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/family-evidence-disposition-tranche-a-v1.tsv"
TRANCHE_A_RECEIPT_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-build-receipt-tranche-a-v1.json"
TRANCHE_A_GENERATOR_PATH = "scripts/trace_round16b/build_evidence_disposition_tranche_a.py"
GENERATOR_PATH = "scripts/trace_round16b/build_evidence_disposition_tranche_b.py"

ARITY4_SWEDEN_KEY = "89817e7a449f1cc7b574fb1b89c9541f765e52825c5cb62bf0a2bb833e8f970a"
ARITY4_SWEDEN_OCCURRENCE_IDS = [
    "R16B-TRIGGER-OCC:1826f68aa42a92bc6dca9d860b71f6023175d5f4f0c28713fd354e2069c54ff8",
    "R16B-TRIGGER-OCC:46f134c8d09b178d1550ae7fff01581b03f2a902eb245432fe7e7b09fc66b0ab",
]

PINNED_INPUT_SHA256 = {
    OCCURRENCE_PATH: "1685e5bfdab735657ce78499b2597e6a20aecd7402d97f515b162a5d16009cd6",
    FAMILY_PATH: "cd4c3ca997c0f4cd5919d4e29d89ca45291fae4f70f78a49742aafb9c76baea7",
    CROSSWALK_PATH: "dfc1751482f3e74de78c2a94fd46f20eb3538d26e8c6bbf94482cac9534e770a",
    CENSUS_PATH: "b40e28810aa59a0e2ac926e403cf45ba9b032b465ee54a62fd7e32b2f6e4fe31",
    METHOD_PATH: "f37ff8aa97d3c9a0d417ee0a9e6ef96971b0c0985bf88bf7bb59af8da8d106e7",
    TAXONOMY_PATH: "20248f9d62f672f88ce1aa691e059e6459747deb9674a3b600ac9959465b165d",
    DATABASE_LEDGER_PATH: "f0bd85a860bd4e14d2010ec3bf361a2830975a4ab9927373fc7d7f32fade3f13",
    GRAPH_PATH: "1dee15d7cc0a9aa25f2a4a0fd7a352d2df5e7eacf88bd71badec5ebd476063bd",
    CALIBRATION_PATH: "cbb41db463dafcd43da4779e2db271fd2c1df0b4c769d5ea1d59bb8fa52333b8",
    TRANCHE_A_OCCURRENCE_PATH: "fc5f9716838af109f3b1c5e097cbefe6c8dd58f37210e7562b67bd8c80e717a9",
    TRANCHE_A_FAMILY_PATH: "5e77187942e0815a0291c24374bbc389cd09a78d9165977f5e73a63fad7fe7f0",
    TRANCHE_A_RECEIPT_PATH: "b4cad410eee7ad36a411f4dbf68eb6cb840c308790878899e216384f4a4d89e1",
    TRANCHE_A_GENERATOR_PATH: "d59b2434c573549cc151ac83a5f3904b6443a70bf1942e2380d510f663847501",
    "data/prefreeze_candidate_v48.sqlite": "ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e",
    "docs/audits/v49-exploration-association-calibration-round1/raw/evidence-provenance.tsv": "3bfc526c160909838da90db700a72c987e1b9ea80fb605358a400951c64c2d8c",
    "docs/audits/v49-exploration-full-space-closure-round1/raw/canonical-composition-registry-v2.json": "51c3e29909a8aa5226a7d18ebaef896aa52c48be6725d722c869515874c6c24d",
    "docs/research/trace-v49-design-history-relation-grammar-round1/07_GRAMMAR_ATTESTATION_REGISTRY.tsv": "62b56052829d23cd2cf820a232479f74cbf663d64465cdc242900e71220df2a8",
    "docs/research/trace-v49-design-history-relation-grammar-round1/14_CLUSTER_EVIDENCE_HANDOFF.tsv": "0fca1a4995577ddb3e33e1a12bebb18ccd14e74684755c26749029722dfb2ccd",
    "docs/research/trace-v49-exploration-composition-review-round1/04_COMPOSITION_EVIDENCE_REGISTRY.tsv": "c3d24a2a6f90d1e0b6ce7f0f483d04a752761cb3699294039c97778ed84dd714",
    "frontend/generated/trace-exploration-v2/production-read-model.json": "53eaf59c95446eeb3781a7153183c54b3ff59fd52f21744cc917053959dfdcc9",
    "scripts/trace-v49-exploration-association-calibration/fixtures/nary-local-coherence-v1.json": "32c8fa359e6bd14d3d2e4d62c4a276a1bcfa6daee1c29e9b18bffb427f6e0e56",
    "scripts/trace-v49-exploration-composition-engine/fixtures/composition-fixtures-v1.json": "0322c715166f4ed8cb4603a5a1f10db69512ef3f41386cec6450c6d52813badb",
    "scripts/trace-v49-exploration-real-database/real-composition-registry-v1.json": "cad6669c93a52924a17d31d07a16b1e1e5b0ffa06917f3cd467a5f2db003393f",
    "scripts/trace-v49-exploration-real-database/scholarly-source-additions-v1.tsv": "473eb44a3b43d3f63261076b13c05e09a1e8b2abb10de8cf73765b0aea597752",
}


FAMILY_SPECS = [
    {
        "ordinal": 12,
        "key": "07d5c44f285178774f70755012d2745feec81d240210c340b5910a738ae0a837",
        "disposition": "HARD_NEGATIVE",
        "rationale": "The R15 hard-negative intrusion fixture contains R14-ASSOC-026, whose professionalization/material-displacement pair is explicitly hard-negative; that defeats the exact proposed triad while leaving R14-ASSOC-010 separately governed.",
        "scope_status": "CLOSE_HARD_NEGATIVE_PARENT_RETAIN_SEPARATE_MATERIAL_CHAIN_PAIR",
        "nonclaims": ["the hard-negative triad does not invalidate the separately governed material-displacement/supply-chain pair", "future independently supported hyperedge evidence is not logically impossible"],
    },
    {
        "ordinal": 13,
        "key": "0e719db533fd03f71aa5fbb293aa0d6aa8b79453db51fe8e0f8b7f0fc59fede9",
        "disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "rationale": "Seven V&A object-centred database loci attach object-type/category and material/technique nodes to seven distinct objects; those roles do not match the current scholarly concept senses and cannot be merged into one historical group.",
        "scope_status": "SPLIT_SEVEN_OBJECT_INCIDENCE_REVIEWS_CLOSE_UNSPLIT_PARENT",
        "nonclaims": ["database incidence is metadata discovery, not association support", "objects are not merged", "no internal pair is manufactured"],
    },
    {
        "ordinal": 14,
        "key": "15f5757830dfe043fb27e73c28ff3bfd902aaa9c938ab254fda8682d359a7249",
        "disposition": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
        "rationale": "Two active pair claims share locators in two source cases, but only the COMP-SRC-001 formal-design-education configuration warrants a conditional child review; COMP-SRC-002 remains a professionalization/institutionalization pair path.",
        "scope_status": "ONE_FORMAL_EDUCATION_CHILD_ONE_PAIR_REROUTE_AND_DERIVATIVE_RECONCILIATION",
        "nonclaims": ["shared pair locators do not establish an unsplit group", "university visual-identity practice is not automatically design education", "no professional sequence or direction is inferred"],
    },
    {
        "ordinal": 15,
        "key": "23b72032e8165ac9f164a43ac0e1932f2fe4354f1b89f62d67ebe7d497de7af1",
        "disposition": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
        "rationale": "The parent combines a Turin 1961 triad review, a Brussels 1958 two-edge pair path, a synthetic control, and derivatives; the Sweden 1954 support belongs to the distinct governed arity-four review family.",
        "scope_status": "TURIN_CHILD_BRUSSELS_PAIR_PATH_SWEDEN_ARITY4_REROUTE_AND_DERIVATIVES",
        "nonclaims": ["a pairwise clique is not a group", "diplomacy is not propaganda", "the Sweden arity-four source is not projected into triads"],
    },
    {
        "ordinal": 16,
        "key": "2770b6b66713cd3191cec7b14915b14624cbda9b7307b53bb230ea7f29d8caec",
        "disposition": "INSUFFICIENT_EVIDENCE",
        "rationale": "The explicit cluster handoff records DEFER_FLATTENING_RISK and states that the sources supply neither one shared three-node composition nor an independent cluster grammar.",
        "scope_status": "CLOSE_NO_CHILD_RETAIN_FLATTENING_RISK",
        "nonclaims": ["shared authority framing is not one historical configuration", "institutionalization, canonization, and professionalization are not collapsed"],
    },
    {
        "ordinal": 17,
        "key": "3648ab4f374cda7a490244914de785b764e7e4f7c872f094e8a2d3f03a71a560",
        "disposition": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
        "rationale": "This subset is emitted only by Round 16A structural descendants; the bounded Sweden 1954 configuration that binds these concepts also includes propaganda and must be reviewed at arity four.",
        "scope_status": "REROUTE_TO_SWEDEN_1954_ARITY4_AND_RECONCILE_DERIVATIVES",
        "nonclaims": ["there is no exhibition/trade claim from path connectivity", "the arity-four source is not projected into this triad", "diplomatic outcome is not asserted"],
    },
    {
        "ordinal": 18,
        "key": "3fab395d77bb9112b04a2eedc91aa128a006839ed048fb6a3a143762a35a3c3c",
        "disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "rationale": "The DGI capture places advertising and cultural transformation in the abstract but propaganda in a separate introduction locus; bridging those sections would invent one triad and the object year remains unresolved.",
        "scope_status": "SPLIT_DGI_LOCUS_TO_TWO_PAIR_INQUIRIES_CLOSE_UNSPLIT_PARENT",
        "nonclaims": ["separated source loci are not one configuration", "advertising is not generally propaganda", "no automatic T0-to-T1 transformation is claimed"],
    },
    {
        "ordinal": 19,
        "key": "7696ac77a3bd8ac70e8e0181b3ae969502426a44200925dffb65ef88312e954a",
        "disposition": "COOCCURRENCE_ONLY",
        "rationale": "R16-SRC-005 is explicitly vocabulary-support-only; its supported-terms field does not prove three distinct participants, and education versus design education requires identity or specialization review.",
        "scope_status": "RETAIN_CRAFT_EDUCATION_PAIR_RESOLVE_EDUCATION_IDENTITY",
        "nonclaims": ["one supported-terms field is not group evidence", "education and design education are not presumed distinct", "vocabulary support does not activate an association"],
    },
    {
        "ordinal": 20,
        "key": "83009b1d124d4635a57866eeffba5e1a1a33e499bd60b30c6346b94ff1a04f8e",
        "disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "rationale": "The direct contact-zone record could support a new source-specific negotiation sense, while the current cultural-negotiation sense is Keraton-bounded and the Keraton evidence does not include rejection; the legacy product crosses those cases.",
        "scope_status": "NEW_CONTACT_ZONE_SENSE_CHILD_KERATON_PAIR_REROUTE_AND_DERIVATIVE_RECONCILIATION",
        "nonclaims": ["contact-zone alternatives are not stages", "participation is not presumed equal or voluntary", "rejection is not imported into the Keraton case"],
    },
    {
        "ordinal": 21,
        "key": "9ade19c60e22d8aa127040cefd633119f8b05e04baf0f814d2d008d0aae8796e",
        "disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "rationale": "One Vienna 1938–1939 poster provides an object-specific discovery locus, but its advertising-as-promotion role conflicts with the current advertising sense and lawful source/visual, rights, and human review remain open.",
        "scope_status": "ONE_VIENNA_OBJECT_ASSOCIATION_REVIEW_PENDING_NEW_ADVERTISING_SENSE",
        "nonclaims": ["metadata is not association evidence", "advertising, exhibition, and propaganda are not generally equivalent", "the object-specific inquiry is inactive"],
    },
    {
        "ordinal": 22,
        "key": "af25d1d4c93f79886769d53d071805bd5b6726130b153e4484121321d1122e3a",
        "disposition": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
        "rationale": "The triad has three active internal pairs but only structural descendants at this identity; its common Sweden 1954 evidence belongs to the exact four-node exposition/trade/propaganda/design-diplomacy review.",
        "scope_status": "REROUTE_TO_SWEDEN_1954_ARITY4_AND_RECONCILE_DERIVATIVES",
        "nonclaims": ["an active pair clique is not group coherence", "the four-node source is not projected into a triad", "one exposition case does not generalize relation identity"],
    },
    {
        "ordinal": 23,
        "key": "d6dfcd4e355294899be8838eb8ec71439d8911ea19f8aa92401d1a52becf76c0",
        "disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "rationale": "GRAM-ATT-026 treats professional education and training as institutional professional domains, whereas the current education sense is Bauhaus arts-crafts vocabulary support; a new source-specific sense is required.",
        "scope_status": "ONE_PROFESSIONAL_EDUCATION_TRAINING_CHILD_PENDING_NEW_SENSE",
        "nonclaims": ["professional education is not substituted by the current Bauhaus education sense", "no universal direction or chronology is inferred", "the local attestation is inquiry-only"],
    },
    {
        "ordinal": 24,
        "key": "e33bd6538eb80f04087e13b1896ff995a5523453a10e8f4aec460ef9fdd87376",
        "disposition": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
        "rationale": "This exact triad is present only in Round 16A derivatives; the bounded source that joins exhibition, trade, and propaganda also contains design diplomacy and is queued only at arity four.",
        "scope_status": "REROUTE_TO_SWEDEN_1954_ARITY4_AND_RECONCILE_DERIVATIVES",
        "nonclaims": ["pair paths and layouts are not group support", "the four-node source is not projected into this triad", "no direction or outcome is asserted"],
    },
    {
        "ordinal": 25,
        "key": "e6b89317c05c3543ab2cd0005c53716c62dcf45e75965992f7b593873772d0e4",
        "disposition": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        "rationale": "The two AIC loci are distinct 1950 and 1948 Chicago objects; education is only a subject/discovery-context field in the 1950 case and needs a new proved design-school mechanism in the 1948 inquiry.",
        "scope_status": "SPLIT_CHICAGO_1950_PAIR_AND_1948_TRIAD_INQUIRY_CLOSE_UNSPLIT_PARENT",
        "nonclaims": ["the two objects are not merged", "subject tags and discovery queries do not prove education", "object discovery does not manufacture pair or group associations"],
    },
]


SOURCE_CLASS_BY_SURFACE = {
    "R16B-LOCAL-SURF-R15-FIXTURES": "R15_RESEARCH_FIXTURE",
    "SURF-DB-001": "DATABASE_DISCOVERY_LOCUS",
    "R16B-LOCAL-SURF-R14-PROVENANCE": "R14_SHARED_LOCATOR_PROVENANCE",
    "R16B-LOCAL-SURF-R16A-SUBGRAPHS": "R16A_CONNECTED_SUBGRAPH",
    "R16B-LOCAL-SURF-R16A-TOPOLOGIES": "R16A_PRESENTATION_TOPOLOGY",
    "R16B-LOCAL-SURF-R16A-PRODUCTION": "R16A_PRODUCT_COMPOSITION",
    "R16B-LOCAL-SURF-R14-NARY": "R14_SYNTHETIC_NARY_CONTROL",
    "R16B-LOCAL-SURF-R10-CLUSTERS": "R10_CLUSTER_HANDOFF",
    "R16B-LOCAL-SURF-R16-SOURCES": "R16_SCHOLARLY_SOURCE_METADATA",
    "R16B-LOCAL-SURF-R13-EVIDENCE": "R13_EXACT_EVIDENCE_RECORD",
    "R16B-LOCAL-SURF-R16-COMPOSITIONS": "R16_LEGACY_PRODUCT_COMPOSITION",
    "R16B-LOCAL-SURF-R10-ATTESTATIONS": "R10_GRAMMAR_ATTESTATION",
}

EXPECTED_SOURCE_CLASS_COUNTS = {
    "DATABASE_DISCOVERY_LOCUS": 11,
    "R10_CLUSTER_HANDOFF": 1,
    "R10_GRAMMAR_ATTESTATION": 1,
    "R13_EXACT_EVIDENCE_RECORD": 1,
    "R14_SHARED_LOCATOR_PROVENANCE": 5,
    "R14_SYNTHETIC_NARY_CONTROL": 2,
    "R15_RESEARCH_FIXTURE": 5,
    "R16A_CONNECTED_SUBGRAPH": 15,
    "R16A_PRESENTATION_TOPOLOGY": 36,
    "R16A_PRODUCT_COMPOSITION": 108,
    "R16_LEGACY_PRODUCT_COMPOSITION": 1,
    "R16_SCHOLARLY_SOURCE_METADATA": 1,
}

EXPECTED_FAMILY_SOURCE_COUNTS = {
    "07d5c44f": {"R15_RESEARCH_FIXTURE": 1},
    "0e719db5": {"DATABASE_DISCOVERY_LOCUS": 7},
    "15f57578": {"R14_SHARED_LOCATOR_PROVENANCE": 2, "R16A_CONNECTED_SUBGRAPH": 1, "R16A_PRESENTATION_TOPOLOGY": 3, "R16A_PRODUCT_COMPOSITION": 9},
    "23b72032": {"R14_SHARED_LOCATOR_PROVENANCE": 2, "R14_SYNTHETIC_NARY_CONTROL": 1, "R15_RESEARCH_FIXTURE": 2, "R16A_CONNECTED_SUBGRAPH": 4, "R16A_PRESENTATION_TOPOLOGY": 9, "R16A_PRODUCT_COMPOSITION": 27},
    "2770b6b6": {"R10_CLUSTER_HANDOFF": 1},
    "3648ab4f": {"R16A_CONNECTED_SUBGRAPH": 1, "R16A_PRESENTATION_TOPOLOGY": 3, "R16A_PRODUCT_COMPOSITION": 9},
    "3fab395d": {"DATABASE_DISCOVERY_LOCUS": 1},
    "7696ac77": {"R16_SCHOLARLY_SOURCE_METADATA": 1},
    "83009b1d": {"R13_EXACT_EVIDENCE_RECORD": 1, "R14_SHARED_LOCATOR_PROVENANCE": 1, "R14_SYNTHETIC_NARY_CONTROL": 1, "R15_RESEARCH_FIXTURE": 2, "R16A_CONNECTED_SUBGRAPH": 4, "R16A_PRESENTATION_TOPOLOGY": 9, "R16A_PRODUCT_COMPOSITION": 27, "R16_LEGACY_PRODUCT_COMPOSITION": 1},
    "9ade19c6": {"DATABASE_DISCOVERY_LOCUS": 1},
    "af25d1d4": {"R16A_CONNECTED_SUBGRAPH": 4, "R16A_PRESENTATION_TOPOLOGY": 9, "R16A_PRODUCT_COMPOSITION": 27},
    "d6dfcd4e": {"R10_GRAMMAR_ATTESTATION": 1},
    "e33bd653": {"R16A_CONNECTED_SUBGRAPH": 1, "R16A_PRESENTATION_TOPOLOGY": 3, "R16A_PRODUCT_COMPOSITION": 9},
    "e6b89317": {"DATABASE_DISCOVERY_LOCUS": 2},
}

EXPECTED_GENERIC_CLASS_COUNTS = {
    "EVIDENCE_BEARING_INPUT": 7,
    "EXPLICIT_NEAR_MISS": 1,
    "HARD_NEGATIVE_CONTROL": 1,
    "METADATA_DISCOVERY": 11,
    "STRUCTURAL_ECHO": 164,
    "SYNTHETIC_CONTROL": 2,
    "VOCABULARY_ONLY_COOCCURRENCE": 1,
}

OCCURRENCE_FIELDS = [
    "parent_checkpoint_sha", "review_tranche", "family_ordinal", "candidate_id",
    "participant_set_key", "trigger_occurrence_id", "source_occurrence_sha256",
    "trigger_id", "trigger_class", "emission_kind", "source_path", "input_surface_id",
    "input_record_refs_json", "source_locator", "content_hashes_json",
    "upstream_record_ids_json", "upstream_source_ids_json", "upstream_locators_json",
    "occurrence_source_class", "occurrence_evidence_class", "classification_detail",
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
    "linked_occurrence_ids_sha256", "occurrence_source_class_counts_json",
    "occurrence_evidence_class_counts_json", "evidence_bearing_input_count",
    "metadata_discovery_count", "structural_echo_count", "synthetic_control_count",
    "hard_negative_control_count", "explicit_near_miss_count",
    "vocabulary_only_cooccurrence_count", "review_input_record_ids_json",
    "review_locators_json", "internal_possible_pair_count", "internal_active_pair_count",
    "internal_active_pair_ids_json", "internal_active_round14_assessment_ids_json",
    "final_parent_disposition", "parent_disposition_status", "disposition_rationale",
    "scope_split_or_reroute_status", "queue_record_count",
    "conditional_scoped_child_review_count", "direct_group_support_status",
    "composite_group_support_status", "global_coherence_status", "rights_review_status",
    "source_text_review_status", "human_review_status", "counterevidence_review_status",
    "association_identity_status", "association_activation_status", "product_eligibility",
    "pair_projection_count", "explicit_nonclaims_json", "record_sha256",
]

QUEUE_FIELDS = [
    "parent_checkpoint_sha", "review_tranche", "memo_queue_ref", "queue_id",
    "queue_record_kind", "parent_candidate_id", "parent_family_ordinal", "queue_action",
    "target_or_child", "target_candidate_or_pair_refs_json", "scope_key", "scope_label",
    "proposed_participant_labels_json", "proposed_participant_sense_ids_json",
    "proposed_relation_form", "candidate_support_mode_if_reviewed",
    "evidence_occurrence_ids_json", "evidence_anchor_note", "active_pair_refs_json",
    "case_time_geography_institution_actor_mechanism_note",
    "required_scope_or_sense_resolution", "required_gates", "rights_review_status",
    "source_text_review_status", "human_review_status", "counterevidence_review_status",
    "queue_status", "association_identity_created", "association_active",
    "pair_projection_created", "product_effect", "product_eligibility",
    "explicit_nonclaims_json", "record_sha256",
]

INPUT_FIELDS = base.INPUT_FIELDS
GAP_FIELDS = [
    "gap_id", "last_reviewed_checkpoint", "gap", "severity", "status",
    "checkpoint006_tranche_b_evidence", "authority_dependency", "required_next_action",
    "record_sha256",
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


def source_class(occurrence: dict[str, str]) -> str:
    try:
        return SOURCE_CLASS_BY_SURFACE[occurrence["input_surface_id"]]
    except KeyError as exc:
        raise AssertionError(f"unclassified tranche-B input surface: {occurrence['input_surface_id']}") from exc


def generic_class(participant_set_key: str, exact_source_class: str) -> str:
    if participant_set_key.startswith("07d5c44f") and exact_source_class == "R15_RESEARCH_FIXTURE":
        return "HARD_NEGATIVE_CONTROL"
    if exact_source_class == "DATABASE_DISCOVERY_LOCUS":
        return "METADATA_DISCOVERY"
    if exact_source_class in {"R14_SHARED_LOCATOR_PROVENANCE", "R13_EXACT_EVIDENCE_RECORD", "R10_GRAMMAR_ATTESTATION"}:
        return "EVIDENCE_BEARING_INPUT"
    if exact_source_class == "R14_SYNTHETIC_NARY_CONTROL":
        return "SYNTHETIC_CONTROL"
    if exact_source_class == "R10_CLUSTER_HANDOFF":
        return "EXPLICIT_NEAR_MISS"
    if exact_source_class == "R16_SCHOLARLY_SOURCE_METADATA":
        return "VOCABULARY_ONLY_COOCCURRENCE"
    return "STRUCTURAL_ECHO"


def classification_policy(exact_source_class: str, evidence_class: str) -> tuple[str, str, str, str, str]:
    if evidence_class == "HARD_NEGATIVE_CONTROL":
        return (
            "R15_HARD_NEGATIVE_INTRUSION_CONTROL_BOUND_TO_R14_ASSOC_026",
            "The research fixture explicitly retains a hard-negative pair as an audit control; it cannot support the exact triad.",
            "HARD_NEGATIVE_CONTROL_INPUT_NOT_SUPPORT",
            "UPSTREAM_HARD_NEGATIVE_CONTROL_PRESENT",
            "NOT_APPLICABLE_CONTROL_RECORD",
        )
    if evidence_class == "METADATA_DISCOVERY":
        return (
            "DATABASE_LOCUS_METADATA_OR_OBJECT_INCIDENCE_DISCOVERY_ONLY",
            "The frozen database locus is a discovery trigger; bounded senses, exact source or visual evidence, rights, and global coherence remain unreviewed.",
            "METADATA_DISCOVERY_NOT_SUPPORT",
            "LAWFUL_SOURCE_OR_VISUAL_REVIEW_OPEN",
            "OPEN_SOURCE_TEXT_VISUAL_AND_ACCESS_RIGHTS_REVIEW",
        )
    if evidence_class == "EVIDENCE_BEARING_INPUT":
        return (
            f"{exact_source_class}_NOT_YET_GOVERNED_GROUP_SUPPORT",
            "A locator-bearing passage, attestation, or shared-locator provenance bundle is retained only as a scoped review input; no group disposition is inherited.",
            "SCOPED_REVIEW_INPUT_NOT_SUPPORT",
            "BOUNDED_UPSTREAM_RECORD_PRESENT_FULL_SOURCE_REVIEW_OPEN",
            "OPEN_FOR_ANY_SUPPORT_USE",
        )
    if evidence_class == "SYNTHETIC_CONTROL":
        return (
            "SYNTHETIC_PAIR_BINDING_LAYOUT_CONTROL_NOT_EVIDENCE",
            "The n-ary fixture tests software behavior and pair binding only; synthetic layout success is not historical group evidence.",
            "NOT_EVIDENCE_TEST_CONTROL_ONLY",
            "NOT_APPLICABLE_SYNTHETIC_CONTROL",
            "NOT_APPLICABLE_CONTROL_RECORD",
        )
    if evidence_class == "EXPLICIT_NEAR_MISS":
        return (
            "EXPLICIT_CLUSTER_NEAR_MISS_DEFER_FLATTENING_RISK",
            "The upstream cluster handoff explicitly states that no shared three-node composition or independent cluster grammar is supported.",
            "NEGATIVE_OR_NEAR_MISS_INPUT_NOT_SUPPORT",
            "BOUNDED_UPSTREAM_NON_SUPPORT_CONTEXT_REVIEWED",
            "NOT_APPLICABLE_NO_SUPPORT_USE",
        )
    if evidence_class == "VOCABULARY_ONLY_COOCCURRENCE":
        return (
            "SCHOLARLY_METADATA_VOCABULARY_SUPPORT_ONLY",
            "A supported-terms metadata field establishes vocabulary review value only and cannot prove distinct roles or an association.",
            "VOCABULARY_SUPPORT_ONLY_NOT_ASSOCIATION_EVIDENCE",
            "FULL_SOURCE_AND_DISTINCT_SENSE_REVIEW_OPEN",
            "OPEN_FOR_ANY_SUPPORT_USE",
        )
    return (
        f"{exact_source_class}_STRUCTURAL_DESCENDANT_NOT_EVIDENCE",
        "A prior subgraph, topology, fixture, product composition, or legacy product record is a reconciliation target, not historical evidence.",
        "NOT_EVIDENCE_RECONCILIATION_ONLY",
        "NOT_APPLICABLE_STRUCTURAL_RECORD",
        "NOT_APPLICABLE_TO_NON_SUPPORT_CLASSIFICATION",
    )


row_hash = base.row_hash
occurrence_digest = base.occurrence_digest
source_row_details = base.source_row_details
input_record_count = base.input_record_count


def resolve_occurrence_ids(all_occurrence_ids: list[str], prefixes: list[str]) -> list[str]:
    """Resolve each memo prefix to one immutable v2 occurrence, in prefix order."""
    resolved: list[str] = []
    for prefix in prefixes:
        matches = [value for value in all_occurrence_ids if occurrence_digest(value).startswith(prefix)]
        if len(matches) != 1:
            raise AssertionError(f"occurrence prefix must resolve exactly once: {prefix}: {matches}")
        resolved.append(matches[0])
    if len(set(resolved)) != len(resolved):
        raise AssertionError(f"duplicate occurrence resolved from prefixes: {prefixes}")
    return resolved


def build_queue_rows(
    families_by_key: dict[str, dict[str, str]],
    occurrences: list[dict[str, str]],
    active_pairs_by_family: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Materialize the reviewer memo's 37 controls without creating candidates."""
    occurrence_ids = [row["trigger_occurrence_id"] for row in occurrences]
    occurrences_by_family: dict[str, list[dict[str, str]]] = {}
    for row in occurrences:
        occurrences_by_family.setdefault(row["participant_set_key"], []).append(row)

    queue: list[dict[str, Any]] = []

    def add(
        memo_ref: str,
        family_prefix: str,
        kind: str,
        action: str,
        target: str,
        scope_key: str,
        scope_label: str,
        proposed_labels: list[str],
        relation_form: str,
        support_mode: str,
        evidence_prefixes: list[str],
        evidence_note: str,
        target_refs: list[str],
        context: str,
        resolution: str,
        gates: str,
        product_effect: str,
        nonclaims: list[str],
    ) -> None:
        family_keys = [key for key in families_by_key if key.startswith(family_prefix)]
        if len(family_keys) != 1:
            raise AssertionError(f"queue family prefix must resolve exactly once: {family_prefix}: {family_keys}")
        parent = families_by_key[family_keys[0]]
        parent_labels = json.loads(parent["canonical_labels_json"])
        parent_senses = json.loads(parent["participant_sense_ids_json"])
        sense_by_label = dict(zip(parent_labels, parent_senses, strict=True))
        proposed_senses = [
            sense_by_label.get(
                label,
                "REVIEW_ONLY_NEW_OR_SCOPE_SPECIFIC_SENSE:"
                + "_".join(character if character.isalnum() else "_" for character in label.upper()).strip("_"),
            )
            for label in proposed_labels
        ]
        evidence_ids = resolve_occurrence_ids(occurrence_ids, evidence_prefixes)
        identity = {
            "memo_queue_ref": memo_ref,
            "parent_candidate_id": parent["candidate_id"],
            "queue_action": action,
            "target_or_child": target,
            "scope_key": scope_key,
            "evidence_occurrence_ids": evidence_ids,
        }
        if kind == "PARENT_CLOSE_CONTROL":
            queue_status = "CLOSED_PARENT_CONTROL_NOT_ASSOCIATION"
            gate_status = "NOT_APPLICABLE_FINAL_PARENT_NON_SUPPORT"
        elif kind == "DERIVATIVE_RECONCILIATION":
            queue_status = "OPEN_DERIVATIVE_RECONCILIATION_NOT_ASSOCIATION"
            gate_status = "NOT_APPLICABLE_RECONCILIATION_CONTROL"
        else:
            queue_status = "OPEN_CONDITIONAL_REVIEW_NOT_ASSOCIATION"
            gate_status = "OPEN_NO_GATE_PASSED_BY_QUEUE"
        queue.append(finalize_row({
            "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
            "review_tranche": TRANCHE_ID,
            "memo_queue_ref": memo_ref,
            "queue_id": f"R16B-TRANCHE-B-QUEUE:{row_hash(identity)}",
            "queue_record_kind": kind,
            "parent_candidate_id": parent["candidate_id"],
            "parent_family_ordinal": next(spec["ordinal"] for spec in FAMILY_SPECS if spec["key"] == parent["participant_set_key"]),
            "queue_action": action,
            "target_or_child": target,
            "target_candidate_or_pair_refs_json": canonical_json(target_refs),
            "scope_key": scope_key,
            "scope_label": scope_label,
            "proposed_participant_labels_json": canonical_json(proposed_labels),
            "proposed_participant_sense_ids_json": canonical_json(proposed_senses),
            "proposed_relation_form": relation_form,
            "candidate_support_mode_if_reviewed": support_mode,
            "evidence_occurrence_ids_json": canonical_json(evidence_ids),
            "evidence_anchor_note": evidence_note,
            "active_pair_refs_json": canonical_json(active_pairs_by_family[parent["candidate_id"]]),
            "case_time_geography_institution_actor_mechanism_note": context,
            "required_scope_or_sense_resolution": resolution,
            "required_gates": gates,
            "rights_review_status": gate_status,
            "source_text_review_status": gate_status,
            "human_review_status": gate_status,
            "counterevidence_review_status": gate_status,
            "queue_status": queue_status,
            "association_identity_created": "false",
            "association_active": "false",
            "pair_projection_created": "false",
            "product_effect": product_effect,
            "product_eligibility": "INELIGIBLE_REVIEW_OR_RECONCILIATION_QUEUE_NOT_ASSOCIATION",
            "explicit_nonclaims_json": canonical_json(nonclaims + [
                "queue membership is not a governed association disposition",
                "no association identity, activation, pair projection, or product eligibility is created",
            ]),
        }))

    hard = ["4a7850042726"]
    vam = [
        ("13f8bfba9384", "SURF-VAM20K-03165", "Clowns; Germany; 1972; O1316564"),
        ("31bb942b9d71", "SURF-VAM20K-03010", "Ballett; Germany; 1968; O1316563"),
        ("3761e1065c6e", "SURF-VAM20K-03163", "Der Besuch der alten Dame; Germany; 1972; O1169376"),
        ("558e8cd312ff", "SURF-VAM20K-03052", "Herr Puntila und Sein Knecht Matti; Germany; 1969; O1316577"),
        ("ba22c60b7295", "SURF-VAM20K-03127", "Klaus Klettermaus und die anderen Tiere im Hackebackewald; Germany; 1973; O1316570"),
        ("f3e727d8ab1c", "SURF-VAM20K-03166", "Gesang vom Lusitanischen Popanz; Germany; 1972; O1316569"),
        ("f8f0eb5992f8", "SURF-VAM20K-00867", "Amerika Hurra; Germany; 1986-1987; O1316562"),
    ]

    add("TBQ-001", "07d5c44f", "PAIR_OR_SCOPE_REROUTE", "RETAIN_SEPARATE_PAIR", "R14-ASSOC-010", "MATERIAL_CHAIN_PAIR", "material displacement / supply chain bounded material-chain pair", ["material displacement", "supply chain"], "EXISTING_GOVERNED_PAIR_ONLY", "EXISTING_PAIR_ONLY", hard, "R14-EVID-010-01; R14-EVID-010-02; hard-negative fixture also carries separately governed R14-ASSOC-010.", ["R14-ASSOC-010"], "Bounded material chains; distinct from the hard-negative professionalization/material-displacement control.", "Retain the pair under its existing qualification; do not create the triad.", "NONE_BEYOND_EXISTING_PAIR_GOVERNANCE", "RETAIN_EXISTING_PAIR_PATH_ONLY", ["the hard-negative triad does not invalidate the separately governed pair"])
    add("TBQ-002", "07d5c44f", "PARENT_CLOSE_CONTROL", "CLOSE_PARENT_NON_SUPPORT", "R16B-LOCAL-FAMILY:07d5c44f", "EXACT_FROZEN_TRIAD", "material displacement / supply chain / professionalization", ["material displacement", "supply chain", "professionalization"], "UNSPLIT_PARENT_CONTROL", "HARD_NEGATIVE", hard, "R14-ASSOC-026; R15-COMP-006.", ["R14-ASSOC-026"], "Exact frozen triad containing an upstream hard-negative pair.", "Preserve final hard-negative parent disposition.", "FINAL_GOVERNED_PARENT_RECORD", "INELIGIBLE_AUDIT_CONTROL_ONLY", ["future independent hyperedge evidence is not logically impossible"])

    for offset, (prefix, target, object_scope) in enumerate(vam, 3):
        add(f"TBQ-{offset:03d}", "0e719db5", "CONDITIONAL_SCOPED_CHILD_REVIEW", "CREATE_OBJECT_INCIDENCE_REVIEW", target, target.replace("SURF-", "OBJECT_INCIDENCE_"), object_scope, ["photography", "advertising", "typography"], "OBJECT_FEATURE_INCIDENCE_REVIEW_NOT_ASSOCIATION", "OBJECT_FEATURE_INCIDENCE_NOT_ASSOCIATION", [prefix], f"{target}; frozen V&A object metadata locus.", [], object_scope, "Resolve new object-feature senses and review the lawful source or visual object record.", "LAWFUL_SOURCE_OR_VISUAL_REVIEW; RIGHTS; HUMAN_POLICY_REVIEW; COUNTEREVIDENCE", "NO_PRODUCT_UNTIL_REVIEW", ["no cross-object association", "no pair manufacture", "metadata classification is not historical evidence"])
    add("TBQ-010", "0e719db5", "PARENT_CLOSE_CONTROL", "CLOSE_UNSPLIT_PARENT", "R16B-LOCAL-FAMILY:0e719db5", "SEVEN_DISTINCT_VA_OBJECTS", "seven distinct V&A objects under current scholarly senses", ["photography", "advertising", "typography"], "UNSPLIT_PARENT_CONTROL", "BOUNDED_SENSE_OR_SCOPE_CONFLICT", [item[0] for item in vam], "R16B-DB-FAMILY:0e719db5; seven frozen database loci.", [], "Seven different objects, dates, and object-feature/category metadata roles.", "Keep the object reviews separate and close the current-sense unsplit parent.", "FINAL_GOVERNED_PARENT_RECORD", "INELIGIBLE", ["metadata classifications are not historical group evidence", "the seven objects are not merged"])

    add("TBQ-011", "15f57578", "CONDITIONAL_SCOPED_CHILD_REVIEW", "CREATE_SCOPED_CHILD_REVIEW", "formal design education / institutionalization / professionalization", "FORMAL_DESIGN_EDUCATION_1870_1970", "Western interior design, 1870-1970; named education and accreditation mechanisms", ["institutionalization", "design education", "professionalization"], "INCIDENCE_HYPEREDGE_REVIEW", "COHERENT_COMPOSITE_SUPPORT_CANDIDATE_NOT_DECIDED", ["fe60bb8d7d6a"], "COMP-SRC-001; COMP-EVID-001; accepted manuscript p.9.", [], "Western interior design, 1870-1970; education, association, accreditation, and occupational-trust mechanisms.", "Freeze a formal-design-education sense and complete REVIEW-PAIR-A plus REVIEW-NODE-002/-003.", "EXACT_TEXT; RIGHTS; SENSE; ROLE; SCOPE; HUMAN_REVIEW; COUNTEREVIDENCE", "NO_PRODUCT_UNTIL_REVIEW", ["no universal sequence or direction"])
    add("TBQ-012", "15f57578", "PAIR_OR_SCOPE_REROUTE", "REROUTE_TO_PAIR_ONLY", "R14-ASSOC-001", "GRAPHIC_DESIGN_PROFESSIONAL_PROJECT", "graphic-design professional project and university visual-identity field", ["institutionalization", "professionalization"], "EXISTING_GOVERNED_PAIR_ONLY", "PAIR_ONLY", ["73d9538d23a8"], "COMP-SRC-002; COMP-EVID-002; pp.185, 194.", ["R14-ASSOC-001"], "University visual-identity field and graphic designers' professional project.", "Maintain source scope and exclude design education as an unsupported third node.", "EXISTING_PAIR_SCOPE_QUALIFICATION", "RETAIN_PAIR_PATH_ONLY", ["a university client or institution is not automatically design education"])
    structural_15f = [row["trigger_occurrence_id"] for row in occurrences_by_family[FAMILY_SPECS[2]["key"]] if source_class(row).startswith("R16A_")]
    add("TBQ-013", "15f57578", "DERIVATIVE_RECONCILIATION", "RECONCILE_PRIOR_PRODUCT", "parent derivative set", "ROUND16A_DERIVATIVE_SET", "1 subgraph; 3 topologies; 9 product compositions", ["institutionalization", "design education", "professionalization"], "DERIVATIVE_RECONCILIATION_ONLY", "REMOVE_OR_INQUIRY_ONLY", [occurrence_digest(value) for value in structural_15f], "All 13 Round 16A structural descendants linked to the parent.", [], "Round 16A renderable derivatives of an unsupported unsplit parent.", "Reconcile after the parent, child, and pair-only decisions without treating structure as evidence.", "PARENT_AND_CHILD_DECISIONS; PRODUCT_RECONCILIATION", "NO_ACTIVE_TRIAD_PRODUCT", ["presentation topology is not historical semantics"])

    add("TBQ-014", "23b72032", "CONDITIONAL_SCOPED_CHILD_REVIEW", "CREATE_SCOPED_CHILD_REVIEW", "exhibition / propaganda / design diplomacy", "TURIN_INTERNATIONAL_LABOUR_EXHIBITION_1961", "Turin international labour exhibition, 1961", ["exhibition", "propaganda", "design diplomacy"], "INCIDENCE_HYPEREDGE_REVIEW", "DIRECT_OR_COHERENT_COMPOSITE_CANDIDATE_NOT_DECIDED", ["5edf4303c5bc"], "COMP-SRC-024; R14-EVID-005-02; R14-EVID-006-02; R14-EVID-008-01; Design Diplomacy section p.175.", [], "Turin international labour exhibition, 1961; diplomatic design and propaganda in one bounded case.", "Review exact text, rights, REVIEW-GAP-005, and REVIEW-ACT-029.", "EXACT_TEXT; RIGHTS; ROLE; SCOPE; HUMAN_REVIEW; COUNTEREVIDENCE", "NO_PRODUCT_UNTIL_REVIEW", ["diplomacy is not propaganda", "intent is not reception"])
    add("TBQ-015", "23b72032", "PAIR_OR_SCOPE_REROUTE", "REROUTE_TO_PAIR_PATH", "R14-ASSOC-005 + R14-ASSOC-006", "BRUSSELS_EXPO_1958", "Brussels Expo, 1958", ["exhibition", "propaganda", "design diplomacy"], "TWO_EDGE_PAIR_PATH_ONLY", "PAIR_PATH_ONLY", ["b4bba36c6480"], "COMP-SRC-023; R14-EVID-005-01; R14-EVID-006-01; abstract/p.123.", ["R14-ASSOC-005", "R14-ASSOC-006"], "Brussels Expo 1958; two separately governed pair claims.", "Require further exact group evidence; retain only the pair path now.", "EXISTING_PAIR_SCOPE_QUALIFICATIONS", "NO_TRIAD_PRODUCT", ["a connected two-edge path is not group coherence"])
    add("TBQ-016", "23b72032", "PAIR_OR_SCOPE_REROUTE", "REROUTE_TO_EXISTING_ARITY4", ARITY4_SWEDEN_KEY, "SWEDEN_IN_SYDNEY_1954", "Sweden in Sydney, 1954", ["exhibition", "trade", "propaganda", "design diplomacy"], "EXISTING_ARITY4_REVIEW_FAMILY", "DIRECT_ARITY4_CANDIDATE_NOT_DECIDED", [occurrence_digest(value) for value in ARITY4_SWEDEN_OCCURRENCE_IDS], "COMP-SRC-025; COMP-EVID-026; p.282.", [f"R16B-LOCAL-FAMILY:{ARITY4_SWEDEN_KEY}"], "Swedish exposition, Sydney retail venue, 1954; propaganda, goodwill, trade, national representation, designed display.", "Review the exact arity-four family; do not project subsets.", "RIGHTS; EXACT_GROUP_REVIEW; HUMAN_REVIEW; COUNTEREVIDENCE", "RECONCILE_THROUGH_ARITY4", ["no subset or pair projection from the four-node source"])
    structural_23b = [row["trigger_occurrence_id"] for row in occurrences_by_family[FAMILY_SPECS[3]["key"]] if source_class(row).startswith("R16A_")]
    add("TBQ-017", "23b72032", "DERIVATIVE_RECONCILIATION", "RECONCILE_PRIOR_PRODUCT", "parent derivative set", "ROUND16A_DERIVATIVE_SET", "4 subgraphs; 9 topologies; 27 product compositions", ["exhibition", "propaganda", "design diplomacy"], "DERIVATIVE_RECONCILIATION_ONLY", "REMOVE_OR_INQUIRY_ONLY", [occurrence_digest(value) for value in structural_23b], "All 40 Round 16A structural descendants; excludes fixtures and synthetic controls.", [], "Round 16A renderable descendants of the unsplit parent.", "Reconcile after parent, scoped-child, pair-path, and arity-four decisions.", "PARENT_CHILD_ARITY4_DECISIONS; PRODUCT_RECONCILIATION", "NO_ACTIVE_TRIAD_PRODUCT", ["fixtures and topologies are not evidence"])

    add("TBQ-018", "2770b6b6", "PARENT_CLOSE_CONTROL", "CLOSE_NO_CHILD", "R16B-LOCAL-FAMILY:2770b6b6", "EXACT_FROZEN_TRIAD", "institutionalization / canonization / professionalization", ["institutionalization", "canonization", "professionalization"], "UNSPLIT_PARENT_CONTROL", "INSUFFICIENT_EVIDENCE", ["5c167ce72b23"], "CLUSTER-HANDOFF-001.", [], "Exact triad; explicit DEFER_FLATTENING_RISK handoff.", "Close without a child because no shared three-node composition or independent cluster grammar is supported.", "FINAL_GOVERNED_PARENT_RECORD", "INELIGIBLE", ["shared authority framing is not one configuration"])

    add("TBQ-019", "3648ab4f", "PAIR_OR_SCOPE_REROUTE", "REROUTE_TO_EXISTING_ARITY4", ARITY4_SWEDEN_KEY, "SWEDEN_IN_SYDNEY_1954", "Sweden in Sydney, 1954", ["exhibition", "trade", "propaganda", "design diplomacy"], "EXISTING_ARITY4_REVIEW_FAMILY", "DIRECT_ARITY4_CANDIDATE_NOT_DECIDED", [occurrence_digest(value) for value in ARITY4_SWEDEN_OCCURRENCE_IDS], "COMP-SRC-025; COMP-EVID-026; p.282.", [f"R16B-LOCAL-FAMILY:{ARITY4_SWEDEN_KEY}"], "Swedish exposition in Sydney, 1954.", "Review the exact arity-four family; do not project the exhibition/trade/design-diplomacy subset.", "RIGHTS; EXACT_GROUP_REVIEW; HUMAN_REVIEW; COUNTEREVIDENCE", "RECONCILE_THROUGH_ARITY4", ["no exhibition/trade claim from path connectivity", "no subset projection"])
    structural_3648 = [row["trigger_occurrence_id"] for row in occurrences_by_family[FAMILY_SPECS[5]["key"]]]
    add("TBQ-020", "3648ab4f", "DERIVATIVE_RECONCILIATION", "RECONCILE_PRIOR_PRODUCT", "parent derivative set", "ROUND16A_DERIVATIVE_SET", "1 subgraph; 3 topologies; 9 product compositions", ["exhibition", "trade", "design diplomacy"], "DERIVATIVE_RECONCILIATION_ONLY", "REMOVE_OR_INQUIRY_ONLY", [occurrence_digest(value) for value in structural_3648], "All 13 linked Round 16A structural descendants.", [], "Round 16A renderable descendants of the unsplit parent.", "Reconcile against the arity-four decision.", "ARITY4_DECISION; PRODUCT_RECONCILIATION", "NO_ACTIVE_TRIAD_PRODUCT", ["no diplomatic outcome or direction"])

    add("TBQ-021", "3fab395d", "PAIR_OR_SCOPE_REROUTE", "SPLIT_LOCUS_REVIEW", "advertising / cultural transformation", "DGI_ABSTRACT_LOCUS", "DGI article abstract; twentieth-century Indonesian print design", ["advertising", "cultural transformation"], "PAIR_OR_SCOPED_CHILD_INQUIRY", "PAIR_OR_SCOPED_CHILD_INQUIRY_NOT_DECIDED", ["b240fe15d420"], "DGITRACE2026R0395; abstract portion.", [], "Twentieth-century Indonesian print design; abstract locus only.", "Resolve exact locator, rights, source-specific senses, and transformation mechanism.", "EXACT_LOCATOR; RIGHTS; SENSE; HUMAN_REVIEW; COUNTEREVIDENCE", "NO_PRODUCT_UNTIL_REVIEW", ["no automatic T0-to-T1 claim"])
    add("TBQ-022", "3fab395d", "PAIR_OR_SCOPE_REROUTE", "SPLIT_LOCUS_REVIEW", "advertising / propaganda", "DGI_INTRODUCTION_LOCUS", "DGI article introduction; printed communication", ["advertising", "propaganda"], "PAIR_OR_SCOPED_CHILD_INQUIRY", "PAIR_OR_SCOPED_CHILD_INQUIRY_NOT_DECIDED", ["b240fe15d420"], "DGITRACE2026R0395; introduction portion.", [], "Printed communication; introduction locus only.", "Resolve exact locator, rights, promotional/communication senses, and same-case scope.", "EXACT_LOCATOR; RIGHTS; SENSE; HUMAN_REVIEW; COUNTEREVIDENCE", "NO_PRODUCT_UNTIL_REVIEW", ["advertising is not generally propaganda"])
    add("TBQ-023", "3fab395d", "PARENT_CLOSE_CONTROL", "CLOSE_UNSPLIT_PARENT", "R16B-LOCAL-FAMILY:3fab395d", "ABSTRACT_TO_INTRODUCTION_UNSUPPORTED_BRIDGE", "DGI abstract-to-introduction synthesis", ["cultural transformation", "propaganda", "advertising"], "UNSPLIT_PARENT_CONTROL", "BOUNDED_SENSE_OR_SCOPE_CONFLICT", ["b240fe15d420"], "R16B-TRIGGER-OCC:b240fe15d420...; one database discovery row spanning separated loci.", [], "Abstract and introduction are distinct loci; object year remains unresolved.", "Preserve the unsupported-bridge reason and close the unsplit parent.", "FINAL_GOVERNED_PARENT_RECORD", "INELIGIBLE", ["do not bridge separated loci into a triad"])

    add("TBQ-024", "7696ac77", "PAIR_OR_SCOPE_REROUTE", "REROUTE_TO_PAIR_ONLY", "R14-ASSOC-020", "BAUHAUS_1919_CRAFT_EDUCATION", "craft / education; Bauhaus 1919 founding program", ["craft", "education"], "EXISTING_GOVERNED_PAIR_ONLY", "EXISTING_PAIR_ONLY", ["14c991561fa8"], "R14-EVID-020-01; R14-ARC-001; the linked R16 source row is vocabulary support only.", ["R14-ASSOC-020"], "Bauhaus 1919 founding program; workshop education and art/craft context.", "Maintain the pair qualifications and do not add design education as a third node.", "EXISTING_PAIR_SCOPE_QUALIFICATION", "RETAIN_PAIR_PATH_ONLY", ["vocabulary support does not add design education as a third node"])
    add("TBQ-025", "7696ac77", "PAIR_OR_SCOPE_REROUTE", "QUEUE_IDENTITY_RESOLUTION", "education versus design education", "EDUCATION_DESIGN_EDUCATION_IDENTITY", "Bauhaus/source R16-SRC-005", ["education", "design education"], "DUPLICATE_OR_SPECIALIZATION_REVIEW", "DUPLICATE_OR_SPECIALIZATION_REVIEW_NOT_DECIDED", ["14c991561fa8"], "R16-SRC-005; vocabulary-support-only supported-terms metadata.", [], "Bauhaus/source R16-SRC-005; two labels in one supported-terms field.", "Prove distinct bounded roles or resolve duplicate/specialization identity.", "RIGHTS; EXACT_SENSES; DISTINCT_ROLE_PROOF; HUMAN_REVIEW", "NO_TRIAD_PRODUCT_PENDING_IDENTITY", ["labels in one supported-terms field are not distinct participants"])

    add("TBQ-026", "83009b1d", "CONDITIONAL_SCOPED_CHILD_REVIEW", "CREATE_NEW_SENSE_CHILD", "adaptation / contact-zone negotiation NEW / rejection", "CONTACT_ZONE_NEGOTIATION_SENSE", "architectural contact zones; broad conceptual case", ["adaptation", "contact-zone negotiation NEW", "rejection"], "INCIDENCE_HYPEREDGE_REVIEW", "DIRECT_HIGHER_ORDER_SUPPORT_CANDIDATE_NOT_DECIDED", ["7ae5b18ed4ea"], "COMP-SRC-013; COMP-EVID-014; p.354 Contact Zone section.", [], "Architectural contact zones; broad conceptual case and unequal participation conditions.", "Create and govern a source-specific negotiation sense; complete REVIEW-GAP-002 and REVIEW-ACT-024.", "NEW_SENSE; RIGHTS; ROLE; SCOPE; HUMAN_REVIEW; COUNTEREVIDENCE", "NO_PRODUCT_UNTIL_REVIEW", ["alternatives are not stages", "participation is not equal or voluntary"])
    add("TBQ-027", "83009b1d", "PAIR_OR_SCOPE_REROUTE", "REROUTE_TO_PAIR_CHILD", "adaptation / cultural negotiation", "KERATON_SURAKARTA", "Keraton Surakarta", ["adaptation", "cultural negotiation"], "PAIR_ONLY", "PAIR_ONLY", ["6aad8b98c16a"], "COMP-SRC-014; COMP-EVID-015; abstract and results.", ["R14-ASSOC-013"], "Keraton Surakarta; unequal actors and one bounded adaptation/negotiation case.", "Maintain unequal-actor and case bounds; exclude rejection.", "PAIR_SCOPE; RIGHTS; HUMAN_REVIEW_IF_NEW_CHILD_IDENTITY", "RETAIN_PAIR_PATH_ONLY", ["the Keraton evidence has no rejection participant"])
    derivative_8300 = [row["trigger_occurrence_id"] for row in occurrences_by_family[FAMILY_SPECS[8]["key"]] if source_class(row).startswith("R16A_") or source_class(row) == "R16_LEGACY_PRODUCT_COMPOSITION"]
    add("TBQ-028", "83009b1d", "DERIVATIVE_RECONCILIATION", "RECONCILE_PRIOR_PRODUCT", "parent derivative set", "ROUND16_AND_ROUND16A_DERIVATIVE_SET", "4 subgraphs; 9 topologies; 27 Round 16A product compositions; 1 legacy Round 16 composition", ["adaptation", "cultural negotiation", "rejection"], "DERIVATIVE_RECONCILIATION_ONLY", "REMOVE_OR_INQUIRY_ONLY", [occurrence_digest(value) for value in derivative_8300], "All 41 product/topology/subgraph derivatives; excludes two R15 fixtures and the synthetic control.", [], "Prior products combine the current senses and may cross cases.", "Reconcile after sense split and child decisions.", "SENSE_SPLIT; CHILD_DECISIONS; PRODUCT_RECONCILIATION", "NO_ACTIVE_EXACT_TRIAD_PRODUCT", ["do not cross cases to add rejection"])

    add("TBQ-029", "9ade19c6", "CONDITIONAL_SCOPED_CHILD_REVIEW", "CREATE_OBJECT_ASSOCIATION_REVIEW", "exhibition / propaganda / advertising-as-promotion NEW", "VIENNA_1938_1939_ANTIBOLSHEVIST_POSTER", "1938-1939 NSDAP anti-Bolshevist exhibition poster; Vienna", ["exhibition", "propaganda", "advertising-as-promotion NEW"], "OBJECT_SPECIFIC_INCIDENCE_HYPEREDGE_REVIEW", "OBJECT_SPECIFIC_DIRECT_CANDIDATE_NOT_DECIDED", ["1a1ff85412c7"], "LOCTRACE2026I3172E16AA089B6; frozen database discovery locus.", [], "Vienna, 1938-1939; one NSDAP anti-Bolshevist exhibition poster.", "Complete lawful object/source review and govern a new advertising-as-promotion sense.", "LAWFUL_SOURCE_OR_VISUAL_REVIEW; RIGHTS; NEW_SENSE; HUMAN_REVIEW; COUNTEREVIDENCE", "NO_PRODUCT_UNTIL_REVIEW", ["no general equivalence among advertising, exhibition, and propaganda"])

    add("TBQ-030", "af25d1d4", "PAIR_OR_SCOPE_REROUTE", "REROUTE_TO_EXISTING_ARITY4", ARITY4_SWEDEN_KEY, "SWEDEN_IN_SYDNEY_1954", "Sweden in Sydney, 1954", ["exhibition", "trade", "propaganda", "design diplomacy"], "EXISTING_ARITY4_REVIEW_FAMILY", "DIRECT_ARITY4_CANDIDATE_NOT_DECIDED", [occurrence_digest(value) for value in ARITY4_SWEDEN_OCCURRENCE_IDS], "COMP-SRC-025; COMP-EVID-026; p.282.", [f"R16B-LOCAL-FAMILY:{ARITY4_SWEDEN_KEY}"], "Swedish exposition in Sydney, 1954.", "Review the exact arity-four family; do not project the trade/propaganda/design-diplomacy subset.", "RIGHTS; EXACT_GROUP_REVIEW; HUMAN_REVIEW; COUNTEREVIDENCE", "RECONCILE_THROUGH_ARITY4", ["the triad is not an automatic projection", "one exposition case does not generalize relation identity"])
    structural_af25 = [row["trigger_occurrence_id"] for row in occurrences_by_family[FAMILY_SPECS[10]["key"]]]
    add("TBQ-031", "af25d1d4", "DERIVATIVE_RECONCILIATION", "RECONCILE_PRIOR_PRODUCT", "parent derivative set", "ROUND16A_DERIVATIVE_SET", "4 subgraphs; 9 topologies; 27 product compositions", ["trade", "propaganda", "design diplomacy"], "DERIVATIVE_RECONCILIATION_ONLY", "REMOVE_OR_INQUIRY_ONLY", [occurrence_digest(value) for value in structural_af25], "All 40 linked Round 16A structural descendants.", [], "Round 16A renderable descendants of the unsplit parent.", "Reconcile against the arity-four decision.", "ARITY4_DECISION; PRODUCT_RECONCILIATION", "NO_ACTIVE_TRIAD_PRODUCT", ["one exposition case does not generalize relation identity"])

    add("TBQ-032", "d6dfcd4e", "CONDITIONAL_SCOPED_CHILD_REVIEW", "CREATE_NEW_SENSE_CHILD", "institutionalization / professional education or training NEW / professionalization", "PROFESSIONAL_EDUCATION_TRAINING_SENSE", "professional work, education, and training", ["institutionalization", "professional education or training NEW", "professionalization"], "INCIDENCE_HYPEREDGE_REVIEW", "DIRECT_LOCAL_ATTESTATION_INQUIRY_NOT_DECIDED", ["2e9463db546d"], "GRAM-SRC-025; GRAM-ATT-026; section preceding A neo-institutional perspective.", [], "Professional work, education, and training in an institutional professional-domain passage.", "Create and govern a professional-education/training sense and align it with design-history authority.", "NEW_SENSE; RIGHTS; DESIGN_HISTORY_ALIGNMENT; HUMAN_REVIEW; COUNTEREVIDENCE", "INQUIRY_ONLY", ["no universal direction, chronology, or Bauhaus-education substitution"])

    add("TBQ-033", "e33bd653", "PAIR_OR_SCOPE_REROUTE", "REROUTE_TO_EXISTING_ARITY4", ARITY4_SWEDEN_KEY, "SWEDEN_IN_SYDNEY_1954", "Sweden in Sydney, 1954", ["exhibition", "trade", "propaganda", "design diplomacy"], "EXISTING_ARITY4_REVIEW_FAMILY", "DIRECT_ARITY4_CANDIDATE_NOT_DECIDED", [occurrence_digest(value) for value in ARITY4_SWEDEN_OCCURRENCE_IDS], "COMP-SRC-025; COMP-EVID-026; p.282.", [f"R16B-LOCAL-FAMILY:{ARITY4_SWEDEN_KEY}"], "Swedish exposition in Sydney, 1954.", "Review the exact arity-four family; do not project the exhibition/trade/propaganda subset.", "RIGHTS; EXACT_GROUP_REVIEW; HUMAN_REVIEW; COUNTEREVIDENCE", "RECONCILE_THROUGH_ARITY4", ["the triad is not an automatic projection"])
    structural_e33 = [row["trigger_occurrence_id"] for row in occurrences_by_family[FAMILY_SPECS[12]["key"]]]
    add("TBQ-034", "e33bd653", "DERIVATIVE_RECONCILIATION", "RECONCILE_PRIOR_PRODUCT", "parent derivative set", "ROUND16A_DERIVATIVE_SET", "1 subgraph; 3 topologies; 9 product compositions", ["exhibition", "trade", "propaganda"], "DERIVATIVE_RECONCILIATION_ONLY", "REMOVE_OR_INQUIRY_ONLY", [occurrence_digest(value) for value in structural_e33], "All 13 linked Round 16A structural descendants.", [], "Round 16A renderable descendants of the unsplit parent.", "Reconcile against the arity-four decision.", "ARITY4_DECISION; PRODUCT_RECONCILIATION", "NO_ACTIVE_TRIAD_PRODUCT", ["pair path and layout are not group support"])

    add("TBQ-035", "e6b89317", "PAIR_OR_SCOPE_REROUTE", "REROUTE_TO_OBJECT_PAIR_REVIEW", "exhibition / typography", "CHICAGO_1950_STA_EXHIBITION_ANNOUNCEMENT", "Society of Typographic Arts exhibition announcement; Chicago; 1950", ["exhibition", "typography"], "OBJECT_PAIR_DISCOVERY", "OBJECT_PAIR_DISCOVERY_NOT_DECIDED", ["45410143763c"], "HISTORICALAICTRACE2026V1R0206; frozen database discovery locus.", [], "Chicago, 1950; Society of Typographic Arts exhibition announcement.", "Lawfully review the object/visual record and object-feature senses; exclude education absent evidence.", "LAWFUL_SOURCE_OR_VISUAL_REVIEW; RIGHTS; SENSE; HUMAN_REVIEW; COUNTEREVIDENCE", "NO_TRIAD_PRODUCT", ["education is only a subject tag and must be excluded absent evidence"])
    add("TBQ-036", "e6b89317", "CONDITIONAL_SCOPED_CHILD_REVIEW", "CREATE_OBJECT_TRIAD_INQUIRY", "exhibition / design-school education NEW / typography", "CHICAGO_1948_MOMENTUM_CATALOGUE", "Momentum Exhibition Catalogue; Institute of Design context; Chicago; 1948", ["exhibition", "design-school education NEW", "typography"], "OBJECT_SPECIFIC_INCIDENCE_HYPEREDGE_REVIEW", "OBJECT_SPECIFIC_INQUIRY_NOT_DECIDED", ["6e52fc0f1dbd"], "HISTORICALAICTRACE2026V1R0161; frozen database discovery locus.", [], "Chicago, 1948; Momentum Exhibition Catalogue; Institute of Design context.", "Lawfully review the record/visual, prove an educational mechanism, and govern new senses.", "LAWFUL_SOURCE_OR_VISUAL_REVIEW; RIGHTS; EDUCATIONAL_MECHANISM; NEW_SENSES; HUMAN_REVIEW; COUNTEREVIDENCE", "NO_PRODUCT_UNTIL_REVIEW", ["subject tags and discovery query do not prove education"])
    add("TBQ-037", "e6b89317", "PARENT_CLOSE_CONTROL", "CLOSE_UNSPLIT_PARENT", "R16B-LOCAL-FAMILY:e6b89317", "TWO_DISTINCT_CHICAGO_OBJECT_LOCI", "two distinct AIC object loci", ["exhibition", "education", "typography"], "UNSPLIT_PARENT_CONTROL", "BOUNDED_SENSE_OR_SCOPE_CONFLICT", ["45410143763c", "6e52fc0f1dbd"], "R16B-DB-FAMILY:e6b89317; two frozen AIC loci.", [], "Chicago 1950 and Chicago 1948; two distinct objects and incompatible current roles/senses.", "Keep the pair review and triad inquiry separate; close the unsplit current-sense parent.", "FINAL_GOVERNED_PARENT_RECORD", "INELIGIBLE", ["do not merge the two objects or current incompatible senses"])

    queue.sort(key=lambda row: row["memo_queue_ref"])
    expected_refs = [f"TBQ-{value:03d}" for value in range(1, 38)]
    if [row["memo_queue_ref"] for row in queue] != expected_refs:
        raise AssertionError("memo queue references must be exactly TBQ-001 through TBQ-037")
    expected_kinds = {
        "CONDITIONAL_SCOPED_CHILD_REVIEW": 13,
        "DERIVATIVE_RECONCILIATION": 6,
        "PAIR_OR_SCOPE_REROUTE": 13,
        "PARENT_CLOSE_CONTROL": 5,
    }
    if dict(Counter(row["queue_record_kind"] for row in queue)) != expected_kinds:
        raise AssertionError("memo queue record-kind distribution changed")
    if any(
        row["association_identity_created"] != "false"
        or row["association_active"] != "false"
        or row["pair_projection_created"] != "false"
        or not row["product_eligibility"].startswith("INELIGIBLE")
        for row in queue
    ):
        raise AssertionError("queue must remain fail closed")
    return queue


def build_artifacts() -> dict[str, bytes]:
    for relative, expected in PINNED_INPUT_SHA256.items():
        actual = sha256_file(relative)
        if actual != expected:
            raise AssertionError(f"pinned input changed: {relative}: {actual} != {expected}")

    parent_census = read_json(CENSUS_PATH)
    if parent_census["local_candidate_family_count"] != 35 or parent_census["trigger_occurrence_count"] != 359:
        raise AssertionError("checkpoint-004 census totals changed")
    if any(parent_census["closure"].values()):
        raise AssertionError("checkpoint-004 unexpectedly claims closure")

    tranche_a_receipt = read_json(TRANCHE_A_RECEIPT_PATH)
    if (
        tranche_a_receipt["status"] != "PASS_FAIL_CLOSED_TRANCHE_A"
        or tranche_a_receipt["family_count"] != 11
        or tranche_a_receipt["linked_occurrence_count"] != 112
    ):
        raise AssertionError("published tranche-A receipt boundary changed")

    taxonomy_rows = read_tsv(TAXONOMY_PATH)
    taxonomy = {row["disposition"]: row for row in taxonomy_rows}
    for spec in FAMILY_SPECS:
        row = taxonomy.get(spec["disposition"])
        if row is None:
            raise AssertionError(f"non-taxonomy parent disposition: {spec['disposition']}")
        if row["status_class"] != "FINAL_NON_SUPPORTING" or row["potentially_active"] != "false":
            raise AssertionError(f"tranche-B disposition must be final non-supporting: {spec['disposition']}")

    calibration = {row["assessment_id"]: row for row in read_tsv(CALIBRATION_PATH)}
    hard_negative = calibration.get("R14-ASSOC-026")
    if (
        hard_negative is None
        or hard_negative["hard_negative"] != "true"
        or {hard_negative["node_a"], hard_negative["node_b"]} != {"professionalization", "material displacement"}
    ):
        raise AssertionError("R14-ASSOC-026 hard-negative authority changed")

    occurrences = read_tsv(OCCURRENCE_PATH)
    families = read_tsv(FAMILY_PATH)
    occurrence_by_id = {row["trigger_occurrence_id"]: row for row in occurrences}
    family_by_key = {row["participant_set_key"]: row for row in families}
    if len(occurrence_by_id) != 359 or len(family_by_key) != 35:
        raise AssertionError("checkpoint-004 occurrence/family uniqueness changed")

    tranche_a_occurrence_ids = {row["trigger_occurrence_id"] for row in read_tsv(TRANCHE_A_OCCURRENCE_PATH)}
    tranche_a_family_keys = {row["participant_set_key"] for row in read_tsv(TRANCHE_A_FAMILY_PATH)}
    if len(tranche_a_occurrence_ids) != 112 or len(tranche_a_family_keys) != 11:
        raise AssertionError("tranche-A conservation boundary changed")

    graph = read_json(GRAPH_PATH)
    active_edge_by_labels = {
        tuple(sorted((edge["label_a"], edge["label_b"]))): edge
        for edge in graph["edges"]
    }

    selected_occurrence_ids: list[str] = []
    selected_families_by_key: dict[str, dict[str, str]] = {}
    active_pairs_by_family: dict[str, list[str]] = {}
    active_round14_by_family: dict[str, list[str]] = {}
    for spec in FAMILY_SPECS:
        family = family_by_key.get(spec["key"])
        if family is None:
            raise AssertionError(f"missing tranche-B family: {spec['key']}")
        if int(family["arity"]) != 3:
            raise AssertionError(f"tranche-B parent must remain arity three: {family['candidate_id']}")
        selected_families_by_key[spec["key"]] = family
        family_occurrence_ids = json.loads(family["trigger_occurrence_ids_json"])
        if len(family_occurrence_ids) != int(family["occurrence_count"]):
            raise AssertionError(f"family occurrence count mismatch: {family['candidate_id']}")
        selected_occurrence_ids.extend(family_occurrence_ids)
        labels = json.loads(family["canonical_labels_json"])
        edges = [
            active_edge_by_labels[pair]
            for pair in (tuple(sorted(value)) for value in itertools.combinations(labels, 2))
            if pair in active_edge_by_labels
        ]
        active_pairs_by_family[family["candidate_id"]] = sorted(edge["association_id"] for edge in edges)
        active_round14_by_family[family["candidate_id"]] = sorted(edge["round14_assessment_id"] for edge in edges)

    if len(selected_occurrence_ids) != 187 or len(set(selected_occurrence_ids)) != 187:
        raise AssertionError("tranche B must bind exactly 187 unique occurrences")
    if tranche_a_occurrence_ids.intersection(selected_occurrence_ids):
        raise AssertionError("tranche A and tranche B occurrence rows must be disjoint")
    if tranche_a_family_keys.intersection(selected_families_by_key):
        raise AssertionError("tranche A and tranche B parent families must be disjoint")

    occurrence_rows: list[dict[str, Any]] = []
    rows_by_family: dict[str, list[dict[str, Any]]] = {}
    for spec in FAMILY_SPECS:
        family = selected_families_by_key[spec["key"]]
        rows_by_family[family["candidate_id"]] = []
        for occurrence_id in json.loads(family["trigger_occurrence_ids_json"]):
            source = occurrence_by_id[occurrence_id]
            exact_class = source_class(source)
            evidence_class = generic_class(family["participant_set_key"], exact_class)
            detail, reason, use, source_text, rights = classification_policy(exact_class, evidence_class)
            upstream_ids, source_ids, locators = source_row_details(source)
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
                "exact_group_support_status": "NOT_GOVERNED_SUPPORT",
                "source_text_review_status": source_text,
                "rights_review_status": rights,
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
    source_class_counts = Counter(row["occurrence_source_class"] for row in occurrence_rows)
    generic_class_counts = Counter(row["occurrence_evidence_class"] for row in occurrence_rows)
    if dict(source_class_counts) != EXPECTED_SOURCE_CLASS_COUNTS:
        raise AssertionError(f"exact source-class counts changed: {dict(source_class_counts)}")
    if dict(generic_class_counts) != EXPECTED_GENERIC_CLASS_COUNTS:
        raise AssertionError(f"generic evidence-class counts changed: {dict(generic_class_counts)}")
    for spec in FAMILY_SPECS:
        family = selected_families_by_key[spec["key"]]
        actual = dict(Counter(row["occurrence_source_class"] for row in rows_by_family[family["candidate_id"]]))
        expected = EXPECTED_FAMILY_SOURCE_COUNTS[spec["key"][:8]]
        if actual != expected:
            raise AssertionError(f"family source-class count mismatch: {spec['key']}: {actual} != {expected}")

    queue_rows = build_queue_rows(selected_families_by_key, occurrences, active_pairs_by_family)
    queue_count_by_parent = Counter(row["parent_candidate_id"] for row in queue_rows)
    conditional_count_by_parent = Counter(
        row["parent_candidate_id"]
        for row in queue_rows
        if row["queue_record_kind"] == "CONDITIONAL_SCOPED_CHILD_REVIEW"
    )

    family_rows: list[dict[str, Any]] = []
    for spec in FAMILY_SPECS:
        family = selected_families_by_key[spec["key"]]
        linked = rows_by_family[family["candidate_id"]]
        exact_counts = Counter(row["occurrence_source_class"] for row in linked)
        generic_counts = Counter(row["occurrence_evidence_class"] for row in linked)
        review_rows = [row for row in linked if row["occurrence_evidence_class"] != "STRUCTURAL_ECHO"]
        review_input_ids = sorted({
            value
            for row in review_rows
            for value in json.loads(row["upstream_record_ids_json"])
        })
        review_locators = sorted({
            value
            for row in review_rows
            for value in json.loads(row["upstream_locators_json"])
        })
        active_pairs = active_pairs_by_family[family["candidate_id"]]
        active_round14 = active_round14_by_family[family["candidate_id"]]
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
            "occurrence_source_class_counts_json": canonical_json(dict(sorted(exact_counts.items()))),
            "occurrence_evidence_class_counts_json": canonical_json(dict(sorted(generic_counts.items()))),
            "evidence_bearing_input_count": generic_counts["EVIDENCE_BEARING_INPUT"],
            "metadata_discovery_count": generic_counts["METADATA_DISCOVERY"],
            "structural_echo_count": generic_counts["STRUCTURAL_ECHO"],
            "synthetic_control_count": generic_counts["SYNTHETIC_CONTROL"],
            "hard_negative_control_count": generic_counts["HARD_NEGATIVE_CONTROL"],
            "explicit_near_miss_count": generic_counts["EXPLICIT_NEAR_MISS"],
            "vocabulary_only_cooccurrence_count": generic_counts["VOCABULARY_ONLY_COOCCURRENCE"],
            "review_input_record_ids_json": canonical_json(review_input_ids),
            "review_locators_json": canonical_json(review_locators),
            "internal_possible_pair_count": arity * (arity - 1) // 2,
            "internal_active_pair_count": len(active_pairs),
            "internal_active_pair_ids_json": canonical_json(active_pairs),
            "internal_active_round14_assessment_ids_json": canonical_json(active_round14),
            "final_parent_disposition": spec["disposition"],
            "parent_disposition_status": "FINAL_FOR_UNSPLIT_PARENT_REVIEW_FAMILY_FAIL_CLOSED",
            "disposition_rationale": spec["rationale"],
            "scope_split_or_reroute_status": spec["scope_status"],
            "queue_record_count": queue_count_by_parent[family["candidate_id"]],
            "conditional_scoped_child_review_count": conditional_count_by_parent[family["candidate_id"]],
            "direct_group_support_status": "NO_ACTIVE_DIRECT_SUPPORT_FOR_UNSPLIT_PARENT",
            "composite_group_support_status": "NO_ACTIVE_COMPOSITE_SUPPORT_FOR_UNSPLIT_PARENT",
            "global_coherence_status": "FAIL_CLOSED_NOT_PASSED",
            "rights_review_status": "OPEN_ONLY_FOR_SEPARATE_QUEUE_REVIEWS_NO_PARENT_SUPPORT_USE",
            "source_text_review_status": "OPEN_ONLY_FOR_SEPARATE_QUEUE_REVIEWS_NO_PARENT_SUPPORT_USE",
            "human_review_status": "OPEN_FOR_ANY_ASSOCIATION_ACTIVATION",
            "counterevidence_review_status": "OPEN_FOR_ANY_ASSOCIATION_ACTIVATION",
            "association_identity_status": "NOT_CREATED_PARENT_IS_REVIEW_FAMILY_NOT_ASSOCIATION",
            "association_activation_status": "INACTIVE",
            "product_eligibility": "INELIGIBLE_UNSPLIT_PARENT_NOT_GOVERNED_ASSOCIATION",
            "pair_projection_count": 0,
            "explicit_nonclaims_json": canonical_json(spec["nonclaims"]),
        }))

    final_distribution = dict(Counter(row["final_parent_disposition"] for row in family_rows))
    expected_final_distribution = {
        "BOUNDED_SENSE_OR_SCOPE_CONFLICT": 6,
        "COOCCURRENCE_ONLY": 1,
        "HARD_NEGATIVE": 1,
        "INSUFFICIENT_EVIDENCE": 1,
        "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE": 5,
    }
    if final_distribution != expected_final_distribution:
        raise AssertionError(f"tranche-B parent distribution changed: {final_distribution}")
    if len(family_rows) != 14 or len(occurrence_rows) != 187 or len(queue_rows) != 37:
        raise AssertionError("tranche-B headline counts changed")
    if sum(int(row["linked_occurrence_count"]) for row in family_rows) != 187:
        raise AssertionError("family-to-occurrence conservation failed")
    if sum(int(row["queue_record_count"]) for row in family_rows) != 37:
        raise AssertionError("family-to-queue conservation failed")
    if any(
        row["association_activation_status"] != "INACTIVE"
        or int(row["pair_projection_count"])
        or not row["product_eligibility"].startswith("INELIGIBLE")
        for row in family_rows
    ):
        raise AssertionError("parent activation, projection, or product eligibility is forbidden")

    disposed_keys = tranche_a_family_keys | set(selected_families_by_key)
    disposed_occurrence_ids = tranche_a_occurrence_ids | set(selected_occurrence_ids)
    remaining_families = [row for row in families if row["participant_set_key"] not in disposed_keys]
    remaining_occurrence_ids = {
        occurrence_id
        for row in remaining_families
        for occurrence_id in json.loads(row["trigger_occurrence_ids_json"])
    }
    if (
        len(disposed_keys) != 25
        or len(disposed_occurrence_ids) != 299
        or len(remaining_families) != 10
        or len(remaining_occurrence_ids) != 60
        or disposed_occurrence_ids.intersection(remaining_occurrence_ids)
        or disposed_occurrence_ids | remaining_occurrence_ids != set(occurrence_by_id)
        or any(int(row["arity"]) < 4 for row in remaining_families)
    ):
        raise AssertionError("cumulative tranche-A/B coverage partition changed")

    tranche_a_distribution = Counter(row["final_parent_disposition"] for row in read_tsv(TRANCHE_A_FAMILY_PATH))
    cumulative_distribution = dict(sorted((tranche_a_distribution + Counter(final_distribution)).items()))
    expected_cumulative_distribution = {
        "BOUNDED_SENSE_OR_SCOPE_CONFLICT": 11,
        "COOCCURRENCE_ONLY": 2,
        "HARD_NEGATIVE": 1,
        "INQUIRY_ONLY_OR_UNRESOLVED": 3,
        "INSUFFICIENT_EVIDENCE": 2,
        "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE": 5,
        "TOPOLOGY_OR_ROLE_CONFLICT": 1,
    }
    if cumulative_distribution != expected_cumulative_distribution:
        raise AssertionError(f"cumulative A+B distribution changed: {cumulative_distribution}")

    instruction_reconciliation = {
        "count_mismatch_detected": True,
        "earlier_summary_claims": {
            "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE": 4,
            "BOUNDED_SENSE_OR_SCOPE_CONFLICT": 7,
        },
        "explicit_family_key_lists_and_exact_v2_rows": {
            "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE": 5,
            "BOUNDED_SENSE_OR_SCOPE_CONFLICT": 6,
        },
        "resolved_distribution": expected_final_distribution,
        "resolution_status": "FAIL_CLOSED_EXACT_LISTED_FAMILY_KEYS_AND_ROW_EVIDENCE_CONTROL",
        "semantic_effect": "No supporting disposition, association identity, activation, pair projection, product eligibility, or closure is created by resolving the arithmetic contradiction.",
    }

    input_roles = {
        OCCURRENCE_PATH: "IMMUTABLE_CHECKPOINT004_OCCURRENCE_UNIVERSE",
        FAMILY_PATH: "IMMUTABLE_CHECKPOINT004_FAMILY_UNIVERSE",
        CROSSWALK_PATH: "IMMUTABLE_PARTICIPANT_SENSE_AUTHORITY",
        CENSUS_PATH: "IMMUTABLE_CHECKPOINT004_HEADLINE_AND_CLOSURE_BOUNDARY",
        METHOD_PATH: "GOVERNED_EVIDENCE_AND_ACTIVATION_METHOD",
        TAXONOMY_PATH: "EXACT_GOVERNED_DISPOSITION_TAXONOMY",
        DATABASE_LEDGER_PATH: "FROZEN_DATABASE_DISCOVERY_OCCURRENCE_AUTHORITY",
        GRAPH_PATH: "IMMUTABLE_ROUND16A_ACTIVE_PAIR_BASELINE",
        CALIBRATION_PATH: "HARD_NEGATIVE_AND_PAIR_ASSESSMENT_AUTHORITY",
        TRANCHE_A_OCCURRENCE_PATH: "PUBLISHED_TRANCHE_A_OCCURRENCE_DISJOINTNESS_AUTHORITY",
        TRANCHE_A_FAMILY_PATH: "PUBLISHED_TRANCHE_A_PARENT_DISPOSITION_AUTHORITY",
        TRANCHE_A_RECEIPT_PATH: "PUBLISHED_TRANCHE_A_BUILD_RECEIPT",
        TRANCHE_A_GENERATOR_PATH: "PUBLISHED_TRANCHE_A_GENERATOR_SOURCE",
        GENERATOR_PATH: "DETERMINISTIC_TRANCHE_B_GENERATOR_SOURCE",
    }
    source_paths = sorted({row["source_path"] for row in occurrence_rows})
    all_input_paths = list(dict.fromkeys([
        OCCURRENCE_PATH,
        FAMILY_PATH,
        CROSSWALK_PATH,
        CENSUS_PATH,
        METHOD_PATH,
        TAXONOMY_PATH,
        DATABASE_LEDGER_PATH,
        GRAPH_PATH,
        CALIBRATION_PATH,
        TRANCHE_A_OCCURRENCE_PATH,
        TRANCHE_A_FAMILY_PATH,
        TRANCHE_A_RECEIPT_PATH,
        TRANCHE_A_GENERATOR_PATH,
        *source_paths,
        GENERATOR_PATH,
    ]))
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

    gap_specs = [
        ("GAP-017", "Ten higher-arity checkpoint-004 families remain undisposed after tranches A and B", "CLOSURE_BLOCKING", "OPEN_10_FAMILIES_60_OCCURRENCES", "Tranches A+B conserve and dispose 25 families/299 occurrences; ten arity-four-or-greater families/60 occurrences remain.", "GOVERNED_EVIDENCE_REVIEW", "Complete additive higher-arity evidence tranches and prove all 35 families have one final parent disposition."),
        ("GAP-018", "Tranche-B parent-outcome count instruction was arithmetically contradictory", "HIGH", "RESOLVED_FAIL_CLOSED_5_PAIRWISE_6_SCOPE_CONFLICT", "The prose claimed 4 pairwise and 7 scope conflicts, while its explicit keys and exact v2 rows prove 5 and 6; the discrepancy is retained in the census and receipt.", "EXACT_LISTED_KEYS_AND_ROW_AUTHORITY", "Independent verification must reproduce the exact 14-key distribution and reject either prose count as a ledger count."),
        ("GAP-019", "Thirty-seven memo queue rows are review/reconciliation controls, not association candidates", "CLOSURE_BLOCKING", "CONTROLLED_ZERO_IDENTITIES", "The queue has 13 scoped-child reviews, 13 pair/scope reroutes, six derivative reconciliations, and five parent-close controls; every row creates zero identities.", "SCOPE_SENSE_RIGHTS_AND_HUMAN_AUTHORITY", "Review queued child/reroute work separately and issue new governed identities only after all gates pass."),
        ("GAP-020", "Database discovery and structural descendants can be mistaken for group evidence", "CLOSURE_BLOCKING", "CONTROLLED_IN_TRANCHE_B_CONTINUES_GLOBALLY", "Eleven metadata discoveries and 164 structural echoes are classified row-exactly as non-support; two synthetic controls are also non-evidence.", "METHOD_AND_INDEPENDENT_VERIFIER", "Retest that metadata, topology, fixtures, and product descendants cannot activate associations."),
        ("GAP-021", "A hard-negative pair and pair-supported groups require distinct global-coherence handling", "CLOSURE_BLOCKING", "CONTROLLED_NO_PROJECTION_OR_ACTIVATION", "One hard-negative parent and five pairwise-without-group parents remain inactive; the separately governed R14-ASSOC-010 pair is retained without triad activation.", "GLOBAL_COHERENCE_AND_INCIDENCE_SEMANTICS", "Verify hard-negative, clique-invalidity, sparse-hyperedge, and no-projection controls independently."),
        ("GAP-022", "Sweden 1954 evidence belongs to an exact arity-four family", "CLOSURE_BLOCKING", "OPEN_ARITY4_89817E7A_REVIEW", "Four triad-parent queue controls reroute to 89817e7a... without projecting the arity-four source into any triad or pair.", "ARITY4_GROUP_EVIDENCE_AND_HUMAN_REVIEW", "Review the complete arity-four structure, rights, roles, scope, counterevidence, and global coherence."),
        ("GAP-023", "Product reconciliation remains unavailable for tranche B", "CLOSURE_BLOCKING", "OPEN_ZERO_PRODUCT_ELIGIBILITY", "All 14 parents and all 37 queue controls are product-ineligible; six derivative sets remain explicit reconciliation work and no runtime changed.", "PRODUCT_AND_GLOBAL_COHERENCE_AUTHORITY", "Reconcile every prior descendant only after governed association decisions; do not preserve a composition for compatibility alone."),
        ("GAP-024", "External source-text, rights, counterevidence, and design-history review remain open", "CLOSURE_BLOCKING", "OPEN", "Conditional children and reroutes retain all required gates; no active fact depends on pending review.", "LAWFUL_ACCESS_RIGHTS_AND_SCHOLARLY_REVIEW", "Complete adaptive source review and falsification in resumable evidence shards before any support decision."),
    ]
    gap_rows = [finalize_row({
        "gap_id": gap_id,
        "last_reviewed_checkpoint": "CHECKPOINT-006-TRANCHE-B",
        "gap": gap,
        "severity": severity,
        "status": status,
        "checkpoint006_tranche_b_evidence": evidence,
        "authority_dependency": dependency,
        "required_next_action": action,
    }) for gap_id, gap, severity, status, evidence, dependency, action in gap_specs]

    queue_kind_counts = dict(sorted(Counter(row["queue_record_kind"] for row in queue_rows).items()))
    census = {
        "format": "trace-round16b-evidence-disposition-tranche-b-census-v1",
        "builder_version": BUILDER_VERSION,
        "source_sha": AUTHORIZED_SOURCE_SHA,
        "source_tree": AUTHORIZED_SOURCE_TREE,
        "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
        "review_tranche": TRANCHE_ID,
        "checkpoint004_candidate_family_count": 35,
        "checkpoint004_trigger_occurrence_count": 359,
        "tranche_family_count": len(family_rows),
        "tranche_linked_occurrence_count": len(occurrence_rows),
        "occurrence_source_class_counts": dict(sorted(source_class_counts.items())),
        "occurrence_evidence_class_counts": dict(sorted(generic_class_counts.items())),
        "final_parent_disposition_counts": dict(sorted(final_distribution.items())),
        "instruction_count_reconciliation": instruction_reconciliation,
        "memo_queue_record_count": len(queue_rows),
        "memo_queue_record_kind_counts": queue_kind_counts,
        "memo_queue_association_candidate_count": 0,
        "conditional_scoped_child_review_count": queue_kind_counts["CONDITIONAL_SCOPED_CHILD_REVIEW"],
        "pair_or_scope_reroute_count": queue_kind_counts["PAIR_OR_SCOPE_REROUTE"],
        "derivative_reconciliation_count": queue_kind_counts["DERIVATIVE_RECONCILIATION"],
        "parent_close_control_count": queue_kind_counts["PARENT_CLOSE_CONTROL"],
        "internal_active_pair_count_distribution": dict(sorted(Counter(str(row["internal_active_pair_count"]) for row in family_rows).items())),
        "cumulative_tranche_a_b": {
            "disposed_family_count": len(disposed_keys),
            "disposed_occurrence_count": len(disposed_occurrence_ids),
            "final_parent_disposition_counts": cumulative_distribution,
            "remaining_undisposed_family_count": len(remaining_families),
            "remaining_undisposed_occurrence_count": len(remaining_occurrence_ids),
            "remaining_family_arity_distribution": dict(sorted(Counter(row["arity"] for row in remaining_families).items())),
        },
        "association_identity_created_count": 0,
        "association_activation_count": 0,
        "pair_projection_created_count": 0,
        "product_eligible_count": 0,
        "active_pending_review_count": 0,
        "closure": {
            "pair_association_closure": False,
            "higher_order_association_closure": False,
            "global_composition_coherence_closure": False,
            "product_association_reachability_closure": False,
            "computational_space_closure": False,
            "function3_closure": False,
        },
        "semantic_boundary": "Final dispositions apply only to fourteen unchanged arity-three parent review families. The 37 queue rows are conditional review, reroute, reconciliation, or closure controls; they are not association candidates, identities, support decisions, or product paths.",
    }

    note = f"""# Checkpoint 006 — Evidence disposition tranche B

## Boundary

This additive tranche binds published checkpoint 005 `{PARENT_CHECKPOINT_SHA}` and reviews the fourteen remaining arity-three participant-set families from the immutable checkpoint-004 v2 census. It does not edit tranche-A artifacts, create an association identity, activate an association, project a hyperedge or arity-four source into pairs or triads, change the product model, or claim closure.

All 187 linked trigger occurrences are conserved row-exactly. Their exact source classes are 11 database-discovery loci, seven evidence-bearing inputs, one explicit near-miss, one hard-negative control, two synthetic controls, one vocabulary-only co-occurrence, and 164 structural descendants. Database metadata, fixtures, subgraphs, topologies, and product records are not promoted to historical evidence.

## Final unsplit-parent decisions

The exact fourteen-key ledger yields:

- 5 `PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE`;
- 6 `BOUNDED_SENSE_OR_SCOPE_CONFLICT`;
- 1 `HARD_NEGATIVE`;
- 1 `INSUFFICIENT_EVIDENCE`;
- 1 `COOCCURRENCE_ONLY`.

An earlier summary claimed four pairwise-without-group and seven bounded-sense/scope conflicts, but it explicitly listed five pairwise family keys and only six scope-conflict keys. The exact family ledger, 187 occurrence rows, reviewer supplement, and taxonomy resolve the distribution to five and six. The contradiction is preserved machine-readably in the census and receipt. Resolution is fail-closed: every outcome is final non-supporting and no identity or activation results.

The hard-negative parent contains the governed `R14-ASSOC-026` control. `R14-ASSOC-010` remains a separately governed material-displacement/supply-chain pair; retaining that pair neither activates nor repairs the triad. The five pairwise-supported parent groups likewise remain inactive because local edges do not establish global group coherence.

## Conditional scoped-child and reroute queue

The separate 37-row memo queue contains exactly 13 conditional scoped-child reviews, 13 pair-or-scope reroutes, six derivative reconciliations, and five parent-close controls. These rows do not inflate the candidate universe: their association-candidate and created-identity counts are zero.

The queue preserves seven separate V&A object-incidence reviews; formal-design-education and Turin child reviews; DGI split loci; education/design-education identity review; a contact-zone negotiation-sense child; Keraton pair scope; a Vienna object-specific inquiry; professional-education/training sense work; two separate Chicago object paths; and four fail-closed reroutes to the exact Sweden-in-Sydney 1954 arity-four family `{ARITY4_SWEDEN_KEY}`. That four-node source is never projected into triads or pairs.

## Cumulative coverage and closure

Tranches A and B together provide final unsplit-parent dispositions for 25 of 35 checkpoint-004 families and conserve 299 of 359 trigger occurrences. The remaining ten families contain 60 occurrences and all have arity four or greater. No association or product path is active while evidence, rights, sense, scope, counterevidence, or human review remains pending.

Pair, higher-order, global-composition-coherence, product-reachability, computational-space, and Function 3 closure all remain false.
""".encode("utf-8")

    occurrence_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-occurrence-disposition-tranche-b-v1.tsv"
    family_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/family-evidence-disposition-tranche-b-v1.tsv"
    queue_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/conditional-scoped-child-reroute-queue-tranche-b-v1.tsv"
    input_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-input-manifest-tranche-b-v1.tsv"
    gap_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/recursive-gap-ledger-checkpoint006-tranche-b-v1.tsv"
    census_output = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-census-tranche-b-v1.json"
    note_output = "docs/research/trace-v49-exploration-higher-order-association-closure-round16b/10_EVIDENCE_DISPOSITION_TRANCHE_B.md"
    artifacts: dict[str, bytes] = {
        occurrence_output: tsv_bytes(OCCURRENCE_FIELDS, occurrence_rows),
        family_output: tsv_bytes(FAMILY_FIELDS, family_rows),
        queue_output: tsv_bytes(QUEUE_FIELDS, queue_rows),
        input_output: tsv_bytes(INPUT_FIELDS, input_rows),
        gap_output: tsv_bytes(GAP_FIELDS, gap_rows),
        census_output: json_bytes(census),
        note_output: note,
    }
    output_hashes = {
        path: {"bytes": len(payload), "sha256": sha256_bytes(payload)}
        for path, payload in sorted(artifacts.items())
    }
    receipt = {
        "format": "trace-round16b-evidence-disposition-tranche-b-build-receipt-v1",
        "builder_version": BUILDER_VERSION,
        "source_sha": AUTHORIZED_SOURCE_SHA,
        "source_tree": AUTHORIZED_SOURCE_TREE,
        "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
        "review_tranche": TRANCHE_ID,
        "input_count": len(input_rows),
        "input_manifest_sha256": sha256_bytes(artifacts[input_output]),
        "family_count": len(family_rows),
        "linked_occurrence_count": len(occurrence_rows),
        "occurrence_source_class_counts": dict(sorted(source_class_counts.items())),
        "occurrence_evidence_class_counts": dict(sorted(generic_class_counts.items())),
        "final_parent_disposition_counts": dict(sorted(final_distribution.items())),
        "instruction_count_reconciliation": instruction_reconciliation,
        "memo_queue_record_count": len(queue_rows),
        "memo_queue_record_kind_counts": queue_kind_counts,
        "memo_queue_association_candidate_count": 0,
        "cumulative_disposed_family_count": len(disposed_keys),
        "cumulative_disposed_occurrence_count": len(disposed_occurrence_ids),
        "remaining_undisposed_family_count": len(remaining_families),
        "remaining_undisposed_occurrence_count": len(remaining_occurrence_ids),
        "association_identity_created_count": 0,
        "association_activation_count": 0,
        "pair_projection_created_count": 0,
        "product_eligible_count": 0,
        "active_pending_review_count": 0,
        "closure_flags_true_count": 0,
        "output_count_excluding_receipt": len(artifacts),
        "output_hashes": output_hashes,
        "aggregate_output_sha256": sha256_text(canonical_json(output_hashes)),
        "status": "PASS_FAIL_CLOSED_TRANCHE_B",
    }
    artifacts["docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-build-receipt-tranche-b-v1.json"] = json_bytes(receipt)
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
    receipt_path = RAW / "evidence-disposition-build-receipt-tranche-b-v1.json"
    print(receipt_path.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
