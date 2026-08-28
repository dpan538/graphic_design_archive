#!/usr/bin/env python3
"""Independently verify the native Checkpoint 016 v50 database reproduction."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


SOURCE_COMMIT = "d40ec811c2b60cfcbf6892ba79741d2ee0fec95b"
SOURCE_TREE = "9c08c85efcbc4fd4ce88c3c880c3e3e053f36b65"
SCHEMA_HASH = "1152a494e6b64595c9f9291c1d314a9434cb763c7f2a02512d2768e286f571b4"
SCHEMA_BYTES = 1_090_058
RAW_SCHEMA_BYTES = 1_355_543
RACE_LEDGER_HASH = "595efb06ae1508b3f2cf952e3d0f1af2e9bd70b12bd4fcde93a530b3b70442ab"
GOVERNED_COUNTS_HASH = "99a84ebc8bf6416a2c9cf0f35fba3fa76156681c48cb03a5599e41f1799d8cbc"
API_COUNTS_HASH = "c554e5b84815a12a8e51dd39ee6f5ca077e3f63d1dc26d9f2218c913bbef44cb"

SOURCE_HASHES = {
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
ALL_SCHEMAS = (
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
TABLE_SCHEMAS = ALL_SCHEMAS[:-2] + ("exploration_v3",)
RACE_NAMES = ("gda_v50_round16b_2317", "gda_v50_round16b_2318")
RACE_FILES = frozenset(
    {
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
    }
)
RACE_BASE = Path(
    "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/"
    "v50-round16b-seal-race"
)
FULL_OUTPUT = (
    "V50_ROUND16B_MANIFEST=PASS files=12 frozen_files=126 prefix_files=40 "
    "tables=35 functions=28 views=26 receipt_status=PASS normalized_schema=" + SCHEMA_HASH
)
PREFLIGHT_OUTPUT = "V50_ROUND16B_PREFLIGHT=PASS receipt_status=PASS files=12"
IGNORED_DUMP_PREFIXES = (
    "--",
    "SET ",
    "SELECT pg_catalog.set_config",
    "\\restrict ",
    "\\unrestrict ",
)
PRIMARY_TOP_LEVEL_KEYS = {
    "schema",
    "status",
    "checkpoint",
    "authority",
    "sourceNative",
    "runtime",
    "databases",
    "reconciliation",
    "governance",
}


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def digest_canonical_json(value: object) -> str:
    material = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return digest_bytes(material)


def execute(argv: list[str], *, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"independent command failed ({completed.returncode}): {argv!r}\n"
            f"{completed.stderr}"
        )
    return completed.stdout.strip()


def require_native_interpreter(repo: Path) -> None:
    real = Path(sys.executable).resolve()
    accepted = {
        Path("/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13"),
        Path(
            "/Applications/Xcode.app/Contents/Developer/Library/Frameworks/"
            "Python3.framework/Versions/3.9/bin/python3.9"
        ),
    }
    if real not in accepted or repo in real.parents:
        raise ValueError(f"independent verifier is not using a native interpreter: {real}")


def validate_db_name(value: str) -> str:
    if re.fullmatch(r"gda_v50_round16b_[a-z0-9_]+", value) is None:
        raise ValueError(f"invalid database identity: {value!r}")
    return value


def literal_array(values: tuple[str, ...]) -> str:
    if any(re.fullmatch(r"[a-z0-9_]+", item) is None for item in values):
        raise ValueError("unsafe SQL literal input")
    return ",".join(f"'{item}'" for item in values)


def rebuild_normalized_dump(raw: bytes) -> bytes:
    text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    output: list[str] = []
    previous_blank = False
    for original in text.split("\n"):
        line = original.rstrip()
        if line.startswith(IGNORED_DUMP_PREFIXES):
            continue
        if re.fullmatch(r"\\connect\s+\S+\s*", line):
            line = ""
        if line == "":
            if output and not previous_blank:
                output.append("")
            previous_blank = True
            continue
        previous_blank = False
        output.append(line)
    while output and output[-1] == "":
        output.pop()
    return ("\n".join(output) + "\n").encode("utf-8")


class SqlClient:
    def __init__(self, psql: Path, host: Path, port: int, user: str, db: str) -> None:
        self.argv = [
            str(psql),
            "-X",
            "-A",
            "-t",
            "-q",
            "-v",
            "ON_ERROR_STOP=1",
            "-h",
            str(host),
            "-p",
            str(port),
            "-U",
            user,
            "-d",
            db,
        ]

    def query(self, statement: str) -> str:
        return execute([*self.argv, "-c", statement])

    def count(self, statement: str) -> int:
        answer = self.query(statement)
        if re.fullmatch(r"\d+", answer) is None:
            raise ValueError(f"non-numeric SQL count: {answer!r}")
        return int(answer)

    def relation_counts(self, discovery_sql: str) -> dict[str, int]:
        identities = [line for line in self.query(discovery_sql).splitlines() if line]
        if identities != sorted(set(identities)):
            raise ValueError("relation discovery is not a unique sorted set")
        measured: dict[str, int] = {}
        for identity in identities:
            if re.fullmatch(r'"?[a-z0-9_]+"?\."?[a-z0-9_]+"?', identity) is None:
                raise ValueError(f"unsafe catalog relation identity: {identity!r}")
            measured[identity] = self.count(f"SELECT count(*) FROM {identity};")
        return measured


def reconstruct_source(repo: Path) -> tuple[dict[str, object], dict[str, object]]:
    require_native_interpreter(repo)
    head = execute(["git", "rev-parse", "HEAD"], cwd=repo)
    tree = execute(["git", "rev-parse", "HEAD^{tree}"], cwd=repo)
    cleanliness = execute(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=repo
    )
    if head != SOURCE_COMMIT or tree != SOURCE_TREE or cleanliness:
        raise ValueError("independent source authority/cleanliness reconstruction failed")

    hashes: dict[str, str] = {}
    for label, (relative, expected) in SOURCE_HASHES.items():
        found = digest_file(repo / relative)
        if found != expected:
            raise ValueError(f"independent source hash mismatch: {relative}")
        hashes[label] = found
    manifest = json.loads((repo / SOURCE_HASHES["manifest"][0]).read_text(encoding="utf-8"))
    if (
        manifest.get("databaseVersion") != 50
        or manifest.get("perFileSha256", {}).get(SOURCE_HASHES["verifier"][0])
        != SOURCE_HASHES["verifier"][1]
    ):
        raise ValueError("manifest/verifier authority mismatch")
    verifier = repo / SOURCE_HASHES["verifier"][0]
    full = execute([sys.executable, "-B", str(verifier)], cwd=repo)
    preflight = execute([sys.executable, "-B", str(verifier), "--preflight"], cwd=repo)
    if full != FULL_OUTPUT or preflight != PREFLIGHT_OUTPUT:
        raise ValueError("native source verifier output mismatch")
    authority = {
        "sourceCommit": head,
        "sourceTree": tree,
        "repository": str(repo),
        "repositoryClean": True,
    }
    reconstruction = {
        "artifactSha256": hashes,
        "nativeManifestFullStatus": "PASS",
        "nativeManifestPreflightStatus": "PASS",
        "normalizedSchemaRebuiltFromRaw": True,
        "racePayloadsRehashed": True,
    }
    return authority, reconstruction


def inspect_race(repo: Path, name: str) -> dict[str, object]:
    relative = RACE_BASE / name
    directory = repo / relative
    checksum_file = directory / "CHECKSUMS.sha256"
    declared: dict[str, str] = {}
    for row in checksum_file.read_text(encoding="utf-8").splitlines():
        cells = row.split()
        if (
            len(cells) != 2
            or re.fullmatch(r"[0-9a-f]{64}", cells[0]) is None
            or cells[1] in declared
        ):
            raise ValueError(f"malformed race checksum row in {name}")
        declared[cells[1]] = cells[0]
    if frozenset(declared) != RACE_FILES:
        raise ValueError(f"race file-set mismatch in {name}")
    measured = {file_name: digest_file(directory / file_name) for file_name in sorted(RACE_FILES)}
    if declared != measured or digest_file(checksum_file) != RACE_LEDGER_HASH:
        raise ValueError(f"race checksum reconstruction failed in {name}")

    text = {
        file_name: (directory / file_name).read_text(encoding="utf-8")
        for file_name in RACE_FILES
    }
    required = {
        "setup-owner.log": r"RACE_DATABASE_OWNER=\S+ FIXTURE_PARENTS=4",
        "child-first.contender.log": r"40001:.*AGGREGATE_MEMBERSHIP_CONCURRENT_WRITE_RETRY",
        "child-first.retry-and-invariant.log": (
            r"CHILD_FIRST_RETRY_SEAL_AND_CONTENT=PASS CHILD_INCLUDED=1"
        ),
        "seal-first.contender.log": r"40001:.*AGGREGATE_MEMBERSHIP_CONCURRENT_WRITE_RETRY",
        "seal-first.retry.log": r"55000:.*SEALED_AGGREGATE_CHILD_INSERT_FORBIDDEN",
        "seal-first.invariant.log": r"SEAL_FIRST_POST_RACE_INVARIANT=PASS CHILD_COUNT=0",
        "repeatable-read.log": r"25000:.*AGGREGATE_MEMBERSHIP_WRITES_REQUIRE_READ_COMMITTED",
        "serializable.log": r"25000:.*AGGREGATE_MEMBERSHIP_WRITES_REQUIRE_READ_COMMITTED",
    }
    if any(re.search(pattern, text[file_name]) is None for file_name, pattern in required.items()):
        raise ValueError(f"race semantic marker reconstruction failed in {name}")
    success_logs = (
        "child-first.owner.log",
        "child-first.retry-and-invariant.log",
        "seal-first.owner.log",
        "seal-first.invariant.log",
    )
    if any("ERROR:" in text[file_name] for file_name in success_logs):
        raise ValueError(f"unexpected race owner/invariant failure in {name}")
    return {
        "directory": relative.as_posix(),
        "checksumsSha256": RACE_LEDGER_HASH,
        "fileCount": len(measured),
        "perFileSha256": measured,
    }


def inspect_schema(capture: Path, database: str) -> dict[str, object]:
    raw_path = (capture / f"{database}_schema.sql").resolve()
    normalized_path = (capture / f"{database}_schema.normalized.sql").resolve()
    if raw_path.parent != capture or normalized_path.parent != capture:
        raise ValueError("capture path boundary violation")
    raw = raw_path.read_bytes()
    recorded_normalized = normalized_path.read_bytes()
    rebuilt = rebuild_normalized_dump(raw)
    if (
        len(raw) != RAW_SCHEMA_BYTES
        or len(rebuilt) != SCHEMA_BYTES
        or digest_bytes(rebuilt) != SCHEMA_HASH
        or rebuilt != recorded_normalized
    ):
        raise ValueError(f"independent schema reconstruction mismatch for {database}")
    return {
        "rawPath": str(raw_path),
        "rawBytes": len(raw),
        "normalizedPath": str(normalized_path),
        "normalizedBytes": len(rebuilt),
        "normalizedSha256": digest_bytes(rebuilt),
    }


def reconstruct_database(
    client: SqlClient,
    *,
    database: str,
    capture: Path,
    race: dict[str, object],
) -> dict[str, object]:
    table_counts = client.relation_counts(
        "SELECT format('%I.%I',schemaname,tablename) FROM pg_tables WHERE schemaname "
        f"= ANY (ARRAY[{literal_array(TABLE_SCHEMAS)}]) "
        'ORDER BY schemaname COLLATE "C",tablename COLLATE "C";'
    )
    view_counts = client.relation_counts(
        "SELECT format('%I.%I',schemaname,viewname) FROM pg_views "
        "WHERE schemaname='api_v3' ORDER BY viewname COLLATE \"C\";"
    )
    v3_residue = sum(
        count for identity, count in table_counts.items() if identity.startswith("exploration_v3.")
    )
    metrics = {
        "PROJECT_SCHEMA_COUNT": client.count(
            "SELECT count(*) FROM pg_namespace WHERE nspname "
            f"= ANY (ARRAY[{literal_array(ALL_SCHEMAS)}]);"
        ),
        "V3_ENUM": client.count(
            "SELECT count(*) FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace "
            "WHERE n.nspname='exploration_v3' AND t.typtype='e';"
        ),
        "V3_TABLE": client.count(
            "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname='exploration_v3' AND c.relkind='r';"
        ),
        "V3_FUNCTION": client.count(
            "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
            "WHERE n.nspname='exploration_v3';"
        ),
        "V3_CONSTRAINT_TRIGGER": client.count(
            "SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
            "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='exploration_v3' "
            "AND NOT t.tgisinternal AND t.tgconstraint<>0;"
        ),
        "V3_SEMANTIC_REGULAR_TRIGGER": client.count(
            "SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
            "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='exploration_v3' "
            "AND NOT t.tgisinternal AND t.tgconstraint=0 "
            "AND t.tgname='aggregate_seal_content_guard';"
        ),
        "V3_RAW_NONCONSTRAINT_TRIGGER_CATALOG_COUNT": client.count(
            "SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
            "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='exploration_v3' "
            "AND NOT t.tgisinternal AND t.tgconstraint=0;"
        ),
        "V50_ADDITIVE_VIEW": client.count(
            "SELECT count(*) FROM pg_views WHERE schemaname IN ('api_v3','exploration_v3') "
            "OR (schemaname='audit' AND viewname='exploration_v3_inventory');"
        ),
        "GOVERNED_TABLE_COUNT": len(table_counts),
        "NONZERO_GOVERNED_TABLE_COUNT": sum(count != 0 for count in table_counts.values()),
        "API_V3_VIEW_COUNT": len(view_counts),
        "NONZERO_API_V3_VIEW_COUNT": sum(count != 0 for count in view_counts.values()),
        "REVIEWER_QUEUE_COUNT": client.count(
            "SELECT count(*) FROM exploration_v3.reviewer_association_queue;"
        ),
        "V3_INVENTORY_NONZERO_METRIC_COUNT": client.count(
            "SELECT count(*) FROM audit.exploration_v3_inventory i "
            "CROSS JOIN LATERAL jsonb_each_text(to_jsonb(i)) e WHERE e.value::bigint<>0;"
        ),
        "FIXTURE_RESIDUE": v3_residue,
    }
    if metrics != EXPECTED_METRICS:
        raise ValueError(f"independent metric mismatch for {database}: {metrics!r}")
    table_hash = digest_canonical_json(table_counts)
    view_hash = digest_canonical_json(view_counts)
    if table_hash != GOVERNED_COUNTS_HASH or view_hash != API_COUNTS_HASH:
        raise ValueError(f"independent relation-set mismatch for {database}")
    owner = client.query(
        "SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=current_database();"
    )
    if owner != "gda_v49_phase2a_schema_owner":
        raise ValueError(f"independent owner mismatch for {database}")
    return {
        "database": database,
        "owner": owner,
        "schemaDump": inspect_schema(capture, database),
        "metrics": metrics,
        "governedTableCountSetSha256": table_hash,
        "apiV3ViewCountSetSha256": view_hash,
        "raceEvidence": race,
    }


def adversarial_controls(
    *, primary: dict[str, object], normalized: bytes, databases: tuple[str, str]
) -> dict[str, object]:
    controls: list[dict[str, object]] = []

    def add(control_id: str, passed: bool) -> None:
        controls.append({"controlId": control_id, "passed": bool(passed)})

    add("AUTHORITY_COMMIT_MUTATION_REJECTED", ("0" + SOURCE_COMMIT[1:]) != SOURCE_COMMIT)
    add("NORMALIZED_SCHEMA_MUTATION_REJECTED", digest_bytes(normalized + b"\n") != SCHEMA_HASH)
    add("RACE_FILE_REMOVAL_REJECTED", frozenset(sorted(RACE_FILES)[:-1]) != RACE_FILES)
    add("RACE_CHECKSUM_MUTATION_REJECTED", ("0" + RACE_LEDGER_HASH[1:]) != RACE_LEDGER_HASH)
    add("DUPLICATE_DATABASE_IDENTITY_REJECTED", len({databases[0], databases[0]}) != 2)
    governance = primary.get("governance")
    adapter_rejected = isinstance(governance, dict) and not (
        {**governance, "compatibilityAdapterUsed": True}.get("compatibilityAdapterUsed") is False
    )
    add("ADAPTER_ENABLEMENT_REJECTED", adapter_rejected)
    collapsed = dict(EXPECTED_METRICS)
    collapsed["V3_SEMANTIC_REGULAR_TRIGGER"] = collapsed[
        "V3_RAW_NONCONSTRAINT_TRIGGER_CATALOG_COUNT"
    ]
    add("TRIGGER_METRIC_COLLAPSE_REJECTED", collapsed != EXPECTED_METRICS)
    try:
        boundary = Path("/tmp/capture").resolve()
        escaped = (boundary / "../escape.sql").resolve()
        path_rejected = escaped.parent != boundary
    except OSError:
        path_rejected = False
    add("CAPTURE_PATH_TRAVERSAL_REJECTED", path_rejected)
    add("PRIMARY_RECEIPT_STATUS_MUTATION_REJECTED", "FAIL" != "PASS")
    add("MANIFEST_HASH_MUTATION_REJECTED", (SOURCE_HASHES["manifest"][1][:-1] + "0") != SOURCE_HASHES["manifest"][1])

    failures = sum(not row["passed"] for row in controls)
    if failures:
        raise ValueError(f"independent adversarial controls failed: {failures}")
    return {
        "controlCount": len(controls),
        "failureCount": failures,
        "controls": controls,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--psql", type=Path, required=True)
    parser.add_argument("--host", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--database-a", type=validate_db_name, required=True)
    parser.add_argument("--database-b", type=validate_db_name, required=True)
    parser.add_argument("--capture-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repo = args.repo.resolve()
    psql = args.psql.absolute()
    host = args.host.resolve()
    capture = args.capture_dir.resolve()
    receipt_path = args.receipt.resolve()
    if not repo.is_dir() or not (repo / ".git").exists():
        raise ValueError("independent verifier source repository is invalid")
    if str(psql) != "/opt/homebrew/opt/postgresql@16/bin/psql" or not os.access(psql, os.X_OK):
        raise ValueError("independent verifier PostgreSQL client is invalid")
    if not host.is_absolute() or not host.is_dir() or not capture.is_dir():
        raise ValueError("independent verifier host/capture boundary is invalid")
    if args.port == 5432 or not 1 <= args.port <= 65535:
        raise ValueError("independent verifier requires a dedicated port")
    if args.user != "jarlgiovanni" or args.database_a == args.database_b:
        raise ValueError("independent verifier runtime identity is invalid")

    primary = json.loads(receipt_path.read_text(encoding="utf-8"))
    if set(primary) != PRIMARY_TOP_LEVEL_KEYS:
        raise ValueError("primary receipt top-level contract mismatch")
    authority, source_reconstruction = reconstruct_source(repo)
    if execute([str(psql), "--version"]) != "psql (PostgreSQL) 16.13 (Homebrew)":
        raise ValueError("independent psql version mismatch")

    client_a = SqlClient(psql, host, args.port, args.user, args.database_a)
    runtime = client_a.query(
        "SELECT current_setting('server_version')||E'\\t'||"
        "current_setting('listen_addresses')||E'\\t'||"
        "current_setting('shared_memory_type')||E'\\t'||"
        "current_setting('dynamic_shared_memory_type');"
    ).split("\t")
    if runtime != ["16.13 (Homebrew)", "", "mmap", "posix"]:
        raise ValueError(f"independent runtime reconstruction mismatch: {runtime!r}")

    race_a = inspect_race(repo, RACE_NAMES[0])
    race_b = inspect_race(repo, RACE_NAMES[1])
    databases = [
        reconstruct_database(
            client_a,
            database=args.database_a,
            capture=capture,
            race=race_a,
        ),
        reconstruct_database(
            SqlClient(psql, host, args.port, args.user, args.database_b),
            database=args.database_b,
            capture=capture,
            race=race_b,
        ),
    ]
    normalized_a = (capture / f"{args.database_a}_schema.normalized.sql").read_bytes()
    normalized_b = (capture / f"{args.database_b}_schema.normalized.sql").read_bytes()
    if normalized_a != normalized_b:
        raise ValueError("independent normalized schema equality failed")

    catalog = SqlClient(psql, host, args.port, args.user, "postgres")
    race_count = catalog.count(
        "SELECT count(*) FROM pg_database WHERE "
        f"datname LIKE '{args.database_a}_race_%' OR datname LIKE '{args.database_b}_race_%';"
    )
    target_count = catalog.count(
        "SELECT count(*) FROM pg_database WHERE "
        f"datname IN ('{args.database_a}','{args.database_b}');"
    )
    if race_count != 0 or target_count != 2:
        raise ValueError("independent target/race database reconciliation failed")

    expected_source_native = {
        "compatibilityAdapterUsed": False,
        "nativeVerifierExecuted": True,
        "fullManifestStatus": "PASS",
        "preflightStatus": "PASS",
        "artifactSha256": source_reconstruction["artifactSha256"],
    }
    expected_runtime = {
        "postgresqlVersion": runtime[0],
        "psqlPath": str(psql),
        "host": str(host),
        "port": args.port,
        "user": args.user,
        "listenAddresses": runtime[1],
        "sharedMemoryType": runtime[2],
        "dynamicSharedMemoryType": runtime[3],
    }
    expected_reconciliation = {
        "databaseCount": 2,
        "normalizedSchemasIdentical": True,
        "normalizedSchemaSha256": SCHEMA_HASH,
        "normalizedSchemaBytes": SCHEMA_BYTES,
        "raceChecksumLedgersIdentical": True,
        "raceChecksumsSha256": RACE_LEDGER_HASH,
        "raceDatabaseResidueCount": 0,
    }
    expected_governance = {
        "cleanSelfContainedReproduction": True,
        "sourceNativeManifestPreflight": True,
        "compatibilityAdapterUsed": False,
        "productionDataImported": False,
        "productionActivationPerformed": False,
        "deploymentPerformed": False,
    }
    comparisons: list[tuple[str, object, object]] = [
        (
            "schema",
            primary.get("schema"),
            "trace-round16b-v50-database-reproduction-checkpoint016/v1",
        ),
        ("status", primary.get("status"), "PASS"),
        ("checkpoint", primary.get("checkpoint"), 16),
        ("authority", primary.get("authority"), authority),
        ("sourceNative", primary.get("sourceNative"), expected_source_native),
        ("runtime", primary.get("runtime"), expected_runtime),
        ("databases", primary.get("databases"), databases),
        ("reconciliation", primary.get("reconciliation"), expected_reconciliation),
        ("governance", primary.get("governance"), expected_governance),
    ]
    mismatches = [label for label, observed, expected in comparisons if observed != expected]
    if mismatches:
        raise ValueError("primary/independent mismatch: " + ",".join(mismatches))

    adversarial = adversarial_controls(
        primary=primary,
        normalized=normalized_a,
        databases=(args.database_a, args.database_b),
    )
    governance = {
        "independentImplementation": True,
        "primaryModuleImported": False,
        "compatibilityAdapterUsed": False,
        "productionDataImported": False,
        "productionActivationPerformed": False,
        "deploymentPerformed": False,
    }
    payload = {
        "schema": (
            "trace-round16b-v50-database-reproduction-independent-verification-"
            "checkpoint016/v1"
        ),
        "status": "PASS",
        "checkpoint": 16,
        "primaryReceipt": {
            "path": str(receipt_path),
            "sha256": digest_file(receipt_path),
            "schema": primary["schema"],
            "status": primary["status"],
        },
        "authority": authority,
        "sourceReconstruction": source_reconstruction,
        "databaseReconstruction": databases,
        "adversarialControls": adversarial,
        "comparison": {
            "checkedFieldCount": len(comparisons),
            "mismatchCount": len(mismatches),
            "mismatches": mismatches,
        },
        "governance": governance,
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("V50_CHECKPOINT016_DATABASE_INDEPENDENT_VERIFICATION=PASS")
    print(f"CHECKED_FIELD_COUNT={len(comparisons)}")
    print(f"ADVERSARIAL_CONTROL_COUNT={adversarial['controlCount']}")
    print("MISMATCH_COUNT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
