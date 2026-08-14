#!/usr/bin/env python3
"""Verify a frozen Phase 2B staging bundle and issue a reusable attestation.

This verifier intentionally performs no semantic replay and opens no database
connection.  It reads each descriptor exactly once, verifies the manifest's
size and SHA-256 binding, and hashes a canonical payload that later import runs
can validate without rescanning the 4.5 GB bundle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_MANIFEST_SHA256 = "01ac60c705f7450c6668a91ee6a3d2842c3b0258a4ecd85139611bf916681322"
EXPECTED_SCHEMA_SHA256 = "4ec9a76421548bda1b90ccdbf604906df9da9d349a70c9100abdddd1a7fee105"
EXPECTED_CANDIDATE_SHA256 = "b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48"
EXPECTED_BUNDLE_BINDING_SHA256 = "174bc9ef19293ebbb12feb0fc77ef45185bce489466d2005b04e26250e35742b"
EXPECTED_DESCRIPTOR_COUNT = 35
ATTESTATION_SCHEMA = "gda-v49-phase2b-staging-attestation/v1"


class AttestationError(RuntimeError):
    """A frozen-staging binding invariant failed."""


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise AttestationError(f"DUPLICATE_JSON_KEY:{key}")
        value[key] = item
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def read_manifest(path: Path) -> tuple[dict[str, Any], str]:
    manifest_sha256 = sha256_file(path)
    if manifest_sha256 != EXPECTED_MANIFEST_SHA256:
        raise AttestationError(
            f"MANIFEST_SHA256_MISMATCH:{manifest_sha256}"
        )
    try:
        manifest = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=strict_object,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AttestationError("MANIFEST_READ_FAILED") from error
    if not isinstance(manifest, dict):
        raise AttestationError("MANIFEST_NOT_OBJECT")
    return manifest, manifest_sha256


def verify(stage: Path) -> dict[str, Any]:
    started_wall = time.monotonic()
    started_cpu = time.process_time()
    manifest_path = stage / "staging-manifest.json"
    if not manifest_path.is_file():
        raise AttestationError("MISSING_STAGING_MANIFEST")
    manifest, manifest_sha256 = read_manifest(manifest_path)

    if manifest.get("schema") != "gda-v49-phase2b-staging-manifest/v1":
        raise AttestationError("MANIFEST_SCHEMA_MISMATCH")
    if manifest.get("schemaNormalizedSha256") != EXPECTED_SCHEMA_SHA256:
        raise AttestationError("SCHEMA_SHA256_MISMATCH")
    if manifest.get("candidate", {}).get("sha256") != EXPECTED_CANDIDATE_SHA256:
        raise AttestationError("CANDIDATE_SHA256_MISMATCH")
    if manifest.get("bundleBinding", {}).get("sha256") != EXPECTED_BUNDLE_BINDING_SHA256:
        raise AttestationError("BUNDLE_BINDING_SHA256_MISMATCH")

    files = manifest.get("files")
    if not isinstance(files, dict) or len(files) != EXPECTED_DESCRIPTOR_COUNT:
        raise AttestationError("DESCRIPTOR_COUNT_MISMATCH")
    actual_names = {
        path.name for path in stage.iterdir()
        if path.is_file() and path.name != "staging-manifest.json"
    }
    if actual_names != set(files):
        raise AttestationError("DESCRIPTOR_ALLOWLIST_MISMATCH")

    descriptors: list[dict[str, Any]] = []
    total_bytes = 0
    for name in sorted(files):
        descriptor = files[name]
        if not isinstance(descriptor, dict):
            raise AttestationError(f"DESCRIPTOR_NOT_OBJECT:{name}")
        expected_bytes = descriptor.get("bytes")
        expected_sha256 = descriptor.get("sha256")
        path = stage / name
        if not path.is_file() or path.is_symlink():
            raise AttestationError(f"DESCRIPTOR_NOT_REGULAR_FILE:{name}")
        actual_bytes = path.stat().st_size
        if actual_bytes != expected_bytes:
            raise AttestationError(
                f"DESCRIPTOR_SIZE_MISMATCH:{name}:{actual_bytes}:{expected_bytes}"
            )
        actual_sha256 = sha256_file(path)
        if actual_sha256 != expected_sha256:
            raise AttestationError(
                f"DESCRIPTOR_SHA256_MISMATCH:{name}:{actual_sha256}"
            )
        total_bytes += actual_bytes
        descriptors.append(
            {"bytes": actual_bytes, "path": name, "sha256": actual_sha256}
        )

    payload = {
        "bundleBindingSha256": EXPECTED_BUNDLE_BINDING_SHA256,
        "candidateSha256": EXPECTED_CANDIDATE_SHA256,
        "descriptorCount": len(descriptors),
        "descriptors": descriptors,
        "manifestSha256": manifest_sha256,
        "schema": ATTESTATION_SCHEMA,
        "schemaNormalizedSha256": EXPECTED_SCHEMA_SHA256,
        "stageRealpath": os.path.realpath(stage),
        "totalDescriptorBytes": total_bytes,
    }
    return {
        "attestationPayload": payload,
        "attestationSha256": canonical_sha256(payload),
        "cpuSeconds": round(time.process_time() - started_cpu, 6),
        "status": "PASS",
        "verifiedAtUtc": datetime.now(timezone.utc).isoformat(),
        "wallSeconds": round(time.monotonic() - started_wall, 6),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = verify(args.stage_dir.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AttestationError, OSError, json.JSONDecodeError) as error:
        print(
            json.dumps({"error": str(error), "status": "FAIL"}, sort_keys=True),
            file=sys.stderr,
        )
        raise SystemExit(2)
