#!/usr/bin/env python3
"""Generate immutable-source v49 release and data/audit indexes from inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


TAG = "v49-data-api-closure-20260821"
SOURCE = "d78f496bcdf2cd6941791986007cd7a885c4c532"
TREE = "f0549c319d1e0b0cf5e0aab5a2b297361675b701"
SCHEMA = "df1e7741e59e5e6bf1ca80f2a33edfad1abb2fc6d95b57d4d6993b49917020dd"
PROJECTION = "11d92b70bd3a87113d4daabac2b5e4e38a3416cc55be894b42b0dd3d072ca640"
INPUTS = [
    ("generated/public_surfaces_prefreeze_candidate_v48.json", "sole_canonical_population_input"),
    ("data/prefreeze_candidate_v48.sqlite", "reconciliation_only"),
    ("generated/prefreeze_candidate_v48_transfer_manifest.json", "integrity_manifest"),
    ("data/prefreeze_candidate_v48_transfer_manifest.csv", "integrity_manifest"),
]


def digest_paths(repo: Path, paths: list[str]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        data = (repo / path).read_bytes()
        digest.update(path.encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(data).hexdigest().encode())
        digest.update(b"\n")
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    release_dir = repo / "docs/releases/v49"
    release_dir.mkdir(parents=True, exist_ok=True)
    inventory = json.loads(args.inventory.read_text())
    files = inventory["files"]
    by_path = {row["path"]: row for row in files}
    checksum_lines = [f'{row["sha256"]}  {row["path"]}' for row in sorted(files, key=lambda item: item["path"])]
    (release_dir / "SOURCE_TREE_FILES.sha256").write_text("\n".join(checksum_lines) + "\n")
    api_contract_paths = [
        "READ_API_V1.md",
        "docs/api/v49-read-api-catalog.md",
        "docs/api/v49-read-api-openapi.yaml",
        "docs/api/v49-read-interface-map.md",
    ]
    manifest = {
        "format": "gda-v49-release-manifest/v1",
        "release": "v49",
        "sourceReleaseTag": TAG,
        "sourceCommit": SOURCE,
        "sourceTree": TREE,
        "schemaSha256": SCHEMA,
        "releaseProjectionDigest": PROJECTION,
        "canonicalInputSha256": by_path[INPUTS[0][0]]["sha256"],
        "apiContractDigest": digest_paths(repo, api_contract_paths),
        "objectCount": 15923,
        "relationshipCount": 47982,
        "eligibleCount": 7995,
        "heldCount": 7928,
        "acceptedTraceCount": 0,
        "positiveRightsCount": 0,
        "publicReadEndpointCount": 18,
        "sourceTrackedFileCount": len(files),
        "sourceTrackedBytes": sum(row["byte_size"] for row in files),
        "sourceFileChecksums": "SOURCE_TREE_FILES.sha256",
        "authoritativeAuditPackages": [
            "docs/audits/v49-phase2b-migration",
            "docs/audits/v49-release-projection-snapshot-db-closure",
            "docs/audits/v49-api-read-contract-closure",
        ],
    }
    (release_dir / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    data_inputs = []
    for path, role in INPUTS:
        row = by_path[path]
        data_inputs.append({"path": path, "role": role, "sha256": row["sha256"], "byteSize": row["byte_size"], "lfs": row["lfs_pointer_status"] == "LFS_TRACKED", "mutable": False})
    (release_dir / "DATA_INPUT_MANIFEST.json").write_text(json.dumps({"format": "gda-v49-data-input-manifest/v1", "canonicalPopulationInputCount": 1, "inputs": data_inputs}, indent=2) + "\n")
    audit_roots: dict[str, dict[str, int]] = {}
    for row in files:
        path = row["path"]
        if not path.startswith("docs/audits/"):
            continue
        parts = path.split("/")
        if len(parts) < 3:
            continue
        root = "/".join(parts[:3])
        summary = audit_roots.setdefault(root, {"fileCount": 0, "byteSize": 0})
        summary["fileCount"] += 1
        summary["byteSize"] += row["byte_size"]
    authoritative = set(manifest["authoritativeAuditPackages"])
    audit_payload = [{"path": path, **values, "classification": "FINAL_AUTHORITATIVE" if path in authoritative else "INDEXED_SUPPORTING_EVIDENCE", "sourceAnchor": TAG} for path, values in sorted(audit_roots.items())]
    (release_dir / "AUDIT_PACKAGE_MANIFEST.json").write_text(json.dumps({"format": "gda-v49-audit-package-manifest/v1", "packages": audit_payload}, indent=2) + "\n")
    (release_dir / "RELEASE_INDEX.md").write_text(f"""# v49 release index

The immutable source release is annotated tag `{TAG}` at `{SOURCE}` (tree `{TREE}`). It preserves the complete pre-hygiene database closure, API closure, historical data, audit evidence, and repository state.

- Release manifest: `docs/releases/v49/RELEASE_MANIFEST.json`
- Source checksums: `docs/releases/v49/SOURCE_TREE_FILES.sha256`
- Data inputs: `docs/releases/v49/DATA_INPUT_MANIFEST.json`
- Audit index: `docs/releases/v49/AUDIT_INDEX.md`
- Active database root: `database/`
- Historical database skeleton: `db/` at `{TAG}` only

The active tip may remove anchored historical captures, prompts, reports, generated intermediates, and `db/`; retrieve them with `git show {TAG}:<path>` without rewriting history.
""")
    (release_dir / "SOURCE_TREE_SUMMARY.md").write_text(f"""# v49 immutable source tree summary

| Field | Value |
|---|---|
| Tag | `{TAG}` |
| Commit | `{SOURCE}` |
| Tree | `{TREE}` |
| Tracked files | {len(files)} |
| Tracked bytes | {sum(row['byte_size'] for row in files)} |
| Schema SHA-256 | `{SCHEMA}` |
| Release projection digest | `{PROJECTION}` |
| Objects / relationships | 15,923 / 47,982 |
| Public Read API templates | 18 |

The remote annotated tag object and peeled commit are independently recorded in the repository-closure audit package.
""")
    (release_dir / "DATA_RETENTION.md").write_text(f"""# v49 data retention

Only four byte-pinned v48 artifacts remain in the active tree. `{INPUTS[0][0]}` is the sole canonical population input; SQLite and transfer manifests are reconciliation/integrity evidence and never backfill canonical state. Their bytes and missing/null/empty semantics are frozen.

Historical raw captures, backups, queues, audits, v46/v47 outputs, and superseded summaries are removed from the active tip only after `{TAG}` was remotely verified. They remain recoverable from that immutable source tree and are not copied into an active archive directory.
""")
    lines = ["# v49 audit index", "", f"All listed packages are recoverable at `{TAG}`. Final authoritative packages remain active; supporting packages remain indexed evidence unless a later maintenance revision proves them redundant.", "", "| Package | Classification | Files | Bytes |", "|---|---|---:|---:|"]
    for item in audit_payload:
        lines.append(f"| `{item['path']}` | {item['classification']} | {item['fileCount']} | {item['byteSize']} |")
    (release_dir / "AUDIT_INDEX.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"status": "PASS", "tag": TAG, "source": SOURCE, "tree": TREE, "files": len(files), "dataInputs": len(data_inputs), "auditPackages": len(audit_payload), "apiContractDigest": manifest["apiContractDigest"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
