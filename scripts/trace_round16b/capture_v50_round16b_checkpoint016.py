#!/usr/bin/env python3
"""Capture the native Checkpoint 016 v50 database reproduction receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


EXPECTED_COMMIT = "d40ec811c2b60cfcbf6892ba79741d2ee0fec95b"
EXPECTED_TREE = "9c08c85efcbc4fd4ce88c3c880c3e3e053f36b65"
EXPECTED_POSTGRESQL_VERSION = "16.13 (Homebrew)"
EXPECTED_NORMALIZED_SCHEMA_SHA256 = (
    "1152a494e6b64595c9f9291c1d314a9434cb763c7f2a02512d2768e286f571b4"
)
EXPECTED_NORMALIZED_SCHEMA_BYTES = 1_090_058
EXPECTED_RAW_SCHEMA_BYTES = 1_355_543
EXPECTED_RACE_CHECKSUMS_SHA256 = (
    "595efb06ae1508b3f2cf952e3d0f1af2e9bd70b12bd4fcde93a530b3b70442ab"
)
EXPECTED_GOVERNED_TABLE_SET_SHA256 = (
    "99a84ebc8bf6416a2c9cf0f35fba3fa76156681c48cb03a5599e41f1799d8cbc"
)
EXPECTED_API_V3_VIEW_SET_SHA256 = (
    "c554e5b84815a12a8e51dd39ee6f5ca077e3f63d1dc26d9f2218c913bbef44cb"
)

ARTIFACT_HASHES = {
    "manifest": (
        "database/schema-manifest-v50-round16b.json",
        "5f11af95c21417846cd6a71b92173c2d265d5389365fcce08d8c1b7d5b456433",
    ),
    "verifier": (
        "database/scripts/verify_v50_round16b_manifest.py",
        "9a7897f21b943377ca868431463a94828be06627a5344f06956e1efa55ee1423",
    ),
    "replay": (
        "database/scripts/replay_v50_round16b.sh",
        "a215bd3a8bf6030a8ab4d77db12bb90a6e6301352f582322917ca637889ef9de",
    ),
    "test": (
        "database/scripts/run_v50_round16b_tests.sh",
        "f73e1645cfbe95bac75cda49ea1ab4bf8b7571f84032309e3895e1f4561458d6",
    ),
    "schemaNormalizer": (
        "database/scripts/schema_hash.py",
        "147da466b77d2237f475e48288f13f09e7068d40c33737b6336b53131cf4abec",
    ),
    "clusterRoles": (
        "database/roles/001_cluster_roles.sql",
        "ffe5136ac890225ddaf6c8cfc370d144684f30378c02276aadefe9804a7d7f0a",
    ),
}

PROJECT_SCHEMAS = (
    "raw",
    "core",
    "provenance",
    "research",
    "rights",
    "workflow",
    "release",
    "audit",
    "api_v1",
    "exploration_v3",
    "api_v3",
)
GOVERNED_TABLE_SCHEMAS = PROJECT_SCHEMAS[:-2] + ("exploration_v3",)
EXPECTED_METRICS = {
    "API_V3_VIEW_COUNT": 24,
    "FIXTURE_RESIDUE": 0,
    "GOVERNED_TABLE_COUNT": 278,
    "NONZERO_API_V3_VIEW_COUNT": 0,
    "NONZERO_GOVERNED_TABLE_COUNT": 0,
    "PROJECT_SCHEMA_COUNT": 11,
    "REVIEWER_QUEUE_COUNT": 0,
    "V3_CONSTRAINT_TRIGGER": 29,
    "V3_ENUM": 21,
    "V3_FUNCTION": 28,
    "V3_INVENTORY_NONZERO_METRIC_COUNT": 0,
    "V3_RAW_NONCONSTRAINT_TRIGGER_CATALOG_COUNT": 57,
    "V3_SEMANTIC_REGULAR_TRIGGER": 1,
    "V3_TABLE": 35,
    "V50_ADDITIVE_VIEW": 26,
}
RACE_FILES = (
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
RACE_ROOT = Path(
    "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/"
    "v50-round16b-seal-race"
)
RACE_DIRECTORY_NAMES = ("gda_v50_round16b_2317", "gda_v50_round16b_2318")
EXPECTED_FULL_VERIFIER_OUTPUT = (
    "V50_ROUND16B_MANIFEST=PASS files=12 frozen_files=126 prefix_files=40 "
    "tables=35 functions=28 views=26 receipt_status=PASS normalized_schema="
    + EXPECTED_NORMALIZED_SCHEMA_SHA256
)
EXPECTED_PREFLIGHT_OUTPUT = "V50_ROUND16B_PREFLIGHT=PASS receipt_status=PASS files=12"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def run(argv: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        argv,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    if result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {argv!r}\n{result.stderr}"
        )
    return result.stdout.strip()


def require_native_python(repo: Path) -> None:
    executable = Path(sys.executable).resolve()
    allowed = (
        Path("/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13"),
        Path(
            "/Applications/Xcode.app/Contents/Developer/Library/Frameworks/"
            "Python3.framework/Versions/3.9/bin/python3.9"
        ),
    )
    if executable not in allowed or repo == executable or repo in executable.parents:
        raise ValueError(f"non-native Python executable: {executable}")


def validate_database_name(value: str) -> str:
    if re.fullmatch(r"gda_v50_round16b_[a-z0-9_]+", value) is None:
        raise ValueError(f"invalid Round 16B database name: {value!r}")
    return value


def sql_literals(values: tuple[str, ...]) -> str:
    return ",".join("'" + value.replace("'", "''") + "'" for value in values)


class DatabaseProbe:
    def __init__(
        self, psql: Path, host: Path, port: int, user: str, database: str
    ) -> None:
        self.base = [
            str(psql),
            "-X",
            "-Atq",
            "-v",
            "ON_ERROR_STOP=1",
            "-h",
            str(host),
            "-p",
            str(port),
            "-U",
            user,
            "-d",
            database,
        ]

    def text(self, sql: str) -> str:
        return run([*self.base, "-c", sql])

    def integer(self, sql: str) -> int:
        value = self.text(sql)
        if re.fullmatch(r"[0-9]+", value) is None:
            raise ValueError(f"expected non-negative integer, got {value!r}")
        return int(value)

    def exact_relation_counts(self, relation_query: str) -> dict[str, int]:
        relations = tuple(line for line in self.text(relation_query).splitlines() if line)
        if len(relations) != len(set(relations)):
            raise ValueError("duplicate governed relation identity")
        return {
            relation: self.integer(f"SELECT count(*) FROM {relation};")
            for relation in relations
        }


def verify_authority(repo: Path) -> dict[str, object]:
    require_native_python(repo)
    commit = run(["git", "rev-parse", "HEAD"], cwd=repo)
    tree = run(["git", "rev-parse", "HEAD^{tree}"], cwd=repo)
    status = run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=repo
    )
    if commit != EXPECTED_COMMIT or tree != EXPECTED_TREE:
        raise ValueError(f"unexpected source authority: {commit}/{tree}")
    if status:
        raise ValueError(f"source repository is not clean: {status}")
    return {
        "sourceCommit": commit,
        "sourceTree": tree,
        "repository": str(repo),
        "repositoryClean": True,
    }


def verify_source_native(repo: Path) -> dict[str, object]:
    observed: dict[str, str] = {}
    for key, (relative, expected) in ARTIFACT_HASHES.items():
        path = repo / relative
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f"source artifact drift: {relative}: {actual}")
        observed[key] = actual

    manifest_path = repo / ARTIFACT_HASHES["manifest"][0]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    managed = manifest.get("perFileSha256")
    verifier_relative, verifier_hash = ARTIFACT_HASHES["verifier"]
    if (
        manifest.get("databaseVersion") != 50
        or not isinstance(managed, dict)
        or managed.get(verifier_relative) != verifier_hash
    ):
        raise ValueError("v50 manifest does not bind the corrected native verifier")

    verifier = repo / verifier_relative
    full = run([sys.executable, "-B", str(verifier)], cwd=repo)
    preflight = run([sys.executable, "-B", str(verifier), "--preflight"], cwd=repo)
    if full != EXPECTED_FULL_VERIFIER_OUTPUT:
        raise ValueError(f"unexpected full v50 verifier output: {full!r}")
    if preflight != EXPECTED_PREFLIGHT_OUTPUT:
        raise ValueError(f"unexpected v50 preflight output: {preflight!r}")
    return {
        "compatibilityAdapterUsed": False,
        "nativeVerifierExecuted": True,
        "fullManifestStatus": "PASS",
        "preflightStatus": "PASS",
        "artifactSha256": observed,
    }


def verify_race_evidence(repo: Path, directory_name: str) -> dict[str, object]:
    relative = RACE_ROOT / directory_name
    directory = repo / relative
    checksum_path = directory / "CHECKSUMS.sha256"
    rows: dict[str, str] = {}
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if (
            len(fields) != 2
            or re.fullmatch(r"[0-9a-f]{64}", fields[0]) is None
            or fields[1] in rows
        ):
            raise ValueError(f"invalid race checksum row: {line!r}")
        rows[fields[1]] = fields[0]
    if set(rows) != set(RACE_FILES):
        raise ValueError(f"race evidence file-set mismatch: {directory_name}")
    actual = {name: sha256(directory / name) for name in RACE_FILES}
    if rows != actual:
        raise ValueError(f"race evidence payload mismatch: {directory_name}")
    checksum_sha = sha256(checksum_path)
    if checksum_sha != EXPECTED_RACE_CHECKSUMS_SHA256:
        raise ValueError(f"race checksum-ledger drift: {directory_name}")
    return {
        "directory": relative.as_posix(),
        "checksumsSha256": checksum_sha,
        "fileCount": len(actual),
        "perFileSha256": actual,
    }


def normalized_capture(capture_dir: Path, database: str) -> dict[str, object]:
    raw = (capture_dir / f"{database}_schema.sql").resolve()
    normalized = (capture_dir / f"{database}_schema.normalized.sql").resolve()
    if raw.parent != capture_dir or normalized.parent != capture_dir:
        raise ValueError("schema capture path escaped the capture directory")
    if not raw.is_file() or not normalized.is_file():
        raise ValueError(f"schema capture missing for {database}")
    normalized_hash = sha256(normalized)
    if (
        raw.stat().st_size != EXPECTED_RAW_SCHEMA_BYTES
        or normalized.stat().st_size != EXPECTED_NORMALIZED_SCHEMA_BYTES
        or normalized_hash != EXPECTED_NORMALIZED_SCHEMA_SHA256
    ):
        raise ValueError(f"schema capture mismatch for {database}")
    return {
        "rawPath": str(raw),
        "rawBytes": raw.stat().st_size,
        "normalizedPath": str(normalized),
        "normalizedBytes": normalized.stat().st_size,
        "normalizedSha256": normalized_hash,
    }


def capture_database(
    probe: DatabaseProbe,
    *,
    database: str,
    capture_dir: Path,
    race: dict[str, object],
) -> dict[str, object]:
    governed_counts = probe.exact_relation_counts(
        "SELECT format('%I.%I',schemaname,tablename) FROM pg_tables "
        f"WHERE schemaname = ANY (ARRAY[{sql_literals(GOVERNED_TABLE_SCHEMAS)}]) "
        'ORDER BY schemaname COLLATE "C",tablename COLLATE "C";'
    )
    api_view_counts = probe.exact_relation_counts(
        "SELECT format('%I.%I',schemaname,viewname) FROM pg_views "
        "WHERE schemaname='api_v3' ORDER BY viewname COLLATE \"C\";"
    )
    exploration_counts = {
        name: count
        for name, count in governed_counts.items()
        if name.startswith("exploration_v3.")
    }
    metrics = {
        "PROJECT_SCHEMA_COUNT": probe.integer(
            "SELECT count(*) FROM pg_namespace WHERE nspname = ANY "
            f"(ARRAY[{sql_literals(PROJECT_SCHEMAS)}]);"
        ),
        "V3_ENUM": probe.integer(
            "SELECT count(*) FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace "
            "WHERE n.nspname='exploration_v3' AND t.typtype='e';"
        ),
        "V3_TABLE": probe.integer(
            "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname='exploration_v3' AND c.relkind='r';"
        ),
        "V3_FUNCTION": probe.integer(
            "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
            "WHERE n.nspname='exploration_v3';"
        ),
        "V3_CONSTRAINT_TRIGGER": probe.integer(
            "SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
            "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='exploration_v3' "
            "AND NOT t.tgisinternal AND t.tgconstraint<>0;"
        ),
        "V3_SEMANTIC_REGULAR_TRIGGER": probe.integer(
            "SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
            "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='exploration_v3' "
            "AND NOT t.tgisinternal AND t.tgconstraint=0 "
            "AND t.tgname='aggregate_seal_content_guard';"
        ),
        "V3_RAW_NONCONSTRAINT_TRIGGER_CATALOG_COUNT": probe.integer(
            "SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
            "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='exploration_v3' "
            "AND NOT t.tgisinternal AND t.tgconstraint=0;"
        ),
        "V50_ADDITIVE_VIEW": probe.integer(
            "SELECT count(*) FROM pg_views WHERE schemaname IN ('api_v3','exploration_v3') "
            "OR (schemaname='audit' AND viewname='exploration_v3_inventory');"
        ),
        "GOVERNED_TABLE_COUNT": len(governed_counts),
        "NONZERO_GOVERNED_TABLE_COUNT": sum(value != 0 for value in governed_counts.values()),
        "API_V3_VIEW_COUNT": len(api_view_counts),
        "NONZERO_API_V3_VIEW_COUNT": sum(value != 0 for value in api_view_counts.values()),
        "REVIEWER_QUEUE_COUNT": probe.integer(
            "SELECT count(*) FROM exploration_v3.reviewer_association_queue;"
        ),
        "V3_INVENTORY_NONZERO_METRIC_COUNT": probe.integer(
            "SELECT count(*) FROM audit.exploration_v3_inventory i "
            "CROSS JOIN LATERAL jsonb_each_text(to_jsonb(i)) e WHERE e.value::bigint<>0;"
        ),
        "FIXTURE_RESIDUE": sum(exploration_counts.values()),
    }
    if metrics != EXPECTED_METRICS:
        raise ValueError(f"unexpected live metrics for {database}: {metrics!r}")
    governed_hash = canonical_sha256(governed_counts)
    api_hash = canonical_sha256(api_view_counts)
    if governed_hash != EXPECTED_GOVERNED_TABLE_SET_SHA256:
        raise ValueError(f"governed table count-set drift for {database}")
    if api_hash != EXPECTED_API_V3_VIEW_SET_SHA256:
        raise ValueError(f"api_v3 view count-set drift for {database}")
    owner = probe.text(
        "SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=current_database();"
    )
    if owner != "gda_v49_phase2a_schema_owner":
        raise ValueError(f"unexpected database owner for {database}: {owner}")
    return {
        "database": database,
        "owner": owner,
        "schemaDump": normalized_capture(capture_dir, database),
        "metrics": metrics,
        "governedTableCountSetSha256": governed_hash,
        "apiV3ViewCountSetSha256": api_hash,
        "raceEvidence": race,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--psql", type=Path, required=True)
    parser.add_argument("--host", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--database-a", type=validate_database_name, required=True)
    parser.add_argument("--database-b", type=validate_database_name, required=True)
    parser.add_argument("--capture-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repo = args.repo.resolve()
    psql = args.psql.absolute()
    host = args.host.resolve()
    capture_dir = args.capture_dir.resolve()
    if not repo.is_dir() or not (repo / ".git").exists():
        raise ValueError(f"invalid source repository: {repo}")
    if str(psql) != "/opt/homebrew/opt/postgresql@16/bin/psql" or not os.access(psql, os.X_OK):
        raise ValueError(f"unexpected PostgreSQL client: {psql}")
    if not host.is_absolute() or not host.is_dir():
        raise ValueError(f"invalid PostgreSQL socket directory: {host}")
    if args.port == 5432 or not 1 <= args.port <= 65535:
        raise ValueError(f"invalid dedicated PostgreSQL port: {args.port}")
    if args.user != "jarlgiovanni":
        raise ValueError(f"unexpected PostgreSQL administrator: {args.user}")
    if args.database_a == args.database_b:
        raise ValueError("fresh reproduction database identities must be distinct")
    if not capture_dir.is_dir():
        raise ValueError(f"schema capture directory missing: {capture_dir}")

    psql_version = run([str(psql), "--version"])
    if psql_version != "psql (PostgreSQL) 16.13 (Homebrew)":
        raise ValueError(f"unexpected psql version: {psql_version}")
    authority = verify_authority(repo)
    source_native = verify_source_native(repo)

    probe_a = DatabaseProbe(psql, host, args.port, args.user, args.database_a)
    runtime_values = probe_a.text(
        "SELECT current_setting('server_version')||E'\\t'||"
        "current_setting('listen_addresses')||E'\\t'||"
        "current_setting('shared_memory_type')||E'\\t'||"
        "current_setting('dynamic_shared_memory_type');"
    ).split("\t")
    if runtime_values != [EXPECTED_POSTGRESQL_VERSION, "", "mmap", "posix"]:
        raise ValueError(f"unexpected PostgreSQL runtime identity: {runtime_values!r}")

    race_a = verify_race_evidence(repo, RACE_DIRECTORY_NAMES[0])
    race_b = verify_race_evidence(repo, RACE_DIRECTORY_NAMES[1])
    databases = [
        capture_database(
            probe_a,
            database=args.database_a,
            capture_dir=capture_dir,
            race=race_a,
        ),
        capture_database(
            DatabaseProbe(psql, host, args.port, args.user, args.database_b),
            database=args.database_b,
            capture_dir=capture_dir,
            race=race_b,
        ),
    ]
    if (capture_dir / f"{args.database_a}_schema.normalized.sql").read_bytes() != (
        capture_dir / f"{args.database_b}_schema.normalized.sql"
    ).read_bytes():
        raise ValueError("normalized schemas are not byte-identical")

    postgres_probe = DatabaseProbe(psql, host, args.port, args.user, "postgres")
    race_residue = postgres_probe.integer(
        "SELECT count(*) FROM pg_database WHERE "
        f"datname LIKE '{args.database_a}_race_%' "
        f"OR datname LIKE '{args.database_b}_race_%';"
    )
    target_count = postgres_probe.integer(
        "SELECT count(*) FROM pg_database WHERE "
        f"datname IN ('{args.database_a}','{args.database_b}');"
    )
    if race_residue != 0 or target_count != 2:
        raise ValueError(
            f"database identity/residue mismatch: targets={target_count} races={race_residue}"
        )
    if run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=repo
    ):
        raise ValueError("source repository changed during database capture")

    payload = {
        "schema": "trace-round16b-v50-database-reproduction-checkpoint016/v1",
        "status": "PASS",
        "checkpoint": 16,
        "authority": authority,
        "sourceNative": source_native,
        "runtime": {
            "postgresqlVersion": runtime_values[0],
            "psqlPath": str(psql),
            "host": str(host),
            "port": args.port,
            "user": args.user,
            "listenAddresses": runtime_values[1],
            "sharedMemoryType": runtime_values[2],
            "dynamicSharedMemoryType": runtime_values[3],
        },
        "databases": databases,
        "reconciliation": {
            "databaseCount": len(databases),
            "normalizedSchemasIdentical": True,
            "normalizedSchemaSha256": EXPECTED_NORMALIZED_SCHEMA_SHA256,
            "normalizedSchemaBytes": EXPECTED_NORMALIZED_SCHEMA_BYTES,
            "raceChecksumLedgersIdentical": (
                race_a["checksumsSha256"] == race_b["checksumsSha256"]
            ),
            "raceChecksumsSha256": EXPECTED_RACE_CHECKSUMS_SHA256,
            "raceDatabaseResidueCount": race_residue,
        },
        "governance": {
            "cleanSelfContainedReproduction": True,
            "sourceNativeManifestPreflight": True,
            "compatibilityAdapterUsed": False,
            "productionDataImported": False,
            "productionActivationPerformed": False,
            "deploymentPerformed": False,
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("V50_CHECKPOINT016_DATABASE_REPRODUCTION=PASS")
    print(f"DATABASE_COUNT={len(databases)}")
    print(f"NORMALIZED_SCHEMA_SHA256={EXPECTED_NORMALIZED_SCHEMA_SHA256}")
    print(f"RACE_CHECKSUMS_SHA256={EXPECTED_RACE_CHECKSUMS_SHA256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
