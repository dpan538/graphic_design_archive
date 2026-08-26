#!/usr/bin/env python3
"""Unit and metamorphic tests for TRACE v49 Round 15."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
ENGINE = Path(__file__).resolve().parent
REPO = ENGINE.parents[1]
sys.path.insert(0, str(ENGINE))

from fixtures import FIXTURES  # noqa: E402
from model import (  # noqa: E402
    MAX_ADMITTED_DEGREE, METHOD_VERSION, TOPOLOGIES, FrozenInput,
    canonical_hash, compose, load_frozen_input, validate_image,
)


class Round15Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.frozen = load_frozen_input(REPO)
        cls.images = {fixture["fixtureId"]: compose(fixture, cls.frozen) for fixture in FIXTURES}

    def test_frozen_association_package_is_consumed_without_recalibration(self) -> None:
        self.assertEqual(self.frozen.package["methodVersion"], "trace-generic-association-rubric-v1")
        self.assertEqual(len(self.frozen.assessments), 35)
        self.assertEqual(sum(item["activeForProximity"] for item in self.frozen.assessments.values()), 21)
        self.assertEqual(sum(not item["activeForProximity"] for item in self.frozen.assessments.values()), 14)
        self.assertEqual(sum(item["hardNegative"] for item in self.frozen.assessments.values()), 10)
        fixture_inputs = {association_id for fixture in FIXTURES for association_id in fixture["associationIds"]}
        self.assertEqual(fixture_inputs, set(self.frozen.assessments))

    def test_failed_associations_are_structurally_ineligible(self) -> None:
        for image in self.images.values():
            admitted = set(image["semantic_core"]["admitted_association_ids"])
            controls = {
                item["assessment_id"] for item in image["composition_core"]["candidate_decisions"]
                if item["semantic_eligibility"] == "NOT_QUALIFIED"
            }
            self.assertFalse(admitted & controls)
            self.assertTrue(all(self.frozen.assessments[association_id]["activeForProximity"] for association_id in admitted))

    def test_candidate_roles_are_not_overloaded(self) -> None:
        fields = {
            "semantic_eligibility", "composition_eligibility", "neighbourhood_role",
            "topology_role", "presentation_role", "decision_state",
        }
        for image in self.images.values():
            for candidate in image["composition_core"]["candidate_decisions"]:
                self.assertTrue(fields <= set(candidate))
                if candidate["semantic_eligibility"] == "NOT_QUALIFIED":
                    self.assertEqual(candidate["composition_eligibility"], "INELIGIBLE")
                    self.assertEqual(candidate["decision_state"], "INELIGIBLE_CONTROL")

    def test_provenance_chain_is_complete_for_every_admission(self) -> None:
        for image in self.images.values():
            validate_image(image, self.frozen)
            admitted = set(image["semantic_core"]["admitted_association_ids"])
            self.assertEqual(admitted, {row["assessment_id"] for row in image["provenance"]})
            for row in image["provenance"]:
                self.assertTrue(row["evidence_ids"] and row["source_ids"] and row["source_urls"])
                self.assertTrue(all(url.startswith("https://") for url in row["source_urls"]))

    def test_input_order_pair_orientation_and_idempotence(self) -> None:
        for fixture in FIXTURES:
            baseline = self.images[fixture["fixtureId"]]
            permuted = copy.deepcopy(fixture)
            permuted["nodeIds"].reverse(); permuted["seedNodeIds"].reverse(); permuted["associationIds"].reverse()
            self.assertEqual(baseline["semantic_core_hash"], compose(permuted, self.frozen)["semantic_core_hash"])
            self.assertEqual(baseline["semantic_core_hash"], compose(fixture, self.frozen)["semantic_core_hash"])
        reversed_assessments = {}
        for key, original in self.frozen.assessments.items():
            item = dict(original); item["nodeA"], item["nodeB"] = item["nodeB"], item["nodeA"]
            reversed_assessments[key] = item
        reversed_frozen = FrozenInput(self.frozen.package, reversed_assessments, self.frozen.provenance)
        for fixture in FIXTURES:
            self.assertEqual(self.images[fixture["fixtureId"]]["semantic_core_hash"], compose(fixture, reversed_frozen)["semantic_core_hash"])

    def test_failed_and_duplicate_injection_are_semantically_invariant(self) -> None:
        fixture = next(item for item in FIXTURES if item["fixtureId"] == "R15-COMP-005")
        without_control = {**fixture, "associationIds": ["R14-ASSOC-016", "R14-ASSOC-021"]}
        self.assertEqual(compose(fixture, self.frozen)["semantic_core_hash"], compose(without_control, self.frozen)["semantic_core_hash"])
        duplicate = next(item for item in FIXTURES if item["fixtureId"] == "R15-COMP-013")
        without_duplicate = {**duplicate, "associationIds": ["R14-ASSOC-010", "R14-ASSOC-011"]}
        self.assertEqual(compose(duplicate, self.frozen)["semantic_core_hash"], compose(without_duplicate, self.frozen)["semantic_core_hash"])

    def test_semantic_and_presentation_hashes_are_separate(self) -> None:
        for fixture in FIXTURES:
            baseline = self.images[fixture["fixtureId"]]
            changed_seed = {**fixture, "visualSeed": fixture["visualSeed"] + "-changed"}
            changed = compose(changed_seed, self.frozen)
            self.assertEqual(baseline["semantic_core_hash"], changed["semantic_core_hash"])
            self.assertNotEqual(baseline["presentation_hash"], changed["presentation_hash"])
        sample = copy.deepcopy(next(iter(self.images.values())))
        old_hash = sample["semantic_core_hash"]
        sample["semantic_core"]["topology_type"] = "UNRESOLVED"
        self.assertNotEqual(old_hash, canonical_hash(sample["semantic_core"]))

    def test_all_six_topologies_are_distinct_and_exercised(self) -> None:
        selected = Counter(image["semantic_core"]["topology_type"] for image in self.images.values())
        self.assertTrue(all(selected[topology] >= 1 for topology in TOPOLOGIES))
        signatures = {
            "LINEAR_PATH": ("PATH", 1), "BINARY_FORK": ("FORK", 2),
            "BINARY_CONVERGENCE": ("CONVERGE", 2), "QUALIFIED_PATH": ("GATED_PATH", 1),
            "REFLEXIVE_RETURN": ("NAV_RETURN", 1), "EVIDENCE_GAP_TREE": ("GAP_BRANCH", 2),
        }
        self.assertEqual(len(set(signatures.values())), len(TOPOLOGIES))
        ambiguous = self.images["R15-COMP-004"]
        self.assertEqual(ambiguous["semantic_core"]["topology_type"], "UNRESOLVED")
        self.assertGreater(len(ambiguous["semantic_core"]["topology_candidates"]), 1)

    def test_pruning_split_gap_and_unresolved_explanations_are_bounded(self) -> None:
        state_counts = Counter(
            state["state"] for image in self.images.values()
            for state in image["semantic_core"]["association_states"]
        )
        for state in ("ADMITTED", "PRUNED", "SPLIT_BOUNDARY", "EVIDENCE_GAP", "UNRESOLVED"):
            self.assertGreater(state_counts[state], 0)
        for image in self.images.values():
            self.assertLessEqual(image["composition_core"]["degree_bound"], MAX_ADMITTED_DEGREE)
            for candidate in image["composition_core"]["candidate_decisions"]:
                self.assertTrue(candidate["reason_code"] and candidate["explanation"])
                self.assertNotIn("historically false", candidate["explanation"].lower())
                self.assertNotIn("disproved", candidate["explanation"].lower())

    def test_visual_contract_has_no_default_relation_leakage(self) -> None:
        for image in self.images.values():
            positions = image["presentation_hints"]["node_positions"]
            self.assertEqual({item["node_radius"] for item in positions}, {16})
            self.assertEqual({item["relative_layer"] for item in positions}, {0})
            self.assertTrue(all(not edge["arrowhead"] and edge["stroke_width"] == 2 for edge in image["presentation_hints"]["edge_hints"]))
            self.assertFalse(image["presentation_hints"]["semantic_mutation_permitted"])

    def test_no_relation_inflation_or_product_input(self) -> None:
        payload = json.dumps([
            {key: image[key] for key in ("semantic_core", "evidence_core", "composition_core", "presentation_hints", "provenance")}
            for image in self.images.values()
        ], ensure_ascii=False)
        for token in ("typed_relation", "causal_relation", "directional_relation", "hierarchical_relation", "archiveObjectId", "contextDTO", "spacetimeDTO", "embedding", "vectorDatabase"):
            self.assertNotIn(token, payload)
        self.assertEqual(METHOD_VERSION, "trace-evidence-governed-composition-v1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
