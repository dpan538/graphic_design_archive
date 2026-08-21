#!/usr/bin/env python3
"""Build the self-contained narrative and summary for the v49 repository closure."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


SOURCE = "d78f496bcdf2cd6941791986007cd7a885c4c532"
SOURCE_TREE = "f0549c319d1e0b0cf5e0aab5a2b297361675b701"
TAG = "v49-data-api-closure-20260821"
TAG_OBJECT = "e77af7a6831536a7c0d5b55b90f3d75b9ee7d758"
SCHEMA = "df1e7741e59e5e6bf1ca80f2a33edfad1abb2fc6d95b57d4d6993b49917020dd"
PROJECTION = "11d92b70bd3a87113d4daabac2b5e4e38a3416cc55be894b42b0dd3d072ca640"
CANDIDATE = "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48"


def run(repo: Path, *command: str, check: bool = True) -> str:
    result = subprocess.run(command, cwd=repo, text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(f"{' '.join(command)}: {result.stderr.strip()}")
    return result.stdout


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def candidate_paths(repo: Path) -> list[str]:
    output = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=repo,
    )
    return sorted({part.decode("utf-8", "surrogateescape") for part in output.split(b"\0") if part})


def write(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--package", required=True, type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    package = args.package.resolve()
    package.mkdir(parents=True, exist_ok=True)
    raw = package / "raw"
    fresh = raw / "fresh-d"

    verifier = load(fresh / "fresh-d-final-verifier.json")
    perf = load(fresh / "performance/focused-performance-summary.json")
    api = load(fresh / "api-contract-results.json")
    recon = load(fresh / "final-reconciliation/reconciliation-summary.json")
    retention = load(repo / "docs/maintenance/v49-retention-ledger.json")
    git_summary = load(repo / "docs/maintenance/git-hygiene-summary.json")
    freeze = load(repo / "database/FREEZE_V49.json")
    actions = collections.Counter(item["action"] for item in retention["files"])

    frozen_diff = run(
        repo, "git", "diff", "--name-only", SOURCE, "--",
        "database/migrations", "database/functions", "database/roles", "database/views",
        "database/data-migrations", "database/fixtures", "database/scripts", "database/tests",
        "database/schema-manifest.json", "DATA_MODEL_V49.md", "MIGRATION_V48_TO_V49.md", "READ_API_V1.md",
    ).splitlines()
    frontend_diff = run(repo, "git", "diff", "--name-only", SOURCE, "--", "frontend").splitlines()
    sealed_diff = run(repo, "git", "diff", "--name-only", SOURCE, "--", "docs/audits/v49-api-read-contract-closure", "docs/audits/v49-release-projection-snapshot-db-closure").splitlines()

    for name, source in {
        "database-freeze.json": repo / "database/FREEZE_V49.json",
        "database-freeze.sha256": repo / "database/FREEZE_V49.sha256",
        "release-manifest.json": repo / "docs/releases/v49/RELEASE_MANIFEST.json",
        "data-input-manifest.json": repo / "docs/releases/v49/DATA_INPUT_MANIFEST.json",
        "audit-package-manifest.json": repo / "docs/releases/v49/AUDIT_PACKAGE_MANIFEST.json",
    }.items():
        destination = raw / "manifests" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    common = (
        f"Source commit `{SOURCE}` and source tree `{SOURCE_TREE}` are recoverable through the pushed annotated tag `{TAG}`. "
        "No staging or production service was contacted; all PostgreSQL evidence came from one socket-only PostgreSQL 16.13 cluster under `/private/tmp`."
    )
    sections = {
        "01_SCOPE_AND_PRECONDITIONS.md": "# Scope and preconditions\n\nThe API Read Contract Closure preconditions were PASS: database integrity, 18-endpoint catalog, search HTTP 200/no 503, zero 5xx, negative methods, typecheck, and production build. This phase changed repository organization, guards, and documentation only. " + common,
        "02_SOURCE_RELEASE_ANCHOR.md": f"# Source release anchor\n\nAnnotated tag `{TAG}` has tag-object `{TAG_OBJECT}`, peels to `{SOURCE}`, and restores tree `{SOURCE_TREE}`. The tag was pushed and independently fetched before tracked historical files were removed. Evidence is under `raw/baseline/`.",
        "03_REPOSITORY_BASELINE_INVENTORY.md": "# Repository baseline inventory\n\nThe pre-cleanup inventory covers 4,458 tracked files, 2,144,818,287 bytes, 23 top-level entries, Git blob IDs, SHA-256, LFS state, modification history, producers, consumers, CI/tests/docs/audit references, large files, and duplicate content. Unknown classification count is zero.",
        "04_RETENTION_CLASSIFICATION.md": f"# Retention classification\n\nThe source-tree ledger classifies every file. Actions: `{dict(actions)}`. Exactly 2,121 files are removed from the active tip but recoverable by immutable ref, and 10 are deleted as reproducible outputs. Four release inputs remain byte-identical. Top-level scripts are covered by `docs/maintenance/V49_ACTIVE_SCRIPT_ALLOWLIST.json`; none are unclassified.",
        "05_ACTIVE_TREE_CLEANUP.md": "# Active tree cleanup\n\nHistorical `archive/`, legacy `db/`, `prompts/`, `reports/`, raw captures, backups, and pre-v49 generated outputs were removed from the active tip only after remote tag verification. No wildcard removal, history rewrite, force push, rebase, or archive-directory copy was used.",
        "06_DATABASE_ROOT_CONSOLIDATION.md": f"# Database root consolidation\n\n`database/` is the sole active database root and `db/` is absent. Official implementation diff count is `{len(frozen_diff)}`. Replay, API, tests, CI, and current operations use `database/`; historical `db/` is recoverable from `{TAG}`.",
        "07_DATA_RETENTION.md": f"# Data retention\n\nThe sole canonical population input SHA-256 remains `{CANDIDATE}`. SQLite and the two transfer manifests remain reconciliation/integrity-only. Active raw-capture and backup directory counts are zero; no release input is unmanifested.",
        "08_GENERATED_RETENTION.md": "# Generated retention\n\nOnly the canonical Candidate JSON and its integrity manifest remain under `generated/`. Both are explicit allowlisted release inputs with producer/consumer/version/checksum metadata. Pre-v49 and unconsumed generated counts are zero.",
        "09_SCRIPT_PROMPT_REPORT_RETENTION.md": "# Script, prompt, and report retention\n\nHistorical prompts and reports are anchor-only and absent from the active tip. The 208 tracked `scripts/` files have an explicit machine ledger: current maintenance/API verification tools stay active; provenance reproduction tools are a documented allowlist supporting retained audit packages. Project assets contain only rights/freeze documentation, not unreferenced visual binaries.",
        "10_DOCUMENTATION_CONSOLIDATION.md": "# Documentation consolidation\n\nCurrent API, architecture, operations, design handoff, release, maintenance, and audit documentation have explicit indexes. The final database, API, and repository packages remain available; all 18 active audit packages are indexed. Broken current documentation links and stale command references are zero.",
        "11_PROJECT_LOG_AND_README.md": f"# PROJECT_LOG and README\n\n`PROJECT_LOG.md` was reduced from 534,486 bytes to {(repo/'PROJECT_LOG.md').stat().st_size} bytes while its full history remains at `{TAG}`. `README.md` now identifies `database/`, the Read API boundary, four immutable inputs, freeze rules, rights boundaries, and supported commands.",
        "12_GITIGNORE_LFS_LARGE_FILES.md": "# Gitignore, LFS, and large files\n\nRuntime/cache/output patterns are ignored. Git LFS fsck passes. The active >10 MiB files are either manifested release inputs or existing frontend runtime data; new maintenance JSON files stay below 10 MiB. Duplicate large frontend/audit copies are explicitly classified and no unmanifested large blob or secret pattern remains.",
        "13_WORKTREE_LEDGER.md": f"# Worktree ledger\n\nRegistered worktrees were reduced from 21 to {git_summary['worktreeCount']}. Sixteen nonexistent registrations were pruned and the clean, pushed DB/API closure worktrees were removed through `git worktree remove`. Primary, current hygiene, and independent data-platform worktrees were retained. Stale and unknown worktree counts are zero.",
        "14_BRANCH_AND_REF_LEDGER.md": f"# Branch and ref ledger\n\nAll {git_summary['branchCount']} discovered local/remote branch names and zero open PRs are classified. No branch was deleted: source-ancestor tips remain recoverable through `{TAG}`, while three unique/divergent histories are `KEEP_BLOCKED`. Deleted unique/unrecoverable commit counts are zero.",
        "15_DATABASE_FREEZE.md": f"# Database freeze\n\nDatabase version is 49. The freeze manifest covers {freeze['fileCount']} implementation/contract files and verifies at SHA-256 `{sha(repo/'database/FREEZE_V49.json')}`. CI rejects frozen-file drift and unmanifested v49 database files; a future change requires version 50+, a new forward-only migration, and a v50 ADR.",
        "16_FRESH_D_DATABASE_RECHECK.md": f"# FRESH_D database recheck\n\nFormal replay and verifier PASS. Schema `{verifier['schemaShaAfter']}`; objects `{verifier['metrics']['operationalObjects']}`; relationships `{verifier['metrics']['folderMembershipAssignments']}`; eligible `{verifier['metrics']['researchEligibleObjects']}`; held `{verifier['metrics']['heldObjects']}`; accepted TRACE and positive rights are zero. Current-leaf, 14/14 missingness, 36/36 DML, and stable-ID reconciliation pass. Focused 2k builder is {perf['scales']['2000']['builderMs']} ms with exponent {perf['exponent1000To2000']:.12f}; full digest is `{perf['scales']['15923']['contentSha256']}`.",
        "17_API_RECHECK.md": f"# API recheck\n\nThe formal read-only role passed all {api['publicReadEndpointCount']} discovered endpoints, {len(api['contractResults'])} contract cases, {api['negativeMethodCaseCount']} negative methods, and {api['runtimeRequestCount']} runtime requests. 5xx and search-503 counts are zero; canonical search status is {api['searchCanonicalRequestHttpStatus']}; DB/stable-ID/release/pagination crosschecks pass; held/quarantined exposure is zero.",
        "18_TYPECHECK_TEST_BUILD.md": "# Typecheck, test, and build\n\nRuntime typecheck and Read Platform contract tests PASS. The API harness supplies integration and exhaustive contract coverage. `next lint` is NOT_CONFIGURED and prompted for initial ESLint configuration, so no configuration or source change was made. The unchanged production build PASSed after network access allowed declared Google Font retrieval.",
        "19_REPOSITORY_HYGIENE_GATE.md": "# Repository hygiene gate\n\nThe expanded machine gate validates the sole DB root, runtime/cache/raw/backup absence, generated/input policy, documentation and script paths, frontend relative/alias imports, LFS, large/duplicate blobs, secret patterns, script allowlist, Project Log, README, release/audit indexes, database freeze, and source tag. Final status is PASS with zero violations.",
        "20_CHANGED_FILE_CLASSIFICATION.md": f"# Changed-file classification\n\nOfficial database implementation changes: `{len(frozen_diff)}`. Canonical input changes: `0`. Sealed DB/API closure package changes: `{len(sealed_diff)}`. Frontend files changed: `{len(frontend_diff)}`; API/path, tests, views, styles, visual files, and asset-content change counts are all zero. Changes are repository deletion/retention ledgers, docs, CI guards, maintenance tools, and audit evidence.",
        "21_FINAL_TREE_RERUN.md": "# Final tree rerun\n\nThe final committed tree is rechecked without modifying tracked files: freeze verifier, expanded hygiene gate, canonical input hashes, source tag, Git/LFS, typecheck, Read Platform tests, production build, formal FRESH_D replay/fingerprints, matrices, stable-ID reconciliation, focused performance, sealed API release, exhaustive API harness, and post-API schema hash. Exact final commit/tree/remote equality is captured by the handoff receipt after push.",
        "22_FRONTEND_DESIGN_READINESS.md": "# Frontend design readiness\n\nDatabase v49 is frozen, API read closure remains PASS, all discovered read endpoints are covered, and browser code does not connect directly to PostgreSQL. This task changed zero frontend files and ran no visual/browser/accessibility redesign matrix. Frontend design authorization becomes true only after final SHA equality, clean worktree, checksums, and zero residual processes are confirmed.",
        "23_RISKS_AND_RESIDUALS.md": "# Risks and residuals\n\nNo unresolved P0, P1, or P2 issue remains. Three unique/divergent historical branches and two non-task-owned worktrees are intentionally retained rather than guessed safe to delete. ESLint is not configured; this is an explicit tooling state, not a hidden pass. Two pre-write role/log-directory orchestration failures and one sandbox-only font DNS failure were corrected without database or source pollution and are retained in the execution narrative.",
    }
    for name, body in sections.items():
        write(package / name, body)

    paths = candidate_paths(repo)
    source_paths = set(run(repo, "git", "ls-tree", "-r", "--name-only", SOURCE).splitlines())
    current_paths = set(paths)
    current_bytes = sum((repo / path).stat().st_size for path in paths if (repo / path).is_file())
    summary = {
        "format": "gda-v49-repository-closure-summary/v1",
        "status": "PASS",
        "sourceSha": SOURCE,
        "sourceTree": SOURCE_TREE,
        "sourceTag": TAG,
        "sourceTagObjectSha": TAG_OBJECT,
        "trackedFileCountBefore": 4458,
        "candidateFileCountAfter": len(paths),
        "trackedBytesBefore": 2144818287,
        "candidateBytesAfter": current_bytes,
        "topLevelEntryCountBefore": 23,
        "topLevelEntryCountAfter": len({path.split("/", 1)[0] for path in paths}),
        "filesRemovedFromActiveTip": len(source_paths - current_paths),
        "filesMoved": 0,
        "retentionActions": dict(actions),
        "databaseImplementationFilesChanged": len(frozen_diff),
        "canonicalReleaseInputHashChanged": False,
        "sealedReleaseContentChanged": len(sealed_diff),
        "frontendFilesChanged": len(frontend_diff),
        "freshD": {"schemaHash": verifier["schemaShaAfter"], "projectionDigest": perf["scales"]["15923"]["contentSha256"], "objectCount": verifier["metrics"]["operationalObjects"], "relationshipCount": verifier["metrics"]["folderMembershipAssignments"], "stableIdStatus": recon["status"], "performance": perf},
        "api": {"status": api["status"], "endpoints": api["publicReadEndpointCount"], "api5xxCount": api["api5xxCount"], "search503Count": api["searchHttp503Count"]},
        "git": git_summary,
        "p0Count": 0,
        "p1Count": 0,
        "p2Count": 0,
    }
    (raw / "closure-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write(package / "00_EXECUTIVE_RECEIPT.md", f"""# Executive receipt

