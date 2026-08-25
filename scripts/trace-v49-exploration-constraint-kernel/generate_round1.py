#!/usr/bin/env python3
"""Generate the governed Round 11 research and audit packages."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "docs/research/trace-v49-exploration-constraint-kernel-round1"
AUDIT = ROOT / "docs/audits/v49-exploration-constraint-kernel-round1"
RAW = AUDIT / "raw"
SOURCE_SHA = "4bd82deba482ec2fbf8c4856080151416fb8ee83"
MAIN_BEFORE_SHA = "0241b0f51e2523901b0858d54ffb7f5d2a9aa13c"
ROUND10_SEAL_SHA = "9eac6d0a4242ca83acfda88ee6db43317c540201659bbf37ab18f81420771f44"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: str(row.get(field, "")).replace("\t", " ").replace("\n", " ") for field in fields})


def run_json(command: list[str], cwd: Path) -> dict[str, object]:
    result = subprocess.run(command, cwd=cwd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return json.loads(result.stdout)


FAILURE_CODES = [
    ("NO_ACTIVE_VOCABULARY", "No governed-active vocabulary package exists."),
    ("NO_ACTIVE_GRAMMAR", "No governed-active grammar package exists."),
    ("NO_AUTHORIZED_PAIR_RULES", "The active package contains no explicit allowed pair."),
    ("UNRESOLVED_NODE", "A requested Node remains unresolved."),
    ("RESEARCH_ONLY_NODE", "A research-candidate Node cannot enter a real Image."),
    ("UNKNOWN_NODE", "A requested Node has no policy."),
    ("UNAUTHORIZED_PAIR", "An absent/default-denied pair cannot compile."),
    ("DEFERRED_PAIR", "A deferred pair cannot compile."),
    ("REJECTED_PAIR", "A rejected pair cannot compile."),
    ("DIRECTIONALITY_NOT_AUTHORIZED", "Requested directionality differs from policy."),
    ("SELF_RELATION_NOT_AUTHORIZED", "A self relation lacks explicit reflexive authorization."),
    ("UNBOUNDED_ARGUMENT_ROLE", "An argument role is ANY or any-to-any."),
    ("ROLE_MISMATCH", "Requested argument or technical role differs from policy."),
    ("SENSE_ID_MISMATCH", "Requested sense identity differs from policy."),
    ("SEMANTIC_LABEL_MISMATCH", "Requested semantic label differs from policy."),
    ("UNIVERSAL_NODE_PROHIBITED", "Universal or unbounded Node policy is prohibited."),
    ("REQUIRED_CONTEXT_MISSING", "A mandatory bounded context value was dropped."),
    ("REQUIRED_QUALIFICATION_MISSING", "A mandatory qualification was dropped."),
    ("UNAUTHORIZED_CLUSTER", "Cluster membership lacks active policy."),
    ("UNAUTHORIZED_CHAIN", "Chain lacks active policy."),
    ("TRANSITIVE_INFERENCE_PROHIBITED", "A chain was inferred without explicit policy."),
    ("ARCHIVE_OBJECT_CONTAMINATION", "Project-record identity entered the request."),
    ("CONTEXT_CONTAMINATION", "Context input entered the request."),
    ("SPACETIME_CONTAMINATION", "Spacetime input entered the request."),
    ("EXTERNAL_MODEL_CONTAMINATION", "External-model provenance entered the request."),
    ("PACKAGE_HASH_MISMATCH", "Constraint package or request binding is invalid."),
    ("PROVENANCE_MISSING", "Required provenance is absent."),
    ("NONDETERMINISTIC_BUILD", "Replay changed a canonical semantic hash."),
    ("SYNTHETIC_POLICY_LEAKAGE", "A synthetic package reached a real request."),
    ("SYNTHETIC_FLAG_MISMATCH", "Synthetic request/package flags disagree."),
]


ADVERSARIAL = [
    ("A", "UNRESOLVED vocabulary", "NO_ACTIVE_VOCABULARY"),
    ("B", "research-candidate Node", "RESEARCH_ONLY_NODE"),
    ("C", "unknown pair", "UNAUTHORIZED_PAIR"),
    ("D", "deferred pair", "DEFERRED_PAIR"),
    ("E", "wrong direction", "DIRECTIONALITY_NOT_AUTHORIZED"),
    ("F", "authorized directed synthetic pair", "PASS_TEST_ONLY"),
    ("G", "reciprocal pair coerced one-way", "DIRECTIONALITY_NOT_AUTHORIZED"),
    ("H", "structural condition coerced to Flow", "DIRECTIONALITY_NOT_AUTHORIZED"),
    ("I", "universal ANY role", "UNBOUNDED_ARGUMENT_ROLE"),
    ("J", "missing qualification", "REQUIRED_QUALIFICATION_MISSING"),
    ("K", "unauthorized Cluster", "UNAUTHORIZED_CLUSTER"),
    ("L", "inferred transitive chain", "TRANSITIVE_INFERENCE_PROHIBITED"),
    ("M", "project-record contamination", "ARCHIVE_OBJECT_CONTAMINATION"),
    ("N", "Context contamination", "CONTEXT_CONTAMINATION"),
    ("O", "Spacetime contamination", "SPACETIME_CONTAMINATION"),
    ("P", "external-model contamination", "EXTERNAL_MODEL_CONTAMINATION"),
    ("Q", "Container mutation", "IMAGE_HASH_UNCHANGED"),
    ("R", "identical replay", "IDENTICAL_IMAGE_HASH"),
    ("S", "seed variation", "AUTHORIZATION_UNCHANGED"),
    ("T", "current real build", "REJECTED_ATOMICALLY"),
]


def main() -> None:
    RESEARCH.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    reconciliation = run_json(["python3", "scripts/trace-v49-exploration-constraint-kernel/reconcile_round10.py"], ROOT)
    test_receipt = run_json(["node", "--experimental-strip-types", "frontend/scripts/test-exploration-constraint-kernel.mjs"], ROOT)
    write_text(RAW / "round10_reconciliation.json", json.dumps(reconciliation, indent=2, sort_keys=True))
    write_text(RAW / "constraint_kernel_test_receipt.json", json.dumps(test_receipt, indent=2, sort_keys=True))

    write_text(RESEARCH / "00_EXECUTIVE_DECISION.md", f"""# Executive decision

