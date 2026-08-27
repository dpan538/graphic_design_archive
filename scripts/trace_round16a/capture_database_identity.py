#!/usr/bin/env python3
"""Capture the direct frozen database identity and four category authorities.

This Round 16A generator deliberately excludes Search, Context, and Spacetime
artifacts.  Release identity comes from the v49 freeze/release manifests, public
eligibility comes from the checksum-pinned Phase 2B surface ledger, and category
authority comes directly from the frozen SQLite ``object_folder_refs`` table.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_RELATIVE = Path("docs/audits/v49-exploration-full-space-closure-round1/raw")

FREEZE_RELATIVE = Path("database/FREEZE_V49.json")
FREEZE_DIGEST_RELATIVE = Path("database/FREEZE_V49.sha256")
RELEASE_RELATIVE = Path("docs/releases/v49/RELEASE_MANIFEST.json")
SQLITE_RELATIVE = Path("data/prefreeze_candidate_v48.sqlite")
CANONICAL_JSON_RELATIVE = Path("generated/public_surfaces_prefreeze_candidate_v48.json")
ELIGIBILITY_LEDGER_RELATIVE = Path(
    "docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv"
)
ELIGIBILITY_MANIFEST_RELATIVE = Path("docs/audits/v49-phase2b-migration/MANIFEST.json")

IDENTITY_OUTPUT_NAME = "database-identity-v2.json"
CATEGORY_OUTPUT_NAME = "category-authority-v2.tsv"

CATEGORIES = (
    ("region", "Region"),
    ("theme", "Theme"),
    ("medium", "Medium / format"),
    ("movement", "Movement context"),
)
EXPECTED_FOLDER_TYPES = frozenset(category_id for category_id, _ in CATEGORIES)

CATEGORY_FIELDS = (
    "category_id",
    "label",
    "authority_table",
    "folder_type",
    "folder_row_count",
    "real_folder_count",
    "bound_surface_count",
    "eligible_binding_row_count",
    "eligible_folder_count",
    "eligible_surface_count",
    "example_folder_id",
    "example_folder_title",
    "example_eligible_surface_id",
    "database_authority_validated",
    "status",
)


class ValidationError(RuntimeError):
    """A stable fail-closed validation failure."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValidationError(code)


def relative_name(path: Path) -> str:
    return path.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON_OBJECT_REQUIRED:{path.name}")
    return value


def freeze_digest_from_ledger(path: Path) -> str:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    require(len(lines) == 1, "FREEZE_DIGEST_LEDGER_ROW_COUNT_MISMATCH")
    fields = lines[0].split()
    require(len(fields) == 2, "FREEZE_DIGEST_LEDGER_FORMAT_INVALID")
    require(fields[1] == FREEZE_RELATIVE.as_posix(), "FREEZE_DIGEST_LEDGER_PATH_MISMATCH")
    require(len(fields[0]) == 64, "FREEZE_DIGEST_LEDGER_HASH_INVALID")
    return fields[0]


def eligibility_manifest_entry(manifest: dict[str, Any]) -> dict[str, Any]:
    files = manifest.get("files")
    require(isinstance(files, list), "ELIGIBILITY_MANIFEST_FILES_INVALID")
    matches = [item for item in files if item.get("path") == ELIGIBILITY_LEDGER_RELATIVE.name]
    require(len(matches) == 1, "ELIGIBILITY_LEDGER_MANIFEST_ENTRY_COUNT_MISMATCH")
    entry = matches[0]
    require(isinstance(entry.get("sha256"), str), "ELIGIBILITY_LEDGER_MANIFEST_HASH_MISSING")
    require(isinstance(entry.get("bytes"), int), "ELIGIBILITY_LEDGER_MANIFEST_SIZE_MISSING")
    return entry


