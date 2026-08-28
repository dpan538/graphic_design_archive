#!/usr/bin/env python3
"""Reconcile every governed Round 16A product-space object against Round 16B.

The 749,944 transition rows are classified from both endpoint states and are
streamed into 64 predeclared-LFS shards.  No Round 16A object is treated as a
higher-order association merely because it was renderable or pair-connected.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator


REPO = Path(__file__).resolve().parents[2]
RAW_REL = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw"
RAW = REPO / RAW_REL
REPORT_REL = (
    "docs/research/trace-v49-exploration-higher-order-association-closure-round16b/"
    "19_ROUND16A_GLOBAL_RECONCILIATION.md"
)
LARGE_REL = f"{RAW_REL}/large/round16a-transition-reconciliation-v1"

SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
AUTHORITY_BASE_SHA = "468105499c7be102deec7d6555aced688dea9901"
BUILDER_VERSION = "trace-round16b-round16a-global-reconciliation-builder-v1"

R16A_RAW = "docs/audits/v49-exploration-full-space-closure-round1/raw"
REGISTRY_PATH = f"{R16A_RAW}/canonical-composition-registry-v2.json"
ENUMERATION_PATH = f"{R16A_RAW}/composition-enumeration-v2.tsv"
REJECTION_PATH = f"{R16A_RAW}/composition-rejection-ledger-v2.tsv"
STATE_PATH = f"{R16A_RAW}/state-census-v2.tsv"
TRANSITION_PATH = f"{R16A_RAW}/transition-census-v2.tsv"
WORKFLOW_PATH = f"{R16A_RAW}/workflow-census-v2.tsv"
EXPORT_PATH = f"{R16A_RAW}/export-census-v2.tsv"
READ_MODEL_PATH = "frontend/generated/trace-exploration-v2/production-read-model.json"
LEGACY_SOURCE_PATH = "scripts/trace-v49-exploration-real-database/real-composition-registry-v1.json"

PRIOR_CORE_PATH = f"{RAW_REL}/prior-object-reconciliation-universe-v1-core.tsv"
PRIOR_STATES_PATH = f"{RAW_REL}/prior-object-reconciliation-universe-v1-states.tsv"
PRIOR_WORKFLOWS_PATH = f"{RAW_REL}/prior-object-reconciliation-universe-v1-workflows.tsv"
PRIOR_EXPORTS_PATH = f"{RAW_REL}/prior-object-reconciliation-universe-v1-exports.tsv"
PRIOR_SET_PATH = f"{RAW_REL}/prior-object-set-manifest-v1.tsv"
LOCAL_FAMILY_PATH = f"{RAW_REL}/local-candidate-family-ledger-v2.tsv"
TAXONOMY_PATH = f"{RAW_REL}/association-disposition-taxonomy.tsv"
FAMILY_PATHS = [
    f"{RAW_REL}/family-evidence-disposition-tranche-{value}-v1.tsv"
    for value in ("a", "b", "c")
]
CORRECTION_PATH = f"{RAW_REL}/source-scope-reconciliation-ledger-shard-2-v1.tsv"
VOCAB_IMPACT_PATH = f"{RAW_REL}/active-vocabulary-evidence-impact-ledger-shard-2-v1.tsv"

INPUT_MANIFEST_PATH = f"{RAW_REL}/round16a-global-reconciliation-input-manifest-v1.tsv"
FAMILY_IMPACT_PATH = f"{RAW_REL}/round16a-global-reconciliation-family-impact-v1.tsv"
MATRIX_PATH = f"{RAW_REL}/round16a-global-reconciliation-transition-endpoint-matrix-v1.tsv"
SHARD_MANIFEST_PATH = f"{RAW_REL}/round16a-global-reconciliation-transition-shard-manifest-v1.tsv"
OUTPUT_MANIFEST_PATH = f"{RAW_REL}/round16a-global-reconciliation-output-manifest-v1.tsv"
CENSUS_PATH = f"{RAW_REL}/round16a-global-reconciliation-census-v1.json"
RECEIPT_PATH = f"{RAW_REL}/round16a-global-reconciliation-build-receipt-v1.json"
GAP_PATH = f"{RAW_REL}/recursive-gap-ledger-round16a-global-reconciliation-v1.tsv"

OBJECT_OUTPUTS = {
    "ROUND16A_ASSOCIATION_SUBGRAPH": f"{RAW_REL}/round16a-global-reconciliation-subgraphs-v1.tsv",
    "ROUND16A_TOPOLOGY_COMPOSITION": f"{RAW_REL}/round16a-global-reconciliation-topologies-v1.tsv",
    "ROUND16A_CATEGORY_ENTRY": f"{RAW_REL}/round16a-global-reconciliation-categories-v1.tsv",
    "ROUND16A_SEED_VARIANT": f"{RAW_REL}/round16a-global-reconciliation-seeds-v1.tsv",
    "ROUND16A_PRODUCTION_COMPOSITION": f"{RAW_REL}/round16a-global-reconciliation-compositions-v1.tsv",
    "ROUND16A_STATE": f"{RAW_REL}/round16a-global-reconciliation-states-v1.tsv",
    "ROUND16A_WORKFLOW": f"{RAW_REL}/round16a-global-reconciliation-workflows-v1.tsv",
    "ROUND16A_EXPORT": f"{RAW_REL}/round16a-global-reconciliation-exports-v1.tsv",
    "ROUND16A_LEGACY_RECONCILIATION": f"{RAW_REL}/round16a-global-reconciliation-legacy-v1.tsv",
    "ROUND16A_TOPOLOGY_ENUMERATION_RESULT": f"{RAW_REL}/round16a-global-reconciliation-topology-attempts-v1.tsv",
    "ROUND16A_TOPOLOGY_REJECTION": f"{RAW_REL}/round16a-global-reconciliation-topology-rejections-v1.tsv",
}

PINNED_INPUT_SHA256 = {
    ".gitattributes": "39220b2b34b02184bc84ff293163c874819305b6cbf1005faac573d5bab48098",
    REGISTRY_PATH: "51c3e29909a8aa5226a7d18ebaef896aa52c48be6725d722c869515874c6c24d",
    ENUMERATION_PATH: "75efbe8f0e5d18d431b1e525900da6eb30ff6abe1a97d407058e637680ada2cd",
    REJECTION_PATH: "dc10dbb41a9e4492ca682507bfa9b46df318039f83f022e16b7b3f3d8d485951",
    READ_MODEL_PATH: "53eaf59c95446eeb3781a7153183c54b3ff59fd52f21744cc917053959dfdcc9",
    STATE_PATH: "35bf2057b0e24bdd951988361eea152c173ba0b69fefc10c656b402f4ee630a5",
    TRANSITION_PATH: "3a58b52f3c95fbc33ad992481ff55485b9a566418adc15daa1a39f86e9dd96a0",
    WORKFLOW_PATH: "66a70a7f4d67a2f7052bb6a7f6da10004de8218faec4b05fb8d8a52904131b28",
    EXPORT_PATH: "7e0e97e0c5848c34438705818fcb78bd1fc87bd705d238ea45e4cc4791f7f009",
    LEGACY_SOURCE_PATH: "cad6669c93a52924a17d31d07a16b1e1e5b0ffa06917f3cd467a5f2db003393f",
    PRIOR_CORE_PATH: "fd143cc01ec943967cd497efbfb341a994b4d08ed488cf47f1eb345b5845e713",
    PRIOR_STATES_PATH: "fab7057bb7c59feeb91a09d08fee55dd843cf2059dac683f89760a8a64354c87",
    PRIOR_WORKFLOWS_PATH: "991569c0e8ab1c8eca040877387db44bf67fb09359fabf7266ba8fb99d8373cc",
    PRIOR_EXPORTS_PATH: "d0e7ee1eb8c44b74ec50246509f686e023d5b3bc7f38aa479b8e199521d4b836",
    PRIOR_SET_PATH: "9e61df859f8266024920c03fd1f76c791d67fa50338362da3736457357ea7764",
    LOCAL_FAMILY_PATH: "cd4c3ca997c0f4cd5919d4e29d89ca45291fae4f70f78a49742aafb9c76baea7",
    TAXONOMY_PATH: "20248f9d62f672f88ce1aa691e059e6459747deb9674a3b600ac9959465b165d",
    FAMILY_PATHS[0]: "5e77187942e0815a0291c24374bbc389cd09a78d9165977f5e73a63fad7fe7f0",
    FAMILY_PATHS[1]: "1f6547e799963d14c45335569aaa9a5facf9eb1715afe6c462605acdae16a090",
    FAMILY_PATHS[2]: "560ac2574c3c0855387bfa423ece6ed99a17193771575c0014f2752a3fd820d5",
    CORRECTION_PATH: "38535b145bad9a73d53952bb9f43b313f7c72fad15331e2665467034ce5597c0",
    VOCAB_IMPACT_PATH: "22c9765705c197dd8b5e291d15a088377d71a37ef551fb3d6e73b73f15ad1b69",
}

FINAL_DISPOSITION_TO_OUTCOME = {
    "DIRECT_HIGHER_ORDER_SUPPORT": "RETAINED",
    "COHERENT_COMPOSITE_SUPPORT": "RETAINED",
    "MIXED_DIRECT_AND_COMPOSITE_SUPPORT": "RETAINED",
    "PAIRWISE_SUPPORT_WITHOUT_GROUP_COHERENCE": "CORRECTED",
    "INQUIRY_ONLY_OR_UNRESOLVED": "INQUIRY",
    "INSUFFICIENT_EVIDENCE": "REJECTED",
    "COOCCURRENCE_ONLY": "REJECTED",
    "BOUNDED_SENSE_OR_SCOPE_CONFLICT": "REJECTED",
    "TOPOLOGY_OR_ROLE_CONFLICT": "REJECTED",
    "HARD_NEGATIVE": "REJECTED",
    "DUPLICATE_IDENTITY_MERGED": "CORRECTED",
}
OUTCOME_SEVERITY = {"RETAINED": 0, "CORRECTED": 1, "INQUIRY": 2, "REJECTED": 3}
SEVERITY_OUTCOME = {value: key for key, value in OUTCOME_SEVERITY.items()}
FILE_HASH_CACHE: dict[str, str] = {}

OBJECT_FIELDS = [
    "authority_base_sha", "source_sha", "prior_object_type", "prior_id", "source_path",
    "source_file_sha256", "source_record_ref", "source_record_sha256", "participant_set_key",
    "participant_sense_ids_json", "candidate_ids_json", "candidate_final_dispositions_json",
    "upstream_object_ids_json", "prior_association_ids_json", "prior_status", "prior_topology",
    "reconciliation_outcome", "outcome_basis", "semantic_carry_forward_authorized",
    "active_fact_created", "product_eligible", "pair_projection_eligible",
    "required_next_action", "record_sha256",
]
TRANSITION_FIELDS = [
    "authority_base_sha", "source_sha", "shard_id", "prior_transition_id", "current_state_id",
    "current_state_hash", "current_state_reconciliation_outcome", "action", "target_id",
    "next_state_id", "next_state_hash", "next_state_reconciliation_outcome",
    "reconciliation_outcome", "outcome_severity_rule", "same_state", "baseline_executed",
    "baseline_passed", "baseline_state_mutated", "baseline_database_snapshot", "source_path",
    "source_file_sha256", "source_record_sha256", "semantic_carry_forward_authorized",
    "active_fact_created", "product_eligible", "required_next_action", "record_sha256",
]


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cached_sha256_file(relative: str) -> str:
    if relative not in FILE_HASH_CACHE:
        FILE_HASH_CACHE[relative] = sha256_file(REPO / relative)
    return FILE_HASH_CACHE[relative]


def row_hash(row: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(row).encode("utf-8"))


def id_set_hash(values: Iterable[str]) -> str:
    material = "".join(f"{value}\n" for value in sorted(values))
    return sha256_bytes(material.encode("utf-8"))


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def tsv_bytes(fields: list[str], rows: Iterable[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, dialect="excel-tab", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return stream.getvalue().encode("utf-8")


def serialized_tsv_row(fields: list[str], row: dict[str, Any]) -> bytes:
    values = [str(row.get(field, "")) for field in fields]
    if any("\t" in value or "\n" in value or "\r" in value for value in values):
        raise ValueError("streamed transition field contains a TSV control character")
    return ("\t".join(values) + "\n").encode("utf-8")


def read_tsv(relative: str) -> list[dict[str, str]]:
    with (REPO / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, dialect="excel-tab"))


def read_json(relative: str) -> Any:
    return json.loads((REPO / relative).read_text(encoding="utf-8"))


def file_record_count(relative: str) -> int:
    if relative.endswith(".tsv"):
        with (REPO / relative).open(encoding="utf-8", newline="") as handle:
            return max(0, sum(1 for _ in handle) - 1)
    return 1


def lower_bool(value: bool) -> str:
    return str(value).lower()


def verify_inputs() -> None:
    for relative, expected in PINNED_INPUT_SHA256.items():
        observed = cached_sha256_file(relative)
        if observed != expected:
            raise ValueError(f"pinned input drift: {relative}: {observed} != {expected}")
    attrs = (REPO / ".gitattributes").read_text(encoding="utf-8")
    required = f"{RAW_REL}/large/** filter=lfs diff=lfs merge=lfs -text"
    if required not in attrs:
        raise ValueError("the predeclared Round 16B large-artifact LFS rule is absent")


def load_families() -> dict[str, dict[str, str]]:
    local = {row["candidate_id"]: row for row in read_tsv(LOCAL_FAMILY_PATH)}
    taxonomy = {row["disposition"]: row for row in read_tsv(TAXONOMY_PATH)}
    final_rows = [row for path in FAMILY_PATHS for row in read_tsv(path)]
    final: dict[str, dict[str, str]] = {}
    for row in final_rows:
        candidate_id = row["candidate_id"]
        if candidate_id in final:
            raise ValueError(f"duplicate final family: {candidate_id}")
        if candidate_id not in local:
            raise ValueError(f"final family absent from governed universe: {candidate_id}")
        disposition = row["final_parent_disposition"]
        if disposition not in taxonomy or taxonomy[disposition]["status_class"] == "NONFINAL":
            raise ValueError(f"nonfinal or unknown governed disposition: {disposition}")
        if disposition not in FINAL_DISPOSITION_TO_OUTCOME:
            raise ValueError(f"unmapped governed disposition: {disposition}")
        if row["participant_set_key"] != local[candidate_id]["participant_set_key"]:
            raise ValueError(f"family participant-set drift: {candidate_id}")
        final[candidate_id] = row
    if set(final) != set(local):
        raise ValueError("the three final disposition tranches do not exactly cover local family v2")
    return final


def load_prior_rows() -> tuple[dict[tuple[str, str], dict[str, str]], dict[str, dict[str, str]]]:
    rows = [
        *read_tsv(PRIOR_CORE_PATH), *read_tsv(PRIOR_STATES_PATH),
        *read_tsv(PRIOR_WORKFLOWS_PATH), *read_tsv(PRIOR_EXPORTS_PATH),
    ]
    prior: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        key = (row["prior_object_type"], row["prior_id"])
        if key in prior:
            raise ValueError(f"duplicate prior object: {key}")
        prior[key] = row
    sets = {row["prior_object_type"]: row for row in read_tsv(PRIOR_SET_PATH)}
    return prior, sets


def validate_exact_set(object_type: str, rows: list[dict[str, str]], sets: dict[str, dict[str, str]]) -> None:
    ids = [row["prior_id"] for row in rows]
    authority = sets[object_type]
    if len(ids) != int(authority["record_count"]) or len(ids) != len(set(ids)):
        raise ValueError(f"prior object count/uniqueness mismatch: {object_type}")
    if id_set_hash(ids) != authority["sorted_id_set_sha256"]:
        raise ValueError(f"prior object identity-set mismatch: {object_type}")


def classify_prior(row: dict[str, str], families: dict[str, dict[str, str]]) -> tuple[str, str, list[str]]:
    senses = json.loads(row["participant_sense_ids_json"])
    candidates = json.loads(row["round16b_candidate_ids_json"])
    if len(senses) == 2:
        if candidates:
            raise ValueError(f"pair baseline unexpectedly linked to group family: {row['prior_id']}")
        return "RETAINED", "ROUND16A_ACTIVE_PAIR_BASELINE_NO_GROUP_CLAIM", []
    if len(senses) < 2 or len(candidates) != 1:
        raise ValueError(f"non-pair prior object lacks one exact family: {row['prior_id']}")
    candidate_id = candidates[0]
    family = families.get(candidate_id)
    if family is None:
        raise ValueError(f"prior object references nonfinal family: {candidate_id}")
    disposition = family["final_parent_disposition"]
    return FINAL_DISPOSITION_TO_OUTCOME[disposition], f"FAMILY_FINAL_DISPOSITION:{disposition}", [disposition]


def next_action(object_type: str, outcome: str) -> str:
    if object_type == "ROUND16A_TOPOLOGY_REJECTION":
        return "Preserve this exact prior topology-rejection receipt; the reconciliation outcome does not convert the rejected topology into a valid one."
    if object_type == "ROUND16A_TOPOLOGY_ENUMERATION_RESULT":
        return "Preserve the exact prior VALID/INVALID attempt while applying the independently derived semantic outcome; never equate topology validity with group support."
    return {
        "RETAINED": "Preserve the exact pair baseline without a manufactured group claim; regenerate any v3 product descendant before product activation.",
        "CORRECTED": "Preserve separately governed pair records, remove the unsupported group-coherence implication, and regenerate with corrected association provenance.",
        "INQUIRY": "Preserve as an explicitly inquiry-only baseline artifact; do not activate a product path while evidence or authority remains unresolved.",
        "REJECTED": "Preserve the audit receipt, retire the prior object from active product eligibility, and do not project or synthesize a replacement association.",
    }[outcome]


def object_record(row: dict[str, str], families: dict[str, dict[str, str]]) -> dict[str, str]:
    outcome, basis, dispositions = classify_prior(row, families)
    material = {
        "authority_base_sha": AUTHORITY_BASE_SHA,
        "source_sha": SOURCE_SHA,
        "prior_object_type": row["prior_object_type"],
        "prior_id": row["prior_id"],
        "source_path": row["source_path"],
        "source_file_sha256": cached_sha256_file(row["source_path"]),
        "source_record_ref": row["source_record_ref"],
        "source_record_sha256": row["record_sha256"],
        "participant_set_key": row["participant_set_key"],
        "participant_sense_ids_json": row["participant_sense_ids_json"],
        "candidate_ids_json": row["round16b_candidate_ids_json"],
        "candidate_final_dispositions_json": canonical_json(dispositions),
        "upstream_object_ids_json": row["prior_parent_ids_json"],
        "prior_association_ids_json": row["prior_association_ids_json"],
        "prior_status": row["prior_status"],
        "prior_topology": row["prior_topology"],
        "reconciliation_outcome": outcome,
        "outcome_basis": basis,
        "semantic_carry_forward_authorized": "false",
        "active_fact_created": "false",
        "product_eligible": "false",
        "pair_projection_eligible": "false",
        "required_next_action": next_action(row["prior_object_type"], outcome),
    }
    return {**material, "record_sha256": row_hash(material)}


def distribution(rows: Iterable[dict[str, str]]) -> dict[str, int]:
    return dict(sorted(Counter(row["reconciliation_outcome"] for row in rows).items()))


def shard_relative(index: int) -> str:
    start, end = index * 4, index * 4 + 3
    return f"{LARGE_REL}/round16a-transition-reconciliation-{start:02x}-{end:02x}-v1.tsv"


def transition_record(
    source: dict[str, str], state_outcomes: dict[str, str], state_hashes: dict[str, str]
) -> tuple[int, dict[str, str]]:
    transition_id = source["transition_id"]
    prefix = "R16A-TRANSITION-"
    suffix = transition_id.removeprefix(prefix)
    if not transition_id.startswith(prefix) or len(suffix) != 24 or suffix.upper() != suffix:
        raise ValueError(f"malformed transition identity: {transition_id}")
    try:
        shard = int(suffix[:2], 16) // 4
    except ValueError as exc:
        raise ValueError(f"malformed transition hex identity: {transition_id}") from exc
    current = source["current_state_id"]
    nxt = source["next_state_id"]
    if current not in state_outcomes or nxt not in state_outcomes:
        raise ValueError(f"transition endpoint absent from state census: {transition_id}")
    if state_hashes[current] != source["current_state_hash"] or state_hashes[nxt] != source["next_state_hash"]:
        raise ValueError(f"transition endpoint hash mismatch: {transition_id}")
    current_outcome = state_outcomes[current]
    next_outcome = state_outcomes[nxt]
    outcome = SEVERITY_OUTCOME[max(OUTCOME_SEVERITY[current_outcome], OUTCOME_SEVERITY[next_outcome])]
    material = {
        "authority_base_sha": AUTHORITY_BASE_SHA,
        "source_sha": SOURCE_SHA,
        "shard_id": f"R16B-R16A-TRANSITION-SHARD-{shard:02d}",
        "prior_transition_id": transition_id,
        "current_state_id": current,
        "current_state_hash": source["current_state_hash"],
        "current_state_reconciliation_outcome": current_outcome,
        "action": source["action"],
        "target_id": source["target_id"],
        "next_state_id": nxt,
        "next_state_hash": source["next_state_hash"],
        "next_state_reconciliation_outcome": next_outcome,
        "reconciliation_outcome": outcome,
        "outcome_severity_rule": "MAX_CURRENT_AND_NEXT_STATE_SEVERITY",
        "same_state": lower_bool(current == nxt),
        "baseline_executed": source["executed"],
        "baseline_passed": source["passed"],
        "baseline_state_mutated": source["state_mutated"],
        "baseline_database_snapshot": source["database_snapshot"],
        "source_path": TRANSITION_PATH,
        "source_file_sha256": PINNED_INPUT_SHA256[TRANSITION_PATH],
        "source_record_sha256": row_hash(source),
        "semantic_carry_forward_authorized": "false",
        "active_fact_created": "false",
        "product_eligible": "false",
        "required_next_action": "Regenerate transitions only after the v3 higher-order-aware reachable state space is frozen; this row is a complete baseline reconciliation receipt.",
    }
    return shard, {**material, "record_sha256": row_hash(material)}


def iter_transition_records(context: dict[str, Any]) -> Iterator[tuple[int, dict[str, str]]]:
    with (REPO / TRANSITION_PATH).open(encoding="utf-8", newline="") as handle:
        previous = ""
        for source in csv.DictReader(handle, dialect="excel-tab"):
            if previous and source["transition_id"] <= previous:
                raise ValueError("transition source is not strictly sorted and unique")
            previous = source["transition_id"]
            yield transition_record(source, context["state_outcomes"], context["state_hashes"])


def analyze_transitions(context: dict[str, Any]) -> dict[str, Any]:
    header = serialized_tsv_row(TRANSITION_FIELDS, {field: field for field in TRANSITION_FIELDS})
    shard_hashes = [hashlib.sha256(header) for _ in range(64)]
    shard_bytes = [len(header) for _ in range(64)]
    shard_counts = [0] * 64
    shard_id_hashes = [hashlib.sha256() for _ in range(64)]
    first_ids = [""] * 64
    last_ids = [""] * 64
    global_id_hash = hashlib.sha256()
    matrix: Counter[tuple[str, str]] = Counter()
    outcomes: Counter[str] = Counter()
    actions: Counter[str] = Counter()
    state_mutated: Counter[str] = Counter()
    same_state: Counter[str] = Counter()
    focus_total = focus_self = 0
    count = 0
    for shard, row in iter_transition_records(context):
        payload = serialized_tsv_row(TRANSITION_FIELDS, row)
        transition_id = row["prior_transition_id"]
        shard_hashes[shard].update(payload)
        shard_bytes[shard] += len(payload)
        shard_counts[shard] += 1
        shard_id_hashes[shard].update(f"{transition_id}\n".encode("utf-8"))
        first_ids[shard] = first_ids[shard] or transition_id
        last_ids[shard] = transition_id
        global_id_hash.update(f"{transition_id}\n".encode("utf-8"))
        matrix[(row["current_state_reconciliation_outcome"], row["next_state_reconciliation_outcome"])] += 1
        outcomes[row["reconciliation_outcome"]] += 1
        actions[row["action"]] += 1
        state_mutated[row["baseline_state_mutated"]] += 1
        same_state[row["same_state"]] += 1
        if row["action"] == "FOCUS_NODE":
            focus_total += 1
            focus_self += row["same_state"] == "true"
        count += 1
    authority = context["set_manifest"]["ROUND16A_TRANSITION"]
    if count != int(authority["record_count"]) or global_id_hash.hexdigest() != authority["sorted_id_set_sha256"]:
        raise ValueError("transition count or exact identity-set conservation failed")
    if any(value == 0 for value in shard_counts):
        raise ValueError("one or more deterministic transition shards are empty")
    expected_outcomes = {"CORRECTED": 195636, "INQUIRY": 281484, "REJECTED": 265032, "RETAINED": 7792}
    if dict(sorted(outcomes.items())) != expected_outcomes:
        raise ValueError(f"post-hoc transition outcome regression: {dict(outcomes)}")
    if state_mutated != Counter({"false": 749944}) or same_state != Counter({"false": 738188, "true": 11756}):
        raise ValueError("transition state-mutated/same-state regression")
    if focus_total != 18480 or focus_self != 5760:
        raise ValueError("FOCUS_NODE control regression")
    expected_matrix = {
        ("RETAINED", "RETAINED"): 7792, ("RETAINED", "CORRECTED"): 11280,
        ("RETAINED", "INQUIRY"): 6480, ("RETAINED", "REJECTED"): 6912,
        ("CORRECTED", "RETAINED"): 38448, ("CORRECTED", "CORRECTED"): 145908,
        ("CORRECTED", "INQUIRY"): 41472, ("CORRECTED", "REJECTED"): 46656,
        ("INQUIRY", "RETAINED"): 43920, ("INQUIRY", "CORRECTED"): 114312,
        ("INQUIRY", "INQUIRY"): 75300, ("INQUIRY", "REJECTED"): 58968,
        ("REJECTED", "RETAINED"): 25272, ("REJECTED", "CORRECTED"): 48600,
        ("REJECTED", "INQUIRY"): 33048, ("REJECTED", "REJECTED"): 45576,
    }
    if dict(matrix) != expected_matrix:
        raise ValueError("post-hoc transition endpoint-matrix regression")
    shards = []
    for index in range(64):
        shards.append({
            "shard_index": index,
            "shard_id": f"R16B-R16A-TRANSITION-SHARD-{index:02d}",
            "prefix_start": f"{index * 4:02x}",
            "prefix_end": f"{index * 4 + 3:02x}",
            "path": shard_relative(index),
            "record_count": shard_counts[index],
            "first_transition_id": first_ids[index],
            "last_transition_id": last_ids[index],
            "sorted_transition_id_set_sha256": shard_id_hashes[index].hexdigest(),
            "output_bytes": shard_bytes[index],
            "output_sha256": shard_hashes[index].hexdigest(),
        })
    return {
        "record_count": count,
        "sorted_id_set_sha256": global_id_hash.hexdigest(),
        "outcomes": dict(sorted(outcomes.items())),
        "actions": dict(sorted(actions.items())),
        "state_mutated": dict(sorted(state_mutated.items())),
        "same_state": dict(sorted(same_state.items())),
        "matrix": matrix,
        "focus_total": focus_total,
        "focus_self": focus_self,
        "shards": shards,
    }


def load_context() -> dict[str, Any]:
    verify_inputs()
    families = load_families()
    prior, sets = load_prior_rows()
    ledgers: dict[str, list[dict[str, str]]] = {}
    for object_type in OBJECT_OUTPUTS:
        source = [row for (kind, _), row in prior.items() if kind == object_type]
        validate_exact_set(object_type, source, sets)
        ledgers[object_type] = [object_record(row, families) for row in sorted(source, key=lambda value: value["prior_id"])]

    registry = read_json(REGISTRY_PATH)
    read_model = read_json(READ_MODEL_PATH)
    subgraphs = {row["association_subgraph_id"]: row for row in registry["association_subgraphs"]}
    topologies = {row["composition_id"]: row for row in registry["topology_compositions"]}
    categories = {row["category_entry_id"]: row for row in registry["category_entries"]}
    subgraph_outcomes = {row["prior_id"]: row["reconciliation_outcome"] for row in ledgers["ROUND16A_ASSOCIATION_SUBGRAPH"]}
    topology_outcomes = {row["prior_id"]: row["reconciliation_outcome"] for row in ledgers["ROUND16A_TOPOLOGY_COMPOSITION"]}
    category_outcomes = {row["prior_id"]: row["reconciliation_outcome"] for row in ledgers["ROUND16A_CATEGORY_ENTRY"]}
    seed_outcomes = {row["prior_id"]: row["reconciliation_outcome"] for row in ledgers["ROUND16A_SEED_VARIANT"]}
    composition_outcomes = {row["prior_id"]: row["reconciliation_outcome"] for row in ledgers["ROUND16A_PRODUCTION_COMPOSITION"]}

    for topology_id, topology in topologies.items():
        if topology_outcomes[topology_id] != subgraph_outcomes[topology["association_subgraph_id"]]:
            raise ValueError(f"topology/subgraph outcome mismatch: {topology_id}")
        for seed in topology["seed_variants"]:
            if seed_outcomes[seed["seed_id"]] != topology_outcomes[topology_id]:
                raise ValueError(f"seed/topology outcome mismatch: {seed['seed_id']}")
    for category_id, category in categories.items():
        if category_outcomes[category_id] != topology_outcomes[category["composition_id"]]:
            raise ValueError(f"category/topology outcome mismatch: {category_id}")
    for composition_id, composition in read_model["compositions"].items():
        if composition_outcomes[composition_id] != category_outcomes[composition["category_entry_id"]] or composition_outcomes[composition_id] != seed_outcomes[composition["seed_id"]]:
            raise ValueError(f"composition parent outcome mismatch: {composition_id}")

    state_source = {row["state_id"]: row for row in read_tsv(STATE_PATH)}
    state_outcomes = {row["prior_id"]: row["reconciliation_outcome"] for row in ledgers["ROUND16A_STATE"]}
    state_hashes = {state_id: row["state_hash"] for state_id, row in state_source.items()}
    for state_id, source in state_source.items():
        expected = composition_outcomes[source["composition_id"]]
        if state_outcomes[state_id] != expected or expected != category_outcomes[source["category_entry_id"]] or expected != seed_outcomes[source["seed_id"]]:
            raise ValueError(f"state parent outcome mismatch: {state_id}")

    workflow_source = {row["workflow_id"]: row for row in read_tsv(WORKFLOW_PATH)}
    workflow_outcomes = {row["prior_id"]: row["reconciliation_outcome"] for row in ledgers["ROUND16A_WORKFLOW"]}
    for workflow_id, source in workflow_source.items():
        outcome = composition_outcomes[source["composition_id"]]
        if workflow_outcomes[workflow_id] != outcome or outcome != state_outcomes[source["start_state_id"]] or outcome != state_outcomes[source["target_state_id"]]:
            raise ValueError(f"workflow endpoint outcome mismatch: {workflow_id}")
    export_source = {row["export_variant_id"]: row for row in read_tsv(EXPORT_PATH)}
    export_outcomes = {row["prior_id"]: row["reconciliation_outcome"] for row in ledgers["ROUND16A_EXPORT"]}
    for export_id, source in export_source.items():
        if export_outcomes[export_id] != composition_outcomes[source["composition_id"]] or composition_outcomes[source["composition_id"]] != state_outcomes[source["state_id"]]:
            raise ValueError(f"export state outcome mismatch: {export_id}")

    for attempt in read_tsv(ENUMERATION_PATH):
        prior_id = f"{attempt['association_subgraph_id']}|{attempt['topology_family']}"
        row = next(value for value in ledgers["ROUND16A_TOPOLOGY_ENUMERATION_RESULT"] if value["prior_id"] == prior_id)
        if row["reconciliation_outcome"] != subgraph_outcomes[attempt["association_subgraph_id"]]:
            raise ValueError(f"topology attempt outcome mismatch: {prior_id}")
    for rejection in read_tsv(REJECTION_PATH):
        row = next(value for value in ledgers["ROUND16A_TOPOLOGY_REJECTION"] if value["prior_id"] == rejection["rejection_id"])
        if row["reconciliation_outcome"] != subgraph_outcomes[rejection["association_subgraph_id"]]:
            raise ValueError(f"topology rejection outcome mismatch: {rejection['rejection_id']}")

    legacy_source_ids = {row["compositionId"] for row in read_json(LEGACY_SOURCE_PATH)["compositions"]}
    legacy_registry = {row["legacy_composition_id"]: row for row in registry["round16_legacy_reconciliation"]}
    if legacy_source_ids != set(legacy_registry):
        raise ValueError("legacy source/registry identity mismatch")
    legacy_outcomes = {row["prior_id"]: row["reconciliation_outcome"] for row in ledgers["ROUND16A_LEGACY_RECONCILIATION"]}
    for legacy_id, authority in legacy_registry.items():
        if authority["round16a_composition_id"] and legacy_outcomes[legacy_id] != topology_outcomes[authority["round16a_composition_id"]]:
            raise ValueError(f"legacy/topology outcome mismatch: {legacy_id}")

    corrections = read_tsv(CORRECTION_PATH)
    if len(corrections) != 1:
        raise ValueError("checkpoint009 source-scope correction cardinality drift")
    correction = corrections[0]
    required_correction = {
        "candidate_family_created": "false", "additive_disposition": "SOURCE_SCOPE_CONFLICT_QUARANTINE",
        "legacy_artifact_mutated": "false", "evidence_activation_eligible": "false",
        "product_eligible": "false", "pair_projection_eligible": "false",
    }
    if any(correction[key] != value for key, value in required_correction.items()):
        raise ValueError("checkpoint009 source correction lost its fail-closed boundary")
    impact = next(row for row in read_tsv(VOCAB_IMPACT_PATH) if row["canonical_label"] == "cultural transformation")
    correction_sense = impact["participant_sense_id"]
    if any(correction_sense in json.loads(row["participant_sense_ids_json"]) for row in ledgers["ROUND16A_ASSOCIATION_SUBGRAPH"]):
        raise ValueError("isolated corrected vocabulary unexpectedly entered the Round16A subgraph space")

    expected = {
        "ROUND16A_ASSOCIATION_SUBGRAPH": {"CORRECTED": 11, "INQUIRY": 18, "REJECTED": 8, "RETAINED": 21},
        "ROUND16A_TOPOLOGY_COMPOSITION": {"CORRECTED": 27, "INQUIRY": 15, "REJECTED": 18, "RETAINED": 21},
        "ROUND16A_CATEGORY_ENTRY": {"CORRECTED": 27, "INQUIRY": 15, "REJECTED": 18, "RETAINED": 21},
        "ROUND16A_SEED_VARIANT": {"CORRECTED": 81, "INQUIRY": 51, "REJECTED": 54, "RETAINED": 42},
        "ROUND16A_PRODUCTION_COMPOSITION": {"CORRECTED": 81, "INQUIRY": 51, "REJECTED": 54, "RETAINED": 42},
        "ROUND16A_STATE": {"CORRECTED": 1944, "INQUIRY": 2184, "REJECTED": 1296, "RETAINED": 336},
        "ROUND16A_WORKFLOW": {"CORRECTED": 1944, "INQUIRY": 2184, "REJECTED": 1296, "RETAINED": 336},
        "ROUND16A_EXPORT": {"CORRECTED": 3888, "INQUIRY": 4368, "REJECTED": 2592, "RETAINED": 672},
        "ROUND16A_LEGACY_RECONCILIATION": {"INQUIRY": 2, "REJECTED": 2, "RETAINED": 7},
        "ROUND16A_TOPOLOGY_ENUMERATION_RESULT": {"CORRECTED": 66, "INQUIRY": 108, "REJECTED": 48, "RETAINED": 126},
        "ROUND16A_TOPOLOGY_REJECTION": {"CORRECTED": 39, "INQUIRY": 103, "REJECTED": 30, "RETAINED": 105},
    }
    for object_type, wanted in expected.items():
        if distribution(ledgers[object_type]) != wanted:
            raise ValueError(f"post-hoc {object_type} reconciliation regression")
    return {
        "families": families, "set_manifest": sets, "ledgers": ledgers,
        "state_outcomes": state_outcomes, "state_hashes": state_hashes,
        "correction": correction, "correction_sense": correction_sense,
    }


def family_impact_rows(context: dict[str, Any]) -> list[dict[str, str]]:
    families = context["families"]
    ledgers = context["ledgers"]
    mapped = sorted({candidate for row in ledgers["ROUND16A_ASSOCIATION_SUBGRAPH"] for candidate in json.loads(row["candidate_ids_json"])})
    result = []
    for candidate_id in mapped:
        family = families[candidate_id]
        counts = {}
        for object_type, label in [
            ("ROUND16A_ASSOCIATION_SUBGRAPH", "subgraph_count"),
            ("ROUND16A_TOPOLOGY_ENUMERATION_RESULT", "topology_attempt_count"),
            ("ROUND16A_TOPOLOGY_REJECTION", "topology_rejection_count"),
            ("ROUND16A_TOPOLOGY_COMPOSITION", "topology_composition_count"),
            ("ROUND16A_CATEGORY_ENTRY", "category_count"), ("ROUND16A_SEED_VARIANT", "seed_count"),
            ("ROUND16A_PRODUCTION_COMPOSITION", "composition_count"), ("ROUND16A_STATE", "state_count"),
            ("ROUND16A_WORKFLOW", "workflow_count"), ("ROUND16A_EXPORT", "export_count"),
            ("ROUND16A_LEGACY_RECONCILIATION", "legacy_count"),
        ]:
            counts[label] = sum(candidate_id in json.loads(row["candidate_ids_json"]) for row in ledgers[object_type])
        material = {
            "authority_base_sha": AUTHORITY_BASE_SHA, "source_sha": SOURCE_SHA,
            "candidate_id": candidate_id, "participant_set_key": family["participant_set_key"],
            "participant_sense_ids_json": family["participant_sense_ids_json"],
            "canonical_labels_json": family["canonical_labels_json"], "arity": family["arity"],
            "final_parent_disposition": family["final_parent_disposition"],
            "global_coherence_status": family["global_coherence_status"],
            "reconciliation_outcome": FINAL_DISPOSITION_TO_OUTCOME[family["final_parent_disposition"]],
            **{key: str(value) for key, value in counts.items()},
            "checkpoint009_source_correction_overlap_count": lower_bool(context["correction_sense"] in json.loads(family["participant_sense_ids_json"])),
        }
        result.append({**material, "record_sha256": row_hash(material)})
    if len(result) != 9:
        raise ValueError("post-hoc mapped family count regression")
    return result


def build_report(census: dict[str, Any]) -> bytes:
    lines = [
        "# Round 16A global reconciliation under the Round 16B evidence model", "",
        f"Authority base: `{AUTHORITY_BASE_SHA}`. Authorized source: `{SOURCE_SHA}`.", "",
        "Every prior subgraph, topology attempt and rejection, topology composition, category, seed, production composition, state, transition, workflow, export, and legacy composition has an explicit outcome. `RETAINED` preserves a pair baseline, not a group claim. `CORRECTED` removes unsupported group coherence while preserving separately governed pairs. `INQUIRY` is product-ineligible. `REJECTED` remains an audit receipt.", "",
        "| Object | Retained | Corrected | Inquiry | Rejected | Total |", "|---|---:|---:|---:|---:|---:|",
    ]
    for name, values in census["main_object_distributions"].items():
        lines.append(f"| {name} | {values.get('RETAINED',0)} | {values.get('CORRECTED',0)} | {values.get('INQUIRY',0)} | {values.get('REJECTED',0)} | {sum(values.values())} |")
    lines.extend([
        "", f"The {census['transition_count']:,} transitions are partitioned into 64 first-byte-range LFS shards and classified by the maximum severity of both endpoint-state outcomes.", "",
        "Checkpoint 009's `COMP-EVID-018` scope correction changes none of these counts because `cultural transformation` has degree zero and appears in no Round 16A subgraph. It nevertheless remains a closure blocker and requires an independent support re-audit.", "",
        "All closure flags remain false. Product regeneration and independent verification are still pending.",
    ])
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_small_artifacts(context: dict[str, Any], transition: dict[str, Any]) -> tuple[dict[str, bytes], dict[str, int]]:
    ledgers = context["ledgers"]
    artifacts: dict[str, bytes] = {}
    record_counts: dict[str, int] = {}
    for object_type, path in OBJECT_OUTPUTS.items():
        artifacts[path] = tsv_bytes(OBJECT_FIELDS, ledgers[object_type])
        record_counts[path] = len(ledgers[object_type])

    family_rows = family_impact_rows(context)
    family_fields = list(family_rows[0])
    artifacts[FAMILY_IMPACT_PATH] = tsv_bytes(family_fields, family_rows)
    record_counts[FAMILY_IMPACT_PATH] = len(family_rows)

    matrix_rows = []
    for current in OUTCOME_SEVERITY:
        for nxt in OUTCOME_SEVERITY:
            derived = SEVERITY_OUTCOME[max(OUTCOME_SEVERITY[current], OUTCOME_SEVERITY[nxt])]
            material = {
                "current_state_reconciliation_outcome": current,
                "next_state_reconciliation_outcome": nxt,
                "transition_count": str(transition["matrix"][(current, nxt)]),
                "derived_reconciliation_outcome": derived,
                "outcome_severity_rule": "MAX_CURRENT_AND_NEXT_STATE_SEVERITY",
            }
            matrix_rows.append({**material, "record_sha256": row_hash(material)})
    artifacts[MATRIX_PATH] = tsv_bytes(list(matrix_rows[0]), matrix_rows)
    record_counts[MATRIX_PATH] = len(matrix_rows)

    shard_rows = []
    for shard in transition["shards"]:
        material = {
            "shard_id": shard["shard_id"], "prefix_start": shard["prefix_start"],
            "prefix_end": shard["prefix_end"], "path": shard["path"],
            "record_count": str(shard["record_count"]), "first_transition_id": shard["first_transition_id"],
            "last_transition_id": shard["last_transition_id"],
            "sorted_transition_id_set_sha256": shard["sorted_transition_id_set_sha256"],
            "output_bytes": str(shard["output_bytes"]), "output_sha256": shard["output_sha256"],
            "lfs_required": "true", "source_file_sha256": PINNED_INPUT_SHA256[TRANSITION_PATH],
        }
        shard_rows.append({**material, "record_sha256": row_hash(material)})
    artifacts[SHARD_MANIFEST_PATH] = tsv_bytes(list(shard_rows[0]), shard_rows)
    record_counts[SHARD_MANIFEST_PATH] = len(shard_rows)

    input_specs = [
        (path, "TSV_ROWS" if path.endswith(".tsv") else "PINNED_FILE")
        for path in PINNED_INPUT_SHA256
    ]
    input_rows = []
    for ordinal, (path, selector) in enumerate(input_specs, 1):
        input_rows.append({
            "ordinal": str(ordinal), "path": path, "selector": selector,
            "record_count": str(transition["record_count"] if path == TRANSITION_PATH else file_record_count(path)),
            "bytes": str((REPO / path).stat().st_size), "sha256": PINNED_INPUT_SHA256[path],
            "use_boundary": "EXACT_AUTHORITY_INPUT_NO_SEMANTIC_STATUS_INHERITED",
        })
    artifacts[INPUT_MANIFEST_PATH] = tsv_bytes(list(input_rows[0]), input_rows)
    record_counts[INPUT_MANIFEST_PATH] = len(input_rows)

    main_types = [
        "ROUND16A_ASSOCIATION_SUBGRAPH", "ROUND16A_TOPOLOGY_COMPOSITION", "ROUND16A_CATEGORY_ENTRY",
        "ROUND16A_SEED_VARIANT", "ROUND16A_PRODUCTION_COMPOSITION", "ROUND16A_STATE",
        "ROUND16A_WORKFLOW", "ROUND16A_EXPORT", "ROUND16A_LEGACY_RECONCILIATION",
    ]
    main_distributions = {kind: distribution(ledgers[kind]) for kind in main_types}
    main_totals = Counter()
    for values in main_distributions.values():
        main_totals.update(values)
    main_totals.update(transition["outcomes"])
    census = {
        "format": "trace-round16b-round16a-global-reconciliation-census-v1",
        "builder_version": BUILDER_VERSION, "authority_base_sha": AUTHORITY_BASE_SHA,
        "source_sha": SOURCE_SHA, "source_tree": SOURCE_TREE,
        "status": "PASS_WITH_OPEN_CLOSURE_BLOCKERS",
        "mapped_governed_family_count": len(family_rows),
        "main_object_distributions": main_distributions,
        "transition_outcome_distribution": transition["outcomes"],
        "main_object_total_distribution": dict(sorted(main_totals.items())),
        "main_object_count": sum(main_totals.values()),
        "topology_attempt_count": len(ledgers["ROUND16A_TOPOLOGY_ENUMERATION_RESULT"]),
        "topology_attempt_distribution": distribution(ledgers["ROUND16A_TOPOLOGY_ENUMERATION_RESULT"]),
        "topology_rejection_count": len(ledgers["ROUND16A_TOPOLOGY_REJECTION"]),
        "topology_rejection_distribution": distribution(ledgers["ROUND16A_TOPOLOGY_REJECTION"]),
        "reconciled_row_count_including_topology_audit_records": sum(main_totals.values()) + len(ledgers["ROUND16A_TOPOLOGY_ENUMERATION_RESULT"]) + len(ledgers["ROUND16A_TOPOLOGY_REJECTION"]),
        "transition_count": transition["record_count"],
        "transition_sorted_id_set_sha256": transition["sorted_id_set_sha256"],
        "transition_action_distribution": transition["actions"],
        "transition_same_state_distribution": transition["same_state"],
        "transition_baseline_state_mutated_distribution": transition["state_mutated"],
        "focus_node_transition_count": transition["focus_total"],
        "focus_node_self_transition_count": transition["focus_self"],
        "transition_shard_count": len(transition["shards"]),
        "transition_shard_record_count_min": min(row["record_count"] for row in transition["shards"]),
        "transition_shard_record_count_max": max(row["record_count"] for row in transition["shards"]),
        "checkpoint009_quarantined_source_scope_correction_count": 1,
        "checkpoint009_correction_round16a_subgraph_overlap_count": 0,
        "active_fact_created_count": 0, "product_activation_count": 0, "pair_projection_created_count": 0,
        "closure": {
            "pair_association_closure": False, "higher_order_association_closure": False,
            "global_composition_coherence_closure": False, "product_association_reachability_closure": False,
            "computational_space_closure": False, "function3_closure": False,
        },
    }
    if census["main_object_count"] != 773671 or census["reconciled_row_count_including_topology_audit_records"] != 774296:
        raise ValueError("global object-conservation total regression")
    artifacts[CENSUS_PATH] = json_bytes(census)
    record_counts[CENSUS_PATH] = 1

    gaps = [
        ("R16B-GLOBAL-GAP-001", "GROUP_COHERENCE", "11 Round16A subgraphs require corrected association provenance."),
        ("R16B-GLOBAL-GAP-002", "INQUIRY", "18 Round16A subgraphs remain inquiry-only and product-ineligible."),
        ("R16B-GLOBAL-GAP-003", "REJECTION", "8 Round16A subgraphs fail bounded sense or scope coherence."),
        ("R16B-GLOBAL-GAP-004", "SOURCE_SCOPE", "COMP-EVID-018 is quarantined and cultural-transformation support requires re-audit."),
        ("R16B-GLOBAL-GAP-005", "PRODUCT_REGENERATION", "The v3 reachable runtime, workflows, transitions, and exports remain to be regenerated."),
        ("R16B-GLOBAL-GAP-006", "INDEPENDENT_VERIFICATION", "Independent reconstruction and clean-worktree reproduction remain pending."),
    ]
    gap_rows = []
    for gap_id, gap_class, evidence in gaps:
        material = {
            "gap_id": gap_id, "gap_class": gap_class, "severity": "CLOSURE_BLOCKING", "status": "OPEN",
            "evidence": evidence, "required_action": "Resolve and independently verify before any closure decision.",
            "closure_effect": "ALL_CLOSURE_FLAGS_REMAIN_FALSE",
        }
        gap_rows.append({**material, "record_sha256": row_hash(material)})
    artifacts[GAP_PATH] = tsv_bytes(list(gap_rows[0]), gap_rows)
    record_counts[GAP_PATH] = len(gap_rows)
    artifacts[REPORT_REL] = build_report(census)
    record_counts[REPORT_REL] = 1

    output_rows = []
    payload_meta = {
        path: {"record_count": record_counts[path], "bytes": len(payload), "sha256": sha256_bytes(payload), "lfs_required": False}
        for path, payload in artifacts.items()
    }
    for shard in transition["shards"]:
        payload_meta[shard["path"]] = {"record_count": shard["record_count"], "bytes": shard["output_bytes"], "sha256": shard["output_sha256"], "lfs_required": True}
    for ordinal, path in enumerate(sorted(payload_meta), 1):
        meta = payload_meta[path]
        output_rows.append({
            "ordinal": str(ordinal), "path": path, "record_count": str(meta["record_count"]),
            "bytes": str(meta["bytes"]), "sha256": meta["sha256"],
            "lfs_required": lower_bool(meta["lfs_required"]),
        })
    artifacts[OUTPUT_MANIFEST_PATH] = tsv_bytes(list(output_rows[0]), output_rows)
    record_counts[OUTPUT_MANIFEST_PATH] = len(output_rows)
    aggregate = sha256_bytes(canonical_json([
        {"path": row["path"], "sha256": row["sha256"]} for row in output_rows
    ]).encode("utf-8"))
    receipt = {
        "format": "trace-round16b-round16a-global-reconciliation-build-receipt-v1",
        "builder_version": BUILDER_VERSION, "builder_sha256": sha256_file(Path(__file__)),
        "authority_base_sha": AUTHORITY_BASE_SHA, "source_sha": SOURCE_SHA, "source_tree": SOURCE_TREE,
        "status": "PASS_WITH_OPEN_CLOSURE_BLOCKERS", "input_count": len(input_rows),
        "output_count_excluding_receipt": len(output_rows) + 1,
        "output_manifest_sha256": sha256_bytes(artifacts[OUTPUT_MANIFEST_PATH]),
        "aggregate_output_sha256_excluding_manifest_and_receipt": aggregate,
        "main_object_count": census["main_object_count"],
        "reconciled_row_count_including_topology_audit_records": census["reconciled_row_count_including_topology_audit_records"],
        "transition_count": transition["record_count"], "transition_shard_count": len(transition["shards"]),
        "active_fact_created_count": 0, "product_activation_count": 0, "pair_projection_created_count": 0,
        "history_rewritten": False, "force_push_used": False, "rollback_tag_pushed": False,
        "origin_main_rewritten": False, "deployment_performed": False,
        "closure_flags_true_count": 0,
    }
    artifacts[RECEIPT_PATH] = json_bytes(receipt)
    record_counts[RECEIPT_PATH] = 1
    return artifacts, record_counts


def stream_shards(context: dict[str, Any], check: bool) -> list[str]:
    expected = {str(REPO / shard_relative(index)) for index in range(64)}
    shard_dir = REPO / LARGE_REL
    if shard_dir.exists():
        unexpected = {str(path) for path in shard_dir.glob("*.tsv")} - expected
        if unexpected:
            raise ValueError("unexpected transition shard files: " + ";".join(sorted(unexpected)))
    mismatches: set[str] = set()
    header = serialized_tsv_row(TRANSITION_FIELDS, {field: field for field in TRANSITION_FIELDS})
    current_index = -1
    handle: Any = None
    current_path: Path | None = None

    def close_current() -> None:
        nonlocal handle
        if handle is not None:
            if check and handle.read(1):
                mismatches.add(str(current_path.relative_to(REPO)))
            handle.close()
            handle = None

    def emit(payload: bytes) -> None:
        if handle is None:
            return
        if check:
            if handle.read(len(payload)) != payload:
                mismatches.add(str(current_path.relative_to(REPO)))
        else:
            handle.write(payload)

    for shard, row in iter_transition_records(context):
        if shard != current_index:
            close_current()
            if shard != current_index + 1:
                raise ValueError("transition shard stream is not contiguous")
            current_index = shard
            current_path = REPO / shard_relative(shard)
            if check:
                if current_path.exists():
                    handle = current_path.open("rb")
                else:
                    mismatches.add(str(current_path.relative_to(REPO)))
                    handle = None
            else:
                current_path.parent.mkdir(parents=True, exist_ok=True)
                handle = current_path.open("wb")
            emit(header)
        emit(serialized_tsv_row(TRANSITION_FIELDS, row))
    close_current()
    if current_index != 63:
        raise ValueError("transition stream did not materialize all 64 shards")
    return sorted(mismatches)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="compare deterministic bytes without rewriting artifacts")
    args = parser.parse_args()
    context = load_context()
    transition = analyze_transitions(context)
    artifacts, _ = build_small_artifacts(context, transition)
    failures = []
    for relative, payload in sorted(artifacts.items()):
        path = REPO / relative
        if args.check:
            if not path.exists() or path.read_bytes() != payload:
                failures.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    failures.extend(stream_shards(context, args.check))
    result = {
        "status": "PASS" if not failures else "FAIL", "mode": "CHECK" if args.check else "WRITE",
        "small_output_count": len(artifacts), "transition_shard_count": 64,
        "mismatch_count": len(set(failures)), "mismatches": sorted(set(failures)),
    }
    print(canonical_json(result))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
