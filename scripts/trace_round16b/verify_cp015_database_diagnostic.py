#!/usr/bin/env python3
"""Independently confirm that the CP15 database artifact is diagnostic, not a PASS receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


EXPECTED_HEAD = "024935e8d0c36cf0c4724b1960c71f28afef6595"
EXPECTED_TREE = "28f8ab204378d75d16d98334bbd105d47641f37e"
EXPECTED_SCHEMA_HASH = "1152a494e6b64595c9f9291c1d314a9434cb763c7f2a02512d2768e286f571b4"
EXPECTED_RACE_HASH = "595efb06ae1508b3f2cf952e3d0f1af2e9bd70b12bd4fcde93a530b3b70442ab"
EXPECTED_DATABASES = {
    "gda_v50_round16b_cp015_final_a",
    "gda_v50_round16b_cp015_final_b",
}
EXPECTED_METRICS = {
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repo = args.repo.resolve()
    receipt_path = args.receipt.resolve()
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    checks: list[dict[str, object]] = []

    def check(check_id: str, condition: bool, observed: object) -> None:
        checks.append({"checkId": check_id, "ok": condition, "observed": observed})

    check("SCHEMA", payload.get("schema") == "trace-round16b-cp015-database-diagnostic/v1", payload.get("schema"))
    check("SUPERSEDED_STATUS", payload.get("status") == "SUPERSEDED_DIAGNOSTIC_ONLY", payload.get("status"))
    check("NO_CLEAN_REPRODUCTION_CLAIM", payload.get("cleanSelfContainedReproduction") is False, payload.get("cleanSelfContainedReproduction"))
    check("NO_PASS_CLAIM", payload.get("reproductionPassClaimed") is False, payload.get("reproductionPassClaimed"))
    check("SOURCE_NATIVE_PREFLIGHT_FALSE", payload.get("sourceNativeManifestPreflight") is False, payload.get("sourceNativeManifestPreflight"))
    check("ADAPTER_DISCLOSED", payload.get("compatibilityAdapterUsed") is True, payload.get("compatibilityAdapterUsed"))
    source = payload.get("source", {})
    check("SOURCE_HEAD", source.get("head") == EXPECTED_HEAD, source.get("head"))
    check("SOURCE_TREE", source.get("tree") == EXPECTED_TREE, source.get("tree"))
    check("SOURCE_CLEAN_CAPTURE", source.get("cleanAtCapture") is True, source.get("cleanAtCapture"))
    check("POSTGRESQL_16_13", str(payload.get("runtime", {}).get("postgresqlVersion", "")).startswith("16.13"), payload.get("runtime", {}).get("postgresqlVersion"))
    check("SOCKET_ONLY", payload.get("runtime", {}).get("tcpListenerUsed") is False, payload.get("runtime", {}).get("tcpListenerUsed"))
    adapter = payload.get("compatibilityAdapter", {})
    check("ADAPTER_HASH", adapter.get("sha256") == sha256(args.adapter), adapter.get("sha256"))
    reason = str(payload.get("supersessionReason", ""))
    check("ABSOLUTE_PATH_DEFECT_EXPLICIT", "absolute race-evidence path" in reason and "hybrid run" in reason, reason)
    databases = payload.get("databases", [])
    names = {item.get("database") for item in databases if isinstance(item, dict)}
    check("DATABASE_SET", names == EXPECTED_DATABASES, sorted(str(value) for value in names))
    for item in databases:
        name = item.get("database", "MISSING")
        check(f"{name}:OWNER", item.get("owner") == "gda_v49_phase2a_schema_owner", item.get("owner"))
        check(f"{name}:METRICS", item.get("metrics") == EXPECTED_METRICS, item.get("metrics"))
        check(f"{name}:SCHEMA_HASH", item.get("normalizedSchemaSha256") == EXPECTED_SCHEMA_HASH, item.get("normalizedSchemaSha256"))
        race = item.get("raceEvidence", {})
        check(f"{name}:RACE_HASH", race.get("checksumsSha256") == EXPECTED_RACE_HASH, race.get("checksumsSha256"))
        relative = race.get("relativeDirectory")
        checksum_path = repo / str(relative) / "CHECKSUMS.sha256"
        check(f"{name}:RACE_LEDGER_FILE", checksum_path.is_file(), str(checksum_path))
        if checksum_path.is_file():
            check(f"{name}:RACE_LEDGER_PAYLOAD", sha256(checksum_path) == EXPECTED_RACE_HASH, sha256(checksum_path))
        per_file = race.get("perFileSha256", {})
        check(f"{name}:RACE_FILE_SET", isinstance(per_file, dict) and len(per_file) == 12, sorted(per_file) if isinstance(per_file, dict) else per_file)
        if isinstance(per_file, dict) and relative:
            mismatches = [
                filename
                for filename, expected in per_file.items()
                if not (repo / str(relative) / filename).is_file()
                or sha256(repo / str(relative) / filename) != expected
            ]
            check(f"{name}:RACE_PAYLOADS", not mismatches, mismatches)
    check("SCHEMA_RECONCILED", payload.get("normalizedSchemasIdentical") is True and payload.get("normalizedSchemaSha256") == EXPECTED_SCHEMA_HASH, payload.get("normalizedSchemaSha256"))
    check("RACE_DATABASES_DISPOSED", payload.get("raceDatabaseCountAtCapture") == 0, payload.get("raceDatabaseCountAtCapture"))
    check("FROZEN_MANIFEST_UNMODIFIED", payload.get("frozenCheckpoint11ManifestModified") is False, payload.get("frozenCheckpoint11ManifestModified"))
    check("FROZEN_RECEIPT_UNMODIFIED", payload.get("frozenCheckpoint11ReceiptModified") is False, payload.get("frozenCheckpoint11ReceiptModified"))
    check("NO_DEPLOYMENT", payload.get("deploymentPerformed") is False, payload.get("deploymentPerformed"))

    failures = [row for row in checks if not row["ok"]]
    output = {
        "schema": "trace-round16b-cp015-database-diagnostic-independent-verification/v1",
        "status": "VERIFIED_SUPERSEDED_DIAGNOSTIC_ONLY" if not failures else "INVALID_DIAGNOSTIC",
        "reproductionPassClaimed": False,
        "cleanSelfContainedReproduction": False,
        "receipt": str(receipt_path),
        "receiptSha256": sha256(receipt_path),
        "checkCount": len(checks),
        "failureCount": len(failures),
        "checks": checks,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"CP15_DATABASE_DIAGNOSTIC_INDEPENDENT_STATUS={output['status']}")
    print(f"CHECK_COUNT={len(checks)} FAILURE_COUNT={len(failures)}")
    print("REPRODUCTION_PASS_CLAIMED=false")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
