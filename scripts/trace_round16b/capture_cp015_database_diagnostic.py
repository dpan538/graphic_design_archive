#!/usr/bin/env python3
"""Capture the superseded CP15 database diagnostic without claiming reproduction closure."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


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
TABLE_SCHEMAS = PROJECT_SCHEMAS[:-2] + ("exploration_v3",)
EXPECTED_NUMERIC_METRICS = {
    "PROJECT_SCHEMA_COUNT": 11,
    "V3_ENUM": 21,
    "V3_TABLE": 35,
    "V3_FUNCTION": 28,
    "V3_CONSTRAINT_TRIGGER": 29,
    "V3_REGULAR_TRIGGER": 1,
    "V50_ADDITIVE_VIEW": 26,
    "GOVERNED_TABLE_COUNT": 278,
    "NONZERO_GOVERNED_TABLE_COUNT": 0,
    "API_V3_VIEW_COUNT": 24,
    "NONZERO_API_V3_VIEW_COUNT": 0,
    "REVIEWER_QUEUE_COUNT": 0,
    "V3_INVENTORY_NONZERO_METRIC_COUNT": 0,
    "FIXTURE_RESIDUE": 0,
}
EXPECTED_SCHEMA_SHA256 = "1152a494e6b64595c9f9291c1d314a9434cb763c7f2a02512d2768e286f571b4"
EXPECTED_RACE_CHECKSUMS_SHA256 = "595efb06ae1508b3f2cf952e3d0f1af2e9bd70b12bd4fcde93a530b3b70442ab"
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
    )
    if result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {argv!r}\n{result.stderr}"
        )
    return result.stdout.strip()


class DatabaseProbe:
    def __init__(self, psql: Path, host: Path, port: int, user: str, database: str) -> None:
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
        if not value.isdigit():
            raise ValueError(f"expected non-negative integer, got {value!r}")
        return int(value)

    def exact_relation_counts(self, relation_query: str) -> dict[str, int]:
        relations = [line for line in self.text(relation_query).splitlines() if line]
        counts = {relation: self.integer(f"SELECT count(*) FROM {relation};") for relation in relations}
        return counts


def race_evidence(source_repo: Path, directory_name: str) -> dict[str, object]:
    relative = Path(
        "docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/"
        "v50-round16b-seal-race"
    ) / directory_name
    directory = source_repo / relative
    checksum_path = directory / "CHECKSUMS.sha256"
    rows: dict[str, str] = {}
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 2 or fields[1] in rows:
            raise ValueError(f"invalid race checksum row: {line!r}")
        rows[fields[1]] = fields[0]
    if set(rows) != set(RACE_FILES):
        raise ValueError("race checksum file set mismatch")
    actual = {name: sha256(directory / name) for name in RACE_FILES}
    if actual != rows:
        raise ValueError("race evidence payload mismatch")
    checksum_sha = sha256(checksum_path)
    if checksum_sha != EXPECTED_RACE_CHECKSUMS_SHA256:
        raise ValueError("race checksum ledger hash mismatch")
    return {
        "relativeDirectory": relative.as_posix(),
        "checksumsSha256": checksum_sha,
        "perFileSha256": actual,
        "fileCount": len(actual),
    }


def database_capture(
    probe: DatabaseProbe,
    *,
    name: str,
    normalized_schema: Path,
    raw_schema: Path,
    race: dict[str, object],
) -> dict[str, object]:
    governed_counts = probe.exact_relation_counts(
        "SELECT format('%I.%I',schemaname,tablename) FROM pg_tables "
        f"WHERE schemaname = ANY (ARRAY[{','.join(repr(value) for value in TABLE_SCHEMAS)}]) "
        "ORDER BY schemaname COLLATE \"C\",tablename COLLATE \"C\";"
    )
    api_view_counts = probe.exact_relation_counts(
        "SELECT format('%I.%I',schemaname,viewname) FROM pg_views "
        "WHERE schemaname='api_v3' ORDER BY viewname COLLATE \"C\";"
    )
    exploration_counts = {
        relation: count
        for relation, count in governed_counts.items()
        if relation.startswith("exploration_v3.")
    }
    metrics = {
        "PROJECT_SCHEMA_COUNT": probe.integer(
            "SELECT count(*) FROM pg_namespace WHERE nspname = ANY "
            f"(ARRAY[{','.join(repr(value) for value in PROJECT_SCHEMAS)}]);"
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
        "V3_REGULAR_TRIGGER": probe.integer(
            "SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
            "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='exploration_v3' "
            "AND NOT t.tgisinternal AND t.tgconstraint=0 "
            "AND t.tgname='aggregate_seal_content_guard';"
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
    if metrics != EXPECTED_NUMERIC_METRICS:
        raise ValueError(f"unexpected database metrics for {name}: {metrics!r}")
    normalized_hash = sha256(normalized_schema)
    if normalized_hash != EXPECTED_SCHEMA_SHA256:
        raise ValueError(f"normalized schema hash mismatch for {name}")
    owner = probe.text(
        "SELECT pg_get_userbyid(datdba) FROM pg_database "
        f"WHERE datname={repr(name)};"
    )
    return {
        "database": name,
        "owner": owner,
        "metrics": metrics,
        "governedTableCountSetSha256": canonical_sha256(governed_counts),
        "apiV3ViewCountSetSha256": canonical_sha256(api_view_counts),
        "rawSchemaDumpSha256": sha256(raw_schema),
        "rawSchemaDumpBytes": raw_schema.stat().st_size,
        "normalizedSchemaSha256": normalized_hash,
        "normalizedSchemaBytes": normalized_schema.stat().st_size,
        "raceEvidence": race,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--psql", type=Path, required=True)
    parser.add_argument("--host", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--database-a", required=True)
    parser.add_argument("--database-b", required=True)
    parser.add_argument("--capture-dir", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_repo = args.source_repo.resolve()
    head = run(["git", "rev-parse", "HEAD"], cwd=source_repo)
    tree = run(["git", "rev-parse", "HEAD^{tree}"], cwd=source_repo)
    status = run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=source_repo)
    if status:
        raise ValueError(f"detached source worktree is not clean: {status}")
    server_version = DatabaseProbe(
        args.psql, args.host, args.port, args.user, args.database_a
    ).text("SHOW server_version;")
    if not server_version.startswith("16.13"):
        raise ValueError(f"unexpected PostgreSQL version: {server_version}")

    databases = []
    for suffix, database, race_name in (
        ("a", args.database_a, "gda_v50_round16b_2317"),
        ("b", args.database_b, "gda_v50_round16b_2318"),
    ):
        databases.append(
            database_capture(
                DatabaseProbe(args.psql, args.host, args.port, args.user, database),
                name=database,
                normalized_schema=args.capture_dir / f"{database}_schema.normalized.sql",
                raw_schema=args.capture_dir / f"{database}_schema.sql",
                race=race_evidence(source_repo, race_name),
            )
        )
    normalized_equal = (
        databases[0]["normalizedSchemaSha256"]
        == databases[1]["normalizedSchemaSha256"]
        == EXPECTED_SCHEMA_SHA256
    )
    if not normalized_equal:
        raise ValueError("normalized schema reconciliation failed")
    race_database_count = DatabaseProbe(
        args.psql, args.host, args.port, args.user, "postgres"
    ).integer(
        "SELECT count(*) FROM pg_database WHERE "
        "datname LIKE 'gda_v50_round16b_cp015_final_%_race_%';"
    )
    if race_database_count != 0:
        raise ValueError("disposable race database remains")

    payload = {
        "schema": "trace-round16b-cp015-database-diagnostic/v1",
        "status": "SUPERSEDED_DIAGNOSTIC_ONLY",
        "observationalRunCompleted": True,
        "cleanSelfContainedReproduction": False,
        "reproductionPassClaimed": False,
        "sourceNativeManifestPreflight": False,
        "compatibilityAdapterUsed": True,
        "supersessionReason": (
            "The frozen checkpoint11 verifier compares a historical absolute race-evidence "
            "path to the current checkout root. The adapter validated the exact byte-identical "
            "recorded locus, but this creates a hybrid run and cannot prove clean-checkout "
            "self-containment. A new run from an additive portability-correction commit is required."
        ),
        "source": {
            "head": head,
            "tree": tree,
            "worktree": str(source_repo),
            "cleanAtCapture": True,
        },
        "runtime": {
            "postgresqlVersion": server_version,
            "host": str(args.host),
            "port": args.port,
            "adminUser": args.user,
            "tcpListenerUsed": False,
        },
        "compatibilityAdapter": {
            "path": str(args.adapter),
            "sha256": sha256(args.adapter),
            "scope": "verify_v50_round16b_manifest.py preflight and replay-sequence emission only",
        },
        "databases": databases,
        "normalizedSchemasIdentical": normalized_equal,
        "normalizedSchemaSha256": EXPECTED_SCHEMA_SHA256,
        "raceDatabaseCountAtCapture": race_database_count,
        "frozenCheckpoint11ManifestModified": False,
        "frozenCheckpoint11ReceiptModified": False,
        "deploymentPerformed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("CP15_DATABASE_DIAGNOSTIC=SUPERSEDED_DIAGNOSTIC_ONLY")
    print(f"DATABASE_COUNT={len(databases)}")
    print(f"NORMALIZED_SCHEMA_SHA256={EXPECTED_SCHEMA_SHA256}")
    print("CLEAN_SELF_CONTAINED_REPRODUCTION=false")
    print("REPRODUCTION_PASS_CLAIMED=false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
