#!/usr/bin/env python3
"""Independently verify the append-only Round 16A execution evidence.

The verifier intentionally does not import the execution logger.  It treats the
JSONL/TSV ledgers and command artifacts as untrusted inputs, validates their
shape and cross-file hashes, and writes one deterministic verification receipt.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDITS_RELATIVE = Path("docs/audits")
AUDIT_RELATIVE = AUDITS_RELATIVE / "v49-exploration-full-space-closure-round1"
RAW_RELATIVE = AUDIT_RELATIVE / "raw"
COMMANDS_RELATIVE = RAW_RELATIVE / "commands"

EVENTS_RELATIVE = RAW_RELATIVE / "execution-events.jsonl"
COMMAND_LEDGER_RELATIVE = RAW_RELATIVE / "command-ledger.tsv"
CHECKPOINT_LEDGER_RELATIVE = RAW_RELATIVE / "checkpoint-ledger.tsv"
OUTPUT_RELATIVE = RAW_RELATIVE / "execution-log-verification.json"

EVENT_REQUIRED_TYPES: dict[str, type] = {
    "sequence": int,
    "timestamp_utc": str,
    "phase_id": str,
    "operation_id": str,
    "status": str,
    "command": str,
    "cwd": str,
    "input_paths": list,
    "input_hashes": dict,
    "input_count": int,
    "output_paths": list,
    "output_hashes": dict,
    "output_count": int,
    "cumulative_metrics": dict,
    "duration_ms": int,
    "rss_bytes": int,
    "heap_used_bytes": int,
    "cpu_user_ms": int,
    "cpu_system_ms": int,
    "warning_codes": list,
    "error_codes": list,
    "git_sha": str,
}

COMMAND_LEDGER_FIELDS = (
    "command_id",
    "phase_id",
    "operation_id",
    "start_timestamp_utc",
    "end_timestamp_utc",
    "cwd",
    "command",
    "exit_code",
    "stdout_path",
    "stderr_path",
    "meta_path",
)

CHECKPOINT_LEDGER_FIELDS = (
    "checkpoint_id",
    "phase",
    "commit_sha",
    "timestamp_utc",
    "exact_counts",
    "commands",
    "known_limitations",
    "next_gate",
)

TRUNCATION_POLICY_MARKERS = (
    "warning: truncated output",
    "[output truncated]",
    "<output truncated>",
    "output was truncated",
    "output has been truncated",
    "original token count:",
    "tokens truncated",
    "lines omitted due to output limit",
    "bytes omitted due to output limit",
    "output omitted due to size",
)

UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
TERMINAL_EVENT_STATUSES = {"PASS", "FAIL"}
EVENT_STATUSES = TERMINAL_EVENT_STATUSES | {"STARTED"}
LATEST_WRITER_RULE = (
    "Execution events are append-only historical observations. For each mutable local file "
    "path, only the highest-sequence completed PASS or FAIL event that names that path is "
    "compared with the current file bytes; superseded event hashes remain schema-validated "
    "history and are never compared with later file contents."
)


class VerificationError(RuntimeError):
    """A stable fail-closed verification failure."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise VerificationError(code)


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    return hashlib.sha256(data).hexdigest()


def relative(path: Path, repo: Path) -> str:
    return path.resolve().relative_to(repo.resolve()).as_posix()


def validate_string_list(value: Any, code: str) -> None:
    require(isinstance(value, list), code)
    require(all(isinstance(item, str) for item in value), code)


def validate_string_map(value: Any, code: str) -> None:
    require(isinstance(value, dict), code)
    require(
        all(isinstance(key, str) and isinstance(item, str) for key, item in value.items()),
        code,
    )


