#!/usr/bin/env python3
"""Verify the Round 16B clean-baseline import evidence artifacts.

The verifier is intentionally read-only. It validates the embedded stale-session
classification, the declared BASE..TIP path set, Git mode/blob identity, and the
SHA-256 digest of every declared Round 16B blob. By default it verifies the
current Git index so it can run before Commit 1; pass ``--integration-tree HEAD``
after the commit is created.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RECEIPT = REPOSITORY_ROOT / "STALE_SESSION_RECOVERY_RECEIPT.json"
DEFAULT_LEDGER = (
    REPOSITORY_ROOT
    / "docs/audits/v49-exploration-round16b-main-integration"
    / "round16b-path-equivalence-ledger.v1.json"
)


def git(*arguments: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY_ROOT,
        check=True,
        input=input_bytes,
        stdout=subprocess.PIPE,
    ).stdout


def nul_paths(*arguments: str) -> list[str]:
    payload = git(*arguments)
    return [
        item.decode("utf-8", "surrogateescape")
        for item in payload.split(b"\0")
        if item
    ]


def tree_entries(tree: str) -> dict[str, tuple[str, str]]:
    if tree == "INDEX":
        records = git("ls-files", "-s", "-z").split(b"\0")
        result: dict[str, tuple[str, str]] = {}
        for record in records:
            if not record:
                continue
            metadata, raw_path = record.split(b"\t", 1)
            mode, oid, stage = metadata.decode("ascii").split()
            if stage != "0":
                raise AssertionError(
                    f"unmerged index entry for {raw_path!r} at stage {stage}"
                )
            path = raw_path.decode("utf-8", "surrogateescape")
            result[path] = (mode, oid)
        return result

    records = git("ls-tree", "-r", "-z", tree).split(b"\0")
    result = {}
    for record in records:
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, object_type, oid = metadata.decode("ascii").split()
        if object_type != "blob":
            raise AssertionError(
                f"unsupported {object_type} entry at {raw_path!r} in {tree}"
            )
        path = raw_path.decode("utf-8", "surrogateescape")
        result[path] = (mode, oid)
    return result


def blob_sha256s(object_ids: Iterable[str]) -> dict[str, str]:
    unique_ids = sorted(set(object_ids))
    process = subprocess.Popen(
        ["git", "cat-file", "--batch"],
        cwd=REPOSITORY_ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    digests: dict[str, str] = {}
    try:
        for requested_oid in unique_ids:
            process.stdin.write(requested_oid.encode("ascii") + b"\n")
            process.stdin.flush()
            header = process.stdout.readline().decode("ascii").rstrip("\n")
            returned_oid, object_type, raw_size = header.split()
            if object_type != "blob":
                raise AssertionError(
                    f"expected blob {requested_oid}, got {object_type}"
                )
            payload = process.stdout.read(int(raw_size))
            terminator = process.stdout.read(1)
            if len(payload) != int(raw_size) or terminator != b"\n":
                raise AssertionError(f"truncated cat-file payload for {requested_oid}")
            if returned_oid != requested_oid:
                raise AssertionError(
                    f"cat-file returned {returned_oid} for {requested_oid}"
                )
            digests[requested_oid] = hashlib.sha256(payload).hexdigest()
    finally:
        process.stdin.close()
        return_code = process.wait()
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, process.args)
    return digests


def expect(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def validate_receipt(receipt: dict[str, Any], failures: list[str]) -> None:
    classification = receipt["stale_session_classification"]
    entries = classification["entries"]
    observed_classes = Counter(entry["classification"] for entry in entries)
    expect(
        len(entries) == classification["entry_count"] == 10_951,
        "stale-session classification does not contain exactly 10,951 entries",
        failures,
    )
    expect(
        all(
            observed_classes[name] == count
            for name, count in classification["classification_counts"].items()
        ),
        "embedded classification counts do not match its entries",
        failures,
    )
    expect(
        receipt["required_result"]["STALE_ROUND16B_PROCESS_CONTINUED"] is False,
        "stale Round 16B process continuation flag is not false",
        failures,
    )
    stopped = receipt["process_inventory_and_disposition"][
        "stale_temporary_postgresql_clusters"
    ]
    expect(len(stopped) == 6, "receipt does not record six stopped clusters", failures)
    expect(
        all(item["disposition"] == "STOPPED_FAST" for item in stopped),
        "not every stale temporary PostgreSQL cluster is marked STOPPED_FAST",
        failures,
    )


def validate_ledger(
    ledger: dict[str, Any], integration_tree: str, failures: list[str]
) -> None:
    identities = ledger["identities"]
    base = identities["base_sha"]
    source = identities["round16b_source_sha"]
    expected_paths = nul_paths("diff", "--name-only", "-z", base, source)
    rows = ledger["declared_paths"]
    row_paths = [row["path"] for row in rows]

    expect(len(expected_paths) == 4_362, "BASE..TIP path count is not 4,362", failures)
    expect(row_paths == expected_paths, "ledger path order/set differs from BASE..TIP", failures)
    expect(len(row_paths) == len(set(row_paths)), "ledger contains duplicate paths", failures)

    source_entries = tree_entries(source)
    integration_entries = tree_entries(integration_tree)
    object_ids = [source_entries[path][1] for path in expected_paths]
    digests = blob_sha256s(object_ids)

    mismatch_count = 0
    omission_count = 0
    for row in rows:
        path = row["path"]
        source_entry = source_entries.get(path)
        integration_entry = integration_entries.get(path)
        if integration_entry is None:
            omission_count += 1
            continue
        if source_entry != integration_entry:
            mismatch_count += 1
        source_record = row["round16b_source"]
        integration_record = row["integration_import"]
        expected_digest = digests[source_entry[1]] if source_entry else None
        if source_record != {
            "mode": source_entry[0],
            "blob_id": source_entry[1],
            "sha256": expected_digest,
        }:
            mismatch_count += 1
        if integration_record != {
            "mode": integration_entry[0],
            "blob_id": integration_entry[1],
            "sha256": expected_digest,
        }:
            mismatch_count += 1
        if row["equivalence_status"] != "BYTE_EQUIVALENT":
            mismatch_count += 1

    permitted_extras = {
        item["path"] for item in ledger["explained_integration_only_paths"]
    }
    actual_extras = set(integration_entries) - set(source_entries)
    unexplained_extras = actual_extras - permitted_extras
    expect(mismatch_count == 0, f"declared-path mismatch count is {mismatch_count}", failures)
    expect(omission_count == 0, f"declared-path omission count is {omission_count}", failures)
    expect(
        not unexplained_extras,
        f"unexplained integration-only paths: {sorted(unexplained_extras)!r}",
        failures,
    )

    summary = ledger["summary"]
    expect(
        summary["ROUND16B_DECLARED_PATH_MISMATCH_COUNT"] == 0,
        "ledger records a nonzero declared-path mismatch count",
        failures,
    )
    expect(
        summary["ROUND16B_UNEXPLAINED_PATH_OMISSION_COUNT"] == 0,
        "ledger records a nonzero unexplained omission count",
        failures,
    )
    expect(
        summary["ROUND16B_UNEXPLAINED_EXTRA_PATH_COUNT"] == 0,
        "ledger records a nonzero unexplained extra-path count",
        failures,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument(
        "--integration-tree",
        default="INDEX",
        help="Git tree-ish to verify, or INDEX (default)",
    )
    arguments = parser.parse_args()

    receipt = json.loads(arguments.receipt.read_text(encoding="utf-8"))
    ledger = json.loads(arguments.ledger.read_text(encoding="utf-8"))
    failures: list[str] = []
    validate_receipt(receipt, failures)
    validate_ledger(ledger, arguments.integration_tree, failures)

    result = {
        "status": "PASS" if not failures else "FAIL",
        "integration_tree": arguments.integration_tree,
        "stale_session_entry_count": receipt["stale_session_classification"][
            "entry_count"
        ],
        "round16b_declared_path_count": ledger["summary"][
            "round16b_declared_path_count"
        ],
        "failure_count": len(failures),
        "failures": failures,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
