#!/usr/bin/env python3
"""Reproduce and compare the complete deterministic Round 16A semantic space.

This driver is intentionally an orchestrator, not a second generator.  The
caller creates a new Git worktree at the final Round 16A commit and passes its
path here.  The driver then:

* proves that the primary and reproduction roots are distinct worktrees for
  the same repository and are both at the requested final commit;
* rebuilds the vocabulary and pair universes;
* rebuilds the frozen Crossref query log using ``--merge-only`` (there is no
  HTTP capture path in this mode);
* rebuilds the association census/graph and the complete finite exploration
  space; and
* invokes the independent verifier as a separate process, without importing
  any generator enumeration function.

Only deterministic semantic/census artifacts are compared.  The two measured
performance receipts and the vocabulary builder's historical research-note
side effects are restored byte-for-byte before the final clean-worktree gate.
The final receipt is written in the primary worktree so the isolated
reproduction worktree can finish clean.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Sequence


SOURCE_SHA = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e"
SCHEMA_VERSION = "trace-exploration-round16a-reproducibility-verification-v2"
REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_REL = Path("docs/audits/v49-exploration-full-space-closure-round1")
RAW_REL = AUDIT_REL / "raw"
RESEARCH_REL = Path("docs/research/trace-v49-exploration-full-space-closure-round1")
MODEL_REL = Path("frontend/generated/trace-exploration-v2/production-read-model.json")
DEFAULT_OUTPUT_REL = RAW_REL / "reproducibility-verification.json"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
NETWORK_GUARD_SOURCE = b"""\
import sys

_DENIED_EVENTS = {
    "socket.connect",
    "socket.getaddrinfo",
    "socket.gethostbyaddr",
    "socket.gethostbyname",
    "socket.gethostbyname_ex",
}


def _deny_network(event, _arguments):
    if event in _DENIED_EVENTS:
        raise RuntimeError("TRACE_ROUND16A_REPRODUCTION_NETWORK_DENIED:" + event)