def parse_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    seen_sequences: set[int] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            require(bool(line.strip()), f"EXECUTION_EVENT_BLANK_LINE:{line_number}")
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise VerificationError(f"EXECUTION_EVENT_JSON_INVALID:{line_number}:{error.msg}") from error
            require(isinstance(event, dict), f"EXECUTION_EVENT_OBJECT_REQUIRED:{line_number}")
            missing = sorted(set(EVENT_REQUIRED_TYPES) - set(event))
            require(not missing, f"EXECUTION_EVENT_REQUIRED_FIELDS_MISSING:{line_number}:{','.join(missing)}")
            for field, expected_type in EVENT_REQUIRED_TYPES.items():
                value = event[field]
                valid = is_int(value) if expected_type is int else isinstance(value, expected_type)
                require(valid, f"EXECUTION_EVENT_FIELD_TYPE_INVALID:{line_number}:{field}")

            sequence = event["sequence"]
            require(sequence > 0, f"EXECUTION_EVENT_SEQUENCE_NONPOSITIVE:{line_number}")
            require(sequence not in seen_sequences, f"EXECUTION_EVENT_SEQUENCE_DUPLICATE:{sequence}")
            seen_sequences.add(sequence)
            require(UTC_TIMESTAMP.fullmatch(event["timestamp_utc"]) is not None, f"EXECUTION_EVENT_TIMESTAMP_INVALID:{sequence}")
            require(bool(event["phase_id"]), f"EXECUTION_EVENT_PHASE_EMPTY:{sequence}")
            require(bool(event["operation_id"]), f"EXECUTION_EVENT_OPERATION_EMPTY:{sequence}")
            require(bool(event["status"]), f"EXECUTION_EVENT_STATUS_EMPTY:{sequence}")
            require(event["status"] in EVENT_STATUSES, f"EXECUTION_EVENT_STATUS_INVALID:{sequence}")
            require(bool(event["command"]), f"EXECUTION_EVENT_COMMAND_EMPTY:{sequence}")
            require(Path(event["cwd"]).is_absolute(), f"EXECUTION_EVENT_CWD_NOT_ABSOLUTE:{sequence}")
            validate_string_list(event["input_paths"], f"EXECUTION_EVENT_INPUT_PATHS_INVALID:{sequence}")
            validate_string_list(event["output_paths"], f"EXECUTION_EVENT_OUTPUT_PATHS_INVALID:{sequence}")
            validate_string_list(event["warning_codes"], f"EXECUTION_EVENT_WARNING_CODES_INVALID:{sequence}")
            validate_string_list(event["error_codes"], f"EXECUTION_EVENT_ERROR_CODES_INVALID:{sequence}")
            validate_string_map(event["input_hashes"], f"EXECUTION_EVENT_INPUT_HASHES_INVALID:{sequence}")
            validate_string_map(event["output_hashes"], f"EXECUTION_EVENT_OUTPUT_HASHES_INVALID:{sequence}")
            require(event["input_count"] >= 0, f"EXECUTION_EVENT_INPUT_COUNT_NEGATIVE:{sequence}")
            require(event["output_count"] >= 0, f"EXECUTION_EVENT_OUTPUT_COUNT_NEGATIVE:{sequence}")
            for field in (
                "duration_ms",
                "rss_bytes",
                "heap_used_bytes",
                "cpu_user_ms",
                "cpu_system_ms",
            ):
                require(event[field] >= 0, f"EXECUTION_EVENT_RESOURCE_VALUE_NEGATIVE:{sequence}:{field}")
            require(GIT_SHA.fullmatch(event["git_sha"]) is not None, f"EXECUTION_EVENT_GIT_SHA_INVALID:{sequence}")
            events.append(event)

    require(bool(events), "EXECUTION_EVENT_LOG_EMPTY")
    sequences = sorted(seen_sequences)
    expected = list(range(1, len(events) + 1))
    require(sequences == expected, "EXECUTION_EVENT_SEQUENCE_NOT_CONTIGUOUS_FROM_ONE")
    require([event["sequence"] for event in events] == expected, "EXECUTION_EVENT_FILE_ORDER_MISMATCH")
    return events


def event_output_file(path_text: str, event: dict[str, Any]) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else Path(event["cwd"]) / path


