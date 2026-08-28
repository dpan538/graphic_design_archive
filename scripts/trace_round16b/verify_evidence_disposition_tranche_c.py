#!/usr/bin/env python3
"""Independently verify Round 16B evidence-disposition tranche C.

This verifier does not import or invoke the tranche-C builder.  It reconstructs
family/occurrence coverage from the immutable candidate ledgers, enumerates
pair incidence with nested index loops, measures connectivity with union-find,
and checks every fail-closed boundary before writing a deterministic receipt.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw"
SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
PARENT_CHECKPOINT_SHA = "f97d20b37b58a509d04cdf3bc3385486fc8d173c"
VERIFIER_VERSION = "trace-round16b-evidence-disposition-tranche-c-independent-verifier-v1"

OCCURRENCE_UNIVERSE = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/candidate-trigger-occurrence-ledger-v2.tsv"
FAMILY_UNIVERSE = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/local-candidate-family-ledger-v2.tsv"
GRAPH_PATH = "docs/audits/v49-exploration-full-space-closure-round1/raw/validated-association-graph-v2.json"
CALIBRATION_PATH = "docs/audits/v49-exploration-association-calibration-round1/raw/association-calibration.tsv"

OCCURRENCE_PATHS = {
    "A": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-occurrence-disposition-tranche-a-v1.tsv",
    "B": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-occurrence-disposition-tranche-b-v1.tsv",
    "C": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-occurrence-disposition-tranche-c-v1.tsv",
}
FAMILY_PATHS = {
    "A": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/family-evidence-disposition-tranche-a-v1.tsv",
    "B": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/family-evidence-disposition-tranche-b-v1.tsv",
    "C": "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/family-evidence-disposition-tranche-c-v1.tsv",
}
QUEUE_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/scoped-higher-order-review-queue-tranche-c-v1.tsv"
INPUT_MANIFEST_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-input-manifest-tranche-c-v1.tsv"
GAP_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/recursive-gap-ledger-checkpoint007-tranche-c-v1.tsv"
CENSUS_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-census-tranche-c-v1.json"
BUILD_RECEIPT_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-build-receipt-tranche-c-v1.json"
SOURCE_HYPOTHESIS_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/scoped-association-hypothesis-ledger-shard-1-v1.tsv"
VERIFIER_PATH = "scripts/trace_round16b/verify_evidence_disposition_tranche_c.py"
OUTPUT_PATH = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-disposition-independent-verification-tranche-c-v1.json"

EXPECTED_FAMILIES = {
    "08555e0036d8fa72ac6454261ba70bfa4ad09988a59f17c92c3401fd0d1d907d": (4, 1, "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE"),
    "0c335e4ef6d612535b516a59ac96442d3cbf17affbbd517d57c6d74388f8fd2d": (4, 1, "BOUNDED_SENSE_OR_SCOPE_CONFLICT"),
    "89817e7a449f1cc7b574fb1b89c9541f765e52825c5cb62bf0a2bb833e8f970a": (4, 49, "INQUIRY_ONLY_OR_UNRESOLVED"),
    "9ba898462d422755c40d8ef6228e8a7faa6e74dd9b4b0499f82694e8ae4515da": (4, 3, "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE"),
    "d936154cb902968e2e5e0404e3dffaa3b61b47480b69f600b766b96351b66148": (5, 1, "INQUIRY_ONLY_OR_UNRESOLVED"),
    "5f28402103d5315b59cf0f022e43f679658b1e4d1e960072ae945a66c87d5669": (6, 1, "BOUNDED_SENSE_OR_SCOPE_CONFLICT"),
    "6bd3485742a465105a9adb73f09f1d700f9601abf114d49ba37d02cbbe0337f7": (6, 1, "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE"),
    "b2f6aef3aded759512be2f639056c7dacb37707ae596bf8c078035ccd5cd96d5": (6, 1, "HARD_NEGATIVE"),
    "ed83d4054c6d0fa7f02d620e5253572e58205ac5d7839b870b10748486883188": (6, 1, "HARD_NEGATIVE"),
    "3d978cc2b2ed5a65ad9841e04307657d41e0a23034f54b821fa59ce974e43e00": (8, 1, "BOUNDED_SENSE_OR_SCOPE_CONFLICT"),
}
SWEDEN_KEY = "89817e7a449f1cc7b574fb1b89c9541f765e52825c5cb62bf0a2bb833e8f970a"
HUTTON_KEY = "d936154cb902968e2e5e0404e3dffaa3b61b47480b69f600b766b96351b66148"
EXPECTED_CLIQUE_CONTROL_KEYS = {
    "7e0a0ee4f78d2f565c4f7771653ecc5a27828dd9fb704139d1e068f2a5fdce64",
    "1d76bf657bbdec293265d051268a2a1153be0108b15a8d63ebbf2cb98cf6f06a",
    "23b72032e8165ac9f164a43ac0e1932f2fe4354f1b89f62d67ebe7d497de7af1",
    "83009b1d124d4635a57866eeffba5e1a1a33e499bd60b30c6346b94ff1a04f8e",
    "af25d1d4c93f79886769d53d071805bd5b6726130b153e4484121321d1122e3a",
}
EXPECTED_C_DISTRIBUTION = {
    "BOUNDED_SENSE_OR_SCOPE_CONFLICT": 3,
    "HARD_NEGATIVE": 2,
    "INQUIRY_ONLY_OR_UNRESOLVED": 2,
    "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE": 3,
}
EXPECTED_CUMULATIVE_DISTRIBUTION = {
    "BOUNDED_SENSE_OR_SCOPE_CONFLICT": 14,
    "COOCCURRENCE_ONLY": 2,
    "HARD_NEGATIVE": 3,
    "INQUIRY_ONLY_OR_UNRESOLVED": 5,
    "INSUFFICIENT_EVIDENCE": 2,
    "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE": 8,
    "TOPOLOGY_OR_ROLE_CONFLICT": 1,
}
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
SURFACE_CLASS = {
    "R16B-LOCAL-SURF-R13-EVIDENCE": "R13_EXACT_EVIDENCE_RECORD",
    "R16B-LOCAL-SURF-R14-PROVENANCE": "R14_SHARED_LOCATOR_PROVENANCE",
    "R16B-LOCAL-SURF-R14-NARY": "R14_SYNTHETIC_NARY_CONTROL",
    "R16B-LOCAL-SURF-R15-FIXTURES": "R15_RESEARCH_FIXTURE",
    "R16B-LOCAL-SURF-R16A-SUBGRAPHS": "R16A_CONNECTED_SUBGRAPH",
    "R16B-LOCAL-SURF-R16A-TOPOLOGIES": "R16A_PRESENTATION_TOPOLOGY",
    "R16B-LOCAL-SURF-R16A-PRODUCTION": "R16A_PRODUCT_COMPOSITION",
    "R16B-LOCAL-SURF-R16-COMPOSITIONS": "R16_LEGACY_PRODUCT_COMPOSITION",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(relative: str) -> str:
    return digest_bytes((REPO / relative).read_bytes())


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def read_tsv(relative: str) -> list[dict[str, str]]:
    with (REPO / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, dialect="excel-tab"))


def read_json(relative: str) -> Any:
    return json.loads((REPO / relative).read_text(encoding="utf-8"))


def verify_record_hashes(rows: list[dict[str, str]], label: str) -> int:
    for ordinal, row in enumerate(rows, 1):
        stored = row.get("record_sha256", "")
        payload = {key: value for key, value in row.items() if key != "record_sha256"}
        actual = digest_bytes(canonical_json(payload).encode("utf-8"))
        if stored != actual:
            raise AssertionError(f"record hash mismatch: {label}:{ordinal}: {actual} != {stored}")
    return len(rows)


def nested_pairs(labels: list[str]) -> list[frozenset[str]]:
    pairs: list[frozenset[str]] = []
    left = 0
    while left < len(labels):
        right = left + 1
        while right < len(labels):
            pairs.append(frozenset((labels[left], labels[right])))
            right += 1
        left += 1
    return pairs


def union_find_component_count(labels: list[str], active_pairs: set[frozenset[str]]) -> int:
    parent = {label: label for label in labels}

    def root(label: str) -> str:
        while parent[label] != label:
            parent[label] = parent[parent[label]]
            label = parent[label]
        return label

    for pair in active_pairs:
        left, right = tuple(pair)
        left_root = root(left)
        right_root = root(right)
        if left_root != right_root:
            parent[right_root] = left_root
    return len({root(label) for label in labels})


def json_safe(value: Any) -> Any:
    if isinstance(value, (set, frozenset)):
        converted = [json_safe(item) for item in value]
        return sorted(converted, key=canonical_json)
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def check(name: str, observed: Any, expected: Any) -> dict[str, Any]:
    if observed != expected:
        raise AssertionError(f"{name}: observed={observed!r} expected={expected!r}")
    return {"check": name, "status": "PASS", "observed": json_safe(observed)}


def build_verification_receipt() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    occurrence_universe = read_tsv(OCCURRENCE_UNIVERSE)
    family_universe = read_tsv(FAMILY_UNIVERSE)
    occurrences_by_tranche = {key: read_tsv(path) for key, path in OCCURRENCE_PATHS.items()}
    families_by_tranche = {key: read_tsv(path) for key, path in FAMILY_PATHS.items()}
    queue = read_tsv(QUEUE_PATH)
    inputs = read_tsv(INPUT_MANIFEST_PATH)
    gaps = read_tsv(GAP_PATH)
    census = read_json(CENSUS_PATH)
    build_receipt = read_json(BUILD_RECEIPT_PATH)
    source_hypotheses = read_tsv(SOURCE_HYPOTHESIS_PATH)
    graph = read_json(GRAPH_PATH)
    calibration = read_tsv(CALIBRATION_PATH)

    checks.append(check("authorized_source_sha", build_receipt["source_sha"], SOURCE_SHA))
    checks.append(check("authorized_source_tree", build_receipt["source_tree"], SOURCE_TREE))
    checks.append(check("parent_checkpoint_sha", build_receipt["parent_checkpoint_sha"], PARENT_CHECKPOINT_SHA))
    checks.append(check("builder_status", build_receipt["status"], "PASS_FAIL_CLOSED_TRANCHE_C_LOCAL_PARENT_COVERAGE_ONLY"))
    checks.append(check("candidate_universe_family_count", len(family_universe), 35))
    checks.append(check("candidate_universe_occurrence_count", len(occurrence_universe), 359))
    checks.append(check("tranche_occurrence_counts", {key: len(value) for key, value in occurrences_by_tranche.items()}, {"A": 112, "B": 187, "C": 60}))
    checks.append(check("tranche_family_counts", {key: len(value) for key, value in families_by_tranche.items()}, {"A": 11, "B": 14, "C": 10}))

    universe_occurrence_by_id = {row["trigger_occurrence_id"]: row for row in occurrence_universe}
    universe_family_by_key = {row["participant_set_key"]: row for row in family_universe}
    checks.append(check("candidate_occurrence_id_uniqueness", len(universe_occurrence_by_id), 359))
    checks.append(check("candidate_family_key_uniqueness", len(universe_family_by_key), 35))

    all_disposition_occurrence_ids: list[str] = []
    all_disposition_family_keys: list[str] = []
    for tranche in ("A", "B", "C"):
        all_disposition_occurrence_ids.extend(row["trigger_occurrence_id"] for row in occurrences_by_tranche[tranche])
        all_disposition_family_keys.extend(row["participant_set_key"] for row in families_by_tranche[tranche])
    checks.append(check("cumulative_occurrence_row_count", len(all_disposition_occurrence_ids), 359))
    checks.append(check("cumulative_occurrence_disjoint_union", len(set(all_disposition_occurrence_ids)), 359))
    checks.append(check("cumulative_occurrence_universe_equality", set(all_disposition_occurrence_ids), set(universe_occurrence_by_id)))
    checks.append(check("cumulative_family_row_count", len(all_disposition_family_keys), 35))
    checks.append(check("cumulative_family_disjoint_union", len(set(all_disposition_family_keys)), 35))
    checks.append(check("cumulative_family_universe_equality", set(all_disposition_family_keys), set(universe_family_by_key)))

    c_families = {row["participant_set_key"]: row for row in families_by_tranche["C"]}
    c_occurrences = {row["trigger_occurrence_id"]: row for row in occurrences_by_tranche["C"]}
    checks.append(check("tranche_c_exact_family_keys", set(c_families), set(EXPECTED_FAMILIES)))
    independently_selected_ids: set[str] = set()
    for key, (arity, count, disposition) in EXPECTED_FAMILIES.items():
        source_family = universe_family_by_key[key]
        direct_ids = {row["trigger_occurrence_id"] for row in occurrence_universe if row["participant_set_key"] == key}
        family_ids = set(json.loads(source_family["trigger_occurrence_ids_json"]))
        checks.append(check(f"family_join_{key[:8]}", direct_ids, family_ids))
        checks.append(check(f"family_arity_{key[:8]}", int(source_family["arity"]), arity))
        checks.append(check(f"family_occurrence_count_{key[:8]}", len(direct_ids), count))
        checks.append(check(f"family_disposition_{key[:8]}", c_families[key]["final_parent_disposition"], disposition))
        independently_selected_ids.update(direct_ids)
    checks.append(check("tranche_c_occurrence_join_equality", set(c_occurrences), independently_selected_ids))
    checks.append(check("tranche_c_parent_distribution", dict(Counter(row["final_parent_disposition"] for row in c_families.values())), EXPECTED_C_DISTRIBUTION))
    cumulative_distribution = dict(Counter(row["final_parent_disposition"] for tranche in families_by_tranche.values() for row in tranche))
    checks.append(check("cumulative_parent_distribution", cumulative_distribution, EXPECTED_CUMULATIVE_DISTRIBUTION))

    source_counts = Counter()
    for occurrence_id in sorted(independently_selected_ids):
        input_surface = universe_occurrence_by_id[occurrence_id]["input_surface_id"]
        if input_surface not in SURFACE_CLASS:
            raise AssertionError(f"independent source-class mapping missing: {input_surface}")
        source_counts[SURFACE_CLASS[input_surface]] += 1
        generated = c_occurrences[occurrence_id]
        checks.append(check(f"occurrence_source_join_{occurrence_id[-12:]}", generated["source_occurrence_sha256"], universe_occurrence_by_id[occurrence_id]["occurrence_sha256"]))
    checks.append(check("tranche_c_independent_source_class_counts", dict(source_counts), EXPECTED_SOURCE_CLASS_COUNTS))
    checks.append(check("tranche_c_reported_source_class_counts", dict(Counter(row["occurrence_source_class"] for row in c_occurrences.values())), EXPECTED_SOURCE_CLASS_COUNTS))

    active_edges_by_pair = {frozenset((edge["label_a"], edge["label_b"])): edge for edge in graph["edges"]}
    if len(active_edges_by_pair) != len(graph["edges"]):
        raise AssertionError("active graph contains duplicate endpoint pairs")

    def reconstruct_pair_control(key: str) -> tuple[int, int, int, set[frozenset[str]]]:
        labels = json.loads(universe_family_by_key[key]["canonical_labels_json"])
        possible = nested_pairs(labels)
        active = {pair for pair in possible if pair in active_edges_by_pair}
        components = union_find_component_count(labels, active)
        return len(active), len(possible), components, active

    sweden_active, sweden_possible, sweden_components, sweden_pairs = reconstruct_pair_control(SWEDEN_KEY)
    checks.append(check("sweden_active_pair_count", sweden_active, 5))
    checks.append(check("sweden_possible_pair_count", sweden_possible, 6))
    checks.append(check("sweden_active_pair_graph_components", sweden_components, 1))
    missing_sweden = set(nested_pairs(json.loads(universe_family_by_key[SWEDEN_KEY]["canonical_labels_json"]))) - sweden_pairs
    checks.append(check("sweden_only_missing_pair", missing_sweden, {frozenset(("exhibition", "trade"))}))
    checks.append(check("sweden_reported_active_pair_count", int(c_families[SWEDEN_KEY]["internal_active_pair_count"]), 5))

    hutton_active, hutton_possible, hutton_components, _ = reconstruct_pair_control(HUTTON_KEY)
    checks.append(check("hutton_active_pair_count", hutton_active, 4))
    checks.append(check("hutton_possible_pair_count", hutton_possible, 10))
    checks.append(check("hutton_active_pair_graph_components", hutton_components, 2))
    checks.append(check("hutton_reported_pair_and_component_counts", [int(c_families[HUTTON_KEY]["internal_active_pair_count"]), int(c_families[HUTTON_KEY]["active_pair_graph_component_count"])], [4, 2]))

    prior_families = families_by_tranche["A"] + families_by_tranche["B"]
    clique_controls = {
        row["participant_set_key"]
        for row in prior_families
        if int(row["internal_possible_pair_count"]) == int(row["internal_active_pair_count"])
        and row["association_activation_status"] != "ACTIVE"
        and row["final_parent_disposition"] in {
            "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE",
            "INQUIRY_ONLY_OR_UNRESOLVED",
            "BOUNDED_SENSE_OR_SCOPE_CONFLICT",
        }
    }
    checks.append(check("inherited_pairwise_clique_invalid_keys", clique_controls, EXPECTED_CLIQUE_CONTROL_KEYS))
    checks.append(check("inherited_pairwise_clique_invalid_count", len(clique_controls), 5))

    hard_negative_by_pair = {
        frozenset((row["node_a"], row["node_b"])): row
        for row in calibration
        if row["hard_negative"] == "true"
    }
    for key, expected_count in {
        "b2f6aef3aded759512be2f639056c7dacb37707ae596bf8c078035ccd5cd96d5": 3,
        "ed83d4054c6d0fa7f02d620e5253572e58205ac5d7839b870b10748486883188": 2,
        "3d978cc2b2ed5a65ad9841e04307657d41e0a23034f54b821fa59ce974e43e00": 5,
    }.items():
        labels = json.loads(universe_family_by_key[key]["canonical_labels_json"])
        count = sum(1 for pair in nested_pairs(labels) if pair in hard_negative_by_pair)
        checks.append(check(f"independent_hard_negative_count_{key[:8]}", count, expected_count))
        checks.append(check(f"reported_hard_negative_count_{key[:8]}", int(c_families[key]["internal_hard_negative_pair_count"]), expected_count))

    identity_rows = [row for row in queue if row["association_identity_created"] == "true"]
    expected_identity_parents = {"R16B-LOCAL-FAMILY:" + SWEDEN_KEY, "R16B-LOCAL-FAMILY:" + HUTTON_KEY}
    checks.append(check("scoped_inquiry_identity_count", len(identity_rows), 2))
    checks.append(check("scoped_inquiry_identity_parents", {row["parent_candidate_id"] for row in identity_rows}, expected_identity_parents))
    checks.append(check("scoped_identity_id_uniqueness", len({row["association_id"] for row in identity_rows}), 2))
    checks.append(check("scoped_identity_id_format", all(re.fullmatch(r"R16B-ASSOC:[0-9a-f]{64}", row["association_id"]) is not None and re.fullmatch(r"R16B-ASSOC-REV:[0-9a-f]{64}", row["association_revision_id"]) is not None for row in identity_rows), True))
    checks.append(check("scoped_identity_inquiry_only", all(row["association_activation_status"] == "INQUIRY_ONLY" for row in identity_rows), True))
    checks.append(check("scoped_identity_human_review_open", all(row["human_review_status"] == "OPEN_EXTERNAL_DESIGN_HISTORY_REVIEW" for row in identity_rows), True))

    governed_source_hypotheses = [row for row in source_hypotheses if row["governed_association_id"]]
    queue_identity_map = {
        row["parent_candidate_id"]: {
            "association_id": row["association_id"],
            "association_revision_id": row["association_revision_id"],
            "scope_key": row["scope_key"],
            "participant_labels_json": row["participant_labels_json"],
            "participant_sense_ids_json": row["participant_sense_ids_json"],
        }
        for row in identity_rows
    }
    source_identity_map = {
        row["linked_parent_candidate_id"]: {
            "association_id": row["governed_association_id"],
            "association_revision_id": row["governed_association_revision_id"],
            "scope_key": row["scope_key"],
            "participant_labels_json": row["participant_labels_json"],
            "participant_sense_ids_json": row["participant_sense_ids_json"],
        }
        for row in governed_source_hypotheses
    }
    checks.append(check("source_shard_governed_identity_count", len(governed_source_hypotheses), 2))
    checks.append(check("source_shard_canonical_identity_equality", source_identity_map, queue_identity_map))
    checks.append(check("source_shard_canonical_authority_path", {row["canonical_identity_authority_path"] for row in governed_source_hypotheses}, {QUEUE_PATH}))
    checks.append(check("source_shard_canonical_queue_refs", {row["canonical_identity_queue_ref"] for row in governed_source_hypotheses}, {"TCQ-003", "TCQ-006"}))
    checks.append(check("source_shard_identity_inquiry_only", all(row["governed_identity_status"] == "INQUIRY_ONLY" and row["external_human_review_status"] == "OPEN" and row["association_activation_status"] == "INACTIVE" and row["active_fact_created"] == "false" for row in governed_source_hypotheses), True))
    checks.append(check("source_shard_no_projection_or_product", any(int(row["pair_projection_count"]) or int(row["subset_projection_count"]) or not row["product_eligibility"].startswith("INELIGIBLE") for row in source_hypotheses), False))
    checks.append(check("queue_no_active_association", any(row["association_activation_status"] == "ACTIVE" for row in queue), False))
    checks.append(check("queue_no_pair_projection", any(row["pair_projection_created"] != "false" or row["pair_projection_policy"] != "NONE" for row in queue), False))
    checks.append(check("queue_no_subset_projection", any(row["subset_projection_created"] != "false" for row in queue), False))
    checks.append(check("queue_no_product_path", any(row["product_path_created"] != "false" or row["product_eligibility"] != "INELIGIBLE" for row in queue), False))
    checks.append(check("family_no_active_association", any(row["association_activation_status"] == "ACTIVE" for row in c_families.values()), False))
    checks.append(check("family_no_pair_projection", any(int(row["pair_projection_count"]) != 0 for row in c_families.values()), False))
    checks.append(check("family_no_product_eligibility", any(row["product_eligibility"] != "INELIGIBLE" for row in c_families.values()), False))
    checks.append(check("occurrence_no_activation_or_projection", any(row["association_activation_created"] != "false" or row["pair_projection_created"] != "false" for row in c_occurrences.values()), False))
    checks.append(check("active_pending_review_count", sum(1 for row in c_families.values() if row["association_activation_status"] == "ACTIVE" and "OPEN" in row["human_review_status"]), 0))

    checks.append(check("queue_record_count", len(queue), 12))
    checks.append(check("gap_record_count", len(gaps), 8))
    checks.append(check("input_manifest_record_count", len(inputs), 24))
    checks.append(check("input_manifest_unique_paths", len({row["path"] for row in inputs}), 24))
    for row in inputs:
        checks.append(check(f"input_pin_{row['input_ordinal']}", [row["pin_match"], row["sha256"], digest_file(row["path"])], ["true", row["pinned_sha256"], row["pinned_sha256"]]))

    record_hash_count = 0
    for label, rows in [
        ("tranche_c_occurrences", list(c_occurrences.values())),
        ("tranche_c_families", list(c_families.values())),
        ("tranche_c_queue", queue),
        ("tranche_c_inputs", inputs),
        ("tranche_c_gaps", gaps),
    ]:
        record_hash_count += verify_record_hashes(rows, label)
    checks.append(check("record_hash_row_count", record_hash_count, 114))

    for relative, metadata in build_receipt["output_hashes"].items():
        payload = (REPO / relative).read_bytes()
        checks.append(check(f"builder_output_hash_{Path(relative).name}", [len(payload), digest_bytes(payload)], [metadata["bytes"], metadata["sha256"]]))
    checks.append(check("builder_aggregate_output_hash", digest_bytes(canonical_json(build_receipt["output_hashes"]).encode("utf-8")), build_receipt["aggregate_output_sha256"]))

    checks.append(check("local_parent_disposition_coverage", census["cumulative_tranche_a_b_c"]["local_parent_disposition_coverage"], True))
    checks.append(check("remaining_local_families", census["cumulative_tranche_a_b_c"]["remaining_undisposed_local_family_count"], 0))
    checks.append(check("remaining_local_occurrences", census["cumulative_tranche_a_b_c"]["remaining_undisposed_local_occurrence_count"], 0))
    checks.append(check("candidate_universe_closure_false", census["cumulative_tranche_a_b_c"]["candidate_universe_closure"], False))
    checks.append(check("all_closure_flags_false", all(value is False for value in census["closure"].values()), True))
    checks.append(check("build_receipt_closure_flags_true_count", build_receipt["closure_flags_true_count"], 0))
    checks.append(check("build_receipt_active_association_count", build_receipt["active_association_count"], 0))
    checks.append(check("build_receipt_projection_and_product_counts", [build_receipt["pair_projection_created_count"], build_receipt["subset_projection_created_count"], build_receipt["product_path_created_count"], build_receipt["product_eligible_count"]], [0, 0, 0, 0]))

    if not checks or any(item["status"] != "PASS" for item in checks):
        raise AssertionError("independent verification did not pass every check")
    return {
        "format": "trace-round16b-evidence-disposition-independent-verification-tranche-c-v1",
        "verifier_version": VERIFIER_VERSION,
        "verifier_independence": {
            "imports_builder": False,
            "calls_builder": False,
            "family_occurrence_join": "DIRECT_OCCURRENCE_LEDGER_PARTICIPANT_SET_JOIN",
            "pair_enumeration": "NESTED_INDEX_LOOPS",
            "connectivity": "UNION_FIND",
        },
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "parent_checkpoint_sha": PARENT_CHECKPOINT_SHA,
        "verified_build_receipt_path": BUILD_RECEIPT_PATH,
        "verified_build_receipt_sha256": digest_file(BUILD_RECEIPT_PATH),
        "verified_source_hypothesis_ledger_path": SOURCE_HYPOTHESIS_PATH,
        "verified_source_hypothesis_ledger_sha256": digest_file(SOURCE_HYPOTHESIS_PATH),
        "verifier_path": VERIFIER_PATH,
        "verifier_sha256": digest_file(VERIFIER_PATH),
        "check_count": len(checks),
        "pass_count": len(checks),
        "failure_count": 0,
        "verified_counts": {
            "local_candidate_families": 35,
            "local_trigger_occurrences": 359,
            "tranche_c_families": 10,
            "tranche_c_occurrences": 60,
            "scoped_inquiry_identities": 2,
            "active_associations": 0,
            "active_pending_review": 0,
            "pair_projections": 0,
            "subset_projections": 0,
            "product_paths": 0,
            "closure_flags_true": 0,
        },
        "control_results": {
            "inherited_pairwise_clique_invalid_parent_count": 5,
            "sweden_active_pairs": 5,
            "sweden_possible_pairs": 6,
            "sweden_missing_pair": ["exhibition", "trade"],
            "hutton_active_pairs": 4,
            "hutton_possible_pairs": 10,
            "hutton_active_pair_graph_components": 2,
            "hard_negative_parent_controls": 2,
            "no_projection": True,
        },
        "checks": checks,
        "status": "PASS_INDEPENDENT_FAIL_CLOSED_TRANCHE_C_LOCAL_PARENT_COVERAGE_ONLY",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="compare generated receipt with the materialized receipt")
    args = parser.parse_args()
    payload = json_bytes(build_verification_receipt())
    output = REPO / OUTPUT_PATH
    if args.check:
        if not output.exists() or output.read_bytes() != payload:
            raise SystemExit("deterministic verification receipt mismatch")
        print(canonical_json({"status": "PASS", "mode": "CHECK", "output": OUTPUT_PATH}))
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    print(output.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
