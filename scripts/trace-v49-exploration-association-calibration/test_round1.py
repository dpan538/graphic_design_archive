#!/usr/bin/env python3
"""Unit and conformance tests for TRACE v49 Round 14."""

from __future__ import annotations

import csv
import json
import sys
import unittest
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path

sys.dont_write_bytecode = True
ENGINE = Path(__file__).resolve().parent
REPO = ENGINE.parents[1]
sys.path.insert(0, str(ENGINE))

from calibration_input import build_inputs  # noqa: E402
from generate_round1 import canonical_hash, schema  # noqa: E402
from local_coherence import local_pairs, pair_key, repair_boolean_graph, validate_local_composition  # noqa: E402
from model import (  # noqa: E402
    DIRECT_POLICIES, DIMENSIONS, GENERIC_TYPES, SELECTED_DIRECT_POLICY, SELECTED_SKIP_POLICY,
    SKIP_POLICIES, assess, confusion, perturb, policy_pass,
)
from nary_fixtures import NARY_FIXTURES  # noqa: E402


class Round14Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases, cls.evidence = build_inputs(REPO)
        cls.evidence_by_assessment = defaultdict(list)
        for row in cls.evidence:
            cls.evidence_by_assessment[row["assessment_id"]].append(row)
        cls.decisions = {case.assessment_id: assess(case, cls.evidence_by_assessment[case.assessment_id]) for case in cls.cases}

    def test_bounded_calibration_strata_and_type_coverage(self) -> None:
        self.assertEqual(len(self.cases), 35)
        self.assertEqual(Counter(case.calibration_stratum for case in self.cases), {"CLEAR_POSITIVE": 10, "BORDERLINE": 12, "NEGATIVE": 13})
        self.assertEqual(sum(case.hard_negative for case in self.cases), 10)
        self.assertEqual({case.primary_generic_type for case in self.cases}, set(GENERIC_TYPES))
        self.assertTrue(all(case.secondary_generic_type != case.primary_generic_type for case in self.cases))

    def test_evidence_channels_status_and_redirects(self) -> None:
        statuses = Counter(item["evidenceStatus"] for item in self.decisions.values())
        self.assertEqual(statuses, {"EXTERNALLY_SUPPORTED": 18, "SOURCE_SUPPORTED": 3, "QUALIFIED": 1, "INSUFFICIENT": 13})
        for item in self.decisions.values():
            if item["evidenceStatus"] == "SOURCE_SUPPORTED":
                self.assertTrue(item["archiveSourceRefs"])
                self.assertFalse(item["externalSourceRefs"])
                self.assertIn("Independent scholarly validation pending", item["qualification"])
            if item["evidenceStatus"] == "EXTERNALLY_SUPPORTED":
                self.assertTrue(item["externalSourceRefs"])
            if item["activeForProximity"]:
                self.assertTrue(item["redirectTargets"])
                self.assertTrue(all(url.startswith("https://") for url in item["redirectTargets"]))

    def test_cooccurrence_insufficient_and_qualification_gates(self) -> None:
        self.assertEqual(sum(case.cooccurrence_only and self.decisions[case.assessment_id]["activeForProximity"] for case in self.cases), 0)
        self.assertTrue(all(not item["activeForProximity"] for item in self.decisions.values() if item["evidenceStatus"] == "INSUFFICIENT"))
        qualified = [item for item in self.decisions.values() if item["evidenceStatus"] == "QUALIFIED"]
        self.assertEqual(len(qualified), 1)
        self.assertFalse(qualified[0]["activeForProximity"])
        self.assertTrue(qualified[0]["qualification"])

    def test_direct_and_skip_thresholds_are_deterministic(self) -> None:
        self.assertEqual(SELECTED_DIRECT_POLICY.minimum_strength, "MODERATE")
        self.assertEqual(SELECTED_SKIP_POLICY.minimum_strength, "MODERATE")
        self.assertEqual(SELECTED_DIRECT_POLICY.allowed_statuses, SELECTED_SKIP_POLICY.allowed_statuses)
        for case in self.cases:
            first = assess(case, self.evidence_by_assessment[case.assessment_id])
            second = assess(case, self.evidence_by_assessment[case.assessment_id])
            self.assertEqual(first, second)
            self.assertEqual(first["directNeighbourPass"], case.expected_direct_pass)
            self.assertEqual(first["skipOnePass"], case.expected_skip_one_pass)

    def test_threshold_boundary_and_false_positive_priority(self) -> None:
        selected = next(case for case in self.cases if case.assessment_id == "R14-ASSOC-012")
        self.assertTrue(self.decisions[selected.assessment_id]["directNeighbourPass"])
        lowered = perturb(selected, "D1", -1)
        self.assertFalse(assess(lowered, self.evidence_by_assessment[selected.assessment_id])["directNeighbourPass"])
        qualified = self.decisions["R14-ASSOC-022"]
        permissive = DIRECT_POLICIES[3]
        self.assertTrue(policy_pass(qualified["associationStrength"], qualified["evidenceConfidence"], qualified["evidenceStatus"], permissive))
        self.assertFalse(qualified["directNeighbourPass"])

    def test_sweep_reproduces_expected_confusions(self) -> None:
        for policy in (*DIRECT_POLICIES, *SKIP_POLICIES):
            expected = [case.expected_direct_pass if policy.neighbourhood == "DIRECT" else case.expected_skip_one_pass for case in self.cases]
            actual = [policy_pass(self.decisions[case.assessment_id]["associationStrength"], self.decisions[case.assessment_id]["evidenceConfidence"], self.decisions[case.assessment_id]["evidenceStatus"], policy) for case in self.cases]
            matrix = confusion(expected, actual)
            if policy.selected:
                self.assertEqual(matrix["false_positive"], 0)
                self.assertEqual(matrix["false_negative"], 0)
        self.assertGreater(confusion([case.expected_direct_pass for case in self.cases], [policy_pass(self.decisions[case.assessment_id]["associationStrength"], self.decisions[case.assessment_id]["evidenceConfidence"], self.decisions[case.assessment_id]["evidenceStatus"], DIRECT_POLICIES[3]) for case in self.cases])["false_positive"], 0)

    def test_all_six_topology_local_rules(self) -> None:
        self.assertEqual(len(NARY_FIXTURES), 6)
        self.assertEqual({fixture["strategy"] for fixture in NARY_FIXTURES}, {"LINEAR_PATH", "BINARY_FORK", "BINARY_CONVERGENCE", "QUALIFIED_PATH", "REFLEXIVE_RETURN", "EVIDENCE_GAP_TREE"})
        for fixture in NARY_FIXTURES:
            with self.subTest(strategy=fixture["strategy"]):
                result = validate_local_composition(fixture, self.decisions)
                self.assertEqual(result["result"], fixture["expectedResult"])
                self.assertEqual(set(result["directPairs"] + result["skipOnePairs"]), set(fixture["pairBindings"]))
        reflexive = next(fixture for fixture in NARY_FIXTURES if fixture["strategy"] == "REFLEXIVE_RETURN")
        self.assertNotIn(pair_key(*reflexive["navigationReturn"]), local_pairs(reflexive["nodes"], [tuple(edge) for edge in reflexive["semanticEdges"]])[0])

    def test_pruning_terminal_internal_skip_and_branch(self) -> None:
        terminal = repair_boolean_graph(["A", "B", "C"], [("A", "B"), ("B", "C")], {"A|B": True, "B|C": False, "A|C": False})
        self.assertEqual(terminal["result"], "PRUNED")
        self.assertEqual(terminal["prunedNodes"], ["C"])
        internal = repair_boolean_graph(["A", "B", "C", "D"], [("A", "B"), ("B", "C"), ("C", "D")], {"A|B": True, "B|C": False, "C|D": True, "A|C": False, "B|D": False})
        self.assertEqual(internal["result"], "SPLIT")
        self.assertEqual(internal["components"], [["A", "B"], ["C", "D"]])
        skip = repair_boolean_graph(["A", "B", "C"], [("A", "B"), ("B", "C")], {"A|B": True, "B|C": True, "A|C": False})
        self.assertEqual(skip["result"], "SPLIT")
        branch = repair_boolean_graph(["A", "B", "C"], [("A", "B"), ("A", "C")], {"A|B": True, "A|C": False, "B|C": False})
        self.assertEqual(branch["prunedNodes"], ["C"])

    def test_schema_and_package_hash(self) -> None:
        value = schema()
        self.assertEqual(value["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(value["additionalProperties"])
        self.assertFalse(value["$defs"]["assessment"]["additionalProperties"])
        package = json.loads((ENGINE / "fixtures/association-assessments-v1.json").read_text(encoding="utf-8"))
        canonical = package.pop("canonicalHash")
        self.assertEqual(canonical_hash(package), canonical)
        self.assertTrue(package["pythonNormative"])
        self.assertEqual(package["typescriptMirrorMode"], "SCHEMA_AND_FROZEN_DECISION_VALIDATION_ONLY")

    def test_sensitivity_fixture_matches_generated_rows(self) -> None:
        path = REPO / "docs/audits/v49-exploration-association-calibration-round1/raw/sensitivity-analysis.tsv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual(len(rows), len(self.cases) * len(DIMENSIONS) * 2)
        changes = sum(row["direct_decision_changed"] == "true" for row in rows) + sum(row["skip_one_decision_changed"] == "true" for row in rows)
        self.assertLessEqual(changes * 10, len(rows) * 2)

    def test_round13_files_not_used_as_write_targets(self) -> None:
        package_paths = [path.as_posix() for path in ENGINE.rglob("*.py")]
        self.assertTrue(all("trace-v49-exploration-composition-review-round1" not in path for path in package_paths))
        reassessment = REPO / "docs/audits/v49-exploration-association-calibration-round1/raw/round13-reassessment.tsv"
        with reassessment.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["round13_file_mutated"] == "false" for row in rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
