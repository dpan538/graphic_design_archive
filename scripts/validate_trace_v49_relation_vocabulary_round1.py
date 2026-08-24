#!/usr/bin/env python3
"""Deterministic hard-gate verifier for TRACE v49 relation vocabulary Round 1."""

from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "docs/research/trace-v49-design-history-relation-vocabulary-round1"
AUDIT = ROOT / "docs/audits/v49-design-history-relation-vocabulary-round1"
RAW = AUDIT / "raw"
SOURCE_SHA = "0526c3375285d8785d2993cdad9d1da620766423"
REGISTRY_VERSION = "trace-design-history-relation-candidates-v1"
REGISTRY_SHA = "818b306406d6a557a563ec285ae36394106c4c88a3e14cae19e4f1da4e92f4d5"
ROLES = {"DISCOVERY", "VERIFY_A", "VERIFY_B", "SEMANTIC_VERIFY", "ADVERSARIAL_REVIEW"}
PASS_DECISIONS = {"PASS_TO_GRAMMAR_RESEARCH", "PASS_TO_GRAMMAR_RESEARCH_FOUNDATIONAL_TERM"}
ALLOWED_DECISIONS = PASS_DECISIONS | {
    "DEFER_SINGLE_ATTESTATION", "DEFER_TRANSLATION", "DEFER_SEMANTIC_AMBIGUITY",
    "DEFER_SEMANTICALLY_UNEXPLAINABLE", "DEFER_INSUFFICIENT_DESIGN_HISTORY_USAGE",
    "REJECT_NOT_RELATIONAL", "REJECT_TOPIC_OR_ENTITY", "REJECT_UNATTESTED_NOMINALIZATION",
    "REJECT_GENERIC_NON_DESIGN_HISTORY_TERM", "REJECT_IMPORTED_THEORY_WITHOUT_DESIGN_HISTORY_USE",
    "REJECT_ONE_OFF_METAPHOR", "REJECT_UNVERIFIABLE_SOURCE", "REJECT_OTHER_WITH_REASON",
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def fail(message: str) -> None:
    raise AssertionError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def unique_ids(rows: list[dict[str, str]], key: str, label: str) -> set[str]:
    values = [row[key] for row in rows]
    require(all(values), f"{label}: blank {key}")
    require(len(values) == len(set(values)), f"{label}: duplicate {key}")
    return set(values)


def verify_checksums() -> None:
    manifest = read_tsv(AUDIT / "MANIFEST.tsv")
    manifest_paths = unique_ids(manifest, "path", "manifest")
    for row in manifest:
        path = ROOT / row["path"]
        require(path.is_file(), f"manifest missing file: {row['path']}")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"], f"manifest hash mismatch: {row['path']}")
        require(path.stat().st_size == int(row["bytes"]), f"manifest byte mismatch: {row['path']}")
    checksum_lines = (AUDIT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    require(len(checksum_lines) == len(manifest) + 1, "checksum row count mismatch")
    seen: set[str] = set()
    for line in checksum_lines:
        digest, rel = line.split("  ", 1)
        path = ROOT / rel
        require(path.is_file(), f"checksum missing file: {rel}")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, f"checksum mismatch: {rel}")
        seen.add(rel)
    require(manifest_paths <= seen, "checksums omit manifest entry")
    require("docs/audits/v49-design-history-relation-vocabulary-round1/MANIFEST.tsv" in seen, "manifest is not checksummed")


def verify_changed_files() -> None:
    output = subprocess.run(
        ["git", "diff", "--name-only", SOURCE_SHA, "HEAD"], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout.splitlines()
    allowed_exact = {
        "PROJECT_LOG.md", "docs/research/EXPLORATION_CURRENT.md",
        "scripts/validate_trace_v49_relation_vocabulary_round1.py",
        "scripts/trace-v49-relation-vocabulary/generate_round1.py",
    }
    allowed_prefixes = (
        "docs/research/trace-v49-design-history-relation-vocabulary-round1/",
        "docs/audits/v49-design-history-relation-vocabulary-round1/",
    )
    disallowed = [path for path in output if path not in allowed_exact and not path.startswith(allowed_prefixes)]
    require(not disallowed, f"out-of-scope changed files: {disallowed}")
    protected_prefixes = (
        "database/", "frontend/src/app/search/", "frontend/src/features/search-v49/",
        "frontend/src/features/trace-v49/context/", "frontend/src/features/trace-v49/spacetime/",
        "frontend/src/lib/trace/exploration-domain.ts", "frontend/src/app/trace/exploration/",
        "frontend/src/app/api/trace/exploration/", "frontend/src/app/api/v1/trace/exploration/",
    )
    require(not [path for path in output if path.startswith(protected_prefixes)], "protected or active Exploration file changed")


def main() -> None:
    freeze = RAW / "candidate_registry_identity_v1.tsv"
    require(hashlib.sha256(freeze.read_bytes()).hexdigest() == REGISTRY_SHA, "candidate freeze hash mismatch")

    sources = read_tsv(RESEARCH / "03_SCHOLARLY_SOURCE_REGISTRY.tsv")
    candidates = read_tsv(RESEARCH / "04_RAW_CANDIDATE_TERM_REGISTRY.tsv")
    attestations = read_tsv(RESEARCH / "05_TERM_ATTESTATION_REGISTRY.tsv")
    matrix = read_tsv(RESEARCH / "06_TERM_VERIFICATION_MATRIX.tsv")
    glosses = read_tsv(RESEARCH / "07_SEMANTIC_GLOSS_REGISTRY.tsv")
    contestation = read_tsv(RESEARCH / "08_CONTESTATION_AND_POLYSEMY.tsv")
    synonyms = read_tsv(RESEARCH / "09_SYNONYM_AND_CONFUSABLE_REVIEW.tsv")
    directionality = read_tsv(RESEARCH / "10_DIRECTIONALITY_OBSERVATIONS.tsv")
    handoff = read_tsv(RESEARCH / "11_GRAMMAR_EVIDENCE_HANDOFF.tsv")
    rejected = read_tsv(RESEARCH / "12_REJECTED_AND_DEFERRED_TERMS.tsv")

    require(len(sources) == 50, "source count must be 50")
    require(len(candidates) == 33, "candidate count must be 33")
    require(len(attestations) == 55, "attestation count must be 55")
    require(len(matrix) == 165, "verification matrix must contain candidate x five roles")
    source_ids = unique_ids(sources, "source_id", "sources")
    candidate_ids = unique_ids(candidates, "candidate_id", "candidates")
    unique_ids(attestations, "attestation_id", "attestations")
    unique_ids(matrix, "verification_id", "verification matrix")

    required_candidate_fields = {
        "candidate_id", "candidate_label", "original_language_label", "published_translation_label",
        "grammatical_form", "noun_attested", "discovery_source_id", "discovery_locator",
        "observed_usage_role", "first_attestation_count", "peer_reviewed_article_attestation_count",
        "independent_scholarly_attestation_count", "plain_language_gloss_status",
        "directionality_observation_status", "contestation_status", "polysemy_status",
        "discovery_agent_id", "candidate_registry_version", "candidate_registry_sha256", "final_decision",
    }
    require(required_candidate_fields <= set(candidates[0]), "candidate schema incomplete")
    require(all(row["metadata_verified"] == "true" for row in sources), "source metadata verification incomplete")
    require(all(row["stable_publisher_url"].startswith("https://") for row in sources), "source stable URL missing")
    require(all(row["candidate_registry_version"] == REGISTRY_VERSION for row in candidates), "candidate version mismatch")
    require(all(row["candidate_registry_sha256"] == REGISTRY_SHA for row in candidates), "candidate hash binding mismatch")
    require(all(row["final_decision"] in ALLOWED_DECISIONS for row in candidates), "unknown candidate decision")
    require(all(row["noun_attested"] == "true" for row in candidates), "non-noun entered noun registry")
    require(all(row["discovery_source_id"] in source_ids for row in candidates), "candidate discovery source orphan")
    require(all(row["all_required_checks_complete"] == "true" for row in candidates), "candidate incomplete flag")

    for row in attestations:
        require(row["candidate_id"] in candidate_ids, f"orphan candidate attestation {row['attestation_id']}")
        require(row["source_id"] in source_ids, f"orphan source attestation {row['attestation_id']}")
        require(row["source_metadata_verified"] == "true" and row["attestation_verified"] == "true", f"unverified attestation {row['attestation_id']}")
        require(0 < int(row["context_word_count"]) <= 20, f"context word limit failed {row['attestation_id']}")
        require(int(row["context_word_count"]) == len(row["bounded_context"].split()), f"context count mismatch {row['attestation_id']}")
        require(hashlib.sha256(row["bounded_context"].encode()).hexdigest() == row["context_sha256"], f"context hash mismatch {row['attestation_id']}")
        require(row["exact_attested_term"].casefold() in row["bounded_context"].casefold(), f"exact term absent from context {row['attestation_id']}")

    by_candidate_roles: dict[str, set[str]] = defaultdict(set)
    by_candidate_results: dict[str, dict[str, str]] = defaultdict(dict)
    for row in matrix:
        require(row["candidate_id"] in candidate_ids, "orphan matrix row")
        require(row["candidate_registry_sha256"] == REGISTRY_SHA, "matrix hash mismatch")
        require(row["all_required_checks_complete"] == "true", "matrix incomplete check")
        by_candidate_roles[row["candidate_id"]].add(row["verification_role"])
        by_candidate_results[row["candidate_id"]][row["verification_role"]] = row["result"]
    require(all(by_candidate_roles[candidate_id] == ROLES for candidate_id in candidate_ids), "candidate missing required verification role")
    require(all(len([row for row in matrix if row["candidate_id"] == candidate_id]) == 5 for candidate_id in candidate_ids), "duplicate verification role")

    candidate_by_id = {row["candidate_id"]: row for row in candidates}
    pass_ids = {row["candidate_id"] for row in candidates if row["final_decision"] in PASS_DECISIONS}
    defer_ids = {row["candidate_id"] for row in candidates if row["final_decision"].startswith("DEFER_")}
    reject_ids = {row["candidate_id"] for row in candidates if row["final_decision"].startswith("REJECT_")}
    require((len(pass_ids), len(defer_ids), len(reject_ids)) == (16, 12, 5), "decision count mismatch")

    gloss_by_id = {row["candidate_id"]: row for row in glosses}
    require(set(gloss_by_id) == pass_ids, "semantic gloss rows must equal pass rows")
    attestation_counts = Counter(row["candidate_id"] for row in attestations if row["independent_scholarly_work"] == "true")
    for candidate_id in pass_ids:
        row = candidate_by_id[candidate_id]
        results = by_candidate_results[candidate_id]
        require(int(row["peer_reviewed_article_attestation_count"]) >= 1, f"pass lacks article {candidate_id}")
        require(int(row["independent_scholarly_attestation_count"]) >= 2, f"pass lacks second scholarly work {candidate_id}")
        require(attestation_counts[candidate_id] >= 2, f"pass lacks two attestation rows {candidate_id}")
        require(results["VERIFY_A"] == "VERIFY_A_PASS", f"pass failed verifier A {candidate_id}")
        require(results["VERIFY_B"] == "VERIFY_B_PASS", f"pass failed verifier B {candidate_id}")
        require(results["SEMANTIC_VERIFY"] == "SEMANTIC_PASS", f"pass failed semantic review {candidate_id}")
        require(results["ADVERSARIAL_REVIEW"] == "ADVERSARIAL_PASS", f"pass failed adversarial review {candidate_id}")
        gloss = gloss_by_id[candidate_id]
        require(gloss["plain_language_gloss"].startswith("In design-history scholarship,"), f"non-contract gloss {candidate_id}")
        require(gloss["explainability_pass"] == "true", f"explainability failed {candidate_id}")
        require({gloss["reviewer_1_comprehension"], gloss["reviewer_2_comprehension"], gloss["reviewer_3_comprehension"]} == {"YES"}, f"three-reviewer comprehension failed {candidate_id}")
        require(all(gloss[key] for key in ["natural_language_relation_frame", "why_relational", "scope_in", "scope_out", "subject_role_description", "object_role_description", "confusable_terms", "natural_language_test_A", "natural_language_test_B", "natural_language_test_C"]), f"semantic field missing {candidate_id}")

    require(len(contestation) == 33 and {row["candidate_id"] for row in contestation} == candidate_ids, "contestation coverage mismatch")
    require(sum(row["polysemy_status"] == "SEMANTIC_POLYSEMY_REQUIRES_SPLIT" for row in contestation) == 4, "polysemy split count mismatch")
    require(len(synonyms) == 33 and all(row["merge_decision"] == "KEEP_DISTINCT" for row in synonyms), "synonym merge gate failed")
    require(len(directionality) == 33 and {row["candidate_id"] for row in directionality} == candidate_ids, "directionality coverage mismatch")
    require({row["candidate_id"] for row in handoff} == pass_ids and len(handoff) == 16, "Round 10 handoff must equal pass set")
    require(all(row["relation_grammar_selected"] == "false" for row in handoff), "grammar selected prematurely")
    require({row["candidate_id"] for row in rejected} == defer_ids | reject_ids and len(rejected) == 17, "defer/reject ledger mismatch")

    source_class_counts = Counter(row["source_class"] for row in sources)
    require(source_class_counts["ARTICLE"] == 42, "peer-reviewed article corpus count mismatch")
    require(source_class_counts["BOOK"] + source_class_counts["CHAPTER"] == 6, "book/chapter count mismatch")
    require(source_class_counts["SCHOLARLY_EDITORIAL"] + source_class_counts["TRANSLATED_ARTICLE"] == 2, "supplementary count mismatch")
    strata = {item for row in sources for item in row["source_strata"].split("|")}
    require(len(strata) == 8, "all eight source strata not represented")
    require(len({row["discovery_batch"] for row in sources}) == 5, "saturation batch count mismatch")
    saturation = (RESEARCH / "14_LEXICAL_SATURATION_REPORT.md").read_text(encoding="utf-8")
    require("LEXICAL_SATURATION_REACHED=true" in saturation and "SATURATION_BATCH_COUNT=5" in saturation, "saturation gate failed")

    round10 = (RESEARCH / "17_ROUND10_GRAMMAR_HANDOFF.md").read_text(encoding="utf-8")
    require("ROUND10_INPUT_EQUALS_PASS_TERM_COUNT=true" in round10 and "RELATION_GRAMMAR_SELECTED=false" in round10, "Round 10 policy gate failed")
    verify_checksums()
    verify_changed_files()

    print("SOURCE_REGISTRY_VALIDATION=PASS")
    print("ATTESTATION_VALIDATION=PASS")
    print("FULL_CANDIDATE_VERIFICATION=PASS")
    print("NOUN_ATTESTATION_GATE=PASS")
    print("NATURAL_LANGUAGE_EXPLAINABILITY_GATE=PASS")
    print("POLYSEMY_CONTESTATION_GATE=PASS")
    print("SYNONYM_GATE=PASS")
    print("GLOBAL_SOURCE_BREADTH_GATE=PASS")
    print("LEXICAL_SATURATION_GATE=PASS")
    print("CANDIDATE_TERM_FULL_VERIFICATION_RATE=1.0")
    print("CANDIDATES_WITH_INCOMPLETE_VERIFICATION=0")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, subprocess.CalledProcessError) as exc:
        print(f"VALIDATION=FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
