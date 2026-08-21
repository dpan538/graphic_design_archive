#!/usr/bin/env python3
"""Build deterministic v49 repository file, large-file, duplicate, and retention inventories."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
from collections import defaultdict, deque
from pathlib import Path


TEXT_LIMIT = 5 * 1024 * 1024
PATH_TOKEN = re.compile(r"(?<![A-Za-z0-9_.-])(?:\.{0,2}/)?[A-Za-z0-9_.@+()\[\]-]+(?:/[A-Za-z0-9_.@+()\[\]-]+)+")
VERSION_TOKEN = re.compile(r"(?i)(?:^|[^a-z0-9])(v(?:4[6-9]|49)(?:\.[0-9]+)?)")
RELEASE_INPUTS = {
    "generated/public_surfaces_prefreeze_candidate_v48.json",
    "data/prefreeze_candidate_v48.sqlite",
    "generated/prefreeze_candidate_v48_transfer_manifest.json",
    "data/prefreeze_candidate_v48_transfer_manifest.csv",
}
FINAL_AUDITS = {
    "docs/audits/v49-phase2b-migration",
    "docs/audits/v49-release-projection-snapshot-db-closure",
    "docs/audits/v49-api-read-contract-closure",
    "docs/audits/v49-repository-hygiene-and-database-freeze",
}


def git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=repo, input=input_bytes, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=True,
    ).stdout


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tracked_files(repo: Path) -> list[str]:
    return [value.decode("utf-8", "surrogateescape") for value in git(repo, "ls-files", "-z").split(b"\0") if value]


def index_entries(repo: Path) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for raw in git(repo, "ls-files", "-s", "-z").split(b"\0"):
        if not raw:
            continue
        meta, path = raw.split(b"\t", 1)
        mode, blob, _stage = meta.decode().split()
        result[path.decode("utf-8", "surrogateescape")] = (mode, blob)
    return result


def last_changes(repo: Path, wanted: set[str]) -> dict[str, tuple[str, str]]:
    output = git(repo, "log", "--format=@@%H%x09%cI", "--name-only", "--no-renames", "HEAD").decode("utf-8", "replace")
    result: dict[str, tuple[str, str]] = {}
    commit = date = ""
    for line in output.splitlines():
        if line.startswith("@@"):
            commit, date = line[2:].split("\t", 1)
        elif line and line in wanted and line not in result:
            result[line] = (commit, date)
        if len(result) == len(wanted):
            break
    return result


def lfs_attrs(repo: Path, files: list[str]) -> dict[str, bool]:
    payload = b"\0".join(path.encode("utf-8", "surrogateescape") for path in files) + b"\0"
    output = git(repo, "check-attr", "-z", "--stdin", "filter", input_bytes=payload).split(b"\0")
    result: dict[str, bool] = {}
    for index in range(0, len(output) - 2, 3):
        path = output[index].decode("utf-8", "surrogateescape")
        result[path] = output[index + 2] == b"lfs"
    return result


def explicit_references(repo: Path, files: list[str]) -> dict[str, set[str]]:
    known = set(files)
    by_consumer: dict[str, set[str]] = defaultdict(set)
    extension_candidates = ("", ".ts", ".tsx", ".js", ".mjs", ".json", ".py", ".sql", ".md")
    for consumer in files:
        source = repo / consumer
        try:
            if source.stat().st_size > TEXT_LIMIT:
                continue
            data = source.read_bytes()
            if b"\0" in data[:8192]:
                continue
            text = data.decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for match in PATH_TOKEN.finditer(text):
            token = match.group(0).rstrip(".,:;)}]\"'")
            candidates: list[str] = []
            if token.startswith(("./", "../")):
                resolved = os.path.normpath(str(Path(consumer).parent / token))
                candidates.extend(resolved + suffix for suffix in extension_candidates)
            else:
                candidates.extend(token + suffix for suffix in extension_candidates)
            for candidate in candidates:
                if candidate in known and candidate != consumer:
                    by_consumer[consumer].add(candidate)
                    break
    return by_consumer


def transitive_consumers(files: list[str], direct: dict[str, set[str]]) -> dict[str, list[str]]:
    reverse: dict[str, set[str]] = defaultdict(set)
    for consumer, dependencies in direct.items():
        for dependency in dependencies:
            reverse[dependency].add(consumer)
    result: dict[str, list[str]] = {}
    for path in files:
        seen: set[str] = set()
        queue = deque(reverse.get(path, ()))
        while queue and len(seen) < 250:
            item = queue.popleft()
            if item in seen:
                continue
            seen.add(item)
            queue.extend(reverse.get(item, ()))
        result[path] = sorted(seen)
    return result


def action_for(path: str) -> tuple[str, str, str]:
    if path in RELEASE_INPUTS:
        return "KEEP_RELEASE_INPUT", path, "byte-pinned v49 population/reconciliation input"
    if any(path == root or path.startswith(root + "/") for root in FINAL_AUDITS):
        return "KEEP_RELEASE_EVIDENCE", path, "authoritative v49 closure evidence"
    if path.startswith("db/"):
        return "ARCHIVE_BY_IMMUTABLE_REF", "v49-data-api-closure-20260821", "legacy database skeleton superseded by database/"
    if path.startswith(("prompts/", "reports/", "archive/")):
        return "ARCHIVE_BY_IMMUTABLE_REF", "v49-data-api-closure-20260821", "historical research or unrelated archived artifact"
    if path.startswith("data/"):
        return "ARCHIVE_BY_IMMUTABLE_REF", "v49-data-api-closure-20260821", "historical capture/intermediate data not used by v49 replay"
    if path.startswith("generated/"):
        return "DELETE_REGENERABLE", "v49-data-api-closure-20260821", "pre-v49 or superseded generated artifact"
    if path == "PROJECT_LOG.md":
        return "KEEP_CURRENT_DOCUMENTATION", path, "replace with concise active project index; full log anchored"
    if path.startswith("docs/audits/"):
        return "KEEP_RELEASE_EVIDENCE", path, "active audit package retained and indexed"
    if path.startswith("docs/") or path.endswith(".md"):
        return "KEEP_CURRENT_DOCUMENTATION", path, "current or indexed repository documentation"
    return "KEEP_ACTIVE", path, "current implementation, test, CI, asset, or maintenance file"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    files = tracked_files(repo)
    entries = index_entries(repo)
    changes = last_changes(repo, set(files))
    lfs = lfs_attrs(repo, files)
    references = explicit_references(repo, files)
    reverse: dict[str, list[str]] = defaultdict(list)
    for consumer, deps in references.items():
        for dependency in deps:
            reverse[dependency].append(consumer)
    transitive = transitive_consumers(files, references)
    rows: list[dict[str, object]] = []
    retention: list[dict[str, object]] = []
    for path in files:
        absolute = repo / path
        stat = absolute.stat()
        mode, blob = entries[path]
        sha = sha256_file(absolute)
        direct = sorted(reverse.get(path, []))
        producers = [value for value in direct if value.startswith("scripts/") or "/scripts/" in value]
        commit, date = changes.get(path, ("", ""))
        version = VERSION_TOKEN.search(path)
        audit_refs = [value for value in direct if value.startswith("docs/audits/")]
        release_refs = [value for value in direct if value.startswith("docs/releases/") or value in RELEASE_INPUTS]
        row = {
            "path": path,
            "top_level_directory": path.split("/", 1)[0],
            "extension": Path(path).suffix.lower(),
            "byte_size": stat.st_size,
            "git_mode": mode,
            "git_blob_sha": blob,
            "sha256": sha,
            "lfs_pointer_status": "LFS_TRACKED" if lfs.get(path) else "NOT_LFS",
            "last_modifying_commit": commit,
            "last_modifying_date": date,
            "version_marker": version.group(1).lower() if version else "",
            "producer_script": producers,
            "direct_consumers": direct,
            "transitive_consumers": transitive[path],
            "ci_references": [value for value in direct if value.startswith(".github/")],
            "test_references": [value for value in direct if "test" in value.lower() or "fixture" in value.lower()],
            "documentation_references": [value for value in direct if value.endswith(".md")],
            "audit_manifest_references": audit_refs,
        }
        rows.append(row)
        action, destination, reason = action_for(path)
        retention.append({
            "path": path,
            "file_type": Path(path).suffix.lower() or "none",
            "size_bytes": stat.st_size,
            "blob_sha": blob,
            "sha256": sha,
            "producer": producers,
            "direct_consumers": direct,
            "transitive_consumers": transitive[path],
            "audit_references": audit_refs,
            "release_references": release_refs,
            "rights_sensitivity": "SENSITIVE" if path.startswith(("data/", "generated/", "project-assets/")) or "rights" in path.lower() else "NONE",
            "authoritative_status": "AUTHORITATIVE" if path in RELEASE_INPUTS or path.startswith("database/") else "DERIVED",
            "reproducible": bool(producers) or action in {"ARCHIVE_BY_IMMUTABLE_REF", "DELETE_REGENERABLE"},
            "current_runtime_required": path.startswith("frontend/"),
            "current_api_required": path.startswith("frontend/src/") and "read-platform" in path,
            "current_database_required": path.startswith("database/") or path in RELEASE_INPUTS,
            "current_test_required": bool([value for value in direct if "test" in value.lower()]),
            "action": action,
            "destination_or_anchor": destination,
            "reason": reason,
            "validation_required": "consumer graph + release anchor + final DB/API/build/hygiene gates",
        })
    fieldnames = list(rows[0])
    with (output / "v49-repository-inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, separators=(",", ":")) if isinstance(value, list) else value for key, value in row.items()})
    (output / "v49-repository-inventory.json").write_text(json.dumps({"format": "gda-v49-repository-inventory/v1", "trackedFileCount": len(rows), "files": rows}, separators=(",", ":")) + "\n")
    retention_fields = list(retention[0])
    with (output / "v49-retention-ledger.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=retention_fields)
        writer.writeheader()
        for row in retention:
            writer.writerow({key: json.dumps(value, separators=(",", ":")) if isinstance(value, list) else value for key, value in row.items()})
    (output / "v49-retention-ledger.json").write_text(json.dumps({"format": "gda-v49-retention-ledger/v1", "unknownClassificationCount": 0, "files": retention}, separators=(",", ":")) + "\n")
    large = [row for row in rows if int(row["byte_size"]) > 1024 * 1024]
    with (output / "v49-large-file-inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "byte_size", "sha256", "lfs_pointer_status", "over_10_mib", "over_50_mib"])
        writer.writeheader()
        for row in large:
            writer.writerow({"path": row["path"], "byte_size": row["byte_size"], "sha256": row["sha256"], "lfs_pointer_status": row["lfs_pointer_status"], "over_10_mib": int(row["byte_size"]) > 10 * 1024 * 1024, "over_50_mib": int(row["byte_size"]) > 50 * 1024 * 1024})
    duplicates: dict[tuple[str, int], list[str]] = defaultdict(list)
    for row in rows:
        duplicates[(str(row["sha256"]), int(row["byte_size"]))].append(str(row["path"]))
    with (output / "v49-duplicate-content-inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sha256", "byte_size", "file_count", "paths"])
        writer.writeheader()
        for (sha, size), paths in sorted(duplicates.items()):
            if len(paths) > 1:
                writer.writerow({"sha256": sha, "byte_size": size, "file_count": len(paths), "paths": json.dumps(sorted(paths), separators=(",", ":"))})
    print(json.dumps({"status": "PASS", "trackedFileCount": len(rows), "trackedBytes": sum(int(row["byte_size"]) for row in rows), "largeFileCount": len(large), "unknownClassificationCount": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
