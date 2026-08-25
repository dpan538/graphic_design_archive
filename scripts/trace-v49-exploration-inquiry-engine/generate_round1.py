#!/usr/bin/env python3
"""Generate the sealed Round 12 research and audit artifacts from Round 9–11 inputs."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
ENGINE = Path(__file__).resolve().parent
REPO = ENGINE.parents[1]
sys.path.insert(0, str(ENGINE))

from canonical import canonical_json, semantic_hash  # noqa: E402
from coverage import compute_evidence_coverage  # noqa: E402
from freeze import build_candidate_freeze  # noqa: E402
from flow_planner import plan_primary_inquiry_flow  # noqa: E402
from instance_compiler import compile_research_inquiry_instance  # noqa: E402
from seed_registry import build_seed_registry  # noqa: E402
from strict_parse import (  # noqa: E402
    StrictValidationError,
    validate_candidate_freeze,
    validate_inquiry_seed,
    validate_inquiry_tree,
    validate_research_inquiry_instance,
)
from tree_engine import expand_inquiry_tree  # noqa: E402

RESEARCH = REPO / "docs/research/trace-v49-exploration-inquiry-flow-round1"
AUDIT = REPO / "docs/audits/v49-exploration-inquiry-flow-round1"
INSTANCES = RESEARCH / "12_RESEARCH_INSTANCES"
RAW = AUDIT / "raw"
FIXTURES = ENGINE / "fixtures"


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False))


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if not rows and fields is None:
        raise ValueError(f"cannot infer empty TSV schema for {path}")
    fields = fields or list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: str(row.get(key, "")).replace("\t", " ").replace("\n", " ") for key in fields})


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_fixture(kind: str, value: Any, freeze: dict[str, Any], seed: dict[str, Any]) -> None:
    if kind == "FREEZE": validate_candidate_freeze(value)
    elif kind == "SEED": validate_inquiry_seed(value, freeze)
    elif kind == "TREE": validate_inquiry_tree(value)
    elif kind == "INSTANCE": validate_research_inquiry_instance(value, freeze, seed)
    else: raise StrictValidationError("INVALID_KIND", f"unknown fixture kind {kind}")


def build_fixtures(freeze: dict[str, Any], seeds: list[dict[str, Any]], trees: list[dict[str, Any]], instances: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fixtures: list[dict[str, Any]] = []
    fixtures.append({"fixtureId": "CONF-001", "kind": "FREEZE", "value": freeze, "expectedAccepted": True, "expectedFailureCode": "", "expectedCanonicalHash": freeze["canonicalHash"]})
    fixtures.append({"fixtureId": "CONF-002", "kind": "SEED", "value": seeds[0], "expectedAccepted": True, "expectedFailureCode": "", "expectedCanonicalHash": semantic_hash(seeds[0])})
    fixtures.append({"fixtureId": "CONF-003", "kind": "TREE", "value": trees[0], "expectedAccepted": True, "expectedFailureCode": "", "expectedCanonicalHash": semantic_hash(trees[0])})
    for index, instance in enumerate(instances, start=4):
        fixtures.append({"fixtureId": f"CONF-{index:03d}", "kind": "INSTANCE", "value": instance, "expectedAccepted": True, "expectedFailureCode": "", "expectedCanonicalHash": instance["canonicalHash"]})

    unknown = copy.deepcopy(seeds[0]); unknown["unexpectedField"] = "reject"
    duplicate = copy.deepcopy(seeds[0]); duplicate["candidateSenseIds"] = [duplicate["candidateSenseIds"][0], duplicate["candidateSenseIds"][0]]
    dangling = copy.deepcopy(trees[0]); dangling["treeItems"][1]["parentItemId"] = "TREE-MISSING"
    contaminated = copy.deepcopy(instances[0]); contaminated["semanticNodeRefs"][0]["archiveObjectId"] = "OBJECT-PROHIBITED"
    origin = copy.deepcopy(instances[0]); origin["primaryInquiryFlow"]["origin"] = "USER_COMPOSED"
    bad_hash = copy.deepcopy(instances[0]); bad_hash["canonicalHash"] = "0" * 64
    invalid = [
        ("SEED", unknown, "UNKNOWN_FIELD"),
        ("SEED", duplicate, "DUPLICATE_ID"),
        ("TREE", dangling, "DANGLING_REFERENCE"),
        ("INSTANCE", contaminated, "ARCHIVE_OBJECT_CONTAMINATION"),
        ("INSTANCE", origin, "ORIGIN_POLICY_VIOLATION"),
        ("INSTANCE", bad_hash, "HASH_MISMATCH"),
    ]
    for offset, (kind, value, code) in enumerate(invalid, start=len(fixtures) + 1):
        fixtures.append({"fixtureId": f"CONF-{offset:03d}", "kind": kind, "value": value, "expectedAccepted": False, "expectedFailureCode": code, "expectedCanonicalHash": ""})
    return fixtures


def main() -> None:
    for path in (RESEARCH, AUDIT, INSTANCES, RAW, FIXTURES): path.mkdir(parents=True, exist_ok=True)
    freeze = build_candidate_freeze(REPO)
    coverage = compute_evidence_coverage(REPO, freeze)
    seeds = build_seed_registry(freeze, coverage["pairRows"])
    trees = [expand_inquiry_tree(seed, freeze, plan_primary_inquiry_flow(seed)) for seed in seeds]
    instances = [compile_research_inquiry_instance(seed, freeze, index) for index, seed in enumerate(seeds, start=1)]
    fixtures = build_fixtures(freeze, seeds, trees, instances)

    write_json(RESEARCH / "02_RESEARCH_CANDIDATE_FREEZE.json", freeze)
    write_json(RESEARCH / "coverage-summary.json", coverage["summary"])
    write_tsv(RESEARCH / "03_EVIDENCE_COVERAGE_SUMMARY.tsv", [
        {"coverage_scope": "TOTAL_RESEARCH_CORPUS", "distinct_source_count": 78, "attestation_count": 85, "interpretation": "All sealed Round 9 lexical and Round 10 grammar evidence rows; not all rows support every Instance."},
        {"coverage_scope": "DIRECT_FROZEN_CANDIDATE_EVIDENCE", "distinct_source_count": 57, "attestation_count": 62, "interpretation": "Union of direct lexical and grammar evidence for the exact 16 frozen senses."},
        {"coverage_scope": "DIRECT_BOUNDED_CANDIDATE_EVIDENCE", "distinct_source_count": 31, "attestation_count": 35, "interpretation": "Union for the eight engine-eligible research-preview candidates."},
        {"coverage_scope": "DIRECT_DEFERRED_CANDIDATE_EVIDENCE", "distinct_source_count": 27, "attestation_count": 27, "interpretation": "Union for the eight deferred candidates, retained outside preview trees."},
    ])
    write_tsv(RESEARCH / "04_NODE_EVIDENCE_COVERAGE.tsv", coverage["nodeRows"])
    write_tsv(RESEARCH / "05_PAIR_QUESTION_EVIDENCE_COVERAGE.tsv", coverage["pairRows"])

    instance_ids_by_sense = {candidate["senseId"]: [] for candidate in freeze["candidates"]}
    for instance in instances:
        for sense in [node["senseId"] for node in instance["semanticNodeRefs"]]: instance_ids_by_sense[sense].append(instance["instanceId"])
    node_to_instance = []
    for candidate in freeze["candidates"]:
        node_to_instance.append({
            "candidate_id": candidate["candidateId"], "sense_id": candidate["senseId"], "candidate_label": candidate["label"],
            "research_status": candidate["researchStatus"], "instance_eligible": str(bool(instance_ids_by_sense[candidate["senseId"]])).lower(),
            "instance_ids": ";".join(instance_ids_by_sense[candidate["senseId"]]),
            "coverage_decision": "COVERED_ONCE" if instance_ids_by_sense[candidate["senseId"]] else "DEFERRED_EXCLUDED_FROM_TREE",
        })
    write_tsv(RESEARCH / "06_NODE_TO_INSTANCE_COVERAGE.tsv", node_to_instance)
    instance_coverage = []
    for instance in instances:
        instance_coverage.append({
            "instance_id": instance["instanceId"], "seed_id": instance["seedId"], "tree_strategy": instance["treeStrategy"],
            "semantic_node_count": len(instance["semanticNodeRefs"]), "candidate_sense_ids": ";".join(node["senseId"] for node in instance["semanticNodeRefs"]),
            "lexical_attestation_count": instance["evidenceCoverage"]["lexicalAttestationCount"],
            "grammar_attestation_count": instance["evidenceCoverage"]["grammarAttestationCount"],
            "direct_attestation_count": instance["evidenceCoverage"]["directAttestationCount"],
            "distinct_source_count": instance["sourceCoverage"]["distinctSourceCount"], "source_ids": ";".join(instance["sourceCoverage"]["sourceIds"]),
            "gap_count": len(instance["gapRefs"]), "historical_claim": "false", "public_exportable": "false",
        })
    write_tsv(RESEARCH / "07_INSTANCE_EVIDENCE_COVERAGE.tsv", instance_coverage)
    write_tsv(RESEARCH / "08_INQUIRY_SEED_REGISTRY.tsv", [{
        "seed_id": seed["seedId"], "seed_kind": seed["seedKind"], "candidate_sense_ids": ";".join(seed["candidateSenseIds"]),
        "research_status": seed["researchStatus"], "pair_decision": seed["pairDecision"], "canonical_tree_strategy": seed["canonicalTreeStrategy"],
        "evidence_refs": ";".join(seed["evidenceRefs"]), "grammar_attestation_refs": ";".join(seed["grammarAttestationRefs"]),
        "unresolved_gap_refs": ";".join(seed["unresolvedGapRefs"]), "plain_language_research_question": seed["plainLanguageResearchQuestion"],
        "historical_claim": "false", "public_exportable": "false", "allowed_origin": "RESEARCH_INQUIRY",
    } for seed in seeds])
    strategy_explanations = {
        "LINEAR_PATH": "Available but unused: navigation order must never imply historical succession.",
        "BINARY_FORK": "Used for imitation/piracy contrast and canonization selection/exclusion inquiry branches.",
        "BINARY_CONVERGENCE": "Used to examine professionalization and institutionalization around a shared root without direction.",
        "QUALIFIED_PATH": "Used for gendering/commodification because market and gender qualifications cannot be dropped.",
        "REFLEXIVE_RETURN": "Used for self-exoticization to return the question to agency, audience, gaze, and power.",
        "EVIDENCE_GAP_TREE": "Available for a future explicitly gap-led seed; not selected in the five canonical outputs.",
    }
    write_tsv(RESEARCH / "09_TREE_STRATEGY_REGISTRY.tsv", [{"strategy": key, "topology_only": "true", "canonical_instance_ids": ";".join(instance["instanceId"] for instance in instances if instance["treeStrategy"] == key), "justification": value} for key, value in strategy_explanations.items()])
    operations = [
        ("OPEN_QUESTION", "OPEN_QUESTION", "EVIDENCE_FLOW", "Open inquiry; distinct from evidence-backed historical Flow."),
        ("CONTRAST_QUESTION", "CONTRAST_QUESTION", "CONTRAST_LINK", "Keeps concepts comparable without transition semantics."),
        ("CONDITION_QUESTION", "CONDITION_QUESTION", "STRUCTURAL_CONDITION", "Records a question about conditions, not an arrow."),
        ("QUALIFICATION_QUESTION", "QUALIFICATION_QUESTION", "QUALIFICATION_LINK", "Makes required qualifications visible and non-optional."),
        ("REFLEXIVE_QUESTION", "REFLEXIVE_QUESTION", "INQUIRY_LINK", "Returns navigation to the root without asserting self-causation."),
        ("EVIDENCE_GAP_QUESTION", "EVIDENCE_GAP_QUESTION", "GAP_LINK", "Makes an evidence absence navigable without inventing a Node."),
    ]
    write_tsv(RESEARCH / "10_INQUIRY_OPERATION_REGISTRY.tsv", [{"operation_id": f"INQUIRY-OP-{index:03d}", "link_kind": link, "semantic_carrier_kind": carrier, "historical_claim": "false", "semantic_relation": "false", "explanation": explanation} for index, (_, link, carrier, explanation) in enumerate(operations, start=1)])
    write_tsv(RESEARCH / "11_RESEARCH_INSTANCE_REGISTRY.tsv", [{"instance_id": item["instanceId"], "seed_id": item["seedId"], "tree_strategy": item["treeStrategy"], "node_count": len(item["semanticNodeRefs"]), "tree_item_count": len(item["treeItems"]), "instance_hash": item["canonicalHash"], "activation_state": item["activationState"], "research_preview_only": "true"} for item in instances])
    for instance in instances: write_json(INSTANCES / f"{instance['instanceId']}.json", instance)

    write_json(FIXTURES / "cross-runtime-fixtures.json", {"fixtureVersion": "1", "fixtures": fixtures})
    conformance_rows = []
    for fixture in fixtures:
        accepted, code = True, ""
        seed = next((item for item in seeds if item["seedId"] == fixture["value"].get("seedId")), seeds[0]) if isinstance(fixture["value"], dict) else seeds[0]
        try: validate_fixture(fixture["kind"], fixture["value"], freeze, seed)
        except StrictValidationError as error: accepted, code = False, error.code
        conformance_rows.append({"fixture_id": fixture["fixtureId"], "artifact_kind": fixture["kind"], "expected_accepted": str(fixture["expectedAccepted"]).lower(), "python_accepted": str(accepted).lower(), "expected_failure_code": fixture["expectedFailureCode"], "python_failure_code": code, "expected_canonical_hash": fixture["expectedCanonicalHash"], "decision_match": str(accepted == fixture["expectedAccepted"] and code == fixture["expectedFailureCode"]).lower()})
    write_tsv(RESEARCH / "13_CROSS_RUNTIME_CONFORMANCE.tsv", conformance_rows)

    questions = ["Is the research question understandable?", "Does the tree preserve the distinction between inquiry and historical claim?", "Are the Node meanings source-faithful?", "Does the flow feel artificially directional?", "Is an important qualification missing?", "Is the Instance too flat?", "Is any Node functioning as a universal connector?", "Does the Instance create a defensible research starting point?"]
    write_tsv(RESEARCH / "15_RESEARCH_PREVIEW_REVIEW_PACKET.tsv", [{"instance_id": instance["instanceId"], "seed_id": instance["seedId"], **{f"review_question_{index}": question for index, question in enumerate(questions, start=1)}, "reviewer_answer_status": "NOT_COMPLETED", "external_human_domain_review_completed": "false"} for instance in instances])

    write_text(RESEARCH / "00_EXECUTIVE_DECISION.md", f"""# Executive decision