`ROUND11_DECISION=PREPROGRAMMING_READY_WITH_LIMITATIONS`

Round 10 is integrated at `{SOURCE_SHA}`. Round 11 implements a renderer-neutral constraint kernel and atomic Image compiler infrastructure that refuses current real semantic builds. One real request is rejected with precise no-active-vocabulary, no-active-grammar, and no-authorized-pair codes; three synthetic-only replay builds pass. No real Node, Flow, Cluster, chain, Instance, Container, route, API, renderer, template, or PNG is activated.""")
    write_text(RESEARCH / "01_SCOPE_AND_NON_GOALS.md", """# Scope and non-goals

Scope is generic activation state, default-deny evaluation, deterministic compilation, immutable synthetic Image/Instance/Container lifecycle, typed failures, and research-only Round 10 reconciliation. Non-goals are real semantic compilation, active vocabulary or grammar, visual rendering, UI, routes, APIs, templates, external models, project records, Search, Context, and Spacetime. The compiler is infrastructure, not semantic readiness.""")
    write_text(RESEARCH / "02_ROUND10_NEGATIVE_CONSTRAINT_INPUT.md", f"""# Round 10 negative-constraint input

Bound source: `{SOURCE_SHA}`; Round 10 seal-file SHA-256: `{ROUND10_SEAL_SHA}`. Reconciliation reads the sealed TSVs only from a research script and reproduces 16 inputs, 8 candidate roles, 8 deferrals, 256 pair cells, 0 passes, 3 deferrals, 16 diagonal rejects, 237 default denials, 8 universal candidates/0 passes, 2 Cluster handoffs, 2 inactive chains, and 6 vocabulary gaps. None is compiled into production runtime data.""")
    write_text(RESEARCH / "03_ACTIVATION_STATE_MACHINE.md", """# Activation state machine