def load_eligibility_ledger(path: Path) -> tuple[set[str], set[str], int]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required_fields = {"surface_id_exact", "research_disposition"}
        require(reader.fieldnames is not None, "ELIGIBILITY_LEDGER_HEADER_MISSING")
        require(required_fields.issubset(reader.fieldnames), "ELIGIBILITY_LEDGER_COLUMNS_MISSING")
        eligible: set[str] = set()
        held: set[str] = set()
        row_count = 0
        for row in reader:
            row_count += 1
            surface_id = row["surface_id_exact"]
            disposition = row["research_disposition"]
            require(bool(surface_id), f"ELIGIBILITY_LEDGER_EMPTY_SURFACE_ID:{row_count}")
            require(disposition in {"eligible", "held"}, f"UNKNOWN_RESEARCH_DISPOSITION:{disposition}")
            target = eligible if disposition == "eligible" else held
            require(surface_id not in target, f"DUPLICATE_ELIGIBILITY_SURFACE_ID:{surface_id}")
            target.add(surface_id)
    require(eligible.isdisjoint(held), "ELIGIBLE_HELD_OVERLAP")
    require(row_count == len(eligible) + len(held), "ELIGIBILITY_LEDGER_ID_UNIQUENESS_FAILURE")
    return eligible, held, row_count


def sqlite_uri(path: Path) -> str:
    # Frozen input: immutable mode prevents lock/WAL creation as well as writes.
    return f"{path.resolve().as_uri()}?mode=ro&immutable=1"


def scalar(connection: sqlite3.Connection, sql: str) -> int:
    row = connection.execute(sql).fetchone()
    require(row is not None and len(row) == 1, "SQLITE_SCALAR_QUERY_SHAPE_INVALID")
    return int(row[0])


def schema_catalog_identity(connection: sqlite3.Connection) -> tuple[int, str]:
    rows = connection.execute(
        """
        SELECT type, name, tbl_name, COALESCE(sql, '')
        FROM sqlite_master
        WHERE name NOT LIKE 'sqlite_%'
        ORDER BY type, name, tbl_name
        """
    ).fetchall()
    payload = [
        {"type": row[0], "name": row[1], "table": row[2], "sql": row[3]}
        for row in rows
    ]
    return len(payload), canonical_sha256(payload)