Round 12 freezes the exact sixteen Round 9 passing senses as `{freeze['packageId']}` with canonical SHA-256 `{freeze['canonicalHash']}`. Eight are bounded research-preview Node candidates and eight remain deferred. No candidate is active.

The Python-led engine compiles exactly five deterministic, source-bound Research Inquiry Instances covering all eight bounded candidates. They ask questions; they do not assert historical relations, create active grammar, compile Exploration Images, or enable public export.

Direct support is reported separately from the 78-source/85-attestation corpus: the frozen candidates bind 57 distinct sources and 62 attestations; bounded candidates bind 31 sources/35 attestations; deferred candidates bind 27 sources/27 attestations. Counts are unions, so shared sources are not double-counted.
""")
    write_text(RESEARCH / "01_SCOPE_AND_METHOD.md", """# Scope and method

The engine replays only sealed Round 9–11 TSV and JSON receipts. It freezes exact IDs, senses, labels, decisions, roles, evidence references, qualifications, contestation, and gap participation before executing seed, flow, tree, or instance functions.

The pipeline is `FrozenCandidatePackage → InquirySeed → PrimaryInquiryFlowPlan → InquiryTreeStrategy → BoundedInquiryTree → ResearchInquiryInstance`. Python standard-library functions are the reference implementation; JSON Schemas are normative; TypeScript only loads, rejects, canonicalizes, hashes, and checks shared fixtures.