sys.addaudithook(_deny_network)
"""


# Each required public receipt flag governs a group, rather than a hand-picked
# single file.  A group passes only when every deterministic artifact in that
# stage has the same bytes in both worktrees.
ARTIFACT_GROUPS: dict[str, tuple[Path, ...]] = {
    "VOCABULARY_CENSUS_HASH_MATCH": (
        RAW_REL / "vocabulary-candidate-universe-v2.json",
        RAW_REL / "vocabulary-candidate-universe-v2.tsv",
        RAW_REL / "vocabulary-census-v2.json",
        RAW_REL / "vocabulary-census-v2.tsv",
        RAW_REL / "future-vocabulary-candidates.tsv",
        RAW_REL / "active-vocabulary-v2.json",
    ),
    "PAIR_CENSUS_HASH_MATCH": (
        RAW_REL / "pair-universe-v2.json",
        RAW_REL / "pair-universe-v2.tsv",
        RAW_REL / "association-query-log-v2.jsonl",
        RAW_REL / "association-census-v2.json",
        RAW_REL / "association-census-v2.tsv",
        RAW_REL / "association-evidence-ledger-v2.tsv",
        RAW_REL / "association-build-summary-v2.json",
    ),
    "GRAPH_HASH_MATCH": (
        RAW_REL / "validated-association-graph-v2.json",
        RAW_REL / "graph-statistics-v2.json",
    ),
    "COMPOSITION_REGISTRY_HASH_MATCH": (
        RAW_REL / "exploration-parameter-universe-v2.json",
        RAW_REL / "composition-enumeration-v2.tsv",
        RAW_REL / "composition-rejection-ledger-v2.tsv",
        RAW_REL / "canonical-composition-registry-v2.json",
        RAW_REL / "composition-statistics-v2.json",
        RAW_REL / "category-entry-census-v2.tsv",
    ),
    "STATE_CENSUS_HASH_MATCH": (RAW_REL / "state-census-v2.tsv",),
    "TRANSITION_CENSUS_HASH_MATCH": (RAW_REL / "transition-census-v2.tsv",),
    "WORKFLOW_CENSUS_HASH_MATCH": (RAW_REL / "workflow-census-v2.tsv",),
    "EXPORT_CENSUS_HASH_MATCH": (RAW_REL / "export-census-v2.tsv",),
}


# These additional deterministic groups make the broad "all deterministic
# artifacts" requirement fail closed while preserving the eight named public
# hash gates above.
ADDITIONAL_GROUPS: dict[str, tuple[Path, ...]] = {
    "FROZEN_AUTHORITY_INPUT_HASH_MATCH": (
        RAW_REL / "category-authority-v2.tsv",
        RAW_REL / "database-identity-v2.json",
    ),
    "PRODUCTION_READ_MODEL_HASH_MATCH": (
        MODEL_REL,
        RAW_REL / "production-read-model-metadata-v2.json",
        RAW_REL / "space-generation-summary-v2.json",
    ),
    "INDEPENDENT_VERIFICATION_HASH_MATCH": (
        RAW_REL / "independent-verification.json",
        RAW_REL / "independent-verification-cases-v2.tsv",
        RAW_REL / "quantitative-audit.json",
        RAW_REL / "headline-numbers.json",
        RAW_REL / "metric-dictionary.json",
    ),
}


NONDETERMINISTIC_SIDE_EFFECTS = (
    RAW_REL / "association-build-performance-v2.json",
    RAW_REL / "space-generation-performance-v2.json",
)


# The vocabulary census builder historically writes these two notes.  The
# final Round 16A report builder later assigns those names to other reports, so
# reproduction restores their final committed bytes after verifying the raw
# vocabulary artifacts.
HISTORICAL_NOTE_SIDE_EFFECTS = (
    RESEARCH_REL / "06_VOCABULARY_CENSUS.md",
    RESEARCH_REL / "07_VOCABULARY_DISPOSITION_RECONCILIATION.md",
)


QUERY_CACHE_REL = RAW_REL / "association-query-cache-v2"
QUERY_SHARDS_REL = RAW_REL / "association-query-shards-v2"
QUERY_SHARDS = tuple(
    QUERY_SHARDS_REL / f"batch-{index:03d}.jsonl" for index in range(1, 7)
)


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


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def git_result(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )


def git(root: Path, *args: str) -> str:
    completed = git_result(root, *args)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"GIT_COMMAND_FAILED:{' '.join(args)}:{detail}")
    return completed.stdout.strip()


def git_path(root: Path, *args: str) -> Path:
    value = Path(git(root, *args))
    return (value if value.is_absolute() else root / value).resolve()


def git_status(root: Path, paths: Sequence[Path] | None = None) -> list[str]:
    arguments = ["status", "--porcelain=v1", "--untracked-files=all"]
    if paths:
        arguments.extend(["--", *(path.as_posix() for path in paths)])
    output = git(root, *arguments)
    return output.splitlines() if output else []


def manifest_for_paths(root: Path, paths: Iterable[Path]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    missing: list[str] = []
    for relative in sorted(set(paths), key=lambda path: path.as_posix()):
        path = root / relative
        if not path.is_file():
            missing.append(relative.as_posix())
            continue
        entries.append(
            {
                "path": relative.as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    material = {"files": entries, "missing": missing}
    return {
        **material,
        "file_count": len(entries),
        "total_bytes": sum(entry["bytes"] for entry in entries),
        "manifest_hash": canonical_hash(material),
    }


def manifest_for_tree(root: Path, relative: Path) -> dict[str, Any]:
    directory = root / relative
    if not directory.is_dir():
        return {
            "files": [],
            "missing": [relative.as_posix()],
            "file_count": 0,
            "total_bytes": 0,
            "manifest_hash": canonical_hash(
                {"files": [], "missing": [relative.as_posix()]}
            ),
        }
    paths = (
        path.relative_to(root)
        for path in directory.rglob("*")
        if path.is_file() and not path.name.endswith(".lock")
    )
    return manifest_for_paths(root, paths)


def compare_manifests(
    primary_root: Path, reproduction_root: Path, paths: Iterable[Path]
) -> dict[str, Any]:
    primary = manifest_for_paths(primary_root, paths)
    reproduction = manifest_for_paths(reproduction_root, paths)
    primary_by_path = {row["path"]: row for row in primary["files"]}
    reproduction_by_path = {row["path"]: row for row in reproduction["files"]}
    all_paths = sorted(set(primary_by_path) | set(reproduction_by_path))
    mismatches = [
        {
            "path": path,
            "primary": primary_by_path.get(path),
            "reproduction": reproduction_by_path.get(path),
        }
        for path in all_paths
        if primary_by_path.get(path) != reproduction_by_path.get(path)
    ]
    match = not primary["missing"] and not reproduction["missing"] and not mismatches
    return {
        "match": match,
        "primary_manifest_hash": primary["manifest_hash"],
        "reproduction_manifest_hash": reproduction["manifest_hash"],
        "file_count": primary["file_count"],
        "total_bytes": primary["total_bytes"],
        "primary_missing": primary["missing"],
        "reproduction_missing": reproduction["missing"],
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "files": primary["files"],
    }


def compare_tree(
    primary_root: Path, reproduction_root: Path, relative: Path
) -> dict[str, Any]:
    primary = manifest_for_tree(primary_root, relative)
    reproduction = manifest_for_tree(reproduction_root, relative)
    primary_by_path = {row["path"]: row for row in primary["files"]}
    reproduction_by_path = {row["path"]: row for row in reproduction["files"]}
    paths = sorted(set(primary_by_path) | set(reproduction_by_path))
    mismatches = [
        {
            "path": path,
            "primary": primary_by_path.get(path),
            "reproduction": reproduction_by_path.get(path),
        }
        for path in paths
        if primary_by_path.get(path) != reproduction_by_path.get(path)
    ]
    match = not primary["missing"] and not reproduction["missing"] and not mismatches
    return {
        "path": relative.as_posix(),
        "match": match,
        "primary_manifest_hash": primary["manifest_hash"],
        "reproduction_manifest_hash": reproduction["manifest_hash"],
        "file_count": primary["file_count"],
        "total_bytes": primary["total_bytes"],
        "primary_missing": primary["missing"],
        "reproduction_missing": reproduction["missing"],
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }


def compare_governed_manifest_documents(
    primary: dict[str, Any], reproduction: dict[str, Any]
) -> dict[str, Any]:
    primary_rows = primary.get("files")
    reproduction_rows = reproduction.get("files")
    if not isinstance(primary_rows, list) or not isinstance(reproduction_rows, list):
        raise ValueError("GOVERNED_PREFLIGHT_MANIFEST_FILES_INVALID")
    primary_by_path = {
        row["path"]: row
        for row in primary_rows
        if isinstance(row, dict) and isinstance(row.get("path"), str)
    }
    reproduction_by_path = {
        row["path"]: row
        for row in reproduction_rows
        if isinstance(row, dict) and isinstance(row.get("path"), str)
    }
    if len(primary_by_path) != len(primary_rows):
        raise ValueError("PRIMARY_GOVERNED_PREFLIGHT_MANIFEST_ROW_INVALID")
    if len(reproduction_by_path) != len(reproduction_rows):
        raise ValueError("REPRODUCTION_GOVERNED_PREFLIGHT_MANIFEST_ROW_INVALID")
    paths = sorted(set(primary_by_path) | set(reproduction_by_path))
    mismatches = [
        {
            "path": path,
            "primary": primary_by_path.get(path),
            "reproduction": reproduction_by_path.get(path),
        }
        for path in paths
        if primary_by_path.get(path) != reproduction_by_path.get(path)
    ]
    match = (
        primary.get("schema_version") == reproduction.get("schema_version")
        and primary.get("manifest_hash") == reproduction.get("manifest_hash")
        and not mismatches
        and bool(primary_rows)
    )
    return {
        "match": match,
        "primary_manifest_hash": primary.get("manifest_hash"),
        "reproduction_manifest_hash": reproduction.get("manifest_hash"),
        "primary_file_count": len(primary_rows),
        "reproduction_file_count": len(reproduction_rows),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }


def command_plan(root: Path) -> list[tuple[str, list[str]]]:
    python = sys.executable
    scripts = root / "scripts/trace_round16a"
    raw = root / RAW_REL
    merge_arguments: list[str] = [
        python,
        "-B",
        str(scripts / "search_association_pairs.py"),
        "--repo-root",
        str(root),
        "--pair-universe",
        str(raw / "pair-universe-v2.json"),
        "--cache-dir",
        str(root / QUERY_CACHE_REL),
        "--merge-only",
        "--merge-output",
        str(raw / "association-query-log-v2.jsonl"),
    ]
    for shard in QUERY_SHARDS:
        merge_arguments.extend(["--shard-input", str(root / shard)])
    return [
        (
            "VOCABULARY_UNIVERSE_REGENERATION",
            [
                python,
                "-B",
                str(scripts / "build_vocabulary_universe.py"),
                "--repo-root",
                str(root),
            ],
        ),
        (
            "VOCABULARY_CENSUS_REGENERATION",
            [
                python,
                "-B",
                str(scripts / "build_vocabulary_census.py"),
                "--repo-root",
                str(root),
            ],
        ),
        (
            "PAIR_UNIVERSE_REGENERATION",
            [
                python,
                "-B",
                str(scripts / "build_pair_universe.py"),
                "--repo-root",
                str(root),
            ],
        ),
        ("FROZEN_QUERY_LOG_OFFLINE_MERGE", merge_arguments),
        (
            "PAIR_CENSUS_AND_GRAPH_REGENERATION",
            [python, "-B", str(scripts / "build_association_census.py")],
        ),
        (
            "FINITE_EXPLORATION_SPACE_REGENERATION",
            [python, "-B", str(scripts / "build_exploration_space.py")],
        ),
        (
            "INDEPENDENT_VERIFIER_NO_WAIVER",
            [
                python,
                "-B",
                str(scripts / "verify_full_space.py"),
                "--case-tsv",
                str(raw / "independent-verification-cases-v2.tsv"),
            ],
        ),
    ]


def run_command(
    label: str, argv: Sequence[str], root: Path, timeout_seconds: int
) -> dict[str, Any]:
    print(
        "REPRO_COMMAND_START "
        + json.dumps({"label": label, "argv": list(argv)}, ensure_ascii=False),
        flush=True,
    )
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["TRACE_ROUND16A_REPRODUCTION_NETWORK_POLICY"] = (
        "DENY_CAPTURE_OFFLINE_MERGE_ONLY"
    )
    network_guard = tempfile.TemporaryDirectory(
        prefix="trace-round16a-network-deny-"
    )
    try:
        guard_root = Path(network_guard.name)
        atomic_write(guard_root / "sitecustomize.py", NETWORK_GUARD_SOURCE)
        inherited_python_path = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = str(guard_root) + (
            os.pathsep + inherited_python_path if inherited_python_path else ""
        )
        completed = subprocess.run(
            list(argv),
            cwd=root,
            env=environment,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        if stdout:
            sys.stdout.buffer.write(stdout)
            if not stdout.endswith(b"\n"):
                sys.stdout.buffer.write(b"\n")
        if stderr:
            sys.stderr.buffer.write(stderr)
            if not stderr.endswith(b"\n"):
                sys.stderr.buffer.write(b"\n")
        sys.stdout.flush()
        sys.stderr.flush()
        receipt = {
            "label": label,
            "argv": list(argv),
            "cwd": str(root),
            "exit_code": completed.returncode,
            "stdout_bytes": len(stdout),
            "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
            "stderr_bytes": len(stderr),
            "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
            "network_guard": "PYTHON_AUDIT_HOOK_DENY_DNS_AND_SOCKET_CONNECT",
            "status": "PASS" if completed.returncode == 0 else "FAIL",
        }
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or b""
        stderr = error.stderr or b""
        receipt = {
            "label": label,
            "argv": list(argv),
            "cwd": str(root),
            "exit_code": None,
            "stdout_bytes": len(stdout),
            "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
            "stderr_bytes": len(stderr),
            "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
            "network_guard": "PYTHON_AUDIT_HOOK_DENY_DNS_AND_SOCKET_CONNECT",
            "status": "FAIL",
            "error_code": "COMMAND_TIMEOUT",
        }
    finally:
        network_guard.cleanup()
    print(
        "REPRO_COMMAND_FINISH "
        + json.dumps(receipt, ensure_ascii=False, sort_keys=True),
        flush=True,
    )
    return receipt


def snapshot_side_effects(root: Path) -> dict[Path, bytes | None]:
    snapshots: dict[Path, bytes | None] = {}
    for relative in (*NONDETERMINISTIC_SIDE_EFFECTS, *HISTORICAL_NOTE_SIDE_EFFECTS):
        path = root / relative
        snapshots[relative] = path.read_bytes() if path.is_file() else None
    return snapshots


def restore_side_effects(root: Path, snapshots: dict[Path, bytes | None]) -> None:
    for relative, content in snapshots.items():
        path = root / relative
        if content is None:
            if path.exists():
                if not path.is_file():
                    raise RuntimeError(f"SIDE_EFFECT_PATH_NOT_FILE:{relative}")
                path.unlink()
        else:
            atomic_write(path, content)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--reproduction-root", type=Path, required=True)
    parser.add_argument("--final-sha", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--command-timeout-seconds", type=int, default=1800)
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Print the exact isolated-worktree command plan without executing it.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    primary = args.primary_root.resolve()
    reproduction = args.reproduction_root.resolve()
    final_sha = args.final_sha.strip().lower()
    if not SHA40.fullmatch(final_sha):
        raise SystemExit("--final-sha must be one full lowercase 40-character Git SHA")
    if args.command_timeout_seconds <= 0:
        raise SystemExit("--command-timeout-seconds must be positive")
    plan = command_plan(reproduction)
    if args.plan_only:
        print(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "mode": "PLAN_ONLY",
                    "primary_root": str(primary),
                    "reproduction_root": str(reproduction),
                    "final_sha": final_sha,
                    "commands": [
                        {"label": label, "argv": argv} for label, argv in plan
                    ],
                    "preflight": (
                        "Before these commands, invoke each worktree's independent "
                        "verifier with --hash-only-manifest to temporary external files "
                        "and require identical governed source/input manifests."
                    ),
                    "network_policy": (
                        "FROZEN_QUERY_CACHE_MERGE_ONLY_NO_CAPTURE_COMMAND"
                    ),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.output is None:
        output = primary / DEFAULT_OUTPUT_REL
    else:
        output = (
            args.output.resolve()
            if args.output.is_absolute()
            else (primary / args.output).resolve()
        )
    if not output.is_relative_to(primary):
        raise SystemExit("--output must remain inside --primary-root")
    named_matches = {name: False for name in ARTIFACT_GROUPS}
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "FAIL",
        "reproducibility_verification": "FAIL",
        "source_sha": SOURCE_SHA,
        "final_code_sha": final_sha,
        "primary_root": str(primary),
        "reproduction_root": str(reproduction),
        "network_request_count": 0,
        "network_enforcement": {
            "python_audit_hook": "DENY_DNS_AND_SOCKET_CONNECT",
            "search_replay_mode": "MERGE_ONLY",
            "capture_command_count": 0,
            "guarded_command_count": 0,
            "unguarded_command_count": 0,
        },
        "performance_timing_hash_comparison_required": False,
        "commands": [],
        "artifact_groups": {},
        "additional_artifact_groups": {},
        "hash_matches": dict(named_matches),
        "failure_codes": [],
        **named_matches,
    }
    snapshots: dict[Path, bytes | None] = {}
    try:
        if primary == reproduction:
            raise RuntimeError("REPRODUCTION_ROOT_MUST_DIFFER_FROM_PRIMARY")
        if not primary.is_dir() or not reproduction.is_dir():
            raise RuntimeError("WORKTREE_ROOT_MISSING")
        primary_top = git_path(primary, "rev-parse", "--show-toplevel")
        reproduction_top = git_path(reproduction, "rev-parse", "--show-toplevel")
        if primary_top != primary or reproduction_top != reproduction:
            raise RuntimeError("WORKTREE_ROOT_NOT_TOPLEVEL")
        primary_head = git(primary, "rev-parse", "HEAD")
        reproduction_head = git(reproduction, "rev-parse", "HEAD")
        if primary_head != final_sha or reproduction_head != final_sha:
            raise RuntimeError(
                "FINAL_SHA_MISMATCH:"
                f"primary={primary_head}:reproduction={reproduction_head}:expected={final_sha}"
            )
        primary_common = git_path(primary, "rev-parse", "--git-common-dir")
        reproduction_common = git_path(
            reproduction, "rev-parse", "--git-common-dir"
        )
        if primary_common != reproduction_common:
            raise RuntimeError("ROOTS_ARE_NOT_LINKED_GIT_WORKTREES")
        ancestor = git_result(primary, "merge-base", "--is-ancestor", SOURCE_SHA, final_sha)
        if ancestor.returncode != 0:
            raise RuntimeError("FROZEN_SOURCE_NOT_ANCESTOR_OF_FINAL_SHA")
        source_tree_sha = git(primary, "rev-parse", f"{SOURCE_SHA}^{{tree}}")
        final_tree_sha = git(primary, "rev-parse", f"{final_sha}^{{tree}}")

        comparison_paths = sorted(
            {
                path
                for paths in (*ARTIFACT_GROUPS.values(), *ADDITIONAL_GROUPS.values())
                for path in paths
            },
            key=lambda path: path.as_posix(),
        )
        primary_artifact_changes = git_status(primary, comparison_paths)
        if primary_artifact_changes:
            raise RuntimeError(
                "PRIMARY_DETERMINISTIC_ARTIFACTS_NOT_COMMITTED:"
                + json.dumps(primary_artifact_changes, ensure_ascii=False)
            )
        initial_status = git_status(reproduction)
        if initial_status:
            raise RuntimeError(
                "REPRODUCTION_WORKTREE_NOT_CLEAN_AT_START:"
                + json.dumps(initial_status, ensure_ascii=False)
            )

        cache_comparison_before = compare_tree(primary, reproduction, QUERY_CACHE_REL)
        shard_comparison_before = compare_tree(primary, reproduction, QUERY_SHARDS_REL)
        if not cache_comparison_before["match"] or not shard_comparison_before["match"]:
            raise RuntimeError("FROZEN_QUERY_INPUT_HASH_MISMATCH")

        receipt["source_tree_sha"] = source_tree_sha
        receipt["final_tree_sha"] = final_tree_sha
        receipt["worktree"] = {
            "primary_head": primary_head,
            "reproduction_head": reproduction_head,
            "same_git_common_directory": True,
            "distinct_worktree_roots": True,
            "clean_at_start": True,
        }
        receipt["offline_search_replay"] = {
            "mode": "MERGE_ONLY",
            "network_capture_enabled": False,
            "network_request_count": 0,
            "cache": cache_comparison_before,
            "shards": shard_comparison_before,
        }

        with tempfile.TemporaryDirectory(
            prefix="trace-round16a-repro-preflight-"
        ) as temporary_directory:
            temporary_root = Path(temporary_directory)
            preflight_documents: dict[str, dict[str, Any]] = {}
            for label, root in (("PRIMARY", primary), ("REPRODUCTION", reproduction)):
                manifest_path = temporary_root / f"{label.casefold()}-governed.json"
                argv = [
                    sys.executable,
                    "-B",
                    str(root / "scripts/trace_round16a/verify_full_space.py"),
                    "--hash-only-manifest",
                    str(manifest_path),
                ]
                command_receipt = run_command(
                    f"{label}_GOVERNED_SOURCE_INPUT_PREFLIGHT",
                    argv,
                    root,
                    args.command_timeout_seconds,
                )
                receipt["commands"].append(command_receipt)
                if command_receipt["status"] != "PASS":
                    raise RuntimeError(
                        f"GOVERNED_SOURCE_INPUT_PREFLIGHT_FAILED:{label}"
                    )
                preflight_documents[label] = read_json(manifest_path)
            governed_preflight = compare_governed_manifest_documents(
                preflight_documents["PRIMARY"],
                preflight_documents["REPRODUCTION"],
            )
        receipt["governed_source_input_preflight"] = governed_preflight
        if not governed_preflight["match"]:
            raise RuntimeError("GOVERNED_SOURCE_INPUT_PREFLIGHT_MISMATCH")

        snapshots = snapshot_side_effects(reproduction)
        for label, argv in plan:
            command_receipt = run_command(
                label, argv, reproduction, args.command_timeout_seconds
            )
            receipt["commands"].append(command_receipt)
            if command_receipt["status"] != "PASS":
                raise RuntimeError(f"REPRODUCTION_COMMAND_FAILED:{label}")
        restore_side_effects(reproduction, snapshots)
        snapshots = {}

        cache_comparison_after = compare_tree(primary, reproduction, QUERY_CACHE_REL)
        shard_comparison_after = compare_tree(primary, reproduction, QUERY_SHARDS_REL)
        receipt["offline_search_replay"]["cache_after"] = cache_comparison_after
        receipt["offline_search_replay"]["shards_after"] = shard_comparison_after
        receipt["offline_search_replay"]["cache_unchanged"] = (
            cache_comparison_after["match"]
            and cache_comparison_before["primary_manifest_hash"]
            == cache_comparison_after["primary_manifest_hash"]
            and cache_comparison_before["reproduction_manifest_hash"]
            == cache_comparison_after["reproduction_manifest_hash"]
        )
        receipt["offline_search_replay"]["shards_unchanged"] = (
            shard_comparison_after["match"]
            and shard_comparison_before["primary_manifest_hash"]
            == shard_comparison_after["primary_manifest_hash"]
            and shard_comparison_before["reproduction_manifest_hash"]
            == shard_comparison_after["reproduction_manifest_hash"]
        )
        receipt["offline_search_replay"]["frozen_inputs_unchanged"] = (
            receipt["offline_search_replay"]["cache_unchanged"]
            and receipt["offline_search_replay"]["shards_unchanged"]
        )
        if not receipt["offline_search_replay"]["frozen_inputs_unchanged"]:
            raise RuntimeError("FROZEN_QUERY_INPUT_CHANGED_DURING_REPLAY")

        for name, paths in ARTIFACT_GROUPS.items():
            comparison = compare_manifests(primary, reproduction, paths)
            receipt["artifact_groups"][name] = comparison
            receipt[name] = comparison["match"]
        receipt["hash_matches"] = {
            name: receipt[name] for name in ARTIFACT_GROUPS
        }
        for name, paths in ADDITIONAL_GROUPS.items():
            comparison = compare_manifests(primary, reproduction, paths)
            receipt["additional_artifact_groups"][name] = comparison
            receipt[name] = comparison["match"]

        independent = read_json(reproduction / RAW_REL / "independent-verification.json")
        independent_pass = (
            independent.get("status") == "PASS"
            and independent.get("fail_count") == 0
            and independent.get("skip_count") == 0
            and independent.get("generator_import_count") == 0
        )
        receipt["independent_verifier"] = {
            "status": independent.get("status"),
            "case_count": independent.get("case_count"),
            "pass_count": independent.get("pass_count"),
            "fail_count": independent.get("fail_count"),
            "skip_count": independent.get("skip_count"),
            "generator_import_count": independent.get("generator_import_count"),
            "direct_edge_mask_enumeration": independent.get(
                "direct_edge_mask_enumeration"
            ),
            "pass": independent_pass,
        }

        final_status_lines = git_status(reproduction)
        guarded_command_count = sum(
            command.get("network_guard")
            == "PYTHON_AUDIT_HOOK_DENY_DNS_AND_SOCKET_CONNECT"
            for command in receipt["commands"]
        )
        unguarded_command_count = len(receipt["commands"]) - guarded_command_count
        receipt["network_enforcement"]["guarded_command_count"] = (
            guarded_command_count
        )
        receipt["network_enforcement"]["unguarded_command_count"] = (
            unguarded_command_count
        )
        if unguarded_command_count:
            raise RuntimeError("REPRODUCTION_COMMAND_WITHOUT_NETWORK_GUARD")
        receipt["worktree"]["clean_at_end"] = not final_status_lines
        receipt["worktree"]["final_status_lines"] = final_status_lines
        required_match = all(receipt[name] is True for name in ARTIFACT_GROUPS)
        additional_match = all(
            receipt[name] is True for name in ADDITIONAL_GROUPS
        )
        deterministic_mismatch_count = sum(
            not comparison["match"]
            for comparison in (
                *receipt["artifact_groups"].values(),
                *receipt["additional_artifact_groups"].values(),
            )
        )
        receipt["deterministic_artifact_mismatch_count"] = (
            deterministic_mismatch_count
        )
        receipt["all_required_hashes_match"] = required_match
        receipt["all_deterministic_artifacts_match"] = (
            required_match and additional_match
        )
        receipt["clean_worktree_reproduction"] = not final_status_lines
        success = (
            required_match
            and additional_match
            and independent_pass
            and not final_status_lines
        )
        if not success:
            if not required_match:
                receipt["failure_codes"].append("REQUIRED_HASH_MISMATCH")
            if not additional_match:
                receipt["failure_codes"].append("ADDITIONAL_HASH_MISMATCH")
            if not independent_pass:
                receipt["failure_codes"].append("INDEPENDENT_VERIFIER_FAILED")
            if final_status_lines:
                receipt["failure_codes"].append("REPRODUCTION_WORKTREE_DIRTY_AT_END")
        else:
            receipt["status"] = "PASS"
            receipt["reproducibility_verification"] = "PASS"
    except Exception as error:
        receipt["failure_codes"].append(f"{type(error).__name__}:{error}")
    finally:
        if snapshots:
            try:
                restore_side_effects(reproduction, snapshots)
            except Exception as error:
                receipt["failure_codes"].append(
                    f"SIDE_EFFECT_RESTORE_FAILED:{type(error).__name__}:{error}"
                )
        atomic_write(output, canonical_bytes(receipt))

    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
