#!/usr/bin/env python3
"""Fail-closed validation for TRACE v49 relation-grammar Round 10."""

from __future__ import annotations

import csv
import hashlib
import argparse
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "docs/research/trace-v49-design-history-relation-grammar-round1"
AUDIT = ROOT / "docs/audits/v49-design-history-relation-grammar-round1"
ROUND9 = ROOT / "docs/research/trace-v49-design-history-relation-vocabulary-round1"
SOURCE_SHA = "0241b0f51e2523901b0858d54ffb7f5d2a9aa13c"
EXPECTED_LABELS = [
    "mediation", "canonization", "professionalization", "institutionalization",
    "transnational interactions", "cultural translation", "design exchanges",
    "commodification", "gendering", "displacement", "transculturation",
    "cultural mobility", "self-exoticization", "coloniality", "imitation", "piracy",
]
REVIEWER_ROLES = {
    "AGENT-GRAMMAR-DISCOVERY", "AGENT-GRAMMAR-VERIFY-A",
    "AGENT-GRAMMAR-VERIFY-B", "AGENT-GRAMMAR-SEMANTIC",
    "AGENT-GRAMMAR-ADVERSARIAL", "AGENT-UNIVERSAL-NODE-RED-TEAM",
    "AGENT-SOURCE-BREADTH-REVIEW",
}
NODE_ROLES = {
    "DIRECTED_PROCESS", "DIRECTED_STATE_TRANSITION", "HISTORIOGRAPHIC_POSITIONING",
    "STRUCTURAL_CONDITION", "REFLEXIVE_PROCESS", "MULTIPARTY_ENCOUNTER",
    "NORMATIVELY_QUALIFIED_RELATION", "BOUNDED_INTERMEDIARY_PROCESS",
    "UNRESOLVED_MIXED_ROLE", "GRAMMAR_UNSUITABLE",
}
NODE_DECISIONS = {
    "PASS_FLOW_ELIGIBLE_NODE", "PASS_STRUCTURAL_CONDITION_NODE",
    "PASS_HISTORIOGRAPHIC_POSITION_NODE", "PASS_REFLEXIVE_NODE",
    "PASS_MULTIPARTY_NODE", "PASS_NORMATIVE_RELATION_NODE",
    "DEFER_SPLIT_REQUIRED", "DEFER_TOO_BROAD", "DEFER_HIGH_CONNECTIVITY",
    "DEFER_INSUFFICIENT_GRAMMAR_EVIDENCE", "DEFER_UNRESOLVED_DIRECTIONALITY",
    "REJECT_GRAMMAR_UNSUITABLE",
}
PAIR_DECISIONS = {
    "PASS_EVIDENCE_BACKED_FLOW", "PASS_EVIDENCE_BACKED_CONDITION",
    "PASS_EVIDENCE_BACKED_CONTRAST", "PASS_EVIDENCE_BACKED_QUALIFICATION",
    "DEFER_SINGLE_ATTESTATION", "DEFER_DIRECTIONALITY", "DEFER_ROLE_AMBIGUITY",
    "DEFER_HIGH_CONNECTIVITY", "DEFER_SOURCE_CONCENTRATION",
    "REJECT_SEMANTIC_CONFLICT", "REJECT_ROLE_MISMATCH",
    "REJECT_UNSUPPORTED_COMPOSITION", "REJECT_SELF_RELATION",
    "UNSUPPORTED_DEFAULT_DENY",
}
UNIVERSAL_LABELS = {
    "mediation", "transnational interactions", "cultural translation",
    "design exchanges", "displacement", "transculturation", "cultural mobility", "coloniality",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def tsv(path: Path) -> list[dict[str, str]]:
    require(path.is_file(), f"missing file: {path.relative_to(ROOT)}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def split_ids(value: str) -> list[str]:
    return [item for item in value.split(";") if item]


def main(allow_pending_reviews: bool = False) -> None:
    require(git("rev-parse", SOURCE_SHA) == SOURCE_SHA, "source SHA is unavailable")
    require(git("merge-base", SOURCE_SHA, "HEAD") == SOURCE_SHA, "HEAD is not descended from source SHA")

    required_research = [f"{index:02d}_" for index in range(25)]
    research_names = {path.name for path in RESEARCH.iterdir() if path.is_file()}
    for prefix in required_research:
        require(any(name.startswith(prefix) for name in research_names), f"missing research file prefix {prefix}")
    required_audit = {f"{index:02d}_" for index in range(11)}
    audit_names = {path.name for path in AUDIT.iterdir() if path.is_file()}
    for prefix in required_audit:
        require(any(name.startswith(prefix) for name in audit_names), f"missing audit file prefix {prefix}")
    require({"MANIFEST.tsv", "SHA256SUMS.txt"} <= audit_names, "audit seal files missing")
    require((AUDIT / "raw").is_dir(), "audit raw directory missing")

    inputs = tsv(RESEARCH / "02_ROUND9_INPUT_TERM_REGISTRY.tsv")
    require(len(inputs) == 16, "input row count is not 16")
    require([row["candidate_label"] for row in inputs] == EXPECTED_LABELS, "input labels/order changed")
    require(len({row["candidate_id"] for row in inputs}) == 16, "duplicate input candidate ID")
    require(len({row["sense_id"] for row in inputs}) == 16, "duplicate input sense ID")
    require(all(row["round9_final_decision"].startswith("PASS_TO_GRAMMAR_RESEARCH") for row in inputs), "non-passing Round 9 input entered")
    require(all(row["round9_grammar_selected"] == "false" and row["exact_input_verified"] == "true" for row in inputs), "Round 9 input gate failed")
    identity = "\n".join(f"{r['candidate_id']}\t{r['sense_id']}\t{r['candidate_label']}\t{r['round9_final_decision']}" for r in inputs) + "\n"
    input_hash = digest(identity.encode())
    require(input_hash == "da22e62828b9d6ae2dd1692ec4f23b82a984ce9d53240d198246915668481aec", "input identity hash changed")

    round9_rows = tsv(ROUND9 / "04_RAW_CANDIDATE_TERM_REGISTRY.tsv")
    round9_pass = [row for row in round9_rows if row["final_decision"].startswith("PASS_TO_GRAMMAR_RESEARCH")]
    require([(r["candidate_id"], r["candidate_label"]) for r in round9_pass] == [(r["candidate_id"], r["candidate_label"]) for r in inputs], "Round 9 passing set was not reproduced exactly")

    sources = tsv(RESEARCH / "03_GRAMMAR_SCHOLARLY_SOURCE_REGISTRY.tsv")
    source_ids = {row["source_id"] for row in sources}
    require(len(sources) >= 24 and len(source_ids) == len(sources), "source count/identity gate failed")
    require(all(row["new_for_round10"] == "true" and row["metadata_verified"] == "true" for row in sources), "unverified or non-new grammar source")
    for row in sources:
        for field in ("authors", "year", "title", "publication", "source_class", "publisher", "doi_isbn", "stable_publisher_url", "source_language", "source_stratum", "discovery_batch"):
            require(bool(row[field].strip()), f"empty source metadata {row['source_id']}:{field}")
    require(len({r["publication"] for r in sources}) >= 20, "venue breadth is too narrow")
    require(len({r["publisher"] for r in sources}) >= 10, "publisher breadth is too narrow")
    require(len({r["source_language"] for r in sources}) >= 3, "language breadth is too narrow")
    require(len({r["source_stratum"] for r in sources}) >= 15, "source-stratum breadth is too narrow")

    attestations = tsv(RESEARCH / "07_GRAMMAR_ATTESTATION_REGISTRY.tsv")
    att_ids = {row["grammar_attestation_id"] for row in attestations}
    require(len(attestations) >= 25 and len(att_ids) == len(attestations), "attestation count/identity gate failed")
    for row in attestations:
        require(row["source_id"] in source_ids, f"orphan source in {row['grammar_attestation_id']}")
        require(row["candidate_label"] in EXPECTED_LABELS, f"orphan term in {row['grammar_attestation_id']}")
        for field in ("exact_attested_noun", "bounded_context", "page_section_locator", "observed_subject_role", "observed_target_role", "observed_additional_parties", "observed_directionality", "observed_qualifier", "observed_contestation", "evidence_sha256"):
            require(bool(row[field].strip()), f"empty attestation field {row['grammar_attestation_id']}:{field}")
        require(row["exact_attested_noun"].lower() in row["bounded_context"].lower(), f"exact noun absent from bounded context {row['grammar_attestation_id']}")
        require(row["metadata_verified"] == "true", f"unverified attestation {row['grammar_attestation_id']}")

    nodes = tsv(RESEARCH / "05_NODE_ROLE_DECISION_REGISTRY.tsv")
    require(len(nodes) == 16 and {r["candidate_label"] for r in nodes} == set(EXPECTED_LABELS), "node review is not exact")
    require(all(r["primary_technical_role"] in NODE_ROLES for r in nodes), "invalid technical node role")
    require(all(r["final_node_role_decision"] in NODE_DECISIONS for r in nodes), "invalid node decision")
    node_by_id = {row["candidate_id"]: row for row in nodes}
    node_counts = Counter(r["final_node_role_decision"] for r in nodes)
    require(sum(v for k, v in node_counts.items() if k.startswith("PASS_")) == 8, "passing node count changed")
    require(sum(v for k, v in node_counts.items() if k.startswith("DEFER_")) == 8, "deferred node count changed")

    derivation = tsv(RESEARCH / "04_NODE_DERIVATION_REGISTRY.tsv")
    require(len(derivation) == 16 and {r["candidate_id"] for r in derivation} == set(node_by_id), "derivation coverage failed")
    for row in derivation:
        require(row["orphan"] == "false" and row["all_provenance_links_verified"] == "true", f"orphan derivation {row['candidate_id']}")
        require(split_ids(row["new_grammar_source_ids"]) and set(split_ids(row["new_grammar_source_ids"])) <= source_ids, f"invalid new sources {row['candidate_id']}")
        require(split_ids(row["new_grammar_attestation_ids"]) and set(split_ids(row["new_grammar_attestation_ids"])) <= att_ids, f"invalid new attestations {row['candidate_id']}")
        require(row["node_role_decision"] == node_by_id[row["candidate_id"]]["final_node_role_decision"], f"derivation decision mismatch {row['candidate_id']}")

    arguments = tsv(RESEARCH / "06_ARGUMENT_ROLE_REGISTRY.tsv")
    require(len(arguments) == 16 and {r["candidate_id"] for r in arguments} == set(node_by_id), "argument-role coverage failed")
    role_fields = ("arity", "subject_role", "target_role", "additional_party_roles", "input_state", "output_state", "required_context", "required_qualification", "scope_in", "scope_out")
    for row in arguments:
        require(all(row[field].strip() for field in role_fields), f"empty role field {row['candidate_id']}")
        require(row["contains_any_role"] == "false" and row["empty_role_count"] == "0", f"unbounded role {row['candidate_id']}")
        require(all(token.strip().upper() != "ANY" for field in ("subject_role", "target_role", "additional_party_roles") for token in row[field].replace(";", " ").split()), f"ANY role text {row['candidate_id']}")

    directions = tsv(RESEARCH / "10_DIRECTIONALITY_AND_ARITY.tsv")
    allowed_directions = {"DIRECTED", "RECIPROCAL", "REFLEXIVE", "MULTIPARTY", "STRUCTURAL_NON_EDGE", "MIXED_USAGE_DEFER", "UNRESOLVED_DEFER"}
    require(len(directions) == 16 and all(r["directionality_decision"] in allowed_directions for r in directions), "directionality gate failed")
    require(all(r["self_loop_authorized"] == "false" for r in directions), "self-loop authorization found")
    require(all(r["visual_arrow_authorized"] == "false" for r in directions), "an arrow is authorized without a passing directed pair rule")
    att_by_candidate = defaultdict(list)
    for row in attestations:
        att_by_candidate[row["candidate_term_id"]].append(row)
    for row in nodes:
        if row["primary_technical_role"] == "DIRECTED_STATE_TRANSITION":
            require(any(att["observed_state_transition"] != "no bounded before-to-after transition attested" for att in att_by_candidate[row["candidate_id"]]), f"state-transition node lacks transition evidence {row['candidate_id']}")

    qualifications = tsv(RESEARCH / "11_QUALIFICATION_AND_CONTESTATION.tsv")
    require(len(qualifications) == 16, "qualification coverage failed")
    require(all(r["contestation_preserved"] == "true" and r["historical_shift_preserved"] == "true" and r["source_bounded_meaning_preserved"] == "true" and r["normative_qualifier_loss"] == "false" for r in qualifications), "qualification/contestation loss")

    matrix = tsv(RESEARCH / "08_ORDERED_PAIR_COMPATIBILITY_MATRIX.tsv")
    input_ids = [r["candidate_id"] for r in inputs]
    expected_keys = {f"{s}->{t}" for s in input_ids for t in input_ids}
    require(len(matrix) == 256 and {r["ordered_pair_key"] for r in matrix} == expected_keys, "ordered-pair Cartesian coverage failed")
    require(all(r["decision"] in PAIR_DECISIONS for r in matrix), "invalid pair decision")
    matrix_by_key = {r["ordered_pair_key"]: r for r in matrix}
    pair_counts = Counter(r["decision"] for r in matrix)
    require(sum(v for k, v in pair_counts.items() if k.startswith("PASS_")) == 0, "unexpected passing pair")
    require(sum(v for k, v in pair_counts.items() if k.startswith("DEFER_")) == 3, "deferred pair count changed")
    require(pair_counts["REJECT_SELF_RELATION"] == 16, "diagonal review count changed")
    require(pair_counts["UNSUPPORTED_DEFAULT_DENY"] == 237, "default-deny count changed")
    for row in matrix:
        if row["source_candidate_id"] == row["target_candidate_id"]:
            require(row["decision"] == "REJECT_SELF_RELATION", f"diagonal not rejected {row['ordered_pair_key']}")
        require(row["natural_language_explanation_complete"] == "true", f"missing pair explanation {row['ordered_pair_key']}")
        expected_review = "PENDING_REVIEW" if allow_pending_reviews else "PASS_REVIEW_COMPLETE"
        require(row["semantic_review_status"] == row["adversarial_review_status"] == row["universal_node_review_status"] == expected_review, f"pair review status failed {row['ordered_pair_key']}")

    rules = tsv(RESEARCH / "09_FLOW_RULE_CANDIDATE_REGISTRY.tsv")
    require(len(rules) == 3, "flow candidate count changed")
    for row in rules:
        key = f"{row['source_candidate_id']}->{row['target_candidate_id']}"
        require(key in matrix_by_key and row["final_rule_decision"] == matrix_by_key[key]["decision"], f"flow/matrix mismatch {key}")
        require(row["final_rule_decision"].startswith("DEFER_"), f"unexpected flow pass {key}")
        require(row["natural_language_explanation"].strip() and row["scope_out"].strip() and row["qualification"].strip(), f"incomplete flow explanation {key}")
        require(row["semantic_review_status"] == row["adversarial_review_status"] == row["universal_node_review_status"] == expected_review, f"flow review status failed {key}")

    universal = tsv(RESEARCH / "12_UNIVERSAL_NODE_AUDIT.tsv")
    require(len(universal) == 16, "universal-node review coverage failed")
    actual_universal = {r["candidate_label"] for r in universal if r["universal_node_candidate"] == "true"}
    require(actual_universal == UNIVERSAL_LABELS, "universal-node candidates changed")
    require(all(r["universal_node_passed"] == "false" and r["any_role_usage"] == "false" and r["literal_any_token"] == "false" and r["repeated_bridge_use"] == "false" for r in universal), "universal-node gate failed")
    require({r["candidate_label"] for r in universal if r["semantic_any_like_role"] == "true"} == UNIVERSAL_LABELS, "semantic any-like audit changed")
    require(max(int(r["allowed_out_degree"]) for r in universal) == 0 and max(int(r["allowed_in_degree"]) for r in universal) == 0, "allowed degree is nonzero")

    flattening = tsv(RESEARCH / "13_SEMANTIC_FLATTENING_REVIEW.tsv")
    require(len(flattening) == 16, "flattening review coverage failed")
    require(all(r["synonym_merge_performed"] == "false" and r["sense_collapse_performed"] == "false" and r["semantic_flattening_found"] == "false" for r in flattening), "semantic flattening found")

    explanations = tsv(RESEARCH / "16_GRAMMAR_NATURAL_LANGUAGE_EXPLANATIONS.tsv")
    require(len([r for r in explanations if r["record_type"] == "NODE"]) == 16, "node explanation coverage failed")
    require(len([r for r in explanations if r["record_type"] == "PAIR"]) == 3, "pair explanation coverage failed")
    require(all(r["plain_language_explanation"].strip() and r["research_question_example"].strip() and r["conceptual_field_example"].strip() and r["non_object_example"] == "true" and r["non_circular"] == "true" and r["explanation_verified"] == "true" for r in explanations), "natural-language gate failed")

    verification = tsv(RESEARCH / "17_FULL_VERIFICATION_MATRIX.tsv")
    process_receipts = tsv(AUDIT / "raw/multi_agent_process_receipts.tsv")
    receipt_ids = {r["process_receipt_id"] for r in process_receipts}
    require(len(process_receipts) == 7 and {r["reviewer_role"] for r in process_receipts} == REVIEWER_ROLES, "multi-agent process receipt coverage failed")
    expected_receipt_outcome = "PENDING_INDEPENDENT_REVIEW" if allow_pending_reviews else "PASS_AFTER_INDEPENDENT_REVIEW"
    expected_independence = "false" if allow_pending_reviews else "true"
    require(all(r["final_outcome"] == expected_receipt_outcome and r["independent_of_generator"] == expected_independence and r["computational_review"] == "true" and r["external_human_domain_review"] == "false" for r in process_receipts), "multi-agent process receipt status failed")
    if allow_pending_reviews:
        require(all(r["finding_and_resolution"] == "review pending; no finding serialized" for r in process_receipts), "pending receipt contains a prefilled conclusion")
    else:
        require(all(r["finding_and_resolution"] != "review pending; no finding serialized" for r in process_receipts), "final receipt lacks a finding")
    require(len(verification) == 7 * (16 + 256), "full verification row count failed")
    grouped: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in verification:
        expected_matrix_review = "PENDING_REVIEW" if allow_pending_reviews else "PASS_REVIEW_COMPLETE"
        expected_matrix_independence = "false" if allow_pending_reviews else "true"
        require(row["reviewer_role"] in REVIEWER_ROLES and row["process_receipt_id"] in receipt_ids and row["review_decision"] == expected_matrix_review and row["independent_process"] == expected_matrix_independence, f"invalid verification row {row['verification_id']}")
        grouped[(row["record_type"], row["record_key"])].add(row["reviewer_role"])
    expected_records = {("NODE_ROLE", cid) for cid in input_ids} | {("ORDERED_PAIR_CELL", key) for key in expected_keys}
    require(set(grouped) == expected_records and all(roles == REVIEWER_ROLES for roles in grouped.values()), "verification role coverage failed")

    clusters = tsv(RESEARCH / "14_CLUSTER_EVIDENCE_HANDOFF.tsv")
    require(all(len(split_ids(r["candidate_term_ids"])) >= 3 and r["synonym_collapse"] == "false" and r["equivalence_claim"] == "false" for r in clusters), "cluster handoff gate failed")
    chains = tsv(RESEARCH / "15_OBSERVED_RELATION_CHAIN_REGISTRY.tsv")
    require(all(r["transitive_inference"] == "false" and r["active_grammar_selected"] == "false" for r in chains), "transitive or active chain found")
    gaps = tsv(RESEARCH / "20_VOCABULARY_GAP_REGISTER.tsv")
    require(all(r["new_public_label_created"] == "false" for r in gaps), "new public vocabulary created")

    current_text = (ROOT / "docs/research/EXPLORATION_CURRENT.md").read_text(encoding="utf-8")
    require("UNRESOLVED_RELATION_VOCABULARY_VERSION" in current_text and "UNRESOLVED_RELATION_GRAMMAR_VERSION" in current_text, "active unresolved versions changed")
    require("FINAL_ACTIVE_RELATION_TYPE_COUNT=0" in current_text, "active relation type count changed")

    status_lines = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).splitlines()
    changed_paths = []
    for line in status_lines:
        path = line[3:].split(" -> ")[-1]
        changed_paths.append(path)
    allowed_prefixes = (
        "docs/research/trace-v49-design-history-relation-grammar-round1/",
        "docs/audits/v49-design-history-relation-grammar-round1/",
        "scripts/trace-v49-relation-grammar/",
    )
    allowed_exact = {"PROJECT_LOG.md", "docs/research/EXPLORATION_CURRENT.md"}
    require(all(path in allowed_exact or path.startswith(allowed_prefixes) for path in changed_paths), f"protected path changed: {changed_paths}")
    require(all("__pycache__/" not in path and not path.endswith(".pyc") for path in changed_paths), "generated Python cache entered changed paths")

    manifest = tsv(AUDIT / "MANIFEST.tsv")
    require(len({r["path"] for r in manifest}) == len(manifest), "duplicate manifest path")
    required_support = {"PROJECT_LOG.md", "docs/research/EXPLORATION_CURRENT.md", "scripts/trace-v49-relation-grammar/generate_round1.py", "scripts/trace-v49-relation-grammar/validate_round1.py"}
    require(required_support <= {r["path"] for r in manifest}, "support files missing from manifest")
    for row in manifest:
        path = ROOT / row["path"]
        require(path.is_file(), f"manifest path missing: {row['path']}")
        require(path.stat().st_size == int(row["bytes"]), f"manifest size mismatch: {row['path']}")
        require(digest(path.read_bytes()) == row["sha256"], f"manifest hash mismatch: {row['path']}")
    checksum_rows = {}
    for line in (AUDIT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        checksum, path = line.split("  ", 1)
        checksum_rows[path] = checksum
    require(len(checksum_rows) == len(manifest) + 1 and "docs/audits/v49-design-history-relation-grammar-round1/MANIFEST.tsv" in checksum_rows, "checksum coverage failed")
    for path, checksum in checksum_rows.items():
        require(digest((ROOT / path).read_bytes()) == checksum, f"checksum mismatch: {path}")

    print("ROUND10_VALIDATION=PASS")
    print(f"ROUND9_INPUT_TERM_COUNT={len(inputs)}")
    print(f"ROUND9_INPUT_TERM_HASH={input_hash}")
    print(f"GRAMMAR_SCHOLARLY_SOURCE_COUNT={len(sources)}")
    print(f"GRAMMAR_ATTESTATION_COUNT={len(attestations)}")
    print(f"NODE_ROLE_REVIEW_COUNT={len(nodes)}")
    print(f"NODE_ROLE_FULL_VERIFICATION_RATE={'PENDING' if allow_pending_reviews else '1.0'}")
    print("NODE_ROLE_STRUCTURAL_COVERAGE_RATE=1.0")
    print(f"ORDERED_PAIR_MATRIX_CELL_COUNT={len(matrix)}")
    print(f"PAIR_MATRIX_REVIEW_RATE={'PENDING' if allow_pending_reviews else '1.0'}")
    print("PAIR_MATRIX_STRUCTURAL_COVERAGE_RATE=1.0")
    print(f"DEFER_PAIR_RULE_COUNT={sum(v for k, v in pair_counts.items() if k.startswith('DEFER_'))}")
    print(f"REJECT_PAIR_RULE_COUNT={sum(v for k, v in pair_counts.items() if k.startswith('REJECT_'))}")
    print(f"UNSUPPORTED_DEFAULT_DENY_COUNT={pair_counts['UNSUPPORTED_DEFAULT_DENY']}")
    print(f"UNIVERSAL_NODE_CANDIDATE_COUNT={len(actual_universal)}")
    print("UNIVERSAL_NODE_PASS_COUNT=0")
    print("MAX_ALLOWED_OUT_DEGREE=0")
    print("MAX_ALLOWED_IN_DEGREE=0")
    print(f"FULL_VERIFICATION_ROW_COUNT={len(verification)}")
    print(f"MANIFEST_ROW_COUNT={len(manifest)}")
    print("AUDIT_SEAL=PASS")


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--allow-pending-reviews", action="store_true")
        args = parser.parse_args()
        main(allow_pending_reviews=args.allow_pending_reviews)
    except (AssertionError, subprocess.CalledProcessError, OSError, ValueError) as error:
        print(f"ROUND10_VALIDATION=FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
