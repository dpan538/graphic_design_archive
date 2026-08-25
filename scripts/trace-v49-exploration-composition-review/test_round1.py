#!/usr/bin/env python3
"""Unit tests for Round 13 tree functions and preservation gates."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ENGINE = Path(__file__).resolve().parent
REPO = ENGINE.parents[1]
sys.path.insert(0, str(ENGINE))

from instance_v2 import compile_instance_v2, validate_instance_v2  # noqa: E402
from topology import STRATEGIES, assert_no_duplicate_topologies, build_tree, validate_tree  # noqa: E402


class Round13Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.nodes = [
            {"senseId": "SYN-A", "label": "A", "lexicalAttestationIds": ["LEX-A"], "grammarAttestationIds": ["GRAM-A"]},
            {"senseId": "SYN-B", "label": "B", "lexicalAttestationIds": ["LEX-B"], "grammarAttestationIds": ["GRAM-B"]},
        ]

    def test_six_distinct_topologies(self) -> None:
        fixtures = {strategy: build_tree(strategy, strategy, "How should A and B be investigated?", self.nodes, ["GRAM-A"], ["GAP-A"]) for strategy in STRATEGIES}
        assert_no_duplicate_topologies(fixtures)

    def test_strategy_invariants(self) -> None:
        for strategy in STRATEGIES:
            items = build_tree(strategy, strategy, "How should A and B be investigated?", self.nodes, ["GRAM-A"], ["GAP-A"])
            validate_tree(strategy, items)
            self.assertLessEqual(len(items), 7)
            self.assertLessEqual(max(item["depth"] for item in items), 4)

    def test_fake_convergence_rejected(self) -> None:
        items = build_tree("BINARY_CONVERGENCE", "CONV", "How should A and B be investigated?", self.nodes, ["GRAM-A"], ["GAP-A"])
        next(item for item in items if item["branchStatus"] == "CONVERGENCE")["convergenceSourceItemIds"] = []
        with self.assertRaisesRegex(ValueError, "BINARY_CONVERGENCE_TOPOLOGY"):
            validate_tree("BINARY_CONVERGENCE", items)

    def test_shared_negative_topology_fixtures(self) -> None:
        path = ENGINE / "fixtures/tree-strategy-negative-v2.json"
        package = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(package["cases"]), 12)
        for case in package["cases"]:
            with self.subTest(case=case["caseId"]):
                with self.assertRaisesRegex(ValueError, case["expectedError"]):
                    validate_tree(case["strategy"], case["treeItems"])

    def test_reflexive_return_is_navigation_only(self) -> None:
        items = build_tree("REFLEXIVE_RETURN", "RETURN", "How should A be investigated?", self.nodes[:1], ["GRAM-A"], ["GAP-A"])
        root = next(item for item in items if item["parentItemId"] is None)
        return_item = next(item for item in items if item["branchStatus"] == "RETURN" and item["navigationTargetItemId"] is not None)
        self.assertEqual(return_item["navigationTargetItemId"], root["itemId"])
        self.assertNotEqual(return_item["parentItemId"], root["itemId"])

    def test_v1_v2_semantic_preservation(self) -> None:
        v1_dir = REPO / "docs/research/trace-v49-exploration-inquiry-flow-round1/12_RESEARCH_INSTANCES"
        for path in sorted(v1_dir.glob("INQUIRY-INSTANCE-*.json")):
            v1 = json.loads(path.read_text(encoding="utf-8"))
            v2 = compile_instance_v2(v1)
            validate_instance_v2(v2, v1)
            self.assertFalse(v2["historicalClaim"])
            self.assertFalse(v2["semanticRelation"])
            self.assertFalse(v2["publicExportable"])
            for binding_key in ("evidenceRefs", "gapRefs"):
                parent_bindings = {reference for item in v1["treeItems"] for reference in item.get(binding_key, [])}
                child_bindings = {reference for item in v2["treeItems"] for reference in item.get(binding_key, [])}
                self.assertEqual(parent_bindings, child_bindings)

    def test_semantic_mutation_rejected(self) -> None:
        path = REPO / "docs/research/trace-v49-exploration-inquiry-flow-round1/12_RESEARCH_INSTANCES/INQUIRY-INSTANCE-001.json"
        v1 = json.loads(path.read_text(encoding="utf-8"))
        v2 = compile_instance_v2(v1)
        changed = copy.deepcopy(v2)
        changed["rootInquiry"] = "How did this become a historical claim?"
        with self.assertRaisesRegex(ValueError, "V1_V2_SEMANTIC_PRESERVATION_FAILURE"):
            validate_instance_v2(changed, v1)

    def test_strict_json_schema_contracts(self) -> None:
        instance_schema = json.loads((REPO / "schemas/trace/exploration/research-inquiry-instance-v2.schema.json").read_text(encoding="utf-8"))
        tree_schema = json.loads((REPO / "schemas/trace/exploration/inquiry-tree-v2.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(instance_schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(instance_schema["additionalProperties"])
        self.assertFalse(tree_schema["additionalProperties"])
        self.assertFalse(tree_schema["$defs"]["treeItem"]["additionalProperties"])
        instance_fields = set(instance_schema["properties"])
        self.assertEqual(instance_fields, set(instance_schema["required"]))
        tree_required = set(tree_schema["$defs"]["treeItem"]["required"])
        tree_allowed = set(tree_schema["$defs"]["treeItem"]["properties"])
        self.assertEqual(tree_allowed - tree_required, {"candidateSenseId"})
        for path in sorted((REPO / "docs/research/trace-v49-exploration-composition-review-round1/12_RESEARCH_INSTANCES_V2").glob("*.json")):
            instance = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(set(instance), instance_fields)
            for item in instance["treeItems"]:
                self.assertLessEqual(set(item), tree_allowed)
                self.assertLessEqual(tree_required, set(item))


if __name__ == "__main__":
    unittest.main(verbosity=2)
