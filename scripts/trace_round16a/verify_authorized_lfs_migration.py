#!/usr/bin/env python3
"""Verify the one authorized Round 16A Git-LFS history migration.

This verifier is deliberately independent of ``git lfs migrate``.  It consumes
the immutable pre/post evidence captured around the migration, restores the
original bundle into a new temporary repository, and uses Git plumbing plus
SHA-256 reads to prove all of the following:

* the bundle is content-addressed, complete, cleanly restorable, and advertises
  the exact pre-migration branch head;
* the source-to-head history is the same linear eight-commit history with
  identical author/committer/message metadata under the supplied old-to-new
  commit map;
* the only local ref movement is the governed branch, remote main/source refs
  are unchanged, and the remote branch did not exist before migration;
* every mapped tree changes exactly ``.gitattributes`` and whichever of the two
  authorized payload paths existed in that commit;
* every replacement is a canonical LFS pointer whose oid and size equal the
  SHA-256 and byte count of the original bundle payload;
* both current worktree payloads are hydrated and hash to their current pointer
  oids, while no ordinary blob over 100,000,000 bytes remains in the pushed
  source-to-branch range; and
* checkpoint evidence is append-only and no force-push command was recorded.

The verifier performs no fetch, push, migration, ref update, checkout in the
governed repository, or generator import.  Its only repository writes are the
final deterministic receipt and byte-for-byte evidence copies under
``raw/history-migration``.  The clean restore drill is isolated in a temporary
directory and uses ``GIT_LFS_SKIP_SMUDGE=1``.

Input ledger formats
--------------------

``pre/post ref ledger`` (tab-separated, sorted by scope then refname)::

    scope  refname  object_sha

``scope`` is ``LOCAL`` or ``REMOTE``.  Local rows are the complete
``git for-each-ref`` inventory captured immediately before and after the
migration.  The verifier also reconciles the persistent local namespaces
(``refs/heads``, ``refs/tags``, and ``refs/remotes``) against the live
repository; volatile application-owned refs remain covered by the immutable
pre/post comparison without making later verification timing-dependent.
Remote rows are the complete ``git ls-remote --refs`` inventory plus an
explicit governed branch row whose value is ``ABSENT`` when that branch does
not exist.

``pre oversized ledger`` (tab-separated, sorted by path then blob oid)::

    blob_oid  bytes  sha256  path  containing_commits

``containing_commits`` is a comma-separated, oldest-to-newest list of every
Round 16A checkpoint commit whose tree contains that exact path/blob pair.

``old-to-new map`` is the headerless ``OLD-SHA,NEW-SHA`` CSV emitted by
``git lfs migrate import --object-map``.  A conventional OLD-SHA,NEW-SHA header
is accepted.  Checkpoint ledgers use the repository's existing eight-column
format; the post ledger must preserve the complete pre ledger byte-for-byte and
append exactly ``CHECKPOINT-008``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "trace-round16a-authorized-lfs-migration-receipt/v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_REL = Path("docs/audits/v49-exploration-full-space-closure-round1/raw")
OUTPUT_REL = RAW_REL / "authorized-lfs-migration-receipt.json"
HISTORY_REL = RAW_REL / "history-migration"

EXPECTED_COMMIT_COUNT = 8
EXPECTED_PRE_CHECKPOINT_COUNT = 7
ORDINARY_BLOB_LIMIT_BYTES = 100_000_000

BRANCH_REF = "refs/heads/codex/trace-v49-exploration-full-space-closure-round1"
LOCAL_MAIN_REF = "refs/heads/main"
LOCAL_SOURCE_REF = "refs/heads/research/v49-exploration-real-database-round1-20260826"
SOURCE_TAG_REF = "refs/tags/rollback/trace-v49-exploration-full-space-closure-round1-source"
REMOTE_MAIN_REF = "refs/heads/main"
REMOTE_SOURCE_REF = "refs/heads/research/v49-exploration-real-database-round1-20260826"

MIGRATED_PATHS = (
    "docs/audits/v49-exploration-full-space-closure-round1/raw/independent-verification.json",
    "docs/audits/v49-exploration-full-space-closure-round1/raw/independent-verification-cases-v2.tsv",
)
LFS_RULE_LINES = tuple(
    f"{path} filter=lfs diff=lfs merge=lfs -text" for path in MIGRATED_PATHS
)
ALLOWED_TREE_DELTA_PATHS = frozenset((".gitattributes", *MIGRATED_PATHS))

REF_FIELDS = ("scope", "refname", "object_sha")
OVERSIZED_FIELDS = ("blob_oid", "bytes", "sha256", "path", "containing_commits")
CHECKPOINT_FIELDS = (
    "checkpoint_id",
    "phase",
    "commit_sha",
    "timestamp_utc",
    "exact_counts",
    "commands",
    "known_limitations",
    "next_gate",
)

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
FORCE_PUSH = re.compile(
    r"(?i)(?:^|\s)git(?:\s+-\S+)*\s+push\b[^\n]*"
    r"(?:--force(?:-with-lease|-if-includes)?|-f(?:\s|$)|--mirror\b|(?:^|\s)\+\S+)"
)
POINTER = re.compile(
    rb"version https://git-lfs.github.com/spec/v1\n"
    rb"oid sha256:([0-9a-f]{64})\n"
    rb"size ([1-9][0-9]*)\n\Z"
)


class VerificationError(RuntimeError):
    """A stable, machine-readable migration verification failure."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise VerificationError(code)


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_command(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
    input_bytes: bytes | None = None,
) -> tuple[bytes, bytes]:
    completed = subprocess.run(
        list(argv),
        cwd=cwd,
        env=dict(env) if env is not None else None,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode("utf-8", "replace").strip()
        rendered = " ".join(argv)
        raise VerificationError(
            f"COMMAND_FAILED:{rendered}:EXIT_{completed.returncode}:{detail[:400]}"
        )
    return completed.stdout, completed.stderr


def git(repo: Path, *args: str, env: Mapping[str, str] | None = None) -> bytes:
    stdout, _stderr = run_command(("git", *args), cwd=repo, env=env)
    return stdout


def git_text(repo: Path, *args: str, env: Mapping[str, str] | None = None) -> str:
    return git(repo, *args, env=env).decode("utf-8", "strict")


def resolve_commit(repo: Path, value: str) -> str:
    result = git_text(repo, "rev-parse", "--verify", f"{value}^{{commit}}").strip()
    require(SHA40.fullmatch(result) is not None, f"COMMIT_SHA_INVALID:{value}:{result}")
    return result


def git_object_type(repo: Path, oid: str) -> str:
    return git_text(repo, "cat-file", "-t", oid).strip()


def git_object_size(repo: Path, oid: str) -> int:
    value = git_text(repo, "cat-file", "-s", oid).strip()
    try:
        return int(value)
    except ValueError as error:
        raise VerificationError(f"OBJECT_SIZE_INVALID:{oid}:{value}") from error


def git_blob(repo: Path, oid_or_spec: str) -> bytes:
    require(
        git_object_type(repo, oid_or_spec) == "blob",
        f"OBJECT_NOT_BLOB:{oid_or_spec}",
    )
    return git(repo, "cat-file", "blob", oid_or_spec)


def sha256_git_blob(repo: Path, oid: str) -> str:
    process = subprocess.Popen(
        ["git", "cat-file", "blob", oid],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    require(process.stdout is not None, f"BLOB_STREAM_MISSING:{oid}")
    require(process.stderr is not None, f"BLOB_ERROR_STREAM_MISSING:{oid}")
    digest = hashlib.sha256()
    for block in iter(lambda: process.stdout.read(1024 * 1024), b""):
        digest.update(block)
    process.stdout.close()
    stderr = process.stderr.read()
    process.stderr.close()
    returncode = process.wait()
    if returncode != 0:
        detail = stderr.decode("utf-8", "replace").strip()
        raise VerificationError(f"BLOB_READ_FAILED:{oid}:{detail[:400]}")
    return digest.hexdigest()


def range_commits(repo: Path, source_sha: str, head_sha: str) -> list[str]:
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", source_sha, head_sha],
            cwd=repo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0,
        f"SOURCE_NOT_ANCESTOR:{source_sha}:{head_sha}",
    )
    commits = [
        line
        for line in git_text(repo, "rev-list", "--reverse", f"{source_sha}..{head_sha}").splitlines()
        if line
    ]
    require(
        len(commits) == EXPECTED_COMMIT_COUNT,
        f"RANGE_COMMIT_COUNT:{len(commits)}:EXPECTED_{EXPECTED_COMMIT_COUNT}",
    )
    merges = git_text(repo, "rev-list", "--merges", f"{source_sha}..{head_sha}").splitlines()
    require(not merges, f"RANGE_MERGE_COMMIT_COUNT:{len(merges)}")
    expected_parent = source_sha
    for commit in commits:
        parents = git_text(repo, "show", "-s", "--format=%P", commit).strip().split()
        require(parents == [expected_parent], f"NONLINEAR_PARENT:{commit}:{parents}")
        expected_parent = commit
    return commits


def tree_map(repo: Path, commit: str) -> dict[str, tuple[str, str, str]]:
    output = git(repo, "ls-tree", "-r", "-z", "--full-tree", commit)
    result: dict[str, tuple[str, str, str]] = {}
    for record in output.split(b"\0"):
        if not record:
            continue
        try:
            left, raw_path = record.split(b"\t", 1)
            mode, object_type, oid = left.decode("ascii").split(" ")
            path = raw_path.decode("utf-8", "strict")
        except (ValueError, UnicodeDecodeError) as error:
            raise VerificationError(f"LS_TREE_RECORD_INVALID:{record[:200]!r}") from error
        require(path not in result, f"LS_TREE_PATH_DUPLICATE:{commit}:{path}")
        result[path] = (mode, object_type, oid)
    return result


def tree_blob_sizes(repo: Path, commit: str) -> dict[tuple[str, str], int]:
    """Return ``(path, oid) -> bytes`` without one cat-file process per blob."""
    output = git(repo, "ls-tree", "-r", "-l", "-z", "--full-tree", commit)
    result: dict[tuple[str, str], int] = {}
    for record in output.split(b"\0"):
        if not record:
            continue
        try:
            left, raw_path = record.split(b"\t", 1)
            fields = left.decode("ascii").split()
            path = raw_path.decode("utf-8", "strict")
        except (ValueError, UnicodeDecodeError) as error:
            raise VerificationError(f"LS_TREE_SIZE_RECORD_INVALID:{record[:200]!r}") from error
        require(len(fields) == 4, f"LS_TREE_SIZE_FIELD_COUNT:{commit}:{path}:{fields}")
        _mode, object_type, oid, raw_size = fields
        if object_type != "blob":
            continue
        try:
            size = int(raw_size)
        except ValueError as error:
            raise VerificationError(f"LS_TREE_SIZE_INVALID:{commit}:{path}:{raw_size}") from error
        result[(path, oid)] = size
    return result


def commit_metadata(repo: Path, commit: str) -> tuple[tuple[bytes, ...], bytes]:
    raw = git(repo, "cat-file", "commit", commit)
    header, separator, message = raw.partition(b"\n\n")
    require(bool(separator), f"COMMIT_HEADER_SEPARATOR_MISSING:{commit}")
    logical: list[bytes] = []
    for line in header.splitlines():
        if line.startswith(b" "):
            require(bool(logical), f"COMMIT_HEADER_CONTINUATION_ORPHAN:{commit}")
            logical[-1] += b"\n" + line
        else:
            logical.append(line)
    retained: list[bytes] = []
    for field in logical:
        key = field.split(b" ", 1)[0]
        if key in {b"tree", b"parent"}:
            continue
        require(
            key not in {b"gpgsig", b"gpgsig-sha256", b"mergetag"},
            f"SIGNED_OR_MERGETAGGED_COMMIT_UNSUPPORTED:{commit}:{key.decode('ascii')}",
        )
        retained.append(field)
    return tuple(retained), message


def parse_pointer(content: bytes, *, commit: str, path: str) -> tuple[str, int]:
    match = POINTER.fullmatch(content)
    require(match is not None, f"LFS_POINTER_NONCANONICAL:{commit}:{path}")
    assert match is not None
    return match.group(1).decode("ascii"), int(match.group(2))


def parse_ref_ledger(path: Path, label: str) -> dict[tuple[str, str], str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        require(tuple(reader.fieldnames or ()) == REF_FIELDS, f"{label}_HEADER_INVALID")
        rows = list(reader)
    result: dict[tuple[str, str], str] = {}
    observed_order: list[tuple[str, str]] = []
    for row_number, row in enumerate(rows, start=2):
        scope = row["scope"]
        refname = row["refname"]
        object_sha = row["object_sha"]
        require(scope in {"LOCAL", "REMOTE"}, f"{label}_SCOPE_INVALID:{row_number}:{scope}")
        require(refname.startswith("refs/"), f"{label}_REF_INVALID:{row_number}:{refname}")
        require(
            object_sha == "ABSENT" or SHA40.fullmatch(object_sha) is not None,
            f"{label}_OBJECT_INVALID:{row_number}:{object_sha}",
        )
        require(
            not (scope == "LOCAL" and object_sha == "ABSENT"),
            f"{label}_LOCAL_ABSENT_FORBIDDEN:{row_number}:{refname}",
        )
        key = (scope, refname)
        require(key not in result, f"{label}_REF_DUPLICATE:{scope}:{refname}")
        result[key] = object_sha
        observed_order.append(key)
    require(observed_order == sorted(observed_order), f"{label}_NOT_SORTED")
    return result


def current_local_refs(repo: Path) -> dict[tuple[str, str], str]:
    output = git_text(
        repo,
        "for-each-ref",
        "--format=%(refname)%09%(objectname)",
        "refs/heads",
        "refs/tags",
        "refs/remotes",
    )
    result: dict[tuple[str, str], str] = {}
    for line in output.splitlines():
        if not line:
            continue
        try:
            refname, object_sha = line.split("\t", 1)
        except ValueError as error:
            raise VerificationError(f"CURRENT_REF_RECORD_INVALID:{line}") from error
        require(SHA40.fullmatch(object_sha) is not None, f"CURRENT_REF_SHA_INVALID:{line}")
        result[("LOCAL", refname)] = object_sha
    return result


def verify_ref_ledgers(
    *,
    repo: Path,
    pre: dict[tuple[str, str], str],
    post: dict[tuple[str, str], str],
    branch_ref: str,
    old_sha: str,
    new_sha: str,
    source_sha: str,
    local_main_ref: str,
    local_source_ref: str,
    source_tag_ref: str,
    remote_main_ref: str,
    remote_source_ref: str,
    remote_branch_post_state: str,
) -> dict[str, Any]:
    pre_local = {key: value for key, value in pre.items() if key[0] == "LOCAL"}
    post_local = {key: value for key, value in post.items() if key[0] == "LOCAL"}
    require(pre_local.keys() == post_local.keys(), "LOCAL_REF_KEY_SET_CHANGED")
    local_changes = sorted(
        key for key in pre_local if pre_local[key] != post_local[key]
    )
    branch_key = ("LOCAL", branch_ref)
    require(local_changes == [branch_key], f"LOCAL_REF_CHANGE_SCOPE:{local_changes}")
    require(pre_local.get(branch_key) == old_sha, "LOCAL_BRANCH_PRE_SHA_MISMATCH")
    require(post_local.get(branch_key) == new_sha, "LOCAL_BRANCH_POST_SHA_MISMATCH")

    actual_local = current_local_refs(repo)
    persistent_prefixes = ("refs/heads/", "refs/tags/", "refs/remotes/")
    post_persistent_local = {
        key: value
        for key, value in post_local.items()
        if key[1].startswith(persistent_prefixes)
    }
    require(
        actual_local == post_persistent_local,
        "POST_PERSISTENT_LOCAL_REF_LEDGER_NOT_CURRENT",
    )

    for refname, label in (
        (local_main_ref, "LOCAL_MAIN"),
        (local_source_ref, "LOCAL_SOURCE"),
        (source_tag_ref, "SOURCE_TAG"),
    ):
        key = ("LOCAL", refname)
        require(key in pre_local and key in post_local, f"{label}_REF_MISSING")
        require(pre_local[key] == post_local[key], f"{label}_REF_CHANGED")
    require(resolve_commit(repo, local_source_ref) == source_sha, "LOCAL_SOURCE_SHA_CHANGED")
    require(resolve_commit(repo, source_tag_ref) == source_sha, "SOURCE_TAG_SHA_CHANGED")

    pre_remote = {key: value for key, value in pre.items() if key[0] == "REMOTE"}
    post_remote = {key: value for key, value in post.items() if key[0] == "REMOTE"}
    require(pre_remote.keys() == post_remote.keys(), "REMOTE_REF_KEY_SET_CHANGED")
    remote_branch_key = ("REMOTE", branch_ref)
    require(remote_branch_key in pre_remote, "REMOTE_BRANCH_ABSENCE_ROW_MISSING_PRE")
    require(remote_branch_key in post_remote, "REMOTE_BRANCH_ABSENCE_ROW_MISSING_POST")
    require(pre_remote[remote_branch_key] == "ABSENT", "REMOTE_BRANCH_PREEXISTED")
    expected_remote_post = "ABSENT" if remote_branch_post_state == "absent" else new_sha
    require(
        post_remote[remote_branch_key] == expected_remote_post,
        "REMOTE_BRANCH_POST_STATE_MISMATCH",
    )
    remote_changes = sorted(
        key for key in pre_remote if pre_remote[key] != post_remote[key]
    )
    expected_remote_changes = [] if expected_remote_post == "ABSENT" else [remote_branch_key]
    require(
        remote_changes == expected_remote_changes,
        f"REMOTE_REF_CHANGE_SCOPE:{remote_changes}",
    )
    for refname, label in (
        (remote_main_ref, "REMOTE_MAIN"),
        (remote_source_ref, "REMOTE_SOURCE"),
    ):
        key = ("REMOTE", refname)
        require(key in pre_remote and key in post_remote, f"{label}_REF_MISSING")
        require(pre_remote[key] != "ABSENT", f"{label}_REF_ABSENT")
        require(pre_remote[key] == post_remote[key], f"{label}_REF_CHANGED")
    require(
        pre_remote[("REMOTE", remote_source_ref)] == source_sha,
        "REMOTE_SOURCE_SHA_MISMATCH",
    )
    require(
        pre_remote[("REMOTE", remote_main_ref)] == source_sha,
        "REMOTE_MAIN_SHA_MISMATCH",
    )
    return {
        "local_ref_count": len(pre_local),
        "local_changed_ref_count": 1,
        "local_changed_ref": branch_ref,
        "remote_ref_count": len(pre_remote),
        "remote_changed_ref_count": len(expected_remote_changes),
        "remote_branch_pre_state": "ABSENT",
        "remote_branch_post_state": expected_remote_post,
        "local_main_unchanged": True,
        "local_source_unchanged": True,
        "source_tag_unchanged": True,
        "remote_main_unchanged": True,
        "remote_source_unchanged": True,
    }


def parse_object_map(path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row_number, row in enumerate(csv.reader(handle), start=1):
            if not row or not any(cell.strip() for cell in row):
                continue
            require(len(row) == 2, f"OBJECT_MAP_COLUMN_COUNT:{row_number}:{len(row)}")
            old_sha, new_sha = (cell.strip().lower() for cell in row)
            if row_number == 1 and old_sha == "old-sha" and new_sha == "new-sha":
                continue
            require(SHA40.fullmatch(old_sha) is not None, f"OBJECT_MAP_OLD_INVALID:{row_number}")
            require(SHA40.fullmatch(new_sha) is not None, f"OBJECT_MAP_NEW_INVALID:{row_number}")
            rows.append((old_sha, new_sha))
    require(len(rows) == EXPECTED_COMMIT_COUNT, f"OBJECT_MAP_ROW_COUNT:{len(rows)}")
    require(len({old for old, _new in rows}) == len(rows), "OBJECT_MAP_OLD_DUPLICATE")
    require(len({new for _old, new in rows}) == len(rows), "OBJECT_MAP_NEW_DUPLICATE")
    require(all(old != new for old, new in rows), "OBJECT_MAP_IDENTITY_ROW")
    return rows


def parse_oversized_ledger(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        require(tuple(reader.fieldnames or ()) == OVERSIZED_FIELDS, "OVERSIZED_HEADER_INVALID")
        raw_rows = list(reader)
    rows: list[dict[str, Any]] = []
    for row_number, raw in enumerate(raw_rows, start=2):
        oid = raw["blob_oid"]
        sha256 = raw["sha256"]
        path_text = raw["path"]
        containing_commits = raw["containing_commits"].split(",")
        require(SHA40.fullmatch(oid) is not None, f"OVERSIZED_OID_INVALID:{row_number}")
        require(SHA256.fullmatch(sha256) is not None, f"OVERSIZED_SHA256_INVALID:{row_number}")
        require(path_text in MIGRATED_PATHS, f"OVERSIZED_PATH_UNAUTHORIZED:{row_number}:{path_text}")
        require(
            containing_commits
            and all(SHA40.fullmatch(commit) is not None for commit in containing_commits),
            f"OVERSIZED_CONTAINING_COMMITS_INVALID:{row_number}",
        )
        require(
            len(containing_commits) == len(set(containing_commits)),
            f"OVERSIZED_CONTAINING_COMMITS_DUPLICATE:{row_number}",
        )
        try:
            size = int(raw["bytes"])
        except ValueError as error:
            raise VerificationError(f"OVERSIZED_BYTES_INVALID:{row_number}") from error
        require(size > ORDINARY_BLOB_LIMIT_BYTES, f"OVERSIZED_BYTES_NOT_OVER_LIMIT:{row_number}")
        rows.append(
            {
                "blob_oid": oid,
                "bytes": size,
                "sha256": sha256,
                "path": path_text,
                "containing_commits": containing_commits,
            }
        )
    require(len(rows) == 5, f"OVERSIZED_LEDGER_ROW_COUNT:{len(rows)}")
    keys = [(row["path"], row["blob_oid"]) for row in rows]
    require(keys == sorted(keys), "OVERSIZED_LEDGER_NOT_SORTED")
    require(len(set(keys)) == len(keys), "OVERSIZED_LEDGER_DUPLICATE")
    require({row["path"] for row in rows} == set(MIGRATED_PATHS), "OVERSIZED_PATH_SET")
    return rows


def enumerate_oversized(repo: Path, commits: Iterable[str]) -> list[dict[str, Any]]:
    candidates: dict[tuple[str, str], dict[str, Any]] = {}
    for commit in commits:
        for (path, oid), size in tree_blob_sizes(repo, commit).items():
            if size > ORDINARY_BLOB_LIMIT_BYTES:
                record = candidates.setdefault(
                    (path, oid), {"bytes": size, "containing_commits": []}
                )
                require(record["bytes"] == size, f"OVERSIZED_SIZE_UNSTABLE:{path}:{oid}")
                record["containing_commits"].append(commit)
    rows: list[dict[str, Any]] = []
    for (path, oid), record in sorted(candidates.items()):
        rows.append(
            {
                "blob_oid": oid,
                "bytes": record["bytes"],
                "sha256": sha256_git_blob(repo, oid),
                "path": path,
                "containing_commits": record["containing_commits"],
            }
        )
    return rows


def enumerate_reachable_oversized(repo: Path, head_sha: str) -> list[dict[str, Any]]:
    """Enumerate oversized ordinary blobs across the complete reachable history."""
    object_lines = git(repo, "rev-list", "--objects", head_sha)
    batch_stdout, _batch_stderr = run_command(
        (
            "git",
            "cat-file",
            "--batch-check=%(objectname)\t%(objecttype)\t%(objectsize)\t%(rest)",
        ),
        cwd=repo,
        input_bytes=object_lines,
    )
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        batch_stdout.decode("utf-8", "surrogateescape").splitlines(), start=1
    ):
        fields = line.split("\t", 3)
        require(len(fields) == 4, f"REACHABLE_OBJECT_RECORD_INVALID:{line_number}")
        oid, object_type, size_text, path = fields
        if object_type != "blob":
            continue
        try:
            size = int(size_text)
        except ValueError as error:
            raise VerificationError(
                f"REACHABLE_OBJECT_SIZE_INVALID:{line_number}:{size_text}"
            ) from error
        if size > ORDINARY_BLOB_LIMIT_BYTES:
            rows.append({"blob_oid": oid, "bytes": size, "path": path})
    return sorted(rows, key=lambda row: (row["path"], row["blob_oid"]))


def parse_checkpoint_ledger(path: Path, label: str) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        require(tuple(reader.fieldnames or ()) == CHECKPOINT_FIELDS, f"{label}_HEADER_INVALID")
        rows = list(reader)
    for row_number, row in enumerate(rows, start=2):
        require(
            set(row) == set(CHECKPOINT_FIELDS) and all(row[field] is not None for field in CHECKPOINT_FIELDS),
            f"{label}_ROW_INVALID:{row_number}",
        )
        require(SHA40.fullmatch(row["commit_sha"]) is not None, f"{label}_COMMIT_INVALID:{row_number}")
    return rows


def semicolon_metrics(value: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for token in value.split(";"):
        if not token:
            continue
        require("=" in token, f"CHECKPOINT_METRIC_INVALID:{token}")
        key, item = token.split("=", 1)
        normalized = key.strip().upper()
        require(normalized and normalized not in result, f"CHECKPOINT_METRIC_DUPLICATE:{normalized}")
        result[normalized] = item.strip()
    return result


def verify_checkpoint_ledgers(
    *,
    pre_path: Path,
    post_path: Path,
    old_commits: list[str],
    new_sha: str,
) -> dict[str, Any]:
    pre_bytes = pre_path.read_bytes()
    post_bytes = post_path.read_bytes()
    require(pre_bytes.endswith(b"\n"), "PRE_CHECKPOINT_FINAL_NEWLINE_MISSING")
    require(post_bytes.startswith(pre_bytes), "CHECKPOINT_LEDGER_BYTE_PREFIX_CHANGED")
    pre = parse_checkpoint_ledger(pre_path, "PRE_CHECKPOINT")
    post = parse_checkpoint_ledger(post_path, "POST_CHECKPOINT")
    require(len(pre) == EXPECTED_PRE_CHECKPOINT_COUNT, f"PRE_CHECKPOINT_COUNT:{len(pre)}")
    require(len(post) == EXPECTED_PRE_CHECKPOINT_COUNT + 1, f"POST_CHECKPOINT_COUNT:{len(post)}")
    require(post[: len(pre)] == pre, "CHECKPOINT_LEDGER_NOT_APPEND_ONLY")
    require(
        [row["checkpoint_id"] for row in pre]
        == [f"CHECKPOINT-{index:03d}" for index in range(1, 8)],
        "PRE_CHECKPOINT_ID_SEQUENCE",
    )
    require(
        [row["commit_sha"] for row in pre] == old_commits[:7],
        "PRE_CHECKPOINT_COMMIT_SEQUENCE",
    )
    appended = post[-1]
    require(appended["checkpoint_id"] == "CHECKPOINT-008", "POST_CHECKPOINT_ID")
    require(appended["commit_sha"] == new_sha, "POST_CHECKPOINT_COMMIT_SHA")
    require(
        "LFS" in appended["phase"].upper() and "MIGRATION" in appended["phase"].upper(),
        "POST_CHECKPOINT_PHASE",
    )
    require(
        "verify_authorized_lfs_migration.py" in appended["commands"],
        "POST_CHECKPOINT_VERIFIER_COMMAND_MISSING",
    )
    metrics = semicolon_metrics(appended["exact_counts"])
    required_metrics = {
        "HISTORY_REWRITTEN": "true",
        "HISTORY_REWRITE_AUTHORIZED": "true",
        "FORCE_PUSH_USED": "false",
        "MAPPED_COMMIT_COUNT": "8",
        "OVERSIZED_GIT_BLOB_COUNT": "0",
    }
    for name, expected in required_metrics.items():
        require(metrics.get(name, "").lower() == expected, f"POST_CHECKPOINT_METRIC:{name}")
    require(
        "original_history_preserved_in_verified_bundle=true"
        in appended["known_limitations"].lower(),
        "POST_CHECKPOINT_BUNDLE_PRESERVATION_MISSING",
    )
    return {
        "pre_checkpoint_count": len(pre),
        "post_checkpoint_count": len(post),
        "append_only": True,
        "appended_checkpoint_id": appended["checkpoint_id"],
        "appended_checkpoint_commit_sha": appended["commit_sha"],
    }


def parse_bundle_sha_file(path: Path, bundle: Path) -> str:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    require(len(lines) == 1, f"BUNDLE_SHA_LINE_COUNT:{len(lines)}")
    match = re.fullmatch(r"([0-9a-f]{64})[ \t]+[* ]?(.+)", lines[0])
    require(match is not None, "BUNDLE_SHA_FORMAT_INVALID")
    assert match is not None
    recorded = match.group(1)
    referenced = Path(match.group(2)).name
    require(referenced == bundle.name, f"BUNDLE_SHA_FILENAME:{referenced}:{bundle.name}")
    actual = sha256_file(bundle)
    require(actual == recorded, f"BUNDLE_SHA_MISMATCH:{recorded}:{actual}")
    return actual


def parse_bundle_heads(output: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in output.splitlines():
        if not line:
            continue
        try:
            oid, refname = line.split(" ", 1)
        except ValueError as error:
            raise VerificationError(f"BUNDLE_HEAD_RECORD_INVALID:{line}") from error
        require(SHA40.fullmatch(oid) is not None, f"BUNDLE_HEAD_SHA_INVALID:{line}")
        require(refname not in result, f"BUNDLE_HEAD_DUPLICATE:{refname}")
        result[refname] = oid
    return result


def verify_bundle_and_history(
    *,
    repo: Path,
    bundle: Path,
    bundle_sha_file: Path,
    branch_ref: str,
    source_sha: str,
    old_sha: str,
    new_sha: str,
    object_map: list[tuple[str, str]],
    oversized_ledger: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], list[str], list[str]]:
    bundle_sha256 = parse_bundle_sha_file(bundle_sha_file, bundle)
    verify_stdout, verify_stderr = run_command(
        ("git", "bundle", "verify", str(bundle)), cwd=repo
    )
    heads_stdout, _heads_stderr = run_command(
        ("git", "bundle", "list-heads", str(bundle)), cwd=repo
    )
    bundle_heads = parse_bundle_heads(heads_stdout.decode("utf-8", "strict"))
    require(bundle_heads.get(branch_ref) == old_sha, "BUNDLE_BRANCH_HEAD_MISMATCH")
    require(
        set(bundle_heads).issubset({branch_ref, "HEAD"}),
        f"BUNDLE_ADVERTISES_UNEXPECTED_REFS:{sorted(bundle_heads)}",
    )
    if "HEAD" in bundle_heads:
        require(bundle_heads["HEAD"] == old_sha, "BUNDLE_HEAD_PSEUDOREF_MISMATCH")

    new_commits = range_commits(repo, source_sha, new_sha)
    require([new for _old, new in object_map] == new_commits, "OBJECT_MAP_NEW_ORDER")

    with tempfile.TemporaryDirectory(prefix="trace-round16a-lfs-bundle-restore-") as temporary:
        restore = Path(temporary) / "restored"
        restore.mkdir()
        run_command(("git", "init", "--quiet"), cwd=restore)
        restore_env = dict(os.environ)
        restore_env.update(
            {
                "GIT_LFS_SKIP_SMUDGE": "1",
                "GIT_TERMINAL_PROMPT": "0",
            }
        )
        run_command(
            (
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "fetch",
                "--quiet",
                "--no-tags",
                str(bundle),
                branch_ref,
            ),
            cwd=restore,
            env=restore_env,
        )
        run_command(
            (
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "checkout",
                "--quiet",
                "--detach",
                old_sha,
            ),
            cwd=restore,
            env=restore_env,
        )
        restored_head = resolve_commit(restore, "HEAD")
        require(restored_head == old_sha, "RESTORE_HEAD_MISMATCH")
        restored_status = git_text(
            restore, "status", "--porcelain=v1", "--untracked-files=all", env=restore_env
        ).splitlines()
        require(not restored_status, f"RESTORE_WORKTREE_DIRTY:{restored_status}")
        fsck_stdout, fsck_stderr = run_command(
            ("git", "fsck", "--full", "--strict", "--no-reflogs"), cwd=restore
        )
        old_commits = range_commits(restore, source_sha, old_sha)
        require([old for old, _new in object_map] == old_commits, "OBJECT_MAP_OLD_ORDER")
        restored_oversized = enumerate_oversized(restore, old_commits)
        require(restored_oversized == oversized_ledger, "PRE_OVERSIZED_LEDGER_MISMATCH")

        source_tree_old = git_text(restore, "rev-parse", f"{source_sha}^{{tree}}").strip()
        source_tree_new = git_text(repo, "rev-parse", f"{source_sha}^{{tree}}").strip()
        require(source_tree_old == source_tree_new, "SOURCE_TREE_CHANGED")

        payload_lookup = {
            (row["path"], row["blob_oid"]): row for row in restored_oversized
        }
        observed_pointer_versions: dict[tuple[str, str], dict[str, Any]] = {}
        per_commit_deltas: list[dict[str, Any]] = []
        for index, (old_commit, new_commit) in enumerate(object_map, start=1):
            require(
                commit_metadata(restore, old_commit) == commit_metadata(repo, new_commit),
                f"COMMIT_METADATA_CHANGED:{old_commit}:{new_commit}",
            )
            old_tree = tree_map(restore, old_commit)
            new_tree = tree_map(repo, new_commit)
            changed_paths = sorted(
                path
                for path in old_tree.keys() | new_tree.keys()
                if old_tree.get(path) != new_tree.get(path)
            )
            expected_changes = {".gitattributes"}
            expected_changes.update(path for path in MIGRATED_PATHS if path in old_tree)
            require(
                set(changed_paths) == expected_changes,
                f"TREE_DELTA_SCOPE:{old_commit}:{new_commit}:{changed_paths}",
            )
            require(
                set(changed_paths).issubset(ALLOWED_TREE_DELTA_PATHS),
                f"TREE_DELTA_UNAUTHORIZED:{new_commit}",
            )
            old_attributes = git_blob(restore, f"{old_commit}:.gitattributes")
            new_attributes = git_blob(repo, f"{new_commit}:.gitattributes")
            old_lines = old_attributes.decode("utf-8", "strict").splitlines()
            new_lines = new_attributes.decode("utf-8", "strict").splitlines()
            require(
                new_lines == [*old_lines, *LFS_RULE_LINES],
                f"GITATTRIBUTES_DELTA_INVALID:{new_commit}",
            )
            for migrated_path in MIGRATED_PATHS:
                old_entry = old_tree.get(migrated_path)
                new_entry = new_tree.get(migrated_path)
                require((old_entry is None) == (new_entry is None), f"MIGRATED_PATH_EXISTENCE:{new_commit}:{migrated_path}")
                attributes = git_text(
                    repo,
                    "check-attr",
                    f"--source={new_commit}",
                    "filter",
                    "diff",
                    "merge",
                    "text",
                    "--",
                    migrated_path,
                )
                values: dict[str, str] = {}
                for line in attributes.splitlines():
                    _path, attribute, value = line.rsplit(": ", 2)
                    values[attribute] = value
                require(
                    values == {"filter": "lfs", "diff": "lfs", "merge": "lfs", "text": "unset"},
                    f"GITATTRIBUTES_RESOLUTION:{new_commit}:{migrated_path}:{values}",
                )
                if old_entry is None:
                    continue
                old_mode, old_type, old_oid = old_entry
                new_mode, new_type, new_oid = new_entry or ("", "", "")
                require(old_mode == new_mode and old_type == new_type == "blob", f"MIGRATED_PATH_MODE:{new_commit}:{migrated_path}")
                payload = payload_lookup.get((migrated_path, old_oid))
                require(payload is not None, f"ORIGINAL_PAYLOAD_LEDGER_MISSING:{old_oid}:{migrated_path}")
                pointer_oid, pointer_size = parse_pointer(
                    git_blob(repo, new_oid), commit=new_commit, path=migrated_path
                )
                assert payload is not None
                require(pointer_oid == payload["sha256"], f"POINTER_OID_MISMATCH:{new_commit}:{migrated_path}")
                require(pointer_size == payload["bytes"], f"POINTER_SIZE_MISMATCH:{new_commit}:{migrated_path}")
                observed_pointer_versions[(migrated_path, pointer_oid)] = {
                    "path": migrated_path,
                    "oid_sha256": pointer_oid,
                    "bytes": pointer_size,
                    "pointer_blob_oid": new_oid,
                }
            per_commit_deltas.append(
                {
                    "ordinal": index,
                    "old_commit": old_commit,
                    "new_commit": new_commit,
                    "changed_paths": changed_paths,
                }
            )

        require(len(observed_pointer_versions) == 5, f"POINTER_VERSION_COUNT:{len(observed_pointer_versions)}")
        remaining_oversized = enumerate_oversized(repo, new_commits)
        require(not remaining_oversized, f"POST_MIGRATION_RANGE_OVERSIZED_BLOBS:{remaining_oversized}")
        reachable_oversized = enumerate_reachable_oversized(repo, new_sha)
        require(
            not reachable_oversized,
            f"POST_MIGRATION_REACHABLE_OVERSIZED_BLOBS:{reachable_oversized}",
        )
        reachable_commit_count = len(git_text(repo, "rev-list", new_sha).splitlines())

        restore_summary = {
            "status": "PASS",
            "head_sha": restored_head,
            "head_tree_sha": git_text(restore, "rev-parse", f"{old_sha}^{{tree}}").strip(),
            "source_tree_sha": source_tree_old,
            "clean_worktree": True,
            "commit_count": len(old_commits),
            "merge_commit_count": 0,
            "oversized_blob_count": len(restored_oversized),
            "oversized_objects": restored_oversized,
            "git_fsck": "PASS",
            "git_fsck_stdout_sha256": hashlib.sha256(fsck_stdout).hexdigest(),
            "git_fsck_stderr_sha256": hashlib.sha256(fsck_stderr).hexdigest(),
        }
        topology_summary = {
            "status": "PASS",
            "mapped_commit_count": len(object_map),
            "old_commit_count": len(old_commits),
            "new_commit_count": len(new_commits),
            "metadata_match_count": len(object_map),
            "linear_history": True,
            "source_tree_unchanged": True,
            "per_commit_tree_deltas": per_commit_deltas,
            "authorized_tree_delta_paths": sorted(ALLOWED_TREE_DELTA_PATHS),
            "pointer_versions": sorted(
                observed_pointer_versions.values(),
                key=lambda row: (row["path"], row["oid_sha256"]),
            ),
            "pointer_version_count": len(observed_pointer_versions),
            "post_migration_ordinary_blob_over_limit_count": 0,
            "post_migration_ordinary_blob_scope": "ALL_HISTORY_REACHABLE_FROM_REWRITTEN_BRANCH",
            "reachable_commit_count": reachable_commit_count,
        }

    bundle_summary = {
        "status": "PASS",
        "filename": bundle.name,
        "local_path": str(bundle),
        "bytes": bundle.stat().st_size,
        "sha256": bundle_sha256,
        "sha256_file": bundle_sha_file.name,
        "advertised_refs": dict(sorted(bundle_heads.items())),
        "bundle_verify": "PASS",
        "bundle_verify_stdout_sha256": hashlib.sha256(verify_stdout).hexdigest(),
        "bundle_verify_stderr_sha256": hashlib.sha256(verify_stderr).hexdigest(),
        "complete_clean_restore": True,
    }
    return bundle_summary, {"restore": restore_summary, "topology": topology_summary}, old_commits, new_commits


def verify_hydrated_current_payloads(repo: Path, new_sha: str) -> list[dict[str, Any]]:
    require(resolve_commit(repo, "HEAD") == new_sha, "WORKTREE_HEAD_NOT_NEW_REF")
    entries = tree_map(repo, new_sha)
    result: list[dict[str, Any]] = []
    for migrated_path in MIGRATED_PATHS:
        entry = entries.get(migrated_path)
        require(entry is not None, f"CURRENT_POINTER_PATH_MISSING:{migrated_path}")
        _mode, object_type, pointer_blob_oid = entry or ("", "", "")
        require(object_type == "blob", f"CURRENT_POINTER_NOT_BLOB:{migrated_path}")
        oid_sha256, expected_bytes = parse_pointer(
            git_blob(repo, pointer_blob_oid), commit=new_sha, path=migrated_path
        )
        hydrated = (repo / migrated_path).resolve()
        require(hydrated.is_relative_to(repo), f"HYDRATED_PATH_ESCAPES_REPO:{migrated_path}")
        require(hydrated.is_file(), f"HYDRATED_FILE_MISSING:{migrated_path}")
        actual_bytes = hydrated.stat().st_size
        actual_sha256 = sha256_file(hydrated)
        require(actual_bytes == expected_bytes, f"HYDRATED_SIZE_MISMATCH:{migrated_path}")
        require(actual_sha256 == oid_sha256, f"HYDRATED_HASH_MISMATCH:{migrated_path}")
        result.append(
            {
                "path": migrated_path,
                "bytes": actual_bytes,
                "sha256": actual_sha256,
                "pointer_blob_oid": pointer_blob_oid,
            }
        )
    return result


def force_push_command_count(repo: Path) -> int:
    commands: list[str] = []
    events_path = repo / RAW_REL / "execution-events.jsonl"
    if events_path.is_file():
        for line_number, line in enumerate(events_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise VerificationError(f"EXECUTION_EVENT_JSON_INVALID:{line_number}") from error
            command = event.get("command")
            require(isinstance(command, str), f"EXECUTION_EVENT_COMMAND_INVALID:{line_number}")
            commands.append(command)
    ledger_path = repo / RAW_REL / "command-ledger.tsv"
    if ledger_path.is_file():
        with ledger_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            require(reader.fieldnames is not None and "command" in reader.fieldnames, "COMMAND_LEDGER_HEADER_INVALID")
            commands.extend(row["command"] for row in reader)
    return sum(1 for command in commands if FORCE_PUSH.search(command))


def write_atomically(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def copy_evidence_once(source: Path, destination: Path) -> dict[str, Any]:
    content = source.read_bytes()
    if destination.exists():
        require(destination.is_file(), f"EVIDENCE_DESTINATION_NOT_FILE:{destination}")
        require(destination.read_bytes() == content, f"EVIDENCE_COPY_IMMUTABILITY:{destination.name}")
    else:
        write_atomically(destination, content)
    return {
        "path": destination.as_posix(),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO_ROOT)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--bundle-sha256", type=Path, required=True)
    parser.add_argument("--pre-ref-ledger", type=Path, required=True)
    parser.add_argument("--post-ref-ledger", type=Path, required=True)
    parser.add_argument("--pre-checkpoint-ledger", type=Path, required=True)
    parser.add_argument("--post-checkpoint-ledger", type=Path, required=True)
    parser.add_argument("--object-map", type=Path, required=True)
    parser.add_argument("--pre-oversized-ledger", type=Path, required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--old-ref", required=True)
    parser.add_argument("--new-ref", required=True)
    parser.add_argument("--branch-ref", default=BRANCH_REF)
    parser.add_argument("--local-main-ref", default=LOCAL_MAIN_REF)
    parser.add_argument("--local-source-ref", default=LOCAL_SOURCE_REF)
    parser.add_argument("--source-tag-ref", default=SOURCE_TAG_REF)
    parser.add_argument("--remote-main-ref", default=REMOTE_MAIN_REF)
    parser.add_argument("--remote-source-ref", default=REMOTE_SOURCE_REF)
    parser.add_argument(
        "--remote-branch-post-state",
        choices=("absent", "new"),
        default="absent",
        help="Expected remote branch state in the post-ref ledger.",
    )
    return parser.parse_args()


def verify(args: argparse.Namespace) -> dict[str, Any]:
    repo = args.repo.resolve()
    require(repo.is_dir(), f"REPO_NOT_DIRECTORY:{repo}")
    require(resolve_commit(repo, args.new_ref) == resolve_commit(repo, args.branch_ref), "NEW_REF_NOT_BRANCH_HEAD")
    source_sha = resolve_commit(repo, args.source_ref)
    new_sha = resolve_commit(repo, args.new_ref)
    old_sha = args.old_ref.lower()
    if SHA40.fullmatch(old_sha) is None:
        old_sha = resolve_commit(repo, args.old_ref)

    inputs = {
        "bundle": args.bundle.resolve(),
        "bundle_sha256": args.bundle_sha256.resolve(),
        "pre_ref_ledger": args.pre_ref_ledger.resolve(),
        "post_ref_ledger": args.post_ref_ledger.resolve(),
        "pre_checkpoint_ledger": args.pre_checkpoint_ledger.resolve(),
        "post_checkpoint_ledger": args.post_checkpoint_ledger.resolve(),
        "object_map": args.object_map.resolve(),
        "pre_oversized_ledger": args.pre_oversized_ledger.resolve(),
    }
    for label, path in inputs.items():
        require(path.is_file(), f"INPUT_FILE_MISSING:{label}:{path}")

    pre_refs = parse_ref_ledger(inputs["pre_ref_ledger"], "PRE_REF")
    post_refs = parse_ref_ledger(inputs["post_ref_ledger"], "POST_REF")
    object_map = parse_object_map(inputs["object_map"])
    oversized = parse_oversized_ledger(inputs["pre_oversized_ledger"])

    refs_summary = verify_ref_ledgers(
        repo=repo,
        pre=pre_refs,
        post=post_refs,
        branch_ref=args.branch_ref,
        old_sha=old_sha,
        new_sha=new_sha,
        source_sha=source_sha,
        local_main_ref=args.local_main_ref,
        local_source_ref=args.local_source_ref,
        source_tag_ref=args.source_tag_ref,
        remote_main_ref=args.remote_main_ref,
        remote_source_ref=args.remote_source_ref,
        remote_branch_post_state=args.remote_branch_post_state,
    )
    bundle_summary, history_summary, old_commits, new_commits = verify_bundle_and_history(
        repo=repo,
        bundle=inputs["bundle"],
        bundle_sha_file=inputs["bundle_sha256"],
        branch_ref=args.branch_ref,
        source_sha=source_sha,
        old_sha=old_sha,
        new_sha=new_sha,
        object_map=object_map,
        oversized_ledger=oversized,
    )
    checkpoint_summary = verify_checkpoint_ledgers(
        pre_path=inputs["pre_checkpoint_ledger"],
        post_path=inputs["post_checkpoint_ledger"],
        old_commits=old_commits,
        new_sha=new_sha,
    )
    hydrated = verify_hydrated_current_payloads(repo, new_sha)
    force_count = force_push_command_count(repo)
    require(force_count == 0, f"FORCE_PUSH_COMMAND_COUNT:{force_count}")
    git_fsck_stdout, git_fsck_stderr = run_command(
        ("git", "fsck", "--full", "--strict", "--no-dangling"), cwd=repo
    )
    lfs_fsck_range = f"{source_sha}..{new_sha}"
    lfs_fsck_stdout, lfs_fsck_stderr = run_command(
        ("git", "lfs", "fsck", lfs_fsck_range), cwd=repo
    )

    history_dir = repo / HISTORY_REL
    copies: dict[str, dict[str, Any]] = {}
    copy_names = {
        "bundle_sha256": "original-bundle.sha256",
        "pre_ref_ledger": "pre-ref-ledger.tsv",
        "post_ref_ledger": "post-ref-ledger.tsv",
        "pre_checkpoint_ledger": "pre-checkpoint-ledger.tsv",
        "post_checkpoint_ledger": "post-checkpoint-ledger.tsv",
        "object_map": "old-to-new-object-map.csv",
        "pre_oversized_ledger": "pre-oversized-blobs.tsv",
    }
    for label, filename in copy_names.items():
        record = copy_evidence_once(inputs[label], history_dir / filename)
        record["path"] = (HISTORY_REL / filename).as_posix()
        copies[label] = record

    material: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "authorized_lfs_migration": "PASS",
        "source_sha": source_sha,
        "source_tree_sha": history_summary["restore"]["source_tree_sha"],
        "old_head_sha": old_sha,
        "new_head_sha": new_sha,
        "branch_ref": args.branch_ref,
        "branch": args.branch_ref.removeprefix("refs/heads/"),
        "migrated_paths": sorted(MIGRATED_PATHS),
        "HISTORY_REWRITTEN": True,
        "HISTORY_REWRITE_AUTHORIZED": True,
        "HISTORY_REWRITE_SCOPE_EXACT": True,
        "FORCE_PUSH_USED": False,
        "NETWORK_REQUEST_COUNT": 0,
        "bundle": bundle_summary,
        "restore_drill": history_summary["restore"],
        "topology": history_summary["topology"],
        "refs": refs_summary,
        "checkpoint_ledger": checkpoint_summary,
        "hydrated_current_payloads": hydrated,
        "current_repository_fsck": {
            "git_fsck": "PASS",
            "git_fsck_stdout_sha256": hashlib.sha256(git_fsck_stdout).hexdigest(),
            "git_fsck_stderr_sha256": hashlib.sha256(git_fsck_stderr).hexdigest(),
            "lfs_fsck": "PASS",
            "lfs_fsck_scope": lfs_fsck_range,
            "lfs_fsck_stdout_sha256": hashlib.sha256(lfs_fsck_stdout).hexdigest(),
            "lfs_fsck_stderr_sha256": hashlib.sha256(lfs_fsck_stderr).hexdigest(),
        },
        "copied_evidence": copies,
        "receipt": {
            "AUTHORIZED_LFS_MIGRATION": "PASS",
            "HISTORY_REWRITTEN": True,
            "HISTORY_REWRITE_AUTHORIZED": True,
            "HISTORY_REWRITE_SCOPE_EXACT": True,
            "UNPUBLISHED_ROUND16A_HISTORY_REWRITTEN": True,
            "PUBLIC_EXISTING_HISTORY_REWRITTEN": False,
            "ORIGIN_MAIN_REWRITTEN": False,
            "FORCE_PUSH_USED": False,
            "REMOTE_BRANCH_EXISTED_BEFORE_MIGRATION": False,
            "SOURCE_SHA_PRESERVED": True,
            "SOURCE_TREE_SHA_PRESERVED": True,
            "CHECKPOINT_SEQUENCE_PRESERVED": True,
            "REWRITE_NONALLOWLIST_PATH_COUNT": 0,
            "ORIGIN_MAIN_BEFORE_SHA": source_sha,
            "ORIGIN_MAIN_AFTER_SHA": source_sha,
            "PUBLIC_REMOTE_REF_MAP_HASH_MATCH": True,
            "LFS_POINTER_VALIDATION": "PASS",
            "HYDRATED_PAYLOAD_HASH_MATCH": True,
            "GIT_FSCK": "PASS",
            "LFS_FSCK": "PASS",
            "ORDINARY_OVERSIZED_BLOB_COUNT_AFTER": 0,
            "ROUND16A_MAPPED_COMMIT_COUNT_BEFORE": len(old_commits),
            "ROUND16A_MAPPED_COMMIT_COUNT_AFTER": len(new_commits),
            "ORIGINAL_CHECKPOINT_COUNT_BEFORE": checkpoint_summary["pre_checkpoint_count"],
            "ORIGINAL_CHECKPOINT_COUNT_AFTER": checkpoint_summary["pre_checkpoint_count"],
            "POST_MIGRATION_CHECKPOINT_APPEND_COUNT": (
                checkpoint_summary["post_checkpoint_count"]
                - checkpoint_summary["pre_checkpoint_count"]
            ),
        },
        "metrics": {
            "AUTHORIZED_LFS_MIGRATION": "PASS",
            "HISTORY_REWRITTEN": True,
            "HISTORY_REWRITE_AUTHORIZED": True,
            "HISTORY_REWRITE_SCOPE_EXACT": True,
            "UNPUBLISHED_ROUND16A_HISTORY_REWRITTEN": True,
            "PUBLIC_EXISTING_HISTORY_REWRITTEN": False,
            "ORIGIN_MAIN_REWRITTEN": False,
            "FORCE_PUSH_USED": False,
            "NETWORK_REQUEST_COUNT": 0,
            "MAPPED_COMMIT_COUNT": len(object_map),
            "PRE_MIGRATION_OVERSIZED_GIT_BLOB_COUNT": len(oversized),
            "POST_MIGRATION_OVERSIZED_GIT_BLOB_COUNT": 0,
            "AUTHORIZED_LFS_PATH_COUNT": len(MIGRATED_PATHS),
            "LFS_POINTER_VERSION_COUNT": history_summary["topology"]["pointer_version_count"],
            "HYDRATED_CURRENT_PAYLOAD_HASH_MATCH_COUNT": len(hydrated),
            "LOCAL_UNAUTHORIZED_REF_CHANGE_COUNT": 0,
            "REMOTE_UNAUTHORIZED_REF_CHANGE_COUNT": 0,
            "UNAUTHORIZED_TREE_DELTA_COUNT": 0,
            "FORCE_PUSH_COMMAND_COUNT": force_count,
        },
    }
    material["receipt_hash"] = canonical_hash(material)
    return material


def failure_receipt(error: Exception) -> dict[str, Any]:
    code = str(error) if isinstance(error, VerificationError) else f"INTERNAL_ERROR:{type(error).__name__}:{error}"
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "FAIL",
        "authorized_lfs_migration": "FAIL",
        "error_codes": [code],
    }


def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    output = repo / OUTPUT_REL
    try:
        receipt = verify(args)
        exit_code = 0
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, VerificationError) as error:
        receipt = failure_receipt(error)
        exit_code = 1
    content = canonical_bytes(receipt)
    try:
        write_atomically(output, content)
    except OSError as error:
        print(f"AUTHORIZED_LFS_MIGRATION_RECEIPT_WRITE_FAILED:{error}", file=sys.stderr)
        return 1
    summary = {
        "status": receipt["status"],
        "output": OUTPUT_REL.as_posix(),
        "output_sha256": hashlib.sha256(content).hexdigest(),
    }
    if exit_code:
        summary["error_codes"] = receipt.get("error_codes", [])
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
