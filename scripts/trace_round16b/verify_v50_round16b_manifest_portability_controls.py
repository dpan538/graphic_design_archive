#!/usr/bin/env python3
"""Exercise fail-closed v50 manifest portability controls in an isolated copy."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path, PurePosixPath


REPO = Path(__file__).resolve().parents[2]
MANIFEST_RELATIVE = Path("database/schema-manifest-v50-round16b.json")
VERIFIER_RELATIVE = Path("database/scripts/verify_v50_round16b_manifest.py")
FREEZE_CHECKSUM_RELATIVE = Path("database/FREEZE_V49.sha256")
RAW_RELATIVE = Path(
    "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw"
)
COMMAND_LEDGER_RELATIVE = RAW_RELATIVE / "command-ledger.tsv"
COMMAND_DIRECTORY_RELATIVE = RAW_RELATIVE / "commands"
WRONG_ABSOLUTE_CWD = "/private/tmp/round16b-portability-control-wrong-cwd"
DISAGREEMENT_ABSOLUTE_CWD = "/private/tmp/round16b-portability-control-disagreement"
WRONG_DATABASE = "gda_v50_round16b_9999"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"PORTABILITY_CONTROL_JSON_OBJECT_REQUIRED:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def safe_relative(value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise SystemExit("PORTABILITY_CONTROL_RELATIVE_PATH_INVALID")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts:
        raise SystemExit(f"PORTABILITY_CONTROL_RELATIVE_PATH_INVALID:{value}")
    return Path(*pure.parts)


def copy_governed_file(relative: Path, fixture: Path) -> None:
    source = REPO / relative
    destination = fixture / relative
    if not source.is_file():
        raise SystemExit(f"PORTABILITY_CONTROL_SOURCE_MISSING:{relative.as_posix()}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def governed_inputs() -> tuple[set[Path], dict[str, object], list[str]]:
    manifest = read_json(REPO / MANIFEST_RELATIVE)
    v49_base = manifest.get("v49Base")
    if not isinstance(v49_base, dict):
        raise SystemExit("PORTABILITY_CONTROL_V49_BASE_INVALID")
    freeze_relative = safe_relative(v49_base.get("freezeManifest"))
    freeze = read_json(REPO / freeze_relative)
    receipt_descriptor = manifest.get("executionReceipt")
    if not isinstance(receipt_descriptor, dict):
        raise SystemExit("PORTABILITY_CONTROL_RECEIPT_DESCRIPTOR_INVALID")
    receipt_relative = safe_relative(receipt_descriptor.get("path"))
    receipt = read_json(REPO / receipt_relative)
    managed = manifest.get("perFileSha256")
    frozen = freeze.get("perFileSha256")
    replays = receipt.get("freshReplays")
    command_ids = receipt.get("governedCommandIds")
    if (
        not isinstance(managed, dict)
        or not isinstance(frozen, dict)
        or not isinstance(replays, list)
        or not isinstance(command_ids, list)
        or any(not isinstance(command_id, str) for command_id in command_ids)
    ):
        raise SystemExit("PORTABILITY_CONTROL_GOVERNED_INPUT_CONTRACT_INVALID")

    relative_files = {
        MANIFEST_RELATIVE,
        FREEZE_CHECKSUM_RELATIVE,
        freeze_relative,
        receipt_relative,
        COMMAND_LEDGER_RELATIVE,
        *(safe_relative(value) for value in managed),
        *(safe_relative(value) for value in frozen),
    }
    for command_id in command_ids:
        relative_files.update(
            COMMAND_DIRECTORY_RELATIVE / f"{command_id}.{suffix}"
            for suffix in ("stdout.log", "stderr.log", "meta.json")
        )
    for replay in replays:
        if not isinstance(replay, dict):
            raise SystemExit("PORTABILITY_CONTROL_REPLAY_CONTRACT_INVALID")
        evidence = replay.get("concurrencyEvidence")
        if not isinstance(evidence, dict):
            raise SystemExit("PORTABILITY_CONTROL_EVIDENCE_CONTRACT_INVALID")
        evidence_relative = safe_relative(evidence.get("directory"))
        per_file = evidence.get("perFileSha256")
        if not isinstance(per_file, dict):
            raise SystemExit("PORTABILITY_CONTROL_EVIDENCE_CONTRACT_INVALID")
        relative_files.add(evidence_relative / "CHECKSUMS.sha256")
        relative_files.update(evidence_relative / safe_relative(name) for name in per_file)
    return relative_files, receipt, command_ids


def build_fixture(fixture: Path) -> tuple[dict[str, object], list[str], set[Path]]:
    relative_files, receipt, command_ids = governed_inputs()
    for relative in sorted(relative_files):
        copy_governed_file(relative, fixture)
    return receipt, command_ids, relative_files


def run_verifier(fixture: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(fixture / VERIFIER_RELATIVE)],
        cwd=fixture,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def require_success(fixture: Path, case: str, marker: str) -> None:
    result = run_verifier(fixture)
    if result.returncode != 0 or marker not in result.stdout:
        raise SystemExit(
            f"PORTABILITY_CONTROL_UNEXPECTED_BASELINE:{case}:exit={result.returncode}:"
            f"stdout={result.stdout!r}:stderr={result.stderr!r}"
        )
    print(f"V50_MANIFEST_PORTABILITY_CONTROL=PASS case={case} marker={marker}")


def require_failure(fixture: Path, case: str, marker: str) -> None:
    result = run_verifier(fixture)
    combined = result.stdout + result.stderr
    if result.returncode == 0 or marker not in combined:
        raise SystemExit(
            f"PORTABILITY_CONTROL_DID_NOT_FAIL_CLOSED:{case}:exit={result.returncode}:"
            f"expected={marker}:stdout={result.stdout!r}:stderr={result.stderr!r}"
        )
    print(f"V50_MANIFEST_PORTABILITY_CONTROL=PASS case={case} marker={marker}")


def load_ledger(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
        fieldnames = reader.fieldnames
    if not fieldnames:
        raise SystemExit("PORTABILITY_CONTROL_LEDGER_HEADER_INVALID")
    return fieldnames, rows


def write_ledger(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def replace_ledger_field(
    fixture: Path, command_id: str, field: str, old: str, new: str
) -> None:
    ledger_path = fixture / COMMAND_LEDGER_RELATIVE
    fieldnames, rows = load_ledger(ledger_path)
    matches = [row for row in rows if row.get("command_id") == command_id]
    if len(matches) != 1 or matches[0].get(field) is None:
        raise SystemExit(f"PORTABILITY_CONTROL_LEDGER_ROW_INVALID:{command_id}:{field}")
    current = matches[0][field]
    if old not in current:
        raise SystemExit(
            f"PORTABILITY_CONTROL_LEDGER_MUTATION_TARGET_MISSING:{command_id}:{field}"
        )
    matches[0][field] = current.replace(old, new)
    write_ledger(ledger_path, fieldnames, rows)


def command_meta_path(fixture: Path, command_id: str) -> Path:
    return fixture / COMMAND_DIRECTORY_RELATIVE / f"{command_id}.meta.json"


def first_replay(receipt: dict[str, object]) -> dict[str, object]:
    replays = receipt.get("freshReplays")
    if not isinstance(replays, list) or not replays or not isinstance(replays[0], dict):
        raise SystemExit("PORTABILITY_CONTROL_FIRST_REPLAY_INVALID")
    return replays[0]


def command_id(replay: dict[str, object], command_class: str) -> str:
    command_ids = replay.get("commandIds")
    if not isinstance(command_ids, dict) or not isinstance(command_ids.get(command_class), str):
        raise SystemExit(f"PORTABILITY_CONTROL_COMMAND_ID_INVALID:{command_class}")
    return command_ids[command_class]


def restore_after(
    fixture: Path,
    relative_files: Iterable[Path],
    mutation: Callable[[], None],
    assertion: Callable[[], None],
    cleanup: Callable[[], None] | None = None,
) -> None:
    paths = [fixture / relative for relative in relative_files]
    snapshots = {path: path.read_bytes() for path in paths}
    try:
        mutation()
        assertion()
    finally:
        for path, content in snapshots.items():
            path.write_bytes(content)
        if cleanup is not None:
            cleanup()


def rebind_receipt_hash(fixture: Path) -> None:
    manifest_path = fixture / MANIFEST_RELATIVE
    manifest = read_json(manifest_path)
    descriptor = manifest.get("executionReceipt")
    per_file = manifest.get("perFileSha256")
    if not isinstance(descriptor, dict) or not isinstance(per_file, dict):
        raise SystemExit("PORTABILITY_CONTROL_MANIFEST_RECEIPT_BINDING_INVALID")
    receipt_relative = safe_relative(descriptor.get("path"))
    digest = sha256(fixture / receipt_relative)
    descriptor["sha256"] = digest
    per_file[receipt_relative.as_posix()] = digest
    write_json(manifest_path, manifest)


def mutate_wrong_metadata_cwd(
    fixture: Path, replay: dict[str, object], historical_cwd: str
) -> None:
    test_id = command_id(replay, "test")
    meta_relative = COMMAND_DIRECTORY_RELATIVE / f"{test_id}.meta.json"
    changed = [meta_relative, COMMAND_LEDGER_RELATIVE]

    def mutation() -> None:
        meta_path = fixture / meta_relative
        meta = read_json(meta_path)
        if meta.get("cwd") != historical_cwd:
            raise SystemExit("PORTABILITY_CONTROL_HISTORICAL_CWD_UNEXPECTED")
        meta["cwd"] = WRONG_ABSOLUTE_CWD
        write_json(meta_path, meta)
        replace_ledger_field(
            fixture, test_id, "cwd", historical_cwd, WRONG_ABSOLUTE_CWD
        )

    restore_after(
        fixture,
        changed,
        mutation,
        lambda: require_failure(
            fixture,
            "wrong-metadata-cwd",
            f"V50_RACE_COMMAND_OUTPUT_MISMATCH:{replay['database']}",
        ),
    )


def mutate_metadata_ledger_disagreement(
    fixture: Path, replay: dict[str, object], historical_cwd: str
) -> None:
    test_id = command_id(replay, "test")
    meta_relative = COMMAND_DIRECTORY_RELATIVE / f"{test_id}.meta.json"

    def mutation() -> None:
        meta_path = fixture / meta_relative
        meta = read_json(meta_path)
        if meta.get("cwd") != historical_cwd:
            raise SystemExit("PORTABILITY_CONTROL_HISTORICAL_CWD_UNEXPECTED")
        meta["cwd"] = DISAGREEMENT_ABSOLUTE_CWD
        write_json(meta_path, meta)

    restore_after(
        fixture,
        [meta_relative],
        mutation,
        lambda: require_failure(
            fixture,
            "metadata-ledger-cwd-disagreement",
            f"V50_COMMAND_META_INVALID:{test_id}",
        ),
    )


def mutate_wrong_stdout_evidence_path(
    fixture: Path, replay: dict[str, object], historical_cwd: str
) -> None:
    test_id = command_id(replay, "test")
    stdout_relative = COMMAND_DIRECTORY_RELATIVE / f"{test_id}.stdout.log"
    meta_relative = COMMAND_DIRECTORY_RELATIVE / f"{test_id}.meta.json"
    evidence = replay.get("concurrencyEvidence")
    if not isinstance(evidence, dict):
        raise SystemExit("PORTABILITY_CONTROL_EVIDENCE_CONTRACT_INVALID")
    evidence_relative = safe_relative(evidence.get("directory"))
    expected_path = str(Path(historical_cwd) / evidence_relative)
    wrong_path = str(Path(WRONG_ABSOLUTE_CWD) / evidence_relative)

    def mutation() -> None:
        stdout_path = fixture / stdout_relative
        stdout = stdout_path.read_text(encoding="utf-8")
        if stdout.count(expected_path) != 1:
            raise SystemExit("PORTABILITY_CONTROL_STDOUT_PATH_TARGET_INVALID")
        stdout_path.write_text(stdout.replace(expected_path, wrong_path), encoding="utf-8")
        meta_path = fixture / meta_relative
        meta = read_json(meta_path)
        meta["stdout_sha256"] = sha256(stdout_path)
        write_json(meta_path, meta)

    restore_after(
        fixture,
        [stdout_relative, meta_relative],
        mutation,
        lambda: require_failure(
            fixture,
            "wrong-historical-stdout-evidence-path",
            f"V50_RACE_COMMAND_OUTPUT_MISMATCH:{replay['database']}",
        ),
    )


def mutate_wrong_database_suffix(fixture: Path, receipt_relative: Path) -> None:
    receipt_path = fixture / receipt_relative
    receipt = read_json(receipt_path)
    replay = first_replay(receipt)
    old_database = replay.get("database")
    if not isinstance(old_database, str) or old_database == WRONG_DATABASE:
        raise SystemExit("PORTABILITY_CONTROL_DATABASE_TARGET_INVALID")
    evidence = replay.get("concurrencyEvidence")
    if not isinstance(evidence, dict):
        raise SystemExit("PORTABILITY_CONTROL_EVIDENCE_CONTRACT_INVALID")
    old_evidence_relative = safe_relative(evidence.get("directory"))
    new_evidence_relative = Path(
        old_evidence_relative.as_posix().replace(old_database, WRONG_DATABASE)
    )
    command_ids = [command_id(replay, key) for key in ("replay", "test", "dump", "schemaHash")]
    meta_relatives = [
        COMMAND_DIRECTORY_RELATIVE / f"{value}.meta.json" for value in command_ids
    ]
    stdout_relatives = [
        COMMAND_DIRECTORY_RELATIVE / f"{value}.stdout.log"
        for value in command_ids[:2]
    ]
    changed = [
        MANIFEST_RELATIVE,
        receipt_relative,
        COMMAND_LEDGER_RELATIVE,
        *meta_relatives,
        *stdout_relatives,
    ]

    def mutation() -> None:
        shutil.copytree(
            fixture / old_evidence_relative,
            fixture / new_evidence_relative,
        )
        local_receipt = read_json(receipt_path)
        local_replay = first_replay(local_receipt)
        local_replay["database"] = WRONG_DATABASE
        local_evidence = local_replay.get("concurrencyEvidence")
        if not isinstance(local_evidence, dict):
            raise SystemExit("PORTABILITY_CONTROL_EVIDENCE_CONTRACT_INVALID")
        local_evidence["directory"] = new_evidence_relative.as_posix()
        write_json(receipt_path, local_receipt)

        for local_id, meta_relative in zip(command_ids, meta_relatives, strict=True):
            meta_path = fixture / meta_relative
            meta = read_json(meta_path)
            argv = meta.get("argv")
            command = meta.get("command")
            if not isinstance(argv, list) or not isinstance(command, str):
                raise SystemExit(f"PORTABILITY_CONTROL_COMMAND_META_INVALID:{local_id}")
            meta["argv"] = [
                value.replace(old_database, WRONG_DATABASE) if isinstance(value, str) else value
                for value in argv
            ]
            meta["command"] = command.replace(old_database, WRONG_DATABASE)
            write_json(meta_path, meta)
            replace_ledger_field(
                fixture, local_id, "command", old_database, WRONG_DATABASE
            )

        for local_id, stdout_relative, meta_relative in zip(
            command_ids[:2], stdout_relatives, meta_relatives[:2], strict=True
        ):
            stdout_path = fixture / stdout_relative
            stdout = stdout_path.read_text(encoding="utf-8")
            if old_database not in stdout:
                raise SystemExit(
                    f"PORTABILITY_CONTROL_STDOUT_DATABASE_TARGET_MISSING:{local_id}"
                )
            stdout_path.write_text(
                stdout.replace(old_database, WRONG_DATABASE), encoding="utf-8"
            )
            meta_path = fixture / meta_relative
            meta = read_json(meta_path)
            meta["stdout_sha256"] = sha256(stdout_path)
            write_json(meta_path, meta)
        rebind_receipt_hash(fixture)

    restore_after(
        fixture,
        changed,
        mutation,
        lambda: require_failure(
            fixture,
            "wrong-database-suffix",
            "V50_EXECUTION_RECEIPT_DATABASE_IDENTITY_MISMATCH",
        ),
        cleanup=lambda: shutil.rmtree(fixture / new_evidence_relative),
    )


def mutate_wrong_evidence_checksum(fixture: Path, replay: dict[str, object]) -> None:
    evidence = replay.get("concurrencyEvidence")
    if not isinstance(evidence, dict):
        raise SystemExit("PORTABILITY_CONTROL_EVIDENCE_CONTRACT_INVALID")
    evidence_relative = safe_relative(evidence.get("directory"))
    checksums_relative = evidence_relative / "CHECKSUMS.sha256"

    def mutation() -> None:
        path = fixture / checksums_relative
        content = path.read_text(encoding="utf-8")
        if not content or content[0] not in "0123456789abcdef":
            raise SystemExit("PORTABILITY_CONTROL_CHECKSUM_TARGET_INVALID")
        replacement = "0" if content[0] != "0" else "1"
        path.write_text(replacement + content[1:], encoding="utf-8")

    restore_after(
        fixture,
        [checksums_relative],
        mutation,
        lambda: require_failure(
            fixture,
            "wrong-evidence-checksum",
            f"V50_RACE_CHECKSUM_LEDGER_DRIFT:{replay['database']}",
        ),
    )


def main() -> int:
    source_inputs, source_receipt, _ = governed_inputs()
    source_hashes_before = {relative: sha256(REPO / relative) for relative in source_inputs}
    receipt_descriptor = read_json(REPO / MANIFEST_RELATIVE).get("executionReceipt")
    if not isinstance(receipt_descriptor, dict):
        raise SystemExit("PORTABILITY_CONTROL_RECEIPT_DESCRIPTOR_INVALID")
    receipt_relative = safe_relative(receipt_descriptor.get("path"))

    with tempfile.TemporaryDirectory(prefix="round16b-v50-portability-controls-") as temporary:
        fixture = Path(temporary) / "fixture"
        fixture.mkdir()
        receipt, _, fixture_inputs = build_fixture(fixture)
        if fixture_inputs != source_inputs:
            raise SystemExit("PORTABILITY_CONTROL_FIXTURE_INPUT_SET_MISMATCH")
        replay = first_replay(receipt)
        test_id = command_id(replay, "test")
        test_meta = read_json(command_meta_path(fixture, test_id))
        historical_cwd = test_meta.get("cwd")
        if not isinstance(historical_cwd, str) or not Path(historical_cwd).is_absolute():
            raise SystemExit("PORTABILITY_CONTROL_HISTORICAL_CWD_INVALID")

        require_success(fixture, "valid-baseline", "V50_ROUND16B_MANIFEST=PASS")
        mutate_wrong_metadata_cwd(fixture, replay, historical_cwd)
        mutate_metadata_ledger_disagreement(fixture, replay, historical_cwd)
        mutate_wrong_stdout_evidence_path(fixture, replay, historical_cwd)
        mutate_wrong_database_suffix(fixture, receipt_relative)
        mutate_wrong_evidence_checksum(fixture, replay)

        # Mutation restoration is itself fail-closed: the fixture must return to
        # the same verified baseline before the temporary directory is removed.
        require_success(fixture, "restored-baseline", "V50_ROUND16B_MANIFEST=PASS")

    source_hashes_after = {relative: sha256(REPO / relative) for relative in source_inputs}
    if source_hashes_after != source_hashes_before:
        raise SystemExit("PORTABILITY_CONTROL_SOURCE_ARTIFACT_MUTATION_DETECTED")
    if source_receipt != read_json(REPO / receipt_relative):
        raise SystemExit("PORTABILITY_CONTROL_SOURCE_RECEIPT_MUTATION_DETECTED")
    print(
        "V50_MANIFEST_PORTABILITY_CONTROLS=PASS controls=6 adversarial=5 "
        "restoration_check=PASS governed_source_mutation_count=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
