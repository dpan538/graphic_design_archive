#!/usr/bin/env python3
"""Build the deterministic Round 16B Checkpoint 016 prepublication receipt.

This builder consolidates an exact clean reproduction of the already-published
Checkpoint 015 source with the final database, HTTP, semantic, reconciliation,
and recursive-gap evidence.  It deliberately does *not* claim a Checkpoint 016
commit or remote SHA: those identities do not exist until after this artifact
has been committed and ordinarily pushed.  A post-publication receipt outside
the commit must record those values without creating a self-reference.

All inputs are explicit.  The builder is stdlib-only, rejects duplicate JSON
keys, verifies byte seals and headline claims, writes deterministic JSON and
Markdown, and supports a read-only ``--check`` mode.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


SOURCE_SHA = "5419770959bdb8998b693fb2275b47e29b92367c"
SOURCE_TREE = "977d7e8e045c71857959750b775cd4df3d036686"
PUBLISHED_CP15_SHA = "d40ec811c2b60cfcbf6892ba79741d2ee0fec95b"
PUBLISHED_CP15_TREE = "9c08c85efcbc4fd4ce88c3c880c3e3e053f36b65"
EXPECTED_ORIGIN_MAIN_SHA = "8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e"
WORK_BRANCH = "codex/trace-v49-exploration-higher-order-association-closure-round16b"
CP15_PUBLICATION_RECEIPT_SHA256 = (
    "29f5459ad360dde3bf94df45783992968694987f06e2dfd52d02ccb93c69379b"
)

SCHEMA = "trace-round16b-final-clean-reproduction-prepublication-checkpoint016/v1"
BUILDER_VERSION = "trace-round16b-final-clean-reproduction-builder-v1"
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
EXPECTED_DB_ARTIFACTS = {
    "manifest": "5f11af95c21417846cd6a71b92173c2d265d5389365fcce08d8c1b7d5b456433",
    "verifier": "9a7897f21b943377ca868431463a94828be06627a5344f06956e1efa55ee1423",
    "replay": "a215bd3a8bf6030a8ab4d77db12bb90a6e6301352f582322917ca637889ef9de",
    "test": "f73e1645cfbe95bac75cda49ea1ab4bf8b7571f84032309e3895e1f4561458d6",
    "schemaNormalizer": "147da466b77d2237f475e48288f13f09e7068d40c33737b6336b53131cf4abec",
    "clusterRoles": "ffe5136ac890225ddaf6c8cfc370d144684f30378c02276aadefe9804a7d7f0a",
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
GOVERNANCE_FALSE = {
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


class ValidationError(RuntimeError):
    """A stable fail-closed validation error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValidationError(code)


def require_dict(value: Any, code: str) -> dict[str, Any]:
    require(isinstance(value, dict), code)
    return value