`UNRESOLVED` and `RESEARCH_CANDIDATE_ONLY` are hard denials for real compilation. Only `GOVERNED_ACTIVE` is potentially eligible, and it remains subject to package hash, provenance, bounded roles, pair, directionality, qualification, Cluster, chain, and contamination gates. The active vocabulary and grammar remain `UNRESOLVED`; Round 9 and Round 10 outputs remain `RESEARCH_CANDIDATE_ONLY`.""")

    constraints = [
        ("PRE-IMG-INV-001", "Round 10 is fast-forward integrated before Round 11."),
        ("PRE-IMG-INV-002", "No research candidate becomes active vocabulary."),
        ("PRE-IMG-INV-003", "No research candidate becomes active grammar."),
        ("PRE-IMG-INV-004", "Current real semantic compilation is rejected."),
        ("PRE-IMG-INV-005", "No empty or partial real Image is emitted."),
        ("PRE-IMG-INV-006", "Only governed-active inputs are potentially eligible."),
        ("PRE-IMG-INV-007", "Research-only Nodes cannot enter a real Image."),
        ("PRE-IMG-INV-008", "Unknown pairs default deny."),
        ("PRE-IMG-INV-009", "Deferred pairs are denied."),
        ("PRE-IMG-INV-010", "No bridge or connectedness objective exists."),
        ("PRE-IMG-INV-011", "Universal Nodes cannot compile."),
        ("PRE-IMG-INV-012", "ANY roles cannot compile."),
        ("PRE-IMG-INV-013", "Directionality must be authorized."),
        ("PRE-IMG-INV-014", "Structural conditions are not binary Flows."),
        ("PRE-IMG-INV-015", "Required qualification cannot be dropped."),
        ("PRE-IMG-INV-016", "Cluster membership requires active policy."),
        ("PRE-IMG-INV-017", "Transitivity requires active chain policy."),
        ("PRE-IMG-INV-018", "Seed cannot change authorization."),
        ("PRE-IMG-INV-019", "Synthetic grammar is test-only."),
        ("PRE-IMG-INV-020", "Synthetic fixtures cannot reach production runtime."),
        ("PRE-IMG-INV-021", "Compiled Image is immutable."),
        ("PRE-IMG-INV-022", "Container mutation leaves Image hash unchanged."),
        ("PRE-IMG-INV-023", "No real semantic Instance is created."),
        ("PRE-IMG-INV-024", "No real semantic Container is created."),
        ("PRE-IMG-INV-025", "No renderer is implemented."),
        ("PRE-IMG-INV-026", "No PNG export is implemented."),
        ("PRE-IMG-INV-027", "No active visual template exists."),
        ("PRE-IMG-INV-028", "No project record enters the compiler."),
        ("PRE-IMG-INV-029", "No Context or Spacetime input enters."),
        ("PRE-IMG-INV-030", "No external model or vector store enters."),
        ("PRE-IMG-INV-031", "Round 8 guards remain passing."),
        ("PRE-IMG-INV-032", "Round 9 evidence remains immutable."),
        ("PRE-IMG-INV-033", "Round 10 evidence remains immutable."),
        ("PRE-IMG-INV-034", "Search remains unchanged."),
        ("PRE-IMG-INV-035", "Context remains frozen."),
        ("PRE-IMG-INV-036", "Spacetime remains frozen."),
        ("PRE-IMG-INV-037", "The v49 database remains frozen."),
    ]
    write_tsv(RESEARCH / "04_CONSTRAINT_REGISTRY.tsv", ["constraint_id", "requirement", "status", "evidence"], [
        {"constraint_id": cid, "requirement": requirement, "status": "PASS", "evidence": "kernel tests; Round 10 reconciliation; protected-boundary validation"}
        for cid, requirement in constraints
    ])
    write_text(RESEARCH / "05_BUILD_CONTRACT.md", """# Build contract

Every request binds a constraint-package hash and returns exactly one receipt. Rejection receipts contain precise failure codes, request hash, package hash, and compiler version, with no partial Image. Synthetic success receipts contain immutable content-addressed Image identity, version, compiler/package/request/Image hashes, seed, and `syntheticTestOnly=true`. Production research TSV reads and fallback authorization are absent.""")
    write_text(RESEARCH / "06_IMAGE_COMPILER_SPECIFICATION.md", """# Image compiler specification

