from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "db"

DEFAULT_MIGRATIONS = [
    "001_initial_schema.sql",
    "002_operational_skeleton.sql",
    "004_coverage_skeleton.sql",
    "005_global_classification_skeleton.sql",
    "006_publication_surface_skeleton.sql",
    "007_authority_normalization_skeleton.sql",
    "008_source_rights_policy_skeleton.sql",
    "009_first_ingest_scope_skeleton.sql",
    "011_ingest_contract_targets_skeleton.sql",
    "012_deep_research_outputs_skeleton.sql",
    "013_capture_batch_skeleton.sql",
    "003_read_models.sql",
    "010_seed_data.sql",
]

VALIDATION = "900_validation_queries.sql"


def run_psql(database_url: str, sql_file: Path) -> None:
    cmd = ["psql", database_url, "--set", "ON_ERROR_STOP=1", "--file", str(sql_file)]
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PostgreSQL migrations for the archive index.")
    parser.add_argument("--dry-run", action="store_true", help="List migrations without running them.")
    parser.add_argument("--schema-only", action="store_true", help="Run schema/read-model migrations without seed data.")
    parser.add_argument("--validate", action="store_true", help="Run validation SQL after migrations.")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="PostgreSQL connection URL. Defaults to DATABASE_URL.",
    )
    args = parser.parse_args()

    migrations = list(DEFAULT_MIGRATIONS)
    if args.schema_only:
        migrations = [m for m in migrations if m != "010_seed_data.sql"]

    missing = [m for m in migrations if not (DB / m).exists()]
    if args.validate and not (DB / VALIDATION).exists():
        missing.append(VALIDATION)

    if missing:
        print("Missing migration files:")
        for item in missing:
            print(f"  - {item}")
        raise SystemExit(1)

    print("Migration plan:")
    for migration in migrations:
        print(f"  - db/{migration}")
    if args.validate:
        print(f"  - db/{VALIDATION}")

    if args.dry_run:
        print("Dry run only. No database changes made.")
        return

    if not args.database_url:
        print("DATABASE_URL is required unless --dry-run is used.")
        raise SystemExit(2)

    for migration in migrations:
        run_psql(args.database_url, DB / migration)

    if args.validate:
        run_psql(args.database_url, DB / VALIDATION)

    print("Migrations completed.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"Migration failed: {exc}", file=sys.stderr)
        raise SystemExit(exc.returncode)
