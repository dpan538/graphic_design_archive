#!/usr/bin/env python3
"""Build and verify the additive Round 16B clean-integration seal."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
AUDIT_DIR = REPO / "docs/audits/v49-exploration-round16b-main-integration"
LEDGER_PATH = AUDIT_DIR / "commit-description-ledger.v1.json"
MANIFEST_PATH = AUDIT_DIR / "clean-main-integration-manifest.v1.json"
MARKDOWN_PATH = AUDIT_DIR / "CLEAN_MAIN_INTEGRATION_SEAL.md"

BRANCH = "codex/trace-v49-round16b-evidence-bounded-main-integration"
OLD_MAIN = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e"
OLD_MAIN_TREE = "86c2ed7771034f6d3f0f2e10e7a37aeec0552c71"
RESEARCH_BRANCH = (
    "codex/trace-v49-exploration-higher-order-association-closure-round16b"
)
RESEARCH_SHA = "8c3588e422a3650b634693b409a9c0b13714d58f"
RESEARCH_TREE = "ae5db940828f0536a10f37607d6d1cf34de13dee"
EXPECTED_PRE_SEAL_COMMITS = [
    "c2735cac6f8f057e058f7b64c43de7bfd5c8595b",
    "196ed0100d644ca6d1a5bfe35ecfdb16de73d063",
    "8d7b09a9f68f6af8db04cec366fb0fe85f306d93",
    "289e37d2e8d6d0d08fe899c433fc59d933c4d4bc",
    "0ad349f2302ed1de74dc27d06961b73c0d0ed41b",
    "647219588f22d848f47a5e5c56889abc6fb965fd",
]

SELF_SUBJECT = "chore(integration): seal the clean Round 16B release package"
SELF_BODY = """Context:
The clean integration branch contains six verified release commits rooted directly at the unchanged old-main boundary. This seventh additive commit seals that lineage without rewriting the published Round 16B research history or modifying its historical seal.

Changes:
Add a deterministic integration manifest, a complete seven-entry commit-description ledger, a human-readable seal, and a builder/verifier. Bind the baseline import, public language, canonical Open Inquiry registry and API, complete TRACE API catalog, three-function tree, bounded frontend handoff, verification receipts, old-main identity, research-source identity, and preserved historical seal hashes.

Behavioral impact:
No runtime, API, database, validated topology, export, or frontend visual behavior changes. The release package gains an auditable integrity and commit-message boundary.

Evidence boundary:
The seal records an evidence-bounded functional baseline. It does not establish pair, higher-order, global-composition, product-reachability, computational-space, or Function 3 closure, and it does not turn Open Inquiry records into validated relations.

Verification:
Verified seven complete commit descriptions with zero title-only commits and zero missing required sections; exact old-main and research identities; the clean lineage merge base; all sealed artifact hashes; unchanged historical Round 16B seal hashes; clean integration isolation; deterministic handoff reconstruction; git diff --check; repository hygiene; Git/LFS integrity; and large-blob policy. The final commit identity is bound by an external postpublication receipt because a commit cannot embed its own object ID.

Compatibility and rollback:
This additive seal can be reverted independently without changing runtime behavior. The rollback boundary remains the annotated old-main identity at 8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e; creation of a remote rollback tag and any main update remain subject to the no-auto-deployment safety gate.

Round:
TRACE v49 Round 16B Clean Main Integration

Closure-claim:
evidence-bounded-nonclosure

