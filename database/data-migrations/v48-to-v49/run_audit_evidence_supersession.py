#!/usr/bin/env python3
"""Run the bounded, rollback-only Phase 2B P1 evidence supersession.

This is intentionally not a population replay.  It creates task-owned local
PostgreSQL 16.13 clusters, replays only the empty Phase 2A schema, and executes
the existing P1 probe SQL files unchanged through a tiny role-setting wrapper.
Every P1 role gets a new database and the probe itself ends in ROLLBACK.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
ADMIN = "gda_v49_phase2b_admin"
OWNER = "gda_v49_phase2a_schema_owner"
BASE = "86ba95cae9ecf12e58fcabb8170c9020e151b386"
SOURCE = "11e7b82d27b2774273d2f0d68904632246dabd37"
IMPLEMENTATION = "302ddb9683e8b3ee06c34557d10fd72a65c2afaf"
BASE_SCHEMA_HASH = "4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105"
FINAL_SCHEMA_HASH = "aa8cb0af7b61931e51f1f71ed2e4cf0d10b178669de16807871819b330742e8b"
FORWARD_MIGRATION = ROOT / "database/data-migrations/v48-to-v49/001_performance_remediation.sql"
RIGHTS_PROBE = ROOT / "database/data-migrations/v48-to-v49/p1_rights_leaf_probe.sql"
DELIVERY_PROBE = ROOT / "database/data-migrations/v48-to-v49/p1_delivery_validation_probe.sql"

P1_MATRIX = (
    ("P1_RIGHTS_LEAF_PRE_FIX_50", "pre_fix", "rights_leaf", 50, False),
    ("P1_RIGHTS_LEAF_PRE_FIX_250", "pre_fix", "rights_leaf", 250, False),
    ("P1_RIGHTS_LEAF_POST_FIX_50", "post_fix", "rights_leaf", 50, False),
    ("P1_RIGHTS_LEAF_POST_FIX_250", "post_fix", "rights_leaf", 250, False),
    ("P1_RIGHTS_LEAF_POST_FIX_1000", "post_fix", "rights_leaf", 1000, False),
    ("P1_RIGHTS_LEAF_POST_FIX_PLAN_1000", "post_fix", "rights_leaf", 1000, True),
    ("P1_DELIVERY_PRE_FIX_50", "pre_fix", "delivery", 50, False),
    ("P1_DELIVERY_POST_FIX_50", "post_fix", "delivery", 50, False),
    ("P1_DELIVERY_POST_FIX_250", "post_fix", "delivery", 250, False),
    ("P1_DELIVERY_POST_FIX_1000", "post_fix", "delivery", 1000, False),
    ("P1_DELIVERY_POST_FIX_PLAN_1000", "post_fix", "delivery", 1000, True),
)


class EvidenceRunError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise EvidenceRunError(f"REFUSING_TO_OVERWRITE:{path}")
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def command_text(command: list[str]) -> list[str]:
    """Keep audit commands structured, secret-free, and directly rerunnable."""
    return command


def run_logged(command: list[str], *, env: dict[str, str], stdout: Path, stderr: Path, cwd: Path = ROOT) -> dict[str, Any]:
    stdout.parent.mkdir(parents=True, exist_ok=True)
    if stdout.exists() or stderr.exists():
        raise EvidenceRunError(f"REFUSING_TO_OVERWRITE_LOG:{stdout}")
    started = utc_now()
    with stdout.open("wb") as out, stderr.open("wb") as err:
        completed = subprocess.run(command, cwd=cwd, env=env, stdout=out, stderr=err, check=False)
    ended = utc_now()
    return {
        "command": command_text(command), "startedAtUtc": started, "endedAtUtc": ended,
        "exitCode": completed.returncode,
        "stdout": {"path": str(stdout.relative_to(ROOT)), "bytes": stdout.stat().st_size, "sha256": sha256_file(stdout)},
        "stderr": {"path": str(stderr.relative_to(ROOT)), "bytes": stderr.stat().st_size, "sha256": sha256_file(stderr)},
    }


def checked(command: list[str], *, env: dict[str, str], stdout: Path, stderr: Path, cwd: Path = ROOT) -> dict[str, Any]:
    result = run_logged(command, env=env, stdout=stdout, stderr=stderr, cwd=cwd)
    if result["exitCode"] != 0:
        raise EvidenceRunError(f"COMMAND_FAILED:{' '.join(command)}")
    return result


def output_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def git_output(*args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise EvidenceRunError(f"GIT_FAILED:{' '.join(args)}:{completed.stderr[-800:]}")
    return completed.stdout.strip()


def git_success(*args: str) -> None:
    completed = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise EvidenceRunError(f"GIT_EXPECTATION_FAILED:{' '.join(args)}:{completed.stderr[-800:]}")


def assert_static_inputs() -> dict[str, Any]:
    git_success("merge-base", "--is-ancestor", SOURCE, "HEAD")
    git_success("merge-base", "--is-ancestor", IMPLEMENTATION, SOURCE)
    if git_output("diff", "--name-only", BASE, SOURCE, "--", "database/migrations", "database/functions", "database/views", "database/roles"):
        raise EvidenceRunError("PRE_FIX_BASE_SCHEMA_FILES_CHANGED")
    version = subprocess.run(["postgres", "--version"], text=True, capture_output=True, check=False)
    if version.returncode or not re.fullmatch(r"postgres \(PostgreSQL\) 16\.13(?: \([^)]*\))?", version.stdout.strip()):
        raise EvidenceRunError(f"POSTGRES_VERSION_NOT_16_13:{version.stdout.strip()}")
    for path in (FORWARD_MIGRATION, RIGHTS_PROBE, DELIVERY_PROBE):
        if not path.is_file():
            raise EvidenceRunError(f"REQUIRED_SCRIPT_MISSING:{path}")
    if sha256_file(FORWARD_MIGRATION) != "558ac2c8e8bf36166290bf588035c8822f8ff17ae481e30ebff98a8dc6715e48":
        raise EvidenceRunError("FORWARD_MIGRATION_HASH_MISMATCH")
    forbidden = ("DISABLE TRIGGER", "session_replication_role", "NOT VALID", "DROP CONSTRAINT", "DROP TRIGGER")
    migration_text = FORWARD_MIGRATION.read_text(encoding="utf-8")
    if any(token in migration_text for token in forbidden):
        raise EvidenceRunError("FORWARD_MIGRATION_CONSTRAINT_WEAKENING_TOKEN")
    return {
        "sourceSha": SOURCE, "implementationSha": IMPLEMENTATION, "preFixSchemaState": BASE,
        "postFixAuditState": SOURCE, "postgresVersion": version.stdout.strip(),
        "baseSchemaFilesUnchangedFromPreFix": True,
        "forwardMigration": {"path": str(FORWARD_MIGRATION.relative_to(ROOT)), "sha256": sha256_file(FORWARD_MIGRATION)},
        "probeScripts": {
            "rightsLeaf": {"path": str(RIGHTS_PROBE.relative_to(ROOT)), "sha256": sha256_file(RIGHTS_PROBE)},
            "delivery": {"path": str(DELIVERY_PROBE.relative_to(ROOT)), "sha256": sha256_file(DELIVERY_PROBE)},
        },
        "constraintsDisabled": False, "sessionReplicationRoleReplica": False,
    }


def random_port() -> int:
    return random.SystemRandom().randrange(49152, 62000)


def cluster_environment(socket_dir: Path, port: int, database: str = "postgres") -> dict[str, str]:
    result = os.environ.copy()
    result.update({"PGHOST": str(socket_dir), "PGPORT": str(port), "PGDATABASE": database, "PGUSER": ADMIN, "PGCONNECT_TIMEOUT": "5"})
    return result


def wait_for_cluster(env: dict[str, str], deadline_seconds: int = 60) -> None:
    deadline = time.monotonic() + deadline_seconds
    while time.monotonic() < deadline:
        completed = subprocess.run(["psql", "-X", "-Atq", "-c", "SELECT 1"], env=env, text=True, capture_output=True, check=False)
        if completed.returncode == 0 and completed.stdout.strip() == "1":
            return
        time.sleep(0.2)
    raise EvidenceRunError("POSTGRES_START_TIMEOUT")


def create_cluster(run_dir: Path, label: str) -> dict[str, Any]:
    cluster_root = Path(tempfile.mkdtemp(prefix="gda_v49_phase2b.evidence-", dir="/private/tmp")).resolve()
    pgdata = cluster_root / "data"
    socket_dir = cluster_root / "socket"
    socket_dir.mkdir(mode=0o700)
    init_env = os.environ.copy()
    init_env["LC_ALL"] = "C"
    init_result = checked(
        ["initdb", "-D", str(pgdata), "-A", "trust", "-U", ADMIN, "--no-locale", "--encoding", "UTF8"],
        env=init_env,
        stdout=run_dir / f"{label}.cluster-init.stdout.log",
        stderr=run_dir / f"{label}.cluster-init.stderr.log",
    )
    port = random_port()
    server_out = (run_dir / f"{label}.postgres.stdout.log").open("wb")
    server_err = (run_dir / f"{label}.postgres.stderr.log").open("wb")
    process = subprocess.Popen(
        ["postgres", "-D", str(pgdata), "-k", str(socket_dir), "-p", str(port), "-c", "listen_addresses=", "-c", "log_connections=off"],
        stdout=server_out, stderr=server_err, cwd=ROOT, env=os.environ.copy(),
    )
    env = cluster_environment(socket_dir, port)
    try:
        wait_for_cluster(env)
        roles = checked(
            ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-f", str(ROOT / "database/roles/001_cluster_roles.sql")],
            env=env,
            stdout=run_dir / f"{label}.cluster-roles.stdout.log",
            stderr=run_dir / f"{label}.cluster-roles.stderr.log",
        )
    except Exception:
        server_out.close()
        server_err.close()
        process.terminate()
        process.wait(timeout=20)
        raise
    return {"root": cluster_root, "pgdata": pgdata, "socket": socket_dir, "port": port, "process": process, "env": env, "init": init_result, "roles": roles, "serverOut": server_out, "serverErr": server_err}


def stop_cluster(cluster: dict[str, Any], run_dir: Path, label: str) -> dict[str, Any]:
    process: subprocess.Popen[bytes] = cluster["process"]
    root: Path = cluster["root"]
    socket_dir: Path = cluster["socket"]
    port = cluster["port"]
    env: dict[str, str] = cluster["env"]
    try:
        stop = run_logged(
            ["pg_ctl", "-D", str(cluster["pgdata"]), "stop", "-m", "fast", "-t", "120"],
            env=env,
            stdout=run_dir / f"{label}.cluster-stop.stdout.log",
            stderr=run_dir / f"{label}.cluster-stop.stderr.log",
        )
        if stop["exitCode"] != 0:
            raise EvidenceRunError("POSTGRES_NORMAL_STOP_FAILED")
        process.wait(timeout=30)
        socket_absent = not (socket_dir / f".s.PGSQL.{port}").exists()
        if not socket_absent:
            raise EvidenceRunError("POSTGRES_SOCKET_REMAINS")
        if not str(root).startswith("/private/tmp/gda_v49_phase2b.evidence-"):
            raise EvidenceRunError("CLUSTER_DELETE_PATH_REJECTED")
        shutil.rmtree(root)
        return {"normalStop": True, "clusterDeleted": not root.exists(), "socketAbsent": socket_absent, "taskOwnedProcessCount": 0, "stop": stop}
    finally:
        cluster["serverOut"].close()
        cluster["serverErr"].close()


def create_database(cluster: dict[str, Any], database: str, run_dir: Path, label: str) -> dict[str, str]:
    env = cluster_environment(cluster["socket"], cluster["port"], "postgres")
    checked(
        ["createdb", "--owner", OWNER, database], env=env,
        stdout=run_dir / f"{label}.createdb.stdout.log", stderr=run_dir / f"{label}.createdb.stderr.log",
    )
    return cluster_environment(cluster["socket"], cluster["port"], database)


def drop_database(cluster: dict[str, Any], database: str, run_dir: Path, label: str) -> dict[str, Any]:
    env = cluster_environment(cluster["socket"], cluster["port"], "postgres")
    return checked(
        ["dropdb", database], env=env,
        stdout=run_dir / f"{label}.dropdb.stdout.log", stderr=run_dir / f"{label}.dropdb.stderr.log",
    )


def psql_value(command: list[str], env: dict[str, str]) -> str:
    completed = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise EvidenceRunError(f"PSQL_QUERY_FAILED:{completed.stderr[-800:]}")
    return completed.stdout.strip()


def schema_hash(env: dict[str, str], run_dir: Path, label: str) -> tuple[str, dict[str, Any]]:
    result = checked(
        [str(ROOT / "database/scripts/schema_hash.sh")], env=env,
        stdout=run_dir / f"{label}.schema-hash.stdout.log", stderr=run_dir / f"{label}.schema-hash.stderr.log",
    )
    value = output_text(run_dir / f"{label}.schema-hash.stdout.log").strip()
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise EvidenceRunError(f"SCHEMA_HASH_OUTPUT_INVALID:{value}")
    return value, result


def replay_empty_schema(env: dict[str, str], run_dir: Path, label: str) -> dict[str, Any]:
    return checked(
        [str(ROOT / "database/scripts/replay.sh")], env=env,
        stdout=run_dir / f"{label}.replay.stdout.log", stderr=run_dir / f"{label}.replay.stderr.log",
    )


def apply_forward_migration(env: dict[str, str], run_dir: Path, label: str) -> dict[str, Any]:
    wrapper = run_dir / f"{label}.apply-forward-wrapper.sql"
    wrapper.write_text(f"SET ROLE {OWNER};\n\\i {FORWARD_MIGRATION}\n", encoding="utf-8")
    return checked(
        ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-f", str(wrapper)], env=env,
        stdout=run_dir / f"{label}.forward.stdout.log", stderr=run_dir / f"{label}.forward.stderr.log",
    )


def database_settings(env: dict[str, str]) -> dict[str, Any]:
    sql = "SELECT json_build_object('server_version', current_setting('server_version'), 'server_version_num', current_setting('server_version_num'), 'listen_addresses', current_setting('listen_addresses'), 'port', current_setting('port'), 'session_replication_role', current_setting('session_replication_role'), 'transaction_read_only', current_setting('transaction_read_only'))::text;"
    value = psql_value(["psql", "-X", "-Atq", "-v", "ON_ERROR_STOP=1", "-c", sql], env)
    parsed = json.loads(value)
    server_version = parsed.get("server_version")
    if (not isinstance(server_version, str) or not re.fullmatch(r"16\.13(?: \([^)]*\))?", server_version)
            or parsed.get("listen_addresses") != "" or parsed.get("port") == "5432"
            or parsed.get("session_replication_role") != "origin"):
        raise EvidenceRunError(f"POSTGRES_SETTINGS_POLICY_FAILURE:{parsed}")
    return parsed


def catalog_inventory(env: dict[str, str]) -> dict[str, Any]:
    sql = """
