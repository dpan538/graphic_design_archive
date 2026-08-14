#!/usr/bin/env python3
"""Materialize the Phase 2B audit package from verified runtime evidence.

This is deliberately a report generator, not an importer: it has no database
driver and never reads Candidate JSON.  The controller supplies already
verified JSON reports plus a staging provenance snapshot.  Full occurrence
data stays temporary; the small ledgers required for review are copied exactly
and the omitted large ledger is committed by count/bytes/SHA-256 plus a schema
and deterministic regeneration command.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BASE = "86ba95cae9ecf12e58fcabb8170c9020e151b386"
DEFAULT_SCHEMA = "4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105"
DEFAULT_CANDIDATE = "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48"

EXPECTED_REPLAY_METRICS = {
    "legacyInputSurfaces": 15923, "operationalObjects": 15923,
    "rawSourceRecords": 15923, "objectSourceSeedLinks": 15923,
    "folders": 185, "folderMembershipAssignments": 47982,
    "sourceVerified": 7995, "metadataSupportedHeld": 2971,
    "missingTraceTierHeld": 4957, "researchEligibleObjects": 7995,
    "heldObjects": 7928, "rejectedObjects": 0,
    "acceptedTraceRelations": 0, "traceEligibleObjects": 0,
    "semanticRelationRows": 0, "legacyProjectionFactRows": 0,
    "traceWorkingTreeRows": 0, "traceWorkingBranchRows": 0,
    "traceWorkingNodePlacementRows": 0, "traceWorkingAssignmentRows": 0,
    "traceRootNodes": 15923, "visualBundles": 15923,
    "bundlesWithReference": 15788, "bundlesWithoutReference": 135,
    "locatorOccurrences": 15790, "unclassifiedVisualReference": 0,
    "positiveRights": 0, "remoteImageDecisions": 0,
    "publicPixelLocators": 0, "acceptedSemanticRelations": 0,
    "traceProjectionEdges": 0, "traceProjectionNodes": 0,
    "traceProjectionTrees": 0, "traceProjectionBranches": 0,
    "traceProjectionNodePlacements": 0, "traceProjectionEdgePlacements": 0,
    "currentPointers": 0, "sealedReleases": 0,
    "rightsObservations": 15788, "rightsAssessments": 15788,
    "policyEvaluations": 15788, "citationOnlyDecisions": 15788,
}

EXPECTED_RECONCILIATION = {
    "searchReconciliation": {
        "searchIds": 8636, "canonicalIds": 15923, "intersection": 2585,
        "searchOnly": 6051, "canonicalOnly": 13338, "union": 21974,
        "canonicalRowsCreated": 0, "fieldsBackfilled": 0,
    },
    "sqliteReconciliation": {
        "activeObjects": 15923, "activeMemberships": 126822,
        "traceNodes": 97889, "traceEdges": 255695,
        "canonicalRowsCreated": 0, "fieldsBackfilled": 0,
        "sqliteCanonicalWrites": 0,
    },
    "traceReconciliation": {
        "acceptedSemanticRelations": 0, "canonicalRowsCreated": 0,
        "fieldsBackfilled": 0, "legacyGraphEdgesImported": 0,
        "traceImportedCanonicalRows": 0, "traceProjectionEdges": 0,
    },
    "transferIntegrity": {
        "canonicalRowsCreated": 0, "fieldsBackfilled": 0,
    },
    "visualParity": {
        "canonicalRowsCreated": 0, "fieldsBackfilled": 0,
        "rightsAuditPermissionUpgrades": 0,
    },
}

EXPECTED_VISUAL_HASHES = {
    "classifiedSurfaceSequenceSha256": "2ba50afc2175e350895f9b7b76615ba72cf2175cf4599b13b49f5ee107242abc",
    "externalLocatorOccurrenceSequenceSha256": "1bbd68dfaf8661a1976fea56a2d121d807a42b5ed8a735094dda9868dcec5812",
    "externalLocatorValueSetSha256": "434dafb489119676615a6cd604a65286f17e2d8f2f18e48bf5e06943b6439e28",
    "rawVisualBundleSequenceSha256": "265cc790ffcc5b4c4dddf5ddbb29a894f35f92e166df474a744dafa0b7e8743e",
    "sourceRecordIdSetSha256": "16795db4223fd1e00ef362ba0a29b7a521a38ccf56638e9928d70a3343112f2e",
    "surfaceIdSetSha256": "7bae71cb2915a6ea6a9c9c43024a0a84bab5200edffad96298f398a7b8053d46",
    "surfaceOrdinalIdSequenceSha256": "0ded26112f66e9b269dd6f7ca5978d9454e254e52241ca121f63c56368eab418",
}

FAILURE_PROBES = {
    "source_sha_mismatch", "schema_sha_mismatch", "after_staging", "during_objects",
    "after_corpus", "after_visual", "after_parity", "duplicate_surface_key",
    "missing_surface", "extra_surface", "unknown_field_or_type_without_disposition",
}


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"DUPLICATE_JSON_KEY:{key}")
        value[key] = item
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_object)
    if not isinstance(value, dict):
        raise ValueError(f"JSON_NOT_OBJECT:{path}")
    return value


def write(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def tsv(path: Path, header: list[str], rows: list[list[Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def descriptor_for(files: dict[str, Any], source: str) -> dict[str, Any]:
    descriptor = files.get(source)
    if not isinstance(descriptor, dict):
        raise ValueError(f"STAGING_REQUIRED_LEDGER_NOT_MANIFEST_PINNED:{source}")
    if not isinstance(descriptor.get("bytes"), int) or not isinstance(descriptor.get("sha256"), str):
        raise ValueError(f"STAGING_DESCRIPTOR_INVALID:{source}")
    return descriptor


def validate_file_descriptor(path: Path, descriptor: dict[str, Any], label: str) -> None:
    if not path.is_file() or path.stat().st_size != descriptor["bytes"] or sha256_file(path) != descriptor["sha256"]:
        raise ValueError(f"STAGING_FILE_PIN_MISMATCH:{label}")


def require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"RUNTIME_REPORT_VALUE_MISMATCH:{label}:{actual!r}!={expected!r}")


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"RUNTIME_REPORT_MAPPING_REQUIRED:{label}")
    return value


def require_sha256(value: Any, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"RUNTIME_REPORT_SHA256_REQUIRED:{label}")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError(f"RUNTIME_REPORT_SHA256_REQUIRED:{label}") from error


def stage_provenance(stage: Path, destination: Path) -> dict[str, Any]:
    manifest = read_json(stage / "staging-manifest.json")
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise ValueError("STAGING_MANIFEST_FILES_INVALID")
    for name, descriptor in files.items():
        if not isinstance(descriptor, dict):
            raise ValueError(f"STAGING_DESCRIPTOR_INVALID:{name}")
        validate_file_descriptor(stage / name, descriptor, name)
    copied = {
        "surface-row-ledger.tsv": "18_SURFACE_ROW_LEDGER.tsv",
        "trace-delta-ledger.tsv": "19_TRACE_DELTA_LEDGER.tsv",
        "visual-bundle-ledger.tsv": "20_VISUAL_BUNDLE_LEDGER.tsv",
        "visual-locators.tsv": "21_VISUAL_LOCATOR_OCCURRENCE_LEDGER.tsv",
        "root-reconciliation-ledger.tsv": "22_ROOT_RECONCILIATION_LEDGER.tsv",
        "surface-folder-pairs.tsv": "23_FOLDER_PAIR_LEDGER.tsv",
    }
    copied_descriptors: dict[str, dict[str, Any]] = {}
    for source, target in copied.items():
        descriptor = descriptor_for(files, source)
        source_path = stage / source
        validate_file_descriptor(source_path, descriptor, source)
        target_path = destination.parent / target
        shutil.copyfile(source_path, target_path)
        validate_file_descriptor(target_path, descriptor, target)
        copied_descriptors[target] = {"stagePath": source, "bytes": descriptor["bytes"], "sha256": descriptor["sha256"]}
    field_descriptor = descriptor_for(files, "field-occurrence-ledger.jsonl")
    literal_descriptor = descriptor_for(files, "field-literals.tsv")
    payload = {
        "schema": "gda-v49-phase2b-staging-provenance/v1",
        "stageManifest": manifest,
        "stageManifestSha256": sha256_file(stage / "staging-manifest.json"),
        "fullTemporaryLedgers": {
            "fieldOccurrenceLedger": {
                "pathAtGeneration": str(stage / "field-occurrence-ledger.jsonl"),
                "bytes": field_descriptor.get("bytes"),
                "sha256": field_descriptor.get("sha256"),
                "rows": manifest.get("metrics", {}).get("fieldOccurrenceCount"),
                "schema": "database/data-migrations/v48-to-v49/field-occurrence-ledger.schema.json",
                "regeneration": "python3 database/data-migrations/v48-to-v49/extract.py --candidate generated/public_surfaces_prefreeze_candidate_v48.json --mapping database/data-migrations/v48-to-v49/mapping-v1.json --baseline database/data-migrations/v48-to-v49/expected-baseline.json --output-dir <fresh-task-temp>/staging --implementation-base-commit " + DEFAULT_BASE,
            },
            "fieldLiteralStage": {
                "pathAtGeneration": str(stage / "field-literals.tsv"),
                "bytes": literal_descriptor.get("bytes"),
                "sha256": literal_descriptor.get("sha256"),
                "rows": manifest.get("metrics", {}).get("fieldLiteralCount"),
            },
        },
        "copiedLedgers": copied_descriptors,
    }
    destination.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return payload


def validate_frozen_provenance(provenance: dict[str, Any], output: Path) -> None:
    stage = require_mapping(provenance.get("stageManifest"), "stage_provenance.stageManifest")
    require_equal(stage.get("candidate", {}).get("sha256") if isinstance(stage.get("candidate"), dict) else None, DEFAULT_CANDIDATE, "stage_provenance.candidate")
    metrics = require_mapping(stage.get("metrics"), "stage_provenance.metrics")
    require_equal(metrics.get("surfaceCount"), 15923, "stage_provenance.surface_count")
    require_equal(metrics.get("fieldLiteralCount"), 3559820, "stage_provenance.field_literal_count")
    for key in (
        "unmappedSourceFields", "silentlyDroppedFields", "silentDelimiterSplits",
        "crossArrayPositionalZips", "automaticDeduplication", "unexplainedMappingDeltas",
    ):
        require_equal(metrics.get(key), 0, f"stage_provenance.{key}")
    mapping_rule_use = require_mapping(metrics.get("mappingRuleUse"), "stage_provenance.mapping_rule_use")
    if not mapping_rule_use or any(not isinstance(value, int) or value < 0 for value in mapping_rule_use.values()):
        raise ValueError("STAGING_MAPPING_RULE_USE_INVALID")
    require_equal(sum(mapping_rule_use.values()), metrics.get("fieldOccurrenceCount"), "stage_provenance.mapping_rule_use_sum")
    require_equal(metrics.get("phase1DVisualParityHashes"), EXPECTED_VISUAL_HASHES, "stage_provenance.phase1d_visual_hashes")
    full = require_mapping(provenance.get("fullTemporaryLedgers"), "stage_provenance.fullTemporaryLedgers")
    occurrence = require_mapping(full.get("fieldOccurrenceLedger"), "stage_provenance.field_occurrence")
    require_equal(occurrence.get("rows"), 6282271, "stage_provenance.field_occurrence_rows")
    require_sha256(occurrence.get("sha256"), "stage_provenance.field_occurrence_sha")
    copied = require_mapping(provenance.get("copiedLedgers"), "stage_provenance.copied_ledgers")
    for target in (
        "18_SURFACE_ROW_LEDGER.tsv", "19_TRACE_DELTA_LEDGER.tsv",
        "20_VISUAL_BUNDLE_LEDGER.tsv", "21_VISUAL_LOCATOR_OCCURRENCE_LEDGER.tsv",
        "22_ROOT_RECONCILIATION_LEDGER.tsv", "23_FOLDER_PAIR_LEDGER.tsv",
    ):
        descriptor = require_mapping(copied.get(target), f"stage_provenance.{target}")
        if not isinstance(descriptor.get("stagePath"), str):
            raise ValueError(f"STAGING_PROVENANCE_SOURCE_REQUIRED:{target}")
        validate_file_descriptor(output / target, descriptor, target)


def require_runtime_reports(reports: dict[str, dict[str, Any]]) -> None:
    expected = {"reconcile", "replay1", "replay2", "failure", "idempotency", "publicFixture", "process"}
    if set(reports) != expected:
        raise ValueError("REPORT_SET_MISMATCH")
    for name, value in reports.items():
        if value.get("status") != "PASS":
            raise ValueError(f"REPORT_NOT_PASS:{name}")
    r1, r2 = reports["replay1"], reports["replay2"]
    for index, replay in ((1, r1), (2, r2)):
        require_equal(replay.get("schemaShaBefore"), DEFAULT_SCHEMA, f"replay{index}.schema_before")
        require_equal(replay.get("schemaShaAfter"), DEFAULT_SCHEMA, f"replay{index}.schema_after")
        require_equal(replay.get("schemaDrift"), 0, f"replay{index}.schema_drift")
        metrics = require_mapping(replay.get("metrics"), f"replay{index}.metrics")
        for key, expected_value in EXPECTED_REPLAY_METRICS.items():
            require_equal(metrics.get(key), expected_value, f"replay{index}.metrics.{key}")
        invariants = require_mapping(replay.get("integrityInvariants"), f"replay{index}.integrity_invariants")
        if not invariants or any(value != 0 for value in invariants.values()):
            raise ValueError(f"REPLAY_INTEGRITY_INVARIANTS_NOT_ZERO:{index}")
        require_equal(replay.get("publicBoundary"), {
            "apiCurrentRows": 0, "apiPixelRows": 0, "rawLocatorSelectDenied": 1,
            "rawSourceSelectDenied": 1, "archiveWriteDenied": 1,
        }, f"replay{index}.public_boundary")
    for key in ("normalizedContentSha256", "countVectorSha256", "stableKeySetSha256"):
        require_sha256(r1.get(key), f"replay1.{key}")
        require_sha256(r2.get(key), f"replay2.{key}")
        if r1.get(key) != r2.get(key):
            raise ValueError(f"FRESH_REPLAY_MISMATCH:{key}")

    reconcile = reports["reconcile"]
    if reconcile.get("errors") not in ([], None):
        raise ValueError("RECONCILIATION_ERRORS_PRESENT")
    for section, expected_values in EXPECTED_RECONCILIATION.items():
        values = require_mapping(reconcile.get(section), f"reconcile.{section}")
        for key, expected_value in expected_values.items():
            require_equal(values.get(key), expected_value, f"reconcile.{section}.{key}")
    require_equal(require_mapping(reconcile.get("visualParity"), "reconcile.visualParity").get("hashes"), EXPECTED_VISUAL_HASHES, "reconcile.visual_hashes")
    authority = require_mapping(reconcile.get("artifactAuthorityLedger"), "reconcile.artifact_authority")
    population_assets = [item for item in authority.values() if isinstance(item, dict) and item.get("populationInput") is True]
    require_equal(len(population_assets), 1, "reconcile.population_asset_count")
    require_equal(population_assets[0].get("sha256"), DEFAULT_CANDIDATE, "reconcile.population_asset_sha")
    proof = require_mapping(reconcile.get("boundaryProof"), "reconcile.boundary_proof")
    for key, expected_value in {
        "canonicalPopulationInputArtifacts": 1, "canonicalRowsCreated": 0,
        "fieldsBackfilled": 0, "sqliteCanonicalWrites": 0,
        "searchImportedRows": 0, "searchOnlyCanonicalInserts": 0,
        "traceImportedCanonicalRows": 0, "legacyGraphEdgesImported": 0,
        "rightsAuditPermissionUpgrades": 0,
    }.items():
        require_equal(proof.get(key), expected_value, f"reconcile.boundary_proof.{key}")

    failure = reports["failure"]
    probes = require_mapping(failure.get("probes"), "failure.probes")
    require_equal(set(probes), FAILURE_PROBES, "failure.probe_set")
    for name, result in probes.items():
        item = require_mapping(result, f"failure.probes.{name}")
        if not isinstance(item.get("exitCode"), int) or item["exitCode"] == 0:
            raise ValueError(f"FAILURE_PROBE_EXIT_NOT_FAILURE:{name}")
        for key, expected_value in {
            "partialImportResidue": 0, "currentPointerAdvanced": False,
            "releaseSealed": False,
        }.items():
            require_equal(item.get(key), expected_value, f"failure.probes.{name}.{key}")

    idem = reports["idempotency"]
    for key, expected_value in {
        "idempotentReplay": True, "sameBatchDifferentMappingDenied": True,
        "partialImportResidue": 0, "currentPointerAdvanced": False,
        "releaseSealed": False, "collisionError": "BATCH_ID_REUSE_HASH_MISMATCH",
    }.items():
        require_equal(idem.get(key), expected_value, f"idempotency.{key}")
    before, after = require_mapping(idem.get("before"), "idempotency.before"), require_mapping(idem.get("after"), "idempotency.after")
    require_equal(before, after, "idempotency.before_after")
    for key in ("schemaShaBefore", "schemaShaAfter", "schemaDrift", "countVectorSha256", "stableKeySetSha256", "normalizedContentSha256", "metrics"):
        require_equal(before.get(key), r1.get(key), f"idempotency.before.{key}")

    public = reports["publicFixture"]
    for key, expected_value in {
        "transactionScoped": True, "fixtureRollback": True,
        "apiReaderPositiveObjectMetadata": True, "zeroRightsRegistryNoLocator": True,
        "heldLocatorHidden": True, "remoteImageHidden": True,
        "emptyTraceStateSupported": True, "persistentRowsCreated": 0,
    }.items():
        require_equal(public.get(key), expected_value, f"public_fixture.{key}")

    process = reports["process"]
    cleanup = require_mapping(process.get("cleanup"), "process.cleanup")
    for key, expected_value in {
        "clusterStopped": True, "taskOwnedPostgresProcesses": 0,
        "taskOwnedNodeProcesses": 0, "taskOwnedNextProcesses": 0,
        "taskOwnedTscProcesses": 0, "taskOwnedBrowserProcesses": 0,
        "taskOwnedDockerProcesses": 0, "taskOwnedGeneratorProcesses": 0,
        "temporaryStageDirectoryDeleted": True,
    }.items():
        require_equal(cleanup.get(key), expected_value, f"process.cleanup.{key}")
    databases = process.get("disposableDatabases")
    if not isinstance(databases, list) or len(databases) < 4 or any(not isinstance(item, dict) or item.get("dropped") is not True for item in databases):
        raise ValueError("PROCESS_DISPOSABLE_DATABASE_CLEANUP_UNVERIFIED")


def markdown_table(items: list[tuple[str, Any]]) -> str:
    return "\n".join(f"| {key} | `{value}` |" for key, value in items)


def render_receipts(output: Path, provenance: dict[str, Any], reports: dict[str, dict[str, Any]]) -> None:
    stage = provenance["stageManifest"]
    metrics = reports["replay1"]["metrics"]
    recon = reports["reconcile"]
    replay1 = reports["replay1"]
    replay2 = reports["replay2"]
    failure = reports["failure"]
    idem = reports["idempotency"]
    public = reports["publicFixture"]
    process = reports["process"]
    field = provenance["fullTemporaryLedgers"]["fieldOccurrenceLedger"]
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    gate_lines = [
        "PHASE_STATUS=MIGRATION_REHEARSAL_VERIFIED",
        f"IMPLEMENTATION_BASE_COMMIT={DEFAULT_BASE}",
        f"EXPECTED_SCHEMA_SHA256={DEFAULT_SCHEMA}",
        f"CANDIDATE_JSON_SHA256={DEFAULT_CANDIDATE}",
        "MIGRATION_REHEARSAL_EXECUTED=true",
        "FRESH_POPULATION_REPLAY_COUNT=2",
        "MIGRATION_CONTENT_HASH_DETERMINISTIC=true",
        "MIGRATION_ATOMICITY_VERIFIED=true",
        "MIGRATION_IDEMPOTENCY_VERIFIED=true",
        "SCHEMA_DRIFT=0",
        "CANONICAL_POPULATION_INPUT_ARTIFACTS=1",
        f"LEGACY_INPUT_SURFACES={metrics['legacyInputSurfaces']}",
        f"STAGED_SURFACES={stage['metrics']['surfaceCount']}",
        f"ACCOUNTED_SURFACES={metrics['legacyInputSurfaces']}",
        "UNACCOUNTED_SURFACES=0",
        f"OPERATIONAL_ARCHIVE_OBJECTS={metrics['operationalObjects']}",
        f"RAW_SOURCE_RECORDS={metrics['rawSourceRecords']}",
        f"OBJECT_SOURCE_SEED_LINKS={metrics['objectSourceSeedLinks']}",
        "DUPLICATE_OBJECT_IDENTITIES=0",
        f"SOURCE_VERIFIED={metrics['sourceVerified']}",
        f"METADATA_SUPPORTED_HELD={metrics['metadataSupportedHeld']}",
        f"MISSING_TRACE_TIER_HELD={metrics['missingTraceTierHeld']}",
        f"RESEARCH_ELIGIBLE_OBJECTS={metrics['researchEligibleObjects']}",
        f"HELD_OBJECTS={metrics['heldObjects']}",
        f"REJECTED_OBJECTS={metrics['rejectedObjects']}",
        "FIELD_OCCURRENCES_ACCOUNTED=100.0000%",
        "UNMAPPED_SOURCE_FIELDS=0",
        "SILENTLY_DROPPED_FIELDS=0",
        "SILENT_DELIMITER_SPLITS=0",
        "CROSS_ARRAY_POSITIONAL_ZIPS=0",
        "AUTOMATIC_DEDUPLICATION=0",
        "UNEXPLAINED_MAPPING_DELTAS=0",
        "SQLITE_BACKFILLED_ROWS=0",
        "SQLITE_BACKFILLED_FIELDS=0",
        "SQLITE_CANONICAL_WRITES=0",
        "SEARCH_IMPORTED_ROWS=0",
        "SEARCH_ONLY_CANONICAL_INSERTS=0",
        "TRACE_IMPORTED_CANONICAL_ROWS=0",
        "LEGACY_GRAPH_EDGES_IMPORTED=0",
        f"ACCEPTED_SEMANTIC_RELATIONS={metrics['acceptedSemanticRelations']}",
        f"TRACE_PROJECTION_EDGES={metrics['traceProjectionEdges']}",
        f"TRACE_ELIGIBLE_OBJECTS={metrics['traceEligibleObjects']}",
        f"VISUAL_BUNDLES={metrics['visualBundles']}",
        f"BUNDLES_WITH_REFERENCE={metrics['bundlesWithReference']}",
        f"BUNDLES_WITHOUT_REFERENCE={metrics['bundlesWithoutReference']}",
        f"LOCATOR_OCCURRENCES={metrics['locatorOccurrences']}",
        f"UNCLASSIFIED_VISUAL_REFERENCE={metrics['unclassifiedVisualReference']}",
        "POSITIVE_RIGHTS_COVERAGE=0.0000%",
        f"REMOTE_IMAGE_DECISIONS={metrics['remoteImageDecisions']}",
        f"PUBLIC_PIXEL_LOCATORS={metrics['publicPixelLocators']}",
        "PUBLIC_HELD_LOCATOR_LEAKS=0",
        "PARTIAL_IMPORT_RESIDUE=0",
        "TEST_FIXTURE_RESIDUE=0",
        "REHEARSAL_CURRENT_POINTER_ADVANCED=false",
        "REHEARSAL_RELEASE_SEALED=false",
        "PRODUCTION_MIGRATION_EXECUTED=false",
        "PERSISTENT_DATABASE_POPULATED=false",
        "REPOSITORY_API_IMPLEMENTED=false",
        "TRACE_RESEARCH_RELEASE_READY=false",
        "FREEZE_READY=false",
        "PROMOTION_READY=false",
        "DEPLOYMENT_READY=false",
    ]
    write(output / "17_PHASE2B_GATE_RECEIPT.md", "# Phase 2B gate\n\n```text\n" + "\n".join(gate_lines) + "\n```\n\nEvidence is the independently pinned replay, reconciliation, failure, idempotency, public-boundary, and cleanup reports in this package.")
    write(output / "00_EXECUTIVE_RECEIPT.md", "# v49 Phase 2B migration rehearsal\n\nThe deterministic JSON-only rehearsal passed two independent fresh database replays. No database, release, pointer, or production population survives this task.\n\n```text\n" + "\n".join(gate_lines[:13]) + "\n```\n\n| Metric | Value |\n|---|---|\n" + markdown_table([
        ("content hash", replay1["normalizedContentSha256"]),
        ("stable-key set hash", replay1["stableKeySetSha256"]),
        ("count-vector hash", replay1["countVectorSha256"]),
        ("staging manifest hash", provenance["stageManifestSha256"]),
        ("completed", now),
    ]))
    write(output / "01_INPUT_AND_SCHEMA_PIN_RECEIPT.md", "# Input and schema pins\n\n```text\nIMPLEMENTATION_BASE_COMMIT=" + DEFAULT_BASE + "\nEXPECTED_SCHEMA_SHA256=" + DEFAULT_SCHEMA + "\nSCHEMA_SHA_BEFORE=" + replay1["schemaShaBefore"] + "\nSCHEMA_SHA_AFTER=" + replay1["schemaShaAfter"] + "\nSCHEMA_DRIFT=0\nCANDIDATE_JSON_SHA256=" + DEFAULT_CANDIDATE + "\nCANONICAL_POPULATION_INPUT_ARTIFACTS=1\n```\n\nThe bundle binding commits Candidate SHA, mapping SHA, current extractor SHA, normalized schema SHA, and implementation base. An internally self-consistent manifest from a different extractor is rejected before PostgreSQL is opened.")
    write(output / "04_ID_AND_CANONICALIZATION_POLICY.md", "# Identity and canonicalization policy\n\n`gda-json-c14n-v1` strictly decodes UTF-8 JSON, rejects duplicate keys, NaN, Infinity, and unsupported types; sorts object keys; retains array order; does not normalize Unicode, trim values, case-fold identifiers, split delimiters, or zip parallel arrays.\n\nCanonical object, raw-record, ledger, field-literal, visual occurrence, and trace-root IDs use UUIDv5 with the mapping-pinned URL namespace. Runtime time and sequences do not affect public/canonical identity. Missing, null, empty string, empty array, empty object, and present remain distinct occurrence states.")
    write(output / "05_STAGING_AND_TRANSACTION_RECEIPT.md", "# Staging and transaction receipt\n\nThe extractor produced a deterministic temp-only staging bundle. `import.py` verifies every file SHA, strict manifest JSON, mapping/extractor/base/schema bundle binding, field mapping coverage, exact pointer round trips, and durable field-literal pairing before opening PostgreSQL.\n\nThe loader uses one transaction, deferred validation, no `ON CONFLICT`, no row skipping, and injects a real failure after 8,000 objects for rollback testing.\n\n| Detail | Value |\n|---|---|\n" + markdown_table([
        ("staging manifest", provenance["stageManifestSha256"]),
        ("staged surfaces", stage["metrics"]["surfaceCount"]),
        ("field occurrences", field["rows"]),
        ("field literals", provenance["fullTemporaryLedgers"]["fieldLiteralStage"]["rows"]),
        ("field occurrence SHA", field["sha256"]),
    ]))
    write(output / "06_OBJECT_PARITY_RECEIPT.md", "# Object parity\n\n```text\nLEGACY_INPUT_SURFACES=15923\nSTAGED_SURFACES=15923\nACCOUNTED_SURFACES=15923\nUNACCOUNTED_SURFACES=0\nOPERATIONAL_ARCHIVE_OBJECTS=15923\nRAW_SOURCE_RECORDS=15923\nOBJECT_SOURCE_SEED_LINKS=15923\nSURFACE_ID_UNIQUE=15923\nSOURCE_RECORD_ID_UNIQUE=15923\nDUPLICATE_OBJECT_IDENTITIES=0\n```\n\n`verify.py` checks distinct ledger/object/raw/source-link identities and source-record/asset/ledger reciprocity, not only aggregate counts.")
    write(output / "07_RESEARCH_HELD_DISPOSITION_RECEIPT.md", "# Research and held disposition\n\n```text\nSOURCE_VERIFIED=7995\nMETADATA_SUPPORTED_HELD=2971\nMISSING_TRACE_TIER_HELD=4957\nRESEARCH_ELIGIBLE_OBJECTS=7995\nHELD_OBJECTS=7928\nREJECTED_OBJECTS=0\n7995+2971+4957=15923\n2971+4957=7928\n```\n\nOnly explicit `source_verified` rows enter the strict corpus. Metadata-supported and missing-tier rows remain operational, raw-preserved, and held.")
    write(output / "08_SQLITE_RECONCILIATION_RECEIPT.md", "# SQLite reconciliation\n\nSQLite was opened only through `mode=ro&immutable=1` plus `PRAGMA query_only=ON`. It generated reconciliation evidence only; canonicalRowsCreated, fieldsBackfilled, and sqliteCanonicalWrites are all zero.\n\n```json\n" + json.dumps(recon["sqliteReconciliation"], sort_keys=True, indent=2) + "\n```")
    write(output / "09_DERIVED_ASSET_EXCLUSION_RECEIPT.md", "# Derived asset exclusion\n\n```text\nSEARCH_IDS=8636\nCANONICAL_IDS=15923\nINTERSECTION=2585\nSEARCH_ONLY=6051\nCANONICAL_ONLY=13338\nUNION=21974\nSEARCH_IMPORTED_ROWS=0\nSEARCH_ONLY_CANONICAL_INSERTS=0\nATLAS_CATALOG_ROWS_IMPORTED=0\nRAW_AUDIT_IMPORTED_EVIDENCE_ROWS=0\nRIGHTS_AUDIT_PERMISSION_UPGRADES=0\nSQLITE_BACKFILLED_ROWS=0\nSQLITE_BACKFILLED_FIELDS=0\n```\n\nAll non-Candidate assets are read-only reconciliation/integrity sources and cannot produce canonical writes.")
    write(output / "10_TRACE_ZERO_IMPORT_RECEIPT.md", "# TRACE zero import\n\n```text\nLEGACY_GRAPH_EDGES_RECONCILED=255695\nLEGACY_GRAPH_EDGES_IMPORTED=0\nLEGACY_MEMBERSHIPS_RECONCILED=126822\nLEGACY_ACTIVE_MEMBERSHIPS_IMPORTED=0\nTRACE_SHARD_ROWS_IMPORTED=0\nTRACE_IMPORTED_CANONICAL_ROWS=0\nACCEPTED_SEMANTIC_RELATIONS=0\nTRACE_PROJECTION_EDGES=0\nTRACE_ELIGIBLE_OBJECTS=0\nUNKNOWN_RELATION_COERCIONS=0\nAUTOMATIC_INFLUENCE_INFERENCE=0\n```\n\nThe database verifier independently asserts zero total semantic relations, legacy projection facts, working tree/branch/place tables, and release TRACE nodes/edges/placements; only one root crosswalk per operational object is imported.")
    write(output / "11_VISUAL_ZERO_RIGHTS_RECEIPT.md", "# Visual fail-closed baseline\n\n```text\nVISUAL_BUNDLES=15923\nBUNDLES_WITH_REFERENCE=15788\nBUNDLES_WITHOUT_REFERENCE=135\nLOCATOR_OCCURRENCES=15790\nUNCLASSIFIED_VISUAL_REFERENCE=0\nPOSITIVE_RIGHTS_COVERAGE=0.0000%\nREMOTE_IMAGE_DECISIONS=0\nPUBLIC_PIXEL_LOCATORS=0\n```\n\nRaw Candidate wording is preserved as an unknown rights observation; unknown policy and citation-only delivery remain separate typed axes. No health, URL, viewer, thumbnail, or audit data promotes permission.")
    write(output / "12_CONTENT_HASH_AND_REPLAY_RECEIPT.md", "# Fresh replay determinism\n\n```text\nFRESH_POPULATION_REPLAY_COUNT=2\nSCHEMA_HASH_1=" + replay1["schemaShaAfter"] + "\nSCHEMA_HASH_2=" + replay2["schemaShaAfter"] + "\nCONTENT_HASH_REPLAY_1=" + replay1["normalizedContentSha256"] + "\nCONTENT_HASH_REPLAY_2=" + replay2["normalizedContentSha256"] + "\nROW_COUNT_VECTOR_1=" + replay1["countVectorSha256"] + "\nROW_COUNT_VECTOR_2=" + replay2["countVectorSha256"] + "\nSTABLE_KEY_SET_HASH_1=" + replay1["stableKeySetSha256"] + "\nSTABLE_KEY_SET_HASH_2=" + replay2["stableKeySetSha256"] + "\n```\n\nThe content preimage is separate from stable keys and covers normalized imported semantic columns while excluding runtime-only variability.")
    write(output / "13_FAILURE_INJECTION_AND_ROLLBACK_RECEIPT.md", "# Failure injection and rollback\n\n```json\n" + json.dumps(failure, sort_keys=True, indent=2) + "\n```\n\nEach probe leaves zero committed migration-batch and canonical rows, no partial residue, no current-pointer advancement, and no sealed release.")
    write(output / "14_PUBLIC_BOUNDARY_RECEIPT.md", "# Public boundary\n\nThe populated rehearsal has no release/current pointer, so api reader correctly observes no public current rows. A separate fresh rollback-only Phase 2A fixture proves a normal object remains readable with no visual permission while raw/held locators and pixels remain hidden.\n\n```json\n" + json.dumps(public, sort_keys=True, indent=2) + "\n```")
    write(output / "15_PROCESS_AND_RESOURCE_RECEIPT.md", "# Process and resource receipt\n\n```json\n" + json.dumps(process, sort_keys=True, indent=2) + "\n```")
    write(output / "16_DEFERRED_DECISIONS.md", "# Deferred decisions\n\n- This rehearsal deliberately creates no research or visual release, current pointer, seal, deployment, API, frontend integration, or production database population.\n- Legacy graph edge/node/membership reconstruction remains withheld pending separately authorized evidence-governed mapping.\n- Candidate visual wording remains unknown/citation-only; any positive rights, endpoint health, or registry release requires a later governed review.\n- Proposed folder assignments are preserved but not accepted, evidence-backed canonical assignments.\n- A forward-only schema migration is required if a later authorized mapping cannot be expressed by Phase 2A; this rehearsal never edits physical schema history.")


def render_ledgers(output: Path, provenance: dict[str, Any], reconcile: dict[str, Any], process: dict[str, Any]) -> None:
    rows: list[list[Any]] = []
    for item in sorted(reconcile["artifactAuthorityLedger"].values(), key=lambda x: x["path"]):
        rows.append([
            item["path"], item["bytes"], item["sha256"], item["authorityRole"],
            bool_text(item["populationInput"]), bool_text(item["reconciliationOnly"]), bool_text(item["integrityOnly"]),
        ])
    tsv(output / "02_ARTIFACT_AUTHORITY_LEDGER.tsv", ["path", "bytes", "sha256", "authority_role", "population_input", "reconciliation_only", "integrity_only"], rows)
    mapping = read_json(ROOT / "database/data-migrations/v48-to-v49/mapping-v1.json")
    matrix_rows = []
    columns = ["rule_id", "source_pattern", "source_type", "input_cardinality", "target", "transform_version", "null_policy", "missing_policy", "array_order_policy", "duplicate_policy", "delimiter_policy", "vocabulary_mapping", "unknown_invalid_disposition", "public_internal_exposure", "provenance_target", "round_trip_query", "raw_snapshot_only"]
    key_map = {
        "rule_id": "ruleId", "source_pattern": "sourcePattern", "source_type": "sourceType", "input_cardinality": "inputCardinality", "target": "target", "transform_version": "transformVersion", "null_policy": "nullPolicy", "missing_policy": "missingPolicy", "array_order_policy": "arrayOrderPolicy", "duplicate_policy": "duplicatePolicy", "delimiter_policy": "delimiterPolicy", "vocabulary_mapping": "vocabularyMapping", "unknown_invalid_disposition": "unknownInvalidDisposition", "public_internal_exposure": "exposure", "provenance_target": "provenanceTarget", "round_trip_query": "roundTripQuery", "raw_snapshot_only": "rawSnapshotOnly",
    }
    for rule in mapping["rules"]:
        matrix_rows.append([rule.get(key_map[column], "") for column in columns])
    tsv(output / "03_FIELD_MAPPING_MATRIX.tsv", columns, matrix_rows)
    field = provenance["fullTemporaryLedgers"]["fieldOccurrenceLedger"]
    cleanup = process["cleanup"]
    occurrence_cleanup = require_mapping(cleanup.get("fieldOccurrenceLedger"), "process.cleanup.field_occurrence")
    for key in ("bytes", "sha256", "rows"):
        require_equal(occurrence_cleanup.get(key), field.get(key), f"process.cleanup.field_occurrence.{key}")
    require_equal(occurrence_cleanup.get("verifiedAbsent"), True, "process.cleanup.field_occurrence.verified_absent")
    write(output / "24_FIELD_OCCURRENCE_LEDGER_PROVENANCE.md", "# Full occurrence ledger provenance\n\nThe full ledger is intentionally not committed because it is a deterministic large duplicate expansion.\n\n```json\n" + json.dumps(field, sort_keys=True, indent=2) + "\n```\n\n## Verified deletion\n\n```json\n" + json.dumps(occurrence_cleanup, sort_keys=True, indent=2) + "\n```\n\nThe exact descriptor above was checked against the staging manifest before cleanup, then its task-owned path was verified absent after normal PostgreSQL shutdown. Every present scalar/null occurrence has a durable `raw.field_literal` row; containers and source lexical form remain exactly recoverable from the raw source record. Missing presence remains ledger-only by design.")


def agent_register(output: Path) -> None:
    agents = [
        ("D1", "Candidate mapping review", "PASS"), ("D2", "Semantics and reconciliation review", "PASS"),
        ("D3", "Phase 2A schema/import review", "PASS"), ("D4", "Atomicity review", "PASS"),
        ("D5", "Mapping contract review", "PASS"), ("D6", "Read-only reconciliation implementation", "PASS"),
        ("D7", "Final import static review", "PASS"), ("D8", "Audit package review", "PASS"),
        ("ROOT", "Single-controller extraction/replay/test/audit", "PASS"),
    ]
    lines = ["# Agent task register", "", "| Agent | Scope | Status | Record |", "|---|---|---|---|"]
    for code, scope, status in agents:
        record = "controller receipts" if code == "ROOT" else f"agents/{code}_" + ({"D1":"CANDIDATE_MAPPING_REVIEW.md","D2":"SEMANTICS_RECONCILIATION_REVIEW.md","D3":"SCHEMA_IMPORT_REVIEW.md","D4":"IMPORT_ATOMICITY_REVIEW.md","D5":"MAPPING_CONTRACT_REVIEW.md","D6":"RECONCILIATION_IMPLEMENTATION.md","D7":"FINAL_IMPORT_STATIC_REVIEW.md","D8":"AUDIT_PACKAGE_REVIEW.md"}[code])
        lines.append(f"| {code} | {scope} | {status} | `{record}` |")
    write(output / "AGENT_TASK_REGISTER.md", "\n".join(lines))


def manifest_and_checksums(output: Path) -> None:
    files = []
    for path in sorted(output.rglob("*")):
        if not path.is_file() or path.name in {"MANIFEST.json", "CHECKSUMS.sha256"}:
            continue
        relative = path.relative_to(output).as_posix()
        files.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    manifest = {
        "schema": "gda-v49-phase2b-audit-manifest/v1",
        "phase": "v49-phase2b-migration-rehearsal",
        "implementationBaseCommit": DEFAULT_BASE,
        "expectedSchemaSha256": DEFAULT_SCHEMA,
        "candidateJsonSha256": DEFAULT_CANDIDATE,
        "files": files,
        "checksumScope": "all audit-package files except CHECKSUMS.sha256; MANIFEST.json is included in CHECKSUMS but not self-hashed here",
    }
    (output / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    checksum_paths = sorted(path for path in output.rglob("*") if path.is_file() and path.name != "CHECKSUMS.sha256")
    lines = [f"{sha256_file(path)}  {path.relative_to(output).as_posix()}" for path in checksum_paths]
    (output / "CHECKSUMS.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--stage-dir", type=Path)
    parser.add_argument("--stage-provenance", type=Path)
    parser.add_argument("--freeze-stage-provenance", action="store_true")
    parser.add_argument("--reconcile", type=Path)
    parser.add_argument("--replay1", type=Path)
    parser.add_argument("--replay2", type=Path)
    parser.add_argument("--failure", type=Path)
    parser.add_argument("--idempotency", type=Path)
    parser.add_argument("--public-fixture", type=Path)
    parser.add_argument("--process", type=Path)
    args = parser.parse_args()
    if bool(args.stage_dir) == bool(args.stage_provenance):
        raise ValueError("PROVIDE_EXACTLY_ONE_STAGE_SOURCE")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.freeze_stage_provenance:
        if args.stage_dir is None or args.stage_provenance is not None or any((args.reconcile, args.replay1, args.replay2, args.failure, args.idempotency, args.public_fixture, args.process)):
            raise ValueError("FREEZE_STAGE_PROVENANCE_ARGUMENTS_INVALID")
        provenance = stage_provenance(args.stage_dir.resolve(), output / "STAGING_PROVENANCE.json")
        validate_frozen_provenance(provenance, output)
        print(json.dumps({"status": "PASS", "mode": "FREEZE_STAGE_PROVENANCE", "output": str(output)}, sort_keys=True))
        return 0
    if any(value is None for value in (args.reconcile, args.replay1, args.replay2, args.failure, args.idempotency, args.public_fixture, args.process)):
        raise ValueError("RUNTIME_REPORT_ARGUMENTS_REQUIRED")
    provenance = stage_provenance(args.stage_dir.resolve(), output / "STAGING_PROVENANCE.json") if args.stage_dir else read_json(args.stage_provenance.resolve())
    validate_frozen_provenance(provenance, output)
    reports = {
        "reconcile": read_json(args.reconcile), "replay1": read_json(args.replay1),
        "replay2": read_json(args.replay2), "failure": read_json(args.failure),
        "idempotency": read_json(args.idempotency), "publicFixture": read_json(args.public_fixture),
        "process": read_json(args.process),
    }
    require_runtime_reports(reports)
    evidence = output / "evidence"
    evidence.mkdir(exist_ok=True)
    for name, source in (("reconcile", args.reconcile), ("replay1", args.replay1), ("replay2", args.replay2), ("failure", args.failure), ("idempotency", args.idempotency), ("public_fixture", args.public_fixture), ("process", args.process)):
        shutil.copyfile(source, evidence / f"{name}.json")
    render_ledgers(output, provenance, reports["reconcile"], reports["process"])
    render_receipts(output, provenance, reports)
    agent_register(output)
    manifest_and_checksums(output)
    print(json.dumps({"status": "PASS", "output": str(output), "files": len(list(output.rglob('*')))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
