#!/usr/bin/env python3
"""Independently verify Round 16B append-only execution and checkpoint evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any


SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
ROUND_SLUG = "v49-exploration-higher-order-association-closure-round16b"
RAW_REL = Path(f"docs/audits/{ROUND_SLUG}/raw")
RESEARCH_REL = Path(f"docs/research/trace-{ROUND_SLUG}")
FORBIDDEN_COMMAND_PATTERNS = {
    "FORCE_PUSH": re.compile(r"(?:^|\s)git\s+push\s+[^\n]*(?:--force(?:-with-lease)?|-f(?:\s|$)|\+refs/)", re.I),
    "AMEND": re.compile(r"(?:^|\s)git\s+commit\s+[^\n]*--amend", re.I),
    "REBASE": re.compile(r"(?:^|\s)git\s+rebase(?:\s|$)", re.I),
    "HISTORY_MIGRATION": re.compile(r"(?:filter-repo|filter-branch|git\s+lfs\s+migrate)", re.I),
    "TAG_MUTATION": re.compile(r"(?:^|\s)git\s+tag(?:\s|$)", re.I),
    "MAIN_PUSH": re.compile(r"git\s+push[^\n]*(?:refs/heads/main|HEAD:main)", re.I),
    "DEPLOYMENT": re.compile(r"(?:vercel\s+(?:deploy|--prod)|npm\s+run\s+deploy|kubectl\s+apply)", re.I),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_path(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    if path.is_file():
        return sha256(path)
    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(str(child.relative_to(path)).encode())
        digest.update(b"\0")
        digest.update(sha256(child).encode())
        digest.update(b"\0")
    return digest.hexdigest()


def run(repo: Path, *argv: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv, cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def parse_events(path: Path, failures: list[str]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            failures.append(f"EMPTY_EVENT_LINE:{line_number}")
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            failures.append(f"INVALID_EVENT_JSON:{line_number}")
            continue
        events.append(event)
    sequences = [event.get("sequence") for event in events]
    if sequences != list(range(1, len(events) + 1)):
        failures.append("NONCONTIGUOUS_EVENT_SEQUENCE")
    return events


def parse_ledger(path: Path, failures: list[str]) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        failures.append("EMPTY_COMMAND_LEDGER")
        return []
    header = lines[0].split("\t")
    expected = [
        "command_id", "phase_id", "operation_id", "started_utc", "ended_utc", "cwd",
        "command", "exit_code", "stdout_path", "stderr_path", "meta_path",
    ]
    if header != expected:
        failures.append("COMMAND_LEDGER_HEADER_MISMATCH")
        return []
    rows: list[dict[str, str]] = []
    for line_number, line in enumerate(lines[1:], 2):
        values = line.split("\t")
        if len(values) != len(header):
            failures.append(f"COMMAND_LEDGER_WIDTH:{line_number}")
            continue
        rows.append(dict(zip(header, values)))
    return rows


def resolve_recorded(repo: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    direct = repo / path
    if direct.exists():
        return direct
    return repo / "docs/audits" / path


def verify_checkpoints(repo: Path, path: Path, failures: list[str]) -> dict[str, Any]:
    if not path.exists():
        return {"present": False, "checkpoint_count": 0}
    lines = path.read_text(encoding="utf-8").splitlines()
    expected_header = [
        "checkpoint_id", "phase", "commit_sha", "timestamp_utc", "purpose",
        "verification_operations", "known_limitations", "next_phase",
    ]
    if not lines or lines[0].split("\t") != expected_header:
        failures.append("CHECKPOINT_LEDGER_HEADER_MISMATCH")
        return {"present": True, "checkpoint_count": 0}
    rows = [dict(zip(expected_header, line.split("\t"))) for line in lines[1:] if line]
    ids = [row["checkpoint_id"] for row in rows]
    expected_ids = [f"CHECKPOINT-{index:03d}" for index in range(1, len(rows) + 1)]
    if ids != expected_ids:
        failures.append("CHECKPOINT_SEQUENCE_MISMATCH")
    prior: str | None = None
    for row in rows:
        commit = row["commit_sha"]
        if run(repo, "git", "cat-file", "-e", f"{commit}^{{commit}}").returncode:
            failures.append(f"CHECKPOINT_COMMIT_MISSING:{row['checkpoint_id']}:{commit}")
            continue
        if run(repo, "git", "merge-base", "--is-ancestor", SOURCE_SHA, commit).returncode:
            failures.append(f"CHECKPOINT_NOT_SOURCE_DESCENDANT:{row['checkpoint_id']}")
        if prior and run(repo, "git", "merge-base", "--is-ancestor", prior, commit).returncode:
            failures.append(f"CHECKPOINT_ORDER_MISMATCH:{row['checkpoint_id']}")
        prior = commit
        if not row["purpose"] or not row["verification_operations"] or not row["next_phase"]:
            failures.append(f"CHECKPOINT_REQUIRED_FIELD_EMPTY:{row['checkpoint_id']}")
    return {"present": True, "checkpoint_count": len(rows), "checkpoint_ids": ids}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    raw = repo / RAW_REL
    events_path = raw / "execution-events.jsonl"
    ledger_path = raw / "command-ledger.tsv"
    output_path = args.output if args.output.is_absolute() else repo / args.output
    failures: list[str] = []
    warnings: list[str] = []
    if not events_path.exists():
        failures.append("EVENT_STREAM_MISSING")
        events: list[dict[str, Any]] = []
    else:
        events = parse_events(events_path, failures)
    rows = parse_ledger(ledger_path, failures) if ledger_path.exists() else []
    if not ledger_path.exists():
        failures.append("COMMAND_LEDGER_MISSING")

    row_by_command = {row["command_id"]: row for row in rows}
    if len(row_by_command) != len(rows):
        failures.append("DUPLICATE_COMMAND_LEDGER_ID")
    event_groups: dict[str, list[dict[str, Any]]] = {}
    legacy_events: list[dict[str, Any]] = []
    for event in events:
        command_id = event.get("command_id")
        if command_id:
            event_groups.setdefault(str(command_id), []).append(event)
        else:
            legacy_events.append(event)
        command = str(event.get("command", ""))
        for code, pattern in FORBIDDEN_COMMAND_PATTERNS.items():
            if pattern.search(command):
                failures.append(f"FORBIDDEN_COMMAND:{code}:{event.get('sequence')}")

    if legacy_events:
        if len(legacy_events) != 2 or [event.get("sequence") for event in legacy_events] != [1, 2]:
            failures.append("UNEXPECTED_LEGACY_EVENT_SHAPE")
        elif (
            legacy_events[0].get("status") != "STARTED"
            or legacy_events[1].get("status") not in {"PASS", "FAIL"}
            or legacy_events[0].get("operation_id") != legacy_events[1].get("operation_id")
            or legacy_events[0].get("command") != legacy_events[1].get("command")
        ):
            failures.append("LEGACY_BOOTSTRAP_EVENT_PAIR_MISMATCH")
        else:
            warnings.append("LEGACY_BOOTSTRAP_EVENTS_PRE_COMMAND_ID_SCHEMA=2")

    for command_id, group in event_groups.items():
        ordered = sorted(group, key=lambda event: int(event.get("sequence", 0)))
        if len(ordered) != 2:
            failures.append(f"EVENT_PAIR_COUNT:{command_id}:{len(ordered)}")
            continue
        start, finish = ordered
        if start.get("status") != "STARTED" or finish.get("status") not in {"PASS", "FAIL"}:
            failures.append(f"EVENT_PAIR_STATUS:{command_id}")
        for key in ["phase_id", "operation_id", "command", "cwd", "input_paths", "input_hashes"]:
            if start.get(key) != finish.get(key):
                failures.append(f"EVENT_PAIR_FIELD:{command_id}:{key}")
        if command_id not in row_by_command:
            failures.append(f"EVENT_WITHOUT_LEDGER_ROW:{command_id}")

    meta_ids: set[str] = set()
    for row in rows:
        command_id = row["command_id"]
        meta_path = resolve_recorded(repo, row["meta_path"])
        stdout_path = resolve_recorded(repo, row["stdout_path"])
        stderr_path = resolve_recorded(repo, row["stderr_path"])
        for label, path in [("META", meta_path), ("STDOUT", stdout_path), ("STDERR", stderr_path)]:
            if not path.is_file():
                failures.append(f"{label}_MISSING:{command_id}:{path}")
        if not meta_path.is_file():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta_ids.add(str(meta.get("command_id")))
        if meta.get("command_id") != command_id:
            failures.append(f"META_COMMAND_ID:{command_id}")
        if str(meta.get("exit_code")) != row["exit_code"]:
            failures.append(f"META_EXIT_CODE:{command_id}")
        if stdout_path.is_file() and meta.get("stdout_sha256") != sha256(stdout_path):
            failures.append(f"STDOUT_HASH:{command_id}")
        if stderr_path.is_file() and meta.get("stderr_sha256") != sha256(stderr_path):
            failures.append(f"STDERR_HASH:{command_id}")
    if meta_ids != set(row_by_command):
        failures.append("META_LEDGER_ID_SET_MISMATCH")

    latest_writer: dict[str, dict[str, Any]] = {}
    for event in events:
        if event.get("status") == "PASS":
            for path, digest in event.get("output_hashes", {}).items():
                latest_writer[path] = {"digest": digest, "sequence": event.get("sequence")}
    for raw_path, writer in latest_writer.items():
        path = Path(raw_path)
        if not path.is_absolute():
            path = repo / path
        actual = hash_path(path)
        if actual != writer["digest"]:
            failures.append(f"LATEST_WRITER_HASH:{writer['sequence']}:{raw_path}")

    checkpoint_result = verify_checkpoints(repo, raw / "checkpoint-ledger.tsv", failures)
    result = {
        "schema_version": "trace-round16b-execution-log-verification/v1",
        "source_sha": SOURCE_SHA,
        "event_count": len(events),
        "command_count": len(rows),
        "started_event_count": sum(event.get("status") == "STARTED" for event in events),
        "pass_event_count": sum(event.get("status") == "PASS" for event in events),
        "fail_event_count": sum(event.get("status") == "FAIL" for event in events),
        "legacy_event_count": len(legacy_events),
        "checkpoint_verification": checkpoint_result,
        "warning_codes": sorted(set(warnings)),
        "failure_codes": sorted(set(failures)),
        "status": "PASS" if not failures else "FAIL",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "event_count": len(events), "failure_count": len(result["failure_codes"])}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