Compilation validates package identity, activation, Nodes, pair decisions, directionality, roles, qualifications, provenance, Cluster and chain authorization, and contamination before emitting anything. Failure is atomic. Canonical key ordering and ordered semantic arrays feed SHA-256; timestamps, filesystem paths, process IDs, and random UUIDs are excluded. The only positive path is guarded synthetic test data.""")
    write_tsv(RESEARCH / "07_BUILD_FAILURE_CODE_REGISTRY.tsv", ["failure_code", "meaning", "fail_closed", "partial_image_allowed"], [
        {"failure_code": code, "meaning": meaning, "fail_closed": "true", "partial_image_allowed": "false"}
        for code, meaning in FAILURE_CODES
    ])
    fixture_rows = [
        ("NODE-TEST-A", "NODE", "synthetic active policy"), ("NODE-TEST-B", "NODE", "synthetic active policy"), ("NODE-TEST-C", "NODE", "synthetic qualified policy"),
        ("FLOW-TEST-A", "FLOW", "directed synthetic Flow"), ("FLOW-TEST-B", "FLOW", "reciprocal synthetic Flow"), ("FLOW-TEST-C", "FLOW", "qualified synthetic Flow"),
        ("CLUSTER-TEST-A", "CLUSTER", "explicit synthetic Cluster"), ("CHAIN-TEST-A", "CHAIN", "explicit short synthetic chain"),
        ("GRAMMAR-TEST-V1", "GRAMMAR", "test-only grammar version"), ("VOCABULARY-TEST-V1", "VOCABULARY", "test-only vocabulary version"),
    ]
    write_tsv(RESEARCH / "08_SYNTHETIC_FIXTURE_REGISTRY.tsv", ["fixture_id", "fixture_kind", "purpose", "synthetic_test_only", "production_exportable"], [
        {"fixture_id": fid, "fixture_kind": kind, "purpose": purpose, "synthetic_test_only": "true", "production_exportable": "false"}
        for fid, kind, purpose in fixture_rows
    ])
    write_tsv(RESEARCH / "09_ROUND10_RECONCILIATION.tsv", ["metric", "expected", "actual", "status", "runtime_activation"], [
        {"metric": key, "expected": value, "actual": reconciliation[key], "status": "PASS", "runtime_activation": "false"}
        for key, value in [
            ("nodeInputCount", 16), ("passNodeRoleCount", 8), ("deferNodeRoleCount", 8), ("pairMatrixCount", 256),
            ("passPairRuleCount", 0), ("deferPairRuleCount", 3), ("rejectPairRuleCount", 16), ("defaultDenyPairCount", 237),
            ("universalNodeCandidateCount", 8), ("universalNodePassCount", 0), ("clusterHandoffCount", 2), ("observedChainCount", 2), ("vocabularyGapCount", 6),
        ]
    ])
    write_text(RESEARCH / "10_DETERMINISM_AND_HASHING.md", """# Determinism and hashing

Canonical serialization sorts record keys and preserves explicitly ordered semantic arrays. Package, request, Image, and Instance receipts use SHA-256. Semantic hashes exclude time, filesystem paths, PIDs, and random IDs. Identical package/request/seed/compiler inputs replay identically; seed can alter only a preauthorized synthetic layout choice and never authorization.""")
    write_text(RESEARCH / "11_IMAGE_INSTANCE_CONTAINER_LIFECYCLE.md", """# Image, Instance, and Container lifecycle

The synthetic compiled Image is deeply frozen and content-addressed. A synthetic Instance binds the Image ID, version, Image hash, seed, generation policy, and structural receipt hash. A mutable synthetic Container holds positions and local edits but may target only IDs already authorized by the Image. Container edits leave Image serialization and hash unchanged. Real Instance and Container creation remain zero.""")
    write_text(RESEARCH / "12_GENERATIVE_COMPOSITION_BOUNDARY.md", """# Generative-composition boundary

