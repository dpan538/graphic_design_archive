#!/usr/bin/env python3
"""Render the auditable partial Phase 2B performance-block package.

Unlike ``generate_audit.py``, this renderer cannot emit a successful migration
gate.  It accepts only the immutable live-performance, rollback, relocation,
failure, recovery, reconciliation, and cleanup checkpoints created during the
bounded stop procedure.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[3]
EXPECTED_BASE = "86ba95cae9ecf12e58fcabb8170c9020e151b386"
EXPECTED_SCHEMA = "4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105"
EXPECTED_CANDIDATE = "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48"
EXPECTED_MAIN = {
    "head": "7ef26d66b6ad671fdcc5e11bfa831699a39426bc",
    "branch": "main",
    "trackedCount": 59,
    "stagedCount": 0,
    "untrackedCount": 10937,
    "trackedSha256": "022f7387810c044d00254833c33c81d9f2c1205f15776e7b4407585ce4149c82",
    "stagedSha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "untrackedSha256": "c1c1c00968cadf25a549cd6776fe05676c1f7029dfa92759e26afea4adfc4730",
}
EXPECTED_PROBES = {
    "source_sha_mismatch", "schema_sha_mismatch", "after_staging", "during_objects",
    "after_corpus", "after_visual", "after_parity", "duplicate_surface_key",
    "missing_surface", "extra_surface", "unknown_field_or_type_without_disposition",
}


class AuditError(RuntimeError):
    """A fail-closed partial-audit generation error."""


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AuditError(f"DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def reject_constant(value: str) -> NoReturn:
    raise AuditError(f"UNSUPPORTED_JSON_CONSTANT:{value}")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_object, parse_constant=reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"JSON_READ_FAILED:{path}") from exc
    if not isinstance(value, dict):
        raise AuditError(f"JSON_NOT_OBJECT:{path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def write(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def markdown_table(values: list[tuple[str, Any]]) -> str:
    return "\n".join(f"| {key} | `{value}` |" for key, value in values)


def git_lines(repo: Path, values: list[str]) -> list[str]:
    completed = subprocess.run(["git", *values], cwd=repo, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise AuditError("GIT_COMMAND_FAILED:" + " ".join(values) + ":" + completed.stderr[-1000:])
    return completed.stdout.splitlines()


def collection_sha(lines: list[str]) -> str:
    if not lines:
        return hashlib.sha256(b"").hexdigest()
    return hashlib.sha256(("\n".join(sorted(lines)) + "\n").encode("utf-8")).hexdigest()


def protected_main() -> dict[str, Any]:
    repo = Path("/Users/jarlgiovanni/Desktop/modern_GD_history")
    tracked = git_lines(repo, ["diff", "--name-status"])
    staged = git_lines(repo, ["diff", "--cached", "--name-status"])
    untracked = git_lines(repo, ["ls-files", "--others", "--exclude-standard"])
    result = {
        "head": git_lines(repo, ["rev-parse", "HEAD"])[0],
        "branch": git_lines(repo, ["branch", "--show-current"])[0],
        "trackedCount": len(tracked), "stagedCount": len(staged), "untrackedCount": len(untracked),
        "trackedSha256": collection_sha(tracked), "stagedSha256": collection_sha(staged),
        "untrackedSha256": collection_sha(untracked),
    }
    # The protected worktree belongs to the user.  A later user-side change is
    # evidence to report, never a condition this recovery renderer may repair,
    # overwrite, or hide.  Keep the exact comparison so downstream receipts can
    # distinguish an unchanged protected main from an externally changed one.
    result["matchesInitial"] = result == EXPECTED_MAIN
    return result


def require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AuditError(f"CHECKPOINT_MISMATCH:{label}:{actual!r}!={expected!r}")


def validate_inputs(live: dict[str, Any], rollback: dict[str, Any], relocation: dict[str, Any], failure: dict[str, Any], recovery: dict[str, Any], cleanup: dict[str, Any], provenance: dict[str, Any]) -> None:
    require_equal(live.get("status"), "PERFORMANCE_BLOCKED_LIVE_SNAPSHOT", "live.status")
    require_equal(live.get("expectedSchemaSha256"), EXPECTED_SCHEMA, "live.schema")
    require_equal(live.get("candidateJsonSha256"), EXPECTED_CANDIDATE, "live.candidate")
    require_equal(rollback.get("status"), "PASS", "rollback.status")
    require_equal(rollback.get("schemaSha256"), EXPECTED_SCHEMA, "rollback.schema")
    database = rollback.get("database")
    if not isinstance(database, dict):
        raise AuditError("ROLLBACK_DATABASE_MISSING")
    for key in ("projectTableTotalRows", "migrationBatchRows", "researchCurrentPointers", "visualCurrentPointers", "researchSealedReleases", "visualSealedReleases"):
        require_equal(database.get(key), 0, "rollback." + key)
    require_equal(database.get("otherClientSessions"), [], "rollback.client_sessions")
    require_equal(rollback.get("forbiddenImportProcesses"), [], "rollback.import_processes")
    require_equal(rollback.get("staging", {}).get("descriptorCount"), 35, "rollback.descriptors")
    require_equal(rollback.get("staging", {}).get("descriptorRehash"), "PASS", "rollback.descriptor_rehash")
    require_equal(relocation.get("status"), "PASS", "relocation.status")
    require_equal(relocation.get("before", {}).get("descriptorCount"), 35, "relocation.before_count")
    require_equal(relocation.get("after", {}).get("descriptorCount"), 35, "relocation.after_count")
    require_equal(relocation.get("before", {}).get("descriptors"), relocation.get("after", {}).get("descriptors"), "relocation.descriptor_identity")
    require_equal(relocation.get("sourceVerifiedAbsent"), True, "relocation.source_absent")
    require_equal(failure.get("status"), "PASS", "failure.status")
    probes = failure.get("probes")
    if not isinstance(probes, dict) or set(probes) != EXPECTED_PROBES:
        raise AuditError("FAILURE_PROBE_SET_INVALID")
    for name, probe in probes.items():
        if not isinstance(probe, dict) or not isinstance(probe.get("exitCode"), int) or probe["exitCode"] == 0:
            raise AuditError("FAILURE_PROBE_EXIT_INVALID:" + name)
        for key, expected in (("partialImportResidue", 0), ("currentPointerAdvanced", False), ("releaseSealed", False)):
            require_equal(probe.get(key), expected, f"failure.{name}.{key}")
    require_equal(recovery.get("status"), "PASS", "recovery.status")
    require_equal(cleanup.get("status"), "PASS", "cleanup.status")
    require_equal(cleanup.get("database", {}).get("dropped"), True, "cleanup.database")
    require_equal(cleanup.get("cluster", {}).get("stopped"), True, "cleanup.stopped")
    require_equal(cleanup.get("cluster", {}).get("deleted"), True, "cleanup.deleted")
    require_equal(cleanup.get("taskOwnedPostgresProcesses"), 0, "cleanup.postgres")
    require_equal(cleanup.get("taskOwnedImporterProcesses"), 0, "cleanup.importer")
    require_equal(provenance.get("stageManifestSha256"), relocation.get("after", {}).get("manifestSha256"), "provenance.relocation_manifest")


def copy_evidence(output: Path, inputs: list[tuple[str, Path]]) -> None:
    evidence = output / "evidence"
    evidence.mkdir(exist_ok=True)
    for name, source in inputs:
        destination = evidence / name
        # Re-rendering commonly receives already-archived immutable evidence.
        # Avoid SameFileError while retaining exactly those bytes in place.
        if source.resolve() != destination.resolve():
            shutil.copyfile(source, destination)


def render(output: Path, live: dict[str, Any], rollback: dict[str, Any], relocation: dict[str, Any], failure: dict[str, Any], recovery: dict[str, Any], cleanup: dict[str, Any], provenance: dict[str, Any], protected: dict[str, Any]) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    activity = live["postgres"]["activity"]
    backend = activity["backend"]
    stats = activity["statistics"]
    initial_sample = {
        "capturedAtUtc": "2026-08-14T10:44:34Z",
        "backendPid": 50121,
        "elapsed": "01-06:36:23",
        "cpuTime": "96:53.37",
        "state": "Rs",
        "cpuPercent": "2.1",
        "source": "controller bounded-window baseline captured from the resolved task-owned backend",
    }
    final_sample = {
        "capturedAtUtc": live["capturedAtUtc"],
        "backendPid": backend["pid"],
        "elapsed": live["postgres"]["backend"]["ps"].split()[5],
        "cpuTime": live["postgres"]["backend"]["ps"].split()[6],
        "state": live["postgres"]["backend"]["ps"].split()[4],
        "cpuPercent": live["postgres"]["backend"]["ps"].split()[7],
        "databaseStats": stats,
    }
    gate = [
        "PHASE_STATUS=PARTIAL_PERFORMANCE_BLOCKED",
        "PHASE2B_REHEARSAL_COMPLETE=false",
        "RECOVERY_CHECKPOINT_CREATED=true",
        "STAGING_BUNDLE_VERIFIED=true",
        "STAGING_DESCRIPTOR_FILES_VERIFIED=35",
        "FAILURE_PROBES_PASSED=11/11",
        "FRESH_REPLAY_A_STARTED=true",
        "FRESH_REPLAY_A_COMMITTED=false",
        "FRESH_REPLAY_A_ROLLED_BACK=true",
        "FRESH_POPULATION_REPLAY_COUNT=0",
        "PERFORMANCE_GATE=FAIL",
        "PERFORMANCE_BLOCKING_STAGE=SET_CONSTRAINTS_ALL_IMMEDIATE",
        "DEFERRED_VALIDATION_COMPLETED=false",
        "PARTIAL_IMPORT_RESIDUE=0",
        "MIGRATION_BATCH_RESIDUE=0",
        "CURRENT_POINTER_COUNT=0",
        "SEALED_RELEASE_COUNT=0",
        "SCHEMA_HASH_DETERMINISTIC=true",
        "DATABASE_POPULATION_PARITY_VERIFIED=false",
        "POPULATION_CONTENT_HASH_DETERMINISTIC=false",
        "PUBLIC_BOUNDARY_VERIFIED=false",
        "PRODUCTION_ROW_COUNT=0",
        "DATABASE_POPULATED=false",
        "PRODUCTION_MIGRATION_EXECUTED=false",
        "FREEZE_READY=false",
        "PROMOTION_READY=false",
        "DEPLOYMENT_READY=false",
    ]
    write(output / "00_EXECUTIVE_RECEIPT.md", "# v49 Phase 2B recovery checkpoint\n\nThe bounded Fresh A completion window expired inside deferred PostgreSQL validation. The transaction was cancelled only after a live checkpoint, rolled back with zero durable project rows, and no Fresh B was started. The verified staging bundle is preserved outside Git for a separately authorized performance remediation.\n\n```text\n" + "\n".join(gate) + "\n```\n\n| Evidence | Value |\n|---|---|\n" + markdown_table([("performance checkpoint", live["capturedAtUtc"]), ("rollback checkpoint", rollback["capturedAtUtc"]), ("cache destination", relocation["after"]["realpath"]), ("cleanup", cleanup["cleanedAtUtc"]), ("package generated", now)]))
    write(output / "01_INPUT_AND_SCHEMA_PIN_RECEIPT.md", "# Input and schema pins\n\n```text\nIMPLEMENTATION_BASE_COMMIT=" + EXPECTED_BASE + "\nEXPECTED_SCHEMA_SHA256=" + EXPECTED_SCHEMA + "\nCANDIDATE_JSON_SHA256=" + EXPECTED_CANDIDATE + "\nSCHEMA_SHA_BEFORE=" + EXPECTED_SCHEMA + "\nSCHEMA_SHA_AFTER=" + rollback["schemaSha256"] + "\nSCHEMA_DRIFT=0\nCANONICAL_POPULATION_INPUT_ARTIFACTS=1\n```\n\nThe 35-file staging bundle was descriptor-rehashed before and after an atomic same-filesystem move; no frozen input or Phase 2A migration was modified.")
    write(output / "05_STAGING_AND_TRANSACTION_RECEIPT.md", "# Staging and transaction receipt\n\n```text\nSTAGING_BUNDLE_VERIFIED=true\nSTAGING_DESCRIPTOR_FILES_VERIFIED=35\nSTAGING_MANIFEST_SHA256=" + relocation["after"]["manifestSha256"] + "\nSTAGING_CACHE=" + relocation["after"]["realpath"] + "\nFRESH_A_TRANSACTION_STARTED=true\nFRESH_A_TRANSACTION_COMMITTED=false\nFRESH_A_TRANSACTION_ROLLED_BACK=true\n```\n\nThe bulk staging directory was not recommputed. The reusable cache is outside the repository and its source task-temp path was verified absent only after the destination rehash passed.")
    write(output / "06_OBJECT_PARITY_RECEIPT.md", "# Object parity\n\nNo successful population replay completed. Therefore 15,923 object parity is **not verified**. The cancelled Fresh A database has zero durable project rows, not a partial 15,923-row population.\n\n```text\nOPERATIONAL_ARCHIVE_OBJECTS_VERIFIED=false\nPARTIAL_IMPORT_RESIDUE=0\n```")
    write(output / "07_RESEARCH_HELD_DISPOSITION_RECEIPT.md", "# Research and held disposition\n\nThe staged baseline remains pinned at `7995/2971/4957` and `7995/7928`, but no committed database replay exists. Corpus/held parity therefore remains unverified, not inferred from staging.\n\n```text\nRESEARCH_ELIGIBLE_OBJECTS_VERIFIED=false\nHELD_OBJECTS_VERIFIED=false\nREJECTED_OBJECTS_VERIFIED=false\n```")
    write(output / "08_SQLITE_RECONCILIATION_RECEIPT.md", "# SQLite reconciliation\n\nThe completed reconciliation report is preserved as evidence. SQLite was used only in its locked read-only reconciliation mode; it created no canonical rows or backfilled fields. This recovery checkpoint does not rerun it.\n\n```text\nSQLITE_CANONICAL_WRITES=0\nSQLITE_BACKFILLED_ROWS=0\nSQLITE_BACKFILLED_FIELDS=0\n```")
    write(output / "09_DERIVED_ASSET_EXCLUSION_RECEIPT.md", "# Derived asset exclusion\n\nCandidate JSON remains the sole population input. SQLite, Search, transfer, TRACE, raw-audit, and rights-audit assets remain reconciliation/integrity-only. No Fresh A data persisted.\n\n```text\nSEARCH_IMPORTED_ROWS=0\nSEARCH_ONLY_CANONICAL_INSERTS=0\nTRACE_IMPORTED_CANONICAL_ROWS=0\nRIGHTS_AUDIT_PERMISSION_UPGRADES=0\n```")
    write(output / "10_TRACE_ZERO_IMPORT_RECEIPT.md", "# TRACE zero import\n\nNo committed Phase 2B population exists after rollback. The recovery checkpoint records zero durable semantic relations and zero release projections; it does not claim a successful TRACE migration.\n\n```text\nACCEPTED_TRACE_RELATIONS=0\nTRACE_PROJECTION_EDGES=0\nTRACE_ELIGIBLE_OBJECTS=0\n```")
    write(output / "11_VISUAL_ZERO_RIGHTS_RECEIPT.md", "# Visual zero-rights state\n\nThe staging baseline remains fail-closed, but database parity was not committed. No positive-rights or remote-image outcome exists in the rolled-back database.\n\n```text\nPOSITIVE_RIGHTS_COUNT=0\nREMOTE_IMAGE_DECISIONS=0\nPUBLIC_PIXEL_LOCATORS=0\n```")
    write(output / "12_CONTENT_HASH_AND_REPLAY_RECEIPT.md", "# Fresh replay and content hash\n\nFresh A entered `SET CONSTRAINTS ALL IMMEDIATE` but did not commit; Fresh B was never created. A population content hash would misrepresent an uncommitted transaction, so none is issued.\n\n```text\nFRESH_POPULATION_REPLAY_COUNT=0\nFRESH_A_STARTED=true\nFRESH_A_COMMITTED=false\nFRESH_B_STARTED=false\nPOPULATION_CONTENT_HASH_DETERMINISTIC=false\n```")
    write(output / "13_FAILURE_INJECTION_AND_ROLLBACK_RECEIPT.md", "# Failure probes and rollback\n\nAll eleven persisted negative probes passed before Fresh A. The recovery rollback is an additional bounded cancellation test, independently proving zero rows, zero batch, zero pointers, and zero seals.\n\n```text\nFAILURE_PROBES_PASSED=11/11\nRUNTIME_FAILURE_MARKERS=5\nDURABLE_PROJECT_ROWS_AFTER_CANCEL=0\nMIGRATION_BATCH_RESIDUE=0\nCURRENT_POINTER_COUNT=0\nSEALED_RELEASE_COUNT=0\n```\n\nThe machine-readable reports are in `evidence/`.")
    write(output / "14_PUBLIC_BOUNDARY_RECEIPT.md", "# Public boundary\n\nThe required populated public-boundary fixture was not run because Fresh A did not commit and Fresh B is prohibited this round. Phase 2A boundaries remain schema-verified only; this Phase 2B gate is false.\n\n```text\nPUBLIC_BOUNDARY_VERIFIED=false\nTEST_FIXTURE_RESIDUE=0\n```")
    write(output / "15_PROCESS_AND_RESOURCE_RECEIPT.md", "# Process and resource receipt\n\n```json\n" + json.dumps(cleanup, sort_keys=True, indent=2) + "\n```\n\nThe staging bundle was moved before cluster disposal and remains at the explicitly recorded cache path. The source staging path and task-owned cluster root were both verified absent.")
    write(output / "16_DEFERRED_DECISIONS.md", "# Deferred decisions\n\n- Do not start Fresh B from this recovery branch.\n- Do not rerun extraction, reconciliation, or the eleven completed failure probes.\n- Resume only after separately authorized performance remediation for the deferred validation tail; Phase 2A historical DDL must not be edited.\n- Reuse only the cached staging bundle after rehashing all 35 descriptors and validating its manifest binding.\n- A later successful run still requires two fresh committed populations, content-hash comparison, idempotency, public-role fixture, and a new final audit package.")
    write(output / "17_PHASE2B_GATE_RECEIPT.md", "# Phase 2B performance gate\n\n```text\n" + "\n".join(gate) + "\n```")
    write(output / "18_PERFORMANCE_BLOCK_RECEIPT.md", "# Performance block checkpoint\n\nThe backend was live but operationally unhealthy: it remained in one `SET CONSTRAINTS ALL IMMEDIATE` invocation beyond the bounded completion window. Liveness counters were not treated as completion evidence.\n\n## Bounded-window record\n\n```text\nWINDOW_BASELINE_UTC=2026-08-14T10:44:34Z\nWINDOW_DEADLINE_UTC=2026-08-14T10:54:34Z\nLIVE_SNAPSHOT_CAPTURED_AT_UTC=" + live["capturedAtUtc"] + "\nWINDOW_RESULT=INCOMPLETE\n```\n\nThe additional checkpoint-capture interval is recorded as controller overhead, not as an extension or a successful completion. No Fresh B was started; the resolved backend was cancelled after the live snapshot and its transaction was subsequently proved rolled back.\n\n## CPU and database samples\n\n```json\n" + json.dumps({"initial": initial_sample, "final": final_sample}, sort_keys=True, indent=2) + "\n```\n\n## Resolved transaction\n\n```json\n" + json.dumps({"backend": backend, "locks": activity["locks"], "temporaryDiskKiB": live["temporaryDiskKiB"], "serverLog": live["serverLog"], "runtimeLog": live["runtimeLog"]}, sort_keys=True, indent=2) + "\n```\n\nAt the hard stop, `pg_cancel_backend` was invoked only for the resolved task-owned backend. The runner then exited nonzero and the post-cancel read-only verifier proved atomic rollback.")
    write(output / "19_RECOVERY_RESUME_INSTRUCTIONS.md", "# Resume instructions\n\n1. Start from this recovery branch and do not treat it as a Phase 2B PASS.\n2. Validate the cache at `" + relocation["after"]["realpath"] + "` against its manifest and all 35 descriptors before any PostgreSQL connection.\n3. Do not rerun the extractor, reconciliation program, or completed failure probes.\n4. Obtain separate authorization for a forward-only performance remedy; the blocking stage is `SET CONSTRAINTS ALL IMMEDIATE`, and Phase 2A historical migrations/roles/functions are frozen.\n5. Use a new disposable cluster and Fresh A only after that remedy is reviewed. Fresh B must follow only after Fresh A commits and proves all parity gates.\n6. Preserve the evidence in this package, especially `evidence/performance-live.json`, `evidence/performance-rollback.json`, and `evidence/staging-relocation.json`.")
    protected_current_matches_initial = bool(protected["matchesInitial"])
    d9_receipt = output / "agents" / "D9_INDEPENDENT_PERFORMANCE_FINAL_VERIFIER.md"
    historical_external_change = (
        d9_receipt.is_file()
        and "PROTECTED_MAIN_FINGERPRINT_UNCHANGED=false" in d9_receipt.read_text(encoding="utf-8")
    )
    protected_invariant = protected_current_matches_initial and not historical_external_change
    protected_note = (
        "The protected dirty main was read only and its current fingerprints match the recorded baseline."
        if protected_current_matches_initial else
        "The protected dirty main was read only, but its current fingerprint differs from the recorded baseline."
    )
    write(output / "20_GIT_AND_PROTECTED_MAIN_RECEIPT.md", "# Git and protected-main receipt\n\n```text\nTARGET_START_HEAD=" + EXPECTED_BASE + "\nTARGET_RECOVERY_BRANCH=recovery/v49-phase2b-performance-checkpoint-20260814\nPROTECTED_MAIN_HEAD_BEFORE=" + EXPECTED_MAIN["head"] + "\nPROTECTED_MAIN_HEAD_CURRENT=" + protected["head"] + "\nPROTECTED_MAIN_TRACKED_SHA256_BEFORE=" + EXPECTED_MAIN["trackedSha256"] + "\nPROTECTED_MAIN_TRACKED_SHA256_CURRENT=" + protected["trackedSha256"] + "\nPROTECTED_MAIN_UNTRACKED_SHA256_BEFORE=" + EXPECTED_MAIN["untrackedSha256"] + "\nPROTECTED_MAIN_UNTRACKED_SHA256_CURRENT=" + protected["untrackedSha256"] + "\nPROTECTED_MAIN_CURRENT_MATCHES_INITIAL=" + str(protected_current_matches_initial).lower() + "\nPROTECTED_MAIN_FINGERPRINT_INVARIANT=" + str(protected_invariant).lower() + "\nPROTECTED_MAIN_EXTERNAL_CHANGE_OBSERVED=" + str(historical_external_change or not protected_current_matches_initial).lower() + "\nPROTECTED_MAIN_CONTROLLER_WRITES=0\n```\n\n" + protected_note + " Independent verifier D9 is retained as the authoritative record of any observed external protected-main change; no restore, stash, reset, checkout, or write was attempted.")
    agents = [("D1", "Candidate mapping review", "PASS"), ("D2", "Semantics/reconciliation review", "PASS"), ("D3", "schema/import review", "PASS"), ("D4", "atomicity review", "PASS"), ("D5", "mapping contract review", "PASS"), ("D6", "reconciliation implementation", "PASS"), ("D7", "final static import review", "PASS"), ("D8", "recovery audit/package review", "PASS"), ("D9", "independent performance final verifier", "FAIL: protected-main external fingerprint change"), ("ROOT", "single-controller recovery, cancellation, preservation, cleanup", "PARTIAL_PERFORMANCE_BLOCKED")]
    lines = ["# Agent task register", "", "| Agent | Scope | Status |", "|---|---|---|"]
    lines.extend(f"| {code} | {scope} | {status} |" for code, scope, status in agents)
    write(output / "AGENT_TASK_REGISTER.md", "\n".join(lines))


def manifest_and_checksums(output: Path) -> None:
    files = []
    for path in sorted(output.rglob("*")):
        if not path.is_file() or path.name in {"MANIFEST.json", "CHECKSUMS.sha256"}:
            continue
        files.append({"path": path.relative_to(output).as_posix(), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    manifest = {
        "schema": "gda-v49-phase2b-performance-block-audit-manifest/v1",
        "phase": "v49-phase2b-performance-blocked-recovery",
        "status": "PARTIAL_PERFORMANCE_BLOCKED",
        "implementationBaseCommit": EXPECTED_BASE,
        "expectedSchemaSha256": EXPECTED_SCHEMA,
        "candidateJsonSha256": EXPECTED_CANDIDATE,
        "files": files,
        "checksumScope": "all audit-package files except CHECKSUMS.sha256; MANIFEST.json is included in CHECKSUMS but not self-hashed here",
    }
    (output / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    checksum_paths = sorted(path for path in output.rglob("*") if path.is_file() and path.name != "CHECKSUMS.sha256")
    (output / "CHECKSUMS.sha256").write_text("\n".join(f"{sha256_file(path)}  {path.relative_to(output).as_posix()}" for path in checksum_paths) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--live", type=Path, required=True)
    parser.add_argument("--rollback", type=Path, required=True)
    parser.add_argument("--relocation", type=Path, required=True)
    parser.add_argument("--failure", type=Path, required=True)
    parser.add_argument("--recovery", type=Path, required=True)
    parser.add_argument("--reconcile", type=Path, required=True)
    parser.add_argument("--cleanup", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    live = read_json(args.live.resolve())
    rollback = read_json(args.rollback.resolve())
    relocation = read_json(args.relocation.resolve())
    failure = read_json(args.failure.resolve())
    recovery = read_json(args.recovery.resolve())
    reconcile = read_json(args.reconcile.resolve())
    cleanup = read_json(args.cleanup.resolve())
    provenance = read_json(output / "STAGING_PROVENANCE.json")
    validate_inputs(live, rollback, relocation, failure, recovery, cleanup, provenance)
    if reconcile.get("status") != "PASS" or reconcile.get("errors") not in ([], None):
        raise AuditError("RECONCILIATION_REPORT_INVALID")
    protected = protected_main()
    copy_evidence(output, [
        ("performance-live.json", args.live.resolve()),
        ("performance-rollback.json", args.rollback.resolve()),
        ("staging-relocation.json", args.relocation.resolve()),
        ("failure-injections.json", args.failure.resolve()),
        ("recovery-checkpoint.json", args.recovery.resolve()),
        ("reconcile.json", args.reconcile.resolve()),
        ("process-cleanup.json", args.cleanup.resolve()),
    ])
    render(output, live, rollback, relocation, failure, recovery, cleanup, provenance, protected)
    manifest_and_checksums(output)
    print(json.dumps({"status": "PASS", "phaseStatus": "PARTIAL_PERFORMANCE_BLOCKED", "output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AuditError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