def verify_event_output_hashes(
    events: list[dict[str, Any]], repo: Path
) -> dict[str, Any]:
    """Reconcile current mutable files with their latest completed writer.

    A completed event records what existed when that command ended.  A later
    command may legitimately overwrite the same output, so comparing every
    historical hash with the current bytes makes an append-only log impossible
    to verify after a retry or deterministic regeneration.  Historical records
    still pass through ``parse_events`` and every historical local-file hash is
    required to have SHA-256 shape.  Only the latest completed writer for each
    resolved path is eligible for a current-byte comparison.
    """
    latest_completed_writer: dict[Path, tuple[dict[str, Any], str, str | None]] = {}
    historical_output_hash_observation_count = 0
    historical_local_file_hash_count = 0
    historical_non_file_or_symbolic_hash_count = 0
    completed_writer_observation_count = 0
    existing_unhashed_started_outputs: set[tuple[int, Path]] = set()

    for event in events:
        candidate_names = list(event["output_paths"])
        candidate_names.extend(
            key for key in event["output_hashes"] if key not in event["output_paths"]
        )
        candidates_by_path: dict[Path, tuple[str, str | None]] = {}
        for name in candidate_names:
            candidate = event_output_file(name, event).resolve()
            expected = event["output_hashes"].get(name)
            prior = candidates_by_path.get(candidate)
            if prior is None or (prior[1] is None and expected is not None):
                candidates_by_path[candidate] = (name, expected)

        for candidate, (name, expected) in candidates_by_path.items():
            if expected is not None:
                historical_output_hash_observation_count += 1
                require(
                    expected == "MISSING"
                    or SHA256.fullmatch(expected) is not None
                    or GIT_SHA.fullmatch(expected) is not None,
                    f"HISTORICAL_OUTPUT_HASH_VALUE_INVALID:{event['sequence']}:{name}",
                )
                if candidate.is_file():
                    require(
                        expected == "MISSING" or SHA256.fullmatch(expected) is not None,
                        f"HISTORICAL_LOCAL_OUTPUT_SHA256_INVALID:{event['sequence']}:{name}",
                    )
                    if expected != "MISSING":
                        historical_local_file_hash_count += 1
                else:
                    # Git refs, commit/tree identities, directories, and outputs
                    # no longer present are intentional non-file observations.
                    historical_non_file_or_symbolic_hash_count += 1

            if event["status"] in TERMINAL_EVENT_STATUSES:
                completed_writer_observation_count += 1
                latest_completed_writer[candidate] = (event, name, expected)
            elif candidate.is_file() and expected is None:
                existing_unhashed_started_outputs.add((event["sequence"], candidate))

    verified: list[dict[str, Any]] = []
    latest_non_file_or_symbolic_writer_count = 0
    for candidate, (event, name, expected) in sorted(
        latest_completed_writer.items(), key=lambda item: item[0].as_posix()
    ):
        if not candidate.is_file():
            latest_non_file_or_symbolic_writer_count += 1
            continue
        if expected is None:
            require(
                False,
                f"LATEST_COMPLETED_WRITER_OUTPUT_HASH_MISSING:{event['sequence']}:{name}",
            )
        require(
            SHA256.fullmatch(expected) is not None,
            f"LATEST_COMPLETED_WRITER_OUTPUT_SHA256_INVALID:{event['sequence']}:{name}",
        )
        actual = sha256_file(candidate)
        require(
            actual == expected,
            f"LATEST_COMPLETED_WRITER_OUTPUT_SHA256_MISMATCH:{event['sequence']}:{name}",
        )
        try:
            display_path = relative(candidate, repo)
        except ValueError:
            display_path = candidate.as_posix()
        verified.append(
            {
                "event_sequence": event["sequence"],
                "event_status": event["status"],
                "path": display_path,
                "sha256": actual,
            }
        )

    verified.sort(key=lambda item: (item["path"], item["event_sequence"]))
    latest_completed_writer_count = len(latest_completed_writer)
    return {
        "reconciliation_rule": "APPEND_ONLY_LATEST_COMPLETED_WRITER_V1",
        "reconciliation_rule_description": LATEST_WRITER_RULE,
        "terminal_statuses": sorted(TERMINAL_EVENT_STATUSES),
        "historical_output_hash_observation_count": historical_output_hash_observation_count,
        "historical_local_file_hash_count": historical_local_file_hash_count,
        "historical_non_file_or_symbolic_output_hash_count": historical_non_file_or_symbolic_hash_count,
        "non_file_or_symbolic_output_hash_count": historical_non_file_or_symbolic_hash_count,
        "completed_writer_observation_count": completed_writer_observation_count,
        "latest_completed_writer_count": latest_completed_writer_count,
        "superseded_completed_writer_count": (
            completed_writer_observation_count - latest_completed_writer_count
        ),
        "verified_local_file_hash_count": len(verified),
        "existing_unhashed_started_output_count": len(existing_unhashed_started_outputs),
        "latest_non_file_or_symbolic_writer_count": latest_non_file_or_symbolic_writer_count,
        "mismatch_count": 0,
        "verified": verified,
    }


