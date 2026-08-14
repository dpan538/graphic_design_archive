#!/usr/bin/env python3
"""Transactional importer for one verified Phase 2B staging bundle.

The program never reads Candidate JSON and never writes a schema object.  It
accepts only extractor output whose manifest is pinned to the Candidate hash,
mapping hash, extractor hash, original implementation base and Phase 2A
normalized schema hash.  A psql session either commits the whole population or
the server rolls its transaction back when the session exits on an error.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
MIGRATION_DIR = Path(__file__).resolve().parent
DEFAULT_SCHEMA = "4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105"
DEFAULT_CANDIDATE = "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48"
DEFAULT_BASE = "86ba95cae9ecf12e58fcabb8170c9020e151b386"
OWNER_ROLE = "gda_v49_phase2a_schema_owner"
MIGRATOR_ROLE = "gda_v49_phase2a_migrator"
UUID_NAMESPACE = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")
FIELD_OCCURRENCE_KEYS = {
    "sourceOrdinal", "sourceRecordUuid", "jsonPointer", "relativeJsonPointer",
    "jsonType", "presenceClass", "arrayOrdinal", "literalSha256",
    "fieldLiteralId", "mappingRuleId", "rawSnapshotOnly",
    "exactRawValueLocation",
}
SCALAR_JSON_TYPES = {"string", "number", "boolean", "null"}
JSON_TYPES = SCALAR_JSON_TYPES | {"object", "array", "missing"}
PRESENCE_CLASSES = {"MISSING", "NULL", "EMPTY_STRING", "EMPTY_ARRAY", "EMPTY_OBJECT", "PRESENT"}
PHASE1D_VISUAL_HASHES = {
    "surfaceOrdinalIdSequenceSha256": "0ded26112f66e9b269dd6f7ca5978d9454e254e52241ca121f63c56368eab418",
    "surfaceIdSetSha256": "7bae71cb2915a6ea6a9c9c43024a0a84bab5200edffad96298f398a7b8053d46",
    "sourceRecordIdSetSha256": "16795db4223fd1e00ef362ba0a29b7a521a38ccf56638e9928d70a3343112f2e",
    "rawVisualBundleSequenceSha256": "265cc790ffcc5b4c4dddf5ddbb29a894f35f92e166df474a744dafa0b7e8743e",
    "externalLocatorOccurrenceSequenceSha256": "1bbd68dfaf8661a1976fea56a2d121d807a42b5ed8a735094dda9868dcec5812",
    "externalLocatorValueSetSha256": "434dafb489119676615a6cd604a65286f17e2d8f2f18e48bf5e06943b6439e28",
    "classifiedSurfaceSequenceSha256": "2ba50afc2175e350895f9b7b76615ba72cf2175cf4599b13b49f5ee107242abc",
}


class ImportErrorPhase2B(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ImportErrorPhase2B("DUPLICATE_STAGING_JSON_KEY:" + key)
        value[key] = item
    return value


def b64_json_scalar(value: str, *, context: str) -> str:
    try:
        decoded = json.loads(base64.b64decode(value, validate=True).decode("utf-8"), object_pairs_hook=strict_object)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ImportErrorPhase2B("STAGING_BASE64_JSON_INVALID:" + context) from error
    if not isinstance(decoded, str):
        raise ImportErrorPhase2B("STAGING_BASE64_JSON_NOT_STRING:" + context)
    return decoded


def validate_surface_ledger_contract(stage: Path, *, inject: str | None = None) -> None:
    """Validate the exact 15,923-row source surface identity contract.

    The three identity fault modes alter only the in-memory validation stream.
    That provides a real pre-write staging failure test without editing frozen
    Candidate bytes or making a second multi-gigabyte staging copy.
    """
    ledger_path = stage / "surface-row-ledger.tsv"
    required_header = [
        "source_ordinal", "json_pointer", "surface_id_exact", "source_record_id_exact",
        "record_semantic_sha256", "archive_object_uuid", "raw_record_uuid",
        "trace_root_legacy_id", "tier_presence", "tier_exact_value",
        "research_disposition", "workflow_reason", "import_disposition",
        "parse_error", "quarantine_id",
    ]
    try:
        with ledger_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if reader.fieldnames != required_header:
                raise ImportErrorPhase2B("SURFACE_LEDGER_HEADER_MISMATCH")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as error:
        raise ImportErrorPhase2B("SURFACE_LEDGER_READ_FAILED") from error
    if any(None in row for row in rows):
        raise ImportErrorPhase2B("SURFACE_LEDGER_RAGGED_ROW")
    if inject == "duplicate_surface":
        rows.append(dict(rows[0]))
    elif inject == "missing_surface":
        rows.pop()
    elif inject == "extra_surface":
        extra = dict(rows[0])
        extra["source_ordinal"] = str(len(rows))
        extra["surface_id_exact"] = "__phase2b_injected_extra_surface__"
        extra["source_record_id_exact"] = "__phase2b_injected_extra_source__"
        rows.append(extra)
    if len(rows) != 15923:
        raise ImportErrorPhase2B(f"SURFACE_LEDGER_CARDINALITY_MISMATCH:{len(rows)}")
    ordinals: list[int] = []
    surfaces: list[str] = []
    sources: list[str] = []
    for line_number, row in enumerate(rows, start=2):
        try:
            ordinal = int(row["source_ordinal"])
        except (TypeError, ValueError) as error:
            raise ImportErrorPhase2B(f"SURFACE_LEDGER_ORDINAL_INVALID:{line_number}") from error
        if ordinal < 0 or row["json_pointer"] != f"/surfaces/{ordinal}":
            raise ImportErrorPhase2B(f"SURFACE_LEDGER_POINTER_INVALID:{line_number}")
        if not row["surface_id_exact"] or not row["source_record_id_exact"]:
            raise ImportErrorPhase2B(f"SURFACE_LEDGER_ID_BLANK:{line_number}")
        ordinals.append(ordinal)
        surfaces.append(row["surface_id_exact"])
        sources.append(row["source_record_id_exact"])
    if sorted(ordinals) != list(range(15923)):
        raise ImportErrorPhase2B("SURFACE_LEDGER_ORDINAL_SEQUENCE_MISMATCH")
    if len(set(surfaces)) != 15923:
        raise ImportErrorPhase2B("SURFACE_LEDGER_SURFACE_ID_UNIQUENESS_MISMATCH")
    if len(set(sources)) != 15923:
        raise ImportErrorPhase2B("SURFACE_LEDGER_SOURCE_ID_UNIQUENESS_MISMATCH")


def validate_stage_occurrence_contract(
    stage: Path, mapping_path: Path, manifest: dict[str, Any], *, inject: str | None = None,
) -> None:
    """Validate the generated mapping/field ledger before any DB connection.

    The full ledger remains temporary, but this verifier establishes that every
    emitted occurrence has a declared mapping rule and that every durable raw
    scalar/null literal is exactly paired with its source-record occurrence.
    It deliberately never invents values or treats a delimiter/array position
    as an implicit normalization rule.
    """
    try:
        mapping = json.loads(mapping_path.read_text(encoding="utf-8"), object_pairs_hook=strict_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ImportErrorPhase2B("MAPPING_READ_FAILED") from error
    rules = mapping.get("rules") if isinstance(mapping, dict) else None
    if not isinstance(rules, list):
        raise ImportErrorPhase2B("MAPPING_RULES_NOT_ARRAY")
    rule_by_id: dict[str, dict[str, Any]] = {}
    for rule in rules:
        rule_id = rule.get("ruleId") if isinstance(rule, dict) else None
        if not isinstance(rule_id, str) or not rule_id or rule_id in rule_by_id:
            raise ImportErrorPhase2B("MAPPING_RULE_ID_INVALID_OR_DUPLICATE")
        rule_by_id[rule_id] = rule

    occurrence_path = stage / "field-occurrence-ledger.jsonl"
    literal_path = stage / "field-literals.tsv"
    try:
        literal_handle = literal_path.open("r", encoding="utf-8", newline="")
        literal_reader = csv.DictReader(literal_handle, delimiter="\t")
        expected_literal_header = [
            "field_literal_id", "source_record_id", "json_pointer_json_b64",
            "occurrence_ordinal", "raw_value_b64",
        ]
        if literal_reader.fieldnames != expected_literal_header:
            raise ImportErrorPhase2B("FIELD_LITERAL_HEADER_MISMATCH")
        occurrence_count = 0
        literal_count = 0
        mapping_use: dict[str, int] = {}
        with occurrence_path.open("r", encoding="utf-8", newline="") as occurrences:
            for line_number, line in enumerate(occurrences, start=1):
                if not line.endswith("\n"):
                    raise ImportErrorPhase2B(f"FIELD_OCCURRENCE_MISSING_NEWLINE:{line_number}")
                try:
                    row = json.loads(line, object_pairs_hook=strict_object)
                except json.JSONDecodeError as error:
                    raise ImportErrorPhase2B(f"FIELD_OCCURRENCE_JSON_INVALID:{line_number}") from error
                if not isinstance(row, dict) or set(row) != FIELD_OCCURRENCE_KEYS:
                    raise ImportErrorPhase2B(f"FIELD_OCCURRENCE_SCHEMA_KEYS:{line_number}")
                rule_id = row["mappingRuleId"]
                if inject == "unknown_field" and line_number == 1:
                    # This exercises the same declared-rule gate used for
                    # real staged rows, without mutating the frozen bundle.
                    rule_id = "__phase2b_undeclared_mapping_rule__"
                rule = rule_by_id.get(rule_id) if isinstance(rule_id, str) else None
                if rule is None:
                    raise ImportErrorPhase2B(f"FIELD_OCCURRENCE_UNDECLARED_RULE:{line_number}")
                if row["rawSnapshotOnly"] is not bool(rule.get("rawSnapshotOnly")):
                    raise ImportErrorPhase2B(f"FIELD_OCCURRENCE_RAW_SNAPSHOT_FLAG:{line_number}")
                json_type = row["jsonType"]
                presence = row["presenceClass"]
                record_id = row["sourceRecordUuid"]
                relative_pointer = row["relativeJsonPointer"]
                raw_location = row["exactRawValueLocation"]
                literal_id = row["fieldLiteralId"]
                if json_type not in JSON_TYPES or presence not in PRESENCE_CLASSES:
                    raise ImportErrorPhase2B(f"FIELD_OCCURRENCE_VOCABULARY:{line_number}")
                if not isinstance(relative_pointer, str) or not relative_pointer.startswith("/"):
                    raise ImportErrorPhase2B(f"FIELD_OCCURRENCE_RELATIVE_POINTER:{line_number}")
                if not isinstance(raw_location, str):
                    raise ImportErrorPhase2B(f"FIELD_OCCURRENCE_RAW_LOCATION:{line_number}")
                is_literal = json_type in SCALAR_JSON_TYPES and json_type != "missing"
                if record_id is None:
                    if literal_id is not None or not raw_location.startswith("raw.source_asset.raw_bytes#"):
                        raise ImportErrorPhase2B(f"ROOT_OCCURRENCE_DURABLE_LITERAL_OR_LOCATION:{line_number}")
                else:
                    try:
                        uuid.UUID(record_id)
                    except (ValueError, TypeError) as error:
                        raise ImportErrorPhase2B(f"FIELD_OCCURRENCE_SOURCE_UUID:{line_number}") from error
                    if raw_location != f"raw.source_record.raw_value#{relative_pointer}":
                        raise ImportErrorPhase2B(f"FIELD_OCCURRENCE_RAW_LOCATION_MISMATCH:{line_number}")
                    if is_literal:
                        if not isinstance(literal_id, str):
                            raise ImportErrorPhase2B(f"FIELD_OCCURRENCE_LITERAL_ID_MISSING:{line_number}")
                        ordinal = row["arrayOrdinal"] if isinstance(row["arrayOrdinal"], int) else 0
                        expected_id = str(uuid.uuid5(UUID_NAMESPACE, f"urn:graphic-design-archive:v49:field-literal:{record_id}:{relative_pointer}:{ordinal}"))
                        if literal_id != expected_id:
                            raise ImportErrorPhase2B(f"FIELD_OCCURRENCE_LITERAL_ID_NONDETERMINISTIC:{line_number}")
                        literal_row = next(literal_reader, None)
                        if literal_row is None or None in literal_row:
                            raise ImportErrorPhase2B(f"FIELD_LITERAL_ROW_MISSING_OR_RAGGED:{line_number}")
                        if literal_row["field_literal_id"] != literal_id or literal_row["source_record_id"] != record_id:
                            raise ImportErrorPhase2B(f"FIELD_LITERAL_OCCURRENCE_PAIR_MISMATCH:{line_number}")
                        if literal_row["occurrence_ordinal"] != str(ordinal):
                            raise ImportErrorPhase2B(f"FIELD_LITERAL_ORDINAL_MISMATCH:{line_number}")
                        pointer = b64_json_scalar(literal_row["json_pointer_json_b64"], context=f"literal:{line_number}")
                        if pointer != relative_pointer:
                            raise ImportErrorPhase2B(f"FIELD_LITERAL_POINTER_MISMATCH:{line_number}")
                        try:
                            raw_bytes = base64.b64decode(literal_row["raw_value_b64"], validate=True)
                        except ValueError as error:
                            raise ImportErrorPhase2B(f"FIELD_LITERAL_BASE64_INVALID:{line_number}") from error
                        if row["literalSha256"] != hashlib.sha256(raw_bytes).hexdigest():
                            raise ImportErrorPhase2B(f"FIELD_LITERAL_DIGEST_MISMATCH:{line_number}")
                        literal_count += 1
                    elif literal_id is not None:
                        raise ImportErrorPhase2B(f"FIELD_OCCURRENCE_CONTAINER_LITERAL_ID:{line_number}")
                if not (row["arrayOrdinal"] is None or isinstance(row["arrayOrdinal"], int) and row["arrayOrdinal"] >= 0):
                    raise ImportErrorPhase2B(f"FIELD_OCCURRENCE_ARRAY_ORDINAL:{line_number}")
                mapping_use[rule_id] = mapping_use.get(rule_id, 0) + 1
                occurrence_count += 1
        if next(literal_reader, None) is not None:
            raise ImportErrorPhase2B("FIELD_LITERAL_EXTRA_ROWS")
    except (OSError, UnicodeError, csv.Error) as error:
        raise ImportErrorPhase2B("FIELD_OCCURRENCE_OR_LITERAL_READ_FAILED") from error
    finally:
        try:
            literal_handle.close()
        except UnboundLocalError:
            pass

    metrics = manifest.get("metrics", {})
    if metrics.get("fieldOccurrenceCount") != occurrence_count:
        raise ImportErrorPhase2B("FIELD_OCCURRENCE_COUNT_MISMATCH")
    if metrics.get("fieldLiteralCount") != literal_count:
        raise ImportErrorPhase2B("FIELD_LITERAL_COUNT_MISMATCH")
    if metrics.get("mappingRuleUse") != dict(sorted(mapping_use.items())):
        raise ImportErrorPhase2B("MAPPING_RULE_USE_MISMATCH")


def run(command: list[str], *, env: dict[str, str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, text=True, capture_output=True, env=env, check=False)
    if check and result.returncode != 0:
        raise ImportErrorPhase2B(
            "COMMAND_FAILED:" + " ".join(command[:3]) + "\n"
            + result.stdout[-2000:] + result.stderr[-4000:]
        )
    return result


def sql_path(path: Path) -> str:
    return str(path.resolve()).replace("'", "''")


def require_stage(
    stage: Path, expected_candidate: str, expected_schema: str, mapping_path: Path,
    *, fault: str | None = None,
) -> dict[str, Any]:
    manifest_path = stage / "staging-manifest.json"
    if not manifest_path.is_file():
        raise ImportErrorPhase2B("MISSING_STAGING_MANIFEST")
    try:
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8"), object_pairs_hook=strict_object,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ImportErrorPhase2B("STAGING_MANIFEST_READ_FAILED") from error
    if not isinstance(manifest, dict):
        raise ImportErrorPhase2B("STAGING_MANIFEST_NOT_OBJECT")
    if manifest.get("schema") != "gda-v49-phase2b-staging-manifest/v1":
        raise ImportErrorPhase2B("UNKNOWN_STAGING_MANIFEST_SCHEMA")
    if manifest.get("candidate", {}).get("sha256") != expected_candidate:
        raise ImportErrorPhase2B("CANDIDATE_SHA_MISMATCH")
    if manifest.get("schemaNormalizedSha256") != expected_schema:
        raise ImportErrorPhase2B("STAGING_SCHEMA_SHA_MISMATCH")
    if manifest.get("implementationBaseCommit") != DEFAULT_BASE:
        raise ImportErrorPhase2B("IMPLEMENTATION_BASE_COMMIT_MISMATCH")
    extractor = manifest.get("extractor")
    extractor_sha = extractor.get("sha256") if isinstance(extractor, dict) else None
    if (
        not isinstance(extractor_sha, str)
        or len(extractor_sha) != 64
        or any(char not in "0123456789abcdef" for char in extractor_sha)
    ):
        raise ImportErrorPhase2B("STAGING_EXTRACTOR_SHA_INVALID")
    # A self-consistent manifest from an unknown extractor is not an approved
    # population bundle.  Bind it to the exact checked-out implementation
    # before any PostgreSQL connection is opened.
    if sha256_file(MIGRATION_DIR / "extract.py") != extractor_sha:
        raise ImportErrorPhase2B("STAGING_EXTRACTOR_SHA_MISMATCH")
    binding = manifest.get("bundleBinding")
    if not isinstance(binding, dict) or not isinstance(binding.get("value"), str) or not isinstance(binding.get("sha256"), str):
        raise ImportErrorPhase2B("MISSING_BUNDLE_BINDING")
    expected_binding_payload = {
        "candidateSha256": expected_candidate,
        "extractorSha256": manifest.get("extractor", {}).get("sha256"),
        "implementationBaseCommit": DEFAULT_BASE,
        "mappingSha256": manifest.get("mapping", {}).get("sha256"),
        "schemaNormalizedSha256": expected_schema,
        "version": "gda-phase2b-bundle-binding-v1",
    }
    expected_binding_sha = hashlib.sha256(
        json.dumps(expected_binding_payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if binding.get("sha256") != expected_binding_sha or binding.get("value") != "gda-phase2b-bundle-binding-v1:" + expected_binding_sha:
        raise ImportErrorPhase2B("BUNDLE_BINDING_MISMATCH")
    if not mapping_path.is_file() or sha256_file(mapping_path) != manifest.get("mapping", {}).get("sha256"):
        raise ImportErrorPhase2B("STAGING_MAPPING_SHA_MISMATCH")
    metrics = manifest.get("metrics", {})
    expected_metrics = {
        "surfaceCount": 15923,
        "sourceRecordCount": 15923,
        "traceRootCount": 15923,
        "folderPairCount": 47982,
        "traceEdgeLabelLengthMismatchRows": 9393,
        "unsafePairingHeldRows": 9393,
        "unmappedSourceFields": 0,
        "silentlyDroppedFields": 0,
        "silentDelimiterSplits": 0,
        "crossArrayPositionalZips": 0,
        "automaticDeduplication": 0,
        "unexplainedMappingDeltas": 0,
    }
    for key, value in expected_metrics.items():
        if metrics.get(key) != value:
            raise ImportErrorPhase2B(f"STAGING_METRIC_MISMATCH:{key}")
    if metrics.get("tierCounts") != {"metadata_supported": 2971, "missing": 4957, "source_verified": 7995}:
        raise ImportErrorPhase2B("STAGING_TIER_BASELINE_MISMATCH")
    if metrics.get("visual") != {"locator_occurrences": 15790, "no_reference": 135, "reference_bearing": 15788}:
        raise ImportErrorPhase2B("STAGING_VISUAL_BASELINE_MISMATCH")
    if metrics.get("phase1DVisualParityHashes") != PHASE1D_VISUAL_HASHES:
        raise ImportErrorPhase2B("STAGING_PHASE1D_VISUAL_HASH_MISMATCH")
    required = {
        "source-assets.tsv", "mapping-versions.tsv", "migration-batches.tsv",
        "source-records.tsv", "field-literals.tsv", "entities.tsv", "archive-objects.tsv",
        "surface-ledgers.tsv", "object-source-links.tsv", "legacy-identities.tsv",
        "folders.tsv", "folder-assignments.tsv",
        "legacy-resolutions.tsv", "trace-nodes.tsv", "object-trace-nodes.tsv",
        "corpora.tsv", "corpus-versions.tsv", "corpus-memberships.tsv",
        "held-deltas.tsv", "visual-references.tsv", "visual-bridges.tsv",
        "visual-locators.tsv", "visual-dispositions.tsv", "visual-classifications.tsv",
        "field-occurrence-ledger.jsonl", "surface-row-ledger.tsv", "trace-delta-ledger.tsv",
        "visual-bundle-ledger.tsv", "surface-folder-pairs.tsv", "root-reconciliation-ledger.tsv",
        "observed-pointer-inventory.json", "rights-observations.tsv", "rights-assessments.tsv",
        "policy-evaluations.tsv", "delivery-assessments.tsv",
    }
    files = manifest.get("files", {})
    if set(files) != required:
        raise ImportErrorPhase2B("STAGING_FILE_ALLOWLIST_MISMATCH")
    for name, descriptor in files.items():
        path = stage / name
        if not path.is_file() or path.stat().st_size != descriptor.get("bytes") or sha256_file(path) != descriptor.get("sha256"):
            raise ImportErrorPhase2B(f"STAGING_FILE_HASH_MISMATCH:{name}")
    # This is deliberately before database ownership/schema checks: a staged
    # field or mapping contract failure must not even open a PostgreSQL session.
    validate_surface_ledger_contract(stage, inject=fault)
    validate_stage_occurrence_contract(stage, mapping_path, manifest, inject=fault)
    mapping_rows = (stage / "mapping-versions.tsv").read_text(encoding="utf-8").splitlines()
    if len(mapping_rows) != 2 or manifest["mapping"]["sha256"] not in mapping_rows[1].split("\t"):
        raise ImportErrorPhase2B("STAGING_MAPPING_ROW_MISMATCH")
    try:
        staged_binding = json.loads(base64.b64decode(mapping_rows[1].split("\t")[3]).decode("utf-8"))
    except (IndexError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ImportErrorPhase2B("STAGING_MAPPING_BINDING_DECODE_FAILED") from exc
    if staged_binding != binding["value"]:
        raise ImportErrorPhase2B("STAGING_MAPPING_BINDING_MISMATCH")
    return manifest


def schema_hash(env: dict[str, str]) -> str:
    result = run([str(ROOT / "database/scripts/schema_hash.sh")], env=env)
    return result.stdout.strip()


def psql_env(args: argparse.Namespace, user: str) -> dict[str, str]:
    env = os.environ.copy()
    env.update({"PGHOST": args.pg_host, "PGPORT": str(args.pg_port), "PGDATABASE": args.database, "PGUSER": user})
    return env


def existing_batch(stage_manifest: dict[str, Any], args: argparse.Namespace) -> str | None:
    batch_file = (args.stage_dir / "migration-batches.tsv").read_text(encoding="utf-8").splitlines()
    if len(batch_file) != 2:
        raise ImportErrorPhase2B("BATCH_STAGING_NOT_SINGLETON")
    values = batch_file[1].split("\t")
    batch_id = values[0]
    expected_input = values[4]
    expected_mapping = stage_manifest["mapping"]["sha256"]
    query = (
        "SET ROLE gda_v49_phase2a_schema_owner; "
        "SELECT b.migration_batch_id::text || '|' || b.input_sha256::text || '|' "
        "|| m.specification_sha256::text || '|' || m.parser_version FROM raw.migration_batch b "
        "JOIN raw.mapping_version m ON m.mapping_version_id=b.mapping_version_id "
        f"WHERE b.migration_batch_id = '{batch_id}'::uuid;"
    )
    result = run(["psql", "-X", "-Atq", "-v", "ON_ERROR_STOP=1", "-c", query], env=psql_env(args, MIGRATOR_ROLE))
    found = result.stdout.strip()
    if not found:
        token_query = (
            "SET ROLE gda_v49_phase2a_schema_owner; "
            "SELECT b.migration_batch_id::text || '|' || b.input_sha256::text || '|' "
            "|| m.specification_sha256::text || '|' || m.parser_version FROM raw.migration_batch b "
            "JOIN raw.mapping_version m ON m.mapping_version_id=b.mapping_version_id "
            "WHERE b.batch_token='v48-json-only-b16bb0158c3ea27c'::core.release_token;"
        )
        token_found = run(["psql", "-X", "-Atq", "-v", "ON_ERROR_STOP=1", "-c", token_query], env=psql_env(args, MIGRATOR_ROLE)).stdout.strip()
        if token_found:
            raise ImportErrorPhase2B("BATCH_TOKEN_REUSE_HASH_MISMATCH")
        return None
    components = found.split("|")
    expected_binding = stage_manifest["bundleBinding"]["value"]
    if len(components) != 4 or components[0] != batch_id or components[1] != expected_input or components[2] != expected_mapping or components[3] != expected_binding:
        raise ImportErrorPhase2B("BATCH_ID_REUSE_HASH_MISMATCH")
    return found


def reject_test_batch_mapping_collision(
    stage_manifest: dict[str, Any], args: argparse.Namespace, supplied_mapping_sha: str,
) -> None:
    """Exercise ``existing_batch`` with a synthetic conflicting bundle.

    The staged files themselves remain immutable.  We instead construct an
    in-memory candidate manifest with the *same* batch ID/input/base/schema
    but a distinct mapping component and recomputed bundle binding.  This
    reaches the production collision comparator rather than merely querying a
    row and raising a test-only error.
    """
    actual_mapping_sha = stage_manifest.get("mapping", {}).get("sha256")
    if supplied_mapping_sha == actual_mapping_sha:
        raise ImportErrorPhase2B("BATCH_COLLISION_TEST_MAPPING_NOT_DIFFERENT")
    conflicting = json.loads(json.dumps(stage_manifest))
    conflicting["mapping"]["sha256"] = supplied_mapping_sha
    payload = {
        "candidateSha256": conflicting.get("candidate", {}).get("sha256"),
        "extractorSha256": conflicting.get("extractor", {}).get("sha256"),
        "implementationBaseCommit": conflicting.get("implementationBaseCommit"),
        "mappingSha256": supplied_mapping_sha,
        "schemaNormalizedSha256": conflicting.get("schemaNormalizedSha256"),
        "version": "gda-phase2b-bundle-binding-v1",
    }
    binding_sha = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    conflicting["bundleBinding"] = {
        "value": "gda-phase2b-bundle-binding-v1:" + binding_sha,
        "sha256": binding_sha,
        "payload": payload,
    }
    try:
        existing_batch(conflicting, args)
    except ImportErrorPhase2B as error:
        if str(error) == "BATCH_ID_REUSE_HASH_MISMATCH":
            raise
        raise ImportErrorPhase2B("BATCH_COLLISION_TEST_UNEXPECTED_RESULT:" + str(error)) from error
    raise ImportErrorPhase2B("BATCH_COLLISION_TEST_DID_NOT_DIFFER")


def require_database_owner(args: argparse.Namespace) -> None:
    owner = query_database_owner(args)
    if owner != OWNER_ROLE:
        raise ImportErrorPhase2B("DISPOSABLE_DATABASE_OWNER_MISMATCH:" + owner)


def query_database_owner(args: argparse.Namespace) -> str:
    result = run(
        [
            "psql", "-X", "-Atq", "-v", "ON_ERROR_STOP=1", "-c",
            "SELECT pg_catalog.pg_get_userbyid(d.datdba) "
            "FROM pg_catalog.pg_database d WHERE d.datname = current_database();",
        ],
        env=psql_env(args, args.admin_user),
    )
    return result.stdout.strip()


def build_runtime_sql(stage: Path, inject: str | None, output: Path) -> None:
    table_files = [
        ("gda_stage_source_assets", "source-assets.tsv"),
        ("gda_stage_mapping_versions", "mapping-versions.tsv"),
        ("gda_stage_migration_batches", "migration-batches.tsv"),
        ("gda_stage_source_records", "source-records.tsv"),
        ("gda_stage_field_literals", "field-literals.tsv"),
        ("gda_stage_entities", "entities.tsv"),
        ("gda_stage_archive_objects", "archive-objects.tsv"),
        ("gda_stage_surface_ledgers", "surface-ledgers.tsv"),
        ("gda_stage_object_source_links", "object-source-links.tsv"),
        ("gda_stage_legacy_identities", "legacy-identities.tsv"),
        ("gda_stage_folders", "folders.tsv"),
        ("gda_stage_folder_assignments", "folder-assignments.tsv"),
        ("gda_stage_legacy_resolutions", "legacy-resolutions.tsv"),
        ("gda_stage_trace_nodes", "trace-nodes.tsv"),
        ("gda_stage_object_trace_nodes", "object-trace-nodes.tsv"),
        ("gda_stage_corpora", "corpora.tsv"),
        ("gda_stage_corpus_versions", "corpus-versions.tsv"),
        ("gda_stage_corpus_memberships", "corpus-memberships.tsv"),
        ("gda_stage_held_deltas", "held-deltas.tsv"),
        ("gda_stage_visual_references", "visual-references.tsv"),
        ("gda_stage_visual_bridges", "visual-bridges.tsv"),
        ("gda_stage_visual_locators", "visual-locators.tsv"),
        ("gda_stage_visual_dispositions", "visual-dispositions.tsv"),
        ("gda_stage_visual_classifications", "visual-classifications.tsv"),
        ("gda_stage_rights_observations", "rights-observations.tsv"),
        ("gda_stage_rights_assessments", "rights-assessments.tsv"),
        ("gda_stage_policy_evaluations", "policy-evaluations.tsv"),
        ("gda_stage_delivery_assessments", "delivery-assessments.tsv"),
    ]
    inject_value = inject or ""
    lines = [
        "\\set ON_ERROR_STOP on",
        "BEGIN;",
        f"SET LOCAL gda.phase2b.inject = '{inject_value}';",
        f"SET ROLE {OWNER_ROLE};",
        f"\\i '{sql_path(MIGRATION_DIR / 'prepare-staging.sql')}'",
        f"\\i '{sql_path(MIGRATION_DIR / 'prepare-runtime.sql')}'",
    ]
    for table, filename in table_files:
        lines.append(
            f"\\copy {table} FROM '{sql_path(stage / filename)}' "
            "WITH (FORMAT csv, DELIMITER E'\\t', HEADER true)"
        )
    lines.extend([
        "DO $$ BEGIN IF current_setting('gda.phase2b.inject', true) = 'after_staging' THEN "
        "RAISE EXCEPTION USING ERRCODE='P0001', MESSAGE='PHASE2B_INJECTED_FAILURE:after_staging'; END IF; END $$;",
        f"\\i '{sql_path(MIGRATION_DIR / 'load.sql')}'",
        "COMMIT;",
    ])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-dir", type=Path, required=True)
    parser.add_argument("--pg-host", required=True)
    parser.add_argument("--pg-port", type=int, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--admin-user", default="gda_v49_phase2b_admin")
    parser.add_argument("--mapping", type=Path, default=MIGRATION_DIR / "mapping-v1.json")
    parser.add_argument("--expected-schema", default=DEFAULT_SCHEMA)
    parser.add_argument("--expected-candidate", default=DEFAULT_CANDIDATE)
    parser.add_argument("--inject", choices=("after_staging", "during_objects", "after_objects", "after_corpus", "after_visual", "after_parity"))
    parser.add_argument("--fault", choices=("duplicate_surface", "missing_surface", "extra_surface", "unknown_field"))
    parser.add_argument("--test-batch-mapping-sha", help="failure-test only: a 64-hex mapping SHA expected to conflict with an existing batch")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.pg_port == 5432 or not args.pg_host.startswith("/") or not args.database.startswith("gda_v49_phase2a_"):
        raise ImportErrorPhase2B("DISPOSABLE_CONNECTION_POLICY_VIOLATION")
    args.stage_dir = args.stage_dir.resolve()
    manifest = require_stage(
        args.stage_dir, args.expected_candidate, args.expected_schema,
        args.mapping.resolve(), fault=args.fault,
    )
    if args.fault:
        raise ImportErrorPhase2B("INJECTED_STAGING_PREFLIGHT_FAILURE:" + args.fault)
    admin_env = psql_env(args, args.admin_user)
    require_database_owner(args)
    actual_schema = schema_hash(admin_env)
    if actual_schema != args.expected_schema:
        raise ImportErrorPhase2B("DATABASE_SCHEMA_SHA_MISMATCH:" + actual_schema)
    if args.test_batch_mapping_sha:
        if len(args.test_batch_mapping_sha) != 64 or any(char not in "0123456789abcdef" for char in args.test_batch_mapping_sha):
            raise ImportErrorPhase2B("INVALID_TEST_MAPPING_SHA")
        reject_test_batch_mapping_collision(manifest, args, args.test_batch_mapping_sha)
    existing = existing_batch(manifest, args)
    if existing:
        print(json.dumps({"status": "IDEMPOTENT_NOOP", "batch": existing}, sort_keys=True))
        return 0
    runtime_sql = args.stage_dir / f"runtime-import-{args.database}.sql"
    build_runtime_sql(args.stage_dir, args.inject, runtime_sql)
    try:
        result = run(["psql", "-X", "-v", "ON_ERROR_STOP=1", "-f", str(runtime_sql)], env=psql_env(args, MIGRATOR_ROLE), check=False)
    finally:
        runtime_sql.unlink(missing_ok=True)
    if result.returncode != 0:
        raise ImportErrorPhase2B("IMPORT_TRANSACTION_ROLLED_BACK\n" + result.stdout[-2000:] + result.stderr[-4000:])
    after_schema = schema_hash(admin_env)
    if after_schema != args.expected_schema:
        raise ImportErrorPhase2B("SCHEMA_DRIFT_AFTER_IMPORT:" + after_schema)
    print(json.dumps({
        "status": "COMMITTED", "batchId": manifest["ids"]["migrationBatch"],
        "schemaSha256": after_schema, "stageManifestSha256": sha256_file(args.stage_dir / "staging-manifest.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ImportErrorPhase2B, subprocess.SubprocessError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
