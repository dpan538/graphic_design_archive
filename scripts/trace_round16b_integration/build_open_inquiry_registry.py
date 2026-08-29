#!/usr/bin/env python3
"""Build the canonical, deterministic TRACE Open Inquiry v1 registry."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any, NoReturn


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = (
    REPOSITORY_ROOT
    / "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw"
)
OUTPUT_PATH = (
    REPOSITORY_ROOT
    / "frontend/generated/trace-open-inquiry-v1/open-inquiry-registry.v1.json"
)
API_VERSION = "trace-open-inquiry/v1"
REGISTRY_VERSION = "trace-open-inquiry-registry/v1"
CANONICAL_SERIALIZATION = "UTF8_SORTED_KEYS_COMPACT_JSON_RECORD_DIGEST"

SHARD_1_HEADERS = [
    "evidence_authority_base_sha",
    "shard_id",
    "hypothesis_id",
    "governed_association_id",
    "governed_association_revision_id",
    "canonical_identity_authority_path",
    "canonical_identity_queue_ref",
    "source_ids_json",
    "linked_parent_candidate_id",
    "parent_disposition_preserved",
    "scope_key",
    "scope_note",
    "participant_labels_json",
    "participant_sense_ids_json",
    "arity",
    "participant_order_meaningful",
    "relation_roles_asserted",
    "relation_form",
    "support_mode",
    "exact_group_support_status",
    "global_coherence_status",
    "sense_scope_status",
    "evidence_disposition",
    "governed_identity_status",
    "external_human_review_status",
    "association_activation_status",
    "active_fact_created",
    "product_eligibility",
    "pair_projection_count",
    "subset_projection_count",
    "nonclaims_json",
    "record_sha256",
]

SHARD_2_HEADERS = [
    "authority_base_sha",
    "shard_id",
    "hypothesis_id",
    "hypothesis_key",
    "association_id",
    "association_revision_id",
    "association_class",
    "arity",
    "participant_labels_json",
    "participant_sense_ids_json",
    "order_semantics",
    "role_semantics",
    "source_id",
    "rights_record_id",
    "bounded_scope",
    "locators_json",
    "support_mode",
    "synthesis_steps_json",
    "counterevidence_json",
    "qualifications_json",
    "source_level_disposition",
    "external_human_review_status",
    "activation_status",
    "product_eligible",
    "product_path",
    "pair_projection_policy",
    "implicit_pair_projection_count",
    "nonclaims_json",
    "closure_effect",
    "record_sha256",
]

SOURCES = [
    {
        "filename": "scoped-association-hypothesis-ledger-shard-1-v1.tsv",
        "sha256": "f16deeca67663b05262640cba1512bb46acb0a36ffe8dcae006fd45dc475bed3",
        "bytes": 13_131,
        "record_count": 9,
        "headers": SHARD_1_HEADERS,
        "adapter": 1,
    },
    {
        "filename": "scoped-association-hypothesis-ledger-shard-2-v1.tsv",
        "sha256": "5b7e04bde8fc0c91f7d141f0ecdccf23579394dafba21e33e91ad512f9ab5a4d",
        "bytes": 4_544,
        "record_count": 2,
        "headers": SHARD_2_HEADERS,
        "adapter": 2,
    },
]

FORBIDDEN_FIELDS = {
    "truth_probability",
    "probability_true",
    "likelihood_score",
    "confidence_percentage",
}

CLOSURE_FLAGS = {
    "PAIR_ASSOCIATION_CLOSURE": False,
    "HIGHER_ORDER_ASSOCIATION_CLOSURE": False,
    "GLOBAL_COMPOSITION_COHERENCE_CLOSURE": False,
    "PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE": False,
    "COMPUTATIONAL_SPACE_CLOSURE": False,
    "FUNCTION3_CLOSURE": False,
}


def fail(message: str) -> NoReturn:
    raise ValueError(message)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def nullable(value: str) -> str | None:
    return value if value else None


def require_text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{label}: expected non-empty text")
    return value


def require_literal(value: str, expected: str, label: str) -> None:
    if value != expected:
        fail(f"{label}: expected {expected!r}, found {value!r}")


def require_int(value: str, expected: set[int], label: str) -> int:
    if not value.isascii() or not value.isdigit():
        fail(f"{label}: expected an ASCII integer")
    parsed = int(value)
    if parsed not in expected:
        fail(f"{label}: unexpected integer {parsed}")
    return parsed


def parse_string_array(value: str, label: str, *, allow_empty: bool = False) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        fail(f"{label}: invalid JSON: {error}")
    if not isinstance(parsed, list) or any(not isinstance(item, str) or not item for item in parsed):
        fail(f"{label}: expected an array of non-empty strings")
    if not allow_empty and not parsed:
        fail(f"{label}: expected at least one string")
    return parsed


def assert_no_forbidden_fields(value: Any, path: str = "$") -> None:
    if isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_forbidden_fields(child, f"{path}[{index}]")
    elif isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_FIELDS:
                fail(f"{path}.{key}: forbidden probability field")
            assert_no_forbidden_fields(child, f"{path}.{key}")


def read_source(source: dict[str, Any]) -> list[dict[str, str]]:
    path = RAW_ROOT / source["filename"]
    data = path.read_bytes()
    if len(data) != source["bytes"]:
        fail(f"{path}: byte length mismatch")
    if sha256_bytes(data) != source["sha256"]:
        fail(f"{path}: SHA-256 mismatch")
    if not data.endswith(b"\n") or data.endswith(b"\n\n") or b"\r" in data:
        fail(f"{path}: requires exactly one final LF and no CR bytes")
    text = data.decode("utf-8", errors="strict")
    reader = csv.DictReader(io.StringIO(text, newline=""), dialect="excel-tab")
    if reader.fieldnames != source["headers"]:
        fail(f"{path}: header mismatch")
    rows = list(reader)
    if len(rows) != source["record_count"]:
        fail(f"{path}: row-count mismatch")
    for row_index, row in enumerate(rows, start=2):
        if None in row or any(value is None for value in row.values()):
            fail(f"{path}:{row_index}: malformed field count")
        stored = row["record_sha256"]
        material = {key: value for key, value in row.items() if key != "record_sha256"}
        if sha256_bytes(canonical_bytes(material)) != stored:
            fail(f"{path}:{row_index}: source record SHA-256 mismatch")
    return rows


def normalize_shard_1(
    row: dict[str, str], source: dict[str, Any], source_row_number: int
) -> dict[str, Any]:
    arity = require_int(row["arity"], {2, 3, 4, 5}, "shard1.arity")
    labels = parse_string_array(row["participant_labels_json"], "shard1.participants")
    sense_ids = parse_string_array(row["participant_sense_ids_json"], "shard1.senses")
    if len(labels) != arity or len(sense_ids) != arity:
        fail("shard1: participant/arity mismatch")
    require_literal(row["participant_order_meaningful"], "false", "shard1.order")
    require_literal(row["relation_roles_asserted"], "false", "shard1.roles")
    require_literal(row["active_fact_created"], "false", "shard1.active")
    require_literal(
        row["product_eligibility"],
        "INELIGIBLE_INQUIRY_ONLY_OR_REVIEW_ACTION",
        "shard1.product",
    )
    require_literal(row["pair_projection_count"], "0", "shard1.pair_projection")
    require_literal(row["subset_projection_count"], "0", "shard1.subset_projection")
    if row["external_human_review_status"] != "OPEN":
        fail("shard1: unexpected external-review status")
    if row["association_activation_status"] != "INACTIVE":
        fail("shard1: unexpected activation status")

    association_id = row["governed_association_id"]
    association_revision_id = row["governed_association_revision_id"]
    if bool(association_id) != bool(association_revision_id):
        fail("shard1: incomplete governed association identity")
    identity = None
    if association_id:
        identity = {
            "association_id": association_id,
            "association_revision_id": association_revision_id,
            "authority_path": nullable(row["canonical_identity_authority_path"]),
            "authority_queue_ref": nullable(row["canonical_identity_queue_ref"]),
        }

    return make_record(
        inquiry_id=require_text(row["hypothesis_id"], "shard1.hypothesis_id"),
        inquiry_key=require_text(row["scope_key"], "shard1.scope_key"),
        arity=arity,
        labels=labels,
        sense_ids=sense_ids,
        bounded_scope=require_text(row["scope_note"], "shard1.scope_note"),
        relation_form=require_text(row["relation_form"], "shard1.relation_form"),
        identity=identity,
        evidence={
            "support_mode": require_text(row["support_mode"], "shard1.support_mode"),
            "disposition": require_text(row["evidence_disposition"], "shard1.disposition"),
            "exact_group_support_status": require_text(
                row["exact_group_support_status"], "shard1.exact_group_support_status"
            ),
            "global_coherence_status": require_text(
                row["global_coherence_status"], "shard1.global_coherence_status"
            ),
            "sense_scope_status": require_text(
                row["sense_scope_status"], "shard1.sense_scope_status"
            ),
            "locators": None,
            "synthesis_steps": None,
            "counterevidence": None,
            "qualifications": None,
            "nonclaims": parse_string_array(row["nonclaims_json"], "shard1.nonclaims"),
        },
        provenance={
            "authority_base_sha": require_text(
                row["evidence_authority_base_sha"], "shard1.authority"
            ),
            "shard_id": require_text(row["shard_id"], "shard1.shard_id"),
            "source_ledger_path": (
                "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/"
                + source["filename"]
            ),
            "source_ledger_sha256": source["sha256"],
            "source_row_number": source_row_number,
            "source_record_sha256": row["record_sha256"],
            "source_ids": parse_string_array(row["source_ids_json"], "shard1.source_ids"),
            "rights_record_ids": None,
            "linked_parent_candidate_id": nullable(row["linked_parent_candidate_id"]),
            "parent_disposition_preserved": nullable(row["parent_disposition_preserved"]),
            "source_external_human_review_status": row["external_human_review_status"],
            "source_activation_status": row["association_activation_status"],
        },
    )


def normalize_shard_2(
    row: dict[str, str], source: dict[str, Any], source_row_number: int
) -> dict[str, Any]:
    arity = require_int(row["arity"], {2, 3, 4, 5}, "shard2.arity")
    labels = parse_string_array(row["participant_labels_json"], "shard2.participants")
    sense_ids = parse_string_array(row["participant_sense_ids_json"], "shard2.senses")
    if len(labels) != arity or len(sense_ids) != arity:
        fail("shard2: participant/arity mismatch")
    require_literal(row["order_semantics"], "UNORDERED", "shard2.order")
    require_literal(row["role_semantics"], "NONE_UNTIL_EXTERNAL_REVIEW", "shard2.roles")
    require_literal(row["external_human_review_status"], "PENDING_NOT_ACTIVE", "shard2.review")
    require_literal(row["activation_status"], "INQUIRY_ONLY", "shard2.activation")
    require_literal(row["product_eligible"], "false", "shard2.product")
    require_literal(row["product_path"], "", "shard2.product_path")
    require_literal(row["pair_projection_policy"], "NONE", "shard2.pair_policy")
    require_literal(row["implicit_pair_projection_count"], "0", "shard2.pair_count")

    association_id = require_text(row["association_id"], "shard2.association_id")
    association_revision_id = require_text(
        row["association_revision_id"], "shard2.association_revision_id"
    )
    return make_record(
        inquiry_id=require_text(row["hypothesis_id"], "shard2.hypothesis_id"),
        inquiry_key=require_text(row["hypothesis_key"], "shard2.hypothesis_key"),
        arity=arity,
        labels=labels,
        sense_ids=sense_ids,
        bounded_scope=require_text(row["bounded_scope"], "shard2.bounded_scope"),
        relation_form=require_text(row["association_class"], "shard2.association_class"),
        identity={
            "association_id": association_id,
            "association_revision_id": association_revision_id,
            "authority_path": None,
            "authority_queue_ref": None,
        },
        evidence={
            "support_mode": require_text(row["support_mode"], "shard2.support_mode"),
            "disposition": require_text(
                row["source_level_disposition"], "shard2.disposition"
            ),
            "exact_group_support_status": None,
            "global_coherence_status": None,
            "sense_scope_status": None,
            "locators": parse_string_array(row["locators_json"], "shard2.locators"),
            "synthesis_steps": parse_string_array(
                row["synthesis_steps_json"], "shard2.synthesis"
            ),
            "counterevidence": parse_string_array(
                row["counterevidence_json"], "shard2.counterevidence"
            ),
            "qualifications": parse_string_array(
                row["qualifications_json"], "shard2.qualifications"
            ),
            "nonclaims": parse_string_array(row["nonclaims_json"], "shard2.nonclaims"),
        },
        provenance={
            "authority_base_sha": require_text(row["authority_base_sha"], "shard2.authority"),
            "shard_id": require_text(row["shard_id"], "shard2.shard_id"),
            "source_ledger_path": (
                "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/"
                + source["filename"]
            ),
            "source_ledger_sha256": source["sha256"],
            "source_row_number": source_row_number,
            "source_record_sha256": row["record_sha256"],
            "source_ids": [require_text(row["source_id"], "shard2.source_id")],
            "rights_record_ids": [
                require_text(row["rights_record_id"], "shard2.rights_record_id")
            ],
            "linked_parent_candidate_id": None,
            "parent_disposition_preserved": None,
            "source_external_human_review_status": row["external_human_review_status"],
            "source_activation_status": row["activation_status"],
        },
    )


def make_record(
    *,
    inquiry_id: str,
    inquiry_key: str,
    arity: int,
    labels: list[str],
    sense_ids: list[str],
    bounded_scope: str,
    relation_form: str,
    identity: dict[str, Any] | None,
    evidence: dict[str, Any],
    provenance: dict[str, Any],
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "record_version": API_VERSION,
        "inquiry_id": inquiry_id,
        "inquiry_key": inquiry_key,
        "arity": arity,
        "participants": [
            {"label": label, "sense_id": sense_id}
            for label, sense_id in zip(labels, sense_ids, strict=True)
        ],
        "bounded_scope": bounded_scope,
        "relation_form": relation_form,
        "epistemic_status": "UNRESOLVED_OPEN_INQUIRY",
        "validated_relation": False,
        "counts_as_validated": False,
        "eligible_for_validated_graph": False,
        "eligible_for_validated_composition": False,
        "may_generate_pair_edges": False,
        "may_modify_validated_topology": False,
        "display_eligible": True,
        "display_layer": "OPEN_INQUIRY",
        "default_in_validated_results": False,
        "active": False,
        "external_human_review_status": "PENDING",
        "product_eligible": False,
        "product_path": None,
        "participant_order_meaningful": False,
        "relation_roles_asserted": False,
        "pair_projection_policy": "NONE",
        "implicit_pair_projection_count": 0,
        "inquiry_only_association_identity": identity,
        "evidence": evidence,
        "provenance": provenance,
    }
    record["record_sha256"] = sha256_bytes(canonical_bytes(record))
    return record


def build_registry() -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    input_bindings: list[dict[str, Any]] = []
    for source in SOURCES:
        rows = read_source(source)
        input_bindings.append(
            {
                "path": (
                    "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/"
                    + source["filename"]
                ),
                "sha256": source["sha256"],
                "bytes": source["bytes"],
                "record_count": source["record_count"],
            }
        )
        for source_row_number, row in enumerate(rows, start=2):
            adapter = normalize_shard_1 if source["adapter"] == 1 else normalize_shard_2
            records.append(adapter(row, source, source_row_number))

    records.sort(key=lambda record: record["inquiry_id"])
    if len(records) != 11 or len({record["inquiry_id"] for record in records}) != 11:
        fail("registry: stable inquiry IDs are not exactly 11 unique values")
    if len({record["inquiry_key"] for record in records}) != 11:
        fail("registry: inquiry keys are not unique")
    arity_counts = {
        arity: sum(record["arity"] == arity for record in records)
        for arity in (2, 3, 4, 5)
    }
    if arity_counts != {2: 3, 3: 6, 4: 1, 5: 1}:
        fail(f"registry: unexpected arity counts {arity_counts}")
    identity_count = sum(
        record["inquiry_only_association_identity"] is not None for record in records
    )
    if identity_count != 4:
        fail(f"registry: expected four inquiry-only association identities, found {identity_count}")
    if any(record["active"] for record in records):
        fail("registry: active Open Inquiry record found")
    if sum(record["implicit_pair_projection_count"] for record in records) != 0:
        fail("registry: implicit pair projection found")

    registry = {
        "registry_version": REGISTRY_VERSION,
        "api_version": API_VERSION,
        "canonical_serialization": CANONICAL_SERIALIZATION,
        "input_bindings": input_bindings,
        "counts": {
            "scoped_higher_order_hypothesis_count": 11,
            "arity_2_count": 3,
            "arity_3_count": 6,
            "arity_4_count": 1,
            "arity_5_count": 1,
            "governed_inquiry_only_association_identity_count": 4,
            "ungoverned_hypothesis_count": 7,
            "active_pending_review_count": 0,
            "implicit_pair_projection_count": 0,
        },
        "closure_flags": CLOSURE_FLAGS,
        "records_sha256": sha256_bytes(canonical_bytes(records)),
        "records": records,
    }
    assert_no_forbidden_fields(registry)
    return registry


def rendered_bytes(registry: dict[str, Any]) -> bytes:
    return (
        json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    registry = build_registry()
    output = rendered_bytes(registry)
    if args.check:
        if not OUTPUT_PATH.is_file():
            print(f"FAIL: missing generated registry: {OUTPUT_PATH}", file=sys.stderr)
            return 1
        actual = OUTPUT_PATH.read_bytes()
        if actual != output:
            print("FAIL: generated Open Inquiry registry is stale", file=sys.stderr)
            return 1
        print(
            "PASS: canonical Open Inquiry registry is deterministic "
            f"(records=11, records_sha256={registry['records_sha256']})"
        )
        return 0
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(output)
    print(
        "PASS: wrote canonical Open Inquiry registry "
        f"(records=11, records_sha256={registry['records_sha256']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