def parse_tsv(path: Path, expected_fields: tuple[str, ...], ledger_name: str) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        require(reader.fieldnames == list(expected_fields), f"{ledger_name}_HEADER_MISMATCH")
        rows = list(reader)
    for row_number, row in enumerate(rows, start=2):
        require(None not in row, f"{ledger_name}_EXTRA_COLUMN:{row_number}")
        require(all(value is not None for value in row.values()), f"{ledger_name}_MISSING_COLUMN:{row_number}")
    return rows


def resolve_command_artifact(path_text: str, repo: Path) -> Path:
    raw_path = Path(path_text)
    if raw_path.is_absolute():
        candidates = [raw_path]
    else:
        candidates = [
            repo / raw_path,
            repo / AUDIT_RELATIVE / raw_path,
            repo / AUDITS_RELATIVE / raw_path,
            repo / RAW_RELATIVE / raw_path,
        ]
    matches: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file() and resolved not in matches:
            matches.append(resolved)
    require(len(matches) == 1, f"COMMAND_ARTIFACT_RESOLUTION_COUNT_INVALID:{path_text}:{len(matches)}")
    commands_dir = (repo / COMMANDS_RELATIVE).resolve()
    require(matches[0].parent == commands_dir, f"COMMAND_ARTIFACT_OUTSIDE_COMMAND_DIRECTORY:{path_text}")
    return matches[0]


def require_meta_value(meta: dict[str, Any], field: str, expected: Any, command_id: str) -> None:
    if field in meta:
        require(meta[field] == expected, f"COMMAND_META_LEDGER_MISMATCH:{command_id}:{field}")


def scan_truncation_markers(path: Path) -> list[str]:
    content = path.read_bytes().decode("utf-8", errors="replace").casefold()
    return [marker for marker in TRUNCATION_POLICY_MARKERS if marker.casefold() in content]


def command_artifact_stem(path: Path) -> tuple[str, str] | None:
    for suffix, kind in (
        (".stdout.log", "stdout"),
        (".stderr.log", "stderr"),
        (".meta.json", "meta"),
    ):
        if path.name.endswith(suffix):
            return path.name[: -len(suffix)], kind
    return None


