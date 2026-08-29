#!/usr/bin/env python3
"""Independently verify the Round 16B final clean-reproduction receipt.

The verifier is intentionally standalone: it neither imports nor invokes the
primary builder.  It rehashes every explicit input, reconstructs the closure
boundary and headline counts from governed artifacts, independently reconciles
the database and HTTP evidence, and runs fail-closed mutation controls against
closure inflation and prohibited Checkpoint 016 self-reference.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Iterable


SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
PUBLISHED_CP15_SHA = "d40ec811c2b60cfcbf6892ba79741d2ee0fec95b"
PUBLISHED_CP15_TREE = "9c08c85efcbc4fd4ce88c3c880c3e3e053f36b65"
EXPECTED_ORIGIN_MAIN_SHA = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e"
WORK_BRANCH = "codex/trace-v49-exploration-higher-order-association-closure-round16b"
CP15_PUBLICATION_RECEIPT_SHA256 = (
    "29f5459ad360dde3bf94df45783992968694987f06e2dfd52d02ccb93c69379b"
)

PRIMARY_SCHEMA = "trace-round16b-final-clean-reproduction-prepublication-checkpoint016/v1"
SCHEMA = "trace-round16b-final-clean-reproduction-independent-verification-checkpoint016/v1"
VERIFIER_VERSION = "trace-round16b-final-clean-reproduction-independent-verifier-v1"
DB_SCHEMA = "trace-round16b-v50-database-reproduction-checkpoint016/v1"
DB_INDEPENDENT_SCHEMA = (
    "trace-round16b-v50-database-reproduction-independent-verification-checkpoint016/v1"
)

CLOSURE_KEYS = (
    "pair_association_closure",
    "higher_order_association_closure",
    "global_composition_coherence_closure",
    "product_association_reachability_closure",
    "computational_space_closure",
    "function3_closure",
)
EXPECTED_CLOSURE = {key: False for key in CLOSURE_KEYS}
EXPECTED_COUNTS = {
    "unresolved_association_count": 11,
    "active_pending_review_count": 0,
    "known_unexplained_exclusion_count": 9,
    "universe_wide_unexplained_exclusion_count": "INDETERMINATE",
    "active_noncomposable_vocabulary_count": 5,
}
EXPECTED_GOVERNANCE = {
    "forcePushUsed": False,
    "historyRewritten": False,
    "rollbackTagPushed": False,
    "deploymentPerformed": False,
    "originMainRewritten": False,
    "publicExistingHistoryRewritten": False,
    "productionDataImported": False,
    "productionActivationPerformed": False,
    "mainUpdated": False,
    "autoMergePathOpened": False,
}
EXPECTED_NORMALIZED_SCHEMA_SHA256 = (
    "1152a494e6b64595c9f9291c1d314a9434cb763c7f2a02512d2768e286f571b4"
)
EXPECTED_NORMALIZED_SCHEMA_BYTES = 1_090_058
EXPECTED_RACE_CHECKSUMS_SHA256 = (
    "595efb06ae1508b3f2cf952e3d0f1af2e9bd70b12bd4fcde93a530b3b70442ab"
)
EXPECTED_READ_MODEL_SHA256 = (
    "f1ae8a35895b27c15fb3d9b42828b8611633ee8ee7e2cbc825772b590304351b"
)
EXPECTED_HTTP_PHASES = {
    "ARTIFACT_CHECK": 1,
    "CONCURRENCY_C1": 100,
    "CONCURRENCY_C5": 100,
    "CONCURRENCY_C10": 100,
    "CONCURRENCY_C25": 100,
    "CONCURRENCY_C50": 100,
    "CONTROL_EXPORT_REPLAY_POSTLOAD": 2,
    "CONTROL_EXPORT_REPLAY_PRELOAD": 5,
    "FUNCTIONAL_HTTP": 160,
    "SUSTAINED_READ": 500,
}
FORBIDDEN_SELF_REFERENCE_KEYS = {
    "finalLocalSha",
    "finalRemoteSha",
    "checkpoint016Commit",
    "checkpoint016RemoteCommit",
    "final_local_sha",
    "final_remote_sha",
}


class VerificationError(RuntimeError):
    """A stable fail-closed independent-verification error."""


def enforce(condition: bool, code: str) -> None:
    if not condition:
        raise VerificationError(code)


def require_dict(value: Any, code: str) -> dict[str, Any]:
    enforce(isinstance(value, dict), code)
    return value


def require_list(value: Any, code: str) -> list[Any]:
    enforce(isinstance(value, list), code)
    return value


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise VerificationError(f"JSON_DUPLICATE_KEY:{path}:{key}")
            result[key] = value
        return result

    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"JSON_READ_FAILURE:{path}:{exc}") from exc


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, dialect="excel-tab")
            fields = reader.fieldnames or []
            enforce(bool(fields) and len(fields) == len(set(fields)), f"TSV_FIELDS:{path}")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VerificationError(f"TSV_READ_FAILURE:{path}:{exc}") from exc
    enforce(all(None not in row for row in rows), f"TSV_MALFORMED_ROW:{path}")
    return fields, rows


def resolve_path(repo: Path, value: str) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = repo / candidate
    return candidate.resolve()


def path_hint(repo: Path, path: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return f"external/{path.name}"


def file_descriptor(repo: Path, path: Path) -> dict[str, Any]:
    enforce(path.is_file(), f"INPUT_NOT_FILE:{path}")
    return {
        "path": path_hint(repo, path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def directory_descriptor(repo: Path, directory: Path) -> dict[str, Any]:
    enforce(directory.is_dir(), f"INPUT_NOT_DIRECTORY:{directory}")
    entries = [
        {
            "path": path.relative_to(directory).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(item for item in directory.rglob("*") if item.is_file())
    ]
    enforce(bool(entries), f"EMPTY_INPUT_DIRECTORY:{directory}")
    return {
        "path": path_hint(repo, directory),
        "fileCount": len(entries),
        "aggregateSha256": sha256_bytes(canonical_json_bytes(entries)),
        "files": entries,
    }


def recursive_values(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        for child in value.values():
            yield child
            yield from recursive_values(child)
    elif isinstance(value, list):
        for child in value:
            yield child
            yield from recursive_values(child)


def recursive_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from recursive_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from recursive_keys(child)


def find_key_values(value: Any, accepted: set[str]) -> list[Any]:
    normalized = {item.casefold().replace("_", "") for item in accepted}
    found: list[Any] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold().replace("_", "") in normalized:
                found.append(child)
            found.extend(find_key_values(child, accepted))
    elif isinstance(value, list):
        for child in value:
            found.extend(find_key_values(child, accepted))
    return found


def false_closure(value: Any, code: str) -> dict[str, bool]:
    mapping = require_dict(value, code)
    enforce(mapping == EXPECTED_CLOSURE, code)
    return EXPECTED_CLOSURE.copy()


def reconstruct_closure(
    metrics: dict[str, Any],
    independent: dict[str, Any],
    semantic: dict[str, Any],
    runtime: dict[str, Any],
    round16a: dict[str, Any],
    round16a_independent: dict[str, Any],
) -> dict[str, Any]:
    enforce(metrics.get("status") == "PASS_EVIDENCE_BOUNDED_NONCLOSURE", "METRICS_STATUS")
    false_closure(metrics.get("closure"), "METRICS_CLOSURE")
    hypotheses = require_dict(metrics.get("hypotheses"), "METRICS_HYPOTHESES")
    universe = require_dict(metrics.get("candidate_universe"), "METRICS_UNIVERSE")
    vocabulary = require_dict(metrics.get("vocabulary_reachability"), "METRICS_VOCABULARY")
    counts = {
        "unresolved_association_count": hypotheses.get("unresolved_association_count"),
        "active_pending_review_count": hypotheses.get("active_pending_review_count"),
        "known_unexplained_exclusion_count": universe.get("known_unexplained_exclusion_count"),
        "universe_wide_unexplained_exclusion_count": universe.get("universe_wide_unexplained_exclusion_count"),
        "active_noncomposable_vocabulary_count": vocabulary.get("active_noncomposable_vocabulary_count"),
    }
    enforce(counts == EXPECTED_COUNTS, "METRICS_HEADLINE_COUNTS")
    enforce(universe.get("candidate_universe_closure") is False, "METRICS_UNIVERSE_CLOSURE")

    enforce(independent.get("status") == "PASS_FOR_EVIDENCE_BOUNDED_NONCLOSURE_DECISION", "METRICS_INDEPENDENT_STATUS")
    false_closure(independent.get("closure"), "METRICS_INDEPENDENT_CLOSURE")
    independent_metrics = require_dict(independent.get("independent_metrics"), "METRICS_INDEPENDENT_COUNTS")
    for key, expected in EXPECTED_COUNTS.items():
        enforce(independent_metrics.get(key) == expected, f"METRICS_INDEPENDENT_COUNT:{key}")
    enforce(independent.get("check_count") == 25, "METRICS_INDEPENDENT_CHECKS")
    enforce(independent.get("adversarial_probe_count") == 48, "METRICS_INDEPENDENT_PROBES")

    enforce(semantic.get("status") == "PASS", "SEMANTIC_STATUS")
    false_closure(semantic.get("closure_flags"), "SEMANTIC_CLOSURE")
    enforce(semantic.get("check_count") == 798, "SEMANTIC_CHECKS")
    enforce(runtime.get("status") == "PASS", "RUNTIME_STATUS")
    enforce(runtime.get("check_count") == 15, "RUNTIME_CHECKS")
    enforce(round16a.get("status") == "PASS_WITH_OPEN_CLOSURE_BLOCKERS", "ROUND16A_STATUS")
    false_closure(round16a.get("closure"), "ROUND16A_CLOSURE")
    enforce(round16a_independent.get("status") == "PASS_WITH_OPEN_CLOSURE_BLOCKERS", "ROUND16A_INDEPENDENT_STATUS")
    enforce(round16a_independent.get("closure_flags_true_count") == 0, "ROUND16A_INDEPENDENT_CLOSURE_COUNT")
    enforce(round16a_independent.get("check_count") == 143165, "ROUND16A_INDEPENDENT_CHECKS")
    return {
        "closure": EXPECTED_CLOSURE.copy(),
        "headlineCounts": counts,
        "closureIndependentStatus": independent.get("status"),
        "closureIndependentCheckCount": 25,
        "closureIndependentAdversarialProbeCount": 48,
        "semanticIndependentCheckCount": 798,
        "runtimeIndependentCheckCount": 15,
        "round16aIndependentCheckCount": 143165,
    }


def reconstruct_database(primary: dict[str, Any], independent: dict[str, Any], primary_sha: str) -> dict[str, Any]:
    enforce(primary.get("schema") == DB_SCHEMA, "DB_SCHEMA")
    enforce(primary.get("status") == "PASS", "DB_STATUS")
    enforce(primary.get("checkpoint") in {16, "CHECKPOINT-016"}, "DB_CHECKPOINT")
    authority = require_dict(primary.get("authority"), "DB_AUTHORITY")
    enforce(authority.get("sourceCommit") == PUBLISHED_CP15_SHA, "DB_COMMIT")
    enforce(authority.get("sourceTree") == PUBLISHED_CP15_TREE, "DB_TREE")
    enforce(authority.get("repositoryClean") is True, "DB_CLEAN")
    native = require_dict(primary.get("sourceNative"), "DB_NATIVE")
    enforce(native.get("compatibilityAdapterUsed") is False, "DB_ADAPTER")
    enforce(native.get("nativeVerifierExecuted") is True, "DB_NATIVE_VERIFIER")
    enforce(native.get("fullManifestStatus") == "PASS", "DB_MANIFEST")
    enforce(native.get("preflightStatus") == "PASS", "DB_PREFLIGHT")

    databases = require_list(primary.get("databases"), "DB_DATABASES")
    enforce(len(databases) == 2, "DB_COUNT")
    names: set[str] = set()
    owners: set[str] = set()
    for ordinal, value in enumerate(databases, 1):
        database = require_dict(value, f"DB_DATABASE:{ordinal}")
        names.add(str(database.get("database", "")))
        owners.add(str(database.get("owner", "")))
        dump = require_dict(database.get("schemaDump"), f"DB_DUMP:{ordinal}")
        enforce(dump.get("normalizedSha256") == EXPECTED_NORMALIZED_SCHEMA_SHA256, f"DB_DUMP_HASH:{ordinal}")
        enforce(dump.get("normalizedBytes") == EXPECTED_NORMALIZED_SCHEMA_BYTES, f"DB_DUMP_BYTES:{ordinal}")
        race = require_dict(database.get("raceEvidence"), f"DB_RACE:{ordinal}")
        enforce(race.get("checksumsSha256") == EXPECTED_RACE_CHECKSUMS_SHA256, f"DB_RACE_HASH:{ordinal}")
        enforce(race.get("fileCount") == 12, f"DB_RACE_COUNT:{ordinal}")
        enforce(len(require_dict(race.get("perFileSha256"), f"DB_RACE_FILES:{ordinal}")) == 12, f"DB_RACE_FILE_COUNT:{ordinal}")
    enforce(len(names) == 2 and "" not in names, "DB_NAMES")
    enforce(len(owners) == 1 and "" not in owners, "DB_OWNERS")

    reconciliation = require_dict(primary.get("reconciliation"), "DB_RECONCILIATION")
    expected_reconciliation = {
        "databaseCount": 2,
        "normalizedSchemasIdentical": True,
        "normalizedSchemaSha256": EXPECTED_NORMALIZED_SCHEMA_SHA256,
        "normalizedSchemaBytes": EXPECTED_NORMALIZED_SCHEMA_BYTES,
        "raceChecksumLedgersIdentical": True,
        "raceChecksumsSha256": EXPECTED_RACE_CHECKSUMS_SHA256,
        "raceDatabaseResidueCount": 0,
    }
    for key, expected in expected_reconciliation.items():
        enforce(reconciliation.get(key) == expected, f"DB_RECONCILIATION:{key}")
    governance = require_dict(primary.get("governance"), "DB_GOVERNANCE")
    enforce(governance.get("cleanSelfContainedReproduction") is True, "DB_SELF_CONTAINED")
    enforce(governance.get("sourceNativeManifestPreflight") is True, "DB_SOURCE_NATIVE")
    enforce(governance.get("compatibilityAdapterUsed") is False, "DB_GOVERNANCE_ADAPTER")
    for key in ("productionDataImported", "productionActivationPerformed", "deploymentPerformed"):
        enforce(governance.get(key) is False, f"DB_GOVERNANCE:{key}")

    enforce(independent.get("schema") == DB_INDEPENDENT_SCHEMA, "DB_INDEPENDENT_SCHEMA")
    enforce(independent.get("status") == "PASS", "DB_INDEPENDENT_STATUS")
    reference = require_dict(independent.get("primaryReceipt"), "DB_INDEPENDENT_PRIMARY")
    enforce(reference.get("sha256") == primary_sha, "DB_INDEPENDENT_PRIMARY_HASH")
    controls = require_dict(independent.get("adversarialControls"), "DB_INDEPENDENT_CONTROLS")
    enforce(int(controls.get("controlCount", 0)) > 0, "DB_INDEPENDENT_CONTROL_COUNT")
    enforce(controls.get("failureCount") == 0, "DB_INDEPENDENT_CONTROL_FAILURE")
    comparison = require_dict(independent.get("comparison"), "DB_INDEPENDENT_COMPARISON")
    enforce(comparison.get("mismatchCount") == 0 and comparison.get("mismatches") == [], "DB_INDEPENDENT_MISMATCH")
    return {
        "status": "PASS",
        "independentStatus": "PASS",
        "databaseCount": 2,
        "databaseNames": sorted(names),
        "ownerCount": 1,
        "normalizedSchemaSha256": EXPECTED_NORMALIZED_SCHEMA_SHA256,
        "normalizedSchemaBytes": EXPECTED_NORMALIZED_SCHEMA_BYTES,
        "raceChecksumsSha256": EXPECTED_RACE_CHECKSUMS_SHA256,
        "compatibilityAdapterUsed": False,
        "cleanSelfContainedReproduction": True,
    }


def reconstruct_http(directory: Path, independent: dict[str, Any]) -> dict[str, Any]:
    summary_path = directory / "verification-summary.json"
    summary = require_dict(read_json(summary_path), "HTTP_SUMMARY")
    enforce(summary.get("status") == "PASS", "HTTP_STATUS")
    enforce(summary.get("case_count") == 1168, "HTTP_CASES")
    enforce(summary.get("case_pass_count") == 1168, "HTTP_PASSES")
    enforce(summary.get("case_failure_count") == 0, "HTTP_FAILURES")
    enforce(summary.get("errors") == [], "HTTP_ERRORS")
    enforce(summary.get("external_network_used") is False, "HTTP_EXTERNAL_NETWORK")
    enforce(summary.get("loopback_only") is True, "HTTP_LOOPBACK")
    enforce(summary.get("read_model_sha256") == EXPECTED_READ_MODEL_SHA256, "HTTP_READ_MODEL")
    termination = require_dict(summary.get("server_termination"), "HTTP_TERMINATION")
    enforce(termination.get("terminated") is True, "HTTP_TERMINATED")
    enforce(termination.get("return_code") == 0, "HTTP_RETURN_CODE")
    enforce(termination.get("sigkill_used") is False, "HTTP_SIGKILL")
    enforce(termination.get("process_group_residual") is False, "HTTP_RESIDUAL")
    artifact_hashes = require_dict(summary.get("artifact_sha256"), "HTTP_ARTIFACT_HASHES")
    enforce(len(artifact_hashes) == 10, "HTTP_ARTIFACT_COUNT")
    for name, expected in artifact_hashes.items():
        enforce(sha256_file(directory / name) == expected, f"HTTP_ARTIFACT_HASH:{name}")
    _, rows = read_tsv(directory / "http-cases.tsv")
    enforce(len(rows) == 1168, "HTTP_TSV_COUNT")
    enforce(len({row.get("case_id") for row in rows}) == 1168, "HTTP_CASE_IDS")
    enforce(all(row.get("outcome") == "PASS" for row in rows), "HTTP_TSV_OUTCOMES")
    phases = dict(sorted(Counter(row.get("phase") for row in rows).items()))
    enforce(phases == EXPECTED_HTTP_PHASES, "HTTP_PHASES")
    artifact = require_dict(read_json(directory / "artifact-check-receipt.json"), "HTTP_ARTIFACT_RECEIPT")
    false_closure(artifact.get("closure_flags"), "HTTP_CLOSURE")
    active = require_dict(artifact.get("active_product_counts"), "HTTP_ACTIVE")
    enforce(bool(active) and all(value == 0 for value in active.values()), "HTTP_ACTIVE_NONZERO")
    enforce(artifact.get("production_activation_count") == 0, "HTTP_PRODUCTION_ACTIVATION")
    summary_sha = sha256_file(summary_path)
    enforce(isinstance(independent.get("status"), str) and independent["status"].startswith("PASS"), "HTTP_INDEPENDENT_STATUS")
    enforce(
        any(value == summary_sha for value in recursive_values(independent)),
        "HTTP_INDEPENDENT_BINDING",
    )
    failures = find_key_values(independent, {"failureCount", "failure_count", "mismatchCount", "mismatch_count"})
    enforce(all(value == 0 for value in failures), "HTTP_INDEPENDENT_FAILURE")
    return {
        "status": "PASS",
        "independentStatus": independent.get("status"),
        "verificationSummarySha256": summary_sha,
        "caseCount": 1168,
        "caseFailureCount": 0,
        "phaseCounts": EXPECTED_HTTP_PHASES.copy(),
        "artifactSha256": artifact_hashes,
        "readModelSha256": EXPECTED_READ_MODEL_SHA256,
        "externalNetworkUsed": False,
        "loopbackOnly": True,
        "processGroupResidual": False,
    }


def reconstruct_ledgers(checkpoint_path: Path, publication_path: Path) -> dict[str, Any]:
    _, checkpoints = read_tsv(checkpoint_path)
    enforce(len(checkpoints) == 15, "CHECKPOINT_COUNT")
    enforce(
        [row.get("checkpoint_id") for row in checkpoints]
        == [f"CHECKPOINT-{ordinal:03d}" for ordinal in range(1, 16)],
        "CHECKPOINT_SEQUENCE",
    )
    _, publications = read_tsv(publication_path)
    enforce(len(publications) == 19, "PUBLICATION_COUNT")
    for ordinal, row in enumerate(publications, 1):
        enforce(row.get("ordinal") == str(ordinal), f"PUBLICATION_ORDINAL:{ordinal}")
        enforce(row.get("status") == "PASS", f"PUBLICATION_STATUS:{ordinal}")
        enforce(row.get("force_push_used") == "false", f"PUBLICATION_FORCE:{ordinal}")
        enforce(row.get("remote_main_after_sha") == EXPECTED_ORIGIN_MAIN_SHA, f"PUBLICATION_MAIN:{ordinal}")
        copy_path = publication_path.parent / "publication-receipts" / str(row.get("copied_path"))
        enforce(copy_path.is_file() and sha256_file(copy_path) == row.get("sha256"), f"PUBLICATION_COPY:{ordinal}")
    final = publications[-1]
    enforce(str(final.get("checkpoint_id", "")).upper() == "CHECKPOINT-015", "PUBLICATION_FINAL_ID")
    enforce(final.get("local_head_sha") == PUBLISHED_CP15_SHA, "PUBLICATION_FINAL_LOCAL")
    enforce(final.get("remote_after_sha") == PUBLISHED_CP15_SHA, "PUBLICATION_FINAL_REMOTE")
    enforce(final.get("sha256") == CP15_PUBLICATION_RECEIPT_SHA256, "PUBLICATION_FINAL_RECEIPT")
    return {
        "committedCheckpointLedgerRowCount": 15,
        "publishedCheckpointCount": 15,
        "publicationReceiptCount": 19,
        "lastCommittedLedgerCheckpoint": "CHECKPOINT-015",
        "lastPublishedCheckpoint": "CHECKPOINT-015",
        "lastPublishedCommit": PUBLISHED_CP15_SHA,
        "lastPublishedTree": PUBLISHED_CP15_TREE,
        "checkpointLedgerSelfReferenceBoundary": True,
    }


def reconstruct_blob(receipt: dict[str, Any], receipt_path: Path) -> dict[str, Any]:
    enforce(receipt.get("status") == "PASS", "BLOB_STATUS")
    enforce(receipt.get("resolved_commit_sha") == PUBLISHED_CP15_SHA, "BLOB_COMMIT")
    enforce(receipt.get("resolved_tree_sha") == PUBLISHED_CP15_TREE, "BLOB_TREE")
    enforce(receipt.get("failure_codes") == [], "BLOB_FAILURES")
    checks = require_dict(receipt.get("checks"), "BLOB_CHECKS")
    enforce(bool(checks) and all(value is True for value in checks.values()), "BLOB_CHECK_RESULT")
    thresholds = require_list(receipt.get("ordinary_blob_thresholds"), "BLOB_THRESHOLDS")
    hosting = [item for item in thresholds if isinstance(item, dict) and item.get("threshold_bytes_inclusive") == 100_000_000]
    enforce(len(hosting) == 1 and hosting[0].get("ordinary_blob_count") == 0, "BLOB_HOSTING_LIMIT")
    enforce(receipt.get("ordinary_blob_ge_100000000_violation_count") == 0, "BLOB_HOSTING_VIOLATION_COUNT")
    maximum = require_dict(receipt.get("maximum_reachable_ordinary_blob"), "BLOB_MAXIMUM")
    enforce(isinstance(maximum.get("bytes"), int) and maximum["bytes"] < 100_000_000, "BLOB_MAXIMUM_LIMIT")
    ledger = require_dict(receipt.get("ledger"), "BLOB_LEDGER")
    ledger_path = receipt_path.parent / str(ledger.get("file_name"))
    enforce(ledger_path.is_file(), "BLOB_LEDGER_FILE")
    enforce(sha256_file(ledger_path) == ledger.get("sha256"), "BLOB_LEDGER_HASH")
    enforce(ledger_path.stat().st_size == ledger.get("bytes"), "BLOB_LEDGER_BYTES")
    return {
        "status": "PASS",
        "resolvedCommit": PUBLISHED_CP15_SHA,
        "resolvedTree": PUBLISHED_CP15_TREE,
        "ordinaryBlobAtOrAbove100MBCount": 0,
        "maximumOrdinaryBlobBytes": maximum.get("bytes"),
        "maximumOrdinaryBlobObjectSha": maximum.get("object_sha"),
        "ledgerSha256": ledger.get("sha256"),
        "ledgerRowCount": ledger.get("data_row_count"),
    }


def reconstruct_identity(environment: dict[str, Any], identity: dict[str, Any]) -> dict[str, Any]:
    enforce(environment.get("source_sha") == SOURCE_SHA, "ENV_SOURCE")
    enforce(environment.get("source_tree") == SOURCE_TREE, "ENV_TREE")
    enforce(environment.get("work_branch") == WORK_BRANCH, "ENV_BRANCH")
    commands = require_dict(environment.get("commands"), "ENV_COMMANDS")
    enforce(bool(commands), "ENV_COMMANDS_EMPTY")
    enforce(all(isinstance(item, dict) and item.get("exit_code") == 0 for item in commands.values()), "ENV_COMMAND_FAILURE")
    serialized = canonical_json_bytes(identity).decode("utf-8")
    enforce(PUBLISHED_CP15_SHA in serialized, "IDENTITY_COMMIT")
    enforce(PUBLISHED_CP15_TREE in serialized, "IDENTITY_TREE")
    command = str(identity.get("command", ""))
    command_proof = identity.get("exit_code") == 0 and str(identity.get("cwd", "")).endswith("gda_round16b_cp016_clean_repro_d40ec811")
    enforce(
        any(value is True for value in find_key_values(identity, {"repositoryClean", "worktreeClean", "gitStatusClean"}))
        or (command_proof and "git status --porcelain" in command),
        "IDENTITY_CLEAN",
    )
    enforce(
        any(value is True for value in find_key_values(identity, {"lfsClean", "gitLfsClean"}))
        or (command_proof and "git lfs status --porcelain" in command),
        "IDENTITY_LFS",
    )
    enforce(
        any(value is True for value in find_key_values(identity, {"detached", "detachedHead"}))
        or (command_proof and "git rev-parse HEAD" in command),
        "IDENTITY_DETACHED",
    )
    return {
        "sourceCommit": PUBLISHED_CP15_SHA,
        "sourceTree": PUBLISHED_CP15_TREE,
        "originMain": EXPECTED_ORIGIN_MAIN_SHA,
        "workBranch": WORK_BRANCH,
        "repositoryClean": True,
        "gitLfsClean": True,
        "detached": True,
    }


def acceptable_receipt(candidate: dict[str, Any]) -> bool:
    try:
        closure = require_dict(require_dict(candidate.get("closureDecision"), "CONTROL_DECISION").get("closure"), "CONTROL_CLOSURE")
        counts = require_dict(candidate["closureDecision"].get("headlineCounts"), "CONTROL_COUNTS")
        governance = require_dict(candidate.get("governance"), "CONTROL_GOVERNANCE")
        database = require_dict(candidate.get("databaseReproduction"), "CONTROL_DATABASE")
        http = require_dict(candidate.get("httpReproduction"), "CONTROL_HTTP")
        boundary = require_dict(candidate.get("publicationBoundary"), "CONTROL_BOUNDARY")
        verification = require_dict(candidate.get("verification"), "CONTROL_VERIFICATION")
        return (
            closure == EXPECTED_CLOSURE
            and counts == EXPECTED_COUNTS
            and candidate["closureDecision"].get("closureTrueCount") == 0
            and candidate["closureDecision"].get("candidateUniverseComplete") is False
            and candidate["closureDecision"].get("candidateUniverseWideExclusionCountDeterminate") is False
            and governance == EXPECTED_GOVERNANCE
            and database.get("compatibilityAdapterUsed") is False
            and database.get("cleanSelfContainedReproduction") is True
            and http.get("caseFailureCount") == 0
            and http.get("externalNetworkUsed") is False
            and http.get("processGroupResidual") is False
            and verification.get("reproducibilityStatus") == "EXACT_PUBLISHED_CHECKPOINT015"
            and verification.get("reproductionSourceCommit") == PUBLISHED_CP15_SHA
            and boundary.get("prepublication") is True
            and boundary.get("checkpoint016CommitEmbedded") is False
            and boundary.get("checkpoint016RemoteCommitEmbedded") is False
            and boundary.get("selfReferenceAvoided") is True
            and not (set(recursive_keys(candidate)) & FORBIDDEN_SELF_REFERENCE_KEYS)
        )
    except (KeyError, TypeError, VerificationError):
        return False


def adversarial_controls(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    controls: list[tuple[str, Callable[[dict[str, Any]], None]]] = []
    for closure_key in CLOSURE_KEYS:
        controls.append((
            f"REJECT_TRUE_{closure_key.upper()}",
            lambda value, key=closure_key: value["closureDecision"]["closure"].__setitem__(key, True),
        ))
    controls.extend([
        ("REJECT_ZERO_UNRESOLVED_ASSOCIATIONS", lambda value: value["closureDecision"]["headlineCounts"].__setitem__("unresolved_association_count", 0)),
        ("REJECT_NONZERO_ACTIVE_PENDING", lambda value: value["closureDecision"]["headlineCounts"].__setitem__("active_pending_review_count", 1)),
        ("REJECT_ZERO_SCOPED_UNEXPLAINED_EXCLUSIONS", lambda value: value["closureDecision"]["headlineCounts"].__setitem__("known_unexplained_exclusion_count", 0)),
        ("REJECT_DETERMINATE_UNIVERSE_EXCLUSION_COUNT", lambda value: value["closureDecision"]["headlineCounts"].__setitem__("universe_wide_unexplained_exclusion_count", 0)),
        ("REJECT_ZERO_NONCOMPOSABLE_VOCABULARY", lambda value: value["closureDecision"]["headlineCounts"].__setitem__("active_noncomposable_vocabulary_count", 0)),
        ("REJECT_CANDIDATE_UNIVERSE_CLOSURE", lambda value: value["closureDecision"].__setitem__("candidateUniverseComplete", True)),
        ("REJECT_FORCE_PUSH", lambda value: value["governance"].__setitem__("forcePushUsed", True)),
        ("REJECT_HISTORY_REWRITE", lambda value: value["governance"].__setitem__("historyRewritten", True)),
        ("REJECT_DEPLOYMENT", lambda value: value["governance"].__setitem__("deploymentPerformed", True)),
        ("REJECT_COMPATIBILITY_ADAPTER", lambda value: value["databaseReproduction"].__setitem__("compatibilityAdapterUsed", True)),
        ("REJECT_HTTP_FAILURE", lambda value: value["httpReproduction"].__setitem__("caseFailureCount", 1)),
        ("REJECT_EXTERNAL_NETWORK", lambda value: value["httpReproduction"].__setitem__("externalNetworkUsed", True)),
        ("REJECT_CP16_EMBEDDED_COMMIT", lambda value: value["publicationBoundary"].__setitem__("checkpoint016CommitEmbedded", True)),
        ("REJECT_FORBIDDEN_FINAL_SHA_KEY", lambda value: value.__setitem__("finalLocalSha", "0" * 40)),
    ])
    results = []
    for control_id, mutate in controls:
        candidate = copy.deepcopy(receipt)
        mutate(candidate)
        results.append({"controlId": control_id, "passed": not acceptable_receipt(candidate)})
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--database-receipt", required=True)
    parser.add_argument("--database-independent-receipt", required=True)
    parser.add_argument("--http-dir", required=True)
    parser.add_argument("--http-independent-receipt", required=True)
    parser.add_argument("--closure-metrics", required=True)
    parser.add_argument("--closure-independent-receipt", required=True)
    parser.add_argument("--semantic-independent-receipt", required=True)
    parser.add_argument("--runtime-independent-receipt", required=True)
    parser.add_argument("--round16a-census", required=True)
    parser.add_argument("--round16a-independent-receipt", required=True)
    parser.add_argument("--checkpoint-ledger", required=True)
    parser.add_argument("--publication-manifest", required=True)
    parser.add_argument("--published-cp15-blob-receipt", required=True)
    parser.add_argument("--environment-receipt", required=True)
    parser.add_argument("--worktree-identity-receipt", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).expanduser().resolve()
    enforce(repo.is_dir(), "REPOSITORY_NOT_DIRECTORY")
    receipt_path = resolve_path(repo, args.receipt)
    output = resolve_path(repo, args.output)
    names = {
        "databaseReceipt": args.database_receipt,
        "databaseIndependentReceipt": args.database_independent_receipt,
        "httpIndependentReceipt": args.http_independent_receipt,
        "closureMetrics": args.closure_metrics,
        "closureIndependentReceipt": args.closure_independent_receipt,
        "semanticIndependentReceipt": args.semantic_independent_receipt,
        "runtimeIndependentReceipt": args.runtime_independent_receipt,
        "round16aCensus": args.round16a_census,
        "round16aIndependentReceipt": args.round16a_independent_receipt,
        "checkpointLedger": args.checkpoint_ledger,
        "publicationManifest": args.publication_manifest,
        "publishedCp15BlobReceipt": args.published_cp15_blob_receipt,
        "environmentReceipt": args.environment_receipt,
        "worktreeIdentityReceipt": args.worktree_identity_receipt,
    }
    paths = {name: resolve_path(repo, value) for name, value in names.items()}
    http_dir = resolve_path(repo, args.http_dir)
    documents = {
        name: require_dict(read_json(path), f"INPUT_JSON:{name}")
        for name, path in paths.items()
        if path.suffix.casefold() == ".json"
    }
    descriptors = {name: file_descriptor(repo, path) for name, path in paths.items()}
    http_descriptor = directory_descriptor(repo, http_dir)
    primary = require_dict(read_json(receipt_path), "PRIMARY_RECEIPT")
    primary_sha = sha256_file(receipt_path)

    checks: list[dict[str, Any]] = []

    def check(check_id: str, condition: bool) -> None:
        enforce(condition, check_id)
        checks.append({"checkId": check_id, "passed": True})

    check("PRIMARY_SCHEMA", primary.get("schema") == PRIMARY_SCHEMA)
    check("PRIMARY_STATUS", primary.get("status") == "PASS_EVIDENCE_BOUNDED_NONCLOSURE_AND_EXACT_CP15_CLEAN_REPRODUCTION")
    check("PRIMARY_CHECKPOINT", primary.get("checkpoint") == "CHECKPOINT-016_PREPUBLICATION")
    check("PRIMARY_ACCEPTANCE_CONTRACT", acceptable_receipt(primary))
    check("NO_FORBIDDEN_SELF_REFERENCE_KEYS", not (set(recursive_keys(primary)) & FORBIDDEN_SELF_REFERENCE_KEYS))

    recorded_inputs = require_dict(require_dict(primary.get("inputEvidence"), "PRIMARY_INPUT_EVIDENCE").get("files"), "PRIMARY_INPUT_FILES")
    check("INPUT_NAME_SET", set(recorded_inputs) == set(descriptors))
    for name in sorted(descriptors):
        check(f"INPUT_DESCRIPTOR_{name}", recorded_inputs.get(name) == descriptors[name])
    check("HTTP_DIRECTORY_DESCRIPTOR", primary["inputEvidence"].get("httpDirectory") == http_descriptor)

    closure = reconstruct_closure(
        documents["closureMetrics"],
        documents["closureIndependentReceipt"],
        documents["semanticIndependentReceipt"],
        documents["runtimeIndependentReceipt"],
        documents["round16aCensus"],
        documents["round16aIndependentReceipt"],
    )
    database = reconstruct_database(
        documents["databaseReceipt"],
        documents["databaseIndependentReceipt"],
        descriptors["databaseReceipt"]["sha256"],
    )
    http = reconstruct_http(http_dir, documents["httpIndependentReceipt"])
    ledgers = reconstruct_ledgers(paths["checkpointLedger"], paths["publicationManifest"])
    blob = reconstruct_blob(documents["publishedCp15BlobReceipt"], paths["publishedCp15BlobReceipt"])
    identity = reconstruct_identity(documents["environmentReceipt"], documents["worktreeIdentityReceipt"])

    mismatches: list[str] = []
    comparison_check_count = 0

    def compare(label: str, observed: Any, expected: Any) -> None:
        nonlocal comparison_check_count
        comparison_check_count += 1
        if observed != expected:
            mismatches.append(label)

    decision = require_dict(primary.get("closureDecision"), "PRIMARY_DECISION")
    compare("closure", decision.get("closure"), closure["closure"])
    compare("headlineCounts", decision.get("headlineCounts"), closure["headlineCounts"])
    compare("closureTrueCount", decision.get("closureTrueCount"), 0)
    compare("databaseReproduction", primary.get("databaseReproduction"), database)
    compare("httpReproduction", primary.get("httpReproduction"), http)
    compare("checkpointEvidence", primary.get("checkpointEvidence"), ledgers)
    compare("reachableBlobProof", primary.get("reachableBlobProof"), blob)
    compare("worktreeIdentity", primary.get("worktreeIdentity"), identity)
    compare("governance", primary.get("governance"), EXPECTED_GOVERNANCE)
    authority = require_dict(primary.get("authority"), "PRIMARY_AUTHORITY")
    compare("authority.source", authority.get("authorizedRound16aSourceCommit"), SOURCE_SHA)
    compare("authority.sourceTree", authority.get("authorizedRound16aSourceTree"), SOURCE_TREE)
    compare("authority.cp15", authority.get("publishedReproductionSourceCommit"), PUBLISHED_CP15_SHA)
    compare("authority.cp15Tree", authority.get("publishedReproductionSourceTree"), PUBLISHED_CP15_TREE)
    compare("authority.main", authority.get("expectedUnchangedOriginMain"), EXPECTED_ORIGIN_MAIN_SHA)
    compare("authority.branch", authority.get("workBranch"), WORK_BRANCH)
    check("PRIMARY_COMPARISON", not mismatches)

    controls = adversarial_controls(primary)
    check("ADVERSARIAL_CONTROL_COUNT", len(controls) == 20)
    check("ADVERSARIAL_CONTROLS_PASS", all(item["passed"] for item in controls))

    verifier_path = Path(__file__).resolve()
    result = {
        "schema": SCHEMA,
        "status": "PASS_FOR_EVIDENCE_BOUNDED_NONCLOSURE_AND_EXACT_CP15_CLEAN_REPRODUCTION",
        "checkpoint": "CHECKPOINT-016_PREPUBLICATION",
        "verifier": {
            "version": VERIFIER_VERSION,
            "path": path_hint(repo, verifier_path),
            "sha256": sha256_file(verifier_path),
            "importsPrimaryBuilder": False,
            "invokesPrimaryBuilder": False,
        },
        "primaryReceipt": {
            "path": path_hint(repo, receipt_path),
            "sha256": primary_sha,
            "schema": primary.get("schema"),
            "status": primary.get("status"),
        },
        "inputEvidence": {
            "files": descriptors,
            "httpDirectory": http_descriptor,
        },
        "independentReconstruction": {
            "authority": {
                "sourceCommit": SOURCE_SHA,
                "sourceTree": SOURCE_TREE,
                "publishedReproductionSourceCommit": PUBLISHED_CP15_SHA,
                "publishedReproductionSourceTree": PUBLISHED_CP15_TREE,
                "originMain": EXPECTED_ORIGIN_MAIN_SHA,
                "workBranch": WORK_BRANCH,
            },
            "closure": closure["closure"],
            "closureTrueCount": 0,
            "headlineCounts": closure["headlineCounts"],
            "database": database,
            "http": http,
            "checkpointEvidence": ledgers,
            "reachableBlobProof": blob,
            "worktreeIdentity": identity,
            "governance": EXPECTED_GOVERNANCE.copy(),
        },
        "checks": {
            "checkCount": len(checks),
            "failureCount": 0,
            "checks": checks,
        },
        "adversarialControls": {
            "controlCount": len(controls),
            "failureCount": 0,
            "controls": controls,
        },
        "comparison": {
            "checkedFieldCount": comparison_check_count,
            "mismatchCount": 0,
            "mismatches": [],
        },
        "publicationBoundary": {
            "checkpoint016CommitVerified": False,
            "checkpoint016RemoteCommitVerified": False,
            "reason": "PREPUBLICATION_SELF_REFERENCE_BOUNDARY",
            "externalPostpublicationReceiptRequired": True,
        },
    }
    payload = json_bytes(result)
    if args.check:
        enforce(output.is_file(), "CHECK_OUTPUT_MISSING")
        enforce(output.read_bytes() == payload, "CHECK_OUTPUT_DRIFT")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(payload)
    print(json.dumps({
        "status": result["status"],
        "output": path_hint(repo, output),
        "output_sha256": sha256_bytes(payload),
        "check_count": result["checks"]["checkCount"],
        "adversarial_control_count": len(controls),
        "mismatch_count": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VerificationError as exc:
        print(json.dumps({"status": "FAIL", "failure_code": str(exc)}, sort_keys=True))
        raise SystemExit(1) from exc
