#!/usr/bin/env python3
"""Independently reconstruct and verify the Round 16B local candidate census."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
PARENT_SHA = "af056edadb43c1eb9e219217c42fd58b74ac5efd"
SELECTOR_VERSION = "trace-round16b-local-candidate-selector-v1"
RAW_REL = Path("docs/audits/v49-exploration-higher-order-association-closure-round16b/raw")
VOCAB = Path("docs/audits/v49-exploration-full-space-closure-round1/raw/vocabulary-census-v2.json")
R9_CANDIDATES = Path("docs/research/trace-v49-design-history-relation-vocabulary-round1/04_RAW_CANDIDATE_TERM_REGISTRY.tsv")
R9_ATTEST = Path("docs/research/trace-v49-design-history-relation-vocabulary-round1/05_TERM_ATTESTATION_REGISTRY.tsv")
R9_GLOSSES = Path("docs/research/trace-v49-design-history-relation-vocabulary-round1/07_SEMANTIC_GLOSS_REGISTRY.tsv")
R10_ROLES = Path("docs/research/trace-v49-design-history-relation-grammar-round1/06_ARGUMENT_ROLE_REGISTRY.tsv")
R10_ATTEST = Path("docs/research/trace-v49-design-history-relation-grammar-round1/07_GRAMMAR_ATTESTATION_REGISTRY.tsv")
R10_CLUSTERS = Path("docs/research/trace-v49-design-history-relation-grammar-round1/14_CLUSTER_EVIDENCE_HANDOFF.tsv")
R10_CHAINS = Path("docs/research/trace-v49-design-history-relation-grammar-round1/15_OBSERVED_RELATION_CHAIN_REGISTRY.tsv")
R13_EVIDENCE = Path("docs/research/trace-v49-exploration-composition-review-round1/04_COMPOSITION_EVIDENCE_REGISTRY.tsv")
R13_GAPS = Path("docs/research/trace-v49-exploration-composition-review-round1/07_VOCABULARY_GAP_DECISIONS.tsv")
R14_ASSESSMENTS = Path("scripts/trace-v49-exploration-association-calibration/fixtures/association-assessments-v1.json")
R14_PROVENANCE = Path("docs/audits/v49-exploration-association-calibration-round1/raw/evidence-provenance.tsv")
R14_NARY = Path("scripts/trace-v49-exploration-association-calibration/fixtures/nary-local-coherence-v1.json")
R15_FIXTURES = Path("scripts/trace-v49-exploration-composition-engine/fixtures/composition-fixtures-v1.json")
R15_DECISIONS = Path("docs/audits/v49-exploration-composition-engine-round1/raw/composition-decision-audit.json")
R15_RESULTS = Path("docs/audits/v49-exploration-composition-engine-round1/raw/composition-fixture-results.tsv")
R16_COMPOSITIONS = Path("scripts/trace-v49-exploration-real-database/real-composition-registry-v1.json")
R16_SOURCES = Path("scripts/trace-v49-exploration-real-database/scholarly-source-additions-v1.tsv")
R16_READ_MODEL = Path("frontend/generated/trace-exploration-v1/read-model.json")
R16A_PAIRS = Path("docs/audits/v49-exploration-full-space-closure-round1/raw/association-census-v2.tsv")
R16A_GRAPH = Path("docs/audits/v49-exploration-full-space-closure-round1/raw/validated-association-graph-v2.json")
R16A_REGISTRY = Path("docs/audits/v49-exploration-full-space-closure-round1/raw/canonical-composition-registry-v2.json")
R16A_ENUMERATION = Path("docs/audits/v49-exploration-full-space-closure-round1/raw/composition-enumeration-v2.tsv")
R16A_REJECTIONS = Path("docs/audits/v49-exploration-full-space-closure-round1/raw/composition-rejection-ledger-v2.tsv")
R16A_READ_MODEL = Path("frontend/generated/trace-exploration-v2/production-read-model.json")
R16A_STATES = Path("docs/audits/v49-exploration-full-space-closure-round1/raw/state-census-v2.tsv")
R16A_TRANSITIONS = Path("docs/audits/v49-exploration-full-space-closure-round1/raw/transition-census-v2.tsv")
R16A_WORKFLOWS = Path("docs/audits/v49-exploration-full-space-closure-round1/raw/workflow-census-v2.tsv")
R16A_EXPORTS = Path("docs/audits/v49-exploration-full-space-closure-round1/raw/export-census-v2.tsv")
METHOD_SURFACES = Path("docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/evidence-surface-inventory.tsv")

PRIOR_ARTIFACT_NAMESPACES = (
    ("ROUND15_AUDIT", "docs/audits/v49-exploration-composition-engine-round1"),
    ("ROUND15_RESEARCH", "docs/research/trace-v49-exploration-composition-engine-round1"),
    ("ROUND15_GENERATOR", "scripts/trace-v49-exploration-composition-engine"),
    ("ROUND16_AUDIT", "docs/audits/v49-exploration-real-database-round1"),
    ("ROUND16_RESEARCH", "docs/research/trace-v49-exploration-real-database-round1"),
    ("ROUND16_GENERATOR", "scripts/trace-v49-exploration-real-database"),
    ("ROUND16A_AUDIT", "docs/audits/v49-exploration-full-space-closure-round1"),
    ("ROUND16A_RESEARCH", "docs/research/trace-v49-exploration-full-space-closure-round1"),
    ("ROUND16A_GENERATOR", "scripts/trace_round16a"),
    ("ROUND16_READ_MODEL", "frontend/generated/trace-exploration-v1"),
    ("ROUND16A_READ_MODEL", "frontend/generated/trace-exploration-v2"),
    ("ROUND16_RUNTIME", "frontend/src/features/trace-v49/exploration"),
    ("ROUND16A_RUNTIME", "frontend/src/features/trace-v49/exploration-v2"),
    ("ROUND16_API", "frontend/src/app/api/trace/v1/exploration"),
    ("ROUND16A_API", "frontend/src/app/api/trace/v2/exploration"),
    ("ROUND15_16_16A_SCHEMA", "schemas/trace/exploration"),
)

EXPECTED_PRIOR_SHARDS = {
    "prior-object-reconciliation-universe-v1-core.tsv",
    "prior-object-reconciliation-universe-v1-exports.tsv",
    "prior-object-reconciliation-universe-v1-states.tsv",
    "prior-object-reconciliation-universe-v1-workflows.tsv",
}
EXPECTED_OUTPUT_NAMES = {
    "candidate-trigger-occurrence-ledger-v1.tsv",
    "concept-sense-crosswalk-v1.tsv",
    "isolated-active-term-audit-ledger-v1.tsv",
    "local-candidate-census-v1.json",
    "local-candidate-family-ledger-v1.tsv",
    "local-candidate-input-manifest-v1.tsv",
    "local-surface-disposition-ledger-v1.tsv",
    "open-participant-resolution-ledger-v1.tsv",
    "prior-artifact-file-manifest-v1.tsv",
    *EXPECTED_PRIOR_SHARDS,
    "prior-object-set-manifest-v1.tsv",
    "prior-production-descendant-manifest-v1.tsv",
}
EXPECTED_CLOSURE_KEYS = {
    "PAIR_ASSOCIATION_CLOSURE",
    "HIGHER_ORDER_ASSOCIATION_CLOSURE",
    "GLOBAL_COMPOSITION_COHERENCE_CLOSURE",
    "PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE",
    "COMPUTATIONAL_SPACE_CLOSURE",
    "FUNCTION3_CLOSURE",
}
EXPECTED_TRIGGER_ID_BY_CLASS = {
    "EXPLICIT_CLUSTER_NEAR_MISS": "TRG-007",
    "ROUND14_NARY_FIXTURE": "TRG-007",
    "ROUND15_COMPOSITION_FIXTURE": "TRG-004",
    "ROUND16_LEGACY_COMPOSITION": "TRG-004",
    "ROUND16A_CONNECTED_SUBGRAPH": "TRG-004",
    "ROUND16A_TOPOLOGY_COMPOSITION": "TRG-004",
    "ROUND16A_PRODUCTION_COMPOSITION": "TRG-004",
    "ROUND14_ACTIVE_PAIR_SHARED_LOCUS_BUNDLE": "TRG-003",
    "ROUND14_CONCEPT_ONLY_HIGHER_ORDER_LEAD": "TRG-002",
    "ROUND10_DIRECT_PASSAGE": "TRG-002",
    "ROUND13_DIRECT_POSITIVE_FIELD_PASSAGE": "TRG-002",
    "ROUND13_INCIDENTAL_CASE_LABEL_CONTROL": "TRG-002",
    "ROUND13_QUALIFICATION_CONTEXT_EXTENSION": "TRG-002",
    "ROUND14_QUALIFIED_SHARED_LOCUS_OVERLAP": "TRG-008",
    "ROUND14_ARCHIVE_EXACT_CONTEXT_DUPLICATE": "TRG-002",
    "ROUND16_VOCABULARY_ONLY_MULTI_TERM": "TRG-006",
    "ROUND9_SOURCE_LOCATOR_CONTEXT_COLLISION": "TRG-002",
}

EXPECTED_INPUT_SURFACES = {
    "R16B-LOCAL-SURF-R16A-VOCABULARY": (VOCAB, "json:candidates"),
    "R16B-LOCAL-SURF-R09-CANDIDATES": (R9_CANDIDATES, "tsv_rows"),
    "R16B-LOCAL-SURF-R09-ATTESTATIONS": (R9_ATTEST, "tsv_rows"),
    "R16B-LOCAL-SURF-R09-GLOSSES": (R9_GLOSSES, "tsv_rows"),
    "R16B-LOCAL-SURF-R10-ROLES": (R10_ROLES, "tsv_rows"),
    "R16B-LOCAL-SURF-R10-ATTESTATIONS": (R10_ATTEST, "tsv_rows"),
    "R16B-LOCAL-SURF-R10-CLUSTERS": (R10_CLUSTERS, "tsv_rows"),
    "R16B-LOCAL-SURF-R10-CHAINS": (R10_CHAINS, "tsv_rows"),
    "R16B-LOCAL-SURF-R13-EVIDENCE": (R13_EVIDENCE, "tsv_rows"),
    "R16B-LOCAL-SURF-R13-GAP-DECISIONS": (R13_GAPS, "tsv_rows"),
    "R16B-LOCAL-SURF-R14-ASSESSMENTS": (R14_ASSESSMENTS, "json:assessments"),
    "R16B-LOCAL-SURF-R14-PROVENANCE": (R14_PROVENANCE, "tsv_rows"),
    "R16B-LOCAL-SURF-R14-NARY": (R14_NARY, "json:fixtures"),
    "R16B-LOCAL-SURF-R15-FIXTURES": (R15_FIXTURES, "json:fixtures"),
    "R16B-LOCAL-SURF-R15-DECISIONS": (R15_DECISIONS, "json:images"),
    "R16B-LOCAL-SURF-R15-RESULTS": (R15_RESULTS, "tsv_rows"),
    "R16B-LOCAL-SURF-R16-COMPOSITIONS": (R16_COMPOSITIONS, "json:compositions"),
    "R16B-LOCAL-SURF-R16-SOURCES": (R16_SOURCES, "tsv_rows"),
    "R16B-LOCAL-SURF-R16-READ-MODEL": (R16_READ_MODEL, "json:file"),
    "R16B-LOCAL-SURF-R16A-PAIR-CENSUS": (R16A_PAIRS, "tsv_rows"),
    "R16B-LOCAL-SURF-R16A-GRAPH-NODES": (R16A_GRAPH, "json:nodes"),
    "R16B-LOCAL-SURF-R16A-GRAPH-EDGES": (R16A_GRAPH, "json:edges"),
    "R16B-LOCAL-SURF-R16A-SUBGRAPHS": (R16A_REGISTRY, "json:association_subgraphs"),
    "R16B-LOCAL-SURF-R16A-TOPOLOGIES": (R16A_REGISTRY, "json:topology_compositions"),
    "R16B-LOCAL-SURF-R16A-CATEGORIES": (R16A_REGISTRY, "json:category_entries"),
    "R16B-LOCAL-SURF-R16A-ADAPTERS": (R16A_REGISTRY, "json:round15_adapter_records"),
    "R16B-LOCAL-SURF-R16A-ENUMERATION": (R16A_ENUMERATION, "tsv_rows"),
    "R16B-LOCAL-SURF-R16A-REJECTIONS": (R16A_REJECTIONS, "tsv_rows"),
    "R16B-LOCAL-SURF-R16A-PRODUCTION": (R16A_READ_MODEL, "json:compositions"),
    "R16B-LOCAL-SURF-R16A-STATES": (R16A_STATES, "tsv_rows"),
    "R16B-LOCAL-SURF-R16A-TRANSITIONS": (R16A_TRANSITIONS, "tsv_rows"),
    "R16B-LOCAL-SURF-R16A-WORKFLOWS": (R16A_WORKFLOWS, "tsv_rows"),
    "R16B-LOCAL-SURF-R16A-EXPORTS": (R16A_EXPORTS, "tsv_rows"),
    "R16B-LOCAL-METHOD-SURFACE-INVENTORY": (METHOD_SURFACES, "tsv_rows"),
}

EXPECTED_TRIGGER_CLASSES = {
    "EXPLICIT_CLUSTER_NEAR_MISS": 2,
    "ROUND14_NARY_FIXTURE": 6,
    "ROUND15_COMPOSITION_FIXTURE": 24,
    "ROUND16_LEGACY_COMPOSITION": 4,
    "ROUND16A_CONNECTED_SUBGRAPH": 37,
    "ROUND16A_TOPOLOGY_COMPOSITION": 60,
    "ROUND16A_PRODUCTION_COMPOSITION": 186,
    "ROUND14_ACTIVE_PAIR_SHARED_LOCUS_BUNDLE": 10,
    "ROUND14_CONCEPT_ONLY_HIGHER_ORDER_LEAD": 1,
    "ROUND10_DIRECT_PASSAGE": 3,
    "ROUND13_DIRECT_POSITIVE_FIELD_PASSAGE": 6,
    "ROUND13_INCIDENTAL_CASE_LABEL_CONTROL": 1,
    "ROUND13_QUALIFICATION_CONTEXT_EXTENSION": 1,
    "ROUND14_QUALIFIED_SHARED_LOCUS_OVERLAP": 1,
    "ROUND14_ARCHIVE_EXACT_CONTEXT_DUPLICATE": 4,
    "ROUND16_VOCABULARY_ONLY_MULTI_TERM": 1,
    "ROUND9_SOURCE_LOCATOR_CONTEXT_COLLISION": 1,
}
EXPECTED_TRIGGER_IDS = {"TRG-002": 17, "TRG-003": 10, "TRG-004": 311, "TRG-006": 1, "TRG-007": 8, "TRG-008": 1}
EXPECTED_ARITY = {"3": 21, "4": 4, "5": 1, "6": 4, "8": 1}
EXPECTED_MANIFEST = {
    "ROUND15_FIXTURE": (25, "128f3302ee7ffddce826273cc97e4af4f88f8c4db680f08446235d1031424b1a"),
    "ROUND15_SEMANTIC_IMAGE": (25, "ae85da77efeac5356621da8bb77ca20a2ccd9afb41ea1a8a764acc494ea7093b"),
    "ROUND15_FIXTURE_RESULT": (25, "128f3302ee7ffddce826273cc97e4af4f88f8c4db680f08446235d1031424b1a"),
    "ROUND16_LEGACY_COMPOSITION": (11, "8715a3710e1bfe3c240132084b8b0fedbebb9d2c54e84eb25e37b156fb9091f0"),
    "ROUND16_VOCABULARY_REPRESENTATION": (26, "5558281f01a5b43aeeea8e2ef351448e06374f3d12529f689426ec427c9918ca"),
    "ROUND16_ASSOCIATION_REPRESENTATION": (21, "a877ae2220450dade055af0f3e1866d56e152019270b5430704fab1c90e617f7"),
    "ROUND16_CATEGORY_REPRESENTATION": (4, "1b91a31df1c85bce0107b13b98e6a92de7a77a5cfa44a3661fe486fff3a16238"),
    "ROUND16_SOURCE_INVENTORY_ENTRY": (10, "709263e6ca987c2d7dd588c6cf1911bffd2713db11949cb2a0eff4c065d783ee"),
    "ROUND16_FAILED_ASSOCIATION_AUDIT": (14, "c34048829f3c64cd937bc19c17544aa0f9c23c4da000722f4a5be8612e6139e9"),
    "ROUND16_STATE_HASH_INDEX": (52, "ac01d3148625238a149851f96502b8874b34627dc87874619128b60625fd2aa2"),
    "ROUND16_CAPABILITY_FIELD": (11, "c7c79046c8548c722babda636798c516a81ba96f9c3e5db98b04840f2c6b1769"),
    "ROUND16_DATABASE_AUTHORITY_FIELD": (14, "3359c3c6a6a596da6ff142e345dbee6e1ce6edf47b597ccf6875b2e735932826"),
    "ROUND16_EMBEDDED_SEMANTIC_IMAGE": (11, "f9355a30295c7199c293d14058c57c1b6fd73fdf37aadba9645277df66f6a45a"),
    "ROUND16_MAP": (4, "dd3bf21707194d0759d36c2ea2ba36b4d84164f89da0a3c403a4d15a3244f123"),
    "ROUND16_TREE": (26, "03c05b23305e7d58814868d3e9ab168b77148cf71b7ba6dff4fcdb88bd5643df"),
    "ROUND16_STATE": (52, "3a04f4f3ee66e8647a19964d5f89c3167e43872f73e6f111d920bc9978629108"),
    "ROUND16_TRANSITION": (816, "1cbe9951237b81f29af61aa0ccd928cfe0f8afcd97f0be4b87afb75df30dea92"),
    "ROUND16_WORKFLOW": (5, "8b1583da45bf9454a0078483f6f76dcf62929b57cc95031d5b74a0734a9a0ba6"),
    "ROUND16_EXPORT_MANIFEST_KEY": (104, "d22169f85385a6a7800e419a7d5be2c9314a0819e1023974c7b290db208c9fbb"),
    "ROUND16_EXPORT": (104, "36adb733b9bd76de8058dd3b66c936f774bd6dc5b214c1f3693e4aba4f992924"),
    "ROUND16A_VOCABULARY_CANDIDATE": (65, "cdc1f562bdc73b07d8173bc0edd4798a7e83ca8ce8ad650d0c75d891b3a1a89a"),
    "ROUND16A_PAIR_CENSUS": (465, "806d39f00794fa8762f9600732c829af7538335a53822abedc92725ef022f34d"),
    "ROUND16A_ACTIVE_PAIR_ASSOCIATION": (21, "fcf8bf2fb0f60bbf5993dd84e056bc35dddfd5af9c927c0f8886642346b53c75"),
    "ROUND16A_ASSOCIATION_SUBGRAPH": (58, "a20e2dbbe5f720a8ba26b4746e9fae49416ed1958e948b22e3dc5b3fa3ad6188"),
    "ROUND16A_LEGACY_RECONCILIATION": (11, "8715a3710e1bfe3c240132084b8b0fedbebb9d2c54e84eb25e37b156fb9091f0"),
    "ROUND16A_ROUND15_ADAPTER_RECORD": (58, "3a0f8e3c7186184dd454747c9b590d8b44a5c5618a8ca0f1ed2ea91f6aa728e1"),
    "ROUND16A_TOPOLOGY_COMPOSITION": (81, "a0eb64e0f60fdaf280f1221a8036c83b263fd6e98399badfb0d372193f0abed2"),
    "ROUND16A_CATEGORY_ENTRY": (81, "df752a327984d8057b3e2d0e42ad478c5e2e0d4292e56c4316e333f0f4563c3a"),
    "ROUND16A_SEED_VARIANT": (228, "0d062da1382d2a2c041febe7fd458e38cc056d63b31cd2d33b555bd39990a886"),
    "ROUND16A_PRODUCTION_COMPOSITION": (228, "d6477415cdc379637d396b8c271dc7ca59a6b1e4fbd86bc6e4974f0b12c05656"),
    "ROUND16A_VOCABULARY_REPRESENTATION": (31, "012b9c9f3b1eeecaa20dcdd21567cea830404e0c49cdd4b061e97baf68c50eb5"),
    "ROUND16A_ASSOCIATION_REPRESENTATION": (21, "fcf8bf2fb0f60bbf5993dd84e056bc35dddfd5af9c927c0f8886642346b53c75"),
    "ROUND16A_CATEGORY_REPRESENTATION": (81, "df752a327984d8057b3e2d0e42ad478c5e2e0d4292e56c4316e333f0f4563c3a"),
    "ROUND16A_STATE_HASH_INDEX": (5760, "bfb3a623cd96dc27878f99a5ec69ed77795a40c53a7d45ad9aae6ec1ea24ae33"),
    "ROUND16A_TRANSITION_DESCRIPTOR_FIELD": (3, "b2228e60f3f9dc7e79485065dfd5989b17df2d035a34eed28ea7dc323131d35a"),
    "ROUND16A_CAPABILITY_FIELD": (16, "1fbf6611df4d79edf0fc4e8829c9d61a7dbf25848491b5de1d7519b3f1550b3d"),
    "ROUND16A_DATABASE_AUTHORITY_FIELD": (6, "1d87dacd29279d2e421084fd349bb6b63f588ff398a0c45f8ec681b89a35697c"),
    "ROUND16A_STATE": (5760, "68027be5be45c1fbc42adae105b64c9f2ad8da4b99e98608747e351c3d0fc062"),
    "ROUND16A_TRANSITION": (749944, "27328cf72733c5454c41c8b396f19a5934a82068a45e4de42de396e166a06fe9"),
    "ROUND16A_WORKFLOW": (5760, "93bb188482e9028dccebd05b7e601d00edaa179862f2fb359c19944841a7a863"),
    "ROUND16A_EXPORT": (11520, "d575dc7f4454b142561f127556b5ff3566cd7bac4d3663719b6dc6aff3215788"),
    "ROUND16A_TOPOLOGY_ENUMERATION_RESULT": (348, "549eb1d8c80ad55d64f642f6b24d79310b6a89b7be49a7af9bba0f2afebca366"),
    "ROUND16A_TOPOLOGY_REJECTION": (277, "711d10b04681849d6297a7120857854fb2b58894dfff59157d97f15fd43b3bd4"),
}
EXPECTED_MANIFEST_METADATA = {
    "ROUND15_FIXTURE": (R15_FIXTURES, "json:fixtures", True),
    "ROUND15_SEMANTIC_IMAGE": (R15_DECISIONS, "json:images", True),
    "ROUND15_FIXTURE_RESULT": (R15_RESULTS, "tsv_rows", True),
    "ROUND16_LEGACY_COMPOSITION": (R16_COMPOSITIONS, "json:compositions", True),
    "ROUND16_VOCABULARY_REPRESENTATION": (R16_READ_MODEL, "json:vocabulary", True),
    "ROUND16_ASSOCIATION_REPRESENTATION": (R16_READ_MODEL, "json:associations", True),
    "ROUND16_CATEGORY_REPRESENTATION": (R16_READ_MODEL, "json:categories", True),
    "ROUND16_SOURCE_INVENTORY_ENTRY": (R16_READ_MODEL, "json:source_inventory", True),
    "ROUND16_FAILED_ASSOCIATION_AUDIT": (R16_READ_MODEL, "json:failed_associations_audit_only", True),
    "ROUND16_STATE_HASH_INDEX": (R16_READ_MODEL, "json:states_by_hash", True),
    "ROUND16_CAPABILITY_FIELD": (R16_READ_MODEL, "json:capabilities", True),
    "ROUND16_DATABASE_AUTHORITY_FIELD": (R16_READ_MODEL, "json:database", True),
    "ROUND16_EMBEDDED_SEMANTIC_IMAGE": (R16_READ_MODEL, "json:compositions", True),
    "ROUND16_MAP": (R16_READ_MODEL, "json:maps", True),
    "ROUND16_TREE": (R16_READ_MODEL, "json:trees", True),
    "ROUND16_STATE": (R16_READ_MODEL, "json:states", True),
    "ROUND16_TRANSITION": (R16_READ_MODEL, "json:transitions", True),
    "ROUND16_WORKFLOW": (R16_READ_MODEL, "json:workflows", True),
    "ROUND16_EXPORT_MANIFEST_KEY": (R16_READ_MODEL, "json:export_manifests", False),
    "ROUND16_EXPORT": (R16_READ_MODEL, "json:export_manifests", True),
    "ROUND16A_VOCABULARY_CANDIDATE": (VOCAB, "json:candidates", True),
    "ROUND16A_PAIR_CENSUS": (R16A_PAIRS, "tsv_rows", True),
    "ROUND16A_ACTIVE_PAIR_ASSOCIATION": (R16A_GRAPH, "json:edges", True),
    "ROUND16A_ASSOCIATION_SUBGRAPH": (R16A_REGISTRY, "json:association_subgraphs", True),
    "ROUND16A_LEGACY_RECONCILIATION": (R16A_REGISTRY, "json:round16_legacy_reconciliation", True),
    "ROUND16A_ROUND15_ADAPTER_RECORD": (R16A_REGISTRY, "json:round15_adapter_records", True),
    "ROUND16A_TOPOLOGY_COMPOSITION": (R16A_REGISTRY, "json:topology_compositions", True),
    "ROUND16A_CATEGORY_ENTRY": (R16A_REGISTRY, "json:category_entries", True),
    "ROUND16A_SEED_VARIANT": (R16A_REGISTRY, "json:topology_compositions", True),
    "ROUND16A_PRODUCTION_COMPOSITION": (R16A_READ_MODEL, "json:compositions", True),
    "ROUND16A_VOCABULARY_REPRESENTATION": (R16A_READ_MODEL, "json:vocabulary", True),
    "ROUND16A_ASSOCIATION_REPRESENTATION": (R16A_READ_MODEL, "json:associations", True),
    "ROUND16A_CATEGORY_REPRESENTATION": (R16A_READ_MODEL, "json:categories", True),
    "ROUND16A_STATE_HASH_INDEX": (R16A_READ_MODEL, "json:states_by_hash", True),
    "ROUND16A_TRANSITION_DESCRIPTOR_FIELD": (R16A_READ_MODEL, "json:transitions", True),
    "ROUND16A_CAPABILITY_FIELD": (R16A_READ_MODEL, "json:capabilities", True),
    "ROUND16A_DATABASE_AUTHORITY_FIELD": (R16A_READ_MODEL, "json:database", True),
    "ROUND16A_STATE": (R16A_STATES, "tsv_rows", True),
    "ROUND16A_TRANSITION": (R16A_TRANSITIONS, "tsv_rows:transition_id", False),
    "ROUND16A_WORKFLOW": (R16A_WORKFLOWS, "tsv_rows", True),
    "ROUND16A_EXPORT": (R16A_EXPORTS, "tsv_rows", True),
    "ROUND16A_TOPOLOGY_ENUMERATION_RESULT": (R16A_ENUMERATION, "tsv_rows", True),
    "ROUND16A_TOPOLOGY_REJECTION": (R16A_REJECTIONS, "tsv_rows", True),
}

EXPECTED_OPEN_BLOCKERS = [
    "Candidate scopes and cases may split participant-set review families into multiple semantic association candidates.",
    "Twenty-one method-inventory surfaces are hash-accounted but remain explicitly deferred from executable selector review, so local trigger completeness is open.",
    "Local evidence, rights, negative evidence, and source-bundle synthesis have not yet received final dispositions.",
    "Database discovery and adaptive external scholarly searches have not yet been completed.",
    "Ten n-ary role templates lack closed governed participant sets.",
    "Five pair-isolated active terms lack final product-accessibility dispositions.",
    "Every prior composition and downstream v2 object remains pending global-coherence and v3 regeneration review.",
]


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_id(prefix: str, value: Any) -> str:
    return f"{prefix}:{sha256_text(canonical_json(value))}"


def split_semicolon(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, dialect="excel-tab"))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def selector_record_count(path: Path, selector: str) -> int:
    if selector == "tsv_rows":
        with path.open(encoding="utf-8", newline="") as handle:
            return sum(1 for _ in csv.DictReader(handle, dialect="excel-tab"))
    if selector == "jsonl_rows":
        with path.open(encoding="utf-8") as handle:
            return sum(bool(line.strip()) for line in handle)
    if selector == "file":
        return 1
    payload = read_json(path)
    if selector == "json:file":
        return 1
    if not selector.startswith("json:"):
        raise ValueError(f"unsupported selector: {selector}")
    return len(payload[selector.split(":", 1)[1]])


def id_hash(values: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for value in sorted(values):
        digest.update(value.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def sense_id(candidate_id: str) -> str:
    return f"R16B-SENSE:{sha256_text('round16a-vocabulary-candidate:' + candidate_id)}"


def family_normal_form(labels: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(set(labels), key=str.casefold))


def family_digest(families: Iterable[Iterable[str]]) -> str:
    values = [list(family_normal_form(value)) for value in families]
    values.sort(key=lambda value: (len(value), [item.casefold() for item in value]))
    return sha256_text(canonical_json(values))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    raw = repo / RAW_REL
    failures: list[str] = []
    checks: dict[str, Any] = {}

    def require(code: str, condition: bool, detail: Any = None) -> None:
        checks[code] = {"pass": bool(condition), "detail": detail}
        if not condition:
            failures.append(code)

    crosswalk = read_tsv(raw / "concept-sense-crosswalk-v1.tsv")
    occurrences = read_tsv(raw / "candidate-trigger-occurrence-ledger-v1.tsv")
    families = read_tsv(raw / "local-candidate-family-ledger-v1.tsv")
    open_roles = read_tsv(raw / "open-participant-resolution-ledger-v1.tsv")
    isolated = read_tsv(raw / "isolated-active-term-audit-ledger-v1.tsv")
    set_manifest = read_tsv(raw / "prior-object-set-manifest-v1.tsv")
    descendants = read_tsv(raw / "prior-production-descendant-manifest-v1.tsv")
    input_manifest = read_tsv(raw / "local-candidate-input-manifest-v1.tsv")
    surface_dispositions = read_tsv(raw / "local-surface-disposition-ledger-v1.tsv")
    prior_artifact_files = read_tsv(raw / "prior-artifact-file-manifest-v1.tsv")
    prior_files = sorted(raw.glob("prior-object-reconciliation-universe-v1-*.tsv"))
    prior_rows = [row for path in prior_files for row in read_tsv(path)]
    census = read_json(raw / "local-candidate-census-v1.json")
    receipt = read_json(raw / "local-candidate-build-receipt.json")

    vocabulary = read_json(repo / VOCAB)["candidates"]
    vocab_by_label = {row["canonical_label"]: row for row in vocabulary}
    vocab_by_id = {row["vocabulary_id"]: row for row in vocabulary if row["vocabulary_id"]}
    crosswalk_by_label = {row["canonical_label"]: row for row in crosswalk}
    crosswalk_by_sense = {row["participant_sense_id"]: row for row in crosswalk}
    family_by_id = {row["candidate_id"]: row for row in families}

    require("SOURCE_AND_PARENT_EXACT", census["source_sha"] == SOURCE_SHA and census["source_tree"] == SOURCE_TREE and census["parent_checkpoint_sha"] == PARENT_SHA)
    require("RECEIPT_SOURCE_AND_PARENT_EXACT", receipt["source_sha"] == SOURCE_SHA and receipt["source_tree"] == SOURCE_TREE and receipt["parent_checkpoint_sha"] == PARENT_SHA)
    require("SELECTOR_VERSION_EXACT", census["selector_version"] == SELECTOR_VERSION and receipt["selector_version"] == SELECTOR_VERSION)

    # Crosswalk reconstruction.
    expected_senses = {row["canonical_label"]: sense_id(row["vocabulary_candidate_id"]) for row in vocabulary}
    require("CROSSWALK_COUNT_65", len(crosswalk) == len(vocabulary) == 65, len(crosswalk))
    require("CROSSWALK_LABEL_SET_EXACT", set(crosswalk_by_label) == set(expected_senses))
    require("CROSSWALK_SENSE_ALGORITHM_EXACT", all(crosswalk_by_label[label]["participant_sense_id"] == value for label, value in expected_senses.items()))
    require("CROSSWALK_IDS_UNIQUE", len(crosswalk_by_sense) == 65 and len({row["vocabulary_candidate_id"] for row in crosswalk}) == 65)
    disposition_counts = Counter(row["disposition"] for row in crosswalk)
    require("CROSSWALK_DISPOSITION_COUNTS", disposition_counts == {"ACTIVE": 31, "RESEARCH_ONLY": 21, "REJECTED": 12, "MERGED_SUPERSEDED": 1}, disposition_counts)
    require("ACTIVE_TRV_RESOLUTION", all(row["vocabulary_id"].startswith("TRV:") for row in crosswalk if row["disposition"] == "ACTIVE"))
    require("NONACTIVE_HAS_NO_TRV", all(not row["vocabulary_id"] for row in crosswalk if row["disposition"] != "ACTIVE"))
    adaptation_sense = crosswalk_by_label["adaptation"]["participant_sense_id"]
    cultural_adaptation = crosswalk_by_label["cultural adaptation"]
    require("MERGED_ALIAS_RESOLVES_EXACTLY", cultural_adaptation["canonical_resolution_sense_id"] == adaptation_sense and cultural_adaptation["crosswalk_status"] == "RESOLVED_MERGED_ALIAS")
    require("NORMALIZED_LABELS_UNIQUE", len({row["normalized_label"] for row in crosswalk}) == 65)
    r9_candidates = read_tsv(repo / R9_CANDIDATES)
    require("ROUND9_CANDIDATE_CROSSWALK_COMPLETE", all(row["candidate_id"] in json.loads(crosswalk_by_label[row["candidate_label"]]["source_concept_ids_json"]) for row in r9_candidates))
    r9_candidate_by_label = {row["candidate_label"]: row for row in r9_candidates}
    crosswalk_field_failures: list[str] = []
    for source in vocabulary:
        row = crosswalk_by_label[source["canonical_label"]]
        resolution_label = source["merge_target_label"] or source["canonical_label"]
        expected_status = {
            "MERGED_SUPERSEDED": "RESOLVED_MERGED_ALIAS",
            "REJECTED": "RESOLVED_CONTROL_ONLY",
        }.get(source["disposition"], "RESOLVED_CANONICAL")
        expected_material = {
            "participant_sense_id": expected_senses[source["canonical_label"]],
            "vocabulary_candidate_id": source["vocabulary_candidate_id"],
            "vocabulary_id": source["vocabulary_id"],
            "canonical_label": source["canonical_label"],
            "normalized_label": source["normalized_label"],
            "canonical_resolution_sense_id": expected_senses[resolution_label],
            "disposition": source["disposition"],
            "status": source["status"],
        }
        exact_fields = {
            **expected_material,
            "bounded_sense": source["bounded_sense"],
            "scope_note": source["scope_note"],
            "merge_target_vocabulary_id": source["merge_target_vocabulary_id"],
            "source_system": "ROUND16A_VOCABULARY_CENSUS_V2",
            "authority_path": str(VOCAB),
            "authority_record_id": source["vocabulary_candidate_id"],
            "source_sha": SOURCE_SHA,
            "crosswalk_status": expected_status,
        }
        if any(row[key] != str(value) for key, value in exact_fields.items()):
            crosswalk_field_failures.append(source["canonical_label"])
        expected_source_concepts = [r9_candidate_by_label[source["canonical_label"]]["candidate_id"]] if source["canonical_label"] in r9_candidate_by_label else []
        if json.loads(row["source_concept_ids_json"]) != expected_source_concepts:
            crosswalk_field_failures.append(f"source-concepts:{source['canonical_label']}")
        if row["record_sha256"] != sha256_text(canonical_json(expected_material)):
            crosswalk_field_failures.append(f"record-hash:{source['canonical_label']}")
    require("CROSSWALK_SOURCE_FIELDS_AND_HASHES_EXACT", not crosswalk_field_failures, crosswalk_field_failures[:20])

    # Input surfaces and build receipt are independently bound.
    input_by_surface = {row["input_surface_id"]: row for row in input_manifest}
    require("INPUT_SURFACE_IDS_UNIQUE", len(input_by_surface) == len(input_manifest) == 34)
    actual_input_specs = {
        key: (Path(row["path"]), row["record_selector"])
        for key, row in input_by_surface.items()
    }
    require("INPUT_SURFACE_PATHS_AND_SELECTORS_EXACT", actual_input_specs == EXPECTED_INPUT_SURFACES)
    expected_input_ids = {
        surface_id: f"R16B-LOCAL-INPUT-{index:03d}"
        for index, surface_id in enumerate(EXPECTED_INPUT_SURFACES, 1)
    }
    require(
        "INPUT_MANIFEST_IDS_AND_ORDER_EXACT",
        all(input_by_surface[surface_id]["input_id"] == input_id for surface_id, input_id in expected_input_ids.items())
        and [row["input_id"] for row in input_manifest] == list(expected_input_ids.values()),
    )
    require(
        "INPUT_MANIFEST_USE_BOUNDARY_EXACT",
        all(
            row["use_boundary"]
            == "CANDIDATE_DISCOVERY_OR_PRIOR_RECONCILIATION_ONLY; NO SUPPORT DISPOSITION INHERITED"
            for row in input_manifest
        ),
    )
    input_failures: list[str] = []
    input_path_hashes: dict[str, str] = {}
    for row in input_manifest:
        path = repo / row["path"]
        if not path.is_file() or sha256_file(path) != row["sha256"] or path.stat().st_size != int(row["bytes"]):
            input_failures.append(row["input_surface_id"])
        else:
            input_path_hashes[row["path"]] = row["sha256"]
        if path.is_file() and selector_record_count(path, row["record_selector"]) != int(row["record_count"]):
            input_failures.append(f"record-count:{row['input_surface_id']}")
        if receipt["input_sha256"].get(row["path"]) != row["sha256"]:
            input_failures.append(f"receipt:{row['input_surface_id']}")
    require("INPUT_PATH_HASH_SIZE_AND_RECEIPT_EXACT", not input_failures, input_failures)
    require("RECEIPT_INPUT_HASH_KEY_SET_EXACT", receipt["input_sha256"] == input_path_hashes)
    require("PRODUCTION_SURFACE_ADDED", input_by_surface["R16B-LOCAL-SURF-R16A-PRODUCTION"]["path"] == str(R16A_READ_MODEL))
    require("ROUND13_MIRROR_NOT_DOUBLE_COUNTED", not any("06_VOCABULARY_GAP_EVIDENCE" in row["path"] for row in input_manifest))

    # Occurrence identities, resolutions, and family bindings.
    occurrence_failures: list[str] = []
    family_occurrences: dict[str, list[str]] = defaultdict(list)
    for row in occurrences:
        surface = input_by_surface.get(row["input_surface_id"])
        if not surface or surface["path"] != row["source_path"]:
            occurrence_failures.append(f"surface:{row['trigger_occurrence_id']}")
        raw_labels = json.loads(row["raw_participant_labels_json"])
        raw_senses = json.loads(row["raw_participant_sense_ids_json"])
        expected_raw_senses = [crosswalk_by_label[label]["participant_sense_id"] for label in raw_labels]
        if raw_senses != expected_raw_senses:
            occurrence_failures.append(f"label-sense:{row['trigger_occurrence_id']}")
        resolved = sorted({crosswalk_by_sense[value]["canonical_resolution_sense_id"] for value in raw_senses})
        if resolved != json.loads(row["participant_sense_ids_json"]):
            occurrence_failures.append(f"resolution:{row['trigger_occurrence_id']}")
        expected_set_key = sha256_text(canonical_json(resolved))
        if expected_set_key != row["participant_set_key"] or len(resolved) < 3:
            occurrence_failures.append(f"set:{row['trigger_occurrence_id']}")
        if row["candidate_id"] != f"R16B-LOCAL-FAMILY:{expected_set_key}":
            occurrence_failures.append(f"candidate-equation:{row['trigger_occurrence_id']}")
        if row["selector_version"] != SELECTOR_VERSION:
            occurrence_failures.append(f"selector:{row['trigger_occurrence_id']}")
        if EXPECTED_TRIGGER_ID_BY_CLASS.get(row["trigger_class"]) != row["trigger_id"]:
            occurrence_failures.append(f"trigger-map:{row['trigger_occurrence_id']}")
        record_refs = sorted(json.loads(row["input_record_refs_json"]))
        content_hashes = sorted(json.loads(row["content_hashes_json"]))
        expected_scope_id = stable_id("R16B-SCOPE-HYP", {
            "source_path": row["source_path"],
            "record_refs": record_refs,
            "locator": row["locator"],
            "content_hashes": content_hashes,
        })
        if row["scope_hypothesis_id"] != expected_scope_id:
            occurrence_failures.append(f"scope:{row['trigger_occurrence_id']}")
        identity = {
            "trigger_class": row["trigger_class"], "source_path": row["source_path"],
            "record_refs": record_refs, "locator": row["locator"],
            "content_hashes": content_hashes,
            "raw_participant_sense_ids": raw_senses, "selector_version": row["selector_version"],
        }
        if f"R16B-TRIGGER-OCC:{sha256_text(canonical_json(identity))}" != row["trigger_occurrence_id"]:
            occurrence_failures.append(f"id:{row['trigger_occurrence_id']}")
        material = {key: value for key, value in row.items() if key != "occurrence_sha256"}
        if sha256_text(canonical_json(material)) != row["occurrence_sha256"]:
            occurrence_failures.append(f"hash:{row['trigger_occurrence_id']}")
        if row["candidate_id"] not in family_by_id:
            occurrence_failures.append(f"candidate:{row['trigger_occurrence_id']}")
        family_occurrences[row["candidate_id"]].append(row["trigger_occurrence_id"])
    require("OCCURRENCE_COUNT_348", len(occurrences) == 348, len(occurrences))
    require("OCCURRENCE_IDS_UNIQUE", len({row["trigger_occurrence_id"] for row in occurrences}) == 348)
    require("OCCURRENCE_IDENTITIES_RESOLVE", not occurrence_failures, occurrence_failures[:20])
    require("TRIGGER_CLASS_COUNTS_EXACT", Counter(row["trigger_class"] for row in occurrences) == EXPECTED_TRIGGER_CLASSES, Counter(row["trigger_class"] for row in occurrences))
    require("TRIGGER_ID_COUNTS_EXACT", Counter(row["trigger_id"] for row in occurrences) == EXPECTED_TRIGGER_IDS, Counter(row["trigger_id"] for row in occurrences))

    # Reconstruct the complete method-surface disposition partition, including
    # the selected two-party chain control that must emit no higher-order row.
    method_surface_rows = read_tsv(repo / METHOD_SURFACES)
    method_surface_by_id = {row["surface_id"]: row for row in method_surface_rows}
    disposition_by_id = {row["surface_id"]: row for row in surface_dispositions}
    require(
        "METHOD_SURFACE_INVENTORY_AND_LEDGER_IDS_EXACT",
        len(method_surface_rows) == len(method_surface_by_id) == len(surface_dispositions) == len(disposition_by_id) == 44
        and set(method_surface_by_id) == set(disposition_by_id)
        and [row["surface_id"] for row in surface_dispositions] == [row["surface_id"] for row in method_surface_rows],
    )
    input_by_path_selector = {(row["path"], row["record_selector"]): row for row in input_manifest}
    require("INPUT_PATH_SELECTOR_KEYS_UNIQUE", len(input_by_path_selector) == len(input_manifest) == 34)
    occurrence_count_by_input = Counter(row["input_surface_id"] for row in occurrences)
    chain_rows = read_tsv(repo / R10_CHAINS)
    chain_ids = [row["chain_id"] for row in chain_rows]
    expected_chain_content = {
        (
            "OBS-CHAIN-001",
            "GRAM-SRC-005",
            "REL-CAND-0005>REL-CAND-0006",
            "professionalization>institutionalization",
            "SOURCE_OBSERVED_SEQUENCE_AND_CONDITION",
            "false",
            "false",
        ),
        (
            "OBS-CHAIN-002",
            "GRAM-SRC-023",
            "REL-CAND-0032>REL-CAND-0033",
            "imitation>piracy",
            "SOURCE_OBSERVED_NORMATIVE_RECLASSIFICATION",
            "false",
            "false",
        ),
    }
    actual_chain_content = {
        (
            row["chain_id"],
            row["source_ids"],
            row["ordered_term_ids"],
            row["ordered_labels"],
            row["directionality"],
            row["transitive_inference"],
            row["active_grammar_selected"],
        )
        for row in chain_rows
    }
    chain_shape_exact = (
        len(chain_rows) == len(set(chain_ids)) == 2
        and actual_chain_content == expected_chain_content
        and all(len(row["ordered_labels"].split(">")) == 2 for row in chain_rows)
        and all(len(row["ordered_term_ids"].split(">")) == 2 for row in chain_rows)
        and all(row["transitive_inference"] == "false" for row in chain_rows)
        and all(row["active_grammar_selected"] == "false" for row in chain_rows)
    )
    expected_chain_proof = canonical_json({
        "row_count": len(chain_rows),
        "chain_ids": sorted(chain_ids),
        "ordered_labels": sorted(row["ordered_labels"] for row in chain_rows),
        "participant_count_each": [2 for _ in chain_rows],
        "transitive_inference_values": sorted(set(row["transitive_inference"] for row in chain_rows)),
        "active_grammar_selected_values": sorted(set(row["active_grammar_selected"] for row in chain_rows)),
        "higher_order_occurrence_count": 0,
    })
    chain_input = input_by_surface["R16B-LOCAL-SURF-R10-CHAINS"]
    require(
        "ROUND10_CHAIN_TWO_PARTY_INACTIVE_NONTRANSITIVE_ZERO_EMISSION",
        chain_shape_exact
        and chain_input["path"] == str(R10_CHAINS)
        and int(chain_input["record_count"]) == 2
        and occurrence_count_by_input[chain_input["input_surface_id"]] == 0,
    )
    surface_failures: list[str] = []
    expected_disposition_counts = {
        "DEFERRED_HUMAN_REVIEW_PENDING": 1,
        "DEFERRED_LOCAL_SELECTOR_REVIEW": 15,
        "DEFERRED_METADATA_QUERY_LOG_REVIEW": 1,
        "DEFERRED_SOURCE_RIGHTS_AND_EVIDENCE_REVIEW": 3,
        "DEFERRED_TRG009_DATABASE_DISCOVERY": 1,
        "INSPECTED_ZERO_HIGHER_ORDER_EMISSION": 1,
        "SELECTED_EXECUTION_INPUT": 22,
    }
    selected_next_action = "Carry the exact input and every emitted or reconciliation record into evidence and global-coherence review."
    for surface in method_surface_rows:
        surface_id = surface["surface_id"]
        row = disposition_by_id[surface_id]
        path = repo / surface["path"]
        selector = surface["record_selector"]
        count = selector_record_count(path, selector)
        size = path.stat().st_size
        digest = sha256_file(path)
        input_row = input_by_path_selector.get((surface["path"], selector))
        if surface_id == "SURF-R10-006":
            expected_disposition = "INSPECTED_ZERO_HIGHER_ORDER_EMISSION"
            expected_proof = expected_chain_proof
            next_action = "Retain as a bounded two-term chain control; do not infer transitivity, direction, pair activation, or a higher-order association."
        elif input_row:
            expected_disposition = "SELECTED_EXECUTION_INPUT"
            expected_proof = "NOT_APPLICABLE"
            next_action = selected_next_action
        elif surface["evidence_authority"] == "BIBLIOGRAPHIC_IDENTITY":
            expected_disposition = "DEFERRED_SOURCE_RIGHTS_AND_EVIDENCE_REVIEW"
            expected_proof = "NOT_REVIEWED_IN_CHECKPOINT003"
            next_action = "Review source identity, access, rights, locators, and bounded evidence before activating any trigger."
        elif surface_id == "SURF-DB-001":
            expected_disposition = "DEFERRED_TRG009_DATABASE_DISCOVERY"
            expected_proof = "NOT_REVIEWED_IN_CHECKPOINT003"
            next_action = "Run governed database discovery; treat co-occurrence as a lead only and require scholarly follow-up."
        elif surface["evidence_authority"] == "PENDING_HUMAN_REVIEW":
            expected_disposition = "DEFERRED_HUMAN_REVIEW_PENDING"
            expected_proof = "NOT_REVIEWED_IN_CHECKPOINT003"
            next_action = "Keep affected claims inactive until independent human review is completed and recorded."
        elif surface["evidence_authority"] == "METADATA_DISCOVERY_ONLY":
            expected_disposition = "DEFERRED_METADATA_QUERY_LOG_REVIEW"
            expected_proof = "NOT_REVIEWED_IN_CHECKPOINT003"
            next_action = "Reconcile metadata-only results during adaptive source discovery; metadata cannot support an association."
        else:
            expected_disposition = "DEFERRED_LOCAL_SELECTOR_REVIEW"
            expected_proof = "NOT_REVIEWED_IN_CHECKPOINT003"
            next_action = "Implement and independently verify a bounded selector or a record-exact non-emission proof in a later tranche."
        occurrence_count = occurrence_count_by_input[input_row["input_surface_id"]] if input_row else 0
        material = {
            "surface_id": surface_id,
            "path": surface["path"],
            "record_selector": selector,
            "record_count": count,
            "bytes": size,
            "sha256": digest,
            "matched_input_id": input_row["input_id"] if input_row else "",
            "trigger_occurrence_count": occurrence_count,
            "disposition": expected_disposition,
            "zero_emission_proof": expected_proof,
        }
        exact = (
            int(surface["record_count"]) == count
            and int(surface["bytes"]) == size
            and surface["sha256"] == digest
            and row["round"] == surface["round"]
            and row["path"] == surface["path"]
            and row["record_selector"] == selector
            and int(row["record_count"]) == count
            and int(row["bytes"]) == size
            and row["sha256"] == digest
            and row["evidence_authority"] == surface["evidence_authority"]
            and row["candidate_trigger_ids"] == surface["candidate_trigger_ids"]
            and json.loads(row["matched_input_ids_json"]) == ([input_row["input_id"]] if input_row else [])
            and int(row["trigger_occurrence_count"]) == occurrence_count
            and row["disposition"] == expected_disposition
            and row["zero_emission_proof"] == expected_proof
            and row["candidate_universe_closure_effect"] == ("OPEN" if expected_disposition.startswith("DEFERRED_") else "ACCOUNTED_IN_CHECKPOINT003_LOCAL_TRANCHE")
            and row["required_next_action"] == next_action
            and row["record_sha256"] == sha256_text(canonical_json(material))
        )
        if not exact:
            surface_failures.append(surface_id)
    surface_disposition_counts = Counter(row["disposition"] for row in surface_dispositions)
    selected_method_surface_count = sum(not row["disposition"].startswith("DEFERRED_") for row in surface_dispositions)
    deferred_method_surface_count = sum(row["disposition"].startswith("DEFERRED_") for row in surface_dispositions)
    require("METHOD_SURFACE_SOURCE_BINDINGS_DISPOSITIONS_AND_HASHES_EXACT", not surface_failures, surface_failures[:20])
    require(
        "METHOD_SURFACE_23_ACCOUNTED_21_EXPLICIT_DEFERRALS",
        selected_method_surface_count == 23
        and deferred_method_surface_count == 21
        and surface_disposition_counts == expected_disposition_counts
        and all(row["candidate_universe_closure_effect"] == "OPEN" for row in surface_dispositions if row["disposition"].startswith("DEFERRED_")),
        surface_disposition_counts,
    )

    # Reconstruct all structural occurrence IDs directly from frozen sources.
    expected_structural_ids = {
        "EXPLICIT_CLUSTER_NEAR_MISS": {row["cluster_handoff_id"] for row in read_tsv(repo / R10_CLUSTERS)},
        "ROUND14_NARY_FIXTURE": {row["fixtureId"] for row in read_json(repo / R14_NARY)["fixtures"]},
        "ROUND15_COMPOSITION_FIXTURE": {row["fixtureId"] for row in read_json(repo / R15_FIXTURES)["fixtures"] if len(set(row["nodeIds"])) >= 3},
        "ROUND16_LEGACY_COMPOSITION": {row["compositionId"] for row in read_json(repo / R16_COMPOSITIONS)["compositions"] if len(set(row["nodeIds"])) >= 3},
        "ROUND16A_CONNECTED_SUBGRAPH": {row["association_subgraph_id"] for row in read_json(repo / R16A_REGISTRY)["association_subgraphs"] if row["node_count"] >= 3},
        "ROUND16A_TOPOLOGY_COMPOSITION": {row["composition_id"] for row in read_json(repo / R16A_REGISTRY)["topology_compositions"] if row["node_count"] >= 3},
        "ROUND16A_PRODUCTION_COMPOSITION": {key for key, row in read_json(repo / R16A_READ_MODEL)["compositions"].items() if len(set(row["node_ids"])) >= 3},
    }
    structural_failures = []
    for trigger_class, expected_ids in expected_structural_ids.items():
        actual = {json.loads(row["input_record_refs_json"])[0] for row in occurrences if row["trigger_class"] == trigger_class}
        if actual != expected_ids:
            structural_failures.append(trigger_class)
    require("STRUCTURAL_SOURCE_ID_SETS_EXACT", not structural_failures, structural_failures)
    require("STRUCTURAL_OCCURRENCE_COUNT_319", sum(len(value) for value in expected_structural_ids.values()) == 319)

    # Direct evidence/control selectors are deliberately exact and bounded.
    refs_by_class = {
        key: {value for row in occurrences if row["trigger_class"] == key for value in json.loads(row["input_record_refs_json"])}
        for key in EXPECTED_TRIGGER_CLASSES
    }
    require("ROUND10_DIRECT_IDS_EXACT", refs_by_class["ROUND10_DIRECT_PASSAGE"] == {"GRAM-ATT-001", "GRAM-ATT-002", "GRAM-ATT-026"})
    require("ROUND13_DIRECT_IDS_EXACT", refs_by_class["ROUND13_DIRECT_POSITIVE_FIELD_PASSAGE"] == {"COMP-EVID-008", "COMP-EVID-010", "COMP-EVID-011", "COMP-EVID-014", "COMP-EVID-021", "COMP-EVID-026"})
    require("ROUND13_INCIDENTAL_CONTROL_ID_EXACT", refs_by_class["ROUND13_INCIDENTAL_CASE_LABEL_CONTROL"] == {"COMP-EVID-003"})
    require("ROUND9_COLLISION_IDS_EXACT", refs_by_class["ROUND9_SOURCE_LOCATOR_CONTEXT_COLLISION"] == {"ATT-0005", "ATT-0018", "ATT-0029"})
    require("R14_ARCHIVE_IDS_EXACT", refs_by_class["ROUND14_ARCHIVE_EXACT_CONTEXT_DUPLICATE"] == {"R14-EVID-018-01", "R14-EVID-027-01", "R14-EVID-031-01", "R14-EVID-032-01"})
    require("CONSUMER_CONTEXT_PRIMARY_AND_CORROBORATION", refs_by_class["ROUND13_QUALIFICATION_CONTEXT_EXTENSION"] == {"COMP-EVID-004", f"{R10_ATTEST}#GRAM-ATT-027"})
    require("QUALIFIED_OVERLAP_ROWS_EXACT", refs_by_class["ROUND14_QUALIFIED_SHARED_LOCUS_OVERLAP"] == {"R14-EVID-013-01", "R14-EVID-014-01", "R14-EVID-015-01", "R14-EVID-022-03"})
    require("ROUND14_CONCEPT_ONLY_LEAD_REFS_EXACT", refs_by_class["ROUND14_CONCEPT_ONLY_HIGHER_ORDER_LEAD"] == {"R14-EVID-025-02", f"{R13_EVIDENCE}#COMP-EVID-022"})
    r13_source_by_id = {row["evidence_id"]: row for row in read_tsv(repo / R13_EVIDENCE)}
    added_r13_occurrence_failures: list[str] = []
    for record_id, trigger_class, expected_labels in [
        ("COMP-EVID-011", "ROUND13_DIRECT_POSITIVE_FIELD_PASSAGE", ["production", "mediating devices", "consumption"]),
        ("COMP-EVID-003", "ROUND13_INCIDENTAL_CASE_LABEL_CONTROL", ["commodification", "gendering", "Brazilian exposition"]),
    ]:
        matches = [
            row for row in occurrences
            if row["trigger_class"] == trigger_class and json.loads(row["input_record_refs_json"]) == [record_id]
        ]
        source = r13_source_by_id[record_id]
        if not (
            len(matches) == 1
            and json.loads(matches[0]["raw_participant_labels_json"]) == expected_labels
            and matches[0]["locator"] == source["locator"]
            and json.loads(matches[0]["content_hashes_json"]) == [sha256_text(canonical_json(source))]
        ):
            added_r13_occurrence_failures.append(record_id)
    require("ADDED_R13_SELECTORS_MATCH_SOURCE_EXACTLY", not added_r13_occurrence_failures, added_r13_occurrence_failures)
    concept_leads = [row for row in occurrences if row["trigger_class"] == "ROUND14_CONCEPT_ONLY_HIGHER_ORDER_LEAD"]
    provenance_by_evidence = {row["evidence_id"]: row for row in read_tsv(repo / R14_PROVENANCE)}
    mobility_source = provenance_by_evidence["R14-EVID-025-02"]
    mobility_upstream = r13_source_by_id["COMP-EVID-022"]
    require(
        "ROUND14_CONCEPT_ONLY_LEAD_MATCHES_SOURCES",
        len(concept_leads) == 1
        and json.loads(concept_leads[0]["raw_participant_labels_json"]) == ["cultural mobility", "mobile object", "mediation"]
        and concept_leads[0]["locator"] == mobility_source["locator"]
        and json.loads(concept_leads[0]["content_hashes_json"]) == sorted([
            sha256_text(canonical_json(mobility_source)),
            sha256_text(canonical_json(mobility_upstream)),
        ])
        and concept_leads[0]["polarity"] == "INQUIRY_ONLY_HIGHER_ORDER_LEAD"
        and concept_leads[0]["emission_kind"] == "DIRECT_PASSAGE_INQUIRY_FAMILY",
    )

    # Independently derive the ten active exact-source+locator pair bundles.
    assessments = {row["assessmentId"]: row for row in read_json(repo / R14_ASSESSMENTS)["assessments"]}
    provenance_rows = read_tsv(repo / R14_PROVENANCE)
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in provenance_rows:
        if row["support_role"] == "ASSOCIATION_SUPPORT" and assessments[row["assessment_id"]]["activeForProximity"]:
            groups[(row["source_id"], row["locator"])].append(row)
    expected_groups = {
        tuple(sorted(row["evidence_id"] for row in values))
        for values in groups.values()
        if len(
            {
                label
                for row in values
                for label in (
                    assessments[row["assessment_id"]]["nodeA"],
                    assessments[row["assessment_id"]]["nodeB"],
                )
            }
        ) >= 3
    }
    actual_groups = {tuple(sorted(json.loads(row["input_record_refs_json"]))) for row in occurrences if row["trigger_class"] == "ROUND14_ACTIVE_PAIR_SHARED_LOCUS_BUNDLE"}
    require("R14_ACTIVE_LOCUS_GROUPS_EXACT", len(expected_groups) == 10 and actual_groups == expected_groups, len(expected_groups))

    # Family reconstruction and fail-closed lifecycle.
    occurrence_by_id = {row["trigger_occurrence_id"]: row for row in occurrences}
    structural_families: set[tuple[str, ...]] = set()
    for trigger_class in expected_structural_ids:
        for row in occurrences:
            if row["trigger_class"] == trigger_class:
                structural_families.add(family_normal_form(json.loads(row["raw_participant_labels_json"])))
    extra_families = {
        family_normal_form(value) for value in [
            ["adaptation", "cultural negotiation", "cultural transfer", "rejection"],
            ["appropriation", "creative appropriation", "design exchanges"],
            ["commodification", "consumer culture", "gendering"],
            ["commodification", "gendering", "Brazilian exposition"],
            ["consumption", "material displacement", "production", "production site", "supply chain"],
            ["consumption", "mediating channels", "production"],
            ["consumption", "mediating devices", "production"],
            ["craft", "design education", "education"],
            ["education", "institutionalization", "professionalization"],
            ["exhibition", "photography", "typography"],
            ["cultural mobility", "mobile object", "mediation"],
        ]
    }
    actual_families = {family_normal_form(json.loads(row["canonical_labels_json"])) for row in families}
    require("STRUCTURAL_FAMILY_COUNT_AND_DIGEST", len(structural_families) == 20 and family_digest(structural_families) == "86858975b8b2758af6986f13be44239f9203530db58cb7641c837b0b18560c5c")
    require("EXTRA_FAMILY_COUNT_AND_DIGEST", len(extra_families) == 11 and family_digest(extra_families) == "dbf95e03c9b2a843a1659862e245e82790a7ba70af4c077d0d1a43e14dc0b541")
    require("FULL_FAMILY_SET_EXACT", actual_families == structural_families | extra_families and family_digest(actual_families) == "4e642a548250ab19cc9c0bbe3339499bc4352c68c79e0cc2540269fa1b53da7c")
    require("FAMILY_COUNT_AND_ARITY", len(families) == 31 and Counter(row["arity"] for row in families) == EXPECTED_ARITY, Counter(row["arity"] for row in families))
    require("FAMILY_IDS_UNIQUE", len(family_by_id) == len(families) == 31)
    family_identity_failures: list[str] = []
    family_senses_by_id: dict[str, tuple[str, ...]] = {}
    for row in families:
        candidate_id = row["candidate_id"]
        senses = json.loads(row["participant_sense_ids_json"])
        expected_senses_for_family = sorted(set(senses))
        family_senses_by_id[candidate_id] = tuple(expected_senses_for_family)
        expected_set_key = sha256_text(canonical_json(expected_senses_for_family))
        expected_candidate_id = f"R16B-LOCAL-FAMILY:{expected_set_key}"
        expected_labels = [crosswalk_by_sense[value]["canonical_label"] for value in expected_senses_for_family]
        occurrence_ids = sorted(family_occurrences[candidate_id])
        expected_trigger_ids = sorted({occurrence_by_id[value]["trigger_id"] for value in occurrence_ids})
        expected_emission_kinds = sorted({occurrence_by_id[value]["emission_kind"] for value in occurrence_ids})
        disposition_counts_for_family = Counter(crosswalk_by_sense[value]["disposition"] for value in expected_senses_for_family)
        expected_eligibility = "CONTROL_ONLY_REJECTED_PARTICIPANT" if disposition_counts_for_family["REJECTED"] else "REVIEW_ELIGIBLE_NOT_VALIDATED"
        family_material = {
            "candidate_id": expected_candidate_id,
            "participant_sense_ids": expected_senses_for_family,
            "scope_resolution_status": "UNRESOLVED_MAY_SPLIT_BY_CASE",
            "occurrence_ids": occurrence_ids,
        }
        equations_hold = (
            senses == expected_senses_for_family
            and candidate_id == expected_candidate_id
            and row["participant_set_key"] == expected_set_key
            and json.loads(row["canonical_labels_json"]) == expected_labels
            and int(row["arity"]) == len(expected_senses_for_family)
            and int(row["occurrence_count"]) == len(occurrence_ids)
            and sorted(json.loads(row["trigger_occurrence_ids_json"])) == occurrence_ids
            and json.loads(row["trigger_ids_json"]) == expected_trigger_ids
            and json.loads(row["emission_kinds_json"]) == expected_emission_kinds
            and int(row["active_participant_count"]) == disposition_counts_for_family["ACTIVE"]
            and int(row["research_only_participant_count"]) == disposition_counts_for_family["RESEARCH_ONLY"]
            and int(row["rejected_participant_count"]) == disposition_counts_for_family["REJECTED"]
            and row["candidate_object_kind"] == "LOCAL_PARTICIPANT_SET_REVIEW_FAMILY_NOT_ASSOCIATION"
            and row["order_semantics"] == "UNRESOLVED"
            and row["role_semantics"] == "UNRESOLVED"
            and row["scope_resolution_status"] == "UNRESOLVED_MAY_SPLIT_BY_CASE"
            and row["case_resolution_status"] == "UNRESOLVED"
            and row["participant_eligibility"] == expected_eligibility
            and row["family_content_sha256"] == sha256_text(canonical_json(family_material))
        )
        if not equations_hold:
            family_identity_failures.append(candidate_id)
    require("FAMILY_IDENTITIES_CONTENT_AND_COUNTS_EXACT", not family_identity_failures, family_identity_failures[:20])
    require("FAMILY_OCCURRENCE_PARTITIONS_EXACT", all(sorted(json.loads(row["trigger_occurrence_ids_json"])) == sorted(family_occurrences[row["candidate_id"]]) and int(row["occurrence_count"]) == len(family_occurrences[row["candidate_id"]]) for row in families))
    require("ALL_FAMILIES_FAIL_CLOSED", all(row["lifecycle_state"] == "DISCOVERED" and row["proposed_disposition"] == "PENDING_GOVERNED_REVIEW" and row["evidence_review_status"] == "NOT_STARTED" and row["global_coherence_status"] == "NOT_REVIEWED" and row["product_eligibility"] == "INELIGIBLE_PENDING_GOVERNED_REVIEW" and row["association_identity_frozen"] == "False" for row in families))
    require("CONTROL_ONLY_FAMILY_COUNT_3", Counter(row["participant_eligibility"] for row in families)["CONTROL_ONLY_REJECTED_PARTICIPANT"] == 3)
    used_senses = {value for row in families for value in json.loads(row["participant_sense_ids_json"])}
    used_dispositions = Counter(crosswalk_by_sense[value]["disposition"] for value in used_senses)
    require("FAMILY_SENSE_DISTRIBUTION_EXACT", len(used_senses) == 43 and used_dispositions == {"ACTIVE": 30, "RESEARCH_ONLY": 6, "REJECTED": 7}, used_dispositions)
    require("SELF_EXOTICIZATION_NOT_IN_FAMILIES", crosswalk_by_label["self-exoticization"]["participant_sense_id"] not in used_senses)

    # Open-role and isolated-term queues.
    source_open_role_rows = [row for row in read_tsv(repo / R10_ROLES) if row["arity"] in {"MULTIPARTY", "2+", "3", "3+", "STRUCTURAL"}]
    source_open_roles = {row["candidate_id"] for row in source_open_role_rows}
    require("OPEN_ROLE_QUEUE_EXACT", len(open_roles) == 10 and {row["source_candidate_id"] for row in open_roles} == source_open_roles)
    require("OPEN_ROLE_QUEUE_NOT_EMITTED", all(row["participant_resolution_status"] == "OPEN" and row["candidate_emitted"] == "false" for row in open_roles))
    open_role_by_source = {row["source_candidate_id"]: row for row in open_roles}
    open_role_failures: list[str] = []
    expected_open_role_reason = "Round 10 arity describes argument roles, not a closed governed concept participant set; role nouns are not promoted to vocabulary concepts."
    for source in source_open_role_rows:
        row = open_role_by_source[source["candidate_id"]]
        support_ids = split_semicolon(source["source_support_ids"])
        material = {
            "candidate_id": source["candidate_id"],
            "arity": source["arity"],
            "roles": [source["subject_role"], source["target_role"], source["additional_party_roles"]],
            "source_support_ids": support_ids,
        }
        exact = (
            row["participant_resolution_queue_id"] == stable_id("R16B-PARTICIPANT-QUEUE", material)
            and row["source_path"] == str(R10_ROLES)
            and row["relation_label"] == source["candidate_label"]
            and row["relation_participant_sense_id"] == crosswalk_by_label[source["candidate_label"]]["participant_sense_id"]
            and row["declared_argument_arity"] == source["arity"]
            and all(row[key] == source[key] for key in ["subject_role", "target_role", "additional_party_roles", "required_context", "required_qualification"])
            and json.loads(row["source_support_ids_json"]) == support_ids
            and row["reason"] == expected_open_role_reason
            and row["record_sha256"] == sha256_text(canonical_json(material))
        )
        if not exact:
            open_role_failures.append(source["candidate_id"])
    require("OPEN_ROLE_IDENTITIES_AND_SOURCE_FIELDS_EXACT", not open_role_failures, open_role_failures)
    graph = read_json(repo / R16A_GRAPH)
    isolated_nodes = [row for row in graph["nodes"] if row["isolated"]]
    source_isolated = {row["canonical_label"] for row in isolated_nodes}
    require("ISOLATED_ACTIVE_SET_EXACT", len(isolated) == 5 and {row["canonical_label"] for row in isolated} == source_isolated == {"canonization", "cultural transfer", "cultural transformation", "mobile object", "self-exoticization"})
    require("ISOLATED_TERMS_NOT_PREMATURELY_COMPOSABLE", all(row["higher_order_composability_proven"] == "false" and row["product_accessibility_disposition"] == "OPEN" for row in isolated))
    isolated_by_label = {row["canonical_label"]: row for row in isolated}
    isolated_failures: list[str] = []
    expected_isolated_action = "Review exact group evidence and either validate a product path, keep inquiry-only, reclassify vocabulary, or record an explicit non-product policy."
    for node in isolated_nodes:
        row = isolated_by_label[node["canonical_label"]]
        participant_sense_id = crosswalk_by_label[node["canonical_label"]]["participant_sense_id"]
        expected_family_ids = sorted(candidate_id for candidate_id, senses in family_senses_by_id.items() if participant_sense_id in senses)
        exact = (
            row["isolation_audit_id"] == stable_id("R16B-ISOLATED-AUDIT", {"vocabulary_id": node["vocabulary_id"]})
            and row["vocabulary_id"] == node["vocabulary_id"]
            and row["participant_sense_id"] == participant_sense_id
            and row["round16a_pair_degree"] == str(node["degree"])
            and json.loads(row["local_candidate_family_ids_json"]) == expected_family_ids
            and row["required_next_action"] == expected_isolated_action
        )
        if not exact:
            isolated_failures.append(node["canonical_label"])
    require("ISOLATED_IDENTITIES_AND_FAMILY_LINKS_EXACT", not isolated_failures, isolated_failures)

    # Prior-object commitments and detailed shards.
    require("PRIOR_SHARD_FILE_SET_EXACT", {path.name for path in prior_files} == EXPECTED_PRIOR_SHARDS, [path.name for path in prior_files])
    manifest_by_type = {row["prior_object_type"]: row for row in set_manifest}
    require("PRIOR_SET_MANIFEST_COMPLETE", set(manifest_by_type) == set(EXPECTED_MANIFEST) and len(set_manifest) == 43)
    manifest_failures = []
    for object_type, (count, digest) in EXPECTED_MANIFEST.items():
        row = manifest_by_type.get(object_type, {})
        expected_path, expected_selector, expected_row_exact = EXPECTED_MANIFEST_METADATA[object_type]
        if int(row.get("record_count", -1)) != count or int(row.get("unique_id_count", -1)) != count or row.get("sorted_id_set_sha256") != digest:
            manifest_failures.append(object_type)
        if (
            row.get("source_path") != str(expected_path)
            or row.get("record_selector") != expected_selector
            or row.get("row_exact_reconciliation_ledger") != str(expected_row_exact).lower()
        ):
            manifest_failures.append(f"metadata:{object_type}")
        path = repo / row.get("source_path", "MISSING")
        if not path.is_file() or sha256_file(path) != row.get("source_sha256") or path.stat().st_size != int(row.get("source_bytes", -1)):
            manifest_failures.append(f"source:{object_type}")
    require("PRIOR_SET_COUNTS_HASHES_AND_SOURCES_EXACT", not manifest_failures, manifest_failures)
    require("TRANSITION_LEDGER_NOT_DUPLICATED", manifest_by_type["ROUND16A_TRANSITION"]["row_exact_reconciliation_ledger"] == "false" and "WITHOUT_DUPLICATING_LFS_LEDGER" in manifest_by_type["ROUND16A_TRANSITION"]["coverage_status"])
    prior_distribution = Counter(row["prior_object_type"] for row in prior_rows)
    expected_row_exact = {object_type: count for object_type, (count, _) in EXPECTED_MANIFEST.items() if manifest_by_type[object_type]["row_exact_reconciliation_ledger"] == "true"}
    require("PRIOR_ROW_EXACT_DISTRIBUTION", prior_distribution == expected_row_exact and len(prior_rows) == 32135, prior_distribution)
    require("PRIOR_ROW_KEYS_UNIQUE", len({(row["prior_object_type"], row["prior_id"]) for row in prior_rows}) == len(prior_rows))
    require("PRIOR_ROWS_ALL_PENDING", all("PENDING" in row["reconciliation_status"] and row["coverage_mode"] == "ROW_EXACT" for row in prior_rows))
    require("PRIOR_SHARDS_BELOW_WARNING", all(path.stat().st_size < 25_000_000 for path in prior_files), {path.name: path.stat().st_size for path in prior_files})
    prior_ids_by_type: dict[str, list[str]] = defaultdict(list)
    for row in prior_rows:
        prior_ids_by_type[row["prior_object_type"]].append(row["prior_id"])
    require(
        "PRIOR_ROW_ID_SETS_MATCH_MANIFEST",
        all(id_hash(prior_ids_by_type[object_type]) == manifest_by_type[object_type]["sorted_id_set_sha256"] for object_type in expected_row_exact),
    )
    family_id_by_senses = {senses: candidate_id for candidate_id, senses in family_senses_by_id.items()}
    expected_prior_action = "Assign an evidence and global-coherence disposition, then regenerate or retire downstream product objects without silently carrying v2 semantics."
    prior_row_failures: list[str] = []
    for row in prior_rows:
        object_type = row["prior_object_type"]
        senses = json.loads(row["participant_sense_ids_json"])
        parent_ids = json.loads(row["prior_parent_ids_json"])
        association_ids = json.loads(row["prior_association_ids_json"])
        expected_senses = sorted(set(senses))
        expected_candidate_id = family_id_by_senses.get(tuple(expected_senses), "") if len(expected_senses) >= 3 else ""
        if len(expected_senses) >= 3 and expected_candidate_id:
            expected_status = "HIGHER_ORDER_FAMILY_REVIEW_PENDING"
        elif len(expected_senses) == 2:
            expected_status = "PAIRWISE_BASELINE_RECONCILIATION_PENDING"
        else:
            expected_status = "OBJECT_POLICY_RECONCILIATION_PENDING"
        material = {
            "prior_object_type": object_type,
            "prior_id": row["prior_id"],
            "source_path": row["source_path"],
            "source_record_ref": row["source_record_ref"],
            "participant_sense_ids": expected_senses,
            "parent_ids": sorted(parent_ids),
            "association_ids": sorted(association_ids),
            "topology": row["prior_topology"],
            "prior_status": row["prior_status"],
            "candidate_id": expected_candidate_id,
            "extra": {},
        }
        equations_hold = (
            senses == expected_senses
            and parent_ids == sorted(parent_ids)
            and association_ids == sorted(association_ids)
            and row["source_path"] == str(EXPECTED_MANIFEST_METADATA[object_type][0])
            and bool(row["source_record_ref"])
            and row["participant_set_key"] == (sha256_text(canonical_json(expected_senses)) if expected_senses else "")
            and json.loads(row["round16b_candidate_ids_json"]) == ([expected_candidate_id] if expected_candidate_id else [])
            and row["reconciliation_status"] == expected_status
            and row["required_next_action"] == expected_prior_action
            and row["coverage_mode"] == "ROW_EXACT"
            and row["record_sha256"] == sha256_text(canonical_json(material))
        )
        if not equations_hold:
            prior_row_failures.append(f"{object_type}:{row['prior_id']}")
    require("PRIOR_ROW_IDENTITIES_LINKS_STATUS_AND_HASHES_EXACT", not prior_row_failures, prior_row_failures[:20])

    # Independently enumerate every Git blob in the governed Round 15/16/16A
    # artifact namespaces at the authorized source commit.  This deliberately
    # uses Git's source tree rather than the generator's working-tree walk.
    source_tree_result = subprocess.run(
        ["git", "rev-parse", f"{SOURCE_SHA}^{{tree}}"],
        cwd=repo,
        check=True,
        text=True,
        capture_output=True,
    )
    actual_source_tree = source_tree_result.stdout.strip()
    require("SOURCE_TREE_OBJECT_EXACT", actual_source_tree == SOURCE_TREE, actual_source_tree)

    expected_prior_files: dict[str, dict[str, Any]] = {}
    namespace_counts: Counter[str] = Counter()
    namespace_scan_failures: list[str] = []
    for namespace_id, namespace_prefix in PRIOR_ARTIFACT_NAMESPACES:
        tree_result = subprocess.run(
            ["git", "ls-tree", "-r", "-l", SOURCE_SHA, "--", namespace_prefix],
            cwd=repo,
            check=True,
            text=True,
            capture_output=True,
        )
        for line in tree_result.stdout.splitlines():
            try:
                metadata, path = line.split("\t", 1)
                mode, object_type, object_sha, object_bytes = metadata.split()
                size = int(object_bytes)
            except (ValueError, TypeError):
                namespace_scan_failures.append(f"parse:{namespace_id}:{line}")
                continue
            if object_type != "blob" or path in expected_prior_files:
                namespace_scan_failures.append(f"object-or-overlap:{namespace_id}:{path}")
                continue
            expected_prior_files[path] = {
                "namespace_id": namespace_id,
                "namespace_prefix": namespace_prefix,
                "git_mode": mode,
                "git_object_type": object_type,
                "git_blob_sha": object_sha,
                "git_blob_bytes": size,
            }
            namespace_counts[namespace_id] += 1
        if namespace_counts[namespace_id] == 0:
            namespace_scan_failures.append(f"empty:{namespace_id}:{namespace_prefix}")
    require(
        "PRIOR_ARTIFACT_NAMESPACE_LS_TREE_EXACT",
        not namespace_scan_failures
        and len(expected_prior_files) == 1464
        and len(namespace_counts) == len(PRIOR_ARTIFACT_NAMESPACES) == 16,
        {"failures": namespace_scan_failures[:20], "counts": dict(namespace_counts)},
    )

    artifact_by_path = {row["path"]: row for row in prior_artifact_files}
    expected_artifact_paths = set(expected_prior_files)
    require(
        "PRIOR_ARTIFACT_PATHS_UNIQUE_ORDERED_AND_COMPLETE",
        len(prior_artifact_files) == len(artifact_by_path) == 1464
        and set(artifact_by_path) == expected_artifact_paths
        and [row["path"] for row in prior_artifact_files] == sorted(expected_artifact_paths),
    )
    object_types_by_path: dict[str, list[str]] = defaultdict(list)
    for manifest_row in set_manifest:
        object_types_by_path[manifest_row["source_path"]].append(manifest_row["prior_object_type"])
    expected_artifact_action = (
        "Preserve or explicitly supersede this source-tree artifact; where no row-level commitment exists, "
        "complete object-policy and semantic reconciliation before final closure."
    )
    artifact_failures: list[str] = []
    covered_manifest_types: set[str] = set()
    for path, source_binding in expected_prior_files.items():
        row = artifact_by_path.get(path)
        if row is None:
            artifact_failures.append(f"missing:{path}")
            continue
        covered_types = sorted(object_types_by_path.get(path, []))
        covered_manifest_types.update(covered_types)
        coverage_mode = (
            "ROW_EXACT_PLUS_FILE_BOUND"
            if covered_types
            else "FILE_BOUND_OBJECT_POLICY_RECONCILIATION_PENDING"
        )
        material = {
            "source_sha": SOURCE_SHA,
            "source_tree": SOURCE_TREE,
            "namespace_id": source_binding["namespace_id"],
            "namespace_prefix": source_binding["namespace_prefix"],
            "path": path,
            "git_mode": source_binding["git_mode"],
            "git_object_type": source_binding["git_object_type"],
            "git_blob_sha": source_binding["git_blob_sha"],
            "git_blob_bytes": source_binding["git_blob_bytes"],
            "object_set_coverage": covered_types,
            "coverage_mode": coverage_mode,
            "reconciliation_status": "PENDING",
        }
        exact = (
            row["prior_artifact_file_id"] == stable_id("R16B-PRIOR-FILE", {"path": path})
            and row["source_sha"] == SOURCE_SHA
            and row["source_tree"] == SOURCE_TREE
            and row["namespace_id"] == source_binding["namespace_id"]
            and row["namespace_prefix"] == source_binding["namespace_prefix"]
            and row["git_mode"] == source_binding["git_mode"]
            and row["git_object_type"] == "blob" == source_binding["git_object_type"]
            and row["git_blob_sha"] == source_binding["git_blob_sha"]
            and int(row["git_blob_bytes"]) == source_binding["git_blob_bytes"]
            and json.loads(row["object_set_coverage_json"]) == covered_types
            and row["coverage_mode"] == coverage_mode
            and row["reconciliation_status"] == "PENDING"
            and row["required_next_action"] == expected_artifact_action
            and row["record_sha256"] == sha256_text(canonical_json(material))
        )
        if not exact:
            artifact_failures.append(path)
    expected_covered_manifest_types = {
        row["prior_object_type"]
        for row in set_manifest
        if row["source_path"] in expected_artifact_paths
    }
    require(
        "PRIOR_ARTIFACT_METADATA_COVERAGE_STATUS_AND_HASHES_EXACT",
        not artifact_failures
        and covered_manifest_types == expected_covered_manifest_types
        and all(row["reconciliation_status"] == "PENDING" for row in prior_artifact_files),
        artifact_failures[:20],
    )

    # Cross-round no-loss and topology invariants.
    r15_fixtures = read_json(repo / R15_FIXTURES)["fixtures"]
    r15_decisions = read_json(repo / R15_DECISIONS)["images"]
    r15_results = read_tsv(repo / R15_RESULTS)
    require("ROUND15_ONE_TO_ONE", {row["fixtureId"] for row in r15_fixtures} == {row["audit"]["fixture_id"] for row in r15_decisions} == {row["fixture_id"] for row in r15_results})
    r16_registry = read_json(repo / R16_COMPOSITIONS)["compositions"]
    r16_model = read_json(repo / R16_READ_MODEL)
    r16_ids = {row["compositionId"] for row in r16_registry}
    require("ROUND16_COMPOSITION_SET_EXACT", r16_ids == set(r16_model["compositions"]) and len(r16_ids) == 11)
    registry = read_json(repo / R16A_REGISTRY)
    legacy_counts = Counter(row["disposition"] for row in registry["round16_legacy_reconciliation"])
    require("ROUND16_LEGACY_DISPOSITIONS_PRESERVED", legacy_counts == {"PRESERVED_CANONICAL": 7, "REJECTED_WITH_REASON": 4})
    r16_composition_by_id = {row["compositionId"]: row for row in r16_registry}
    r16_composition_senses = {
        composition_id: sorted({crosswalk_by_label[label]["canonical_resolution_sense_id"] for label in row["nodeIds"]})
        for composition_id, row in r16_composition_by_id.items()
    }
    r16a_model = read_json(repo / R16A_READ_MODEL)
    r16a_production_senses = {
        composition_id: sorted({
            crosswalk_by_label[vocab_by_id[value]["canonical_label"]]["canonical_resolution_sense_id"]
            for value in row["node_ids"]
        })
        for composition_id, row in r16a_model["compositions"].items()
    }
    added_source_ids = {
        "ROUND16_VOCABULARY_REPRESENTATION": {row["vocabulary_id"] for row in r16_model["vocabulary"]},
        "ROUND16_ASSOCIATION_REPRESENTATION": {row["association_id"] for row in r16_model["associations"]},
        "ROUND16_CATEGORY_REPRESENTATION": {row["category_id"] for row in r16_model["categories"]},
        "ROUND16_SOURCE_INVENTORY_ENTRY": set(r16_model["source_inventory"]),
        "ROUND16_FAILED_ASSOCIATION_AUDIT": {row["association_id"] for row in r16_model["failed_associations_audit_only"]},
        "ROUND16_STATE_HASH_INDEX": set(r16_model["states_by_hash"]),
        "ROUND16_CAPABILITY_FIELD": set(r16_model["capabilities"]),
        "ROUND16_DATABASE_AUTHORITY_FIELD": set(r16_model["database"]),
        "ROUND16A_LEGACY_RECONCILIATION": {row["legacy_composition_id"] for row in registry["round16_legacy_reconciliation"]},
        "ROUND16A_VOCABULARY_REPRESENTATION": {row["vocabulary_id"] for row in r16a_model["vocabulary"]},
        "ROUND16A_ASSOCIATION_REPRESENTATION": {row["association_id"] for row in r16a_model["associations"]},
        "ROUND16A_CATEGORY_REPRESENTATION": {row["category_entry_id"] for row in r16a_model["categories"]},
        "ROUND16A_STATE_HASH_INDEX": set(r16a_model["states_by_hash"]),
        "ROUND16A_TRANSITION_DESCRIPTOR_FIELD": set(r16a_model["transitions"]),
        "ROUND16A_CAPABILITY_FIELD": set(r16a_model["capabilities"]),
        "ROUND16A_DATABASE_AUTHORITY_FIELD": set(r16a_model["database"]),
    }
    require(
        "ADDED_NO_LOSS_SOURCE_ID_SETS_EXACT",
        all(set(prior_ids_by_type[object_type]) == identifiers for object_type, identifiers in added_source_ids.items()),
        {key: len(value) for key, value in added_source_ids.items()},
    )
    prior_by_key = {(row["prior_object_type"], row["prior_id"]): row for row in prior_rows}
    added_row_failures: list[str] = []

    def verify_added_prior(
        object_type: str,
        prior_id: str,
        source_record_ref: str,
        *,
        senses: list[str] | None = None,
        parent_ids: list[str] | None = None,
        association_ids: list[str] | None = None,
        prior_status: str,
    ) -> None:
        row = prior_by_key[(object_type, prior_id)]
        if not (
            row["source_record_ref"] == source_record_ref
            and json.loads(row["participant_sense_ids_json"]) == sorted(set(senses or []))
            and json.loads(row["prior_parent_ids_json"]) == sorted(parent_ids or [])
            and json.loads(row["prior_association_ids_json"]) == sorted(association_ids or [])
            and row["prior_topology"] == ""
            and row["prior_status"] == prior_status
        ):
            added_row_failures.append(f"{object_type}:{prior_id}")

    for row in r16_model["vocabulary"]:
        vocabulary_id = row["vocabulary_id"]
        verify_added_prior(
            "ROUND16_VOCABULARY_REPRESENTATION", vocabulary_id, f"vocabulary/{vocabulary_id}",
            senses=[crosswalk_by_label[vocab_by_id[vocabulary_id]["canonical_label"]]["canonical_resolution_sense_id"]],
            prior_status=row["activation_status"],
        )
    for row in r16_model["associations"]:
        association_id = row["association_id"]
        verify_added_prior(
            "ROUND16_ASSOCIATION_REPRESENTATION", association_id, f"associations/{association_id}",
            senses=[crosswalk_by_label[vocab_by_id[value]["canonical_label"]]["canonical_resolution_sense_id"] for value in row["endpoint_vocabulary_ids"]],
            association_ids=[association_id], prior_status=row["support_status"],
        )
    for row in r16_model["categories"]:
        category_id = row["category_id"]
        verify_added_prior(
            "ROUND16_CATEGORY_REPRESENTATION", category_id, f"categories/{category_id}",
            parent_ids=[row["map_id"]], prior_status="V1_CATEGORY_REPRESENTATION",
        )
    for key, value in r16_model["source_inventory"].items():
        verify_added_prior("ROUND16_SOURCE_INVENTORY_ENTRY", key, f"source_inventory/{key}", prior_status=f"PATH:{value}")
    for row in r16_model["failed_associations_audit_only"]:
        association_id = row["association_id"]
        verify_added_prior(
            "ROUND16_FAILED_ASSOCIATION_AUDIT", association_id, f"failed_associations_audit_only/{association_id}",
            senses=[crosswalk_by_label[label]["canonical_resolution_sense_id"] for label in row["endpoint_labels"]],
            association_ids=[association_id],
            prior_status=f"{row['support_status']}:HARD_NEGATIVE={str(row['hard_negative']).lower()}",
        )
    for state_hash, state_id in r16_model["states_by_hash"].items():
        composition_id = r16_model["states"][state_id]["selected_composition_id"]
        verify_added_prior(
            "ROUND16_STATE_HASH_INDEX", state_hash, f"states_by_hash/{state_hash}",
            senses=r16_composition_senses[composition_id], parent_ids=[state_id, composition_id],
            prior_status="V1_STATE_HASH_INDEX",
        )
    for key, value in r16_model["capabilities"].items():
        verify_added_prior(
            "ROUND16_CAPABILITY_FIELD", key, f"capabilities/{key}",
            prior_status=f"CONTENT_SHA256:{sha256_text(canonical_json(value))}",
        )
    for key, value in r16_model["database"].items():
        verify_added_prior(
            "ROUND16_DATABASE_AUTHORITY_FIELD", key, f"database/{key}",
            prior_status=f"CONTENT_SHA256:{sha256_text(canonical_json(value))}",
        )
    for row in registry["round16_legacy_reconciliation"]:
        legacy_id = row["legacy_composition_id"]
        verify_added_prior(
            "ROUND16A_LEGACY_RECONCILIATION", legacy_id, legacy_id,
            senses=r16_composition_senses[legacy_id],
            parent_ids=[row["round16a_composition_id"]] if row["round16a_composition_id"] else [],
            prior_status=f"{row['disposition']}:{row['reason']}",
        )
    for row in r16a_model["vocabulary"]:
        vocabulary_id = row["vocabulary_id"]
        verify_added_prior(
            "ROUND16A_VOCABULARY_REPRESENTATION", vocabulary_id, f"vocabulary/{vocabulary_id}",
            senses=[crosswalk_by_label[vocab_by_id[vocabulary_id]["canonical_label"]]["canonical_resolution_sense_id"]],
            prior_status=row["activation_status"],
        )
    for row in r16a_model["associations"]:
        association_id = row["association_id"]
        verify_added_prior(
            "ROUND16A_ASSOCIATION_REPRESENTATION", association_id, f"associations/{association_id}",
            senses=[crosswalk_by_label[vocab_by_id[value]["canonical_label"]]["canonical_resolution_sense_id"] for value in row["endpoint_vocabulary_ids"]],
            association_ids=[association_id], prior_status=row["support_status"],
        )
    registry_categories_by_id = {row["category_entry_id"]: row for row in registry["category_entries"]}
    for row in r16a_model["categories"]:
        category_entry_id = row["category_entry_id"]
        authority = registry_categories_by_id[category_entry_id]
        verify_added_prior(
            "ROUND16A_CATEGORY_REPRESENTATION", category_entry_id, f"categories/{category_entry_id}",
            senses=[crosswalk_by_label[vocab_by_id[value]["canonical_label"]]["canonical_resolution_sense_id"] for value in authority["node_ids"]],
            parent_ids=row["composition_ids"] + [row["initial_state_id"]],
            association_ids=authority["association_ids"], prior_status=row["category_id"],
        )
    for state_hash, state_id in r16a_model["states_by_hash"].items():
        composition_id = r16a_model["states"][state_id]["composition_id"]
        verify_added_prior(
            "ROUND16A_STATE_HASH_INDEX", state_hash, f"states_by_hash/{state_hash}",
            senses=r16a_production_senses[composition_id], parent_ids=[state_id, composition_id],
            prior_status="V2_STATE_HASH_INDEX",
        )
    for key, value in r16a_model["transitions"].items():
        verify_added_prior(
            "ROUND16A_TRANSITION_DESCRIPTOR_FIELD", key, f"transitions/{key}",
            prior_status=f"CONTENT_SHA256:{sha256_text(canonical_json(value))}",
        )
    for key, value in r16a_model["capabilities"].items():
        verify_added_prior(
            "ROUND16A_CAPABILITY_FIELD", key, f"capabilities/{key}",
            prior_status=f"CONTENT_SHA256:{sha256_text(canonical_json(value))}",
        )
    for key, value in r16a_model["database"].items():
        verify_added_prior(
            "ROUND16A_DATABASE_AUTHORITY_FIELD", key, f"database/{key}",
            prior_status=f"CONTENT_SHA256:{sha256_text(canonical_json(value))}",
        )
    require("ADDED_NO_LOSS_ROWS_MATCH_SOURCE_SEMANTICS", not added_row_failures, added_row_failures[:20])
    require("ROUND16_DERIVED_COUNTS", (len(r16_model["maps"]), len(r16_model["trees"]), len(r16_model["states"]), len(r16_model["transitions"]), len(r16_model["workflows"]), len(r16_model["export_manifests"])) == (4, 26, 52, 816, 5, 104))
    enumeration = read_tsv(repo / R16A_ENUMERATION)
    rejections = read_tsv(repo / R16A_REJECTIONS)
    require("ROUND16A_ENUMERATION_COMPLETE", len(registry["association_subgraphs"]) == 58 and len(registry["round15_adapter_records"]) == 58 and len(enumeration) == 348)
    enum_decisions = Counter(row["decision"] for row in enumeration)
    require("ROUND16A_VALID_INVALID_COUNTS", enum_decisions == {"VALID": 81, "INVALID": 267} and len(rejections) == 277, enum_decisions)
    invalid_keys = {(row["association_subgraph_id"], row["topology_family"]) for row in enumeration if row["decision"] == "INVALID"}
    rejected_invalid_keys = {(row["association_subgraph_id"], row["topology_family"]) for row in rejections if row["decision"] == "INVALID"}
    require("INVALID_ENUMERATION_REJECTION_SET_EXACT", invalid_keys == rejected_invalid_keys and len(invalid_keys) == 267)
    require("TOPOLOGY_DISTRIBUTIONS_EXACT", Counter(row["topology_family"] for row in registry["topology_compositions"]) == {"LINEAR_PATH": 45, "BINARY_FORK": 18, "BINARY_CONVERGENCE": 18})
    require("CATEGORY_DISTRIBUTION_EXACT", Counter(row["category_id"] for row in registry["category_entries"]) == {"region": 25, "theme": 48, "medium": 2, "movement": 6})
    seed_ids = {seed["seed_id"] for row in registry["topology_compositions"] for seed in row["seed_variants"]}
    model = r16a_model
    production_ids = set(model["compositions"])
    entry_production_ids = {value for row in registry["category_entries"] for value in row["production_composition_ids"]}
    require("SEED_AND_PRODUCTION_BIJECTION_COUNTS", len(seed_ids) == len(production_ids) == 228 and production_ids == entry_production_ids)
    production_arity = Counter(len(row["node_ids"]) for row in model["compositions"].values())
    require("PRODUCTION_ARITY_DISTRIBUTION", production_arity == {2: 42, 3: 162, 4: 24}, production_arity)

    # State/workflow/export and transition reconstruction, including per-PCOMP commitments.
    states = read_tsv(repo / R16A_STATES)
    workflows = read_tsv(repo / R16A_WORKFLOWS)
    exports = read_tsv(repo / R16A_EXPORTS)
    state_by_id = {row["state_id"]: row for row in states}
    states_by_comp: dict[str, list[str]] = defaultdict(list)
    workflows_by_comp: dict[str, list[str]] = defaultdict(list)
    exports_by_comp: dict[str, list[str]] = defaultdict(list)
    for row in states: states_by_comp[row["composition_id"]].append(row["state_id"])
    for row in workflows: workflows_by_comp[row["composition_id"]].append(row["workflow_id"])
    for row in exports: exports_by_comp[row["composition_id"]].append(row["export_variant_id"])
    require("STATE_FORMULA_ALL_COMPOSITIONS", all(len(states_by_comp[key]) == len(value["node_ids"]) * 2 ** len(value["node_ids"]) for key, value in model["compositions"].items()))
    require("WORKFLOW_TARGET_STATE_BIJECTION", {row["target_state_id"] for row in workflows} == set(state_by_id) and len(workflows) == len(states) == 5760)
    export_per_state = Counter(row["state_id"] for row in exports)
    require("EXACTLY_TWO_EXPORTS_PER_STATE", len(exports) == 11520 and set(export_per_state) == set(state_by_id) and set(export_per_state.values()) == {2})

    transition_count = 0
    transition_digest = hashlib.sha256()
    previous = ""
    action_counts: Counter[str] = Counter()
    transition_counts_by_comp: Counter[str] = Counter()
    transition_digests_by_comp = {key: hashlib.sha256() for key in production_ids}
    transition_failures: list[str] = []
    with (repo / R16A_TRANSITIONS).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, dialect="excel-tab"):
            transition_id = row["transition_id"]
            if previous and transition_id <= previous:
                transition_failures.append("order")
            current = state_by_id.get(row["current_state_id"])
            following = state_by_id.get(row["next_state_id"])
            if not current or not following or current["state_hash"] != row["current_state_hash"] or following["state_hash"] != row["next_state_hash"]:
                transition_failures.append(transition_id)
            if row["executed"] != "true" or row["passed"] != "true" or row["state_mutated"] != "false":
                transition_failures.append(f"flags:{transition_id}")
            composition_id = current["composition_id"] if current else ""
            transition_digest.update(transition_id.encode()); transition_digest.update(b"\n")
            if composition_id:
                transition_counts_by_comp[composition_id] += 1
                transition_digests_by_comp[composition_id].update(transition_id.encode())
                transition_digests_by_comp[composition_id].update(b"\n")
            action_counts[row["action"]] += 1
            previous = transition_id
            transition_count += 1
    require("TRANSITION_GLOBAL_COMMITMENT", transition_count == 749944 and transition_digest.hexdigest() == EXPECTED_MANIFEST["ROUND16A_TRANSITION"][1])
    require("TRANSITION_REFERENCES_AND_FLAGS", not transition_failures, transition_failures[:20])
    require("TRANSITION_ACTION_DISTRIBUTION", action_counts == {"SELECT_CATEGORY": 23040, "FOCUS_NODE": 18480, "EXPAND_NODE": 8112, "COLLAPSE_NODE": 9240, "MOVE_FOCUS": 7824, "SELECT_COMPOSITION": 671728, "RESET_CATEGORY": 5760, "EXPORT_CURRENT_STATE": 5760}, action_counts)
    descendant_by_comp = {row["production_composition_id"]: row for row in descendants}
    require("PRODUCTION_DESCENDANT_IDS_EXACT", len(descendant_by_comp) == len(descendants) == 228 and set(descendant_by_comp) == production_ids)
    descendant_failures = []
    for composition_id in production_ids:
        row = descendant_by_comp.get(composition_id)
        if not row:
            descendant_failures.append(f"missing:{composition_id}")
            continue
        expected = (
            len(states_by_comp[composition_id]), id_hash(states_by_comp[composition_id]),
            transition_counts_by_comp[composition_id], transition_digests_by_comp[composition_id].hexdigest(),
            len(workflows_by_comp[composition_id]), id_hash(workflows_by_comp[composition_id]),
            len(exports_by_comp[composition_id]), id_hash(exports_by_comp[composition_id]),
        )
        actual = (
            int(row["state_count"]), row["state_id_set_sha256"],
            int(row["transition_count_by_current_state"]), row["transition_id_set_sha256"],
            int(row["workflow_count"]), row["workflow_id_set_sha256"],
            int(row["export_count"]), row["export_id_set_sha256"],
        )
        production_senses = tuple(sorted({
            crosswalk_by_label[vocab_by_id[value]["canonical_label"]]["canonical_resolution_sense_id"]
            for value in model["compositions"][composition_id]["node_ids"]
        }))
        linked_candidate_id = family_id_by_senses.get(production_senses, "") if len(production_senses) >= 3 else ""
        expected_candidate_ids = [linked_candidate_id] if linked_candidate_id else []
        if (
            expected != actual
            or int(row["participant_arity"]) != len(production_senses)
            or json.loads(row["round16b_candidate_ids_json"]) != expected_candidate_ids
            or row["partition_status"] != "COMPLETE_PENDING_ROUND16B_REGENERATION"
            or row["semantic_carry_forward_authorized"] != "false"
        ):
            descendant_failures.append(composition_id)
    require("PRODUCTION_DESCENDANT_PARTITIONS_EXACT", len(descendants) == 228 and not descendant_failures, descendant_failures[:20])

    # Receipt hashes, honesty boundary, and implementation independence.
    require("BUILD_OUTPUT_KEY_SET_EXACT", set(receipt["output_sha256"]) == EXPECTED_OUTPUT_NAMES, sorted(receipt["output_sha256"]))
    output_failures = [name for name, digest in receipt["output_sha256"].items() if sha256_file(raw / name) != digest]
    require("BUILD_OUTPUT_HASHES_EXACT", not output_failures, output_failures)
    require(
        "BUILD_RECEIPT_COUNTS_EXACT",
        receipt["crosswalk_record_count"] == 65
        and receipt["trigger_occurrence_count"] == 348
        and receipt["local_candidate_family_count"] == 31
        and receipt["open_participant_resolution_queue_count"] == 10
        and receipt["isolated_active_vocabulary_count"] == 5
        and receipt["prior_row_exact_reconciliation_object_count"] == 32135
        and receipt["prior_transition_set_count"] == 749944
        and receipt["prior_artifact_file_count"] == 1464
        and receipt["prior_artifact_namespace_count"] == 16
        and receipt["input_manifest_record_count"] == 34
        and receipt["method_surface_count"] == 44
        and receipt["selected_method_surface_count"] == 23
        and receipt["deferred_method_surface_count"] == 21
        and receipt["method_surface_disposition_distribution"] == dict(sorted(expected_disposition_counts.items()))
        and receipt["status"] == "PASS_WITH_OPEN_RESEARCH_BLOCKERS",
    )
    require("NO_HISTORY_OR_FORCE_OR_CLOSURE_CLAIM", receipt["history_rewritten"] is False and receipt["force_push_used"] is False and receipt["closure_claimed"] is False)
    require("CENSUS_ALL_CLOSURES_FALSE", set(census["closure"]) == EXPECTED_CLOSURE_KEYS and all(value is False for value in census["closure"].values()) and census["active_candidate_family_count"] == 0 and census["evidence_review_complete_candidate_count"] == 0 and census["global_coherence_pass_candidate_count"] == 0)
    require("OPEN_BLOCKERS_PRESERVED", census["open_blockers"] == EXPECTED_OPEN_BLOCKERS and census["candidate_universe_status"] == "INITIAL_LOCAL_LOWER_BOUND_NOT_CLOSED")
    require(
        "IMPLEMENTED_SELECTOR_BOUNDARY_REJECTS_CANDIDATE_UNIVERSE_CLOSURE",
        census["semantic_boundary"]
        == "These are participant-set review families emitted by the implemented local selectors, not a complete trigger universe, governed associations, evidence dispositions, or product-active facts."
        and census["candidate_universe_status"] == "INITIAL_LOCAL_LOWER_BOUND_NOT_CLOSED"
        and receipt["closure_claimed"] is False,
    )
    expected_census_candidates: list[dict[str, Any]] = []
    for row in families:
        expected_census_candidates.append({
            "candidate_id": row["candidate_id"],
            "candidate_object_kind": row["candidate_object_kind"],
            "participant_set_key": row["participant_set_key"],
            "participant_sense_ids": json.loads(row["participant_sense_ids_json"]),
            "canonical_labels": json.loads(row["canonical_labels_json"]),
            "arity": int(row["arity"]),
            "order_semantics": row["order_semantics"],
            "role_semantics": row["role_semantics"],
            "scope_resolution_status": row["scope_resolution_status"],
            "case_resolution_status": row["case_resolution_status"],
            "trigger_occurrence_ids": json.loads(row["trigger_occurrence_ids_json"]),
            "trigger_ids": json.loads(row["trigger_ids_json"]),
            "participant_eligibility": row["participant_eligibility"],
            "lifecycle_state": row["lifecycle_state"],
            "proposed_disposition": row["proposed_disposition"],
            "evidence_review_status": row["evidence_review_status"],
            "global_coherence_status": row["global_coherence_status"],
            "product_eligibility": row["product_eligibility"],
            "association_identity_frozen": row["association_identity_frozen"].lower() == "true",
            "family_content_sha256": row["family_content_sha256"],
        })
    expected_census_candidates.sort(key=lambda row: row["candidate_id"])
    actual_census_candidates = sorted(census["candidates"], key=lambda row: row["candidate_id"])
    require("CENSUS_CANDIDATE_OBJECTS_MATCH_LEDGER", actual_census_candidates == expected_census_candidates)
    census_metrics_exact = (
        census["format"] == "trace-round16b-local-candidate-census-v1"
        and census["status"] == "PASS_WITH_OPEN_RESEARCH_BLOCKERS"
        and census["selector_version"] == SELECTOR_VERSION
        and census["semantic_boundary"] == "These are participant-set review families emitted by the implemented local selectors, not a complete trigger universe, governed associations, evidence dispositions, or product-active facts."
        and census["crosswalk_record_count"] == len(crosswalk)
        and census["crosswalk_disposition_distribution"] == dict(sorted(disposition_counts.items()))
        and census["input_surface_count"] == len(input_manifest)
        and census["trigger_occurrence_count"] == len(occurrences)
        and census["trigger_occurrence_distribution"] == dict(sorted(Counter(row["trigger_class"] for row in occurrences).items()))
        and census["local_candidate_family_count"] == len(families)
        and census["candidate_arity_distribution"] == dict(sorted(Counter(row["arity"] for row in families).items()))
        and census["control_only_candidate_family_count"] == Counter(row["participant_eligibility"] for row in families)["CONTROL_ONLY_REJECTED_PARTICIPANT"]
        and census["open_participant_resolution_queue_count"] == len(open_roles)
        and census["isolated_active_vocabulary_count"] == len(isolated)
        and census["isolated_active_vocabulary_proven_composable_count"] == sum(row["higher_order_composability_proven"] == "true" for row in isolated)
        and census["prior_row_exact_reconciliation_object_count"] == len(prior_rows)
        and census["prior_row_exact_reconciliation_distribution"] == dict(sorted(prior_distribution.items()))
        and census["prior_transition_set_count"] == transition_count
        and census["prior_transition_set_sha256"] == transition_digest.hexdigest()
        and census["prior_artifact_file_count"] == len(prior_artifact_files) == 1464
        and census["prior_artifact_namespace_count"] == len(PRIOR_ARTIFACT_NAMESPACES) == 16
        and census["method_surface_count"] == len(surface_dispositions) == 44
        and census["selected_method_surface_count"] == selected_method_surface_count == 23
        and census["deferred_method_surface_count"] == deferred_method_surface_count == 21
        and census["method_surface_disposition_distribution"] == dict(sorted(surface_disposition_counts.items()))
    )
    require("CENSUS_METRICS_MATCH_ALL_LEDGER_TOTALS", census_metrics_exact)
    verifier_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imports = {alias.name for node in ast.walk(verifier_tree) if isinstance(node, ast.Import) for alias in node.names} | {node.module or "" for node in ast.walk(verifier_tree) if isinstance(node, ast.ImportFrom)}
    require("VERIFIER_DOES_NOT_IMPORT_GENERATOR", "build_local_candidate_census" not in imports and "scripts.trace_round16b.build_local_candidate_census" not in imports)
    require("GENERATOR_AND_VERIFIER_DISTINCT", (repo / "scripts/trace_round16b/build_local_candidate_census.py").resolve() != Path(__file__).resolve())

    result = {
        "format": "trace-round16b-local-candidate-independent-verification-v1",
        "source_sha": SOURCE_SHA,
        "source_tree": SOURCE_TREE,
        "parent_checkpoint_sha": PARENT_SHA,
        "status": "PASS" if not failures else "FAIL",
        "check_count": len(checks),
        "failure_count": len(failures),
        "failure_codes": failures,
        "crosswalk_record_count": len(crosswalk),
        "trigger_occurrence_count": len(occurrences),
        "candidate_family_count": len(families),
        "open_role_queue_count": len(open_roles),
        "isolated_active_count": len(isolated),
        "prior_row_exact_count": len(prior_rows),
        "prior_transition_set_count": transition_count,
        "prior_artifact_file_count": len(prior_artifact_files),
        "prior_artifact_namespace_count": len(namespace_counts),
        "method_surface_count": len(surface_dispositions),
        "selected_method_surface_count": selected_method_surface_count,
        "deferred_method_surface_count": deferred_method_surface_count,
        "closure_claimed": False,
        "checks": checks,
    }
    output = args.output if args.output.is_absolute() else repo / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ["status", "check_count", "failure_count", "failure_codes"]}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