def verify_command_ledger(
    rows: list[dict[str, str]], events: list[dict[str, Any]], repo: Path
) -> dict[str, Any]:
    command_ids: set[str] = set()
    expected_artifacts: set[Path] = set()
    verified_stream_hash_count = 0
    missing_recorded_stream_hash_count = 0
    truncation_matches: list[dict[str, str]] = []
    artifact_inventory: list[dict[str, Any]] = []

    for row_number, row in enumerate(rows, start=2):
        command_id = row["command_id"]
        require(bool(command_id), f"COMMAND_LEDGER_ID_EMPTY:{row_number}")
        require(command_id not in command_ids, f"COMMAND_LEDGER_ID_DUPLICATE:{command_id}")
        command_ids.add(command_id)
        require(bool(row["phase_id"]), f"COMMAND_LEDGER_PHASE_EMPTY:{command_id}")
        require(bool(row["operation_id"]), f"COMMAND_LEDGER_OPERATION_EMPTY:{command_id}")
        require(bool(row["command"]), f"COMMAND_LEDGER_COMMAND_EMPTY:{command_id}")
        require(Path(row["cwd"]).is_absolute(), f"COMMAND_LEDGER_CWD_NOT_ABSOLUTE:{command_id}")
        require(UTC_TIMESTAMP.fullmatch(row["start_timestamp_utc"]) is not None, f"COMMAND_LEDGER_START_INVALID:{command_id}")
        require(UTC_TIMESTAMP.fullmatch(row["end_timestamp_utc"]) is not None, f"COMMAND_LEDGER_END_INVALID:{command_id}")
        try:
            exit_code = int(row["exit_code"])
        except ValueError as error:
            raise VerificationError(f"COMMAND_LEDGER_EXIT_CODE_INVALID:{command_id}") from error

        stdout_path = resolve_command_artifact(row["stdout_path"], repo)
        stderr_path = resolve_command_artifact(row["stderr_path"], repo)
        meta_path = resolve_command_artifact(row["meta_path"], repo)
        require(stdout_path.name == f"{command_id}.stdout.log", f"COMMAND_STDOUT_NAME_MISMATCH:{command_id}")
        require(stderr_path.name == f"{command_id}.stderr.log", f"COMMAND_STDERR_NAME_MISMATCH:{command_id}")
        require(meta_path.name == f"{command_id}.meta.json", f"COMMAND_META_NAME_MISMATCH:{command_id}")
        expected_artifacts.update((stdout_path, stderr_path, meta_path))

        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise VerificationError(f"COMMAND_META_JSON_INVALID:{command_id}:{error.msg}") from error
        require(isinstance(meta, dict), f"COMMAND_META_OBJECT_REQUIRED:{command_id}")
        require(meta.get("command_id") == command_id, f"COMMAND_META_ID_MISMATCH:{command_id}")
        require(meta.get("exit_code") == exit_code, f"COMMAND_META_EXIT_CODE_MISMATCH:{command_id}")
        require(meta.get("sanitized") is True, f"COMMAND_META_NOT_SANITIZED:{command_id}")
        require(isinstance(meta.get("environment_versions"), dict), f"COMMAND_META_ENVIRONMENT_INVALID:{command_id}")
        require_meta_value(meta, "phase_id", row["phase_id"], command_id)
        require_meta_value(meta, "operation_id", row["operation_id"], command_id)
        require_meta_value(meta, "start_timestamp_utc", row["start_timestamp_utc"], command_id)
        require_meta_value(meta, "end_timestamp_utc", row["end_timestamp_utc"], command_id)
        require_meta_value(meta, "cwd", row["cwd"], command_id)
        require_meta_value(meta, "command", row["command"], command_id)
        if "commands" in meta:
            validate_string_list(meta["commands"], f"COMMAND_META_COMMANDS_INVALID:{command_id}")
            require(bool(meta["commands"]), f"COMMAND_META_COMMANDS_EMPTY:{command_id}")
        else:
            require(isinstance(meta.get("command"), str), f"COMMAND_META_COMMAND_MISSING:{command_id}")

        for stream_name, stream_path in (("stdout", stdout_path), ("stderr", stderr_path)):
            actual_hash = sha256_file(stream_path)
            recorded_hash = meta.get(f"{stream_name}_sha256")
            if recorded_hash is None:
                missing_recorded_stream_hash_count += 1
            else:
                require(isinstance(recorded_hash, str), f"COMMAND_STREAM_HASH_TYPE_INVALID:{command_id}:{stream_name}")
                require(SHA256.fullmatch(recorded_hash) is not None, f"COMMAND_STREAM_HASH_INVALID:{command_id}:{stream_name}")
                require(actual_hash == recorded_hash, f"COMMAND_STREAM_HASH_MISMATCH:{command_id}:{stream_name}")
                verified_stream_hash_count += 1
            markers = scan_truncation_markers(stream_path)
            truncation_matches.extend(
                {
                    "command_id": command_id,
                    "stream": stream_name,
                    "marker": marker,
                }
                for marker in markers
            )
            artifact_inventory.append(
                {
                    "path": relative(stream_path, repo),
                    "byte_size": stream_path.stat().st_size,
                    "sha256": actual_hash,
                }
            )
        for flag in ("truncated", "stdout_truncated", "stderr_truncated", "output_truncated"):
            require(meta.get(flag) is not True, f"COMMAND_META_TRUNCATION_FLAG_TRUE:{command_id}:{flag}")
        artifact_inventory.append(
            {
                "path": relative(meta_path, repo),
                "byte_size": meta_path.stat().st_size,
                "sha256": sha256_file(meta_path),
            }
        )

    require(not truncation_matches, "COMMAND_LOG_TRUNCATION_POLICY_MARKER_FOUND")

    commands_dir = repo / COMMANDS_RELATIVE
    actual_artifacts = {path.resolve() for path in commands_dir.iterdir() if path.is_file()}
    unexpected = sorted(actual_artifacts - expected_artifacts)
    unexpected_groups: dict[str, set[str]] = {}
    for path in unexpected:
        parsed = command_artifact_stem(path)
        require(parsed is not None, f"UNKNOWN_COMMAND_ARTIFACT:{path.name}")
        stem, kind = parsed
        unexpected_groups.setdefault(stem, set()).add(kind)

    inflight_groups: list[str] = []
    if unexpected_groups:
        last_event = events[-1]
        for stem, kinds in unexpected_groups.items():
            is_inflight = (
                last_event["status"] == "STARTED"
                and stem.endswith(f"-{last_event['operation_id']}")
                and kinds.issubset({"stdout", "stderr"})
                and "stdout" in kinds
                and "stderr" in kinds
            )
            require(is_inflight, f"UNLEDGERED_COMMAND_ARTIFACT_GROUP:{stem}")
            inflight_groups.append(stem)
    require(len(inflight_groups) <= 1, "MULTIPLE_INFLIGHT_COMMAND_ARTIFACT_GROUPS")

    artifact_inventory.sort(key=lambda item: item["path"])
    return {
        "row_count": len(rows),
        "unique_command_id_count": len(command_ids),
        "stdout_log_count": len(rows),
        "stderr_log_count": len(rows),
        "meta_file_count": len(rows),
        "verified_stream_hash_count": verified_stream_hash_count,
        "missing_recorded_stream_hash_count": missing_recorded_stream_hash_count,
        "truncation_policy_marker_count": 0,
        "unledgered_completed_artifact_count": 0,
        "inflight_command_group_count": len(inflight_groups),
        "artifact_inventory_sha256": canonical_sha256(artifact_inventory),
        "artifact_inventory": artifact_inventory,
    }


