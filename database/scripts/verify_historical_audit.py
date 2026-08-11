#!/usr/bin/env python3
"""Verify a historical audit package without conflating it with current HEAD."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], stderr=subprocess.STDOUT)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-base-commit", required=True)
    parser.add_argument("--audit-manifest", required=True)
    parser.add_argument("--checksums", required=True)
    parser.add_argument("--expected-normative-version", required=True)
    parser.add_argument("--current-implementation-commit", required=True)
    args = parser.parse_args()

    root = pathlib.Path(git("rev-parse", "--show-toplevel").decode().strip())
    base = git("rev-parse", f"{args.expected_base_commit}^{{commit}}").decode().strip()
    current = git("rev-parse", f"{args.current_implementation_commit}^{{commit}}").decode().strip()
    head = git("rev-parse", "HEAD").decode().strip()
    if current != head:
        raise SystemExit("current implementation identity does not equal HEAD")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", base, current],
        check=False,
    ).returncode:
        raise SystemExit("expected base is not an ancestor of implementation")

    manifest_path = pathlib.PurePosixPath(args.audit_manifest)
    checksum_path = pathlib.PurePosixPath(args.checksums)
    manifest_bytes = git("show", f"{base}:{manifest_path}")
    checksums_bytes = git("show", f"{base}:{checksum_path}")
    manifest = json.loads(manifest_bytes)
    if manifest.get("packageVersion") != args.expected_normative_version:
        raise SystemExit("historical normative/package version mismatch")

    checked = 0
    failures: list[str] = []
    for line in checksums_bytes.decode("utf-8").splitlines():
        if not line.strip():
            continue
        digest, path = line.split(None, 1)
        path = path.strip()
        try:
            payload = git("show", f"{base}:{path}")
        except subprocess.CalledProcessError:
            failures.append(f"missing-at-base:{path}")
            continue
        actual = hashlib.sha256(payload).hexdigest()
        checked += 1
        if actual != digest:
            failures.append(f"sha256:{path}")

    result = {
        "schema": "v49.historical-audit-verification/v1",
        "status": "PASS" if not failures else "FAIL",
        "expectedBaseCommit": base,
        "historicalManifestPath": str(manifest_path),
        "historicalChecksumsPath": str(checksum_path),
        "historicalPackageVersion": manifest.get("packageVersion"),
        "expectedNormativeVersion": args.expected_normative_version,
        "currentImplementationCommit": current,
        "historicalChecksumEntriesChecked": checked,
        "failures": failures,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