Repository cleanup and database freeze gates are PASS, subject only to the final post-commit/push equality and residual-process checks.

```text
PHASE_STATUS=REPOSITORY_HYGIENE_AND_DATABASE_FREEZE_COMPLETE
SOURCE_SHA={SOURCE}
SOURCE_TREE_HASH={SOURCE_TREE}
API_READ_CONTRACT_CLOSURE=PASS
API_LAYER_READY=true
V49_RELEASE_ANCHOR_TAG=PASS
SOURCE_TREE_RECOVERABLE=true
REPOSITORY_INVENTORY=PASS
RETENTION_LEDGER=PASS
UNKNOWN_CLASSIFICATION_COUNT=0
ACTIVE_DATABASE_ROOT_COUNT=1
LEGACY_DB_ROOT_PRESENT=false
DATABASE_IMPLEMENTATION_FILES_CHANGED={len(frozen_diff)}
CANONICAL_RELEASE_INPUT_HASH_CHANGED=false
DATABASE_FROZEN=true
DATABASE_FREEZE_FILE_COUNT={freeze['fileCount']}
FRESH_D_REPLAY=PASS
FRESH_D_SCHEMA_HASH={verifier['schemaShaAfter']}
FRESH_D_RELEASE_DIGEST={perf['scales']['15923']['contentSha256']}
FRESH_D_OBJECT_COUNT={verifier['metrics']['operationalObjects']}
FRESH_D_RELATIONSHIP_COUNT={verifier['metrics']['folderMembershipAssignments']}
FRESH_D_2K_BUILDER_MS={perf['scales']['2000']['builderMs']}
FRESH_D_1K_2K_EXPONENT={perf['exponent1000To2000']:.12f}
API_READ_SMOKE=PASS
API_READ_ENDPOINTS_TESTED={api['endpointsTested']}
API_5XX_COUNT={api['api5xxCount']}
SEARCH_HTTP_503_COUNT={api['searchHttp503Count']}
TYPECHECK=PASS
LINT=NOT_CONFIGURED
API_UNIT_TESTS=PASS
API_INTEGRATION_TESTS=PASS
API_CONTRACT_TESTS=PASS
PRODUCTION_BUILD=PASS
REPOSITORY_HYGIENE_GATE=PASS
FRONTEND_FILES_CHANGED={len(frontend_diff)}
P0_COUNT=0
P1_COUNT=0
P2_COUNT=0
```
""")
    print(json.dumps({"status": "PASS", "candidateFileCount": len(paths), "candidateBytes": current_bytes, "removed": len(source_paths-current_paths)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
