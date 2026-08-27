#!/usr/bin/env python3
"""Start Next production, measure readiness, and remain attached for logging."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time
import uuid
from urllib.error import URLError
from urllib.request import Request, urlopen


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontend", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3034)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--probe-module", type=Path, required=True)
    parser.add_argument("--readiness-timeout-seconds", type=float, default=120)
    args = parser.parse_args()

    frontend = args.frontend.resolve()
    node = shutil.which("node")
    next_cli = frontend / "node_modules/next/dist/bin/next"
    if node is None:
        raise RuntimeError("NODE_EXECUTABLE_NOT_FOUND")
    if not next_cli.is_file():
        raise RuntimeError(f"NEXT_PRODUCTION_CLI_NOT_FOUND:{next_cli}")
    if not (frontend / ".next").is_dir():
        raise RuntimeError("NEXT_PRODUCTION_BUILD_NOT_FOUND")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.probe.parent.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["NODE_ENV"] = "production"
    probe_session_id = str(uuid.uuid4())
    require_option = f"--require={args.probe_module.resolve()}"
    existing_node_options = environment.get("NODE_OPTIONS", "").strip()
    environment["NODE_OPTIONS"] = f"{existing_node_options} {require_option}".strip()
    environment["TRACE_RUNTIME_PROBE_PATH"] = str(args.probe.resolve())
    environment["TRACE_RUNTIME_PROBE_SESSION_ID"] = probe_session_id
    environment["TRACE_RUNTIME_PROBE_ROLE"] = "NEXT_PRODUCTION_SERVER"

    started_utc = utc_now()
    started = time.monotonic()
    command = [node, str(next_cli), "start", "--hostname", args.host, "--port", str(args.port)]
    process = subprocess.Popen(
        command,
        cwd=frontend,
        env=environment,
    )

    def stop(_signum: int, _frame: object) -> None:
        if process.poll() is None:
            process.terminate()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        readiness_url = f"http://{args.host}:{args.port}/api/trace/v2/exploration/capabilities"
        deadline = started + args.readiness_timeout_seconds
        attempts = 0
        first_request_ms = 0.0
        response_bytes = 0
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"Production server exited before readiness: {process.returncode}")
            attempts += 1
            request_start = time.monotonic()
            try:
                with urlopen(Request(readiness_url, headers={"Accept": "application/json"}), timeout=2) as response:
                    body = response.read()
                    first_request_ms = (time.monotonic() - request_start) * 1000
                    response_bytes = len(body)
                    if response.status == 200:
                        payload = json.loads(body)
                        if payload.get("api_version") == "trace-exploration/v2" and payload.get("database_snapshot"):
                            break
            except (URLError, TimeoutError, ConnectionError, json.JSONDecodeError):
                pass
            time.sleep(0.05)
        else:
            raise RuntimeError("Production server readiness deadline exceeded")

        receipt = {
            "schema_version": "trace-exploration-production-server-startup-v2",
            "status": "READY",
            "started_utc": started_utc,
            "ready_utc": utc_now(),
            "server_pid": process.pid,
            "server_command": command,
            "host": args.host,
            "port": args.port,
            "readiness_url": readiness_url,
            "readiness_attempt_count": attempts,
            "cold_start_ms": (time.monotonic() - started) * 1000,
            "first_successful_request_ms": first_request_ms,
            "first_request_including_model_import_ms": first_request_ms,
            "first_response_bytes": response_bytes,
            "probe_path": str(args.probe.resolve()),
            "probe_session_id": probe_session_id,
        }
        args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(receipt, sort_keys=True), flush=True)
        return_code = process.wait()
        print(json.dumps({"status": "SERVER_EXIT", "return_code": return_code, "timestamp_utc": utc_now()}), flush=True)
        return 0 if return_code in (0, -signal.SIGTERM) else return_code
    except BaseException:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
