#!/usr/bin/env python3
"""Verify the forward-only Round 16B database inventory without writing files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "database/schema-manifest-v50-round16b.json"
EXPECTED_SCHEMA = "gda-v50.trace-exploration-higher-order-association/v1"
EXPECTED_PHASE = "round16b-research-schema-capability"
REQUIRED_REPLAY = [
    "database/migrations/014_exploration_v3_higher_order_associations.sql",
    "database/functions/020_exploration_v3_integrity.sql",
    "database/views/003_exploration_v3_read_contract.sql",
    "database/roles/008_exploration_v3_grants.sql",
]
REQUIRED_VERIFICATION = [
    "database/scripts/verify_v50_round16b_manifest.py",
    "database/scripts/replay_v50_round16b.sh",
    "database/tests/014_exploration_v3_higher_order_associations.sql",
    "database/scripts/run_v50_round16b_tests.sh",
]
EXECUTION_RECEIPT = (
    "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/"
    "v50-round16b-replay-receipt-checkpoint011.json"
)
RAW_ROOT = ROOT / "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw"
COMMAND_LEDGER = RAW_ROOT / "command-ledger.tsv"
COMMAND_DIRECTORY = RAW_ROOT / "commands"
RACE_EVIDENCE_PREFIX = (
    "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/"
    "v50-round16b-seal-race"
)
RACE_EVIDENCE_FILES = (
    "child-first.contender.log",
    "child-first.owner.log",
    "child-first.retry-and-invariant.log",
    "createdb.log",
    "dropdb.log",
    "repeatable-read.log",
    "seal-first.contender.log",
    "seal-first.invariant.log",
    "seal-first.owner.log",
    "seal-first.retry.log",
    "serializable.log",
    "setup-owner.log",
)
EXPECTED_REPLAY_DATABASES = {
    "gda_v50_round16b_2317",
    "gda_v50_round16b_2318",
}
MANAGED_FILES = {
    "database/VERSION",
    *REQUIRED_REPLAY,
    "database/tests/014_exploration_v3_higher_order_associations.sql",
    "database/scripts/replay_v50_round16b.sh",
    "database/scripts/verify_v50_round16b_manifest.py",
    "database/scripts/run_v50_round16b_tests.sh",
    "database/ROUND16B_V50.md",
    "docs/adr/0006-v50-exploration-v3-database-contract.md",
    EXECUTION_RECEIPT,
}
FREEZE_SEQUENCE_KEYS = {
    "migrationSequence": "database/migrations/",
    "functionSequence": "database/functions/",
    "roleSequence": "database/roles/",
    "viewSequence": "database/views/",
}
CLUSTER_ROLE_PRECONDITION = "database/roles/001_cluster_roles.sql"
REPLAY_BOUNDARY = (
    "Apply every sequence entry in database/FREEZE_V49.json before the additive v50 sequence."
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_prefix(path: Path, prefix: str) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.startswith(prefix))


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def is_sha256(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def require_string_list(value: object, code: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise SystemExit(code)
    if len(value) != len(set(value)):
        raise SystemExit(code + "_DUPLICATE")
    return value


def command_ledger_rows() -> dict[str, dict[str, str]]:
    with COMMAND_LEDGER.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if not rows or any(not row.get("command_id") for row in rows):
        raise SystemExit("V50_COMMAND_LEDGER_INVALID")
    result = {row["command_id"]: row for row in rows}
    if len(result) != len(rows):
        raise SystemExit("V50_COMMAND_LEDGER_DUPLICATE_ID")
    return result


def verified_command(
    command_id: str, rows: dict[str, dict[str, str]]
) -> tuple[dict[str, object], str]:
    row = rows.get(command_id)
    if row is None or row.get("exit_code") != "0":
        raise SystemExit(f"V50_COMMAND_LEDGER_RESOLUTION_INVALID:{command_id}")
    expected_suffixes = {
        "stdout_path": f"/raw/commands/{command_id}.stdout.log",
        "stderr_path": f"/raw/commands/{command_id}.stderr.log",
        "meta_path": f"/raw/commands/{command_id}.meta.json",
    }
    for key, suffix in expected_suffixes.items():
        if not row.get(key, "").endswith(suffix):
            raise SystemExit(f"V50_COMMAND_LEDGER_PATH_INVALID:{command_id}:{key}")
    stdout_path = COMMAND_DIRECTORY / f"{command_id}.stdout.log"
    stderr_path = COMMAND_DIRECTORY / f"{command_id}.stderr.log"
    meta_path = COMMAND_DIRECTORY / f"{command_id}.meta.json"
    if not all(path.is_file() for path in (stdout_path, stderr_path, meta_path)):
        raise SystemExit(f"V50_COMMAND_EVIDENCE_MISSING:{command_id}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if (
        meta.get("command_id") != command_id
        or meta.get("exit_code") != 0
        or meta.get("timed_out") is not False
        or meta.get("launch_error") != ""
        or meta.get("command") != row.get("command")
        or meta.get("cwd") != row.get("cwd")
        or not isinstance(meta.get("cwd"), str)
        or not Path(str(meta["cwd"])).is_absolute()
        or meta.get("stdout_sha256") != sha256(stdout_path)
        or meta.get("stderr_sha256") != sha256(stderr_path)
    ):
        raise SystemExit(f"V50_COMMAND_META_INVALID:{command_id}")
    argv = meta.get("argv")
    if not isinstance(argv, list) or any(not isinstance(value, str) for value in argv):
        raise SystemExit(f"V50_COMMAND_ARGV_INVALID:{command_id}")
    return meta, stdout_path.read_text(encoding="utf-8")


def verify_race_evidence(
    replay: dict[str, object], test_stdout: str, test_meta: dict[str, object]
) -> None:
    database = replay["database"]
    evidence = replay.get("concurrencyEvidence")
    expected_directory = f"{RACE_EVIDENCE_PREFIX}/{database}"
    if not isinstance(evidence, dict) or evidence.get("directory") != expected_directory:
        raise SystemExit(f"V50_RACE_EVIDENCE_DESCRIPTOR_INVALID:{database}")
    expected_checksums_hash = evidence.get("checksumsSha256")
    per_file = evidence.get("perFileSha256")
    if (
        not is_sha256(expected_checksums_hash)
        or not isinstance(per_file, dict)
        or set(per_file) != set(RACE_EVIDENCE_FILES)
        or any(not is_sha256(value) for value in per_file.values())
    ):
        raise SystemExit(f"V50_RACE_EVIDENCE_HASH_CONTRACT_INVALID:{database}")
    evidence_directory = ROOT / expected_directory
    checksums_path = evidence_directory / "CHECKSUMS.sha256"
    if not checksums_path.is_file() or sha256(checksums_path) != expected_checksums_hash:
        raise SystemExit(f"V50_RACE_CHECKSUM_LEDGER_DRIFT:{database}")
    checksum_rows: dict[str, str] = {}
    for line in checksums_path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 2 or fields[1] in checksum_rows:
            raise SystemExit(f"V50_RACE_CHECKSUM_LEDGER_INVALID:{database}")
        checksum_rows[fields[1]] = fields[0]
    if set(checksum_rows) != set(RACE_EVIDENCE_FILES) or checksum_rows != per_file:
        raise SystemExit(f"V50_RACE_CHECKSUM_SET_MISMATCH:{database}")
    for name, expected in checksum_rows.items():
        path = evidence_directory / name
        if not path.is_file() or sha256(path) != expected:
            raise SystemExit(f"V50_RACE_EVIDENCE_FILE_DRIFT:{database}:{name}")
    logs = {
        name: (evidence_directory / name).read_text(encoding="utf-8")
        for name in RACE_EVIDENCE_FILES
    }
    required_patterns = {
        "setup-owner.log": r"RACE_DATABASE_OWNER=\S+ FIXTURE_PARENTS=4",
        "child-first.contender.log": (
            r"40001:.*AGGREGATE_MEMBERSHIP_CONCURRENT_WRITE_RETRY"
        ),
        "child-first.retry-and-invariant.log": (
            r"CHILD_FIRST_RETRY_SEAL_AND_CONTENT=PASS CHILD_INCLUDED=1"
        ),
        "seal-first.contender.log": (
            r"40001:.*AGGREGATE_MEMBERSHIP_CONCURRENT_WRITE_RETRY"
        ),
        "seal-first.retry.log": r"55000:.*SEALED_AGGREGATE_CHILD_INSERT_FORBIDDEN",
        "seal-first.invariant.log": (
            r"SEAL_FIRST_POST_RACE_INVARIANT=PASS CHILD_COUNT=0"
        ),
        "repeatable-read.log": (
            r"25000:.*AGGREGATE_MEMBERSHIP_WRITES_REQUIRE_READ_COMMITTED"
        ),
        "serializable.log": (
            r"25000:.*AGGREGATE_MEMBERSHIP_WRITES_REQUIRE_READ_COMMITTED"
        ),
    }
    for name, pattern in required_patterns.items():
        if re.search(pattern, logs[name]) is None:
            raise SystemExit(f"V50_RACE_EVIDENCE_MARKER_MISSING:{database}:{name}")
    if any("ERROR:" in logs[name] for name in (
        "child-first.owner.log", "seal-first.owner.log",
        "child-first.retry-and-invariant.log", "seal-first.invariant.log",
    )):
        raise SystemExit(f"V50_RACE_OWNER_OR_INVARIANT_FAILURE:{database}")
    expected_facts = {
        "childFirstLoserSqlstate": "40001",
        "sealFirstLoserSqlstate": "40001",
        "sealFirstRetrySqlstate": "55000",
        "repeatableReadSqlstate": "25000",
        "serializableSqlstate": "25000",
        "childFirstIncludedCount": 1,
        "sealFirstChildCount": 0,
        "disposableDatabaseDropped": True,
    }
    if any(evidence.get(key) != value for key, value in expected_facts.items()):
        raise SystemExit(f"V50_RACE_RECEIPT_FACT_MISMATCH:{database}")
    path_markers = re.findall(
        r"^V50_SEAL_RACE_EVIDENCE_DIR=(\S+) CHECKSUMS_SHA256="
        + re.escape(str(expected_checksums_hash))
        + r"$",
        test_stdout,
        flags=re.MULTILINE,
    )
    recorded_command_root = Path(str(test_meta["cwd"]))
    expected_recorded_directory = str(recorded_command_root / expected_directory)
    if (
        "V50_SEAL_RACE_CHILD_FIRST=PASS LOSER_SQLSTATE=40001 "
        "RETRY_SEAL=PASS CHILD_INCLUDED=1" not in test_stdout
        or "V50_SEAL_RACE_SEAL_FIRST=PASS LOSER_SQLSTATE=40001 "
        "RETRY_CHILD_SQLSTATE=55000 CHILD_COUNT=0" not in test_stdout
        or "V50_SEAL_ISOLATION_GUARDS=PASS REPEATABLE_READ_SQLSTATE=25000 "
        "SERIALIZABLE_SQLSTATE=25000" not in test_stdout
        or "V50_RACE_DATABASE_DISPOSED=PASS" not in test_stdout
        or path_markers != [expected_recorded_directory]
    ):
        raise SystemExit(f"V50_RACE_COMMAND_OUTPUT_MISMATCH:{database}")


def verify_freeze(payload: dict[str, object]) -> tuple[dict[str, object], list[str]]:
    v49_base = payload.get("v49Base")
    if not isinstance(v49_base, dict):
        raise SystemExit("V49_BASE_CONTRACT_INVALID")
    freeze_relative = v49_base.get("freezeManifest")
    expected_freeze = v49_base.get("freezeManifestSha256")
    if not isinstance(freeze_relative, str) or not isinstance(expected_freeze, str):
        raise SystemExit("V49_FREEZE_MANIFEST_CONTRACT_INVALID")
    freeze_path = ROOT / freeze_relative
    if sha256(freeze_path) != expected_freeze:
        raise SystemExit("V49_FREEZE_MANIFEST_DRIFT")
    freeze_checksum_path = ROOT / "database/FREEZE_V49.sha256"
    checksum_fields = freeze_checksum_path.read_text(encoding="utf-8").split()
    if len(checksum_fields) != 2 or checksum_fields != [expected_freeze, freeze_relative]:
        raise SystemExit("V49_FREEZE_CHECKSUM_LEDGER_MISMATCH")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if freeze.get("version") != 49 or freeze.get("freezeStatus") != "FROZEN":
        raise SystemExit("V49_FREEZE_METADATA_INVALID")
    frozen_hashes = freeze.get("perFileSha256")
    if not isinstance(frozen_hashes, dict) or any(
        not isinstance(path, str) or not isinstance(digest, str)
        for path, digest in frozen_hashes.items()
    ):
        raise SystemExit("V49_FREEZE_FILE_HASH_CONTRACT_INVALID")
    if freeze.get("fileCount") != len(frozen_hashes):
        raise SystemExit("V49_FREEZE_FILE_COUNT_MISMATCH")
    frozen_mismatches = [
        relative
        for relative, expected in frozen_hashes.items()
        if not (ROOT / relative).is_file() or sha256(ROOT / relative) != expected
    ]
    if frozen_mismatches:
        raise SystemExit("V49_FROZEN_PATH_DRIFT:" + ",".join(sorted(frozen_mismatches)))
    sequences: dict[str, list[str]] = {}
    for key, prefix in FREEZE_SEQUENCE_KEYS.items():
        sequence = require_string_list(freeze.get(key), f"V49_{key.upper()}_INVALID")
        expected_sequence = sorted(path for path in frozen_hashes if path.startswith(prefix))
        if sequence != expected_sequence:
            raise SystemExit(f"V49_{key.upper()}_DRIFT")
        sequences[key] = sequence
    roles = sequences["roleSequence"]
    if not roles or roles[0] != CLUSTER_ROLE_PRECONDITION:
        raise SystemExit("V49_CLUSTER_ROLE_PRECONDITION_MISSING")
    replay_prefix = (
        sequences["migrationSequence"]
        + sequences["functionSequence"]
        + sequences["viewSequence"]
        + roles[1:]
    )
    if v49_base.get("frozenFileCount") != len(frozen_hashes):
        raise SystemExit("V49_BASE_FROZEN_FILE_COUNT_MISMATCH")
    if v49_base.get("clusterRolePrecondition") != CLUSTER_ROLE_PRECONDITION:
        raise SystemExit("V49_BASE_CLUSTER_ROLE_PRECONDITION_MISMATCH")
    if v49_base.get("replayPrefixFileCount") != len(replay_prefix):
        raise SystemExit("V49_BASE_REPLAY_PREFIX_COUNT_MISMATCH")
    if v49_base.get("replayPrefixOrderSha256") != canonical_sha256(replay_prefix):
        raise SystemExit("V49_BASE_REPLAY_PREFIX_ORDER_MISMATCH")
    if v49_base.get("frozenFileMutationCount") != 0:
        raise SystemExit("V49_BASE_FROZEN_MUTATION_COUNT_MISMATCH")
    if v49_base.get("replayBoundary") != REPLAY_BOUNDARY:
        raise SystemExit("V49_BASE_REPLAY_BOUNDARY_MISMATCH")
    return freeze, replay_prefix


def verify_execution_receipt(
    payload: dict[str, object], *, require_complete: bool
) -> dict[str, object]:
    descriptor = payload.get("executionReceipt")
    if not isinstance(descriptor, dict) or descriptor.get("path") != EXECUTION_RECEIPT:
        raise SystemExit("V50_EXECUTION_RECEIPT_DESCRIPTOR_INVALID")
    expected_hash = descriptor.get("sha256")
    if not is_sha256(expected_hash):
        raise SystemExit("V50_EXECUTION_RECEIPT_HASH_INVALID")
    receipt_path = ROOT / EXECUTION_RECEIPT
    if not receipt_path.is_file() or sha256(receipt_path) != expected_hash:
        raise SystemExit("V50_EXECUTION_RECEIPT_DRIFT")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema") != "gda-v50.round16b-replay-receipt/v1":
        raise SystemExit("V50_EXECUTION_RECEIPT_SCHEMA_INVALID")
    if receipt.get("databaseVersion") != 50 or receipt.get("checkpoint") != 11:
        raise SystemExit("V50_EXECUTION_RECEIPT_VERSION_INVALID")
    status = receipt.get("status")
    if status == "PENDING" and not require_complete:
        return receipt
    if status != "PASS":
        raise SystemExit("V50_EXECUTION_RECEIPT_STATUS_INVALID")
    postgres_version = receipt.get("postgresqlVersion")
    if not isinstance(postgres_version, str) or not postgres_version.startswith("16."):
        raise SystemExit("V50_EXECUTION_RECEIPT_POSTGRES_VERSION_INVALID")
    replays = receipt.get("freshReplays")
    if not isinstance(replays, list) or len(replays) != 2:
        raise SystemExit("V50_EXECUTION_RECEIPT_REPLAY_COUNT_INVALID")
    database_names: set[str] = set()
    normalized_hashes: set[str] = set()
    server_versions: set[str] = set()
    dump_paths: set[str] = set()
    governed_ids: list[str] = []
    ledger_rows = command_ledger_rows()
    for replay in replays:
        if not isinstance(replay, dict):
            raise SystemExit("V50_EXECUTION_RECEIPT_REPLAY_INVALID")
        database = replay.get("database")
        normalized_hash = replay.get("normalizedSchemaSha256")
        if (
            not isinstance(database, str)
            or not database.startswith("gda_v50_round16b_")
            or database in database_names
            or replay.get("replayStatus") != "PASS"
            or replay.get("schemaCount") != 11
            or replay.get("testStatus") != "PASS"
            or replay.get("fixtureResidue") != 0
            or not is_sha256(normalized_hash)
        ):
            raise SystemExit("V50_EXECUTION_RECEIPT_REPLAY_INVALID")
        database_names.add(database)
        normalized_hashes.add(normalized_hash)
        command_ids = replay.get("commandIds")
        if not isinstance(command_ids, dict) or set(command_ids) != {
            "replay", "test", "dump", "schemaHash"
        } or any(not isinstance(value, str) or not value for value in command_ids.values()):
            raise SystemExit("V50_EXECUTION_RECEIPT_REPLAY_COMMANDS_INVALID")
        governed_ids.extend(command_ids[key] for key in (
            "replay", "test", "dump", "schemaHash"
        ))
        replay_meta, replay_stdout = verified_command(command_ids["replay"], ledger_rows)
        test_meta, test_stdout = verified_command(command_ids["test"], ledger_rows)
        dump_meta, _ = verified_command(command_ids["dump"], ledger_rows)
        hash_meta, hash_stdout = verified_command(command_ids["schemaHash"], ledger_rows)
        replay_argv = replay_meta["argv"]
        test_argv = test_meta["argv"]
        dump_argv = dump_meta["argv"]
        hash_argv = hash_meta["argv"]
        if (
            "database/scripts/replay_v50_round16b.sh" not in replay_argv
            or "database/scripts/run_v50_round16b_tests.sh" not in test_argv
            or not any(Path(value).name == "pg_dump" for value in dump_argv)
            or "--schema-only" not in dump_argv
            or database not in dump_argv
            or "database/scripts/schema_hash.py" not in hash_argv
        ):
            raise SystemExit(f"V50_EXECUTION_COMMAND_CLASS_INVALID:{database}")
        dump_outputs: list[str] = []
        for index, value in enumerate(dump_argv):
            if value == "-f" and index + 1 < len(dump_argv):
                dump_outputs.append(dump_argv[index + 1])
            elif value.startswith("--file="):
                dump_outputs.append(value.split("=", 1)[1])
        expected_dump = f"/private/tmp/{database}_schema.sql"
        hash_inputs = [value for value in hash_argv if value.endswith("_schema.sql")]
        if dump_outputs != [expected_dump] or hash_inputs != [expected_dump]:
            raise SystemExit(f"V50_DUMP_HASH_PATH_BINDING_INVALID:{database}")
        dump_paths.add(expected_dump)
        replay_match = re.search(
            rf"^V50_ROUND16B_REPLAY_OK database={re.escape(database)} "
            r"schemas=11 postgresql=(16\.[0-9.]+)(?: \([^\r\n()]+\))?$",
            replay_stdout,
            re.MULTILINE,
        )
        if replay_match is None:
            raise SystemExit(f"V50_REPLAY_COMMAND_MARKER_INVALID:{database}")
        server_versions.add(replay_match.group(1))
        required_test_markers = (
            "V50_EXPLORATION_V3_HIGHER_ORDER_ASSOCIATION_TESTS=PASS",
            "V50_ROUND16B_CONTRACT_TESTS=PASS SEAL_RACE_MATRIX=PASS "
            "ISOLATION_GUARDS=PASS FIXTURE_RESIDUE=0",
        )
        if any(marker not in test_stdout for marker in required_test_markers):
            raise SystemExit(f"V50_TEST_COMMAND_MARKER_INVALID:{database}")
        if hash_stdout.strip() != normalized_hash:
            raise SystemExit(f"V50_SCHEMA_HASH_COMMAND_OUTPUT_MISMATCH:{database}")
        verify_race_evidence(replay, test_stdout, test_meta)
    if len(normalized_hashes) != 1 or receipt.get("normalizedSchemasIdentical") is not True:
        raise SystemExit("V50_EXECUTION_RECEIPT_NORMALIZATION_MISMATCH")
    if database_names != EXPECTED_REPLAY_DATABASES:
        raise SystemExit("V50_EXECUTION_RECEIPT_DATABASE_IDENTITY_MISMATCH")
    if len(dump_paths) != 2:
        raise SystemExit("V50_EXECUTION_RECEIPT_DUMP_PATH_COLLISION")
    if receipt.get("normalizedSchemaSha256") != next(iter(normalized_hashes)):
        raise SystemExit("V50_EXECUTION_RECEIPT_HEADLINE_HASH_MISMATCH")
    if len(server_versions) != 1 or receipt.get("postgresqlVersion") != next(iter(server_versions)):
        raise SystemExit("V50_EXECUTION_RECEIPT_POSTGRES_VERSION_EVIDENCE_MISMATCH")
    command_ids = receipt.get("governedCommandIds")
    if (
        not isinstance(command_ids, list)
        or command_ids != governed_ids
        or any(not isinstance(value, str) or not value for value in command_ids)
        or len(command_ids) != len(set(command_ids))
    ):
        raise SystemExit("V50_EXECUTION_RECEIPT_COMMAND_IDS_INVALID")
    return receipt


def verify_manifest(
    *, require_execution: bool = True
) -> tuple[dict[str, object], dict[str, object], list[str], dict[str, int], dict[str, object]]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if payload.get("schema") != EXPECTED_SCHEMA or payload.get("phase") != EXPECTED_PHASE:
        raise SystemExit("V50_MANIFEST_IDENTITY_MISMATCH")
    if payload.get("databaseVersion") != 50 or (ROOT / "database/VERSION").read_text().strip() != "50":
        raise SystemExit("V50_DATABASE_VERSION_MISMATCH")
    if payload.get("additiveReplayOrder") != REQUIRED_REPLAY:
        raise SystemExit("V50_ADDITIVE_REPLAY_ORDER_MISMATCH")
    if payload.get("verificationOrder") != REQUIRED_VERIFICATION:
        raise SystemExit("V50_VERIFICATION_ORDER_MISMATCH")
    if payload.get("managedFilesDigestAlgorithm") != "sha256 per file; manifest excludes itself":
        raise SystemExit("V50_MANAGED_DIGEST_ALGORITHM_MISMATCH")
    if any(payload.get(flag) is not False for flag in (
        "productionDataImported", "productionActivationPerformed", "deploymentPerformed"
    )):
        raise SystemExit("V50_RESEARCH_ONLY_BOUNDARY_MISMATCH")
    freeze, replay_prefix = verify_freeze(payload)
    per_file = payload.get("perFileSha256")
    if not isinstance(per_file, dict) or set(per_file) != MANAGED_FILES:
        raise SystemExit("V50_MANAGED_FILE_SET_MISMATCH")
    mismatches: list[str] = []
    for relative, expected in per_file.items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != expected:
            mismatches.append(relative)
    if mismatches:
        raise SystemExit("V50_MANAGED_FILE_DRIFT:" + ",".join(sorted(mismatches)))
    inventory = payload["objectInventory"]
    actual = {
        "newSchemaCount": count_prefix(ROOT / REQUIRED_REPLAY[0], "CREATE SCHEMA "),
        "newEnumTypeCount": count_prefix(ROOT / REQUIRED_REPLAY[0], "CREATE TYPE "),
        "newTableCount": count_prefix(ROOT / REQUIRED_REPLAY[0], "CREATE TABLE "),
        "newIntegrityFunctionCount": count_prefix(ROOT / REQUIRED_REPLAY[1], "CREATE FUNCTION "),
        "newConstraintTriggerCount": count_prefix(ROOT / REQUIRED_REPLAY[1], "CREATE CONSTRAINT TRIGGER "),
        "newRegularTriggerCount": count_prefix(ROOT / REQUIRED_REPLAY[1], "CREATE TRIGGER "),
        "newViewCount": count_prefix(ROOT / REQUIRED_REPLAY[2], "CREATE VIEW "),
    }
    for key, value in actual.items():
        if inventory.get(key) != value:
            raise SystemExit(f"V50_OBJECT_INVENTORY_MISMATCH:{key}:{inventory.get(key)}:{value}")
    function_text = (ROOT / REQUIRED_REPLAY[1]).read_text(encoding="utf-8")
    migration_text = (ROOT / REQUIRED_REPLAY[0]).read_text(encoding="utf-8")
    if "pair_projection_policy = 'NONE'" not in function_text:
        # Static migration constraints use the same policy literal and the
        # independent test proves the dynamic realization boundary.
        if "pair_projection_policy = 'NONE'" not in migration_text:
            raise SystemExit("HIGHER_ORDER_NONE_POLICY_MISSING")
    if "IMPLICIT_HYPEREDGE" in function_text or "INSERT INTO exploration_v3.association" in function_text:
        raise SystemExit("IMPLICIT_PAIR_GENERATOR_DETECTED")
    additive_text = "\n".join(
        (ROOT / relative).read_text(encoding="utf-8") for relative in REQUIRED_REPLAY
    )
    derived_zeroes = {
        "implicitHyperedgePairProjectionFunctionCount": 0,
        "v49ObjectReplacementCount": sum(
            additive_text.count(token) for token in ("CREATE OR REPLACE ", "DROP ")
        ),
    }
    for key, value in derived_zeroes.items():
        if inventory.get(key) != value:
            raise SystemExit(f"V50_OBJECT_INVENTORY_MISMATCH:{key}:{inventory.get(key)}:{value}")
    receipt = verify_execution_receipt(payload, require_complete=require_execution)
    return payload, freeze, replay_prefix, actual, receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    emit = parser.add_mutually_exclusive_group()
    emit.add_argument("--emit-v49-replay-prefix", action="store_true")
    emit.add_argument("--emit-additive-replay", action="store_true")
    emit.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    require_execution = not (
        args.emit_v49_replay_prefix or args.emit_additive_replay or args.preflight
    )
    payload, freeze, replay_prefix, actual, receipt = verify_manifest(
        require_execution=require_execution
    )
    if args.emit_v49_replay_prefix:
        print("\n".join(replay_prefix))
        return 0
    if args.emit_additive_replay:
        print("\n".join(REQUIRED_REPLAY))
        return 0
    if args.preflight:
        print(
            "V50_ROUND16B_PREFLIGHT=PASS "
            f"receipt_status={receipt['status']} files={len(payload['perFileSha256'])}"
        )
        return 0
    print(
        "V50_ROUND16B_MANIFEST=PASS "
        f"files={len(payload['perFileSha256'])} frozen_files={freeze['fileCount']} "
        f"prefix_files={len(replay_prefix)} tables={actual['newTableCount']} "
        f"functions={actual['newIntegrityFunctionCount']} views={actual['newViewCount']} "
        f"receipt_status={receipt['status']} normalized_schema={receipt['normalizedSchemaSha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
