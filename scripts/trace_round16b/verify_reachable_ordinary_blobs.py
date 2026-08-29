#!/usr/bin/env python3
"""Inventory every Git blob reachable from a Round 16B commit.

The ledger contains one row for every distinct (blob object, historical path)
pair found in the complete commit ancestry of ``--ref``.  LFS pointer blobs are
identified from their canonical pointer syntax and are counted separately from
ordinary Git payloads.  Hosting-limit checks apply only to ordinary payloads.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterable


AUTHORIZED_SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
HOSTING_LIMIT_BYTES = 100_000_000
THRESHOLDS_BYTES = (25_000_000, 50_000_000, 90_000_000, HOSTING_LIMIT_BYTES)
LFS_POINTER_MAX_BYTES = 4096
LFS_VERSION_LINE = "version https://git-lfs.github.com/spec/v1"
LFS_OID_RE = re.compile(r"oid sha256:[0-9a-f]{64}\Z")
LFS_SIZE_RE = re.compile(r"size (0|[1-9][0-9]*)\Z")
LFS_EXTENSION_RE = re.compile(r"ext-[A-Za-z0-9.-]+ .+\Z")


class VerificationError(RuntimeError):
    """Raised when a required Git operation or invariant fails."""


def git(repo: Path, *argv: str, input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(
        ("git", *argv),
        cwd=repo,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        command = "git " + " ".join(argv)
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise VerificationError(f"{command} failed ({result.returncode}): {detail}")
    return result.stdout


def resolve_commit(repo: Path, revision: str) -> str:
    if not revision or "\0" in revision or "\n" in revision:
        raise VerificationError("revision must be a non-empty single-line value")
    return git(
        repo,
        "rev-parse",
        "--verify",
        "--end-of-options",
        f"{revision}^{{commit}}",
    ).decode("ascii").strip()


def resolve_tree(repo: Path, commit_sha: str) -> str:
    return git(
        repo,
        "rev-parse",
        "--verify",
        "--end-of-options",
        f"{commit_sha}^{{tree}}",
    ).decode("ascii").strip()


def reachable_object_ids(repo: Path, commit_sha: str) -> set[str]:
    output = git(repo, "rev-list", "--objects", "--no-object-names", commit_sha)
    object_ids = {
        line.decode("ascii")
        for line in output.splitlines()
        if line
    }
    if not object_ids:
        raise VerificationError(f"no objects were reachable from {commit_sha}")
    return object_ids


def batch_object_info(repo: Path, object_ids: Iterable[str]) -> dict[str, tuple[str, int]]:
    requested = sorted(set(object_ids))
    if not requested:
        return {}
    output = git(
        repo,
        "cat-file",
        "--batch-check=%(objectname) %(objecttype) %(objectsize)",
        input_bytes=("\n".join(requested) + "\n").encode("ascii"),
    )
    inventory: dict[str, tuple[str, int]] = {}
    for line in output.decode("ascii").splitlines():
        parts = line.split(" ")
        if len(parts) != 3 or not parts[2].isdigit():
            raise VerificationError(f"unexpected git cat-file inventory row: {line!r}")
        object_sha, object_type, size_text = parts
        inventory[object_sha] = (object_type, int(size_text))
    if set(inventory) != set(requested):
        missing = sorted(set(requested) - set(inventory))
        raise VerificationError(f"git cat-file omitted {len(missing)} objects: {missing[:3]}")
    return inventory


def batch_object_contents(
    repo: Path,
    object_ids: Iterable[str],
    expected_type: str,
) -> dict[str, bytes]:
    requested = sorted(set(object_ids))
    if not requested:
        return {}
    output = git(
        repo,
        "cat-file",
        "--batch",
        input_bytes=("\n".join(requested) + "\n").encode("ascii"),
    )
    stream = io.BytesIO(output)
    contents: dict[str, bytes] = {}
    for expected_sha in requested:
        header = stream.readline()
        if not header:
            raise VerificationError(f"git cat-file omitted content for {expected_sha}")
        parts = header.rstrip(b"\n").split(b" ")
        if len(parts) != 3 or not parts[2].isdigit():
            raise VerificationError(f"unexpected git cat-file content header: {header!r}")
        object_sha = parts[0].decode("ascii")
        object_type = parts[1].decode("ascii")
        byte_size = int(parts[2])
        if object_sha != expected_sha or object_type != expected_type:
            raise VerificationError(
                "git cat-file content mismatch: "
                f"expected {expected_sha} {expected_type}, got {object_sha} {object_type}"
            )
        content = stream.read(byte_size)
        if len(content) != byte_size or stream.read(1) != b"\n":
            raise VerificationError(f"truncated git cat-file content for {expected_sha}")
        contents[object_sha] = content
    if stream.read():
        raise VerificationError("git cat-file returned trailing unparsed bytes")
    return contents


def is_lfs_pointer(content: bytes) -> bool:
    """Recognize a canonical v1 Git LFS pointer, including extension lines."""

    if len(content) > LFS_POINTER_MAX_BYTES:
        return False
    try:
        text = content.decode("ascii")
    except UnicodeDecodeError:
        return False
    lines = text.splitlines()
    if len(lines) < 3 or lines[0] != LFS_VERSION_LINE:
        return False
    oid_count = 0
    size_count = 0
    reached_oid = False
    reached_size = False
    for line in lines[1:]:
        if not reached_oid and LFS_EXTENSION_RE.fullmatch(line):
            continue
        if not reached_oid and LFS_OID_RE.fullmatch(line):
            oid_count += 1
            reached_oid = True
            continue
        if reached_oid and not reached_size and LFS_SIZE_RE.fullmatch(line):
            size_count += 1
            reached_size = True
            continue
        return False
    return oid_count == 1 and size_count == 1 and reached_size


def parse_tree(content: bytes, raw_object_bytes: int) -> tuple[tuple[bytes, bytes, str], ...]:
    entries: list[tuple[bytes, bytes, str]] = []
    offset = 0
    while offset < len(content):
        space = content.find(b" ", offset)
        nul = content.find(b"\0", space + 1)
        if space < 0 or nul < 0:
            raise VerificationError("malformed raw Git tree object")
        mode = content[offset:space]
        name = content[space + 1:nul]
        object_start = nul + 1
        object_end = object_start + raw_object_bytes
        if not mode or not name or object_end > len(content):
            raise VerificationError("malformed raw Git tree entry")
        entries.append((mode, name, content[object_start:object_end].hex()))
        offset = object_end
    return tuple(entries)


def commit_root_trees(commit_contents: dict[str, bytes]) -> dict[str, str]:
    roots: dict[str, str] = {}
    for commit_sha, content in commit_contents.items():
        first_line = content.split(b"\n", 1)[0]
        if not first_line.startswith(b"tree "):
            raise VerificationError(f"commit {commit_sha} has no leading tree header")
        try:
            tree_sha = first_line[5:].decode("ascii")
        except UnicodeDecodeError as exc:
            raise VerificationError(f"commit {commit_sha} has a non-ASCII tree id") from exc
        roots[commit_sha] = tree_sha
    return roots


def collect_aliases(
    root_trees: Iterable[str],
    trees: dict[str, tuple[tuple[bytes, bytes, str], ...]],
    blob_ids: set[str],
) -> dict[str, set[bytes]]:
    aliases: dict[str, set[bytes]] = defaultdict(set)
    seen_tree_contexts: set[tuple[str, bytes]] = set()
    stack = [(tree_sha, b"") for tree_sha in sorted(set(root_trees), reverse=True)]
    while stack:
        tree_sha, prefix = stack.pop()
        context = (tree_sha, prefix)
        if context in seen_tree_contexts:
            continue
        seen_tree_contexts.add(context)
        try:
            entries = trees[tree_sha]
        except KeyError as exc:
            raise VerificationError(f"tree {tree_sha} is absent from reachable inventory") from exc
        for mode, name, object_sha in entries:
            path = name if not prefix else prefix + b"/" + name
            if mode == b"40000":
                stack.append((object_sha, path))
            elif mode == b"160000":
                # A gitlink records a submodule commit, not a blob in this object database.
                continue
            elif object_sha in blob_ids:
                aliases[object_sha].add(path)
            else:
                raise VerificationError(
                    f"non-tree entry {path!r} references unclassified object {object_sha}"
                )
    return aliases


def path_text(path: bytes) -> str:
    return path.decode("utf-8", "surrogateescape")


def path_list(paths: Iterable[bytes]) -> list[str]:
    return [path_text(path) for path in sorted(set(paths))]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def blob_summary(
    object_sha: str,
    sizes: dict[str, int],
    aliases: dict[str, set[bytes]],
) -> dict[str, Any]:
    paths = path_list(aliases.get(object_sha, set()))
    return {
        "object_sha": object_sha,
        "bytes": sizes[object_sha],
        "alias_count": len(paths),
        "alias_paths": paths,
    }


def threshold_receipts(
    ordinary_ids: set[str],
    sizes: dict[str, int],
    aliases: dict[str, set[bytes]],
) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for threshold in THRESHOLDS_BYTES:
        matching = sorted(
            (object_sha for object_sha in ordinary_ids if sizes[object_sha] >= threshold),
            key=lambda object_sha: (-sizes[object_sha], object_sha),
        )
        receipts.append(
            {
                "threshold_bytes_inclusive": threshold,
                "ordinary_blob_count": len(matching),
                "blob_path_alias_count": sum(len(aliases[object_sha]) for object_sha in matching),
                "ordinary_blobs": [blob_summary(sha, sizes, aliases) for sha in matching],
            }
        )
    return receipts


def violation_commit_map(
    violation_ids: set[str],
    commit_trees: dict[str, str],
    trees: dict[str, tuple[tuple[bytes, bytes, str], ...]],
) -> dict[str, dict[str, set[bytes]]]:
    found: dict[str, dict[str, set[bytes]]] = {
        object_sha: defaultdict(set) for object_sha in violation_ids
    }

    @lru_cache(maxsize=None)
    def contained(tree_sha: str) -> tuple[tuple[str, bytes], ...]:
        rows: list[tuple[str, bytes]] = []
        for mode, name, object_sha in trees[tree_sha]:
            if mode == b"40000":
                for nested_sha, nested_path in contained(object_sha):
                    rows.append((nested_sha, name + b"/" + nested_path))
            elif object_sha in violation_ids:
                rows.append((object_sha, name))
        return tuple(rows)

    for commit_sha, tree_sha in sorted(commit_trees.items()):
        for object_sha, path in contained(tree_sha):
            found[object_sha][commit_sha].add(path)
    return found


def containing_commit_rows(
    rows: dict[str, set[bytes]],
    allowed_commits: set[str] | None = None,
) -> list[dict[str, Any]]:
    return [
        {
            "commit_sha": commit_sha,
            "alias_paths": path_list(paths),
        }
        for commit_sha, paths in sorted(rows.items())
        if allowed_commits is None or commit_sha in allowed_commits
    ]


def run_self_checks() -> int:
    """Exercise the semantic boundaries without depending on repository state."""

    canonical_pointer = (
        LFS_VERSION_LINE
        + "\n"
        + "oid sha256:"
        + ("a" * 64)
        + "\nsize 100000000\n"
    ).encode("ascii")
    canonical_pointer_with_extension = (
        LFS_VERSION_LINE
        + "\next-demo.example deterministic-extension\n"
        + "oid sha256:"
        + ("b" * 64)
        + "\nsize 7\n"
    ).encode("ascii")
    noncanonical_pointer_extra_line = canonical_pointer + b"unexpected value\n"
    noncanonical_pointer_uppercase_oid = canonical_pointer.replace(b"a" * 64, b"A" * 64)
    noncanonical_pointer_missing_size = canonical_pointer.rsplit(b"\nsize ", 1)[0] + b"\n"

    historical_trees = {
        "subtree": ((b"100644", b"shared.bin", "blob-a"),),
        "root-old": (
            (b"100644", b"old-name.bin", "blob-a"),
            (b"40000", b"nested", "subtree"),
        ),
        "root-new": (
            (b"100644", b"new-name.bin", "blob-a"),
            (b"40000", b"nested", "subtree"),
        ),
    }
    historical_aliases = collect_aliases(
        ("root-old", "root-new"), historical_trees, {"blob-a"}
    )

    boundary_sizes = {
        "below-25": 24_999_999,
        "at-25": 25_000_000,
        "at-50": 50_000_000,
        "at-90": 90_000_000,
        "at-100": 100_000_000,
    }
    boundary_aliases = {
        object_sha: {f"{object_sha}.bin".encode("ascii")}
        for object_sha in boundary_sizes
    }
    boundary_receipts = threshold_receipts(
        set(boundary_sizes), boundary_sizes, boundary_aliases
    )

    violation_trees = {
        "leaf": ((b"100644", b"payload.bin", "blob-violation"),),
        "root-one": ((b"100644", b"first.bin", "blob-violation"),),
        "root-two": (
            (b"40000", b"relocated", "leaf"),
            (b"100644", b"second-alias.bin", "blob-violation"),
        ),
    }
    containing = violation_commit_map(
        {"blob-violation"},
        {"commit-one": "root-one", "commit-two": "root-two"},
        violation_trees,
    )["blob-violation"]
    all_containing_rows = containing_commit_rows(containing)
    range_containing_rows = containing_commit_rows(containing, {"commit-two"})

    checks = {
        "canonical_lfs_pointer_accepted": is_lfs_pointer(canonical_pointer),
        "canonical_lfs_pointer_with_extension_accepted": is_lfs_pointer(
            canonical_pointer_with_extension
        ),
        "noncanonical_lfs_pointer_extra_line_rejected": not is_lfs_pointer(
            noncanonical_pointer_extra_line
        ),
        "noncanonical_lfs_pointer_uppercase_oid_rejected": not is_lfs_pointer(
            noncanonical_pointer_uppercase_oid
        ),
        "noncanonical_lfs_pointer_missing_size_rejected": not is_lfs_pointer(
            noncanonical_pointer_missing_size
        ),
        "historical_aliases_cover_rename_and_shared_subtree": historical_aliases
        == {
            "blob-a": {
                b"new-name.bin",
                b"old-name.bin",
                b"nested/shared.bin",
            }
        },
        "threshold_boundaries_are_inclusive": [
            row["ordinary_blob_count"] for row in boundary_receipts
        ]
        == [4, 3, 2, 1],
        "threshold_receipts_are_deterministic": boundary_receipts
        == threshold_receipts(set(boundary_sizes), boundary_sizes, boundary_aliases),
        "violation_containing_commits_are_complete": all_containing_rows
        == [
            {"commit_sha": "commit-one", "alias_paths": ["first.bin"]},
            {
                "commit_sha": "commit-two",
                "alias_paths": ["relocated/payload.bin", "second-alias.bin"],
            },
        ],
        "violation_source_range_filter_is_exact": range_containing_rows
        == [
            {
                "commit_sha": "commit-two",
                "alias_paths": ["relocated/payload.bin", "second-alias.bin"],
            }
        ],
    }
    failures = sorted(name for name, passed in checks.items() if not passed)
    print(
        json.dumps(
            {
                "schema_version": "trace-round16b-reachable-blob-self-check/v1",
                "status": "PASS" if not failures else "FAIL",
                "check_count": len(checks),
                "checks": checks,
                "failure_codes": failures,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inventory all ordinary Git blobs reachable from a Round 16B ref."
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="run deterministic in-memory boundary fixtures and exit",
    )
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--ref")
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    operational_values = (args.repo, args.ref, args.ledger, args.receipt)
    if args.self_check:
        if any(value is not None for value in operational_values):
            parser.error("--self-check cannot be combined with operational arguments")
        return run_self_checks()
    missing_arguments = [
        option
        for option, value in zip(
            ("--repo", "--ref", "--ledger", "--receipt"),
            operational_values,
            strict=True,
        )
        if value is None
    ]
    if missing_arguments:
        parser.error("the following arguments are required: " + ", ".join(missing_arguments))

    assert args.repo is not None
    assert args.ref is not None
    assert args.ledger is not None
    assert args.receipt is not None

    repo = args.repo.resolve()
    ledger_path = args.ledger if args.ledger.is_absolute() else repo / args.ledger
    receipt_path = args.receipt if args.receipt.is_absolute() else repo / args.receipt
    ledger_path = ledger_path.resolve()
    receipt_path = receipt_path.resolve()
    if ledger_path == receipt_path:
        parser.error("--ledger and --receipt must identify different files")

    target_commit = resolve_commit(repo, args.ref)
    target_tree = resolve_tree(repo, target_commit)
    source_commit = resolve_commit(repo, AUTHORIZED_SOURCE_SHA)
    source_tree = resolve_tree(repo, source_commit)
    source_ancestor_result = subprocess.run(
        ("git", "merge-base", "--is-ancestor", source_commit, target_commit),
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if source_ancestor_result.returncode not in (0, 1):
        detail = source_ancestor_result.stderr.decode("utf-8", "replace").strip()
        raise VerificationError(f"git merge-base --is-ancestor failed: {detail}")
    source_is_ancestor = source_ancestor_result.returncode == 0

    target_object_ids = reachable_object_ids(repo, target_commit)
    source_object_ids = reachable_object_ids(repo, source_commit)
    inventory = batch_object_info(repo, target_object_ids)
    object_type_counts = Counter(object_type for object_type, _ in inventory.values())
    commit_ids = {sha for sha, (kind, _) in inventory.items() if kind == "commit"}
    tree_ids = {sha for sha, (kind, _) in inventory.items() if kind == "tree"}
    blob_ids = {sha for sha, (kind, _) in inventory.items() if kind == "blob"}
    blob_sizes = {sha: inventory[sha][1] for sha in blob_ids}

    object_format = git(repo, "rev-parse", "--show-object-format").decode("ascii").strip()
    if object_format not in {"sha1", "sha256"}:
        raise VerificationError(f"unsupported Git object format: {object_format!r}")
    raw_object_bytes = 20 if object_format == "sha1" else 32
    commit_contents = batch_object_contents(repo, commit_ids, "commit")
    commit_trees = commit_root_trees(commit_contents)
    tree_contents = batch_object_contents(repo, tree_ids, "tree")
    trees = {
        tree_sha: parse_tree(content, raw_object_bytes)
        for tree_sha, content in tree_contents.items()
    }
    aliases = collect_aliases(commit_trees.values(), trees, blob_ids)
    missing_alias_ids = sorted(blob_ids - set(aliases))

    pointer_candidates = {
        sha for sha, size in blob_sizes.items() if size <= LFS_POINTER_MAX_BYTES
    }
    pointer_contents = batch_object_contents(repo, pointer_candidates, "blob")
    lfs_pointer_ids = {
        sha for sha, content in pointer_contents.items() if is_lfs_pointer(content)
    }
    ordinary_ids = blob_ids - lfs_pointer_ids
    violation_ids = {
        sha for sha in ordinary_ids if blob_sizes[sha] >= HOSTING_LIMIT_BYTES
    }

    new_object_ids = target_object_ids - source_object_ids
    new_blob_ids = blob_ids & new_object_ids
    new_pointer_ids = lfs_pointer_ids & new_blob_ids
    new_ordinary_ids = ordinary_ids & new_blob_ids
    source_to_ref_commits = commit_ids & new_object_ids

    ledger_lines = [
        "object_sha\tbyte_size\tblob_kind\tintroduced_after_authorized_source\talias_path_json\n"
    ]
    for object_sha in sorted(blob_ids):
        kind = "lfs_pointer" if object_sha in lfs_pointer_ids else "ordinary"
        introduced = "true" if object_sha in new_blob_ids else "false"
        for alias in sorted(aliases.get(object_sha, set())):
            encoded_path = json.dumps(path_text(alias), ensure_ascii=True)
            ledger_lines.append(
                f"{object_sha}\t{blob_sizes[object_sha]}\t{kind}\t{introduced}\t{encoded_path}\n"
            )
    ledger_payload = "".join(ledger_lines).encode("utf-8")
    atomic_write(ledger_path, ledger_payload)
    ledger_row_count = len(ledger_lines) - 1
    total_alias_count = sum(len(paths) for paths in aliases.values())

    maximum_ordinary: dict[str, Any] | None = None
    if ordinary_ids:
        maximum_sha = min(ordinary_ids, key=lambda sha: (-blob_sizes[sha], sha))
        maximum_ordinary = blob_summary(maximum_sha, blob_sizes, aliases)

    violation_commits = violation_commit_map(
        violation_ids,
        commit_trees,
        trees,
    ) if violation_ids else {}
    violations: list[dict[str, Any]] = []
    for object_sha in sorted(violation_ids, key=lambda sha: (-blob_sizes[sha], sha)):
        all_rows = containing_commit_rows(violation_commits[object_sha])
        range_rows = containing_commit_rows(
            violation_commits[object_sha],
            source_to_ref_commits if source_is_ancestor else set(),
        )
        row = blob_summary(object_sha, blob_sizes, aliases)
        row.update(
            {
                "reachable_containing_commit_count": len(all_rows),
                "reachable_containing_commits": all_rows,
                "source_to_ref_containing_commit_count": len(range_rows),
                "source_to_ref_containing_commits": range_rows,
            }
        )
        violations.append(row)

    checks = {
        "authorized_source_is_ancestor_of_target": source_is_ancestor,
        "every_reachable_blob_has_at_least_one_historical_path": not missing_alias_ids,
        "ledger_row_count_matches_blob_path_alias_count": ledger_row_count == total_alias_count,
        "ordinary_blob_hosting_limit_pass": not violation_ids,
    }
    failure_codes = sorted(key for key, passed in checks.items() if not passed)
    new_blob_summaries = [
        {
            "object_sha": sha,
            "bytes": blob_sizes[sha],
            "blob_kind": "lfs_pointer" if sha in lfs_pointer_ids else "ordinary",
            "alias_count": len(aliases.get(sha, set())),
            "alias_paths": path_list(aliases.get(sha, set())),
        }
        for sha in sorted(new_blob_ids)
    ]
    receipt: dict[str, Any] = {
        "schema_version": "trace-round16b-reachable-ordinary-blob-verification/v1",
        "status": "PASS" if not failure_codes else "FAIL",
        "requested_ref": args.ref,
        "resolved_commit_sha": target_commit,
        "resolved_tree_sha": target_tree,
        "git_object_format": object_format,
        "authorized_source": {
            "commit_sha": source_commit,
            "tree_sha": source_tree,
            "is_ancestor_of_target": source_is_ancestor,
        },
        "scope_definition": {
            "reachable_objects": "all Git objects reachable through the target commit and its ancestry",
            "alias": "one distinct blob-object and historical-tree-path pair across all reachable commits",
            "ordinary_blob": "a Git blob that is not a syntactically valid Git LFS v1 pointer",
            "threshold_units": "decimal bytes; comparisons are inclusive",
        },
        "counts": {
            "reachable_object_count": len(target_object_ids),
            "reachable_commit_count": len(commit_ids),
            "reachable_tree_count": len(tree_ids),
            "reachable_blob_count": len(blob_ids),
            "reachable_blob_path_alias_count": total_alias_count,
            "reachable_additional_alias_count": total_alias_count - len(blob_ids),
            "ordinary_blob_count": len(ordinary_ids),
            "lfs_pointer_blob_count": len(lfs_pointer_ids),
            "object_type_counts": dict(sorted(object_type_counts.items())),
        },
        "ledger": {
            "file_name": ledger_path.name,
            "sha256": sha256_bytes(ledger_payload),
            "bytes": len(ledger_payload),
            "data_row_count": ledger_row_count,
            "column_count": 5,
        },
        "maximum_reachable_ordinary_blob": maximum_ordinary,
        "ordinary_blob_thresholds": threshold_receipts(ordinary_ids, blob_sizes, aliases),
        "ordinary_blob_ge_100000000_violation_count": len(violations),
        "ordinary_blob_ge_100000000_violations": violations,
        "lfs_pointer": {
            "blob_count": len(lfs_pointer_ids),
            "blob_path_alias_count": sum(len(aliases[sha]) for sha in lfs_pointer_ids),
            "maximum_pointer_blob_bytes": max(
                (blob_sizes[sha] for sha in lfs_pointer_ids), default=0
            ),
            "object_shas": sorted(lfs_pointer_ids),
        },
        "newly_introduced_since_authorized_source": {
            "definition": "target reachable object set minus authorized-source reachable object set",
            "object_count": len(new_object_ids),
            "commit_count": len(source_to_ref_commits),
            "tree_count": len(tree_ids & new_object_ids),
            "blob_count": len(new_blob_ids),
            "blob_path_alias_count": sum(len(aliases[sha]) for sha in new_blob_ids),
            "ordinary_blob_count": len(new_ordinary_ids),
            "lfs_pointer_blob_count": len(new_pointer_ids),
            "blob_object_shas": sorted(new_blob_ids),
            "blobs": new_blob_summaries,
            "ordinary_blob_thresholds": threshold_receipts(
                new_ordinary_ids, blob_sizes, aliases
            ),
        },
        "missing_historical_path_blob_count": len(missing_alias_ids),
        "missing_historical_path_blob_object_shas": missing_alias_ids,
        "checks": checks,
        "failure_codes": failure_codes,
    }
    receipt_payload = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
    atomic_write(receipt_path, receipt_payload)
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "resolved_commit_sha": target_commit,
                "reachable_object_count": len(target_object_ids),
                "reachable_blob_count": len(blob_ids),
                "reachable_blob_path_alias_count": total_alias_count,
                "ordinary_blob_count": len(ordinary_ids),
                "lfs_pointer_blob_count": len(lfs_pointer_ids),
                "ordinary_blob_ge_100000000_violation_count": len(violations),
                "ledger_sha256": receipt["ledger"]["sha256"],
                "receipt_sha256": sha256_bytes(receipt_payload),
            },
            sort_keys=True,
        )
    )
    return 0 if not failure_codes else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VerificationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