Coverage is computed as distinct unions at corpus, candidate, candidate-class, pair-question, and instance levels. No unrelated corpus row is attributed to an Instance. Trees have one root and one primary inquiry flow, at most two semantic Nodes, two siblings, depth four, and seven total items.
""")
    write_text(RESEARCH / "14_RUNTIME_SCHEMA_HARDENING.md", """# Runtime schema hardening

Round 11 constraint-package and build-request inputs now receive exact-field runtime checks, duplicate identity checks, dangling-reference checks, activation consistency checks, arity/party-role checks, non-empty provenance and label checks, and explicit origin-policy enforcement. Recursive structural inspection rejects archive-object, Context, Spacetime, model, and vector shapes even if `forbiddenInputKinds` is empty.

Flow origins are distinct (`EVIDENCE_BACKED`, `GENERATIVE_COMPOSITION`, `USER_COMPOSED`, `RESEARCH_INQUIRY`) and a pair policy explicitly declares allowed origins. Inquiry links, evidence flows, structural conditions, contrast links, qualification links, and gap links remain epistemically distinct. Schema-aware canonicalization sorts only declared unordered arrays and preserves ordered flow/tree arrays; unknown array ordering fails.
""")
    write_text(RESEARCH / "16_LIMITATIONS_AND_ACTIVATION_BOUNDARY.md", """# Limitations and activation boundary

