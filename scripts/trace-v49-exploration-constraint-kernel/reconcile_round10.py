#!/usr/bin/env python3
"""Read-only reconciliation of the sealed Round 10 negative constraints."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "docs/research/trace-v49-design-history-relation-grammar-round1"
AUDIT = ROOT / "docs/audits/v49-design-history-relation-grammar-round1"
ROUND10_SHA = "4bd82deba482ec2fbf8c4856080151416fb8ee83"
EXPECTED_SEAL_FILE_SHA256 = "9eac6d0a4242ca83acfda88ee6db43317c540201659bbf37ab18f81420771f44"


def read_tsv(name: str) -> list[dict[str, str]]:
    with (RESEARCH / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify_round10_seal() -> None:
    def committed_bytes(path: str) -> bytes:
        return subprocess.run(
            ["git", "show", f"{ROUND10_SHA}:{path}"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout

    seal_relative = "docs/audits/v49-design-history-relation-grammar-round1/SHA256SUMS.txt"
    manifest_relative = "docs/audits/v49-design-history-relation-grammar-round1/MANIFEST.tsv"
    seal_bytes = committed_bytes(seal_relative)
    require(hashlib.sha256(seal_bytes).hexdigest() == EXPECTED_SEAL_FILE_SHA256, "Round 10 seal-file identity changed")
    require((ROOT / seal_relative).read_bytes() == seal_bytes, "Round 10 seal file differs from its authoritative commit")
    manifest_bytes = committed_bytes(manifest_relative)
    require((ROOT / manifest_relative).read_bytes() == manifest_bytes, "Round 10 manifest differs from its authoritative commit")
    manifest = list(csv.DictReader(io.StringIO(manifest_bytes.decode("utf-8")), delimiter="\t"))
    require(len(manifest) == 44, "Round 10 manifest row count changed")
    for row in manifest:
        historical = committed_bytes(row["path"])
        require(hashlib.sha256(historical).hexdigest() == row["sha256"], f"Round 10 manifest hash mismatch at authoritative commit: {row['path']}")
        if row["path"].startswith("docs/research/trace-v49-design-history-relation-grammar-round1/"):
            current = ROOT / row["path"]
            require(current.is_file(), f"Round 10 research input missing: {row['path']}")
            require(hashlib.sha256(current.read_bytes()).hexdigest() == row["sha256"], f"Round 10 research input changed: {row['path']}")


def reconcile() -> dict[str, object]:
    verify_round10_seal()
    inputs = read_tsv("02_ROUND9_INPUT_TERM_REGISTRY.tsv")
    nodes = read_tsv("05_NODE_ROLE_DECISION_REGISTRY.tsv")
    pairs = read_tsv("08_ORDERED_PAIR_COMPATIBILITY_MATRIX.tsv")
    universal = read_tsv("12_UNIVERSAL_NODE_AUDIT.tsv")
    clusters = read_tsv("14_CLUSTER_EVIDENCE_HANDOFF.tsv")
    chains = read_tsv("15_OBSERVED_RELATION_CHAIN_REGISTRY.tsv")
    gaps = read_tsv("20_VOCABULARY_GAP_REGISTER.tsv")

    node_decisions = Counter(row["final_node_role_decision"] for row in nodes)
    pair_decisions = Counter(row["decision"] for row in pairs)
    pass_nodes = sum(value for key, value in node_decisions.items() if key.startswith("PASS_"))
    defer_nodes = sum(value for key, value in node_decisions.items() if key.startswith("DEFER_"))
    pass_pairs = sum(value for key, value in pair_decisions.items() if key.startswith("PASS_"))
    defer_pairs = sum(value for key, value in pair_decisions.items() if key.startswith("DEFER_"))
    reject_pairs = sum(value for key, value in pair_decisions.items() if key.startswith("REJECT_"))
    default_pairs = pair_decisions["UNSUPPORTED_DEFAULT_DENY"]
    universal_candidates = sum(row["universal_node_candidate"] == "true" for row in universal)
    universal_passes = sum(row["universal_node_passed"] == "true" for row in universal)

    actual = {
        "round10Sha": ROUND10_SHA,
        "round10SealFileSha256": EXPECTED_SEAL_FILE_SHA256,
        "nodeInputCount": len(inputs),
        "passNodeRoleCount": pass_nodes,
        "deferNodeRoleCount": defer_nodes,
        "pairMatrixCount": len(pairs),
        "passPairRuleCount": pass_pairs,
        "deferPairRuleCount": defer_pairs,
        "rejectPairRuleCount": reject_pairs,
        "defaultDenyPairCount": default_pairs,
        "universalNodeCandidateCount": universal_candidates,
        "universalNodePassCount": universal_passes,
        "clusterHandoffCount": len(clusters),
        "observedChainCount": len(chains),
        "vocabularyGapCount": len(gaps),
    }
    expected = {
        "nodeInputCount": 16,
        "passNodeRoleCount": 8,
        "deferNodeRoleCount": 8,
        "pairMatrixCount": 256,
        "passPairRuleCount": 0,
        "deferPairRuleCount": 3,
        "rejectPairRuleCount": 16,
        "defaultDenyPairCount": 237,
        "universalNodeCandidateCount": 8,
        "universalNodePassCount": 0,
        "clusterHandoffCount": 2,
        "observedChainCount": 2,
        "vocabularyGapCount": 6,
    }
    for key, value in expected.items():
        require(actual[key] == value, f"Round 10 reconciliation mismatch for {key}: {actual[key]} != {value}")
    require(len({(row["source_candidate_id"], row["target_candidate_id"]) for row in pairs}) == 256, "Round 10 pair matrix has duplicate keys")
    return {**actual, "reconciliation": "PASS", "activeRuntimeImportAuthorized": False}


if __name__ == "__main__":
    try:
        print(json.dumps(reconcile(), indent=2, sort_keys=True))
    except (AssertionError, OSError) as exc:
        print(json.dumps({"reconciliation": "FAIL", "error": str(exc)}, indent=2))
        raise SystemExit(1)
