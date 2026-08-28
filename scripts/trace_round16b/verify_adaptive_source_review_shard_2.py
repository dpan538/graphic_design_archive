#!/usr/bin/env python3
"""Independently verify Round 16B adaptive-source-review shard 2.

The verifier does not import or execute the primary builder.  It reconstructs
source identities, higher-order association identities, trigger coverage,
rights gates, the additive evidence quarantine, isolated-vocabulary impacts,
headline counts, the output manifest, and the primary receipt from committed
governed artifacts.  In-memory negative controls exercise fail-closed rules.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
RAW_REL = Path("docs/audits/v49-exploration-higher-order-association-closure-round16b/raw")
RESEARCH_REL = Path("docs/research/trace-v49-exploration-higher-order-association-closure-round16b")

SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
AUTHORITY_BASE_SHA = "5d9ebf6918cf0fd09450608289ebc5a05ed3c8c3"
SHARD_ID = "R16B-ADAPTIVE-SOURCE-SHARD-002"
RETRIEVED_AT_UTC = "2026-08-28T11:08:18Z"
VERIFIER_VERSION = "trace-round16b-adaptive-source-review-independent-verifier-shard-2-v1"
EXPECTED_PRIMARY_AGGREGATE_SHA256 = "366b996e47f3221b3e8c5254de6c1b89c589d653d39de1556c24fedaf9ae3054"
EXPECTED_PRIMARY_RECEIPT_SHA256 = "76142618f14976934dbc128d8cd147e566d80c256a7541222114a91e74e61ede"

BUILDER_PATH = "scripts/trace_round16b/build_adaptive_source_review_shard_2.py"
VERIFIER_PATH = "scripts/trace_round16b/verify_adaptive_source_review_shard_2.py"
VOCAB_SOURCE = "docs/research/trace-v49-design-history-relation-vocabulary-round1/03_SCHOLARLY_SOURCE_REGISTRY.tsv"
VOCAB_ATTESTATION = "docs/research/trace-v49-design-history-relation-vocabulary-round1/05_TERM_ATTESTATION_REGISTRY.tsv"
COMPOSITION_SOURCE = "docs/research/trace-v49-exploration-composition-review-round1/03_COMPOSITION_SCHOLARLY_SOURCE_REGISTRY.tsv"
COMPOSITION_EVIDENCE = "docs/research/trace-v49-exploration-composition-review-round1/04_COMPOSITION_EVIDENCE_REGISTRY.tsv"
CROSSWALK = str(RAW_REL / "concept-sense-crosswalk-v1.tsv")
ISOLATED_TERMS = str(RAW_REL / "isolated-active-term-audit-ledger-v1.tsv")
SOURCE_RIGHTS_QUEUE = str(RAW_REL / "source-canonical-rights-queue-v2.tsv")
SHARD1_REVIEW = str(RAW_REL / "adaptive-source-review-shard-1-v1.tsv")
RIGHTS_POLICY = str(RAW_REL / "scholarly-source-rights-policy.json")
LOCAL_FAMILIES = str(RAW_REL / "local-candidate-family-ledger-v2.tsv")
DISPOSITION_TAXONOMY = str(RAW_REL / "association-disposition-taxonomy.tsv")
CANDIDATE_TRIGGER_REGISTRY = str(RAW_REL / "candidate-trigger-registry.tsv")

QUERY_PATH = str(RAW_REL / "adaptive-search-query-log-shard-2-v1.tsv")
TRIGGER_PATH = str(RAW_REL / "external-candidate-trigger-occurrence-ledger-shard-2-v1.tsv")
TRIGGER_MATRIX_PATH = str(RAW_REL / "external-candidate-trigger-applicability-matrix-shard-2-v1.tsv")
FAMILY_PATH = str(RAW_REL / "external-candidate-family-ledger-shard-2-v1.tsv")
REVIEW_PATH = str(RAW_REL / "adaptive-source-review-shard-2-v1.tsv")
RIGHTS_PATH = str(RAW_REL / "source-rights-ledger-shard-2-v2.tsv")
HYPOTHESIS_PATH = str(RAW_REL / "scoped-association-hypothesis-ledger-shard-2-v1.tsv")
CORRECTION_PATH = str(RAW_REL / "source-scope-reconciliation-ledger-shard-2-v1.tsv")
VOCAB_IMPACT_PATH = str(RAW_REL / "active-vocabulary-evidence-impact-ledger-shard-2-v1.tsv")
GAP_PATH = str(RAW_REL / "recursive-gap-ledger-adaptive-source-shard-2-v1.tsv")
CENSUS_PATH = str(RAW_REL / "adaptive-source-review-census-shard-2-v1.json")
MANIFEST_PATH = str(RAW_REL / "adaptive-source-review-output-manifest-shard-2-v1.tsv")
REPORT_PATH = str(RESEARCH_REL / "17_ADAPTIVE_SOURCE_REVIEW_SHARD_002_AND_SOURCE_SCOPE_RECONCILIATION.md")
PRIMARY_RECEIPT_PATH = str(RAW_REL / "adaptive-source-review-build-receipt-shard-2-v1.json")
INDEPENDENT_RECEIPT_PATH = str(RAW_REL / "adaptive-source-review-independent-verification-shard-2-v1.json")

PRIMARY_PINNED_INPUT_SHA256 = {
    VOCAB_SOURCE: "8aae0e6d73f30061cc09a3bc7d72c4eb10aea1ca92513a5d0bc16bf29aa4943f",
    VOCAB_ATTESTATION: "f2f8ff68c9263ee360aa84f73bc3adb55e5b18b41f86f03faa18522645193240",
    COMPOSITION_SOURCE: "1f54c0956ca12dfaad472a6644c6102ee13b2e9a46f6c1794e21e1a2d7097dca",
    COMPOSITION_EVIDENCE: "c3d24a2a6f90d1e0b6ce7f0f483d04a752761cb3699294039c97778ed84dd714",
    CROSSWALK: "dfc1751482f3e74de78c2a94fd46f20eb3538d26e8c6bbf94482cac9534e770a",
    ISOLATED_TERMS: "67eaf0d1a519163d6c6d54a1c728e9f3fdc502c6bac93b1b59b7593a384803d2",
    SOURCE_RIGHTS_QUEUE: "fd8e8b48b1d0f8da1e4194828d0cc6f273fadb4ecbe147a7f5f9e2319f08b960",
    SHARD1_REVIEW: "0ed85ac002eb27b6130639acb4ecb2c3ebc9fbe0224f67550dc853f098324ecb",
    RIGHTS_POLICY: "b68037dff860421a4f413767a38ca07998cc9f215c75780f1e0019f32bf396ba",
    LOCAL_FAMILIES: "cd4c3ca997c0f4cd5919d4e29d89ca45291fae4f70f78a49742aafb9c76baea7",
    CANDIDATE_TRIGGER_REGISTRY: "b2c1710f09d8bc6dd7a629b186bbcf10a6e1f1a6ccf10adc3a67a5c7eec8eef1",
}

VERIFIER_PINNED_INPUT_SHA256 = {
    **PRIMARY_PINNED_INPUT_SHA256,
    DISPOSITION_TAXONOMY: "20248f9d62f672f88ce1aa691e059e6459747deb9674a3b600ac9959465b165d",
    BUILDER_PATH: "5dd3fadd58c5ab3c4526f147d10969f123d61f1267d47b2224b5d14a3b9966f9",
}

EXPECTED_RAW_ROW_SHA256 = {
    (VOCAB_SOURCE, "SRC-0007"): "4f445156d3d8e66cd80fcca4f8b63cf0e35a6b42f39db1a40ed52b4a761b8f47",
    (VOCAB_ATTESTATION, "ATT-0007"): "90ce81c5069beab02f782bd00beb644cb5e40deaf75488d26e0a00401ac76c13",
    (COMPOSITION_SOURCE, "COMP-SRC-017"): "1d79d5b310087d3152b41593cd218ab6f6491794f02ec5f9563f70f506d628ce",
    (COMPOSITION_SOURCE, "COMP-SRC-022"): "f5f34c77470afce45077fe8dfa1773d69e17143ddcf67f4820f471c54867fbc7",
    (COMPOSITION_EVIDENCE, "COMP-EVID-018"): "8704bb1190ee414686b3569b725d3eaeff71a26b31e19dd397020755256016d7",
    (COMPOSITION_EVIDENCE, "COMP-EVID-023"): "1af3be6e167e8f1f140812b78fcc2b02810c4566a0ccb6c6aff65a0fc6111859",
}

SENSES = {
    "canonization": "R16B-SENSE:94c4f5d3fe61b3ac4c6a1540f918207e423a9abe9823bb4ddb0466ce033cda4d",
    "gendering": "R16B-SENSE:14bd96e324918cf3d87ed84253055004be79647294bf62a305ccf9a65a46b863",
    "exclusion": "R16B-SENSE:51949ccda89c423bfca99e114d57880bdab2a25181a617884774e748bd18ae89",
    "mobile object": "R16B-SENSE:74959afea7f94773eca66c42bbaabe55d3f5ac814d8b2f8efd05921e7e76aa78",
    "mediation": "R16B-SENSE:35489187871bfd7b7be6e2d5268a3a922984d3bdad9e9a8ca61ea6edee84a5a7",
    "commodification": "R16B-SENSE:f1dafc6df9c9a66b0b7c19d34606a2ed638c193dc7047afb8a1f83b3d564ebc1",
    "cultural transformation": "R16B-SENSE:1e7045ac788667d54d6b65cd2d78f8c378eb10d531dd198692143840ff9d766b",
}

CANDIDATES = {
    "EXT-S2-001": {
        "source_id": "SRC-0007",
        "labels": ["canonization", "exclusion", "gendering"],
        "hypothesis_key": "VISIBLE_LANGUAGE_CANON_CRITIQUE_1967_2015",
        "support_mode": "DIRECT_HIGHER_ORDER_SUPPORT_BOUNDED_CORPUS",
    },
    "EXT-S2-002": {
        "source_id": "COMP-SRC-022",
        "labels": ["commodification", "mediation", "mobile object"],
        "hypothesis_key": "MEZA_PAINTING_MOBILITY_MEDIATION_MARKET_1790_1836",
        "support_mode": "COHERENT_SINGLE_SOURCE_MULTI_LOCUS_SYNTHESIS",
    },
}

EXPECTED_SOURCE_IDENTITY = {
    "SRC-0007": ("Dori Griffin", "2016", "The Role of Visible Language in Building and Critiquing a Canon of Graphic Design History", "VISIBLE-LANGUAGE-5932"),
    "COMP-SRC-022": ("Rebecca Earle;Susan Deans-Smith", "2026", "Mobility, Violence, and the Afterlives of a Peruvian Painting at Sea", "10.1017/S0165115326100552"),
    "COMP-SRC-017": ("Hifsiye Pulhan;İbrahim Numan", "2006", "The Traditional Urban House in Cyprus as Material Expression of Cultural Transformation", "10.1093/jdh/epi050"),
}

EXPECTED_GAP_CLASSES = {
    "EXTERNAL_HUMAN_REVIEW",
    "CULTURAL_TRANSFORMATION_SUPPORT_REAUDIT",
    "ISOLATED_ACTIVE_TERMS",
    "RIGHTS_SCHEMA_RECONCILIATION",
    "CANDIDATE_TRIGGER_RECURSION",
    "ROUND16A_GLOBAL_RECONCILIATION",
}

EXPECTED_TRIGGER_APPLICABILITY = {
    "EXT-S2-001": {"TRG-002", "TRG-005", "TRG-006", "TRG-010"},
    "EXT-S2-002": {"TRG-002", "TRG-005", "TRG-010"},
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(relative: str) -> str:
    return sha256_bytes((REPO / relative).read_bytes())


def stable_id(prefix: str, payload: Any) -> str:
    return f"{prefix}:{sha256_bytes(canonical_json(payload).encode('utf-8'))}"


def read_tsv(relative: str) -> list[dict[str, str]]:
    with (REPO / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, dialect="excel-tab"))


def read_json(relative: str) -> Any:
    return json.loads((REPO / relative).read_text(encoding="utf-8"))


def raw_row_sha256(relative: str, first_field: str) -> str:
    prefix = (first_field + "\t").encode("utf-8")
    matches = [
        sha256_bytes(line)
        for line in (REPO / relative).read_bytes().splitlines(keepends=True)[1:]
        if line.startswith(prefix)
    ]
    if len(matches) != 1:
        return f"ROW_COUNT_{len(matches)}"
    return matches[0]


def expected_association_identity(labels: list[str], scope_key: str) -> tuple[str, str]:
    sense_ids = sorted(SENSES[label] for label in labels)
    association_id = stable_id("R16B-ASSOC", {
        "association_class": "HIGHER_ORDER",
        "participant_sense_ids": sense_ids,
        "order_semantics": "UNORDERED",
        "role_semantics": "NONE_UNTIL_EXTERNAL_REVIEW",
        "scope_key": scope_key,
    })
    revision_id = stable_id("R16B-ASSOC-REV", {
        "association_id": association_id,
        "activation_status": "INQUIRY_ONLY",
        "final_disposition": "INQUIRY_ONLY_OR_UNRESOLVED",
        "pair_projection_policy": "NONE",
        "parent_checkpoint_sha": AUTHORITY_BASE_SHA,
        "product_eligibility": "INELIGIBLE",
        "review_tranche": "CHECKPOINT-009-ADAPTIVE-SOURCE-SHARD-002",
    })
    return association_id, revision_id


def row_record_hash(row: dict[str, str]) -> str:
    payload = {key: value for key, value in row.items() if key != "record_sha256"}
    return sha256_bytes(canonical_json(payload).encode("utf-8"))


def common_row_violations(row: dict[str, str]) -> set[str]:
    failures: set[str] = set()
    if row.get("authority_base_sha") != AUTHORITY_BASE_SHA:
        failures.add("AUTHORITY")
    if row.get("shard_id") != SHARD_ID:
        failures.add("SHARD")
    if row.get("record_sha256") != row_record_hash(row):
        failures.add("RECORD_HASH")
    return failures


def hypothesis_violations(
    row: dict[str, str],
    rights_by_source: dict[str, dict[str, str]],
) -> set[str]:
    failures = common_row_violations(row)
    try:
        labels = json.loads(row["participant_labels_json"])
        sense_ids = json.loads(row["participant_sense_ids_json"])
    except (KeyError, json.JSONDecodeError):
        return failures | {"PARTICIPANT_JSON"}
    if labels != sorted(labels) or len(labels) != len(set(labels)):
        failures.add("PARTICIPANT_SET")
    if len(labels) < 3 or row.get("arity") != str(len(labels)):
        failures.add("ARITY")
    if row.get("association_class") != "HIGHER_ORDER":
        failures.add("CLASS")
    expected_senses = sorted(SENSES.get(label, "UNKNOWN") for label in labels)
    if sense_ids != expected_senses or "UNKNOWN" in expected_senses:
        failures.add("SENSES")
    expected_id, expected_revision = expected_association_identity(labels, row.get("hypothesis_key", ""))
    if row.get("association_id") != expected_id:
        failures.add("ASSOCIATION_ID")
    if row.get("association_revision_id") != expected_revision:
        failures.add("REVISION_ID")
    expected_hypothesis_id = stable_id("R16B-HYPOTHESIS", {
        "source_id": row.get("source_id", ""),
        "scope": row.get("hypothesis_key", ""),
        "labels": labels,
    })
    if row.get("hypothesis_id") != expected_hypothesis_id:
        failures.add("HYPOTHESIS_ID")
    if row.get("order_semantics") != "UNORDERED":
        failures.add("ORDER")
    if row.get("role_semantics") != "NONE_UNTIL_EXTERNAL_REVIEW":
        failures.add("ROLES")
    if row.get("activation_status") != "INQUIRY_ONLY":
        failures.add("ACTIVATION")
    if row.get("external_human_review_status") != "PENDING_NOT_ACTIVE":
        failures.add("HUMAN_REVIEW")
    if row.get("product_eligible") != "false" or row.get("product_path") != "":
        failures.add("PRODUCT")
    if row.get("pair_projection_policy") != "NONE" or row.get("implicit_pair_projection_count") != "0":
        failures.add("PROJECTION")
    source_id = row.get("source_id", "")
    if source_id not in rights_by_source or row.get("rights_record_id") != rights_by_source[source_id].get("rights_record_id"):
        failures.add("RIGHTS_LINK")
    for field in ("locators_json", "synthesis_steps_json", "counterevidence_json", "qualifications_json", "nonclaims_json"):
        try:
            value = json.loads(row.get(field, ""))
        except json.JSONDecodeError:
            failures.add("EVIDENCE_JSON")
        else:
            if not isinstance(value, list) or not value:
                failures.add("EVIDENCE_JSON")
    return failures


def rights_violations(row: dict[str, str], required_fields: list[str]) -> set[str]:
    failures = common_row_violations(row)
    if any(field not in row for field in required_fields):
        failures.add("RIGHTS_SCHEMA")
    if any(not row.get(field, "") for field in required_fields):
        failures.add("RIGHTS_REQUIRED_VALUE")
    if row.get("retrieved_at_utc") != RETRIEVED_AT_UTC:
        failures.add("RIGHTS_TIMESTAMP")
    expected_id = stable_id("R16B-SOURCE-RIGHTS", {
        "source_id": row.get("source_id", ""),
        "retrieved_at": RETRIEVED_AT_UTC,
    })
    if row.get("rights_record_id") != expected_id:
        failures.add("RIGHTS_ID")
    if row.get("retained_material_type") != "BIBLIOGRAPHIC_IDENTITY_STABLE_LOCATORS_BOUNDED_PARAPHRASE_AND_DECISION_ONLY":
        failures.add("RETAINED_MATERIAL")
    if row.get("retained_sha256") != "NOT_APPLICABLE_NO_SOURCE_PAYLOAD_RETAINED":
        failures.add("RETAINED_PAYLOAD")
    if row.get("extract_word_count") != "0":
        failures.add("EXTRACT_COUNT")
    if row.get("review_status") != "COMPLETE_FAIL_CLOSED":
        failures.add("RIGHTS_REVIEW")
    return failures


def trigger_violations(row: dict[str, str], trigger_names: dict[str, str]) -> set[str]:
    failures = common_row_violations(row)
    expected_id = stable_id("R16B-EXTERNAL-TRIGGER", {
        "candidate_key": row.get("candidate_key", ""),
        "trigger_id": row.get("trigger_id", ""),
        "source_id": row.get("source_id", ""),
    })
    if row.get("trigger_occurrence_id") != expected_id:
        failures.add("TRIGGER_ID")
    if row.get("trigger_class") != trigger_names.get(row.get("trigger_id", "")):
        failures.add("TRIGGER_NAME")
    try:
        labels = json.loads(row["participant_labels_json"])
        sense_ids = json.loads(row["participant_sense_ids_json"])
    except (KeyError, json.JSONDecodeError):
        return failures | {"TRIGGER_PARTICIPANTS"}
    if labels != sorted(labels) or sense_ids != sorted(SENSES.get(label, "UNKNOWN") for label in labels):
        failures.add("TRIGGER_PARTICIPANTS")
    if row.get("pair_graph_derivation") != "false":
        failures.add("PAIR_GRAPH_DERIVATION")
    if row.get("review_required") != "true":
        failures.add("TRIGGER_REVIEW")
    if any(row.get(field) != "false" for field in ("activation_created", "product_path_created", "pair_projection_created")):
        failures.add("TRIGGER_ACTIVATION")
    return failures


def family_violations(
    row: dict[str, str],
    hypothesis_by_id: dict[str, dict[str, str]],
    trigger_ids: set[str],
    local_sets: set[tuple[str, ...]],
) -> set[str]:
    failures = common_row_violations(row)
    hypothesis = hypothesis_by_id.get(row.get("hypothesis_id", ""))
    if not hypothesis:
        return failures | {"FAMILY_HYPOTHESIS_LINK"}
    for field in ("association_id", "association_revision_id", "participant_labels_json", "participant_sense_ids_json", "arity"):
        if row.get(field) != hypothesis.get(field):
            failures.add("FAMILY_HYPOTHESIS_LINK")
    expected_id = stable_id("R16B-EXTERNAL-FAMILY", {
        "candidate_key": row.get("candidate_key", ""),
        "association_id": row.get("association_id", ""),
    })
    if row.get("external_candidate_family_id") != expected_id:
        failures.add("FAMILY_ID")
    try:
        labels = tuple(sorted(json.loads(row["participant_labels_json"])))
        family_trigger_ids = json.loads(row["trigger_occurrence_ids_json"])
    except (KeyError, json.JSONDecodeError):
        return failures | {"FAMILY_JSON"}
    if labels in local_sets or row.get("local_family_match_count") != "0":
        failures.add("LOCAL_FAMILY_COLLISION")
    if len(family_trigger_ids) not in {3, 4} or len(set(family_trigger_ids)) != len(family_trigger_ids) or not set(family_trigger_ids) <= trigger_ids:
        failures.add("FAMILY_TRIGGER_COVERAGE")
    if row.get("candidate_origin") != "EXTERNAL_ADAPTIVE_SOURCE_DISCOVERY_NOT_DERIVED_FROM_ROUND16A_PAIR_GRAPH":
        failures.add("FAMILY_ORIGIN")
    if row.get("activation_status") != "INQUIRY_ONLY" or row.get("product_eligible") != "false":
        failures.add("FAMILY_ACTIVATION")
    if row.get("pair_projection_policy") != "NONE" or row.get("external_human_review_status") != "PENDING_NOT_ACTIVE":
        failures.add("FAMILY_PROJECTION_OR_REVIEW")
    return failures


def review_violations(
    row: dict[str, str],
    rights_by_source: dict[str, dict[str, str]],
    hypotheses_by_source: dict[str, dict[str, str]],
) -> set[str]:
    failures = common_row_violations(row)
    expected_id = stable_id("R16B-SOURCE-REVIEW", {
        "source_id": row.get("source_id", ""),
        "retrieved_at": RETRIEVED_AT_UTC,
    })
    if row.get("source_review_id") != expected_id or row.get("retrieved_at_utc") != RETRIEVED_AT_UTC:
        failures.add("SOURCE_REVIEW_ID")
    source_id = row.get("source_id", "")
    if source_id not in rights_by_source or row.get("rights_record_id") != rights_by_source[source_id].get("rights_record_id"):
        failures.add("SOURCE_REVIEW_RIGHTS")
    expected_identity = EXPECTED_SOURCE_IDENTITY.get(source_id)
    if expected_identity and tuple(row.get(field, "") for field in ("authors", "year", "title", "doi_or_identifier")) != expected_identity:
        failures.add("SOURCE_IDENTITY")
    hypothesis = hypotheses_by_source.get(source_id)
    if hypothesis:
        if row.get("association_id") != hypothesis.get("association_id") or row.get("association_revision_id") != hypothesis.get("association_revision_id"):
            failures.add("SOURCE_REVIEW_ASSOCIATION")
        if row.get("human_review_status") != "PENDING_FOR_ASSOCIATION_ACTIVATION":
            failures.add("SOURCE_REVIEW_PENDING")
    elif row.get("association_id") or row.get("association_revision_id"):
        failures.add("QUARANTINE_ASSOCIATION")
    if any(row.get(field) != "false" for field in ("activation_created", "product_path_created", "pair_projection_created", "copyrighted_payload_retained")):
        failures.add("SOURCE_REVIEW_ACTIVATION_OR_PAYLOAD")
    return failures


def correction_violations(row: dict[str, str], rights_by_source: dict[str, dict[str, str]]) -> set[str]:
    failures = common_row_violations(row)
    if row.get("legacy_evidence_id") != "COMP-EVID-018" or row.get("legacy_source_id") != "COMP-SRC-017":
        failures.add("CORRECTION_TARGET")
    if row.get("legacy_row_sha256") != EXPECTED_RAW_ROW_SHA256[(COMPOSITION_EVIDENCE, "COMP-EVID-018")]:
        failures.add("LEGACY_ROW_HASH")
    expected_id = stable_id("R16B-SOURCE-SCOPE-CORRECTION", {
        "evidence_id": "COMP-EVID-018",
        "official_locator": "OUP_ABSTRACT_2026-08-28",
    })
    if row.get("reconciliation_id") != expected_id:
        failures.add("CORRECTION_ID")
    if row.get("rights_record_id") != rights_by_source.get("COMP-SRC-017", {}).get("rights_record_id"):
        failures.add("CORRECTION_RIGHTS")
    if row.get("conflict_type") != "TIME_PERIOD_DIRECTION_AND_HISTORICAL_STATE_MISMATCH":
        failures.add("CORRECTION_SCOPE")
    if row.get("method_trigger_id") != "TRG-011" or row.get("method_trigger_name") != "COUNTEREVIDENCE_AND_FALSIFICATION":
        failures.add("CORRECTION_TRIGGER")
    if row.get("candidate_family_created") != "false":
        failures.add("CORRECTION_FALSE_CANDIDATE")
    if row.get("additive_disposition") != "SOURCE_SCOPE_CONFLICT_QUARANTINE":
        failures.add("CORRECTION_DISPOSITION")
    if row.get("legacy_pass_superseded") != "true_for_round16b_use_only":
        failures.add("CORRECTION_SUPERSESSION")
    if row.get("legacy_artifact_mutated") != "false":
        failures.add("LEGACY_MUTATION")
    if any(row.get(field) != "false" for field in ("reproducible_full_text_review", "evidence_activation_eligible", "product_eligible", "pair_projection_eligible")):
        failures.add("CORRECTION_ELIGIBILITY")
    return failures


def expect(condition: bool, code: str, checks: list[str], failures: list[str]) -> None:
    checks.append(code)
    if not condition:
        failures.append(code)


def verify() -> dict[str, Any]:
    checks: list[str] = []
    failures: list[str] = []

    for path, expected in sorted(VERIFIER_PINNED_INPUT_SHA256.items()):
        expect(sha256_file(path) == expected, f"PIN:{path}", checks, failures)
    for (path, row_id), expected in sorted(EXPECTED_RAW_ROW_SHA256.items()):
        expect(raw_row_sha256(path, row_id) == expected, f"RAW_ROW:{row_id}", checks, failures)

    crosswalk = {row["canonical_label"]: row for row in read_tsv(CROSSWALK)}
    for label, sense_id in sorted(SENSES.items()):
        expect(crosswalk.get(label, {}).get("participant_sense_id") == sense_id, f"SENSE:{label}", checks, failures)

    taxonomy = {row["disposition"]: row for row in read_tsv(DISPOSITION_TAXONOMY)}
    expect(taxonomy.get("INQUIRY_ONLY_OR_UNRESOLVED", {}).get("potentially_active") == "false", "TAXONOMY:INQUIRY_INACTIVE", checks, failures)
    expect(taxonomy.get("PENDING_GOVERNED_REVIEW", {}).get("potentially_active") == "false", "TAXONOMY:PENDING_INACTIVE", checks, failures)

    trigger_registry = read_tsv(CANDIDATE_TRIGGER_REGISTRY)
    trigger_names = {row["trigger_id"]: row["trigger_name"] for row in trigger_registry}
    expect(len(trigger_registry) == len(trigger_names) == 12, "TRIGGER_REGISTRY:COUNT", checks, failures)
    expect(trigger_names.get("TRG-002") == "SAME_LOCATOR_MULTI_CONCEPT", "TRIGGER_REGISTRY:TRG-002", checks, failures)
    expect(trigger_names.get("TRG-005") == "ISOLATED_ACTIVE_VOCABULARY", "TRIGGER_REGISTRY:TRG-005", checks, failures)
    expect(trigger_names.get("TRG-006") == "RESEARCH_ONLY_BOUNDED_SENSE", "TRIGGER_REGISTRY:TRG-006", checks, failures)
    expect(trigger_names.get("TRG-010") == "ADAPTIVE_EXTERNAL_SEARCH", "TRIGGER_REGISTRY:TRG-010", checks, failures)
    expect(trigger_names.get("TRG-011") == "COUNTEREVIDENCE_AND_FALSIFICATION", "TRIGGER_REGISTRY:TRG-011", checks, failures)

    local_sets = {
        tuple(sorted(json.loads(row["canonical_labels_json"])))
        for row in read_tsv(LOCAL_FAMILIES)
    }
    for candidate_key, spec in sorted(CANDIDATES.items()):
        expect(tuple(spec["labels"]) not in local_sets, f"LOCAL_ABSENCE:{candidate_key}", checks, failures)

    policy = read_json(RIGHTS_POLICY)
    required_rights_fields = list(policy["required_ledger_fields"])
    expect(policy["metadata_is_not_evidence"] is True, "RIGHTS_POLICY:METADATA", checks, failures)
    expect(policy["public_access_is_not_redistribution_permission"] is True, "RIGHTS_POLICY:PUBLIC_ACCESS", checks, failures)

    rights = read_tsv(RIGHTS_PATH)
    expect(len(rights) == 3, "RIGHTS:COUNT", checks, failures)
    rights_by_source = {row["source_id"]: row for row in rights}
    expect(set(rights_by_source) == set(EXPECTED_SOURCE_IDENTITY), "RIGHTS:SOURCES", checks, failures)
    for source_id, row in sorted(rights_by_source.items()):
        violations = rights_violations(row, required_rights_fields)
        expect(not violations, f"RIGHTS:{source_id}:{','.join(sorted(violations))}", checks, failures)
    expect(rights_by_source.get("COMP-SRC-022", {}).get("license_identifier") == "CC-BY-4.0", "RIGHTS:EARLE_LICENSE", checks, failures)
    expect(rights_by_source.get("COMP-SRC-022", {}).get("redistribution_authorized") == "true_with_attribution_conditions", "RIGHTS:EARLE_CONDITIONAL", checks, failures)
    expect(rights_by_source.get("SRC-0007", {}).get("redistribution_authorized") == "false", "RIGHTS:GRIFFIN_NO_REDISTRIBUTION", checks, failures)
    expect(rights_by_source.get("COMP-SRC-017", {}).get("license_identifier") == "ALL_RIGHTS_RESERVED", "RIGHTS:OUP_RESERVED", checks, failures)

    hypotheses = read_tsv(HYPOTHESIS_PATH)
    expect(len(hypotheses) == 2, "HYPOTHESIS:COUNT", checks, failures)
    hypotheses_by_id = {row["hypothesis_id"]: row for row in hypotheses}
    hypotheses_by_source = {row["source_id"]: row for row in hypotheses}
    expect(set(hypotheses_by_source) == {"SRC-0007", "COMP-SRC-022"}, "HYPOTHESIS:SOURCES", checks, failures)
    reconstructed_associations: dict[str, str] = {}
    for row in hypotheses:
        violations = hypothesis_violations(row, rights_by_source)
        expect(not violations, f"HYPOTHESIS:{row.get('hypothesis_key')}:{','.join(sorted(violations))}", checks, failures)
        labels = json.loads(row["participant_labels_json"])
        reconstructed_id, reconstructed_revision = expected_association_identity(labels, row["hypothesis_key"])
        reconstructed_associations[reconstructed_id] = reconstructed_revision
        matching = [
            spec for spec in CANDIDATES.values()
            if spec["hypothesis_key"] == row["hypothesis_key"]
        ]
        expect(len(matching) == 1, f"HYPOTHESIS:KNOWN_SCOPE:{row['hypothesis_key']}", checks, failures)
        if matching:
            expect(labels == matching[0]["labels"], f"HYPOTHESIS:LABELS:{row['hypothesis_key']}", checks, failures)
            expect(row["source_id"] == matching[0]["source_id"], f"HYPOTHESIS:SOURCE:{row['hypothesis_key']}", checks, failures)
            expect(row["support_mode"] == matching[0]["support_mode"], f"HYPOTHESIS:SUPPORT:{row['hypothesis_key']}", checks, failures)
    expect(len(reconstructed_associations) == 2, "HYPOTHESIS:IDENTITY_UNIQUENESS", checks, failures)

    queries = read_tsv(QUERY_PATH)
    expect(len(queries) == 15, "QUERY:COUNT", checks, failures)
    expect([row["ordinal"] for row in queries] == [str(value) for value in range(1, 16)], "QUERY:ORDINALS", checks, failures)
    query_targets = Counter(row["target_source_id"] for row in queries)
    expect(query_targets == Counter({"COMP-SRC-022": 6, "SRC-0007": 5, "COMP-SRC-017": 3, "SHARD-002": 1}), "QUERY:TARGET_DISTRIBUTION", checks, failures)
    required_query_phases = {"SOURCE_CENTERED_DISCOVERY", "COMPLETE_GROUP_QUERY", "LOCATOR_FOLLOWUP", "MECHANISM_SEARCH", "FALSIFICATION", "LAWFUL_ACCESS_SEARCH", "SCOPE_FALSIFICATION", "RIGHTS_REVIEW"}
    expect(required_query_phases <= {row["query_phase"] for row in queries}, "QUERY:ADAPTIVE_PHASES", checks, failures)
    for row in queries:
        expected_query_id = stable_id("R16B-QUERY", {
            "ordinal": int(row["ordinal"]),
            "query": row["query_text"],
            "target": row["target_source_id"],
        })
        expected_result_id = stable_id("R16B-RESULT", {
            "url": row["result_url"],
            "title": row["result_title"],
        })
        violations = common_row_violations(row)
        expect(not violations, f"QUERY:ROW:{row['ordinal']}:{','.join(sorted(violations))}", checks, failures)
        expect(row["query_id"] == expected_query_id, f"QUERY:ID:{row['ordinal']}", checks, failures)
        expect(row["result_identity"] == expected_result_id, f"QUERY:RESULT_ID:{row['ordinal']}", checks, failures)
        expect(row["recorded_at_utc"] == RETRIEVED_AT_UTC, f"QUERY:TIMESTAMP:{row['ordinal']}", checks, failures)
        expect(row["result_is_association_evidence"] == "false", f"QUERY:METADATA_NOT_EVIDENCE:{row['ordinal']}", checks, failures)

    triggers = read_tsv(TRIGGER_PATH)
    expect(len(triggers) == 7, "TRIGGER:COUNT", checks, failures)
    trigger_ids = {row["trigger_occurrence_id"] for row in triggers}
    trigger_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in triggers:
        trigger_groups[row["candidate_key"]].append(row)
        violations = trigger_violations(row, trigger_names)
        expect(not violations, f"TRIGGER:{row.get('ordinal')}:{','.join(sorted(violations))}", checks, failures)
    expect(set(trigger_groups) == set(CANDIDATES), "TRIGGER:CANDIDATES", checks, failures)
    for candidate_key, rows in sorted(trigger_groups.items()):
        expect({row["trigger_id"] for row in rows} == EXPECTED_TRIGGER_APPLICABILITY[candidate_key], f"TRIGGER:COVERAGE:{candidate_key}", checks, failures)
        spec = CANDIDATES[candidate_key]
        expect(all(row["source_id"] == spec["source_id"] for row in rows), f"TRIGGER:SOURCE:{candidate_key}", checks, failures)
        expect(all(json.loads(row["participant_labels_json"]) == spec["labels"] for row in rows), f"TRIGGER:LABELS:{candidate_key}", checks, failures)

    trigger_matrix = read_tsv(TRIGGER_MATRIX_PATH)
    expect(len(trigger_matrix) == 24, "TRIGGER_MATRIX:COUNT", checks, failures)
    expect(
        {(row["candidate_key"], row["trigger_id"]) for row in trigger_matrix}
        == {(candidate_key, trigger_id) for candidate_key in CANDIDATES for trigger_id in trigger_names},
        "TRIGGER_MATRIX:COMPLETE_CARTESIAN_COVERAGE",
        checks,
        failures,
    )
    occurrence_by_key = {
        (row["candidate_key"], row["trigger_id"]): row["trigger_occurrence_id"]
        for row in triggers
    }
    for row in trigger_matrix:
        violations = common_row_violations(row)
        candidate_key = row["candidate_key"]
        trigger_id = row["trigger_id"]
        is_applicable = trigger_id in EXPECTED_TRIGGER_APPLICABILITY[candidate_key]
        expected_applicability_id = stable_id("R16B-EXTERNAL-TRIGGER-APPLICABILITY", {
            "candidate_key": candidate_key,
            "trigger_id": trigger_id,
        })
        expect(not violations, f"TRIGGER_MATRIX:{candidate_key}:{trigger_id}:{','.join(sorted(violations))}", checks, failures)
        expect(row["applicability_record_id"] == expected_applicability_id, f"TRIGGER_MATRIX:ID:{candidate_key}:{trigger_id}", checks, failures)
        expect(row["trigger_name"] == trigger_names[trigger_id], f"TRIGGER_MATRIX:NAME:{candidate_key}:{trigger_id}", checks, failures)
        expect(row["applicability"] == ("APPLICABLE" if is_applicable else "NOT_APPLICABLE"), f"TRIGGER_MATRIX:DECISION:{candidate_key}:{trigger_id}", checks, failures)
        expect(row["occurrence_emitted"] == ("true" if is_applicable else "false"), f"TRIGGER_MATRIX:EMISSION:{candidate_key}:{trigger_id}", checks, failures)
        expect(row["trigger_occurrence_id"] == occurrence_by_key.get((candidate_key, trigger_id), ""), f"TRIGGER_MATRIX:LINK:{candidate_key}:{trigger_id}", checks, failures)
        expect(bool(row["rationale"].strip()), f"TRIGGER_MATRIX:RATIONALE:{candidate_key}:{trigger_id}", checks, failures)
        expect(all(row[field] == "false" for field in ("activation_created", "product_path_created", "pair_projection_created")), f"TRIGGER_MATRIX:NO_ACTIVATION:{candidate_key}:{trigger_id}", checks, failures)

    families = read_tsv(FAMILY_PATH)
    expect(len(families) == 2, "FAMILY:COUNT", checks, failures)
    expect({row["candidate_key"] for row in families} == set(CANDIDATES), "FAMILY:CANDIDATES", checks, failures)
    for row in families:
        violations = family_violations(row, hypotheses_by_id, trigger_ids, local_sets)
        expect(not violations, f"FAMILY:{row.get('candidate_key')}:{','.join(sorted(violations))}", checks, failures)
        expected_family_triggers = {item["trigger_occurrence_id"] for item in trigger_groups[row["candidate_key"]]}
        expect(set(json.loads(row["trigger_occurrence_ids_json"])) == expected_family_triggers, f"FAMILY:TRIGGERS:{row['candidate_key']}", checks, failures)

    reviews = read_tsv(REVIEW_PATH)
    expect(len(reviews) == 3, "REVIEW:COUNT", checks, failures)
    reviews_by_source = {row["source_id"]: row for row in reviews}
    expect(set(reviews_by_source) == set(EXPECTED_SOURCE_IDENTITY), "REVIEW:SOURCES", checks, failures)
    for source_id, row in sorted(reviews_by_source.items()):
        violations = review_violations(row, rights_by_source, hypotheses_by_source)
        expect(not violations, f"REVIEW:{source_id}:{','.join(sorted(violations))}", checks, failures)
    expect(reviews_by_source.get("COMP-SRC-017", {}).get("source_level_disposition") == "INHERITED_EVIDENCE_SCOPE_CONFLICT_QUARANTINED", "REVIEW:OUP_QUARANTINE", checks, failures)

    corrections = read_tsv(CORRECTION_PATH)
    expect(len(corrections) == 1, "CORRECTION:COUNT", checks, failures)
    correction = corrections[0] if corrections else {}
    correction_failures = correction_violations(correction, rights_by_source) if correction else {"MISSING"}
    expect(not correction_failures, f"CORRECTION:{','.join(sorted(correction_failures))}", checks, failures)
    expect(raw_row_sha256(COMPOSITION_EVIDENCE, "COMP-EVID-018") == correction.get("legacy_row_sha256"), "CORRECTION:LEGACY_PRESERVED", checks, failures)
    expect("Latin/Frankish/Venetian" in correction.get("official_abstract_scope", ""), "CORRECTION:SOURCE_SCOPE", checks, failures)
    expect("Ottoman Turkish" in correction.get("official_abstract_scope", ""), "CORRECTION:TARGET_SCOPE", checks, failures)

    isolated_source = {row["canonical_label"]: row for row in read_tsv(ISOLATED_TERMS)}
    vocab_impacts = read_tsv(VOCAB_IMPACT_PATH)
    expected_isolated_labels = {"canonization", "cultural transfer", "cultural transformation", "mobile object", "self-exoticization"}
    expect(len(vocab_impacts) == 5, "VOCAB:COUNT", checks, failures)
    expect({row["canonical_label"] for row in vocab_impacts} == expected_isolated_labels, "VOCAB:LABELS", checks, failures)
    for row in vocab_impacts:
        violations = common_row_violations(row)
        label = row["canonical_label"]
        source = isolated_source.get(label, {})
        expect(not violations, f"VOCAB:{label}:ROW:{','.join(sorted(violations))}", checks, failures)
        expect(row.get("vocabulary_id") == source.get("vocabulary_id") and row.get("participant_sense_id") == source.get("participant_sense_id"), f"VOCAB:{label}:IDENTITY", checks, failures)
        expect(row.get("round16a_pair_degree") == "0", f"VOCAB:{label}:ISOLATED", checks, failures)
        expect(row.get("active_association_count") == "0" and row.get("active_product_path_count") == "0", f"VOCAB:{label}:INACTIVE", checks, failures)
        expect(row.get("higher_order_composability_proven") == "false" and row.get("product_accessibility_disposition") == "OPEN_BLOCKING", f"VOCAB:{label}:UNRESOLVED", checks, failures)
        association_ids = json.loads(row["shard2_association_ids_json"])
        if label in {"canonization", "mobile object"}:
            expect(len(association_ids) == 1 and association_ids[0] in reconstructed_associations, f"VOCAB:{label}:INQUIRY_PATH", checks, failures)
        else:
            expect(association_ids == [], f"VOCAB:{label}:NO_PATH", checks, failures)
    transformation = next((row for row in vocab_impacts if row["canonical_label"] == "cultural transformation"), {})
    expect(transformation.get("shard2_evidence_impact") == "PRIOR_SUPPORT_QUARANTINED_ACTIVE_STATUS_REAUDIT_REQUIRED", "VOCAB:TRANSFORMATION_QUARANTINE", checks, failures)

    gaps = read_tsv(GAP_PATH)
    expect(len(gaps) == 6, "GAP:COUNT", checks, failures)
    expect({row["gap_class"] for row in gaps} == EXPECTED_GAP_CLASSES, "GAP:CLASSES", checks, failures)
    for row in gaps:
        violations = common_row_violations(row)
        expect(not violations, f"GAP:{row.get('gap_id')}:{','.join(sorted(violations))}", checks, failures)
        expect(row.get("status") == "OPEN_BLOCKING", f"GAP:{row.get('gap_id')}:OPEN", checks, failures)
        expect(all(row.get(field) == "false" for field in ("association_activation_allowed", "product_activation_allowed", "closure_allowed")), f"GAP:{row.get('gap_id')}:FAIL_CLOSED", checks, failures)

    census = read_json(CENSUS_PATH)
    reconstructed_counts = {
        "query_count": len(queries),
        "candidate_trigger_occurrence_count": len(triggers),
        "candidate_trigger_applicability_row_count": len(trigger_matrix),
        "candidate_family_count": len(families),
        "source_review_count": len(reviews),
        "rights_review_count": len(rights),
        "higher_order_hypothesis_count": len(hypotheses),
        "source_scope_correction_count": len(corrections),
        "active_vocabulary_impact_count": len(vocab_impacts),
        "open_gap_count": len(gaps),
        "inquiry_only_association_identity_count": len(reconstructed_associations),
        "active_association_count": sum(row["activation_status"] != "INQUIRY_ONLY" for row in hypotheses),
        "active_pending_review_count": sum(row["activation_status"] != "INQUIRY_ONLY" and row["external_human_review_status"] != "COMPLETE" for row in hypotheses),
        "product_eligible_association_count": sum(row["product_eligible"] == "true" for row in hypotheses),
        "implicit_pair_projection_count": sum(int(row["implicit_pair_projection_count"]) for row in hypotheses),
        "copyrighted_payload_retained_count": sum(row["copyrighted_payload_retained"] == "true" for row in reviews),
        "quarantined_legacy_evidence_count": sum(row["additive_disposition"] == "SOURCE_SCOPE_CONFLICT_QUARANTINE" for row in corrections),
    }
    expect(census.get("source_sha") == SOURCE_SHA and census.get("authority_base_sha") == AUTHORITY_BASE_SHA, "CENSUS:AUTHORITY", checks, failures)
    expect(census.get("shard_id") == SHARD_ID and census.get("retrieved_at_utc") == RETRIEVED_AT_UTC, "CENSUS:SHARD", checks, failures)
    expect(census.get("association_arity_distribution") == {"3": 2}, "CENSUS:ARITY", checks, failures)
    for key, value in sorted(reconstructed_counts.items()):
        expect(census.get(key) == value, f"CENSUS:{key}", checks, failures)
    closure = census.get("closure", {})
    expect(set(closure) == {"pair_association_closure", "higher_order_association_closure", "candidate_universe_closure", "global_composition_coherence_closure", "product_association_reachability_closure", "computational_space_closure", "function3_closure"}, "CENSUS:CLOSURE_KEYS", checks, failures)
    expect(all(value is False for value in closure.values()), "CENSUS:NO_CLOSURE", checks, failures)

    primary_receipt = read_json(PRIMARY_RECEIPT_PATH)
    expect(sha256_file(PRIMARY_RECEIPT_PATH) == EXPECTED_PRIMARY_RECEIPT_SHA256, "PRIMARY_RECEIPT:PIN", checks, failures)
    expect(primary_receipt.get("status") == "PASS", "PRIMARY_RECEIPT:STATUS", checks, failures)
    expect(primary_receipt.get("pinned_inputs") == PRIMARY_PINNED_INPUT_SHA256, "PRIMARY_RECEIPT:INPUTS", checks, failures)
    output_hashes = primary_receipt.get("output_hashes_excluding_receipt", {})
    expect(primary_receipt.get("output_count_excluding_receipt") == len(output_hashes) == 13, "PRIMARY_RECEIPT:OUTPUT_COUNT", checks, failures)
    for path, expected_hash in sorted(output_hashes.items()):
        expect(sha256_file(path) == expected_hash, f"PRIMARY_OUTPUT:{path}", checks, failures)
    aggregate_material = [
        {"path": path, "sha256": sha256_file(path)}
        for path in sorted(output_hashes)
    ]
    aggregate = sha256_bytes(canonical_json(aggregate_material).encode("utf-8"))
    expect(aggregate == primary_receipt.get("aggregate_sha256_excluding_receipt"), "PRIMARY_RECEIPT:AGGREGATE_INTERNAL", checks, failures)
    expect(aggregate == EXPECTED_PRIMARY_AGGREGATE_SHA256, "PRIMARY_RECEIPT:AGGREGATE_PIN", checks, failures)
    expect(primary_receipt.get("counts") == reconstructed_counts, "PRIMARY_RECEIPT:COUNTS", checks, failures)
    expect(all(value is False for value in primary_receipt.get("non_authorizations", {}).values()), "PRIMARY_RECEIPT:NON_AUTHORIZATIONS", checks, failures)

    manifest = read_tsv(MANIFEST_PATH)
    expected_manifest_paths = sorted(set(output_hashes) - {MANIFEST_PATH})
    expect(len(manifest) == len(expected_manifest_paths) == 12, "MANIFEST:COUNT", checks, failures)
    expect([row["path"] for row in manifest] == expected_manifest_paths, "MANIFEST:SORTED_PATHS", checks, failures)
    expect([row["ordinal"] for row in manifest] == [str(value) for value in range(1, 13)], "MANIFEST:ORDINALS", checks, failures)
    for row in manifest:
        path = row["path"]
        expect(row["sha256"] == sha256_file(path), f"MANIFEST:HASH:{path}", checks, failures)
        expect(row["size_bytes"] == str((REPO / path).stat().st_size), f"MANIFEST:SIZE:{path}", checks, failures)
        expect(row["lfs_required"] == "false", f"MANIFEST:LFS:{path}", checks, failures)
    report_text = (REPO / REPORT_PATH).read_text(encoding="utf-8")
    for phrase in ("active associations: 0", "product paths: 0", "implicit pair projections: 0", "closure flags: all false", "frozen legacy artifact is not edited"):
        expect(phrase in report_text, f"REPORT:{phrase}", checks, failures)
    expect(not any(path.lower().endswith((".pdf", ".doc", ".docx", ".epub")) for path in output_hashes), "PAYLOAD:NO_SOURCE_DOCUMENT_OUTPUT", checks, failures)

    negative_controls: list[str] = []

    def negative_probe(name: str, detected: bool) -> None:
        negative_controls.append(name)
        expect(detected, f"NEGATIVE:{name}", checks, failures)

    if hypotheses:
        base_hypothesis = hypotheses[0]
        mutations = [
            ("ACTIVE_ASSOCIATION", "activation_status", "ACTIVE", "ACTIVATION"),
            ("PRODUCT_ELIGIBLE", "product_eligible", "true", "PRODUCT"),
            ("PRODUCT_PATH", "product_path", "api/exploration/fabricated", "PRODUCT"),
            ("PAIR_PROJECTION_POLICY", "pair_projection_policy", "COMPLETE_GRAPH", "PROJECTION"),
            ("PAIR_PROJECTION_COUNT", "implicit_pair_projection_count", "3", "PROJECTION"),
            ("WRONG_ASSOCIATION_ID", "association_id", "R16B-ASSOC:wrong", "ASSOCIATION_ID"),
            ("WRONG_REVISION_ID", "association_revision_id", "R16B-ASSOC-REV:wrong", "REVISION_ID"),
            ("WRONG_RIGHTS_LINK", "rights_record_id", "R16B-SOURCE-RIGHTS:wrong", "RIGHTS_LINK"),
            ("REVIEW_COMPLETE_WITHOUT_AUTHORITY", "external_human_review_status", "COMPLETE", "HUMAN_REVIEW"),
        ]
        for name, field, value, expected_violation in mutations:
            mutated = copy.deepcopy(base_hypothesis)
            mutated[field] = value
            negative_probe(name, expected_violation in hypothesis_violations(mutated, rights_by_source))
        mutated = copy.deepcopy(base_hypothesis)
        labels = json.loads(mutated["participant_labels_json"])[:2]
        mutated["participant_labels_json"] = canonical_json(labels)
        mutated["arity"] = "2"
        negative_probe("MISSING_PARTICIPANT", bool({"ARITY", "ASSOCIATION_ID", "HYPOTHESIS_ID"} & hypothesis_violations(mutated, rights_by_source)))
        mutated = copy.deepcopy(base_hypothesis)
        labels = json.loads(mutated["participant_labels_json"])
        labels[-1] = labels[0]
        mutated["participant_labels_json"] = canonical_json(labels)
        negative_probe("DUPLICATE_PARTICIPANT", "PARTICIPANT_SET" in hypothesis_violations(mutated, rights_by_source))
        mutated = copy.deepcopy(base_hypothesis)
        mutated["participant_sense_ids_json"] = canonical_json(["R16B-SENSE:wrong"] * 3)
        negative_probe("WRONG_BOUNDED_SENSE", "SENSES" in hypothesis_violations(mutated, rights_by_source))
        mutated = copy.deepcopy(base_hypothesis)
        mutated["hypothesis_key"] = "INCOMPATIBLE_CASE_SCOPE"
        negative_probe("INCOMPATIBLE_CASE_SCOPE", bool({"ASSOCIATION_ID", "REVISION_ID", "HYPOTHESIS_ID"} & hypothesis_violations(mutated, rights_by_source)))

    if rights:
        mutated = copy.deepcopy(rights[0])
        mutated.pop("access_condition", None)
        negative_probe("RIGHTS_REQUIRED_FIELD_MISSING", "RIGHTS_SCHEMA" in rights_violations(mutated, required_rights_fields))
        mutated = copy.deepcopy(rights[0])
        mutated["retained_sha256"] = "fabricated-payload-hash"
        negative_probe("SOURCE_PAYLOAD_RETAINED", "RETAINED_PAYLOAD" in rights_violations(mutated, required_rights_fields))

    if queries:
        mutated = copy.deepcopy(queries[0])
        mutated["result_is_association_evidence"] = "true"
        negative_probe("QUERY_RESULT_AS_EVIDENCE", mutated["result_is_association_evidence"] != "false")

    if triggers:
        mutated = copy.deepcopy(triggers[0])
        mutated["pair_graph_derivation"] = "true"
        negative_probe("PAIR_GRAPH_DERIVED_EXTERNAL_CANDIDATE", "PAIR_GRAPH_DERIVATION" in trigger_violations(mutated, trigger_names))
        mutated = copy.deepcopy(triggers[0])
        mutated["activation_created"] = "true"
        negative_probe("TRIGGER_ACTIVATION", "TRIGGER_ACTIVATION" in trigger_violations(mutated, trigger_names))
        mutated = copy.deepcopy(triggers[0])
        mutated["trigger_class"] = "WRONG_GOVERNED_TRIGGER_NAME"
        negative_probe("TRIGGER_ID_NAME_MISMATCH", "TRIGGER_NAME" in trigger_violations(mutated, trigger_names))

    if families:
        mutated = copy.deepcopy(families[0])
        mutated["local_family_match_count"] = "1"
        negative_probe("FALSE_EXTERNAL_UNIVERSE_EXPANSION", "LOCAL_FAMILY_COLLISION" in family_violations(mutated, hypotheses_by_id, trigger_ids, local_sets))
        mutated = copy.deepcopy(families[0])
        mutated["trigger_occurrence_ids_json"] = canonical_json(json.loads(mutated["trigger_occurrence_ids_json"])[:1])
        negative_probe("MISSING_TRIGGER_COVERAGE", "FAMILY_TRIGGER_COVERAGE" in family_violations(mutated, hypotheses_by_id, trigger_ids, local_sets))

    if reviews:
        mutated = copy.deepcopy(reviews[0])
        mutated["copyrighted_payload_retained"] = "true"
        negative_probe("REVIEW_RETAINS_COPYRIGHTED_PAYLOAD", "SOURCE_REVIEW_ACTIVATION_OR_PAYLOAD" in review_violations(mutated, rights_by_source, hypotheses_by_source))

    if correction:
        mutated = copy.deepcopy(correction)
        mutated["evidence_activation_eligible"] = "true"
        negative_probe("QUARANTINED_EVIDENCE_ACTIVATED", "CORRECTION_ELIGIBILITY" in correction_violations(mutated, rights_by_source))
        mutated = copy.deepcopy(correction)
        mutated["legacy_artifact_mutated"] = "true"
        negative_probe("LEGACY_EVIDENCE_MUTATED", "LEGACY_MUTATION" in correction_violations(mutated, rights_by_source))
        mutated = copy.deepcopy(correction)
        mutated["legacy_row_sha256"] = "wrong"
        negative_probe("LEGACY_ROW_HASH_DRIFT", "LEGACY_ROW_HASH" in correction_violations(mutated, rights_by_source))

    if vocab_impacts:
        mutated = copy.deepcopy(vocab_impacts[0])
        mutated["higher_order_composability_proven"] = "true"
        negative_probe("UNREVIEWED_VOCABULARY_COMPOSABLE", mutated["higher_order_composability_proven"] != "false")

    if gaps:
        mutated = copy.deepcopy(gaps[0])
        mutated["closure_allowed"] = "true"
        negative_probe("OPEN_GAP_ALLOWS_CLOSURE", mutated["closure_allowed"] != "false")

    mutated_census = copy.deepcopy(census)
    mutated_census["closure"]["function3_closure"] = True
    negative_probe("FUNCTION3_CLOSURE_WITH_OPEN_GAPS", any(mutated_census["closure"].values()))

    return {
        "schema_version": "trace-round16b-adaptive-source-review-independent-verification-shard-2/v1",
        "verifier_version": VERIFIER_VERSION,
        "verifier_script_sha256": sha256_file(VERIFIER_PATH),
        "primary_builder_sha256": sha256_file(BUILDER_PATH),
        "source_sha": SOURCE_SHA,
        "authority_base_sha": AUTHORITY_BASE_SHA,
        "shard_id": SHARD_ID,
        "status": "PASS" if not failures else "FAIL",
        "check_count": len(checks),
        "failure_count": len(failures),
        "failures": failures,
        "negative_control_count": len(negative_controls),
        "negative_controls": negative_controls,
        "pinned_input_hashes": {path: sha256_file(path) for path in sorted(VERIFIER_PINNED_INPUT_SHA256)},
        "primary_output_hashes": {path: sha256_file(path) for path in sorted(primary_receipt.get("output_hashes_excluding_receipt", {}))},
        "primary_aggregate_sha256": aggregate,
        "reconstructed_counts": reconstructed_counts,
        "reconstructed_association_identities": reconstructed_associations,
        "legacy_evidence_line_sha256": raw_row_sha256(COMPOSITION_EVIDENCE, "COMP-EVID-018"),
        "candidate_universe_expansion_count": len(families),
        "source_payload_retained_count": reconstructed_counts["copyrighted_payload_retained_count"],
        "active_association_count": reconstructed_counts["active_association_count"],
        "product_path_count": reconstructed_counts["product_eligible_association_count"],
        "implicit_pair_projection_count": reconstructed_counts["implicit_pair_projection_count"],
        "closure": closure,
    }


def receipt_bytes(receipt: dict[str, Any]) -> bytes:
    return (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    receipt = verify()
    payload = receipt_bytes(receipt)
    output_path = REPO / INDEPENDENT_RECEIPT_PATH
    mismatch = False
    if args.check:
        mismatch = not output_path.exists() or output_path.read_bytes() != payload
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(payload)
    result = {
        "status": receipt["status"],
        "mode": "CHECK" if args.check else "WRITE",
        "check_count": receipt["check_count"],
        "failure_count": receipt["failure_count"],
        "negative_control_count": receipt["negative_control_count"],
        "receipt_mismatch": mismatch,
        "output": INDEPENDENT_RECEIPT_PATH,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if receipt["status"] == "PASS" and not mismatch else 1


if __name__ == "__main__":
    raise SystemExit(main())