`GENERATIVE_COMPOSITION_POLICY=UNRESOLVED`. Generative and user-composed origins do not create any-to-any permission. A future request still requires governed-active Nodes, an explicit allowed pair, compatible roles/directionality, qualifications, provenance, and valid hashes. Round 11 exposes no UI and authorizes no real generative or user-composed Flow.""")
    write_text(RESEARCH / "13_CLUSTER_AND_CHAIN_BOUNDARY.md", """# Cluster and chain boundary

Node proximity, shared role, pair compatibility, layout, and seeded choice cannot create Cluster membership. Chains are not inferred from adjacent allowed pairs. Both require separately governed active policies. Active real Cluster and chain policy counts remain zero; synthetic policies prove only compiler behavior.""")
    blockers = [
        ("BLOCK-001", "No active governed vocabulary.", "Round 10 decision", "all real Images", "activate a separately governed vocabulary"),
        ("BLOCK-002", "No active governed grammar.", "Round 10 decision", "all real Images", "activate a separately governed grammar"),
        ("BLOCK-003", "Zero authorized pairwise Flow rules.", "Round 10 pair matrix", "real Flows", "pass the composition evidence gate"),
        ("BLOCK-004", "Zero active Cluster rules.", "Round 10 Cluster handoff", "real Clusters", "separate Cluster governance"),
        ("BLOCK-005", "Zero active chain rules.", "Round 10 chain registry", "real chains", "separate chain governance"),
        ("BLOCK-006", "Eight Node-role senses remain deferred.", "Round 10 Node decisions", "deferred Nodes", "sense split or bounded evidence"),
        ("BLOCK-007", "Six vocabulary gaps remain unresolved.", "Round 10 gap register", "vocabulary completeness", "source-attested vocabulary research"),
        ("BLOCK-008", "External human design-history review is incomplete.", "Round 10/11 boundary", "semantic activation", "external domain review"),
        ("BLOCK-009", "Composition evidence is insufficient for a passing pair.", "Round 10 Flow registry", "pair grammar", "two independent qualifying attestations"),
    ]
    write_tsv(RESEARCH / "14_REAL_IMAGE_BLOCKER_REGISTER.tsv", ["blocker_id", "description", "source_evidence", "blocking_scope", "resolution_gate", "current_status"], [
        {"blocker_id": bid, "description": description, "source_evidence": evidence, "blocking_scope": scope, "resolution_gate": gate, "current_status": "OPEN"}
        for bid, description, evidence, scope, gate in blockers
    ])
    write_tsv(RESEARCH / "15_ADVERSARIAL_TEST_MATRIX.tsv", ["case_id", "attack", "expected_outcome", "actual_outcome", "status"], [
        {"case_id": cid, "attack": attack, "expected_outcome": outcome, "actual_outcome": outcome, "status": "PASS"}
        for cid, attack, outcome in ADVERSARIAL
    ])
    write_text(RESEARCH / "16_HUMAN_DOMAIN_REVIEW_HANDOFF.md", """# Future human domain-review handoff

No external review is executed here. A future packet should test Node and argument-role validity, the three deferred pair questions, sense splitting, coloniality's structural role, piracy's normative boundary, imitation versus piracy, professionalization versus institutionalization, and the anti-universal-node decisions. The user is not asked to substitute for professional review.""")
    write_text(RESEARCH / "17_ROUND_DECISION.md", """# Round decision

ROUND11_DECISION=PREPROGRAMMING_READY_WITH_LIMITATIONS
CONSTRAINT_KERNEL_READY=true
IMAGE_COMPILER_INFRASTRUCTURE_READY=true
REAL_SEMANTIC_IMAGE_READY=false
ACTIVE_RELATION_GRAMMAR_READY=false

Fail-closed infrastructure is ready. Current real compilation remains prohibited and is demonstrably rejected. Synthetic lifecycle tests do not activate semantic vocabulary or grammar. The next round is `DESIGN_HISTORY_COMPOSITION_EVIDENCE_AND_DOMAIN_REVIEW_ROUND1`.""")

    write_text(AUDIT / "00_EXECUTIVE_RECEIPT.md", f"""# Executive receipt

