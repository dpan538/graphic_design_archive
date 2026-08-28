#!/usr/bin/env python3
"""Independent verifier for the Round 16A global reconciliation.

The verifier does not import or execute the primary builder.  It reconstructs
the generic object ledgers from the frozen prior-object universe, reconstructs
all 749,944 transition rows from the Round 16A transition census and both
endpoint-state outcomes, and compares every governed output byte-for-byte.

Default mode writes only the independent-verification receipt.  ``--check`` is
fully read-only and requires that receipt to reproduce byte-for-byte.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator


REPO = Path(__file__).resolve().parents[2]
RAW_REL = "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw"
R16A_RAW = "docs/audits/v49-exploration-full-space-closure-round1/raw"
REPORT_REL = (
    "docs/research/trace-v49-exploration-higher-order-association-closure-round16b/"
    "19_ROUND16A_GLOBAL_RECONCILIATION.md"
)
LARGE_REL = f"{RAW_REL}/large/round16a-transition-reconciliation-v1"

SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
AUTHORITY_BASE_SHA = "468105499c7be102deec7d6555aced688dea9901"
BUILDER_VERSION = "trace-round16b-round16a-global-reconciliation-builder-v1"
VERIFIER_VERSION = "trace-round16b-round16a-global-reconciliation-independent-verifier-v1"

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
BUILD_RECEIPT_PATH = f"{RAW_REL}/round16a-global-reconciliation-build-receipt-v1.json"
GAP_PATH = f"{RAW_REL}/recursive-gap-ledger-round16a-global-reconciliation-v1.tsv"
INDEPENDENT_RECEIPT_PATH = f"{RAW_REL}/round16a-global-reconciliation-independent-verification-v1.json"
BUILDER_PATH = "scripts/trace_round16b/build_round16a_global_reconciliation.py"

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

# This order is part of the primary input-manifest contract.
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
OUTCOMES = ("RETAINED", "CORRECTED", "INQUIRY", "REJECTED")
SEVERITY = {value: index for index, value in enumerate(OUTCOMES)}
BY_SEVERITY = {value: key for key, value in SEVERITY.items()}

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
FAMILY_FIELDS = [
    "authority_base_sha", "source_sha", "candidate_id", "participant_set_key",
    "participant_sense_ids_json", "canonical_labels_json", "arity",
    "final_parent_disposition", "global_coherence_status", "reconciliation_outcome",
    "subgraph_count", "topology_attempt_count", "topology_rejection_count",
    "topology_composition_count", "category_count", "seed_count", "composition_count",
    "state_count", "workflow_count", "export_count", "legacy_count",
    "checkpoint009_source_correction_overlap_count", "record_sha256",
]
MATRIX_FIELDS = [
    "current_state_reconciliation_outcome", "next_state_reconciliation_outcome",
    "transition_count", "derived_reconciliation_outcome", "outcome_severity_rule",
    "record_sha256",
]
SHARD_MANIFEST_FIELDS = [
    "shard_id", "prefix_start", "prefix_end", "path", "record_count",
    "first_transition_id", "last_transition_id", "sorted_transition_id_set_sha256",
    "output_bytes", "output_sha256", "lfs_required", "source_file_sha256",
    "record_sha256",
]
INPUT_MANIFEST_FIELDS = [
    "ordinal", "path", "selector", "record_count", "bytes", "sha256", "use_boundary",
]
OUTPUT_MANIFEST_FIELDS = [
    "ordinal", "path", "record_count", "bytes", "sha256", "lfs_required",
]
GAP_FIELDS = [
    "gap_id", "gap_class", "severity", "status", "evidence", "required_action",
    "closure_effect", "record_sha256",
]

EXPECTED_DISTRIBUTIONS = {
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
EXPECTED_MATRIX = {
    ("RETAINED", "RETAINED"): 7792,
    ("RETAINED", "CORRECTED"): 11280,
    ("RETAINED", "INQUIRY"): 6480,
    ("RETAINED", "REJECTED"): 6912,
    ("CORRECTED", "RETAINED"): 38448,
    ("CORRECTED", "CORRECTED"): 145908,
    ("CORRECTED", "INQUIRY"): 41472,
    ("CORRECTED", "REJECTED"): 46656,
    ("INQUIRY", "RETAINED"): 43920,
    ("INQUIRY", "CORRECTED"): 114312,
    ("INQUIRY", "INQUIRY"): 75300,
    ("INQUIRY", "REJECTED"): 58968,
    ("REJECTED", "RETAINED"): 25272,
    ("REJECTED", "CORRECTED"): 48600,
    ("REJECTED", "INQUIRY"): 33048,
    ("REJECTED", "REJECTED"): 45576,
}
EXPECTED_TRANSITION_OUTCOMES = {
    "CORRECTED": 195636, "INQUIRY": 281484, "REJECTED": 265032, "RETAINED": 7792,
}
EXPECTED_ACTIONS = {
    "COLLAPSE_NODE": 9240, "EXPAND_NODE": 8112, "EXPORT_CURRENT_STATE": 5760,
    "FOCUS_NODE": 18480, "MOVE_FOCUS": 7824, "RESET_CATEGORY": 5760,
    "SELECT_CATEGORY": 23040, "SELECT_COMPOSITION": 671728,
}


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


def row_hash(row: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(row).encode("utf-8"))


def id_set_hash(values: Iterable[str]) -> str:
    return sha256_bytes("".join(f"{value}\n" for value in sorted(values)).encode("utf-8"))


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
    if any(any(control in value for control in ("\t", "\n", "\r")) for value in values):
        raise AssertionError("TSV control character in streamed transition field")
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


def distribution(rows: Iterable[dict[str, str]]) -> dict[str, int]:
    return dict(sorted(Counter(row["reconciliation_outcome"] for row in rows).items()))


class Checks:
    """Compact deterministic check log for the independent receipt."""

    def __init__(self) -> None:
        self.ids: list[str] = []

    def equal(self, check_id: str, observed: Any, expected: Any) -> None:
        if observed != expected:
            raise AssertionError(f"{check_id}: observed={observed!r}; expected={expected!r}")
        self.ids.append(check_id)

    def true(self, check_id: str, condition: bool, observed: Any = None) -> None:
        if not condition:
            raise AssertionError(f"{check_id}: condition failed; observed={observed!r}")
        self.ids.append(check_id)


@dataclass
class Context:
    families: dict[str, dict[str, str]]
    set_manifest: dict[str, dict[str, str]]
    ledgers: dict[str, list[dict[str, str]]]
    state_outcomes: dict[str, str]
    state_hashes: dict[str, str]
    correction_sense: str
    family_source_rows: list[dict[str, str]]


@dataclass
class TransitionSummary:
    record_count: int
    sorted_id_set_sha256: str
    outcomes: dict[str, int]
    actions: dict[str, int]
    state_mutated: dict[str, int]
    same_state: dict[str, int]
    matrix: Counter[tuple[str, str]]
    focus_total: int
    focus_self: int
    shards: list[dict[str, Any]]


def verify_inputs(checks: Checks) -> None:
    for relative, expected in PINNED_INPUT_SHA256.items():
        path = REPO / relative
        checks.true(f"input_exists:{relative}", path.is_file(), relative)
        checks.equal(f"input_sha256:{relative}", sha256_file(path), expected)
    attrs = (REPO / ".gitattributes").read_text(encoding="utf-8")
    rule = f"{RAW_REL}/large/** filter=lfs diff=lfs merge=lfs -text"
    checks.true("lfs_rule_predeclared", rule in attrs, rule)


def load_families(checks: Checks) -> tuple[dict[str, dict[str, str]], list[dict[str, str]]]:
    local_rows = read_tsv(LOCAL_FAMILY_PATH)
    local = {row["candidate_id"]: row for row in local_rows}
    checks.equal("local_family_unique_count", len(local), len(local_rows))
    taxonomy = {row["disposition"]: row for row in read_tsv(TAXONOMY_PATH)}
    final_rows = [row for path in FAMILY_PATHS for row in read_tsv(path)]
    final: dict[str, dict[str, str]] = {}
    for row in final_rows:
        candidate_id = row["candidate_id"]
        checks.true(f"final_family_unique:{candidate_id}", candidate_id not in final, candidate_id)
        checks.true(f"final_family_governed:{candidate_id}", candidate_id in local, candidate_id)
        disposition = row["final_parent_disposition"]
        checks.true(f"final_disposition_known:{candidate_id}", disposition in taxonomy, disposition)
        checks.true(
            f"final_disposition_final:{candidate_id}",
            taxonomy[disposition]["status_class"] != "NONFINAL",
            disposition,
        )
        checks.true(f"final_disposition_mapped:{candidate_id}", disposition in FINAL_DISPOSITION_TO_OUTCOME, disposition)
        checks.equal(
            f"final_family_key:{candidate_id}", row["participant_set_key"],
            local[candidate_id]["participant_set_key"],
        )
        senses = json.loads(row["participant_sense_ids_json"])
        checks.equal(f"family_sense_order:{candidate_id}", senses, sorted(set(senses)))
        checks.equal(
            f"family_key_reconstructed:{candidate_id}",
            sha256_bytes(canonical_json(senses).encode("utf-8")), row["participant_set_key"],
        )
        final[candidate_id] = row
    checks.equal("final_family_exact_coverage", set(final), set(local))
    checks.equal("final_family_count", len(final), 35)
    return final, final_rows


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


def classify_prior(
    row: dict[str, str], families: dict[str, dict[str, str]]
) -> tuple[str, str, list[str]]:
    senses = json.loads(row["participant_sense_ids_json"])
    candidates = json.loads(row["round16b_candidate_ids_json"])
    if len(senses) == 2:
        if candidates:
            raise AssertionError(f"pair baseline linked to group family: {row['prior_id']}")
        return "RETAINED", "ROUND16A_ACTIVE_PAIR_BASELINE_NO_GROUP_CLAIM", []
    if len(senses) < 2 or len(candidates) != 1:
        raise AssertionError(f"non-pair object lacks one exact family: {row['prior_id']}")
    candidate_id = candidates[0]
    if candidate_id not in families:
        raise AssertionError(f"object references nonfinal family: {candidate_id}")
    disposition = families[candidate_id]["final_parent_disposition"]
    return FINAL_DISPOSITION_TO_OUTCOME[disposition], f"FAMILY_FINAL_DISPOSITION:{disposition}", [disposition]


def expected_object_record(
    source: dict[str, str], families: dict[str, dict[str, str]], source_file_sha: str
) -> dict[str, str]:
    outcome, basis, dispositions = classify_prior(source, families)
    material = {
        "authority_base_sha": AUTHORITY_BASE_SHA,
        "source_sha": SOURCE_SHA,
        "prior_object_type": source["prior_object_type"],
        "prior_id": source["prior_id"],
        "source_path": source["source_path"],
        "source_file_sha256": source_file_sha,
        "source_record_ref": source["source_record_ref"],
        "source_record_sha256": source["record_sha256"],
        "participant_set_key": source["participant_set_key"],
        "participant_sense_ids_json": source["participant_sense_ids_json"],
        "candidate_ids_json": source["round16b_candidate_ids_json"],
        "candidate_final_dispositions_json": canonical_json(dispositions),
        "upstream_object_ids_json": source["prior_parent_ids_json"],
        "prior_association_ids_json": source["prior_association_ids_json"],
        "prior_status": source["prior_status"],
        "prior_topology": source["prior_topology"],
        "reconciliation_outcome": outcome,
        "outcome_basis": basis,
        "semantic_carry_forward_authorized": "false",
        "active_fact_created": "false",
        "product_eligible": "false",
        "pair_projection_eligible": "false",
        "required_next_action": next_action(source["prior_object_type"], outcome),
    }
    return {**material, "record_sha256": row_hash(material)}


def load_context(checks: Checks) -> Context:
    verify_inputs(checks)
    families, family_source_rows = load_families(checks)
    prior_rows = [
        *read_tsv(PRIOR_CORE_PATH), *read_tsv(PRIOR_STATES_PATH),
        *read_tsv(PRIOR_WORKFLOWS_PATH), *read_tsv(PRIOR_EXPORTS_PATH),
    ]
    prior: dict[tuple[str, str], dict[str, str]] = {}
    for row in prior_rows:
        key = (row["prior_object_type"], row["prior_id"])
        if key in prior:
            raise AssertionError(f"duplicate prior object: {key}")
        prior[key] = row
    sets = {row["prior_object_type"]: row for row in read_tsv(PRIOR_SET_PATH)}
    checks.equal("prior_object_key_uniqueness", len(prior), len(prior_rows))

    source_hash_cache: dict[str, str] = {}
    ledgers: dict[str, list[dict[str, str]]] = {}
    for object_type in OBJECT_OUTPUTS:
        sources = sorted(
            (row for (kind, _), row in prior.items() if kind == object_type),
            key=lambda row: row["prior_id"],
        )
        authority = sets[object_type]
        ids = [row["prior_id"] for row in sources]
        checks.equal(f"set_count:{object_type}", len(ids), int(authority["record_count"]))
        checks.equal(f"set_unique:{object_type}", len(ids), len(set(ids)))
        checks.equal(f"set_hash:{object_type}", id_set_hash(ids), authority["sorted_id_set_sha256"])
        output_rows = []
        for source in sources:
            senses = json.loads(source["participant_sense_ids_json"])
            checks.equal(f"participant_order:{object_type}:{source['prior_id']}", senses, sorted(set(senses)))
            checks.equal(
                f"participant_key:{object_type}:{source['prior_id']}",
                sha256_bytes(canonical_json(senses).encode("utf-8")), source["participant_set_key"],
            )
            source_path = source["source_path"]
            if source_path not in source_hash_cache:
                source_hash_cache[source_path] = sha256_file(REPO / source_path)
            output_rows.append(expected_object_record(source, families, source_hash_cache[source_path]))
        ledgers[object_type] = output_rows
        checks.equal(
            f"outcome_distribution:{object_type}", distribution(output_rows),
            EXPECTED_DISTRIBUTIONS[object_type],
        )

    # Independent source-set conservation for the two audit ledgers.
    enumeration = read_tsv(ENUMERATION_PATH)
    enumeration_ids = {
        f"{row['association_subgraph_id']}|{row['topology_family']}" for row in enumeration
    }
    attempt_ids = {row["prior_id"] for row in ledgers["ROUND16A_TOPOLOGY_ENUMERATION_RESULT"]}
    checks.equal("topology_attempt_source_set", attempt_ids, enumeration_ids)
    checks.equal("topology_attempt_count", len(enumeration), 348)
    checks.equal("topology_attempt_decisions", Counter(row["decision"] for row in enumeration), Counter({"INVALID": 267, "VALID": 81}))
    rejections = read_tsv(REJECTION_PATH)
    rejection_ids = {row["rejection_id"] for row in rejections}
    output_rejection_ids = {row["prior_id"] for row in ledgers["ROUND16A_TOPOLOGY_REJECTION"]}
    checks.equal("topology_rejection_source_set", output_rejection_ids, rejection_ids)
    checks.equal("topology_rejection_count", len(rejections), 277)
    checks.equal(
        "topology_rejection_decisions", Counter(row["decision"] for row in rejections),
        Counter({"INVALID": 267, "PRUNED": 8, "UNRESOLVED": 2}),
    )

    # Independently prove that every known parent carries the same semantic
    # outcome. Unknown parents belong to earlier governed object classes.
    outcome_by_id = {
        row["prior_id"]: row["reconciliation_outcome"]
        for rows in ledgers.values() for row in rows
    }
    checked_parent_edges = 0
    for rows in ledgers.values():
        for row in rows:
            for parent_id in json.loads(row["upstream_object_ids_json"]):
                if parent_id in outcome_by_id:
                    checks.equal(
                        f"parent_outcome:{row['prior_id']}:{parent_id}",
                        row["reconciliation_outcome"], outcome_by_id[parent_id],
                    )
                    checked_parent_edges += 1
    checks.true("parent_edge_conservation_nonempty", checked_parent_edges > 30000, checked_parent_edges)

    registry = read_json(REGISTRY_PATH)
    read_model = read_json(READ_MODEL_PATH)
    registry_subgraphs = {row["association_subgraph_id"] for row in registry["association_subgraphs"]}
    registry_topologies = {row["composition_id"] for row in registry["topology_compositions"]}
    registry_categories = {row["category_entry_id"] for row in registry["category_entries"]}
    checks.equal("registry_subgraph_set", registry_subgraphs, {row["prior_id"] for row in ledgers["ROUND16A_ASSOCIATION_SUBGRAPH"]})
    checks.equal("registry_topology_set", registry_topologies, {row["prior_id"] for row in ledgers["ROUND16A_TOPOLOGY_COMPOSITION"]})
    checks.equal("registry_category_set", registry_categories, {row["prior_id"] for row in ledgers["ROUND16A_CATEGORY_ENTRY"]})
    checks.equal("read_model_composition_set", set(read_model["compositions"]), {row["prior_id"] for row in ledgers["ROUND16A_PRODUCTION_COMPOSITION"]})

    legacy_source_ids = {row["compositionId"] for row in read_json(LEGACY_SOURCE_PATH)["compositions"]}
    legacy_registry_ids = {row["legacy_composition_id"] for row in registry["round16_legacy_reconciliation"]}
    checks.equal("legacy_source_registry_set", legacy_source_ids, legacy_registry_ids)
    checks.equal("legacy_output_set", legacy_source_ids, {row["prior_id"] for row in ledgers["ROUND16A_LEGACY_RECONCILIATION"]})

    state_source = {row["state_id"]: row for row in read_tsv(STATE_PATH)}
    state_outcomes = {
        row["prior_id"]: row["reconciliation_outcome"] for row in ledgers["ROUND16A_STATE"]
    }
    state_hashes = {state_id: source["state_hash"] for state_id, source in state_source.items()}
    checks.equal("state_source_output_set", set(state_source), set(state_outcomes))
    workflow_ids = {row["workflow_id"] for row in read_tsv(WORKFLOW_PATH)}
    export_ids = {row["export_variant_id"] for row in read_tsv(EXPORT_PATH)}
    checks.equal("workflow_source_output_set", workflow_ids, {row["prior_id"] for row in ledgers["ROUND16A_WORKFLOW"]})
    checks.equal("export_source_output_set", export_ids, {row["prior_id"] for row in ledgers["ROUND16A_EXPORT"]})

    corrections = read_tsv(CORRECTION_PATH)
    checks.equal("checkpoint009_correction_count", len(corrections), 1)
    correction = corrections[0]
    expected_boundary = {
        "candidate_family_created": "false",
        "additive_disposition": "SOURCE_SCOPE_CONFLICT_QUARANTINE",
        "legacy_artifact_mutated": "false",
        "evidence_activation_eligible": "false",
        "product_eligible": "false",
        "pair_projection_eligible": "false",
    }
    for field, expected in expected_boundary.items():
        checks.equal(f"checkpoint009_boundary:{field}", correction[field], expected)
    cultural = [
        row for row in read_tsv(VOCAB_IMPACT_PATH)
        if row["canonical_label"] == "cultural transformation"
    ]
    checks.equal("cultural_transformation_impact_count", len(cultural), 1)
    correction_sense = cultural[0]["participant_sense_id"]
    overlap = sum(
        correction_sense in json.loads(row["participant_sense_ids_json"])
        for row in ledgers["ROUND16A_ASSOCIATION_SUBGRAPH"]
    )
    checks.equal("checkpoint009_subgraph_overlap", overlap, 0)
    return Context(families, sets, ledgers, state_outcomes, state_hashes, correction_sense, family_source_rows)


def family_impact_rows(context: Context) -> list[dict[str, str]]:
    mapped = sorted({
        candidate_id
        for row in context.ledgers["ROUND16A_ASSOCIATION_SUBGRAPH"]
        for candidate_id in json.loads(row["candidate_ids_json"])
    })
    labels = [
        ("ROUND16A_ASSOCIATION_SUBGRAPH", "subgraph_count"),
        ("ROUND16A_TOPOLOGY_ENUMERATION_RESULT", "topology_attempt_count"),
        ("ROUND16A_TOPOLOGY_REJECTION", "topology_rejection_count"),
        ("ROUND16A_TOPOLOGY_COMPOSITION", "topology_composition_count"),
        ("ROUND16A_CATEGORY_ENTRY", "category_count"),
        ("ROUND16A_SEED_VARIANT", "seed_count"),
        ("ROUND16A_PRODUCTION_COMPOSITION", "composition_count"),
        ("ROUND16A_STATE", "state_count"),
        ("ROUND16A_WORKFLOW", "workflow_count"),
        ("ROUND16A_EXPORT", "export_count"),
        ("ROUND16A_LEGACY_RECONCILIATION", "legacy_count"),
    ]
    result = []
    for candidate_id in mapped:
        family = context.families[candidate_id]
        counts = {
            label: str(sum(
                candidate_id in json.loads(row["candidate_ids_json"])
                for row in context.ledgers[object_type]
            ))
            for object_type, label in labels
        }
        material = {
            "authority_base_sha": AUTHORITY_BASE_SHA,
            "source_sha": SOURCE_SHA,
            "candidate_id": candidate_id,
            "participant_set_key": family["participant_set_key"],
            "participant_sense_ids_json": family["participant_sense_ids_json"],
            "canonical_labels_json": family["canonical_labels_json"],
            "arity": family["arity"],
            "final_parent_disposition": family["final_parent_disposition"],
            "global_coherence_status": family["global_coherence_status"],
            "reconciliation_outcome": FINAL_DISPOSITION_TO_OUTCOME[family["final_parent_disposition"]],
            **counts,
            "checkpoint009_source_correction_overlap_count": lower_bool(
                context.correction_sense in json.loads(family["participant_sense_ids_json"])
            ),
        }
        result.append({**material, "record_sha256": row_hash(material)})
    if len(result) != 9:
        raise AssertionError(f"mapped family count: {len(result)} != 9")
    return result


def transition_suffix(transition_id: str) -> str:
    prefix = "R16A-TRANSITION-"
    if not transition_id.startswith(prefix):
        raise AssertionError(f"transition prefix: {transition_id}")
    suffix = transition_id[len(prefix):]
    if len(suffix) != 24 or suffix.upper() != suffix or any(char not in "0123456789ABCDEF" for char in suffix):
        raise AssertionError(f"transition suffix: {transition_id}")
    return suffix


def shard_relative(index: int) -> str:
    return (
        f"{LARGE_REL}/round16a-transition-reconciliation-"
        f"{index * 4:02x}-{index * 4 + 3:02x}-v1.tsv"
    )


def expected_transition(
    source: dict[str, str], context: Context
) -> tuple[int, dict[str, str]]:
    suffix = transition_suffix(source["transition_id"])
    shard = int(suffix[:2], 16) // 4
    current = source["current_state_id"]
    nxt = source["next_state_id"]
    if current not in context.state_outcomes or nxt not in context.state_outcomes:
        raise AssertionError(f"transition endpoint missing: {source['transition_id']}")
    if source["current_state_hash"] != context.state_hashes[current]:
        raise AssertionError(f"current endpoint hash: {source['transition_id']}")
    if source["next_state_hash"] != context.state_hashes[nxt]:
        raise AssertionError(f"next endpoint hash: {source['transition_id']}")
    current_outcome = context.state_outcomes[current]
    next_outcome = context.state_outcomes[nxt]
    outcome = BY_SEVERITY[max(SEVERITY[current_outcome], SEVERITY[next_outcome])]
    material = {
        "authority_base_sha": AUTHORITY_BASE_SHA,
        "source_sha": SOURCE_SHA,
        "shard_id": f"R16B-R16A-TRANSITION-SHARD-{shard:02d}",
        "prior_transition_id": source["transition_id"],
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


def iter_transition_source() -> Iterator[dict[str, str]]:
    with (REPO / TRANSITION_PATH).open(encoding="utf-8", newline="") as handle:
        previous = ""
        for source in csv.DictReader(handle, dialect="excel-tab"):
            transition_id = source["transition_id"]
            if previous and transition_id <= previous:
                raise AssertionError("transition source is not strictly sorted and unique")
            previous = transition_id
            yield source


def verify_transition_shards(context: Context, checks: Checks) -> TransitionSummary:
    expected_paths = {shard_relative(index) for index in range(64)}
    shard_dir = REPO / LARGE_REL
    checks.true("transition_shard_directory", shard_dir.is_dir(), LARGE_REL)
    actual_paths = {
        path.relative_to(REPO).as_posix() for path in shard_dir.glob("*.tsv")
    }
    checks.equal("transition_shard_path_set", actual_paths, expected_paths)

    header = serialized_tsv_row(TRANSITION_FIELDS, {field: field for field in TRANSITION_FIELDS})
    shard_hashes = [hashlib.sha256(header) for _ in range(64)]
    shard_bytes = [len(header)] * 64
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
    focus_total = 0
    focus_self = 0
    count = 0
    current_shard = -1
    actual_handle: Any = None

    def close_shard() -> None:
        nonlocal actual_handle
        if actual_handle is not None:
            trailing = actual_handle.read(1)
            if trailing:
                raise AssertionError(f"trailing transition bytes in shard {current_shard}")
            actual_handle.close()
            actual_handle = None

    for source in iter_transition_source():
        shard, row = expected_transition(source, context)
        if shard != current_shard:
            close_shard()
            if shard != current_shard + 1:
                raise AssertionError(f"noncontiguous transition shard stream: {current_shard} -> {shard}")
            current_shard = shard
            actual_handle = (REPO / shard_relative(shard)).open("rb")
            if actual_handle.readline() != header:
                raise AssertionError(f"transition header mismatch: shard {shard}")
        payload = serialized_tsv_row(TRANSITION_FIELDS, row)
        if actual_handle.readline() != payload:
            raise AssertionError(f"transition row mismatch: {row['prior_transition_id']}")
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
    close_shard()
    checks.equal("transition_last_shard", current_shard, 63)
    authority = context.set_manifest["ROUND16A_TRANSITION"]
    checks.equal("transition_count", count, int(authority["record_count"]))
    checks.equal("transition_count_regression", count, 749944)
    checks.equal("transition_id_set_hash", global_id_hash.hexdigest(), authority["sorted_id_set_sha256"])
    checks.equal("transition_outcomes", dict(sorted(outcomes.items())), EXPECTED_TRANSITION_OUTCOMES)
    checks.equal("transition_matrix", dict(matrix), EXPECTED_MATRIX)
    checks.equal("transition_actions", dict(sorted(actions.items())), EXPECTED_ACTIONS)
    checks.equal("transition_state_mutated", state_mutated, Counter({"false": 749944}))
    checks.equal("transition_same_state", same_state, Counter({"false": 738188, "true": 11756}))
    checks.equal("focus_node_count", focus_total, 18480)
    checks.equal("focus_node_self_count", focus_self, 5760)
    checks.true("transition_shards_nonempty", all(shard_counts), shard_counts)

    shards = []
    for index in range(64):
        path = REPO / shard_relative(index)
        expected_sha = shard_hashes[index].hexdigest()
        checks.equal(f"shard_size:{index:02d}", path.stat().st_size, shard_bytes[index])
        checks.equal(f"shard_sha256:{index:02d}", sha256_file(path), expected_sha)
        shards.append({
            "shard_id": f"R16B-R16A-TRANSITION-SHARD-{index:02d}",
            "prefix_start": f"{index * 4:02x}",
            "prefix_end": f"{index * 4 + 3:02x}",
            "path": shard_relative(index),
            "record_count": shard_counts[index],
            "first_transition_id": first_ids[index],
            "last_transition_id": last_ids[index],
            "sorted_transition_id_set_sha256": shard_id_hashes[index].hexdigest(),
            "output_bytes": shard_bytes[index],
            "output_sha256": expected_sha,
        })
    checks.equal("transition_shard_count", len(shards), 64)
    checks.equal("transition_shard_min", min(shard_counts), 11455)
    checks.equal("transition_shard_max", max(shard_counts), 11940)
    return TransitionSummary(
        count, global_id_hash.hexdigest(), dict(sorted(outcomes.items())),
        dict(sorted(actions.items())), dict(sorted(state_mutated.items())),
        dict(sorted(same_state.items())), matrix, focus_total, focus_self, shards,
    )


def build_report(census: dict[str, Any]) -> bytes:
    lines = [
        "# Round 16A global reconciliation under the Round 16B evidence model", "",
        f"Authority base: `{AUTHORITY_BASE_SHA}`. Authorized source: `{SOURCE_SHA}`.", "",
        "Every prior subgraph, topology attempt and rejection, topology composition, category, seed, production composition, state, transition, workflow, export, and legacy composition has an explicit outcome. `RETAINED` preserves a pair baseline, not a group claim. `CORRECTED` removes unsupported group coherence while preserving separately governed pairs. `INQUIRY` is product-ineligible. `REJECTED` remains an audit receipt.", "",
        "| Object | Retained | Corrected | Inquiry | Rejected | Total |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, values in census["main_object_distributions"].items():
        lines.append(
            f"| {name} | {values.get('RETAINED',0)} | {values.get('CORRECTED',0)} | "
            f"{values.get('INQUIRY',0)} | {values.get('REJECTED',0)} | {sum(values.values())} |"
        )
    lines.extend([
        "", f"The {census['transition_count']:,} transitions are partitioned into 64 first-byte-range LFS shards and classified by the maximum severity of both endpoint-state outcomes.", "",
        "Checkpoint 009's `COMP-EVID-018` scope correction changes none of these counts because `cultural transformation` has degree zero and appears in no Round 16A subgraph. It nevertheless remains a closure blocker and requires an independent support re-audit.", "",
        "All closure flags remain false. Product regeneration and independent verification are still pending.",
    ])
    return ("\n".join(lines) + "\n").encode("utf-8")


def reconstruct_primary_artifacts(
    context: Context, transition: TransitionSummary
) -> tuple[dict[str, bytes], dict[str, int], dict[str, Any]]:
    artifacts: dict[str, bytes] = {}
    counts: dict[str, int] = {}
    for object_type, path in OBJECT_OUTPUTS.items():
        artifacts[path] = tsv_bytes(OBJECT_FIELDS, context.ledgers[object_type])
        counts[path] = len(context.ledgers[object_type])

    family_rows = family_impact_rows(context)
    artifacts[FAMILY_IMPACT_PATH] = tsv_bytes(FAMILY_FIELDS, family_rows)
    counts[FAMILY_IMPACT_PATH] = len(family_rows)

    matrix_rows = []
    for current in OUTCOMES:
        for nxt in OUTCOMES:
            derived = BY_SEVERITY[max(SEVERITY[current], SEVERITY[nxt])]
            material = {
                "current_state_reconciliation_outcome": current,
                "next_state_reconciliation_outcome": nxt,
                "transition_count": str(transition.matrix[(current, nxt)]),
                "derived_reconciliation_outcome": derived,
                "outcome_severity_rule": "MAX_CURRENT_AND_NEXT_STATE_SEVERITY",
            }
            matrix_rows.append({**material, "record_sha256": row_hash(material)})
    artifacts[MATRIX_PATH] = tsv_bytes(MATRIX_FIELDS, matrix_rows)
    counts[MATRIX_PATH] = 16

    shard_rows = []
    for shard in transition.shards:
        material = {
            "shard_id": shard["shard_id"],
            "prefix_start": shard["prefix_start"],
            "prefix_end": shard["prefix_end"],
            "path": shard["path"],
            "record_count": str(shard["record_count"]),
            "first_transition_id": shard["first_transition_id"],
            "last_transition_id": shard["last_transition_id"],
            "sorted_transition_id_set_sha256": shard["sorted_transition_id_set_sha256"],
            "output_bytes": str(shard["output_bytes"]),
            "output_sha256": shard["output_sha256"],
            "lfs_required": "true",
            "source_file_sha256": PINNED_INPUT_SHA256[TRANSITION_PATH],
        }
        shard_rows.append({**material, "record_sha256": row_hash(material)})
    artifacts[SHARD_MANIFEST_PATH] = tsv_bytes(SHARD_MANIFEST_FIELDS, shard_rows)
    counts[SHARD_MANIFEST_PATH] = 64

    input_rows = []
    for ordinal, path in enumerate(PINNED_INPUT_SHA256, 1):
        input_rows.append({
            "ordinal": str(ordinal),
            "path": path,
            "selector": "TSV_ROWS" if path.endswith(".tsv") else "PINNED_FILE",
            "record_count": str(transition.record_count if path == TRANSITION_PATH else file_record_count(path)),
            "bytes": str((REPO / path).stat().st_size),
            "sha256": PINNED_INPUT_SHA256[path],
            "use_boundary": "EXACT_AUTHORITY_INPUT_NO_SEMANTIC_STATUS_INHERITED",
        })
    artifacts[INPUT_MANIFEST_PATH] = tsv_bytes(INPUT_MANIFEST_FIELDS, input_rows)
    counts[INPUT_MANIFEST_PATH] = len(input_rows)

    main_types = [
        "ROUND16A_ASSOCIATION_SUBGRAPH", "ROUND16A_TOPOLOGY_COMPOSITION",
        "ROUND16A_CATEGORY_ENTRY", "ROUND16A_SEED_VARIANT",
        "ROUND16A_PRODUCTION_COMPOSITION", "ROUND16A_STATE", "ROUND16A_WORKFLOW",
        "ROUND16A_EXPORT", "ROUND16A_LEGACY_RECONCILIATION",
    ]
    main_distributions = {
        object_type: distribution(context.ledgers[object_type]) for object_type in main_types
    }
    totals: Counter[str] = Counter()
    for values in main_distributions.values():
        totals.update(values)
    totals.update(transition.outcomes)
    census = {
        "format": "trace-round16b-round16a-global-reconciliation-census-v1",
        "builder_version": BUILDER_VERSION,
        "authority_base_sha": AUTHORITY_BASE_SHA,
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "status": "PASS_WITH_OPEN_CLOSURE_BLOCKERS",
        "mapped_governed_family_count": len(family_rows),
        "main_object_distributions": main_distributions,
        "transition_outcome_distribution": transition.outcomes,
        "main_object_total_distribution": dict(sorted(totals.items())),
        "main_object_count": sum(totals.values()),
        "topology_attempt_count": len(context.ledgers["ROUND16A_TOPOLOGY_ENUMERATION_RESULT"]),
        "topology_attempt_distribution": distribution(context.ledgers["ROUND16A_TOPOLOGY_ENUMERATION_RESULT"]),
        "topology_rejection_count": len(context.ledgers["ROUND16A_TOPOLOGY_REJECTION"]),
        "topology_rejection_distribution": distribution(context.ledgers["ROUND16A_TOPOLOGY_REJECTION"]),
        "reconciled_row_count_including_topology_audit_records": (
            sum(totals.values())
            + len(context.ledgers["ROUND16A_TOPOLOGY_ENUMERATION_RESULT"])
            + len(context.ledgers["ROUND16A_TOPOLOGY_REJECTION"])
        ),
        "transition_count": transition.record_count,
        "transition_sorted_id_set_sha256": transition.sorted_id_set_sha256,
        "transition_action_distribution": transition.actions,
        "transition_same_state_distribution": transition.same_state,
        "transition_baseline_state_mutated_distribution": transition.state_mutated,
        "focus_node_transition_count": transition.focus_total,
        "focus_node_self_transition_count": transition.focus_self,
        "transition_shard_count": len(transition.shards),
        "transition_shard_record_count_min": min(row["record_count"] for row in transition.shards),
        "transition_shard_record_count_max": max(row["record_count"] for row in transition.shards),
        "checkpoint009_quarantined_source_scope_correction_count": 1,
        "checkpoint009_correction_round16a_subgraph_overlap_count": 0,
        "active_fact_created_count": 0,
        "product_activation_count": 0,
        "pair_projection_created_count": 0,
        "closure": {
            "pair_association_closure": False,
            "higher_order_association_closure": False,
            "global_composition_coherence_closure": False,
            "product_association_reachability_closure": False,
            "computational_space_closure": False,
            "function3_closure": False,
        },
    }
    if census["main_object_count"] != 773671:
        raise AssertionError("main object conservation regression")
    if census["reconciled_row_count_including_topology_audit_records"] != 774296:
        raise AssertionError("audit-inclusive object conservation regression")
    artifacts[CENSUS_PATH] = json_bytes(census)
    counts[CENSUS_PATH] = 1

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
            "gap_id": gap_id,
            "gap_class": gap_class,
            "severity": "CLOSURE_BLOCKING",
            "status": "OPEN",
            "evidence": evidence,
            "required_action": "Resolve and independently verify before any closure decision.",
            "closure_effect": "ALL_CLOSURE_FLAGS_REMAIN_FALSE",
        }
        gap_rows.append({**material, "record_sha256": row_hash(material)})
    artifacts[GAP_PATH] = tsv_bytes(GAP_FIELDS, gap_rows)
    counts[GAP_PATH] = 6
    artifacts[REPORT_REL] = build_report(census)
    counts[REPORT_REL] = 1

    # The primary output manifest covers 19 pre-manifest small artifacts plus
    # the 64 transition payloads. It intentionally does not list itself.
    payload_meta = {
        path: {
            "record_count": counts[path], "bytes": len(payload),
            "sha256": sha256_bytes(payload), "lfs_required": False,
        }
        for path, payload in artifacts.items()
    }
    for shard in transition.shards:
        payload_meta[shard["path"]] = {
            "record_count": shard["record_count"], "bytes": shard["output_bytes"],
            "sha256": shard["output_sha256"], "lfs_required": True,
        }
    output_rows = []
    for ordinal, path in enumerate(sorted(payload_meta), 1):
        meta = payload_meta[path]
        output_rows.append({
            "ordinal": str(ordinal), "path": path,
            "record_count": str(meta["record_count"]), "bytes": str(meta["bytes"]),
            "sha256": meta["sha256"], "lfs_required": lower_bool(meta["lfs_required"]),
        })
    artifacts[OUTPUT_MANIFEST_PATH] = tsv_bytes(OUTPUT_MANIFEST_FIELDS, output_rows)
    counts[OUTPUT_MANIFEST_PATH] = len(output_rows)
    aggregate = sha256_bytes(canonical_json([
        {"path": row["path"], "sha256": row["sha256"]} for row in output_rows
    ]).encode("utf-8"))
    receipt = {
        "format": "trace-round16b-round16a-global-reconciliation-build-receipt-v1",
        "builder_version": BUILDER_VERSION,
        "builder_sha256": sha256_file(REPO / BUILDER_PATH),
        "authority_base_sha": AUTHORITY_BASE_SHA,
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "status": "PASS_WITH_OPEN_CLOSURE_BLOCKERS",
        "input_count": len(input_rows),
        "output_count_excluding_receipt": len(output_rows) + 1,
        "output_manifest_sha256": sha256_bytes(artifacts[OUTPUT_MANIFEST_PATH]),
        "aggregate_output_sha256_excluding_manifest_and_receipt": aggregate,
        "main_object_count": census["main_object_count"],
        "reconciled_row_count_including_topology_audit_records": census["reconciled_row_count_including_topology_audit_records"],
        "transition_count": transition.record_count,
        "transition_shard_count": len(transition.shards),
        "active_fact_created_count": 0,
        "product_activation_count": 0,
        "pair_projection_created_count": 0,
        "history_rewritten": False,
        "force_push_used": False,
        "rollback_tag_pushed": False,
        "origin_main_rewritten": False,
        "deployment_performed": False,
        "closure_flags_true_count": 0,
    }
    artifacts[BUILD_RECEIPT_PATH] = json_bytes(receipt)
    counts[BUILD_RECEIPT_PATH] = 1
    return artifacts, counts, census


def verify_primary_bytes(
    artifacts: dict[str, bytes], transition: TransitionSummary, checks: Checks
) -> None:
    checks.equal("primary_small_artifact_count", len(artifacts), 20)
    for relative, expected in sorted(artifacts.items()):
        path = REPO / relative
        checks.true(f"primary_exists:{relative}", path.is_file(), relative)
        checks.equal(f"primary_bytes:{relative}", path.read_bytes(), expected)
    output_manifest = read_tsv(OUTPUT_MANIFEST_PATH)
    checks.equal("output_manifest_count", len(output_manifest), 82)
    checks.equal(
        "output_manifest_path_set",
        {row["path"] for row in output_manifest},
        ({path for path in artifacts if path not in {OUTPUT_MANIFEST_PATH, BUILD_RECEIPT_PATH}}
         | {row["path"] for row in transition.shards}),
    )
    checks.equal(
        "output_manifest_lfs_set",
        {row["path"] for row in output_manifest if row["lfs_required"] == "true"},
        {row["path"] for row in transition.shards},
    )


def run_negative_controls(context: Context, checks: Checks) -> list[dict[str, str]]:
    controls: list[dict[str, str]] = []

    all_pair_nonretained = [
        row for row in context.family_source_rows
        if int(row["internal_possible_pair_count"]) > 0
        and row["internal_active_pair_count"] == row["internal_possible_pair_count"]
        and FINAL_DISPOSITION_TO_OUTCOME[row["final_parent_disposition"]] != "RETAINED"
    ]
    checks.true("control_all_pairs_not_group", bool(all_pair_nonretained), all_pair_nonretained)
    controls.append({"control": "ALL_INTERNAL_PAIRS_ACTIVE_GROUP_NOT_RETAINED", "status": "PASS"})

    invalid_semantic = [
        row for row in context.ledgers["ROUND16A_TOPOLOGY_ENUMERATION_RESULT"]
        if row["prior_status"] == "VALID" and row["reconciliation_outcome"] != "RETAINED"
    ]
    checks.true("control_renderable_not_semantic", bool(invalid_semantic), len(invalid_semantic))
    controls.append({"control": "RENDERABLE_TOPOLOGY_NOT_GROUP_VALIDITY", "status": "PASS"})

    all_rows = [row for rows in context.ledgers.values() for row in rows]
    checks.true(
        "control_no_hyperedge_projection",
        all(row["pair_projection_eligible"] == "false" for row in all_rows),
    )
    controls.append({"control": "HYPEREDGE_NOT_PROJECTED_TO_PAIR_EDGES", "status": "PASS"})
    checks.true(
        "control_no_pending_active_fact",
        all(row["active_fact_created"] == "false" and row["product_eligible"] == "false" for row in all_rows),
    )
    controls.append({"control": "PENDING_OR_INQUIRY_NEVER_ACTIVE", "status": "PASS"})

    checks.equal(
        "control_endpoint_order_independence",
        BY_SEVERITY[max(SEVERITY["RETAINED"], SEVERITY["REJECTED"])], "REJECTED",
    )
    checks.equal(
        "control_endpoint_order_independence_reverse",
        BY_SEVERITY[max(SEVERITY["REJECTED"], SEVERITY["RETAINED"])], "REJECTED",
    )
    controls.append({"control": "BOTH_TRANSITION_ENDPOINTS_CONTROL_SEVERITY", "status": "PASS"})

    try:
        transition_suffix("R16A-TRANSITION-Z0003889D89108267090F470")
    except AssertionError:
        controls.append({"control": "MALFORMED_TRANSITION_ID_REJECTED", "status": "PASS"})
        checks.ids.append("control_malformed_transition_id")
    else:
        raise AssertionError("malformed transition id negative control was accepted")

    sample = context.ledgers["ROUND16A_ASSOCIATION_SUBGRAPH"][0]
    material = {key: value for key, value in sample.items() if key != "record_sha256"}
    corrupted = dict(material)
    corrupted["prior_status"] += "-CORRUPTED"
    checks.true("control_record_hash_corruption", row_hash(corrupted) != sample["record_sha256"])
    controls.append({"control": "RECORD_HASH_CORRUPTION_DETECTED", "status": "PASS"})
    return controls


def independent_receipt(
    checks: Checks,
    context: Context,
    transition: TransitionSummary,
    census: dict[str, Any],
    controls: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "format": "trace-round16b-round16a-global-reconciliation-independent-verification-v1",
        "verifier_version": VERIFIER_VERSION,
        "verifier_sha256": sha256_file(Path(__file__)),
        "authority_base_sha": AUTHORITY_BASE_SHA,
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "status": "PASS_WITH_OPEN_CLOSURE_BLOCKERS",
        "check_count": len(checks.ids),
        "check_id_set_sha256": id_set_hash(checks.ids),
        "primary_output_manifest_sha256": sha256_file(REPO / OUTPUT_MANIFEST_PATH),
        "primary_build_receipt_sha256": sha256_file(REPO / BUILD_RECEIPT_PATH),
        "verified_primary_output_count_including_receipt": 84,
        "generic_object_ledger_count": len(OBJECT_OUTPUTS),
        "mapped_governed_family_count": 9,
        "main_object_count": census["main_object_count"],
        "reconciled_row_count_including_topology_audit_records": census["reconciled_row_count_including_topology_audit_records"],
        "topology_attempt_count": len(context.ledgers["ROUND16A_TOPOLOGY_ENUMERATION_RESULT"]),
        "topology_attempt_valid_count": 81,
        "topology_attempt_invalid_count": 267,
        "topology_rejection_count": len(context.ledgers["ROUND16A_TOPOLOGY_REJECTION"]),
        "topology_rejection_invalid_count": 267,
        "topology_rejection_pruned_count": 8,
        "topology_rejection_unresolved_count": 2,
        "transition_count": transition.record_count,
        "transition_shard_count": len(transition.shards),
        "transition_outcome_distribution": transition.outcomes,
        "transition_endpoint_matrix_verified": True,
        "transition_exact_identity_set_verified": True,
        "object_exact_identity_sets_verified": True,
        "source_parent_conservation_verified": True,
        "semantic_carry_forward_authorized_count": 0,
        "active_fact_created_count": 0,
        "product_activation_count": 0,
        "pair_projection_created_count": 0,
        "negative_controls": controls,
        "closure_flags_true_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true",
        help="verify the independent receipt without rewriting any artifact",
    )
    args = parser.parse_args()
    checks = Checks()
    context = load_context(checks)
    transition = verify_transition_shards(context, checks)
    artifacts, _, census = reconstruct_primary_artifacts(context, transition)
    verify_primary_bytes(artifacts, transition, checks)
    controls = run_negative_controls(context, checks)
    receipt = independent_receipt(checks, context, transition, census, controls)
    payload = json_bytes(receipt)
    receipt_path = REPO / INDEPENDENT_RECEIPT_PATH
    if args.check:
        checks.true("independent_receipt_exists", receipt_path.is_file(), INDEPENDENT_RECEIPT_PATH)
        if receipt_path.read_bytes() != payload:
            raise AssertionError(f"independent receipt mismatch: {INDEPENDENT_RECEIPT_PATH}")
        mode = "CHECK"
    else:
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_bytes(payload)
        mode = "WRITE_INDEPENDENT_RECEIPT_ONLY"
    print(canonical_json({
        "status": "PASS", "mode": mode, "verifier_version": VERIFIER_VERSION,
        "check_count": receipt["check_count"], "transition_count": transition.record_count,
        "independent_receipt": INDEPENDENT_RECEIPT_PATH,
        "independent_receipt_sha256": sha256_bytes(payload),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