def capture_sqlite(
    database_path: Path,
    eligible_ids: set[str],
    held_ids: set[str],
    expected_object_count: int,
    expected_relationship_count: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    connection = sqlite3.connect(sqlite_uri(database_path), uri=True, isolation_level=None)
    try:
        connection.execute("PRAGMA query_only=ON")
        require(scalar(connection, "PRAGMA query_only") == 1, "SQLITE_QUERY_ONLY_NOT_ENFORCED")
        quick_check = [row[0] for row in connection.execute("PRAGMA quick_check")]
        require(quick_check == ["ok"], "SQLITE_QUICK_CHECK_FAILED")

        schema_meta = dict(connection.execute("SELECT key, value FROM schema_meta ORDER BY key"))
        required_schema_meta = {
            "active_object_count": str(expected_object_count),
            "candidate_status": "prefreeze_candidate_v48",
            "official_release": "false",
            "schema_version": "prefreeze_candidate_v48_sqlite_v1",
            "source_payload": CANONICAL_JSON_RELATIVE.as_posix(),
            "trace_influence_policy": "not_inferred",
        }
        for key, expected in required_schema_meta.items():
            require(schema_meta.get(key) == expected, f"SQLITE_SCHEMA_META_MISMATCH:{key}")

        object_rows = connection.execute("SELECT surface_id FROM objects ORDER BY surface_id").fetchall()
        object_ids = {row[0] for row in object_rows}
        require(len(object_rows) == len(object_ids), "SQLITE_OBJECT_SURFACE_ID_DUPLICATE")
        require(len(object_ids) == expected_object_count, "SQLITE_OBJECT_COUNT_MISMATCH")
        require(eligible_ids | held_ids == object_ids, "ELIGIBILITY_LEDGER_DATABASE_ID_SET_MISMATCH")

        folder_rows = connection.execute(
            """
            SELECT folder_type, folder_id, title, surface_id
            FROM object_folder_refs
            ORDER BY folder_type, folder_id, title, surface_id
            """
        ).fetchall()
        require(len(folder_rows) == expected_relationship_count, "SQLITE_FOLDER_RELATIONSHIP_COUNT_MISMATCH")

        observed_types = {row[0] for row in folder_rows}
        require(observed_types == EXPECTED_FOLDER_TYPES, "SQLITE_GOVERNED_FOLDER_TYPE_SET_MISMATCH")

        category_accumulators: dict[str, dict[str, Any]] = {
            category_id: {
                "folder_ids": set(),
                "surface_ids": set(),
                "eligible_bindings": [],
                "folder_row_count": 0,
            }
            for category_id, _ in CATEGORIES
        }
        folder_titles: dict[tuple[str, str], str] = {}
        orphan_count = 0
        for folder_type, folder_id, title, surface_id in folder_rows:
            require(bool(folder_id), f"EMPTY_FOLDER_ID:{folder_type}")
            require(bool(title), f"EMPTY_FOLDER_TITLE:{folder_type}:{folder_id}")
            if surface_id not in object_ids:
                orphan_count += 1
            key = (folder_type, folder_id)
            prior_title = folder_titles.setdefault(key, title)
            require(prior_title == title, f"FOLDER_ID_TITLE_CONFLICT:{folder_type}:{folder_id}")
            accumulator = category_accumulators[folder_type]
            accumulator["folder_row_count"] += 1
            accumulator["folder_ids"].add(folder_id)
            accumulator["surface_ids"].add(surface_id)
            if surface_id in eligible_ids:
                accumulator["eligible_bindings"].append((folder_id, title, surface_id))
        require(orphan_count == 0, "ORPHAN_FOLDER_BINDING_COUNT_NONZERO")

        category_rows: list[dict[str, Any]] = []
        for category_id, label in CATEGORIES:
            accumulator = category_accumulators[category_id]
            bindings = sorted(accumulator["eligible_bindings"])
            require(bool(accumulator["folder_ids"]), f"CATEGORY_WITHOUT_REAL_FOLDER:{category_id}")
            require(bool(bindings), f"CATEGORY_WITHOUT_ELIGIBLE_BINDING:{category_id}")
            example_folder_id, example_title, example_surface_id = bindings[0]
            category_rows.append(
                {
                    "category_id": category_id,
                    "label": label,
                    "authority_table": "object_folder_refs",
                    "folder_type": category_id,
                    "folder_row_count": accumulator["folder_row_count"],
                    "real_folder_count": len(accumulator["folder_ids"]),
                    "bound_surface_count": len(accumulator["surface_ids"]),
                    "eligible_binding_row_count": len(bindings),
                    "eligible_folder_count": len({binding[0] for binding in bindings}),
                    "eligible_surface_count": len({binding[2] for binding in bindings}),
                    "example_folder_id": example_folder_id,
                    "example_folder_title": example_title,
                    "example_eligible_surface_id": example_surface_id,
                    "database_authority_validated": "true",
                    "status": "PASS",
                }
            )

        schema_object_count, schema_catalog_sha256 = schema_catalog_identity(connection)
        database_counts = {
            "object_count": len(object_ids),
            "object_folder_reference_count": len(folder_rows),
            "governed_folder_type_count": len(observed_types),
            "real_folder_count": len(folder_titles),
            "eligible_object_count": len(eligible_ids),
            "held_object_count": len(held_ids),
            "orphan_folder_binding_count": orphan_count,
        }
        sqlite_identity = {
            "schema_meta": {key: required_schema_meta[key] for key in sorted(required_schema_meta)},
            "schema_catalog_object_count": schema_object_count,
            "schema_catalog_sha256": schema_catalog_sha256,
            "pragma_application_id": scalar(connection, "PRAGMA application_id"),
            "pragma_schema_version": scalar(connection, "PRAGMA schema_version"),
            "pragma_user_version": scalar(connection, "PRAGMA user_version"),
            "query_only": True,
            "quick_check": "ok",
            "counts": database_counts,
            "observed_governed_folder_types": sorted(observed_types),
        }
        return sqlite_identity, category_rows
    finally:
        connection.close()


def render_category_tsv(rows: Iterable[dict[str, Any]]) -> bytes:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(
        handle,
        fieldnames=CATEGORY_FIELDS,
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode("utf-8")


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


def manifest_reconciliation(freeze: dict[str, Any], release: dict[str, Any]) -> None:
    require(freeze.get("version") == 49, "FREEZE_VERSION_MISMATCH")
    require(freeze.get("freezeStatus") == "FROZEN", "DATABASE_NOT_FROZEN")
    require(release.get("release") == "v49", "RELEASE_VERSION_MISMATCH")
    comparisons = (
        ("sourceReleaseTag", "sourceReleaseTag"),
        ("sourceReleaseCommit", "sourceCommit"),
        ("schemaHash", "schemaSha256"),
        ("releaseProjectionDigest", "releaseProjectionDigest"),
        ("canonicalInputDigest", "canonicalInputSha256"),
        ("apiContractDigest", "apiContractDigest"),
        ("objectCount", "objectCount"),
        ("relationshipCount", "relationshipCount"),
        ("eligibleCount", "eligibleCount"),
        ("heldCount", "heldCount"),
        ("acceptedTraceCount", "acceptedTraceCount"),
        ("positiveRightsCount", "positiveRightsCount"),
    )
    for freeze_key, release_key in comparisons:
        require(
            freeze.get(freeze_key) == release.get(release_key),
            f"FREEZE_RELEASE_MANIFEST_MISMATCH:{freeze_key}:{release_key}",
        )
    require(
        int(freeze["eligibleCount"]) + int(freeze["heldCount"]) == int(freeze["objectCount"]),
        "PUBLIC_HELD_OBJECT_COUNT_EQUATION_FAILED",
    )
    canonical_paths = freeze.get("canonicalInputPaths")
    release_evidence_paths = freeze.get("releaseEvidencePaths")
    require(isinstance(canonical_paths, list), "FREEZE_CANONICAL_INPUT_PATHS_MISSING")
    require(isinstance(release_evidence_paths, list), "FREEZE_RELEASE_EVIDENCE_PATHS_MISSING")
    require(SQLITE_RELATIVE.as_posix() in canonical_paths, "SQLITE_NOT_A_GOVERNED_CANONICAL_INPUT")
    require(
        CANONICAL_JSON_RELATIVE.as_posix() in canonical_paths,
        "CANONICAL_JSON_NOT_A_GOVERNED_CANONICAL_INPUT",
    )
    require(
        RELEASE_RELATIVE.as_posix() in release_evidence_paths,
        "RELEASE_MANIFEST_NOT_GOVERNED_RELEASE_EVIDENCE",
    )


def capture(repo: Path) -> dict[str, Any]:
    paths = {
        "freeze_manifest": repo / FREEZE_RELATIVE,
        "freeze_digest_ledger": repo / FREEZE_DIGEST_RELATIVE,
        "release_manifest": repo / RELEASE_RELATIVE,
        "sqlite_database": repo / SQLITE_RELATIVE,
        "canonical_population_json": repo / CANONICAL_JSON_RELATIVE,
        "eligibility_ledger": repo / ELIGIBILITY_LEDGER_RELATIVE,
        "eligibility_manifest": repo / ELIGIBILITY_MANIFEST_RELATIVE,
    }
    for role, path in paths.items():
        require(path.is_file(), f"REQUIRED_INPUT_MISSING:{role}:{path}")

    freeze = read_json(paths["freeze_manifest"])
    release = read_json(paths["release_manifest"])
    eligibility_manifest = read_json(paths["eligibility_manifest"])
    manifest_reconciliation(freeze, release)

    input_hashes = {role: sha256_file(path) for role, path in paths.items()}
    freeze_expected_sha256 = freeze_digest_from_ledger(paths["freeze_digest_ledger"])
    require(
        input_hashes["freeze_manifest"] == freeze_expected_sha256,
        "FREEZE_MANIFEST_SHA256_MISMATCH",
    )

    per_file_hashes = freeze.get("perFileSha256")
    require(isinstance(per_file_hashes, dict), "FREEZE_PER_FILE_HASHES_MISSING")
    require(
        per_file_hashes.get(SQLITE_RELATIVE.as_posix()) == input_hashes["sqlite_database"],
        "SQLITE_SHA256_MISMATCH",
    )
    require(
        per_file_hashes.get(CANONICAL_JSON_RELATIVE.as_posix())
        == input_hashes["canonical_population_json"],
        "CANONICAL_JSON_SHA256_MISMATCH",
    )
    require(
        freeze.get("canonicalInputDigest") == input_hashes["canonical_population_json"],
        "FREEZE_CANONICAL_INPUT_DIGEST_MISMATCH",
    )
    require(
        release.get("canonicalInputSha256") == input_hashes["canonical_population_json"],
        "RELEASE_CANONICAL_INPUT_DIGEST_MISMATCH",
    )

    eligibility_entry = eligibility_manifest_entry(eligibility_manifest)
    require(
        eligibility_entry["sha256"] == input_hashes["eligibility_ledger"],
        "ELIGIBILITY_LEDGER_SHA256_MISMATCH",
    )
    require(
        eligibility_entry["bytes"] == paths["eligibility_ledger"].stat().st_size,
        "ELIGIBILITY_LEDGER_SIZE_MISMATCH",
    )
    require(
        eligibility_manifest.get("candidateJsonSha256") == input_hashes["canonical_population_json"],
        "ELIGIBILITY_MANIFEST_CANONICAL_INPUT_MISMATCH",
    )

    eligible_ids, held_ids, eligibility_row_count = load_eligibility_ledger(
        paths["eligibility_ledger"]
    )
    require(len(eligible_ids) == int(freeze["eligibleCount"]), "ELIGIBLE_OBJECT_COUNT_MISMATCH")
    require(len(held_ids) == int(freeze["heldCount"]), "HELD_OBJECT_COUNT_MISMATCH")

    sqlite_identity, category_rows = capture_sqlite(
        paths["sqlite_database"],
        eligible_ids,
        held_ids,
        int(freeze["objectCount"]),
        int(freeze["relationshipCount"]),
    )
    require(
        sha256_file(paths["sqlite_database"]) == input_hashes["sqlite_database"],
        "SQLITE_CHANGED_DURING_CAPTURE",
    )

    category_tsv = render_category_tsv(category_rows)
    category_sha256 = hashlib.sha256(category_tsv).hexdigest()
    release_id = str(release["release"])
    snapshot_id = f"{release_id}:{input_hashes['sqlite_database']}"
    identity_basis = {
        "database_content_sha256": input_hashes["sqlite_database"],
        "freeze_manifest_sha256": input_hashes["freeze_manifest"],
        "release_manifest_sha256": input_hashes["release_manifest"],
        "release_id": release_id,
        "schema_catalog_sha256": sqlite_identity["schema_catalog_sha256"],
        "schema_version": sqlite_identity["schema_meta"]["schema_version"],
    }

    artifact_rows = [
        {
            "byte_size": paths[role].stat().st_size,
            "path": relative_name(path.relative_to(repo)),
            "role": role,
            "sha256": input_hashes[role],
        }
        for role, path in sorted(paths.items(), key=lambda item: item[1].as_posix())
    ]
    identity_document = {
        "format": "trace-exploration-database-identity-v2",
        "status": "PASS",
        "database_snapshot_id": snapshot_id,
        "database_identity_sha256": canonical_sha256(identity_basis),
        "database_schema_version": int(freeze["version"]),
        "release_id": release_id,
        "source_release_tag": release["sourceReleaseTag"],
        "source_release_commit": release["sourceCommit"],
        "database_content_sha256": input_hashes["sqlite_database"],
        "canonical_population_sha256": input_hashes["canonical_population_json"],
        "freeze_manifest_sha256": input_hashes["freeze_manifest"],
        "release_manifest_sha256": input_hashes["release_manifest"],
        "eligibility_ledger_sha256": input_hashes["eligibility_ledger"],
        "category_authority_sha256": category_sha256,
        "identity_basis": identity_basis,
        "sqlite": sqlite_identity,
        "release_counts": {
            "object_count": int(release["objectCount"]),
            "relationship_count": int(release["relationshipCount"]),
            "eligible_count": int(release["eligibleCount"]),
            "held_count": int(release["heldCount"]),
            "accepted_trace_count": int(release["acceptedTraceCount"]),
            "positive_rights_count": int(release["positiveRightsCount"]),
        },
        "eligibility": {
            "ledger_row_count": eligibility_row_count,
            "eligible_count": len(eligible_ids),
            "held_count": len(held_ids),
            "eligible_held_overlap_count": 0,
            "database_id_set_mismatch_count": 0,
        },
        "category_authority": {
            "expected_governed_folder_types": [category_id for category_id, _ in CATEGORIES],
            "observed_governed_folder_types": sqlite_identity["observed_governed_folder_types"],
            "governed_folder_type_count": len(category_rows),
            "category_without_real_folder_count": 0,
            "category_without_eligible_binding_count": 0,
            "category_authority_artifact": f"raw/{CATEGORY_OUTPUT_NAME}",
        },
        "closure_metrics": {
            "direct_database_snapshot_validated": True,
            "direct_database_category_binding_ready": True,
            "category_without_database_authority_count": 0,
        },
        "scope_boundary": {
            "search_dependency_count": 0,
            "context_dependency_count": 0,
            "spacetime_dependency_count": 0,
            "database_text_cooccurrence_association_pass_count": 0,
            "database_metadata_inferred_relation_count": 0,
        },
        "inputs": artifact_rows,
        "validation": {
            "freeze_release_reconciliation": "PASS",
            "frozen_artifact_hashes": "PASS",
            "sqlite_read_only": "PASS",
            "sqlite_schema_identity": "PASS",
            "public_held_reconciliation": "PASS",
            "four_category_authority": "PASS",
        },
    }

    raw_dir = repo / RAW_RELATIVE
    identity_path = raw_dir / IDENTITY_OUTPUT_NAME
    category_path = raw_dir / CATEGORY_OUTPUT_NAME
    write_atomically(category_path, category_tsv)
    identity_bytes = json.dumps(
        identity_document, ensure_ascii=False, indent=2, sort_keys=True
    ).encode("utf-8") + b"\n"
    write_atomically(identity_path, identity_bytes)
    return {
        "status": "PASS",
        "database_snapshot_id": snapshot_id,
        "database_identity_sha256": identity_document["database_identity_sha256"],
        "database_identity_output": relative_name(identity_path.relative_to(repo)),
        "database_identity_output_sha256": hashlib.sha256(identity_bytes).hexdigest(),
        "category_authority_output": relative_name(category_path.relative_to(repo)),
        "category_authority_output_sha256": category_sha256,
        "governed_folder_type_count": len(category_rows),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture direct v49 database/release identity and category authority."
    )
    parser.add_argument("--repo", type=Path, default=REPO_ROOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = capture(args.repo.resolve())
    except (OSError, ValueError, KeyError, sqlite3.Error, ValidationError) as error:
        print(f"DATABASE_IDENTITY_CAPTURE_FAILED:{error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