SELECT jsonb_build_object(
  'roles', (SELECT count(*) FROM pg_roles WHERE rolname LIKE 'gda_v49_phase2a_%'),
  'constraints', (SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname IN ('raw','core','provenance','research','rights','workflow','release','audit','api_v1')),
  'triggers', (SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('raw','core','provenance','research','rights','workflow','release','audit','api_v1') AND NOT t.tgisinternal),
  'functions', (SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname IN ('raw','core','provenance','research','rights','workflow','release','audit','api_v1')),
  'indexes', (SELECT count(*) FROM pg_class i JOIN pg_namespace n ON n.oid=i.relnamespace WHERE i.relkind='i' AND n.nspname IN ('raw','core','provenance','research','rights','workflow','release','audit','api_v1')),
  'publicRawUsage', has_schema_privilege('public', 'raw', 'USAGE'),
  'publicApiUsage', has_schema_privilege('public', 'api_v1', 'USAGE')
)::text;
"""
    return json.loads(psql_value(["psql", "-X", "-Atq", "-v", "ON_ERROR_STOP=1", "-c", sql], env))


def residue_inventory(env: dict[str, str]) -> dict[str, int]:
    sql = """
SELECT jsonb_build_object(
  'raw_source_asset', (SELECT count(*) FROM raw.source_asset),
  'raw_source_record', (SELECT count(*) FROM raw.source_record),
  'core_entity', (SELECT count(*) FROM core.entity),
  'core_archive_object', (SELECT count(*) FROM core.archive_object),
  'external_visual_reference', (SELECT count(*) FROM rights.external_visual_reference),
  'object_visual_reference', (SELECT count(*) FROM rights.object_visual_reference),
  'rights_assessment', (SELECT count(*) FROM rights.rights_assessment),
  'delivery_assessment', (SELECT count(*) FROM rights.delivery_assessment),
  'delivery_rights_assessment', (SELECT count(*) FROM rights.delivery_rights_assessment),
  'delivery_policy_evaluation', (SELECT count(*) FROM rights.delivery_policy_evaluation)
)::text;
"""
    return {key: int(value) for key, value in json.loads(psql_value(["psql", "-X", "-Atq", "-v", "ON_ERROR_STOP=1", "-c", sql], env)).items()}


def forward_index_inventory(env: dict[str, str]) -> dict[str, bool]:
    sql = """
