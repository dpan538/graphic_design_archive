#!/usr/bin/env python3
"""Write or verify the explicit, non-recursive v49 database freeze manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


SOURCE_TAG = "v49-data-api-closure-20260821"
SOURCE_COMMIT = "d78f496bcdf2cd6941791986007cd7a885c4c532"
SCHEMA_HASH = "df1e7741e59e5e6bf1ca80f2a33edfad1abb2fc6d95b57d4d6993b49917020dd"
PROJECTION_DIGEST = "11d92b70bd3a87113d4daabac2b5e4e38a3416cc55be894b42b0dd3d072ca640"
CANONICAL_INPUT_DIGEST = "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48"
API_CONTRACT_DIGEST = "ab3d479d239d74471b6eb04b299da05a63598faa9ccb5b5c2f2b480a9c5c3b55"
FROZEN_ROOTS = [
    "database/migrations",
    "database/functions",
    "database/roles",
    "database/views",
    "database/data-migrations",
    "database/fixtures",
    "database/scripts",
    "database/tests",
]
FROZEN_FILES = [
    "database/schema-manifest.json",
    "DATA_MODEL_V49.md",
    "MIGRATION_V48_TO_V49.md",
    "READ_API_V1.md",
    "generated/public_surfaces_prefreeze_candidate_v48.json",
    "data/prefreeze_candidate_v48.sqlite",
    "generated/prefreeze_candidate_v48_transfer_manifest.json",
    "data/prefreeze_candidate_v48_transfer_manifest.csv",
    "docs/api/v49-read-api-catalog.md",
    "docs/api/v49-read-api-openapi.yaml",
    "docs/api/v49-read-interface-map.md",
]
MAINTENANCE_EXCLUSIONS = {
    "database/FROZEN_V49.md",
    "database/FREEZE_V49.json",
    "database/FREEZE_V49.sha256",
    "database/VERSION",
}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def files_for(repo: Path) -> list[str]:
    result: set[str] = set(FROZEN_FILES)
    for root in FROZEN_ROOTS:
        for path in (repo / root).rglob("*"):
            if path.is_file():
                result.add(path.relative_to(repo).as_posix())
    missing = sorted(path for path in result if not (repo / path).is_file())
    if missing:
        raise SystemExit("MISSING_FROZEN_PATH:" + ",".join(missing))
    return sorted(result)


def sequence(paths: list[str], prefix: str) -> list[str]:
    return [path for path in paths if path.startswith(prefix + "/")]


def write_manifest(repo: Path, cleanup_commit: str) -> dict[str, object]:
    if not re.fullmatch(r"[0-9a-f]{40}", cleanup_commit):
        raise SystemExit("CLEANUP_COMMIT_MUST_BE_FULL_SHA")
    paths = files_for(repo)
    hashes = {path: sha(repo / path) for path in paths}
    payload: dict[str, object] = {
        "version": 49,
        "freezeStatus": "FROZEN",
        "sourceReleaseTag": SOURCE_TAG,
        "sourceReleaseCommit": SOURCE_COMMIT,
        "cleanupCommit": cleanup_commit,
        "schemaHash": SCHEMA_HASH,
        "releaseProjectionDigest": PROJECTION_DIGEST,
        "canonicalInputDigest": CANONICAL_INPUT_DIGEST,
        "apiContractDigest": API_CONTRACT_DIGEST,
        "objectCount": 15923,
        "relationshipCount": 47982,
        "eligibleCount": 7995,
        "heldCount": 7928,
        "acceptedTraceCount": 0,
        "positiveRightsCount": 0,
        "frozenPaths": FROZEN_ROOTS + FROZEN_FILES,
        "fileCount": len(paths),
        "perFileSha256": hashes,
        "migrationSequence": sequence(paths, "database/migrations"),
        "functionSequence": sequence(paths, "database/functions"),
        "roleSequence": sequence(paths, "database/roles"),
        "viewSequence": sequence(paths, "database/views"),
        "canonicalInputPaths": [
            "generated/public_surfaces_prefreeze_candidate_v48.json",
            "data/prefreeze_candidate_v48.sqlite",
            "generated/prefreeze_candidate_v48_transfer_manifest.json",
            "data/prefreeze_candidate_v48_transfer_manifest.csv",
        ],
        "releaseEvidencePaths": [
            "docs/audits/v49-phase2b-migration",
            "docs/audits/v49-release-projection-snapshot-db-closure",
            "docs/audits/v49-api-read-contract-closure",
            "docs/releases/v49/RELEASE_MANIFEST.json",
        ],
        "createdAtUtc": "2026-08-21T00:00:00Z",
        "freezePolicyVersion": "gda-v49-database-freeze/v1",
        "manifestSelfHashExcluded": True,
        "maintenanceExclusions": sorted(MAINTENANCE_EXCLUSIONS),
    }
    target = repo / "database/FREEZE_V49.json"
    target.write_text(json.dumps(payload, indent=2) + "\n")
    digest = sha(target)
    (repo / "database/FREEZE_V49.sha256").write_text(f"{digest}  database/FREEZE_V49.json\n")
    return {"status": "PASS", "mode": "write", "fileCount": len(paths), "manifestSha256": digest}


def verify(repo: Path) -> dict[str, object]:
    manifest_path = repo / "database/FREEZE_V49.json"
    payload = json.loads(manifest_path.read_text())
    expected_digest = (repo / "database/FREEZE_V49.sha256").read_text().split()[0]
    actual_digest = sha(manifest_path)
    if expected_digest != actual_digest:
        raise SystemExit("FREEZE_MANIFEST_DIGEST_MISMATCH")
    if payload.get("version") != 49 or payload.get("freezeStatus") != "FROZEN":
        raise SystemExit("FREEZE_METADATA_INVALID")
    expected = payload.get("perFileSha256", {})
    mismatches = [path for path, digest in expected.items() if not (repo / path).is_file() or sha(repo / path) != digest]
    if mismatches:
        raise SystemExit("FROZEN_PATH_DRIFT:" + ",".join(mismatches))
    current_paths = set(files_for(repo))
    unmanifested = sorted(current_paths - set(expected))
    version = int((repo / "database/VERSION").read_text().strip())
    if unmanifested and version < 50:
        raise SystemExit("UNMANIFESTED_V49_DATABASE_FILE:" + ",".join(unmanifested))
    if version >= 50 and unmanifested:
        adrs = list((repo / "docs/adr").glob("*v50*")) + list((repo / "docs/adr").glob("*V50*"))
        if not adrs:
            raise SystemExit("V50_ADR_REQUIRED")
    if payload["canonicalInputDigest"] != sha(repo / "generated/public_surfaces_prefreeze_candidate_v48.json"):
        raise SystemExit("CANONICAL_INPUT_DIGEST_DRIFT")
    return {"status": "PASS", "mode": "verify", "databaseVersion": version, "frozenFileCount": len(expected), "manifestSha256": actual_digest, "frozenPathDriftCount": 0, "unmanifestedV49DatabaseFileCount": len(unmanifested)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--cleanup-commit")
    args = parser.parse_args()
    repo = args.repo.resolve()
    result = write_manifest(repo, args.cleanup_commit or "") if args.write else verify(repo)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
