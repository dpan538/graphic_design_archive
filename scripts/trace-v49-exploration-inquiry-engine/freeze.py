"""Build and verify the immutable 16-sense research-candidate freeze."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from canonical import semantic_hash
from model import CandidateResearchStatus, split_refs
from strict_parse import validate_candidate_freeze


ROUND9_REGISTRY_SHA = "818b306406d6a557a563ec285ae36394106c4c88a3e14cae19e4f1da4e92f4d5"
ROUND10_INPUT_SHA = "da22e62828b9d6ae2dd1692ec4f23b82a984ce9d53240d198246915668481aec"
ROUND10_COMMIT_SHA = "4bd82deba482ec2fbf8c4856080151416fb8ee83"
ROUND11_COMMIT_SHA = "5ca999b53d9a5d18b47317817402f9e51ad26cec"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _index(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    result = {row[key]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"duplicate {key} in sealed input")
    return result


def build_candidate_freeze(repo: Path) -> dict[str, Any]:
    r9 = repo / "docs/research/trace-v49-design-history-relation-vocabulary-round1"
    r10 = repo / "docs/research/trace-v49-design-history-relation-grammar-round1"
    inputs = read_tsv(r10 / "02_ROUND9_INPUT_TERM_REGISTRY.tsv")
    raw = _index(read_tsv(r9 / "04_RAW_CANDIDATE_TERM_REGISTRY.tsv"), "candidate_id")
    lexical = read_tsv(r9 / "05_TERM_ATTESTATION_REGISTRY.tsv")
    gloss = _index(read_tsv(r9 / "07_SEMANTIC_GLOSS_REGISTRY.tsv"), "candidate_id")
    contestation = _index(read_tsv(r9 / "08_CONTESTATION_AND_POLYSEMY.tsv"), "candidate_id")
    direction = _index(read_tsv(r9 / "10_DIRECTIONALITY_OBSERVATIONS.tsv"), "candidate_id")
    handoff = _index(read_tsv(r9 / "11_GRAMMAR_EVIDENCE_HANDOFF.tsv"), "candidate_id")
    nodes = _index(read_tsv(r10 / "05_NODE_ROLE_DECISION_REGISTRY.tsv"), "candidate_id")
    arguments = _index(read_tsv(r10 / "06_ARGUMENT_ROLE_REGISTRY.tsv"), "candidate_id")
    grammar = read_tsv(r10 / "07_GRAMMAR_ATTESTATION_REGISTRY.tsv")
    direction10 = _index(read_tsv(r10 / "10_DIRECTIONALITY_AND_ARITY.tsv"), "candidate_id")
    qualification = _index(read_tsv(r10 / "11_QUALIFICATION_AND_CONTESTATION.tsv"), "candidate_id")
    pair_questions = [row for row in read_tsv(r10 / "09_FLOW_RULE_CANDIDATE_REGISTRY.tsv") if row["final_rule_decision"].startswith("DEFER_")]
    clusters = read_tsv(r10 / "14_CLUSTER_EVIDENCE_HANDOFF.tsv")
    chains = read_tsv(r10 / "15_OBSERVED_RELATION_CHAIN_REGISTRY.tsv")
    gaps = read_tsv(r10 / "20_VOCABULARY_GAP_REGISTER.tsv")

    if len(inputs) != 16 or any(row["exact_input_verified"] != "true" for row in inputs):
        raise ValueError("Round 10 input registry is not the exact 16-sense verified set")
    registry_hashes = {raw[row["candidate_id"]]["candidate_registry_sha256"] for row in inputs}
    if registry_hashes != {ROUND9_REGISTRY_SHA}:
        raise ValueError("Round 9 candidate registry hash mismatch")

    candidates: list[dict[str, Any]] = []
    for row in inputs:
        candidate_id, sense_id = row["candidate_id"], row["sense_id"]
        node, argument = nodes[candidate_id], arguments[candidate_id]
        is_bounded = node["pass_node"] == "true" and node["final_node_role_decision"].startswith("PASS_")
        # Round 9 binds the attestation to the unique passing candidate ID; its
        # optional sense column is intentionally blank in the sealed registry.
        lex_rows = [item for item in lexical if item["candidate_id"] == candidate_id and item["sense_id_if_applicable"] in {"", sense_id}]
        grammar_rows = [item for item in grammar if item["candidate_term_id"] == candidate_id and item["candidate_sense_id"] == sense_id]
        pair_ids = sorted({item["rule_id"] for item in pair_questions if candidate_id in {item["source_candidate_id"], item["target_candidate_id"]}})
        cluster_ids = sorted({item["cluster_handoff_id"] for item in clusters if candidate_id in split_refs(item["candidate_term_ids"])} )
        chain_ids = sorted({item["chain_id"] for item in chains if candidate_id in item["ordered_term_ids"].split(">")})
        gap_ids = sorted({item["gap_id"] for item in gaps if row["candidate_label"] in split_refs(item["trigger_terms"])} )
        source_ids = sorted({item["source_id"] for item in lex_rows} | {item["source_id"] for item in grammar_rows})
        candidate = {
            "candidateId": candidate_id,
            "senseId": sense_id,
            "label": row["candidate_label"],
            "researchStatus": CandidateResearchStatus.BOUNDED.value if is_bounded else CandidateResearchStatus.DEFERRED.value,
            "round9Decision": row["round9_final_decision"],
            "round10NodeRoleDecision": node["final_node_role_decision"],
            "technicalRole": node["primary_technical_role"],
            "plainLanguageGlossRef": f"docs/research/trace-v49-design-history-relation-vocabulary-round1/07_SEMANTIC_GLOSS_REGISTRY.tsv#{candidate_id}:{sense_id}",
            "argumentRoleRef": f"docs/research/trace-v49-design-history-relation-grammar-round1/06_ARGUMENT_ROLE_REGISTRY.tsv#{candidate_id}",
            "directionalityStatus": direction10[candidate_id]["directionality_decision"],
            "qualificationStatus": qualification[candidate_id]["required_qualification"],
            "contestationStatus": contestation[candidate_id]["contestation_status"],
            "lexicalAttestationIds": sorted(item["attestation_id"] for item in lex_rows),
            "grammarAttestationIds": sorted(item["grammar_attestation_id"] for item in grammar_rows),
            "sourceIds": source_ids,
            "pairQuestionIds": pair_ids,
            "clusterHandoffIds": cluster_ids,
            "observedChainIds": chain_ids,
            "vocabularyGapIds": gap_ids,
            "active": False,
        }
        if not lex_rows or not grammar_rows or raw[candidate_id]["candidate_label"] != candidate["label"] or gloss[candidate_id]["sense_id"] != sense_id or handoff[candidate_id]["sense_id"] != sense_id or not argument["source_support_ids"] or not direction[candidate_id]["evidence_attestation_ids"]:
            raise ValueError(f"incomplete or inconsistent sealed evidence for {candidate_id}")
        candidates.append(candidate)

    unsigned = {
        "packageId": "trace-exploration-research-candidates-v1",
        "version": "1",
        "round9CandidateRegistrySha256": ROUND9_REGISTRY_SHA,
        "round10InputTermSha256": ROUND10_INPUT_SHA,
        "round10CommitSha": ROUND10_COMMIT_SHA,
        "round11CommitSha": ROUND11_COMMIT_SHA,
        "active": False,
        "candidates": candidates,
    }
    package = {**unsigned, "canonicalHash": semantic_hash(unsigned)}
    return validate_candidate_freeze(package)


def load_candidate_freeze(path: Path) -> dict[str, Any]:
    return validate_candidate_freeze(json.loads(path.read_text(encoding="utf-8")))