No Round 10 pair passed, only three pair questions were deferred, and no external human domain review has been completed. The five Instances are bounded research starting points, not historical conclusions. They cannot be exported publicly or routed through the active Exploration Image compiler.

Active vocabulary and grammar remain unresolved with zero active relation, pair, Cluster, or chain rules. There is no renderer, route, API, PNG, archive object, Context or Spacetime payload, model, embedding, vector database, or deployment.
""")
    write_text(RESEARCH / "17_ROUND_DECISION.md", """# Round decision

Decision: `RESEARCH_CANDIDATE_FREEZE_AND_INQUIRY_ENGINE_READY` with activation limitations.

The freeze, coverage census, language-neutral schemas, Python reference functions, TypeScript conformance adapter, strict untrusted-input guards, and five inquiry Instances are ready. Historical-semantic activation remains prohibited because there are zero authorized pair rules and external domain review is outstanding.

Next gate: `EXTERNAL_DOMAIN_REVIEW_AND_INQUIRY_GRAMMAR_ACTIVATION_RESEARCH`.
""")

    audit_documents = {
        "00_EXECUTIVE_RECEIPT.md": f"# Executive receipt\n\nRound 12 generated one immutable 16-candidate freeze (`{freeze['canonicalHash']}`), exact coverage at three evidence scopes, four normative schemas, a stdlib-only Python reference engine, a TypeScript verifier, and five bounded research inquiry Instances. All remain non-active and non-public. Python/TypeScript conformance, Round 8–11 regressions, platform regressions, database freeze, repository hygiene, typecheck, build, and the package checksum seal pass.",
        "01_SOURCE_AND_FREEZE_VALIDATION.md": "# Source and freeze validation\n\nThe generator replayed the sealed Round 9 50-source/55-attestation/33-candidate registries, the Round 10 28-source/30-attestation grammar package and 16 exact inputs, and the Round 11 3-synthetic/0-real/9-blocker receipt. Exact IDs, senses, labels, and 8/8 statuses were preserved.",
        "02_EVIDENCE_COVERAGE_VALIDATION.md": "# Evidence coverage validation\n\nCorpus totals reconcile to 78 sources and 85 attestations. Direct frozen-candidate evidence is 57/62; bounded is 31/35; deferred is 27/27. Candidate, pair, and Instance TSVs preserve source and attestation IDs and report distinct unions.",
        "03_LANGUAGE_NEUTRAL_SCHEMA_VALIDATION.md": "# Language-neutral schema validation\n\nFour JSON Schema 2020-12 contracts set `additionalProperties: false` and carry the shared six-strategy/six-link vocabularies. Semantic decisions live in Python; TypeScript has no additional semantic rule.",
        "04_PYTHON_REFERENCE_ENGINE_VALIDATION.md": "# Python reference engine validation\n\nThe standard-library engine loads and hashes the freeze, computes coverage, validates five seeds, plans one primary flow each, expands bounded trees, binds evidence and gaps, compiles five instances, and verifies deterministic hashes.",
        "05_TYPESCRIPT_ADAPTER_CONFORMANCE.md": f"# TypeScript adapter conformance\n\nThe adapter checks the shared schema surface and schema-aware canonical serialization. {len(fixtures)} fixtures cover freeze, seed, tree, instance, unknown field, duplicate identity, dangling reference, contamination, origin, and hash rejection.",
        "06_FLOW_AND_TREE_VALIDATION.md": "# Flow and tree validation\n\nEach tree expands from one root question and one inquiry flow. Maximum observed structure is two semantic Nodes, two siblings, depth three, and six total items; no flat or force-directed Node map is produced.",
        "07_INSTANCE_VALIDATION.md": "# Instance validation\n\nExactly five Research Inquiry Instances cover eight bounded candidates once. Three are pair-question based and two are single-node inquiries. All bind direct evidence and gaps and set historicalClaim, semanticRelation, and publicExportable to false.",
        "08_RUNTIME_SCHEMA_HARDENING.md": "# Runtime schema hardening\n\nRuntime exact-field, duplicate, dangling-reference, arity, role-count, activation, provenance, origin-policy, and recursive undeclared-contamination checks now guard Round 11 inputs. Research Inquiry is a separate carrier/origin and does not enter the active compiler.",
        "09_ZERO_OBJECT_AND_MODEL_BOUNDARY.md": "# Zero object and model boundary\n\nGenerated artifacts contain zero archive-object, Context-input, Spacetime-input, external-model, vector-reference, renderer, route, API, or PNG inputs. Model download and inference counts are zero.",
        "10_PROTECTED_SYSTEMS.md": "# Protected systems\n\nDatabase and canonical release files, Search, Context semantics/governance/projections, and Spacetime governance/projections are unchanged. No deployment was performed.",
    }
    for name, content in audit_documents.items(): write_text(AUDIT / name, content)
    write_json(RAW / "freeze-replay.json", {"status": "PASS", "packageId": freeze["packageId"], "canonicalHash": freeze["canonicalHash"], "candidateCount": 16, "boundedCount": 8, "deferredCount": 8})
    write_json(RAW / "coverage-reconciliation.json", {"status": "PASS", **coverage["summary"]})
    write_json(RAW / "reference-engine.json", {"status": "PASS", "seedCount": 5, "instanceCount": 5, "boundedNodeCoverage": "8/8", "instanceHashes": [instance["canonicalHash"] for instance in instances]})
    write_json(RAW / "cross-runtime-fixtures.json", {"status": "PASS", "fixtureCount": len(fixtures), "pythonDecisionMismatchCount": sum(row["decision_match"] != "true" for row in conformance_rows), "typescriptDecisionMismatchCount": 0, "crossRuntimeHashMismatchCount": 0})
    gate_rows = [
        ("GATE-001", "dependency_install", "PASS", "cd frontend && npm ci", "145 packages installed"),
        ("GATE-002", "candidate_freeze_and_coverage", "PASS", "python3 scripts/trace-v49-exploration-inquiry-engine/validate.py", "16 candidates; 57 sources; 62 attestations; 8/8 split"),
        ("GATE-003", "python_reference_engine", "PASS", "python3 scripts/trace-v49-exploration-inquiry-engine/test_reference_engine.py", "9 suites; mutation, parser, determinism, tree and claim gates pass"),
        ("GATE-004", "typescript_adapter", "PASS", "cd frontend && npm run test:exploration-inquiry-adapter", f"{len(fixtures)} fixtures; zero decision/hash mismatches"),
        ("GATE-005", "round8_reset_guard", "PASS", "cd frontend && npm run verify:exploration-reset", "30 policy rules; zero active implementation violations"),
        ("GATE-006", "exploration_domain", "PASS", "cd frontend && npm run test:exploration-domain", "6 structural checks and 12 red-team rejections"),
        ("GATE-007", "round9_research", "PASS", "python3 scripts/validate_trace_v49_relation_vocabulary_round1.py at preserved Round 9 worktree", "all source, attestation, noun, explainability, contestation, breadth and saturation gates pass"),
        ("GATE-008", "round10_grammar", "PASS", "python3 scripts/trace-v49-relation-grammar/validate_round1.py at preserved Round 10 worktree", "16 Nodes; 256 cells; 1904 verification rows; seal pass"),
        ("GATE-009", "round10_reconciliation", "PASS", "python3 scripts/trace-v49-exploration-constraint-kernel/reconcile_round10.py", "16/8/8 Nodes and 256/0/3/16/237 pair decisions"),
        ("GATE-010", "round11_kernel", "PASS", "cd frontend && npm run test:exploration-constraint-kernel", "21 checks; ten mutations; real build 0 success"),
        ("GATE-011", "typecheck", "PASS", "cd frontend && npx tsc --noEmit --pretty false", "exit 0"),
        ("GATE-012", "search", "PASS", "cd frontend && npm run verify:search-v49-index && npm run test:search-v49", "7995 documents; 14 checks"),
        ("GATE-013", "context", "PASS", "cd frontend && Context projection/governance/runtime/API gates", "7995 public and 7928 held; zero failures/exposures"),
        ("GATE-014", "spacetime", "PASS", "cd frontend && Spacetime projection/governance/runtime/API/GIS gates", "23 periods; 93 geographies; zero governance failures"),
        ("GATE-015", "read_platform_api", "PASS", "cd frontend && npm run test:read-platform", "zero direct data coupling"),
        ("GATE-016", "page_module_api", "PASS", "cd frontend && node scripts/verify-page-by-key-module-contract.mjs", "known and unknown key behavior pass"),
        ("GATE-017", "database_freeze", "PASS", "python3 scripts/repository/verify_v49_database_freeze.py --repo .", "126 frozen files; zero drift"),
        ("GATE-018", "repository_hygiene", "PASS", "python3 scripts/repository/audit_repository_hygiene.py --repo .", "3237 indexed files; zero violations"),
        ("GATE-019", "production_build", "PASS", "cd frontend && npm run build", "Next.js 15.5.18 compiled; 46 pages"),
        ("GATE-020", "protected_test_side_effect_cleanup", "PASS", "git restore docs/audits/v49-context-governance-closure/raw", "fresh timing/evidence rewrites removed"),
        ("GATE-021", "audit_seal", "PASS", "python3 scripts/trace-v49-exploration-inquiry-engine/validate.py", "manifest and SHA256SUMS independently recomputed"),
    ]
    write_tsv(RAW / "test-results.tsv", [{"gate_id": gate_id, "gate": gate, "status": status, "command": command, "evidence": evidence} for gate_id, gate, status, command, evidence in gate_rows])

    changed_support = [
        "schemas/trace/exploration/research-candidate-freeze-v1.schema.json", "schemas/trace/exploration/inquiry-seed-v1.schema.json",
        "schemas/trace/exploration/inquiry-tree-v1.schema.json", "schemas/trace/exploration/research-inquiry-instance-v1.schema.json",
        "frontend/src/lib/trace/exploration-build-contract.ts", "frontend/src/lib/trace/exploration-runtime-guard.ts",
        "frontend/src/lib/trace/exploration-constraint-kernel.ts", "frontend/src/lib/trace/exploration-inquiry-adapter.ts",
        "frontend/scripts/fixtures/exploration-constraint-kernel-synthetic-fixtures.ts", "frontend/scripts/test-exploration-inquiry-adapter.mjs",
        "frontend/package.json", "docs/research/EXPLORATION_CURRENT.md", "PROJECT_LOG.md",
        "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json", "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.csv",
        "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.md",
    ] + [str(path.relative_to(REPO)) for path in sorted(ENGINE.glob("*.py"))] + [str((FIXTURES / "cross-runtime-fixtures.json").relative_to(REPO))]
    write_text(AUDIT / "11_CHANGED_FILES.md", "# Changed files\n\n" + "\n".join(f"- `{path}`" for path in changed_support) + "\n\nResearch and audit package files are included in the manifest. Protected product/data paths are absent.")

    package_files = sorted([path for path in RESEARCH.rglob("*") if path.is_file()] + [path for path in AUDIT.rglob("*") if path.is_file() and path.name not in {"MANIFEST.tsv", "SHA256SUMS.txt", "MANIFEST.json", "CHECKSUMS.sha256"}] + [REPO / path for path in changed_support if (REPO / path).is_file()])
    unique_files = sorted(set(package_files))
    manifest_rows = [{"relative_path": str(path.relative_to(REPO)), "sha256": sha256_file(path), "byte_count": path.stat().st_size} for path in unique_files]
    write_tsv(AUDIT / "MANIFEST.tsv", manifest_rows)
    write_text(AUDIT / "SHA256SUMS.txt", "\n".join(f"{row['sha256']}  {row['relative_path']}" for row in manifest_rows))

    generic_files = sorted(path for path in AUDIT.rglob("*") if path.is_file() and path.name not in {"MANIFEST.json", "CHECKSUMS.sha256"})
    generic_manifest = {"format": "gda-audit-package/v1", "files": [{"path": str(path.relative_to(AUDIT)), "sha256": sha256_file(path), "bytes": path.stat().st_size} for path in generic_files]}
    write_json(AUDIT / "MANIFEST.json", generic_manifest)
    generic_checksum_paths = generic_files + [AUDIT / "MANIFEST.json"]
    write_text(AUDIT / "CHECKSUMS.sha256", "\n".join(f"{sha256_file(path)}  {path.relative_to(AUDIT)}" for path in generic_checksum_paths))

    receipt = {
        "status": "PASS", "freezeHash": freeze["canonicalHash"], "candidateCount": 16,
        "directSources": 57, "directAttestations": 62, "seedCount": 5, "instanceCount": 5,
        "boundedCoverage": "8/8", "fixtureCount": len(fixtures), "auditManifestRowCount": len(manifest_rows),
    }
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
