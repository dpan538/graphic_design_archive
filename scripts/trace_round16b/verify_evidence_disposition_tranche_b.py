#!/usr/bin/env python3
"""Independent verifier for Round 16B evidence-disposition tranche B.

The verifier intentionally does not import or execute the tranche-B builder.
It reconstructs the governed selector, occurrence classes, active internal
pairs, cumulative coverage, queue safety, and receipt hashes from committed
inputs and the materialized artifacts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
PARENT_SHA = "adf3cc7a214aa1b8fdaef75b7a9e8888c39c906e"
TRANCHE = "CHECKPOINT-006-EVIDENCE-TRANCHE-B"
BUILDER_VERSION = "trace-round16b-evidence-disposition-tranche-b-v1"

RAW = Path("docs/audits/v49-exploration-higher-order-association-closure-round16b/raw")
RESEARCH = Path("docs/research/trace-v49-exploration-higher-order-association-closure-round16b")
V2_OCCURRENCES = RAW / "candidate-trigger-occurrence-ledger-v2.tsv"
V2_FAMILIES = RAW / "local-candidate-family-ledger-v2.tsv"
ACTIVE_GRAPH = Path("docs/audits/v49-exploration-full-space-closure-round1/raw/validated-association-graph-v2.json")
TRANCHE_A_OCCURRENCES = RAW / "evidence-occurrence-disposition-tranche-a-v1.tsv"
TRANCHE_A_FAMILIES = RAW / "family-evidence-disposition-tranche-a-v1.tsv"
OCCURRENCE_OUTPUT = RAW / "evidence-occurrence-disposition-tranche-b-v1.tsv"
FAMILY_OUTPUT = RAW / "family-evidence-disposition-tranche-b-v1.tsv"
QUEUE_OUTPUT = RAW / "conditional-scoped-child-reroute-queue-tranche-b-v1.tsv"
INPUT_MANIFEST = RAW / "evidence-disposition-input-manifest-tranche-b-v1.tsv"
GAP_OUTPUT = RAW / "recursive-gap-ledger-checkpoint006-tranche-b-v1.tsv"
CENSUS_OUTPUT = RAW / "evidence-disposition-census-tranche-b-v1.json"
BUILD_RECEIPT = RAW / "evidence-disposition-build-receipt-tranche-b-v1.json"
RESEARCH_NOTE = RESEARCH / "10_EVIDENCE_DISPOSITION_TRANCHE_B.md"
DEFAULT_OUTPUT = RAW / "evidence-disposition-independent-verification-tranche-b-v1.json"


FAMILY_DISPOSITIONS = {
    "07d5c44f285178774f70755012d2745feec81d240210c340b5910a738ae0a837": "HARD_NEGATIVE",
    "0e719db533fd03f71aa5fbb293aa0d6aa8b79453db51fe8e0f8b7f0fc59fede9": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
    "15f5757830dfe043fb27e73c28ff3bfd902aaa9c938ab254fda8682d359a7249": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
    "23b72032e8165ac9f164a43ac0e1932f2fe4354f1b89f62d67ebe7d497de7af1": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
    "2770b6b66713cd3191cec7b14915b14624cbda9b7307b53bb230ea7f29d8caec": "INSUFFICIENT_EVIDENCE",
    "3648ab4f374cda7a490244914de785b764e7e4f7c872f094e8a2d3f03a71a560": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
    "3fab395d77bb9112b04a2eedc91aa128a006839ed048fb6a3a143762a35a3c3c": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
    "7696ac77a3bd8ac70e8e0181b3ae969502426a44200925dffb65ef88312e954a": "COOCCURRENCE_ONLY",
    "83009b1d124d4635a57866eeffba5e1a1a33e499bd60b30c6346b94ff1a04f8e": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
    "9ade19c60e22d8aa127040cefd633119f8b05e04baf0f814d2d008d0aae8796e": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
    "af25d1d4c93f79886769d53d071805bd5b6726130b153e4484121321d1122e3a": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
    "d6dfcd4e355294899be8838eb8ec71439d8911ea19f8aa92401d1a52becf76c0": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
    "e33bd6538eb80f04087e13b1896ff995a5523453a10e8f4aec460ef9fdd87376": "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
    "e6b89317c05c3543ab2cd0005c53716c62dcf45e75965992f7b593873772d0e4": "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
}

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

EXPECTED_SOURCE_COUNTS = {
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
EXPECTED_EVIDENCE_COUNTS = {
    "EVIDENCE_BEARING_INPUT": 7,
    "EXPLICIT_NEAR_MISS": 1,
    "HARD_NEGATIVE_CONTROL": 1,
    "METADATA_DISCOVERY": 11,
    "STRUCTURAL_ECHO": 164,
    "SYNTHETIC_CONTROL": 2,
    "VOCABULARY_ONLY_COOCCURRENCE": 1,
}
EXPECTED_DISPOSITION_COUNTS = {
    "BOUNDED_SENSE_OR_SCOPE_CONFLICT": 6,
    "COOCCURRENCE_ONLY": 1,
    "HARD_NEGATIVE": 1,
    "INSUFFICIENT_EVIDENCE": 1,
    "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE": 5,
}
EXPECTED_QUEUE_KIND_COUNTS = {
    "CONDITIONAL_SCOPED_CHILD_REVIEW": 13,
    "DERIVATIVE_RECONCILIATION": 6,
    "PAIR_OR_SCOPE_REROUTE": 13,
    "PARENT_CLOSE_CONTROL": 5,
}
EXPECTED_CUMULATIVE_COUNTS = {
    "BOUNDED_SENSE_OR_SCOPE_CONFLICT": 11,
    "COOCCURRENCE_ONLY": 2,
    "HARD_NEGATIVE": 1,
    "INQUIRY_ONLY_OR_UNRESOLVED": 3,
    "INSUFFICIENT_EVIDENCE": 2,
    "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE": 5,
    "TOPOLOGY_OR_ROLE_CONFLICT": 1,
}
EXPECTED_CLOSURE_KEYS = {
    "pair_association_closure",
    "higher_order_association_closure",
    "global_composition_coherence_closure",
    "product_association_reachability_closure",
    "computational_space_closure",
    "function3_closure",
}
EXPECTED_OUTPUTS = {
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


def verify_record_hashes(rows: list[dict[str, str]]) -> list[int]:
    failures: list[int] = []
    for index, row in enumerate(rows, 1):
        material = dict(row)
        actual = material.pop("record_sha256", "")
        if actual != row_hash(material):
            failures.append(index)
    return failures


def evidence_class(key: str, source_class: str) -> str:
    if key.startswith("07d5c44f") and source_class == "R15_RESEARCH_FIXTURE":
        return "HARD_NEGATIVE_CONTROL"
    if source_class == "DATABASE_DISCOVERY_LOCUS":
        return "METADATA_DISCOVERY"
    if source_class in {"R14_SHARED_LOCATOR_PROVENANCE", "R13_EXACT_EVIDENCE_RECORD", "R10_GRAMMAR_ATTESTATION"}:
        return "EVIDENCE_BEARING_INPUT"
    if source_class == "R14_SYNTHETIC_NARY_CONTROL":
        return "SYNTHETIC_CONTROL"
    if source_class == "R10_CLUSTER_HANDOFF":
        return "EXPLICIT_NEAR_MISS"
    if source_class == "R16_SCHOLARLY_SOURCE_METADATA":
        return "VOCABULARY_ONLY_COOCCURRENCE"
    return "STRUCTURAL_ECHO"


def input_record_count(path: Path) -> int:
    if path.suffix == ".tsv":
        return len(read_tsv(path)[1])
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    def require(check_id: str, condition: bool, detail: Any = None) -> None:
        record: dict[str, Any] = {"check_id": check_id, "status": "PASS" if condition else "FAIL"}
        if detail not in (None, "", [], {}):
            record["detail"] = detail
        checks.append(record)
        if not condition:
            failures.append(check_id)

    required = {
        V2_OCCURRENCES, V2_FAMILIES, ACTIVE_GRAPH, TRANCHE_A_OCCURRENCES,
        TRANCHE_A_FAMILIES, OCCURRENCE_OUTPUT, FAMILY_OUTPUT, QUEUE_OUTPUT,
        INPUT_MANIFEST, GAP_OUTPUT, CENSUS_OUTPUT, BUILD_RECEIPT, RESEARCH_NOTE,
    }
    missing = sorted(str(path) for path in required if not (repo / path).is_file())
    require("REQUIRED_ARTIFACTS_PRESENT", not missing, missing)
    if missing:
        payload = {"format": "trace-round16b-evidence-disposition-tranche-b-independent-verification-v1", "status": "FAIL", "checks": checks, "failures": failures}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 1

    _, v2_families = read_tsv(repo / V2_FAMILIES)
    _, v2_occurrences = read_tsv(repo / V2_OCCURRENCES)
    family_by_key = {row["participant_set_key"]: row for row in v2_families}
    occurrence_by_id = {row["trigger_occurrence_id"]: row for row in v2_occurrences}
    selected_keys = set(FAMILY_DISPOSITIONS)
    selected_occurrences = [row for row in v2_occurrences if row["participant_set_key"] in selected_keys]
    selected_ids = {row["trigger_occurrence_id"] for row in selected_occurrences}
    require("CHECKPOINT004_UNIVERSE_EXACT", len(v2_families) == len(family_by_key) == 35 and len(v2_occurrences) == len(occurrence_by_id) == 359)
    require("TRANCHE_B_SELECTOR_EXACT_14_ARITY3", selected_keys.issubset(family_by_key) and len(selected_keys) == 14 and all(int(family_by_key[key]["arity"]) == 3 for key in selected_keys))
    require("TRANCHE_B_OCCURRENCE_SELECTOR_EXACT_187", len(selected_occurrences) == len(selected_ids) == 187)
    source_row_hash_failures = []
    for row in selected_occurrences:
        material = dict(row)
        actual = material.pop("occurrence_sha256", "")
        if row_hash(material) != actual:
            source_row_hash_failures.append(row["trigger_occurrence_id"])
    require("SELECTED_V2_OCCURRENCE_HASHES_EXACT", not source_row_hash_failures, source_row_hash_failures[:10])

    expected_source_by_id: dict[str, str] = {}
    expected_evidence_by_id: dict[str, str] = {}
    source_mapping_failures: list[str] = []
    for row in selected_occurrences:
        source_class = SOURCE_CLASS_BY_SURFACE.get(row["input_surface_id"])
        if source_class is None:
            source_mapping_failures.append(row["input_surface_id"])
            continue
        expected_source_by_id[row["trigger_occurrence_id"]] = source_class
        expected_evidence_by_id[row["trigger_occurrence_id"]] = evidence_class(row["participant_set_key"], source_class)
    require("ALL_SOURCE_SURFACES_INDEPENDENTLY_CLASSIFIED", not source_mapping_failures, sorted(set(source_mapping_failures)))
    require("SOURCE_CLASS_COUNTS_EXACT", dict(sorted(Counter(expected_source_by_id.values()).items())) == EXPECTED_SOURCE_COUNTS)
    require("EVIDENCE_CLASS_COUNTS_EXACT", dict(sorted(Counter(expected_evidence_by_id.values()).items())) == EXPECTED_EVIDENCE_COUNTS)

    _, out_occurrences = read_tsv(repo / OCCURRENCE_OUTPUT)
    out_occurrence_by_id = {row["trigger_occurrence_id"]: row for row in out_occurrences}
    require("OUTPUT_OCCURRENCE_COVERAGE_EXACT_187", len(out_occurrences) == len(out_occurrence_by_id) == 187 and set(out_occurrence_by_id) == selected_ids)
    require("OUTPUT_OCCURRENCE_RECORD_HASHES_EXACT", not verify_record_hashes(out_occurrences), verify_record_hashes(out_occurrences)[:10])
    occurrence_failures: list[str] = []
    for occurrence_id, source in {row["trigger_occurrence_id"]: row for row in selected_occurrences}.items():
        actual = out_occurrence_by_id.get(occurrence_id)
        if actual is None:
            continue
        if (
            actual["parent_checkpoint_sha"] != PARENT_SHA
            or actual["review_tranche"] != TRANCHE
            or actual["candidate_id"] != source["candidate_id"]
            or actual["participant_set_key"] != source["participant_set_key"]
            or actual["source_occurrence_sha256"] != source["occurrence_sha256"]
            or actual["occurrence_source_class"] != expected_source_by_id[occurrence_id]
            or actual["occurrence_evidence_class"] != expected_evidence_by_id[occurrence_id]
            or actual["exact_group_support_status"] != "NOT_GOVERNED_SUPPORT"
            or actual["product_eligibility"] != "INELIGIBLE_NOT_GOVERNED_ASSOCIATION_SUPPORT"
            or actual["pair_projection_created"] != "false"
            or actual["association_activation_created"] != "false"
        ):
            occurrence_failures.append(occurrence_id)
    require("OUTPUT_OCCURRENCES_FAIL_CLOSED_AND_SOURCE_BOUND", not occurrence_failures, occurrence_failures[:10])

    _, out_families = read_tsv(repo / FAMILY_OUTPUT)
    out_family_by_key = {row["participant_set_key"]: row for row in out_families}
    require("OUTPUT_FAMILY_COVERAGE_EXACT_14", len(out_families) == len(out_family_by_key) == 14 and set(out_family_by_key) == selected_keys)
    require("OUTPUT_FAMILY_RECORD_HASHES_EXACT", not verify_record_hashes(out_families), verify_record_hashes(out_families))
    graph = read_json(repo / ACTIVE_GRAPH)
    active_edges = graph["edges"]
    family_failures: list[str] = []
    for key, disposition in FAMILY_DISPOSITIONS.items():
        source = family_by_key[key]
        actual = out_family_by_key.get(key)
        if actual is None:
            continue
        ids = sorted(row["trigger_occurrence_id"] for row in selected_occurrences if row["participant_set_key"] == key)
        source_counts = dict(sorted(Counter(expected_source_by_id[value] for value in ids).items()))
        evidence_counts = dict(sorted(Counter(expected_evidence_by_id[value] for value in ids).items()))
        labels = set(json.loads(source["canonical_labels_json"]))
        active = sorted(edge["association_id"] for edge in active_edges if {edge["label_a"], edge["label_b"]}.issubset(labels))
        if (
            actual["parent_checkpoint_sha"] != PARENT_SHA
            or actual["review_tranche"] != TRANCHE
            or actual["candidate_id"] != source["candidate_id"]
            or actual["canonical_labels_json"] != source["canonical_labels_json"]
            or int(actual["arity"]) != 3
            or int(actual["linked_occurrence_count"]) != len(ids)
            or actual["linked_occurrence_ids_sha256"] != sha256_text(canonical_json(ids))
            or json.loads(actual["occurrence_source_class_counts_json"]) != source_counts
            or json.loads(actual["occurrence_evidence_class_counts_json"]) != evidence_counts
            or int(actual["internal_possible_pair_count"]) != math.comb(3, 2)
            or int(actual["internal_active_pair_count"]) != len(active)
            or json.loads(actual["internal_active_pair_ids_json"]) != active
            or actual["final_parent_disposition"] != disposition
            or actual["parent_disposition_status"] != "FINAL_FOR_UNSPLIT_PARENT_REVIEW_FAMILY_FAIL_CLOSED"
            or actual["direct_group_support_status"] != "NO_ACTIVE_DIRECT_SUPPORT_FOR_UNSPLIT_PARENT"
            or actual["composite_group_support_status"] != "NO_ACTIVE_COMPOSITE_SUPPORT_FOR_UNSPLIT_PARENT"
            or actual["global_coherence_status"] != "FAIL_CLOSED_NOT_PASSED"
            or actual["association_identity_status"] != "NOT_CREATED_PARENT_IS_REVIEW_FAMILY_NOT_ASSOCIATION"
            or actual["association_activation_status"] != "INACTIVE"
            or not actual["product_eligibility"].startswith("INELIGIBLE_")
            or int(actual["pair_projection_count"]) != 0
        ):
            family_failures.append(key)
    require("FAMILY_ROWS_AND_ACTIVE_PAIRS_INDEPENDENTLY_RECONSTRUCTED", not family_failures, family_failures)
    actual_dispositions = dict(sorted(Counter(row["final_parent_disposition"] for row in out_families).items()))
    require("FINAL_PARENT_DISPOSITION_COUNTS_EXACT", actual_dispositions == EXPECTED_DISPOSITION_COUNTS, actual_dispositions)
    clique_rows = [row for row in out_families if int(row["internal_active_pair_count"]) == 3]
    require("PAIRWISE_CLIQUES_REMAIN_GROUP_INVALID", len(clique_rows) == 3 and all(row["global_coherence_status"] == "FAIL_CLOSED_NOT_PASSED" and row["association_activation_status"] == "INACTIVE" for row in clique_rows), [row["participant_set_key"] for row in clique_rows])
    hard_negative_rows = [row for row in out_families if row["final_parent_disposition"] == "HARD_NEGATIVE"]
    require("HARD_NEGATIVE_PARENT_REMAINS_INACTIVE", len(hard_negative_rows) == 1 and hard_negative_rows[0]["association_activation_status"] == "INACTIVE" and int(hard_negative_rows[0]["pair_projection_count"]) == 0)

    _, queue_rows = read_tsv(repo / QUEUE_OUTPUT)
    queue_refs = [row["memo_queue_ref"] for row in queue_rows]
    require("QUEUE_REFS_EXACT_TBQ001_037", queue_refs == [f"TBQ-{value:03d}" for value in range(1, 38)])
    require("QUEUE_RECORD_HASHES_EXACT", not verify_record_hashes(queue_rows), verify_record_hashes(queue_rows))
    queue_kinds = dict(sorted(Counter(row["queue_record_kind"] for row in queue_rows).items()))
    require("QUEUE_KIND_COUNTS_EXACT", queue_kinds == EXPECTED_QUEUE_KIND_COUNTS, queue_kinds)
    queue_failures: list[str] = []
    for row in queue_rows:
        evidence_ids = json.loads(row["evidence_occurrence_ids_json"])
        if (
            row["parent_checkpoint_sha"] != PARENT_SHA
            or row["review_tranche"] != TRANCHE
            or not evidence_ids
            or not set(evidence_ids).issubset(occurrence_by_id)
            or row["association_identity_created"] != "false"
            or row["association_active"] != "false"
            or row["pair_projection_created"] != "false"
            or not row["product_eligibility"].startswith("INELIGIBLE_")
            or row["queue_status"] == "GOVERNED_ASSOCIATION"
        ):
            queue_failures.append(row["memo_queue_ref"])
    require("QUEUE_IS_NONCANDIDATE_FAIL_CLOSED_AND_PROVENANCED", not queue_failures, queue_failures)
    queue_parent_counts = Counter(row["parent_candidate_id"] for row in queue_rows)
    require("EVERY_QUEUE_PARENT_IS_A_TRANCHE_B_FAMILY", set(queue_parent_counts).issubset({row["candidate_id"] for row in out_families}))
    sweden_rows = [row for row in queue_rows if "89817e7a449f1cc7b574fb1b89c9541f765e52825c5cb62bf0a2bb833e8f970a" in row["target_or_child"]]
    require("ARITY4_SWEDEN_REROUTES_NEVER_PROJECT", len(sweden_rows) == 4 and all(row["pair_projection_created"] == "false" and row["association_active"] == "false" for row in sweden_rows))

    _, manifest_rows = read_tsv(repo / INPUT_MANIFEST)
    manifest_failures: list[str] = []
    for ordinal, row in enumerate(manifest_rows, 1):
        path = repo / row["path"]
        material = dict(row)
        actual_record_hash = material.pop("record_sha256", "")
        if (
            row["parent_checkpoint_sha"] != PARENT_SHA
            or int(row["input_ordinal"]) != ordinal
            or not path.is_file()
            or int(row["bytes"]) != path.stat().st_size
            or int(row["input_record_count"]) != input_record_count(path)
            or row["sha256"] != sha256_file(path)
            or row["pinned_sha256"] != row["sha256"]
            or row["pin_match"] != "true"
            or actual_record_hash != row_hash(material)
        ):
            manifest_failures.append(row["path"])
    require("INPUT_MANIFEST_25_PATHS_HASHED_AND_PINNED", len(manifest_rows) == 25 and not manifest_failures, manifest_failures)
    require("INPUT_MANIFEST_BINDS_BUILDER_SOURCE", manifest_rows[-1]["path"] == "scripts/trace_round16b/build_evidence_disposition_tranche_b.py")

    _, tranche_a_families = read_tsv(repo / TRANCHE_A_FAMILIES)
    _, tranche_a_occurrences = read_tsv(repo / TRANCHE_A_OCCURRENCES)
    disposed_keys = {row["participant_set_key"] for row in tranche_a_families} | selected_keys
    disposed_ids = {row["trigger_occurrence_id"] for row in tranche_a_occurrences} | selected_ids
    remaining_families = [row for row in v2_families if row["participant_set_key"] not in disposed_keys]
    remaining_ids = {row["trigger_occurrence_id"] for row in v2_occurrences if row["participant_set_key"] not in disposed_keys}
    require("TRANCHES_A_B_PARTITION_EXACT_25_OF_35", len(disposed_keys) == 25 and len(remaining_families) == 10 and disposed_keys | {row["participant_set_key"] for row in remaining_families} == set(family_by_key))
    require("TRANCHES_A_B_OCCURRENCE_PARTITION_EXACT_299_OF_359", len(disposed_ids) == 299 and len(remaining_ids) == 60 and disposed_ids.isdisjoint(remaining_ids) and disposed_ids | remaining_ids == set(occurrence_by_id))
    require("ALL_REMAINING_FAMILIES_ARITY4_OR_GREATER", all(int(row["arity"]) >= 4 for row in remaining_families), Counter(row["arity"] for row in remaining_families))
    cumulative = Counter(row["final_parent_disposition"] for row in tranche_a_families) + Counter(FAMILY_DISPOSITIONS.values())
    require("CUMULATIVE_PARENT_DISPOSITIONS_EXACT", dict(sorted(cumulative.items())) == EXPECTED_CUMULATIVE_COUNTS, dict(sorted(cumulative.items())))

    _, gap_rows = read_tsv(repo / GAP_OUTPUT)
    require("GAP_LEDGER_GAP017_024_EXACT_AND_HASHED", len(gap_rows) == 8 and [row["gap_id"] for row in gap_rows] == [f"GAP-{value:03d}" for value in range(17, 25)] and not verify_record_hashes(gap_rows))
    require("GAPS_RETAIN_CLOSURE_BLOCKERS", sum(row["severity"] == "CLOSURE_BLOCKING" for row in gap_rows) == 7 and any(row["status"] == "OPEN" for row in gap_rows))

    census = read_json(repo / CENSUS_OUTPUT)
    closure = census.get("closure", {})
    require("CENSUS_AUTHORITY_AND_COUNTS_EXACT", census.get("format") == "trace-round16b-evidence-disposition-tranche-b-census-v1" and census.get("builder_version") == BUILDER_VERSION and census.get("source_sha") == SOURCE_SHA and census.get("source_tree") == SOURCE_TREE and census.get("parent_checkpoint_sha") == PARENT_SHA and census.get("tranche_family_count") == 14 and census.get("tranche_linked_occurrence_count") == 187 and census.get("memo_queue_record_count") == 37)
    require("CENSUS_CLOSURE_KEYS_ALL_FALSE", set(closure) == EXPECTED_CLOSURE_KEYS and not any(closure.values()), closure)
    require("CENSUS_ZERO_ACTIVATION_METRICS", all(census.get(key) == 0 for key in ["association_identity_created_count", "association_activation_count", "pair_projection_created_count", "product_eligible_count", "active_pending_review_count"]))
    reconciliation = census.get("instruction_count_reconciliation", {})
    require("ARITHMETIC_CONTRADICTION_PRESERVED_FAIL_CLOSED", reconciliation.get("count_mismatch_detected") is True and reconciliation.get("earlier_summary_claims") == {"PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE": 4, "BOUNDED_SENSE_OR_SCOPE_CONFLICT": 7} and reconciliation.get("explicit_family_key_lists_and_exact_v2_rows") == {"PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE": 5, "BOUNDED_SENSE_OR_SCOPE_CONFLICT": 6} and reconciliation.get("resolution_status") == "FAIL_CLOSED_EXACT_LISTED_FAMILY_KEYS_AND_ROW_EVIDENCE_CONTROL")

    receipt = read_json(repo / BUILD_RECEIPT)
    output_hash_failures: dict[str, Any] = {}
    for relative, expected in receipt.get("output_hashes", {}).items():
        path = repo / relative
        actual = {"bytes": path.stat().st_size, "sha256": sha256_file(path)} if path.is_file() else {"bytes": -1, "sha256": "MISSING"}
        if actual != expected:
            output_hash_failures[relative] = {"expected": expected, "actual": actual}
    require("RECEIPT_OUTPUT_HASHES_EXACT", not output_hash_failures and set(receipt.get("output_hashes", {})) == EXPECTED_OUTPUTS, output_hash_failures)
    require("RECEIPT_AGGREGATE_HASH_EXACT", receipt.get("aggregate_output_sha256") == sha256_text(canonical_json(receipt.get("output_hashes", {}))))
    require("RECEIPT_INPUT_MANIFEST_HASH_EXACT", receipt.get("input_manifest_sha256") == sha256_file(repo / INPUT_MANIFEST))
    require("RECEIPT_FAIL_CLOSED_HEADLINE_EXACT", receipt.get("status") == "PASS_FAIL_CLOSED_TRANCHE_B" and receipt.get("family_count") == 14 and receipt.get("linked_occurrence_count") == 187 and receipt.get("memo_queue_record_count") == 37 and receipt.get("cumulative_disposed_family_count") == 25 and receipt.get("cumulative_disposed_occurrence_count") == 299 and receipt.get("remaining_undisposed_family_count") == 10 and receipt.get("remaining_undisposed_occurrence_count") == 60 and receipt.get("closure_flags_true_count") == 0)
    require("RESEARCH_NOTE_BOUND_TO_RECEIPT", sha256_file(repo / RESEARCH_NOTE) == receipt["output_hashes"][str(RESEARCH_NOTE)]["sha256"])

    payload = {
        "format": "trace-round16b-evidence-disposition-tranche-b-independent-verification-v1",
        "verifier_implementation": "standalone-no-builder-import-or-execution",
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "parent_checkpoint_sha": PARENT_SHA,
        "review_tranche": TRANCHE,
        "check_count": len(checks),
        "pass_count": sum(row["status"] == "PASS" for row in checks),
        "failure_count": len(failures),
        "failures": failures,
        "checks": checks,
        "reconstructed_metrics": {
            "family_count": len(out_families),
            "occurrence_count": len(out_occurrences),
            "queue_count": len(queue_rows),
            "cumulative_disposed_family_count": len(disposed_keys),
            "cumulative_disposed_occurrence_count": len(disposed_ids),
            "remaining_family_count": len(remaining_families),
            "remaining_occurrence_count": len(remaining_ids),
            "association_identity_created_count": 0,
            "association_activation_count": 0,
            "pair_projection_created_count": 0,
            "product_eligible_count": 0,
            "closure_flags_true_count": sum(bool(value) for value in closure.values()),
        },
        "status": "PASS" if not failures else "FAIL",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{payload['status']}: {payload['pass_count']}/{payload['check_count']} checks; output={output}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
