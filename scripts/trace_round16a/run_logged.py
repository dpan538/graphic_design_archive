#!/usr/bin/env python3
"""Execute one Round 16A command with append-only human and machine evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import shlex
import subprocess
import sys
import threading
import time
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_DIR = REPO_ROOT / "docs/research/trace-v49-exploration-full-space-closure-round1"
RAW_DIR = REPO_ROOT / "docs/audits/v49-exploration-full-space-closure-round1/raw"
COMMAND_DIR = RAW_DIR / "commands"
EVENTS_PATH = RAW_DIR / "execution-events.jsonl"
COMMAND_LEDGER_PATH = RAW_DIR / "command-ledger.tsv"
LIVE_LOG_PATH = RESEARCH_DIR / "00_LIVE_EXECUTION_LOG.md"
LOCK_PATH = RAW_DIR / ".execution-log.lock"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_path(raw_path: str, cwd: Path) -> str:
    path = Path(raw_path)
    if not path.is_absolute():
        path = cwd / path
    if not path.exists():
        return "MISSING"
    if path.is_file():
        return sha256_file(path)
    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(str(child.relative_to(path)).encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(child).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def git_sha(cwd: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=cwd, text=True, capture_output=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else "NOT_A_GIT_WORKTREE"


def next_sequence_locked() -> int:
    if not EVENTS_PATH.exists():
        return 1
    last = ""
    with EVENTS_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                last = line
    return json.loads(last)["sequence"] + 1 if last else 1


def current_rss_bytes() -> int:
    # macOS reports ru_maxrss in bytes; Linux reports KiB.
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def append_event(event: dict[str, Any], human: str) -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        event["sequence"] = next_sequence_locked()
        with EVENTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        with LIVE_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(human.replace("{sequence}", str(event["sequence"])))
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return int(event["sequence"])


def stream_pipe(pipe: Any, sink: Any, terminal: Any) -> None:
    for chunk in iter(lambda: pipe.read(65536), b""):
        sink.write(chunk)
        sink.flush()
        terminal.buffer.write(chunk)
        terminal.buffer.flush()
    pipe.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True)
    parser.add_argument("--operation", required=True)
    parser.add_argument("--operation-id", required=True)
    parser.add_argument("--cwd", default=str(REPO_ROOT))
    parser.add_argument("--input", action="append", default=[])
    parser.add_argument("--output", action="append", default=[])
    parser.add_argument("--input-count", type=int)
    parser.add_argument("--output-count", type=int)
    parser.add_argument("--cumulative", default="{}")
    parser.add_argument("--warning", action="append", default=[])
    parser.add_argument("--decision", default="Command result governs continuation.")
    parser.add_argument("--next-operation", default="Proceed to the next governed operation.")
    parser.add_argument("--timeout-seconds", type=int, default=0)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("a command is required after --")
    return args


def main() -> int:
    args = parse_args()
    cwd = Path(args.cwd).resolve()
    command_text = shlex.join(args.command)
    start_timestamp = utc_now()
    command_id = f"{int(time.time() * 1000)}-{args.operation_id}"
    stdout_path = COMMAND_DIR / f"{command_id}.stdout.log"
    stderr_path = COMMAND_DIR / f"{command_id}.stderr.log"
    meta_path = COMMAND_DIR / f"{command_id}.meta.json"
    COMMAND_DIR.mkdir(parents=True, exist_ok=True)

    input_hashes = {path: hash_path(path, cwd) for path in args.input}
    start_event = {
        "timestamp_utc": start_timestamp,
        "phase_id": args.phase,
        "operation_id": args.operation_id,
        "status": "STARTED",
        "command": command_text,
        "cwd": str(cwd),
        "input_paths": args.input,
        "input_hashes": input_hashes,
        "input_count": args.input_count if args.input_count is not None else len(args.input),
        "output_paths": args.output,
        "output_hashes": {},
        "output_count": 0,
        "cumulative_metrics": json.loads(args.cumulative),
        "duration_ms": 0,
        "rss_bytes": current_rss_bytes(),
        "heap_used_bytes": 0,
        "cpu_user_ms": 0,
        "cpu_system_ms": 0,
        "warning_codes": args.warning,
        "error_codes": [],
        "git_sha": git_sha(cwd),
    }
    start_human = (
        "\n## Event {sequence}\n\n"
        f"- Sequence: {{sequence}}\n- UTC timestamp: {start_timestamp}\n- Phase: {args.phase}\n"
        f"- Operation: START — {args.operation}\n- Input artifact(s): {', '.join(args.input) or 'none'}\n"
        f"- Input count: {start_event['input_count']}\n- Output artifact(s): {', '.join(args.output) or 'none'}\n"
        f"- Output count: pending\n- Command or script: `{command_text}`\n- Elapsed duration: running\n"
        f"- Current cumulative counts: {args.cumulative}\n- Warnings: {', '.join(args.warning) or 'none'}\n"
        f"- Errors: none at start\n- Decision: operation started\n- Next operation: {args.next_operation}\n"
        f"- Current Git SHA: `{start_event['git_sha']}`\n"
    )
    append_event(start_event, start_human)

    usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    monotonic_start = time.monotonic()
    timed_out = False
    with stdout_path.open("wb") as stdout_handle, stderr_path.open("wb") as stderr_handle:
        process = subprocess.Popen(args.command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_thread = threading.Thread(
            target=stream_pipe, args=(process.stdout, stdout_handle, sys.stdout), daemon=True
        )
        stderr_thread = threading.Thread(
            target=stream_pipe, args=(process.stderr, stderr_handle, sys.stderr), daemon=True
        )
        stdout_thread.start()
        stderr_thread.start()
        try:
            return_code = process.wait(timeout=args.timeout_seconds or None)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.terminate()
            try:
                return_code = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                return_code = process.wait()
        stdout_thread.join()
        stderr_thread.join()

    duration_ms = round((time.monotonic() - monotonic_start) * 1000)
    end_timestamp = utc_now()
    usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu_user_ms = round((usage_after.ru_utime - usage_before.ru_utime) * 1000)
    cpu_system_ms = round((usage_after.ru_stime - usage_before.ru_stime) * 1000)
    output_hashes = {path: hash_path(path, cwd) for path in args.output}
    status = "PASS" if return_code == 0 and not timed_out else "FAIL"
    error_codes: list[str] = []
    if return_code != 0:
        error_codes.append(f"COMMAND_EXIT_{return_code}")
    if timed_out:
        error_codes.append("COMMAND_TIMEOUT")

    meta = {
        "command_id": command_id,
        "phase_id": args.phase,
        "operation_id": args.operation_id,
        "start_timestamp_utc": start_timestamp,
        "end_timestamp_utc": end_timestamp,
        "cwd": str(cwd),
        "argv": args.command,
        "command": command_text,
        "exit_code": return_code,
        "timed_out": timed_out,
        "duration_ms": duration_ms,
        "environment_versions": {
            "python": sys.version.split()[0],
            "platform": sys.platform,
        },
        "stdout_sha256": sha256_file(stdout_path),
        "stderr_sha256": sha256_file(stderr_path),
        "sanitized": True,
    }
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    finish_event = {
        "timestamp_utc": end_timestamp,
        "phase_id": args.phase,
        "operation_id": args.operation_id,
        "status": status,
        "command": command_text,
        "cwd": str(cwd),
        "input_paths": args.input,
        "input_hashes": input_hashes,
        "input_count": args.input_count if args.input_count is not None else len(args.input),
        "output_paths": args.output,
        "output_hashes": output_hashes,
        "output_count": args.output_count if args.output_count is not None else len(args.output),
        "cumulative_metrics": json.loads(args.cumulative),
        "duration_ms": duration_ms,
        "rss_bytes": current_rss_bytes(),
        "heap_used_bytes": 0,
        "cpu_user_ms": cpu_user_ms,
        "cpu_system_ms": cpu_system_ms,
        "warning_codes": args.warning,
        "error_codes": error_codes,
        "git_sha": git_sha(cwd),
    }
    finish_human = (
        "\n## Event {sequence}\n\n"
        f"- Sequence: {{sequence}}\n- UTC timestamp: {end_timestamp}\n- Phase: {args.phase}\n"
        f"- Operation: {status} — {args.operation}\n- Input artifact(s): {', '.join(args.input) or 'none'}\n"
        f"- Input count: {finish_event['input_count']}\n- Output artifact(s): {', '.join(args.output) or 'none'}\n"
        f"- Output count: {finish_event['output_count']}\n- Command or script: `{command_text}`\n"
        f"- Elapsed duration: {duration_ms} ms\n- Current cumulative counts: {args.cumulative}\n"
        f"- Warnings: {', '.join(args.warning) or 'none'}\n- Errors: {', '.join(error_codes) or 'none'}\n"
        f"- Decision: {args.decision if status == 'PASS' else 'Stop this operation and preserve failure evidence.'}\n"
        f"- Next operation: {args.next_operation}\n- Current Git SHA: `{finish_event['git_sha']}`\n"
    )
    append_event(finish_event, finish_human)

    with COMMAND_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        fields = [
            command_id,
            args.phase,
            args.operation_id,
            start_timestamp,
            end_timestamp,
            str(cwd),
            command_text.replace("\t", " ").replace("\n", " "),
            str(return_code),
            str(stdout_path.relative_to(RAW_DIR.parent.parent)),
            str(stderr_path.relative_to(RAW_DIR.parent.parent)),
            str(meta_path.relative_to(RAW_DIR.parent.parent)),
        ]
        handle.write("\t".join(fields) + "\n")
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