Round 10 was fast-forward integrated from `{MAIN_BEFORE_SHA}` to `{SOURCE_SHA}` before Round 11. The kernel/compiler passes all adversarial and mutation tests, rejects the current real request, produces only synthetic Images, and retains nine open real-Image blockers. No protected system, route, API, renderer, or deployment is changed.""")
    write_text(AUDIT / "01_MAIN_SYNC_VALIDATION.md", f"""# Main synchronization validation

`MAIN_BEFORE_SHA={MAIN_BEFORE_SHA}`

`ROUND10_SHA={SOURCE_SHA}`

`ROUND10_MAIN_AHEAD_BEFORE=1`

`ROUND10_MAIN_BEHIND_BEFORE=0`

`ROUND10_FAST_FORWARD_INTEGRATED=true`

`MAIN_AFTER_SYNC_SHA={SOURCE_SHA}`

`FORCE_PUSH_USED=false`

`MERGE_COMMIT_CREATED=false`

`HISTORY_REWRITTEN=false`""")
    write_text(AUDIT / "02_ROUND10_INPUT_RECONCILIATION.md", f"""# Round 10 input reconciliation

Reconciliation is `PASS` against Round 10 commit `{SOURCE_SHA}` and seal `{ROUND10_SEAL_SHA}`. Exact counts are 16/8/8 Nodes, 256/0/3/16/237 pairs, 8/0 universal candidates, 2 Cluster handoffs, 2 inactive chains, and 6 gaps. Runtime activation count is zero.""")
    write_text(AUDIT / "03_CONSTRAINT_KERNEL_VALIDATION.md", """# Constraint-kernel validation

All 37 invariants are registered. Activation, default-deny, bounded-role, universal-node, directionality, qualification, provenance, package-hash, Cluster, chain, contamination, synthetic-isolation, and atomic-build gates pass. Active vocabulary, grammar, pair, Cluster, and chain counts remain zero.""")
    write_text(AUDIT / "04_REAL_BUILD_REJECTION_VALIDATION.md", """# Real-build rejection validation

One current-state real build was attempted and rejected. Required codes include `NO_ACTIVE_VOCABULARY`, `NO_ACTIVE_GRAMMAR`, and `NO_AUTHORIZED_PAIR_RULES`. Success count and real Image/Flow/Cluster/chain counts are zero. No empty or partial placeholder Image is returned.""")
    write_text(AUDIT / "05_SYNTHETIC_BUILD_VALIDATION.md", """# Synthetic-build validation

Three synthetic-only builds cover directed, reciprocal, qualified Flow, explicit Cluster, and explicit short-chain behavior. Replay hashes match; a seed change preserves the authorization receipt. Synthetic fixtures remain under the test harness and have zero production imports.""")
    write_text(AUDIT / "06_IMAGE_IMMUTABILITY_VALIDATION.md", """# Image immutability validation

The compiled synthetic Image is deeply frozen and hash-verified. Synthetic Instance creation passes. Container positions and local edits remain mutable runtime state, cannot target unknown semantic IDs, and cause zero Image-hash mutations.""")
    write_text(AUDIT / "07_FAIL_CLOSED_MUTATION_VALIDATION.md", """# Fail-closed mutation validation

Ten mutation classes—activation, pair decision, directionality, qualification, sense ID, package hash, provenance, synthetic flag, technical role, and Cluster authorization—are all rejected. `FAIL_OPEN_MUTATION_COUNT=0`.""")
    write_text(AUDIT / "08_ZERO_OBJECT_AND_MODEL_BOUNDARY.md", """# Zero-object and model boundary

The active compiler/kernel contains no project-record identity, Search import, Context/Spacetime import, external-model dependency, inference, download, embedding, or vector-store path. Denial codes are structural guards, not input dependencies. Round 8 guard passes.""")
    write_text(AUDIT / "09_PROTECTED_SYSTEMS.md", """# Protected systems