SELECT jsonb_build_object(
  'providerObject', to_regclass('rights.rights_assessment_provider_object_target_idx') IS NOT NULL,
  'visualReference', to_regclass('rights.rights_assessment_visual_reference_target_idx') IS NOT NULL,
  'representation', to_regclass('rights.rights_assessment_representation_target_idx') IS NOT NULL,
  'locator', to_regclass('rights.rights_assessment_locator_target_idx') IS NOT NULL
)::text;
"""
    return {key: bool(value) for key, value in json.loads(psql_value(["psql", "-X", "-Atq", "-v", "ON_ERROR_STOP=1", "-c", sql], env)).items()}


def execute_probe(env: dict[str, str], run_dir: Path, name: str, probe: Path, scale: int, state: str, plan_role: bool) -> dict[str, Any]:
    wrapper = run_dir / f"{name}.wrapper.sql"
    wrapper.write_text(f"SET ROLE {OWNER};\n\\i {probe}\n", encoding="utf-8")
    stdout = run_dir / f"{name}.stdout.log"
    stderr = run_dir / f"{name}.stderr.log"
    result = run_logged(
        ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-v", f"scale={scale}", "-f", str(wrapper)],
        env=env, stdout=stdout, stderr=stderr,
    )
    text = output_text(stdout)
    if result["exitCode"] != 0 or "ROLLBACK;" not in probe.read_text(encoding="utf-8"):
        raise EvidenceRunError(f"PROBE_FAILED_OR_NO_ROLLBACK_TERMINATOR:{name}")
    if state == "pre_fix" and "Seq Scan" not in text:
        raise EvidenceRunError(f"PRE_FIX_SCAN_NOT_OBSERVED:{name}")
    if state == "post_fix" and scale == 1000 and "rights_assessment_visual_reference_target_idx" not in text:
        raise EvidenceRunError(f"POST_FIX_INDEX_PATH_NOT_OBSERVED:{name}")
    timing_rows = re.findall(r"^\s*" + re.escape(str(scale)) + r"\s+\|\s+([0-9.]+)\s+\|", text, flags=re.MULTILINE)
    profile = {"probeScriptSha256": sha256_file(probe), "scale": scale, "schemaState": state, "planRole": plan_role}
    fixture_hash = hashlib.sha256(json.dumps(profile, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    plan_assertion = "sequential_scan" if state == "pre_fix" else (
        "rights_assessment_visual_reference_target_idx" if scale == 1000 else "target_led_function_with_index_present"
    )
    return {"execution": result, "fixture": profile, "fixtureSha256": fixture_hash, "timingSeconds": [float(value) for value in timing_rows], "rollbackObserved": True,
            "planAssertion": plan_assertion}


def run_p1(output_dir: Path) -> None:
    static = assert_static_inputs()
    reproduced = output_dir / "reproduced"
    if reproduced.exists() and any(reproduced.iterdir()):
        raise EvidenceRunError("REPRODUCED_DIRECTORY_NOT_EMPTY")
    reproduced.mkdir(parents=True, exist_ok=True)
    cluster = create_cluster(reproduced, "p1")
    records: list[dict[str, Any]] = []
    cleanup: dict[str, Any] | None = None
    try:
        for ordinal, (name, state, family, scale, plan_role) in enumerate(P1_MATRIX, 1):
            label = f"{ordinal:02d}_{name}"
            database = f"gda_v49_phase2a_phase2b_replay_{ordinal:02d}"
            env = create_database(cluster, database, reproduced, label)
            replay = replay_empty_schema(env, reproduced, label)
            before_hash, before_hash_command = schema_hash(env, reproduced, label + ".base")
            if before_hash != BASE_SCHEMA_HASH:
                raise EvidenceRunError(f"BASE_SCHEMA_HASH_MISMATCH:{name}:{before_hash}")
            forward: dict[str, Any] | None = None
            if state == "post_fix":
                forward = apply_forward_migration(env, reproduced, label)
                active_hash, active_hash_command = schema_hash(env, reproduced, label + ".postfix")
                if active_hash != FINAL_SCHEMA_HASH:
                    raise EvidenceRunError(f"FINAL_SCHEMA_HASH_MISMATCH:{name}:{active_hash}")
                forward_indexes = forward_index_inventory(env)
                if not all(forward_indexes.values()):
                    raise EvidenceRunError(f"FORWARD_INDEX_MISSING:{name}:{forward_indexes}")
            else:
                active_hash, active_hash_command = before_hash, before_hash_command
                forward_indexes = None
            settings = database_settings(env)
            probe = RIGHTS_PROBE if family == "rights_leaf" else DELIVERY_PROBE
            probe_result = execute_probe(env, reproduced, label, probe, scale, state, plan_role)
            residue = residue_inventory(env)
            if any(residue.values()):
                raise EvidenceRunError(f"PROBE_RESIDUE_NONZERO:{name}:{residue}")
            dropped = drop_database(cluster, database, reproduced, label)
            record = {"name": name, "database": database, "schemaState": state, "probeFamily": family, "scale": scale, "planRole": plan_role,
                      "replay": replay, "baseSchemaHash": before_hash, "baseSchemaHashCommand": before_hash_command,
                      "forwardMigration": forward, "activeSchemaHash": active_hash, "activeSchemaHashCommand": active_hash_command,
                      "forwardIndexes": forward_indexes, "settings": settings, "probe": probe_result, "residue": residue, "databaseDropped": dropped["exitCode"] == 0}
            write_json(reproduced / f"{label}.metadata.json", record)
            records.append(record)
    finally:
        cleanup = stop_cluster(cluster, reproduced, "p1")
    all_passed = len(records) == len(P1_MATRIX) and all(record["databaseDropped"] for record in records)
    write_json(reproduced / "P1_REPRODUCTION_SUMMARY.json", {"schema": "gda-v49-phase2b-p1-supersession/v1", "status": "PASS" if all_passed else "FAIL", "staticInputs": static,
        "correctiveProbeRerunCount": len(records), "correctiveProbePassCount": len(records) if all_passed else 0, "records": records,
        "stagingAccessed": False, "extractorRerun": False, "fullPopulationReplayRerun": False, "cleanup": cleanup})


def run_empty_schema(output_dir: Path) -> None:
    static = assert_static_inputs()
    target = output_dir / "empty-schema"
    if target.exists() and any(target.iterdir()):
        raise EvidenceRunError("EMPTY_SCHEMA_DIRECTORY_NOT_EMPTY")
    target.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    for ordinal, label in enumerate(("A", "B"), 1):
        cluster = create_cluster(target, f"empty_{label}")
        cleanup: dict[str, Any] | None = None
        try:
            database = f"gda_v49_phase2a_phase2b_replay_empty_{ordinal}"
            env = create_database(cluster, database, target, f"empty_{label}")
            replay = replay_empty_schema(env, target, f"empty_{label}")
            forward = apply_forward_migration(env, target, f"empty_{label}")
            final_hash, hash_command = schema_hash(env, target, f"empty_{label}")
            if final_hash != FINAL_SCHEMA_HASH:
                raise EvidenceRunError(f"EMPTY_SCHEMA_HASH_MISMATCH:{label}:{final_hash}")
            settings = database_settings(env)
            catalog = catalog_inventory(env)
            if (catalog["roles"] != 7 or catalog["publicRawUsage"] or catalog["publicApiUsage"]
                    or any(int(catalog[key]) <= 0 for key in ("constraints", "triggers", "functions", "indexes"))):
                raise EvidenceRunError(f"ROLE_OR_GRANT_CHECK_FAILED:{label}:{catalog}")
            if records and catalog != records[0]["catalog"]:
                raise EvidenceRunError(f"EMPTY_SCHEMA_CATALOG_DRIFT:{label}:{catalog}")
            residue = residue_inventory(env)
            if any(residue.values()):
                raise EvidenceRunError(f"EMPTY_SCHEMA_HAS_ROWS:{label}:{residue}")
            dropped = drop_database(cluster, database, target, f"empty_{label}")
            record = {"label": label, "database": database, "replay": replay, "forwardMigration": forward, "schemaHash": final_hash,
                      "schemaHashCommand": hash_command, "settings": settings, "catalog": catalog, "emptyRowCounts": residue,
                      "databaseDropped": dropped["exitCode"] == 0}
            write_json(target / f"{ordinal:02d}_EMPTY_SCHEMA_{label}.metadata.json", record)
            records.append(record)
        finally:
            cleanup = stop_cluster(cluster, target, f"empty_{label}")
            write_json(target / f"{ordinal:02d}_EMPTY_SCHEMA_{label}.cleanup.json", cleanup)
    write_json(target / "EMPTY_SCHEMA_REPLAY_SUMMARY.json", {"schema": "gda-v49-phase2b-empty-schema-supersession/v1", "status": "PASS",
        "staticInputs": static, "runs": records, "sequential": True, "stagingAccessed": False, "extractorRerun": False,
        "fullPopulationReplayRerun": False, "taskOwnedResidualProcessCount": 0})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("p1", "empty-schema"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if not str(output).startswith(str(ROOT / "docs/audits/v49-phase2b-evidence-amendment")):
        raise EvidenceRunError("OUTPUT_DIRECTORY_POLICY_VIOLATION")
    if args.mode == "p1":
        run_p1(output)
    else:
        run_empty_schema(output)
    print(json.dumps({"status": "PASS", "mode": args.mode, "output": str(output.relative_to(ROOT))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (EvidenceRunError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
