#!/usr/bin/env python3
"""Run one Round 16B operation with append-only machine and human evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
from pathlib import Path
import resource
import shlex
import subprocess
import sys
import threading
import time
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ROUND_SLUG = "v49-exploration-higher-order-association-closure-round16b"
RESEARCH_DIR = REPO_ROOT / f"docs/research/trace-{ROUND_SLUG}"
RAW_DIR = REPO_ROOT / f"docs/audits/{ROUND_SLUG}/raw"
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
        digest.update(str(child.relative_to(path)).encode())
        digest.update(b"\0")
        digest.update(sha256_file(child).encode())
        digest.update(b"\0")
    return digest.hexdigest()


def git_sha(cwd: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=cwd, text=True, capture_output=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else "NOT_A_GIT_WORKTREE"


def current_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def next_sequence_locked() -> int:
    if not EVENTS_PATH.exists():
        return 1
    last = ""
    with EVENTS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                last = line
    return int(json.loads(last)["sequence"]) + 1 if last else 1


def append_event(event: dict[str, Any], human: str) -> None:
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
    started = utc_now()
    command_id = f"{int(time.time() * 1000)}-{args.operation_id}"
    COMMAND_DIR.mkdir(parents=True, exist_ok=True)
    stdout_path = COMMAND_DIR / f"{command_id}.stdout.log"
    stderr_path = COMMAND_DIR / f"{command_id}.stderr.log"
    meta_path = COMMAND_DIR / f"{command_id}.meta.json"
    input_hashes = {path: hash_path(path, cwd) for path in args.input}

    start_event = {
        "command_id": command_id,
        "timestamp_utc": started,
        "phase_id": args.phase,
        "operation_id": args.operation_id,
        "status": "STARTED",
        "command": command_text,
        "cwd": str(cwd),
        "input_paths": args.input,
        "input_hashes": input_hashes,
        "output_paths": args.output,
        "output_hashes": {},
        "duration_ms": 0,
        "rss_bytes": current_rss_bytes(),
        "warning_codes": args.warning,
        "error_codes": [],
        "git_sha": git_sha(cwd),
    }
    append_event(
        start_event,
        "\n## Event {sequence}\n\n"
        f"- UTC timestamp: {started}\n- Phase: {args.phase}\n"
        f"- Operation: START — {args.operation}\n- Command: `{command_text}`\n"
        f"- Inputs: {', '.join(args.input) or 'none'}\n"
        f"- Declared outputs: {', '.join(args.output) or 'none'}\n"
        f"- Warnings: {', '.join(args.warning) or 'none'}\n"
        f"- Git SHA: `{start_event['git_sha']}`\n",
    )

    usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    clock = time.monotonic()
    timed_out = False
    with stdout_path.open("wb") as stdout_handle, stderr_path.open("wb") as stderr_handle:
        process = subprocess.Popen(args.command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out_thread = threading.Thread(
            target=stream_pipe, args=(process.stdout, stdout_handle, sys.stdout), daemon=True
        )
        err_thread = threading.Thread(
            target=stream_pipe, args=(process.stderr, stderr_handle, sys.stderr), daemon=True
        )
        out_thread.start()
        err_thread.start()
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
        out_thread.join()
        err_thread.join()

    ended = utc_now()
    duration_ms = round((time.monotonic() - clock) * 1000)
    usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)
    errors: list[str] = []
    if return_code:
        errors.append(f"COMMAND_EXIT_{return_code}")
    if timed_out:
        errors.append("COMMAND_TIMEOUT")
    status = "PASS" if not errors else "FAIL"
    output_hashes = {path: hash_path(path, cwd) for path in args.output}
    meta = {
        "command_id": command_id,
        "phase_id": args.phase,
        "operation_id": args.operation_id,
        "start_timestamp_utc": started,
        "end_timestamp_utc": ended,
        "cwd": str(cwd),
        "argv": args.command,
        "command": command_text,
        "exit_code": return_code,
        "timed_out": timed_out,
        "duration_ms": duration_ms,
        "stdout_sha256": sha256_file(stdout_path),
        "stderr_sha256": sha256_file(stderr_path),
        "sanitized": True,
    }
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    finish_event = {
        "command_id": command_id,
        "timestamp_utc": ended,
        "phase_id": args.phase,
        "operation_id": args.operation_id,
        "status": status,
        "command": command_text,
        "cwd": str(cwd),
        "input_paths": args.input,
        "input_hashes": input_hashes,
        "output_paths": args.output,
        "output_hashes": output_hashes,
        "duration_ms": duration_ms,
        "rss_bytes": current_rss_bytes(),
        "cpu_user_ms": round((usage_after.ru_utime - usage_before.ru_utime) * 1000),
        "cpu_system_ms": round((usage_after.ru_stime - usage_before.ru_stime) * 1000),
        "warning_codes": args.warning,
        "error_codes": errors,
        "git_sha": git_sha(cwd),
    }
    append_event(
        finish_event,
        "\n## Event {sequence}\n\n"
        f"- UTC timestamp: {ended}\n- Phase: {args.phase}\n"
        f"- Operation: {status} — {args.operation}\n- Command: `{command_text}`\n"
        f"- Inputs: {', '.join(args.input) or 'none'}\n"
        f"- Outputs: {', '.join(args.output) or 'none'}\n"
        f"- Duration: {duration_ms} ms\n- Warnings: {', '.join(args.warning) or 'none'}\n"
        f"- Errors: {', '.join(errors) or 'none'}\n"
        f"- Decision: {args.decision if status == 'PASS' else 'Preserve the failure and correct it additively.'}\n"
        f"- Next: {args.next_operation}\n- Git SHA: `{finish_event['git_sha']}`\n",
    )
    if not COMMAND_LEDGER_PATH.exists():
        COMMAND_LEDGER_PATH.write_text(
            "command_id\tphase_id\toperation_id\tstarted_utc\tended_utc\tcwd\tcommand\texit_code\tstdout_path\tstderr_path\tmeta_path\n",
            encoding="utf-8",
        )
    with COMMAND_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        relative_root = RAW_DIR.parent.parent
        fields = [
            command_id,
            args.phase,
            args.operation_id,
            started,
            ended,
            str(cwd),
            command_text.replace("\t", " ").replace("\n", " "),
            str(return_code),
            str(stdout_path.relative_to(relative_root)),
            str(stderr_path.relative_to(relative_root)),
            str(meta_path.relative_to(relative_root)),
        ]
        handle.write("\t".join(fields) + "\n")
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