Deployment:
none"""

REQUIRED_SECTIONS = [
    "Context:",
    "Changes:",
    "Behavioral impact:",
    "Evidence boundary:",
    "Verification:",
    "Compatibility and rollback:",
    "Round:",
    "Closure-claim:",
    "Deployment:",
]

ROLES = [
    "verified_round16b_baseline_import",
    "public_language_and_status_correction",
    "canonical_open_inquiry_registry_and_api",
    "complete_trace_api_catalog",
    "bounded_frontend_handoff",
    "integration_and_isolation_verification",
    "clean_integration_package_seal",
]

SEALED_GROUPS = {
    "clean_baseline_import": [
        "STALE_SESSION_RECOVERY_REPORT.md",
        "STALE_SESSION_RECOVERY_RECEIPT.json",
        "docs/audits/v49-exploration-round16b-main-integration/round16b-path-equivalence-ledger.v1.json",
        "docs/audits/v49-exploration-round16b-main-integration/verify_commit1_evidence.py",
    ],
    "public_language_and_status": [
        "README.md",
        "PROJECT_LOG.md",
        "docs/README.md",
        "docs/maintenance/DOCUMENTATION_MAP.md",
        "docs/releases/v49/AUDIT_INDEX.md",
        "docs/releases/v49/RELEASE_INDEX.md",
        "docs/research/EXPLORATION_CURRENT.md",
        "docs/research/trace-v49-exploration-round16b-main-integration/00_PUBLIC_LANGUAGE_AND_STATUS.md",
        "docs/audits/v49-exploration-round16b-main-integration/public-language-status-receipt.v1.json",
    ],
    "open_inquiry_registry_and_api": [
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/scoped-association-hypothesis-ledger-shard-1-v1.tsv",
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/scoped-association-hypothesis-ledger-shard-2-v1.tsv",
        "docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json",
        "frontend/generated/trace-open-inquiry-v1/open-inquiry-registry.v1.json",
        "frontend/src/app/api/trace/v1/open-inquiry/route.ts",
        "frontend/src/app/api/trace/v1/open-inquiry/[inquiryId]/route.ts",
        "frontend/src/features/trace-v49/open-inquiry-v1/controller.server.ts",
        "frontend/src/features/trace-v49/open-inquiry-v1/registry.server.ts",
        "frontend/src/features/trace-v49/open-inquiry-v1/service.server.ts",
        "frontend/src/features/trace-v49/open-inquiry-v1/types.ts",
        "frontend/scripts/test-trace-open-inquiry-v1.mjs",
        "schemas/trace/exploration/open-inquiry/v1/detail-response.schema.json",
        "schemas/trace/exploration/open-inquiry/v1/error.schema.json",
        "schemas/trace/exploration/open-inquiry/v1/list-response.schema.json",
        "schemas/trace/exploration/open-inquiry/v1/registry.schema.json",
        "scripts/trace_round16b_integration/build_open_inquiry_registry.py",
        "docs/audits/v49-exploration-round16b-main-integration/open-inquiry-registry-api-receipt.v1.json",
        "docs/research/trace-v49-exploration-round16b-main-integration/01_OPEN_INQUIRY_REGISTRY_AND_API.md",
    ],
    "trace_api_catalog": [
        "docs/api/trace/TRACE_API_CATALOG.md",
        "docs/api/trace/trace-api-catalog.v1.json",
        "docs/audits/v49-exploration-round16b-main-integration/build_trace_api_catalog.py",
        "docs/audits/v49-exploration-round16b-main-integration/trace-api-catalog-verification-receipt.v1.json",
    ],
    "trace_function_tree": [
        "docs/frontend/trace-v49-handoff/TRACE_FUNCTION_TREE.md",
        "docs/frontend/trace-v49-handoff/trace-function-tree.v1.json",
    ],
    "bounded_frontend_handoff": [
        "docs/audits/v49-exploration-round16b-main-integration/build_frontend_handoff.py",
        "docs/frontend/trace-v49-handoff/ACCESSIBILITY_AND_RESPONSIVE_CONSTRAINTS.md",
        "docs/frontend/trace-v49-handoff/DATA_CONTRACTS_AND_EXAMPLES.md",
        "docs/frontend/trace-v49-handoff/EXPORT_CONTRACT.md",
        "docs/frontend/trace-v49-handoff/FRONTEND_STATE_MATRIX.md",
        "docs/frontend/trace-v49-handoff/HANDOFF_INTEGRITY_REPORT.md",
        "docs/frontend/trace-v49-handoff/KNOWN_LIMITATIONS_AND_OPEN_DESIGN_QUESTIONS.md",
        "docs/frontend/trace-v49-handoff/NAVIGATION_AND_CROSS_FUNCTION_STATE.md",
        "docs/frontend/trace-v49-handoff/OPEN_INQUIRY_UX_CONTRACT.md",
        "docs/frontend/trace-v49-handoff/SOURCE_MANIFEST.json",
        "docs/frontend/trace-v49-handoff/START_HERE.md",
        "docs/frontend/trace-v49-handoff/TERMINOLOGY_AND_UI_COPY.md",
    ],
    "integration_verification": [
        "docs/audits/v49-exploration-round16b-main-integration/integration-isolation-verification-receipt.v1.json",
        "docs/audits/v49-exploration-round16b-main-integration/verify_clean_integration.py",
        "docs/research/trace-v49-exploration-round16b-main-integration/02_INTEGRATION_AND_ISOLATION_VERIFICATION.md",
        "frontend/scripts/validate-trace-open-inquiry-v1-http.mjs",
        "frontend/package.json",
    ],
    "historical_round16b_seal_unchanged": [
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/MANIFEST.json",
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/CHECKSUMS.sha256",
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/large-file-policy.json",
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/final-clean-reproduction-receipt-checkpoint016.json",
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/final-clean-reproduction-independent-verification-checkpoint016.json",
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/repository-hygiene-checkpoint016.json",
        "docs/research/trace-v49-exploration-higher-order-association-closure-round16b/31_FINAL_CLEAN_REPRODUCTION_AND_EVIDENCE_BOUNDED_NONCLOSURE.md",
        "docs/research/trace-v49-exploration-higher-order-association-closure-round16b/32_REPOSITORY_HYGIENE_CHECKPOINT016.md",
    ],
    "commit_description_ledger": [
        "docs/audits/v49-exploration-round16b-main-integration/build_clean_integration_seal.py",
        "docs/audits/v49-exploration-round16b-main-integration/commit-description-ledger.v1.json",
    ],
}

HISTORICAL_SEAL_SHA256 = {
    "docs/audits/v49-exploration-higher-order-association-closure-round16b/MANIFEST.json":
        "4f7a628985fa430ba2b819965574eabdb5ca3ffc81398fb48335289134bb02ee",
    "docs/audits/v49-exploration-higher-order-association-closure-round16b/CHECKSUMS.sha256":
        "fcc590dd500cb6b5d57e52411119aadbcd6f804116bab8a03c8a179365cd2bcf",
    "docs/audits/v49-exploration-higher-order-association-closure-round16b/large-file-policy.json":
        "3edb4ec79f7c7d06cf145aebdd86fadba915b6bd75040edb65507578d06b441c",
}


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    )
    return result.stdout.rstrip("\n")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def commit_record(commit_sha: str, ordinal: int) -> dict[str, object]:
    subject = git("show", "-s", "--format=%s", commit_sha)
    body = git("show", "-s", "--format=%b", commit_sha)
    missing = [section for section in REQUIRED_SECTIONS if section not in body]
    return {
        "ordinal": ordinal,
        "role": ROLES[ordinal - 1],
        "commit_sha": commit_sha,
        "subject": subject,
        "body": body,
        "subject_sha256": sha256(subject.encode("utf-8")),
        "body_sha256": sha256(body.encode("utf-8")),
        "title_only": not bool(body.strip()),
        "missing_required_sections": missing,
    }


def build_ledger() -> tuple[dict[str, object], list[str]]:
    failures: list[str] = []
    commits = git("rev-list", "--reverse", f"{OLD_MAIN}..HEAD").splitlines()
    if commits[:6] != EXPECTED_PRE_SEAL_COMMITS:
        failures.append("PRE_SEAL_COMMIT_IDENTITY_MISMATCH")
    if len(commits) not in (6, 7):
        failures.append("UNEXPECTED_CLEAN_INTEGRATION_COMMIT_COUNT")

    records = [commit_record(commit, index + 1) for index, commit in enumerate(commits[:6])]
    if len(commits) == 7:
        actual_self = commit_record(commits[6], 7)
        if actual_self["subject"] != SELF_SUBJECT or actual_self["body"] != SELF_BODY:
            failures.append("SEAL_COMMIT_DESCRIPTION_MISMATCH")

    self_missing = [section for section in REQUIRED_SECTIONS if section not in SELF_BODY]
    records.append(
        {
            "ordinal": 7,
            "role": ROLES[6],
            "commit_sha": "SELF_BOUND_EXTERNALLY_AFTER_PUBLICATION",
            "subject": SELF_SUBJECT,
            "body": SELF_BODY,
            "subject_sha256": sha256(SELF_SUBJECT.encode("utf-8")),
            "body_sha256": sha256(SELF_BODY.encode("utf-8")),
            "title_only": not bool(SELF_BODY.strip()),
            "missing_required_sections": self_missing,
        }
    )

    title_only_count = sum(bool(record["title_only"]) for record in records)
    missing_count = sum(bool(record["missing_required_sections"]) for record in records)
    if title_only_count:
        failures.append("TITLE_ONLY_NEW_COMMIT")
    if missing_count:
        failures.append("NEW_COMMIT_MISSING_REQUIRED_SECTION")

    ledger = {
        "schema_version": "trace-round16b-clean-integration-commit-description-ledger/v1",
        "status": "PASS" if not failures else "FAIL",
        "branch": BRANCH,
        "base_sha": OLD_MAIN,
        "entry_count": 7,
        "TITLE_ONLY_NEW_COMMIT_COUNT": title_only_count,
        "NEW_COMMIT_MISSING_REQUIRED_SECTION_COUNT": missing_count,
        "required_sections": REQUIRED_SECTIONS,
        "self_reference_boundary": (
            "Entry 7 contains the exact complete subject and body. Its commit SHA is "
            "bound by the external postpublication receipt because a Git commit cannot "
            "contain its own object ID."
        ),
        "commits": records,
        "failure_codes": failures,
    }
    return ledger, failures


def git_mode(relative_path: str) -> str:
    if relative_path in {
        str(LEDGER_PATH.relative_to(REPO)),
        str(Path(__file__).resolve().relative_to(REPO)),
    }:
        return "100644"
    output = git("ls-files", "--stage", "--", relative_path)
    if not output:
        return "UNTRACKED_EXPECTED_100644"
    return output.split(maxsplit=1)[0]


def build_manifest(ledger_data: bytes, failures: list[str]) -> dict[str, object]:
    if git("rev-parse", f"{EXPECTED_PRE_SEAL_COMMITS[0]}^") != OLD_MAIN:
        failures.append("BASELINE_IMPORT_PARENT_MISMATCH")
    if git("merge-base", "HEAD", RESEARCH_SHA) != OLD_MAIN:
        failures.append("RESEARCH_LINEAGE_MERGE_BASE_MISMATCH")
    if git("rev-parse", f"{OLD_MAIN}^{{tree}}") != OLD_MAIN_TREE:
        failures.append("OLD_MAIN_TREE_IDENTITY_MISMATCH")
    if git("rev-parse", f"{RESEARCH_SHA}^{{tree}}") != RESEARCH_TREE:
        failures.append("RESEARCH_TREE_IDENTITY_MISMATCH")

    sealed_groups: list[dict[str, object]] = []
    unique_paths: set[str] = set()
    historical_mismatch_count = 0
    missing_count = 0
    for group, paths in SEALED_GROUPS.items():
        artifacts: list[dict[str, object]] = []
        for relative_path in paths:
            if relative_path in unique_paths:
                failures.append(f"DUPLICATE_SEALED_PATH:{relative_path}")
            unique_paths.add(relative_path)
            if relative_path == str(LEDGER_PATH.relative_to(REPO)):
                data = ledger_data
            else:
                path = REPO / relative_path
                if not path.is_file():
                    failures.append(f"MISSING_SEALED_PATH:{relative_path}")
                    missing_count += 1
                    continue
                data = path.read_bytes()
            digest = sha256(data)
            if relative_path in HISTORICAL_SEAL_SHA256:
                if digest != HISTORICAL_SEAL_SHA256[relative_path]:
                    historical_mismatch_count += 1
                    failures.append(f"HISTORICAL_SEAL_HASH_MISMATCH:{relative_path}")
            artifacts.append(
                {
                    "path": relative_path,
                    "git_mode": git_mode(relative_path),
                    "bytes": len(data),
                    "sha256": digest,
                }
            )
        sealed_groups.append(
            {"group": group, "artifact_count": len(artifacts), "artifacts": artifacts}
        )

    manifest = {
        "schema_version": "trace-round16b-clean-main-integration-manifest/v1",
        "status": "PASS" if not failures else "FAIL",
        "round": "TRACE v49 Round 16B Clean Main Integration",
        "closure_claim": "evidence-bounded-nonclosure",
        "deployment": "none",
        "identities": {
            "old_main_sha": OLD_MAIN,
            "old_main_tree": OLD_MAIN_TREE,
            "research_branch": RESEARCH_BRANCH,
            "research_source_sha": RESEARCH_SHA,
            "research_source_tree": RESEARCH_TREE,
            "integration_branch": BRANCH,
            "baseline_import_sha": EXPECTED_PRE_SEAL_COMMITS[0],
            "verification_commit_sha": EXPECTED_PRE_SEAL_COMMITS[5],
            "seal_commit_sha": "SELF_BOUND_EXTERNALLY_AFTER_PUBLICATION",
        },
        "lineage": {
            "baseline_import_parent_equals_old_main": True,
            "integration_research_merge_base_equals_old_main": True,
            "published_research_history_rewritten": False,
            "research_branch_merged": False,
            "research_commits_cherry_picked": False,
        },
        "commit_description_ledger": {
            "path": str(LEDGER_PATH.relative_to(REPO)),
            "sha256": sha256(ledger_data),
            "entry_count": 7,
            "TITLE_ONLY_NEW_COMMIT_COUNT": 0,
            "NEW_COMMIT_MISSING_REQUIRED_SECTION_COUNT": 0,
        },
        "sealed_group_count": len(sealed_groups),
        "sealed_unique_artifact_count": len(unique_paths),
        "sealed_artifact_missing_count": missing_count,
        "historical_round16b_seal_modified_count": historical_mismatch_count,
        "self_excluded_generated_paths": [
            str(MANIFEST_PATH.relative_to(REPO)),
            str(MARKDOWN_PATH.relative_to(REPO)),
        ],
        "self_exclusion_reason": (
            "The manifest and its human rendering are excluded from their own "
            "artifact hash set to avoid a cryptographic hash cycle. Their exact "
            "bytes are verified by this sealed deterministic builder."
        ),
        "sealed_groups": sealed_groups,
        "closure_flags": {
            "PAIR_ASSOCIATION_CLOSURE": False,
            "HIGHER_ORDER_ASSOCIATION_CLOSURE": False,
            "GLOBAL_COMPOSITION_COHERENCE_CLOSURE": False,
            "PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE": False,
            "COMPUTATIONAL_SPACE_CLOSURE": False,
            "FUNCTION3_CLOSURE": False,
        },
        "publication_boundary": {
            "external_postpublication_receipt_required": True,
            "rollback_tag_creation_requires_no_auto_deployment_proof": True,
            "main_fast_forward_requires_no_auto_deployment_proof": True,
            "deployment_authorized": False,
        },
        "failure_codes": failures,
    }
    manifest["status"] = "PASS" if not failures else "FAIL"
    return manifest


def build_markdown(manifest: dict[str, object], ledger: dict[str, object]) -> bytes:
    identities = manifest["identities"]
    lines = [
        "# Clean Round 16B main-integration seal",
        "",
        "## Result",
        "",
        f"`STATUS={manifest['status']}`",
        "",
        f"`TITLE_ONLY_NEW_COMMIT_COUNT={ledger['TITLE_ONLY_NEW_COMMIT_COUNT']}`",
        "",
        f"`NEW_COMMIT_MISSING_REQUIRED_SECTION_COUNT={ledger['NEW_COMMIT_MISSING_REQUIRED_SECTION_COUNT']}`",
        "",
        f"`SEALED_UNIQUE_ARTIFACT_COUNT={manifest['sealed_unique_artifact_count']}`",
        "",
        f"`HISTORICAL_ROUND16B_SEAL_MODIFIED_COUNT={manifest['historical_round16b_seal_modified_count']}`",
        "",
        "## Exact identities",
        "",
        f"- Old main: `{identities['old_main_sha']}`",
        f"- Old-main tree: `{identities['old_main_tree']}`",
        f"- Research branch: `{identities['research_branch']}`",
        f"- Research source: `{identities['research_source_sha']}`",
        f"- Research-source tree: `{identities['research_source_tree']}`",
        f"- Integration branch: `{identities['integration_branch']}`",
        f"- Baseline import: `{identities['baseline_import_sha']}`",
        f"- Integration verification: `{identities['verification_commit_sha']}`",
        "- Seal commit: externally bound after publication.",
        "",
        "The integration branch is rooted directly at old main. Its merge base with",
        "the published Round 16B research source is old main, so the research branch",
        "was neither merged nor cherry-picked and its historical seal remains unchanged.",
        "",
        "## Commit descriptions",
        "",
    ]
    for record in ledger["commits"]:
        lines.append(
            f"{record['ordinal']}. `{record['commit_sha']}` — {record['subject']}"
        )
    lines.extend(
        [
            "",
            "The machine ledger stores the complete subject and body for all seven",
            "entries. Entry 7 is self-bound by exact message content; the external",
            "postpublication receipt binds its final Git object ID.",
            "",
            "## Sealed surfaces",
            "",
        ]
    )
    for group in manifest["sealed_groups"]:
        lines.append(f"- `{group['group']}`: {group['artifact_count']} artifacts")
    lines.extend(
        [
            "",
            "The manifest records Git mode, byte count, and SHA-256 for every sealed",
            "artifact. The bounded handoff source manifest transitively binds its 49",
            "required implementation sources.",
            "",
            "## Evidence and publication boundary",
            "",
            "This is an evidence-bounded functional baseline, not a closure claim.",
            "All six closure flags remain false. Open Inquiry remains isolated from",
            "validated associations, composition, topology, exports, and metrics.",
            "Frontend visual design, Search work, and deployment are outside this seal.",
            "A rollback tag or main push remains conditional on proving that a main",
            "push cannot automatically deploy.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def compare(path: Path, expected: bytes, failures: list[str]) -> None:
    if not path.is_file():
        failures.append(f"MISSING_GENERATED_OUTPUT:{path.relative_to(REPO)}")
    elif path.read_bytes() != expected:
        failures.append(f"STALE_GENERATED_OUTPUT:{path.relative_to(REPO)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    ledger, failures = build_ledger()
    ledger_data = json_bytes(ledger)
    manifest = build_manifest(ledger_data, failures)
    ledger["status"] = "PASS" if not failures else "FAIL"
    ledger["failure_codes"] = failures
    ledger_data = json_bytes(ledger)
    manifest["commit_description_ledger"]["sha256"] = sha256(ledger_data)
    manifest["status"] = "PASS" if not failures else "FAIL"
    manifest["failure_codes"] = failures
    manifest_data = json_bytes(manifest)
    markdown_data = build_markdown(manifest, ledger)

    if args.check:
        compare(LEDGER_PATH, ledger_data, failures)
        compare(MANIFEST_PATH, manifest_data, failures)
        compare(MARKDOWN_PATH, markdown_data, failures)
    else:
        LEDGER_PATH.write_bytes(ledger_data)
        MANIFEST_PATH.write_bytes(manifest_data)
        MARKDOWN_PATH.write_bytes(markdown_data)

    status = "PASS" if not failures else "FAIL"
    print(f"CLEAN_INTEGRATION_SEAL_STATUS={status}")
    print("NEW_COMMIT_COUNT=7")
    print(f"TITLE_ONLY_NEW_COMMIT_COUNT={ledger['TITLE_ONLY_NEW_COMMIT_COUNT']}")
    print(
        "NEW_COMMIT_MISSING_REQUIRED_SECTION_COUNT="
        f"{ledger['NEW_COMMIT_MISSING_REQUIRED_SECTION_COUNT']}"
    )
    print(f"SEALED_UNIQUE_ARTIFACT_COUNT={manifest['sealed_unique_artifact_count']}")
    print(f"SEALED_ARTIFACT_MISSING_COUNT={manifest['sealed_artifact_missing_count']}")
    print(
        "HISTORICAL_ROUND16B_SEAL_MODIFIED_COUNT="
        f"{manifest['historical_round16b_seal_modified_count']}"
    )
    for failure in failures:
        print(f"FAILURE_CODE={failure}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