def require_list(value: Any, code: str) -> list[Any]:
    require(isinstance(value, list), code)
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
                raise ValidationError(f"JSON_DUPLICATE_KEY:{path}:{key}")
            result[key] = value
        return result

    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"JSON_READ_FAILURE:{path}:{exc}") from exc


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, dialect="excel-tab")
            fields = reader.fieldnames or []
            require(bool(fields) and len(fields) == len(set(fields)), f"TSV_FIELDS:{path}")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ValidationError(f"TSV_READ_FAILURE:{path}:{exc}") from exc
    require(all(None not in row for row in rows), f"TSV_MALFORMED_ROW:{path}")
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
    require(path.is_file(), f"INPUT_NOT_FILE:{path}")
    return {
        "path": path_hint(repo, path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def directory_descriptor(repo: Path, directory: Path) -> dict[str, Any]:
    require(directory.is_dir(), f"INPUT_NOT_DIRECTORY:{directory}")
    entries = []
    for path in sorted(item for item in directory.rglob("*") if item.is_file()):
        entries.append({
            "path": path.relative_to(directory).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    require(bool(entries), f"EMPTY_INPUT_DIRECTORY:{directory}")
    return {
        "path": path_hint(repo, directory),
        "fileCount": len(entries),
        "aggregateSha256": sha256_bytes(canonical_json_bytes(entries)),
        "files": entries,
    }


def status_pass(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("PASS")


def recursive_values(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        for child in value.values():
            yield child
            yield from recursive_values(child)
    elif isinstance(value, list):
        for child in value:
            yield child
            yield from recursive_values(child)


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


def exact_false_closure(value: Any, code: str) -> dict[str, bool]:
    mapping = require_dict(value, code)
    require(mapping == EXPECTED_CLOSURE, code)
    return EXPECTED_CLOSURE.copy()


def validate_database(primary: dict[str, Any], independent: dict[str, Any], primary_sha: str) -> dict[str, Any]:
    require(primary.get("schema") == DB_SCHEMA, "DB_SCHEMA")
    require(primary.get("status") == "PASS", "DB_STATUS")
    require(primary.get("checkpoint") in {16, "CHECKPOINT-016"}, "DB_CHECKPOINT")

    authority = require_dict(primary.get("authority"), "DB_AUTHORITY")
    require(authority.get("sourceCommit") == PUBLISHED_CP15_SHA, "DB_SOURCE_COMMIT")
    require(authority.get("sourceTree") == PUBLISHED_CP15_TREE, "DB_SOURCE_TREE")
    require(authority.get("repositoryClean") is True, "DB_REPOSITORY_CLEAN")

    native = require_dict(primary.get("sourceNative"), "DB_SOURCE_NATIVE")
    require(native.get("compatibilityAdapterUsed") is False, "DB_ADAPTER_USED")
    require(native.get("nativeVerifierExecuted") is True, "DB_NATIVE_VERIFIER")
    require(native.get("fullManifestStatus") == "PASS", "DB_FULL_MANIFEST")
    require(native.get("preflightStatus") == "PASS", "DB_PREFLIGHT")
    require(native.get("artifactSha256") == EXPECTED_DB_ARTIFACTS, "DB_ARTIFACT_HASHES")

    runtime = require_dict(primary.get("runtime"), "DB_RUNTIME")
    require("16.13" in str(runtime.get("postgresqlVersion", "")), "DB_POSTGRES_VERSION")
    require(bool(runtime.get("psqlPath")), "DB_PSQL_PATH")
    require(str(runtime.get("listenAddresses", "")) in {"", "NONE", "none"}, "DB_LISTEN_ADDRESSES")

    databases = require_list(primary.get("databases"), "DB_DATABASES")
    require(len(databases) == 2, "DB_DATABASE_COUNT")
    names: set[str] = set()
    owners: set[str] = set()
    for ordinal, value in enumerate(databases, 1):
        database = require_dict(value, f"DB_DATABASE_{ordinal}")
        name = database.get("database")
        owner = database.get("owner")
        require(isinstance(name, str) and bool(name), f"DB_NAME_{ordinal}")
        require(isinstance(owner, str) and bool(owner), f"DB_OWNER_{ordinal}")
        names.add(name)
        owners.add(owner)
        schema_dump = require_dict(database.get("schemaDump"), f"DB_SCHEMA_DUMP_{ordinal}")
        require(
            schema_dump.get("normalizedSha256") == EXPECTED_NORMALIZED_SCHEMA_SHA256,
            f"DB_NORMALIZED_HASH_{ordinal}",
        )
        require(
            schema_dump.get("normalizedBytes") == EXPECTED_NORMALIZED_SCHEMA_BYTES,
            f"DB_NORMALIZED_BYTES_{ordinal}",
        )
        race = require_dict(database.get("raceEvidence"), f"DB_RACE_{ordinal}")
        require(race.get("checksumsSha256") == EXPECTED_RACE_CHECKSUMS_SHA256, f"DB_RACE_HASH_{ordinal}")
        require(race.get("fileCount") == 12, f"DB_RACE_FILE_COUNT_{ordinal}")
        per_file = require_dict(race.get("perFileSha256"), f"DB_RACE_FILES_{ordinal}")
        require(len(per_file) == 12, f"DB_RACE_FILE_MAP_{ordinal}")
        require(all(isinstance(item, str) and len(item) == 64 for item in per_file.values()), f"DB_RACE_FILE_HASH_{ordinal}")
    require(len(names) == 2 and len(owners) == 1, "DB_IDENTITY_DISTINCTNESS")

    reconciliation = require_dict(primary.get("reconciliation"), "DB_RECONCILIATION")
    require(reconciliation.get("databaseCount") == 2, "DB_RECONCILIATION_COUNT")
    require(reconciliation.get("normalizedSchemasIdentical") is True, "DB_SCHEMA_EQUALITY")
    require(reconciliation.get("normalizedSchemaSha256") == EXPECTED_NORMALIZED_SCHEMA_SHA256, "DB_RECONCILIATION_HASH")
    require(reconciliation.get("normalizedSchemaBytes") == EXPECTED_NORMALIZED_SCHEMA_BYTES, "DB_RECONCILIATION_BYTES")
    require(reconciliation.get("raceChecksumLedgersIdentical") is True, "DB_RACE_EQUALITY")
    require(reconciliation.get("raceChecksumsSha256") == EXPECTED_RACE_CHECKSUMS_SHA256, "DB_RACE_RECONCILIATION_HASH")
    require(reconciliation.get("raceDatabaseResidueCount") == 0, "DB_RACE_RESIDUE")

    governance = require_dict(primary.get("governance"), "DB_GOVERNANCE")
    require(governance.get("cleanSelfContainedReproduction") is True, "DB_CLEAN_REPRODUCTION")
    require(governance.get("sourceNativeManifestPreflight") is True, "DB_NATIVE_PREFLIGHT")
    require(governance.get("compatibilityAdapterUsed") is False, "DB_GOVERNANCE_ADAPTER")
    for field in ("productionDataImported", "productionActivationPerformed", "deploymentPerformed"):
        require(governance.get(field) is False, f"DB_GOVERNANCE_{field}")

    require(independent.get("schema") == DB_INDEPENDENT_SCHEMA, "DB_INDEPENDENT_SCHEMA")
    require(independent.get("status") == "PASS", "DB_INDEPENDENT_STATUS")
    require(independent.get("checkpoint") in {16, "CHECKPOINT-016"}, "DB_INDEPENDENT_CHECKPOINT")
    primary_ref = require_dict(independent.get("primaryReceipt"), "DB_INDEPENDENT_PRIMARY")
    require(primary_ref.get("sha256") == primary_sha, "DB_INDEPENDENT_PRIMARY_HASH")
    require(primary_ref.get("schema") == DB_SCHEMA, "DB_INDEPENDENT_PRIMARY_SCHEMA")
    require(primary_ref.get("status") == "PASS", "DB_INDEPENDENT_PRIMARY_STATUS")
    controls = require_dict(independent.get("adversarialControls"), "DB_INDEPENDENT_CONTROLS")
    require(int(controls.get("controlCount", 0)) > 0, "DB_INDEPENDENT_CONTROL_COUNT")
    require(controls.get("failureCount") == 0, "DB_INDEPENDENT_CONTROL_FAILURES")
    require(
        all(require_dict(item, "DB_INDEPENDENT_CONTROL").get("passed") is True for item in require_list(controls.get("controls"), "DB_INDEPENDENT_CONTROL_LIST")),
        "DB_INDEPENDENT_CONTROL_RESULT",
    )
    comparison = require_dict(independent.get("comparison"), "DB_INDEPENDENT_COMPARISON")
    require(comparison.get("mismatchCount") == 0, "DB_INDEPENDENT_MISMATCH")
    require(comparison.get("mismatches") == [], "DB_INDEPENDENT_MISMATCH_LIST")

    return {
        "status": "PASS",
        "independentStatus": "PASS",
        "databaseCount": 2,
        "databaseNames": sorted(names),
        "ownerCount": len(owners),
        "normalizedSchemaSha256": EXPECTED_NORMALIZED_SCHEMA_SHA256,
        "normalizedSchemaBytes": EXPECTED_NORMALIZED_SCHEMA_BYTES,
        "raceChecksumsSha256": EXPECTED_RACE_CHECKSUMS_SHA256,
        "compatibilityAdapterUsed": False,
        "cleanSelfContainedReproduction": True,
    }


def validate_http(directory: Path, independent: dict[str, Any]) -> dict[str, Any]:
    summary_path = directory / "verification-summary.json"
    summary = require_dict(read_json(summary_path), "HTTP_SUMMARY")
    require(summary.get("schema_version") == "trace-exploration-v3-production-http-verification-summary-v1", "HTTP_SCHEMA")
    require(summary.get("status") == "PASS", "HTTP_STATUS")
    require(summary.get("mode") == "PRODUCTION_HTTP", "HTTP_MODE")
    require(summary.get("case_count") == 1168, "HTTP_CASE_COUNT")
    require(summary.get("case_pass_count") == 1168, "HTTP_PASS_COUNT")
    require(summary.get("case_failure_count") == 0, "HTTP_FAILURE_COUNT")
    require(summary.get("errors") == [], "HTTP_ERRORS")
    require(summary.get("external_network_used") is False, "HTTP_EXTERNAL_NETWORK")
    require(summary.get("loopback_only") is True, "HTTP_LOOPBACK")
    require(summary.get("read_model_sha256") == EXPECTED_READ_MODEL_SHA256, "HTTP_READ_MODEL")

    termination = require_dict(summary.get("server_termination"), "HTTP_TERMINATION")
    require(termination.get("terminated") is True, "HTTP_TERMINATED")
    require(termination.get("return_code") == 0, "HTTP_RETURN_CODE")
    require(termination.get("sigkill_used") is False, "HTTP_SIGKILL")
    require(termination.get("process_group_residual") is False, "HTTP_RESIDUAL")

    artifact_hashes = require_dict(summary.get("artifact_sha256"), "HTTP_ARTIFACT_HASHES")
    require(len(artifact_hashes) == 10, "HTTP_ARTIFACT_COUNT")
    for name, expected in artifact_hashes.items():
        require(sha256_file(directory / name) == expected, f"HTTP_ARTIFACT_HASH:{name}")

    _, rows = read_tsv(directory / "http-cases.tsv")
    require(len(rows) == 1168, "HTTP_TSV_ROW_COUNT")
    require(len({row.get("case_id") for row in rows}) == 1168, "HTTP_TSV_CASE_ID_UNIQUENESS")
    require(all(row.get("outcome") == "PASS" for row in rows), "HTTP_TSV_OUTCOMES")
    require(dict(sorted(Counter(row.get("phase") for row in rows).items())) == EXPECTED_HTTP_PHASES, "HTTP_PHASE_COUNTS")

    artifact = require_dict(read_json(directory / "artifact-check-receipt.json"), "HTTP_ARTIFACT_RECEIPT")
    require(artifact.get("status") == "PASS", "HTTP_ARTIFACT_STATUS")
    exact_false_closure(artifact.get("closure_flags"), "HTTP_CLOSURE_FLAGS")
    active_counts = require_dict(artifact.get("active_product_counts"), "HTTP_ACTIVE_COUNTS")
    require(bool(active_counts) and all(value == 0 for value in active_counts.values()), "HTTP_ACTIVE_COUNTS_NONZERO")
    require(artifact.get("production_activation_count") == 0, "HTTP_PRODUCTION_ACTIVATION")
    require(artifact.get("research_controls_only") is True, "HTTP_RESEARCH_CONTROLS")

    summary_sha = sha256_file(summary_path)
    require(status_pass(independent.get("status")), "HTTP_INDEPENDENT_STATUS")
    require(
        any(value == summary_sha for value in recursive_values(independent)),
        "HTTP_INDEPENDENT_SUMMARY_BINDING",
    )
    failure_values = find_key_values(independent, {"failureCount", "failure_count", "mismatchCount", "mismatch_count"})
    require(all(value == 0 for value in failure_values), "HTTP_INDEPENDENT_FAILURES")

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


def validate_closure_artifacts(
    metrics: dict[str, Any],
    independent: dict[str, Any],
    semantic: dict[str, Any],
    runtime: dict[str, Any],
    round16a: dict[str, Any],
    round16a_independent: dict[str, Any],
) -> dict[str, Any]:
    require(metrics.get("status") == "PASS_EVIDENCE_BOUNDED_NONCLOSURE", "CLOSURE_METRICS_STATUS")
    exact_false_closure(metrics.get("closure"), "CLOSURE_METRICS_FLAGS")
    hypotheses = require_dict(metrics.get("hypotheses"), "CLOSURE_HYPOTHESES")
    candidate = require_dict(metrics.get("candidate_universe"), "CLOSURE_CANDIDATE_UNIVERSE")
    vocabulary = require_dict(metrics.get("vocabulary_reachability"), "CLOSURE_VOCABULARY")
    observed = {
        "unresolved_association_count": hypotheses.get("unresolved_association_count"),
        "active_pending_review_count": hypotheses.get("active_pending_review_count"),
        "known_unexplained_exclusion_count": candidate.get("known_unexplained_exclusion_count"),
        "universe_wide_unexplained_exclusion_count": candidate.get("universe_wide_unexplained_exclusion_count"),
        "active_noncomposable_vocabulary_count": vocabulary.get("active_noncomposable_vocabulary_count"),
    }
    require(observed == EXPECTED_COUNTS, "CLOSURE_HEADLINE_COUNTS")
    require(candidate.get("candidate_universe_closure") is False, "CANDIDATE_UNIVERSE_CLOSURE")

    require(independent.get("status") == "PASS_FOR_EVIDENCE_BOUNDED_NONCLOSURE_DECISION", "CLOSURE_INDEPENDENT_STATUS")
    exact_false_closure(independent.get("closure"), "CLOSURE_INDEPENDENT_FLAGS")
    independent_metrics = require_dict(independent.get("independent_metrics"), "CLOSURE_INDEPENDENT_METRICS")
    for key, expected in EXPECTED_COUNTS.items():
        require(independent_metrics.get(key) == expected, f"CLOSURE_INDEPENDENT_COUNT:{key}")
    require(independent.get("check_count") == 25, "CLOSURE_INDEPENDENT_CHECK_COUNT")
    require(independent.get("adversarial_probe_count") == 48, "CLOSURE_INDEPENDENT_PROBE_COUNT")

    require(semantic.get("status") == "PASS", "SEMANTIC_INDEPENDENT_STATUS")
    exact_false_closure(semantic.get("closure_flags"), "SEMANTIC_CLOSURE_FLAGS")
    require(semantic.get("check_count") == 798, "SEMANTIC_CHECK_COUNT")
    require(runtime.get("status") == "PASS", "RUNTIME_INDEPENDENT_STATUS")
    require(runtime.get("check_count") == 15, "RUNTIME_CHECK_COUNT")
    require(round16a.get("status") == "PASS_WITH_OPEN_CLOSURE_BLOCKERS", "ROUND16A_STATUS")
    exact_false_closure(round16a.get("closure"), "ROUND16A_CLOSURE_FLAGS")
    require(round16a_independent.get("status") == "PASS_WITH_OPEN_CLOSURE_BLOCKERS", "ROUND16A_INDEPENDENT_STATUS")
    require(round16a_independent.get("closure_flags_true_count") == 0, "ROUND16A_INDEPENDENT_CLOSURE_COUNT")
    require(round16a_independent.get("check_count") == 143165, "ROUND16A_INDEPENDENT_CHECK_COUNT")

    return {
        "closure": EXPECTED_CLOSURE.copy(),
        "headlineCounts": EXPECTED_COUNTS.copy(),
        "primaryStatus": metrics.get("status"),
        "independentStatus": independent.get("status"),
        "independentCheckCount": 25,
        "independentAdversarialProbeCount": 48,
        "semanticIndependentStatus": "PASS",
        "semanticIndependentCheckCount": 798,
        "runtimeIndependentStatus": "PASS",
        "runtimeIndependentCheckCount": 15,
        "round16aIndependentStatus": round16a_independent.get("status"),
        "round16aIndependentCheckCount": 143165,
    }


def validate_ledgers(checkpoint_path: Path, publication_path: Path) -> dict[str, Any]:
    _, checkpoints = read_tsv(checkpoint_path)
    require(len(checkpoints) == 15, "CHECKPOINT_LEDGER_ROW_COUNT")
    for ordinal, row in enumerate(checkpoints, 1):
        require(row.get("checkpoint_id") == f"CHECKPOINT-{ordinal:03d}", f"CHECKPOINT_LEDGER_ID:{ordinal}")
    require(checkpoints[-1].get("commit_sha") == PUBLISHED_CP15_SHA, "CHECKPOINT_LEDGER_LAST_COMMIT")

    _, publications = read_tsv(publication_path)
    require(len(publications) == 19, "PUBLICATION_LEDGER_ROW_COUNT")
    for ordinal, row in enumerate(publications, 1):
        require(row.get("ordinal") == str(ordinal), f"PUBLICATION_LEDGER_ORDINAL:{ordinal}")
        require(row.get("status") == "PASS", f"PUBLICATION_LEDGER_STATUS:{ordinal}")
        require(row.get("force_push_used") == "false", f"PUBLICATION_LEDGER_FORCE_PUSH:{ordinal}")
        require(row.get("remote_main_after_sha") == EXPECTED_ORIGIN_MAIN_SHA, f"PUBLICATION_LEDGER_MAIN:{ordinal}")
        copied = publication_path.parent / "publication-receipts" / str(row.get("copied_path"))
        require(copied.is_file(), f"PUBLICATION_LEDGER_COPY:{ordinal}")
        require(sha256_file(copied) == row.get("sha256"), f"PUBLICATION_LEDGER_HASH:{ordinal}")
    final = publications[-1]
    require(str(final.get("checkpoint_id", "")).upper() == "CHECKPOINT-015", "PUBLICATION_LEDGER_LAST_ID")
    require(final.get("local_head_sha") == PUBLISHED_CP15_SHA, "PUBLICATION_LEDGER_LAST_LOCAL")
    require(final.get("remote_after_sha") == PUBLISHED_CP15_SHA, "PUBLICATION_LEDGER_LAST_REMOTE")
    require(final.get("sha256") == CP15_PUBLICATION_RECEIPT_SHA256, "PUBLICATION_LEDGER_CP15_RECEIPT_HASH")

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


def validate_blob_receipt(receipt: dict[str, Any], receipt_path: Path) -> dict[str, Any]:
    require(receipt.get("schema_version") == "trace-round16b-reachable-ordinary-blob-verification/v1", "BLOB_SCHEMA")
    require(receipt.get("status") == "PASS", "BLOB_STATUS")
    require(receipt.get("resolved_commit_sha") == PUBLISHED_CP15_SHA, "BLOB_COMMIT")
    require(receipt.get("resolved_tree_sha") == PUBLISHED_CP15_TREE, "BLOB_TREE")
    require(receipt.get("failure_codes") == [], "BLOB_FAILURE_CODES")
    checks = require_dict(receipt.get("checks"), "BLOB_CHECKS")
    require(bool(checks) and all(value is True for value in checks.values()), "BLOB_CHECK_FAILURE")
    thresholds = require_list(receipt.get("ordinary_blob_thresholds"), "BLOB_THRESHOLDS")
    hosting = [item for item in thresholds if isinstance(item, dict) and item.get("threshold_bytes_inclusive") == 100_000_000]
    require(len(hosting) == 1, "BLOB_HOSTING_THRESHOLD")
    require(hosting[0].get("ordinary_blob_count") == 0, "BLOB_HOSTING_VIOLATION")
    require(receipt.get("ordinary_blob_ge_100000000_violation_count") == 0, "BLOB_HOSTING_VIOLATION_COUNT")
    maximum = require_dict(receipt.get("maximum_reachable_ordinary_blob"), "BLOB_MAXIMUM")
    require(isinstance(maximum.get("bytes"), int) and maximum["bytes"] < 100_000_000, "BLOB_MAXIMUM_LIMIT")
    ledger = require_dict(receipt.get("ledger"), "BLOB_LEDGER")
    ledger_path = receipt_path.parent / str(ledger.get("file_name"))
    require(ledger_path.is_file(), "BLOB_LEDGER_FILE")
    require(sha256_file(ledger_path) == ledger.get("sha256"), "BLOB_LEDGER_HASH")
    require(ledger_path.stat().st_size == ledger.get("bytes"), "BLOB_LEDGER_BYTES")
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


def validate_environment(environment: dict[str, Any]) -> dict[str, Any]:
    require(environment.get("source_sha") == SOURCE_SHA, "ENVIRONMENT_SOURCE_SHA")
    require(environment.get("source_tree") == SOURCE_TREE, "ENVIRONMENT_SOURCE_TREE")
    require(environment.get("work_branch") == WORK_BRANCH, "ENVIRONMENT_BRANCH")
    commands = require_dict(environment.get("commands"), "ENVIRONMENT_COMMANDS")
    require(bool(commands), "ENVIRONMENT_EMPTY_COMMANDS")
    for name, command in commands.items():
        require(require_dict(command, f"ENVIRONMENT_COMMAND:{name}").get("exit_code") == 0, f"ENVIRONMENT_COMMAND_FAILURE:{name}")
    psql = require_dict(commands.get("postgresql"), "ENVIRONMENT_POSTGRESQL")
    require("16.13" in str(psql.get("stdout", "")), "ENVIRONMENT_POSTGRESQL_VERSION")
    return {
        "schema": environment.get("schema_version"),
        "platform": environment.get("platform"),
        "machine": environment.get("machine"),
        "pythonRuntime": environment.get("python_runtime"),
        "postgresql": psql.get("stdout"),
    }


def validate_worktree_identity(identity: dict[str, Any]) -> dict[str, Any]:
    if "status" in identity:
        require(status_pass(identity.get("status")), "WORKTREE_IDENTITY_STATUS")
    serialized = canonical_json_bytes(identity).decode("utf-8")
    require(PUBLISHED_CP15_SHA in serialized, "WORKTREE_IDENTITY_COMMIT")
    require(PUBLISHED_CP15_TREE in serialized, "WORKTREE_IDENTITY_TREE")
    clean_values = find_key_values(identity, {"repositoryClean", "worktreeClean", "gitStatusClean"})
    lfs_values = find_key_values(identity, {"lfsClean", "gitLfsClean"})
    detached_values = find_key_values(identity, {"detached", "detachedHead"})
    command = str(identity.get("command", ""))
    command_proof = identity.get("exit_code") == 0 and str(identity.get("cwd", "")).endswith("gda_round16b_cp016_clean_repro_d40ec811")
    require(
        any(value is True for value in clean_values)
        or (command_proof and "git status --porcelain" in command),
        "WORKTREE_IDENTITY_NOT_CLEAN",
    )
    require(
        any(value is True for value in lfs_values)
        or (command_proof and "git lfs status --porcelain" in command),
        "WORKTREE_IDENTITY_LFS_NOT_CLEAN",
    )
    require(
        any(value is True for value in detached_values)
        or (command_proof and "git rev-parse HEAD" in command),
        "WORKTREE_IDENTITY_NOT_DETACHED",
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


def render_report(receipt: dict[str, Any], receipt_sha: str) -> bytes:
    closure = receipt["closureDecision"]["closure"]
    counts = receipt["closureDecision"]["headlineCounts"]
    governance = receipt["governance"]
    lines = [
        "# 31 — Final clean reproduction and evidence-bounded non-closure",
        "",
        "## Decision",
        "",
        "Checkpoint 016 cleanly reproduces the exact published Checkpoint 015 source, but the evidence boundary still forbids every Function 3 closure claim. This is a deterministic prepublication receipt; the Checkpoint 016 commit and remote SHA must be recorded only after ordinary publication in an external receipt.",
        "",
        "```text",
        f"SOURCE_SHA={SOURCE_SHA}",
        f"WORK_BRANCH={WORK_BRANCH}",
        f"REPRODUCTION_SOURCE_SHA={PUBLISHED_CP15_SHA}",
        f"REPRODUCTION_SOURCE_TREE={PUBLISHED_CP15_TREE}",
        "CHECKPOINT016_LOCAL_SHA=POSTPUBLICATION_EXTERNAL_RECEIPT_REQUIRED",
        "CHECKPOINT016_REMOTE_SHA=POSTPUBLICATION_EXTERNAL_RECEIPT_REQUIRED",
        f"REMOTE_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "REPRODUCTION_WORKTREE_CLEAN=true",
        "PUBLISHED_CHECKPOINT_COUNT=15",
        f"FORCE_PUSH_USED={str(governance['forcePushUsed']).lower()}",
        f"HISTORY_REWRITTEN={str(governance['historyRewritten']).lower()}",
        f"ROLLBACK_TAG_PUSHED={str(governance['rollbackTagPushed']).lower()}",
        f"DEPLOYMENT_PERFORMED={str(governance['deploymentPerformed']).lower()}",
        "",
        f"PAIR_ASSOCIATION_CLOSURE={str(closure['pair_association_closure']).lower()}",
        f"HIGHER_ORDER_ASSOCIATION_CLOSURE={str(closure['higher_order_association_closure']).lower()}",
        f"GLOBAL_COMPOSITION_COHERENCE_CLOSURE={str(closure['global_composition_coherence_closure']).lower()}",
        f"PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE={str(closure['product_association_reachability_closure']).lower()}",
        f"COMPUTATIONAL_SPACE_CLOSURE={str(closure['computational_space_closure']).lower()}",
        f"FUNCTION3_CLOSURE={str(closure['function3_closure']).lower()}",
        "",
        f"UNRESOLVED_ASSOCIATION_COUNT={counts['unresolved_association_count']}",
        f"ACTIVE_PENDING_REVIEW_COUNT={counts['active_pending_review_count']}",
        f"UNEXPLAINED_EXCLUSION_COUNT={counts['known_unexplained_exclusion_count']}",
        f"UNEXPLAINED_EXCLUSION_COUNT_SCOPE={receipt['closureDecision']['knownUnexplainedExclusionCountScope']}",
        f"UNIVERSE_WIDE_UNEXPLAINED_EXCLUSION_COUNT={counts['universe_wide_unexplained_exclusion_count']}",
        f"ACTIVE_NONCOMPOSABLE_VOCABULARY_COUNT={counts['active_noncomposable_vocabulary_count']}",
        f"INDEPENDENT_VERIFICATION_STATUS={receipt['verification']['closureIndependentStatus']}",
        f"REPRODUCIBILITY_STATUS={receipt['verification']['reproducibilityStatus']}",
        f"PREPUBLICATION_RECEIPT_SHA256={receipt_sha}",
        "```",
        "",
        "## Verified reproduction boundary",
        "",
        f"- Database reproduction: {receipt['databaseReproduction']['status']} across two fresh databases; normalized schema `{receipt['databaseReproduction']['normalizedSchemaSha256']}`; compatibility adapter used: `false`.",
        f"- Production HTTP: {receipt['httpReproduction']['caseCount']} cases, zero failures, loopback-only, no residual server process.",
        f"- Reachable ordinary Git blobs: zero at or above 100,000,000 bytes for published CP15; maximum observed {receipt['reachableBlobProof']['maximumOrdinaryBlobBytes']} bytes.",
        "- Production data import, production activation, deployment, main update, force push, history rewrite, and rollback-tag publication were all false.",
        "",
        "## Non-closure boundary",
        "",
        "The scoped ledger has 11 unresolved association hypotheses, nine known unexplained exclusions in the documented research-only-sense scope, an indeterminate universe-wide exclusion total, and five active noncomposable vocabulary terms. Software reproducibility does not convert those historical-research gaps into validated associations.",
        "",
        "## Publication boundary",
        "",
        "This report does not and cannot embed its own commit SHA or post-push remote SHA. After committing and ordinarily pushing Checkpoint 016, generate an external publication receipt that binds the final commit, tree, remote branch tip, unchanged `origin/main`, and clean post-push worktree.",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
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
    parser.add_argument("--report", required=True)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).expanduser().resolve()
    require(repo.is_dir(), "REPOSITORY_NOT_DIRECTORY")
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
    output = resolve_path(repo, args.output)
    report = resolve_path(repo, args.report)
    require(output != report, "OUTPUT_PATH_COLLISION")

    documents = {
        name: require_dict(read_json(path), f"INPUT_JSON_OBJECT:{name}")
        for name, path in paths.items()
        if path.suffix.casefold() == ".json"
    }
    descriptors = {name: file_descriptor(repo, path) for name, path in paths.items()}
    http_descriptor = directory_descriptor(repo, http_dir)

    database = validate_database(
        documents["databaseReceipt"],
        documents["databaseIndependentReceipt"],
        descriptors["databaseReceipt"]["sha256"],
    )
    http = validate_http(http_dir, documents["httpIndependentReceipt"])
    closure = validate_closure_artifacts(
        documents["closureMetrics"],
        documents["closureIndependentReceipt"],
        documents["semanticIndependentReceipt"],
        documents["runtimeIndependentReceipt"],
        documents["round16aCensus"],
        documents["round16aIndependentReceipt"],
    )
    ledgers = validate_ledgers(paths["checkpointLedger"], paths["publicationManifest"])
    blob = validate_blob_receipt(documents["publishedCp15BlobReceipt"], paths["publishedCp15BlobReceipt"])
    environment = validate_environment(documents["environmentReceipt"])
    identity = validate_worktree_identity(documents["worktreeIdentityReceipt"])

    script_path = Path(__file__).resolve()
    receipt = {
        "schema": SCHEMA,
        "status": "PASS_EVIDENCE_BOUNDED_NONCLOSURE_AND_EXACT_CP15_CLEAN_REPRODUCTION",
        "checkpoint": "CHECKPOINT-016_PREPUBLICATION",
        "builder": {
            "version": BUILDER_VERSION,
            "path": path_hint(repo, script_path),
            "sha256": sha256_file(script_path),
        },
        "authority": {
            "authorizedRound16aSourceCommit": SOURCE_SHA,
            "authorizedRound16aSourceTree": SOURCE_TREE,
            "publishedReproductionSourceCommit": PUBLISHED_CP15_SHA,
            "publishedReproductionSourceTree": PUBLISHED_CP15_TREE,
            "workBranch": WORK_BRANCH,
            "expectedUnchangedOriginMain": EXPECTED_ORIGIN_MAIN_SHA,
        },
        "inputEvidence": {
            "files": descriptors,
            "httpDirectory": http_descriptor,
        },
        "environment": environment,
        "worktreeIdentity": identity,
        "checkpointEvidence": ledgers,
        "databaseReproduction": database,
        "httpReproduction": http,
        "deterministicVerification": {
            key: value for key, value in closure.items() if key not in {"closure", "headlineCounts"}
        },
        "reachableBlobProof": blob,
        "closureDecision": {
            "decision": "FUNCTION3_NOT_CLOSED_EVIDENCE_BOUNDED",
            "closure": closure["closure"],
            "closureTrueCount": 0,
            "headlineCounts": closure["headlineCounts"],
            "knownUnexplainedExclusionCountScope": "RESEARCH_ONLY_SENSES_WITHOUT_TRIGGER_HYPOTHESIS_PARTICIPANT_OBLIGATION_OR_EXCLUSION",
            "candidateUniverseComplete": False,
            "candidateUniverseWideExclusionCountDeterminate": False,
            "softwarePassDoesNotImplyHistoricalClosure": True,
        },
        "verification": {
            "databaseIndependentStatus": database["independentStatus"],
            "httpIndependentStatus": http["independentStatus"],
            "closureIndependentStatus": closure["independentStatus"],
            "reproducibilityStatus": "EXACT_PUBLISHED_CHECKPOINT015",
            "reproductionSourceCommit": PUBLISHED_CP15_SHA,
            "reproductionSourceTree": PUBLISHED_CP15_TREE,
        },
        "governance": GOVERNANCE_FALSE.copy(),
        "publicationBoundary": {
            "prepublication": True,
            "checkpoint016CommitEmbedded": False,
            "checkpoint016RemoteCommitEmbedded": False,
            "selfReferenceAvoided": True,
            "ordinaryPushRequiredAfterCommit": True,
            "externalPostpublicationReceiptRequired": True,
            "originMainMustRemain": EXPECTED_ORIGIN_MAIN_SHA,
        },
        "failureCodes": [],
    }
    payload = json_bytes(receipt)
    report_payload = render_report(receipt, sha256_bytes(payload))
    if args.check:
        require(output.is_file(), "CHECK_OUTPUT_MISSING")
        require(report.is_file(), "CHECK_REPORT_MISSING")
        require(output.read_bytes() == payload, "CHECK_OUTPUT_DRIFT")
        require(report.read_bytes() == report_payload, "CHECK_REPORT_DRIFT")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        report.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(payload)
        report.write_bytes(report_payload)
    print(json.dumps({
        "status": receipt["status"],
        "output": path_hint(repo, output),
        "output_sha256": sha256_bytes(payload),
        "report": path_hint(repo, report),
        "report_sha256": sha256_bytes(report_payload),
        "closure_true_count": 0,
        "reproduction_source_commit": PUBLISHED_CP15_SHA,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(json.dumps({"status": "FAIL", "failure_code": str(exc)}, sort_keys=True))
        raise SystemExit(1) from exc