def verify_checkpoint_ledger(rows: list[dict[str, str]]) -> dict[str, Any]:
    checkpoint_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        checkpoint_id = row["checkpoint_id"]
        require(bool(checkpoint_id), f"CHECKPOINT_LEDGER_ID_EMPTY:{row_number}")
        require(checkpoint_id not in checkpoint_ids, f"CHECKPOINT_LEDGER_ID_DUPLICATE:{checkpoint_id}")
        checkpoint_ids.add(checkpoint_id)
        require(bool(row["phase"]), f"CHECKPOINT_LEDGER_PHASE_EMPTY:{checkpoint_id}")
        require(GIT_SHA.fullmatch(row["commit_sha"]) is not None, f"CHECKPOINT_LEDGER_COMMIT_SHA_INVALID:{checkpoint_id}")
        require(UTC_TIMESTAMP.fullmatch(row["timestamp_utc"]) is not None, f"CHECKPOINT_LEDGER_TIMESTAMP_INVALID:{checkpoint_id}")
        require(bool(row["exact_counts"]), f"CHECKPOINT_LEDGER_EXACT_COUNTS_EMPTY:{checkpoint_id}")
        require(bool(row["commands"]), f"CHECKPOINT_LEDGER_COMMANDS_EMPTY:{checkpoint_id}")
        require(bool(row["next_gate"]), f"CHECKPOINT_LEDGER_NEXT_GATE_EMPTY:{checkpoint_id}")
    return {
        "row_count": len(rows),
        "unique_checkpoint_id_count": len(checkpoint_ids),
        "shape_status": "PASS",
    }


def input_inventory(paths: Iterable[Path], repo: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": relative(path, repo),
            "byte_size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(paths, key=lambda item: item.as_posix())
    ]


