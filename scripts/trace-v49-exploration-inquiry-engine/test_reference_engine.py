#!/usr/bin/env python3
"""Round 12 standard-library reference-engine and strict-parser tests."""

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

from canonical import canonical_json, semantic_hash, without_hash  # noqa: E402
from coverage import compute_evidence_coverage  # noqa: E402
from flow_planner import plan_primary_inquiry_flow  # noqa: E402
from freeze import build_candidate_freeze  # noqa: E402
from instance_compiler import compile_research_inquiry_instance, verify_research_inquiry_instance  # noqa: E402
from seed_registry import build_seed_registry  # noqa: E402
from strict_parse import (  # noqa: E402
    StrictValidationError,
    detect_structural_contamination,
    validate_candidate_freeze,
    validate_inquiry_seed,
    validate_inquiry_tree,
    validate_research_inquiry_instance,
)
from tree_engine import expand_inquiry_tree, validate_tree_limits  # noqa: E402


class ReferenceEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.freeze = build_candidate_freeze(REPO)
        cls.coverage = compute_evidence_coverage(REPO, cls.freeze)
        cls.seeds = build_seed_registry(cls.freeze, cls.coverage["pairRows"])
        cls.trees = [expand_inquiry_tree(seed, cls.freeze, plan_primary_inquiry_flow(seed)) for seed in cls.seeds]
        cls.instances = [compile_research_inquiry_instance(seed, cls.freeze, index) for index, seed in enumerate(cls.seeds, start=1)]

    def expect_code(self, code: str, function, *args) -> None:
        with self.assertRaises(StrictValidationError) as captured:
            function(*args)
        self.assertEqual(captured.exception.code, code)

    def test_freeze_exact_counts_and_replay(self) -> None:
        self.assertEqual(len(self.freeze["candidates"]), 16)
        self.assertEqual(sum(item["researchStatus"] == "BOUNDED_NODE_ROLE_CANDIDATE" for item in self.freeze["candidates"]), 8)
        self.assertEqual(sum(item["researchStatus"] == "DEFERRED_NODE_ROLE_CANDIDATE" for item in self.freeze["candidates"]), 8)
        self.assertEqual(self.freeze, build_candidate_freeze(REPO))
        self.assertEqual(self.freeze["canonicalHash"], semantic_hash(without_hash(self.freeze)))

    def test_freeze_mutations_fail_or_change_hash(self) -> None:
        for mutate in (
            lambda value: value["candidates"][0].update(label="mediation-mutated"),
            lambda value: value["candidates"][0].update(senseId="SENSE-MUTATED"),
            lambda value: value["candidates"][0].update(researchStatus="BOUNDED_NODE_ROLE_CANDIDATE"),
            lambda value: value["candidates"][0]["grammarAttestationIds"].append("GRAM-ATT-MUTATED"),
            lambda value: value["candidates"][0]["lexicalAttestationIds"].pop(),
            lambda value: value["candidates"][0]["sourceIds"].pop(),
        ):
            changed = copy.deepcopy(self.freeze); mutate(changed)
            self.assertNotEqual(semantic_hash(without_hash(changed)), self.freeze["canonicalHash"])
            with self.assertRaises(StrictValidationError): validate_candidate_freeze(changed)

    def test_exact_evidence_coverage(self) -> None:
        summary = self.coverage["summary"]
        expected = {
            "totalResearchSourceCount": 78, "totalResearchAttestationCount": 85,
            "frozenCandidateDirectSourceCount": 57, "frozenCandidateDirectAttestationCount": 62,
            "boundedCandidateDirectSourceCount": 31, "boundedCandidateDirectAttestationCount": 35,
            "deferredCandidateDirectSourceCount": 27, "deferredCandidateDirectAttestationCount": 27,
            "pairQuestionCount": 3, "clusterHandoffCount": 2, "observedChainCount": 2, "gapCount": 6,
        }
        for key, value in expected.items(): self.assertEqual(summary[key], value, key)
        self.assertEqual(len(self.coverage["nodeRows"]), 16)
        self.assertEqual(len(self.coverage["pairRows"]), 3)

    def test_five_seed_flow_tree_and_instance_pipeline(self) -> None:
        self.assertEqual(len(self.seeds), 5)
        self.assertEqual(len({sense for seed in self.seeds for sense in seed["candidateSenseIds"]}), 8)
        self.assertEqual([seed["canonicalTreeStrategy"] for seed in self.seeds], ["BINARY_CONVERGENCE", "QUALIFIED_PATH", "BINARY_FORK", "BINARY_FORK", "REFLEXIVE_RETURN"])
        for seed, tree, instance in zip(self.seeds, self.trees, self.instances):
            validate_inquiry_seed(seed, self.freeze); validate_inquiry_tree(tree); validate_tree_limits(tree)
            self.assertEqual(tree["primaryInquiryFlow"]["origin"], "RESEARCH_INQUIRY")
            self.assertFalse(tree["primaryInquiryFlow"]["historicalClaim"])
            self.assertTrue(verify_research_inquiry_instance(instance, self.freeze, seed))
            self.assertTrue(instance["rootInquiry"].endswith("?"))
            self.assertFalse(instance["historicalClaim"]); self.assertFalse(instance["semanticRelation"])
            self.assertLessEqual(len(instance["semanticNodeRefs"]), 2)
            self.assertLessEqual(len(instance["treeItems"]), 7)
        self.assertEqual(sum(len(item["semanticNodeRefs"]) == 2 for item in self.instances), 3)
        self.assertEqual(sum(len(item["semanticNodeRefs"]) == 1 for item in self.instances), 2)

    def test_determinism_and_schema_aware_ordering(self) -> None:
        replay = [compile_research_inquiry_instance(seed, self.freeze, index) for index, seed in enumerate(self.seeds, start=1)]
        self.assertEqual(self.instances, replay)
        reordered = copy.deepcopy(self.freeze); reordered["candidates"].reverse()
        self.assertEqual(semantic_hash(without_hash(reordered)), self.freeze["canonicalHash"])
        self.assertNotEqual(canonical_json({"treeItems": [{"itemId": "A"}, {"itemId": "B"}]}), canonical_json({"treeItems": [{"itemId": "B"}, {"itemId": "A"}]}))
        with self.assertRaises(ValueError): canonical_json({"undeclaredArray": ["B", "A"]})
        with self.assertRaises(ValueError): canonical_json({"score": 0.5})

    def test_strict_unknown_duplicate_dangling_and_limits(self) -> None:
        seed = copy.deepcopy(self.seeds[0]); seed["unknown"] = True
        self.expect_code("UNKNOWN_FIELD", validate_inquiry_seed, seed, self.freeze)
        seed = copy.deepcopy(self.seeds[0]); seed["candidateSenseIds"] = [seed["candidateSenseIds"][0]] * 2
        self.expect_code("DUPLICATE_ID", validate_inquiry_seed, seed, self.freeze)
        tree = copy.deepcopy(self.trees[0]); tree["treeItems"][1]["parentItemId"] = "MISSING"
        self.expect_code("DANGLING_REFERENCE", validate_inquiry_tree, tree)
        tree = copy.deepcopy(self.trees[0]); tree["treeItems"][1]["depth"] = 5
        self.expect_code("TREE_LIMIT", validate_inquiry_tree, tree)
        instance = copy.deepcopy(self.instances[0]); instance["semanticNodeRefs"][1]["senseId"] = instance["semanticNodeRefs"][0]["senseId"]
        self.expect_code("DUPLICATE_SEMANTIC_ID", validate_research_inquiry_instance, instance, self.freeze, self.seeds[0])

    def test_structural_contamination_without_declaration(self) -> None:
        cases = [
            ({"archiveObjectId": "x"}, "ARCHIVE_OBJECT_CONTAMINATION"),
            ({"contextDTO": {"termId": "x"}}, "CONTEXT_CONTAMINATION"),
            ({"spacetimeDTO": {"periodId": "x"}}, "SPACETIME_CONTAMINATION"),
            ({"modelId": "external"}, "EXTERNAL_MODEL_CONTAMINATION"),
            ({"vectorReference": "x"}, "VECTOR_REFERENCE_CONTAMINATION"),
        ]
        for value, code in cases: self.assertIn(code, detect_structural_contamination(value))
        contaminated = copy.deepcopy(self.instances[0]); contaminated["semanticNodeRefs"][0]["recordUrl"] = "/record"
        self.expect_code("ARCHIVE_OBJECT_CONTAMINATION", validate_research_inquiry_instance, contaminated, self.freeze, self.seeds[0])

    def test_origin_carrier_question_and_claim_rejection(self) -> None:
        origin = copy.deepcopy(self.instances[0]); origin["primaryInquiryFlow"]["origin"] = "USER_COMPOSED"
        self.expect_code("ORIGIN_POLICY_VIOLATION", validate_research_inquiry_instance, origin, self.freeze, self.seeds[0])
        carrier = copy.deepcopy(self.instances[0]); carrier["primaryInquiryFlow"]["semanticRelation"] = True
        self.expect_code("CARRIER_SEPARATION", validate_research_inquiry_instance, carrier, self.freeze, self.seeds[0])
        question = copy.deepcopy(self.instances[0]); question["rootInquiry"] = "This is not a question."
        self.expect_code("QUESTION_FORM_REQUIRED", validate_research_inquiry_instance, question, self.freeze, self.seeds[0])
        claim = copy.deepcopy(self.instances[0]); claim["evidenceSummary"] = "Professionalization caused institutionalization."
        self.expect_code("HISTORICAL_CLAIM_REJECTED", validate_research_inquiry_instance, claim, self.freeze, self.seeds[0])

    def test_shared_conformance_fixtures(self) -> None:
        fixture_file = ENGINE / "fixtures/cross-runtime-fixtures.json"
        fixtures = json.loads(fixture_file.read_text(encoding="utf-8"))["fixtures"]
        self.assertGreaterEqual(len(fixtures), 10)
        mismatches = []
        for fixture in fixtures:
            accepted, code = True, ""
            seed = next((item for item in self.seeds if item["seedId"] == fixture["value"].get("seedId")), self.seeds[0]) if isinstance(fixture["value"], dict) else self.seeds[0]
            try:
                if fixture["kind"] == "FREEZE": validate_candidate_freeze(fixture["value"])
                elif fixture["kind"] == "SEED": validate_inquiry_seed(fixture["value"], self.freeze)
                elif fixture["kind"] == "TREE": validate_inquiry_tree(fixture["value"])
                elif fixture["kind"] == "INSTANCE": validate_research_inquiry_instance(fixture["value"], self.freeze, seed)
            except StrictValidationError as error: accepted, code = False, error.code
            if accepted != fixture["expectedAccepted"] or code != fixture["expectedFailureCode"]: mismatches.append(fixture["fixtureId"])
        self.assertEqual(mismatches, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
