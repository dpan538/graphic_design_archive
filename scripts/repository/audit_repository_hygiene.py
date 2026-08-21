#!/usr/bin/env python3
"""Machine-readable repository hygiene gate for the frozen v49 active tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path


TAG = "v49-data-api-closure-20260821"
SOURCE = "d78f496bcdf2cd6941791986007cd7a885c4c532"
ALLOWED_GENERATED = {
    "generated/public_surfaces_prefreeze_candidate_v48.json",
    "generated/prefreeze_candidate_v48_transfer_manifest.json",
}
RUNTIME_PATTERNS = [
    re.compile(r"(^|/)(?:node_modules|\.next|coverage|htmlcov|test-results|playwright-report|browser-cache|sessions?|cookies?|downloads?|pgdata|postgres-data|audit-staging)(/|$)"),
    re.compile(r"(?:\.sqlite-(?:journal|wal|shm)|\.db-(?:journal|wal|shm)|postmaster\.pid|\.s\.PGSQL\.)"),
]
SECRET_PATTERNS = [
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b"),
]
CURRENT_DOC_ROOTS = (
    "docs/api/", "docs/architecture/", "docs/operations/", "docs/design/",
    "docs/releases/v49/", "docs/maintenance/",
)


def run(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(args, cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def tracked(repo: Path) -> list[str]:
    result = run(repo, "git", "ls-files", "-z")
    if result.returncode:
        raise SystemExit(result.stderr.decode("utf-8", "replace"))
    return [value.decode("utf-8", "surrogateescape") for value in result.stdout.split(b"\0") if value]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def doc_link_failures(repo: Path, files: list[str]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    selected = [path for path in files if path in {"README.md", "PROJECT_LOG.md", "DATA_MODEL_V49.md", "MIGRATION_V48_TO_V49.md", "READ_API_V1.md"} or path.startswith(CURRENT_DOC_ROOTS)]
    pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    for path in selected:
        source = repo / path
        try:
            text = source.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        for target in pattern.findall(text):
            clean = target.split("#", 1)[0].split("?", 1)[0]
            if not clean or clean.startswith(("http://", "https://", "mailto:", "/")):
                continue
            resolved = (source.parent / clean).resolve()
            try:
                resolved.relative_to(repo)
            except ValueError:
                failures.append({"source": path, "target": target})
                continue
            if not resolved.exists():
                failures.append({"source": path, "target": target})
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    files = tracked(repo)
    tracked_set = set(files)
    data_manifest = json.loads((repo / "docs/releases/v49/DATA_INPUT_MANIFEST.json").read_text())
    release_inputs = {item["path"] for item in data_manifest["inputs"]}
    runtime_files = sorted(path for path in files if any(pattern.search(path) for pattern in RUNTIME_PATTERNS))
    raw_dirs = sorted({part for path in files for part in Path(path).parts if part.endswith("_raw")})
    backup_dirs = sorted({path.split("/", 2)[0] + "/" + path.split("/", 2)[1] for path in files if "/backups/" in "/" + path})
    pre_v49_generated = sorted(path for path in files if path.startswith("generated/") and re.search(r"v(?:4[0-8]|[0-3][0-9])", path, re.I))
    unconsumed_generated = sorted(path for path in files if path.startswith("generated/") and path not in ALLOWED_GENERATED)
    unmanifested_inputs = sorted((release_inputs - tracked_set) | ({"generated/public_surfaces_prefreeze_candidate_v48.json"} - release_inputs))
    large: list[dict[str, object]] = []
    unmanifested_large: list[str] = []
    duplicate_map: dict[tuple[str, int], list[str]] = defaultdict(list)
    for path in files:
        source = repo / path
        size = source.stat().st_size
        if size > 1024 * 1024:
            digest = sha(source)
            duplicate_map[(digest, size)].append(path)
            if size > 10 * 1024 * 1024:
                category = "release_input" if path in release_inputs else "final_audit_evidence" if path.startswith("docs/audits/") else "current_frontend_runtime" if path.startswith("frontend/") else "inventory_evidence" if path.startswith("docs/maintenance/v49-") else "UNMANIFESTED"
                large.append({"path": path, "byteSize": size, "sha256": digest, "category": category})
                if category == "UNMANIFESTED":
                    unmanifested_large.append(path)
    duplicate_large_violations = []
    duplicate_large_allowlist = []
    for (digest, size), paths in duplicate_map.items():
        if size <= 1024 * 1024 or len(paths) < 2:
            continue
        item = {"sha256": digest, "byteSize": size, "paths": sorted(paths)}
        if all(path.startswith("docs/audits/") for path in paths) or all(path.startswith("frontend/") for path in paths):
            item["reason"] = "self-contained audit evidence or current frontend contract copy"
            duplicate_large_allowlist.append(item)
        else:
            duplicate_large_violations.append(item)
    secret_matches: list[dict[str, str]] = []
    for path in files:
        if path.startswith("docs/audits/"):
            continue
        source = repo / path
        if source.stat().st_size > 1024 * 1024:
            continue
        try:
            data = source.read_bytes()
        except OSError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(data):
                secret_matches.append({"path": path, "pattern": pattern.pattern.decode("ascii", "replace")})
    links = doc_link_failures(repo, files)
    lfs = run(repo, "git", "lfs", "fsck")
    tag = run(repo, "git", "rev-parse", f"{TAG}^{{}}")
    tag_commit = tag.stdout.decode().strip() if tag.returncode == 0 else ""
    project_log_bytes = (repo / "PROJECT_LOG.md").stat().st_size
    freeze = run(repo, "python3", "scripts/repository/verify_v49_database_freeze.py", "--repo", str(repo))
    checks = {
        "activeDatabaseRootCount": 1 if (repo / "database").is_dir() and not (repo / "db").exists() else 0,
        "activeDatabaseRoot": "database" if (repo / "database").is_dir() else None,
        "legacyDbRootPresent": (repo / "db").exists(),
        "trackedRuntimeFiles": runtime_files,
        "activeRawCaptureDirectories": raw_dirs,
        "activeBackupDirectories": backup_dirs,
        "preV49Generated": pre_v49_generated,
        "unconsumedGenerated": unconsumed_generated,
        "unmanifestedReleaseInputs": unmanifested_inputs,
        "brokenDocumentationLinks": links,
        "brokenLfsPointerCount": 0 if lfs.returncode == 0 else 1,
        "lfsFsckOutput": (lfs.stdout + lfs.stderr).decode("utf-8", "replace").strip(),
        "unmanifestedLargeFiles": unmanifested_large,
        "largeFileManifest": large,
        "duplicateLargeBlobViolations": duplicate_large_violations,
        "duplicateLargeBlobAllowlist": duplicate_large_allowlist,
        "secretPatternMatches": secret_matches,
        "projectLogBytes": project_log_bytes,
        "projectLogPolicyPass": project_log_bytes <= 100000,
        "readmeV49ArchitecturePass": all(value in (repo / "README.md").read_text() for value in ["database/", "v49", "Read API", "v49-data-api-closure-20260821"]),
        "releaseManifestPass": (repo / "docs/releases/v49/RELEASE_MANIFEST.json").is_file(),
        "auditIndexPass": (repo / "docs/releases/v49/AUDIT_INDEX.md").is_file(),
        "databaseFreezePass": freeze.returncode == 0,
        "databaseFreezeOutput": (freeze.stdout + freeze.stderr).decode("utf-8", "replace").strip(),
        "sourceTagCommit": tag_commit,
        "sourceTagResolvable": tag_commit == SOURCE,
    }
    violations = []
    predicates = {
        "ACTIVE_DATABASE_ROOT": checks["activeDatabaseRootCount"] == 1,
        "LEGACY_DB_ROOT": not checks["legacyDbRootPresent"],
        "TRACKED_RUNTIME": not runtime_files,
        "RAW_CAPTURE": not raw_dirs,
        "BACKUP_DIRECTORY": not backup_dirs,
        "PRE_V49_GENERATED": not pre_v49_generated,
        "UNCONSUMED_GENERATED": not unconsumed_generated,
        "UNMANIFESTED_RELEASE_INPUT": not unmanifested_inputs,
        "BROKEN_DOC_LINK": not links,
        "BROKEN_LFS": checks["brokenLfsPointerCount"] == 0,
        "UNMANIFESTED_LARGE": not unmanifested_large,
        "DUPLICATE_LARGE": not duplicate_large_violations,
        "SECRET_PATTERN": not secret_matches,
        "PROJECT_LOG_POLICY": checks["projectLogPolicyPass"],
        "README_V49": checks["readmeV49ArchitecturePass"],
        "RELEASE_MANIFEST": checks["releaseManifestPass"],
        "AUDIT_INDEX": checks["auditIndexPass"],
        "DATABASE_FREEZE": checks["databaseFreezePass"],
        "SOURCE_TAG": checks["sourceTagResolvable"],
    }
    violations.extend(name for name, passed in predicates.items() if not passed)
    payload = {"format": "gda-v49-repository-hygiene/v1", "status": "PASS" if not violations else "FAIL", "trackedFileCount": len(files), "checks": checks, "violations": violations}
    rendered = json.dumps(payload, indent=2) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text("# Repository hygiene gate\n\n```json\n" + rendered + "```\n")
    print(json.dumps({"status": payload["status"], "trackedFileCount": len(files), "violationCount": len(violations), "violations": violations}, sort_keys=True))
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