def verify(repo: Path) -> dict[str, Any]:
    events_path = repo / EVENTS_RELATIVE
    command_ledger_path = repo / COMMAND_LEDGER_RELATIVE
    checkpoint_ledger_path = repo / CHECKPOINT_LEDGER_RELATIVE
    for path in (events_path, command_ledger_path, checkpoint_ledger_path):
        require(path.is_file(), f"EXECUTION_EVIDENCE_INPUT_MISSING:{relative(path, repo)}")

    evidence_paths = (events_path, command_ledger_path, checkpoint_ledger_path)
    core_inputs_before = input_inventory(evidence_paths, repo)

    events = parse_events(events_path)
    event_output_summary = verify_event_output_hashes(events, repo)
    command_rows = parse_tsv(command_ledger_path, COMMAND_LEDGER_FIELDS, "COMMAND_LEDGER")
    checkpoint_rows = parse_tsv(
        checkpoint_ledger_path, CHECKPOINT_LEDGER_FIELDS, "CHECKPOINT_LEDGER"
    )
    command_summary = verify_command_ledger(command_rows, events, repo)
    checkpoint_summary = verify_checkpoint_ledger(checkpoint_rows)
    core_inputs = input_inventory(evidence_paths, repo)
    require(
        core_inputs == core_inputs_before,
        "EXECUTION_EVIDENCE_CHANGED_DURING_VERIFICATION",
    )
    return {
        "format": "trace-exploration-execution-log-verification-v1",
        "status": "PASS",
        "execution_events": {
            "event_count": len(events),
            "first_sequence": events[0]["sequence"],
            "last_sequence": events[-1]["sequence"],
            "unique_sequence_count": len({event["sequence"] for event in events}),
            "sequence_gap_count": 0,
            "required_field_failure_count": 0,
            "field_type_failure_count": 0,
            "status_counts": {
                status: sum(event["status"] == status for event in events)
                for status in sorted({event["status"] for event in events})
            },
        },
        "event_output_hashes": event_output_summary,
        "command_ledger": command_summary,
        "checkpoint_ledger": checkpoint_summary,
        "full_command_log_ready": True,
        "execution_log_sequence_gap_count": 0,
        "execution_event_hash_failure_count": 0,
        "inputs": core_inputs,
        "input_inventory_sha256": canonical_sha256(core_inputs),
        "validation": {
            "execution_event_schema": "PASS",
            "execution_event_sequence": "PASS",
            "existing_output_hashes": "PASS",
            "historical_output_hash_schema": "PASS",
            "mutable_output_latest_writer_hashes": "PASS",
            "command_ledger_reconciliation": "PASS",
            "command_stream_hashes_where_present": "PASS",
            "command_log_nontruncation": "PASS",
            "checkpoint_ledger_shape": "PASS",
        },
    }


def write_atomically(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False
        ) as handle:
            temporary_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def render_receipt(document: dict[str, Any]) -> bytes:
    return json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def failure_receipt(error: Exception) -> dict[str, Any]:
    if isinstance(error, VerificationError):
        code = str(error)
    else:
        code = f"VERIFIER_INTERNAL_ERROR:{type(error).__name__}:{error}"
    return {
        "format": "trace-exploration-execution-log-verification-v1",
        "status": "FAIL",
        "error_codes": [code],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify Round 16A execution evidence.")
    parser.add_argument("--repo", type=Path, default=REPO_ROOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    output_path = repo / OUTPUT_RELATIVE
    try:
        receipt = verify(repo)
        exit_code = 0
    except (OSError, ValueError, KeyError, TypeError, VerificationError) as error:
        receipt = failure_receipt(error)
        exit_code = 1
    content = render_receipt(receipt)
    try:
        write_atomically(output_path, content)
    except OSError as error:
        print(f"EXECUTION_LOG_VERIFICATION_WRITE_FAILED:{error}", file=sys.stderr)
        return 1
    summary = {
        "status": receipt["status"],
        "output": relative(output_path, repo),
        "output_sha256": hashlib.sha256(content).hexdigest(),
    }
    if receipt["status"] == "FAIL":
        summary["error_codes"] = receipt["error_codes"]
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