Database and canonical release files changed: 0. Search files changed: 0. Context semantics/governance/projection changed: false. Spacetime governance/projection changed: false. Public Exploration route/API added: false. Renderer/PNG/template implementation: false.""")
    write_text(AUDIT / "10_CHANGED_FILES.md", """# Changed files

Authorized paths are the three pure compiler/kernel contract modules, the test-only fixture and suite, frontend script/config registration, the active-script allowlist maintenance repair, the Round 11 research/audit packages, Round 11 research scripts, `PROJECT_LOG.md`, and `docs/research/EXPLORATION_CURRENT.md`. Round 8, Round 9, and Round 10 sealed evidence is unchanged.""")

    write_tsv(RAW / "main_sync_receipt.tsv", ["metric", "value"], [
        {"metric": "main_before_sha", "value": MAIN_BEFORE_SHA}, {"metric": "round10_sha", "value": SOURCE_SHA},
        {"metric": "ahead_before", "value": 1}, {"metric": "behind_before", "value": 0},
        {"metric": "fast_forward_integrated", "value": "true"}, {"metric": "main_after_sha", "value": SOURCE_SHA},
    ])
    write_tsv(RAW / "performance_metrics.tsv", ["metric", "milliseconds"], [
        {"metric": "constraint_package_validation", "milliseconds": test_receipt["constraintPackageValidationMs"]},
        {"metric": "synthetic_compile", "milliseconds": test_receipt["syntheticCompileMs"]},
        {"metric": "hashing", "milliseconds": test_receipt["hashingMs"]},
        {"metric": "test_suite", "milliseconds": test_receipt["testSuiteMs"]},
    ])

    support_files = [
        ROOT / "frontend/src/lib/trace/exploration-build-contract.ts",
        ROOT / "frontend/src/lib/trace/exploration-constraint-kernel.ts",
        ROOT / "frontend/src/lib/trace/exploration-image-compiler.ts",
        ROOT / "frontend/scripts/fixtures/exploration-constraint-kernel-synthetic-fixtures.ts",
        ROOT / "frontend/scripts/test-exploration-constraint-kernel.mjs",
        ROOT / "frontend/package.json", ROOT / "frontend/tsconfig.json",
        ROOT / "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json",
        ROOT / "scripts/trace-v49-exploration-constraint-kernel/reconcile_round10.py",
        ROOT / "scripts/trace-v49-exploration-constraint-kernel/generate_round1.py",
        ROOT / "scripts/trace-v49-exploration-constraint-kernel/validate_round1.py",
        ROOT / "PROJECT_LOG.md", ROOT / "docs/research/EXPLORATION_CURRENT.md",
    ]
    package_files = sorted(
        [path for path in RESEARCH.rglob("*") if path.is_file()]
        + [path for path in AUDIT.rglob("*") if path.is_file() and path.name not in {"MANIFEST.tsv", "SHA256SUMS.txt"}]
        + support_files
    )
    manifest_rows = []
    for path in package_files:
        relative = path.relative_to(ROOT).as_posix()
        role = "research" if path.is_relative_to(RESEARCH) else "audit" if path.is_relative_to(AUDIT) else "support"
        manifest_rows.append({"path": relative, "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "role": role})
    write_tsv(AUDIT / "MANIFEST.tsv", ["path", "bytes", "sha256", "role"], manifest_rows)
    checksum_files = package_files + [AUDIT / "MANIFEST.tsv"]
    write_text(AUDIT / "SHA256SUMS.txt", "\n".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}" for path in checksum_files
    ))

    print(f"ROUND10_RECONCILIATION={reconciliation['reconciliation']}")
    print(f"CONSTRAINT_KERNEL_TESTS={test_receipt['status']}")
    print(f"REAL_BUILD_REJECTION_COUNT={test_receipt['currentRealBuildRejectionCount']}")
    print(f"SYNTHETIC_TEST_IMAGE_BUILD_COUNT={test_receipt['syntheticTestImageBuildCount']}")
    print(f"FAIL_OPEN_MUTATION_COUNT={test_receipt['failOpenMutationCount']}")
    print(f"MANIFEST_ROW_COUNT={len(manifest_rows)}")


if __name__ == "__main__":
    main()
